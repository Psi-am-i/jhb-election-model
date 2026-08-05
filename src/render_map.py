"""Render the ward-winner map into the forecast pages.

Reads the per-ward winner probabilities the Monte Carlo now records
(ward_winner_probs.csv) and the MDB 2026 ward boundaries, and writes an
inline SVG choropleth between the __MAP_START__/__MAP_END__ markers of
forecast-sheet.html and drafts/forecast-draft.html. Same principle as
render_sheet.py: generated from model outputs, never hand-drawn.

Colour = modal winning party (same chips as the seat chart). Confidence:
  p(win) >= 0.90  full colour
  0.70 - 0.90     faded
  < 0.70          neutral grey, "too close to call"

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
    # WardID style 79800094 -> 94
    gdf.loc[gdf["wardno"].str.len() > 3, "wardno"] = (
        gdf.loc[gdf["wardno"].str.len() > 3, "wardno"].str[-3:].str.lstrip("0"))
    gdf = gdf.to_crs(epsg=4326)
    gdf["geometry"] = gdf.geometry.simplify(args.simplify, preserve_topology=True)

    minx, miny, maxx, maxy = gdf.total_bounds
    W = 760.0
    scale = W / (maxx - minx)
    H = (maxy - miny) * scale * 1.15  # rough lat/lon aspect correction for Joburg

    def xy(x, y):
        return ((x - minx) * scale, (maxy - y) * scale * 1.15)

    paths, called = [], {"solid": 0, "faded": 0, "grey": 0}
    for _, row in gdf.iterrows():
        p = probs.get(row["wardno"])
        if p is None:
            fill, tip, cls = GREY, f"Ward {row['wardno']}", "grey"
        else:
            pw = float(p["p_win"])
            winner = p["winner"]
            name = NAMES.get(winner, winner.title())
            if pw >= 0.90:
                fill, opacity, cls = CHIPS.get(winner, GREY), "1", "solid"
            elif pw >= 0.70:
                fill, opacity, cls = CHIPS.get(winner, GREY), "0.45", "faded"
            else:
                fill, opacity, cls = GREY, "0.85", "grey"
            tip = (f"Ward {row['wardno']} — {name} wins in {pw:.0%} of simulations"
                   + (f" (next: {NAMES.get(p['runner_up'], p['runner_up'].title())} "
                      f"{float(p['p_runner_up']):.0%})" if cls != "solid" else ""))
        called[cls] += 1

        geoms = row.geometry.geoms if row.geometry.geom_type == "MultiPolygon" \
            else [row.geometry]
        d = ""
        for geom in geoms:
            for ring in [geom.exterior, *geom.interiors]:
                pts = [xy(x, y) for x, y in ring.coords]
                d += "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + "Z"
        op = "" if cls == "solid" and p is not None else f' fill-opacity="{opacity}"' \
            if p is not None else ""
        paths.append(f'<path d="{d}" fill="{fill}"{op} stroke="var(--paper)" '
                     f'stroke-width="0.7"><title>{tip}</title></path>')

    legend_parties = ["ANC", "DA", "EFF", "ASA", "PA", "IFP", "ALJAMAAH"]
    swatches = " ".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:12px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:{CHIPS[c]};'
        f'display:inline-block"></span>{NAMES[c]}</span>'
        for c in legend_parties)

    snippet = f"""{MARK_START}
  <section>
    <div class="eyebrow">The map — every ward, called by 5,000 simulations</div>
    <h2>Who wins where</h2>
    <figure>
      <svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" aria-label="Johannesburg ward map coloured by predicted winning party"
           style="width:100%;height:auto;display:block">{''.join(paths)}</svg>
      <figcaption>{swatches}<br>
      Solid colour: the party wins that ward in <b>at least 90%</b> of simulations
      ({called['solid']} of 135 wards). Faded: wins in 70–90% ({called['faded']} wards).
      Grey: too close to call ({called['grey']} wards). Hover a ward for its numbers.
      Colours identify parties only.</figcaption>
    </figure>
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
    print(f"called: {called}  ·  svg ~{sum(len(p) for p in paths) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
