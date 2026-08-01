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
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

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

# Municipalities are written "JHB - City of Johannesburg" in one layout and
# "JHB - CITY OF JOHANNESBURG [JOHANNESBURG]" in the other, so match on the code.
MUNI_CODE = "JHB"

# Tried in order; the first that decodes the whole file wins. CP850 never fails,
# so it must come last.
ENCODINGS = ("utf-8-sig", "cp850")


def _normalise(name: str) -> str:
    """Map a raw header cell onto its canonical form.

    Strips the BOM and whitespace, folds case, replaces the volatile
    ``Generated Datetime: <timestamp>`` header with a stable name, then
    collapses spaces to underscores.
    """
    name = name.lstrip("﻿").strip()
    if name.upper().startswith("GENERATED DATETIME"):
        return "GENERATED_DATETIME"
    return name.upper().replace(" ", "_")


def sniff_encoding(src: Path) -> str:
    """Return the first encoding in :data:`ENCODINGS` that decodes ``src`` cleanly."""
    data = src.read_bytes()
    for encoding in ENCODINGS:
        try:
            data.decode(encoding)
        except UnicodeDecodeError:
            continue
        return encoding
    raise ValueError(f"{src.name}: no candidate encoding decodes the file")


def _is_int(cell: str) -> bool:
    return cell.strip().lstrip("-").isdigit()


def _muni_code(municipality: str) -> str:
    return municipality.split("-")[0].strip().upper()


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
    while cells and not _is_int(cells[-1]):
        cells.pop()
    if len(cells) < 8:
        raise ValueError(f"too few columns: {row!r}")

    party_votes = cells.pop()
    party_name = cells.pop()
    valid, spoilt, registered = cells.pop(), cells.pop(), cells.pop()
    if not all(_is_int(value) for value in (valid, spoilt, registered)):
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
    src: Path, muni_code: str = MUNI_CODE, event: str | None = None
) -> list[dict[str, str]]:
    """Return the rows of ``src`` for one municipality, with canonical columns.

    ``event`` filters the 2014 bulk file to one ballot (``NATIONAL`` or
    ``PROVINCIAL``); it is ignored by the results-portal layout, whose files
    already contain a single ballot.
    """
    with src.open(encoding=sniff_encoding(src), newline="") as handle:
        reader = csv.reader(handle)
        header = [_normalise(cell) for cell in next(reader)]

        if "ELECTORAL_EVENT" in header:
            rows = _read_bulk(reader, header, muni_code, event)
        else:
            rows = _read_portal(reader, muni_code)

    return rows


def _read_portal(reader, muni_code: str) -> list[dict[str, str]]:
    rows, shifted = [], set()
    for row in reader:
        if len(row) < 2 or _muni_code(row[1]) != muni_code:
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


def _read_bulk(reader, header: list[str], muni_code: str, event: str | None) -> list[dict[str, str]]:
    rows = []
    for cells in reader:
        row = dict(zip(header, cells))
        if _muni_code(row.get("MUNICIPALITY", "")) != muni_code:
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


def summarise(rows: list[dict[str, str]], top: int = 10) -> str:
    """Format a turnout and party-share summary, for eyeballing against §8 anchors."""
    # Registration/turnout columns repeat on every party row for a VD, so
    # collapse to one row per VD before summing.
    per_vd = {row["VD_Number"]: row for row in rows}
    registered = sum(int(r["Registered_Population"]) for r in per_vd.values())
    valid = sum(int(r["Total_Valid_Votes"]) for r in per_vd.values())
    spoilt = sum(int(r["Spoilt_Votes"]) for r in per_vd.values())

    votes: Counter[str] = Counter()
    for row in rows:
        votes[row["sPartyName"]] += int(row["Party_Votes"])

    wards = {row["Ward"] for row in rows if row["Ward"]}
    lines = [
        f"  VDs {len(per_vd):,}   wards {len(wards) or '-'}   parties {len(votes)}",
        f"  registered {registered:,}   valid {valid:,}   spoilt {spoilt:,}"
        f"   turnout {(valid + spoilt) / registered:.2%}",
    ]
    lines += [
        f"    {party:<45s} {count:>8,}  {count / valid:>6.2%}"
        for party, count in votes.most_common(top)
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="unzipped national CSV")
    parser.add_argument("year", help="election year, used in the output filename")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--muni-code", default=MUNI_CODE)
    parser.add_argument(
        "--event",
        default="PROVINCIAL",
        help="ballot to keep from a combined file (2014 only)",
    )
    args = parser.parse_args(argv)

    rows = read_municipality(args.source, args.muni_code, args.event)
    if not rows:
        print(f"no rows for {args.muni_code!r} in {args.source}", file=sys.stderr)
        return 1

    destination = args.out_dir / f"npe{args.year}_JHB_vd_party.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"{args.year} -> {destination}  ({len(rows):,} rows)")
    print(summarise(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
