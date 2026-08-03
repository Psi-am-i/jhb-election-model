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
import csv
from collections import Counter
from pathlib import Path

from seats import INDEPENDENT, allocate, eligible_parties

# Published by the IEC for CoJ 2021, keyed by combined ward+PR votes because the
# report's party names wrap across lines in the PDF and vote totals are unique.
OFFICIAL_2021 = {
    620_289: ("AFRICAN NATIONAL CONGRESS", 91),
    482_653: ("DEMOCRATIC ALLIANCE", 71),
    296_345: ("ACTIONSA", 44),
    196_163: ("ECONOMIC FREEDOM FIGHTERS", 29),
    54_176: ("PATRIOTIC ALLIANCE", 8),
    43_544: ("INKATHA FREEDOM PARTY", 7),
    24_671: ("VRYHEIDSFRONT PLUS", 4),
    19_468: ("AFRICAN CHRISTIAN DEMOCRATIC PARTY", 3),
    17_608: ("AL JAMA-AH", 3),
    10_960: ("AFRICAN INDEPENDENT CONGRESS", 2),
}
OFFICIAL_QUOTA_2021 = 6_794
OFFICIAL_A_2021 = 1_834_260

# Quota and total-valid-votes as published on each year's Seat Calculation
# Detail report, so every year self-asserts rather than leaving a reviewer to
# check figures by eye. 2011 ran on a 260-seat council.
OFFICIAL_HEADLINE = {
    "2011": {"quota": 8_319, "A": 2_162_768, "seats": 260},
    "2016": {"quota": 9_247, "A": 2_496_617, "seats": 270},
    "2021": {"quota": 6_794, "A": 1_834_260, "seats": 270},
}


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
        "--seats",
        type=int,
        default=270,
        help="council size; CoJ was 260 under the 2011 delimitation",
    )
    args = parser.parse_args(argv)

    path = args.data_dir / f"lge{args.year}_JHB_vd_party_clean.csv"
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
        total_seats=args.seats,
        independent_wards=independent_wards,
        no_pr_list_wards=no_pr_list_wards,
    )

    print(f"CoJ {args.year}")
    print(f"  A (total valid votes, both ballots, eligible parties) = {result.total_votes:,}")
    print(f"  C (independent ward councillors) = {independent_wards}")
    print(f"  D (ward seats, parties with no PR list) = {no_pr_list_wards}")
    print(f"  quota Q = {result.quota:,}   seats allocated = {sum(result.seats.values()):,}")
    print(f"  excluded from A: {[p for p in excluded if p not in combined]}")
    print(f"  wards won: {sum(wins.values())} across {len(wins)} parties")

    headline = OFFICIAL_HEADLINE.get(args.year)
    if headline:
        ok_quota = result.quota == headline["quota"]
        ok_a = result.total_votes == headline["A"]
        ok_seats = sum(result.seats.values()) == headline["seats"]
        print(
            f"\n  vs IEC published: quota {headline['quota']:,}"
            f" {'MATCH' if ok_quota else 'MISMATCH'}"
            f" | A {headline['A']:,} {'MATCH' if ok_a else 'MISMATCH'}"
            f" | seats {headline['seats']} {'MATCH' if ok_seats else 'MISMATCH'}"
        )

    if args.year != "2021":
        for party, count in result.top():
            print(f"    {party:<45s} {count:>3d}")
        if headline and not (ok_quota and ok_a and ok_seats):
            print("\n  FAIL: does not reproduce the published headline figures")
            return 1
        print("\n  PASS: reproduces the published quota, total valid votes and council size")
        return 0

    print(f"\n  vs IEC published (quota {OFFICIAL_QUOTA_2021:,}, A {OFFICIAL_A_2021:,}):")
    ok = result.quota == OFFICIAL_QUOTA_2021 and result.total_votes == OFFICIAL_A_2021
    print(f"    quota {'MATCH' if result.quota == OFFICIAL_QUOTA_2021 else 'MISMATCH'}"
          f"   A {'MATCH' if result.total_votes == OFFICIAL_A_2021 else 'MISMATCH'}")

    by_votes = {votes: party for party, votes in combined.items()}
    for votes, (name, expected) in sorted(OFFICIAL_2021.items(), reverse=True):
        party = by_votes.get(votes)
        got = result.seats.get(party) if party else None
        flag = "ok " if got == expected else "BAD"
        ok &= got == expected
        print(f"    {flag} {name:<42s} {votes:>9,}  expected {expected:>3d}  got {got}")

    print(f"\n  {'PASS' if ok else 'FAIL'}: allocator reproduces the published council")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
