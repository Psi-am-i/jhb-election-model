"""Run the pre-freeze arms of ``prereg/2026-10-23-prefreeze-arms.md`` and check them.

    .venv/bin/python rounds/2026-10-23-out-of-sample/prefreeze/run_arms.py run --arm B --out DIR
    .venv/bin/python rounds/.../run_arms.py run --arm A7 --out DIR --draws 200   # a smoke run
    .venv/bin/python rounds/.../run_arms.py check --out DIR      # C1-C3, PASS/FAIL each
    .venv/bin/python rounds/.../run_arms.py baseline --out DIR   # C4: B's headline figures
    .venv/bin/python rounds/.../run_arms.py summary --out DIR    # the amendment's tables

Johannesburg 2026, seed 20261104, 5,000 draws (``--draws`` overrides). One arm
per invocation: the in-process patches below are installed for the duration of
one ``run_model`` call and removed after it, and a fresh process keeps one
arm's state out of the next. ``DIR`` must lie outside ``data/``
(``arms.check_out``); nothing here writes under ``data/``, edits
``montecarlo.py`` or ``pools.py``, or re-emits anything.

THE ARMS (prereg table, and its amendment):

    B    the tree as it is.
    BF   B with the amendment's definition of a real fit applied to fold 1:
         a fold-1 row that is not a real fit (``fold.fit_status``: base
         citywide share <= 0.001, no target votes, or unseen) is removed
         before ``run_model`` sees the parameters, so that party takes
         ``gamma_recent.csv``, then 1.0 -- the order ``run_model`` intends.
    A7t  B with ``turnout.csv`` rebuilt by ``turnout.py --kappa-bye 0`` (no
         by-election turnout tilt); ``w_bye`` unchanged.
    A7   A7t, with every ``byelection_*`` file removed and ``w_bye = 0``.
    G2   γ from fold 2 (``fold2_parameters.csv``), real fits only, as BF.
    GP   γ from folds 1 and 2 fitted together (``fold.py --pool 1,2``), the
         sums of every fold whose row is a real fit; a party no fold fitted
         takes ``gamma_recent``, then 1.0.

A7 and A7t read a full copy of ``data/processed/`` at ``DIR/<arm>/processed``
(copies, not links) with their own ``turnout.csv``; every other arm reads the
live directory. γ is switched in process: ``montecarlo.load_parameters`` is
replaced, for the call, by a function that returns the arm's parameters when
the fold-1 file is asked for (``montecarlo.gamma_fold_for`` names fold 1 for
2026; ``GAMMA_FOLD`` is not edited, because ``montecarlo.py``'s syntax tree is
in ``width_record_key``). ``run_model``'s own ``gamma_source`` therefore says
``fold1`` for a G2 or GP party; the true source is recorded here.

WHAT A RUN WRITES, under ``DIR/<arm>/``:

* ``joburg-2026/``: ``arms.run_city_year``'s ``arrays.npz``, ``meta.json`` and
  ``trace/`` (so its width-record check, its calibration refusal and
  ``check_pairing``'s fields apply), plus ``extra.npz`` (``council_sizes``,
  ``thresholds``) and ``seat_draws.csv`` in ``montecarlo.py``'s format (the
  13 parties with most mean seats) for ``coalitions.py --draws-file``;
* ``meta.json``: per ballot and party, the γ drawn (read from the arrays
  ``solve_and_predict`` was given, by a recording wrapper) and its source
  (``fold1``, ``fold1 placeholder (<status>)``, ``fold2``, ``pooled 1+2``,
  ``recent``, ``default 1.0``), each fold's ``fit_status``, the parties that
  took ``recent`` or the default (the fallback list), whether every draw used
  the same γ, ``w_bye``, the by-election weights and the by-election files
  present;
* ``gamma/gamma_pooled_fold1-2.csv``: the fit statuses (and GP's γ).
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import csv
import hashlib
import io
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

import arms             # noqa: E402
import cityconfig       # noqa: E402
import fold             # noqa: E402
import montecarlo as M  # noqa: E402

CITY, YEAR = "joburg", "2026"
SEED = 20261104
DRAWS = 5000
ARM_ORDER = ("B", "BF", "A7t", "A7", "G2", "GP")
# The `--set` overrides each arm applies (prereg: A7 is `w_bye = 0`).
SETS: dict[str, dict] = {"B": {}, "BF": {}, "A7t": {}, "A7": {"w_bye": 0.0},
                         "G2": {}, "GP": {}}
# The arms that read their own copy of data/processed.
OWN_PROCESSED = {"A7t", "A7"}
# How each arm's γ parameters are built (see `arm_parameters`).
GAMMA_MODE = {"B": "fold1 as written", "A7t": "fold1 as written",
              "A7": "fold1 as written", "BF": "fold1 real fits",
              "G2": "fold2 real fits", "GP": "pooled 1+2 real fits"}
# Who each arm is compared with in the report (amendment: G2 and GP against BF
# as well as B).
COMPARE_WITH = {"BF": ["B"], "A7t": ["B"], "A7": ["B"],
                "G2": ["BF", "B"], "GP": ["BF", "B"]}
# Each arm's input and its evidence status, for the report's opening line.
EVIDENCE = {
    "B": "The tree as published. No backtest tests the 2026 γ or the by-elections.",
    "BF": "Fold-1 placeholder rows removed so gamma_recent applies. Not tested by any backtest.",
    "A7t": "By-election turnout tilt off (κ = 0). No backtest target has a by-election.",
    "A7": "By-elections off (w_bye = 0, no turnout tilt, no by-election files). No backtest target has a by-election.",
    "G2": "γ from fold 2 (2019 → 2021). The 2026 γ is not tested by any backtest.",
    "GP": "γ from folds 1 and 2 pooled. The 2026 γ is not tested by any backtest.",
}
# The prereg's count of VDs carrying a by-election turnout tilt in the live
# turnout.csv ("79 of 825 VDs"), which C2 confirms.
PREREG_TILTED_VDS = 79
# Implied-tilt tolerance: turnout.csv carries five decimals, which bounds the
# implied tilt's rounding error near 1e-4 at Johannesburg's turnouts.
TILT_TOL = 1e-4
NO_BACKTEST = "No backtest: neither input is tested by any backtest."


def _arm_check(arm: str) -> None:
    if arm not in ARM_ORDER:
        raise SystemExit(f"unknown arm {arm!r}; the arms are {list(ARM_ORDER)}")


def register_arms() -> None:
    """Make these arms known to ``arms`` in process: ``fresh_scenario`` reads
    ``arms.ARMS`` for the overrides, and ``run_city_year``/``check_pairing``
    apply the width check, the calibration refusal and the variant check to
    ``arms.UNIVERSAL_ARMS`` (every arm here draws with the shipped universal
    law). Nothing in ``src/arms.py`` changes."""
    for arm, sets in SETS.items():
        if arm in arms.ARMS and arms.ARMS[arm] != sets:
            raise SystemExit(f"arm {arm} already means {arms.ARMS[arm]} in arms.py")
        arms.ARMS[arm] = sets
    arms.UNIVERSAL_ARMS = frozenset(arms.UNIVERSAL_ARMS | set(SETS))


def _live_processed() -> Path:
    cityconfig.use(CITY)
    return cityconfig.use_target(YEAR).processed


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def _quiet(fn, *args, log: Path | None = None):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        got = fn(*args)
    if log is not None:
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(buf.getvalue())
    return got


# --------------------------------------------------------------------------
# inputs: the processed copy and the γ parameters
# --------------------------------------------------------------------------

def build_processed(arm: str, arm_dir: Path) -> Path:
    """A7/A7t: a full copy of the live processed directory, with
    ``turnout.csv`` rebuilt at κ = 0 and, for A7, every ``byelection_*``
    file removed. Returns its path."""
    import turnout
    dest = arm_dir / "processed"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(_live_processed(), dest, symlinks=False)
    if arm == "A7":
        for f in sorted(dest.glob("byelection_*")):
            f.unlink()
    (dest / "turnout.csv").unlink()
    _quiet(turnout.main, ["--kappa-bye", "0", "--out", str(dest / "turnout.csv"),
                          "--city", CITY, "--target", YEAR],
           log=arm_dir / "turnout_kappa0.log")
    return dest


def fit_statuses(arm_dir: Path) -> dict:
    """``fold.py --pool 1,2`` into ``arm_dir/gamma``, read back: per ballot and
    party, each fold's ``fit_status``, the folds that contributed and the
    pooled γ."""
    gdir = arm_dir / "gamma"
    _quiet(fold.main, ["--pool", "1,2", "--out", str(gdir), "--city", CITY],
           log=gdir / "pool.log")
    return fold.read_pooled(fold.pooled_path(gdir, [1, 2]))


def real_fit_rows(params: dict, pooled: dict, fold_n: int) -> dict:
    """``params`` (``fold.load_parameters``' shape) with every γ row removed
    that ``fit_status`` does not call a real fit in fold ``fold_n``. A row
    whose party the refit does not know is removed too, and reported by
    ``check``'s C3 (the refit must equal the file)."""
    out = copy.deepcopy(params)
    for ballot, values in out.items():
        status = pooled.get(ballot, {})
        values["gamma"] = {
            p: g for p, g in values["gamma"].items()
            if (status.get(p) or {}).get("status", {}).get(fold_n) == fold.FITTED}
    return out


def pooled_rows(pooled: dict) -> dict:
    """The pooled fit as parameters: a γ row for every party some fold fitted
    (γ as written, four decimals, as every fold file carries it)."""
    return {ballot: {"theta": {}, "theta_raw": {},
                     "gamma": {p: r["gamma"] for p, r in rows.items()
                               if r["gamma"] is not None}}
            for ballot, rows in pooled.items()}


def arm_parameters(arm: str, pooled: dict, city_processed: Path) -> dict:
    """The fold parameters ``run_model`` is handed for this arm."""
    fold1 = fold.load_parameters(city_processed / "fold1_parameters.csv")
    mode = GAMMA_MODE[arm]
    if mode == "fold1 as written":
        return fold1
    if mode == "fold1 real fits":
        return real_fit_rows(fold1, pooled, 1)
    if mode == "fold2 real fits":
        return real_fit_rows(
            fold.load_parameters(city_processed / "fold2_parameters.csv"), pooled, 2)
    return pooled_rows(pooled)


def gamma_label(arm: str, ballot: str, party: str, pooled: dict) -> str:
    """The source a fold-file γ row has in this arm."""
    mode = GAMMA_MODE[arm]
    row = pooled.get(ballot, {}).get(party) or {"status": {}, "contributing": []}
    if mode == "fold1 as written":
        st = row["status"].get(1, fold.UNFITTED_UNSEEN)
        return "fold1" if st == fold.FITTED else f"fold1 placeholder ({st})"
    if mode == "fold1 real fits":
        return "fold1"
    if mode == "fold2 real fits":
        return "fold2"
    return "pooled " + "+".join(str(f) for f in row["contributing"])


def expected_gamma(params: dict, recent: dict, universe, arm: str,
                   pooled: dict) -> dict:
    """``{ballot: {party: (γ, source)}}`` by ``run_model``'s own order
    (montecarlo.py, the γ block of ``run_model``): the fold row, then
    ``gamma_recent``, then 1.0."""
    out = {}
    for ballot in ("PR", "Ward"):
        out[ballot] = {}
        for p in universe:
            if p in params[ballot]["gamma"]:
                out[ballot][p] = (float(params[ballot]["gamma"][p]),
                                  gamma_label(arm, ballot, p, pooled))
            elif p in recent:
                out[ballot][p] = (float(recent[p]), "recent")
            else:
                out[ballot][p] = (1.0, "default 1.0")
    return out


def read_recent(processed: Path) -> dict:
    path = processed / "gamma_recent.csv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["party"]: float(r["gamma"]) for r in csv.DictReader(fh)}


# --------------------------------------------------------------------------
# the patches, for one run_model call
# --------------------------------------------------------------------------

class Recorder:
    """Wraps ``montecarlo.solve_and_predict`` and keeps the γ vector each
    ballot was given: the first PR and Ward calls, and how many later calls
    were given a different vector (expected 0)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.calls = 0
        self.first: list[np.ndarray] = []
        self.differing = 0

    def wrap(self, original):
        def solve_and_predict(dev, base_city, target, gamma, *a, **k):
            slot = self.calls % 2          # PR, then Ward, every draw
            if self.calls < 2:
                self.first.append(np.array(gamma, dtype=float, copy=True))
            elif not np.array_equal(gamma, self.first[slot]):
                self.differing += 1
            self.calls += 1
            return original(dev, base_city, target, gamma, *a, **k)
        return solve_and_predict


@contextlib.contextmanager
def patched(params: dict, recorder: Recorder | None, fold_n: int,
            counter: dict | None = None):
    """``montecarlo.load_parameters`` returns ``params`` for
    ``fold{fold_n}_parameters.csv`` (and the real file for any other), and
    ``solve_and_predict`` is recorded, for the duration of the block.
    ``counter["fold_loads"]`` counts the times the substitute was handed out,
    so a run can show the patch bound (``run_model`` looks the name up as a
    module global at call time)."""
    orig_load, orig_solve = M.load_parameters, M.solve_and_predict
    name = f"fold{fold_n}_parameters.csv"

    def load_parameters(path):
        if Path(path).name == name:
            if counter is not None:
                counter["fold_loads"] = counter.get("fold_loads", 0) + 1
            return copy.deepcopy(params)
        return orig_load(path)

    M.load_parameters = load_parameters
    if recorder is not None:
        M.solve_and_predict = recorder.wrap(orig_solve)
    try:
        yield
    finally:
        M.load_parameters, M.solve_and_predict = orig_load, orig_solve


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------

def write_seat_draws(run, dest: Path) -> None:
    """``seat_draws.csv`` as ``montecarlo.py`` writes it: draw, threshold,
    council size and the 13 parties with most mean seats."""
    universe = list(run.universe)
    seats = np.array([[s.get(p, 0) for p in universe] for s in run.seat_draws])
    top = [universe[j] for j in np.argsort(-seats.mean(axis=0), kind="stable")[:13]]
    with (dest / "seat_draws.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "threshold", "council_size"] + top)
        for i, s in enumerate(run.seat_draws):
            w.writerow([i, int(run.thresholds[i]), int(run.council_sizes[i])]
                       + [int(s.get(p, 0)) for p in top])


def run_arm(arm: str, out: Path, draws: int, seed: int) -> dict:
    _arm_check(arm)
    os.chdir(REPO)
    out = arms.check_out(out)
    register_arms()
    # NOT `arms.check_tree`: it belongs to the 2026-10-12 round, whose census
    # hold (`pools.IDENTIFICATION_REACH`) this tree no longer carries, and it
    # refuses every non-C0 arm here for that reason. The pairing these arms
    # need is `check_pairing`'s (one commit, clean src/, one set of specs and
    # one width-record key), applied by `check`.
    live = _live_processed()
    city_processed = cityconfig.active().processed
    arm_dir = out / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    processed = build_processed(arm, arm_dir) if arm in OWN_PROCESSED else None
    read_from = processed or live
    pooled = fit_statuses(arm_dir)
    target = cityconfig.use_target(YEAR)
    fold_n = M.gamma_fold_for(target)
    if fold_n != 1:
        raise SystemExit(f"run_model reads fold {fold_n} for {YEAR}; the "
                         f"prereg's baseline is fold 1")
    params = arm_parameters(arm, pooled, city_processed)
    recorder = Recorder()
    state: dict = {}
    counter = {"fold_loads": 0}

    def run_model(target, scenario, data_dir, **kw):
        if processed is not None:
            kw["processed"] = processed
        full = kw.get("stop_after") is None
        if full:
            recorder.reset()
        with patched(params, recorder if full else None, fold_n, counter):
            got = M.run_model(target, scenario, data_dir, **kw)
        if full:
            state["run"] = got
        return got

    meta_cy = arms.run_city_year(arm, CITY, YEAR, out, draws=draws, seed=seed,
                                 run_model=run_model)
    run = state["run"]
    dest = out / arm / f"{CITY}-{YEAR}"
    np.savez_compressed(dest / "extra.npz",
                        council_sizes=np.asarray(run.council_sizes, dtype=np.int64),
                        thresholds=np.asarray(run.thresholds, dtype=np.int64))
    write_seat_draws(run, dest)

    universe = list(run.universe)
    recent = read_recent(read_from)
    want = expected_gamma(params, recent, universe, arm, pooled)
    gamma: dict = {}
    fallback: dict = {}
    for k, ballot in enumerate(("PR", "Ward")):
        drawn_vec = recorder.first[k]
        gamma[ballot] = {}
        for p in universe:
            g_want, source = want[ballot][p]
            drawn = float(drawn_vec[run.index[p]])
            row = pooled.get(ballot, {}).get(p) or {"status": {}, "contributing": []}
            gamma[ballot][p] = {
                "drawn": drawn, "source": source, "expected": g_want,
                "fold1": row["status"].get(1, fold.UNFITTED_UNSEEN),
                "fold2": row["status"].get(2, fold.UNFITTED_UNSEEN),
                "pooled": row.get("gamma"),
                "run_model_label": run.gamma_source.get(p)}
        fallback[ballot] = sorted(p for p in universe
                                  if want[ballot][p][1] in ("recent", "default 1.0"))
    sc = run.scenario
    meta = {
        "arm": arm, "prereg": "prereg/2026-10-23-prefreeze-arms.md",
        "evidence": EVIDENCE[arm], "gamma_mode": GAMMA_MODE[arm],
        "sets": SETS[arm], "draws": draws, "seed": seed,
        "processed": str(read_from),
        "turnout_sha": _sha(read_from / "turnout.csv"),
        "byelection_files": sorted(f.name for f in read_from.glob("byelection_*")),
        "w_bye": sc.get("w_bye"),
        "bye_weight": sc.get("_bye_weight"),
        "seeded": sorted(p for p, v in (sc.get("pool_seeds") or {}).items() if v > 0),
        "poll_levels": sorted(sc.get("poll_levels") or {}),
        "gamma": gamma, "fallback": fallback,
        "solve_calls": recorder.calls,
        "patched_fold_loads": counter["fold_loads"],
        "solve_calls_with_other_gamma": recorder.differing,
        "city_year_meta": str(dest / "meta.json"),
        "git": meta_cy["git"],
    }
    (arm_dir / "meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True,
                                                  default=float))
    return meta


# --------------------------------------------------------------------------
# reading back
# --------------------------------------------------------------------------

def load(out: Path, arm: str) -> dict | None:
    """An arm's metas and arrays, or None where it has not run."""
    d = Path(out) / arm
    cy = d / f"{CITY}-{YEAR}"
    if not (d / "meta.json").exists() or not (cy / "meta.json").exists():
        return None
    a = np.load(cy / "arrays.npz")
    e = np.load(cy / "extra.npz")
    return {"meta": json.loads((d / "meta.json").read_text()),
            "cy": json.loads((cy / "meta.json").read_text()),
            "arrays": {k: a[k] for k in a.files},
            "extra": {k: e[k] for k in e.files},
            "trace": cy / "trace"}


def _trace(run: dict, stage: str) -> dict:
    return json.loads((run["trace"] / f"{stage}.json").read_text())


def _result(name: str, ok: bool, detail: str) -> bool:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    return ok


def _turnout(path: Path) -> dict:
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return {r["VD_Number"]: r for r in csv.DictReader(fh)}


def implied_tilt(rows: dict, base_npe: str, year: str) -> dict:
    """Per VD, projected turnout over (base-NPE turnout × λ̂): the by-election
    tilt ``turnout.py`` multiplied in, read back from the file. VDs at the
    1.0 cap are left out."""
    out = {}
    for vd, r in rows.items():
        proj = float(r[f"turnout_{year}_projected"])
        denom = float(r[f"turnout_{base_npe}"]) * float(r["lambda_hat"])
        if proj < 1.0 and denom > 0:
            out[vd] = proj / denom
    return out


def check(out: Path) -> int:
    """C1-C3 (prereg, blocking), PASS/FAIL per condition."""
    os.chdir(REPO)
    out = arms.check_out(out)
    register_arms()
    live = _live_processed()
    target = cityconfig.use_target(YEAR)
    runs = {a: load(out, a) for a in ARM_ORDER}
    ok = True

    print("C1 pairing (arms.check_pairing against B; G2 and GP also against BF)")
    if runs["B"] is None:
        ok = _result("C1", False, "arm B has not run")
    for arm in ARM_ORDER[1:]:
        if runs[arm] is None:
            print(f"  ----  {arm}: not run")
            continue
        for other in COMPARE_WITH[arm]:
            if runs[other] is None:
                ok = _result(f"C1 {arm} vs {other}", False, f"{other} has not run") and ok
                continue
            try:
                arms.check_pairing(arm, runs[arm]["cy"], other, runs[other]["cy"])
                ok = _result(f"C1 {arm} vs {other}", True,
                             "seed, draws, commit, specs, width key and variant agree") and ok
            except SystemExit as exc:
                ok = _result(f"C1 {arm} vs {other}", False, str(exc)) and ok

    print("C2 the switch took")
    live_t = _turnout(live / "turnout.csv")
    base_npe = target.previous_npe
    for arm in ("A7t", "A7"):
        r = runs[arm]
        if r is None:
            print(f"  ----  {arm}: not run")
            continue
        m = r["meta"]
        used = Path(m["processed"])
        t = _turnout(used / "turnout.csv")
        tilt = implied_tilt(t, base_npe, YEAR)
        ratio = {vd: float(live_t[vd][f"turnout_{YEAR}_projected"])
                 / float(t[vd][f"turnout_{YEAR}_projected"])
                 for vd in live_t if vd in t and float(t[vd][f"turnout_{YEAR}_projected"]) > 0}
        tilted = sorted(vd for vd, x in ratio.items() if abs(x - 1) > TILT_TOL)
        worst = max(abs(x - 1) for x in tilt.values())
        worst_tilted = max((abs(tilt[vd] - 1) for vd in tilted if vd in tilt), default=0.0)
        ok = _result(f"C2 {arm} turnout", set(t) == set(live_t)
                     and len(tilted) == PREREG_TILTED_VDS and worst < TILT_TOL,
                     f"{len(tilted)} VDs differ from the live turnout (prereg "
                     f"{PREREG_TILTED_VDS}); implied tilt in the run's turnout, "
                     f"largest |x-1| {worst:.2e} over all {len(tilt)} VDs, "
                     f"{worst_tilted:.2e} over those {len(tilted)} "
                     f"(tolerance {TILT_TOL}); file {used / 'turnout.csv'}") and ok
    r = runs["A7"]
    if r is not None:
        m = r["meta"]
        weights = {p: (v or {}).get("weight") for p, v in (m["bye_weight"] or {}).items()}
        ok = _result("C2 A7 by-election weights",
                     m["w_bye"] == 0 and not m["byelection_files"]
                     and all(w == 0 for w in weights.values()),
                     f"w_bye {m['w_bye']}, by-election files in the run's processed "
                     f"{m['byelection_files'] or 'none'}, weights recorded "
                     f"{weights or 'none (no party has evidence)'}") and ok
        for arm in ("B", "A7"):
            if runs[arm] is None:
                continue
            spine = _trace(runs[arm], "20_spine")["level"]
            before = _trace(runs[arm], "30_centres")["before_shrink"]
            other = set(runs[arm]["meta"]["seeded"]) | set(runs[arm]["meta"]["poll_levels"])
            on = [p for p in before if p in spine and p not in other]
            off = sorted(p for p in on if abs(before[p] - spine[p]) > 1e-12)
            routed = sorted(p for p in before if p not in on)
            if arm == "A7":
                ok = _result("C2 A7 levels", not off and len(on) > 0,
                             f"{len(on)} spine-route parties, centre before the shrink "
                             f"equals the spine level for {len(on) - len(off)}; off: "
                             f"{off or 'none'}; not on the spine route (seeded, poll "
                             f"or θ-mode, not compared): {routed or 'none'}") and ok
            else:
                print(f"  info  B levels (the detector sees): {len(off)} of {len(on)} "
                      f"spine-route parties sit off their spine level in B: {off}")
    for arm in ("B", "BF", "G2", "GP", "A7t", "A7"):
        r = runs[arm]
        if r is None:
            continue
        m = r["meta"]
        bad = [f"{b}:{p} drawn {v['drawn']} expected {v['expected']} ({v['source']})"
               for b, rows in m["gamma"].items() for p, v in rows.items()
               if v["drawn"] != v["expected"]]
        own = sum(1 for rows in m["gamma"].values() for v in rows.values()
                  if v["source"] not in ("recent", "default 1.0"))
        name = (f"C2 {arm} γ drawn equals the arm's fit" if arm in ("G2", "GP")
                else f"C2 {arm} γ drawn equals its source (info for the prereg)")
        ok = _result(name, not bad and m["solve_calls_with_other_gamma"] == 0
                     and m["solve_calls"] > 0 and m.get("patched_fold_loads", 0) >= 1,
                     f"patched loader handed out {m.get('patched_fold_loads', 0)} "
                     f"times; {own} party-ballots from {m['gamma_mode']}, fallback "
                     f"(recent/default) PR {len(m['fallback']['PR'])}, Ward "
                     f"{len(m['fallback']['Ward'])}; {m['solve_calls']} solve calls, "
                     f"{m['solve_calls_with_other_gamma']} with another γ; "
                     f"mismatches: {bad[:5] or 'none'}") and ok
    if runs["G2"] is not None:
        # The arm's fit is the fold-2 FILE; is the file what the fold code fits?
        f2 = fold.load_parameters(cityconfig.active().processed / "fold2_parameters.csv")
        pooled2_dir = out / "_checks" / "pool2"
        _quiet(fold.main, ["--pool", "2", "--out", str(pooled2_dir), "--city", CITY])
        p2 = fold.read_pooled(fold.pooled_path(pooled2_dir, [2]))
        diff = [f"{b}:{p}" for b in p2 for p, r in p2[b].items()
                if r["gamma"] is not None and abs(r["gamma"] - f2[b]["gamma"].get(p, np.nan)) > 0]
        _result("C2 G2 (extra) fold 2's pooled-alone γ equals fold2_parameters.csv",
                not diff, f"real-fit rows differing: {diff or 'none'}")

    print("C3 vintage")
    chk = out / "_checks"
    import turnout
    t25 = chk / "turnout_kappa025.csv"
    _quiet(turnout.main, ["--kappa-bye", "0.25", "--out", str(t25), "--city", CITY,
                          "--target", YEAR], log=chk / "turnout_kappa025.log")
    same = t25.read_bytes() == (live / "turnout.csv").read_bytes()
    c3 = same
    ok = _result("C3 turnout.py --kappa-bye 0.25 equals live turnout.csv", same,
                 f"{t25} against {live / 'turnout.csv'}, byte for byte") and ok
    f1 = chk / "fold"
    _quiet(fold.main, ["--fold", "1", "--out", str(f1), "--city", CITY],
           log=chk / "fold1.log")
    live_f1 = cityconfig.active().processed / "fold1_parameters.csv"
    same = (f1 / "fold1_parameters.csv").read_bytes() == live_f1.read_bytes()
    c3 = c3 and same
    ok = _result("C3 fold-1 refit equals fold1_parameters.csv", same,
                 f"{f1 / 'fold1_parameters.csv'} against {live_f1}, byte for byte") and ok
    if not c3:
        print("  If a C3 line failed, the arm it affects reads scratch-built files "
              "in both its baseline and its own run (prereg C3), and the report "
              "says the baseline differs from the site. This driver does not do "
              "that switch: stop and take it to the owner.")
    print(f"\n{'ALL PASS' if ok else 'SOME FAILED'}")
    return 0 if ok else 1


# --------------------------------------------------------------------------
# C4 and the summary
# --------------------------------------------------------------------------

def figures(run: dict) -> dict:
    """Per party: mean, median, 5th and 95th percentile seats, mean list share
    (percentage points), mean wards won, P(largest alone) and P(tied largest)
    (``reweight.largest_party``, the site's one definition), P(majority alone)
    against each draw's threshold; and each ward's favourite."""
    import reweight
    a = run["arrays"]
    cols = run["cy"]["seat_cols"]
    sd, ww, pr = a["seat_draws"], a["ward_winner_draws"], a["pr_share_draws"]
    thr = run["extra"]["thresholds"]
    lp = reweight.largest_party(sd, cols)
    parties = {}
    for j, p in enumerate(cols):
        s = sd[:, j]
        parties[p] = {"mean": float(s.mean()), "median": float(np.median(s)),
                      "p5": float(np.percentile(s, 5)), "p95": float(np.percentile(s, 95)),
                      "list_share": 100 * float(pr[:, j].mean()),
                      "wards": float((ww == j).sum(1).mean()),
                      "largest_alone": float(lp["outright"][p]),
                      "majority": float((s >= thr).mean())}
    wards = {}
    for w in range(ww.shape[1]):
        v, c = np.unique(ww[:, w], return_counts=True)
        o = np.argsort(-c, kind="stable")
        wards[str(w + 1)] = {"fav": cols[v[o[0]]], "p": float(c[o[0]] / ww.shape[0])}
    return {"parties": parties, "wards": wards, "tied": float(lp["tied"])}


def baseline(out: Path) -> int:
    """C4: B's P(largest alone) and median seats per party, to set beside the
    live site. Not a standard of correctness (prereg C4)."""
    run = load(arms.check_out(out), "B")
    if run is None:
        raise SystemExit("arm B has not run")
    f = figures(run)
    rows = sorted(f["parties"].items(), key=lambda kv: -kv[1]["mean"])
    print(f"B, {run['cy']['draws']} draws, seed {run['cy']['seed']}, commit "
          f"{run['cy']['git']['commit'][:9]}")
    print(f"{'party':<12s} {'P(largest alone)':>17s} {'median seats':>13s}")
    for p, v in rows:
        if v["mean"] >= 0.5 or v["largest_alone"] > 0:
            print(f"{p:<12s} {100 * v['largest_alone']:>16.1f}% {v['median']:>13.0f}")
    print(f"{'tied':<12s} {100 * f['tied']:>16.1f}%")
    return 0


def _real(source: str) -> bool:
    return not (source.startswith("fold1 placeholder") or source == "default 1.0")


def gamma_table(runs: dict) -> list[dict]:
    """Per ballot and party, the γ drawn and its source in B, BF, G2 and GP,
    with each arm's change from its comparators classified: ``changed`` (a
    real fit in both, different values), ``appeared`` (a real fit in the arm
    only), ``lost`` (in the comparator only), ``moved`` (neither a real fit,
    different values). A real fit is any fold, pooled or recent value; a
    fold-1 placeholder row and the 1.0 default are not. Negative drawn γ is
    flagged."""
    arms_here = [a for a in ("B", "BF", "G2", "GP") if runs.get(a)]
    keys = sorted({(b, p) for a in arms_here
                   for b, rows in runs[a]["meta"]["gamma"].items() for p in rows})
    table = []
    for b, p in keys:
        row = {"ballot": b, "party": p}
        for a in arms_here:
            v = runs[a]["meta"]["gamma"][b].get(p)
            row[a] = None if v is None else {"gamma": v["drawn"], "source": v["source"],
                                             "negative": v["drawn"] < 0}
        for a in arms_here:
            for c in COMPARE_WITH.get(a, []):
                if c not in arms_here or row[a] is None or row[c] is None:
                    continue
                x, y = row[a], row[c]
                if x["gamma"] == y["gamma"]:
                    continue
                kind = ("changed" if _real(x["source"]) and _real(y["source"])
                        else "appeared" if _real(x["source"])
                        else "lost" if _real(y["source"]) else "moved")
                row[f"{a}_vs_{c}"] = kind
        if any(k.endswith(tuple(f"_vs_{c}" for c in ARM_ORDER)) for k in row) or \
                any(row[a] and row[a]["negative"] for a in arms_here):
            table.append(row)
    return table


def summary(out: Path) -> int:
    """``DIR/summary.json`` and ``DIR/summary.md``: per arm in the fixed order
    (B, BF, A7t, A7, G2, GP), its evidence status, the headline chances, per
    party the median-seat movement set beside B's 5-95% seat range, the ward
    favourites that change, and the γ table."""
    out = arms.check_out(out)
    runs = {a: load(out, a) for a in ARM_ORDER}
    if runs["B"] is None:
        raise SystemExit("arm B has not run")
    fig = {a: figures(r) for a, r in runs.items() if r}
    fb = fig["B"]["parties"]
    shown = [p for p, v in sorted(fb.items(), key=lambda kv: -kv[1]["mean"])
             if v["mean"] >= 0.5]
    res = {"backtest": NO_BACKTEST, "order": [a for a in ARM_ORDER if a in fig],
           "arms": {}, "gamma": gamma_table(runs)}
    md = ["# Pre-freeze arms, Johannesburg 2026", "", NO_BACKTEST, ""]
    for a in res["order"]:
        f = fig[a]
        entry = {"evidence": EVIDENCE[a], "tied": f["tied"], "parties": f["parties"],
                 "against": {}}
        md += [f"## {a}", "", EVIDENCE[a], "",
               "P(largest alone): " + ", ".join(
                   f"{p} {100 * f['parties'][p]['largest_alone']:.1f}%"
                   for p in shown[:4] if p in f["parties"])
               + f", tied {100 * f['tied']:.1f}%", ""]
        for c in ["B"] + [x for x in COMPARE_WITH.get(a, []) if x != "B"]:
            if a == c or c not in fig:
                continue
            fc = fig[c]
            changed = sorted((w for w in f["wards"]
                              if f["wards"][w]["fav"] != fc["wards"][w]["fav"]), key=int)
            moves = {p: {"median": f["parties"].get(p, {}).get("median", 0.0)
                         - fc["parties"].get(p, {}).get("median", 0.0),
                         "B_p5": fb[p]["p5"], "B_p95": fb[p]["p95"]} for p in shown}
            entry["against"][c] = {
                "median_seat_moves": moves,
                "ward_favourites_changed": [
                    {"ward": w, "from": fc["wards"][w]["fav"], "to": f["wards"][w]["fav"],
                     "p_from": fc["wards"][w]["p"], "p_to": f["wards"][w]["p"]}
                    for w in changed]}
            md += [f"### {a} against {c}", "",
                   f"Ward favourites that change: {len(changed)} of {len(f['wards'])}"
                   + (": " + ", ".join(f"ward {w} {fc['wards'][w]['fav']} → "
                                       f"{f['wards'][w]['fav']}" for w in changed)
                      if changed else ""), "",
                   "| party | median seats, " + c + " | median seats, " + a
                   + " | change | B's 5–95% seat range | P(largest alone), " + c
                   + " | P(largest alone), " + a + " |",
                   "|---|---|---|---|---|---|---|"]
            for p in shown:
                x, y = f["parties"].get(p, {}), fc["parties"].get(p, {})
                md.append(f"| {p} | {y.get('median', 0):.0f} | {x.get('median', 0):.0f} | "
                          f"{x.get('median', 0) - y.get('median', 0):+.0f} | "
                          f"{fb[p]['p5']:.0f}–{fb[p]['p95']:.0f} | "
                          f"{100 * y.get('largest_alone', 0):.1f}% | "
                          f"{100 * x.get('largest_alone', 0):.1f}% |")
            md.append("")
        res["arms"][a] = entry
    md += ["## γ drawn, by source (B, BF, G2, GP)", "",
           "Rows where any arm's γ differs from its comparator, or is negative. "
           "Kinds: changed (a real fit in both), appeared (a real fit in the arm "
           "only), lost (in the comparator only), moved (neither). A real fit is a "
           "fold, pooled or recent value; a fold-1 placeholder row and the 1.0 "
           "default are not. Negative γ is flagged, not bounded.", ""]
    cols = [a for a in ("B", "BF", "G2", "GP") if a in fig]
    md += ["| ballot | party | " + " | ".join(cols) + " | kinds |",
           "|---|---|" + "---|" * len(cols) + "---|"]
    for row in res["gamma"]:
        cells = []
        for a in cols:
            v = row.get(a)
            cells.append("—" if v is None else
                         f"{v['gamma']:.4f} ({v['source']})"
                         + (" **negative**" if v["negative"] else ""))
        kinds = ", ".join(f"{k.replace('_vs_', ' vs ')}: {v}" for k, v in row.items()
                          if "_vs_" in k)
        md.append(f"| {row['ballot']} | {row['party']} | " + " | ".join(cells)
                  + f" | {kinds} |")
    (out / "summary.json").write_text(json.dumps(res, indent=1, sort_keys=True))
    (out / "summary.md").write_text("\n".join(md) + "\n")
    print(f"wrote {out / 'summary.json'} and {out / 'summary.md'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--arm", required=True, choices=ARM_ORDER)
    r.add_argument("--out", required=True, type=Path)
    r.add_argument("--draws", type=int, default=DRAWS)
    r.add_argument("--seed", type=int, default=SEED)
    for name in ("check", "baseline", "summary"):
        s = sub.add_parser(name)
        s.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "run":
        meta = run_arm(a.arm, a.out, a.draws, a.seed)
        print(f"arm {a.arm}: {meta['draws']} draws, seed {meta['seed']}, wrote "
              f"{Path(a.out).resolve() / a.arm}")
        return 0
    return {"check": check, "baseline": baseline, "summary": summary}[a.cmd](a.out)


if __name__ == "__main__":
    raise SystemExit(main())
