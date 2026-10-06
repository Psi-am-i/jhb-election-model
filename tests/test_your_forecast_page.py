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
* section 2's start is the published ward calls and panel middles
  (``start_rule``, through ``build_make``), and the hand-off from section 1
  is the same rule on the reader's weights: at the published setting it IS
  the published start, and under any setting its ward calls are the ward
  winners section 1 shows;
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
    # listed region is on the page, and each region has one writer
    on_page = [name for _, _, name in S._live_scan(html)[0]]
    listed = set().union(*(S.LIVE_WRITERS[w] for w in WRITERS))
    assert set(on_page) == listed, (set(on_page) ^ listed)
    assert len(on_page) == len(set(on_page)), sorted(on_page)
    assert sum(len(S.LIVE_WRITERS[w]) for w in WRITERS) == len(listed)
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

def test_the_start_is_the_published_ward_calls_and_the_panel_middles():
    site = _built()
    d = _data(site)
    schema, start = d["schema"], d["start"]
    wards = schema["x-ward-ids"]
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
    man = json.loads((ROOT / "site/draws/manifest.json").read_text(encoding="utf-8"))
    assert d["model_ref"] == man["published_run"]["model_run_id"]
    assert schema["x-seat-context"]["parties"] == man["parties"]
    assert isinstance(schema["x-total-votes"], int) and schema["x-total-votes"] > 0
    assert math.isclose(math.fsum(start["combined_share"].values()), 100.0, abs_tol=1e-9)
    # the middles the start aims at are the forecast page's own
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
    held = {}
    for c in start["ward_calls"]:
        held[c] = held.get(c, 0) + 1
    others = sum(n for p, n in got.items() if p not in named)
    off = {}
    for g, mid in page.items():
        if g == "OTHERS":
            continue
        n = got.get(g, 0)
        assert n == max(mid, held.get(g, 0)), (g, n, mid, held.get(g, 0))
        off[g] = n - mid
    assert others == seated["council"] - sum(got.get(g, 0) for g in named)
    assert others >= sum(v for p, v in held.items() if p not in named)
    off["OTHERS"] = others - page["OTHERS"]
    print(f"  untouched section 2 against the published middles: {off}")


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
    published setting the hand-off IS the start the build writes (ward calls,
    shares, seats: one rule, ``start_rule``, unit weights). Under every other
    setting its ward calls are exactly the ward winners section 1 shows for
    that setting, its shares seat the targets ``start_rule`` sets on the
    weighted draws, and they differ from the published start: the test can
    see a hand-off that ignored the weights."""
    site = _built()
    d = _data(site)
    NP, ns = _engine()
    T, wards = d["schema"]["x-total-votes"], d["schema"]["x-ward-ids"]
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
    moved = 0
    for name, s in settings:
        h = json.loads(ns["handoff"](json.dumps({"settings": s, "total": T})))
        assert not h.get("refused"), (name, h)
        r = json.loads(ns["compute"](json.dumps(s)))
        assert {x["ward"]: x["winner"] for x in r["wards"]} == h["ward_calls"], name
        calls = [h["ward_calls"][w] for w in wards]
        assert math.isclose(math.fsum(h["share"].values()), 100.0, abs_tol=1e-9), name
        seated = score_forecasts.seat_forecast({"ward_calls": calls, "combined_share": h["share"]}, d["schema"])
        assert seated["ok"], (name, seated["errors"])
        assert {p: v["total"] for p, v in seated["seats"].items()} == h["seats"], name
        if name == "published":
            assert calls == d["start"]["ward_calls"]
            assert h["seats"] == d["start"]["seats"]
            assert all(math.isclose(h["share"][p], v, abs_tol=1e-12) for p, v in d["start"]["combined_share"].items())
        elif calls != d["start"]["ward_calls"] or h["seats"] != d["start"]["seats"]:
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
    share = dict(d["start"]["combined_share"])
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
    sc, pc = cols("seats/deduct"), cols("pr_share")
    # the score, by a loop over the draws: the forecast against each draw as
    # if it were the result (JUDGEMENT-CALLS §N4), the competition's three
    # measures written out here, not called
    seat_errs, right, vote_errs = [], [], []
    seat_rows, pr_rows, win_rows = arr["seats/deduct"], arr["pr_share"], arr["ward_winner"]
    named = set(pc) - {"OTHER"}
    mine_pts = {c: v for c, v in share.items() if c in named}
    mine_pts["OTHER"] = sum(v for c, v in share.items() if c not in named)
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
        v = arr["pr_share"][:, pc.index(c)] * 100.0
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
    refusal, never a convergence one. With the rounding allowance at zero
    the old refusal comes back for at least one of them (the positive
    control)."""
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
    allowance = R.DUAL_ROUNDING
    try:
        R.DUAL_ROUNDING = 0.0
        assert refusals(), "no convergence refusal without the allowance: the test cannot see the defect"
    finally:
        R.DUAL_ROUNDING = allowance


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


def test_the_calls_to_act_are_full_width_rows_where_the_owner_put_them():
    """B3. "Share this forecast" is a full-width row at the end of section 1
    (section 1's sheet) and at the foot of section 2, after the analysis and
    before the notes (section 2's sheet); "Analyse my forecast" is the same
    bold row in step 4. Each button carries its one line on what it gives,
    and section 2's names the map, the seats, our chance and the sealed link.
    A share box moved back into the levers' column is caught."""
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
        for sel in ('class="btn primary shareopen yf-ctabtn"', 'class="btn primary yf-analyse yf-ctabtn"'):
            i = at(sel)
            if i < 0 or "<small>" not in page[i:page.index("</button>", i)]:
                out.append(f"no full-width row with its line: {sel}")
        if page.count('class="btn primary shareopen yf-ctabtn"') != 2:
            out.append("not one share row in each section")
        i = page.find('class="btn primary shareopen yf-ctabtn"', s2) if s2 > 0 else -1
        line = page[i:page.index("</button>", i)] if i >= 0 else ""
        for w in ("map", "seats", "chance", "sealed link"):
            if w not in line:
                out.append(f"section 2's line does not name {w}")
        return out

    assert misplaced(html) == []
    row = html[html.index('<div class="pl-sharebox yf-sharebox yf-cta"'):]
    row = row[:row.index("</dialog>") + len("</dialog>\n    </div>")]
    moved = html.replace(row, "").replace('<div class="pl-controls">', '<div class="pl-controls">' + row, 1)
    assert misplaced(moved)
    assert re.search(r"\.yf \.yf-ctabtn\{[^}]*display:block;width:100%", css)
    # step 4 names what it holds now
    assert "Next: see how likely it is" in html and "Share it, or see how likely it is" not in html


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
