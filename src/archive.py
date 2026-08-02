"""Inventory every raw input with a checksum and its provenance.

The sources this model depends on are not durable. The MDB has already retired
the per-municipality shapefile downloads its old site served, the IEC's
by-election reports are reachable only through session-bound tokens, and Stats SA
withdraws and reissues products. If a file we relied on disappears upstream, we
need to know exactly what we had, where it came from, and whether the copy on
disk is still the copy we validated against.

``data/`` is gitignored, so the manifest is the tracked record: it goes in git
even though the bytes do not. Together with ``SOURCES.md``, which records how
each file was obtained, it makes the raw layer reconstructible or at least
auditable.

    python src/archive.py            # build/refresh the manifest
    python src/archive.py --verify   # re-hash and report drift
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

MANIFEST = Path("data/archive_manifest.csv")
COLUMNS = ["path", "bytes", "sha256", "modified_utc", "provenance"]

# Longest matching prefix wins, so specific paths override general ones.
PROVENANCE = {
    "data/raw/elections/_source/npe2014": "elections.org.za Downloadable-results, 2014 NPE complete VD-level (zipped CSV)",
    "data/raw/elections/_source/npe2019": "results.elections.org.za NPEPublicReports/827/Downloadable Results/Provincial.zip",
    "data/raw/elections/_source/npe2024": "results.elections.org.za NPEPublicReports/1335/Downloadable Results/Provincial.zip",
    "data/raw/elections/_source/lge2016_national": "elections.org.za Downloadable-results, 2016 LGE complete VD-level (zipped CSV)",
    "data/raw/elections/_source/lge2016_JHB_seats": "results.elections.org.za LGEPublicReports/402/Seat Calculation Detail/GP/JHB.pdf",
    "data/raw/elections/_source/lge2021_JHB_seats": "results.elections.org.za LGEPublicReports/1091/Seat Calculation Detail/GP/JHB.pdf",
    "data/raw/elections/_source/lge2021_JHB_detailed": "results.elections.org.za LGEPublicReports/1091/Detailed Results/GP/JHB.pdf",
    "data/raw/elections/_reports/": "results.elections.org.za LGEPublicReports/{402,1091,197}, via src/fetch_iec.py",
    "data/raw/elections/lge": "derived: src/ingest_lge.py",
    "data/raw/elections/npe": "derived: src/ingest_npe.py",
    # These two are raw downloads that predate fetch_iec.py, so they sit beside
    # the derived files and would otherwise inherit the wrong label.
    "data/raw/elections/lge2016_JHB_vd_party.csv": "results.elections.org.za LGEPublicReports/402/Downloadable Party Results/GP/JHB.csv",
    "data/raw/elections/lge2021_JHB_vd_party.csv": "results.elections.org.za LGEPublicReports/1091/Downloadable Party Results/GP/JHB.csv",
    "data/raw/geo/wards2011_SA": "arcgis.com item 12d2deb98816451ab7c4dc09cdfeee6b (MDB Wards 2011, File Geodatabase)",
    "data/raw/geo/wards2016_SA": "arcgis.com item cfddb54aab5f4d62b2144d80d49b3fdb (MDB Wards 2016, File Geodatabase)",
    "data/raw/geo/wards2011_JHB": "derived: src/build_geo.py, clipped from wards2011_SA",
    "data/raw/geo/wards2016_JHB": "derived: src/build_geo.py, clipped from wards2016_SA",
    "data/raw/geo/wards2020_JHB": "MDB FeatureServer SA_Wards2020 (2021 LGE delimitation), via src/fetch_boundaries.py",
    "data/raw/geo/wards2026_JHB": "MDB FeatureServer MDBWards2026, via src/fetch_boundaries.py",
    "data/raw/geo/vds2026_JHB": "MDB FeatureServer VotingDistricts2026_Final, via src/fetch_boundaries.py",
    "data/raw/geo/votingstations2026_JHB": "MDB FeatureServer VotingStations_March2026, via src/fetch_boundaries.py",
    "data/raw/byelections/": "results.elections.org.za by-election dashboard MapsJason, via src/fetch_byelections.py",
    "data/raw/covariates/Ward-Product": "statssa.gov.za Ward-level Small Area Population Estimates 2022",
    "data/raw/covariates/Ward Product_Locked spreadsheets/": "unpacked from statssa.gov.za Ward-Product_Locked-spreadsheets.zip",
    "data/raw/covariates/Ward-statistical": "statssa.gov.za ward product technical note",
    "data/processed/": "derived: src/build_concordance.py, src/build_crosswalk.py",
}


def provenance_for(path: str) -> str:
    match = max(
        (key for key in PROVENANCE if path.startswith(key)), key=len, default=None
    )
    return PROVENANCE[match] if match else "UNRECORDED -- add to src/archive.py"


def digest(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def scan(roots: list[Path]) -> list[dict[str, str]]:
    rows = []
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.name in {".gitkeep", ".DS_Store"}:
                continue
            if path == MANIFEST:
                continue
            stat = path.stat()
            key = path.as_posix()
            rows.append(
                {
                    "path": key,
                    "bytes": str(stat.st_size),
                    "sha256": digest(path),
                    "modified_utc": datetime.fromtimestamp(
                        stat.st_mtime, timezone.utc
                    ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "provenance": provenance_for(key),
                }
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="check against the manifest")
    parser.add_argument(
        "--roots",
        nargs="*",
        type=Path,
        default=[Path("data/raw"), Path("data/processed")],
    )
    args = parser.parse_args(argv)

    current = scan(args.roots)

    if args.verify:
        if not MANIFEST.exists():
            print(f"no manifest at {MANIFEST} -- run without --verify first")
            return 1
        with MANIFEST.open(encoding="utf-8", newline="") as handle:
            recorded = {row["path"]: row for row in csv.DictReader(handle)}
        now = {row["path"]: row for row in current}

        missing = sorted(set(recorded) - set(now))
        added = sorted(set(now) - set(recorded))
        changed = [
            p for p in sorted(set(recorded) & set(now))
            if recorded[p]["sha256"] != now[p]["sha256"]
        ]
        for label, items in (("missing", missing), ("changed", changed), ("new", added)):
            for item in items:
                print(f"  {label:<8s} {item}")
        total = len(missing) + len(changed) + len(added)
        print(f"\n{len(now):,} files; {total} difference(s) from the manifest")
        return 1 if missing or changed else 0

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(current)

    total = sum(int(row["bytes"]) for row in current)
    unrecorded = [r["path"] for r in current if r["provenance"].startswith("UNRECORDED")]
    print(f"{len(current):,} files, {total / 1e6:,.1f} MB -> {MANIFEST}")
    for row in current:
        print(f"  {int(row['bytes']) / 1e6:>8.2f} MB  {row['path']}")
    if unrecorded:
        print(f"\n{len(unrecorded)} file(s) with no recorded provenance:")
        for path in unrecorded:
            print(f"  - {path}")
        return 1
    print("\nevery file has recorded provenance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
