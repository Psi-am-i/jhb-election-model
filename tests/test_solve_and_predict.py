"""``montecarlo.solve_and_predict`` — the calibration solver, value-tested at last.

This is the function that makes every draw's voting-district shares add back up
to the citywide total that draw drew. It runs twice per draw (PR and ward), so
on a 1,500-draw run it executes 3,000 times, and until this file it had never
been tested: the only mention of it anywhere under ``tests/`` was a line in a
*comment* in ``test_ipf_feasibility.py`` listing it as a site where a module
constant had been frozen into a default argument (MODEL-LOG §1.33).

It is a fixed-point iteration, so the properties worth pinning are the ones an
iterative solver loses silently.

CLASS A — A SOLVER THAT DOES NOT CONVERGE AND DOES NOT SAY SO. ``rounds``
    exhausts, the loop falls out of the bottom, and the function returns a
    well-formed array of rows that each sum to 1.0 and are not the answer. There
    is no exception, no warning, no returned flag, no guard counter — nothing
    downstream can distinguish a converged solve from an abandoned one. The
    house has the opposite precedent one module away: ``pools.balance_margins``
    raises ``RuntimeError("margin balancing did not converge")``, and
    ``pools.py`` raises on non-convergence in three separate places. Two inputs
    below reach the silent path, and both are reachable in production.

CLASS B — AN ANOMALY THAT TAKES THE NEUTRAL VALUE. The multiplicative update is
    guarded by ``np.where(got > 1e-9, target / got, 1.0)``. The fallback ``1.0``
    is the identity multiplier, so "this party's realised share is degenerate"
    and "this party is already exactly right" produce the same step: none. Feed
    a weight vector that sums to zero and every entry of ``got`` is NaN,
    ``NaN > 1e-9`` is False for all of them, and forty rounds of the solver do
    exactly nothing while reporting success. This is the defect class
    ARCHITECTURE.md was written about, reached without a single ``dict.get``.

The remaining tests pin what the solver must never lose quietly: rows on the
simplex, the citywide target actually hit, ``tol`` binding, weight-scale
invariance, monotonicity in the deviations, determinism, and no mutation of the
caller's arrays.

Every expected value here is either an invariant (conservation, monotonicity,
bounds, invariance) or arithmetic that can be done by hand on a constructed
input — see each docstring. Nothing is asserted because the implementation
happens to return it.

Run:
    ./.venv/bin/python tests/test_solve_and_predict.py
    ./.venv/bin/python -m pytest tests/test_solve_and_predict.py -q
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module  # noqa: E402

import montecarlo as M  # noqa: E402


# --------------------------------------------------------------------------
# A constructed city: 4 voting districts, 3 parties. No file on disk is read,
# so nothing here depends on the archive, on `pools_*.json`, or on any city
# config — and every number below can be checked with a calculator.
# --------------------------------------------------------------------------

BASE = np.array([0.50, 0.30, 0.20])          # last election's citywide shares
TARGET = np.array([0.45, 0.35, 0.20])        # the share this draw wants
DEV = np.array([                             # per-VD deviation, in logit space
    [+0.4, -0.2, -0.2],
    [-0.3, +0.5, -0.1],
    [+0.1, +0.1, -0.3],
    [-0.2, -0.4, +0.6],
])
GAMMA = np.array([1.0, 1.0, 1.0])            # how far each party's dev carries
WEIGHT = np.array([1.0, 2.0, 3.0, 4.0])      # registration x turnout, per VD
WEIGHTS_N = WEIGHT / WEIGHT.sum()


def _citywide(pred, weight=WEIGHT):
    """The weighted citywide share the returned per-VD shares actually imply.

    This is the quantity the solver exists to control, recomputed here from the
    RETURNED array rather than read out of the solver, so a solver that stops
    early cannot report its own success.
    """
    w = np.asarray(weight, dtype=float)
    return (w / w.sum()) @ pred


def _solve_counting_rounds(*args, **kwargs):
    """``(prediction, rounds_actually_run)``.

    ``solve_and_predict`` calls the module-global ``logit`` once per round and
    once more after the loop, so counting calls counts rounds. Nothing else in
    the function is observable from outside — which is itself the point of
    CLASS A above: the number of rounds it took is not in the return value, and
    a caller cannot find out.
    """
    calls = {"n": 0}
    real = M.logit

    def spy(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    M.logit = spy
    try:
        out = M.solve_and_predict(*args, **kwargs)
    finally:
        M.logit = real
    return out, calls["n"] - 1


# --------------------------------------------------------------------------
# what the solver is for
# --------------------------------------------------------------------------

def test_every_returned_row_is_a_probability_distribution_over_parties():
    """Conservation. If this fails, every downstream vote count is wrong.

    ``run_model`` multiplies the returned array by ``weight`` and reads the
    product as votes (``pr_votes = weight @ pr_eff``), and it tallies ward
    winners from ``part_cast[:, None] * wd_eff[part_vd]``. Both treat a row as
    a party's share of the votes cast in that VD, so the rows must sum to one
    and lie in (0, 1). The final line of the function divides by the row sum,
    so this is an invariant of the code as written, not a measurement — which
    is exactly why a test should hold it there.

    The who-turns-out tilt was deleted from ``run_model`` for breaking this
    property: it multiplied the calibrated shares afterwards, "so rows stopped
    summing to one and the realised citywide share was no longer the one
    drawn" (montecarlo.py, in the comment where the tilt used to be).
    """
    pred = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT)
    assert pred.shape == DEV.shape
    assert np.all(np.isfinite(pred))
    assert np.all(pred > 0.0) and np.all(pred < 1.0)
    assert np.allclose(pred.sum(axis=1), 1.0, atol=1e-12)


def test_the_returned_shares_reproduce_the_citywide_target_within_tol():
    """The contract. A solver that returns rows summing to 1 but NOT summing
    to the drawn citywide target has silently replaced the draw with something
    else, and every score in the repository is then measured against a target
    the model did not actually hit.

    Checked against ``tol`` as passed, on the returned array, with the weighted
    average recomputed here rather than taken from the solver.
    """
    tol = 1e-6
    pred = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT, tol=tol)
    gap = np.abs(_citywide(pred) - TARGET).max()
    assert gap < tol, f"citywide gap {gap:.3e} is not within tol {tol:.0e}"


def test_gamma_of_zero_puts_the_citywide_target_in_every_district_exactly():
    """γ = 0 is the neutral value of the geography channel, and it is pinned
    here DELIBERATELY, because a parameter that is the identity at its neutral
    value is the failure mode ARCHITECTURE.md names.

    Hand arithmetic, no implementation consulted. With γ = 0 the deviations
    drop out: ``pred = expit(level)`` is the same row for every VD. The seed
    ``theta = target / base`` makes ``base * theta = target`` exactly, so
    ``level = logit(target)`` (no clipping — every target here is well inside
    [0.002, 0.998]) and ``expit(logit(target)) = target``. The target sums to
    one, so the row normalisation is a division by one. Every VD is therefore
    the citywide target to floating-point exactness, in ONE round.

    γ = 0 is safe here in the sense that matters — it is not silently
    absent-able. ``gamma`` is a required positional parameter of a function
    called with ``gamma["PR"]`` / ``gamma["Ward"]``, so omitting it is a
    TypeError and a missing key is a KeyError; neither can arrive as 0.
    """
    pred, rounds_run = _solve_counting_rounds(
        DEV, BASE, TARGET, np.zeros(3), WEIGHT)
    assert rounds_run == 1, f"γ=0 should solve in one round, took {rounds_run}"
    assert np.allclose(pred, TARGET[None, :], atol=1e-14), (
        "with γ=0 every district must BE the citywide target:\n" + repr(pred))


def test_zero_deviations_put_the_citywide_target_in_every_district_exactly():
    """The same hand computation reached the other way, and the reason the one
    above is not merely a property of γ.

    With ``dev = 0`` the term ``gamma * dev`` vanishes whatever γ is, so the
    seed ``theta = target / base`` again lands ``expit(logit(target))`` in every
    row. If this ever disagreed with the γ=0 case, the two arguments would not
    be entering the model multiplied together as the docstring of the level
    stage claims.
    """
    pred = M.solve_and_predict(np.zeros_like(DEV), BASE, TARGET,
                               np.array([3.0, 0.5, 1.7]), WEIGHT)
    assert np.allclose(pred, TARGET[None, :], atol=1e-14)


def test_all_the_weight_on_one_district_calibrates_that_district_to_the_target():
    """A degenerate case with a hand-known answer, and the strongest available
    check that the solver is solving the equation it claims to.

    ``got = weights @ pred`` with all the weight on VD *i* is just ``pred[i]``,
    so the fixed point is ``pred[i] == target`` — the calibration must land that
    one district exactly on the citywide target, however extreme its deviations
    are. A solver that had, say, transposed ``dev`` or dropped ``gamma`` would
    still return rows summing to one and would fail this.
    """
    weight = np.array([0.0, 0.0, 1.0, 0.0])
    pred = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, weight, tol=1e-12,
                               rounds=200)
    assert np.allclose(pred[2], TARGET, atol=1e-10), repr(pred[2])


def test_a_district_with_a_larger_deviation_gets_a_larger_share_of_that_party():
    """Monotonicity in ``dev``. If this fails the geography has been inverted
    or is not connected, and the model would place a party's strength in the
    wrong half of the city while every citywide number stayed perfect — the
    error the citywide-target test above cannot see, because it is invisible to
    the weighted average.

    Argued, not measured: ``expit`` is strictly increasing, γ > 0 here, and for
    the constructed rows below only party 0's deviation varies, so the
    pre-normalisation numerator for party 0 strictly increases while the other
    two are identical across rows. ``a / (a + b + c)`` is strictly increasing in
    ``a`` with ``b, c`` fixed, so the normalised share must strictly increase.
    """
    dev = np.array([[0.0, 0.0, 0.0],
                    [1.0, 0.0, 0.0],
                    [2.0, 0.0, 0.0]])
    pred = M.solve_and_predict(dev, BASE, TARGET, GAMMA, np.ones(3))
    col = pred[:, 0]
    assert col[0] < col[1] < col[2], f"party 0's share is not monotone: {col}"


def test_scaling_every_weight_by_a_constant_changes_nothing():
    """The solver normalises ``weight`` internally, so it must be invariant to
    the units the caller keeps its weights in.

    It matters because ``run_model`` passes ``weight_cal = reg * t_draw`` —
    registered voters times a turnout rate — and nothing anywhere fixes that
    product's scale. If the answer depended on it, a change to how turnout is
    expressed (a rate against a percentage) would move every forecast while
    looking like a units tidy-up.

    Scaled by 1024, a power of two, so the assertion can be bitwise: the
    normalisation divides by a sum scaled by the same exact power, and binary
    floating point loses nothing.
    """
    a = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT)
    b = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT * 1024.0)
    assert np.array_equal(a, b), np.abs(a - b).max()


def test_the_solver_is_deterministic_and_does_not_mutate_its_inputs():
    """Two defects at once, both of which would corrupt a Monte Carlo run in a
    way no single-draw inspection could find.

    Determinism: ``run_model`` calls this 3,000 times in a 1,500-draw run and
    the run is expected to be reproducible from its seed. There is no RNG in
    the function, so any non-determinism would be leaked state.

    No mutation: ``dev``, ``base_city`` and ``weight`` are the SAME arrays on
    every draw — ``dev_pr``, ``dev_ward``, ``base_city`` are built once outside
    the draw loop. An in-place write to any of them would make draw *d+1* start
    from draw *d*'s leftovers, and the run would still produce a full,
    plausible distribution. ``weight_cal`` is rebuilt per draw and would hide
    it further.
    """
    dev, base = DEV.copy(), BASE.copy()
    target, gamma, weight = TARGET.copy(), GAMMA.copy(), WEIGHT.copy()
    first = M.solve_and_predict(dev, base, target, gamma, weight)
    second = M.solve_and_predict(dev, base, target, gamma, weight)
    assert np.array_equal(first, second), "not deterministic"
    for name, now, before in (("dev", dev, DEV), ("base_city", base, BASE),
                              ("target", target, TARGET),
                              ("gamma", gamma, GAMMA),
                              ("weight", weight, WEIGHT)):
        assert np.array_equal(now, before), f"solve_and_predict mutated {name}"


# --------------------------------------------------------------------------
# tol and the round budget
# --------------------------------------------------------------------------

def test_the_solver_stops_before_the_round_budget_when_it_has_converged():
    """The ``break`` must actually be reachable.

    If it were not — if ``gap`` were computed on the wrong quantity, or
    compared after the update that makes it stale — the solver would silently
    spend the full budget on every one of the 3,000 calls per run, and the only
    symptom would be that the model got slower. It is asserted here as "fewer
    than the budget" rather than a pinned round count, because the number of
    rounds is a property of these constructed inputs and of nothing else.
    """
    _, rounds_run = _solve_counting_rounds(
        DEV, BASE, TARGET, GAMMA, WEIGHT, rounds=40, tol=1e-6)
    assert 0 < rounds_run < 40, (
        f"converged solve used {rounds_run} of 40 rounds; the break is either "
        f"unreachable or fires immediately")


def test_a_tighter_tol_gives_a_demonstrably_tighter_answer():
    """``tol`` must bind, and it must bind on the RETURNED array.

    A tolerance that is read but not enforced is the same defect as a lever
    that is read but not consumed: it reads as a working dial and every value
    of it gives the same answer (ITERATING.md rule 6 — sweep it to a value that
    MUST change the answer, and confirm the answer changes).

    Two assertions, both invariants rather than pinned numbers: the achieved
    citywide gap is strictly smaller at each tighter rung, and at every rung it
    is within the tolerance that was asked for. ``rounds`` is set high enough
    that ``tol`` is the binding constraint and not the budget.
    """
    achieved = []
    for tol in (1e-1, 1e-3, 1e-6, 1e-12):
        pred = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT,
                                   rounds=200, tol=tol)
        gap = np.abs(_citywide(pred) - TARGET).max()
        assert gap < tol, f"tol={tol:g} not honoured: gap {gap:.3e}"
        achieved.append(gap)
    assert all(b < a for a, b in zip(achieved, achieved[1:])), (
        f"tightening tol did not tighten the answer: {achieved}")

    # AND ``tol`` is a promise about EVERY party's citywide share, not about
    # their average. The rungs above cannot tell the two apart: three parties
    # whose gaps are within a small factor of each other, plus one further
    # contraction after the break, hide any slack in the criterion. So the
    # promise is checked where the two quantities differ — a council with many
    # parties, only one of which is hard to place.
    #
    # Twelve parties on an equal citywide base and an equal target, with a
    # single party whose per-VD deviation runs from -4 to +4 logits across the
    # four districts: a deliberate stress input, not a plausible city. Only
    # that party's citywide share is hard to hit, and the other eleven absorb
    # its error in eleven slivers, so the MEAN per-party gap is about a twelfth
    # of the largest one. A criterion built on the mean would stop with that
    # one party several times outside the tolerance the caller asked for, and
    # every other number in the run would look right. Asserted per party, on
    # the returned array, as an invariant: no party may be outside ``tol``.
    parties = 12
    flat = np.full(parties, 1.0 / parties)
    stress = np.zeros((len(WEIGHT), parties))
    stress[:, 0] = np.linspace(-4.0, 4.0, len(WEIGHT))
    tol = 1e-6
    pred = M.solve_and_predict(stress, flat, flat, np.ones(parties), WEIGHT,
                               rounds=200, tol=tol)
    per_party = np.abs(_citywide(pred) - flat)
    assert per_party.max() < tol, (
        f"tol={tol:g} is honoured on average but not party by party: worst "
        f"party {per_party.max():.3e}, mean {per_party.mean():.3e}")


# --------------------------------------------------------------------------
# CLASS A / CLASS B — the silent paths. These document ACTUAL behaviour that
# is wrong; see this file's header and the findings written up against it.
# --------------------------------------------------------------------------

def test_a_target_under_the_level_floor_stalls_and_the_solver_now_says_so():
    """RE-RECORDED 2026-08-26. Half of what this documented is fixed.

    **The stall is still real and is still not fixed** — that is F12 in
    MODEL-LOG §1.98, it is `moving`, and it needs a measurement before anything
    touches it. What IS fixed is the silence: `solve_and_predict` now takes a
    `stats` dict and records `nonconvergent`, the worst gap, and how many
    parties were unreachable, so a caller can no longer be handed a stalled
    answer with no way to know (F9).

    **Two things changed under this test and both matter.** The floor the
    parameter's own default resolves moved from `SHARE_FLOOR` (0.002) to
    `DEFAULTS["level_floor"]` (1e-6), so the old fixture — a party asked for
    0.1% of the city — is no longer under the floor and no longer stalls. The
    target below is now genuinely sub-1e-6, which is what the shipped
    configuration actually produces: with `dirichlet_floor` 1e-4 against the
    Black African pool's α = 26.86, 97.4% of floored-member draws land under
    1e-6 and every draw carries at least one.

    Still asserted, because they are still true and still wrong:

    ``logit`` clips its argument into ``[floor, 1 - SHARE_FLOOR]``, so once a
    party's implied citywide share ``base_city * theta`` falls under the floor,
    multiplying ``theta`` again moves ``level`` not at all. The update becomes a
    no-op for that party and the iteration sits on a fixed point that is NOT
    the target. Asserted below: the answer at 1,000 rounds and at 5,000 rounds
    is the same array, so this is a stall and not slow convergence.

    With the parameter's own default floor (``level_floor=None`` →
    ``SHARE_FLOOR`` = 0.002) a party asked for 0.1% of the city comes back at
    roughly 0.15% — a miss of ~480x ``tol`` — and the function returns it with
    no exception, no warning, and no way for the caller to know. One module
    away, the same situation raises: ``pools.balance_margins`` ends
    ``raise RuntimeError("margin balancing did not converge")``.

    Sub-0.2% citywide targets are ordinary; that is why DEFAULTS carries
    ``level_floor`` 1e-6, adopted 2026-08-06 to "free sub-0.2% targets"
    (MODEL-LOG §1.18), and the second half of this test shows that floor does
    free them. The defect is that the SIGNAL is missing, not that production is
    currently on the bad floor: nothing here would tell anyone if it were.
    """
    # tol is DELIBERATELY tighter than the shipped 1e-6 here. The floor and the
    # default tolerance are the same order (1e-6 each), so in a three-party toy
    # the floored party's irreducible error is about the size of tol itself and
    # the stall is marginal. In the real model ~47 parties are floored at once
    # and their summed theft is well above tol; a tighter tol reproduces that
    # margin honestly in three parties rather than faking it.
    target = np.array([0.6000, 0.3999991, 0.0000009])   # sums to 1; p2 under 1e-6
    tol = 1e-9

    stalled, rounds_run = _solve_counting_rounds(
        DEV, BASE, target, GAMMA, WEIGHT, rounds=40, tol=tol)
    assert rounds_run == 40, "expected the whole round budget to be spent"
    assert np.allclose(stalled.sum(axis=1), 1.0), (
        "the abandoned answer is well-formed, which is what makes it silent")
    gap = np.abs(_citywide(stalled) - target).max()
    assert gap > 10 * tol, (
        f"gap {gap:.3e} — if this is now small the floor stall is FIXED, which "
        f"is F12 in MODEL-LOG §1.98; re-read this test, do not re-record it")

    # IT IS THE CITYWIDE GAP THAT IS STUCK, NOT THE ARRAY. Measured: from 1,000
    # to 5,000 rounds the gap moves 4.0987e-07 -> 4.0759e-07 (0.6%), while the
    # per-VD array moves by 1.46e-04. theta for the floored party keeps
    # shrinking, which cannot move its own clipped level but does slightly move
    # everyone else through the row renormalisation. So this is not a fixed
    # point in theta; it is a fixed point in what the caller asked for.
    long_run = _citywide(M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT,
                                             rounds=1000, tol=tol))
    longer = _citywide(M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT,
                                           rounds=5000, tol=tol))
    gap_1k = np.abs(long_run - target).max()
    gap_5k = np.abs(longer - target).max()
    assert gap_5k > 10 * tol, "five thousand rounds should not have fixed it"
    assert abs(gap_5k - gap_1k) < 0.05 * gap_1k, (
        f"not a stall after all — 5x the rounds moved the gap from {gap_1k:.4e} "
        f"to {gap_5k:.4e}, which is more than the 5% a stall permits")

    # THE HALF THAT IS FIXED. The caller is now told, and told precisely enough
    # to act: `nonconvergent` alone would be alarming and useless, because on
    # the shipped configuration it fires on every solve. What distinguishes a
    # broken solver from an unreachable target is `unreachable_parties` and the
    # reachable-only gap, so both are recorded.
    stats: dict = {}
    M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=40, tol=tol,
                        stats=stats)
    assert stats["solves"] == 1
    assert stats["rounds"] == 40, "a stalled solve spends the whole budget"
    assert stats["nonconvergent"] == 1, (
        "the solver stalled and did not report it — this is the silence F9 "
        "closed, and it has reopened")
    assert stats["unreachable_parties"] >= 1, (
        "the stall's CAUSE must be reported, not just its symptom: one party's "
        "target is below the level floor and no theta can reach it")
    assert stats["worst_gap"] >= 10 * tol

    # And the reachable-only reading must be clean here, because the two
    # parties above the floor ARE solvable. If this ever fires, the solver is
    # failing at something it could have done — a different defect entirely.
    assert stats["worst_gap_reachable"] < stats["worst_gap"], (
        "the reachable gap should exclude the floored party's irreducible "
        "error; if they are equal the split is not doing its job")

    # Recording must not change the answer.
    quiet = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=40,
                                tol=tol)
    loud = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=40,
                               tol=tol, stats={})
    assert np.array_equal(quiet, loud), "passing `stats` moved a number"

    # The floor is the cause, and lowering it is A cure — but NOT the one to
    # reach for: at 1e-9 the update's own guard (`got > 1e-9`) becomes the next
    # binding constraint, and `got` was measured at 2.06e-8 on real Joburg 2021
    # geography. See MODEL-LOG §1.98, coupling F12+F10.
    freed = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT,
                                rounds=400, tol=tol, level_floor=1e-12)
    assert np.abs(_citywide(freed) - target).max() < 1e-6


def test_weights_that_sum_to_zero_return_an_uncalibrated_answer_in_silence():
    """**DOCUMENTS A DEFECT. The behaviour asserted here is the wrong one.**

    CLASS B, and the ARCHITECTURE.md defect class reached without a
    ``dict.get``. ``weights = weight / weight.sum()`` is 0/0 for an all-zero
    weight vector, so every entry of ``got`` is NaN. The update is guarded by

        theta = theta * np.where(got > 1e-9, target / got, 1.0)

    and ``NaN > 1e-9`` is False, so the guard's NEUTRAL value — the identity
    multiplier 1.0 — is taken for every party, in every round. Forty rounds run
    and none of them does anything. ``gap`` is NaN, ``NaN < tol`` is False, so
    the loop never breaks and never complains either.

    What comes back is finite, positive, and row-normalised: the seeded answer
    ``theta = target / base_city``, bit-identical to what ``rounds=0`` returns,
    i.e. the calibration never happened. Asserted against the ``rounds=0``
    answer rather than against a recorded array, so it says "no calibration
    occurred" rather than pinning a number.

    A degenerate weight vector is not hypothetical: ``weight_cal = reg *
    t_draw``, and a city-year whose registration column failed to parse gives
    exactly this — silently, for every draw, in every VD.

    The only signal that anything went wrong is numpy's own "invalid value
    encountered in divide" RuntimeWarning, which no caller catches, no log
    records and no guard counter counts.
    """
    seed_only = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT, rounds=0)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with np.errstate(invalid="warn", divide="warn"):
            pred, rounds_run = _solve_counting_rounds(
                DEV, BASE, TARGET, GAMMA, np.zeros(len(DEV)), rounds=40)

    assert rounds_run == 40, "expected every round to be spent doing nothing"
    assert np.all(np.isfinite(pred)) and np.allclose(pred.sum(axis=1), 1.0), (
        "the answer is well-formed, which is what makes the failure silent")
    assert np.array_equal(pred, seed_only), (
        "expected the uncalibrated seed; if this now differs, the NaN guard "
        "has changed and the finding should be re-read")
    assert np.abs(_citywide(pred, WEIGHT) - TARGET).max() > 1e-3, (
        "the seed happens to be calibrated here, so this input no longer "
        "demonstrates the silent failure")
    # Nothing but a numpy warning marks it, and nothing consumes that.
    assert any(issubclass(w.category, RuntimeWarning) for w in caught), (
        "not even numpy's warning survives now")


def test_a_round_budget_of_zero_returns_the_seed_without_complaint():
    """**DOCUMENTS A DEFECT.** The same silence from the other end.

    ``rounds=0`` skips the loop entirely and returns the seeded prediction —
    the calibration is not attempted at all — and the function reports this
    exactly as it reports a converged solve. There is no return value, no flag
    and no counter that separates "solved" from "never tried"; the whole
    difference is invisible at the seam.

    Asserted as an invariant, not a number: the returned rows are on the
    simplex, and the citywide shares they imply are NOT the target.
    """
    pred = M.solve_and_predict(DEV, BASE, TARGET, GAMMA, WEIGHT, rounds=0)
    assert np.allclose(pred.sum(axis=1), 1.0)
    assert np.abs(_citywide(pred) - TARGET).max() > 1e-3, (
        "an unsolved answer that is already on target proves nothing")


def test_omitting_level_floor_now_resolves_the_floor_production_actually_uses():
    """RE-RECORDED 2026-08-26, DELIBERATELY. It used to document the defect.

    **What it asserted before, and why it now asserts the opposite.** This test
    was written to pin `level_floor=None` resolving to the module's
    ``SHARE_FLOOR`` (0.002) — the "micro floor artefact" production REPLACED on
    2026-08-06 with 1e-6, because 0.002 will not let a sub-0.2% target through
    (MODEL-LOG §1.18). Its own docstring said it "fails the day the two are
    reconciled — which is the point". They were reconciled in MODEL-LOG §1.98
    (F11), so it failed, and this is the re-record it asked for.

    **Nothing on the live path moved.** Both production call sites
    (``montecarlo.py:3192``, ``:3194``) pass ``level_floor=scenario["level_floor"]``
    explicitly, and ``scenario["level_floor"]`` is a hard index that cannot fall
    back — so no run has ever taken the default. It was a trap for the NEXT
    caller, and this test file's own author walked into it.

    Asserted: omitting the argument now gives the same answer as passing
    ``DEFAULTS["level_floor"]``, and a materially BETTER one than the replaced
    0.002 — i.e. the default is the production value, and it is not inert.
    """
    assert M.DEFAULTS["level_floor"] == 1e-6, (
        "DEFAULTS['level_floor'] has moved; re-read this test's argument")
    assert M.SHARE_FLOOR == 0.002, (
        "SHARE_FLOOR is still the CEILING term (1 - SHARE_FLOOR) and the "
        "deviation floor; only the level_floor resolution changed")

    target = np.array([0.6000, 0.3990, 0.0010])
    implicit = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=200)
    explicit = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=200,
                                   level_floor=M.DEFAULTS["level_floor"])
    assert np.allclose(implicit, explicit, atol=0, rtol=0), (
        "omitting level_floor no longer resolves DEFAULTS['level_floor']; the "
        "default has drifted away from production again (MODEL-LOG §1.98 F11)")

    replaced = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=200,
                                   level_floor=M.SHARE_FLOOR)
    now = abs(_citywide(implicit)[2] - target[2])
    then = abs(_citywide(replaced)[2] - target[2])
    assert then > 10 * now, (
        f"the replaced 0.002 floor should still be materially worse for a "
        f"sub-0.2% party, or §1.18's reason for replacing it has evaporated: "
        f"now {now:.3e}, replaced {then:.3e}")


def test_the_level_floor_is_resolved_at_call_time_and_not_frozen_at_import():
    """MODEL-LOG §1.33, CLASS 13, at this specific site.

    ``solve_and_predict`` was one of four functions that captured a module
    constant in a default argument (``def f(..., level_floor=SHARE_FLOOR)``),
    which Python evaluates once at import. Setting ``montecarlo.SHARE_FLOOR``
    afterwards — which is how every sweep in this repository reaches a constant
    — then changed nothing, and the constant read as inert at every value.

    ``tests/test_ipf_feasibility.py`` guards the SHAPE of the fix with an AST
    walk. This guards the BEHAVIOUR: rebinding the module attribute must reach
    the call. An AST walk cannot see a fix that is undone by some other route,
    and a source-shape test that passes while the behaviour is broken is
    precisely what MODEL-LOG §1.96 says is worse than no test at all.

    RE-POINTED 2026-08-26. The guard is unchanged in substance; what it watches
    moved. ``level_floor=None`` used to resolve ``SHARE_FLOOR`` and now resolves
    ``DEFAULTS["level_floor"]`` (MODEL-LOG §1.98, F11), so rebinding
    ``M.SHARE_FLOOR`` is no longer the way to reach this floor — rebinding
    ``M.DEFAULTS["level_floor"]`` is, and that is what a sweep does. Watching
    the old name would have left the CLASS 13 guard passing against a constant
    the function had stopped reading, which is the §1.96 failure exactly.
    """
    target = np.array([0.6000, 0.3999991, 0.0000009])  # sums to 1; under 1e-6
    before = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=200)
    original = M.DEFAULTS["level_floor"]
    try:
        M.DEFAULTS["level_floor"] = 1e-9
        after = M.solve_and_predict(DEV, BASE, target, GAMMA, WEIGHT, rounds=200)
    finally:
        M.DEFAULTS["level_floor"] = original
    assert not np.allclose(before, after), (
        "setting montecarlo.DEFAULTS['level_floor'] did not reach "
        "solve_and_predict; the floor is frozen at import again "
        "(MODEL-LOG §1.33, re-pointed §1.98)")
    assert np.abs(_citywide(after) - target).max() < 1e-6, (
        "with the floor lowered the sub-floor target must become reachable")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
