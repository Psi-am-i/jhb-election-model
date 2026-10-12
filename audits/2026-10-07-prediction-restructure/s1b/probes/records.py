"""SPEC-B2r2 probe: record exceedances. Read-only.

Ordered in time by the later election of each consecutive metro LGE pair
(2006, 2011, 2016, 2021; all metros of one election form one round). Whenever a
round's swing beats the previous record in that direction, the exceedance is
new record minus old record. Two scopes:
  party-own : record per (party, bin, direction), pooled over metros
  pooled    : record per (bin, direction), all parties (the quantity the
              editor's bin extremes are made of)
Ward level: stood-both (ward, party) pairs, bins by starting ward share.
Citywide: stood-both (city, party) pairs, bins by prior citywide share.
Exclusions (mergers, splits, collapses) are detected from the data; see
detect()."""
import collections, json, statistics, sys
from load import all_data, ward_shares, prior_on, parts_of, CITIES, YEARS
import b2bt as B
import cityswing as CS

EDGES = B.EDGES
data = all_data()
VANISH_MIN, SPLIT_MIN, COLLAPSE_FROM, COLLAPSE_KEEP, CORR = 0.01, 0.05, 0.02, 0.25, 0.5

def city_share(c, y):
    return B.city_prior(c, y)

def corr(x, y):
    n = len(x)
    if n < 3: return 0.0
    mx, my = sum(x) / n, sum(y) / n
    sx = sum((a - mx) ** 2 for a in x) ** .5; sy = sum((b - my) ** 2 for b in y) ** .5
    return 0.0 if sx == 0 or sy == 0 else sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)

def detect():
    """{(city, b): {party: reason}} of swings to leave out, and the evidence."""
    out = collections.defaultdict(dict); ev = []
    for c in CITIES:
        for a, b in zip(YEARS, YEARS[1:]):
            vds_b = data[(c, b)][0]
            h, _, _ = prior_on(parts_of(vds_b), data[(c, a)][0])
            s, _, _ = ward_shares(vds_b)
            Ha, Hb = city_share(c, a), city_share(c, b)
            prb = data[(c, b)][1]
            wards = [w for w in s if w in h]
            stood = [p for p in Hb if Ha.get(p, 0) > 0 and p != "IND"]
            def sw(p): return [s[w].get(p, 0) - h[w].get(p, 0) for w in wards]
            # merger: a party with >= 1% that stands nowhere at b (no ward or list vote)
            for q, v in Ha.items():
                if q == "IND" or v < VANISH_MIN or Hb.get(q, 0) > 0 or prb.get(q, 0) > 0:
                    continue
                hq = [h[w].get(q, 0) for w in wards]
                best = max(stood, key=lambda p: corr(sw(p), hq))
                r = corr(sw(best), hq)
                kind = "merger" if r >= CORR else "dissolution"
                ev.append((kind, c, a, b, q, round(100 * v, 1), best, round(r, 2)))
                if kind == "merger":
                    out[(c, b)][best] = f"merger: {q} ({100*v:.1f}% at {a}) absorbed, r={r:.2f}"
            # split: a party new to the city at b with >= 5% of the ward vote
            for n_, v in Hb.items():
                if n_ == "IND" or v < SPLIT_MIN or Ha.get(n_, 0) > 0:
                    continue
                sn = [s[w].get(n_, 0) for w in wards]
                src = min(stood, key=lambda p: corr(sw(p), sn))
                r = corr(sw(src), sn)
                kind = "split" if r <= -CORR else "new party"
                ev.append((kind, c, a, b, n_, round(100 * v, 1), src, round(r, 2)))
                if kind == "split":
                    out[(c, b)].setdefault(src, f"split: {n_} ({100*v:.1f}%) drew from it, r={r:.2f}")
            # collapse: from >= 2% to under a quarter of it
            for p in stood:
                if Ha[p] >= COLLAPSE_FROM and Hb[p] < COLLAPSE_KEEP * Ha[p]:
                    ev.append(("collapse", c, a, b, p, round(100 * Ha[p], 1), round(100 * Hb[p], 1), None))
                    out[(c, b)][p] = f"collapse: {100*Ha[p]:.1f}% -> {100*Hb[p]:.1f}%"
    return out, ev

EXCL, EVIDENCE = detect()
def excluded(c, b, p, which):
    """which: 'all', 'cope' (COPE's collapse and split only + the ID merger), 'none'."""
    if which == "none": return False
    r = EXCL.get((c, b), {}).get(p)
    if r is None: return False
    if which == "all": return True
    return ("COPE" in r) or p == "COPE" or "INDEPENDENT_DEMOCRATS" in r

def ward_obs(which):
    """[(year b, city, party, bin, swing)] stood-both, after exclusions."""
    return [(r[2], r[0], r[4], B.bin_of(r[5]), r[6] - r[5]) for r in B.TRANS
            if r[5] > 0 and r[6] > 0 and not excluded(r[0], r[2], r[4], which)]

def city_obs(which):
    return [(b, c, p, B.bin_of(H), V - H) for c, b, p, H, V in CS.PAIRS
            if H > 0 and V > 0 and not excluded(c, b, p, which)]

def exceedances(obs, key):
    """Events (year, key, direction, old, new, exceedance) in round order."""
    rec = {}; ev = []
    for y in YEARS[1:]:
        rnd = collections.defaultdict(list)
        for o in obs:
            if o[0] == y: rnd[key(o)].append(o[4])
        for k, v in rnd.items():
            for d, f in (("up", max), ("down", min)):
                m = f(v); old = rec.get((k, d))
                if old is None:
                    rec[(k, d)] = m
                elif (d == "up" and m > old) or (d == "down" and m < old):
                    ev.append((y, k, d, old, m, abs(m - old))); rec[(k, d)] = m
    return ev

def describe(xs):
    if not xs: return "n=0"
    xs = sorted(xs); n = len(xs)
    q = lambda f: xs[int(round(f * (n - 1)))]
    return (f"n={n} mean {100*statistics.mean(xs):.2f} median {100*statistics.median(xs):.2f} "
            f"sd {100*(statistics.pstdev(xs)):.2f} p25 {100*q(.25):.2f} p75 {100*q(.75):.2f} min {100*xs[0]:.2f} max {100*xs[-1]:.2f} pts")

if __name__ == "__main__":
    print("EXCLUSIONS DETECTED (kind, city, a, b, party, share, partner, r):")
    for e in EVIDENCE: print("  ", e)
    res = {}
    for which in ("all", "cope", "none"):
        W, C = ward_obs(which), city_obs(which)
        sets = {
            "ward, party-own (party, bin)": exceedances(W, lambda o: (o[2], o[3])),
            "ward, pooled (bin)": exceedances(W, lambda o: o[3]),
            "city, party-own (party)": exceedances(C, lambda o: o[2]),
            "city, pooled (bin)": exceedances(C, lambda o: o[3]),
        }
        res[which] = sets
        print(f"\n=== exclusions: {which}")
        for name, ev in sets.items():
            print(f" {name}: {describe([e[5] for e in ev])}")
            if "ward" in name:
                for bn in range(len(EDGES) - 1):
                    xs = [e[5] for e in ev if (e[1][1] if isinstance(e[1], tuple) else e[1]) == bn]
                    print(f"     bin ({EDGES[bn]:.2f},{EDGES[bn+1]:.2f}]: {describe(xs)}")
            for y in YEARS[2:]:
                xs = [e[5] for e in ev if e[0] == y]
                print(f"     at {y}: {describe(xs)}")
            # do exceedances shrink as the record grows?
            olds = [abs(e[3]) for e in ev]; xs = [e[5] for e in ev]
            print(f"     corr(|old record|, exceedance) = {corr(olds, xs):.2f}")
    json.dump({w: {k: v for k, v in s.items()} for w, s in res.items()}, open("records.json", "w"), default=str)
