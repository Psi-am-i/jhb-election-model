"""Re-weighting the published draws: exact when untouched, and honest when moved.

Build step S4 of `audits/2026-09-28-interactive-architecture/PLAN.md`;
`src/reweight.py` is the engine the page runs under Pyodide. What this module
proves:

1. UNIFORM WEIGHTS ARE THE PUBLISHED FORECAST, BIT FOR BIT. From the draw file
   of a fresh export at the published seed and draws: every party's median,
   p5 and p95 in `forecast_summary.json`, its structural probabilities and
   median threshold, and every ward's Jeffreys win probability in
   `ward_winner_probs.csv`. A poll at infinite error is exactly uniform.
2. THE TURNOUT TILT AGREES WITH MOVING TURNOUT IN THE MODEL. Black African
   turnout +5 points, the other three pools held at their means, against a
   paired re-run of the model with that pool's drawn turnout shifted by 0.05
   after the IPF on the same seed. Pre-registered in
   `prereg/2026-09-28-reweight-against-paired-rerun.md` (P1: DA, ANC, EFF,
   PA and MK within 2 SE; P2: every party whose seats vary within 3 SE). The
   SE combines the tilt's linearised SE (`reweight.weighted_mean_se`) with
   the paired re-run's sd/sqrt(n), in quadrature.
3. THE REFUSALS FIRE. A constructed case below the effective-draw floor, and a
   target outside the draws, are refused; a modest target is not.
4. THE WEIGHTED STATISTICS REDUCE CORRECTLY on constructed inputs, including
   numpy's own percentile at every quantile, and are mirror-symmetric.
5. TWO CONTROLS AT ONCE HIT WHAT THE READER ASKED FOR. A turnout tilt solved
   on a poll's weights meets its turnout target exactly, on a constructed case
   where turnout and poll agreement are correlated — the case in which
   multiplying a tilt solved alone by the poll's weights misses (blind review
   A7). The poll has one control, its error (A8).
6. EACH QUANTILE REPORTS WHAT IT RESTS ON, which can be far less than Kish's
   count for the weights as a whole.
7. THE S6 LANE R ADDITIONS (`audits/2026-09-30-interactive-s6/SPEC-v2.md`),
   each on a constructed case that fails when the function is broken: the
   trust dial's mapping and its endpoints (decision 2), `poll_weights` under
   trust, `page_polls` admitting exactly what `polling.screen` admits (F8),
   `combine_polls` keeping every party two polls name (F8), `Refused` on the
   polled base (F9), `turnout_tilt(pin_to=)` (F4, F10), `sampling_se` against
   a bootstrap and against repeated samples on INTEGER values (F2), and the
   owner's per-figure precision rule, `MAX_FIGURE_SE_SEATS` (F17 as
   re-decided 2026-09-30). On the published draws: uniform weights withhold
   no published figure, and a tilt past the draws' reach does.

⚠️ The tilt matches a MEAN and the re-run moves the whole distribution. Check
2 is what licenses the page to present one as the other, at this size of move
and no further; it says nothing about +8 points, where the draws run out.

Two full model runs go in parallel subprocesses, so this module takes minutes.
"""

from __future__ import annotations

import csv
import json
import math
import os
import pickle
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import reweight as R  # noqa: E402

PROCESSED = ROOT / "data" / "processed"
SUMMARY = PROCESSED / "forecast_summary.json"
WARD_PROBS = PROCESSED / "ward_winner_probs.csv"
SPEC = PROCESSED / "pools_2026.json"
POOL = "Black African"
SHIFT = 0.05
#: The parties PLAN.md §3 reported for this comparison; P1 of the
#: pre-registration is stated over them. Every party is then tested alike (P2).
PLAN_PARTIES = ("DA", "ANC", "EFF", "PA", "MK")

# The paired re-run: the export's own `_run_law`, with the named pool's drawn
# turnout raised by SHIFT. Identified by its band, not its position. The wrapper
# draws nothing, so every other random number lands where it did in the base.
_SHIFTED = r'''
import json, pickle, sys
src, out, pool, shift, seed, draws = sys.argv[1:7]
sys.path.insert(0, src)
import montecarlo as mc
import export_draws as E
band = tuple(float(x) for x in json.load(open("data/processed/pools_2026.json"))
             ["pools"][pool]["turnout"])
real = mc.correlated_triangular
hits = [0]
def shifted(rng, spec, z_common, rho):
    value = real(rng, spec, z_common, rho)
    if tuple(float(x) for x in spec) == band:
        hits[0] += 1
        return value + float(shift)
    return value
mc.correlated_triangular = shifted
run = E._run_law("deduct", "joburg", "2026", int(draws), int(seed))
run["hits"] = hits[0]
with open(out, "wb") as handle:
    pickle.dump(run, handle)
'''

_STATE: dict = {}


def _published_run() -> tuple[int, int]:
    summary = json.loads(SUMMARY.read_text())
    return int(summary["scenario"]["seed"]), int(summary["_draws"])


def _runs() -> dict:
    """A statute-only export and the paired shifted run, once, in parallel."""
    if _STATE:
        return _STATE
    import montecarlo as M
    seed, draws = _published_run()
    tmp = tempfile.TemporaryDirectory(prefix="reweight_test_")
    base = Path(tmp.name)
    worker = base / "shifted.py"
    worker.write_text(_SHIFTED, encoding="utf-8")
    env = dict(os.environ, PYTHONHASHSEED=str(M.HASH_SEED))
    commands = {
        "export": [sys.executable, str(ROOT / "src" / "export_draws.py"),
                   "--city", "joburg", "--target", "2026", "--laws", "deduct",
                   "--seed", str(seed), "--draws", str(draws),
                   "--out", str(base / "out")],
        "shifted": [sys.executable, str(worker), str(ROOT / "src"),
                    str(base / "shifted.pkl"), POOL, str(SHIFT), str(seed),
                    str(draws)],
    }

    def launch(cmd):
        done = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True,
                              text=True, timeout=3600)
        if done.returncode != 0:
            raise AssertionError(f"{cmd[1]} failed:\n{done.stderr[-4000:]}")

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(launch, commands.values()))
    manifest = json.loads((base / "out" / "manifest.json").read_text())
    arrays = R.unpack((base / "out" / "base.bin").read_bytes(), manifest)
    with (base / "shifted.pkl").open("rb") as handle:
        shifted = pickle.load(handle)
    _STATE.update(tmp=tmp, manifest=manifest, arrays=arrays, shifted=shifted,
                  seed=seed, draws=draws)
    return _STATE


def _pools(manifest) -> list[str]:
    return next(b for b in manifest["blocks"]
                if b["name"] == "pool_turnout")["columns"]


# -- 1: uniform weights are the published forecast ---------------------------

def _party_figures(arrays, manifest, w) -> dict[str, dict[str, float]]:
    seats = arrays["seats/deduct"]
    return {p: {"median": R.weighted_quantile(seats[:, j], w, 0.5),
                "p5": R.weighted_quantile(seats[:, j], w, 0.05),
                "p95": R.weighted_quantile(seats[:, j], w, 0.95)}
            for j, p in enumerate(manifest["parties"])}


def _mismatches(published: dict, computed: dict) -> list[str]:
    bad = []
    for party, figs in published.items():
        for k in ("median", "p5", "p95"):
            if party not in computed or computed[party][k] != figs[k]:
                bad.append(f"{party}.{k}")
    return bad


def test_uniform_weights_give_every_published_seat_figure_exactly():
    st = _runs()
    arrays, manifest = st["arrays"], st["manifest"]
    summary = json.loads(SUMMARY.read_text())
    w = R.uniform(st["draws"])
    computed = _party_figures(arrays, manifest, w)
    # 0. the right population, both directions: every published party is in the
    #    file, and every file party that `main` would publish is published
    seats = arrays["seats/deduct"].astype(np.int64)
    would_publish = {p for j, p in enumerate(manifest["parties"])
                     if seats[:, j].mean() >= 0.4}
    assert set(summary["parties"]) == would_publish
    scanned(len(summary["parties"]), of=len(manifest["parties"]), low=0.05,
            high=1.0, what="published parties compared",
            denominator="the file's seat-winning parties")
    assert _mismatches(summary["parties"], computed) == []
    # 2. it can see a one-seat change, and goes quiet when it is reverted
    party = next(iter(summary["parties"]))
    kept = computed[party]["median"]
    computed[party]["median"] = kept + 1.0
    assert _mismatches(summary["parties"], computed) == [f"{party}.median"]
    computed[party]["median"] = kept
    assert _mismatches(summary["parties"], computed) == []


def test_uniform_weights_give_the_published_structural_figures_exactly():
    st = _runs()
    arrays, manifest = st["arrays"], st["manifest"]
    structural = json.loads(SUMMARY.read_text())["structural"]
    w = R.uniform(st["draws"])
    parties = manifest["parties"]
    seats = arrays["seats/deduct"].astype(np.int64)
    council = arrays["council/deduct"].astype(np.int64)
    threshold, total = council[:, 0], seats.sum(axis=1)
    col = {p: j for j, p in enumerate(parties)}

    def without(*names):
        return total - sum(seats[:, col[n]] for n in names)

    means = seats[:, :-1].mean(axis=0)
    ranked = sorted(range(len(parties)), key=lambda j: -means[j])
    largest = np.array(ranked)[seats[:, ranked].argmax(axis=1)]
    field = without("ANC", "EFF", "MK")
    ours = {
        "P(some majority without ANC, EFF and MK)":
            R.weighted_probability(field >= threshold, w),
        "P(some majority without the ANC)":
            R.weighted_probability(without("ANC") >= threshold, w),
        "P(some majority without the DA)":
            R.weighted_probability(without("DA") >= threshold, w),
        "P(DA is the largest single party)":
            R.weighted_probability(largest == col["DA"], w),
        "P(ANC is the largest single party)":
            R.weighted_probability(largest == col["ANC"], w),
        "field without ANC, EFF and MK: median seats":
            R.weighted_quantile(field, w, 0.5),
    }
    differ = {k: (v, structural[k]) for k, v in ours.items()
              if structural[k] != v}
    assert not differ, differ
    assert int(R.weighted_quantile(threshold, w, 0.5)) == \
        json.loads(SUMMARY.read_text())["threshold_median"]


def test_uniform_weights_give_every_published_ward_probability_exactly():
    st = _runs()
    arrays, manifest = st["arrays"], st["manifest"]
    codes = manifest["ward_parties"]
    wards = next(b for b in manifest["blocks"]
                 if b["name"] == "ward_winner")["columns"]
    w = R.uniform(st["draws"])
    probs = R.ward_win_probability(arrays["ward_winner"], w, len(codes))
    counts = np.stack([np.bincount(arrays["ward_winner"][:, j],
                                   minlength=len(codes))
                       for j in range(len(wards))])
    # the published formula, bit for bit, where a party won the ward at all
    jeffreys = (counts + 0.5) / (st["draws"] + 1.0)
    assert np.array_equal(probs[counts > 0], jeffreys[counts > 0])
    with WARD_PROBS.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [r["ward"] for r in rows] == wards
    differ = []
    for j, row in enumerate(rows):
        published = dict(item.split(":") for item in row["dist"].split("|"))
        ours = {codes[c]: f"{probs[j, c]:.4f}"
                for c in np.flatnonzero(counts[j])}
        if published != ours:
            differ.append(row["ward"])
    scanned(len(rows), of=len(wards), low=1.0, high=1.0,
            what="wards compared", denominator="the file's wards")
    assert not differ, differ


def test_an_infinite_poll_error_is_uniform_exactly_and_a_finite_one_is_not():
    st = _runs()
    arrays, manifest = st["arrays"], st["manifest"]
    columns = manifest["parties"] + ["OTHER"]
    # a constructed poll: the five parties with the largest mean PR share, at
    # equal shares (chosen by a rule, not by name)
    means = arrays["pr_share"][:, :-1].mean(axis=0)
    poll = {manifest["parties"][j]: 1.0 for j in np.argsort(-means)[:5]}
    w0 = R.poll_weights(arrays["pr_share"], columns, poll, sd=math.inf)
    assert np.array_equal(w0, R.uniform(st["draws"]))
    w1 = R.poll_weights(arrays["pr_share"], columns, poll, sd=0.05)
    assert not np.array_equal(w1, w0)
    assert R.effective_draws(w1) < st["draws"]


# -- 2: the turnout tilt against a paired re-run ------------------------------

def test_the_paired_rerun_moved_exactly_the_named_pool():
    """The positive control: the shift landed, on the right pool, and only there."""
    st = _runs()
    base = st["arrays"]["pool_turnout"]
    shifted = np.asarray(st["shifted"]["pool_turnouts"])
    names = _pools(st["manifest"])
    j = names.index(POOL)
    assert st["shifted"]["pool_names"] == names
    assert st["shifted"]["hits"] == st["draws"]
    assert np.allclose(shifted[:, j] - base[:, j], SHIFT, rtol=0, atol=1e-15)
    others = [k for k in range(len(names)) if k != j]
    assert np.array_equal(shifted[:, others], base[:, others])


def _comparison(st) -> list[tuple[str, float, float, float]]:
    """(party, re-weighted change, re-run change, combined SE) per varying party."""
    arrays, manifest = st["arrays"], st["manifest"]
    names = _pools(manifest)
    shift = np.zeros(len(names))
    shift[names.index(POOL)] = SHIFT
    w = R.turnout_tilt(arrays["pool_turnout"], shift)
    seats = arrays["seats/deduct"].astype(float)
    universe = st["shifted"]["universe"]
    moved = np.asarray(st["shifted"]["seats"], dtype=float)
    n = seats.shape[0]
    out = []
    for j, party in enumerate(manifest["parties"]):
        s = seats[:, j]
        if s.std() == 0:
            continue
        mw, se_w = R.weighted_mean_se(s, w)
        paired = moved[:, universe.index(party)] - s
        se = float(np.hypot(se_w, paired.std() / np.sqrt(n)))
        out.append((party, mw - s.mean(), float(paired.mean()), se))
    return out


def _outside(rows, k: float) -> list[str]:
    return [p for p, dw, dr, se in rows if abs(dw - dr) > k * se]


def test_black_african_plus_five_points_matches_a_paired_rerun():
    st = _runs()
    rows = _comparison(st)
    for p, dw, dr, se in rows:
        if p in PLAN_PARTIES or abs(dr) >= 0.5:
            print(f"  {p:<12s} re-run {dr:+.2f}  re-weighted {dw:+.2f}  "
                  f"SE {se:.2f}  z {(dw - dr) / se:+.2f}")
    # 0. the right population: every party whose seats vary, and the five
    #    PLAN.md named are among them
    assert set(PLAN_PARTIES) <= {r[0] for r in rows}
    # 1. it looked
    scanned(len(rows), of=len(st["manifest"]["parties"]), low=0.3, high=1.0,
            what="parties compared", denominator="the file's seat-winning parties")
    # P1 and P2 of the pre-registration
    assert _outside([r for r in rows if r[0] in PLAN_PARTIES], 2.0) == []
    assert _outside(rows, 3.0) == []
    # 2. it can see: one party's re-run moved by four SE is caught, then reverted
    p, dw, dr, se = rows[0]
    rows[0] = (p, dw, dr + 4.0 * se, se)
    assert _outside(rows, 3.0) == [p]
    rows[0] = (p, dw, dr, se)
    assert _outside(rows, 3.0) == []


def test_the_headline_setting_keeps_enough_draws_and_one_pool_alone_does_less():
    st = _runs()
    t = st["arrays"]["pool_turnout"]
    names = _pools(st["manifest"])
    j = names.index(POOL)
    shift = np.zeros(len(names))
    shift[j] = SHIFT
    joint = R.turnout_tilt(t, shift)
    ess = R.require_effective(joint)
    print(f"  effective draws at {POOL} +{SHIFT:.0%}, others held: {ess:.0f}")
    # the other three really are held at their means
    held = (joint / joint.sum()) @ t - t.mean(axis=0)
    assert abs(held[j] - SHIFT) < 1e-9
    assert np.max(np.abs(np.delete(held, j))) < 1e-9
    # P5: selecting on one pool alone lifts all four and moves the DA by less
    alone = R._tilt(t[:, [j]], np.array([t[:, j].mean() + SHIFT]),
                    tolerance=1e-10, steps=200)
    da = st["manifest"]["parties"].index("DA")
    s = st["arrays"]["seats/deduct"][:, da].astype(float)
    move_joint = R.weighted_mean_se(s, joint)[0] - s.mean()
    move_alone = R.weighted_mean_se(s, alone)[0] - s.mean()
    print(f"  DA mean seats: joint {move_joint:+.2f}, one pool alone "
          f"{move_alone:+.2f}")
    assert abs(move_alone) < 0.5 * abs(move_joint)


# -- 3: the refusals fire -----------------------------------------------------

def _constructed_turnouts(n: int = 5000) -> np.ndarray:
    rng = np.random.default_rng(7)
    common = rng.standard_normal(n)
    return np.column_stack([0.4 + 0.05 * (0.8 * common + 0.6 * rng.standard_normal(n))
                            for _ in range(4)])


def test_the_refusal_floor_is_read_at_call_time():
    """Rebinding MIN_EFFECTIVE_DRAWS reaches require_effective (CLASS 13)."""
    w = np.ones(300)
    kept = R.MIN_EFFECTIVE_DRAWS
    try:
        R.MIN_EFFECTIVE_DRAWS = 301
        try:
            R.require_effective(w)
        except R.Refused:
            pass
        else:
            raise AssertionError("a rebound floor did not reach the call")
        R.MIN_EFFECTIVE_DRAWS = 299
        assert R.require_effective(w) == 300.0
    finally:
        R.MIN_EFFECTIVE_DRAWS = kept
    assert R.require_effective(w, floor=300) == 300.0


def test_the_refusal_floor_fires_below_it_and_not_above():
    t = _constructed_turnouts()
    modest = R.turnout_tilt(t, [0.01, 0.0, 0.0, 0.0])
    assert R.require_effective(modest) >= R.MIN_EFFECTIVE_DRAWS
    # 1.6 standard deviations on one pool with the other three held: the pools
    # are correlated, so few draws carry that combination
    steep = R.turnout_tilt(t, [0.08, 0.0, 0.0, 0.0])
    assert R.effective_draws(steep) < R.MIN_EFFECTIVE_DRAWS
    try:
        R.require_effective(steep)
    except R.Refused as exc:
        assert "effective draws" in str(exc)
    else:
        raise AssertionError("a setting below the floor was not refused")


def test_a_target_outside_the_draws_is_refused_not_extrapolated():
    t = _constructed_turnouts()
    beyond = t[:, 0].max() - t[:, 0].mean() + 0.01
    for shift in ([beyond, 0, 0, 0], [0, 0, 0, -1.0]):
        try:
            R.turnout_tilt(t, shift)
        except R.Refused:
            continue
        raise AssertionError(f"shift {shift} leaves the draws and was answered")


def test_a_single_pool_target_is_not_offered():
    t = _constructed_turnouts()
    for bad in ([0.02], [0.02, 0.0], [0.02, np.nan, 0.0, 0.0]):
        try:
            R.turnout_tilt(t, bad)
        except ValueError:
            continue
        raise AssertionError(f"shift {bad} was accepted without a target per pool")
    assert np.array_equal(R.turnout_tilt(t, [0, 0, 0, 0]), R.uniform(len(t)))


# -- 4: the statistics, on constructed inputs ---------------------------------

def test_weighted_quantile_is_numpys_percentile_under_constant_weights():
    rng = np.random.default_rng(3)
    for n in (2, 3, 10, 999, 5000):
        x = rng.integers(0, 40, size=n)
        for c in (1.0, 0.1, 7.0):
            w = np.full(n, c)
            for q in (0, 0.05, 0.25, 0.5, 0.5001, 0.75, 0.95, 1):
                assert R.weighted_quantile(x, w, q) == float(np.percentile(x, 100 * q)), (n, c, q)
            assert R.weighted_quantile(x, w, 0.5) == float(np.median(x))
        y = rng.standard_normal(n)
        for q in (0.05, 0.5, 0.95):
            assert R.weighted_quantile(y, np.ones(n), q) == float(np.quantile(y, q))


def test_weighted_quantile_mirrors_and_ignores_a_draw_of_zero_weight():
    rng = np.random.default_rng(4)
    x = rng.standard_normal(301)
    w = rng.uniform(0.1, 2.0, size=301)
    for q in (0.1, 0.5, 0.9):
        assert np.isclose(R.weighted_quantile(x, w, q),
                          -R.weighted_quantile(-x, w, 1 - q), rtol=0, atol=1e-12)
    # a draw of zero weight is absent, not a draw at the edge
    xi = np.array([1.0, 2.0, 3.0, 4.0, 100.0])
    for q in (0.05, 0.5, 0.95):
        assert R.weighted_quantile(xi, [1, 1, 1, 1, 0], q) == \
            float(np.quantile(xi[:4], q))
    # more weight on a draw pulls the quantile toward it
    assert R.weighted_quantile(xi[:4], [1, 3, 1, 1], 0.5) < \
        R.weighted_quantile(xi[:4], [1, 1, 1, 1], 0.5)


def test_poll_weights_use_the_polled_base_and_treat_every_party_alike():
    rng = np.random.default_rng(5)
    shares = rng.dirichlet(np.ones(4) * 5, size=400)
    cols = ["A", "B", "C", "D"]
    # the same poll in any units gives the same weights
    a = R.poll_weights(shares, cols, {"A": 0.3, "B": 0.2}, sd=0.05)
    b = R.poll_weights(shares, cols, {"A": 30, "B": 20}, sd=0.05)
    assert np.allclose(a, b, rtol=1e-12, atol=0)
    # relabelling the parties relabels nothing else: no party is special
    perm = [2, 3, 0, 1]
    c = R.poll_weights(shares[:, perm], [cols[i] for i in perm],
                       {"A": 0.3, "B": 0.2}, sd=0.05)
    assert np.allclose(a, c, rtol=1e-12, atol=0)
    try:
        R.poll_weights(shares, cols, {"Q": 0.3}, sd=0.05)
    except R.Refused:
        pass
    else:
        raise AssertionError("a poll naming a party the draws lack was accepted")


def test_the_poll_has_one_control_and_it_moves_the_weights_monotonically():
    """A8: an sd and a trust exponent were one degree of freedom. The control is
    now trust (decision 2) or sd, exactly one of them, never both and never
    neither."""
    rng = np.random.default_rng(8)
    shares = rng.dirichlet(np.ones(4) * 5, size=2000)
    cols, poll = ["A", "B", "C", "D"], {"A": 0.35, "B": 0.25}
    for bad in ({"sd": 0.05, "trust": 0.5}, {"sigma": 0.05}, {}):
        try:
            R.poll_weights(shares, cols, poll, **bad)
        except TypeError:
            continue
        raise AssertionError(f"poll_weights accepted {sorted(bad)}")
    for bad in (0.0, -0.01, math.nan):
        try:
            R.poll_weights(shares, cols, poll, sd=bad)
        except ValueError:
            continue
        raise AssertionError(f"sd={bad} was accepted")
    # the one control spans the whole range: from the published forecast at
    # infinity to ever fewer draws as the error shrinks
    ess = [R.effective_draws(R.poll_weights(shares, cols, poll, sd=sd))
           for sd in (math.inf, 0.5, 0.1, 0.05, 0.02, 0.01)]
    assert ess[0] == 2000.0
    assert all(a > b for a, b in zip(ess, ess[1:])), ess


def _correlated_draws(n: int = 5000):
    """Turnout and party A's share driven by ONE common factor, as in the model.

    A high-turnout draw is a draw where A does well, so a poll putting A high
    selects high-turnout draws. The constructed case the old test lacked: it
    drew shares independently of turnout, where multiplying weights happens to
    work.
    """
    rng = np.random.default_rng(12)
    common = rng.standard_normal(n)
    t = np.column_stack([0.4 + 0.05 * (0.8 * common + 0.6 * rng.standard_normal(n))
                         for _ in range(4)])
    a = 0.35 + 0.04 * (0.7 * common + 0.7 * rng.standard_normal(n))
    b = 0.25 + 0.03 * rng.standard_normal(n)
    shares = np.column_stack([a, b, 1.0 - a - b])
    return t, shares, ["A", "B", "C"]


def _turnout_miss(t, w) -> np.ndarray:
    """Weighted mean turnout minus the published (uniform) mean, per pool."""
    return (w / w.sum()) @ t - t.mean(axis=0)


def test_a_tilt_solved_on_the_poll_hits_its_target_and_one_multiplied_in_misses():
    t, shares, cols = _correlated_draws()
    poll = R.poll_weights(shares, cols, {"A": 0.38, "B": 0.25}, sd=0.03)
    shift = np.array([0.01, 0.0, 0.0, 0.0])
    # (0) the construction is what it claims: the poll alone moves turnout
    assert np.all(_turnout_miss(t, poll) > 0.005)
    # (a) the old behaviour — tilt solved on uniform, poll multiplied in —
    #     misses the requested turnout on every pool. This is the leg that
    #     shows the test can see A7.
    old = R.turnout_tilt(t, shift) * poll
    assert np.all(np.abs(_turnout_miss(t, old) - shift) > 0.003), \
        _turnout_miss(t, old) - shift
    # (b) solved on the poll: every pool exactly on target, the poll kept
    both = R.turnout_tilt(t, shift, base=poll)
    assert both.max() == 1.0
    assert np.max(np.abs(_turnout_miss(t, both) - shift)) < 1e-9
    assert R.effective_draws(both) < R.effective_draws(poll)
    # (c) a uniform base is no base, and an infinite poll error is uniform
    assert np.allclose(R.turnout_tilt(t, shift, base=R.uniform(len(t))),
                       R.turnout_tilt(t, shift), rtol=0, atol=1e-12)
    untouched = R.poll_weights(shares, cols, {"A": 0.38, "B": 0.25},
                               sd=math.inf)
    assert np.array_equal(untouched, R.uniform(len(t)))
    # (d) with a poll on, a zero shift holds turnout at its published mean
    held = R.turnout_tilt(t, np.zeros(4), base=poll)
    assert np.max(np.abs(_turnout_miss(t, held))) < 1e-9
    # (e) a draw the base gives no weight keeps none
    zeroed = poll.copy()
    zeroed[:10] = 0.0
    assert np.all(R.turnout_tilt(t, shift, base=zeroed)[:10] == 0.0)
    try:
        R.turnout_tilt(t, shift, base=np.zeros(len(t)))
    except R.Refused:
        pass
    else:
        raise AssertionError("a base leaving no draw any weight was answered")


def test_combine_polls_keeps_every_party_two_polls_name_and_reports_the_spread():
    """F8: one poll naming fewer parties must not delete the rest from all."""
    p1 = {"A": 30, "B": 20, "C": 50}            # renormalised: .3 .2 .5
    p2 = {"A": 0.2, "B": 0.2, "C": 0.4, "D": 0.2}
    p3 = {"id": "rec", "numbers": {"A": 0.3, "B": 0.1}}   # a register record
    avg, spread = R.combine_polls([p1, p2, p3])
    # C is named by two polls and kept; D by one and left out. The old rule —
    # the intersection — would have kept A and B only.
    assert set(avg) == {"A", "B", "C"}
    assert np.isclose(avg["C"], (0.5 + 0.4) / 2)
    assert np.isclose(avg["A"], (0.3 + 0.2 + 0.75) / 3)
    assert np.isclose(avg["B"], (0.2 + 0.2 + 0.25) / 3)
    assert np.allclose(spread["A"], (0.2, 0.75))
    assert np.allclose(spread["C"], (0.4, 0.5))
    # each poll on its own base: A in p3 is .3/.4, not .3
    assert np.isclose(spread["A"][1], 0.75)
    # one poll is itself, renormalised, and its spread is its one value
    one, one_spread = R.combine_polls([p1])
    assert one == {"A": 0.3, "B": 0.2, "C": 0.5}
    assert one_spread["C"] == (0.5, 0.5)
    # no party named by two polls: refused, not an empty average
    try:
        R.combine_polls([{"A": 1.0}, {"B": 1.0}])
    except R.Refused:
        pass
    else:
        raise AssertionError("polls with no party in common were combined")
    try:
        R.combine_polls([{"A": 0.0}, {"A": 0.0}])
    except R.Refused:
        pass
    else:
        raise AssertionError("a poll giving its parties no share was combined")


def test_a_quantile_reports_its_own_effective_draws():
    rng = np.random.default_rng(13)
    n = 5000
    x = rng.standard_normal(n)
    # uniform: every quantile rests on exactly the draw count
    for q in (0.05, 0.5, 0.95):
        ess_q, se = R.quantile_effective_draws(x, np.ones(n), q)
        assert np.isclose(ess_q, n, rtol=1e-12), (q, ess_q)
        assert np.isclose(se, np.sqrt(q * (1 - q) / n), rtol=0.05)
    assert R.tail_effective_draws(x, np.ones(n), 0.05) == \
        float((x <= np.percentile(x, 5)).sum())
    # constructed: the weights as a whole are healthy, but the lower tail is
    # carried by eight heavy draws. Kish's count stays in the thousands; the
    # 5th percentile's level and value both rest on far fewer.
    w = np.ones(n)
    tail = np.flatnonzero(x < -1.645)
    w[tail] = 0.0
    w[tail[:8]] = 31.0
    kish = R.effective_draws(w)
    ess_q, se = R.quantile_effective_draws(x, w, 0.05)
    assert kish > 1000, kish
    assert ess_q < 0.25 * kish, (kish, ess_q)
    assert R.tail_effective_draws(x, w, 0.05) < 10
    # the upper tail of the same weights is not starved, and says so
    ess_hi, _ = R.quantile_effective_draws(x, w, 0.95)
    assert ess_hi > 0.9 * kish, (ess_hi, kish)
    assert R.tail_effective_draws(x, w, 0.95) > 200
    # one side only: nothing to estimate
    assert R.quantile_effective_draws(np.ones(10), np.ones(10), 0.05)[0] == 0.0


def test_a_figure_under_a_poll_says_what_it_is():
    rng = np.random.default_rng(14)
    x = rng.integers(20, 60, size=1000).astype(float)
    shares = rng.dirichlet(np.ones(3) * 5, size=1000)
    poll = R.poll_weights(shares, ["A", "B", "C"], {"A": 0.5, "B": 0.2},
                          sd=0.05)
    polled = R.figure(x, poll, 0.05, poll=True)
    plain = R.figure(x, R.uniform(1000), 0.05, poll=False)
    assert polled["label"] == R.POLL_LABEL == "the model's draws nearest this poll"
    assert plain["label"] is None
    assert plain["withheld"] is False and polled["withheld"] is False
    assert plain["value"] == float(np.percentile(x, 5))
    assert plain["sampling_se"] == R.sampling_se(x, R.uniform(1000), 0.05)
    assert plain["effective_draws"] == 1000.0
    assert polled["effective_draws"] < plain["effective_draws"]
    assert polled["quantile_effective_draws"] < plain["quantile_effective_draws"]
    assert polled["tail_effective_draws"] < plain["tail_effective_draws"]


def test_ward_win_probability_under_weights_uses_the_effective_sample():
    winners = np.array([[0], [0], [1], [1]])
    w = np.array([1.0, 1.0, 1.0, 3.0])
    p = R.ward_win_probability(winners, w, 2)
    ess = R.effective_draws(w)
    assert np.isclose(p[0, 1], (ess * 4 / 6 + 0.5) / (ess + 1))
    assert np.isclose(p[0].sum(), (ess + 1.0) / (ess + 1.0))


# -- 7: S6 lane R -------------------------------------------------------------

def _record(**extra) -> dict:
    """A constructed register record that `polling.validate` accepts."""
    rec = {"id": "constructed", "scope": "metro", "city": "joburg",
           "house": "H", "n": 800, "n_basis": "standalone",
           "fieldwork_end": "2026-07-01",
           "numbers": {"A": 0.35, "B": 0.25}, "asof": "2026-11-04"}
    rec.update(extra)
    return rec


def test_the_trust_dial_is_the_models_own_poll_error_over_trust():
    """Decision 2: sd(t) = polling.poll_sd / t; 0 is infinite; [0, 1] only."""
    import polling
    from datetime import date
    rec = _record()
    own = polling.poll_sd(rec, 0.35, asof=date(2026, 11, 4))
    # the 1 end is the model's own number for this poll, drift to polling day
    assert R.poll_trust_sd(rec, 0.35, 1.0) == own
    assert own > polling.poll_sd(rec, 0.35)          # drift is in it
    # the mapping is 1/t, not 1/sqrt(t) (the exponent reading, A8)
    assert R.poll_trust_sd(rec, 0.35, 0.5) == own / 0.5
    assert R.poll_trust_sd(rec, 0.35, 0.25) == own / 0.25
    # the 0 end is infinite, before anything is priced: a record with no date
    # at all still answers at zero trust
    undated = _record()
    del undated["asof"]
    assert R.poll_trust_sd(undated, 0.35, 0.0) == math.inf
    # at non-zero trust an undated record is refused, not priced at zero drift
    try:
        R.poll_trust_sd(undated, 0.35, 0.5)
    except R.Refused:
        pass
    else:
        raise AssertionError("a poll with no date to price drift at was priced")
    assert R.poll_trust_sd(undated, 0.35, 1.0, asof="2026-11-04") == own
    for bad in (-0.01, 1.01, math.nan, math.inf):
        try:
            R.poll_trust_sd(rec, 0.35, bad)
        except R.Refused:
            continue
        raise AssertionError(f"trust {bad} was accepted")


def test_poll_weights_under_trust_price_each_party_on_the_polled_base():
    import polling
    from datetime import date
    rng = np.random.default_rng(21)
    shares = rng.dirichlet(np.ones(4) * 5, size=3000)
    cols = ["A", "B", "C", "D"]
    rec = _record()
    w = R.poll_weights(shares, cols, rec, trust=0.5)
    # by hand: each party its own poll_sd at its reported share, over trust,
    # divided by the polled total S, on the renormalised base
    raw = {"A": 0.35, "B": 0.25}
    s_total = sum(raw.values())
    x = shares[:, :2] / shares[:, :2].sum(axis=1, keepdims=True)
    y = np.array([raw["A"], raw["B"]]) / s_total
    sds = np.array([polling.poll_sd(rec, raw[p], asof=date(2026, 11, 4)) / 0.5
                    for p in ("A", "B")]) / s_total
    ll = -0.5 * np.square((x - y) / sds).sum(axis=1)
    assert np.allclose(w, np.exp(ll - ll.max()), rtol=1e-12, atol=0)
    # the per-party error matters: one sd for both parties gives other weights
    one = R.poll_weights(shares, cols, raw, sd=float(sds.mean()))
    assert not np.allclose(w, one, rtol=1e-6, atol=0)
    # zero trust is the published forecast exactly
    assert np.array_equal(R.poll_weights(shares, cols, rec, trust=0.0),
                          R.uniform(len(shares)))
    # more trust, fewer draws
    ess = [R.effective_draws(R.poll_weights(shares, cols, rec, trust=t))
           for t in (0.0, 0.25, 0.5, 1.0)]
    assert all(a > b for a, b in zip(ess, ess[1:])), ess
    # trust needs the record: a bare map carries no sample size
    try:
        R.poll_weights(shares, cols, raw, trust=0.5)
    except R.Refused:
        pass
    else:
        raise AssertionError("trust was priced without the poll's record")


def test_the_polled_base_refuses_with_refused_not_a_bare_value_error():
    """F9: each is a poll the draws cannot answer, which the page reports."""
    shares = np.array([[0.5, 0.5, 0.0], [0.4, 0.4, 0.2]])
    cols = ["A", "B", "C"]
    cases = {"names a party the draws lack": {"Q": 0.3},
             "names no party": {},
             "gives its parties no share": {"A": 0.0, "B": 0.0},
             "a draw gives the polled parties nothing": {"C": 0.3}}
    for why, poll in cases.items():
        try:
            R._on_polled_base(shares, cols, poll)
        except R.Refused:
            continue
        except ValueError as exc:
            raise AssertionError(f"{why}: ValueError, not Refused: {exc}")
        raise AssertionError(f"{why}: answered")
    x, y = R._on_polled_base(shares, cols, {"A": 3, "B": 1})
    assert np.allclose(y, [0.75, 0.25]) and np.allclose(x[0], [0.5, 0.5])


def _joburg_2026():
    import cityconfig
    return cityconfig.Target(city=cityconfig.load("joburg"), year="2026")


def test_page_polls_are_exactly_what_the_models_rules_admit():
    """F8, on a constructed register: one poll of each refusal, one admitted."""
    import montecarlo
    import polling
    floor = float(montecarlo.DEFAULTS["poll_min_n"])
    ok = _record(id="ok")
    del ok["asof"]
    register = [
        ok,
        dict(ok, id="after-polling-day", fieldwork_end="2026-11-10"),
        dict(ok, id="commissioned", commissioned_by="a party"),
        dict(ok, id="other-city", city="tshwane"),
        dict(ok, id="other-election", target="2021"),
        dict(ok, id="small", n=floor - 1),
        dict(ok, id="national", scope="national", city=None),
    ]
    kept_load = polling.load
    kept_floor = montecarlo.DEFAULTS["poll_min_n"]
    polling.load = lambda path=polling.REGISTER: [dict(p) for p in register]
    try:
        got = R.page_polls(_joburg_2026())
        assert [p["id"] for p in got] == ["ok"]
        assert got[0]["asof"] == "2026-11-04" == _joburg_2026().date.isoformat()
        assert "asof" not in register[0]            # a copy, not the record
        # the floor is the model's, read at call time: lower it and the
        # small poll is admitted, exactly as the model would admit it
        montecarlo.DEFAULTS["poll_min_n"] = floor - 2
        assert [p["id"] for p in R.page_polls(_joburg_2026())] == ["ok", "small"]
        # a malformed register raises here as it does for the model
        polling.load = lambda path=polling.REGISTER: [dict(ok, scope="Metro")]
        try:
            R.page_polls(_joburg_2026())
        except polling.PollRegisterError:
            pass
        else:
            raise AssertionError("a malformed register was offered on the page")
    finally:
        polling.load = kept_load
        montecarlo.DEFAULTS["poll_min_n"] = kept_floor


def test_page_polls_on_the_real_register_both_directions():
    import montecarlo
    import polling
    target = _joburg_2026()
    page = R.page_polls(target)
    kept, declined = polling.screen(
        target, min_n=float(montecarlo.DEFAULTS["poll_min_n"]))
    admitted = {p["id"] for p in kept if p.get("scope") == "metro"}
    scanned(len(page), of=len(polling.load()), low=0.05, high=1.0,
            what="polls on the page", denominator="records in the register")
    # page -> rules, and rules -> page
    assert {p["id"] for p in page} == admitted
    assert not {p["id"] for p in page} & {x.poll_id for x in declined}


def test_a_pinned_tilt_holds_another_cells_turnout_at_the_published_mean():
    """F4/F10: a cell's own mean is not the published one; pin_to says which."""
    published = _constructed_turnouts()
    rng = np.random.default_rng(22)
    # a second, unpaired cell: its own draws, its mean off by sampling
    cell = published[rng.permutation(len(published))] + 0.004
    pin = published.mean(axis=0)
    held = R.turnout_tilt(cell, np.zeros(4), pin_to=pin)
    assert np.max(np.abs((held / held.sum()) @ cell - pin)) < 1e-9
    assert not np.array_equal(held, R.uniform(len(cell)))
    # unpinned, a zero shift is the cell's own mean: uniform, and off the pin
    free = R.turnout_tilt(cell, np.zeros(4))
    assert np.array_equal(free, R.uniform(len(cell)))
    assert np.all(np.abs(cell.mean(axis=0) - pin) > 0.003)
    # a shift is measured from the pin
    moved = R.turnout_tilt(cell, [0.01, 0, 0, 0], pin_to=pin)
    assert np.allclose((moved / moved.sum()) @ cell, pin + [0.01, 0, 0, 0],
                       rtol=0, atol=1e-9)
    # with a poll on and pin_to the published mean, the poll cannot move turnout
    t, shares, cols = _correlated_draws()
    poll = R.poll_weights(shares, cols, {"A": 0.38, "B": 0.25}, sd=0.03)
    both = R.turnout_tilt(t, np.zeros(4), base=poll, pin_to=t.mean(axis=0))
    assert np.max(np.abs(_turnout_miss(t, both))) < 1e-9
    for bad in (pin[:3], [np.nan, 0.4, 0.4, 0.4]):
        try:
            R.turnout_tilt(cell, np.zeros(4), pin_to=bad)
        except ValueError:
            continue
        raise AssertionError(f"pin_to {bad} was accepted")


def _bootstrap_se(v, w, q, reps: int, seed: int) -> float:
    """Resample the draws with their weights; the sd of the weighted quantile."""
    rng = np.random.default_rng(seed)
    n = len(v)
    out = []
    for _ in range(reps):
        i = rng.integers(0, n, n)
        out.append(R.weighted_quantile(v[i], w[i], q))
    return float(np.std(out))


#: How close `sampling_se` must come to the check it is compared with: within
#: this RATIO, or within SE_FLOOR seats, whichever is looser. The floor is for
#: integer figures whose true SE is near zero (the quantile sits deep inside a
#: block of tied seats, so a re-run rarely moves it), where a ratio of two
#: near-zero numbers means nothing; it is a twentieth of the page's ceiling.
SE_TOLERANCE = 0.30
SE_FLOOR = 0.10


def _agrees(est: float, check: float) -> bool:
    return abs(est - check) <= max(SE_TOLERANCE * check, SE_FLOOR)


def test_sampling_se_agrees_with_a_bootstrap_on_weighted_integer_seats():
    rng = np.random.default_rng(23)
    n = 5000
    seats = np.round(rng.normal(80.3, 15.0, n))
    driver = (seats - seats.mean()) / seats.std() + rng.standard_normal(n)
    tilted = np.exp(driver)
    uni = R.uniform(n)
    ratios = []
    for q in (0.05, 0.5, 0.95):
        est_u = R.sampling_se(seats, uni, q)
        est_w = R.sampling_se(seats, tilted, q)
        boot_u = _bootstrap_se(seats, uni, q, 400, 1)
        boot_w = _bootstrap_se(seats, tilted, q, 400, 2)
        print(f"  q={q}: uniform {est_u:.3f} (bootstrap {boot_u:.3f}); "
              f"tilted {est_w:.3f} (bootstrap {boot_w:.3f}); "
              f"Kish {R.effective_draws(tilted):.0f}")
        assert _agrees(est_u, boot_u), (q, est_u, boot_u)
        assert _agrees(est_w, boot_w), (q, est_w, boot_w)
        ratios.append(est_w / est_u)
    # it can see the weights: the tilt starves the upper tail, the bootstrap
    # agrees, and an estimator that ignored the weights would not
    assert max(ratios) > 3.0, ratios
    # and the check can see a wrong estimator: the uniform SE offered for the
    # tilted p95 is caught, and the real one passes again
    wrong = R.sampling_se(seats, uni, 0.95)
    boot = _bootstrap_se(seats, tilted, 0.95, 400, 2)
    assert not _agrees(wrong, boot)
    assert _agrees(R.sampling_se(seats, tilted, 0.95), boot)


def test_sampling_se_matches_repeated_samples_where_a_density_would_say_zero():
    """Integer values: an estimator built on a density, or on a narrow
    difference of the quantile function, is zero inside a block of ties,
    while a re-run moves the figure by a seat when the level crosses the
    block's edge.

    Two checks per case, each the mean over one-sample estimates: against a
    bootstrap on the SAME samples, always; and against the spread of repeated
    independent samples, where a re-run really moves the figure. Where it does
    not (the quantile deep inside a block, true SE zero), a one-sample
    estimate cannot know the block edge exactly and overstates the SE — the
    bootstrap as much as this estimator, measured 2026-09-30 at a tenth of a
    seat on average. That is the conservative direction and is printed, not
    asserted."""
    rng = np.random.default_rng(24)
    n = 5000
    repeated_all = []
    for mean, sd in ((60.5, 8.0), (30.2, 5.0)):
        for q in (0.05, 0.5, 0.95):
            repeated = float(np.std([
                np.percentile(np.round(rng.normal(mean, sd, n)), 100 * q)
                for _ in range(200)]))
            ests, boots = [], []
            for k in range(10):
                x = np.round(rng.normal(mean, sd, n))
                ests.append(R.sampling_se(x, R.uniform(n), q))
                boots.append(_bootstrap_se(x, R.uniform(n), q, 100, k))
            est, boot = float(np.mean(ests)), float(np.mean(boots))
            print(f"  mean {mean}, q={q}: estimate {est:.3f}, bootstrap "
                  f"{boot:.3f}, repeated samples {repeated:.3f}")
            assert _agrees(est, boot), (mean, q, est, boot)
            if repeated > 3 * SE_FLOOR:
                assert _agrees(est, repeated), (mean, q, est, repeated)
            repeated_all.append(repeated)
    # the cases include ones where a re-run really moves the figure, which is
    # where a density-based SE of zero would fail
    assert max(repeated_all) > 3 * SE_FLOOR, repeated_all
    # and on smooth values it is the textbook s / f(x_q): the median of a
    # normal has SE sqrt(pi/2) sd / sqrt(n)
    x = rng.normal(0.0, 3.0, n)
    textbook = math.sqrt(math.pi / 2) * 3.0 / math.sqrt(n)
    assert abs(R.sampling_se(x, R.uniform(n), 0.5) / textbook - 1) < 0.15
    # every draw alike: nothing to estimate
    assert R.sampling_se(np.full(50, 7.0), R.uniform(50), 0.05) == 0.0


def test_many_quantiles_at_once_are_the_single_quantile_bit_for_bit():
    rng = np.random.default_rng(25)
    x = rng.integers(0, 40, size=777).astype(float)
    w = rng.uniform(0.0, 2.0, size=777)
    levels = np.linspace(0, 1, 101)
    many = R._weighted_quantiles(x, w, levels)
    assert [float(v) for v in many] == [R.weighted_quantile(x, w, q)
                                        for q in levels]


def test_a_figure_above_the_se_ceiling_is_withheld_and_the_slider_stops():
    rng = np.random.default_rng(26)
    n = 5000
    seats = np.round(rng.normal(60.0, 8.0, n))
    uni = R.uniform(n)
    heavy = np.exp(3.0 * (seats - seats.mean()) / seats.std())
    figs = {("X", 0.05): (seats, 0.05), ("X", 0.5): (seats, 0.5),
            ("X", 0.95): (seats, 0.95)}
    assert R.within_precision(figs, uni)
    assert R.imprecise_figures(figs, uni) == []
    shown = R.figure(seats, uni, 0.05, poll=False)
    assert shown["withheld"] is False and shown["value"] is not None
    # a constructed heavy tilt: some figures fall past the ceiling and some do
    # not, and the slider's stop and the figure's own rule name the same ones
    ses = {k: R.sampling_se(v, heavy, q) for k, (v, q) in figs.items()}
    bad = R.imprecise_figures(figs, heavy)
    assert bad == [k for k, se in ses.items() if se > R.MAX_FIGURE_SE_SEATS]
    assert bad and len(bad) < len(figs), ses
    assert bad == [k for k, (v, q) in figs.items()
                   if R.figure(v, heavy, q, poll=False)["withheld"]]
    assert not R.within_precision(figs, heavy)
    hidden = R.figure(seats, heavy, bad[0][1], poll=False)
    assert hidden["withheld"] is True and hidden["value"] is None
    assert hidden["sampling_se"] > R.MAX_FIGURE_SE_SEATS
    q_hidden = bad[0][1]
    # the ceiling is read at call time: raise it past the SE and it is shown
    kept = R.MAX_FIGURE_SE_SEATS
    try:
        R.MAX_FIGURE_SE_SEATS = hidden["sampling_se"] + 1.0
        assert R.figure(seats, heavy, q_hidden, poll=False)["withheld"] is False
        assert R.within_precision({bad[0]: (seats, q_hidden)}, heavy)
    finally:
        R.MAX_FIGURE_SE_SEATS = kept
    assert R.figure(seats, heavy, q_hidden, poll=False)["withheld"] is True


def test_uniform_weights_withhold_no_published_figure_and_a_far_tilt_does():
    st = _runs()
    arrays, manifest = st["arrays"], st["manifest"]
    summary = json.loads(SUMMARY.read_text())["parties"]
    seats = arrays["seats/deduct"].astype(float)
    col = {p: j for j, p in enumerate(manifest["parties"])}
    w = R.uniform(st["draws"])
    qs = {"p5": 0.05, "median": 0.5, "p95": 0.95}
    figs = {(p, k): (seats[:, col[p]], q) for p in summary for k, q in qs.items()}
    scanned(len(figs), of=3 * len(manifest["parties"]), low=0.05, high=1.0,
            what="published figures checked", denominator="3 x the file's parties")
    for (p, k), (v, q) in figs.items():
        f = R.figure(v, w, q, poll=False)
        assert f["withheld"] is False, (p, k, f["sampling_se"])
        assert f["value"] == summary[p][k], (p, k)
    assert R.within_precision(figs, w)
    # Black African +8 points with the others held: past what the draws carry
    names = _pools(manifest)
    shift = np.zeros(len(names))
    shift[names.index(POOL)] = 0.08
    far = R.turnout_tilt(arrays["pool_turnout"], shift)
    worst = R.imprecise_figures(figs, far)
    print(f"  withheld at {POOL} +8: {len(worst)} of {len(figs)} figures")
    assert worst and not R.within_precision(figs, far)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
