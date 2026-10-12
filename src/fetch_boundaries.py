"""Download CoJ ward and voting-district boundaries from the MDB Spatial Knowledge Hub.

The MDB publishes its boundaries through an ArcGIS Hub site
(``spatialhub-mdb-sa.opendata.arcgis.com``). The catalogue's DCAT feed only
advertises download endpoints for some layers, but every layer sits behind a
plain ArcGIS FeatureServer that can be queried directly -- which is better
anyway, since we can filter to Johannesburg server-side instead of pulling the
whole country.

The layer URLs below were resolved from the "Wards2026" web map
(item 6d7488a7f83645218e547d403871e1e0), which is what the MDB's own ward
delimitation viewer draws.

Delimitation-to-election mapping, which is the thing that is easy to get wrong:

    2020 delimitation -> 2021 LGE
    2026 delimitation -> 2026 LGE
    2016 delimitation -> 2016 LGE   (File Geodatabase only, see MISSING below)

Usage:
    python src/fetch_boundaries.py [--muni JHB] [--out-dir data/raw/geo]
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://services7.arcgis.com/oeoyTUJC8HEeYsRB/arcgis/rest/services"

# name -> (service, where-clause template, description). The boundary layers key
# municipality on the CAT_B code; the voting-station layer has no CAT_B column
# and spells the municipality out in full instead.
LAYERS = {
    "wards2026": (
        "MDBWards2026",
        "CAT_B='{muni}'",
        "2026 ward boundaries (for the 4 Nov 2026 election)",
    ),
    "vds2026": (
        "VotingDistricts2026_Final",
        "CAT_B='{muni}'",
        "2026 voting districts, with ward link",
    ),
    "wards2020": (
        "SA_Wards2020",
        "CAT_B='{muni}'",
        "2020 delimitation = the 2021 LGE ward boundaries",
    ),
    "votingstations2026": (
        "VotingStations_March2026",
        "MUNICIPALI LIKE '{muni} - %'",
        "2026 voting stations (points)",
    ),
}

# The 2016 and 2011 ward layers are published only as File Geodatabase item
# downloads, not as feature services, so they are fetched separately.
FGDB_ITEMS = {
    "wards2016": ("cfddb54aab5f4d62b2144d80d49b3fdb", "2016 delimitation = 2016 LGE wards"),
    "wards2011": ("12d2deb98816451ab7c4dc09cdfeee6b", "2011 delimitation = 2011/2014 wards"),
}

USER_AGENT = "Mozilla/5.0 (jhb-election-model; boundary fetch)"
PAGE_SIZE = 1000


def _get(url: str, params: dict[str, str], timeout: int = 90) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def feature_count(service: str, where: str) -> int:
    return _get(
        f"{BASE}/{service}/FeatureServer/0/query",
        {"where": where, "returnCountOnly": "true", "f": "json"},
    )["count"]


def fetch_geojson(service: str, where: str) -> dict:
    """Page through a FeatureServer layer and return one GeoJSON FeatureCollection.

    Layers cap a single response at 2,000 records, so results are paged. WGS84 is
    requested explicitly rather than trusting the layer's stored projection.
    """
    features: list[dict] = []
    offset = 0
    while True:
        page = _get(
            f"{BASE}/{service}/FeatureServer/0/query",
            {
                "where": where,
                "outFields": "*",
                "outSR": "4326",
                "f": "geojson",
                "resultOffset": str(offset),
                "resultRecordCount": str(PAGE_SIZE),
            },
        )
        batch = page.get("features", [])
        features.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(0.3)  # be polite to a free public service

    return {"type": "FeatureCollection", "features": features}


def fetch_fgdb(item_id: str, destination: Path) -> int:
    """Download an ArcGIS item's File Geodatabase payload. Returns bytes written."""
    url = f"https://www.arcgis.com/sharing/rest/content/items/{item_id}/data"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        payload = response.read()
    destination.write_bytes(payload)
    return len(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--muni", default="JHB", help="CAT_B municipality code")
    parser.add_argument("--out-dir", type=Path, default=Path("data/raw/geo"))
    args = parser.parse_args(argv)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    for name, (service, clause, description) in LAYERS.items():
        where = clause.format(muni=args.muni)
        count = feature_count(service, where)
        collection = fetch_geojson(service, where)
        got = len(collection["features"])
        destination = args.out_dir / f"{name}_{args.muni}.geojson"
        destination.write_text(json.dumps(collection), encoding="utf-8")
        flag = "" if got == count else f"  ** expected {count} **"
        print(f"{name:<20s} {got:>5,} features -> {destination.name}{flag}")
        print(f"{'':<20s} {description}")

    # These two are whole-country geodatabase downloads; filtering happens later.
    for name, (item_id, description) in FGDB_ITEMS.items():
        destination = args.out_dir / f"{name}_SA.gdb.zip"
        size = fetch_fgdb(item_id, destination)
        print(f"{name:<20s} {size / 1e6:>5.1f} MB -> {destination.name}  (whole SA)")
        print(f"{'':<20s} {description}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
