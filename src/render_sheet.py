"""Regenerate forecast-sheet.html's data block from the model outputs.

The sheet's previous revision hand-copied its numbers into the HTML, so any
re-run silently made them stale (review, Part 4). This script computes every
figure the sheet displays from `seat_draws.csv` and `forecast_summary.json`
and rewrites the block between the __GEN_START__ / __GEN_END__ markers.

Run after any montecarlo.py re-run:
    python src/render_sheet.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import tomllib
from pathlib import Path

import numpy as np

import cityconfig


def _md(text: str) -> str:
    """The only markup claims.toml needs: **bold**."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)

CHIPS = {
    "DA": "#1B5EA8", "ANC": "#1B7A3D", "EFF": "#B3202B", "MK": "#5B6E22",
    "ASA": "#2FA79B", "PA": "#E0A419", "IFP": "#C8442A", "RISE": "#7A6BA8",
    "VFPLUS": "#B0752D", "ACDP": "#6B4E9E", "ALJAMAAH": "#2E8B72",
    "ENTRANT": "#b9b9b9",
}
NAMES = {
    "DA": "DA", "ANC": "ANC", "EFF": "EFF", "MK": "MK Party", "ASA": "ActionSA",
    "PA": "PA", "IFP": "IFP", "RISE": "Rise Mzansi", "VFPLUS": "VF+",
    "ACDP": "ACDP", "ALJAMAAH": "Al Jama-ah", "ENTRANT": "New entrant",
    "SOUTH_AFRICAN_COMMUNIST_PARTY": "SACP", "BOSA": "BOSA",
    "ALL_CITIZENS_PARTY": "All Citizens Party",
}
CHART_PARTIES = ["DA", "ANC", "EFF", "ASA", "MK", "PA", "IFP", "RISE",
                 "ALJAMAAH", "ENTRANT"]

ALLIANCE_8 = ("DA", "ASA", "PA", "IFP", "VFPLUS", "ACDP", "RISE", "ALJAMAAH")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=None,
                        help="where inputs are read (default: the target's own processed "
                             "directory). A literal data/processed is "
                             "JOHANNESBURG's, whatever --city says")
    parser.add_argument("--sheet", type=Path, default=Path("forecast-sheet.html"))
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))
    args.processed = args.processed or cityconfig.use_target(
        getattr(args, "target", None)).processed

    with (args.processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    parties = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    S = {p: np.array([int(r[p]) for r in rows]) for p in parties}
    thr = np.array([int(r["threshold"]) for r in rows])
    council = np.array([int(r["council_size"]) for r in rows])
    summary = json.loads((args.processed / "forecast_summary.json").read_text())

    def q(series):
        return (int(round(np.median(series))), int(round(np.percentile(series, 5))),
                int(round(np.percentile(series, 95))))

    def coalition(*members):
        total = sum(S[p] for p in members if p in S)
        med, lo, hi = q(total)
        return {"p": round(float((total >= thr).mean()), 4),
                "med": med, "lo": lo, "hi": hi}

    # largest party, and whether anyone ever gets to govern alone
    stack = np.stack([S[p] for p in parties])
    largest = stack.argmax(axis=0)
    p_da_largest = float((np.array(parties)[largest] == "DA").mean())
    p_anc_largest = float((np.array(parties)[largest] == "ANC").mean())
    p_alone = float((stack.max(axis=0) >= thr).mean())
    alone_str = f"{p_alone:.0%}" if p_alone >= 0.001 else "&lt;0.1%"

    p_excessive = summary.get("p_excessive_by_party", {}).get("ANC", 0.0)
    thr_med = int(np.median(thr))
    minority = {m["scenario"]: m["p_viable"] for m in summary["minority"]}
    da_minority = minority.get("DA minority, only ANC opposes (2021 pattern)", 0.0)
    anc_da = coalition("ANC", "DA")

    gen = {
        "tiles": [
            {"n": alone_str, "chance": True,
             "l": "One party reaches a majority alone"},
            {"n": f"{anc_da['p']:.0%}", "chance": True,
             "l": "ANC + DA have a majority — the only two-party combination "
                  "that reliably reaches one"},
            {"n": f"{p_da_largest:.0%}", "chance": True,
             "l": "The DA is the largest single party"},
            {"n": f"{p_anc_largest:.0%}", "chance": True,
             "l": "The ANC is the largest single party"},
            {"n": f"{p_excessive:.0%}", "chance": True,
             "l": "The ANC triggers the excessive-seats clause",
             "sub": "Keeps every ward it wins, takes zero list seats — "
                    "everyone else squeezed"},
            {"n": "270 · 136", "chance": False,
             "l": "Total seats · majority threshold",
             "sub": "The excessive-seats law keeps the council at 270"},
        ],
        "parties": [
            {"name": NAMES[p], "chip": CHIPS[p],
             **dict(zip(("med", "lo", "hi"), q(S[p])))}
            for p in CHART_PARTIES if p in S
        ] + [{"name": "Others", "chip": "#8b918b",
              **dict(zip(("med", "lo", "hi"),
                         q(sum(S[p] for p in parties
                               if p not in CHART_PARTIES))))}],
        "coalitions": [
            {"name": "ANC + DA", "key": True, **anc_da},
            {"name": "Eight-party alliance (no ANC, EFF or MK)", "key": True,
             **coalition(*ALLIANCE_8)},
            {"name": "Nine-party alliance (no DA or ActionSA)", "key": True,
             **coalition("ANC", "EFF", "MK", "PA", "IFP", "VFPLUS", "ACDP",
                         "RISE", "ALJAMAAH")},
            {"name": "DA + EFF + ActionSA", **coalition("DA", "EFF", "ASA")},
            {"name": "DA + EFF + MK", **coalition("DA", "EFF", "MK")},
            {"name": "ANC + EFF + MK", **coalition("ANC", "EFF", "MK")},
            {"name": "DA + ActionSA", **coalition("DA", "ASA")},
        ],
        "minority_da_2021": round(da_minority, 4),
        "meta": {"threshold_median": thr_med,
                 "council_median": int(np.median(council)),
                 "p_excessive_anc": round(p_excessive, 4)},
    }

    # --- "Who can govern": the interactive's full analysis, computed from ---
    # the published 5,000-draw run (discovered combinations, passenger
    # filter, cushion, stability, survivability) so the forecast page shows
    # the same table the simulator builds live.
    means = {p: float(S[p].mean()) for p in parties}
    # Every party `seat_draws.csv` tracks. A cap of 12 dropped VF+ (mean 2.2
    # seats) and flipped the DA's all-together row from 53.7% to 48.6%.
    top = [p for p in sorted(parties, key=lambda q: -means[q]) if means[p] >= 0.4]
    nT = len(top)
    med_of = {p: int(round(np.median(S[p]))) for p in parties}
    _sum_cache: dict[int, np.ndarray] = {}

    def msum(m):
        if m not in _sum_cache:
            tot = None
            for k in range(nT):
                if m & (1 << k):
                    tot = S[top[k]] if tot is None else tot + S[top[k]]
            _sum_cache[m] = tot
        return _sum_cache[m]

    def wp(m):
        return float((msum(m) >= thr).mean())

    def chip_of(p, extra=""):
        c = CHIPS.get(p, "#8b918b")
        return (f'<span class="chip" style="background:{c};display:inline-block;'
                f'width:8px;height:8px;border-radius:2px;margin-right:4px">'
                f'</span>{extra or NAMES.get(p, p)}')

    def glabel(m):
        return " + ".join(chip_of(top[k]) for k in range(nT) if m & (1 << k))

    def mask_of(codes):
        m = 0
        for c in codes:
            if c in top:
                m |= 1 << top.index(c)
        return m

    def detail(m, med, barred=frozenset()):
        """Cushion, stability and survivability for one coalition mask."""
        cushion = med - 136
        if cushion <= 0:
            return f"{'+' if cushion > 0 else ''}{cushion}", "—", "—"
        members = [top[k] for k in range(nT) if m & (1 << k)]
        overall = min(100.0, cushion / med * 100)
        per = ", ".join(
            f"{min(100.0, cushion / max(med_of[p], 1) * 100):.0f}%&nbsp;of&nbsp;"
            f"{NAMES.get(p, p)}" for p in members)
        stab = (f"<b>{overall:.0f}%</b> of all councillors can defect"
                f'<div style="font-size:11px;color:var(--ink-3);margin-top:2px">'
                f"survives defection of {per}</div>")
        bits = []
        for p in members:
            low = 1 << top.index(p)
            if wp(m ^ low) >= 0.5:
                bits.append(f"survives {NAMES.get(p, p)} exit")
                continue
            rescue = None
            for j in range(nT):
                # a party the group rules out cannot be the rescuer
                if m & (1 << j) or top[j] in barred:
                    continue
                restore = wp((m ^ low) | (1 << j))
                if restore >= 0.5 and (rescue is None or restore > rescue[1]):
                    rescue = (top[j], restore)
            bits.append(f"{NAMES.get(p, p)} exit survivable only if "
                        f"{NAMES.get(rescue[0], rescue[0])} steps in" if rescue
                        else f"{NAMES.get(p, p)} exit breaks it")
        return f"+{cushion}", stab, "; ".join(bits)

    def smallest_share(m):
        """Share of draws in which `m` is a SMALLEST workable majority: it
        reaches the threshold and loses it if any one member leaves."""
        tot = msum(m)
        ok = tot >= thr
        for k in range(nT):
            if m & (1 << k):
                ok &= (tot - S[top[k]]) < thr
        return float(ok.mean())

    def row(m, key=False, label=None, barred=frozenset()):
        med = int(round(np.median(msum(m))))
        cushion, stab, surv = detail(m, med, barred)
        return {"key": key, "label": label or glabel(m), "p": wp(m),
                "mwc": smallest_share(m), "med": med, "cushion": cushion,
                "stab": stab, "surv": surv}

    # Two questions a reader asks, not one ranked list. Ranking every pair and
    # triple by P(majority) filled the table with DA + ANC + <anyone>, and the
    # old p >= 0.5 filter could never show a DA option without the ANC at all.
    # Each group lists the SMALLEST workable majorities available to its anchor
    # from the parties it is not barred from — mathematics only; how politically
    # likely any deal is stays the reader's judgement.
    from itertools import combinations
    GROUPS = (("The DA without the ANC, EFF or MK", "DA", {"ANC", "EFF", "MK"}),
              ("The ANC without the DA", "ANC", {"DA"}))
    SHOW, MIN_SHARE, MAX_PARTNERS = 6, 0.01, 4
    out_rows = [row(mask_of(("ANC", "DA")), key=True)]
    for title, anchor, barred in GROUPS:
        if anchor not in top:
            continue
        pool = [i for i, p in enumerate(top) if p != anchor and p not in barred]
        base = 1 << top.index(anchor)
        cands = []
        for k in range(1, MAX_PARTNERS + 1):
            for combo in combinations(pool, k):
                m = base
                for i in combo:
                    m |= 1 << i
                s = smallest_share(m)
                if s >= MIN_SHARE:
                    cands.append((s, m))
        cands.sort(key=lambda sm: -sm[0])
        out_rows.append({"group": title})
        out_rows += [row(m, barred=barred) for _, m in cands[:SHOW]]
        everyone = base
        for i in pool:
            everyone |= 1 << i
        out_rows.append(row(everyone, key=True, barred=barred,
                            label=f"All of them together: {glabel(everyone)}"))
    note = ("“Majority in” is the share of simulations in which the combination reaches "
            "the 136 needed. “Smallest form in” is the share in which it does so with no "
            "passenger — lose any one partner and the majority goes. A simulation can have "
            "several smallest forms, so that column does not add to 100%. The simulations "
            f"track {nT} parties individually; the rest hold {270 - sum(means.values()):.0f} "
            "seats on average between them and are left out of every row, so the "
            "all-together rows understate what a broader deal could reach.")
    gen["govern"] = {"rows": out_rows, "note": note}

    # --- claims tested: rendered from content/<city>/claims.toml ----------
    # Claims are data so the newsdesk can propose one as a diff. Verdicts
    # stay human — they require a model run.
    claims_path = Path("content") / args.city / "claims.toml"
    if claims_path.exists():
        with claims_path.open("rb") as fh:
            claims = tomllib.load(fh).get("claim", [])
        boxes = []
        for c in claims:
            steps = "".join(
                f'<li><div class="stepbody">{_md(step)}</div></li>'
                for step in c.get("steps", []))
            vclass = "vtrue" if c["verdict"].upper() == "TRUE" else "vfalse"
            link = (f'<a href="{c["url"]}" target="_blank" rel="noopener">'
                    f'{c["outlet"]}</a>') if c.get("url") else c.get("outlet", "")
            badge = (f'<span class="verdict {vclass}">'
                     f'{c["verdict"].upper()}</span>')
            ident = (f'<img class="plogo" src="logos/{c["logo"]}.png" alt="" '
                     f'width="44" height="44">' if c.get("logo") else
                     f'<span class="chip" style="background:{c["chip"]}"></span>')
            boxes.append(
                f'<article class="claim" data-party="{c["party"]}">'
                f'<div class="claim-top">{ident}'
                f'<div class="claim-who"><b>{c.get("party_name", c["party"])}'
                f'</b><span>{c["speaker"]} \u00b7 {link}</span></div>'
                f'{badge}</div>'
                f'<blockquote class="claim-quote">{c["quote"]}'
                f'<span class="q-close">\u201d</span></blockquote>'
                f'<p class="claim-intro">{_md(c["intro"])}</p>'
                f'<ol class="claimsteps">{steps}</ol></article>')
        claims_html = ("<!-- __CLAIMS_START__ -->\n    "
                       + "\n    ".join(boxes)
                       + "\n    <!-- __CLAIMS_END__ -->")
        for tgt in (Path("forecast-sheet.html"), Path("drafts/forecast-draft.html")):
            t = tgt.read_text(encoding="utf-8")
            if "__CLAIMS_START__" in t:
                a = t.index("<!-- __CLAIMS_START__ -->")
                b2 = t.index("<!-- __CLAIMS_END__ -->") + len("<!-- __CLAIMS_END__ -->")
                tgt.write_text(t[:a] + claims_html + t[b2:], encoding="utf-8")
        print(f"claims: {len(claims)} box(es) rendered from {claims_path}")

    # two-ballots arithmetic strip: 135 wards + 135 list = 270
    def bar(items, total, label):
        segs = ""
        for nm, n, col in items:
            if n <= 0: continue
            segs += (f'<div data-tip="{nm} — {n} seats" title="{nm} — {n} seats" style="width:{n/total*100:.2f}%;'
                     f'background:{col}"></div>')
        return (f'<div style="display:flex;flex-direction:column;gap:4px">'
                f'<div style="font:650 10.5px var(--sans, sans-serif);letter-spacing:.1em;'
                f'text-transform:uppercase;color:var(--ink-3)">{label}</div>'
                f'<div style="display:flex;height:26px;border-radius:3px;overflow:hidden">{segs}</div></div>')

    # Bars must sum exactly as the headline claims (135 + 135 = 270): named
    # parties plus a "Smaller parties" bucket are rounded with largest
    # remainder to the exact bar totals, and list = council − wards so the
    # three bars are mutually consistent by construction.
    def round_to_total(vals: dict[str, float], total: int) -> dict[str, int]:
        floors = {k: int(v) for k, v in vals.items()}
        rem = total - sum(floors.values())
        for k in sorted(vals, key=lambda q: floors[q] - vals[q])[:max(rem, 0)]:
            floors[k] += 1
        return floors

    # ⛔ MEANS, NOT MEDIANS. Medians do not add: the party medians summed to 240
    # of 270, so "Smaller parties = 270 − named medians" showed 39 seats against
    # a real 13-24 (2011-2021), and "ANC list = median total − MEAN wards" showed
    # 7 list seats for a party that gets none in most draws. Means add exactly,
    # so wards + list = total holds per party and every bar sums to its size.
    # `seat_draws.csv` omits the smallest parties, which is why the remainder is
    # taken from 270 rather than summed.
    OTHER = "__other__"
    mean_tot = {p: float(S[p].mean()) for p in parties}
    named = [(pty, v) for pty, v in sorted(summary["parties"].items(),
                                           key=lambda kv: -mean_tot.get(kv[0], 0.0))
             if NAMES.get(pty) and CHIPS.get(pty) and mean_tot.get(pty, 0.0) >= 2.5]
    ward_raw = {pty: float(v.get("ward_wins_mean", 0.0)) for pty, v in named}
    tot_raw = {pty: mean_tot[pty] for pty, v in named}
    ward_raw[OTHER] = max(135.0 - sum(ward_raw.values()), 0.0)
    tot_raw[OTHER] = max(270.0 - sum(tot_raw.values()), 0.0)
    ward_n = round_to_total(ward_raw, 135)
    tot_n = round_to_total(tot_raw, 270)
    list_n = {k: max(tot_n[k] - ward_n[k], 0) for k in tot_n}
    list_n[OTHER] = max(list_n[OTHER] + 135 - sum(list_n.values()), 0)

    def seg(k):
        return ("Smaller parties", "#8b918b") if k == OTHER else (NAMES[k], CHIPS[k])
    order = [pty for pty, _ in named] + [OTHER]
    wardsb = [(seg(k)[0], ward_n[k], seg(k)[1]) for k in order if ward_n.get(k, 0) > 0]
    listb = [(seg(k)[0], list_n[k], seg(k)[1]) for k in order if list_n.get(k, 0) > 0]
    totb = [(seg(k)[0], tot_n[k], seg(k)[1]) for k in order if tot_n.get(k, 0) > 0]

    anc_list = list_n.get("ANC", 0)
    p_none = f"{p_excessive:.0%}"
    n_word = ("<b>under one seat</b>" if anc_list == 0 else
              "<b>a single seat</b>" if anc_list == 1 else f"<b>{anc_list} seats</b>")
    anc_note = (f"Note the ANC's list bar: {n_word} on average. In at least {p_none} of simulations "
                "it gets none at all — its ward wins already exceed its proportional share, "
                "so the excessive-seats clause strips its list seats and everyone else's "
                "shrink to fit")
    ballots_caption = (f"Every bar is the average across all simulations, so the three add up "
                       f"exactly. Hover a segment for its seats. {anc_note} — while ActionSA, with "
                       "broad support but no stronghold wards, lives almost wholly on the "
                       "list. Two opposite ways of turning votes into seats, in one city.")
    strip = f"""<!-- __BALLOTS_START__ -->
  <details class="rollup" data-band="forecast" open>
    <summary><span class="eyebrow">The arithmetic — two ballots, one council</span>
    <h2>135 wards + 135 list seats = 270</h2></summary>
    <div style="display:flex;flex-direction:column;gap:14px">
      {bar(wardsb, 135, "Ward seats — won race by race")}
      {bar(listb, 135, "+ List seats — topping parties up to their share")}
      {bar(totb, 270, "= The council")}
    </div>
    <figcaption>{ballots_caption}</figcaption>
  </details>
  <!-- __BALLOTS_END__ -->"""
    for tgt in (Path("forecast-sheet.html"), Path("drafts/forecast-draft.html")):
        s = tgt.read_text(encoding="utf-8")
        if "__BALLOTS_START__" in s:
            a = s.index("<!-- __BALLOTS_START__ -->")
            b2 = s.index("<!-- __BALLOTS_END__ -->") + len("<!-- __BALLOTS_END__ -->")
            tgt.write_text(s[:a] + strip + s[b2:], encoding="utf-8")

    # --- excessive-seats regime comparison (regenerate via ------------------
    # src/overhang_regimes.py, which runs the expand and level counterfactuals
    # and restores the reference outputs)
    REG_PARTIES = ["DA", "ANC", "EFF", "ASA", "MK", "PA", "IFP", "ALJAMAAH"]
    regimes = []
    for key, label, note in (
            ("deduct", "South African law", "fixed 270 — others squeezed"),
            ("expand", "Germany 2000", "council grows"),
            ("level", "Germany 2015", "council grows &amp; levelled"),
            ("cap", "Germany 2023",
             "fixed 270 — wins not seated if not proportional")):
        if key == "deduct":
            summ = summary
            sd = rows
        else:
            sp = args.processed / f"regime_{key}_summary.json"
            dp = args.processed / f"regime_{key}_seat_draws.csv"
            if not (sp.exists() and dp.exists()):
                regimes = []
                break
            summ = json.loads(sp.read_text(encoding="utf-8"))
            with dp.open(encoding="utf-8", newline="") as fh:
                sd = list(csv.DictReader(fh))
        council_med = int(np.median([int(r["council_size"]) for r in sd]))
        thr_med = int(np.median([int(r["threshold"]) for r in sd]))
        meds = {p: int(round(v["median"])) for p, v in summ["parties"].items()}
        regimes.append((label, note, meds, council_med, thr_med))

    if regimes:
        head = "".join(
            f'<th colspan="2" style="text-align:center'
            + (';border-left:1px solid var(--rule-soft)' if k else "")
            + f'">{lab}<br><span style="font-weight:400;color:var(--ink-3)">{note}</span></th>'
            for k, (lab, note, *_) in enumerate(regimes))
        sub = "<th></th>" + "".join(
            f'<th class="num"'
            + (f' style="border-left:1px solid var(--rule-soft)"' if k else "")
            + '>seats</th><th class="num">share</th>'
            for k in range(len(regimes)))
        cols = ('<colgroup><col style="width:15%">'
                + '<col style="width:9.5%"><col style="width:11.75%">' * 4
                + "</colgroup>")

        def _n_for(p, meds, cm):
            return (max(cm - sum(meds.get(q, 0) for q in REG_PARTIES), 0)
                    if p == "__OTH__" else meds.get(p, 0))

        def _delta(val, base, unit=""):
            d = val - base
            if abs(d) < (0.05 if unit else 0.5):
                return ""
            cls = "up" if d > 0 else "dn"
            mag = f"{abs(d):.1f}" if unit else f"{abs(d):.0f}"
            return f'<span class="rd {cls}">{"+" if d > 0 else "−"}{mag}{unit}</span>'

        base_meds, base_cm = regimes[0][2], regimes[0][3]
        body = ""
        for p in REG_PARTIES + ["__OTH__"]:
            chip = "#8b918b" if p == "__OTH__" else CHIPS[p]
            nm = (f'<span class="chip" style="background:{chip};display:inline-block;'
                  f'width:9px;height:9px;border-radius:2px;margin-right:6px"></span>'
                  f'{"Smaller parties" if p == "__OTH__" else NAMES[p]}')
            n0 = _n_for(p, base_meds, base_cm)
            s0 = n0 / base_cm * 100
            cells = ""
            for k, (lab, note, meds, cm, tm) in enumerate(regimes):
                n = _n_for(p, meds, cm)
                ds = "" if k == 0 else _delta(n, n0)
                dp = "" if k == 0 else _delta(n / cm * 100, s0, "pt")
                gl = ';border-left:1px solid var(--rule-soft)' if k else ""
                cells += (f'<td class="num" style="white-space:nowrap{gl}">{n}{ds}</td>'
                          f'<td class="num" style="color:var(--ink-3);white-space:nowrap">'
                          f'{n / cm:.1%}{dp}</td>')
            body += f"<tr><td>{nm}</td>{cells}</tr>"
        for row_lab, pick in (("Council size", 3), ("Majority line", 4)):
            cells = "".join(
                f'<td class="num" colspan="2"'
                + (' style="border-left:1px solid var(--rule-soft)"' if k else "")
                + f'><b>{rr[pick]}</b></td>'
                for k, rr in enumerate(regimes))
            body += (f'<tr style="border-top:1px solid var(--rule)">'
                     f"<td><b>{row_lab}</b></td>{cells}</tr>")
        regimes_html = (
            "<!-- __REGIMES_START__ -->\n"
            '    <div class="tablewrap"><table style="table-layout:fixed;min-width:820px">'
            f"{cols}"
            f'<thead><tr><th></th>{head}</tr><tr>{sub}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>\n"
            "    <!-- __REGIMES_END__ -->")
        for tgt in (Path("forecast-sheet.html"), Path("drafts/forecast-draft.html")):
            s = tgt.read_text(encoding="utf-8")
            if "__REGIMES_START__" in s:
                a = s.index("<!-- __REGIMES_START__ -->")
                b2 = s.index("<!-- __REGIMES_END__ -->") + len("<!-- __REGIMES_END__ -->")
                tgt.write_text(s[:a] + regimes_html + s[b2:], encoding="utf-8")
        print("regimes table:", " · ".join(
            f"{lab}: council {cm}, thr {tm}" for lab, _, _, cm, tm in regimes))

    html = args.sheet.read_text(encoding="utf-8")
    start = html.index("// __GEN_START__")
    start = html.index("\n", start) + 1
    end = html.index("// __GEN_END__")
    block = f"const GEN = {json.dumps(gen, indent=1)};\n"
    args.sheet.write_text(html[:start] + block + html[end:], encoding="utf-8")

    print(f"rewrote GEN block in {args.sheet}:")
    for t in gen["tiles"]:
        print(f"  tile {t['n']:>5s}  {t['l'][:60]}")
    for c in gen["coalitions"]:
        print(f"  {c['name']:<42s} P={c['p']:.1%}  {c['med']} [{c['lo']}–{c['hi']}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
