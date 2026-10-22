"""B2 backtest: ward-by-ward ranges vs slice B's bounds, 24 city-years
(2011, 2016, 2021 x 8 metros), each built only from elections before it.

Ranges for party p in target ward w, h = p's ward-ballot share there at the
preceding LGE (previous VDs joined onto the target's wards):
  h > 0 : [h + Dlo(bin(h)) - widen, h + Dhi(bin(h)) + widen], clipped to [0, 1]
  h = 0 : [0, N + widen]          (a party new to the ward)
  ward with no prior record: [0, 1]
Dlo/Dhi/N from the transitions (a -> b) with b < target, over (ward, party)
pairs where the party stood both times (h > 0 and s > 0); N over pairs with
h = 0 and s > 0. stat: extremes, or percentiles."""
import collections, json, sys
sys.path.append("pylib")
from load import all_data, ward_shares, prior_on, parts_of, CITIES, YEARS, SCRATCH
from ward_poly import ward_range

EDGES = [0.0, 0.01, 0.05, 0.15, 0.35, 0.60, 1.0001]
def bin_of(h):
    for i in range(len(EDGES) - 1):
        if EDGES[i] < h <= EDGES[i + 1] or (i == 0 and h <= EDGES[1]):
            return i
    return len(EDGES) - 2

data = all_data()
OUTLIST = []
def city_prior(c, y):
    acc = collections.Counter()
    for d in data[(c, y)][0].values():
        acc.update(d["wv"])
    t = sum(acc.values())
    return {p: v / t for p, v in acc.items() if v}
TRANS = []  # (city, a, b, ward, party, h, s, Hcity_prev)
for c in CITIES:
    for a, b in zip(YEARS, YEARS[1:]):
        h, _, _ = prior_on(parts_of(data[(c, b)][0]), data[(c, a)][0])
        s, _, _ = ward_shares(data[(c, b)][0])
        HC = city_prior(c, a)
        for w in s:
            if w not in h:
                continue
            for p in set(h[w]) | set(s[w]):
                if p == "IND":
                    continue
                TRANS.append((c, a, b, w, p, h[w].get(p, 0.0), s[w].get(p, 0.0), HC.get(p, 0.0)))

def q(xs, f):
    xs = sorted(xs); return xs[int(round(f * (len(xs) - 1)))]

def allowance(before, stat):
    """{bin: (Dlo, Dhi)}, N, population counts; from transitions with b < before."""
    rows = [r for r in TRANS if r[2] < before]
    by = collections.defaultdict(list); new = []
    for r in rows:
        if r[5] > 0 and r[6] > 0:
            by[bin_of(r[5])].append(r[6] - r[5])
        elif r[5] == 0 and r[6] > 0 and r[7] == 0:     # new to the city
            new.append(r[6])
    lo_f, hi_f = {"ext": (0, 1), "p01": (.01, .99), "p05": (.05, .95)}[stat]
    D = {i: (q(v, lo_f), q(v, hi_f)) for i, v in by.items()}
    for i in range(len(EDGES) - 1):          # an empty bin borrows the widest
        if i not in D:
            D[i] = (min(x[0] for x in D.values()), max(x[1] for x in D.values()))
    return D, q(new, hi_f), {i: len(v) for i, v in by.items()}, len(new)

def ranges(prior_w, roster, D, N, widen, Hc=None):
    lo, hi = {}, {}
    for p in roster:
        h = prior_w.get(p, 0.0) if prior_w is not None else None
        if h == 0.0 and Hc and Hc.get(p, 0) > 0:      # absent from this ward, stood in the city
            h = Hc[p]
        if h is None:
            lo[p], hi[p] = 0.0, 1.0
        elif h > 0:
            dl, dh = D[bin_of(h)]
            lo[p], hi[p] = max(0.0, h + dl - widen), min(1.0, h + dh + widen)
        else:
            lo[p], hi[p] = 0.0, min(1.0, N + widen)
    return lo, hi

def slice_b_extremes(before):
    """q_win, q_run over every metro LGE file before `before` (build_make.panel_extremes' rule)."""
    win, run = 1.0, 0.0
    for c in CITIES:
        for y in YEARS:
            if y >= before:
                continue
            s, _, _ = ward_shares(data[(c, y)][0])
            for w, sh in s.items():
                v = sorted(sh.values(), reverse=True)
                win = min(win, v[0]); run = max(run, v[1] if len(v) > 1 else 0)
    return max(0.0, win - .05), min(.5, run + .05)

def city_year(c, T, stat, widen=0.05, lp_check=False, combine=True):
    prevY = YEARS[YEARS.index(T) - 1]
    vds, _ = data[(c, T)]
    s, tot, reg = ward_shares(vds)
    h, cov, turn = prior_on(parts_of(vds), data[(c, prevY)][0])
    roster = sorted({p for w in s for p in s[w]})           # who stood anywhere at T
    D, N, nb, nn = allowance(T, stat)
    # e: the target roll x the preceding election's turnout (build_make.expected_ward_shares' rule)
    exp = {w: reg[w] * turn.get(w, sum(turn.values()) / len(turn)) for w in s}
    E = sum(exp.values()); e = {w: exp[w] / E for w in s}
    A = sum(tot.values()); a = {w: tot[w] / A for w in s}   # hindsight weights
    winner = {w: max(s[w], key=s[w].get) for w in s}
    out = collections.Counter()
    fl = collections.Counter(); ce = collections.Counter(); fla = collections.Counter(); cea = collections.Counter()
    infeasible = []
    perward = {}
    qw, qr = slice_b_extremes(T)
    HCT = city_prior(c, prevY)
    for w in s:
        lo, hi = ranges(h.get(w), roster, D, N, widen, HCT)
        W0 = winner[w]
        if combine:
            lo[W0] = max(lo[W0], qw)
            for p in roster:
                if p != W0:
                    hi[p] = min(hi[p], qr)
        if not ward_range(roster, lo, hi, W0)[0]:     # the slice B shape alone: always feasible
            infeasible.append(w)
            lo = {p: 0.0 for p in roster}; hi = {p: qr for p in roster}; lo[W0] = qw; hi[W0] = 1.0
        perward[w] = (lo, hi)
        for p in roster:
            sp, hp = s[w].get(p, 0.0), (h.get(w) or {}).get(p, 0.0)
            if p == "IND" or (sp == 0 and hp == 0):
                continue
            out["pairs"] += 1
            if sp < lo[p] - 1e-12 or sp > hi[p] + 1e-12:
                kind = "notstood" if sp == 0 else ("new" if hp == 0 else "stood")
                out["out_" + kind] += 1
                OUTLIST.append((c, T, w, p, kind, round(hp, 3), round(sp, 3), round(lo[p], 3), round(hi[p], 3), p == winner[w]))
                if p == winner[w]:
                    out["out_winner"] += 1
        ok, mins, maxs = ward_range(roster, lo, hi, winner[w])
        assert ok
        for p in roster:
            fl[p] += e[w] * mins[p]; ce[p] += e[w] * maxs[p]
            fla[p] += a[w] * mins[p]; cea[p] += a[w] * maxs[p]
    V = collections.Counter()
    for w in s:
        for p, v in s[w].items():
            V[p] += a[w] * v
    # slice B
    won = collections.Counter(); wona = collections.Counter()
    for w in s:
        won[winner[w]] += e[w]; wona[winner[w]] += a[w]
    sb_ward_out = 0; sb_pairs = 0
    for w in s:
        for p in roster:
            sp, hp = s[w].get(p, 0.0), (h.get(w) or {}).get(p, 0.0)
            if p == "IND" or (sp == 0 and hp == 0):
                continue
            sb_pairs += 1
            if (p == winner[w] and sp < qw) or (p != winner[w] and sp > qr):
                sb_ward_out += 1
    res = {"city": c, "T": T, "stat": stat + ("+sb" if combine else ""), "wards": len(s), "pairs": out["pairs"],
           "ward_out": out["out_stood"] + out["out_new"] + out["out_notstood"],
           "ward_out_stood": out["out_stood"], "ward_out_new": out["out_new"],
           "ward_out_notstood": out["out_notstood"], "ward_out_winner": out["out_winner"],
           "infeasible_wards": len(infeasible), "sb_pairs": sb_pairs, "sb_ward_out": sb_ward_out}
    def cnt(F, C, big):
        return sum(1 for p in roster if (V[p] >= .01 or not big) and (V[p] < F[p] - 1e-9 or V[p] > C[p] + 1e-9))
    def sbF(wn, p): return qw * wn[p]
    def sbC(wn, p): return wn[p] + qr * (1 - wn[p])
    res.update({
        "parties": len(roster), "parties_ge1": sum(1 for p in roster if V[p] >= .01),
        "city_out_e": cnt(fl, ce, False), "city_out_e_ge1": cnt(fl, ce, True),
        "city_out_hind": cnt(fla, cea, False),
        "sb_city_out_e": sum(1 for p in roster if V[p] < sbF(won, p) - 1e-9 or V[p] > sbC(won, p) + 1e-9),
        "sb_city_out_e_ge1": sum(1 for p in roster if V[p] >= .01 and (V[p] < sbF(won, p) - 1e-9 or V[p] > sbC(won, p) + 1e-9)),
        "sb_city_out_hind": sum(1 for p in roster if V[p] < sbF(wona, p) - 1e-9 or V[p] > sbC(wona, p) + 1e-9),
        "which_out_e": sorted([(p, round(100 * V[p], 2), round(100 * fl[p], 2), round(100 * ce[p], 2)) for p in roster
                               if V[p] < fl[p] - 1e-9 or V[p] > ce[p] + 1e-9], key=lambda x: -x[1])[:6],
        "sb_which_out_e": sorted([(p, round(100 * V[p], 2), round(100 * sbF(won, p), 2), round(100 * sbC(won, p), 2))
                                  for p in roster if V[p] < sbF(won, p) - 1e-9 or V[p] > sbC(won, p) + 1e-9],
                                 key=lambda x: -x[1])[:6],
        "width_big": {p: (round(100 * fl[p], 1), round(100 * V[p], 1), round(100 * ce[p], 1),
                          round(100 * sbF(won, p), 1), round(100 * sbC(won, p), 1))
                      for p in sorted(roster, key=lambda p: -V[p])[:4]},
        "n_bins": nb, "n_new": nn,
    })
    if lp_check:
        res["joint_feasible_e"] = joint_lp(roster, list(s), perward, winner, e, V)
    return res

def joint_lp(roster, wards, perward, winner, wt, V):
    """Is V (citywide ward shares) inside the joint set: x_wp in ranges, ward sums 1,
    winner >= each other, sum_w wt_w x_wp = V_p?  Slack-minimising LP: returns
    the least total |violation| of the citywide equalities (0 = feasible)."""
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import lil_matrix
    P = len(roster); Wn = len(wards); n = Wn * P; ns = 2 * P
    idx = lambda wi, pi: wi * P + pi
    bounds = []
    for w in wards:
        lo, hi = perward[w]
        bounds += [(lo[p], hi[p]) for p in roster]
    bounds += [(0, None)] * ns
    c = np.zeros(n + ns); c[n:] = 1
    Aeq = lil_matrix((Wn + P, n + ns)); beq = []
    for wi in range(Wn):
        for pi in range(P):
            Aeq[wi, idx(wi, pi)] = 1
        beq.append(1)
    for pi, p in enumerate(roster):
        for wi, w in enumerate(wards):
            Aeq[Wn + pi, idx(wi, pi)] = wt[w]
        Aeq[Wn + pi, n + 2 * pi] = 1; Aeq[Wn + pi, n + 2 * pi + 1] = -1
        beq.append(V[p])
    rows = Wn * (P - 1)
    Aub = lil_matrix((rows, n + ns)); r = 0
    for wi, w in enumerate(wards):
        iw = roster.index(winner[w])
        for pi in range(P):
            if pi == iw:
                continue
            Aub[r, idx(wi, pi)] = 1; Aub[r, idx(wi, iw)] = -1; r += 1
    res = linprog(c, A_ub=Aub.tocsr(), b_ub=np.zeros(rows), A_eq=Aeq.tocsr(), b_eq=beq,
                  bounds=bounds, method="highs")
    return None if res.status != 0 else round(100 * res.fun, 3)

if __name__ == "__main__":
    stats = sys.argv[1:] or ["ext", "p01", "p05"]
    allres = []
    for stat in stats:
      for comb in (False, True):
        for T in ["2011", "2016", "2021"]:
            for c in CITIES:
                r = city_year(c, T, stat, lp_check=True, combine=comb)
                allres.append(r)
                print(json.dumps({k: r[k] for k in r if k not in ("width_big",)}))
    json.dump(allres, open(SCRATCH + "/backtest_" + "_".join(stats) + ".json", "w"), indent=1)
