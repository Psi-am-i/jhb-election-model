"""Sharing on every page (audits/2026-10-09-site-batch/SHARE-BRIEF.md): each
claim's own page (item 1) and the share button by every page's title (item 2).

Each scan-shaped test states its population and asserts it equals what was
scanned both ways, and shows its detector catches a constructed violation and
goes quiet when it is reverted (CLAUDE.md §4). The built tests share
test_og_pages' one build into a temporary directory.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urljoin

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, skip  # noqa: E402

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
        start = text.index(f'<div class="pgshare" {build_site.SHARE_MARK}>')
        if text[text.index("</h1>") + len("</h1>"):start].strip():
            faults.append(f"{rel}: the share button is not by the page title")
        box = text[start:text.index("</script>\n</div>", start) + len("</script>\n</div>")]
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
        b = keep.index("</script>\n</div>", a) + len("</script>\n</div>")
        victim.write_text(keep[:a] + keep[b:], encoding="utf-8")
        got = button_faults(out, pages)
        assert got == [f"{claim_page(claims()[0])}: carries 0 share buttons"], got
        # a button showing another page's image
        victim.write_text(re.sub(r'(<div class="preview"><img src=")[^"]*', r"\1../og.png", keep, count=1),
                          encoding="utf-8")
        assert any("the sheet shows ['../og.png']" in f for f in button_faults(out, pages))
        victim.write_text(keep, encoding="utf-8")
        assert button_faults(out, pages) == []
        # a wrong canonical, a wrong og:url, a button away from the title, a
        # wrong script: each caught, and quiet again once reverted
        rel = claim_page(claims()[0])
        here = page_url(rel)
        box = keep[a:b]
        cases = [
            (keep.replace(f'<link rel="canonical" href="{here}">', f'<link rel="canonical" href="{SITE_URL}/">', 1),
             f"{rel}: canonical or og:url is not {here}"),
            (keep.replace(f'<meta property="og:url" content="{here}">', f'<meta property="og:url" content="{SITE_URL}/">', 1),
             f"{rel}: canonical or og:url is not {here}"),
            ((keep[:a] + keep[b:]).replace("</footer>", box + "</footer>", 1),
             f"{rel}: the share button is not by the page title"),
            (keep.replace(f'js/{build_site.PAGE_SHARE_JS}"', 'js/sheet.js"', 1),
             f"{rel}: the sheet loads ['../js/sheet.js']"),
        ]
        for text, want in cases:
            assert text != keep, want
            victim.write_text(text, encoding="utf-8")
            got = button_faults(out, pages)
            assert got == [want], (want, got)
            victim.write_text(keep, encoding="utf-8")
            assert button_faults(out, pages) == [], want
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



# ---------------------------------------------------------------------------
# the sheet in a browser: Share… only where the Web Share API is, and the
# sheet inside a phone's width on a content-box page

#: Playwright, as interactive/tools/yf_jump_check.mjs finds it.
PLAYWRIGHT = os.environ.get("PLAYWRIGHT") or str(
    Path.home() / ".npm/_npx/e41f203b7505f1fb/node_modules/playwright/index.mjs")

_IN_PAGE = r"""
import { readFileSync, existsSync, statSync } from "node:fs";
import { join, extname } from "node:path";
const { chromium } = await import(process.env.PLAYWRIGHT);
const [root, path, share] = JSON.parse(process.argv[1]);
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript",
  ".png": "image/png", ".svg": "image/svg+xml", ".woff2": "font/woff2" };
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
// the site as the static-assets Worker serves it: clean addresses
await ctx.route("http://site.test/**", route => {
  let p = decodeURIComponent(new URL(route.request().url()).pathname), f = join(root, p);
  if (p.endsWith("/")) f = join(f, "index.html");
  else if (!extname(p) && existsSync(f + ".html")) f += ".html";
  if (!existsSync(f) || statSync(f).isDirectory()) return route.fulfill({ status: 404, body: "" });
  return route.fulfill({ status: 200, body: readFileSync(f), contentType: TYPES[extname(f)] || "application/octet-stream" });
});
await ctx.route(/^https?:\/\/(?!site\.test)/, route => route.abort());
await ctx.addInitScript(share ? () => { Navigator.prototype.share = async () => {}; }
                              : () => { delete Navigator.prototype.share; delete navigator.share; });
const pg = await ctx.newPage();
const errors = [];
pg.on("pageerror", e => errors.push(e.message));
await pg.goto("http://site.test" + path, { waitUntil: "load" });
await pg.waitForFunction(() => document.querySelector("[data-pgshare] .shurl"));
const seen = () => pg.evaluate(() => {
  const b = document.querySelector("[data-pgshare] .shnative");
  return { display: getComputedStyle(b).display, disabled: b.disabled };
});
const before = await seen();
await pg.click("[data-pgshare] .pgshare-open");
await pg.waitForFunction(() => document.querySelector("[data-pgshare] dialog").open);
const after = await seen();
const fit = await pg.evaluate(() => {
  const d = document.querySelector("[data-pgshare] dialog"), r = d.getBoundingClientRect();
  return { right: r.right, scroll: d.scrollWidth - d.clientWidth, sizing: getComputedStyle(d).boxSizing,
           btn: document.querySelector("[data-pgshare] .shwa").getBoundingClientRect().height,
           page: getComputedStyle(document.querySelector(".pgshare").parentElement).boxSizing };
});
await browser.close();
process.stdout.write(JSON.stringify({ before, after, fit, errors }));
"""


def in_page(out: Path, path: str, share: bool) -> dict:
    """The share button's Share… and the sheet's size at 375 wide on ``path``,
    with or without the Web Share API."""
    if not Path(PLAYWRIGHT).is_file():
        skip(f"needs Playwright ({PLAYWRIGHT}; set PLAYWRIGHT)")
    run = subprocess.run(["node", "--input-type=module", "-e", _IN_PAGE, json.dumps([str(out), path, share])],
                         capture_output=True, text=True, cwd=ROOT, env={**os.environ, "PLAYWRIGHT": PLAYWRIGHT},
                         timeout=180)
    assert run.returncode == 0, run.stderr[-2000:]
    return json.loads(run.stdout)


def sheet_faults(got: dict, share: bool) -> list[str]:
    """Share… displayed exactly when the Web Share API exists, before and
    after the sheet opens; the sheet within the 375px screen with no sideways
    scroll; its buttons sized by their border box; no script error."""
    faults = []
    for when in ("before", "after"):
        shown = got[when]["display"] != "none"
        if shown != share:
            faults.append(f"{when} opening: Share\u2026 is {'shown' if shown else 'hidden'} "
                          f"with the Web Share API {'present' if share else 'absent'}")
    f = got["fit"]
    if f["right"] > 375.5 or f["scroll"] > 0:
        faults.append(f"the sheet overflows the screen: right edge {f['right']}, sideways scroll {f['scroll']}")
    if f["btn"] > 50:
        faults.append(f"a sheet button is {f['btn']}px tall")
    faults += [f"script error: {e}" for e in got["errors"]]
    return faults


def test_share_shows_only_where_the_browser_can_share_and_the_sheet_fits_a_phone():
    out = built()
    # a claim page and an article: the forecast sheet's content-box pages
    pages = [f"/{og_pages.CLAIM_DIR}/{claims()[0]['slug']}",
             "/" + next(iter(build_site.article_meta())).removesuffix(".html")]
    for path in pages:
        absent, present = in_page(out, path, False), in_page(out, path, True)
        assert absent["fit"]["page"] == "content-box", (path, absent["fit"])   # the case that matters
        assert sheet_faults(absent, False) == [], (path, absent)
        assert sheet_faults(present, True) == [], (path, present)
    # it can see: the stylesheet without its [hidden] rule shows Share… where
    # the browser cannot share, and the detector goes quiet once it is back
    css = out / "css" / "site.css"
    keep = css.read_text(encoding="utf-8")
    rule = ".btn[hidden]{display:none;}"
    assert keep.count(rule) == 1
    try:
        css.write_text(keep.replace(rule, ""), encoding="utf-8")
        got = sheet_faults(in_page(out, pages[0], False), False)
        assert any("Share\u2026 is shown with the Web Share API absent" in g for g in got), got
    finally:
        css.write_text(keep, encoding="utf-8")
    assert sheet_faults(in_page(out, pages[0], False), False) == []


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
