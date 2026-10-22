"""Step 11 arm run: one city-year (or Johannesburg 2026) in one arm tree.

Run with the ARM TREE as the working directory and PYTHONHASHSEED=0:

    cd <arm tree> && PYTHONHASHSEED=0 .venv/bin/python <this file> \
        --mode panel --city capetown --year 2016 --draws 1000 --out <dir> [--set k=v]
    cd <arm tree> && PYTHONHASHSEED=0 .venv/bin/python <this file> \
        --mode forecast --city joburg --year 2026 --draws 5000 --out <dir> [--set k=v]
    cd <arm tree> && PYTHONHASHSEED=0 .venv/bin/python <this file> \
        --mode rule_a --city capetown --year 2016 --out <dir>

Imports the tree's own `src/` (sys.path[0] = cwd/src), so the code measured is
the arm's. Writes only under --out (outside every tree's data/processed).

panel:    `compare_history.run_city_year(city, year, draws, data/raw/elections,
          overrides, run_dir=<out>/trace)`, the seed `run_city_year` uses
          (seed=None, so DEFAULTS["seed"]). No history.json is written.
forecast: `montecarlo.run_model` with the scenario `load_scenario` builds after
          `apply_city`, as `montecarlo.main` builds it, `processed` = the
          target's own directory, `run_dir=<out>/trace`. No `main`, so no
          forecast artefact is written.
rule_a:   the arm's own audits/2026-10-07-prediction-restructure/backtest/rule_a.py,
          executed unchanged through runpy with its output path under --out.

Instruments (pre-registration §2), installed for the run and delegating
unchanged; neither changes a number:
  * the tie classifier, a wrapper around `montecarlo.allocate` accepting any
    keyword (arm A's `allocate` has no `lot`). Per call: available, quota =
    total // available + 1, whole-vote surplus, shortfall, ranking by
    (-surplus, -votes), the pair (ranked[shortfall-1], ranked[shortfall]).
    Class "lot": equal surplus and equal votes; "item2": equal surplus,
    unequal votes; otherwise untied (no pair when shortfall <= 0 or
    shortfall >= number of parties, as `tie_at_the_cut`).
  * a wrapper around `montecarlo.allocate_with_overhang` numbering the draws,
    so each `allocate` call inside `run_model` is assigned to its draw. Calls
    outside `run_model` (rule A's `seats_of`) are recorded separately.

Saved: <out>/result.json (run_city_year's dict, panel only), <out>/arrays.npz
(every drawn array the ModelRun carries, copied before `relabel_run`),
<out>/meta.json (universe, wards, pool names, guards, stale state, tie
classes, timing).
"""
from __future__ import annotations

import argparse
import inspect
import json
import os
import runpy
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--mode", choices=("panel", "forecast", "rule_a"), required=True)
ap.add_argument("--city", required=True)
ap.add_argument("--year", required=True)
ap.add_argument("--draws", type=int, default=1000)
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--set", action="append", default=[])
ap.add_argument("--move-aside", default=None,
                help="data/processed file to rename for the run and restore "
                     "after (P12's record-absent run)")
ap.add_argument("--module-set", action="append", default=[],
                help="MODULE.NAME=VALUE: set a module constant for the run "
                     "(P19's BYE_MIN_WEIGHT inertness check)")
args = ap.parse_args()
assert os.environ.get("PYTHONHASHSEED") == "0", "PYTHONHASHSEED must be 0"
out: Path = args.out
out.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# the instruments
# --------------------------------------------------------------------------
STATE = {"in_run": False, "draw": -1}
CALLS_IN_RUN: list[tuple[int, str]] = []      # (draw, class)
CALLS_OUTSIDE: list[dict] = []                # rule A's seat calls
_orig_allocate = M.allocate
_alloc_sig = inspect.signature(_orig_allocate)


def classify(combined, total_seats, independent_wards, no_pr_list_wards):
    available = total_seats - independent_wards - no_pr_list_wards
    if available <= 0 or not combined:
        return "untied", None
    total = sum(combined.values())
    quota = total // available + 1
    surplus = {p: v - (v // quota) * quota for p, v in combined.items()}
    shortfall = available - sum(v // quota for v in combined.values())
    if shortfall <= 0 or shortfall >= len(surplus):
        return "untied", None
    ranked = sorted(surplus, key=lambda p: (-surplus[p], -combined[p]))
    a, b = ranked[shortfall - 1], ranked[shortfall]
    if surplus[a] != surplus[b]:
        return "untied", None
    pair = {"inside": a, "outside": b, "surplus": int(surplus[a]),
            "votes": [int(combined[a]), int(combined[b])], "shortfall": shortfall}
    return ("lot" if combined[a] == combined[b] else "item2"), pair


def probe_allocate(*a, **kw):
    bound = _alloc_sig.bind(*a, **kw)
    bound.apply_defaults()
    ar = bound.arguments
    cls, pair = classify(ar["combined"], ar["total_seats"],
                         ar.get("independent_wards", 0) or 0,
                         ar.get("no_pr_list_wards", 0) or 0)
    if STATE["in_run"]:
        CALLS_IN_RUN.append((STATE["draw"], cls))
    else:
        CALLS_OUTSIDE.append({"class": cls, "pair": pair})
    return _orig_allocate(*a, **kw)


_orig_awo = M.allocate_with_overhang


def probe_awo(*a, **kw):
    if STATE["in_run"]:
        STATE["draw"] += 1
    return _orig_awo(*a, **kw)


M.allocate = probe_allocate
M.allocate_with_overhang = probe_awo

CAPTURED: dict = {}
_orig_run_model = M.run_model


def _seat_matrix(seat_draws, universe):
    cols = list(universe) + sorted({p for s in seat_draws for p in s} - set(universe))
    mat = np.array([[s.get(p, 0) for p in cols] for s in seat_draws], dtype=np.int64)
    return cols, mat


def probe_run_model(*a, **kw):
    STATE["in_run"], STATE["draw"] = True, -1
    t0 = time.time()
    try:
        run = _orig_run_model(*a, **kw)
    finally:
        STATE["in_run"] = False
    CAPTURED["seconds"] = time.time() - t0
    # COPIED HERE, before compare_history's relabel_run rewrites the run.
    cols, seats = _seat_matrix(run.seat_draws, run.universe)
    arrays = {"seat_draws": seats}
    for name in ("pr_share_draws", "ward_share_draws", "pr_vote_draws",
                 "ward_vote_draws", "ward_winner_draws", "pool_turnout_draws",
                 "council_sizes", "thresholds", "ward_winner_counts"):
        v = getattr(run, name, None)
        if v is not None:
            arrays[name] = np.array(v, copy=True)
    over = getattr(run, "over_draws", None)
    CAPTURED.update(
        arrays=arrays, seat_cols=cols, universe=list(run.universe),
        wards=[str(w) for w in run.wards],
        pool_turnout_names=list(getattr(run, "pool_turnout_names", []) or []),
        guards=json.loads(json.dumps(run.guards or {}, default=str)),
        pools_stale=run.scenario.get("_pools_stale"),
        pools_stale_allowed=run.scenario.get("_pools_stale_allowed"),
        allow_stale_pools=run.scenario.get("allow_stale_pools"),
        local_record_only=run.scenario.get("_local_record_only"),
        draws=run.draws, lot=getattr(run, "lot", None),
        over_draws=[sorted(x) for x in over] if over else None,
        overhang_count=dict(run.overhang_count or {}),
        ward_win_sum=dict(run.ward_win_sum or {}),
        notes=dict(run.notes or {}),
        roster_state=getattr(run, "roster_state", None),
        ward_pr_ratio=(dict(zip(run.universe, np.asarray(run.ratio).tolist()))
                       if getattr(run, "ratio", None) is not None else None),
        contestation=run.scenario.get("_contestation"),
        contestation_prev=run.scenario.get("_contestation_prev"),
        w_bye=run.scenario.get("w_bye"),
        bye_weight_mode=run.scenario.get("bye_weight_mode"),
        seed=run.scenario.get("seed"))
    return run


M.run_model = probe_run_model

for spec in args.module_set:
    name, value = spec.split("=", 1)
    mod_name, const = name.rsplit(".", 1)
    mod = __import__(mod_name)
    setattr(mod, const, type(getattr(mod, const))(value))

moved = None
if args.move_aside:
    src_p = ROOT / "data" / "processed" / args.move_aside
    moved = src_p.with_name(src_p.name + ".step11-aside")
    assert src_p.exists() and not moved.exists()
    src_p.rename(moved)

# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------
t_start = time.time()
result = None
try:
    if args.mode == "panel":
        import compare_history as CH
        result = CH.run_city_year(args.city, args.year, args.draws,
                                  Path("data/raw/elections"), list(args.set),
                                  run_dir=out / "trace")
    elif args.mode == "forecast":
        city = cityconfig.use(args.city)
        target = cityconfig.use_target(args.year)
        M.apply_city(city)
        scenario = M.load_scenario(argparse.Namespace(
            config=None, set=list(args.set), draws=args.draws, seed=None,
            city=args.city, target=args.year, counterfactual=False))
        M.run_model(target, scenario, Path("data/raw/elections"),
                    target.processed, verbose=False, run_dir=out / "trace")
    else:
        script = ROOT / "audits/2026-10-07-prediction-restructure/backtest/rule_a.py"
        sys.argv = [str(script), args.city, args.year, str(out / "rule_a.json")]
        runpy.run_path(str(script), run_name="__main__")
finally:
    if moved is not None:
        moved.rename(ROOT / "data" / "processed" / args.move_aside)

# --------------------------------------------------------------------------
# what is kept
# --------------------------------------------------------------------------
arrays = CAPTURED.pop("arrays")
draws = CAPTURED["draws"]
per_draw = np.zeros((draws, 2), dtype=np.int8)   # [:,0] lot, [:,1] item2
for d, cls in CALLS_IN_RUN:
    if cls == "lot":
        per_draw[d, 0] = 1
    elif cls == "item2":
        per_draw[d, 1] = 1
arrays["tie_class_per_draw"] = per_draw
np.savez_compressed(out / "arrays.npz", **arrays)
pop1 = per_draw.any(axis=1)
meta = dict(CAPTURED, mode=args.mode, city=args.city, year=args.year,
            draws_requested=args.draws, overrides=list(args.set),
            module_set=list(args.module_set), move_aside=args.move_aside,
            tree=str(ROOT), wall_seconds=time.time() - t_start,
            ties={"allocate_calls_in_run": len(CALLS_IN_RUN),
                  "awo_calls": STATE["draw"] + 1,
                  "draws_population_1": int(pop1.sum()),
                  "draws_with_lot_call": int(per_draw[:, 0].sum()),
                  "draws_with_item2_call": int(per_draw[:, 1].sum()),
                  "draws_lot_only": int((per_draw[:, 0] & ~per_draw[:, 1]).sum()),
                  "draws_item2_only": int((per_draw[:, 1] & ~per_draw[:, 0]).sum()),
                  "draws_both": int((per_draw[:, 0] & per_draw[:, 1]).sum()),
                  "calls_outside_run": CALLS_OUTSIDE})
(out / "meta.json").write_text(json.dumps(meta, indent=1, default=str))
if result is not None:
    (out / "result.json").write_text(json.dumps(result, indent=1, default=str))
assert CAPTURED["pools_stale"] in (None, ""), f"STALE: {CAPTURED['pools_stale']}"
# one allocate_with_overhang call per draw inside run_model, or the draw
# numbering (and so P1's populations) is wrong
assert STATE["draw"] + 1 == draws, (STATE["draw"] + 1, draws)
print(f"{args.mode} {args.city} {args.year} draws={draws} "
      f"pop1={int(pop1.sum())} stale={CAPTURED['pools_stale']!r} "
      f"{meta['wall_seconds']:.0f}s")
