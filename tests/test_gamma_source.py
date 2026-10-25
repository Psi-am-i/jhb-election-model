"""Which γ a run reads: the fold file's status column, the placeholder skip,
the per city-year source, and the precedence check over a pool.

``prereg/2026-10-23-freeze-settings.md`` changes 1 and 2 (DATA-QUALITY 21;
JUDGEMENT-CALLS §V1, §V2). Tested on constructed files:

1. a fold file round-trips its ``fit_status`` column: ``fold.load_parameters``
   reads γ from ``fitted`` rows only, θ from every row, and REFUSES a file
   without the column; ``fold.main`` writes the column last, after value
   columns it leaves as they were (real data, skipped when absent);
2. ``montecarlo.resolve_gamma``: Johannesburg 2026 reads the pooled file and
   labels each party by the folds that contributed; Tshwane 2026 reads its
   fold-1 file, where a placeholder row falls through to ``recent`` and is
   never labelled as a fold; a missing pooled file is refused;
3. ``gamma_folds_for`` checks every fold in a pool against the target year,
   and ``gamma_fold_for`` refuses a pooled target;
4. ``declares._fit_rows``: a fold file with and without the column, and a
   pooled file that agrees and one that disagrees with the fold files beside it.
"""

from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import cityconfig  # noqa: E402
import declares  # noqa: E402
import fold  # noqa: E402
import montecarlo as M  # noqa: E402

HEADER = ["ballot", "party", "theta_raw", "theta_calibrated", "gamma", "fit_status"]


def _write_fold(path: Path, rows, status=True) -> None:
    """``rows``: (ballot, party, theta_raw, theta_cal, gamma, status)."""
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER if status else HEADER[:-1])
        for r in rows:
            w.writerow(r if status else r[:-1])


def _write_pooled(path: Path, rows, folds=(1, 2)) -> None:
    """``rows``: (ballot, party, gamma or "", contributing, {fold: status})."""
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["ballot", "party", "gamma", "sum_wxy", "sum_wxx", "n_vd",
                    "contributing"] + [f"fold{f}" for f in folds])
        for ballot, party, g, contributing, status in rows:
            w.writerow([ballot, party, g, "0.0", "0.0", 0, contributing]
                       + [status[f] for f in folds])


def _target(slug: str, year: str):
    return SimpleNamespace(city=SimpleNamespace(slug=slug), year=year)


class _CityProcessed:
    """``cityconfig.active()`` answering ``processed = root`` for the block."""

    def __init__(self, root: Path):
        self.root, self.saved = root, cityconfig.active

    def __enter__(self):
        cityconfig.active = lambda: SimpleNamespace(processed=self.root)
        return self

    def __exit__(self, *exc):
        cityconfig.active = self.saved


F, BASE, TGT, UNS = (fold.FITTED, fold.UNFITTED_BASE, fold.UNFITTED_TARGET,
                     fold.UNFITTED_UNSEEN)
FOLD1 = [("PR", "A", "1.0000", "1.1000", "0.8000", F),
         ("PR", "P", "1.0000", "2.0000", "1.0000", BASE),
         ("PR", "Z", "0.0000", "0.0000", "0.0000", TGT),
         ("Ward", "A", "1.0000", "1.2000", "0.7000", F),
         ("Ward", "P", "1.0000", "2.1000", "1.0000", BASE),
         ("Ward", "Z", "0.0000", "0.0000", "0.0000", TGT)]


# --------------------------------------------------------------------------
# 1. the status column
# --------------------------------------------------------------------------

def test_load_parameters_reads_fitted_gamma_only_and_every_theta():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fold1_parameters.csv"
        _write_fold(path, FOLD1)
        got = fold.load_parameters(path)
    assert got["PR"]["gamma"] == {"A": 0.8}
    assert got["Ward"]["gamma"] == {"A": 0.7}
    # θ is calibrated for every party, placeholders included.
    assert got["PR"]["theta"] == {"A": 1.1, "P": 2.0, "Z": 0.0}
    assert got["PR"]["status"] == {"A": F, "P": BASE, "Z": TGT}
    # The detector goes quiet when the rows are real fits.
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fold1_parameters.csv"
        _write_fold(path, [r[:5] + (F,) for r in FOLD1])
        assert set(fold.load_parameters(path)["PR"]["gamma"]) == {"A", "P", "Z"}


def test_load_parameters_refuses_a_file_without_the_column():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "fold1_parameters.csv"
        _write_fold(path, FOLD1, status=False)
        try:
            fold.load_parameters(path)
        except SystemExit as exc:
            assert "fit_status" in str(exc) and "fold.py --fold" in str(exc)
        else:
            raise AssertionError("a fold file without fit_status was read")


def test_fold_main_writes_the_status_column_last():
    """Real data: fold 1 refit into a scratch directory. The header gains
    ``fit_status`` as its last column, and each row's status is
    ``fit_status`` recomputed from the raw files."""
    data = Path("data/raw/elections")
    cityconfig.use("joburg")
    spec = fold.FOLDS[1]
    for role in ("base", "target"):
        if not cityconfig.resolve_path(data / spec[role][0].replace(
                "{CODE}", cityconfig.active().code)).exists():
            skip(f"no raw {role} file for fold 1")
    import contextlib
    import io
    with tempfile.TemporaryDirectory() as tmp:
        with contextlib.redirect_stdout(io.StringIO()):
            assert fold.main(["--fold", "1", "--city", "joburg",
                              "--out", tmp]) == 0
        path = Path(tmp) / "fold1_parameters.csv"
        with path.open(encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames == HEADER
            rows = list(reader)
    base_votes, _ = fold.load(data / spec["base"][0], spec["base"][1])
    base_city = fold.citywide(base_votes)
    for ballot in ("PR", "Ward"):
        _, target_city, _, universe = fold.fold_target(1, data, ballot, base_city)
        mine = [r for r in rows if r["ballot"] == ballot]
        assert len(mine) == len(universe)
        for r in mine:
            assert r["fit_status"] == fold.fit_status(
                r["party"], base_city, target_city, universe), r
    assert {r["fit_status"] for r in rows} >= {F, BASE}


# --------------------------------------------------------------------------
# 2. the source per city and year
# --------------------------------------------------------------------------

def _tree(tmp: Path) -> tuple[Path, Path]:
    """A city directory with a fold-1 file and a pooled file, and a target
    directory with a recent γ for P and Q."""
    city, target = tmp / "city", tmp / "city" / "2026"
    target.mkdir(parents=True)
    _write_fold(city / "fold1_parameters.csv", FOLD1)
    _write_pooled(fold.pooled_path(city, [1, 2]), [
        ("PR", "A", "0.8500", "1+2", {1: F, 2: F}),
        ("PR", "P", "0.5000", "2", {1: BASE, 2: F}),
        ("PR", "Z", "", "", {1: TGT, 2: UNS}),
        ("Ward", "A", "0.7500", "1+2", {1: F, 2: F}),
        ("Ward", "P", "0.4000", "2", {1: BASE, 2: F}),
        ("Ward", "Z", "", "", {1: TGT, 2: UNS})])
    (target / "gamma_recent.csv").write_text("party,gamma\nP,0.3\nZ,0.2\n")
    return city, target


def test_joburg_2026_reads_the_pool_and_labels_the_contributing_folds():
    assert M.GAMMA_POOL.get("joburg|2026") == (1, 2)
    with tempfile.TemporaryDirectory() as tmp:
        city, target = _tree(Path(tmp))
        with _CityProcessed(city):
            got = M.resolve_gamma(_target("joburg", "2026"), target,
                                  ["A", "P", "Z", "Q"])
    assert got["PR"] == {"A": (0.85, "pooled 1+2"), "P": (0.5, "pooled 2"),
                         "Z": (0.2, "recent"), "Q": (1.0, "default 1.0")}
    assert got["Ward"]["A"] == (0.75, "pooled 1+2")


def test_tshwane_2026_keeps_fold_1_and_a_placeholder_is_not_a_fold():
    assert "tshwane|2026" not in M.GAMMA_POOL
    assert M.gamma_folds_for(_target("tshwane", "2026")) == (M.GAMMA_FOLD["2026"],)
    with tempfile.TemporaryDirectory() as tmp:
        city, target = _tree(Path(tmp))
        with _CityProcessed(city):
            got = M.resolve_gamma(_target("tshwane", "2026"), target,
                                  ["A", "P", "Z", "Q"])
    assert got["PR"] == {"A": (0.8, "fold1"), "P": (0.3, "recent"),
                         "Z": (0.2, "recent"), "Q": (1.0, "default 1.0")}
    for ballot in got:
        for p, (_g, src) in got[ballot].items():
            assert not (src.startswith("fold") and p in ("P", "Z")), (p, src)


def test_a_missing_pooled_file_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        city, target = _tree(Path(tmp))
        fold.pooled_path(city, [1, 2]).unlink()
        with _CityProcessed(city):
            try:
                M.resolve_gamma(_target("joburg", "2026"), target, ["A"])
            except SystemExit as exc:
                assert "--pool 1,2" in str(exc)
            else:
                raise AssertionError("joburg 2026 ran without its pooled γ")


def test_run_model_and_the_interactive_read_one_chain():
    """``run_model`` and ``export_interactive.main`` both call
    ``resolve_gamma``, and neither reads a fold file itself."""
    import export_interactive as EI
    for fn in (M.run_model, EI.main):
        assert "resolve_gamma" in fn.__code__.co_names, fn.__name__
        assert "load_parameters" not in fn.__code__.co_names, fn.__name__
    assert "load_parameters" in M.resolve_gamma.__code__.co_names


# --------------------------------------------------------------------------
# 3. the precedence check over a pool
# --------------------------------------------------------------------------

def test_every_fold_in_a_pool_must_precede_the_target():
    saved = dict(M.GAMMA_POOL)
    try:
        # fold 2 targets 2021, so a 2021 pool of folds 1 and 2 has seen it.
        M.GAMMA_POOL["joburg|2021"] = (1, 2)
        try:
            M.gamma_folds_for(_target("joburg", "2021"))
        except SystemExit as exc:
            assert "fold 2" in str(exc)
        else:
            raise AssertionError("a pool containing the target's own fold passed")
        # The detector goes quiet on a pool that precedes the target.
        M.GAMMA_POOL["joburg|2021"] = (1, 3)
        assert M.gamma_folds_for(_target("joburg", "2021")) == (1, 3)
    finally:
        M.GAMMA_POOL.clear()
        M.GAMMA_POOL.update(saved)
    assert M.gamma_folds_for(_target("joburg", "2026")) == (1, 2)
    try:
        M.gamma_fold_for(_target("joburg", "2026"))
    except SystemExit as exc:
        assert "gamma_folds_for" in str(exc)
    else:
        raise AssertionError("gamma_fold_for named one fold for a pooled target")
    assert M.gamma_fold_for(_target("joburg", "2021")) == M.GAMMA_FOLD["2021"]


# --------------------------------------------------------------------------
# 4. declares
# --------------------------------------------------------------------------

def test_declares_checks_the_column_and_the_pool_against_the_folds():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_fold(root / "fold1_parameters.csv", FOLD1)
        _write_fold(root / "fold2_parameters.csv",
                    [("PR", "A", "1", "1", "0.9", F), ("PR", "P", "1", "1", "0.5", F),
                     ("Ward", "A", "1", "1", "0.8", F), ("Ward", "P", "1", "1", "0.4", F)])
        good = [("PR", "A", "0.85", "1+2", {1: F, 2: F}),
                ("PR", "P", "0.5", "2", {1: BASE, 2: F}),
                ("PR", "Z", "", "", {1: TGT, 2: UNS}),
                ("Ward", "A", "0.75", "1+2", {1: F, 2: F}),
                ("Ward", "P", "0.4", "2", {1: BASE, 2: F}),
                ("Ward", "Z", "", "", {1: TGT, 2: UNS})]
        pooled = fold.pooled_path(root, [1, 2])
        _write_pooled(pooled, good)

        def states():
            return {Path(r.path).name: r.states["fit_status"]
                    for r in declares._fit_rows(root)}
        assert states() == {"fold1_parameters.csv": declares.DECLARED,
                            "fold2_parameters.csv": declares.DECLARED,
                            pooled.name: declares.DECLARED}
        # a pooled status that disagrees with fold 1's file
        bad = [good[0], ("PR", "P", "0.5", "1+2", {1: F, 2: F})] + good[2:]
        _write_pooled(pooled, bad)
        assert states()[pooled.name] == declares.LYING
        _write_pooled(pooled, good)
        assert states()[pooled.name] == declares.DECLARED
        # a fold file without the column
        _write_fold(root / "fold1_parameters.csv", FOLD1, status=False)
        st = states()
        assert st["fold1_parameters.csv"] == declares.UNDECLARED
        assert st[pooled.name] == declares.UNDECLARED
    assert "fit" in declares.KINDS and "fit" in declares.REPORT_ORDER


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
