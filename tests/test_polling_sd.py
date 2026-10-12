"""CLASS 15 — A WEIGHT THAT CANNOT BE DECOMPOSED IS A WEIGHT NOBODY CAN ARGUE WITH.

`polling.POLL_RMS_ERROR` was a flat 3.0pp applied to every poll of every party.
It was measured — the RMS of Ipsos's nine 2016 metro readings, a track record
rather than a nominal margin — and it was measured on **full-sample metro polls
by one house two days before polling day**. Both admitted 2026 polls are
~500-person subsamples of a national sample, by a different house, with an
undisclosed likely-voter screen, taken months out. Applying the same 3.0pp to
those was the assumption most in need of stating before a real 2026 poll moved a
published number.

`n` was recorded on every poll and read by nothing, and there was no cap at all:
ten waves of one house would each have blended at w≈0.9 and the forecast would
have become the poll.

These tests guard the four properties the replacement rests on.

**1. It preserves its own calibration.** The decomposition is only allowed to
call `POLL_HOUSE_SD` measured because removing the sampling term from the 3.03pp
track record is where that number comes from. Run the calibration polls back
through and it must return 3.03pp. If it does not, `POLL_HOUSE_SD` has become a
free parameter and the register row claiming otherwise is false.

**2. Screen and drift are EXCESS, not additions.** The 2.5pp residual is the
TOTAL non-sampling error of polls that had a disclosed method and zero days of
drift, so their screen error is already inside it. A decomposition that adds a
screen term to the calibration case charges it twice — which is the arithmetic
trap in this design and the one thing a reader will not notice.

**3. Averaging waves of ONE house buys nothing.** House error is a common bias.
`effective_houses` must return 1.0 for any number of waves by one house, so that
the aggregate's house term cannot be shrunk by publishing more often.

**4. The cap is bounded and monotone**, because it is the only thing standing
between a single DA-adjacent house and the published forecast.

MODEL-LOG §1.67.
"""

from __future__ import annotations

import math
import statistics as st
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import polling as PG  # noqa: E402

# The nine readings POLL_RMS_ERROR_2016 is the RMS of: ANC/DA/EFF in each of
# Johannesburg, Tshwane and Nelson Mandela Bay, Ipsos 2016.
CALIBRATION_SHARES = (0.46, 0.41, 0.08, 0.47, 0.43, 0.09, 0.37, 0.44, 0.06)

# Fieldwork ended 2016-08-01; polling day was 2016-08-03.
CALIBRATION_POLL = {
    "n": PG.POLL_CAL_N_2016,
    "deff": PG.POLL_CAL_DEFF_2016,
    "screen_disclosed": True,
    "fieldwork_end": "2016-08-01",
}
CALIBRATION_ASOF = date(2016, 8, 3)


def test_the_decomposition_reproduces_the_track_record_it_was_built_from():
    """Run the calibration polls back through σ_poll and get 3.03pp."""
    sds = [PG.poll_sd(CALIBRATION_POLL, s, asof=CALIBRATION_ASOF)
           for s in CALIBRATION_SHARES]
    rms = math.sqrt(sum(x * x for x in sds) / len(sds))
    assert abs(rms - PG.POLL_RMS_ERROR_2016) < 0.0005, (
        f"the decomposition returns {rms:.5f} on its own calibration polls "
        f"against a measured {PG.POLL_RMS_ERROR_2016:.5f} — a gap of "
        f"{abs(rms - PG.POLL_RMS_ERROR_2016) * 100:.3f}pp.\n"
        f"POLL_HOUSE_SD is only carried as MEASURED because it is the residual "
        f"of that track record after the sampling term is removed. If the parts "
        f"no longer sum back to the whole it is a free parameter, and its "
        f"register row is wrong.")


def test_screen_and_drift_are_excess_over_the_calibration_case():
    """Zero for a disclosed screen and zero days out, or every poll pays twice."""
    parts = PG.sd_components(CALIBRATION_POLL, 0.45, asof=CALIBRATION_ASOF)
    assert parts["screen"] == 0.0, (
        f"the calibration poll is charged {parts['screen']:.4f} of screen error. "
        f"Its screen error is already inside POLL_HOUSE_SD, because that "
        f"constant is the TOTAL non-sampling residual of these very polls. A "
        f"screen term here is double counting.")
    # Drift must VANISH as days -> 0. The calibration poll is two days out, not
    # zero, so it carries 0.14pp — negligible against the 3.03pp it has to
    # reproduce, which is why the check above closes to 0.02pp. Assert the
    # property (zero at zero) and the consequence (negligible at two), not an
    # exact zero the calibration case does not have.
    same_day = PG.sd_components(
        dict(CALIBRATION_POLL, fieldwork_end="2016-08-03"), 0.45,
        asof=CALIBRATION_ASOF)
    assert same_day["drift"] == 0.0, (
        f"a poll whose fieldwork ends ON polling day is charged "
        f"{same_day['drift']:.4f} of drift. Drift is an EXCESS term over the "
        f"calibration case and must be zero at zero days out.")
    assert parts["drift"] < 0.002, (
        f"the calibration poll, two days out, is charged "
        f"{parts['drift'] * 100:.2f}pp of drift. It must stay negligible "
        f"against the 3.03pp it has to reproduce, or POLL_DRIFT_PP_PER_ROOT_DAY "
        f"is large enough to have moved the calibration itself.")
    # and both must be positive for the case they exist for
    live = dict(CALIBRATION_POLL, screen_disclosed=False,
                fieldwork_end="2026-07-31")
    later = PG.sd_components(live, 0.45, asof=date(2026, 11, 4))
    assert later["screen"] > 0 and later["drift"] > 0, (
        "an undisclosed screen 96 days out is charged nothing for either — the "
        "excess terms are inert and the decomposition has collapsed to the flat "
        "constant it replaced")


def test_waves_of_one_house_do_not_multiply_into_independent_evidence():
    """H_eff is 1.0 for one house however many waves it publishes."""
    asof = date(2026, 11, 4)
    one = [{"house": "SRF", "fieldwork_end": f"2026-0{m}-01", "numbers": {"DA": 0.4}}
           for m in (3, 5, 7, 9)]
    h = PG.effective_houses(one, asof=asof)
    assert abs(h - 1.0) < 1e-9, (
        f"four waves of one house give H_eff = {h:.3f}, not 1.0. House error is "
        f"a COMMON BIAS across a house's waves — averaging them cuts the "
        f"sampling term and does not touch it. If publishing more often raises "
        f"H_eff, a single house can buy its way to the weight cap.")
    two = one + [{"house": "Ipsos", "fieldwork_end": "2026-09-01",
                  "numbers": {"DA": 0.4}}]
    assert PG.effective_houses(two, asof=asof) > 1.2, (
        "adding a genuinely independent second house does not raise H_eff, so "
        "the measure is not counting houses at all")


def test_the_weight_cap_is_bounded_monotone_and_bites_at_one_house():
    """It is the only thing between one DA-adjacent house and the forecast."""
    caps = [PG.weight_cap(h) for h in (0, 1, 2, 3, 8, 100)]
    assert caps[0] == 0.0, "no houses must mean no weight"
    assert all(b > a for a, b in zip(caps, caps[1:])), (
        f"weight_cap is not monotone in the number of houses: {caps}")
    assert all(c <= 1.0 for c in caps), f"weight_cap exceeds 1: {caps}"
    assert abs(caps[1] - 0.5) < 1e-9, (
        f"the cap at ONE house is {caps[1]:.3f}, not 0.500. The rule §1.67 ships "
        f"is 'a single unreplicated house is never worth more than the model "
        f"itself', which is exactly one half and is why POLL_HOUSE_K is 1.0. A "
        f"different value is allowed, but it needs a sentence someone can check "
        f"— it shipped at 1.4 for a day with no stated reason and that is the "
        f"thing the register exists to catch.")
    assert caps[-1] > 0.95, (
        "with a hundred houses the cap must be near 1.0 — the asymptote is 1 by "
        "argument, because with enough independent houses inverse variance is "
        "the right answer and no cap is wanted")


def test_a_subsample_is_priced_as_a_subsample():
    """`n` finally does work, and a metro cut of a national sample is discounted."""
    sub = {"n": 504, "n_basis": "metro-subsample"}
    standalone = {"n": 504, "n_basis": "standalone"}
    assert PG.effective_n(sub) < PG.effective_n(standalone), (
        "a metro cut of a national sample is priced the same as a "
        "purpose-designed metro poll of the same size")
    assert abs(PG.effective_n(sub) - 504 / PG.POLL_DEFF_SUBSAMPLE) < 1e-9
    assert PG.effective_n({}) is None, (
        "a poll with no recorded n must return None rather than a guess — "
        "`n` was in the schema and read by nothing for the whole life of this "
        "module, and a silent default is how that happens again")
    explicit = PG.design_effect({"n": 504, "deff": 2.4})
    assert explicit == 2.4, (
        "a design effect published by the house must win over our default")


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
