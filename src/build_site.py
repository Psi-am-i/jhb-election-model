"""Build the public site (joburg.whysoserious.org) into ./site.

Same principle as render_sheet.py: styled artefacts are generated from the
canonical sources, never hand-copied, so they cannot go stale.

Two kinds of page:

* **Rendered documents** — the four Markdown records (methodology, model log,
  sources, the original plan) converted to house-styled HTML. The Markdown
  stays canonical; regenerate rather than editing the HTML.
* **Copied artefacts** — forecast-sheet.html, forecast-interactive.html and
  model-review.html are already house-styled deliverables and are copied
  verbatim under stable public names.

Plus a hand-authored index.html hub with the drill-down cards.

Usage:
    python src/build_site.py          # -> ./site/
Then deploy:
    npx wrangler deploy               # static-assets Worker, see wrangler.toml
"""

from __future__ import annotations

import argparse
import re
import shutil
from datetime import date
from pathlib import Path

import markdown

import stats as statlib

STYLE = """
  :root{
    --paper:#fbfbfa; --paper-2:#f2f3f1; --rule:#d9dbd6; --rule-soft:#e7e8e4;
    --ink:#1a1d1b; --ink-2:#4a4f4b; --ink-3:#767b76;
    --accent:#a8621f; --accent-soft:#f0e2d5; --good:#2f6d4a;
    --serif:"Iowan Old Style","Palatino Linotype",Palatino,Georgia,"Times New Roman",serif;
    --sans:ui-sans-serif,system-ui,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  }
  @media (prefers-color-scheme:dark){
    :root{
      --paper:#141715; --paper-2:#1c201d; --rule:#333833; --rule-soft:#282d29;
      --ink:#eceee9; --ink-2:#b6bcb6; --ink-3:#868d86;
      --accent:#d9954f; --accent-soft:#3a2a1a; --good:#6fb98a;
    }
  }
  *{box-sizing:border-box;margin:0;}
  body{background:var(--paper);color:var(--ink);font-family:var(--sans);
    font-size:15px;line-height:1.62;-webkit-font-smoothing:antialiased;}
  .page{max-width:900px;margin:0 auto;padding:28px 24px 72px;}

  .topnav{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;
    justify-content:space-between;font-family:var(--mono);font-size:14px;color:var(--ink-3);
    border-bottom:1px solid var(--rule);padding-bottom:10px;margin-bottom:26px;}
  .topnav a{color:var(--ink-3);text-decoration:none;}
  .topnav a:hover{color:var(--accent);}
  .topnav a.home{color:var(--accent);font-weight:600;}
  .topnav a.active{color:var(--accent);}

  .kicker{font-size:11px;font-weight:650;letter-spacing:.16em;text-transform:uppercase;
    color:var(--accent);margin-bottom:10px;}
  h1{font-family:var(--serif);font-weight:600;font-size:clamp(28px,4.6vw,40px);
    line-height:1.12;letter-spacing:-.012em;text-wrap:balance;margin:0 0 10px;}
  .standfirst{font-family:var(--serif);font-size:clamp(16px,2.2vw,19px);line-height:1.5;
    color:var(--ink-2);text-wrap:pretty;margin-bottom:6px;}
  .dateline{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:var(--mono);
    font-size:11.5px;color:var(--ink-3);border-top:1px solid var(--rule);
    border-bottom:1px solid var(--rule);padding:9px 0;margin:14px 0 8px;}
  .dateline b{color:var(--ink-2);font-weight:600;}

  h2{font-family:var(--serif);font-weight:600;font-size:24px;line-height:1.2;
    letter-spacing:-.006em;margin:42px 0 4px;padding-top:18px;
    border-top:1px solid var(--rule);}
  h3{font-family:var(--serif);font-weight:600;font-size:18px;line-height:1.3;margin:28px 0 2px;}
  h4{font-size:14px;font-weight:650;margin:20px 0 2px;}
  p{margin:10px 0;}
  ul,ol{margin:10px 0;padding-left:20px;
    display:flex;flex-direction:column;gap:5px;}
  strong{font-weight:650;}
  hr{border:none;border-top:1px solid var(--rule-soft);margin:26px 0;}
  a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px;}

  code{font-family:var(--mono);font-size:.86em;background:var(--paper-2);
    border:1px solid var(--rule-soft);border-radius:3px;padding:.08em .34em;}
  pre{background:var(--paper-2);border:1px solid var(--rule-soft);border-radius:5px;
    padding:13px 15px;overflow-x:auto;margin:14px 0;line-height:1.5;}
  pre code{background:none;border:none;padding:0;font-size:12.5px;color:var(--ink-2);}

  .tablewrap{overflow-x:auto;margin:14px 0;}
  table{border-collapse:collapse;width:100%;font-size:13.5px;}
  th{font-family:var(--sans);font-size:10.5px;font-weight:650;letter-spacing:.1em;
    text-transform:uppercase;color:var(--ink-3);text-align:left;
    padding:0 12px 7px 0;border-bottom:1px solid var(--rule);vertical-align:bottom;}
  td{padding:8px 12px 8px 0;border-bottom:1px solid var(--rule-soft);
    vertical-align:top;color:var(--ink-2);}
  td:first-child{color:var(--ink);}

  blockquote{border-left:2px solid var(--accent);background:var(--paper-2);
    padding:10px 16px;margin:14px 0;color:var(--ink-2);}
  blockquote p{margin:6px 0;}
  blockquote h3,blockquote h4{margin-top:8px;}

  .colophon{font-family:var(--mono);font-size:11px;line-height:1.65;color:var(--ink-3);
    border-top:1px solid var(--rule);padding-top:12px;margin-top:48px;}
  .sitefooter{font-family:var(--mono);font-size:11px;line-height:1.8;color:var(--ink-3);
    border-top:1px solid var(--rule);padding-top:14px;margin-top:20px;}
  .sitefooter a{color:var(--ink-3);}
  .sitefooter a:hover{color:var(--accent);}

  /* index cards */
  .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
    gap:14px;margin:22px 0;}
  .card{display:flex;flex-direction:column;gap:6px;border:1px solid var(--rule-soft);
    background:var(--paper-2);padding:16px 18px;text-decoration:none;color:var(--ink);
    transition:border-color .15s;}
  .card:hover{border-color:var(--accent);}
  .card.hero{background:var(--accent-soft);border-color:color-mix(in srgb,var(--accent) 35%,transparent);}
  .card .t{font-family:var(--serif);font-weight:600;font-size:19px;line-height:1.25;}
  .card .d{font-size:13px;color:var(--ink-2);line-height:1.45;}
  .card .tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;
    text-transform:uppercase;color:var(--accent);}

  @media print{
    body{background:#fff;color:#000;font-size:10pt;}
    .page{max-width:none;padding:0;}
    .topnav{display:none;}
    h2,h3{break-after:avoid;} table,blockquote,pre{break-inside:avoid;}
  }
"""

NAV_ITEMS = [
    ("./", "forecast"),
    ("interactive", "interactive"),
    ("methodology", "methodology"),
    ("review", "review"),
    ("sources", "sources"),
    ("plan", "plan"),
    ("https://github.com/Psi-am-i/jhb-election-model", "source-code"),
]


def nav_for(active_href: str) -> str:
    """The site nav with the current page held in the accent colour."""
    links = "\n".join(
        f'  <a{" class=\"active\"" if href == active_href else ""} '
        f'href="{href}">{label}</a>'
        for href, label in NAV_ITEMS
    )
    return ('<nav class="topnav">\n'
            '  <a class="home" href="./">joburg.whysoserious.city</a>\n'
            f"{links}\n</nav>")

# Standalone nav styling injected into the artefact pages (which carry their
# own stylesheets); the rendered documents get it via STYLE above.
NAV_CSS = """<style>
  /* site-wide standard container: every page, same width and padding */
  a{color:var(--accent);text-decoration-thickness:1px;text-underline-offset:2px;}
  .sheet{max-width:900px;margin:0 auto;padding:28px 24px 72px;}
  @media (min-width:1440px){.sheet{max-width:1040px;}}
  @media (max-width:560px){.sheet{padding:20px 14px 56px;}h1{text-wrap:pretty;}}
  .layout{grid-template-columns:minmax(0,270px) minmax(0,1fr);}
  @media (max-width:840px){.layout{grid-template-columns:1fr;}}
{FOOTER_CSS_PLACEHOLDER}
  .topnav{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;
    justify-content:space-between;font-family:var(--mono);font-size:14px;color:var(--ink-3);
    border-bottom:1px solid var(--rule);padding-bottom:10px;margin-bottom:22px;}
  .topnav a{color:var(--ink-3);text-decoration:none;}
  .topnav a:hover{color:var(--accent);}
  .topnav a.home{color:var(--accent);font-weight:600;}
  .topnav a.active{color:var(--accent);}
</style>"""



OG_META = """<meta property="og:site_name" content="Johannesburg 2026 Election Model">
<meta property="og:type" content="website">
<meta property="og:title" content="Who governs Johannesburg after 4 November 2026?">
<meta property="og:description" content="5,000 simulations of the November vote. Nobody wins — and an obscure clause of the seat law hands the shrinking ANC an unbreakable floor. Explore every ward, every coalition, every assumption.">
<meta property="og:url" content="https://joburg.whysoserious.city/">
<link rel="canonical" href="https://joburg.whysoserious.city/">
<meta property="og:image" content="https://joburg.whysoserious.city/share.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Hillbrow Tower silhouetted against a Johannesburg sunset">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://joburg.whysoserious.city/share.jpg">
"""

FOOTER = """<footer class="sitefooter">
  <div>Johannesburg · 2026 Local Government Election Model · Free to distribute with attribution and linkback.</div>
  <div><a href="./">joburg.whysoserious.city</a> · model design by <a href="mailto:psi@whysoserious.city">psi@whysoserious.city</a> · whysoserious.city is part of picnic labs · <a href="https://github.com/Psi-am-i/jhb-election-model">source &amp; data on GitHub</a></div>
</footer>"""

FOOTER_CSS = """
  .sitefooter{font-family:var(--mono);font-size:11px;line-height:1.8;color:var(--ink-3);
    border-top:1px solid var(--rule);padding-top:14px;margin-top:44px;}
  .sitefooter a{color:var(--ink-3);}
  .sitefooter a:hover{color:var(--accent);}"""


NAV_CSS = NAV_CSS.replace("{FOOTER_CSS_PLACEHOLDER}", FOOTER_CSS)


def inject_nav(html: str, active_href: str) -> str:
    """Give an artefact page the site navigation: CSS into <head>, nav bar
    at the top of its content container so it aligns with the content."""
    html = html.replace("</head>", OG_META + NAV_CSS + "\n</head>", 1)
    marker = '<div class="sheet">'
    html = html.replace(marker, marker + "\n" + nav_for(active_href), 1)
    # Footer goes at the end of the content container so it aligns with it.
    # Marker only — an earlier fallback guessed at closing tags and prepended
    # the footer above the doctype on the sheet. Fail loudly instead.
    marker_close = "</div><!-- /sheet -->"
    if marker_close not in html:
        raise SystemExit("artefact page lacks the </div><!-- /sheet --> container marker")
    return html.replace(marker_close, FOOTER + "\n" + marker_close, 1)

# source markdown -> (output, kicker, standfirst)
DOCS = {
    "docs-public/methodology.md": (
        "methodology.html",
        "Methodology",
        "The machinery in plain language: how the council is actually "
        "elected, how the simulation runs, what is validated — and what can "
        "only be stated honestly.",
    ),
    "docs-public/review.md": (
        "review.html",
        "The review",
        "Most forecasts show you their conclusions. This page shows you our "
        "mistakes — six errors, one false headline claim, and the repair, "
        "published in full.",
        "model-review.html",
    ),
    "docs-public/sources.md": (
        "sources.html",
        "Data sources",
        "Every number in this model traces back to a public record. Where "
        "each one lives, what state it was in, and how hard South Africa's "
        "public records actually are to reach.",
    ),
    "joburg-prediction-model-plan-v2.md": (
        "plan.html",
        "The original plan (rev 2, annotated)",
        "The build plan the model was constructed against — kept as written, "
        "including the parts implementation later proved wrong, with its "
        "correction boxes.",
    ),
}

# already-styled artefacts copied verbatim under stable public names
# already-styled artefacts, nav-injected; the forecast IS the landing page
ARTEFACTS = {
    "forecast-sheet.html": "index.html",
    "forecast-interactive.html": "interactive.html",
}

CARDS = [
    ("./", "The forecast", "hero",
     "Two pages: seats, coalition arithmetic, and the overhang finding that "
     "moves the majority bar. Start here."),
    ("interactive.html", "The interactive model", "hero",
     "Every assumption as a bounded slider at its default. Drag one and see "
     "which conclusions bend and which refuse."),
    ("methodology", "Methodology", "document",
     "How the council is actually elected, how the simulation runs, and the "
     "honest boundary of what can be validated. Full technical brief on GitHub."),
    ("review.html", "Implementation review", "document",
     "The audit that found six errors in the first build — including a false "
     "headline claim — and the same-day resolution of all of them."),
    ("https://github.com/Psi-am-i/jhb-election-model/blob/main/MODEL-LOG.md",
     "Engineering log", "github",
     "The day-by-day build record — every finding, obstacle, decision and "
     "risk, in full technical detail. Lives on GitHub, for those who want "
     "all of it."),
    ("sources", "Data sources", "document",
     "Every number traces to a public record — where each lives, and how "
     "hard public records actually are to reach. Technical recipes on GitHub."),
    ("plan.html", "The original plan", "document",
     "The rev-2 plan as written — including what the build later proved "
     "wrong. Kept because the divergence is part of the record."),
]


def shell(title: str, kicker: str, masthead: str, body: str, generated_note: str, active_href: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{OG_META}<style>{STYLE}</style>
</head>
<body>
<div class="page">
{nav_for(active_href)}
<header>
  <div class="kicker">{kicker}</div>
{masthead}
</header>
{body}
<div class="colophon">
  {generated_note}
</div>
{FOOTER}
</div>
</body>
</html>
"""


def render_doc(source: Path, kicker: str, standfirst: str, output: str = "",
               tech: str | None = None) -> str:
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip()
    body_md = "\n".join(lines[1:])

    html = markdown.markdown(body_md, extensions=["tables", "fenced_code", "smarty"])
    html = html.replace("<table>", '<div class="tablewrap"><table>')
    html = html.replace("</table>", "</table></div>")

    masthead = (f"  <h1>{title}</h1>\n"
                f'  <p class="standfirst">{standfirst}</p>')
    if str(source).startswith("docs-public/"):
        tech = tech or source.name.replace(".md", "").upper() + ".md"
        note = (f"Reader edition, generated from {source} on "
                f"{date.today().isoformat()}. The full technical record — "
                f"every URL, identifier and workaround — is "
                f'<a href="https://github.com/Psi-am-i/jhb-election-model/blob/main/{tech}">'
                f"{tech} on GitHub</a>.")
    else:
        note = (f"Generated from {source.name} by src/build_site.py on "
                f"{date.today().isoformat()} — the Markdown file in the project "
                f"repository is canonical; regenerate rather than editing this page.")
    return shell(f"Johannesburg 2026 — {title}", kicker, masthead, html, note,
                 active_href=output.removesuffix(".html"))


def build_documents() -> str:
    cards = "\n".join(
        f'  <a class="card{" hero" if tag == "hero" else ""}" href="{href}">'
        f'<span class="tag">{tag}</span>'
        f'<span class="t">{title}</span>'
        f'<span class="d">{desc}</span></a>'
        for href, title, tag, desc in CARDS
    )
    masthead = """  <h1>Who governs Johannesburg after 4&nbsp;November&nbsp;2026?</h1>
  <p class="standfirst">A voting-district model of the City of Johannesburg —
  5,000 simulations over 865 voting districts, both ballots, the statutory seat
  formula, and the coalition arithmetic it permits. The forecast, the machinery,
  and the full warts-and-all record of how it was built, reviewed, broken and
  corrected.</p>
  <div class="dateline">
    <span><b>Election</b> 4 November 2026</span>
    <span><b>Forecast issued</b> 4 August 2026 (rev 2)</span>
    <span><b>Headline</b> overhang moves the majority bar to ~141; one pairing reliably clears it</span>
  </div>"""
    body = f"""<div class="cards">
{cards}
</div>
<p style="color:var(--ink-2);font-size:13.5px">Everything here is
reproducible: the documents are generated from the project's canonical records,
the sheet's figures come straight from the model outputs, and the interactive
page emits a scenario file that reproduces any slider state exactly in the full
model. The review page documents the errors found in the first build — published
deliberately, because a forecast whose mistakes are hidden is not worth
trusting.</p>"""
    note = "Site generated by src/build_site.py on " + date.today().isoformat() + "."
    return shell("Johannesburg 2026 — Council Forecast", "Forecast & model record",
                 masthead, body, note, active_href="documents")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("site"))
    parser.add_argument("--stats", type=Path,
                        default=Path("content/joburg/stats.toml"))
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--strict-drift", action="store_true",
                        help="treat pinned-stat drift as an error, not a warning")
    args = parser.parse_args(argv)

    args.out.mkdir(exist_ok=True)
    registry = statlib.load_registry(args.stats) if args.stats.exists() else {}
    ctx = statlib.load_context(args.processed)
    all_drift: list[dict] = []
    unresolved_all: list[str] = []

    for source, spec in DOCS.items():
        output, kicker, standfirst = spec[:3]
        tech = spec[3] if len(spec) > 3 else None
        page = render_doc(Path(source), kicker, standfirst, output, tech)
        page, drift, unresolved = statlib.render(page, registry, ctx)
        all_drift += drift
        unresolved_all += [f"{source}: {u}" for u in unresolved]
        (args.out / output).write_text(page, encoding="utf-8")
        print(f"  rendered {source:<28s} -> site/{output}")

    for source, output in ARTEFACTS.items():
        href = "./" if output == "index.html" else output.removesuffix(".html")
        html = inject_nav(Path(source).read_text(encoding="utf-8"), href)
        html, drift, unresolved = statlib.render(html, registry, ctx)
        all_drift += drift
        unresolved_all += [f"{source}: {u}" for u in unresolved]
        (args.out / output).write_text(html, encoding="utf-8")
        print(f"  nav+copy {source:<28s} -> site/{output}")
    stale = args.out / "forecast.html"
    if stale.exists():
        stale.unlink()  # superseded: the forecast is index.html now

    # --- stat provenance: unresolved tokens are fatal, drift only warns ---
    if unresolved_all:
        print("\nUNRESOLVED STATS — refusing to publish a silent blank:")
        for item in sorted(set(unresolved_all)):
            print(f"  ✗ {item}")
        raise SystemExit(1)
    n_pinned = sum(1 for e in registry.values() if e.get("mode") == "fixed")
    n_free = len(registry) - n_pinned
    print(f"\nstats: {n_free} free tokens resolved live · {n_pinned} pinned")
    print(statlib.drift_report(all_drift))
    if all_drift and args.strict_drift:
        raise SystemExit(1)

    # Serve everything as UTF-8 regardless of meta tags — the sheet originally
    # shipped without a <head> and mojibake'd every em-dash (review of the
    # deployed site, 2026-08-04). All assets here are HTML, so a blanket
    # header is safe; revisit if non-HTML assets are ever added.
    (args.out / "_headers").write_text(
        "/*\n  Content-Type: text/html; charset=utf-8\n"
        "/share.jpg\n  ! Content-Type\n  Content-Type: image/jpeg\n"
        # working copies: reachable for review, never indexed
        "/dev/*\n  X-Robots-Tag: noindex, nofollow\n"
        "/drafts/*\n  X-Robots-Tag: noindex, nofollow\n",
        encoding="utf-8")
    (args.out / "robots.txt").write_text(
        "# The published pages are meant to be indexed. Working copies are\n"
        "# not: /dev/ is the pre-release build and /drafts/ holds\n"
        "# side-by-side rewrites, both of which duplicate live content.\n"
        "User-agent: *\n"
        "Disallow: /dev/\n"
        "Disallow: /drafts/\n"
        "Allow: /\n", encoding="utf-8")
    print("  wrote    _headers + robots.txt (utf-8; /dev and /drafts noindex)")

    total = sum(f.stat().st_size for f in args.out.glob("*.html"))
    print(f"site: {len(list(args.out.glob('*.html')))} pages, {total / 1024:.0f} KB total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
