"""Voter pools: what a party talks to, measured rather than asserted.

The model used to carry ``BLOCS`` — two hand-drawn lists of parties assumed to
trade votes with each other. That is a claim about parties. A pool is a claim
about *voters*: a characteristic people have, measured from the census, against
which each party is described by the rate at which it wins them.

Three things this module is careful about, each because getting them wrong
produces output that looks right.

**Every party is fitted at once, subject to what must be true.** Fitting each
party on its own is not a model of an election: it let two parties both claim
most of a pool while a third went negative to balance, and nothing noticed —
the white pool came out assigned 111.4% of its voters and the Coloured pool
90.4%, with 106.1% of the vote existing in total. :func:`fit_joint` imposes the
two facts that must hold, that no party can win negative votes and that every
voter votes for someone, and :func:`balance_margins` then matches both known
totals exactly. Those constraints are also what identifies the small parties: a
pool that must add to one says something about every party in it that no
single-party regression can see.

**A dimension must earn its place.** The design takes n dimensions — race, age,
sex, and income, education or home language the day we hold them. Every one of
them improves in-sample fit, and most of that is collinearity: ward %Black
African correlates +0.75 with %aged 20-29. So the base dimension carries the
pools and every further dimension enters as a *deviation from the city mean*,
admitted only if it improves fit out-of-sample when vectors fitted on one city
are tested against another. Age and sex are fitted and rejected; see
``config/dimensions.toml``.

Time and geography are both handled rather than assumed. Censuses are a decade
apart, so composition is interpolated to polling day and damped-extrapolated
past the last one (:func:`composition_at`). Ward boundaries move between
delimitations and ward codes are contiguous and *reused*, so Census 2022's 135
Johannesburg codes join the 2011 election's 130 wards at a perfect 130/130 —
every one the wrong polygon. :func:`reproject` goes through voting districts
instead, which every election file maps to its own wards, and reports how much
of the electorate it could account for.

Usage::

    python src/pools.py --city joburg --target 2026          # fit and report
    python src/pools.py --city joburg --target 2026 --emit   # write the pools
    python src/pools.py --gate                               # re-run admission
"""

from __future__ import annotations

import argparse
import csv
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path

import numpy as np

import cityconfig
import parties as P

CONFIG = Path("config/dimensions.toml")

# Convergence tolerance on the projected-gradient map in :func:`_solve`,
# relative to the size of the fitted vector. Rates live in [0, 1] and the
# weighted objective is normalised, so this is a genuinely tight stop.
SOLVE_TOL = 1e-9


# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Census:
    """One published census, on one delimitation."""
    year: int
    delimitation: int
    source: str
    sheet: str
    code_column: int
    total_column: int
    columns: tuple


@dataclass(frozen=True)
class Dimension:
    name: str
    role: str
    admitted: bool
    categories: tuple[str, ...]
    censuses: tuple[Census, ...]
    note: str = ""


@dataclass
class Config:
    covariate_root: Path
    dimensions: tuple[Dimension, ...]
    fit: dict
    gate: dict
    damping: float = 0.6
    max_extrapolation: float = 8.0

    def base(self) -> Dimension:
        base = [d for d in self.dimensions if d.role == "base"]
        if len(base) != 1:
            raise SystemExit(f"need exactly one base dimension, found {len(base)}")
        return base[0]

    def tilts(self, *, admitted_only: bool = True) -> list[Dimension]:
        return [d for d in self.dimensions
                if d.role == "tilt" and (d.admitted or not admitted_only)]


def load_config(path: Path = CONFIG) -> Config:
    raw = tomllib.loads(Path(path).read_text())
    dims = []
    for d in raw["dimension"]:
        censuses = tuple(sorted(
            (Census(year=int(c["year"]), delimitation=int(c["delimitation"]),
                    source=c["source"], sheet=c["sheet"],
                    code_column=int(c["code_column"]),
                    total_column=int(c["total_column"]),
                    columns=tuple(c["columns"]))
             for c in d.get("census", [])),
            key=lambda c: c.year))
        if not censuses:
            raise SystemExit(f"dimension {d['name']!r} declares no census")
        dims.append(Dimension(
            name=d["name"], role=d["role"], admitted=bool(d["admitted"]),
            categories=tuple(d["categories"]), censuses=censuses,
            note=d.get("note", "")))
    return Config(
        covariate_root=Path(raw["covariate_root"]),
        dimensions=tuple(dims),
        fit=raw.get("fit", {}),
        gate=raw.get("gate", {}),
        damping=float(raw.get("extrapolation_damping", 0.6)),
        max_extrapolation=float(raw.get("extrapolation_max_years", 8)),
    )


# --------------------------------------------------------------------------
# covariates
# --------------------------------------------------------------------------
def read_census(dim: Dimension, census: Census, cfg: Config) -> dict[str, np.ndarray]:
    """One census: ward -> composition over this dimension, summing to 1."""
    import openpyxl

    path = cfg.covariate_root / census.source
    if not path.exists():
        raise SystemExit(f"{dim.name} {census.year}: missing covariate file {path}")
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    if census.sheet not in book.sheetnames:
        raise SystemExit(f"{dim.name} {census.year}: {path.name} has no sheet "
                         f"{census.sheet!r}; found {book.sheetnames}")
    rows = book[census.sheet].iter_rows(values_only=True)
    next(rows)  # header

    def cell(row, spec) -> float:
        ix = spec if isinstance(spec, (list, tuple)) else (spec,)
        return sum(float(row[i] or 0.0) for i in ix)

    out: dict[str, np.ndarray] = {}
    for row in rows:
        code = str(row[census.code_column]).strip()
        vec = np.array([cell(row, c) for c in census.columns], dtype=float)
        if vec.sum() > 0:
            # Renormalised over the listed categories, so where the columns do
            # not exhaust the total (age drops the under-20 bands) the shares
            # are of the *modelled* population, not of everybody.
            out[code] = vec / vec.sum()
    return out


def read_census_population(dim: Dimension, census: Census,
                           cfg: Config) -> dict[str, float]:
    """Ward -> the population this dimension's categories are counted over.

    :func:`read_census` normalises each ward to shares and throws the head count
    away, which is fine for composition and wrong for everything else: a pool's
    size in the *electorate* is population times turnout, and without the
    denominator neither term is available.
    """
    import openpyxl

    path = cfg.covariate_root / census.source
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = book[census.sheet].iter_rows(values_only=True)
    next(rows)

    def cell(row, spec) -> float:
        ix = spec if isinstance(spec, (list, tuple)) else (spec,)
        return sum(float(row[i] or 0.0) for i in ix)

    out: dict[str, float] = {}
    for row in rows:
        code = str(row[census.code_column]).strip()
        if census.total_column >= 0:
            total = float(row[census.total_column] or 0.0)
        else:
            total = sum(cell(row, c) for c in census.columns)
        if total > 0:
            out[code] = total
    return out


@dataclass
class PoolCounts:
    """A pool is a set of people, and three nested subsets of it.

    ``people ⊇ voting_age ⊇ registered ⊇ voted``, each a wards x pools count.
    Collapsing these into one votes-per-head number, which is what this module
    did first, throws away three separate processes and hides which of them is
    doing the work. Measured on Johannesburg 2021 the composite spans four to
    one across pools, and almost none of that is turnout::

        pool             adult   registration   turnout   votes/person
        Black African    69.9%       43%         35.9%       0.107
        Coloured         63.8%       77%         55.4%       0.272
        Indian/Asian     69.6%       78%         44.0%       0.237
        White            90.5%      173%         52.9%       0.830

    Turnout — the thing "voting percentage" normally means — spans only about
    1.5 to 1. The spread is mostly registration, and the white pool's 173% is
    impossible, so the composite leaned hardest on its least trustworthy part.

    The levels also behave differently over time, which is the forecasting
    reason to keep them apart: ageing is near-deterministic and moves in one
    direction (South Africa's Black African pool is much younger, so its
    eligible share grows every cycle), registration drifts slowly, and turnout
    swings — the 2021 ANC collapse was 587k abstentions, not switches.
    """

    wards: list[str]
    categories: tuple[str, ...]
    people: np.ndarray
    voting_age: np.ndarray
    registered: np.ndarray
    voted: np.ndarray
    rates: dict[str, np.ndarray] = field(default_factory=dict)
    violations: list[str] = field(default_factory=list)

    def composition(self, level: str = "voted") -> np.ndarray:
        counts = getattr(self, level)
        total = counts.sum(axis=1, keepdims=True)
        return np.divide(counts, total, out=np.zeros_like(counts), where=total > 0)

    def totals(self, level: str = "voted") -> np.ndarray:
        return getattr(self, level).sum(axis=0)


def _nest(parent: np.ndarray, observed: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Split an observed ward total across pools, in proportion to the parent.

    One rate per pool is fitted across wards (``observed_w ~ sum_g parent_wg
    r_g``), applied, then each ward is scaled so its pools sum to what was
    actually observed there. The rate carries the between-ward information; the
    scaling makes every ward agree with the published count.
    """
    rate = _nnls(parent, observed)
    child = parent * rate[None, :]
    row = child.sum(axis=1)
    scale = np.divide(observed, row, out=np.ones_like(row), where=row > 0)
    return child * scale[:, None], rate


def _nnls(A: np.ndarray, b: np.ndarray, iters: int = 40000) -> np.ndarray:
    x = np.full(A.shape[1], b.sum() / max(A.sum(), 1e-9))
    lipschitz = float(np.linalg.norm(A, 2) ** 2)
    if lipschitz <= 0:
        return x
    for _ in range(iters):
        x = np.maximum(x - (A.T @ (A @ x - b)) / lipschitz, 0.0)
    return x


def ward_totals(city: cityconfig.City, year: str,
                ballot: str = "PR") -> tuple[dict[str, float], dict[str, float]]:
    """Ward -> registered voters, and ward -> votes cast. Both published."""
    template = cityconfig.CALENDAR[year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        raise SystemExit(f"no result file for {city.slug} {year}: {path}")
    # The results-portal NPE layout (2019, 2024) carries no Ward column at all,
    # so those files land with it blank. A national election has no ward
    # contest, but its voting districts still sit inside wards, and the LGE
    # under the same delimitation says which. Without this the registration
    # series loses two of its five cycles.
    fallback: dict[str, str] = {}

    reg: dict[str, float] = defaultdict(float)
    votes: dict[str, float] = defaultdict(float)
    seen: set[str] = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        reader = csv.DictReader(fh)
        # National elections have one ballot and no BallotType column; local
        # ones have two. Filtering on a column that is not there silently
        # dropped every NPE row, which cost the series five of its cycles.
        has_ballot = "BallotType" in (reader.fieldnames or [])
        for row in reader:
            if has_ballot and row.get("BallotType") != ballot:
                continue
            vd = row["VD_Number"].strip()
            ward = (row.get("Ward") or "").strip()
            if not ward:
                if not fallback:
                    lge = max((y for y in cityconfig.CALENDAR
                               if int(y) <= int(year)
                               and cityconfig.CALENDAR[y].kind == "LGE"
                               and cityconfig.CALENDAR[y].results),
                              key=int, default=None)
                    if lge:
                        try:
                            fallback = vd_map(city, lge)[0]
                        except SystemExit:
                            fallback = {}
                ward = fallback.get(vd, "")
            if vd not in seen:            # registration is per VD, not per row
                seen.add(vd)
                reg[ward] += float(row.get("Registered_Population") or 0)
            votes[ward] += int(float(row.get("Party_Votes") or 0))
    return dict(reg), dict(votes)


def pool_counts(city: cityconfig.City, year: str, cfg: Config) -> PoolCounts:
    """Build the four nested levels for one city and election.

    Three of the four are observed rather than modelled: the census publishes
    people and the 20+ count per ward, and the IEC publishes registered voters
    and votes cast per voting district. Only the *split of each across pools*
    is estimated, and each level is anchored to its published ward total.

    Nesting violations are reported, not clamped. Johannesburg's white pool
    comes out with more registered voters than adults, which cannot be true;
    silently capping it would bury a defect in the public record (Census 2022's
    ward-level undercount, or voters registered where they do not live) inside
    our own numbers.
    """
    base = cfg.base()
    when = polling_decimal_year(year, city)
    reg_by_ward, votes_by_ward = ward_totals(city, year)
    codes = set(reg_by_ward)

    comp_by_ward, _ = composition_at(base, cfg, when, codes,
                                     city=city, election_year=year)
    people_by_ward = read_census_population(base, base.censuses[-1], cfg)
    age = next((d for d in cfg.dimensions if d.name == "age"), None)
    adults_by_ward = (read_census_population(age, age.censuses[-1], cfg)
                      if age else {})

    wards = sorted(w for w in codes
                   if w in comp_by_ward and w in people_by_ward
                   and reg_by_ward.get(w, 0) > 0)
    if not wards:
        raise SystemExit(f"{city.slug} {year}: no ward joined the census")

    comp = np.array([comp_by_ward[w] for w in wards])
    people = comp * np.array([people_by_ward[w] for w in wards])[:, None]

    rates: dict[str, np.ndarray] = {}
    if adults_by_ward:
        observed_adults = np.array([adults_by_ward.get(w, 0.0) for w in wards])
        voting_age, rates["adult_share"] = _nest(people, observed_adults)
    else:
        # No age table: every pool assumed equally adult, which is false and
        # said out loud rather than assumed silently.
        voting_age = people.copy()
        rates["adult_share"] = np.ones(people.shape[1])

    registered, rates["registration"] = _nest(
        voting_age, np.array([reg_by_ward[w] for w in wards]))
    voted, rates["turnout"] = _nest(
        registered, np.array([votes_by_ward.get(w, 0.0) for w in wards]))

    # How wrong the census would have to be for this to hold. Registration is
    # counted; ward population is a modelled small-area estimate, and for the
    # 2022 census the estimates for exactly these groups are the disputed ones.
    # So this ratio is reported as a property of the census, not of the model.
    implied = registered.sum(axis=0) / np.maximum(voting_age.sum(axis=0), 1e-9)
    rates["census_correction"] = np.maximum(implied, 1.0)

    violations = []
    for name, child, parent in (("registered", registered, voting_age),
                                ("voted", voted, registered)):
        over = child.sum(axis=0) / np.maximum(parent.sum(axis=0), 1e-9)
        for g, ratio in enumerate(over):
            if ratio > 1.0:
                violations.append(
                    f"{base.categories[g]}: {name} is {ratio:.0%} of the level "
                    f"above it, which is impossible. Do NOT read this as a "
                    f"census undercount: the published Census 2022 figures for "
                    f"the white and Indian groups are argued to be too HIGH, "
                    f"not too low (over-adjustment for a 62%/72% "
                    f"post-enumeration undercount, leaving them 14%/24% above "
                    f"projections), which makes this gap wider rather than "
                    f"narrower. See DATA-QUALITY.md item 11.")

    return PoolCounts(wards=wards, categories=base.categories, people=people,
                      voting_age=voting_age, registered=registered, voted=voted,
                      rates=rates, violations=violations)


def registration_series(city: cityconfig.City, cfg: Config,
                        before: str | None = None) -> dict[str, np.ndarray]:
    """Each pool's share of the registered roll, at every election on disk.

    This is the series the model should lean on, and the census is the junior
    partner. Registration is *counted*, published per voting district, and we
    hold ten cycles of it for Johannesburg (2000 through 2024) plus the roll
    for the target. The census offers one usable ward-level observation, and
    for the groups that matter most it is the disputed one: Census 2022 has
    Johannesburg's white population falling by 211,000 in eleven years, from
    12.3% to 7.0%, while the 2021 roll carries ~560,000 registered white
    voters — a figure consistent with the 2011 count and not with the 2022 one.

    Two things this buys. The trend in a pool's share of the roll is measured
    over many cycles rather than inferred from two censuses. And each series
    checks the other: where the census implies a change the roll does not show,
    the roll wins and the run says so.

    ``before`` restricts to elections strictly before that year, so a backtest
    cannot see its own target's roll.
    """
    out: dict[str, np.ndarray] = {}
    for year in cityconfig.CALENDAR:
        if before is not None and int(year) >= int(before):
            continue
        if cityconfig.CALENDAR[year].results is None:
            continue
        try:
            counts = pool_counts(city, year, cfg)
        except SystemExit:
            continue           # that election is not on disk for this city
        total = counts.totals("registered")
        if total.sum() > 0:
            out[year] = total / total.sum()
    return out


def projected_pool_shares(series: dict[str, np.ndarray], target: str,
                          damping: float = 0.6) -> tuple[np.ndarray, str]:
    """Carry each pool's share of the roll forward to the target election.

    A straight line through the last two observations, damped, which is the
    same treatment :func:`composition_at` gives census composition — and for
    the same reason: a trend measured over one interval, extended, claims more
    than the data supports.
    """
    years = sorted(series)
    if not years:
        raise SystemExit("no registration series: cannot size the pools")
    if len(years) == 1:
        return series[years[0]], f"{years[0]} roll held flat"
    a, b = years[-2], years[-1]
    span = int(b) - int(a)
    step = (int(target) - int(b)) / span if span else 0.0
    trend = series[b] - series[a]
    shares = np.maximum(series[b] + damping * step * trend, 1e-6)
    return shares / shares.sum(), (
        f"{b} roll carried to {target} on the {a}-{b} trend, damped x{damping:g}")


def vd_map(city: cityconfig.City, year: str) -> tuple[dict[str, str], dict[str, float]]:
    """VD -> ward, and VD -> registered voters, as at one election.

    Each election file records which voting districts made up which ward *that
    year*, which is what makes VDs the common currency between delimitations.
    """
    template = cityconfig.CALENDAR[year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        raise SystemExit(f"no result file for {city.slug} {year}: {path}")
    ward_of, reg = {}, {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            vd = (row.get("VD_Number") or "").strip()
            ward = (row.get("Ward") or "").strip()
            if not vd or not ward:
                continue
            ward_of[vd] = ward
            reg[vd] = max(reg.get(vd, 0.0), float(row.get("Registered_Population") or 0))
    return ward_of, reg


def reproject(comp: dict[str, np.ndarray], city: cityconfig.City,
              from_year: str, to_year: str) -> tuple[dict[str, np.ndarray], float]:
    """Move a ward-level composition from one delimitation onto another.

    Wards are redrawn between elections, so a census published on the 2011
    wards cannot be joined to the 2021 wards — and because ward codes are
    contiguous and reused, the bad join *succeeds*. The fix is to go through
    voting districts, which are far smaller and which every election file maps
    to its own wards: push each old ward's composition down to its VDs, then
    pull it back up into the new wards, weighting by registered voters.

    This is areal interpolation with population weights, and it assumes
    composition is uniform within an old ward. That assumption is wrong in
    detail and unavoidable without small-area census data; its error is second
    order next to joining the wrong polygons outright.

    Returns the reprojected composition and the fraction of the target
    electorate that could actually be mapped.
    """
    old_ward, _ = vd_map(city, from_year)
    new_ward, reg = vd_map(city, to_year)

    acc: dict[str, np.ndarray] = {}
    weight: dict[str, float] = {}
    mapped = total = 0.0
    for vd, ward in new_ward.items():
        w = reg.get(vd, 0.0)
        total += w
        src = old_ward.get(vd)
        if src is None or src not in comp or w <= 0:
            continue          # a VD that did not exist under the old delimitation
        mapped += w
        acc[ward] = acc.get(ward, 0.0) + comp[src] * w
        weight[ward] = weight.get(ward, 0.0) + w

    out = {ward: v / weight[ward] for ward, v in acc.items() if weight[ward] > 0}
    return out, (mapped / total if total > 0 else 0.0)


_LOG_FLOOR = 1e-6


def delimitation_for(year: str) -> int:
    """Which delimitation an election was fought on.

    Wards are redrawn for each local election and stand until the next one, so
    the delimitation is the most recent LGE at or before the year: the 2019
    national election used the 2016 wards, the 2024 national the 2021 wards.
    """
    lge = [int(y) for y, e in cityconfig.CALENDAR.items()
           if e.kind == "LGE" and int(y) <= int(year)]
    return max(lge) if lge else int(year)


def composition_at(dim: Dimension, cfg: Config, when: float,
                   ward_codes: set[str] | None = None,
                   city: cityconfig.City | None = None,
                   election_year: str | None = None
                   ) -> tuple[dict[str, np.ndarray], str]:
    """Ward composition interpolated to a decimal year.

    Censuses are a decade apart and elections fall between them, so neither
    endpoint describes polling day: the 2016 election sits five years past
    Census 2011 and six short of Census 2022. Composition is interpolated in
    log-share space and renormalised, which keeps every result inside the
    simplex — linear interpolation of shares can leave it under extrapolation,
    and extrapolation is exactly what the 2026 forecast needs.

    Returns the composition and a one-line provenance string, because a number
    that was extrapolated four years past its source should say so wherever it
    is reported.
    """
    frames, notes = [], []
    for census in dim.censuses:
        comp = read_census(dim, census, cfg)
        # Ward codes are contiguous and REUSED, so a subset test always passes
        # and the old guard never fired — Census 2022's codes "match" the 2011
        # election's 130 wards perfectly, every one a different polygon. Compare
        # delimitations instead, which is the thing that actually differs.
        on_delimitation = (
            ward_codes is None or election_year is None
            or census.delimitation == delimitation_for(election_year))
        if not on_delimitation:
            # Published on a different delimitation. Ward codes would still
            # join — wrongly — so go through voting districts instead.
            if city is None or election_year is None:
                raise SystemExit(
                    f"{dim.name}: Census {census.year} is on the "
                    f"{census.delimitation} delimitation and the target wards "
                    f"are not; reprojection needs the city and election.")
            comp, covered = reproject(comp, city, str(census.delimitation),
                                      election_year)
            notes.append(f"Census {census.year} reprojected from the "
                         f"{census.delimitation} wards via VDs "
                         f"({covered:.1%} of the electorate mapped)")
            if ward_codes is not None and not set(comp) >= ward_codes:
                missing = len(ward_codes - set(comp))
                notes.append(f"{missing} ward(s) unmapped and dropped")
        frames.append((census, comp))

    if not frames:
        raise SystemExit(f"{dim.name}: no usable census")

    if len(frames) == 1:
        census, comp = frames[0]
        gap = when - census.year
        if abs(gap) > cfg.max_extrapolation:
            # A NOTE, NOT A BLOCKER. The census supplies composition only —
            # which pool a ward's people belong to. The *level* of every pool
            # comes from the registered roll, which is counted at every
            # election. So a distant census degrades the split, it does not
            # invalidate the count, and refusing to run cost us the only two
            # other targets we could have scored.
            notes.append(
                f"Census {census.year} used {abs(gap):.1f}y from the target, "
                f"past the {cfg.max_extrapolation:g}y guide — composition only, "
                f"pool sizes still come from the roll")
        how = (f"Census {census.year} held flat ({gap:+.1f}y; no second census "
               f"to establish a trend)")
        return comp, "; ".join(notes + [how])

    # Bracket the date where we can, else extrapolate off the nearest pair.
    years = [c.year for c, _ in frames]
    if when <= years[0]:
        i, j = 0, 1
    elif when >= years[-1]:
        i, j = len(frames) - 2, len(frames) - 1
    else:
        j = next(k for k, y in enumerate(years) if y >= when)
        i = j - 1

    (ca, fa), (cb, fb) = frames[i], frames[j]
    span = cb.year - ca.year
    t = (when - ca.year) / span
    inside = 0.0 <= t <= 1.0
    if not inside:
        # Damped: a decade of ward-level drift, extended straight, claims more
        # than the data supports.
        overshoot = t - 1.0 if t > 1 else t
        t = (1.0 + cfg.damping * overshoot) if t > 1 else (cfg.damping * t)

    shared = set(fa) & set(fb)
    if ward_codes is not None:
        shared &= ward_codes
    out = {}
    for code in shared:
        la = np.log(np.maximum(fa[code], _LOG_FLOOR))
        lb = np.log(np.maximum(fb[code], _LOG_FLOOR))
        v = np.exp(la + t * (lb - la))
        out[code] = v / v.sum()

    if inside:
        how = (f"interpolated between Census {ca.year} and {cb.year} "
               f"(t={t:.2f} toward {cb.year})")
    else:
        how = (f"extrapolated from the {ca.year}-{cb.year} trend, damped "
               f"x{cfg.damping:g} ({when - cb.year:+.1f}y past {cb.year})")
    return out, "; ".join(notes + [how])


def polling_decimal_year(year: str, city: cityconfig.City | None = None) -> float:
    """Polling day as a decimal year, without demanding council structure.

    ``cityconfig.Target`` refuses a year with no ``[structure.by_year]`` entry,
    which is right for a forecast — you cannot allocate seats in a council
    whose size you do not know — and wrong here. A national election does not
    elect a council, so requiring one silently dropped 2014, 2019 and 2024 from
    the registration series, which is most of it.
    """
    date = cityconfig.CALENDAR[year].date
    if city is not None:
        try:
            own = city.structure_for(year).get("election_date")
            if own and str(_date.fromisoformat(str(own)).year) == year:
                date = _date.fromisoformat(str(own))
        except SystemExit:
            pass
    start = _date(date.year, 1, 1).toordinal()
    end = _date(date.year + 1, 1, 1).toordinal()
    return date.year + (date.toordinal() - start) / (end - start)


def election_decimal_year(target: cityconfig.Target) -> float:
    """Polling day as a decimal year, so a November poll is not treated as
    January's composition."""
    d = target.date
    start = _date(d.year, 1, 1).toordinal()
    end = _date(d.year + 1, 1, 1).toordinal()
    return d.year + (d.toordinal() - start) / (end - start)


# --------------------------------------------------------------------------
# election data
# --------------------------------------------------------------------------
def ward_party_shares(city: cityconfig.City, year: str,
                      ballot: str = "PR") -> tuple[dict[str, dict[str, float]],
                                                   dict[str, float]]:
    """Ward -> {party: share}, and ward -> votes cast."""
    template = cityconfig.CALENDAR[year].results
    if template is None:
        raise SystemExit(f"{year} has no result file")
    path = city.path("raw", "elections", template)
    if not path.exists():
        raise SystemExit(f"no result file for {city.slug} {year}: {path}")

    tally: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") != ballot:
                continue
            ward = (row.get("Ward") or "").strip()
            if not ward:
                continue
            tally[ward][P.canonical(row["sPartyName"])] += int(float(row["Party_Votes"] or 0))

    shares, votes = {}, {}
    for ward, counts in tally.items():
        total = sum(counts.values())
        if total <= 0:
            continue
        votes[ward] = float(total)
        shares[ward] = {p: c / total for p, c in counts.items()}
    return shares, votes


# --------------------------------------------------------------------------
# the fit
# --------------------------------------------------------------------------
@dataclass
class PartyFit:
    party: str
    citywide: float
    rates: np.ndarray                     # appeal rate within each pool
    tilts: dict[str, np.ndarray] = field(default_factory=dict)
    r2: float = float("nan")
    bounds: np.ndarray | None = None      # (n_pools, 2) Duncan-Davis interval

    def composition(self, pool_votes: np.ndarray) -> np.ndarray:
        """Where the party's votes come from — shares summing to 1."""
        got = self.rates * pool_votes
        return got / got.sum() if got.sum() > 0 else got

    def identified(self, floor: float = 0.002) -> np.ndarray:
        """Per pool: is the fitted rate actually pinned down by the data?

        Two ways it is not. The deterministic bound may be wide — the ANC among
        white voters is 0-27.7%, so any point estimate in there is a choice, not
        a finding. Or the estimate may be sitting on the floor, which means the
        fit walked to the edge of what it was allowed and would have kept going:
        a floor stops a rate reading as impossible, but it does not make the
        number at the floor a measurement.
        """
        if self.bounds is None:
            return np.zeros(len(self.rates), dtype=bool)
        narrow = (self.bounds[:, 1] - self.bounds[:, 0]) < 0.25
        return narrow & (self.rates > floor * 1.5)


def _project_simplex(rows: np.ndarray) -> np.ndarray:
    """Euclidean projection of each row onto the probability simplex.

    Duchi et al.'s sort-and-threshold: the closest point with non-negative
    entries summing to one.
    """
    n = rows.shape[1]
    srt = np.sort(rows, axis=1)[:, ::-1]
    cs = np.cumsum(srt, axis=1) - 1.0
    idx = np.arange(1, n + 1)
    cond = srt - cs / idx > 0
    rho = n - 1 - np.argmax(cond[:, ::-1], axis=1)
    theta = cs[np.arange(rows.shape[0]), rho] / (rho + 1.0)
    return np.maximum(rows - theta[:, None], 0.0)


def fit_joint(E: np.ndarray, Y: np.ndarray, votes: np.ndarray, *,
              iters: int = 20000) -> np.ndarray:
    """Fit every party's pool rates at once, subject to what must be true.

    Fitting each party on its own is not a model of an election. It lets two
    parties both claim most of a pool while a third is pushed negative to
    balance the books, and nothing notices: measured on Johannesburg 2021 the
    independent fits assigned the white pool **111.4%** of its voters and the
    Coloured pool **90.4%**, claiming 106.1% of the vote in total, with Al
    Jama-ah at −1.9% ± 0.3 among white voters and the PA at −3.5% among Indian
    voters. Those negatives are tight, not noisy, which makes them
    misspecification rather than a lack of data.

    Two things must hold, and imposing them is also what identifies the small
    parties — a pool that must add to one says something about every party in
    it that no single-party regression can see:

    * **no negative votes**, so every rate is at least zero — the real floor,
      not the 0.2% fudge that used to stand in for one; and
    * **every voter votes for someone**, so each pool's rates sum to one.

    ``E`` is wards x pools (each ward's electorate composition), ``Y`` is
    wards x parties (vote shares), and the returned ``R`` is pools x parties.
    The projection onto the simplex enforces both constraints exactly at every
    iteration, so the answer satisfies them by construction rather than
    approximately.
    """
    sw = np.sqrt(votes / max(votes.sum(), 1e-12))
    Ew, Yw = E * sw[:, None], Y * sw[:, None]
    lipschitz = float(np.linalg.norm(Ew, 2) ** 2)
    if lipschitz <= 0:
        return np.full((E.shape[1], Y.shape[1]), 1.0 / Y.shape[1])
    step = 1.0 / lipschitz

    R = np.full((E.shape[1], Y.shape[1]), 1.0 / Y.shape[1])
    Z, t = R.copy(), 1.0
    for _ in range(iters):
        nxt = _project_simplex(Z - step * (Ew.T @ (Ew @ Z - Yw)))
        t_next = 0.5 * (1.0 + np.sqrt(1.0 + 4.0 * t * t))
        if float(((Z - nxt) * (nxt - R)).sum()) > 0:
            Z, t_next = nxt.copy(), 1.0
        else:
            Z = nxt + ((t - 1.0) / t_next) * (nxt - R)
        R, t = nxt, t_next

    gmap = lipschitz * (R - _project_simplex(R - step * (Ew.T @ (Ew @ R - Yw))))
    if float(np.abs(gmap).max()) > SOLVE_TOL * max(1.0, float(np.abs(R).max())):
        raise RuntimeError(
            f"joint pool fit did not converge in {iters} iterations: projected "
            f"gradient {np.abs(gmap).max():.3e}")
    return R


def balance_margins(R: np.ndarray, electorate: np.ndarray,
                    party_votes: np.ndarray, iters: int = 2000,
                    tol: float = 1e-12) -> np.ndarray:
    """Force both margins of the party x pool vote matrix to their known totals.

    Two totals are known exactly and neither is a modelling choice: each pool
    contains a known number of voters, and each party won a known number of
    votes. The constrained fit gets the first right by construction and the
    second only approximately — Al Jama-ah came out implying 1.3% of the vote
    against an actual 0.8%, the PA 3.7% against 3.0% — because a least-squares
    surface has no reason to respect a margin nobody told it about.

    Iterative proportional fitting scales rows and columns alternately until
    both hold. It preserves non-negativity and every zero, and lands on the
    matrix closest to the starting one in KL divergence, so it adjusts the fit
    rather than replacing it. It is the same procedure ``solve_and_predict``
    uses to calibrate voting districts to a citywide target.
    """
    counts = R * electorate[:, None]
    target_rows = electorate.astype(float)
    target_cols = party_votes.astype(float)

    # A party the fit zeroed in every pool can never be scaled back up — IPF
    # multiplies, and nothing times anything is nothing — so its votes stay
    # permanently unplaced and the margins never close. Three micro-parties did
    # this at national scale (Free Democrats 111 votes, Eastern Cape Movement
    # 98, Civic Independent 73), and the balancing stalled at exactly the
    # largest of them. Seed any such column proportionally to the pools: for a
    # party with no spatial signal at all, "its voters look like the electorate"
    # is the maximum-entropy answer, and IPF moves it from there.
    empty = (counts.sum(axis=0) <= 0) & (target_cols > 0)
    if empty.any():
        counts[:, empty] = (target_rows[:, None] / target_rows.sum()) * \
            target_cols[empty][None, :]
    # The margins must agree on the grand total or no solution exists.
    scale = target_rows.sum() / max(target_cols.sum(), 1e-12)
    target_cols = target_cols * scale

    for _ in range(iters):
        col = counts.sum(axis=0)
        counts *= np.divide(target_cols, col, out=np.ones_like(col),
                            where=col > 0)[None, :]
        row = counts.sum(axis=1)
        counts *= np.divide(target_rows, row, out=np.ones_like(row),
                            where=row > 0)[:, None]
        if (np.abs(counts.sum(axis=0) - target_cols).max() < tol * target_rows.sum()
                and np.abs(counts.sum(axis=1) - target_rows).max()
                < tol * target_rows.sum()):
            break
    else:
        raise RuntimeError("margin balancing did not converge")

    return counts / np.maximum(electorate, 1e-12)[:, None]


def _r2(y: np.ndarray, pred: np.ndarray, w: np.ndarray) -> float:
    mean = np.average(y, weights=w)
    denom = (((y - mean) ** 2) * w).sum()
    return 1.0 - (((y - pred) ** 2) * w).sum() / denom if denom > 0 else float("nan")


def bounds(y: np.ndarray, comp: np.ndarray, votes: np.ndarray) -> np.ndarray:
    """Duncan-Davis method of bounds: what the arithmetic alone allows.

    No model. In each ward the party's votes coming from pool g are at least
    (its votes minus everyone outside g) and at most (its votes, or all of g).
    Summing those over wards gives a hard interval on the citywide rate.

    Computed on the pools' *voters* rather than their population, so it no
    longer assumes pools vote at the same rate. Its *width* is the signal:
    where it spans most of the unit interval, ward data cannot see that pool.
    """
    n_pools = comp.shape[1]
    out = np.zeros((n_pools, 2))
    for g in range(n_pools):
        pool = comp[:, g] * votes
        party = y * votes
        lo = np.maximum(0.0, party - (votes - pool)).sum()
        hi = np.minimum(party, pool).sum()
        total = pool.sum()
        out[g] = (lo / total, hi / total) if total > 0 else (0.0, 1.0)
    return out


def fit_city(city: cityconfig.City, year: str, cfg: Config, *,
             admitted_only: bool = True,
             extra_tilts: list[Dimension] | None = None,
             party_list: list[str] | None = None):
    """Fit every party's pool vector from one city's ward results.

    Composition is taken as at that election's polling day, not as at whichever
    census happens to be lying around.
    """
    shares, votes = ward_party_shares(city, year)

    # The pool is a set of people and three nested subsets of it; the party
    # rates act on the innermost one, the people who actually voted.
    counts = pool_counts(city, year, cfg)
    for violation in counts.violations:
        print(f"  ! {violation}")

    base = cfg.base()
    tilt_dims = list(cfg.tilts(admitted_only=admitted_only))
    if extra_tilts:
        tilt_dims += [d for d in extra_tilts if d.name not in {t.name for t in tilt_dims}]

    wards = [w for w in counts.wards if w in shares]
    keep = [i for i, w in enumerate(counts.wards) if w in shares]
    if not wards:
        raise SystemExit(f"{city.slug} {year}: no ward joined the covariates")
    comp = counts.composition("voted")[keep]
    vote = np.array([votes[w] for w in wards])
    provenance = f"nested pool counts from {year}"

    if tilt_dims:
        raise SystemExit(
            f"the joint fit does not carry tilt dimensions yet "
            f"({', '.join(d.name for d in tilt_dims)}). No tilt is admitted, so "
            f"this is unreachable in production; it is a refusal rather than a "
            f"silent single-dimension fit.")

    universe = party_list or sorted({p for w in wards for p in shares[w]})
    universe = [p for p in universe
                if any(shares[w].get(p, 0.0) > 0 for w in wards)]
    Y = np.array([[shares[w].get(p, 0.0) for p in universe] for w in wards])

    # Every party at once, subject to what must be true: no negative votes, and
    # each pool's rates summing to one because every voter voted for someone.
    R = fit_joint(comp, Y, vote)
    pool_votes = (comp * vote[:, None]).sum(axis=0)
    party_votes = (Y * vote[:, None]).sum(axis=0)
    R = balance_margins(R, pool_votes, party_votes)

    fits: dict[str, PartyFit] = {}
    for i, party in enumerate(universe):
        y = Y[:, i]
        fits[party] = PartyFit(
            party=party,
            citywide=float(np.average(y, weights=vote)),
            rates=R[:, i],
            r2=_r2(y, comp @ R[:, i], vote),
            bounds=bounds(y, comp, vote),
        )

    pool_votes = (comp * vote[:, None]).sum(axis=0)
    return fits, {"wards": wards, "comp": comp, "votes": vote,
                  "shares": shares, "tilt_dims": tilt_dims, "counts": counts,
                  "pool_votes": pool_votes, "categories": base.categories,
                  "provenance": provenance, "year": year,
                  "rates": counts.rates}


# --------------------------------------------------------------------------
# emitting the scenario the simulation actually draws from
# --------------------------------------------------------------------------
METRO_CODES = ("JHB", "TSH", "EKU", "ETH", "CPT", "MAN", "NMA", "BUF")


def metro_file(code: str, year: str) -> Path | None:
    for candidate in (Path(f"data/raw/elections/_metros/lge{year}_{code}_vd_party.csv"),
                      Path(f"data/raw/elections/_reports/"
                           f"lge{year}_{code}_downloadable_party_results.csv")):
        if candidate.exists():
            return candidate
    return None


def metro_citywide(code: str, year: str, ballot: str = "PR") -> dict[str, float]:
    """One metro's citywide party shares, through the same cleaner the city
    pipeline uses — the raw files have carried thousands separators that parse
    as a silent 68% vote loss."""
    from ingest_lge import read_municipality

    path = metro_file(code, year)
    if path is None:
        return {}
    counts: dict[str, int] = defaultdict(int)
    for row in read_municipality(path, code, ballot):
        counts[P.canonical(row["sPartyName"])] += int(row["Party_Votes"] or 0)
    total = sum(counts.values())
    return {p: c / total for p, c in counts.items()} if total else {}


def metro_ward_shares(code: str, year: str, ballot: str = "PR"
                      ) -> tuple[dict[str, dict[str, float]], dict[str, float]]:
    """One metro's ward-level party shares and votes cast."""
    from ingest_lge import read_municipality

    path = metro_file(code, year)
    if path is None:
        return {}, {}
    tally: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in read_municipality(path, code, ballot):
        ward = (row["Ward"] or "").strip()
        if ward:
            tally[ward][P.canonical(row["sPartyName"])] += int(row["Party_Votes"] or 0)
    shares, votes = {}, {}
    for ward, counts in tally.items():
        total = sum(counts.values())
        if total > 0:
            votes[ward] = float(total)
            shares[ward] = {p: c / total for p, c in counts.items()}
    return shares, votes


def turnout_record(city: cityconfig.City, cfg: Config, before: str | None = None,
                   kind: str = "LGE") -> dict[str, np.ndarray]:
    """Turnout per pool at every prior election of one kind.

    This is the quantity that decides how big a pool is on the day, and it is
    measured, not inferred. Johannesburg, per pool::

        year  kind   Black Afr  Coloured  Indian  White   overall
        2011  LGE      50.8%     60.3%    45.2%   63.6%    54.2%
        2016  LGE      50.2%     64.7%    58.7%   69.3%    56.0%
        2021  LGE      36.4%     54.3%    40.8%   52.7%    41.6%
        2014  NPE      70.4%     75.0%    62.6%   77.6%    71.9%
        2024  NPE      56.5%     63.4%    62.8%   69.2%    60.2%

    Local elections run fifteen to twenty points below national ones, which is
    why ``kind`` filters: a local forecast learns nothing useful from national
    turnout levels. Black African turnout is consistently the lowest and white
    the highest, and 2021 was a collapse across every pool at once — which is
    the correlated shock the model has never had.
    """
    out: dict[str, np.ndarray] = {}
    for year, election in sorted(cityconfig.CALENDAR.items()):
        if election.kind != kind or not election.results:
            continue
        if before is not None and int(year) >= int(before):
            continue
        try:
            out[year] = pool_counts(city, year, cfg).rates["turnout"]
        except SystemExit:
            continue
    return out


def turnout_band(record: dict[str, np.ndarray], n_pools: int,
                 ) -> list[tuple[float, float, float]]:
    """(low, mode, high) turnout per pool: last election, widened by history.

    Two things the record has to be read carefully for.

    **Turnout is strongly serially correlated**, so the last local election is
    a far better centre than the mean of all of them. Johannesburg's Black
    African pool ran 50.8%, 50.2%, then 36.4% — centring on 45.8% would forecast
    a recovery nobody has evidence for.

    **But 2021 is the LOWEST on record for every pool**, so taking the
    historical minimum as the floor would make the band one-sided: turnout
    could rise and never fall. A sample without a further decline in it is a
    limit of the sample, not evidence that decline cannot happen — the same
    error that gave the old bloc ranges a floor they could never cross. So the
    WIDTH comes from history and the CENTRE from the last election: the band is
    the last election's turnout times the historical log-range either way, with
    the top capped at the highest turnout the city has actually recorded.
    """
    if not record:
        return [(0.30, 0.50, 0.70)] * n_pools
    years = sorted(record)
    arr = np.array([record[y] for y in years])
    previous = arr[-1]
    bands = []
    for g in range(n_pools):
        column = np.maximum(arr[:, g], 1e-6)
        centre = float(previous[g])
        # half the observed log-range: the width history supports, symmetric
        # so a further decline is never assigned probability zero
        spread = float(np.log(column.max() / column.min())) if len(column) > 1 else 0.30
        low = centre * float(np.exp(-spread))
        high = min(centre * float(np.exp(spread)), float(column.max()))
        bands.append((low, centre, max(high, centre * 1.001)))
    return bands


def turnout_limits(record: dict[str, np.ndarray], registered: np.ndarray,
                   margin: float = 0.10) -> dict:
    """What a reader may set turnout to, and the rule tying the two sliders.

    The interactive offers a citywide turnout slider and a per-pool one. Both
    are bounded by what the city has actually done, plus a ``margin`` either
    way — a reader may explore a turnout ten per cent below the worst on record
    or ten per cent above the best, and no further, because beyond that they
    are not adjusting this model's assumption but inventing a different city.

    The two must agree. Per-pool turnouts imply a citywide figure — the
    registration-weighted mean — and a reader who moves every pool to its
    ceiling has implicitly moved the citywide slider too. So the pool sliders
    are constrained to combinations whose weighted mean lies inside the
    citywide range; :func:`constrain_pool_turnout` performs that projection.
    """
    if not record or registered.sum() <= 0:
        return {}
    years = sorted(record)
    arr = np.array([record[y] for y in years])
    citywide = (arr * registered[None, :]).sum(axis=1) / registered.sum()
    return {
        "city": {"low": float(citywide.min() * (1 - margin)),
                 "high": float(citywide.max() * (1 + margin)),
                 "observed_low": float(citywide.min()),
                 "observed_high": float(citywide.max()),
                 "previous": float(citywide[-1])},
        "pool": [{"low": float(arr[:, g].min() * (1 - margin)),
                  "high": float(arr[:, g].max() * (1 + margin)),
                  "observed_low": float(arr[:, g].min()),
                  "observed_high": float(arr[:, g].max()),
                  "previous": float(arr[-1, g])}
                 for g in range(arr.shape[1])],
        "margin": margin,
    }


def constrain_pool_turnout(pool_turnout: np.ndarray, registered: np.ndarray,
                           limits: dict) -> tuple[np.ndarray, str]:
    """Project a reader's per-pool turnouts back inside the citywide range.

    Moving every pool to its ceiling implies a citywide turnout above anything
    the city has recorded, which the citywide slider does not permit — so the
    per-pool sliders must not be a way around it. When the implied citywide
    figure falls outside the allowed range the whole vector is scaled onto the
    nearest edge, which preserves the reader's *relative* judgement about which
    pools turn out and only overrides the level they did not mean to set.
    """
    if not limits or registered.sum() <= 0:
        return pool_turnout, ""
    implied = float((pool_turnout * registered).sum() / registered.sum())
    low, high = limits["city"]["low"], limits["city"]["high"]
    if low <= implied <= high:
        return pool_turnout, ""
    edge = low if implied < low else high
    scaled = pool_turnout * (edge / implied)
    return scaled, (f"pool turnouts implied a citywide {implied:.1%}, outside "
                    f"the permitted {low:.1%}-{high:.1%}; scaled to {edge:.1%} "
                    f"keeping their relative pattern")


def registered_at_target(city: cityconfig.City, target: cityconfig.Target,
                         cfg: Config, fitted_on: str) -> np.ndarray:
    """How many registered voters each pool holds at the target.

    Not a forecast. The roll is published per voting district before polling
    day, and each ward's pool composition comes from that ward's own data, so
    a pool's size is *counted* rather than drawn::

        registered at target  x  that ward's pool composition  =  pool size

    This replaces the pool "ratio" — a triangular fitted to two historical
    transitions that stood in for population change, registration change and
    turnout change all at once, and that had to be borrowed from other cities
    to have any sample at all. None of that is necessary: two of the three
    terms are known, and the third (turnout) is measured separately and drawn.
    """
    counts = pool_counts(city, fitted_on, cfg)
    composition = counts.composition("registered")
    by_ward = {w: composition[i] for i, w in enumerate(counts.wards)}

    roll = _target_roll(city, target)
    if not roll:
        # No published roll yet: fall back to the fitting election's own, and
        # say so. Better a stated stand-in than a silent one.
        print(f"  ! no {target.year} roll on disk; pool sizes taken from "
              f"{fitted_on}'s roll instead")
        return counts.totals("registered")

    total = np.zeros(len(counts.categories))
    unmatched = 0.0
    for ward, registered in roll.items():
        if ward in by_ward:
            total += by_ward[ward] * registered
        else:
            unmatched += registered
    if unmatched > 0.01 * sum(roll.values()):
        print(f"  ! {unmatched / sum(roll.values()):.1%} of the {target.year} "
              f"roll is in wards with no measured composition")
    return total


def _target_roll(city: cityconfig.City, target: cityconfig.Target,
                 ) -> dict[str, float]:
    """Ward -> registered voters at the target, from whichever roll exists."""
    if cityconfig.CALENDAR[target.year].results:
        try:
            return ward_totals(city, target.year)[0]
        except SystemExit:
            pass
    path = target.processed / f"vd_ward_{target.year}.csv"
    if not path.exists():
        path = Path("data/processed") / f"vd_ward_{target.year}.csv"
    if not path.exists():
        return {}
    roll: dict[str, float] = defaultdict(float)
    seen: set[str] = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            vd = (row.get("VD_Number") or "").strip()
            ward = (row.get("WardID_" + target.year) or row.get("Ward") or "").strip()
            if not vd or not ward or vd in seen:
                continue
            seen.add(vd)
            roll[ward] += float(row.get("vd_registered") or 0)
    return dict(roll)


def pool_totals(composition: dict[str, np.ndarray], shares: dict[str, float],
                n_pools: int) -> np.ndarray:
    """Each pool's share of the total vote.

    A pool's total is its members' weighted contributions, so a party drawing
    half its vote from one pool brings half its share to it. This is the same
    arithmetic ``montecarlo.pool_spec`` does, kept identical on purpose.
    """
    total = np.zeros(n_pools)
    for party, weight in composition.items():
        total += weight * shares.get(party, 0.0)
    return total


def lge_transitions(before: str | None = None) -> tuple[tuple[str, str], ...]:
    """Consecutive local-election pairs, optionally ending before a target.

    A range measured on the transition it is about to predict is not a prior.
    These were hard-coded, so a 2021 backtest measured its pool ratios partly
    on 2016->2021 — the target itself.
    """
    years = sorted((y for y, e in cityconfig.CALENDAR.items()
                    if e.kind == "LGE" and e.results), key=int)
    pairs = tuple(zip(years, years[1:]))
    if before is None:
        return pairs
    return tuple(p for p in pairs if int(p[1]) < int(before))


def measure_pool_ratios(composition: dict[str, np.ndarray], n_pools: int,
                        transitions=None, codes=None) -> list[list[float]]:
    """How much a pool's vote total moves between elections, IN ONE CITY.

    ``codes`` defaults to nothing and the caller must name the city, because
    this function takes ONE ``composition`` — one city's fitted party-to-pool
    weights — and an earlier version defaulted to all eight metros. That
    applied Johannesburg's mapping to Cape Town's, eThekwini's and Mangaung's
    party shares and called the result those cities' pool ratios. It measured a
    quantity that describes no city: in Johannesburg the PA draws ~94% of its
    vote from the Coloured pool, while in Cape Town the DA, GOOD and the PA
    occupy that pool completely differently.

    The transposed ranges were also WIDER on three of four pools (Black African
    0.87-1.01 against Johannesburg's own 0.94-1.01), so the model was importing
    volatility from cities whose pool structure it then ignored.

    A pool is local. Its composition comes from that city's wards, its size
    from that city's registration roll, and its movement from that city's own
    history. Restricting to one city costs sample size — two transitions rather
    than sixteen — and the honest answer to a thin sample is a wider interval,
    not a borrowed one.
    """
    if transitions is None:
        transitions = lge_transitions()
    if not codes:
        raise ValueError(
            "measure_pool_ratios needs the city whose composition it was given. "
            "Passing several metros applies one city's party-to-pool weights to "
            "another city's votes, which measures nothing real.")
    ratios: list[list[float]] = [[] for _ in range(n_pools)]
    for code in codes:
        for before, after in transitions:
            a = metro_citywide(code, before)
            b = metro_citywide(code, after)
            if not a or not b:
                continue
            ta = pool_totals(composition, a, n_pools)
            tb = pool_totals(composition, b, n_pools)
            for g in range(n_pools):
                if ta[g] > 1e-6:
                    ratios[g].append(float(tb[g] / ta[g]))
    return ratios


def dirichlet_alpha(splits: list[np.ndarray], min_share: float = 0.01) -> float:
    """Method of moments: alpha + 1 = m(1-m)/Var, over members that matter.

    ``min_share`` is not a tidying detail. A pool has forty-odd members and
    most are parties polling a fraction of a percent whose share is stable
    simply because it is tiny; taking the median across all of them returns the
    behaviour of the noise floor, not of the pool. Estimated that way every
    pool pinned to the 200 ceiling, which would have made the simulation far
    more confident than the evidence warrants — the opposite of what a
    concentration parameter is for.
    """
    if len(splits) < 3:
        return 12.0
    arr = np.array(splits)
    m = arr.mean(axis=0)
    v = arr.var(axis=0, ddof=1)
    usable = (v > 1e-12) & (m > min_share) & (m < 1 - 1e-4)
    if usable.sum() < 2:
        usable = (v > 1e-12) & (m > 1e-3) & (m < 1 - 1e-4)
    if not usable.any():
        return 12.0
    est = (m[usable] * (1 - m[usable]) / v[usable]) - 1.0
    # Weight by member size: the pool's dispersion is what its large members do.
    return float(np.clip(np.average(est, weights=m[usable]), 1.0, 200.0))


def entrant_record(transitions, codes=METRO_CODES) -> list[float]:
    """Every share won by a party that was not there at the previous election.

    The record, not a judgement. A party arriving from nothing is the single
    largest error the model makes — ActionSA won 44 of Johannesburg's 270 seats
    in 2021 and the model gave it zero, because it held 0.0000% of the 2019
    baseline and multiplicative growth cannot lift a party off zero. The same
    happened to the PA's 8 seats. Between them that is the whole of the model's
    112-seat absolute error at that target.
    """
    seen: list[float] = []
    for code in codes:
        for before, after in transitions:
            a, b = metro_citywide(code, before), metro_citywide(code, after)
            if not a or not b:
                continue
            reach = _ward_reach(code, after)
            for party, share in b.items():
                if a.get(party, 0.0) <= 1e-4 < share:
                    seen.append((share, reach.get(party, 1.0)))
    return sorted(seen)


def _ward_reach(code: str, year: str) -> dict[str, float]:
    """Fraction of wards each party fielded a ward candidate in."""
    from ingest_lge import read_municipality
    path = metro_file(code, year)
    if path is None:
        return {}
    wards: dict[str, set] = defaultdict(set)
    seen: set = set()
    for row in read_municipality(path, code, "Ward"):
        ward = (row.get("Ward") or "").strip()
        if not ward:
            continue
        seen.add(ward)
        if int(float(row.get("Party_Votes") or 0)) > 0:
            wards[P.canonical(row["sPartyName"])].add(ward)
    return {p: len(w) / len(seen) for p, w in wards.items()} if seen else {}


def splinter_record(city: cityconfig.City,
                    pairs=(("COPE", "ANC", "2004", "2009"),
                           ("EFF", "ANC", "2009", "2014"),
                           ("MK", "ANC", "2019", "2024"))) -> list[float]:
    """What share of its parent's vote each known splinter took, measured.

    The three splits this city has on record, each as the splinter's first
    result over the parent's previous one::

        COPE from the ANC   9.61% against 68.56%   0.140
        EFF  from the ANC  10.13% against 62.35%   0.162
        MK   from the ANC  12.22% against 49.62%   0.246

    Which party split from which is a judgement and is declared here with its
    evidence; how much it took is not, and is measured. An earlier version of
    this used one half, which was invented and three times too large.
    """
    out = []
    for splinter, parent, before, after in pairs:
        a, b = metro_citywide(city.code, before), metro_citywide(city.code, after)
        if not a or not b:
            a = a or _npe_citywide(city, before)
            b = b or _npe_citywide(city, after)
        if a.get(parent, 0) > 0 and b.get(splinter, 0) > 0:
            out.append(b[splinter] / a[parent])
    return sorted(out)


def _npe_citywide(city: cityconfig.City, year: str) -> dict[str, float]:
    template = cityconfig.CALENDAR[year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        return {}
    counts: dict[str, int] = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") in (None, "", "PR"):
                counts[P.canonical(row["sPartyName"])] += int(
                    float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()} if total else {}


def contesting_parties(city: cityconfig.City, year: str) -> set[str]:
    """Who is on the ballot at the target. Names only, never votes.

    Nomination lists close and are published weeks before polling day, so the
    roster is available to a forecaster; the results are not. Taking the names
    from the result file is therefore legitimate, and taking anything else from
    it would not be.

    Without this a genuine entrant can never be seeded, because it is absent
    from the baseline entirely and the earlier code looked for newcomers among
    baseline parties. ActionSA held no 2019 national vote at all, so it never
    reached the seeding logic and stayed at zero all the way to a 44-seat miss.
    """
    template = cityconfig.CALENDAR[year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        return set()
    out = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            out.add(P.canonical(row["sPartyName"]))
    return out


def arrival_rules(newcomers: set[str], lineage: dict[str, dict],
                  rates: np.ndarray, universe: list[str], categories,
                  record: list[tuple[float, float]],
                  splinter_fractions: list[float], pool_size: np.ndarray,
                  contestation: dict[str, float] | None = None,
                  ) -> tuple[dict[str, dict], dict[str, str]]:
    """How a party that was not here last time takes its votes.

    **A splinter takes votes out of POOLS, not out of a named party.** It
    inherits its parent's pool weights — that is what makes it a splinter — and
    captures a share of each pool its parent draws on. Everyone holding that
    pool then loses in proportion to the weight they hold there, which falls
    out of the simplex constraint for free: the pool's rates must sum to one,
    so inserting a party at rate ``r`` scales every other party by ``1 - r``.

    The parent loses most because it holds most, but it is never named and
    never singled out. If MK takes Black African votes, every party with Black
    African votes gives some up, in proportion. The previous version debited
    the parent by name for the whole amount, which is a claim about two parties
    rather than about an electorate, and it is not how a defection works.

    Capture size comes from the record — the three splits this city has seen
    took 0.140, 0.162 and 0.246 of their parent's vote — and is a band, not a
    point, because the user is expected to have a view. MK draining the ANC's
    Zulu support was obvious to any observer in 2024 and invisible to this
    model; when home-language pools exist the same mechanism will express it by
    leaning the inherited weights, which is a judgement and is meant to be.

    **An entrant has no parent, so it has no pool weights, and the default —
    an even share of every pool — is almost certainly wrong.** It is deliberate:
    the flat default makes the absence of a judgement visible instead of
    convenient, and the question the user must answer is a specific one, which
    ``judgements/`` now asks in as many words: *which pools does this party pull
    from, and how much support do you expect?* Its size defaults inside the
    range other arrivals have managed, scaled by how much of the city it
    actually contests — a party fielding candidates in a third of the wards
    cannot win what one fielding everywhere can.

    Returns, per party, a dict of ``pool -> capture rate`` plus the band on the
    whole thing, and a note explaining where each number came from.
    """
    if not record:
        return {}, {}
    # AN ARRIVAL'S SIZE SCALES WITH HOW MUCH OF THE CITY IT CONTESTS. The
    # record is dominated by parties that fielded candidates in a handful of
    # wards, so its raw median (0.08%) describes a micro-party, not a serious
    # entrant. Measuring yield PER WARD CONTESTED and multiplying by the new
    # party's own reach is what separates ActionSA, on 99% of wards, from a
    # party on 5% of them.
    # CONTESTATION MOVES YOU UP THE BAND. Measured across eight metros: an
    # arrival contesting under a tenth of the wards sits at the 23rd percentile
    # of all arrivals, one contesting over 90% at the 86th. Correlation on logs
    # +0.44. Every wide-contesting arrival that mattered is in that top group —
    # ActionSA 18.1% in Johannesburg, the EFF 11.6/11.1/10.9% across three
    # metros, GOOD 3.7% in Cape Town.
    #
    # But it does not separate a serious party from a shell. Of the 45 arrivals
    # on more than 90% of wards, only about fourteen cleared 1%; the rest are
    # vanity registrations that field candidates everywhere and win nothing,
    # which is why that group's median is only 0.49%. So the default places a
    # party by its reach and no further, and the judgement layer is where
    # "this one is real" gets said.
    #
    # Note what is NOT here: a declining party. COPE contested 96-100% of wards
    # in several metros while falling 1.11% to 0.21%, and never appears in this
    # record at all, because it always held a prior share. Contestation predicts
    # ARRIVAL, not survival.
    all_shares = [s for s, _ in record]

    def comparators(reach: float | None) -> list[float]:
        """Arrivals that contested about as much of the city as this one."""
        if reach is None:
            return all_shares
        near = [s for s, r in record if abs(r - reach) < 0.25]
        return near if len(near) >= 8 else all_shares
    f_lo, f_mid, f_hi = ((min(splinter_fractions),
                          float(np.median(splinter_fractions)),
                          max(splinter_fractions)) if splinter_fractions
                         else (lo_e, mid_e, hi_e))
    index = {p: i for i, p in enumerate(universe)}
    n_pools = len(categories)

    rules: dict[str, dict] = {}
    notes: dict[str, str] = {}
    for party in sorted(newcomers):
        declared = lineage.get(party, {})
        parent = (declared.get("parent") or "").strip().upper()
        weights = declared.get("weights")
        reach = (contestation or {}).get(party)

        if weights:
            vec = np.array([float(w) for w in weights], dtype=float)
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n_pools, 1.0 / n_pools)
            size = float(declared.get("support", mid_e))
            capture = _capture_from_share(vec, size, pool_size)
            why = "pools and support declared in judgements/"
        elif parent and parent in index:
            # The parent's own rates ARE its pool weights. Capturing f of each
            # is what "inherits the parent's split" means, and the pool
            # renormalisation does the rest.
            capture = {categories[g]: float(f_mid * rates[g, index[parent]])
                       for g in range(n_pools) if rates[g, index[parent]] > 0}
            why = (f"splinter: takes {f_mid:.1%} of {parent}'s share of each "
                   f"pool it draws on, band {f_lo:.1%}-{f_hi:.1%} from the "
                   f"COPE/EFF/MK record. Every party in those pools gives up "
                   f"the same proportion; none is named.")
        else:
            vec = np.full(n_pools, 1.0 / n_pools)
            reach_used = reach if reach is not None else 0.5
            # Reach chooses the PLACE in the band, not a multiplier on it: a
            # party on 99% of wards is placed near the top of what arrivals
            # like it have managed, one on 10% near the bottom.
            peers = comparators(reach)
            place = float(np.clip(reach_used, 0.05, 0.95))
            size = float(np.quantile(peers, place))
            lo_e = float(np.quantile(peers, 0.25))
            hi_e = float(np.quantile(peers, 0.95))
            # A judgement may say this one is unlike its comparators. Mashaba
            # had been mayor of this city and was widely liked; nothing
            # measurable said so, and doubling the default would have put
            # ActionSA at 18.4% against an actual 18.12%.
            size *= float(declared.get("overperform", 1.0))
            capture = _capture_from_share(vec, size, pool_size)
            mult = float(declared.get("overperform", 1.0))
            why = (f"entrant: even share of every pool. Placed at the "
                   f"{place:.0%} mark of comparable arrivals "
                   f"({lo_e:.2%}-{hi_e:.2%}) because it contests "
                   f"{reach_used:.0%} of wards, giving {size:.2%}"
                   + (f" after a x{mult:g} judgement" if mult != 1.0 else "")
                   + ". THE EVEN SPREAD IS A PLACEHOLDER: declare which pools "
                     "it pulls from and what support you expect.")
        centre = max(size, 1e-9) if not parent else 1.0
        rules[party] = {"capture": capture,
                        "band": [f_lo / f_mid, 1.0, f_hi / f_mid] if parent
                                else [lo_e / centre, 1.0, hi_e / centre]}
        notes[party] = why
    return rules, notes


def _reach_of(contestation) -> float:
    """The reach this arrival has, when one is known."""
    if isinstance(contestation, (int, float)):
        return float(contestation)
    return 1.0


def _capture_from_share(weights: np.ndarray, share: float,
                        pool_size: np.ndarray) -> dict:
    """Turn "x% of the city, spread across pools like this" into a rate per pool.

    To win ``share`` of the city with its votes distributed as ``weights``, a
    party needs ``share * w_g * total`` votes out of pool ``g``, which is a rate
    of that over the pool's own size. A pool holding 4% of the electorate must
    give up far more of itself than one holding 65% to yield the same citywide
    number, which is exactly why a flat pool spread is such a strong assumption.
    """
    total = weights.sum()
    if total <= 0 or pool_size.sum() <= 0:
        return {}
    weights = weights / total
    electorate = pool_size.sum()
    out = {}
    for g, w in enumerate(weights):
        if w > 0 and pool_size[g] > 0:
            out[g] = float(min(share * w * electorate / pool_size[g], 0.9))
    return out


def apply_arrivals(rates: np.ndarray, universe: list[str], rules: dict[str, dict],
                   scale: float = 1.0) -> tuple[np.ndarray, list[str]]:
    """Insert each arrival into the pools it captures from.

    THE MECHANISM, in one line: a party entering pool ``g`` at rate ``r`` leaves
    ``1 - r`` for everyone already there, shared out in proportion to what each
    already held. Nobody is named and nobody is singled out; the parent loses
    most only because it held most.

    ``scale`` multiplies every capture, which is how a draw expresses "this
    arrival did better or worse than the central case" without changing who it
    takes from.
    """
    if not rules:
        return rates, universe
    out = rates.copy()
    names = list(universe)
    for party, rule in rules.items():
        column = np.zeros(out.shape[0])
        for g, r in rule["capture"].items():
            g = int(g)
            take = float(np.clip(r * scale, 0.0, 0.95))
            if take <= 0:
                continue
            out[g, :] *= (1.0 - take)      # everyone in the pool, in proportion
            column[g] = take
        out = np.hstack([out, column[:, None]])
        names.append(party)
    return out, names


def lineage_path(city: cityconfig.City, target: cityconfig.Target) -> Path:
    return Path("judgements") / f"{city.slug}-{target.year}.toml"


def load_lineage(city: cityconfig.City, target: cityconfig.Target) -> dict[str, dict]:
    path = lineage_path(city, target)
    if not path.exists():
        return {}
    raw = tomllib.loads(path.read_text())
    return {k: v for k, v in (raw.get("party") or {}).items()}


def write_lineage_template(city: cityconfig.City, target: cityconfig.Target,
                           newcomers: dict[str, float], existing: dict[str, dict],
                           pools_named: list[str]) -> Path:
    """Ask for the judgements the model cannot make, with defaults filled in.

    A party in the target's baseline that did not contest the fitting election
    has no measured pool vector, and the model has no way to learn one. There
    are exactly two defensible defaults and choosing between them is a human
    call: a **splinter** is defined identically to its parent and takes votes
    accordingly, an **entrant** defaults to an even share of every pool. Both
    defaults are usually wrong in an interesting way — it was obvious to any
    observer that MK would drain the ANC's Zulu support specifically, and
    nothing in the data could have said so before the fact.

    So the file is generated with the model's default and left for a human to
    override. After the election the vector is measured and the judgement is
    retired.
    """
    path = lineage_path(city, target)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return path

    lines = [
        f"# Judgements for {city.name}, target {target.year}.",
        "#",
        "# These parties will be on the ballot and did not contest the election",
        "# the pool weights were fitted on, so nothing measured says who votes",
        "# for them. THE MODEL CANNOT ANSWER THIS. You can.",
        "#",
        "# TWO QUESTIONS PER PARTY:",
        "#",
        "#   1. WHICH POOLS DOES IT PULL FROM?",
        "#      Set `parent` and it inherits that party's pool weights — which",
        "#      is what a splinter is. It then takes its votes OUT OF THOSE",
        "#      POOLS, and every party holding them gives up the same",
        "#      proportion of what it held. No party is singled out: the parent",
        "#      loses most only because it holds most.",
        "#      Or set `weights` directly, in the order",
        f"#        {', '.join(pools_named)}",
        "#      normalised, so [0, 0, 0, 1] means 'entirely the last pool'.",
        "#      Leave both unset and it takes an even share of every pool,",
        "#      which is almost certainly wrong and is meant to look wrong.",
        "#",
        "#   2. HOW MUCH SUPPORT DO YOU EXPECT?",
        "#      `support` is its share of the city. The default is what",
        "#      arrivals have historically won per ward contested, times the",
        "#      wards this one is contesting — so it rises with reach and falls",
        "#      without it. Override when you know something the record does",
        "#      not: ActionSA in 2021 was led by a popular former mayor of this",
        "#      city and took 18.12%, against a default near a third of one per",
        "#      cent. Nothing measurable could have said so; a person could.",
        "#",
        "# Every override is recorded in the run's provenance, and should be",
        "# deleted once the election has been held and the weights measured.",
        "",
    ]
    for party, share in sorted(newcomers.items(), key=lambda kv: -kv[1]):
        lines += [
            f"[party.{party}]",
            f"baseline_share = {share:.4f}",
            'parent = ""      # e.g. "ANC" to inherit the ANC\'s pool vector',
            f'# weights = [{", ".join("0.0" for _ in pools_named)}]',
            "",
        ]
    path.write_text("\n".join(lines))
    return path


def emit_pools(city: cityconfig.City, target: cityconfig.Target, cfg: Config,
               *, from_year: str | None = None) -> dict:
    """Build the ``scenario["pools"]`` structure from measurement.

    A pool is a body of voters, and a party's membership of it is the measured
    share of its vote that comes from there — not a list of parties someone
    decided trade with each other.
    """
    year = from_year or target.previous_lge or target.year
    fits, ctx = fit_city(city, year, cfg)
    cats = list(ctx["categories"])
    n = len(cats)

    # Size the pools as they will be at the TARGET, not as they were at the
    # election the rates were fitted on. The roll is counted every cycle and
    # the census is not, so the trend comes from the roll; `before` keeps a
    # backtest from seeing its own target's registration.
    series = registration_series(city, cfg, before=target.year)
    target_shares, roll_note = projected_pool_shares(series, target.year)
    composition = {p: f.composition(target_shares) for p, f in fits.items()}

    # --- parties with no measured vector -------------------------------------
    # The baseline is the election the forecast starts from; the pool vectors
    # come from the preceding LGE. Anything in the first and not the second —
    # MK is 12.2% of the 2024 baseline and did not exist in 2021 — has no
    # measured vector. Left alone it is in no pool at all, falls through to the
    # residual bucket, and gets drawn against a range meant for minor parties.
    baseline = {}
    if target.previous_npe:
        path = city.path("raw", "elections",
                         cityconfig.CALENDAR[target.previous_npe].results)
        if path.exists():
            counts: dict[str, int] = defaultdict(int)
            with open(path, encoding="utf-8", errors="replace") as fh:
                for row in csv.DictReader(fh):
                    counts[P.canonical(row["sPartyName"])] += int(
                        float(row.get("Party_Votes") or 0))
            total = sum(counts.values())
            baseline = {p: c / total for p, c in counts.items()} if total else {}

    # Who is on the ballot at the target, minus who already has a measured
    # vector. Taken from the roster, not the baseline: a genuine entrant is
    # absent from the baseline entirely, so looking there could never find one
    # — which is exactly how ActionSA stayed at zero into a 44-seat miss.
    # Who needs a vector, and who needs a LEVEL, are two different questions,
    # and conflating them broke both halves.
    #
    # `composition` holds a pool vector for every party that contested the
    # fitting election. A party missing from it needs one — that is `no_vector`.
    # MK is in that set for a 2026 target, because it did not exist in 2021.
    #
    # But MK is NOT a party with no level: it holds 12.22% of the 2024 baseline.
    # Seeding it as though it were added a second copy of a split that is
    # already in the baseline numbers — MK started at 12.22% + 15.98% = 28.20%
    # while the ANC was debited to 15.98%, half its measured share, which is
    # why this code produced ANC 36 / MK 68. A seed is for a party with NO
    # baseline; everyone else already has their level from the baseline itself.
    roster = contesting_parties(city, target.year)
    roster_is_real = bool(roster)
    if not roster:
        # A target that has not happened has no result file and therefore no
        # roster. Falling through with an empty set silently deleted every seed
        # from the 2026 spec — the live forecast — while the backtests, which do
        # have a roster, looked fine. Fall back to the baseline plus anyone
        # already carrying a pool vector, and say so.
        roster = set(baseline) | set(composition)
        print(f"  ! no published roster for {target.year} (it has not been "
              f"held). Parties in the {target.previous_npe} baseline still get "
              f"a pool vector, but NO GENUINE ENTRANT CAN BE FOUND: a party "
              f"contesting {target.year} with no {target.previous_npe} vote is "
              f"invisible here, and ActionSA in 2021 was exactly that. Declare "
              f"one in {lineage_path(city, target)}, or point this at the "
              f"published nomination list.")
    no_vector = {p for p in roster
                 if p not in composition and p not in ("IND", "ENTRANT")}
    # A seed is only for a party with no level to start from.
    newcomers = {p for p in no_vector if baseline.get(p, 0.0) <= 0.0}
    lineage = load_lineage(city, target)
    inherited: dict[str, str] = {}
    for party in sorted(no_vector):
        rule = lineage.get(party, {})
        weights = rule.get("weights")
        parent = (rule.get("parent") or "").strip().upper()
        if weights:
            vec = np.array([float(w) for w in weights], dtype=float)
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n, 1.0 / n)
            inherited[party] = "judged weights"
        elif parent and parent in composition:
            # A splinter is defined identically to its parent until the numbers
            # say otherwise.
            vec = composition[parent].copy()
            inherited[party] = f"splinter of {parent}"
        else:
            # An entrant draws an even share of every pool. Almost certainly
            # wrong, and deliberately so: it is the assumption that makes the
            # absence of a judgement visible rather than convenient.
            vec = np.full(n, 1.0 / n)
            inherited[party] = ("entrant, even share of every pool"
                                + (f" (parent {parent!r} not measured)"
                                   if parent else ""))
        composition[party] = vec

    # A pool's size at the target is COUNTED, not drawn: the published roll,
    # split by each ward's own composition. What is uncertain is turnout, and
    # that is measured from this city's own local elections. The pool "ratio"
    # this replaces was a triangular standing in for population change,
    # registration change and turnout change at once, fitted to two
    # transitions.
    registered = registered_at_target(city, target, cfg, year)
    record = turnout_record(city, cfg, before=target.year)
    turnout = turnout_band(record, n)
    limits = turnout_limits(record, registered)

    record = entrant_record(lge_transitions(before=target.year))
    rates_matrix = np.array([[fits[p].rates[g] if p in fits else 0.0
                              for p in sorted(fits)] for g in range(n)])
    universe_fitted = sorted(fits)
    # Who contests how much of the city. Nomination lists are public before
    # polling day; for a target already held the roster stands in.
    reach = _ward_reach(city.code, target.year) or _ward_reach(city.code, year)
    arrivals, seed_notes = arrival_rules(
        newcomers, lineage, rates_matrix, universe_fitted, cats, record,
        splinter_record(city), registered, contestation=reach)
    # An arrival's composition follows from where it captures, so it does not
    # need a separate vector: the pools it takes from ARE its pool weights.
    for party, rule in arrivals.items():
        vec = np.zeros(n)
        for g, r in rule["capture"].items():
            vec[int(g)] = r * registered[int(g)]
        composition[party] = vec / vec.sum() if vec.sum() > 0 else np.full(n, 1.0 / n)
    seeds = {p: float(sum(r * registered[int(g)] for g, r in rule["capture"].items())
                      / max(registered.sum(), 1e-9))
             for p, rule in arrivals.items()}
    seed_bands = {p: rule["band"] for p, rule in arrivals.items()}
    # no_vector, NOT newcomers: the file exists to ask a human which parent a
    # party with no measured vector belongs to, and MK is the case it was built
    # for. Passing the seed set generated an EMPTY template for 2026, so a
    # regenerated file would have silently dropped MK's declared parent.
    template = write_lineage_template(
        city, target, {p: baseline.get(p, 0.0) for p in no_vector},
        lineage, list(ctx["categories"]))

    transitions = lge_transitions(before=target.year)

    # Each pool's internal split, per metro-year, for the concentration.
    splits: list[list[np.ndarray]] = [[] for _ in range(n)]
    split_years = sorted({y for pair in transitions for y in pair}, key=int)
    for code in METRO_CODES:
        for y in split_years:
            shares = metro_citywide(code, y)
            if not shares:
                continue
            for g in range(n):
                contrib = np.array([composition[p][g] * shares.get(p, 0.0)
                                    for p in composition])
                if contrib.sum() > 0:
                    splits[g].append(contrib / contrib.sum())

    out = {}
    for g, name in enumerate(cats):
        members = {p: float(w[g]) for p, w in composition.items() if w[g] > 1e-4}
        if not members:
            continue
        lo, mid, hi = turnout[g]
        out[name] = {
            "members": members,
            "registered": float(registered[g]),
            "turnout": [lo, mid, hi],
            "alpha": dirichlet_alpha(splits[g]),
            "derived_from": f"pool vectors fitted on {city.slug} {year}; size "
                            f"from the {target.year} roll split by each ward's "
                            f"own composition; turnout from {city.slug}'s local "
                            f"elections before {target.year}",
            # Which members' weights the ward data actually pins down. The rest
            # are the model's guesses and are where a judgement belongs. A
            # party with no measured vector at all (it did not contest the
            # fitting election) is never identified — its weights came from a
            # lineage rule, not from a ward.
            "identified": sorted(p for p in members
                                 if p in fits and fits[p].identified()[g]),
        }
    return {"pools": out, "fitted_on": year, "target": target.year,
            "turnout_limits": limits,
            "seeds": {p: v for p, v in seeds.items() if abs(v) > 1e-9},
            "seed_bands": {p: list(v) for p, v in seed_bands.items()},
            "seed_notes": seed_notes,
            "entrant_record": [[float(share), float(reach)] for share, reach in record],
            "provenance": f"{ctx['provenance']}; pools sized by {roll_note}",
            "pool_shares_at_target": target_shares.tolist(),
            "registration_series": {y: v.tolist() for y, v in series.items()},
            "categories": cats,
            "no_measured_vector": inherited,
            "judgement_file": str(template)}


# --------------------------------------------------------------------------
# admission: does a dimension earn its place?
# --------------------------------------------------------------------------
def gate(cfg: Config, year: str = "2021",
         slugs: tuple[str, ...] = ("joburg", "tshwane")) -> dict[str, dict]:
    """Fit on one city, predict another, and see whether a tilt helped.

    In-sample gain is not evidence — every dimension we hold shows some, mostly
    by re-describing the base. Only a dimension that transfers is real.
    """
    tested = [d for d in cfg.dimensions if d.role == "tilt"]
    parties = list(cfg.gate.get("gate_parties", ["ANC", "DA", "EFF"]))
    results: dict[str, dict] = {}

    prepared = {}
    for slug in slugs:
        city = cityconfig.load(slug)
        for dim in tested:
            prepared[(slug, dim.name)] = fit_city(
                city, year, cfg, admitted_only=False, extra_tilts=[dim],
                party_list=parties)
        prepared[(slug, None)] = fit_city(city, year, cfg, admitted_only=False,
                                          extra_tilts=[], party_list=parties)

    for dim in tested:
        gains = {}
        for train, test in ((slugs[0], slugs[1]), (slugs[1], slugs[0])):
            base_fits, _ = prepared[(train, None)]
            dim_fits, _ = prepared[(train, dim.name)]
            _, base_ctx = prepared[(test, None)]
            _, dim_ctx = prepared[(test, dim.name)]
            for party in parties:
                if party not in base_fits or party not in dim_fits:
                    continue
                y = np.array([base_ctx["shares"][w].get(party, 0.0)
                              for w in base_ctx["wards"]])
                v = base_ctx["votes"]
                b0 = np.concatenate([base_fits[party].rates])
                b1 = np.concatenate([dim_fits[party].rates,
                                     dim_fits[party].tilts[dim.name]])
                r0 = _r2(y, base_ctx["X"] @ b0, v)
                r1 = _r2(y, dim_ctx["X"] @ b1, v)
                gains.setdefault(party, []).append(r1 - r0)
        mean_gain = float(np.mean([np.mean(g) for g in gains.values()])) if gains else 0.0
        results[dim.name] = {
            "gain": mean_gain,
            "per_party": {p: float(np.mean(g)) for p, g in gains.items()},
            "admit": mean_gain >= float(cfg.gate.get("min_oos_gain", 0.01)),
            "currently": dim.admitted,
        }
    return results


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
def _report(fits, ctx, title: str) -> None:
    cats = ctx["categories"]
    print(f"\n{title}")
    print(f"  pools: {', '.join(cats)}")
    print(f"  {'party':10s}{'city%':>7s}  " +
          "".join(f"{c[:11]:>13s}" for c in cats) + f"{'R2':>7s}")
    order = sorted(fits, key=lambda p: -fits[p].citywide)
    for party in order[:14]:
        f = fits[party]
        cells = []
        for g in range(len(cats)):
            mark = " " if f.identified()[g] else "?"
            cells.append(f"{f.rates[g]:>11.1%}{mark} ")
        print(f"  {party:10s}{f.citywide:>7.1%}  " + "".join(cells) + f"{f.r2:>7.2f}")
    print("  ? = the fitted rate is not identified by ward data; the "
          "deterministic bound spans >50 points and a judgement belongs there.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    cityconfig.add_city_argument(ap)
    cityconfig.add_target_argument(ap)
    ap.add_argument("--gate", action="store_true",
                    help="re-test which dimensions earn admission")
    ap.add_argument("--emit", action="store_true",
                    help="write the measured pools the simulation draws from")
    ap.add_argument("--from-year", default=None,
                    help="election to fit the vectors on (default: the target's "
                         "preceding LGE)")
    args = ap.parse_args()

    cfg = load_config()

    if args.gate:
        print("Dimension admission — out-of-sample gain, fitted on one metro, "
              "tested on the other")
        for name, r in gate(cfg).items():
            verdict = "ADMIT" if r["admit"] else "reject"
            flag = "" if r["admit"] == r["currently"] else "   << config disagrees"
            per = "  ".join(f"{p} {g:+.3f}" for p, g in r["per_party"].items())
            print(f"  {name:18s} mean gain {r['gain']:+.3f}   {verdict:6s} {per}{flag}")
        return

    city = cityconfig.use(args.city)
    target = cityconfig.use_target(args.target)

    if args.emit:
        import json
        spec = emit_pools(city, target, cfg, from_year=args.from_year)
        out = city.processed / f"pools_{target.year}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(spec, indent=2, sort_keys=True))
        print(f"{city.name} {target.year}: {len(spec['pools'])} pools -> {out}")
        for name, cfgp in spec["pools"].items():
            top = sorted(cfgp["members"].items(), key=lambda kv: -kv[1])[:4]
            share = ", ".join(f"{p} {w:.0%}" for p, w in top)
            lo, mid, hi = cfgp["turnout"]
            print(f"  {name:16s} {cfgp['registered']:>9,.0f} registered  "
                  f"turnout {lo:.0%}/{mid:.0%}/{hi:.0%}  "
                  f"alpha {cfgp['alpha']:5.1f}  {share}")
            if not cfgp["identified"]:
                print(f"  {'':16s} !! no member's weight is identified by ward "
                      f"data; every one is a judgement")
        return

    year = args.from_year or target.previous_lge or target.year
    fits, ctx = fit_city(city, year, cfg)
    _report(fits, ctx, f"{city.name} — pool vectors fitted on {year} "
                       f"(for target {target.year})")
    print(f"  composition: {ctx['provenance']}")

    print(f"\n  Where each party's vote comes from (composition, {year}):")
    cats = ctx["categories"]
    print(f"  {'party':10s}" + "".join(f"{c[:11]:>13s}" for c in cats))
    for party in sorted(fits, key=lambda p: -fits[p].citywide)[:8]:
        comp = fits[party].composition(ctx["pool_votes"])
        print(f"  {party:10s}" + "".join(f"{x:>13.1%}" for x in comp))


if __name__ == "__main__":
    main()
