"""VD-level turnout series and the λ drop-off factors (plan §3.3).

Local elections draw far fewer voters than the national/provincial elections
that precede them. λ is that drop-off, measured per voting district:

    λ_2016(i) = T_2016(i) / T_2014(i)
    λ_2021(i) = T_2021(i) / T_2019(i)
    λ̂(i)      = w_recency · λ_2021(i) + (1 − w_recency) · λ_2016(i)
    T_2026(i) = T_2024(i) · λ̂(i)

Assumption A3 is that the *relative* pattern across VDs is stable even though
the absolute level is not — if Sandton dropped off less than Ivory Park in both
2016 and 2021, it will again in 2026. This module does not assume that, it
measures it: the correlation between λ_2016 and λ_2021 across VDs is reported,
and it is the number that says whether A3 holds.

**Turnout definition.** The IEC computes turnout as the higher of the ward or PR
ballot's votes cast, over registered voters plus MEC7 (election-day
registrations). MEC7 is not published per VD, so turnout here is votes cast over
registered voters alone, taking the higher ballot at an LGE. That runs slightly
below the IEC's published figure — 42.14% against 42.61% for CoJ in 2021 — and
the gap is the MEC7 denominator. Consistency across elections matters more than
matching the headline, since λ is a ratio and a consistent bias largely divides
out.

Usage:
    python src/turnout.py [--w-recency 0.70]
"""

from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

# election -> (filename, is an LGE with two ballots)
ELECTIONS = {
    "2011": ("lge2011_JHB_vd_party_clean.csv", True),
    "2014": ("npe2014_JHB_vd_party.csv", False),
    "2016": ("lge2016_JHB_vd_party_clean.csv", True),
    "2019": ("npe2019_JHB_vd_party.csv", False),
    "2021": ("lge2021_JHB_vd_party_clean.csv", True),
    "2024": ("npe2024_JHB_vd_party.csv", False),
}

# The λ pairs: each LGE against the national election that preceded it.
LAMBDA_PAIRS = {"2016": ("2014", "2016"), "2021": ("2019", "2021")}


def read_turnout(path: Path, two_ballot: bool) -> dict[str, tuple[int, int]]:
    """Return VD -> (registered, votes cast).

    Votes cast is valid plus spoilt. At an LGE a voter casts both a ward and a PR
    ballot, so the two are counted separately and the higher taken, matching how
    the IEC reports turnout.
    """
    registered: dict[str, int] = {}
    valid: defaultdict[tuple[str, str], int] = defaultdict(int)
    spoilt: dict[tuple[str, str], int] = {}

    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            vd = row["VD_Number"]
            ballot = row.get("BallotType", "") if two_ballot else ""
            registered.setdefault(vd, int(row["Registered_Population"]))
            spoilt.setdefault((vd, ballot), int(row["Spoilt_Votes"]))
            valid[(vd, ballot)] += int(row["Party_Votes"])

    cast: defaultdict[str, int] = defaultdict(int)
    for (vd, ballot), votes in valid.items():
        cast[vd] = max(cast[vd], votes + spoilt.get((vd, ballot), 0))
    return {vd: (registered[vd], cast[vd]) for vd in registered}


def turnout_series(data_dir: Path) -> dict[str, dict[str, float]]:
    """Return election -> VD -> turnout, plus the citywide figure per election.

    Turnout above 1.05 is treated as a registration mismatch, not a
    measurement — e.g. VD 32851278-adjacent 32840018 shows 245% in 2019,
    which poisons its λ and projected a 9.9% 2026 turnout before this guard.
    Such VD-years are dropped; downstream blends fall back to the other cycle
    or the citywide mean.
    """
    series: dict[str, dict[str, float]] = {}
    for year, (filename, two_ballot) in ELECTIONS.items():
        counts = read_turnout(data_dir / filename, two_ballot)
        dropped = [vd for vd, (r, c) in counts.items() if r > 0 and c / r > 1.05]
        if dropped:
            print(f"  ! {year}: dropped {len(dropped)} VD(s) with turnout > 105% "
                  f"(registration mismatch): {', '.join(dropped[:5])}")
        series[year] = {
            vd: cast / registered
            for vd, (registered, cast) in counts.items()
            if registered > 0 and cast / registered <= 1.05
        }
        series[f"_counts_{year}"] = counts  # type: ignore[assignment]
    return series


def citywide(counts: dict[str, tuple[int, int]]) -> float:
    registered = sum(r for r, _ in counts.values())
    cast = sum(c for _, c in counts.values())
    return cast / registered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    parser.add_argument("--out", type=Path, default=Path("data/processed/turnout.csv"))
    parser.add_argument(
        "--w-recency",
        type=float,
        default=0.70,
        help="weight on 2021's drop-off vs 2016's (plan §3.5, range 0.50-0.90)",
    )
    parser.add_argument(
        "--kappa-bye",
        type=float,
        default=0.25,
        help="damping on the §3.3 by-election turnout covariate (0 disables). "
             "For VDs in a ward that held a by-election, λ̂ is tilted by the "
             "ward's by-election/2021 turnout ratio relative to the citywide "
             "median of that ratio — the only pre-election measure of "
             "differential enthusiasm. Weighted modestly per the plan: it "
             "shares assumption A4's selection bias.",
    )
    args = parser.parse_args(argv)

    series = turnout_series(args.data_dir)

    print("citywide turnout (votes cast / registered, higher ballot at an LGE):")
    for year in ELECTIONS:
        counts = series[f"_counts_{year}"]  # type: ignore[index]
        registered = sum(r for r, _ in counts.values())
        print(f"  {year}  {citywide(counts):>7.2%}   {len(counts):>3d} VDs, {registered:>9,} registered")

    # --- λ per VD ------------------------------------------------------------
    lambdas: dict[str, dict[str, float]] = {}
    for label, (before, after) in LAMBDA_PAIRS.items():
        common = set(series[before]) & set(series[after])
        lambdas[label] = {
            vd: series[after][vd] / series[before][vd]
            for vd in common
            if series[before][vd] > 0.05  # ignore near-empty VDs; ratios explode
        }
        values = sorted(lambdas[label].values())
        print(
            f"\nλ_{label} = T_{after}/T_{before} across {len(values)} VDs:"
            f"  p10 {values[len(values)//10]:.3f}"
            f"  median {statistics.median(values):.3f}"
            f"  p90 {values[9*len(values)//10]:.3f}"
        )

    # Assumption A3: is the relative pattern stable between the two cycles?
    shared = sorted(set(lambdas["2016"]) & set(lambdas["2021"]))
    a, b = [lambdas["2016"][v] for v in shared], [lambdas["2021"][v] for v in shared]
    correlation = statistics.correlation(a, b)
    print(
        f"\nAssumption A3 -- correlation between λ_2016 and λ_2021 across"
        f" {len(shared)} VDs: {correlation:+.3f}"
    )
    print(
        "  A3 bets that VDs which held up in one cycle hold up in the next."
        f"\n  {'Supported' if correlation > 0.3 else 'NOT supported'} at this correlation."
    )

    # --- does the ratio specification actually predict best? -----------------
    # A3 is only worth betting on if λ carries the information. Test it by
    # predicting 2021 VD turnout three ways and scoring against the actuals.
    # This is the turnout sub-model's own miniature backtest, and it is cheap.
    shared21 = [
        vd for vd in series["2021"]
        if vd in series["2019"] and vd in series["2016"] and vd in lambdas["2016"]
    ]
    predictors = {
        "T_2019 x λ_2016  (the plan's ratio form)": lambda vd: series["2019"][vd] * lambdas["2016"][vd],
        "T_2016           (previous LGE level)": lambda vd: series["2016"][vd],
        "T_2019           (preceding NPE level)": lambda vd: series["2019"][vd],
    }
    # Every predictor is rescaled so its registration-weighted citywide turnout
    # equals the actual. Without this the comparison is rigged: the citywide
    # drift predictor is handed the true 2021 total, which is information from
    # the future, while the ratio form has to guess the level from 2016's
    # drop-off. Normalising isolates the question A3 actually asks -- who is
    # right about the *relative* pattern across VDs, given the citywide total.
    registered = {vd: series["_counts_2024"].get(vd, (0, 0))[0] for vd in shared21}  # type: ignore[index]
    actual_citywide = sum(series["2021"][vd] * registered[vd] for vd in shared21) / sum(
        registered.values()
    )

    print("\npredicting 2021 VD turnout, each rescaled to the true citywide total:")
    for label, predict in predictors.items():
        raw = {vd: predict(vd) for vd in shared21}
        mean_raw = sum(raw[vd] * registered[vd] for vd in shared21) / sum(registered.values())
        factor = actual_citywide / mean_raw if mean_raw else 1.0
        errors = [abs(raw[vd] * factor - series["2021"][vd]) for vd in shared21]
        print(
            f"  {label:<48s} MAE {statistics.mean(errors):.4f}"
            f"   (level correction x{factor:.3f})"
        )
    print(
        "  (MAE in turnout points, so 0.0400 is 4 percentage points per VD.)"
        "\n  The level correction shows how far each predictor's own citywide"
        "\n  level was out before rescaling -- the ratio form's is the cost of"
        "\n  assuming 2016's drop-off would repeat in 2021. It did not."
    )

    # The same question one cycle earlier. λ_2011 would need the 2009 NPE, which
    # we do not hold, so the ratio form cannot be tested here -- but the two
    # level predictors can, which is what distinguishes them anyway.
    shared16 = [
        vd for vd in series["2016"] if vd in series["2011"] and vd in series["2014"]
    ]
    reg16 = {vd: series["_counts_2016"].get(vd, (0, 0))[0] for vd in shared16}  # type: ignore[index]
    actual16 = sum(series["2016"][vd] * reg16[vd] for vd in shared16) / sum(reg16.values())
    print("\nthe same test one cycle earlier, predicting 2016 VD turnout:")
    for label, source_year in (("T_2011  (previous LGE level)", "2011"),
                               ("T_2014  (preceding NPE level)", "2014")):
        raw = {vd: series[source_year][vd] for vd in shared16}
        mean_raw = sum(raw[vd] * reg16[vd] for vd in shared16) / sum(reg16.values())
        factor = actual16 / mean_raw if mean_raw else 1.0
        errors = [abs(raw[vd] * factor - series["2016"][vd]) for vd in shared16]
        print(f"  {label:<48s} MAE {statistics.mean(errors):.4f}")

    # --- §3.3 by-election turnout covariate -----------------------------------
    # ward (2021 delimitation) -> most recent contest's turnout ratio vs the
    # citywide median ratio. VD membership comes from the 2021 result file.
    bye_tilt: dict[str, float] = {}
    bye_path = Path("data/processed/byelection_turnout.csv")
    if args.kappa_bye > 0 and bye_path.exists():
        ward_ratio: dict[str, tuple[str, float]] = {}
        with bye_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                ratio = float(row["ratio_vs_median"])
                prior = ward_ratio.get(row["ward"])
                if prior is None or row["date"] > prior[0]:
                    ward_ratio[row["ward"]] = (row["date"], ratio)
        vd_ward_2021: dict[str, str] = {}
        with (args.data_dir / ELECTIONS["2021"][0]).open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                vd_ward_2021.setdefault(row["VD_Number"], row["Ward"])
        for vd, ward in vd_ward_2021.items():
            if ward in ward_ratio:
                bye_tilt[vd] = 1.0 + args.kappa_bye * (ward_ratio[ward][1] - 1.0)
        print(
            f"\n§3.3 by-election turnout covariate: κ={args.kappa_bye}, "
            f"{len(ward_ratio)} wards, {len(bye_tilt)} VDs tilted "
            f"(range ×{min(bye_tilt.values()):.2f}–×{max(bye_tilt.values()):.2f})"
        )

    # --- blended λ̂ and the 2026 projection ------------------------------------
    w = args.w_recency
    rows = []
    projected_cast = projected_reg = 0
    counts2024 = series["_counts_2024"]  # type: ignore[index]
    for vd, (registered, cast) in counts2024.items():
        if vd not in series["2024"]:
            continue  # dropped as implausible above
        l16, l21 = lambdas["2016"].get(vd), lambdas["2021"].get(vd)
        if l16 is None and l21 is None:
            continue
        # Fall back to whichever cycle we have when a VD is missing from one.
        blended = (
            w * l21 + (1 - w) * l16 if l16 is not None and l21 is not None
            else (l21 if l21 is not None else l16)
        )
        t2024 = series["2024"][vd]
        t2026 = min(t2024 * blended * bye_tilt.get(vd, 1.0), 1.0)
        projected_cast += t2026 * registered
        projected_reg += registered
        rows.append(
            {
                "VD_Number": vd,
                "registered_2024": str(registered),
                **{f"turnout_{y}": f"{series[y].get(vd, float('nan')):.5f}" for y in ELECTIONS},
                "lambda_2016": f"{l16:.5f}" if l16 is not None else "",
                "lambda_2021": f"{l21:.5f}" if l21 is not None else "",
                "lambda_hat": f"{blended:.5f}",
                "turnout_2026_projected": f"{t2026:.5f}",
            }
        )

    # A3 (review): the previous-LGE-level pattern won the head-to-head above,
    # so it is emitted alongside the ratio form — same citywide level (from
    # λ̂), different relative pattern. Consumers choose or blend (montecarlo
    # blends per draw; the level cancels in seats, the pattern does not).
    level_projection = projected_cast / projected_reg
    with21 = [(r, float(r[f"turnout_2021"])) for r in rows
              if r["turnout_2021"] != "nan" and not r["turnout_2021"].startswith("na")]
    mean21 = (sum(t * int(r["registered_2024"]) for r, t in with21)
              / sum(int(r["registered_2024"]) for r, t in with21))
    for row in rows:
        t21 = row["turnout_2021"]
        if t21 != "nan" and not t21.startswith("na"):
            level = min(float(t21) * level_projection / mean21, 1.0)
            row["turnout_2026_level"] = f"{level:.5f}"
        else:
            row["turnout_2026_level"] = ""

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    blended_all = sorted(float(r["lambda_hat"]) for r in rows)
    print(
        f"\nλ̂ (w_recency={w}) across {len(rows)} VDs:"
        f"  p10 {blended_all[len(blended_all)//10]:.3f}"
        f"  median {statistics.median(blended_all):.3f}"
        f"  p90 {blended_all[9*len(blended_all)//10]:.3f}"
    )
    print(
        f"\nprojected citywide 2026 turnout: {projected_cast / projected_reg:>7.2%}"
        f"   (plan §8.2 expects roughly 38-42%)"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
