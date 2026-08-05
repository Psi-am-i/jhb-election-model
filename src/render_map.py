"""Render the ward-winner map into the forecast pages.

Reads ward_winner_probs.csv (written by every Monte Carlo run) and the MDB
2026 ward boundaries, and writes an inline SVG choropleth between the
__MAP_START__/__MAP_END__ markers of forecast-sheet.html and
drafts/forecast-draft.html.

Presentation (user review 2026-08-06): the city is drawn ROTATED 90° so its
long north–south axis runs across the page (north points right — marked);
major districts are labelled; the 70–90% tier is HATCHED rather than faded
(opacity was invisible on dark backgrounds); a three-tier key explains
solid / hatched / grey; tooltips are JS-driven because native SVG titles are
unreliable across browsers.

Usage:  python src/render_map.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

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

W = 820.0
COS = 0.898  # cos(latitude) lon->km correction for Johannesburg


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
    scale = W / (maxy - miny)          # rotated: page-x spans latitude
    H = (maxx - minx) * COS * scale    # page-y spans corrected longitude

    def xy(x, y):
        # rotate 90° clockwise: north -> right, west -> top (chirality kept)
        return ((y - miny) * scale, (x - minx) * COS * scale)

    paths, hatches, called = [], [], {"solid": 0, "hatch": 0, "grey": 0}
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
            runner = (f" · next: {NAMES.get(p['runner_up'], p['runner_up'].title())} "
                      f"{float(p['p_runner_up']):.0%}")
            if pw >= 0.90:
                fill, cls = CHIPS.get(winner, GREY), "solid"
                tip = f"Ward {row['wardno']} · {name} wins in {pw:.0%} of simulations"
            elif pw >= 0.70:
                fill, cls = CHIPS.get(winner, GREY), "hatch"
                tip = f"Ward {row['wardno']} · leaning {name} ({pw:.0%}){runner}"
            else:
                fill, cls = GREY, "grey"
                tip = (f"Ward {row['wardno']} · too close to call — {name} {pw:.0%}"
                       f"{runner}")
        called[cls] += 1
        paths.append(f'<path d="{d}" fill="{fill}" stroke="var(--paper)" '
                     f'stroke-width="0.8" data-tip="{tip}"></path>')
        if cls == "hatch":
            hatches.append(f'<path d="{d}" fill="url(#maphatch)" '
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
        f'pointer-events:none">N →</text>')

    party_sw = " ".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:11px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:{CHIPS[c]};'
        f'display:inline-block"></span>{NAMES[c]}</span>'
        for c in ("ANC", "DA", "EFF", "ASA", "PA", "IFP", "ALJAMAAH"))
    tier_key = f"""<span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px">
      <svg width="18" height="12"><rect width="18" height="12" rx="2" fill="{CHIPS['ANC']}"/></svg>
      <b>Safe</b>&nbsp;— won in ≥90% of simulations ({called['solid']} wards)</span>
    <span style="display:inline-flex;align-items:center;gap:6px;margin-right:14px">
      <svg width="18" height="12"><defs><pattern id="kh" width="5" height="5" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><rect width="5" height="5" fill="{CHIPS['ANC']}"/><line x1="0" y1="0" x2="0" y2="5" stroke="var(--paper)" stroke-width="2.4"/></pattern></defs><rect width="18" height="12" rx="2" fill="url(#kh)"/></svg>
      <b>Leaning</b>&nbsp;— 70–90% ({called['hatch']} wards)</span>
    <span style="display:inline-flex;align-items:center;gap:6px">
      <svg width="18" height="12"><rect width="18" height="12" rx="2" fill="{GREY}"/></svg>
      <b>Toss-up</b>&nbsp;— under 70% ({called['grey']} wards)</span>"""

    snippet = f"""{MARK_START}
  <section>
    <div class="eyebrow">The map — every ward, called by 5,000 simulations</div>
    <h2>Who wins where</h2>
    <figure>
      <div style="position:relative">
      <svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" id="wardmap"
           aria-label="Johannesburg ward map, rotated with north to the right, coloured by predicted winning party"
           style="width:100%;height:auto;display:block">
        <defs><pattern id="maphatch" width="6" height="6" patternTransform="rotate(45)"
          patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="6"
          stroke="var(--paper)" stroke-width="2.6"/></pattern></defs>
        {''.join(paths)}{''.join(hatches)}{''.join(labels)}
      </svg>
      <div id="maptip" style="position:fixed;display:none;pointer-events:none;z-index:9;
        font:12px/1.4 ui-sans-serif,system-ui;background:var(--ink);color:var(--paper);
        padding:6px 10px;border-radius:4px;max-width:280px"></div>
      </div>
      <figcaption style="display:flex;flex-direction:column;gap:6px">
        <span>{tier_key}</span>
        <span>{party_sw}</span>
        <span>The city is drawn with north to the right so it fits the page. Touch or hover any
        ward for its numbers. Colours identify parties only.</span>
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
