"""THE SEAM: ``levels.theta_prior`` — the θ band, and the block it reports.

``theta_prior(target, baseline) -> (priors, groups)`` is the retention layer:
per party a ``(low, mode, high)`` on θ, the ratio of a local share to the
national share before it, plus a diagnostic block. It has existed for the whole
life of this model with **no test on what it returns**. Two files call it —
``tests/test_drawer.py:418`` and ``tests/test_ipf_feasibility.py:133`` — and
both use it only as a FIXTURE, to build a scenario for something else.

That is not a hypothetical gap. ``tests/test_drawer.py:410`` records it
happening::

    the goldens did not move when §1.49 changed `theta_prior`:
    they were not reaching it

§1.49 changed **what the estimator shrinks toward** — from a single flat
common centre to a centre that varies with party size — and the entire suite
was silent. Whichever of the two was right, nothing in the repository could
tell. This file makes that change, and its opposite, visible.

WHAT IS PINNED, AND ON WHAT AUTHORITY

Nothing here asserts a number because ``levels.py`` returns it. Every expected
value is either

* **arithmetic on a constructed record**, whose ratios lie exactly on a line
  ``log θ = a + b·log(size)`` chosen by this file, so the size centre is known
  in closed form before any code runs and the shrunk mean is
  ``centre + w·d`` with ``w = worth / (worth + SHRINK)`` — the rule stated in
  the function's own docstring and in ``JUDGEMENT-CALLS.md``, not read off the
  implementation; or
* **an invariant** that must hold whatever the fit says: the band is symmetric
  in log space about the mode, every party in the baseline gets exactly one
  prior and one width, widths are positive and finite and inside
  ``[SD_FLOOR, SD_CEILING]``, and the same record gives the same answer twice.

THE CONSTRUCTED RECORD IS BALANCED ON PURPOSE. Every observation placed off
the line at ``+d`` is mirrored by one at the same size at ``−d``, so the
residuals and the size-weighted residuals both sum to zero and the ordinary
least squares line through the record is *provably unchanged* by the parties
under test. Without that, adding the party being measured would move the centre
it is being measured against.

THREE FINDINGS ARE DOCUMENTED HERE, NOT FIXED (phase A is tests only):

1. ``montecarlo.py:2319`` reads ``_groups.get("small", {})`` and
   ``theta_prior`` has no ``"small"`` key, so ``__small__`` is built from the
   typed defaults 0.8/0.8 on every run — and nothing reads ``__small__``.
2. a record holding exactly ONE observation makes ``np.std(..., ddof=1)``
   return ``nan``, and every band and every width comes back ``nan`` with no
   error.
3. parties in the record but absent from the baseline DO receive a prior,
   priced at size ``0.0``, which the function's own comment says is impossible.

Run:
    ./.venv/bin/python tests/test_theta_prior.py
    ./.venv/bin/python -m pytest tests/test_theta_prior.py -q
"""

from __future__ import annotations

import math
import sys
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import levels  # noqa: E402


# --------------------------------------------------------------------------
# The constructed record.
#
# `A` and `B` are this file's choice, not the model's: every filler observation
# is placed exactly on `log θ = A + B·log(size)`, so ordinary least squares
# through the record recovers (A, B) to float precision and the centre a party
# is shrunk toward is known before any code runs.
# --------------------------------------------------------------------------
A, B = math.log(0.90), -0.10          # centre 0.90 at size 1, falling with size
D = 0.25                              # how far the parties under test sit off it
S0 = 0.10                             # the size they all sit at
FILLER_SIZES = (0.0005, 0.001, 0.003, 0.008, 0.02, 0.05, 0.12, 0.30)


def _line(size: float) -> float:
    """The centre this file put in the record. ``exp(A + B·log size)``."""
    return math.exp(A + B * math.log(size))


def _rel(share: float) -> float:
    """What one observation is worth: ``share / (share + RELIABILITY_HALF)``.

    Restated from the documented rule rather than imported from
    ``levels._reliability``, so a change to the private helper cannot quietly
    change what this file expects.
    """
    return share / (share + levels.RELIABILITY_HALF)


def _weight(worth: float) -> float:
    """The shrinkage weight on a party's OWN mean: ``worth / (worth + SHRINK)``.

    The rule in :func:`levels.theta_prior`'s docstring. ``SHRINK`` is read from
    the module because it is a declared constant, not a result.
    """
    return worth / (worth + levels.SHRINK)


def _filler() -> dict[str, list[tuple[float, float]]]:
    """Twenty-four observations sitting exactly on the line, over eight parties.

    Twenty is ``size_centre``'s minimum; three observations each keeps every
    filler party's own mean on the line too, so none of them distorts the fit.
    """
    record: dict[str, list[tuple[float, float]]] = {}
    for i, size in enumerate(FILLER_SIZES):
        party = f"FILLER_{i:02d}"
        record[party] = [(_line(size * m), size * m) for m in (0.9, 1.0, 1.1)]
    return record


def _ladder(counts=(1, 2, 3, 4, 6)) -> dict[str, list[tuple[float, float]]]:
    """Parties with 1..6 identical observations at ``S0``, each ``+D`` off the line.

    Each is mirrored at ``−D`` so the record's residuals cancel exactly, at the
    same x, and the least-squares line is unmoved. Same share on every row, so
    the ONLY thing that differs between them is how much record they have.
    """
    record: dict[str, list[tuple[float, float]]] = {}
    for n in counts:
        record[f"LADDER_{n}"] = [(_line(S0) * math.exp(D), S0)] * n
        record[f"MIRROR_{n}"] = [(_line(S0) * math.exp(-D), S0)] * n
    return record


def _baseline(record: dict[str, list[tuple[float, float]]],
              extra: dict[str, float] | None = None) -> dict[str, float]:
    """A baseline covering every party in the record, plus any extras.

    Every recorded party needs a baseline size or it drops out of the
    dispersion fit — see ``test_a_party_missing_from_the_baseline_is_dropped``.
    """
    base = {party: obs[0][1] for party, obs in record.items()}
    base.update(extra or {})
    return base


@contextmanager
def synthetic_record(record: dict[str, list[tuple[float, float]]]):
    """Feed ``theta_prior`` a record this file wrote, and prove it was used.

    Yields a list that gains one entry per call to ``levels.theta_record``. A
    test that patches a function the code under test does not actually call
    passes against the real archive while believing it tested a hand-built
    input, so every test here asserts the call happened.
    """
    calls: list[tuple] = []
    real = levels.theta_record

    def fake(target, codes=levels.METRO_CODES):
        calls.append((target, codes))
        return {party: list(obs) for party, obs in record.items()}

    levels.theta_record = fake
    try:
        yield calls
    finally:
        levels.theta_record = real


TARGET_UNUSED = "theta_prior passes the target only to theta_record"


def _real_target(year: str = "2021"):
    """A real ``Target`` WITHOUT mutating the module's active target.

    ``cityconfig.use_target`` is global state; constructing the dataclass reads
    the same calendar and leaves every other test file's target alone.
    """
    return cityconfig.Target(city=cityconfig.active(), year=year)


def _real_baseline(year: str = "2021", code: str = "JHB") -> dict[str, float]:
    """The preceding national election's citywide shares, off disk."""
    npe = cityconfig.preceding(year, "NPE")
    template = cityconfig.CALENDAR[npe].results if npe else None
    if not template:
        skip(f"no national election before {year} in the calendar")
    base = levels._citywide(
        "data/raw/elections/" + template.replace("{CODE}", code))
    if not base:
        skip(f"{template.replace('{CODE}', code)} is not in data/raw/elections")
    return base


# --------------------------------------------------------------------------
# What it shrinks TOWARD
# --------------------------------------------------------------------------

def test_a_party_with_no_record_of_its_own_sits_exactly_on_the_size_centre():
    """The party the shrinkage cannot help lands on ``centre(size)`` and nothing else.

    If this fails, a party facing its first local election with a national vote
    to convert — MK at 2026 is the live one — is being handed some other
    number: the flat common mean, a typed constant, or its own absent record.
    The expected value is arithmetic on a record this file built, where every
    ratio lies on ``exp(A + B·log size)``: a least-squares line through points
    that are already collinear is that line, so the centre at size 0.05 is
    ``exp(A + B·log 0.05)`` whatever the implementation does to get there.
    """
    record = _filler()
    baseline = _baseline(record, {"NOHIST": 0.05})
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1, "theta_prior no longer reads levels.theta_record"

    assert "NOHIST" in priors, (
        "a party with a national baseline and no retention record got no θ "
        "prior at all; `montecarlo.blended_centres` would fall through to the "
        "AssertionError at montecarlo.py:1096")
    assert abs(priors["NOHIST"][1] - _line(0.05)) < 1e-9, (
        f"a party with no record of its own came back at "
        f"{priors['NOHIST'][1]:.9f}; the record it was given puts the centre "
        f"for a party of its size at {_line(0.05):.9f}")


def test_the_shrink_target_is_the_size_centre_and_not_the_flat_common_mean():
    """§1.49's change, which the whole suite failed to notice when it landed.

    Until 2026-08-18 ``theta_prior`` shrank toward ``mu_all``, one number for
    the entire ballot, while ``levels._shrunk`` — the estimator ``spine`` uses
    for the SAME quantity — shrank toward the size centre. They disagreed by
    construction (ANC 0.869 against 0.862, PA 1.115 against 1.197) and the
    register carried it at 🔴 as "at least one is wrong". The flat centre was
    the wrong one: it hands every party the same retention when the record says
    small parties GAIN going into a local election and large ones lose
    (``size_centre``: median θ 1.31 below 0.2%, 0.94 above 10%, n=235).

    The two answers are far apart in the constructed record by construction —
    a small party's centre is well above the flat mean — so a silent revert to
    ``mu_all`` fails here rather than passing unnoticed for weeks.
    """
    record = _filler()
    baseline = _baseline(record, {"TINY": 0.0005, "BIG": 0.30})
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    flat = groups["centre"]["weighted_geomean"]     # exp(mu_all), the flat common centre
    assert abs(priors["TINY"][1] - _line(0.0005)) < 1e-9, (
        f"the smallest party came back at {priors['TINY'][1]:.6f}, not at the "
        f"size centre {_line(0.0005):.6f}. If it came back at {flat:.6f} the "
        f"shrink target has reverted to the flat mean — §1.49 undone.")
    assert abs(priors["BIG"][1] - _line(0.30)) < 1e-9, (
        f"the largest party came back at {priors['BIG'][1]:.6f}, not at the "
        f"size centre {_line(0.30):.6f}")
    assert priors["TINY"][1] > priors["BIG"][1] * 1.05, (
        f"a party at 0.05% of the vote is centred at {priors['TINY'][1]:.4f} "
        f"and one at 30% at {priors['BIG'][1]:.4f}. The gradient the record "
        f"contains has been flattened away, which is precisely what erases "
        f"the mid-ballot parties this model under-forecasts.")


# --------------------------------------------------------------------------
# The shrinkage itself
# --------------------------------------------------------------------------

def test_a_party_with_a_thinner_record_is_shrunk_further_toward_the_centre():
    """More record, less shrinkage — monotonically, with nothing overshooting.

    Every party in the ladder makes the SAME claim (its ratios are all
    ``exp(D)`` above the centre for its size) off the SAME share, so the only
    thing that differs is how many observations it has. The documented rule is
    ``mu = w·own + (1−w)·centre`` with ``w = worth/(worth + SHRINK)``, so the
    distance from the centre must be ``w·D``: strictly increasing in the number
    of observations, always positive, and never past ``D`` itself.

    If this fails, either a thin record is being trusted like a thick one — the
    failure the 0.2% cut was reaching for, where a party going from 30 votes to
    90 becomes evidence that parties triple — or the shrinkage has stopped
    being monotone in the evidence, which would make the spine's blend
    (``k/(worth+k)``, keyed on the same ``worth``) incoherent with it.
    """
    counts = (1, 2, 3, 4, 6)
    record = _filler() | _ladder(counts)
    baseline = _baseline(record)
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    centre = _line(S0)
    gaps = []
    for n in counts:
        expected_w = _weight(n * _rel(S0))
        got = math.log(priors[f"LADDER_{n}"][1] / centre)
        assert abs(got - expected_w * D) < 1e-9, (
            f"a party with {n} observation(s) worth {n * _rel(S0):.4f} sits "
            f"{got:.6f} above the centre in log units; the documented rule "
            f"worth/(worth+SHRINK={levels.SHRINK}) puts it at "
            f"{expected_w * D:.6f}")
        gaps.append(got)
        assert abs(math.log(priors[f"MIRROR_{n}"][1] / centre) + got) < 1e-9, (
            "the same evidence pointing the other way is not shrunk by the "
            "same amount; the estimator is not symmetric about the centre")

    assert all(b > a for a, b in zip(gaps, gaps[1:])), (
        f"distance from the centre by record length: {gaps}. It must increase "
        f"strictly — a party with six observations of its own must be trusted "
        f"more than one with a single observation.")
    assert 0 < gaps[0] and gaps[-1] < D, (
        f"the shrunk mean left the interval between the centre and the "
        f"party's own mean (0, {D}): {gaps[0]:.6f} .. {gaps[-1]:.6f}")


def test_shrinkage_is_keyed_on_what_the_record_is_worth_not_on_how_many_rows():
    """Three ratios measured off 0.02% of the vote are three WEAK statements.

    Two parties, three observations each, identical claims — one measured off
    10% of the national vote, one off 0.02%. The second must end up on the
    group centre and the first must not. This is the whole reason the 0.2% hard
    cut was replaced by a continuous reliability weight (``theta_record``): the
    cut was right about the NUMBER and wrong about the PARTY, and dropping the
    party did not stop the model forming a view of it — it meant the view came
    from a constant somebody typed.

    If this fails the weighting has gone back to counting rows, and a party
    that went from 30 votes to 90 is once again evidence.
    """
    tiny = 0.0002
    record = _filler()
    record["SOLID"] = [(_line(S0) * math.exp(D), S0)] * 3
    record["SOLID_MIRROR"] = [(_line(S0) * math.exp(-D), S0)] * 3
    record["FLIMSY"] = [(_line(tiny) * math.exp(D), tiny)] * 3
    record["FLIMSY_MIRROR"] = [(_line(tiny) * math.exp(-D), tiny)] * 3
    baseline = _baseline(record)
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    solid = math.log(priors["SOLID"][1] / _line(S0))
    flimsy = math.log(priors["FLIMSY"][1] / _line(tiny))
    assert abs(solid - _weight(3 * _rel(S0)) * D) < 1e-9
    assert abs(flimsy - _weight(3 * _rel(tiny)) * D) < 1e-9
    assert flimsy * 4 < solid, (
        f"a party with three ratios off {tiny:.2%} of the vote kept "
        f"{flimsy / D:.1%} of its own claim and one with three ratios off "
        f"{S0:.0%} kept {solid / D:.1%}. Row counting is back.")
    assert groups["worth"]["FLIMSY"] < groups["worth"]["SOLID"], (
        "the reported `worth` no longer orders these two the way the "
        "shrinkage does, so `spine`'s blend and the shrinkage are keyed on "
        "different numbers — the thing reporting `worth` rather than "
        "recomputing it exists to prevent")


def test_a_party_with_no_history_does_not_receive_the_prior_of_one_with_history():
    """Same size, same everything else — one has a record, one has none. They differ.

    The defect this catches is the one that makes the whole layer pointless: a
    party's own retention record being collected, weighted, shrunk and then
    discarded, so that every party of a given size receives the same band. That
    would be invisible from outside — the numbers would still look plausible —
    and it is exactly what §1.49's silence showed the suite could not detect.

    NOTE WHAT DOES **NOT** DIFFER, and is asserted so a change to it is
    deliberate: the WIDTH. ``sd`` is a function of the party's size at the
    target alone, so a party with no record at all is given the same width as
    one with six observations. That is the documented design — the width is the
    group's spread, not the party's, because a party's own two or three
    observations sit almost on top of its own mean (see the SD_FLOOR block) —
    but it does mean nothing in the band expresses how thin the evidence is.
    """
    record = _filler() | _ladder((3,))
    baseline = _baseline(record, {"NEWCOMER": S0})
    baseline["LADDER_3"] = S0
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    newcomer, veteran = priors["NEWCOMER"], priors["LADDER_3"]
    assert abs(newcomer[1] - _line(S0)) < 1e-9
    assert abs(math.log(veteran[1] / newcomer[1])
               - _weight(3 * _rel(S0)) * D) < 1e-9, (
        f"the party with a record came back at {veteran[1]:.6f} and the party "
        f"with none at {newcomer[1]:.6f}. If these are equal the record is "
        f"being collected and thrown away.")
    assert abs(veteran[1] - newcomer[1]) > 1e-6 * newcomer[1]

    assert abs(groups["sd"]["NEWCOMER"] - groups["sd"]["LADDER_3"]) < 1e-12, (
        "the width now depends on the party's own record as well as its size. "
        "That may be an improvement, but it is a MODEL CHANGE: it must be "
        "backtested against real results and written up, not arrive as a "
        "side effect.")


def test_the_shrink_target_is_taken_at_the_size_the_record_was_measured_at():
    """A party whose national vote has MOVED is shrunk toward the centre for the size it was.

    ``theta_prior``'s own comment: *"The size the shrink target is taken at is
    the party's own observed size, weighted the same way ``_shrunk`` weights
    it, so the two estimators agree party-for-party rather than merely in
    form."* Two sizes are in scope at that line and they are the same type —
    ``size`` (the party's size in the baseline, i.e. at the target) and
    ``obs_size`` (the reliability-weighted size its ratios were measured off).
    They coincide for a party whose vote has not moved, so the swap is
    invisible on any record where the two are equal.

    Here they are made to differ by a factor of twenty: the record is measured
    off 10% of the vote, the baseline carries 0.5%. The documented rule fixes
    the answer in closed form — every ratio lies on ``exp(A + B·log size)`` and
    the party sits ``D`` above the centre for its OBSERVED size, so the mode is
    ``exp(A + B·log S0 + w·D)`` — and the test asserts first that the two
    candidate answers are far enough apart to tell apart.

    If this fails, the shrink target is being evaluated at the wrong size. That
    is not cosmetic: it breaks the party-for-party agreement with ``_shrunk``
    that §1.49 was made to establish, and the register carried that
    disagreement at 🔴 as "at least one is wrong" for as long as it existed.
    """
    record = _filler()
    record["DIVERGED"] = [(_line(S0) * math.exp(D), S0)] * 2
    record["DIVERGED_MIRROR"] = [(_line(S0) * math.exp(-D), S0)] * 2
    baseline = _baseline(record)
    baseline["DIVERGED"] = S0 / 20.0       # the vote moved between the two
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    w = _weight(2 * _rel(S0))
    at_observed = _line(S0) * math.exp(w * D)
    at_baseline = math.exp(w * (A + B * math.log(S0) + D)
                           + (1 - w) * (A + B * math.log(baseline["DIVERGED"])))
    assert abs(math.log(at_observed / at_baseline)) > 1e-3, (
        "this test cannot discriminate: the two candidate shrink targets have "
        "become numerically indistinguishable on the constructed record")

    assert abs(priors["DIVERGED"][1] - at_observed) < 1e-9, (
        f"the party came back at {priors['DIVERGED'][1]:.9f}. Shrunk toward "
        f"the centre for the size it was MEASURED at it is {at_observed:.9f}; "
        f"toward the centre for its size in the baseline it is "
        f"{at_baseline:.9f}.")


def test_theta_and_the_spine_estimator_agree_party_for_party_on_the_same_record():
    """ONE ESTIMATOR, NOT TWO — the §1.49 invariant, asserted rather than assumed.

    ``levels._shrunk`` is the estimator ``spine`` uses for a party's shrunk
    log-mean, and its docstring says it was *"extracted so ρ gets exactly the
    same treatment"*: *"If the two routes were shrunk differently, the
    comparison between them in ``spine`` would be measuring the estimators
    rather than the evidence."* Before 2026-08-18 they did differ — one shrank
    toward the flat ``mu_all``, the other toward the size centre — and they
    disagreed by construction (ANC 0.869 against 0.862, PA 1.115 against
    1.197). Nothing in the suite could see it.

    So the mode ``theta_prior`` returns for a party WITH a record must be
    ``exp`` of what ``_shrunk`` returns for that party on the same record,
    exactly. Asserted on a constructed record where the baseline and the
    observed sizes deliberately disagree, and again on the real 2021 archive,
    where every party's two sizes differ for real. The reported ``worth`` must
    match too, since ``spine``'s blend weight and this shrinkage are required
    to be keyed on the same number.

    This says nothing about whether the shared rule is RIGHT — the arithmetic
    tests above do that. It says the two consumers cannot drift apart again.
    """
    record = _filler()
    record["DIVERGED"] = [(_line(S0) * math.exp(D), S0)] * 2
    record["DIVERGED_MIRROR"] = [(_line(S0) * math.exp(-D), S0)] * 2
    baseline = _baseline(record)
    baseline["DIVERGED"] = S0 / 20.0
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1
    mus, _mu_all, worth = levels._shrunk(record)

    for party in record:
        assert abs(math.log(priors[party][1]) - mus[party]) < 1e-12, (
            f"{party}: theta_prior centres it at "
            f"{math.log(priors[party][1]):.12f} in log space and the "
            f"estimator `spine` uses at {mus[party]:.12f}. The two have come "
            f"apart again — §1.49.")
        assert abs(groups["worth"][party] - worth[party]) < 1e-12, (
            f"{party}: the reported worth and `_shrunk`'s disagree")

    # The same, on the archive, where the two sizes differ for every party.
    baseline_2021 = _real_baseline("2021")
    real_priors, real_groups = levels.theta_prior(_real_target("2021"),
                                                  baseline_2021)
    real_record = levels.theta_record(_real_target("2021"))
    assert real_record, "the archive gave no retention record at 2021"
    real_mus, _mu, real_worth = levels._shrunk(real_record)
    for party in real_record:
        assert abs(math.log(real_priors[party][1]) - real_mus[party]) < 1e-9, (
            f"{party} at 2021: theta_prior "
            f"{math.exp(math.log(real_priors[party][1])):.6f} against "
            f"`_shrunk` {math.exp(real_mus[party]):.6f}")
        assert abs(real_groups["worth"][party] - real_worth[party]) < 1e-12


# --------------------------------------------------------------------------
# The width.
#
# A SECOND constructed record, built so the dispersion fit is known in closed
# form. `theta_prior` fits `log((log r − mu_all)²) = c + d·log(size)` and
# reports `sd(size) = exp(½(c + d·log size))`. Here every party sits at one
# size with two mirrored ratios `exp(±e)`, so
#   * the reliability weights on the pair are equal and `mu_all` is exactly 0,
#   * both rows give the same squared deviation `e²`, and
#   * choosing `e = exp(½(DISP_C + DISP_SLOPE·log size))` puts every point of
#     the fit exactly on the line, so least squares recovers it to float
#     precision and `sd` at any size is known before the code runs.
# The constants below are this file's choice; they are set so the resulting
# widths sit strictly inside [SD_FLOOR, SD_CEILING] and the clip cannot mask a
# change.
# --------------------------------------------------------------------------
DISP_C, DISP_SLOPE = -3.0862, -0.3435
DISP_SIZES = (0.0005, 0.0009, 0.0015, 0.003, 0.006,
              0.012, 0.025, 0.06, 0.14, 0.30)


def _sd_line(size: float) -> float:
    """The width this file put in the record: ``exp(½(c + d·log size))``."""
    return math.exp(0.5 * (DISP_C + DISP_SLOPE * math.log(size)))


def _dispersion_record() -> dict[str, list[tuple[float, float]]]:
    """Ten parties, two mirrored ratios each, all exactly on the width line."""
    record: dict[str, list[tuple[float, float]]] = {}
    for i, size in enumerate(DISP_SIZES):
        e = _sd_line(size)
        record[f"P{i:02d}"] = [(math.exp(e), size), (math.exp(-e), size)]
    return record


def test_the_width_is_the_dispersion_line_evaluated_and_not_a_typed_default():
    """The four reported widths are the fit evaluated, to float precision.

    Everything else in this file pins the width only by INVARIANT — positive,
    finite, inside the clip, falling with size. All four of those survive the
    width being replaced by a constant near 0.4, or by the fit read off the
    wrong axis, so on its own that is not enough: the width is what reaches the
    draw as ``sd_measured`` (montecarlo.py:1546) and it decides how wide every
    party's band is.

    Here the record is built so the answer is arithmetic done before the code
    runs: ``mu_all`` is exactly 0 by mirroring, both rows of a party give the
    same squared deviation, and the squared deviations lie exactly on
    ``exp(DISP_C + DISP_SLOPE·log size)``. Least squares through collinear
    points is that line, so ``sd(size)`` must be ``exp(½(c + d·log size))``
    whatever the implementation does to get there — including at the four sizes
    the block reports, which are not sizes any party in the record has.

    If this fails, the fit is no longer the documented one: the ½ is gone, the
    deviations are being taken about each party's own mean instead of the
    common centre (two earlier attempts did exactly that and came out too
    narrow — see the comment above the fit), or a typed default has appeared.
    """
    record = _dispersion_record()
    baseline = _baseline(record)
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    assert abs(math.log(groups["centre"]["weighted_geomean"])) < 1e-12, (
        "the mirrored record no longer has a common centre of exactly 1, so "
        "the closed form below does not apply and this test is not measuring "
        "what it claims")

    for key, size in (("at_0.1%", 0.001), ("at_1%", 0.01),
                      ("at_10%", 0.10), ("at_40%", 0.40)):
        want = _sd_line(size)
        assert levels.SD_FLOOR < want < levels.SD_CEILING, (
            f"{key}: the constructed width {want:.4f} has drifted onto the "
            f"clip, so this test can no longer see a change")
        assert abs(groups["spread"][key] - want) < 1e-9, (
            f"{key}: reported {groups['spread'][key]:.9f}, and the record "
            f"this file built puts the fitted width there at {want:.9f}")

    for party, obs in record.items():
        want = _sd_line(obs[0][1])
        assert abs(groups["sd"][party] - want) < 1e-9, (
            f"{party}: per-party width {groups['sd'][party]:.9f} against "
            f"{want:.9f} from the line the record contains")
        low, mode, high = priors[party]
        assert abs(math.log(high / mode) - 1.2816 * want) < 1e-8, (
            f"{party}: the band's half-width in log space is "
            f"{math.log(high / mode):.6f}, not 1.2816 × sd = "
            f"{1.2816 * want:.6f}. The band has stopped being the 10th to "
            f"90th percentile of the lognormal the docstring describes.")


def test_every_observation_counts_toward_the_dispersion_fit_not_just_the_first():
    """Repeating an outlier five times must widen the fit. Once does not equal five.

    The fit is over OBSERVATIONS, not over parties: ``for r, _share in
    ratios`` appends one point per row. A defect that took one row per party —
    a stray ``[0]``, a ``break``, or a dict keyed by party — would leave every
    invariant in this file intact, because the widths would still be positive,
    finite, inside the clip and falling with size. It would silently discard
    most of the record: at Johannesburg 2021 the archive carries several rows
    for most parties.

    Two records differing ONLY in how many times one large-party outlier
    appears. The outlier sits far above the line at 30% of the vote, and it is
    mirrored so the common centre and the size-centre fit are untouched, so the
    only thing that can move is the dispersion. Five copies must give a
    strictly wider fitted width at 40% than one copy.
    """
    def spread_with(copies: int):
        record = _dispersion_record()
        record["NOISY"] = [(math.exp(1.0), 0.30)] * copies
        record["NOISY_MIRROR"] = [(math.exp(-1.0), 0.30)] * copies
        with synthetic_record(record) as calls:
            _priors, groups = levels.theta_prior(
                TARGET_UNUSED, _baseline(record))
        assert len(calls) == 1
        return groups["spread"]

    once, five_times = spread_with(1), spread_with(5)
    for label, block in (("one copy", once), ("five copies", five_times)):
        assert levels.SD_FLOOR < block["at_40%"] < levels.SD_CEILING, (
            f"{label}: the fitted width at 40% is {block['at_40%']:.4f}, on "
            f"the clip, so this test cannot see the difference it is for")
    assert five_times["at_40%"] > once["at_40%"] * 1.05, (
        f"the same outlier repeated five times gives a fitted width at 40% of "
        f"{five_times['at_40%']:.6f} against {once['at_40%']:.6f} for one "
        f"copy. Replicated evidence is not reaching the dispersion fit — rows "
        f"after the first are being dropped.")


# --------------------------------------------------------------------------
# The band, and the block
# --------------------------------------------------------------------------

def test_every_band_is_ordered_and_symmetric_in_log_space_about_its_mode():
    """``low·high == mode²``, and ``low < mode < high``, for every party.

    The docstring says the band is the 10th to 90th percentile of a lognormal,
    which forces the mode to be the geometric mean of the endpoints. Consumers
    lean on it: ``montecarlo``'s by-election clamp reads the band as
    ``low/mid`` and ``high/mid``, and §1.49 is only safe to have made as an
    unscored correctness fix BECAUSE a shift in the centre cancels out of those
    two ratios. If the band ever stops being log-symmetric, that argument is
    void and §1.49 has to be re-measured.

    Checked on the real 2021 archive, not on a constructed record, so it covers
    every party the model actually prices — including the ones whose width is
    pinned to ``SD_FLOOR`` or ``SD_CEILING`` by the clip.
    """
    baseline = _real_baseline("2021")
    priors, groups = levels.theta_prior(_real_target("2021"), baseline)
    assert priors, "no θ prior at all at 2021 — the archive is not being read"
    for party, (low, mode, high) in priors.items():
        assert 0 < low < mode < high < math.inf, (
            f"{party}: band ({low!r}, {mode!r}, {high!r}) is not a strictly "
            f"ordered positive triple")
        assert abs(math.log(low * high) - 2 * math.log(mode)) < 1e-9, (
            f"{party}: the band is no longer symmetric about the mode in log "
            f"space, so `low/mid` and `high/mid` are no longer a pure function "
            f"of the width and §1.49's cancellation argument is dead")


def test_every_party_priced_has_a_positive_finite_width_inside_the_clip():
    """A ``nan`` or a zero width reaches the draw as a level with no spread.

    ``montecarlo.make_drawer`` reads this block as ``sd_measured.get(party,
    sd_default)`` (montecarlo.py:1546) — a **present** key wins over the
    default, so a ``nan`` here is not caught by the fallback and propagates
    into the draw. ``SD_FLOOR``/``SD_CEILING`` bound it by construction; that
    they still do is what makes ``JUDGEMENT-CALLS``' 🟢 on ``SD_FLOOR`` a claim
    about something live.
    """
    baseline = _real_baseline("2021")
    priors, groups = levels.theta_prior(_real_target("2021"), baseline)
    sd = groups["sd"]
    assert set(sd) == set(priors), (
        f"{len(set(priors) - set(sd))} priced parties have no width and "
        f"{len(set(sd) - set(priors))} widths belong to no priced party; "
        f"§1.59's dispersion column and its residual column would then be "
        f"over different populations")
    for party, width in sd.items():
        assert math.isfinite(width), f"{party}: sd(log θ) is {width!r}"
        assert levels.SD_FLOOR <= width <= levels.SD_CEILING, (
            f"{party}: sd(log θ) = {width:.6f} is outside the declared clip "
            f"[{levels.SD_FLOOR}, {levels.SD_CEILING}]")


def test_the_reported_spread_falls_as_the_party_gets_bigger():
    """Size predicts how UNCERTAIN a party is — the claim SD_FLOOR sits on.

    ``levels.py``'s constants block states the binned record: sd(log θ) of
    0.72, 0.46, 0.25, 0.26 from the smallest band to the largest, correlation
    between log size and |log θ| of −0.37. The four figures the function
    reports at 0.1%, 1%, 10% and 40% are that line evaluated, and they must
    not increase with size. If they do, the fitted slope has flipped sign and
    every write-up that says "0.26 at 40% of the vote rising to 0.72 at 0.1%"
    — the constants block, §1.59, JUDGEMENT-CALLS, and ``run_model``'s own
    verbose line — is stale.
    """
    baseline = _real_baseline("2021")
    _priors, groups = levels.theta_prior(_real_target("2021"), baseline)
    spread = groups["spread"]
    ladder = [spread["at_0.1%"], spread["at_1%"],
              spread["at_10%"], spread["at_40%"]]
    assert all(math.isfinite(x) and x > 0 for x in ladder), ladder
    assert all(a >= b for a, b in zip(ladder, ladder[1:])), (
        f"reported sd(log θ) at 0.1%, 1%, 10%, 40% is {ladder}, which does "
        f"not fall with size. The dispersion fit has changed sign.")
    assert ladder[0] > ladder[-1], (
        f"sd(log θ) is now flat across the whole ballot ({ladder}). The "
        f"size-dispersion fit is doing nothing and every party is being handed "
        f"one width.")


def test_the_groups_block_is_a_diagnostic_and_is_not_a_partition_of_parties():
    """There is exactly ONE group, and ``groups`` does not enumerate members.

    The name says "the groups they were drawn from" and the docstring says a
    party is shrunk "toward its group's" mean, which reads as a partition —
    small parties here, large parties there. It is not one, and this is
    deliberate: an earlier version DID split the ballot at 5%, "which invented
    a discontinuity" (constants block), and the split was removed in favour of
    a centre and a width that both vary continuously with size. So the group
    is the whole record, every party is in it, and ``groups`` is four
    diagnostic keys.

    This is asserted because a caller has already been caught believing
    otherwise: ``montecarlo.py:2319`` reads ``_groups.get("small", {})`` and
    then ``small.get("median", 0.8)``. There is no ``"small"`` key, so the
    ``__small__`` band it builds is the typed pair 0.8/0.8 on every run of
    every city-year — the absence-is-the-neutral-value defect class exactly.
    ``__small__`` is then read by nothing. See the findings for this file.

    ``worth`` is keyed on parties WITH a record, not on the baseline, so it is
    not total over the priors either — a caller that iterates it is iterating a
    subset, and one that does ``worth.get(p, 0.0)`` is silently treating "no
    record" as "worth nothing", which happens to be right here.
    """
    record = _filler() | _ladder((2,))
    baseline = _baseline(record, {"NOHIST": 0.05})
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    # `absorption` ADDED 2026-08-27 and pinned here deliberately. It is the
    # absorption accounting from NULL-RESULTS.md §4.3 — how much the shrinkage,
    # the SD clamps and the pooled fallback each SWALLOWED — and it exists
    # because "no change" was being reported without anyone able to say which
    # stage ate the change. It is a diagnostic like the other four and no
    # arithmetic reads it; if that ever stops being true this assertion is the
    # place it will be noticed.
    assert set(groups) == {"centre", "spread", "worth", "sd", "absorption"}, (
        f"the diagnostic block's keys are now {sorted(groups)}. Every caller "
        f"reads it with `.get(name, <default>)`, so an added or renamed key is "
        f"invisible until someone notices a typed default in the output — "
        f"which is what happened to `small` at montecarlo.py:2319.")
    assert "small" not in groups, (
        "a `small` key has appeared, so montecarlo.py:2319's `__small__` band "
        "has silently STOPPED being the typed 0.8/0.8 it has always been. "
        "Whatever it now is, it is a change to the forecast and must be "
        "measured against real results.")

    assert set(groups["worth"]) == set(record), (
        "`worth` no longer covers exactly the parties with a record")
    assert "NOHIST" not in groups["worth"], (
        "a party with no retention record now reports a `worth`. `spine` "
        "weights the local route by k/(worth+k); a worth appearing from "
        "nowhere for a party with no record moves that blend.")

    assert set(groups["sd"]) == set(priors), "widths and priors disagree"
    everything = [obs for rows in record.values() for obs in rows]
    assert groups["centre"]["n"] == len(everything), (
        f"the block reports n={groups['centre']['n']} over a record holding "
        f"{len(everything)} observations")
    assert abs(groups["centre"]["effective_n"]
               - sum(_rel(share) for _r, share in everything)) < 1e-9, (
        "`effective_n` is no longer the sum of what the observations are "
        "worth, so the headline 'n transitions' and the weight actually "
        "carried have come apart")


def test_group_membership_is_total_and_deterministic_over_the_baseline():
    """Every baseline party gets exactly one prior and one width, twice running.

    Totality: ``montecarlo.blended_centres`` raises an ``AssertionError`` for a
    party with a national baseline and no spine level, no seed and no θ prior
    (montecarlo.py:1096) — a party silently dropped here is a crash there, or
    worse, a party quietly priced by whatever answers first.

    Determinism: the function fits two least-squares lines and iterates a
    ``set``. If any part of it depended on iteration order the model would be
    irreproducible run to run, which no golden and no freeze could diagnose.
    """
    record = _filler() | _ladder((1, 3))
    baseline = _baseline(record, {"NOHIST_A": 0.07, "NOHIST_B": 0.004})
    with synthetic_record(record):
        first, groups_a = levels.theta_prior(TARGET_UNUSED, baseline)
    with synthetic_record(record):
        second, groups_b = levels.theta_prior(TARGET_UNUSED, baseline)

    missing = sorted(set(baseline) - set(first))
    assert not missing, (
        f"{len(missing)} parties in the baseline got no θ prior "
        f"(first: {missing[0]}); montecarlo.py:1096 raises for exactly this")
    assert set(first) == set(record) | set(baseline)
    assert first == second and groups_a == groups_b, (
        "two calls on the same record returned different answers; the layer "
        "is not a function of its inputs")


# --------------------------------------------------------------------------
# FINDINGS — behaviour documented here because phase A does not edit src/
# --------------------------------------------------------------------------

def test_a_record_of_one_observation_is_refused_rather_than_returning_nan():
    """RE-RECORDED 2026-08-28. The silent nan is now a named refusal (F21).

    This pinned the defect: `np.std(..., ddof=1)` over ONE observation is
    `nan`, `np.clip` propagates it, `sd_for` hands the same nan to every party,
    and `make_drawer` reads `sd_measured.get(party, sd_default)` with the key
    PRESENT — so the default never fires and the nan reaches the draw. Its own
    message authorised this rewrite: *"If it has been given a guard, DELETE
    THIS TEST and record the fix; if it has been given a typed default width,
    that is a judgement call and belongs in JUDGEMENT-CALLS.md."* It was given
    a guard, not a width.

    **The refusal is unreachable on the archive, which is the point of it.**
    `theta_record` reads `target.year` and `codes` and never `target.city`, so
    the record is identical for all eight metros: 175 observations at 2016, 272
    at 2021, 410 at 2026. Narrowed to a single metro code — the only narrowing
    any caller can do — the thinnest non-empty record is 7. So this converts an
    unverified assumption into a checked one at the site that depends on it,
    and costs nothing.
    """
    record = {"ONLY": [(1.2, 0.05)]}
    with synthetic_record(record) as calls:
        try:
            levels.theta_prior(TARGET_UNUSED, {"ONLY": 0.05, "OTHER": 0.10})
        except ValueError as exc:
            assert "observation" in str(exc), exc
            assert "nan" in str(exc), (
                f"the refusal must say WHAT would have happened — a silent "
                f"nan band for every party — not merely that the input was "
                f"short: {exc}")
        else:
            raise AssertionError(
                "a one-observation record no longer refuses. If it now "
                "returns a typed default width, that is a judgement call and "
                "belongs in JUDGEMENT-CALLS.md, not in a fallback. §1.97 F21.")
    assert len(calls) == 1, (
        "theta_record was not called, so this test did not exercise the "
        "injected record at all")

def test_a_party_in_the_record_but_absent_from_the_baseline_is_priced_at_size_zero():
    """FINDING. The function's own comment says this party "is not here and cannot be".

    ``theta_prior``'s PATH TWO comment: *"a party with NO baseline at all is
    not here and cannot be: θ converts a national share into a local one and
    there is no national share to convert."* The loop iterates
    ``set(record) | set(baseline)``, so it IS here — 20 of the 56 parties
    priced at Johannesburg 2021 are in the record and not in the 2019 national
    result.

    Each is priced at ``baseline.get(party, 0.0)`` — absence read as the
    neutral value 0.0 — so its width is evaluated two decades below the
    smallest observation in the record (``log(max(size, 1e-5))``) and lands on
    ``SD_CEILING``, and its centre is extrapolated to ``log(1e-6)``. Nothing
    downstream consumes them (``blended_centres`` iterates ``base_city``), so
    this is currently inert; it is recorded because "inert" here rests on a
    caller's loop, not on the contract the comment states, and because the
    same ``.get(party, 0.0)`` silently drops those parties out of the
    dispersion fit as well.
    """
    record = _filler()
    record["GONE_NATIONAL"] = [(_line(S0) * math.exp(D), S0)] * 2
    record["GONE_MIRROR"] = [(_line(S0) * math.exp(-D), S0)] * 2
    baseline = _baseline(record)
    del baseline["GONE_NATIONAL"]          # in the record, not in the baseline
    with synthetic_record(record) as calls:
        priors, groups = levels.theta_prior(TARGET_UNUSED, baseline)
    assert len(calls) == 1

    assert "GONE_NATIONAL" in priors, (
        "a party with a record and no national baseline is no longer priced. "
        "That matches the PATH TWO comment and is very likely right — record "
        "the change, and delete this test.")
    widest = max(groups["sd"].values())
    assert groups["sd"]["GONE_NATIONAL"] == widest, (
        f"its width is {groups['sd']['GONE_NATIONAL']:.4f} against a widest "
        f"of {widest:.4f}. It is being priced at size 0.0, below anything in "
        f"the record, so it should carry the widest band the fit can give.")
    assert groups["sd"]["GONE_NATIONAL"] > groups["sd"]["FILLER_00"], (
        "the party with NO size is no longer wider than the smallest party "
        "with one; the size-zero extrapolation has moved")

    # And on the real archive, where it is not hypothetical.
    baseline_2021 = _real_baseline("2021")
    real, real_groups = levels.theta_prior(_real_target("2021"), baseline_2021)
    orphans = sorted(set(real) - set(baseline_2021))
    assert orphans, (
        "no party is priced without a national baseline at 2021 any more — "
        "the code now agrees with its PATH TWO comment; delete this test")
    at_ceiling = [p for p in orphans
                  if real_groups["sd"][p] == levels.SD_CEILING]
    assert len(at_ceiling) == len(orphans), (
        f"{len(orphans) - len(at_ceiling)} of {len(orphans)} parties priced "
        f"without a baseline are no longer pinned to SD_CEILING="
        f"{levels.SD_CEILING}; the size-zero extrapolation has moved")


def test_an_empty_record_returns_an_empty_prior_that_reads_as_success():
    """FINDING (class: absence is the neutral value). No record, no prior, no word.

    Called with no metro codes — or, in production, with an archive whose files
    are missing, since ``levels._citywide`` swallows ``FileNotFoundError`` and
    returns ``{}`` — ``theta_prior`` returns ``({}, {})``. The caller at
    montecarlo.py:2318 is ``if _prior:``, so the entire θ layer, the per-party
    widths and the reported worth are skipped **without a line of output**, and
    the run continues on whatever answers first in ``blended_centres``.

    This is §1.43's shape exactly: a swallowed file error is indistinguishable
    from a deliberate exclusion, which is why the whole NPE1999→LGE2000
    transition contributed zero observations for months. The record here is
    empty for an honest reason (no codes), and the point is that the RETURN
    VALUE cannot tell the two apart.
    """
    baseline = _real_baseline("2021")
    priors, groups = levels.theta_prior(_real_target("2021"), baseline, codes=())
    assert priors == {} and groups == {}, (
        "an empty record now returns something; if it raises or reports, this "
        "finding is fixed and the test should be rewritten around the guard")
    assert baseline, (
        "the baseline was non-empty — every one of these parties lost its θ "
        "prior and the caller's `if _prior:` says nothing about it")


def test_a_party_missing_from_the_baseline_is_dropped_from_the_dispersion_fit():
    """FINDING (same class). Enough absences and the estimator changes, silently.

    The size-dispersion fit skips any recorded party with
    ``baseline.get(party, 0.0) <= 0``. Below six surviving rows the function
    switches to a completely different estimator — one pooled sd for the whole
    ballot, with no size gradient at all — and reports nothing. The switch is
    driven by how many recorded parties happen to appear in the national
    result, which is a property of the ARCHIVE, not a modelling choice.

    Constructed here at the boundary: the same record fitted with a full
    baseline gives a width that varies with size; with the baseline stripped to
    a single party it gives one flat width to every party.
    """
    record = _filler()
    full = _baseline(record)
    with synthetic_record(record):
        _p_full, groups_full = levels.theta_prior(TARGET_UNUSED, full)
    stripped = {"FILLER_00": full["FILLER_00"]}
    with synthetic_record(record):
        _p_thin, groups_thin = levels.theta_prior(TARGET_UNUSED, stripped)

    fitted = groups_full["spread"]
    assert fitted["at_0.1%"] != fitted["at_40%"], (
        "with a full baseline the width no longer varies with size at all")
    flat = groups_thin["spread"]
    assert flat["at_0.1%"] == flat["at_40%"], (
        f"the stripped-baseline run still varies with size ({flat}); the "
        f"silent fallback has been given a guard or a report, in which case "
        f"this finding is fixed")
    assert set(groups_thin["sd"].values()) == {flat["at_40%"]}, (
        "the pooled fallback is no longer handing every party one width")


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
