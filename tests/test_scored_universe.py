"""The scored column set, and the calibration test that has to survive it.

Two defects, both in the INSTRUMENT rather than in the model — which is the
class this repository can least afford, because a broken scorer cannot be
caught by a backtest: it changes what "better" means and every tuning decision
taken against it is taken against nothing.

⛔ **#13 — THE SCORED UNIVERSE IS CHOSEN BY THE FORECASTER.**
``score.seat_matrix`` admits a column when ``truth[i] > 0 or
samples[:, i].max() > 0``. The second clause is the forecaster's own draws, so
two forecasters scored on the same city-year are scored on different columns.
Measured on the committed panel: across 24 city-years the model is scored over
**580** columns and uniform-swing over **332**, and at Johannesburg 2021 alone
it is 55 against 19. ``compare_history`` states this exactly and then scopes the
warning to ``energy`` and ``variogram`` — while the report prints a
``crps.total`` margin of 38.3% over uniform-swing off the same column sets.

⛔ **#15 — THE CALIBRATION HEADLINE RESTS ON A POPULATION THE FORECASTER
SELECTS.** ``claimed`` admits a column when the model gives it a seat in half
its draws. That rule is very nearly the complement of this model's dominant
failure mode, and on the fixed ``reference`` population it drops **eight of the
ten worst columns**. And the χ² printed beside it is a nominal test on columns
that cluster inside city-years, so its rejection of uniformity was never
established.

WHAT SHAPE OF TEST, and what was rejected. ``tests/_support.election_files_read``
is this suite's exemplar: it watches the real mechanism and asserts both that the
bad thing is absent and that the mechanism ran at all. A spy is the wrong
instrument for a scorer — there is no I/O, only arithmetic — so the two
instruments here are:

* for #13, **an invariant with a constructed violation**. The invariant is that
  two forecasters scored on a held universe carry identical column sets and
  identical CRPS and energy totals; the violation is a synthetic pair whose
  admitted columns differ by construction, pushed through the same predicate,
  which must come back False and name the columns.
* for #15, **a positive control on a fixture of known width and shift** —
  ``test_calibration_report._shift_scale_results``, the suite's existing
  constructed calibration panel. The clustered test must reject a population
  built to be non-uniform and must not reject one built to be calibrated; and
  because the point of the correction is the DESIGN EFFECT, there is a third
  control where the columns are correlated inside their clusters but still
  uniform marginally, which the nominal test rejects falsely and the corrected
  one must not.

Every assertion below is on a NUMBER. None is on the wording of a verdict
string: this repository has already shipped a test that pinned a ``why`` note
while the arithmetic beside it was broken.
"""

from __future__ import annotations

import json
import math
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned, skip  # noqa: E402

import numpy as np  # noqa: E402

import score as S  # noqa: E402


# ---------------------------------------------------------------------------
# constructed forecasters
# ---------------------------------------------------------------------------

# A council of 195 seats over six real parties, three of which are small enough
# that a forecaster can plausibly miss them. Fixed rather than drawn from the
# repository's own output: a fixture whose premise is a passing state of the
# tree expires silently the day that state changes.
ACTUAL = {"ANC": 90, "DA": 60, "EFF": 30, "IFP": 9, "PA": 5, "TINY": 1}

# The input-selected population a comparison should be held on — here a stand-in
# for `compare_history.reference_universe`, which is built from a previous
# result and a nomination slate and cannot be computed inside `score.py`.
# ⛔ IT DOES NOT CONTAIN EVERY SEAT-WINNER, deliberately: `TINY` won a seat and
# is absent, exactly as seven real parties are absent from `reference` across
# the committed panel (ALJAMAAH at Johannesburg 2011, PA at Johannesburg 2016
# and Ekurhuleni 2016, IFP at Tshwane 2021, MINORITIES_OF_SOUTH_AFRICA at
# eThekwini 2016, AGENCY_FOR_NEW_AGENDA at Mangaung 2016, AIC at Buffalo City
# 2011). That is why the held universe is a union and not this list.
FIXED = ["ANC", "DA", "EFF", "IFP", "PA", "COPE", "ACDP", "ATM"]

# What each forecaster believes. The model carries two GHOST columns — parties
# that won nothing and were never on the fixed list — because phantom mass is
# the thing the admission rule exists to penalise, and a held universe that
# quietly forgave it would be a worse instrument than the one it replaced.
_MODEL = {"ANC": (88, 9), "DA": (62, 8), "EFF": (33, 5), "IFP": (7, 3),
          "PA": (0.2, 0.6), "GHOST_A": (0.4, 0.8), "GHOST_B": (0.3, 0.7)}
_BENCH = {"ANC": (95, 0.01), "DA": (58, 0.01), "EFF": (28, 0.01),
          "IFP": (10, 0.01)}


def _draws(spec, n=400, seed=11):
    """``n`` seat draws from a ``{party: (mean, sd)}`` spec, rounded and clipped."""
    rng = np.random.default_rng(seed)
    return [{p: int(max(0, round(rng.normal(m, sd)))) for p, (m, sd) in spec.items()}
            for _ in range(n)]


def _pair():
    """The model and a deterministic baseline, scored their own way and held."""
    model, bench = _draws(_MODEL, seed=11), _draws(_BENCH, seed=12)
    own = {"model": S.score_seats(model, ACTUAL),
           "bench": S.score_seats(bench, ACTUAL)}
    held = S.hold_universe([model, bench], ACTUAL, fixed=FIXED)
    on_held = {"model": S.score_seats(model, ACTUAL, universe=held),
               "bench": S.score_seats(bench, ACTUAL, universe=held)}
    return model, bench, own, held, on_held


# ---------------------------------------------------------------------------
# #13 — the invariant, and a constructed violation of it
# ---------------------------------------------------------------------------


def test_the_default_admission_rule_leaves_two_forecasters_incomparable():
    """The defect itself, reproduced: the column set moves with the forecaster.

    This is the *premise* of everything below, and it is constructed rather than
    observed — if it ever passes because both forecasters happened to admit the
    same columns, the fixture has stopped reproducing the defect and every
    assertion after it is about nothing.
    """
    _, _, own, _, _ = _pair()
    report = S.comparable(own)

    assert report["by_forecaster"]["model"] != report["by_forecaster"]["bench"], (
        f"the fixture is meant to reproduce the denominator drift and did not: "
        f"both forecasters were scored on "
        f"{report['by_forecaster']['model']} columns. Fix the fixture, not the "
        f"assertion — the whole point is a pair whose admitted sets differ.")
    # The exact asymmetry, so a change to the admission rule fails here loudly
    # rather than somewhere downstream: model 8 columns, baseline 6.
    assert report["by_forecaster"] == {"model": 8, "bench": 6}, \
        report["by_forecaster"]
    assert report["comparable"] is False
    assert sorted(report["mismatch"]) == ["bench", "model"]
    assert report["mismatch"]["model"]["only_here"] == ["GHOST_A", "GHOST_B"], (
        "the columns only the model has are its phantom mass, and the "
        "predicate must name them — a boolean alone cannot be acted on")
    assert report["mismatch"]["bench"]["missing"] == ["GHOST_A", "GHOST_B"]


def test_holding_the_universe_moves_no_crps_and_no_energy_number():
    """⛔ THE LOAD-BEARING CLAIM, AND IT IS AN EXACT ONE.

    A column outside a forecaster's own scored set is, by the admission rule,
    zero in the truth and zero in every one of its draws. Such a column
    contributes ``E|X-y| = 0`` and a spread term of 0 to CRPS, and an extra zero
    coordinate leaves every Euclidean norm unchanged, so it contributes nothing
    to the energy score either. Holding the universe at a SUPERSET therefore
    changes neither, for the model or for the baseline — which is what makes the
    38.3% CRPS margin in the report quotable **as it stands**.

    Asserted with ``==`` on floats, not ``isclose``. The claim is exact
    arithmetic, and a tolerance here would hide the one thing worth knowing: a
    future admission rule that admits a column the forecaster does NOT put mass
    on would break the invariance, and it must break this test rather than drift
    inside a tolerance.
    """
    _, _, own, held, on_held = _pair()

    assert set(held) >= set(own["model"]["parties"]), \
        "the held universe must be a superset or the invariance does not apply"
    assert set(held) >= set(own["bench"]["parties"])

    for name in ("model", "bench"):
        assert on_held[name]["crps"]["total"] == own[name]["crps"]["total"], (
            f"{name}: CRPS total moved from {own[name]['crps']['total']!r} to "
            f"{on_held[name]['crps']['total']!r} when the universe was held. "
            f"Both-zero columns must contribute exactly zero; if they do not, "
            f"the admission rule or `crps_sample` has changed and no "
            f"model-vs-baseline margin computed either way is quotable.")
        assert on_held[name]["energy"] == own[name]["energy"], (
            f"{name}: energy score moved from {own[name]['energy']!r} to "
            f"{on_held[name]['energy']!r}. An extra zero coordinate cannot "
            f"change a Euclidean norm.")

    # And the margin itself — the number the report prints — is untouched.
    before = own["bench"]["crps"]["total"] - own["model"]["crps"]["total"]
    after = on_held["bench"]["crps"]["total"] - on_held["model"]["crps"]["total"]
    assert before == after and before > 0, (before, after)


def test_holding_the_universe_is_what_makes_the_comparison_one_comparison():
    """After holding, the sets are identical and the result says so."""
    _, _, _, held, on_held = _pair()
    report = S.comparable(on_held)

    assert report["comparable"] is True, report["mismatch"]
    assert report["mismatch"] == {}
    assert report["n"] == len(held) == 11
    assert (on_held["model"]["universe_key"]
            == on_held["bench"]["universe_key"] == report["key"])
    assert on_held["model"]["universe_held"] is True
    # The key is order-insensitive: no score here depends on column order, so a
    # key that cried wolf on a reordering would be a guard nobody could keep.
    assert S.universe_key(held) == S.universe_key(list(reversed(held)))
    # ...and it is NOT insensitive to content, which is the half that matters.
    assert S.universe_key(held) != S.universe_key(held[:-1])


def test_the_predicate_catches_a_constructed_violation_of_the_held_universe():
    """⛔ CAN THE DETECTOR SEE? One column removed, through the same predicate.

    The invariant above is only evidence if the thing asserting it would fail
    when the invariant is false. So take a genuinely held pair — the state
    ``test_holding_the_universe_is_what_makes_the_comparison_one_comparison``
    certifies — and break it by one column.
    """
    _, _, _, _, on_held = _pair()
    assert S.comparable(on_held)["comparable"] is True, "precondition"

    broken = {"model": dict(on_held["model"]), "bench": dict(on_held["bench"])}
    dropped = broken["bench"]["parties"][3]
    broken["bench"]["parties"] = [p for p in broken["bench"]["parties"]
                                  if p != dropped]

    report = S.comparable(broken)
    assert report["comparable"] is False, (
        f"a forecaster scored on one fewer column than its opponent was "
        f"reported comparable. The predicate is decoration.")
    assert report["mismatch"]["bench"]["missing"] == [dropped]
    assert report["by_forecaster"] == {"model": 11, "bench": 10}
    assert report["key"] is None, "a mismatched pair has no single universe key"


def test_a_universe_that_omits_a_real_seat_winner_is_refused():
    """The one omission that is never defensible, and why ``reference`` alone
    is not the held universe.

    Dropping a column where a party actually won deletes a real error from the
    sum for BOTH forecasters at once, which forgives whichever of them was worse
    on it. ``TINY`` here stands for the seven parties that won seats outside the
    committed panel's ``reference`` population.
    """
    model = _draws(_MODEL, seed=11)
    assert ACTUAL["TINY"] > 0 and "TINY" not in FIXED, "precondition"

    try:
        S.score_seats(model, ACTUAL, universe=list(FIXED))
    except ValueError as exc:
        assert "TINY" in str(exc), str(exc)
    else:
        raise AssertionError(
            "score_seats accepted a universe with no column for TINY, which won "
            "a seat. The score would have stopped counting a real error and "
            "nothing would have said so.")

    # And the union built by `hold_universe` does contain it, from either side.
    assert "TINY" in S.hold_universe([model], ACTUAL, fixed=FIXED)
    assert "TINY" in S.hold_universe([], ACTUAL, fixed=FIXED)

    # `parties` and `universe` are different operations and may not be given
    # together: one fixes the column ORDER over a forecaster-chosen set, the
    # other fixes the SET. Whichever won would be an argument-order accident.
    held = S.hold_universe([model], ACTUAL, fixed=FIXED)
    try:
        S.score_seats(model, ACTUAL, parties=held, universe=held)
    except ValueError as exc:
        assert "universe" in str(exc) and "parties" in str(exc)
    else:
        raise AssertionError("score_seats accepted both `parties` and "
                             "`universe` and silently picked one")


def test_dropping_a_forecasters_own_claims_is_allowed_counted_and_priced():
    """The other omission IS defensible, so it is recorded rather than refused —
    and the price is asserted as arithmetic, not described.

    A universe of ``reference ∪ seat-winners`` and nothing else forgives phantom
    mass: the model's GHOST columns stop being scored. That is a real choice with
    a real cost, and the cost is exactly the CRPS those columns carried.
    """
    model = _draws(_MODEL, seed=11)
    own = S.score_seats(model, ACTUAL)
    fixed_only = sorted(set(FIXED) | {p for p, s in ACTUAL.items() if s > 0})
    thin = S.score_seats(model, ACTUAL, universe=fixed_only)

    assert thin["dropped_claims"] == ["GHOST_A", "GHOST_B"], thin["dropped_claims"]
    assert own["dropped_claims"] == [], (
        "a forecaster scored on its own set drops nothing by definition")

    forgiven = sum(own["crps"]["per_party"][p] for p in thin["dropped_claims"])
    assert forgiven > 0, (
        f"the ghost columns carried CRPS {forgiven!r}, so this fixture no "
        f"longer prices anything. Phantom mass must cost something or the "
        f"choice being tested is not a choice.")
    assert math.isclose(own["crps"]["total"] - thin["crps"]["total"], forgiven,
                        rel_tol=0, abs_tol=1e-12), (
        f"dropping {thin['dropped_claims']} moved the CRPS total by "
        f"{own['crps']['total'] - thin['crps']['total']!r}, not by the "
        f"{forgiven!r} those columns carried. The two must agree exactly or "
        f"the scored set is not what `dropped_claims` says it is.")


def test_the_variogram_is_the_one_score_that_moves_and_it_is_not_predictable():
    """⛔ AND IT MOVES BOTH WAYS, so no direction may be predicted from ``d``.

    ``variogram_score`` is a MEAN over ``d(d-1)/2`` pairs. A both-zero column
    adds ``d`` non-zero cross terms and ``m(m-1)/2`` zero ones, so

        V(m) = (S + m·C) / [(d+m)(d+m-1)/2]

    rises while ``m < d - 1 - 2S/C`` and falls after it. This test pins both
    limbs on one real forecast: padding a little raises it, padding a lot drives
    it towards zero. A future reader tempted to say "the model is scored over
    more columns, so its variogram is flattered" must fail here. Where the
    crossover actually sits — and the factor of two the old formula had in it —
    is
    ``test_the_variogram_crossover_formula_predicts_the_measured_peak``.
    """
    rng = np.random.default_rng(7)
    truth = np.array([90., 60., 30., 20., 10., 5., 3., 0.])
    samples = np.maximum(0, np.round(rng.normal(
        truth + np.array([5, -4, 2, 0, 3, -1, 1, 2.]),
        np.array([9, 8, 5, 4, 3, 2, 2, 2.]), size=(500, 8))))
    names = [f"P{i}" for i in range(8)]

    def padded(m):
        s = np.hstack([samples, np.zeros((500, m))])
        t = np.concatenate([truth, np.zeros(m)])
        ns = names + [f"Z{i}" for i in range(m)]
        return (S.crps_by_party(s, t, ns)["total"], S.energy_score(s, t),
                S.variogram_score(s, t))

    base = padded(0)
    for m in (5, 20, 50):
        crps, energy, vario = padded(m)
        assert crps == base[0], (m, crps, base[0])
        assert energy == base[1], (m, energy, base[1])
        assert vario != base[2], (
            f"padding by {m} both-zero columns left the variogram at "
            f"{vario!r}. It is a mean over pairs and it cannot be invariant; "
            f"if it is, the normalisation has gone.")

    assert padded(5)[2] > base[2], (
        "a small pad must RAISE the variogram on this fixture — the cross "
        "terms dominate before the pair count does")
    assert padded(50)[2] < base[2] / 2, (
        "a large pad must drive it towards zero — the pair count dominates in "
        "the end")


def test_the_variogram_crossover_formula_predicts_the_measured_peak():
    """⛔ WHERE THE TURN IS, AND THE FORMULA THAT SAID IT WAS TWICE AS FAR.

    ``hold_universe`` states the closed form and the condition for it to rise.
    The form is right — it reproduces ``variogram_score`` to 3e-17 below — and
    until 2026-09-13 the condition beside it read ``m < 2C/V - 2d + 1``, which
    is the continuous condition ``m < C/V(m) - d + ½`` multiplied by two.

    The fix is checked three ways, because a formula that agrees with one
    measurement is fitted to it:

    * the closed form ``V(m) = (S + mC) / [(d+m)(d+m-1)/2]`` reproduces the real
      function exactly, so ``S`` and ``C`` are the right two numbers;
    * the corrected discrete condition ``m < d - 1 - 2S/C`` names the measured
      integer peak on **two fixtures whose peaks are in different places** —
      otherwise it is one coincidence;
    * **the constructed violation**: the OLD condition, pushed through the same
      comparison, must get the peak wrong. If it does not, this fixture cannot
      see the defect and nothing above it means anything.
    """
    def variogram_curve(truth, offsets, sds, seed, n=500):
        rng = np.random.default_rng(seed)
        d = truth.size
        samples = np.maximum(0, np.round(
            rng.normal(truth + offsets, sds, size=(n, d))))
        p = 0.5
        expected = (np.abs(samples[:, :, None]
                           - samples[:, None, :]) ** p).mean(axis=0)
        real = np.abs(truth[:, None] - truth[None, :]) ** p
        iu = np.triu_indices(d, 1)
        S_ = float(((real[iu] - expected[iu]) ** 2).sum())
        # C is the cost of ONE both-zero column: d cross terms, each the gap
        # between the true |y_j - 0|^p and the forecast's E|X_j - 0|^p.
        C_ = float(((np.abs(truth) ** p
                     - (np.abs(samples) ** p).mean(axis=0)) ** 2).sum())
        curve = {}
        for m in range(0, 40):
            s = np.hstack([samples, np.zeros((n, m))])
            t = np.concatenate([truth, np.zeros(m)])
            curve[m] = S.variogram_score(s, t)
        return d, S_, C_, curve

    # Fixture one is the panel above, unchanged: mixed-sign offsets distort the
    # pair gaps, so S is large against C and the turn comes early (m=3).
    # Fixture two is a narrower ladder with a UNIFORM bias, which the pair
    # differences cancel — S collapses, C does not, and the turn moves out to
    # m=5 on six columns instead of eight.
    cases = [
        (np.array([90., 60., 30., 20., 10., 5., 3., 0.]),
         np.array([5, -4, 2, 0, 3, -1, 1, 2.]),
         np.array([9, 8, 5, 4, 3, 2, 2, 2.]), 7),
        (np.array([50., 45., 40., 35., 30., 25.]),
         np.full(6, 3.0), np.full(6, 1.5), 23),
    ]
    peaks = []
    for truth, offsets, sds, seed in cases:
        d, S_, C_, curve = variogram_curve(truth, offsets, sds, seed)

        closed = max(abs(curve[m] - 2 * (S_ + m * C_) / ((d + m) * (d + m - 1)))
                     for m in curve)
        assert closed < 1e-12, (
            f"the closed form V(m) = (S + mC)/[(d+m)(d+m-1)/2] is off by "
            f"{closed!r} from the measured variogram. S and C are then not the "
            f"two numbers the condition is written in and the condition cannot "
            f"be checked at all.")

        peak = max(curve, key=curve.get)
        peaks.append(peak)
        assert 0 < peak < 39, (
            f"the variogram peaks at m={peak}, at the edge of the range "
            f"scanned. A fixture whose turn is not interior cannot locate it.")

        # The corrected condition: V(m+1) > V(m) exactly while m < d - 1 - 2S/C.
        crossover = d - 1.0 - 2.0 * S_ / C_
        assert peak == math.ceil(crossover), (
            f"d={d} S={S_:.4f} C={C_:.4f}: the corrected condition puts the "
            f"last rising step at m<{crossover:.3f}, so the peak should be "
            f"m={math.ceil(crossover)}, and the measured peak is m={peak}.")
        # ...and it is a real turn, not a plateau the ceiling happened to land on
        assert curve[peak] > curve[peak - 1] and curve[peak] > curve[peak + 1]

        # ⛔ THE CONSTRUCTED VIOLATION. The old condition, same S, same C, same
        # comparison. `2C/V - 2d + 1` is self-referential in V, so it is read at
        # the peak, exactly as a reader would have read it.
        old = 2.0 * C_ / curve[peak] - 2.0 * d + 1.0
        assert math.ceil(old) != peak, (
            f"the OLD condition returns {old:.2f} and the measured peak is "
            f"m={peak}, so on this fixture the defect is invisible and the "
            f"assertion above proves nothing. Choose a fixture where the two "
            f"formulas disagree — they always do off m = C/V - d + ½, and the "
            f"old one is that doubled.")
        assert old > crossover, (
            f"the old condition ({old:.2f}) must place the turn FURTHER out "
            f"than the corrected one ({crossover:.2f}) — it is the corrected "
            f"one doubled, and a reader following it pads too far")

    assert peaks[0] != peaks[1], (
        f"both fixtures peak at m={peaks[0]}, so the condition has been checked "
        f"against one number twice. The second fixture exists to move the peak.")


def test_the_committed_panel_is_scored_on_sets_that_differ():
    """The defect on the real artefact, with the population it covers stated.

    Scan-shaped: it reads live repository state, so it must show it scanned the
    right thing and that the thing is non-empty and within a two-sided band.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    records = json.loads(path.read_text())["records"]

    rows = [r for r in records if r.get("n_scored") and r.get("opponents")]
    scanned(rows, of=records, low=0.9, high=1.0,
            what="city-year rows carrying both a model n_scored and opponents",
            denominator="rows in history.json")

    differ = [r for r in rows
              if any(o.get("n_scored") not in (None, r["n_scored"])
                     for o in r["opponents"].values())]
    scanned(differ, of=rows, low=0.75, high=1.0,
            what="city-years where a baseline was scored on a different number "
                 "of columns from the model",
            denominator="city-year rows scanned")

    model_cols = sum(r["n_scored"] for r in rows)
    swing_cols = sum(r["opponents"]["uniform-swing"]["n_scored"] for r in rows
                     if "n_scored" in r["opponents"].get("uniform-swing", {}))
    assert model_cols > 1.5 * swing_cols, (
        f"the model is scored over {model_cols} columns across the panel and "
        f"uniform-swing over {swing_cols}. This test exists because that ratio "
        f"was 580:332; if it has closed, say so in MODEL-LOG rather than "
        f"loosening the assertion.")


# ---------------------------------------------------------------------------
# #15 — the clustered calibration test
# ---------------------------------------------------------------------------


def _fixture_groups(seed, n_city_years, width_mult, shift, replicates=32):
    """PIT columns from the suite's own constructed calibration panel.

    ``test_calibration_report._shift_scale_results`` builds city-years whose
    small parties have a KNOWN width (``width_mult``) and a KNOWN level error
    (``shift``), through the real ``calibration_columns``. It is imported rather
    than copied: a second generator of the same panel is a second definition of
    what "calibrated" means here, and the two would drift.

    The PITs are re-randomised ``replicates`` times from the stored jump
    intervals, because a χ² computed on ONE randomisation is not a stable
    number — on the committed panel a re-roll moves it from 19.3 to 66.2.
    """
    import compare_history as C
    from test_calibration_report import _shift_scale_results

    results = _shift_scale_results(seed, n_city_years, width_mult=width_mult,
                                   shift=shift)
    groups = []
    for r in results:
        block = r["calibration"]["claimed"]
        if not block["pit"]:
            continue
        drawn, exact = C.redraw_pits(block, replicates=replicates)
        assert exact, (
            "redraw_pits fell back to the single stored randomisation, so this "
            "control is testing one re-roll and not the statistic")
        groups.append(drawn)
    assert len(groups) == n_city_years, (
        f"the fixture produced {len(groups)} clusters for {n_city_years} "
        f"city-years. `_shift_scale_results` has changed shape and this "
        f"control no longer constructs what it says it does.")
    return groups


def test_the_clustered_test_does_not_reject_a_calibrated_population():
    """The null control. A test that rejects everything measures nothing."""
    groups = _fixture_groups(4242, 12, width_mult=1.0, shift=0.0)
    n = sum(g.shape[1] for g in groups)
    assert 100 <= n <= 200, (
        f"the calibrated fixture carries {n} claimed columns; the control was "
        f"calibrated at ~144 and a panel an order of magnitude different is "
        f"not the same test")

    result = S.chi2_clustered(groups, draws=4000)
    assert result["estimable"] is True
    assert result["chi2_rs"] < result["chi2_crit_95"], (
        f"χ²_RS {result['chi2_rs']:.2f} against {result['chi2_crit_95']} on a "
        f"population built to be calibrated. The test rejects its own null and "
        f"nothing it says about the model can be read.")
    assert result["rejects_in"] <= 0.15 * result["replicates"], (
        f"{result['rejects_in']}/{result['replicates']} randomisations reject a "
        f"calibrated population, against a nominal 5%")


def test_the_clustered_test_rejects_a_population_built_to_be_wrong():
    """The positive control, on both kinds of wrong.

    A shifted forecast and a forecast of the wrong width fail uniformity for
    different reasons, and a test that saw only one of them would pass this
    suite while being blind to half of what it is quoted for.
    """
    for label, kwargs, floor in (
            ("shifted +2 seats", {"width_mult": 1.0, "shift": 2.0}, 80.0),
            ("1.6x too wide", {"width_mult": 1.6, "shift": 0.0}, 25.0),
            ("0.5x too narrow", {"width_mult": 0.5, "shift": 0.0}, 40.0)):
        result = S.chi2_clustered(_fixture_groups(4242, 12, **kwargs),
                                  draws=4000)
        assert result["chi2_rs"] > max(floor, result["chi2_crit_95"]), (
            f"{label}: χ²_RS {result['chi2_rs']:.2f} against a critical value "
            f"of {result['chi2_crit_95']} and an expected floor of {floor}. "
            f"The clustering correction has swallowed a real fault.")
        assert result["rejects_in"] == result["replicates"], (
            f"{label}: only {result['rejects_in']}/{result['replicates']} "
            f"randomisations reject a population built to be non-uniform")


def test_the_correction_rescues_a_clustered_population_the_nominal_test_fails():
    """⛔ THE CONTROL ON THE CORRECTION ITSELF, not merely on the statistic.

    The two controls above would both pass if ``chi2_clustered`` ignored the
    design effect entirely and printed Pearson's χ². What the correction is FOR
    is a population whose columns are correlated inside their clusters but still
    uniform marginally: the nominal test rejects it falsely and the corrected
    one must not.

    Built with a Gaussian copula — each city-year draws one latent ``z`` and
    each column is ``Phi(rho·z + sqrt(1-rho²)·e)``, which is exactly U(0,1)
    marginally whatever ``rho`` is. Constructed rather than observed: no state
    of this repository is the premise.
    """
    def panel(rho, seed=7, k=24, per=15, replicates=16):
        rng = np.random.default_rng(seed)
        phi = np.vectorize(lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0))))
        out = []
        for _ in range(k):
            z = rng.normal(size=(replicates, 1))
            e = rng.normal(size=(replicates, per))
            out.append(np.clip(phi(rho * z + math.sqrt(1 - rho * rho) * e),
                               1e-9, 1 - 1e-9))
        return out

    independent = S.chi2_clustered(panel(0.0), draws=2000)
    clustered = S.chi2_clustered(panel(0.85), draws=2000)
    crit = independent["chi2_crit_95"]

    assert abs(independent["deff"] - 1.0) < 0.25, (
        f"design effect {independent['deff']:.2f} on independent columns. It "
        f"must be ~1 there or the estimator is measuring something else.")
    assert independent["chi2_rs"] < crit, independent["chi2_rs"]

    assert clustered["chi2"] > crit, (
        f"the NOMINAL χ² reads {clustered['chi2']:.2f} against {crit} on a "
        f"clustered-but-uniform population, so it does not reject and this "
        f"control proves nothing. Raise rho or the columns per cluster — do "
        f"not weaken the assertion below.")
    assert clustered["deff"] > 2.0, (
        f"design effect {clustered['deff']:.2f} on columns correlated at "
        f"rho=0.85. The correction is inert.")
    assert clustered["chi2_rs"] < crit, (
        f"χ²_RS {clustered['chi2_rs']:.2f} against {crit}: the correction did "
        f"not rescue a population that is uniform by construction, so a "
        f"rejection it reports on the real panel cannot be distinguished from "
        f"this artefact.")


def _top_decile_panel(k=24, per=24, replicates=16, seed=5, qs=(0.02, 0.18)):
    """Clusters whose dependence lives ONLY in the top PIT decile.

    Each cluster draws a share ``q`` of its columns for the top decile from
    ``qs`` and spreads the rest over ``[0, 0.9)``. With ``qs`` a spread pair the
    top-decile count is over-dispersed between clusters and the other nine bins
    are not; with ``qs`` a constant pair nothing is, and the same generator is
    the null. Constructed, so no state of this repository is its premise.
    """
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(k):
        rows = []
        for _ in range(replicates):
            q = qs[int(rng.integers(0, len(qs)))]
            n_top = int(rng.binomial(per, q))
            rows.append(np.concatenate([rng.uniform(0.9, 1.0, n_top),
                                        rng.uniform(0.0, 0.9, per - n_top)]))
        out.append(np.array(rows))
    return out


def test_the_cell_design_effects_are_the_replicate_mean_not_one_randomisation():
    """⛔ δ̄ AND ITS CELLS MUST DESCRIBE THE SAME QUANTITY. They did not.

    ``deff`` is averaged over the R randomisations; ``deff_cells`` used to store
    the FIRST one. On the committed ``reference`` population the stored cells
    averaged 1.115 while ``deff`` read 1.072, and single-randomisation cells
    move by up to 0.5 — so the two numbers printed side by side were estimates
    of the same thing from different samples.

    The check is an exact identity rather than a re-implementation: ``deff`` is
    ``Σ(1-p₀)d_k/(B-1)``, LINEAR in the cells, so the replicate mean of the
    cells reproduces it to floating point and the first randomisation's cells do
    not. The constructed violation is the r=0 vector itself, obtained by asking
    the same function for a one-replicate run, and pushed through the same
    identity.
    """
    groups = _top_decile_panel(replicates=24, seed=11)
    bins, p0 = 10, 0.1
    full = S.chi2_clustered(groups, bins=bins, draws=2000)

    assert len(full["deff_cells"]) == bins
    assert len(full["deff_cells_sd"]) == bins
    assert full["replicates"] == 24

    identity = (1.0 - p0) * sum(full["deff_cells"]) / (bins - 1)
    assert math.isclose(identity, full["deff"], rel_tol=0, abs_tol=1e-12), (
        f"Σ(1-p₀)·deff_cells/(B-1) is {identity!r} and `deff` is "
        f"{full['deff']!r}. `deff` is linear in the cells, so these agree "
        f"exactly when the cells are the replicate MEAN and not otherwise. "
        f"They are then two estimates of one quantity and only one is printed "
        f"with its provenance.")

    # ...and the identity is not vacuous: the replicates genuinely disagree, so
    # a first-randomisation vector would be a different vector.
    assert max(full["deff_cells_sd"]) > 0.05, (
        f"the cell design effects vary by at most "
        f"{max(full['deff_cells_sd']):.4f} across randomisations, so storing "
        f"one of them would have been harmless and this test is asserting "
        f"nothing. The fixture has stopped reproducing the defect.")

    # ⛔ THE CONSTRUCTED VIOLATION: the r=0 cells, through the same identity.
    r_zero = S.chi2_clustered([b[:1] for b in groups], bins=bins, draws=500)
    wrong = (1.0 - p0) * sum(r_zero["deff_cells"]) / (bins - 1)
    assert abs(wrong - full["deff"]) > 0.02, (
        f"the first randomisation's cells give {wrong!r} against a "
        f"replicate-averaged `deff` of {full['deff']!r}, a gap of "
        f"{abs(wrong - full['deff']):.4f}. The detector cannot see the defect "
        f"it was written for at this gap — raise the replicate count or the "
        f"between-cluster spread rather than lowering this bound.")


def test_the_design_effect_localises_to_the_cells_the_dependence_is_in():
    """⛔ CAN THE CELL ESTIMATOR SEE WHERE THE CLUSTERING IS? Constructed, both ways.

    The finding on the real panel is that δ̄ ≈ 1 is an average over cells running
    0.11 to 2.84, with the high ones in the high PIT bins. That reading is worth
    nothing unless the per-cell estimator can actually localise dependence, so
    it is given a panel where the dependence is in the top decile **by
    construction** and a null from the same generator where there is none.
    """
    hit = S.chi2_clustered(_top_decile_panel(), draws=2000)
    null = S.chi2_clustered(_top_decile_panel(qs=(0.10, 0.10)), draws=2000)

    cells, others = hit["deff_cells"], hit["deff_cells"][:-1]
    assert cells[-1] > 2.0, (
        f"the top cell reads {cells[-1]:.2f} on a panel whose top-decile count "
        f"is over-dispersed between clusters by construction. The estimator "
        f"cannot see a design effect it was handed.")
    assert max(others) < 1.4, (
        f"the nine cells with no cluster-level over-dispersion read up to "
        f"{max(others):.2f}. The estimator is smearing dependence across cells "
        f"and the pattern measured on the real panel cannot be read as "
        f"localisation.")
    assert cells[-1] > 2.0 * max(others), (cells,)

    # The null: the SAME generator with the cluster-level spread removed.
    assert max(null["deff_cells"]) < 1.4 and abs(null["deff"] - 1.0) < 0.15, (
        f"cells {[round(v, 2) for v in null['deff_cells']]} and δ̄ "
        f"{null['deff']:.2f} on a panel with no between-cluster spread at all. "
        f"Every cell must sit near 1 there or a high cell means nothing.")
    # And δ̄ hides it in exactly the way the docstring says: one cell at 2.4+
    # while the mean is barely off 1.
    assert hit["deff"] < 1.4 < cells[-1], (hit["deff"], cells[-1])


def test_the_high_pit_cells_carry_the_clustering_on_the_committed_panel():
    """⛔ DEFECT: THE OLD EXPLANATION OF δ̄ ≈ 1 PREDICTED THE WRONG SIGN.

    The record said council seats are zero-sum, so within-city-year errors are
    negatively correlated, pushing the between-cluster variance DOWN. That
    predicts δ̄ < 1 and every measured δ̄ is ≥ 1 (1.07, 1.01, 1.13, 1.06).

    What is true is the cell pattern: the low and middle cells do run below 1 —
    the zero-sum intuition is right there — and the high ones run 1.2 to 2.8. A
    high PIT is the truth landing above the forecast, i.e. a party the model
    UNDER-forecast, which is this model's dominant failure, and it arrives a
    whole city-year at a time. **The clustering is concentrated in the failure
    mode**, which is why the mean is the wrong summary and why the Satterthwaite
    form below has to be computed rather than assumed.

    ``claimed`` is asserted to be the EXCEPTION, not skipped: its selection rule
    drops the under-forecast columns before they can cluster, so its top decile
    is nearly empty and its top cell is the lowest of the ten.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    import compare_history as C

    records = json.loads(path.read_text())["records"]
    groups, mass = {}, {}
    for pop in ("reference", "seat_holders", "claimed"):
        blocks, hist = [], np.zeros(10)
        for r in records:
            block = (r.get("calibration") or {}).get(pop)
            if not block or not block["pit"]:
                continue
            drawn, exact = C.redraw_pits(block, replicates=64)
            assert exact, f"{pop}: the artefact predates the stored PIT jumps"
            blocks.append(drawn)
            for rep in range(drawn.shape[0]):
                hist += np.histogram(drawn[rep], bins=10, range=(0.0, 1.0))[0]
        scanned(blocks, of=records, low=0.9, high=1.0,
                what=f"city-years contributing a `{pop}` PIT block",
                denominator="rows in history.json")
        groups[pop] = S.chi2_clustered(blocks)
        mass[pop] = hist / hist.sum()

    for pop, lo_max, hi_min in (("reference", 1.0, 1.2),
                                ("seat_holders", 0.9, 1.4)):
        cells = np.array(groups[pop]["deff_cells"])
        bottom, top = cells[:5].mean(), cells[5:].mean()
        assert bottom < lo_max < hi_min < top, (
            f"`{pop}` cell design effects {[round(v, 2) for v in cells]}: the "
            f"bottom five average {bottom:.2f} and the top five {top:.2f}. "
            f"Measured 0.77/1.37 on `reference` and 0.42/1.85 on "
            f"`seat_holders`. The finding is that the clustering sits in the "
            f"HIGH cells; if the sides have swapped, the explanation in "
            f"`chi2_clustered` has to be rewritten again rather than kept.")
        assert top > 1.4 * bottom, (bottom, top)
        # The trend itself, as a correlation rather than a two-group split.
        trend = float(np.corrcoef(np.arange(10.0), cells)[0, 1])
        assert trend > 0.5, (
            f"`{pop}`: corr(bin index, cell deff) is {trend:+.3f} against a "
            f"measured +0.71 on `reference` and +0.90 on `seat_holders`")
        # ...and the population really is top-heavy, which is what makes a high
        # cell there a statement about the model's failure mode.
        assert mass[pop][-1] > mass[pop][0], (
            f"`{pop}` holds {mass[pop][-1]:.1%} of its PIT mass in the top "
            f"decile against {mass[pop][0]:.1%} in the bottom. The reading "
            f"'high PIT = under-forecast = this model's dominant failure' "
            f"needs the histogram to be top-heavy and it is not.")

    # ⛔ AND `claimed` IS THE EXCEPTION, BY THE SAME SELECTION RULE THE
    # CLAIM_FRACTION note prices. Its top decile is nearly empty.
    claimed = np.array(groups["claimed"]["deff_cells"])
    assert claimed[-1] == claimed.min(), (
        f"`claimed` cells {[round(v, 2) for v in claimed]}: its top cell is no "
        f"longer the lowest. The measured value is 0.35, and the reason is "
        f"that the rule drops the under-forecast columns before they can "
        f"cluster — if that has changed, so has the objection to leading with "
        f"`claimed`.")
    assert mass["claimed"][-1] < 0.4 * mass["reference"][-1], (
        f"`claimed` carries {mass['claimed'][-1]:.1%} of its mass in the top "
        f"decile against `reference`'s {mass['reference'][-1]:.1%} (measured "
        f"2.3% against 12.4%)")


def test_the_satterthwaite_correction_is_computed_and_the_rejection_survives():
    """⛔ FIRST-ORDER ASSUMES THE CELLS ARE HOMOGENEOUS AND THEY ARE NOT.

    Rao & Scott's first-order correction divides χ² by the MEAN cell design
    effect. On this panel that mean is an average over cells running 0.11 to
    2.84, so whether first order is adequate is a question with an answer and it
    was left unanswered. The second-order (Satterthwaite) form divides again by
    ``1 + cv²`` and reads the result against χ² on ``(B-1)/(1+cv²)`` dof.

    Measured on the committed artefact, R=64: cv² 0.177 / 0.279 / 0.572 / 0.156,
    adjusted statistics 27.46 / 32.17 / 70.42 / 20.50 against adjusted criticals
    15.04 / 14.16 / 12.19 / 15.23, on ``reference`` / ``claimed`` /
    ``seat_holders`` / ``all``. **First order is adequate; the rejection stands
    on both quotable populations.**
    """
    # The mechanism first, constructed: heterogeneous cells must shrink both the
    # statistic and the dof, homogeneous ones must leave them alone.
    het = S.chi2_clustered(_top_decile_panel(), draws=2000)
    hom = S.chi2_clustered(_top_decile_panel(qs=(0.10, 0.10)), draws=2000)
    assert het["deff_cv2"] > 2.0 * hom["deff_cv2"], (
        f"cv² is {het['deff_cv2']:.3f} on cells built to be heterogeneous and "
        f"{hom['deff_cv2']:.3f} on cells built to be uniform. cv² is the whole "
        f"input to the second-order form; if it cannot tell those apart the "
        f"correction is inert.")
    assert het["chi2_satt"] < het["chi2_rs"] and het["dof_satt"] < het["dof"]
    assert math.isclose(het["dof_satt"], het["dof"] / (1.0 + het["deff_cv2"]),
                        rel_tol=0.05), (het["dof_satt"], het["deff_cv2"])
    assert het["chi2_satt_crit_95"] < het["chi2_crit_95"], (
        "fewer degrees of freedom must lower the critical value too — an "
        "adjusted statistic read against the unadjusted critical value is the "
        "correction applied to one side only")

    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    import compare_history as C
    records = json.loads(path.read_text())["records"]

    expected = {"reference": (0.177, 27.46, 15.04),
                "claimed": (0.279, 32.17, 14.16)}
    for pop, (cv2, stat, crit) in expected.items():
        blocks = []
        for r in records:
            block = (r.get("calibration") or {}).get(pop)
            if not block or not block["pit"]:
                continue
            drawn, exact = C.redraw_pits(block, replicates=64)
            assert exact
            blocks.append(drawn)
        scanned(blocks, of=records, low=0.9, high=1.0,
                what=f"city-years contributing a `{pop}` PIT block",
                denominator="rows in history.json")
        result = S.chi2_clustered(blocks)

        assert math.isclose(result["deff_cv2"], cv2, rel_tol=0.25), (
            f"`{pop}` cv² {result['deff_cv2']:.3f} against a measured {cv2}. "
            f"The cell heterogeneity has moved and the size of the "
            f"second-order correction with it.")
        assert math.isclose(result["chi2_satt"], stat, rel_tol=0.25), (
            f"`{pop}` Satterthwaite χ² {result['chi2_satt']:.2f} against a "
            f"measured {stat}")
        assert math.isclose(result["chi2_satt_crit_95"], crit, rel_tol=0.10), (
            f"`{pop}` adjusted critical {result['chi2_satt_crit_95']:.2f} "
            f"against a measured {crit}")
        assert result["chi2_satt"] > result["chi2_satt_crit_95"], (
            f"`{pop}`: the rejection does NOT survive the second-order "
            f"correction — χ² {result['chi2_satt']:.2f} against "
            f"{result['chi2_satt_crit_95']:.2f}. That is a change to what this "
            f"repository may claim about calibration and belongs in MODEL-LOG "
            f"before this assertion is touched.")
        assert result["rejects_satt"] == result["replicates"], (
            f"`{pop}`: {result['rejects_satt']}/{result['replicates']} "
            f"randomisations reject after the second-order correction")
        # first order is ADEQUATE, which is the claim being recorded: the two
        # corrections agree about the verdict, they are not close in value
        assert result["chi2_rs"] > result["chi2_crit_95"], "first order too"


def test_the_fractional_dof_critical_value_matches_an_exact_computation():
    """The Satterthwaite dof is not a whole number, so the table is interpolated.

    Pinned against an exact inverse of the regularised incomplete gamma,
    bisected to 1e-12 and verified to reproduce every entry of ``_CHI2_95`` at
    integer dof. Those exact values are LITERALS here rather than a second
    implementation: a routine that computed them in the test would be a second
    definition of the critical value, which is the failure ``column_rng``
    exists for.
    """
    exact = {1.45: 4.8734, 2.50: 6.9281, 5.00: 11.0705, 5.74: 12.2010,
             6.92: 13.9505, 7.67: 15.0355, 7.80: 15.2217, 9.00: 16.9190,
             12.50: 21.6958, 19.50: 30.7779}
    worst = 0.0
    for dof, truth in exact.items():
        got = S.chi2_crit_95(dof)
        assert got is not None, dof
        worst = max(worst, abs(got - truth))
        bound = 0.07 if dof < 5 else 0.01
        assert abs(got - truth) <= bound, (
            f"chi2_crit_95({dof}) = {got:.4f} against an exact {truth:.4f}, a "
            f"gap of {abs(got - truth):.4f} over a bound of {bound}. The "
            f"docstring's claim is 0.066 worst at dof 1.45 and under 0.01 for "
            f"dof >= 5; if that no longer holds the interpolation has to be "
            f"replaced, not the bound.")
    assert worst > 0.01, (
        f"the worst gap across the pinned values is {worst:.5f}, so this test "
        f"would pass against an exact implementation and against a broken one "
        f"alike. It exists to bound a KNOWN approximation error and must "
        f"include a point where that error is visible.")

    # Integer dof must come back as the table itself, not as an interpolation of
    # it — the table is the single definition and this is its extension.
    for dof, value in S._CHI2_95.items():
        assert S.chi2_crit_95(dof) == value, dof
        assert S.chi2_crit_95(float(dof)) == value, dof
    # Monotone, and refusing to extrapolate.
    grid = [1.0 + 0.25 * i for i in range(77)]
    values = [S.chi2_crit_95(d) for d in grid]
    assert all(b > a for a, b in zip(values, values[1:])), "not monotone in dof"
    for outside in (0.0, 0.99, 20.01, 45.0, None):
        assert S.chi2_crit_95(outside) is None, (
            f"chi2_crit_95({outside}) returned a value. Outside the table an "
            f"extrapolated critical value is a fabrication and None is the "
            f"honest answer.")


def test_clustering_by_cycle_is_the_level_this_panel_cannot_test():
    """⛔ THE LIMITATION ON THE WHOLE RESULT, AS NUMBERS RATHER THAN A CAVEAT.

    ``compare_history`` clusters by CITY-YEAR, and at that level the correction
    buys almost nothing (δ̄ 1.07). But the panel is 8 cities × 3 CYCLES and the
    cycle effect is the large one — on ``reference``, sd(z) runs 0.601 / 0.889 /
    1.265 pooled across 2011 / 2016 / 2021, and 0.452 / 1.155 / 1.960 on the
    ranks 4-12 band, which is what §1.228 quotes. **Band and pooled are
    different populations and both are correct**; the assertion below is on the
    pooled figure because that is what this file computes. Re-clustered on year the design effect is
    1.5 to 2.2, and on ``reference`` and ``all`` the rejection stops being
    established by this function's own rule.

    **So the quotable statement is "clustering at the CITY-YEAR level buys
    almost nothing", never "the clustering correction buys almost nothing".**

    And k=3 is refused by default for a reason this test also pins: three
    clusters give each cell two degrees of freedom and the cell estimates blow
    up. The year-level numbers are a warning about the panel, not a test of the
    model, and ``min_clusters`` has to be lowered deliberately to see them.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    import compare_history as C
    records = json.loads(path.read_text())["records"]

    by_city_year, by_cycle, sd_by_cycle = {}, {}, {}
    for pop in ("reference", "all"):
        blocks, years = [], {}
        for r in records:
            block = (r.get("calibration") or {}).get(pop)
            if not block or not block["pit"]:
                continue
            drawn, exact = C.redraw_pits(block, replicates=64)
            assert exact
            blocks.append(drawn)
            years.setdefault(r["year"], []).append(drawn)
            if pop == "reference":
                sd_by_cycle.setdefault(r["year"], []).extend(
                    float(z) for z in block["z"] if z is not None)
        scanned(blocks, of=records, low=0.9, high=1.0,
                what=f"city-years contributing a `{pop}` PIT block",
                denominator="rows in history.json")
        assert len(years) == 3, sorted(years)
        by_city_year[pop] = S.chi2_clustered(blocks)
        cycles = [np.hstack(v) for _, v in sorted(years.items())]
        # The default floor REFUSES this, which is the point of the floor.
        refused = S.chi2_clustered(cycles)
        assert refused["estimable"] is False and refused["clusters"] == 3
        assert math.isnan(refused["deff"]) and math.isnan(refused["chi2_rs"])
        assert refused["min_clusters"] == 8
        by_cycle[pop] = S.chi2_clustered(cycles, min_clusters=3)
        assert by_cycle[pop]["estimable"] is True

    # The cycle effect that says the level is wrong.
    sds = {y: float(np.std(v, ddof=1)) for y, v in sd_by_cycle.items()}
    ordered = [sds[y] for y in sorted(sds)]
    assert ordered[-1] > 1.8 * ordered[0], (
        f"sd(z) by cycle is {[round(v, 3) for v in ordered]} across "
        f"{sorted(sds)} (measured 0.601 / 0.889 / 1.265 POOLED; §1.228's "
        f"0.452 / 1.155 / 1.960 is the ranks 4-12 band of the same "
        f"population, a 4.3x spread against this 2.1x). The cycle effect is "
        f"the whole reason city-year is suspected of being the wrong cluster "
        f"level; if it has gone, so has this limitation.")

    for pop in ("reference", "all"):
        near, cycle = by_city_year[pop], by_cycle[pop]
        assert near["deff"] < 1.2 < 1.4 < cycle["deff"], (
            f"`{pop}` δ̄ is {near['deff']:.2f} clustered by city-year and "
            f"{cycle['deff']:.2f} clustered by cycle (measured 1.07 against "
            f"1.61 on `reference`, 1.06 against 1.47 on `all`). The gap "
            f"between the two IS the limitation; without it there is nothing "
            f"to record.")
        assert cycle["rejects_in"] < cycle["replicates"], (
            f"`{pop}` rejects in {cycle['rejects_in']}/{cycle['replicates']} "
            f"randomisations at the cycle level (measured 51/64 and 35/64), so "
            f"it is NOT established there by this function's own rule. If it "
            f"now is, the limitation has weakened and the docstring should say "
            f"so rather than this assertion being deleted.")
    # `claimed` is the population that does survive the move, and saying which
    # ones do is the difference between a caveat and a finding.
    assert by_city_year["reference"]["rejects_in"] == 64, "precondition"


def _resampler_definitions(directory) -> list[str]:
    """Module basenames under ``directory`` that DEFINE a cluster resampler.

    Factored out of the scan below so the identical glob, read and predicate can
    be run over a CONSTRUCTED directory. That is the only way this guard can be
    shown to see a fourth implementation, since adding one to ``src/`` to find
    out is not available to a test.

    It matches a definition and deliberately not a call: the 2026-09-13
    consolidation turned ``compare_history``'s definition into two call sites,
    and a predicate that counted those would report the debt as never repaid.
    """
    return sorted(p.name for p in sorted(Path(directory).glob("*.py"))
                  if "def cluster_bootstrap" in p.read_text()
                  or "def _cluster_bootstrap" in p.read_text())


def test_there_is_one_cluster_resampler_in_the_repository_not_two():
    """One resampler, however many call sites — and the count is asserted.

    ``score.cluster_bootstrap`` is the definition. ``compare_history`` held a
    private copy, ``_cluster_bootstrap_ci``, which was this function pinned to
    the pooled mean; on **2026-09-13 it was deleted** and both of its call sites
    now call into ``score``. The two were shown bit-for-bit identical before the
    deletion — same float, same hex, same degenerate ``nan`` — and the whole
    ``pooled_calibration`` output was diffed across ~60 intervals afterwards
    with no number moving. **So ``score.cluster_bootstrap`` is now the single
    definition for those two, and the remaining debt runs one way: towards
    ``theta_residual``.**

    ``theta_residual.cluster_bootstrap`` is still a genuine third
    implementation — the same scheme specialised to ``sd(residual)``: resample
    metro-years, recompute, take percentiles. It is ``score.cluster_bootstrap``
    with a ``statistic`` and should become a call to it when that file is next
    opened, which is another piece of work.

    The assertion is an equality on a NAMED SET, not a floor or an "at most
    one". A fourth implementation must turn it red; so must a silent rename that
    hides ``theta_residual``'s; and so must a disappearance, which means a
    consolidation this test should be updated to describe in the same commit.
    Both of those are demonstrated below on a constructed directory rather than
    asserted.
    """
    modules = sorted((ROOT / "src").glob("*.py"))
    scanned(modules, of=modules, low=1.0, high=1.0,
            what="modules scanned for a cluster resampler",
            denominator="`.py` files in src/")
    defining = _resampler_definitions(ROOT / "src")
    assert set(defining) == {"score.py", "theta_residual.py"}, (
        f"cluster resamplers are defined in {sorted(defining)}, against the "
        f"two recorded here. The definition belongs in score.py; "
        f"theta_residual.py is known debt with a named owner. A NEW one is a "
        f"second definition of a published interval — the failure mode "
        f"score.column_rng exists for — and a DISAPPEARANCE means a "
        f"consolidation that this test should be updated to describe, in the "
        f"same commit, as it was for compare_history.py on 2026-09-13.")

    # ⛔ CAN THE SCAN SEE ONE ARRIVE, AND ONE GO? Same glob, same read, same
    # predicate, over a directory built for the purpose. Without this the
    # assertion above is a passing state of the tree asserting itself.
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / "score.py").write_text(
            "def cluster_bootstrap(groups, statistic=None):\n    return {}\n")
        (tmp / "theta_residual.py").write_text(
            "def cluster_bootstrap(rows, rng):\n    return 0.0, 1.0\n")
        # A CALL SITE IS NOT A DEFINITION. This is the shape compare_history has
        # now, and counting it would report the consolidation as never done.
        (tmp / "innocent.py").write_text(
            "import score as S\n\n"
            "def summarise(groups):\n    return S.cluster_bootstrap(groups)\n")
        assert _resampler_definitions(tmp) == ["score.py",
                                               "theta_residual.py"], (
            f"the scan reads {_resampler_definitions(tmp)} on a constructed "
            f"directory holding two definitions and one call site. It is "
            f"counting the wrong thing, so what it says about src/ is not what "
            f"it claims to say.")

        # a fourth arrives
        (tmp / "newcomer.py").write_text(
            "def _cluster_bootstrap_ci(groups):\n    return 0.0, 1.0, 20000\n")
        arrived = _resampler_definitions(tmp)
        assert arrived == ["newcomer.py", "score.py", "theta_residual.py"], (
            f"a fourth implementation was written into the scanned directory "
            f"and the scan returned {arrived}. The guard cannot see the thing "
            f"it exists to catch.")
        assert set(arrived) != {"score.py", "theta_residual.py"}, (
            "...and the assertion above would therefore have failed, which is "
            "the half that matters")

        # ...and a silent rename hides one, which must be equally visible
        (tmp / "newcomer.py").unlink()
        (tmp / "theta_residual.py").write_text(
            "def bootstrap_over_metro_years(rows, rng):\n    return 0.0, 1.0\n")
        renamed = _resampler_definitions(tmp)
        assert renamed == ["score.py"], (
            f"theta_residual's resampler was renamed and the scan returned "
            f"{renamed}. A rename must turn this red — otherwise the debt can "
            f"be hidden from the test that tracks it by editing one line.")

    # ``compare_history`` must hold no copy AND must still be using the shared
    # one. Only the first half is covered by the set equality: a module that
    # deleted its copy and then stopped calling anything would pass that and
    # have quietly dropped a published interval.
    source = (ROOT / "src" / "compare_history.py").read_text()
    calls = len(re.findall(r"(?<!def )\bcluster_bootstrap\(", source))
    assert calls >= 2, (
        f"compare_history calls a cluster resampler {calls} times. Its own "
        f"copy was deleted on 2026-09-13 in favour of two calls into score; "
        f"if those have gone too, an interval the report publishes is no "
        f"longer being computed.")
    import compare_history as C
    assert not hasattr(C, "_cluster_bootstrap_ci"), (
        "compare_history._cluster_bootstrap_ci is back. It was deleted as a "
        "duplicate of score.cluster_bootstrap after the two were shown "
        "bit-for-bit identical; a reappearance is the duplication returning.")

    rng = np.random.default_rng(3)
    groups = [rng.random(n) for n in (7, 11, 4, 15, 9, 6, 12, 8, 5, 10)]
    mine = S.cluster_bootstrap(groups)
    assert mine["clusters"] == 10 and mine["n"] == sum(len(g) for g in groups)
    # It refuses to invent an interval from one cluster, which is the shape the
    # three-city-year panel had when this question was first asked.
    assert math.isnan(S.cluster_bootstrap(groups[:1])["lo"])

    # ⛔ THE INTERVAL ITSELF, IN HEX. Until 2026-09-13 this was guarded by a
    # cross-check against compare_history's independent copy, bit for bit. The
    # consolidation removed the second implementation and with it the only
    # thing that would have noticed score.cluster_bootstrap drifting, so the
    # value it produced at the moment of consolidation is pinned instead.
    # Measured on THIS fixture; a tolerance here would be the drift the
    # cross-check existed to stop.
    assert (mine["lo"].hex(), mine["hi"].hex(), mine["draws"]) == (
        "0x1.e0588928f4da3p-2", "0x1.212ae725d383fp-1", 20000), (
        f"score.cluster_bootstrap returns [{mine['lo']!r}, {mine['hi']!r}] on "
        f"the pinned fixture, against the [0.46908773720243796, "
        f"0.564780448310337] it returned when compare_history's independent "
        f"copy was deleted in its favour. Nothing else now checks this number.")


def test_the_bootstrap_resamples_city_years_and_not_columns():
    """⛔ THE DEFINING PROPERTY, CONSTRUCTED — and the one that is invisible.

    A bootstrap that resamples COLUMNS returns an interval far too tight and
    looks entirely healthy doing it: same shape, same centre, a plausible width.
    Nothing downstream would notice, and the figure it produced would be quoted.

    So build clusters that differ from each other far more than their members
    differ inside them — the shape of a real panel, where a city-year shares a
    turnout draw and a national swing — and require the cluster interval to be
    much wider than the column one. The column bootstrap is written out in full
    here on purpose: it is the WRONG answer, and a test needs it present to
    show the right one is not it.
    """
    rng = np.random.default_rng(31)
    offsets = rng.normal(0.0, 1.0, size=12)
    groups = [rng.normal(off, 0.05, size=16) for off in offsets]

    clustered = S.cluster_bootstrap(groups, draws=4000, seed=5)
    flat = np.concatenate(groups)
    naive = rng.choice(flat, size=(4000, flat.size), replace=True).mean(axis=1)
    naive_width = float(np.percentile(naive, 97.5) - np.percentile(naive, 2.5))
    cluster_width = clustered["hi"] - clustered["lo"]

    assert naive_width > 0, "the column bootstrap produced no interval at all"
    # The expected ratio here is sqrt(n_total / k) = sqrt(192/12) = 4: the
    # cluster bootstrap has 12 independent units and the column one thinks it
    # has 192. The bound is set at 3 so that noise cannot decide the test, and
    # it is a bound on a RATIO rather than on a width so it does not go stale
    # when the fixture's scale changes.
    assert cluster_width > 3 * naive_width, (
        f"the cluster interval is {cluster_width:.4f} wide and a column "
        f"bootstrap of the same values is {naive_width:.4f}, a ratio of "
        f"{cluster_width / naive_width:.2f} against an expected 4. On clusters "
        f"whose between variance dwarfs their within variance the two cannot "
        f"be close; if they are, this function is resampling columns and every "
        f"interval it has ever produced is too tight.")
    assert clustered["clusters"] == 12 and clustered["n"] == 192
    assert math.isclose(clustered["point"], float(flat.mean()), rel_tol=1e-12)


def test_the_clustered_test_refuses_to_estimate_a_design_effect_it_cannot():
    """Eight clusters is the floor, and below it the result says so.

    The question "does the PIT histogram reject uniformity" was first asked on
    a THREE city-year panel. Three clusters cannot estimate ten cell design
    effects, and a number printed there would have been a fabrication — so the
    honest output is ``estimable: False``, not a smaller number.
    """
    rng = np.random.default_rng(21)
    tiny = [rng.random((8, 22)) for _ in range(3)]
    result = S.chi2_clustered(tiny)
    assert result["estimable"] is False
    assert math.isnan(result["chi2_rs"]) and math.isnan(result["deff"])
    assert result["clusters"] == 3

    # ...and it DOES estimate at eight, so the floor is a floor and not a wall.
    enough = S.chi2_clustered([rng.random((8, 22)) for _ in range(8)])
    assert enough["estimable"] is True
    assert enough["clusters"] == 8 and not math.isnan(enough["deff"])


def test_the_committed_panel_still_rejects_uniformity_once_clustered():
    """The measured answer, pinned. **It rejects — the fear was not borne out.**

    The nominal test was quoted as settled and was not: the columns cluster
    inside city-years and the nominal p is the independent one. Corrected, the
    design effect comes out at ≈1 and the rejection stands on both populations
    that may be quoted.

    ⚠️ **δ̄ ≈ 1 IS AN AVERAGE AND NOT A DESCRIPTION OF ANY CELL**, and this
    docstring used to explain it with a mechanism that predicts the wrong sign
    (zero-sum councils ⇒ negative within-cluster correlation ⇒ δ̄ < 1, against
    four measured values all ≥ 1). What the cells say, and why it matters, is
    ``test_the_high_pit_cells_carry_the_clustering_on_the_committed_panel``;
    whether the first-order form is adequate given that spread is
    ``test_the_satterthwaite_correction_is_computed_and_the_rejection_survives``;
    and the limitation that this is the city-year level and not the cycle level
    is ``test_clustering_by_cycle_is_the_level_this_panel_cannot_test``. **This
    test is the city-year headline alone and must not be quoted without them.**
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    import compare_history as C

    records = json.loads(path.read_text())["records"]
    measured = {}
    for pop in ("reference", "claimed"):
        groups = []
        for r in records:
            block = (r.get("calibration") or {}).get(pop)
            if not block or not block["pit"]:
                continue
            drawn, exact = C.redraw_pits(block, replicates=64)
            assert exact, f"{pop}: the artefact predates the stored PIT jumps"
            groups.append(drawn)
        scanned(groups, of=records, low=0.9, high=1.0,
                what=f"city-years contributing a `{pop}` PIT block",
                denominator="rows in history.json")
        measured[pop] = S.chi2_clustered(groups)

    for pop, result in measured.items():
        crit = result["chi2_crit_95"]
        assert result["estimable"] is True
        assert 0.5 < result["deff"] < 2.0, (
            f"`{pop}` design effect {result['deff']:.2f}. The measured figures "
            f"are 1.07 on `reference` and 1.01 on `claimed`; a value outside "
            f"this band means the panel's dependence structure has changed and "
            f"the reported rejection has to be re-argued, not re-asserted.")
        assert result["chi2_rs"] > crit, (
            f"`{pop}`: χ²_RS {result['chi2_rs']:.2f} against {crit}. The "
            f"measured figures are 32.33 and 41.05. If this has fallen below "
            f"the critical value the calibration claim has CHANGED — the "
            f"honest status is then 'not established', and that belongs in "
            f"MODEL-LOG before this assertion is touched.")
        assert result["rejects_in"] == result["replicates"], (
            f"`{pop}`: {result['rejects_in']}/{result['replicates']} "
            f"randomisations reject. Anything less and the answer depends on "
            f"the PIT re-roll rather than on the model.")
        assert result["ci_lo"] > crit, (
            f"`{pop}`: the cluster-bootstrap 95% interval on χ² is "
            f"[{result['ci_lo']:.2f}, {result['ci_hi']:.2f}] and its lower "
            f"bound has fallen to the critical value. Measured: [18.20, 80.39] "
            f"on `reference` and [25.49, 84.91] on `claimed`.")


def test_the_claimed_population_drops_the_columns_the_model_got_most_wrong():
    """⛔ #15(a), AS A NUMBER. The selection rule is not informationless.

    Forecast-selection leaves PIT uniform *under calibration* — a statement
    about the null, and the only thing that argument buys. When the null is
    false the selection can be very far from neutral, and here it is: the rule
    admits a column only when the model gives it a seat in half its draws, and
    the model's dominant failure is giving a real party essentially zero.

    Measured against the FIXED ``reference`` population on the committed panel:
    ``claimed`` keeps 2 of the 10 worst |z| columns, reads sd(z) 0.784 against
    1.062, and a mean z of +0.014 against +0.105.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    records = json.loads(path.read_text())["records"]

    rows = []
    for r in records:
        cal = r.get("calibration") or {}
        ref, claimed = cal.get("reference"), cal.get("claimed")
        if not ref or not claimed:
            continue
        keep = set(claimed["parties"])
        for party, z in zip(ref["parties"], ref["z"]):
            if z is not None:
                rows.append((party, float(z), party in keep))

    scanned(rows, of=records, low=10.0, high=30.0,
            what="columns in the fixed `reference` population carrying a z",
            denominator="rows in history.json")

    worst = sorted(rows, key=lambda t: -abs(t[1]))[:10]
    kept_worst = sum(1 for _, _, inc in worst if inc)
    assert kept_worst <= 4, (
        f"`claimed` keeps {kept_worst} of the ten worst columns in the fixed "
        f"population. The measured figure is 2/10, and the whole objection to "
        f"leading with `claimed` is that the rule drops them. If this has "
        f"risen the objection has weakened and the report should say so.")

    z_all = np.array([z for _, z, _ in rows])
    z_kept = np.array([z for _, z, inc in rows if inc])
    assert z_kept.size >= 50 and z_all.size > z_kept.size, (z_all.size, z_kept.size)
    assert z_kept.std(ddof=1) < 0.90 * z_all.std(ddof=1), (
        f"sd(z) reads {z_kept.std(ddof=1):.3f} on the claimed columns against "
        f"{z_all.std(ddof=1):.3f} on the fixed population (measured: 0.784 "
        f"against 1.062). `claimed` understating the width fault is the "
        f"finding; if it no longer does, this test is the place that says so.")
    assert abs(z_kept.mean()) < abs(z_all.mean()), (
        f"mean z {z_kept.mean():+.3f} on claimed against {z_all.mean():+.3f} "
        f"on the fixed population (measured: +0.014 against +0.105). The "
        f"selection flattering the level bias is the other half of the finding.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
