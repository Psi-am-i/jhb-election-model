"""One arm of prereg/2026-10-30-census-adjusted-composition.md, Johannesburg 2026.

    PYTHONHASHSEED=0 .venv/bin/python rounds/2026-10-23-out-of-sample/census-adjust/arms/run_arm.py --arm B|N|E

One process per arm (pools keeps process-level caches, e.g. _PANEL_SPREAD_CACHE,
that must not carry one arm's census into another).

1. Patches ``pools.read_census`` for the population-group dimension, Census 2022
   (arms N, E; B unpatched), so the emit's pool fit and the run's per-VD
   composition (``montecarlo.run_model`` -> ``pools.pool_counts``) both read it.
2. Emits the 2026 pool spec in process (``pools.emit_pools``, as the CLI's
   ``--emit --out`` does) into specs/<arm>/pools_2026.json. Nothing under data/.
3. Points ``montecarlo.read_pool_spec`` at that file (the one seam through which
   run_model reads the spec; its staleness check runs on the arm's file).
4. Runs ``montecarlo.run_model`` in process with arm U's scenario (the default,
   as the frozen forecast), seed and draws as given, no width override (the
   width record's key is computed from data/processed, which is untouched).
5. Writes <arm>/arrays.npz and <arm>/meta.json here.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
os.chdir(REPO)
sys.path.insert(0, str(REPO / "src"))

import cityconfig  # noqa: E402
import pools  # noqa: E402
import montecarlo as M  # noqa: E402
import arms as A  # noqa: E402

G = ["Black African", "Coloured", "Indian/Asian", "White"]
EXCESS = {"White": 290000 / 4525800, "Indian/Asian": 190000 / 1705882}
WARDS_CSV = HERE.parent / "wards.csv"


def e_shares() -> dict[str, np.ndarray]:
    out = {}
    for r in csv.DictReader(open(WARDS_CSV)):
        v = np.array([float(r[f"c11_{g}"]) for g in G])
        out[r["ward"]] = v / v.sum()
    return out


def install_patch(arm: str) -> dict:
    orig = pools.read_census
    calls = {"patched": 0, "passed": 0, "wards_changed": 0}
    if arm == "B":
        return calls
    fac = np.array([1 - EXCESS.get(g, 0.0) for g in G])
    E = e_shares() if arm == "E" else None

    def patched(dim, census, cfg):
        comp = orig(dim, census, cfg)
        if dim.name != "population_group" or int(census.year) != 2022:
            calls["passed"] += 1
            return comp
        assert list(dim.categories) == G, dim.categories
        calls["patched"] += 1
        out = {}
        for w, v in comp.items():
            if arm == "N":
                x = np.asarray(v, dtype=float) * fac
                out[w] = x / x.sum()
            elif arm == "E" and w in E:
                out[w] = E[w].copy()
            else:
                out[w] = v
        calls["wards_changed"] = sum(1 for w in comp
                                     if not np.allclose(out[w], comp[w]))
        if arm == "E":
            missing = set(E) - set(comp)
            assert not missing, f"E wards not in census: {sorted(missing)[:5]}"
        return out

    pools.read_census = patched
    return calls


def citywide_mix(city, year: str) -> dict:
    """Roll-weighted (registered) and votes-weighted citywide mix, from
    pool_counts as the run reads it."""
    cfg = pools.load_config()
    pc = pools.pool_counts(city, year, cfg)
    reg = pc.registered.sum(axis=0); vot = pc.voted.sum(axis=0)
    return {"registered": {c: round(100 * float(x / reg.sum()), 3)
                           for c, x in zip(pc.categories, reg)},
            "voted": {c: round(100 * float(x / vot.sum()), 3)
                      for c, x in zip(pc.categories, vot)}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=["B", "N", "E"])
    ap.add_argument("--draws", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--tag", default="", help="subfolder prefix, e.g. smoke")
    a = ap.parse_args()
    assert os.environ.get("PYTHONHASHSEED") == M.HASH_SEED, \
        "run under PYTHONHASHSEED=" + M.HASH_SEED
    seed = int(a.seed if a.seed is not None else M.DEFAULTS["seed"])
    arm = a.arm
    base = HERE / a.tag if a.tag else HERE
    dest = base / arm
    dest.mkdir(parents=True, exist_ok=True)
    calls = install_patch(arm)

    city = cityconfig.use("joburg")
    target = cityconfig.use_target("2026")
    cfg = pools.load_config()

    # --- emit the arm's spec, outside data/ ---
    spec = pools.emit_pools(city, target, cfg)
    spec_dir = base / "specs" / arm
    spec_dir.mkdir(parents=True, exist_ok=True)
    spec_path = spec_dir / "pools_2026.json"
    spec_path.write_text(json.dumps(spec, indent=2, sort_keys=True))
    print(f"emitted {spec_path}; fitted_on {spec['fitted_on']}; "
          f"census calls {calls}", flush=True)

    mix = citywide_mix(city, spec["fitted_on"])
    print("citywide mix", json.dumps(mix), flush=True)
    spec_pools = {n: {"registered": c.get("registered"),
                      "members_top": dict(sorted(c["members"].items(),
                                                 key=lambda kv: -kv[1])[:4])}
                  for n, c in spec["pools"].items()}

    # --- point run_model at the arm's spec ---
    orig_read = M.read_pool_spec

    def read_arm_spec(_path, c, t):
        return orig_read(spec_path, c, t)
    M.read_pool_spec = read_arm_spec

    # --- run, arm U's scenario (defaults) ---
    tgt, scenario = A.fresh_scenario("U", "joburg", "2026", a.draws, seed)
    run = M.run_model(tgt, scenario, A.DATA, verbose=False)
    assert scenario.get("_pools_stale") in (None, ""), scenario.get("_pools_stale")
    universe = list(run.universe)
    seats = np.array([[s.get(p, 0) for p in universe] for s in run.seat_draws],
                     dtype=np.int64)
    np.savez_compressed(
        dest / "arrays.npz", seat_draws=seats,
        ward_winner_draws=np.asarray(run.ward_winner_draws, dtype=np.int64),
        pr_share_draws=np.asarray(run.pr_share_draws, dtype=float),
        thresholds=np.asarray(run.thresholds),
        council_sizes=np.asarray(run.council_sizes))
    guards = dict(getattr(run, "guards", {}) or {})
    meta = {"arm": arm, "draws": a.draws, "seed": seed,
            "universe": universe, "wards": list(run.wards),
            "commit": subprocess.run(["git", "rev-parse", "HEAD"], text=True,
                                     capture_output=True).stdout.strip(),
            "src_dirty": bool(subprocess.run(
                ["git", "status", "--porcelain", "--", "src"], text=True,
                capture_output=True).stdout.strip()),
            "census_calls": calls, "citywide_mix": mix,
            "spec_artefact_key": spec.get("artefact_key"),
            "spec_pools": spec_pools,
            "pools_spec_read": str(spec_path),
            "width_record_key": M.width_record_key(),
            "width_record_variant": M.width_record_variant(scenario),
            "draw_law": guards.get("draw_law"),
            "kappa_converged": guards.get("kappa_converged"),
            "kappa_iters": guards.get("kappa_iters")}
    (dest / "meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True,
                                               default=str))
    print("mean seats", dict(zip(universe, np.round(seats.mean(0), 2))))
    print(f"wrote {dest}")


if __name__ == "__main__":
    main()
