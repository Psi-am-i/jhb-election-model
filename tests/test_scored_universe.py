"""The scored column set, and the calibration test that has to survive it.

Two defects, both in the INSTRUMENT rather than in the model — which is the
class this repository can least afford, because a broken scorer cannot be
caught by a backtest: it changes what "better" means and every tuning decision
taken against it is taken against nothing.

⛔ **#13 — THE SCORED UNIVERSE IS CHOSEN BY THE FORECASTER.**
``score.seat_matrix`` admits a column when ``truth[i] > 0 or
samples[:, i].max() > 0``. The second clause is the forecaster's own draws, so
two forecasters scored on the same city-year are scored on different columns.
Measured on the committed panel: across 24 city-years the model is scored over
**580** columns and uniform-swing over **332**, and at Johannesburg 2021 alone
it is 55 against 19. ``compare_history`` states this exactly and then scopes the
warning to ``energy`` and ``variogram`` — while the report prints a
``crps.total`` margin of 38.3% over uniform-swing off the same column sets.

⛔ **#15 — THE CALIBRATION HEADLINE RESTS ON A POPULATION THE FORECASTER
SELECTS.** ``claimed`` admits a column when the model gives it a seat in half
its draws. That rule is very nearly the complement of this model's dominant
failure mode, and on the fixed ``reference`` population it drops **eight of the
ten worst columns**. And the χ² printed beside it is a nominal test on columns
that cluster inside city-years, so its rejection of uniformity was never
established.

WHAT SHAPE OF TEST, and what was rejected. ``tests/_support.election_files_read``
is this suite's exemplar: it watches the real mechanism and asserts both that the
bad thing is absent and that the mechanism ran at all. A spy is the wrong
instrument for a scorer — there is no I/O, only arithmetic — so the two
instruments here are:

* for #13, **an invariant with a constructed violation**. The invariant is that
  two forecasters scored on a held universe carry identical column sets and
  identical CRPS and energy totals; the violation is a synthetic pair whose
  admitted columns differ by construction, pushed through the same predicate,
  which must come back False and name the columns.
* for #15, **a positive control on a fixture of known width and shift** —
  ``test_calibration_report._shift_scale_results``, the suite's existing
  constructed calibration panel. The clustered test must reject a population
  built to be non-uniform and must not reject one built to be calibrated; and
  because the point of the correction is the DESIGN EFFECT, there is a third
  control where the columns are correlated inside their clusters but still
  uniform marginally, which the nominal test rejects falsely and the corrected
  one must not.

Every assertion below is on a NUMBER. None is on the wording of a verdict
string: this repository has already shipped a test that pinned a ``why`` note
while the arithmetic beside it was broken.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned, skip  # noqa: E402

import numpy as np  # noqa: E402

import score as S  # noqa: E402


# ---------------------------------------------------------------------------
# constructed forecasters
# ---------------------------------------------------------------------------

# A council of 195 seats over six real parties, three of which are small enough
# that a forecaster can plausibly miss them. Fixed rather than drawn from the
# repository's own output: a fixture whose premise is a passing state of the
# tree expires silently the day that state changes.
ACTUAL = {"ANC": 90, "DA": 60, "EFF": 30, "IFP": 9, "PA": 5, "TINY": 1}

# The input-selected population a comparison should be held on — here a stand-in
# for `compare_history.reference_universe`, which is built from a previous
# result and a nomination slate and cannot be computed inside `score.py`.
# ⛔ IT DOES NOT CONTAIN EVERY SEAT-WINNER, deliberately: `TINY` won a seat and
# is absent, exactly as seven real parties are absent from `reference` across
# the committed panel (ALJAMAAH at Johannesburg 2011, PA at Johannesburg 2016
# and Ekurhuleni 2016, IFP at Tshwane 2021, MINORITIES_OF_SOUTH_AFRICA at
# eThekwini 2016, AGENCY_FOR_NEW_AGENDA at Mangaung 2016, AIC at Buffalo City
# 2011). That is why the held universe is a union and not this list.
FIXED = ["ANC", "DA", "EFF", "IFP", "PA", "COPE", "ACDP", "ATM"]

# What each forecaster believes. The model carries two GHOST columns — parties
# that won nothing and were never on the fixed list — because phantom mass is
# the thing the admission rule exists to penalise, and a held universe that
# quietly forgave it would be a worse instrument than the one it replaced.
_MODEL = {"ANC": (88, 9), "DA": (62, 8), "EFF": (33, 5), "IFP": (7, 3),
          "PA": (0.2, 0.6), "GHOST_A": (0.4, 0.8), "GHOST_B": (0.3, 0.7)}
_BENCH = {"ANC": (95, 0.01), "DA": (58, 0.01), "EFF": (28, 0.01),
          "IFP": (10, 0.01)}


def _draws(spec, n=400, seed=11):
    """``n`` seat draws from a ``{party: (mean, sd)}`` spec, rounded and clipped."""
    rng = np.random.default_rng(seed)
    return [{p: int(max(0, round(rng.normal(m, sd)))) for p, (m, sd) in spec.items()}
            for _ in range(n)]


def _pair():
    """The model and a deterministic baseline, scored their own way and held."""
    model, bench = _draws(_MODEL, seed=11), _draws(_BENCH, seed=12)
    own = {"model": S.score_seats(model, ACTUAL),
           "bench": S.score_seats(bench, ACTUAL)}
    held = S.hold_universe([model, bench], ACTUAL, fixed=FIXED)
    on_held = {"model": S.score_seats(model, ACTUAL, universe=held),
               "bench": S.score_seats(bench, ACTUAL, universe=held)}
    return model, bench, own, held, on_held


# ---------------------------------------------------------------------------
# #13 — the invariant, and a constructed violation of it
# ---------------------------------------------------------------------------


def test_the_default_admission_rule_leaves_two_forecasters_incomparable():
    """The defect itself, reproduced: the column set moves with the forecaster.

    This is the *premise* of everything below, and it is constructed rather than
    observed — if it ever passes because both forecasters happened to admit the
    same columns, the fixture has stopped reproducing the defect and every
    assertion after it is about nothing.
    """
    _, _, own, _, _ = _pair()
    report = S.comparable(own)

    assert report["by_forecaster"]["model"] != report["by_forecaster"]["bench"], (
        f"the fixture is meant to reproduce the denominator drift and did not: "
        f"both forecasters were scored on "
        f"{report['by_forecaster']['model']} columns. Fix the fixture, not the "
        f"assertion — the whole point is a pair whose admitted sets differ.")
    # The exact asymmetry, so a change to the admission rule fails here loudly
    # rather than somewhere downstream: model 8 columns, baseline 6.
    assert report["by_forecaster"] == {"model": 8, "bench": 6}, \
        report["by_forecaster"]
    assert report["comparable"] is False
    assert sorted(report["mismatch"]) == ["bench", "model"]
    assert report["mismatch"]["model"]["only_here"] == ["GHOST_A", "GHOST_B"], (
        "the columns only the model has are its phantom mass, and the "
        "predicate must name them — a boolean alone cannot be acted on")
    assert report["mismatch"]["bench"]["missing"] == ["GHOST_A", "GHOST_B"]


def test_holding_the_universe_moves_no_crps_and_no_energy_number():
    """⛔ THE LOAD-BEARING CLAIM, AND IT IS AN EXACT ONE.

    A column outside a forecaster's own scored set is, by the admission rule,
    zero in the truth and zero in every one of its draws. Such a column
    contributes ``E|X-y| = 0`` and a spread term of 0 to CRPS, and an extra zero
    coordinate leaves every Euclidean norm unchanged, so it contributes nothing
    to the energy score either. Holding the universe at a SUPERSET therefore
    changes neither, for the model or for the baseline — which is what makes the
    38.3% CRPS margin in the report quotable **as it stands**.

    Asserted with ``==`` on floats, not ``isclose``. The claim is exact
    arithmetic, and a tolerance here would hide the one thing worth knowing: a
    future admission rule that admits a column the forecaster does NOT put mass
    on would break the invariance, and it must break this test rather than drift
    inside a tolerance.
    """
    _, _, own, held, on_held = _pair()

    assert set(held) >= set(own["model"]["parties"]), \
        "the held universe must be a superset or the invariance does not apply"
    assert set(held) >= set(own["bench"]["parties"])

    for name in ("model", "bench"):
        assert on_held[name]["crps"]["total"] == own[name]["crps"]["total"], (
            f"{name}: CRPS total moved from {own[name]['crps']['total']!r} to "
            f"{on_held[name]['crps']['total']!r} when the universe was held. "
            f"Both-zero columns must contribute exactly zero; if they do not, "
            f"the admission rule or `crps_sample` has changed and no "
            f"model-vs-baseline margin computed either way is quotable.")
        assert on_held[name]["energy"] == own[name]["energy"], (
            f"{name}: energy score moved from {own[name]['energy']!r} to "
            f"{on_held[name]['energy']!r}. An extra zero coordinate cannot "
            f"change a Euclidean norm.")

    # And the margin itself — the number the report prints — is untouched.
    before = own["bench"]["crps"]["total"] - own["model"]["crps"]["total"]
    after = on_held["bench"]["crps"]["total"] - on_held["model"]["crps"]["total"]
    assert before == after and before > 0, (before, after)


def test_holding_the_universe_is_what_makes_the_comparison_one_comparison():
    """After holding, the sets are identical and the result says so."""
    _, _, _, held, on_held = _pair()
    report = S.comparable(on_held)

    assert report["comparable"] is True, report["mismatch"]
    assert report["mismatch"] == {}
    assert report["n"] == len(held) == 11
    assert (on_held["model"]["universe_key"]
            == on_held["bench"]["universe_key"] == report["key"])
    assert on_held["model"]["universe_held"] is True
    # The key is order-insensitive: no score here depends on column order, so a
    # key that cried wolf on a reordering would be a guard nobody could keep.
    assert S.universe_key(held) == S.universe_key(list(reversed(held)))
    # ...and it is NOT insensitive to content, which is the half that matters.
    assert S.universe_key(held) != S.universe_key(held[:-1])


def test_the_predicate_catches_a_constructed_violation_of_the_held_universe():
    """⛔ CAN THE DETECTOR SEE? One column removed, through the same predicate.

    The invariant above is only evidence if the thing asserting it would fail
    when the invariant is false. So take a genuinely held pair — the state
    ``test_holding_the_universe_is_what_makes_the_comparison_one_comparison``
    certifies — and break it by one column.
    """
    _, _, _, _, on_held = _pair()
    assert S.comparable(on_held)["comparable"] is True, "precondition"

    broken = {"model": dict(on_held["model"]), "bench": dict(on_held["bench"])}
    dropped = broken["bench"]["parties"][3]
    broken["bench"]["parties"] = [p for p in broken["bench"]["parties"]
                                  if p != dropped]

    report = S.comparable(broken)
    assert report["comparable"] is False, (
        f"a forecaster scored on one fewer column than its opponent was "
        f"reported comparable. The predicate is decoration.")
    assert report["mismatch"]["bench"]["missing"] == [dropped]
    assert report["by_forecaster"] == {"model": 11, "bench": 10}
    assert report["key"] is None, "a mismatched pair has no single universe key"


def test_a_universe_that_omits_a_real_seat_winner_is_refused():
    """The one omission that is never defensible, and why ``reference`` alone
    is not the held universe.

    Dropping a column where a party actually won deletes a real error from the
    sum for BOTH forecasters at once, which forgives whichever of them was worse
    on it. ``TINY`` here stands for the seven parties that won seats outside the
    committed panel's ``reference`` population.
    """
    model = _draws(_MODEL, seed=11)
    assert ACTUAL["TINY"] > 0 and "TINY" not in FIXED, "precondition"

    try:
        S.score_seats(model, ACTUAL, universe=list(FIXED))
    except ValueError as exc:
        assert "TINY" in str(exc), str(exc)
    else:
        raise AssertionError(
            "score_seats accepted a universe with no column for TINY, which won "
            "a seat. The score would have stopped counting a real error and "
            "nothing would have said so.")

    # And the union built by `hold_universe` does contain it, from either side.
    assert "TINY" in S.hold_universe([model], ACTUAL, fixed=FIXED)
    assert "TINY" in S.hold_universe([], ACTUAL, fixed=FIXED)

    # `parties` and `universe` are different operations and may not be given
    # together: one fixes the column ORDER over a forecaster-chosen set, the
    # other fixes the SET. Whichever won would be an argument-order accident.
    held = S.hold_universe([model], ACTUAL, fixed=FIXED)
    try:
        S.score_seats(model, ACTUAL, parties=held, universe=held)
    except ValueError as exc:
        assert "universe" in str(exc) and "parties" in str(exc)
    else:
        raise AssertionError("score_seats accepted both `parties` and "
                             "`universe` and silently picked one")


def test_dropping_a_forecasters_own_claims_is_allowed_counted_and_priced():
    """The other omission IS defensible, so it is recorded rather than refused —
    and the price is asserted as arithmetic, not described.

    A universe of ``reference ∪ seat-winners`` and nothing else forgives phantom
    mass: the model's GHOST columns stop being scored. That is a real choice with
    a real cost, and the cost is exactly the CRPS those columns carried.
    """
    model = _draws(_MODEL, seed=11)
    own = S.score_seats(model, ACTUAL)
    fixed_only = sorted(set(FIXED) | {p for p, s in ACTUAL.items() if s > 0})
    thin = S.score_seats(model, ACTUAL, universe=fixed_only)

    assert thin["dropped_claims"] == ["GHOST_A", "GHOST_B"], thin["dropped_claims"]
    assert own["dropped_claims"] == [], (
        "a forecaster scored on its own set drops nothing by definition")

    forgiven = sum(own["crps"]["per_party"][p] for p in thin["dropped_claims"])
    assert forgiven > 0, (
        f"the ghost columns carried CRPS {forgiven!r}, so this fixture no "
        f"longer prices anything. Phantom mass must cost something or the "
        f"choice being tested is not a choice.")
    assert math.isclose(own["crps"]["total"] - thin["crps"]["total"], forgiven,
                        rel_tol=0, abs_tol=1e-12), (
        f"dropping {thin['dropped_claims']} moved the CRPS total by "
        f"{own['crps']['total'] - thin['crps']['total']!r}, not by the "
        f"{forgiven!r} those columns carried. The two must agree exactly or "
        f"the scored set is not what `dropped_claims` says it is.")


def test_the_variogram_is_the_one_score_that_moves_and_it_is_not_predictable():
    """⛔ AND IT MOVES BOTH WAYS, so no direction may be predicted from ``d``.

    ``variogram_score`` is a MEAN over ``d(d-1)/2`` pairs. A both-zero column
    adds ``d`` non-zero cross terms and ``m(m-1)/2`` zero ones, so

        V(m) = (S + m·C) / [(d+m)(d+m-1)/2]

    rises while ``m < 2C/V - 2d + 1`` and falls after it. This test pins both
    limbs on one real forecast: padding a little raises it, padding a lot drives
    it towards zero. A future reader tempted to say "the model is scored over
    more columns, so its variogram is flattered" must fail here.
    """
    rng = np.random.default_rng(7)
    truth = np.array([90., 60., 30., 20., 10., 5., 3., 0.])
    samples = np.maximum(0, np.round(rng.normal(
        truth + np.array([5, -4, 2, 0, 3, -1, 1, 2.]),
        np.array([9, 8, 5, 4, 3, 2, 2, 2.]), size=(500, 8))))
    names = [f"P{i}" for i in range(8)]

    def padded(m):
        s = np.hstack([samples, np.zeros((500, m))])
        t = np.concatenate([truth, np.zeros(m)])
        ns = names + [f"Z{i}" for i in range(m)]
        return (S.crps_by_party(s, t, ns)["total"], S.energy_score(s, t),
                S.variogram_score(s, t))

    base = padded(0)
    for m in (5, 20, 50):
        crps, energy, vario = padded(m)
        assert crps == base[0], (m, crps, base[0])
        assert energy == base[1], (m, energy, base[1])
        assert vario != base[2], (
            f"padding by {m} both-zero columns left the variogram at "
            f"{vario!r}. It is a mean over pairs and it cannot be invariant; "
            f"if it is, the normalisation has gone.")

    assert padded(5)[2] > base[2], (
        "a small pad must RAISE the variogram on this fixture — the cross "
        "terms dominate before the pair count does")
    assert padded(50)[2] < base[2] / 2, (
        "a large pad must drive it towards zero — the pair count dominates in "
        "the end")


def test_the_committed_panel_is_scored_on_sets_that_differ():
    """The defect on the real artefact, with the population it covers stated.

    Scan-shaped: it reads live repository state, so it must show it scanned the
    right thing and that the thing is non-empty and within a two-sided band.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    records = json.loads(path.read_text())["records"]

    rows = [r for r in records if r.get("n_scored") and r.get("opponents")]
    scanned(rows, of=records, low=0.9, high=1.0,
            what="city-year rows carrying both a model n_scored and opponents",
            denominator="rows in history.json")

    differ = [r for r in rows
              if any(o.get("n_scored") not in (None, r["n_scored"])
                     for o in r["opponents"].values())]
    scanned(differ, of=rows, low=0.75, high=1.0,
            what="city-years where a baseline was scored on a different number "
                 "of columns from the model",
            denominator="city-year rows scanned")

    model_cols = sum(r["n_scored"] for r in rows)
    swing_cols = sum(r["opponents"]["uniform-swing"]["n_scored"] for r in rows
                     if "n_scored" in r["opponents"].get("uniform-swing", {}))
    assert model_cols > 1.5 * swing_cols, (
        f"the model is scored over {model_cols} columns across the panel and "
        f"uniform-swing over {swing_cols}. This test exists because that ratio "
        f"was 580:332; if it has closed, say so in MODEL-LOG rather than "
        f"loosening the assertion.")


# ---------------------------------------------------------------------------
# #15 — the clustered calibration test
# ---------------------------------------------------------------------------


def _fixture_groups(seed, n_city_years, width_mult, shift, replicates=32):
    """PIT columns from the suite's own constructed calibration panel.

    ``test_calibration_report._shift_scale_results`` builds city-years whose
    small parties have a KNOWN width (``width_mult``) and a KNOWN level error
    (``shift``), through the real ``calibration_columns``. It is imported rather
    than copied: a second generator of the same panel is a second definition of
    what "calibrated" means here, and the two would drift.

    The PITs are re-randomised ``replicates`` times from the stored jump
    intervals, because a χ² computed on ONE randomisation is not a stable
    number — on the committed panel a re-roll moves it from 19.3 to 66.2.
    """
    import compare_history as C
    from test_calibration_report import _shift_scale_results

    results = _shift_scale_results(seed, n_city_years, width_mult=width_mult,
                                   shift=shift)
    groups = []
    for r in results:
        block = r["calibration"]["claimed"]
        if not block["pit"]:
            continue
        drawn, exact = C.redraw_pits(block, replicates=replicates)
        assert exact, (
            "redraw_pits fell back to the single stored randomisation, so this "
            "control is testing one re-roll and not the statistic")
        groups.append(drawn)
    assert len(groups) == n_city_years, (
        f"the fixture produced {len(groups)} clusters for {n_city_years} "
        f"city-years. `_shift_scale_results` has changed shape and this "
        f"control no longer constructs what it says it does.")
    return groups


def test_the_clustered_test_does_not_reject_a_calibrated_population():
    """The null control. A test that rejects everything measures nothing."""
    groups = _fixture_groups(4242, 12, width_mult=1.0, shift=0.0)
    n = sum(g.shape[1] for g in groups)
    assert 100 <= n <= 200, (
        f"the calibrated fixture carries {n} claimed columns; the control was "
        f"calibrated at ~144 and a panel an order of magnitude different is "
        f"not the same test")

    result = S.chi2_clustered(groups, draws=4000)
    assert result["estimable"] is True
    assert result["chi2_rs"] < result["chi2_crit_95"], (
        f"χ²_RS {result['chi2_rs']:.2f} against {result['chi2_crit_95']} on a "
        f"population built to be calibrated. The test rejects its own null and "
        f"nothing it says about the model can be read.")
    assert result["rejects_in"] <= 0.15 * result["replicates"], (
        f"{result['rejects_in']}/{result['replicates']} randomisations reject a "
        f"calibrated population, against a nominal 5%")


def test_the_clustered_test_rejects_a_population_built_to_be_wrong():
    """The positive control, on both kinds of wrong.

    A shifted forecast and a forecast of the wrong width fail uniformity for
    different reasons, and a test that saw only one of them would pass this
    suite while being blind to half of what it is quoted for.
    """
    for label, kwargs, floor in (
            ("shifted +2 seats", {"width_mult": 1.0, "shift": 2.0}, 80.0),
            ("1.6x too wide", {"width_mult": 1.6, "shift": 0.0}, 25.0),
            ("0.5x too narrow", {"width_mult": 0.5, "shift": 0.0}, 40.0)):
        result = S.chi2_clustered(_fixture_groups(4242, 12, **kwargs),
                                  draws=4000)
        assert result["chi2_rs"] > max(floor, result["chi2_crit_95"]), (
            f"{label}: χ²_RS {result['chi2_rs']:.2f} against a critical value "
            f"of {result['chi2_crit_95']} and an expected floor of {floor}. "
            f"The clustering correction has swallowed a real fault.")
        assert result["rejects_in"] == result["replicates"], (
            f"{label}: only {result['rejects_in']}/{result['replicates']} "
            f"randomisations reject a population built to be non-uniform")


def test_the_correction_rescues_a_clustered_population_the_nominal_test_fails():
    """⛔ THE CONTROL ON THE CORRECTION ITSELF, not merely on the statistic.

    The two controls above would both pass if ``chi2_clustered`` ignored the
    design effect entirely and printed Pearson's χ². What the correction is FOR
    is a population whose columns are correlated inside their clusters but still
    uniform marginally: the nominal test rejects it falsely and the corrected
    one must not.

    Built with a Gaussian copula — each city-year draws one latent ``z`` and
    each column is ``Phi(rho·z + sqrt(1-rho²)·e)``, which is exactly U(0,1)
    marginally whatever ``rho`` is. Constructed rather than observed: no state
    of this repository is the premise.
    """
    def panel(rho, seed=7, k=24, per=15, replicates=16):
        rng = np.random.default_rng(seed)
        phi = np.vectorize(lambda x: 0.5 * (1.0 + math.erf(x / math.sqrt(2.0))))
        out = []
        for _ in range(k):
            z = rng.normal(size=(replicates, 1))
            e = rng.normal(size=(replicates, per))
            out.append(np.clip(phi(rho * z + math.sqrt(1 - rho * rho) * e),
                               1e-9, 1 - 1e-9))
        return out

    independent = S.chi2_clustered(panel(0.0), draws=2000)
    clustered = S.chi2_clustered(panel(0.85), draws=2000)
    crit = independent["chi2_crit_95"]

    assert abs(independent["deff"] - 1.0) < 0.25, (
        f"design effect {independent['deff']:.2f} on independent columns. It "
        f"must be ~1 there or the estimator is measuring something else.")
    assert independent["chi2_rs"] < crit, independent["chi2_rs"]

    assert clustered["chi2"] > crit, (
        f"the NOMINAL χ² reads {clustered['chi2']:.2f} against {crit} on a "
        f"clustered-but-uniform population, so it does not reject and this "
        f"control proves nothing. Raise rho or the columns per cluster — do "
        f"not weaken the assertion below.")
    assert clustered["deff"] > 2.0, (
        f"design effect {clustered['deff']:.2f} on columns correlated at "
        f"rho=0.85. The correction is inert.")
    assert clustered["chi2_rs"] < crit, (
        f"χ²_RS {clustered['chi2_rs']:.2f} against {crit}: the correction did "
        f"not rescue a population that is uniform by construction, so a "
        f"rejection it reports on the real panel cannot be distinguished from "
        f"this artefact.")


def test_there_is_one_cluster_resampler_in_the_repository_not_two():
    """One resampler, however many call sites — and the count is asserted.

    ``compare_history._cluster_bootstrap_ci`` is ``score.cluster_bootstrap``
    pinned to the pooled mean. ``compare_history`` cannot be imported from
    ``score`` (the dependency runs the other way), so the general version lives
    in ``score``; the specialised one must be shown to AGREE rather than assumed
    to, and no third one may appear.

    Bit-identical where both exist, not merely close: both draw the same cluster
    indices from the same seed and reduce them the same way, and a tolerance
    here would let two definitions of one number drift a long way before
    anything noticed. If ``compare_history`` is later changed to call into
    ``score`` — which is what should happen when that file is next opened — this
    test keeps working and keeps counting, rather than skipping.
    """
    modules = sorted((ROOT / "src").glob("*.py"))
    scanned(modules, of=modules, low=1.0, high=1.0,
            what="modules scanned for a cluster resampler",
            denominator="`.py` files in src/")
    defining = [p.name for p in modules
                if "def cluster_bootstrap" in p.read_text()
                or "def _cluster_bootstrap" in p.read_text()]
    # ⚠️ THE STATE TODAY IS THREE, AND THIS RECORDS IT RATHER THAN WISHING IT
    # AWAY. `compare_history._cluster_bootstrap_ci` is this function pinned to
    # the pooled mean and is asserted below to agree with it bit for bit.
    # `theta_residual.cluster_bootstrap` is the same scheme again — resample
    # metro-years, recompute `sd(residual)`, take percentiles — found by this
    # scan on 2026-09-13 and NOT consolidated here because that file belongs to
    # another piece of work. Both are `score.cluster_bootstrap` with a
    # `statistic`, and both should become calls to it when those files are next
    # opened. The assertion is an equality on the SET, not a floor: a fourth
    # implementation must turn this red, and so must a rename that hides one.
    assert set(defining) == {"score.py", "compare_history.py",
                             "theta_residual.py"}, (
        f"cluster resamplers are defined in {sorted(defining)}, against the "
        f"three recorded here. There is one such function and it belongs in "
        f"score.py; the other two are known debt with a named owner. A new one "
        f"is a second definition of a published interval — the failure mode "
        f"score.column_rng exists for — and a disappearance means a "
        f"consolidation that this test should be updated to describe, in the "
        f"same commit.")

    rng = np.random.default_rng(3)
    groups = [rng.random(n) for n in (7, 11, 4, 15, 9, 6, 12, 8, 5, 10)]
    mine = S.cluster_bootstrap(groups)
    assert mine["clusters"] == 10 and mine["n"] == sum(len(g) for g in groups)
    # It refuses to invent an interval from one cluster, which is the shape the
    # three-city-year panel had when this question was first asked.
    assert math.isnan(S.cluster_bootstrap(groups[:1])["lo"])

    if "compare_history.py" not in defining:
        return
    import compare_history as C
    lo, hi, draws = C._cluster_bootstrap_ci(groups)
    assert (mine["lo"], mine["hi"], mine["draws"]) == (lo, hi, draws), (
        f"score.cluster_bootstrap returns {(mine['lo'], mine['hi'])} where "
        f"compare_history._cluster_bootstrap_ci returns {(lo, hi)} on the same "
        f"clusters. They are meant to be one resampler.")
    assert math.isnan(C._cluster_bootstrap_ci(groups[:1])[0]), \
        "the two must agree about the degenerate case too"


def test_the_bootstrap_resamples_city_years_and_not_columns():
    """⛔ THE DEFINING PROPERTY, CONSTRUCTED — and the one that is invisible.

    A bootstrap that resamples COLUMNS returns an interval far too tight and
    looks entirely healthy doing it: same shape, same centre, a plausible width.
    Nothing downstream would notice, and the figure it produced would be quoted.

    So build clusters that differ from each other far more than their members
    differ inside them — the shape of a real panel, where a city-year shares a
    turnout draw and a national swing — and require the cluster interval to be
    much wider than the column one. The column bootstrap is written out in full
    here on purpose: it is the WRONG answer, and a test needs it present to
    show the right one is not it.
    """
    rng = np.random.default_rng(31)
    offsets = rng.normal(0.0, 1.0, size=12)
    groups = [rng.normal(off, 0.05, size=16) for off in offsets]

    clustered = S.cluster_bootstrap(groups, draws=4000, seed=5)
    flat = np.concatenate(groups)
    naive = rng.choice(flat, size=(4000, flat.size), replace=True).mean(axis=1)
    naive_width = float(np.percentile(naive, 97.5) - np.percentile(naive, 2.5))
    cluster_width = clustered["hi"] - clustered["lo"]

    assert naive_width > 0, "the column bootstrap produced no interval at all"
    # The expected ratio here is sqrt(n_total / k) = sqrt(192/12) = 4: the
    # cluster bootstrap has 12 independent units and the column one thinks it
    # has 192. The bound is set at 3 so that noise cannot decide the test, and
    # it is a bound on a RATIO rather than on a width so it does not go stale
    # when the fixture's scale changes.
    assert cluster_width > 3 * naive_width, (
        f"the cluster interval is {cluster_width:.4f} wide and a column "
        f"bootstrap of the same values is {naive_width:.4f}, a ratio of "
        f"{cluster_width / naive_width:.2f} against an expected 4. On clusters "
        f"whose between variance dwarfs their within variance the two cannot "
        f"be close; if they are, this function is resampling columns and every "
        f"interval it has ever produced is too tight.")
    assert clustered["clusters"] == 12 and clustered["n"] == 192
    assert math.isclose(clustered["point"], float(flat.mean()), rel_tol=1e-12)


def test_the_clustered_test_refuses_to_estimate_a_design_effect_it_cannot():
    """Eight clusters is the floor, and below it the result says so.

    The question "does the PIT histogram reject uniformity" was first asked on
    a THREE city-year panel. Three clusters cannot estimate ten cell design
    effects, and a number printed there would have been a fabrication — so the
    honest output is ``estimable: False``, not a smaller number.
    """
    rng = np.random.default_rng(21)
    tiny = [rng.random((8, 22)) for _ in range(3)]
    result = S.chi2_clustered(tiny)
    assert result["estimable"] is False
    assert math.isnan(result["chi2_rs"]) and math.isnan(result["deff"])
    assert result["clusters"] == 3

    # ...and it DOES estimate at eight, so the floor is a floor and not a wall.
    enough = S.chi2_clustered([rng.random((8, 22)) for _ in range(8)])
    assert enough["estimable"] is True
    assert enough["clusters"] == 8 and not math.isnan(enough["deff"])


def test_the_committed_panel_still_rejects_uniformity_once_clustered():
    """The measured answer, pinned. **It rejects — the fear was not borne out.**

    The nominal test was quoted as settled and was not: the columns cluster
    inside city-years and the nominal p is the independent one. Corrected, the
    design effect comes out at ≈1 and the rejection stands on both populations
    that may be quoted.

    δ̄ ≈ 1 is not an accident. Seats inside a council are zero-sum, so a
    city-year's per-column errors are NEGATIVELY correlated, which pushes the
    between-cluster variance of a pooled cell share down towards — and sometimes
    below — its independent value. A metro council is not a cluster sample of
    independent households, and the survey-sampling intuition that motivated
    this check points the wrong way here.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    import compare_history as C

    records = json.loads(path.read_text())["records"]
    measured = {}
    for pop in ("reference", "claimed"):
        groups = []
        for r in records:
            block = (r.get("calibration") or {}).get(pop)
            if not block or not block["pit"]:
                continue
            drawn, exact = C.redraw_pits(block, replicates=64)
            assert exact, f"{pop}: the artefact predates the stored PIT jumps"
            groups.append(drawn)
        scanned(groups, of=records, low=0.9, high=1.0,
                what=f"city-years contributing a `{pop}` PIT block",
                denominator="rows in history.json")
        measured[pop] = S.chi2_clustered(groups)

    for pop, result in measured.items():
        crit = result["chi2_crit_95"]
        assert result["estimable"] is True
        assert 0.5 < result["deff"] < 2.0, (
            f"`{pop}` design effect {result['deff']:.2f}. The measured figures "
            f"are 1.07 on `reference` and 1.01 on `claimed`; a value outside "
            f"this band means the panel's dependence structure has changed and "
            f"the reported rejection has to be re-argued, not re-asserted.")
        assert result["chi2_rs"] > crit, (
            f"`{pop}`: χ²_RS {result['chi2_rs']:.2f} against {crit}. The "
            f"measured figures are 32.33 and 41.05. If this has fallen below "
            f"the critical value the calibration claim has CHANGED — the "
            f"honest status is then 'not established', and that belongs in "
            f"MODEL-LOG before this assertion is touched.")
        assert result["rejects_in"] == result["replicates"], (
            f"`{pop}`: {result['rejects_in']}/{result['replicates']} "
            f"randomisations reject. Anything less and the answer depends on "
            f"the PIT re-roll rather than on the model.")
        assert result["ci_lo"] > crit, (
            f"`{pop}`: the cluster-bootstrap 95% interval on χ² is "
            f"[{result['ci_lo']:.2f}, {result['ci_hi']:.2f}] and its lower "
            f"bound has fallen to the critical value. Measured: [18.20, 80.39] "
            f"on `reference` and [25.49, 84.91] on `claimed`.")


def test_the_claimed_population_drops_the_columns_the_model_got_most_wrong():
    """⛔ #15(a), AS A NUMBER. The selection rule is not informationless.

    Forecast-selection leaves PIT uniform *under calibration* — a statement
    about the null, and the only thing that argument buys. When the null is
    false the selection can be very far from neutral, and here it is: the rule
    admits a column only when the model gives it a seat in half its draws, and
    the model's dominant failure is giving a real party essentially zero.

    Measured against the FIXED ``reference`` population on the committed panel:
    ``claimed`` keeps 2 of the 10 worst |z| columns, reads sd(z) 0.784 against
    1.062, and a mean z of +0.014 against +0.105.
    """
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    records = json.loads(path.read_text())["records"]

    rows = []
    for r in records:
        cal = r.get("calibration") or {}
        ref, claimed = cal.get("reference"), cal.get("claimed")
        if not ref or not claimed:
            continue
        keep = set(claimed["parties"])
        for party, z in zip(ref["parties"], ref["z"]):
            if z is not None:
                rows.append((party, float(z), party in keep))

    scanned(rows, of=records, low=10.0, high=30.0,
            what="columns in the fixed `reference` population carrying a z",
            denominator="rows in history.json")

    worst = sorted(rows, key=lambda t: -abs(t[1]))[:10]
    kept_worst = sum(1 for _, _, inc in worst if inc)
    assert kept_worst <= 4, (
        f"`claimed` keeps {kept_worst} of the ten worst columns in the fixed "
        f"population. The measured figure is 2/10, and the whole objection to "
        f"leading with `claimed` is that the rule drops them. If this has "
        f"risen the objection has weakened and the report should say so.")

    z_all = np.array([z for _, z, _ in rows])
    z_kept = np.array([z for _, z, inc in rows if inc])
    assert z_kept.size >= 50 and z_all.size > z_kept.size, (z_all.size, z_kept.size)
    assert z_kept.std(ddof=1) < 0.90 * z_all.std(ddof=1), (
        f"sd(z) reads {z_kept.std(ddof=1):.3f} on the claimed columns against "
        f"{z_all.std(ddof=1):.3f} on the fixed population (measured: 0.784 "
        f"against 1.062). `claimed` understating the width fault is the "
        f"finding; if it no longer does, this test is the place that says so.")
    assert abs(z_kept.mean()) < abs(z_all.mean()), (
        f"mean z {z_kept.mean():+.3f} on claimed against {z_all.mean():+.3f} "
        f"on the fixed population (measured: +0.014 against +0.105). The "
        f"selection flattering the level bias is the other half of the finding.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
