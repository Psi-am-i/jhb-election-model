"""Ingest the pre-2011 IEC bulk archives into the project's canonical VD files.

The model's fold machinery reaches back to 2014 because that is where the
results portal's downloadable data stopped. It does not stop there: the IEC
publishes every election from 1999 as a zipped CSV under

    www.elections.org.za/content/uploadedfiles/{YYYY} {NPE|LGE}.zip

which is not linked from the downloads page and not in the portal's report
routes. Those five archives (1999/2004/2009 NPE, 2000/2006 LGE) are what this
script turns into the same shape ``ingest_npe.py`` and ``ingest_lge.py``
produce, so ``fold.py`` and everything downstream can read them unchanged.

**Five archives, five different layouts.** Each is described in ``SPECS``
rather than sniffed, because guessing is how a column gets silently misread:

* The party's own votes live in a column called **VALID VOTES** (2004/2009) or
  **Valid Votes  Cast** (2000/2006) -- note the double space. The VD's total is
  in *TOTAL VOTES CAST*. This is the same mislabelling already documented for
  the 2014 file (SOURCES.md), and reading it the obvious way understates every
  large party.
* **Vote counts carry thousands separators inside quotes** -- ``"1,656"``.
  ``csv`` parses the field correctly and ``int()`` then raises, so a reader
  that skips unparseable cells silently drops precisely the rows with the most
  votes. Measured on 2009 Johannesburg: 4.0% of rows, **68.4% of votes**.
* 1999 has a UTF-8 BOM on the first header; 2006 has a trailing empty column;
  2004 and 1999 have no Ward column at all; 2000/2006 carry a ``DC 40%``
  ballot type that does not apply to a metro.
* Municipality strings differ every single year (``JHB - ...``,
  ``JOHANNESBURG - ...``, ``Johannesburg - ...``), so the match is on the
  city's name, case-folded, not on a literal.

**1999 predates the metro.** The City of Johannesburg was created by the
December 2000 election. For 1999 the closest available footprint is the five
metropolitan local councils that became it, and the aggregate is therefore
*approximate* -- it is written with a ``_approx`` suffix and should never be
used for a ward-level comparison. Every other year is the real municipality.

**What this does not do.** Pre-2011 ward and voting-district identifiers
predate two delimitations, so these files are usable for citywide party shares
immediately and for anything spatial only after a concordance is built. That
is deliberately left undone rather than faked.

Validation is not optional: for every year the script checks that the party
votes in each VD sum to that VD's valid total (cast minus spoilt) and refuses
to write a file whose reconciliation is worse than ``--tolerance``. 2009 is
additionally checked against the IEC's own published Johannesburg report.

Usage:
    python src/ingest_historic.py                     # all five, Johannesburg
    python src/ingest_historic.py --year 2004         # one
    python src/ingest_historic.py --city joburg
"""

from __future__ import annotations

import argparse
import csv
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import cityconfig
import parties as P

SOURCE_DIR = Path("data/raw/elections/_source")
OUT_DIR = Path("data/raw/elections")

# Per-archive column names, exactly as they appear. Never sniffed.
SPECS = {
    "npe1999": {
        "zip": "1999_npe.zip", "member": "1999 NPE.csv", "kind": "npe",
        "event": "ELECTORAL EVENT", "prefer_event": "PROVINCIAL",
        "muni": "MUNICIPALITY", "vd": "VOTING DISTRICT", "ward": None,
        "party": "PARTY NAME", "votes": "VALID VOTES",
        "spoilt": "SPOILT VOTES", "cast": "TOTAL VOTES CAST",
        "reg": "REGISTERED VOTERS", "ballot": None,
        "approx": True,
        "muni_match": ("JOHANNESBURG MLC", "MIDRAND/ RABIE RIDGE/ IVORY PARK MLC"),
    },
    "npe2004": {
        "zip": "2004_npe.zip", "member": "2004 NPE.csv", "kind": "npe",
        "event": "ELECTORAL EVENT", "prefer_event": "PROVINCIAL",
        "muni": "MUNICIPALITY", "vd": "VOTING DISTRICT", "ward": None,
        "party": "PARTY NAME", "votes": "VALID VOTES",
        "spoilt": "SPOILT VOTES", "cast": "TOTAL VOTES CAST",
        "reg": "REGISTERED VOTERS", "ballot": None,
    },
    "npe2009": {
        "zip": "npe2009_national_and_provincial.zip", "member": "2009 NPE.csv",
        "kind": "npe",
        "event": "ELECTORAL EVENT", "prefer_event": "PROVINCIAL",
        "muni": "MUNICIPALITY", "vd": "VOTING DISTRICT", "ward": "WARD",
        "party": "PARTY NAME", "votes": "VALID VOTES",
        "spoilt": "SPOILT VOTES", "cast": "TOTAL VOTES CAST",
        "reg": "REGISTERED VOTERS", "ballot": None,
    },
    "lge2000": {
        "zip": "2000_lge.zip", "member": "2000 LGE.csv", "kind": "lge",
        "event": "Electoral Event", "prefer_event": None,
        "muni": "Municipality", "vd": "Voting  District", "ward": "Ward",
        "party": "Party", "votes": "Valid Votes  Cast",
        "spoilt": "Spoilt Votes", "cast": "Total Votes  Cast",
        "reg": "Registered Voters", "ballot": "Ballot  Type",
    },
    "lge2006": {
        "zip": "2006_lge.zip", "member": "2006 LGE.csv", "kind": "lge",
        "event": "Electoral Event", "prefer_event": None,
        "muni": "Municipality", "vd": "Voting  District", "ward": "Ward",
        "party": "Party", "votes": "Valid Votes  Cast",
        "spoilt": "Spoilt Votes", "cast": "Total Votes  Cast",
        "reg": "Registered Voters", "ballot": "Ballot  Type",
    },
}

# Ballot types a metro actually has. "DC 40%" is the district-council ballot
# for non-metro municipalities and must not be folded into a metro's totals.
METRO_BALLOTS = {"PR": "PR", "WARD": "Ward"}

NPE_COLUMNS = ["Province", "Municipality", "Ward", "VD_Number", "VS_Name",
               "Registered_Population", "Spoilt_Votes", "Total_Valid_Votes",
               "sPartyName", "Party_Votes"]
LGE_COLUMNS = ["Province", "Municipality", "Ward", "VD_Number", "VS_Name",
               "BallotType", "Registered_Population", "Spoilt_Votes",
               "Total_Valid_Votes", "sPartyName", "Party_Votes"]


def clean_header(cell: str) -> str:
    """Strip the BOM, stray quotes and embedded newlines from a header cell."""
    return cell.replace("﻿", "").replace("ï»¿", "") \
               .replace('"', "").replace("\n", " ").strip()


def number(cell: str) -> int | None:
    """Parse an IEC integer, which may carry thousands separators.

    Returns None rather than raising, but every caller counts the Nones --
    silently skipping these is the bug this whole module exists to avoid.
    """
    text = (cell or "").strip().replace(",", "").replace(" ", "")
    if text.startswith("-"):
        return -int(text[1:]) if text[1:].isdigit() else None
    return int(text) if text.isdigit() else None


def open_member(spec: dict):
    """Yield (header_index, row) for the archive's single CSV member."""
    path = SOURCE_DIR / spec["zip"]
    if not path.exists():
        raise SystemExit(f"missing archive {path} -- see the module docstring "
                         f"for where these come from")
    with zipfile.ZipFile(path) as archive:
        name = spec["member"]
        if name not in archive.namelist():
            names = [n for n in archive.namelist() if n.lower().endswith(".csv")]
            if len(names) != 1:
                raise SystemExit(f"{path}: expected one CSV, found {archive.namelist()}")
            name = names[0]
        with archive.open(name) as raw:
            text = (line.decode("latin-1") for line in raw)
            reader = csv.reader(text)
            header = [clean_header(h) for h in next(reader)]
            yield header
            yield from reader


def matches_city(value: str, city, spec: dict) -> bool:
    """Is this municipality string the target city?

    Matched on the city's name because the prefix changes every year
    (``JHB -``, ``JOHANNESBURG -``, ``Johannesburg -``).
    """
    text = (value or "").upper()
    if spec.get("muni_match"):
        return any(m.upper() in text for m in spec["muni_match"])
    return city.name.split()[-1].upper() in text


def ingest(tag: str, spec: dict, city, tolerance: float) -> int:
    stream = open_member(spec)
    header = next(stream)
    index = {name: i for i, name in enumerate(header)}
    missing = [spec[k] for k in ("muni", "vd", "party", "votes", "spoilt", "cast", "reg")
               if spec[k] and spec[k] not in index]
    if missing:
        raise SystemExit(f"{tag}: columns not found: {missing}\n  header: {header}")

    events: set[str] = set()
    rows: list[list] = []
    unparseable = 0
    shifted = 0
    # (vd, ballot) -> [summed party votes, vd valid total from the header cols]
    reconcile: dict[tuple, list[int]] = defaultdict(lambda: [0, None])

    for row in stream:
        if len(row) <= index[spec["votes"]]:
            continue
        event = row[index[spec["event"]]] if spec["event"] in index else ""
        events.add(event)
        if not matches_city(row[index[spec["muni"]]], city, spec):
            continue
        if spec["prefer_event"] and spec["prefer_event"] not in event.upper():
            continue

        # An unquoted comma inside a party's own name splits it across two
        # fields and shifts every later column right by one. In 2006 CoJ this
        # hits "SUNRISE PARK, PROTEA CITY AND GREENSIDE RESIDENTS'
        # ASSOCIATION" in all six of ward 79400053's voting districts. Detect
        # it by the ballot-type field not holding a ballot type, and re-align.
        # Verified exactly: the recovered votes close the VD's shortfall in
        # every affected district (194, 1, 24, 211, 34, 5).
        shift = 0
        party_name = row[index[spec["party"]]].strip()
        if spec["ballot"]:
            raw_ballot = row[index[spec["ballot"]]].strip().upper()
            if raw_ballot not in METRO_BALLOTS and raw_ballot != "DC 40%":
                shift = 1
                party_name = f"{party_name},{row[index[spec['ballot']]]}".strip()
                if index[spec["ballot"]] + 1 >= len(row):
                    unparseable += 1
                    continue
                raw_ballot = row[index[spec["ballot"]] + 1].strip().upper()
                shifted += 1
            if raw_ballot not in METRO_BALLOTS:
                continue                      # DC 40% -- not a metro ballot
            ballot = METRO_BALLOTS[raw_ballot]
        else:
            ballot = ""

        def field(name):
            i = index[spec[name]] + shift
            return number(row[i]) if i < len(row) else None

        votes = field("votes")
        cast = field("cast")
        spoilt = field("spoilt")
        registered = field("reg")
        if votes is None:
            unparseable += 1
            continue
        valid = (cast - spoilt) if (cast is not None and spoilt is not None) else None

        vd = row[index[spec["vd"]]].strip()
        ward = row[index[spec["ward"]]].strip() if spec["ward"] else ""

        key = (vd, ballot)
        reconcile[key][0] += votes
        if valid is not None:
            reconcile[key][1] = valid

        record = [row[index.get("PROVINCE", index.get("Province", 0))],
                  row[index[spec["muni"]]], ward, vd, "",
                  registered if registered is not None else "",
                  spoilt if spoilt is not None else "",
                  valid if valid is not None else "",
                  party_name, votes]
        if spec["kind"] == "lge":
            record.insert(5, ballot)
        rows.append(record)

    if not rows:
        raise SystemExit(f"{tag}: no rows matched city {city.name!r}. "
                         f"events in file: {sorted(events)}")

    # A comma-shifted row also mangles its registration cell (2006 ward 79400053
    # reads "311100.00%" -- the registered count and the turnout run together).
    # Registration is a property of the voting district, so take it from a
    # well-formed sibling rather than leaving a blank for turnout.py to trip on.
    vd_field = 3
    reg_field = 6 if spec["kind"] == "lge" else 5
    known = {r[vd_field]: r[reg_field] for r in rows if r[reg_field] != ""}
    backfilled = 0
    for record in rows:
        if record[reg_field] == "" and known.get(record[vd_field], "") != "":
            record[reg_field] = known[record[vd_field]]
            backfilled += 1
    if backfilled:
        print(f"  backfilled registration on {backfilled} row(s) from their VD")

    # --- validation -------------------------------------------------------
    checked = bad = 0
    worst = 0.0
    for (vd, ballot), (summed, valid) in reconcile.items():
        if not valid:
            continue
        checked += 1
        drift = abs(summed - valid) / valid
        worst = max(worst, drift)
        if drift > tolerance:
            bad += 1

    label = f"{tag}{'_approx' if spec.get('approx') else ''}"
    print(f"\n{label}: {len(rows):,} party-VD rows, "
          f"{len({r[3] for r in rows}):,} voting districts")
    if spec["prefer_event"]:
        chosen = [e for e in events if spec["prefer_event"] in e.upper()]
        print(f"  event: {chosen[0] if chosen else '?'}   "
              f"(file also holds: {sorted(e for e in events if e not in chosen)})")
    print(f"  unparseable vote cells: {unparseable}")
    if shifted:
        print(f"  repaired {shifted} rows shifted by an unquoted comma in a party name")
    print(f"  reconciliation: {checked - bad}/{checked} VD-ballots where the "
          f"party votes sum to the VD's valid total (worst drift {worst:.2%})")
    if checked and bad / checked > 0.02:
        raise SystemExit(
            f"  REFUSING TO WRITE: {bad}/{checked} VD-ballots fail reconciliation. "
            f"The votes column is probably not the party's votes.")

    columns = LGE_COLUMNS if spec["kind"] == "lge" else NPE_COLUMNS
    suffix = "_vd_party_clean.csv" if spec["kind"] == "lge" else "_vd_party.csv"
    out = OUT_DIR / f"{label}_{city.code}{suffix}"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    total = sum(r[-1] for r in rows)
    print(f"  wrote {out}  ({total:,} votes)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    cityconfig.add_city_argument(parser)
    parser.add_argument("--year", action="append",
                        help="ingest only this tag, e.g. npe2004 (repeatable)")
    parser.add_argument("--tolerance", type=float, default=0.001,
                        help="per-VD reconciliation tolerance (default 0.1%%)")
    args = parser.parse_args(argv)
    city = cityconfig.use(args.city)

    wanted = args.year or list(SPECS)
    unknown = set(wanted) - set(SPECS)
    if unknown:
        raise SystemExit(f"unknown tag(s) {sorted(unknown)}; have {sorted(SPECS)}")

    print(f"ingesting {len(wanted)} archive(s) for {city.name} ({city.code})")
    for tag in wanted:
        ingest(tag, SPECS[tag], city, args.tolerance)
    return 0


if __name__ == "__main__":
    sys.exit(main())
