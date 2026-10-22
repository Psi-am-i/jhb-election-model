"""Realistic editor population: slice-B-style moves (one party set inside its
box range, the others rescaled in proportion inside their own box) from rule
A's state on rule A's map, ext+sb ranges. Each state checked by the joint LP."""
import random, sys
sys.path.append("pylib")
import ours as O, b2bt as B
per, qw, qr, D, N = O.build("ext", True); pm = O.apply_map(per, O.calls, qw, qr, True)
fl, ce, bad = O.box(pm, O.calls)
codes = O.codes
def rescale(v, p, t):
    others = [c for c in codes if c != p]; R = 1 - t
    def at(k): return sum(min(ce[c], max(fl[c], k * v[c])) for c in others)
    a, b = 0.0, 1.0
    while at(b) < R: b *= 2
    for _ in range(100):
        m = (a + b) / 2
        if at(m) < R: a = m
        else: b = m
    out = {c: min(ce[c], max(fl[c], b * v[c])) for c in others}; out[p] = t
    return out
rng = random.Random(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
walks, steps = int(sys.argv[2]) if len(sys.argv) > 2 else 4, int(sys.argv[3]) if len(sys.argv) > 3 else 25
res = []
big = [c for c in codes if O.VA[c] > 0.005]
for k in range(walks):
    v = dict(O.VA)
    for s in range(steps):
        p = rng.choice(big)                 # readers move the visible parties
        lo = max(fl[p], 1 - sum(ce[c] for c in codes if c != p)); hi = min(ce[p], 1 - sum(fl[c] for c in codes if c != p))
        t = lo + rng.random() * (hi - lo)   # anywhere in the range
        t = min(hi, max(lo, t))
        v = rescale(v, p, t)
        sl = B.joint_lp(codes, O.wards, pm, O.calls, O.e, v)
        res.append(sl)
inf = [x for x in res if x is None or x > 1e-6]
srt = sorted(x or 0 for x in res)
print(f"states {len(res)} (walks {walks} x steps {steps}, moves anywhere in the slider range, rule A's map): jointly infeasible {len(inf)}; "
      f"slack median {srt[len(srt)//2]} p90 {srt[int(.9*len(srt))]} max {srt[-1]} points")
