"""Section 1 of "your forecast" ("Adjust the model"): its published figures.

``src/build_your_forecast.py`` assembles the page (``/your-forecast/``) from
``interactive/your-forecast.html`` and copies its files; ``build_site.main``
renders, scans, stamps and ledgers it like every other page (INTEGRATION §3c).
This module fills section 1's ``<!-- __PLAY:<name>__ -->`` markers (:data:`FILL`)
and writes the data files section 1 reads; it decides nothing about what is
allowed on a page.

``parties.json``
    Party names, colours, the article a name takes in a sentence ("the
    ANC", "ActionSA") and whether the site has the party's logo, for the
    draws' roster, from the site's one definition (``render_sheet.NAMES`` /
    ``CHIPS``, then :func:`reader_name`), so the page types none.
``ward_paths.json``
    The ward boundaries (``render_map``'s ``ward_paths.json``: geometry and
    place labels, no figure). ``js/model.js`` draws the map under a reader's
    settings from it; the published map is drawn here (:func:`map_twin`).
``labels.json``
    The word list and number range of ``interactive/js/labels.js``, read by
    node, so the share sheet can offer a random label without importing a
    module that holds a data block.
``laws.json``
    The seat laws' names, as ``/forecast`` prints them
    (``render_sheet.SEAT_LAWS``, the one definition).

First paint is the published forecast AS TOKENS (DESIGN §4)
===========================================================

Every results element exists twice: a BUILD TWIN written here, whose figures
are ``{{…}}`` tokens that ``build_site`` renders with ``stats.render`` (so
each is ledgered, drift-checked and arrowed as on ``/forecast``), and an empty
LIVE sibling that ``js/model.js`` fills once a control moves. Nothing
from ``/forecast`` is embedded. The twins' figures come from:

* the seat rows and banner: the forecast sheet's own seat tokens
  (``forecast-sheet.html``'s ``__SEATS__`` region, ``render_sheet``'s
  ``seats.<P>.*``), so the untouched page is the forecast page's figures,
  drawn by the site's one seat table (``src/seat_table.py``; the reader's rows
  by its JS twin, ``js/seat-table.js``);
* the largest party, ties and a majority alone: ``reweight.largest_party``
  and ``reweight.majority_alone`` over ``seat_draws.csv``, the definitions
  ``render_sheet`` uses;
* the published map: ``render_map.ward_layers`` over ``ward_winner_probs.csv``,
  between ``__MAP_START__``/``__MAP_END__`` so the number scan lists its
  tooltips as generated, as on ``/forecast``;
* turnout by group, the line under the by-election control and its
  footnote: the published draws (``site/draws/``) through ``src/reweight.py``,
  the arithmetic the page itself runs;
* where each party's votes come from, and the new-party note:
  ``pools_<target>.json`` (``pools[g].members``, ``pool_shares_at_target``,
  ``no_measured_vector``), the spec the forecast consumed. NOT
  ``pools_<target>_simulation.json``, which carries a fifth bloc the forecast
  never reads.

Figures a reader's settings produce are NOT here: they are written at view
time into ``data-live`` regions by ``js/model.js``, and the share sheet
(region ``share``) by ``js/play-share.js`` through the one share sheet
(``js/share-sheet.js``), which shows an image that ``js/share-card.js`` (the
card module of both sections) draws from the same result as
``js/play-card.js`` words it (``stats.LIVE_WRITERS``);
``stats.script_writes`` holds each to that.

Share card and preview
======================

The page's own ``og:title``/``og:description``
(``build_your_forecast.OG_TITLE``, ``OG_DESCRIPTION``) carry no figure, and ``og:image`` is the site's
default share image (``og.png``). A link with settings in its query string gets the same generic
preview: nothing renders a card per link on the server. The image of a
reader's settings is drawn in their browser and attached or downloaded by
them.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INTERACTIVE = REPO_ROOT / "interactive"
SHEET = REPO_ROOT / "forecast-sheet.html"
DRAWS = REPO_ROOT / "site" / "draws"

#: The one line of the Worker that differs between the prototype and the site.
DRAWS_LINE = ('const DRAWS = "../../site/draws/";', 'const DRAWS = "../../draws/";')
#: The markers model.html carries, each filled by one function below.
FILL = ("banner", "oneline", "map", "seats", "turnout", "refused",
        "bye", "maxse", "largeparties", "election", "seatscale", "seatticks",
        "seathead")
#: How many parties the banner names, in the published order.
BANNER_PARTIES = 6
#: How a refused poll is described, by polling.screen's rule. A rule not here
#: is not a reason a reader of this cycle's polls needs (another city, another
#: election, after polling day).
REFUSED_AS = {"commissioned": "commissioned by a party or campaign",
              "no-city": "reporting several cities together",
              "under-min-n": "with too small a sample",
              "undated": "with no fieldwork date",
              "outside-window": "taken too long before polling day"}

_REL_ATTR = re.compile(r'\b(href|src)="(?![a-z][a-z0-9+.-]*:|/|#|\.\./)([^"]*)"', re.I)
#: A seat row of the forecast sheet's table (src/seat_table.py), read back by
#: its data attributes and its three token cells.
_SEAT_ROW = re.compile(
    r'<div class="st-row" data-code="([A-Z_]+)"[^>]*>'
    r'<div class="st-name"><span class="pchip pc-\1"></span>([^<]*)</div>'
    r'<div class="st-graphic">.*?</div>'
    r'<div class="st-seats"><b>(\{\{@seats\.\1\.median=([^;]*);[^}]*\}\})</b></div>'
    r'<div class="st-range">(\{\{@seats\.\1\.p5=([^;]*);[^}]*\}\})–(\{\{@seats\.\1\.p95=([^;]*);[^}]*\}\})</div></div>',
    re.S)


class PlayBuildError(SystemExit):
    """The page cannot be assembled; the message says what to do."""


def occurs_once(text: str, needle: str, what: str) -> int:
    """Where ``needle`` is in ``text``; refused unless it occurs exactly once.
    Shared with ``build_your_forecast`` (one definition)."""
    n = text.count(needle)
    if n != 1:
        raise PlayBuildError(f"build_play: {what}: {needle!r} occurs {n} times, not once")
    return text.index(needle)


def one_level_down(html: str) -> str:
    """Relative links and images, re-pointed from the site root to a page one level down."""
    return _REL_ATTR.sub(lambda m: f'{m.group(1)}="../{m.group(2)}"', html)


def _tok(name: str, value, fmt: str, source: str) -> str:
    """A generated token (``stats.GEN_TOKEN``): rendered, ledgered and scanned as one."""
    return f"{{{{@{name}={value};{fmt};{source}}}}}"


def _chance(name: str, value: float, source: str) -> str:
    return _tok(name, f"{float(value):.6f}", "chance", source)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _esc(s: str) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ==========================================================================
# what the twins are made of
# ==========================================================================

def seat_rows(sheet: str) -> list[dict]:
    """The forecast sheet's seat rows, in its order, each with its own tokens.

    ``code``, ``name``, the three token strings (``median``, ``p5``,
    ``p95``) and their pinned values (``m``, ``lo``, ``hi``). Refuses a sheet
    whose ``__SEATS__`` region it cannot read, rather than show fewer rows.
    """
    lo = occurs_once(sheet, "<!-- __SEATS_START__ -->", "the forecast sheet's seats region")
    hi = sheet.index("<!-- __SEATS_END__ -->", lo)
    region = sheet[lo:hi]
    rows = [{"code": m.group(1), "name": m.group(2),
             "median": m.group(3), "p5": m.group(5), "p95": m.group(7),
             "m": float(m.group(4)), "lo": float(m.group(6)), "hi": float(m.group(8))}
            for m in _SEAT_ROW.finditer(region)]
    if len(rows) != region.count('<div class="st-row" data-code=') or not rows:
        raise PlayBuildError("build_play: the forecast sheet's seat rows are not in the form "
                             "build_play reads (src/seat_table.py's row_html); fix one or the other")
    return rows


def _ordered(rows: list[dict]) -> list[dict]:
    """Party rows by middle seat count, then name (STYLE rule 7); Others last."""
    named = sorted((r for r in rows if r["code"] != "OTHERS"),
                   key=lambda r: (-round(r["m"]), r["name"].lower()))
    return named + [r for r in rows if r["code"] == "OTHERS"]


def _draws_cell(path: str = "."):
    import reweight as R
    d = DRAWS if path == "." else DRAWS / path
    man = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    return man, R.unpack((d / "base.bin").read_bytes(), man)


def _seat_draws(processed: Path):
    import numpy as np
    with (processed / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    parties = [k for k in rows[0] if k not in ("draw", "threshold", "council_size")]
    seats = np.array([[int(float(r[p] or 0)) for p in parties] for r in rows])
    thr = np.array([int(float(r["threshold"])) for r in rows])
    return parties, seats, thr


def roster_codes(manifest: dict) -> list[str]:
    """Every party the draws carry, in the draw file's column order: the
    columns of its ``ward_vote`` block, which is the run's whole universe
    (``export_draws``: no party summed or dropped), so a party on the ballot
    that never wins a seat is on it too. A ward-only party (a ward slate and no
    PR list, ``levels.Ballots.ward_only``, MODEL-LOG §1.306) is such a party:
    it carries ward votes, so the entry schema must name it, and since
    2026-10-16 the page's roster and the schema's ``parties`` are this list
    (``build_make.model_artefact``). ``manifest["parties"]`` is the seat
    blocks' columns, the seat-winning parties only; it is the answer for a
    manifest written before the vote blocks existed."""
    for block in manifest.get("blocks") or ():
        if block.get("name") == "ward_vote":
            return [str(c) for c in block["columns"]]
    return [str(c) for c in manifest.get("parties") or ()]


def roster() -> dict:
    """``{code: {name, colour, article, logo}}`` for every party the draws carry
    (:func:`roster_codes`).

    ``article`` is "the " for a name written as an abbreviation ("the ANC"),
    else empty ("ActionSA", "MK Party"): one rule, so the page types no list.
    """
    import render_sheet
    codes = list(render_sheet.NAMES)
    man = DRAWS / "manifest.json"
    if man.is_file():
        codes = roster_codes(json.loads(man.read_text(encoding="utf-8"))) or codes
    out = {}
    for c in codes:
        name = render_sheet.NAMES.get(c) or reader_name(c)
        out[c] = {"code": c, "name": name, "colour": render_sheet.CHIPS.get(c, render_sheet.OTHER_CHIP),
                  "article": "the " if name.isupper() else "",
                  # the site serves its logo (/logos/<code>.png, src/prep_logos.py)
                  "logo": (REPO_ROOT / "site" / "logos" / f"{c}.png").is_file()}
    return out


# The reader-facing name of a party the pages do not name by hand: one
# definition, in `render_map` (which the browser also runs), re-exported here
# for the callers that have always found it here.
from render_map import READER_NAMES, reader_name  # noqa: E402,F401


# ==========================================================================
# the twins
# ==========================================================================

def banner(rows: list[dict]) -> str:
    """The sticky banner's published seats: the first BANNER_PARTIES rows."""
    items = "".join(
        f'<span class="pl-bi"><i class="pc-{r["code"]}"></i>{_esc(r["name"])} <b>{r["median"]}</b></span>'
        for r in _ordered(rows) if r["code"] != "OTHERS")
    items = "".join(re.findall(r'<span class="pl-bi">.*?</b></span>', items)[:BANNER_PARTIES])
    return (f'<span class="pl-bitems">{items}</span>'
            f'<span class="pl-bmaj">Majority {{{{majority}}}}</span>')


def table_rows(rows: list[dict], others_sub: str | None = None) -> list[dict]:
    """The sheet's rows as rows of the site's seat table (src/seat_table.py),
    with their own tokens: the published panel on /play/ and /make/."""
    return [{"code": r["code"], "name": r["name"],
             "sub": others_sub if r["code"] == "OTHERS" else None,
             "seats": r["median"], "lo": r["p5"], "hi": r["p95"],
             "m": r["m"], "p5": r["lo"], "p95": r["hi"]} for r in rows]


def seats(rows: list[dict], others_count: str) -> str:
    """The published seat rows: the sheet's tokens, in the site's seat table."""
    import seat_table
    return seat_table.table(table_rows(_ordered(rows), f"({others_count} parties)"),
                            label="Seats in the published forecast")


def others_count(rows: list[dict]) -> str:
    """How many parties "Others" sums: those outside the published rows that win
    a seat in any simulation, counted as ``pyboot/page.py`` counts them."""
    man, arrays = _draws_cell(".")
    cols = next(b for b in man["blocks"] if b["name"] == "seats/deduct")["columns"]
    shown = {r["code"] for r in rows}
    block = arrays["seats/deduct"]
    n = sum(1 for j, c in enumerate(cols) if c not in shown and c != "OTHER" and block[:, j].max() > 0)
    return _tok("play.others_count", n, "int",
                "site/draws/base.bin, parties outside the named rows winning a seat in any simulation")


def oneline(processed: Path, names: dict) -> str:
    """The one-line result: the two parties most often alone with the most seats
    (alphabetical), ties, and a majority alone, by reweight's definitions."""
    import reweight as R
    parties, seats_, thr = _seat_draws(processed)
    lp = R.largest_party(seats_, parties)
    src = f"seat_draws.csv, {len(seats_):,} simulations"
    top = sorted(sorted(lp["outright"], key=lambda p: -lp["outright"][p])[:2],
                 key=lambda p: names[p]["name"].lower())

    def share(p):
        return _chance(f'play.largest.{p}', lp['outright'][p], src + ', the party alone with the most seats')

    def who(p, cap=False):
        nm = names[p]["article"] + _esc(names[p]["name"])
        return nm[:1].upper() + nm[1:] if cap else nm
    tied = _chance("play.largest_tied", lp["tied"], src + ", two or more parties level on the most seats")
    alone = _chance("play.alone", R.majority_alone(seats_, thr), src + ", one party at or above the threshold")
    # the site's one wording (play-card.js largestLine, model.js renderResult):
    # a chance, never "of simulations" (STYLE rule 10); note-browser says what
    # a chance is
    return (f"Most seats: {share(top[0])} chance it's {who(top[0])}, "
            f"{share(top[1])} chance it's {who(top[1])}. Two or more parties tie "
            f"for the most seats: {tied} chance. One party wins a majority on its own: {alone} chance.")


def map_twin(processed: Path, geometry: dict) -> str:
    """The published map, drawn by ``render_map.ward_layers`` (the forecast map's rule)."""
    import render_map as RM
    with (processed / "ward_winner_probs.csv").open(encoding="utf-8", newline="") as fh:
        calls = RM.probs_calls(csv.DictReader(fh))
    patterns, fills, hatches = RM.ward_layers(geometry["paths"], calls, prefix="pub")
    labels = "".join(f'<text x="{l["x"]}" y="{l["y"]}" text-anchor="middle" class="pl-maplabel">{_esc(l["t"])}</text>'
                     for l in geometry["labels"])
    w, h = geometry["W"], geometry["H"]
    return (f'{RM.MARK_START}<svg class="pl-wardmap" viewBox="0 0 {w:.0f} {h:.0f}" role="img" '
            f'aria-label="Johannesburg wards, north to the right, coloured by the party that wins each">'
            f'<defs>{patterns}</defs>{fills}{hatches}{labels}'
            f'<text x="{w - 14:.0f}" y="20" text-anchor="end" class="pl-north">N ↗</text></svg>{RM.MARK_END}')


def turnout() -> str:
    """Each group's published turnout: the mean of the draws' ``pool_turnout``."""
    man, arrays = _draws_cell(".")
    pools = next(b for b in man["blocks"] if b["name"] == "pool_turnout")["columns"]
    means = arrays["pool_turnout"].mean(axis=0)
    src = (f"site/draws/base.bin pool_turnout, mean of {int(man['draws']):,} simulations "
           f"(votes per registered voter in the group)")
    return "".join(
        f'<div class="pl-tslider"><div class="pl-tlab"><span>{_esc(g)}</span><span class="pl-tval">'
        f'{_tok(f"play.turnout.{_slug(g)}", f"{float(m):.6f}", "pct0", src)}</span></div>'
        f'<div class="pl-rail"><span class="pl-zero"></span><span class="pl-knob"></span></div></div>'
        for g, m in zip(pools, means))


def refused_polls() -> str:
    """The polls of this election the page does not offer, and why (``polling.screen``)."""
    import cityconfig
    import polling
    from datetime import date
    target = cityconfig.target()
    register = {p.get("id"): p for p in polling.load()}
    _, excluded = polling.screen(target)
    since = cityconfig.CALENDAR[target.previous_lge].date if target.previous_lge else date.min
    said = []
    for x in excluded:
        p = register.get(x.poll_id) or {}
        end = str(p.get("fieldwork_end") or "")
        if (x.rule in REFUSED_AS and str(p.get("target") or target.year) == str(target.year)
                and p.get("city") in (None, target.city.slug)
                and (not end or date.fromisoformat(end) > since)):
            said.append(REFUSED_AS[x.rule])
    if not said:
        return ""
    words = ["a poll " + s for s in said]
    return "Not offered: " + (words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]) + "."


def _bye_cells() -> tuple[dict, list[dict]]:
    """The index and its cells in ``export_draws.order_bye_cells``' order (by
    each cell's effective weight, not ``w_bye``, which the published cell
    leaves ``None``)."""
    import export_draws
    index = json.loads((DRAWS / "index.json").read_text(encoding="utf-8"))
    return index, export_draws.order_bye_cells(index["cells"])


def bye_ends(cells: list[dict]) -> list[tuple[str, dict]]:
    """The by-election control's two ends against the published cell, as
    ``(label, cell)``, the most weight first: the override cells at either end
    of ``cells`` (ordered by ``_bye_cells``), each labelled by which side of
    the published cell it sits. With the published cell tied at an end, that
    end is still the override cell, never the published one."""
    pub = next(i for i, c in enumerate(cells) if c["path"] == ".")
    others = [(i, c) for i, c in enumerate(cells) if c["path"] != "."]
    if not others:
        return []
    ends = [others[-1]] if len(others) == 1 else [others[-1], others[0]]
    return [("Fully" if i > pub else "Not at all", c) for i, c in ends]


def _cell_medians(path: str) -> tuple[dict, dict]:
    """``{party: (median, its sampling se)}`` under the published law, and the cell's centres."""
    import reweight as R
    man, arrays = _draws_cell(path)
    cols = next(b for b in man["blocks"] if b["name"] == "seats/deduct")["columns"]
    w = R.uniform(int(man["draws"]))
    out = {}
    for j, c in enumerate(cols):
        v = arrays["seats/deduct"][:, j].astype(float)
        if c != "OTHER" and v.max() > 0:
            out[c] = (R.weighted_quantile(v, w, 0.5), R.sampling_se(v, w, 0.5))
    return out, (man.get("centres") or {}).get("values") or {}


def _moves(cell: dict, pub: dict) -> list[tuple[str, int]]:
    """Each party's middle seat change against the published cell, rounded,
    where ``reweight.beyond_noise`` says it is more than sampling noise."""
    import reweight as R
    out = []
    for c in set(cell) | set(pub):
        a, b = cell.get(c, (0.0, 0.0)), pub.get(c, (0.0, 0.0))
        d = R.beyond_noise(a[0], a[1], b[0], b[1])
        if not d["within_noise"] and round(d["difference"]):
            out.append((c, int(round(d["difference"]))))
    return out


def bye_line(names: dict) -> str:
    """The line under the by-election control: each party's middle seat change
    at either end against the published weight, where it is larger than
    sampling noise. No party's move is explained here: the page explains every
    move or none (critic, 2026-10-02), and note 5 says why the cells differ."""
    index, cells = _bye_cells()
    pub, _ = _cell_medians(".")
    parts = []
    for label, c in bye_ends(cells):
        med, _ = _cell_medians(c["path"])
        mv = sorted(_moves(med, pub), key=lambda x: names.get(x[0], {"name": x[0]})["name"].lower())
        src = f"site/draws/{c['path']} against site/draws/., middle seats beyond sampling noise"
        said = ", ".join(f"{_esc(names.get(p, {'name': p})['name'])} {'+' if d > 0 else '−'}"
                         f"{_tok(f'play.bye.{_slug(c['path'])}.{p}', abs(d), 'int', src)}" for p, d in mv)
        parts.append(f"{label}: {said or 'no change larger than sampling noise'}.")
    return "Change in middle seat counts against the forecast. " + " ".join(parts)


_PROCESSED: Path | None = None


def _target_date() -> str:
    """The election being forecast, ISO 8601 (``cityconfig``'s calendar)."""
    import cityconfig
    return cityconfig.target().date.isoformat()


def _processed() -> Path:
    assert _PROCESSED is not None, "assemble() sets the processed directory first"
    return _PROCESSED


def fills(processed: Path) -> dict[str, str]:
    """Every ``<!-- __PLAY:<name>__ -->`` marker's content (:data:`FILL`)."""
    import reweight as R
    import seat_table
    global _PROCESSED
    _PROCESSED = processed
    sheet = SHEET.read_text(encoding="utf-8")
    rows = seat_rows(sheet)
    names = roster()
    geometry = json.loads((processed / "ward_paths.json").read_text(encoding="utf-8"))
    out = {
        "banner": banner(rows),
        "oneline": oneline(processed, names),
        "map": map_twin(processed, geometry),
        "seats": seats(rows, others_count(rows)),
        "turnout": turnout(),
        "refused": refused_polls(),
        "bye": bye_line(names),
        "maxse": _tok("play.max_figure_se", R.MAX_FIGURE_SE_SEATS, "one_dp",
                      "reweight.MAX_FIGURE_SE_SEATS, the owner's precision rule (JUDGEMENT-CALLS §N2)"),
        "largeparties": _tok("play.closeness_large_parties", R.CLOSENESS_LARGE_PARTIES, "int",
                             "reweight.CLOSENESS_LARGE_PARTIES, the parties that make the badge's "
                             "large-party mean (JUDGEMENT-CALLS §N10)"),
        # attribute values on two LIVE regions, read by js/model.js: the
        # election day (for the share image), and the seat table's axis, ticks
        # and header words (src/seat_table.py, the one definition)
        "election": _target_date(),
        "seatscale": str(seat_table.SEAT_SCALE),
        "seatticks": " ".join(str(x) for x in seat_table.SEAT_TICKS),
        "seathead": "|".join(seat_table.HEAD),
    }
    assert set(out) == set(FILL)
    return out


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


def labels_json() -> bytes:
    """``interactive/js/labels.js``'s words and number range, read by node."""
    src = (INTERACTIVE / "js" / "labels.js").as_uri()
    run = subprocess.run(
        ["node", "--input-type=module", "-e",
         f'const m = await import("{src}"); '
         f'console.log(JSON.stringify({{words: m.LABEL_WORDS, max: m.LABEL_MAX_NUMBER}}));'],
        cwd=REPO_ROOT, capture_output=True, text=True)
    if run.returncode:
        raise PlayBuildError(f"build_play: interactive/js/labels.js could not be read:\n{run.stderr}")
    return (run.stdout.strip() + "\n").encode("utf-8")


def ward_paths_json(processed: Path) -> bytes:
    """The ward boundaries and place labels, and the stripe tile
    (``render_map.toss_pattern``'s), for the map under a reader's settings."""
    import render_map as RM
    geometry = json.loads((Path(processed) / "ward_paths.json").read_text(encoding="utf-8"))
    return (json.dumps({"W": geometry["W"], "H": geometry["H"], "paths": geometry["paths"],
                        "places": geometry["labels"], "step": RM.TOSS_STEP, "rotate": RM.TOSS_ROTATE},
                       separators=(",", ":")) + "\n").encode("utf-8")


def laws_json() -> bytes:
    """``{law: {label, note}}`` from ``render_sheet.SEAT_LAWS``, in its order."""
    import html
    import render_sheet
    return (json.dumps({k: {"label": label, "note": html.unescape(note)}
                        for k, label, note in render_sheet.SEAT_LAWS}, indent=1) + "\n").encode("utf-8")


def roster_json() -> bytes:
    return (json.dumps(roster(), indent=1, sort_keys=True) + "\n").encode("utf-8")
