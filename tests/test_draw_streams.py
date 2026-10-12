"""Keyed draw streams: the samplers are exact, the indexing holds, arms pair.

Design: ``audits/2026-10-11-model-round/step1/1c-paired-draws-design.md`` with
every fix in ``step2/2-review-1c.md``; the tests the pre-registration
``prereg/2026-10-12-universal-draw.md`` §6 requires before any arm runs.

Four groups, each against CONSTRUCTED inputs except the run-level wiring tests,
which run ``run_model`` in process on one small real city-year (as
``test_chain`` does) because the wiring between the draw loop and the drawer
exists nowhere else:

* **V1, samplers exact.** Two-sample Kolmogorov-Smirnov at N = 200,000 per
  side, rejecting at D > 0.00616 (α = 0.001 per comparison). The slot gamma,
  boosted at every shape, against numpy; the fallback ALONE (slots forced to
  zero); the Student t built from a normal and a gamma, and the wrong constant
  that must reject; the Dirichlet per component; the triangular from Φ(z).
  POWER ROWS: a 5% shape error and a doubled df must reject, so a pass means
  something.
* **V2, indexing.** Chunk sizes give byte-identical rows; a short run is the
  prefix of a long one; an earlier read and a changed width raise; keys are
  stable across interpreters (``PYTHONHASHSEED``); the entropy pin.
* **V3, pairing on a constructed spec** of two pools and seven parties, 2,000
  draws: the compared key set is the one the spec implies, in both directions;
  primitives are bit-identical; derived quantities that depend on no changed
  input are bit-identical; drawn shares of unchanged parties correlate above
  the pre-registered thresholds (prereg §6.3, V3.4); the entrant gate nests;
  a tie keyed by its label survives losing a member; a shape crossing 1 stays
  paired.
* **V4, the detectors can see.** City and target in the root key; distinct
  keys uncorrelated; distinct entropies over a real run's keys.
"""

from __future__ import annotations

import copy
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import montecarlo as M  # noqa: E402
import seats  # noqa: E402

N = 200_000
KS_CRIT = 1.949 * math.sqrt(2.0 / N)        # c(0.001)·√(2/N) = 0.00616


def ks(a, b) -> float:
    """The two-sample Kolmogorov-Smirnov statistic D (ties handled exactly)."""
    a = np.sort(np.asarray(a, dtype=float))
    b = np.sort(np.asarray(b, dtype=float))
    grid = np.concatenate([a, b])
    fa = np.searchsorted(a, grid, side="right") / a.size
    fb = np.searchsorted(b, grid, side="right") / b.size
    return float(np.max(np.abs(fa - fb)))


def slot_gamma(shape: float, n: int, J: int, seed: int,
               fallback_rng=None) -> tuple[np.ndarray, int]:
    """n log Gamma(shape) values through `log_gamma_slots` at J slots, with
    the exhausted ones replaced by an exact fallback. Returns (log values,
    fallbacks)."""
    g = np.random.default_rng(seed)
    z = g.standard_normal((n, J))
    u = 1.0 - g.random((n, J + 1))
    lg, ok = M.log_gamma_slots(np.full(n, shape), z, u[:, :J], u[:, J])
    bad = np.flatnonzero(~ok)
    if bad.size:
        fb = fallback_rng or np.random.default_rng(seed + 1)
        lg[bad] = (np.log(fb.standard_gamma(shape + 1.0, bad.size))
                   + np.log(1.0 - fb.random(bad.size)) / shape)
    return lg, int(bad.size)


def log_reference(shape: float, n: int, seed: int) -> np.ndarray:
    """An independent exact log Gamma(shape) from numpy.

    numpy's own gamma underflows to exact 0.0 at tiny shapes, so below 0.1 the
    reference is the boost identity on numpy's gamma, log G(a+1) + log(U)/a;
    above it, numpy's `standard_gamma` itself."""
    g = np.random.default_rng(seed)
    if shape < 0.1:
        return (np.log(g.standard_gamma(shape + 1.0, n))
                + np.log(1.0 - g.random(n)) / shape)
    return np.log(g.standard_gamma(shape, n))


# --------------------------------------------------------------------------
# V1 — samplers exact
# --------------------------------------------------------------------------

GAMMA_SHAPES = (1e-4, 0.01, 0.1, 0.5, 0.99, 1.0, 1.01, 3.5, 10.0, 100.0)


def test_the_slot_gamma_is_exact_at_every_shape_at_four_slots_and_at_one():
    """V1 (prereg §6.1): boosted at every shape, at J = 4 and J = 1."""
    worst = []
    for J in (M.GAMMA_SLOTS, 1):
        for k, a in enumerate(GAMMA_SHAPES):
            mine, _ = slot_gamma(a, N, J, seed=1000 + k)
            ref = log_reference(a, N, seed=5000 + k)
            D = ks(mine, ref)
            worst.append((D, J, a))
            assert D <= KS_CRIT, (
                f"slot gamma at shape {a}, J={J}: KS D={D:.5f} > {KS_CRIT:.5f}. "
                f"The keyed sampler does not draw Gamma({a}).")
    assert len(worst) == 2 * len(GAMMA_SHAPES)


def test_the_fallback_alone_is_exact_and_one_slot_exercises_it():
    """V1 (review finding 5): the fallback path ALONE, slots forced to zero,
    against numpy below and above shape 1; and at J = 1 the counter fires."""
    for k, a in enumerate((0.3, 0.9, 1.7, 6.0)):
        mine, fb = slot_gamma(a, N, 0, seed=200 + k)
        assert fb == N, "at J = 0 every gamma must take the fallback"
        D = ks(mine, log_reference(a, N, seed=300 + k))
        assert D <= KS_CRIT, f"the fallback alone at shape {a}: D={D:.5f}"
    # the counter on the stream class: J = 1 forces fallbacks, counted
    saved = M.GAMMA_SLOTS
    try:
        M.GAMMA_SLOTS = 1
        st = M.DrawStreams("fallback|count|1", 400)
        for d in range(400):
            st.log_gamma("split", ("P|A", "P|B"), np.array([1.0, 0.05]), d)
        assert st.gamma_draws == 800
        assert 0 < st.gamma_fallbacks < 800, (
            f"{st.gamma_fallbacks} fallbacks in 800 gammas at one slot: the "
            f"fallback is not counted (or every gamma fell back)")
    finally:
        M.GAMMA_SLOTS = saved


def test_the_gamma_test_has_power():
    """Power row: Gamma(1.05·a) against Gamma(a) must reject at 0.01-100."""
    for k, a in enumerate((0.01, 0.1, 1.0, 10.0, 100.0)):
        x, _ = slot_gamma(a, N, M.GAMMA_SLOTS, seed=70 + k)
        y, _ = slot_gamma(1.05 * a, N, M.GAMMA_SLOTS, seed=90 + k)
        assert ks(x, y) > KS_CRIT, f"no power at shape {a}"


def _t_from_slots(df: float, n: int, seed: int, wrong: bool = False):
    g = np.random.default_rng(seed)
    z = g.standard_normal(n)
    lg, _ = slot_gamma(df / 2.0, n, M.GAMMA_SLOTS, seed=seed + 1)
    if wrong:                                  # z / sqrt(G/df): a different law
        return z * np.exp(-0.5 * (lg - math.log(df)))
    return M.student_t(z, lg, df)


def test_the_student_t_is_exact_and_the_wrong_constant_rejects():
    """V1: t = z/sqrt(2G/df) at df 2.5, 4, 7, 30; z/sqrt(G/df) rejects."""
    for k, df in enumerate((2.5, 4.0, 7.0, 30.0)):
        ref = np.random.default_rng(400 + k).standard_t(df, N)
        D = ks(_t_from_slots(df, N, 410 + 10 * k), ref)
        assert D <= KS_CRIT, f"Student t at df {df}: D={D:.5f}"
        if df < 30:
            Dw = ks(_t_from_slots(df, N, 410 + 10 * k, wrong=True), ref)
            assert Dw > KS_CRIT, f"the wrong constant passed at df {df}"
    # power row: t at 2·df against df
    for k, df in enumerate((2.5, 4.0, 7.0)):
        assert ks(_t_from_slots(2 * df, N, 600 + k),
                  np.random.default_rng(650 + k).standard_t(df, N)) > KS_CRIT


def _dirichlet_from_slots(alpha, n, seed):
    alpha = np.asarray(alpha, dtype=float)
    cols = [slot_gamma(a, n, M.GAMMA_SLOTS, seed=seed + 7 * i)[0]
            for i, a in enumerate(alpha)]
    lg = np.column_stack(cols)
    return np.array([M.pool_split(row, alpha) for row in lg[:5]]), lg


def _log_shares(lg):
    m = lg.max(axis=1, keepdims=True)
    return lg - (m + np.log(np.exp(lg - m).sum(axis=1, keepdims=True)))


def test_the_dirichlet_is_exact_per_component():
    """V1 (review finding 2): a vector with a member at DIRICHLET_FLOOR × alpha
    against numpy's own Dirichlet; a vector with every α < 0.1, where numpy
    switches to stick-breaking and returns exact zeros, against an independent
    log-space boost-identity reference."""
    total = 16.1
    alpha = np.array([0.55, 0.30, 0.15 - M.DIRICHLET_FLOOR, M.DIRICHLET_FLOOR]) * total
    _, lg = _dirichlet_from_slots(alpha, N, 800)
    mine = np.exp(_log_shares(lg))
    ref = np.random.default_rng(801).dirichlet(alpha, N)
    for j in range(alpha.size):
        assert ks(mine[:, j], ref[:, j]) <= KS_CRIT, f"component {j}"
    # pool_split is the normaliser the drawer uses: same values as the log form
    rows = np.array([M.pool_split(r, alpha) for r in lg[:200]])
    assert np.allclose(rows, mine[:200], atol=1e-12)

    small = np.array([0.05, 0.02, 0.08, 0.003])
    _, lg = _dirichlet_from_slots(small, N, 900)
    refs = np.column_stack([log_reference(a, N, 950 + i)
                            for i, a in enumerate(small)])
    mine, ref = _log_shares(lg), _log_shares(refs)
    for j in range(small.size):
        assert ks(mine[:, j], ref[:, j]) <= KS_CRIT, f"small component {j}"
    # power: one α doubled rejects at that component
    dbl = small.copy()
    dbl[0] *= 2
    _, lg2 = _dirichlet_from_slots(dbl, N, 990)
    assert ks(_log_shares(lg2)[:, 0], ref[:, 0]) > KS_CRIT


def test_the_triangular_from_a_normal_is_exact():
    """V1: tri_from_z against numpy's triangular, three bands, one mode at an edge."""
    for k, spec in enumerate(((0.3, 0.5, 0.7), (0.01, 0.01, 0.12), (0.0, 0.9, 1.0))):
        z = np.random.default_rng(1100 + k).standard_normal(N)
        mine = np.array([M.tri_from_z(x, spec) for x in z])
        ref = np.random.default_rng(1200 + k).triangular(*spec, N)
        assert ks(mine, ref) <= KS_CRIT, f"triangular {spec}"


# --------------------------------------------------------------------------
# V2 — indexing
# --------------------------------------------------------------------------

def test_chunk_size_changes_no_row_and_reads_are_forward_only():
    """V2 at stream level: chunks 1, 7, 256 give identical rows; an earlier
    read raises; a changed k raises; a read past the run raises."""
    rows = {}
    for chunk in (1, 7, 256):
        st = M.DrawStreams("chunk|test|1", 300, chunk=chunk)
        rows[chunk] = (
            np.array([st.normals("level.z", "ANC", d) for d in range(300)]),
            np.array([st.uniforms("vd_turnout.noise", "", d, k=5)
                      for d in range(300)]),
            np.array([st.log_gamma("split", ("P|A", "P|B"), [0.4, 3.0], d)
                      for d in range(300)]))
    for chunk in (7, 256):
        for a, b in zip(rows[1], rows[chunk]):
            assert np.array_equal(a, b), f"chunk {chunk} moved a row"
    st = M.DrawStreams("chunk|test|1", 50)
    st.normals("x", "a", 9)
    for bad in (lambda: st.normals("x", "a", 5),          # earlier draw
                lambda: st.normals("x", "a", 10, k=2),    # changed width
                lambda: st.normals("y", "a", 50)):        # past the run
        try:
            bad()
        except (IndexError, ValueError):
            continue
        raise AssertionError("a wiring defect was accepted by DrawStreams")


def test_the_entropy_pin_and_one_definition():
    """V2: the pinned value, now on the one definition both users share."""
    import score
    assert seats.stable_entropy("ANC") == 16408193524922255279
    assert score._column_entropy("ANC") == seats.stable_entropy("ANC")


_KEY_SCRIPT = (
    "import sys; sys.path.insert(0, sys.argv[1]); import montecarlo as M; "
    "st = M.DrawStreams('joburg|2021|7', 3); "
    "print(repr(st.normals('level.z', 'ANC', 0)[0]), "
    "repr(st.log_gamma('split', ('Black African|ANC',), [0.7], 0)[0]))")


def test_keys_are_stable_across_interpreters():
    """V2: PYTHONHASHSEED 0 and 4 give byte-identical first rows. A key built
    on `hash()` fails here (prereg §6.4)."""
    out = []
    for seed in ("0", "4"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, "-c", _KEY_SCRIPT,
                            str(ROOT / "src")], capture_output=True, text=True,
                           env=env, check=True)
        out.append(r.stdout.strip())
    assert out[0] == out[1] and out[0], out


def _small_run(draws: int, chunk: int | None = None):
    """`run_model` in process, Buffalo City 2021: the smallest council."""
    import argparse
    import cityconfig
    saved = M.STREAM_CHUNK
    try:
        if chunk is not None:
            M.STREAM_CHUNK = chunk
        city = cityconfig.use("buffalocity")
        target = cityconfig.use_target("2021")
        M.apply_city(city)
        scenario = M.load_scenario(argparse.Namespace(
            config=None, set=[], draws=draws, seed=20261104,
            city="buffalocity", target="2021"))
        # The shipped law (universal) with a FIXTURE width record: the wiring
        # is the subject here, not the record's values, and the record file
        # exists only after a re-emit window.
        return M.run_model(target, scenario, verbose=False,
                           width_override=dict(FIXTURE_RECORD))
    finally:
        M.STREAM_CHUNK = saved


_RUNS: dict = {}


def _run(draws: int, chunk: int | None = None):
    key = (draws, chunk)
    if key not in _RUNS:
        _RUNS[key] = _small_run(draws, chunk)
    return _RUNS[key]


DRAW_FIELDS = ("pr_share_draws", "ward_share_draws", "pr_vote_draws",
               "ward_vote_draws", "ward_winner_draws", "pool_turnout_draws")


def test_the_chunk_size_changes_no_drawn_number_in_a_real_run():
    """V2 at run level (review finding 6): STREAM_CHUNK 1, 7 and 256 give
    byte-identical draw arrays, so the drawer's index and the loop's agree and
    no cache desynchronises from the per-stream buffers."""
    base = _run(30, 256)
    for chunk in (1, 7):
        other = _run(30, chunk)
        for f in DRAW_FIELDS:
            assert np.array_equal(getattr(base, f), getattr(other, f)), (
                f"STREAM_CHUNK={chunk} moved {f}")
        assert base.seat_draws == other.seat_draws


def test_a_short_run_is_the_prefix_of_a_long_one():
    """V2 (prereg §6.2): the first 20 draws of a 40-draw run are the 20-draw
    run. A drawer that ignores the loop's `d` fails here (prereg §6.4)."""
    short, long_ = _run(20), _run(40)
    for f in ("pr_share_draws", "ward_winner_draws"):
        assert np.array_equal(getattr(short, f), getattr(long_, f)[:20]), f
    assert short.seat_draws == long_.seat_draws[:20]


def test_a_real_runs_keys_are_recorded_and_distinct():
    """V4: every key the run read is on the board, and their entropies are
    distinct (a collision would pair two quantities that must be independent)."""
    run = _run(30, 256)
    keys = run.guards["stream_keys"]
    assert keys == sorted(keys) and len(keys) == len({tuple(k) for k in keys})
    st = M.DrawStreams(run.lot, 1)
    ents = {tuple(st.entropy(kind, stage, name))
            for stage, name in keys for kind in ("z", "u")}
    assert len(ents) == 2 * len(keys), "two stream keys share an entropy"
    stages = {stage for stage, _ in keys}
    for need in ("turnout.common", "turnout.pool", "level.z",
                 "vd_turnout.blend", "vd_turnout.noise", "ward_noise"):
        assert need in stages, f"the run read no {need} stream"
    # The universal law draws no gamma (no Dirichlet, a normal own term), so
    # the count is zero; what it reads instead is the shared factor and the
    # calibration pass's own streams.
    assert run.guards["gamma_draws"] == 0 == run.guards["gamma_fallbacks"]
    assert "level.shared" in stages and "calib.level.z" in stages
    assert "split" not in stages and "level.chi" not in stages
    # the universal draw's own board, on a real city-year (fixture widths)
    g = run.guards
    assert g["kappa_error"] and max(g["kappa_error"].values()) < M.KAPPA_TOL
    assert set(g["width"]) == set(g["kappa_error"])
    assert g["mean_error"]["parties"] == len(g["mean_error"]["z"]) > 0


# --------------------------------------------------------------------------
# V4 — the root key and distinct keys are independent
# --------------------------------------------------------------------------

def test_one_partys_shocks_are_independent_across_city_years_and_keys():
    """V4: the ANC's `level.z` at two city-years, and two distinct keys at one,
    are uncorrelated (|corr| < 5/√2000). Dropping city and target from the root
    key, or one key for every stage, fails here (prereg §6.4)."""
    D = 2000
    a = M.DrawStreams(seats.lot_identity("joburg", "2021", 7), D)
    b = M.DrawStreams(seats.lot_identity("tshwane", "2021", 7), D)
    za = np.array([a.normals("level.z", "ANC", d)[0] for d in range(D)])
    zb = np.array([b.normals("level.z", "ANC", d)[0] for d in range(D)])
    zc = np.array([a.normals("level.z", "DA", d)[0] for d in range(D)])
    zd = np.array([a.normals("ward_noise", "ANC", d)[0] for d in range(D)])
    bound = 5 / math.sqrt(D)
    for x, y, what in ((za, zb, "two city-years"), (za, zc, "two parties"),
                       (za, zd, "two stages")):
        assert abs(np.corrcoef(x, y)[0, 1]) < bound, what


# --------------------------------------------------------------------------
# V3 — pairing on a constructed spec (two pools, seven parties)
# --------------------------------------------------------------------------

class RecordingStreams(M.DrawStreams):
    """A DrawStreams that keeps every row it serves, and every gamma by name.

    It changes no value: rows come from the parent's `_row`, gammas from the
    parent's `log_gamma`. It is how the primitives (V3.2) and the derived
    gammas per party (V3.3) are captured without trusting the drawer's arrays.
    """

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.rows: dict = {}
        self.gammas: dict = {}

    def _row(self, kind, stage, name, d, k):
        r = super()._row(kind, stage, name, d, k)
        self.rows.setdefault((kind, stage, name), []).append(np.array(r))
        return r

    def log_gamma(self, stage, names, shapes, d):
        lg = super().log_gamma(stage, names, shapes, d)
        for nm, v in zip(tuple(names), lg):
            self.gammas.setdefault((stage, nm), []).append(float(v))
        return lg


V3_DRAWS = 2000
POOL1 = ("A", "B", "C", "D")
POOL2 = ("D", "E", "F", "G")
PARTIES = ("A", "B", "C", "D", "E", "F", "G")


# A constructed width record for the universal law: the shape of design v4
# §1.1's 2026 fit, typed here as a fixture (not a measurement of anything).
FIXTURE_RECORD = {"kind": "fit",
                  "curve": {"a": 0.03, "b": 0.816, "log_mid": math.log(0.0856),
                            "k": 2.57},
                  "delta": 0.873, "location": {"c1": 0.342, "c2": 0.075},
                  "rho": {"lo": 0.33, "hi": 0.11}}


def base_spec(with_entrant: bool = False, tie: bool = False,
              law: str = "incumbent"):
    """Two pools, seven parties (D in both), measured-width shocks.

    ``law`` selects the draw law. The 1c pairing tests run on the incumbent
    law (the streams are the subject); the same arms under the universal law
    run with :data:`FIXTURE_RECORD`."""
    pools = {
        "P1": {"members": {"A": 1.0, "B": 1.0, "C": 1.0, "D": 0.5,
                           "E": 0.05, "F": 0.05, "G": 0.05},
               "registered": 600000.0, "turnout": [0.45, 0.55, 0.65],
               "alpha": 60.0},
        "P2": {"members": {"A": 0.05, "B": 0.05, "C": 0.05, "D": 0.5,
                           "E": 1.0, "F": 1.0, "G": 1.0},
               "registered": 400000.0, "turnout": [0.40, 0.50, 0.62],
               "alpha": 40.0},
    }
    if tie:
        pools["P3"] = {"members": {"G": 0.0001, "B": 0.0001},
                       "registered": 50000.0, "turnout": [0.3, 0.4, 0.5],
                       "alpha": 10.0}
        pools["P2"]["tie"] = "T"
        pools["P3"]["tie"] = "T"
    # Centres consistent with the pools' capacities (P1 casts 62% of the
    # votes at modal turnout, P2 38%; D is half in each), so the per-draw
    # balance is feasible at the centre and the fixture tests the draw rather
    # than the partial-balance fallback.
    centres = {"A": 0.35, "B": 0.15, "C": 0.07, "D": 0.10,
               "E": 0.18, "F": 0.09, "G": 0.06}
    sc = copy.deepcopy(M.DEFAULTS)
    sc["pools"] = pools
    sc["_theta_sd"] = {p: 0.3 for p in PARTIES + ("X",)}
    sc["entrant_prob"] = 0.25 if with_entrant else 0.0
    sc["draw_law"] = law
    sc["_width"] = dict(FIXTURE_RECORD)
    sc["_new_parties"] = []
    sc["_strength_applied"] = []
    index = {p: i for i, p in enumerate(PARTIES)}
    if with_entrant:
        index["ENTRANT"] = len(index)
        centres["ENTRANT"] = 0.0
    return sc, dict(centres), index


def run_arm(sc, centres, index, lot="v3|constructed|1", draws=V3_DRAWS):
    import contextlib
    import io
    st = RecordingStreams(lot, draws)
    with contextlib.redirect_stdout(io.StringIO()):
        drawer = M.make_drawer(sc, dict(centres), centres, index, st)
        out = np.array([drawer() for _ in range(draws)])
    return st, out, drawer


def implied_keys(sc, index) -> set:
    """The (stage, name) keys the spec implies, written from the spec alone."""
    spec_pools = {n: c for n, c in sc["pools"].items()
                  if any(p in index for p in c["members"])}
    keys = {("turnout.common", "")}
    keys |= {("turnout.pool", c.get("tie") or n) for n, c in spec_pools.items()}
    ipf = {p for c in spec_pools.values() for p in c["members"] if p in index}
    indiv = {p for p in index if p not in ipf and p != "ENTRANT"}
    if sc.get("draw_law", "universal") == "universal":
        # One latent draw per party plus the shared factor; no gamma, no
        # split; and the calibration pass's own streams (design v1 §1.6).
        run = set(keys) | {("level.shared", "")}
        run |= {("level.z", p) for p in ipf | indiv}
        keys = run | {("calib." + st, nm) for st, nm in run}
    else:
        for p in ipf | indiv:
            keys |= {("level.z", p), ("level.chi", p)}
        keys |= {("split", f"{n}|{p}") for n, c in spec_pools.items()
                 for p, w in c["members"].items() if p in index and float(w) > 0}
    if "ENTRANT" in index:
        keys |= {("entrant.gate", "ENTRANT"), ("entrant.share", "ENTRANT")}
    return keys


def _corr_unchanged(base_out, arm_out, base_index, arm_index, skip=()):
    cs = []
    for p, i in base_index.items():
        if p in skip or p == "ENTRANT":
            continue
        x, y = base_out[:, i], arm_out[:, arm_index[p]]
        cs.append(float(np.corrcoef(x, y)[0, 1]))
    return np.array(cs)


def _assert_population_and_primitives(sb, sa, sc_b, idx_b, sc_a, idx_a):
    """V3.1 and V3.2 for one arm against the base."""
    kb, ka = implied_keys(sc_b, idx_b), implied_keys(sc_a, idx_a)
    assert sb.keys == kb, (sorted(sb.keys ^ kb)[:6], "base read != spec implies")
    assert sa.keys == ka, (sorted(sa.keys ^ ka)[:6], "arm read != spec implies")
    shared = sb.keys & sa.keys
    scanned(shared, of=len(sb.keys), low=0.5, high=1.0,
            what="stream keys compared between arms",
            denominator="keys the base arm read")
    for (kind, stage, name), rows in sb.rows.items():
        if (stage, name) not in shared:
            continue
        other = sa.rows.get((kind, stage, name))
        assert other is not None and np.array_equal(
            np.array(rows), np.array(other)), (
            f"primitives of {stage}/{name} ({kind}) differ between arms")
    return shared


def test_adding_a_party_to_a_pool_pairs_everything_else():
    """V3 arm (i) at 0.1%, 1%, 5%, with the pre-registered thresholds."""
    sc0, c0, i0 = base_spec()
    sb, ob, db = run_arm(sc0, c0, i0)
    for share, (med, mn) in ((0.001, (0.99, 0.95)), (0.01, (0.99, 0.95)),
                             (0.05, (0.98, 0.93))):
        sc1, c1, _ = base_spec()
        sc1["pools"]["P1"]["members"]["X"] = 1.0
        c1["X"] = share
        i1 = {p: k for k, p in enumerate(PARTIES + ("X",))}
        sa, oa, da = run_arm(sc1, c1, i1)
        _assert_population_and_primitives(sb, sa, sc0, i0, sc1, i1)
        # V3.3 derived: pool turnouts are bit-identical. Pool 2's split
        # gammas are NOT: design 1c V3 item 3 listed them as bit-identical,
        # but its own §2.6 point 2 says why they cannot be — the per-draw
        # balance sets every member's shape from all shocked centres jointly,
        # so a party added to pool 1 moves pool 2's shapes slightly. Their
        # primitives are identical (above), and the value moves smoothly with
        # the shape, so the gammas are asserted near-identical.
        assert np.array_equal(np.array(db.turnout_record),
                              np.array(da.turnout_record))
        # D is in both pools, so the balance moves its pool-2 shape directly
        # and furthest (measured at 500 draws: 0.99997 / 0.968 / 0.937 at the
        # three sizes); a rejection sampler's accepted slot can also flip on
        # a small shape change, which is a jump. E, F and G are pool 2 only.
        for p in POOL2:
            x = np.array(sb.gammas[("split", f"P2|{p}")])
            y = np.array(sa.gammas[("split", f"P2|{p}")])
            floor = 0.90 if p == "D" else 0.99
            assert np.corrcoef(x, y)[0, 1] > floor, (share, p)
        cs = _corr_unchanged(ob, oa, i0, i1)
        assert np.median(cs) >= med and cs.min() >= mn, (share, cs)


def test_adding_an_individual_party_pairs_everything_else():
    """V3 arm (ii): a dummy party in no pool."""
    sc0, c0, i0 = base_spec()
    sb, ob, _ = run_arm(sc0, c0, i0)
    sc1, c1, _ = base_spec()
    c1["X"] = 0.01
    i1 = {p: k for k, p in enumerate(PARTIES + ("X",))}
    sa, oa, _ = run_arm(sc1, c1, i1)
    _assert_population_and_primitives(sb, sa, sc0, i0, sc1, i1)
    assert np.median(_corr_unchanged(ob, oa, i0, i1)) >= 0.99


def test_a_centre_change_pairs_and_the_shocks_are_untouched():
    """V3 arm (iii): one centre ×1.2; every party's level gamma is unchanged."""
    sc0, c0, i0 = base_spec()
    sb, ob, db = run_arm(sc0, c0, i0)
    c1 = dict(c0, B=c0["B"] * 1.2)
    sa, oa, da = run_arm(sc0, c1, i0)
    _assert_population_and_primitives(sb, sa, sc0, i0, sc0, i0)
    for p in PARTIES:
        assert sb.gammas[("level.chi", p)] == sa.gammas[("level.chi", p)], p
    assert np.array_equal(np.array(db.turnout_record), np.array(da.turnout_record))
    assert np.median(_corr_unchanged(ob, oa, i0, i0, skip=("B",))) >= 0.99


def test_the_entrant_gate_nests_when_its_probability_rises():
    """V3 arm (iv): entrant_prob 0.25 → 0.35. Gate and share primitives are
    identical; the share is used in strictly more draws, and in every draw
    the lower probability used it. Drawing the share only when the gate passed
    fails here (prereg §6.4)."""
    sc0, c0, i0 = base_spec(with_entrant=True)
    sb, ob, _ = run_arm(sc0, c0, i0)
    sc1 = copy.deepcopy(sc0)
    sc1["entrant_prob"] = 0.35
    sa, oa, _ = run_arm(sc1, c0, i0)
    _assert_population_and_primitives(sb, sa, sc0, i0, sc1, i0)
    e = i0["ENTRANT"]
    used0, used1 = ob[:, e] > 0, oa[:, e] > 0
    assert used1.sum() > used0.sum() and np.all(used1[used0])
    assert np.allclose(ob[used0, e], oa[used0, e])


def test_a_df_change_moves_only_the_transform():
    """V3 arm (v): LEVEL_DF 7 → 4. `level.z` primitives and pool turnouts are
    identical; the gammas move (their shape is df/2) but every primitive under
    them is the same."""
    sc0, c0, i0 = base_spec()
    sb, ob, db = run_arm(sc0, c0, i0)
    saved = M.LEVEL_DF
    try:
        M.LEVEL_DF = 4.0
        sa, oa, da = run_arm(sc0, c0, i0)
    finally:
        M.LEVEL_DF = saved
    _assert_population_and_primitives(sb, sa, sc0, i0, sc0, i0)
    assert np.array_equal(np.array(db.turnout_record), np.array(da.turnout_record))
    assert np.median(_corr_unchanged(ob, oa, i0, i0)) >= 0.9


def test_ward_noise_is_per_party_and_scales_with_its_sd():
    """V3 arm (vi): ward_noise_sd 0.10 → 0.12, and a party added to the
    universe. Every existing party's column of primitives is identical; the
    sd moves only the transform."""
    st0 = M.DrawStreams("v3|wards|1", 50)
    st1 = M.DrawStreams("v3|wards|1", 50)
    uni0, uni1 = list(PARTIES), list(PARTIES) + ["X"]
    for d in range(50):
        m0 = M.ward_noise_multiplier(st0, uni0, d, 9, 0.10)
        m1 = M.ward_noise_multiplier(st1, uni1, d, 9, 0.12)
        assert m0.shape == (9, 7) and m1.shape == (9, 8)
        assert np.allclose(np.log(m0) / 0.10, np.log(m1[:, :7]) / 0.12)


def test_a_dirichlet_shape_crossing_one_stays_paired():
    """V3 arm (vii) (review finding 1): a centre change built so one pool
    member's Dirichlet shape crosses 1. Its split gamma correlates above 0.99
    between arms. The boost applied only below shape 1 fails here."""
    sc0, c0, i0 = base_spec()
    sc0 = copy.deepcopy(sc0)
    sc0["pools"]["P1"]["alpha"] = 20.0
    sc0["_theta_sd"] = {p: 0.0 for p in PARTIES}   # isolate the split
    c0 = dict(c0, C=0.030)
    c1 = dict(c0, C=0.0315)
    sb, _, db = run_arm(sc0, c0, i0)
    sa, _, da = run_arm(sc0, c1, i0)
    # the member's shape is moved*alpha: read it off the drawer's own spec
    def shape_of(drawer, centres):
        spec = M.pool_spec(sc0, centres, i0)
        idx, _reg, _t, props, alpha, names, *_ = spec["P1"]
        return float(props[names.index("C")] * alpha)
    a0, a1 = shape_of(db, c0), shape_of(da, c1)
    assert a0 < 1.0 < a1, (a0, a1, "the constructed change does not cross 1")
    x = np.array(sb.gammas[("split", "P1|C")])
    y = np.array(sa.gammas[("split", "P1|C")])
    assert np.corrcoef(x, y)[0, 1] > 0.99


def test_a_tie_keyed_by_its_label_survives_losing_a_member_pool():
    """Review finding 3: removing one member pool of a tie leaves the other
    tied pool's turnout primitive bit-identical, because the stream is keyed by
    the declared label, not by the surviving members."""
    sc0, c0, i0 = base_spec(tie=True)
    sb, _, _ = run_arm(sc0, c0, i0)
    sc1 = copy.deepcopy(sc0)
    del sc1["pools"]["P3"]
    sa, _, _ = run_arm(sc1, c0, i0)
    assert ("turnout.pool", "T") in sb.keys and ("turnout.pool", "T") in sa.keys
    assert np.array_equal(np.array(sb.rows[("z", "turnout.pool", "T")]),
                          np.array(sa.rows[("z", "turnout.pool", "T")]))


def test_the_universal_law_pairs_the_same_arms():
    """V3 arms (i) at 1% and (iii) under the universal law (design 1j v4-L1)
    with the fixture record: the population is the one the spec implies (no
    gamma, no split, the calibration streams), the primitives are
    bit-identical, and the unchanged parties' drawn shares meet the
    pre-registered thresholds (prereg §6.3, V3.4)."""
    sc0, c0, i0 = base_spec(law="universal")
    sb, ob, db = run_arm(sc0, c0, i0)
    sc1, c1, _ = base_spec(law="universal")
    sc1["pools"]["P1"]["members"]["X"] = 1.0
    c1["X"] = 0.01
    i1 = {p: k for k, p in enumerate(PARTIES + ("X",))}
    sa, oa, da = run_arm(sc1, c1, i1)
    _assert_population_and_primitives(sb, sa, sc0, i0, sc1, i1)
    assert not any(st == "split" or st.endswith("level.chi") for st, _ in sb.keys)
    cs = _corr_unchanged(ob, oa, i0, i1)
    assert np.median(cs) >= 0.99 and cs.min() >= 0.95, cs
    c2 = dict(c0, B=c0["B"] * 1.2)
    sa2, oa2, _ = run_arm(sc0, c2, i0)
    _assert_population_and_primitives(sb, sa2, sc0, i0, sc0, i0)
    assert np.median(_corr_unchanged(ob, oa2, i0, i0, skip=("B",))) >= 0.99


def test_make_drawer_refuses_a_shared_generator():
    sc0, c0, i0 = base_spec()
    try:
        M.make_drawer(sc0, c0, c0, i0, np.random.default_rng(1))
    except TypeError as exc:
        assert "DrawStreams" in str(exc)
        return
    raise AssertionError("make_drawer accepted a np.random.Generator")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
