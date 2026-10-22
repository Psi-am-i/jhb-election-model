import sys, json, argparse, time
from pathlib import Path
sys.path.insert(0, "src")
import numpy as np
import cityconfig, montecarlo as M
from fold import load, citywide
from pools import SPLITS
CODES = {"joburg":"JHB","tshwane":"TSH","ekurhuleni":"EKU","ethekwini":"ETH",
         "capetown":"CPT","mangaung":"MAN","nelsonmandelabay":"NMA","buffalocity":"BUF"}
D = Path("data/raw/elections")
slug, year, draws = sys.argv[1], sys.argv[2], int(sys.argv[3])
code = CODES[slug]
t0 = time.time()
city = cityconfig.use(slug)
target = cityconfig.use_target(year)
M.apply_city(city)
scenario = M.load_scenario(argparse.Namespace(config=None, set=[], draws=draws, seed=None, city=slug, target=year))
import os
if os.environ.get("SUBUNIT_AT_MEAN") == "1":
    class Proxy:
        def __init__(self, r): self._r = r
        def __getattr__(self, k): return getattr(self._r, k)
        def dirichlet(self, alpha):
            x = self._r.dirichlet(alpha); a = np.asarray(alpha, float); mask = a < 1.0
            if mask.any() and (~mask).any():
                m = a[mask] / a.sum(); rest = x[~mask]; rest = rest / rest.sum() * (1 - m.sum())
                x = x.copy(); x[mask] = m; x[~mask] = rest
            return x
    _orig = M.make_drawer
    M.make_drawer = lambda s_, b, c, i, rng: _orig(s_, b, c, i, Proxy(rng))
run = M.run_model(target, scenario, D, verbose=False)
# pre-target history, same definition as world.py
hist = set()
for y in sorted(cityconfig.CALENDAR):
    if y >= year: break
    e = cityconfig.CALENDAR[y]
    if not e.results: continue
    p = D / e.results.replace("{CODE}", code)
    if not p.exists(): continue
    v, _ = load(p, "PR" if e.kind == "LGE" else None)
    hist |= {q for q, s in citywide(v).items() if s > 0 and q != "IND"}
first = sorted(q for q in run.universe if (q not in hist and q not in SPLITS and q != "IND") or q == "ENTRANT")
seated, out5, out7, fseats, fwon = [], [], [], [], []
per = {}
for sd in run.seat_draws:
    pp = {q: s for q, s in sd.items() if s > 0 and q != "IND"}
    srt = sorted(pp.values(), reverse=True)
    seated.append(len(pp)); out5.append(sum(srt[5:])); out7.append(sum(srt[7:]))
    fseats.append(sum(pp.get(q, 0) for q in first)); fwon.append(sum(1 for q in first if pp.get(q, 0) > 0))
    for q in pp: per[q] = per.get(q, 0) + 1
res = {"city": slug, "year": year, "draws": len(run.seat_draws), "secs": round(time.time()-t0,1),
       "universe": len(run.universe), "first_in_universe": first,
       "seeds": sorted((scenario.get("pool_seeds") or {}).keys()),
       "seated": seated, "out5": out5, "out7": out7, "first_seats": fseats, "first_won": fwon,
       "p_seat": {q: c/len(run.seat_draws) for q, c in per.items()}}
json.dump(res, open(sys.argv[4], "w"))
q = lambda a: (int(np.percentile(a,5)), float(np.median(a)), int(np.percentile(a,95)))
print(slug, year, "draws", res["draws"], "secs", res["secs"], "univ", res["universe"], "nfirst", len(first),
      "seated", q(seated), "out7", q(out7), "first_seats", q(fseats), "first_won", q(fwon))
