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

#: The forecast card's figures: the two largest parties' chances of the most
#: seats (the card prints them as its largest-party line), and the chance of
#: one party alone with a majority (the seat-range article's).
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
INTERACTIVE_BODY = ("Pick your winners, seal your prediction and see how it ranks "
                    "against the result.")
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


def figure_pool(published: list[dict]) -> tuple[dict[str, str], dict[str, dict]]:
    """``(pool, records)``: every token a page printed, by name, with the
    string it printed, and the record ``stats.render`` made of it (what the
    publication ledger takes). A token printed differently on two pages is
    marked :data:`AMBIGUOUS`, and an image that draws it is refused (it could
    show only one)."""
    seen: dict[str, str] = {}
    records: dict[str, dict] = {}
    for r in published:
        t = r.get("token")
        if not t:
            continue
        seen[t] = r["display"] if seen.get(t, r["display"]) == r["display"] else AMBIGUOUS
        records.setdefault(t, r)
    return seen, records


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
                if k not in ("map", "map_svg", "badge", "logo", "logos", "seal", "slug", "layout", "page", "kind_colour", "result", "geometry"):
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


def forecast_spec(pool: dict, *, yfd: dict, out: Path, election: dict, headline: str) -> dict:
    """/forecast: our forecast's one card, the card the share sheet of
    /your-forecast/ draws (play-card.js, through og-pages.mjs). Its figures are
    the compute result for the published settings, which page.py gives run
    natively (interactive/tools/native_play.py --result untouched), and its date
    is forecast.json's ``forecast_date``; nothing here is typed. The chances the
    pages print (``p_anc_largest``, ``p_da_largest``), the council's size and
    the date the pages print must be the card's own, or the build refuses."""
    import sys
    import build_play
    run = subprocess.run([sys.executable, str(REPO_ROOT / "interactive" / "tools" / "native_play.py"),
                          "--result", "untouched"], capture_output=True, text=True, cwd=REPO_ROOT)
    if run.returncode:
        raise OgError("og_pages: the published forecast could not be computed natively "
                      f"(interactive/tools/native_play.py):\n{run.stderr[-2000:]}")
    r = json.loads(run.stdout)
    if r.get("refused"):
        raise OgError(f"og_pages: the published forecast was refused: {r['refused']}")
    date = _long(yfd["forecast_date"])
    if date != pool["generated_date"]:
        raise OgError(f"forecast.json's forecast_date reads {date!r}, the pages print {pool['generated_date']!r}")
    roster = build_play.roster()
    for code, tok in FORECAST_LARGEST:
        if r["largest"][code]["text"] != pool[tok]:
            raise OgError(f"the card's chance for {code} to hold the most seats is {r['largest'][code]['text']!r}, "
                          f"the pages print {pool[tok]!r}")
    if str(int(r["council"])) != pool["council_size"]:
        raise OgError(f"the card's council is {r['council']} seats, the pages print {pool['council_size']}")
    codes = sorted(set(r["shown"]) | set(r["largest"]))
    logos = {c: f"{c}.png" for c in codes if roster[c]["logo"]}
    geometry = json.loads((out / "your-forecast" / "ward_paths.json").read_text(encoding="utf-8"))
    when = _long(election["date"])
    figures = {"generated_date": _fig(pool, "generated_date"), "council_size": _fig(pool, "council_size"),
               **{tok: _fig(pool, tok) for _c, tok in FORECAST_LARGEST}}
    top = ", ".join(f"{pool[tok]} chance it's {roster[code]['article']}{roster[code]['name']}"
                    for code, tok in FORECAST_LARGEST)
    alt = (f"whysoserious.city forecast, {date}. {election['city']} council, {when}, {pool['council_size']} seats. "
           f"Most seats: {top}. Ward map, contested wards striped; each party at its middle seat count.")
    return {"layout": "forecast", "headline": headline, "date_line": f"Forecast of {date}.",
            "result": r, "geometry": geometry, "when": when, "forecast_date": yfd["forecast_date"],
            "roster": {c: {k: roster[c][k] for k in ("name", "colour", "article", "logo")} for c in codes},
            "logos": logos, "figures": figures, "alt": alt}


def verdict_badge(word: str) -> str:
    """The owner's badge file for a verdict word (render_sheet.VERDICT_BADGE),
    refusing a word with none."""
    import render_sheet
    f = render_sheet.VERDICT_BADGE.get(" ".join(word.upper().split()))
    if f is None or not (STAMPS / f).is_file():
        raise OgError(f"no badge for the verdict {word!r} (render_sheet.VERDICT_BADGE, src/stamps/)")
    return f


# --------------------------------------------------------------------------
# a claim, read the one way every claim page, card and image reads it

_VERDICT_SPAN = re.compile(r'<span class="verdict v-[a-z]+">([^<]+)</span>')


def verdict_word(verdict: str) -> str:
    """A verdict as a page prints it: upper case, single spaces."""
    return " ".join(str(verdict).upper().split())


def printed_verdicts(html: str) -> list[str]:
    """Every verdict badge's words in ``html``, in page order (render_sheet's
    ``<span class="verdict v-…">``)."""
    return _VERDICT_SPAN.findall(html)


def claim_logo(claim: dict) -> str | None:
    """The file name of a claim's party logo in site/logos/, or None."""
    logo = REPO_ROOT / "site" / "logos" / f"{claim.get('logo', claim['party'])}.png"
    return logo.name if logo.is_file() else None


def speaker_name(claim: dict) -> str:
    """Who said it, without their role: the part of ``speaker`` before its
    first comma."""
    return claim["speaker"].split(",")[0].strip()


def claim_party(claim: dict) -> str:
    """The party's name on a claim's own page, its tab title and its image:
    claims.toml's ``party_name``, the name the claim's card prints, so the
    three cannot name the party differently from the card under them."""
    return claim["party_name"]


def claims_spec(html: str, claims: list[dict], *, headline: str) -> dict:
    """/claims: one badge per party, the first claim per party in claims.toml
    order. Each verdict is the one the page prints (checked against it)."""
    import build_play
    roster = build_play.roster()
    printed = Counter(printed_verdicts(html))
    typed = Counter(verdict_word(c["verdict"]) for c in claims)
    if printed != typed:
        raise OgError(f"claims.html prints verdicts {dict(printed)}, claims.toml has "
                      f"{dict(typed)}: the image would not show the page's verdicts")
    items, seen = [], set()
    for c in claims:
        if c["party"] in seen:
            continue
        seen.add(c["party"])
        # the roster's short name: the strip's columns are narrow
        items.append({"verdict": c["verdict"], "badge": stamp_path(verdict_badge(c["verdict"])),
                      "code": c["party"], "party": roster[c["party"]]["name"],
                      "colour": roster[c["party"]]["colour"],
                      "logo": claim_logo(c), "speaker": speaker_name(c)})
    latest = max((c["published"] for c in claims),
                 key=lambda d: datetime.strptime(d, "%d %B %Y"))
    alt = (f"{headline}. " + "; ".join(f"{i['party']}: {i['verdict']} ({i['speaker']})" for i in items) + ".")
    return {"layout": "claims", "headline": headline,
            "date_line": f"One claim per party, each tested against the forecast. Latest tested {latest}.",
            "items": items, "figures": {}, "alt": alt}


def run_date() -> str:
    """The run the pages are built on, as "21 October 2026"
    (forecast_summary.json ``_generated``)."""
    import cityconfig
    from datetime import date
    g = json.loads((cityconfig.active().processed / "forecast_summary.json").read_text(encoding="utf-8"))["_generated"]
    y, m, d = (int(x) for x in str(g)[:10].split("-"))
    return f"{d} {date(y, m, d):%B %Y}"


def claim_spec(html: str, claim: dict) -> dict:
    """A claim's own page: its quote, its verdict badge, its party's logo and
    name, and who said it. The verdict is the one the page prints (checked
    against it); the image draws no figure, so the page's tokens stay the
    page's."""
    import build_play
    roster = build_play.roster()
    printed, word = printed_verdicts(html), verdict_word(claim["verdict"])
    if printed != [word]:
        raise OgError(f"claims/{claim.get('slug')}: the page prints verdicts {printed}, "
                      f"claims.toml has {word!r}")
    party, speaker = claim_party(claim), speaker_name(claim)
    quote = " ".join(claim["quote"].split())
    # The tested statement only where the badge needs it to make sense
    # (claims.toml `card_test = true`); otherwise one reason and a pointer to
    # the page (owner, 2026-10-22). A settled verdict's reason is its
    # `settled` text; a chance verdict's is render_sheet.VERDICT_REASON.
    import render_sheet
    if claim.get("card_test"):
        statement, reason = " ".join(claim["label"].split()), None
    else:
        statement = None
        if claim["verdict"] in render_sheet.SETTLED_VERDICTS:
            why = " ".join(str(claim.get("card_reason") or "").split())
            if not why:
                raise OgError(f"claims/{claim.get('slug')}: a settled verdict's card needs card_reason")
        else:
            why = render_sheet.VERDICT_REASON[verdict_word(claim["verdict"])]
        reason = why
    return {"layout": "claim", "quote": quote, "verdict": claim["verdict"],
            "badge": stamp_path(verdict_badge(claim["verdict"])),
            "code": claim["party"], "party": party, "colour": roster[claim["party"]]["colour"],
            "logo": claim_logo(claim), "speaker": speaker,
            # beside the stamp: the tested statement (claims.toml's label), or
            # the reason and "see more"
            "statement": statement, "reason": reason,
            "more": "Click to see more analysis of this claim." if reason else None,
            # the forecast the verdict is from: the run the page is built on
            # (owner, 2026-10-22: the card said the first test's date)
            # A settled verdict (FALSE/TRUE) rests on the figures of the day it
            # was tested, which the page dates; it still stands on the current
            # run, so both dates (review 2026-10-22, owner: the card said only
            # the first test's date)
            "date_line": (f"Tested on {claim['published']}; the verdict stands on the forecast of {run_date()}."
                          if claim["verdict"] in render_sheet.SETTLED_VERDICTS else
                          f"Tested against the whysoserious.city forecast of {run_date()}."),
            # the top bar takes the party's colour from the roster, like its chip
            "kind_colour": roster[claim["party"]]["colour"],
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
    text = json.dumps({k: v for k, v in spec.items() if k not in ("figures", "map", "map_svg", "result", "geometry")},
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
