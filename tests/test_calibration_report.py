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
    figure near 0.50. That is not a hypothetical: on the nine city-years the
    claimed population pools to **0.588** and splits into **0.431 at ranks 1-3**
    and **0.750 at ranks 4-12** (n=27 and n=26, cluster-bootstrap CIs [0.380,
    0.479] and [0.674, 0.810], both excluding 0.50 in opposite directions). The
    same rank ordering the band table already used was eleven lines away.

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


def _banded_results(rng, n_city_years, lam_forecast, lam_truth_top,
                    lam_truth_mid, per_band=3):
    """City-years whose TOP of the ballot and MIDDLE are biased opposite ways.

    ``per_band`` parties at ranks 1-3 and ``per_band`` at ranks 4-12, with the
    truth drawn BELOW the forecast at the top and ABOVE it in the middle. Equal
    band sizes and symmetric shifts, so the pooled mean PIT comes out at
    ~0.50 — a forecast that reads perfectly centred and is not centred anywhere.

    That is this model's own shape (claimed columns, committed history.json at
    1500 draws: ranks 1-3 mean PIT 0.431, ranks 4-12 0.750, pooled 0.587) and it
    is the case the pooled statistic shipped unable to see.

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

    The model's own figures (claimed columns, committed history.json, 1500
    draws): pooled 0.587, ranks 1-3 0.431, ranks 4-12 0.750.
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

    The whole force of the finding is that the signed vote bands (+32.50pp at
    ranks 1-3, −37.34pp at 4-12, committed history.json at 1500 draws) and the
    per-band PIT (0.431 / 0.750) are the SAME statement measured twice. That
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


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
