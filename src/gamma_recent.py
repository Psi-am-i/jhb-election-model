"""Fit γ on the last LGE→NPE transition for parties fold 1 never saw (review A4).

γ — how much of a party's local deviation from its citywide mean persists —
is fitted on fold 1 (2014→2016) and transfers across cycles (MODEL-LOG 1.7).
But a party absent in 2014/2016 gets no fit and previously defaulted to
γ = 1.0, full preservation of its 2024 geography. That default landed on
exactly the parties whose geography is least settled: ActionSA (first contest
2021), the PA (negligible before 2021), MK (first contest 2024).

This script fits γ where one more transition exists: the last completed LGE
PR → NPE pair strictly before the target (2021→2024 when building 2026).
The direction is reversed relative to the folds (LGE→NPE rather than NPE→LGE).
⚠️ That is NOT symmetric: a regression of y on x is attenuated differently from
x on y, so the fitted coefficient measures how much LGE geography flattens
into an NPE, while the model applies it in the opposite direction. Under the
alternative reading (2026 geography resembles 2021's), the right coefficient
is roughly the reciprocal — a real sensitivity, flagged by the 2026-08-05
blind audit, carried as a documented judgement until fold-tested. MK cannot be fitted at all
(one election); it keeps the explicit default, now a documented judgement
rather than a silent fallback.

Output: gamma_recent.csv under the target's processed directory, consumed by
montecarlo.py for any party without a fold-1 γ.

Usage:
    python src/gamma_recent.py [--city joburg] [--target 2026]
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
from pathlib import Path

from fold import citywide, fit_gamma, load, shares

# Fit only parties that meaningfully contested both elections.
MIN_SHARE = 0.005


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    # Defaults to the ACTIVE TARGET's processed directory, resolved after
    # --city/--target are parsed. A fixed data/processed/gamma_recent.csv
    # default meant every city and every target wrote over Johannesburg 2026's.
    parser.add_argument("--out", type=Path, default=None)
    cityconfig.add_city_argument(parser)
    cityconfig.add_target_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))
    target = cityconfig.use_target(getattr(args, "target", None))
    if args.out is None:
        args.out = target.processed / "gamma_recent.csv"

    # The freshest completed transition the target is allowed to see: the last
    # LGE before it, against the last NPE before it. The NPE must come after
    # the LGE or this is not a transition at all — which is the case for any
    # target whose preceding NPE predates its preceding LGE.
    base_year, target_year = target.previous_lge, target.previous_npe
    if base_year is None or target_year is None or target_year < base_year:
        raise SystemExit(
            f"no completed LGE→NPE transition before {target.year} "
            f"(last LGE {base_year}, last NPE {target_year}); γ_recent cannot "
            f"be fitted for this target")

    base_votes, _ = load(args.data_dir / target.results(base_year), "PR")
    target_votes, _ = load(args.data_dir / target.results(target_year), None)

    base_share, base_city = shares(base_votes), citywide(base_votes)
    target_share, target_city = shares(target_votes), citywide(target_votes)
    weights = {vd: sum(counts.values()) for vd, counts in base_votes.items()}

    rows = []
    print(f"γ fitted on {base_year} LGE (PR) → {target_year} NPE, per party:")
    print(f"  {'party':<10s} {base_year:>7s} {target_year:>7s} {'γ':>6s} {'VDs':>5s}")
    for party in sorted(base_city, key=lambda p: -base_city[p]):
        if base_city.get(party, 0) < MIN_SHARE or target_city.get(party, 0) < MIN_SHARE:
            continue
        gamma, n = fit_gamma(base_share, target_share, base_city, target_city,
                             weights, party)
        rows.append({"party": party, "gamma": f"{gamma:.4f}",
                     f"share_{base_year}": f"{base_city[party]:.4f}",
                     f"share_{target_year}": f"{target_city[party]:.4f}", "n_vd": n})
        print(f"  {party:<10s} {base_city[party]:>7.2%} {target_city[party]:>7.2%}"
              f" {gamma:>6.2f} {n:>5d}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["party", "gamma", f"share_{base_year}",
                                f"share_{target_year}", "n_vd"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
