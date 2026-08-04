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
        return (int(np.median(series)), int(np.percentile(series, 5)),
                int(np.percentile(series, 95)))

    def coalition(*members):
        total = sum(S[p] for p in members if p in S)
        med, lo, hi = q(total)
        return {"p": round(float((total >= thr).mean()), 4),
                "med": med, "lo": lo, "hi": hi}

    # largest party
    stack = np.stack([S[p] for p in parties])
    largest = stack.argmax(axis=0)
    p_da_largest = float((np.array(parties)[largest] == "DA").mean())

    p_overhang = summary["p_overhang"]
    thr_med = int(np.median(thr))
    minority = {m["scenario"]: m["p_viable"] for m in summary["minority"]}
    da_minority = minority.get("DA minority, only ANC opposes (2021 pattern)", 0.0)
    anc_da = coalition("ANC", "DA")

    gen = {
        "tiles": [
            {"n": f"{anc_da['p']:.0%}", "hero": True,
             "l": "Chance an ANC–DA coalition clears the majority — the only pairing that reliably can"},
            {"n": f"{p_overhang:.0%}",
             "l": f"Simulations where overhang expands the council — median threshold {thr_med}, not 136"},
            {"n": f"{da_minority:.0%}",
             "l": "A DA minority government is viable if only the ANC votes against (the 2021 pattern)"},
            {"n": f"{p_da_largest:.0%}",
             "l": "Simulations in which the DA is the largest single party"},
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
            {"name": "DA + EFF + ActionSA", **coalition("DA", "EFF", "ASA")},
            {"name": "DA + EFF + MK", **coalition("DA", "EFF", "MK")},
            {"name": "ANC + EFF + MK", **coalition("ANC", "EFF", "MK")},
            {"name": "DA + ActionSA", **coalition("DA", "ASA")},
        ],
        "minority_da_2021": round(da_minority, 4),
        "meta": {"threshold_median": thr_med,
                 "council_median": int(np.median(council)),
                 "p_overhang": round(p_overhang, 4)},
    }

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
