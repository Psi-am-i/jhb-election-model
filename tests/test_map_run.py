"""The ward maps are drawn from the run the headline beside them quotes.

Site sweep, 2026-10-23: the map, its tooltips, its legend counts and its
council bar on the live home and forecast pages had been drawn from the
29 September run and never redrawn, while the headline beside them quoted the
21 October one (ward 1 "contested, ANC 84%" on a run that gives 91%). Nothing
compared the two. Owner, 2026-10-23: "agree on a map test".

Each map snippet now carries ``data-run``, the content hash of the run it was
drawn from (``render_map.drawn_from``, through ``publication.
forecast_content_sha``), and ``build_site`` refuses to build when either map
on the forecast sheet names another run than ``data/processed``
(``build_site.maps_are_current``).

What this file proves, in the order CLAUDE.md §4 asks:

0. the right population: every map region the sheet carries (both maps), and
   both are required;
1. it looked: each region yields its stamp;
2. it can see: a constructed foreign stamp, and a missing one, are caught, and
   the detector is quiet again on the constructed current page;
3. constructed inputs: the unit tests build their own run and page.

The last test is the live one: the committed sheet against the run in
``data/processed``. It is the check the owner asked for, and it fails whenever
the map is not redrawn after a run.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import build_site  # noqa: E402
import hex_cartogram  # noqa: E402
import publication  # noqa: E402
import render_map as RM  # noqa: E402
from _support import skip  # noqa: E402


def _run(content: dict) -> Path:
    """A constructed run: a processed directory holding only its summary."""
    proc = Path(tempfile.mkdtemp()) / "processed"
    proc.mkdir()
    (proc / "forecast_summary.json").write_text(json.dumps(content), encoding="utf-8")
    return proc


def _page(geo_run: str | None, hex_run: str | None) -> str:
    def region(start, end, run, mapname):
        attr = f' {RM.RUN_ATTR}="{run}"' if run is not None else ""
        return (f'{start}<details data-map="{mapname}"{attr}>'
                f'<svg><path data-tip="Ward 1 · ANC"></path></svg></details>{end}')
    return ("<html><body>"
            + region(RM.MARK_START, RM.MARK_END, geo_run, "geo")
            + "<p>The headline.</p>"
            + region(hex_cartogram.MARK_START, hex_cartogram.MARK_END, hex_run, "cartogram")
            + "</body></html>")


def test_the_stamp_is_the_runs_content_hash_and_ignores_its_volatile_stamps():
    a = _run({"parties": {"ANC": 1}, "_generated": "2026-10-21T10:03:00Z"})
    b = _run({"parties": {"ANC": 1}, "_generated": "2026-10-23T09:00:00Z"})
    c = _run({"parties": {"ANC": 2}, "_generated": "2026-10-21T10:03:00Z"})
    assert RM.drawn_from(a) == RM.drawn_from(b) == publication.forecast_content_sha(a)
    assert RM.drawn_from(a) != RM.drawn_from(c)
    # the one definition: run_identity records the same hash
    assert publication.run_identity(a)["forecast_content_sha256"] == RM.drawn_from(a)


def test_a_page_whose_maps_name_this_run_has_no_problem():
    proc = _run({"parties": {"ANC": 1}})
    run = RM.drawn_from(proc)
    page = _page(run, run)
    # it looked: both regions, each with its stamp
    found = RM._RUN.findall(page)
    assert [name for name, _ in found] == ["MAP", "HEXMAP"], found
    assert RM.stale_maps(page, proc) == []


def test_a_map_drawn_from_another_run_is_caught_and_the_detector_goes_quiet_when_redrawn():
    proc = _run({"parties": {"ANC": 1}})
    run = RM.drawn_from(proc)
    old = "0" * 64
    for geo, hexr, which in ((old, run, "MAP"), (run, old, "HEXMAP")):
        problems = RM.stale_maps(_page(geo, hexr), proc)
        assert len(problems) == 1 and f"the {which} map was drawn from run" in problems[0], problems
    assert RM.stale_maps(_page(run, run), proc) == []


def test_a_map_naming_no_run_is_caught():
    proc = _run({"parties": {"ANC": 1}})
    run = RM.drawn_from(proc)
    problems = RM.stale_maps(_page(None, run), proc)
    assert len(problems) == 1 and "names no run" in problems[0], problems


def test_the_build_requires_both_maps_on_the_sheet():
    proc = _run({"parties": {"ANC": 1}})
    run = RM.drawn_from(proc)
    root = Path(tempfile.mkdtemp())
    sheet = root / "sheet.html"
    saved = build_site.REPO_ROOT
    build_site.REPO_ROOT = root
    try:
        sheet.write_text(_page(run, run), encoding="utf-8")
        assert build_site.maps_are_current(proc, pages=("sheet.html",)) == []
        # take the cartogram away: the build must say so, not pass an absent map
        sheet.write_text(_page(run, run).split(hex_cartogram.MARK_START)[0], encoding="utf-8")
        problems = build_site.maps_are_current(proc, pages=("sheet.html",))
        assert any(hex_cartogram.MARK_START in p for p in problems), problems
        # and a stale stamp on a full page
        sheet.write_text(_page("0" * 64, run), encoding="utf-8")
        assert build_site.maps_are_current(proc, pages=("sheet.html",)), "a stale map passed"
    finally:
        build_site.REPO_ROOT = saved


def test_the_published_sheets_maps_are_drawn_from_the_current_run():
    """THE LIVE CHECK. The committed forecast sheet (the home page's map is cut
    from it at build time) against the run in ``data/processed``, which is the
    run the headline figures are read from. Red means: re-run
    ``src/render_map.py`` and ``src/hex_cartogram.py --into`` for each page."""
    proc = ROOT / "data" / "processed"
    if not (proc / "forecast_summary.json").is_file():
        skip("no run in data/processed")
    problems = build_site.maps_are_current(proc)
    assert problems == [], problems
