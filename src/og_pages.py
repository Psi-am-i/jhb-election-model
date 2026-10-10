"""A share image for each designed page (BRIEF item 9; the specification is
``audits/2026-10-09-site-batch/OG-IMPLEMENTATION-SPEC.md``, built as its
Option A).

PYTHON RESOLVES, NODE DRAWS. This module builds one *card spec* per page from
the build's own render: every figure is the ``display`` string a page printed
for its token (``stats.render``'s record), and every word is the page's own or
one declared here. ``src/og-pages.mjs`` turns each spec into SVG with
share-card.js's primitives and rasterises it (``src/og-raster-node.mjs``); it
holds layout constants only and types no figure.

Which pages have an image (owner's defaults, 2026-10-10): ``/forecast``,
``/claims``, each article, and ``/your-forecast/``. The home page,
``/commentary`` and the documents keep the site's ``og.png``. No claim has an
image of its own in this release.

The images are written to ``<out>/og-page/<slug>-<name>.png``, where ``<name>``
is a hash of the SVG, the card faces and the rasteriser's version, written in
letters (``a``-``p`` for the hex digits) so that the number scan, which reads
``content="…"`` attributes, finds no digits in an image address. A changed
figure, word, layout, badge or face changes the address. The build deletes
every other file in ``og-page/`` and refuses on any node failure: there is no
fallback to an old image or to ``og.png``.

Prerequisite: ``npm ci`` in ``worker-api/`` (resvg-wasm), as for the Worker.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDERER = REPO_ROOT / "src" / "og-pages.mjs"
STAMPS = REPO_ROOT / "src" / "stamps"
CARD_FONTS_JS = REPO_ROOT / "interactive" / "js" / "card-fonts.js"

#: Where the images are served, beside the pages. Not /og/: /og/1/… are the
#: Worker's reader-card routes and /og.png its fallback (src/share-edge.js).
OG_DIR = "og-page"

#: The forecast card's coalitions (owner, 2026-10-10, "looks good" on the mock
#: in og-design/make_og.mjs): each a list of groups of party codes, written
#: with ", " inside a group and " + " between groups, and the token holding the
#: share of simulations in which they hold a majority together
#: (content/joburg/stats.toml).
FORECAST_COALITIONS = (
    ((("ANC",), ("DA",)), "p_anc_da"),
    ((("DA", "ASA", "PA"), ("IFP", "VFPLUS", "ACDP")), "p_majority_da_asa_pa_ifp_vfplus_acdp"),
    ((("ANC", "EFF", "PA"), ("ALJAMAAH",)), "p_majority_anc_eff_pa_aljamaah"),
    ((("ANC",), ("EFF",), ("MK",)), "p_majority_anc_eff_mk"),
)
#: The forecast card's other figures: most seats, one party alone.
FORECAST_LARGEST = (("ANC", "p_anc_largest"), ("DA", "p_da_largest"))
FORECAST_ALONE = "p_alone"

#: The article with a designed visual, by ``og_visual`` in articles.toml: the
#: seat ranges of the largest parties, this many rows.
SEAT_RANGE_ROWS = 6
VISUALS = {"seat-ranges"}

#: The interactive card's words (the approved mock-up, og-design/make_og.mjs,
#: 43bbf59). The map is our prediction's, labelled as such.
INTERACTIVE_HEAD = "Know Politics?"
INTERACTIVE_BODY = ("Pick your winners, seal your prediction and let's see if you "
                    "can beat us on election day.")
INTERACTIVE_CTA = "Make yours at"
INTERACTIVE_MAP_LABEL = "Our prediction"
PREDICTION_SEAL = "seal-official-prediction.svg"


class OgError(SystemExit):
    """A share image cannot be made; the message says why."""


# --------------------------------------------------------------------------
# which pages, and the head's placeholder


def designed(output: str, articles: dict) -> tuple[str, str] | None:
    """``(slug, layout)`` for a page with a share image of its own, else None
    (the page keeps ``og.png``)."""
    import build_your_forecast as yf
    if output == "forecast.html":
        return "forecast", "forecast"
    if output == "claims.html":
        return "claims", "claims"
    if output in articles:
        return output.removesuffix(".html"), "article"
    if output == yf.YF_PAGE:
        return yf.YF_DIR, "interactive"
    return None


def pending(site: str, slug: str) -> tuple[str, str]:
    """The head's image address and alt text before the image exists:
    ``page_og`` writes these, :func:`fill` replaces them."""
    return f"{site}/{OG_DIR}/@@{slug}@@.png", f"@@alt:{slug}@@"


def fill(html: str, site: str, slug: str, filename: str, alt: str) -> str:
    """The page with its image address (twice: og:image, twitter:image) and
    alt text in place of :func:`pending`'s. Refuses unless each placeholder
    is there exactly as often as ``page_og`` writes it."""
    from html import escape
    url, alt_mark = pending(site, slug)
    if html.count(url) != 2 or html.count(alt_mark) != 1:
        raise OgError(f"{slug}: the page head does not carry the image placeholders "
                      f"page_og writes ({html.count(url)} address, {html.count(alt_mark)} alt)")
    return html.replace(url, f"{site}/{OG_DIR}/{filename}").replace(alt_mark, escape(alt))


# --------------------------------------------------------------------------
# figures


def figure_pool(published: list[dict], registry: dict, ctx: dict, extra=()) -> dict[str, str]:
    """Every token a page printed, by name, with the string it printed. A
    token printed differently on two pages is refused (the image could show
    only one). ``extra`` names registry tokens no page prints (the forecast
    card's coalitions); each is rendered by ``stats.render`` exactly as a page
    renders it, with no provenance markup."""
    import stats as statlib
    seen: dict[str, str] = {}
    for r in published:
        t = r.get("token")
        if not t:
            continue
        if t in seen and seen[t] != r["display"]:
            raise OgError(f"token {t} prints as {seen[t]!r} and {r['display']!r} on different "
                          f"pages; a share image cannot show both")
        seen[t] = r["display"]
    for t in extra:
        if t in seen:
            continue
        out, _drift, unresolved = statlib.render("{{" + t + "}}", registry, ctx, wrap=False)
        if unresolved:
            raise OgError(f"share image token {t} does not resolve: {unresolved}")
        seen[t] = out
    return seen


def _fig(pool: dict, token: str) -> dict:
    if token not in pool:
        raise OgError(f"the share image needs {token}, which no page printed")
    return {"token": token, "display": pool[token]}


# --------------------------------------------------------------------------
# glyphs


def faces() -> dict[str, set[int]]:
    """The characters each card face carries, read from card-fonts.js (written
    from src/card-fonts/ by interactive/tools/card_fonts.mjs)."""
    text = CARD_FONTS_JS.read_text(encoding="utf-8")
    out = {}
    for name, body in re.findall(r"^  (\w+): \{[^\n]*?w: \{([^}]*)\}", text, re.M):
        out[name] = {int(k) for k in re.findall(r"(\d+):", body)}
    if not out:
        raise OgError(f"{CARD_FONTS_JS.name}: no faces read")
    return out


def uncovered(spec: dict, have: dict[str, set[int]] | None = None) -> list[str]:
    """Every character of every string in ``spec`` that some card face lacks
    (the images draw in all of them). The map paths and the image names are
    not text."""
    have = have or faces()
    common = set.intersection(*have.values())
    bad = []

    def walk(v, where):
        if isinstance(v, dict):
            for k, x in v.items():
                if k not in ("map", "map_svg", "badge", "logo", "seal", "slug", "layout"):
                    walk(x, f"{where}.{k}")
        elif isinstance(v, list):
            for i, x in enumerate(v):
                walk(x, f"{where}[{i}]")
        elif isinstance(v, str):
            miss = sorted({c for c in v if ord(c) not in common})
            if miss:
                bad.append(f"{where}: {''.join(miss)!r} in {v!r}")
    walk(spec, spec.get("slug", "spec"))
    return bad


# --------------------------------------------------------------------------
# the specs


def _long(iso: str) -> str:
    import stats as statlib
    return statlib._fmt(iso, "date_long")


def _vote_line(election: dict, pool: dict, figures: dict) -> str:
    figures["council_size"] = _fig(pool, "council_size")
    return (f"{election['city']} council, {pool['council_size']} seats, vote on "
            f"{_long(election['date'])}.")


def map_paths(html: str) -> str:
    """The forecast page's ward map, as the page draws it, without its key:
    the <svg> holding the first <pattern> (contested wards are striped)."""
    i = html.find("<pattern")
    if i < 0:
        raise OgError("forecast.html: no striped ward map (<pattern>) to draw")
    a, b = html.rfind("<svg", 0, i), html.find("</svg>", i)
    m = html[a:b + len("</svg>")]
    return re.sub(r'<g transform="translate\(532,548\)">[\s\S]*?</g>', "", m, count=1)


def ward_shapes(map_svg: str) -> int:
    """How many distinct ward outlines a map holds."""
    return len(set(re.findall(r'<path d="([^"]+)"', map_svg)))


def forecast_spec(html: str, pool: dict, *, election: dict, wards: int, headline: str) -> dict:
    """/forecast: the headline, most seats, one party alone, the owner's four
    coalitions, and the page's striped ward map."""
    import build_play
    roster = build_play.roster()
    figures: dict = {}
    rows = []
    for code, tok in FORECAST_LARGEST:
        figures[tok] = _fig(pool, tok)
        rows.append({"label": roster[code]["name"], "value": pool[tok]})
    figures[FORECAST_ALONE] = _fig(pool, FORECAST_ALONE)
    coalitions = []
    for groups, tok in FORECAST_COALITIONS:
        figures[tok] = _fig(pool, tok)
        label = " + ".join(", ".join(roster[c]["name"] for c in g) for g in groups)
        coalitions.append({"label": label, "value": pool[tok]})
    figures["generated_date"] = _fig(pool, "generated_date")
    m = map_paths(html)
    if ward_shapes(m) != wards:
        raise OgError(f"forecast.html's map holds {ward_shapes(m)} ward outlines, not the "
                      f"{wards} wards of the geometry: the map was not cut out whole")
    date = f"Forecast of {pool['generated_date']}. " + _vote_line(election, pool, figures)
    alt = (f"{headline} Most seats: " + ", ".join(f"{r['label']} {r['value']}" for r in rows) +
           f". One party alone with a majority: {pool[FORECAST_ALONE]}. Coalitions with a majority: " +
           "; ".join(f"{c['label']} {c['value']}" for c in coalitions) +
           ". The ward map, contested wards striped.")
    return {"layout": "forecast", "headline": headline, "date_line": date,
            "most_seats": "Most seats", "rows": rows,
            "alone": {"label": "One party alone, a majority", "value": pool[FORECAST_ALONE]},
            "coalitions_head": "Coalitions with a majority", "coalitions": coalitions,
            "key_label": "Striped: contested wards", "map_svg": m,
            "figures": figures, "alt": alt}


def verdict_badge(word: str) -> str:
    """The owner's badge file for a verdict word (render_sheet.VERDICT_BADGE),
    refusing a word with none."""
    import render_sheet
    f = render_sheet.VERDICT_BADGE.get(" ".join(word.upper().split()))
    if f is None or not (STAMPS / f).is_file():
        raise OgError(f"no badge for the verdict {word!r} (render_sheet.VERDICT_BADGE, src/stamps/)")
    return f


def claims_spec(html: str, claims: list[dict], *, headline: str) -> dict:
    """/claims: one badge per party, the first claim per party in claims.toml
    order. Each verdict is the one the page prints (checked against it)."""
    import build_play
    roster = build_play.roster()
    printed = Counter(re.findall(r'<span class="verdict v-[a-z]+">([^<]+)</span>', html))
    typed = Counter(" ".join(c["verdict"].upper().split()) for c in claims)
    if printed != typed:
        raise OgError(f"claims.html prints verdicts {dict(printed)}, claims.toml has "
                      f"{dict(typed)}: the image would not show the page's verdicts")
    items, seen = [], set()
    for c in claims:
        if c["party"] in seen:
            continue
        seen.add(c["party"])
        logo = REPO_ROOT / "site" / "logos" / f"{c.get('logo', c['party'])}.png"
        items.append({"verdict": c["verdict"], "badge": verdict_badge(c["verdict"]),
                      "code": c["party"], "party": roster[c["party"]]["name"],
                      "colour": roster[c["party"]]["colour"],
                      "logo": logo.name if logo.is_file() else None,
                      "speaker": c["speaker"].split(",")[0]})
    latest = max((c["published"] for c in claims),
                 key=lambda d: datetime.strptime(d, "%d %B %Y"))
    alt = (f"{headline}. " + "; ".join(f"{i['party']}: {i['verdict']} ({i['speaker']})" for i in items) + ".")
    return {"layout": "claims", "headline": headline,
            "date_line": f"One claim per party, each tested against the forecast. Latest tested {latest}.",
            "items": items, "figures": {}, "alt": alt}


def article_spec(art: dict, pool: dict, *, rows: list[dict]) -> dict:
    """An article: its headline (``og_headline`` or its title) and date; the
    seat ranges where ``og_visual = "seat-ranges"`` (the forecast page's
    rows, ``rows``: [{code, name, colour}] largest first by middle)."""
    import seat_table
    visual = art.get("og_visual")
    if visual is not None and visual not in VISUALS:
        raise OgError(f"articles.toml {art['href']}: og_visual {visual!r} is not one of {sorted(VISUALS)}")
    headline = art.get("og_headline") or art["title"]
    figures: dict = {}
    date = f"Published {_long(art['date'])}."
    spec = {"layout": "article", "headline": headline, "ranges": None, "figures": figures}
    alt = headline + "."
    if visual == "seat-ranges":
        if not rows:
            raise OgError(f"{art['href']}: its share image draws the seat ranges, and the build "
                          "rendered no forecast page to read their parties from")
        out = []
        for r in rows[:SEAT_RANGE_ROWS]:
            got = {}
            for q in ("median", "p5", "p95"):
                tok = f"seats.{r['code']}.{q}"
                figures[tok] = _fig(pool, tok)
                got[q] = pool[tok]
            out.append({"name": r["name"], "colour": r["colour"], "m": got["median"],
                        "p5": got["p5"], "p95": got["p95"]})
        for tok in ("majority", FORECAST_ALONE, "seats.band", "generated_date"):
            figures[tok] = _fig(pool, tok)
        spec["ranges"] = {"rows": out, "majority": pool["majority"], "scale": seat_table.SEAT_SCALE,
                          "majority_label": f"{pool['majority']} for a majority",
                          "note": f"Seats: middle, and the range in {pool['seats.band']} of simulations",
                          "lead": f"Chance of one party majority: {pool[FORECAST_ALONE]}"}
        date += f" Figures as of {pool['generated_date']}."
        alt += (" Seats, middle and range: " + ", ".join(f"{o['name']} {o['m']} ({o['p5']} to {o['p95']})" for o in out) +
                f". {pool['majority']} for a majority. One party majority: {pool[FORECAST_ALONE]}.")
    spec["date_line"] = date
    spec["alt"] = alt
    return spec


def seat_rows(html: str) -> list[dict]:
    """The forecast page's seat-table parties, largest first by middle (ties
    by name), Others left out: [{code, name, colour}]. The figures themselves
    are taken from the tokens by name."""
    import build_play
    roster = build_play.roster()
    rows = [(c, int(m)) for c, m in re.findall(r'data-code="([^"]+)" data-m="(\d+)"', html) if c != "OTHERS"]
    if not rows:
        raise OgError("forecast.html: no seat-table rows (data-code, data-m)")
    rows.sort(key=lambda x: (-x[1], roster[x[0]]["name"]))
    return [{"code": c, "name": roster[c]["name"], "colour": roster[c]["colour"]} for c, _m in rows]


def interactive_spec(forecast_json: dict, pool: dict, *, election: dict, site: str) -> dict:
    """/your-forecast/: the call to make a prediction, and our prediction's
    ward map (forecast.json ``start.ward_calls`` over its ``geometry``),
    labelled as ours, with the owner's prediction seal."""
    import build_play
    roster = build_play.roster()
    geom, calls = forecast_json["geometry"], forecast_json["start"]["ward_calls"]
    if len(calls) != len(geom["wards"]):
        raise OgError(f"forecast.json: {len(calls)} ward calls for {len(geom['wards'])} wards")
    figures: dict = {}
    date = _vote_line(election, pool, figures)
    wards = [{"path": w["path"], "colour": roster[c]["colour"]} for w, c in zip(geom["wards"], calls)]
    return {"layout": "interactive", "headline": INTERACTIVE_HEAD, "body": INTERACTIVE_BODY,
            "cta": INTERACTIVE_CTA, "site": site, "date_line": date,
            "map_label": INTERACTIVE_MAP_LABEL, "seal": PREDICTION_SEAL,
            "map": {"W": geom["W"], "H": geom["H"], "wards": wards},
            "figures": figures,
            "alt": f"{INTERACTIVE_HEAD} {INTERACTIVE_BODY} Our prediction's ward map, each ward in "
                   f"the colour of the party we call it for."}


def check(spec: dict) -> dict:
    """Refuse a spec with a character no card face draws, or a figure whose
    string does not appear in the text it carries."""
    bad = uncovered(spec)
    if bad:
        raise OgError("characters the card faces do not carry: " + "; ".join(bad))
    text = json.dumps({k: v for k, v in spec.items() if k not in ("figures", "map", "map_svg")},
                      ensure_ascii=False)
    unused = [t for t, f in spec["figures"].items() if f["display"] not in text]
    if unused:
        raise OgError(f"{spec['slug']}: figures carried but not drawn: {unused}")
    return spec


# --------------------------------------------------------------------------
# drawing


def render_all(specs: list[dict], out_dir: Path) -> dict[str, str]:
    """Draw every spec with ``src/og-pages.mjs`` (one node process, one wasm
    initialisation) into ``out_dir``; returns ``{slug: file name}``. Every
    other file in ``out_dir`` is deleted, so it holds exactly what pages name.
    Any failure stops the build."""
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(specs, ensure_ascii=False)
    try:
        run = subprocess.run(["node", str(RENDERER), "-", str(out_dir)], input=payload,
                             capture_output=True, text=True, cwd=REPO_ROOT)
    except FileNotFoundError:
        raise OgError("og_pages: node is not installed, so no share image can be drawn") from None
    if run.returncode:
        raise OgError(f"og_pages: src/og-pages.mjs failed (is `npm ci` done in worker-api/?):\n{run.stderr}")
    manifest = json.loads(run.stdout)
    want = {s["slug"] for s in specs}
    if set(manifest) != want:
        raise OgError(f"og_pages: drew {sorted(manifest)}, asked for {sorted(want)}")
    keep = set(manifest.values())
    for f in out_dir.iterdir():
        if f.name not in keep:
            f.unlink()
    return manifest
