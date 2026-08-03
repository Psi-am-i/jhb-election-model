"""Per-ward turnout leverage on the 2026 council (plan §5).

For each 2026 ward, turnout is perturbed by ±5 percentage points across the VD
parts inside it, shares held fixed, and the whole seat allocation re-run. Leverage
is the resulting change in seats per point of turnout.

Two results from the fold work shape what this can and cannot show:

* The citywide turnout *level* cannot move seats at all — scaling every VD's
  turnout scales the quota identically. Only *differential* turnout matters, so
  perturbing one ward against the rest of the city is exactly the right
  experiment and a citywide turnout scenario would be exactly the wrong one.
* Turnout is second-order against θ for forecast accuracy. Leverage is therefore
  a statement about *sensitivity*, not a forecast: it says where a turnout
  movement would matter most, not how likely one is.

**Baseline.** 2024 NPE VD shares carried to 2026, with γ from fold 1 (which
transfers across cycles) and a citywide target built from §3.5's central θ
defaults. θ is then calibrated to hit that target.

θ is *not* reused from fold 2, even though that is the most recent observed
transition. θ is tied to the baseline it was measured against: fold 2's θ_PA is
huge because the PA went from 0.03% in 2019 to 2.96% in 2021, and applying that
factor to the PA's 2.91% share of 2024 puts it at 116 of 270 seats. That is the
"θ does not transfer" finding from fold 2 showing up as an absurdity rather than
as a modest error, and it is the reason the scenario is specified in citywide
terms and θ solved for, rather than carried over.

This is a scenario, not a forecast — the forecast is §3.5's Monte Carlo over the
parameter ranges. Leverage rankings are far less sensitive to the baseline than
seat counts are, because they depend on the *geography* of support rather than
its level.

Both ballots are given the same citywide target, which ignores split-ticket
voting (ActionSA's ward and PR shares differed by 4pp in 2021). That understates
ward-ballot differences but does not affect the geography that drives leverage.

Assumption A5 — marginal voters resemble their VD — is inherited from the plan
and applies: shares are held fixed under the perturbation.

Usage:
    python src/leverage.py [--delta 0.05]
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

import parties as P
from fold import calibrate_theta, citywide, load, load_parameters, predict, shares
from seats import allocate, eligible_parties

DA_BLOC_COALITION = ("DA", "ASA")

# Central θ defaults from plan §3.5, applied to each party's 2024 CoJ share to
# give a citywide target for 2026. f_other = 1.30 covers everything unlisted.
THETA_CENTRAL = {
    "ANC": 0.75,
    "DA": 1.30,
    "EFF": 0.85,
    "ASA": 1.50,
    "MK": 0.60,
    "PA": 1.40,
}
F_OTHER = 1.30


def scenario_citywide(base_city: dict[str, float]) -> dict[str, float]:
    """Citywide 2026 target from §3.5's central parameters, renormalised to 1."""
    scaled = {
        party: share * THETA_CENTRAL.get(party, F_OTHER)
        for party, share in base_city.items()
        if party != "IND"
    }
    total = sum(scaled.values())
    return {party: value / total for party, value in scaled.items()}


def load_ward_parts(path: Path) -> list[tuple[str, str, int]]:
    """Return (VD, 2026 ward, registered voters in that part)."""
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            (row["VD_Number"], row["Ward_2026"], int(row["part_registered"]))
            for row in csv.DictReader(handle)
        ]


def load_projected_turnout(path: Path) -> dict[str, float]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {
            row["VD_Number"]: float(row["turnout_2026_projected"])
            for row in csv.DictReader(handle)
            if row["turnout_2026_projected"]
        }


def council(
    parts: list[tuple[str, str, int]],
    turnout: dict[str, float],
    predicted: dict[str, dict[str, dict[str, float]]],
    bump: tuple[str, float] | None = None,
) -> tuple[dict[str, int], dict[str, float]]:
    """Allocate the council, optionally perturbing one ward's turnout.

    Returns integer seats *and* fractional entitlements (party votes ÷ quota).

    The fractional figure is what leverage is measured on. Moving one ward of 135
    by five points shifts citywide shares by only about a twentieth of a point,
    which almost never crosses a largest-remainder boundary — so integer seats
    report zero for nearly every ward and a spurious 2 for whichever one happens
    to sit on a rounding edge. That is a property of the rounding, not of the
    ward. Entitlement is continuous and gives the elasticity index §5 asks for.
    """
    ward_bumped, delta = bump if bump else (None, 0.0)
    votes: dict[str, defaultdict[str, float]] = {
        "Ward": defaultdict(float),
        "PR": defaultdict(float),
    }
    for vd, ward, registered in parts:
        rate = turnout.get(vd)
        if rate is None or vd not in predicted["PR"]:
            continue
        if ward == ward_bumped:
            rate = min(max(rate + delta, 0.0), 1.0)
        cast = registered * rate
        for ballot in ("Ward", "PR"):
            for party, share in predicted[ballot][vd].items():
                votes[ballot][party] += cast * share

    combined = eligible_parties(
        {p: int(round(v)) for p, v in votes["Ward"].items()},
        {p: int(round(v)) for p, v in votes["PR"].items()},
    )
    result = allocate(combined)
    entitlement = {p: v / result.quota for p, v in combined.items()}
    return result.seats, entitlement


def council_group(
    parts: list[tuple[str, str, int]],
    turnout: dict[str, float],
    predicted: dict[str, dict[str, dict[str, float]]],
    wards: set[str],
    delta: float,
) -> tuple[dict[str, int], dict[str, float]]:
    """Same as :func:`council`, perturbing a whole set of wards together."""
    votes: dict[str, defaultdict[str, float]] = {
        "Ward": defaultdict(float),
        "PR": defaultdict(float),
    }
    for vd, ward, registered in parts:
        rate = turnout.get(vd)
        if rate is None or vd not in predicted["PR"]:
            continue
        if ward in wards:
            rate = min(max(rate + delta, 0.0), 1.0)
        cast = registered * rate
        for ballot in ("Ward", "PR"):
            for party, share in predicted[ballot][vd].items():
                votes[ballot][party] += cast * share

    combined = eligible_parties(
        {p: int(round(v)) for p, v in votes["Ward"].items()},
        {p: int(round(v)) for p, v in votes["PR"].items()},
    )
    result = allocate(combined)
    return result.seats, {p: v / result.quota for p, v in combined.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--delta", type=float, default=0.05, help="turnout perturbation")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--top", type=int, default=15)
    args = parser.parse_args(argv)

    base_votes, _ = load(args.data_dir / "npe2024_JHB_vd_party.csv", None)
    base_share, base_city = shares(base_votes), citywide(base_votes)
    params = load_parameters(args.processed / "fold1_parameters.csv")
    target_city = scenario_citywide(base_city)
    universe = [p for p in base_city if p != "IND"]

    parts = load_ward_parts(args.processed / "vd_ward_2026.csv")
    turnout = load_projected_turnout(args.processed / "turnout.csv")

    # Weight VDs by their projected 2026 votes cast when solving for θ, so the
    # calibration and the application use the same weighting (MODEL-LOG 1.8).
    registered_by_vd: defaultdict[str, int] = defaultdict(int)
    for vd, _ward, registered in parts:
        registered_by_vd[vd] += registered
    weight = {
        vd: registered_by_vd[vd] * turnout.get(vd, 0.0)
        for vd in base_share
        if vd in registered_by_vd
    }

    predicted = {}
    for ballot in ("Ward", "PR"):
        gamma = {p: params[ballot]["gamma"].get(p, 1.0) for p in universe}
        theta = calibrate_theta(
            base_share, base_city, target_city, gamma, weight, universe
        )
        predicted[ballot] = predict(base_share, base_city, theta, gamma)

    print("2026 central scenario, citywide (§3.5 defaults on the 2024 base):")
    for party in sorted(target_city, key=lambda p: -target_city[p])[:7]:
        print(f"  {party:<10s} {base_city.get(party, 0):>7.2%} -> {target_city[party]:>7.2%}")
    print()

    baseline, _ = council(parts, turnout, predicted)
    total = sum(baseline.values())
    coalition_base = sum(baseline.get(p, 0) for p in DA_BLOC_COALITION)
    print(f"baseline council ({total} seats):")
    for party, seats in sorted(baseline.items(), key=lambda kv: -kv[1])[:8]:
        print(f"  {party:<10s} {seats:>3d}")
    print(f"  DA+ActionSA combined: {coalition_base}  (majority needs 136)\n")

    ward_registered: defaultdict[str, int] = defaultdict(int)
    ward_turnout_num: defaultdict[str, float] = defaultdict(float)
    for vd, ward, registered in parts:
        ward_registered[ward] += registered
        ward_turnout_num[ward] += registered * turnout.get(vd, 0.0)

    rows = []
    for ward in sorted(ward_registered, key=lambda w: int(w)):
        up_seats, up = council(parts, turnout, predicted, (ward, args.delta))
        down_seats, down = council(parts, turnout, predicted, (ward, -args.delta))
        # Total entitlement displaced, halved because every seat gained by one
        # party is lost by another and would otherwise be counted twice.
        moved = sum(abs(up.get(p, 0.0) - down.get(p, 0.0)) for p in set(up) | set(down)) / 2
        coalition_swing = (
            sum(up.get(p, 0.0) for p in DA_BLOC_COALITION)
            - sum(down.get(p, 0.0) for p in DA_BLOC_COALITION)
        )
        seats_moved_int = sum(
            abs(up_seats.get(p, 0) - down_seats.get(p, 0))
            for p in set(up_seats) | set(down_seats)
        ) // 2
        registered = ward_registered[ward]
        rows.append(
            {
                "ward": ward,
                "registered": registered,
                "turnout": ward_turnout_num[ward] / registered if registered else 0.0,
                "entitlement_moved": moved,
                "seats_moved_int": seats_moved_int,
                "coalition_swing": coalition_swing,
                # Seats moved per point of turnout, over the ±delta span.
                "leverage": moved / (2 * args.delta * 100),
                "leverage_per_10k": moved / (2 * args.delta * 100) / (registered / 10_000)
                if registered
                else 0.0,
            }
        )

    out = args.processed / "ward_leverage.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "turnout": f"{row['turnout']:.4f}",
                             "entitlement_moved": f"{row['entitlement_moved']:.4f}",
                             "coalition_swing": f"{row['coalition_swing']:+.4f}",
                             "leverage": f"{row['leverage']:.5f}",
                             "leverage_per_10k": f"{row['leverage_per_10k']:.5f}"})

    ranked = sorted(rows, key=lambda r: -r["leverage"])
    print(f"highest leverage wards (±{args.delta:.0%} turnout, shares fixed):")
    print(f"  {'ward':>5s} {'registered':>11s} {'turnout':>8s} {'seats/pt':>9s} {'DA+ASA seats':>13s}")
    for row in ranked[: args.top]:
        print(
            f"  {row['ward']:>5s} {row['registered']:>11,} {row['turnout']:>8.1%}"
            f" {row['leverage']:>9.4f} {row['coalition_swing']:>+13.3f}"
        )
    print(f"  (seats/pt = entitlement displaced per percentage point of ward turnout;")
    print(f"   DA+ASA is the coalition's entitlement change across the full ±{args.delta:.0%} span)")

    # --- test the plan's advance prediction --------------------------------
    print(f"\n{'':-<66}")
    print("plan §5 predicts leverage is highest in high-registration,")
    print("high-ANC-share, historically low-turnout wards -- not marginal wards.\n")

    anc_share = {}
    margin = {}
    ward_votes: defaultdict[str, defaultdict[str, float]] = defaultdict(lambda: defaultdict(float))
    for vd, ward, registered in parts:
        if vd not in predicted["PR"]:
            continue
        cast = registered * turnout.get(vd, 0.0)
        for party, share in predicted["PR"][vd].items():
            ward_votes[ward][party] += cast * share
    for ward, tally in ward_votes.items():
        cast = sum(tally.values())
        if not cast:
            continue
        anc_share[ward] = tally.get("ANC", 0.0) / cast
        ordered = sorted(tally.values(), reverse=True)
        margin[ward] = (ordered[0] - ordered[1]) / cast if len(ordered) > 1 else 1.0

    leverage = {r["ward"]: r["leverage"] for r in rows}
    common = [w for w in leverage if w in anc_share]
    def corr(a, b):
        va, vb = np.array([a[w] for w in common]), np.array([b[w] for w in common])
        if va.std() == 0 or vb.std() == 0:
            return float("nan")
        return float(np.corrcoef(va, vb)[0, 1])

    print(f"  correlation of leverage with ward ANC share  : {corr(leverage, anc_share):+.3f}")
    print(f"  correlation of leverage with ward registration: "
          f"{corr(leverage, {w: float(ward_registered[w]) for w in common}):+.3f}")
    print(f"  correlation of leverage with ward turnout     : "
          f"{corr(leverage, {w: ward_turnout_num[w] / ward_registered[w] for w in common}):+.3f}")
    print(f"  correlation of leverage with ward marginality : {corr(leverage, {w: -margin[w] for w in common}):+.3f}")
    print("  (marginality is the negated winner's margin, so positive means")
    print("   leverage is higher in closer wards -- the hypothesis §5 rejects.)")
    # --- the plan's actual claim is about a cluster, not a single ward -------
    # "A ten-point turnout swing across Soweto moves the ANC's citywide share by
    # several points and reallocates a dozen seats." One ward cannot do that;
    # test the cluster.
    print(f"\n{'':-<66}")
    print("cluster test: perturb a whole bloc of wards together by ±5 points")
    print("(§5's claim is about Soweto as a cluster, not any single ward)\n")

    by_anc = sorted(anc_share, key=lambda w: -anc_share[w])
    clusters = {
        "top 30 ANC-share wards (Soweto/Orange Farm-like)": by_anc[:30],
        "bottom 30 ANC-share wards (northern suburbs)": by_anc[-30:],
        "30 most marginal wards": sorted(margin, key=lambda w: margin[w])[:30],
    }
    print(f"  {'cluster':<48s} {'seats moved':>11s} {'DA+ASA':>8s}")
    for label, members in clusters.items():
        group = set(members)
        up_seats, up = council_group(parts, turnout, predicted, group, args.delta)
        down_seats, down = council_group(parts, turnout, predicted, group, -args.delta)
        seats_moved = sum(
            abs(up_seats.get(p, 0) - down_seats.get(p, 0))
            for p in set(up_seats) | set(down_seats)
        ) // 2
        swing = (
            sum(up.get(p, 0.0) for p in DA_BLOC_COALITION)
            - sum(down.get(p, 0.0) for p in DA_BLOC_COALITION)
        )
        print(f"  {label:<48s} {seats_moved:>11d} {swing:>+8.2f}")

    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
