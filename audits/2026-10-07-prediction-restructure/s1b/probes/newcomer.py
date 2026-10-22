"""Split h = 0 pairs: new to the city (no ward vote anywhere in the city at the
preceding LGE) vs absent from this ward only (stood elsewhere). 32 transitions,
IND excluded."""
import collections
from load import all_data, ward_shares, prior_on, parts_of, CITIES, YEARS
data = all_data()
newc, absent = [], []
for c in CITIES:
    for a, b in zip(YEARS, YEARS[1:]):
        prev = data[(c, a)][0]
        stood_city = {p for d in prev.values() for p, v in d["wv"].items() if v > 0}
        h, _, _ = prior_on(parts_of(data[(c, b)][0]), prev)
        s, _, _ = ward_shares(data[(c, b)][0])
        for w in s:
            if w not in h: continue
            for p, v in s[w].items():
                if p == "IND" or h[w].get(p, 0) > 0: continue
                (absent if p in stood_city else newc).append((v, c, b, w, p))
def q(xs, f):
    xs = sorted(xs); return xs[int(round(f * (len(xs) - 1)))]
for name, xs in [("new to the city", newc), ("absent from the ward only", absent)]:
    v = [x[0] for x in xs]
    print(f"{name}: n={len(v)} max {100*max(v):.1f} {max(xs)[1:]} p99 {100*q(v,.99):.1f} p95 {100*q(v,.95):.1f}; top5 {[ (round(100*x[0],1),)+x[1:] for x in sorted(xs, reverse=True)[:5]]}")
for before in ["2011", "2016", "2021"]:
    print(before, "new-to-city max from b<", before, round(100*max([x[0] for x in newc if x[2] < before]),1),
          "absent max", round(100*max([x[0] for x in absent if x[2] < before]),1))
