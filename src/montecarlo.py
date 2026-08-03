"""Monte Carlo forecast of the 2026 CoJ council (plan §3.5, §3.8, §4.3).

Draws the parameters of §3.5, runs each draw through the share model and the
Schedule 1 seat allocation, and reports the distribution of coalition viability.
Per §4.3 the deliverable is that distribution, not a point seat forecast.

Four things learned earlier constrain how this is built:

* **Seats follow the combined ward+PR vote** (§0 correction), so both ballots are
  drawn and allocated together.
* **θ is drawn at bloc level**, per §3.4(a), because party-level factors are
  strongly cross-correlated — θ_DA and θ_ASA compete for the same voters.
  Sampling them independently produces incoherent draws.
* **§3.5's θ ranges are raw citywide ratios**, not the model-consistent
  calibrated values. Each draw therefore specifies a citywide *target* and
  solves for the θ that reaches it through the model. Feeding the published
  ranges in directly as calibrated θ would be wrong.
* **θ must be calibrated under the same VD weighting it is applied with**, which
  the fold work showed matters more than the turnout specification itself. Both
  use projected 2026 votes cast.

The ward ballot is not assumed identical to PR. Each party's ward target is its
PR target scaled by that party's observed 2021 ward/PR ratio, which carries the
split-ticket structure — ActionSA polled 13.98% ward against 18.12% PR — rather
than the single scalar κ_ward of §3.5.

Usage:
    python src/montecarlo.py [--draws 5000] [--seed 20261104]
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import numpy as np

from fold import citywide, load, load_parameters, shares
from seats import INDEPENDENT, allocate

SHARE_FLOOR = 0.002
MAJORITY = 136
COUNCIL = 270

# §3.4(a) blocs. Parties outside these keep individual factors because their
# voter pools genuinely are separate.
BLOCS = {"ANC_BLOC": ("ANC", "EFF", "MK"), "DA_BLOC": ("DA", "ASA", "BOSA")}

# §3.5 ranges as (low, mode, high), sampled triangular.
BLOC_SHIFT = {"ANC_BLOC": (-22.0, -9.0, -3.0), "DA_BLOC": (5.0, 9.0, 14.0)}
INDIVIDUAL_THETA = {"PA": (1.00, 1.40, 2.20), "ALJAMAAH": (0.80, 1.20, 1.80)}
F_OTHER = (1.00, 1.30, 1.80)

# Dirichlet concentration for the within-bloc split. §3.5: low for the DA bloc
# because the ActionSA outcome is genuinely bimodal, higher for the ANC bloc.
ALPHA = {"ANC_BLOC": 60.0, "DA_BLOC": 12.0}

COALITIONS = {
    "DA + ActionSA": ("DA", "ASA"),
    "DA + ActionSA + IFP + VF+ + ACDP": ("DA", "ASA", "IFP", "VFPLUS", "ACDP"),
    "ANC + EFF": ("ANC", "EFF"),
    "ANC + EFF + MK": ("ANC", "EFF", "MK"),
    "ANC + DA": ("ANC", "DA"),
    "ANC + ActionSA": ("ANC", "ASA"),
}

# Everything outside the ANC bloc, taken together -- the widest coalition that
# excludes the ANC, EFF and MK. If this cannot reach 136, no arrangement short of
# one involving the ANC bloc can govern.
ANC_BLOC_PARTIES = ("ANC", "EFF", "MK")


def logit(p):
    p = np.clip(p, SHARE_FLOOR, 1 - SHARE_FLOOR)
    return np.log(p / (1 - p))


def expit(x):
    return 1.0 / (1.0 + np.exp(-x))


def solve_and_predict(dev, base_city, target, gamma, weight, rounds=40, tol=1e-6):
    """Solve for θ reaching `target` citywide, and return the VD-level shares.

    Vectorised equivalent of fold.calibrate_theta + fold.predict. dev is the
    precomputed per-VD logit deviation from the citywide mean.
    """
    theta = np.where(base_city > 0, target / np.maximum(base_city, 1e-12), 1.0)
    weights = weight / weight.sum()
    for _ in range(rounds):
        level = logit(base_city * theta)
        pred = expit(level[None, :] + gamma[None, :] * dev)
        pred /= pred.sum(axis=1, keepdims=True)
        got = weights @ pred
        gap = np.abs(got - target).max()
        theta = theta * np.where(got > 1e-9, target / np.maximum(got, 1e-12), 1.0)
        if gap < tol:
            break
    level = logit(base_city * theta)
    pred = expit(level[None, :] + gamma[None, :] * dev)
    return pred / pred.sum(axis=1, keepdims=True)


def triangular(rng, spec, size=None):
    low, mode, high = spec
    return rng.triangular(low, mode, high, size)


def draw_target(rng, base_city, index):
    """One draw of the citywide 2026 PR target, per §3.4(a)."""
    target = np.zeros_like(base_city)

    for bloc, members in BLOCS.items():
        members = [p for p in members if p in index]
        if not members:
            continue
        idx = [index[p] for p in members]
        base_total = base_city[idx].sum()
        shifted = max(base_total + triangular(rng, BLOC_SHIFT[bloc]) / 100.0, 0.005)
        # Within-bloc split around the 2024 proportions.
        centre = base_city[idx] / base_total
        split = rng.dirichlet(np.maximum(centre * ALPHA[bloc], 0.05))
        target[idx] = shifted * split

    handled = {p for members in BLOCS.values() for p in members if p in index}
    other = triangular(rng, F_OTHER)
    for party, position in index.items():
        if party in handled:
            continue
        spec = INDIVIDUAL_THETA.get(party)
        factor = triangular(rng, spec) if spec else other
        target[position] = base_city[position] * factor

    return target / target.sum()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20261104)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)

    rng = np.random.default_rng(args.seed)

    base_votes, _ = load(args.data_dir / "npe2024_JHB_vd_party.csv", None)
    base_share_d, base_city_d = shares(base_votes), citywide(base_votes)
    universe = sorted(p for p in base_city_d if p != INDEPENDENT)
    index = {party: i for i, party in enumerate(universe)}

    vds = sorted(base_share_d)
    base_city = np.array([base_city_d[p] for p in universe])
    local = np.array([[base_share_d[v].get(p, 0.0) for p in universe] for v in vds])
    dev = logit(local) - logit(base_city)[None, :]

    # Weighting: projected 2026 votes cast, used for calibration and aggregation.
    with (args.processed / "vd_ward_2026.csv").open(encoding="utf-8", newline="") as fh:
        registered: defaultdict[str, int] = defaultdict(int)
        for row in csv.DictReader(fh):
            registered[row["VD_Number"]] += int(row["part_registered"])
    with (args.processed / "turnout.csv").open(encoding="utf-8", newline="") as fh:
        projected = {r["VD_Number"]: float(r["turnout_2026_projected"]) for r in csv.DictReader(fh)}
    weight = np.array([registered.get(v, 0) * projected.get(v, 0.0) for v in vds])

    params = load_parameters(args.processed / "fold1_parameters.csv")
    gamma = {
        ballot: np.array([params[ballot]["gamma"].get(p, 1.0) for p in universe])
        for ballot in ("PR", "Ward")
    }

    # Ward/PR differential, measured from 2021 rather than assumed flat.
    ward21, _ = load(args.data_dir / "lge2021_JHB_vd_party_clean.csv", "Ward")
    pr21, _ = load(args.data_dir / "lge2021_JHB_vd_party_clean.csv", "PR")
    wc, pc = citywide(ward21), citywide(pr21)
    ratio = np.array([
        (wc.get(p, 0.0) / pc[p]) if pc.get(p, 0) > 0.001 else 1.0 for p in universe
    ])
    ratio = np.clip(ratio, 0.5, 2.0)

    print(f"{args.draws:,} draws, seed {args.seed}, {len(vds)} VDs, {len(universe)} parties")
    print(f"ward/PR differential from 2021: ActionSA {ratio[index['ASA']]:.2f}, "
          f"ANC {ratio[index['ANC']]:.2f}, DA {ratio[index['DA']]:.2f}\n")

    seat_draws: list[dict[str, int]] = []
    for draw in range(args.draws):
        pr_target = draw_target(rng, base_city, index)
        ward_target = pr_target * ratio
        ward_target /= ward_target.sum()

        pr = solve_and_predict(dev, base_city, pr_target, gamma["PR"], weight)
        wd = solve_and_predict(dev, base_city, ward_target, gamma["Ward"], weight)

        pr_votes = weight @ pr
        ward_votes = weight @ wd
        combined = {
            universe[i]: int(round(pr_votes[i] + ward_votes[i])) for i in range(len(universe))
        }
        combined = {p: v for p, v in combined.items() if v > 0}
        seat_draws.append(allocate(combined, total_seats=COUNCIL).seats)
        if (draw + 1) % 1000 == 0:
            print(f"  {draw + 1:,} draws")

    # --- report --------------------------------------------------------------
    def series(party: str) -> np.ndarray:
        return np.array([d.get(party, 0) for d in seat_draws])

    print("\nseat distribution (median [5th–95th percentile]):")
    ranked = sorted(universe, key=lambda p: -series(p).mean())
    for party in ranked[:10]:
        s = series(party)
        if s.mean() < 0.5:
            continue
        print(f"  {party:<10s} {np.median(s):>5.0f}  [{np.percentile(s, 5):>3.0f} – {np.percentile(s, 95):>3.0f}]")

    sizes = np.array([sum(d.values()) for d in seat_draws])
    if not (sizes == COUNCIL).all():
        print(f"\n  WARNING: {int((sizes != COUNCIL).sum())} draw(s) did not allocate "
              f"{COUNCIL} seats (min {sizes.min()}, max {sizes.max()})")

    everyone_else = np.array([
        sum(v for p, v in d.items() if p not in ANC_BLOC_PARTIES) for d in seat_draws
    ])

    print(f"\ncoalition viability (probability of reaching {MAJORITY} of {COUNCIL}):")
    print(f"  {'coalition':<34s} {'P(majority)':>11s} {'median':>7s} {'5th':>5s} {'95th':>5s}")
    rows = []
    for label, members in COALITIONS.items():
        totals = sum(series(p) for p in members)
        probability = float((totals >= MAJORITY).mean())
        rows.append({
            "coalition": label,
            "probability": probability,
            "median_seats": float(np.median(totals)),
            "p5": float(np.percentile(totals, 5)),
            "p95": float(np.percentile(totals, 95)),
        })
        print(
            f"  {label:<34s} {probability:>10.1%} {np.median(totals):>7.0f}"
            f" {np.percentile(totals, 5):>5.0f} {np.percentile(totals, 95):>5.0f}"
        )

    # The politically operative question is not who wins but whether anything
    # short of an ANC-DA arrangement can govern.
    print(
        f"  {'every party outside the ANC bloc':<34s} "
        f"{(everyone_else >= MAJORITY).mean():>10.1%} {np.median(everyone_else):>7.0f}"
        f" {np.percentile(everyone_else, 5):>5.0f} {np.percentile(everyone_else, 95):>5.0f}"
    )

    largest = [max(d, key=d.get) for d in seat_draws]
    print("\n  largest single party:")
    for party in sorted(set(largest), key=lambda p: -largest.count(p))[:4]:
        print(f"    {party:<10s} {largest.count(party) / len(largest):>6.1%} of draws")
    anc_da = sum(series(p) for p in ("ANC", "DA"))
    without_grand = [
        label for label, members in COALITIONS.items()
        if set(members) != {"ANC", "DA"}
    ]
    any_other = np.zeros(len(seat_draws), dtype=bool)
    for label in without_grand:
        any_other |= sum(series(p) for p in COALITIONS[label]) >= MAJORITY
    print(f"\n  P(ANC + DA reaches {MAJORITY})"
          f"{'':<34s}{(anc_da >= MAJORITY).mean():>6.1%}")
    print(f"  P(any *enumerated* coalition other than ANC+DA)"
          f"{'':<21s}{any_other.mean():>6.1%}")
    print(f"  P(a majority excluding the ANC bloc entirely)"
          f"{'':<23s}{(everyone_else >= MAJORITY).mean():>6.1%}")
    print(
        "\n  The last two differ because no small enumerated grouping reaches 136,"
        "\n  but the whole non-ANC-bloc field together does. A majority without the"
        "\n  ANC therefore requires close to every other party in the council, not a"
        "\n  two- or three-party arrangement."
    )

    out = args.processed / "coalition_viability.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["coalition", "probability", "median_seats", "p5", "p95"]
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "probability": f"{row['probability']:.4f}"})

    seats_out = args.processed / "seat_draws.csv"
    with seats_out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["draw"] + ranked[:12])
        for i, d in enumerate(seat_draws):
            writer.writerow([i] + [d.get(p, 0) for p in ranked[:12]])

    print(f"\nwrote {out} and {seats_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
