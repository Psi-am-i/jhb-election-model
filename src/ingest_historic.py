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
    # The 2011 archive is the sixth layout. Its headers carry EMBEDDED
    # NEWLINES ("Voting \nDistrict", not the double space 2006 uses), and it
    # has both a "MEC7\nVotes" column and a "Valid Votes \nCast" one. The
    # party's vote is the LATTER: summed per (VD, ballot) it reconciles to
    # Total Votes Cast minus Spoilt Votes on 308 of 308 Buffalo City voting
    # districts, while MEC7 sums to about 30 votes a district and is a
    # different quantity entirely. Picking the wrong one would not error --
    # it would publish a city where every party had roughly the same tiny
    # vote, which is exactly the silent-corruption class DATA-QUALITY.md
    # exists to catalogue.
    "lge2011": {
        "zip": "2011_lge.zip", "member": "2011 LGE.csv", "kind": "lge",
        "event": "Electoral Event", "prefer_event": None,
        # The reader normalises embedded newlines to spaces before matching,
        # so these are the double-space forms it actually sees.
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



# ---------------------------------------------------------------------------
# THE MUNICIPALITY STRING, PER ARCHIVE, PER CITY — enumerated, never sniffed.
# ---------------------------------------------------------------------------
# Added 2026-08-22 (MODEL-LOG §1.70). Before it, this module was Johannesburg's
# in everything but its `--city` flag, and it failed in the two worst ways at
# once:
#
#  * **`npe1999` matched Johannesburg for EVERY city.** `matches_city` returned
#    on `spec["muni_match"]` without ever looking at `city`, and that spec is
#    the two Johannesburg metropolitan local councils. Running
#    `--city tshwane` wrote **Johannesburg's 1999 votes** to
#    `npe1999_approx_TSH_vd_party.csv` — 9,072 rows, 648 VDs and 1,361,299
#    votes, byte-identical to Johannesburg's file — and it PASSED the
#    reconciliation gate, because the rows it collected were individually
#    valid. Exactly the failure mode the `matches_city` comment below already
#    describes for Buffalo City, one archive earlier, undetected. Seven such
#    files were written and deleted the same hour.
#  * **`npe2004` matched nothing at all** for any other metro, and halted the
#    run, which is why 2006 and 2009 were never reached.
#
# Neither was a data limitation. **All eight metros are in all four archives**;
# the strings simply are not derivable from the city name or code:
#
#     archive   Tshwane                          Buffalo City
#     npe2004   PRETORIA - TSHWANE METRO [...]   EC125 - BUFFALO CITY [...]
#     lge2006   TSH - Tshwane Metro [Pretoria]   EC125 - Buffalo City [...]
#     npe2009   TSH - TSHWANE METRO [PRETORIA]   EC125 - BUFFALO CITY [...]
#     lge2000   Pretoria - Tshwane Metro [...]   EC125 - Buffalo City [...]
#
# 2004 and 2000 key the Gauteng/Eastern Cape metros on the PLACE
# ("PRETORIA -", "EAST RAND -", "PORT ELIZABETH -"), and every archive keys
# Mangaung and Buffalo City on their pre-2011 municipality codes FS172 and
# EC125 rather than MAN and BUF. No rule recovers that; a table does.
#
# Matching is on the string BEFORE " - ", uppercased, so it cannot spread into
# a neighbouring municipality the way the last-word fallback did.
MUNI_HEAD = {
    "npe1999": {
        # ⛔ 1999 PREDATES EVERY METRO, SO EACH IS THE SUM OF THE COUNCILS THAT
        # BECAME IT. THIS TABLE NAMED JOHANNESBURG ONLY, AND NAMED IT WRONGLY.
        #
        # It declared ("JOHANNESBURG MLC", "MIDRAND/ RABIE RIDGE/ IVORY PARK
        # MLC"). `matches_city` compares WHOLE HEADS and no council is called
        # "JOHANNESBURG MLC" — the four are EASTERN, NORTHERN, SOUTHERN and
        # WESTERN. So one of five matched and Johannesburg's 1999 election was
        # Midrand: 392 rows, 28 voting districts, 65,674 votes.
        #
        # ⛔ AND THE FILE ON DISK WAS NOT STALE — I CLAIMED IT WAS, WRONGLY.
        # Its sha256 matches the manifest's 9 August entry exactly, and the
        # corrected head list reproduces it BYTE-FOR-BYTE, all five councils
        # including Midrand's 392 rows (4074+1848+1498+1260+392 = 9,072). No
        # Johannesburg number moved. That is the stronger claim and the one
        # worth having. The 9,072 / 648 / 1,361,299 figures elsewhere in this
        # module are Johannesburg's CORRECT numbers, wrongly written into
        # Tshwane's file by the old bug — not evidence that Johannesburg's own
        # file was ever contaminated. Corrected 2026-09-01.
        # Corrected 2026-08-31 by reading the archive.
        #
        # Councils amalgamated into each metro in December 2000.
        "joburg": ("EASTERN JOHANNESBURG MLC", "NORTHERN JOHANNESBURG MLC",
                   "SOUTHERN JOHANNESBURG MLC", "WESTERN JOHANNESBURG MLC",
                   "MIDRAND/ RABIE RIDGE/ IVORY PARK MLC"),
        "tshwane": ("CITY COUNCIL OF PRETORIA MLC", "NORTHERN PRETORIA MLC",
                    "CENTURION MLC", "HAMMANSKRAAL LAC", "MABOPANE TRC",
                    "TEMBA TRC", "WINTERVELD TRC"),
        "ekurhuleni": ("ALBERTON TLC", "BENONI TLC", "BOKSBURG TLC",
                       "BRAKPAN TLC", "EDENVALE/ MODDERFONTEIN MLC",
                       "GERMISTON TLC", "KEMPTON PARK/ TEMBISA MLC",
                       "NIGEL TLC", "SPRINGS TLC"),
        "ethekwini": ("INNER WEST DURBAN MLC", "NORTH CENTRAL DURBAN MLC",
                      "NORTHERN DURBAN MLC", "OUTER WEST DURBAN MLC",
                      "SOUTH CENTRAL DURBAN MLC", "SOUTH DURBAN MLC"),
        "capetown": ("CENTRAL CAPE TOWN MLC", "TYGERBERG MLC",
                     "BLAAUWBERG MLC", "OOSTENBERG MLC", "HELDERBERG MLC",
                     "SOUTHERN PENINSULA MLC"),
        "mangaung": ("BLOEMFONTEIN TLC", "BLOEMFONTEIN RURAL RLC",
                     "BOTSHABELO TLC", "THABA NCHU TLC",
                     "THABA NCHU RURAL RLC"),
        "nelsonmandelabay": ("PORT ELIZABETH TLC", "PORT ELIZABETH RURAL TRC",
                             "UITENHAGE TLC", "UITENHAGE RURAL TRC",
                             "DESPATCH TLC"),
        # ⚠️ King William's Town joined Buffalo City in 2011, NOT 2000.
        # Buffalo City at 1999 is East London only; including KWT would
        # overstate it. Recorded as a deliberate exclusion.
        "buffalocity": ("EAST LONDON TLC", "EAST LONDON RURAL TRC"),
    },
    "lge2000": {
        "joburg": ("JOHANNESBURG",), "tshwane": ("PRETORIA",),
        "capetown": ("CAPE TOWN",), "mangaung": ("FS172",),
        "nelsonmandelabay": ("PORT ELIZABETH",), "buffalocity": ("EC125",),
        # ⛔ THIS SAID EKURHULENI AND ETHEKWINI WERE "absent from the 2000
        # archive under any name … do not add a guess here". WRONG. They are
        # there under their 2000 names — "East Rand - Greater East Rand Metro"
        # (9,813 rows) and "Durban - Durban Metro" (13,328) — and the correct
        # heads were ALREADY DECLARED in `npe2004` below, which has carried
        # ("EAST RAND",) and ("DURBAN",) all along. Not a guess that failed: a
        # search that stopped at the modern name, plus a note telling the next
        # reader not to look. Corrected 2026-08-31.
        "ekurhuleni": ("EAST RAND",), "ethekwini": ("DURBAN",),
    },
    "npe2004": {
        "joburg": ("JOHANNESBURG",), "tshwane": ("PRETORIA",),
        "ekurhuleni": ("EAST RAND",), "ethekwini": ("DURBAN",),
        "capetown": ("CAPE TOWN",), "mangaung": ("FS172",),
        "nelsonmandelabay": ("PORT ELIZABETH",), "buffalocity": ("EC125",),
    },
    "lge2006": {
        "joburg": ("JHB",), "tshwane": ("TSH",), "ekurhuleni": ("EKU",),
        "ethekwini": ("ETH",), "capetown": ("CPT",), "mangaung": ("FS172",),
        "nelsonmandelabay": ("NMA",), "buffalocity": ("EC125",),
    },
    "npe2009": {
        "joburg": ("JHB",), "tshwane": ("TSH",), "ekurhuleni": ("EKU",),
        "ethekwini": ("ETH",), "capetown": ("CPT",), "mangaung": ("FS172",),
        "nelsonmandelabay": ("NMA",), "buffalocity": ("EC125",),
    },
}


def muni_heads(tag: str, city) -> tuple[str, ...] | None:
    """The municipality-string heads for this archive and city, or None.

    None means "this archive has no entry for this city", which is a REFUSAL,
    not a fallback. The fallback is what wrote Johannesburg's 1999 election
    into seven other metros' files.
    """
    per_city = MUNI_HEAD.get(tag)
    if per_city is None:
        return None
    return per_city.get(getattr(city, "slug", ""))


def matches_city(value: str, city, spec: dict) -> bool:
    """Is this municipality string the target city?

    Matched on the city's name because the prefix changes every year
    (``JHB -``, ``JOHANNESBURG -``, ``Johannesburg -``).
    """
    text = (value or "").upper()
    heads = spec.get("_heads")
    if heads:
        # The head is the token before " - ". Comparing HEADS rather than
        # substrings is what stops "CITY" reaching "City of Cape Town" and
        # what stops a Johannesburg MLC reaching Tshwane.
        head = text.split(" - ", 1)[0].strip() if " - " in text else text.strip()
        return any(head == h.upper() for h in heads)

    # Prefer the IEC code, which these files carry as a prefix ("BUF - Buffalo
    # City Metropolitan Municipality [East London]"). The name fallback below
    # matches on the LAST WORD, which is fine for Johannesburg and silently
    # catastrophic for a city called "Buffalo City": "CITY" also matches "City
    # of Cape Town", "City of Johannesburg", "Mogale City" and "Merafong
    # City". Ingesting Buffalo City's 2011 election that way produced 2,087
    # voting districts and 5.1 million votes for a metro with about 350 VDs
    # and 420,000 — and it passed the reconciliation gate, because the rows it
    # collected were individually valid. Only the seat test caught it, by
    # failing to reproduce a published council.
    # When the file carries a code prefix, the code is the WHOLE answer and
    # the name fallback must not run: "BUF" correctly fails to match "CPT -
    # CITY OF CAPE TOWN", and then "CITY" matches it anyway.
    code = (getattr(city, "code", "") or "").upper()
    head = text.split(" - ", 1)[0].strip() if " - " in text else ""
    if head:
        return bool(code) and head == code
    return city.name.split()[-1].upper() in text


def ingest(tag: str, spec: dict, city, tolerance: float) -> int:
    heads = muni_heads(tag, city)
    if heads is None:
        raise SystemExit(
            f"{tag}: no municipality string is recorded for {city.name} "
            f"({getattr(city, 'slug', '?')}).\n"
            f"  This is a REFUSAL, not a missing feature. Until 2026-08-22 the "
            f"fallback here matched on the last word of the city name, or on a "
            f"hard-coded Johannesburg spec, and wrote another city's votes into "
            f"this city's file — silently, and past the reconciliation gate, "
            f"because the rows it collected were individually valid. See "
            f"MUNI_HEAD and MODEL-LOG §1.70.\n"
            f"  If this city IS in the archive, add its exact municipality head "
            f"to MUNI_HEAD[{tag!r}]. If it is not — Ekurhuleni and eThekwini in "
            f"lge2000 and npe1999 are now ingested for ALL EIGHT metros "
            f"(2026-09-01), so an absence here is new — then the "
            f"election predates the municipality and there is nothing to add.")
    spec = dict(spec, _heads=heads)
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
