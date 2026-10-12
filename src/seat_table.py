"""The seat table: ONE component for every list of party seats on the site.

Owner's sweep, 2026-10-03: the seat rows were built five times, with five
different columns (`render_sheet`'s chart, `render_home`'s rows, `build_play`'s
published twin, `model.js` under a reader's settings and `make.js`'s council).
This module is the Python renderer, used by /forecast, the home page and the
published panels of /play/ and /make/. ``interactive/js/seat-table.js`` is the
JavaScript renderer, used where a reader's settings make the figures in the
browser. Both write the SAME markup for the same rows, and
``tests/test_seat_table.py`` holds them to it; the look is
``src/css/seat-table.css``.

The columns, in order: the party's chip and name; the range graphic (the band
from the low to the high end of the range and a mark at the middle, on one seat
axis); the middle seat count, in bold, with a fixed-width slot after it for an
arrow so an arrow never moves a number; the range as text. A header row names
every column and a scale row gives the axis.

A row is a dict with the same keys in both renderers:

``code``
    the party code: the chip's colour class ``pc-<code>`` (src/site_assets.py
    generates one per ``render_sheet.CHIPS`` entry) and ``data-code``.
``name``, ``sub``
    the label, as text, and an optional note after it ("(14 parties)").
``seats``, ``lo``, ``hi``
    the cell CONTENT of the middle and the two ends of the range. Here these
    are usually ``{{tokens}}``, which ``stats.render`` turns into ledgered
    figures, so they (and ``sub``) are written as given and never escaped.
    ``lo`` and ``hi`` of None leave the range cell empty (a single council has
    no range); ``lo`` alone is printed alone ("withheld"). The JS renderer
    writes all of them as text.
``m``, ``p5``, ``p95``
    the same three as numbers, for the graphic only (None draws nothing).
``ghost``
    a second mark, as a number: the published middle beside a reader's.
``arrow``
    the reader's change against the published forecast ("▲3"), or None.
``title``
    a tooltip on the seat count, or None.

Nothing here computes a figure or names a token: the caller does both, so each
page keeps the token names its ledger rows were published under.
"""
from __future__ import annotations

from html import escape

#: The seat axis, in seats, for every seat table on the site. The JS renderer
#: takes it from the table's own ``data-scale``.
SEAT_SCALE = 125
#: The scale row's ticks.
SEAT_TICKS = (0, 25, 50, 75, 100, 125)
#: The header row's words, one per column (owner's list, 2026-10-03, item 4):
#: the party, the range graphic, the middle seat count, the range as text.
HEAD = ("party", "middle and range", "seats", "range")
#: A single council's (/your-forecast/ section 2): its mark is the party's
#: seats on the axis, and it has no range (one council, not simulations), so
#: the range column carries no heading and css/seat-table.css folds it into
#: the seats column.
HEAD_COUNCIL = ("party", "on the seat scale", "seats", "")


def _pct(v: float, scale: float) -> str:
    return f"{100.0 * float(v) / scale:.2f}%"


def _attrs(pairs) -> str:
    return "".join(f' {k}="{escape(str(v), quote=True)}"' for k, v in pairs)


def graphic(row: dict, scale: float | None = None) -> str:
    """The range graphic: an SVG whose geometry is attributes, so the page
    carries no style. Percent coordinates need no viewBox and draw the marks
    at their own pixel widths whatever the column's width."""
    scale = SEAT_SCALE if scale is None else scale
    parts = ['<line class="st-axis" x1="0" x2="100%" y1="10" y2="10"></line>']
    if row.get("p5") is not None and row.get("p95") is not None:
        parts.append(f'<rect class="st-band" x="{_pct(row["p5"], scale)}" y="6" '
                     f'width="{_pct(float(row["p95"]) - float(row["p5"]), scale)}" '
                     f'height="8" rx="4"></rect>')
    if row.get("ghost") is not None:
        x = _pct(row["ghost"], scale)
        parts.append(f'<line class="st-ghost" x1="{x}" x2="{x}" y1="0" y2="20"></line>')
    if row.get("m") is not None:
        x = _pct(row["m"], scale)
        parts.append(f'<line class="st-med" x1="{x}" x2="{x}" y1="2" y2="18"></line>')
    return ('<svg class="st-svg" width="100%" height="20" aria-hidden="true">'
            + "".join(parts) + "</svg>")


def row_html(row: dict, scale: float | None = None) -> str:
    """One party's row."""
    scale = SEAT_SCALE if scale is None else scale
    data = [("class", "st-row"), ("data-code", row["code"])]
    data += [(f"data-{k}", row[k]) for k in ("m", "p5", "p95") if row.get(k) is not None]
    sub = f'<span class="st-sub">{row["sub"]}</span>' if row.get("sub") else ""
    name = (f'<div class="st-name"><span class="pchip pc-{escape(row["code"])}"></span>'
            f'{escape(row["name"], quote=False)}{sub}</div>')
    arrow = (f'<span class="arrow reader">{escape(row["arrow"], quote=False)}</span>'
             if row.get("arrow") else "")
    title = _attrs([("title", row["title"])]) if row.get("title") else ""
    seats = f'<div class="st-seats"{title}><b>{row["seats"]}{arrow}</b></div>'
    lo, hi = row.get("lo"), row.get("hi")
    rng = f"{lo}–{hi}" if lo is not None and hi is not None else "" if lo is None else f"{lo}"
    return (f"<div{_attrs(data)}>{name}"
            f'<div class="st-graphic">{graphic(row, scale)}</div>'
            f'{seats}<div class="st-range">{rng}</div></div>')


def head_html(head=None) -> str:
    """The header row: a word over each column."""
    head = HEAD if head is None else head
    return ('<div class="st-row st-head">'
            f'<div class="st-name">{escape(head[0])}</div>'
            f'<div class="st-graphic">{escape(head[1])}</div>'
            f'<div class="st-seats">{escape(head[2])}</div>'
            f'<div class="st-range">{escape(head[3])}</div></div>')


def scale_html(scale: float | None = None, ticks=None) -> str:
    """The axis under the rows. Its numbers sit in a ``ticks`` element, which
    the number scan lists as chart chrome (``stats.CHROME_CLASSES``)."""
    scale = SEAT_SCALE if scale is None else scale
    ticks = SEAT_TICKS if ticks is None else ticks
    def anchor(i: int) -> str:
        return "start" if i == 0 else "end" if i == len(ticks) - 1 else "middle"
    texts = "".join(f'<text x="{_pct(t, scale)}" y="11" text-anchor="{anchor(i)}">{t}</text>'
                    for i, t in enumerate(ticks))
    return ('<div class="st-row st-scale"><div></div>'
            f'<svg class="ticks st-ticks" width="100%" height="14" aria-hidden="true">{texts}</svg>'
            '<div></div><div></div></div>')


def table(rows: list[dict], *, scale: float | None = None, ticks=None, head=None,
          label: str | None = None) -> str:
    """The whole table: header, one row per party in the order given, scale."""
    scale = SEAT_SCALE if scale is None else scale
    ticks = SEAT_TICKS if ticks is None else ticks
    head = HEAD if head is None else head
    aria = _attrs([("aria-label", label)]) if label else ""
    return (f'<div class="st" data-scale="{scale:g}"{aria}>' + head_html(head)
            + "".join(row_html(r, scale) for r in rows) + scale_html(scale, ticks) + "</div>")
