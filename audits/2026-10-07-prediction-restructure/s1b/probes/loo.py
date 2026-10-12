"""SPEC-B2r2 probe: is the mean record exceedance a sound allowance?
Leave-one-election-out and causal (events before Y only). For each held-out
election Y: bin extremes from pairs ending before Y (all stood-both swings,
as the bounds are built), widened by the allowance A; count real stood-both
swings at Y outside, ward level and citywide."""
import statistics, collections
import records as R
import b2bt as B
import cityswing as CS
YS = ["2011", "2016", "2021"]

def stat(xs, how):
    if not xs: return None
    xs = sorted(xs)
    return {"mean": statistics.mean(xs), "median": statistics.median(xs),
            "p75": xs[int(round(.75 * (len(xs) - 1)))], "max": xs[-1]}[how]

def extremes(obs, before):
    d = collections.defaultdict(lambda: [1, -1])
    for y, c, p, bn, sw in obs:
        if y < before:
            d[bn][0] = min(d[bn][0], sw); d[bn][1] = max(d[bn][1], sw)
    allv = [x for v in d.values() for x in v]
    for bn in range(len(B.EDGES) - 1):
        if bn not in d: d[bn] = [min(allv), max(allv)]
    return d

def outside(obs, Y, A):
    ext = extremes(obs, Y); n = o = 0
    for y, c, p, bn, sw in obs:
        if y != Y: continue
        n += 1; o += sw < ext[bn][0] - A or sw > ext[bn][1] + A
    return o, n

WALL = R.ward_obs("none"); CALL = R.city_obs("none")      # what the bounds are built from
for level, obs, evsets in (("ward", WALL, {"pooled": R.exceedances(R.ward_obs("all"), lambda o: o[3]),
                                             "party-own": R.exceedances(R.ward_obs("all"), lambda o: (o[2], o[3]))}),
                           ("city", CALL, {"pooled": R.exceedances(R.city_obs("all"), lambda o: o[3]),
                                           "party-own": R.exceedances(R.city_obs("all"), lambda o: o[2])})):
    print(f"\n=== {level} level: real stood-both swings outside bin extremes (pairs before Y) +/- A")
    for Y in YS:
        o, n = outside(obs, Y, 0.0); print(f"  {Y}: A=0 -> {o}/{n};  flat 5 -> {outside(obs, Y, .05)[0]}/{n}")
        for scope, ev in evsets.items():
            for how in ("mean", "median", "p75", "max"):
                loo = stat([e[5] for e in ev if e[0] != Y], how)
                cau = stat([e[5] for e in ev if e[0] < Y], how)
                lo = outside(obs, Y, loo)[0]
                ca = "n/a" if cau is None else f"{100*cau:.2f} -> {outside(obs, Y, cau)[0]}/{n}"
                print(f"    {scope:9s} {how:6s}: LOO A={100*loo:.2f} -> {lo}/{n} | causal A={ca}")
