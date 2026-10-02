"""/make/ ("make your own forecast") goes through the number gate like every page.

The same rules as /play/ (tests/test_play_page.py): the untouched page is
ledgered tokens (the published seat panel); a figure computed from the
reader's edits appears only inside a LIVE region, which holds no build-time
digit, and only a module in ``stats.LIVE_WRITERS`` may write one.

These tests build the real site into a temporary directory (never ``site/``)
and hold the BUILT page to that, then show each guard fires on a constructed
violation and goes quiet when it is reverted. They also hold the start state
to its stated definition (src/build_make.py): the published ward calls and the
published list-ballot medians, seated by the statute.
"""
from __future__ import annotations

import contextlib
import csv
import io
import json
import math
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import run_module, skip  # noqa: E402

import build_make  # noqa: E402
import build_site  # noqa: E402
import deploy_check  # noqa: E402
import stats as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WRITER = "make/js/make.js"
SHARE = "make/js/make-share.js"
CARD = "make/js/forecast-card.js"
MAKE_WRITERS = (WRITER, SHARE, CARD)
STAMP = re.compile(r"<!-- built-pages: (.*?) blocking=(\d+) -->")

_BUILT: dict = {}


def _build(out: Path, *extra: str) -> tuple[int | str | None, str]:
    buf = io.StringIO()
    code: int | str | None = 0
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = build_site.main(["--out", str(out), *extra])
    except SystemExit as exc:
        code = exc.code
    return code, buf.getvalue()


def _built() -> Path:
    if not (ROOT / "data" / "processed" / "forecast_summary.json").is_file():
        skip("data/processed/forecast_summary.json is absent: the site cannot be built here")
    if not (ROOT / "site" / "draws" / "base.bin").is_file():
        skip("site/draws/ is absent: /make/ starts from the published draws")
    if "site" not in _BUILT:
        tmp = Path(tempfile.mkdtemp(prefix="make-page-"))
        site = tmp / "site"
        site.mkdir()
        code, log = _build(site)
        assert code in (0, None), log[-3000:]
        _BUILT["site"] = site
    return _BUILT["site"]


def _stamp(site: Path) -> tuple[dict, int]:
    m = STAMP.search((site.parent / "NUMBERS-REVIEW.md").read_text(encoding="utf-8"))
    assert m, "the review carries no built-pages stamp"
    return dict(p.split("=", 1) for p in m.group(1).split()), int(m.group(2))


def _writes(site: Path, writers=None) -> list[str]:
    page = site / build_make.MAKE_PAGE
    return S.script_writes(page.read_text(encoding="utf-8"), page=page, root=site,
                           writers=S.LIVE_WRITERS if writers is None else writers)


def _data(site: Path) -> dict:
    return json.loads((site / build_make.MAKE_DIR / build_make.DATA).read_text(encoding="utf-8"))


# -- the gate ------------------------------------------------------------------

def test_the_built_make_page_is_stamped_and_blocks_nothing():
    site = _built()
    pages, blocking = _stamp(site)
    assert build_make.MAKE_PAGE in pages, sorted(pages)
    assert blocking == 0
    review = (site.parent / "NUMBERS-REVIEW.md").read_text(encoding="utf-8")
    section = re.search(rf"^## {re.escape(build_make.MAKE_PAGE)} — (.*?)$(.*?)(?=^## |\Z)", review, re.S | re.M)
    assert section, "the review has no section for the make page"
    assert "| BLOCKS |" not in section.group(2)
    hits = S.scan_numbers((site / build_make.MAKE_PAGE).read_text(encoding="utf-8"))
    assert [h for h in hits if h["region"].startswith("live:") and S.is_blocking(h)] == []
    assert deploy_check.check("joburg", site, preview=False,
                              review=site.parent / "NUMBERS-REVIEW.md") == []


def test_first_paint_is_tokens_and_the_live_regions_are_the_listed_ones():
    site = _built()
    html = (site / build_make.MAKE_PAGE).read_text(encoding="utf-8")
    # the published seat panel, as rendered token spans in a shadow root
    hosts = html.split('<template shadowrootmode="open">')[1:]
    assert len(hosts) == 1 and hosts[0].count('class="mstat"') >= 5, hosts[:1]
    # no prototype banner and no placeholder data
    assert 'class="proto"' not in html and "placeholder" not in html.lower()
    # every LIVE region on the page is one a make writer is listed for, and
    # every listed region is on the page (both directions)
    on_page = {name for _, _, name in S._live_scan(html)[0]}
    listed = set().union(*(S.LIVE_WRITERS[w] for w in MAKE_WRITERS))
    assert on_page == listed, (on_page ^ listed)
    assert sum(len(S.LIVE_WRITERS[w]) for w in MAKE_WRITERS) == len(listed)
    assert {w for w in S.LIVE_WRITERS if w.startswith("make/")} == set(MAKE_WRITERS)
    for w in MAKE_WRITERS:
        assert (site / w).is_file(), w
    for name in on_page:
        assert re.search(rf'data-live="{name}"[^>]*>(?:(?!data-live=).)*?[Cc]omputed in your browser',
                         html, re.S), name
    # the Worker's seat module was pointed at the copy beside it
    engine = (site / "make/js/seat-engine.js").read_text(encoding="utf-8")
    assert build_make.SEATS_LINE[1] in engine and build_make.SEATS_LINE[0] not in engine
    for f in build_make.WORKER_API_JS:
        assert (site / "make/js" / f).read_bytes() == (ROOT / "worker-api/src" / f).read_bytes()
    # its own card: no digit, generic image
    og = dict(re.findall(r'<meta property="og:(title|description|url)" content="([^"]*)"', html))
    assert og["title"] == build_make.OG_TITLE and og["url"].endswith("/make/"), og
    from html import unescape
    assert not re.search(r"\d", unescape(og["title"] + og["description"])), og
    # linked from /play/ and from the home page
    assert 'href="../make/"' in (site / "play/index.html").read_text(encoding="utf-8")
    assert 'href="make/"' in (site / "index.html").read_text(encoding="utf-8")


def test_the_page_scripts_pass_and_the_check_reaches_the_writers():
    site = _built()
    assert _writes(site) == []
    found = _writes(site, writers={k: v for k, v in S.LIVE_WRITERS.items() if k != WRITER})
    assert any(w.startswith(f"{WRITER}: a data source") for w in found), found
    # its imports are read as non-writers
    for f in ("make/js/make-state.js", "make/js/builder-state.js", "make/js/map.js", "make/js/card-text.js"):
        mod = site / f
        body = mod.read_text(encoding="utf-8")
        try:
            mod.write_text(body + "\nexport const rows = [1, 2];\n", encoding="utf-8")
            assert any(w.startswith(f"{f}: a data block") for w in _writes(site)), f
        finally:
            mod.write_text(body, encoding="utf-8")
    assert _writes(site) == []


def test_a_figure_outside_a_live_region_is_refused_and_the_refusal_reverts():
    site = _built()
    cases = (
        (WRITER, "document.querySelector('.pubseats').textContent = '66';\n", "a lookup that is not a LIVE selector"),
        (WRITER, "document.querySelector('[data-live=\"share\"] .shurl').value = '1';\n", "a LIVE region it is not listed for"),
        (WRITER, "one.bars.innerHTML = '<b>1</b>';\n", "HTML injection"),
        (WRITER, "one.bars.closest('.builder').append('1');\n", "traversal out of the region"),
        (SHARE, "document.querySelector('[data-live=\"council\"] .bars').textContent = '1';\n", "a LIVE region it is not listed for"),
        (CARD, "document.querySelector('[data-live=\"share\"] img').alt = '1';\n", "a LIVE region it is not listed for"),
        (CARD, "export const D = [77, 70];\n", "a data block"),
        (CARD, 'fetch("../forecast.json");\n', "a data source"),
    )
    for f, line, what in cases:
        mod = site / f
        body = mod.read_text(encoding="utf-8")
        try:
            mod.write_text(body + line, encoding="utf-8")
            found = _writes(site)
            assert any(w.startswith(f"{f} (LIVE writer): {what}") for w in found), (f, line, found)
        finally:
            mod.write_text(body, encoding="utf-8")
        assert _writes(site) == [], (f, line)


def test_the_build_blocks_an_unlisted_writer_and_a_typed_live_digit():
    _built()
    real_writers, real_assemble = dict(S.LIVE_WRITERS), build_make.assemble
    with tempfile.TemporaryDirectory() as t:
        del S.LIVE_WRITERS[WRITER]
        try:
            (Path(t) / "a").mkdir()
            code, log = _build(Path(t) / "a")
        finally:
            S.LIVE_WRITERS.clear()
            S.LIVE_WRITERS.update(real_writers)
        assert code not in (0, None) and "PAGE SCRIPT WRITES FIGURES" in log, log[-2000:]
        assert f"make/index.html: {WRITER}: a data source" in log

        def typed(**kw):
            html = real_assemble(**kw)
            marker = '<p class="ess restate">'
            assert html.count(marker) == 1
            return html.replace(marker, marker + "The DA wins 77 seats. ")
        build_make.assemble = typed
        try:
            (Path(t) / "b").mkdir()
            code, log = _build(Path(t) / "b")
        finally:
            build_make.assemble = real_assemble
        assert code in (0, None), log[-2000:]
        pages, blocking = _stamp(Path(t) / "b")
        assert blocking >= 1 and build_make.MAKE_PAGE in pages
        review = (Path(t) / "NUMBERS-REVIEW.md").read_text(encoding="utf-8")
        assert re.search(r"\| BLOCKS \| num \| live:council \| `77` \|", review), review[-3000:]

        (Path(t) / "c").mkdir()
        code, log = _build(Path(t) / "c")
        assert code in (0, None), log[-2000:]
        assert _stamp(Path(t) / "c")[1] == 0


# -- the start state -------------------------------------------------------------

def test_the_start_is_the_published_ward_calls_and_the_panel_middles():
    site = _built()
    d = _data(site)
    schema, start = d["schema"], d["start"]
    wards = schema["x-ward-ids"]
    # the ward calls are the forecast map's winners wherever those have no tie
    with (ROOT / "data/processed/ward_winner_probs.csv").open(encoding="utf-8", newline="") as h:
        published = {r["ward"]: r for r in csv.DictReader(h)}
    agree = 0
    for w, call in zip(wards, start["ward_calls"]):
        probs = sorted((float(x.split(":")[1]) for x in published[w]["dist"].split("|")), reverse=True)
        if len(probs) > 1 and probs[0] == probs[1]:
            continue
        assert call == published[w]["winner"], w
        agree += 1
    assert agree >= len(wards) - 2, agree
    # no placeholder
    assert schema["x-placeholder"] is False and not d["model_ref"].startswith("placeholder")
    man = json.loads((ROOT / "site/draws/manifest.json").read_text(encoding="utf-8"))
    assert d["model_ref"] == man["published_run"]["model_run_id"]
    assert schema["x-seat-context"]["parties"] == man["parties"]
    assert isinstance(schema["x-total-votes"], int) and schema["x-total-votes"] > 0
    assert math.isclose(math.fsum(start["combined_share"].values()), 100.0, abs_tol=1e-9)

    # the middles the start aims at are the forecast page's own: the seat
    # panel's rows from seat_draws.csv (render_sheet's source), Others by
    # scenarios.others_per_draw, both through scenarios.seat_quantiles
    import scenarios
    seat_csv = ROOT / "data/processed/seat_draws.csv"
    with seat_csv.open(encoding="utf-8", newline="") as h:
        rows = list(csv.DictReader(h))
    named = [p for p in scenarios.NAMED_PARTIES if p in rows[0]]
    page = {p: scenarios.seat_quantiles([float(r[p]) for r in rows])[0] for p in named}
    page["OTHERS"] = scenarios.seat_quantiles(scenarios.others_per_draw(seat_csv.parent, named))[0]
    assert {g: v for g, v in start["published_middle"].items() if g in page} == page

    # the untouched council, seated by the statute from the stored shares
    import score_forecasts
    seated = score_forecasts.seat_forecast({"ward_calls": start["ward_calls"],
                                           "combined_share": start["combined_share"]}, schema)
    assert seated["ok"], seated["errors"]
    got = {p: v["total"] for p, v in seated["seats"].items()}
    assert got == start["seats"]
    assert sum(got.values()) == seated["council"]
    # each panel row opens at its middle, one seat off where the middles do
    # not fill the council, or at its ward count where the wards it is called
    # for exceed its middle
    held = {}
    for c in start["ward_calls"]:
        held[c] = held.get(c, 0) + 1
    others = sum(n for p, n in got.items() if p not in named)
    off = {}
    for g, mid in page.items():
        n = others if g == "OTHERS" else got.get(g, 0)
        wards_held = (sum(v for p, v in held.items() if p not in named) if g == "OTHERS"
                      else held.get(g, 0))
        if wards_held > mid:
            assert n == wards_held, (g, n, wards_held)
        else:
            assert abs(n - mid) <= 1, (g, n, mid)
        off[g] = n - mid
    print(f"  untouched /make/ against the published middles: {off}")


def test_the_data_file_is_the_one_the_build_writes():
    site = _built()
    assert _data(site) == json.loads(json.dumps(build_make.forecast_data(), sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
