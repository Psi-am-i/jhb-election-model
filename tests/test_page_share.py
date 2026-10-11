"""Sharing on every page (audits/2026-10-09-site-batch/SHARE-BRIEF.md): each
claim's own page (item 1) and the share button by every page's title (item 2).

Each scan-shaped test states its population and asserts it equals what was
scanned both ways, and shows its detector catches a constructed violation and
goes quiet when it is reverted (CLAUDE.md §4). The built tests share
test_og_pages' one build into a temporary directory.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import build_site  # noqa: E402
import og_pages  # noqa: E402
from test_og_pages import SITE_URL, built, meta  # noqa: E402

import build_your_forecast as yf  # noqa: E402


def claims() -> list[dict]:
    return build_site.load_claims("joburg")


def claim_page(c: dict) -> str:
    return f"{og_pages.CLAIM_DIR}/{c['slug']}.html"


def share_pages() -> set[str]:
    """Every page that must carry the share button, from the build's own
    tables: the documents, the artefact pages, each claim's page, and the
    leaderboard once published. Not "Your forecast" (its own two sheets) and
    not the apex portal (not Johannesburg's)."""
    import build_leaderboard as lb
    pages = {spec[0] for spec in build_site.DOCS.values()} | set(build_site.ARTEFACTS)
    pages |= {claim_page(c) for c in claims()}
    if lb.published("joburg"):
        pages.add(lb.LB_PAGE)
    return pages


#: The pages that carry none, and why: their own sheets, or not this city's.
NO_BUTTON = {yf.YF_PAGE, "portal.html"}


def page_url(page: str) -> str:
    """The address a page is served at, as its canonical link names it."""
    if page == "index.html":
        return SITE_URL + "/"
    if page.endswith("/index.html"):
        return f"{SITE_URL}/{page.removesuffix('index.html')}"
    return f"{SITE_URL}/{page.removesuffix('.html')}"


def button_faults(out: Path, pages: set[str]) -> list[str]:
    """Each page in ``pages`` carries exactly one share button, right after
    its one </h1>; its preview is the page's own og:image (resolved from where
    the page is served); its script is js/page-share.js and is there; and the
    page's canonical address and og:url are its own. Every other page under
    ``out`` carries none."""
    faults = []
    for f in sorted(out.rglob("*.html")):
        rel = f.relative_to(out).as_posix()
        text = f.read_text(encoding="utf-8")
        n = text.count(build_site.SHARE_MARK)
        if rel not in pages:
            if n:
                faults.append(f"{rel}: carries {n} share button(s) and should carry none")
            continue
        if n != 1:
            faults.append(f"{rel}: carries {n} share buttons")
            continue
        here = page_url(rel)
        if re.findall(r'<link rel="canonical" href="([^"]*)">', text) != [here] or meta(text, "og:url") != [here]:
            faults.append(f"{rel}: canonical or og:url is not {here}")
        og = meta(text, "og:image")
        part = text[text.index("</h1>") + len("</h1>"):]
        if not part.lstrip().startswith(f'<div class="pgshare" {build_site.SHARE_MARK}>'):
            faults.append(f"{rel}: the share button is not by the page title")
        box = part[:part.index("</div>\n", part.index("</dialog>")) + 6]
        img = re.findall(r'<div class="preview"><img src="([^"]*)"', box)
        if len(og) != 1 or len(img) != 1 or urljoin(here, img[0]) != og[0]:
            faults.append(f"{rel}: the sheet shows {img}, the page's og:image is {og}")
        elif not (out / og[0][len(SITE_URL) + 1:]).is_file():
            faults.append(f"{rel}: its share image {og[0]} is not in the build")
        js = re.findall(r'<script type="module" src="([^"]*)"></script>', box)
        if len(js) != 1 or urljoin(here, js[0]) != f"{SITE_URL}/js/{build_site.PAGE_SHARE_JS}":
            faults.append(f"{rel}: the sheet loads {js}")
    return faults


# ---------------------------------------------------------------------------
# item 2: a share button on every page


def test_every_page_carries_one_share_button_wired_to_its_own_image_and_address():
    out = built()
    pages = share_pages()
    scanned = {f.relative_to(out).as_posix() for f in out.rglob("*.html")}
    # the population is the page set, both ways: every page the tables name
    # is in the build, and every page in the build is named or excepted
    assert pages <= scanned, pages - scanned
    assert scanned - pages == NO_BUTTON & scanned, scanned - pages
    assert yf.YF_PAGE in scanned
    # two-sided: the documents, the artefacts and the claims, no more
    assert len(build_site.ARTEFACTS) + len(claims()) <= len(pages) <= len(scanned)
    assert len(claims()) >= 1
    assert button_faults(out, pages) == []
    # "Your forecast" keeps its own two sheets
    yf_text = (out / yf.YF_PAGE).read_text(encoding="utf-8")
    assert yf_text.count('<dialog class="sharesheet"') == 2


def test_a_missing_or_miswired_button_is_caught():
    out = built()
    pages = share_pages()
    victim = out / claim_page(claims()[0])
    keep = victim.read_text(encoding="utf-8")
    try:
        # a page with no button
        a = keep.index('<div class="pgshare"')
        b = keep.index("</div>\n", keep.index("</dialog>", a)) + 6
        victim.write_text(keep[:a] + keep[b:], encoding="utf-8")
        got = button_faults(out, pages)
        assert got == [f"{claim_page(claims()[0])}: carries 0 share buttons"], got
        # a button showing another page's image
        victim.write_text(re.sub(r'(<div class="preview"><img src=")[^"]*', r"\1../og.png", keep, count=1),
                          encoding="utf-8")
        assert any("the sheet shows ['../og.png']" in f for f in button_faults(out, pages))
        victim.write_text(keep, encoding="utf-8")
        assert button_faults(out, pages) == []
        # a button on "Your forecast", which keeps its own sheets
        yf_page = out / yf.YF_PAGE
        yf_keep = yf_page.read_text(encoding="utf-8")
        try:
            yf_page.write_text(yf_keep.replace("</body>", f"<div {build_site.SHARE_MARK}></div></body>", 1),
                               encoding="utf-8")
            assert button_faults(out, pages) == [f"{yf.YF_PAGE}: carries 1 share button(s) and should carry none"]
        finally:
            yf_page.write_text(yf_keep, encoding="utf-8")
    finally:
        victim.write_text(keep, encoding="utf-8")
    assert button_faults(out, pages) == []


def test_share_button_refuses_a_page_it_cannot_place_or_wire():
    head = f'<meta property="og:image" content="{SITE_URL}/og.png">'
    ok = build_site.share_button(head + "<h1>T</h1><p>x</p>")
    assert ok.count(build_site.SHARE_MARK) == 1 and 'src="og.png"' in ok
    assert 'src="../og.png"' in build_site.share_button(head + "<h1>T</h1>", "../")
    for bad in (head + "<h1>A</h1><h1>B</h1>", head + "<p>no title</p>", "<h1>T</h1>",
                '<meta property="og:image" content="https://elsewhere.example/x.png"><h1>T</h1>', ok):
        try:
            build_site.share_button(bad)
        except SystemExit:
            continue
        raise AssertionError(f"share_button placed a button on {bad[:80]!r}")


# ---------------------------------------------------------------------------
# item 1: one claim, one page, one image


def test_each_claim_has_its_own_page_image_and_link_back():
    out = built()
    cs = claims()
    on_disk = {f.relative_to(out).as_posix() for f in (out / og_pages.CLAIM_DIR).glob("*.html")}
    assert on_disk == {claim_page(c) for c in cs}, on_disk ^ {claim_page(c) for c in cs}
    listing = (out / "claims.html").read_text(encoding="utf-8")
    images = set()
    for c in cs:
        text = (out / claim_page(c)).read_text(encoding="utf-8")
        # its own card, and only it
        assert text.count('<article class="claim ') == 1, c["slug"]
        assert f'data-party="{c["party"]}"' in text
        assert " ".join(c["quote"].split()) in " ".join(text.split())
        # its own image
        og = meta(text, "og:image")
        assert len(og) == 1 and re.fullmatch(
            rf"{re.escape(SITE_URL)}/{og_pages.OG_DIR}/{og_pages.claim_image_slug(c['slug'])}-[a-p]{{12}}\.png", og[0]), og
        images.add(og[0])
        # a link back to all claims, and the claims page's link to it
        assert f'href="../claims">{build_site.CLAIM_BACK}</a>' in text
        assert f'href="{og_pages.CLAIM_DIR}/{c["slug"]}">{build_site.CLAIM_LINK}</a>' in listing
    assert len(images) == len(cs)
    assert listing.count(build_site.CLAIM_LINK) == len(cs)


def test_a_card_that_does_not_match_its_claim_is_refused():
    page = ('<header class="masthead" id="claims"><h1>C</h1></header><section class="claimlist">'
            '<article class="claim pc-DA" data-party="DA"><div class="pubdate">1 May: Published</div>'
            '<span class="verdict v-false">FALSE</span><blockquote class="claim-quote">Q one'
            '<span class="q-close">x</span></blockquote></article></section>')
    c = {"slug": "one", "party": "DA", "verdict": "FALSE", "quote": "Q one", "label": "L", "captured": "2026-05-01"}
    linked = build_site.link_claims(page, [c])
    assert 'id="one"' in linked and f'href="claims/one">{build_site.CLAIM_LINK}</a>' in linked
    for wrong in ({**c, "party": "ANC"}, {**c, "verdict": "TRUE"}, {**c, "quote": "Q two"}):
        try:
            build_site.link_claims(page, [wrong])
        except SystemExit:
            continue
        raise AssertionError(f"a card was matched to {wrong}")
    try:
        build_site.link_claims(page, [c, {**c, "slug": "two"}])
    except SystemExit:
        pass
    else:
        raise AssertionError("one card was matched to two claims")


def test_a_claim_slug_must_be_words_and_unique():
    for bad in ("Da-Claim", "da-490k", "da--x", "", None):
        assert not (isinstance(bad, str) and build_site.CLAIM_SLUG.fullmatch(bad)), bad
    assert build_site.CLAIM_SLUG.fullmatch("da-outright-majority")
    assert len({c["slug"] for c in claims()}) == len(claims())


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
