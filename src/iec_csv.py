"""Shared helpers for reading IEC result CSVs.

The IEC's published files are inconsistent between elections in encoding,
header punctuation and quoting, so the reading code is kept here and the
per-election-type modules (:mod:`ingest_npe`, :mod:`ingest_lge`) only deal with
their own layout.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

# Tried in order; the first that decodes the whole file wins. CP850 never fails,
# so it must come last.
ENCODINGS = ("utf-8-sig", "cp850")

# Municipalities are written "JHB - City of Johannesburg" in some files and
# "JHB - CITY OF JOHANNESBURG [JOHANNESBURG]" in others, so match on the code.
MUNI_CODE = "JHB"


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


def normalise_header(name: str) -> str:
    """Fold a raw header cell to an upper-snake-case key.

    Strips the BOM and whitespace, and replaces the volatile
    ``Generated Datetime: <timestamp>`` / ``DateGenerated`` headers with stable
    names so a file's header is comparable between elections.
    """
    name = name.lstrip("﻿").strip().upper()
    if name.startswith("GENERATED DATETIME"):
        return "GENERATED_DATETIME"
    return name.replace(" ", "_")


def is_int(cell: str) -> bool:
    return cell.strip().lstrip("-").isdigit()


def muni_code(municipality: str) -> str:
    return municipality.split("-")[0].strip().upper()


def ward_number(ward: str) -> str:
    """Reduce ``Ward 79800001`` to ``79800001``; pass anything else through."""
    ward = ward.strip()
    return ward.split()[-1] if ward.lower().startswith("ward ") else ward


def write_csv(destination: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def summarise(rows: list[dict[str, str]], top: int = 10) -> str:
    """Format a turnout and party-share summary, for eyeballing against plan §8.

    Assumes one row per VD x party, with the registration and spoilt-vote
    columns repeated on every row of a VD.
    """
    per_vd = {row["VD_Number"]: row for row in rows}
    registered = sum(int(r["Registered_Population"]) for r in per_vd.values())
    valid = sum(int(r["Total_Valid_Votes"]) for r in per_vd.values())
    spoilt = sum(int(r["Spoilt_Votes"]) for r in per_vd.values())

    votes: Counter[str] = Counter()
    for row in rows:
        votes[row["sPartyName"]] += int(row["Party_Votes"])

    wards = {row["Ward"] for row in rows if row.get("Ward")}
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
