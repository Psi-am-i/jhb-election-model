"""``fold.fit_gamma``'s split into sums, the pooled γ, and the real-fit rule.

``prereg/2026-10-23-prefreeze-arms.md`` (arm GP and the amendment) needs γ
fitted over folds 1 and 2 together, and a definition of which fold rows are
real fits. Three things are tested here, each on constructed input:

1. ``fit_gamma`` returns what it returned before the split
   (``gamma_sums`` then ``gamma_from_sums``), against the pre-split formula
   written out in the test;
2. pooling adds the folds' sums, which equals the through-origin fit over the
   stacked VD rows and is NOT the mean of the folds' γs, on an input where the
   two differ; and a fold whose row is not a real fit contributes nothing;
3. the arms' rule (``rounds/2026-10-23-out-of-sample/prefreeze/run_arms.py``):
   a party fitted in both folds, in one, and in neither, and where each takes
   its γ from (the fold row, ``gamma_recent``, then 1.0).
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import fold  # noqa: E402

DRIVER = ROOT / "rounds/2026-10-23-out-of-sample/prefreeze/run_arms.py"


def _driver():
    spec = importlib.util.spec_from_file_location("prefreeze_run_arms", DRIVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fold_data(seed: int, n: int, weight_scale: float):
    """A constructed fold: two parties, ``n`` VDs, base and target shares
    with a known deviation pattern, VD weights scaled by ``weight_scale``."""
    rng = np.random.default_rng(seed)
    a = rng.uniform(0.2, 0.8, n)
    base = {f"v{i}": {"A": a[i], "B": 1 - a[i]} for i in range(n)}
    b = np.clip(a + rng.normal(0, 0.1, n) * (1 + seed), 0.05, 0.95)
    target = {f"v{i}": {"A": b[i], "B": 1 - b[i]} for i in range(n)}
    weights = {f"v{i}": int(100 * weight_scale * (1 + i)) for i in range(n)}
    base_city = {"A": float(a.mean()), "B": float(1 - a.mean())}
    target_city = {"A": float(b.mean()), "B": float(1 - b.mean())}
    return base, target, base_city, target_city, weights


def _pre_split_fit(base, target, base_city, target_city, weights, party):
    """``fit_gamma`` as written before 2026-10-23, verbatim in substance."""
    common = [vd for vd in base if vd in target]
    x, y, w = [], [], []
    for vd in common:
        x.append(fold.logit(base[vd].get(party, 0.0))
                 - fold.logit(base_city.get(party, fold.SHARE_FLOOR)))
        y.append(fold.logit(target[vd].get(party, 0.0))
                 - fold.logit(target_city.get(party, fold.SHARE_FLOOR)))
        w.append(weights.get(vd, 1))
    xa, ya, wa = np.array(x), np.array(y), np.array(w, dtype=float)
    denominator = float((wa * xa * xa).sum())
    if denominator == 0:
        return 0.0, len(common)
    return float((wa * xa * ya).sum() / denominator), len(common)


def test_fit_gamma_is_unchanged_by_the_split():
    for seed in range(4):
        data = _fold_data(seed, 30, 1.0)
        for party in ("A", "B", "absent"):
            got = fold.fit_gamma(*data, party)
            want = _pre_split_fit(*data, party)
            assert got == want, (party, got, want)
    # The zero-denominator branch: no deviation anywhere returns 0.0.
    flat = {f"v{i}": {"A": 0.5, "B": 0.5} for i in range(5)}
    city = {"A": 0.5, "B": 0.5}
    assert fold.fit_gamma(flat, flat, city, city, {}, "A") == (0.0, 5)
    assert fold.gamma_from_sums(3.0, 0.0) == 0.0


def test_pooling_is_stacking_rows_not_averaging_gammas():
    one = _fold_data(1, 25, 1.0)
    two = _fold_data(2, 40, 7.0)        # heavier VDs, more of them
    s1 = fold.gamma_sums(*one, "A")
    s2 = fold.gamma_sums(*two, "A")
    pooled = fold.gamma_from_sums(s1[0] + s2[0], s1[1] + s2[1])

    # The stacked fit, written out: every VD row of both folds, each with its
    # own fold's citywide means, in one through-origin weighted regression.
    xs, ys, ws = [], [], []
    for base, target, bc, tc, w in (one, two):
        for vd in base:
            xs.append(fold.logit(base[vd]["A"]) - fold.logit(bc["A"]))
            ys.append(fold.logit(target[vd]["A"]) - fold.logit(tc["A"]))
            ws.append(w[vd])
    xa, ya, wa = np.array(xs), np.array(ys), np.array(ws, dtype=float)
    stacked = float((wa * xa * ya).sum()) / float((wa * xa * xa).sum())
    assert math.isclose(pooled, stacked, rel_tol=1e-12), (pooled, stacked)

    g1, g2 = fold.fit_gamma(*one, "A")[0], fold.fit_gamma(*two, "A")[0]
    mean = (g1 + g2) / 2
    # The input must be one where the two readings differ, or this proves nothing.
    assert abs(pooled - mean) > 0.01, (pooled, mean, g1, g2)
    assert s1[2] + s2[2] == 65


def test_pooled_gamma_takes_only_real_fits():
    """``pooled_gamma`` on two constructed folds: A fitted in both, B fitted
    in fold 1 only (fold 2's base share under the threshold), C in neither
    (no target votes in fold 1, unseen in fold 2)."""
    one = _fold_data(3, 20, 1.0)
    two = _fold_data(4, 20, 3.0)
    folds = {}
    for n, (base, target, bc, tc, w) in ((1, one), (2, two)):
        base = {vd: dict(s) for vd, s in base.items()}
        bc = dict(bc)
        tc = dict(tc)
        for vd in base:
            base[vd]["B"] = 0.05 if n == 1 else 0.0005
        bc["B"] = 0.05 if n == 1 else 0.0005
        target = {vd: dict(s, B=0.04) for vd, s in target.items()}
        tc["B"] = 0.04
        if n == 1:
            bc["C"] = 0.02          # in the base, no votes in the target
        folds[n] = (base, target, bc, tc, w)

    saved = fold.fold_inputs, fold.fold_target
    try:
        fold.fold_inputs = lambda n, data_dir, *a, **k: {
            "base_share": folds[n][0], "base_city": folds[n][2],
            "base_weight": folds[n][4], "weight": folds[n][4],
            "weight_label": "constructed", "flagged": set()}
        fold.fold_target = lambda n, data_dir, ballot, base_city: (
            folds[n][1], folds[n][3], {},
            [p for p in set(base_city) | set(folds[n][3]) if p != "IND"])
        got = fold.pooled_gamma([1, 2], Path("unused"))
    finally:
        fold.fold_inputs, fold.fold_target = saved

    a, b, c = (got["PR"][p] for p in ("A", "B", "C"))
    assert a["contributing"] == [1, 2] and a["status"] == {1: fold.FITTED, 2: fold.FITTED}
    s1, s2 = (fold.gamma_sums(folds[n][0], folds[n][1], folds[n][2], folds[n][3],
                              folds[n][4], "A") for n in (1, 2))
    assert a["gamma"] == fold.gamma_from_sums(s1[0] + s2[0], s1[1] + s2[1])
    assert b["contributing"] == [1]
    assert b["status"] == {1: fold.FITTED, 2: fold.UNFITTED_BASE}
    assert b["gamma"] == fold.fit_gamma(*folds[1], "B")[0]
    assert c["contributing"] == [] and c["gamma"] is None
    assert c["status"] == {1: fold.UNFITTED_TARGET, 2: fold.UNFITTED_UNSEEN}


def test_the_pooled_file_reads_back_what_was_written():
    """``write_pooled`` then ``read_pooled``: the γ at four decimals, a blank
    γ for a party no fold fitted, the contributing folds and each fold's
    status; and ``--out`` under data/ is refused."""
    import argparse
    import tempfile
    constructed = {
        "PR": {"A": {"gamma": 0.81234, "sxy": 1.5, "sxx": 2.0, "n": 9,
                     "contributing": [1, 2],
                     "status": {1: fold.FITTED, 2: fold.FITTED}},
               "C": {"gamma": None, "sxy": 0.0, "sxx": 0.0, "n": 0,
                     "contributing": [],
                     "status": {1: fold.UNFITTED_TARGET, 2: fold.UNFITTED_UNSEEN}}},
        "Ward": {"A": {"gamma": -0.0926, "sxy": -1.0, "sxx": 10.8, "n": 9,
                       "contributing": [2],
                       "status": {1: fold.UNFITTED_BASE, 2: fold.FITTED}}}}
    saved = fold.pooled_gamma
    with tempfile.TemporaryDirectory() as tmp:
        args = argparse.Namespace(pool="1,2", out=Path(tmp), fit_from=None,
                                  entrant=[], turnout="level", stability="all",
                                  w_split=0.6, data_dir=Path("unused"))
        try:
            fold.pooled_gamma = lambda folds, data_dir: constructed
            assert fold.write_pooled(args) == 0
        finally:
            fold.pooled_gamma = saved
        got = fold.read_pooled(fold.pooled_path(Path(tmp), [1, 2]))
    assert got["PR"]["A"] == {"gamma": 0.8123, "contributing": [1, 2],
                              "status": {1: fold.FITTED, 2: fold.FITTED}}
    assert got["PR"]["C"]["gamma"] is None and got["PR"]["C"]["contributing"] == []
    assert got["Ward"]["A"]["gamma"] == -0.0926
    assert got["Ward"]["A"]["status"] == {1: fold.UNFITTED_BASE, 2: fold.FITTED}
    try:
        fold.refuse_data_out(ROOT / "data" / "x")
    except SystemExit:
        pass
    else:
        raise AssertionError("--out under data/ was not refused")
    fold.refuse_data_out(Path(tempfile.gettempdir()))


def test_fit_status_names_each_placeholder():
    universe = ["A", "B", "C"]
    base_city = {"A": 0.3, "B": 0.001, "C": 0.2}
    target_city = {"A": 0.3, "B": 0.01}
    assert fold.fit_status("A", base_city, target_city, universe) == fold.FITTED
    assert fold.fit_status("B", base_city, target_city, universe) == fold.UNFITTED_BASE
    assert fold.fit_status("C", base_city, target_city, universe) == fold.UNFITTED_TARGET
    assert fold.fit_status("D", base_city, target_city, universe) == fold.UNFITTED_UNSEEN


def test_the_arms_rule_on_parties_fitted_in_both_one_and_neither():
    D = _driver()
    F, BASE, TGT, UNS = (fold.FITTED, fold.UNFITTED_BASE, fold.UNFITTED_TARGET,
                         fold.UNFITTED_UNSEEN)
    # BOTH fitted in both folds; ONE in fold 2 only; NEITHER in neither, with
    # a recent γ; NOREC in neither, without one.
    pooled = {b: {
        "BOTH": {"gamma": 0.8, "contributing": [1, 2], "status": {1: F, 2: F}},
        "ONE": {"gamma": 0.6, "contributing": [2], "status": {1: BASE, 2: F}},
        "NEITHER": {"gamma": None, "contributing": [], "status": {1: TGT, 2: UNS}},
        "NOREC": {"gamma": None, "contributing": [], "status": {1: BASE, 2: BASE}},
    } for b in ("PR", "Ward")}
    fold1 = {b: {"theta": {}, "theta_raw": {},
                 "gamma": {"BOTH": 0.9, "ONE": 1.0, "NEITHER": 0.0, "NOREC": 1.0}}
             for b in ("PR", "Ward")}
    fold2 = {b: {"theta": {}, "theta_raw": {},
                 "gamma": {"BOTH": 0.7, "ONE": 0.6, "NOREC": 1.0}}
             for b in ("PR", "Ward")}
    recent = {"NEITHER": 0.5, "ONE": 0.4}
    universe = ["BOTH", "ONE", "NEITHER", "NOREC"]

    def drawn(arm, params):
        return {p: D.expected_gamma(params, recent, universe, arm, pooled)["PR"][p]
                for p in universe}

    # B: the fold-1 file as written, placeholders block gamma_recent.
    b = drawn("B", fold1)
    assert b["ONE"] == (1.0, f"fold1 placeholder ({BASE})")
    assert b["NEITHER"] == (0.0, f"fold1 placeholder ({TGT})")
    assert b["BOTH"] == (0.9, "fold1")

    bf = drawn("BF", D.real_fit_rows(fold1, pooled, 1))
    assert bf == {"BOTH": (0.9, "fold1"), "ONE": (0.4, "recent"),
                  "NEITHER": (0.5, "recent"), "NOREC": (1.0, "default 1.0")}

    g2 = drawn("G2", D.real_fit_rows(fold2, pooled, 2))
    assert g2 == {"BOTH": (0.7, "fold2"), "ONE": (0.6, "fold2"),
                  "NEITHER": (0.5, "recent"), "NOREC": (1.0, "default 1.0")}

    gp = drawn("GP", D.pooled_rows(pooled))
    assert gp == {"BOTH": (0.8, "pooled 1+2"), "ONE": (0.6, "pooled 2"),
                  "NEITHER": (0.5, "recent"), "NOREC": (1.0, "default 1.0")}
    # The rule must not mutate the file it filters.
    assert fold1["PR"]["gamma"]["ONE"] == 1.0


def test_the_arms_patch_reaches_run_model():
    """The γ switch replaces ``montecarlo.load_parameters`` in process. That
    reaches ``run_model`` only because ``run_model`` looks the name up as a
    module global; and the substitute must be handed out for the fold-1 file
    only, as a copy, and be removed afterwards."""
    import montecarlo as M
    D = _driver()
    assert "load_parameters" in M.run_model.__code__.co_names
    params = {"PR": {"theta": {}, "theta_raw": {}, "gamma": {"X": 0.5}}}
    counter: dict = {}
    original = M.load_parameters
    with D.patched(params, None, 1, counter):
        got = M.load_parameters(Path("anywhere/fold1_parameters.csv"))
        assert got == params and got is not params
        assert M.load_parameters is not original
    assert counter == {"fold_loads": 1}
    assert M.load_parameters is original


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
