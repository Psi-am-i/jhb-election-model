"""Probe: raw ward swing vs ward swing net of the party's citywide swing
(uniform-swing residual), by starting share, stood-both pairs, IND excluded,
32 transitions. Also citywide swings by prior citywide share."""
import collections, sys
from load import all_data, ward_shares, prior_on, parts_of, CITIES, YEARS
EDGES = [0.0, 0.01, 0.05, 0.15, 0.35, 0.60, 1.0001]
def bin_of(h):
    for i in range(len(EDGES) - 1):
        if h <= EDGES[i + 1]:
            return i
data = all_data()
raw = collections.defaultdict(list); dev = collections.defaultdict(list); city = []
newc = []
for c in CITIES:
    for a, b in zip(YEARS, YEARS[1:]):
        vds = data[(c, b)][0]
        h, cov, turn = prior_on(parts_of(vds), data[(c, a)][0])
        s, tot, reg = ward_shares(vds)
        wards = [w for w in s if w in h]
        A = sum(tot[w] for w in wards)
        wt = {w: tot[w] / A for w in wards}          # weights: the target's votes
        H = collections.Counter(); S = collections.Counter()
        for w in wards:
            for p, v in h[w].items(): H[p] += wt[w] * v
            for p, v in s[w].items(): S[p] += wt[w] * v
        for p in set(H) | set(S):
            if p != "IND" and H[p] > 0 and S[p] > 0:
                city.append((S[p] - H[p], H[p], c, a, b, p))
        for w in wards:
            for p in set(h[w]) & set(s[w]):
                if p == "IND":
                    continue
                d = s[w][p] - h[w][p]
                raw[bin_of(h[w][p])].append((d, c, b, w, p))
                dev[bin_of(h[w][p])].append((d - (S[p] - H[p]), c, b, w, p))
def q(xs, f):
    xs = sorted(xs); return xs[int(round(f * (len(xs) - 1)))]
print("bin | n | raw swing min..max (p01..p99) | residual after citywide swing min..max (p01..p99), points")
for i in sorted(raw):
    r = [x[0] * 100 for x in raw[i]]; d = [x[0] * 100 for x in dev[i]]
    print(f"({EDGES[i]:.2f},{EDGES[i+1]:.2f}] n={len(r)} raw {min(r):.1f}..{max(r):.1f} ({q(r,.01):.1f}..{q(r,.99):.1f})"
          f" | resid {min(d):.1f}..{max(d):.1f} ({q(d,.01):.1f}..{q(d,.99):.1f})  resid argmin {min(dev[i])[1:]} argmax {max(dev[i])[1:]}")
print("\ncitywide ward-ballot swing (points) by prior citywide share, stood both, 32 transitions:")
cb = collections.defaultdict(list)
for x in city:
    cb[bin_of(x[1])].append(x)
for i in sorted(cb):
    v = [x[0] * 100 for x in cb[i]]
    print(f"({EDGES[i]:.2f},{EDGES[i+1]:.2f}] n={len(v)} min {min(v):.1f} {min(cb[i])[2:]} max {max(v):.1f} {max(cb[i])[2:]}")
