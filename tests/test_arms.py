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


COUNCIL = 40


def _lr(shares, council):
    """Largest remainder of one share vector: the fixture's seat law."""
    exact = np.asarray(shares, dtype=float) * council
    base = np.floor(exact).astype(int)
    for j in np.argsort(-(exact - base))[:council - int(base.sum())]:
        base[j] += 1
    return [int(x) for x in base]


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
            ward_winner_draws=W,
            seat_draws=[dict(zip(PARTIES, _lr(row, COUNCIL))) for row in S],
            guards=guards, pool_turnout_names=["P1", "P2"])


def _ok_width(year, scenario):
    return {"constructed": True}


# The runner records the live commit and whether src/ is dirty; a test must
# not depend on the working tree it happens to run in, so the git reads are
# constructed: one clean commit, its parent as C0's final tree.
_REAL_GIT = A._git


def _fake_git(*args):
    if args[:1] == ("status",):
        return ""
    if args == ("rev-parse", "HEAD"):
        return "c" * 40
    if args == ("rev-parse", "HEAD^"):
        return "f" * 40
    return _REAL_GIT(*args)


A._git = _fake_git


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
        same = A.compare(out, "U", "US", _actuals(), resamples=50,
                         population=CITY_YEARS)
        assert set(same["per_city_year"]) == {f"{c}-{y}" for c, y in CITY_YEARS}
        for row in same["per_city_year"].values():
            assert row["score"]["list_mae_difference"] == 0.0
            assert row["score"]["crps_mean_difference"] == 0.0
            assert row["score"]["mc_error"]["list_mae"] == 0.0
            assert row["score"]["mc_error"]["crps_mean"] == 0.0
            assert row["r2"]["median"] > 1 - 1e-12 and row["r2"]["passes"]
        assert same["cluster_interval"]["all"]["clusters"] == len(CITY_YEARS)
        assert same["classified_by"] == "I"
        shift = A.compare(out, "U", "UC", _actuals(), resamples=50,
                          population=CITY_YEARS)
        for row in shift["per_city_year"].values():
            assert row["score"]["crps_mean_difference"] != 0.0
            assert row["score"]["mc_error"]["crps_mean"] > 0
            assert row["r2"]["median"] >= A.R2_MIN_MEDIAN, row
        indep = A.compare(out, "I", "U", _actuals(), resamples=50,
                          population=CITY_YEARS)
        for row in indep["per_city_year"].values():
            assert abs(row["r2"]["median"]) < 0.5 and not row["r2"]["passes"]
        # arms of different draw counts are not paired
        A.run_city_year("UC", "joburg", "2021", out, draws=DRAWS + 1, seed=11,
                        run_model=model, width_check=_ok_width)
        try:
            A.compare(out, "U", "UC", _actuals(), resamples=5,
                      population=CITY_YEARS)
        except SystemExit as exc:
            assert "not paired" in str(exc)
        else:
            raise AssertionError("arms of different draws were compared")


def _meta_path(out, arm, cy):
    return Path(out) / arm / f"{cy[0]}-{cy[1]}" / "meta.json"


def _edit_meta(out, arm, cy, **kw):
    p = _meta_path(out, arm, cy)
    m = json.loads(p.read_text())
    m.update(kw)
    p.write_text(json.dumps(m))
    return m


def test_the_scored_population_is_the_prereg_s_and_2011_enters_no_interval():
    """Prereg §2: the scored population is the 16 city-years of 2016 and
    2021, one definition (`plausibility.scored_population`) for both
    scorers, its size asserted. A 2011 city-year run beside a constructed
    population is reported with `scored` false and its reason, carries its
    scores (S6 reads them), and changes no interval: the intervals with and
    without it are identical and count the population's clusters. Mutation
    probe: dropping the `key in pop_set` gate puts 2011 into the intervals
    and this test goes red."""
    pop = P
    full = pop.scored_population()
    assert len(full) == pop.SCORED_COUNT == 16
    assert {y for _c, y in full} == {"2016", "2021"}
    import compare_history as CH
    assert set(full) == {(c, y) for c in CH.CITIES for y in ("2016", "2021")}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        for arm in ("I", "U", "UC"):
            _run(out, arm, model)
        act = _actuals()
        base = A.compare(out, "U", "UC", act, resamples=5,
                         population=CITY_YEARS)
        for arm in ("I", "U", "UC"):
            _run(out, arm, model, cys=[("joburg", "2011")])
        act[("joburg", "2011")] = act[CITY_YEARS[0]]
        res = A.compare(out, "U", "UC", act, resamples=5,
                        population=CITY_YEARS)
        row = res["per_city_year"]["joburg-2011"]
        assert row["scored"] is False and "untestable" in row["not_scored_because"]
        assert "list_mae_difference" in row["score"]
        assert res["cluster_interval"] == base["cluster_interval"]
        assert res["cluster_interval"]["all"]["clusters"] == len(CITY_YEARS)
        assert res["population"]["scored"] == sorted(
            f"{c}-{y}" for c, y in CITY_YEARS)


def test_an_incomplete_population_refuses_unless_the_flag_is_passed():
    """A population member missing from one arm refuses, naming it; with
    `allow_incomplete` the comparison runs and its output records the flag,
    the missing city-year and the city-year present in one arm only.
    Mutation probe: the refusal removed, the first assertion goes red."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        for arm in ("I", "U"):
            _run(out, arm, model)
        _run(out, "UC", model, cys=CITY_YEARS[:2])
        try:
            A.compare(out, "U", "UC", _actuals(), resamples=5,
                      population=CITY_YEARS)
        except SystemExit as exc:
            assert "ekurhuleni-2016" in str(exc), exc
        else:
            raise AssertionError("an incomplete population was scored")
        res = A.compare(out, "U", "UC", _actuals(), resamples=5,
                        population=CITY_YEARS, allow_incomplete=True)
        pb = res["population"]
        assert pb["allow_incomplete"] is True and pb["complete"] is False
        assert pb["missing_in_UC"] == ["ekurhuleni-2016"]
        assert pb["only_in_U"] == ["ekurhuleni-2016"]
        assert res["cluster_interval"]["all"]["clusters"] == 2


def test_the_pair_must_be_the_registered_one():
    """`check_pairing`: different pool specs, a different commit, a dirty
    tree, the shrink-off variant on an arm other than US (or the shipped
    variant on US) each refuse; C0 is accepted only when its
    `final_commit` is the other arm's commit and it ran without the hold.
    Each refusal is constructed by editing one field of a meta written by
    the runner and reverted before the next."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        cy = CITY_YEARS[:1]
        for arm in ("I", "U", "UC", "US", "C0"):
            _run(out, arm, model, cys=cy)
        # C0 ran in its own worktree: its own commit, whose parent is the
        # final tree the other arms ran at (amendment 3)
        _edit_meta(out, "C0", cy[0], census_hold=False, final_commit="c" * 40,
                   git={"commit": "0" * 40, "dirty": False})
        kw = dict(resamples=3, population=cy)
        A.compare(out, "U", "UC", _actuals(), **kw)
        A.compare(out, "U", "US", _actuals(), **kw)
        A.compare(out, "I", "U", _actuals(), **kw)
        mu = json.loads(_meta_path(out, "UC", cy[0]).read_text())
        mus = json.loads(_meta_path(out, "US", cy[0]).read_text())
        assert json.loads(mus["width_record_variant"])["level_shrink"] == 0.0
        cases = [
            ("UC", dict(spec_keys={"x": "moved"}), "pool specs", "U"),
            ("UC", dict(git={"commit": "d" * 40, "dirty": False}),
             "different commits", "U"),
            ("UC", dict(git={"commit": "c" * 40, "dirty": True}), "dirty",
             "U"),
            ("UC", dict(width_record_variant=mus["width_record_variant"]),
             "level_shrink = 0 for US", "U"),
            ("US", dict(width_record_variant=mu["width_record_variant"]),
             "level_shrink = 0 for US", "U"),
            ("UC", dict(width_record_key={"record_sha": "other"}),
             "different keys", "U"),
            ("C0", dict(final_commit="e" * 40), "final tree", "U"),
            ("C0", dict(census_hold=True), "census hold", "U"),
        ]
        for arm, edit, says, other in cases:
            keep = json.loads(_meta_path(out, arm, cy[0]).read_text())
            _edit_meta(out, arm, cy[0], **edit)
            try:
                A.compare(out, other, arm, _actuals(), **kw)
            except SystemExit as exc:
                assert says in str(exc), (arm, edit, exc)
            else:
                raise AssertionError(f"{arm} {edit} was compared")
            _meta_path(out, arm, cy[0]).write_text(json.dumps(keep))
            A.compare(out, other, arm, _actuals(), **kw)
        # C0's specs and record are its own: they are not compared
        _edit_meta(out, "C0", cy[0], spec_keys={"c0": "own emit"},
                   width_record_key={"record_sha": "c0"})
        A.compare(out, "U", "C0", _actuals(), **kw)


def test_parties_drawn_by_neither_arm_enter_no_class_and_the_classifier_must_exist():
    """A party only in the actuals has identical zero mass in both arms; it
    is listed with its share and leaves every interval unchanged. Without
    the exclusion it would add zero-difference rows to `small` and `all`
    (mutation probe: the `undrawn` exclusion removed changes the `all`
    interval and this test goes red). A classifying arm that has not run
    refuses: there is no fallback to another arm's centres."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        for arm in ("I", "U", "UC"):
            _run(out, arm, model)
        kw = dict(resamples=3, population=CITY_YEARS)
        base = A.compare(out, "U", "UC", _actuals(), **kw)
        act = {k: dict(v, ZZ=0.004) for k, v in _actuals().items()}
        res = A.compare(out, "U", "UC", act, **kw)
        for row in res["per_city_year"].values():
            assert row["score"]["undrawn_actual"] == {"ZZ": 0.004}
        assert res["cluster_interval"]["all"]["n"] == \
            base["cluster_interval"]["all"]["n"]
        assert res["cluster_interval"] == base["cluster_interval"]
        import shutil
        shutil.rmtree(out / "I")
        try:
            A.compare(out, "U", "UC", _actuals(), **kw)
        except SystemExit as exc:
            assert "has not run" in str(exc), exc
        else:
            raise AssertionError("compared with no classifying arm")


# --------------------------------------------------------------------------
# the registered instruments (prereg §10; amendment 3)
# --------------------------------------------------------------------------

def test_wrong_party_seats_is_half_the_summed_error_of_the_coherent_council():
    """U15, S4. Three draws of a ten-seat council: the mean vector
    (5, 3.33, 1.67) apportioned by largest remainder is (5, 3, 2); against
    an actual (3, 4, 2) plus a party D the model never seated with 1, the
    summed absolute error over the union is 2 + 1 + 0 + 1 = 4, so 2 seats
    were given to the wrong party. An ENTRANT column refuses."""
    draws = np.array([[5, 3, 2], [6, 3, 1], [4, 4, 2]])
    got = A.wrong_party_seats(draws, ["A", "B", "C"], 10,
                              {"A": 3, "B": 4, "C": 2, "D": 1})
    assert got == 2.0, got
    assert A.wrong_party_seats(draws, ["A", "B", "C"], 10,
                               {"A": 5, "B": 3, "C": 2}) == 0.0
    try:
        A.wrong_party_seats(draws, ["A", "B", "ENTRANT"], 10, {"A": 10})
    except SystemExit as exc:
        assert "ENTRANT" in str(exc)
    else:
        raise AssertionError("an ENTRANT column was scored unrelabelled")


def test_the_band_and_the_log_sd_on_constructed_columns():
    """U11/U14: a realised share inside [P5, P95] counts, the ends included,
    and one outside does not. U12/M4: the drawn log-sd of a lognormal
    column is its log sd (to the sample); a column with a zero draw is
    excluded by name, not floored."""
    S = np.linspace(0.0, 1.0, 1001)[:, None].repeat(4, axis=1)
    got = A.band_inside(S, np.array([0.5, 0.05, 0.95, 0.01]))
    assert got.tolist() == [True, True, True, False], got
    g = np.random.default_rng(3)
    z = g.standard_normal(20000)
    cols = np.c_[0.2 * np.exp(0.3 * z), 0.1 * np.exp(0.1 * z),
                 np.r_[0.0, np.full(19999, 0.05)]]
    sd, excl = A.drawn_log_sd(cols, ["X", "Y", "Z"])
    assert abs(sd["X"] - 0.3 * z.std()) < 1e-12
    assert abs(sd["Y"] - 0.1 * z.std()) < 1e-12
    assert excl == ["Z"] and "Z" not in sd
    ex = A.width_excess(sd, {"X": {"total": 0.25}, "Y": {"total": 0.2}})
    assert abs(ex["excess"]["X"] - (sd["X"] - 0.25)) < 1e-12
    assert ex["max"] == max(ex["excess"].values()) and ex["parties"] == 2


def test_the_implausible_draw_counts_follow_the_registered_definition():
    """§5.6 row 1: draws with an ESTABLISHED party (previous share above 0
    and under 1%) drawn above 5%. Constructed: X (previous 0.5%) exceeds 5%
    in exactly 7 draws, Y (previous 2%) in 50, N (new, previous 0) in 30;
    only X's 7 count. Row 2 reads arm I's centres: X's centre and Y's are
    under 1%, and their exceedances are in disjoint draws, so 57 count."""
    D = 200
    S = np.full((D, 4), 0.01)
    S[:, 3] = 1 - S[:, :3].sum(axis=1)
    S[:7, 0] = 0.06
    S[10:60, 1] = 0.07
    S[100:130, 2] = 0.08
    cols = ["X", "Y", "N", "BIG"]
    prev = {"X": 0.005, "Y": 0.02, "BIG": 0.9, "GONE": 0.004}
    got = A.implausible_draws(S, cols, prev, None)
    assert got["established_under_1_above_5"] == 7, got
    assert got["established_parties"] == 1
    assert got["centre_under_1_above_5"] is None
    got = A.implausible_draws(S, cols, prev, {"X": 0.004, "Y": 0.008,
                                              "N": 0.02, "BIG": 0.9})
    assert got["centre_under_1_above_5"] == 57, got
    assert got["centre_parties"] == 2


def test_compare_carries_every_registered_instrument():
    """On the constructed arms: identical arms (U, US) give zero per-cycle
    differences, equal band coverage and log-sd medians, and zero
    wrong-party-seat difference; the per-cycle class means recombine, by
    their counts, into the pooled mean the cluster interval reports; the
    band counts cover every classed party-city-year; the §5.6 counts appear
    at a forecast in `previous`. Population: the per-cycle city-years sum
    to the scored population."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        for arm in ("I", "U", "UC", "US"):
            _run(out, arm, model)
            _run(out, arm, model, cys=[("joburg", "2026")])
        seats = {cy: (COUNCIL, dict(zip(PARTIES, _lr(
            [0.31, 0.24, 0.16, 0.1, 0.09, 0.06, 0.04], COUNCIL))))
                 for cy in CITY_YEARS}
        prev = {("joburg", "2026"): {"A": 0.3, "F": 0.005, "G": 0.004}}
        kw = dict(resamples=3, population=CITY_YEARS, seats_actual=seats,
                  previous=prev)
        same = A.compare(out, "U", "US", _actuals(), **kw)["instruments"]
        assert sum(v["city_years"] for v in same["per_cycle"].values()) == \
            len(CITY_YEARS)
        for v in same["per_cycle"].values():
            assert v["list_mae_difference_mean"] == 0.0
            assert v["crps_mean_difference"]["all"]["mean"] == 0.0
        assert same["band_coverage"]["U"] == same["band_coverage"]["US"]
        assert same["large_log_sd_median"]["U"] == \
            same["large_log_sd_median"]["US"]
        assert same["wrong_party_seats"]["total"]["difference"] == 0.0
        assert same["implausible_draws"]["joburg-2026"]["difference"] == {
            "established_under_1_above_5": 0, "centre_under_1_above_5": 0}
        res = A.compare(out, "U", "UC", _actuals(), **kw)
        inst = res["instruments"]
        pooled = sum(v["crps_mean_difference"]["all"]["mean"]
                     * v["crps_mean_difference"]["all"]["n"]
                     for v in inst["per_cycle"].values())
        n = sum(v["crps_mean_difference"]["all"]["n"]
                for v in inst["per_cycle"].values())
        assert abs(pooled / n - res["cluster_interval"]["all"]["point"]) < 1e-12
        assert n == res["cluster_interval"]["all"]["n"]
        classed = sum(c["of"] for c in inst["band_coverage"]["UC"].values())
        assert classed == n == len(CITY_YEARS) * len(PARTIES)
        per = inst["wrong_party_seats"]["per_city_year"]
        assert set(per) == {f"{c}-{y}" for c, y in CITY_YEARS}
        assert abs(inst["wrong_party_seats"]["total"]["difference"]
                   - sum(r["difference"] for r in per.values())) < 1e-12
        cnt = inst["implausible_draws"]["joburg-2026"]["U"]
        assert cnt["draws"] == DRAWS and cnt["established_parties"] == 2


def test_describe_reads_the_run_s_own_widths_and_the_forecast_counts():
    """M4/M5 and §5.6 for one arm: the drawn log-sd per party, its excess
    over the run's `trace/35_widths` total, and at a forecast in `previous`
    the counts, with the centres of arm I."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        model = FakeModel()
        for arm in ("I", "U"):
            _run(out, arm, model, cys=[("joburg", "2026")])
        tr = out / "U" / "joburg-2026" / "trace"
        tr.mkdir(parents=True, exist_ok=True)
        (tr / "35_widths.json").write_text(json.dumps(
            {"parties": {p: {"total": 0.1} for p in PARTIES}}))
        res = A.describe(out, "U", {("joburg", "2026"): {"F": 0.005}})
        row = res["per_city_year"]["joburg-2026"]
        S = P.load_run_dir(out / "U" / "joburg-2026")["pr_share_draws"]
        S = S / S.sum(axis=1, keepdims=True)
        assert abs(row["drawn_log_sd"]["A"] - np.log(S[:, 0]).std()) < 1e-12
        assert abs(row["m5"]["excess"]["A"]
                   - (row["drawn_log_sd"]["A"] - 0.1)) < 1e-12
        assert row["implausible"]["established_parties"] == 1
        assert row["implausible"]["centre_under_1_above_5"] is not None


def test_the_c0_tree_is_the_final_tree_with_only_the_census_pools_hunks_reverted():
    """Amendment 3 point 7. The C0 recipe reverts the census commit's
    `src/pools.py` hunks on the final tree, nothing else (a whole-commit
    revert conflicts in `tests/test_pool_bounds.py` and `MODEL-INDEX.md`).
    Constructed from this tree's committed `pools.py`: the reverted text
    restores `REGISTRATION_MAX` and drops `IDENTIFICATION_REACH`, and
    `c0_faults` accepts it; one extra edit to the reverted file, or a second
    changed path, is refused; the unreverted file is refused. Mutation
    probes: the byte comparison removed, or the path check removed, each
    turn this red."""
    final = _REAL_GIT("show", f"HEAD:{A.CENSUS_PATH}") + "\n"
    patch = _REAL_GIT("diff", f"{A.CENSUS_COMMIT}^", A.CENSUS_COMMIT, "--",
                      A.CENSUS_PATH) + "\n"
    assert "IDENTIFICATION_REACH" in final and patch.startswith("diff --git")
    c0 = A.reverse_census(final, patch)
    assert "REGISTRATION_MAX =" in c0 and "IDENTIFICATION_REACH =" not in c0
    assert A.c0_faults(final, c0, [A.CENSUS_PATH], patch) == []
    assert A.c0_faults(final, c0 + "X = 1\n", [A.CENSUS_PATH], patch)
    assert A.c0_faults(final, c0, [A.CENSUS_PATH,
                                   "tests/test_pool_bounds.py"], patch)
    assert A.c0_faults(final, final, [A.CENSUS_PATH], patch)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
