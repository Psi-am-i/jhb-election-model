"""/play/ ("play with the model") goes through the number gate like every page.

SPEC-v2 decision 1 (owner, 2026-09-30): the untouched page is ledgered
tokens; a figure computed from a reader's settings appears only inside a LIVE
region (``data-live``), which holds no build-time digit, and only a module in
``stats.LIVE_WRITERS`` may write one. INTEGRATION §3c's done-when: the build
stamps ``blocking=0`` with the page included.

These tests build the real site into a temporary directory (never ``site/``)
and hold the BUILT page to that, then show each guard fires on a constructed
violation and goes quiet when it is reverted (CLAUDE.md §4):

* the page is in the review stamp, blocks nothing, and ``deploy_check`` passes
  on the build;
* its first paint is token spans (the published forecast, ledgered), and its
  LIVE regions are exactly the ones its writer is listed for, both directions;
* a figure written outside a LIVE region, by the listed writer or by a module
  that is not listed, is refused, on the built files and by the build itself;
* a digit typed into a LIVE region at build time blocks the stamp.
"""
from __future__ import annotations

import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import run_module, skip  # noqa: E402

import build_play  # noqa: E402
import build_site  # noqa: E402
import deploy_check  # noqa: E402
import stats as S  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WRITER = "play/js/model.js"
SHARE = "play/js/play-share.js"
#: The page's writers: the page, its share sheet, and the share image.
PLAY_WRITERS = (WRITER, SHARE, "play/js/play-card.js")
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
    if "site" not in _BUILT:
        tmp = Path(tempfile.mkdtemp(prefix="play-page-"))
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
    page = site / build_play.PLAY_PAGE
    return S.script_writes(page.read_text(encoding="utf-8"), page=page, root=site,
                           writers=S.LIVE_WRITERS if writers is None else writers)


def test_the_built_play_page_is_stamped_and_blocks_nothing():
    site = _built()
    pages, blocking = _stamp(site)
    assert build_play.PLAY_PAGE in pages, sorted(pages)
    assert blocking == 0
    # the page's own section of the review: it was looked at (it carries the
    # published forecast's panels, so its scan is far from empty) and none of
    # its rows blocks
    review = (site.parent / "NUMBERS-REVIEW.md").read_text(encoding="utf-8")
    section = re.search(rf"^## {re.escape(build_play.PLAY_PAGE)} — (.*?)$(.*?)(?=^## |\Z)", review, re.S | re.M)
    assert section, "the review has no section for the play page"
    assert sum(int(n) for n in re.findall(r"(\d+) \w+", section.group(1))) > 100, section.group(1)
    assert "| BLOCKS |" not in section.group(2)
    # and the rule the build applied is the one in stats: a raw scan of the
    # page finds nothing blocking inside a LIVE region
    hits = S.scan_numbers((site / build_play.PLAY_PAGE).read_text(encoding="utf-8"))
    assert [h for h in hits if h["region"].startswith("live:") and S.is_blocking(h)] == []
    # deploy_check sees every page of this build, the nested one included
    assert deploy_check.check("joburg", site, preview=False,
                              review=site.parent / "NUMBERS-REVIEW.md") == []


def test_first_paint_is_tokens_and_the_live_regions_are_the_listed_ones():
    site = _built()
    html = (site / build_play.PLAY_PAGE).read_text(encoding="utf-8")
    assert "js/published.js" not in html and not (site / "play/js/published.js").exists()
    # the published figures are rendered token spans, in both published hosts
    hosts = html.split('<template shadowrootmode="open">')[1:]
    assert len(hosts) == 2
    for host in hosts:
        assert host.count('class="mstat"') >= 5, host[:300]
    # every LIVE region on the page is one the writer is listed for, and every
    # listed region is on the page (both directions)
    on_page = {name for _, _, name in S._live_scan(html)[0]}
    listed = set().union(*(S.LIVE_WRITERS[w] for w in PLAY_WRITERS))
    assert on_page == listed, (on_page ^ listed)
    # each region has exactly one writer
    assert sum(len(S.LIVE_WRITERS[w]) for w in PLAY_WRITERS) == len(listed)
    # every writer listed for this page ships with it, and nothing else under play/js is one
    assert {w for w in S.LIVE_WRITERS if w.startswith("play/")} == set(PLAY_WRITERS)
    for w in PLAY_WRITERS:
        assert (site / w).is_file(), w
    # each figure region carries its visible label; none is hidden at build time
    for name in on_page - {"engine", "law", "actions"}:
        assert re.search(rf'data-live="{name}"[^>]*>(?:(?!data-live=).)*?[Cc]omputed in your browser',
                         html, re.S), name
    # the Worker was pointed at the served draws, and at nothing else
    worker = (site / "play/js/model-worker.js").read_text(encoding="utf-8")
    assert build_play.DRAWS_LINE[1] in worker and build_play.DRAWS_LINE[0] not in worker


def test_the_page_scripts_pass_and_the_check_reaches_the_writer():
    site = _built()
    assert _writes(site) == []
    # it looked: unlisted, the writer is refused for what a writer does
    found = _writes(site, writers={})
    assert any(w.startswith(f"{WRITER}: a data source") for w in found), found
    # and its import, play-state.js, was read as a non-writer
    state = site / "play/js/play-state.js"
    body = state.read_text(encoding="utf-8")
    try:
        state.write_text(body + "\nexport const rows = [1, 2];\n", encoding="utf-8")
        assert any(w.startswith("play/js/play-state.js: a data block") for w in _writes(site))
    finally:
        state.write_text(body, encoding="utf-8")
    assert _writes(site) == []


def test_a_figure_outside_a_live_region_is_refused_and_the_refusal_reverts():
    site = _built()
    writer = site / WRITER
    body = writer.read_text(encoding="utf-8")
    cases = (
        # the listed writer, writing into the published seats panel
        ("document.querySelector('.pubseats').textContent = String(r.draws);\n",
         "a lookup that is not a LIVE selector"),
        # the listed writer, into a LIVE region it is not listed for
        ("document.querySelector('[data-live=\"headline\"]').textContent = '1';\n",
         "a LIVE region it is not listed for"),
        # the listed writer, by markup
        ("R.seats.innerHTML = '<td>1</td>';\n", "HTML injection"),
    )
    try:
        for line, what in cases:
            writer.write_text(body + line, encoding="utf-8")
            found = _writes(site)
            assert any(what in w for w in found), (line, found)
            writer.write_text(body, encoding="utf-8")
            assert _writes(site) == [], line
        # the share sheet, writing into the seat table it is not listed for,
        # and the share image, which is listed for no region at all
        for f, line in ((SHARE, "document.querySelector('[data-live=\"seats\"] table').textContent = '1';\n"),
                        ("play/js/play-card.js", "document.querySelector('[data-live=\"share\"] img').alt = '1';\n")):
            mod = site / f
            kept = mod.read_text(encoding="utf-8")
            mod.write_text(kept + line, encoding="utf-8")
            found = _writes(site)
            assert any(w.startswith(f"{f} (LIVE writer): a LIVE region it is not listed for") for w in found), (f, found)
            mod.write_text(kept, encoding="utf-8")
            assert _writes(site) == [], f
        # a module that is NOT listed, imported by the writer, writing a figure
        extra = site / "play/js/extra.js"
        extra.write_text("export function show(n) {\n"
                         "  document.querySelector('[data-live=\"seats\"]').textContent = `${n} seats`;\n}\n",
                         encoding="utf-8")
        writer.write_text('import { show } from "./extra.js";\n' + body, encoding="utf-8")
        found = _writes(site)
        assert any(w.startswith("play/js/extra.js: template interpolation") for w in found), found
    finally:
        writer.write_text(body, encoding="utf-8")
        (site / "play/js/extra.js").unlink(missing_ok=True)
    assert _writes(site) == []


def test_the_build_itself_blocks_an_unlisted_writer_and_a_typed_live_digit():
    _built()      # skips, loudly, where the site cannot be built
    real_writers, real_assemble = dict(S.LIVE_WRITERS), build_play.assemble
    with tempfile.TemporaryDirectory() as t:
        # 1. the page's writer, unlisted: the build refuses outright
        S.LIVE_WRITERS.clear()
        try:
            (Path(t) / "a").mkdir()
            code, log = _build(Path(t) / "a")
        finally:
            S.LIVE_WRITERS.update(real_writers)
        assert code not in (0, None) and "PAGE SCRIPT WRITES FIGURES" in log, log[-2000:]
        assert f"play/index.html: {WRITER}: a data source" in log

        # 2. a digit typed into a LIVE region at build time: the stamp blocks
        def typed(**kw):
            html = real_assemble(**kw)
            marker = '<p class="stubnote seatsempty">'
            assert html.count(marker) == 1
            return html.replace(marker, marker + "The DA wins 71 seats. ")
        build_play.assemble = typed
        try:
            (Path(t) / "b").mkdir()
            code, log = _build(Path(t) / "b")
        finally:
            build_play.assemble = real_assemble
        assert code in (0, None), log[-2000:]
        pages, blocking = _stamp(Path(t) / "b")
        assert blocking >= 1 and build_play.PLAY_PAGE in pages
        review = (Path(t) / "NUMBERS-REVIEW.md").read_text(encoding="utf-8")
        assert re.search(r"\| BLOCKS \| num \| live:seats \| `71` \|", review), review[:2000]

        # 3. reverted, the same build is quiet again
        (Path(t) / "c").mkdir()
        code, log = _build(Path(t) / "c")
        assert code in (0, None), log[-2000:]
        assert _stamp(Path(t) / "c")[1] == 0


def test_the_default_build_writes_the_play_page_links_it_and_gives_it_its_own_card():
    """/play/ is in every Johannesburg build (its draws ship since 2026-10-01),
    so one build command makes the whole site. Every page's nav links to it,
    and its share card is its own and carries no figure."""
    site = _built()
    assert (site / build_play.PLAY_PAGE).is_file(), "the default build wrote no /play/"
    assert not (ROOT / "site" / ".assetsignore").exists() or \
        "draws/" not in (ROOT / "site" / ".assetsignore").read_text(encoding="utf-8"), \
        "the draws are still excluded from the upload, so /play/ would ship without them"
    # the nav: every page links to /play/, the play page one level down
    # the portal is the apex site's page, with no city nav
    pages = sorted(p for p in site.glob("*.html") if p.name != "portal.html")
    assert len(pages) >= 5, pages
    for page in pages:
        assert 'href="play/">play with the model</a>' in page.read_text(encoding="utf-8"), page.name
    play = (site / build_play.PLAY_PAGE).read_text(encoding="utf-8")
    assert 'class="active" href="../play/">play with the model</a>' in play
    # its own card: title, description and url, and no digit in either text
    og = dict(re.findall(r'<meta property="og:(title|description|url)" content="([^"]*)"', play))
    assert og["title"] == build_play.OG_TITLE and og["url"].endswith("/play/"), og
    from html import unescape
    assert not re.search(r"\d", unescape(og["title"] + og["description"])), og
    assert play.count('property="og:image"') == 1


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
