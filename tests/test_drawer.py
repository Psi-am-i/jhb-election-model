"""Golden-seed CHARACTERISATION of the citywide prior in ``montecarlo.py``.

``montecarlo.make_drawer`` returns a closure that produces one citywide PR
target vector per call. Everything downstream -- the VD solve, the ward races,
the seat draws, the published probabilities -- is conditioned on that vector,
so a change in its distribution moves every number the site publishes.

**This file records what the code does. It does not claim that what it does is
right.** Some of these assertions pin behaviour that is known to be wrong.

``draw_pools()`` distorts the configured pool bands in TWO separate places,
and they are easy to confuse because they act on the same numbers one after the
other. Re-record with ``--decompose`` to reproduce the current figures.

* **Plan item 3.1, OPEN — renormalisation.** ``draw_pools()`` builds each
  pool's total from its configured ratio triangular, fills in the individual
  parties, and then divides the whole vector by its own sum. Because the pieces
  are drawn independently and generally sum to more than one, that division
  pulls the realised distribution IN — from **both** ends, not one. The
  forecast is therefore more confident than any documented judgement supports,
  and most of that confidence is a low ceiling.

* **The entrant rescale.** Separately, and *after* renormalisation,
  ``target *= (1.0 - share)`` scales every established party down to make room
  for the hypothetical new entrant. Since the entrant draws a positive share on
  25% of draws, this shifts every pool DOWN. Whether it is a defect at all is a
  modelling judgement (an entrant's votes must come from somewhere), but it is a
  different step with a different fix, and attributing it to 3.1 would send
  whoever fixes 3.1 after a defect that is not there.

``test_renormalisation_narrows_the_largest_pool_from_both_sides`` asserts that
the first gap is there. **When 3.1 is fixed that test must fail**, loudly and
deliberately, and it should then be deleted along with the GOLDEN values below.

Re-record after a deliberate change with:
    ./.venv/bin/python tests/test_drawer.py --record

Re-measure the A/B/C table above with:
    ./.venv/bin/python tests/test_drawer.py --decompose

Run:
    ./.venv/bin/python tests/test_drawer.py
    ./.venv/bin/python -m pytest tests/test_drawer.py -q
"""

from __future__ import annotations

import copy
import json
import csv
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import cityconfig  # noqa: E402
import montecarlo as mc  # noqa: E402

CITY = "joburg"
SEED = 20261104          # the shipped seed; the drawer is exercised as configured
DRAWS = 2000             # enough for a stable p5/p95, ~0.2s to produce

# Percentage points. The draw is bit-for-bit reproducible for a given numpy
# version, so this is slack for a float difference, not for a real change in
# the prior: re-emitting the pools, or nudging a party's blended centre, moves
# these values well clear of it. A numpy UPGRADE can legitimately move them too
# (the RNG stream is versioned); that is a re-record, and should be noted as
# one in MODEL-LOG.md.
TOL = 0.01

ELECTIONS = ROOT / "data" / "raw" / "elections"
PROCESSED = ROOT / "data" / "processed"

# Recorded 2026-08-10 from data/processed/pools_2026.json, seed 20261104,
# 2000 draws, numpy 2.5.1. Values are percentages: (mean, p5, p95).
#
# RE-RECORDED 2026-08-13, deliberately, for three changes to the draw:
#   * a per-party level shock connected to the measured sd(log θ), drawn from a
#     Student-t rather than a bounded triangular (montecarlo.log_shock);
#   * one correlated citywide turnout factor across pools, ρ = 0.63 measured
#     (montecarlo.TURNOUT_CORRELATION);
#   * turnout bands built in logit space, so they are two-sided everywhere
#     (pools.turnout_band).
# The prior moved as intended and by little: ANC mean 23.33% -> 23.15%, DA
# 27.69% -> 27.79%, EFF 9.94% -> 10.27%. The pool p5/p95 tightened at the White
# pool (25.18-36.51 -> 25.65-35.75) and loosened at Black African, which is the
# correlated turnout factor doing what it was added to do.
#
# For the record, alongside these: no realised pool band is the configured one,
# and two separate steps are responsible. See the A/B/C table in the module
# docstring — renormalisation for A-to-B (plan item 3.1), the entrant rescale
# for B-to-C.
GOLDEN_PARTIES: dict[str, tuple[float, float, float]] = {
    "ANC": (23.1513, 12.7812, 34.7449),
    "DA": (27.7919, 21.2187, 34.7480),
    "EFF": (10.2745, 3.4773, 19.6961),
    "ASA": (11.6717, 4.7547, 21.1789),
    "MK": (8.1683, 2.0484, 16.8382),
    "PA": (3.5227, 2.3640, 4.7755),
    "VFPLUS": (0.7884, 0.0097, 2.9621),
    "ALJAMAAH": (0.8365, 0.2790, 1.6276),
    "ENTRANT": (1.5042, 0.0000, 7.8337),
}
GOLDEN_POOLS: dict[str, tuple[float, float, float]] = {
    "Black African": (53.5913, 46.2636, 60.0886),
    "Coloured": (8.1105, 6.3735, 10.3526),
    "Indian/Asian": (6.1703, 4.8139, 7.9311),
    "White": (30.6238, 25.6488, 35.7547),
}

WATCHED = ("ANC", "DA", "EFF", "ASA", "MK", "PA", "VFPLUS", "ALJAMAAH", "ENTRANT")


# --------------------------------------------------------------------------
# fixture: rebuild exactly the inputs montecarlo.main hands to make_drawer
# --------------------------------------------------------------------------

def build_inputs():
    """Return (scenario, base_city_d, centres, index) as ``main`` assembles them."""
    city = cityconfig.load(CITY)
    cityconfig.use(CITY)
    mc.apply_city(city)
    scenario = copy.deepcopy(mc.DEFAULTS)

    base_path = ELECTIONS / "npe2024_{CODE}_vd_party.csv"
    if not cityconfig.resolve_path(base_path).exists():
        skip(f"no national baseline for {CITY} at {base_path} — the prior "
             f"cannot be rebuilt without it")
    base_votes, _ = mc.load(base_path, None)
    base_city_d = mc.citywide(base_votes)

    universe = sorted(p for p in base_city_d if p not in (mc.INDEPENDENT, "IND"))
    if scenario["entrant_prob"] > 0:
        universe.append("ENTRANT")
    index = {party: i for i, party in enumerate(universe)}

    lge_path = ELECTIONS / "lge2021_{CODE}_vd_party_clean.csv"
    if not cityconfig.resolve_path(lge_path).exists():
        skip(f"no 2021 result file for {CITY} at {lge_path}")
    pr21, _ = mc.load(lge_path, "PR")
    share_2021 = mc.citywide(pr21)

    bye: dict[str, tuple[float, float]] = {}
    bye_path = PROCESSED / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                bye[row["party"]] = (float(row["weight_sum"]),
                                     float(row["weighted_delta"]))

    # The drawer has no engine without pools, so the fixture must load the
    # measured spec exactly as run_model does — otherwise this file would test
    # a configuration the forecast never runs.
    spec_path = city.processed / "pools_2026.json"
    if not spec_path.exists():
        skip(f"no pool spec at {spec_path} — run: python src/pools.py "
             f"--city {CITY} --target 2026 --emit")
    scenario["pools"] = json.loads(spec_path.read_text())["pools"]

    centres, _ = mc.blended_centres(scenario, base_city_d, share_2021, bye)
    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0
    return scenario, base_city_d, centres, index


_CACHE: dict[int, tuple] = {}


def draw_matrix(draws: int = DRAWS, cache: bool = True):
    """Return (matrix (draws x parties), index, scenario, base_city_d, centres).

    Cached per draw count so the suite reads the input files once rather than
    once per test; ``cache=False`` forces a genuinely fresh build, which is how
    the determinism test earns its keep.
    """
    if cache and draws in _CACHE:
        return _CACHE[draws]
    scenario, base_city_d, centres, index = build_inputs()
    rng = np.random.default_rng(SEED)
    draw = mc.make_drawer(scenario, base_city_d, centres, index, rng)
    matrix = np.array([draw() for _ in range(draws)])
    result = (matrix, index, scenario, base_city_d, centres)
    if cache:
        _CACHE[draws] = result
    return result


def marginals(column: np.ndarray) -> tuple[float, float, float]:
    return (float(column.mean() * 100),
            float(np.percentile(column, 5) * 100),
            float(np.percentile(column, 95) * 100))


def triangular_quantile(low: float, mode: float, high: float, p: float) -> float:
    """Exact quantile of Triangular(low, mode, high) -- no sampling noise."""
    mode = min(max(mode, low), high)
    split = (mode - low) / (high - low)
    if p <= split:
        return low + math.sqrt(p * (high - low) * (mode - low))
    return high - math.sqrt((1 - p) * (high - low) * (high - mode))


def _pools(scenario, base_city_d, centres, index):
    lean = scenario["polling_lean"] * scenario["polling_span"]
    return mc.pool_spec(scenario, base_city_d, centres, index, lean)


def configured_pool_band(name, scenario, base_city_d, centres, index):
    """Stage A: the 5th-95th percentile this pool's own configuration implies.

    A pool moves by a RATIO on its base, not by a shift in points, so the band
    is base x the ratio triangular's quantiles. Taken from ``mc.pool_spec`` so
    the mode is the one the sampler was actually asked for, including the
    one-sided-range reflection it applies.
    """
    spec = _pools(scenario, base_city_d, centres, index)
    _idx, registered, turnout, _props, _alpha, _names, _levels, _wts = spec[name]
    low, mode, high = turnout

    # A pool's SHARE, not its vote count. Registration is counted and turnout
    # is drawn, so the pool's share of the city is
    #     reg_g * t_g / sum_h(reg_h * t_h)
    # and the denominator moves with every pool. The band below holds the other
    # pools at their modal turnout and moves this one, which is the like-for-
    # like comparison against a sampled share. An earlier version multiplied a
    # registration count by a turnout quantile and reported a band of 59
    # million, having been written when the pool's base was a vote share.
    others = sum(spec[nm][1] * spec[nm][2][1] for nm in spec if nm != name)

    def share_at(quantile: float) -> float:
        t = triangular_quantile(low, mode, high, quantile)
        mine = registered * t
        return 100.0 * mine / (mine + others) if mine + others else 0.0

    return share_at(0.05), share_at(0.95), (low, mode, high)


def before_entrant_rescale(matrix: np.ndarray, index: dict) -> np.ndarray:
    """Stage B: the draws as they were before ``target *= (1.0 - share)``.

    The entrant rescale (montecarlo.py:665-669, and :621-625 in the pooled
    engine) is exactly invertible from the output: it scales every established
    party by ``1 - share`` and then parks ``share`` in the entrant's slot, so
    dividing the vector by ``1 - matrix[:, ENTRANT]`` and zeroing that slot
    recovers the post-renormalisation vector to floating-point precision. That
    is what lets this file attribute each distortion to the step that caused
    it without reimplementing ``draw()``.
    """
    entrant = index.get("ENTRANT")
    if entrant is None:
        return matrix.copy()
    share = matrix[:, entrant]
    out = matrix / (1.0 - share)[:, None]
    out[:, entrant] = 0.0
    return out


def pool_total(matrix: np.ndarray, index: dict, scenario, name: str) -> np.ndarray:
    """A pool's share of the vote, per draw.

    A party contributes to a pool in proportion to the share of its vote that
    comes from there, so this is the weighted sum -- not a membership count.
    """
    members = scenario["pools"][name]["members"]
    total = np.zeros(matrix.shape[0])
    for party, weight in members.items():
        if party in index:
            total += float(weight) * matrix[:, index[party]]
    return total


def pool_band(matrix, index, scenario, name: str) -> tuple[float, float]:
    total = pool_total(matrix, index, scenario, name)
    return (float(np.percentile(total, 5) * 100),
            float(np.percentile(total, 95) * 100))


def stages(name: str):
    """(A, B, C) bands for one pool, plus its ratio triangular."""
    matrix, index, scenario, base_city_d, centres = draw_matrix()
    a_p5, a_p95, spec = configured_pool_band(
        name, scenario, base_city_d, centres, index)
    b_p5, b_p95 = pool_band(before_entrant_rescale(matrix, index), index,
                            scenario, name)
    c_p5, c_p95 = pool_band(matrix, index, scenario, name)
    return (a_p5, a_p95), (b_p5, b_p95), (c_p5, c_p95), spec


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

def test_every_draw_is_a_probability_vector():
    matrix, _, _, _, _ = draw_matrix()
    sums = matrix.sum(axis=1)
    assert np.all(matrix >= 0), "a target vector contained a negative share"
    assert np.allclose(sums, 1.0, atol=1e-9), (
        f"target vectors do not sum to 1 (min {sums.min()}, max {sums.max()})")


def test_party_marginals_match_recorded():
    """The realised per-party marginals are what they were when recorded."""
    if not GOLDEN_PARTIES:
        skip("no GOLDEN_PARTIES recorded — run: "
             "./.venv/bin/python tests/test_drawer.py --record")
    matrix, index, _, _, _ = draw_matrix()
    drift = []
    for party, want in sorted(GOLDEN_PARTIES.items()):
        assert party in index, (
            f"{party} has left the party universe; the prior has changed shape, "
            f"not just scale")
        got = marginals(matrix[:, index[party]])
        for label, a, b in zip(("mean", "p5", "p95"), got, want):
            if abs(a - b) > TOL:
                drift.append(f"{party} {label}: recorded {b:.4f}%, now {a:.4f}% "
                             f"({a - b:+.4f}pp)")
    assert not drift, (
        "the citywide prior has moved from its recorded behaviour:\n  "
        + "\n  ".join(drift)
        + "\n\nIf this change was deliberate, re-record with "
          "`./.venv/bin/python tests/test_drawer.py --record` and say so in "
          "MODEL-LOG.md. If it was not, something changed the forecast.")


def test_pool_marginals_match_recorded():
    if not GOLDEN_POOLS:
        skip("no GOLDEN_POOLS recorded — run: "
             "./.venv/bin/python tests/test_drawer.py --record")
    matrix, index, scenario, _, _ = draw_matrix()
    drift = []
    for name, want in sorted(GOLDEN_POOLS.items()):
        assert name in scenario["pools"], (
            f"pool {name} has left the spec; the prior has changed shape, not "
            f"just scale. Re-emit and re-record deliberately.")
        got = marginals(pool_total(matrix, index, scenario, name))
        for label, a, b in zip(("mean", "p5", "p95"), got, want):
            if abs(a - b) > TOL:
                drift.append(f"{name} {label}: recorded {b:.4f}%, now {a:.4f}% "
                             f"({a - b:+.4f}pp)")
    assert not drift, ("pool totals have moved from their recorded behaviour:\n  "
                       + "\n  ".join(drift))


def _largest_pool(scenario, base_city_d, centres, index) -> str:
    spec = _pools(scenario, base_city_d, centres, index)
    return max(spec, key=lambda name: spec[name][1])


def test_the_realised_pool_prior_is_not_the_configured_one():
    """DOCUMENTS A KNOWN DEFECT (plan item 3.1) — delete this when 3.1 is fixed.

    Renormalisation is stage A -> stage B: the configured ratio band against
    the draws as they stand *before* the entrant rescale.

    Under the two-bloc engine this compressed both tails inward. Under N pools
    it does something different, and worse. The pools are drawn independently
    and their sum varies, so dividing by that sum redistributes between them:
    the dominant pool absorbs the variance downward while the small pools widen
    upward. Measured 2026-08-10, seed 20261104, 2000 draws:

      pool            configured p5-p95     realised (stage B)
      Black African   63.63 - 68.69         52.98 - 68.59      p5 -10.65
      Indian/Asian     4.86 -  5.93          5.01 -  8.72      p95 +2.79
      Other            0.83 -  1.75          1.01 -  3.55      p95 +1.80

    Indian/Asian realises nearly three times the width it was configured with.
    Nobody chose that: it is an artefact of normalising after the fact. The
    fix is to draw the composition jointly, or to draw the residual as one
    quantity with an explicit total, so the sum is one by construction.

    This test asserts the gap EXISTS, so that fixing 3.1 fails the suite
    instead of passing it silently. When that happens: delete this test and
    re-record GOLDEN_PARTIES/GOLDEN_POOLS.
    """
    _m, index, scenario, base_city_d, centres = draw_matrix()
    name = _largest_pool(scenario, base_city_d, centres, index)
    (a_p5, a_p95), (b_p5, b_p95), _, spec = stages(name)

    # The PROPERTY, not a magnitude in points. An earlier version demanded the
    # dominant pool's p5 fall by more than five points, which held while the
    # pool ratio was a narrow [0.89, 0.96, 1.01] and stopped holding the moment
    # the ratio widened to [0.70, 0.91, 1.40] — not because renormalisation had
    # been fixed, but because the same distortion is smaller relative to a wider
    # band. A test that fails on a legitimate re-fit trains people to re-record
    # without reading, and then catches nothing.
    width_a, width_b = a_p95 - a_p5, b_p95 - b_p5
    assert abs(width_b - width_a) > 0.05 * width_a, (
        f"renormalisation no longer changes pool {name!r}'s band: configured "
        f"{a_p5:.2f}-{a_p95:.2f}%, realised {b_p5:.2f}-{b_p95:.2f}% "
        f"(ratio triangular {spec}). Either plan item 3.1 (post-hoc "
        f"renormalisation in draw_pools) has been fixed — in which case DELETE "
        f"this test and re-record the golden values — or the arithmetic "
        f"changed. Do not 'fix' this by loosening the threshold.")

    widened = []
    for other in scenario["pools"]:
        if other == name:
            continue
        (o_a5, o_a95), (o_b5, o_b95), _, _ = stages(other)
        if (o_b95 - o_b5) > (o_a95 - o_a5) * 1.2:
            widened.append(other)
    assert widened, (
        "no pool realises a materially wider band than it was configured "
        "with. Under the measurement this file records, the small pools widen "
        "as the dominant one is dragged down — that is the same defect seen "
        "from the other end. If it has gone, 3.1 may be fixed: re-measure "
        "with `--decompose` and rewrite this file's docstring.")


def test_entrant_rescale_pushes_every_pool_down():
    """ATTRIBUTION GUARD — this one must survive the fix for plan item 3.1.

    Renormalisation pulls a band inward. The entrant rescale is a separate,
    later step that scales every established party by ``1 - share`` on the
    draws where the hypothetical entrant takes one, so it moves every pool
    DOWN. Read off the final output alone the two are indistinguishable, and
    fixing 3.1 will not close the part this step causes. This test exists so
    that the next person to read this file is not sent after a defect that is
    not there.
    """
    _m, index, scenario, base_city_d, centres = draw_matrix()
    offenders = []
    for name in scenario["pools"]:
        (_a5, _a95), (b_p5, _b95), (c_p5, _c95), _spec = stages(name)
        if c_p5 - b_p5 >= 0:
            offenders.append(f"{name}: p5 moved {c_p5 - b_p5:+.3f}pp "
                             f"({b_p5:.2f}% -> {c_p5:.2f}%)")
    assert not offenders, (
        "the entrant rescale no longer pushes these pools' lower tails down:\n  "
        + "\n  ".join(offenders)
        + "\n\nIf entrant_prob or entrant_share changed this is expected and "
          "the docstring should be re-measured (`--decompose`); if they did "
          "not, the rescale step has changed behaviour.")


def test_drawer_is_deterministic_for_a_fixed_seed():
    """Same seed, same draws -- twice."""
    first, _, _, _, _ = draw_matrix(50, cache=False)
    second, _, _, _, _ = draw_matrix(50, cache=False)
    assert np.array_equal(first, second), (
        "make_drawer is not reproducible from its seed; every recorded value "
        "in this file, and every published forecast, is unrepeatable")


# --------------------------------------------------------------------------
# recording
# --------------------------------------------------------------------------

def record() -> None:
    matrix, index, scenario, base_city_d, centres = draw_matrix()
    print(f"# recorded from seed {SEED}, {DRAWS} draws, numpy {np.__version__}")
    print("GOLDEN_PARTIES = {")
    for party in WATCHED:
        if party not in index:
            continue
        m, lo, hi = marginals(matrix[:, index[party]])
        print(f'    "{party}": ({m:.4f}, {lo:.4f}, {hi:.4f}),')
    print("}")
    print("GOLDEN_POOLS = {")
    for name in scenario["pools"]:
        m, lo, hi = marginals(pool_total(matrix, index, scenario, name))
        print(f'    "{name}": ({m:.4f}, {lo:.4f}, {hi:.4f}),')
    print("}")
    decompose()


def decompose() -> None:
    """Print the A/B/C table in the module docstring, with the step deltas."""
    print(f"# decomposed from seed {SEED}, {DRAWS} draws, numpy {np.__version__}")
    _m, _i, scenario, _b, _c = draw_matrix()
    for name in scenario["pools"]:
        (a5, a95), (b5, b95), (c5, c95), spec = stages(name)
        print(f"# {name}  (ratio triangular {spec})")
        print(f"#   A as configured             {a5:7.4f} - {a95:7.4f}")
        print(f"#   B after renormalisation     {b5:7.4f} - {b95:7.4f}"
              f"   (p5 {b5 - a5:+.4f}, p95 {b95 - a95:+.4f})")
        print(f"#   C after the entrant rescale {c5:7.4f} - {c95:7.4f}"
              f"   (p5 {c5 - b5:+.4f}, p95 {c95 - b95:+.4f})")


if __name__ == "__main__":
    if "--record" in sys.argv:
        record()
        raise SystemExit(0)
    if "--decompose" in sys.argv:
        decompose()
        raise SystemExit(0)
    raise SystemExit(run_module(globals()))
