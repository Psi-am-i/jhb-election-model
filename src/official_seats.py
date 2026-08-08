"""Read the IEC's own Seat Calculation Detail as the validation ground truth.

`validate_seats.py` used to carry Johannesburg's published 2011/2016/2021
results as hand-typed tables. On any other metro that silently compared the
new city's arithmetic against Joburg's answers — the failure mode this whole
refactor exists to prevent.

The IEC publishes the authoritative numbers per municipality in a machine
-readable spreadsheet: quota, total valid votes, seats available, the
independent and no-list deductions, and every party's votes and final seats.
Parsing it means the expected values are never typed, for any city.

    from official_seats import read
    o = read("TSH", 2021)
    o["quota"], o["A"], o["seats"], o["parties"]["ACTIONSA"]
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

REPORTS = Path("data/raw/elections/_reports")

# The IEC changed both the wording AND the letter scheme between elections.
# 2021 labels the valid-vote total explicitly; 2011 does not, and reuses (A)
# for the seat count that 2021 leaves unlettered. Match on wording, never on
# the letters, and derive anything the older layout omits.
LABELS = {
    "quota": ("Quota",),
    "A": ("Total Valid Votes",),
    "seats": ("Total Seats Available",),
    "independents": ("Independent Ward Council", "Independent Seats Won"),
    "no_list": ("Ward Councillors Seats f", "Ward Councillors from Parties"),
}


def read(code: str, year: int, reports: Path = REPORTS) -> dict | None:
    """Official figures for one municipality-year, or None if not on disk."""
    path = reports / f"lge{year}_{code}_seat_calculation_detail.xls"
    if not path.exists():
        return None
    frame = pd.read_excel(path, header=None)

    out: dict = {"path": str(path), "parties": {}}
    for key, labels in LABELS.items():
        for _, row in frame.iterrows():
            first = str(row.iloc[0])
            if any(first.startswith(l) for l in labels):
                nums = [v for v in row[1:] if isinstance(v, (int, float))
                        and not pd.isna(v)]
                if nums:
                    out[key] = int(nums[0])
                break

    # the party table starts at the row whose first cell is "Party Name";
    # its last numeric column is the party's final seat count
    start = None
    for i, row in frame.iterrows():
        if str(row.iloc[0]).strip() == "Party Name":
            start = i + 1
            break
    if start is None:
        return out


    for _, row in frame.iloc[start:].iterrows():
        name = str(row.iloc[0]).strip()
        if not name or name == "nan" or name.lower().startswith("total"):
            continue
        nums = [v for v in row[1:] if isinstance(v, (int, float)) and not pd.isna(v)]
        if len(nums) < 2:
            continue
        out["parties"][name.upper()] = {"votes": int(nums[0]),
                                        "seats": int(nums[-1])}

    if "A" not in out and out["parties"]:
        # the 2011 layout omits the valid-vote total; it is the sum of the
        # party rows the quota was computed over
        out["A"] = sum(p["votes"] for p in out["parties"].values())
        out["A_derived"] = True
    return out


if __name__ == "__main__":
    import sys
    code = sys.argv[1] if len(sys.argv) > 1 else "JHB"
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2021
    o = read(code, year)
    if not o:
        raise SystemExit(f"no seat calculation detail for {code} {year}")
    print(f"{code} {year}: quota {o.get('quota'):,} · A {o.get('A'):,} · "
          f"{o.get('seats')} seats · {len(o['parties'])} parties")
    for name, d in sorted(o["parties"].items(), key=lambda kv: -kv[1]["seats"])[:8]:
        print(f"  {name[:40]:40s} {d['votes']:>9,}  {d['seats']:>3d}")
