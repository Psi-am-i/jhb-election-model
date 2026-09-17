"""Build the public site (joburg.whysoserious.org) into ./site.

Same principle as render_sheet.py: styled artefacts are generated from the
canonical sources, never hand-copied, so they cannot go stale.

Two kinds of page:

* **Rendered documents** — the four Markdown records (methodology, model log,
  sources, the original plan) converted to house-styled HTML. The Markdown
  stays canonical; regenerate rather than editing the HTML.
* **Copied artefacts** — forecast-sheet.html and
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
import json

import cityconfig
import re
import shutil
from datetime import date
from pathlib import Path

import markdown

import publication
import stats as statlib

# The repository root, resolved from THIS FILE rather than the process's working
# directory. `publication.LEDGER_ROOT` is a relative path by design (see the
# LEVEL_DF class of defect, §1.33: a `Path` frozen as a default argument), and a
# relative ledger path read from the wrong CWD is worse than a missing one — it
# resolves to an empty ledger, which reads as "nothing was ever published".
REPO_ROOT = Path(__file__).resolve().parents[1]

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
    # "interactive" removed with the page itself — see ARTEFACTS. The comment
    # below records what happened the LAST time a nav entry outlived its page:
    # every page linked to plan.html for weeks after no build produced it.
    ("about", "about the model"),
    ("methodology", "methodology"),
    ("review", "review"),
    ("sources", "sources"),
    # "plan" was removed from DOCS when the plan became Appendix A of
    # MODEL-LOG.md, but the nav link stayed. Every page on the site therefore
    # linked to site/plan.html — a file no build touches any more, describing
    # the two-bloc engine that was deleted in 87806a7. A dead link to a live
    # page is one thing; a live link to a dead model is another.
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
    "docs-public/about-the-model.md": (
        "about.html",
        "About the model",
        "A forecast that has never been scored is an opinion. This is the "
        "scoring: run against an election that already happened, in eight "
        "cities, against what occurred and against three deliberately stupid "
        "alternatives.",
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
    # The plan is no longer published as a page of its own: it is Appendix A
    # of MODEL-LOG.md, where it belongs. It is the model's starting point and
    # every numbered finding in that log is a delta from it, so the two only
    # make sense read together. As a standalone page it also carried 55 model
    # figures with no provenance — historical assertions the sourcing audit
    # cannot tell from live claims, and which nobody was maintaining.
}

# already-styled artefacts copied verbatim under stable public names
# already-styled artefacts, nav-injected; the forecast IS the landing page
# THE INTERACTIVE IS WITHHELD until it works. Its sliders write to
# montecarlo.DEFAULTS' schema, and this session has changed that schema
# substantially: the pool draw now balances both margins by IPF, the level
# shock moved to the centres, polls blend by inverse variance, and several
# keys the sliders bind to no longer mean what they meant. A slider that
# silently sets a key the engine no longer reads is worse than no slider, so
# the page is not published until it has been rebuilt against the current
# schema. `interactive.html` is therefore absent from the site rather than
# broken on it, and the nav entry goes with it.
ARTEFACTS = {
    "forecast-sheet.html": "index.html",
}



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
    # Skip any leading HTML comment and blank lines before taking the title.
    # A generated page opens with a "do not edit by hand" marker, and without
    # this the marker BECAME the <title> — "Johannesburg 2026 — <!-- GENERATED
    # by src/build_validation.py..." went out in the tab and the share card.
    start = 0
    while start < len(lines) and (
            not lines[start].strip() or lines[start].lstrip().startswith("<!--")):
        if lines[start].lstrip().startswith("<!--"):
            while start < len(lines) and "-->" not in lines[start]:
                start += 1
        start += 1
    if start >= len(lines):
        raise SystemExit(f"{source}: no title line found")
    title = lines[start].lstrip("# ").strip()
    body_md = "\n".join(lines[start + 1:])

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




def _ledger_candidates(published: list[dict], ledger: dict, ident: dict,
                       now: str, *, reason: str | None,
                       change_class: str | None):
    """The rows this build WOULD publish, and the reader-facing diff of them.

    ⛔ ONE FUNCTION BUILDS BOTH, DELIBERATELY. The printed report, the
    `changes.json` the page renders from, and the rows `--publish` appends must
    describe the same thing or the site tells the reader one story while the
    permanent record keeps another. Two code paths over the same data is how
    that gap opens, and this repository's standing rule is one definition only.

    A token can appear on several pages. It is ONE published figure — the
    registry resolves it once per build — so it becomes one row, and the pages
    it reached are recorded on the diff rather than duplicated into the ledger.
    If two occurrences of one token ever disagree, that is a renderer bug and
    it is raised rather than silently reconciled.

    `movement` is computed against the LAST PUBLISHED row, not against the
    previous build: an unpublished experimental build must not consume a
    token's change, or the move it made would never be disclosed to anyone.
    """
    by_token: dict[str, dict] = {}
    pages: dict[str, list[str]] = {}
    for occ in published:
        name = occ["token"]
        pages.setdefault(name, [])
        if occ.get("page") and occ["page"] not in pages[name]:
            pages[name].append(occ["page"])
        first = by_token.setdefault(name, occ)
        if first["display"] != occ["display"]:
            raise SystemExit(
                f"token {name!r} rendered as {first['display']!r} on "
                f"{first.get('page')} and {occ['display']!r} on "
                f"{occ.get('page')}. One token is one published figure; two "
                f"values means the registry resolved twice and the ledger "
                f"cannot say which one the reader was shown.")

    rows: list[publication.Row] = []
    changes: list[dict] = []
    for name in sorted(by_token):
        occ = by_token[name]
        prev = ledger.get(name)
        try:
            movement = publication.classify(prev, occ["value"], occ["display"],
                                            tolerance=occ.get("tolerance"),
                                            fmt=occ.get("fmt"))
        except ValueError as exc:
            # A tolerance written in the wrong units. Loud rather than silent
            # was already the design (`publication.classify`); a refusal rather
            # than a traceback is what makes it actionable, and it belongs in
            # the same family as every other build refusal.
            raise SystemExit(
                f"refusing to publish: {exc}\n"
                f"Fix the tolerance in the stats registry. Nothing was "
                f"written to the ledger.") from None
        rows.append(publication.Row(
            token=name, value=occ["value"], display=occ["display"],
            fmt=occ.get("fmt"), source=occ.get("source", ""),
            model_run_id=ident["model_run_id"], run_at=ident["run_at"],
            as_of=ident["as_of"], published_at=now,
            # A row that did not move owes no explanation; one that did owes
            # both, and `--publish` refuses the batch if they are missing.
            change_class=(change_class if movement != "none" else None),
            reason=(reason if movement != "none" else None),
            movement=movement,
            provenance={k: ident.get(k) for k in
                        ("git_commit", "git_dirty", "pool_artefact_keys",
                         "forecast_content_sha256", "draws", "as_of_is")}))
        changes.append({
            "token": name, "movement": movement,
            "value": occ["value"], "display": occ["display"],
            "previous": None if prev is None else prev.display,
            "previous_published_at": None if prev is None else prev.published_at,
            "fmt": occ.get("fmt"), "source": occ.get("source", ""),
            "mode": occ.get("mode"), "pages": pages[name],
        })
    return rows, changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("site"))
    parser.add_argument("--strict", action="store_true",
                        help="fail the build on unsourced model figures or "
                             "claims, not just on unresolved tokens")
    parser.add_argument("--stats", type=Path,
                        default=Path("content/joburg/stats.toml"))
    parser.add_argument("--processed", type=Path, default=None,
                        help="where inputs are read (default: the target's own processed "
                             "directory). A literal data/processed is "
                             "JOHANNESBURG's, whatever --city says")
    parser.add_argument("--strict-drift", action="store_true",
                        help="treat pinned-stat drift as an error, not a warning")
    parser.add_argument("--allow-orphans", action="store_true",
                        help="publish even when a pinned claim is tied to a "
                             "scenario key the model no longer has. Staging "
                             "escape hatch only — the claim is a number on the "
                             "page that cannot be re-derived or drift-checked, "
                             "so say why in the commit if you use it.")
    parser.add_argument("--ledger-root", type=Path, default=None,
                        help="where the publication ledger lives (default: "
                             "publications/ under the repository root). Exists "
                             "so the end-to-end build can be exercised against "
                             "a throwaway ledger — the real one is append-only "
                             "and a test must never be able to write to it.")
    parser.add_argument("--publish", action="store_true",
                        help="APPEND this build's figures to the publication "
                             "ledger. Without it the build reports what moved "
                             "and appends NO LEDGER ROW (site/changes.json is "
                             "still written) — the ledger is append-only, "
                             "so a row written by an experimental build is "
                             "permanent.")
    parser.add_argument("--reason",
                        help="why the figures moved, in the reader's language. "
                             "Required by --publish whenever anything moved.")
    parser.add_argument("--change-class", choices=publication.CHANGE_CLASSES,
                        help="what KIND of change this is: recompute, "
                             "data_revision, mechanism or bugfix. 'the model "
                             "moved' and 'we were wrong' are different "
                             "sentences and the reader is owed which.")
    parser.add_argument("--allow-stale-sources", action="store_true",
                        help="publish even when a token's source FILE is older "
                             "than the reference run. Staging escape hatch "
                             "only — the number is live-looking prose fed by a "
                             "dead model, and nothing downstream can tell.")
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    cityconfig.use(getattr(args, "city", None))
    args.processed = args.processed or cityconfig.use_target(
        getattr(args, "target", None)).processed

    args.out.mkdir(exist_ok=True)
    registry = statlib.load_registry(args.stats) if args.stats.exists() else {}
    ctx = statlib.load_context(args.processed)
    audit_cfg = statlib.load_audit_config(registry)
    all_drift: list[dict] = []
    unresolved_all: list[str] = []
    audits: dict[str, tuple[list[str], list[str]]] = {}
    # Every number-shaped string on every page, for the committed review file.
    scans: dict[str, list[dict]] = {}
    scan_cfg = {"fixed": audit_cfg["fixed"], "allow": audit_cfg["allow"]}
    generated: list[str] = []
    # Every token OCCURRENCE that reached a reader, in reading order. The
    # ledger needs the raw value AND the displayed string; see `stats.render`.
    published: list[dict] = []

    for source, spec in DOCS.items():
        output, kicker, standfirst = spec[:3]
        tech = spec[3] if len(spec) > 3 else None
        page = render_doc(Path(source), kicker, standfirst, output, tech)
        seen: list[dict] = []
        page, drift, unresolved = statlib.render(page, registry, ctx,
                                                 record=seen)
        published += [{**r, "page": output} for r in seen]
        all_drift += drift
        unresolved_all += [f"{source}: {u}" for u in unresolved]
        # A GENERATED page is exempt from the typed-figure audit, and only a
        # generated page is. The audit exists to catch numbers a PERSON typed
        # and then failed to update — the four that went stale on the live
        # site. A page written by a script from a recorded run cannot go stale
        # in that way: re-running the script is the only way to change it, and
        # the run's seed, draw count and date are printed at its foot. Marking
        # it as a token per figure would be weaker, not stronger — 25 pinned
        # values a human maintains against one command that regenerates all of
        # them. The marker is in the source, so this cannot be claimed for a
        # hand-written page by accident.
        if Path(source).read_text(encoding="utf-8").lstrip().startswith(
                "<!-- GENERATED by "):
            generated.append(output)
            scans[output] = statlib.scan_numbers(page, generated_page=True, **scan_cfg)
        else:
            audits[output] = statlib.audit(page, **audit_cfg)
            scans[output] = statlib.scan_numbers(page, **scan_cfg)
        (args.out / output).write_text(page, encoding="utf-8")
        print(f"  rendered {source:<28s} -> site/{output}")

    for source, output in ARTEFACTS.items():
        href = "./" if output == "index.html" else output.removesuffix(".html")
        html = inject_nav(Path(source).read_text(encoding="utf-8"), href)
        seen = []
        html, drift, unresolved = statlib.render(html, registry, ctx,
                                                 record=seen)
        published += [{**r, "page": output} for r in seen]
        all_drift += drift
        unresolved_all += [f"{source}: {u}" for u in unresolved]
        audits[output] = statlib.audit(html, **audit_cfg)
        scans[output] = statlib.scan_numbers(html, **scan_cfg)
        (args.out / output).write_text(html, encoding="utf-8")
        print(f"  nav+copy {source:<28s} -> site/{output}")
    # EVERY PAGE THIS BUILD NO LONGER PRODUCES IS REMOVED, not just the one
    # somebody remembered. A single hard-coded `forecast.html` unlink stood here
    # for months while `plan.html` and, the moment the interactive was withheld,
    # `interactive.html` both stayed on the site — served, linked from nothing,
    # and describing a model that had moved on. A page nobody rebuilds is worse
    # than a missing one: it looks current and cannot be.
    produced = {"index.html"} | {spec[0] for spec in DOCS.values()} \
        | set(ARTEFACTS.values()) | {"portal.html"}
    for page in sorted(args.out.glob("*.html")):
        if page.name not in produced:
            page.unlink()
            print(f"  removed  site/{page.name} (no longer produced by this build)")

    # --- stat provenance: unresolved tokens are fatal, drift only warns ---
    if unresolved_all:
        print("\nUNRESOLVED STATS — refusing to publish a silent blank:")
        for item in sorted(set(unresolved_all)):
            print(f"  ✗ {item}")
        raise SystemExit(1)

    # ORPHANED PINNED CLAIMS ARE FATAL TOO, since 2026-08-17. They were detected
    # and PRINTED, which is a comment rather than an audit: ten front-page claims
    # sat pinned to `turnout_tilt_da` — a lever `run_model` no longer has — for
    # weeks, through two independent reviews that both named them, because
    # nothing stopped the build. An unresolved token is fatal because it would
    # publish a blank; an orphan is worse, because it publishes a NUMBER that
    # reads as current and cannot be re-derived or drift-checked. Nothing in the
    # pipeline could ever tell the reader it was stale.
    #
    # `--allow-orphans` exists so the fix can be staged: re-derive the claims
    # under a mechanism that exists, or cut them. It should not survive that.
    #
    # BOTH PROVENANCE REFUSALS ARE REPORTED BEFORE EITHER EXITS. They are
    # independent faults with independent remedies — one is re-capturing a
    # pinned claim, the other is re-running `overhang_regimes.py` — and exiting
    # on the first would hand the builder one of them per build.
    orphans = statlib.orphaned_scenario_claims(registry)
    refuse = False
    if orphans and not args.allow_orphans:
        refuse = True
        print("\nORPHANED PINNED CLAIMS — refusing to publish a number whose "
              "mechanism the model no longer has:")
        for name, key in orphans:
            print(f"  ✗ {name}  (pinned to scenario key {key!r})")
        print("  Re-capture each under a mechanism that exists, or cut the "
              "claim. Pass --allow-orphans to publish anyway and say why.")
    # A STALE BACKING FILE IS FATAL, since 2026-08-24, and for the same reason
    # the orphan check above is. `mode = "free"` is not a freshness guarantee:
    # a free token is recomputed every build from a FILE, and if that file is
    # old the token republishes an old model's number while reading — to the
    # reader, to a reviewer, and to the drift report — as the model speaking
    # now. `anc_entitlement` sat twice on the live front page resolving out of
    # `regime_cap_summary.json`, dated 2026-08-07, whose scenario block still
    # names `turnout_tilt_da` and twelve other levers `run_model` has not had
    # for weeks. The drift audit reported no drift, correctly: a frozen file
    # cannot drift.
    #
    # WARN OR REFUSE? Refuse. This repository has already run that experiment:
    # `orphaned_scenario_claims` PRINTED its finding, and ten front-page claims
    # survived two independent reviews that both named them, because a print is
    # a comment and not an audit. This defect is the same class wearing a
    # better disguise — the orphans at least declared themselves `fixed`.
    # `--allow-stale-sources` exists so the fix can be staged, exactly as
    # `--allow-orphans` does, and should not outlive it.
    stale = statlib.freshness_problems(registry, ctx)
    if stale and not args.allow_stale_sources:
        refuse = True
        print("\nSTALE SOURCE FILES — refusing to publish a live-looking "
              "number resolved out of a dead model's output:")
        print(statlib.freshness_report(stale))
        print("  Re-run the command above, or pass --allow-stale-sources and "
              "say why.")
    elif stale:
        print("\n!! publishing against STALE source files (--allow-stale-sources):")
        print(statlib.freshness_report(stale))
    # A SUPERSEDED FIGURE IN LIVE PRESENT TENSE IS FATAL, since 2026-08-31,
    # and it is the second clause of the attribution rule this whole ledger
    # exists to keep. The owner's standard is that a published number need not
    # be re-derivable — it must be ATTRIBUTABLE, and a figure whose mechanism
    # the model no longer has may still be published *as history*: "as of 7
    # August the model said the DA would be short by 39 seats". What it may not
    # do is speak in the present. Without this check the rule is a licence.
    #
    # The prose DECLARES its own dating by enclosing the sentence in an element
    # carrying `data-asof`; see `stats.DATED_REGION` for why it is declared per
    # occurrence rather than sniffed for a nearby date.
    city = cityconfig.active().slug
    # ROOT IS ANCHORED TO THE REPOSITORY, NOT THE WORKING DIRECTORY. `latest`
    # defaults to a relative `publications/`, so a build run from anywhere but
    # the repo root would read an EMPTY ledger, classify every token as `new`,
    # and let `dated_context_violations` return [] — the refusal failing OPEN
    # and silently, which is the exact failure the declared-dating design was
    # chosen to avoid.
    ledger_root = args.ledger_root or (REPO_ROOT / publication.LEDGER_ROOT)
    ledger = publication.latest(city, root=ledger_root)
    undated = publication.dated_context_violations(published, ledger)
    if undated:
        refuse = True
        print("\nSUPERSEDED FIGURES IN LIVE PRESENT TENSE — refusing to "
              "publish a retired number as though it were current:")
        for v in undated:
            print(f"  ✗ {v['token']} = {v['display']}")
            print(f"      {v['why']}")
        print("  Wrap the sentence in <span data-asof=\"YYYY-MM-DD\">…</span> "
              "so it reads as history, or cut the claim.")

    # A PUBLISHED TOKEN THAT LEAVES THE REGISTRY UNRETIRED IS FATAL, since
    # 2026-08-31 — and this is the DURABLE half of the pre-ledger backfill.
    #
    # Backfilling the ten `turnout_tilt_da` claims and retiring them is a
    # cleanup: it fixes ten rows. This is the fix. The seam was never really
    # "the ledger started empty"; it was that a figure can stop being produced
    # and simply VANISH — deleted from the registry, gone from the page, and
    # nothing anywhere saying it stopped being current or when. `retire()` is
    # the only thing that sets `superseded_at`, and `dated_context_violations`
    # — the second clause of the attribution rule — is built entirely on that
    # stamp. So a token that disappears without a retirement takes the check
    # with it: there is no row left to fire on.
    #
    # The next deleted lever reopens the hole otherwise, and it will be deleted
    # for a good reason, by someone with no idea a claim on the front page was
    # pinned to it. That is exactly how `turnout_tilt_da` happened.
    #
    # NO ESCAPE HATCH, unlike --allow-orphans and --allow-stale-sources. Those
    # stage a fix that needs model work; this one is satisfied by one call to
    # `publication.retire()` with a reason, which is the whole obligation.
    vanished = sorted(t for t, row in ledger.items()
                      if t not in registry and not row.superseded_at)
    if vanished:
        refuse = True
        print("\nPUBLISHED TOKENS THAT LEFT THE REGISTRY UNRETIRED — refusing "
              "to let a figure stop being current without saying so:")
        for name in vanished:
            row = ledger[name]
            print(f"  ✗ {name} = {row.display}  (last published "
                  f"{row.published_at}, run {row.model_run_id})")
        print("  Each was published, is no longer in the stats registry, and "
              "carries no supersession stamp — so nothing can tell a reader "
              "when it stopped being true. Close each one out:")
        print(f"    P.retire({city!r}, '<token>', reason='<why>', "
              f"change_class='mechanism', root=Path({str(ledger_root)!r}))")

    # ⛔ A DECLARED HISTORICAL CLAIM MUST APPEAR IN DATED PROSE. FATAL.
    #
    # `historical` exempts a token from the orphan refusal because its
    # mechanism is gone and it can never be re-derived — the owner's ruling
    # allows that, as HISTORY. This is the other half of the bargain, and
    # without it the declaration is just `--allow-orphans` spelled differently:
    # a figure the model cannot produce, sitting in the present tense, with a
    # line in a config file quietly excusing it.
    #
    # `dated` comes from the prose itself (`stats.DATED_REGION`), per
    # occurrence, never inferred — see that regex for why a guess here fails
    # OPEN on exactly the prose it cannot parse.
    bad_asof = sorted({m for o in published
                       for m in (o.get("malformed_asof") or [])})
    if bad_asof:
        refuse = True
        print("\nMALFORMED `data-asof` REGION — refusing to publish against a "
              "dating declaration that cannot be trusted:")
        for m in bad_asof:
            print(f"  ✗ {m}")
        print("  A region that does not parse dates NOTHING, so every "
              "historical claim inside it would publish in the present tense.")

    published = [o for o in published if o.get("token")]

    # ⛔ THE DATE MUST BE THE RIGHT DATE, NOT MERELY A WELL-FORMED ONE.
    #
    # Parsing `data-asof` closed "banana"; it did not close `2099-12-31`, nor a
    # date BEFORE the figure was captured. Either lets a page say a figure was
    # true at a time it was not, which is the whole obligation the declaration
    # buys. Found in review 2026-08-31, after the parser fix.
    today = date.today().isoformat()
    wrong_date = []
    for o in published:
        a, cap = o.get("asof", ""), o.get("captured", "")
        if not o.get("historical") or not a:
            continue
        if a > today:
            wrong_date.append((o["token"], a, "is in the future"))
        elif cap and a < cap:
            wrong_date.append((o["token"], a,
                               f"precedes the figure's own capture date {cap}"))
    if wrong_date:
        refuse = True
        print("\nA HISTORICAL FIGURE IS DATED TO A TIME IT WAS NOT TRUE — "
              "refusing:")
        for tok, a, why in sorted(set(wrong_date)):
            print(f"  ✗ {tok}  dated {a}, which {why}")
    undated_history = [o for o in published
                       if o.get("historical") and not o.get("dated")]
    if undated_history:
        refuse = True
        seen = sorted({o["token"] for o in undated_history})
        print("\nHISTORICAL CLAIMS IN LIVE PRESENT TENSE — refusing to publish "
              "a figure the model can no longer produce as though it were "
              "current:")
        for tok in seen:
            occ = [o for o in undated_history if o["token"] == tok]
            print(f"  ✗ {tok}  ({len(occ)} occurrence(s) on "
                  f"{', '.join(sorted({o.get('page', '?') for o in occ}))})")
        print('  Enclose the passage in <span data-asof="YYYY-MM-DD">…</span> '
              "so it reads as history, or cut the claim. A token declared "
              "`historical` is one nothing can re-derive; the date is what "
              "tells the reader when it was true.")

    if refuse:
        raise SystemExit(1)

    n_pinned = sum(1 for e in registry.values() if e.get("mode") == "fixed")
    # `registry` carries the [audit] block alongside the tokens, so
    # `len(registry) - n_pinned` counted it as a free token and printed 16
    # where there are 15. Caught in review 2026-08-31 — and it had already
    # travelled into a review write-up unverified, which is what a wrong count
    # in a build log does.
    n_free = sum(1 for e in registry.values()
                 if isinstance(e, dict) and e.get("mode") != "fixed"
                 and e.get("source"))
    print(f"\nstats: {n_free} free tokens resolved live · {n_pinned} pinned")
    print(statlib.drift_report(all_drift, registry))
    if all_drift and args.strict_drift:
        raise SystemExit(1)

    if generated:
        print(f"\ngenerated pages, exempt from the typed-figure audit because "
              f"every number in them comes from a recorded run: "
              f"{', '.join(sorted(generated))}")

    # --- the audit: what reached the reader without provenance -------------
    # A token carries its source to the reader and drift-checks itself. A
    # figure typed into prose does neither, which is how four went stale and
    # the standfirst claimed 54% while the model said 62%. Strings are audited
    # for the same reason: "the DA is the largest party" is a model result in
    # words and goes stale exactly as quietly.
    total_n = sum(len(n) for n, _ in audits.values())
    total_c = sum(len(c) for _, c in audits.values())
    print(f"\nsourcing audit: {total_n} unsourced figure(s), "
          f"{total_c} unsourced claim(s) across {len(audits)} page(s)")
    for page in sorted(audits):
        numbers, claims = audits[page]
        if numbers or claims:
            print(f"  --- {page}")
            print(statlib.audit_report(numbers, claims, limit=6))
    # THE NUMBER REVIEW FILE — committed, regenerated every build, so a git diff
    # shows every number that appeared, changed or vanished on the site. Owner,
    # 2026-09-17: "even when we type in by hand, we should be able to scrape
    # things that look like numbers and flag them for tracking and manual
    # review." Blocking kinds (statlib.GATING) in prose stop a --publish.
    # Only the real build writes the committed file. A build into a temporary
    # --out (every test does this) writes its review beside that output, so a
    # test can never rewrite what the owner reviews.
    real_out = args.out.resolve() == (REPO_ROOT / "site").resolve()
    review_path = (REPO_ROOT / "content" / city / "NUMBERS-REVIEW.md" if real_out
                   else args.out.parent / "NUMBERS-REVIEW.md")
    lines = ["# Numbers on the site — generated by build_site.py, do not edit",
             "",
             "Every number-shaped string a reader can see that is not a token. "
             "Clear a row by making it a `{{token}}` or registering it under "
             "`[[audit.fixed]]` in `content/<city>/stats.toml` (value, context, "
             "kind, source, reviewed). `BLOCKS` rows stop `--publish`.", ""]
    blocking = 0
    for page in sorted(scans):
        hits = scans[page]
        counts: dict[str, int] = {}
        for h in hits:
            counts[h["status"]] = counts.get(h["status"], 0) + 1
        lines += [f"## {page} — " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items())), "",
                  "| | kind | region | value | context |", "|---|---|---|---|---|"]
        for h in hits:
            if h["status"] != "unreviewed":
                continue
            gate = h["region"] == "prose" and h["kind"] in statlib.GATING
            blocking += gate
            ctx = h["context"].replace("|", "\\|")
            lines.append(f"| {'BLOCKS' if gate else 'review'} | {h['kind']} | "
                         f"{h['region']} | `{h['value']}` | …{ctx}… |")
        lines.append("")
    import hashlib as _hashlib
    shas = {page: _hashlib.sha256((args.out / page).read_bytes()).hexdigest()
            for page in sorted(scans) if (args.out / page).is_file()}
    lines.insert(1, "<!-- built-pages: " + " ".join(f"{k}={v}" for k, v in shas.items())
                 + f" blocking={blocking} -->")
    review_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"number review: {blocking} blocking, "
          f"{sum(len(v) for v in scans.values())} scanned -> {review_path}")

    if (total_n or total_c) and args.strict:
        raise SystemExit(
            "refusing to publish: model figures or claims reach the reader "
            "with no source. Register each as a {{token}}, or add its context "
            "to [audit].allow in the stats registry if it is historical fact, "
            "a statement of the rules, or reviewed static prose.")

    # --- the publication ledger: what moved, and on whose authority --------
    # ⛔ CHANGING THE FORECAST IS EXPECTED. LEAVING THE READER TO NOTICE IS NOT.
    #
    # The owner's ruling, 2026-08-30: a forecast value is live at one point and
    # is bound to be superseded, the old value going into that token's history.
    # We do not have to be able to RE-DERIVE it. We have to be able to say what
    # it was, when that was, and which model produced it.
    #
    # So this section is not a gate on the forecast moving — it is a gate on
    # the move being SILENT. Every occurrence that reached a reader is
    # classified against the last published row and reported; publishing them
    # requires a reason of a stated kind.
    #
    # --publish is opt-in because the ledger is append-only: a row written by
    # an experimental build can never be taken back, and this script is run
    # many times a day during a rewrite.
    ident = publication.run_identity(args.processed)
    now = publication.utc_now()
    rows, changes = _ledger_candidates(published, ledger, ident, now,
                                       reason=args.reason,
                                       change_class=args.change_class)
    summary = publication.summarise(rows)
    # ⛔ `new` IS NOT A MOVE, and treating it as one writes a lie into a record
    # that cannot be rewritten. `classify` returns "new" for a first
    # publication; if that counts as moved, the FIRST EVER --publish demands a
    # --change-class, and every founding row is then stamped `recompute` /
    # `mechanism` / `bugfix` — none of which describes a figure that was never
    # published before. Found in blind review 2026-08-31; the print two lines
    # below already counted new separately and this did not.
    moved = [c for c in changes if c["movement"] not in ("none", "new")]

    # NEW IS COUNTED SEPARATELY FROM CHANGED, because they are different
    # sentences to a reader and `summarise` is right to keep them apart: a
    # first publication did not MOVE. Reporting them together printed "0
    # visibly changed" directly above a list of twelve tokens.
    n_new = len(summary["by_movement"].get("new", []))
    print(f"\npublication ledger ({city}): {summary['n']} token(s) on the "
          f"page · {n_new} published for the first time · "
          f"{summary['n_visible']} visibly changed · "
          f"{summary['n_rounding']} moved below the displayed precision")
    visible = [c for c in changes
               if c["movement"] in ("new", "nominal", "material", "minor")]
    for c in sorted(visible, key=lambda c: c["token"])[:12]:
        was = "—" if c["previous"] is None else c["previous"]
        print(f"  {c['movement']:<9s} {c['token']:<28s} {was} -> {c['display']}")
    if len(visible) > 12:
        print(f"  … and {len(visible) - 12} more")

    # The reader-facing record. Written on EVERY build, published or not, so
    # the page layer renders "what changed" from the same classification the
    # ledger stores — not a second copy of the logic that can drift away from
    # it. These are the exact rows `--publish` would append.
    (args.out / "changes.json").write_text(
        json.dumps({"city": city, "run": ident, "summary": summary,
                    "changes": changes}, indent=2, sort_keys=True, default=str),
        encoding="utf-8")
    print("  wrote    site/changes.json (the reader-facing 'what changed')")

    if args.publish:
        if moved and not (args.reason and args.change_class):
            raise SystemExit(
                f"refusing to publish: {len(moved)} token(s) moved and the "
                f"change is undeclared. Pass --reason and --change-class.\n"
                f"A forecast is EXPECTED to move. What a reader may not be "
                f"asked to do is notice on their own.")
        # After the declaration check, so a test of that refusal still reaches
        # it; before the append, so nothing is written past an unreviewed number.
        if blocking:
            raise SystemExit(
                f"refusing to publish: {blocking} number(s) typed into prose are "
                f"neither tokens nor registered fixed facts. Each is listed as "
                f"BLOCKS in {review_path}.")
        try:
            n = publication.append(city, rows, root=ledger_root)
        except publication.Unattributable as exc:
            # A refusal, not a crash. The ledger is append-only, so this is the
            # last moment the defect is fixable, and the builder needs to be
            # told what to DO — not handed a traceback.
            raise SystemExit(
                f"refusing to publish: {exc}\n"
                f"Nothing was written. Re-run the model "
                f"(`.venv/bin/python src/montecarlo.py --city {city}`) so the "
                f"forecast carries the run stamp this row must be attributed "
                f"to, then build again.") from None
        print(f"  appended {n} row(s) to {ledger_root}/{city}/ledger.jsonl "
              f"as run {ident['model_run_id']}")
    else:
        print("  (dry run — pass --publish to append these to the ledger)")

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
