"""B2a with repainting: each step repaints 10 random wards to one of the
parties with a ward on rule A's map, or moves a slider anywhere in its range;
limits recomputed for the new map; joint LP on each state."""
import io, contextlib, random, sys
sys.path.append("pylib")
import b2r2, b2bt as B
with contextlib.redirect_stdout(io.StringIO()):
    per, city, pm, fl, ce, calls, e, codes, wards, VA = b2r2.year2026()
qw, qr, _, _ = b2r2.shape_bounds("2026")
painters = sorted(set(calls.values())) + ["ASA"]
rng = random.Random(9); res = []; conflicts = 0; SUMLO = []
v = dict(VA); cl = dict(calls)
for step in range(100):
    if rng.random() < 0.4:
        P = rng.choice(painters)
        for w in rng.sample(wards, 10): cl[w] = P
    pm2, fl2, ce2, fb = b2r2.shape_and_box(per, codes, wards, e, cl, qw, qr)
    lo, hi, conf = b2r2.b2a_limits(fl2, ce2, city, codes); conflicts += bool(conf); SUMLO.append(sum(lo.values()))
    # clamp into the limits (others rescaled), then move one party anywhere in range
    p = rng.choice([c for c in codes if VA[c] > 0.005])
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
    l = max(lo[p], 1 - sum(hi[c] for c in codes if c != p)); h = min(hi[p], 1 - sum(lo[c] for c in codes if c != p))
    v = rescale(v, p, l + rng.random() * (h - l))
    res.append(B.joint_lp(codes, wards, pm2, cl, e, v))
srt = sorted(x or 0 for x in res)
print(f"B2a with repaints: {len(res)} states, jointly infeasible {sum(1 for x in res if x is None or x > 1e-6)}; median {srt[len(srt)//2]}, p90 {srt[89]}, max {srt[-1]} points; steps with a map/limit conflict {conflicts}; max sum of lower limits {max(SUMLO):.3f}, steps with sum > 1: {sum(1 for x in SUMLO if x > 1)}")
