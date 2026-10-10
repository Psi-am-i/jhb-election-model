"""/your-forecast/ goes through the number gate like every page, and its two
sections are one forecast.

The page (owner, 2026-10-03) replaced /play/ and /make/: section 1, "Adjust
the model", is the published draws re-weighted by the reader's settings;
section 2, "Break the model", is the reader's own forecast, seated by the law,
opened from section 1's settings. SPEC-v2 decision 1 holds for both: the
untouched page is ledgered tokens; a figure computed from a reader's settings
or edits appears only inside a LIVE region (``data-live``), which holds no
build-time digit, and only a module in ``stats.LIVE_WRITERS`` may write one,
into the regions it is listed for.

These tests build the real site into a temporary directory (never ``site/``)
and hold the BUILT page to that, then show each guard fires on a constructed
violation and goes quiet when it is reverted (CLAUDE.md §4):

* the page is in the review stamp, blocks nothing, and ``deploy_check``
  passes on the build; the retired /play/ and /make/ are not in it;
* its first paint is token spans (the published forecast, ledgered) in build
  twins, and its LIVE regions are exactly the ones its writers are listed
  for, both directions, each with one writer;
* a figure written outside a LIVE region, by a listed writer or by a module
  that is not listed, is refused, on the built files and by the build itself;
* section 1's engine (``pyboot/page.py``) at uniform weights shows the
  forecast page's rows, and its by-election line is the build's;
* section 2's start is our prediction, rule A on the published draws
  (``src/prediction.py``, through ``build_make``), and the hand-off from
  section 1 is the same rule on the reader's weights: at the published
  setting it IS the published start, and under any setting its ward calls are
  the ward winners section 1 shows;
* "Analyse my forecast" is ``reweight``'s arithmetic on the published draws.
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
import build_play  # noqa: E402
import build_site  # noqa: E402
import build_your_forecast as YF  # noqa: E402
import deploy_check  # noqa: E402
import stats as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = YF.YF_DIR
ADJUST = f"{D}/js/model.js"
BREAK = f"{D}/js/make.js"
#: Every writer the page ships: each section's page module and share sheet
#: content, the one share sheet, section 1's share-image words, the card
#: module of both sections, and the arrival view a shared link opens.
SHEET = f"{D}/js/share-sheet.js"
WRITERS = (ADJUST, f"{D}/js/play-share.js", f"{D}/js/play-card.js", SHEET,
           BREAK, f"{D}/js/make-share.js", f"{D}/js/share-card.js", f"{D}/js/arrival.js",
           f"{D}/js/entries.js")
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
    """One real build into a temporary site, shared by the tests below."""
    if not (ROOT / "data" / "processed" / "forecast_summary.json").is_file():
        skip("data/processed/forecast_summary.json is absent: the site cannot be built here")
    if not (ROOT / "site" / "draws" / "base.bin").is_file():
        skip("site/draws/ is absent: the page runs on the published draws")
    if "site" not in _BUILT:
        tmp = Path(tempfile.mkdtemp(prefix="your-forecast-"))
        site = tmp / "site"
        site.mkdir()
        # a stale copy of each retired page, which the build must remove
        for d in YF.RETIRED:
            (site / d).mkdir()
            (site / d / "index.html").write_text("<p>old</p>", encoding="utf-8")
        code, log = _build(site)
        assert code in (0, None), log[-3000:]
        _BUILT["site"] = site
    return _BUILT["site"]


def _html(site: Path) -> str:
    return (site / YF.YF_PAGE).read_text(encoding="utf-8")


def _stamp(site: Path) -> tuple[dict, int]:
    m = STAMP.search((site.parent / "NUMBERS-REVIEW.md").read_text(encoding="utf-8"))
    assert m, "the review carries no built-pages stamp"
    return dict(p.split("=", 1) for p in m.group(1).split()), int(m.group(2))


def _writes(site: Path, writers=None) -> list[str]:
    page = site / YF.YF_PAGE
    return S.script_writes(page.read_text(encoding="utf-8"), page=page, root=site,
                           writers=S.LIVE_WRITERS if writers is None else writers)


def _data(site: Path) -> dict:
    return json.loads((site / D / build_make.DATA).read_text(encoding="utf-8"))


# -- the gate ------------------------------------------------------------------

def test_the_built_page_is_stamped_blocks_nothing_and_replaces_the_old_two():
    site = _built()
    pages, blocking = _stamp(site)
    assert YF.YF_PAGE in pages, sorted(pages)
    assert blocking == 0
    # the page's own section of the review: it was looked at (the published
    # map's tooltips are scanned as a generated region, so its scan is far
    # from empty) and none of its rows blocks
    review = (site.parent / "NUMBERS-REVIEW.md").read_text(encoding="utf-8")
    section = re.search(rf"^## {re.escape(YF.YF_PAGE)} — (.*?)$(.*?)(?=^## |\Z)", review, re.S | re.M)
    assert section, "the review has no section for the page"
    assert sum(int(n) for n in re.findall(r"(\d+) \w+", section.group(1))) > 100, section.group(1)
    assert "| BLOCKS |" not in section.group(2)
    assert "| generated:MAP:attr |" in section.group(2)
    hits = S.scan_numbers(_html(site))
    assert [h for h in hits if h["region"].startswith("live:") and S.is_blocking(h)] == []
    assert deploy_check.check("joburg", site, preview=False,
                              review=site.parent / "NUMBERS-REVIEW.md") == []
    # the retired pages are gone from the build, stale copies included, and
    # nothing in the review is stamped for them
    for d in YF.RETIRED:
        assert not (site / d).exists(), d
        assert not any(p.startswith(d + "/") for p in pages), d


def test_first_paint_is_tokens_and_the_live_regions_are_the_listed_ones():
    site = _built()
    html = _html(site)
    # nothing of /forecast is embedded (DESIGN §4)
    assert "shadowrootmode" not in html
    for other in ('id="tiles"', 'id="coalitions"', 'id="claims"'):
        assert other not in html, other
    assert "__PLAY:" not in html and "__MAKE:" not in html
    assert 'class="proto"' not in html and "placeholder" not in html.lower()
    # section 1's twins: each twin's figures are rendered token spans
    sheet = build_play.seat_rows((ROOT / "forecast-sheet.html").read_text(encoding="utf-8"))
    for part in ("pl-banner pl-pub", "pl-oneline pl-pub yf-slot", "pl-seats pl-pub", "pl-pub pl-turntwin"):
        lo = html.index(f'class="{part}"')
        assert html[lo:lo + 6000].count('class="mstat') >= 2, part
    seats = html[html.index('class="pl-seats pl-pub"'):html.index('data-live="seats"')]
    assert seats.count('<div class="st-row" data-code=') == len(sheet)
    assert html.count("<!-- __MAP_START__ -->") == 1 and html.count("<!-- __MAP_END__ -->") == 1
    # one seat table on the page at build time, the published forecast's:
    # section 2 shows none of its own (the reader scrolls past section 1's)
    assert html.count('<div class="st" ') == 1
    # every LIVE region on the page is one a writer is listed for, every
    # listed region is on the page, and each region has one writer that
    # reaches it by selector. The one share sheet is listed for both share
    # regions but selects nothing: it writes only to the elements the
    # region's own module handed it (test_the_page_scripts_pass… holds it
    # to no lookup), so it is the one writer counted apart. It cannot be
    # listed for no region: that contract refuses a data source, and the
    # sheet fetches the seal and the card's fonts and logos.
    on_page = [name for _, _, name in S._live_scan(html)[0]]
    listed = set().union(*(S.LIVE_WRITERS[w] for w in WRITERS))
    assert set(on_page) == listed, (set(on_page) ^ listed)
    assert len(on_page) == len(set(on_page)), sorted(on_page)
    assert sum(len(S.LIVE_WRITERS[w]) for w in WRITERS if w != SHEET) == len(listed)
    assert S.LIVE_WRITERS[SHEET] == {"share", "b-share"} <= listed
    assert {w for w in S.LIVE_WRITERS if w.startswith(D + "/")} == set(WRITERS)
    assert not [w for w in S.LIVE_WRITERS if w.split("/")[0] in YF.RETIRED]
    for w in WRITERS:
        assert (site / w).is_file(), w
    # said once, in the notes
    text = re.sub(r"<[^>]+>", " ", html)
    assert len(re.findall(r"worked out in your browser", text)) == 1
    assert not re.search(r"[Cc]omputed in your browser", text)
    # each Worker loader was pointed at the served layout, and at nothing else
    worker = (site / D / "js/model-worker.js").read_text(encoding="utf-8")
    assert build_play.DRAWS_LINE[1] in worker and build_play.DRAWS_LINE[0] not in worker
    engine = (site / D / "js/seat-engine.js").read_text(encoding="utf-8")
    assert build_make.SEATS_LINE[1] in engine and build_make.SEATS_LINE[0] not in engine
    state = (site / D / "js/play-state.js").read_text(encoding="utf-8")
    assert YF.BLOCKLIST_LINE[1] in state and YF.BLOCKLIST_LINE[0] not in state
    for f in build_make.WORKER_API_JS:
        assert (site / D / "js" / f).read_bytes() == (ROOT / "worker-api/src" / f).read_bytes()
    # the seat laws' names are the one definition the forecast sheet's
    # regime table is written from (render_sheet.SEAT_LAWS)
    import render_sheet
    laws = json.loads((site / D / "laws.json").read_text(encoding="utf-8"))
    assert [(k, v["label"]) for k, v in laws.items()] == [(k, n) for k, n, _ in render_sheet.SEAT_LAWS]
    # the notes reach the reader through a LIVE region, where the number gate
    # cannot see them: no digit, and no em-dash aside (STYLE rules 4 and 8)
    for k, v in laws.items():
        assert not re.search(r"\d|\u2014|&", v["note"]), (k, v["note"])
    sheet_text = (ROOT / "forecast-sheet.html").read_text(encoding="utf-8")
    regimes = sheet_text[sheet_text.index("<!-- __REGIMES_START__ -->"):sheet_text.index("<!-- __REGIMES_END__ -->")]
    assert re.findall(r'class="rg-h[^"]*">([^<]+)<br>', regimes) == [n for _k, n, _ in render_sheet.SEAT_LAWS]


def test_the_page_scripts_pass_and_the_check_reaches_every_writer():
    site = _built()
    assert _writes(site) == []
    # it looked: each section's page module, unlisted, is refused for what a
    # writer does
    for w in (ADJUST, BREAK):
        found = _writes(site, writers={k: v for k, v in S.LIVE_WRITERS.items() if k != w})
        assert any(x.startswith(f"{w}: a data source") for x in found), (w, found)
    # their imports are read as non-writers
    for f in ("play-state.js", "yf-url.js", "make-state.js", "builder-state.js", "map.js",
              "card-text.js", "seat-table.js"):
        mod = site / D / "js" / f
        body = mod.read_text(encoding="utf-8")
        try:
            mod.write_text(body + "\nexport const rows = [1, 2];\n", encoding="utf-8")
            assert any(w.startswith(f"{D}/js/{f}: a data block") for w in _writes(site)), f
        finally:
            mod.write_text(body, encoding="utf-8")
    assert _writes(site) == []


def test_a_figure_outside_a_live_region_is_refused_and_the_refusal_reverts():
    site = _built()
    share1, share2, card = f"{D}/js/play-share.js", f"{D}/js/make-share.js", f"{D}/js/play-card.js"
    cases = (
        # section 1's writer: into the published seat twin, into a region it
        # is not listed for (section 2's), by markup
        (ADJUST, "document.querySelector('.pl-seats').textContent = String(r.draws);\n", "a lookup that is not a LIVE selector"),
        (ADJUST, "document.querySelector('[data-live=\"b-council\"] .bars').textContent = '1';\n", "a LIVE region it is not listed for"),
        (ADJUST, "R.seats.innerHTML = '<td>1</td>';\n", "HTML injection"),
        # section 2's writer: into section 1's seats, out of its region
        (BREAK, "document.querySelector('[data-live=\"seats\"]').textContent = '66';\n", "a LIVE region it is not listed for"),
        (BREAK, "one.bars.closest('.builder').append('1');\n", "traversal out of the region"),
        # the share sheets, into each other's region
        (share1, "document.querySelector('[data-live=\"b-share\"] .shurl').value = '1';\n", "a LIVE region it is not listed for"),
        (share2, "document.querySelector('[data-live=\"share\"] img').alt = '1';\n", "a LIVE region it is not listed for"),
        # the share image's words, listed for no region
        (card, "document.querySelector('[data-live=\"share\"] img').alt = '1';\n", "a LIVE region it is not listed for"),
        (card, "export const D = [412, 38];\n", "a data block"),
        (card, 'fetch("../draws/index.json");\n', "a data source"),
        (card, 'document["body"].append("97 seats");\n', "a document-level handle"),
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
    # the one share sheet looks up nothing: it writes only to the elements
    # each section took from its own region and handed it (the build's scan
    # would allow it a lookup into either region it is listed for, so this
    # is checked here); and each section's content module stays in its one
    # region
    sheet_js = (site / SHEET).read_text(encoding="utf-8")
    looks = lambda js: [w for w in ("querySelector", "getElementBy", "elementFromPoint") if w in js]
    assert looks(sheet_js) == []
    assert looks(sheet_js + "document.querySelector('[data-live=\"share\"] img').alt = '1';") == ["querySelector"]
    assert S.LIVE_WRITERS[SHEET] == frozenset({"share", "b-share"})
    assert S.LIVE_WRITERS[f"{D}/js/play-share.js"] == frozenset({"share"})
    assert S.LIVE_WRITERS[f"{D}/js/make-share.js"] == frozenset({"b-share"})
    assert _writes(site) == []
    # a module that is NOT listed, imported by a writer, writing a figure
    writer = site / ADJUST
    body = writer.read_text(encoding="utf-8")
    extra = site / D / "js/extra.js"
    try:
        extra.write_text("export function show(n) {\n"
                         "  document.querySelector('[data-live=\"seats\"]').textContent = `${n} seats`;\n}\n",
                         encoding="utf-8")
        writer.write_text('import { show } from "./extra.js";\n' + body, encoding="utf-8")
        assert any(w.startswith(f"{D}/js/extra.js: template interpolation") for w in _writes(site))
    finally:
        writer.write_text(body, encoding="utf-8")
        extra.unlink(missing_ok=True)
    assert _writes(site) == []


def test_the_build_itself_blocks_an_unlisted_writer_and_a_typed_live_digit():
    _built()      # skips, loudly, where the site cannot be built
    real_writers, real_assemble = dict(S.LIVE_WRITERS), YF.assemble
    with tempfile.TemporaryDirectory() as t:
        # 1. both sections' page modules, unlisted: the build refuses outright
        for w in (ADJUST, BREAK):
            del S.LIVE_WRITERS[w]
        try:
            (Path(t) / "a").mkdir()
            code, log = _build(Path(t) / "a")
        finally:
            S.LIVE_WRITERS.clear()
            S.LIVE_WRITERS.update(real_writers)
        assert code not in (0, None) and "PAGE SCRIPT WRITES FIGURES" in log, log[-2000:]
        for w in (ADJUST, BREAK):
            assert f"{YF.YF_PAGE}: {w}: a data source" in log, w

        # 2. a digit typed into a LIVE region of each section: the stamp blocks
        def typed(**kw):
            html = real_assemble(**kw)
            for marker, words in (('<div data-live="flips" class="pl-flips yf-slot">', "The DA wins 71 seats. "),
                                  ('<p class="ess restate yf-slot">', "The DA wins 77 seats. ")):
                assert html.count(marker) == 1, marker
                html = html.replace(marker, marker + words)
            return html
        YF.assemble = typed
        try:
            (Path(t) / "b").mkdir()
            code, log = _build(Path(t) / "b")
        finally:
            YF.assemble = real_assemble
        assert code in (0, None), log[-2000:]
        pages, blocking = _stamp(Path(t) / "b")
        assert blocking >= 2 and YF.YF_PAGE in pages
        review = (Path(t) / "NUMBERS-REVIEW.md").read_text(encoding="utf-8")
        assert re.search(r"\| BLOCKS \| num \| live:flips \| `71` \|", review), review[:2000]
        assert re.search(r"\| BLOCKS \| num \| live:b-council \| `77` \|", review), review[-3000:]

        # 3. reverted, the same build is quiet again
        (Path(t) / "c").mkdir()
        code, log = _build(Path(t) / "c")
        assert code in (0, None), log[-2000:]
        assert _stamp(Path(t) / "c")[1] == 0


def test_deploy_check_refuses_a_file_git_does_not_track_then_goes_quiet():
    """Wrangler uploads site/ from disk, ignored files included: two gitignored
    .pyc files carrying a local path sat in the served page code unseen by the
    runbook's `git status` (code review 2026-10-01). Shown on a throwaway
    repository."""
    import subprocess
    with tempfile.TemporaryDirectory() as t:
        repo = Path(t)
        site = repo / "site"
        (site / D / "py/page").mkdir(parents=True)
        (site / "index.html").write_text("<p>page</p>", encoding="utf-8")
        (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n.DS_Store\n", encoding="utf-8")
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)
        git("init", "-q")
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "site")
        assert deploy_check.untracked(site, root=repo) == []
        stray = site / D / "py/page/__pycache__/polling.cpython-313.pyc"
        stray.parent.mkdir()
        stray.write_bytes(b"/Users/someone/site/py/page/polling.py")
        (site / "new.js").write_text("x", encoding="utf-8")
        (site / ".DS_Store").write_bytes(b"")
        assert deploy_check.untracked(site, root=repo) == [
            "new.js", f"{D}/py/page/__pycache__/polling.cpython-313.pyc"]
        stray.unlink()
        git("add", "site/new.js")
        assert deploy_check.untracked(site, root=repo) == []


def test_every_page_links_it_and_it_has_its_own_card():
    """Every page's nav links to /your-forecast/, the page one level down
    marks itself, and its share card is its own and carries no figure."""
    site = _built()
    pages = sorted(p for p in site.glob("*.html") if p.name != "portal.html")
    assert len(pages) >= 5, pages
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert f'href="{YF.YF_HREF}">your forecast</a>' in text, page.name
        for d in YF.RETIRED:
            assert f'href="{d}/"' not in text, (page.name, d)
    html = _html(site)
    assert f'class="active" href="../{YF.YF_HREF}">your forecast</a>' in html
    og = dict(re.findall(r'<meta property="og:(title|description|url)" content="([^"]*)"', html))
    assert og["title"] == YF.OG_TITLE and og["url"].endswith(f"/{YF.YF_HREF}"), og
    from html import unescape
    assert not re.search(r"\d", unescape(og["title"] + og["description"])), og
    assert html.count('property="og:image"') == 1


def test_wide_section_1_stacks_the_map_over_the_seat_table_at_full_size():
    """Owner, 2026-10-03 ("stacked … plenty of space … too small"): on a wide
    screen the map sits ABOVE the seat table, each the results column's full
    width, in the page's flow. The levers' column is play.css's, which holds
    still and scrolls on its own so the results stay beside the lever being
    moved (owner, 2026-10-05: "they used to, which was good as you could see
    the effect"), and on this page it shows no scroll bar (owner, 2026-10-05:
    "a visible scroll bar beside the results text"). On the built page the
    map's figure comes before the seat table's inside the results grid; the
    stylesheets give the grid no second column, put no height cap or inner
    scroll on the results column, and cap the map only at the window's
    height; the levers' column is sticky and scrolls on its own, with its
    scroll bar hidden in both spellings. A constructed side-by-side grid, a
    capped results column, a column taken out of its sticky scroll and one
    whose scroll bar shows are caught, and the check goes quiet when they are
    reverted."""
    site = _built()
    html = _html(site)
    grid = html[html.index('class="pl-rgrid"'):]
    assert grid.index('class="pl-mapfig"') < grid.index('class="pl-seatfig"') < grid.index('class="pl-mapnotes"')
    play = (site / D / "css" / "play.css").read_text(encoding="utf-8")
    yf = (site / D / "css" / "your-forecast.css").read_text(encoding="utf-8")

    def side_by_side(css: str) -> list[str]:
        return [m.group(0) for m in re.finditer(r"\.pl-rgrid\{[^}]*grid-template-columns[^}]*\}", css)]

    def capped(css: str) -> list[str]:
        return [m.group(0) for m in re.finditer(r"\.pl-resultscol\{[^}]*(?:max-height|overflow)[^}]*\}", css)]

    assert not side_by_side(play + yf)
    assert side_by_side(play + ".pl-rgrid{display:grid;grid-template-columns:1fr 330px;}")
    assert not capped(play + yf)
    assert capped(play + ".pl-resultscol{max-height:calc(100vh - 60px);overflow-y:auto;}")
    def column(css: str) -> dict[str, str]:
        """The levers' column as the LAST rule for each property leaves it."""
        last = {}
        for body in re.findall(r"\.pl-controls\{([^}]*)\}", css):
            for decl in body.split(";"):
                if ":" in decl:
                    k, v = (x.strip() for x in decl.split(":", 1))
                    last["overflow-y" if k == "overflow" else k] = v.split()[-1] if k == "overflow" else v
        return last

    def holds_still(css: str) -> bool:
        """Sticky, capped at the window's height, scrolling on its own."""
        c = column(css)
        return (c.get("position") == "sticky" and c.get("max-height", "").startswith("calc(100vh")
                and c.get("overflow-y") in ("auto", "scroll"))

    def bar_shows(css: str) -> bool:
        """Does the column show a scroll bar: a scrollbar-width other than
        none, a stable gutter, or no WebKit rule hiding the bar?"""
        c = column(css)
        return (c.get("scrollbar-width") != "none" or "stable" in c.get("scrollbar-gutter", "")
                or not re.search(r"\.pl-controls::-webkit-scrollbar\{display:none;?\}", css))

    assert holds_still(play) and bar_shows(play), \
        "play.css no longer gives /play/ its still, self-scrolling column with its bar: re-check this test"
    assert holds_still(play + yf), "the levers' column does not hold still and scroll on its own on /your-forecast/"
    assert not holds_still(play + yf + ".yf .pl-controls{position:static;}")
    assert not holds_still(play + yf + ".yf .pl-controls{overflow:visible;}")
    assert not bar_shows(play + yf), "the levers' column shows a scroll bar on /your-forecast/"
    assert bar_shows(play + yf + ".yf .pl-controls{scrollbar-width:auto;}")
    assert bar_shows(play + yf + ".yf .pl-controls{scrollbar-gutter:stable;}")
    assert bar_shows(play + yf.replace("::-webkit-scrollbar{display:none;}", "::-webkit-scrollbar{width:8px;}"))
    assert ".pl-controls::after{" in yf and "position:sticky;bottom:0" in yf, "the column's foot has no fade"
    assert re.search(r"\.yf \.pl-wardmap\{max-height:calc\(100vh - \d+px\);\}", yf)


def test_every_footnote_marker_names_its_notes_position():
    """Each footnote marker's number is its note's place in the notes list,
    including the one css/your-forecast.css draws inside the vote step (a
    LIVE region holds no build-time digit). Every note is pointed at. A
    marker moved out of step is caught, and the check goes quiet when it is
    reverted."""
    site = _built()
    html = _html(site)
    css = (site / D / "css" / "your-forecast.css").read_text(encoding="utf-8")
    notes = re.findall(r'<li id="(note-[a-z-]+)"', html[html.index('aria-labelledby="h-notes"'):])

    def wrong(page: str, sheet: str) -> list:
        marks = re.findall(r'<sup class="fn"><a href="#(note-[a-z-]+)">(\d+)</a></sup>', page)
        drawn = re.findall(r'<a class="(yf-fn[a-z]+)" href="#(note-[a-z-]+)"', page)
        for cls, note in drawn:
            m = re.search(r"\." + cls + r"::after\{content:\"(\d+)\";\}", sheet)
            marks.append((note, m.group(1) if m else "?"))
        bad = [(n, k) for n, k in marks if n not in notes or int(k) != notes.index(n) + 1]
        return bad + [n for n in notes if n not in {m for m, _ in marks}]

    assert len(notes) >= 8, notes
    assert not wrong(html, css)
    assert wrong(html, css.replace('.yf-fnvote::after{content:"8";}', '.yf-fnvote::after{content:"7";}'))
    assert wrong(html.replace('href="#note-outcome">9<', 'href="#note-outcome">8<'), css)


def test_the_vote_is_a_table_with_no_spinner_and_no_inner_scroll():
    """Section 2's vote (owner, 2026-10-03): a row per party with the seat
    table's columns (party | slider | percent), the percent a text box with
    a decimal keypad (no spinner arrows), and the list never scrolls inside
    itself; the ward list is one table per area with fixed columns."""
    site = _built()
    js = (site / D / "js" / "make.js").read_text(encoding="utf-8")
    css = (site / D / "css" / "interactive.css").read_text(encoding="utf-8")
    assert 'type: "number"' not in js and 'inputMode: "decimal"' in js
    prlist = re.findall(r"\.prlist\{[^}]*\}", css)
    assert prlist and not any("max-height" in r or "overflow" in r for r in prlist), prlist
    assert re.search(r"\.prrow\{display:grid;grid-template-columns:minmax\(0,\d+px\) minmax\(0,1fr\) \d+px;", css)
    assert re.search(r"\.wltable\{[^}]*table-layout:fixed", css)
    assert 'el("table", { className: k ? "wltable wlcont" : "wltable" }' in js and 'el("details", { className: "rollup prmore" }' in js


# -- section 1: the engine -------------------------------------------------------

def _engine():
    """pyboot/page.py as the Worker runs it, natively, every cell loaded."""
    import importlib.util
    import os
    spec = importlib.util.spec_from_file_location("native_play", ROOT / "interactive/tools/native_play.py")
    NP = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(NP)
    cwd, path = os.getcwd(), list(sys.path)
    try:
        ns = NP._page(NP.SERVED, NP.SERVED)
        for c in NP.cells():
            d = NP.DRAWS / c["path"]
            ns["load_cell"](c["path"], (d / "manifest.json").read_text(), (d / "base.bin").read_bytes())
        ns["set_polls"](json.dumps(json.loads((NP.DRAWS / "index.json").read_text()).get("polls", [])))
    finally:
        os.chdir(cwd)
        sys.path[:] = path
    return NP, ns


PUBLISHED = {"cell": ".", "law": "deduct", "shift": [0, 0, 0, 0], "polls": [], "trust": 0}


def test_the_page_engine_at_uniform_weights_is_the_forecast_pages_rows():
    """DESIGN §4: the untouched page IS the published forecast, so section 1's
    LIVE side at uniform weights must show the rows the build twin shows, with
    the same figures, and call every ward as ward_winner_probs.csv does."""
    import subprocess
    _built()            # it also runs sync_py.mjs, which writes the served copy
    run = subprocess.run([sys.executable, str(ROOT / "interactive/tools/native_play.py")],
                         cwd=ROOT, capture_output=True, text=True, check=True)
    cases = {c["name"]: c["result"] for c in json.loads(run.stdout)["cases"]}
    out = cases["untouched"]
    sheet = {r["code"]: r for r in build_play.seat_rows((ROOT / "forecast-sheet.html").read_text(encoding="utf-8"))}
    assert set(out["shown"]) | {"OTHERS"} == set(sheet), (sorted(out["shown"]), sorted(sheet))
    for code, row in sheet.items():
        f = out["seats"][code]
        assert (round(f["median"]["value"]), round(f["p5"]["value"]), round(f["p95"]["value"])) == \
            (round(row["m"]), round(row["lo"]), round(row["hi"])), code
    assert out["flips"] == []
    with (ROOT / "data/processed/ward_winner_probs.csv").open(encoding="utf-8", newline="") as fh:
        pub = {r["ward"]: r for r in csv.DictReader(fh)}
    import render_map as RM
    for w in out["wards"]:
        call = RM.ward_call(w["ward"], pub[w["ward"]]["winner"], float(pub[w["ward"]]["p_win"]), pub[w["ward"]]["dist"])
        assert (w["winner"], w["fill"]) == (pub[w["ward"]]["winner"], call["fill"]), w["ward"]
    assert len(out["wards"]) == len(pub)
    moved = cases["black-african-plus-5"]
    assert moved["flips"] and any(moved["seats"][c]["vs_published"] for c in moved["shown"])


def test_the_live_by_election_line_is_the_builds_at_every_setting():
    """At the published turnout, poll and seat law, the reader's by-election
    comparison (page.py ``against_published_cell``) lists exactly the moves
    the build's line under the control lists (``build_play._moves``), for
    every by-election cell; at least one is outside the shown rows, which is
    the case the critic's S1 defect broke."""
    _built()
    NP, ns = _engine()
    pub, _ = build_play._cell_medians(".")
    others = [c for c in NP.cells() if c["path"] != "."]
    assert len(others) >= 2, others
    outside = 0
    for c in others:
        res = json.loads(ns["compute"](json.dumps({**PUBLISHED, "cell": c["path"]})))
        live = res["against_published_cell"]
        med, _ = build_play._cell_medians(c["path"])
        assert set(live) == set(med) | set(pub), (c["path"], sorted(set(live) ^ (set(med) | set(pub))))
        got = sorted((p, int(round(d["difference"]))) for p, d in live.items()
                     if not d["within_noise"] and round(d["difference"]))
        want = sorted(build_play._moves(med, pub))
        assert got == want, (c["path"], got, want)
        outside += sum(1 for p, _ in want if p not in res["shown"])
    assert outside, "no move outside the shown rows: the test cannot see the defect it guards"


# -- section 2: the start, and the hand-off from section 1 ---------------------

def test_the_start_is_rule_a_on_the_published_draws():
    """Section 2 opens on our prediction: rule A (``prediction.rule_a``) on the
    served draws, each draw counted once, in the schema's ward order, seated by
    ``prediction.seats_of``. Recomputed here from ``site/draws`` and compared
    with what the build wrote; the ward calls also agree with the forecast
    page's ``ward_winner_probs.csv`` wherever that file has no tie."""
    import numpy as np
    import prediction
    import reweight as R
    site = _built()
    d = _data(site)
    schema, start = d["schema"], d["start"]
    wards = schema["x-ward-ids"]
    man = json.loads((ROOT / "site/draws/manifest.json").read_text(encoding="utf-8"))
    arr = R.unpack((ROOT / "site/draws/base.bin").read_bytes(), man)
    cols = {b["name"]: b["columns"] for b in man["blocks"]}
    want = prediction.rule_a(arr["ward_winner"], man["ward_parties"], cols["ward_winner"],
                             arr["ward_vote"], arr["list_vote"], cols["list_vote"], ward_ids=wards)
    roster = schema["x-seat-context"]["parties"]
    assert start["ward_calls"] == want["ward_calls"]
    assert start["ward_votes"] == {p: want["ward_votes"][p] for p in roster}
    assert start["list_votes"] == {p: want["list_votes"][p] for p in roster}
    seated = prediction.seats_of(start, schema["x-seat-context"]["council"], order=roster)
    assert start["seats"] == {p: v["total"] for p, v in seated["seats"].items()}
    assert sum(start["seats"].values()) == seated["council"]
    assert start["rule"] == "rule A: src/prediction.py"
    # it can see: a different vote block gives a different start
    other = prediction.rule_a(arr["ward_winner"], man["ward_parties"], cols["ward_winner"],
                              arr["ward_vote"], np.roll(arr["list_vote"], 1, axis=1),
                              cols["list_vote"], ward_ids=wards)
    assert other["list_votes"] != want["list_votes"]
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
    assert schema["x-placeholder"] is False and not d["model_ref"].startswith("placeholder")
    assert d["model_ref"] == man["published_run"]["model_run_id"]
    assert schema["x-seat-context"]["parties"] == man["parties"]
    # no total is fixed: each prediction states its own (SPEC-B D1)
    assert "x-total-votes" not in schema and "x-share-sum" not in schema
    for gone in ("combined_share", "published_middle"):
        assert gone not in start, gone
    # as an entry, it re-seats exactly under reader_seats (the entry path)
    import score_forecasts
    entry = {"v": score_forecasts.entry_version(schema), "ward_calls": start["ward_calls"],
             "ward_votes": start["ward_votes"], "list_votes": start["list_votes"]}
    seated = score_forecasts.seat_forecast(entry, schema)
    assert seated["ok"], seated["errors"]
    assert {p: v["total"] for p, v in seated["seats"].items()} == start["seats"]


_DECODE = r"""
import { readFileSync } from "node:fs";
import * as B from "%s";
import * as MS from "%s";
const D = JSON.parse(readFileSync(process.argv[2], "utf8"));
const ctx = B.contextOf(D.schema);
const got = MS.decode(D.start.f, ctx);
process.stdout.write(JSON.stringify({ state: got.state, coalition: got.coalition, format: MS.FORMAT,
  out_of_bounds: B.outOfBounds(got.state, ctx) }));
"""


def _decode_start(d: dict) -> dict:
    """``decode(start.f)`` by the page's own decoder, under node."""
    import subprocess
    with tempfile.TemporaryDirectory() as t:
        (Path(t) / "dec.mjs").write_text(_DECODE % ((ROOT / "interactive/js/builder-state.js").as_uri(),
                                                    (ROOT / "interactive/js/make-state.js").as_uri()))
        (Path(t) / "data.json").write_text(json.dumps(d))
        p = subprocess.run(["node", str(Path(t) / "dec.mjs"), str(Path(t) / "data.json")],
                           capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)


def _start_mismatch(start: dict, decoded: dict, roster: list[str]) -> list[str]:
    st = decoded["state"]
    out = []
    if st["calls"] != start["ward_calls"]:
        out.append("ward calls differ")
    for ballot, key in (("ward", "ward_votes"), ("list", "list_votes")):
        if set(st[ballot]) != set(roster) or set(start[key]) != set(roster):
            out.append(f"{key} are not keyed by the roster, both ways")
        elif st[ballot] != start[key]:
            out.append(f"{key} differ")
    if decoded["coalition"] != []:
        out.append("the start names a coalition")
    return out


def test_the_start_is_decode_of_its_f():
    """Guard G7 (encoding side). ``start.f`` decodes, by the page's own
    decoder, to exactly the prediction object beside it: the 135 calls and
    both ballots' whole votes over the roster (keys equal both ways); the
    entry version in the schema is the page's FORMAT; ``out_of_bounds`` is the
    decoder's own list. A copy with one list vote changed is caught, and the
    comparison is quiet again once it is reverted."""
    import copy
    site = _built()
    d = _data(site)
    start, roster = d["start"], d["schema"]["x-seat-context"]["parties"]
    got = _decode_start(d)
    assert len(start["ward_calls"]) == len(d["schema"]["x-ward-ids"])
    assert _start_mismatch(start, got, roster) == []
    assert d["schema"]["properties"]["v"]["const"] == got["format"]
    assert start["out_of_bounds"] == got["out_of_bounds"]
    bad = copy.deepcopy(start)
    first = roster[0]
    bad["list_votes"][first] += 1
    assert _start_mismatch(bad, got, roster) == ["list_votes differ"]
    bad["list_votes"][first] -= 1
    assert _start_mismatch(bad, got, roster) == []


def _panel_row(ward, ballot, party, votes, vd="1", registered=100, valid=100):
    return {"Province": "x", "Municipality": "x", "Ward": ward, "VD_Number": vd, "VS_Name": "x",
            "BallotType": ballot, "Registered_Population": str(registered), "Spoilt_Votes": "0",
            "Total_Valid_Votes": str(valid), "sPartyName": party, "Party_Votes": str(votes)}


def _write_panel(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


_FRESH: dict = {}


def _fresh() -> dict:
    """``forecast.json`` as the build makes it now (``build_make.forecast_data``,
    which reads and writes nothing), once per run: what "the served bounds"
    means below."""
    if "d" not in _FRESH:
        _FRESH["d"] = json.loads(json.dumps(build_make.forecast_data()))
    return _FRESH["d"]


def test_the_editor_bounds_are_regenerated_from_the_panel():
    """Amendment 1, point 3, and slice B2a. ``x-editor-bounds`` names its
    panel, and the panel is exactly the cleaned metro LGE files before the
    target, both ways, each with its sha256 (``sources`` holds every file the
    bounds read, the national files of the prior among them); ``e`` is over
    exactly the schema's wards and sums to one; each election's extremes are
    ``panel_extremes`` over that election's files, and the effective bounds
    are the panel's extremes widened by their shape allowance (the mean of the
    record events, or ``EDITOR_WIDEN_PP`` with fewer than
    ``MIN_RECORD_EVENTS``), the runner-up's capped at ``RUNNER_UP_MAX``. Each
    input is shown to move its bound, and each reverted equals the built
    bounds: a constructed result file moves ``q_win`` (a ward won lower),
    ``q_run`` (a runner-up higher), ``gap_min`` and ``gap_max`` (a party's list
    share far below and far above its ward share); lifting the cap moves the
    capped ``q_run``; a roll with one ward's registration doubled moves that
    ward's ``e``, and a previous election with one VD's turnout doubled moves
    its ward's ``e``."""
    import cityconfig
    import hashlib
    import inputs_preflight
    import montecarlo
    from _support import scanned
    city = cityconfig.active()
    target = str(city.default_target)
    d = _fresh()
    b = d["schema"]["x-editor-bounds"]
    wards = d["schema"]["x-ward-ids"]
    roster = d["schema"]["x-seat-context"]["parties"]
    every = sorted((ROOT / "data/raw/elections").glob("lge*_*_vd_party_clean.csv"))
    files = [f for f in every if f.name[3:7] < target]
    assert b["panel"] == [f.name for f in files], b["panel"]
    # it looked: the panel is a two-sided fraction of every cleaned LGE file
    scanned(files, of=every, low=0.5, high=1.0, what="panel files",
            denominator="cleaned LGE result files on disk")
    # every file the bounds read, recomputed from the pairs and the priors, both ways
    tgt = cityconfig.Target(city=city, year=target)
    read = set(b["panel"])
    read |= {f"lge{y}_{c}_vd_party_clean.csv" for c, a_, b_ in b["swing"]["pairs"] for y in (a_, b_)}
    read |= {f"npe{n}_{c}_vd_party.csv" for c, n, _l in b["swing"]["npe_pairs"]}
    read |= {f"lge{l}_{c}_vd_party_clean.csv" for c, _n, l in b["swing"]["npe_pairs"]}
    read |= {f"lge{tgt.previous_lge}_{city.code}_vd_party_clean.csv", f"npe{tgt.previous_npe}_{city.code}_vd_party.csv"}
    assert set(b["sources"]) == read, (sorted(set(b["sources"]) ^ read))
    for name, sha in b["sources"].items():
        assert sha == hashlib.sha256((ROOT / "data/raw/elections" / name).read_bytes()).hexdigest(), name
    assert sorted(b["e"], key=int) == sorted(wards, key=int)
    assert math.isclose(math.fsum(b["e"].values()), 1.0, abs_tol=1e-12)
    per_year, ext, shape = b["shape"]["per_year"], b["panel_extremes"], b["shape"]["allowance"]
    assert sorted(per_year) == sorted({f.name[3:7] for f in files})
    for y, got in per_year.items():
        assert build_make.panel_extremes([f for f in files if f.name[3:7] == y]) == got, y
    assert build_make.panel_extremes(files) == ext
    for q in ("q_win", "q_run", "gap_min", "gap_max"):
        a = shape[q]
        assert (len(a["events"]) >= build_make.MIN_RECORD_EVENTS) == a["rule"].startswith("mean"), q
        if a["rule"].startswith("mean"):
            assert math.isclose(a["value"], math.fsum(e["exceedance"] for e in a["events"]) / len(a["events"])), q
        else:
            unit = 100.0 if q.startswith("q_") else 1.0
            assert a["value"] == build_make.EDITOR_WIDEN_PP / unit, q
    assert math.isclose(b["q_win"], max(0.0, ext["q_win"]["value"] - shape["q_win"]["value"]))
    assert math.isclose(b["q_run"], min(build_make.RUNNER_UP_MAX, ext["q_run"]["value"] + shape["q_run"]["value"]))
    assert math.isclose(b["gap_min"], ext["gap_min"]["value"] - shape["gap_min"]["value"])
    assert math.isclose(b["gap_max"], ext["gap_max"]["value"] + shape["gap_max"]["value"])
    # the cap: lifted, the capped bound moves to the widened extreme; restored, back
    widened = ext["q_run"]["value"] + shape["q_run"]["value"]
    real = build_make.RUNNER_UP_MAX
    try:
        build_make.RUNNER_UP_MAX = 1.0
        lifted = build_make.editor_bounds(city, target, wards, roster)["q_run"]
    finally:
        build_make.RUNNER_UP_MAX = real
    assert math.isclose(lifted, widened)
    assert (lifted != b["q_run"]) == (widened > real)
    assert build_make.editor_bounds(city, target, wards, roster)["q_run"] == b["q_run"]
    with tempfile.TemporaryDirectory() as t:
        odd = Path(t) / "lge2000_XXX_vd_party_clean.csv"
        # ward 1 won on 11 of 101 votes (ten parties); ward 2's runner-up holds
        # 49 of 100; on the list P0 is far above its ward share, P2 far below
        rows = [_panel_row("1", "Ward", f"P{i}", 11 if i == 0 else 10) for i in range(10)]
        rows += [_panel_row("2", "Ward", "P0", 51), _panel_row("2", "Ward", "P1", 49)]
        rows += [_panel_row("1", "PR", "P0", 170), _panel_row("1", "PR", "P1", 30),
                 _panel_row("1", "PR", "P2", 1)]
        _write_panel(odd, rows)
        moved = build_make.panel_extremes(files + [odd])
        for key, lower in (("q_win", True), ("q_run", False), ("gap_min", True), ("gap_max", False)):
            assert moved[key]["file"] == odd.name, key
            assert (moved[key]["value"] < ext[key]["value"]) == lower, key
        assert build_make.panel_extremes(files) == ext
        e0, _ = build_make.expected_ward_shares(city, target, wards)
        assert e0 == b["e"]
        snap = inputs_preflight.roll_snapshot(city.slug)
        with snap.open(encoding="utf-8", newline="") as fh:
            roll = list(csv.DictReader(fh))
        roll[0]["Registered"] = str(2 * int(roll[0]["Registered"]))
        doubled = Path(t) / snap.name
        _write_panel(doubled, roll)
        e1, _ = build_make.expected_ward_shares(city, target, wards, roll=doubled)
        w0 = str(int(roll[0]["Ward"][len(city.ward_prefix):]))
        assert e1[w0] > e0[w0]
        roll[0]["Registered"] = str(int(roll[0]["Registered"]) // 2)
        _write_panel(doubled, roll)
        assert build_make.expected_ward_shares(city, target, wards, roll=doubled)[0] == e0
        # the previous election's turnout: one VD's valid ward votes doubled
        tgt = cityconfig.Target(city=city, year=target)
        prev = cityconfig.resolve_path(ROOT / city.path("raw", "elections") / tgt.results(tgt.previous_lge))
        parts, _label = montecarlo.ward_parts(tgt, ROOT / city.path("raw", "elections"), ROOT / tgt.crosswalk.parent)
        with prev.open(encoding="utf-8", newline="") as fh:
            old = list(csv.DictReader(fh))
        in_file = {r["VD_Number"] for r in old}
        vd, ward = next((v, w) for v, w, _reg in parts if v in in_file)
        def turnout(k):
            out = [dict(r) for r in old]
            for r in out:
                if r["VD_Number"] == vd and r["BallotType"].strip().upper() == "WARD":
                    r["Total_Valid_Votes"] = str(int(r["Total_Valid_Votes"]) * k)
            path = Path(t) / prev.name
            _write_panel(path, out)
            return build_make.expected_ward_shares(city, target, wards, previous=path)[0]
        assert turnout(2)[str(ward)] > e0[str(ward)]
        assert turnout(1) == e0


def _mirror(t: str, replace: dict | None = None) -> Path:
    """A directory standing in for ``data/raw/elections``: a link to every file
    there, except the ones named in ``replace`` (``{name: rows}``), written as
    constructed copies. The bounds read it through their ``elections``
    argument; nothing under ``data/`` is touched."""
    src = ROOT / "data/raw/elections"
    out = Path(t) / "elections"
    out.mkdir()
    for f in src.iterdir():
        if f.is_file() and f.name not in (replace or {}):
            (out / f.name).symlink_to(f)
    for name, rows in (replace or {}).items():
        _write_panel(out / name, rows)
    return out


def _rows(name: str) -> list[dict]:
    with (ROOT / "data/raw/elections" / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _ranges_from(b: dict, wards, roster, **where) -> tuple[dict, dict]:
    """``(ward_ranges, party_ranges)`` from the priors read at ``where``
    (``elections``, ``processed``) under the served swings and allowance, so a
    change to a prior is seen alone."""
    import cityconfig
    city = cityconfig.active()
    target = str(city.default_target)
    local = build_make.ward_priors(city, target, wards, **where)
    national = build_make.npe_priors(city, target, wards, **where)
    bins = {k: b["swing"]["extremes"][k] for k in ("ward", "npe_ward")}
    cells, party = build_make.ward_ranges(roster, wards, local, national, bins, b["allowance"],
                                          b["swing"]["newcomer"])
    return json.loads(json.dumps(cells)), json.loads(json.dumps(party))


def _changed(a: dict, b: dict) -> set[str]:
    """The wards whose ward ranges differ between two ``ward_ranges``."""
    return {w for w in set(a) | set(b) if a.get(w) != b.get(w)}


def test_the_ward_ranges_are_regenerated_from_the_panel():
    """Slice B2a (SPEC-B2r2 §4-§5). Populations, each recomputed here from the
    files and compared both ways: ``swing.pairs`` is every (metro, a, b) of
    consecutive cleaned local files before the target, a the calendar's local
    election before b; ``swing.npe_pairs`` every (metro, n, l), n the
    calendar's national election before l, the approximation left out; the
    ``ward_ranges`` cells are exactly the (ward, party) pairs with a ward vote
    in the ward's parts at the preceding local election, or, for a party with
    no ward vote anywhere in the city then, a national vote in them; each
    ``party_ranges`` entry is of the kind its party's history says (local,
    national or newcomer); ``party_ranges`` and ``city_limits`` are keyed by
    exactly the roster.

    Constructed violations, each on a mirror of the result files with one
    file rewritten (or one crosswalk), each seen and each quiet when reverted:
    (1) one VD's party votes in the preceding file raised: exactly the wards
    that VD's parts lie in change their ranges; (2) a split VD's
    ``part_registered`` changed: both its wards' priors and ``e`` move; (3) a
    stood-both swing pushed past its bin's greatest: that bin's extreme moves,
    no other; (4) a party's ward rows deleted in one ward's VDs: its range
    there becomes its citywide one; (5) a party deleted from the preceding
    file: its national vote becomes its prior, and deleted from the national
    file too it becomes a newcomer; (6) a party new to local
    elections deleted from the national file: it becomes a newcomer; (7) one
    VD's national votes raised: exactly that VD's wards move."""
    import collections
    import cityconfig
    import montecarlo
    import parties as P
    from _support import scanned
    city = cityconfig.active()
    target = str(city.default_target)
    d = _fresh()
    b = d["schema"]["x-editor-bounds"]
    wards = d["schema"]["x-ward-ids"]
    roster = d["schema"]["x-seat-context"]["parties"]
    tgt = cityconfig.Target(city=city, year=target)
    el = ROOT / "data/raw/elections"
    # -- the pairs, recomputed from the file names and the calendar
    lge = {(m.group(2), m.group(1)) for f in el.glob("lge*_*_vd_party_clean.csv")
           if (m := re.fullmatch(r"lge(\d{4})_([A-Z]+)_vd_party_clean\.csv", f.name))}
    npe = {(m.group(2), m.group(1)) for f in el.glob("npe*_*_vd_party.csv")
           if (m := re.fullmatch(r"npe(\d{4})_([A-Z]+)_vd_party\.csv", f.name))}
    pairs = {(c, cityconfig.preceding(y, "LGE"), y) for c, y in lge
             if y < target and (c, cityconfig.preceding(y, "LGE")) in lge}
    npe_pairs = {(c, cityconfig.preceding(y, "NPE"), y) for c, y in lge
                 if y < target and (c, cityconfig.preceding(y, "NPE")) in npe}
    assert {tuple(x) for x in b["swing"]["pairs"]} == pairs
    assert {tuple(x) for x in b["swing"]["npe_pairs"]} == npe_pairs
    scanned(pairs, of=[x for x in lge if x[1] < target], low=0.5, high=1.0,
            what="local pairs", denominator="cleaned local files before the target")
    assert all(build_make.APPROXIMATE not in cityconfig.CALENDAR[n].results for _c, n, _l in b["swing"]["npe_pairs"])
    # -- the cells and the kinds, recomputed with a join written here
    parts, _label = montecarlo.ward_parts(tgt, el, ROOT / tgt.crosswalk.parent)
    prev = f"lge{tgt.previous_lge}_{city.code}_vd_party_clean.csv"
    nat = f"npe{tgt.previous_npe}_{city.code}_vd_party.csv"
    local_by_vd = collections.defaultdict(set)
    for r in _rows(prev):
        if r["BallotType"].strip().upper() == "WARD" and int(r["Party_Votes"]) > 0:
            local_by_vd[r["VD_Number"].strip()].add(P.canonical(r["sPartyName"]))
    national_by_vd = collections.defaultdict(set)
    for r in _rows(nat):
        if int(r["Party_Votes"]) > 0:
            national_by_vd[r["VD_Number"].strip()].add(P.canonical(r["sPartyName"]))
    stood_local = set().union(*local_by_vd.values())
    stood_national = set().union(*national_by_vd.values())
    kind = {c: "local" if c in stood_local else "national" if c in stood_national else "newcomer"
            for c in roster}
    want = set()
    for vd, w, reg in parts:
        if reg > 0:
            want |= {(str(w), c) for c in local_by_vd.get(vd, ()) if c in kind}
            want |= {(str(w), c) for c in national_by_vd.get(vd, ()) if kind.get(c) == "national"}
    got = {(w, c) for w, row in b["ward_ranges"].items() for c in row}
    assert got == want, (sorted(got - want)[:5], sorted(want - got)[:5])
    scanned(got, of=len(wards) * len(roster), low=0.05, high=0.95, what="(ward, party) cells",
            denominator="wards times roster parties")
    assert {c: v["kind"] for c, v in b["party_ranges"].items()} == kind
    assert set(b["city_limits"]) == set(roster)
    assert {"local", "national", "newcomer"} == set(kind.values())
    for w, row in b["ward_ranges"].items():
        for c, (lo, hi) in row.items():
            assert 0.0 <= lo <= hi <= 1.0, (w, c)
    # -- the constructed violations
    served = (b["ward_ranges"], b["party_ranges"])
    vd_wards = collections.defaultdict(set)
    for vd, w, reg in parts:
        if reg > 0:
            vd_wards[vd].add(str(w))
    with tempfile.TemporaryDirectory() as t:
        assert _ranges_from(b, wards, roster, elections=_mirror(t)) == served
    # (1) one VD's party votes raised in the preceding file
    rows = _rows(prev)
    vd = next(v for v in sorted(vd_wards) if len(vd_wards[v]) == 1 and v in local_by_vd)
    for r in rows:
        if r["VD_Number"].strip() == vd and r["BallotType"].strip().upper() == "WARD" and int(r["Party_Votes"]) > 0:
            r["Party_Votes"] = str(int(r["Party_Votes"]) * 3 + 100)
            break
    with tempfile.TemporaryDirectory() as t:
        cells, _party = _ranges_from(b, wards, roster, elections=_mirror(t, {prev: rows}))
    assert _changed(cells, b["ward_ranges"]) == vd_wards[vd]
    # (2) a split VD's part_registered changed in a copied crosswalk
    with tgt.crosswalk.open(encoding="utf-8", newline="") as fh:
        xw = list(csv.DictReader(fh))
    split = next(r["VD_Number"] for r in xw if r.get("is_split") == "Y" and r["VD_Number"] in local_by_vd)
    both = {r[f"Ward_{target}"] for r in xw if r["VD_Number"] == split}
    first = next(r for r in xw if r["VD_Number"] == split)
    first["part_registered"] = str(int(first["part_registered"]) * 2 + 1)
    e0 = b["e"]
    with tempfile.TemporaryDirectory() as t:
        proc = Path(t) / "processed"
        proc.mkdir()
        _write_panel(proc / tgt.crosswalk.name, xw)
        h0 = build_make.ward_priors(city, target, wards)["h"]
        h1 = build_make.ward_priors(city, target, wards, processed=proc)["h"]
        e1, _ = build_make.expected_ward_shares(city, target, wards, processed=proc)
    assert len(both) == 2
    assert {w for w in wards if h0.get(w) != h1.get(w)} == both
    assert all(e1[w] != e0[w] for w in both)
    # (3) one stood-both swing pushed past its bin's greatest, by rewriting the
    # later file of a transition (one whose later election starts no pair, of
    # another metro), read by swing_panel from a mirror
    panel = build_make.swing_panel(city, target)
    ext = build_make.swing_extremes(panel)
    assert json.loads(json.dumps({k: ext[k] for k in ("ward", "city", "npe_ward", "npe_city")})) \
        == b["swing"]["extremes"]
    last = max(y for _c, _a, y in pairs)
    code3, _a3, b3, w3, p3, h3, _s3 = next(r for r in panel["ward_rows"] if r[0] != city.code and r[2] == last
                                          and 0.05 < r[5] <= 0.15 and r[6] > 0)
    k = build_make._bin(h3)
    want = h3 + ext["ward"][k][1] + 0.05
    assert want < 1
    name3 = f"lge{b3}_{code3}_vd_party_clean.csv"
    rows3 = _rows(name3)
    in_ward = [r for r in rows3 if r["BallotType"].strip().upper() == "WARD" and r["Ward"].strip() == w3]
    mine = [r for r in in_ward if P.canonical(r["sPartyName"]) == p3]
    rest = sum(int(r["Party_Votes"]) for r in in_ward if P.canonical(r["sPartyName"]) != p3)
    for r in mine:
        r["Party_Votes"] = "0"
    mine[0]["Party_Votes"] = str(math.ceil(want * rest / (1 - want)))
    with tempfile.TemporaryDirectory() as t:
        moved = build_make.swing_extremes(build_make.swing_panel(city, target, elections=_mirror(t, {name3: rows3})))["ward"]
    assert moved[k][1] >= want - h3 - 1e-9 > ext["ward"][k][1]
    assert [j for j in range(len(moved)) if moved[j][1] != ext["ward"][j][1]] == [k]
    with tempfile.TemporaryDirectory() as t:
        assert build_make.swing_extremes(build_make.swing_panel(city, target, elections=_mirror(t)))["ward"] \
            == ext["ward"]
    # (4) a party's ward rows deleted in one ward's VDs
    w = next(w for w in wards if any(kind[c] == "local" for c in b["ward_ranges"].get(w, {})))
    c = next(c for c in sorted(b["ward_ranges"][w]) if kind[c] == "local")
    its = {vd for vd, ws in vd_wards.items() if w in ws}
    cut = [r for r in _rows(prev) if not (r["VD_Number"].strip() in its and P.canonical(r["sPartyName"]) == c
                                         and r["BallotType"].strip().upper() == "WARD")]
    with tempfile.TemporaryDirectory() as t:
        cells, party = _ranges_from(b, wards, roster, elections=_mirror(t, {prev: cut}))
    assert c not in cells.get(w, {}) and party[c]["kind"] == "local"
    lost = {x for x in wards if c in b["ward_ranges"].get(x, {}) and c not in cells.get(x, {})}
    assert w in lost and lost <= set().union(*(vd_wards[v] for v in its))
    # (5) a party deleted from the preceding file: its national vote becomes
    # its prior; deleted from the national file too, it is a newcomer
    c5 = min((c for c in roster if kind[c] == "local" and c in stood_national),
             key=lambda c: b["party_ranges"][c]["prior"])
    gone = [r for r in _rows(prev) if P.canonical(r["sPartyName"]) != c5]
    with tempfile.TemporaryDirectory() as t:
        cells, party = _ranges_from(b, wards, roster, elections=_mirror(t, {prev: gone}))
    assert party[c5]["kind"] == "national"
    assert {w for w, row in cells.items() if c5 in row} == \
        {str(w) for vd, w, reg in parts if reg > 0 and c5 in national_by_vd.get(vd, ())}
    nat_gone = [r for r in _rows(nat) if P.canonical(r["sPartyName"]) != c5]
    with tempfile.TemporaryDirectory() as t:
        cells, party = _ranges_from(b, wards, roster, elections=_mirror(t, {prev: gone, nat: nat_gone}))
    assert party[c5]["kind"] == "newcomer" and not any(c5 in row for row in cells.values())
    # (6) a party new to local elections deleted from the national file
    c6 = max((c for c in roster if kind[c] == "national"), key=lambda c: b["party_ranges"][c]["prior"])
    nrows = [r for r in _rows(nat) if P.canonical(r["sPartyName"]) != c6]
    with tempfile.TemporaryDirectory() as t:
        cells, party = _ranges_from(b, wards, roster, elections=_mirror(t, {nat: nrows}))
    assert party[c6]["kind"] == "newcomer" and not any(c6 in row for row in cells.values())
    # (7) one VD's national votes raised
    nrows = _rows(nat)
    vd7 = next(v for v in sorted(vd_wards) if len(vd_wards[v]) == 1
               and c6 in national_by_vd.get(v, ()))
    for r in nrows:
        if r["VD_Number"].strip() == vd7 and P.canonical(r["sPartyName"]) == c6:
            r["Party_Votes"] = str(int(r["Party_Votes"]) * 3 + 100)
    with tempfile.TemporaryDirectory() as t:
        cells, _party = _ranges_from(b, wards, roster, elections=_mirror(t, {nat: nrows}))
    assert _changed(cells, b["ward_ranges"]) == vd_wards[vd7]
    # reverted: the plain mirror again gives the served ranges
    with tempfile.TemporaryDirectory() as t:
        assert _ranges_from(b, wards, roster, elections=_mirror(t)) == served


def _parts_differ(ours, theirs) -> list:
    """The parts in one list and not the other, both ways."""
    a, b = set(ours), set(theirs)
    return sorted(a - b)[:3] + sorted(b - a)[:3]


def test_the_panel_reads_a_held_election_as_ward_parts_does():
    """``build_make._held_parts`` restates ``montecarlo.ward_parts``' rule for
    a held election (every VD whole, in the ward its own file names), because
    that function resolves the file through the ACTIVE city and the panel
    reads every metro. Held equal on every held local election of every metro
    on disk, both ways, each metro made the active city for its own call (and
    the active city restored after); a constructed difference (one VD moved to
    another ward) is found by the same comparison, which is quiet again on the
    real lists."""
    import cityconfig
    import montecarlo
    from _support import scanned
    el = ROOT / "data/raw/elections"
    slugs = sorted(f.stem for f in (ROOT / "cities").glob("*.toml"))
    saved = (cityconfig._ACTIVE, cityconfig._TARGET)
    compared = []
    try:
        for slug in slugs:
            city = cityconfig.use(slug)
            for y, e in cityconfig.CALENDAR.items():
                if e.kind != "LGE" or not e.results:
                    continue
                path = el / e.results.replace("{CODE}", city.code)
                if not path.is_file():
                    continue
                tgt = cityconfig.Target(city=city, year=y)
                theirs, _label = montecarlo.ward_parts(tgt, el, ROOT / tgt.crosswalk.parent)
                ours = build_make._held_parts(build_make._lge(path))
                assert _parts_differ(ours, theirs) == [], (slug, y)
                assert len(ours) == len(theirs), (slug, y)
                compared.append((slug, y))
    finally:
        cityconfig._ACTIVE, cityconfig._TARGET = saved
    every = list(el.glob("lge*_*_vd_party_clean.csv"))
    scanned(compared, of=every, low=0.9, high=1.0, what="held local elections compared",
            denominator="cleaned local result files on disk")
    # it can see: one VD moved to another ward is found, both ways
    moved = list(ours)
    moved[0] = (moved[0][0], moved[0][1] + "x", moved[0][2])
    assert len(_parts_differ(moved, theirs)) == 2
    assert _parts_differ(ours, theirs) == []


def test_the_city_limits_are_regenerated_from_the_panel():
    """Slice B2a, JUDGEMENT-CALLS §R12. Every party's ``city_limits`` entry is
    recomputed here: its kind from the files (``local`` with a ward vote in the
    city at the preceding local election, else ``national`` with a vote at the
    preceding national one, else ``newcomer``), equal to its ``party_ranges``
    kind (one rule); a local party's prior is its share of the preceding
    election joined onto the target's wards by a join written here and
    weighted by the served ``e``, moved by the citywide extremes of its bin and
    the city allowance; a national party's, its national citywide share moved
    by the national-to-local citywide extremes; a newcomer's, zero to the
    citywide newcomer cap plus the city allowance. Constructed, each seen and
    quiet when reverted: one citywide swing pushed past its bin moves that
    bin's extreme and exactly the limits of the local parties starting in it;
    a party's collapse from a national to a local election is left out of the
    national-to-local citywide extremes, and the same swing short of a
    collapse moves them."""
    import bisect
    import collections
    import cityconfig
    import montecarlo
    import parties as P
    city = cityconfig.active()
    target = str(city.default_target)
    d = _fresh()
    b = d["schema"]["x-editor-bounds"]
    wards = d["schema"]["x-ward-ids"]
    roster = d["schema"]["x-seat-context"]["parties"]
    tgt = cityconfig.Target(city=city, year=target)
    el = ROOT / "data/raw/elections"
    parts, _label = montecarlo.ward_parts(tgt, el, ROOT / tgt.crosswalk.parent)
    prev = f"lge{tgt.previous_lge}_{city.code}_vd_party_clean.csv"
    nat = f"npe{tgt.previous_npe}_{city.code}_vd_party.csv"
    by_vd = collections.defaultdict(collections.Counter)
    for r in _rows(prev):
        if r["BallotType"].strip().upper() == "WARD":
            by_vd[r["VD_Number"].strip()][P.canonical(r["sPartyName"])] += int(r["Party_Votes"])
    national = collections.Counter()
    for r in _rows(nat):
        national[P.canonical(r["sPartyName"])] += int(r["Party_Votes"])
    nat_total = sum(national.values())
    local_city = collections.Counter()
    for c in by_vd.values():
        local_city.update(c)
    vd_reg = collections.Counter()
    for vd, _w, reg in parts:
        vd_reg[vd] += reg
    acc = collections.defaultdict(collections.Counter)
    for vd, w, reg in parts:
        if vd in by_vd and vd_reg[vd]:
            for c, v in by_vd[vd].items():
                acc[str(w)][c] += v * reg / vd_reg[vd]
    prior_e = collections.Counter()
    for w, c in acc.items():
        t = sum(c.values())
        for code, v in c.items():
            prior_e[code] += b["e"][w] * v / t
    kind = {c: "local" if local_city[c] > 0 else "national" if national[c] > 0 else "newcomer" for c in roster}
    assert {c: v["kind"] for c, v in b["city_limits"].items()} == kind
    assert {c: v["kind"] for c, v in b["party_ranges"].items()} == kind
    ext, A = b["swing"]["extremes"], b["allowance"]["city"]["value"]
    def moved(x, bins):
        lo, hi = bins[bisect.bisect_left(b["swing"]["bins"], x)]
        return max(0.0, x + lo - A), min(1.0, x + hi + A)
    for c in roster:
        got = b["city_limits"][c]
        if kind[c] == "local":
            want = moved(prior_e[c], ext["city"])
        elif kind[c] == "national":
            want = moved(national[c] / nat_total, ext["npe_city"])
        else:
            want = (0.0, min(1.0, b["swing"]["newcomer"]["city"]["value"] + A))
        assert math.isclose(got["lo"], want[0], abs_tol=1e-12) and math.isclose(got["hi"], want[1], abs_tol=1e-12), c
    # constructed: one citywide swing past its bin
    panel = build_make.swing_panel(city, target)
    bins = build_make.swing_extremes(panel)
    local = build_make.ward_priors(city, target, wards)
    npe = build_make.npe_priors(city, target, wards)
    pe = collections.Counter()
    for w in wards:
        for c, v in local["h"].get(w, {}).items():
            pe[c] += b["e"][w] * v
    limits = lambda bs: build_make.city_limits(roster, pe, npe, local["city"], bs, b["allowance"], b["swing"]["newcomer"])
    assert json.loads(json.dumps(limits(bins))) == b["city_limits"]
    k = build_make._bin(pe["DA"])
    pushed = dict(panel, city_rows=panel["city_rows"] + [("ZZZ", "2021", "ZZ", pe["DA"],
                                                          pe["DA"] + bins["city"][k][1] + 0.01)])
    nb = build_make.swing_extremes(pushed)
    assert [j for j in range(len(nb["city"])) if nb["city"][j] != bins["city"][j]] == [k]
    lim = limits(nb)
    moved_parties = {c for c in roster if lim[c] != limits(bins)[c]}
    assert moved_parties == {c for c in roster if kind[c] == "local" and build_make._bin(pe[c]) == k}
    assert "DA" in moved_parties
    # constructed: a collapse from national to local, and the same swing short of one
    top = 0.5
    collapse = dict(panel, npe_city_rows=panel["npe_city_rows"]
                    + [("ZZZ", "2019", "2021", "ZZ", top, build_make.COLLAPSE_KEEP * top / 2)])
    kept = build_make.swing_extremes(collapse)
    assert kept["npe_city"] == bins["npe_city"] and ["ZZZ", "2021", "ZZ"] in [list(x) for x in kept["npe_collapses"]]
    near = top * build_make.COLLAPSE_KEEP * 1.01
    short = dict(panel, npe_city_rows=panel["npe_city_rows"] + [("ZZZ", "2019", "2021", "ZZ", top, near)])
    if near - top < bins["npe_city"][build_make._bin(top)][0]:
        assert build_make.swing_extremes(short)["npe_city"] != bins["npe_city"]
    else:
        raise AssertionError("the constructed swing does not reach past its bin; choose a larger drop")
    assert build_make.swing_extremes(panel) == bins


def test_the_allowance_is_the_mean_of_record_events():
    """SPEC-B2r2 §1-§2. ``allowance`` and ``exclusions`` are regenerated from
    the panel (equal to the served ones), each allowance is the mean of its
    events where there are at least ``MIN_RECORD_EVENTS`` and
    ``EDITOR_WIDEN_PP`` otherwise, and the events of the served panel are
    there in both scopes (ward and city). Constructed inputs, each seen and
    each quiet when reverted: a later round with a swing 3 points beyond a
    bin's record adds one event of 3 points and moves the allowance to the new
    mean; a vanished party whose ward shares correlate perfectly with one
    party's swings is a merger, and that party's event is gone; a later
    election with a lower winning share adds a ``q_win`` event; and a shape
    quantity with one event keeps ``EDITOR_WIDEN_PP`` until a second
    arrives."""
    import cityconfig
    import copy
    city = cityconfig.active()
    target = str(city.default_target)
    b = _fresh()["schema"]["x-editor-bounds"]
    panel = build_make.swing_panel(city, target)
    excl = build_make.exclusions(panel)
    allow = build_make.allowances(panel, excl)
    assert json.loads(json.dumps(excl)) == b["exclusions"]
    assert json.loads(json.dumps(allow)) == b["allowance"]
    fallback = build_make.EDITOR_WIDEN_PP / 100.0
    for scope in ("ward", "city"):
        a = allow[scope]
        assert a["events"], scope
        if len(a["events"]) >= build_make.MIN_RECORD_EVENTS:
            assert math.isclose(a["value"], math.fsum(e["exceedance"] for e in a["events"]) / len(a["events"]))
        else:
            assert a["value"] == fallback
        assert all(e["round"] < target and e["direction"] in ("up", "down") for e in a["events"])
    # a later round 3 points beyond a bin's record
    skip = {(e["metro"], e["b"], e["excludes"]) for e in excl if e["excludes"]}
    record = max(s - h for c, _a, y, _w, p, h, s in panel["ward_rows"]
                 if 0.15 < h <= 0.35 and s > 0 and (c, y, p) not in skip)
    later = dict(panel, ward_rows=panel["ward_rows"] + [("ZZZ", "2021", "2099", "1", "P", 0.25, 0.25 + record + 0.03)])
    more = build_make.allowances(later, excl)["ward"]
    new = [e for e in more["events"] if e not in allow["ward"]["events"]]
    assert len(new) == 1 and new[0]["round"] == "2099" and new[0]["direction"] == "up"
    assert math.isclose(new[0]["exceedance"], 0.03)
    assert math.isclose(more["value"], (math.fsum(e["exceedance"] for e in allow["ward"]["events"]) + 0.03)
                        / (len(allow["ward"]["events"]) + 1))
    assert build_make.allowances(panel, excl) == allow
    # a vanished party absorbed by the party that set an event
    event = next(e for e in allow["ward"]["events"] if e["direction"] == "up")
    code, a, by, _w, party, _h, _s = next(
        r for r in panel["ward_rows"] if r[2] == event["round"] and r[5] > 0 and r[6] > 0
        and build_make._bin(r[5]) == event["key"] and r[6] - r[5] == event["new"])
    absorbed = copy.deepcopy(panel)
    data = absorbed["pair_data"][(code, a, by)]
    wards = sorted(w for w in data["s"] if w in data["h"])
    swing = [data["s"][w].get(party, 0.0) - data["h"][w].get(party, 0.0) for w in wards]
    for w, x in zip(wards, swing):
        data["h"][w]["ZZ_GONE"] = x - min(swing) + 0.001
    data["Ha"]["ZZ_GONE"] = 2 * build_make.VANISH_MIN
    merged = build_make.exclusions(absorbed)
    found = [e for e in merged if e["party"] == "ZZ_GONE"]
    assert len(found) == 1 and found[0]["kind"] == "merger" and found[0]["excludes"] == party
    after = build_make.allowances(absorbed, merged)["ward"]["events"]
    key = (event["round"], event["key"], event["direction"], event["new"])
    assert key not in {(e["round"], e["key"], e["direction"], e["new"]) for e in after}
    assert build_make.exclusions(panel) == excl
    # a party new to the city drawing from the party that set the event: a
    # split, which leaves out the source's swings
    split = copy.deepcopy(panel)
    data = split["pair_data"][(code, a, by)]
    for w, x in zip(wards, swing):
        data["s"][w]["ZZ_NEW"] = max(swing) - x + 0.001
    data["Hb"]["ZZ_NEW"] = 2 * build_make.SPLIT_MIN
    found = [e for e in build_make.exclusions(split) if e["party"] == "ZZ_NEW"]
    assert len(found) == 1 and found[0]["kind"] == "split" and found[0]["excludes"] == party
    after = build_make.allowances(split, build_make.exclusions(split))["ward"]["events"]
    assert key not in {(e["round"], e["key"], e["direction"], e["new"]) for e in after}
    # the party that set the event collapsing citywide: its own swings left out
    fall = copy.deepcopy(panel)
    data = fall["pair_data"][(code, a, by)]
    data["Ha"][party] = 2 * build_make.COLLAPSE_FROM
    data["Hb"][party] = build_make.COLLAPSE_KEEP * build_make.COLLAPSE_FROM
    found = [e for e in build_make.exclusions(fall) if e["kind"] == "collapse" and e["party"] == party
             and e["b"] == by and e["metro"] == code]
    assert len(found) == 1 and found[0]["excludes"] == party
    after = build_make.allowances(fall, build_make.exclusions(fall))["ward"]["events"]
    assert key not in {(e["round"], e["key"], e["direction"], e["new"]) for e in after}
    # reverted: the real panel's events again
    assert build_make.allowances(panel, build_make.exclusions(panel)) == allow
    # the shape: a later election with a lower winning share
    per_year = b["shape"]["per_year"]
    low = min(v["q_win"]["value"] for v in per_year.values())
    later = dict(per_year, **{"2099": {**per_year[max(per_year)],
                                      "q_win": {"value": low - 0.03, "file": "constructed", "ward": "1"}}})
    got = build_make.shape_allowances(later)["q_win"]["events"]
    assert [e["round"] for e in got if e not in b["shape"]["allowance"]["q_win"]["events"]] == ["2099"]
    assert json.loads(json.dumps(build_make.shape_allowances(per_year))) == b["shape"]["allowance"]
    # one event keeps EDITOR_WIDEN_PP; a second makes it the mean
    def year(q_win):
        return {"q_win": {"value": q_win}, "q_run": {"value": 0.4},
                "gap_min": {"value": -1.0}, "gap_max": {"value": 2.0}}
    one = build_make.shape_allowances({"a": year(0.30), "b": year(0.28)})["q_win"]
    assert len(one["events"]) == 1 and one["value"] == fallback
    two = build_make.shape_allowances({"a": year(0.30), "b": year(0.28), "c": year(0.24)})["q_win"]
    assert len(two["events"]) == 2 and math.isclose(two["value"], 0.03)


def test_the_data_file_is_the_one_the_build_writes():
    site = _built()
    assert _data(site) == json.loads(json.dumps(build_make.forecast_data(), sort_keys=True))


#: Section 1 settings the hand-off is checked under: the published one, one
#: turnout move, a by-election cell and a poll believed at half. A setting the
#: engine refuses is skipped and counted, so the test says what it covered.
HANDOFF_SETTINGS = (
    ("published", PUBLISHED),
    ("black-african-plus-5", {**PUBLISHED, "shift": [5, 0, 0, 0]}),
    ("white-minus-5", {**PUBLISHED, "shift": [0, 0, 0, -5]}),
    ("by-elections-not-counted", None),         # the w_bye = 0 cell, filled below
    ("poll-at-half", None),                     # the first poll offered, filled below
)


def test_the_hand_off_is_the_published_start_untouched_and_section_1s_wards_moved():
    """Section 2 "continues the same forecast" (owner, 2026-10-03). At the
    published setting the hand-off IS the start the build writes: rule A, one
    function, unit weights (ward calls and both ballots' votes). Under every
    other setting its ward calls are exactly the ward winners section 1 shows
    for that setting, and it differs from the published start: the test can
    see a hand-off that ignored the weights. It is a prediction object (calls,
    both ballots' whole votes, nothing else), and as an entry it seats."""
    site = _built()
    d = _data(site)
    NP, ns = _engine()
    wards = d["schema"]["x-ward-ids"]
    cells = {c["w_bye"]: c["path"] for c in NP.cells()}
    poll = ns["polls"]()[0]["id"]
    settings = []
    for name, s in HANDOFF_SETTINGS:
        if name == "by-elections-not-counted":
            s = {**PUBLISHED, "cell": cells[min(cells)]}
        elif name == "poll-at-half":
            s = {**PUBLISHED, "polls": [poll], "trust": 0.5}
        settings.append((name, s))
    import score_forecasts
    roster = d["schema"]["x-seat-context"]["parties"]
    moved = 0
    for name, s in settings:
        h = json.loads(ns["handoff"](json.dumps({"settings": s})))
        assert not h.get("refused"), (name, h)
        assert "seats" not in h, "the hand-off carries no seats: they are derived"
        r = json.loads(ns["compute"](json.dumps(s)))
        assert {x["ward"]: x["winner"] for x in r["wards"]} == h["ward_calls"], name
        calls = [h["ward_calls"][w] for w in wards]
        votes = ({p: h["ward_votes"][p] for p in roster}, {p: h["list_votes"][p] for p in roster})
        assert set(h) == {"ward_calls", "ward_votes", "list_votes"}, (name, sorted(h))
        seated = score_forecasts.seat_forecast({"v": score_forecasts.entry_version(d["schema"]),
                                                "ward_calls": calls, "ward_votes": votes[0],
                                                "list_votes": votes[1]}, d["schema"])
        assert seated["ok"], (name, seated["errors"])
        if name == "published":
            assert calls == d["start"]["ward_calls"]
            assert votes == (d["start"]["ward_votes"], d["start"]["list_votes"])
        elif calls != d["start"]["ward_calls"] or votes != (d["start"]["ward_votes"], d["start"]["list_votes"]):
            moved += 1
    print(f"  {moved} of {len(settings) - 1} settings moved the hand-off from the published start")
    assert moved >= 1, "no setting moved the hand-off: the test cannot see one that ignores the weights"


def test_the_analysis_is_reweights_arithmetic_on_the_published_draws():
    """page.py ``analyse`` on a constructed forecast (the published start with
    three wards given to another party) equals ``reweight.ward_calls_likelihood``
    and ``reweight.within_band`` computed here on the published cell's draws,
    each draw counted once; its score equals the competition's three measures
    worked out here draw by draw; and it moves when the forecast does."""
    import numpy as np
    import reweight as R
    site = _built()
    d = _data(site)
    _NP, ns = _engine()
    wards = d["schema"]["x-ward-ids"]
    calls = dict(zip(wards, d["start"]["ward_calls"]))
    other = sorted(set(calls.values()))
    for w in wards[:3]:
        calls[w] = next(c for c in other if c != calls[w])
    # the reader's list-ballot percent, as make.js sends it (B.percentOf "list")
    list_total = sum(d["start"]["list_votes"].values())
    share = {c: 100.0 * v / list_total for c, v in d["start"]["list_votes"].items()}
    seats = dict(d["start"]["seats"])
    top2 = sorted(seats, key=lambda c: -seats[c])[:2]
    a = json.loads(ns["analyse"](json.dumps({"ward_calls": calls, "share": share, "seats": seats,
                                             "coalition": top2})))
    man = json.loads((ROOT / "site/draws/manifest.json").read_text(encoding="utf-8"))
    arr = R.unpack((ROOT / "site/draws/base.bin").read_bytes(), man)
    cols = lambda n: next(b for b in man["blocks"] if b["name"] == n)["columns"]
    codes = man["ward_parties"]
    w = R.uniform(int(man["draws"]))
    k = [codes.index(calls[x]) if calls[x] in codes else len(codes) for x in cols("ward_winner")]
    want = R.ward_calls_likelihood(arr["ward_winner"], w, len(codes) + 1, k)
    assert all(math.isclose(a["wards"][x]["p"], p, rel_tol=1e-12) for x, p in zip(cols("ward_winner"), want["p"]))
    sc, pc = cols("seats/deduct"), cols("list_vote")
    # the score, by a loop over the draws: the forecast against each draw as
    # if it were the result (JUDGEMENT-CALLS §N4), the competition's three
    # measures written out here, not called
    seat_errs, right, vote_errs = [], [], []
    seat_rows, win_rows = arr["seats/deduct"], arr["ward_winner"]
    lv = np.asarray(arr["list_vote"], dtype=float)
    pr_rows = lv / lv.sum(axis=1, keepdims=True)
    assert set(share) <= set(pc), "a reader party the list_vote block does not carry"
    mine_pts = dict(share)
    for i in range(int(man["draws"])):
        drawn = {c: int(seat_rows[i, j]) for j, c in enumerate(sc) if c != "OTHER"}
        seat_errs.append(sum(abs(seats.get(c, 0) - drawn.get(c, 0)) for c in set(seats) | set(drawn)))
        right.append(sum(codes[win_rows[i, j]] == calls[x] for j, x in enumerate(cols("ward_winner"))))
        listed = {c: 100.0 * float(pr_rows[i, j]) for j, c in enumerate(pc)}
        vote_errs.append(sum(abs(mine_pts.get(c, 0.0) - listed.get(c, 0.0)) for c in set(mine_pts) | set(listed)))
    n = len(seat_errs)
    got = a["score"]
    # the seat line, written out: each party's median seats over the draws,
    # rounded half up; that forecast's error against each draw; its median,
    # rounded down (reweight.seat_error_line, JUDGEMENT-CALLS §N4)
    middle = {c: int(np.floor(np.median(seat_rows[:, j]) + 0.5)) for j, c in enumerate(sc)}
    mid_errs = [sum(abs(middle[c] - int(seat_rows[i, j])) for j, c in enumerate(sc)) for i in range(n)]
    line = int(np.floor(np.median(mid_errs)))
    assert got["within"] == line and line > 0
    assert math.isclose(got["seat_error"], sum(seat_errs) / n, rel_tol=1e-9)
    assert math.isclose(got["seat_error_within"]["p"],
                        sum(e <= line for e in seat_errs) / n, rel_tol=1e-9)
    assert got["seat_error_within"]["text"] == R.chance_text(got["seat_error_within"]["p"])
    assert math.isclose(got["wards_called"], sum(right) / n, rel_tol=1e-9)
    assert math.isclose(got["list_vote_error"], sum(vote_errs) / n, rel_tol=1e-9)
    assert a["wards_count"] == len(cols("ward_winner"))
    # it looked: the forecast misses somewhere in every measure
    assert 0 < got["seat_error"] and 0 < got["wards_called"] < a["wards_count"] and got["list_vote_error"] > 0
    assert a["seats"], "no party analysed"
    for c, got in a["seats"].items():
        v = arr["seats/deduct"][:, sc.index(c)].astype(float)
        assert math.isclose(got["p"], R.within_band(v, w, seats.get(c, 0), R.ANALYSIS_SEAT_BAND), rel_tol=1e-12), c
        assert got["text"] == R.chance_text(got["p"])
    for c, got in a["share"].items():
        v = pr_rows[:, pc.index(c)] * 100.0
        assert math.isclose(got["p"], R.within_band(v, w, share.get(c, 0.0), R.ANALYSIS_SHARE_BAND_POINTS), rel_tol=1e-12), c
    assert (a["seat_band"], a["share_band"]) == (R.ANALYSIS_SEAT_BAND, R.ANALYSIS_SHARE_BAND_POINTS)
    # the headline: the reader's council-level outcome, read off the reader's
    # seats here, scored on the same draws by reweight.council_outcome
    held = {c: v for c, v in seats.items() if v > 0}
    most = max(held.values())
    tops = [c for c, v in held.items() if v == most]
    need = sum(held.values()) // 2 + 1
    o = a["outcome"]
    assert (o["largest"], o["majority_alone"], o["coalition"]) == (
        tops[0] if len(tops) == 1 else None, most >= need, sorted(top2))
    pc_cols = [c for c in sc if c != "OTHER"]
    want_o = R.council_outcome(arr["seats/deduct"][:, [sc.index(c) for c in pc_cols]].astype(float), pc_cols,
                               arr["council/deduct"][:, 0], w, largest=o["largest"],
                               majority_alone=o["majority_alone"], coalition=o["coalition"])
    assert math.isclose(o["p"], want_o, rel_tol=1e-12) and o["text"] == R.chance_text(o["p"])
    # the coalition part bites on the real draws: without it the chance is
    # at least as high, and a coalition of the two smallest shown parties
    # (never a majority) scores zero
    bare = json.loads(ns["analyse"](json.dumps({"ward_calls": calls, "share": share, "seats": seats})))
    assert bare["outcome"]["p"] >= o["p"] and bare["outcome"]["coalition"] == []
    small = sorted(a["seats"], key=lambda c: seats.get(c, 0))[:2]
    tiny = json.loads(ns["analyse"](json.dumps({"ward_calls": calls, "share": share, "seats": seats,
                                                "coalition": small})))
    assert tiny["outcome"]["p"] == 0.0, small
    # it moves with the forecast: the start's own calls score higher
    b = json.loads(ns["analyse"](json.dumps({"ward_calls": dict(zip(wards, d["start"]["ward_calls"])),
                                             "share": share, "seats": seats})))
    assert b["score"]["wards_called"] > a["score"]["wards_called"]
    assert np.isfinite(a["score"]["list_vote_error"])
    # a row the page shows stays while the reader edits: "keep" holds it
    gone = sorted(set(sc) - {"OTHER"} - set(a["seats"]))[0]
    kept = json.loads(ns["analyse"](json.dumps({"ward_calls": calls, "share": share, "seats": seats,
                                                "keep": [gone]})))
    assert gone in kept["seats"] and set(a["seats"]) < set(kept["seats"])



# -- Lane B (owner, 2026-10-05): stops said, every option applies or says why --

def test_every_discrete_option_applies_at_the_published_settings():
    """B2. The owner saw "not at all" and "fully" go back to "partly", and
    Germany 2015 go back to Germany 2000. The engine is not why: at the
    published turnout, no poll, every by-election cell under every seat law
    is shown, none refused and every figure within the precision ceiling.
    A discrete option is refused only by the OTHER settings (a poll or a
    turnout move that leaves the slider at its stop), and the page then
    says so beside the control (``test_a_refused_option_is_said_beside_its_control``).
    The check can see a refusal: with the ceiling at zero every option is
    refused."""
    _built()
    NP, ns = _engine()
    R = ns["R"]
    laws = ns["_CELLS"]["."]["manifest"]["laws"]
    cells = [c["path"] for c in NP.cells()]
    assert len(cells) >= 3 and len(laws) >= 4, (cells, laws)

    def shown(path, law):
        res = json.loads(ns["compute"](json.dumps({**PUBLISHED, "cell": path, "law": law})))
        return res["refused"] is None and res["within_precision"] is True

    assert all(shown(c, k) for c in cells for k in laws)
    ceiling = R.MAX_FIGURE_SE_SEATS
    try:
        R.MAX_FIGURE_SE_SEATS = 0.0
        assert not any(shown(c, k) for c in cells for k in laws)
    finally:
        R.MAX_FIGURE_SE_SEATS = ceiling


def test_a_poll_at_any_belief_is_not_refused_by_the_tilts_rounding():
    """B1. A poll at one trust step was refused "the tilt did not converge"
    (owner's test, 2026-10-05) although its turnout target, the published
    mean, lies well inside the draws: with a poll on, page.py pins turnout
    at the published mean, and the tilt's step-halving test rejected the
    exact Newton step once the dual's decrease fell below what a float
    resolves at its size (``reweight.DUAL_ROUNDING``). Every poll the page
    offers, at a spread of beliefs, now gets weights or an effective-draw
    refusal, never a convergence one, on the served draws.

    The positive control's input is CONSTRUCTED (CLAUDE.md §4, requirement
    3). It used to be the served draws themselves, and it expired when the
    served list shares became exact (whole list votes over their total,
    2026-10-08, MODEL-LOG §1.291): no poll then reproduced the failure. It is
    now the served list shares stepped to the 1e-5 resolution the draw file
    stored until then, which does reproduce it: through the same
    ``poll_weights`` and pinned ``turnout_tilt`` the page runs, with the
    rounding allowance at zero at least one poll is refused "did not
    converge", and with the shipped allowance none is."""
    _built()
    NP, ns = _engine()
    R = ns["R"]
    ids = [p["id"] for p in ns["polls"]()]
    assert ids, "the page offers no poll"
    beliefs = (0.05, 0.10, 0.25, 0.50, 1.00)

    def refusals():
        out = []
        for pid in ids:
            for t in beliefs:
                res = json.loads(ns["compute"](json.dumps({**PUBLISHED, "polls": [pid], "trust": t})))
                if res["refused"] and "did not converge" in res["refused"]:
                    out.append((pid, t))
        return out

    assert refusals() == []

    # the positive control, on constructed shares (docstring)
    import numpy as np
    man = json.loads((ROOT / "site/draws/manifest.json").read_text(encoding="utf-8"))
    arr = R.unpack((ROOT / "site/draws/base.bin").read_bytes(), man)
    cols = next(b for b in man["blocks"] if b["name"] == "list_vote")["columns"]
    step = 1e-5                                   # the retired pr_share block's storage step
    stepped = np.round(R.list_shares(arr["list_vote"]) / step) * step
    turnout = arr["pool_turnout"]
    pin = turnout.mean(axis=0)                    # page.py pins to the published mean with a poll on
    # the full register records, as page.py's poll weights receive them
    # (``polls()`` returns only the fields the page shows, without ``asof``)
    records = json.loads((ROOT / "site/draws/index.json").read_text(encoding="utf-8"))["polls"]

    def constructed_refusals():
        out = []
        for poll in records:
            for t in beliefs:
                try:
                    w = R.poll_weights(stepped, cols, poll, trust=t)
                    R.turnout_tilt(turnout, np.zeros(turnout.shape[1]), base=w / w.sum(), pin_to=pin)
                except R.Refused as exc:
                    if "did not converge" in str(exc):
                        out.append((poll["id"], t))
        return out

    assert constructed_refusals() == [], "the shipped allowance refuses the constructed shares"
    allowance = R.DUAL_ROUNDING
    try:
        R.DUAL_ROUNDING = 0.0
        assert constructed_refusals(), \
            "no convergence refusal without the allowance on the constructed shares: the test cannot see the defect"
    finally:
        R.DUAL_ROUNDING = allowance
    assert constructed_refusals() == [], "the allowance was not restored"


def test_a_refused_option_is_said_beside_its_control():
    """B1 and B2, on the built page's section 1 module: a stop is never
    silent. A slider that stops records the furthest setting it reaches
    (``limits``) and why, and shades the track past it (``pl-zone`` rects
    from ``play-state.js stopZones``); a discrete option refused at the other
    settings is recorded (``unavailable``), marked, and named with its reason
    in the line beside its control. Each reason has a reserved slot: under
    the turnout sliders and under the poll's slider (``pl-zonewhy``); the
    seat law's line; the by-election line. The old single message in the
    results column ("The greyed control stops here") is gone. A constructed
    revert of the old branch is caught."""
    site = _built()
    js = (site / ADJUST).read_text(encoding="utf-8")
    css = (site / D / "css" / "your-forecast.css").read_text(encoding="utf-8")
    play = (site / D / "css" / "play.css").read_text(encoding="utf-8")

    def silent(src: str) -> list[str]:
        out = []
        if "The greyed control stops here" in src:
            out.append("the stop is said only in the results column")
        for need in ("limits[which] = PS.withStop(", "unavailable[which] = {", "paintZone(", "refusedWords(",
                     'className: "pl-note pl-zonewhy yf-slot", id: "turnout-why"',
                     "inputs.trustwhy = R.trustwhy",
                     "say(R.lawnow, unavailable.law ? refusedWords(", "say(R.bye, unavailable.cell ? refusedWords(",
                     "PS.heldAtStop("):
            if need not in src:
                out.append(f"missing: {need}")
        return out

    assert silent(js) == []
    assert silent(js.replace("unavailable[which] = {", "lastRefused = {"))
    assert silent(js + '\nR.engine.textContent = "The greyed control stops here";\n')
    assert re.search(r"\.yf \.pl-zonewhy\.yf-slot\{[^}]*height:", css)
    assert re.search(r"\.pl-zone\{[^}]*position:absolute[^}]*pointer-events:none", play)
    assert re.search(r"\.pl-popt\.pl-unavail\{", play) and re.search(r"\.pl-seg3 button\.pl-unavail\{", play)
    # the reasons reach the reader through LIVE regions model.js is listed for
    for region in ("turnout", "trust", "trustwhy", "byelection", "lawnow"):
        assert region in S.LIVE_WRITERS[ADJUST], region


def test_refusal_lines_are_live_readable_and_revert_one_control():
    """The diff review's fixes to B1 and B2 (2026-10-05). A refused poll's
    reason sits after the belief slider's block, not in it (the block fades
    to .45 while no poll is chosen). Every reason line is a live region
    (role="status") written only when its words change, and a refused option
    is described by its line. A refusal turns into words in one function
    (whyNot). A slider that has not moved since the last figures shown
    records no stop. A refused discrete option sends back only its own
    control (play-state.js movedGroups), not every control moved since. Each
    constructed revert is caught."""
    site = _built()
    js = (site / ADJUST).read_text(encoding="utf-8")
    html = _html(site)

    def broken(src: str, page: str) -> list[str]:
        out = []
        trust = page.find('data-live="trust"')
        why = page.find('data-live="trustwhy"')
        if "inputs.trustwhy);" in src or "inputs.trustwhy = R.trustwhy" not in src or not 0 < trust < why:
            out.append("the poll's reason is inside the fading block")
        if 'id: "turnout-why", role: "status"' not in src:
            out.append("not live: the turnout line")
        for slot in ('id="trust-why" role="status"', 'id="bye-why" role="status"', 'id="law-why" role="status"'):
            if slot not in page:
                out.append(f"not live: {slot}")
        if 'control.setAttribute("aria-describedby", line)' not in src:
            out.append("a refused option is not described by its line")
        if "function say(node, text" not in src or "if (node.textContent === text) return;" not in src:
            out.append("a live line is rewritten with the same words")
        if "tooFew" in src:
            out.append("two writers for a refusal's reason")
        if "if (slider && from === to)" not in src:
            out.append("a slider that did not move records a stop")
        if "discreteSet(which, back, discreteValue(which, accepted.state))" not in src or "PS.movedGroups(" not in src:
            out.append("a refused option sends every control back")
        return out

    assert broken(js, html) == []
    assert broken(js.replace("inputs.trustwhy = R.trustwhy", "R.trust.append(inputs.trustwhy)"), html)
    assert broken(js.replace("if (node.textContent === text) return;", ""), html)
    assert broken(js + "\nconst tooFew = 1;\n", html)
    assert broken(js, html.replace('id="bye-why" role="status"', 'id="bye-why"'))
    assert broken(js.replace("if (slider && from === to)", "if (false)"), html)


def test_the_calls_to_act_are_large_buttons_where_the_owner_put_them():
    """B3, and the owner's layout notes of 2026-10-10 (large buttons in place
    of the full-width rows). "Share this forecast" is a large button at the
    end of section 1 (section 1's sheet) and at the foot of section 2, after
    the analysis and before the notes (section 2's sheet); "Analyse my
    forecast" is the same button in step 4. Each button is followed by its
    one line on what it gives, and section 2's names the map, the seats, our
    chance and the sealed link. A share box moved back into the levers'
    column is caught, and so is a button drawn the row's full width."""
    site = _built()
    html = _html(site)
    css = (site / D / "css" / "your-forecast.css").read_text(encoding="utf-8")

    def misplaced(page: str) -> list[str]:
        out = []
        at = lambda s: page.index(s) if s in page else -1
        s1, s2, notes = at('data-live="share"'), at('data-live="b-share"'), at('class="pl-notes"')
        layout_end = page.rindex('class="pl-resultscol"', 0, s1) if s1 > 0 and 'class="pl-resultscol"' in page[:s1] else -1
        if not (0 < layout_end < s1 < at('id="break"')):
            out.append("section 1's share row is not after the levers and results")
        if s1 > 0 and at('class="pl-controls"') < s1 < at('class="pl-resultscol"'):
            out.append("section 1's share row is inside the levers' column")
        if not (at('class="yf-analysis"') < s2 < notes):
            out.append("section 2's share row is not between the analysis and the notes")
        share = 'class="btn primary shareopen yf-ctabtn"'
        if page.count(share) != 2:
            out.append("not one share row in each section")
        # each row, in its own section, with its one line
        rows = (("section 1", page.find(share, s1) if s1 > 0 else -1, ("map", "council", "seats", "sealed")),
                ("section 2", page.find(share, s2) if s2 > 0 else -1, ("map", "seats", "chance", "sealed link")),
                ("step 4", at('class="btn primary yf-analyse yf-ctabtn"'), ()))
        for where, i, words in rows:
            end = page.find("</button>", i) if i >= 0 else -1
            after = page[end + len("</button>"):] if end >= 0 else ""
            m = re.match(r'\s*<p class="yf-ctanote">([^<]+)</p>', after)
            line = m.group(1) if m else ""
            if not m:
                out.append(f"no button followed by its line: {where}")
            for w in words:
                if w not in line:
                    out.append(f"{where}'s line does not name {w}")
        return out

    assert misplaced(html) == []
    row = html[html.index('<div class="pl-sharebox yf-sharebox yf-cta"'):]
    row = row[:row.index("</dialog>") + len("</dialog>\n    </div>")]
    moved = html.replace(row, "").replace('<div class="pl-controls">', '<div class="pl-controls">' + row, 1)
    assert misplaced(moved)
    assert misplaced(html.replace('<p class="yf-ctanote">', '<p class="yf-note">', 1))
    button = re.search(r"\.yf \.yf-ctabtn\{([^}]*)\}", css)
    assert button and "font:700" in button.group(1) and "width:100%" not in button.group(1), button
    # step 4 names what it holds now
    assert "Next: see how likely it is" in html and "Share it, or see how likely it is" not in html


def test_both_share_sheets_are_one_sheet_with_one_set_of_controls():
    """Amendment A (owner, 2026-10-06): one sheet, one set of options, the
    same words. Each section's <dialog> carries the same controls, by class
    and by visible words, in the same order; what differs is content only.
    A control missing from one sheet, or one worded differently, is caught."""
    html = _html(_built())

    def controls(region: str) -> list[tuple[str, str]]:
        start = html.index(f'data-live="{region}"')
        dlg = html[html.index("<dialog", start):html.index("</dialog>", start)]
        return [(re.search(r'class="([^"]+)"', m.group(1)).group(1) if 'class="' in m.group(1) else m.group(0)[:12],
                 re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(2))).strip())
                for m in re.finditer(r"<(?:button|a|input|select|option)\b([^>]*)>([^<]*)", dlg)]

    def differ(a: list, b: list) -> list:
        return [x for x in a if x not in b] + [x for x in b if x not in a] if a != b else []

    one, two = controls("share"), controls("b-share")
    assert len(one) >= 10, one
    want = {"shname", "shurl", "btn shcopy", "shimg", "btn primary shnative", "btn shwa", "btn shx", "btn shdl", "x"}
    assert want <= {c for c, _ in one}, sorted(want - {c for c, _ in one})
    assert differ(one, two) == [], differ(one, two)
    # it can see: a sheet without WhatsApp, or with Copy link worded otherwise
    assert differ([c for c in one if c[0] != "btn shwa"], two)
    assert differ([(c, "Copy") if c == "btn shcopy" else (c, w) for c, w in one], two)


def test_a_chip_pressed_keeps_its_focus():
    """B4, the diff review's fix: choosing a chip repaints the chips without
    rebuilding the ones already drawn, so a chip pressed with Enter or Space
    keeps the focus; a chip that goes hands the focus to the select. A
    paintBrush that rebuilds every chip is caught."""
    site = _built()
    js = (site / BREAK).read_text(encoding="utf-8")

    def drops(src: str) -> list[str]:
        m = re.search(r"function paintBrush\(\) \{(.*?)\n\}", src, re.S)
        if not m:
            return ["no paintBrush"]
        body, out = m.group(1), []
        if "one.brush.replaceChildren(" in body:
            out.append("every chip is rebuilt")
        if "have.get(c)" not in body:
            out.append("a chip already drawn is not kept")
        if "one.brushselect.focus()" not in src:
            out.append("a chip that goes leaves the focus nowhere")
        return out

    assert drops(js) == []
    assert drops(js.replace("let b = have.get(c);", "let b = null; one.brush.replaceChildren();"))


def test_next_scrolls_to_the_next_step_and_focuses_its_first_control():
    """B5, on the built module: every "Next" goes through one function that
    marks the step done, highlights the next, scrolls to it and focuses its
    first control (the first vote slider, the first coalition chip,
    "Analyse my forecast"), leaving a disabled control unfocused. A handler
    that only scrolls is caught."""
    site = _built()
    js = (site / BREAK).read_text(encoding="utf-8")

    def incomplete(src: str) -> list[str]:
        m = re.search(r"function goToStep\(k\) \{(.*?)\n\}", src, re.S)
        if not m:
            return ["no goToStep"]
        body = m.group(1)
        need = ("step = Math.max(step, k)", "paintSteps()", "scrollIntoView(", "FIRST[k]()", "!f.disabled",
                "f.focus({ preventScroll: true })")
        out = [n for n in need if n not in body]
        if "[one.next1, one.next2, one.next3].forEach((b, i) => b.addEventListener(\"click\", () => goToStep(i + 1)))" not in src:
            out.append("the Next buttons do not call goToStep")
        if "() => firstVote, () => one.coal.firstElementChild, () => one.analyse" not in src:
            out.append("the first controls are not the vote, the coalition and the analysis")
        return out

    assert incomplete(js) == []
    assert incomplete(js.replace("f.focus({ preventScroll: true })", ""))


def test_the_analysis_has_the_headline_your_map_and_the_citywide_part():
    """B6, on the built page: the headline names what "this outcome" is and
    says it is the citywide result only; "Ward wins" is a part titled "Your
    map" holding the reader's map (an SVG make.js shades by our chance for
    each call, with a legend), the expected count of ward calls right and a
    line on hover and tap; "Citywide vote and seats" holds the table of each
    party's seats and vote beside its chance, then the totals. The long
    explanation is the note on the outcome, not the region. Each of these
    removed is caught."""
    site = _built()
    html = _html(site)
    js = (site / BREAK).read_text(encoding="utf-8")
    region = html[html.index('data-live="b-analysis"'):html.index('class="yf-ctafoot"')]
    note = re.search(r'<li id="note-outcome">(.*?)</li>', html, re.S).group(1)

    def missing(reg: str, src: str, nt: str) -> list[str]:
        need_html = ('class="yf-outcome yf-slot"', 'class="yf-verdict yf-slot"', "citywide result only",
                     ">Ward wins<", ">Your map<", 'class="yf-amapsvg"', 'class="yf-alegend"',
                     'class="yf-expected yf-slot"', ">Citywide vote and seats<", 'class="yf-atable"',
                     'class="yf-sseats yf-slot"', 'class="yf-svote yf-slot"')
        need_js = ('"This outcome: " + outcomeWords(', "chanceSentence(a.outcome.text)",
                   "new WardMap(one.amap, geom, { byCode, readonly: true, labelFor: wardWords })",
                   "SHADE_FLOOR + (1 - SHADE_FLOOR) * a.wards[w].p", "amap.setShade(",
                   "ward calls to come true", 'one.amap.addEventListener("click"', 'one.anote.textContent = "";')
        out = [n for n in need_html if n not in reg] + [n for n in need_js if n not in src]
        if "score your forecast against each simulation" not in re.sub(r"\s+", " ", nt):
            out.append("the explanation is not in the note")
        if "simulation" in re.sub(r"<[^>]+>", " ", reg):
            out.append("the region explains with simulations (STYLE rule 10)")
        return out

    assert missing(region, js, note) == []
    assert missing(region.replace(">Your map<", ">Wards<"), js, note)
    assert missing(region, js.replace("amap.setShade(", "amap.setCalls("), note)
    assert missing(region + "<p>Of the simulations</p>", js, note)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
