"""No inline CSS or JS on any page; one stylesheet, built from src/css/.

Owner's sweep, 2026-10-03: "HTML, CSS and JS in separate, maintainable files,
no inline CSS". `site_assets.scan_site` is the gate (build_site refuses a build,
deploy_check a deploy); this module holds it to the four-part absence rule
(CLAUDE.md §4):

0. it scanned the right thing: every page under a site, at any depth, and
   nothing else; the population is computed from the tree, not assumed;
1. it looked: the population of the real build is non-empty and within a
   two-sided bound of the pages the build produces;
2. it can see: each kind of violation, written into a constructed page, is
   caught, and the detector goes quiet when it is removed;
3. its input is constructed: the detector cases are pages this test writes.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import site_assets as SA  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

CLEAN = """<!doctype html><html><head><title>t</title>
<link rel="stylesheet" href="css/site.css">
<script src="js/theme.js"></script>
<script defer src="js/stat-tip.js"></script>
<!-- a comment may say <style> and style="x" and <script>x</script> -->
</head><body class="pg-doc"><p>Prose that mentions the style= attribute and onclick= in words.</p>
<svg class="st-svg" width="100%" height="20"><rect x="1%" width="2%" height="8"></rect></svg>
</body></html>"""

#: One constructed violation of each kind the gate names.
VIOLATIONS = {
    "a <style> element": '<style>p{color:red}</style>',
    "a style attribute": '<span style="color:red">x</span>',
    "an event-handler attribute": '<button onclick="go()">x</button>',
    "a javascript: URL": '<a href="javascript:go()">x</a>',
    "an inline <script>": '<script>go()</script>',
    "an inline <script> beside a src": '<script src="js/x.js">go()</script>',
    "a style attribute on SVG": '<svg><text style="fill:red">1</text></svg>',
}


def _site(pages: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for rel, html in pages.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")
    (root / "css").mkdir(exist_ok=True)
    (root / "css" / "site.css").write_text("p{}", encoding="utf-8")   # not a page
    return root


def test_the_scan_reads_every_page_at_every_depth_and_nothing_else():
    root = _site({"index.html": CLEAN, "play/index.html": CLEAN, "a/b/c.html": CLEAN})
    pages, problems = SA.scan_site(root)
    on_disk = sorted(f.relative_to(root).as_posix() for f in root.rglob("*")
                     if f.is_file() and f.suffix == ".html")
    assert pages == on_disk == ["a/b/c.html", "index.html", "play/index.html"]
    assert problems == []


def test_each_violation_is_caught_and_the_detector_goes_quiet_without_it():
    for what, snippet in VIOLATIONS.items():
        bad = CLEAN.replace("</body>", snippet + "</body>")
        root = _site({"index.html": CLEAN, "make/index.html": bad})
        _, problems = SA.scan_site(root)
        assert problems and all(p.startswith("make/index.html: ") for p in problems), (what, problems)
        (root / "make" / "index.html").write_text(CLEAN, encoding="utf-8")
        assert SA.scan_site(root)[1] == [], what


def test_the_built_site_carries_no_inline_css_or_js():
    site = ROOT / "site"
    pages, problems = SA.scan_site(site)
    # two-sided: the build's own pages (build_site.DOCS + ARTEFACTS + portal,
    # /your-forecast/), not a floor that ratchets
    import build_site as B
    import build_your_forecast as YF
    expected = {spec[0] for spec in B.DOCS.values()} | set(B.ARTEFACTS) | {"portal.html"}
    expected |= {YF.YF_PAGE}
    assert expected <= set(pages), sorted(expected - set(pages))
    assert len(pages) <= len(expected) + 2, pages
    assert problems == [], problems[:5]


def test_the_templates_carry_no_inline_css_or_js():
    templates = [ROOT / "forecast-sheet.html", ROOT / "home.html",
                 ROOT / "interactive" / "your-forecast.html"]
    for t in templates:
        assert SA.inline_problems(t.read_text(encoding="utf-8")) == [], t.name


def test_page_rules_are_scoped_without_changing_their_specificity():
    css = ("*{margin:0}\nbody{color:red}\n:root{--x:1}\nh2,.a > b{x:y}\n"
           "@media (max-width:5px){.c,.d{x:y}}\n@keyframes k{from{a:b}to{a:c}}")
    out = SA.scope_css(css, "pg-x")
    assert ":where(.pg-x),:where(.pg-x) *{margin:0}" in out
    assert "body:where(.pg-x){color:red}" in out
    assert ":root{--x:1}" in out
    assert ":where(.pg-x) h2,:where(.pg-x) .a > b{x:y}" in out
    assert "@media (max-width:5px){:where(.pg-x) .c,:where(.pg-x) .d{x:y}}" in out
    assert "@keyframes k{from{a:b}to{a:c}}" in out


def test_the_stylesheet_lists_every_source_file_and_scopes_every_page_file():
    on_disk = sorted(p.name for p in SA.CSS_SRC.glob("*.css"))
    assert on_disk == sorted(SA.CSS_FILES)
    css = SA.site_css()
    for name in SA.CSS_FILES:
        assert f"/* ---- src/css/{name} ---- */" in css
    page_rules = re.findall(r"/\* ---- src/css/page-([\w-]+)\.css ---- \*/\n(.*?)(?=/\* ---- |\Z)", css, re.S)
    assert len(page_rules) == sum(1 for n in SA.CSS_FILES if n.startswith("page-"))
    for name, body in page_rules:
        for sel in re.findall(r"(?:^|[{}])\s*([^@{}\s][^{}]*)\{", body):
            for s in sel.split(","):
                s = s.strip()
                assert (f".pg-{name})" in s or s.startswith(":root")), (name, s)


def test_page_type_and_the_stylesheet_scope_by_one_pattern():
    import build_site
    m = SA.PAGE_CSS.fullmatch("page-your-forecast.css")
    assert m and m.group(1) == "your-forecast"
    for bad in ("page-.css", "page--x.css", "page-X.css", "page-a_b.css"):
        assert not SA.PAGE_CSS.fullmatch(bad), bad
    for name in SA.CSS_FILES:
        if name.startswith("page-"):
            kind = SA.PAGE_CSS.fullmatch(name).group(1)
            assert build_site.page_type(kind) == f" pg-{kind}"
    assert build_site.page_type("") == ""
    assert build_site.page_type("no-such-page") == ""


def test_the_light_palette_is_written_once_and_emitted_twice():
    src = (SA.CSS_SRC / "tokens.css").read_text(encoding="utf-8")
    assert src.count("--paper:#fbfbfa") == 1
    css = SA.site_css()
    assert css.count("--paper:#fbfbfa") == 2
    assert '@media (prefers-color-scheme: light){\n  :root:not([data-theme="dark"])' in css


def test_every_party_colour_is_a_class_from_the_one_palette():
    import render_sheet
    css = SA.colour_css()
    for code, colour in render_sheet.CHIPS.items():
        assert f".pc-{code}{{--pc:{colour};}}" in css
    assert f"--pc-other:{render_sheet.OTHER_CHIP}" in css


def test_the_typefaces_are_ibm_plex_from_this_site_and_every_face_has_its_file():
    """Owner, 2026-10-03: IBM Plex Mono, Serif and Sans, self-hosted. Every
    face FONT_FACES names is declared once in site.css, from a file in
    src/fonts/ served under fonts/, with font-display swap and no font
    service anywhere in the stylesheet; the three type tokens put the Plex
    family first with system fallbacks. Both directions: a file no face names
    and a face with no file each stop the build, and go quiet when reverted."""
    css = SA.site_css()
    faces = re.findall(r'@font-face\{font-family:"(IBM Plex (?:Sans|Serif|Mono))";[^}]*'
                       r'font-display:swap;src:url\("\.\./fonts/([^"]+)"\)', css)
    named = {(fam, SA.font_file(stem, n)) for fam, stem, fs in SA.FONT_FACES for n, _, _ in fs}
    assert set(faces) == named and len(faces) == len(named)
    assert {f for _, f in faces} == {p.name for p in SA.FONT_SRC.glob("*.woff2")}
    assert (SA.FONT_SRC / "OFL.txt").read_text(encoding="utf-8").count("SIL Open Font License") >= 1
    assert not re.search(r"fonts\.(?:googleapis|gstatic)|//[a-z.]+/[^)]*\.woff", css)
    tokens = (SA.CSS_SRC / "tokens.css").read_text(encoding="utf-8")
    for var, fam, fallback in (("--serif", "IBM Plex Serif", "serif"), ("--sans", "IBM Plex Sans", "sans-serif"),
                               ("--mono", "IBM Plex Mono", "monospace")):
        m = re.search(var + r':"' + fam + r'",[^;]*\b' + fallback + ";", tokens)
        assert m, var
    # both directions of the file check
    extra = SA.FONT_SRC / "IBMPlexSans-Thin-Latin1.woff2"
    try:
        extra.write_bytes(b"x")
        try:
            SA.font_files()
            raise AssertionError("a file no face names was not caught")
        except SystemExit:
            pass
    finally:
        extra.unlink()
    SA.font_files()
    saved = SA.FONT_FACES
    try:
        SA.FONT_FACES = saved + (("IBM Plex Mono", "IBMPlexMono", (("Italic", 400, "italic"),)),)
        try:
            SA.font_files()
            raise AssertionError("a face with no file was not caught")
        except SystemExit:
            pass
    finally:
        SA.FONT_FACES = saved
    SA.font_files()


def _vector_logo_problems(name: str, group: str, parts: tuple[str, ...], muted: bool = True) -> list[str]:
    """A logo file is paths only (no raster, no live text, no <use>), one
    colour (currentColor on its outer group, so a <use> from a page inherits
    the text colour), and its one muted part, where it has one (``muted``),
    takes the page's ink-3 token rather than a colour of its own; a logo with
    none carries no style at all."""
    raw = (SA.BRAND_SRC / name).read_text(encoding="utf-8")
    out = []
    # a comment holding "--" is not XML, and a page's <use> of the file draws nothing
    if any("--" in c for c in re.findall(r"<!--(.*?)-->", raw, flags=re.S)):
        out.append(f"{name}: a comment holds a double hyphen")
    logo = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    if "<image" in logo or "data:" in logo or "<use" in logo or "<text" in logo:
        out.append(f"{name}: not paths only")
    if f'<g id="{group}" fill="currentColor"' not in logo:
        out.append(f"{name}: #{group} is not drawn in currentColor")
    out += [f"{name}: no #{p}" for p in parts if f'id="{p}"' not in logo]
    if re.search(r'fill="#|fill:#|fill="rgb|fill:rgb', logo):
        out.append(f"{name}: a colour of its own")
    styled = re.findall(r'style="([^"]*)"', logo)
    if styled != (["fill:var(--ink-3,currentColor)"] if muted else []):
        out.append(f"{name}: styles {styled}")
    return out


def test_the_logos_are_one_colour_vector_and_their_links_keep_the_names():
    """The owner's logos (2026-10-05). logo.svg, the Hillbrow Tower as the J
    of "Johannesburg" under "ELECTION FORECAST", is every city page's home
    link, named with the city and the site's address; whysoserious.svg, the
    umbrella site's, heads the portal and sits in the footer, linking to the
    apex. The favicons and the
    default share image are linked and copied; the built pages carry them."""
    assert _vector_logo_problems(SA.LOGO, "logo", ("tower", "lettering"), muted=False) == []
    assert _vector_logo_problems(SA.UMBRELLA, "wsc", ("skyline", "wsc-name", "wsc-sub")) == []
    import build_site as B
    assert B.LOGO_NAME == "Johannesburg \u2014 joburg.whysoserious.city"
    nav = B.nav_for("forecast")
    assert (f'<a class="home" href="./" aria-label="{B.LOGO_NAME}"><svg class="logo" viewBox="{SA.LOGO_VIEWBOX}"'
            in nav) and f'<use href="{SA.LOGO}#logo">' in nav
    assert (f'<a class="foot-umbrella" href="{SA.APEX_URL}" aria-label="whysoserious.city">'
            f'<svg class="wsc-logo" viewBox="{SA.UMBRELLA_VIEWBOX}"') in B.FOOTER
    assert f'<use href="{SA.UMBRELLA}#wsc">' in B.FOOTER
    head = SA.head()
    for href in ("favicon.svg", "favicon-32.png", "apple-touch-icon.png"):
        assert f'href="{href}"' in head and href in SA.BRAND_FILES
    assert "og.png" in B.OG_META and "share.jpg" not in B.OG_META
    site = ROOT / "site"
    for name in SA.BRAND_FILES:
        assert (site / name).read_bytes() == (SA.BRAND_SRC / name).read_bytes(), name
    for page in ("index.html", "forecast.html", "your-forecast/index.html"):
        html = (site / page).read_text(encoding="utf-8")
        assert f'aria-label="{B.LOGO_NAME}"' in html and "logo.svg#logo" in html, page
        assert "whysoserious.svg#wsc" in html, page
    portal = (site / "portal.html").read_text(encoding="utf-8")
    assert re.search(r'<header class="pmast">\s*<a class="pm-logo" href="./" aria-label="[^"]+">'
                     r'<svg class="wsc-logo"', portal)


def test_the_logo_check_fires_on_each_constructed_violation():
    saved = SA.BRAND_SRC
    with tempfile.TemporaryDirectory() as d:
        try:
            SA.BRAND_SRC = Path(d)
            good = (saved / SA.LOGO).read_text(encoding="utf-8")
            for old, new in (('<g id="logo" fill="currentColor"', '<g id="logo" fill="#000"'),
                             ('id="tower"', 'id="towr"'),
                             ('<g id="lettering"', '<image href="data:x"/><g id="lettering"'),
                             ('<g id="lettering">', '<g id="lettering" style="fill:#939393">'),
                             ("<!-- ", "<!-- --x ")):
                assert good.count(old) == 1, old
                (Path(d) / SA.LOGO).write_text(good.replace(old, new, 1), encoding="utf-8")
                assert _vector_logo_problems(SA.LOGO, "logo", ("tower", "lettering"), muted=False), new
            (Path(d) / SA.LOGO).write_text(good, encoding="utf-8")
            assert _vector_logo_problems(SA.LOGO, "logo", ("tower", "lettering"), muted=False) == []
        finally:
            SA.BRAND_SRC = saved


