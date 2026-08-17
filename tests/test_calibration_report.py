"""What the scoreboard cannot see, it cannot report — and nobody goes looking.

Two classes of error, both about the INSTRUMENT rather than the model. Neither
moves a forecast by a single seat; both changed what everyone downstream
believed the forecast was doing.

CLASS 8 (continued) — SUMMARY ARTEFACT. A reported statistic that is not what it
    claims. `test_regressions.py` records two instances (the unrelabelled
    ENTRANT, and marginal medians presented as a council). This is the third and
    it hid the largest one: `compare_history.rank_bands` reported a SIGNED sum of
    per-party error within each rank band. The sign is a real finding — it is
    what shows one band eating another — but a signed sum is not a measure of
    error, because two parties wrong in opposite directions inside one band
    cancel and the band then reports as accurate. At **Johannesburg 2021 ranks
    1-3 read +1.36pp on the published statistic and 26.69pp of actual error**:
    ANC +6.53 and DA +7.39 against ActionSA −12.59. That city-year is the model's
    WORST on seats (104 of coherent error) and it read SECOND-BEST on the
    headline band table. Across nine city-years the signed total understated the
    top-of-ballot error by 2.2× (+32.67pp against 72.06pp).

    Same class, second instance in the same function: the bands iterate the
    parties that actually stood, so mass the model gives to a party that did not
    stand at all is invisible to every band and was reported nowhere. It is why
    the three bands summed to −6.48pp rather than to zero.

CLASS 12 — AN ERROR THE HARNESS PRODUCES NO STATISTIC FOR. Not a wrong number: a
    missing one. `score.py` has computed PIT and coverage per run since it was
    written, and `compare_history` — the nine-city-year scoreboard everything is
    judged on — pulled `crps.total` out of it and dropped the rest. So the
    single largest systematic property of this model was unmeasured by the thing
    that measures the model. Pooled over the nine city-years the seat-holding
    columns cover 42/75/87 against nominal 50/80/90 and carry a mean PIT of
    0.762; every scored column gives 0.589. Both reject uniformity, both skew
    the same way, and `sweep.py` independently reports ten anomalies of the form
    "interval excludes the truth — ABOVE the whole forecast" and zero below.

    The direction of the diagnosis is what a calibration statistic buys: the
    bands are roughly the right WIDTH (90% nominal → 87% actual) and the centres
    are LOW. That is a level fault, not a dispersion fault, and it has a
    different remedy. A harness that reports neither number cannot tell the two
    apart, and a reviewer had to compute them by hand to find it.

Both are tested here against COMPUTED NUMBERS rather than against the source
text, because a grep for a column name is not a test that the column is right —
which is the mistake `test_regressions.py` records at CLASS 8 itself.

See MODEL-LOG §1.34.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import compare_history as C  # noqa: E402
import score as S  # noqa: E402


# ---------------------------------------------------------------------------
# helpers — synthetic forecasts with a known answer
# ---------------------------------------------------------------------------

class _Run:
    """The two attributes :func:`compare_history.rank_bands` actually reads."""

    def __init__(self, shares: dict[str, float]):
        self.universe = list(shares)
        self.index = {p: i for i, p in enumerate(self.universe)}
        # rank_bands takes the MEAN over draws, so two identical rows give a
        # mean exactly equal to the share asked for and the test asserts on
        # arithmetic rather than on Monte Carlo noise.
        row = [shares[p] for p in self.universe]
        self.pr_share_draws = np.array([row, row], dtype=float)
        self.ward_share_draws = None


def _poisson_forecast(rng, parties, lam_forecast, lam_truth, draws=600):
    """A seat forecast with a KNOWN calibration.

    ``lam_forecast == lam_truth`` is a perfectly calibrated discrete forecast:
    the truth is a fresh draw from the very distribution being forecast, so its
    randomised PIT is uniform by construction. Setting ``lam_truth`` above
    ``lam_forecast`` makes the truth land high in the forecast distribution,
    which is the shape this model has and the shape the pooled statistic must
    be able to name.
    """
    seat_draws = [{} for _ in range(draws)]
    actual = {}
    for party in parties:
        column = rng.poisson(lam_forecast, size=draws)
        for d, value in zip(seat_draws, column):
            d[party] = int(value)
        actual[party] = int(rng.poisson(lam_truth))
    return seat_draws, actual


def _synthetic_results(rng, n_city_years, parties_per, lam_forecast, lam_truth):
    """``n_city_years`` blocks in the shape ``pooled_calibration`` consumes."""
    results = []
    for k in range(n_city_years):
        parties = [f"P{k}_{j}" for j in range(parties_per)]
        seat_draws, actual = _poisson_forecast(rng, parties, lam_forecast,
                                               lam_truth)
        results.append({
            "city": f"Synthetic{k}", "year": "2021",
            "calibration": C.calibration_columns(seat_draws, actual, None,
                                                 seed=10_000 + k),
        })
    return results


# ---------------------------------------------------------------------------
# CLASS 8 — the band statistic that nets out offsetting errors
# ---------------------------------------------------------------------------

def test_rank_bands_reports_absolute_error_and_not_only_the_signed_sum():
    """Johannesburg 2021, ranks 1-3: +1.36pp signed, 26.69pp of real error.

    The numbers below are that city-year's, rounded: ANC forecast 39.75% against
    an actual 33.22% (+6.53), DA 32.84% against 25.45% (+7.39), ActionSA 5.53%
    against 18.12% (−12.59). The signed sum is +1.33pp — the second-best row in
    the whole band table — and the band is 26.51pp wrong. The model's worst
    city-year on seats read as one of its best here for four months.

    A signed statistic is kept, because the sign genuinely says something an
    absolute one destroys: it is what shows ranks 1-3 eating ranks 4-12. What is
    forbidden is reporting it ALONE.
    """
    actual_pr = {"ANC": 0.3322, "DA": 0.2545, "ASA": 0.1812,
                 "EFF": 0.1011, "PA": 0.0296, "IFP": 0.0236}
    run = _Run({"ANC": 0.3975, "DA": 0.3284, "ASA": 0.0553,
                "EFF": 0.1384, "PA": 0.0008, "IFP": 0.0122,
                "ENTRANT": 0.0674})
    actual_seats = {"ANC": 91, "DA": 71, "ASA": 44, "EFF": 29, "PA": 8, "IFP": 7}

    bands = C.rank_bands(run, actual_pr, actual_seats)
    top = bands["1-3"]

    assert "abs_pp" in top, (
        "rank_bands reports no absolute error. A signed sum over a band cancels "
        "offsetting errors: this case is +1.33pp signed and 26.51pp wrong, and "
        "the signed figure was the only one published.")

    signed, absolute = top["signed_pp"], top["abs_pp"]
    assert abs(signed) < 2.0, (
        f"the synthetic case is meant to reproduce the cancellation and did "
        f"not: signed {signed:+.2f}pp. Fix the fixture, not the assertion.")
    assert absolute > 25.0, (
        f"absolute band error came out at {absolute:.2f}pp, but the three "
        f"parties are 6.53 + 7.39 + 12.59 = 26.51pp wrong. The absolute column "
        f"is netting something out and is therefore not an absolute column.")
    assert absolute > 10 * abs(signed), (
        f"absolute {absolute:.2f}pp against signed {signed:+.2f}pp — the whole "
        f"point of this row is that the two differ by an order of magnitude")

    # The invariant, on every band: |signed| <= abs, and they coincide only
    # when every party in the band errs the same way (Tshwane 2021 ranks 1-3,
    # +7.64 signed and 7.64 absolute, is the real instance).
    for label in ("1-3", "4-12", "13+"):
        band = bands[label]
        assert band["abs_pp"] + 1e-9 >= abs(band["signed_pp"]), (
            f"band {label}: |signed| {abs(band['signed_pp']):.4f} exceeds "
            f"absolute {band['abs_pp']:.4f}, which is arithmetically impossible "
            f"— the two columns are not being computed over the same parties")


def test_the_report_itself_prints_both_band_columns():
    """A statistic computed and not printed is a statistic nobody reads.

    The defect was in the published table, not in the arithmetic: `rank_bands`
    could have returned anything and the report showed one number per band. So
    assert on the rendered row, and assert by parsing its numbers rather than by
    grepping the source — a source grep on one file is exactly how the
    unrelabelled ENTRANT survived (CLASS 8, `test_regressions.py`).
    """
    actual_pr = {"ANC": 0.3322, "DA": 0.2545, "ASA": 0.1812, "EFF": 0.1011}
    run = _Run({"ANC": 0.3975, "DA": 0.3284, "ASA": 0.0553, "EFF": 0.1384})
    bands = C.rank_bands(run, actual_pr, {"ANC": 91, "DA": 71, "ASA": 44})

    result = {
        "city": "Synthetic", "slug": "synthetic", "year": "2021", "council": 270,
        "votes": [], "pr_mae": 6.96, "ward_mae": 6.22, "pr_mae_median": 6.96,
        "ward_mae_median": 6.22, "bands": bands, "seats": {},
        "seat_abs_err": 105, "seat_abs_err_coherent": 104, "median_sum": 257,
        "crps": 79.5, "calibration": {}, "opponents": {},
    }
    text = C.render([result])
    rows = [line for line in text.splitlines()
            if line.startswith("| Synthetic 2021 |")]
    assert rows, "the rendered report has no row for the city-year it was given"

    # The band row is whichever row carries the signed band figure — found by
    # its value, so this does not depend on the column order, the heading text
    # or how many tables the report happens to have.
    signed = round(bands["1-3"]["signed_pp"], 2)
    numbers = {line: {round(float(v), 2)
                      for v in re.findall(r"-?\d+\.\d+", line)} for line in rows}
    band_rows = [line for line, values in numbers.items() if signed in values]
    assert band_rows, (
        f"no row of the report carries the signed band error {signed:+.2f}pp. "
        f"The sign is the finding that shows one band eating another and must "
        f"stay — the absolute column is an addition, not a replacement.")

    absolute = bands["1-3"].get("abs_pp")
    assert absolute is not None, (
        "rank_bands returns no absolute error, so the report has none to "
        "print: every band row a reader sees is a figure with the offsetting "
        "errors already cancelled out of it")

    printed = set().union(*(numbers[line] for line in band_rows))
    assert round(absolute, 2) in printed, (
        f"the band table prints no absolute error for ranks 1-3 "
        f"({absolute:.2f}pp against a signed "
        f"{bands['1-3']['signed_pp']:+.2f}pp). A reader is being shown the "
        f"cancelled figure and nothing else, which is how the model's worst "
        f"city-year read as its second-best.")


def test_mass_on_parties_that_did_not_stand_is_reported_somewhere():
    """The bands iterate the ballot, so a phantom party falls outside all three.

    `rank_bands` walks `actual_pr`, so a share the model assigns to a party that
    contested nothing is counted by no band. Across the nine city-years that is
    6.48pp — which is precisely why the three signed bands summed to −6.48pp
    instead of to zero, a discrepancy visible in the printed totals for months
    and explained nowhere. It includes the generic ENTRANT column in a city-year
    where no party arrived, which is a genuine error and should be paid for.
    """
    # Both vectors are shares and both sum to one, which is what makes the
    # identity below (bands + phantom = 0) hold exactly.
    actual_pr = {"ANC": 0.40, "DA": 0.30, "EFF": 0.20, "IFP": 0.10}
    run = _Run({"ANC": 0.40, "DA": 0.30, "EFF": 0.20, "IFP": 0.08,
                "ENTRANT": 0.02})

    bands = C.rank_bands(run, actual_pr, {"ANC": 100, "DA": 80})
    assert "phantom" in bands, (
        "rank_bands reports no phantom mass. Every point the model puts on a "
        "party that did not stand is currently invisible to the statistic that "
        "is supposed to say where the vote error sits.")
    assert bands["phantom"]["n"] == 1, (
        f"expected one phantom party, got {bands['phantom']['n']}: "
        f"{bands['phantom'].get('top')}")
    assert abs(bands["phantom"]["pp"] - 2.0) < 1e-6, (
        f"phantom mass reported as {bands['phantom']['pp']:.4f}pp; the fixture "
        f"puts exactly 2.00pp on a party that did not contest")

    signed_total = sum(bands[label]["signed_pp"] for label in ("1-3", "4-12", "13+"))
    assert abs(signed_total + bands["phantom"]["pp"]) < 1e-6, (
        f"the bands sum to {signed_total:+.4f}pp and the phantom total is "
        f"{bands['phantom']['pp']:.4f}pp. These must be equal and opposite — "
        f"shares sum to one on both sides — and if they are not, some of the "
        f"error is being counted twice or not at all.")


# ---------------------------------------------------------------------------
# CLASS 12 — an error the harness produces no statistic for
# ---------------------------------------------------------------------------

def test_pooled_calibration_is_produced_and_is_flat_for_a_calibrated_forecast():
    """A forecast that IS calibrated must read as calibrated, or nothing else counts.

    The truth here is a fresh draw from the same Poisson the forecast is made
    of, so the randomised PIT is uniform by construction and coverage must match
    the nominal level. This is the null: an instrument that fails it manufactures
    its own conclusion, which `score.py` records having happened twice — 93% of
    perfectly calibrated replicates printed "U-shaped, under-dispersed, widen it"
    under an outcome-selected column rule.

    Read against the model's own pooled figures (n=132 seat-holding columns):
    42/75/87 against nominal 50/80/90, mean PIT 0.762.
    """
    rng = np.random.default_rng(4242)
    results = _synthetic_results(rng, n_city_years=8, parties_per=30,
                                 lam_forecast=40.0, lam_truth=40.0)
    pooled = C.pooled_calibration(results)

    assert set(pooled) >= {"claimed", "all"}, (
        "pooled_calibration does not report both populations. The difference "
        "between the columns the model CLAIMS and every column carried is "
        "itself the finding — one is diluted by ~200 parties correctly at zero.")

    block = pooled["all"]
    assert block["n"] >= 100, (
        f"only {block['n']} columns pooled; per city-year these statistics are "
        f"noise (Johannesburg 2021 reads 12/62/75 on n=8) and pooling is the "
        f"only thing that makes them readable")

    mean = block["pit"]["mean"]
    assert abs(mean - 0.5) < 0.06, (
        f"pooled mean PIT {mean:.3f} on a PERFECTLY CALIBRATED forecast. The "
        f"instrument is biased and any verdict it prints about the model — "
        f"which reads 0.762 — is unreadable.")
    crit = block["pit"]["chi2_crit_95"]
    assert block["pit"]["chi2"] < crit, (
        f"χ² {block['pit']['chi2']:.1f} against the 5% critical value {crit} "
        f"for a forecast drawn from the truth's own distribution. The histogram "
        f"is rejecting uniformity where uniformity is the fact.")

    # Coverage of a DISCRETE quantity over-covers under calibration — the
    # interval has to contain whole endpoints — so the null is one-sided: a
    # calibrated forecast may cover a little too much and must never cover
    # materially too little. That asymmetry is what makes the model's own 42%
    # at a nominal 50% a finding rather than an artefact: discreteness pushes
    # the other way.
    for row in block["coverage"]:
        empirical, level = row["empirical"], row["level"]
        assert empirical > level - 0.03, (
            f"nominal {level:.0%} covered only {empirical:.0%} on a calibrated "
            f"forecast ({row['inside']}/{row['counted']}). Discreteness can "
            f"only inflate coverage, so an instrument that under-covers on the "
            f"null cannot be quoted about the model's 42/75/87.")
        assert empirical < level + 0.12, (
            f"nominal {level:.0%} covered {empirical:.0%} "
            f"({row['inside']}/{row['counted']}) — far wider than the "
            f"discreteness of the endpoints can explain, so the intervals "
            f"themselves are not being read at the level asked for")


def test_pooled_calibration_detects_a_forecast_that_is_systematically_low():
    """The fault the harness could not see: right width, wrong centre.

    The forecast is Poisson(40) and the truth is Poisson(46) — very nearly the
    same spread, shifted up — which is this model's shape: pooled coverage
    42/75/87 against
    nominal 50/80/90 (bands roughly the right WIDTH) with a mean PIT of 0.762
    (centres LOW). `sweep.py` says the same thing from the other side: ten
    anomalies of the form "interval excludes the truth, above the whole
    forecast", and zero below.

    So the statistic must not merely reject uniformity — it must reject it
    UPWARDS. A U-shaped verdict here would send the next iteration to widen the
    bands, which is the wrong remedy for a level bias and would make the
    forecast less sharp for nothing.
    """
    rng = np.random.default_rng(4242)
    results = _synthetic_results(rng, n_city_years=8, parties_per=30,
                                 lam_forecast=40.0, lam_truth=46.0)
    pooled = C.pooled_calibration(results)
    block = pooled["all"]

    mean = block["pit"]["mean"]
    assert mean > 0.65, (
        f"pooled mean PIT {mean:.3f} for a forecast whose truth is a shade "
        f"under one standard deviation too high per party. A statistic that "
        f"cannot see a shift of that size cannot see the model's own.")
    crit = block["pit"]["chi2_crit_95"]
    assert block["pit"]["chi2"] > crit, (
        f"χ² {block['pit']['chi2']:.1f} against a 5% critical value of {crit}: "
        f"the histogram calls a badly biased forecast flat")
    assert "under-predicts" in block["pit"]["verdict"], (
        f"the verdict reads {block['pit']['verdict']!r} for a forecast that is "
        f"systematically LOW. The direction is the whole diagnosis — a level "
        f"fault and a dispersion fault need opposite fixes.")

    cover90 = [row for row in block["coverage"] if row["level"] == 0.9][0]
    assert cover90["empirical"] < 0.9, (
        f"nominal 90% covered {cover90['empirical']:.0%} of a truth shifted "
        f"three seats up; coverage is not responding to the bias at all")

    calibrated = C.pooled_calibration(
        _synthetic_results(np.random.default_rng(4242), 8, 30, 40.0, 40.0))
    assert mean > calibrated["all"]["pit"]["mean"] + 0.1, (
        "the biased and the calibrated forecast return the same pooled mean "
        "PIT, so the statistic is not measuring what it is quoted for")


def test_the_pooled_pit_is_randomised_because_seats_are_integers():
    """A deterministic PIT on integer data prints bias that is not there.

    Seats are a discrete quantity, so ``F(y)`` jumps. Taking the plain CDF value
    at the truth adds ``P(X = y)`` of upward bias to every column — for a
    Poisson(5) forecast that is about +0.09 on the mean and a χ² far past the
    critical value — and the model's real finding is a mean PIT of 0.762 read
    against 0.5. An instrument carrying its own upward bias cannot be used to
    diagnose an upward bias. The randomised transform
    ``u = F(y⁻) + v·(F(y) − F(y⁻))`` restores exact uniformity under calibration.

    Both halves are asserted: that the randomised statistic passes the null, and
    that the deterministic one computed over the same numbers FAILS it. Without
    the second half this test would pass on a version that had quietly dropped
    the randomisation and simply been lucky.
    """
    rng = np.random.default_rng(7)
    results = _synthetic_results(rng, n_city_years=8, parties_per=30,
                                 lam_forecast=2.5, lam_truth=2.5)
    pooled = C.pooled_calibration(results)["all"]

    # 1. the randomised statistic, on a calibrated forecast, is flat
    assert abs(pooled["pit"]["mean"] - 0.5) < 0.06, (
        f"randomised pooled PIT mean {pooled['pit']['mean']:.3f} on a "
        f"calibrated discrete forecast")

    # 2. the same columns, transformed deterministically, are NOT — so the test
    #    above is testing the randomisation and not merely a kind seed.
    deterministic = []
    rng2 = np.random.default_rng(7)
    for k in range(8):
        parties = [f"Q{k}_{j}" for j in range(30)]
        seat_draws, actual = _poisson_forecast(rng2, parties, 2.5, 2.5)
        _, samples, truth = S.seat_matrix(seat_draws, actual, None)
        for j in range(samples.shape[1]):
            deterministic.append(float((samples[:, j] <= truth[j]).mean()))
    flat = S.pit_histogram(np.array(deterministic))
    assert flat["mean"] > 0.55, (
        f"the deterministic PIT of the same data has mean {flat['mean']:.3f}; "
        f"this test can no longer tell a randomised transform from a plain one")
    assert flat["chi2"] > flat["chi2_crit_95"], (
        "the deterministic PIT no longer fails the uniformity test, so passing "
        "it proves nothing about the randomisation")

    # 3. and the randomisation must actually be varying: the same integer data
    #    under two seeds must give different PIT values, or nothing is being
    #    drawn across the jump.
    parties = [f"R{j}" for j in range(20)]
    seat_draws, actual = _poisson_forecast(np.random.default_rng(11), parties,
                                           2.5, 2.5)
    a = C.calibration_columns(seat_draws, actual, None, seed=1)["all"]["pit"]
    b = C.calibration_columns(seat_draws, actual, None, seed=2)["all"]["pit"]
    assert a != b, (
        "two different seeds gave identical PIT values for the same integer "
        "seat draws, so no randomisation is being applied across the jump and "
        "the histogram will report discreteness as bias")


def test_the_report_prints_the_pooled_calibration_numbers():
    """Computed is not reported, and only what is reported gets acted on.

    `score.py` has produced coverage and PIT per run since it was written. The
    nine-city-year scoreboard took `crps.total` from it and discarded the rest,
    so a reviewer had to recompute the pooled figures by hand to find a bias
    that had been in every run for months. The point of this change is that the
    numbers appear in the standard report.
    """
    rng = np.random.default_rng(2026)
    results = _synthetic_results(rng, n_city_years=3, parties_per=20,
                                 lam_forecast=5.0, lam_truth=8.0)
    for r in results:
        r["city"], r["year"] = "Synthetic", "2021"
    text = C.render_calibration(results)
    pooled = C.pooled_calibration(results)

    assert "alibration" in text and "PIT" in text, \
        "the report has no calibration block at all"
    for pop in ("claimed", "all"):
        n = pooled[pop]["n"]
        assert str(n) in text, (
            f"the report does not state the pooled n for {pop} ({n}). A "
            f"calibration figure without its denominator invites exactly the "
            f"per-city-year reading that makes it noise.")
        mean = f"{pooled[pop]['pit']['mean']:.3f}"
        assert mean in text, (
            f"pooled mean PIT for {pop} is {mean} and does not appear in the "
            f"report; it is the number that says which direction the model is "
            f"wrong in")
    for row in pooled["all"]["coverage"]:
        assert f"{100 * row['empirical']:.0f}%" in text, (
            f"pooled coverage at the {row['level']:.0%} level "
            f"({row['inside']}/{row['counted']}) is not printed. Coverage says "
            f"whether the bands are the right WIDTH; PIT says whether they are "
            f"in the right PLACE. One without the other cannot separate a level "
            f"fault from a dispersion fault.")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
