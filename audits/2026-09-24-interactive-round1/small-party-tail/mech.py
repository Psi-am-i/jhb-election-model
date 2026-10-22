import sys, json, argparse
from pathlib import Path
sys.path.insert(0, "src")
import numpy as np
import cityconfig, montecarlo as M
variant = sys.argv[1]; draws = int(sys.argv[2])
D = Path("data/raw/elections")
city = cityconfig.use("joburg"); target = cityconfig.use_target("2026"); M.apply_city(city)
scenario = M.load_scenario(argparse.Namespace(config=None, set=[], draws=draws, seed=None, city="joburg", target="2026"))
SPEC = json.load(open("data/processed/pools_2026.json"))
seeds = {p for p, v in SPEC["seeds"].items() if v > 0 and p != "SOUTH_AFRICAN_COMMUNIST_PARTY"}
captured = {}
class Proxy:
    def __init__(self, r): self._r = r
    def __getattr__(self, k): return getattr(self._r, k)
    def dirichlet(self, alpha):
        x = self._r.dirichlet(alpha)
        a = np.asarray(alpha, float)
        mask = a < 1.0
        if variant == "subunit_at_mean" and mask.any() and (~mask).any():
            m = a[mask] / a.sum()
            rest = x[~mask]; rest = rest / rest.sum() * (1 - m.sum())
            x = x.copy(); x[mask] = m; x[~mask] = rest
        return x
orig = M.make_drawer
orig_ps = M.pool_spec
def ps(*a, **k):
    out = orig_ps(*a, **k); captured["pools"] = out; return out
def md(scenario_, base, centres, index, rng):
    captured["index"] = index; captured["centres"] = dict(centres)
    return orig(scenario_, base, centres, index, Proxy(rng))
M.make_drawer = md; M.pool_spec = ps
if variant == "scale1000": scenario["dirichlet_scale"] = 1000.0
run = M.run_model(target, scenario, D, verbose=False)
n = len(run.seat_draws)
p_seat = {q: sum(1 for sd in run.seat_draws if sd.get(q, 0) > 0) / n for q in run.universe}
seat_mean = {q: sum(sd.get(q, 0) for sd in run.seat_draws) / n for q in run.universe}
seed_p = sorted(p_seat[q] for q in seeds if q in p_seat)
top7 = {"ANC","DA","ASA","EFF","MK","PA","IFP"}
seated = [sum(1 for q, s in sd.items() if s > 0 and q != "IND") for sd in run.seat_draws]
out7 = [sum(s for q, s in sd.items() if q not in top7 and q != "IND") for sd in run.seat_draws]
seedseats = [sum(sd.get(q, 0) for q in seeds) for sd in run.seat_draws]
pc = lambda a: (int(np.percentile(a, 5)), float(np.median(a)), int(np.percentile(a, 95)))
print(variant, "draws", n, "nseeds", len(seeds), "seated", pc(seated), "outside named 7", pc(out7), "seed seats", pc(seedseats),
      "sum seed seat mean", round(sum(seat_mean[q] for q in seeds), 2))
print("seed p_seat quantiles (min, q25, med, q75, max):", [round(v, 3) for v in np.percentile(seed_p, [0,25,50,75,100])])
print("non-seed, non-top7 p_seat:", sorted(((q, round(p_seat[q],2), round(seat_mean[q],2)) for q in run.universe if q not in seeds and q not in top7), key=lambda t:-t[1]))
ix = run.index
pr = run.pr_share_draws; wd = run.ward_share_draws
rows = []
for q in sorted(seeds):
    i = ix[q]
    rows.append((q, SPEC["seeds"][q], round(p_seat[q],3), float(pr[:, i].mean()), float(np.median(pr[:, i])), float(wd[:, i].mean()) if wd is not None else None))
for r in rows[:6]: print("seed", r)
print("mean over seeds: seed %.5f p_seat %.4f prmean %.5f prmedian %.6f wardmean %s" % tuple([np.mean([r[k] for r in rows]) for k in (1,2,3,4)] + [np.mean([r[5] for r in rows]) if rows[0][5] is not None else None]))
print("corr(seed, p_seat)", np.corrcoef([r[1] for r in rows], [r[2] for r in rows])[0,1])
# seat-winning PR share: smallest PR share that won a seat, per draw
mins = []
for d, sd in enumerate(run.seat_draws):
    w = [pr[d, ix[q]] for q, s in sd.items() if s > 0 and q in ix]
    if w: mins.append(min(w))
print("smallest seat-winning PR share per draw, pct (5,50,95):", np.percentile(mins, [5,50,95]))
if variant == "base":
    # the per-pool alpha and in-pool mean for two micro seeds
    pools = captured["pools"]; idx = captured["index"]
    for party in ("AFRICAN_ECONOMIC_FREEDOM", "MOVE_SA"):
        i = idx[party]
        print("party", party, "centre", captured["centres"].get(party), "seed", scenario["pool_seeds"][party], "band", scenario["pool_seed_bands"][party])
        for name, tup in pools.items():
            pidx, reg, spec, props, alpha, names, levels, wts = tup
            if party in names:
                j = list(names).index(party)
                print("   pool", name, "alpha_total", round(alpha, 3), "mean in pool", props[j], "component alpha", props[j]*alpha)
    json.dump({"p_seat": p_seat, "seat_mean": seat_mean}, open("/tmp/smalltail_mech_base.json", "w"))
print("thresholds sample:", None if run.thresholds is None else np.percentile(run.thresholds, [5,50,95]))
