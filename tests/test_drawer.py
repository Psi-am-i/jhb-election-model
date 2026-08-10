"""Golden-seed CHARACTERISATION of the citywide prior in ``montecarlo.py``.

``montecarlo.make_drawer`` returns a closure that produces one citywide PR
target vector per call. Everything downstream -- the VD solve, the ward races,
the seat draws, the published probabilities -- is conditioned on that vector,
so a change in its distribution moves every number the site publishes.

**This file records what the code does. It does not claim that what it does is
right.** Some of these assertions pin behaviour that is known to be wrong.

``draw()`` distorts the configured bloc bands in TWO separate places, and they
are easy to confuse because they act on the same numbers one after the other.
Measured on 2026-08-10 with the shipped Johannesburg configuration, seed
20261104, 2000 draws (the ``--decompose`` mode below reproduces every figure):

  stage                         ANC bloc p5-p95     DA bloc p5-p95
  A  as configured              37.66% - 50.65%     39.23% - 45.99%
  B  after renormalisation      38.74% - 46.58%     38.70% - 45.42%
  C  after the entrant rescale  37.67% - 46.45%     37.48% - 45.12%

Stage A is the exact triangular quantile; B and C are 2000-draw sample
quantiles. Sampling the shift triangular instead gives A = 37.69%-50.76% and
39.22%-46.02%, so read a tenth of a point of noise into every A-to-B figure
below. It changes none of the conclusions.

* **Plan item 3.1, OPEN — renormalisation (A to B).** ``draw()`` builds the two
  bloc totals from the configured triangular shift ranges, fills in the
  individual parties, and then divides the whole vector by its own sum
  (``montecarlo.py:620`` in the pooled engine, ``:664`` in the bloc engine).
  Because the pieces are drawn independently and generally sum to more than
  one, that division pulls the realised distribution IN — from **both** ends,
  not one. The ANC bloc's p95 falls 4.07 points while its p5 *rises* 1.08
  points; the DA bloc loses about half a point at each end. The forecast is
  therefore more confident about the ANC bloc than any documented judgement
  supports, and most of that confidence is a low ceiling.

* **The entrant rescale (B to C).** Separately, and *after* renormalisation,
  ``target *= (1.0 - share)`` (``montecarlo.py:665-669``, and ``:621-625`` in
  the pooled engine) scales every established party down to make room for the
  hypothetical new entrant. Since the entrant draws a positive share on 25% of
  draws, this shifts every bloc DOWN — about 1.1 points off each bloc's p5.
  That, not renormalisation, is the whole of the DA bloc's 1.75-point drop
  below its configured p5. Whether it is a defect at all is a modelling
  judgement (an entrant's votes must come from somewhere), but it is a
  different step with a different fix, and attributing it to 3.1 would send
  whoever fixes 3.1 after a defect that is not there.

``test_renormalisation_narrows_the_anc_bloc_from_both_sides`` asserts that the
first gap is there. **When 3.1 is fixed that test must fail**, loudly and
deliberately, and it should then be deleted along with the GOLDEN values below,
which will also move.
``test_da_bloc_lower_tail_gap_is_the_entrant_rescale_not_renormalisation``
asserts the second, and must NOT be affected by fixing 3.1 — if fixing 3.1
moves it, the two steps were not as separable as measured here. That is the
intended failure: this file's job is to make sure the prior cannot change by
accident, only on purpose.

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
# the prior. Measured sensitivity at this threshold: moving the ANC bloc's
# configured upper shift by one point shows up as 0.18pp, dropping the DA
# bloc's Dirichlet concentration from 12 to 8 as 0.18pp, nudging the ANC's
# blended centre by 0.5% as 0.06pp, and the PA's by 1% as 0.015pp. A numpy
# UPGRADE can legitimately move these figures (the RNG stream is versioned);
# that is a re-record, and it should be noted as one.
TOL = 0.01

ELECTIONS = ROOT / "data" / "raw" / "elections"
PROCESSED = ROOT / "data" / "processed"

# Recorded 2026-08-10 from the shipped cities/joburg.toml, seed 20261104,
# 2000 draws, numpy 2.5.1. Values are percentages: (mean, p5, p95).
#
# For the record, alongside these: neither realised bloc band is the configured
# one, and two separate steps are responsible. See the A/B/C table in the module
# docstring — renormalisation for A-to-B (plan item 3.1), the entrant rescale
# for B-to-C.
GOLDEN_PARTIES: dict[str, tuple[float, float, float]] = {
    "ANC": (23.7716, 18.8248, 28.8967),
    "DA": (29.4637, 19.5417, 37.7167),
    "EFF": (10.1638, 6.5377, 14.4417),
    "ASA": (11.2653, 3.7965, 20.6735),
    "MK": (8.2488, 4.8483, 12.2410),
    "PA": (4.5594, 3.3534, 5.6536),
    "VFPLUS": (1.0673, 0.6834, 1.5090),
    "ALJAMAAH": (1.4298, 0.8823, 2.0748),
    "ENTRANT": (1.5090, 0.0000, 8.1594),
}
GOLDEN_BLOCS: dict[str, tuple[float, float, float]] = {
    "ANC_BLOC": (42.1842, 37.6683, 46.4480),
    "DA_BLOC": (41.3759, 37.4787, 45.1182),
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


def configured_bloc_band(bloc: str, scenario, base_city_d, centres, index):
    """Stage A: the 5th-95th percentile the bloc's own configuration implies.

    Base share plus the configured shift triangular, before renormalisation and
    before the entrant rescale. Computed from the exact triangular quantile, so
    it carries no sampling noise of its own -- but it is being compared against
    sampled stages, and at 2000 draws that comparison is good to roughly a
    tenth of a point, which is why the thresholds below are whole points.

    The mode must be derived exactly as ``make_drawer`` derives it
    (montecarlo.py:479-493), including the polling lean, or this is a band the
    sampler was never asked to produce.
    """
    members = [p for p in mc.BLOCS[bloc] if p in index]
    base = sum(base_city_d.get(p, 0.0) for p in members)
    centre_total = sum(centres.get(p, 0.0) for p in members)
    low, _, high = (scenario["anc_bloc_shift"] if bloc == "ANC_BLOC"
                    else scenario["da_bloc_shift"])
    # montecarlo.py:479 -- `polling_lean * polling_span`, with no halving.
    # Inert while polling_lean is 0, but a half-sized lean here would silently
    # measure the wrong band the moment the lever is used.
    lean = scenario["polling_lean"] * scenario["polling_span"]
    evidence_mode = (centre_total - base) * 100.0
    evidence_mode += lean if bloc == "DA_BLOC" else -lean
    mode = min(max(evidence_mode, low), high)
    p5 = base * 100 + triangular_quantile(low, mode, high, 0.05)
    p95 = base * 100 + triangular_quantile(low, mode, high, 0.95)
    return p5, p95, (low, mode, high)


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


def bloc_band(matrix: np.ndarray, index: dict, bloc: str) -> tuple[float, float]:
    """(p5, p95) of a bloc's total share, in percentage points."""
    ids = [index[p] for p in mc.BLOCS[bloc] if p in index]
    total = matrix[:, ids].sum(axis=1)
    return (float(np.percentile(total, 5) * 100),
            float(np.percentile(total, 95) * 100))


def stages(bloc: str):
    """(A, B, C) bands for one bloc, plus the bloc's shift triangular."""
    matrix, index, scenario, base_city_d, centres = draw_matrix()
    a_p5, a_p95, spec = configured_bloc_band(
        bloc, scenario, base_city_d, centres, index)
    b_p5, b_p95 = bloc_band(before_entrant_rescale(matrix, index), index, bloc)
    c_p5, c_p95 = bloc_band(matrix, index, bloc)
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


def test_bloc_marginals_match_recorded():
    if not GOLDEN_BLOCS:
        skip("no GOLDEN_BLOCS recorded — run: "
             "./.venv/bin/python tests/test_drawer.py --record")
    matrix, index, _, _, _ = draw_matrix()
    drift = []
    for bloc, want in sorted(GOLDEN_BLOCS.items()):
        ids = [index[p] for p in mc.BLOCS[bloc] if p in index]
        got = marginals(matrix[:, ids].sum(axis=1))
        for label, a, b in zip(("mean", "p5", "p95"), got, want):
            if abs(a - b) > TOL:
                drift.append(f"{bloc} {label}: recorded {b:.4f}%, now {a:.4f}% "
                             f"({a - b:+.4f}pp)")
    assert not drift, ("bloc totals have moved from their recorded behaviour:\n  "
                       + "\n  ".join(drift))


def test_renormalisation_narrows_the_anc_bloc_from_both_sides():
    """DOCUMENTS A KNOWN DEFECT (plan item 3.1) — delete this when 3.1 is fixed.

    Renormalisation is stage A -> stage B: the configured shift band against
    the draws as they stand *before* the entrant rescale. Isolating it that way
    matters. The naive comparison — configured band against the final output —
    mixes in the entrant rescale, and that mixture reads as a one-sided
    compression of the ANC bloc's upper tail. It is not one-sided. Dividing the
    assembled vector by its own sum pulls BOTH tails in: the p95 falls about
    4.2 points and the p5 RISES about 1.0. The final p5 only looks untouched
    because the entrant rescale then pushes it back down by about the same
    amount, which is a coincidence of this configuration, not a property of the
    defect.

    This test asserts the gap EXISTS, so that fixing 3.1 fails the suite
    instead of passing it silently. When that happens: delete this test and
    re-record GOLDEN_PARTIES/GOLDEN_BLOCS.
    """
    (a_p5, a_p95), (b_p5, b_p95), _, spec = stages("ANC_BLOC")

    assert a_p95 - b_p95 > 2.0, (
        f"renormalisation no longer pulls the ANC bloc's upper tail in: "
        f"configured p95 {a_p95:.2f}%, post-renormalisation p95 {b_p95:.2f}% "
        f"(shift triangular {spec}). Either plan item 3.1 (post-hoc "
        f"renormalisation at montecarlo.py:620/:664) has been fixed — in which "
        f"case DELETE this test and re-record the golden values — or the "
        f"configuration changed. Do not 'fix' this by loosening the threshold.")
    assert b_p5 - a_p5 > 0.5, (
        f"renormalisation no longer lifts the ANC bloc's LOWER tail: "
        f"configured p5 {a_p5:.2f}%, post-renormalisation p5 {b_p5:.2f}%. "
        f"Measured on 2026-08-10 the lift was +1.08pp — the compression is "
        f"two-sided, and this half of it is the half that is easy to miss "
        f"because the entrant rescale hides it in the final output. If this "
        f"half has gone but the upper tail above has not, 3.1 has changed "
        f"shape rather than being fixed, and the module docstring's A/B/C "
        f"table needs re-measuring (`--decompose`).")


def test_da_bloc_lower_tail_gap_is_the_entrant_rescale_not_renormalisation():
    """ATTRIBUTION GUARD — this one must survive the fix for plan item 3.1.

    The DA bloc's realised p5 sits about 1.75 points below the p5 its
    configuration implies. Read off the final output alone that looks like the
    same renormalisation defect as the ANC bloc's, pointing outward instead of
    inward. It is not. Renormalisation costs the DA bloc about half a point at
    the p5 (stage A -> B, inward, like everything else it touches); the
    remaining ~1.2 points are the entrant rescale (stage B -> C), which scales
    every established party by ``1 - share`` on the 25% of draws where the
    hypothetical entrant takes a share.

    So the entrant rescale, not renormalisation, is the larger part of the gap,
    and it moves the band the OTHER way. Fixing 3.1 will not close it. This
    test exists so that the next person to read this file is not sent after a
    defect that does not exist.
    """
    (a_p5, _), (b_p5, _), (c_p5, _), spec = stages("DA_BLOC")
    renorm = b_p5 - a_p5
    rescale = c_p5 - b_p5

    assert renorm < 0, (
        f"renormalisation now moves the DA bloc's p5 UP ({renorm:+.2f}pp: "
        f"configured {a_p5:.2f}% -> post-renormalisation {b_p5:.2f}%, shift "
        f"triangular {spec}). Every measurement to date has renormalisation "
        f"pulling a band inward; if it is pushing this one out, the A/B/C "
        f"table in the module docstring is stale — re-measure with "
        f"`./.venv/bin/python tests/test_drawer.py --decompose`.")
    assert rescale < -0.5, (
        f"the entrant rescale barely moves the DA bloc's p5 any more "
        f"({rescale:+.2f}pp: post-renormalisation {b_p5:.2f}% -> final "
        f"{c_p5:.2f}%). Measured on 2026-08-10 it was -1.22pp, and it — not "
        f"renormalisation — is what puts the realised p5 below the configured "
        f"one. If entrant_prob or entrant_share changed, this is expected and "
        f"the docstring's A/B/C table should be re-measured; if they did not, "
        f"montecarlo.py:665-669 has changed behaviour.")
    assert abs(rescale) > abs(renorm), (
        f"the DA bloc's lower-tail gap is no longer dominated by the entrant "
        f"rescale: renormalisation {renorm:+.2f}pp vs rescale {rescale:+.2f}pp "
        f"(configured p5 {a_p5:.2f}% -> {b_p5:.2f}% -> {c_p5:.2f}%). The "
        f"attribution this file documents has changed; re-measure with "
        f"`--decompose` and rewrite the module docstring before touching "
        f"either step.")


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
    print("GOLDEN_BLOCS = {")
    for bloc in mc.BLOCS:
        ids = [index[p] for p in mc.BLOCS[bloc] if p in index]
        m, lo, hi = marginals(matrix[:, ids].sum(axis=1))
        print(f'    "{bloc}": ({m:.4f}, {lo:.4f}, {hi:.4f}),')
    print("}")
    decompose()


def decompose() -> None:
    """Print the A/B/C table in the module docstring, with the step deltas."""
    print(f"# decomposed from seed {SEED}, {DRAWS} draws, numpy {np.__version__}")
    for bloc in mc.BLOCS:
        (a5, a95), (b5, b95), (c5, c95), spec = stages(bloc)
        print(f"# {bloc}  (shift triangular {spec})")
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
