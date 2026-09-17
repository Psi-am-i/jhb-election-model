"""An equal-area hex tile cartogram: one hexagon per ward, one ward per hexagon.

WHY THIS EXISTS
---------------
The geographic choropleth in ``render_map.py`` is honest about *where* and
dishonest about *how many*. Johannesburg's wards are drawn to hold roughly
equal population, and each returns exactly one councillor, so ward **area
carries no information** -- but area is what the eye reads. The wards the DA
wins are large, low-density and northern; the wards the ANC and MK win are
small and dense. Measured on the committed inputs the DA takes about 1.6x its
seat share of the map's ink and MK about a fifth of its own, so the picture
contradicts the headline on the same page. ``PUBLISHING-BACKLOG.md`` §7 states
the problem; ``MODEL-LOG.md`` §1.90 records the measurement.

A hex tile cartogram is the honest picture *for this quantity*: every ward gets
an identical hexagon, so ink share equals seat share by construction, and each
hexagon is placed near the ward's real centroid so the geography survives in
outline. It does not replace the geographic map -- it answers the other
question. Show both.

THE MECHANISM
-------------
1. **Centroids.** ``data/processed/ward_paths.json`` already holds every ward
   as an SVG path in *screen* coordinates -- projected, rotated and scaled
   exactly as the geographic map draws it. The path grammar there is only
   ``M``/``L``/``Z`` with absolute coordinates, so it parses without a
   geometry library. Each ward's polygon area and area-weighted centroid come
   from the shoelace formula, with the largest subpath's winding taken as the
   exterior orientation so interior rings (holes) subtract rather than add.

2. **The grid.** Pointy-top hexagons on an offset row grid. The circumradius is
   chosen so that ``N`` hexagons have the same total area as the city itself
   (``R = sqrt(A_city / N / (3*sqrt(3)/2))``), which makes the cartogram occupy
   roughly the real silhouette -- the two maps then overlay, which is what makes
   a toggle between them legible. Candidate cells cover the wards' bounding box
   plus a two-cell margin; there are more cells than wards, and the unused ones
   are simply not drawn.

3. **The assignment.** Choosing which ward goes in which cell is a rectangular
   linear assignment problem: minimise the total squared displacement between
   ward centroids and cell centres. ``scipy`` is not installed here, so
   :func:`assign_optimal` is a numpy implementation of the Jonker-Volgenant
   shortest-augmenting-path algorithm (the e-maxx Hungarian formulation) with
   its inner loops vectorised -- O(n^2 m), a few hundred milliseconds at
   135x~450. :func:`assign_greedy` is the cheap alternative the backlog
   allowed: outermost ward first, nearest free cell. Both are deterministic;
   the optimal one is the default because it is measurably better and the cost
   is invisible (see MODEL-LOG §1.90 for the two displacement numbers).

4. **The rendering.** Same visual language as the geographic map, deliberately:
   the same party colours, the same four confidence tiers (Safe >=90% solid,
   Strongly leaning 75-90% finely hatched, Leaning 60-75% heavily hatched,
   Toss-up <60% grey), the same challenger-coloured hatch patterns, the same
   district labels and the same tooltip text. The colours are *imported* from
   ``render_map`` rather than copied. The tier thresholds cannot be imported --
   they are inline in that module's ``main`` -- so
   ``tests/test_hex_cartogram.py`` reads ``render_map.py``'s source and fails if
   the two drift apart.

The snippet is written between ``__HEXMAP_START__``/``__HEXMAP_END__``, a
distinct marker pair from the geographic map's, so both can sit on one page.

Usage:
    .venv/bin/python src/hex_cartogram.py                  # preview + layout + table
    .venv/bin/python src/hex_cartogram.py --assign greedy  # the cheap layout
    .venv/bin/python src/hex_cartogram.py --into forecast-sheet.html
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np

from render_map import CHIPS, GREY, NAMES

MARK_START = "<!-- __HEXMAP_START__ -->"
MARK_END = "<!-- __HEXMAP_END__ -->"

# Tier thresholds. These are NOT free parameters -- they are the geographic
# map's, and tests/test_hex_cartogram.py asserts they still are.
# Tiers, floors and the drawing rule are render_map's — imported, never copied.
from render_map import SAFE, TIP_FLOOR, OTHER_FLOOR, ward_call, ward_hatch, map_key  # noqa: E402

# Hexagon area as a multiple of (city area / ward count). 1.0 makes the tiles
# cover the real silhouette; smaller values loosen the packing and shorten the
# displacements at the cost of a sparser picture. Declared, not measured --
# JUDGEMENT-CALLS.md.
CELL_AREA_FACTOR = 1.0
GRID_MARGIN_CELLS = 2     # candidate cells beyond the wards' bounding box

_NUM = re.compile(r"-?\d+(?:\.\d+)?")


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def parse_path(d: str) -> list[list[tuple[float, float]]]:
    """Split an ``M x y L x y ... Z`` path into its rings.

    ``ward_paths.json`` is written by ``render_map.py`` and uses no other
    commands and no relative coordinates, so this is a complete parser for that
    file and for nothing else.
    """
    rings: list[list[tuple[float, float]]] = []
    for chunk in d.split("M"):
        chunk = chunk.strip().rstrip("Z").strip()
        if not chunk:
            continue
        nums = [float(x) for x in _NUM.findall(chunk)]
        rings.append(list(zip(nums[0::2], nums[1::2])))
    return rings


def _ring_moments(pts: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Signed area and first moments of one closed ring (shoelace)."""
    a = cx = cy = 0.0
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    return a / 2.0, cx / 6.0, cy / 6.0


def polygon_area_centroid(d: str) -> tuple[float, float, float]:
    """Area and area-weighted centroid of a multi-ring SVG path.

    The ring with the largest magnitude is taken to be the exterior, and its
    winding fixes the sign, so holes subtract. (Every Johannesburg ward comes
    out positive under that rule -- checked -- but a ward that enclosed another
    would not without it.)
    """
    rings = parse_path(d)
    moments = [_ring_moments(p) for p in rings]
    biggest = max(range(len(moments)), key=lambda i: abs(moments[i][0]))
    sign = 1.0 if moments[biggest][0] > 0 else -1.0
    area = sum(m[0] for m in moments) * sign
    mx = sum(m[1] for m in moments) * sign
    my = sum(m[2] for m in moments) * sign
    if area == 0.0:                                   # degenerate: fall back
        pts = rings[biggest]
        return 0.0, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    return area, mx / area, my / area


def hex_vertices(cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    """The six corners of a pointy-top hexagon of circumradius ``r``."""
    return [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
            for a in (-90, -30, 30, 90, 150, 210)]


def hex_grid(xs: np.ndarray, ys: np.ndarray, r: float,
             margin: int | None = None) -> np.ndarray:
    """Candidate cell centres covering the points' bounding box, plus a margin.

    `margin` RESOLVES AT CALL TIME. It was `margin: int = GRID_MARGIN_CELLS`,
    which freezes the constant at import — the `LEVEL_DF` shape, and the fourth
    instance in this repository. `test_no_numeric_module_constant_is_a_default
    _argument` caught it the same day. MODEL-LOG §1.89.

    Pointy-top offset rows: horizontal pitch ``sqrt(3) r``, vertical pitch
    ``1.5 r``, odd rows shifted half a pitch right. Returned in row-major
    order, which is what makes the assignment's tie-breaks reproducible.
    """
    if margin is None:
        margin = GRID_MARGIN_CELLS
    dx = math.sqrt(3.0) * r
    dy = 1.5 * r
    x0 = float(xs.min()) - margin * dx
    y0 = float(ys.min()) - margin * dy
    ncol = int(math.ceil((float(xs.max()) - x0) / dx)) + margin + 1
    nrow = int(math.ceil((float(ys.max()) - y0) / dy)) + margin + 1
    cells = [(x0 + c * dx + (row % 2) * dx / 2.0, y0 + row * dy)
             for row in range(nrow) for c in range(ncol)]
    return np.asarray(cells, dtype=float)


# --------------------------------------------------------------------------
# assignment
# --------------------------------------------------------------------------

def assign_optimal(cost: np.ndarray) -> np.ndarray:
    """Minimum-cost assignment of every row to a distinct column.

    Jonker-Volgenant / Hungarian with potentials (the e-maxx formulation),
    rectangular with ``n <= m``, inner loops vectorised over columns. Returns
    an array of column indices, one per row.

    ``scipy.optimize.linear_sum_assignment`` would do this in one line, and
    scipy is not a dependency of this repository -- adding one for a
    presentation feature is not a trade worth making, and the algorithm is
    forty lines. ``tests/test_hex_cartogram.py`` checks it against brute force
    on small random matrices.

    Ties are broken by lowest column index (``argmin``), so the result is a
    deterministic function of the cost matrix even where the optimum is not
    unique.
    """
    cost = np.asarray(cost, dtype=float)
    n, m = cost.shape
    if n > m:
        raise ValueError(f"need at least as many cells as wards ({n} > {m})")
    u = np.zeros(n + 1)
    v = np.zeros(m + 1)
    p = np.zeros(m + 1, dtype=np.int64)      # p[j] = 1-based row filling col j
    way = np.zeros(m + 1, dtype=np.int64)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = np.full(m + 1, np.inf)
        used = np.zeros(m + 1, dtype=bool)
        while True:
            used[j0] = True
            i0 = int(p[j0])
            free = ~used[1:]
            cur = cost[i0 - 1] - u[i0] - v[1:]
            better = free & (cur < minv[1:])
            minv[1:][better] = cur[better]
            way[1:][better] = j0
            candidates = np.where(free, minv[1:], np.inf)
            k = int(np.argmin(candidates))
            delta = float(candidates[k])
            j1 = k + 1
            np.add.at(u, p[used], delta)     # p[j] is distinct across used j
            v[used] -= delta
            minv[~used] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = int(way[j0])
            p[j0] = p[j1]
            j0 = j1
    out = np.full(n, -1, dtype=np.int64)
    for j in range(1, m + 1):
        if p[j]:
            out[p[j] - 1] = j - 1
    return out


def assign_greedy(cost: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Outermost ward first, nearest free cell. The cheap alternative.

    Kept because the backlog allowed it and because it is the honest baseline
    the optimal assignment has to beat -- see MODEL-LOG §1.90 for by how much.
    Outermost first because the periphery has the least freedom: served last,
    it ends up flung well past the edge of the city.
    """
    centre = points.mean(axis=0)
    order = np.argsort(-np.hypot(*(points - centre).T), kind="stable")
    taken = np.zeros(cost.shape[1], dtype=bool)
    out = np.full(cost.shape[0], -1, dtype=np.int64)
    for i in order:
        row = np.where(taken, np.inf, cost[i])
        j = int(np.argmin(row))
        taken[j] = True
        out[i] = j
    return out


# --------------------------------------------------------------------------
# layout
# --------------------------------------------------------------------------

class Layout:
    """A ward -> hexagon placement, plus everything measured on the way."""

    def __init__(self, cells: dict[str, tuple[float, float]], radius: float,
                 centroids: dict[str, tuple[float, float]],
                 areas: dict[str, float], width: float, height: float,
                 labels: list[dict], method: str):
        self.cells = cells
        self.radius = radius
        self.centroids = centroids
        self.areas = areas
        self.width = width
        self.height = height
        self.labels = labels
        self.method = method

    @property
    def wards(self) -> list[str]:
        return list(self.cells)

    def displacements(self) -> np.ndarray:
        return np.array([math.dist(self.cells[w], self.centroids[w])
                         for w in self.cells])


def ward_geometry(paths: dict[str, str]) -> tuple[dict, dict]:
    """Area and centroid per ward, in the geographic map's screen coordinates."""
    areas, centroids = {}, {}
    for ward in sorted(paths, key=_ward_key):
        a, cx, cy = polygon_area_centroid(paths[ward])
        areas[ward] = a
        centroids[ward] = (cx, cy)
    return areas, centroids


def _ward_key(ward: str):
    """Sort wards numerically where possible. Fixes the iteration order, and
    with it every tie-break and the byte order of the emitted SVG."""
    return (0, int(ward), "") if ward.isdigit() else (1, 0, ward)


def build_layout(ward_paths: dict, method: str = "optimal",
                 area_factor: float | None = None) -> Layout:
    """Place every ward on its own hexagon. Deterministic.

    `area_factor` RESOLVES AT CALL TIME, for the reason given on `hex_grid`.
    """
    if area_factor is None:
        area_factor = CELL_AREA_FACTOR
    paths = ward_paths["paths"]
    areas, centroids = ward_geometry(paths)
    wards = sorted(paths, key=_ward_key)
    pts = np.array([centroids[w] for w in wards], dtype=float)

    city_area = sum(areas.values())
    hex_area = city_area / len(wards) * area_factor
    radius = math.sqrt(hex_area / (1.5 * math.sqrt(3.0)))

    cells = hex_grid(pts[:, 0], pts[:, 1], radius)
    diff = pts[:, None, :] - cells[None, :, :]
    cost = (diff ** 2).sum(axis=2)           # squared displacement

    if method == "optimal":
        idx = assign_optimal(cost)
    elif method == "greedy":
        idx = assign_greedy(cost, pts)
    else:
        raise ValueError(f"unknown assignment method {method!r}")

    placed = {w: (float(cells[j][0]), float(cells[j][1]))
              for w, j in zip(wards, idx)}
    return Layout(placed, radius, centroids, areas,
                  float(ward_paths["W"]), float(ward_paths["H"]),
                  list(ward_paths.get("labels", [])), method)


# --------------------------------------------------------------------------
# the tier language, shared with the geographic map
# --------------------------------------------------------------------------

def classify(row: dict) -> dict:
    """One ward's fill, class, tooltip and bands — ``render_map.ward_call``."""
    return ward_call(row["ward"], row["winner"], float(row["p_win"]), row["dist"])


def _luminance(hex_colour: str) -> float:
    r, g, b = (int(hex_colour[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def render(layout: Layout, probs: dict[str, dict], city_name: str = "the city") -> str:
    """The inline-SVG snippet, between __HEXMAP_START__/__HEXMAP_END__.

    Deterministic: the ward order is fixed by :func:`_ward_key`, every
    coordinate is formatted to one decimal, and the pattern dictionary is
    filled in that same order.
    """
    r = layout.radius
    W, H = layout.width, layout.height
    patterns: dict[str, str] = {}
    tiles, hatches, numbers = [], [], []
    called = {"solid": 0, "contested": 0}

    # ONE hexagon, defined once at the origin and <use>d 135 times. Not a size
    # optimisation: emitting 135 separate <polygon>s with coordinates rounded
    # for legibility made the tiles differ in area by ~1e-2 px^2, and
    # test_every_hexagon_is_identical_and_none_overlap caught it. A shared
    # shape makes "every ward is drawn the same size" true by construction
    # instead of true to a tolerance -- which is the entire claim of the
    # figure, so it should not rest on a rounding argument.
    cell = " ".join(f"{x:.6f},{y:.6f}" for x, y in hex_vertices(0.0, 0.0, r))

    for ward in layout.wards:
        cx, cy = layout.cells[ward]
        row = probs.get(ward)
        if row is None:
            info = {"fill": GREY, "cls": "contested", "bands": [], "tip": f"Ward {ward}"}
        else:
            info = classify(row)
        called[info["cls"]] += 1
        at = f'x="{cx:.1f}" y="{cy:.1f}"'
        tiles.append(f'<use href="#hexcell" xlink:href="#hexcell" {at} '
                     f'fill="{info["fill"]}" stroke="var(--paper)" '
                     f'stroke-width="1.2" data-tip="{info["tip"]}"></use>')
        pid = ward_hatch(info, patterns)
        if pid:
            hatches.append(f'<use href="#hexcell" xlink:href="#hexcell" {at} '
                           f'fill="url(#{pid})" pointer-events="none"></use>')
        # Ward numbers where they fit: the hexagon's inradius must clear the
        # glyphs. At the default radius all 135 fit; a smaller area factor
        # drops the widest ones rather than overprinting them.
        size = max(7.0, min(11.0, r * 0.42))
        if r * math.sqrt(3.0) / 2.0 >= size * 0.32 * len(ward) + 2.0:
            ink = "#ffffff" if _luminance(info["fill"]) < 0.55 else "#12140f"
            numbers.append(
                f'<text x="{cx:.1f}" y="{cy + size * 0.35:.1f}" text-anchor="middle" '
                f'style="font:600 {size:.1f}px ui-monospace,monospace;fill:{ink};'
                f'opacity:.85;pointer-events:none">{ward}</text>')

    labels = []
    for lab in layout.labels:
        labels.append(
            f'<text x="{lab["x"]}" y="{lab["y"]}" text-anchor="middle" '
            f'style="font:650 11px ui-sans-serif,system-ui;letter-spacing:.08em;'
            f'text-transform:uppercase;fill:var(--ink);stroke:var(--paper);'
            f'stroke-width:3px;paint-order:stroke;pointer-events:none">{lab["t"]}</text>')
    labels.append(
        f'<text x="{W - 14:.0f}" y="20" text-anchor="end" '
        f'style="font:600 11px ui-monospace,monospace;fill:var(--ink-3);'
        f'pointer-events:none">N ↗</text>')
    labels.append(
        '<text x="8" y="16" style="font:650 10.5px ui-sans-serif,system-ui;'
        'letter-spacing:.1em;text-transform:uppercase;fill:var(--ink-3);'
        'pointer-events:none">One hexagon = one ward = one councillor</text>')

    tier_key = map_key(called)

    return f"""{MARK_START}
  <details class="rollup" data-band="forecast" data-map="cartogram" open style="display:none">
    <summary><span class="eyebrow">The same forecast, drawn by seats instead of by land</span>
    <h2>Who wins how many</h2></summary>
    <div class="maptoggle" style="display:flex;gap:6px;margin:4px 0 10px;font-size:13px">
      <button type="button" data-show="geo" aria-pressed="false">By land area</button>
      <button type="button" data-show="cartogram" aria-pressed="true">Every ward the same size</button>
    </div>
    <figure>
      <div style="position:relative">
      <svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" id="wardhexmap"
           xmlns:xlink="http://www.w3.org/1999/xlink"
           aria-label="{city_name} ward cartogram: one equal hexagon per ward, placed near its real location and coloured by predicted winning party"
           style="width:100%;height:auto;display:block">
        <defs><polygon id="hexcell" points="{cell}"/>{''.join(patterns.values())}</defs>
        {''.join(tiles)}{''.join(hatches)}{''.join(numbers)}{''.join(labels)}
      </svg>
      <div id="hextip" style="position:fixed;display:none;pointer-events:none;z-index:9;
        font:12px/1.4 ui-sans-serif,system-ui;background:var(--ink);color:var(--paper);
        padding:6px 10px;border-radius:4px;max-width:280px"></div>
      </div>
      <figcaption style="display:flex;flex-direction:column;gap:6px">
        <span>{tier_key}</span>
        <span>Every ward elects one councillor, so on this map every ward is the same
        size — each hexagon sits as close to its ward's real position as the grid
        allows. The geographic map above answers <em>where</em>; this one answers
        <em>how many</em>. Touch or hover any
        hexagon for its numbers.</span>
      </figcaption>
    </figure>
    <script>
    (function() {{
      var tip = document.getElementById('hextip');
      var svg = document.getElementById('wardhexmap');
      function show(e) {{
        var t = e.target.getAttribute && e.target.getAttribute('data-tip');
        if (t) {{ tip.textContent = t; tip.style.display = 'block';
          tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 14) + 'px';
        }} else tip.style.display = 'none';
      }}
      svg.addEventListener('mousemove', show);
      svg.addEventListener('click', show);
      svg.addEventListener('mouseleave', function() {{ tip.style.display = 'none'; }});
    }})();
    </script>
  </details>
  {MARK_END}"""


# --------------------------------------------------------------------------
# the measurement this whole thing exists for
# --------------------------------------------------------------------------

def ink_table(areas: dict[str, float], probs: dict[str, dict]) -> dict:
    """Seat share against ink share, per party. The distortion table.

    ``areas`` is whatever the map actually draws -- real ward polygons for the
    choropleth, identical hexagons for the cartogram -- so the same function
    measures both, and the point of the exercise is that on the second one
    every ratio is 1.
    """
    total = sum(areas.values())
    n = len(areas)
    rows: dict[str, dict] = {}
    for ward, area in areas.items():
        row = probs.get(ward)
        winner = row["winner"] if row else "UNKNOWN"
        r = rows.setdefault(winner, {"wards": 0, "ink": 0.0})
        r["wards"] += 1
        r["ink"] += area
    for party, r in rows.items():
        r["seat_share"] = r["wards"] / n
        r["ink_share"] = r["ink"] / total
        r["distortion"] = r["ink_share"] / r["seat_share"]
    return dict(sorted(rows.items(), key=lambda kv: -kv[1]["wards"]))


def format_table(title: str, table: dict) -> str:
    out = [title, f"{'party':<10}{'wards':>7}{'seat %':>9}{'ink %':>9}{'distortion':>12}"]
    for party, r in table.items():
        out.append(f"{party:<10}{r['wards']:>7}{r['seat_share']*100:>9.1f}"
                   f"{r['ink_share']*100:>9.1f}{r['distortion']:>11.2f}x")
    return "\n".join(out)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

PREVIEW = """<!doctype html><meta charset="utf-8"><title>Ward cartogram preview</title>
<style>:root{{--paper:#fbfaf7;--ink:#12140f;--ink-3:#6b6f66}}
body{{background:var(--paper);color:var(--ink);margin:0;padding:28px;
font:16px/1.5 ui-sans-serif,system-ui;max-width:1000px}}
figcaption{{color:var(--ink-3);font-size:13px;margin-top:10px}}
summary h2{{margin:.2em 0}} .eyebrow{{color:var(--ink-3);font-size:12px;
letter-spacing:.1em;text-transform:uppercase}}</style>
{snippet}
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", type=Path,
                        default=Path("data/processed/ward_paths.json"))
    parser.add_argument("--probs", type=Path,
                        default=Path("data/processed/ward_winner_probs.csv"))
    parser.add_argument("--assign", choices=("optimal", "greedy"), default="optimal")
    parser.add_argument("--area-factor", type=float, default=CELL_AREA_FACTOR)
    parser.add_argument("--preview", type=Path, default=Path("drafts/hex-cartogram.html"))
    parser.add_argument("--layout-out", type=Path,
                        default=Path("data/processed/ward_hex_layout.json"))
    parser.add_argument("--into", type=Path, default=None,
                        help="splice the snippet into this page's __HEXMAP_ markers")
    args = parser.parse_args(argv)

    ward_paths = json.loads(args.paths.read_text(encoding="utf-8"))
    with args.probs.open(encoding="utf-8", newline="") as fh:
        probs = {r["ward"]: r for r in csv.DictReader(fh)}

    layout = build_layout(ward_paths, method=args.assign, area_factor=args.area_factor)
    snippet = render(layout, probs)

    hex_area = 1.5 * math.sqrt(3.0) * layout.radius ** 2
    before = ink_table(layout.areas, probs)
    after = ink_table({w: hex_area for w in layout.wards}, probs)
    print(format_table("geographic choropleth — ink by real ward area", before))
    print()
    print(format_table("hex cartogram — ink by hexagon", after))
    disp = layout.displacements()
    print(f"\nassignment: {layout.method}  ·  radius {layout.radius:.2f}px  ·  "
          f"displacement mean {disp.mean():.1f}px, median "
          f"{float(np.median(disp)):.1f}px, max {disp.max():.1f}px")

    if args.layout_out:
        args.layout_out.parent.mkdir(parents=True, exist_ok=True)
        args.layout_out.write_text(json.dumps({
            "W": layout.width, "H": layout.height, "radius": layout.radius,
            "method": layout.method, "area_factor": args.area_factor,
            "cells": {w: [round(x, 3), round(y, 3)]
                      for w, (x, y) in layout.cells.items()},
        }, separators=(",", ":"), sort_keys=False), encoding="utf-8")
        print(f"  layout into {args.layout_out}")

    if args.preview:
        args.preview.parent.mkdir(parents=True, exist_ok=True)
        args.preview.write_text(PREVIEW.format(snippet=snippet), encoding="utf-8")
        print(f"  preview into {args.preview}")

    if args.into:
        t = args.into.read_text(encoding="utf-8")
        if MARK_START not in t:
            print(f"  ! no {MARK_START} in {args.into}; nothing spliced")
            return 1
        start = t.index(MARK_START)
        end = t.index(MARK_END) + len(MARK_END)
        args.into.write_text(t[:start] + snippet + t[end:], encoding="utf-8")
        print(f"  cartogram into {args.into}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
