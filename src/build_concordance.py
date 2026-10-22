"""Build the VD concordance and the VD -> 2026 ward apportionment (plan §2, steps 2 and 5).

The plan anticipates a hard spatial problem: historic VDs intersected against
2026 VDs, votes apportioned across children, boundary nibbles thresholded. The
data turns out to be much kinder than that, in one way and less kind in another.

**Kinder: VD numbers are stable.** Between 98.8% and 100% of the VDs in each
historic election still exist in the 2026 VD set under the same number, and the
VDs that do not carry only 0.21%-0.45% of that election's votes. The concordance
is therefore keyed on VD number, with a small named residual, rather than a
shapefile intersection. A handful of the leftovers are recoverable by
voting-station name; most are tents and temporary stations that simply stopped
existing. Whatever is still unmatched is reported, not silently dropped.

**The caveat that matters.** A stable VD *number* is not a stable VD *boundary*.
When a VD splits, one child conventionally keeps the parent's number over a
smaller area, so an unchanged number can still hide a changed catchment -- and a
historic vote total would then describe a different piece of ground from the
2026 VD it is matched to. No historic VD boundaries are published (the MDB hosts
only 2026-era voting-district layers), so this cannot be checked geometrically
with the data in hand. Two independent proxies both suggest catchments are
broadly stable for VDs whose number persists:

* registration tracks the citywide trend closely -- median per-VD ratio 0.97-0.99
  against citywide, with only 0-2 VDs per transition losing more than 30%
  relative, where routine carve-ups would leave a fat left tail;
* roughly 90% of VDs keep the same voting station between consecutive
  elections, rising to 99.1% from 2024 to 2026.

Neither is proof. So rather than assume the question away, every VD is given a
``stability`` flag from those two signals, and the unstable ones can be
down-weighted through ``w_split`` (plan §2 step 2, default 0.6) exactly as
split-derived observations are. The risk is concentrated in the backtest folds,
which compare VD-level shares across time; the 2026 projection is much less
exposed, because the 2026 VD set *is* the 2024 set.

Note also that changing *ward* boundaries are not a source of error here. Votes
are attached to VD numbers and then apportioned into 2026 wards using 2026
registration, which is precisely the mechanism that absorbs ward reshape.

**Less kind: VDs do not nest inside 2026 wards.** 181 of 865 VDs straddle a 2026
ward boundary and are stored as one polygon per ward part, so their votes have
to be apportioned between wards.

That apportionment is where the MDB data pays off. Assumption A1 asks that
splits be weighted by *registered voters* rather than area wherever the roll
permits. It does permit: on the 2026 VD layer ``REGPOP`` is the VD's total
registration, repeated on each part, while ``WardPop`` is that part's own
registration. They reconcile exactly -- every one of the 865 VDs has parts
summing to its total, and the grand total is 2,348,781.

Weighting by registration rather than area also fixes 59 parts that have zero
registered voters. These are slivers where a VD polygon crosses a ward boundary
without any voters on the other side; area weighting would hand them a real
share of the vote.

Usage:
    python src/build_concordance.py
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
import inputs_preflight
import re
from collections import defaultdict
from pathlib import Path

import geopandas as gpd

# Each election, its file, and the ballot to read for VD membership.
ELECTIONS = {
    # ⛔ EXTENDED BACK TO 1999 ON 2026-09-01. This table began at 2011, so every
    # election before it was joined on ward numbers that were redrawn at each
    # delimitation — comparing different pieces of ground and calling it a
    # transition. The voting district is the stable atom and it is stable a long
    # way back: 723 of 727 of Johannesburg's 2006 VDs survive into 2011, and 648
    # of 652 of its 2000 VDs survive into 2006. Owner, 2026-08-31: *"you have
    # the ward maps. Calculate what ward became what and adjust systematically
    # to compensate when this happens (and it happens in every cycle)."*
    "1999": ("npe1999_approx_{CODE}_vd_party.csv", None),
    "2000": ("lge2000_{CODE}_vd_party_clean.csv", "PR"),
    "2004": ("npe2004_{CODE}_vd_party.csv", None),
    "2006": ("lge2006_{CODE}_vd_party_clean.csv", "PR"),
    "2009": ("npe2009_{CODE}_vd_party.csv", None),
    "2011": ("lge2011_{CODE}_vd_party_clean.csv", "PR"),
    "2014": ("npe2014_{CODE}_vd_party.csv", None),
    "2016": ("lge2016_{CODE}_vd_party_clean.csv", "PR"),
    "2019": ("npe2019_{CODE}_vd_party.csv", None),
    "2021": ("lge2021_{CODE}_vd_party_clean.csv", "PR"),
    "2024": ("npe2024_{CODE}_vd_party.csv", None),
}


# A VD whose registration moves this far against the citywide trend, or whose
# voting station changes, is treated as possibly redrawn rather than assumed
# stable. Deliberately loose: the flag feeds a down-weight, not an exclusion.
REG_DRIFT_TOLERANCE = 0.30


def normalise_station(name: str) -> str:
    """Fold a voting-station name for comparison across elections."""
    folded = re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper())
    return re.sub(r"\s+", " ", folded).strip()


def read_vd_votes(path: Path, ballot: str | None) -> dict[str, tuple[str, int, int]]:
    """Return VD -> (voting-station name, total votes, registered voters)."""
    names: dict[str, str] = {}
    registered: dict[str, int] = {}
    votes: defaultdict[str, int] = defaultdict(int)
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if ballot and row.get("BallotType", "").upper() != ballot.upper():
                continue
            vd = row["VD_Number"]
            names.setdefault(vd, row.get("VS_Name", "").strip())
            registered.setdefault(vd, int(row["Registered_Population"]))
            votes[vd] += int(row["Party_Votes"])
    return {
        vd: (names.get(vd, ""), total, registered.get(vd, 0))
        for vd, total in votes.items()
    }


def stability_flags(
    source: dict[str, tuple[str, int, int]],
    later: dict[str, tuple[str, int, int]],
) -> dict[str, str]:
    """Compare a VD against the next election: 'stable', or why it is suspect.

    Registration is compared *relative to the citywide change*, so a VD is only
    flagged when it moves against the city rather than with it.
    """
    common = [vd for vd in source if vd in later and source[vd][2] > 200]
    if not common:
        return {}
    citywide = sum(later[vd][2] for vd in common) / sum(source[vd][2] for vd in common)

    flags: dict[str, str] = {}
    for vd, (station, _, registered) in source.items():
        if vd not in later:
            continue
        reasons = []
        if registered > 200:
            ratio = (later[vd][2] / registered) / citywide
            if abs(ratio - 1) > REG_DRIFT_TOLERANCE:
                reasons.append("registration_drift")
        # Only meaningful when both sides actually name a station: the 2014 bulk
        # export carries no station names, so comparing against it would flag
        # every VD in 2011 and 2014 rather than telling us anything.
        before, after = normalise_station(station), normalise_station(later[vd][0])
        if before and after and before != after:
            reasons.append("station_changed")
        flags[vd] = "+".join(reasons) if reasons else "stable"
    return flags


def ward_parts(vds: gpd.GeoDataFrame) -> list[dict[str, str]]:
    """Return one row per VD/ward part, weighted by that part's registered voters."""
    frame = vds.copy()
    frame["VD_Number"] = frame["VDNumber"].astype(str)
    parts = frame.groupby("VD_Number")["WardNo"].transform("nunique")

    rows = []
    for _, row in frame.sort_values(["VD_Number", "WardNo"]).iterrows():
        total = int(row["REGPOP"])
        part = int(row["WardPop"])
        rows.append(
            {
                "VD_Number": row["VD_Number"],
                "Ward_2026": str(row["WardNo"]),
                "WardID_2026": str(row.get("WardID", "")),
                "vd_registered": str(total),
                "part_registered": str(part),
                # Registration weight per assumption A1. A VD wholly inside one
                # ward gets 1.0; a zero-voter sliver correctly gets 0.0.
                "weight": f"{(part / total if total else 0.0):.6f}",
                "is_split": "Y" if parts[row.name] > 1 else "N",
            }
        )
    return rows


ASSIGNMENT_2026 = Path("archive/vd-ward-assignment-2026/assignment.csv")


def read_assignment(path: Path | None = None) -> dict[str, str]:
    """``{VD_Number: WardID_2026}`` from the committed assignment file
    (archive/vd-ward-assignment-2026/README.md)."""
    path = cityconfig.resolve_path(path or ASSIGNMENT_2026)
    with path.open(encoding="utf-8", newline="") as fh:
        return {r["VD_Number"].strip(): r["WardID_2026"].strip()
                for r in csv.DictReader(fh)}


def apportion_roll(rows: list[dict[str, str]], roll: dict[str, int],
                   assignment: dict[str, str]) -> None:
    """Add ``part_registered_2026`` to ``ward_parts`` rows, in place.

    The rule (JUDGEMENT-CALLS section T1): the IEC counts each of its voting
    districts wholly in one ward, so each VD is assigned to ONE ward
    (``assignment``, ``{VD_Number: WardID}``) and its whole 2026 figure sits on
    that ward's row, 0 on its other parts. A ward's VDs are scaled by
    ``roll[w] / sum(vd_registered of the VDs assigned to w)`` and made whole
    numbers by largest remainder (ties to the earlier VD number), so the ward's
    rows sum to ``roll[w]`` exactly. ``roll`` is ``{WardID: registered}``.

    Refuses, rather than passes: a VD missing from the assignment, an
    assignment naming a VD the crosswalk lacks, an assigned ward that is not one
    of the VD's parts, a ward left with no VDs or with no registration, and a
    ward set that differs between the snapshot and the crosswalk."""
    wards = {row["WardID_2026"] for row in rows}
    if wards != set(roll):
        raise SystemExit(
            f"the snapshot and the crosswalk name different wards: "
            f"{sorted(set(roll) - wards)[:5]} only in the snapshot, "
            f"{sorted(wards - set(roll))[:5]} only in the crosswalk")
    vd_parts: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        vd_parts[row["VD_Number"]].append(row)
    missing = sorted(set(vd_parts) - set(assignment))
    if missing:
        raise SystemExit(f"{len(missing)} VD(s) missing from the assignment: {missing[:5]}")
    extra = sorted(set(assignment) - set(vd_parts))
    if extra:
        raise SystemExit(f"{len(extra)} assigned VD(s) not in the crosswalk: {extra[:5]}")
    by_ward: defaultdict[str, list[str]] = defaultdict(list)
    for vd, parts in vd_parts.items():
        if assignment[vd] not in {p["WardID_2026"] for p in parts}:
            raise SystemExit(f"VD {vd} is assigned to ward {assignment[vd]}, "
                             f"which is not one of its parts")
        by_ward[assignment[vd]].append(vd)
    registered = {vd: int(parts[0]["vd_registered"]) for vd, parts in vd_parts.items()}
    figure: dict[str, int] = {}
    for ward in sorted(roll):
        vds = sorted(by_ward.get(ward, []))
        if not vds:
            raise SystemExit(f"ward {ward}: no VD is assigned to it")
        base = sum(registered[v] for v in vds)
        if base <= 0:
            raise SystemExit(f"ward {ward}: its assigned VDs sum to {base}, so "
                             f"the snapshot's {roll[ward]} cannot be apportioned")
        quota = {v: registered[v] * roll[ward] / base for v in vds}
        given = {v: int(q) for v, q in quota.items()}
        order = sorted(vds, key=lambda v: (-(quota[v] - given[v]), v))
        for v in order[:roll[ward] - sum(given.values())]:
            given[v] += 1
        figure.update(given)
    for row in rows:
        row["part_registered_2026"] = str(
            figure[row["VD_Number"]] if assignment[row["VD_Number"]] == row["WardID_2026"] else 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geo-dir", type=Path, default=Path("data/raw/geo"))
    parser.add_argument("--elections-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="where to write (default: the city's own "
                             "processed directory)")
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    city = cityconfig.use(getattr(args, "city", None))

    # {CODE} IS SUBSTITUTED, and was not until 2026-08-18: this read the literal
    # string "vds2026_{CODE}.geojson", which exists for no city, so the script
    # could not be run for any of the eight metros -- including Johannesburg,
    # whose file is `vds2026_JHB.geojson`. `cityconfig.resolve_path` is the
    # helper that already existed for this.
    geo = cityconfig.resolve_path(args.geo_dir / "vds2026_{CODE}.geojson")
    if not geo.exists():
        raise SystemExit(
            f"no 2026 VD layer for {city.name}: {geo}\n"
            f"  Download it from the MDB Spatial Knowledge Hub -- see SOURCES.md, "
            f"'Boundaries'. A missing per-city input REFUSES here rather than "
            f"falling back to another city's, which is the fault MODEL-LOG "
            f"§1.40 records shipping.")
    vds = gpd.read_file(geo)

    # PER CITY, and it was not: --out-dir defaulted to `data/processed` for
    # every city, so a Tshwane run would overwrite Johannesburg's concordance
    # under a name that does not say whose it is. `city.processed` is the
    # per-city directory the rest of the pipeline already reads.
    out_dir = args.out_dir if args.out_dir is not None else city.processed
    out_dir = cityconfig.resolve_path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 5: VD -> 2026 ward, registration weighted -----------------------
    parts = ward_parts(vds)
    # The 2026 roll: the IEC snapshot, apportioned over the parts. Absent for a
    # city with no snapshot, in which case the crosswalk carries the MDB layer's
    # registration only and says so by lacking the column.
    snap = inputs_preflight.roll_snapshot(city.slug)
    if snap is not None:
        apportion_roll(parts, inputs_preflight.read_roll_snapshot(snap),
                       read_assignment())
        for part in parts:
            part["roll_snapshot"] = inputs_preflight.snapshot_label(snap)
    destination = out_dir / "vd_ward_2026.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(parts[0]))
        writer.writeheader()
        writer.writerows(parts)

    split_vds = {p["VD_Number"] for p in parts if p["is_split"] == "Y"}
    zero = [p for p in parts if p["weight"] == "0.000000"]
    print(f"VD -> 2026 ward: {len(parts):,} parts, {len({p['VD_Number'] for p in parts}):,} VDs")
    print(f"  {len(split_vds)} VD(s) split across wards; {len(zero)} zero-voter sliver part(s)")
    print(f"  wrote {destination}")

    # --- Step 2: historic VD -> 2026 VD --------------------------------------
    target = {str(v) for v in vds["VDNumber"]}
    by_station: defaultdict[str, set[str]] = defaultdict(set)
    for _, row in vds.iterrows():
        by_station[str(row["VotingStat"]).strip().upper()].add(str(row["VDNumber"]))

    # Stability is judged against the *next* election in the series, so the
    # last one has nothing to compare against and is stable by construction.
    years = list(ELECTIONS)
    loaded = {
        # `read_vd_votes` resolves {CODE} itself (see its first line), so the
        # template is passed through rather than substituted twice.
        year: read_vd_votes(args.elections_dir / filename, ballot)
        for year, (filename, ballot) in ELECTIONS.items()
    }
    flags = {
        year: stability_flags(loaded[year], loaded[years[i + 1]])
        for i, year in enumerate(years[:-1])
    }
    flags[years[-1]] = {vd: "stable" for vd in loaded[years[-1]]}

    concordance = []
    print("\nhistoric VD -> 2026 VD:")
    print(f"  {'election':<9s} {'VDs':>5s} {'identity':>9s} {'by name':>8s} {'lost':>5s}  {'votes lost':>10s}")
    for year in years:
        source = loaded[year]
        cast = sum(total for _, total, _ in source.values())
        identity = named = 0
        lost_votes = 0

        for vd, (station, total, _registered) in sorted(source.items()):
            if vd in target:
                method, mapped = "identity", vd
                identity += 1
            else:
                candidates = by_station.get(station.upper(), set())
                # Only trust a station-name match when it is unambiguous.
                if len(candidates) == 1:
                    method, mapped = "station_name", next(iter(candidates))
                    named += 1
                else:
                    method, mapped = "unmatched", ""
                    lost_votes += total
            concordance.append(
                {
                    "election": year,
                    "vd_historic": vd,
                    "vd_2026": mapped,
                    "method": method,
                    "vs_name": station,
                    "votes": str(total),
                    "stability": flags[year].get(vd, "unknown"),
                }
            )

        lost = len(source) - identity - named
        print(
            f"  {year:<9s} {len(source):>5d} {identity:>9d} {named:>8d} {lost:>5d}"
            f"  {lost_votes / cast:>9.2%}"
        )

    destination = out_dir / "vd_concordance.csv"
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(concordance[0]))
        writer.writeheader()
        writer.writerows(concordance)
    print(f"  wrote {destination}")

    print(
        "\nUnmatched VDs are mostly tents and temporary stations that stopped"
        "\nexisting. They are recorded with method='unmatched' rather than"
        "\ndropped, so the loss stays visible downstream."
    )

    # Boundary-stability flags. A VD keeping its number does not guarantee it
    # kept its catchment, and no historic VD boundaries are published to check
    # against, so these two proxies stand in and feed the w_split down-weight.
    print("\nVD boundary stability vs the following election:")
    print(f"  {'election':<9s} {'stable':>7s} {'suspect':>8s}  {'share of votes suspect':>22s}")
    for year in years:
        rows = [r for r in concordance if r["election"] == year]
        cast = sum(int(r["votes"]) for r in rows)
        suspect = [r for r in rows if r["stability"] not in ("stable", "unknown")]
        flagged = sum(int(r["votes"]) for r in suspect)
        print(
            f"  {year:<9s} {len(rows) - len(suspect):>7d} {len(suspect):>8d}"
            f"  {flagged / cast if cast else 0:>21.1%}"
        )
    print(
        "  ('suspect' = registration moved >30% against the citywide trend, or the\n"
        "   voting station changed. Down-weight these via w_split rather than\n"
        "   excluding them; see the module docstring.)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
