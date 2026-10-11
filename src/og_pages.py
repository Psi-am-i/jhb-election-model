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
``/claims``, each article, and ``/your-forecast/``; and each claim's own page,
``/claims/<slug>`` (owner, 2026-10-11, SHARE-BRIEF item 1: the quote large,
the verdict badge, the party logo, the speaker). The home page,
``/commentary`` and the documents keep the site's ``og.png``.

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

import site_assets

REPO_ROOT = Path(__file__).resolve().parents[1]
RENDERER = REPO_ROOT / "src" / "og-pages.mjs"
#: The owner's stamps: site_assets' one definition.
STAMPS = site_assets.STAMP_SRC
CARD_FONTS_JS = REPO_ROOT / "interactive" / "js" / "card-fonts.js"
TOKENS_CSS = site_assets.CSS_SRC / "tokens.css"

#: Each layout's colour bar: the site's colour for that kind of page, read
#: from tokens.css (its dark theme, the images' ground). The forecast's bar is
#: the ink, as in the approved mock-up: the site's forecast kind (--accent)
#: is the claims' colour too.
KIND_TOKEN = {"claims": "--k-claim", "claim": "--k-claim", "article": "--k-article",
              "forecast": "--ink", "interactive": "--k-interactive"}


def kind_colour(layout: str) -> str:
    """The colour of ``layout``'s bar, from the first :root block of
    tokens.css."""
    css = TOKENS_CSS.read_text(encoding="utf-8")
    block = re.search(r":root\s*\{([^}]*)\}", css)
    m = block and re.search(rf"{re.escape(KIND_TOKEN[layout])}\s*:\s*(#[0-9a-fA-F]{{6}})", block.group(1))
    if not m:
        raise OgError(f"tokens.css: no {KIND_TOKEN[layout]} in its first :root block")
    return m.group(1)


def stamp_path(file: str) -> str:
    """A stamp as og-pages.mjs reads it: its path from the repository root."""
    return (STAMPS / file).relative_to(REPO_ROOT).as_posix()

#: Where the images are served, beside the pages. Not /og/: /og/<n>/… are the
#: Worker's reader-card routes and /og.png its fallback (src/share-edge.js).
OG_DIR = "og-page"

#: The forecast card's coalitions (owner, 2026-10-10, "looks good" on the mock
#: in og-design/make_og.mjs; JUDGEMENT-CALLS §S1). THE ONE DEFINITION of each
#: set: its parties, in groups. The label is written from it (", " inside a
#: group, " + " between groups, the parties' names), and so is its figure, the
#: token ``coal.<render_sheet.coalition_key>.majority``: the share of
#: simulations in which they hold a majority together. /forecast's coalition
#: table prints that token for the sets it lists; for a set it does not, the
#: image computes it over every party's seats (``stats.coalition_majority``)
#: and records it, as a generated token, under the forecast page.
FORECAST_COALITIONS = (
    (("ANC",), ("DA",)),
    (("DA", "ASA", "PA"), ("IFP", "VFPLUS", "ACDP")),
    (("ANC", "EFF", "PA"), ("ALJAMAAH",)),
    (("ANC",), ("EFF",), ("MK",)),
)


def coalition_token(groups) -> str:
    """The token holding a coalition's majority chance, as /forecast names it."""
    import render_sheet
    return f"coal.{render_sheet.coalition_key([c for g in groups for c in g])}.majority"


def coalition_label(groups, roster: dict) -> str:
    return " + ".join(", ".join(roster[c]["name"] for c in g) for g in groups)
#: The forecast card's other figures: most seats, one party alone.
FORECAST_LARGEST = (("ANC", "p_anc_largest"), ("DA", "p_da_largest"))
FORECAST_ALONE = "p_alone"

#: The article with a designed visual, by ``og_visual`` in articles.toml: the
#: seat ranges of the largest parties, this many rows.
SEAT_RANGE_ROWS = 6
VISUALS = {"seat-ranges"}

#: The interactive card's words (the approved mock-up, og-design/make_og.mjs,
#: 43bbf59). The map is our prediction's, labelled as such by the owner's
#: OFFICIAL PREDICTION seal over its corner.
INTERACTIVE_HEAD = "Know Politics?"
INTERACTIVE_BODY = ("Pick your winners, seal your prediction and let's see if you "
                    "can beat us on election day.")
INTERACTIVE_CTA = "Make yours at"
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
    if output.startswith(CLAIM_DIR + "/") and output.endswith(".html"):
        return claim_image_slug(output.removeprefix(CLAIM_DIR + "/").removesuffix(".html")), "claim"
    return None


#: Where each claim's own page is written: ``<out>/claims/<slug>.html``,
#: served at ``/claims/<slug>`` (build_site.claim_pages).
CLAIM_DIR = "claims"


def claim_image_slug(slug: str) -> str:
    """A claim page's image slug: ``claim-<slug>``, which no other page's
    ``<slug>-<12 letters>`` can be read as (the claims page's is ``claims``)."""
    return f"claim-{slug}"


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


#: The marker figure_pool leaves for a token pages printed in more than one
#: way: drawing it is refused (``_fig``), carrying it is not.
AMBIGUOUS = "\x00ambiguous"


def figure_pool(published: list[dict], registry: dict, ctx: dict) -> tuple[dict[str, str], dict[str, dict]]:
    """``(pool, records)``: every token a page printed, by name, with the
    string it printed, and the record ``stats.render`` made of it (what the
    publication ledger takes). A token printed differently on two pages is
    marked :data:`AMBIGUOUS`, and an image that draws it is refused (it could
    show only one). Each forecast-card coalition no page prints is added as a
    generated token (:func:`coalition_figure`)."""
    seen: dict[str, str] = {}
    records: dict[str, dict] = {}
    for r in published:
        t = r.get("token")
        if not t:
            continue
        seen[t] = r["display"] if seen.get(t, r["display"]) == r["display"] else AMBIGUOUS
        records.setdefault(t, r)
    for groups in FORECAST_COALITIONS:
        t = coalition_token(groups)
        if t not in seen:
            seen[t], records[t] = coalition_figure(groups, registry, ctx)
    return seen, records


def coalition_figure(groups, registry: dict, ctx: dict) -> tuple[str, dict]:
    """A coalition's majority chance as a generated token, rendered by
    ``stats.render`` as a page renders one (format "chance", as /forecast's
    coalition table prints it): ``(display, record)``."""
    import stats as statlib
    members = [c for g in groups for c in g]
    p = statlib.coalition_majority(members, ctx)
    if p is None:
        raise OgError(f"no draws to compute {coalition_token(groups)} from")
    n = len(ctx.get("draws") or [])
    text = (f"{{{{@{coalition_token(groups)}={p:.6f};chance;seat_detail_draws.csv, {n:,} "
            f"simulations, every party's seats}}}}")
    rec: list[dict] = []
    out, _drift, unresolved = statlib.render(text, registry, ctx, wrap=False, record=rec)
    if unresolved or len(rec) != 1:
        raise OgError(f"{coalition_token(groups)} did not render: {unresolved}")
    return out, rec[0]


def ledger_records(specs: list[dict], records: dict[str, dict]) -> list[dict]:
    """One publication-ledger record per figure each image prints, under the
    page that carries the image (``spec["page"]``), so the image's figures
    get ledger rows, change diffs and drift checks like the page's own. An
    image is not a dated passage, whatever the page the figure came from."""
    return [{**records[tok], "page": s["page"], "dated": False, "asof": ""}
            for s in specs for tok in s["figures"]]


def _fig(pool: dict, token: str) -> dict:
    if token not in pool:
        raise OgError(f"the share image needs {token}, which no page printed")
    if pool[token] == AMBIGUOUS:
        raise OgError(f"the share image needs {token}, which pages print in more than one way")
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
                if k not in ("map", "map_svg", "badge", "logo", "seal", "slug", "layout", "page", "kind_colour"):
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
    """The forecast page's ward map as the image draws it: the <svg> that
    holds the first <pattern> (contested wards are striped), reduced to its
    viewBox, its <pattern> definitions and its <path> elements. The key, the
    north mark and anything else the page draws in other elements are left
    out by what they are, not by where the page puts them."""
    i = html.find("<pattern")
    if i < 0:
        raise OgError("forecast.html: no striped ward map (<pattern>) to draw")
    a, b = html.rfind("<svg", 0, i), html.find("</svg>", i)
    m = html[a:b]
    vb = re.search(r'viewBox="([^"]+)"', m[:m.find(">") + 1])
    if not vb:
        raise OgError("forecast.html: the ward map's <svg> has no viewBox")
    patterns = re.findall(r"<pattern\b[\s\S]*?</pattern>", m)
    paths = re.findall(r"<path\b[^>]*>", m)
    return (f'<svg viewBox="{vb.group(1)}"><defs>{"".join(patterns)}</defs>'
            + "".join(paths) + "</svg>")


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
    for groups in FORECAST_COALITIONS:
        tok = coalition_token(groups)
        figures[tok] = _fig(pool, tok)
        coalitions.append({"label": coalition_label(groups, roster), "value": pool[tok]})
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
        items.append({"verdict": c["verdict"], "badge": stamp_path(verdict_badge(c["verdict"])),
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


def claim_spec(html: str, claim: dict) -> dict:
    """A claim's own page: its quote, its verdict badge, its party's logo and
    name, and who said it. The verdict is the one the page prints (checked
    against it); the image draws no figure, so the page's tokens stay the
    page's."""
    import build_play
    roster = build_play.roster()
    printed = re.findall(r'<span class="verdict v-[a-z]+">([^<]+)</span>', html)
    word = " ".join(claim["verdict"].upper().split())
    if printed != [word]:
        raise OgError(f"claims/{claim.get('slug')}: the page prints verdicts {printed}, "
                      f"claims.toml has {word!r}")
    logo = REPO_ROOT / "site" / "logos" / f"{claim.get('logo', claim['party'])}.png"
    party = roster[claim["party"]]["name"]
    speaker = claim["speaker"].split(",")[0]
    quote = " ".join(claim["quote"].split())
    return {"layout": "claim", "quote": quote, "verdict": claim["verdict"],
            "badge": stamp_path(verdict_badge(claim["verdict"])),
            "code": claim["party"], "party": party, "colour": roster[claim["party"]]["colour"],
            "logo": logo.name if logo.is_file() else None, "speaker": speaker,
            "date_line": f"Tested against the forecast. Published {claim['published']}.",
            "figures": {},
            "alt": f"\u201c{quote}\u201d {speaker}, {party}. Verdict: {claim['verdict']}."}


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
            "seal": stamp_path(PREDICTION_SEAL),
            "map": {"W": geom["W"], "H": geom["H"], "wards": wards},
            "figures": figures,
            "alt": f"{INTERACTIVE_HEAD} {INTERACTIVE_BODY} Our prediction's ward map, each ward in "
                   f"the colour of the party we call it for."}


def check(spec: dict) -> dict:
    """Refuse a spec with a character no card face draws, or a figure whose
    string does not appear in the text it carries."""
    spec.setdefault("kind_colour", kind_colour(spec["layout"]))
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
    other file in ``out_dir`` is deleted, so it holds exactly what pages name;
    a directory there is refused, never removed. Any failure stops the build."""
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
        if f.is_dir():
            raise OgError(f"og_pages: {f} is a directory; {out_dir.name}/ holds the share "
                          "images only, and nothing here removes a directory")
        if f.name not in keep:
            f.unlink()
    return manifest
