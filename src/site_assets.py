"""The site's one stylesheet and its scripts, and the gate that keeps them out
of the pages.

Owner's sweep, 2026-10-03: "HTML, CSS and JS in separate, maintainable files,
no inline CSS, no repeated elements." Until then every page carried its own
<style> blocks (the palette, the nav, the token styling, and each template's
own sheet) and inline <script>s (the theme, the tooltips, the coalition
filter), and the generators wrote `style="…"` into every chip, bar and label.

What this module owns
=====================

``site/css/site.css``
    Built from ``src/css/`` in :data:`CSS_FILES` order, plus one generated
    block (:func:`colour_css`): a class per party colour (``pc-<code>``, from
    ``render_sheet.CHIPS``) and per city accent (``city-<slug>``, from
    ``cities/*.toml``). A ``page-<name>.css`` file holds one kind of page's
    own rules; :func:`scope_css` confines them to pages whose <body> carries
    the class ``pg-<name>``, at the specificity they were written with
    (``:where``), so the pages share one file without their rules meeting.
``site/fonts/``
    The site's typefaces, IBM Plex Sans, Serif and Mono, byte copies of
    ``src/fonts/`` with their licence; :func:`font_css` declares them at the
    head of ``site.css``.
``site/logo.svg``, ``whysoserious.svg``, ``favicon.svg``, ``favicon-32.png``, ``apple-touch-icon.png``, ``og.png``
    The owner's logo and what is made from it (:data:`BRAND_FILES`), byte
    copies of ``src/brand/``.
``site/js/``
    The site's scripts, byte copies of ``src/js/*.js``: the theme (in <head>,
    before first paint), the provenance pop-over, the maps, the forecast
    sheet's filter and the hash forwarder. Each is scanned by
    ``stats.script_writes`` like any other script a page loads.

All three directories are written whole by every build (:func:`write`), so nothing
under them survives that the build did not write.

The gate
========

:func:`inline_problems` lists every inline ``<style>``, ``style=`` attribute,
inline ``<script>`` and ``on…=`` handler in a page. ``build_site`` refuses a
build that ships one and ``deploy_check`` refuses a deploy.
"""
from __future__ import annotations

import re
import shutil
import tomllib
from html import escape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CSS_SRC = REPO_ROOT / "src" / "css"
JS_SRC = REPO_ROOT / "src" / "js"
FONT_SRC = REPO_ROOT / "src" / "fonts"

#: Where the stylesheet, the scripts and the typefaces are served, relative
#: to the site root. fonts.css names the faces relative to the stylesheet.
CSS_PATH = "css/site.css"
JS_DIR = "js"
FONT_DIR = "fonts"
BRAND_SRC = REPO_ROOT / "src" / "brand"
#: The owner's logos, served at the site root. ``logo.svg`` (2026-10-05,
#: his "joburglogo.svg", replacing the 2026-10-03 one and the first of
#: 2026-10-05): the Hillbrow Tower as the J of "Johannesburg", "ELECTION
#: FORECAST" above the rest of the word, the nav's home link (``#logo``).
#: The tower-J alone is the favicon (SVG, and PNG at 32 and 180 px) and,
#: tight, the share cards' mark (``mark.svg``); ``og.png`` is the default
#: share image. ``whysoserious.svg`` is the umbrella site's logo (``#wsc``):
#: the apex portal's masthead and the footer's "part of" line. A viewBox is
#: the logo's box in its file's coordinates, for a page's <svg><use>.
LOGO = "logo.svg"
LOGO_VIEWBOX = "19 87 2826 1296"
UMBRELLA = "whysoserious.svg"
UMBRELLA_VIEWBOX = "440 272 1984 1016"
#: The umbrella site's address, which its logo links to.
APEX_URL = "https://whysoserious.city/"


def umbrella_svg(cls: str) -> str:
    """The umbrella logo (:data:`UMBRELLA`) for a page: one <svg><use>,
    decorative (the link around it carries the name), in the text colour."""
    return (f'<svg class="{cls}" viewBox="{UMBRELLA_VIEWBOX}" aria-hidden="true" focusable="false">'
            f'<use href="{UMBRELLA}#wsc"></use></svg>')


BRAND_FILES = ("logo.svg", "whysoserious.svg", "favicon.svg", "favicon-32.png", "apple-touch-icon.png", "og.png", "mark.svg")

#: The stylesheet's parts, in cascade order. A ``page-<name>.css`` is scoped to
#: ``.pg-<name>`` (:func:`scope_css`); every other file applies to every page.
#: The order is the one each page had when these were inline blocks: the
#: palette, the page's own rules, then the furniture every page shares.
CSS_FILES = ("tokens.css", "toggle.css",
             "page-doc.css", "page-sheet.css", "page-home.css", "page-portal.css",
             "page-art.css", "page-board.css",
             "page-claims.css", "page-commentary.css", "page-methodology.css",
             "chrome.css", "stat.css", "maps.css", "seat-table.css", "components.css")

#: A page stylesheet's file name; group 1 is the page type, ``pg-<type>`` its
#: body class. The one pattern for both ends: :func:`site_css` scopes by it and
#: ``build_site.page_type`` names the body class by it, so a type the one
#: accepts the other scopes (a hyphenated ``page-your-forecast.css`` included).
PAGE_CSS = re.compile(r"page-([a-z]+(?:-[a-z]+)*)\.css")



# --------------------------------------------------------------------------
# the stylesheet

_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _split_selectors(prelude: str) -> list[str]:
    out, depth, cur = [], 0, ""
    for ch in prelude:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    out.append(cur)
    return [s.strip() for s in out if s.strip()]


def _scope_selector(sel: str, scope: str) -> str:
    where = f":where(.{scope})"
    if sel.startswith((":root", "html")):
        return sel
    if sel == "*":
        return f"{where},{where} *"
    if re.match(r"body\b", sel):
        return "body" + where + sel[4:]
    return f"{where} {sel}"


def _blocks(css: str):
    """``(prelude, body)`` for each top-level rule or at-rule."""
    i = 0
    while True:
        j = css.find("{", i)
        if j < 0:
            if css[i:].strip():
                raise ValueError(f"CSS left over after the last rule: {css[i:].strip()[:60]!r}")
            return
        depth, k = 1, j + 1
        while depth:
            if k >= len(css):
                raise ValueError(f"unclosed rule: {css[i:j].strip()[:60]!r}")
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        yield css[i:j].strip(), css[j + 1:k - 1]
        i = k


def scope_css(css: str, scope: str) -> str:
    """Every rule of ``css`` confined to elements inside ``.<scope>`` (or the
    ``<body class="<scope>">`` itself), with its specificity unchanged.

    ``body`` becomes ``body:where(.scope)``, ``*`` covers the body too, and
    ``:root``/``html`` rules are left alone (a page's <body> class cannot
    reach its root). ``@media``/``@supports`` blocks are scoped inside;
    other at-rules are copied as written.
    """
    out = []
    for prelude, body in _blocks(_COMMENT.sub("", css)):
        if prelude.startswith(("@media", "@supports")):
            out.append(f"{prelude}{{{scope_css(body, scope)}}}")
        elif prelude.startswith("@"):
            out.append(f"{prelude}{{{body}}}")
        else:
            sels = ",".join(_scope_selector(s, scope) for s in _split_selectors(prelude))
            out.append(f"{sels}{{{body.strip()}}}")
    return "\n".join(out)


def _light_twice(css: str) -> str:
    """The light palette, emitted a second time for a reader with no script.

    ``tokens.css`` writes it once, as ``:root[data-theme="light"]{…}``; the
    same declarations go into ``@media (prefers-color-scheme: light)`` under
    ``:root:not([data-theme="dark"])``, so the OS is honoured before (or
    without) js/theme.js. One copy in the source, two in the output."""
    m = re.search(r':root\[data-theme="light"\]\{(.*?)\}', css, re.S)
    if not m:
        raise ValueError('tokens.css has no :root[data-theme="light"] palette')
    media = ('@media (prefers-color-scheme: light){\n  :root:not([data-theme="dark"]){'
             + m.group(1) + "}\n}\n")
    return css[:m.start()] + media + css[m.start():]


#: The typefaces (owner, 2026-10-03): IBM Plex Sans, Serif and Mono, served
#: from this site, never a font service. The files are IBM's own "split"
#: Latin-1 subsets (npm @ibm/plex-sans 1.1.0, @ibm/plex-serif 2.0.0,
#: @ibm/plex-mono 2.5.0, ``fonts/split/woff2/``), byte copies in
#: ``src/fonts/`` with their licence, the SIL Open Font License 1.1
#: (``OFL.txt``). Family, file stem, then (style name, weight, style).
FONT_FACES = (
    ("IBM Plex Sans", "IBMPlexSans", (("Regular", 400, "normal"), ("Italic", 400, "italic"),
                                      ("Medium", 500, "normal"), ("SemiBold", 600, "normal"),
                                      ("Bold", 700, "normal"))),
    ("IBM Plex Serif", "IBMPlexSerif", (("Regular", 400, "normal"), ("Italic", 400, "italic"),
                                        ("SemiBold", 600, "normal"), ("Bold", 700, "normal"))),
    ("IBM Plex Mono", "IBMPlexMono", (("Regular", 400, "normal"), ("SemiBold", 600, "normal"),
                                      ("Bold", 700, "normal"))),
)
#: IBM's unicode-range for the Latin-1 split. A character outside it (the
#: arrows, the check mark) falls back to the next font in tokens.css's stack.
FONT_RANGE = ("U+0000,U+000D,U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+02C6,U+02DA,"
              "U+02DC,U+2013-2014,U+2018-201A,U+201C-201E,U+2020-2022,U+2026,U+2030,"
              "U+2039-203A,U+2044,U+2074,U+20AC,U+2122,U+2212,U+FB01-FB02")


def font_file(stem: str, style_name: str) -> str:
    return f"{stem}-{style_name}-Latin1.woff2"


def font_css() -> str:
    """The generated block: one ``@font-face`` per face in :data:`FONT_FACES`,
    ``font-display: swap`` (the fallback shows until a face loads), each file
    named relative to the stylesheet. tokens.css puts the families first in
    ``--serif``, ``--sans`` and ``--mono``."""
    lines = ["/* generated by src/site_assets.py from FONT_FACES: do not edit */"]
    for family, stem, faces in FONT_FACES:
        for style_name, weight, style in faces:
            lines.append(f'@font-face{{font-family:"{family}";font-style:{style};font-weight:{weight};'
                         f'font-display:swap;src:url("../{FONT_DIR}/{font_file(stem, style_name)}") '
                         f'format("woff2");unicode-range:{FONT_RANGE};}}')
    return "\n".join(lines) + "\n"


def colour_css() -> str:
    """The generated block: ``.pc-<code>`` per party colour, ``.city-<slug>``
    per city accent. One definition each (``render_sheet.CHIPS``,
    ``cities/<slug>.toml``'s ``[site] accent``), so no page or script carries
    a colour as a literal."""
    import build_portal
    import render_sheet
    lines = ["/* generated by src/site_assets.py from render_sheet.CHIPS and "
             "cities/*.toml: do not edit */",
             f":root{{--pc-other:{render_sheet.OTHER_CHIP};}}"]
    for code, colour in render_sheet.CHIPS.items():
        lines.append(f".pc-{code}{{--pc:{colour};}}")
    for f in sorted((REPO_ROOT / "cities").glob("*.toml")):
        site = tomllib.loads(f.read_text(encoding="utf-8")).get("site", {})
        lines.append(f".city-{f.stem}{{--city:{site.get('accent', build_portal.DEFAULT_ACCENT)};}}")
    return "\n".join(lines) + "\n"


def site_css() -> str:
    """``site/css/site.css``, whole: the typefaces first (:func:`font_css`)."""
    parts = [font_css()]
    for name in CSS_FILES:
        text = (CSS_SRC / name).read_text(encoding="utf-8")
        if name == "tokens.css":
            text = _light_twice(text)
        m = PAGE_CSS.fullmatch(name)
        if m:
            text = scope_css(text, f"pg-{m.group(1)}")
        elif name.startswith("page-"):
            raise SystemExit(f"src/css/{name} is a page stylesheet whose name "
                             f"site_assets.PAGE_CSS cannot scope: its rules would "
                             f"reach every page. Name it page-<lowercase-words>.css.")
        parts.append(f"/* ---- src/css/{name} ---- */\n{text.strip()}\n")
    on_disk = sorted(p.name for p in CSS_SRC.glob("*.css"))
    if on_disk != sorted(CSS_FILES):
        raise SystemExit(f"src/css holds {on_disk}, and site_assets.CSS_FILES lists "
                         f"{sorted(CSS_FILES)}: a stylesheet that is not listed never "
                         f"reaches a page. List it, in cascade order, or delete it.")
    parts.append(colour_css())
    return "\n".join(parts)


def js_files() -> list[Path]:
    return sorted(JS_SRC.glob("*.js"))


def font_files() -> list[Path]:
    """The typefaces :data:`FONT_FACES` names, and their licence. A face
    whose file is missing, or a file no face names, stops the build."""
    named = {font_file(stem, n) for _, stem, faces in FONT_FACES for n, _, _ in faces}
    on_disk = {f.name for f in FONT_SRC.glob("*.woff2")}
    if named != on_disk:
        raise SystemExit(f"src/fonts holds {sorted(on_disk - named)} that no face names, and "
                         f"site_assets.FONT_FACES names {sorted(named - on_disk)} that are not there")
    return sorted([*(FONT_SRC / n for n in named), FONT_SRC / "OFL.txt"])


def write(out: Path) -> list[str]:
    """Write ``css/site.css``, ``js/*.js`` and ``fonts/`` under ``out``;
    returns the paths."""
    written = []
    css_dir, js_dir, font_dir = out / "css", out / JS_DIR, out / FONT_DIR
    for d in (css_dir, js_dir, font_dir):
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True)
    (out / CSS_PATH).write_text(site_css(), encoding="utf-8")
    written.append(CSS_PATH)
    for f in js_files():
        shutil.copyfile(f, js_dir / f.name)
        written.append(f"{JS_DIR}/{f.name}")
    for f in font_files():
        shutil.copyfile(f, font_dir / f.name)
        written.append(f"{FONT_DIR}/{f.name}")
    for name in BRAND_FILES:
        shutil.copyfile(BRAND_SRC / name, out / name)
        written.append(name)
    return written


# --------------------------------------------------------------------------
# what a page puts in its <head>

def head(*scripts: str) -> str:
    """The stylesheet, the favicons, the theme script (blocking, so the
    palette is chosen before first paint) and the provenance pop-over; then any page scripts
    named, deferred. Relative links: /play/ and /make/ re-point them
    (``build_play.one_level_down``)."""
    tags = [f'<link rel="stylesheet" href="{CSS_PATH}">',
            '<link rel="icon" href="favicon.svg" type="image/svg+xml">',
            '<link rel="icon" href="favicon-32.png" sizes="32x32" type="image/png">',
            '<link rel="apple-touch-icon" href="apple-touch-icon.png">',
            f'<script src="{JS_DIR}/theme.js"></script>',
            f'<script defer src="{JS_DIR}/stat-tip.js"></script>']
    tags += [f'<script defer src="{JS_DIR}/{escape(s)}"></script>' for s in scripts]
    return "\n".join(tags) + "\n"


# --------------------------------------------------------------------------
# the gate

#: What may not appear in a page. Each pattern matches inside a tag, so prose
#: that mentions "style" is not a hit.
INLINE = (
    ("a <style> element", re.compile(r"<style\b", re.I)),
    ("a style attribute", re.compile(r"<[a-zA-Z][^>]*?\sstyle\s*=", re.S)),
    ("an event-handler attribute", re.compile(r"<[a-zA-Z][^>]*?\son[a-z]+\s*=", re.S)),
    ("a javascript: URL", re.compile(r"""\s(?:href|src|action)\s*=\s*["']?\s*javascript:""", re.I)),
)
_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)


def inline_problems(html: str) -> list[str]:
    """Every inline style or script in ``html``, as ``"<what>: …context…"``.

    A ``<script>`` must have a ``src`` and an empty body. HTML comments are
    skipped, so a template's own documentation of its markers is not a hit.
    """
    text = re.sub(r"<!--.*?-->", " ", html, flags=re.S)
    out = []
    for what, pat in INLINE:
        for m in pat.finditer(text):
            out.append(f"{what}: …{text[m.start():m.start() + 80].strip()}…")
    for m in _SCRIPT.finditer(text):
        if not re.search(r"\bsrc\s*=", m.group(1)) or m.group(2).strip():
            out.append(f"an inline <script>: …{m.group(0)[:80].strip()}…")
    return out


def scan_site(root: Path) -> tuple[list[str], list[str]]:
    """Every page under ``root`` (at any depth: wrangler ships the directory
    whole) and every inline style or script in them: ``(pages, problems)``,
    each problem as ``"<page>: <what>"``. ``build_site`` refuses a build and
    ``deploy_check`` a deploy on any problem."""
    pages = sorted(f.relative_to(root).as_posix() for f in root.rglob("*.html"))
    problems = [f"{rel}: {w}" for rel in pages
                for w in inline_problems((root / rel).read_text(encoding="utf-8"))]
    return pages, problems
