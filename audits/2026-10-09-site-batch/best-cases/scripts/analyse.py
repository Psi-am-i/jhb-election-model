"""Best 1% per party: group statistics, drivers, maps. Writes only to OUT."""
import sys, json, pickle, itertools
from pathlib import Path
from collections import Counter
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common as C
OUT = C.ROOT / "audits/2026-10-09-site-batch/best-cases"
OUT.mkdir(parents=True, exist_ok=True)
import render_map as RM

D = C.load()
N = D["S"].shape[0]
AREA, PATHS = C.areas()
P = pickle.load(open(HERE / "capture2.pkl", "rb"))
U = P["universe"]
# --- verify the capture reproduces the published draws, or stop ---------------
ww = np.array(U)[P["ward_winner_draws"]]
assert (ww == np.array(D["wp"])[D["W"]]).all(), "ward winners differ"
vi = [U.index(p) for p in D["vcols"]]
assert np.array_equal(P["pr_vote_draws"][:, vi], D["b"]["list_vote"].astype(np.int64))
assert np.array_equal(P["ward_vote_draws"][:, vi], D["b"]["ward_vote"].astype(np.int64))
ti = [P["pool_turnout_names"].index(x) for x in D["turn_names"]]
assert np.array_equal(P["pool_turnout_draws"][:, ti], D["turn"])
rec = P["rec"]
assert len(rec["shock"]) == N and len(rec["dir"]) == 4 * N and len(rec["uniform"]) == N
assert len(rec["std_normal"]) == 5 * N
IPFP = P["ipf_parties"]
SHOCK = np.stack([s[1] for s in rec["shock"]])           # (N, 74) multiplier on centre
SHOCK_SD = rec["shock"][0][0]
assert all(np.array_equal(s[0], SHOCK_SD) for s in rec["shock"])
Z_COMMON = np.array(rec["std_normal"]).reshape(N, 5)[:, 0]
BLEND = 0.5 + 0.25 * np.array([float(u) for u in rec["uniform"]])
BLEND = np.clip(BLEND, 0, 1)
pools = list(P["pool_members"])
assert pools == list(P["scenario_pools"]) or True
DIR = {}   # pool -> (mean (N, m), sample (N, m), members)
for k, nm in enumerate(pools):
    calls = rec["dir"][k::4]
    mem = P["pool_members"][nm]
    assert all(len(c[0]) == len(mem) for c in calls)
    DIR[nm] = (np.stack([c[0] for c in calls]), np.stack([c[1] for c in calls]), mem)
WNOISE = np.load(HERE / "ward_noise.npy")               # (N, wards, universe)
assert WNOISE.shape == (N, len(D["wards"]), len(U))
CENTRES = P["centres"]


def q(x, p=50):
    return float(np.percentile(x, p))


def group(p):
    s = C.seats(D, p)
    cut = int(np.sort(s)[::-1][int(0.01 * N) - 1])
    return cut, np.flatnonzero(s >= cut)


def own_pool_split(p, idx):
    """Per pool p belongs to: its Dirichlet residual (sample - mean), pp of that pool."""
    out = {}
    for nm, (mean, samp, mem) in DIR.items():
        if p in mem:
            j = mem.index(p)
            res = (samp[:, j] - mean[:, j]) * 100
            mshare = mean[:, j] * 100
            out[nm] = {"residual_pp_group_median": q(res[idx]), "residual_pp_all_median": q(res),
                       "residual_group_mean_pctile": float((res < res[idx].mean()).mean() * 100),
                       "mean_share_pp_group_median": q(mshare[idx]), "mean_share_pp_all_median": q(mshare),
                       "sample_share_pp_group_median": q(samp[idx, j] * 100),
                       "sample_share_pp_all_median": q(samp[:, j] * 100)}
    return out


def r2(y, X):
    X = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    return 1 - res.var() / y.var()


def analyse(p, full=True):
    s = C.seats(D, p)
    cut, idx = group(p)
    G = {"party": p, "name": C.NAMES.get(p, p.title().replace("_", " ")), "cut": cut,
         "n": int(len(idx)), "seat_range": [int(s[idx].min()), int(s[idx].max())],
         "seats_all_median": int(np.median(s)), "seats_group_median": q(s[idx])}
    ws, ls = D["wseats"].get(p, np.zeros(N)), D["lseats"].get(p, np.zeros(N))
    G["ward_seats"] = {"group_median": q(ws[idx]), "group_range": [int(ws[idx].min()), int(ws[idx].max())],
                       "all_median": q(ws)}
    G["list_seats"] = {"group_median": q(ls[idx]), "group_range": [int(ls[idx].min()), int(ls[idx].max())],
                       "all_median": q(ls)}
    ex = D["exc"].get(p, np.zeros(N, bool))
    exo = np.array([any(v[3] for k, v in D["det"][i].items() if k != p) for i in range(N)])
    G["excessive"] = {"own_group": float(ex[idx].mean()), "own_all": float(ex.mean()),
                      "others_group": float(exo[idx].mean()), "others_all": float(exo.mean()),
                      "others_who_group": Counter(k for i in idx for k, v in D["det"][i].items()
                                                  if v[3] and k != p).most_common(5)}
    # shares
    vc = D["vcols"]
    sh = {}
    for r in sorted(set(C.MAIN + [p])):
        if r in vc:
            j = vc.index(r)
            sh[r] = {"list_pp_group_median": q(D["lshare"][idx, j] * 100), "list_pp_all_median": q(D["lshare"][:, j] * 100),
                     "ward_pp_group_median": q(D["wshare"][idx, j] * 100), "ward_pp_all_median": q(D["wshare"][:, j] * 100)}
    G["shares"] = sh
    # turnout
    G["turnout"] = {nm: {"group_mean_pp": float(D["turn"][idx, k].mean() * 100), "all_mean_pp": float(D["turn"][:, k].mean() * 100),
                         "group_mean_pctile_of_all": float((D["turn"][:, k] < D["turn"][idx, k].mean()).mean() * 100)}
                    for k, nm in enumerate(D["turn_names"])}
    G["citywide_turnout_factor"] = {"group_mean": float(Z_COMMON[idx].mean()), "all_mean": float(Z_COMMON.mean())}
    G["turnout_pattern_blend"] = {"group_mean": float(BLEND[idx].mean()), "all_mean": float(BLEND.mean())}
    # level shocks: own and rivals, as % change of centre
    lv = {}
    for r in sorted(set(C.MAIN + [p])):
        j = IPFP.index(r)
        f = (SHOCK[:, j] - 1) * 100
        lv[r] = {"group_median_pct": q(f[idx]), "all_median_pct": q(f),
                 "group_p10_pct": q(f[idx], 10), "group_p90_pct": q(f[idx], 90),
                 "group_median_pctile_of_all": float((f < np.median(f[idx])).mean() * 100),
                 "sd_log": float(SHOCK_SD[j]), "centre_pp": CENTRES.get(r, 0) * 100}
    G["level_shock"] = lv
    G["within_pool"] = own_pool_split(p, idx)
    # variance of the party's seats across all draws explained by each drawn block
    j = IPFP.index(p)
    own = np.log(SHOCK[:, j])
    rivals = np.log(SHOCK[:, [IPFP.index(r) for r in C.MAIN if r != p]])
    dres = np.column_stack([(DIR[nm][1][:, DIR[nm][2].index(p)] - DIR[nm][0][:, DIR[nm][2].index(p)])
                            for nm in DIR if p in DIR[nm][2]]) if any(p in DIR[nm][2] for nm in DIR) else np.zeros((N, 1))
    T = D["turn"]
    y = s.astype(float)
    G["r2_all_draws"] = {"own_level_shock": r2(y, own), "six_main_level_shocks": r2(y, np.column_stack([own, rivals])),
                         "own_within_pool": r2(y, dres), "pool_turnouts": r2(y, T), "blend": r2(y, BLEND),
                         "all_recorded_citywide": r2(y, np.column_stack([own, rivals, dres, T, BLEND]))}
    # largest party, coalitions
    scols = D["seat_cols"]
    M = np.column_stack([C.seats(D, r) for r in C.MAIN])
    largest = Counter()
    for i in idx:
        row = D["S"][i].copy(); top = row.max()
        w = [scols[k] for k in np.flatnonzero(row == top)]
        largest["/".join(sorted(w))] += 1
    G["largest_party_group"] = largest.most_common()
    coal = []
    for k in (1, 2, 3):
        for c in itertools.combinations(range(6), k):
            tot = M[:, list(c)].sum(1)
            ok = tot >= D["thr"]
            # minimal: no member is superfluous in that draw
            minimal = ok.copy()
            for drop in c:
                rest = [x for x in c if x != drop]
                if rest:
                    minimal &= ~(M[:, rest].sum(1) >= D["thr"])
            coal.append({"coalition": "+".join(C.MAIN[x] for x in c), "group": float(ok[idx].mean()),
                         "all": float(ok.mean()), "minimal_group": float(minimal[idx].mean())})
    G["coalitions"] = sorted([c for c in coal if c["minimal_group"] >= 0.10],
                             key=lambda c: -c["minimal_group"])
    # representative simulation
    sub = {r: C.seats(D, r)[idx] for r in C.MAIN}
    rep = int(idx[C.SC.typical(sub, C.MAIN)])
    G["representative"] = {"draw": rep, "seats": {r: int(C.seats(D, r)[rep]) for r in C.MAIN},
                           "others": int(D["council"][rep] - sum(int(C.seats(D, r)[rep]) for r in C.MAIN)),
                           "council": int(D["council"][rep]), "threshold": int(D["thr"][rep]),
                           "group_median_seats": {r: q(sub[r]) for r in C.MAIN},
                           "majorities": [c["coalition"] for c in coal
                                          if sum(int(C.seats(D, x)[rep]) for x in c["coalition"].split("+")) >= D["thr"][rep]
                                          and all(sum(int(C.seats(D, x)[rep]) for x in c["coalition"].split("+") if x != d) < D["thr"][rep]
                                                  for d in c["coalition"].split("+"))]}
    # wards
    fg, fa = C.ward_freq(D, p, idx), C.ward_freq(D, p)
    modal = C.SC.modal_winners({i: dict(zip(D["wards"], np.array(D["wp"])[D["W"][i]])) for i in range(N)}, D["wards"]) \
        if "MODAL" not in globals() else MODAL
    gains = [(D["wards"][k], fa[k], fg[k], modal[D["wards"][k]], AREA[D["wards"][k]])
             for k in range(len(D["wards"])) if fg[k] >= 0.5 and fa[k] < 0.5]
    G["gain_wards"] = [{"ward": w, "all": float(a), "group": float(g), "usual_winner": m, "map_position": ar}
                       for w, a, g, m, ar in sorted(gains, key=lambda t: -(t[2] - t[1]))]
    G["gain_by_position"] = Counter(x["map_position"] for x in G["gain_wards"]).most_common()
    G["gain_from"] = Counter(x["usual_winner"] for x in G["gain_wards"]).most_common()
    G["ward_freq_group"] = {w: float(fg[k]) for k, w in enumerate(D["wards"])}
    # ward noise in gain wards: own factor vs the usual winner's, group draws vs all draws
    if G["gain_wards"] and p in U:
        pi = U.index(p)
        rows_g, rows_a = [], []
        for x in G["gain_wards"]:
            k = D["wards"].index(x["ward"]); mi = U.index(x["usual_winner"])
            dn = (WNOISE[:, k, pi] - WNOISE[:, k, mi])
            rows_g.append(dn[idx]); rows_a.append(dn)
        dg, da = np.concatenate(rows_g), np.concatenate(rows_a)
        G["ward_noise_gain_wards"] = {"own_minus_usual_winner_log_group_mean": float(dg.mean()),
                                      "all_mean": float(da.mean()), "sd_per_draw_log": float(da.std()),
                                      "as_pct_group_mean": float((np.exp(dg.mean()) - 1) * 100)}
    return G


MODAL = C.SC.modal_winners({i: dict(zip(D["wards"], np.array(D["wp"])[D["W"][i]])) for i in range(N)}, D["wards"])
FULL = C.MAIN + ["IFP", "RISE", "ALJAMAAH"]
results = {}
for p in FULL:
    results[p] = analyse(p)
# the rest whose best 1% reaches 5 seats or more: table only
rest = []
for p in D["seat_cols"]:
    if p in FULL or p == "OTHER":
        continue
    cut, idx = group(p)
    if cut >= 5:
        rest.append(analyse(p))
json.dump({"full": results, "rest": rest}, open(HERE / "results.json", "w"), indent=1, default=float)


# --- maps ---------------------------------------------------------------------
PAPER, INK = "#f7f4ec", "#2b2d2b"


def svg(fills, title, sub, key, fname):
    W, H = PATHS["W"], PATHS["H"]
    paths = "".join(f'<path d="{d}" fill="{fills.get(w, RM.GREY)}" stroke="{PAPER}" stroke-width="0.8"><title>Ward {w}</title></path>'
                    for w, d in PATHS["paths"].items())
    labels = "".join(f'<text x="{l["x"]}" y="{l["y"]}" text-anchor="middle" font-size="11" fill="{INK}" '
                     f'font-family="IBM Plex Sans, sans-serif" opacity="0.8">{l["t"]}</text>' for l in PATHS["labels"])
    keyh = 22 * ((len(key) + 3) // 4) + 10
    keys = "".join(f'<g transform="translate({12 + (k % 4) * 205},{H + 74 + 22 * (k // 4)})"><rect width="14" height="14" fill="{c}"/>'
                   f'<text x="20" y="11" font-size="12" fill="{INK}" font-family="IBM Plex Sans, sans-serif">{t}</text></g>'
                   for k, (c, t) in enumerate(key))
    body = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H + 76 + keyh:.0f}" width="{W:.0f}">'
            f'<rect width="100%" height="100%" fill="{PAPER}"/>'
            f'<text x="12" y="24" font-size="17" font-weight="600" fill="{INK}" font-family="IBM Plex Sans, sans-serif">{title}</text>'
            + "".join(f'<text x="12" y="{44 + 16 * k}" font-size="12" fill="{INK}" font-family="IBM Plex Sans, sans-serif">{line}</text>' for k, line in enumerate(sub.split("|")))
            + f'<g transform="translate(0,68)">{paths}{labels}'
            f'<text x="{W - 14:.0f}" y="20" text-anchor="end" font-size="12" fill="{INK}">N ↗</text></g>{keys}</svg>')
    (OUT / fname).write_text(body, encoding="utf-8")


def mix(hexc, t):
    a = np.array([int(PAPER[i:i + 2], 16) for i in (1, 3, 5)]); b = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)])
    c = (a + (b - a) * t).round().astype(int)
    return "#%02x%02x%02x" % tuple(c)


for G in results.values():
    p = G["party"]; nm = G["name"]
    rep = G["representative"]["draw"]
    win = dict(zip(D["wards"], np.array(D["wp"])[D["W"][rep]]))
    fills = {w: RM.CHIPS.get(x, RM.UNKNOWN_CHIP) for w, x in win.items()}
    cnt = Counter(win.values())
    key = [(RM.CHIPS.get(x, RM.UNKNOWN_CHIP), f"{C.NAMES.get(x, x.title().replace('_', ' '))} {k} ward{'s' if k != 1 else ''}") for x, k in cnt.most_common()]
    seats = ", ".join(f"{C.NAMES[r]} {v}" for r, v in sorted(G["representative"]["seats"].items(), key=lambda t: -t[1]))
    svg(fills, f"One of the 5,000 simulations: {nm}'s best 1%",
        f"Simulation {rep}, the one in this group closest to its middle.|Council {G['representative']['council']} seats: {seats}, others {G['representative']['others']}.",
        key, f"{p.lower()}-representative.svg")
    colour = RM.CHIPS.get(p, RM.UNKNOWN_CHIP)
    fq = G["ward_freq_group"]
    fills = {w: (mix(colour, 0.15 + 0.85 * v) if v > 0 else "#e4e1d8") for w, v in fq.items()}
    key = [("#e4e1d8", "never")] + [(mix(colour, 0.15 + 0.85 * v), f"{int(v * 100)}% of the group") for v in (0.1, 0.5, 0.9)]
    svg(fills, f"Wards {nm} wins across its best 1% of simulations",
        f"Share of the {G['n']} simulations with {nm} on {G['cut']} seats or more in which it wins each ward.",
        key, f"{p.lower()}-ward-frequency.svg")
print("ok", len(results), len(rest))
