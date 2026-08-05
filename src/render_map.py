"""Render the ward-winner map into the forecast pages.

Reads ward_winner_probs.csv (written by every Monte Carlo run) and the MDB
2026 ward boundaries, and writes an inline SVG choropleth between the
__MAP_START__/__MAP_END__ markers of forecast-sheet.html and
drafts/forecast-draft.html.

Presentation (user reviews 2026-08-06): rotated 90° (north right, marked);
districts labelled; four confidence tiers — Safe >=90% solid, Strongly
leaning 75-90% finely hatched, Leaning 60-75% heavily hatched, Toss-up <60%
grey — with a swatch key; JS tooltips list every party winning >=5% of a
ward's simulations plus an "other" remainder.

Usage:  python src/render_map.py
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import math

import geopandas as gpd

CHIPS = {
    "DA": "#1B5EA8", "ANC": "#1B7A3D", "EFF": "#B3202B", "MK": "#5B6E22",
    "ASA": "#2FA79B", "PA": "#E0A419", "IFP": "#C8442A", "RISE": "#7A6BA8",
    "VFPLUS": "#B0752D", "ACDP": "#6B4E9E", "ALJAMAAH": "#2E8B72",
}
NAMES = {"DA": "DA", "ANC": "ANC", "EFF": "EFF", "MK": "MK Party",
         "ASA": "ActionSA", "PA": "PA", "IFP": "IFP", "ALJAMAAH": "Al Jama-ah"}
GREY = "#9aa09a"
MARK_START = "<!-- __MAP_START__ -->"
MARK_END = "<!-- __MAP_END__ -->"

# (label, lon, lat) — approximate district centroids for orientation
DISTRICTS = [
    ("Midrand", 28.128, -25.995),
    ("Diepsloot", 28.012, -25.937),
    ("Sandton", 28.057, -26.107),
    ("Randburg", 27.950, -26.094),
    ("Alexandra", 28.100, -26.103),
    ("Roodepoort", 27.865, -26.160),
    ("CBD", 28.043, -26.204),
    ("Soweto", 27.870, -26.260),
    ("Lenasia", 27.830, -26.328),
    ("Orange Farm", 27.860, -26.478),
]

W = 840.0
COS = 0.898   # cos(latitude) lon->km correction for Johannesburg
ANG = math.radians(40)  # map rotated 40° clockwise: north up-right, Soweto SW


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geo", type=Path, default=Path("data/raw/geo/wards2026_JHB.geojson"))
    parser.add_argument("--probs", type=Path,
                        default=Path("data/processed/ward_winner_probs.csv"))
    parser.add_argument("--simplify", type=float, default=0.0006)
    args = parser.parse_args(argv)

    with args.probs.open(encoding="utf-8", newline="") as fh:
        probs = {r["ward"]: r for r in csv.DictReader(fh)}

    gdf = gpd.read_file(args.geo)
    ward_col = next(c for c in ("WardNo", "WARD_NO", "WardID", "WARD_ID", "Ward")
                    if c in gdf.columns)
    gdf["wardno"] = gdf[ward_col].astype(str).str.lstrip("0").str.strip()
    gdf.loc[gdf["wardno"].str.len() > 3, "wardno"] = (
        gdf.loc[gdf["wardno"].str.len() > 3, "wardno"].str[-3:].str.lstrip("0"))
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf.geometry.simplify(args.simplify, preserve_topology=True)

    minx, miny, maxx, maxy = gdf.total_bounds
    ca, sa = math.cos(ANG), math.sin(ANG)

    def rot(x, y):
        # rotate ANG clockwise: north up-right, Soweto bottom-left (no mirror)
        e = (x - minx) * COS
        n = (y - miny)
        return (e * ca + n * sa, e * sa - n * ca)

    # Fit the viewBox to the CITY's rotated extent, not the rotated bounding
    # rectangle — Johannesburg lies diagonally, so the rectangle bound left
    # the shape floating in dead margin (user screenshot, 2026-08-06).
    rxs, rys = [], []
    for geom in gdf.geometry:
        gs = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for g in gs:
            for x, y in g.exterior.coords:
                rx, ry = rot(x, y)
                rxs.append(rx); rys.append(ry)
    rminx, rmaxx, rminy, rmaxy = min(rxs), max(rxs), min(rys), max(rys)
    PAD = 8.0
    scale = (W - 2 * PAD) / (rmaxx - rminx)
    H = (rmaxy - rminy) * scale + 2 * PAD

    def xy(x, y):
        rx, ry = rot(x, y)
        return ((rx - rminx) * scale + PAD, (ry - rminy) * scale + PAD)

    paths, hatches, called = [], [], {"solid": 0, "strong": 0, "lean": 0, "grey": 0}
    patterns: dict[str, str] = {}
    for _, row in gdf.iterrows():
        p = probs.get(row["wardno"])
        geoms = row.geometry.geoms if row.geometry.geom_type == "MultiPolygon" \
            else [row.geometry]
        d = ""
        for geom in geoms:
            for ring in [geom.exterior, *geom.interiors]:
                pts = [xy(x, y) for x, y in ring.coords]
                d += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"

        if p is None:
            fill, cls = GREY, "grey"
            tip = f"Ward {row['wardno']}"
        else:
            pw = float(p["p_win"])
            winner = p["winner"]
            name = NAMES.get(winner, winner.title())
            entries = [(c.split(":")[0], float(c.split(":")[1]))
                       for c in p["dist"].split("|")]
            main = [(c, v) for c, v in entries if v >= 0.05]
            other = sum(v for c, v in entries if v < 0.05)
            share = " · ".join(f"{NAMES.get(c, c.title())} {v:.0%}" for c, v in main)
            if other >= 0.005:
                share += f" · other {other:.0%}"
            challengers = [c for c, v in main if c != winner][:2]
            if pw >= 0.90:
                fill, cls, verdict = CHIPS.get(winner, GREY), "solid", f"safe {name}"
            elif pw >= 0.75:
                fill, cls, verdict = CHIPS.get(winner, GREY), "strong", f"strongly leaning {name}"
            elif pw >= 0.60:
                fill, cls, verdict = CHIPS.get(winner, GREY), "lean", f"leaning {name}"
            else:
                fill, cls, verdict = GREY, "grey", "too close to call"
            tip = f"Ward {row['wardno']} · {verdict} — {share}"
        called[cls] += 1
        paths.append(f'<path d="{d}" fill="{fill}" stroke="var(--paper)" '
                     f'stroke-width="0.8" data-tip="{tip}"></path>')
        if p is not None and cls in ("strong", "lean") and challengers:
            cols = [CHIPS.get(c, GREY) for c in challengers]
            pid = f"h_{cls}_" + "_".join(c.lstrip("#") for c in cols)
            if pid not in patterns:
                width = 3.2 if cls == "lean" else 1.6   # bolder = more contested
                step = 7.0
                lines = f'<line x1="0" y1="0" x2="0" y2="{step}" stroke="{cols[0]}" stroke-width="{width}"/>'
                if len(cols) > 1:   # three-way ward: alternate both challengers
                    lines += (f'<line x1="{step/2}" y1="0" x2="{step/2}" y2="{step}" '
                              f'stroke="{cols[1]}" stroke-width="{width}"/>')
                patterns[pid] = (f'<pattern id="{pid}" width="{step}" height="{step}" '
                                 f'patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
                                 f'{lines}</pattern>')
            hatches.append(f'<path d="{d}" fill="url(#{pid})" '
                           f'pointer-events="none"></path>')

    labels = []
    for name, lx, ly in DISTRICTS:
        px, py = xy(lx, ly)
        if -10 <= px <= W + 10 and -10 <= py <= H + 10:
            labels.append(
                f'<text x="{px:.0f}" y="{py:.0f}" text-anchor="middle" '
                f'style="font:650 11px ui-sans-serif,system-ui;letter-spacing:.08em;'
                f'text-transform:uppercase;fill:var(--ink);stroke:var(--paper);'
                f'stroke-width:3px;paint-order:stroke;pointer-events:none">{name}</text>')
    labels.append(
        f'<text x="{W - 14:.0f}" y="20" text-anchor="end" '
        f'style="font:600 11px ui-monospace,monospace;fill:var(--ink-3);'
        f'pointer-events:none">N ↗</text>')

    # council inset: the city silhouette filled with banded seat proportions
    summary = json.loads(Path("data/processed/forecast_summary.json").read_text())
    seats = sorted(((k, round(v["median"])) for k, v in summary["parties"].items()
                    if round(v["median"]) >= 1), key=lambda kv: -kv[1])
    named_total = sum(n for _, n in seats)
    if named_total < 270:
        seats.append(("OTHER", 270 - named_total))
    outline = gdf.geometry.union_all().simplify(0.0012)
    od = ""
    for g in (outline.geoms if outline.geom_type == "MultiPolygon" else [outline]):
        pts = [xy(x, y) for x, y in g.exterior.coords]
        od += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
    MINI_W = 300.0
    ms = MINI_W / W
    mini_h = H * ms
    mx, my = W - MINI_W - 4, H - mini_h - 6   # bottom-right blank corner

    # Area-proportional bands: equal-width strips under-sold whichever party
    # sat at a narrow end of the silhouette (user review: DA looked small).
    # Integrate the outline's area profile along x and put band boundaries at
    # each party's cumulative seat share of the TOTAL AREA.
    from shapely.geometry import Polygon, box
    screen_polys = []
    for g in (outline.geoms if outline.geom_type == "MultiPolygon" else [outline]):
        screen_polys.append(Polygon([xy(x, y) for x, y in g.exterior.coords]))
    import numpy as _np
    xs = _np.linspace(0.0, W, 337)
    slab = _np.zeros(len(xs) - 1)
    for i in range(len(xs) - 1):
        strip = box(xs[i], 0, xs[i + 1], H)
        slab[i] = sum(pl.intersection(strip).area for pl in screen_polys)
    cum = _np.concatenate([[0.0], _np.cumsum(slab)])
    total_area = cum[-1]
    bands, acc = [], 0
    cursor_x = 0.0
    for party, n in seats:
        acc += n
        x_end = float(_np.interp(acc / 270.0 * total_area, cum, xs))
        col = CHIPS.get(party, GREY)
        nm = NAMES.get(party, "Others" if party == "OTHER" else party.title())
        bands.append(f'<rect x="{cursor_x:.1f}" y="0" width="{x_end - cursor_x:.1f}" '
                     f'height="{H:.0f}" fill="{col}" '
                     f'data-tip="{nm} — {n} of 270 seats (median)"/>')
        cursor_x = x_end
    inset = f"""<g transform="translate({mx:.0f},{my:.0f}) scale({ms:.4f})">
      <clipPath id="cityclip"><path d="{od}"/></clipPath>
      <g clip-path="url(#cityclip)">{''.join(bands)}</g>
      <path d="{od}" fill="none" stroke="var(--ink-3)" stroke-width="2"/>
    </g>
    <text x="{mx + MINI_W:.0f}" y="{my - 8:.0f}" text-anchor="end"
      style="font:650 10.5px ui-sans-serif,system-ui;letter-spacing:.1em;
      text-transform:uppercase;fill:var(--ink-3);pointer-events:none">The full council — 270 seats, proportional</text>
    <text x="8" y="16"
      style="font:650 10.5px ui-sans-serif,system-ui;letter-spacing:.1em;
      text-transform:uppercase;fill:var(--ink-3);pointer-events:none">Ward races — 135 seats, first past the post</text>"""

    party_sw = " ".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:11px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:{CHIPS[c]};'
        f'display:inline-block"></span>{NAMES[c]}</span>'
        for c in ("ANC", "DA", "EFF", "ASA", "PA", "IFP", "ALJAMAAH"))
    KEY_BASE = "#7d6aa6"  # neutral purple: no party owns it
    def key_swatch(pattern_lines: float | None) -> str:
        base = f'<rect width="18" height="12" rx="2" fill="{KEY_BASE}"/>'
        if pattern_lines is None:
            return base
        return (f'{base}<g stroke="#000" stroke-width="{pattern_lines}" '
                f'transform="rotate(45 9 6)">'
                + "".join(f'<line x1="{x}" y1="-8" x2="{x}" y2="20"/>'
                          for x in range(-8, 27, 6)) + "</g>")

    tier_key = f"""<span style="display:inline-flex;align-items:center;gap:6px;margin-right:13px">
      <svg width="18" height="12">{key_swatch(None)}</svg>
      <b>Safe</b>&nbsp;≥90% ({called['solid']})</span>
    <span style="display:inline-flex;align-items:center;gap:6px;margin-right:13px">
      <svg width="18" height="12">{key_swatch(1.6)}</svg>
      <b>Strongly leaning</b>&nbsp;75–90% ({called['strong']})</span>
    <span style="display:inline-flex;align-items:center;gap:6px;margin-right:13px">
      <svg width="18" height="12">{key_swatch(3.2)}</svg>
      <b>Leaning</b>&nbsp;60–75% ({called['lean']})</span>
    <span style="display:inline-flex;align-items:center;gap:6px">
      <svg width="18" height="12"><rect width="18" height="12" rx="2" fill="{GREY}"/></svg>
      <b>Toss-up</b>&nbsp;under 60% ({called['grey']})</span>"""

    snippet = f"""{MARK_START}
  <section>
    <div class="eyebrow">The map — every ward, called using 5,000 simulations</div>
    <h2>Who wins where</h2>
    <figure>
      <div style="position:relative">
      <svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" id="wardmap"
           aria-label="Johannesburg ward map, rotated with north to the right, coloured by predicted winning party"
           style="width:100%;height:auto;display:block">
        <defs>{''.join(patterns.values())}</defs>
        {''.join(paths)}{''.join(hatches)}{''.join(labels)}{inset}
      </svg>
      <div id="maptip" style="position:fixed;display:none;pointer-events:none;z-index:9;
        font:12px/1.4 ui-sans-serif,system-ui;background:var(--ink);color:var(--paper);
        padding:6px 10px;border-radius:4px;max-width:280px"></div>
      </div>
      <figcaption style="display:flex;flex-direction:column;gap:6px">
        <span>{tier_key}</span>
        <span>{party_sw}</span>
        <span>Touch or hover any ward to see a party's chance of winning it. A ward needs no
        majority — highest total wins. Smaller map shows final seats when combined with the
        Party Proportional Representation ballot.</span>
      </figcaption>
    </figure>
    <script>
    (function() {{
      var tip = document.getElementById('maptip');
      var map = document.getElementById('wardmap');
      map.addEventListener('mousemove', function(e) {{
        var t = e.target.getAttribute && e.target.getAttribute('data-tip');
        if (t) {{ tip.textContent = t; tip.style.display = 'block';
          tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 14) + 'px';
        }} else tip.style.display = 'none';
      }});
      map.addEventListener('mouseleave', function() {{ tip.style.display = 'none'; }});
      map.addEventListener('click', function(e) {{
        var t = e.target.getAttribute && e.target.getAttribute('data-tip');
        if (t) {{ tip.textContent = t; tip.style.display = 'block';
          tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 14) + 'px'; }}
      }});
    }})();
    </script>
  </section>
  {MARK_END}"""

    for target in (Path("forecast-sheet.html"), Path("drafts/forecast-draft.html")):
        t = target.read_text(encoding="utf-8")
        if MARK_START not in t:
            print(f"  ! no map markers in {target}; skipped")
            continue
        start = t.index(MARK_START)
        end = t.index(MARK_END) + len(MARK_END)
        target.write_text(t[:start] + snippet + t[end:], encoding="utf-8")
        print(f"  map into {target}")
    print(f"called: {called}  ·  {W:.0f}x{H:.0f}  ·  "
          f"svg ~{sum(len(p) for p in paths) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
