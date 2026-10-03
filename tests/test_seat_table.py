"""The site's one seat table: the Python and JavaScript renderers write the same
markup for the same rows (owner's sweep, 2026-10-03).

`src/seat_table.py` draws the published tables at build time and
`interactive/js/seat-table.js` draws a reader's in the browser. A difference
between them is a page whose table changes look when a reader touches a
control, so the two are run on the same constructed rows and compared as
markup. The JS side runs under node against a minimal DOM (below) that
serialises elements the way the Python renderer writes them.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import skip  # noqa: E402

import seat_table as ST  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

#: Constructed rows covering every optional key: a range, no range, a range
#: withheld (``lo`` alone), a sub-label, a ghost mark, an arrow, a title, a
#: name that needs escaping, and a party with no colour of its own.
ROWS = [
    {"code": "DA", "name": "DA", "sub": None, "seats": "66", "lo": "45", "hi": "90",
     "m": 66, "p5": 45, "p95": 90, "ghost": 64, "arrow": "▲2", "title": None},
    {"code": "ALJAMAAH", "name": "Al Jama-ah & co", "sub": None, "seats": "2", "lo": "1", "hi": "6",
     "m": 2, "p5": 1, "p95": 6, "ghost": None, "arrow": None, "title": "2 wards, 0 list"},
    {"code": "NEWCO", "name": "New Co", "sub": None, "seats": "withheld", "lo": "withheld", "hi": None,
     "m": None, "p5": None, "p95": None, "ghost": None, "arrow": "▼1", "title": None},
    {"code": "OTHERS", "name": "Others", "sub": "(14 parties)", "seats": "23", "lo": None, "hi": None,
     "m": 23.5, "p5": None, "p95": None, "ghost": None, "arrow": None, "title": None},
]
OPTS = {"scale": 125, "ticks": [0, 25, 50, 75, 100, 125], "head": ["seats", "range"], "label": "Seats"}

#: A DOM just large enough for seat-table.js, serialising as src/seat_table.py
#: writes: attributes in the order set, `html.escape` rules, no void elements.
NODE = r"""
const esc = (s, q) => { s = String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  return q ? s.replace(/"/g, "&quot;").replace(/'/g, "&#x27;") : s; };
class El {
  constructor(tag) { this.tag = tag; this.attrs = []; this.kids = []; }
  setAttribute(k, v) { this.attrs.push([k, String(v)]); }
  append(...ks) { for (const k of ks) this.kids.push(k); }
  get outerHTML() {
    return "<" + this.tag + this.attrs.map(([k, v]) => " " + k + '="' + esc(v, true) + '"').join("") + ">" +
      this.kids.map(k => (k instanceof El ? k.outerHTML : esc(k, false))).join("") + "</" + this.tag + ">";
  }
}
const doc = { createElement: t => new El(t), createElementNS: (ns, t) => new El(t) };
const { seatTable } = await import(process.argv[1]);
const { rows, opts } = JSON.parse(process.argv[2]);
process.stdout.write(seatTable(doc, rows, opts).outerHTML);
"""


def _js(rows, opts) -> str:
    if not shutil.which("node"):
        skip("node is not installed")
    run = subprocess.run(
        ["node", "--input-type=module", "-e", NODE,
         (ROOT / "interactive" / "js" / "seat-table.js").as_uri(),
         json.dumps({"rows": rows, "opts": opts})],
        capture_output=True, text=True, cwd=ROOT)
    assert run.returncode == 0, run.stderr
    return run.stdout


def _py(rows, opts) -> str:
    # the Python renderer's cells are markup (tokens); the JS renderer's are
    # text. The constructed cells are plain, so the two read the same.
    return ST.table(rows, scale=opts["scale"], ticks=opts["ticks"], head=opts["head"],
                    label=opts["label"])


def test_python_and_javascript_write_the_same_table():
    py, js = _py(ROWS, OPTS), _js(ROWS, OPTS)
    assert py == js, "\n".join(["python: " + py, "js:     " + js])


def test_the_comparison_can_see_a_difference():
    # the detector: one row changed on one side only must not compare equal
    moved = [dict(ROWS[0], m=67)] + ROWS[1:]
    assert _py(moved, OPTS) != _js(ROWS, OPTS)
    assert _py(ROWS, OPTS) == _js(ROWS, OPTS)


def test_every_row_has_every_column_and_the_arrow_sits_in_the_seat_cell():
    html = _py(ROWS, OPTS)
    assert html.count('<div class="st-row" data-code=') == len(ROWS)
    for col in ("st-name", "st-graphic", "st-seats", "st-range"):
        assert html.count(f'<div class="{col}"') == len(ROWS) + (1 if col in ("st-seats", "st-range") else 0), col
    assert '<b>66<span class="arrow reader">▲2</span></b>' in html
    assert '<div class="st-range">45–90</div>' in html
    assert '<div class="st-range">withheld</div>' in html
    assert 'style=' not in html


def test_build_play_reads_back_the_rows_the_sheet_writes():
    import build_play
    rows = [{"code": "DA", "name": "DA", "seats": "{{@seats.DA.median=66;int;s}}",
             "lo": "{{@seats.DA.p5=45;int;s}}", "hi": "{{@seats.DA.p95=90;int;s}}",
             "m": 66, "p5": 45, "p95": 90},
            {"code": "OTHERS", "name": "Others", "seats": "{{@seats.OTHERS.median=23;int;s}}",
             "lo": "{{@seats.OTHERS.p5=8;int;s}}", "hi": "{{@seats.OTHERS.p95=47;int;s}}",
             "m": 23, "p5": 8, "p95": 47}]
    sheet = "<!-- __SEATS_START__ -->" + ST.table(rows) + "<!-- __SEATS_END__ -->"
    got = build_play.seat_rows(sheet)
    assert [(r["code"], r["name"], r["m"], r["lo"], r["hi"]) for r in got] == \
        [("DA", "DA", 66.0, 45.0, 90.0), ("OTHERS", "Others", 23.0, 8.0, 47.0)]
    assert got[0]["median"] == rows[0]["seats"] and got[1]["p95"] == rows[1]["hi"]
    # and the real sheet: one row per row it writes
    real = (ROOT / "forecast-sheet.html").read_text(encoding="utf-8")
    region = real[real.index("<!-- __SEATS_START__ -->"):real.index("<!-- __SEATS_END__ -->")]
    assert len(build_play.seat_rows(real)) == region.count('<div class="st-row" data-code=') > 0
