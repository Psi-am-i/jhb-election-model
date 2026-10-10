"""Two token sources in src/stats.py, on constructed inputs:
``history:<city>:<year>:<path>`` (the home page's ward counts, from
history.json) and ``derived:coalition_majority.<A>+<B>+…`` (the forecast
share image's coalitions, over every party's seats). Each is shown to read the
right record, to return nothing where there is nothing, and to refuse an
ambiguous or malformed source.
"""
from __future__ import annotations

import csv
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import stats  # noqa: E402


def _hist(*records):
    return {"history": {"records": list(records)}}


def test_a_history_source_reads_its_own_city_year_only():
    ctx = _hist({"slug": "joburg", "year": "2011", "wards": {"called": 126, "n_wards": 130}},
                {"slug": "joburg", "year": "2016", "wards": {"called": 134, "n_wards": 135}},
                {"slug": "tshwane", "year": "2011", "wards": {"called": 90, "n_wards": 105}})
    assert stats.resolve("history:joburg:2011:wards.called", ctx) == 126
    assert stats.resolve("history:joburg:2016:wards.n_wards", ctx) == 135
    assert stats.resolve("history:tshwane:2011:wards.called", ctx) == 90
    # nothing where there is nothing: no record, no path, no file
    assert stats.resolve("history:joburg:2021:wards.called", ctx) is None
    assert stats.resolve("history:joburg:2011:wards.missing", ctx) is None
    assert stats.resolve("history:joburg:2011:wards.called", {}) is None


def test_a_history_source_refuses_two_records_and_a_malformed_name():
    two = _hist({"slug": "joburg", "year": "2011", "wards": {"called": 1}},
                {"slug": "joburg", "year": "2011", "wards": {"called": 2}})
    for bad, ctx in (("history:joburg:2011:wards.called", two), ("history:joburg:2011", {}),
                     ("history::2011:wards.called", {})):
        try:
            stats.resolve(bad, ctx)
        except SystemExit:
            continue
        raise AssertionError(f"{bad} was resolved")


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


def test_a_coalition_majority_counts_its_small_partner():
    """B + C reaches 6 in draws 0 and 2 only because C, a party seat_draws.csv
    does not carry, adds its seats: over every party's seats it is 2 of 4."""
    with tempfile.TemporaryDirectory() as t:
        p = _processed(Path(t), {0: {"A": 5, "B": 4, "C": 2}, 1: {"A": 7, "B": 3, "C": 1},
                                 2: {"A": 4, "B": 5, "C": 2}, 3: {"A": 6, "B": 5, "C": 0}}, 6)
        ctx = stats.load_context(p)
        assert stats.resolve("derived:coalition_majority.B+C", ctx) == 0.5
        assert stats.resolve("derived:coalition_majority.A", ctx) == 0.5
        assert stats.resolve("derived:coalition_majority.A+B", ctx) == 1.0
        assert stats.resolve("derived:coalition_majority.D", ctx) == 0.0   # no seats anywhere
        for bad in ("derived:coalition_majority.B+B", "derived:coalition_majority.", "derived:coalition_majority.A+"):
            try:
                stats.resolve(bad, ctx)
            except SystemExit:
                continue
            raise AssertionError(f"{bad} was resolved")
        assert stats.resolve("derived:coalition_majority.A", {}) is None


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
