"""Write the prototype's fixtures under interactive/fixtures/.

PROTOTYPE ONLY. Nothing here is model output.

Two kinds of file:

* **geometry.json** — a COPY of the ward geography the live site already draws
  (data/processed/ward_paths.json and ward_hex_layout.json), plus a ward->sector
  table derived from data/raw/geo/wards2026_JHB.geojson by the method in
  audits/2026-09-27-interactive-levers/DESIGN-decided.md §1 (central = the
  nearest fifth of wards to the city centroid, the rest by compass bearing
  from it, computed in lon/lat because the SVG map is rotated north-right).
  Geography, not a model number, but still a copy: production reads the
  processed files directly, or the S5 ward-to-sector file once it exists.
  The source paths and sha256 of each input are written into the file.

* **placeholder-model.json** — SYNTHETIC. A seeded
  random generator makes up a roster, a "most likely" ward map, citywide
  shares and draws so the builder has something to render. The synthetic
  draws are no longer written out: "play with the model" reads the published
  draws (site/draws/) since S6, and they are kept here only because the
  model fixture's `published_seats_median` is computed from them. They are not derived
  from ward_draws.csv, seat_draws.csv or any other artefact of the model,
  because the model is about to be re-emitted and a real-looking number in a
  prototype is a model number in a page. Party names and colours are the
  site's own (src/render_sheet.CHIPS / NAMES — a third copy of the colours,
  which production must emit from one place).

Usage (stdlib only):
    python3 interactive/tools/make_fixtures.py
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "interactive" / "fixtures"
SEED = 20260928

SRC_PATHS = ROOT / "data/processed/ward_paths.json"
SRC_HEX = ROOT / "data/processed/ward_hex_layout.json"
SRC_GEO = ROOT / "data/raw/geo/wards2026_JHB.geojson"

# The site's colours and short names (src/render_sheet.py CHIPS and NAMES).
# Extra roster entries get neutral greys: in the real roster most parties have
# no chip either, and the page must cope with that.
ROSTER = [
    ("ACDP", "ACDP", "#6B4E9E"),
    ("ALJAMAAH", "Al Jama-ah", "#2E8B72"),
    ("ALL_CITIZENS_PARTY", "All Citizens Party", "#8a8f8a"),
    ("ANC", "ANC", "#1B7A3D"),
    ("ASA", "ActionSA", "#2FA79B"),
    ("BOSA", "BOSA", "#9a9f9a"),
    ("DA", "DA", "#1B5EA8"),
    ("EFF", "EFF", "#B3202B"),
    ("IFP", "IFP", "#C8442A"),
    ("MK", "MK Party", "#5B6E22"),
    ("PA", "PA", "#E0A419"),
    ("RISE", "Rise Mzansi", "#7A6BA8"),
    ("SOUTH_AFRICAN_COMMUNIST_PARTY", "SACP", "#a3726b"),
    ("VFPLUS", "VF+", "#B0752D"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ring_centroid(coords):
    """Area-weighted centroid of one polygon ring (shoelace)."""
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(coords, coords[1:] + coords[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if abs(a) < 1e-15:
        xs, ys = zip(*coords)
        return sum(xs) / len(xs), sum(ys) / len(ys), 0.0
    return cx / (3 * a), cy / (3 * a), abs(a) / 2


def feature_centroid(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    tx = ty = tw = 0.0
    for poly in polys:
        x, y, w = ring_centroid([tuple(p[:2]) for p in poly[0]])
        tx += x * w
        ty += y * w
        tw += w
    return tx / tw, ty / tw


def sectors() -> dict[str, str]:
    geo = json.loads(SRC_GEO.read_text())
    cent = {str(f["properties"]["WardNo"]): feature_centroid(f["geometry"])
            for f in geo["features"]}
    mx = sum(c[0] for c in cent.values()) / len(cent)
    my = sum(c[1] for c in cent.values()) / len(cent)
    coslat = math.cos(math.radians(my))
    dist = {w: math.hypot((x - mx) * coslat, y - my) for w, (x, y) in cent.items()}
    n_central = round(len(cent) / 5)
    central = set(sorted(dist, key=dist.get)[:n_central])
    out = {}
    for w, (x, y) in cent.items():
        if w in central:
            out[w] = "central"
            continue
        bearing = math.degrees(math.atan2((x - mx) * coslat, y - my)) % 360
        out[w] = ("north" if bearing >= 315 or bearing < 45 else
                  "east" if bearing < 135 else
                  "south" if bearing < 225 else "west")
    return out


def geometry() -> dict:
    paths = json.loads(SRC_PATHS.read_text())
    hexes = json.loads(SRC_HEX.read_text())
    sec = sectors()
    wards = sorted(paths["paths"], key=int)
    assert len(wards) == 135 and set(wards) == set(hexes["cells"]) == set(sec)
    return {
        "_about": ("COPY of the live site's ward geography, for the prototype only. "
                   "Production reads data/processed directly. Sectors derived per "
                   "DESIGN-decided.md §1 by interactive/tools/make_fixtures.py."),
        "_sources": {str(p.relative_to(ROOT)): sha(p) for p in (SRC_PATHS, SRC_HEX, SRC_GEO)},
        "_generated": date.today().isoformat(),
        "W": paths["W"], "H": paths["H"], "hex_radius": hexes["radius"],
        "labels": paths["labels"],
        "wards": [{"id": w, "path": paths["paths"][w], "hex": hexes["cells"][w],
                   "sector": sec[w]} for w in wards],
    }


def dirichlet(rng, alphas):
    g = [rng.gammavariate(a, 1.0) for a in alphas]
    s = sum(g)
    return [x / s for x in g]


def placeholder(geom) -> tuple[dict, dict]:
    rng = random.Random(SEED)
    codes = [c for c, _, _ in ROSTER]
    # Synthetic "strength" per party: random, then sorted by nothing in
    # particular. These are made-up numbers and deliberately not the model's.
    weights = [rng.uniform(0.2, 1.0) ** 3 for _ in codes]
    tot = sum(weights)
    shares = [w / tot for w in weights]

    # A spatially smooth made-up ward map: a handful of random seed points,
    # each ward takes the party of its nearest seed.
    W, H = geom["W"], geom["H"]
    seeds = []
    for _ in range(9):
        party = rng.choices(codes, weights=weights)[0]
        seeds.append((rng.uniform(0, W), rng.uniform(0, H), party))
    likely = {}
    for w in geom["wards"]:
        x, y = w["hex"]
        likely[w["id"]] = min(seeds, key=lambda s: (s[0] - x) ** 2 + (s[1] - y) ** 2)[2]

    model = {
        "_about": ("PLACEHOLDER — SYNTHETIC, NOT MODEL OUTPUT. Generated by "
                   "interactive/tools/make_fixtures.py from a seeded random number "
                   "generator so the prototype has something to draw. Replace with "
                   "the model's emitted artefacts (S2 export_draws) before any use."),
        "placeholder": True,
        "seed": SEED,
        "model_ref": "placeholder-" + str(SEED),
        "run_date": None,
        "city": "joburg",
        "target": "2026",
        "council_seats": 270,
        "ward_seats": 135,
        "majority": 136,
        # The combined valid vote (ward and list ballots together) the
        # reader's shares are scaled to by src/reader_seats.py. SYNTHETIC, from
        # its own seeded generator so the rest of the file is unchanged; the
        # real value is the start state's combined total from the S2 export.
        "total_votes": random.Random(f"{SEED}-total-votes").randint(1_200_000, 1_800_000),
        # Roster parties with no PR list (independents included). None in the
        # placeholder roster; the certified roster says which (CLAUDE.md §4b).
        "no_pr_list": [],
        "roster_order": "alphabetical by party code (placeholder for the IEC ballot order)",
        "parties": [{"code": c, "name": n, "colour": col} for c, n, col in ROSTER],
        # Each party's share of the COMBINED vote, ward and list ballots
        # together, in percent: what the reader's slider shows and what the
        # statute counts (DESIGN-decided §10).
        "combined_share": {c: round(s * 100, 2) for c, s in zip(codes, shares)},
        "likely_ward_winner": likely,
    }

    # Draws for the "play with the model" page: per grid cell and seat law,
    # synthetic pool turnouts, PR shares and seats. Shapes follow PLAN.md §8
    # (what S2 will record); the numbers are made up.
    pools = ["black_african", "coloured", "indian_asian", "white"]
    base_t = [0.37, 0.53, 0.45, 0.52]   # synthetic centres, not measured bands
    laws = ["deduct", "expand", "level", "cap"]
    cells = {}
    n = 240
    for ds in (0.5, 1, 2):
        for wb in (0, 0.4, 1):
            key = f"ds{ds}_wb{wb}"
            crng = random.Random(f"{SEED}-{key}")
            draws = []
            for _ in range(n):
                common = crng.gauss(0, 0.05)
                t = [min(0.9, max(0.1, b + common + crng.gauss(0, 0.04))) for b in base_t]
                conc = 60 / ds
                alphas = [max(0.05, s * conc * (1 + 0.3 * wb * crng.uniform(-1, 1))) for s in shares]
                # turnout tilt: each pool is tied to a random pair of parties
                pr = dirichlet(crng, alphas)
                seats = {}
                for law in laws:
                    extra = {"deduct": 0, "expand": 6, "level": 14, "cap": 0}[law]
                    total = 270 + (crng.randint(0, extra) if extra else 0)
                    raw = [p * total for p in pr]
                    fl = [int(r) for r in raw]
                    rem = sorted(range(len(raw)), key=lambda i: -(raw[i] - fl[i]))
                    for i in rem[: total - sum(fl)]:
                        fl[i] += 1
                    seats[law] = fl
                draws.append({"t": [round(x, 4) for x in t],
                              "pr": [round(x * 100, 3) for x in pr],
                              "seats": seats})
            cells[key] = draws
    draws = {
        "_about": model["_about"],
        "placeholder": True,
        "parties": codes,
        "pools": pools,
        "pool_labels": {"black_african": "Black African", "coloured": "Coloured",
                        "indian_asian": "Indian/Asian", "white": "White"},
        "laws": {"deduct": "The law (surplus deducted from everyone else)",
                 "expand": "Not the law: council grows by the excess",
                 "level": "Not the law: council grows until everyone is covered",
                 "cap": "Not the law: excess ward winners are not seated"},
        "grid": {"dirichlet_scale": [0.5, 1, 2], "w_bye": [0, 0.4, 1]},
        "grid_default": {"dirichlet_scale": 1, "w_bye": 0},
        "refusal_floor_fraction": 0.04,
        "cells": cells,
        "polls": [
            {"id": "poll-a", "house": "Placeholder house A", "date": "2026-07-01", "n": 800,
             "shares": {"ANC": 30, "DA": 28, "ASA": 14, "EFF": 9, "MK": 6},
             "caveat": "Placeholder poll. Real rows come from polls.json."},
            {"id": "poll-b", "house": "Placeholder house B", "date": "2026-08-15", "n": 1200,
             "shares": {"ANC": 19, "DA": 33, "ASA": 12, "EFF": 12, "MK": 10},
             "caveat": "Placeholder poll. Real rows come from polls.json."},
            {"id": "poll-c", "house": "Placeholder house C", "date": "2026-09-10", "n": 600,
             "shares": {"ANC": 25, "DA": 25, "ASA": 16, "EFF": 10, "MK": 8},
             "caveat": "Placeholder poll. Real rows come from polls.json."},
        ],
    }
    # The "published" figure a reader's forecast is compared with: the median
    # of the synthetic base cell under the law. Placeholder like the rest.
    base = cells["ds1_wb0"]
    med = {}
    for k, c in enumerate(codes):
        v = sorted(d["seats"]["deduct"][k] for d in base)
        med[c] = v[len(v) // 2]
    model["published_seats_median"] = med
    return model, draws


def demo_forecast(geom, model) -> dict:
    """One saved reader forecast, so /f/ works in any browser."""
    rng = random.Random(f"{SEED}-demo")
    codes = [p["code"] for p in model["parties"]]
    calls = dict(model["likely_ward_winner"])
    for w in rng.sample(sorted(calls, key=int), 30):
        calls[w] = rng.choice(codes[:12])
    pr = dict(model["combined_share"])
    # The demo's coalition: its own three largest parties by ward wins plus a
    # rough list share, so the shared page shows the majority state. Chosen
    # by rule, not by hand, so no party is picked out.
    wins = {c: 0 for c in codes}
    for c in calls.values():
        wins[c] += 1
    tot = sum(pr.values())
    rough = {c: wins[c] + pr[c] / tot * 135 for c in codes}
    coalition = sorted(sorted(rough, key=rough.get, reverse=True)[:3])
    return {
        "_about": "PLACEHOLDER — a made-up reader forecast for the prototype's shared page.",
        "id": "demo7Qx2Lp",
        "display_name": "pollster-23",
        "created_at": "2026-09-28T09:00:00Z",
        "model_ref": model["model_ref"],
        "ward_calls": [calls[w["id"]] for w in geom["wards"]],
        "combined_share": pr,
        "coalition": coalition,
        "mayor": max(coalition, key=rough.get),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    geom = geometry()
    model, _ = placeholder(geom)
    counts: dict[str, int] = {}
    for w in geom["wards"]:
        counts[w["sector"]] = counts.get(w["sector"], 0) + 1
    print("sector ward counts:", counts)
    (OUT / "geometry.json").write_text(json.dumps(geom, separators=(",", ":")))
    (OUT / "placeholder-model.json").write_text(json.dumps(model, indent=1))
    (OUT / "demo-forecast.json").write_text(json.dumps(demo_forecast(geom, model), indent=1))
    for p in sorted(OUT.iterdir()):
        print(f"{p.name:28s} {p.stat().st_size:>9,d} bytes")


if __name__ == "__main__":
    main()
