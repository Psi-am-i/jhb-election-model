"""Ingest IEC local-government election results to a JHB VD-level subset.

Source files come from
``results.elections.org.za/home/LGEPublicReports/{id}/Downloadable Party Results/GP/JHB.csv``
(id 1091 = 2021, 402 = 2016), which unlike the national/provincial exports are
fetchable with plain curl. See ``SOURCES.md``.

These files are better behaved than the NPE ones -- properly quoted, UTF-8 --
and carry two columns the NPE files lack:

* ``Ward``, giving the VD->ward lookup for that election's delimitation for free;
* ``BallotType``, distinguishing the ``PR`` and ``Ward`` ballots. Per plan §0 the
  PR ballot is the primary modelling target, since seats are compensatory.

As in the 2014 NPE file, ``TotalValidVotes`` is the *party's* votes rather than
the VD total, so the VD total is recomputed per VD and ballot type.

Usage:
    python src/ingest_lge.py <JHB.csv> <year> [--ballot PR|Ward|all]
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
from collections import defaultdict
from pathlib import Path

from iec_csv import (
    active_muni_code,
    muni_code,
    normalise_header,
    sniff_encoding,
    summarise,
    ward_number,
    write_csv,
)

COLUMNS = [
    "Province",
    "Municipality",
    "Ward",
    "VD_Number",
    "VS_Name",
    "BallotType",
    "Registered_Population",
    "Spoilt_Votes",
    "Total_Valid_Votes",
    "sPartyName",
    "Party_Votes",
]


def read_municipality(
    src: Path, code: str | None = None, ballot: str | None = None
) -> list[dict[str, str]]:
    """Return the rows of ``src`` for one municipality, with canonical columns."""
    code = code or active_muni_code()
    with src.open(encoding=sniff_encoding(src), newline="") as handle:
        reader = csv.reader(handle)
        header = [normalise_header(cell) for cell in next(reader)]
        rows = []
        for cells in reader:
            row = dict(zip(header, cells))
            if muni_code(row.get("MUNICIPALITY", "")) != code:
                continue
            if ballot and row["BALLOTTYPE"].strip().upper() != ballot.upper():
                continue
            rows.append(
                {
                    "Province": row["PROVINCE"].strip(),
                    "Municipality": row["MUNICIPALITY"].strip(),
                    "Ward": ward_number(row["WARD"]),
                    "VD_Number": row["VOTINGDISTRICT"].strip(),
                    "VS_Name": row["VOTINGSTATIONNAME"].strip(),
                    "BallotType": row["BALLOTTYPE"].strip(),
                    "Registered_Population": row["REGISTEREDVOTERS"].strip(),
                    "Spoilt_Votes": row["SPOILTVOTES"].strip(),
                    "Total_Valid_Votes": "",
                    "sPartyName": row["PARTYNAME"].strip(),
                    "Party_Votes": row["TOTALVALIDVOTES"].strip(),
                }
            )

    # TotalValidVotes is the party's own votes, so the VD total has to be summed
    # -- separately per ballot type, since a voter casts one of each.
    totals: defaultdict[tuple[str, str], int] = defaultdict(int)
    for row in rows:
        totals[(row["VD_Number"], row["BallotType"])] += int(row["Party_Votes"])
    for row in rows:
        row["Total_Valid_Votes"] = str(totals[(row["VD_Number"], row["BallotType"])])
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("year")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--muni-code", default=None,
                        help="override the active city's IEC code")
    parser.add_argument(
        "--ballot",
        default="all",
        help="keep only this ballot type; 'all' keeps both (default)",
    )
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    ballot = None if args.ballot == "all" else args.ballot
    rows = read_municipality(args.source, args.muni_code, ballot)
    if not rows:
        print(f"no rows for {args.muni_code!r} in {args.source}")
        return 1

    destination = args.out_dir / f"lge{args.year}_{cityconfig.active().code}_vd_party_clean.csv"
    write_csv(destination, COLUMNS, rows)
    print(f"{args.year} -> {destination}  ({len(rows):,} rows)")

    # Summarise each ballot separately; they have different valid-vote totals.
    for kind in sorted({row["BallotType"] for row in rows}):
        subset = [row for row in rows if row["BallotType"] == kind]
        print(f"  --- {kind} ballot ---")
        print(summarise(subset))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
