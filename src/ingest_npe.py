"""Ingest IEC national/provincial election bulk result files to a JHB VD-level subset.

The IEC publishes VD-level results in two quite different layouts, and this
module normalises both onto :data:`COLUMNS`.

**Results-portal layout** (2019, 2024) --
``results.elections.org.za/home/NPEPublicReports/{id}/Downloadable Results/Provincial.zip``,
one row per VD x party. Awkward in three ways:

* header punctuation drifts (2024 ``VD_Number``, 2019 ``VD Number`` plus a
  trailing empty column);
* encoding drifts (2024 UTF-8, 2019 DOS CP850 -- ``SIWENDU CAF\\x90`` is CAFÉ);
* voting-station names are written *unquoted*, so a name containing a comma
  silently shifts every column after it.

**2014 bulk layout** --
``www.elections.org.za/content/Elections/Downloadable-results/...``, properly
quoted, covers the national and provincial ballots in one file, and carries the
2011-delimitation ward number. Its ``VALID VOTES`` column is the *party's*
votes, not the VD total, so the VD total is recomputed by summing parties.

Usage:
    python src/ingest_npe.py <source.csv> <year> [--event PROVINCIAL]
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
import sys
from collections import defaultdict
from pathlib import Path

from iec_csv import (
    active_muni_code,
    is_int,
    muni_code,
    normalise_header,
    sniff_encoding,
    summarise,
    write_csv,
)

# Canonical column names, in output order. Ward is blank for the results-portal
# layout, which does not carry it.
COLUMNS = [
    "Province",
    "Municipality",
    "Ward",
    "VD_Number",
    "VS_Name",
    "Registered_Population",
    "Spoilt_Votes",
    "Total_Valid_Votes",
    "sPartyName",
    "Party_Votes",
]


def parse_portal_row(row: list[str]) -> dict[str, str]:
    """Parse one results-portal row, tolerating unquoted commas in the station name.

    The row is anchored at both ends rather than by position: the first three
    cells are fixed, the tail is recovered by walking back from the right past
    any trailing datetime/padding cells, and whatever is left in the middle is
    the station name rejoined.
    """
    cells = [cell.strip() for cell in row]
    # Drop trailing padding and the Generated_Datetime column, which is empty on
    # some rows, a timestamp on others, and pushed off the end on shifted rows.
    while cells and not is_int(cells[-1]):
        cells.pop()
    if len(cells) < 8:
        raise ValueError(f"too few columns: {row!r}")

    party_votes = cells.pop()
    party_name = cells.pop()
    valid, spoilt, registered = cells.pop(), cells.pop(), cells.pop()
    if not all(is_int(value) for value in (valid, spoilt, registered)):
        raise ValueError(f"non-numeric vote columns: {row!r}")

    station = ", ".join(cells[3:])
    if not station:
        raise ValueError(f"empty voting-station name: {row!r}")

    return {
        "Province": cells[0],
        "Municipality": cells[1],
        "Ward": "",
        "VD_Number": cells[2],
        "VS_Name": station,
        "Registered_Population": registered,
        "Spoilt_Votes": spoilt,
        "Total_Valid_Votes": valid,
        "sPartyName": party_name,
        "Party_Votes": party_votes,
    }


def parse_bulk_row(row: dict[str, str]) -> dict[str, str]:
    """Parse one 2014-bulk row. ``Total_Valid_Votes`` is filled in afterwards."""
    return {
        "Province": row["PROVINCE"].strip(),
        "Municipality": row["MUNICIPALITY"].strip(),
        "Ward": row["WARD"].strip(),
        "VD_Number": row["VOTING_DISTRICT"].strip(),
        "VS_Name": "",
        "Registered_Population": row["REGISTERED_VOTERS"].strip(),
        "Spoilt_Votes": row["SPOILT_VOTES"].strip(),
        "Total_Valid_Votes": "",
        "sPartyName": row["PARTY_NAME"].strip(),
        "Party_Votes": row["VALID_VOTES"].strip(),
    }


def read_municipality(
    src: Path, code: str | None = None, event: str | None = None
) -> list[dict[str, str]]:
    """Return the rows of ``src`` for one municipality, with canonical columns.

    ``event`` filters the 2014 bulk file to one ballot (``NATIONAL`` or
    ``PROVINCIAL``); it is ignored by the results-portal layout, whose files
    already contain a single ballot.
    """
    code = code or active_muni_code()
    with src.open(encoding=sniff_encoding(src), newline="") as handle:
        reader = csv.reader(handle)
        header = [normalise_header(cell) for cell in next(reader)]

        if "ELECTORAL_EVENT" in header:
            rows = _read_bulk(reader, header, code, event)
        else:
            rows = _read_portal(reader, code)

    return rows


def _read_portal(reader, code: str) -> list[dict[str, str]]:
    rows, shifted = [], set()
    for row in reader:
        if len(row) < 2 or muni_code(row[1]) != code:
            continue
        parsed = parse_portal_row(row)
        if "," in parsed["VS_Name"]:
            shifted.add(parsed["VD_Number"])
        rows.append(parsed)

    if shifted:
        print(
            f"  realigned {len(shifted)} VD(s) whose station name contained a comma: "
            + ", ".join(sorted(shifted)),
            file=sys.stderr,
        )
    return rows


def _read_bulk(reader, header: list[str], code: str, event: str | None) -> list[dict[str, str]]:
    rows = []
    for cells in reader:
        row = dict(zip(header, cells))
        if muni_code(row.get("MUNICIPALITY", "")) != code:
            continue
        if event and event.upper() not in row["ELECTORAL_EVENT"].upper():
            continue
        rows.append(parse_bulk_row(row))

    # This layout's VALID VOTES is the party's own votes, so the VD total has to
    # be summed rather than read off.
    totals: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        totals[row["VD_Number"]] += int(row["Party_Votes"])
    for row in rows:
        row["Total_Valid_Votes"] = str(totals[row["VD_Number"]])
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="unzipped national CSV")
    parser.add_argument("year", help="election year, used in the output filename")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--muni-code", default=None,
                        help="override the active city's IEC code")
    parser.add_argument(
        "--event",
        default="PROVINCIAL",
        help="ballot to keep from a combined file (2014 only)",
    )
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    rows = read_municipality(args.source, args.muni_code, args.event)
    if not rows:
        print(f"no rows for {args.muni_code!r} in {args.source}", file=sys.stderr)
        return 1

    destination = args.out_dir / f"npe{args.year}_{cityconfig.active().code}_vd_party.csv"
    write_csv(destination, COLUMNS, rows)
    print(f"{args.year} -> {destination}  ({len(rows):,} rows)")
    print(summarise(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
