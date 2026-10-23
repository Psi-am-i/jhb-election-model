"""Build the portal at whysoserious.city — one card per city.

The portal is deliberately thin: it exists to route people to a city and to
say honestly which cities are actually modelled yet. A card shows that
city's current headline number pulled from its own `forecast_summary.json`,
so the hub can never quietly disagree with the page it links to. Cities
without a model yet say so plainly rather than teasing.

    python src/build_portal.py            # -> site/portal.html
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cityconfig
import site_assets

ELECTION = "4 November 2026"
#: A city card's colour when its cities/<slug>.toml declares no [site] accent.
DEFAULT_ACCENT = "#a8621f"


def city_card(slug: str) -> dict:
    """Everything the portal needs about one city, from its own outputs."""
    city = cityconfig.load(slug)
    summary_path = city.processed / "forecast_summary.json"
    # ⛔ A CITY WITHOUT A SUBDOMAIN IS NOT A CRASH, IT IS A CITY WITH NO PAGE
    # YET. This read `city.identity["subdomain"]` unconditionally, and the
    # seven metros ingested on 2026-09-01 carry no subdomain — so the portal
    # died with a KeyError from the moment the model grew beyond two cities,
    # and `build_all` stopped before the site every time. The card already has
    # an "In preparation" state for exactly these cities; it just never got to
    # use it. A city that IS live and has no address is a different thing and
    # refuses below.
    subdomain = city.identity.get("subdomain")
    card = {
        "slug": slug,
        "name": city.name,
        "formal": city.identity.get("formal_name", city.name),
        "url": ("https://" + subdomain) if subdomain else None,
        "accent": city.site.get("accent", DEFAULT_ACCENT),
        "council": city.council,
        "majority": city.majority,
        "wards": city.wards,
        "live": summary_path.exists(),
        "headline": None,
    }
    if card["live"] and not subdomain:
        raise SystemExit(
            f"{slug} has a forecast ({summary_path}) but no `subdomain` in its "
            f"[identity] block, so the portal would link its card nowhere. "
            f"Either declare the address it publishes at, or move the summary "
            f"out of the way — a live card with a dead link is worse than a "
            f"city the portal says is in preparation.")
    if card["live"]:
        s = json.loads(summary_path.read_text(encoding="utf-8"))
        top = sorted(s["parties"].items(), key=lambda kv: -kv[1]["median"])[:2]
        card["headline"] = {
            "leader": top[0][0], "leader_seats": round(top[0][1]["median"]),
            "second": top[1][0], "second_seats": round(top[1][1]["median"]),
            "pair": s["structural"].get("P(ANC+DA is winning)"),
        }
    return card


def render(cards: list[dict]) -> str:
    live = [c for c in cards if c["live"]]
    soon = [c for c in cards if not c["live"]]

    def card_html(c: dict) -> str:
        if c["live"]:
            h = c["headline"]
            # ⛔ A TIE IS NOT A LEAD. With both medians at 66 this printed
            # "DA leads on the median simulation, ANC on 66", the leader
            # chosen by dictionary order (R4, 2026-09-30) — the defect
            # `render_home` already guards against for the largest-party odds.
            # A median is per party, not one simulation; a tie names the two
            # parties alphabetically (STYLE.md rule 7).
            def the(name: str) -> str:
                return f"the {name}" if name.isupper() else name
            if h["leader_seats"] == h["second_seats"]:
                a, b = sorted((h["leader"], h["second"]))
                sub = (f'{the(a)} and {the(b)} each have a median of '
                       f'{h["leader_seats"]} seats')
            else:
                sub = (f'{the(h["leader"])}\'s median is {h["leader_seats"]} '
                       f'seats and {the(h["second"])}\'s is {h["second_seats"]}')
            sub = sub[0].upper() + sub[1:]
            detail = (f'<div class="pc-num">{h["leader_seats"]}'
                      f'<span>/{c["council"]}</span></div>'
                      f'<div class="pc-sub">{sub}. '
                      f'{c["majority"]} is a majority.</div>')
            cta = "Open the forecast →"
        else:
            # a city with no 2026 forecast is described by its config's
            # top-level structure, which is its 2021 council (cities/*.toml)
            detail = (f'<div class="pc-num pc-soon">{c["council"]}'
                      f'<span> seats in 2021</span></div>'
                      # "Not modelled yet" was flatly contradicted by
                      # /about, which publishes a 2021 backtest for all eight
                      # metros. What is missing is a 2026 FORECAST, and the
                      # card has to say which of the two it means.
                      f'<div class="pc-sub">{c["wards"]} wards in 2021. No 2026 '
                      f'forecast yet — its 2021 backtest is on the '
                      f'<a href="https://joburg.whysoserious.city/about">'
                      f'scoring page</a>.</div>')
            cta = "In preparation"
        klass = "pcard" + ("" if c["live"] else " pcard-soon")
        href = f' href="{c["url"]}"' if c["live"] else ""
        tag = "a" if c["live"] else "div"
        # the card's colour is its city's class (src/site_assets.colour_css,
        # from cities/<slug>.toml): the page carries no style
        return (f'<{tag} class="{klass} city-{c["slug"]}"{href}>'
                f'<div class="pc-name">{c["formal"]}</div>'
                f'{detail}<div class="pc-cta">{cta}</div></{tag}>')

    cards_html = "".join(card_html(c) for c in live + soon)
    return f"""<div class="portal">
  <header class="pmast">
    <a class="pm-logo" href="./" aria-label="whysoserious.city — open city modelling &amp; forecasting">{site_assets.umbrella_svg("wsc-logo")}</a>
    <div class="kicker">South African local government · {ELECTION}</div>
    <h1>Who governs your city?</h1>
    <!-- ⛔ NO SLIDER EXISTS ON ANY PAGE. This read "every assumption a slider
         you can move", in the present tense, on the one page `deploy_check`
         does not scan. Describe what is here; the interactive can change this
         sentence when it ships and not before. -->
    <p class="standfirst">Each forecast here is thousands of simulated
    elections under the real seat law, with every assumption written down where
    you can check it. A metro without a 2026 forecast yet is marked in
    preparation. Pick a city.</p>
  </header>
  <div class="pcards">{cards_html}</div>
  <p class="pfoot">Each city is modelled from the Electoral Commission's own
  voting-district results, and every metro's seat calculation reproduces its
  published 2011, 2016 and 2021 councils. A city shows numbers here once it has
  a 2026 forecast; until then it says "in preparation".</p>
</div>"""


# The portal's own rules are src/css/page-portal.css, scoped to its <body>
# (`pg-portal`) in the site's one stylesheet, on top of the documents' rules
# (`pg-doc`).



def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("site/portal.html"))
    ap.add_argument("--cities", type=Path, default=Path("cities"))
    args = ap.parse_args(argv)

    slugs = sorted(p.stem for p in args.cities.glob("*.toml"))
    cards = [city_card(s) for s in slugs]
    body = render(cards)

    import build_site  # reuse the site's head and footer, not its nav
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Who governs your city? \u00b7 South African metro election models</title>
<meta property="og:site_name" content="whysoserious.city">
<meta property="og:type" content="website">
<meta property="og:title" content="Who governs your city?">
<meta property="og:description" content="Voting-district models of South
 Africa's metros for the {ELECTION} local government election: thousands of
 simulated elections, the real seat law, every assumption written down.">
<meta property="og:url" content="https://whysoserious.city/">
{build_site.SITE_HEAD}</head>
<body class="pg-doc pg-portal">
<div class="page">
{body}
{build_site.FOOTER}
</div>
</body>
</html>
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    live = sum(1 for c in cards if c["live"])
    print(f"portal: {len(cards)} cities ({live} live) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
