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

ELECTION = "4 November 2026"


def city_card(slug: str) -> dict:
    """Everything the portal needs about one city, from its own outputs."""
    city = cityconfig.load(slug)
    summary_path = city.processed / "forecast_summary.json"
    card = {
        "slug": slug,
        "name": city.name,
        "formal": city.identity.get("formal_name", city.name),
        "url": "https://" + city.identity["subdomain"],
        "accent": city.site.get("accent", "#a8621f"),
        "council": city.council,
        "majority": city.majority,
        "wards": city.wards,
        "live": summary_path.exists(),
        "headline": None,
    }
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
            detail = (f'<div class="pc-num">{h["leader_seats"]}'
                      f'<span>/{c["council"]}</span></div>'
                      f'<div class="pc-sub">{h["leader"]} leads on the median '
                      f'simulation, {h["second"]} on {h["second_seats"]} — '
                      f'{c["majority"]} needed to govern</div>')
            cta = "Open the forecast →"
        else:
            detail = (f'<div class="pc-num pc-soon">{c["council"]}'
                      f'<span> seats</span></div>'
                      f'<div class="pc-sub">{c["wards"]} wards. Not modelled '
                      f'yet — no numbers, and we would rather say so.</div>')
            cta = "In preparation"
        klass = "pcard" + ("" if c["live"] else " pcard-soon")
        href = f' href="{c["url"]}"' if c["live"] else ""
        tag = "a" if c["live"] else "div"
        return (f'<{tag} class="{klass}"{href} style="--city:{c["accent"]}">'
                f'<div class="pc-name">{c["formal"]}</div>'
                f'{detail}<div class="pc-cta">{cta}</div></{tag}>')

    cards_html = "".join(card_html(c) for c in live + soon)
    return f"""<div class="portal">
  <header class="pmast">
    <div class="kicker">South African local government · {ELECTION}</div>
    <h1>Who governs your city?</h1>
    <p class="standfirst">A voting-district model of each metro: thousands of
    simulated elections, the real seat law, and every assumption a slider you
    can move. No party is barracked for; nothing is hand-typed. Pick a city.</p>
  </header>
  <div class="pcards">{cards_html}</div>
  <p class="pfoot">Each city is modelled from the Electoral Commission's own
  voting-district results. A city appears here with numbers only once its
  allocator reproduces that city's published 2011, 2016 and 2021 councils
  exactly — until then it says "in preparation", because a plausible-looking
  wrong forecast is worse than none.</p>
</div>"""


PORTAL_CSS = """
  .portal{display:flex;flex-direction:column;gap:26px;}
  .pmast{display:flex;flex-direction:column;gap:10px;}
  .pcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));
    gap:14px;}
  .pcard{display:flex;flex-direction:column;gap:7px;padding:20px 20px 18px;
    border:1px solid var(--rule);border-top:3px solid var(--city);
    background:var(--paper-2);text-decoration:none;color:var(--ink);
    transition:border-color .15s,transform .15s;}
  a.pcard:hover{border-color:var(--city);transform:translateY(-2px);}
  .pcard-soon{opacity:.72;}
  .pc-name{font-family:var(--serif);font-weight:600;font-size:20px;}
  .pc-num{font-family:var(--mono);font-size:34px;font-weight:600;
    letter-spacing:-.02em;line-height:1;color:var(--city);}
  .pc-num span{font-size:15px;color:var(--ink-3);}
  .pc-num.pc-soon{color:var(--ink-3);}
  .pc-sub{font-size:12.5px;color:var(--ink-2);line-height:1.45;}
  .pc-cta{font-family:var(--mono);font-size:11.5px;color:var(--city);
    margin-top:4px;}
  .pcard-soon .pc-cta{color:var(--ink-3);}
  .pfoot{font-size:12.5px;color:var(--ink-3);line-height:1.6;max-width:70ch;}
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path("site/portal.html"))
    ap.add_argument("--cities", type=Path, default=Path("cities"))
    args = ap.parse_args(argv)

    slugs = sorted(p.stem for p in args.cities.glob("*.toml"))
    cards = [city_card(s) for s in slugs]
    body = render(cards)

    import build_site  # reuse the site's palette and footer, not its nav
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
 simulated elections, the real seat law, every assumption a slider.">
<meta property="og:url" content="https://whysoserious.city/">
<style>{build_site.STYLE}{PORTAL_CSS}</style>
</head>
<body>
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
