"""B2a's limits (box intersected with the citywide limit), rule A's map: moves
anywhere in a slider's range, others rescaled in proportion inside their
limits; joint LP on each state. And moves of up to 10 points."""
import io, contextlib, random, sys
sys.path.append("pylib")
import b2r2, b2bt as B
with contextlib.redirect_stdout(io.StringIO()):
    per, city, pm, fl, ce, calls, e, codes, wards, VA = b2r2.year2026()
lo, hi, conf = b2r2.b2a_limits(fl, ce, city, codes)
def rescale(v, p, t):
    others = [c for c in codes if c != p]; R = 1 - t
    at = lambda k: sum(min(hi[c], max(lo[c], k * v[c])) for c in others)
    a, b = 0.0, 1.0
    while at(b) < R: b *= 2
    for _ in range(100):
        m = (a + b) / 2
        if at(m) < R: a = m
        else: b = m
    out = {c: min(hi[c], max(lo[c], b * v[c])) for c in others}; out[p] = t; return out
big = [c for c in codes if VA[c] > 0.005]
for label, wide in (("anywhere in range", True), ("up to 10 points", False)):
    rng = random.Random(2); res = []
    for k in range(4):
        v = dict(VA)
        for s in range(25):
            p = rng.choice(big)
            l = max(lo[p], 1 - sum(hi[c] for c in codes if c != p)); h = min(hi[p], 1 - sum(lo[c] for c in codes if c != p))
            t = l + rng.random() * (h - l) if wide else v[p] + (rng.random() - .5) * .2
            v = rescale(v, p, min(h, max(l, t)))
            res.append(B.joint_lp(codes, wards, pm, calls, e, v))
    srt = sorted(x or 0 for x in res)
    print(f"B2a, moves {label}: {len(res)} states, jointly infeasible {sum(1 for x in res if x is None or x > 1e-6)}; median slack {srt[len(srt)//2]}, max {srt[-1]} points")
