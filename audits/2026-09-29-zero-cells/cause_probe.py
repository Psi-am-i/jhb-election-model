"""For each flagged out-of-universe party: was it roster-dropped, in the
preceding NPE baseline file at all, or seeded? 3-draw runs; prints only."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, "/tmp/zc_src/src")
import cityconfig, montecarlo as M
from fold import load, citywide
R = Path("audits/2026-09-29-zero-cells/results")
out = {}
for line in (R / "panel.txt").read_text().split("\n"):
    if not line.strip():
        continue
    c, y = line.split()
    d = json.loads((R / f"{c}-{y}.json").read_text())
    flagged = sorted({x["party"] for x in d["zero_cells"]
                      if x["why"] == "not in universe" and x["party"] != "ZC_CONTROL"})
    city = cityconfig.use(c); t = cityconfig.use_target(y); M.apply_city(city)
    sc = M.load_scenario(argparse.Namespace(config=None, set=[], draws=3, seed=None, city=c, target=y))
    sc["seed"] = 20261104
    r = M.run_model(t, sc, verbose=False)
    npe = citywide(load(Path("data/raw/elections") / t.results(t.previous_npe), "PR")[0])
    seeds = {k for k, v in (r.scenario.get("pool_seeds") or {}).items() if v > 0}
    cls = {}
    for p in flagged:
        cls[p] = ("roster_dropped" if p in r.roster_dropped else
                  "seeded?!" if p in seeds else
                  "in NPE baseline file?!" if p in npe else
                  "IND excluded" if p in ("IND", "INDEPENDENT") else
                  "no NPE baseline, not seeded")
    out[f"{c} {y}"] = {"previous_npe": t.previous_npe, "universe_matches": list(r.universe) == [p for p in d["universe"]] or d["relabel_entrant"] is not None, "classes": cls}
    print(c, y, t.previous_npe, {k: sum(1 for v in cls.values() if v == k) for k in set(cls.values())}, flush=True)
(R / "cause_probe.json").write_text(json.dumps(out, indent=1))
