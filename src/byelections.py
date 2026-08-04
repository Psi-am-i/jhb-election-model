"""By-election evidence for the 2026 forecast (plan §3.6, §3.3 covariate).

This implements the part of the plan the original build skipped (review E4):
the 15 CoJ by-elections since 2021 are turned into two quantitative signals
rather than narrative colour.

**Share deltas, not levels (assumption A4).** A by-election's raw share
inherits massive selection bias — contests happen where councillors die,
resign or defect, skewing toward unstable wards. Within-ward *deltas* against
the same ward's 2021 ward-ballot result largely difference that out. Per plan
§3.6 each contest is weighted

    weight(j) = exp(−age_months(j) / τ) × √(votes_cast(j)) × ρ(j)

where ρ(j) is the similarity of ward j's party profile to the citywide profile
(1 − total-variation distance on the 2021 ward ballot), so a by-election in a
demographically typical ward counts for more than one in an outlier.

**Turnout ratio (plan §3.3's discarded covariate).** Each contest's turnout
relative to the same ward's 2021 turnout, normalised by the citywide median of
that ratio across contests, is a live differential-enthusiasm signal — the
Ward 99 Linden collapse (24% from 57%) is exactly the suburban-apathy failure
mode nothing else measures before election day.

Caveats carried forward, and why the output is a *tilt* rather than a truth:
by-elections are candidate contests at 18–50% turnout; a party absent from a
contest contributes no delta for it (absence is a nomination decision, not a
collapse); MK's deltas are measured against a zero 2021 base and are therefore
genuine new-party evidence, not swing. The consumer (montecarlo.py) blends
these deltas in at weight ``w_bye`` (default 0.4 per §3.5) — they move the
centre of the prior, never replace it.

Outputs:
    data/processed/byelection_party_deltas.csv   weighted per-party share deltas
    data/processed/byelection_turnout.csv        per-ward turnout ratios

Usage:
    python src/byelections.py [--tau 18]
"""

from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

import parties as P

ELECTION_DAY = date(2026, 11, 4)
JHB_PREFIX = "798"


def load_byelections(path: Path) -> dict[tuple[str, str], dict]:
    """Return (date, ward) -> {party: votes} for CoJ contests."""
    contests: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ward = row["WardID"]
            if not ward.startswith(JHB_PREFIX):
                continue
            key = (row["ByElectionDate"], ward)
            party = P.canonical(row["PartyFullName"])
            contests[key][party] = contests[key].get(party, 0) + int(row["Party_Votes"])
    return contests


def ward_2021(path: Path) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """2021 ward-ballot votes per ward, and registered voters per ward."""
    votes: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    registered_vd: dict[tuple[str, str], int] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["BallotType"].upper() != "WARD":
                continue
            ward = row["Ward"]
            votes[ward][P.canonical(row["sPartyName"])] += int(row["Party_Votes"])
            registered_vd[(ward, row["VD_Number"])] = int(row["Registered_Population"])
    registered: defaultdict[str, int] = defaultdict(int)
    for (ward, _vd), reg in registered_vd.items():
        registered[ward] += reg
    return {w: dict(v) for w, v in votes.items()}, dict(registered)


def similarity(local: dict[str, float], city: dict[str, float]) -> float:
    """1 − total-variation distance between a ward's shares and the citywide mix."""
    keys = set(local) | set(city)
    return 1.0 - 0.5 * sum(abs(local.get(k, 0.0) - city.get(k, 0.0)) for k in keys)


def age_months(when: str) -> float:
    d = date.fromisoformat(when)
    return (ELECTION_DAY.year - d.year) * 12 + (ELECTION_DAY.month - d.month) + (
        ELECTION_DAY.day - d.day
    ) / 30.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau", type=float, default=18.0,
                        help="recency half-life in months (plan §3.5, range 6-36)")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)

    contests = load_byelections(
        args.data_dir / "byelections" / "byelections_Gauteng_vd_party.csv"
    )
    votes21, registered21 = ward_2021(
        args.data_dir / "elections" / "lge2021_JHB_vd_party_clean.csv"
    )

    city_totals: defaultdict[str, int] = defaultdict(int)
    for tally in votes21.values():
        for party, count in tally.items():
            city_totals[party] += count
    city_cast = sum(city_totals.values())
    city_share = {p: v / city_cast for p, v in city_totals.items()}

    # --- per-contest deltas and weights -------------------------------------
    delta_rows = []
    turnout_rows = []
    weighted: defaultdict[str, float] = defaultdict(float)
    weight_sum: defaultdict[str, float] = defaultdict(float)

    for (when, ward), tally in sorted(contests.items()):
        base = votes21.get(ward)
        if not base:
            print(f"  ! no 2021 ward-ballot base for {ward} ({when}); skipped")
            continue
        base_cast = sum(base.values())
        bye_cast = sum(tally.values())
        base_share = {p: v / base_cast for p, v in base.items()}
        rho = similarity(base_share, city_share)
        w = math.exp(-age_months(when) / args.tau) * math.sqrt(bye_cast) * rho

        reg = registered21.get(ward, 0)
        t21 = base_cast / reg if reg else float("nan")
        t_bye = bye_cast / reg if reg else float("nan")
        turnout_rows.append(
            {"ward": ward, "date": when, "turnout_2021": t21, "turnout_bye": t_bye,
             "ratio": t_bye / t21 if t21 else float("nan"), "votes_cast": bye_cast}
        )

        for party in set(tally):  # only parties that contested (A4: absence ≠ collapse)
            d = tally[party] / bye_cast - base_share.get(party, 0.0)
            weighted[party] += w * d
            weight_sum[party] += w
            delta_rows.append(
                {"ward": ward, "date": when, "party": party,
                 "share_2021": f"{base_share.get(party, 0.0):.4f}",
                 "share_bye": f"{tally[party] / bye_cast:.4f}",
                 "delta": f"{d:+.4f}", "weight": f"{w:.2f}", "rho": f"{rho:.3f}"}
            )

    ratios = [r["ratio"] for r in turnout_rows if r["ratio"] == r["ratio"]]
    median_ratio = statistics.median(ratios)
    for row in turnout_rows:
        row["ratio_vs_median"] = (
            row["ratio"] / median_ratio if row["ratio"] == row["ratio"] else float("nan")
        )

    # --- report and write ----------------------------------------------------
    print(f"{len(turnout_rows)} CoJ by-elections, τ = {args.tau} months\n")
    print(f"  {'party':<10s} {'contests':>8s} {'Σweight':>9s} {'weighted Δ':>11s}")
    summary = []
    for party in sorted(weighted, key=lambda p: -weight_sum[p]):
        n = sum(1 for r in delta_rows if r["party"] == party)
        mean_delta = weighted[party] / weight_sum[party]
        summary.append({"party": party, "contests": n,
                        "weight_sum": f"{weight_sum[party]:.2f}",
                        "weighted_delta": f"{mean_delta:+.4f}"})
        if weight_sum[party] > 10:
            print(f"  {party:<10s} {n:>8d} {weight_sum[party]:>9.1f} {mean_delta:>+10.1%}")

    print(f"\n  turnout ratio (bye/2021), citywide median {median_ratio:.3f}:")
    for row in sorted(turnout_rows, key=lambda r: r["ratio_vs_median"]):
        print(f"    ward {row['ward'][-3:]}  {row['date']}  "
              f"{row['turnout_bye']:.1%} vs {row['turnout_2021']:.1%}  "
              f"(× {row['ratio_vs_median']:.2f} of median)")

    args.processed.mkdir(parents=True, exist_ok=True)
    out_deltas = args.processed / "byelection_party_deltas.csv"
    with out_deltas.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0]))
        writer.writeheader()
        writer.writerows(summary)

    out_detail = args.processed / "byelection_contest_detail.csv"
    with out_detail.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(delta_rows[0]))
        writer.writeheader()
        writer.writerows(delta_rows)

    out_turnout = args.processed / "byelection_turnout.csv"
    with out_turnout.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(turnout_rows[0]))
        writer.writeheader()
        for row in turnout_rows:
            writer.writerow({**row,
                             "turnout_2021": f"{row['turnout_2021']:.4f}",
                             "turnout_bye": f"{row['turnout_bye']:.4f}",
                             "ratio": f"{row['ratio']:.4f}",
                             "ratio_vs_median": f"{row['ratio_vs_median']:.4f}"})

    print(f"\nwrote {out_deltas}, {out_detail}, {out_turnout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
