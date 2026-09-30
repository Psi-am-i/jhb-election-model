"""Build "play with the model" (``/play/``) from ``interactive/`` into the site.

Called by ``build_site.main``, which renders, scans, stamps and ledgers the page
like every other (INTEGRATION §3c: "built by build_site.py from interactive/,
so the number gate and deploy_check see it like every other page"). This
module only ASSEMBLES it; it decides nothing about what is allowed on a page.

What the served page is made of
===============================

``play/index.html``
    ``interactive/model.html`` with its prototype-only parts cut
    (``__DEVONLY__`` spans), the site's ``THEME_HEAD``, nav and footer put in
    one level down, and the published forecast's own panels spliced in.
``play/js/``, ``play/css/``, ``play/pyboot/page.py``
    Byte copies of the page's modules (``PLAY_JS``), its stylesheet and its
    Python entry, except ONE declared line of ``model-worker.js``: where the
    draws are (``DRAWS_LINE``), which is ``site/draws/`` beside the prototype
    and ``/draws/`` when served. The build refuses if that line is not there
    exactly once, so a moved constant cannot ship a Worker that 404s.
``play/py/``
    The served copy of the page's Python (``manifest.json`` and ``page/``),
    written by ``interactive/tools/sync_py.mjs`` — the one definition of that
    copy and its hash — which this build runs, then copies.
``play/parties.json``
    Party names and colours for the draws' roster, from the site's one
    definition (``render_sheet.NAMES`` / ``CHIPS``, then
    ``parties.display_name``), so the page types none.

First paint is the published forecast AS TOKENS
===============================================

The untouched page shows the published forecast (SPEC-v2 F6). Its panels are
cut from ``forecast-sheet.html`` — the SOURCE template, whose figures are
``{{…}}`` tokens — and ``build_site`` renders them with ``stats.render``, so
every figure on first paint is ledgered, drift-checked and arrowed exactly as
on ``/forecast``. Each group of panels sits in a declarative shadow root with
the sheet's own stylesheet, so the two pages' class names cannot collide.
The sheet's inline scripts (the map tooltip, the coalition filter) are not
carried: they are the forecast page's, and the controls they drive are hidden.
The ``MAP`` region keeps its markers, so the number scan classifies its
figures as generated, exactly as on ``/forecast``.

Figures a reader's settings produce are NOT here: they are written at view
time into ``data-live`` regions by ``play/js/model.js`` only
(``stats.LIVE_WRITERS``), and ``stats.script_writes`` holds it to that.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIVE = REPO_ROOT / "interactive"
SHEET = REPO_ROOT / "forecast-sheet.html"
DRAWS = REPO_ROOT / "site" / "draws"

#: Where the page is served, relative to the site root.
PLAY_DIR = "play"
PLAY_PAGE = f"{PLAY_DIR}/index.html"
#: The modules the page loads, statically or as its Worker. Nothing else under
#: interactive/js ships: the builder's modules are not part of this page.
PLAY_JS = ("model.js", "play-state.js", "model-worker.js", "reweight-engine.js")
PLAY_CSS = ("interactive.css",)
PLAY_PYBOOT = ("page.py",)
#: The one line of the Worker that differs between the prototype and the site.
DRAWS_LINE = ('const DRAWS = "../../site/draws/";', 'const DRAWS = "../../draws/";')

#: The published forecast's panels, by host marker in model.html. Each is a
#: slice of forecast-sheet.html from its first string to its last, both
#: included; each must occur exactly once.
PANELS = {
    "seats": (("<figure>", '<div class="chart" id="seats">'), "</figure>"),
    "tiles": ('<section class="stats" id="tiles">', "<!-- __TILES_END__ --></section>"),
    "govern": ("<!-- __GOVERN_LEDE_START__ -->", "<!-- __GOVERN_NOTE_END__ --></figcaption>"),
    "map": ("<!-- __MAP_START__ -->", "<!-- __MAP_END__ -->"),
    "claims": ('<section class="claimband" id="claims">', "<!-- __CLAIMS_END__ -->", "</section>"),
}
#: Which panels fill which host, in order.
HOSTS = {"seats": ("seats",), "panels": ("tiles", "govern", "map", "claims")}
#: The forecast page's controls, which need its scripts, are hidden here.
HIDE_CSS = (".maptoggle,.govfilter,#govMore,script{display:none!important}"
            ":host{display:block}")

_DEVONLY = re.compile(r"<!-- __DEVONLY_START__ -->.*?<!-- __DEVONLY_END__ -->\n?", re.S)
_SCRIPT = re.compile(r"<script\b[^>]*>.*?</script>\s*", re.S | re.I)
_STYLE = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
_REL_ATTR = re.compile(r'\b(href|src)="(?![a-z][a-z0-9+.-]*:|/|#|\.\./)([^"]*)"', re.I)


class PlayBuildError(SystemExit):
    """The page cannot be assembled; the message says what to do."""


def _once(text: str, needle: str, what: str) -> int:
    n = text.count(needle)
    if n != 1:
        raise PlayBuildError(f"build_play: {what}: {needle!r} occurs {n} times, not once")
    return text.index(needle)


def one_level_down(html: str) -> str:
    """Relative links and images, re-pointed from the site root to ``/play/``."""
    return _REL_ATTR.sub(lambda m: f'{m.group(1)}="../{m.group(2)}"', html)


def panel(sheet: str, name: str) -> str:
    """One published panel, cut from the forecast sheet's source template."""
    spec = PANELS[name]
    if name == "seats":
        (opener, anchor), closer = spec
        at = _once(sheet, anchor, "the seats chart")
        lo = sheet.rindex(opener, 0, at)
        hi = sheet.index(closer, at) + len(closer)
    else:
        lo = _once(sheet, spec[0], f"the {name} panel")
        hi = lo
        for closer in spec[1:]:
            hi = sheet.index(closer, hi) + len(closer)
    return _SCRIPT.sub("", sheet[lo:hi])


def published_host(sheet: str, names, stat_css: str) -> str:
    """A declarative shadow root holding these panels and the sheet's styles."""
    head = sheet[:sheet.index("</head>")]
    css = "\n".join(_STYLE.findall(head))
    body = "\n".join(panel(sheet, n) for n in names)
    return ('<template shadowrootmode="open"><style>' + css + "\n" + stat_css + "\n"
            + HIDE_CSS + '</style><div class="page">' + one_level_down(body)
            + "</div></template>")


def assemble(*, theme_head: str, nav: str, footer: str, stat_css: str,
             cut_markers) -> str:
    """The page's HTML, tokens unrendered: model.html with the site put in."""
    page = (INTERACTIVE / "model.html").read_text(encoding="utf-8")
    starts = page.count("<!-- __DEVONLY_START__ -->")
    if not starts or starts != page.count("<!-- __DEVONLY_END__ -->"):
        raise PlayBuildError("build_play: model.html's __DEVONLY__ markers do not pair")
    page = _DEVONLY.sub("", page)
    # the leading authoring comment describes the markers; it is not the page's
    page = re.sub(r"<!--\n  \"Play with the model\".*?-->\n", "", page, count=1, flags=re.S)
    sheet = cut_markers(SHEET.read_text(encoding="utf-8"), None)
    for marker, value in (("<!-- __PLAYHEAD__ -->", theme_head),
                          ("<!-- __PLAYNAV__ -->", one_level_down(nav)),
                          ("<!-- __PLAYFOOT__ -->", one_level_down(footer))):
        _once(page, marker, "model.html")
        page = page.replace(marker, value)
    for host, names in HOSTS.items():
        marker = f"<!-- __PUBLISHED:{host}__ -->"
        _once(page, marker, "model.html")
        page = page.replace(marker, published_host(sheet, names, stat_css))
    left = re.findall(r"<!-- __[A-Z:a-z]+__ -->", page)
    if left:
        raise PlayBuildError(f"build_play: unfilled markers in model.html: {left}")
    return page


def sync_python() -> None:
    """Run the one copy rule (``sync_py.mjs``); refuse, saying how, if it cannot."""
    tool = INTERACTIVE / "tools" / "sync_py.mjs"
    try:
        run = subprocess.run(["node", str(tool)], cwd=REPO_ROOT, capture_output=True, text=True)
    except FileNotFoundError:
        raise PlayBuildError("build_play: node is not installed, so the page's Python cannot be "
                             "copied by interactive/tools/sync_py.mjs") from None
    if run.returncode:
        raise PlayBuildError(f"build_play: {tool.relative_to(REPO_ROOT)} failed:\n{run.stderr}")


def roster() -> dict:
    """``{code: {name, colour}}`` for every party the draws carry."""
    import parties as _parties
    import render_sheet
    codes = list(render_sheet.NAMES)
    man = DRAWS / "manifest.json"
    if man.is_file():
        codes = json.loads(man.read_text(encoding="utf-8")).get("parties") or codes
    return {c: {"code": c, "name": render_sheet.NAMES.get(c) or _parties.display_name(c),
                "colour": render_sheet.CHIPS.get(c, "#8b918b")} for c in codes}


def write_assets(out: Path) -> list[str]:
    """Copy everything the page loads into ``out/play/``; returns the paths written."""
    dest = out / PLAY_DIR
    if dest.exists():
        shutil.rmtree(dest)          # nothing under play/ survives a build that did not write it
    written = []

    def put(rel: str, data: bytes) -> None:
        f = dest / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        written.append(f"{PLAY_DIR}/{rel}")

    for name in PLAY_JS:
        data = (INTERACTIVE / "js" / name).read_bytes()
        if name == "model-worker.js":
            text = data.decode("utf-8")
            _once(text, DRAWS_LINE[0], "js/model-worker.js, the draws location")
            data = text.replace(DRAWS_LINE[0], DRAWS_LINE[1]).encode("utf-8")
        put(f"js/{name}", data)
    for name in PLAY_CSS:
        put(f"css/{name}", (INTERACTIVE / "css" / name).read_bytes())
    for name in PLAY_PYBOOT:
        put(f"pyboot/{name}", (INTERACTIVE / "pyboot" / name).read_bytes())
    sync_python()
    manifest = json.loads((INTERACTIVE / "py" / "manifest.json").read_text(encoding="utf-8"))
    put("py/manifest.json", (INTERACTIVE / "py" / "manifest.json").read_bytes())
    page = manifest["page"]
    for rel in [*page["files"], *page["data"], "page_code_ref.py"]:
        put(f"py/{page['dir']}/{rel}", (INTERACTIVE / "py" / page["dir"] / rel).read_bytes())
    put("parties.json", (json.dumps(roster(), indent=1, sort_keys=True) + "\n").encode("utf-8"))
    return written
