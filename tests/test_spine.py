"""``levels.spine`` — the national-to-local level path, called by nothing that asserts.

The spine is where every party's central level comes from at every runnable
target (MODEL-LOG §1.52: *"the spine reaches every party at every target"*), and
it decides ActionSA's 2026 level — 5.98% on the national route, 15.23% on its
own last local result (§1.30). Until this file it was **invoked** twice in the
suite, at ``test_ipf_feasibility.py:137`` and ``test_drawer.py:422``, and
**asserted about** nowhere: both call it to build a fixture and neither looks at
what came back. Its blend weight, its three routes and its constant were
therefore unguarded.

WHAT THESE TESTS PIN, and why each one is justified independently of the
implementation:

* **The three routes.** ``spine``'s own docstring and §1.30 define them: a party
  with both records blends, one with only a national record takes the national
  route at weight 0, one with only a local record takes the local route at
  weight 1. Each is checkable against a constructed record by hand.
* **The blend is a weighted GEOMETRIC mean**, ``w = k / (worth + k)`` on the
  local route (§1.30). Two consequences follow with no reference to the code:
  the blend lies strictly between the two routes, and at ``worth = k`` it is
  exactly ``sqrt(national x local)`` — which is precisely what ``SPINE_K``'s
  declaration claims ("at worth = k the two routes are equal").
* **That the weight binds.** A weight that does not move the answer is this
  repository's most expensive defect class (``ITERATING.md`` rule 6, CLASS 13 in
  ``test_ipf_feasibility.py``, and ``SPINE_K`` was itself one of the four sites
  frozen at import until §1.33). Monotonicity in ``k``, in both directions, is
  the check that cannot be passed by a dead lever.
* **That the weight is keyed on the theta record ALONE.** §1.43 NEGATIVE 3
  measured the symmetric version — ``w = (worth_rho + k)/(worth_rho + worth_theta
  + 2k)`` — at 338 coherent seats against 312 and rejected it. The asymmetry is
  a deliberate, measured choice, so ``_worth_r`` being discarded with an
  underscore must not be quietly "fixed".

THE FOUR CASES CONSTRUCTED HERE ARE HAND-COMPUTABLE. Every observed ratio in the
constructed records is 1.0 unless a test says otherwise, so the shrinkage in
``levels._shrunk`` is the identity in log space (own mean, group mean and size
fit all equal log 1 = 0) and each route's level is exactly the share it starts
from. No expected value below is read off a run.

Three tests document behaviour that is WRONG. They are named and docstringed as
such and are listed in this file's findings: an empty theta record reporting a
group centre of exactly 1.0, ``k = 0`` dividing by zero for the party the local
route exists for, and the flat group centre reaching a first-local-election
party in place of the size centre (§1.93).

Run:
    ./.venv/bin/python tests/test_spine.py
    ./.venv/bin/python -m pytest tests/test_spine.py -q
"""

from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import cityconfig  # noqa: E402
import levels  # noqa: E402

SRC = ROOT / "src"


def _target(year: str = "2021") -> cityconfig.Target:
    """A Target built directly, so no test here moves ``cityconfig``'s globals.

    ``cityconfig.use_target`` rebinds the module-level ``_TARGET`` and the
    city's ``target_year``; two other files in the suite call it, and a test
    file that silently changed the active target for whatever ran next would be
    the same class of cross-contamination this file exists to guard against.
    """
    return cityconfig.Target(city=cityconfig.active(), year=year)


@contextmanager
def records(theta: dict, rho: dict):
    """Run ``spine`` against CONSTRUCTED retention records.

    ``spine`` reads its evidence through ``levels.theta_record`` and
    ``levels.local_record``, which walk ``data/raw/elections``. Both are looked
    up as module globals at call time, so substituting them here is enough --
    and it is the only way to state an expected level that is arithmetic rather
    than a transcription of whatever the archive currently holds.
    """
    real_t, real_r = levels.theta_record, levels.local_record
    levels.theta_record = lambda *a, **k: theta
    levels.local_record = lambda *a, **k: rho
    try:
        yield
    finally:
        levels.theta_record, levels.local_record = real_t, real_r


# --- the constructed fixture -------------------------------------------------
#
# Every ratio is 1.0, so every party's shrunk log-mean is 0 and every route's
# level is exactly the share it starts from:
#
#   BOTH      national 9%, local 1%   -> blends between 0.09 and 0.01
#   UP        national 1%, local 9%   -> blends the other way (monotonicity)
#   NOTHETA   national 5%, local 2%   -> in both records' PARTIES, but with no
#                                        theta observations of its own
#   NATONLY   national 6%, no local   -> first local election (MK in 2026)
#   LOCONLY   no national, local 4%   -> stood locally, not nationally
#   NEITHER   national 0.0, no local  -> in neither; must not appear at all
THETA = {"BOTH": [(1.0, 0.30)], "UP": [(1.0, 0.30)], "NATONLY": [(1.0, 0.20)]}
RHO = {"BOTH": [(1.0, 0.25)], "UP": [(1.0, 0.25)],
       "NOTHETA": [(1.0, 0.25)], "LOCONLY": [(1.0, 0.15)]}
BASELINE = {"BOTH": 0.09, "UP": 0.01, "NOTHETA": 0.05,
            "NATONLY": 0.06, "NEITHER": 0.0}
PREV_LOCAL = {"BOTH": 0.01, "UP": 0.09, "NOTHETA": 0.02, "LOCONLY": 0.04}


def _spine(k: float | None = 1.0, theta=THETA, rho=RHO,
           baseline=BASELINE, prev_local=PREV_LOCAL):
    with records(theta, rho):
        return levels.spine(_target(), baseline, prev_local, k=k)


def _close(a: float, b: float, tol: float = 1e-12) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


# --- the three routes --------------------------------------------------------

def test_a_party_with_only_a_national_record_takes_the_national_route_at_zero_local_weight():
    """A first-local-election party must not be handed an invented local result.

    MK in 2026 is the case ``spine``'s docstring names: there is no previous
    local share to move forward, so the weight on the local route is 0 by
    necessity and the level is the national share times the party's retention
    ratio -- 1.0 by construction here, so 6.00% in and 6.00% out.

    If this failed, a party facing its first local election would be levelled
    off a local result it does not have -- either the group's, which §1.30
    measured as worse than doing nothing, or zero.
    """
    level, info = _spine()
    assert "NATONLY" in level, "a party with a national record must be levelled"
    assert info["detail"]["NATONLY"]["route"].startswith("national only")
    assert info["detail"]["NATONLY"]["w_local"] == 0.0
    assert _close(level["NATONLY"], 0.06), level["NATONLY"]


def test_a_party_with_only_a_local_record_takes_the_local_route_at_full_weight():
    """A party that stood locally but not nationally has no national route to blend.

    ``nat_level`` is 0 for it, and a geometric blend with 0 is 0 -- so the
    weight must be exactly 1, not merely large. The level is its previous local
    share times rho, 1.0 by construction, so 4.00%.

    If this failed the party would be levelled at (or toward) zero, which is
    the silent way an entire route disappears.
    """
    level, info = _spine()
    assert info["detail"]["LOCONLY"]["route"].startswith("local only")
    assert info["detail"]["LOCONLY"]["w_local"] == 1.0
    assert _close(level["LOCONLY"], 0.04), level["LOCONLY"]


def test_a_party_with_both_records_lands_strictly_between_its_two_routes():
    """The blend must be a compromise, not a silent selection of one route.

    With ``0 < w < 1`` a weighted geometric mean of two distinct positive
    numbers is strictly inside the interval they span -- an invariant of the
    mean itself, independent of this implementation. BOTH's routes are 9.00%
    (national) and 1.00% (local), so its level must be strictly between them.

    If it equalled an endpoint, the blend would have collapsed to one route
    while still reporting itself as a blend, which is exactly the failure
    §1.30's task #22 was opened to end: the model could not say why a party sat
    where it sat.
    """
    level, info = _spine(k=1.0)
    d = info["detail"]["BOTH"]
    assert d["route"] == "blend"
    assert 0.0 < d["w_local"] < 1.0, d
    assert _close(d["national"], 0.09) and _close(d["local"], 0.01), d
    assert 0.01 < level["BOTH"] < 0.09, level["BOTH"]


def test_the_two_routes_reported_in_the_diagnostic_are_the_routes_that_were_blended():
    """The per-party detail must describe the arithmetic that actually happened.

    ``_spine_info["detail"]`` is what ``run_model`` writes to the trace and to
    the report, and it is the only answer anyone gets to "why is this party at
    this number?". A detail block that names routes the blend did not use is
    worse than none: log-linearity in ``w`` is checkable, so check it. With
    ``level = national^(1-w) * local^w`` the log of the level is affine in
    ``w``, so the level at the midpoint weight is the geometric mean of the
    levels at the two ends.

    A ROUTE IS A LEVEL, NOT AN INPUT SHARE. §1.30 quotes ActionSA's two routes
    as 5.98% and 15.23% -- each a predicted share at the target, a previous
    share already multiplied by the retention its record measured. Reporting
    the raw ``baseline`` / ``prev_local`` shares under those keys would be
    invisible in any fixture whose ratios are 1.0, and would make the trace
    disagree with the very number it exists to explain, so the second half of
    this test runs a record with real retention in it (theta 1.3, rho 1.2, so
    every party's shrunk log-mean is log 1.3 / log 1.2 whatever the weights)
    and requires the two reported routes to reproduce the reported level under
    the reported weight.
    """
    lo, info_lo = _spine(k=0.4)
    hi, info_hi = _spine(k=4.0)
    w_lo = info_lo["detail"]["BOTH"]["w_local"]
    w_hi = info_hi["detail"]["BOTH"]["w_local"]
    worth = info_lo["detail"]["BOTH"]["worth"]
    mid_w = 0.5 * (w_lo + w_hi)
    # invert w = k/(worth+k) for the k that produces the midpoint weight
    k_mid = worth * mid_w / (1.0 - mid_w)
    mid, _ = _spine(k=k_mid)
    assert _close(mid["BOTH"], math.sqrt(lo["BOTH"] * hi["BOTH"]), 1e-9), (
        f"the blend is not log-linear in its own reported weight: "
        f"{mid['BOTH']} vs {math.sqrt(lo['BOTH'] * hi['BOTH'])}")

    # ... and the two routes reported are the LEVELLED routes, not the inputs.
    theta = {"B": [(1.3, 0.10)], "C": [(1.3, 0.04)]}
    rho = {"B": [(1.2, 0.10)], "C": [(1.2, 0.04)]}
    level, info = _spine(theta=theta, rho=rho, baseline={"B": 0.09},
                         prev_local={"B": 0.01})
    d = info["detail"]["B"]
    assert _close(d["national"], 0.09 * 1.3), d
    assert _close(d["local"], 0.01 * 1.2), d
    assert not _close(d["national"], 0.09) and not _close(d["local"], 0.01), (
        "the detail reports the raw previous shares, not the routes the blend "
        "was computed from; the retention record has vanished from the trace")
    w = d["w_local"]
    assert _close(level["B"], d["national"] ** (1 - w) * d["local"] ** w, 1e-9), (
        "the reported routes and weight do not reproduce the reported level")


# --- the weight, and whether it binds ---------------------------------------

def test_the_blend_at_k_equal_to_the_partys_worth_is_the_geometric_mean_of_the_routes():
    """``SPINE_K``'s declaration claims "at worth = k the two routes are equal".

    That is a checkable statement and it is what the constant MEANS -- the
    number is documented as the amount of theta evidence at which the model
    stops preferring a party's own last local result. At ``k = worth`` the
    weight must be exactly 0.5 and the level exactly ``sqrt(0.09 x 0.01)`` =
    3.00%, computed by hand from the constructed shares.

    If this failed, ``SPINE_K`` would not be the quantity its declaration and
    §1.30's fitted table say it is, and the leave-one-metro-out fit that chose
    1.0 would have been fitting something else.
    """
    _, info = _spine(k=1.0)
    worth = info["detail"]["BOTH"]["worth"]
    assert worth > 0.0, "the fixture must give BOTH a theta record"
    level, at_worth = _spine(k=worth)
    assert _close(at_worth["detail"]["BOTH"]["w_local"], 0.5, 1e-12)
    assert _close(level["BOTH"], math.sqrt(0.09 * 0.01), 1e-12), level["BOTH"]


def test_raising_k_moves_a_blended_party_monotonically_toward_its_local_result():
    """The lever must bind, in both directions, across its whole range.

    ``SPINE_K`` was one of the four constants frozen in a default argument
    until §1.33 (``def spine(..., k: float = SPINE_K)``), where every sweep of
    it returned identical rows and it read as a dead number. A monotone,
    strictly-moving response over a wide sweep is the check that cannot be
    passed by a lever that does not reach the computation.

    BOTH falls from 9.00% toward 1.00% as k rises; UP rises from 1.00% toward
    9.00%. Both must be strict at every step, and the ends must approach the
    two routes -- if raising k did not eventually place a party on its own
    local result, §1.30's ActionSA case (w = 1.00) could not occur.
    """
    ks = [0.01, 0.05, 0.2, 0.5, 1.0, 2.0, 5.0, 20.0, 200.0]
    got = [_spine(k=k) for k in ks]
    down = [lv["BOTH"] for lv, _ in got]
    up = [lv["UP"] for lv, _ in got]
    ws = [info["detail"]["BOTH"]["w_local"] for _, info in got]
    assert all(a > b for a, b in zip(down, down[1:])), down
    assert all(a < b for a, b in zip(up, up[1:])), up
    assert all(a < b for a, b in zip(ws, ws[1:])), ws
    assert down[0] > 0.085 and down[-1] < 0.011, down
    assert up[0] < 0.012 and up[-1] > 0.085, up


def test_k_equal_to_zero_puts_every_blended_party_exactly_on_its_national_route():
    """k = 0 is the "no local route at all" end of the sweep, and it is a real model.

    It is the pure national spine -- the configuration §1.30 measured at RMSE
    0.275 against the blend's 0.236 -- so it is the natural floor of any sweep
    of ``SPINE_K`` and must be reachable and exact, not merely approached.

    IT IS NOT REACHABLE THROUGH THE SCENARIO. ``montecarlo.py:2868`` reads the
    lever as ``float(scenario.get('spine_k') or _levels.SPINE_K)``, and
    ``0.0 or 1.0`` is ``1.0`` -- so ``spine_k = 0`` silently becomes the
    committed default and a sweep whose lowest rung is 0 reports the k = 1 row
    there. That is a finding against the call site, not against ``spine``; this
    test pins the behaviour ``spine`` itself offers, so that the fix at the
    call site has something to arrive at.

    ``NOTHETA`` is held out of this fixture because at k = 0 it RAISES -- see
    ``test_k_equal_to_zero_divides_by_zero_for_a_party_with_no_theta_record``,
    which is the other half of this pair.
    """
    base = {p: v for p, v in BASELINE.items() if p != "NOTHETA"}
    prev = {p: v for p, v in PREV_LOCAL.items() if p != "NOTHETA"}
    level, info = _spine(k=0.0, baseline=base, prev_local=prev)
    assert info["detail"]["BOTH"]["w_local"] == 0.0
    assert _close(level["BOTH"], 0.09), level["BOTH"]
    assert _close(level["UP"], 0.01), level["UP"]
    # and the routes that have no choice are unmoved by k
    assert _close(level["NATONLY"], 0.06) and _close(level["LOCONLY"], 0.04)


def test_the_blend_weight_ignores_the_local_records_own_evidence():
    """§1.43 NEGATIVE 3 rejected the symmetric weight; the asymmetry is deliberate.

    ``spine`` computes ``_worth_r`` and throws it away. Made symmetric --
    ``w = (worth_rho + k)/(worth_rho + worth_theta + 2k)`` -- the model scored
    338 coherent seats against 312, 4/9 against 6/9 beating uniform swing, and
    CRPS 280.8 against 264.8. It was measured and rejected.

    So: piling observations into the LOCAL record must not move the weight at
    all, while one more observation in the THETA record must lower it. If the
    first half of that ever fails, someone has "fixed" the underscore and the
    model has silently taken the worse of two measured options.
    """
    _, base = _spine()
    fat_rho = dict(RHO, BOTH=[(1.0, 0.25)] * 12)
    _, with_rho = _spine(rho=fat_rho)
    assert (with_rho["detail"]["BOTH"]["w_local"]
            == base["detail"]["BOTH"]["w_local"]), (
        "the local record's weight of evidence has entered the blend weight; "
        "§1.43 NEGATIVE 3 measured that at 338 seats against 312")
    fat_theta = dict(THETA, BOTH=[(1.0, 0.30)] * 4)
    _, with_theta = _spine(theta=fat_theta)
    assert (with_theta["detail"]["BOTH"]["worth"]
            > base["detail"]["BOTH"]["worth"])
    assert (with_theta["detail"]["BOTH"]["w_local"]
            < base["detail"]["BOTH"]["w_local"]), (
        "more theta evidence must move a party toward the national spine")


def test_a_party_with_no_theta_record_sits_entirely_on_its_own_last_local_result():
    """ActionSA in 2026: w = 1.00 because it has no forward theta at all (§1.30).

    ``worth = 0`` gives ``w = k/(0+k) = 1`` for every k > 0, so the party's
    national route is discarded entirely however small k is. That is the
    intended behaviour -- ``spine``'s docstring says "a party whose theta is
    nothing but the group centre sits on its own last local result" -- and it
    is what moves ActionSA from 5.98% to 15.23%, the single largest thing the
    spine does to the 2026 forecast.

    RE-RECORDED 2026-08-28 (§1.97 F7). The note here used to read: *"the route
    is still LABELLED 'blend' while nothing is blended... the number is right;
    the label is not."* The label is now `blend at full local (no θ evidence)`,
    which is what actually happened — a selection, not a blend.

    `routes["blend"]` still counts it as a blend, deliberately: that counter is
    about WHICH RECORDS THE PARTY HAS, and this party has both. What changed is
    the per-party label, which is what a reader checks when asking why a party
    sits where it does.
    """
    for k in (0.01, 1.0, 100.0):
        level, info = _spine(k=k)
        d = info["detail"]["NOTHETA"]
        assert d["worth"] == 0.0, d
        assert d["w_local"] == 1.0, d
        assert d["route"] == "blend at full local (no θ evidence)", d
        assert d["route"].startswith("blend"), (
            f"the label must still say it took the blend ROUTE (the party has "
            f"both records); only what happened WITHIN it changed: {d}")
        assert _close(level["NOTHETA"], 0.02), level["NOTHETA"]


def test_spine_k_is_resolved_in_the_body_so_setting_the_module_constant_reaches_the_blend():
    """CLASS 13, the constant frozen at import (§1.33, ITERATING.md rule 6).

    ``def spine(..., k: float = SPINE_K)`` would evaluate the constant once at
    import; every sweep in this repository reaches the model by assigning to
    the module attribute, so the lever would read as inert at every value.
    ``spine`` resolves ``k = SPINE_K if k is None else float(k)`` in the body
    for exactly this reason, and ``test_ipf_feasibility.py:405`` bans the
    default-argument form by AST -- but no test had checked that the resolution
    actually happens.

    Assigning ``levels.SPINE_K`` must therefore be indistinguishable from
    passing that value explicitly, and must differ from the committed 1.0.
    """
    explicit, _ = _spine(k=4.0)
    at_one, _ = _spine(k=1.0)
    real = levels.SPINE_K
    try:
        levels.SPINE_K = 4.0
        via_constant, info = _spine(k=None)
    finally:
        levels.SPINE_K = real
    assert info["k"] == 4.0, info["k"]
    assert _close(via_constant["BOTH"], explicit["BOTH"]), (
        "setting levels.SPINE_K did not reach the blend -- the constant is "
        "frozen somewhere and every sweep of it is reporting the same rows")
    assert not _close(via_constant["BOTH"], at_one["BOTH"]), (
        "the fixture cannot tell 4.0 from 1.0, so it cannot detect freezing")
    assert levels.SPINE_K == real


# --- the party with neither record, and the neutral value -------------------

def test_a_party_with_neither_record_is_absent_from_the_spine_rather_than_present_at_a_level():
    """Absence is the ONLY signal that the spine could not reach a party.

    ``NEITHER`` holds a national baseline of exactly 0.0 and no previous local
    share. ``spine`` skips it: it appears in neither the level dict nor the
    per-party detail. That is deliberate -- ``spine``'s docstring says such a
    party is an arrival and ``pools.arrival_rules`` sizes it -- and it is the
    right shape, because a level of 0.0 would be a number the party could
    plausibly deserve, whereas a missing key cannot be mistaken for one.

    WHAT IS NOT SAFE is what happens next.
    ``montecarlo.blended_centres:1081`` reads the result as
    ``elif party in spine_level``, so a party the spine could not reach falls
    silently through to the theta prior with nothing recorded anywhere. §1.52
    put a loud ``AssertionError`` at the END of that chain, which is why this
    is currently survivable -- but the spine's own silence about who it dropped
    is not, and the diagnostic block is where it should be said. Recorded in
    this file's findings.
    """
    level, info = _spine()
    assert "NEITHER" not in level, level
    assert "NEITHER" not in info["detail"], info["detail"]
    assert set(level) == set(info["detail"]), (
        "every levelled party must carry a detail block and vice versa")
    assert set(level) == {"BOTH", "UP", "NOTHETA", "NATONLY", "LOCONLY"}, set(level)
    assert all(v > 0.0 for v in level.values()), level


def test_a_party_with_no_record_of_its_own_is_moved_by_the_group_centre_and_not_by_one():
    """The measured group centre must reach a party with no observations of its own.

    ``_shrunk`` returns a party with no evidence entirely to the group target,
    and ``spine`` falls back to the group centre --
    ``mu_t.get(party, c_t)`` / ``mu_r.get(party, c_r)`` -- for a party present
    in a previous result but absent from the retention record. That is the
    whole design: ``spine``'s docstring describes "a party whose theta is
    nothing but the group centre", and §1.30's ActionSA case is a party carried
    forward on evidence that is not its own.

    Substituting the NEUTRAL 1.0 there is ``ARCHITECTURE.md``'s opening defect
    class running the other way -- a measured record silently discarded and
    reported as if no retention had been observed. It is invisible to any
    fixture whose ratios are all 1.0, so this one's are not: every theta
    observation is 1.3 and every rho observation 1.2, which makes each record's
    weighted log-mean exactly ``log 1.3`` and ``log 1.2`` whatever the weights
    are, and the two levels below arithmetic.

    Both sides are checked because both fall back, and the rho side reaches a
    party that stood in the previous local election and is absent from the
    paired local-to-local record -- a party that contested locally for the
    first time last time.
    """
    theta = {"T1": [(1.3, 0.02)], "T2": [(1.3, 0.20), (1.3, 0.05)]}
    rho = {"R1": [(1.2, 0.03)], "R2": [(1.2, 0.15), (1.2, 0.06)]}
    level, info = _spine(theta=theta, rho=rho,
                         baseline={"NO_THETA_NAT": 0.05},
                         prev_local={"NO_RHO_LOC": 0.05})
    assert _close(info["theta_centre"], 1.3), info["theta_centre"]
    assert _close(info["rho_centre"], 1.2), info["rho_centre"]
    assert info["detail"]["NO_THETA_NAT"]["route"].startswith("national only")
    assert info["detail"]["NO_RHO_LOC"]["route"].startswith("local only")
    assert _close(level["NO_THETA_NAT"], 0.05 * 1.3), (
        "the theta record's measured centre did not reach a party without one "
        "of its own; a neutral 1.0 there discards the record silently")
    assert _close(level["NO_RHO_LOC"], 0.05 * 1.2), (
        "the local record's measured centre did not reach a party without one "
        "of its own; a neutral 1.0 there discards the record silently")


def test_an_empty_theta_record_reports_a_group_centre_of_exactly_one():
    """WRONG, and pinned as it stands: no evidence is reported as neutral evidence.

    ``_shrunk`` returns ``({}, 0.0, {})`` when the record is empty, and
    ``spine`` publishes ``exp(0.0) = 1.0`` as ``theta_centre`` and levels every
    party with no theta record of its own at ``national x 1.0``. So "we have no
    national-to-local retention record at all" and "the record says parties
    retain their national share exactly" produce the same level AND the same
    diagnostic number.

    That is the defect class ``ARCHITECTURE.md`` opens with -- absence
    indistinguishable from the neutral value -- landing in the diagnostic that
    exists to make the spine explicable. ``n_theta = 0`` is the only signal,
    and nothing consults it: ``spine`` does not refuse, ``run_model`` prints
    ``theta centre 1.00`` beside ``0 theta observations``, and the guard
    ``if not mu_t and not mu_r`` only fires when BOTH records are empty.

    The same holds symmetrically for rho, and it is reachable: ``local_record``
    returns nothing at target 2006, the earliest LGE with a predecessor, since
    the only prior pair is not strictly before it.
    """
    level, info = _spine(theta={})
    assert info["n_theta"] == 0
    assert info["theta_centre"] == 1.0, (
        "an empty record now reports something other than the neutral value; "
        "if that is a fix, this test is the place to say so")
    assert _close(level["NATONLY"], 0.06), level["NATONLY"]
    # ... and it is arithmetically identical to a record that measured 1.0.
    measured_one, info_one = _spine(theta={"X": [(1.0, 0.30)]})
    assert info_one["theta_centre"] == 1.0
    assert _close(level["NATONLY"], measured_one["NATONLY"]), (
        "no record and a record of exactly 1.0 must at least be "
        "distinguishable somewhere; today they are not")


def test_the_spine_returns_nothing_when_neither_record_has_a_single_observation():
    """The one case ``spine`` does refuse -- and the refusal is silent downstream.

    With both records empty there is no evidence of any kind, and ``spine``
    returns ``({}, {})`` rather than levelling every party at its raw previous
    share. That is correct.

    ``montecarlo.py:2869`` then reads ``if _spine:``, which is false, so
    ``scenario["spine_level"]`` is never set, no ``20_spine`` trace block is
    written, ``note_constant`` never fires, and every party falls through to
    the theta prior exactly as if the spine had agreed with it. An empty
    diagnostic dict is returned to a caller that does not look at it. Recorded
    in this file's findings.
    """
    level, info = _spine(theta={}, rho={})
    assert level == {} and info == {}


def test_a_first_local_election_party_gets_the_flat_group_centre_not_the_size_centre():
    """WRONG, and already known (§1.93): two estimators for one quantity.

    ``_shrunk`` shrinks each party's OWN mean toward ``size_centre`` -- the
    fitted ``log theta = a + b log(size)`` that §3.5 adopted because small
    parties gain going into a local election and large ones lose -- but returns
    the FLAT ``mu_all`` as the group centre, and ``spine`` hands that flat
    number to every party with no record of its own. ``theta_prior``'s own
    comment calls the flat centre the wrong one. §1.93: *"theta_prior falls back
    to the size centre and _shrunk to the flat centre ... and the spine takes
    _shrunk's. The named case is MK in 2026."*

    The consequence is stated here as an equality that should NOT hold: a party
    at 0.20% of the national vote and a party at 30% of it, both facing their
    first local election, get the identical retention multiplier -- the one
    thing ``size_centre`` was fitted to deny. The record below carries a real
    size gradient (small parties above 1.0, large ones below) and enough
    observations for ``size_centre`` to fit, and it changes nothing for either.
    """
    graded = {}
    for i, size in enumerate([0.0005, 0.001, 0.002, 0.004, 0.01, 0.02,
                              0.05, 0.10, 0.20, 0.35]):
        # ratio falls with size: 1.4 at the bottom of the ballot, 0.9 at the top
        ratio = 1.4 * (size / 0.0005) ** -0.06
        graded[f"P{i}"] = [(ratio, size), (ratio * 1.02, size)]
    assert sum(len(v) for v in graded.values()) >= 20, "size_centre needs 20 obs"
    fit = levels.size_centre(graded)
    assert fit is not None and fit[1] < 0.0, (
        "the constructed record must have a real downward size gradient")
    baseline = {"TINY": 0.002, "HUGE": 0.30}
    level, info = _spine(theta=graded, rho=RHO, baseline=baseline,
                         prev_local={})
    tiny = level["TINY"] / 0.002
    huge = level["HUGE"] / 0.30
    assert info["detail"]["TINY"]["route"].startswith("national only")
    assert _close(tiny, huge), (tiny, huge)
    assert _close(tiny, info["theta_centre"]), (
        "both take the flat group centre")
    size_tiny = math.exp(fit[0] + fit[1] * math.log(0.002))
    size_huge = math.exp(fit[0] + fit[1] * math.log(0.30))
    assert not _close(size_tiny, size_huge, 1e-6), (
        "the size centre distinguishes them; the spine does not")


def test_k_equal_to_zero_puts_a_party_with_no_theta_record_on_its_national_route():
    """RE-RECORDED 2026-08-28. The 0/0 is resolved, and the limit was CHOSEN.

    This was `..._divides_by_zero_for_a_party_with_no_theta_record` and pinned
    the crash: `w = k / (worth + k)` is `0.0 / 0.0` for a party with both
    records and no θ evidence, and it raised `ZeroDivisionError` out of the
    middle of `run_model`. It said *"if that is the fix, assert the intended
    weight here instead — the limit from above is w = 1, the party's own local
    result."*

    **The limit from above is NOT what was chosen, and the disagreement is the
    point.** `w` weights the LOCAL route, so `k = 0` means "pure national
    spine". Taking `w = 1` at `worth = 0` would make `k = 0` mean pure-national
    for every party EXCEPT those with no θ evidence, which are precisely the
    parties the local route exists to serve — so the lever would mean two
    different things depending on who it was applied to. **A lever that means
    two things is not a lever**, and `spine_k` exists to be swept.

    The owner's call, 2026-08-28, choosing `w = 0.0` when `worth + k <= 0`, and
    the reasoning is on the record: *ActionSA is a local party, the spine makes
    no sense there either.* The national route for a party with no national
    history is not a quantity worth protecting the discontinuity for.

    NOTHING SHIPS DIFFERENTLY. At `spine_k = None` the resolved k is
    `SPINE_K = 1.0`, so `worth + k` is never zero and this branch never runs on
    any shipped configuration — which is what makes it a free change and why it
    could land without a backtest.
    """
    levels, info = _spine(k=0.0)
    for party, d in info["detail"].items():
        if d["route"].startswith("blend"):
            assert d["w_local"] == 0.0, (
                f"{party}: k=0 must put every blended party on its NATIONAL "
                f"route, and this one is at w_local={d['w_local']}. If the "
                f"limit was deliberately changed, re-read the docstring above "
                f"before re-recording — the choice is registered in "
                f"JUDGEMENT-CALLS.md.")
            assert abs(levels[party] - d["national"]) < 1e-12, (
                f"{party}: w_local is 0 but the level is not the national one")

def test_the_diagnostic_counts_the_observations_the_blend_was_actually_built_from():
    """``n_theta`` and ``n_rho`` are the only account of how much evidence there was.

    ``run_model`` writes them to the trace and to ``note_constant`` as
    "k=1.0, N theta and M rho observations before <year>", and §1.43's headline
    fix was measured in exactly these units (theta observations 119 -> 126 at
    target 2021, 257 -> 264 at 2026). A count that does not track the record
    would have hidden that fix and would hide the next swallowed file error.
    """
    _, info = _spine()
    assert info["n_theta"] == sum(len(v) for v in THETA.values()) == 3
    assert info["n_rho"] == sum(len(v) for v in RHO.values()) == 4
    _, fatter = _spine(theta=dict(THETA, BOTH=[(1.0, 0.30)] * 5))
    assert fatter["n_theta"] == 7, fatter["n_theta"]


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
