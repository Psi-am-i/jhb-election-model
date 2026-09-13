"""One election, laid out so a fault can be ISOLATED rather than summarised.

A headline seat error says the forecast was 62 out. It does not say whether the
citywide vote was wrong, or the vote was right and the ward geography wrong, or
the ward calls were right and the seat arithmetic concentrated a small vote
error at the top. Those are three different bugs with three different fixes, and
a single number cannot tell them apart.

So this prints five things for one city-year, in the order a fault travels
through the model:

1. **CITYWIDE VOTE** — every party, PR and ward ballot, predicted against
   actual, with the error in points. This is the model's primary output; seats
   are a consequence of it.
2. **SEATS, SPLIT INTO WARD AND LIST** — because they fail for different
   reasons. Ward seats are won one contest at a time and depend on geography;
   list seats are the entitlement left over after ward wins are deducted, and
   depend only on the citywide vote and the quota. A party can be right on
   votes and wrong on wards, or the reverse.
3. **EVERY WARD CALLED WRONG** — the ward, who won it, who the model said, and
   what probability the model put on the party that actually won. A ward lost at
   p=0.45 is noise; a ward lost at p=0.02 is a fault.
4. **WHERE THE SEAT ERROR CAME FROM** — the same total decomposed by party, so
   a 62 can be read as "the ANC alone is 25 of it" instead of as a mystery.
5. **THE SAME MEASURE FOR THE NAIVE BASELINES** — because a seat error means
   nothing until "last time happens again" is standing beside it.

⛔ **THERE ARE TWO SEAT POINT FORECASTS AND THIS FILE REPORTED ONE AS THE
OTHER.** Sections 2 and 4 show the per-party MEDIAN over draws, which is what a
reader wants beside a per-party actual. The median of a sum is not the sum of
medians, so that vector does not fill a council: on the Johannesburg panel it
sums to 243 / 259 / 253 against chambers of 260 / 270 / 270. The baselines in
section 5 are deterministic — every draw is identical — so THEIR medians are a
chamber, and until 2026-09-12 this table set a 253-seat vector against 270-seat
ones and read the shortfall as skill.

It was worth a verdict. Johannesburg 2016 printed "model better" (21 against
uniform swing's 26) on a year the model **loses** (28 against 26) — which is
what ``compare_history``'s own sign count had said all along, ``2016: 0W 1L
0T``. 2011 printed a win on a tie.

So every verdict here is computed from :data:`VERDICT_STATISTIC` —
``seat_abs_err_coherent``, the largest-remainder apportionment of the MEAN seat
vector, which IS a council — on **both** sides, through the one function that
defines it (``compare_history.coherent_seats``). The marginal figure is still
printed, because sections 2 and 4 are built on it and the two must reconcile,
but it is labelled, it carries what it sums to, and it decides nothing.
MODEL-LOG §1.214.

Usage::

    python src/diagnose.py --city joburg --target 2016
    python src/diagnose.py --city joburg --target 2021 --draws 2000
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backtest as B
import benchmarks as BM
import cityconfig
import montecarlo as M
# ⛔ ONE DEFINITION OF THE COHERENT CHAMBER, AND IT IS NOT HERE. `coherent_seats`
# apportions the mean seat vector by largest remainder so the result IS a
# council; `seats_from_draws` is the marginal median it must never be confused
# with, and its docstring carries the argument for keeping both. Importing them
# rather than copying them is what stops section 5 drifting away from the panel
# that adjudicates the model. CLAUDE.md: one definition only.
#
# `seat_abs_err` and `chamber_fill` arrive by the same route and for the same
# reason. Both were written out longhand here AND in `compare_history`, and
# `compare_history.seat_abs_err`'s docstring names this file as the second copy:
# "the defect fix #34 removes was not in this arithmetic but in WHICH VECTOR
# each call site handed it. One name makes the pairing visible at every call."
# Two copies cannot be made to disagree about the pairing by one edit, which is
# exactly the property wanted.
from compare_history import (chamber_fill, coherent_seats, scored_opponents,
                             seat_abs_err, seats_from_draws)
from fold import citywide, load

# `score`, `seats.allocate` and `seats.eligible_parties` were imported here and
# used by nothing — verified by AST reference count across src/ and tests/ on
# 2026-09-12. Removed with this change rather than left as furniture; every one
# of them is still imported, and used, by the modules that actually allocate.


def run(city_slug: str, year: str, draws: int, data_dir: Path):
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=None, draws=draws, seed=None,
        city=city_slug, target=year))
    return target, M.run_model(target, scenario, data_dir, verbose=False)


# ---------------------------------------------------------------------------
# THE BASELINE TABLE — as data first, as text second.
#
# SEPARATED FROM `main` DELIBERATELY. The defect these functions exist to
# prevent is arithmetic, and arithmetic buried inside a print loop cannot be
# tested without a data directory, a model run and three minutes. Everything
# below is pure — dicts in, dicts and strings out — so a CONSTRUCTED inversion
# goes through it in milliseconds. See `tests/test_diagnose_baselines.py`.
# ---------------------------------------------------------------------------

BASELINES = scored_opponents()
"""The forecasters section 5 scores. **DERIVED FROM THE PANEL, NEVER TYPED.**

⛔ THIS WAS A TYPED TUPLE AND THE TYPING IS WHAT BROKE IT. `benchmarks.py`
gained `uniform-swing+roster`; this list did not; and the diagnostic would have
gone on printing three opponents while the scoreboard printed four, for the same
city-year, with nothing saying which was the panel's view. That is the silent
drop this repository keeps paying for — a lever left in the register, a party
deleted from the code, a whole panel's worth of city-years (§1.69) — and the
answer is always the same one: derive it, in the inclusive direction, so an
unknown name appears rather than disappears.

`compare_history.scored_opponents` is that derivation, and taking it rather than
re-deriving it here is the point. It reads `benchmarks.BENCHMARKS` minus
`compare_history.OPPONENTS_NOT_SCORED` — today `blended-swing` alone, whose
written reason names this file — so the diagnostic and the panel **cannot**
disagree about who the opponents are. A second derivation with the same inputs
would be a second thing to keep in step, which is the state this replaces.

⚠️ ORDER COMES WITH IT. `scored_opponents` sorts by `OPPONENT_ORDER` first, so a
reference the panel has not ranked prints last here too. `baseline_rows` orders
its rows off this tuple, so the table and the scoreboard read in one order.
"""

VERDICT_STATISTIC = "seat_abs_err_coherent"
"""The statistic every verdict in section 5 is computed from, both sides.

Named, and printed, because the alternative has a record. `compare_history`
carries `seat_abs_err` and `seat_abs_err_coherent` under two names for exactly
this reason (§1.214): on 2026-09-08 a marginal 706 was read against a coherent
707 and a batch that was +38 coherent was reported as "essentially flat".
"""


# `_abs_err` LIVED HERE AND IT WAS THE SECOND COPY OF `compare_history
# .seat_abs_err`. Deleted 2026-09-13, not because the two had drifted — they had
# not, the arithmetic was identical — but because the defect §1.214 records was
# never in this arithmetic at all. It was in WHICH VECTOR each call site handed
# it, and a repository with two names for one operation has two places to check
# that pairing and no way to fix both in one edit. CLAUDE.md: one definition.


def seat_scores(draws, actual_seats: dict, council: int) -> dict:
    """Both seat point forecasts for ONE forecaster, and what each one fills.

    ``marginal``  per-party median over draws (`compare_history.seats_from_draws`).
                  What a reader wants beside a per-party actual, and NOT a
                  chamber — the median of a sum is not the sum of medians.
    ``coherent``  largest remainder on the mean seat vector
                  (`compare_history.coherent_seats`). A council, by construction.

    ``draw_total`` is the mean number of seats this forecaster's own draws
    actually fill, and it is here because `coherent_seats` RESCALES to
    ``council``. Schedule 1 takes independents (C) and the winners of wards
    contested by parties with no PR list (D) out of the pool before the quota is
    struck (`seats.outside_pool_wards`, MODEL-LOG §1.163), so a forecaster whose
    draws fill ``council - C - D`` would be rescaled UP — inventing phantom
    seats and flattering whoever fills the chamber. That is the same defect this
    change removes, running the other way. It is therefore reported and flagged
    in the print, never silently corrected: `fills_council` is False whenever the
    draws do not fill the chamber they are about to be apportioned into.
    """
    marginal = seats_from_draws(draws)
    coherent = coherent_seats(draws, council)
    return {
        "marginal": marginal,
        "coherent": coherent,
        "marginal_err": seat_abs_err(marginal, actual_seats),
        "coherent_err": seat_abs_err(coherent, actual_seats),
        "marginal_sum": sum(marginal.values()),
        "coherent_sum": sum(coherent.values()),
        # `draw_total` and `fills_council`, from the ONE function that decides
        # what "filled the chamber" means. It was two lines here and the same
        # two lines in `compare_history.chamber_fill`, including the half-seat
        # tolerance — a constant that has to be the same number in the panel and
        # in the diagnostic or the two flag different rows.
        **chamber_fill(draws, council),
        "council": council,
    }


def baseline_rows(model_draws, bench_draws: dict, actual_seats: dict,
                  council: int) -> list[dict]:
    """One row per forecaster, the model first, every row scored the SAME WAY.

    ⛔ THE POINT OF THIS FUNCTION IS THAT THERE IS ONE CALL TO `seat_scores`
    AND EVERY FORECASTER GOES THROUGH IT. The defect it replaces used the same
    code path for both sides too — and that was not enough, because the
    consequence of a marginal median is asymmetric: a DETERMINISTIC baseline's
    median is its allocation exactly, while a stochastic forecaster's is short
    of the chamber. Identical treatment of a statistic that means different
    things by forecaster is not a like-for-like comparison.

    ``bench_draws`` maps name -> draws. A value that is not a non-empty list is
    an ERROR ROW carrying that value as its reason: `benchmarks.run_one` raises
    `SystemExit` for a baseline that cannot be computed for a year, and a
    forecaster that could not run must appear in the table saying so rather than
    vanish from it.

    ``margin`` is ``row.coherent_err - model.coherent_err``, so POSITIVE means
    the model is better by that many seats. ``better`` is the sign of the
    margin and nothing else.
    """
    model = {"name": "this model", "is_model": True, "margin": None,
             "better": None, **seat_scores(model_draws, actual_seats, council)}
    rows = [model]
    ordered = ([n for n in BASELINES if n in bench_draws]
               + [n for n in bench_draws if n not in BASELINES])
    for name in ordered:
        draws = bench_draws[name]
        if not isinstance(draws, list) or not draws:
            rows.append({"name": name, "is_model": False, "margin": None,
                         "better": None,
                         "error": str(draws) if draws else "not computed"})
            continue
        row = {"name": name, "is_model": False,
               **seat_scores(draws, actual_seats, council)}
        row["margin"] = row["coherent_err"] - model["coherent_err"]
        row["better"] = ("tie" if row["margin"] == 0
                         else "model" if row["margin"] > 0 else "baseline")
        rows.append(row)
    return rows


def render_baselines(rows: list[dict]) -> list[str]:
    """Section 5 as lines. BOTH statistics, labelled, verdict named."""
    model = rows[0]
    out = [
        "5. THE SAME MEASURE FOR THE NAIVE BASELINES",
        "",
        f"  ⛔ THE VERDICT IS `{VERDICT_STATISTIC}`, ON BOTH SIDES, THROUGH",
        "     ONE FUNCTION: largest remainder on the mean seat vector, which IS",
        "     a council.",
        "  The `marginal` column sums per-party MEDIANS, and this model's",
        f"     fill {model['marginal_sum']} of {model['council']} seats — "
        f"short of a chamber, which flatters",
        "     whichever forecaster over-forecasts. It is printed because",
        "     sections 2 and 4 are built on it and the two must reconcile.",
        "     IT DECIDES NOTHING. Reading one as the other is MODEL-LOG",
        "     §1.214.",
        "",
        f"  {'forecaster':<20}{'coherent':>10}{'marginal':>10}"
        f"{'medians fill':>16}{'verdict (coherent)':>23}",
    ]
    for r in rows:
        if "error" in r:
            out.append(f"  {r['name']:<20}{'—':>10}{'—':>10}"
                       f"{'—':>16}{r['error'][:23]:>23}")
            continue
        name = r["name"] + ("" if r["fills_council"] else " *")
        fills = f"{r['marginal_sum']} of {r['council']}"
        if r["is_model"]:
            verdict = "—"
        elif r["better"] == "tie":
            verdict = "tie, 0 seats in it"
        elif r["better"] == "model":
            verdict = f"model better by {r['margin']}"
        else:
            verdict = f"BASELINE BETTER by {-r['margin']}"
        out.append(f"  {name:<20}{r['coherent_err']:>10}{r['marginal_err']:>10}"
                   f"{fills:>16}{verdict:>23}")
    flagged = [r for r in rows if "error" not in r and not r["fills_council"]]
    if flagged:
        # Built outside the f-string: a nested f-string quoted with the same
        # character is a syntax error before Python 3.12, and this file has to
        # import on whatever interpreter the CLI is run with.
        names = ", ".join(r["name"] for r in flagged)
        fills = ", ".join("%.1f" % r["draw_total"] for r in flagged)
        out += [
            "",
            f"  * {names}: these draws fill {fills} seats, not "
            f"{model['council']}, so the",
            "    largest-remainder apportionment RESCALED them UP and part of",
            "    the error above is the chamber definition rather than the",
            "    forecast. Schedule 1 removes independents (C) and no-PR-list",
            "    ward winners (D) from the pool before the quota is struck:",
            "    `seats.outside_pool_wards`, MODEL-LOG §1.163. FLAGGED, NOT",
            "    CORRECTED — inventing the missing seats is this section's own",
            "    defect, inverted.",
        ]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--target", default="2021")
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    ap.add_argument("--wards", type=int, default=40,
                    help="how many wrong ward calls to list (0 = all)")
    args = ap.parse_args(argv)

    target, run_ = run(args.city, args.target, args.draws, args.data_dir)
    path = args.data_dir / target.results(target.year)
    actual_seats, actual_ward_winners = B.actual_result(
        path, target.council, int(target.year))

    pr_votes, _ = load(path, "PR")
    ward_votes, _ = load(path, "Ward")
    actual_pr, actual_wd = citywide(pr_votes), citywide(ward_votes)

    idx = run_.index
    name = cityconfig.active().name

    # ENTRANT IS RELABELLED, exactly as backtest.relabel_entrant and
    # score.seat_matrix do it. The model draws a GENERIC entrant because it
    # cannot know a new party's name, so scoring maps it onto whichever
    # seat-winning party had no baseline at all.
    #
    # Not doing this made the first version of this report double-count, and in
    # the most misleading possible direction. At Johannesburg 2016 it showed the
    # AIC at 0.00% predicted against 1.62% actual -- a total miss -- and ENTRANT
    # at 1.46% against 0.00% actual -- pure phantom mass. They are the SAME
    # FORECAST. The model said "a party will arrive at about 1.5%" and the AIC
    # arrived at 1.62%, which is close, and the table called it two separate
    # failures worth 3pp between them.
    # The newcomer test is against the model's BASELINE -- the preceding
    # national election -- not against its index. A party can be in the index
    # (the pool fit gave it a vector) and still have no baseline to grow from,
    # which is exactly the AIC in 2016: present in the index, absent from the
    # 2014 NPE, and therefore the party the generic entrant stands for.
    #
    # ⛔ AND THAT SENTENCE WAS RIGHT WHILE `compare_history` DID THE OPPOSITE.
    # It passed `{p: 1.0 for p in run.index}` — the index this comment says not
    # to use — so the panel and this diagnostic could name different parties as
    # the arrival at the same city-year. Both now go through
    # `backtest.entrant_actual_for_target`, which is the only thing that reads
    # the preceding NPE for this purpose. §1.206, fix #12.
    arrived = B.entrant_actual_for_target(target, actual_seats, args.data_dir)
    relabelled_from_entrant = False
    if arrived and "ENTRANT" in idx:
        e = idx["ENTRANT"]
        if arrived in idx:
            run_.pr_share_draws[:, idx[arrived]] += run_.pr_share_draws[:, e]
            run_.ward_share_draws[:, idx[arrived]] += run_.ward_share_draws[:, e]
        else:
            # Not in the index at all, so the ENTRANT column IS its whole
            # forecast. Point the lookup at that column rather than reporting
            # the party as a flat zero, which is a missing row masquerading as
            # a prediction of nothing.
            idx[arrived] = e
            e = None
        if e is not None:
            run_.pr_share_draws[:, e] = 0.0
            run_.ward_share_draws[:, e] = 0.0
        # Whichever branch ran, ENTRANT must not also be printed as a party in
        # its own right: its mass now belongs to `arrived` and showing both
        # counts the same forecast twice.
        relabelled_from_entrant = True
        run_.seat_draws = [
            {**{k: v for k, v in d.items() if k != "ENTRANT"},
             arrived: d.get(arrived, 0) + d.get("ENTRANT", 0)}
            for d in run_.seat_draws]
        print(f"\n  (ENTRANT relabelled onto {arrived}, which arrived from "
              f"nothing and won {actual_seats.get(arrived, 0)} seats — the "
              f"model's generic-entrant slot IS its forecast for it)")

    # ---- 1. citywide vote ------------------------------------------------
    print(f"\n{'=' * 78}\n{name} {target.year} — council {target.council}, "
          f"{len(run_.wards)} wards, {run_.draws} draws\n{'=' * 78}")
    print("\n1. CITYWIDE VOTE  (model = mean over draws; err in percentage points)\n")
    print(f"  {'party':<14}{'PR model':>10}{'PR actual':>11}{'err':>8}"
          f"{'ward model':>12}{'ward actual':>12}{'err':>8}")
    universe = sorted((set(actual_pr) | set(idx)) - {"ENTRANT"}
                      if arrived else set(actual_pr) | set(idx),
                      key=lambda p: -actual_pr.get(p, 0.0))
    pr_err_total = wd_err_total = 0.0
    for p in universe:
        a_pr, a_wd = actual_pr.get(p, 0.0), actual_wd.get(p, 0.0)
        i = idx.get(p)
        m_pr = float(run_.pr_share_draws[:, i].mean()) if i is not None else 0.0
        m_wd = float(run_.ward_share_draws[:, i].mean()) if i is not None else 0.0
        pr_err_total += abs(m_pr - a_pr)
        wd_err_total += abs(m_wd - a_wd)
        if max(a_pr, m_pr) < 0.002:
            continue
        print(f"  {p[:13]:<14}{m_pr:>9.2%} {a_pr:>10.2%} {100*(m_pr-a_pr):>+7.2f}"
              f"{m_wd:>11.2%} {a_wd:>11.2%} {100*(m_wd-a_wd):>+7.2f}")
    print(f"\n  total absolute vote error: PR {100*pr_err_total:.2f}pp, "
          f"ward {100*wd_err_total:.2f}pp  (sums both directions, so a model "
          f"that moves 3pp from small parties to large scores 6)")

    # ---- 2. seats, split -------------------------------------------------
    actual_wardwins = Counter(actual_ward_winners.values())
    # ⛔ THIS WAS A SECOND DEFINITION OF `seats_from_draws`, COPIED. It is the
    # same comprehension, without the docstring that says the result does not
    # sum to a council — so the one warning that would have stopped section 5
    # comparing it to a chamber was the thing the copy left behind.
    scores = seat_scores(run_.seat_draws, actual_seats, target.council)
    model_seats = scores["marginal"]
    # Model ward wins: the modal winner of each ward, which is the call it makes.
    model_ward_call: dict[str, str] = {}
    probs = run_.ward_probabilities()
    for ward, dist in probs.items():
        if dist:
            model_ward_call[ward] = max(dist, key=dist.get)
    model_wardwins = Counter(model_ward_call.values())

    print("\n2. SEATS — total, ward and list, because they fail differently\n")
    print(f"  {'party':<14}{'seats':>13}{'ward seats':>16}{'list seats':>16}")
    print(f"  {'':<14}{'model':>6}{'actual':>7}{'model':>8}{'actual':>8}"
          f"{'model':>8}{'actual':>8}")
    rows = sorted(set(actual_seats) | set(model_seats),
                  key=lambda p: -actual_seats.get(p, 0))
    for p in rows:
        a_s, m_s = actual_seats.get(p, 0), model_seats.get(p, 0)
        a_w, m_w = actual_wardwins.get(p, 0), model_wardwins.get(p, 0)
        if not (a_s or m_s or a_w or m_w):
            continue
        # List seats are the entitlement left after ward wins are deducted --
        # plan §0: winning a ward does not add a seat, it decides which
        # entitled seat a ward councillor fills. Negative means overhang.
        print(f"  {p[:13]:<14}{m_s:>6}{a_s:>7}{m_w:>8}{a_w:>8}"
              f"{m_s - m_w:>8}{a_s - a_w:>8}")
    print(f"\n  ward calls: {sum(1 for w, c in model_ward_call.items() if actual_ward_winners.get(w) == c)}"
          f"/{len(model_ward_call)} correct")
    print(f"  the model's seats above are per-party MEDIANS and fill "
          f"{scores['marginal_sum']} of {scores['council']} seats; the "
          f"coherent point\n  forecast — largest remainder on the mean vector, "
          f"used in sections 4 and 5 — fills {scores['coherent_sum']}")

    # ---- 3. wards called wrong -------------------------------------------
    wrong = []
    for ward, call in model_ward_call.items():
        truth = actual_ward_winners.get(ward)
        if truth is None or truth == call:
            continue
        wrong.append((probs[ward].get(truth, 0.0), ward, truth, call,
                      probs[ward].get(call, 0.0)))
    wrong.sort()
    print(f"\n3. WARDS CALLED WRONG — {len(wrong)} of {len(model_ward_call)}\n")
    if wrong:
        print(f"  {'ward':<12}{'won by':<14}{'model said':<14}"
              f"{'P(model call)':>14}{'P(actual winner)':>18}")
        shown = wrong if args.wards == 0 else wrong[:args.wards]
        for p_true, ward, truth, call, p_call in shown:
            flag = "  <-- ruled out" if p_true < 0.02 else ""
            print(f"  {ward:<12}{truth[:13]:<14}{call[:13]:<14}"
                  f"{p_call:>13.0%}{p_true:>17.0%}{flag}")
        if len(wrong) > len(shown):
            print(f"  ... and {len(wrong) - len(shown)} more")
        ruled_out = sum(1 for p, *_ in wrong if p < 0.02)
        print(f"\n  of the {len(wrong)} wrong calls, {ruled_out} gave the actual "
              f"winner under 2% — those are faults, not bad luck; the rest are "
              f"contests the model saw as close and lost")

    # ---- 4. where the seat error came from -------------------------------
    print("\n4. WHERE THE SEAT ERROR CAME FROM\n")
    err_marg = {p: scores["marginal"].get(p, 0) - actual_seats.get(p, 0)
                for p in set(actual_seats) | set(scores["marginal"])}
    err_coh = {p: scores["coherent"].get(p, 0) - actual_seats.get(p, 0)
               for p in set(actual_seats) | set(scores["coherent"])}
    total = scores["coherent_err"]
    print(f"  {'party':<14}{'marginal':>10}{'coherent':>10}"
          f"{'share of coherent':>20}")
    for p in sorted(set(err_marg) | set(err_coh),
                    key=lambda q: (-abs(err_coh.get(q, 0)),
                                   -abs(err_marg.get(q, 0)))):
        m, c = err_marg.get(p, 0), err_coh.get(p, 0)
        if not m and not c:
            continue
        share = f"{abs(c) / total:.0%}" if total else "—"
        print(f"  {p[:13]:<14}{m:>+10}{c:>+10}{share:>20}")
    print("\n  total absolute seat error, and they are NOT the same statistic:")
    print(f"    coherent{scores['coherent_err']:>8}   largest remainder on the "
          f"MEAN seat vector; fills {scores['coherent_sum']}")
    print(f"    {'':<16}of {scores['council']}. ⛔ THIS IS WHAT SECTION 5'S "
          f"VERDICT USES.")
    print(f"    marginal{scores['marginal_err']:>8}   sum of per-party MEDIANS; "
          f"fills {scores['marginal_sum']} of {scores['council']},")
    print(f"    {'':<16}so it is not comparable to a forecaster that fills the "
          f"chamber.")

    # ---- benchmarks, on the same party set AND the same statistic --------
    #
    # The baselines are computed BEFORE anything is printed, because the table
    # is now rendered from rows rather than assembled a line at a time — which
    # is what lets `tests/test_diagnose_baselines.py` put a constructed
    # inversion through the same arithmetic with no data directory at all.
    ctx = BM.build_context(int(target.year), args.data_dir)
    bench_draws: dict[str, object] = {}
    for bench in BASELINES:
        try:
            bench_draws[bench] = BM.run_one(bench, ctx,
                                            draws=min(args.draws, 2000))
        except SystemExit as exc:
            # Not `continue`. A baseline that cannot be computed for this year
            # must appear in the table saying so; dropping the row leaves the
            # reader to notice an absence.
            bench_draws[bench] = str(exc)
    print()
    for line in render_baselines(baseline_rows(
            run_.seat_draws, bench_draws, actual_seats, target.council)):
        print(line)
    return 0


if __name__ == "__main__":
    M.fix_hash_seed()          # may replace the process; see `fix_hash_seed`
    raise SystemExit(main())
