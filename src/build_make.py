"""Build "make your own forecast" (``/make/``) from ``interactive/`` into the site.

Called by ``build_site.main`` next to ``build_play``, which renders, scans,
stamps and ledgers the page like every other. This module only ASSEMBLES it
and writes the data it starts from; it decides nothing about what is allowed
on a page. Anonymous, as /play/ is: no sign-in, no server storage, no prize.
The reader's forecast lives in the page's address (``js/make-state.js``).

What the served page is made of
===============================

``make/index.html``
    ``interactive/make.html`` with its prototype-only parts cut
    (``__DEVONLY__`` spans), the site's ``THEME_HEAD``, nav and footer, and
    the published forecast's seat panel cut from ``forecast-sheet.html`` as
    ``{{tokens}}`` (``build_play.published_host``), so first paint is ledgered
    tokens.
``make/forecast.json``
    The one data file the page reads (:func:`forecast_data`): the generated
    schema (``worker-api/tools/make_schema.mjs``'s own ``build``, run on the
    artefact :func:`model_artefact` writes from the published draws), the ward
    geometry, and the start state.
``make/js/``, ``make/css/``, ``make/pyboot/boot.py``, ``make/py/``
    Byte copies of the page's modules (``MAKE_JS``), the stylesheet, the seat
    code's boot file and the served seat code (``interactive/tools/sync_py.mjs``
    writes it; its ``manifest.files``), except ONE declared line of
    ``seat-engine.js`` (``SEATS_LINE``): where the Worker's own
    ``seats.js`` is. ``seats.js`` and the ``http.js`` it imports are copied
    beside it from ``worker-api/src``. Both run only inside the page's Web
    Worker, which the number gate does not follow (it cannot touch the page).

The start state, stated exactly
===============================

* **Ward calls**: the modal winner of each ward over the published draws'
  ``ward_winner`` block (``site/draws/``), by
  ``score_forecasts.model_forecast``: the one definition of "the model as a
  reader who changed nothing". It is the ``winner`` column of
  ``ward_winner_probs.csv`` that the forecast page's map passes to
  ``render_map.ward_call`` wherever that column has no tie
  (``tests/test_make_page.py``).
* **Vote shares**: there is NO published combined (ward + list) share. The
  draws' manifest refuses one (``export_draws.COMBINED_SHARE_REFUSAL``). The
  start uses the same ``model_forecast`` rule on the only per-draw share the
  draws publish, the LIST (PR) ballot share ``pr_share``: each roster party's
  median over the 5,000 draws, renormalised to sum to 100 (the medians alone
  do not). The ``OTHER`` column is not a party and is left out before
  renormalising. MODEL-LOG §1.270 measures what feeding a list share as the
  combined vote costs, so the untouched reader's council need not equal the
  published medians, and the page does not call it the model's forecast.
* **Total combined vote** (``reader_seats``' ``total_votes``, the schema's
  ``x-total-votes``): nothing published carries it. It is two ballots times
  the median over the draws of each draw's citywide votes cast, the sum over
  the four voter pools of the pool's registration (``pools_2026.json``) times
  the draw's pool turnout (the draws' ``pool_turnout`` block). Spoilt ballots
  are not taken off. It moves a seat only at a quota remainder boundary.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

import numpy as np

import build_play

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIVE = REPO_ROOT / "interactive"
DRAWS = REPO_ROOT / "site" / "draws"
WORKER_SRC = REPO_ROOT / "worker-api" / "src"

#: Where the page is served, relative to the site root.
MAKE_DIR = "make"
MAKE_PAGE = f"{MAKE_DIR}/index.html"
MAKE_HREF = f"{MAKE_DIR}/"
#: The page's share card text: no figure. A link carrying a forecast shows the
#: same generic preview; the image of a reader's forecast is drawn in their
#: browser.
OG_TITLE = "Make your own Johannesburg election forecast"
OG_DESCRIPTION = ("Call every Johannesburg ward, set each party's share of the vote "
                  "and pick who governs. The seats follow from the law.")
#: The page's modules. make-worker.js, seat-engine.js and the two worker-api
#: files run only in the Web Worker.
MAKE_JS = ("make.js", "make-state.js", "builder-state.js", "map.js", "make-share.js",
           "forecast-card.js", "card-text.js", "make-worker.js", "seat-engine.js")
WORKER_API_JS = ("seats.js", "http.js")
MAKE_CSS = ("interactive.css",)
MAKE_PYBOOT = ("boot.py",)
#: The one line of seat-engine.js that differs between the repository and the site.
SEATS_LINE = ('from "../../worker-api/src/seats.js";', 'from "./seats.js";')
#: The data file the page reads.
DATA = "forecast.json"
#: The site's own photograph (Hillbrow Tower) the share image is drawn on.
PHOTO = "share.jpg"

#: The published panel shown beside the reader's council, by host marker.
HOSTS = {"seats": ("seats",)}

_DEVONLY = re.compile(r"<!-- __DEVONLY_START__ -->.*?<!-- __DEVONLY_END__ -->\n?", re.S)


class MakeBuildError(SystemExit):
    """The page cannot be assembled; the message says what to do."""


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --------------------------------------------------------------------------
# the start state


def _draws(draws: Path = DRAWS) -> tuple[dict, dict, bytes]:
    import reweight
    man_bytes = (draws / "manifest.json").read_bytes()
    manifest = json.loads(man_bytes)
    blob = (draws / "base.bin").read_bytes()
    return manifest, reweight.unpack(blob, manifest), man_bytes + blob


def _columns(manifest: dict, name: str) -> list[str]:
    return next(b for b in manifest["blocks"] if b["name"] == name)["columns"]


def total_votes(manifest: dict, arrays: dict, pools_file: Path) -> tuple[int, dict]:
    """``(total_votes, provenance)``; module docstring."""
    pools = json.loads(pools_file.read_text(encoding="utf-8"))["pools"]
    names = _columns(manifest, "pool_turnout")
    missing = [n for n in names if n not in pools]
    if missing:
        raise MakeBuildError(f"build_make: pools {missing} of the draws are not in {pools_file}")
    registered = np.array([float(pools[n]["registered"]) for n in names])
    cast = np.asarray(arrays["pool_turnout"], dtype=float) @ registered
    total = int(round(2 * float(np.median(cast))))
    return total, {
        "rule": ("two ballots times the median over the draws of the votes cast, "
                 "the sum over voter pools of registration times the draw's pool turnout; "
                 "spoilt ballots not taken off"),
        "pool_turnout": "site/draws/base.bin pool_turnout",
        "registration": str(pools_file.relative_to(REPO_ROOT)) if pools_file.is_relative_to(REPO_ROOT) else pools_file.name,
        "registration_sha256": _sha(pools_file.read_bytes()),
    }


def model_artefact(manifest: dict, total: int, roster: dict) -> dict:
    """The model artefact ``make_schema.mjs`` reads, from the published draws."""
    import cityconfig
    city = cityconfig.active()
    target = str(city.default_target)
    structure = city.structure_for(target)
    council = int(structure["council"])
    run = manifest["published_run"]["model_run_id"]
    parties = list(manifest["parties"])
    return {
        "model_ref": run,
        "city": city.slug,
        "target": target,
        "council_seats": council,
        "ward_seats": int(structure["wards"]),
        "majority": council // 2 + 1,
        "total_votes": total,
        "no_pr_list": [],
        "parties": [{"code": c, "name": roster[c]["name"], "colour": roster[c]["colour"]} for c in parties],
        "placeholder": False,
    }


def geometry() -> dict:
    """The ward geometry and compass sectors, by the prototype tool's own
    definition (``interactive/tools/make_fixtures.geometry``), without its
    date stamp so a rebuild is byte-stable."""
    sys.path.insert(0, str(INTERACTIVE / "tools"))
    try:
        import make_fixtures
    finally:
        sys.path.pop(0)
    geom = make_fixtures.geometry()
    geom.pop("_generated", None)
    geom["_about"] = ("The live site's ward geography (data/processed/ward_paths.json, "
                      "ward_hex_layout.json) with compass sectors derived by "
                      "interactive/tools/make_fixtures.sectors (DESIGN-decided §1).")
    return geom


def make_schema(artefact: dict, geom: dict) -> dict:
    """The generated schema, by ``worker-api/tools/make_schema.mjs``'s ``build``."""
    tool = REPO_ROOT / "worker-api" / "tools" / "make_schema.mjs"
    script = ("import { build } from " + json.dumps(tool.as_uri()) + ";\n"
              "let s = ''; process.stdin.on('data', d => s += d).on('end', () => {\n"
              "  const { model, geometry } = JSON.parse(s);\n"
              "  const out = build(Buffer.from(model), Buffer.from(geometry),\n"
              "    { model: 'make/forecast.json model artefact (build_make.model_artefact)',\n"
              "      geometry: 'make/forecast.json geometry (build_make.geometry)' });\n"
              "  process.stdout.write(out['generated/forecast.schema.json']);\n"
              "});\n")
    payload = json.dumps({"model": json.dumps(artefact, sort_keys=True),
                          "geometry": json.dumps(geom, sort_keys=True)})
    try:
        run = subprocess.run(["node", "--input-type=module", "-e", script], input=payload,
                             capture_output=True, text=True, cwd=REPO_ROOT)
    except FileNotFoundError:
        raise MakeBuildError("build_make: node is not installed, so the schema cannot be "
                             "generated by worker-api/tools/make_schema.mjs") from None
    if run.returncode:
        raise MakeBuildError(f"build_make: make_schema.mjs failed:\n{run.stderr}")
    return json.loads(run.stdout)


def start_state(manifest: dict, arrays: dict, schema: dict) -> dict:
    """The model's central state as a reader forecast; module docstring."""
    import score_forecasts
    roster = list(schema["x-seat-context"]["parties"])
    wards = _columns(manifest, "ward_winner")
    codes = manifest["ward_parties"]
    winners = np.asarray(arrays["ward_winner"], dtype=np.int64)
    counts = np.zeros((len(wards), len(roster)), dtype=np.int64)
    col = {p: j for j, p in enumerate(roster)}
    for k, code in enumerate(codes):
        counts[:, col[code]] = (winners == k).sum(axis=0)
    share_cols = _columns(manifest, "pr_share")
    keep = [j for j, c in enumerate(share_cols) if c in col]
    dropped = [c for c in share_cols if c not in col]
    if dropped != ["OTHER"]:
        raise MakeBuildError(f"build_make: the draws' pr_share carries {dropped} off the roster; "
                             "only OTHER is expected")
    shares = np.asarray(arrays["pr_share"], dtype=float)[:, keep]
    forecast = score_forecasts.model_forecast(
        counts.tolist(), roster, wards, shares.tolist(), [share_cols[j] for j in keep], schema)
    medians_sum = math.fsum(statistics.median(shares[:, j].tolist()) for j in range(shares.shape[1]))
    return {
        "ward_calls": forecast["ward_calls"],
        "combined_share": forecast["combined_share"],
        "rule": ("score_forecasts.model_forecast on the published draws: each ward's modal "
                 "winner; each party's median LIST-ballot share (pr_share; no combined share is "
                 "published), renormalised to 100"),
        "median_share_sum": round(medians_sum, 6),
    }


def forecast_data(draws: Path = DRAWS) -> dict:
    """Everything ``make/forecast.json`` carries."""
    import cityconfig
    manifest, arrays, raw = _draws(draws)
    pools_file = REPO_ROOT / "data" / "processed" / f"pools_{cityconfig.active().default_target}.json"
    total, total_src = total_votes(manifest, arrays, pools_file)
    roster = build_play.roster()
    geom = geometry()
    artefact = model_artefact(manifest, total, roster)
    schema = make_schema(artefact, geom)
    start = start_state(manifest, arrays, schema)
    ctx = schema["x-seat-context"]
    # What a link is read against: change any of these and an old link's
    # positions mean different parties, wards or votes (js/make-state.js).
    context_ref = _sha(json.dumps([ctx["parties"], ctx["wards"], schema["x-total-votes"]]).encode())[:12]
    return {
        "_about": ("Written by src/build_make.py from the published draws (site/draws/). "
                   "Do not edit."),
        "model_ref": artefact["model_ref"],
        "context_ref": context_ref,
        "draws_sha256": _sha(raw),
        "total_votes_source": total_src,
        "schema": schema,
        "geometry": {k: geom[k] for k in ("W", "H", "hex_radius", "labels", "wards")},
        "start": start,
    }


# --------------------------------------------------------------------------
# the page


def assemble(*, theme_head: str, nav: str, footer: str, stat_css: str, cut_markers) -> str:
    """The page's HTML, tokens unrendered: make.html with the site put in."""
    page = (INTERACTIVE / "make.html").read_text(encoding="utf-8")
    starts = page.count("<!-- __DEVONLY_START__ -->")
    if not starts or starts != page.count("<!-- __DEVONLY_END__ -->"):
        raise MakeBuildError("build_make: make.html's __DEVONLY__ markers do not pair")
    page = _DEVONLY.sub("", page)
    page = re.sub(r"<!--\n  \"Make your own forecast\".*?-->\n", "", page, count=1, flags=re.S)
    sheet = cut_markers(build_play.SHEET.read_text(encoding="utf-8"), None)
    for marker, value in (("<!-- __MAKEHEAD__ -->", theme_head),
                          ("<!-- __MAKENAV__ -->", build_play.one_level_down(nav)),
                          ("<!-- __MAKEFOOT__ -->", build_play.one_level_down(footer))):
        build_play._once(page, marker, "make.html")
        page = page.replace(marker, value)
    for host, names in HOSTS.items():
        marker = f"<!-- __PUBLISHED:{host}__ -->"
        build_play._once(page, marker, "make.html")
        page = page.replace(marker, build_play.published_host(sheet, names, stat_css))
    left = re.findall(r"<!-- __[A-Z:a-z]+__ -->", page)
    if left:
        raise MakeBuildError(f"build_make: unfilled markers in make.html: {left}")
    return page


def write_assets(out: Path) -> list[str]:
    """Copy everything the page loads into ``out/make/``; returns the paths written."""
    dest = out / MAKE_DIR
    if dest.exists():
        shutil.rmtree(dest)          # nothing under make/ survives a build that did not write it
    written = []

    def put(rel: str, data: bytes) -> None:
        f = dest / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_bytes(data)
        written.append(f"{MAKE_DIR}/{rel}")

    for name in MAKE_JS:
        data = (INTERACTIVE / "js" / name).read_bytes()
        if name == "seat-engine.js":
            text = data.decode("utf-8")
            build_play._once(text, SEATS_LINE[0], "js/seat-engine.js, the seats.js import")
            data = text.replace(SEATS_LINE[0], SEATS_LINE[1]).encode("utf-8")
        put(f"js/{name}", data)
    for name in WORKER_API_JS:
        put(f"js/{name}", (WORKER_SRC / name).read_bytes())
    for name in MAKE_CSS:
        put(f"css/{name}", (INTERACTIVE / "css" / name).read_bytes())
    for name in MAKE_PYBOOT:
        put(f"pyboot/{name}", (INTERACTIVE / "pyboot" / name).read_bytes())
    build_play.sync_python()
    manifest = json.loads((INTERACTIVE / "py" / "manifest.json").read_text(encoding="utf-8"))
    put("py/manifest.json", (INTERACTIVE / "py" / "manifest.json").read_bytes())
    for rel in manifest["files"]:
        put(f"py/{rel}", (INTERACTIVE / "py" / rel).read_bytes())
    put(DATA, (json.dumps(forecast_data(), indent=None, sort_keys=True,
                          separators=(",", ":")) + "\n").encode("utf-8"))
    return written
