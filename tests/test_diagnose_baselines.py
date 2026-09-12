"""``diagnose.py``'s baseline table — the model and the baselines, one statistic.

⛔ **THE DEFECT THIS EXISTS FOR. The repository's own diagnostic tool told the
operator the model had WON a year it lost.**

``diagnose.main`` built both sides of its section 5 from per-party medians over
draws — the same expression for the model and for each baseline, which is why it
read as fair::

    bs = {p: int(np.median([d.get(p, 0) for d in bd])) for p in {...}}
    berr = sum(abs(bs.get(p, 0) - actual_seats.get(p, 0)) for p in ...)
    verdict = "model better" if total < berr else "BASELINE BETTER"

**One code path, asymmetric consequence.** ``last-lge`` and ``uniform-swing``
are deterministic: every draw is identical, so their per-party median IS the
allocation and sums exactly to the council. The model is stochastic, and the
median of a sum is not the sum of medians — its marginal vector sums to 243 /
259 / 253 against chambers of 260 / 270 / 270 on the Johannesburg panel. The
table therefore set a 253-seat vector against 270-seat ones, and the unallocated
seats subtract error wherever the model over-forecasts, which is exactly where
its error lives.

Measured consequence, Johannesburg:

    year   printed                              comparable (coherent)   verdict
    2011   55 vs uniform-swing 60, "better"     60 vs 60                tie
    2016   21 vs uniform-swing 26, "better"     28 vs 26                model LOSES
    2021   95 vs uniform-swing 126, "better"    86 vs 126               model better

``compare_history``'s own sign count had said so all along (``2016: 0W 1L 0T``),
and ``compare_history.py:1542`` carries this error class in red as §1.214.

WHY THIS SHAPE OF TEST, and what was rejected. An **open-spy** (the instrument
``tests/_support.election_files_read`` provides, and the best one here) watches a
mechanism's I/O and asserts both that the bad thing was absent and that the
mechanism ran. There is no I/O in this defect: it is arithmetic. So the
instrument is a **constructed inversion** — a synthetic draw set whose marginal
comparison and coherent comparison give OPPOSITE verdicts — put through the real
functions, with the *numbers* asserted and never the word "better". A test on the
word would be the trap this project has already fallen into: pinning a `why`
string while the arithmetic beside it is wrong.

**THE POPULATION** these four tests cover is *every forecaster row section 5
prints*, which is ``diagnose.BASELINES`` plus the model. It is asserted to be
what was scanned, in both directions: every name is a key of
``benchmarks.BENCHMARKS``, the registry's remainder is the single name
(``blended-swing``) this table deliberately omits, and every row returned maps to
a name that was passed in.

Nothing here runs the model, reads ``data/``, or needs a scenario: every function
under test is pure, which is the reason they were lifted out of ``main``.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import benchmarks as BM  # noqa: E402
import compare_history as C  # noqa: E402
import diagnose as D  # noqa: E402

DIAGNOSE_SRC = (ROOT / "src" / "diagnose.py").read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# THE CONSTRUCTED INVERSION — Johannesburg 2016 in miniature.
#
# A council of 270 and three real parties, plus ten micro-parties that each hold
# three seats in 3 of 30 draws. Every draw sums to EXACTLY 270, so the model is
# not being handed an incoherent forecast; the incoherence is created purely by
# taking a median down each column, which is the defect.
#
#   each micro:   seats in 3 of 30 draws  ->  median 0, mean 0.3
#   ANC:          137 in every draw       ->  median 137 (actual 140)
#
#   model marginal   {ANC 137, DA 90, EFF 40, ten zeros}   fills 267   err 3
#   model coherent   the above + three remainder seats     fills 270   err 6
#   baseline         {ANC 142, DA 88, EFF 40}, every draw  fills 270   err 4
#
# So the marginal comparison says the model wins by 1 and the coherent one says
# it LOSES by 2. Every integer above is asserted below; none of them was read
# off a run of this model, and none is a golden.
# ---------------------------------------------------------------------------

COUNCIL = 270
ACTUAL = {"ANC": 140, "DA": 90, "EFF": 40}


def model_draws() -> list[dict]:
    """30 draws, each filling exactly 270 seats, medians filling 267."""
    return [{"ANC": 137, "DA": 90, "EFF": 40, f"M{i % 10}": 3}
            for i in range(30)]


def deterministic_baseline(seats: dict, n: int = 30) -> list[dict]:
    """``n`` identical draws — what `last-lge` and `uniform-swing` produce."""
    return [dict(seats) for _ in range(n)]


BASELINE = {"ANC": 142, "DA": 88, "EFF": 40}


def test_the_verdict_comes_from_the_statistic_that_fills_the_council():
    """The inversion, with the verdict taken from the coherent side.

    THE INVARIANT IS STATED AS A NUMBER, NOT AS A WORD: the vector the verdict
    is computed from is the one whose seats sum to the council. A test on the
    string "BASELINE BETTER" would pass against arithmetic that had drifted,
    which is the fault class CLAUDE.md §4 names ("assert the number, not the
    message").

    WHICH three micro-parties collect the remainder seats is deliberately NOT
    asserted: all ten tie at a remainder of 0.3 and ``np.argsort`` is not a
    stable sort. The error totals are invariant to that order — each phantom
    seat costs 1 whoever holds it — so the totals are what is pinned.
    """
    rows = D.baseline_rows(model_draws(), {"uniform-swing":
                                           deterministic_baseline(BASELINE)},
                           ACTUAL, COUNCIL)
    model, bench = rows[0], rows[1]

    # The model: marginal is three seats short of the chamber, coherent is not.
    assert model["marginal_sum"] == 267, model["marginal_sum"]
    assert model["coherent_sum"] == COUNCIL == 270, model["coherent_sum"]
    assert model["marginal_err"] == 3, model["marginal_err"]
    assert model["coherent_err"] == 6, model["coherent_err"]

    # The baseline is deterministic, so both statistics agree — which is the
    # whole asymmetry: the same expression means two different things.
    assert bench["marginal_sum"] == bench["coherent_sum"] == COUNCIL
    assert bench["marginal_err"] == bench["coherent_err"] == 4

    # THE FIXTURE STILL INVERTS. Asserted, so that a future change which stops
    # it inverting fails here loudly instead of passing on a premise that has
    # quietly become vacuous — the "input is constructed, not observed" rule.
    assert model["marginal_err"] < bench["marginal_err"], (
        "the fixture no longer inverts: the marginal comparison must favour "
        "the model, or this test is no longer testing anything")
    assert model["coherent_err"] > bench["coherent_err"], (
        "the fixture no longer inverts: the coherent comparison must favour "
        "the baseline")

    # And the verdict follows the coherent one, by two seats.
    assert bench["margin"] == -2, bench["margin"]
    assert bench["better"] == "baseline", bench

    # The invariant, independent of either file's text: the statistic the
    # verdict is computed from is the one that fills the chamber.
    verdict_sum = sum(model["coherent"].values())
    assert verdict_sum == model["council"], (verdict_sum, model["council"])
    assert bench["margin"] == bench["coherent_err"] - model["coherent_err"]
    assert bench["margin"] != bench["marginal_err"] - model["marginal_err"], (
        "the margin is computable from the marginal statistic too, and here it "
        "must not be: on this fixture the two disagree in SIGN")


def test_two_identical_forecasters_cannot_beat_each_other():
    """Score the same draws as model and as baseline: it must be a tie.

    THE GENERAL FORM OF THE DEFECT. The original code did not use two different
    statistics — it used one, whose meaning depends on whether the forecaster is
    deterministic. This test catches the general case: because the fixture's
    marginal total (267) and coherent total (270) differ, scoring one side by
    one statistic and the other by the other cannot produce a tie here. It would
    report the model as three seats better than itself.
    """
    draws = model_draws()
    rows = D.baseline_rows(draws, {"last-lge": draws}, ACTUAL, COUNCIL)
    model, twin = rows[0], rows[1]
    assert twin["margin"] == 0, twin["margin"]
    assert twin["better"] == "tie", twin["better"]
    for key in ("marginal_err", "coherent_err", "marginal_sum", "coherent_sum"):
        assert model[key] == twin[key], (key, model[key], twin[key])
    # The premise: on this fixture the two statistics genuinely differ, so the
    # tie above is evidence rather than an arithmetic identity.
    assert model["marginal_err"] != model["coherent_err"]


def _largest_remainder_inlined(source: str) -> list[str]:
    """Functions that apportion by largest remainder, by their own shape.

    The signature of the operation: inside ONE function, a floor of a scaled
    vector and an ordering of the remainders. That is the shape
    ``compare_history.coherent_seats`` has (``np.floor`` then ``np.argsort`` on
    ``exact - base``), and it is the shape anyone re-inlining it would write.
    """
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        calls = {ast.unparse(c.func) for c in ast.walk(node)
                 if isinstance(c, ast.Call)}
        floors = {c for c in calls if c.split(".")[-1] == "floor"}
        orders = {c for c in calls
                  if c.split(".")[-1] in ("argsort", "sort") or c == "sorted"}
        if floors and orders:
            found.append(node.name)
    return found


VIOLATION = '''
import numpy as np

def coherent_seats_copy(draws, council):
    parties = sorted({p for d in draws for p in d})
    mean = np.array([np.mean([d.get(p, 0) for d in draws]) for p in parties])
    exact = mean * (council / mean.sum())
    base = np.floor(exact).astype(int)
    for i in np.argsort(-(exact - base))[:council - int(base.sum())]:
        base[i] += 1
    return {p: int(n) for p, n in zip(parties, base)}
'''


def test_one_definition_of_the_coherent_chamber():
    """`diagnose` must REACH the statistic, never re-implement it.

    Two independent checks, because they fail differently. Object identity
    catches a copy that has drifted in behaviour; the AST detector catches a
    copy that has not drifted yet. CLAUDE.md forbids a second definition of
    anything, and this file's defect is what a second definition costs: the
    warning about what a marginal median does NOT sum to lived in
    ``seats_from_draws``' docstring, and the copy at ``diagnose.py:160`` left it
    behind.

    IT CAN SEE: the detector is run over a CONSTRUCTED violation — a working
    copy of the apportionment, in the shape the real one has — and must find it.
    """
    assert D.coherent_seats is C.coherent_seats, (
        "diagnose must use compare_history's coherent_seats, not its own")
    assert D.seats_from_draws is C.seats_from_draws, (
        "diagnose must use compare_history's seats_from_draws, not a copy of "
        "the comprehension")

    assert _largest_remainder_inlined(VIOLATION) == ["coherent_seats_copy"], (
        "the detector cannot see a re-inlined largest-remainder apportionment, "
        "so its silence about diagnose.py below means nothing")
    inlined = _largest_remainder_inlined(DIAGNOSE_SRC)
    assert not inlined, (
        f"src/diagnose.py apportions seats itself in {inlined}. There is one "
        f"definition of a coherent chamber and it is compare_history."
        f"coherent_seats.")


def test_a_forecaster_whose_draws_do_not_fill_the_council_is_flagged():
    """Rescaling a short chamber UP is the same defect, inverted.

    ``coherent_seats`` normalises to ``council``. Schedule 1 takes independents
    (C) and no-PR-list ward winners (D) out of the pool before the quota is
    struck (``seats.outside_pool_wards``; eThekwini 2011 C=1, 2016 C=4, §1.163),
    so a forecaster whose own draws fill ``council - C - D`` would be scaled up
    and handed phantom seats — flattering whichever side fills the chamber.

    It is reported rather than corrected, and the flag is asserted BOTH ways: a
    one-sided check would pass with the flag wired to ``False``.
    """
    short = D.seat_scores(deterministic_baseline({"ANC": 140, "DA": 86,
                                                  "EFF": 40}), ACTUAL, COUNCIL)
    full = D.seat_scores(deterministic_baseline(BASELINE), ACTUAL, COUNCIL)
    assert short["draw_total"] == 266.0, short["draw_total"]
    assert full["draw_total"] == 270.0, full["draw_total"]
    assert short["fills_council"] is False
    assert full["fills_council"] is True
    # And the apportionment really did move seats it was not given: 266 drawn,
    # 270 apportioned.
    assert short["coherent_sum"] == COUNCIL

    lines = D.render_baselines(D.baseline_rows(
        model_draws(), {"last-lge": deterministic_baseline({"ANC": 140,
                                                            "DA": 86,
                                                            "EFF": 40})},
        ACTUAL, COUNCIL))
    assert any(ln.strip().startswith("last-lge *") for ln in lines), (
        "a rescaled forecaster must carry the flag in the table")
    assert any("266.0 seats" in ln for ln in lines), (
        "the footnote must say what the draws actually filled")

    clean = D.render_baselines(D.baseline_rows(
        model_draws(), {"last-lge": deterministic_baseline(BASELINE)},
        ACTUAL, COUNCIL))
    assert not any("*" in ln for ln in clean), (
        "a forecaster that fills the council must NOT be flagged; the flag "
        "fires on everything and therefore says nothing")


def _cells(lines: list[str], name: str) -> list[int]:
    """Every integer printed on the table row for ``name``."""
    for line in lines:
        if line.strip().startswith(name):
            return [int(n) for n in re.findall(r"-?\d+", line[line.index(name)
                                                              + len(name):])]
    raise AssertionError(f"no row for {name!r} in:\n" + "\n".join(lines))


def test_every_baseline_the_table_prints_is_scored_and_named():
    """THE POPULATION — and that the printed table carries what was computed.

    (0) THE RIGHT SET, in both directions. The population is the forecasters
    section 5 prints. Every one must be a real benchmark, and the registry's
    remainder must be the single name this table omits ON PURPOSE — so a fifth
    benchmark landing in ``benchmarks.BENCHMARKS`` fails here and somebody
    decides, rather than being silently left out of the diagnostic.

    Then the round trip: the numbers PRINTED are parsed back out and asserted
    equal to the numbers COMPUTED. A table that computes the coherent statistic
    and prints the marginal one in its column is the original defect wearing a
    fix, and nothing else here would catch it.
    """
    assert set(D.BASELINES) <= set(BM.BENCHMARKS), (
        f"diagnose prints {sorted(set(D.BASELINES) - set(BM.BENCHMARKS))}, "
        f"which benchmarks.py cannot run")
    assert set(BM.BENCHMARKS) - set(D.BASELINES) == {"blended-swing"}, (
        f"the set of benchmarks diagnose does NOT print has changed to "
        f"{sorted(set(BM.BENCHMARKS) - set(D.BASELINES))}. Add it to "
        f"diagnose.BASELINES or record here why the table omits it.")
    # (1) IT LOOKED. Three of the four registered benchmarks today; the
    # denominator is the registry, so it moves with the tree rather than going
    # stale, and a one-sided floor could not be repaired by lowering it.
    scanned(D.BASELINES, of=sorted(BM.BENCHMARKS), low=0.5, high=1.0,
            what="baselines diagnose's section 5 scores",
            denominator="benchmarks.BENCHMARKS")

    # `main` must iterate the constant, or the constant is a decoration and the
    # population above is not the population printed.
    main_node = next(n for n in ast.parse(DIAGNOSE_SRC).body
                     if isinstance(n, ast.FunctionDef) and n.name == "main")
    literals = {n.value for n in ast.walk(main_node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value in set(BM.BENCHMARKS)}
    assert not literals, (
        f"diagnose.main names benchmarks as string literals {sorted(literals)} "
        f"instead of iterating BASELINES, so the declared population and the "
        f"printed one can differ")
    assert "BASELINES" in {n.id for n in ast.walk(main_node)
                           if isinstance(n, ast.Name)}
    # IT CAN SEE: the same detector over a constructed `main` that hard-codes
    # the names must find them.
    control = ast.parse('def main():\n    for b in ("last-lge",):\n        pass\n')
    assert {n.value for n in ast.walk(control)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)
            and n.value in set(BM.BENCHMARKS)} == {"last-lge"}

    # Rows out == forecasters in, both directions, plus the model.
    bench_draws = {"last-lge": deterministic_baseline({"ANC": 120, "DA": 100,
                                                       "EFF": 50}),
                   "uniform-swing": deterministic_baseline(BASELINE),
                   "prior-lge-noise": "no prior LGE for this target"}
    rows = D.baseline_rows(model_draws(), bench_draws, ACTUAL, COUNCIL)
    assert rows[0]["is_model"] is True
    assert [r["name"] for r in rows[1:]] == list(D.BASELINES), [
        r["name"] for r in rows]
    assert {r["name"] for r in rows[1:]} == set(bench_draws)

    # A baseline that could not run is a ROW, not an absence — and carries no
    # verdict, because it has no numbers to earn one.
    failed = rows[-1]
    assert failed["error"] == "no prior LGE for this target"
    assert failed["margin"] is None and failed["better"] is None
    assert "coherent_err" not in failed

    lines = D.render_baselines(rows)
    assert any(D.VERDICT_STATISTIC in ln for ln in lines), (
        "the table must name the statistic its verdict is computed from")

    # THE ROUND TRIP. Columns are coherent, marginal, medians-fill, council,
    # then the margin carried in the verdict.
    model_cells = _cells(lines, "this model")
    assert model_cells[:4] == [rows[0]["coherent_err"], rows[0]["marginal_err"],
                               rows[0]["marginal_sum"], COUNCIL], model_cells
    assert model_cells[0] != model_cells[1], (
        "on this fixture the two statistics differ (6 and 3); a table printing "
        "the same number in both columns has lost one of them")

    swing = _cells(lines, "uniform-swing")
    assert swing[:4] == [rows[2]["coherent_err"], rows[2]["marginal_err"],
                         rows[2]["marginal_sum"], COUNCIL], swing
    # The verdict carries the margin AS A NUMBER, and it is the coherent one.
    assert swing[4] == abs(rows[2]["margin"]) == 2, swing


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
