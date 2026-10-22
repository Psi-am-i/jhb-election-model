"""Build and check the party crosswalk across every source file.

Emits ``data/processed/party_crosswalk.csv`` -- one row per distinct raw party
string, with its canonical code and the elections it appears in -- and
runs the checks that matter:

* every canonical code that won seats is one we track deliberately, not a
  name-derived fallback that could drift between elections;
* no two raw strings for the same real party map to different codes (caught by
  eyeballing the ``sources`` column: a party present in six elections should
  appear on one row, not several);

Usage:
    python src/build_crosswalk.py
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
from collections import Counter, defaultdict
from pathlib import Path

import parties as P

ELECTIONS = {
    "2011 LGE": "lge2011_{CODE}_vd_party_clean.csv",
    "2014 NPE": "npe2014_{CODE}_vd_party.csv",
    "2016 LGE": "lge2016_{CODE}_vd_party_clean.csv",
    "2019 NPE": "npe2019_{CODE}_vd_party.csv",
    "2021 LGE": "lge2021_{CODE}_vd_party_clean.csv",
    "2024 NPE": "npe2024_{CODE}_vd_party.csv",
}

# Parties that took CoJ seats in 2016 or 2021. Each must resolve to a
# hand-maintained code -- a name-derived fallback would be fragile for something
# the seat allocator depends on.
def seat_winners(city) -> set[str]:
    """Parties that actually won a seat in this city, from the IEC's own
    reports rather than a hand-kept list.

    The list used to be Johannesburg's, so building any other metro failed on
    a CoJ micro-party that had never contested there.
    """
    import official_seats
    from parties import canonical
    found: set[str] = set()
    for year in (2011, 2016, 2021):
        official = official_seats.read(city.code, year)
        if not official:
            continue
        for name, row in official["parties"].items():
            if row["seats"] > 0:
                found.add(canonical(name))
    return found


def read_votes(path: Path, ballot: str | None = None) -> Counter[str]:
    """Total votes by raw party string.

    ``ballot`` selects one ballot from an LGE file ("PR" or "Ward"); None sums
    both, which is the seat-determining quantity per plan §0. NPE files have a
    single ballot and ignore it.
    """
    totals: Counter[str] = Counter()
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if ballot and row.get("BallotType", ballot).upper() != ballot.upper():
                continue
            totals[row["sPartyName"].strip()] += int(row["Party_Votes"])
    return totals


def read_byelection_names(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as handle:
        return {
            row["PartyFullName"].strip()
            for row in csv.DictReader(handle)
            if row["PartyFullName"].strip()
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--byelections", type=Path,
                        default=Path("data/raw/byelections/byelections_Gauteng_vd_party.csv"))
    parser.add_argument("--out", type=Path, default=Path("data/processed/party_crosswalk.csv"))
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    sources: defaultdict[str, set[str]] = defaultdict(set)
    peak: defaultdict[str, float] = defaultdict(float)
    per_election: dict[str, Counter[str]] = {}

    for label, filename in ELECTIONS.items():
        totals = read_votes(args.data_dir / filename)
        per_election[label] = totals
        cast = sum(totals.values())
        for raw, votes in totals.items():
            sources[raw].add(label)
            peak[raw] = max(peak[raw], votes / cast)

    for raw in read_byelection_names(args.byelections):
        sources[raw].add("by-elections")

    rows = []
    for raw in sorted(sources):
        code = P.canonical(raw)
        rows.append(
            {
                "raw_name": raw,
                "canonical": code,
                "display_name": P.display_name(code),
                "has_theta": "Y" if P.is_modelled(code) else "",
                "peak_share": f"{peak.get(raw, 0):.5f}",
                "sources": "; ".join(sorted(sources[raw])),
            }
        )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    codes = {r["canonical"] for r in rows}
    print(f"{len(rows)} raw party strings -> {len(codes)} canonical parties")
    print(f"wrote {args.out}\n")

    # Which raw strings collapsed together -- the whole point of the exercise.
    merged: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        merged[row["canonical"]].append(row["raw_name"])
    for code, names in sorted(merged.items()):
        if len(names) > 1:
            print(f"  merged into {code}: {names}")

    failures = []
    tracked = set(P.PARTIES) | set(P.MINOR_ALIASES.values())
    for code in sorted(seat_winners(cityconfig.active())):
        if code not in codes:
            failures.append(f"seat-winning party {code} never appears in the data")
        elif code not in tracked:
            failures.append(f"seat-winning party {code} relies on a derived code")

    # Merging two raw strings is only ever correct when it was asked for
    # explicitly. A merge that happens via a derived code is a collision.
    for code, names in sorted(merged.items()):
        if len(names) > 1 and code not in tracked:
            failures.append(f"derived code {code} collides across {names}")

    # A grouped-share anchor table stood here, rolling parties into a handful
    # of buckets someone had chosen and reporting the swing of each. The model
    # no longer groups parties by judgement: it fits each one's voter pools from
    # ward demographics. `python src/pools.py --city <city> --target <year>`
    # prints the measured equivalent.

    if failures:
        print("\nFAIL:")
        for problem in failures:
            print(f"  - {problem}")
        return 1
    print("\nPASS: every seat-winning party has a hand-maintained code")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
