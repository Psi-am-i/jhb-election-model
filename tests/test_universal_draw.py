"""The universal draw (design 1j v4-L1): its width record and its drawer.

Design: ``audits/2026-10-11-model-round/step1/1j-universal-draw-design-v4.md``
and its addendum (option L1), on the machinery of v3 (and its addendum), v2
and v1; the tests the pre-registration ``prereg/2026-10-12-universal-draw.md``
names (M2, J1-J4, M6) and the ones the designs' writer's order lists.

Every input is CONSTRUCTED: a width record typed as a fixture, residual rows
simulated from known parameters, the two-pool spec of ``test_draw_streams``.
A fixture proves a mechanism, never a magnitude (MEMORY: fixture proves
mechanism). The record's values on the real panel are the re-emit window's
measurement (prereg M3).
"""

from __future__ import annotations

import copy
import json
import os
import math
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import montecarlo as M  # noqa: E402
import width_record as W  # noqa: E402
from test_draw_streams import (FIXTURE_RECORD, PARTIES, base_spec,  # noqa: E402
                               run_arm)

TRUTH = {"a": 0.03, "b": 0.82, "mid": 0.085, "k": 2.6, "delta": 0.85,
         "c1": 0.34, "c2": 0.075}


# --------------------------------------------------------------------------
# the curves and one party's width
# --------------------------------------------------------------------------

def test_the_width_curve_is_the_logistic_the_design_states():
    c = FIXTURE_RECORD["curve"]
    a, b = c["a"], c["b"]
    mid = math.exp(c["log_mid"])
    assert abs(M.width_sigma(c, mid) - (a + b) / 2) < 1e-12
    assert abs(M.width_sigma(c, 1e-7) - b) < 1e-3
    assert abs(M.width_sigma(c, 0.999) - a) < 0.05
    xs = [0.0005, 0.005, 0.05, 0.25]
    assert all(M.width_sigma(c, x) > M.width_sigma(c, y)
               for x, y in zip(xs, xs[1:])), "σ(s) must fall with size"


def test_the_location_is_zero_in_the_block_and_clamped_below():
    loc = FIXTURE_RECORD["location"]
    assert M.width_location(loc, 0.20) == 0.0
    assert M.width_location(loc, 0.45) == 0.0
    L = math.log(0.005 / 0.20)
    assert abs(M.width_location(loc, 0.005)
               - (loc["c1"] * L + loc["c2"] * L * L)) < 1e-12
    # the clamp at the record's 1st-percentile centre (review 2-review-1j-v4 §1)
    assert M.width_location(loc, 1e-6) == M.width_location(loc, M.LOCATION_CLAMP)
    assert M.width_location(loc, 1e-6, clamp=False) != \
        M.width_location(loc, M.LOCATION_CLAMP)


def test_the_shared_loading_interpolates_and_vanishes_in_the_block():
    rho = FIXTURE_RECORD["rho"]
    assert M.width_rho(rho, 0.001) == rho["lo"]
    assert abs(M.width_rho(rho, M.RHO_ANCHOR_HI) - rho["hi"]) < 1e-12
    assert M.width_rho(rho, 0.25) == 0.0
    mid = math.sqrt(M.RHO_ANCHOR_LO * M.RHO_ANCHOR_HI)
    assert rho["hi"] < M.width_rho(rho, mid) < rho["lo"]


def test_one_partys_width_new_judged_and_fallback():
    rec = FIXTURE_RECORD
    est = M.party_width(rec, 0.01, new=False)
    new = M.party_width(rec, 0.01, new=True)
    assert est["delta"] == 0.0 and new["delta"] == rec["delta"]
    assert abs(new["total"] - math.hypot(new["sigma"], rec["delta"])) < 1e-12
    # a judgement REPLACES the newness term, never adds to it (v3 §11.1)
    judged = M.party_width(rec, 0.01, new=True, sigma_j=0.3)
    assert judged["delta"] == 0.3
    zero = M.party_width(rec, 0.01, new=True, sigma_j=0.0)
    assert zero["total"] == zero["sigma"]
    fb = {"kind": "fallback", "fallback": {"with_history": 0.27, "without": 0.48}}
    assert M.party_width(fb, 0.3, new=False, history=True)["total"] == 0.27
    assert M.party_width(fb, 0.3, new=True, history=False)["total"] == 0.48
    assert M.party_width(fb, 0.3, new=False, history=True)["rho"] == 0.0


def test_pool_spec_centres_sum_to_one_and_follow_votes():
    sc, c, i = base_spec()
    spec = M.pool_spec(sc, c, i)
    psc = M.pool_spec_centres(spec)
    assert abs(sum(psc.values()) - 1.0) < 1e-12
    # by hand: pool vote shares at modal turnout times the post-IPF props
    pv = {n: v[1] * v[2][1] for n, v in spec.items()}
    tot = sum(pv.values())
    for p in PARTIES:
        hand = sum(float(v[3][v[5].index(p)]) * pv[n] / tot
                   for n, v in spec.items() if p in v[5])
        assert abs(psc[p] - hand) < 1e-12, p


# --------------------------------------------------------------------------
# the width record's estimator, on rows simulated from known parameters
# --------------------------------------------------------------------------

def simulate_rows(seed: int, truth=TRUTH, n_city=8, years=("2011", "2016"),
                  rho_lo=0.0):
    """Residual rows drawn from design v4 §1's own model at known values."""
    g = np.random.default_rng(seed)
    curve = {"a": truth["a"], "b": truth["b"], "log_mid": math.log(truth["mid"]),
             "k": truth["k"]}
    loc = {"c1": truth["c1"], "c2": truth["c2"]}
    rows = []
    sizes = np.exp(np.linspace(math.log(0.0004), math.log(0.18), 30))
    for y in years:
        for ci in range(n_city):
            city = f"c{ci}"
            z = g.standard_normal()
            for j, s in enumerate(sizes):
                new = j % 5 == 0
                sig = M.width_sigma(curve, s)
                sg2 = sig * sig + (truth["delta"] ** 2 if new else 0.0)
                r = (M.width_location(loc, s, clamp=False) - sg2 / 2
                     + math.sqrt(sg2) * (math.sqrt(rho_lo) * z
                                         if s < 0.01 and not new else 0.0)
                     + math.sqrt(sg2 * (1 - (rho_lo if s < 0.01 and not new
                                              else 0.0)))
                     * g.standard_normal())
                rows.append({"city": city, "year": y, "party": f"P{j}",
                             "s": float(s), "act": 1.0, "new": new,
                             "block": False, "r": float(r)})
    return rows


def test_the_joint_fit_recovers_the_parameters_it_was_simulated_from():
    """Estimation recovers truth on its own model (identification, review
    2-review-1j-v4 §1), and the location does not eat spread: the fitted b is
    near the true b, not inflated."""
    rows = simulate_rows(3, n_city=16, years=("2011", "2016", "2021"))
    fit = W.fit_joint(rows)
    assert abs(fit["curve"]["b"] - TRUTH["b"]) < 0.12, fit
    assert abs(fit["delta"] - TRUTH["delta"]) < 0.25, fit
    assert abs(fit["location"]["c1"] - TRUTH["c1"]) < 0.25, fit
    # and without a location in the truth, the fit finds none to speak of
    flat = dict(TRUTH, c1=0.0, c2=0.0)
    fit0 = W.fit_joint(simulate_rows(4, truth=flat, n_city=16,
                                     years=("2011", "2016", "2021")))
    L = math.log(0.001 / 0.2)
    assert abs(M.width_location(fit0["location"], 0.001, clamp=False)) < 0.35
    assert abs(M.width_location(fit["location"], 0.001, clamp=False)
               - (TRUTH["c1"] * L + TRUTH["c2"] * L * L)) < 0.5


def test_the_fit_weights_one_unit_per_party_cycle():
    rows = [{"party": "A", "year": "2011"}, {"party": "A", "year": "2011"},
            {"party": "A", "year": "2016"}, {"party": "B", "year": "2011"}]
    w = W._weights(rows)
    assert list(w) == [0.5, 0.5, 1.0, 1.0]


def test_the_fit_refuses_a_record_too_thin_to_fit():
    rows = simulate_rows(5, n_city=1, years=("2011",))[:10]
    try:
        W.fit_joint(rows)
    except SystemExit as exc:
        assert "MIN_ESTABLISHED" in str(exc)
        return
    raise AssertionError("a record of ten rows was fitted")


def test_the_shared_share_is_found_where_it_was_put_and_not_elsewhere():
    """ρ below 1% recovered from a constructed city-year effect; 0 where none
    was put (the 1-20% group). It can see, and it goes quiet."""
    rows = simulate_rows(6, n_city=16, years=("2011", "2016", "2021"),
                         rho_lo=0.45)
    fit = W.fit_joint(rows)
    rho = W.shared_shares(rows, fit)
    assert 0.25 < rho["lo"] < 0.65, rho
    assert rho["hi"] < 0.12, rho
    rows0 = simulate_rows(6, n_city=16, years=("2011", "2016", "2021"))
    rho0 = W.shared_shares(rows0, W.fit_joint(rows0))
    assert rho0["lo"] < 0.12, rho0


def test_residual_rows_use_the_block_frame():
    case = {"city": "x", "year": "2016",
            "centres": {"A": 0.5, "B": 0.3, "C": 0.15, "D": 0.05},
            "actual": {"A": 0.45, "B": 0.33, "C": 0.12, "D": 0.0},
            "new": ["C"]}
    rows = {r["party"]: r for r in W.residual_rows([case])}
    A, P = 0.45 + 0.33, 0.5 + 0.3
    assert abs(rows["C"]["r"] - (math.log(0.12 / 0.15) - math.log(A / P))) < 1e-12
    assert abs(rows["A"]["r"] - math.log((0.45 / A) / (0.5 / P))) < 1e-12
    assert rows["D"]["r"] is None, "a zero result has no log residual"
    assert rows["C"]["new"] and not rows["A"]["new"]
    single = dict(case, centres={"A": 0.7, "C": 0.15, "D": 0.15})
    rs = {r["party"]: r for r in W.residual_rows([single])}
    assert rs["A"]["r"] is None, "a one-member block has no within-block residual"


def test_the_record_reads_the_models_own_centres_at_a_real_city_year():
    """The writer's seam on one real backtest city-year (Buffalo City 2016):
    `run_model(stop_after="drawer_inputs")` hands back the model's own inputs
    with no draw, the residual rows are measured about the `pool_spec` centres
    it builds, and the fixed point's own location comes back finite for every
    drawn party. Wiring only: the widths are the fixture's."""
    inp = W.drawer_inputs("buffalocity", "2016", [])
    case = W.case_for(inp, "buffalocity", "2016")
    assert abs(sum(case["centres"].values()) - 1.0) < 1e-9
    assert set(case["centres"]) <= set(inp.index)
    assert set(case["new"]) <= set(inp.index)
    prior = inp.prior_pr_share
    assert all(float(prior.get(p, 0.0) or 0.0) <= 0 for p in case["new"])
    rows = W.residual_rows([case])
    with_r = [r for r in rows if r["r"] is not None]
    scanned(with_r, of=len(case["centres"]), low=0.3, high=1.0,
            what="parties with a residual", denominator="pooled parties")
    delta = W.location_shift({("buffalocity", "2016"): inp},
                             dict(FIXTURE_RECORD), draws=200)
    assert delta and all(np.isfinite(v) for v in delta.values())
    assert {p for (_c, _y, p) in delta} == set(case["centres"]) & set(delta_names(inp))


def delta_names(inp):
    """The parties the universal drawer draws at a city-year: the pooled
    members on the ballot (no pool-less party exists at any emitted spec)."""
    return {p for cfg in inp.scenario["pools"].values() for p in cfg["members"]
            if p in inp.index}


# --------------------------------------------------------------------------
# the drawer under the universal law
# --------------------------------------------------------------------------

def _universal_run(seed: int, draws: int = 2000, centres=None, sc=None):
    sc0, c0, i0 = base_spec(law="universal")
    sc0 = sc if sc is not None else sc0
    return run_arm(sc0, centres or c0, i0, lot=f"universal|test|{seed}",
                   draws=draws)


def test_the_calibration_conserves_every_centre_and_records_nothing():
    """Design v1 §1.2: each party's mean drawn share is its `pool_spec`
    centre; the calibration pass appends nothing to the turnout or split
    records, counts no balance, and leaves the capacity counters as found."""
    M._reset_cap_counters()
    st, out, drawer = _universal_run(1)
    assert len(drawer.turnout_record) == out.shape[0]
    assert all(len(v) == out.shape[0] for v in drawer.split_record.values())
    assert drawer.ipf_stats["balances"] == out.shape[0]
    assert max(drawer.kappa_error.values()) < M.KAPPA_TOL
    c = dict(zip(drawer.u_names, drawer.u_centres))
    for p in PARTIES:
        mean = out[:, PARTIES.index(p)].mean()
        assert abs(mean / c[p] - 1) < 0.05, (p, mean, c[p])
    assert any(stage.startswith("calib.") for stage, _ in st.keys)
    assert not any(stage == "split" for stage, _ in st.keys)


class _Patched:
    """Set module constants of `montecarlo` for a block, restoring them."""

    def __init__(self, **values):
        self.values = values
        self.saved = {}

    def __enter__(self):
        for k, v in self.values.items():
            self.saved[k] = getattr(M, k)
            setattr(M, k, v)
        return self

    def __exit__(self, *exc):
        for k, v in self.saved.items():
            setattr(M, k, v)
        return False


def _remeasured_error(drawer) -> dict:
    """The calibration pass's relative error, measured again on fresh
    calibration streams at the κ the drawer holds now: the κ it draws with.
    Leaves the capacity counters as found."""
    und, mov = M.capped_targets.undershoots, M.capped_targets.moved
    try:
        cal = M.DrawStreams(drawer.streams.run_lot, M.N_CAL)
        vals = np.array([drawer(dd, calib=True, strm=cal)
                         for dd in range(M.N_CAL)])
    finally:
        M.capped_targets.undershoots, M.capped_targets.moved = und, mov
    rel = np.abs(vals.mean(axis=0) / np.asarray(drawer.u_centres) - 1.0)
    return {p: float(rel[k]) for k, p in enumerate(drawer.u_names)}


def test_the_recorded_calibration_error_is_the_error_of_the_kappa_drawn_with():
    """Step-6 item 2. Converging: `kappa_converged` is True, fewer than
    `KAPPA_MAX_ITER` iterations ran, and the recorded `kappa_error` equals,
    to the bit, the error re-measured at the κ the drawer holds. NOT
    converging (constructed: `KAPPA_TOL` 0, which no mean can meet, and three
    iterations): `kappa_converged` is False, `kappa_iters` is the cap, and the
    recorded error is still the re-measured one, i.e. the run did not apply
    an update after its last measurement."""
    with _Patched(N_CAL=600):
        _, _, ok = _universal_run(7, draws=20)
        assert ok.kappa_converged is True
        assert 1 <= ok.kappa_iters < M.KAPPA_MAX_ITER
        assert max(ok.kappa_error.values()) < M.KAPPA_TOL
        assert _remeasured_error(ok) == ok.kappa_error
        with _Patched(KAPPA_TOL=0.0, KAPPA_MAX_ITER=3):
            _, _, bad = _universal_run(7, draws=20)
        assert bad.kappa_converged is False
        assert bad.kappa_iters == 3
        assert _remeasured_error(bad) == bad.kappa_error, (
            "the recorded calibration error does not describe the κ the run "
            "draws with: an update was applied after the last measurement")
        assert {p: w["kappa"] for p, w in bad.widths.items()} != \
            {p: w["kappa"] for p, w in ok.widths.items()}


def test_a_converging_calibration_is_unchanged_by_the_cap():
    """Step-6 item 2, bit-identity: on a converging run the cap is never
    reached, so raising `KAPPA_MAX_ITER` far above the iterations used changes
    no κ and no drawn number."""
    _, a, da = _universal_run(8, draws=200)
    assert da.kappa_converged and da.kappa_iters < M.KAPPA_MAX_ITER
    with _Patched(KAPPA_MAX_ITER=10 ** 6):
        _, b, db = _universal_run(8, draws=200)
    assert np.array_equal(a, b)
    assert db.kappa_iters == da.kappa_iters
    assert db.kappa_error == da.kappa_error


def test_a_switch_of_one_law_refuses_under_the_other():
    """Step-6 item 5: `centre_correction` under the incumbent law was ignored
    in silence, and `arrival_group_draw` under the universal law drew the
    arrival Dirichlet on top of δ. Each now stops the drawer with a sentence
    naming the switch and the law; the same spec with the switch off, or
    under its own law, draws."""
    cases = [("incumbent", "centre_correction", True),
             ("universal", "arrival_group_draw", True)]
    for law, key, value in cases:
        sc, c, i = base_spec(law=law)
        sc[key] = value
        try:
            run_arm(sc, c, i, lot=f"refuse|{key}", draws=5)
        except SystemExit as exc:
            assert f"{key} is on under draw_law='{law}'" in str(exc), exc
        else:
            raise AssertionError(f"{key} under the {law} law was accepted")
        sc[key] = False
        _, out, _ = run_arm(sc, c, i, lot=f"refuse|{key}", draws=5)
        assert out.shape == (5, len(PARTIES))
    sc, c, i = base_spec(law="universal")
    sc["centre_correction"] = True
    run_arm(sc, c, i, lot="refuse|own-law", draws=5)


def test_widths_are_read_in_the_records_frame():
    """Step-6 item 6. `width_record` fits each width at s = the pooled
    party's `pool_spec_centres` value (pooled parties only, summing to one
    over them). The drawer reads every pooled party's width at that same
    number, with or without an individual-path party; the conserved share
    differs from it by (1 − the individual mass), which the run records.
    Population: every drawn party is checked, both directions."""
    import contextlib
    import io
    for with_x in (False, True):
        sc, c, i = base_spec(law="universal")
        if with_x:
            i = dict(i, X=len(i))
            c = dict(c, X=0.05)
        with contextlib.redirect_stdout(io.StringIO()):
            psc = M.pool_spec_centres(M.pool_spec(copy.deepcopy(sc), dict(c), i))
        _, _, d = run_arm(sc, c, i, lot=f"frame|{with_x}", draws=5)
        assert set(d.widths) == set(i), (sorted(d.widths), sorted(i))
        for p in PARTIES:
            w = d.widths[p]
            assert w["centre_uncorrected"] == max(psc[p], 1e-12), (p, w)
            assert w["sigma"] == M.width_sigma(FIXTURE_RECORD["curve"],
                                               w["centre_uncorrected"])
        mass = d.individual_mass
        if not with_x:
            assert mass == 0.0
            continue
        assert 0 < mass < 1 and abs(d.widths["X"]["centre_uncorrected"]
                                    - mass) < 1e-12
        c_of = dict(zip(d.u_names, d.u_centres))
        for p in PARTIES:
            assert abs(c_of[p] - psc[p] * (1 - mass)) < 1e-12, p
            assert abs(d.widths[p]["centre_uncorrected"] - c_of[p]) > 1e-6, p


def test_the_split_is_the_centre_and_alpha_is_never_read():
    """Under the universal law a pool's `alpha` reaches nothing: NaN it and
    every drawn number is unchanged (design v1 §6)."""
    _, a, _ = _universal_run(2, draws=300)
    sc, c, i = base_spec(law="universal")
    for cfg in sc["pools"].values():
        cfg["alpha"] = float("nan")
    _, b, _ = run_arm(sc, c, i, lot="universal|test|2", draws=300)
    assert np.array_equal(a, b)


def test_the_own_term_is_the_rest_of_the_budget():
    """Composition is subtracted, not added; a floored party carries the
    excess (design v1 §2.5, v2 N1)."""
    _, _, drawer = _universal_run(3, draws=50)
    for p, w in drawer.widths.items():
        budget = w["sigma"] ** 2 * (1 - w["rho"]) + w["delta"] ** 2
        assert abs(w["own"] ** 2 + w["v_comp"] - w["floored"] - budget) < 1e-12
        assert w["v_comp"] >= 0 and w["own"] >= 0
    assert any(w["v_comp"] > 0 for w in drawer.widths.values()), (
        "no party carries any turnout composition: the measurement looked at "
        "nothing")


def test_the_falsifier_is_quiet_on_clean_runs_and_sees_a_twenty_percent_error():
    """Prereg M2 (design v2 §9): at most one false alarm in 20 seed pairs, and
    an injected ×1.2 mean error on one party is detected."""
    alarms = 0
    detected = 0
    for seed in range(20):
        _, _, drawer = _universal_run(100 + seed, draws=2000)
        rep = M.mean_conservation(drawer.conserve_record, drawer.calib_ratio,
                                  drawer.u_names, drawer.u_centres)
        assert rep["parties"] == len(PARTIES)
        alarms += bool(rep["fired"])
        if seed < 10:
            rec = np.array(drawer.conserve_record)
            k = list(drawer.u_names).index("C")
            rec[:, k] *= 1.2
            bad = M.mean_conservation(rec, drawer.calib_ratio, drawer.u_names,
                                      drawer.u_centres)
            detected += "C" in bad["fired"]
    assert alarms <= 1, f"{alarms} false alarms in 20 clean runs"
    assert detected == 10, f"a ×1.2 error detected in {detected} of 10"


def test_a_judged_party_takes_its_judged_width():
    """Design v3 §11: σ_J replaces the newness term in the drawer."""
    sc, c, i = base_spec(law="universal")
    sc["_new_parties"] = ["C"]
    _, _, d0 = run_arm(sc, c, i, lot="judged|1", draws=20)
    sc2 = copy.deepcopy(sc)
    sc2["_strength_applied"] = [{"party": "C", "support": None,
                                 "overperform": 1.0, "sigma_j": 0.25,
                                 "register": "§SJ0"}]
    _, _, d1 = run_arm(sc2, c, i, lot="judged|1", draws=20)
    assert d0.widths["C"]["delta"] == FIXTURE_RECORD["delta"]
    assert d1.widths["C"]["delta"] == 0.25 and d1.widths["C"]["judged"]


def test_the_centre_correction_is_the_records_location_below_the_block():
    """Prereg §3.3 (arm UC): off, the draw is bit-identical to the universal
    draw; on, every party with `pool_spec` centre below 20% has it multiplied
    by exp(m(s)) (s clamped at 0.016%) and the vector is renormalised, before
    the calibration pass, so the run conserves the corrected centres. Widths
    stay at the uncorrected centres (the arm differs in its centres alone)."""
    sc, c, i = base_spec(law="universal")
    sc["centre_correction"] = False
    _, off, d_off = run_arm(sc, c, i, lot="uc|1", draws=300)
    sc0, _, _ = base_spec(law="universal")
    _, u, _ = run_arm(sc0, c, i, lot="uc|1", draws=300)
    assert np.array_equal(off, u), "the switch off moved a drawn number"
    sc_on = copy.deepcopy(sc)
    sc_on["centre_correction"] = True
    _, on, d_on = run_arm(sc_on, c, i, lot="uc|1", draws=300)
    loc = FIXTURE_RECORD["location"]
    s0 = np.array(d_off.u_centres)
    want = np.array([x * math.exp(M.width_location(loc, x)) if x < M.WIDTH_BLOCK
                     else x for x in s0])
    want = want / want.sum()
    assert np.allclose(d_on.u_centres, want, rtol=1e-12)
    big = [k for k, x in enumerate(s0) if x >= M.WIDTH_BLOCK]
    assert big, "the fixture has no party in the block: nothing checks the line"
    for k in big:
        assert d_on.centre_correction["factor"][d_on.u_names[k]] == 1.0
    for p in d_on.u_names:
        assert d_on.widths[p]["sigma"] == d_off.widths[p]["sigma"], p
    assert max(d_on.kappa_error.values()) < M.KAPPA_TOL
    assert not np.array_equal(on, off)
    # the 2011 fallback carries no location: the switch applies nothing there
    fb = M.centre_correction({"kind": "fallback", "fallback": {}})
    assert fb["location"] is None and "fallback" in fb["why"]


def test_the_correction_is_fitted_on_earlier_cycles_only():
    """Prereg §3.3: the location a target's correction uses is the width
    record's own, and the record for each target reads strictly earlier
    cycles."""
    for target, cycles in W.FORWARD.items():
        assert all(int(y) < int(target) for y in cycles), (target, cycles)
    assert W.FORWARD["2016"] == ("2011",)
    assert W.FORWARD["2021"] == ("2011", "2016")
    assert W.FORWARD["2026"] == ("2011", "2016", "2021")


# --------------------------------------------------------------------------
# strength judgements: read at run time, ignored on a backtest, hashed
# --------------------------------------------------------------------------

class _City:
    def __init__(self, slug):
        self.slug = slug


class _Target:
    def __init__(self, slug, year):
        self.city, self.year = _City(slug), year


class _Rebound:
    """Undoes `_with_judgements`: `pools.JUDGEMENTS_DIR` back to the tree's."""

    def __init__(self, real):
        self.real = real

    def restore(self):
        import pools
        pools.JUDGEMENTS_DIR = self.real


def _with_judgements(text: str, slug: str, year: str):
    """A scratch judgements directory, bound as `pools.JUDGEMENTS_DIR` (the
    path is anchored to the repository, not the working directory)."""
    import pools
    tmp = tempfile.TemporaryDirectory()
    d = Path(tmp.name) / "judgements"
    d.mkdir()
    (d / f"{slug}-{year}.toml").write_text(text)
    real = pools.JUDGEMENTS_DIR
    pools.JUDGEMENTS_DIR = d
    return tmp, _Rebound(real)


def test_a_strength_entry_needs_its_width_and_its_register_row():
    import os
    tmp, bound = _with_judgements('[party.NEWP]\nsupport = 0.02\n', "joburg", "2026")
    try:
        try:
            M.strength_judgements(_Target("joburg", "2026").city,
                                  _Target("joburg", "2026"))
        except SystemExit as exc:
            assert "sigma_j" in str(exc) and "register" in str(exc)
        else:
            raise AssertionError("a strength without sigma_j was accepted")
    finally:
        bound.restore()
        tmp.cleanup()


def test_a_backtest_ignores_judgements_and_a_forecast_applies_them():
    import os
    body = ('[party.NEWP]\nsupport = 0.02\nsigma_j = 0.4\n'
            'register = "§SJ1"\n')
    for year, held in (("2021", True), ("2026", False)):
        tmp, bound = _with_judgements(body, "joburg", year)
        try:
            t = _Target("joburg", year)
            applied, ignored = M.strength_judgements(t.city, t)
        finally:
            bound.restore()
            tmp.cleanup()
        if held:
            assert applied == [] and ignored[0]["party"] == "NEWP"
            assert "backtest" in ignored[0]["reason"]
        else:
            assert ignored == [] and applied[0]["sigma_j"] == 0.4


def test_a_strength_edit_moves_no_spec_key_and_a_weights_edit_does():
    """Prereg J1: `support`, `overperform`, `sigma_j` and `register` are out of
    `pools._judgements_sha`, so editing one leaves every spec's
    `artefact_key` unchanged; editing `weights` still moves it (the detector
    can see)."""
    import os
    import pools
    body = ('[party.NEWP]\nweights = [1, 0, 0, 0]\nsupport = {sup}\n'
            'overperform = {ov}\nsigma_j = {sj}\nregister = "{rg}"\n')
    base = dict(sup=0.02, ov=1.0, sj=0.3, rg="§SJ1")
    t = _Target("joburg", "2026")
    shas = {}
    for label, kw in (("base", base), ("support", dict(base, sup=0.05)),
                      ("overperform", dict(base, ov=1.5)),
                      ("sigma_j", dict(base, sj=0.9)),
                      ("register", dict(base, rg="§SJ9"))):
        tmp, bound = _with_judgements(body.format(**kw), "joburg", "2026")
        try:
            shas[label] = pools._judgements_sha(t.city, t)
        finally:
            bound.restore()
            tmp.cleanup()
    assert len(set(shas.values())) == 1, shas
    tmp, bound = _with_judgements(body.format(**base).replace("[1, 0, 0, 0]",
                                                           "[0, 1, 0, 0]"),
                                "joburg", "2026")
    try:
        assert pools._judgements_sha(t.city, t) != shas["base"]
    finally:
        bound.restore()
        tmp.cleanup()


def test_the_applied_hash_covers_every_strength_key_and_only_the_applied_set():
    e = {"party": "X", "support": 0.02, "overperform": 1.0, "sigma_j": 0.4,
         "register": "§SJ1"}
    base = M.judgements_applied_sha([e])
    for k, v in (("support", 0.03), ("overperform", 1.1), ("sigma_j", 0.5),
                 ("register", "§SJ2"), ("party", "Y")):
        assert M.judgements_applied_sha([dict(e, **{k: v})]) != base, k
    assert M.judgements_applied_sha([]) != base
    assert M.judgements_applied_sha([]) == M.judgements_applied_sha([])


def test_the_judged_centre_is_exact_after_normalisation():
    centres = {"A": 0.5, "B": 0.3, "C": 0.2}
    sc = {"draw_law": "universal", "apply_judgements": True}
    import os
    body = '[party.C]\noverperform = 0.5\nsigma_j = 0.3\nregister = "§SJ1"\n'
    tmp, bound = _with_judgements(body, "joburg", "2026")
    try:
        rec = M._apply_strength_judgements(_Target("joburg", "2026"), sc,
                                           centres, "universal")
    finally:
        bound.restore()
        tmp.cleanup()
    tot = sum(centres.values())
    assert abs(centres["C"] / tot - 0.1) < 1e-12
    assert rec["applied"][0]["centre_judged"] == 0.1
    assert sc["_judgements_applied_sha"] == rec["judgements_sha"]
    # the switch off: nothing applied, recorded as ignored with the reason
    sc_off = {"draw_law": "universal", "apply_judgements": False}
    tmp, bound = _with_judgements(body, "joburg", "2026")
    try:
        c2 = {"A": 0.5, "B": 0.3, "C": 0.2}
        rec2 = M._apply_strength_judgements(_Target("joburg", "2026"), sc_off,
                                            c2, "universal")
    finally:
        bound.restore()
        tmp.cleanup()
    assert c2 == {"A": 0.5, "B": 0.3, "C": 0.2} and not rec2["applied"]
    assert rec2["ignored"] and "off" in rec2["ignored"][0]["reason"]


def register_rows(text: str) -> set[str]:
    """The `§SJ<n>` rows of JUDGEMENT-CALLS.md's strength section."""
    import re
    section = text.split("## SJ. Strength judgements", 1)
    if len(section) < 2:
        raise AssertionError("JUDGEMENT-CALLS.md has no strength section")
    body = section[1].split("\n## ", 1)[0]
    return set(re.findall(r"^\|\s*(§SJ\d+)\s*\|", body, flags=re.M))


def strength_entries(root: Path) -> dict[str, str]:
    """Every strength entry in ``root``'s judgements files: {file:party: register}."""
    import tomllib
    out = {}
    for f in sorted(root.glob("*.toml")):
        for party, body in (tomllib.loads(f.read_text()).get("party") or {}).items():
            if "support" in body or "overperform" in body:
                out[f"{f.name}:{party}"] = str(body.get("register", ""))
    return out


def register_faults(rows: set[str], entries: dict[str, str]) -> list[str]:
    out = [f"{k} names register row {v!r}, which does not exist"
           for k, v in entries.items() if v not in rows]
    named = set(entries.values())
    out += [f"register row {r} names no entry" for r in sorted(rows - named)]
    return out


def test_every_strength_entry_has_a_register_row_and_every_row_an_entry():
    """Prereg J4 / design v3 §11.2: the register guard over strength
    judgements, both directions. The live population is checked (today both
    are empty, and that is stated, not assumed), and a constructed violation in
    each direction is caught and goes quiet when fixed."""
    live_rows = register_rows((ROOT / "JUDGEMENT-CALLS.md").read_text())
    live = strength_entries(ROOT / "judgements")
    assert not register_faults(live_rows, live), register_faults(live_rows, live)
    files = list((ROOT / "judgements").glob("*.toml"))
    scanned(files, of=len(files), low=1.0, high=1.0,
            what="judgements files scanned for strength entries",
            denominator="judgements files on disk")
    text = "## SJ. Strength judgements\n| row |\n|---|\n| §SJ1 | X |\n\n## T\n"
    assert register_rows(text) == {"§SJ1"}
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "joburg-2026.toml").write_text(
            '[party.X]\nsupport = 0.02\nsigma_j = 0.3\nregister = "§SJ2"\n')
        faults = register_faults({"§SJ1"}, strength_entries(d))
        assert any("does not exist" in f for f in faults)
        assert any("names no entry" in f for f in faults)
        (d / "joburg-2026.toml").write_text(
            '[party.X]\nsupport = 0.02\nsigma_j = 0.3\nregister = "§SJ1"\n')
        assert not register_faults({"§SJ1"}, strength_entries(d))


# --------------------------------------------------------------------------
# the record file: refusals
# --------------------------------------------------------------------------

def test_the_record_refuses_missing_stale_and_wrong_variant():
    sc = copy.deepcopy(M.DEFAULTS)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for case in ("missing", "stale", "variant", "year", "good"):
            path = root / M.WIDTH_RECORD
            if path.exists():
                path.unlink()
            if case != "missing":
                key = M.width_record_key(processed=root)
                if case == "stale":
                    key = dict(key, record_sha="0" * 16)
                variant = M.width_record_variant(
                    dict(sc, level_shrink=0.0) if case == "variant" else sc)
                targets = {} if case == "year" else {"2026": FIXTURE_RECORD}
                path.write_text(json.dumps({"artefact_key": key, "variants": {
                    variant: {"targets": targets}}}))
            if case == "good":
                rec = M.read_width_record("2026", sc, processed=root)
                assert rec["curve"] == FIXTURE_RECORD["curve"]
                continue
            try:
                M.read_width_record("2026", sc, processed=root)
            except SystemExit:
                continue
            raise AssertionError(f"read_width_record accepted a {case} record")


def test_a_re_emit_with_no_code_change_marks_the_width_record_stale():
    """Step-6 item 7. The key covers the specs the record reads (by content,
    their `artefact_key` included), the live judgements of those city-years
    and the group-share record's key. Constructed under a scratch processed
    root: a record written under the live key is read; a changed spec key, a
    changed group-share key, and a spec that disappears each make
    `read_width_record` refuse; each reverted, it reads again. Population:
    the specs keyed are every (city, cycle) `width_record` fits on, both
    ways."""
    specs = W.record_specs()
    want = {(c, y) for c in W.record_cities()
            for y in {y for ys in W.FORWARD.values() for y in ys}}
    assert {(c, y) for c, y, _r in specs} == want and specs
    sc = copy.deepcopy(M.DEFAULTS)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        spec = root / specs[0][2]
        spec.parent.mkdir(parents=True, exist_ok=True)
        gs = root / "group_share_record.json"

        def put(spec_key="a", gs_key="g"):
            spec.write_text(json.dumps({"artefact_key": {"pools_sha": spec_key},
                                        "pools": {}}))
            gs.write_text(json.dumps({"artefact_key": {"record_sha": gs_key}}))

        def reads() -> bool:
            try:
                M.read_width_record("2026", sc, processed=root)
            except SystemExit as exc:
                assert "STALE" in str(exc), exc
                return False
            return True

        put()
        (root / M.WIDTH_RECORD).write_text(json.dumps({
            "artefact_key": M.width_record_key(processed=root),
            "variants": {M.width_record_variant(sc): {
                "targets": {"2026": FIXTURE_RECORD}}}}))
        assert reads()
        put(spec_key="b")
        assert not reads(), "a changed spec key was accepted"
        put()
        assert reads()
        put(gs_key="h")
        assert not reads(), "a changed group-share key was accepted"
        put()
        assert reads()
        spec.unlink()
        assert not reads(), "a vanished spec was accepted"
        put()
        assert reads()


def test_the_width_key_covers_the_results_the_fallback_and_the_centres_inputs():
    """Step-7 review item 3. Beyond the specs, the key covers every other
    input the record reads: the realised result file of each residual
    city-year (`record_result_files`: the 2021 files behind target 2026's
    rows), the raw files the 2011 fallback can read (`fallback_files`), the
    code of `compare_history` (`actual_shares`) and `theta_residual`, and
    `bye_value.json`'s key (`blended_centres`). Constructed: the raw root is
    a scratch tree of symlinks to the real files (nothing under `data/` is
    written), a record under the live key reads, and changing each input
    alone makes `read_width_record` refuse; reverted, it reads. Population:
    the result files are one per (city, cycle) of `record_specs`, both ways,
    and the fallback files are the calendar's elections up to 2006 in every
    metro."""
    import pools
    import levels
    import cityconfig
    res = W.record_result_files()
    assert {(c, y) for c, y, _p in res} == {(c, y) for c, y, _r in W.record_specs()}
    assert len(res) == len(W.record_specs()) and res
    fb = W.fallback_files()
    years = [y for y, e in cityconfig.CALENDAR.items()
             if e.results and int(y) <= 2006]
    assert len(fb) == len(years) * len(levels.METRO_CODES) and fb
    assert all(int(f.name[3:7]) <= 2006 for f in fb)
    sc = copy.deepcopy(M.DEFAULTS)
    real_data, real_code_sha = W.DATA, pools._code_sha
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "processed"
        raw = Path(tmp) / "raw"
        root.mkdir()
        raw.mkdir()
        for f in {p for _c, _y, p in res} | set(fb):
            if f.exists():
                (raw / f.name).symlink_to(f)
        by = root / "bye_value.json"
        moved = {"name": None}

        def code_sha(path):
            if Path(path).name == moved["name"]:
                return "moved"
            return real_code_sha(path)

        def reads() -> bool:
            try:
                M.read_width_record("2026", sc, processed=root)
            except SystemExit as exc:
                assert "STALE" in str(exc), exc
                return False
            return True

        W.DATA = raw
        pools._code_sha = code_sha
        try:
            by.write_text(json.dumps({"artefact_key": {"bye": "a"}}))
            (root / M.WIDTH_RECORD).write_text(json.dumps({
                "artefact_key": M.width_record_key(processed=root),
                "variants": {M.width_record_variant(sc): {
                    "targets": {"2026": FIXTURE_RECORD}}}}))
            assert reads()
            for target in (res[-1][2], fb[0]):
                link = raw / target.name
                link.unlink()
                link.write_bytes(target.read_bytes() + b"\n")
                assert not reads(), f"a changed {target.name} was accepted"
                link.unlink()
                link.symlink_to(target)
                assert reads()
            for name in ("compare_history.py", "theta_residual.py"):
                moved["name"] = name
                assert not reads(), f"a changed {name} was accepted"
                moved["name"] = None
                assert reads()
            by.write_text(json.dumps({"artefact_key": {"bye": "b"}}))
            assert not reads(), "a changed bye_value key was accepted"
            by.write_text(json.dumps({"artefact_key": {"bye": "a"}}))
            assert reads()
        finally:
            W.DATA = real_data
            pools._code_sha = real_code_sha


def test_the_judgements_file_is_found_from_any_directory_and_a_forecast_needs_it():
    """Step-7 review item 5. `pools.lineage_path` resolves under the
    repository's `judgements/`, so the hash a forecast declares is the same
    whether the process runs from the root, from `src/` or from elsewhere
    (it used to read `{}` away from the root and declare the empty set). A
    FORECAST whose file is missing refuses; a backtest's missing file is the
    empty set, as the judgements are ignored there."""
    import pools
    t = _Target("joburg", "2026")
    cwd = os.getcwd()
    want = (ROOT / "judgements" / "joburg-2026.toml").resolve()
    shas = set()
    try:
        for where in (ROOT, ROOT / "src", Path(tempfile.gettempdir())):
            os.chdir(where)
            assert pools.lineage_path(t.city, t).resolve() == want
            shas.add(M.live_judgements_sha("joburg", "2026", dict(M.DEFAULTS)))
    finally:
        os.chdir(cwd)
    assert want.exists() and len(shas) == 1, shas
    with tempfile.TemporaryDirectory() as tmp:
        real = pools.JUDGEMENTS_DIR
        pools.JUDGEMENTS_DIR = Path(tmp)
        try:
            try:
                M.strength_judgements(t.city, t)
            except SystemExit as exc:
                assert "does not exist" in str(exc), exc
            else:
                raise AssertionError("a forecast ran without its judgements file")
            held = _Target("joburg", "2021")
            assert M.strength_judgements(held.city, held) == ([], [])
        finally:
            pools.JUDGEMENTS_DIR = real


def test_the_emit_reads_which_parties_are_judged_and_never_how_strong():
    """Step-7 review item 4 (JUDGEMENT-CALLS §L2). `pools.judged_parties`
    names the parties carrying `support` or `overperform` on a FORECAST and
    none on a backtest (which ignores judgements). `_judgements_sha` hashes
    that membership: adding `support` to a party moves the spec key,
    changing its value does not. Mutation probes: dropping the membership
    marker leaves the key unmoved by an added `support` (red); dropping the
    held-target rule names a party on a backtest (red)."""
    import pools
    lineage = {"A": {"support": 0.02, "sigma_j": 0.3, "register": "§SJ1"},
               "B": {"overperform": 1.5, "sigma_j": 0.3, "register": "§SJ1"},
               "C": {"weights": [1, 0]}, "D": {"baseline_share": 0.01}}
    assert pools.judged_parties(lineage, _Target("joburg", "2026")) == {"A", "B"}
    assert pools.judged_parties(lineage, _Target("joburg", "2021")) == frozenset()
    t = _Target("joburg", "2026")
    bodies = {"none": '[party.NEWP]\nweights = [1, 0, 0, 0]\n',
              "low": ('[party.NEWP]\nweights = [1, 0, 0, 0]\nsupport = 0.02\n'
                      'sigma_j = 0.3\nregister = "§SJ1"\n'),
              "high": ('[party.NEWP]\nweights = [1, 0, 0, 0]\nsupport = 0.09\n'
                       'sigma_j = 0.3\nregister = "§SJ1"\n')}
    shas = {}
    for label, body in bodies.items():
        tmp, bound = _with_judgements(body, "joburg", "2026")
        try:
            shas[label] = pools._judgements_sha(t.city, t)
        finally:
            bound.restore()
            tmp.cleanup()
    assert shas["low"] == shas["high"], "a strength VALUE moved the spec key"
    assert shas["none"] != shas["low"], "adding `support` left the spec key"


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
