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
import ast
import csv
import time
import os
import contextlib
import hashlib
import tomllib
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path

import numpy as np

import cityconfig
import parties as P

# ---------------------------------------------------------------------------
# ONE WRITER ON THE SHARED ARTEFACTS, ENFORCED — not asked for politely
# ---------------------------------------------------------------------------
# `data/processed/**/pools_*.json` is precomputed and shared. CLAUDE.md has said
# "exactly one worker may re-emit, and nobody else measures while it does" since
# the rule cost this project a retracted result. It was still only a rule, and on
# 2026-08-27 it was broken twice inside thirty minutes by two background jobs
# racing: eighteen specs ended up carrying TWO different `pools_sha` values, and
# every measurement taken against that tree was meaningless.
#
# A convention that depends on remembering is not a guard. This is the guard.
#
#   emit  -> EXCLUSIVE lock. A second emit fails immediately with a named error
#            rather than interleaving.
#   read  -> SHARED lock, taken by the long readers (compare_history, the suite).
#            An emit cannot start while one is held, and a reader cannot start
#            while an emit holds the exclusive lock.
#
# Non-blocking by design: waiting silently is how you get a job that looks hung.
# Set POOLS_LOCK_WAIT=<seconds> to wait instead of failing.

LOCK_PATH = Path("data/processed/.pools.lock")


@contextlib.contextmanager
def artefact_lock(mode: str, what: str = ""):
    """Hold the pool-artefact lock. ``mode`` is "emit" (exclusive) or "read".

    Raises SystemExit with an explanatory message rather than blocking, so a
    collision is a loud failure at the start instead of a corrupt measurement at
    the end.
    """
    import fcntl
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    flag = fcntl.LOCK_EX if mode == "emit" else fcntl.LOCK_SH
    wait = float(os.environ.get("POOLS_LOCK_WAIT", "0") or 0)
    fh = open(LOCK_PATH, "a+")
    deadline = time.monotonic() + wait
    while True:
        try:
            fcntl.flock(fh.fileno(), flag | fcntl.LOCK_NB)
            break
        except OSError:
            if time.monotonic() >= deadline:
                fh.close()
                held = ""
                try:
                    held = LOCK_PATH.read_text().strip().splitlines()[-1]
                except Exception:
                    pass
                raise SystemExit(
                    f"pools artefacts are locked by another process"
                    + (f" — {held}" if held else "")
                    + f"\n  wanted: {mode} {what}"
                    + "\n  The shared pool specs may not be written by two "
                      "processes, nor read by a measurement while one writes "
                      "(CLAUDE.md, 'Shared artefacts: one writer')."
                      "\n  Wait for it to finish, or set POOLS_LOCK_WAIT=600 "
                      "to queue behind it.")
            time.sleep(0.25)
    try:
        if mode == "emit":
            fh.seek(0); fh.truncate()
            fh.write(f"emit pid={os.getpid()} {what}\n"); fh.flush()
        yield
    finally:
        try:
            if mode == "emit":
                fh.seek(0); fh.truncate(); fh.flush()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)
            fh.close()

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


def _sha(path: Path) -> str:
    """Short content hash of a file, or a marker when it is not there."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]
    except OSError:
        return "missing"


def _code_sha(path: Path) -> str:
    """Hash what the module DOES, ignoring comments and docstrings.

    A whole-file hash would be wrong here, and wrong in the specific way that
    makes a guard useless. `CLAUDE.md` requires the documentation to change in
    the same commit as the model, so this file's docstrings move constantly —
    and a staleness warning that fires every time someone improves a comment is
    a warning everyone learns to ignore. Then the one that matters is ignored
    too.

    So the hash is taken over the parsed syntax tree with docstrings stripped:
    any change to what the code computes moves it, and no change to how the code
    is explained does.

    Falls back to the byte hash if the file will not parse, which is the safe
    direction — an unparseable module should look changed.

    One caveat worth knowing: `ast.dump` output is not guaranteed stable across
    Python versions, so a interpreter upgrade will mark every spec stale. That
    is a re-emit worth doing anyway, for the same reason a numpy upgrade is a
    deliberate golden re-record.
    """
    try:
        tree = ast.parse(Path(path).read_text())
    except (OSError, SyntaxError):
        return _sha(path)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            body.pop(0)
    return hashlib.sha256(
        ast.dump(tree, annotate_fields=False).encode()).hexdigest()[:16]


def artefact_key(city, target, config_path: Path = CONFIG) -> dict:
    """What an emitted spec was built FROM, so staleness can be detected.

    `pools_*.json` is precomputed. Changing this file does nothing until the
    spec is re-emitted, and re-emitting it changes the baseline of every
    measurement in flight. Until now the only protection was a rule in
    `CLAUDE.md` — *"one writer, and nobody measures while it writes"* — that a
    person had to remember, and **it has already failed twice**: a lever sweep
    returned different answers on two identical runs, and two `EXPECTED_INERT`
    reasons written from those unstable readings had to be retracted.

    A hash of the code and the config that produced a spec turns that from
    something you must remember into something a run can check. It does not stop
    anyone re-emitting; it stops the result being believed afterwards.

    **Deliberately not a hash of the inputs.** The census and roll files are
    large and numerous, and hashing them on every run would cost more than it
    catches; the code and the config are what change when someone is working.
    A wrong-city INPUT is a different failure and is caught by refusing the
    fallback, which is where `pools.py` now refuses by name.
    """
    return {
        "schema": 1,
        "city": getattr(city, "slug", str(city)),
        "target": getattr(target, "year", str(target)),
        "pools_sha": _code_sha(Path(__file__)),
        "config_sha": _sha(config_path),
    }


def stale_reason(spec: dict, city, target, config_path: Path = CONFIG) -> str | None:
    """Why this spec should not be trusted for this run, or None.

    Returns a sentence, not a boolean, because the caller prints it and the
    useful part is *which* thing moved.
    """
    key = spec.get("artefact_key")
    if not key:
        return ("emitted before artefact keys existed, so nothing can say "
                "whether it matches the current pools.py — re-emit to check")
    now = artefact_key(city, target, config_path)
    if key.get("city") != now["city"] or key.get("target") != now["target"]:
        return (f"built for {key.get('city')} {key.get('target')}, "
                f"not {now['city']} {now['target']}")
    moved = [name for name in ("pools_sha", "config_sha")
             if key.get(name) != now[name]]
    if moved:
        which = " and ".join(
            {"pools_sha": "src/pools.py", "config_sha": str(config_path)}[m]
            for m in moved)
        return (f"{which} changed since this spec was emitted "
                f"({', '.join(f'{m} {key.get(m)} -> {now[m]}' for m in moved)}); "
                f"re-emit before believing any measurement taken against it")
    return None


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


def read_census_population(census: Census,
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


# The one bloc currently defined this way, kept beside the function that
# builds it so there is a single place to change it — and deliberately NOT in
# cities/*.toml, where it would sit next to settings the published forecast
# reads and would be one edit away from becoming one.
SIMULATION_BLOC = {"parent": "Black African", "name": "IFP-located",
                   "indicator": "IFP", "within_rate": 0.90}


def vote_located_bloc(city: cityconfig.City, before_year: str,
                      indicator: str = "IFP", within_rate: float = 0.90,
                      ward_of: dict[str, str] | None = None,
                      ) -> tuple[dict[str, float], dict]:
    """Locate a voter bloc the census cannot see, using a party that only it votes for.

    ================================================================
    THIS IS A PROXY. IT IS MEANT TO BE REPLACED.
    ================================================================

    The pools are population groups because that is the only ward-level
    characteristic Stats SA publishes. It is too coarse, and the model knows
    it: the ANC and the IFP are both overwhelmingly African-supported and
    stand on entirely separate ground (district correlation −0.14). South
    Africa's African electorate is not one electorate — Zulu, Xhosa, Sotho,
    Pedi, Tswana, Tsonga, Venda, Ndebele and Swati are distinct — and the
    right way to carry that is **Census 2022 home language by ward**, which we
    do not hold. The request is drafted at
    ``drafts/statssa-request-language.md`` and had not been sent as of
    2026-08-11. When it lands, this function should be replaced by it, or at
    the very least validated against it and demoted to a covariate.

    Until then: a party with a narrow, well-understood constituency is an
    *indicator* for a bloc no table describes. Three are already visible in
    the fit, each near-zero in every pool but one — the PA locates the
    Coloured pool (0.412 ± 0.017), Al Jama-ah the Indian/Muslim one (0.190 ±
    0.019), and the IFP a bloc inside "Black African" that has no column of
    its own.

    WHY THE IFP AND WHY THE PEAK. Measured on Johannesburg's 135 wards:

    * The IFP's ward geography is almost perfectly stable — 2016 against 2021
      correlates **+0.985**, and +0.986 once Black African share is removed.
      It is a real, sharply-located, persistent constituency.
    * MK, which did not exist until December 2023, arrived **on top of it**.
      Correlation of MK's 2024 ward share with the IFP's, after removing Black
      African share from both sides: +0.65. Over the same wards the ANC's and
      the EFF's associations with MK *invert* (−0.24, −0.28). So MK's map is
      not "where African voters are", it is "where the IFP is".
    * The bloc SWITCHES, which is why this takes the peak across the record
      rather than the most recent election. Against MK 2024, the older IFP
      geography predicts better than the newer: 2011 +0.684, 2006 +0.682,
      2000 +0.675, against 2021's +0.646, and the peak beats all of them at
      **+0.687**. Removing the 2021 IFP vote as well, MK still correlates
      +0.325 with IFP 2011 — there are wards the bloc left, voting ANC in the
      middle years and MK in 2024, and only the old vote finds them.

    WHAT THIS IS NOT. It does not identify Zulu voters. It identifies the bloc
    the IFP stands on, which we have external reason to believe is largely
    Zulu — exactly the kind of naming-from-outside-knowledge the census does
    when it labels a fitted factor. Calling the result "Zulu" would be a claim
    the data does not make, so the pool is named for what was measured.

    It also does not claim MK belongs to this bloc. It does not: in wards
    79800046/51/52 MK took 33-34% where the IFP has never exceeded 5.2% in
    twenty-four years. That is ANC defection, not a bloc switching, and the
    joint fit is left to split MK between this pool and the general African
    one rather than being told the answer.

    THE ONE JUDGEMENT, stated so it can be argued with. An indicator party's
    vote share is not the bloc's population share; the bloc has to vote for it
    at some rate, and that rate is ``within_rate``. 0.90 is anchored on ward
    79800065, where the IFP peaked at 77.7% of a ward that is 88.2% Black
    African — a rate much below 0.9 would make the bloc larger than the pool
    it sits inside. It is a judgement and it scales the pool's SIZE; it does
    not affect which wards the bloc is found in, which is what the +0.985
    stability above is about.

    ``before_year`` keeps this honest in a backtest: only elections strictly
    before the target are read, so the bloc for a 2016 target is located with
    2000-2011 and cannot borrow the geography of the election being forecast.

    Returns ``({ward: bloc share of that ward's people}, provenance)``.
    """
    years = sorted((y for y, e in cityconfig.CALENDAR.items()
                    if e.kind == "LGE" and e.results and int(y) < int(before_year)),
                   key=int)
    if not years:
        return {}, {"indicator": indicator, "elections": [],
                    "within_rate": within_rate, "before": before_year}
    # The VD-to-ward map comes from the CALLER, because the caller's wards are
    # the ones the result has to be keyed by and it is already reading that
    # election. Building it here from ``before_year`` read the target's own
    # file — boundaries only, never votes, but a temporal test cannot tell
    # those apart at the file and should not have to. Standing alone, fall
    # back to the last election strictly before the target.
    if ward_of is None:
        ward_of, _ = vd_map(city, years[-1])
    peak: dict[str, float] = defaultdict(float)
    used: list[str] = []
    for year in years:
        template = cityconfig.CALENDAR[year].results
        path = city.path("raw", "elections", template) if template else None
        if not path or not path.exists():
            continue
        votes: dict[str, float] = defaultdict(float)
        total: dict[str, float] = defaultdict(float)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                if row.get("BallotType") not in (None, "", "PR"):
                    continue
                ward = ward_of.get((row.get("VD_Number") or "").strip())
                if not ward:
                    continue
                v = float(row.get("Party_Votes") or 0)
                total[ward] += v
                if P.canonical(row["sPartyName"]) == indicator:
                    votes[ward] += v
        if not total:
            continue
        used.append(year)
        for ward, tot in total.items():
            if tot > 0:
                peak[ward] = max(peak[ward], votes.get(ward, 0.0) / tot)
    return ({w: min(s / within_rate, 1.0) for w, s in peak.items()},
            {"indicator": indicator, "elections": used,
             "within_rate": within_rate, "before": before_year})


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


def pool_counts(city: cityconfig.City, year: str, cfg: Config, *,
                split_bloc: dict | None = None) -> PoolCounts:
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
    people_by_ward = read_census_population(base.censuses[-1], cfg)
    age = next((d for d in cfg.dimensions if d.name == "age"), None)
    adults_by_ward = (read_census_population(age.censuses[-1], cfg)
                      if age else {})

    wards = sorted(w for w in codes
                   if w in comp_by_ward and w in people_by_ward
                   and reg_by_ward.get(w, 0) > 0)
    if not wards:
        raise SystemExit(f"{city.slug} {year}: no ward joined the census")

    comp = np.array([comp_by_ward[w] for w in wards])
    categories = base.categories

    # A pool the census cannot see, carved out of the one it is hiding inside.
    # Opt-in and off by default: adding a column changes the shape of every
    # downstream artefact (turnout dials, the emitted spec, the reader's pool
    # controls), so it is measured before it is adopted. See
    # :func:`vote_located_bloc` for what this is and why it is a placeholder.
    if split_bloc:
        parent = split_bloc.get("parent", "Black African")
        bloc_name = split_bloc.get("name", "IFP-located")
        shares_by_ward, _prov = vote_located_bloc(
            city, split_bloc.get("before") or year,
            indicator=split_bloc.get("indicator", "IFP"),
            within_rate=float(split_bloc.get("within_rate", 0.90)),
            ward_of=vd_map(city, year)[0])
        g = categories.index(parent)
        carved = np.array([min(shares_by_ward.get(w, 0.0), comp[i, g])
                           for i, w in enumerate(wards)])
        # Taken OUT of the parent, never added on top: the bloc's members are
        # already counted there, and a ward's composition must still sum to 1.
        comp = np.column_stack([comp, carved])
        comp[:, g] -= carved
        categories = categories + (bloc_name,)

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
                    f"{categories[g]}: {name} is {ratio:.0%} of the level "
                    f"above it, which is impossible. Do NOT read this as a "
                    f"census undercount: the published Census 2022 figures for "
                    f"the white and Indian groups are argued to be too HIGH, "
                    f"not too low (over-adjustment for a 62%/72% "
                    f"post-enumeration undercount, leaving them 14%/24% above "
                    f"projections), which makes this gap wider rather than "
                    f"narrower. See DATA-QUALITY.md item 11.")

    return PoolCounts(wards=wards, categories=categories, people=people,
                      voting_age=voting_age, registered=registered, voted=voted,
                      rates=rates, violations=violations)


def registration_series(city: cityconfig.City, cfg: Config,
                        before: str | None = None,
                        split_bloc: dict | None = None) -> dict[str, np.ndarray]:
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
            counts = pool_counts(city, year, cfg, split_bloc=split_bloc)
        except SystemExit:
            continue           # that election is not on disk for this city
        total = counts.totals("registered")
        if total.sum() > 0:
            out[year] = total / total.sum()
    return out


def projected_pool_shares(series: dict[str, np.ndarray], target: str,
                          damping: float = 0.6) -> tuple[np.ndarray, str]:
    """Carry each pool's share of the roll forward to the target election.

    **THE TREND IS A RATE OF CHANGE, NOT A DIFFERENCE** (owner, 2026-08-27:
    *"the pool size prediction should rely on rate of change not raw
    numbers"*), and that choice is what lets this projection survive a pool
    whose LEVEL is known to be wrong.

    Johannesburg's white pool is sized from a census population the roll
    contradicts by roughly 2x (`DATA-QUALITY.md` items 11 and 13). Under the
    additive trend used until 2026-08-27 that bias entered TWICE: once in the
    level carried forward, and again in the increment, because a difference
    between two inflated numbers is itself inflated. **A ratio is not.** If a
    pool's share carries a constant factor k in every year::

        share_b / share_a = (c_b / c_a) · (S_a / S_b)

    and k divides out — the remaining term is the roll's own growth, common to
    every pool. So a log-space trend measures a pool's real rate of change even
    when nobody can agree how many people are in it, which is the situation we
    are actually in and expect to stay in.

    Damped for the same reason as before, and the same reason
    :func:`composition_at` damps census composition: a trend measured over one
    interval, extended, claims more than the data supports.

    A pool that vanishes between observations has no defined rate of change and
    holds its last share instead — a log of zero would carry it to zero
    everywhere and silently delete a pool.
    """
    years = sorted(series)
    if not years:
        raise SystemExit("no registration series: cannot size the pools")
    if len(years) == 1:
        return series[years[0]], f"{years[0]} roll held flat"
    a, b = years[-2], years[-1]
    span = int(b) - int(a)
    step = (int(target) - int(b)) / span if span else 0.0
    prev = np.asarray(series[a], dtype=float)
    last = np.asarray(series[b], dtype=float)
    FLOOR = 1e-9
    movable = (prev > FLOOR) & (last > FLOOR)
    ratio = np.ones_like(last)
    np.divide(last, prev, out=ratio, where=movable)
    rate = np.zeros_like(last)
    np.log(ratio, out=rate, where=movable)
    shares = np.maximum(last * np.exp(damping * step * rate), 1e-6)
    return shares / shares.sum(), (
        f"{b} roll carried to {target} on the {a}-{b} RATE of change "
        f"(log-space, invariant to a constant level bias), damped x{damping:g}")


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


# KEPT DELIBERATELY, AND UNEXERCISED (owner, 2026-08-28). It is read only at
# `composition_at`'s two-or-more-census interpolation, and every dimension in
# `config/dimensions.toml` declares exactly ONE census — population_group, age
# and sex, verified — so `len(frames) == 1`, the function returns early, and
# these two lines never execute on any shipped configuration.
#
# NOT DEAD CODE, AND NOT DELETED. The interpolation is real capability that a
# second census would need immediately, and the Stats SA correspondence is live
# on exactly that question (SOURCES.md: no Census 2022 SAL exists; the surviving
# route is a rake of 2011 ward language onto 2022 municipal totals). Deleting it
# would throw away the machinery on the day before it is wanted.
#
# What it is NOT is a null: a sweep of it returns flat because the branch is
# UNREACHABLE, which is `NULL-RESULTS.md`'s cause A by unreachability rather
# than by undelivery, and a fifth state the cause codes do not name. It is also
# invisible to `compare_history`'s serial-forcing guard, whose filter skips a
# leading underscore. Declared in JUDGEMENT-CALLS.md so it is not mistaken for
# either a live constant or an oversight. §1.119
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


def _scale_into_box(x: np.ndarray, lo: np.ndarray, hi: np.ndarray,
                    target: np.ndarray, steps: int = 100) -> np.ndarray:
    """Rescale each ROW by one factor so its clipped sum lands on ``target``.

    This is the box-constrained version of a single IPF half-step. Plain IPF
    multiplies a row by ``target / rowsum``; that is exactly the factor found
    here when nothing binds, and when a cell hits a wall the factor keeps
    growing so the row still reaches its total out of the cells that can still
    move. ``sum(clip(f*row, lo, hi))`` is continuous and non-decreasing in
    ``f``, so bisection finds it — and a cell fixed at ``lo`` (a party the
    arithmetic says *must* draw from this pool) is reached even from a hard
    zero, which no multiplicative step can do.

    ``target`` is clipped into ``[sum(lo), sum(hi)]`` first, because nothing
    outside that is reachable at any factor; the caller checks feasibility and
    reports, so this clip is a guard rather than a silent repair.
    """
    want = np.clip(target, lo.sum(axis=1), hi.sum(axis=1))
    f_lo = np.zeros_like(want)
    f_hi = np.ones_like(want)
    for _ in range(200):
        short = np.clip(x * f_hi[:, None], lo, hi).sum(axis=1) < want
        if not short.any():
            break
        # Capped, not unbounded: an all-zero row can never reach its target by
        # scaling, and letting the bracket run to inf turns 0 * inf into nan.
        f_hi = np.where(short, np.minimum(f_hi * 4.0, 1e30), f_hi)
    for _ in range(steps):
        mid = 0.5 * (f_lo + f_hi)
        below = np.clip(x * mid[:, None], lo, hi).sum(axis=1) < want
        f_lo = np.where(below, mid, f_lo)
        f_hi = np.where(below, f_hi, mid)
    return np.clip(x * (0.5 * (f_lo + f_hi))[:, None], lo, hi)


def balance_within_bounds(R: np.ndarray, electorate: np.ndarray,
                          party_votes: np.ndarray, lo: np.ndarray,
                          hi: np.ndarray, iters: int = 4000,
                          tol: float = 1e-12) -> np.ndarray:
    """:func:`balance_margins`, with the method of bounds as a third truth.

    Three things about a real election are known before any model runs. Each
    pool holds a counted number of voters; each party won a counted number of
    votes; and :func:`bounds` says, from the ward arithmetic alone, the
    narrowest interval each rate can possibly lie in. ``fit_joint`` respects
    the first, ``balance_margins`` adds the second — and NOTHING enforced the
    third, which was computed, stored on every :class:`PartyFit`, and read at
    exactly one place, to set a display flag.

    What that cost, measured at Johannesburg 2021. The joint fit put the PA at
    **51.49%** of the Coloured pool against a Duncan-Davis ceiling of 40.97%,
    and zero in all three other pools — a corner solution, and not an artefact
    of this optimiser (plain NNLS lands on 54.21% and the same three zeros).
    IPF then walked it to 41.21%, still outside, and the emitted vector was
    Coloured **1.0000**. At the 2026 target that party's level is about 102% of
    every vote the Coloured pool casts, which is not a number an election can
    produce, and the per-draw balance could not solve it.

    Adding the bounds is not a repair applied afterwards. A projection followed
    by a rescale is not a projection — clipping and then running IPF puts the
    rate straight back outside, which is precisely how 51.49% became 41.21%
    rather than 40.97%. So the box enters the iteration itself: each half-step
    scales a row (or a column) by the single factor that lands its *clipped*
    sum on the known total, which is a Bregman projection onto a convex set
    exactly as the unbounded half-step is. Both margins still hold exactly.

    **The unbounded answer is tried first, and kept when it is already legal.**
    This is not an optimisation; it is the difference between enforcing a
    constraint and replacing a solver. The seeding below fires on a condition
    that has nothing to do with the bounds — see its comment — so the bounded
    path moves fits that never violated anything, and it moves them the wrong
    way. Measured across the ten production fits, the bounded path costs ward
    SSE at every one, worst at Nelson Mandela Bay 2016 (+3.71%) and Buffalo
    City 2016 (+2.02%); at **Ekurhuleni 2016 it cost +0.61% with zero
    violations to fix**, taking the DA's Indian/Asian rate from 1.00 to 0.90
    and spreading Al Jama-ah from two pools across all four. Five of the ten
    fits — joburg 2011, joburg 2016, tshwane 2016, ekurhuleni 2016, mangaung
    2016 — have no violation at all, and ``balance_margins``' answer at each is
    both a strictly better ward fit and a fixed point of the iteration below
    (at Ekurhuleni, one full sweep moves it by 2.8e-12). Running it anyway
    bought nothing and paid for it.

    So: balance the margins; if every rate already lies inside its interval,
    that IS the answer and it is returned untouched. Only a fit the arithmetic
    can actually refute pays for the projection.

    ``lo`` and ``hi`` are pools x parties rate matrices from :func:`bounds`.
    """
    counts = R * electorate[:, None]
    target_rows = electorate.astype(float)
    target_cols = party_votes.astype(float)
    # Same reason as in :func:`balance_margins`: a party the fit zeroed in every
    # pool cannot be scaled back up, so seed it proportionally to the pools —
    # "its voters look like the electorate" is the maximum-entropy answer for a
    # party with no spatial signal at all, and the iteration moves it from there.
    empty = (counts.sum(axis=0) <= 0) & (target_cols > 0)
    if empty.any():
        counts[:, empty] = (target_rows[:, None] / target_rows.sum()) * \
            target_cols[empty][None, :]
    scale = target_rows.sum() / max(target_cols.sum(), 1e-12)
    target_cols = target_cols * scale
    lo_c = lo * electorate[:, None]
    hi_c = hi * electorate[:, None]

    # Feasibility, stated rather than discovered. The bounds and the margins are
    # arithmetic on the SAME ward table, so the true cross-tabulation satisfies
    # all of it and an infeasible system means one of the two inputs is not what
    # it claims to be. Saying so beats iterating to a cap and returning a matrix
    # that quietly satisfies neither.
    trouble = []
    if (lo_c.sum(axis=1) > target_rows + 1e-6).any():
        trouble.append("a pool's lower bounds already exceed its voters")
    if (hi_c.sum(axis=1) < target_rows - 1e-6).any():
        trouble.append("a pool's upper bounds cannot cover its voters")
    if (lo_c.sum(axis=0) > target_cols + 1e-6).any():
        trouble.append("a party's lower bounds already exceed its votes")
    if (hi_c.sum(axis=0) < target_cols - 1e-6).any():
        trouble.append("a party's upper bounds cannot cover its votes")
    if trouble:
        raise RuntimeError("the method of bounds and the known margins "
                           "disagree: " + "; ".join(trouble))

    # THE UNBOUNDED ANSWER FIRST, KEPT IF IT IS ALREADY LEGAL. The tolerance is
    # three orders tighter than the one the bounds test asserts at (1e-9), so
    # nothing passes through here that a reader would call a violation.
    #
    # ``balance_margins`` is left exactly as it is — ``montecarlo`` runs it once
    # per draw and its output must not move — so the two adjustments it needs
    # for this use are made here, at the call.
    #
    # First, a tighter stop. Its criterion is relative to the GRAND TOTAL, so at
    # the shipped 1e-12 a small party's column can still be off by a microvote,
    # which is 1e-12 of that party's citywide share; the bounded iteration below
    # lands the same quantity at 2e-16. IPF converges geometrically and both
    # margins are simultaneously satisfiable at the fixed point, so 1e-15 costs
    # a handful of extra sweeps — measured at under a millisecond on every fit,
    # inside the shipped 2000-iteration cap — and takes the share error to 9e-16
    # and the pool margin to 1e-16.
    #
    # Second, one exact column rescale. Its loop ends on a ROW half-step, which
    # leaves the residual on the party margin; the bounded iteration ends on a
    # COLUMN half-step and has the opposite profile. Rescaling once puts the
    # party margin exactly on its total, which is why the tighter stop has to
    # come first: the correction is then ~1e-15, small enough that a cell
    # already pinned AT its Duncan-Davis ceiling is not pushed through it. It is
    # applied BEFORE the bound check, so the matrix checked is the matrix
    # returned.
    try:
        unbounded = balance_margins(R, electorate, party_votes, tol=1e-15)
    except RuntimeError:
        unbounded = None          # it did not converge; the bounded path may
    if unbounded is not None:
        c = unbounded * electorate[:, None]
        col = c.sum(axis=0)
        c = c * np.divide(target_cols, col, out=np.ones_like(col),
                          where=col > 0)[None, :]
        unbounded = c / np.maximum(electorate, 1e-12)[:, None]
        if bool((unbounded >= lo - 1e-12).all()
                and (unbounded <= hi + 1e-12).all()):
            return unbounded

    # THE SAME ARGUMENT, ONE CELL AT A TIME — and without it this does not
    # converge at all. A corner solution is full of exact zeros, and a
    # multiplicative step cannot move one: anything times nothing is nothing. So
    # the PA, capped at the Coloured pool's ceiling of 27,183 votes and zeroed
    # everywhere else, can only ever account for 27,183 of its 27,346 votes and
    # the party margin never closes. Those zeros are not a measurement —
    # ``PartyFit.identified`` says as much of any rate sitting on a boundary —
    # they are where least squares stopped. Seed each of them with the pool's
    # share of the votes the fit failed to place, which is the maximum-entropy
    # answer for a cell nothing is known about, and let the iteration move it.
    #
    # READ THE TRIGGER CAREFULLY — IT IS NOT THE BOUND. ``unplaced`` compares a
    # party's known total against its CLIPPED RAW FIT column, and the raw fit is
    # NNLS on the ward table: nothing ever asked it to reproduce a party total,
    # so it does not. At Ekurhuleni 2016 with the box removed entirely
    # (lo=0, hi=1, so the clip is inert) 15 of 25 parties are still seeded and
    # 3,716 votes — 0.41% of the city — are still "unplaced", with no bound
    # binding anywhere. A ceiling that clips a cell can ENLARGE the shortfall;
    # it is not what creates it. That is why this whole block now runs only
    # after the unbounded answer has been shown to be illegal.
    unplaced = np.maximum(target_cols - np.minimum(counts, hi_c).sum(axis=0), 0.0)
    blank = counts <= 0
    room = np.where(blank, target_rows[:, None], 0.0)
    room /= np.maximum(room.sum(axis=0), 1e-12)[None, :]
    counts = np.where(blank, np.minimum(room * unplaced[None, :], hi_c), counts)

    for _ in range(iters):
        counts = _scale_into_box(counts, lo_c, hi_c, target_rows)
        counts = _scale_into_box(counts.T, lo_c.T, hi_c.T, target_cols).T
        if (np.abs(counts.sum(axis=1) - target_rows).max()
                < tol * target_rows.sum()
                and np.abs(counts.sum(axis=0) - target_cols).max()
                < tol * target_rows.sum()):
            break
    else:
        raise RuntimeError("bounded margin balancing did not converge")

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
             party_list: list[str] | None = None,
             split_bloc: dict | None = None):
    """Fit every party's pool vector from one city's ward results.

    Composition is taken as at that election's polling day, not as at whichever
    census happens to be lying around.
    """
    shares, votes = ward_party_shares(city, year)

    # The pool is a set of people and three nested subsets of it; the party
    # rates act on the innermost one, the people who actually voted.
    counts = pool_counts(city, year, cfg, split_bloc=split_bloc)
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
    raw = fit_joint(comp, Y, vote)
    pool_votes = (comp * vote[:, None]).sum(axis=0)
    party_votes = (Y * vote[:, None]).sum(axis=0)

    # The method of bounds is data, not diagnostics. It was computed here and
    # read only to set a display flag, so a rate the ward arithmetic forbids was
    # emitted anyway — see :func:`balance_within_bounds`. Every fitted rate is
    # now held inside its own interval while both known margins are matched, so
    # the three things known about the election hold together.
    #
    # ENFORCING a constraint is not the same as REPLACING the solver. Five of
    # the ten production fits — joburg 2011, joburg 2016, tshwane 2016,
    # ekurhuleni 2016, mangaung 2016 — violate no bound at all, and for those
    # the unbounded balance is returned as it stands. It has to be: at
    # Ekurhuleni 2016 the bounded path cost 0.61% of ward SSE with nothing to
    # correct, purely through seeding that fires on a condition the bounds have
    # no part in.
    dd = [bounds(Y[:, i], comp, vote) for i in range(len(universe))]
    lo = np.column_stack([b[:, 0] for b in dd])
    hi = np.column_stack([b[:, 1] for b in dd])
    R = balance_within_bounds(raw, pool_votes, party_votes, lo, hi)

    fits: dict[str, PartyFit] = {}
    for i, party in enumerate(universe):
        y = Y[:, i]
        fits[party] = PartyFit(
            party=party,
            citywide=float(np.average(y, weights=vote)),
            rates=R[:, i],
            r2=_r2(y, comp @ R[:, i], vote),
            bounds=dd[i],
        )

    pool_votes = (comp * vote[:, None]).sum(axis=0)
    # ``raw`` and ``Y`` are returned so a test can assert on the FIT rather than
    # on the balanced product. IPF forces both margins whatever it is handed, so
    # every constraint checked after ``balance_margins`` is a statement about
    # ``balance_margins``; reconstructing the fit in the test instead would let
    # the two drift (the universe filter below is easy to miss) and would assert
    # about a matrix production never used.
    return fits, {"wards": wards, "comp": comp, "votes": vote,
                  "shares": shares, "tilt_dims": tilt_dims, "counts": counts,
                  "pool_votes": pool_votes, "categories": counts.categories,
                  "provenance": provenance, "year": year,
                  "rates": counts.rates, "raw_rates": raw, "parties": universe,
                  "Y": Y}


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




def turnout_record(city: cityconfig.City, cfg: Config, before: str | None = None,
                   split_bloc: dict | None = None,
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
            out[year] = pool_counts(city, year, cfg,
                                    split_bloc=split_bloc).rates["turnout"]
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
    the last election's turnout times the historical log-range either way.

    **The same argument applies to the top, and used not to be applied there.**
    The band was additionally capped at the highest turnout the city had ever
    recorded, which is the identical error the paragraph above rejects, pointing
    the other way. It bound almost everywhere it could:

        target 2016   4 of 4 pools had high == mode, in every metro
        target 2021   3 or 4 of 4 pools, in every metro
        target 2026   0 of 4 — because 2021 was the lowest on record

    A mode equal to the high is a triangular that cannot rise at all. So every
    historical backtest this repository has ever run was scored with turnout
    forbidden from increasing, while the live forecast — the one case where the
    cap does not bind — was fine. That is the worst possible arrangement: the
    instrument was biased in exactly the runs used to judge the model, and not
    in the run being judged. Turnout has risen at a South African local
    election before (2000 → 2006), so the cap was not even describing the
    record it claimed to come from.

    **THE BAND IS BUILT IN LOGIT SPACE, and that is the whole mechanism.** The
    constraint wanted here is "turnout does not change by more than it has been
    seen to change", which is a statement about the CHANGE; a cap on the LEVEL
    is a different statement that happens to sometimes imply it. Working in log
    space needed a cap because ``centre × exp(spread)`` can exceed 1, and a
    turnout above 100% is not a bold forecast but a broken one — the first
    version of this capped at the observed maximum, the second at 1.0, and both
    are levels standing in for a constraint on change.

    A turnout is a proportion, so the natural scale for it is the logit, which
    is what proportions are modelled on generally and what every serious
    treatment of turnout uses. Then::

        spread = max observed |logit(t_i) - logit(t_j)|
        band   = expit(logit(previous) ∓ spread)

    reads exactly as the sentence intended, is symmetric in the scale the
    quantity actually lives on, and **cannot leave (0, 1) for any spread
    whatever**, so there is no cap anywhere and none of the pinning above can
    recur. It also fixes the artefact the log-space version left behind:
    Tshwane's Indian/Asian pool is small and noisy, its observed log-range is
    wide, and the log band ran to a 100% turnout ceiling. In logit space the
    same evidence gives a wide but finite band.
    """
    if not record:
        return [(0.30, 0.50, 0.70)] * n_pools
    years = sorted(record)
    arr = np.array([record[y] for y in years])
    previous = arr[-1]
    bands = []
    def _logit(x):
        x = np.clip(x, 1e-4, 1 - 1e-4)
        return np.log(x / (1 - x))

    def _expit(x):
        return 1.0 / (1.0 + np.exp(-x))

    for g in range(n_pools):
        column = np.clip(arr[:, g], 1e-4, 1 - 1e-4)
        centre = float(np.clip(previous[g], 1e-4, 1 - 1e-4))
        # The observed range of CHANGE, on the scale a proportion lives on.
        # One observation supports no statement about change, so it falls back
        # to 0.30 logits — the same default the log version used, now in the
        # units it is actually applied in.
        lg = _logit(column)
        spread = float(lg.max() - lg.min()) if len(column) > 1 else 0.30
        low = float(_expit(_logit(centre) - spread))
        high = float(_expit(_logit(centre) + spread))
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
        # NOTE: only the "city" band above BINDS. `constrain_pool_turnout`
        # reads `limits["city"]["low"]/["high"]` and nothing anywhere reads
        # `limits["pool"]` — grep it. The per-pool bands are emitted for the
        # interactive and for inspection, and a reader who assumes the name
        # means the draw is constrained per pool is wrong. Recorded rather
        # than deleted because `export_interactive` consumes the emitted
        # block. MODEL-LOG §1.69.
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
                         cfg: Config, fitted_on: str,
                         split_bloc: dict | None = None) -> np.ndarray:
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
    counts = pool_counts(city, fitted_on, cfg, split_bloc=split_bloc)
    composition = counts.composition("registered")
    by_ward = {w: composition[i] for i, w in enumerate(counts.wards)}

    # A missing roll used to stand in the fitting election's own and print a
    # warning. That branch is gone with the wrong-city fallback that made it
    # reachable: :func:`_target_roll` now refuses and names the file, because
    # the two cases it was covering are both worse served by a stand-in. A
    # future target with no roll is a data-acquisition gap that should be
    # stated once, loudly, rather than absorbed into pool sizes five years out
    # of date; and the case that actually reached it in practice was not a
    # missing roll at all — it was another city's roll being loaded and its
    # ward codes failing to join.
    roll = _target_roll(city, target)

    total = np.zeros(len(counts.categories))
    unmatched = 0.0
    for ward, registered in roll.items():
        if ward in by_ward:
            total += by_ward[ward] * registered
        else:
            unmatched += registered
    share_unmatched = unmatched / sum(roll.values()) if sum(roll.values()) else 1.0
    if share_unmatched > 0.5 or total.sum() <= 0:
        # A WARNING IS NOT ENOUGH WHEN NOTHING MATCHED. Tshwane 2026 printed
        # "100.0% of the 2026 roll is in wards with no measured composition" and
        # then emitted a spec in which EVERY POOL HELD ZERO REGISTERED VOTERS.
        # A pool's votes are its registration times a drawn turnout, so a spec
        # like that forecasts an election in which nobody votes, and it sat on
        # disk looking like any other artefact — it was found only because a
        # regression test asserted on a key it happened to be missing.
        #
        # This is a ward-code join failure. WHAT IT IS NOT, ANY MORE, IS A
        # WRONG-FILE BUG — and that is the only cause it has ever actually had.
        # The message here used to say "almost certainly a delimitation
        # boundary", and it was published saying so, while the real cause was
        # `_target_roll` loading Johannesburg's roll for every other city. Read
        # the sample codes below before reaching for geography: if they are
        # another city's prefix, the roll is the wrong file, not the wrong
        # vintage.
        sample = sorted(w for w in roll if w not in by_ward)[:3]
        known = sorted(by_ward)[:3]
        raise SystemExit(
            f"{city.name} {target.year}: {share_unmatched:.1%} of the roll is in "
            f"wards with no measured composition, and the pools would hold "
            f"{total.sum():,.0f} registered voters between them. Refusing to "
            f"emit a spec whose pools are empty.\n"
            f"  unmatched ward codes in the {target.year} roll: "
            f"{', '.join(sample) or '(none)'}\n"
            f"  ward codes the composition fitted on {fitted_on} is keyed on: "
            f"{', '.join(known) or '(none)'}\n"
            f"  If those two share a prefix, it is a delimitation change and "
            f"the crosswalk needs fixing (or fit the composition on a year "
            f"whose wards match). If they do NOT share a prefix, the roll "
            f"belongs to a different city and the bug is upstream of this "
            f"check.")
    if share_unmatched > 0.01:
        print(f"  ! {share_unmatched:.1%} of the {target.year} "
              f"roll is in wards with no measured composition")
    return total


def _target_roll(city: cityconfig.City, target: cityconfig.Target,
                 ) -> dict[str, float]:
    """Ward -> registered voters at the target, from THIS CITY'S roll.

    An election that has been held publishes its own roll inside the result
    file, so that is read first. Only a future target — 2026 is the single year
    in ``CALENDAR`` with no results — needs the separately published
    pre-election roll, and that lands in the city's own processed directory.

    THERE IS NO FALLBACK TO ANOTHER DIRECTORY, AND THERE MUST NOT BE. This
    function used to end::

        path = target.processed / f"vd_ward_{target.year}.csv"
        if not path.exists():
            path = Path("data/processed") / f"vd_ward_{target.year}.csv"

    and ``data/processed/`` is not a shared root: it is *Johannesburg's* own
    directory, because ``cities/joburg.toml`` is the one config carrying
    ``legacy_processed_root`` (see :meth:`cityconfig.City.processed`). So the
    second line handed **every other city Johannesburg's ward roll**. The
    2026 file's first data row is ward 79800094; Johannesburg's wards are
    798000xx and Tshwane's are 799000xx, so 100% of the codes then failed to
    join — and the caller reported that as *"almost certainly a delimitation
    boundary"*, a geographic diagnosis of a wrong-file bug. That refusal was
    published. It blocked the whole multi-city expansion behind an imaginary
    delimitation problem for as long as it stood.

    Note the fallback could never have helped even the city it stole from:
    Johannesburg's 2026 target IS the default target, so ``target.processed``
    already resolves to the bare ``data/processed/`` and the first line finds
    the file. The branch was reachable only by a city it could only mislead.

    A missing roll is therefore a refusal naming the file it wanted, never a
    silent substitution.
    """
    if cityconfig.CALENDAR[target.year].results:
        try:
            return ward_totals(city, target.year)[0]
        except SystemExit:
            pass
    path = target.processed / f"vd_ward_{target.year}.csv"
    if not path.exists():
        raise SystemExit(
            f"{city.name} {target.year}: no ward roll for this city. Wanted "
            f"{path}, which does not exist.\n"
            f"  This is a missing input, not a modelling problem: the "
            f"{target.year} roll is published per voting district and has to "
            f"be acquired and cleaned into that path for {city.slug} the same "
            f"way data/processed/vd_ward_2026.csv was for joburg. Every "
            f"non-Johannesburg city needs its own; there is no shared one, and "
            f"reading another city's is how this used to report a delimitation "
            f"boundary that was never there.")
    # ONE VD THAT STRADDLES TWO WARDS BELONGS TO BOTH, IN PROPORTION.
    #
    # Until 2026-08-26 this read `vd_registered` and skipped every row after a
    # VD's first (`vd in seen`), so each of the 181 SPLIT VDs landed WHOLE in
    # whichever ward sorted first. `montecarlo.ward_parts` reads the same file
    # and uses `part_registered` — the apportioned split, which is assumption A1
    # and the entire reason the column exists — so the model built its pools on
    # one map of the city and its ward tallies on another. **124 of the 135
    # wards disagreed**, worst by 16,657 registered voters (79800008).
    #
    # NOTHING COULD HAVE CAUGHT IT: sum(part_registered) == vd_registered for
    # all 865 VDs, so the citywide total is identical either way (2,348,781) and
    # every conservation check passes under both rules. Nor could the backtest —
    # `_target_roll` is reached only when CALENDAR[year].results is None, so all
    # sixteen city-years take the ward_totals branch. It was live at 2026 only,
    # in the published forecast, and unscoreable.
    #
    # The corroboration is independent of A1: wards are delimited to hold
    # roughly equal populations, and the old rule gave Johannesburg ward rolls
    # ranging 5,902 to 36,649 (CV 30.0%) against 14,791 to 20,007 (CV 11.9%)
    # under this one. A 6.2x spread is not something a delimitation produces.
    # MODEL-LOG §1.99; guarded by tests/test_ward_parts.py.
    roll: dict[str, float] = defaultdict(float)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            vd = (row.get("VD_Number") or "").strip()
            ward = (row.get("WardID_" + target.year) or row.get("Ward") or "").strip()
            if not vd or not ward:
                continue
            roll[ward] += float(row.get("part_registered")
                                or row.get("vd_registered") or 0)
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


def dirichlet_alpha(splits: list[np.ndarray],
                    min_share: float | None = None) -> float:
    """Method of moments: alpha + 1 = m(1-m)/Var, over members that matter.

    ``min_share`` is not a tidying detail. A pool has forty-odd members and
    most are parties polling a fraction of a percent whose share is stable
    simply because it is tiny; taking the median across all of them returns the
    behaviour of the noise floor, not of the pool. Estimated that way every
    pool pinned to the 200 ceiling, which would have made the simulation far
    more confident than the evidence warrants — the opposite of what a
    concentration parameter is for.
    """
    # Resolved in the BODY, never as a default argument: a default is
    # evaluated once at import, which froze SHARE_FLOOR, SPINE_K and LEVEL_DF
    # at four sites and made every sweep of them read as flat (§1.33).
    min_share = ALPHA_MIN_SHARE if min_share is None else min_share
    if len(splits) < 3:
        return ALPHA_FALLBACK
    arr = np.array(splits)
    m = arr.mean(axis=0)
    v = arr.var(axis=0, ddof=1)
    usable = (v > 1e-12) & (m > min_share) & (m < 1 - 1e-4)
    if usable.sum() < 2:
        usable = (v > 1e-12) & (m > 1e-3) & (m < 1 - 1e-4)
    if not usable.any():
        return ALPHA_FALLBACK
    est = (m[usable] * (1 - m[usable]) / v[usable]) - 1.0
    # Weight by member size: the pool's dispersion is what its large members do.
    return float(np.clip(np.average(est, weights=m[usable]),
                         ALPHA_FLOOR, ALPHA_CEILING))


# Parties that arrived as a SPLIT rather than from nothing: a known figure
# left a known party and took a share of it with them. Declared here with
# their evidence, exactly as `splinter_record`'s pairs are, because which
# party someone split from is a judgement and cannot be read off a result
# file.
#
# They are removed from the entrant record because they are not entrants and
# because leaving them in makes it describe nobody. Measured across eight
# metros before 2021, the arrivals contesting more than 90% of wards are: the
# EFF eight times (3.12% to 11.64%), the AIC once at 1.51% — and twelve
# vanity registrations, none above 0.43%, of which the largest is the
# Democratic Liberal Congress. The 95th percentile of that mixture is 11.10%,
# and it IS the EFF. Sizing the Nationalist Coloured Party of South Africa by
# it is how Cape Town came to assign 155% of its electorate to newcomers.
# ---------------------------------------------------------------------------
# THE RULE, because three places used to answer this question and disagree.
#
# A party is a SPLIT if a NAMED person left a NAMED party and took a share of
# its vote with them. That claim needs a person, a party and a date, and it is
# a judgement — no result file records it. Everything else is an ENTRANT.
#
# The two are sized by different machinery and it is not a matter of degree:
#   split   -> a FRACTION OF ITS PARENT (`splinter_record`: COPE took 0.140 of
#              the ANC, the EFF 0.162, MK 0.246) and it inherits the parent's
#              pool vector, because that is what splitting means.
#   entrant -> the TYPICAL result of arrivals that contested as much of a city,
#              spread evenly over the pools as a stated placeholder.
#
# This dict is now the single source of truth. It was three: this list, the
# `pairs` in `splinter_record`, and a `parent` field in each city's judgement
# file — and they disagreed. ActionSA was in the first, absent from the
# second, and blank in the third, so it was removed from the entrant record
# for being a split AND sized as an entrant for having no parent, arriving at
# 0.1% against an actual 18.12%. `splinter_record`'s pairs stay separate
# because they answer a different question (how much a split took, measured
# off two national elections) and not every split has a pair to measure.
@dataclass(frozen=True)
class Split:
    """One party that broke off another.

    ``parent``        the party it left, whose pool vector it inherits.
    ``measured_from`` the (NPE before, NPE after) pair its share of the parent
                      is measured across, or None where no such pair exists —
                      ActionSA never contested a national election before its
                      first local one, so it contributes no measurement and
                      is sized from the ones that do.
    ``home``          the metro code where the leader's own following is, or
                      None. **This is the single largest thing about a split
                      and the model was blind to it.**
    ``why``           the person, the party and the date. This is the whole
                      evidence for the classification and it is required.

    HOW MUCH A SPLIT TAKES DEPENDS ALMOST ENTIRELY ON WHETHER IT IS AT HOME.
    Measured as a fraction of the parent's previous vote, in each metro:

        split          leader's city   at home   median elsewhere   ratio
        GOOD 2019      Cape Town         0.056        0.006          x8.7
        ActionSA 2021  Johannesburg      0.611        0.103          x5.9
        MK 2024        eThekwini         0.885        0.024         x36.7

    Three splits, three cities, the same direction every time. It is not the
    leader's fame: Patricia de Lille was at least as well known nationally in
    2019 as Julius Malema was in 2014, and GOOD took 0.9% of the DA's vote in
    Johannesburg against 5.6% in Cape Town. What travels is not a reputation,
    it is a constituency.

    WHY THIS MATTERED. The record used to size every split — COPE 0.140, EFF
    0.162, MK 0.246 — is measured in JOHANNESBURG, and none of those three
    leaders was based there. They are AWAY figures, and they were being
    applied to ActionSA, whose leader had been the mayor of the city it was
    contesting. The home cases run 0.056 to 0.885; the away cases sit around
    0.02 to 0.25. Sizing a home split from away numbers is why ActionSA came
    out at 5.08% against an actual 16.1%.
    """

    parent: str
    measured_from: tuple[str, str] | None
    why: str
    home: str | None = None


# How many home-city splits must be on record before they are used to size
# one. Two is the smallest number that is an average rather than an
# anecdote; at target 2021 there is one and the model says so.
MIN_HOME_SPLITS = 2

# How much of a splinter's starting pool vector is its PARENT's, the rest being
# the city's own composition. MEASURED: fitting each splinter's vector at its
# first election and regressing on (parent, city average) over 22 metro-cases
# gives a median of 0.35 — EFF 0.89, GOOD 0.28, ActionSA about 0.02. Pure
# inheritance was the assumption and it is wrong for two of the three.
SPLINTER_PARENT_WEIGHT = 0.35

SPLITS: dict[str, Split] = {
    "COPE": Split("ANC", ("2004", "2009"),
                  "Lekota and Shilowa, after the ANC's 2008 Polokwane split",
                  home=None),          # national figures, no one metro base
    "EFF":  Split("ANC", ("2009", "2014"),
                  "Malema and the ANC Youth League leadership, expelled from "
                  "the ANC 2012-13",
                  home=None),          # Limpopo roots, no metro base
    "NFP":  Split("IFP", ("2009", "2014"),
                  "Magwaza-Msibi, the IFP's National Chairperson, 2011",
                  home="ETH"),         # KZN
    "GOOD": Split("DA", ("2014", "2019"),
                  "De Lille, the DA's own mayor of Cape Town, who left in 2018",
                  home="CPT"),
    "MK":   Split("ANC", ("2019", "2024"),
                  "Zuma, a former State President, 2023",
                  home="ETH"),         # KZN: 0.885 there against 0.246 in JHB
    "ASA":  Split("DA", None,
                  "Mashaba, the DA's own mayor of Johannesburg, who resigned "
                  "the party in October 2019",
                  home="JHB"),
}


def classify_arrival(party: str, declared_parent: str | None = None
                     ) -> tuple[str | None, str]:
    """SPLIT OR ENTRANT — the definition, and the only place that decides.

    Returns ``(parent, why)``; a parent of None means entrant.

    A party is a **split** if a NAMED person left a NAMED party and took a
    share of its vote with them. That claim needs a person, a party and a
    date, no result file records any of it, so it is declared in
    :data:`SPLITS` with its evidence — or, for a case only one city knows
    about, in that city's judgement file, which wins when it says anything.

    Everything else is an **entrant**: a name on a ballot, with no machine and
    no inherited vote.

    The two are sized by different machinery and it is not a matter of degree.
    A split takes a fraction of its PARENT and inherits the parent's pool
    vector, because that is what splitting means. An entrant is sized at the
    typical result of arrivals that contested as much of a city.

    THIS FUNCTION EXISTS BECAUSE THE ANSWER USED TO LIVE IN THREE PLACES —
    this list, the ``pairs`` argument of :func:`splinter_record`, and a
    ``parent`` field in every city's judgement file — and they disagreed.
    ActionSA was named in the first, missing from the second and blank in the
    third, so it was excluded from the entrant record for being a split and
    then sized as an entrant for having no parent, arriving at 0.1% against an
    actual 18.12%. Both other callers now derive from :data:`SPLITS`:
    ``splinter_record`` builds its pairs from it, ``entrant_record`` excludes
    it, and a test fails if any of them drift apart.
    """
    declared = (declared_parent or "").strip().upper()
    if declared:
        return declared, "declared in this city's judgement file"
    split = SPLITS.get(party)
    if split is not None:
        return split.parent, split.why
    return None, "no lineage on record: arrived from nothing"


def entrant_record(transitions, codes=METRO_CODES,
                   exclude=frozenset(SPLITS)) -> list[float]:
    """Every share won by a party that arrived FROM NOTHING.

    The record, not a judgement. A party arriving from nothing is the single
    largest error the model makes — ActionSA won 44 of Johannesburg's 270 seats
    in 2021 and the model gave it zero, because it held 0.0000% of the 2019
    baseline and multiplicative growth cannot lift a party off zero. The same
    happened to the PA's 8 seats. Between them that is the whole of the model's
    112-seat absolute error at that target.

    **A split is not an entrant and is excluded.** Both are absent from the
    previous result, so the arithmetic cannot tell them apart, but nothing
    else about them is alike: a split starts with a leader, a machine and a
    share of a known party's vote, and is sized by `splinter_record` as a
    fraction of that parent. An entrant starts with a name on a ballot. Mixing
    them gave one distribution whose upper half is the EFF and whose lower
    half is everybody else, and then handed the EFF's number to everybody
    else.
    """
    seen: list[float] = []
    for code in codes:
        for before, after in transitions:
            a, b = metro_citywide(code, before), metro_citywide(code, after)
            if not a or not b:
                continue
            reach = _ward_reach(code, after)
            for party, share in b.items():
                if party in exclude:
                    continue
                if a.get(party, 0.0) <= 1e-4 < share:
                    seen.append((share, reach.get(party, 1.0)))
    return sorted(seen)


def _ward_reach(code: str, year: str) -> dict[str, float]:
    """Fraction of wards each party fielded a ward candidate in.

    Presence on the ward ballot, not votes on it — see
    ``levels.contestation``, which measures the same quantity for the drawer
    and carries the argument. A party is listed in a voting district's rows
    because it stood there, so counting the rows is a nomination fact a
    forecaster has before polling day; counting only the rows that scored
    would read the result this feeds a forecast of.
    """
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
        wards[P.canonical(row["sPartyName"])].add(ward)
    return {p: len(w) / len(seen) for p, w in wards.items()} if seen else {}


def home_splinter_record(exclude: str | None = None,
                         before_year: str | None = None) -> dict[str, float]:
    """What each split took OF ITS PARENT, measured in its leader's own city.

    Returns ``{party: fraction}``. ``before_year`` drops any split that had not
    happened yet, exactly as :func:`splinter_record` does, and **every caller
    that is building a forecast passes the target's year.**

    THE HISTORY, BECAUSE THE DEFAULT USED TO BE THE OTHER WAY. This record
    ignored the target cutoff on purpose, declared through
    ``backtest.FITTED_ON["splinter_home"]`` and printed in the in-sample
    banner. The reasoning, which is the project owner's: the home/away effect
    is large and consistent (Split's docstring: x8.7, x5.9, x36.7 across three
    cities) but only one home split had happened before 2021, and one
    observation is not a sample — sizing ActionSA from De Lille's 0.056 alone
    put it at 1.87% against an actual 16.1%. The choice was between a structure
    we have measured and cannot populate in period, and a number we know is
    wrong.

    WHAT NOBODY DID WAS PRICE IT, and an independent audit did (2026-08-14).
    ``pools_2021.json`` carried the home record as GOOD 0.0558 (2019) and MK
    0.8853 (**2024**), so MK's eThekwini result four years after the target was
    what sized ActionSA in the 2021 backtest::

        Johannesburg 2021      seat error   CRPS    ASA predicted (actual 18.12%)
        as it stood                    65   47.4    12.24%
        home record honest            102   79.6     4.76%
        uniform-swing                 126  126.0    —

    Johannesburg 2021 is one of the three city-years the model wins and it is
    the city being published, and **57% of its margin over uniform swing was a
    2024 result**. Across nine city-years the honest figures are CRPS 303.6
    (was 271.4) and seat error 400 (was 363) against uniform swing's 376/376.

    So the default is now filtered, per ITERATING.md: a historical score has to
    be honest before anything measured against it means anything. The old
    behaviour is still reachable — ``--retrospective-home`` — because the
    question it answers ("what is this rule worth once the record exists?") is
    a real one; it is just not a forecast.

    **The filter is also the right answer for 2026 with no special case.** MK's
    2024 split genuinely precedes a 2026 target, so it is included there and
    excluded at 2021 by the same rule.

    ``exclude`` drops one party, and every caller passes the party it is
    sizing. Retrospective is one thing; letting ActionSA's own 0.611 set
    ActionSA's expectation is another, and it would make the rule look good by
    construction.
    """
    out: dict[str, float] = {}
    for party, split in sorted(SPLITS.items()):
        if party == exclude or split.home is None or split.measured_from is None:
            continue
        before, after = split.measured_from
        if before_year and int(after) >= int(before_year):
            continue                      # had not happened yet at the target
        a = metro_citywide(split.home, before) or _npe_citywide_for(split.home, before)
        b = metro_citywide(split.home, after) or _npe_citywide_for(split.home, after)
        if a.get(split.parent, 0) > 0 and b.get(party, 0) > 0:
            out[party] = b[party] / a[split.parent]
    return out


def splinter_record(city: cityconfig.City | None, before_year: str | None = None,
                    splits: dict | None = None,
                    at_home: bool = False,
                    city_code: str | None = None) -> list[float]:
    """What share of its parent's vote each known splinter took, measured.

    The three splits this city has on record, each as the splinter's first
    result over the parent's previous one::

        COPE from the ANC   9.61% against 68.56%   0.140
        EFF  from the ANC  10.13% against 62.35%   0.162
        MK   from the ANC  12.22% against 49.62%   0.246

    Which party split from which is a judgement and is declared here with its
    evidence; how much it took is not, and is measured. An earlier version of
    this used one half, which was invented and three times too large.

    ``before_year`` drops any split that had not happened yet, which is the
    difference between a measurement and a leak: the MK pair reads 2024, so a
    backtest at 2016 was sizing its splinters on a split eight years in its
    own future. The years were hardcoded and the caller passed no target, so
    nothing could have noticed. ``backtest.FITTED_ON`` used to carry a
    "splinter" key announcing this instead — an announcement no scenario could
    ever clear, so no target before 2021 could print an all-clear, whether or
    not it was owed one. Enforcing it here is the same trade γ already makes.
    """
    here = city_code or (city.code if city is not None else None)
    out = []
    for splinter, split in sorted((splits if splits is not None
                                   else SPLITS).items()):
        if split.measured_from is None:
            continue          # a split with no national pair to measure across
        parent, (before, after) = split.parent, split.measured_from
        if before_year and int(after) >= int(before_year):
            continue
        # MEASURE EACH SPLIT WHERE ITS LEADER ACTUALLY WAS. `at_home` asks for
        # the fractions a split takes in its leader's OWN city; the default
        # asks for what it takes in a city where the leader has no following.
        # They are different quantities by an order of magnitude (Split's
        # docstring has the three cases), and reading one as the other is why
        # a home-city split was being sized from away numbers.
        code = split.home if at_home else here
        if code is None or (at_home and split.home is None):
            continue          # no home on record; it contributes to neither
        if not at_home and split.home == here:
            continue          # this city IS its home; not an away observation
        a, b = metro_citywide(code, before), metro_citywide(code, after)
        if not a or not b:
            a = a or _npe_citywide_for(code, before)
            b = b or _npe_citywide_for(code, after)
        if a.get(parent, 0) > 0 and b.get(splinter, 0) > 0:
            out.append(b[splinter] / a[parent])
    return sorted(out)


# The narrowest a splinter band may be, in log units. A record of one
# observation has no spread of its own, and (min, median, max) of a single
# number is a band of ZERO WIDTH — a triangular that puts probability 1 on a
# point and probability 0 on everything else.
#
# That is not a corner case here, it is the normal state: at target 2021 SEVEN
# of the eight metros have an away-splinter record of exactly one observation
# (Johannesburg alone has four). So for seven metros the model was asserting
# that an arrival's size was known exactly. ActionSA then took 19 of Tshwane's
# 214 seats against a band of 0.4%-0.4%, an outcome the forecast had ruled out
# entirely rather than merely thought unlikely.
#
# 0.90 is the log-spread of the pooled cross-metro record itself, so a thin
# record inherits the spread the full record shows rather than a typed one; it
# is a floor, and a city with a richer record than that keeps its own.
# THE SELECTION RULE BEHIND THE DOMINANT WIDTH LEVER, promoted from inline
# literals 2026-08-22 (MODEL-LOG §1.69). `dirichlet_scale` — a multiplier on
# what `dirichlet_alpha` returns — has been registered and swept for weeks and
# JUDGEMENT-CALLS.md §B calls the per-pool concentration "the model's dominant
# width lever (83-98% of drawn variance for every party except ANC and DA)".
# The rule that decides what goes INTO that fit was four numbers typed in the
# function body, invisible to
# `test_every_tunable_constant_is_in_the_judgement_register`, which reads only
# module-level assignments and DEFAULTS.
#
# `dirichlet_alpha`'s own docstring says what is at stake: without the share
# cut "every pool pinned to the 200 ceiling", i.e. the simulation far more
# confident than the evidence warrants. A constant that can saturate the
# dominant width lever is not a tidying detail.
# THE TRIANGULAR SUPPORT OF EVERY SEEDED ARRIVAL, consumed in `montecarlo`
# as `low, _, high = seed_band`. The long comment beside the code narrates why
# the CENTRE moved from median to mean and why a `clip(reach, 0.05, 0.95)` was
# a disaster — and never mentions that the surviving percentile pair is itself
# a choice. 25/95 rather than 10/90 or 5/95 sets how wide an ActionSA-class
# arrival's band is. Promoted 2026-08-22, §1.69.
ARRIVAL_BAND_LO = 0.25
ARRIVAL_BAND_HI = 0.95

ALPHA_MIN_SHARE = 0.01     # pool members below this are noise floor, not signal
ALPHA_FLOOR = 1.0          # a Dirichlet concentration below 1 is a spike
ALPHA_CEILING = 200.0      # above this the pool is effectively deterministic
ALPHA_FALLBACK = 12.0      # too few splits to fit; neither confident nor flat

SPLIT_SD_FLOOR = 0.90


def pooled_splinter_record(before_year: str | None = None) -> list[float]:
    """Every away-splinter fraction observed in any metro, for the spread.

    A single city's record is usually one number (see SPLIT_SD_FLOOR). How much
    splinters VARY is a question the whole record can answer even when one
    city's cannot, and it is the same borrowing the pool vectors already do:
    direction from the city, magnitude from everyone.
    """
    out: list[float] = []
    for code in METRO_CODES:
        out.extend(splinter_record(None, before_year, city_code=code))
    return sorted(out)


def _band_from(record: list[float], label: str, pooled: list[float] | None
               ) -> tuple[float, float, float, str]:
    """(lo, mid, hi) for a splinter fraction, never degenerate.

    The centre is this city's own record; the WIDTH comes from whichever of the
    city's record and the pooled cross-metro record says more, floored at
    SPLIT_SD_FLOOR. Built in log space, so the band is 10th-to-90th percentile
    of a lognormal rather than the min and max of however many observations
    happened to exist — which is what made a record of one collapse.
    """
    mid = float(np.median(record))
    if mid <= 0:
        return min(record), mid, max(record), label
    spreads = []
    for sample in (record, pooled or []):
        vals = [v for v in sample if v > 0]
        if len(vals) >= 2:
            spreads.append(float(np.std(np.log(vals), ddof=1)))
    sd = max(spreads) if spreads else SPLIT_SD_FLOOR
    sd = max(sd, SPLIT_SD_FLOOR)
    lo = float(mid * np.exp(-1.2816 * sd))
    # A splinter takes a share OF ITS PARENT, so 1.0 is the whole of it and
    # there is nothing above that to draw. Johannesburg's own record is wide
    # enough that the lognormal top came out at 1.17 — a party taking 117% of
    # the vote its parent had, which is not a bold forecast but an arithmetic
    # impossibility.
    hi = float(min(mid * np.exp(1.2816 * sd), 1.0))
    if len(record) < 2:
        label += f", widened from the pooled record (n={len(pooled or [])})"
    return lo, mid, hi, label


def _npe_citywide_for(code: str, year: str) -> dict[str, float]:
    """One metro's NPE shares by IEC code, for reading a split where it lived."""
    template = cityconfig.CALENDAR[year].results
    if not template:
        return {}
    path = Path(str(template).replace("{CODE}", code))
    if not path.exists():
        path = Path("data/raw/elections") / path.name
    if not path.exists():
        return {}
    counts: dict[str, int] = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") in (None, "", "PR"):
                counts[P.canonical(row["sPartyName"])] += int(
                    float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()} if total else {}


def arrival_group_record(before_year: str | None = None
                         ) -> list[tuple[float, float]]:
    """What ARRIVALS TAKE AS A GROUP in a metro, and how concentrated it is.

    One entry per metro-year strictly before the target, as
    ``(group total share, implied Dirichlet concentration)``.

    THE REASON THIS EXISTS. The model sizes each arrival on its own, through a
    single generic entrant slot with a 25% probability. Scored across nine
    city-years (``src/arrivals.py``), that gives a median seat to **one of the
    thirty-two parties that arrived and won one**, 14 seats against 130. The six
    it sizes anywhere near right are the six that received the entrant slot, and
    there is exactly one of those per city; the other twenty-six get about
    0.07% each because nothing is left to give them.

    The quantity that behaves regularly is the GROUP TOTAL. Over sixteen
    metro-years it runs 0.31% to 19.99%, median 3.11%, and it is rising —
    2016 spans 0.31-4.74% against 2021's 1.53-19.99%. Drawing that and splitting
    it is a far smaller claim than sizing thirty parties independently, and it
    is the external review's item 4.

    The concentration matters as much as the total, because the split is not
    even: the largest arrival took 91% of the group in Johannesburg 2021 and 20%
    in Cape Town 2016. The implied symmetric-Dirichlet α ranges 0.22 to 20.66
    with a median of 4.85, so the draw has to be able to produce both "one party
    takes almost all of it" and "thirty parties share it".
    """
    out: list[tuple[float, float]] = []
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    for year in lge:
        if before_year and int(year) >= int(before_year):
            continue
        prev = cityconfig.preceding(year, "NPE")
        if not prev:
            continue
        for code in METRO_CODES:
            local = metro_citywide(code, year)
            natl = _npe_citywide_for(code, prev)
            if not local or not natl:
                continue
            arr = {p: s for p, s in local.items()
                   if p != "IND" and s > 0 and natl.get(p, 0.0) <= 0}
            if len(arr) < 3:
                continue
            total = float(sum(arr.values()))
            shares = np.array(list(arr.values())) / total
            n = len(shares)
            var = float(shares.var())
            mean = 1.0 / n
            alpha = max((mean * (1 - mean) / max(var, 1e-9)) - 1.0, 0.01)
            out.append((total, float(alpha)))
    return out


def arrival_group_spec(before_year: str | None, reach: dict[str, float],
                       parties: list[str]) -> dict | None:
    """The group total to draw, and how to split it between named arrivals.

    Split weights are each arrival's WARD REACH, because that is what predicts
    an arrival's size and nothing else measured does. Over 258 arrivals across
    eight metros and two elections:

        corr(ward reach, log vote share)      +0.393
        corr(metros contested, log vote)      +0.145
        geographic concentration of the vote  -0.09  (task #22, established parties)

    Arrivals that took 0.5% or more — the ones that win seats — have a **median
    ward reach of 99% against 33% for the rest**, and among those contesting
    60-100% of wards 16% clear 0.5% against 0-3% everywhere else. Expected vote
    is close to proportional to reach above about 5% of wards, so reach is used
    directly as the weight rather than through a fitted curve.

    Ward reach is a nomination fact, published weeks before polling day, so this
    is a forecast input and not hindsight — the same justification
    ``levels.contestation`` runs on.

    Returns None when there is no roster to split between, which is every target
    that has not been held. **The 2026 forecast therefore still depends on the
    generic entrant slot until nomination lists close.**
    """
    record = arrival_group_record(before_year)
    if not record or not parties:
        return None
    totals = np.array([t for t, _ in record])
    alphas = np.array([a for _, a in record])
    logs = np.log(totals)
    weights = {p: max(float(reach.get(p, 0.0)), 0.02) for p in parties}
    return {
        "total_log_median": float(np.mean(logs)),
        "total_log_sd": float(np.std(logs, ddof=1)) if len(logs) > 1 else 0.8,
        "alpha": float(np.median(alphas)),
        "weights": weights,
        "n_observations": len(record),
        "derived_from": (f"{len(record)} metro-years before {before_year}; "
                         f"split by ward reach (corr +0.393 on log vote)"),
    }


def metro_roster(code: str, year: str) -> set[str]:
    """Who stood in ONE metro, by IEC code. Names only, never votes.

    :func:`contesting_parties` is the same fact keyed on a `City`; this is keyed
    on the bare code, because the caller that needs it — the poll path's
    contested-area conversion — iterates :data:`METRO_CODES` and has no city
    objects to hand.

    **It exists to close a temporal leak.** That caller used to ask which metros
    a party got VOTES in at the target::

        _stood = [c for c in METRO_CODES
                  if metro_citywide(c, target.year).get(party, 0.0) > 0]

    which reads the result the backtest is predicting. Row existence is the
    nomination fact and reading it does not touch the outcome — the argument
    `levels.contestation` already runs on (MODEL-LOG §1.47).

    Measured before the change, so the correction is not mistaken for a result:
    the two definitions **agree for every party the poll path actually touches**.
    At 2021 they differ only for Al Jama-ah, which has a row in Ekurhuleni and
    no votes there — and Al Jama-ah has a baseline, so the path skips it. The
    48-seat gain in §1.65 is therefore not leakage; the leak was real and inert.
    """
    from ingest_lge import read_municipality

    path = metro_file(code, year)
    if path is None:
        return set()
    # Through the same reader `metro_citywide` uses, so the two answers are
    # like-for-like and the header drift between `_metros/` (`PartyName`) and
    # the clean files (`sPartyName`) is handled in one place. PR ballot, again
    # to match, and because that is the ballot a national poll speaks to.
    return {P.canonical(row["sPartyName"])
            for row in read_municipality(path, code, "PR")}


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


def _arrival_total_prior(before_year: str | int) -> float | None:
    """The typical COMBINED share of every party arriving in one city-year.

    Read off ``arrival_group_record`` for city-years strictly before the target,
    so it is a forecast input rather than hindsight. The median rather than the
    mean: the distribution runs 0.31%-4.74% over sixteen metro-years and the
    mean is pulled by Cape Town 2021, which is one observation.
    """
    rec = arrival_group_record(before_year=str(before_year))
    if not rec:
        return None
    import numpy as _np
    return float(_np.median([s for s, _ in rec]))


def arrival_rules(newcomers: set[str], lineage: dict[str, dict],
                  rates: np.ndarray, universe: list[str], categories,
                  record: list[tuple[float, float]],
                  splinter_fractions: list[float], pool_size: np.ndarray,
                  contestation: dict[str, float] | None = None,
                  splinter_home: dict[str, float] | None = None,
                  city_code: str | None = None,
                  pooled_splits: list[float] | None = None,
                  group_total: float | None = None,
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
    # A city with no splinter record of its own cannot size a splinter. The
    # fallback here used to be `(lo_e, mid_e, hi_e)` — three variables defined
    # LATER, per party, inside the loop below, so this raised UnboundLocalError
    # the moment it was reached. Johannesburg never reached it (COPE 2009 and
    # EFF 2014 are always on its record), and the first run on another metro
    # died here: Ekurhuleni has no NPE file before 2019, so no pair resolves.
    #
    # There is no honest number to put in its place. A splinter fraction is a
    # share OF THE PARENT and the arrival record is a share OF THE CITY, so
    # borrowing one for the other is a unit error, not a conservative default.
    # So a splinter with no record is sized as what it is without one — an
    # arrival — and the note says so.
    def band_for(party: str):
        """The splinter record that describes THIS party in THIS city.

        A split in its leader's own city is a different animal from the same
        split anywhere else — 0.611 against 0.103 for ActionSA, 0.885 against
        0.024 for MK — so it is sized from the home record when it is at home
        and the away record when it is not. Returns (lo, mid, hi, which).
        """
        at_home = (city_code is not None
                   and (SPLITS.get(party).home if party in SPLITS else None)
                   == city_code)
        home_pool = {q: f for q, f in (splinter_home or {}).items() if q != party}
        record = sorted(home_pool.values()) if at_home else splinter_fractions
        label = "home" if at_home else "away"
        # A HOME RECORD OF ONE IS NOT A RECORD. The home/away distinction is
        # real and large — see Split — but before 2021 exactly one home split
        # had happened anywhere, GOOD in Cape Town, and it flopped at 0.056.
        # Sizing ActionSA from it alone gave 1.87% against an actual 16.1% and
        # cost Johannesburg 18 seats of MAE, worse than the blended record it
        # replaced. So the split is applied only once there is something to
        # average, and until then the run says which record it fell back to.
        if at_home and len(record) < MIN_HOME_SPLITS:
            record = splinter_fractions
            label = (f"all splits — only {len(home_pool)} home "
                     f"observation(s) once {party} itself is excluded, too "
                     f"few to size from")
        elif at_home:
            label = (f"home-city splits ({', '.join(sorted(home_pool))}), "
                     f"RETROSPECTIVE: not all precede this target")
        if not record:
            return None, None, None, "none"
        return _band_from(record, label, pooled_splits)
    default_support = float(np.median(all_shares)) if all_shares else 0.0
    index = {p: i for i, p in enumerate(universe)}
    n_pools = len(categories)

    rules: dict[str, dict] = {}
    notes: dict[str, str] = {}
    entrant_sizes: dict[str, float] = {}
    for party in sorted(newcomers):
        declared = lineage.get(party, {})
        # Split or entrant is decided in exactly one place, and this is the
        # call to it. `lineage_why` carries the evidence into the run's notes
        # so a reader can see WHY a party was sized the way it was.
        parent, lineage_why = classify_arrival(party, declared.get("parent"))
        parent = parent or ""
        weights = declared.get("weights")
        reach = (contestation or {}).get(party)

        # ONE decision about which machinery sizes this party, used by the
        # branch AND by the band below. They used to be decided separately —
        # the branch on `parent and parent in index and f_mid is not None`,
        # the band on `parent` alone — so a declared split in a city with no
        # splinter record of its own took the entrant branch and then divided
        # None by None building its band. Tshwane, Ekurhuleni and eThekwini
        # all hit it the moment ActionSA got a parent.
        f_lo, f_mid, f_hi, f_kind = band_for(party)
        as_split = bool(parent and parent in index and f_mid is not None)

        if weights:
            vec = np.array([float(w) for w in weights], dtype=float)
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n_pools, 1.0 / n_pools)
            size = float(declared.get("support", default_support))
            capture = _capture_from_share(vec, size, pool_size)
            why = "pools and support declared in judgements/"
        elif as_split:
            # The parent's own rates ARE its pool weights. Capturing f of each
            # is what "inherits the parent's split" means, and the pool
            # renormalisation does the rest.
            # Keyed by pool INDEX, like `_capture_from_share`, because that is
            # what emit_pools consumes: `vec[int(g)] = r * registered[int(g)]`.
            # This branch keyed by pool NAME and therefore crashed with
            # `invalid literal for int() with base 10: 'Black African'` the
            # moment any party was routed to it. Which is why every lineage
            # file in the repository has `parent = ""`: declaring a parent —
            # the whole point of the file — took the model down, so nobody
            # ever did, so the splinter path was never exercised at all.
            # A SPLINTER IS NOT ITS PARENT. Taking f of the parent's rate in
            # every pool and nothing anywhere else says the leavers recruit only
            # among people the parent already had. Measured, that is wrong for
            # most splits: fitting each splinter's own vector at its first
            # election and regressing it on (parent, city average) over 22
            # metro-cases gives a median weight on the parent of 0.35 --
            # EFF 0.89, GOOD 0.28, ActionSA about 0.02, whose vector was very
            # nearly the CITY'S OWN composition.
            #
            # It is the failure that cost the 2021 forecast most. Pure
            # inheritance put ActionSA at 67.2% White when it measured 55.6%
            # Black African, so the debit for its 18% landed on the DA when it
            # should have landed on the ANC.
            #
            # The remainder goes to the city average, not to a named opponent:
            # the record says a splinter reaches beyond its parent, and does not
            # say whose voters it reaches instead.
            alpha = float(SPLINTER_PARENT_WEIGHT)
            size = np.asarray(pool_size, dtype=float)
            mix = size / size.sum() if size.sum() > 0 else np.full(n_pools, 1.0 / n_pools)
            parent_rate = np.array([rates[g, index[parent]] for g in range(n_pools)])
            # Scale the city half onto the parent's own footing so alpha is a
            # weight between two comparable things rather than between a rate
            # and a proportion.
            scale = float(parent_rate @ mix) / max(float(mix @ mix), 1e-12)
            blended = alpha * parent_rate + (1.0 - alpha) * scale * mix
            capture = {g: float(f_mid * blended[g])
                       for g in range(n_pools) if blended[g] > 0}
            why = (f"SPLIT from {parent} ({lineage_why}): takes {f_mid:.1%} of a "
                   f"vector that is {alpha:.0%} {parent}'s pool rates and "
                   f"{1 - alpha:.0%} the city's own composition — measured, "
                   f"median over 22 splinter-metro cases. Band {f_lo:.1%}-"
                   f"{f_hi:.1%} from the {f_kind} splinter record. Every party "
                   f"in those pools gives up the same proportion; none is named.")
        else:
            vec = np.full(n_pools, 1.0 / n_pools)
            reach_used = reach if reach is not None else 0.5
            # REACH CHOOSES THE COMPARATORS. IT DOES NOT CHOOSE THE PLACE.
            #
            # It used to do both: `place = clip(reach, 0.05, 0.95)` was passed
            # straight to `np.quantile`, so a party fielding candidates
            # everywhere was handed the 95th percentile of its band. On the
            # pre-2021 record that percentile is 11.10% and the 12 arrivals
            # that earned it are 8 EFF results plus 4 others; the median of
            # the same band is 0.28%. Every shell party that managed to file
            # nomination papers in every ward — and filing is cheap — was
            # therefore modelled as the EFF. Cape Town seeded 155% of its
            # electorate that way, eThekwini 136%.
            #
            # Contesting widely is a precondition for winning widely and not
            # evidence of it. So the central estimate is what a party like
            # this TYPICALLY manages, the band still reaches up to what the
            # best of them managed, and a party that is genuinely unlike its
            # comparators is raised by the judgement layer below — which is
            # where "this one is led by a former mayor" belongs, because
            # nothing in a result file says it.
            peers = comparators(reach)
            # THE MEAN, NOT THE MEDIAN, AND THE REASON IS WHAT CONSUMES IT.
            #
            # This was `np.median(peers)` until 2026-08-17 and it under-forecast
            # every arrival by a factor of four, which is half the missing
            # small-party seats on the whole nine-city-year record.
            #
            # Arrival sizes are violently right-skewed. Over the 77 arrivals on
            # record before 2021 the median is 0.0498% and the MEAN is 0.2378%,
            # a ratio of 4.78; among the wide-reach arrivals that actually win
            # seats it is 0.0798% against 0.3398%, a ratio of 4.26. Seeding at
            # the median is therefore seeding at a value four fifths of arrivals
            # exceed in expectation.
            #
            # The band below already carried the skew — a triangular running to
            # the 95th percentile, typically 17-24x the seed. It could not do
            # anything with it, because `pool_spec` balances both margins by IPF
            # (MODEL-LOG 'The centres now BIND') and IPF pins each party's MEAN
            # to its centre. So the right tail survives only as spread around a
            # centre that is four times too low: measured on eThekwini 2021,
            # Active Citizens drew p50 0.0083% and p95 0.3613% -- a 44x spread,
            # correctly shaped -- around a mean of 0.0798% against an actual
            # 0.81%. Widening the band cannot fix that and never could.
            #
            # Whatever goes in `centres` IS the expected value, so it must be
            # the expectation. That is the same correction this repository has
            # already made twice: flooring the Dirichlet MEAN rather than its
            # concentration, and reporting the coherent seat vector rather than
            # marginal medians. Third instance, same principle.
            size = float(np.mean(peers))
            lo_e = float(np.quantile(peers, ARRIVAL_BAND_LO))
            hi_e = float(np.quantile(peers, ARRIVAL_BAND_HI))
            # A judgement may say this one is unlike its comparators. Mashaba
            # had been mayor of this city and was widely liked; nothing
            # measurable said so, and doubling the default would have put
            # ActionSA at 18.4% against an actual 18.12%.
            size *= float(declared.get("overperform", 1.0))
            capture = _capture_from_share(vec, size, pool_size)
            mult = float(declared.get("overperform", 1.0))
            why = (f"entrant from nothing: even share of every pool. Sized at "
                   f"the EXPECTED result for the {len(peers)} arrivals that "
                   f"contested about as much of a city ({reach_used:.0%} of "
                   f"wards): mean {size:.2%}, median {np.median(peers):.2%}, "
                   f"band {lo_e:.2%}-{hi_e:.2%}"
                   + (f" after a x{mult:g} judgement" if mult != 1.0 else "")
                   + ". THE EVEN SPREAD IS A PLACEHOLDER: declare which pools "
                     "it pulls from and what support you expect.")
        centre = max(size, 1e-9) if not as_split else 1.0
        rules[party] = {"capture": capture,
                        "band": [f_lo / f_mid, 1.0, f_hi / f_mid] if as_split
                                else [lo_e / centre, 1.0, hi_e / centre]}
        if not as_split and not weights:
            entrant_sizes[party] = size
        notes[party] = why

    # THE GROUP TOTAL IS THE QUANTITY THAT BEHAVES; THE SPLIT IS WHAT REACH
    # PREDICTS. Hold the first, use the mean above only for the second.
    #
    # Seeding each entrant at the reach-matched MEAN is right per party and
    # wrong per city, because a city fields twenty to forty of them: 30 x 0.34%
    # is a 10.2% arrival total against a record whose median is 1.64% and whose
    # maximum over sixteen metro-years is 4.74%. Measured, that over-allocation
    # showed up exactly where it was put -- ranks 13+ went from -4.6pp to
    # +19.4pp and the seat error from 316 to 322, while ranks 4-12 did not move.
    # Seeding at the MEDIAN gets the total right by luck (30 x 0.08% = 1.6%) and
    # the split wrong, spreading the group evenly when reality concentrates it:
    # Cape Town 2021's arrivals totalled 4.74% with the Cape Coloured Congress
    # alone taking 2.83%.
    #
    # So take the mean for the RELATIVE weighting, where it carries the reach
    # signal (arrivals contesting 60-90% of wards clear 0.5% at 27.3% against
    # 7-8% in every other band), and rescale the group to the total the record
    # actually shows. Both numbers are measured, on transitions strictly before
    # the target, and neither is fitted to a backtest score.
    if entrant_sizes and group_total is not None:
        want = float(group_total)
        have = float(sum(entrant_sizes.values()))
        if have > 0 and want > 0:
            k = want / have
            for party in entrant_sizes:
                cap = rules[party]["capture"]
                rules[party]["capture"] = {g: r * k for g, r in cap.items()}
                notes[party] += (f" | group rescaled x{k:.2f}: {len(entrant_sizes)} "
                                 f"entrants summing to {have:.2%} against an "
                                 f"arrival-total record of {want:.2%}")
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




def lineage_path(city: cityconfig.City, target: cityconfig.Target) -> Path:
    return Path("judgements") / f"{city.slug}-{target.year}.toml"


def load_lineage(city: cityconfig.City, target: cityconfig.Target) -> dict[str, dict]:
    path = lineage_path(city, target)
    if not path.exists():
        return {}
    raw = tomllib.loads(path.read_text())
    return {k: v for k, v in (raw.get("party") or {}).items()}


def write_lineage_template(city: cityconfig.City, target: cityconfig.Target,
                           newcomers: dict[str, float],
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
               *, from_year: str | None = None,
               split_bloc: dict | None = None,
               retrospective_home: bool = False) -> dict:
    """Build the ``scenario["pools"]`` structure from measurement.

    A pool is a body of voters, and a party's membership of it is the measured
    share of its vote that comes from there — not a list of parties someone
    decided trade with each other.

    ``retrospective_home`` restores the old unfiltered home-splinter record.
    It answers "what is this rule worth once the record exists?", which is a
    real question and not a forecast; see :func:`home_splinter_record`.
    """
    # None means "no cutoff" — the retrospective mode. Otherwise the target's
    # own year, so a split that had not happened yet cannot size an arrival.
    home_cutoff = None if retrospective_home else target.year
    year = from_year or target.previous_lge or target.year
    fits, ctx = fit_city(city, year, cfg, split_bloc=split_bloc)
    cats = list(ctx["categories"])
    n = len(cats)

    # Size the pools as they will be at the TARGET, not as they were at the
    # election the rates were fitted on. The roll is counted every cycle and
    # the census is not, so the trend comes from the roll; `before` keeps a
    # backtest from seeing its own target's registration.
    series = registration_series(city, cfg, before=target.year,
                                 split_bloc=split_bloc)
    target_shares, roll_note = projected_pool_shares(series, target.year)

    # THE COMPOSITION IS NORMALISED ON VOTES CAST, NOT ON A PROJECTED ROLL.
    #
    # `PartyFit.composition(pool_votes)` says what it wants in its own signature
    # and docstring — "where the party's votes come from" — and the rates it
    # multiplies were fitted against `pool_votes = (comp * vote).sum(axis=0)`.
    # Until 2026-08-17 the production call handed it `target_shares`, a
    # projected REGISTRATION-share vector, while `montecarlo.pool_spec` sized
    # the same pools from the counted roll times turnout. Two denominators for
    # one quantity, and a category error against the function's own contract —
    # the arrival branch below already used the counted roll, so the two sat in
    # the same emitted dict.
    #
    # It made emitted compositions ARITHMETICALLY IMPOSSIBLE. Over nine
    # city-years, 5 of 339 party-pairs claimed a pool weight above
    # `poolshare / actual_share` — the ceiling of taking 100% of that pool.
    # Worst: Mangaung 2021, the ANC drawing a claimed 15.68% of its vote from an
    # Indian/Asian pool casting 1.54% of the ballots, 5.2x the arithmetic
    # maximum. Every violation was on the smallest pool. Re-normalised on votes
    # cast, 0 of 339 remain.
    #
    # Two things went wrong together. `projected_pool_shares` extrapolates the
    # last interval by `damping x step` = 0.6 x 2.5 = 1.5, so the "damping"
    # AMPLIFIES; Mangaung's Indian/Asian series is 2011: 0.0, 2014: 0.0, 2016:
    # 0.0524 — absent before 2016 — so it reads a spurious trend and lands on
    # 0.1311. And at Nelson Mandela Bay the same extrapolator sends that pool to
    # -0.0027, clipped to 1e-6, i.e. EXACTLY ZERO: every fitted party got no
    # weight at all in a pool holding 9,596 registered voters at 86.5% turnout.
    # That collapsed pool is the failure `pool_spec`'s own comment blames for
    # the per-draw capacity guard existing. THE DEFECT THE GUARD WAS BUILT FOR
    # WAS THIS ONE. See MODEL-LOG §1.42.
    registered = registered_at_target(city, target, cfg, year,
                                      split_bloc=split_bloc)
    record = turnout_record(city, cfg, before=target.year,
                            split_bloc=split_bloc)
    turnout = turnout_band(record, n)
    pool_votes_at_target = registered * np.array(
        [float(turnout[g][1]) for g in range(n)])
    composition = {p: f.composition(pool_votes_at_target)
                   for p, f in fits.items()}

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
    # THE ROSTER CUTS BOTH WAYS. It was only ever used to ADD parties — to find
    # a genuine entrant absent from the baseline — and never to remove one. So a
    # party that contested the last national election and is NOT on this
    # ballot kept a pool vector and drew votes anyway.
    #
    # Measured over the whole ballot, the model was putting 2.38% to 2.94% of a
    # city's vote on parties that were not standing (Johannesburg 2021: 16
    # parties, 2.52%; Tshwane: 20 parties, 2.38%; Cape Town: 19 parties, 2.94%).
    # Under largest remainder about 0.4% is a seat, so that is several seats
    # invented from nothing — and it is funded out of the parties ranked 4th to
    # 12th, which are exactly the ones that win marginal seats and which the
    # model under-predicts in 66 of 75 party-city-years.
    #
    # Dropping them from the composition is the whole fix: a pool's members are
    # renormalised when it is drawn, so the vote a non-contestant was holding
    # goes to the parties drawing on the SAME POOLS, which is where it should
    # have gone in the first place. Nothing is redistributed by hand.
    #
    # Only when the roster is real. A target that has not been held has no
    # nomination list, and the fallback roster above is the baseline itself, so
    # this would be a no-op there in any case.
    if roster_is_real:
        absent = sorted(p for p in composition
                        if p not in roster and p not in ("IND", "ENTRANT"))
        if absent:
            held = sum(baseline.get(p, 0.0) for p in absent)
            for party in absent:
                composition.pop(party, None)
            print(f"  not on the {target.year} ballot, dropped from the pools: "
                  f"{len(absent)} parties holding {held:.2%} of the "
                  f"{target.previous_npe} baseline between them "
                  f"({', '.join(absent[:6])}"
                  f"{', …' if len(absent) > 6 else ''})")

    no_vector = {p for p in roster
                 if p not in composition and p not in ("IND", "ENTRANT")}
    # A seed is only for a party with no level to start from.
    newcomers = {p for p in no_vector if baseline.get(p, 0.0) <= 0.0}
    lineage = load_lineage(city, target)
    inherited: dict[str, str] = {}
    for party in sorted(no_vector):
        rule = lineage.get(party, {})
        weights = rule.get("weights")
        # THROUGH classify_arrival, not off the raw field. Every `parent` in
        # every judgements/*.toml is "" -- the file exists to be filled in and
        # nobody has -- so reading it directly meant this loop called ActionSA
        # an entrant and gave it an even share of every pool, while
        # `arrival_rules` (which DOES go through classify_arrival) called it a
        # split from the DA and blended its vector. The emitted vector came from
        # the second, so the draw was right; but the run reported both, and one
        # of the two provenance strings was false. A reader who finds one
        # advertised constant that does not do what it says stops trusting the
        # measured ones, which is this repository's own stated standard.
        parent, _why = classify_arrival(party, rule.get("parent"))
        parent = (parent or "").strip().upper()
        if weights:
            vec = np.array([float(w) for w in weights], dtype=float)
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n, 1.0 / n)
            inherited[party] = "judged weights"
        elif parent and parent in composition:
            # A SPLINTER IS NOT ITS PARENT. Leaving a party to start one means
            # competing for people the parent never had, and the record says so
            # loudly. Fitting each splinter's own vector at its first election
            # and regressing it on (parent, city average) gives the weight the
            # parent actually deserves:
            #
            #   EFF from the ANC    alpha 0.75-1.08, median 0.89   cos to parent 0.998-1.000
            #   GOOD from the DA    alpha -0.02-0.58, median 0.28
            #   ActionSA from DA    alpha -1.07-0.56, median ~0.02  cos to CITY 0.69-0.999
            #
            # 22 cases across eight metros; median alpha 0.35. So the EFF stayed
            # inside the ANC's constituency and pure inheritance was right for
            # it, while ActionSA's vector was very nearly the CITY'S OWN
            # composition — a broad-appeal municipal party, not a faction. Pure
            # inheritance (alpha 1.0) was wrong for two of the three, and wrong
            # in the direction that cost the 2021 forecast most: it put ActionSA
            # at 67.2% White when it measured 55.6% Black African, so the debit
            # for its 18% fell on the DA when it should have fallen on the ANC.
            #
            # The remainder goes to the CITY AVERAGE rather than to any named
            # opponent. That is the weaker and more honest claim: the record says
            # a splinter reaches beyond its parent, and does not say whose voters
            # it reaches instead.
            alpha = float(SPLINTER_PARENT_WEIGHT)
            # The city's own pool composition AT THE FITTING YEAR, which is the
            # basis the vectors themselves are fitted on, so the two halves of
            # the blend are on the same footing.
            _pv = np.asarray(ctx.get("pool_votes"), dtype=float) \
                if ctx.get("pool_votes") is not None else None
            city_mix = (_pv / _pv.sum()) if _pv is not None and _pv.sum() > 0 \
                else np.full(n, 1.0 / n)
            vec = alpha * composition[parent] + (1.0 - alpha) * city_mix
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n, 1.0 / n)
            inherited[party] = (f"splinter of {parent}, {alpha:.0%} its vector "
                                f"and {1 - alpha:.0%} the city average")
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
        splinter_record(city, target.year), registered, contestation=reach,
        splinter_home=home_splinter_record(before_year=home_cutoff),
        city_code=city.code,
        pooled_splits=pooled_splinter_record(target.year),
        # The arrival TOTAL, from city-years strictly before the target. It is
        # the regular quantity (median 1.64%, 0.31%-4.74% over sixteen
        # metro-years) where an individual arrival's size is not.
        group_total=_arrival_total_prior(target.year))
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
        list(ctx["categories"]))

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
    # A spec carrying a vote-located bloc says so IN THE SPEC, not only in the
    # filename it happened to be written to. Anything downstream that loads a
    # dict can then refuse it, or label it, without having to know where it
    # came from — and a spec that quietly reached the published forecast would
    # still be identifiable after the fact.
    marker = {}
    # The home-city splinter record ignores the target cutoff by design, so the
    # spec records WHICH splits it used and WHEN they happened. run_model turns
    # that into a note_constant, and backtest's banner reports any target that
    # is at or before one of them as in-sample. A retrospective input that does
    # not announce itself is the exact defect this repository spent the day
    # removing; this one announces itself through the machinery built for it.
    home_used = home_splinter_record(before_year=home_cutoff)
    if home_used:
        marker["splinter_home"] = {
            "fractions": {k: round(v, 4) for k, v in home_used.items()},
            "measured_at": sorted(SPLITS[k].measured_from[1] for k in home_used),
        }
    if split_bloc:
        marker["simulation_only"] = (
            f"Carries the {split_bloc.get('name')} pool, located by the "
            f"{split_bloc.get('indicator')}'s own ward geography rather than "
            f"by the census. Its LOCATION is measured; its SIZE rests on "
            f"within_rate={split_bloc.get('within_rate')}, a judgement. For "
            f"the reader simulation only — the published forecast reads "
            f"pools_{target.year}.json.")
    return {"pools": out, "fitted_on": year, "target": target.year,
            # What this spec was built FROM, so a run can tell whether the code
            # has moved under it. `provenance` below is the prose account for a
            # reader; this is the machine-checkable one. See `artefact_key`.
            "artefact_key": artefact_key(city, target),
            **marker,
            "turnout_limits": limits,
            "seeds": {p: v for p, v in seeds.items() if abs(v) > 1e-9},
            "seed_bands": {p: list(v) for p, v in seed_bands.items()},
            "seed_notes": seed_notes,
            "entrant_record": [[float(share), float(reach)] for share, reach in record],
            # Arrivals as a GROUP, drawn once and split by ward reach, rather
            # than thirty independent seeds and one generic slot. None where
            # there is no nomination list to split between.
            "arrival_group": arrival_group_spec(
                target.year, reach, sorted(arrivals)) if roster_is_real else None,
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
    # ⚠️ THIS TYPED DEFAULT IS A KNOWN DEFECT AND IS QUEUED, NOT KEPT.
    # `["ANC","DA","EFF"]` silently duplicates `config/dimensions.toml`'s own
    # `gate_parties` and would take over unnoticed if that block were renamed.
    # The fix — raise on absence — was WRITTEN AND REVERTED on 2026-08-31,
    # because it is executable code in `pools.py` and therefore moves the
    # artefact key, invalidating all eighteen emitted specs. It went in as
    # `POOLS-REEMIT-QUEUE.md` entry 6 instead. The guard caught the violation
    # immediately (`pools_2021.json is STALE ... dbdf171344ffd5f0 ->
    # e44c09169ba266ca`), which is the artefact key doing exactly its job.
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
    # The reader simulation may carry structure the published forecast does
    # not. The IFP-located bloc is the first such case: its LOCATION is well
    # evidenced (the IFP's ward geography is stable at +0.985 across 2016-2021
    # and predicts MK's 2024 arrival at +0.65 with African share removed) and
    # its SIZE rests on a judgement, `vote_located_bloc`'s `within_rate` —
    # which the fit itself flags, reporting the bloc's registration at 112% of
    # the level above it. Good enough to let a reader explore; not good enough
    # to publish a seat count from.
    #
    # So it emits to a DIFFERENT FILE. Not a flag inside the same spec, not a
    # config default someone can flip by accident: the published path reads
    # pools_{year}.json and this writes pools_{year}_simulation.json, so the
    # forecast cannot pick it up however the two are invoked. An
    # un-namespaced write has reached a live forecast in this repository
    # before, and the fix then was the same one — separate the paths, do not
    # rely on remembering.
    ap.add_argument("--retrospective-home", action="store_true",
                    help="use the UNFILTERED home-splinter record, ignoring the "
                         "target cutoff. Answers 'what is this rule worth once "
                         "the record exists?' and is NOT a forecast: at target "
                         "2021 it lets MK's 2024 eThekwini split size ActionSA, "
                         "which is worth 37 seats of error and 57%% of the "
                         "margin over uniform swing. See pools.home_splinter_record")
    ap.add_argument("--simulation", action="store_true",
                    help="emit the reader-simulation spec, which carries the "
                         "vote-located bloc, to pools_{target}_simulation.json. "
                         "NEVER read by the published forecast.")
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
        bloc = SIMULATION_BLOC if args.simulation else None
        with artefact_lock("emit", f"{city.slug} {target.year}"):
            spec = emit_pools(city, target, cfg, from_year=args.from_year,
                              retrospective_home=args.retrospective_home,
                              split_bloc=bloc)
            suffix = "_simulation" if args.simulation else ""
            out = city.processed / f"pools_{target.year}{suffix}.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(spec, indent=2, sort_keys=True))
        print(f"{city.name} {target.year}: {len(spec['pools'])} pools -> {out}")
        if bloc:
            print(f"  SIMULATION SPEC — not the published forecast. "
                  f"{spec['simulation_only']}")
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
