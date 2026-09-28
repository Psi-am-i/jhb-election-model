"""Re-weighting the published draws: exact when untouched, and honest when moved.

Build step S4 of `audits/2026-09-28-interactive-architecture/PLAN.md`;
`src/reweight.py` is the engine the page runs under Pyodide. What this module
proves:

1. UNIFORM WEIGHTS ARE THE PUBLISHED FORECAST, BIT FOR BIT. From the draw file
   of a fresh export at the published seed and draws: every party's median,
   p5 and p95 in `forecast_summary.json`, its structural probabilities and
   median threshold, and every ward's Jeffreys win probability in
   `ward_winner_probs.csv`. Trust 0 on a poll is exactly uniform.
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

⚠️ The tilt matches a MEAN and the re-run moves the whole distribution. Check
2 is what licenses the page to present one as the other, at this size of move
and no further; it says nothing about +8 points, where the draws run out.

Two full model runs go in parallel subprocesses, so this module takes minutes.
"""

from __future__ import annotations

import csv
import json
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


def test_trust_zero_is_uniform_exactly_and_trust_above_zero_is_not():
    st = _runs()
    arrays, manifest = st["arrays"], st["manifest"]
    columns = manifest["parties"] + ["OTHER"]
    # a constructed poll: the five parties with the largest mean PR share, at
    # equal shares (chosen by a rule, not by name)
    means = arrays["pr_share"][:, :-1].mean(axis=0)
    poll = {manifest["parties"][j]: 1.0 for j in np.argsort(-means)[:5]}
    w0 = R.poll_weights(arrays["pr_share"], columns, poll, sigma=0.05, trust=0.0)
    assert np.array_equal(w0, R.uniform(st["draws"]))
    w1 = R.poll_weights(arrays["pr_share"], columns, poll, sigma=0.05, trust=1.0)
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
    a = R.poll_weights(shares, cols, {"A": 0.3, "B": 0.2}, sigma=0.05, trust=1)
    b = R.poll_weights(shares, cols, {"A": 30, "B": 20}, sigma=0.05, trust=1)
    assert np.allclose(a, b, rtol=1e-12, atol=0)
    # relabelling the parties relabels nothing else: no party is special
    perm = [2, 3, 0, 1]
    c = R.poll_weights(shares[:, perm], [cols[i] for i in perm],
                       {"A": 0.3, "B": 0.2}, sigma=0.05, trust=1)
    assert np.allclose(a, c, rtol=1e-12, atol=0)
    # tempering: trust t at sigma equals full trust at sigma / sqrt(t)
    d = R.poll_weights(shares, cols, {"A": 0.3, "B": 0.2}, sigma=0.05, trust=0.25)
    e = R.poll_weights(shares, cols, {"A": 0.3, "B": 0.2}, sigma=0.10, trust=1)
    assert np.allclose(d, e, rtol=1e-12, atol=0)
    try:
        R.poll_weights(shares, cols, {"Q": 0.3}, sigma=0.05, trust=1)
    except ValueError:
        pass
    else:
        raise AssertionError("a poll naming a party the draws lack was accepted")


def test_two_controls_combine_by_multiplying_and_trust_zero_changes_nothing():
    t = _constructed_turnouts(400)
    tilt = R.turnout_tilt(t, [0.01, 0.0, 0.0, 0.0])
    rng = np.random.default_rng(6)
    shares = rng.dirichlet(np.ones(3) * 5, size=400)
    poll = R.poll_weights(shares, ["A", "B", "C"], {"A": 0.4, "B": 0.3},
                          sigma=0.05, trust=1.0)
    both = R.combine(tilt, poll)
    assert both.max() == 1.0
    assert np.allclose(both, tilt * poll / (tilt * poll).max(), rtol=1e-12)
    untouched = R.poll_weights(shares, ["A", "B", "C"], {"A": 0.4, "B": 0.3},
                               sigma=0.05, trust=0.0)
    assert np.array_equal(R.combine(tilt, untouched), tilt / tilt.max())
    try:
        R.combine(tilt, np.zeros(400))
    except R.Refused:
        pass
    else:
        raise AssertionError("controls leaving no draw any weight were answered")


def test_combine_polls_averages_on_a_common_base_and_reports_the_spread():
    avg, spread = R.combine_polls([{"A": 30, "B": 20, "C": 50},
                                   {"A": 0.2, "B": 0.3}])
    assert set(avg) == {"A", "B"}
    assert np.isclose(avg["A"], (0.6 + 0.4) / 2) and np.isclose(avg["B"], 0.5)
    assert np.allclose(spread["A"], (0.4, 0.6))


def test_ward_win_probability_under_weights_uses_the_effective_sample():
    winners = np.array([[0], [0], [1], [1]])
    w = np.array([1.0, 1.0, 1.0, 3.0])
    p = R.ward_win_probability(winners, w, 2)
    ess = R.effective_draws(w)
    assert np.isclose(p[0, 1], (ess * 4 / 6 + 0.5) / (ess + 1))
    assert np.isclose(p[0].sum(), (ess + 1.0) / (ess + 1.0))


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
