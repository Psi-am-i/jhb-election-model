"""Coalition arithmetic over Monte Carlo seat draws (plan §3.8).

The original build checked six hand-picked coalitions, which is exactly what
§3.8 warned against ("there is no reason to pre-filter on plausibility, and
good reason not to") — and it produced a false published conclusion: DA+EFF+MK
reaches a majority in ~61% of draws but was never checked (review E1). This
module does what §3.8 actually specified:

* **Full enumeration.** Every subset of seat-holding parties, every draw.
* **Minimal winning coalitions.** Winning subsets where every member is
  necessary. These, not all winners, are the set of deals in which every
  partner has leverage.
* **Power indices.** Banzhaf (share of winning coalitions a party is pivotal
  in) and Shapley–Shubik (pivotality weighted by ordering), reported as
  distributions across draws — a party can be marginal at the median and
  kingmaker in the tail, which is the entire point of computing them.
* **The minority-government class.** The mayor is elected by councillors
  *present and voting*, so abstention installs minority administrations —
  as it did in Johannesburg after 2021. Arithmetic viability of a candidate
  party against a declared set of active opponents is reported alongside
  majority coalitions, with the opposition sets kept as editable scenarios
  (annotate, never filter — declared red lines have a short half-life).

Everything is vectorised over draws with bitmask subset enumeration; with a
dozen seat-holding parties this is 4,096 subsets and runs in seconds.

Usage (post-hoc over a saved run):
    python src/coalitions.py [--draws-file data/processed/seat_draws.csv]
"""

from __future__ import annotations

import argparse
import csv
from itertools import combinations
from math import factorial
from pathlib import Path

import numpy as np


def subset_totals(seats: np.ndarray) -> np.ndarray:
    """Seat totals for every subset. seats: (draws, n) -> (2**n, draws).

    Dynamic programme over bitmasks: each mask adds one party to a smaller
    mask, so the whole table costs one vector add per subset.
    """
    draws, n = seats.shape
    totals = np.zeros((1 << n, draws), dtype=np.int16)
    for mask in range(1, 1 << n):
        low = mask & -mask
        totals[mask] = totals[mask ^ low] + seats[:, low.bit_length() - 1]
    return totals


def minimal_winning(
    totals: np.ndarray, threshold: np.ndarray, n: int
) -> dict[int, np.ndarray]:
    """Mask -> boolean per draw: is this subset a *minimal* winning coalition.

    threshold is per-draw (overhang moves the majority line off 136).
    """
    win = totals >= threshold[None, :]
    out: dict[int, np.ndarray] = {}
    for mask in range(1, len(totals)):
        minimal = win[mask].copy()
        if not minimal.any():
            continue
        members = mask
        while members:
            low = members & -members
            np.logical_and(minimal, ~win[mask ^ low], out=minimal)
            if not minimal.any():
                break
            members ^= low
        if minimal.any():
            out[mask] = minimal
    return out


def banzhaf(win: np.ndarray, n: int) -> np.ndarray:
    """Banzhaf index per party per draw, normalised to sum to 1.

    win: (2**n, draws) boolean. A party is pivotal for subset S (not containing
    it) when S∪{p} wins and S does not.
    """
    draws = win.shape[1]
    swings = np.zeros((n, draws), dtype=np.int32)
    for p in range(n):
        bit = 1 << p
        for mask in range(1 << n):
            if mask & bit:
                continue
            swings[p] += win[mask | bit] & ~win[mask]
    total = swings.sum(axis=0)
    total[total == 0] = 1
    return swings / total


def shapley_shubik(win: np.ndarray, n: int) -> np.ndarray:
    """Shapley–Shubik index per party per draw.

    Same swings as Banzhaf, weighted |S|!(n−|S|−1)!/n! — the probability the
    party is the one that tips a coalition assembled in random order, a better
    proxy for bargaining sequence.
    """
    draws = win.shape[1]
    weight = [factorial(s) * factorial(n - s - 1) / factorial(n) for s in range(n)]
    index = np.zeros((n, draws))
    popcount = np.array([bin(m).count("1") for m in range(1 << n)])
    for p in range(n):
        bit = 1 << p
        for mask in range(1 << n):
            if mask & bit:
                continue
            index[p] += weight[popcount[mask]] * (win[mask | bit] & ~win[mask])
    return index


def minority_viable(
    seats: dict[str, np.ndarray], candidate: str, opposed: tuple[str, ...]
) -> np.ndarray:
    """Arithmetic viability of a minority administration, per draw.

    The mayor needs more votes than the parties that actively vote against —
    everyone else abstaining. This is arithmetic only; whether a party would
    in fact abstain is a political annotation, deliberately not modelled.
    """
    against = sum(seats[p] for p in opposed if p in seats)
    return seats[candidate] > against


def mask_label(mask: int, parties: list[str]) -> str:
    return " + ".join(parties[i] for i in range(len(parties)) if mask & (1 << i))


def analyse(
    seats_by_party: dict[str, np.ndarray],
    threshold: np.ndarray,
    max_parties: int = 12,
) -> dict:
    """Run the full §3.8 suite. Returns a dict of result tables."""
    ranked = sorted(seats_by_party, key=lambda p: -seats_by_party[p].mean())[:max_parties]
    seats = np.stack([seats_by_party[p] for p in ranked], axis=1)
    n = len(ranked)
    draws = seats.shape[0]

    totals = subset_totals(seats)
    win = totals >= threshold[None, :]

    # --- every pair and triple, plus P(majority) for arbitrary subsets -------
    small = []
    for k in (2, 3):
        for combo in combinations(range(n), k):
            mask = sum(1 << i for i in combo)
            p = float(win[mask].mean())
            if p > 0.001:
                small.append({
                    "coalition": mask_label(mask, ranked),
                    "size": k,
                    "probability": p,
                    "median_seats": float(np.median(totals[mask])),
                    "p5": float(np.percentile(totals[mask], 5)),
                    "p95": float(np.percentile(totals[mask], 95)),
                })
    small.sort(key=lambda r: -r["probability"])

    # --- minimal winning coalitions ------------------------------------------
    mwc = minimal_winning(totals, threshold, n)
    mwc_rows = [
        {
            "coalition": mask_label(mask, ranked),
            "size": bin(mask).count("1"),
            "p_mwc": float(flags.mean()),
            "median_seats": float(np.median(totals[mask][flags])) if flags.any() else 0.0,
        }
        for mask, flags in mwc.items()
        if flags.mean() > 0.01
    ]
    mwc_rows.sort(key=lambda r: -r["p_mwc"])

    # --- power indices --------------------------------------------------------
    bz = banzhaf(win, n)
    ss = shapley_shubik(win, n)
    power_rows = [
        {
            "party": ranked[i],
            "banzhaf_median": float(np.median(bz[i])),
            "banzhaf_p5": float(np.percentile(bz[i], 5)),
            "banzhaf_p95": float(np.percentile(bz[i], 95)),
            "shapley_median": float(np.median(ss[i])),
            "shapley_p5": float(np.percentile(ss[i], 5)),
            "shapley_p95": float(np.percentile(ss[i], 95)),
        }
        for i in range(n)
    ]
    power_rows.sort(key=lambda r: -r["banzhaf_median"])

    # --- structural probabilities the narrative needs -------------------------
    anc_bloc = [p for p in ("ANC", "EFF", "MK") if p in ranked]
    idx = {p: i for i, p in enumerate(ranked)}
    without_anc = sum(1 << i for p, i in idx.items() if p != "ANC")
    without_bloc = sum(1 << i for p, i in idx.items() if p not in anc_bloc)
    structural = {
        "P(some majority without the ANC)": float(win[without_anc].mean()),
        "P(some majority without ANC, EFF and MK)": float(win[without_bloc].mean()),
        "P(ANC+DA is winning)": float(win[(1 << idx["ANC"]) | (1 << idx["DA"])].mean())
        if "ANC" in idx and "DA" in idx else float("nan"),
    }

    # --- minority-government class (plan §3.8) --------------------------------
    # Editable scenarios: candidate vs the parties assumed to actively vote
    # against, everyone else abstaining. The 2021 precedent is the first row.
    minority_scenarios = [
        ("DA minority, ANC bloc opposes", "DA", ("ANC", "EFF", "MK")),
        ("DA minority, only ANC opposes (2021 pattern)", "DA", ("ANC",)),
        ("ANC minority, only DA opposes", "ANC", ("DA",)),
        ("ANC minority, DA+ASA oppose", "ANC", ("DA", "ASA")),
    ]
    minority_rows = [
        {"scenario": label, "candidate": cand,
         "opposed": "+".join(opp),
         "p_viable": float(minority_viable(seats_by_party, cand, opp).mean())}
        for label, cand, opp in minority_scenarios
        if cand in seats_by_party
    ]

    return {
        "parties": ranked,
        "pairs_triples": small,
        "mwc": mwc_rows,
        "power": power_rows,
        "structural": structural,
        "minority": minority_rows,
    }


def report(results: dict, majority_note: str = "") -> None:
    print(f"\ncoalition arithmetic — full enumeration over "
          f"{len(results['parties'])} parties {majority_note}")

    print("\n  every pair and triple with P(majority) > 5%:")
    print(f"  {'coalition':<30s} {'P':>7s} {'median':>7s} {'5th–95th':>10s}")
    for row in results["pairs_triples"]:
        if row["probability"] < 0.05:
            continue
        print(f"  {row['coalition']:<30s} {row['probability']:>6.1%} "
              f"{row['median_seats']:>7.0f} {row['p5']:>4.0f}–{row['p95']:<4.0f}")

    print("\n  most frequent minimal winning coalitions (every member necessary):")
    for row in results["mwc"][:10]:
        print(f"  {row['coalition']:<40s} MWC in {row['p_mwc']:>6.1%} of draws")

    print("\n  power indices (Banzhaf median [5th–95th] · Shapley–Shubik median):")
    for row in results["power"]:
        if row["banzhaf_p95"] < 0.01:
            continue
        print(f"  {row['party']:<10s} {row['banzhaf_median']:>6.1%} "
              f"[{row['banzhaf_p5']:>5.1%}–{row['banzhaf_p95']:>5.1%}]"
              f"   ·   {row['shapley_median']:>6.1%}")

    print("\n  structural:")
    for label, value in results["structural"].items():
        shown = f"{value:>6.1%}" if value <= 1.0 else f"{value:>6.0f}"
        print(f"  {label:<45s} {shown}")

    print("\n  minority administrations (candidate > active opposition, rest abstain):")
    for row in results["minority"]:
        print(f"  {row['scenario']:<45s} {row['p_viable']:>6.1%}")


def write_outputs(results: dict, processed: Path) -> None:
    for name, key in (("coalition_pairs_triples.csv", "pairs_triples"),
                      ("coalition_mwc.csv", "mwc"),
                      ("coalition_power.csv", "power"),
                      ("coalition_minority.csv", "minority")):
        rows = results[key]
        if not rows:
            continue
        with (processed / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            for row in rows:
                writer.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v)
                                 for k, v in row.items()})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws-file", type=Path,
                        default=Path("data/processed/seat_draws.csv"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)

    with args.draws_file.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    parties = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    seats = {p: np.array([int(r[p]) for r in rows]) for p in parties}
    threshold = (np.array([int(r["threshold"]) for r in rows])
                 if "threshold" in rows[0] else np.full(len(rows), 136))

    results = analyse(seats, threshold)
    print("NOTE: standalone runs compute structural rows over the stored top-13"
          "\nparties only; montecarlo.py corrects them in-process to count every"
          "\nseat-holding party. Prefer forecast_summary.json for those rows.")
    note = ("(per-draw threshold, overhang-adjusted)"
            if "threshold" in rows[0] else "(fixed majority 136)")
    report(results, note)
    write_outputs(results, args.processed)
    print(f"\nwrote coalition_{{pairs_triples,mwc,power,minority}}.csv to {args.processed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
