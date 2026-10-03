"""Build "your forecast" (``/your-forecast/``) from ``interactive/`` into the site.

Called by ``build_site.main``, which renders, scans, stamps and ledgers the page
like every other (INTEGRATION §3c). This module only ASSEMBLES it and copies
what it loads; it decides nothing about what is allowed on a page.

One page, two sections (owner, 2026-10-03; it replaced ``/play/`` and
``/make/``, which ``src/worker.js`` redirects here with their query strings):

1. **Adjust the model** (``#adjust``): the published draws re-weighted by the
   reader's turnout, poll and by-election settings, and seated under a law the
   reader picks (``js/model.js``, ``pyboot/page.py``, ``src/reweight.py``).
   Its published figures come from :mod:`build_play`.
2. **Break the model** (``#break``): the same forecast as a reader's own,
   every ward called and the vote set by hand, seated by the statute
   (``js/make.js``, the seat code). It opens from section 1's weighted draws
   (``page.py``'s ``handoff``, ``src/start_rule.py``), or from the published
   start :mod:`build_make` writes when section 1 is untouched.

What the served page is made of
===============================

``your-forecast/index.html``
    ``interactive/your-forecast.html`` with its prototype-only parts cut
    (``__DEVONLY__`` spans), the site's head (``build_site.SITE_HEAD``), nav
    and footer put in one level down, section 1's published figures at its
    ``<!-- __PLAY:<name>__ -->`` markers (``build_play.FILL``) and section 2's
    seat-table attributes at its ``<!-- __MAKE:<name>__ -->`` markers.
``your-forecast/js/``, ``css/``, ``pyboot/``
    Byte copies of the page's modules (:data:`JS`), stylesheets and Python
    entries, except ONE declared line of each Worker's loader: where the draws
    are (``build_play.DRAWS_LINE``) and where the Worker's ``seats.js`` is
    (``build_make.SEATS_LINE``). The build refuses if either is not there
    exactly once.
``your-forecast/py/``
    The served Python (``manifest.json``, the seat code, and the page code in
    ``page/``), written by ``interactive/tools/sync_py.mjs``, which this build
    runs, then copies.
``your-forecast/parties.json``, ``ward_paths.json``, ``labels.json``, ``laws.json``
    Section 1's data (:mod:`build_play`).
``your-forecast/forecast.json``
    Section 2's data and published start (:mod:`build_make`).

Every figure a reader's settings or edits produce is written at view time,
only into ``data-live`` regions, only by a module ``stats.LIVE_WRITERS`` lists
for that region; ``stats.script_writes`` holds each to that.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import build_make
import build_play

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIVE = REPO_ROOT / "interactive"
SOURCE = INTERACTIVE / "your-forecast.html"

#: Where the page is served, relative to the site root.
YF_DIR = "your-forecast"
YF_PAGE = f"{YF_DIR}/index.html"
#: The page's address in the nav and in og:url.
YF_HREF = f"{YF_DIR}/"
#: The page directories this one replaced. The build removes them from the
#: site (a page nobody rebuilds still looks current), and src/worker.js
#: redirects their addresses here, query string kept.
RETIRED = ("play", "make")
#: The page's share card text. It carries no figure: a shared link shows this
#: same generic card, because nothing renders per-link previews on the server.
#: og:image is the site's default share image (site_assets.BRAND_FILES).
OG_TITLE = "Your Johannesburg election forecast"
OG_DESCRIPTION = ("Adjust the model's turnout, polls and by-elections, then call every "
                  "ward and set the vote yourself. The seats follow from the law.")
#: The modules the page loads, statically or as one of its two Workers.
JS = (
    # section 1: the page, its share sheet and image, its Worker and engine
    "model.js", "play-state.js", "play-card.js", "play-share.js", "model-worker.js",
    "reweight-engine.js", "pubtip.js",
    # section 2: the page, its state, map and share sheet, its seat Worker
    "make.js", "make-state.js", "builder-state.js", "map.js", "make-share.js",
    "make-worker.js", "seat-engine.js",
    # both: the address, the share image, its text layout, the seat table,
    # the tooltips' placement
    "yf-url.js", "forecast-card.js", "card-text.js", "seat-table.js", "tip.js",
)
CSS = ("interactive.css", "play.css", "your-forecast.css")
PYBOOT = ("page.py", "boot.py")

_DEVONLY = re.compile(r"<!-- __DEVONLY_START__ -->.*?<!-- __DEVONLY_END__ -->\n?", re.S)


class YourForecastBuildError(SystemExit):
    """The page cannot be assembled; the message says what to do."""


def assemble(*, site_head: str, nav: str, footer: str, processed: Path) -> str:
    """The page's HTML, tokens unrendered: your-forecast.html with the site put in."""
    page = SOURCE.read_text(encoding="utf-8")
    starts = page.count("<!-- __DEVONLY_START__ -->")
    if not starts or starts != page.count("<!-- __DEVONLY_END__ -->"):
        raise YourForecastBuildError("build_your_forecast: the __DEVONLY__ markers do not pair")
    page = _DEVONLY.sub("", page)
    # the leading authoring comment describes the markers; it is not the page's
    page = re.sub(r"<!--\n  \"Your forecast\".*?-->\n", "", page, count=1, flags=re.S)
    fills = {"<!-- __YFHEAD__ -->": build_play.one_level_down(site_head),
             "<!-- __YFNAV__ -->": build_play.one_level_down(nav),
             "<!-- __YFFOOT__ -->": build_play.one_level_down(footer),
             **{f"<!-- __PLAY:{k}__ -->": v for k, v in build_play.fills(Path(processed)).items()},
             **build_make.seat_attrs()}
    for marker, value in fills.items():
        build_play.occurs_once(page, marker, SOURCE.name)
        page = page.replace(marker, value)
    left = re.findall(r"<!-- __[A-Z:a-z]+__ -->", page)
    if left:
        raise YourForecastBuildError(f"build_your_forecast: unfilled markers in {SOURCE.name}: {left}")
    return page


def _rewrite(name: str, data: bytes) -> bytes:
    """The one declared line of a Worker loader that differs when served."""
    line = {"model-worker.js": build_play.DRAWS_LINE, "seat-engine.js": build_make.SEATS_LINE}.get(name)
    if not line:
        return data
    text = data.decode("utf-8")
    build_play.occurs_once(text, line[0], f"js/{name}, its served-layout line")
    return text.replace(line[0], line[1]).encode("utf-8")


def write_assets(out: Path, processed: Path) -> list[str]:
    """Copy everything the page loads into ``out/your-forecast/`` and remove
    the retired page directories; returns the paths written."""
    for d in (YF_DIR, *RETIRED):
        if (out / d).exists():
            shutil.rmtree(out / d)   # nothing survives a build that did not write it
    dest = out / YF_DIR
    written = []

    def put(rel: str, data: bytes) -> None:
        f = dest / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        written.append(f"{YF_DIR}/{rel}")

    for name in JS:
        put(f"js/{name}", _rewrite(name, (INTERACTIVE / "js" / name).read_bytes()))
    for name in build_make.WORKER_API_JS:
        put(f"js/{name}", (build_make.WORKER_SRC / name).read_bytes())
    for name in CSS:
        put(f"css/{name}", (INTERACTIVE / "css" / name).read_bytes())
    for name in PYBOOT:
        put(f"pyboot/{name}", (INTERACTIVE / "pyboot" / name).read_bytes())
    build_play.sync_python()
    manifest = json.loads((INTERACTIVE / "py" / "manifest.json").read_text(encoding="utf-8"))
    put("py/manifest.json", (INTERACTIVE / "py" / "manifest.json").read_bytes())
    for rel in manifest["files"]:                       # the seat code
        put(f"py/{rel}", (INTERACTIVE / "py" / rel).read_bytes())
    page = manifest["page"]                             # the page code
    for rel in [*page["files"], *page["data"], "page_code_ref.py"]:
        put(f"py/{page['dir']}/{rel}", (INTERACTIVE / "py" / page["dir"] / rel).read_bytes())
    put("parties.json", build_play.roster_json())
    put("ward_paths.json", build_play.ward_paths_json(processed))
    put("labels.json", build_play.labels_json())
    put("laws.json", build_play.laws_json())
    put(build_make.DATA, (json.dumps(build_make.forecast_data(), indent=None, sort_keys=True,
                                     separators=(",", ":")) + "\n").encode("utf-8"))
    return written
