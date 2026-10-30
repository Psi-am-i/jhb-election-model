"""Compare the arms B, N, E written by run_arm.py. Writes results.json and
seats.csv / wards.csv here. Reads nothing under data/.

Paired Monte Carlo error: one draw-index resample (with replacement) applied
jointly to every arm, arms.MC_RESAMPLES times with arms.MC_SEED; the error is
the standard deviation of the statistic over the resamples.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / "src"))
import arms as A  # noqa: E402
import reweight  # noqa: E402

ARMS = [a for a in ("B", "N", "E") if (HERE / a / "arrays.npz").exists()]
MAIN = ["DA", "ANC", "ASA", "EFF", "MK", "PA"]


def load(arm):
    z = np.load(HERE / arm / "arrays.npz")
    m = json.loads((HERE / arm / "meta.json").read_text())
    return dict(seats=z["seat_draws"], ww=z["ward_winner_draws"], meta=m)


R = {a: load(a) for a in ARMS}
b = R["B"]
U = b["meta"]["universe"]; W = b["meta"]["wards"]
for a in ARMS:
    m = R[a]["meta"]
    assert m["universe"] == U and m["wards"] == W, a
    assert m["draws"] == b["meta"]["draws"] and m["seed"] == b["meta"]["seed"], a
    assert m["commit"] == b["meta"]["commit"] and not m["src_dirty"], a
    assert m["width_record_key"] == b["meta"]["width_record_key"], a
    assert m["width_record_variant"] == b["meta"]["width_record_variant"], a
D = b["seats"].shape[0]
P = len(U)


def win_probs(ww, idx=None):
    """(wards, parties) probability of winning each ward."""
    x = ww if idx is None else ww[idx]
    out = np.zeros((x.shape[1], P))
    for j in range(x.shape[1]):
        out[j] = np.bincount(x[:, j], minlength=P) / x.shape[0]
    return out


def largest(seats):
    r = reweight.largest_party(seats, U)
    return np.array([r["outright"][p] for p in U]), r["tied"]


S = {a: dict(mean=R[a]["seats"].mean(0),
             p5=np.percentile(R[a]["seats"], 5, axis=0),
             p95=np.percentile(R[a]["seats"], 95, axis=0),
             largest=largest(R[a]["seats"]),
             wp=win_probs(R[a]["ww"]),
             majority=float((R[a]["seats"].max(1) >= np.asarray(
                 np.load(HERE / a / "arrays.npz")["thresholds"])).mean()))
     for a in ARMS}

rng = np.random.default_rng(A.MC_SEED)
boots = [rng.integers(0, D, D) for _ in range(A.MC_RESAMPLES)]


def boot(fn):
    return np.std([fn(i) for i in boots], axis=0, ddof=1)


res = {"draws": D, "seed": b["meta"]["seed"], "commit": b["meta"]["commit"],
       "arms": ARMS, "mc_resamples": A.MC_RESAMPLES, "mc_seed": A.MC_SEED,
       "citywide_mix": {a: R[a]["meta"]["citywide_mix"] for a in ARMS},
       "per_arm": {}, "delta": {}}
big = [p for p in U if max(S[a]["mean"][U.index(p)] for a in ARMS) >= 0.5]
for a in ARMS:
    s = S[a]
    res["per_arm"][a] = {
        "mean_seats": {p: round(float(s["mean"][U.index(p)]), 3) for p in big},
        "p5_p95": {p: [float(s["p5"][U.index(p)]), float(s["p95"][U.index(p)])]
                   for p in big},
        "p_largest_alone": {p: round(float(s["largest"][0][U.index(p)]), 4)
                            for p in big if s["largest"][0][U.index(p)] > 0},
        "p_tied_largest": round(float(s["largest"][1]), 4),
        "p_majority_alone": s["majority"],
    }

wards_rows = []
for a in [x for x in ARMS if x != "B"]:
    sa, sb = R[a]["seats"], b["seats"]
    dmean = S[a]["mean"] - S["B"]["mean"]
    dmean_se = boot(lambda i: sa[i].mean(0) - sb[i].mean(0))
    dl = S[a]["largest"][0] - S["B"]["largest"][0]
    dl_se = boot(lambda i: largest(sa[i])[0] - largest(sb[i])[0])
    dtie = S[a]["largest"][1] - S["B"]["largest"][1]
    wpa, wpb = S[a]["wp"], S["B"]["wp"]
    dwp = wpa - wpb
    # the largest per-ward change in any party's winning probability, its cell
    j, k = np.unravel_index(np.argmax(np.abs(dwp)), dwp.shape)
    dwp_se_cell = float(boot(lambda i: win_probs(R[a]["ww"][:, [j]], i)[0, k]
                             - win_probs(b["ww"][:, [j]], i)[0, k]))
    # the largest change in the probability of B's favourite, per ward
    favB = wpb.argmax(1); favA = wpa.argmax(1)
    dfav = wpa[np.arange(len(W)), favB] - wpb[np.arange(len(W)), favB]
    jf = int(np.argmax(np.abs(dfav)))
    changed = [{"ward": W[w], "index_plus_1": int(w) + 1,
                "B_favourite": U[favB[w]], "B_p": round(float(wpb[w, favB[w]]), 4),
                f"{a}_favourite": U[favA[w]], f"{a}_p": round(float(wpa[w, favA[w]]), 4)}
               for w in range(len(W)) if favA[w] != favB[w]]
    # distribution of the max |Δ| statistic itself under resampling
    maxabs = [float(np.max(np.abs(win_probs(R[a]["ww"], i) - win_probs(b["ww"], i))))
              for i in boots[:50]]
    res["delta"][f"{a}-B"] = {
        "mean_seats": {p: [round(float(dmean[U.index(p)]), 3),
                           round(float(dmean_se[U.index(p)]), 3)] for p in big},
        "max_abs_mean_seats": [U[int(np.argmax(np.abs(dmean)))],
                               round(float(np.max(np.abs(dmean))), 3)],
        "p_largest_alone": {p: [round(float(dl[U.index(p)]), 4),
                                round(float(dl_se[U.index(p)]), 4)]
                            for p in big if max(S[x]["largest"][0][U.index(p)]
                                                for x in ARMS) > 0},
        "p_tied": round(float(dtie), 4),
        "favourite_changed": changed,
        "max_ward_prob_change_any_party": {
            "ward": W[j], "index_plus_1": int(j) + 1, "party": U[k],
            "delta": round(float(dwp[j, k]), 4), "se": round(dwp_se_cell, 4),
            "B": round(float(wpb[j, k]), 4), a: round(float(wpa[j, k]), 4),
            "resampled_max_abs_mean_sd_50": [round(float(np.mean(maxabs)), 4),
                                             round(float(np.std(maxabs, ddof=1)), 4)]},
        "max_ward_prob_change_B_favourite": {
            "ward": W[jf], "index_plus_1": jf + 1, "party": U[favB[jf]],
            "delta": round(float(dfav[jf]), 4)},
    }

# P4: |ΔE| > |ΔN| for DA and ANC, the difference's paired error
if {"N", "E"} <= set(ARMS):
    p4 = {}
    for p in ("DA", "ANC"):
        c = U.index(p)
        f = lambda i: (abs(R["E"]["seats"][i, c].mean() - b["seats"][i, c].mean())
                       - abs(R["N"]["seats"][i, c].mean() - b["seats"][i, c].mean()))
        p4[p] = [round(float(f(np.arange(D))), 3), round(float(boot(f)), 3)]
    res["P4_absE_minus_absN"] = p4

(HERE / "results.json").write_text(json.dumps(res, indent=1))

with open(HERE / "seats.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    hdr = ["party"]
    for a in ARMS:
        hdr += [f"{a}_mean", f"{a}_p5", f"{a}_p95", f"{a}_p_largest_alone"]
    for a in ARMS[1:]:
        hdr += [f"{a}-B_mean", f"{a}-B_mean_mcse", f"{a}-B_p_largest", f"{a}-B_p_largest_mcse"]
    w.writerow(hdr)
    for p in big:
        c = U.index(p); row = [p]
        for a in ARMS:
            row += [round(float(S[a]["mean"][c]), 3), S[a]["p5"][c], S[a]["p95"][c],
                    round(float(S[a]["largest"][0][c]), 4)]
        for a in ARMS[1:]:
            d = res["delta"][f"{a}-B"]
            row += d["mean_seats"][p] + d["p_largest_alone"].get(p, [0, 0])
        w.writerow(row)

with open(HERE / "wards.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    hdr = ["ward", "index_plus_1"]
    for a in ARMS:
        hdr += [f"{a}_first", f"{a}_p_first", f"{a}_second", f"{a}_p_second"]
    hdr += ["B_first_p_in_" + a for a in ARMS[1:]]
    w.writerow(hdr)
    for j, ward in enumerate(W):
        row = [ward, j + 1]
        for a in ARMS:
            wp = S[a]["wp"][j]; o = np.argsort(-wp)
            row += [U[o[0]], round(float(wp[o[0]]), 4), U[o[1]], round(float(wp[o[1]]), 4)]
        fb = int(S["B"]["wp"][j].argmax())
        row += [round(float(S[a]["wp"][j, fb]), 4) for a in ARMS[1:]]
        w.writerow(row)

print(json.dumps({k: v for k, v in res.items() if k != "per_arm"}, indent=1)[:6000])
for a in ARMS:
    pa = res["per_arm"][a]
    print(a, {p: (pa["mean_seats"][p], pa["p5_p95"][p]) for p in MAIN},
          "largest", pa["p_largest_alone"], "tied", pa["p_tied_largest"],
          "maj", pa["p_majority_alone"])
