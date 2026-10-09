"""Oracle check: ward_range's closed form against scipy linprog on random wards."""
import random, sys
sys.path.append("pylib")
from scipy.optimize import linprog
from ward_poly import ward_range

def lp(codes, lo, hi, W, p, sense):
    n = len(codes); iW = codes.index(W); ip = codes.index(p)
    c = [0.0] * n; c[ip] = 1.0 if sense == "min" else -1.0
    A = []; b = []
    for i in range(n):
        if i != iW:
            r = [0.0] * n; r[i] = 1; r[iW] = -1; A.append(r); b.append(0)
    res = linprog(c, A_ub=A or None, b_ub=b or None, A_eq=[[1.0] * n], b_eq=[1.0],
                  bounds=[(lo[x], hi[x]) for x in codes], method="highs")
    return None if res.status != 0 else (res.fun if sense == "min" else -res.fun)

rng = random.Random(11)
bad = 0; feas_disagree = 0; n = 0
for t in range(400):
    k = rng.randint(10, 40)
    codes = [f"P{i}" for i in range(k)]
    lo, hi = {}, {}
    for c in codes:
        a = rng.random() ** 3 * 0.3; b = a + rng.random() * 0.7
        if rng.random() < 0.3: a = 0.0
        lo[c] = a; hi[c] = min(1.0, b)
    W = rng.choice(codes)
    ok, mins, maxs = ward_range(codes, lo, hi, W)
    ref = lp(codes, lo, hi, W, W, "min")
    if (ref is not None) != ok:
        feas_disagree += 1; continue
    if not ok:
        continue
    for p in codes:
        n += 1
        a, b = lp(codes, lo, hi, W, p, "min"), lp(codes, lo, hi, W, p, "max")
        if abs(a - mins[p]) > 1e-7 or abs(b - maxs[p]) > 1e-7:
            bad += 1
            if bad <= 5:
                print("MISMATCH", p == W, codes, lo, hi, W, p, (mins[p], a), (maxs[p], b))
print(f"random wards 3000; feasibility disagreements {feas_disagree}; party min/max checked {n}; mismatches {bad}")
