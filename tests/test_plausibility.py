"""The plausibility instrument (`src/plausibility.py`), against the four-part rule.

Design: ``audits/2026-10-11-model-round/step1/1h-plausibility-check-design.md``
§5.3. Every input is CONSTRUCTED (a synthetic five-city record and synthetic
draws from the same process), except the one population test that reads the
real result files, and the import-closure test, which reads the source.

A world-like run draws from the process that made the record, so its draws are
exchangeable with the real outcomes; the tests then plant a defect (a tiny
party jumping, a collapse, zero spread) and require the instrument to see it,
and to go quiet on the same arrays with the defect removed.
"""

from __future__ import annotations

import ast
import math
import sys
from itertools import product
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import plausibility as P  # noqa: E402

YEARS = ("2000", "2006", "2011", "2016", "2021")
CITIES = ("c1", "c2", "c3", "c4", "c5")
N_PARTIES = 14
N_WARDS = 30


def _step(shares: np.ndarray, g, sd=0.25) -> np.ndarray:
    x = shares * np.exp(sd * g.standard_normal(shares.shape))
    return x / x.sum(axis=-1, keepdims=True)


def _winners(shares: np.ndarray, g) -> np.ndarray:
    """Ward winners for draws × parties: each ward a noisy copy of the city."""
    ward = shares[:, None, :] * np.exp(0.6 * g.standard_normal(
        (shares.shape[0], N_WARDS, shares.shape[1])))
    return ward.argmax(axis=2)


def synthetic_record(seed=1):
    g = np.random.default_rng(seed)
    names = [f"P{j:02d}" for j in range(N_PARTIES)]
    rec = {}
    for c in CITIES:
        base = np.array([40, 30, 10, 6, 4] + [1.5] * 3 + [0.4] * 6, float)
        s = base / base.sum()
        t = 0.55
        for y in YEARS:
            s = _step(s[None, :], g)[0]
            t = float(np.clip(t + 0.03 * g.standard_normal(), 0.3, 0.8))
            w = _winners(s[None, :], g)[0]
            rec[(c, y)] = {"pr": dict(zip(names, s)),
                           "winners": {f"w{i}": names[k] for i, k in enumerate(w)},
                           "registered": 1_000_000, "pr_valid": t * 1_000_000,
                           "turnout": t}
    return rec, names, g


def synthetic_runs(rec, names, g, draws=1000, years=("2016", "2021")):
    """World-like draws for each (city, year): the record's own process
    applied to the real previous election."""
    runs = {}
    for c, y in product(CITIES, years):
        prev = rec[(c, str(int(y) - 5))]
        s0 = np.array([prev["pr"][n] for n in names])
        S = _step(np.tile(s0, (draws, 1)), g)
        W = _winners(S, g)
        T = np.clip(prev["turnout"] + 0.03 * g.standard_normal(draws), 0.3, 0.8)
        runs[(c, y)] = {"pr_share_draws": S, "cols": names,
                        "pr_vote_draws": (S * (T * 1_000_000)[:, None]),
                        "ward_winner_draws": W}
    return runs


def _panel(rec, runs, mutate=None):
    trans = P.transitions(rec)
    targets = {}
    for (c, y), run in runs.items():
        r = dict(run)
        if mutate is not None:
            r = mutate(r)
        targets[(c, y)] = P.run_features(r, rec[(c, str(int(y) - 5))],
                                         rec[(c, y)]["registered"])
    return P.score_panel(targets, trans, "strict")


# --------------------------------------------------------------------------

def test_one_definition_for_draws_and_record():
    """(0) A real election passed as a one-row draw matrix gives the record's
    own features exactly: one definition serves both."""
    rec, names, _ = synthetic_record()
    prev, cur = rec[("c2", "2011")], rec[("c2", "2016")]
    real = P.real_features(prev, cur)
    cols = sorted(cur["pr"])
    S = np.array([[cur["pr"][n] for n in cols]])
    idx = {n: i for i, n in enumerate(cols)}
    W = np.array([[idx[p] for p in cur["winners"].values()]])
    run = {"pr_share_draws": S, "cols": cols,
           "pr_vote_draws": S * cur["pr_valid"], "ward_winner_draws": W}
    f = P.run_features(run, prev, cur["registered"])
    assert set(f) == set(P.CITY_FEATURES) == set(real)
    for k in real:
        assert abs(float(f[k][0]) - real[k]) < 1e-9, k


def _joint_rows(n=10):
    """Constructed rows for the eight joint features: record range [0, 1]
    for each, every draw at 0.5 (inside), the real election inside."""
    rows = {ft: {"record": [0.0, 1.0], "real_out": False}
            for ft in P.J8_FEATURES}
    feats = {ft: np.full(n, 0.5) for ft in P.J8_FEATURES}
    return rows, feats


def test_the_seven_and_eight_feature_counts_differ_by_w_top_alone():
    """Step-6 item 1: U1 is registered on the seven whole-vote features
    (prereg §5.1 row 1, §5.2 U1, §5.6 row 4), U3 on those plus `w_top`. A
    draw outside the record on `vol` and `w_top` alone has J = 1 on the seven
    and J = 2 on the eight; so has the real election. Population: each count
    names exactly the features of its set."""
    assert P.J7_FEATURES == tuple(f for f in P.J8_FEATURES if f != "w_top")
    assert "w_top" not in P.J7_FEATURES and len(P.J8_FEATURES) == 8
    assert P.JOINT_SETS == {"J7_no_w_top": P.J7_FEATURES,
                            "J8_with_w_top": P.J8_FEATURES}
    n = 10
    rows, feats = _joint_rows(n)
    feats["vol"][0] = 2.0
    feats["w_top"][0] = 2.0
    rows["vol"]["real_out"] = rows["w_top"]["real_out"] = True
    j7 = P.joint_count(P.J7_FEATURES, rows, feats, n, True)
    j8 = P.joint_count(P.J8_FEATURES, rows, feats, n, True)
    assert j7["features"] == list(P.J7_FEATURES) and j7["complete"]
    assert j8["features"] == list(P.J8_FEATURES) and j8["complete"]
    assert j7["p_ge2"] == 0.0 and j8["p_ge2"] == 1 / n, (j7, j8)
    assert (j7["real"], j8["real"]) == (1, 2)
    # it goes quiet: the w_top excursion removed, the two agree
    feats["w_top"][0] = 0.5
    rows["w_top"]["real_out"] = False
    j8 = P.joint_count(P.J8_FEATURES, rows, feats, n, True)
    assert j8["p_ge2"] == 0.0 and j8["real"] == 1


def test_a_joint_count_missing_a_feature_is_marked_and_left_out_of_the_panel():
    """A run with no ward winners has no `w_top`: the eight-feature count is
    marked incomplete, names what it lacks, and the panel leaves it out and
    lists the targets; the seven-feature count is complete at every scored
    target. With ward winners, both are complete everywhere."""
    rows, feats = _joint_rows()
    del rows["w_top"], feats["w_top"]
    j8 = P.joint_count(P.J8_FEATURES, rows, feats, 10, False)
    assert not j8["complete"] and j8["missing"] == ["w_top"]
    assert P.joint_count(P.J7_FEATURES, rows, feats, 10, False)["complete"]

    rec, names, g = synthetic_record()
    runs = synthetic_runs(rec, names, g, draws=200)

    def no_wards(r):
        r = dict(r)
        r.pop("ward_winner_draws")
        return r
    blind = _panel(rec, runs, mutate=no_wards)["panel"]
    assert blind["J8_with_w_top"]["scored"] == 0
    assert len(blind["J8_with_w_top"]["incomplete"]) == len(runs)
    assert blind["J7_no_w_top"]["scored"] == len(runs)
    assert blind["J7_no_w_top"]["incomplete"] == []
    seen = _panel(rec, runs)["panel"]
    assert seen["J8_with_w_top"]["scored"] == seen["J7_no_w_top"]["scored"] \
        == len(runs)
    assert "J" not in seen, "an unnamed joint count is back in the output"


def test_draw_population_equals_array_rows():
    """(0, 1) Every feature has one value per draw row; a column count that
    disagrees with the named columns raises."""
    rec, names, g = synthetic_record()
    runs = synthetic_runs(rec, names, g, draws=123)
    run = runs[("c1", "2021")]
    f = P.run_features(run, rec[("c1", "2016")], 1_000_000)
    assert all(np.asarray(v).shape == (123,) for v in f.values())
    bad = dict(run, cols=names[:-1])
    try:
        P.run_features(bad, rec[("c1", "2016")], 1_000_000)
    except ValueError:
        return
    raise AssertionError("a draw matrix with an unnamed column was accepted")


def test_poisson_binomial_against_enumeration():
    """(2) The convolution equals brute-force enumeration for n ≤ 10."""
    g = np.random.default_rng(5)
    for n in (1, 4, 10):
        ps = g.uniform(0, 1, n)
        dist = P.poisson_binomial(ps)
        brute = np.zeros(n + 1)
        for bits in product((0, 1), repeat=n):
            brute[sum(bits)] += np.prod([p if b else 1 - p
                                         for p, b in zip(ps, bits)])
        assert np.allclose(dist, brute, atol=1e-12)
        k = n // 2
        le, ge = P.event_tails(ps, k)
        assert abs(le - brute[:k + 1].sum()) < 1e-12
        assert abs(ge - brute[k:].sum()) < 1e-12


def test_a_count_features_pit_splits_its_ties():
    """Prereg §4 / v4 addendum §3.2: the PIT of a count feature is
    randomised over ties, so a realised value equal to every draw sits in the
    middle on average, not at 0 (which would put it outside the central 90%
    of every target and fail a calibrated model)."""
    g = np.random.default_rng(3)
    draws = np.full(500, 3.0)
    pits = np.array([P.randomised_pit(draws, 3.0, g) for _ in range(4000)])
    assert abs(pits.mean() - 0.5) < 0.02 and pits.min() < 0.05 < 0.95 < pits.max()
    assert P.randomised_pit(draws, 4.0, g) == 1.0
    assert P.randomised_pit(draws, 2.0, g) == 0.0


def test_reference_refuses_short_record():
    """(1) A target judged by fewer than the minimum transitions raises."""
    rec, _, _ = synthetic_record()
    trans = P.transitions(rec)
    assert len(P.reference(trans, 2021, "strict")) == 3 * len(CITIES)
    try:
        P.reference(trans, 2011, "strict")      # one cycle: 5 < 8
    except ValueError:
        return
    raise AssertionError("an empty-ish envelope was returned, not refused")


def test_tiny_jump_is_seen_and_unseen():
    """(2, 3) World-like draws keep `tiny_max` near the exchangeable rate and
    pass the event test; inflating one tiny party to 10% in 40% of rows drives
    P(X ≤ obs) below 0.01; the same arrays without the inflation pass again."""
    rec, names, g = synthetic_record(11)
    runs = synthetic_runs(rec, names, g)
    clean = _panel(rec, runs)["panel"]["tiny_max"]
    assert clean["p_le"] > 0.05 and clean["p_ge"] > 0.05, clean
    tiny = names.index("P13")

    def jump(r):
        S = np.array(r["pr_share_draws"], copy=True)
        rows = np.arange(S.shape[0]) % 5 < 2
        S[rows, tiny] = 0.10
        S[rows] /= S[rows].sum(axis=1, keepdims=True)
        return dict(r, pr_share_draws=S)
    bad = _panel(rec, runs, jump)["panel"]["tiny_max"]
    assert bad["p_le"] < 0.01, bad
    again = _panel(rec, runs)["panel"]["tiny_max"]
    assert again["p_le"] > 0.05


def test_collapse_is_seen_and_unseen():
    """(2, 3) Party level: world-like draws keep the under-1% class's collapse
    rate near 1/(n+1); collapsing every small party to a hundredth of its
    previous share in every draw fails the class; reverted, it passes."""
    rec, names, g = synthetic_record(13)
    runs = synthetic_runs(rec, names, g)
    trans = P.transitions(rec)

    def party_runs(mutate=None):
        out = {}
        for (c, y), r in runs.items():
            S = np.array(r["pr_share_draws"], copy=True)
            if mutate:
                S = mutate(S)
            out[(c, y)] = (rec[(c, str(int(y) - 5))]["pr"], names, S)
        return out
    clean = P.score_parties(party_runs(), rec, trans)["0"]
    assert not clean["fails"], clean

    def collapse(S):
        small = [j for j, n in enumerate(names) if j >= 8]
        S[:, small] *= 0.01
        return S / S.sum(axis=1, keepdims=True)
    bad = P.score_parties(party_runs(collapse), rec, trans)["0"]
    assert bad["fails"] and bad["collapse"] > 0.5, bad
    assert not P.score_parties(party_runs(), rec, trans)["0"]["fails"]


def test_two_sided():
    """(1, 2) Zero spread fails the upper tail of the event test (too
    narrow: the world leaves the record more often than the draws do);
    world-like draws pass both tails."""
    rec, names, g = synthetic_record(17)
    runs = synthetic_runs(rec, names, g)
    ok = _panel(rec, runs)["panel"]["vol"]
    assert ok["p_le"] > 0.05 and ok["p_ge"] > 0.05, ok

    def frozen(r):
        S = np.tile(np.asarray(r["pr_share_draws"])[0], (r["pr_share_draws"].shape[0], 1))
        return dict(r, pr_share_draws=S)
    narrow = _panel(rec, runs, frozen)["panel"]
    assert any(narrow[f].get("fails") for f in ("vol", "max_gain", "max_loss",
                                                "tiny_max")), narrow


def test_record_population_is_every_metro_and_cycle():
    """(0, 1) The only test reading live files: `record()` returns exactly the
    eight metros × the local elections with a result file, and the strict
    judging sets are 8 / 16 / 24 / 32 transitions for 2011 / 2016 / 2021 /
    2026, both directions."""
    import compare_history as CH
    import cityconfig
    rec = P.record()
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    expected = {(c, y) for c in CH.CITIES for y in lge}
    assert set(rec) == expected, (sorted(expected - set(rec))[:5],
                                  sorted(set(rec) - expected)[:5])
    trans = P.transitions(rec)
    sizes = {t: len(P.reference(trans, t, "strict")) for t in (2011, 2016, 2021, 2026)}
    assert sizes == {2011: 8, 2016: 16, 2021: 24, 2026: 32}, sizes
    scanned(trans, of=len(rec), low=0.5, high=1.0,
            what="consecutive real transitions", denominator="real elections")
    assert all(e["turnout"] and 0.1 < e["turnout"] < 1.0 for e in rec.values())


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


def import_closure(start: str, src: Path) -> set[str]:
    """Every `src/` module reachable from ``start`` by import, lazy imports
    inside functions included."""
    seen, todo = set(), [start]
    while todo:
        m = todo.pop()
        if m in seen or not (src / f"{m}.py").exists():
            continue
        seen.add(m)
        todo += [x for x in _imports(src / f"{m}.py") if x not in seen]
    return seen


def test_nothing_that_draws_imports_the_judge():
    """(0) Design §3.1: the instrument judges and sets nothing. No module in
    the import closure of `montecarlo` (which draws) imports `plausibility`.
    The detector can see a constructed violation, and goes quiet without it."""
    src = ROOT / "src"
    closure = import_closure("montecarlo", src)
    scanned(closure, of=len(list(src.glob("*.py"))), low=0.05, high=0.9,
            what="modules montecarlo can reach", denominator="modules in src/")
    assert "plausibility" not in closure, "a module the model imports imports the judge"
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        (t / "a.py").write_text("import b\n")
        (t / "b.py").write_text("def f():\n    import plausibility\n")
        (t / "plausibility.py").write_text("")
        assert "plausibility" in import_closure("a", t)
        (t / "b.py").write_text("def f():\n    return 1\n")
        assert "plausibility" not in import_closure("a", t)
        shutil.rmtree(t, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
