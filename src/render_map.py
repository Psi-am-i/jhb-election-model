"""Render the ward-winner map into the forecast pages.

Reads ward_winner_probs.csv (written by every Monte Carlo run) and the MDB
2026 ward boundaries, and writes an inline SVG choropleth between the
__MAP_START__/__MAP_END__ markers of forecast-sheet.html and
drafts/forecast-draft.html.

Presentation (user reviews 2026-08-06): rotated 90° (north right, marked);
districts labelled; four confidence tiers — Safe >=90% solid, Strongly
leaning 75-90% finely hatched, Leaning 60-75% heavily hatched, Toss-up <60%
striped on grey, one stripe per contender in proportion to its share
(owner, 2026-09-17) — with a swatch key; JS tooltips list every party winning >=5% of a
ward's simulations plus an "other" remainder.

Usage:  python src/render_map.py
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cityconfig
import math
import os

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
# Map chrome is per-city: which places to label, the cos-latitude correction
# for lon->km, and how far to rotate so the city sits well in a wide figure.
# All three live in cities/<slug>.toml [map]; the first is editorial, the
# second is derivable from the centroid, the third is an aesthetic call.
_CITY = cityconfig.load(os.environ.get("CITY_SLUG") or None)
_MAP = _CITY.raw.get("map", {})

DISTRICTS = [(d["name"], float(d["lon"]), float(d["lat"]))
             for d in _MAP.get("labels", [])]

W = float(_MAP.get("width", 840.0))
COS = float(_MAP.get("cos_lat", 0.898))   # lon->km correction at this latitude
ANG = math.radians(float(_MAP.get("rotate_deg", 40)))


#: A party gets a STRIPE only if it wins the ward in at least one simulation in
#: ten. Owner, 2026-09-17: "If you win 1:10 I'd say you're reasonably a
#: contender ... 3/50? or 1/16 ... it's fair not to draw you (but you are in the
#: tooltip)." The tooltip keeps its 5% cut; a hairline stripe is not information.
STRIPE_MIN = 0.10
UNKNOWN_CHIP = "#5f6660"   # never GREY: a grey stripe on grey ground vanishes
REST = "__rest__"          # the band for every party below STRIPE_MIN, drawn in GREY


def stripe_parties(entries, winner=None, limit=2):
    """Parties that earn a stripe, strongest first, excluding ``winner``."""
    return [(c, v) for c, v in sorted(entries, key=lambda cv: -cv[1])
            if c != winner and v >= STRIPE_MIN][:limit]


def toss_pattern(contenders, step: float = 7.0, prefix: str = "h"):
    """A too-close-to-call ward's pattern: one BAND per contender.

    The bands tile the whole pattern width in proportion to each contender's
    share, so no ground colour shows between them. The first version drew thin
    lines on grey, and the grey gaps read as extra stripes — a 49/49 IFP/MK ward
    looked like four parties (owner, 2026-09-17). Returns ``(pattern_id, svg)``,
    or ``None`` with fewer than two contenders (the ward stays plain grey).
    """
    if len(contenders) < 2:
        return None
    total = sum(v for _, v in contenders)
    widths = [step * v / total for _, v in contenders]
    cols = [GREY if c == REST else CHIPS.get(c, UNKNOWN_CHIP) for c, _ in contenders]
    pid = f"{prefix}_toss_" + "_".join(
        f"{col.lstrip('#')}{w:.1f}".replace(".", "p") for col, w in zip(cols, widths))
    x, lines = 0.0, []
    for col, w in zip(cols, widths):
        lines.append(f'<line x1="{x + w / 2:.2f}" y1="0" x2="{x + w / 2:.2f}" '
                     f'y2="{step}" stroke="{col}" stroke-width="{w:.2f}"/>')
        x += w
    return pid, (f'<pattern id="{pid}" width="{step}" height="{step}" '
                 f'patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
                 + "".join(lines) + "</pattern>")


#: Solid colour only when one party wins the ward in at least this share of
#: simulations. Owner, 2026-09-17: "safe = solid colour, wins 90%; stripes show
#: every party that wins more than 10% of simulations; thicker = more wins.
#: Leaning and strongly leaning aren't visually different and can be removed."
SAFE = 0.90
TIP_FLOOR = 0.05          # a party is named in the tooltip at >= this share
OTHER_FLOOR = 0.005       # ...and the "other" remainder is shown at >= this


def ward_call(ward: str, winner: str, pw: float, dist: str) -> dict:
    """How ONE ward is drawn and described. The only definition: the geographic
    map and the hex cartogram both call this, so they cannot disagree.

    ``dist`` is ``ward_winner_probs.csv``'s ``PARTY:share|PARTY:share`` field.
    Returns ``fill``, ``cls`` (``solid`` or ``contested``), ``tip`` and
    ``bands`` — the parties that earn a band, strongest first.
    """
    entries = [(c.split(":")[0], float(c.split(":")[1])) for c in dist.split("|")]
    main = [(c, v) for c, v in entries if v >= TIP_FLOOR]
    other = sum(v for c, v in entries if v < TIP_FLOOR)

    def _pc(v):
        # ⛔ never "100%": it reads as certain, and wards that looked safe have lost
        return "over 99%" if v > 0.99 else f"{v:.0%}"
    share = " · ".join(f"{NAMES.get(c, c.title())} {_pc(v)}" for c, v in main)
    if other >= OTHER_FLOOR:
        share += f" · other {other:.0%}"
    name = NAMES.get(winner, winner.title())
    if pw >= SAFE:
        return {"fill": CHIPS.get(winner, UNKNOWN_CHIP), "cls": "solid", "bands": [],
                "tip": f"Ward {ward} · {name} in over 9 of every 10 simulations — {share}"}
    bands = stripe_parties(main, limit=4)
    rest = 1.0 - sum(v for _, v in bands)
    # A ward under 90% with only ONE party at >= 10% still must not look safe,
    # and must not be plain grey either (it read as "too close to call", owner
    # 2026-09-17). Everyone below the stripe line becomes one grey band, sized
    # to its share, whenever it would be a real band or the only other band.
    if rest >= STRIPE_MIN or (len(bands) < 2 and rest > 0):
        bands = bands + [(REST, rest)]
    return {"fill": GREY, "cls": "contested", "bands": bands,
            "tip": f"Ward {ward} · contested — share of simulations won: {share}"}


def ward_hatch(call: dict, patterns: dict, prefix: str = "h") -> str | None:
    """The banded fill for a contested ward, registered in ``patterns``.

    ⛔ ``prefix`` IS NOT DECORATION. Both maps are in one document, and a
    reference resolves to the FIRST element with that id. With shared ids the
    cartogram's bands pointed at the land map's patterns — and when the land map
    is hidden by the toggle, a pattern inside it stops rendering, so every
    contested hexagon went flat grey (owner, 2026-09-18).
    """
    made = toss_pattern(call["bands"], prefix=prefix) if call["cls"] == "contested" else None
    if not made:
        return None
    pid, svg = made
    patterns.setdefault(pid, svg)
    return pid


#: Key swatch colours that belong to no party: a solid block and a striped one
#: in these would otherwise read as "the ANC" or "Rise" (owner, 2026-09-17).
KEY_SOLID, KEY_STRIPE_A, KEY_STRIPE_B = "#d9d3c3", "#d9d3c3", "#4b4f4c"
KEY_PARTIES = ("ANC", "DA", "EFF", "MK", "ASA", "PA", "IFP", "ALJAMAAH")


def party_key() -> str:
    """The party colours, shown first in both maps' keys."""
    return " ".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;margin-right:11px">'
        f'<span style="width:10px;height:10px;border-radius:2px;background:{CHIPS[c]};'
        f'display:inline-block"></span>{NAMES[c]}</span>' for c in KEY_PARTIES)


def map_key(called: dict, n_draws_token: str = "{{n_draws}}") -> str:
    """The key both maps show: party colours, then what solid and striped mean."""
    stripes = "".join(
        f'<rect x="{i * 3}" width="3" height="12" fill="{KEY_STRIPE_A if i % 2 == 0 else KEY_STRIPE_B}" '
        f'transform="skewX(-30)"/>' for i in range(-2, 12))
    return f"""<span style="display:block;margin-bottom:6px">{party_key()}</span>
    <span style="display:inline-flex;align-items:center;gap:6px;margin-right:13px;white-space:nowrap">
      <svg width="18" height="12"><rect width="18" height="12" rx="2" fill="{KEY_SOLID}"/></svg>
      <b>Solid colour</b>&nbsp;one party wins the ward in at least 9 of every 10 simulations ({called.get('solid', 0)})</span>
    <span style="display:inline-flex;align-items:center;gap:6px;white-space:nowrap">
      <svg width="18" height="12"><clipPath id="keyclip"><rect width="18" height="12" rx="2"/></clipPath><g clip-path="url(#keyclip)">{stripes}</g></svg>
      <b>Stripes</b>&nbsp;contested ({called.get('contested', 0)})</span>
    <br><span style="font-size:12px;color:var(--ink-3)">A stripe for every party that wins the ward in
      at least 1 in 10 of the {n_draws_token} simulations; the wider the stripe, the more simulations
      it wins. Grey is every other party together. These are shares of simulations, not vote shares.</span>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geo", type=Path, default=Path("data/raw/geo/wards2026_{CODE}.geojson"))
    parser.add_argument("--probs", type=Path,
                        default=Path("data/processed/ward_winner_probs.csv"))
    parser.add_argument("--simplify", type=float, default=0.0006)
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))

    with args.probs.open(encoding="utf-8", newline="") as fh:
        probs = {r["ward"]: r for r in csv.DictReader(fh)}

    gdf = gpd.read_file(cityconfig.resolve_path(args.geo))
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
    PAD_X, PAD_TOP = 8.0, 2.0
    scale = (W - 2 * PAD_X) / (rmaxx - rminx)
    MAP_H = (rmaxy - rminy) * scale + PAD_TOP
    H = MAP_H + 30.0   # dedicated strip so the inset + its title never overlap the city

    def xy(x, y):
        rx, ry = rot(x, y)
        return ((rx - rminx) * scale + PAD_X, (ry - rminy) * scale + PAD_TOP)

    paths, hatches, called = [], [], {"solid": 0, "contested": 0}
    patterns: dict[str, str] = {}
    path_data: list = []
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
            call = {"fill": GREY, "cls": "contested", "bands": [], "tip": f"Ward {row['wardno']}"}
        else:
            call = ward_call(row["wardno"], p["winner"], float(p["p_win"]), p["dist"])
        called[call["cls"]] = called.get(call["cls"], 0) + 1
        path_data.append((row, d))
        paths.append(f'<path d="{d}" fill="{call["fill"]}" stroke="var(--paper)" '
                     f'stroke-width="0.8" data-tip="{call["tip"]}"></path>')
        pid = ward_hatch(call, patterns)
        if pid:
            hatches.append(f'<path d="{d}" fill="url(#{pid})" pointer-events="none"></path>')

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

    # The full council as a plain stacked bar, not a city silhouette: PR seats
    # have no geography, so drawing them inside the city outline suggested one
    # (owner, 2026-09-17). Same typical simulation as the "two ballots" bars.
    import csv as _csv
    import scenarios as _scen
    with (Path("data/processed") / "seat_draws.csv").open(encoding="utf-8", newline="") as fh:
        _draws = list(_csv.DictReader(fh))
    _parties = [k for k in _draws[0] if k not in ("draw", "threshold", "council_size")]
    _S = {p: [int(r[p]) for r in _draws] for p in _parties}
    _t = _scen.typical(_S, KEY_PARTIES)
    seats = sorted(((p, _S[p][_t]) for p in _parties if _S[p][_t] > 0), key=lambda kv: -kv[1])
    council = int(_draws[_t]["council_size"])
    named_total = sum(n for _, n in seats)
    if named_total < council:
        seats.append(("OTHER", council - named_total))
    BAR_W, BAR_H = 300.0, 18.0
    mx, my = W - BAR_W - 8, H - BAR_H - 30
    bands, cursor_x = [], 0.0
    for party, n in seats:
        w = BAR_W * n / council
        nm = NAMES.get(party, "Others" if party == "OTHER" else party.title())
        bands.append(f'<rect x="{cursor_x:.1f}" y="0" width="{w:.1f}" height="{BAR_H:.0f}" '
                     f'fill="{CHIPS.get(party, GREY)}" data-tip="{nm} — {n} of {council} seats"/>')
        cursor_x += w
    inset = f"""<g transform="translate({mx:.0f},{my:.0f})">{''.join(bands)}
      <rect width="{BAR_W:.0f}" height="{BAR_H:.0f}" fill="none" stroke="var(--ink-3)" stroke-width="1"/></g>
    <text x="{mx + BAR_W:.0f}" y="{my + BAR_H + 16:.0f}" text-anchor="end"
      style="font:650 10.5px ui-sans-serif,system-ui;letter-spacing:.1em;
      text-transform:uppercase;fill:var(--ink-3);pointer-events:none">The full council — {council} seats, one typical simulation</text>
    <text x="8" y="16"
      style="font:650 10.5px ui-sans-serif,system-ui;letter-spacing:.1em;
      text-transform:uppercase;fill:var(--ink-3);pointer-events:none">Ward races — 135 seats, first past the post</text>"""

    tier_key = map_key(called)

    snippet = f"""{MARK_START}
  <details class="rollup" data-band="forecast" data-map="geo" open>
    <summary><span class="eyebrow">The map — every ward, called using {{{{n_draws}}}} simulations</span>
    <h2>Who wins where</h2></summary>
    <p class="maplede">Ward races for half the council — 135 seats, first past the post. A ward needs no
    majority: the highest total wins. A geographic map can mislead, because every ward elects one
    councillor however big or small it is. Switch to <b>Equal Sized Wards</b> to see the same forecast
    drawn by seats.</p>
    <div class="maptoggle">
      <button type="button" data-show="geo" class="on" aria-pressed="true">Normal Map</button>
      <button type="button" data-show="cartogram" aria-pressed="false">Equal Sized Wards</button>
    </div>
    <figure>
      <div style="position:relative">
      <svg viewBox="0 0 {W:.0f} {H:.0f}" role="img" id="wardmap"
           aria-label="{_CITY.name} ward map, rotated with north to the right, coloured by predicted winning party"
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
        <span>Touch or hover any ward for its numbers. The bar shows the whole council, ward and
        list seats together, in one typical simulation.</span>
      </figcaption>
    </figure>
    <script>
    (function() {{
      var tip = document.getElementById('maptip');
      var map = document;
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
  </details>
  {MARK_END}"""

    import json as _json
    Path("data/processed/ward_paths.json").write_text(_json.dumps({
        "W": W, "H": H,
        "paths": {row["wardno"]: d for row, d in path_data},
        "labels": [{"t": name, "x": round(xy(lx, ly)[0]), "y": round(xy(lx, ly)[1])}
                   for name, lx, ly in DISTRICTS
                   if -10 <= xy(lx, ly)[0] <= W + 10 and -10 <= xy(lx, ly)[1] <= H + 10],
    }, separators=(",", ":")), encoding="utf-8")

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
