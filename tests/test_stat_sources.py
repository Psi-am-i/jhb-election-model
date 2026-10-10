"""Two token sources in src/stats.py, on constructed inputs:
``history:<city>:<year>:<path>`` (the home page's ward counts, from
history.json) and ``stats.coalition_majority`` (the forecast share image's
coalitions, over every party's seats). Each is shown to read the right record,
to return nothing where there is nothing, and to refuse an ambiguous or
malformed request.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import stats  # noqa: E402


KEY = {"pools_sha": "c0ffee", "target": "2011"}


def _hist(root: Path, *records, keys=None):
    """A ctx with history.json's records and manifest, and a constructed
    repository whose current Johannesburg spec declares ``KEY`` (the legacy
    processed root, data/processed/, as cityconfig places it)."""
    spec = root / "data" / "processed"
    spec.mkdir(parents=True, exist_ok=True)
    for y in ("2011", "2016"):
        (spec / f"pools_{y}.json").write_text(json.dumps({"artefact_key": {**KEY, "target": y}}))
    if keys is None:
        keys = {"joburg": {f"pools_{y}.json": {**KEY, "target": y} for y in ("2011", "2016")}}
    return {"history": {"records": list(records), "manifest": {
        "pool_artefact_keys": keys, "generated": "2026-09-29T03:01:22Z", "draws": 1000,
        "git_commit": "a2bc44c9d7d6"}}, "spec_root": root}


J11 = {"slug": "joburg", "year": "2011", "wards": {"called": 126, "n_wards": 130}}
J16 = {"slug": "joburg", "year": "2016", "wards": {"called": 134, "n_wards": 135}}


def test_a_history_source_reads_its_own_city_year_only():
    with tempfile.TemporaryDirectory() as t:
        ctx = _hist(Path(t), J11, J16, {"slug": "joburg", "year": "2021", "wards": {"called": 1}})
        assert stats.resolve("history:joburg:2011:wards.called", ctx) == 126
        assert stats.resolve("history:joburg:2016:wards.n_wards", ctx) == 135
        # nothing where there is nothing: no record, no path, no file
        assert stats.resolve("history:joburg:2006:wards.called", ctx) is None
        assert stats.resolve("history:joburg:2011:wards.missing", ctx) is None
        assert stats.resolve("history:joburg:2011:wards.called", {}) is None


def test_a_history_source_refuses_a_record_scored_on_other_specs():
    """The manifest's artefact key for the spec must equal the current spec's.
    Constructed: a moved key, a missing key and a missing spec are each
    refused; restored, the figure is answered again."""
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        moved = {"joburg": {"pools_2011.json": {**KEY, "pools_sha": "stale"}}}
        for keys in (moved, {"joburg": {}}):
            ctx = _hist(root, J11, keys=keys)
            try:
                stats.resolve("history:joburg:2011:wards.called", ctx)
            except SystemExit as e:
                assert "compare_history" in str(e)
            else:
                raise AssertionError(f"a record scored on {keys} was quoted")
        ctx = _hist(root, J11)
        (root / "data/processed/pools_2011.json").unlink()
        assert stats.history_key_fault(ctx["history"], "joburg", "2011", root)
        ctx = _hist(root, J11)                                   # restored
        assert stats.resolve("history:joburg:2011:wards.called", ctx) == 126


def test_a_history_source_refuses_two_records_and_a_malformed_name():
    with tempfile.TemporaryDirectory() as t:
        two = _hist(Path(t), J11, {**J11, "wards": {"called": 2}})
        for bad, ctx in (("history:joburg:2011:wards.called", two), ("history:joburg:2011", {}),
                         ("history::2011:wards.called", {})):
            try:
                stats.resolve(bad, ctx)
            except SystemExit:
                continue
            raise AssertionError(f"{bad} was resolved")


def test_a_history_figure_names_the_backtest_run_not_the_forecast():
    """The tooltip of a history: figure says which run it came from, in words:
    no source grammar, and not "the current model run"."""
    with tempfile.TemporaryDirectory() as t:
        ctx = _hist(Path(t), J11)
        reg = {"w": {"mode": "free", "source": "history:joburg:2011:wards.called", "format": "int"}}
        out, _d, unresolved = stats.render("{{w}}", reg, ctx)
        assert not unresolved
        tip = re.search(r'data-prov="([^"]*)"', out).group(1)
        assert "past elections" in tip and "1,000 simulations" in tip and "29 September 2026" in tip
        assert "a2bc44c" in tip and "history:" not in tip and "current model run" not in tip


def test_the_home_page_ward_tokens_name_history_sources_for_joburg():
    """The six registered tokens: each a free `history:joburg:<year>:wards.…`
    source, one called and one count per election."""
    reg = tomllib.loads((ROOT / "content/joburg/stats.toml").read_text(encoding="utf-8"))
    got = {k: v["source"] for k, v in reg.items() if k.startswith("hist_jhb_wards")}
    assert got == {f"hist_jhb_wards{'_called' if c else ''}_{y}":
                   f"history:joburg:{y}:wards.{'called' if c else 'n_wards'}"
                   for y in ("2011", "2016", "2021") for c in (True, False)}
    assert all(reg[k]["mode"] == "free" for k in got)


def _processed(tmp: Path, detail: dict[int, dict[str, int]], threshold: int) -> Path:
    """A processed directory with seat_draws.csv (the two largest parties) and
    seat_detail_draws.csv (every party), as montecarlo writes them."""
    big = ("A", "B")
    with (tmp / "seat_draws.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "threshold", "council_size", *big])
        for d, seats in detail.items():
            w.writerow([d, threshold, sum(seats.values()), *(seats.get(p, 0) for p in big)])
    with (tmp / "seat_detail_draws.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "party", "ward_seats", "list_seats", "seats", "excessive"])
        for d, seats in detail.items():
            for p, n in seats.items():
                w.writerow([d, p, 0, n, n, 0])
    return tmp


def test_a_coalition_majority_counts_its_small_partner_and_refuses_an_unknown_party():
    """B + C reaches 6 in draws 0 and 2 only because C, a party seat_draws.csv
    does not carry, adds its seats: over every party's seats it is 2 of 4.
    A party the run's seat file does not name is refused, as are an empty or
    repeated member list; the same call with known parties is answered."""
    with tempfile.TemporaryDirectory() as t:
        p = _processed(Path(t), {0: {"A": 5, "B": 4, "C": 2}, 1: {"A": 7, "B": 3, "C": 1},
                                 2: {"A": 4, "B": 5, "C": 2}, 3: {"A": 6, "B": 5}}, 6)
        ctx = stats.load_context(p)
        assert stats.coalition_majority(["B", "C"], ctx) == 0.5
        assert stats.coalition_majority(["A"], ctx) == 0.5
        assert stats.coalition_majority(["A", "B"], ctx) == 1.0
        for bad in (["D"], ["B", "D"], ["B", "B"], [], ["A", ""]):
            try:
                stats.coalition_majority(bad, ctx)
            except SystemExit:
                continue
            raise AssertionError(f"{bad} was answered")
        assert stats.coalition_majority(["B", "C"], ctx) == 0.5     # quiet again
        assert stats.coalition_majority(["A"], {}) is None


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
