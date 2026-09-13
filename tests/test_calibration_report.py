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

CLASS 8, FOURTH INSTANCE — AND IT SHIPPED IN THE COMMIT THAT FIXED THE THIRD.
    The pooled PIT mean added above is itself a signed average, one level up. It
    runs over every claimed column at once, so a model that forecasts the top of
    the ballot too HIGH and the middle too LOW has the two cancel and reports a
    figure near 0.50. That is not a hypothetical: on the NINE city-years the
    claimed population pooled to **0.588** and split into **0.431 at ranks 1-3**
    and **0.750 at ranks 4-12** (n=27 and n=26, cluster-bootstrap CIs [0.380,
    0.479] and [0.674, 0.810], both excluding 0.50 in opposite directions). The
    same rank ordering the band table already used was eleven lines away.

    ⛔ **ON THE SIXTEEN CITY-YEARS THE CANCELLATION IS NO LONGER WHAT MAKES THE
    POOLED FIGURE MISLEADING.** Ranks 1-3 is now **0.510**, CI [0.474, 0.542],
    containing 0.50 with cycles of opposite sign — refuted. Ranks 4-12 is
    **0.613** on ``claimed`` and **0.688** on ``reference``, the latter
    replicating at 0.623 (2016) and 0.745 (2021). So there is ONE bias, not two,
    and the pooled 0.559 understates it by averaging a real departure against a
    centred band. **The reason to disaggregate is unchanged; the arithmetic
    behind it is not.** Re-measured 2026-08-31; MODEL-LOG §1.146.

    Width splits too, and the two coverage measures disagree where discreteness
    bites: a nominal 50% interval covers 70% at ranks 1-3 and 46% at ranks 4-12
    by `score.coverage`, but 27% at ranks 4-12 once the randomised PIT removes
    the whole-endpoint inflation. So "the bands are the right width, do not
    widen them" is right at the top of the ballot and wrong in the middle.

    Tested here by a synthetic city-year set biased UP at ranks 1-3 and DOWN at
    ranks 4-12 by equal amounts: the pooled mean PIT reads 0.485 and the
    pre-fix report calls it "U-shaped — under-dispersed, widen it", which is the
    wrong remedy for both bands at once.

All of these are tested against COMPUTED NUMBERS rather than against the source
text, because a grep for a column name is not a test that the column is right —
which is the mistake `test_regressions.py` records at CLASS 8 itself.

See MODEL-LOG §1.34 and §1.36.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, skip, run_module  # noqa: E402

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


def _banded_results(rng, n_city_years, lam_forecast, lam_truth_top,
                    lam_truth_mid, per_band=3):
    """City-years whose TOP of the ballot and MIDDLE are biased opposite ways.

    ``per_band`` parties at ranks 1-3 and ``per_band`` at ranks 4-12, with the
    truth drawn BELOW the forecast at the top and ABOVE it in the middle. Equal
    band sizes and symmetric shifts, so the pooled mean PIT comes out at
    ~0.50 — a forecast that reads perfectly centred and is not centred anywhere.

    That was this model's own shape when the panel was nine city-years (ranks
    1-3 mean PIT 0.431, ranks 4-12 0.750, pooled 0.587), and it is the case the
    pooled statistic shipped unable to see. **On the committed SIXTEEN
    city-years the shape has changed and only half of it survives**: pooled
    0.559, ranks 1-3 **0.510** (CI contains 0.50, cycles of opposite sign — the
    finding is refuted), ranks 4-12 **0.613**. The synthetic case below is still
    the right test of the INSTRUMENT — a pooled mean that reads 0.50 over two
    opposite biases — it is simply no longer a portrait of this model.
    Re-measured 2026-08-31; MODEL-LOG §1.146.

    ``actual_pr`` is what supplies the ranking, and the shares are descending by
    construction so party index is rank.
    """
    results = []
    for k in range(n_city_years):
        top = [f"T{k}_{j}" for j in range(per_band)]
        mid = [f"M{k}_{j}" for j in range(per_band)]
        d_top, a_top = _poisson_forecast(rng, top, lam_forecast, lam_truth_top)
        d_mid, a_mid = _poisson_forecast(rng, mid, lam_forecast, lam_truth_mid)
        seat_draws = [{**x, **y} for x, y in zip(d_top, d_mid)]
        actual = {**a_top, **a_mid}
        # descending shares: the ``top`` parties rank 1..per_band, the ``mid``
        # parties rank per_band+1.. -- so with per_band=3 they land exactly on
        # the 1-3 / 4-12 boundary the vote table already uses.
        parties = top + mid
        actual_pr = {p: 1.0 - 0.01 * i for i, p in enumerate(parties)}
        results.append({
            "city": f"Banded{k}", "year": "2021",
            "calibration": C.calibration_columns(
                seat_draws, actual, None, seed=30_000 + k, actual_pr=actual_pr),
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


# ---------------------------------------------------------------------------
# CLASS 8 again — a pooled mean over two opposite biases is not a measure of bias
# ---------------------------------------------------------------------------

def test_pooled_pit_is_split_by_rank_band_and_the_bands_disagree():
    """The fault that shipped one day after the identical fault was fixed.

    ``rank_bands`` reported a SIGNED SUM inside a band, so two parties wrong in
    opposite directions cancelled and the band read accurate. That was fixed.
    In the same commit the pooled PIT mean shipped doing the same thing one
    level up: it averages over ALL claimed columns, and if the top of the ballot
    is forecast too high while the middle is forecast too low, the mean sits
    between them and reports a well-centred forecast.

    The fixture makes that explicit and unarguable. Equal band sizes, equal and
    opposite shifts, so the POOLED mean PIT is ~0.50 — indistinguishable from a
    perfectly centred forecast — while ranks 1-3 are far below 0.50 and ranks
    4-12 far above it. A statistic that cannot separate these two cases cannot
    be quoted about direction at all, and it was being quoted about direction in
    ``ITERATING.md`` rule 8.

    The model's own figures, committed history.json, claimed columns:
    **16 city-years (current): pooled 0.559, ranks 1-3 0.510, ranks 4-12
    0.613.** (Nine city-years, superseded: 0.587 / 0.431 / 0.750.)
    """
    rng = np.random.default_rng(31337)
    results = _banded_results(rng, n_city_years=9, lam_forecast=40.0,
                              lam_truth_top=32.0, lam_truth_mid=48.0)
    pooled = C.pooled_calibration(results)
    block = pooled["claimed"]

    assert "by_band" in block, (
        "pooled_calibration reports no split by rank band. The pooled mean PIT "
        "is an average over every claimed column, and this fixture is biased "
        "UP at ranks 1-3 and DOWN at ranks 4-12 by the same amount — so the "
        "pooled figure reads ~0.50 and the forecast is not centred anywhere. "
        "That is the same defect as a signed error sum inside a rank band, and "
        "it shipped in the same commit that fixed one.")

    bands = block["by_band"]
    for label in ("1-3", "4-12"):
        assert label in bands, (
            f"no pooled calibration for ranks {label}. The rank ordering is "
            f"already computed by rank_band_of and used by the vote table; the "
            f"calibration must split on the same one or the two instruments "
            f"cannot be read against each other.")

    pooled_mean = block["pit"]["mean"]
    assert abs(pooled_mean - 0.5) < 0.05, (
        f"the fixture is meant to pool to ~0.50 and pooled to {pooled_mean:.3f}; "
        f"fix the fixture, not the assertion — the whole point is a case the "
        f"pooled statistic calls unbiased")

    top, mid = bands["1-3"]["mean_pit"], bands["4-12"]["mean_pit"]
    assert top < 0.40, (
        f"ranks 1-3 pooled to mean PIT {top:.3f} on a band whose truth is a "
        f"standard deviation BELOW the forecast. The band statistic is not "
        f"seeing an over-forecast it is being handed.")
    assert mid > 0.60, (
        f"ranks 4-12 pooled to mean PIT {mid:.3f} on a band whose truth is a "
        f"standard deviation ABOVE the forecast")
    assert (top - 0.5) * (mid - 0.5) < 0, (
        f"ranks 1-3 ({top:.3f}) and ranks 4-12 ({mid:.3f}) come out on the same "
        f"side of 0.50. The two bands are not being separated at all, so the "
        f"split reports the pooled answer twice.")

    # And the split must distinguish this from a forecast that really IS
    # unbiased everywhere — otherwise the new columns are decoration.
    calibrated = C.pooled_calibration(
        _banded_results(np.random.default_rng(31337), 9, 40.0, 40.0, 40.0)
    )["claimed"]["by_band"]
    spread = abs(top - mid)
    null_spread = abs(calibrated["1-3"]["mean_pit"] - calibrated["4-12"]["mean_pit"])
    assert spread > null_spread + 0.25, (
        f"the biased fixture separates its bands by {spread:.3f} and an "
        f"unbiased one by {null_spread:.3f}. The split is not measuring the "
        f"thing it was added for.")

    # The CIs are what turn "the bands differ" into a claim. Both must exclude
    # 0.50, in opposite directions -- which is what the model's own claimed
    # population does: [0.380, 0.480] and [0.673, 0.810].
    lo_top, hi_top = bands["1-3"]["ci"]
    lo_mid, hi_mid = bands["4-12"]["ci"]
    assert hi_top < 0.5 < lo_mid, (
        f"cluster-bootstrap CIs [{lo_top:.3f}, {hi_top:.3f}] and "
        f"[{lo_mid:.3f}, {hi_mid:.3f}] do not straddle 0.50 in opposite "
        f"directions. Without that the two band means are a difference anyone "
        f"can call noise.")


def test_band_coverage_pools_the_same_columns_the_population_does():
    """Split coverage must be the population's coverage, partitioned.

    Coverage is reported per band as well as pooled, and the pooled figure comes
    from ``score.coverage`` over the whole population while the band figures
    come from per-column hits. If those two paths ever disagree, one of them is
    counting columns the other is not and every band row is unreadable. The
    bands plus ``off-ballot`` are a partition of the population, so both the
    numerators and the denominators must add up exactly.
    """
    rng = np.random.default_rng(99)
    results = _banded_results(rng, n_city_years=6, lam_forecast=12.0,
                              lam_truth_top=9.0, lam_truth_mid=15.0)
    pooled = C.pooled_calibration(results)["claimed"]

    band_n = sum(b["n"] for b in pooled["by_band"].values())
    assert band_n == pooled["n"], (
        f"the bands hold {band_n} columns and the population {pooled['n']}. "
        f"The rank bands plus off-ballot are a partition; if they are not, some "
        f"columns are counted twice or dropped and the band means are averages "
        f"over an unknown set.")

    for row in pooled["coverage"]:
        level = row["level"]
        inside = counted = 0
        for block in pooled["by_band"].values():
            hit = [r for r in block["coverage"] if r["level"] == level][0]
            inside += hit["inside"]
            counted += hit["counted"]
        assert (inside, counted) == (row["inside"], row["counted"]), (
            f"at the {level:.0%} level the bands sum to {inside}/{counted} and "
            f"score.coverage over the whole population gives "
            f"{row['inside']}/{row['counted']}. The per-column hits and the "
            f"pooled coverage are not the same measurement.")


def test_the_width_verdict_is_reported_free_of_discreteness_inflation():
    """The reviewer's 27% and the harness's 46% are two different statistics.

    `score.coverage` reads the empirical quantile interval, which on integer
    seats has to include whole endpoints and so over-covers — its own docstring
    says as much. The randomised PIT does not. On the real ranks 4-12 the gap is
    19 points (interval 0.46, PIT-corrected 0.27) and it decides the width
    verdict; on the real ranks 1-3, whose forecast distributions are tens of
    seats wide, one endpoint is a negligible share of the interval and the two
    measures come out equal (0.704 both ways).

    So the fixture puts one band on a forecast so wide that discreteness cannot
    matter and one on a forecast two seats wide, both PERFECTLY calibrated, and
    asserts that the gap appears where discreteness is and not where it is not.
    A report printing only the quantile coverage would call the small band's
    intervals adequate — which is exactly the mistake available on ranks 4-12.
    """
    # 20 city-years, so the null is asserted on ~60 and ~180 columns rather than
    # on 27, where a perfectly calibrated band sits two standard errors from
    # nominal often enough to make the test a coin toss.
    rng = np.random.default_rng(808)
    results = []
    for k in range(20):
        big = [f"B{k}_{j}" for j in range(3)]     # ranks 1-3, tens of seats
        small = [f"S{k}_{j}" for j in range(9)]   # ranks 4-12, two or three
        d_big, a_big = _poisson_forecast(rng, big, 4000.0, 4000.0)
        d_small, a_small = _poisson_forecast(rng, small, 2.0, 2.0)
        seat_draws = [{**x, **y} for x, y in zip(d_big, d_small)]
        parties = big + small
        results.append({
            "city": f"Discrete{k}", "year": "2021",
            "calibration": C.calibration_columns(
                seat_draws, {**a_big, **a_small}, None, seed=50_000 + k,
                actual_pr={p: 1.0 - 0.01 * i for i, p in enumerate(parties)}),
        })
    bands = C.pooled_calibration(results)["all"]["by_band"]

    def at(block, key, level):
        return [r for r in block[key] if r["level"] == level][0]["empirical"]

    big_gap = at(bands["1-3"], "coverage", 0.5) - at(bands["1-3"], "pit_coverage", 0.5)
    small_gap = at(bands["4-12"], "coverage", 0.5) - at(bands["4-12"], "pit_coverage", 0.5)

    assert abs(big_gap) < 0.05, (
        f"a band whose forecast spans ~130 integers shows a {big_gap:+.3f} gap "
        f"between quantile coverage and PIT coverage. There is nothing for "
        f"discreteness to inflate at that scale, so the two statistics are not "
        f"measuring the same thing at all.")
    assert small_gap > 0.10, (
        f"a band of parties on ~2 seats shows only a {small_gap:+.3f} gap. On "
        f"the real ranks 4-12 it is 0.19, and it is the whole reason the raw "
        f"coverage there reads adequate while the model's intervals are not.")
    assert at(bands["4-12"], "pit_coverage", 0.5) > 0.40, (
        f"the PIT coverage of a PERFECTLY calibrated small-party band is "
        f"{at(bands['4-12'], 'pit_coverage', 0.5):.3f} against a nominal 0.50. "
        f"The corrected statistic must pass the null, or its verdict on the "
        f"model's 0.27 is unreadable.")


def test_the_report_prints_the_per_band_calibration_and_not_only_the_pool():
    """Computed and not printed is the same as not computed.

    This is the lesson `rank_bands` had already taught: the absolute band error
    could have been returned by the function for months and the published table
    still showed one number per band. So assert on the rendered text, by the
    NUMBERS it must contain rather than by a heading.
    """
    rng = np.random.default_rng(606)
    results = _banded_results(rng, n_city_years=9, lam_forecast=40.0,
                              lam_truth_top=32.0, lam_truth_mid=48.0)
    text = C.render_calibration(results)
    bands = C.pooled_calibration(results)["claimed"]["by_band"]

    for label in ("1-3", "4-12"):
        mean = f"{bands[label]['mean_pit']:.3f}"
        assert mean in text, (
            f"the report does not print the mean PIT for ranks {label} "
            f"({mean}). The pooled figure it does print is the average of this "
            f"one and its opposite, and a reader acting on it would reach the "
            f"wrong conclusion about both bands.")
        assert str(bands[label]["n"]) in text, (
            f"no denominator printed for ranks {label} (n={bands[label]['n']})")
        for key in ("coverage", "pit_coverage"):
            for row in bands[label][key]:
                assert f"{100 * row['empirical']:.0f}%" in text, (
                    f"ranks {label}: {key} at the {row['level']:.0%} level "
                    f"({row['inside']}/{row['counted']}) is not printed. Width "
                    f"is band-dependent here — a nominal 50% interval covers "
                    f"70% at ranks 1-3 and 27% at ranks 4-12 on the real data "
                    f"once discreteness is corrected for — so a single pooled "
                    f"coverage row answers the width question wrongly for both.")

    assert "under-forecasts" not in text or "over" in text, (
        "the calibration prose still says a high pooled mean means 'the model "
        "under-forecasts' with nothing beside it. That is false of this model: "
        "it over-forecasts ranks 1-3 and under-forecasts ranks 4-12.")


def test_the_all_population_is_selected_on_the_outcome_and_says_so():
    """`all` was documented as neutral. `score.seat_matrix` makes it a mixture.

    A column is admitted when ``truth[i] > 0 or samples[:, i].max() > 0``. The
    second clause selects on the forecast, which is neutral; the FIRST selects on
    the outcome — a party is in the population because it WON. On the real nine
    city-years five of the 331 ``all`` columns carry PIT exactly 1.0: parties
    given zero seats in every single draw, present only because they won one.

    Asserted by construction rather than by reading the docstring: a party the
    forecast never gives a seat to, which nevertheless wins seats, must appear in
    ``all``, must NOT appear in ``claimed``, and must carry PIT 1.0. `score.py`
    is deliberately not changed — the rule is right for CRPS, which is what it
    is for. What was wrong was the label.
    """
    rng = np.random.default_rng(5)
    parties = [f"Z{j}" for j in range(6)]
    seat_draws, actual = _poisson_forecast(rng, parties, 8.0, 8.0)
    # a party the model is certain gets nothing, and which wins four seats
    for d in seat_draws:
        d["GHOST"] = 0
    actual["GHOST"] = 4
    actual_pr = {p: 1.0 - 0.01 * i for i, p in enumerate(parties + ["GHOST"])}

    blocks = C.calibration_columns(seat_draws, actual, None, seed=1,
                                   actual_pr=actual_pr)
    assert "GHOST" in blocks["all"]["parties"], (
        "a party with a zero forecast in every draw and four actual seats is "
        "not in the `all` population, so the admission rule is not what "
        "score.seat_matrix documents")
    assert "GHOST" not in blocks["claimed"]["parties"], (
        "`claimed` admitted a party the forecast never gives a seat to — then "
        "it is not forecast-selected either and nothing in this report is a "
        "neutral test")
    pit = blocks["all"]["pit"][blocks["all"]["parties"].index("GHOST")]
    assert pit == 1.0, (
        f"the outcome-admitted column has PIT {pit:.3f} rather than exactly "
        f"1.0. It is the extreme value the population can take and five real "
        f"columns sit on it; if it no longer does, the mechanism that makes "
        f"`all` non-neutral has changed and the labelling must be rechecked.")

    label = C._POP_LABEL["all"]
    assert "outcome" in label.lower(), (
        f"`all` is labelled {label!r}, which does not tell the reader that some "
        f"of its columns are there because the party WON. A population "
        f"described as neutral gets quoted as the honest test; this one is a "
        f"mixture and `claimed` is the honest test.")


def test_the_vote_bands_and_the_calibration_bands_are_the_same_partition():
    """Two instruments, one ballot. They must be split on the same rule.

    The whole force of the finding was that the signed vote bands (+32.50pp at
    ranks 1-3, −37.34pp at 4-12) and the per-band PIT (0.431 / 0.750 on nine
    city-years) are the SAME statement measured twice. **On sixteen they are no
    longer**: the seat PIT at ranks 1-3 is 0.510 and does not corroborate the
    vote band there, though it has little power to see 0.26pp per party per
    city-year, so it does not refute it either (MODEL-LOG §1.146). The two
    instruments still must be split on the same rule, which is what this test
    asserts and is unaffected. That
    only holds if "ranks 1-3" means the same parties in both tables — so both
    go through ``rank_band_of`` and this test asserts they agree party by party.
    """
    actual_pr = {"ANC": 0.3322, "DA": 0.2545, "ASA": 0.1812, "EFF": 0.1011,
                 "PA": 0.0296, "IFP": 0.0236, "VFPLUS": 0.0133,
                 "ACDP": 0.0103, "ALJAMAAH": 0.0083, "AIC": 0.0069,
                 "AHC": 0.0043, "GOOD": 0.0033, "SMALL": 0.0011}
    membership = C.rank_band_of(actual_pr)
    assert membership["ANC"] == membership["DA"] == membership["ASA"] == "1-3"
    assert membership["EFF"] == membership["GOOD"] == "4-12"
    assert membership["SMALL"] == "13+"

    run = _Run({p: s for p, s in actual_pr.items()})
    bands = C.rank_bands(run, actual_pr, {})
    for label in ("1-3", "4-12", "13+"):
        expected = sum(1 for b in membership.values() if b == label)
        assert bands[label]["n"] == expected, (
            f"rank_bands counts {bands[label]['n']} parties in band {label} and "
            f"rank_band_of {expected}. The vote table and the calibration table "
            f"would then be splitting the ballot differently while using the "
            f"same band names, which is worse than not splitting it at all.")

    seat_draws = [{p: 1 for p in actual_pr} for _ in range(20)]
    blocks = C.calibration_columns(seat_draws, {p: 1 for p in actual_pr}, None,
                                   seed=1, actual_pr=actual_pr)
    for party, label in zip(blocks["all"]["parties"], blocks["all"]["band"]):
        assert label == membership[party], (
            f"{party} is band {label} in the calibration block and "
            f"{membership[party]} in rank_band_of")


# ---------------------------------------------------------------------------
# CLASS 8, YET AGAIN — a WIDTH verdict taken from a statistic that measures LEVEL
#
# Twice in two days this repository read a width fault off a coverage number.
# First "roughly the right width, do not widen"; then, from the 50% column
# alone, "ranks 4-12 are too narrow, widen them" — into ITERATING.md rule 8.
# Both wrong, in opposite directions, because coverage moves with the level as
# well as with the width and neither reading looked at more than one level.
#
# The fixtures below are the discriminating ones. A forecast whose width is
# EXACTLY right and whose truth is purely shifted loses coverage at every level;
# a forecast that is too wide gains it at 80 and 90 while still losing it at 50.
# The model reads low at 50 and HIGH at 80 and 90, which only the second can do.
# ---------------------------------------------------------------------------

def _shift_scale_results(seed, n_city_years, width_mult, shift, lam=4.0,
                         per_band=9, draws=400):
    """City-years whose ranks 4-12 have a KNOWN width and a KNOWN level error.

    ``width_mult`` rescales the forecast about its own mean without touching the
    truth, so 1.0 is a perfectly dispersed forecast and 1.6 is one whose
    intervals are 1.6x too wide. ``shift`` moves the truth and nothing else.
    Width and level are therefore controlled independently, which is the whole
    point: every statistic in this report has to be asked whether it responds to
    one, the other, or both.

    Three big parties are carried so that ranks 1-3 exist and the nine small
    ones land in the 4-12 band under ``rank_band_of``, exactly as on the real
    ballot.
    """
    rng = np.random.default_rng(seed)
    results = []
    for k in range(n_city_years):
        small = [f"s{k}_{j}" for j in range(per_band)]
        big = [f"B{k}_{j}" for j in range(3)]
        seat_draws = [{} for _ in range(draws)]
        actual = {}
        for party in small:
            raw = rng.poisson(lam, size=draws).astype(float)
            column = np.clip(np.round(lam + width_mult * (raw - lam)), 0,
                             None).astype(int)
            for d, value in zip(seat_draws, column):
                d[party] = int(value)
            actual[party] = max(int(round(rng.poisson(lam) + shift)), 0)
        for party in big:
            column = rng.poisson(60, size=draws)
            for d, value in zip(seat_draws, column):
                d[party] = int(value)
            actual[party] = int(rng.poisson(60))
        parties = big + small
        actual_pr = {p: 1.0 - 0.01 * i for i, p in enumerate(parties)}
        results.append({
            "city": f"Width{k}", "year": "2021",
            "calibration": C.calibration_columns(seat_draws, actual, None,
                                                 seed=70_000 + k,
                                                 actual_pr=actual_pr),
        })
    return results


_WIDTH_KEYS = ("pit_dispersion", "dispersion", "z_bias", "pit_var")


def _band(results, band="4-12", pop="claimed"):
    """The pooled band block, with the width statistics asserted present.

    Asserted here rather than left to a ``KeyError`` at the point of use: a
    missing statistic is the defect these tests exist for, and "KeyError:
    'dispersion'" does not tell the next reader that the report has no
    level-free width statistic and will therefore answer the width question
    from a coverage column again.
    """
    blk = C.pooled_calibration(results)[pop]["by_band"][band]
    missing = [k for k in _WIDTH_KEYS if k not in blk]
    assert not missing, (
        f"pooled_by_band reports no {', '.join(missing)} for ranks {band}. "
        f"Width and level are different faults and coverage measures both at "
        f"once: reading it at a single nominal level gave this project two "
        f"OPPOSITE wrong answers about ranks 4-12 in two days (MODEL-LOG "
        f"§1.34, §1.36, §1.39). The width verdict needs a statistic with the "
        f"level divided out.")
    return blk


def _at(block, key, level):
    return [r for r in block[key] if r["level"] == level][0]["empirical"]


def test_pit_variance_is_not_a_width_statistic():
    """"Variance is shift-invariant, so it is a clean dispersion statistic." No.

    This was proposed on this project as the fix for the coverage confound, and
    it has the same defect one step along. A PIT lives on ``[0, 1]``. Push the
    forecast off centre and its mass piles against an endpoint, and the variance
    falls whatever the width is — so a pure LEVEL error reads as
    under-dispersion, which is exactly the wrong diagnosis with exactly the
    wrong remedy.

    The fixture is a forecast of perfect width whose truth is shifted +2 seats.
    Its PIT variance must come out far below the nominal ``1/12`` while the
    level-free statistics still say the width is right.
    """
    right = _band(_shift_scale_results(4242, 12, width_mult=1.0, shift=2.0))
    nominal = 1.0 / 12.0

    assert right["pit_var"] < 0.75 * nominal, (
        f"the fixture is meant to reproduce the trap and did not: PIT variance "
        f"{right['pit_var']:.4f} against a nominal {nominal:.4f} on a forecast "
        f"of exactly correct width shifted +2 seats. Fix the fixture, not the "
        f"assertion — the point is a case where the variance says 'too narrow' "
        f"and the width is right.")

    assert abs(right["dispersion"] - 1.0) < 0.20, (
        f"the exact level-free dispersion reads {right['dispersion']:.3f} on a "
        f"forecast whose width is right by construction. It is the statistic "
        f"the width verdict now rests on; if it cannot pass this null, nothing "
        f"downstream of it can be quoted.")
    assert abs(right["pit_dispersion"] - 1.0) < 0.20, (
        f"the probit-SD reads {right['pit_dispersion']:.3f} on a correct-width "
        f"forecast shifted +2 seats. It is the fallback for artefacts that "
        f"carry only a PIT, and a fallback that fails the null is worse than "
        f"none.")

    # And it must still SEE a real width fault, or it is merely insensitive.
    wide = _band(_shift_scale_results(4242, 12, width_mult=1.6, shift=2.0))
    assert wide["dispersion"] < 0.85 * right["dispersion"], (
        f"a forecast widened by 1.6x reads {wide['dispersion']:.3f} against "
        f"{right['dispersion']:.3f} for the correct one. The statistic is "
        f"level-free and also fault-free, which makes it decoration.")
    assert wide["pit_dispersion"] < 0.85 * right["pit_dispersion"], (
        f"probit-SD {wide['pit_dispersion']:.3f} against "
        f"{right['pit_dispersion']:.3f}: it does not respond to a 1.6x "
        f"widening")


def test_coverage_at_one_level_cannot_tell_too_wide_from_merely_shifted():
    """The mistake itself, as a fixture: two forecasts, same 50%, opposite width.

    Both are shifted. One has exactly the right width; the other is 1.6x too
    wide. Their 50% coverages are close, because at the 50% level the shift
    dominates — **which is why reading that column alone got the answer wrong
    twice, in opposite directions.** What separates them is the 80% and the 90%,
    where excess width pushes coverage ABOVE nominal and correct width does not,
    and the level-free dispersion statistic, which separates them outright.

    The model's own ranks 4-12 read 32/89/96 against a nominal 50/80/90: down at
    50 and up at 80 and 90. Only the too-wide arm of this fixture does that.
    """
    right = _band(_shift_scale_results(909, 14, width_mult=1.0, shift=2.0))
    wide = _band(_shift_scale_results(909, 14, width_mult=1.6, shift=3.0))

    for label, blk in (("correct width", right), ("1.6x too wide", wide)):
        assert _at(blk, "pit_coverage", 0.5) < 0.5, (
            f"{label}: 50% PIT coverage {_at(blk, 'pit_coverage', 0.5):.3f}. "
            f"Both arms are shifted and both must lose the middle of their own "
            f"interval, or the fixture does not reproduce the confound.")

    # THE TRAP: the 50% column does not separate them.
    gap50 = abs(_at(right, "pit_coverage", 0.5) - _at(wide, "pit_coverage", 0.5))
    assert gap50 < 0.20, (
        f"the two arms differ by {gap50:.3f} at the 50% level, so this fixture "
        f"no longer demonstrates that the 50% column is uninformative about "
        f"width. Rebuild it rather than relaxing the claim — the claim is the "
        f"reason rule 8 was rewritten.")

    # WHAT ACTUALLY SEPARATES THEM, first: the upper levels.
    for level in (0.8, 0.9):
        assert _at(right, "pit_coverage", level) < level + 0.02, (
            f"a forecast of exactly correct width, shifted, covers "
            f"{_at(right, 'pit_coverage', level):.3f} at a nominal {level:.0%}. "
            f"A shift can only REMOVE coverage; if this arm over-covers, the "
            f"inference 'over-covering at 80 and 90 implies excess width' does "
            f"not hold and rule 8 must be rewritten again.")
        assert _at(wide, "pit_coverage", level) > _at(right, "pit_coverage", level), (
            f"at the {level:.0%} level the too-wide arm covers "
            f"{_at(wide, 'pit_coverage', level):.3f} and the correct-width arm "
            f"{_at(right, 'pit_coverage', level):.3f}. Excess width must lift "
            f"the upper levels or there is no statistic here at all.")

    # And second, decisively: the level-free dispersion.
    assert wide["dispersion"] < 0.85 < right["dispersion"], (
        f"level-free dispersion {wide['dispersion']:.3f} (too wide) against "
        f"{right['dispersion']:.3f} (correct). This is the column the width "
        f"verdict is taken from and it must separate the two cases cleanly, "
        f"because the 50% coverage does not.")


def test_the_report_prints_a_level_free_width_statistic():
    """Computed and not printed is not computed. Third time this file says so.

    `rank_bands` returned the absolute band error before the report printed it;
    the pooled PIT was computed before it was split. Both were acted on wrongly
    for months because the published table did not carry the number. The width
    statistic must therefore appear in the rendered report, and be found there
    by its VALUE rather than by a heading.
    """
    results = _shift_scale_results(555, 10, width_mult=1.6, shift=2.0)
    text = C.render_calibration(results)
    blk = _band(results)

    for key in ("pit_dispersion", "dispersion"):
        value = blk[key]
        assert value == value, f"{key} is nan on a fixture built to exercise it"
        assert f"{value:.3f}" in text, (
            f"the report does not print {key} ({value:.3f}). It is the only "
            f"statistic here that separates width from level, and without it "
            f"the width question gets answered from a coverage column again.")

    assert f"{blk['z_bias']:+.3f}" in text, (
        f"the standardised bias ({blk['z_bias']:+.3f}) is not printed. It is "
        f"the LEVEL half of the same decomposition and it is what keeps the "
        f"dispersion column from being read as one.")

    assert "1/12" in text and "not" in text.lower(), (
        "the report does not warn about PIT variance against 1/12. It was "
        "proposed as the clean width statistic, it is not shift-invariant, and "
        "the only defence against it being rediscovered is that the report says "
        "so where it prints it.")


def test_coverage_rows_carry_an_interval():
    """A bare coverage figure is not quotable, and every conclusion used one.

    The whole width argument turned on 27% vs 50% at ranks 4-12 — a difference
    of three discordant columns out of 28, one-sided McNemar p = 0.125. The mean
    PIT had a cluster-bootstrap CI from the day it was added; the coverage rows
    beside it had nothing, and were read as though they had.
    """
    results = _shift_scale_results(77, 9, width_mult=1.0, shift=1.0)
    blk = C.pooled_calibration(results)["claimed"]["by_band"]["4-12"]

    for key in ("coverage", "pit_coverage"):
        for row in blk[key]:
            assert "ci" in row, (
                f"{key} at the {row['level']:.0%} level is reported as "
                f"{row['inside']}/{row['counted']} with no interval. On the "
                f"real data the numbers being argued over differ by two or "
                f"three columns.")
            lo, hi = row["ci"]
            assert lo == lo and lo <= row["empirical"] <= hi, (
                f"{key} at {row['level']:.0%}: point estimate "
                f"{row['empirical']:.3f} outside its own interval "
                f"[{lo:.3f}, {hi:.3f}]")
            assert hi - lo > 0.02, (
                f"{key} at {row['level']:.0%} has interval [{lo:.3f}, "
                f"{hi:.3f}] on {row['counted']} columns clustered in "
                f"{len(results)} city-years. That is too tight to have "
                f"resampled city-years, and a column bootstrap here would be "
                f"the same error the mean PIT's CI exists to avoid.")

    text = C.render_calibration(results)
    row = [r for r in blk["pit_coverage"] if r["level"] == 0.5][0]
    lo, hi = row["ci"]
    assert f"[{100 * lo:.0f}–{100 * hi:.0f}]" in text, (
        f"the rendered report prints the 50% PIT coverage without its interval "
        f"[{100 * lo:.0f}–{100 * hi:.0f}]. That column is the one two reviews "
        f"and this project drew a width conclusion from.")


# ---------------------------------------------------------------------------
# CLASS 8 — the reference artefact nothing could diff
# ---------------------------------------------------------------------------

# The rows this test checks, and NOTHING ELSE. Named here rather than discovered,
# because a test that parses every document for every figure is a research
# project and would be turned off the first time it was noisy. These are the
# figures that steer the next iteration: they are what rule 8 tells a reader to
# act on. Everything else in the documents is unguarded and that is a known,
# stated limit — see the docstring below.
_CHECKED_TABLE = "ITERATING.md"
_CALIB_ROWS = ("ranks 1-3", "ranks 4-12")
_VOTE_ROWS = ("ranks 1-3", "ranks 4-12", "ranks 13+")
# Checked with the bands because rule 8's claim that the level gap is a ZERO-SUM
# transfer is only true once the phantom mass is counted: the three bands alone
# sum to a negative number, and the missing points are exactly this row.
_PHANTOM_ROW = "phantom (parties that did not stand)"


def _artefact():
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    # Through `load_history`, which REFUSES a scoreboard that cannot say what
    # produced it. Returns (manifest, records); every assertion below is about
    # the records and is unchanged.
    import compare_history as ch
    return ch.load_history(path)[1]


def _documented_rows():
    """The marked tables in ITERATING.md, as ``{label: [cells]}`` per shape."""
    text = (ROOT / _CHECKED_TABLE).read_text()
    marker = "CHECKED-AGAINST-ARTEFACT"
    assert marker in text, (
        f"{_CHECKED_TABLE} no longer carries the {marker} marker. The marker is "
        f"how a reader knows which figures are guarded; a guarded table that "
        f"does not say so gets copied into an unguarded one.")
    calib, votes = {}, {}
    for line in text[text.index(marker):].splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        label = cells[0]
        if label in _CALIB_ROWS and len(cells) == 7:
            calib[label] = cells[1:]
        elif label in (*_VOTE_ROWS, _PHANTOM_ROW) and len(cells) == 3:
            votes[label] = cells[1:]
    return calib, votes


# §A38's citations, and the comparison that adjudicates them. FUNCTIONS, so the
# constructed-violation test below pushes its input through the SAME code the
# live test runs — the pattern CLAUDE.md §4 asks for, and the reason the register
# guard's own detector is a function rather than an inline comprehension.
_A38_CITATION = re.compile(
    r"PR (median|mean|actual)\s+`votes\[(\d+)\]`\s*=\s*([\d.]+)%")

# Four decimals, as the entry writes them: a rounding that changes a quoted
# digit is the defect, so the tolerance must be tighter than one.
_A38_TOLERANCE = 0.0001


def _a38_citations(text: str) -> dict[str, tuple[int, float]]:
    """statistic -> (position in the `votes` row, percentage as written)."""
    return {m.group(1): (int(m.group(2)), float(m.group(3)))
            for m in _A38_CITATION.finditer(text)}


def _a38_drift(quoted: dict[str, float], actual: dict[str, float]) -> list[str]:
    """The statistics whose written value has left the artefact's."""
    return [f"{k}: JUDGEMENT-CALLS says {quoted[k]}%, artefact says "
            f"{actual[k]:.4f}%" for k in sorted(actual)
            if abs(quoted[k] - actual[k]) > _A38_TOLERANCE]


def test_the_standing_refusals_figures_match_the_artefact():
    """A figure typed into JUDGEMENT-CALLS prose, held against `history.json`.

    ⛔ **THE EXISTING FIGURES TEST DOES NOT COVER THIS FILE.** Its own docstring
    scopes it to ITERATING.md's two marked tables and excludes prose — a
    deliberate and correct limit, because a test that parsed every number in
    every document would be unmaintainable. The consequence is that a figure in
    a JUDGEMENT-CALLS entry has no guard at all, and on 2026-09-12 §A38 quoted
    the PA's forecast share as "0.09%" with a "33x" miss derived from it. The
    artefact says 0.0969% at the mean — which ROUNDS TO 0.10% — and the true
    ratio is 30x. Both halves of `CLAUDE.md` §2's "never type a model figure
    into prose", inside a rule about discipline.

    So the entry now NAMES its source and its three values, and this holds them
    to it. The pattern generalises: quote the artefact, name the field, and let
    a test own the number.

    ⚠️ **AND IT MUST NAME A FIELD THAT EXISTS.** The first version of the entry
    cited the three numbers as pr_median / pr_mean / pr_actual in backticks, as
    though `history.json` keyed them. It does not: `vote_table` returns unnamed
    tuples and the record stores bare lists, so two of those three names were in
    no module in this repository and the third collided with an unrelated key in
    `montecarlo.py`. `test_every_symbol_the_register_names_exists` failed on the
    two — the register-to-code direction doing exactly its job — and the
    collision is the reminder that a name-level check cannot tell a field from
    its homonym. The entry now cites the POSITION, which the artefact has, and
    this guard reads the artefact AT THE POSITION THE DOCUMENT NAMES, so a
    renumbered citation fails on the value rather than passing on the name.
    """
    text = (ROOT / "JUDGEMENT-CALLS.md").read_text(encoding="utf-8")
    quoted = _a38_citations(text)

    # (1) IT LOOKED. Three statistics, each with a position, or the parse has
    # gone stale. `assert not drift` below is vacuous on an empty parse.
    assert set(quoted) == {"median", "mean", "actual"}, (
        f"parsed {sorted(quoted)} out of JUDGEMENT-CALLS.md; expected the three "
        f"PA statistics §A38 cites. If the entry was reworded, this guard is "
        f"checking nothing and must be repointed, not deleted.")

    # (0) THE RIGHT SET. Three DISTINCT positions in the row `vote_table`
    # writes — `(party, pr_median, pr_mean, pr_actual, ward_*)`. A document that
    # cited one position three times would otherwise satisfy everything below.
    sites = {k: v[0] for k, v in quoted.items()}
    assert sorted(sites.values()) == [1, 2, 3], (
        f"§A38 cites positions {sites} of the `votes` row; `vote_table` puts "
        f"the PR median, mean and actual at 1, 2 and 3. Either the entry is "
        f"wrong or `vote_table`'s tuple changed, and the second one moves every "
        f"reader of this artefact.")

    results = _artefact()
    row = [r for r in results
           if r.get("slug") == "joburg" and str(r.get("year")) == "2021"]
    assert len(row) == 1, "joburg 2021 is not in the artefact exactly once"
    votes = {v[0]: v for v in row[0]["votes"]}
    assert "PA" in votes, "the PA has left the joburg 2021 vote table"
    pa = votes["PA"]
    # Read where the DOCUMENT points, not where this test would like to look.
    actual = {k: pa[i] * 100 for k, i in sites.items()}
    quoted = {k: v[1] for k, v in quoted.items()}

    # (2) THE CLAIM.
    drift = _a38_drift(quoted, actual)
    assert not drift, (
        "§A38's PA figures no longer match the committed artefact:\n  "
        + "\n  ".join(drift)
        + "\n  Paste the artefact's values in, and RECOMPUTE the multiplier "
          "from them rather than from the rounded figure — that is the error "
          "this guard was written for.")

    # (3) AND THE MULTIPLIER IS DERIVED FROM THEM, not from a rounded value.
    ratio = actual["actual"] / actual["mean"]
    # The document uses the multiplication sign, not the letter x. My first
    # version of this regex looked for "x" and silently matched nothing, which
    # is the guard-finds-nothing failure this whole file is about.
    stated = re.search(r"a (\d+)\u00d7 level miss", text)
    assert stated, "§A38 no longer states the level-miss multiple"
    assert abs(int(stated.group(1)) - round(ratio)) <= 1, (
        f"§A38 states a {stated.group(1)}x level miss; the artefact gives "
        f"{actual['actual']:.4f} / {actual['mean']:.4f} = {ratio:.1f}x. "
        f"A ratio computed from a ROUNDED figure rather than from the data is "
        f"exactly how 33x was written for a 30x miss.")


def test_the_A38_figure_detector_can_see_a_drift_and_a_renumbered_citation():
    """(2) IT CAN SEE, on (3) A CONSTRUCTED input.

    The guard above reports on the document as it happens to be, and the
    document is currently correct — so on its own it has never demonstrated it
    can catch anything. Its premise is an observed passing state, which is the
    class `CLAUDE.md` §4 says expires silently.

    Three constructed documents go through `_a38_citations` and `_a38_drift`,
    the same two functions the live test uses, against a constructed vote row.
    Each carries one of the three ways this entry has gone wrong or could:
    a value that drifted from the artefact (the 0.09%-for-0.0969% defect that
    caused this guard to be written), a citation renumbered to a position
    holding a different statistic, and a rewording that leaves the parse
    matching nothing at all — the guard-finds-nothing failure this file's own
    `×`-versus-`x` comment records.
    """
    # A constructed row in `vote_table`'s shape: party, then PR median / mean /
    # actual, then the three ward columns. Not the PA's real numbers — a
    # detector proved against observed values proves nothing about the detector.
    row = ["ZZ", 0.0100, 0.0200, 0.5000, 0.0, 0.0, 0.0]
    good = ("PR median `votes[1]` = 1.0000%, PR mean `votes[2]` = 2.0000%, "
            "PR actual `votes[3]` = 50.0000%")

    # The control: the detector must PASS the correct document, or every
    # failure below is the detector being broken rather than the defect being
    # caught — a positive control that only ever fails is a stuck needle.
    cited = _a38_citations(good)
    assert set(cited) == {"median", "mean", "actual"}, sorted(cited)
    sites = {k: v[0] for k, v in cited.items()}
    assert sorted(sites.values()) == [1, 2, 3]
    clean = _a38_drift({k: v[1] for k, v in cited.items()},
                       {k: row[i] * 100 for k, i in sites.items()})
    assert not clean, f"the detector flagged a correct document: {clean}"

    # (a) A DRIFTED VALUE. 2.0000% written as 1.9%, the shape of the original
    # defect: a truncation that still looks like the number.
    drifted = _a38_citations(good.replace("`votes[2]` = 2.0000%",
                                          "`votes[2]` = 1.9%"))
    seen = _a38_drift({k: v[1] for k, v in drifted.items()},
                      {k: row[v[0]] * 100 for k, v in drifted.items()})
    assert [s.split(":")[0] for s in seen] == ["mean"], (
        f"a value 0.1pp from the artefact was not reported: {seen}. The "
        f"tolerance is {_A38_TOLERANCE}, and this is the defect the guard "
        f"exists for.")

    # (b) A RENUMBERED CITATION. The mean's value kept, its position moved to
    # the median's — the failure a name-based citation could not express and a
    # positional one can. It must be caught by the position check AND, because
    # the live guard reads where the document points, by the value comparison.
    moved = _a38_citations(good.replace("PR mean `votes[2]`", "PR mean `votes[1]`"))
    assert sorted(v[0] for v in moved.values()) == [1, 1, 3], (
        f"the renumbered citation did not survive the parse: {moved}")
    seen = _a38_drift({k: v[1] for k, v in moved.items()},
                      {k: row[v[0]] * 100 for k, v in moved.items()})
    assert [s.split(":")[0] for s in seen] == ["mean"], (
        f"reading position 1 for the mean returned the median's 1.0000% "
        f"against a written 2.0000% and that was not reported: {seen}")

    # (c) A REWORDING. The parse returns nothing, and `assert not drift` is
    # vacuously true on nothing — which is why the live test asserts the key
    # set BEFORE it compares anything.
    assert not _a38_citations(
        good.replace("`votes[", "`vote_row[")), (
        "the citation regex still matched after the document was reworded, so "
        "it is not anchored on the form the entry actually uses")


def test_the_documented_figures_match_the_committed_artefact():
    """The guard that was missing, and the reason three reviews found the same rot.

    `data/processed/history.json` is quoted throughout this repository as "the
    committed artefact". **It was excluded by `.gitignore:5` (`data/**`) and had
    never been committed.** Every run overwrote it, so no diff could show it
    moving and no test could hold a document against it. The consequence was
    realised rather than theoretical: within one commit the record said ranks
    4-12 were n=26, mean PIT 0.750, coverage 46% while the file on disk said
    n=28, 0.757, 43%, and ranks 1-3 absolute was written as 71.12pp against an
    actual 69.59pp.

    So the artefact is now tracked and this test holds the load-bearing figures
    against it.

    **WHAT THIS COVERS:** the two marked tables in `ITERATING.md` rule 8 — the
    per-band n, mean PIT, PIT coverage at all three levels and the level-free
    probit-SD, and the nine-city-year signed and absolute vote error per band.
    Those are the figures rule 8 instructs the next iteration to act on.

    **WHAT IT DOES NOT COVER, and deliberately:** prose anywhere, `MODEL-LOG.md`
    (which is an append-only historical record and whose figures are correct AS
    OF their entry — rewriting them would destroy the record), the docstrings in
    `src/`, and any figure not in the marked tables. A test that parsed every
    document for every number would be unmaintainable and would be disabled the
    first week. The rule that covers the rest is the one in `CLAUDE.md`: the
    record changes in the same commit as the model.

    **When this fails after a legitimate re-run**, the artefact is right and the
    document is stale: paste the values from the failure message into the marked
    table and commit the artefact with them, in the same commit.
    """
    results = _artefact()
    calib_doc, votes_doc = _documented_rows()
    assert calib_doc and votes_doc, (
        "no marked rows parsed out of ITERATING.md. Either the tables were "
        "reshaped or the marker moved; a guard that silently checks nothing is "
        "worse than no guard.")

    bands = C.pooled_calibration(results)["claimed"]["by_band"]
    for label in _CALIB_ROWS:
        key = label.replace("ranks ", "")
        blk, cells = bands[key], calib_doc[label]
        pit_cov = {row["level"]: row["empirical"] for row in blk["pit_coverage"]}
        actual = [str(blk["n"]), f"{blk['mean_pit']:.3f}",
                  *(f"{100 * pit_cov[level]:.0f}%" for level in C.LEVELS),
                  f"{blk['pit_dispersion']:.3f}"]
        names = ("n", "mean PIT", "50% (PIT)", "80% (PIT)", "90% (PIT)",
                 "probit-SD")
        for name, said, is_ in zip(names, cells, actual):
            ok = (said == is_ if name == "n" else
                  abs(_number(said) - _number(is_))
                  <= (2.0 if said.endswith("%") else 0.012))
            assert ok, (
                f"ITERATING.md rule 8 says {label} {name} = {said}; "
                f"data/processed/history.json says {is_}.\n"
                f"The correct row is:  | {label} | " + " | ".join(actual)
                + " |\nA figure quoted from an artefact that disagrees with it "
                  "is how this repository has been wrong three times.")

    signed = {k: sum(r["bands"][k]["signed_pp"] for r in results)
              for k in C.BAND_LABELS}
    absolute = {k: sum(r["bands"][k]["abs_pp"] for r in results)
                for k in C.BAND_LABELS}
    for label in _VOTE_ROWS:
        key = label.replace("ranks ", "")
        said_signed, said_abs = votes_doc[label]
        for name, said, is_ in (("signed", said_signed, signed[key]),
                                ("absolute", said_abs, absolute[key])):
            assert abs(_number(said) - is_) <= 0.5, (
                f"ITERATING.md rule 8 says {label} {name} = {said}; the "
                f"artefact sums to {is_:+.2f}pp over "
                f"{len(results)} city-years.\nThe correct row is:  | {label} | "
                f"{signed[key]:+.2f}pp | {absolute[key]:.2f}pp |")

    # The zero-sum claim, asserted rather than asserted-about. Rule 8 says the
    # level gap between the bands is a TRANSFER, which is only true because
    # shares sum to one over the model's own universe. If the four rows stop
    # summing to zero, either the phantom figure is stale or the identity has
    # broken, and both make the paragraph above them false.
    phantom = sum((r["bands"].get("phantom") or {}).get("pp", 0.0)
                  for r in results)
    said_phantom = _number(votes_doc[_PHANTOM_ROW][0])
    assert abs(said_phantom - phantom) <= 0.5, (
        f"ITERATING.md rule 8 says phantom mass = {said_phantom:+.2f}pp; the "
        f"artefact gives {phantom:+.2f}pp.\nThe correct row is:  "
        f"| {_PHANTOM_ROW} | {phantom:+.2f}pp | — |")
    residual = sum(signed.values()) + phantom
    assert abs(residual) < 0.01, (
        f"the three signed bands and the phantom mass sum to {residual:+.4f}pp "
        f"rather than to zero. Rule 8 calls the level gap a ZERO-SUM transfer "
        f"and that sentence depends on this identity; if shares no longer sum "
        f"to one over the model's universe, the transfer reading is wrong.")


def test_the_scoreboard_artefact_is_tracked_by_git():
    """`.gitignore` excluded the very file every figure is attributed to.

    Checked against `.gitignore` itself rather than by shelling out to git, so
    it runs in a source tree without a `.git` directory. The negation must come
    AFTER the `data/**` line or it does nothing, which is the kind of detail
    that is silently wrong for months.
    """
    lines = [line.strip() for line in
             (ROOT / ".gitignore").read_text().splitlines()]
    try:
        blanket = lines.index("data/**")
    except ValueError:
        return          # the blanket exclusion is gone; nothing to un-ignore
    for target in ("data/processed/history.json", "data/processed/history.md"):
        rule = f"!{target}"
        assert rule in lines, (
            f"{target} is excluded by `data/**` and never re-included, so it "
            f"cannot be committed. Every calibration figure in this repository "
            f"is quoted as coming from the committed artefact; for months there "
            f"was no committed artefact, nothing could diff it, and "
            f"test_the_documented_figures_match_the_committed_artefact has "
            f"nothing to compare against.")
        assert lines.index(rule) > blanket, (
            f"`{rule}` appears before `data/**` in .gitignore, so the blanket "
            f"exclusion wins and the file is still ignored. Order matters here "
            f"and the failure is silent.")


def _number(cell: str) -> float:
    """The first signed decimal in a table cell, ``%`` and ``pp`` stripped."""
    match = re.search(r"[-+−]?\d+(?:\.\d+)?", cell.replace("−", "-"))
    assert match, f"no number in table cell {cell!r}"
    return float(match.group())


def test_the_claimed_population_moves_when_the_forecaster_widens():
    """CLASS 13 — A DENOMINATOR THAT MOVES WITH THE THING BEING MEASURED.

    ``claimed`` selects on the forecast, and :func:`score.score_seats` is right
    that this keeps PIT uniform under calibration. That argument is about ONE
    forecaster. A lever sweep is a comparison ACROSS forecasters, and the
    criterion admits a DIFFERENT SET OF COLUMNS for each of them: on the real
    nine city-years at 1500 draws the ``claimed`` set is 58, 67 and 81 columns
    at ``dirichlet_scale`` 0.5, 1.0 and 2.0, of which 30, 37 and 45 are ranks
    4-12. Both facts about the criterion are true; only the first was written
    down, and four MODEL-LOG sections were measured against the second.

    **NARROWING admits columns**, which is the direction that surprises: a
    higher ``dirichlet_scale`` is a higher concentration and a tighter draw, and
    a party whose mean sits above the claim threshold is then given a seat in
    nearly every draw instead of in some of them. Widening scatters draws back
    onto zero and the party drops out of its own scored population. So the
    criterion rewards confidence with a larger denominator.

    Asserted on two forecasters that differ ONLY in width, so any change in the
    column count is the criterion moving and nothing else.
    """
    rng = np.random.default_rng(11)
    parties = [f"P{j}" for j in range(30)]
    actual = {p: int(rng.poisson(3.0)) for p in parties}
    # same centre, two widths. The narrow one claims a column only where its
    # mean is comfortably above zero; the wide one claims far more.
    def forecast(spread):
        draws = []
        for _ in range(600):
            draws.append({p: int(max(0, rng.normal(1.2, spread)))
                          for p in parties})
        return draws

    narrow = C.calibration_columns(forecast(0.4), actual, None, seed=3)
    wide = C.calibration_columns(forecast(3.0), actual, None, seed=3)
    assert narrow["claimed"]["n"] > wide["claimed"]["n"], (
        f"two forecasters with the same centre and different widths were "
        f"scored on {narrow['claimed']['n']} (narrow) and "
        f"{wide['claimed']['n']} (wide) claimed columns. If those are ever "
        f"equal this test has stopped exercising the mechanism, not proved the "
        f"mechanism gone — widen the gap between the two spreads rather than "
        f"deleting the test.")
    assert narrow["seat_holders"]["n"] == wide["seat_holders"]["n"], (
        "`seat_holders` is outcome-selected and must not move between two "
        "forecasters scored against the same result; if it does, the fault is "
        "not the one this test is about")


def test_the_reference_population_is_fixed_and_keeps_the_worst_columns():
    """The fix for CLASS 13, and the reason it is worth a fourth population.

    ``reference`` is selected by :func:`compare_history.reference_universe` from
    inputs alone, so its membership cannot move when a lever moves — measured on
    the real panel it is 252 columns at every ``dirichlet_scale`` setting, and
    225 of those carry a defined ``z`` at every setting too.

    The second assertion is the one that matters, and it is a stronger statement
    than "the denominator moves": the ``claimed`` rule does not merely select a
    different set, **it selects away from the model's own worst failures.** A
    party the forecaster gives a seat in fewer than half its draws is exactly a
    party the forecaster is failing on, and it is excluded from the population
    that is supposed to be testing the forecaster. On the real panel the two
    largest standardised errors in ranks 4-12 — Cape Town's Cape Coloured
    Congress at z = +12.1 and Johannesburg's PA at +9.3 — are both outside
    ``claimed`` and inside ``reference``, and they are the difference between a
    band that reads 0.823 (too wide, narrow it) and one that reads 1.940 (far
    too narrow). See MODEL-LOG §1.56.
    """
    rng = np.random.default_rng(12)
    parties = [f"P{j}" for j in range(6)]
    seat_draws, actual = _poisson_forecast(rng, parties, 8.0, 8.0)
    # the surge: on the ballot, forecast almost nothing, wins a pile of seats
    for d in seat_draws:
        d["SURGE"] = 0 if rng.random() > 0.05 else 1
    actual["SURGE"] = 9
    actual_pr = {p: 1.0 - 0.01 * i
                 for i, p in enumerate(parties + ["SURGE"])}
    universe = sorted(actual)

    blocks = C.calibration_columns(seat_draws, actual, None, seed=1,
                                   actual_pr=actual_pr, reference=universe)
    assert blocks["reference"]["parties"] == universe, (
        "`reference` did not score the universe it was handed. It is the one "
        "population whose columns are an input, and scoring a subset of it "
        "reintroduces exactly the forecast-dependence it exists to remove")
    assert "SURGE" not in blocks["claimed"]["parties"], (
        "the forecaster claims a party it gives a seat in 5% of draws — then "
        "CLAIM_FRACTION is not doing what this test is about")
    assert "SURGE" in blocks["reference"]["parties"], (
        "`reference` dropped the one column the forecaster fails worst on. "
        "That is the defect, not the fix")

    # and the width statistic must actually see it
    z = blocks["reference"]["z"][universe.index("SURGE")]
    assert z is not None and z > 3.0, (
        f"the surge column carries z={z}, so the failure is in the population "
        f"but invisible to the width statistic — which is the same hiding "
        f"place one level down")

def _top2_null(n: int, reps: int = 20_000) -> dict:
    """What share of Σ(z−z̄)² the top two of `n` columns carry UNDER CALIBRATION.

    Not `2/n`. Under calibration `z` is standard normal, so the squared
    deviations are χ²₁ and heavy-tailed, and the largest two of `n` draws carry
    far more than their equal share — 9.1% at n=170, not 1.2%. Getting this
    wrong makes a concentration test pass on a calibrated band.

    Simulated rather than typed, with a fixed seed, so it re-derives itself at
    whatever `n` the panel happens to have and cannot go stale when the panel
    grows. That is the whole defect this replaced.
    """
    import numpy as np
    rng = np.random.default_rng(20260912)
    z = rng.standard_normal((reps, n))
    d2 = (z - z.mean(axis=1, keepdims=True)) ** 2
    share = np.sort(d2, axis=1)[:, -2:].sum(axis=1) / d2.sum(axis=1)
    return {"mean": float(share.mean()), "p99": float(np.percentile(share, 99))}


def test_a_width_never_travels_without_its_cycle_split_and_its_leverage():
    """Four fields that must accompany every band width. MODEL-LOG §1.134.

    **Each one exists because its absence produced a wrong published
    conclusion.** Pooling two cycles that disagree in sign gave `ITERATING.md`
    rule 8 a false claim to have replicated out of sample, and gave §1.131 a
    "the mid-ballot is 1.8x too narrow" that is two columns. The leverage share
    is one line and would have stopped both.
    """
    import compare_history as ch
    rows = ch.load_history(ROOT / "data/processed/history.json")[1]
    band = ch.pooled_by_band(rows, "reference")["4-12"]

    for field in ("by_cycle", "leverage", "by_p_any", "pit_saturated",
                  "probit_by_clip", "probit_quotable"):
        assert field in band, f"`{field}` is gone from the band report (§1.134)"

    cyc = band["by_cycle"]
    assert set(cyc) >= {"2016", "2021"}, sorted(cyc)
    # THE FINDING, as a structural assertion rather than a pinned number: the
    # cycles do not agree, so the pooled figure describes none of them.
    #
    # ⛔ THIS COMPARED 2016 AGAINST 2021 AND NOTHING ELSE, on a panel that had
    # only those two cycles. The artefact now carries 2011 as well, and 2011 is
    # the EXTREME — so the hard-coded pair measured the narrowest gap available
    # and reported the finding as gone (1.960 vs 1.155 is 1.70x) while the real
    # spread had grown to 4.33x. A two-cycle test on a three-cycle panel is the
    # scanned-the-wrong-set class (`CLAUDE.md` §4), and it failed in the
    # direction that retires a live finding.
    #
    # Measured 2026-09-12 over all 24 city-years: sd(z) is 0.452 at 2011, 1.155
    # at 2016 and 1.960 at 2021 — monotone, and the same shape `CLAUDE.md`
    # records for `k*` ("a 4x spread that no single number resolves").
    # BOTH CLAIMS, because they are different and the pair is the finding.
    # The ordered one is the second-order-election story §1.132 is about (the
    # later cycle is the turbulent one); the all-cycles one is the dispersion.
    # Asserting only the widest pair would stay green on 2011 alone if 2016 and
    # 2021 converged completely — which is the exact event rule 8 and the
    # HANDOVER's item 1 depend on, and it would be reported only in a failure
    # MESSAGE. This repository asserts the number, not the message.
    # `bool(nan)` is True, so a `.get(...)` truth test RETAINS a nan cycle and
    # DROPS one whose sd(z) is exactly 0.0 — which is the single case that
    # would most strongly confirm the finding. `_stats` returns nan for any
    # cycle with fewer than two scored columns.
    spread = {c: v for c in cyc
              if (v := cyc[c].get("sd_z")) is not None and v == v}
    assert len(spread) >= 2, sorted(cyc)
    lo_c, hi_c = min(spread, key=spread.get), max(spread, key=spread.get)
    lo, hi = spread[lo_c], spread[hi_c]

    # ⛔ THE ORDERED CLAIM IS ASSERTED AS MONOTONICITY, NOT AS `2021 > 3x2016`,
    # AND THE DIFFERENCE IS A MEASURED CHANGE, NOT A CONVENIENCE. That pair was
    # 3.5x on the nine-city-year panel and is **1.70x** on twenty-four (1.155
    # at 2016, 1.960 at 2021) — so the specific 3x claim between those two
    # cycles NO LONGER HOLDS and must not be re-asserted. What does hold, and
    # is the stronger structural statement, is that sd(z) rises monotonically
    # with the cycle: 0.452 -> 1.155 -> 1.960. That is directed, uses every
    # cycle, carries no tuned threshold, and breaks if ANY adjacent pair
    # converges or inverts — which is the event rule 8 and the HANDOVER's item
    # 1 depend on. §1.132's own reading is preserved; the pair figure it was
    # written against is not. MODEL-LOG entry filed 2026-09-12.
    ordered = [cyc[c]["sd_z"] for c in sorted(spread)]
    assert all(a < b for a, b in zip(ordered, ordered[1:])), (
        "ranks 4-12 sd(z) by cycle is "
        + ", ".join(f"{c} {spread[c]:.3f}" for c in sorted(spread))
        + " — no longer monotone in the cycle. §1.132 reads the later cycles "
          "as the turbulent ones; an inversion or a convergence between "
          "adjacent cycles changes that, and rule 8 and the HANDOVER's item 1 "
          "both need re-reading.")

    assert hi > 3 * lo, (
        "ranks 4-12 sd(z) by cycle is "
        + ", ".join(f"{c} {spread[c]:.3f}" for c in sorted(spread))
        + f" — widest ratio {hi / lo:.2f}x ({hi_c} over {lo_c}). If the cycles "
        f"have converged, §1.132's central finding — that the pooled width "
        f"describes NO cycle — has changed, and rule 8 and the HANDOVER's item "
        f"1 both need re-reading. Compare every cycle present: this assertion "
        f"named 2016 and 2021 until 2026-09-12 and missed that 2011 is the "
        f"extreme.")

    # ⛔ TWO WRONG ENCODINGS OF THIS, AND THE SECOND WAS MINE.
    #
    # It was `top2 > 0.5`, which is a function of the panel's SIZE and not of
    # the concentration it claims to measure: the same two columns carry 69.5%
    # on nine city-years and 48.5% on twenty-four purely because there are more
    # columns to share the total. That bare floor retired a finding that had
    # not changed.
    #
    # I replaced it with `top2 > 10 * (2/n)` on 2026-09-12, reasoning that two
    # columns "with no concentration" carry 2/n. THAT IS WRONG. `top2` is a
    # share of Σ(z−z̄)², and under calibration those squared deviations are
    # χ²₁ — heavy-tailed — so the top two of n carry FAR more than 2/n.
    # Simulated (200k replicates): at n=170 the null mean is 9.1%, not 1.2%.
    # So "48.5% is 41x expectation" overstated it by ~8x (it is 5.3x), and
    # worse, the bar 10*(2/n) = 11.8% sits BELOW the null's own 95th percentile
    # of 12.4% — a perfectly calibrated band cleared my test 7.9% of the time.
    # A threshold picked after seeing the number, on a wrong benchmark, that
    # barely discriminates: exactly the ratchet `CLAUDE.md` §4 warns about,
    # arrived at from the right diagnosis.
    #
    # So score it against ITS OWN NULL at the observed n. Scale-free,
    # self-calibrating, and the simulation doubles as the positive control.
    _lev, _nz = band["leverage"]["top2"], band["n_z"]
    _null = _top2_null(_nz)
    assert _lev > _null["p99"], (
        f"the two largest columns carry {_lev:.1%} of ranks 4-12's squared "
        f"deviation across {_nz} scored columns. Under calibration the top two "
        f"of {_nz} χ²₁ deviations carry {_null['mean']:.1%} on average and "
        f"{_null['p99']:.1%} at the 99th percentile, so this is "
        f"{_lev / _null['mean']:.1f}x the null mean. Below the 99th percentile "
        f"the 'two columns are the finding' reading is not distinguishable "
        f"from a calibrated band.\n"
        f"  ⚠️ §1.131 measured 69.5% at n=9 against a null mean of 62.4% — "
        f"P(null ≥ 0.695) = 0.27. That finding was NOT significant on the "
        f"panel it was found on; it became real only at n=170.")

    # A SATURATED BAND IS UNQUOTABLE, and it is a field so a consumer must look.
    assert band["pit_saturated"] > 0 and band["probit_quotable"] is False, (
        "reference ranks 4-12 carries saturated PITs and must be marked "
        "unquotable; `_probit`'s clip moves it by 17% across 1e-4..1e-6")
    clips = band["probit_by_clip"]
    assert max(clips.values()) - min(clips.values()) > 0.05, (
        f"probit-SD is now clip-insensitive at {clips}; if that is real, "
        f"`_probit`'s docstring and §1.132 both need rewriting")

    # And ranks 1-3, which the ITERATING table pins, is the SAME columns in both
    # populations -- so a divergence there means the split logic is broken.
    a = ch.pooled_by_band(rows, "reference")["1-3"]
    b = ch.pooled_by_band(rows, "claimed")["1-3"]
    assert a["n_z"] == b["n_z"] and abs(a["dispersion"] - b["dispersion"]) < 1e-9


def test_the_arrival_channel_has_a_score_that_cannot_be_handed_the_answer():
    """`arrival_group_score` must not depend on WHICH arrival it is told about.

    `entrant_actual_for` picks `max(newcomers, key=seats)` — the most favourable
    assignment available, chosen with the outcome in hand — and that is what
    rejected the group arrival mechanism at CRPS 85.9 -> 109.9. A label-free
    score is the referee that comparison needed. MODEL-LOG §1.133.
    """
    import backtest

    idx = {"ANC": 0, "DA": 1, "NEWCO": 2, "TINYCO": 3}
    base = {"ANC": 0.5, "DA": 0.4}
    draws = np.array([[0.50, 0.40, 0.08, 0.02], [0.50, 0.40, 0.04, 0.06],
                      [0.50, 0.40, 0.02, 0.08], [0.50, 0.40, 0.10, 0.00]])
    # ⛔ list-of-dicts, the type a real `ModelRun` carries. This fixture was a
    # dense 2-D array until 2026-08-29, which is why this test passed against a
    # function that could not run on real input at all (MODEL-LOG §1.136).
    seatd = [{"ANC": 100, "DA": 80, "NEWCO": 16, "TINYCO": 4},
             {"ANC": 100, "DA": 80, "NEWCO": 8, "TINYCO": 12},
             {"ANC": 100, "DA": 80, "NEWCO": 4, "TINYCO": 16},
             {"ANC": 100, "DA": 80, "NEWCO": 20, "TINYCO": 0}]

    # THE PROPERTY: two outcomes with the SAME arrival totals but the mass split
    # differently between the two newcomers must score identically. The
    # relabelling score cannot do this -- it would follow whichever is larger.
    one = backtest.arrival_group_score(
        draws, seatd, idx, {"NEWCO": 0.10, "TINYCO": 0.02},
        {"NEWCO": 20, "TINYCO": 4}, base)
    two = backtest.arrival_group_score(
        draws, seatd, idx, {"NEWCO": 0.02, "TINYCO": 0.10},
        {"NEWCO": 4, "TINYCO": 20}, base)
    for k in ("actual_mass", "actual_seats", "mass_pit", "seats_pit",
              "mass_err", "seats_err"):
        assert abs(one[k] - two[k]) < 1e-12, (
            f"`{k}` moved when the SAME total arrival mass was split "
            f"differently between newcomers ({one[k]} vs {two[k]}). The score "
            f"is label-dependent, which is the whole defect it exists to fix.")

    # A party WITH a baseline is never an arrival, however well it did.
    assert one["n_arrived"] == 2 and one["n_columns"] == 2

    # No arrival at all is a legitimate outcome, not a missing measurement.
    none = backtest.arrival_group_score(draws, seatd, {"ANC": 0, "DA": 1},
                                        {}, {}, base)
    assert none["n_arrived"] == 0 and none["mass_pit"] != none["mass_pit"]
    # ⛔ The no-columns branch must carry the SAME KEYS as the live one, or a
    # consumer reading `mass_err` KeyErrors on exactly the city-years where
    # nothing arrived. It omitted all four error/median keys until 2026-08-29.
    for k in ("mass_err", "seats_err", "mass_median", "seats_median"):
        assert k in none, f"`{k}` missing from the no-arrival branch"


def test_arrival_score_runs_on_the_types_PRODUCTION_actually_builds():
    """⛔ THE FIXTURE ABOVE IS THE WRONG TYPE, AND THAT HID A TOTAL FAILURE.

    `seat_draws` is ``list[dict[str, int]]`` on a real `ModelRun`
    (`montecarlo.py`), **not** the dense ``(draws, parties)`` array
    `pr_share_draws` is. `arrival_group_score` indexed both as arrays, so on
    real input it raised ``IndexError: too many indices`` for every city-year;
    `compare_history` caught it per city-year and printed ``nothing runnable``.
    The referee had never produced a single number, and the suite was green —
    because the only test handed it a 2-D fixture production never builds.
    MODEL-LOG §1.136. So this test uses the PRODUCTION types, deliberately.
    """
    import backtest

    idx = {"ANC": 0, "DA": 1, "NEWCO": 2, "TINYCO": 3}
    base = {"ANC": 0.5, "DA": 0.4}
    draws = np.array([[0.50, 0.40, 0.08, 0.02], [0.50, 0.40, 0.04, 0.06],
                      [0.50, 0.40, 0.02, 0.08], [0.50, 0.40, 0.10, 0.00]])
    # A list of {party: seats} dicts, sparse — zero-seat parties are ABSENT,
    # which is how `montecarlo` builds them.
    seatd = [{"ANC": 100, "DA": 80, "NEWCO": 16, "TINYCO": 4},
             {"ANC": 100, "DA": 80, "NEWCO": 8, "TINYCO": 12},
             {"ANC": 100, "DA": 80, "NEWCO": 4, "TINYCO": 16},
             {"ANC": 100, "DA": 80, "NEWCO": 20}]

    got = backtest.arrival_group_score(
        draws, seatd, idx, {"NEWCO": 0.10, "TINYCO": 0.02},
        {"NEWCO": 20, "TINYCO": 4}, base)
    # Drawn arrival seat totals are 20, 20, 20, 20 -> mean 20, realised 24.
    assert got["seats_mean"] == 20.0, got["seats_mean"]
    assert got["seats_err"] == 4.0, got["seats_err"]
    assert got["n_columns"] == 2

    # ⛔ A realised total above EVERY draw must be flagged. Mid-ranking does not
    # remove saturation — `seats_pit` is exactly 1.0 here — and that case is
    # ActionSA-shaped, which is the one this score exists to see.
    assert got["seats_pit"] == 1.0
    assert got["seats_outside_support"] is True


def test_the_arrival_score_is_unchanged_by_the_relabel():
    """The comment at the call site PROMISED this and no assertion existed.

    `compare_history` computes the arrival score AFTER `relabel_run`, on the
    stated grounds that "the relabel renames a column and moves no mass, so the
    group total is identical either way — and asserting that is how a future
    reader knows the label cannot reach this number." No such assertion was
    ever written. It is written here, and it is not free: `relabel_run` has a
    MERGE branch as well as a rename branch, and the merge does move mass
    between columns. MODEL-LOG §1.136.
    """
    import backtest
    from types import SimpleNamespace

    def _run():
        return SimpleNamespace(
            index={"ANC": 0, "DA": 1, "ENTRANT": 2},
            universe=["ANC", "DA", "ENTRANT"],
            pr_share_draws=np.array([[0.50, 0.40, 0.10],
                                     [0.55, 0.35, 0.10],
                                     [0.60, 0.36, 0.04]]),
            ward_share_draws=None, ward_winner_counts=None,
            seat_draws=[{"ANC": 100, "DA": 80, "ENTRANT": 20},
                        {"ANC": 110, "DA": 70, "ENTRANT": 20},
                        {"ANC": 120, "DA": 72, "ENTRANT": 8}],
            ward_win_sum={"ENTRANT": 3}, overhang_count={},
            notes={"ENTRANT": ""})

    base = {"ANC": 0.5, "DA": 0.4}
    shares, seats = {"NEWCO": 0.12}, {"NEWCO": 22}

    before = _run()
    a = backtest.arrival_group_score(before.pr_share_draws, before.seat_draws,
                                     before.index, shares, seats, base)
    after = backtest.relabel_run(_run(), "NEWCO")
    b = backtest.arrival_group_score(after.pr_share_draws, after.seat_draws,
                                     after.index, shares, seats, base)

    for k in ("actual_mass", "actual_seats", "mass_mean", "seats_mean",
              "mass_pit", "seats_pit", "mass_err", "seats_err"):
        assert abs(a[k] - b[k]) < 1e-12, (
            f"`{k}` moved across the relabel ({a[k]} vs {b[k]}). The call site "
            f"claims the label cannot reach this number; it just did.")


def test_the_relabel_ablation_actually_withholds_the_label():
    """⛔ A SWITCH THAT SILENTLY DID NOTHING WOULD PRICE THE LABEL AT ZERO.

    `JHB_SCORE_NO_RELABEL=1` exists to answer "what is the free arrival label
    worth", and `ITERATING.md` now quotes 11.52 CRPS and 2.17 points of margin
    off it (§1.148). If the switch were inert — misspelled, read in the parent
    but not the spawned worker, or applied only at `relabel_run` while
    `entrant_actual` went on reaching `score_seats` — the ablation would return
    the baseline and the label would be priced at nothing. **A number this
    repository quotes must come from a switch someone has watched bite.**

    Mangaung 2016 is used because it is small (~7s at 200 draws) and because it
    is one of the TEN city-years where a label exists. At the other six
    `entrant_actual` is `None`, the ablation is a no-op by construction, and
    this test would pass while proving nothing.
    """
    import os
    import montecarlo as M
    import compare_history as CH
    from pathlib import Path
    data = Path("data/raw/elections")
    if not data.is_dir():
        skip("no election archive on disk")
    M.fix_hash_seed()
    prev = os.environ.get("JHB_SCORE_NO_RELABEL")
    try:
        os.environ.pop("JHB_SCORE_NO_RELABEL", None)
        on = CH.run_city_year("mangaung", "2016", 200, data)
        os.environ["JHB_SCORE_NO_RELABEL"] = "1"
        off = CH.run_city_year("mangaung", "2016", 200, data)
    finally:
        os.environ.pop("JHB_SCORE_NO_RELABEL", None)
        if prev is not None:
            os.environ["JHB_SCORE_NO_RELABEL"] = prev

    assert on["scored_without_relabel"] is False, on["scored_without_relabel"]
    assert off["scored_without_relabel"] is True, (
        "the artefact does not record that it was scored without the label. An "
        "absent or wrong stamp makes two incomparable runs look comparable.")
    assert off["crps"] > on["crps"], (
        f"withholding the arrival label did not make the score worse: "
        f"{on['crps']:.4f} with the label, {off['crps']:.4f} without. Either "
        f"the switch is inert or it is not reaching every consumer of "
        f"`entrant_actual` — it must reach `calibration_columns` and both "
        f"`score_seats` calls, not only `relabel_run`.")


def test_the_arrival_referee_is_rendered_and_reads_the_right_way_round():
    """⛔ THIS SECTION EXISTED AS A NUMBER IN A FILE AND AS NOTHING A READER SAW.

    `backtest.arrival_group_score` was computed into `history.json` on every run
    from the day it was repaired and rendered in no report, so the one
    instrument that scores arrivals WITHOUT handing the model the answer was
    invisible unless somebody opened the JSON. `ITERATING.md` had prescribed
    "reported beside the relabelled score as a sensitivity pair" the whole time.

    The direction is asserted because it is the half a reader gets wrong: these
    are PIT values, so **above 0.5 means the model forecast too LITTLE**. A
    table that renders but is read backwards is worse than no table.
    """
    import compare_history as CH
    rows = [{"city": "Johannesburg", "year": "2021",
             "arrival_group": {"n_arrived": 32, "n_columns": 33,
                               "actual_mass": 0.19988, "actual_seats": 46,
                               "mass_mean": 0.09539, "mass_median": 0.08987,
                               "seats_mean": 22.957, "seats_median": 22.0,
                               "mass_pit": 0.989, "seats_pit": 0.976,
                               "seats_outside_support": False,
                               "mass_err": 0.10449, "seats_err": 23.043}}]
    out = "\n".join(CH._arrival_referee(rows))
    assert "19.99%" in out and "9.54%" in out, (
        f"the actual and forecast arrival mass are not both in the table; a "
        f"sensitivity pair that shows one side is not a pair.\n{out}")
    assert "0.989" in out, "the mass PIT is not rendered"
    assert "too little" in out.lower(), (
        "the table does not tell the reader which way a PIT above 0.5 reads. "
        "It is the one thing they will get wrong.")

    # An artefact from before the referee existed must render nothing, not crash
    # and not an empty table with a misleading panel mean over zero rows.
    assert CH._arrival_referee([{"city": "X", "year": "2016"}]) == [], (
        "a results set with no arrival_group produced output. Older "
        "history.json files have no such key and must render no section.")


def _toy(seed=7):
    import numpy as np
    rng = np.random.default_rng(seed)
    names = ["ANC", "DA", "EFF", "ACTIONSA"]
    X = rng.poisson([90, 70, 30, 12], size=(1000, 4)).astype(float)
    return names, X, np.array([95., 66., 33., 10.]), rng


def test_a_columns_pit_does_not_depend_on_which_other_columns_are_scored():
    """⛔ THE FLOOR USED TO MOVE ON ITS OWN, AND THIS IS WHY.

    `pit_values` drew from ONE stream, one value per column, in column order —
    so the j-th column got the j-th draw and adding, removing or reordering any
    column re-rolled every column after it. A change to the model and a re-roll
    of the randomisation were then indistinguishable.

    Measured on the committed panel before the fix: the seed alone moved the
    pooled mean PIT with sd **0.00955** on `reference` and **0.00528** on
    `claimed`, and moved the statistic ITERATING quotes as Key 2's width floor
    — `reference`/2021 probit-SD, n=235, reading exactly 1.2000 — with sd
    **0.0327**. The 1.2000 → 1.3557 finding built on it is 3.4 sd of a paired
    re-roll. **Key 2 is untradeable; a floor that moves 0.03 while the model
    stands still is not a floor.**

    The assertion is EXACT equality, not a tolerance. Same entropy, same first
    double — if this ever needs a tolerance, the keying has broken.
    """
    import numpy as np
    import score as S
    names, X, y, rng = _toy()
    base = S.pit_values(X, y, names)

    front = np.column_stack([rng.poisson(5, 1000).astype(float), X])
    added = S.pit_values(front, np.r_[4., y], ["NEWPARTY"] + names)
    assert np.array_equal(base, added[1:]), (
        f"adding a column changed other columns' PIT by up to "
        f"{float(np.max(np.abs(base - added[1:])))}. The randomisation is still "
        f"positional, so a model change and a re-roll are indistinguishable.")

    idx = [3, 1, 0, 2]
    reordered = S.pit_values(X[:, idx], y[idx], [names[i] for i in idx])
    assert np.array_equal(base[idx], reordered), "column order still matters"


def test_the_pit_key_is_stable_across_processes_and_is_not_pythons_hash():
    """⛔ `hash()` WOULD HAVE REPRODUCED §1.145 INSIDE THE CALIBRATION KEY.

    Python randomises string hashing per process. This repository pins it with
    `montecarlo.fix_hash_seed()` — but only from an `if __name__ == "__main__"`
    guard, so any IMPORTING caller (a test module, an analysis harness,
    `build_site`) runs unpinned. Keying the PIT on `hash(party)` would have made
    the same forecast produce different calibration depending on how the code
    was entered, which is exactly the defect §1.145 took a day to find.

    The golden literal is the guard: it is machine- and version-independent, and
    it fails the moment anyone swaps blake2b for something process-local.
    """
    import numpy as np
    import score as S
    assert S._column_entropy("ANC") == 16408193524922255279, S._column_entropy("ANC")
    assert S._column_entropy("DA") != S._column_entropy("ANC")

    # ⛔ AND THE GOLDEN IS ON THE OUTPUT, NOT THE HELPER. Asserting
    # `_column_entropy` alone left the key defeatable: it was written out TWICE
    # — in `pit_values` and in `redraw_pits` — and reverting BOTH call sites to
    # `hash()` kept every test in this file green, because neither site was
    # asserted. Found in review 2026-08-31. There is now one `column_rng`, and
    # this golden runs through it.
    rng = np.random.default_rng(3)
    X = rng.poisson([1.0, 2.0], size=(500, 2)).astype(float)
    got = S.pit_values(X, np.array([1., 2.]), ["ANC", "DA"], seed=20211101)
    assert [round(float(v), 12) for v in got] == [0.596815370098, 0.656853108072], (
        f"the PIT column key changed: {[float(v) for v in got]}. If this was "
        f"deliberate, every calibration figure on record moves with it and the "
        f"re-record must be declared. If it was not, something reintroduced a "
        f"process-local hash.")


def test_pit_intervals_returns_the_JUMP_and_a_pit_can_never_leave_zero_one():
    """⛔ `pit_intervals` HAD NO TEST, AND GETTING IT WRONG EMITS PIT > 1 SILENTLY.

    Returning `F(y)` instead of the jump `F(y) - F(y⁻)` produces PIT values up
    to **1.37** on a small-count fixture — and every calibration statistic
    downstream keeps computing, because nothing anywhere asserted the range.
    Measured in review 2026-08-31. Worse, the `mean jump > 0.2` guard in the
    averaging test below is satisfied MORE easily by the wrong quantity, so the
    one test in the neighbourhood actively failed to discriminate.

    This is the cheapest possible guard on the quantity Key 2 is quoted against.
    """
    import numpy as np
    import score as S
    rng = np.random.default_rng(11)
    X = rng.poisson([0.6, 1.2, 2.0, 0.9], size=(1000, 4)).astype(float)
    y = np.array([1., 1., 2., 0.])
    lo, w = S.pit_intervals(X, y)

    below = np.array([float((X[:, j] < y[j]).mean()) for j in range(4)])
    at_or = np.array([float((X[:, j] <= y[j]).mean()) for j in range(4)])
    assert np.allclose(lo, below) and np.allclose(w, at_or - below), (
        "pit_intervals is not returning (F(y-), F(y)-F(y-))")
    assert (w >= 0).all() and (lo + w <= 1 + 1e-12).all()

    pits = S.pit_values(X, y, ["A", "B", "C", "D"])
    assert (pits >= 0).all() and (pits <= 1).all(), (
        f"PIT outside [0,1]: {pits.min():.4f}..{pits.max():.4f}")

    # And the guard must actually fire on the wrong quantity.
    #
    # ⚠️ AT `replicates=64`, DELIBERATELY. The first version of this mutation
    # drew ONE uniform per column and passed — column A's ceiling under the
    # mutation is 1.46, but it only exceeds 1 when u > 0.487, and that seed's
    # draw happened to fall below. The guard was right; the MUTATION was flaky,
    # which is the same defect one level up: a check that only sometimes
    # detects the thing it is checking for. 64 draws makes it 0.487**64.
    assert float((below + at_or).max()) > 1.0, (
        "this fixture cannot exceed 1 even under the mutation, so the mutation "
        "proves nothing. Pick columns with more mass at the outcome.")
    import unittest.mock as _m
    with _m.patch.object(S, "pit_intervals", lambda X_, y_: (below, at_or)):
        try:
            S.pit_values(X, y, ["A", "B", "C", "D"], replicates=64)
        except ValueError:
            pass
        else:
            raise AssertionError(
                "pit_values accepted a jump of F(y) instead of F(y)-F(y-), "
                "emitting PIT above 1. The range guard cannot fire.")


def test_averaging_the_statistic_and_averaging_the_values_are_not_the_same():
    """⛔ THE WRONG ONE INVERTS THIS PROJECT'S WIDTH VERDICT.

    R-averaging exists to take the randomisation noise out of a Key 2 figure.
    The tempting implementation — average the PIT values, then compute one
    statistic — shrinks every draw toward its jump midpoint and reports a
    forecast as better calibrated than it is. Measured on a real city-year:
    probit-SD **0.75 statistic-averaged against 0.43 value-averaged**; on the
    full `reference` population it reads 1.20 correctly and **1.01 —
    "correct"** the wrong way.

    Averaging the statistic is right because the statistic is what carries the
    claim; averaging the values is a different estimator of a different thing.
    """
    import numpy as np
    import compare_history as CH
    import score as S
    # ⛔ SMALL COUNTS, DELIBERATELY. The first version of this test used the
    # shared toy (Poisson means 90/70/30/12) and the two methods agreed to
    # 0.0025 — because the jump mass P(X = y) is negligible for a party
    # holding ninety seats. The effect lives entirely in the small parties,
    # which is where this panel's randomisation lives too (22 truth-one
    # `claimed` columns carry ten times the jump mass of the truth-zero ones).
    # A fixture without that property cannot tell the two estimators apart and
    # would have passed whichever one was implemented.
    import numpy as np
    rng = np.random.default_rng(11)
    names = ["SMALL_A", "SMALL_B", "SMALL_C", "SMALL_D"]
    X = rng.poisson([0.6, 1.2, 2.0, 0.9], size=(1000, 4)).astype(float)
    y = np.array([1., 1., 2., 0.])
    lo, w = S.pit_intervals(X, y)
    assert float(np.mean(w)) > 0.2, (
        f"the fixture's mean jump mass is {float(np.mean(w)):.3f}; too small to "
        f"discriminate. That is the defect this test exists to catch.")
    block = {"parties": names, "pit": list(S.pit_values(X, y, names)),
             "pit_lo": list(lo), "pit_w": list(w), "pit_seed": 20211101}
    drawn, exact = CH.redraw_pits(block, replicates=64)
    assert exact and drawn.shape == (64, 4)
    stat = float(np.mean([CH.pit_dispersion(list(r)) for r in drawn]))
    vals = CH.pit_dispersion(list(drawn.mean(axis=0)))
    assert abs(stat - vals) > 0.05, (
        f"statistic-averaging and value-averaging agree to {abs(stat-vals):.4f} "
        f"on this fixture, so the test cannot tell them apart and would not "
        f"catch the substitution. Pick a fixture with real jump mass.")

    one, _ = CH.redraw_pits(block, replicates=1)
    assert np.array_equal(one[0], np.asarray(block["pit"])), (
        "R=1 must reproduce the stored randomisation exactly, or the artefact "
        "and the redraw are describing different forecasts.")


def test_an_artefact_without_the_intervals_falls_back_LOUDLY():
    """⛔ A SILENT FALLBACK TO R=1 IS A GUARD THAT READS AS WORKING.

    `history.json` written before this change carries `pit` and no
    `pit_lo`/`pit_w`, so the R-averaging cannot run on it. That is expected —
    the re-record is deliberately deferred to the re-emit window — and it is
    precisely the state in which a quiet fallback would report an R=64 figure
    that is really one draw. So the fallback sets `exact=False`, and
    `exact_mean_pit` returns `nan` rather than the single-draw mean, which is a
    different quantity wearing the same name.
    """
    import math
    import compare_history as CH
    import score as S
    names, X, y, _ = _toy()
    old = {"parties": names, "pit": list(S.pit_values(X, y, names))}
    drawn, exact = CH.redraw_pits(old, replicates=64)
    assert drawn.shape[0] == 1 and exact is False, (
        f"an artefact with no stored intervals returned {drawn.shape[0]} "
        f"replicates with exact={exact}. It cannot; there is nothing to redraw "
        f"from, and reporting 64 would be a fabricated precision.")
    assert math.isnan(CH.exact_mean_pit(old)), (
        "exact_mean_pit returned a number for a block that cannot support one.")


def test_pit_values_refuses_a_mis_keyed_or_duplicated_column_set():
    """The name IS the key now, so a wrong name list mis-keys silently.

    A short list would key every column after the gap to the wrong party; a
    duplicate would give two columns the same uniform. Both are invisible in the
    output and permanent in the artefact, so both are refused at the call.
    """
    import score as S
    names, X, y, _ = _toy()
    for bad, why in [(names[:3], "too few names"),
                     (["ANC", "ANC", "EFF", "DA"], "a duplicate name")]:
        try:
            S.pit_values(X, y, bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"{why} was accepted")


if __name__ == "__main__":
    # `run_module`, NOT a hand-rolled loop. Until 2026-08-23 this file ended with
    # `for name, fn in sorted(globals().items()): ... fn()`, which catches
    # neither `SkipTest` nor `SystemExit` — so the FIRST skip aborted the run and
    # every later test in the file silently never executed, and no summary was
    # printed. Five files were in that state; `test_regressions` alone has five
    # `skip(` calls. Under `run_all.py` they were fine, because the suite calls
    # `run_module(vars(module))` itself — the suite hid it. MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
