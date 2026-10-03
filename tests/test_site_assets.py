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
    # /play/ and /make/), not a floor that ratchets
    import build_site as B
    expected = {spec[0] for spec in B.DOCS.values()} | set(B.ARTEFACTS) | {"portal.html"}
    expected |= {"play/index.html", "make/index.html"}
    assert expected <= set(pages), sorted(expected - set(pages))
    assert len(pages) <= len(expected) + 2, pages
    assert problems == [], problems[:5]


def test_the_templates_carry_no_inline_css_or_js():
    templates = [ROOT / "forecast-sheet.html", ROOT / "home.html",
                 ROOT / "interactive" / "model.html", ROOT / "interactive" / "make.html"]
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
    page_rules = re.findall(r"/\* ---- src/css/page-(\w+)\.css ---- \*/\n(.*?)(?=/\* ---- |\Z)", css, re.S)
    assert len(page_rules) == sum(1 for n in SA.CSS_FILES if n.startswith("page-"))
    for name, body in page_rules:
        for sel in re.findall(r"(?:^|[{}])\s*([^@{}\s][^{}]*)\{", body):
            for s in sel.split(","):
                s = s.strip()
                assert (f".pg-{name})" in s or s.startswith(":root")), (name, s)


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
