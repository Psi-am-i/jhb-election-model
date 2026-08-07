"""Export the data pack for the interactive forecast page.

The interactive page (forecast-interactive.html) runs the forecast client-side
so users can move every assumption and watch the seat arithmetic respond. Two
facts make that tractable in a browser:

* **Citywide seat entitlement needs no VD machinery at all.** Both ballots are
  weighted by the same votes-cast vector, and the IPF calibration forces the
  realised citywide share to equal the drawn target — so a draw's combined
  share is simply the mean of its PR and ward targets, and Schedule 1 runs on
  ~15 numbers. The browser reproduces the Python allocation exactly.
* **Ward winners and overhang only need ward-resolution geography.** The page
  runs the same logit-deviation share model over 135 wards instead of 865
  VDs. That is an approximation of the VD-level model (aggregation before
  prediction rather than after); its error against the Python model on the
  central scenario is measured by montecarlo.py and quoted on the page.

The residual micro-party tail is lumped into OTHER client-side; the largest-
remainder arithmetic treats it as one list, which shifts a seat or two of
tail churn but no coalition-relevant quantity — stated on the page.

Output: data/processed/interactive_data.json

Usage:
    python src/export_interactive.py
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
import json
from collections import defaultdict
from pathlib import Path

from fold import citywide, load, load_parameters, shares
from montecarlo import BLOCS, DEFAULTS, PLAN_BOUNDS

# Parties carried individually to the page; the rest is OTHER. Order fixes
# display order. Chip colours are party identification only.
PAGE_PARTIES = [
    ("DA", "DA", "#1B5EA8"),
    ("ANC", "ANC", "#1B7A3D"),
    ("EFF", "EFF", "#B3202B"),
    ("MK", "MK Party", "#5B6E22"),
    ("ASA", "ActionSA", "#2FA79B"),
    ("PA", "Patriotic Alliance", "#E0A419"),
    ("IFP", "IFP", "#C8442A"),
    ("RISE", "Rise Mzansi", "#7A6BA8"),
    ("VFPLUS", "VF+", "#B0752D"),
    ("ACDP", "ACDP", "#6B4E9E"),
    ("ALJAMAAH", "Al Jama-ah", "#2E8B72"),
    ("BOSA", "BOSA", "#3A7CA5"),
]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path,
                        default=Path("data/processed/interactive_data.json"))
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    codes = [c for c, _, _ in PAGE_PARTIES]

    # --- citywide bases -------------------------------------------------------
    base_votes, _ = load(args.data_dir / "npe2024_{CODE}_vd_party.csv", None)
    base_share, base_city = shares(base_votes), citywide(base_votes)
    other_base = 1.0 - sum(base_city.get(c, 0.0) for c in codes) \
        - base_city.get("IND", 0.0)

    ward21, _ = load(args.data_dir / "lge2021_{CODE}_vd_party_clean.csv", "Ward")
    pr21, _ = load(args.data_dir / "lge2021_{CODE}_vd_party_clean.csv", "PR")
    wc, pc = citywide(ward21), citywide(pr21)

    # --- gamma: fold 1, then 2021→2024, then 1.0 (as montecarlo resolves) -----
    params = load_parameters(args.processed / "fold1_parameters.csv")
    recent = {}
    recent_path = args.processed / "gamma_recent.csv"
    if recent_path.exists():
        with recent_path.open(encoding="utf-8", newline="") as fh:
            recent = {r["party"]: float(r["gamma"]) for r in csv.DictReader(fh)}

    def gamma_for(code: str, ballot: str) -> float:
        if code in params[ballot]["gamma"]:
            return params[ballot]["gamma"][code]
        return recent.get(code, 1.0)

    # --- by-election deltas ---------------------------------------------------
    bye = {}
    bye_path = args.processed / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row["party"] in codes:
                    bye[row["party"]] = {
                        "weight_sum": float(row["weight_sum"]),
                        "delta": float(row["weighted_delta"]),
                        "contests": int(row["contests"]),
                    }

    # --- ward-level aggregation ----------------------------------------------
    with (args.processed / "vd_ward_2026.csv").open(encoding="utf-8", newline="") as fh:
        parts = [(r["VD_Number"], r["Ward_2026"], int(r["part_registered"]))
                 for r in csv.DictReader(fh)]

    ratio_pattern, level_pattern = {}, {}
    thi_pattern, tlo_pattern = {}, {}
    with (args.processed / "turnout.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            vd = row["VD_Number"]
            if row["turnout_2026_projected"]:
                ratio_pattern[vd] = float(row["turnout_2026_projected"])
            if row.get("turnout_2026_level"):
                level_pattern[vd] = float(row["turnout_2026_level"])
            # anchors for the who-turns-out sliders: the VD's highest turnout
            # on record, any election 2011-2024 ("all turn out") and its
            # worst local-election turnout on record ("stay home")
            hi = [row.get(f"turnout_{y}") for y in (2011, 2014, 2016, 2019,
                                                    2021, 2024)]
            hi_vals = [float(x) for x in hi if x and x != "nan"]
            if hi_vals:
                thi_pattern[vd] = min(max(hi_vals), 1.0)
            lge = [row.get(f"turnout_{y}") for y in (2011, 2016, 2021)]
            vals = [float(x) for x in lge if x and x != "nan"]
            if vals:
                tlo_pattern[vd] = min(min(vals), 1.0)

    total_reg = sum(reg for _, _, reg in parts)
    reg_with_ratio = sum(reg for vd, _, reg in parts if vd in ratio_pattern) or 1
    reg_with_level = sum(reg for vd, _, reg in parts if vd in level_pattern) or 1
    mean_ratio = sum(ratio_pattern.get(vd, 0) * reg for vd, _, reg in parts) / reg_with_ratio
    mean_level = sum(level_pattern.get(vd, 0) * reg for vd, _, reg in parts) / reg_with_level
    reg_with_thi = sum(reg for vd, _, reg in parts if vd in thi_pattern) or 1
    reg_with_tlo = sum(reg for vd, _, reg in parts if vd in tlo_pattern) or 1
    mean_thi = sum(thi_pattern.get(vd, 0) * reg for vd, _, reg in parts) / reg_with_thi
    mean_tlo = sum(tlo_pattern.get(vd, 0) * reg for vd, _, reg in parts) / reg_with_tlo

    ward_rows: dict[str, dict] = {}
    for vd, ward, reg in parts:
        row = ward_rows.setdefault(ward, {
            "ward": ward, "registered": 0,
            "votes_ratio": 0.0, "votes_level": 0.0,
            "votes_thi": 0.0, "votes_tlo": 0.0,
            "tallies": defaultdict(float), "tally_weight": 0.0,
        })
        row["registered"] += reg
        t_r = ratio_pattern.get(vd, mean_ratio)
        t_l = level_pattern.get(vd, mean_level)
        row["votes_ratio"] += reg * t_r
        row["votes_level"] += reg * t_l
        row["votes_thi"] += reg * thi_pattern.get(vd, mean_thi)
        row["votes_tlo"] += reg * tlo_pattern.get(vd, mean_tlo)
        local = base_share.get(vd)
        if local:
            w = reg * t_r
            row["tally_weight"] += w
            for code in codes:
                row["tallies"][code] += local.get(code, 0.0) * w
            row["tallies"]["OTHER"] += max(
                0.0, 1.0 - sum(local.get(c, 0.0) for c in codes)
                - local.get("IND", 0.0)) * w

    wards_out = []
    for ward in sorted(ward_rows, key=int):
        row = ward_rows[ward]
        tw = row["tally_weight"] or 1.0
        wards_out.append({
            "w": ward,
            "reg": row["registered"],
            "vr": round(row["votes_ratio"]),
            "vl": round(row["votes_level"]),
            "vhi": round(row["votes_thi"]),
            "vlo": round(row["votes_tlo"]),
            "s": [round(row["tallies"][c] / tw, 5) for c in codes]
                 + [round(row["tallies"]["OTHER"] / tw, 5)],
        })

    # --- assemble -------------------------------------------------------------
    blocs = {p: b for b, members in BLOCS.items() for p in members}
    parties_out = []
    for code, name, chip in PAGE_PARTIES:
        parties_out.append({
            "code": code, "name": name, "chip": chip,
            "bloc": blocs.get(code, "IND"),
            "base2024": round(base_city.get(code, 0.0), 5),
            "pr2021": round(pc.get(code, 0.0), 5),
            "ward2021": round(wc.get(code, 0.0), 5),
            "gammaPR": round(gamma_for(code, "PR"), 3),
            "gammaWard": round(gamma_for(code, "Ward"), 3),
            "bounds": PLAN_BOUNDS.get(code),
            "bye": bye.get(code),
        })

    polls = json.loads(Path("polls.json").read_text(encoding="utf-8"))["polls"]
    wp_path = args.processed / "ward_paths.json"
    ward_map = json.loads(wp_path.read_text(encoding="utf-8")) if wp_path.exists() else None

    pack = {
        "generated_from": "src/export_interactive.py",
        "polls": polls,
        "ward_map": ward_map,
        "parties": parties_out,
        "other_base2024": round(other_base, 5),
        "wards": wards_out,
        "defaults": DEFAULTS,
        "citywide_turnout_projection": round(mean_ratio, 4),
        "registered_total": total_reg,
    }
    with args.out.open("w", encoding="utf-8") as handle:
        json.dump(pack, handle, separators=(",", ":"))
    size = args.out.stat().st_size
    print(f"wrote {args.out} ({size / 1024:.0f} KB, {len(wards_out)} wards, "
          f"{len(parties_out)} parties + OTHER)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
