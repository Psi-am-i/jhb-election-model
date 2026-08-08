"""Check :mod:`seats` against the IEC's published seat calculation.

Reproduces the CoJ council from the VD-level result files alone and compares
against the official "Seat Calculation Detail" report. This is the regression
test for the seat allocator -- if it stops matching, the model's output is wrong
regardless of how good the vote forecast is.

Usage:
    python src/validate_seats.py [--year 2021]
"""

from __future__ import annotations

import argparse

import cityconfig
import official_seats
import csv
from collections import Counter
from pathlib import Path

from seats import INDEPENDENT, allocate, eligible_parties

# The expected figures come from the IEC's own Seat Calculation Detail for
# whichever city is being validated (official_seats.py). They used to be
# hand-typed Johannesburg tables, which meant any other metro was silently
# checked against Joburg's published council.

def load_votes(path: Path) -> tuple[dict[str, int], dict[str, int]]:
    """Return (ward votes, PR votes) by party from a cleaned LGE file."""
    ward: Counter[str] = Counter()
    pr: Counter[str] = Counter()
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            bucket = ward if row["BallotType"].upper() == "WARD" else pr
            bucket[row["sPartyName"]] += int(row["Party_Votes"])
    return dict(ward), dict(pr)


def ward_winners(path: Path) -> Counter[str]:
    """Return ward wins by party: the top party on the ward ballot in each ward."""
    totals: dict[str, Counter[str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["BallotType"].upper() != "WARD":
                continue
            totals.setdefault(row["Ward"], Counter())[row["sPartyName"]] += int(
                row["Party_Votes"]
            )
    return Counter(party.most_common(1)[0][0] for party in totals.values())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", default="2021")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument(
        "--seats", type=int, default=None,
        help="council size; defaults to the IEC's published figure for that "
             "year, which is not constant even within a city",
    )
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    city = cityconfig.active()
    official = official_seats.read(city.code, int(args.year))
    if official is None:
        raise SystemExit(
            f"no Seat Calculation Detail for {city.code} {args.year} — fetch it "
            f"with: python src/fetch_iec.py --muni {city.code} "
            f"--province {city.province}")
    seats_total = args.seats or official["seats"]

    path = args.data_dir / f"lge{args.year}_{city.code}_vd_party_clean.csv"
    ward, pr = load_votes(path)
    combined = eligible_parties(ward, pr)
    wins = ward_winners(path)

    excluded = sorted(set(ward) | set(pr) - set(combined))
    independent_wards = wins.get(INDEPENDENT, 0)
    no_pr_list_wards = sum(
        count for party, count in wins.items() if party not in combined and party != INDEPENDENT
    )

    result = allocate(
        combined,
        total_seats=seats_total,
        independent_wards=independent_wards,
        no_pr_list_wards=no_pr_list_wards,
    )

    print(f"{city.name} {args.year}  (source: {Path(official['path']).name})")
    print(f"  A (total valid votes, both ballots, eligible parties) = {result.total_votes:,}")
    print(f"  C (independent ward councillors) = {independent_wards}")
    print(f"  D (ward seats, parties with no PR list) = {no_pr_list_wards}")
    print(f"  quota Q = {result.quota:,}   seats allocated = {sum(result.seats.values()):,}")
    print(f"  wards won: {sum(wins.values())} across {len(wins)} parties")

    ok_quota = result.quota == official["quota"]
    ok_a = result.total_votes == official["A"]
    ok_seats = sum(result.seats.values()) == official["seats"]
    print(f"\n  vs IEC published: quota {official['quota']:,} "
          f"{'MATCH' if ok_quota else 'MISMATCH'} | A {official['A']:,} "
          f"{'MATCH' if ok_a else 'MISMATCH'} | seats {official['seats']} "
          f"{'MATCH' if ok_seats else 'MISMATCH'}")

    # per-party: the official table is keyed on the IEC's own party names
    bad = 0
    rows = sorted(official["parties"].items(), key=lambda kv: -kv[1]["seats"])
    for name, want in rows:
        if want["seats"] == 0:
            continue
        got = result.seats.get(name)
        flag = "ok " if got == want["seats"] else "BAD"
        if flag == "BAD":
            bad += 1
        print(f"    {flag} {name[:42]:42s} {want['votes']:>9,}  "
              f"expected {want['seats']:>3d}  got {got if got is not None else '-'}")

    if bad or not (ok_quota and ok_a and ok_seats):
        print(f"\n  FAIL: {bad} party mismatch(es); the allocator does not "
              f"reproduce {city.name}'s published council")
        return 1
    print(f"\n  PASS: reproduces {city.name}'s published quota, valid votes, "
          f"council size and every party's seats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
