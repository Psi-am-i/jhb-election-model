"""By-election evidence for the target election (plan §3.6, §3.3 covariate).

This implements the part of the plan the original build skipped (review E4):
the by-elections held between the previous local election and the target are
turned into two quantitative signals rather than narrative colour. Both ends
of that window are enforced in ``load_byelections``: contests after the
target's polling day are hindsight, and contests before the previous LGE were
fought under a different ward delimitation. For a target no later than the
first by-election on record that window is empty, and an empty result is the
honest answer rather than an error.

**Share deltas, not levels (assumption A4).** A by-election's raw share
inherits massive selection bias — contests happen where councillors die,
resign or defect, skewing toward unstable wards. Within-ward *deltas* against
the same ward's previous-LGE ward-ballot result largely difference that out.
Per plan §3.6 each contest is weighted

    weight(j) = exp(−age_months(j) / τ) × √(votes_cast(j)) × ρ(j)

where ρ(j) is the similarity of ward j's party profile to the citywide profile
(1 − total-variation distance on the previous LGE's ward ballot), so a
by-election in a demographically typical ward counts for more than one in an
outlier.

**Turnout ratio (plan §3.3's discarded covariate).** Each contest's turnout
relative to the same ward's previous-LGE turnout, normalised by the citywide
median of that ratio across contests, is a live differential-enthusiasm
signal — the
Ward 99 Linden collapse (24% from 57%) is exactly the suburban-apathy failure
mode nothing else measures before election day.

Caveats carried forward, and why the output is a *tilt* rather than a truth:
by-elections are candidate contests at 18–50% turnout; a party absent from a
contest contributes no delta for it (absence is a nomination decision, not a
collapse); a party with no votes at the previous LGE has its deltas measured
against a zero base and they are therefore genuine new-party evidence, not
swing. The consumer (montecarlo.py) blends these deltas in at weight ``w_bye``
(default 0.4 per §3.5) — they move the centre of the prior, never replace it.

Outputs, under the target's processed directory:
    byelection_party_deltas.csv     weighted per-party share deltas
    byelection_contest_detail.csv   one row per contest and party
    byelection_turnout.csv          per-ward turnout ratios

Usage:
    python src/byelections.py [--city joburg] [--target 2026] [--tau 18]
"""

from __future__ import annotations

import argparse

import cityconfig
import csv
import math
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

import parties as P


def load_byelections(path: Path, prefix: str,
                     after: date, before: date) -> dict[tuple[str, str], dict]:
    """Return (date, ward) -> {party: votes} for this city's contests.

    Three filters, and all three used to be missing or wrong. The ward prefix
    picks this city out of the provincial file — it came from a hard-coded
    "798", which handed every city Johannesburg's by-elections.

    `before` drops contests that had not happened yet on the target's polling
    day; without it a 2021 backtest would be reading results from 2025.

    `after` is the previous LGE's polling day, and it is a geography filter
    rather than a hindsight one. Every delta below is taken against a ward of
    that number *in that delimitation*; a contest fought before it carries the
    same ward number over different ground, so the subtraction would compare
    two different places and corrupt the delta with no sign that anything went
    wrong. Contests on polling day itself are the general election, not
    by-elections, so the bound is strict.
    """
    contests: dict[tuple[str, str], dict[str, int]] = defaultdict(dict)
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            ward = row["WardID"]
            if not ward.startswith(prefix):
                continue
            when = row["ByElectionDate"]
            if not after < date.fromisoformat(when) < before:
                continue
            key = (when, ward)
            party = P.canonical(row["PartyFullName"])
            contests[key][party] = contests[key].get(party, 0) + int(row["Party_Votes"])
    return contests


def ward_ballot(path: Path) -> tuple[dict[str, dict[str, int]], dict[str, int]]:
    """Ward-ballot votes per ward, and registered voters per ward.

    Read from the LGE preceding the target: that is both the baseline the
    deltas are taken against and the delimitation the by-election wards were
    fought under.
    """
    votes: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    registered_vd: dict[tuple[str, str], int] = {}
    with cityconfig.resolve_path(path).open(encoding="utf-8", newline="") as handle:
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


def age_months(when: str, election_day: date) -> float:
    d = date.fromisoformat(when)
    return (election_day.year - d.year) * 12 + (election_day.month - d.month) + (
        election_day.day - d.day
    ) / 30.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tau", type=float, default=18.0,
                        help="recency half-life in months (plan §3.5, range 6-36)")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw"))
    # Defaults to the ACTIVE TARGET's processed directory, resolved after
    # --city/--target are parsed; a fixed data/processed default would have
    # every city and every target overwriting Johannesburg 2026's files.
    parser.add_argument("--processed", type=Path, default=None)
    cityconfig.add_city_argument(parser)
    cityconfig.add_target_argument(parser)
    args = parser.parse_args(argv)
    city = cityconfig.use(getattr(args, "city", None))
    target = cityconfig.use_target(getattr(args, "target", None))
    if args.processed is None:
        args.processed = target.processed

    base_lge = target.previous_lge
    if base_lge is None:
        raise SystemExit(f"no local election before {target.year}: there is no "
                         f"ward baseline to take by-election deltas against")
    share_col, turnout_col = f"share_{base_lge}", f"turnout_{base_lge}"

    contests = load_byelections(
        args.data_dir / "byelections" / "byelections_Gauteng_vd_party.csv",
        city.ward_prefix, cityconfig.CALENDAR[base_lge].date, target.date,
    )
    votes21, registered21 = ward_ballot(
        args.data_dir / "elections" / target.results(base_lge)
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
            print(f"  ! no {base_lge} ward-ballot base for {ward} ({when}); skipped")
            continue
        base_cast = sum(base.values())
        bye_cast = sum(tally.values())
        base_share = {p: v / base_cast for p, v in base.items()}
        rho = similarity(base_share, city_share)
        w = math.exp(-age_months(when, target.date) / args.tau) * math.sqrt(bye_cast) * rho

        reg = registered21.get(ward, 0)
        t21 = base_cast / reg if reg else float("nan")
        t_bye = bye_cast / reg if reg else float("nan")
        turnout_rows.append(
            {"ward": ward, "date": when, turnout_col: t21, "turnout_bye": t_bye,
             "ratio": t_bye / t21 if t21 else float("nan"), "votes_cast": bye_cast}
        )

        # Only parties that contested (A4: absence ≠ collapse). Sorted because
        # set iteration order varies with the interpreter's hash seed, which
        # made byelection_contest_detail.csv differ on every run of identical
        # code — noise that hid real diffs. The values were never affected.
        for party in sorted(tally):
            d = tally[party] / bye_cast - base_share.get(party, 0.0)
            weighted[party] += w * d
            weight_sum[party] += w
            delta_rows.append(
                {"ward": ward, "date": when, "party": party,
                 share_col: f"{base_share.get(party, 0.0):.4f}",
                 "share_bye": f"{tally[party] / bye_cast:.4f}",
                 "delta": f"{d:+.4f}", "weight": f"{w:.2f}", "rho": f"{rho:.3f}"}
            )

    ratios = [r["ratio"] for r in turnout_rows if r["ratio"] == r["ratio"]]
    # No contest in the window is the normal state for an early target, not a
    # failure: the window is bounded by the previous LGE below and the target
    # above, and for a target at or before the first by-election on record it
    # is legitimately empty. median() of an empty list raises, so the ratio is
    # left undefined and the tilt simply never applies.
    median_ratio = statistics.median(ratios) if ratios else float("nan")
    for row in turnout_rows:
        row["ratio_vs_median"] = (
            row["ratio"] / median_ratio if row["ratio"] == row["ratio"] else float("nan")
        )

    # --- report and write ----------------------------------------------------
    print(f"{len(turnout_rows)} {city.name} by-elections before {target.date}, "
          f"τ = {args.tau} months\n")
    print(f"  {'party':<10s} {'contests':>8s} {'Σweight':>9s} {'weighted Δ':>11s}")
    summary = []
    # secondary key on the name: weight_sum ties otherwise leave row order
    # at the mercy of dict insertion, which made diffs noisy for no reason
    for party in sorted(weighted, key=lambda p: (-weight_sum[p], p)):
        n = sum(1 for r in delta_rows if r["party"] == party)
        mean_delta = weighted[party] / weight_sum[party]
        summary.append({"party": party, "contests": n,
                        "weight_sum": f"{weight_sum[party]:.2f}",
                        "weighted_delta": f"{mean_delta:+.4f}"})
        if weight_sum[party] > 10:
            print(f"  {party:<10s} {n:>8d} {weight_sum[party]:>9.1f} {mean_delta:>+10.1%}")

    print(f"\n  turnout ratio (bye/{base_lge}), citywide median {median_ratio:.3f}:")
    for row in sorted(turnout_rows, key=lambda r: r["ratio_vs_median"]):
        print(f"    ward {row['ward'][-3:]}  {row['date']}  "
              f"{row['turnout_bye']:.1%} vs {row[turnout_col]:.1%}  "
              f"(× {row['ratio_vs_median']:.2f} of median)")

    # Column names are declared rather than read off the first row: with no
    # contest yet held there is no first row, and a consumer meeting a
    # zero-byte file cannot tell "no by-elections" from "the producer failed".
    # A header-only CSV says the first, unambiguously.
    args.processed.mkdir(parents=True, exist_ok=True)
    out_deltas = args.processed / "byelection_party_deltas.csv"
    with out_deltas.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["party", "contests", "weight_sum", "weighted_delta"])
        writer.writeheader()
        writer.writerows(summary)

    out_detail = args.processed / "byelection_contest_detail.csv"
    with out_detail.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["ward", "date", "party", share_col, "share_bye",
                                "delta", "weight", "rho"])
        writer.writeheader()
        writer.writerows(delta_rows)

    out_turnout = args.processed / "byelection_turnout.csv"
    with out_turnout.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["ward", "date", turnout_col, "turnout_bye",
                                "ratio", "votes_cast", "ratio_vs_median"])
        writer.writeheader()
        for row in turnout_rows:
            writer.writerow({**row,
                             turnout_col: f"{row[turnout_col]:.4f}",
                             "turnout_bye": f"{row['turnout_bye']:.4f}",
                             "ratio": f"{row['ratio']:.4f}",
                             "ratio_vs_median": f"{row['ratio_vs_median']:.4f}"})

    print(f"\nwrote {out_deltas}, {out_detail}, {out_turnout}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
