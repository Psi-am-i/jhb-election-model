"""VD-level turnout series and the λ drop-off factors (plan §3.3).

Local elections draw far fewer voters than the national/provincial elections
that precede them. λ is that drop-off, measured per voting district. Writing
R for the two most recent LGEs whose λ can be measured before the target T,
and N(x) for the national election preceding x:

    λ_prior(i)  = T_prior(i) / T_N(prior)(i)
    λ_recent(i) = T_recent(i) / T_N(recent)(i)
    λ̂(i)        = w_recency · λ_recent(i) + (1 − w_recency) · λ_prior(i)
    T_T(i)      = T_N(T)(i) · λ̂(i)

Building 2026 that reads λ_2016, λ_2021 and T_2024, which is what it always
was; the years are now derived from the target rather than written in.

Assumption A3 is that the *relative* pattern across VDs is stable even though
the absolute level is not — if Sandton dropped off less than Ivory Park in both
2016 and 2021, it will again in 2026. This module does not assume that, it
measures it: the correlation between the two λ series across VDs is reported,
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
    python src/turnout.py [--city joburg] [--target 2026] [--w-recency 0.70]
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
import statistics
from collections import defaultdict
from pathlib import Path

# election -> (filename, is an LGE with two ballots), chronological.
# Derived from cityconfig's calendar rather than kept as a second list. That
# unification currently reaches exactly two modules — this one, and fold.py,
# which imports this dict (as TURNOUT_FILES) and so keeps its old shape.
#
# It is NOT yet true of the pipeline. Four other modules still carry their own
# parallel per-election tables of literal {CODE} templates, and adding or
# correcting an election means editing each of them by hand:
#     build_concordance.py   ELECTIONS  (+ its own per-election ballot flags)
#     build_crosswalk.py     ELECTIONS
#     backtest.py            per-vintage base/actual/prior_lge templates
#     benchmarks.py          per-year prior_npe/earlier_lge templates
#     fold.py                per-fold base/target templates, alongside the
#                            TURNOUT_FILES it imports from here
# A further four (build_geo, export_interactive, leverage, montecarlo) hardcode
# individual filenames rather than a table. Do not read this dict as evidence
# that the calendar has one home; it has one home for two modules.
#
# An election not yet held has no result file and is not in here.
#
# Sorted, not left to CALENDAR's insertion order: main() takes the *last* two
# measurable λ pairs as "the two most recent cycles" and writes the turnout_*
# columns in this order, so chronology here is load-bearing rather than
# cosmetic. Four-digit year strings sort lexicographically into chronology.
ELECTIONS = {
    year: (e.results, e.two_ballot)
    for year, e in sorted(cityconfig.CALENDAR.items()) if e.results
}

# The λ pairs: each LGE against the national election that preceded it, keyed
# by the LGE year. Sorted for the same reason ELECTIONS is.
LAMBDA_PAIRS = {
    year: (cityconfig.preceding(year, "NPE"), year)
    for year, e in sorted(cityconfig.CALENDAR.items())
    if e.kind == "LGE" and e.results and cityconfig.preceding(year, "NPE")
}


def read_turnout(path: Path, two_ballot: bool) -> dict[str, tuple[int, int]]:
    """Return VD -> (registered, votes cast).

    Votes cast is valid plus spoilt. At an LGE a voter casts both a ward and a PR
    ballot, so the two are counted separately and the higher taken, matching how
    the IEC reports turnout.
    """
    registered: dict[str, int] = {}
    valid: defaultdict[tuple[str, str], int] = defaultdict(int)
    spoilt: dict[tuple[str, str], int] = {}

    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as handle:
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


def turnout_series(data_dir: Path,
                   years: list[str] | None = None) -> dict[str, dict[str, float]]:
    """Return election -> VD -> turnout, plus the citywide figure per election.

    Turnout above 1.05 is treated as a registration mismatch, not a
    measurement — e.g. VD 32851278-adjacent 32840018 shows 245% in 2019,
    which poisons its λ and projected a 9.9% 2026 turnout before this guard.
    Such VD-years are dropped; downstream blends fall back to the other cycle
    or the citywide mean.

    Not every city holds every election in ELECTIONS: the pre-2011 archives
    were only ingested for Johannesburg. A missing file is a gap in the record
    rather than an error, so the election is skipped and the caller works from
    whichever years came back — see ``years`` in main().

    `years` restricts which elections are read at all. main() passes the ones
    strictly before the target, so an election after it is never even opened,
    let alone folded into a projection that claims not to have seen it.
    """
    series: dict[str, dict[str, float]] = {}
    wanted = ELECTIONS if years is None else {
        y: ELECTIONS[y] for y in years if y in ELECTIONS}
    for year, (filename, two_ballot) in wanted.items():
        path = cityconfig.resolve_path(data_dir / filename)
        if not path.exists():
            print(f"  ! {year}: no file for {cityconfig.active().name} "
                  f"({path.name}) — election skipped")
            continue
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
    # Defaults to the ACTIVE CITY's processed directory, resolved after
    # --city is parsed. It used to default to data/processed/turnout.csv
    # whatever --city said, so a Tshwane run overwrote Johannesburg's
    # published turnout file -- which montecarlo.py then read.
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--w-recency",
        type=float,
        default=0.70,
        help="weight on the most recent measurable drop-off vs the one before "
             "it (plan §3.5, range 0.50-0.90)",
    )
    parser.add_argument(
        "--kappa-bye",
        type=float,
        default=0.25,
        help="damping on the §3.3 by-election turnout covariate (0 disables). "
             "For VDs in a ward that held a by-election, λ̂ is tilted by the "
             "ward's by-election/previous-LGE turnout ratio relative to the "
             "citywide median of that ratio — the only pre-election measure of "
             "differential enthusiasm. Weighted modestly per the plan: it "
             "shares assumption A4's selection bias.",
    )
    cityconfig.add_city_argument(parser)
    cityconfig.add_target_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))
    target = cityconfig.use_target(getattr(args, "target", None))

    if args.out is None:
        args.out = target.processed / "turnout.csv"

    # The elections this city actually holds AND the target is allowed to see,
    # in calendar order. Everything below iterates this rather than ELECTIONS,
    # so a city whose archive starts late reports on what it has instead of
    # failing on what it does not, and a backtest never touches its own future.
    series = turnout_series(args.data_dir, list(target.before))
    years = [year for year in ELECTIONS if year in series]

    print(f"{cityconfig.active().name} → {target.year} "
          f"({target.date}), from {len(years)} earlier elections")
    print("citywide turnout (votes cast / registered, higher ballot at an LGE):")
    for year in years:
        counts = series[f"_counts_{year}"]  # type: ignore[index]
        registered = sum(r for r, _ in counts.values())
        print(f"  {year}  {citywide(counts):>7.2%}   {len(counts):>3d} VDs, {registered:>9,} registered")

    # --- λ per VD ------------------------------------------------------------
    lambdas: dict[str, dict[str, float]] = {}
    for label, (before, after) in LAMBDA_PAIRS.items():
        if label not in target.before:
            continue  # an LGE at or after the target is not evidence for it
        # λ needs both endpoints. A pair straddling the start of this city's
        # archive simply cannot be measured, and an unmeasurable λ is silence,
        # not a zero — the blend below falls back to the cycle it does have.
        if before not in series or after not in series:
            print(f"\nλ_{label} = T_{after}/T_{before}: not measurable for "
                  f"{cityconfig.active().name} (missing "
                  f"{', '.join(y for y in (before, after) if y not in series)})")
            continue
        common = set(series[before]) & set(series[after])
        lambdas[label] = {
            vd: series[after][vd] / series[before][vd]
            for vd in common
            if series[before][vd] > 0.05  # ignore near-empty VDs; ratios explode
        }
        values = sorted(lambdas[label].values())
        if not values:
            print(f"\nλ_{label} = T_{after}/T_{before}: no VD measurable in both")
            del lambdas[label]  # an empty λ is unmeasured, not measured as zero
            continue
        print(
            f"\nλ_{label} = T_{after}/T_{before} across {len(values)} VDs:"
            f"  p10 {values[len(values)//10]:.3f}"
            f"  median {statistics.median(values):.3f}"
            f"  p90 {values[9*len(values)//10]:.3f}"
        )

    # The two most recent measurable drop-offs, oldest first. Which years those
    # are is a fact about the target and about what this city's archive
    # actually holds, not a constant: building CoJ 2026 they come out as 2016
    # and 2021, which is what used to be written in.
    measured = [label for label in LAMBDA_PAIRS if label in lambdas]
    lam_recent = measured[-1] if measured else None
    lam_prior = measured[-2] if len(measured) > 1 else None
    if lam_recent is None:
        raise SystemExit(
            f"no λ measurable before {target.year} for {cityconfig.active().name}: "
            f"an LGE and the NPE before it must both be on disk")

    # The level λ̂ is applied to, and the LGE supplying the ward delimitation
    # and the alternative (level) turnout pattern.
    base_npe = target.previous_npe
    prev_lge = target.previous_lge
    if base_npe is None or base_npe not in series:
        raise SystemExit(
            f"no national election on disk before {target.year} for "
            f"{cityconfig.active().name}; there is no level to project from")

    # Assumption A3: is the relative pattern stable between the two cycles?
    if lam_prior is None:
        print(f"\nAssumption A3 -- not testable: only λ_{lam_recent} is "
              f"measurable, so there is no second cycle to correlate it with.")
    else:
        shared = sorted(set(lambdas[lam_prior]) & set(lambdas[lam_recent]))
        a = [lambdas[lam_prior][v] for v in shared]
        b = [lambdas[lam_recent][v] for v in shared]
        correlation = statistics.correlation(a, b)
        print(
            f"\nAssumption A3 -- correlation between λ_{lam_prior} and "
            f"λ_{lam_recent} across {len(shared)} VDs: {correlation:+.3f}"
        )
        print(
            "  A3 bets that VDs which held up in one cycle hold up in the next."
            f"\n  {'Supported' if correlation > 0.3 else 'NOT supported'} at this correlation."
        )

    # --- does the ratio specification actually predict best? -----------------
    # A3 is only worth betting on if λ carries the information. Test it by
    # predicting the most recent LGE's VD turnout three ways and scoring
    # against the actuals. This is the turnout sub-model's own miniature
    # backtest, and it is cheap. It needs the cycle before the one it is
    # predicting, so it is silent when only one λ was measurable.
    npe_before_recent = cityconfig.preceding(lam_recent, "NPE")
    if lam_prior is not None and lam_prior in series and npe_before_recent in series:
        shared21 = [
            vd for vd in series[lam_recent]
            if vd in series[npe_before_recent] and vd in series[lam_prior]
            and vd in lambdas[lam_prior]
        ]
        predictors = {
            f"T_{npe_before_recent} x λ_{lam_prior}  (the plan's ratio form)":
                lambda vd: series[npe_before_recent][vd] * lambdas[lam_prior][vd],
            f"T_{lam_prior}           (previous LGE level)":
                lambda vd: series[lam_prior][vd],
            f"T_{npe_before_recent}           (preceding NPE level)":
                lambda vd: series[npe_before_recent][vd],
        }
        # Every predictor is rescaled so its registration-weighted citywide
        # turnout equals the actual. Without this the comparison is rigged: the
        # citywide drift predictor is handed the true total, which is
        # information from the future, while the ratio form has to guess the
        # level from the previous cycle's drop-off. Normalising isolates the
        # question A3 actually asks -- who is right about the *relative*
        # pattern across VDs, given the citywide total.
        registered = {vd: series[f"_counts_{base_npe}"].get(vd, (0, 0))[0]  # type: ignore[index]
                      for vd in shared21}
        actual_citywide = sum(
            series[lam_recent][vd] * registered[vd] for vd in shared21
        ) / sum(registered.values())

        print(f"\npredicting {lam_recent} VD turnout, each rescaled to the "
              f"true citywide total:")
        for label, predict in predictors.items():
            raw = {vd: predict(vd) for vd in shared21}
            mean_raw = sum(raw[vd] * registered[vd] for vd in shared21) / sum(registered.values())
            factor = actual_citywide / mean_raw if mean_raw else 1.0
            errors = [abs(raw[vd] * factor - series[lam_recent][vd]) for vd in shared21]
            print(
                f"  {label:<48s} MAE {statistics.mean(errors):.4f}"
                f"   (level correction x{factor:.3f})"
            )
        print(
            "  (MAE in turnout points, so 0.0400 is 4 percentage points per VD.)"
            "\n  The level correction shows how far each predictor's own citywide"
            "\n  level was out before rescaling -- the ratio form's is the cost of"
            f"\n  assuming {lam_prior}'s drop-off would repeat in {lam_recent}."
        )

        # The same question one cycle earlier. The ratio form needs the NPE
        # before that LGE, which the archive may not reach back to -- but the
        # two level predictors can still run, and they are what distinguishes
        # the two candidate patterns anyway.
        lge_before_prior = cityconfig.preceding(lam_prior, "LGE")
        npe_before_prior = cityconfig.preceding(lam_prior, "NPE")
        if lge_before_prior in series and npe_before_prior in series:
            shared16 = [
                vd for vd in series[lam_prior]
                if vd in series[lge_before_prior] and vd in series[npe_before_prior]
            ]
            reg16 = {vd: series[f"_counts_{lam_prior}"].get(vd, (0, 0))[0]  # type: ignore[index]
                     for vd in shared16}
            actual16 = sum(series[lam_prior][vd] * reg16[vd] for vd in shared16) / sum(reg16.values())
            print(f"\nthe same test one cycle earlier, predicting {lam_prior} VD turnout:")
            for label, source_year in (
                    (f"T_{lge_before_prior}  (previous LGE level)", lge_before_prior),
                    (f"T_{npe_before_prior}  (preceding NPE level)", npe_before_prior)):
                raw = {vd: series[source_year][vd] for vd in shared16}
                mean_raw = sum(raw[vd] * reg16[vd] for vd in shared16) / sum(reg16.values())
                factor = actual16 / mean_raw if mean_raw else 1.0
                errors = [abs(raw[vd] * factor - series[lam_prior][vd]) for vd in shared16]
                print(f"  {label:<48s} MAE {statistics.mean(errors):.4f}")

    # --- §3.3 by-election turnout covariate -----------------------------------
    # ward (previous-LGE delimitation) -> most recent contest's turnout ratio
    # vs the citywide median ratio. VD membership comes from that LGE's file.
    bye_tilt: dict[str, float] = {}
    # Per-city and per-target: the hardcoded path handed Tshwane Johannesburg's
    # by-elections. Ward IDs do not collide across metros so nothing was
    # mis-tilted, but the match rate was zero for a reason that looked like "no
    # by-elections held". Johannesburg's 2026 keeps the legacy path.
    bye_path = target.processed / "byelection_turnout.csv"
    if args.kappa_bye > 0 and prev_lge in series and bye_path.exists():
        ward_ratio: dict[str, tuple[str, float]] = {}
        with bye_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                ratio = float(row["ratio_vs_median"])
                seen = ward_ratio.get(row["ward"])
                if seen is None or row["date"] > seen[0]:
                    ward_ratio[row["ward"]] = (row["date"], ratio)
        vd_ward: dict[str, str] = {}
        _plge = cityconfig.resolve_path(args.data_dir / ELECTIONS[prev_lge][0])
        with _plge.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                vd_ward.setdefault(row["VD_Number"], row["Ward"])
        for vd, ward in vd_ward.items():
            if ward in ward_ratio:
                bye_tilt[vd] = 1.0 + args.kappa_bye * (ward_ratio[ward][1] - 1.0)
        # No overlap means no tilt at all, which is a reportable state rather
        # than a range over an empty set.
        span = (f"(range ×{min(bye_tilt.values()):.2f}–×{max(bye_tilt.values()):.2f})"
                if bye_tilt else f"(no ward matched a {prev_lge} VD; no tilt applied)")
        print(
            f"\n§3.3 by-election turnout covariate: κ={args.kappa_bye}, "
            f"{len(ward_ratio)} wards, {len(bye_tilt)} VDs tilted {span}"
        )

    # --- blended λ̂ and the projection ----------------------------------------
    w = args.w_recency
    rows = []
    projected_cast = projected_reg = 0
    counts_base = series[f"_counts_{base_npe}"]  # type: ignore[index]
    for vd, (registered, cast) in counts_base.items():
        if vd not in series[base_npe]:
            continue  # dropped as implausible above
        l_prior = lambdas[lam_prior].get(vd) if lam_prior else None
        l_recent = lambdas[lam_recent].get(vd)
        if l_prior is None and l_recent is None:
            continue
        # Fall back to whichever cycle we have when a VD is missing from one.
        blended = (
            w * l_recent + (1 - w) * l_prior
            if l_prior is not None and l_recent is not None
            else (l_recent if l_recent is not None else l_prior)
        )
        t_base = series[base_npe][vd]
        t_target = min(t_base * blended * bye_tilt.get(vd, 1.0), 1.0)
        projected_cast += t_target * registered
        projected_reg += registered
        lam_cols = {}
        if lam_prior:
            lam_cols[f"lambda_{lam_prior}"] = f"{l_prior:.5f}" if l_prior is not None else ""
        lam_cols[f"lambda_{lam_recent}"] = f"{l_recent:.5f}" if l_recent is not None else ""
        rows.append(
            {
                "VD_Number": vd,
                f"registered_{base_npe}": str(registered),
                **{f"turnout_{y}": f"{series[y].get(vd, float('nan')):.5f}" for y in years},
                **lam_cols,
                "lambda_hat": f"{blended:.5f}",
                f"turnout_{target.year}_projected": f"{t_target:.5f}",
            }
        )

    # A3 (review): the previous-LGE-level pattern won the head-to-head above,
    # so it is emitted alongside the ratio form — same citywide level (from
    # λ̂), different relative pattern. Consumers choose or blend (montecarlo
    # blends per draw; the level cancels in seats, the pattern does not).
    # It needs the previous LGE's own turnout, so it is omitted outright when
    # that election is not in this city's archive.
    level_projection = projected_cast / projected_reg
    prev_col = f"turnout_{prev_lge}"

    def _measured(row) -> bool:
        value = row[prev_col]
        return value != "nan" and not value.startswith("na")

    if prev_lge in years:
        base_rows = [(r, float(r[prev_col])) for r in rows if _measured(r)]
        reg_col = f"registered_{base_npe}"
        mean_prev = (sum(t * int(r[reg_col]) for r, t in base_rows)
                     / sum(int(r[reg_col]) for r, t in base_rows))
        for row in rows:
            if _measured(row):
                level = min(float(row[prev_col]) * level_projection / mean_prev, 1.0)
                row[f"turnout_{target.year}_level"] = f"{level:.5f}"
            else:
                row[f"turnout_{target.year}_level"] = ""
    else:
        print(f"\n! no {prev_lge} turnout for {cityconfig.active().name}: the "
              f"level pattern column is omitted, leaving only the ratio form.")

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
        f"\nprojected citywide {target.year} turnout: "
        f"{projected_cast / projected_reg:>7.2%}"
        f"   (plan §8.2 expects roughly 38-42%)"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
