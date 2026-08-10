"""Voter pools: what a party talks to, measured rather than asserted.

The model used to carry ``BLOCS`` — two hand-drawn lists of parties assumed to
trade votes with each other. That is a claim about parties. A pool is a claim
about *voters*: a characteristic people have, measured from the census, against
which each party is described by the rate at which it wins them.

Three things this module is careful about, each because getting them wrong
produces output that looks right.

**Nothing is zero.** Non-negative least squares puts small weights on the
boundary and reports them as ``0.0%``. That is a corner of the feasible set, not
a measurement: read literally it says the ANC has no white supporters. So the
fit is bounded below by what the arithmetic can prove rather than by zero.
:func:`bounds` computes the Duncan-Davis interval — pooled over the eight
metros the ANC's rate among Coloured voters is provably at least 0.4% and among
Indian voters at least 0.7% — and :func:`_solve` projects every estimate into
that box each iteration. Without the projection the fit answered 0.2% for a
quantity it had itself proven to be above 0.4%.

**The data is often uninformative, and says so.** Ecological inference can only
pin down a group's behaviour where wards differ a lot in that group's share.
Johannesburg holds one ward that is majority-Indian and three majority-Coloured,
so those rates are unidentifiable *in the city* and the regularisation, not the
evidence, would decide them. :func:`fit_national` therefore fits all eight
metros together — eThekwini has fifteen majority-Indian wards, Cape Town
forty-eight majority-Coloured — and the city fit shrinks toward that national
shape rescaled to the city's own level, because direction transfers between
cities and magnitude does not. Where even the pooled bound stays wide (the ANC
among white voters, 0-20.4%) the estimate is flagged unidentified, and that gap
is where the human judgement layer belongs.

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
        on_delimitation = ward_codes is None or set(comp) >= ward_codes
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
            raise SystemExit(
                f"{dim.name}: only Census {census.year} is available and the "
                f"target is {gap:+.1f} years from it, beyond the "
                f"{cfg.max_extrapolation:g}-year limit. A second census is "
                f"needed to establish a trend.")
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
    lam: float = float("nan")
    bounds: np.ndarray | None = None      # (n_pools, 2) Duncan-Davis interval

    def composition(self, pool_electorate: np.ndarray) -> np.ndarray:
        """Where the party's votes come from — shares summing to 1."""
        got = self.rates * pool_electorate
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


def _solve(X: np.ndarray, y: np.ndarray, w_votes: np.ndarray, *,
           n_base: int, prior_base: np.ndarray, lam: float, floor: float,
           box: np.ndarray | None = None, iters: int = 4000) -> np.ndarray:
    """Weighted ridge toward a prior, with a floor on the base rates.

    ``prior_base`` is where the fit sits when the wards say nothing. A flat
    prior ("wins every pool at its citywide rate") is the honest starting point
    for a party nothing is known about, but for a city it is a bad one: the
    minority rates a single metro cannot identify then get decided by the
    regularisation rather than by evidence, and they collapse to the floor.
    Passing the national fit instead means an unidentified rate falls back on
    what other cities measured. Tilt coefficients shrink toward zero, since
    their null is "no tilt".

    ``box`` is the Duncan-Davis interval per pool, and the base rates are
    projected into it every iteration. Without it the fit will happily return a
    rate the arithmetic has already ruled out — pooled over the eight metros
    the ANC's support among Coloured voters is provably at least 0.4%, and the
    unconstrained fit answered 0.2%. A number below its own proven floor is not
    an estimate.
    """
    sw = np.sqrt(w_votes)
    Xw, yw = X * sw[:, None], y * sw
    prior = np.zeros(X.shape[1])
    prior[:n_base] = prior_base

    beta = prior.copy()
    step = 1.0 / (np.linalg.norm(Xw, 2) ** 2 + lam + 1e-12)
    for _ in range(iters):
        grad = Xw.T @ (Xw @ beta - yw) + lam * (beta - prior)
        beta = beta - step * grad
        beta[:n_base] = np.maximum(beta[:n_base], floor)
        if box is not None:
            beta[:n_base] = np.clip(beta[:n_base], box[:, 0], box[:, 1])
    return beta


def _r2(y: np.ndarray, pred: np.ndarray, w: np.ndarray) -> float:
    mean = np.average(y, weights=w)
    denom = (((y - mean) ** 2) * w).sum()
    return 1.0 - (((y - pred) ** 2) * w).sum() / denom if denom > 0 else float("nan")


def bounds(y: np.ndarray, comp: np.ndarray, votes: np.ndarray) -> np.ndarray:
    """Duncan-Davis method of bounds: what the arithmetic alone allows.

    No model. In each ward the party's votes coming from pool g are at least
    (its votes minus everyone outside g) and at most (its votes, or all of g).
    Summing those over wards gives a hard interval on the citywide rate.

    Assumes turnout does not differ by pool, which it does — the interval is
    indicative rather than exact, but its *width* is the honest signal: where it
    spans most of the unit interval, ward data cannot see that pool at all.
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
             party_list: list[str] | None = None,
             national: dict[str, PartyFit] | None = None):
    """Fit every party's pool vector from one city's ward results.

    Composition is taken as at that election's polling day, not as at whichever
    census happens to be lying around.
    """
    shares, votes = ward_party_shares(city, year)
    when = election_decimal_year(cityconfig.Target(city=city, year=year))
    codes = set(shares)

    base = cfg.base()
    comp_by_ward, provenance = composition_at(base, cfg, when, codes,
                                              city=city, election_year=year)
    tilt_dims = list(cfg.tilts(admitted_only=admitted_only))
    if extra_tilts:
        tilt_dims += [d for d in extra_tilts if d.name not in {t.name for t in tilt_dims}]
    tilt_by_ward = {}
    for d in tilt_dims:
        tilt_by_ward[d.name], _ = composition_at(d, cfg, when, codes,
                                                 city=city, election_year=year)

    wards = sorted(w for w in shares
                   if w in comp_by_ward
                   and all(w in tilt_by_ward[d.name] for d in tilt_dims))
    if not wards:
        raise SystemExit(f"{city.slug} {year}: no ward joined the covariates")

    comp = np.array([comp_by_ward[w] for w in wards])
    vote = np.array([votes[w] for w in wards])
    blocks = [comp]
    for d in tilt_dims:
        m = np.array([tilt_by_ward[d.name][w] for w in wards])
        blocks.append(m - np.average(m, axis=0, weights=vote))
    X = np.hstack(blocks)
    n_base = comp.shape[1]

    floor = float(cfg.fit.get("floor_rate", 0.002))
    grid = list(cfg.fit.get("ridge_grid", [0.0]))
    folds = int(cfg.fit.get("ridge_folds", 5))
    universe = party_list or sorted({p for w in wards for p in shares[w]})

    pool_share = (comp * vote[:, None]).sum(axis=0)
    pool_share = pool_share / pool_share.sum()

    fits: dict[str, PartyFit] = {}
    for party in universe:
        y = np.array([shares[w].get(party, 0.0) for w in wards])
        if y.sum() <= 0:
            continue
        null = float(np.average(y, weights=vote))

        # The prior is the national shape, rescaled to this city's level —
        # direction transfers between cities, magnitude does not (Al Jama-ah is
        # Indian-shaped in both metros at 0.8% and 0.1%). Where there is no
        # national fit for a party, fall back to the flat null.
        box = bounds(y, comp, vote)
        box[:, 0] = np.maximum(box[:, 0], floor)
        box[:, 1] = np.maximum(box[:, 1], box[:, 0])

        prior_base = np.full(n_base, null)
        nat = (national or {}).get(party)
        if nat is not None:
            implied = float(nat.rates @ pool_share)
            if implied > 1e-9:
                prior_base = nat.rates * (null / implied)

        # λ by k-fold cross-validation over wards: how much to trust the wards
        # over the null is itself a question the wards can answer.
        best, best_lam = float("inf"), grid[0]
        if len(grid) > 1 and len(wards) >= folds:
            assign = np.arange(len(wards)) % folds
            for lam in grid:
                err = 0.0
                for k in range(folds):
                    tr, te = assign != k, assign == k
                    beta = _solve(X[tr], y[tr], vote[tr], n_base=n_base,
                                  prior_base=prior_base, lam=lam, floor=floor,
                                  box=box)
                    err += (((X[te] @ beta - y[te]) ** 2) * vote[te]).sum()
                if err < best:
                    best, best_lam = err, lam

        beta = _solve(X, y, vote, n_base=n_base, prior_base=prior_base,
                      lam=best_lam, floor=floor, box=box)
        offset, tilts = n_base, {}
        for d in tilt_dims:
            k = len(d.categories)
            tilts[d.name] = beta[offset:offset + k]
            offset += k
        fits[party] = PartyFit(
            party=party, citywide=null, rates=beta[:n_base], tilts=tilts,
            r2=_r2(y, X @ beta, vote), lam=best_lam, bounds=box,
        )

    pool_electorate = (comp * vote[:, None]).sum(axis=0)
    return fits, {"wards": wards, "comp": comp, "votes": vote, "X": X,
                  "n_base": n_base, "shares": shares, "tilt_dims": tilt_dims,
                  "pool_electorate": pool_electorate, "categories": base.categories,
                  "provenance": provenance, "when": when, "year": year}


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


def fit_national(cfg: Config, year: str = "2021", codes=METRO_CODES,
                 ) -> tuple[dict[str, PartyFit], np.ndarray, list[str]]:
    """Fit pool vectors on every metro at once.

    This exists because a single city cannot identify the pools it has no
    homogeneous wards for. Johannesburg holds one ward that is majority-Indian
    and three that are majority-Coloured; across the eight metros there are
    seventeen and sixty-three, because eThekwini and Cape Town have them. The
    rates the city cannot see are measurable in the country, and a national
    rate is a far better prior for Johannesburg than "appeals to everyone
    equally" — which is what was driving every minority estimate to the floor.

    What this does NOT assume is that a party performs identically everywhere.
    The national vector supplies the *shape*; :func:`fit_city` rescales it to
    the city's own level and lets the city's wards move it from there.
    """
    base = cfg.base()
    census = base.censuses[-1]
    comp_all = read_census(base, census, cfg)

    wards, comp_rows, vote_rows, share_rows = [], [], [], []
    for code in codes:
        shares, votes = metro_ward_shares(code, year)
        for ward in shares:
            if ward in comp_all:
                wards.append(f"{code}:{ward}")
                comp_rows.append(comp_all[ward])
                vote_rows.append(votes[ward])
                share_rows.append(shares[ward])
    if not wards:
        raise SystemExit("national fit: no metro ward joined the census")

    comp = np.array(comp_rows)
    vote = np.array(vote_rows)
    floor = float(cfg.fit.get("floor_rate", 0.002))
    grid = list(cfg.fit.get("ridge_grid", [0.0]))
    universe = sorted({p for s in share_rows for p in s})

    fits: dict[str, PartyFit] = {}
    for party in universe:
        y = np.array([s.get(party, 0.0) for s in share_rows])
        if y.sum() <= 0:
            continue
        null = float(np.average(y, weights=vote))
        prior = np.full(comp.shape[1], null)
        box = bounds(y, comp, vote)
        box[:, 0] = np.maximum(box[:, 0], floor)
        box[:, 1] = np.maximum(box[:, 1], box[:, 0])
        beta = _solve(comp, y, vote, n_base=comp.shape[1], prior_base=prior,
                      lam=grid[len(grid) // 2] if len(grid) > 1 else 0.0,
                      floor=floor, box=box)
        fits[party] = PartyFit(party=party, citywide=null, rates=beta,
                               r2=_r2(y, comp @ beta, vote), bounds=box)
    pool_electorate = (comp * vote[:, None]).sum(axis=0)
    return fits, pool_electorate, list(base.categories)


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


def measure_pool_ratios(composition: dict[str, np.ndarray], n_pools: int,
                        transitions=(("2011", "2016"), ("2016", "2021")),
                        codes=METRO_CODES) -> list[list[float]]:
    """How much a pool's vote total moves between elections, across all metros.

    Sixteen metro-transitions rather than Johannesburg's two, because a range
    fitted on the city it will be used to predict is not a prior. Composition
    is held at its fitted value throughout: we can only see the electorate's
    make-up at one census, so the *definition* of each pool is fixed and what
    is being measured is the movement of its vote.
    """
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
        "# These parties are in the baseline but did not contest the election the",
        "# pool vectors were fitted on, so nothing measurable says which voters",
        "# they talk to. Set `parent` to inherit that party's pool vector (a",
        "# splinter, defined identically to its parent until the numbers say",
        "# otherwise). Leave `parent` empty to treat it as an entrant, drawing an",
        "# even share of every pool.",
        "#",
        "# `weights` overrides the inherited vector outright, when you know",
        "# something the data cannot: order is",
        f"#   {', '.join(pools_named)}",
        "# and the values are normalised, so [0, 0, 0, 1, 0] means 'entirely the",
        "# last pool'. Delete the line to keep the default.",
        "#",
        "# Every override here is recorded in the run's provenance and should be",
        "# deleted once the election has been held and the vector measured.",
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
    national, _, _ = fit_national(cfg, year)
    fits, ctx = fit_city(city, year, cfg, national=national)
    cats = list(ctx["categories"])
    n = len(cats)

    composition = {p: f.composition(ctx["pool_electorate"]) for p, f in fits.items()}

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

    newcomers = {p: s for p, s in baseline.items()
                 if p not in composition and s > 0 and p not in ("IND",)}
    lineage = load_lineage(city, target)
    inherited: dict[str, str] = {}
    for party, share in newcomers.items():
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

    template = write_lineage_template(city, target, newcomers, lineage,
                                      list(ctx["categories"]))

    ratios = measure_pool_ratios(composition, n)

    # Each pool's internal split, per metro-year, for the concentration.
    splits: list[list[np.ndarray]] = [[] for _ in range(n)]
    for code in METRO_CODES:
        for y in ("2011", "2016", "2021"):
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
        obs = sorted(ratios[g])
        if len(obs) >= 4:
            lo, mid, hi = (float(np.quantile(obs, 0.05)), float(np.median(obs)),
                           float(np.quantile(obs, 0.95)))
        else:
            lo, mid, hi = 0.7, 1.0, 1.4
        out[name] = {
            "members": members,
            "ratio": [lo, mid, hi],
            "alpha": dirichlet_alpha(splits[g]),
            "observations": len(obs),
            "derived_from": f"pool vectors fitted on {city.slug} {year}; ratios "
                            f"from {len(obs)} metro transitions across "
                            f"{len(METRO_CODES)} metros",
            # Which members' weights the ward data actually pins down. The rest
            # are the model's guesses and are where a judgement belongs. A
            # party with no measured vector at all (it did not contest the
            # fitting election) is never identified — its weights came from a
            # lineage rule, not from a ward.
            "identified": sorted(p for p in members
                                 if p in fits and fits[p].identified()[g]),
        }
    return {"pools": out, "fitted_on": year, "target": target.year,
            "provenance": ctx["provenance"], "categories": cats,
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
            print(f"  {name:16s} ratio {cfgp['ratio'][0]:.2f}/"
                  f"{cfgp['ratio'][1]:.2f}/{cfgp['ratio'][2]:.2f}  "
                  f"alpha {cfgp['alpha']:5.1f}  n={cfgp['observations']:2d}  {share}")
            if not cfgp["identified"]:
                print(f"  {'':16s} !! no member's weight is identified by ward "
                      f"data; every one is a judgement")
        return

    year = args.from_year or target.previous_lge or target.year
    national, _, _ = fit_national(cfg, year)
    fits, ctx = fit_city(city, year, cfg, national=national)
    _report(fits, ctx, f"{city.name} — pool vectors fitted on {year} "
                       f"(for target {target.year})")
    print(f"  composition: {ctx['provenance']}")

    print(f"\n  Where each party's vote comes from (composition, {year}):")
    cats = ctx["categories"]
    print(f"  {'party':10s}" + "".join(f"{c[:11]:>13s}" for c in cats))
    for party in sorted(fits, key=lambda p: -fits[p].citywide)[:8]:
        comp = fits[party].composition(ctx["pool_electorate"])
        print(f"  {party:10s}" + "".join(f"{x:>13.1%}" for x in comp))


if __name__ == "__main__":
    main()
