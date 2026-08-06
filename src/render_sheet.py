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
from pathlib import Path

import numpy as np

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
}
CHART_PARTIES = ["DA", "ANC", "EFF", "ASA", "MK", "PA", "IFP", "RISE",
                 "ALJAMAAH", "ENTRANT"]

ALLIANCE_8 = ("DA", "ASA", "PA", "IFP", "VFPLUS", "ACDP", "RISE", "ALJAMAAH")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--sheet", type=Path, default=Path("forecast-sheet.html"))
    args = parser.parse_args(argv)

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
    alone_str = (f"{p_alone:.0%}" if p_alone >= 0.001
                 else "<0.1%" if p_alone > 0 else "0%")

    p_excessive = summary.get("p_excessive_by_party", {}).get("ANC", 0.0)
    thr_med = int(np.median(thr))
    minority = {m["scenario"]: m["p_viable"] for m in summary["minority"]}
    da_minority = minority.get("DA minority, only ANC opposes (2021 pattern)", 0.0)
    anc_da = coalition("ANC", "DA")

    gen = {
        "tiles": [
            {"n": f"{anc_da['p']:.0%}", "hero": True,
             "l": "Chance an ANC–DA coalition clears the majority — the only pairing that reliably can"},
            {"n": f"{p_excessive:.0%}",
             "l": "Chance the ANC triggers the excessive-seats clause — keeping every ward it "
                  "wins, taking zero list seats, the shortfall falling on every other party"},
            {"n": f"{da_minority:.0%}",
             "l": "Chance a DA minority government is viable, if only the ANC votes against it (the 2021 pattern)"},
            {"n": f"{p_da_largest:.0%}",
             "l": "Chance the DA is the largest single party"},
            {"n": f"{p_anc_largest:.0%}",
             "l": "Chance the ANC is the largest single party"},
            {"n": alone_str,
             "l": "Chance any party governs alone — a single party reaching the 136-seat "
                  "majority by itself"},
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

    OTHER = "__other__"
    named = [(pty, v) for pty, v in sorted(summary["parties"].items(),
                                           key=lambda kv: -kv[1]["median"])
             if NAMES.get(pty) and CHIPS.get(pty) and round(v["median"]) >= 3]
    ward_raw = {pty: float(v.get("ward_wins_mean", 0.0)) for pty, v in named}
    tot_raw = {pty: float(v["median"]) for pty, v in named}
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
    if anc_list == 0:
        anc_note = ("Note the ANC's list bar: <b>zero</b>. Its ward wins meet its full "
                    "proportional share, so the excessive-seats clause strips its list seats "
                    "entirely and everyone else's shrink to fit")
    else:
        n_word = "a single seat" if anc_list == 1 else f"just {anc_list} seats"
        anc_note = (f"Note the ANC's list bar: <b>{n_word}</b>. Its ward wins soak up nearly "
                    "its whole proportional share, leaving next to nothing to come off the list")
    ballots_caption = (f"Hover a segment for its seats. {anc_note} — while ActionSA, with "
                       "broad support but no stronghold wards, lives almost wholly on the "
                       "list. Two opposite ways of turning votes into seats, in one city.")
    strip = f"""<!-- __BALLOTS_START__ -->
  <section>
    <div class="eyebrow">The arithmetic — two ballots, one council</div>
    <h2>135 wards + 135 list seats = 270</h2>
    <div style="display:flex;flex-direction:column;gap:14px">
      {bar(wardsb, 135, "Ward seats — won race by race")}
      {bar(listb, 135, "+ List seats — topping parties up to their share")}
      {bar(totb, 270, "= The council")}
    </div>
    <figcaption>{ballots_caption}</figcaption>
  </section>
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
            ("deduct", "South African law", "fixed 270, others squeezed"),
            ("expand", "Old Germany", "council grows by the excess"),
            ("level", "Modern Germany", "levelled to proportionality")):
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
        head = "".join(f'<th colspan="2" style="text-align:center">{lab}'
                       f'<br><span style="font-weight:400;color:var(--ink-3)">{note}</span></th>'
                       for lab, note, *_ in regimes)
        sub = "<th></th>" + "".join('<th class="num">seats</th><th class="num">share</th>'
                                    for _ in regimes)
        body = ""
        for p in REG_PARTIES + ["__OTH__"]:
            nm = "Smaller parties" if p == "__OTH__" else NAMES[p]
            cells = ""
            for lab, note, meds, cm, tm in regimes:
                n = (max(cm - sum(meds.get(q, 0) for q in REG_PARTIES), 0)
                     if p == "__OTH__" else meds.get(p, 0))
                cells += (f'<td class="num">{n}</td>'
                          f'<td class="num" style="color:var(--ink-3)">{n / cm:.1%}</td>')
            body += f"<tr><td>{nm}</td>{cells}</tr>"
        for row_lab, pick in (("Council size", 3), ("Majority line", 4)):
            cells = "".join(f'<td class="num" colspan="2"><b>{r[pick]}</b></td>'
                            for r in regimes)
            body += (f'<tr style="border-top:1px solid var(--rule)">'
                     f"<td><b>{row_lab}</b></td>{cells}</tr>")
        regimes_html = (
            "<!-- __REGIMES_START__ -->\n"
            '    <div class="tablewrap"><table>'
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
