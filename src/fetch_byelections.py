"""Download every municipal by-election result since the 2021 LGE, at VD level.

The IEC's downloads page serves by-election reports only through per-session
``ReportViewer?_f=<token>`` links, which cannot be fetched outside the browser
that generated them. The by-election *dashboard* is far friendlier: it is a
static site backed by plain JSON files needing no session at all.

Three endpoints, used in this order:

    MapsJason/{year}/ByElections.js
        every by-election date under a parent election, with its ElectoralEventID

    MapsJason/{eeid}/EEID{eeid}BigMapsNational.js
        that date's national summary -- used only to discover which provinces
        and municipalities actually held a contest, since it carries the leading
        party alone

    MapsJason/{eeid}/EEID{eeid}Munic{municipalityID}.js
        the real payload: voting-district level results for that municipality,
        every party, with candidate names and the ward's historical comparators

Party names arrive as numeric ids resolved through ``MapsJason/{year}/PartyList.js``.

Plan §3.6 wants CoJ contests for the by-election deltas and Gauteng-wide ones for
the swing estimator, so the whole province is kept by default.

Usage:
    python src/fetch_byelections.py [--province Gauteng] [--year 2021]
"""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

DASH = "https://results.elections.org.za/dashboards/byelection/MapsJason"
USER_AGENT = "Mozilla/5.0 (jhb-election-model; by-election fetch)"

COLUMNS = [
    "EEID",
    "ByElectionDate",
    "Province",
    "Municipality",
    "MunicipalityID",
    "WardID",
    "VD_Number",
    "PartyID",
    "PartyName",
    "PartyFullName",
    "CandidateName",
    "Party_Votes",
    "PercOfVotes",
    "IsLeadingParty",
]


def _get_json(url: str, timeout: int = 60):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
    if not body.strip():
        return None
    return json.loads(body.decode("utf-8-sig"))


def party_lookup(year: str) -> dict[int, tuple[str, str]]:
    """Map party id -> (short name, full name)."""
    return {
        entry["ID"]: (entry.get("Name", ""), entry.get("PartyFullName", ""))
        for entry in _get_json(f"{DASH}/{year}/PartyList.js") or []
    }


def contested_municipalities(eeid: int, province: str) -> list[tuple[int, str, str]]:
    """Return (municipality id, municipality name, province) contested at this event."""
    payload = _get_json(f"{DASH}/{eeid}/EEID{eeid}BigMapsNational.js")
    if not payload:
        return []
    found = []
    for prov in payload.get("ProvinceResults", []):
        if province and prov.get("Province") != province:
            continue
        for muni in prov.get("MunicipalityResults", []):
            found.append(
                (muni["MunicipalityID"], muni.get("Municipality", ""), prov.get("Province", ""))
            )
    return found


def municipality_rows(
    eeid: int,
    event: dict,
    muni_id: int,
    muni_name: str,
    province: str,
    parties: dict[int, tuple[str, str]],
) -> list[dict[str, str]]:
    """Flatten one municipality's VD-level results to one row per VD x party."""
    payload = _get_json(f"{DASH}/{eeid}/EEID{eeid}Munic{muni_id}.js")
    if not payload:
        return []

    rows: list[dict[str, str]] = []
    for ward in payload.get("WardResults", []):
        for district in ward.get("VotingDistrictResults", []):
            for result in district.get("PartyBallotResults", []):
                short, full = parties.get(result["ID"], ("", ""))
                rows.append(
                    {
                        "EEID": str(eeid),
                        "ByElectionDate": event.get("dtStartDate", "")[:10],
                        "Province": province,
                        "Municipality": muni_name,
                        "MunicipalityID": str(muni_id),
                        "WardID": str(ward.get("WardID", "")),
                        "VD_Number": str(district.get("VotingDistrictID", "")),
                        "PartyID": str(result["ID"]),
                        "PartyName": short,
                        "PartyFullName": full,
                        "CandidateName": result.get("CandidateName", ""),
                        "Party_Votes": str(result.get("TotalValidVotes", "")),
                        "PercOfVotes": str(result.get("PercOfVotes", "")),
                        "IsLeadingParty": "Y" if result.get("IsLeadingPartyVotes") else "",
                    }
                )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", default="2021", help="parent election year")
    parser.add_argument("--province", default="Gauteng", help="'' keeps every province")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/byelections"))
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    parties = party_lookup(args.year)
    events = sorted(_get_json(f"{DASH}/{args.year}/ByElections.js"), key=lambda e: e["dtStartDate"])
    print(f"{len(events)} by-election dates under the {args.year} LGE; {len(parties)} parties known\n")

    rows: list[dict[str, str]] = []
    skipped: list[str] = []
    for index, event in enumerate(events, 1):
        eeid, date = event["EEID"], event["dtStartDate"][:10]
        try:
            munis = contested_municipalities(eeid, args.province)
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as error:
            skipped.append(f"{date} (EEID {eeid}): {error}")
            continue

        for muni_id, muni_name, province in munis:
            try:
                found = municipality_rows(eeid, event, muni_id, muni_name, province, parties)
            except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as error:
                skipped.append(f"{date} {muni_name}: {error}")
                continue
            rows.extend(found)
            wards = len({r["WardID"] for r in found})
            print(f"  [{index:>3d}/{len(events)}] {date}  {muni_name:<34s} {wards} ward(s), {len(found):>3d} rows")
            time.sleep(0.2)
        time.sleep(0.15)

    destination = args.out_dir / f"byelections_{args.province or 'SA'}_vd_party.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    contests = {(r["EEID"], r["WardID"]) for r in rows}
    jhb = {(r["EEID"], r["WardID"]) for r in rows if r["Municipality"].startswith("JHB")}
    print(
        f"\n{len(rows):,} rows -> {destination}"
        f"\n  {len(contests):,} ward contests, {len(jhb):,} of them in City of Johannesburg"
        f"\n  {len({r['VD_Number'] for r in rows}):,} distinct voting districts"
    )
    if skipped:
        print(f"\n  {len(skipped)} event(s)/municipality skipped (no result file published):")
        for note in skipped[:8]:
            print(f"    - {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
