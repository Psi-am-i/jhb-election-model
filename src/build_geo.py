"""Extract the CoJ subsets from the downloaded boundaries and check them.

:mod:`fetch_boundaries` pulls the 2020/2026 layers already filtered to
Johannesburg, but the 2016 and 2011 ward layers are only published as
whole-country File Geodatabases, so they are clipped here.

The checks matter more than the clipping. Plan §0 requires that the 2026 CoJ ward
list contain exactly 135 wards and that we fail loudly otherwise, and §1.2 warns
that VDs split as registration grows -- the 2026 VD layer carries an explicit
``Split_VD`` flag which tells us how much of that has happened.

Usage:
    python src/build_geo.py [--geo-dir data/raw/geo]
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import geopandas as gpd

EXPECTED_WARDS = 135
MUNI_CODE = "JHB"

# Whole-country geodatabases -> (layer, output name, election(s) they apply to)
GDB_LAYERS = {
    "wards2016_SA.gdb.zip": ("MDBWard2016", "wards2016", "2016 LGE"),
    "wards2011_SA.gdb.zip": ("MDBWard2011", "wards2011", "2011 LGE / 2014 NPE"),
}


def clip_gdb(path: Path, layer: str, out: Path, muni: str) -> gpd.GeoDataFrame:
    """Read a country-wide ward geodatabase and keep one municipality."""
    frame = gpd.read_file(path, layer=layer)
    # Column naming differs between the hosted layers (CAT_B) and the archived
    # geodatabases (LocalMunicipalityCode).
    column = next(
        (
            c
            for c in ("CAT_B", "LocalMunicipalityCode", "MunicCode", "CAT2")
            if c in frame.columns
        ),
        None,
    )
    if column is None:
        raise ValueError(f"{path.name}: no municipality code column in {list(frame.columns)}")
    subset = frame[frame[column].astype(str).str.upper() == muni].to_crs(4326)

    # The 2011 geodatabase stores every ward twice, with byte-identical geometry.
    # Drop exact duplicates, but only those -- two rows sharing a ward id with
    # *different* geometry would be a real problem and must not be silently
    # collapsed.
    key = next((c for c in ("WardID", "WardNumber") if c in subset.columns), None)
    if key:
        marked = subset.assign(_wkb=subset.geometry.apply(lambda g: g.wkb))
        deduped = marked.drop_duplicates(subset=[key, "_wkb"]).drop(columns="_wkb")
        if len(deduped) != len(subset):
            print(f"{'':<12s} dropped {len(subset) - len(deduped)} exact duplicate row(s)")
        conflicting = len(deduped) - deduped[key].nunique()
        if conflicting:
            raise ValueError(
                f"{path.name}: {conflicting} ward id(s) appear with differing geometry"
            )
        subset = deduped

    subset.to_file(out, driver="GeoJSON")
    return subset


def write_vd_ward_lookup(vds: gpd.GeoDataFrame, out: Path) -> None:
    """Write the 2026 VD -> ward lookup, one row per VD/ward part.

    A VD straddling a ward boundary appears once per ward, with ``area_share``
    giving that part's fraction of the VD's total area. Area is a placeholder
    weight: apportioning a VD's *votes* between wards should really be weighted
    by registered voters, which needs the VD-part registration figures the plan
    calls for in §2 step 5. Anything consuming ``area_share`` should treat it as
    a first approximation and say so.
    """
    frame = vds.copy()
    frame["VD_Number"] = frame["VDNumber"].astype(str)
    # Equal-area projection so the shares are not distorted by latitude.
    frame["_area"] = frame.to_crs(6933).geometry.area
    frame["area_share"] = frame["_area"] / frame.groupby("VD_Number")["_area"].transform("sum")
    parts = frame.groupby("VD_Number")["WardNo"].transform("nunique")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["VD_Number", "Ward_2026", "WardID_2026", "area_share", "is_split"])
        for _, row in frame.sort_values(["VD_Number", "WardNo"]).iterrows():
            writer.writerow(
                [
                    row["VD_Number"],
                    row["WardNo"],
                    row.get("WardID", ""),
                    f"{row['area_share']:.6f}",
                    "Y" if parts[row.name] > 1 else "N",
                ]
            )
    print(f"\nwrote {out} ({len(frame):,} VD/ward parts)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geo-dir", type=Path, default=Path("data/raw/geo"))
    parser.add_argument("--muni", default=MUNI_CODE)
    parser.add_argument(
        "--elections-dir", type=Path, default=Path("data/raw/elections")
    )
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)

    failures: list[str] = []

    for filename, (layer, name, applies) in GDB_LAYERS.items():
        source = args.geo_dir / filename
        if not source.exists():
            print(f"{name:<12s} MISSING {source.name} -- run fetch_boundaries.py first")
            continue
        out = args.geo_dir / f"{name}_{args.muni}.geojson"
        subset = clip_gdb(source, layer, out, args.muni)
        print(f"{name:<12s} {len(subset):>5,} wards -> {out.name}   ({applies})")

    print()
    wards2026 = gpd.read_file(args.geo_dir / f"wards2026_{args.muni}.geojson")
    wards2020 = gpd.read_file(args.geo_dir / f"wards2020_{args.muni}.geojson")
    vds2026 = gpd.read_file(args.geo_dir / f"vds2026_{args.muni}.geojson")

    # Plan §0: confirm the 2026 ward list is exactly 135, and fail loudly if not.
    print(f"2026 wards: {len(wards2026)} (expected {EXPECTED_WARDS})")
    if len(wards2026) != EXPECTED_WARDS:
        failures.append(f"2026 ward count is {len(wards2026)}, expected {EXPECTED_WARDS}")
    print(f"2021 wards: {len(wards2020)}")

    # VD polygons outnumber VDs because a VD straddling a ward boundary is stored
    # as one polygon per ward part.
    vd_numbers = vds2026["VDNumber"].astype(str)
    unique_vds = vd_numbers.nunique()
    per_vd_wards = vds2026.groupby(vd_numbers)["WardNo"].nunique()
    split = per_vd_wards[per_vd_wards > 1]
    print(
        f"\n2026 VDs: {unique_vds:,} distinct across {len(vds2026):,} polygons"
        f"   ({len(split)} VD(s) split across >1 ward)"
    )
    if "Split_VD" in vds2026.columns:
        flagged = vds2026["Split_VD"].astype(str).str.upper().isin({"Y", "YES", "1", "TRUE"})
        print(f"   Split_VD flag set on {int(flagged.sum()):,} polygons")

    # How much of the 2024 VD universe survives into 2026 -- this is the size of
    # the concordance problem in plan §2 step 2.
    npe2024 = args.elections_dir / "npe2024_JHB_vd_party.csv"
    if npe2024.exists():
        with npe2024.open(encoding="utf-8", newline="") as handle:
            old = {row["VD_Number"] for row in csv.DictReader(handle)}
        new = set(vd_numbers)
        print(
            f"\nVD continuity 2024 -> 2026: {len(old & new):,} of {len(old):,} carry over"
            f"   ({len(old - new):,} gone, {len(new - old):,} new)"
        )

    write_vd_ward_lookup(vds2026, args.processed_dir / "vd_ward_2026.csv")

    if failures:
        print("\nFAIL:")
        for problem in failures:
            print(f"  - {problem}")
        return 1
    print("\nPASS: boundary checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
