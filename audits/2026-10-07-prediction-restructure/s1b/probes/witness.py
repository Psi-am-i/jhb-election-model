"""B2 probe: the witness editor. A state carries a ward-share matrix X (ward x
party) inside every ward's polytope S_w; a party's slider moves X by a convex
combination toward that party's extreme points, so its range is exactly the
per-party box and every state reached is jointly feasible. Tests: exactness of
moves, the reconstruction of X from (calls, V) by sweeps of single-party moves,
and its cost in operations."""
import json, random, sys, time
sys.path.append("pylib")
import numpy as np
import ours as O
from ward_poly import ward_range

def fill(lo, cap, R, keys):
    room = sum(cap[q] - lo[q] for q in keys)
    x = {q: lo[q] for q in keys}
    if R > 1e-15:
        for q in keys:
            x[q] += R * (cap[q] - lo[q]) / room
    return x

def extremes(codes, lo, hi, W):
    """Per party p: (point where x_p is least, point where x_p is greatest), both in S_w."""
    ok, mins, maxs = ward_range(codes, lo, hi, W)
    assert ok
    oth = [c for c in codes if c != W]
    L = sum(lo[c] for c in oth)
    smax, smin = maxs[W], mins[W]
    pts = {}
    # winner
    cap = {q: min(hi[q], smin) for q in oth}
    a = fill(lo, cap, 1 - smin - L, oth); a[W] = smin
    cap = {q: min(hi[q], smax) for q in oth}
    b = fill(lo, cap, 1 - smax - L, oth); b[W] = smax
    pts[W] = (a, b)
    for p in oth:
        rest = [q for q in oth if q != p]
        Lp = L - lo[p]
        # least: winner at smax, p at mins[p], the rest to their caps
        cap = {q: min(hi[q], smax) for q in rest}
        a = fill(lo, cap, 1 - smax - mins[p] - Lp, rest); a[W] = smax; a[p] = mins[p]
        # greatest: p at maxs[p], winner at the largest sigma allowed, the rest filled
        u = maxs[p]
        sig = min(hi[W], 1 - u - Lp)
        cap = {q: min(hi[q], sig) for q in rest}
        b = fill(lo, cap, 1 - sig - u - Lp, rest); b[W] = sig; b[p] = u
        pts[p] = (a, b)
    return pts

class Editor:
    def __init__(self, codes, wards, per, calls, e):
        self.codes, self.wards, self.calls = codes, wards, calls
        self.e = np.array([e[w] for w in wards])
        P = len(codes); self.ix = {c: i for i, c in enumerate(codes)}
        self.Ymin = np.zeros((P, len(wards), P)); self.Ymax = np.zeros((P, len(wards), P))
        self.lo = np.zeros((len(wards), P)); self.hi = np.zeros((len(wards), P))
        for wi, w in enumerate(wards):
            lo, hi = per[w]
            for c in codes:
                self.lo[wi, self.ix[c]] = lo[c]; self.hi[wi, self.ix[c]] = hi[c]
            pts = extremes(codes, lo, hi, calls[w])
            for p, (a, b) in pts.items():
                self.Ymin[self.ix[p], wi] = [a[c] for c in codes]
                self.Ymax[self.ix[p], wi] = [b[c] for c in codes]
        self.floor = np.einsum("w,pw->p", self.e, self.Ymin[np.arange(P), :, np.arange(P)])
        self.ceil = np.einsum("w,pw->p", self.e, self.Ymax[np.arange(P), :, np.arange(P)])
        self.X = (self.Ymin.mean(0) + self.Ymax.mean(0)) / 2      # a start inside every S_w

    def V(self):
        return self.e @ self.X

    def move(self, p, t):
        i = self.ix[p]; v = self.V()[i]
        t = min(max(t, self.floor[i]), self.ceil[i])
        if abs(t - v) < 1e-15:
            return
        Y, end = (self.Ymax[i], self.ceil[i]) if t > v else (self.Ymin[i], self.floor[i])
        lam = (t - v) / (end - v)
        self.X = (1 - lam) * self.X + lam * Y

    def check(self):
        X = self.X; ok = np.all(X >= self.lo - 1e-9) and np.all(X <= self.hi + 1e-9)
        ok &= np.allclose(X.sum(1), 1)
        win = np.array([self.ix[self.calls[w]] for w in self.wards])
        ok &= np.all(X[np.arange(len(self.wards)), win][:, None] >= X - 1e-9)
        return bool(ok)

    def reconstruct(self, V, sweeps=200, tol=1e-5):
        """Sweeps of single-party moves toward V, largest gap first."""
        Vt = np.array([V[c] for c in self.codes])
        for s in range(sweeps):
            gap = Vt - self.V()
            if np.max(np.abs(gap)) < tol:
                return s, float(np.max(np.abs(gap)))
            for i in np.argsort(-np.abs(gap)):
                self.move(self.codes[i], Vt[i])
        return sweeps, float(np.max(np.abs(Vt - self.V())))

if __name__ == "__main__":
    per, qw, qr, D, N = O.build("ext", True)
    pm = O.apply_map(per, O.calls, qw, qr, True)
    t0 = time.time(); ed = Editor(O.codes, O.wards, pm, O.calls, O.e); t1 = time.time()
    print(f"build: {t1-t0:.2f}s python; inside after start: {ed.check()}")
    # exactness of a single move
    rng = random.Random(5); worst = 0
    for k in range(200):
        p = rng.choice(O.codes); i = ed.ix[p]
        t = ed.floor[i] + rng.random() * (ed.ceil[i] - ed.floor[i])
        ed.move(p, t); worst = max(worst, abs(ed.V()[i] - t))
        assert ed.check(), "left the joint set"
    print(f"200 random moves: every state inside; worst miss of the asked value {worst:.2e}")
    # reconstruction of rule A
    for name, V in [("rule A", O.VA)]:
        ed2 = Editor(O.codes, O.wards, pm, O.calls, O.e)
        s, g = ed2.reconstruct(V)
        print(f"reconstruct {name}: sweeps {s}, worst gap {100*g:.4f} points, inside {ed2.check()}")
    # reconstruction of states known to be feasible (made by random moves)
    res = []
    for k in range(20):
        ed3 = Editor(O.codes, O.wards, pm, O.calls, O.e)
        for m in range(60):
            p = rng.choice(O.codes); i = ed3.ix[p]
            ed3.move(p, ed3.floor[i] + rng.random() * (ed3.ceil[i] - ed3.floor[i]))
        V = dict(zip(O.codes, ed3.V()))
        ed4 = Editor(O.codes, O.wards, pm, O.calls, O.e)
        res.append(ed4.reconstruct(V))
    print("reconstruct 20 feasible states: (sweeps, worst gap points):", [(s, round(100 * g, 4)) for s, g in res])
    edS = Editor(O.codes, O.wards, pm, O.calls, O.e)
    import json
    shot = dict(O.__dict__.get("VS_", {})) or None
