"""The per-ward polytope S_w = {lo <= x <= hi, sum x = 1, x_W >= x_q for all q}
and each party's min and max over it, in closed form (no LP). This is the
function the design ports to builder-state.js; plain Python on purpose."""


def _g(sigma, his):
    """sigma plus the most the non-winners can hold when capped at sigma."""
    return sigma + sum(min(h, sigma) for h in his)


def _sigma_min(a, his):
    """Smallest sigma >= a with sigma + sum(min(hi_q, sigma)) >= 1."""
    if _g(a, his) >= 1:
        return a
    # g is piecewise linear increasing; walk the breakpoints above a
    pts = sorted(h for h in his if h > a)
    lo = a
    for b in pts + [1.0]:
        if _g(b, his) >= 1:
            # g linear on [lo, b] with slope 1 + #(hi_q > lo... ) -> solve
            k = 1 + sum(1 for h in his if h > lo + 1e-15)
            return lo + (1 - _g(lo, his)) / k
        lo = b
    return 1.0


def ward_range(codes, lo, hi, W):
    """(feasible, mins, maxs) for one ward whose painted winner is W."""
    oth = [c for c in codes if c != W]
    L = sum(lo[c] for c in oth)
    his = [hi[c] for c in oth]
    a = max([lo[W]] + [lo[c] for c in oth])
    smax = min(hi[W], 1 - L)
    smin = _sigma_min(a, his)
    if smin > smax + 1e-12:
        return False, None, None
    capmax = sum(min(hi[c], smax) for c in oth)
    mins, maxs = {W: smin}, {W: smax}
    for p in oth:
        Lp = L - lo[p]
        rest_lo = max([lo[W]] + [lo[c] for c in oth if c != p])
        mins[p] = max(lo[p], 1 - smax - (capmax - min(hi[p], smax)))
        best = lo[p]
        # s_p <= sigma, s_p + sigma <= 1 - Lp, sigma in [rest_lo, hi_W], s_p <= hi_p
        s_star = min(max((1 - Lp) / 2, rest_lo), hi[W])
        u = min(hi[p], s_star, 1 - s_star - Lp)
        # when hi_p binds, the others must still be able to absorb: pick the
        # largest sigma allowed for that u and check absorption
        if u >= lo[p]:
            sig = min(hi[W], 1 - u - Lp)
            sig = max(sig, rest_lo, u)
            rest_his = [hi[c] for c in oth if c != p]
            if sig + u + sum(min(h, sig) for h in rest_his) >= 1 - 1e-12 and sig <= hi[W] + 1e-12:
                best = u
            else:  # absorption binds: raise u until the others can take the rest
                best = max(lo[p], 1 - sig - sum(min(h, sig) for h in rest_his))
                best = min(best, hi[p], sig)
        maxs[p] = max(best, mins[p])
    return True, mins, maxs
