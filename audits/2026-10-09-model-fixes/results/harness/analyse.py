"""Step 11: every pre-registered quantity, from the arm runs' saved outputs.

    .venv/bin/python analyse.py <out root = data/arms/step11> <arms root> > measures.json

Reads only. Each arm run left <arm>/<label>/{meta.json, arrays.npz,
result.json (panel), trace/...}. Quantities only; no verdicts.
"""
import json
import sys
from pathlib import Path

import numpy as np

OUT, ARMS_ROOT = Path(sys.argv[1]), Path(sys.argv[2])
J26 = "joburg-2026"
SEVEN = ["AMALGAMATED_RAINBOW_MOVEMENT", "CHANGE", "ECONOMIC_EMANCIPATION_FORUM",
         "INTERNATIONAL_REVELATION_CONGRESS", "SHOSHOLOZA_PROGRESSIVE_PARTY",
         "THE_ORGANIC_HUMANITY_MOVEMENT", "UIM"]
_cache = {}


def run(arm, label):
    key = (arm, label)
    if key not in _cache:
        d = OUT / arm / label
        if not (d / "meta.json").exists():
            _cache[key] = None
        else:
            meta = json.loads((d / "meta.json").read_text())
            arr = dict(np.load(d / "arrays.npz"))
            res = json.loads((d / "result.json").read_text()) if (d / "result.json").exists() else None
            tdir = d / "trace" / label if (d / "trace" / label).exists() else d / "trace"
            _cache[key] = {"meta": meta, "arr": arr, "res": res, "trace": tdir}
    return _cache[key]


def trace(r, stage):
    p = r["trace"] / f"{stage}.json"
    return json.loads(p.read_text()) if p.exists() else None


def panel_labels(arm):
    p = OUT / arm / "runnable.json"
    return [f"{c}-{y}" for c, y in json.loads(p.read_text())] if p.exists() else []


PANEL = panel_labels("A")


def col(r, party, name="pr_share_draws"):
    u = r["meta"]["universe"]
    a = r["arr"].get(name)
    if a is None or party not in u:
        return None
    return a[:, u.index(party)]


def seats(r, party):
    cols = r["meta"]["seat_cols"]
    if party not in cols:
        return np.zeros(r["arr"]["seat_draws"].shape[0], dtype=int)
    return r["arr"]["seat_draws"][:, cols.index(party)]


def mean_seats(r):
    cols = r["meta"]["seat_cols"]
    m = r["arr"]["seat_draws"].mean(axis=0)
    return {p: float(m[i]) for i, p in enumerate(cols)}


def ward_wins_mean(r, party):
    return r["meta"]["ward_win_sum"].get(party, 0) / r["meta"]["draws"]


def aligned(r, name):
    """{party: column} for a (draws, universe) array; seat draws by seat_cols."""
    if name == "seat_draws":
        cols, a = r["meta"]["seat_cols"], r["arr"]["seat_draws"]
    else:
        cols, a = r["meta"]["universe"], r["arr"].get(name)
        if a is None:
            return None
    return {p: a[:, i] for i, p in enumerate(cols)}


ARRAYS = ("pr_share_draws", "ward_share_draws", "pr_vote_draws", "ward_vote_draws",
          "seat_draws", "ward_winner_draws", "pool_turnout_draws")


def identical(r1, r2):
    """Per drawn array: True, or a description of the difference."""
    out = {}
    if r1 is None or r2 is None:
        return {"missing": True}
    u1, u2 = r1["meta"]["universe"], r2["meta"]["universe"]
    for name in ARRAYS:
        if name == "ward_winner_draws":
            a, b = r1["arr"].get(name), r2["arr"].get(name)
            if a is None or b is None:
                out[name] = "absent"
                continue
            na = np.array(u1, dtype=object)[a.astype(int)]
            nb = np.array(u2, dtype=object)[b.astype(int)]
            same = (r1["meta"]["wards"] == r2["meta"]["wards"]) and na.shape == nb.shape and bool((na == nb).all())
            out[name] = True if same else f"{int((na != nb).any(axis=1).sum()) if na.shape == nb.shape else 'shape'} draws differ"
            continue
        if name == "pool_turnout_draws":
            a, b = r1["arr"].get(name), r2["arr"].get(name)
            if a is None or b is None:
                out[name] = "absent"
                continue
            same = r1["meta"]["pool_turnout_names"] == r2["meta"]["pool_turnout_names"] and a.shape == b.shape and np.array_equal(a, b)
            out[name] = True if same else "differs"
            continue
        a, b = aligned(r1, name), aligned(r2, name)
        if a is None or b is None:
            out[name] = "absent"
            continue
        keys = set(a) | set(b)
        n = r1["arr"]["seat_draws"].shape[0]
        diff_draws = np.zeros(n, dtype=bool)
        only = []
        for k in keys:
            x = a.get(k, np.zeros(n))
            y = b.get(k, np.zeros(n))
            if k not in a or k not in b:
                only.append(k)
            diff_draws |= (x != y)
        if not diff_draws.any() and not (only and name != "seat_draws"):
            out[name] = True
        else:
            out[name] = {"draws_differing": int(diff_draws.sum()),
                         "columns_in_one_only": sorted(only)}
    return out


def all_true(d):
    return all(v is True for v in d.values())


def stale(r):
    t = trace(r, "02_pools_artefact")
    return {"trace_stale_reason": None if t is None else t.get("stale_reason"),
            "run_pools_stale": r["meta"].get("pools_stale")}


M = {}
ALL_ARMS = ["A", "B0", "B6", "B8", "B", "C", "C16", "D", "D0", "E"]

# ---------------------------------------------------------------- P10 stale
st = {}
for arm in ALL_ARMS + ["E-extra"]:
    labels = ([J26] + PANEL) if arm != "E-extra" else [
        "joburg-2026-gsrecord-aside", "joburg-2026-inverse-variance",
        "joburg-2026-bye-min-weight-1"]
    a = "E" if arm == "E-extra" else arm
    done, bad, missing = 0, [], []
    for lb in labels:
        r = run(a, lb)
        if r is None:
            missing.append(lb)
            continue
        s = stale(r)
        done += 1
        if s["trace_stale_reason"] or s["run_pools_stale"] or r["meta"].get("pools_stale_allowed") or r["meta"].get("allow_stale_pools"):
            bad.append((lb, s))
    st[arm] = {"runs": done, "non_null": bad, "missing": missing}
M["P10_stale"] = st

# ---------------------------------------------------------------- P1 ties
p1 = {}
for arm in ALL_ARMS:
    rows = {}
    for lb in [J26] + PANEL:
        r = run(arm, lb)
        if r is None:
            continue
        t = r["meta"]["ties"]
        rows[lb] = {k: t[k] for k in ("draws_population_1", "draws_with_lot_call",
                                      "draws_with_item2_call", "draws_both")}
        rows[lb]["draws"] = r["meta"]["draws"]
    p1[arm] = rows


def p1_identity(lb):
    a, b = run("A", lb), run("B0", lb)
    if a is None or b is None:
        return None
    ta, tb = a["arr"]["tie_class_per_draw"].any(axis=1), b["arr"]["tie_class_per_draw"].any(axis=1)
    sa, sb = aligned(a, "seat_draws"), aligned(b, "seat_draws")
    n = len(ta)
    diff = np.zeros(n, dtype=bool)
    for k in set(sa) | set(sb):
        diff |= sa.get(k, np.zeros(n)) != sb.get(k, np.zeros(n))
    pop2 = ~ta & ~tb
    ident = identical(a, b)
    return {"pop1_A": int(ta.sum()), "pop1_B0": int(tb.sum()),
            "pop2_both": int(pop2.sum()),
            "seat_vectors_differing_in_pop2": int((diff & pop2).sum()),
            "seat_vectors_differing_in_pop1": int((diff & ~pop2).sum()),
            "seat_vectors_differing_pop2_by_A_class_only": int((diff & ~ta).sum()),
            "vote_share_arrays": {k: ident[k] for k in ("pr_share_draws", "ward_share_draws", "pr_vote_draws", "ward_vote_draws")},
            "ward_winner_draws": ident["ward_winner_draws"]}


M["P1_counts"] = p1
M["P1_A_vs_B0"] = {lb: p1_identity(lb) for lb in [J26] + PANEL}

# ---------------------------------------------------------------- P2 rule A


def rule_a(arm, lb):
    p = OUT / arm / f"rule_a-{lb}" / "rule_a.json"
    m = OUT / arm / f"rule_a-{lb}" / "meta.json"
    if not p.exists():
        return None
    ra = json.loads(p.read_text())
    meta = json.loads(m.read_text())
    calls = meta["ties"]["calls_outside_run"]
    return {"seats": ra["A"]["seats"], "seat_err": ra["A"]["seat_err"],
            "wards_ok": ra["A"]["wards_ok"], "ward_wins": ra["A"]["ward_wins"],
            "tied_wards": ra["tied_wards"],
            "seat_call_classes": [c["class"] for c in calls],
            "seat_call_pairs": [c["pair"] for c in calls if c["class"] != "untied"]}


p2 = {}
for lb in PANEL:
    a, b = rule_a("A", lb), rule_a("B0", lb)
    if a is None or b is None:
        p2[lb] = None
        continue
    p2[lb] = {"seats_equal": a["seats"] == b["seats"],
              "ward_wins_equal": a["ward_wins"] == b["ward_wins"],
              "seat_err_A": a["seat_err"], "seat_err_B0": b["seat_err"],
              "wards_ok_A": a["wards_ok"], "wards_ok_B0": b["wards_ok"],
              "tied_wards_A": len(a["tied_wards"]), "tied_wards_B0": len(b["tied_wards"]),
              "seat_call_classes_A": a["seat_call_classes"],
              "seat_call_classes_B0": b["seat_call_classes"],
              "tie_pairs_A": a["seat_call_pairs"], "tie_pairs_B0": b["seat_call_pairs"],
              "seats_diff": {p: (a["seats"].get(p, 0), b["seats"].get(p, 0))
                             for p in set(a["seats"]) | set(b["seats"])
                             if a["seats"].get(p, 0) != b["seats"].get(p, 0)}}
M["P2_rule_a"] = p2


def opp_total(arm, name, key="seat_abs_err_coherent"):
    tot, n = 0, 0
    for lb in PANEL:
        r = run(arm, lb)
        if r is None or r["res"] is None:
            continue
        v = (r["res"]["opponents"].get(name) or {}).get(key)
        if isinstance(v, (int, float)):
            tot += v
            n += 1
    return {"total": tot, "city_years": n}


M["P2b_uniform_swing_roster"] = {arm: opp_total(arm, "uniform-swing+roster") for arm in ("A", "B0")}

# ---------------------------------------------------------------- panel scores


def panel_scores(arm):
    out = {}
    for lb in PANEL:
        r = run(arm, lb)
        if r is None or r["res"] is None:
            continue
        res = r["res"]
        out[lb] = {"pr_mae": res["pr_mae"], "ward_mae": res["ward_mae"],
                   "seat_abs_err_coherent": res["seat_abs_err_coherent"],
                   "wards": res.get("wards")}
    return out


SC = {arm: panel_scores(arm) for arm in ALL_ARMS}
M["panel_scores"] = {arm: {lb: {k: v for k, v in d.items() if k != "wards"} for lb, d in s.items()} for arm, s in SC.items()}


def contrast(x, y):
    """y - x over the panel: per city-year deltas, panel means and sums."""
    sx, sy = SC[x], SC[y]
    common = [lb for lb in PANEL if lb in sx and lb in sy]
    d = {lb: {k: sy[lb][k] - sx[lb][k] for k in ("pr_mae", "ward_mae", "seat_abs_err_coherent")} for lb in common}
    n = len(common)
    return {"n": n, "per_city_year": d,
            "pr_mae_mean_x": sum(sx[lb]["pr_mae"] for lb in common) / n if n else None,
            "pr_mae_mean_y": sum(sy[lb]["pr_mae"] for lb in common) / n if n else None,
            "pr_mae_mean_delta": sum(v["pr_mae"] for v in d.values()) / n if n else None,
            "ward_mae_mean_delta": sum(v["ward_mae"] for v in d.values()) / n if n else None,
            "ward_mae_mean_x": sum(sx[lb]["ward_mae"] for lb in common) / n if n else None,
            "ward_mae_mean_y": sum(sy[lb]["ward_mae"] for lb in common) / n if n else None,
            "coherent_sum_x": sum(sx[lb]["seat_abs_err_coherent"] for lb in common),
            "coherent_sum_y": sum(sy[lb]["seat_abs_err_coherent"] for lb in common),
            "coherent_sum_delta": sum(v["seat_abs_err_coherent"] for v in d.values()),
            "pr_mae_max_abs_delta": max((abs(v["pr_mae"]) for v in d.values()), default=None),
            "ward_mae_max_delta": max((v["ward_mae"] for v in d.values()), default=None)}


def seat_moves(x, y, lb=J26):
    a, b = run(x, lb), run(y, lb)
    if a is None or b is None:
        return None
    ma, mb = mean_seats(a), mean_seats(b)
    return {p: {"x": ma.get(p, 0.0), "y": mb.get(p, 0.0), "delta": mb.get(p, 0.0) - ma.get(p, 0.0)}
            for p in sorted(set(ma) | set(mb)) if max(ma.get(p, 0), mb.get(p, 0)) > 0}


def identity_table(x, y, labels):
    return {lb: identical(run(x, lb), run(y, lb)) for lb in labels}


# ---------------------------------------------------------------- P6
def gap_stats(r, party):
    pr, wd = col(r, party), col(r, party, "ward_share_draws")
    if pr is None:
        return None
    g = 100 * (pr - wd)
    return {"mean_gap_pts": float(g.mean()), "share_draws_gap_le_-1.76": float((g <= -1.76).mean()),
            "min_gap": float(g.min()), "max_gap": float(g.max())}


def p6_block(x, y):
    a, b = run(x, J26), run(y, J26)
    if a is None or b is None:
        return None
    out = {"F1_PA_ward_pr_ratio": {x: a["meta"]["ward_pr_ratio"].get("PA"), y: b["meta"]["ward_pr_ratio"].get("PA")},
           "F2_PA_gap": {x: gap_stats(a, "PA"), y: gap_stats(b, "PA")},
           "F3_gaps": {p: {x: gap_stats(a, p), y: gap_stats(b, p)} for p in ("DA", "ANC", "EFF", "ASA", "MK")},
           "F4_PA": {x: {"mean_seats": mean_seats(a).get("PA"), "mean_ward_wins": ward_wins_mean(a, "PA")},
                     y: {"mean_seats": mean_seats(b).get("PA"), "mean_ward_wins": ward_wins_mean(b, "PA")}},
           "F5_seat_moves": seat_moves(x, y),
           "F6_identity": identical(a, b)}
    moves = out["F5_seat_moves"]
    out["F5_largest_other_move"] = max(((p, v["delta"]) for p, v in moves.items() if p not in ("PA", "DA", "ANC")),
                                       key=lambda t: abs(t[1]))
    return out


M["P6_B6_vs_A_2026"] = p6_block("A", "B6")
M["P6_B_vs_A_2026"] = p6_block("A", "B")
c = contrast("A", "B6")
M["P6_B6_vs_A_panel"] = {"contrast": c,
                         "B1_pr_share_identity": {lb: identical(run("A", lb), run("B6", lb)).get("pr_share_draws") for lb in PANEL},
                         "B1_pr_mae_equal": {lb: (SC["A"][lb]["pr_mae"] == SC["B6"][lb]["pr_mae"]) for lb in PANEL if lb in SC["A"] and lb in SC["B6"]},
                         "B4_wards": {lb: {"A": SC["A"][lb]["wards"], "B6": SC["B6"][lb]["wards"]} for lb in PANEL if lb in SC["A"] and lb in SC["B6"]}}
M["P6_B_vs_A_panel"] = {"contrast": contrast("A", "B")}

ch = {}
for arm in ("B", "C", "C16", "D", "E"):
    r = run(arm, J26)
    if r is None:
        continue
    ws = col(r, "CHANGE", "ward_share_draws")
    ch[arm] = {"slate_coverage_now": (r["meta"].get("contestation") or {}).get("CHANGE"),
               "slate_coverage_was": (r["meta"].get("contestation_prev") or {}).get("CHANGE"),
               "ward_pr_ratio": r["meta"]["ward_pr_ratio"].get("CHANGE"),
               "ward_share_max": None if ws is None else float(ws.max()),
               "ward_share_min": None if ws is None else float(ws.min()),
               "draws_ward_share_ge_1e-5": None if ws is None else int((ws >= 1e-5).sum()),
               "ward_wins_total": r["meta"]["ward_win_sum"].get("CHANGE", 0)}
M["P6_CHANGE"] = ch

# ---------------------------------------------------------------- P8
FOUR = ["buffalocity-2011", "buffalocity-2021", "ethekwini-2016", "mangaung-2011"]
M["P8_four_identity"] = identity_table("A", "B8", FOUR)
M["P8_panel"] = contrast("A", "B8")
ru = {}
for arm in ("B8", "B", "C", "C16", "D", "D0", "E"):
    ru[arm] = {}
    for lb in [J26] + PANEL:
        r = run(arm, lb)
        if r is not None:
            ru[arm][lb] = r["meta"]["guards"].get("roster_unrepresented", "ABSENT")
M["P8_roster_unrepresented"] = ru


def seven(arm):
    r = run(arm, J26)
    if r is None:
        return None
    each = {p: (float(col(r, p).mean()) if col(r, p) is not None else None) for p in SEVEN}
    tot_share = sum(v for v in each.values() if v is not None)
    together = sum(seats(r, p) for p in SEVEN)
    return {"mean_list_share_each_pct": {p: (100 * v if v is not None else None) for p, v in each.items()},
            "together_mean_list_share_pct": 100 * tot_share,
            "together_seats_P_0_or_1": float((together <= 1).mean()),
            "together_seats_mean": float(together.mean()),
            "in_universe": [p for p in SEVEN if p in r["meta"]["universe"]]}


M["P8_seven_2026"] = {arm: seven(arm) for arm in ("A", "B8", "B", "C", "C16", "D", "E")}

# ---------------------------------------------------------------- P11, P16, P17
M["P11_seats_2026"] = seat_moves("B", "C")
M["P11_panel"] = contrast("B", "C")


def windows(arm, lb):
    r = run(arm, lb)
    if r is None:
        return None
    sp = trace(r, "20_spine") or {}
    w = sp.get("size_window")
    if not w:
        return "absent"
    return {k: {"h": w[k].get("h"), "status": w[k].get("status"), "best": w[k].get("best"),
                "scored": w[k].get("scored"), "clusters": w[k].get("clusters"), "arm": w[k].get("arm")}
            for k in ("theta", "rho") if k in w}


M["P16_windows_C16"] = {lb: windows("C16", lb) for lb in [J26] + PANEL}
M["P16_C16_vs_C_identity"] = identity_table("C", "C16", [J26] + PANEL)
M["P17_seats_2026"] = seat_moves("C16", "D")


def spine_levels(arm):
    r = run(arm, J26)
    sp = trace(r, "20_spine") if r else None
    return (sp or {}).get("level") or {}


lc, ld = spine_levels("C16"), spine_levels("D")
M["P17_spine_rises"] = {p: {"C16": lc[p], "D": ld[p], "dlog": float(np.log(ld[p] / lc[p]))}
                        for p in sorted(set(lc) & set(ld)) if lc[p] > 0 and ld[p] > lc[p]}
sd = {}
for arm in ("C16", "D", "E"):
    r = run(arm, J26)
    if r is None:
        continue
    g = r["meta"]["guards"]
    sd[arm] = {"level_sd_default_parties": g.get("level_sd_default_parties", "ABSENT"),
               "level_sd_at_size": {p: (g.get("level_sd_at_size") or {}).get(p) for p in SEVEN}
               if isinstance(g.get("level_sd_at_size"), dict) else g.get("level_sd_at_size", "ABSENT")}
M["A1_widths"] = sd
M["P17_panel"] = contrast("C16", "D")

# ---------------------------------------------------------------- P13 SACP


def spec(arm_tree, name="pools_2026.json"):
    return json.loads((ARMS_ROOT / arm_tree / "data" / "processed" / name).read_text())


SACP = "SOUTH_AFRICAN_COMMUNIST_PARTY"


def centre(arm, party):
    r = run(arm, J26)
    c = trace(r, "30_centres") if r else None
    if not c:
        return None
    return {k: (c.get(k) or {}).get(party) for k in ("before_shrink", "after_shrink")}


p13 = {}
for arm, tree in (("A", "A"), ("B", "B")):
    r = run(arm, J26)
    s = seats(r, SACP)
    p13[arm] = {"centre_30": centre(arm, SACP),
                "spec_seed": (spec(tree).get("seeds") or {}).get(SACP),
                "mean_list_share_pct": None if col(r, SACP) is None else 100 * float(col(r, SACP).mean()),
                "mean_seats": float(s.mean()), "P_at_least_one_seat": float((s >= 1).mean())}
sa, sb = spec("A").get("seeds") or {}, spec("B").get("seeds") or {}
notes_b = spec("B").get("seed_notes") or {}
gen = {p: {"A": sa[p], "B": sb[p], "rel": sb[p] / sa[p] - 1}
       for p in sorted(set(sa) & set(sb)) if p != SACP and sa[p] > 0
       and "entrant from nothing" in str(notes_b.get(p, ""))}
p13["generic_entrant_seeds"] = {"n": len(gen), "max_abs_rel": max((abs(v["rel"]) for v in gen.values()), default=None),
                                "rel_range": [min((v["rel"] for v in gen.values()), default=None),
                                              max((v["rel"] for v in gen.values()), default=None)],
                                "per_party": gen}
p13["seat_moves_B_vs_A"] = {p: v for p, v in (seat_moves("A", "B") or {}).items() if p in ("ANC", "DA")}
M["P13"] = p13

# ---------------------------------------------------------------- P12
gs = {}
for arm in ("B", "C", "C16", "D", "D0", "E"):
    gs[arm] = {}
    for lb in [J26] + PANEL:
        r = run(arm, lb)
        if r is None:
            continue
        t = r["meta"]["guards"].get("group_share_tripwire", "ABSENT")
        if isinstance(t, dict):
            gs[arm][lb] = {"population": t["population"], "scanned": t["scanned"],
                           "key_current": t.get("key_current"), "firing": t["pairs"]}
        else:
            gs[arm][lb] = t
M["P12_tripwire"] = gs
aside = run("E", "joburg-2026-gsrecord-aside")
M["P12_aside"] = None if aside is None else {
    "identity_vs_E": identical(run("E", J26), aside),
    "tripwire": aside["meta"]["guards"].get("group_share_tripwire")}

# ---------------------------------------------------------------- P19
def centres_equal(x, y, lb=J26, lb2=None):
    a, b = run(x, lb), run(y, lb2 or lb)
    if a is None or b is None:
        return None
    ca, cb = trace(a, "30_centres"), trace(b, "30_centres")
    return {k: (ca or {}).get(k) == (cb or {}).get(k) for k in ("before_shrink", "after_shrink")}


M["P19_E_vs_D0_2026"] = identical(run("D0", J26), run("E", J26))
M["P19_E_vs_D0_centres"] = centres_equal("D0", "E")
M["P19_inert_centres"] = {lb: centres_equal("E", "E", J26, lb) for lb in ("joburg-2026-inverse-variance", "joburg-2026-bye-min-weight-1")}
M["P12_aside_centres"] = centres_equal("E", "E", J26, "joburg-2026-gsrecord-aside")
M["P19_E_vs_D_panel"] = identity_table("D", "E", PANEL)
M["P19_inert"] = {lb: identical(run("E", J26), run("E", lb)) for lb in
                  ("joburg-2026-inverse-variance", "joburg-2026-bye-min-weight-1")}
p19 = {}
for p in ("ALL_CITIZENS_PARTY", "TRUTH_AND_SOLIDARITY_MOVEMENT"):
    p19[p] = {"E_centre_30": centre("E", p), "D_centre_30": centre("D", p),
              "D0_centre_30": centre("D0", p),
              "E_spec_seed": (spec("E").get("seeds") or {}).get(p),
              "E_mean_seats": float(seats(run("E", J26), p).mean()),
              "D_mean_seats": float(seats(run("D", J26), p).mean())}
p19["seat_moves_E_vs_D"] = {p: v for p, v in (seat_moves("D", "E") or {}).items() if p in ("PA", "DA", "ANC", "MK", "ALL_CITIZENS_PARTY")}
bw = {}
for arm in ("D", "D0", "E"):
    r = run(arm, J26)
    c = trace(r, "30_centres") if r else None
    bw[arm] = {"w_bye": r["meta"].get("w_bye") if r else None,
               "bye_weight_30": (c or {}).get("bye_weight")}
p19["bye_weights"] = bw
M["P19"] = p19

# ---------------------------------------------------------------- whole-arm seat tables at 2026
M["mean_seats_2026"] = {arm: (mean_seats(run(arm, J26)) if run(arm, J26) else None) for arm in ALL_ARMS}
json.dump(M, sys.stdout, indent=1, default=str)
