import sys, json
sys.path.insert(0, "src")
import numpy as np
import pools
CODES = {"joburg":"JHB","tshwane":"TSH","ekurhuleni":"EKU","ethekwini":"ETH","capetown":"CPT","mangaung":"MAN","nelsonmandelabay":"NMA","buffalocity":"BUF"}
F = json.load(open("/tmp/smalltail_firstshares.json"))
cache = {}
rows = []
for c, y, q, share, seats in F:
    k = (CODES[c], y)
    if k not in cache: cache[k] = pools._ward_reach(*k)
    rows.append((c, y, q, share, seats, cache[k].get(q)))
r = np.array([x[5] if x[5] is not None else np.nan for x in rows]); w = np.array([x[4] > 0 for x in rows])
print("reach missing:", np.isnan(r).sum(), "of", len(r))
for lo, hi in [(0, .1), (.1, .25), (.25, .5), (.5, .9), (.9, 1.01)]:
    m = (r >= lo) & (r < hi); print("reach [%.2f,%.2f): n=%d won=%d rate=%.3f" % (lo, hi, m.sum(), w[m].sum(), w[m].mean() if m.sum() else float('nan')))
for yy in ("2011", "2016", "2021"):
    m = np.array([x[1] == yy for x in rows]); print(yy, "n", m.sum(), "won", w[m].sum())
S = json.load(open("data/processed/pools_2026.json"))
print("spec keys roster type", type(S["roster"]).__name__, str(S["roster"])[:300])
print("reach_source", S["reach_source"]); print("seed_notes sample", list(S["seed_notes"].items())[:2])
