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
   (``page.py``'s ``handoff``: rule A, ``src/prediction.py``), or from our
   prediction, which :mod:`build_make` writes, when section 1 is untouched.

What the served page is made of
===============================

``your-forecast/index.html``
    ``interactive/your-forecast.html`` with its prototype-only parts cut
    (``__DEVONLY__`` spans), the site's head (``build_site.SITE_HEAD``), nav
    and footer put in one level down, section 1's published figures at its
    ``<!-- __PLAY:<name>__ -->`` markers (``build_play.FILL``) and section 2's
    seat-table attributes and its ward map's viewBox at its
    ``<!-- __MAKE:<name>__ -->`` markers.
``your-forecast/js/``, ``css/``, ``pyboot/``
    Byte copies of the page's modules (:data:`JS`), stylesheets and Python
    entries, except ONE declared line of each Worker's loader: where the draws
    are (``build_play.DRAWS_LINE``) and where the Worker's ``seats.js`` is
    (``build_make.SEATS_LINE``); and ``play-state.js``'s one import, the name
    blocklist (:data:`BLOCKLIST_LINE`); and ``share-sheet.js``'s import of the
    site's one share sheet, served at ``js/share-dialog.js``
    (:data:`SHARE_DIALOG_LINE`). The build refuses if any is not there
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
#: The page's share card text. It carries no figure. A link that carries a
#: reader's forecast gets its own title and image from the site's Worker
#: (src/share-edge.js rewrites these tags); any other gets these, and og:image
#: is the site's default share image (site_assets.BRAND_FILES).
OG_TITLE = "Your Johannesburg election forecast"
OG_DESCRIPTION = ("Adjust the model's turnout, polls and by-elections, then call every "
                  "ward and set the vote yourself. The seats follow from the law.")
#: The modules the page loads, statically or as one of its two Workers.
JS = (
    # section 1: the page, its share sheet and image, its Worker and engine
    "model.js", "play-state.js", "play-card.js", "play-share.js", "model-worker.js",
    "reweight-engine.js", "pubtip.js",
    # section 2: the page, its state, map and share sheet, its seat Worker,
    # the arrival view a shared link opens, and the share cards and their
    # font widths (one card module with the site's Worker, src/share-edge.js),
    # and the count of sealed forecasts (entries.js)
    "make.js", "make-state.js", "builder-state.js", "map.js", "make-share.js",
    "make-worker.js", "seat-engine.js", "arrival.js", "entries.js", "share-card.js", "card-fonts.js",
    # both: the address, the one share sheet, the PNG step, the seat table,
    # the tooltips' placement
    "yf-url.js", "share-sheet.js", "card-text.js", "seat-table.js", "tip.js",
)
CSS = ("interactive.css", "play.css", "your-forecast.css")
PYBOOT = ("page.py", "boot.py")

#: The one line of play-state.js that differs between the repository and the
#: site: the owner's name blocklist, copied beside it (build_make.WORKER_API_JS).
BLOCKLIST_LINE = ('from "../../worker-api/src/blocklist.js";', 'from "./blocklist.js";')
#: The one line of share-sheet.js that differs: the site's one share sheet
#: (src/js/share-dialog.js), which site_assets serves at js/, two levels up
#: from your-forecast/js/.
SHARE_DIALOG_LINE = ('from "../../src/js/share-dialog.js";', 'from "../../js/share-dialog.js";')

#: What "Your forecast" adds to the site's one share sheet (share_sheet.sheet),
#: the same in both sections: the name above the link; the seal, the entry
#: note and the image picker below it.
SHEET_NAME = ('<label class="namefield">Your name on the image <span class="stubnote">(optional)</span>\n'
              '      <input class="shname" type="text" autocomplete="off" spellcheck="false"></label>\n'
              '    <p class="stubnote shnamenote" role="status"></p>')
SHEET_SEAL = ('<p class="stubnote shseal yf-slot" role="status"></p>\n'
              '    <p class="stubnote shentry">This sheet seals the link when it opens. Every sealed link is an entry in the ranking\n'
              '      against the result, under the name above, and a new name or a changed forecast is another entry.\n'
              '      The leaderboard shows names after the count. <a href="../privacy">How entries are kept</a></p>\n'
              '    <label class="shimgpick">Image <select class="shimg">\n'
              '      <option value="link">Link preview</option>\n'
              '      <option value="story">Story, for a phone</option></select></label>')
#: Each section's sheet, by its marker name: the id of its heading.
SHEETS = {"play": "share-title", "break": "b-share-title"}


def sheets() -> dict[str, str]:
    """Each section's share sheet at its ``<!-- __YFSHEET:<name>__ -->``
    marker: the site's one sheet (share_sheet.sheet) with this page's
    additions."""
    import share_sheet
    return {f"<!-- __YFSHEET:{name}__ -->": share_sheet.sheet(
                heading_id=hid, heading="Share this forecast", link_label="Link to this forecast",
                above_link=SHEET_NAME, below_link=SHEET_SEAL)
            for name, hid in SHEETS.items()}


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
             **build_make.seat_attrs(), **build_make.map_attrs(), **sheets()}
    for marker, value in fills.items():
        build_play.occurs_once(page, marker, SOURCE.name)
        page = page.replace(marker, value)
    left = re.findall(r"<!-- __[A-Z:a-z]+__ -->", page)
    if left:
        raise YourForecastBuildError(f"build_your_forecast: unfilled markers in {SOURCE.name}: {left}")
    return page


def _rewrite(name: str, data: bytes) -> bytes:
    """The one declared line of a module that differs when served."""
    line = {"model-worker.js": build_play.DRAWS_LINE, "seat-engine.js": build_make.SEATS_LINE,
            "play-state.js": BLOCKLIST_LINE, "share-sheet.js": SHARE_DIALOG_LINE}.get(name)
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
