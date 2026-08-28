"""``montecarlo.blended_centres`` — the model's one real router, pinned.

``ARCHITECTURE.md`` ("What is actually wrong, in three parts") calls this the
model's **one real router**: *"This is a pipeline with one real router (the
route-precedence chain in ``blended_centres``)"*. Every party's central level
comes out of a four-branch ``if/elif`` chain here, and until this file the
order of those branches was pinned by **nothing at all** — the function is used
as a FIXTURE in ``tests/test_ipf_feasibility.py`` and ``tests/test_drawer.py``
and neither of them asserts a single thing about the centres it hands back.

An implicit precedence is not a contract. It can be reordered by a well-meant
edit — moving the seed branch above the poll branch, say — and every existing
test still passes, because every existing consumer of this function only needs
*a* number. So the first half of this file constructs, for each pair of routes,
a party for which BOTH are available with DIFFERENT answers, and asserts which
one wins. The declared order, top to bottom:

    1. ``poll_levels``      a poll of this city, for a party with no record
    2. ``pool_seeds``       the arrival record's seed (with its band's mode)
    3. ``spine_level``      ``levels.spine`` — national and local, weighted
    4. ``theta_prior``      baseline × the θ mode
    5. ``AssertionError``   MODEL-LOG §1.52: no per-party fallback constant

The rest pins the arithmetic the routes feed into:

* **``poll_credence``** (``DEFAULTS`` 1.0, MODEL-LOG §1.95) multiplies the
  metro-poll blend weight before it is clamped to [0, 1], inside
  :func:`montecarlo.blend_poll_centre`. §1.95's central claim is that *"1.0 is
  the identity and the shipped default, so adding this moves no number"* — that
  was checked once, by hand, against the freeze. Here it is a permanent test.
  ``blend_poll_centre`` is the metro path's half of the poll channel;
  ``poll_levels`` above is the arrivals half, and §1.95 is explicit that
  credence is scoped to the former ("The arrivals path is a route precedence in
  ``blended_centres``, not a blend").

* **the by-election term.** The deltas in ``bye`` arrive from
  ``byelections.py`` already recency-weighted — ``weighted[p] += w·d`` over
  ``weight_sum[p] += w`` with ``w = exp(−age/τ)·√votes·ρ``, so the decay is a
  weight on a MEAN and cancels for a single contest. This function must
  therefore apply that delta **once** and decay it no further. That is asserted
  as linearity: doubling the delta must move the centre by exactly ``w_bye ×
  delta``, which a second application of any factor would break.

  The double-decay defect the model log records is **not in this function**. It
  is the ward-local term at ``montecarlo.py:2575-2579``, which multiplies the
  move by ``decay`` and then accumulates ``decay × move`` over a denominator of
  ``decay``. That block is out of this seam and is reported separately; it is
  inert only because ``w_bye_local_*`` ship at 0.0.

* **absence is not the neutral value.** ARCHITECTURE.md's headline defect class.
  Three reads here take a default that is indistinguishable from a real value:
  ``prior_pr_share.get(party, 0.0)``, ``bands.get(party)`` → mode 1.0, and
  ``scenario.get("spine_level") or {}``. Each is tested for what it ACTUALLY
  does, with the docstring saying whether that is a contract or a latent
  defect. ``scenario["w_bye"]`` is the one read with no default, and the test
  that it raises is here to keep it that way.

* **the two mutations that survived §1.97's pass, closed.** Both live in the
  by-election clamp and neither was reachable from the tests as first written.
  ``mid = prior[party][1] or 1.0`` → ``mid = 1.0`` is the neutral-value
  substitution again, and it turns the clamp from a spread relative to the
  party's own central θ into an absolute one; it is closed by an INVARIANT —
  rescaling every end of a band changes no dispersion, so it must move no
  bound. The announcement's ``clamped != implied`` → ``clamped < implied``
  moves no number at all: it is a **provenance** defect, and the only one in
  this file tested purely as such. It silences a clamp that binds UPWARD, so
  the report shows a by-election implication next to a centre built from a
  figure the model never used.

**No expected value in this file is taken from what the code returns.** Every
one is either arithmetic done by hand on a constructed input (all inputs are
literals; there is no data file within a mile of this file), or an invariant
that must hold whatever the numbers are — conservation under the level shrink,
convexity of the poll blend, monotonicity in ``w_bye``, finiteness, and the
route identities above.

Run:
    ./.venv/bin/python tests/test_blended_centres.py
    ./.venv/bin/python -m pytest tests/test_blended_centres.py -q
"""

from __future__ import annotations

import math
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module  # noqa: E402

import montecarlo as M  # noqa: E402


# --------------------------------------------------------------------------
# fixtures: every input is a literal, so every expected value is hand arithmetic
# --------------------------------------------------------------------------

BASE = 0.10          # the party's national baseline share

# Four routes, four deliberately distinct answers for the SAME party, so that
# whichever branch fired is readable straight off the returned number.
POLL_LEVEL = 0.37                       # route 1  -> 0.37
SEED_BAND = (0.40, 2.50, 6.00)          # route 2  -> BASE * 2.50 = 0.25
SPINE_LEVEL = 0.31                      # route 3  -> 0.31
THETA_PRIOR = (0.50, 1.70, 4.00)        # route 4  -> BASE * 1.70 = 0.17


def _scenario(**over) -> dict:
    """A scenario with the by-election blend and the level shrink switched off.

    Both are identities at these settings by the source's own declaration
    (``level_shrink = 0.0`` is exactly the identity; ``w > 0`` gates the whole
    by-election block), so a routing test reads the route and nothing else.
    Each is switched back on in its own tests below.
    """
    scenario = {"w_bye": 0.0, "level_shrink": 0.0}
    scenario.update(over)
    return scenario


def _route_of(scenario: dict, party: str = "X", base: float = BASE) -> float:
    centres, _notes = M.blended_centres(scenario, {party: base}, {}, {})
    return centres[party]


@contextmanager
def _plan_bounds(bounds: dict):
    """Pin ``montecarlo.PLAN_BOUNDS`` for the duration of a test.

    ``apply_city`` REBINDS this module global (``montecarlo.py:867-873``), so a
    test that reads it as it finds it depends on whichever city some earlier
    test in the suite last selected. Pinning it makes the by-election clamp
    arithmetic below deterministic and independent of test order.
    """
    saved = M.PLAN_BOUNDS
    M.PLAN_BOUNDS = bounds
    try:
        yield
    finally:
        M.PLAN_BOUNDS = saved


class _RecordingTrace:
    """Enough of :class:`montecarlo.Trace` to see what was recorded."""

    def __init__(self):
        self.records: dict = {}

    def put(self, name, value=None, **_kw):
        self.records[name] = value
        return value


# --------------------------------------------------------------------------
# 1. the route precedence, pair by pair
# --------------------------------------------------------------------------

def test_a_poll_of_this_city_outranks_the_arrival_seed_for_the_same_party():
    """A polled arrival must take the poll's level, not the arrival record's.

    Both routes are live for exactly one class of party — one with no national
    baseline, seeded by ``pools.arrival_rules`` and also named by a metro poll
    — and this pair is reachable on real data: ASA is seeded at 0.0685 in
    ``pools_2021.json`` and named in four polls in ``polls.json``. The source
    states the intended order in as many words at ``montecarlo.py:1075``: *"A
    poll outranks the arrival record for a party with no record."*

    If this failed, a direct reading of the quantity being forecast would be
    overruled by an actuarial prior fitted to OTHER parties' arrivals.
    """
    centre = _route_of(_scenario(poll_levels={"X": POLL_LEVEL},
                                 pool_seeds={"X": 0.02},
                                 pool_seed_bands={"X": SEED_BAND}))
    assert math.isclose(centre, POLL_LEVEL, rel_tol=1e-12), (
        f"poll route lost to the seed: {centre} (poll says {POLL_LEVEL}, "
        f"the seed band's mode says {BASE * SEED_BAND[1]})")


def test_a_poll_of_this_city_outranks_the_spine():
    """The poll branch must sit above the spine branch, not below it.

    The spine (task #22, ``levels.spine``) reaches every party at every
    runnable target — the source says so at ``montecarlo.py:1086-1092``, which
    is why the three per-party fallback branches beneath it were deleted as
    dead. So if the poll branch were moved below the spine branch it would
    become dead code at every target, silently, and no existing test would
    notice: the ``poll_levels`` key would still be written by ``run_model``
    and still be read here, and nothing would ever come of it.
    """
    centre = _route_of(_scenario(poll_levels={"X": POLL_LEVEL},
                                 spine_level={"X": SPINE_LEVEL}))
    assert math.isclose(centre, POLL_LEVEL, rel_tol=1e-12), (
        f"poll route lost to the spine: {centre}")


def test_a_poll_of_this_city_outranks_the_theta_prior():
    """A poll must beat baseline × θ-mode, the weakest of the four routes.

    θ is a NATIONAL-to-local conversion factor. Applying it in preference to a
    direct local reading is the ActionSA 2021 failure recorded at
    ``montecarlo.py:1046-1058``: a correct 11.07% local estimate multiplied by
    1.50 and delivered to the drawer at 16.61%.
    """
    centre = _route_of(_scenario(poll_levels={"X": POLL_LEVEL},
                                 theta_prior={"X": THETA_PRIOR}))
    assert math.isclose(centre, POLL_LEVEL, rel_tol=1e-12), (
        f"poll route lost to the theta prior: {centre}")


def test_an_arrival_seed_outranks_the_spine():
    """A seeded arrival takes its band's mode on the seeded baseline.

    The spine weighs a party's national route against its own last local
    result. An arrival has neither record — that is what "arrival" means — so
    a spine level for it would be the common centre standing in for evidence
    that does not exist, while the seed IS the estimate the arrival record
    produced. Expected value is hand arithmetic: BASE × the band's mode.
    """
    centre = _route_of(_scenario(pool_seeds={"X": 0.02},
                                 pool_seed_bands={"X": SEED_BAND},
                                 spine_level={"X": SPINE_LEVEL}))
    assert math.isclose(centre, BASE * SEED_BAND[1], rel_tol=1e-12), (
        f"seed route lost to the spine: {centre} "
        f"(seed band mode says {BASE * SEED_BAND[1]})")


def test_an_arrival_seed_outranks_the_theta_prior():
    """The seed must beat θ — this pair is the ActionSA 2021 defect exactly.

    ``montecarlo.py:1046-1058`` records what happened when the seed branch was
    absent and a seeded arrival fell through to ``theta_mode``: a LOCAL
    estimate multiplied by a NATIONAL-to-local factor chosen with knowledge of
    what the party went on to do. The branch order is the fix; this test is
    what keeps it.
    """
    centre = _route_of(_scenario(pool_seeds={"X": 0.02},
                                 pool_seed_bands={"X": SEED_BAND},
                                 theta_prior={"X": THETA_PRIOR}))
    assert math.isclose(centre, BASE * SEED_BAND[1], rel_tol=1e-12), (
        f"seed route lost to the theta prior: {centre}")


def test_the_spine_outranks_the_theta_prior():
    """The spine must beat baseline × θ-mode wherever it has a level.

    ``montecarlo.py:1065-1070``: where the spine has a level *"it is the
    answer: it already weighed the party's national route against its own last
    local result by how much θ evidence the party has, and returned the
    blend"*. The θ-only branch is for a party the spine cannot reach. Inverting
    this pair would throw away the local half of every party's evidence and
    leave no trace in any output but the numbers.
    """
    centre = _route_of(_scenario(spine_level={"X": SPINE_LEVEL},
                                 theta_prior={"X": THETA_PRIOR}))
    assert math.isclose(centre, SPINE_LEVEL, rel_tol=1e-12), (
        f"spine route lost to the theta prior: {centre} "
        f"(theta says {BASE * THETA_PRIOR[1]})")


def test_the_four_routes_fire_in_order_as_each_higher_one_is_withdrawn():
    """The whole chain, in one construction: withdraw the winner, the next wins.

    The pairwise tests above can all pass while the chain still misbehaves for
    a party that has three or four routes at once (a seeded arrival that is
    polled AND has a spine level is not hypothetical — the spine reaches every
    party). This walks the ladder on a single party holding all four.
    """
    full = dict(poll_levels={"X": POLL_LEVEL},
                pool_seeds={"X": 0.02}, pool_seed_bands={"X": SEED_BAND},
                spine_level={"X": SPINE_LEVEL}, theta_prior={"X": THETA_PRIOR})
    ladder = [("poll_levels", POLL_LEVEL),
              ("pool_seeds", BASE * SEED_BAND[1]),
              ("spine_level", SPINE_LEVEL),
              (None, BASE * THETA_PRIOR[1])]
    for withdraw, expected in ladder:
        centre = _route_of(_scenario(**full))
        assert math.isclose(centre, expected, rel_tol=1e-12), (
            f"with routes {sorted(full)} live, expected {expected} "
            f"and got {centre}")
        if withdraw:
            full.pop(withdraw)


def test_a_party_with_a_baseline_and_no_route_at_all_raises_loudly():
    """No per-party fallback constant may be reintroduced by accident.

    MODEL-LOG §1.52 deleted ``theta_mode``, ``individual_theta`` and
    ``f_other`` — three branches that had been certified inert for weeks while
    still carried in ``DEFAULTS``, ``apply_city``, two city tomls and the
    register. The replacement is an ``AssertionError``. If this test failed,
    the level of a party the record cannot reach would once again be a number
    somebody typed for whichever parties they happened to name, and the run
    would not say so.
    """
    try:
        _route_of(_scenario())
    except AssertionError as exc:
        assert "spine" in str(exc) and "1.52" in str(exc), (
            f"the no-route failure no longer names the routes it tried: {exc}")
    else:
        raise AssertionError(
            "a party with a national baseline, no spine level, no theta prior "
            "and no arrival seed returned a level instead of raising")


def test_a_seed_of_zero_is_not_a_route_and_falls_through_to_the_spine():
    """The seed branch is gated on a POSITIVE seed, not on the key existing.

    ``seeded.get(party, 0.0) > 0``. A spec that emits a party at exactly 0.0 —
    ``pools_2016.json`` and ``pools_2026.json`` both ship ``seeds`` empty, so
    the zero case is a one-line change away — must fall through rather than
    pin that party's level at ``base × 1.0``. Were the gate ``party in
    seeded``, a zero seed would silently overrule the spine with the baseline
    itself, which is the neutral-value defect wearing a route's clothes.
    """
    centre = _route_of(_scenario(pool_seeds={"X": 0.0},
                                 pool_seed_bands={"X": SEED_BAND},
                                 spine_level={"X": SPINE_LEVEL}))
    assert math.isclose(centre, SPINE_LEVEL, rel_tol=1e-12), (
        f"a zero seed took the seed route: {centre}")


def test_a_seeded_party_with_no_band_is_placed_at_its_baseline_unannounced():
    """DOCUMENTS A NEUTRAL-VALUE READ. ``bands.get(party)`` missing means 1.0.

    ``mode_level = base * (float(band[1]) if band else 1.0)``. A seeded party
    whose band did not make it into the spec is placed at exactly its seeded
    baseline and NOTHING is recorded: ``notes`` gets no entry on the seed
    route at all, so the report cannot distinguish "the arrival record says
    this party is worth its seed" from "the band is missing".

    The value 1.0 is defensible on its own terms — ``montecarlo.py:1050-1053``
    says the arrival rules hand back a band *"whose mode is 1.0 (the seed IS
    the estimate)"* — so this is asserted as the current contract, not as a
    bug. What is asserted alongside it is the silence, which is the part that
    would let a spec regression through unseen.
    """
    scenario = _scenario(pool_seeds={"X": 0.02})       # no pool_seed_bands
    centres, notes = M.blended_centres(scenario, {"X": BASE}, {}, {})
    assert math.isclose(centres["X"], BASE, rel_tol=1e-12), (
        f"a bandless seed no longer lands on the baseline: {centres['X']}")
    assert "X" not in notes, (
        "the seed route now records a note — good; update this test, which "
        "exists to record that it did not")


def test_a_poll_level_for_a_party_outside_the_baseline_is_silently_discarded():
    """DOCUMENTS A SILENT DROP. The loop is over ``base_city``, not the routes.

    ``for party, base in base_city.items()`` — so a ``poll_levels`` entry for a
    party that is not in ``base_city`` produces no centre, no note, no warning
    and no error. And ``run_model`` writes ``poll_levels`` for precisely the
    parties with NO national baseline (``montecarlo.py:2830``: skip if
    ``baseline_before_seeds.get(_party, 0.0) > 0``), which are in
    ``base_city_d`` only if the pool spec ALSO seeded them.

    Today that holds by luck rather than by construction: ASA is both seeded
    and polled at 2021, and ``pools_2026.json`` ships no seeds at all while
    every polled party at 2026 has a 2024 national baseline. A polled arrival
    that the arrival rules do not seed would have the poll channel — measured
    at 48 coherent seats, §1.65 — do nothing for it, in silence.
    """
    scenario = _scenario(poll_levels={"GHOST": 0.20}, spine_level={"X": SPINE_LEVEL})
    centres, notes = M.blended_centres(scenario, {"X": BASE}, {}, {})
    assert "GHOST" not in centres and "GHOST" not in notes, (
        "a poll level for a party outside the baseline now produces a centre; "
        "this test recorded that it did not — re-derive the finding")
    assert set(centres) == {"X"}


def test_the_centres_returned_are_exactly_the_baseline_s_parties():
    """The router adds no party and drops none. A conservation check on keys.

    Downstream, ``index`` and the whole draw matrix are built from the same
    universe, and ``make_drawer`` reads ``centres[party]``. A router that
    dropped a party would surface as a ``KeyError`` far away, or worse as a
    zero.
    """
    base = {"A": 0.40, "B": 0.20, "C": 0.05}
    scenario = _scenario(spine_level={"A": 0.35, "B": 0.22, "C": 0.06})
    centres, _ = M.blended_centres(scenario, base, {}, {})
    assert set(centres) == set(base)


# --------------------------------------------------------------------------
# 2. poll_credence — MODEL-LOG §1.95
# --------------------------------------------------------------------------

def test_the_shipped_poll_credence_is_one_and_one_is_exactly_the_identity():
    """§1.95's whole claim: adding the dial moved no number. Now permanent.

    *"1.0 is the identity and the shipped default, so adding this moves no
    number: it is the sigma arithmetic's own answer, untouched."* That was
    verified once against the freeze, by hand. If it ever stops being true —
    a rescaling of the dial, a floor, a non-linearity — every number in the
    published forecast moves and the register still says the default is inert.

    Asserted two ways: the returned weight is the raw weight EXACTLY, and the
    centre equals the two-point interpolation ``mu + w(share − mu)``, which is
    a different expression from the one the source evaluates.
    """
    assert M.DEFAULTS["poll_credence"] == 1.0, (
        "the shipped poll_credence is no longer 1.0; the identity claim in "
        "MODEL-LOG §1.95 no longer covers the default run")
    for mu, share, w_raw in [(0.30, 0.24, 0.00), (0.30, 0.24, 0.35),
                             (0.05, 0.11, 0.5761), (0.42, 0.42, 0.80),
                             (0.10, 0.90, 1.00)]:
        centre, w = M.blend_poll_centre(mu, share, w_raw,
                                        M.DEFAULTS["poll_credence"])
        assert w == w_raw, f"credence 1.0 moved the weight {w_raw} to {w}"
        assert math.isclose(centre, mu + w_raw * (share - mu), rel_tol=1e-12,
                            abs_tol=1e-15), (
            f"credence 1.0 is not the identity at (mu={mu}, share={share}, "
            f"w={w_raw}): {centre}")
        # and it is the same as not passing the dial at all
        assert M.blend_poll_centre(mu, share, w_raw) == (centre, w)


def test_a_poll_credence_of_zero_returns_the_modelled_centre_untouched():
    """0.0 must ignore the poll exactly, not approximately.

    §1.95 gives 0.0 as "the metro half of ``poll_paths='off'``", so it has to
    be an exact off switch: a residual weight of 1e-16 would make an A/B of
    the poll channel report a difference that is float noise, and the channel
    is currently worth −6 coherent seats (§1.94) — an effect small enough to
    be confused with exactly that.
    """
    for mu, share, w_raw in [(0.30, 0.24, 0.35), (0.05, 0.90, 1.0)]:
        centre, w = M.blend_poll_centre(mu, share, w_raw, 0.0)
        assert w == 0.0
        assert centre == mu, f"credence 0 moved the centre {mu} to {centre}"


def test_a_poll_credence_above_one_is_clamped_at_full_poll_weight():
    """The clamp must BIND above 1, or credence becomes an extrapolator.

    Without the upper clamp, ``w > 1`` makes the result an EXTRAPOLATION
    beyond the poll — ``(1−w)·mu + w·share`` with ``w = 1.4`` lands further
    from the model than the poll itself, which no reading of "believe the poll
    more" supports. §1.95 says "above 1.0 leans in"; leaning in has to stop at
    the poll.
    """
    centre, w = M.blend_poll_centre(0.30, 0.24, 0.60, 5.0)
    assert w == 1.0, f"a credence of 5.0 on w=0.60 gave w={w}, not 1.0"
    assert centre == 0.24, f"clamped weight did not return the poll: {centre}"
    # and below the clamp the dial is exactly multiplicative
    centre, w = M.blend_poll_centre(0.30, 0.24, 0.40, 2.0)
    assert math.isclose(w, 0.80, rel_tol=1e-12)
    assert math.isclose(centre, 0.30 + 0.80 * (0.24 - 0.30), rel_tol=1e-12)
    # a negative credence is clamped at the other end rather than reversing
    centre, w = M.blend_poll_centre(0.30, 0.24, 0.40, -3.0)
    assert w == 0.0 and centre == 0.30


def test_the_poll_blend_is_convex_and_monotone_in_credence():
    """The result may never overshoot the poll or move away from it.

    Both properties are stated as invariants in ``blend_poll_centre``'s own
    docstring, and they are what makes the dial safe to expose to a reader in
    the interactive: whatever they set, the centre stays between what the
    model thought and what the poll said, and more belief never means less
    movement. Checked over a grid rather than at a point, because a clamp
    applied in the wrong place passes at 0 and 1 and fails in between.
    """
    mu, share = 0.32, 0.19
    previous = mu
    for step in range(0, 41):
        credence = step * 0.1                      # 0.0 .. 4.0
        centre, w = M.blend_poll_centre(mu, share, 0.45, credence)
        assert 0.0 <= w <= 1.0, f"weight escaped [0,1] at credence {credence}"
        assert share - 1e-15 <= centre <= mu + 1e-15, (
            f"centre {centre} left [{share}, {mu}] at credence {credence}")
        assert centre <= previous + 1e-15, (
            f"more credence moved the centre back towards the model at "
            f"{credence}: {previous} -> {centre}")
        previous = centre


# --------------------------------------------------------------------------
# 3. the by-election term
# --------------------------------------------------------------------------

def test_the_by_election_delta_enters_the_centre_exactly_once():
    """Linearity in the delta. A second application of anything breaks it.

    ``byelections.py`` already divides ``Σ w·d`` by ``Σ w`` with
    ``w = exp(−age/τ)·√votes·ρ``, so what arrives in ``bye`` is a
    recency-weighted MEAN delta and the decay has already been applied — once,
    and as a weight that cancels for a single contest. This function must
    therefore add it to the previous LGE's PR share once and decay it no
    further.

    The assertion is a slope, not a value: with the clamp slack, the centre
    must be affine in the delta with slope exactly ``w_bye``. Squaring the
    delta, applying a second decay factor, or adding it twice all fail this,
    and none of them would fail a single-point check chosen to match.
    """
    with _plan_bounds({}):                     # (0.0, inf) -> the clamp is slack
        w_bye = 0.5
        centres = []
        for delta in (0.02, 0.04):
            scenario = _scenario(w_bye=w_bye, spine_level={"X": 0.20})
            got, _ = M.blended_centres(scenario, {"X": BASE}, {"X": 0.18},
                                       {"X": (100.0, delta)})
            centres.append(got["X"])
        # hand arithmetic: (1-w)·0.20 + w·(0.18 + delta)
        assert math.isclose(centres[0], 0.5 * 0.20 + 0.5 * 0.20, rel_tol=1e-12)
        assert math.isclose(centres[1], 0.5 * 0.20 + 0.5 * 0.22, rel_tol=1e-12)
        assert math.isclose(centres[1] - centres[0], w_bye * 0.02, rel_tol=1e-12), (
            f"the centre moved {centres[1] - centres[0]:.6f} for a delta step "
            f"of 0.02 at w_bye {w_bye}; exactly once means {w_bye * 0.02:.6f}")


def test_the_by_election_blend_is_monotone_in_w_bye_between_the_two_levels():
    """w_bye must be a convex weight, so 0 and 1 are the two pure answers.

    ``w_bye`` is registered at 0.40 as a §3.5 judgement call in the range 0–1
    and is swept. A sweep of a lever that is not monotone in its own range
    cannot be read, and the two endpoints are what "blends the evidence in at
    weight w" means: 0 is the modelled level, 1 is the (clamped) by-election
    implication.
    """
    with _plan_bounds({}):
        mode, prior_pr, delta = 0.20, 0.18, 0.06     # implied 0.24, above mode
        previous = None
        for step in range(0, 11):
            w = step / 10.0
            scenario = _scenario(w_bye=w, spine_level={"X": mode})
            centres, _ = M.blended_centres(scenario, {"X": BASE},
                                           {"X": prior_pr}, {"X": (100.0, delta)})
            centre = centres["X"]
            assert mode - 1e-15 <= centre <= 0.24 + 1e-15, (
                f"centre {centre} left [{mode}, 0.24] at w_bye {w}")
            if previous is not None:
                assert centre >= previous - 1e-15, (
                    f"w_bye {w} moved the centre back: {previous} -> {centre}")
            previous = centre
        assert math.isclose(previous, 0.24, rel_tol=1e-12), (
            f"w_bye 1.0 did not reach the by-election implication: {previous}")


def test_w_bye_of_zero_removes_the_by_election_contribution_entirely():
    """0.0 is an exact off switch, and it leaves no note behind either.

    The whole block is gated on ``w > 0``, so at 0.0 not one line of it runs.
    That matters beyond the arithmetic: ``notes`` is what the report prints as
    the reason for a party's level, and a note claiming a by-election
    adjustment at weight zero would be a false explanation of a number.
    """
    scenario = _scenario(w_bye=0.0, spine_level={"X": SPINE_LEVEL})
    centres, notes = M.blended_centres(scenario, {"X": BASE}, {"X": 0.18},
                                       {"X": (10_000.0, 0.25)})
    assert centres["X"] == SPINE_LEVEL, (
        f"w_bye 0.0 still moved the centre: {centres['X']}")
    assert "X" not in notes


def test_a_by_election_weight_below_the_minimum_is_ignored_entirely():
    """``BYE_MIN_WEIGHT`` must bind, or one small contest can set a level.

    The weights are ``exp(−age/τ)·√votes·ρ``, so a single stale low-turnout
    contest in an atypical ward can carry a large delta on a weight of a few
    units. The gate is what stops that reaching a citywide level. Asserted on
    both sides of the threshold, from the module's own constant rather than a
    copy of it, so a deliberate change to the constant does not fail here — a
    deliberate change to the RULE does.
    """
    for weight, moves in [(M.BYE_MIN_WEIGHT - 0.001, False),
                          (M.BYE_MIN_WEIGHT, True)]:
        with _plan_bounds({}):
            scenario = _scenario(w_bye=0.5, spine_level={"X": 0.20})
            centres, notes = M.blended_centres(
                scenario, {"X": BASE}, {"X": 0.18}, {"X": (weight, 0.06)})
        if moves:
            assert centres["X"] > 0.20 and "X" in notes, (
                f"a weight at the minimum {weight} was ignored")
        else:
            assert centres["X"] == 0.20 and "X" not in notes, (
                f"a weight of {weight}, below BYE_MIN_WEIGHT "
                f"{M.BYE_MIN_WEIGHT}, moved the centre to {centres['X']}")


def test_the_by_election_clamp_is_relative_to_the_level_not_to_the_baseline():
    """The ActionSA 2026 case, which is why the clamp was rewritten.

    ``montecarlo.py:1119-1136`` records it: the spine put ActionSA at 15.2%
    from its own 2021 local result, the by-elections independently implied
    18.7%, and a clamp computed as ``high × 5.99% national`` cut that to 7.5%
    and dragged the blended centre DOWN to 12.1%. Two pieces of evidence
    agreeing the party is larger than its national share were overruled by a
    bound derived from the national share.

    So the band is applied as a RELATIVE spread — ``low/mid`` and ``high/mid``
    — around whatever level the router settled on. Reconstructed here with the
    real proportions: baseline 5.99%, level 15.2%, implication 18.7%, band
    mode 1.0 with a high of 1.30. ``high/mid × level`` = 19.76% leaves the
    implication untouched; ``high × baseline`` = 7.79% would not, and would
    pull the centre below the level. Both are asserted.
    """
    base, level, implied_target, high = 0.0599, 0.152, 0.187, 1.30
    delta = implied_target - 0.0                  # no previous-LGE PR share
    with _plan_bounds({}):
        scenario = _scenario(w_bye=0.40, spine_level={"X": level},
                             theta_prior={"X": (0.70, 1.00, high)})
        centres, notes = M.blended_centres(scenario, {"X": base}, {},
                                           {"X": (100.0, delta)})
    centre = centres["X"]
    assert math.isclose(centre, 0.60 * level + 0.40 * implied_target,
                        rel_tol=1e-12), (
        f"the clamp bound where it should have been slack: {centre}")
    assert centre > level, (
        "two pieces of evidence agreeing the party is larger than its national "
        "share were overruled by a bound derived from the national share — the "
        "defect at montecarlo.py:1119-1136 is back")
    assert centre > 0.60 * level + 0.40 * (high * base), (
        "the clamp is anchored on the national baseline again")
    assert "clamped" not in notes["X"], notes["X"]


def test_the_by_election_clamp_binds_on_an_absurd_implication():
    """The clamp is not decoration: a runaway implication is cut, and said so.

    §3.5's ranges exist so *"a concentrated party's stronghold swing cannot
    claim an absurd citywide level"*. With the band's high at 1.30 of its mode
    and the router's level at 20%, an implication of 90% must be cut to 26%
    exactly, and the note must say it was cut — a clamp that binds silently
    would leave the report claiming the by-elections implied a number the model
    never used.
    """
    with _plan_bounds({}):
        scenario = _scenario(w_bye=0.50, spine_level={"X": 0.20},
                             theta_prior={"X": (0.70, 1.00, 1.30)})
        centres, notes = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                           {"X": (100.0, 0.90)})
    assert math.isclose(centres["X"], 0.5 * 0.20 + 0.5 * (1.30 * 0.20),
                        rel_tol=1e-12), centres["X"]
    assert "clamped to 26.0%" in notes["X"], notes["X"]


def test_the_theta_band_is_divided_by_its_own_mode_before_it_clamps():
    """The band is a RELATIVE spread. Every other clamp test has a mode of 1.00.

    ``clamped = min(max(implied, (low/mid)·anchor), (high/mid)·anchor)``, and
    ``montecarlo.py:1133-1135`` says why: the band is applied *"as a RELATIVE
    spread — low/mode and high/mode, which is what θ's dispersion actually
    measures — around whatever central level the spine settled on"*. θ's band
    is a band on the NATIONAL route, so its absolute scale is a
    national-to-local factor; only the RATIO to its own mode is dispersion.

    Dropping the ``/ mid`` is invisible to every other test in this file,
    because each of them uses a band whose mode is exactly 1.00 and ``x/1.0``
    is ``x``. On a band of (1.00, 2.00, 3.00) it is not invisible: the party
    could be half or one-and-a-half times its central estimate, so a level of
    20% admits 10%–30%. Without the division the same band would licence 20%
    and 60% — a clamp that widens sixfold at the top because the θ SCALE is 2,
    which is the national-share reasoning the ActionSA 2026 rewrite removed.
    Both ends are asserted, at ``w_bye`` 1.0 so the clamped value IS the centre.
    """
    band, level, anchor = (1.00, 2.00, 3.00), 0.20, 0.20
    for delta, expected, said in [(0.90, 1.50 * anchor, "clamped to 30.0%"),
                                  (0.01, 0.50 * anchor, "clamped to 10.0%")]:
        with _plan_bounds({}):
            scenario = _scenario(w_bye=1.0, spine_level={"X": level},
                                 theta_prior={"X": band})
            centres, notes = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                               {"X": (100.0, delta)})
        assert math.isclose(centres["X"], expected, rel_tol=1e-12), (
            f"band {band} on a level of {level} clamped an implication of "
            f"{delta:.0%} to {centres['X']:.4f}, not {expected:.4f}; the band "
            f"is being read as an absolute multiplier, not as a spread "
            f"relative to its own mode")
        assert said in notes["X"], notes["X"]


def test_a_clamp_that_binds_from_below_is_announced_as_a_clamp():
    """§3.5's range is two-sided, and the note must say so at BOTH ends.

    The clamp binding upward is tested above; this is the other side, where
    the by-elections imply a COLLAPSE the band forbids and the model uses
    ``(low/mid)·anchor`` instead. The number and the note are separate claims:
    the note is what the run prints as why a party is where it is, and a clamp
    that binds silently leaves the report saying the by-elections implied a
    number the model never used — the same false-explanation defect recorded
    for the poll route below.

    The announcement condition must therefore be *"the number used is not the
    number implied"*, not *"the implication was too high"*. Hand arithmetic:
    band (0.70, 1.00, 1.30) on a level of 20% floors at 14%; an implication of
    2% is lifted to 14%, and at ``w_bye`` 0.5 the centre is 17%.
    """
    with _plan_bounds({}):
        scenario = _scenario(w_bye=0.50, spine_level={"X": 0.20},
                             theta_prior={"X": (0.70, 1.00, 1.30)})
        centres, notes = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                           {"X": (100.0, 0.02)})
    assert math.isclose(centres["X"], 0.5 * 0.20 + 0.5 * 0.14, rel_tol=1e-12), (
        f"the floor did not bind: {centres['X']}")
    assert "clamped to 14.0%" in notes["X"], (
        f"the clamp bound from below and the note does not say so: {notes['X']}")


def test_the_clamp_band_is_scale_invariant_because_only_the_ratio_is_dispersion():
    """MUTATION GUARD: ``mid = prior[party][1] or 1.0`` → ``mid = 1.0``.

    ARCHITECTURE.md's headline defect class, in its purest form: a divisor
    replaced by the neutral value 1.0. The line still reads plausibly, nothing
    raises, and the clamp goes on clamping — but it stops being a spread
    RELATIVE to the party's own central θ and becomes an ABSOLUTE one, which is
    the national-share reasoning the ActionSA 2026 rewrite
    (``montecarlo.py:1176-1194``) exists to have removed.

    The test is an INVARIANT rather than a second hand-computed number, because
    the invariant is what the mechanism claims. θ is a ratio — a local share
    over a national one — so the band ``(low, mid, high)`` carries two separable
    things: a SCALE (roughly ``mid``, a national-to-local conversion factor) and
    a DISPERSION (``low/mid`` and ``high/mid``). Only the second is a statement
    about how far the party might be from its own central estimate. Multiplying
    all three ends of the band by the same positive constant therefore changes
    the scale and changes no dispersion at all, so **the admissible interval
    around the router's level must not move**.

    Here the band is ``(0.60, 1.20, 1.80) × c`` for four values of ``c`` spanning
    a factor of fourteen. Its dispersion is 0.5 and 1.5 at every ``c``, so on a
    level of 20% the clamp must admit exactly 10%–30% at every ``c``. With the
    divisor gone the interval is ``(0.60c, 1.80c) × 20%`` and drags the centre
    with it — 36% at ``c = 1``, 252% at ``c = 7``, an implied citywide level
    above 100% of the vote. ``w_bye`` is 1.0 so the clamped value IS the centre
    and nothing else is in the way.
    """
    level, tops, bottoms = 0.20, [], []
    for c in (0.5, 1.0, 2.0, 7.0):
        band = (0.60 * c, 1.20 * c, 1.80 * c)
        for delta, sink in ((0.90, tops), (0.01, bottoms)):
            with _plan_bounds({}):
                scenario = _scenario(w_bye=1.0, spine_level={"X": level},
                                     theta_prior={"X": band})
                centres, _ = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                               {"X": (100.0, delta)})
            sink.append((c, centres["X"]))
    for label, got, expected in (("high", tops, 1.5 * level),
                                 ("low", bottoms, 0.5 * level)):
        for c, value in got:
            assert math.isclose(value, expected, rel_tol=1e-12), (
                f"the {label} end of a band scaled by {c} clamped to {value:.4f}, "
                f"not {expected:.4f}; the band's SCALE is being read as "
                f"dispersion — divide it by its own mode")
        assert len({v for _, v in got}) == 1, (
            f"the {label} clamp bound moved when the whole band was rescaled: "
            f"{got}. Rescaling every end of a band changes no dispersion, so it "
            f"must change no bound")


def test_a_theta_mode_of_zero_falls_back_to_a_neutral_divisor_rather_than_raising():
    """The ``or 1.0`` on the divisor, pinned — and WHY 1.0 looks harmless there.

    This is the companion to the test above and closes nothing that test
    closes: a mode of exactly zero is the one input for which ``mid = 1.0`` is
    the RIGHT answer, and its presence one line away is precisely what makes
    the neutral-value substitution look plausible to a reader. Pinned separately so
    the two claims cannot be confused: the fallback fires only at zero, and
    everywhere else the real mode divides.

    Zero is not reachable through ``levels.theta_prior`` today, but it is the
    value a missing or short band would arrive as, and ``low / 0.0`` raises
    ``ZeroDivisionError`` from inside a loop over parties — a crash, mid-run,
    for one party's malformed band. The declared behaviour is that the clamp
    degrades to the band read absolutely, not that the run dies.
    """
    with _plan_bounds({}):
        scenario = _scenario(w_bye=1.0, spine_level={"X": 0.20},
                             theta_prior={"X": (0.50, 0.0, 2.00)})
        centres, _ = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                       {"X": (100.0, 0.90)})
    assert math.isclose(centres["X"], 2.00 * 0.20, rel_tol=1e-12), centres["X"]


def test_the_clamp_is_announced_whenever_the_number_used_is_not_the_number_implied():
    """MUTATION GUARD: ``if clamped != implied`` → ``if clamped < implied``.

    **This is a test about PROVENANCE, not about arithmetic.** No centre moves
    under this mutation; every number the model reports is unchanged. What
    changes is the note, and the note is the only thing that tells a reader
    where a centre came from. ``notes`` is what the run prints as why a party is
    where it is, and with the comparison flipped a clamp that binds UPWARD — the
    by-elections implied a collapse and §3.5's range forbade it — goes
    unannounced: the report then says *"by-elections imply 6.3%"* next to a
    centre built from 12.5%, a figure the model never used. That is CLAUDE.md's
    standing complaint in miniature — a record that looks current and cannot be
    — and it is worth a test for that reason alone, with no number at stake.

    The condition is therefore stated as the thing a reader needs: **announce
    exactly when the number used is not the number implied**, at either end,
    and stay silent when it is. Five cases on a band of (0.5, 1.0, 1.5) around
    a level of 25% — floor 12.5%, ceiling 37.5%, both exact in binary so the
    two boundary cases are not float noise:

        implied  6.25% → lifted to 12.5%   announced   (dies on ``<``)
        implied 90%    → cut to 37.5%      announced   (dies on ``>``)
        implied 25%    → untouched         silent      (dies on a bare ``True``)
        implied 12.5%  → equals the floor  silent
        implied 37.5%  → equals the ceiling silent

    Each announcement is also required to carry BOTH figures, so the reader can
    see the implication and the number that replaced it, and the announced
    figure is checked against the centre it produced.
    """
    level, w, band = 0.25, 0.50, (0.5, 1.0, 1.5)
    floor, ceiling = 0.125, 0.375
    cases = [(0.0625, floor, "clamped to 12.5%"),
             (0.90, ceiling, "clamped to 37.5%"),
             (0.25, None, None),
             (floor, None, None),
             (ceiling, None, None)]
    for implied, clamped, phrase in cases:
        with _plan_bounds({}):
            scenario = _scenario(w_bye=w, spine_level={"X": level},
                                 theta_prior={"X": band})
            centres, notes = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                               {"X": (100.0, implied)})
        used = clamped if clamped is not None else implied
        assert math.isclose(centres["X"], (1 - w) * level + w * used,
                            rel_tol=1e-12), (
            f"an implication of {implied:.4f} produced {centres['X']:.4f}, not "
            f"the {used:.4f} this case is built on")
        assert f"by-elections imply {implied:.1%}" in notes["X"], notes["X"]
        if phrase is None:
            assert "clamped" not in notes["X"], (
                f"an implication of {implied:.1%} was used unchanged and the "
                f"note claims it was clamped: {notes['X']}")
        else:
            assert phrase in notes["X"], (
                f"the clamp {'lifted' if clamped > implied else 'cut'} "
                f"{implied:.1%} to {clamped:.1%} and the note does not say so: "
                f"{notes['X']}. The announcement condition is 'the number used "
                f"is not the number implied', at BOTH ends — not 'the "
                f"implication was too high'")


def test_plan_bounds_are_recorded_as_read_when_a_party_has_no_theta_band():
    """A hand-typed constant that is consumed must be declared as consumed.

    ``note_constant``'s docstring gives the reason: ``backtest.in_sample_banner``
    was asserting ``theta_mode`` "is no longer read" while target 2021 quietly
    took ActionSA's 1.50 from it. ``PLAN_BOUNDS`` is the same kind of number —
    the plan's §3.5 sanity range, typed by a person — and this is the branch
    that reaches it. If the record were dropped, a backtest could take a
    hand-typed bound and report itself out-of-sample.
    """
    with _plan_bounds({"X": (0.65, 0.90)}):
        scenario = _scenario(w_bye=0.50, spine_level={"X": 0.20})
        M.blended_centres(scenario, {"X": BASE}, {"X": 0.18},
                          {"X": (100.0, 0.30)})
    assert "X" in scenario["_constants_read"]["plan_bounds"], (
        "PLAN_BOUNDS was consumed and not recorded as read")


def test_a_zero_level_falls_back_to_the_baseline_as_the_clamp_anchor():
    """``anchor = mode_level if mode_level > 0 else base`` — the guard branch.

    A relative band around a level of zero is a band of zero width: the
    by-election evidence would be clamped to exactly 0.0 whatever it said, and
    a party the router placed at zero could never be moved off it by any
    contest. The fallback to the national baseline is what stops that, and it
    is a branch nothing else exercises.
    """
    with _plan_bounds({}):
        scenario = _scenario(w_bye=1.0, spine_level={"X": 0.0},
                             theta_prior={"X": (0.50, 1.00, 2.00)})
        centres, _ = M.blended_centres(scenario, {"X": BASE}, {"X": 0.0},
                                       {"X": (100.0, 0.90)})
    # clamp high = (2.00/1.00) × BASE = 0.20, and w_bye 1.0 takes it whole
    assert math.isclose(centres["X"], 2.00 * BASE, rel_tol=1e-12), centres["X"]


def test_a_party_absent_from_the_previous_pr_shares_is_read_as_having_polled_zero():
    """DOCUMENTS A NEUTRAL-VALUE READ. ``prior_pr_share.get(party, 0.0)``.

    ARCHITECTURE.md's defect class, in this function: absence and a genuine
    zero are the same value here. For a party that did not stand at the
    previous LGE, zero IS the right base and ``byelections.py`` says so — *"a
    party with no votes at the previous LGE has its deltas measured against a
    zero base"*. For a ``prior_pr_share`` that arrived empty or short because
    the previous LGE's file did not load, it is not: every by-election party's
    implied level collapses to its delta alone — a number near zero — the
    clamp then drags it up to ``low/mid × level``, and the centres move with
    no error, no warning and no note that anything was missing.

    The behaviour is pinned as it stands, and the two cases are shown to be
    indistinguishable from inside the function: the same call, with the party
    absent and with it present at 0.0, returns the identical number.
    """
    with _plan_bounds({}):
        out = []
        for prior_pr in ({}, {"X": 0.0}):
            scenario = _scenario(w_bye=0.50, spine_level={"X": 0.20})
            centres, _ = M.blended_centres(scenario, {"X": BASE}, prior_pr,
                                           {"X": (100.0, 0.04)})
            out.append(centres["X"])
    assert out[0] == out[1], (
        "an absent previous-LGE share and one of exactly 0.0 now differ; the "
        "neutral-value read this test documents has been closed")
    assert math.isclose(out[0], 0.5 * 0.20 + 0.5 * 0.04, rel_tol=1e-12), out[0]


def test_the_poll_route_note_is_carried_through_the_by_election_block():
    """RE-RECORDED 2026-08-28. The note appends now; it used to overwrite (F38).

    This pinned the defect and said so in its own failure message — *"the note
    now carries the poll route through the by-election block — good; this test
    recorded that it did not"*. Both its assertions invert here, which is the
    outcome it was written to detect.

    A party whose level came from a poll and was then tilted by by-elections
    reported only the second half. The metro-poll block later already appended;
    this one did not, so the run's per-party explanation — the first thing a
    reader checks — dropped the route that set the level.

    **Latent today**: the poll route and the by-election block are mutually
    exclusive at every target that exists. `national_polls` returns nothing at
    2026 (both admitted polls are metro-scope) and `bye` is empty at all
    sixteen backtest city-years. It becomes reachable the moment a national
    poll declared for 2026 names a seeded arrival that also clears
    `BYE_MIN_WEIGHT` — `ALL_CITIZENS_PARTY` (49.55) and
    `TRUTH_AND_SOLIDARITY_MOVEMENT` (30.58) are exactly that shape today,
    lacking only the seed and the poll.

    The note also stopped saying "θ-mode" for routes that are not a θ mode —
    at joburg 2026 all nine tilted parties took the SPINE route, so that label
    was wrong for every one of them on the live forecast.
    """
    scenario = _scenario(w_bye=0.50, poll_levels={"X": 0.20})
    _, notes = M.blended_centres(scenario, {"X": BASE}, {"X": 0.18},
                                 {"X": (100.0, 0.04)})
    note = notes["X"]
    assert note.startswith("level from poll: "), (
        f"the poll route's note no longer leads — the by-election block has "
        f"gone back to overwriting it: {note!r}")
    assert " | " in note, (
        f"the two contributions are not separated; the note should read in "
        f"the order they were applied: {note!r}")
    assert "by-elections imply" in note, (
        f"the by-election half is missing: {note!r}")
    assert "θ-mode" not in note, (
        f"the note calls a poll-route level a θ-mode: {note!r}. Only the "
        f"`prior` branch is a θ mode; the other three are not.")

def test_a_missing_w_bye_raises_rather_than_meaning_zero():
    """The one input read WITHOUT a default, and it must stay that way.

    ``w = scenario["w_bye"]``. Every other read in this function takes a
    default that is indistinguishable from a real value; this one does not, so
    a scenario that forgot the key fails loudly instead of silently switching
    the whole by-election channel off. That is the shape ARCHITECTURE.md's bus
    generalises ("``bus.read(name)`` has no ``default=`` parameter"), already
    present in one line here.
    """
    scenario = {"level_shrink": 0.0, "spine_level": {"X": SPINE_LEVEL}}
    try:
        M.blended_centres(scenario, {"X": BASE}, {}, {})
    except KeyError as exc:
        assert "w_bye" in str(exc)
    else:
        raise AssertionError(
            "a scenario with no w_bye ran anyway; the by-election channel can "
            "now be switched off by omission, which is unreadable from output")


# --------------------------------------------------------------------------
# 4. what leaves the function
# --------------------------------------------------------------------------

def test_every_centre_is_finite_and_positive_on_a_mixed_scenario():
    """A non-finite centre would reach the drawer and poison a whole run.

    Four parties, one on each route, with the by-election term and the level
    shrink both live at their shipped settings. ``logit`` of a centre at 0 or 1
    is infinite and a NaN propagates through the Dirichlet silently, so this is
    the cheapest guard there is on a function that multiplies, divides and
    renormalises.
    """
    base = {"P": 0.30, "Q": 0.10, "R": 0.06, "S": 0.02}
    scenario = _scenario(
        w_bye=M.DEFAULTS["w_bye"],
        level_shrink=M.DEFAULTS["level_shrink"],
        level_shrink_scale=M.DEFAULTS["level_shrink_scale"],
        poll_levels={"P": 0.28},
        pool_seeds={"Q": 0.03}, pool_seed_bands={"Q": SEED_BAND},
        spine_level={"R": 0.07}, theta_prior={"S": THETA_PRIOR})
    with _plan_bounds({}):
        centres, _ = M.blended_centres(
            scenario, base, {"P": 0.26, "R": 0.05},
            {"P": (100.0, 0.03), "R": (100.0, -0.01)})
    assert set(centres) == set(base)
    for party, value in centres.items():
        assert math.isfinite(value), f"{party} centre is {value}"
        assert 0.0 < value < 1.0, f"{party} centre is {value}, outside (0, 1)"


def test_the_centres_do_not_collapse_to_the_baseline_when_the_spine_is_absent():
    """An empty spine degrades to the θ route silently — assert it degrades.

    ``spine_level = scenario.get("spine_level") or {}``. ``run_model`` sets the
    key only ``if _spine:``, and prints a warning on ``FileNotFoundError``
    alone — any other empty result is silent. The failure mode worth catching
    is not the silence (which is recorded as a finding) but a router that,
    having lost the spine, hands back the BASELINE for every party: numerically
    plausible, structurally the model doing nothing, and invisible in any
    output but a backtest.
    """
    base = {"A": 0.40, "B": 0.10}
    prior = {"A": (0.60, 0.75, 0.95), "B": (1.00, 1.45, 2.10)}
    scenario = _scenario(theta_prior=prior)          # no spine_level at all
    centres, _ = M.blended_centres(scenario, base, {}, {})
    for party in base:
        assert math.isclose(centres[party], base[party] * prior[party][1],
                            rel_tol=1e-12), (
            f"{party} came back at {centres[party]}, not baseline × θ-mode")
        assert centres[party] != base[party], (
            f"{party}'s centre is its baseline unchanged; the level layer did "
            f"nothing and said nothing")


def test_the_level_shrink_conserves_the_total_and_the_ordering():
    """The shrink's own claim, checked at this seam: a redistribution, not a cut.

    ``compress_levels`` *"pulls each central level down by its own size, then
    gives the mass back"* by renormalising to the original total. Two calls
    differing only in ``level_shrink`` therefore have to sum to the same
    number, keep every party's rank, and pull the large down relative to the
    small — the ordering IS the claim (§1.44), and it is checkable here
    without running a draw.
    """
    base = {"A": 0.40, "B": 0.20, "C": 0.10, "D": 0.03}
    spine = {"A": 0.42, "B": 0.19, "C": 0.11, "D": 0.04}
    plain, _ = M.blended_centres(_scenario(spine_level=spine), base, {}, {})
    shrunk, _ = M.blended_centres(
        _scenario(spine_level=spine,
                  level_shrink=M.DEFAULTS["level_shrink"],
                  level_shrink_scale=M.DEFAULTS["level_shrink_scale"]),
        base, {}, {})
    assert math.isclose(sum(shrunk.values()), sum(plain.values()), rel_tol=1e-12), (
        f"the shrink did not conserve the total: {sum(plain.values())} -> "
        f"{sum(shrunk.values())}")
    order = sorted(plain, key=lambda p: -plain[p])
    assert sorted(shrunk, key=lambda p: -shrunk[p]) == order, (
        "the shrink reordered the parties")
    ratios = [shrunk[p] / plain[p] for p in order]
    assert ratios == sorted(ratios), (
        f"the pull is not monotone in size: {dict(zip(order, ratios))}")
    assert ratios[0] < 1.0 < ratios[-1], (
        f"the largest party was not pulled down or the smallest not lifted: "
        f"{dict(zip(order, ratios))}")


def test_the_shipped_level_shrink_is_not_the_identity():
    """A lever-is-live check on the one that moves every party's level.

    ``level_shrink`` ships at 0.35 and ``ITERATING.md`` rule 6 is exactly this:
    before trusting a constant, confirm it changes the answer. A shrink that
    had gone inert — a guard inverted, a key renamed, the scale read from a
    default of zero — would leave the model over-forecasting the top of the
    ballot by the +32.30pp the correction was built to remove, and every test
    above would still pass because they set it to 0.0.
    """
    base = {"A": 0.40, "B": 0.03}
    spine = {"A": 0.40, "B": 0.03}
    plain, _ = M.blended_centres(_scenario(spine_level=spine), base, {}, {})
    shipped, _ = M.blended_centres(
        _scenario(spine_level=spine,
                  level_shrink=M.DEFAULTS["level_shrink"],
                  level_shrink_scale=M.DEFAULTS["level_shrink_scale"]),
        base, {}, {})
    assert not math.isclose(shipped["A"], plain["A"], rel_tol=1e-6), (
        f"the shipped level_shrink {M.DEFAULTS['level_shrink']} moved the "
        f"largest party by nothing: {plain['A']} -> {shipped['A']}")


def test_the_trace_records_the_shrink_and_changes_no_number():
    """``--run-dir`` is a record, not a stage. CLAUDE.md: "changes no number".

    The trace exists so an investigation does not have to add a print and
    re-run 169 seconds of comparison. The moment it can alter a result it stops
    being free to switch on, so the same call with and without one must agree
    exactly — and the record must actually contain the before/after pair the
    shrink's ordering claim is read from.
    """
    base = {"A": 0.40, "B": 0.06}
    scenario_kwargs = dict(spine_level={"A": 0.42, "B": 0.05},
                           level_shrink=M.DEFAULTS["level_shrink"],
                           level_shrink_scale=M.DEFAULTS["level_shrink_scale"])
    quiet, quiet_notes = M.blended_centres(
        _scenario(**scenario_kwargs), base, {}, {})
    trace = _RecordingTrace()
    traced, traced_notes = M.blended_centres(
        _scenario(**scenario_kwargs), base, {}, {}, trace=trace)
    assert traced == quiet and traced_notes == quiet_notes, (
        "passing a trace changed the result")
    recorded = trace.records["30_centres"]
    assert recorded["before_shrink"].keys() == recorded["after_shrink"].keys() == base.keys()
    assert recorded["after_shrink"] == traced
    assert math.isclose(recorded["ratio"]["A"],
                        traced["A"] / recorded["before_shrink"]["A"],
                        rel_tol=1e-12)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
