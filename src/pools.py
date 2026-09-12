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
import functools
import io
import hashlib
import json
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
    # ⚠️ These two are the SECOND copy of `extrapolation_damping` /
    # `extrapolation_max_years`. `load_config` always passes both explicitly
    # and refuses if the TOML omits them, so these defaults are unreachable
    # from the emit path — kept only so a hand-built `Config` in a test is
    # constructible, and marked so nobody reads them as the shipped values.
    damping: float = 0.6           # unreachable; see load_config
    max_extrapolation: float = 8.0  # unreachable; see load_config

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


def artefact_key(city, target, config_path: Path | None = None) -> dict:
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
    # ⛔ RESOLVED HERE, NOT IN THE SIGNATURE. A `Path` frozen as a default is
    # evaluated once at import, so rebinding `pools.CONFIG` moved nothing — in
    # the parent or in a worker. That is the `LEVEL_DF` class (§1.33): a
    # constant that reads as configurable and is not. Three signatures carried
    # it; all three now resolve at call time.
    config_path = CONFIG if config_path is None else config_path
    return {
        "schema": 2,
        "city": getattr(city, "slug", str(city)),
        "target": getattr(target, "year", str(target)),
        "pools_sha": _code_sha(Path(__file__)),
        "config_sha": _config_sha(config_path),
        "cities_sha": _cities_sha(),
        "deps_sha": _deps_sha(),
        "judgements_sha": _judgements_sha(city, target),
        "gates_sha": _gates_sha(),
    }


def _gates_sha() -> str:
    """The RESOLVED state of the environment gates that change what is read.

    ⛔ A HOLE THE CODE HASH CANNOT SEE. `_deps_sha` names `levels` as a
    dependency precisely because it carries `HELD_BACK`, "which decides whether
    a fitting election may be read at all" — but `HELD_BACK` is emptied by an
    ENVIRONMENT VARIABLE and `_code_sha` hashes the syntax tree. Measured
    2026-09-05: `HELD_BACK_OFF=1` takes `HELD_BACK` from 14 entries to 0 and
    leaves `deps_sha` byte-identical at `53cedeb94115dd98`.

    `levels.py`'s own comment invites the run that does it — *"`HELD_BACK_OFF=1`
    lifts the gate for one run, so the diagnosis this entry is about can be
    MEASURED"* — so a spec emitted during such a run would report itself current
    for ever after. That is exactly the silent staleness this key exists to
    close, arriving through the one door it did not watch.

    Recorded rather than refused: a diagnostic emit is legitimate, and what
    matters is that the artefact says it was one.
    """
    import levels as _levels
    state = {
        "HELD_BACK_OFF": os.environ.get("HELD_BACK_OFF") == "1",
        "HELD_BACK_n": len(getattr(_levels, "HELD_BACK", ()) or ()),
        "THETA_WINDOW": os.environ.get("THETA_WINDOW", ""),
    }
    return hashlib.sha256(
        json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]


# The first-party modules `emit_pools` actually reads at emit time, whose CODE
# decides emitted numbers. `pools_sha` hashes ONE file and `_code_sha`'s
# docstring claims "any change to what the code computes moves it" — true of
# this file and false of the five below it leans on.
#
#   parties     `P.canonical` — every party name in every file
#   cityconfig  `CALENDAR` dates AND `results` templates; a `results` of None is
#               what empties the 2026 roster
#   ingest_lge  `read_municipality`, the cleaner whose known failure was a
#               silent 68% vote loss
#   levels      `HELD_BACK`, which decides whether a fitting election may be
#               read at all
#
# ⛔ `montecarlo` IS DELIBERATELY EXCLUDED, and the reason is cry-wolf, not
# irrelevance: `read_ward_crosswalk` is a genuine emit-path dependency, but the
# module also carries every forecast lever and changes on most working days.
# Hashing it would mark all 26 specs stale continuously, and a staleness warning
# that fires daily is one nobody reads — the failure `_code_sha` was shaped to
# avoid. The residual risk is named here rather than hidden: a change to
# `read_ward_crosswalk` alone will NOT mark a spec stale.
_EMIT_DEPENDENCIES = ("parties", "cityconfig", "ingest_lge", "levels")


def _deps_sha() -> str:
    """The code of the first-party modules the emit leans on, hashed together."""
    here = Path(__file__).parent
    parts = [f"{name}:{_code_sha(here / f'{name}.py')}"
             for name in _EMIT_DEPENDENCIES]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _cities_sha() -> str:
    """Every `cities/*.toml`, because they are a PANEL input, not a city one.

    ⛔ THE SAME POPULATION BUG AS `config_sha`, ONE DIRECTORY OVER — and it was
    introduced by the turnout-band work that fixed the first one.
    `panel_turnout_spread` globs `cityconfig.CITIES_DIR` to measure how far each
    pool's turnout moves across the whole panel, so **adding a ninth city
    changes the turnout band of all twenty-six existing specs**, in every city,
    including the live 2026 forecast. Nothing marked them stale.

    `MACHINERY.md` called this omission "per-city structure and judgements",
    which understates it: for the band it is a panel input, and the expansion
    roadmap is about to add cities.
    """
    parts = [f"{f.name}:{_sha(f)}"
             for f in sorted(cityconfig.CITIES_DIR.glob("*.toml"))]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


# The key fields that say WHICH artefact this is, rather than what it was built
# from. Compared by name with a better message than the value scan gives, so
# they are excluded from it. Exported because `test_chain` needs the same set
# and a set typed in two places is the defect `stale_reason` was just fixed for.
_IDENTITY_FIELDS = frozenset({"city", "target"})


def _config_sha(config_path: Path) -> str:
    """Every `config/*.toml`, not the one file this used to name.

    ⛔ A POPULATION BUG, NOT A MISSING FILE. The key's claim is *what this spec
    was built FROM*; the population scanned was a single named path. `config/`
    held exactly one file when that was written, so the claim and the scan
    coincided by accident — and the day a second config file appeared its
    content would have been invisible: editable, consumed, and reported current
    by every spec. CLAUDE.md's rule for a scan-shaped claim applies directly —
    state the population the claim covers, and assert it equals what is
    scanned.

    Name AND content, sorted, so adding, removing or renaming a file moves the
    key as surely as editing one does.
    """
    root = Path(config_path).parent
    parts = []
    for f in sorted(root.glob("*.toml")):
        parts.append(f"{f.name}:{_sha(f)}")
    if not parts:                      # the named file is all there is
        return _sha(config_path)
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:16]


def _judgements_sha(city, target) -> str:
    """This city-year's judgement file, hashed as PARSED PAYLOAD not bytes.

    ⛔ IT WAS IN NO HASH AT ALL, AND IT SETS SEEDS. `judgements/<slug>-<year>.toml`
    declares each party's `parent`, `support` and pool `weights`, which
    `classify_arrival` and `emit_pools` read directly. So a hand edit to it
    changed what the model computes and **every emitted spec went on reporting
    itself current** — the silent-staleness hole this whole mechanism exists to
    close, sitting in the one input a human is most likely to edit.

    ⚠️ **THE SEAM THAT WOULD USE THIS DOES NOT EXIST YET.** Queue entry 3 is
    meant to make a published nomination list *a config edit rather than a code
    change*, and it is not built. Today `CALENDAR["2026"].results` is `None`, so
    `contesting_parties` returns an empty set, `roster_is_real` is False, and
    `newcomers` — which derives from `roster` — never iterates a party declared
    in this file. The emitted 2026 spec carries `seeds {}` and
    `arrival_group: null`, and the message `emit_pools` prints pointing a reader
    at this file is, for a genuinely new party, **currently inert**.

    So this hash is here BEFORE its consumer, deliberately: the alternative is
    to build the seam and then remember to key it. Stated as pending rather than
    as done, because a document that looks current and is not is worse than one
    that is missing.

    **PARSED, NOT BYTES**, following `theta_residual`'s memo key, which freezes
    the table rather than the switch. A byte hash would mark all 26 specs stale
    on every comment edit, and a staleness warning that fires on prose is one
    everybody learns to ignore — which is the failure `_code_sha`'s own
    docstring was written to prevent.
    """
    try:
        path = lineage_path(city, target)
    except Exception:
        return "unkeyed"
    if not path.exists():
        return "absent"
    try:
        payload = tomllib.loads(path.read_text())
    except Exception:
        return "unparsable"
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


def stale_reason(spec: dict, city, target,
                 config_path: Path | None = None) -> str | None:
    """Why this spec should not be trusted for this run, or None.

    Returns a sentence, not a boolean, because the caller prints it and the
    useful part is *which* thing moved.
    """
    key = spec.get("artefact_key")
    if not key:
        return ("emitted before artefact keys existed, so nothing can say "
                "whether it matches the current pools.py — re-emit to check")
    # Resolved here too: this function NAMES the file in its message, and an
    # unresolved None would print "None changed since this spec was emitted".
    config_path = CONFIG if config_path is None else config_path
    now = artefact_key(city, target, config_path)
    if key.get("city") != now["city"] or key.get("target") != now["target"]:
        return (f"built for {key.get('city')} {key.get('target')}, "
                f"not {now['city']} {now['target']}")
    # ⛔ DERIVED FROM THE KEY, NOT TYPED HERE. This used to compare a literal
    # tuple and then index a literal dict, so a field added to `artefact_key`
    # and not to BOTH of these was recorded and never checked — and a field
    # added to only one of them raised `KeyError` on a real spec. A number
    # typed in two places; one goes stale. The identity fields are excluded by
    # name because they are compared above with a better message.
    # ⛔ BOTH DIRECTIONS, AND `schema` IS COMPARED.
    #
    # Iterating `now` alone is the code->key direction only: a field present in
    # a STORED key and no longer produced by `artefact_key` was invisible, which
    # is the register->code blindness CLAUDE.md names as this project's worst
    # class. And `schema` sat in `identity`, so a bump that only REMOVED a field
    # passed silently. Comparing the field SETS closes both at once.
    absent = sorted(set(key) ^ set(now))
    if absent:
        return (f"this spec's key records {sorted(set(key) - set(now)) or 'nothing'} "
                f"that the code no longer produces, and the code produces "
                f"{sorted(set(now) - set(key)) or 'nothing'} that it does not "
                f"record — the key's shape has changed (schema "
                f"{key.get('schema')} -> {now['schema']}); re-emit before "
                f"believing any measurement taken against it")
    moved = [name for name in sorted(now) if name not in _IDENTITY_FIELDS
             and key.get(name) != now[name]]
    if moved:
        labels = {"schema": "the artefact key's own shape",
                  "pools_sha": "src/pools.py",
                  "config_sha": f"{Path(config_path).parent}/*.toml",
                  "cities_sha": f"{cityconfig.CITIES_DIR}/*.toml",
                  "deps_sha": "src/{" + ",".join(_EMIT_DEPENDENCIES) + "}.py",
                  "judgements_sha": str(lineage_path(city, target))}
        which = " and ".join(labels.get(m, m) for m in moved)
        return (f"{which} changed since this spec was emitted "
                f"({', '.join(f'{m} {key.get(m)} -> {now[m]}' for m in moved)}); "
                f"re-emit before believing any measurement taken against it")
    return None


def load_config(path: Path | None = None) -> Config:
    # Resolved at call time, not frozen in the signature — see `artefact_key`.
    path = CONFIG if path is None else path
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
        # ⛔ NO TYPED FALLBACK, for the reason `_required_gate` gives: a
        # default here duplicates `config/dimensions.toml` in code and takes
        # over in SILENCE if the key is renamed. These two are the members of
        # that class that MOVE NUMBERS — `damping` is applied in the covariate
        # extrapolation and `max_extrapolation` gates it — where `gate_parties`
        # and `min_oos_gain` cannot, being reachable only from `--gate`.
        # Declaring the population as "two, by grep for `cfg.<section>.get(`"
        # named a SPELLING and missed these, which are `raw.get(` one level up
        # and duplicated a second time as dataclass defaults below.
        damping=_required_setting(raw, "extrapolation_damping"),
        max_extrapolation=_required_setting(raw, "extrapolation_max_years"),
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
        # ⛔ THE WORKBOOK CARRIES A 'Total' ROW AND IT IS NOT A WARD. Harmless
        # under a code join, which simply never asks for it; ruinous in any
        # denominator taken over the dict, where it double-counts the whole
        # country. Exactly one non-8-digit key exists in all three workbooks.
        if code in _CENSUS_TOTAL_ROW or not (code.isdigit() and len(code) == 8):
            continue
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
        # ⛔ THE WORKBOOK CARRIES A 'Total' ROW AND IT IS NOT A WARD. Harmless
        # under a code join, which simply never asks for it; ruinous in any
        # denominator taken over the dict, where it double-counts the whole
        # country. Exactly one non-8-digit key exists in all three workbooks.
        if code in _CENSUS_TOTAL_ROW or not (code.isdigit() and len(code) == 8):
            continue
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
    # Rates that landed on a bound rather than being estimated. A pool listed
    # here has no identifying variation in this city's ward table at that
    # level, and its rate is a clipped corner, not a measurement (§1.164).
    unidentified: list[str] = field(default_factory=list)

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


def _at_bound(rate: np.ndarray, upper: float = 1.0) -> np.ndarray:
    """Which fitted rates are sitting on a bound, i.e. are not estimates."""
    return (rate <= _RATE_BOUND_EPS) | (rate >= upper - _RATE_BOUND_EPS)


# ⚖️ The most a REGISTRATION rate may reach before it is treated as a runaway.
# NOT an estimate — a guard. JUDGEMENT-CALLS §L9,
# prereg/2026-09-05-registration-rate-bound.md.
#
# Registered voters are COUNTED; census voting-age population is MODELLED, so
# their ratio is not a rate bounded by 1. The model computes it separately as
# `census_correction` — 1.206 Indian/Asian and 1.480 White at Johannesburg 2021
# — and the old single bound of 1.0 clipped that very quantity.
#
# ⛔ THE VALUE 2.0 IS UNDEFENDED. The table that used to justify it here was
# measured with the bound lifted on ALL THREE levels, which inflates
# `adult_share` and deflates this rate. Re-derived on the shipped instrument:
#
#     Johannesburg White        1.27 / 1.38 / 1.71 / 1.74
#     Cape Town Indian/Asian    1.90 / 2.13 / 2.26 / 1.93   <- TWO above 2.0
#     Mangaung Indian/Asian        —  /    — / 4.34 / 3.27
#
# So this binds on FOUR cells in TWO cities, not on Mangaung alone — and the
# retracted comment cited Cape Town as proof it binds on nothing. See
# JUDGEMENT-CALLS §L9, which carries the correction and the deferral.
#
# ⚠️ Do NOT cite DATA-QUALITY item 11 for this. Item 11 says the census
# over-statement "does not explain this gap; it WIDENS it" — an over-stated
# denominator makes the ratio smaller. The support for rates above 1 is item 13
# and the `registration_series` docstring.
#
# The per-level split ships because bounding a quantity the model separately
# computes as 1.48 is wrong on its face. The VALUE is deferred, not defended.
REGISTRATION_MAX = 2.0


def _nest(parent: np.ndarray, observed: np.ndarray,
          upper: float = 1.0) -> tuple[np.ndarray, np.ndarray]:
    """Split an observed ward total across pools, in proportion to the parent.

    One rate per pool is fitted across wards (``observed_w ~ sum_g parent_wg
    r_g``), applied, then each ward is scaled so its pools sum to what was
    actually observed there. The rate carries the between-ward information; the
    scaling makes every ward agree with the published count.
    """
    rate = _nnls(parent, observed, upper=upper)
    child = parent * rate[None, :]
    row = child.sum(axis=1)
    scale = np.divide(observed, row, out=np.ones_like(row), where=row > 0)
    return child * scale[:, None], rate


def _nnls(A: np.ndarray, b: np.ndarray, iters: int = 40000,
          upper: float = 1.0) -> np.ndarray:
    """Fit one non-negative rate per pool, BOUNDED ABOVE BY A PROPORTION.

    ⛔ THE UPPER BOUND WAS MISSING AND IT MANUFACTURED EVERY DEGENERATE CELL IN
    THE PANEL (§1.164). Each fitted quantity here — ``adult_share``,
    ``registration``, ``turnout`` — is a PROPORTION of the level above it, so a
    value above 1.0 is not a rate at all. Unbounded, this returned
    ``adult_share`` of **1.3037** at Buffalo City and **2.0573** at Mangaung:
    more adults than people.

    The damage was not the impossible number itself but what it did downstream.
    A pool whose rate runs away takes the OTHER pools' rates down with it to
    keep the ward totals right, and a small pool driven to ``0.0000`` loses its
    whole column from the matrix the composition is then fitted on. Measured at
    Buffalo City 2006, the design matrix's condition number is **18.8 at
    `registered` and 486.9 at `voted`** — a twenty-four-fold degradation created
    entirely here, in the turnout solve, and not present in the census.

    ⚠️ **A BOUND TURNS A RUNAWAY INTO A CORNER, WHICH IS BETTER AND STILL NOT AN
    ESTIMATE.** A rate sitting exactly on 0.0 or on ``upper`` means the ward
    table could not identify that pool, and the caller must SAY SO rather than
    quietly using the clipped value — see :func:`_nest`, which reports it, and
    the ``unidentified`` list on :class:`PoolCounts`. Clipping silently would
    replace a visibly absurd number with an invisibly wrong one, which is
    worse.
    """
    x = np.full(A.shape[1], b.sum() / max(A.sum(), 1e-9))
    x = np.clip(x, 0.0, upper)
    lipschitz = float(np.linalg.norm(A, 2) ** 2)
    if lipschitz <= 0:
        return x
    for _ in range(iters):
        x = np.clip(x - (A.T @ (A @ x - b)) / lipschitz, 0.0, upper)
    return x


# How close to a bound a fitted rate must sit before it is reported as
# unidentified rather than estimated. Not a tuning knob: it exists because
# floating-point iteration lands near a bound rather than exactly on it.
_RATE_BOUND_EPS = 1e-6

# The preceding-NATIONAL share below which a party with no preceding LOCAL
# record is not assumed onto an unheld ballot. Owner's decision 2026-09-03,
# evidence in MODEL-LOG §1.175 and JUDGEMENT-CALLS §K1. Applies ONLY where no
# roster has been published — a held election has a real one and never uses it.
NATIONAL_ONLY_FLOOR = 0.001

# The preceding-LOCAL share below which a party with no preceding NATIONAL vote
# is not assumed onto an unheld ballot. Same value and same reasoning as
# NATIONAL_ONLY_FLOOR, and a better bargain: it drops 59% of that class for
# 0.038pp of vote and NO seats. JUDGEMENT-CALLS §K2, MODEL-LOG §1.176.
PRIOR_LOCAL_FLOOR = 0.001

# The panel-measured turnout band needs a floor on evidence and a stated
# fallback when it does not have it. Neither is tuned: 12 observations is three
# cities' worth of one transition, below which the quantile is noise, and the
# fallback is the value the old code used so that a thin-evidence case is no
# worse than before rather than differently wrong.
_PANEL_SPREAD_MIN_OBS = 12
# Below this many observations of its OWN, a pool cannot estimate its own
# spread and falls back to the panel's. At a 2011 target each pool has one.
_OWN_EVIDENCE_MIN_OBS = 4
# Winsorisation drops the single most extreme observation, so it needs a sample
# that survives losing one. Applied below this, it re-creates the defect it
# exists to fix -- measured, 2011 coverage 5 of 8 -> 1 of 8.
_WINSORISE_MIN_OBS = 6
_PANEL_SPREAD_FALLBACK = 0.30


def ward_totals(city: cityconfig.City, year: str,
                ballot: str = "PR") -> tuple[dict[str, float], dict[str, float]]:
    """Ward -> registered voters, and ward -> votes cast. Both published."""
    template = cityconfig.CALENDAR[year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        raise SystemExit(f"no result file for {city.slug} {year}: {path}")
    # ⛔ THE QUARANTINE IS HONOURED HERE TOO, AND THIS IS THE THIRD READER.
    #
    # `levels.HELD_BACK` withholds the pre-2011 history pending a diagnosis.
    # `levels._citywide` honoured it, `pools._npe_citywide_for` was taught to,
    # and THIS path — `ward_totals`, reached through `pool_counts` and
    # `registration_series` — was not. Measured 2026-09-01: `_citywide` refused
    # Cape Town's `lge2000` while `pool_counts` read 1,269,582 registered voters
    # out of the same file, and it reached the emitted spec — Cape Town's 2016
    # registration series carried 2000/2006/2009/2011/2014 where Johannesburg's
    # carried 2011/2014, and its White pool's turnout ceiling moved 0.7484 to
    # 0.8578. No other metro, because no other metro's 2000 wards join the
    # census — so the leak was CITY-SHAPED AND ARBITRARY.
    #
    # That is worse than the numbers: a quarantine that leaks through one of
    # three readers means the effect being diagnosed is not the effect being
    # measured, and the panel figure adjudicated against it was not measuring
    # what it claimed. **Three readers of one file is the defect this project is
    # named for; the gate is imported, never copied.**
    import levels as _levels
    if _levels._held_back(path):
        raise SystemExit(
            f"{city.slug} {year}: this election is in `levels.HELD_BACK` and "
            f"may not be read. See that dict for the diagnosis it waits on.")
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

    # ⛔ THE COUNT HALF OF THE CENSUS JOIN, TRIGGERED ON DELIMITATION.
    #
    # `composition_at` above already moves the SHARE onto this election's wards
    # whenever the census was published on a different delimitation. These two
    # reads did not, so `people = composition x population` mixed TWO POLYGON
    # SETS: median per-ward disagreement 6.8%-24.4% at a 2011 fitting year and
    # up to 10% at 2016. Every one of the sixteen city-years carried it.
    #
    # ⚠️ THE TRIGGER IS THE DELIMITATION, NOT AN EMPTY OVERLAP, AND THE
    # DIFFERENCE IS NOT COSMETIC. The first version asked `if not (codes &
    # set(people_by_ward))` — which is the trap `composition_at`'s own comment
    # warns about, because ward codes are REUSED and a wrong join therefore
    # SUCCEEDS. Cape Town's municipal code never changed (191...), so its 2006
    # wards "joined" Census 2022 and the branch never fired: it was fitted on
    # 2000, 2006, 2011 and 2016 turnout where every other metro had 2011 and
    # 2016, on a join with a median per-ward error of 14.7%. Nobody saw it
    # because `turnout_record` swallows the refusal.
    src_delim = base.censuses[-1].delimitation

    # ⛔ THE AGE DIMENSION IS GATED ON ITS OWN DELIMITATION, NOT ON THE BASE'S.
    #
    # This block used to sit INSIDE the `base` gate below while using
    # `age.censuses[-1].delimitation` for its own reprojection — so the gate and
    # the operation read two different dimensions. The silent direction is the
    # one that matters: base matches the election delimitation and age does not.
    # The block never runs, `adults_by_ward` stays on its own polygon set, and
    # it is then joined to this election's wards by ward code — **which
    # SUCCEEDS, because ward codes are reused**, the exact trap the comment
    # below warns about one level up.
    #
    # ⚠️ AND THE ADULTS JOIN HAS NO KEY-SET ASSERTION, so the failure is silent
    # in a second way. `people_by_ward` gets `matched = codes & set(...)` and a
    # 50% refusal further down; `adults_by_ward` is read with `.get(w, 0.0)`, so
    # an unmatched ward reads as **zero adults** and `_nest` fits `adult_share`
    # toward the floor rather than raising. Recorded, not fixed here: a new
    # refusal on an unreachable path is a guard nothing can exercise.
    #
    # ⚠️ UNREACHABLE TODAY AND NOT TOMORROW. Every live dimension in
    # `config/dimensions.toml` is Census 2022 on delimitation 2021, so the two
    # gates always agree and this branch is number-neutral — which the emit must
    # CONFIRM by diff, not assume. Each dimension carries its own
    # `[[dimension.census]]` list, and the commented-out base 2011 entry is the
    # highest-value outstanding data request after home language. The moment one
    # dimension gains a census the other does not, this is live, which is why it
    # lands BEFORE that data arrives rather than after. Ultra review #1,
    # POOLS-REEMIT-QUEUE entry 15, §1.195.
    if adults_by_ward:
        age_delim = age.censuses[-1].delimitation
        if int(age_delim) != delimitation_for(year):
            adults_by_ward, _ = reproject_counts(
                adults_by_ward, city, str(age_delim), year)

    if int(src_delim) != delimitation_for(year):
        people_by_ward, cov = reproject_counts(
            people_by_ward, city, str(src_delim), year)
        # ⛔ GATED ON WHAT THE MISSINGNESS DOES, NOT ON HOW MUCH OF IT THERE IS.
        #
        # A coverage floor is a proxy for the quantity that matters — how far
        # the citywide composition moves because of what failed to map — with an
        # unknown transfer function. Measured, the function is weak: randomly
        # ablating Johannesburg's wards from 95% to 60% coverage moves the
        # largest pool share by only 0.021 to 0.028.
        #
        # And coverage is PESSIMISTIC here, because it counts population lost at
        # the voting-district level while whole wards are rarely lost at all:
        # Tshwane reports 72.6% coverage but loses **7 wards of 107**, and those
        # seven are demographically almost identical to the ones kept (largest
        # pool-share difference 0.013). Mangaung loses **one ward of 51** at
        # 0.043. A raw floor of 0.80 blocked both metros from ever becoming
        # backtest targets on the strength of a number that was not measuring
        # the harm.
        #
        # So the refusal is on the demographic SHIFT the loss induces. Coverage
        # is still computed and reported, because a very low one means something
        # structural even when the mix happens to match.
        drift = _reprojection_drift(city, str(src_delim), year, cfg)
        if drift is not None and drift > CENSUS_DRIFT_CEILING:
            raise SystemExit(
                f"{city.slug} {year}: the wards that fail to reproject from the "
                f"{src_delim} delimitation are demographically unlike the ones "
                f"that survive — largest pool-share difference {drift:.3f}, "
                f"ceiling {CENSUS_DRIFT_CEILING:.3f}. Coverage was {cov:.1%}. "
                f"A biased loss cannot be averaged away.")
        if cov < CENSUS_COVERAGE_FLOOR:
            print(f"  !! {city.slug} {year}: census reprojection mapped "
                  f"{cov:.1%} of this city's people, below "
                  f"{CENSUS_COVERAGE_FLOOR:.0%} — admitted because the loss is "
                  f"demographically even (shift {drift if drift is not None else float('nan'):.3f})")

    # ⛔ AND THE KEY SETS MUST AGREE, NOT MERELY INTERSECT.
    #
    # The delimitation label answers "should these join?"; it does not answer
    # "did the right rows join?". A MUNICIPAL boundary change inside one
    # delimitation gives a matching label and a silently wrong join — the same
    # shape as Cape Town, one level down. A join on reusable keys must assert on
    # the KEY SET. Reported rather than raised when the shortfall is small,
    # because a handful of wards genuinely fail to reproject and the coverage
    # floor above is the quantitative guard; a large gap is a different animal.
    matched = codes & set(people_by_ward)
    if codes and len(matched) < 0.5 * len(codes):
        raise SystemExit(
            f"{city.slug} {year}: only {len(matched)} of {len(codes)} election "
            f"wards found a census population after reprojection. The two are "
            f"not describing the same city.")

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

    # ⛔ REGISTRATION IS THE ONE LEVEL THAT MAY EXCEED 1, AND IT WAS CLIPPED.
    # Bounding all three at 1.0 clamped a quantity `census_correction` two
    # blocks down independently computes as 1.206 and 1.480 for this very city,
    # and pushed the surplus into the other pools: Johannesburg's White share of
    # the registered roll read 20.0% against 25.2% unclipped. See
    # REGISTRATION_MAX. `adult_share` and `turnout` genuinely cannot exceed 1
    # and keep the tight bound.
    registered, rates["registration"] = _nest(
        voting_age, np.array([reg_by_ward[w] for w in wards]),
        upper=REGISTRATION_MAX)
    voted, rates["turnout"] = _nest(
        registered, np.array([votes_by_ward.get(w, 0.0) for w in wards]))

    # How wrong the census would have to be for this to hold. Registration is
    # counted; ward population is a modelled small-area estimate, and for the
    # 2022 census the estimates for exactly these groups are the disputed ones.
    # So this ratio is reported as a property of the census, not of the model.
    implied = registered.sum(axis=0) / np.maximum(voting_age.sum(axis=0), 1e-9)
    rates["census_correction"] = np.maximum(implied, 1.0)

    # ⛔ A RATE ON A BOUND IS A REPORT THAT THE POOL IS UNIDENTIFIED.
    #
    # `_nnls` is now bounded to [0, 1] (§1.164), which stops a runaway rate but
    # replaces it with a corner — and a corner is not an estimate either. The
    # three levels are named so a reader can see WHERE identification failed:
    # Mangaung's Indian/Asian pool reaches a maximum ward share of 2.0-2.4%
    # anywhere in the city, so its turnout has never been identifiable and the
    # old code reported 0.0000 as though it were measured.
    unidentified = []
    # ⚠️ EACH LEVEL IS TESTED AGAINST ITS OWN BOUND. `registration` is bounded
    # at REGISTRATION_MAX, not 1.0, so testing it against 1.0 reported every
    # legitimately-above-one rate as a clipped corner — Johannesburg White at
    # 1.739 is an estimate, not a bound. Caught immediately after loosening the
    # bound without moving the detector with it.
    for name in ("adult_share", "registration", "turnout"):
        rate = rates.get(name)
        if rate is None:
            continue
        level_upper = REGISTRATION_MAX if name == "registration" else 1.0
        for g, flag in enumerate(_at_bound(rate, upper=level_upper)):
            if flag:
                reach = float((people[:, g]
                               / np.maximum(people.sum(axis=1), 1e-9)).max())
                # ⛔ TWO CAUSES, ONE MESSAGE, AND IT NAMED THE WRONG ONE. This
                # said "the ward table cannot identify this pool" for pools
                # reaching 71.1% and 77.2% of a single ward — abundant
                # identifying variation. They sat on the bound because the true
                # rate EXCEEDS it, which is a different fault with a different
                # fix, and the message sent the reader to the ward table
                # instead of the census denominator. Found by review 2026-09-05.
                why = ("the ward table cannot identify this pool at this level"
                       if reach < 0.25 else
                       "this pool IS identifiable (it reaches "
                       f"{reach:.1%} of a ward), so the bound is binding "
                       "because the true value lies beyond it — look at the "
                       "denominator, not the ward table")
                unidentified.append(
                    f"{categories[g]}: {name} fitted to {rate[g]:.4f}, which is "
                    f"ON A BOUND — {why}. The value is a clipped corner and not "
                    f"a measurement. Largest share this pool reaches in any "
                    f"ward: {reach:.1%}.")

    violations = []
    for name, child, parent in (("registered", registered, voting_age),
                                ("voted", voted, registered)):
        over = child.sum(axis=0) / np.maximum(parent.sum(axis=0), 1e-9)
        for g, ratio in enumerate(over):
            if ratio > 1.0:
                violations.append(
                    f"{categories[g]}: {name} is {ratio:.0%} of the level "
                    f"above it. ⛔ THE RATIO IS IMPOSSIBLE; THE COUNT IS NOT. "
                    f"Registration and votes are administrative events — an "
                    f"in-person appearance with an ID book — and the "
                    f"denominator is a MODELLED small-area census estimate, so "
                    f"the term that fails here is the estimate. The published "
                    f"ward totals are untouched either way: this machinery "
                    f"SPLITS them and does not revise them, so what a ratio "
                    f"above 1 impeaches is the split, not the roll. Do NOT "
                    f"read this as a "
                    f"census UNDERCOUNT either: the published Census 2022 figures for "
                    f"the white and Indian groups are argued to be too HIGH, "
                    f"not too low (over-adjustment for a 62%/72% "
                    f"post-enumeration undercount, leaving them 14%/24% above "
                    f"projections), which makes this gap wider rather than "
                    f"narrower. See DATA-QUALITY.md item 11.")

    return PoolCounts(wards=wards, categories=categories, people=people,
                      voting_age=voting_age, registered=registered, voted=voted,
                      rates=rates, violations=violations,
                      unidentified=unidentified)


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
    # ⛔ A FUTURE ELECTION HAS NO RESULT FILE AND DOES NOT NEED ONE.
    #
    # The wards of the election being forecast are published before it is held —
    # that is what a delimitation IS — and they land in
    # `<processed>/vd_ward_<year>.csv` with the pre-election roll: VD number,
    # ward id, and the registered voters in each part of a split VD. Requiring a
    # RESULT file to know the ward map confuses "which wards exist" with "who
    # won", and it broke the live 2026 forecast the moment `registered_at_target`
    # started reprojecting.
    template = cityconfig.CALENDAR[year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        # `Target.crosswalk`, not `target.processed` — the crosswalk is CITY
        # level (§1.97 F15, one definition since §1.120). Spelling the path here
        # is what left seven cities' crosswalks on disk where nothing looked;
        # `use_target()` would also have resolved the ACTIVE city's, not this
        # one's, which is the same defect one level along.
        roll = cityconfig.Target(city=city, year=year).crosswalk
        if roll.exists():
            # ONE crosswalk reader (§1.97 F18). This branch used to parse the
            # file itself, which made a THIRD copy of a read that has already
            # built two different cities out of one file without either
            # noticing (F14, §1.99). `ward_column` is passed explicitly because
            # this module keys wards by the MDB identifier the result files
            # carry, not by the ward number `montecarlo` uses.
            import montecarlo as _mc
            parts, _vds, _split = _mc.read_ward_crosswalk(
                roll, year, ward_column=f"WardID_{year}")
            ward_of, reg = {}, {}
            best: dict[str, float] = {}
            for vd, ward, part in parts:
                vd, ward = str(vd).strip(), str(ward).strip()
                if not vd or not ward:
                    continue
                # A split VD appears once per ward. Its registration is the sum
                # of its parts; its ward, for a one-to-one map, is the part that
                # holds most of it.
                reg[vd] = reg.get(vd, 0.0) + float(part)
                if float(part) >= best.get(vd, -1.0):
                    best[vd] = float(part)
                    ward_of[vd] = ward
            if ward_of:
                return ward_of, reg
        raise SystemExit(
            f"no ward map for {city.slug} {year}: neither a result file at "
            f"{path} nor a pre-election roll at {roll}")
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


# The share of a city's census population that must survive reprojection
# before the result is trusted. ⚠️ A CHOSEN NUMBER, NOT A MEASURED ONE — the
# quantity that matters is how far the citywide COMPOSITION moves because of
# what is missing, and coverage is a proxy for that with an unknown transfer
# function. Measured coverage runs 87.0% (Johannesburg 2006) to 72.5%
# (Mangaung 2006); at 0.80 the latter stays blocked. Registered in
# JUDGEMENT-CALLS.md and owed a sensitivity measurement.
CENSUS_COVERAGE_FLOOR = 0.80          # reported, no longer a refusal
# The refusal: how far a city's own composition moves because of wards that fail
# to reproject. MEASURED against the alternative — randomly ablating
# Johannesburg's wards all the way to 60% coverage moves a pool share by 0.028,
# so 0.05 is roughly twice the worst random loss and an order below the ~0.28
# that a genuinely segregated loss of a large block would produce.
CENSUS_DRIFT_CEILING = 0.05


_CENSUS_TOTAL_ROW = {"Total", "TOTAL", "total"}


def delimitation_for(year: str) -> int:
    """Which delimitation an election was fought on.

    Wards are redrawn for each local election and stand until the next one, so
    the delimitation is the most recent LGE at or before the year: the 2019
    national election used the 2016 wards, the 2024 national the 2021 wards.
    """
    lge = [int(y) for y, e in cityconfig.CALENDAR.items()
           if e.kind == "LGE" and int(y) <= int(year)]
    return max(lge) if lge else int(year)


def _reprojection_drift(city: cityconfig.City, from_year: str, to_year: str,
                        cfg: "Config") -> float | None:
    """How far this city's composition MOVES because of what fails to reproject.

    The largest per-pool shift between the citywide census mix computed over all
    source wards and the mix over only those that reach the target
    delimitation. `None` when nothing is lost. **This, not raw coverage and not
    the oddity of the lost wards, is what decides whether a reprojection is
    safe**: losing a quarter of a city evenly is nearly harmless, and losing one
    unrepresentative ward of 111 is harmless too — what matters is the product.
    """
    import numpy as _np
    old_ward, _ = vd_map(city, from_year)
    new_ward, _ = vd_map(city, to_year)
    reached = {w for vd, w in old_ward.items() if new_ward.get(vd) is not None}
    lost = {w for w in old_ward.values()} - reached
    if not lost:
        return None
    base = cfg.base()
    shares = read_census(base, base.censuses[-1], cfg)
    people = read_census_population(base.censuses[-1], cfg)

    def mix(ws):
        acc = _np.zeros(len(base.categories)); tot = 0.0
        for w in ws:
            if w in shares and w in people:
                acc = acc + _np.asarray(shares[w], dtype=float) * float(people[w])
                tot += float(people[w])
        return acc / tot if tot > 0 else acc

    # ⛔ THE HARM IS HOW FAR THE CITY MOVES, NOT HOW ODD THE LOST WARDS ARE.
    #
    # The first version returned |mix(kept) - mix(lost)|, which is the wrong
    # quantity twice over: it ignores HOW MUCH is lost, and it is largest
    # exactly when the loss is smallest and most peculiar. eThekwini loses ONE
    # ward of 111 — 34,980 people, 0.8% of the city — that is 99.8% Black
    # African against a city at 71.5%. That scored 0.282 and refused a metro we
    # already had, on a loss that moves the citywide composition by 0.002.
    #
    # So: compute the citywide mix WITH the lost wards and WITHOUT them, and
    # return how far it actually moved. That is the induced error, which is what
    # a threshold can honestly be set against.
    kept = mix(reached)
    whole = mix(reached | lost)
    if not kept.any() or not whole.any():
        return None
    return float(_np.max(_np.abs(whole - kept)))


def reproject_counts(counts: dict[str, float], city: cityconfig.City,
                     from_year: str, to_year: str) -> tuple[dict[str, float], float]:
    """Move a ward-level COUNT from one delimitation onto another.

    The twin of :func:`reproject`, and it must be a twin rather than a reuse
    because the two quantities move differently. A composition is a SHARE and is
    averaged into the new ward, weighted by registered voters; a population is a
    COUNT and must be SPLIT — each old ward's people are divided among its
    voting districts in proportion to registration, then summed into whichever
    new ward each district now sits in. Averaging a count would destroy it.

    ⛔ WHY THIS EXISTS. `composition_at` has reprojected since it was written, so
    the pre-2011 wards join the census correctly there — but
    `read_census_population` had no such branch, returned census-delimitation
    codes, and NOTHING JOINED. That single gap is what made 2006 unusable as a
    fitting year and therefore 2011 unusable as a backtest target: the whole
    pre-2011 archive was on disk, reconciled, and unreachable because one of two
    parallel census reads could not follow the wards.

    Owner, 2026-08-31: *"wards changed sizes yes… but you have the ward maps.
    Calculate what ward became what and adjust systematically to compensate when
    this happens (and it happens in every cycle)."* This is that compensation
    for the count half.

    Returns the reprojected counts and the fraction of the SOURCE total that
    could be mapped, so a caller can refuse a bad join instead of trusting it.
    """
    old_ward, old_reg = vd_map(city, from_year)
    new_ward, _ = vd_map(city, to_year)

    # Each old ward's registration, so a ward's people can be split across its
    # own voting districts in proportion to where its voters are.
    ward_reg: dict[str, float] = {}
    for vd, ward in old_ward.items():
        ward_reg[ward] = ward_reg.get(ward, 0.0) + old_reg.get(vd, 0.0)

    out: dict[str, float] = {}
    mapped = 0.0
    # ⛔ THE DENOMINATOR IS THIS CITY'S OWN POPULATION, NOT THE NATION'S.
    # The first version summed every key in `counts` — all 4,469 national wards,
    # plus a literal 'Total' row that double-counted the national figure — so
    # coverage came out as city/country, about 3%, and the guard refused every
    # time. Johannesburg 2006 reports 87.0% on the correct denominator and 3.4%
    # on the wrong one; the fix looked like a working refusal and was a broken
    # one.
    total = sum(float(counts[w]) for w in ward_reg if w in counts)
    for vd, src_ward in old_ward.items():
        people = counts.get(src_ward)
        denom = ward_reg.get(src_ward, 0.0)
        dest = new_ward.get(vd)
        if people is None or denom <= 0 or dest is None:
            continue
        share = old_reg.get(vd, 0.0) / denom
        out[dest] = out.get(dest, 0.0) + float(people) * share
        mapped += float(people) * share
    return out, (mapped / total if total > 0 else 0.0)


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


# ⛔ ONE RESOLUTION OF "THIS METRO'S CITYWIDE SHARES", AND A LEDGER OF WHAT
# SERVED IT. `metro_citywide(code, y) or _npe_citywide_for(code, y)` was written
# out at EIGHT sites across five record functions. Two things follow from that
# and both have bitten:
#
#   1. It is the duplication rule's own case — one definition, or the copies
#      drift. `_ward_reach` is NOT widened this way (its reader cannot parse the
#      clean files, §1.208), so which resolution a function uses is a real
#      distinction that eight inline copies cannot express.
#   2. **`HELD_BACK_OFF=1` IS ONE ENV VAR FROM BEING LOAD-BEARING ON THE ARRIVAL
#      RECORD.** `_npe_citywide_for` calls `levels._held_back` and returns `{}`
#      for the seven quarantined metros at lge2000, and every caller guards on
#      empty — so a quarantined metro-year is silently ABSENT from the record
#      rather than refused. That is an 8-way asymmetry taken on an absence, and
#      nothing measured it. Batch plan R4, risk item 5.
#
# The ledger counts, per record, how many (code, year) reads were OFFERED and
# what served each: the metro reader, the citywide fallback the 2000/2006
# widening added, or nothing. It is emitted into the spec, because **the specs
# are not in git** — after a restore, a number's provenance exists nowhere.
#
# ⚠️ COUNTING ONLY. `_citywide_for` returns exactly what the `or` returned:
# `metro_citywide` first, `_npe_citywide_for` when that is falsy, `{}` when
# both are. No value moves; `pools_sha` does.
_TRANSITION_LEDGER: dict[str, dict[str, int]] = {}
_LEDGER_RECORD: str | None = None


def _ledger_reset() -> None:
    """Start a fresh tally. Called once per emit, so counts are per-spec."""
    _TRANSITION_LEDGER.clear()


def _ledgered(name: str):
    """Attribute every `_citywide_for` read inside this function to one record.

    A DECORATOR rather than a `with` block at each call site, because a call
    site can be missed and a decorator cannot: any caller of the record is
    counted, including the tests. ``functools.wraps`` is load-bearing —
    ``tests/test_chain.py`` calls ``inspect.getsource(pools.measure_pool_ratios)``
    and ``inspect.signature`` on it, and both unwrap through ``__wrapped__``
    (verified 2026-09-08 rather than assumed).

    Nesting is handled by saving and restoring, so `splinter_record` called from
    inside `pooled_splinter_record` is attributed to the inner record and the
    outer one resumes afterwards.
    """
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            global _LEDGER_RECORD
            prev = _LEDGER_RECORD
            _LEDGER_RECORD = name
            _TRANSITION_LEDGER.setdefault(
                name, {"offered": 0, "metro": 0, "fallback": 0,
                       "unavailable": 0})
            try:
                return fn(*args, **kwargs)
            finally:
                _LEDGER_RECORD = prev
        return wrapper
    return deco


def _citywide_for(code: str, year: str) -> dict[str, float]:
    """One metro-year's citywide PR shares, from whichever reader can serve it.

    Exactly equivalent to ``metro_citywide(code, year) or
    _npe_citywide_for(code, year)``, which is what it replaces at every site
    that needs a metro-year's citywide shares. The only addition is the tally.

    No count is given here on purpose. This docstring said "all eight sites"
    while there were nine, and POOLS-REEMIT-QUEUE cited the pre-refactor
    token ``or _npe_citywide_for`` as the proof that the change had landed --
    a string that survives in this file only inside a comment, so the queue's
    own grep returned 1 and read as "not landed" on the eve of an
    irreversible emit. Count this helper's own call sites instead.
    """
    served = metro_citywide(code, year)
    how = "metro"
    if not served:
        served = _npe_citywide_for(code, year)
        how = "fallback" if served else "unavailable"
    if _LEDGER_RECORD is not None:
        row = _TRANSITION_LEDGER.setdefault(
            _LEDGER_RECORD,
            {"offered": 0, "metro": 0, "fallback": 0, "unavailable": 0})
        row["offered"] += 1
        row[how] += 1
    return served


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
                 panel_spread: dict[str, float] | None = None,
                 categories: tuple[str, ...] | None = None,
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
        # ⛔ THE WIDTH NO LONGER COMES FROM THIS CITY'S OWN max-min.
        #
        # `max - min` over two or three points is not a spread estimator: it can
        # only grow with sample size, so 2016 and 2021 targets got bands
        # approaching the unit interval while a 2011 target -- one prior
        # election, so no range at all -- got a typed 0.30 logits. Measured
        # against what happened, 7 of 8 2011 bands sat ENTIRELY BELOW the
        # realised turnout. §1.162 §9.
        #
        # `panel_spread` is how far a pool's turnout has actually MOVED between
        # local elections across the whole panel, using only transitions that
        # end before this target. The city's own observed range is kept as a
        # FLOOR: a city that has visibly moved more than the panel typical
        # should not be handed a narrower band than its own history shows.
        lg = _logit(column)
        own = float(lg.max() - lg.min()) if len(column) > 1 else 0.0
        name = categories[g] if categories and g < len(categories) else None
        measured = (panel_spread or {}).get(name, _PANEL_SPREAD_FALLBACK)
        spread = max(measured, own)
        low = float(_expit(_logit(centre) - spread))
        high = float(_expit(_logit(centre) + spread))
        bands.append((low, centre, max(high, centre * 1.001)))
    return bands


_PANEL_SPREAD_CACHE: dict[tuple, tuple[float, int]] = {}


def panel_turnout_spread(cfg: Config, before: str | None = None,
                         split_bloc: dict | None = None
                         ) -> tuple[dict[str, float], int]:
    """How far EACH pool's turnout moves between local elections, panel-wide.

    Returns ``({category: spread_in_logits}, n_observations)``.

    ⛔ WHY THIS EXISTS. :func:`turnout_band` took its width from the city's own
    observed range, ``max - min`` over the years on record, and fell back to a
    typed 0.30 logits when only one year existed. **A 2011 target has exactly
    one prior local election, so every 2011 band was 0.30 logits either side of
    a single reading**; measured against what happened, 7 of 8 sat ENTIRELY
    BELOW the realised turnout, Johannesburg's running 36.5%-43.3% against a
    realised 54.2% (§1.162 §9). And ``max - min`` over two or three points is
    not a spread estimator either: it can only grow with sample size.

    **The replacement is a property of the WORLD.** How much turnout moves
    between consecutive local elections has been observed eight metros at a
    time, and measuring it needs no reference to any forecast we have made —
    which keeps this on the estimation side of the line CLAUDE.md draws.

    ⚠️ **PER POOL, AND THAT IS THE WHOLE POINT.** A single spread pooled across
    every pool was measured first and rejected: small pools move enormously,
    the big pool carries 70-85% of the roll, and applying the small-pool
    movement to the big one **doubled the mean band width to 41.5pp while
    2016's coverage, already 8 of 8, gained nothing.** Coverage is gameable by
    widening and that was the game being played. Each pool now gets the width
    its own movement supports.

    ⚠️ **NO FUTURE.** Only transitions ending strictly before ``before`` count,
    so a 2011 target sees the 2000-2006 movement and nothing later.
    """
    # ⛔ NOT `id(cfg)`. The cache held no reference to the Config, so CPython
    # freed it and handed the same address to the next one — measured, five
    # `load_config()` calls returned three distinct ids with two reused. A
    # sweep that loads config A, emits, drops it, then loads config B with
    # different pool categories would silently get A's panel spread, so the
    # turnout band widths in the spec would come from the wrong dimension set.
    # Keyed on the config's CONTENT instead, which is what it was always
    # meant to mean.
    key = (str(before), _config_sha(CONFIG),
           repr(sorted((split_bloc or {}).items())))
    if key in _PANEL_SPREAD_CACHE:
        return _PANEL_SPREAD_CACHE[key]

    def _logit(x):
        x = np.clip(np.asarray(x, dtype=float), 1e-4, 1 - 1e-4)
        return np.log(x / (1 - x))

    moves: dict[str, list[float]] = {}
    total = 0
    for slug in sorted(q.stem for q in cityconfig.CITIES_DIR.glob("*.toml")):
        try:
            city = cityconfig.load(slug)
        except (Exception, SystemExit):
            continue
        seen: dict[str, tuple[tuple[str, ...], np.ndarray]] = {}
        for year, election in sorted(cityconfig.CALENDAR.items()):
            if election.kind != "LGE" or not election.results:
                continue
            if before is not None and int(year) >= int(before):
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    pc = pool_counts(city, year, cfg, split_bloc=split_bloc)
            except (Exception, SystemExit):
                # SystemExit is NOT an Exception subclass, and this module
                # raises it for a held-back election (`levels.HELD_BACK`) and
                # for a missing result file. Catching `Exception` alone let a
                # held-back Buffalo City 2000 abort the whole panel sweep.
                continue
            seen[year] = (tuple(pc.categories), pc.rates["turnout"])
        years = sorted(seen)
        for a, b in zip(years, years[1:]):
            (ca, ra), (cb, rb) = seen[a], seen[b]
            for i, name in enumerate(ca):
                if name not in cb:
                    continue
                j = cb.index(name)
                x, y = float(ra[i]), float(rb[j])
                # A pool UNIDENTIFIED at either end gives a movement between
                # two corner solutions, which is not a movement.
                if not (_RATE_BOUND_EPS < x < 1 - _RATE_BOUND_EPS
                        and _RATE_BOUND_EPS < y < 1 - _RATE_BOUND_EPS):
                    continue
                moves.setdefault(name, []).append(
                    float(_logit(y) - _logit(x)))
                total += 1

    pooled = [v for vs in moves.values() for v in vs]
    if not pooled:
        _PANEL_SPREAD_CACHE[key] = ({}, 0)
        return _PANEL_SPREAD_CACHE[key]

    def _spread(vals: list[float]) -> float:
        """A robust half-width, WINSORISED AT ONE POINT.

        ⛔ THIS USED TO BE `max(|delta|)` FOR A SMALL SAMPLE AND IT LET ONE
        BROKEN ROW SET THE BAND FOR THE WHOLE PANEL. Buffalo City's Coloured
        turnout is fitted at **0.0375** in 2006 and 0.6004 in 2011 — 3.75% of a
        pool voting is not a turnout, it is a rate-identification failure — and
        that single transition gives |delta logit| = **3.6529**, against a
        second-largest of 1.4320 and a median of 0.9618. It became the Coloured
        band for all eight metros at 2016: [2.5%, 97.5%], an interval that
        states nothing.

        With n around nine the 0.90 quantile IS the maximum, so the two branches
        were the same estimator wearing different names, and both were a single
        order statistic. Winsorising the top point is the smallest change that
        makes the estimate robust to exactly the failure observed: one corrupt
        transition can no longer set the width, two would still show.

        ⚠️ It is winsorisation of ONE point and no more. That is a choice, it is
        registered, and it is not a licence to trim until the answer is liked.
        """
        mag = np.sort(np.abs(vals))
        # ⚠️ WINSORISE ONLY WHERE THE SAMPLE CAN AFFORD IT. Dropping the top
        # point of four leaves three, and the estimate collapses to the typed
        # fallback -- which is the original defect, re-entered by the cure.
        # Measured: winsorising at every n took 2011 coverage from 5 of 8 back
        # to 1 of 8 while fixing 2016. Scarcity and contamination need opposite
        # treatments, and only one of them is robustness.
        if mag.size >= _WINSORISE_MIN_OBS:
            mag = mag[:-1]
        if mag.size < _PANEL_SPREAD_MIN_OBS:
            return float(max(mag.max(), _PANEL_SPREAD_FALLBACK))
        return float(max(np.quantile(mag, 0.90), _PANEL_SPREAD_FALLBACK))

    # ⛔ THE POOLED FLOOR APPLIES ONLY WHERE A POOL HAS NO EVIDENCE OF ITS OWN.
    #
    # It used to be `max(own, pooled)` for every pool under the observation
    # threshold, which handed **Black African — 70-85% of the roll — the
    # small-pool movement** (1.1618) over its own worst observed transition
    # (0.6194), a 1.9x inflation. That is verbatim the behaviour this function's
    # docstring says was measured and rejected, still live as a floor.
    # ⛔ THE POOLED FLOOR IS FOR SCARCITY, NOT FOR EVERY POOL.
    #
    # It used to be `max(own, pooled)` for every pool under the threshold, which
    # handed **Black African -- 70-85% of the roll -- the small-pool movement**
    # (1.1618) over its own worst observed transition (0.6194), a 1.9x
    # inflation, verbatim the behaviour this function's docstring says was
    # rejected. Removing it entirely was worse: at a 2011 target each pool has
    # ONE observation, and its own evidence is no evidence.
    #
    # So the floor applies exactly where a pool cannot speak for itself.
    fallback = _spread(pooled)
    out = ({name: (_spread(vs) if len(vs) >= _OWN_EVIDENCE_MIN_OBS
                   else max(_spread(vs), fallback))
            for name, vs in moves.items()}, total)
    _PANEL_SPREAD_CACHE[key] = out
    return out


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

    # ⛔ THE FITTING YEAR'S WARDS ARE NOT THE TARGET'S WARDS, AND THIS JOINED
    # THEM BY CODE.
    #
    # `by_ward` is keyed on the FITTING election's wards; the roll below is the
    # TARGET's. Wards are redrawn between local elections, so for any pair that
    # straddles a delimitation this was joining composition to the wrong
    # polygon — and because ward codes are reused, it succeeded. Measured share
    # of the target roll sitting in a voting district whose ward code changed
    # since the fitting election: **100% at a 2011 target for seven of eight
    # metros**, and still 3-37% at 2016 and 2021 targets — including the LIVE
    # 2026 forecast, where the target delimitation (2026) differs from 2021's.
    #
    # `reproject` is the SHARE twin and is the right one here: a composition is
    # averaged into the new ward weighted by registration, where a population
    # count would have to be split. See `reproject_counts` for the other half.
    # The fitting election's wards are not the target's. Wards are redrawn
    # between local elections, so for any pair straddling a delimitation this
    # was joining composition to the wrong polygon — and because ward codes are
    # reused, it SUCCEEDED. Measured share of the target roll sitting in a VD
    # whose ward code changed since the fitting election: 100% at a 2011 target
    # for seven of eight metros, and still 3-37% at 2016 and 2021 — including
    # the live 2026 forecast, whose delimitation differs from 2021's.
    #
    # `reproject` is the SHARE twin and is right here: a composition is averaged
    # into the new ward weighted by registration, where a population count must
    # be split. A future target needs no result file — `vd_map` reads the
    # pre-election roll for it.
    if delimitation_for(fitted_on) != delimitation_for(target.year):
        by_ward, covered = reproject(by_ward, city, fitted_on, target.year)
        if covered < CENSUS_COVERAGE_FLOOR:
            raise SystemExit(
                f"{city.slug}: moving the {fitted_on} composition onto the "
                f"{target.year} wards mapped only {covered:.1%} of the target "
                f"electorate. Below {CENSUS_COVERAGE_FLOOR:.0%} the join is "
                f"worse than the refusal it replaces.")

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
    # ⛔ `target.crosswalk`, NOT `target.processed`. The crosswalk is a CITY-level
    # artefact (§1.97 F15) and `Target.crosswalk` is its ONE definition
    # (§1.120). Spelling the path here read `data/processed/<slug>/<year>/` for
    # every city but Johannesburg — whose `legacy_processed_root` collapses the
    # two directories, which is exactly why the defect was invisible and why it
    # blocked `--city <any non-joburg> --target 2026 --emit`. The docstring
    # above has said "the city's own processed directory" throughout; the code
    # disagreed with it.
    path = target.crosswalk
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


@_ledgered("measure_pool_ratios")
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
            # ⛔ THE 2000 AND 2006 METRO RESULTS ARE ON DISK AND `metro_file` CANNOT
            # SEE THEM. `_npe_citywide_for` reads the same `_clean.csv` files through
            # `CALENDAR[year].results`, and the two readers agree to 0.00e+00 on all
            # 24 metro-years where BOTH resolve — so this is a resolver fallback, not
            # a second definition (§1.181). prereg/2026-09-03-arrival-record-widening.
            a = _citywide_for(code, before)
            b = _citywide_for(code, after)
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


@dataclass(frozen=True)
class ArrivalDefinition:
    """One of the ways this module decides that a party has ARRIVED."""
    predicate: str
    population: str
    splits: str
    computed_in: str
    consumed_by: str


# ⛔ THIS MODULE HAS FIVE DEFINITIONS OF "AN ARRIVAL" AND THEY ARE NOT
# INTERCHANGEABLE. NOTHING USED TO SAY WHICH ONE ANY FUNCTION OR TEST USED.
#
# Six errors in three days trace to that silence, and every one of them was a
# quantity measured over one of these populations and spent over another:
# §1.198 (the band claim), §1.199 (dispersion against the wrong estimator),
# §1.200 (the budget scored against the wrong arrival definition), §1.201 (the
# contender test measuring the chaff), §1.203 (the fifth), and §1.179 — the
# group budget itself, which was measured over ARRIVED_VS_NATIONAL and spent
# over ARRIVED_VS_NATIONAL_EXCLUDING_SPLITS, and was right only by accident.
# **None of the six was caught by a test.** Each was found by reading a row and
# asking whether the number could be true.
#
# So each site that computes one of these carries the marker
# ``# ARRIVAL DEFINITION: <NAME>``, and
# ``test_every_arrival_definition_is_named_where_it_is_computed`` asserts the
# register and the code agree IN BOTH DIRECTIONS — a name here with no site,
# and a site naming something not here, both fail. That bidirectionality is the
# point: the register guard that checked only code→register let a deleted lever
# sit in the register for days (CLAUDE.md §4).
#
# ⚠️ A NAME IS NOT A PROOF THAT THEY DIFFER. That is asserted separately, on
# the real record, by ``test_the_arrival_definitions_are_not_interchangeable``.
ARRIVAL_DEFINITIONS: dict[str, ArrivalDefinition] = {
    "ARRIVED_VS_NATIONAL": ArrivalDefinition(
        predicate="local share > 0 and preceding-NPE share <= 0, party != IND",
        population="every metro x every LGE year that has a preceding NPE",
        splits="INCLUDED",
        computed_in="arrival_group_record -> total",
        consumed_by="arrival_group_spec: the group TOTAL and its Dirichlet a"),
    "ARRIVED_VS_NATIONAL_EXCLUDING_SPLITS": ArrivalDefinition(
        predicate="ARRIVED_VS_NATIONAL and party not in SPLITS",
        population="the same rows; a strictly smaller set within each",
        splits="EXCLUDED",
        computed_in="arrival_group_record -> entrants",
        consumed_by="_arrival_total_prior: the group BUDGET, which "
                    "arrival_rules spends only over entrant_sizes"),
    "ARRIVED_VS_LOCAL_EXCLUDING_SPLITS_WITH_REACH": ArrivalDefinition(
        predicate="preceding-LGE share <= 1e-4 < share, party not in SPLITS, "
                  "and the party has a MEASURED ward reach",
        population="consecutive LGE pairs; a party with a national record but "
                   "no local one IS an arrival here and is NOT one above",
        splits="EXCLUDED",
        computed_in="entrant_record",
        consumed_by="comparators(): the per-entrant SIZE record"),
    "SEEDABLE_AT_TARGET": ArrivalDefinition(
        predicate="on the roster, absent from the fitted composition, not IND "
                  "or ENTRANT, and preceding-NPE baseline <= 0",
        population="one target city-year; a forecast set, not a record",
        splits="INCLUDED (a split is seeded, then SIZED off its parent)",
        computed_in="emit_pools -> newcomers",
        consumed_by="arrival_rules: who actually receives a seed"),
    "UNCLASSIFIED_WITH_NATIONAL_RECORD": ArrivalDefinition(
        predicate="on the roster, absent from the fitted composition, no "
                  "parent from classify_arrival, and preceding-NPE baseline "
                  ">= UNCLASSIFIED_FLOOR",
        population="one target city-year; DISJOINT from SEEDABLE_AT_TARGET by "
                   "construction, since one needs baseline <= 0 and the other "
                   "baseline > 0",
        splits="n/a - by construction these have no declared lineage",
        computed_in="emit_pools -> unclassified",
        consumed_by="the emitted spec's `unclassified_with_national_record`: "
                    "the nomination-day flag, not a size"),
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


@_ledgered("entrant_record")
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
            a = _citywide_for(code, before)
            b = _citywide_for(code, after)
            if not a or not b:
                continue
            # ⛔ `_ward_reach` IS NOT WIDENED — it goes through `metro_file`,
            # whose reader cannot parse the clean files. So for a transition
            # the fallback has just made visible, reach is `{}`.
            #
            # `reach.get(party, 1.0)` would then record every pre-2006 arrival
            # as having contested **100% of wards** — a fabricated covariate at
            # the most consequential value, landing squarely in the
            # `abs(r - 1.0) < 0.25` comparator bucket that sizes the arrivals
            # which win seats. 9 rows of 319 at target 2026, 9 of 63 at 2016.
            # SKIP the row instead: an unmeasured reach is not a reach of one.
            reach = _ward_reach(code, after)
            # ARRIVAL DEFINITION: ARRIVED_VS_LOCAL_EXCLUDING_SPLITS_WITH_REACH
            for party, share in b.items():
                if party in exclude:
                    continue
                if a.get(party, 0.0) <= 1e-4 < share and party in reach:
                    seen.append((share, reach[party]))
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


@_ledgered("home_splinter_record")
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
        a = _citywide_for(split.home, before)
        b = _citywide_for(split.home, after)
        if a.get(split.parent, 0) > 0 and b.get(party, 0) > 0:
            out[party] = b[party] / a[split.parent]
    return out


@_ledgered("splinter_record")
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
        # Was `metro_citywide` first and the fallback only under a
        # `if not a or not b:` guard. That guard saved nothing — `x or f()`
        # already short-circuits — and it was the eighth inline copy of the
        # resolution. Same values, one definition, and the ledger now sees it.
        a = _citywide_for(code, before)
        b = _citywide_for(code, after)
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
    """One metro's NPE shares by IEC code, for reading a split where it lived.

    ⛔ HONOURS `levels.HELD_BACK`, AND HAD TO BE TOLD TO. This is a SECOND reader
    of the same election files that `levels._citywide` reads, and when the
    pre-2011 history was held back there it kept flowing in through here —
    `npe1999` reached the splinter records while every other consumer thought it
    was excluded, and the panel moved by 2.63 CRPS for no stated reason.

    Two readers of one file is this repository's signature defect and the owner's
    standing rule is one definition only. The gate is imported rather than
    copied, so it cannot be true in one module and false in the other.
    """
    template = cityconfig.CALENDAR[year].results
    if not template:
        return {}
    path = Path(str(template).replace("{CODE}", code))
    if not path.exists():
        path = Path("data/raw/elections") / path.name
    if not path.exists():
        return {}
    import levels as _levels
    if _levels._held_back(path):
        return {}
    counts: dict[str, int] = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") in (None, "", "PR"):
                counts[P.canonical(row["sPartyName"])] += int(
                    float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()} if total else {}


@_ledgered("arrival_group_record")
def arrival_group_record(before_year: str | None = None
                         ) -> list[tuple[float, float, float]]:
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

    The quantity that behaves regularly is the GROUP TOTAL. Over the **29**
    metro-years now on record it runs 0.31% to 19.99%, **median 1.75%**, and it
    is rising — 2016 spans 0.31-4.74% against 2021's 1.53-19.99%.

    ⚠️ Every figure here is pinned by `test_the_arrival_record_figures_are_the
    _record`, which has now caught this docstring twice: it said "sixteen
    metro-years… median 3.11%" for weeks after the panel became 22, and it said
    22 within hours of the widening that made it 29. That is the guard working,
    and it is why the figures are derived by a test rather than trusted.

    ⛔ **THIS RECORD COUNTS SPLITS AS WELL AS ENTRANTS; ITS CONSUMER DOES NOT.**
    `arrival_rules` spends the budget only over `entrant_sizes`, which excludes
    every `as_split` party. Johannesburg 2021 is 19.99% as a group and **1.87%
    excluding splits**, a factor of 10.7. See `_arrival_total_prior`; do not
    repair one half alone.

    ⛔ **AND THE REASON THIS PARAGRAPH USED TO GIVE WAS FALSE.** It read: *"A
    party at its first local election has no preceding national vote whether it
    is a splinter or an entrant, so EFF, ActionSA, COPE, GOOD, MK and the NFP
    are all in these totals."* **Four of those six are in no row of this
    record.** The predicate is `natl.get(p) <= 0` at the PRECEDING NPE, and a
    contender normally has a national result first — the correction §1.201 had
    already made about the same six parties, not yet carried here. Measured over
    all 29 rows (2026-09-08), the only `SPLITS` members that appear at all are:

        2011  NFP  in JHB, TSH, EKU, ETH, CPT   (5 rows)
        2021  ASA  in JHB, TSH, EKU, ETH        (4 rows)

    EFF held a 2014 national vote before its first local election, COPE a 2004,
    GOOD a 2019 and MK a 2024 — **so none of them can be an arrival by this
    definition**, and 2000, 2006 and 2016 have `entrants == total` EXACTLY in
    every row. **The all-arrivals / entrants-only distinction therefore bites in
    9 rows of 29 and in two cycles of five**, and almost all of its magnitude is
    one party in one city: ActionSA's 18.12% of Johannesburg 2021.

    That does not make the split wrong — `_arrival_total_prior` must still
    measure over the population it is spent on — but it makes the *label*
    promise more than it delivers, which is what the five-way register above
    exists to stop. Do not read "excluding splits" as "excluding the parties you
    are thinking of".

    The concentration matters as much as the total, because the split is not
    even: the largest arrival took 91% of the group in Johannesburg 2021 and 20%
    in Cape Town 2016. The implied symmetric-Dirichlet α ranges 0.22 to 43.21
    with a median of 8.41, so the draw has to be able to produce both "one party
    takes almost all of it" and "thirty parties share it".

    ⛔ **THE WIDENING MOVED THAT CONCENTRATION HARD, AND IT MOVED IT THE WRONG
    WAY.** `arrival_group_spec`'s α, before → after: 2016 8.654 → 10.874 (+26%),
    **2021 4.357 → 9.758 (+124%)**, 2026 5.096 → 8.406 (+65%). A HIGHER α splits
    the group MORE EVENLY — so it makes "one arrival takes 91% of the group"
    less likely, and that case is Johannesburg 2021, ActionSA, the single
    largest error this model makes.

    ⚠️ **And it invalidates the measurement that retired `arrival_group_draw`.**
    That lever was refuted at CRPS 85.9 → 109.9, measured at α = 4.357. The
    spec it would read now carries 9.758. **The refutation does not transfer**
    and must be re-taken before the lever is called dead again. It is inert
    today only because the lever defaults to False.
    """
    out: list[tuple[float, float, float]] = []
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    for year in lge:
        if before_year and int(year) >= int(before_year):
            continue
        prev = cityconfig.preceding(year, "NPE")
        if not prev:
            continue
        for code in METRO_CODES:
            local = _citywide_for(code, year)
            natl = _npe_citywide_for(code, prev)
            if not local or not natl:
                continue
            # ARRIVAL DEFINITION: ARRIVED_VS_NATIONAL
            arr = {p: s for p, s in local.items()
                   if p != "IND" and s > 0 and natl.get(p, 0.0) <= 0}
            # ⚠️ THIS FLOOR BELONGS TO THE CONCENTRATION, NOT TO THE TOTAL,
            # AND IT SELECTS ON THE DEPENDENT VARIABLE. A symmetric-Dirichlet
            # α is not estimable below three members — that is why it is here.
            # `_arrival_total_prior` needs only the total and inherits it
            # anyway. The three rows it excludes are MAN 2006 (0.330%), BUF
            # 2006 (0.493%) and MAN 2011 (0.284%) — **the three smallest
            # arrival totals in the record, two of them in the cycle the
            # widening adds**. Measured effect on the budget (2026-09-04):
            #
            #     2011  1.8769% -> 1.5512% without the floor   (-17.4%)
            #     2016  1.3977% -> 1.2048%                     (-13.8%)
            #     2021  1.6433% -> 1.4840%                      (-9.7%)
            #     2026  2.1867% -> 2.0163%                      (-7.8%)
            #
            # JUDGEMENT-CALLS §L7. Left in place deliberately — removing it is
            # forecast-moving and belongs in a window with a pre-registration,
            # not in a commit that is fixing something else.
            if len(arr) < 3:
                continue
            total = float(sum(arr.values()))
            shares = np.array(list(arr.values())) / total
            n = len(shares)
            var = float(shares.var())
            mean = 1.0 / n
            alpha = max((mean * (1 - mean) / max(var, 1e-9)) - 1.0, 0.01)
            # ⛔ TWO TOTALS, BECAUSE THERE ARE TWO CONSUMERS AND THEY SPEND
            # OVER DIFFERENT POPULATIONS.
            #
            # A party at its FIRST local election has no preceding national
            # vote whether it is a splinter or an entrant, so EFF, ActionSA,
            # COPE, GOOD, MK and the NFP are all in `arr`. But `arrival_rules`
            # spends the group budget only over `entrant_sizes`, which excludes
            # every `as_split` party — so the budget was measured over a
            # population ~1.3x wider than the one it is spent on. Johannesburg
            # 2021 is 19.99% as a group and 1.87% excluding splits, a factor of
            # 10.7, and the whole of that gap is ActionSA (§1.179).
            #
            # `arrival_group_spec` still consumes the ALL-arrivals total and
            # concentration, because it splits between every named arrival.
            # `_arrival_total_prior` takes the entrants-only one. One record,
            # two totals, each spent where it was measured.
            # ⚠️ "ENTRANTS ONLY" IS ONLY DEFINED WHERE `SPLITS` IS POPULATED,
            # WHICH IS 2011 ONWARD. `SPLITS` names six modern parties (COPE,
            # EFF, NFP, GOOD, MK, ASA) and no pre-2011 one, so **all seven rows
            # the 2000/2006 widening adds have `entrants == total` exactly**
            # (verified 2026-09-04). At target 2011 that is every row, so the
            # population fix is a NO-OP on the fold it was measured to justify;
            # at 2016 it is 7 of 13 rows carrying 1.0106pp of the 1.3977pp
            # budget — 72% of the fold — structurally all-arrivals.
            #
            # The 2006 lists contain what look like genuine splits sized as
            # entrants: NATIONAL_DEMOCRATIC_CONVENTION (Jiyane out of the IFP,
            # 2005 — the same shape as the NFP, which IS in SPLITS) in five of
            # the seven, UNITED_INDEPENDENT_FRONT in six. So this corrects a
            # ~1.3x population error from 2011 on and leaves an unbounded one
            # before it. Do not read the label as a guarantee.
            # ARRIVAL DEFINITION: ARRIVED_VS_NATIONAL_EXCLUDING_SPLITS
            entrants = float(sum(v for q, v in arr.items() if q not in SPLITS))
            out.append((total, float(alpha), entrants))
    return out


def arrival_group_spec(before_year: str | None, reach: dict[str, float],
                       parties: list[str]) -> dict | None:
    """The group total to draw, and how to split it between named arrivals.

    ⛔ **THE CLAIM THIS DOCSTRING USED TO OPEN WITH IS REFUTED. It read: "Split
    weights are each arrival's WARD REACH, because that is what predicts an
    arrival's size and nothing else measured does."** Reach does correlate with
    size — within a city-year, which is the population a split operates over,
    Spearman +0.336 over 297 entrant-pairs, R² ≈ 0.11 — but **as a PROPORTIONAL
    WEIGHT it loses to a uniform vector by roughly 7 nats per city-year out of
    sample, on both scored cycles.** A positive correlation on log share is not a
    licence to use the covariate as a weight; that is a link-function error, the
    same shape as reading a rank correlation as a level.

    ⚠️ And reach does not identify the winner: it saturates exactly where the
    decision is. In 2021 six of eight metros have 6–18 parties at reach ≥ 0.90,
    with a mean of 3.4 tied at the maximum, and the highest-reach party is the
    largest arrival in only about a third of city-years. Within the reach ≥ 0.90
    subset the realised top takes 60.0% against 24.4% for an even split — reach
    picks the contender SET and says nothing about which contender wins. §1.220.

    ⚠️ These weights are inert today (`arrival_group_draw` is False) and this note
    exists so that whoever switches the lever on does not inherit the refuted
    rationale with it. The exchangeable vector is the defensible default.

    The original figures, kept because the correlation itself is real — but note
    the record is now 304 pairs, not 258, and re-derives to +0.320:

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
    # ALL-arrivals totals here, deliberately: this splits between every named
    # arrival, splinters included, so it spends over the population it was
    # measured on. `_arrival_total_prior` takes the entrants-only third element
    # because IT spends over entrants only. See `arrival_group_record`.
    totals = np.array([t for t, _, _ in record])
    alphas = np.array([a for _, a, _ in record])
    logs = np.log(totals)
    weights = {p: max(float(reach.get(p, 0.0)), 0.02) for p in parties}
    return {
        # ⛔ RENAMED FROM `total_log_median`, WHICH HELD A MEAN. The field is
        # the location of a LOGNORMAL the drawer samples the group total from,
        # and `np.mean(logs)` is what has always been stored — so the name said
        # median while every consumer spent a mean. Renamed rather than made
        # true: the mean of the logs is the right statistic here (the consumer
        # pins an expectation — §1.180 / JUDGEMENT-CALLS §L6), so the defect
        # was the label. Batched with the re-emit because it changes an emitted
        # key; `montecarlo` reads the old name as a fallback until every spec
        # on disk carries the new one.
        "total_log_mean": float(np.mean(logs)),
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
    # like-for-like. PR ballot, again to match, and because that is the ballot
    # a national poll speaks to.
    #
    # ⛔ THIS COMMENT USED TO CLAIM `read_municipality` HANDLES THE DRIFT
    # BETWEEN `_metros/` (`PartyName`) AND THE CLEAN FILES (`sPartyName`).
    # **It does not, and it cannot.** The reader takes the IEC's raw header —
    # PROVINCE / VOTINGDISTRICT / PARTYNAME / TOTALVALIDVOTES — and *emits*
    # `sPartyName`; handed a `_clean` file it raises `KeyError:
    # 'VOTINGDISTRICT'` (verified 2026-09-08), failing before it ever reaches
    # the party column the comment named. So `metro_file` resolves `_metros/`
    # and `_reports/` ONLY, the clean files are read by `_npe_citywide_for`
    # through a different reader, and **`metro_file` must never be widened to
    # reach them** — doing so breaks `metro_citywide`, `metro_roster` and
    # `_ward_reach` at once. The consequence is real and load-bearing:
    # `_ward_reach` cannot see a transition the citywide fallback has made
    # visible, which is why `entrant_record` SKIPS such a row rather than
    # defaulting its reach to 1.0. §1.197, batch plan R4.
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
    so it is a forecast input rather than hindsight. **The MEAN over ENTRANTS
    ONLY**, for the reason set out below — the consumer pins an expectation.

    ⚠️ These three sentences used to argue the opposite, and survived the change
    that reversed it: *"the median rather than the mean: the distribution is
    violently right-skewed and the mean is pulled by Johannesburg 2021, which is
    one observation."* That is a live argument against what the function now
    does, sitting at the top of the function that does it, and a reader who
    stopped after the first paragraph would have taken it as current. Kept only
    as this note. (The earlier correction it records is real: the docstring also
    once said "0.31%-4.74% over sixteen metro-years", which is 2016's range over
    eight.)

    ⛔ **BOTH HALVES WERE WRONG AND THEY VERY NEARLY CANCELLED.** Until
    2026-09-03 this returned the MEDIAN of the ALL-ARRIVALS total. The budget is
    spent only over `entrant_sizes`, which excludes every `as_split` party, so
    the population was ~1.3x too broad; and it was a median where the consumer
    is an expectation — the correction the entrant branch made on 2026-08-17,
    undone here in aggregate. On the 22-row record: 2.1701% used against
    2.2853% correct. **Repairing either half alone moved it the wrong way** —
    entrants-only median −23%, all-arrivals mean +97% — so they shipped
    together (§1.179, §1.180, JUDGEMENT-CALLS §L6).

    On the widened 29-row record, re-derived 2026-09-03:

        all arrivals   median 1.7458%   mean 3.6932%
        entrants only  median 1.5703%   mean 2.1867%   <- the mean is USED

    The values now passed:

        2011  n= 7  1.8769%      2016  n=13  1.3977%
        2021  n=21  1.6433%      2026  n=29  2.1867%

    ⛔ **THE OUT-OF-SAMPLE TABLE THAT USED TO SIT HERE RANKED BY MAGNITUDE,
    NOT BY SKILL, AND IT IS NOT EVIDENCE FOR THIS CHOICE.** Every estimator
    under-predicts at both scored targets, so Σ|err| collapses to
    `5.6555% − Σ(predictions)` and the biggest number wins by construction.
    ⚠️ **The instrument has TWO effective observations** — every metro-cell in a
    target shares one prediction, so the sum reduces to
    `|2.0424 − p| + |3.6131 − p|`, and "8 of 8 cells" is two year-level facts
    (§1.198). **A flat 2.8% scoring 1.5707% is not evidence either**: for two
    points every constant in [2.0424, 3.6131] scores exactly that, it is the L1
    minimum on an interval, and 2.8 is the midpoint of the two outcomes being
    scored. The honest pre-2016 constant is 1.40 — the pooled mean itself. The
    numbers:
    pooled mean 2.6146%, pooled median 3.0777%, recency 2.6893%, last-cycle
    2.7746% — and **a CONSTANT 2.8%, with no parameters and no record at all,
    scores 1.5707%**, forty percent better than the shipped estimator. Verified
    2026-09-04.

    **The mean is used anyway, and the reason is the consumer, not the score.**
    IPF pins each party's mean to its centre, so whatever goes into a centre is
    an expectation by construction (the 2026-08-17 correction). That argument is
    independent, sound and sufficient on its own. Recency is declined on
    parsimony — a half-life is a parameter a panel with ~3 effective clusters
    cannot support.

    ⚠️ **The 8-of-8 under-prediction is the real finding and it is unfixed.**
    The entrants-only series runs 0.84 → 2.04 → 3.61% over 2011/2016/2021 and
    no backward-looking statistic tracks it. **The 2026 arrival mass is more
    likely low than high**, and that belongs in the copy wherever it is quoted.
    """
    rec = arrival_group_record(before_year=str(before_year))
    if not rec:
        return None
    import numpy as _np
    return float(_np.mean([e for _, _, e in rec]))


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
    # (`default_support`, the median over the whole un-reach-matched record,
    # was deleted 2026-09-03: it was the `weights` branch's fallback and read
    # 4.8x low against the reach-matched `base` the entrant branch uses. One
    # definition of "no information", not two.)
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
        judged = False   # set by the entrant branch; see the group rescale

        # ONE decision about which machinery sizes this party, used by the
        # branch AND by the band below. They used to be decided separately —
        # the branch on `parent and parent in index and f_mid is not None`,
        # the band on `parent` alone — so a declared split in a city with no
        # splinter record of its own took the entrant branch and then divided
        # None by None building its band. Tshwane, Ekurhuleni and eThekwini
        # all hit it the moment ActionSA got a parent.
        f_lo, f_mid, f_hi, f_kind = band_for(party)
        as_split = bool(parent and parent in index and f_mid is not None)

        # ⛔ THE BAND IS A PROPERTY OF THE ARRIVAL RECORD, NOT OF OUR OWN CENTRE.
        #
        # These three were computed inside the entrant branch and read at the
        # bottom by every branch that is not a split. Two consequences, both
        # measured on 2026-09-03 and both on the path this seam exists to open:
        #
        #   * a party declared with `weights` — *"declare which pools it pulls
        #     from and what support you expect"*, which is what the note four
        #     branches down actually instructs a reader to do — raised
        #     `UnboundLocalError: lo_e` when it was the only newcomer;
        #   * and when it was not, it silently inherited the PREVIOUS party's
        #     quantiles rescaled by its own centre. A declared 12% picked up
        #     band [0.029, 1.0, 0.358] — a 95th percentile at 36% of the mean,
        #     which is not a band, and nothing would have said so.
        #
        # Identical in kind to the `(lo_e, mid_e, hi_e)` fallback repaired
        # above: three variables defined later, per party, inside the loop.
        # Fixing it there and leaving it here is why it is hoisted now.
        #
        # Dividing by `base` rather than by the adjusted `size` is the other
        # half. The quantiles describe how big arrivals turn out to be; the
        # declared centre says where we think THIS one sits. Dividing the first
        # by the second made the band narrow in proportion to the judgement —
        # ActionSA's x36 would have produced a band running to 7.7% of its own
        # centre, a forecast made 36x sharper by the act of admitting we are
        # guessing. The relative width belongs to the record and stays put.
        #
        # Number-neutral on the tree as it stands: no judgement file declares
        # `weights`, `support` or `overperform`, so `base` == the old `size`
        # and every emitted band is unchanged. Verified against all 26 specs.
        peers = comparators(reach)
        base = max(float(np.mean(peers)), 1e-9)
        lo_e = float(np.quantile(peers, ARRIVAL_BAND_LO))
        hi_e = float(np.quantile(peers, ARRIVAL_BAND_HI))

        if weights:
            vec = np.array([float(w) for w in weights], dtype=float)
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n_pools, 1.0 / n_pools)
            # ⛔ DECLARING POOLS IS NOT DECLARING A SIZE, AND THE FALLBACK
            # WAS THE WRONG ONE. `default_support` is the median over the
            # WHOLE, un-reach-matched arrival record — the estimator the
            # entrant branch removed on 2026-08-17 for under-forecasting every
            # arrival by a factor of four. On the live Johannesburg 2026 record
            # it reads 0.0607% against `base`'s 0.2901% for a full-reach party,
            # 4.8x low, so the two branches held different beliefs about what
            # "no information" means. They now share `base`.
            # ⛔ `overperform` IS READ HERE TOO, BECAUSE `PARTY_KEYS` PROMISES
            # IT UNCONDITIONALLY. The register describes it as "a multiplier on
            # the default strength", scoped to no branch, and the closed-key
            # refusal ACCEPTS it here — so a party declared with `weights` and
            # `overperform = 1.5` passed every guard and was seeded at the
            # comparator mean with the multiplier dropped on the floor. That is
            # the silent-discard class `PARTY_KEYS` was built to close,
            # surviving inside the mechanism that closed it. The two branches
            # now read the same two keys and combine them the same way: the
            # declaration (or the record) sets the level, the multiplier scales
            # it, and either one makes the party `judged` and therefore held
            # out of the group budget. Number-neutral on the tree as it stands
            # — no judgement file declares any of the three keys.
            stated = declared.get("support")
            mult = float(declared.get("overperform", 1.0))
            judged = stated is not None or mult != 1.0
            size = (float(stated) if stated is not None else base) * mult
            capture = _capture_from_share(vec, size, pool_size)
            short = capture_shortfall(vec, size, pool_size)
            why = ((f"pools and support DECLARED in judgements/: "
                    f"{float(stated):.2%} of the city, split by the declared "
                    f"weights"
                    if stated is not None else
                    f"POOLS declared in judgements/, size NOT declared: "
                    f"{base:.2%} from the {len(peers)} comparable arrivals on "
                    f"record. Set `support` to state it")
                   + (f", after a x{mult:g} judgement — seeded at {size:.2%}"
                      if mult != 1.0 else "")
                   + f". Band {lo_e / base:.2f}-{hi_e / base:.2f}x that centre "
                   + "— the declaration sets the level, the record sets the "
                     "width."
                   + (f" ⚠️ {short:.0%} of the declared share DID NOT FIT: the "
                      f"{MAX_POOL_CAPTURE:.0%} per-pool cap binds on this "
                      f"vector, so the party is seeded at "
                      f"{size * (1 - short):.2%}, not {size:.2%}. Spread the "
                      f"weights or lower `support`." if short > 1e-6 else ""))
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
            size = base
            # A judgement may say this one is unlike its comparators. Mashaba
            # had been mayor of this city and was widely liked, and nothing
            # measurable said so.
            #
            # ⚠️ The figure this comment used to quote — *"doubling the default
            # would have put ActionSA at 18.4% against an actual 18.12%"* — was
            # true when written and stopped being true the moment the group
            # rescale landed below, which renormalised any judgement straight
            # back out. Sizing ActionSA correctly needs `support = 0.18`, and
            # that only reaches the spec because a judged size is now held out
            # of the group budget. §1.178.
            # A judgement may state the level outright, or scale the default.
            # `support` was read ONLY in the `weights` branch above, so an
            # owner who knew the size but not the pools — the ordinary case
            # for a party announced without a ward list — had their number
            # silently discarded and got the comparator mean instead.
            stated = declared.get("support")
            if stated is not None:
                size = float(stated)
            mult = float(declared.get("overperform", 1.0))
            size *= mult
            judged = stated is not None or mult != 1.0
            capture = _capture_from_share(vec, size, pool_size)
            why = (f"entrant from nothing: even share of every pool. "
                   + (f"Sized at a DECLARED {float(stated):.2%} of the city"
                      if stated is not None else
                      f"Sized at the EXPECTED result for the {len(peers)} "
                      f"arrivals that contested about as much of a city "
                      f"({reach_used:.0%} of wards): mean {base:.2%}, median "
                      f"{np.median(peers):.2%}")
                   + (f" after a x{mult:g} judgement" if mult != 1.0 else "")
                   + f". Band {lo_e:.2%}-{hi_e:.2%} on the record, carried "
                   + "across as a RELATIVE width. THE EVEN SPREAD IS A "
                     "PLACEHOLDER: declare which pools it pulls from and what "
                     "support you expect.")
        rules[party] = {"capture": capture,
                        "band": [f_lo / f_mid, 1.0, f_hi / f_mid] if as_split
                                else [lo_e / base, 1.0, hi_e / base]}
        # ⛔ A JUDGED SIZE IS OUTSIDE THE GROUP BUDGET, OR IT IS NOT A SIZE.
        #
        # The rescale below holds the entrant GROUP to the arrival-total record.
        # That record is a prior over arrivals we know NOTHING about; a party
        # somebody has named and sized is not one of them. Leaving a declared
        # party in the budget renormalises the declaration away — measured
        # 2026-09-03 on a synthetic 30-entrant city, a declared 12.00% came out
        # at **0.3687%**, a factor of 33, while the note announced "group
        # rescaled x0.03". `support` had just been made readable and was still
        # doing nothing, and `overperform` had been in this position all along:
        # the comment above claiming a x2 judgement would have put ActionSA at
        # 18.4% has been false since the group rescale landed.
        #
        # It is not SUBTRACTED from the budget either. A cycle containing a
        # 12% arrival is not a cycle the 1.75% record describes, and netting it
        # off leaves the other twenty-nine entrants sharing a negative
        # remainder. The declared party sits outside; the undeclared ones keep
        # the record. JUDGEMENT-CALLS §L2.
        #
        # ⚠️ THE TEST IS `judged`, NOT `weights`. It was `not weights` for one
        # commit, which exempted a party whose POOLS were declared and whose
        # SIZE was not — so a `weights`-only party escaped the budget carrying
        # a number nobody had stated. The exemption is for a party somebody has
        # named AND SIZED; declaring a pool vector is neither.
        if not as_split and not judged:
            entrant_sizes[party] = size
        notes[party] = why

    # THE GROUP TOTAL IS THE QUANTITY THAT BEHAVES; THE SPLIT IS WHAT REACH
    # PREDICTS. Hold the first, use the mean above only for the second.
    #
    # Seeding each entrant at the reach-matched MEAN is right per party and
    # wrong per city, because a city fields twenty to forty of them: 30 x 0.34%
    # is a 10.2% arrival total against a pre-2021 record (n=14) whose median is
    # 1.6155% and whose maximum is 5.61% -- NOT 4.74%, which is 2016's maximum
    # over eight. Measured, that over-allocation
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


# ⚖️ The most of a pool one party may be seeded to take. A bare 0.9 literal
# until 2026-09-03, in no register entry, and it binds SILENTLY — see
# `capture_shortfall`. JUDGEMENT-CALLS §L5.
MAX_POOL_CAPTURE = 0.9


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
            out[g] = float(min(share * w * electorate / pool_size[g],
                               MAX_POOL_CAPTURE))
    return out


def capture_shortfall(weights: "np.ndarray", share: float,
                      pool_size: "np.ndarray") -> float:
    """How much of ``share`` the ``MAX_POOL_CAPTURE`` clip silently removed.

    ⚠️ THE CLIP IS INVISIBLE AND THE NOTE BESIDE IT STILL SAYS "DECLARED".
    Measured 2026-09-03 on Johannesburg-like pool sizes: a flat declaration of
    18.12% emerges at 16.44%, 25% at 20.15%, and 6% concentrated entirely in
    the Indian/Asian pool at **2.85% — 53% short**. Second-order at the
    ActionSA level and severe for a CONCENTRATED declaration, which is exactly
    what `weights` exists to express.

    Returns the fraction of the requested share that did not survive, so the
    caller can say so rather than reporting a number it did not deliver.
    """
    cap = _capture_from_share(weights, share, pool_size)
    if not cap or share <= 0:
        return 0.0
    got = sum(r * pool_size[g] for g, r in cap.items()) / pool_size.sum()
    return max(0.0, 1.0 - got / share)




def lineage_path(city: cityconfig.City, target: cityconfig.Target) -> Path:
    return Path("judgements") / f"{city.slug}-{target.year}.toml"


# Every key the `[roster]` table may carry. Closed for the same reason
# `PARTY_KEYS` is closed, and the failure here is worse: an unrecognised key
# does not mis-size one party, it discards the whole nomination list and falls
# through to a PROJECTED ballot printing only its routine message.
# ⚖️ The preceding-NATIONAL share above which a party with no declared lineage
# is flagged in the emitted spec as a possible undeclared split. JUDGEMENT-CALLS
# §L8. It is a REPORT, not a behaviour: nothing downstream reads it, and the
# party is still sized as an entrant exactly as before.
UNCLASSIFIED_FLOOR = 0.005

# ⚖️ The share of the fitting year's vote a `complete = true` roster may delete
# without an explicit acknowledgement. JUDGEMENT-CALLS §L4.
ROSTER_DROP_CEILING = 0.015

ROSTER_KEYS = {
    "parties":      "the names on the ballot",
    "complete":     "true only when this is the WHOLE ballot; licenses deletion",
    "reach":        "per-party fraction of wards contested, overriding the carry-forward",
    "wards":        "per-party ward lists, for full fidelity once lists land",
    "confirm_drop": "acknowledges a `complete` deletion above ROSTER_DROP_CEILING",
}

# Party codes the repository already knows. A declared name that resolves
# outside this set is either a genuine entrant — which must carry its own
# `[party.X]` table — or a typo. The check lives in `resolve_roster`,
# which has the city's composition and baseline; this set is only one of
# the four things it counts as known.
KNOWN_PARTY_CODES = (set(P.PARTIES) | set(P.ALIASES.values())
                     | set(P.MINOR_ALIASES.values()) | {"IND", "ENTRANT"})


# The only top-level tables a judgement file may carry. `[rostr]` was the last
# silent failure left in this file: `raw.get("roster")` returned None, the run
# fell through to a PROJECTED ballot, and the only sign was the routine "no
# roster for 2026" message it prints every other day of the year. One character,
# and the whole nomination list is discarded on the one day it matters.
LINEAGE_TABLES = {"party", "roster"}


def _lineage_raw(path: Path) -> dict:
    """Parse a judgement file, refusing a top-level table nothing reads."""
    raw = tomllib.loads(path.read_text())
    unknown = sorted(set(raw) - LINEAGE_TABLES)
    if unknown:
        raise SystemExit(
            f"{path} carries top-level {unknown}; only "
            f"{sorted(LINEAGE_TABLES)} are read.\n\n"
            f"`[rostr]` parses cleanly, reads as nothing, and drops the run "
            f"through to a PROJECTED ballot announcing only that no roster was "
            f"declared. Fix the spelling.")
    return raw


def declared_roster(city: cityconfig.City, target: cityconfig.Target) -> dict:
    """A nomination list declared by hand, from `[roster]` in the judgement file.

    Read from the same `judgements/<slug>-<year>.toml` that already carries each
    party's `parent`, `support` and pool `weights`, so a published list is
    **a config edit rather than a code change** on 16 September 2026 — which is
    the whole point of this seam. `load_lineage` has always ignored unknown
    top-level tables, so the file can be prepared and reviewed before this
    reader existed.

    Returns ``{"parties": [...], "complete": bool, "reach": {party: fraction},
    "wards": {party: [ward, ...]}}`` — empty dict when no `[roster]` is
    declared.

    ⛔ ``complete`` DEFAULTS TO FALSE, AND THAT IS THE WHOLE SAFETY PROPERTY.
    A declared roster is used to ADD parties always, and is allowed to REMOVE
    them only when it says it is the entire ballot. Absence from a list somebody
    is halfway through typing is not evidence that a party is not standing, and
    the branch that drops parties from the pools deletes 2.4-2.9% of a city's
    vote across 16-20 parties when it fires wrongly (measured, §1.175). On the
    day, under time pressure, a partial paste must fail safe.
    """
    path = lineage_path(city, target)
    if not path.exists():
        return {}
    raw = _lineage_raw(path)
    block = raw.get("roster")
    if not block:
        return {}
    unknown = sorted(set(block) - set(ROSTER_KEYS))
    if unknown:
        known = "\n".join(f"    {k:14s} {v}" for k, v in ROSTER_KEYS.items())
        raise SystemExit(
            f"[roster] in {path} carries {unknown}, which nothing reads.\n\n"
            f"A key this table does not recognise is ignored in silence, so "
            f"`partys = [...]` discards the entire nomination list and the run "
            f"falls through to a PROJECTED ballot with only a routine message "
            f"to say so. The keys are:\n{known}\n\nFix the spelling.")

    parties = [P.canonical(x) for x in (block.get("parties") or [])]
    wards = {P.canonical(k): list(v)
             for k, v in (block.get("wards") or {}).items()}
    reach = {P.canonical(k): float(v)
             for k, v in (block.get("reach") or {}).items()}
    # ⛔ A DECLARED `wards` LIST WITH NO READER IS THE `baseline_share` DEFECT
    # ONE TABLE OVER. It was parsed, returned, and consumed by nothing except
    # deriving `parties` — so an owner who pasted per-ward nominations and no
    # `[roster.reach]` got `reach = None` for every genuine entrant (it has no
    # prior ward ballot to carry forward), and `comparators(None)` then falls
    # back to the WHOLE un-reach-matched arrival record: the estimator this
    # file removed elsewhere for exactly that reason.
    #
    # Derived the same way `_ward_reach` derives it — a party's ward count over
    # the union of every ward the declaration mentions — so the two definitions
    # of "reach" cannot drift. An explicit `[roster.reach]` still wins.
    if wards:
        seen = {w for ws in wards.values() for w in ws}
        if seen:
            for q, ws in wards.items():
                reach.setdefault(q, len(set(ws)) / len(seen))
    if not parties and wards:
        parties = sorted(wards)

    # (The NAME check lives in `resolve_roster`, not here. It needs the
    # city's own composition and baseline to know what "known" means, and
    # this function has neither. See there.)

    # ⛔ THE TWO SAFETY BOOLEANS ARE TYPE-CHECKED, AND THEY WERE NOT.
    # `bool("false")` is True. Every other key in this table refuses a wrong
    # type loudly; the two whose entire job is safety accepted any truthy
    # string, so one pair of quotes turned the deletion on and a second pair
    # disabled the ceiling that would have caught it — at 22:00 on the one
    # night this file is ever edited.
    flags = {}
    for key in ("complete", "confirm_drop"):
        raw_flag = block.get(key, False)
        if not isinstance(raw_flag, bool):
            raise SystemExit(
                f"[roster] {key} in {path} is {raw_flag!r}, which is "
                f"{type(raw_flag).__name__} and not a boolean.\n\n"
                f"Write `{key} = true` or `{key} = false` without quotes. "
                f"`\"false\"` is a non-empty string and would read as TRUE — "
                f"and this flag decides whether parties are deleted from the "
                f"pools.")
        flags[key] = raw_flag

    return {"parties": parties, "complete": flags["complete"],
            "reach": reach, "wards": wards,
            "confirm_drop": flags["confirm_drop"]}


# Every key a `[party.X]` table may carry, and what reads it.
#
# ⛔ A MISSPELLED KEY IS SILENTLY IGNORED, AND THIS FILE IS EDITED UNDER TIME
# PRESSURE ON THE DAY A NOMINATION LIST LANDS. `support = 0.12` typed as
# `suport` costs nothing to type and the emit prints a party at the comparator
# mean with no complaint. So the set is closed and an unknown key refuses.
#
# `baseline_share` is INFORMATIONAL and nothing reads it — it records what the
# party polled at the preceding national election so a human sizing it has the
# number in front of them. It is NOT the strength knob; `support` is. All three
# docstrings said "parent, `baseline_share` and pool `weights`" and every one
# of the 408 party tables in the tree carries `baseline_share` and nothing
# else, so the documented way to size a declared party was a key with no
# reader. That is the trap this set closes.
PARTY_KEYS = {
    "parent":         "which sizing machinery: a named parent makes it a SPLIT",
    "weights":        "its pool vector, in `categories` order, normalised",
    "support":        "its expected share OF THE CITY — the strength knob",
    "overperform":    "a multiplier on the default strength, when you prefer "
                      "to scale the record rather than replace it",
    "baseline_share": "INFORMATIONAL: what it polled at the preceding national "
                      "election. Nothing reads this.",
}


def load_lineage(city: cityconfig.City, target: cityconfig.Target) -> dict[str, dict]:
    path = lineage_path(city, target)
    if not path.exists():
        return {}
    raw = _lineage_raw(path)
    table = dict((raw.get("party") or {}).items())
    for party, body in table.items():
        unknown = sorted(set(body) - set(PARTY_KEYS))
        if unknown:
            known = "\n".join(f"    {k:15s} {v}" for k, v in PARTY_KEYS.items())
            raise SystemExit(
                f"[party.{party}] in {path} carries {unknown}, which nothing "
                f"reads.\n\nA key this file does not recognise is ignored in "
                f"silence, so a typo costs a forecast rather than a run. The "
                f"keys are:\n{known}\n\nDelete it, or fix the spelling.")
    return table


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
        "#      `support` is its share of the city, and it is read whether or",
        "#      not you also set `weights` — until 2026-09-03 it was read only",
        "#      alongside them, so a party announced without a ward list had",
        "#      its declared size silently discarded. The default is what",
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
            f"# baseline_share is INFORMATIONAL — what it polled at "
            f"{target.previous_npe}. Nothing reads it.",
            f"baseline_share = {share:.4f}",
            'parent = ""      # e.g. "ANC" to inherit the ANC\'s pool vector',
            f'# weights = [{", ".join("0.0" for _ in pools_named)}]',
            "# support = 0.00   # its expected share OF THE CITY. THIS is the",
            "#                  # strength knob; `baseline_share` above is not.",
            "",
        ]
    path.write_text("\n".join(lines))
    return path


def city_mix_for(ctx: dict, n: int) -> "np.ndarray":
    """The city's own pool composition — where this city's votes actually are.

    ONE definition, used by the splinter blend and by an unmeasured entrant.
    It was written inline for the splinter and duplicated as `np.full(n, 1/n)`
    for the entrant, which is how the two came to disagree about what "we have
    no information" means. Falls back to a uniform vector only when the city has
    no measured pool votes at all, where there is genuinely nothing else to say.
    """
    pv = ctx.get("pool_votes")
    if pv is None:
        return np.full(n, 1.0 / n)
    arr = np.asarray(pv, dtype=float)
    return (arr / arr.sum()) if arr.sum() > 0 else np.full(n, 1.0 / n)


def resolve_roster(city: cityconfig.City, target: cityconfig.Target,
                   year: str, composition: dict, baseline: dict[str, float]
                   ) -> tuple[set[str], str, set[str], dict[str, float]]:
    """Who is on the ballot at ``target``, and who may be deleted from the pools.

    ONE definition, called by :func:`emit_pools`. It lives out here rather than
    inline because the three states below form a truth table, and a truth table
    that can only be reached through a 97-second city fit does not get tested —
    which is exactly how the first version of this shipped with the projected
    branch running in the declared case, silently overwriting a hand-declared
    nomination list two lines after reading it.

    Returns ``(roster, roster_source, deliberate, prior_local)``.

    * ``roster`` — every party on the ballot.
    * ``roster_source`` — ``published`` / ``declared`` / ``projected``.
    * ``deliberate`` — the subset of ``composition`` the caller may DELETE.
      Never simply "everyone absent from the roster"; see below.
    * ``prior_local`` — the fitting year's citywide shares, returned because the
      caller quotes them when it reports the drop and re-reading the file to
      get them is how the two floors stopped being measured on comparable
      quantities.
    """
    # ⛔ A ROSTER HAS THREE STATES, NOT TWO, AND THEY LICENSE DIFFERENT THINGS.
    #
    # `roster_is_real` was a boolean, and it conflated "we know the ballot" with
    # "we are allowed to delete parties from the pools". Those are not the same
    # question, and the second one deletes 2.4-2.9% of a city's vote across
    # 16-20 parties when it fires wrongly (§1.175).
    #
    #   published  the target's own result file. Absence is DELIBERATE: the
    #              party did not stand. Dropping is correct.
    #   declared   a hand-written list in the judgement file. Absence is
    #              AMBIGUOUS — it may be a partial paste on a deadline — so it
    #              may only drop when the list says `complete = true`.
    #   projected  our guess. Absence is mostly IGNORANCE, and dropping on
    #              ignorance is how a genuine entrant gets deleted. Only the
    #              parties a MEASURED floor deliberately excluded may be dropped.
    #
    # The rule the three share: **drop what was deliberately excluded, never
    # what was merely absent.**
    # Hoisted: the drop's message quotes it in all three states, and it was
    # previously defined only inside the projected branch.
    prior_local = _npe_citywide_for(city.code, year)

    # ⛔ THE PROJECTED BALLOT IS COMPUTED ONCE AND USED TWICE, FLOORS AND ALL.
    # The projected branch builds it, and a declared-but-INCOMPLETE roster
    # unions with it. Building it in only one place meant the union re-admitted
    # the 13 parties §K1 and §K2 had just excluded on measured evidence —
    # caught 2026-09-04 by `no_vector` going 8 -> 21 on the real 2026 inputs.
    # The floors' justification (§K1: 158 of 226 for 0.10pp; §K2: 112 of 189
    # for 0.038pp and zero seats) applies whoever is asking.
    _thin = {p for p, v in baseline.items()
             if p not in composition and v < NATIONAL_ONLY_FLOOR}
    _local_thin = {p for p, v in (prior_local or {}).items()
                   if p not in baseline and v < PRIOR_LOCAL_FLOOR}
    _projected = ((set(baseline) | set(composition))
                  - _thin - _local_thin - {"IND", "ENTRANT"})

    roster = contesting_parties(city, target.year)
    roster_source = "published"
    deliberate: set[str] = set()
    if roster:
        deliberate = {p for p in composition
                      if p not in roster and p not in ("IND", "ENTRANT")}
    else:
        declared = declared_roster(city, target)
        if declared.get("parties"):
            roster_source = "declared"
            # ⛔ "ADDS ALWAYS, REMOVES NONE" MUST MEAN UNION. IT MEANT REPLACE.
            #
            # `roster = set(declared["parties"])` looked right and inverted the
            # only safety property this branch has. `no_vector` derives from
            # `roster`, so a BASELINE party omitted from a partial paste is not
            # in `roster`, is therefore not in `no_vector`, and never gets a
            # pool vector at all — it falls to the residual bucket and is drawn
            # against a range meant for minor parties.
            #
            # Measured on the real 2026 inputs: pasting the top six and
            # stopping cost **8 parties 15.4826% of the 2024 baseline their
            # pool vector, MK alone at 12.22%** — while the run printed "ADDS 6
            # parties and removes none". The half-typed list is exactly the
            # case `complete` defaults to False for.
            #
            # So an INCOMPLETE roster unions with what a projection would have
            # produced. A COMPLETE one replaces, which is what declaring the
            # whole ballot means.
            declared_set = set(declared["parties"])
            # ⛔ A NAME THAT RESOLVES TO NOTHING BECOMES A PARTY OF ITS OWN —
            # AND THE FIRST VERSION OF THIS CHECK BLOCKED THE REAL BALLOT.
            #
            # `parties.canonical` slugs what it does not recognise, so a
            # mis-transcription becomes a phantom, and under `complete = true`
            # it deletes the real party too. That is worth refusing.
            #
            # But "known" was first defined as the hand-maintained alias tables
            # alone, and **rehearsing the actual 2021 Johannesburg ballot — 57
            # parties, the realistic shape of a nomination list — REFUSED**,
            # because the long tail of small parties that genuinely contested
            # has canonical codes and no alias entry. A guard that fires on the
            # correct input on the one night it runs is worse than no guard.
            #
            # "Known" is therefore: in the alias tables, OR carrying a prior
            # record in this city (the fitted composition or the national
            # baseline), OR placed by its own `[party.X]` table. Only a name
            # with none of those three is a typo.
            # ⚠️ AND A PARTY THAT STOOD LAST TIME IS KNOWN EVEN IF IT SCORED
            # NOTHING. `composition` holds only parties with a fitted vector,
            # so AFRICAN_COVENANT and SAKHISIZWE_CONVENTION — both on the real
            # 2021 Johannesburg ballot with zero votes — were refused by the
            # first version of this, on a rehearsal of the actual ballot. The
            # ballot itself is the authority on who is a real party.
            # ⚠️ CANONICALISED, because `declared_set` is. A quoted TOML key
            # — `[party."SOME NEW PARTY"]` — would otherwise never match
            # `SOME_NEW_PARTY`, so the run would refuse and tell the owner to
            # do the thing they had just done.
            placed = {P.canonical(q) for q in load_lineage(city, target)}
            known = (KNOWN_PARTY_CODES | set(composition) | set(baseline)
                     | set(contesting_parties(city, year)) | placed
                     | {"IND", "ENTRANT"})
            unplaced = sorted(declared_set - known)
            if unplaced:
                raise SystemExit(
                    f"[roster] in {lineage_path(city, target)} names "
                    f"{unplaced[:8]}"
                    f"{' …' if len(unplaced) > 8 else ''}, which resolve to no "
                    f"known party, carry no record in {year} or "
                    f"{target.previous_npe}, and have no [party.X] table.\n\n"
                    f"`parties.canonical` slugs a name it does not recognise, "
                    f"so a mis-transcription becomes a NEW party — and under "
                    f"`complete = true` it also deletes the real one.\n\n"
                    f"⛔ CHECK THE SPELLING FIRST, against parties.py. A real "
                    f"party under an unfamiliar IEC spelling is far more likely "
                    f"than a new one, and 'fixing' it with a [party.X] table "
                    f"turns a party that HAS a baseline into a phantom entrant "
                    f"sized from the arrival record — while `complete = true` "
                    f"deletes the real one. That is the ActionSA failure with "
                    f"the sign reversed.\n\n"
                    f"Only if it is genuinely new: give it a [party.X] table "
                    f"saying how strong it is and which pools it draws from.")
            if declared["complete"]:
                roster = declared_set
            else:
                roster = declared_set | _projected
            # ⛔ A DECLARED PARTY WHOSE KEY DOES NOT MATCH THE BASELINE'S IS
            # SIZED AS AN ARRIVAL, SILENTLY.
            #
            # `KNOWN_PARTY_CODES` catches a name that resolves to nothing. It
            # cannot catch one that resolves to a DIFFERENT valid key from the
            # one the preceding national file used — canonicalisation does not
            # span eras. Measured 2026-09-03 at Johannesburg 2000: npe1999
            # carries `VRYHEIDSFRONT \ FREEDOM FRONT` -> VRYHEIDSFRONT_FREEDOM_
            # FRONT while lge2000 carries `VRYHEIDSFRONT PLUS` -> VFPLUS, so
            # **VF Plus is counted as an ARRIVAL at 0.19% against a baseline
            # where it actually polled 0.29%.**
            #
            # On the record that is a rounding error. On the LIVE path it is
            # not: a party pasted from the nomination list under a spelling the
            # 2024 national file did not use has no baseline, so it is seeded
            # from the arrival record instead of carrying its real share — the
            # ActionSA failure with the sign reversed. MK's 12.22% baseline is
            # exactly what would be lost.
            #
            # It REPORTS rather than refuses: a genuine entrant has no baseline
            # by definition, and that is the case this seam exists for. What the
            # owner needs on the day is the list, to eyeball.
            # ⚠️ THE PREDICATE IS `newcomers`', NOT A LOOKALIKE. The sizing
            # rule is `baseline.get(p, 0.0) <= 0.0`; this warned on
            # `q not in baseline`, so a party PRESENT in the baseline file with
            # zero votes was sized as an arrival in silence. Two such rows exist
            # in lge2021_JHB (AFRICAN_COVENANT, SAKHISIZWE_CONVENTION), so the
            # class is real in this data even though npe2024_JHB has none.
            as_arrival = sorted(q for q in roster
                                if q not in composition
                                and baseline.get(q, 0.0) <= 0.0
                                and q not in ("IND", "ENTRANT"))
            if as_arrival:
                print(f"  ! {len(as_arrival)} declared parties have NO "
                      f"{target.previous_npe} baseline and no fitted vector, so "
                      f"they are sized as ARRIVALS: {', '.join(as_arrival[:8])}"
                      f"{', …' if len(as_arrival) > 8 else ''}. Correct for a "
                      f"genuine entrant. For a party that already exists it "
                      f"means the name here does not match the one in the "
                      f"{target.previous_npe} results and its real share is "
                      f"being thrown away — check it against parties.py.")
            if declared["complete"]:
                deliberate = {p for p in composition
                              if p not in roster and p not in ("IND", "ENTRANT")}
                # ⛔ THE DELETION RECONCILES, OR IT DOES NOT HAPPEN.
                #
                # A count is not a check. §1.175 measured a wrongly-fired drop
                # at 2.4-2.9% of a city's vote across 16-20 parties, and under
                # largest remainder ~0.4% is a seat — so the number that
                # matters is the MASS, and it is the number the message did not
                # print. Above the ceiling the run refuses and names what it
                # would have deleted, because a paste that drops a fifth of the
                # ballot is far likelier to be half a list than a real one.
                dropped_mass = sum((prior_local or {}).get(p, 0.0)
                                   for p in deliberate)
                if dropped_mass > ROSTER_DROP_CEILING and not declared["confirm_drop"]:
                    worst = sorted(deliberate,
                                   key=lambda q: -(prior_local or {}).get(q, 0.0))
                    named = ", ".join(
                        f"{q} {(prior_local or {}).get(q, 0.0):.2%}" for q in worst[:8])
                    raise SystemExit(
                        f"the declared {target.year} roster says `complete = true` "
                        f"and would delete {len(deliberate)} parties holding "
                        f"{dropped_mass:.2%} of the {year} vote, above the "
                        f"{ROSTER_DROP_CEILING:.1%} ceiling.\n\n"
                        f"Largest first: {named}"
                        f"{', …' if len(worst) > 8 else ''}\n\n"
                        f"A drop this size is more often half a nomination list "
                        f"than a real one, and it is funded out of the parties "
                        f"ranked 4th to 12th, which the model already "
                        f"under-predicts (§1.175). Check the list against the "
                        f"IEC's. If it IS right, add `confirm_drop = true` to "
                        f"[roster] in {lineage_path(city, target)}.")
                print(f"  ! the declared {target.year} roster says it is COMPLETE, "
                      f"so {len(deliberate)} parties holding {dropped_mass:.2%} "
                      f"of the {year} vote are dropped from the pools"
                      + (" (confirm_drop)" if declared["confirm_drop"] else ""))
            else:
                added = sorted(declared_set - _projected)
                print(f"  ! the declared {target.year} roster does NOT say "
                      f"`complete = true`, so it is UNIONED with the projected "
                      f"ballot: {len(declared_set)} declared, {len(added)} of "
                      f"them new, {len(roster)} on the ballot in total, and "
                      f"NOTHING removed. Set `complete = true` once the list is "
                      f"known to be the whole ballot.")
        else:
            roster_source = "projected"
            # ⛔ NOT EVERY PARTY WITH A NATIONAL VOTE. Measured over 16 city-years
            # (§1.175): candidates carrying a preceding NATIONAL vote but no
            # preceding LOCAL record number 226, win a seat 13.3% of the time, and
            # carry 5.12% of a city's vote — while the 189 candidates with BOTH
            # kinds of evidence carry 89.73%. Admitting the whole national ballot
            # buys a long tail of parties that will not stand.
            #
            # But the class cannot be dropped: **MK is exactly it for 2026** — a
            # 2024 national party with no 2021 local vector — so the limit is on
            # SIZE, not on class. At a 0.1% national floor, 158 of those 226
            # candidates go and the cost is **0.10pp of a city's vote**; the large
            # ones transfer nearly one-for-one (national 11.51% -> local 11.64%,
            # 10.13% -> 10.93%), which is why cutting the tail is safe.
            #
            # Owner's decision, 2026-09-03. JUDGEMENT-CALLS.md §K1.
            thin = _thin
            # ⛔ AND THE SAME CUT ON THE OTHER SINGLE-SOURCE CLASS, which was left
            # unfiltered in the first draft and is the better bargain of the two.
            # A party that contested the preceding LOCAL election and polled
            # nothing at the preceding national one stands again only 28% of the
            # time (137 of 189 never do, three cycles). At a 0.1% floor on its
            # prior LOCAL share this drops 112 of 189 candidates for **0.038pp of
            # vote and ZERO seats** — against the national floor's 70% for two
            # seats. At 0.2% it costs 5 seats, so the value is the same 0.1% and
            # for the same reason. §K2.
            # `prior_local` is the party's own share at the election the vectors
            # were fitted on, read through the same PR-filtered path `baseline`
            # uses so the two floors are measured on comparable quantities.
            local_thin = _local_thin
            roster = _projected
            # ⛔ THE ONLY PARTIES A GUESS MAY DELETE ARE THE ONES IT DELIBERATELY
            # EXCLUDED. `thin` and `local_thin` are removals made on measured
            # evidence (§K1: 158 of 226 for 0.10pp and two seats; §K2: 112 of 189
            # for 0.038pp and none). Everything else missing from a projected
            # roster is ignorance, and dropping on ignorance is how a genuine
            # entrant is deleted.
            deliberate = {p for p in (thin | local_thin)
                          if p in composition and p not in ("IND", "ENTRANT")}
            if local_thin:
                print(f"  ! {len(local_thin)} parties contested {year} locally below "
                      f"{PRIOR_LOCAL_FLOOR:.1%} and polled nothing nationally, so they "
                      f"are NOT assumed onto the {target.year} ballot (JUDGEMENT-CALLS "
                      f"§K2; costs 0.038pp of vote and zero seats on the record)")
            if thin:
                print(f"  ! {len(thin)} parties held a {target.previous_npe} national "
                      f"vote below {NATIONAL_ONLY_FLOOR:.1%} and no local record, so "
                      f"they are NOT assumed onto the {target.year} ballot "
                      f"(JUDGEMENT-CALLS §K1; costs 0.10pp of vote on the record)")
            print(f"  ! no roster for {target.year}: it has not been held and none "
                  f"is declared, so the ballot is PROJECTED. Parties in the "
                  f"{target.previous_npe} baseline still get a pool vector, but NO "
                  f"GENUINE ENTRANT CAN BE FOUND — a party contesting "
                  f"{target.year} with no {target.previous_npe} vote is invisible "
                  f"to a projection, and ActionSA in 2021 was exactly that "
                  f"(18.12% of Johannesburg). To add one, name it under [roster] "
                  f"in {lineage_path(city, target)} and give it a strength and "
                  f"pools under [party.X] there — the roster table puts a party on "
                  f"the ballot, the party table says how strong it is and which "
                  f"pools it draws from.")
    return roster, roster_source, deliberate, prior_local


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
    # One tally per emit, so `transition_ledger` below counts THIS spec's reads
    # and not every read since the process started. `emit_pools` is the only
    # resetter; a caller measuring a record on its own gets a cumulative tally,
    # which is the right answer for that use and the wrong one here.
    _ledger_reset()
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
    panel_spread, spread_n = panel_turnout_spread(
        cfg, before=target.year, split_bloc=split_bloc)
    if spread_n < _PANEL_SPREAD_MIN_OBS:
        print(f"  !! turnout band width rests on {spread_n} observed pool "
              f"transition(s) before {target.year} — the full observed range "
              f"is used rather than a quantile, because a quantile of that "
              f"many points cannot see a tail it holds no points in")
    turnout = turnout_band(record, n, panel_spread=panel_spread,
                           categories=tuple(cats))
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
    # Who is on the ballot, and who may be deleted from the pools. Three
    # states, and only two of them license a deletion — `resolve_roster`.
    roster, roster_source, deliberate, prior_local = resolve_roster(
        city, target, year, composition, baseline)
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
    absent = sorted(deliberate)
    if absent:
        # ⚠️ REPORT BOTH SHARES. This used to quote only the party's share of
        # the preceding NATIONAL baseline — which is EXACTLY 0.000% for every
        # party `local_thin` removes, because polling nothing nationally is what
        # put it there. The message would have read "27 parties holding 0.00%"
        # while they held 0.038pp of the local vote. A drop that reports itself
        # as free is the one nobody checks.
        held = sum(baseline.get(p, 0.0) for p in absent)
        held_local = sum((prior_local or {}).get(p, 0.0) for p in absent)
        for party in absent:
            composition.pop(party, None)
        print(f"  dropped from the pools as not on the {target.year} ballot "
              f"({roster_source} roster): {len(absent)} parties holding "
              f"{held:.2%} of the {target.previous_npe} national baseline and "
              f"{held_local:.3%} of the {year} local vote "
              f"({', '.join(absent[:6])}{', …' if len(absent) > 6 else ''})")

    # ⛔ A PARTY DECLARED IN THE JUDGEMENT FILE JOINS THE ROSTER, OR THE
    # DECLARATION DOES NOTHING.
    #
    # `no_vector` derives from `roster`, and a PROJECTED roster is built from
    # the baseline and the fitted composition — so a genuinely new party, which
    # by definition appears in neither, was never iterated. The file's own
    # template says "these parties will be on the ballot… THE MODEL CANNOT
    # ANSWER THIS. You can", and `emit_pools` prints a message pointing a reader
    # at it — while the path was inert for exactly the case it advertises.
    # That is why ActionSA could not be declared into the 2021 forecast.
    # ⚠️ AND `[party.X]` DOES NOT PUT A PARTY ON THE BALLOT — `[roster]` DOES.
    #
    # A first version of this added every `[party.X]` entry to the roster, and
    # it was wrong: `write_lineage_template` auto-generates one entry per
    # `no_vector` party, so the file already lists parties the floors have since
    # excluded on measured evidence, and a stale template would have silently
    # overridden §K1 and §K2 — 13 of them at Johannesburg 2026. The file's own
    # header says what those entries are: *"These parties are in the baseline
    # but did not contest the election the pool vectors were fitted on"*. They
    # describe HOW to place a party that is already standing.
    #
    # So the two tables have two jobs, and a genuine entrant needs both:
    #   [roster]   parties = [...]        who is on the ballot
    #   [party.X]  support/parent/weights          how strong, and which pools
    lineage = load_lineage(city, target)

    no_vector = {p for p in roster
                 if p not in composition and p not in ("IND", "ENTRANT")}
    # A seed is only for a party with no level to start from.
    # ARRIVAL DEFINITION: SEEDABLE_AT_TARGET
    newcomers = {p for p in no_vector if baseline.get(p, 0.0) <= 0.0}
    inherited: dict[str, str] = {}
    # ⛔ A PARTY WITH A NATIONAL RECORD AND NO LINEAGE IS THE ActionSA SHAPE,
    # AND NOTHING USED TO SAY SO WHERE ANYONE WOULD SEE IT.
    #
    # `classify_arrival` returns "no lineage on record: arrived from nothing"
    # for anything absent from `SPLITS` and undeclared. That answer is right for
    # a genuine entrant and wrong for a party that plainly exists — it just
    # split from someone nobody has typed in. Getting that wrong once cost
    # 0.1% against an actual 18.12%.
    #
    # The detector triggers on the party's share at the preceding NATIONAL
    # election, not on its (definitionally zero) local baseline: a party that
    # exists nationally and has no local lineage is exactly the case worth a
    # second look. `unclassified` is EMITTED INTO THE SPEC rather than printed,
    # because a print during an emit is scrollback and the emit is the one
    # operation nobody re-runs. In the file it is diffable, it survives into
    # `compare_history`, and a test can assert on it.
    unclassified: dict[str, float] = {}
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
        national = float(baseline.get(party, 0.0))
        # ARRIVAL DEFINITION: UNCLASSIFIED_WITH_NATIONAL_RECORD
        if not parent and national >= UNCLASSIFIED_FLOOR:
            unclassified[party] = national
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
            city_mix = city_mix_for(ctx, n)
            vec = alpha * composition[parent] + (1.0 - alpha) * city_mix
            vec = vec / vec.sum() if vec.sum() > 0 else np.full(n, 1.0 / n)
            inherited[party] = (f"splinter of {parent}, {alpha:.0%} its vector "
                                f"and {1 - alpha:.0%} the city average")
        else:
            # An entrant with no measured vector and no declared parent draws in
            # proportion to WHERE THE VOTES ARE — the city's own pool
            # composition, the same `city_mix` the splinter blend leans on.
            #
            # ⛔ THIS WAS AN EVEN SHARE OF EVERY POOL, `np.full(n, 1/n)`, AND
            # THAT IS NOT A NEUTRAL ASSUMPTION — IT IS AN IMPOSSIBLE ONE.
            # The intent was honest ("make the absence of a judgement visible
            # rather than convenient"), but an even share assigns a party 25% of
            # its vote from a pool that may cast almost nothing. Measured at
            # Buffalo City 2016, where the Indian/Asian pool has 8,107
            # registered voters casting ~1 vote: three parties were each given
            # 0.25 of it, which is 228.93x more than the pool can cast. At
            # Mangaung 2016 the same pool casts EXACTLY ZERO and still carried
            # weight, which made the guard raise ZeroDivisionError rather than
            # report a finding.
            #
            # The city mix keeps the intent — it is still not a fitted vector,
            # and `inherited` still says so — while being arithmetically
            # possible by construction. A party nobody has measured is best
            # assumed to draw like the city, not like a uniform distribution
            # over categories of wildly different size.
            #
            # Found 2026-08-31 by widening `test_pool_bounds`, whose target list
            # was typed when nine specs existed and never grew to sixteen: all
            # nine violations sat in the seven city-years it had stopped
            # scanning.
            vec = city_mix_for(ctx, n)
            inherited[party] = ("entrant, no measured vector — spread as the "
                                "city's own pool composition"
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

    # ONE NAME PER DATASET. This was `record`, the name bound 240 lines
    # above to `turnout_record` and still read at `turnout_limits` two
    # lines up — two unrelated series sharing a name inside one function,
    # so anything hoisted past the rebinding would silently read the other.
    entrant_hist = entrant_record(lge_transitions(before=target.year))
    rates_matrix = np.array([[fits[p].rates[g] if p in fits else 0.0
                              for p in sorted(fits)] for g in range(n)])
    universe_fitted = sorted(fits)
    # Who contests how much of the city. Nomination lists are public before
    # polling day; for a target already held the roster stands in.
    # ⛔ THE REACH FALLBACK WAS SILENT, AND IT IS THE SPLIT WEIGHT.
    #
    # `_ward_reach` at an unheld target returns {} — `metro_file` has no result
    # file to read — so this quietly used the FITTING year's geography and said
    # nothing. Reach sets `arrival_group_spec`'s weights and matches entrant
    # comparators, so carrying it forward is a real assumption, not plumbing.
    #
    # It is kept, not replaced: the owner's instruction is to fall back to
    # previous elections with a declared judgement on direction, and
    # `levels.projected_contestation` measures that direction (median party
    # expands 0.220 of the remaining distance, but only 65.5% expand at all —
    # so applying the median to everyone over-states a third of the roster).
    # What changes is that the fallback now ANNOUNCES itself and can be
    # overridden per party in the judgement file.
    reach = _ward_reach(city.code, target.year)
    reach_source = f"{target.year} ward ballot"
    if not reach:
        reach = _ward_reach(city.code, year)
        reach_source = f"{year} ward ballot, carried forward unchanged"
    declared_reach = (declared_roster(city, target) or {}).get("reach") or {}
    if declared_reach:
        reach = {**reach, **declared_reach}
        reach_source += f"; {len(declared_reach)} declared in judgements"
    print(f"  reach for {target.year}: {reach_source}")
    arrivals, seed_notes = arrival_rules(
        newcomers, lineage, rates_matrix, universe_fitted, cats, entrant_hist,
        splinter_record(city, target.year), registered, contestation=reach,
        splinter_home=home_splinter_record(before_year=home_cutoff),
        city_code=city.code,
        pooled_splits=pooled_splinter_record(target.year),
        # The arrival TOTAL, from city-years strictly before the target. It is
        # the regular quantity where an individual arrival's size is not.
        # ⚠️ For 2026 the value passed is 2.1701% over 22 rows, and it is
        # measured over a population wider than the one it is spent on --
        # see `_arrival_total_prior`. Do not quote a figure here; it decayed
        # once already.
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
            # ⛔ NOT WIDENED, AND THIS IS THE ONE SITE THAT IS NOT. It feeds
            # `dirichlet_alpha` — JUDGEMENT-CALLS §B's "dominant width lever,
            # 83-98% of drawn variance for every party except ANC and DA".
            #
            # Adding 2000/2006 here took the sample from 24 metro-years to 33
            # and moved alpha from [15.61, 22.58, 21.51, 21.94] to
            # [12.73, 14.54, 16.15, 22.42] — a WIDENING of the published
            # forecast on three of four pools. That looked like more evidence
            # and it is double-counting. §1.184:
            #
            #   * Fit alpha per era and the POOLED value sits BELOW BOTH eras'
            #     own (Black African 45.30 early, 15.61 late, 12.73 pooled).
            #     Genuine dispersion lands between them; below both is the
            #     signature of a level shift read as scatter.
            #   * The level shift is a TREND, not noise. Johannesburg's Black
            #     African pool: ANC+EFF+ActionSA is 87.9/89.9/90.7/89.9/87.7%
            #     across 2000-2021 — flat to 3 points over 25 years — while the
            #     ANC alone goes 90.7 -> 53.5. A steady directional transfer
            #     inside the pool, -18.2 then -19.0 points a cycle.
            #   * And it is measured in SHARE space while turnout moves under
            #     it. In votes per REGISTERED voter the same bloc falls
            #     46.1% -> 31.9%: about a third left the electorate rather than
            #     switching. The model already has per-pool turnout bands for
            #     that, and arrivals for the new parties.
            #
            # So three mechanisms the model handles deliberately elsewhere were
            # being counted a second time here as unpredictability. The other
            # three sites keep the fallback; this one does not.
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
            # ⛔ TRANSITIONS OFFERED vs USED, PER RECORD. Batch plan R4, risk
            # item 5: `HELD_BACK_OFF=1` is one env var from being load-bearing
            # on the arrival record, because `_npe_citywide_for` returns `{}`
            # for a quarantined metro-year and every caller guards on empty —
            # so a held-back metro is silently ABSENT rather than refused.
            # `unavailable` is that count, per record, and it was invisible.
            #
            # ⚠️ EMITTED, NOT PRINTED, AND THAT IS THE WHOLE POINT: the specs
            # are NOT in git, so after an emit-measure-restore cycle a number's
            # provenance exists nowhere at all. A print during an emit is
            # scrollback, and the emit is the one operation nobody re-runs.
            # `fallback` counts the reads the 2000/2006 widening (entry 4) made
            # possible; at target 2026 it is 9 of 40 offered, with 7
            # unavailable — the seven metros held back at lge2000. §1.209.
            "transition_ledger": {k: dict(v) for k, v in
                                  sorted(_TRANSITION_LEDGER.items())},
            # The seeded arrival mass as a fraction of this city's electorate,
            # so "the arrival machinery is on at this target" is a NUMBER in the
            # artefact rather than an inference from a non-empty `seeds` dict.
            # Zero with a non-empty roster means the seeds are all below 1e-9;
            # zero with an empty one means the mechanism could not be built.
            "seeded_arrival_mass": float(
                sum(v for v in seeds.values() if v > 0.0)),
            "seed_notes": seed_notes,
            "entrant_record": [[float(share), float(reach)]
                               for share, reach in entrant_hist],
            # Arrivals as a GROUP, drawn once and split by ward reach, rather
            # than thirty independent seeds and one generic slot. None where
            # there is no nomination list to split between.
            "arrival_group": arrival_group_spec(
                target.year, reach, sorted(arrivals))
            if roster_source in ("published", "declared") else None,
            "provenance": (f"{ctx['provenance']}; pools sized by {roll_note}; "
                           f"roster {roster_source}; reach {reach_source}"),
            "pool_shares_at_target": target_shares.tolist(),
            "registration_series": {y: v.tolist() for y, v in series.items()},
            "categories": cats,
            "no_measured_vector": inherited,
            # ⛔ `_nnls`'s docstring promises the caller "must SAY SO rather
            # than quietly using the clipped value — see the `unidentified`
            # list". That list was computed, stored, and read by NOTHING: no
            # print, no field, no test. The clip was silent, which the same
            # docstring calls "worse". Emitted now, so a clipped corner is
            # visible in the artefact a reader actually opens. §L9.
            "rates_on_a_bound": list(
                getattr(ctx.get("counts"), "unidentified", []) or []),
            # Parties with NO FITTED POOL VECTOR and no declared lineage that
            # nevertheless hold a preceding NATIONAL vote — candidates for a
            # split nobody has declared. Emitted, not printed. §L8.
            #
            # ⚠️ NOT "sized as arrivals from nothing". These parties are by
            # definition ABOVE the floor, and `newcomers` filters on
            # `baseline <= 0`, so the flagged set and the seeded set are
            # DISJOINT BY CONSTRUCTION. A flagged party keeps its baseline
            # LEVEL and is given the city's own pool composition as its vector.
            # The defect this points at is therefore the VECTOR, not the size —
            # smaller than the first write-up claimed, and `support` cannot
            # reach these parties at all.
            "unclassified_with_national_record": {
                p: round(v, 6) for p, v in sorted(unclassified.items(),
                                                  key=lambda kv: -kv[1])},
            "judgement_file": str(template)}


# --------------------------------------------------------------------------
# admission: does a dimension earn its place?
# --------------------------------------------------------------------------
def _required_setting(raw: dict, key: str) -> float:
    """A top-level `dimensions.toml` number, or a refusal naming the file."""
    if key not in raw:
        raise SystemExit(
            f"`{key}` is missing from {CONFIG}.\n"
            f"\n"
            f"  There is deliberately NO typed fallback: a default here would "
            f"duplicate the config in code and take over in silence the moment "
            f"the key were renamed. Unlike the `[gate]` settings this one "
            f"REACHES THE EMITTED SPEC, through the covariate extrapolation.")
    return float(raw[key])


def _required_gate(cfg: Config, key: str):
    """A `[gate]` setting, or a refusal naming the file it should be in.

    ⛔ THE TYPED FALLBACK IS THE DEFECT, NOT THE MISSING KEY. `cfg.gate.get(key,
    <literal>)` duplicates `config/dimensions.toml` in code, and the copy takes
    over **silently** if the TOML block is renamed or dropped — which is how a
    party cast typed into `pools.py` comes to decide a gate nobody thinks is
    typed. The owner ruled that class out on 2026-08-30: the cast changes every
    cycle and a typed default cannot.

    **Both instances are fixed, and two is the whole population** — a grep for
    `cfg.<section>.get(` in this module returns exactly `gate_parties` and
    `min_oos_gain`, both here. Fixing one of a two-instance defect is worse than
    fixing neither, because it removes the symptom that would have found the
    other.

    ⚠️ The fix was written and REVERTED once, on 2026-08-31: it is executable
    code, so it moved `pools_sha` and every emitted spec reported STALE
    immediately. That was the artefact key doing its job, and it is why this
    landed in a batched re-emit window (`POOLS-REEMIT-QUEUE.md` entry 6) rather
    than when it was noticed.
    """
    if key not in cfg.gate:
        raise SystemExit(
            f"`[gate] {key}` is missing from {CONFIG}.\n"
            f"\n"
            f"  There is deliberately NO typed fallback: a default here would "
            f"duplicate the config in code and take over in silence the moment "
            f"the block were renamed. Declare it in the TOML, which is the one "
            f"place it belongs and the one place that moves `config_sha` when "
            f"it changes.")
    return cfg.gate[key]


def gate(cfg: Config, year: str = "2021",
         slugs: tuple[str, ...] = ("joburg", "tshwane")) -> dict[str, dict]:
    """Fit on one city, predict another, and see whether a tilt helped.

    In-sample gain is not evidence — every dimension we hold shows some, mostly
    by re-describing the base. Only a dimension that transfers is real.
    """
    tested = [d for d in cfg.dimensions if d.role == "tilt"]
    parties = list(_required_gate(cfg, "gate_parties"))
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
            "admit": mean_gain >= float(_required_gate(cfg, "min_oos_gain")),
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
