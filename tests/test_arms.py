"""The arm runner (`src/arms.py`) on a CONSTRUCTED model, never the real specs.

Step-6 item 8 of the 2026-10-11 model round. `run_model` is replaced by a
constructed one (`FakeModel`) that draws list shares from the run's seed and
city, records the scenario it was handed and writes into it the way the real
one does; the drawer inputs come from `test_draw_streams.base_spec`. What is
proved is the runner's mechanism: a fresh scenario per arm with that arm's
overrides, the files `plausibility.load_run_dir` reads, the refusals
(unconverged calibration, stale width record, wrong tree, an output under
`data/`), and the paired statistics (identical arms differ by exactly zero
with zero Monte Carlo error; a shifted arm is correlated; an independent arm
is not). A fixture proves mechanism, never magnitude.
"""

from __future__ import annotations

import json
import sys
import tempfile
import zlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import arms as A  # noqa: E402
import plausibility as P  # noqa: E402
from test_draw_streams import base_spec  # noqa: E402

PARTIES = ["A", "B", "C", "D", "E", "F", "G"]
CITY_YEARS = [("joburg", "2021"), ("tshwane", "2021"), ("ekurhuleni", "2016")]
DRAWS = 300


class FakeModel:
    """A constructed `run_model`. Shares are a Dirichlet around fixed centres
    from a generator keyed by (seed, city); the incumbent law draws from an
    independent generator; the centre correction multiplies party A by 1.1.
    It REFUSES a scenario that carries an earlier run's write, and then makes
    that write itself, as the real model does."""

    def __init__(self, converged=True, independent_law="incumbent"):
        self.converged = converged
        self.independent_law = independent_law
        self.seen: list[dict] = []

    def __call__(self, target, scenario, data_dir=None, verbose=False,
                 run_dir=None, stop_after=None):
        assert "_fake_ran" not in scenario, "a scenario reused across runs"
        if stop_after == "drawer_inputs":
            sc, c, i = base_spec(law="universal")
            return SimpleNamespace(scenario=sc, centres=c, index=i)
        self.seen.append({k: scenario.get(k) for k in
                          ("draw_law", "centre_correction", "level_shrink",
                           "seed", "draws")} | {"id": id(scenario)})
        scenario["_fake_ran"] = True
        scenario["_judgements_applied_sha"] = "0" * 16
        key = zlib.crc32(f"{scenario['seed']}|{target.city.slug}".encode())
        if scenario.get("draw_law") == self.independent_law:
            key += 1
        g = np.random.default_rng(key)
        base = np.array([30, 25, 15, 10, 10, 6, 4], float)
        S = g.dirichlet(base * 20, size=int(scenario["draws"]))
        if scenario.get("centre_correction"):
            S[:, 0] *= 1.1
            S = S / S.sum(axis=1, keepdims=True)
        law = scenario.get("draw_law")
        guards = {"draw_law": law,
                  "kappa_converged": (self.converged if law == "universal"
                                      else None),
                  "kappa_iters": 2 if law == "universal" else 0,
                  "kappa_error": {}, "mean_error": {}, "gamma_fallbacks": 0,
                  "gamma_draws": 0, "draws": S.shape[0]}
        W = g.integers(0, 3, size=(S.shape[0], 10))
        return SimpleNamespace(
            universe=list(PARTIES), pr_share_draws=S,
            pr_vote_draws=np.round(S * 1e6).astype(np.int64),
            ward_winner_draws=W, seat_draws=[{"A": 1}] * S.shape[0],
            guards=guards, pool_turnout_names=["P1", "P2"])


def _ok_width(year, scenario):
    return {"constructed": True}


def _run(out, arm, model, width_check=_ok_width, cys=CITY_YEARS):
    for city, year in cys:
        A.run_city_year(arm, city, year, out, draws=DRAWS, seed=11,
                        run_model=model, width_check=width_check)


def test_each_arm_gets_a_fresh_scenario_with_its_own_overrides():
    """Four arms run through ONE constructed model, which refuses a scenario
    an earlier run wrote into: every arm gets its own, with its overrides
    and the shared seed and draws. The census-off arm is refused in this
    tree (it carries the hold) and every other arm accepted."""
    model = FakeModel()
    with tempfile.TemporaryDirectory() as tmp:
        for arm in ("I", "U", "UC", "US"):
            _run(Path(tmp), arm, model, cys=CITY_YEARS[:1])
    assert len(model.seen) == 4 and len({s["id"] for s in model.seen}) == 4
    assert [s["draw_law"] for s in model.seen] == [
        "incumbent", "universal", "universal", "universal"]
    assert [bool(s["centre_correction"]) for s in model.seen] == [
        False, False, True, False]
    assert model.seen[3]["level_shrink"] == 0.0
    assert model.seen[1]["level_shrink"] != 0.0
    assert {(s["seed"], s["draws"]) for s in model.seen} == {(11, DRAWS)}
    assert A.census_hold_in_tree()
    for arm in ("I", "U", "UC", "US"):
        A.check_tree(arm)
    try:
        A.check_tree("C0")
    except SystemExit as exc:
        assert "C0 worktree" in str(exc)
    else:
        raise AssertionError("C0 ran in a tree carrying the census hold")


def test_the_files_are_what_plausibility_reads():
    """`arrays.npz` and `meta.json` load through `plausibility.load_run_dir`
    with the columns named, one row per draw, and the meta records the
    run's identity and the calibration pass."""
    with tempfile.TemporaryDirectory() as tmp:
        _run(Path(tmp), "U", FakeModel(), cys=CITY_YEARS[:1])
        d = Path(tmp) / "U" / "joburg-2021"
        run = P.load_run_dir(d)
        assert run["cols"] == PARTIES
        assert run["pr_share_draws"].shape == (DRAWS, len(PARTIES))
        assert run["ward_winner_draws"].max() < len(PARTIES)
        meta = json.loads((d / "meta.json").read_text())
        assert meta["kappa_converged"] is True and meta["seed"] == 11
        assert meta["width_record_current"] is True
        assert set(meta["pool_spec_centres"]) == set(PARTIES)
        assert abs(sum(meta["pool_spec_centres"].values()) - 1) < 1e-9


def test_an_unconverged_or_stale_city_year_is_refused_and_writes_no_arrays():
    """A universal arm whose calibration did not converge, or whose width
    record is stale, writes `REFUSED.json` and no arrays; the incumbent arm,
    which has no calibration, runs; reverted, the universal arm writes. A
    meta claiming non-convergence is refused by `load_arm`."""
    def stale(year, scenario):
        raise A.ArmRefused("width record: STALE (constructed)")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        for model, check, says in ((FakeModel(converged=False), _ok_width,
                                    "did not converge"),
                                   (FakeModel(), stale, "STALE")):
            try:
                A.run_city_year("U", "joburg", "2021", out, draws=DRAWS,
                                seed=11, run_model=model, width_check=check)
            except A.ArmRefused as why:
                assert says in str(why), why
            else:
                raise AssertionError(f"a run that should refuse ({says}) ran")
            d = out / "U" / "joburg-2021"
            assert (d / "REFUSED.json").exists()
            assert not (d / "arrays.npz").exists()
        A.run_city_year("I", "joburg", "2021", out, draws=DRAWS, seed=11,
                        run_model=FakeModel(converged=False))
        _run(out, "U", FakeModel(), cys=CITY_YEARS[:1])
        d = out / "U" / "joburg-2021"
        assert (d / "arrays.npz").exists() and not (d / "REFUSED.json").exists()
        assert len(A.load_arm(out, "U")) == 1
        meta = json.loads((d / "meta.json").read_text())
        (d / "meta.json").write_text(json.dumps(dict(meta,
                                                     kappa_converged=False)))
        try:
            A.load_arm(out, "U")
        except SystemExit:
            pass
        else:
            raise AssertionError("load_arm read an unconverged city-year")


def test_an_output_under_data_is_refused():
    for bad in (ROOT / "data", ROOT / "data" / "processed" / "arms"):
        try:
            A.check_out(bad)
        except SystemExit:
            continue
        raise AssertionError(f"{bad} accepted")
    A.check_out(ROOT / "audits" / "nowhere")


def _actuals():
    return {cy: dict(zip(PARTIES, [0.31, 0.24, 0.16, 0.1, 0.09, 0.06, 0.04]))
            for cy in CITY_YEARS}


def test_the_paired_statistics_see_zero_a_shift_and_independence():
    """US against U is the same draw here (the fake ignores the shrink):
    every difference is exactly zero, with zero Monte Carlo error, and R2's
    median correlation is 1. UC shifts one party: non-zero differences, the
    pairing holds (median correlation ≥ R2's bar). I is drawn independently:
    the median correlation collapses. Population: every city-year is a
    cluster, and every class interval counts its clusters."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        for arm in ("I", "U", "UC", "US"):
            _run(out, arm, model)
        same = A.compare(out, "U", "US", _actuals(), resamples=50)
        assert set(same["per_city_year"]) == {f"{c}-{y}" for c, y in CITY_YEARS}
        for row in same["per_city_year"].values():
            assert row["scored"]["list_mae_difference"] == 0.0
            assert row["scored"]["crps_mean_difference"] == 0.0
            assert row["scored"]["mc_error"]["list_mae"] == 0.0
            assert row["scored"]["mc_error"]["crps_mean"] == 0.0
            assert row["r2"]["median"] > 1 - 1e-12 and row["r2"]["passes"]
        assert same["cluster_interval"]["all"]["clusters"] == len(CITY_YEARS)
        assert same["classified_by"] == "I"
        shift = A.compare(out, "U", "UC", _actuals(), resamples=50)
        for row in shift["per_city_year"].values():
            assert row["scored"]["crps_mean_difference"] != 0.0
            assert row["scored"]["mc_error"]["crps_mean"] > 0
            assert row["r2"]["median"] >= A.R2_MIN_MEDIAN, row
        indep = A.compare(out, "I", "U", _actuals(), resamples=50)
        for row in indep["per_city_year"].values():
            assert abs(row["r2"]["median"]) < 0.5 and not row["r2"]["passes"]
        # arms of different draw counts are not paired
        A.run_city_year("UC", "joburg", "2021", out, draws=DRAWS + 1, seed=11,
                        run_model=model, width_check=_ok_width)
        try:
            A.compare(out, "U", "UC", _actuals(), resamples=5)
        except SystemExit as exc:
            assert "not paired" in str(exc)
        else:
            raise AssertionError("arms of different draws were compared")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
