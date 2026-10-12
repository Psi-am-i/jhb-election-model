"""A10: ward x party cells the model never draws above zero, but the result has.

Measurement only. Runs `montecarlo.run_model` directly on the ARCHIVED, hooked
copy of `src/` made by setup.sh (never the live tree, never montecarlo's main).
Writes only under --out.

    sh audits/2026-09-29-zero-cells/setup.sh 022f8d4
    .venv/bin/python audits/2026-09-29-zero-cells/zero_cells.py \
        --src /tmp/zc_src/src --city joburg --year 2021 --draws 2000 --out DIR

DEFINITIONS (fixed before the first run)
  model ward share, ward ballot   the draw's `ward_tally` row (after ward noise,
                                  the array the ward winner is taken from),
                                  normalised per ward.
  model ward share, PR ballot     part_cast x pr_eff summed to the ward, the same
                                  construction as ward_tally on the PR ballot.
  zero cell                       max over draws of the model share < 1e-12,
                                  and the actual share of that ward on that
                                  ballot > 0. Parties outside the run's universe
                                  have model share 0 by construction and are
                                  counted, tagged "not in universe". ENTRANT is
                                  relabelled onto the scoring arrival exactly as
                                  compare_history does (backtest.relabel_run's
                                  label, from _actual_seats).
  actual ward share               the target's own result file, rows summed by
                                  (Ward, canonical party), per ballot. Rows are
                                  read directly, not via fold.load, because
                                  fold.load keeps one ward per VD and so misfiles
                                  split VDs.
  cause                           for every zero cell, the party's pool
                                  membership in the spec the run loaded:
                                  named in the spec at all, and the pools where
                                  it is exactly 0 or absent.

CONTROLS (--control)
  plant       after the ward winners are taken, the hook sets cell (ward 0,
              largest universe party) of ward_tally and of the PR ward tally to
              exactly 0 in every draw, and (ward 1, same party) to 1e-9 of the
              row. The detector must report the first as a zero cell and must NOT
              report the second.
  actual      a synthetic party ZC_CONTROL is added to the actual tables with 1
              vote in the first actual ward on each ballot. It must come out as a
              zero cell tagged "not in universe".
  c4_extreme  the spec is perturbed so that one named party (--c4-party) has
              membership exactly 0 in every pool but its largest: the most
              extreme hard-zero pattern C4 could produce for that party.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

SEED = 20261104
ZERO = 1e-12
BANDS = [1e-12, 1e-9, 1e-6, 1e-4, 1e-3]


def actual_tables(path, P, cityconfig):
    """{ballot: {ward: {party: votes}}} from the result file's own rows."""
    out = {"PR": defaultdict(lambda: defaultdict(int)),
           "Ward": defaultdict(lambda: defaultdict(int))}
    path = cityconfig.resolve_path(path)
    with path.open(encoding="utf-8", newline="") as h:
        for row in csv.DictReader(h):
            b = row.get("BallotType", "")
            b = "PR" if b.upper() == "PR" else "Ward" if b.upper() == "WARD" else None
            if b is None or not row.get("Ward"):
                continue
            out[b][row["Ward"]][P.canonical(row["sPartyName"])] += int(row["Party_Votes"])
    return {b: {w: dict(c) for w, c in t.items()} for b, t in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--city", required=True)
    ap.add_argument("--year", required=True)
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--control", choices=["none", "plant", "c4_extreme"], default="none")
    ap.add_argument("--c4-party", default=None)
    a = ap.parse_args()
    sys.path.insert(0, a.src)
    import cityconfig
    import montecarlo as M
    import parties as P
    import compare_history as CH

    assert "_ZC_HOOK" in Path(M.__file__).read_text(), "unhooked montecarlo"
    assert Path(M.__file__).resolve().is_relative_to(Path(a.src).resolve())

    city = cityconfig.use(a.city)
    target = cityconfig.use_target(a.year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=[], draws=a.draws, seed=None, city=a.city, target=a.year))
    scenario["seed"] = SEED

    spec_path = target.city.processed / f"pools_{target.year}.json"
    spec = json.loads(spec_path.read_text())

    real_rt = Path.read_text
    if a.control == "c4_extreme":
        pools = spec["pools"]
        w = {g: float(pools[g]["members"].get(a.c4_party, 0.0)) for g in pools}
        keep = max(w, key=w.get)
        assert w[keep] > 0
        for g in pools:
            if g != keep:
                pools[g]["members"].pop(a.c4_party, None)
        spec_text = json.dumps(spec)
        want = str(spec_path.resolve())

        def rt(self, *x, **k):
            if str(Path(self).resolve()) == want:
                return spec_text
            return real_rt(self, *x, **k)
        Path.read_text = rt

    acc = {}

    def hook(L):
        wt = L["ward_tally"]
        pt = np.zeros_like(wt)
        np.add.at(pt, L["part_ward"], L["part_cast"][:, None] * L["pr_eff"][L["part_vd"]])
        if not acc:
            acc["wards"] = list(L["wards"])
            acc["universe"] = list(L["universe"])
            for k in ("W", "PR"):
                acc["max_" + k] = np.zeros(wt.shape)
                acc["pos_" + k] = np.zeros(wt.shape, dtype=np.int64)
            acc["win"] = np.zeros(wt.shape, dtype=np.int64)
            acc["n"] = 0
            acc["min_vd_share_W"] = np.full(wt.shape[1], np.inf)
        if a.control == "plant":
            # fixed at the first draw: the largest party can change between
            # draws, and a plant that moves is not a plant
            if "plant_j" not in acc:
                acc["plant_j"] = int(np.argmax(wt.sum(axis=0)))
                acc["plant_party"] = acc["universe"][acc["plant_j"]]
            j = acc["plant_j"]
            for t in (wt, pt):
                t[0, j] = 0.0
                t[1, j] = 0.0
                t[1, j] = 1e-9 * t[1].sum() / (1 - 1e-9)
        acc["win"][np.arange(wt.shape[0]), L["winners"]] += 1
        for k, t in (("W", wt), ("PR", pt)):
            s = t / np.maximum(t.sum(axis=1, keepdims=True), 1e-300)
            np.maximum(acc["max_" + k], s, out=acc["max_" + k])
            acc["pos_" + k] += s >= ZERO
        acc["min_vd_share_W"] = np.minimum(acc["min_vd_share_W"], L["wd_eff"].min(axis=0))
        acc["n"] += 1

    M._ZC_HOOK = hook
    t0 = time.time()
    try:
        run = M.run_model(target, scenario, verbose=False)
    finally:
        M._ZC_HOOK = None
        Path.read_text = real_rt
    secs = time.time() - t0

    # The hook saw the arrays the model used: its winner tally must equal the
    # run's own (plant mutates only after the winners are taken).
    wc = np.asarray(run.ward_winner_counts)
    assert acc["n"] == a.draws, (acc["n"], a.draws)
    assert np.array_equal(wc, acc["win"]), "hook winners != run winners"
    assert list(run.wards) == acc["wards"]

    data_dir = Path("data/raw/elections")
    _seats, entrant_actual, _winners = CH._actual_seats(target, data_dir)
    universe = list(acc["universe"])
    relabel = None
    if entrant_actual and "ENTRANT" in universe:
        relabel = entrant_actual
        universe = [entrant_actual if p == "ENTRANT" else p for p in universe]
    uidx = {p: i for i, p in enumerate(universe)}

    act = actual_tables(data_dir / target.results(target.year), P, cityconfig)
    act["PR"] = {w: dict(c) for w, c in act["PR"].items()}
    if a.control == "plant" or a.control == "none":
        pass
    # actual-side control, always on: a synthetic party with one vote
    for b in ("PR", "Ward"):
        w0 = sorted(act[b])[0]
        act[b][w0] = dict(act[b][w0])
        act[b][w0]["ZC_CONTROL"] = 1

    widx = {w: i for i, w in enumerate(acc["wards"])}
    spec_pools = spec["pools"]
    spec_named = {p for g in spec_pools.values() for p, v in g["members"].items()}

    def membership(p):
        z = [g for g, c in spec_pools.items() if float(c["members"].get(p, 0.0)) == 0.0]
        return {"named_in_spec": p in spec_named,
                "zero_pools": z, "n_pools": len(spec_pools)}

    cells, near, unmatched = [], {b: {str(x): 0 for x in BANDS} for b in ("PR", "Ward")}, {}
    n_cells_scanned = {"PR": 0, "Ward": 0}
    for b, key in (("PR", "PR"), ("Ward", "W")):
        mx = acc["max_" + key]
        unmatched[b] = sorted(w for w in act[b] if w not in widx)
        for w, row in act[b].items():
            tot = sum(row.values())
            for p, v in row.items():
                if v <= 0 or p in ("SPOILT",):
                    continue
                n_cells_scanned[b] += 1
                if w not in widx:
                    m, why = 0.0, "ward not forecast"
                elif p not in uidx:
                    m, why = 0.0, "not in universe"
                else:
                    m, why = float(mx[widx[w], uidx[p]]), "in universe"
                for x in BANDS:
                    if m < x:
                        near[b][str(x)] += 1
                if m < ZERO:
                    cells.append({"ballot": b, "ward": w, "party": p, "votes": v,
                                  "ward_total": tot, "share": v / tot,
                                  "model_max": m, "why": why,
                                  "pos_draws": (int(acc["pos_" + key][widx[w], uidx[p]])
                                                if why == "in universe" else 0),
                                  **membership(p)})

    # every universe party's smallest max-share over wards: what the floor gives
    floor_report = {}
    for key in ("W", "PR"):
        mx = acc["max_" + key]
        floor_report[key] = {universe[j]: float(mx[:, j].min()) for j in range(len(universe))}

    out = {"city": a.city, "year": a.year, "draws": a.draws, "seed": SEED,
           "control": a.control, "c4_party": a.c4_party,
           "plant_party": acc.get("plant_party"), "plant_wards": acc["wards"][:2],
           "relabel_entrant": relabel, "seconds": round(secs, 1),
           "spec": str(spec_path), "universe": universe,
           "n_wards_model": len(acc["wards"]),
           "n_wards_actual": {b: len(act[b]) for b in act},
           "unmatched_actual_wards": unmatched,
           "cells_scanned": n_cells_scanned,
           "near_zero_counts": near,
           "min_vd_share_W": {universe[j]: float(acc["min_vd_share_W"][j])
                              for j in range(len(universe))},
           "min_over_wards_of_max_share": floor_report,
           "zero_cells": cells}
    Path(a.out).mkdir(parents=True, exist_ok=True)
    tag = "" if a.control == "none" else f"-{a.control}" + (f"-{a.c4_party}" if a.c4_party else "")
    (Path(a.out) / f"{a.city}-{a.year}{tag}.json").write_text(json.dumps(out, indent=1))
    nz = sum(1 for c in cells if c["party"] != "ZC_CONTROL")
    print(f"{a.city} {a.year} {a.control}: {secs:.0f}s, zero cells excl. control "
          f"{nz}, control found {sum(c['party']=='ZC_CONTROL' for c in cells)}")


if __name__ == "__main__":
    main()
