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

#: The source code's home, linked from the nav and the footer.
REPO_URL = "https://github.com/Psi-am-i/jhb-election-model"

import build_play  # noqa: E402  (the interactive page's address, below)

#: The nav, in the owner's order (sweep of 2026-10-03, item 9):
#: joburg.whysoserious.city | our forecast | your forecast | commentary |
#: party claims tested | methodology | review | corrections | sources |
#: source code. No "home" item: the site name at the left of the bar IS the
#: link home (owner, 2026-09-24).
#:
#: ⛔ EVERY HREF IS A PAGE THIS BUILD PRODUCES (or the repository).
#: `tests/test_site_structure.py` checks it both ways. The last time a nav
#: entry outlived its page, every page linked to plan.html for weeks after no
#: build produced it, describing an engine deleted in 87806a7.
#:
#: "your forecast" is the interactive page's own address, read from
#: build_play rather than typed here, so the nav follows the page wherever it
#: moves (and the page's active state, `nav_for(build_play.PLAY_HREF)`,
#: matches it).
NAV_ITEMS = [
    ("forecast", "our forecast"),
    (build_play.PLAY_HREF, "your forecast"),
    ("commentary", "commentary"),
    ("claims", "party claims tested"),
    # /about merged into /methodology (owner's sweep, 2026-10-03); the Worker
    # sends /about there.
    ("methodology", "methodology"),
    ("review", "review"),
    # Corrections has its own place in the nav (owner, 2026-09-17): a page that
    # only exists when someone goes looking for it is not a correction record.
    ("corrections", "corrections"),
    ("sources", "sources"),
    (REPO_URL, "source code"),
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
            f"{links}\n"
            # js/theme.js wires the toggle; the page carries no handler
            '  <button class="themetoggle" type="button" '
            'aria-label="Switch between dark and light" title="Light or dark">'
            # the sun shows while dark (click for light), the moon while light
            '<span class="to-light"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg></span>'
            '<span class="to-dark"><svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round" aria-hidden="true"><path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z"/></svg></span>'
            '</button>\n</nav>')


# CLOUDFLARE WEB ANALYTICS — the site's only analytics (owner, 2026-09-30:
# cookieless, no consent banner, no Google tag). What readers are told about it
# is docs-public/privacy.md; change the two together.
#
# ⛔ THE TOKEN GATES THE BEACON AND ITS PARAGRAPH, NOT THE PAGES. /privacy and
# /support are always published, with the footer links to them. While
# the token is empty the build emits no beacon, and `render_doc` keeps
# privacy.md's `<!-- no-analytics -->` block and drops its `<!-- analytics -->`
# block (`analytics_blocks`); with a token it does the reverse. A privacy page
# describing a beacon the site does not carry is false.
#
# SETUP (manual snippet, the only mode this site uses). In the Cloudflare
# dashboard:
#   1. Web Analytics → Add a site → hostname `joburg.whysoserious.city` → Done.
#   2. Manage site → if it offers automatic setup, choose "Enable with JS
#      Snippet installation" (or Disable automatic injection). Cloudflare's FAQ:
#      one beacon per page, or visits are counted twice.
#   3. Manage site → copy the JS snippet; the token is the 32-hex value in
#      `data-cf-beacon='{"token": "…"}'`. Paste only that value below.
#   4. Rebuild, then check a served page carries `cloudflareinsights` once.
# On 2026-10-01 the live site carried no injected beacon.
#
# Web Analytics does not log query strings (its FAQ), so UTM tags are invisible
# to it. Channels are counted by short paths in src/worker.js instead
# (/go, /x, /li, /fb, /ig, /g), which privacy.md describes.
#
# The token is PUBLIC — it is printed into every page's source by design — so
# it is a constant here, not a Keychain secret (~/CLAUDE.md rule 4 does not
# apply to it). It goes out in SITE_HEAD because that is the one head fragment
# every page carries: the rendered documents, the nav-injected artefacts, the
# portal (`build_portal`), /play/ and /make/ (their `assemble`).
CF_WEB_ANALYTICS_TOKEN = "c14bef699fb74863b4db775ea910b533"   # public site token (Web Analytics site whysoserious.city, auto-injection off 2026-10-01)


def analytics_head(token: str | None = None) -> str:
    """The Web Analytics beacon, or nothing when no token is set."""
    token = (CF_WEB_ANALYTICS_TOKEN if token is None else token).strip()
    if not token:
        return ""
    if not re.fullmatch(r"[0-9a-f]{32}", token):
        raise SystemExit(f"CF_WEB_ANALYTICS_TOKEN {token!r} is not a Cloudflare "
                         "Web Analytics site token (32 lowercase hex characters)")
    # `stats.script_writes` refuses every remote script except this exact URL.
    return (f'<script defer src="{statlib.ANALYTICS_BEACON}" '
            f"data-cf-beacon='{{\"token\": \"{token}\"}}'></script>\n")


import site_assets  # noqa: E402

#: The head every page carries: the site's one stylesheet, the theme script
#: (before first paint), the provenance pop-over and the Web Analytics beacon.
#: THE PALETTE, THE NAV, THE FOOTER AND THE TOKEN STYLING ARE NOT HERE: they
#: are src/css/, built into site/css/site.css by `site_assets` (owner's sweep,
#: 2026-10-03: no inline CSS or JS on any page).
SITE_HEAD = site_assets.head() + analytics_head()


#: The site-wide share card's title and description: the home page's card,
#: and /forecast's with its own address (ARTEFACTS).
OG_TITLE = "Who governs Johannesburg after 4 November 2026?"
OG_DESCRIPTION = ("The November vote, simulated: who could govern "
                  "Johannesburg, how the seat law shapes the council, and how "
                  "sure the model is.")

OG_META = f"""<meta property="og:site_name" content="Johannesburg 2026 Election Model">
<meta property="og:type" content="website">
<meta property="og:title" content="{OG_TITLE}">
<meta property="og:description" content="{OG_DESCRIPTION}">
<meta property="og:url" content="https://joburg.whysoserious.city/">
<link rel="canonical" href="https://joburg.whysoserious.city/">
<meta property="og:image" content="https://joburg.whysoserious.city/share.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="The Hillbrow Tower silhouetted against a Johannesburg sunset">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://joburg.whysoserious.city/share.jpg">
"""

SITE_URL = "https://joburg.whysoserious.city"


#: Where the raw results the model starts from can be downloaded.
IEC_RESULTS_URL = "https://results.elections.org.za/"


#: Where Stats SA publishes the ward-level population estimates the model reads
#: (SOURCES.md, "Covariates"), and where the Municipal Demarcation Board
#: publishes the ward and voting-district boundaries (SOURCES.md, "Boundaries").
STATSSA_URL = "https://www.statssa.gov.za/"
MDB_URL = "https://spatialhub-mdb-sa.opendata.arcgis.com/"


def footer_for() -> str:
    """The site footer: the owner's two blocks (sweep of 2026-10-03, item 14),
    his wording, with a rule between them.

    The sources sentence names what the model reads, per SOURCES.md: from
    Stats SA, the Census 2022 Ward-level Small Area Population Estimates
    (population group, age and head counts by ward, `config/dimensions.toml`);
    from the Municipal Demarcation Board, the 2026 ward and voting-district
    boundaries; from the IEC, the raw results.

    Its links are relative, like the nav's, so a UAT Version URL keeps the
    reader on UAT: absolute /support and /privacy links sent UAT readers to
    live. /play/ re-points them one level down (`build_play.one_level_down`);
    the portal sits at the apex root, where they resolve to the asset root; on
    other city hosts `src/worker.js` serves both pages from the root. The
    licence wording matches LICENSE (code, MIT) and LICENSE-CONTENT (site
    text, charts and published figures, CC BY 4.0)."""
    return f"""<footer class="sitefooter">
  <p class="foot-credits">Johannesburg · 2026 Local Government Election Model · All site text, images, charts and figures are distributed under <a href="https://creativecommons.org/licenses/by/4.0/">Creative Commons BY 4.0 licence</a> and are free to re-use with attribution and a link back. Census and Ward-level Small Area Population Estimates 2022 data from <a href="{STATSSA_URL}">Stats SA</a>. Ward and voting-district boundaries from the <a href="{MDB_URL}">Municipal Demarcation Board</a>. Raw election results from the <a href="{IEC_RESULTS_URL}">IEC</a>. <a href="{REPO_URL}">Code on GitHub</a> (MIT licence) · <a href="privacy">Privacy Policy</a> · Model design by <a href="mailto:psi@whysoserious.city">Psi</a> · © 2026 whysoserious.city is part of picnic labs.</p>
  <hr class="foot-rule">
  <div class="foot-independence">
    <p>This site is politically independent and unaligned. We do not accept donations, money or in-kind support from any political party, any candidate, any of their office-bearers, or any organisation they control or fund, or that campaigns for or against a party or candidate.</p>
    <a class="foot-support" href="support">Support Our Work</a>
  </div>
</footer>"""


FOOTER = footer_for()

def inject_nav(html: str, active_href: str, og_meta: str = OG_META) -> str:
    """Give an artefact page the site navigation: the site's head into
    <head> (`og_meta` is the page's share card and canonical address; the
    site-wide one is the home page's), the class ``pg-art`` onto <body> (the
    rules every artefact page shares, src/css/page-art.css), the nav bar at
    the top of its content container so it aligns with the content, and the
    footer."""
    html = html.replace("</head>", og_meta + SITE_HEAD + "</head>", 1)
    # The template names its own page class (pg-sheet, pg-home); a body with
    # no class gets none of its own page's rules, so it is refused.
    if html.count('<body class="') != 1:
        raise SystemExit('artefact page has no <body class="pg-…">: its own '
                         "rules in site.css would reach nothing")
    html = html.replace('<body class="', '<body class="pg-art ', 1)
    # The forecast sheet's container is `.sheet`; the home page's is `.wrap`,
    # which is why the home page shipped with no menu bar at all. Either will
    # do; neither is a refusal, as it is for the footer below.
    for marker in ('<div class="sheet">', '<div class="wrap">'):
        if marker in html:
            html = html.replace(marker, marker + "\n" + nav_for(active_href), 1)
            break
    else:
        raise SystemExit("artefact page has neither a .sheet nor a .wrap "
                         "container to carry the nav")
    # Footer goes at the end of the content container so it aligns with it.
    # Marker only — an earlier fallback guessed at closing tags and prepended
    # the footer above the doctype on the sheet. Fail loudly instead.
    marker_close = "</div><!-- /sheet -->"
    if marker_close not in html:
        raise SystemExit("artefact page lacks the </div><!-- /sheet --> container marker")
    return html.replace(marker_close, FOOTER + "\n" + marker_close, 1)

# source markdown -> (output, kicker, standfirst[, tech[, og description]])
MODEL_DOCS = {
    "docs-public/corrections.md": (
        "corrections.html",
        "Corrections",
        "",
    ),
    "docs-public/methodology.md": (
        "methodology.html",
        "Methodology",
        "This page explains how the council is elected, how the simulation "
        "runs and what has been tested.",
    ),
    # /about is not a page of its own since the owner's sweep of 2026-10-03
    # (item 12): its scoring, generated into docs-public/about-the-model.md
    # by src/build_validation.py, is part of /methodology's "How accurate is
    # it?" (`validation_html`), and src/worker.js sends /about there.
    "docs-public/review.md": (
        "review.html",
        "The review",
        "",
        "model-review.html",
    ),
    "docs-public/sources.md": (
        "sources.html",
        "Data sources",
        "The model is built from election results, boundary maps, by-election "
        "returns and census tables. This page traces each to its origin and "
        "records the state it was in when we found it.",
    ),
    # The plan is no longer published as a page of its own: it is Appendix A
    # of MODEL-LOG.md, where it belongs. It is the model's starting point and
    # every numbered finding in that log is a delta from it, so the two only
    # make sense read together. As a standalone page it also carried 55 model
    # figures with no provenance — historical assertions the sourcing audit
    # cannot tell from live claims, and which nobody was maintaining.
}

# The site's own policies. Linked from the footer, not the nav: the nav holds
# the model and its record, and these describe the site around it. `False` in
# the fourth slot: no technical record on GitHub backs them, so the colophon
# says what the page is instead of pointing at one. The fifth slot is the share
# card's description (`shell(og=…)`), which carries no model figure.
#
# Always published. privacy.md's Web Analytics paragraph is conditional on the
# token (`analytics_blocks`); the rest of the page is true either way.
POLICY_DOCS = {
    "docs-public/support.md": (
        "support.html",
        "Support",
        "",
        False,
        "Who pays for the Johannesburg 2026 Election Model, who may fund it, "
        "and why no supporter has a say over what it publishes.",
    ),
    "docs-public/privacy.md": (
        "privacy.html",
        "Privacy",
        "This page says what the site records about its readers, what it "
        "does not, and who processes it.",
        False,
        "What the Johannesburg 2026 Election Model records about its readers, "
        "who is responsible for it, where it is processed, and the rights "
        "readers have over it.",
    ),
}


DOCS = {**MODEL_DOCS, **POLICY_DOCS}

_ANALYTICS_BLOCK = re.compile(
    r"^<!-- (no-analytics|analytics) -->\n(.*?)^<!-- /\1 -->\n?", re.S | re.M)


def analytics_blocks(text: str, token: str | None = None) -> str:
    """Keep a document's `<!-- analytics -->` blocks when the Web Analytics
    token is set and its `<!-- no-analytics -->` blocks when it is not; drop
    the other kind and every marker."""
    token = (CF_WEB_ANALYTICS_TOKEN if token is None else token).strip()
    keep = "analytics" if token else "no-analytics"
    return _ANALYTICS_BLOCK.sub(
        lambda m: m.group(2) if m.group(1) == keep else "", text)


# ⛔ THE PRIVACY PAGE NAMES A RESPONSIBLE PARTY, AND THE OWNER HAS NOT FILLED IT.
# POPIA requires the responsible party's identity and address. Until the
# `OWNER:` line in docs-public/privacy.md is replaced, `--publish` refuses
# (`publish_blockers`); a build without --publish (UAT, tests) still runs.
PRIVACY_SOURCE = REPO_ROOT / "docs-public" / "privacy.md"
OWNER_PLACEHOLDER = re.compile(r"^OWNER:", re.M)


def publish_blockers(text: str) -> list[str]:
    """Why privacy.md's text may not be published, or [] when it may."""
    if OWNER_PLACEHOLDER.search(text):
        return ["docs-public/privacy.md still carries the `OWNER:` placeholder: "
                "replace it with the responsible party's legal name and "
                "physical address"]
    return []

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
    # THE HOME PAGE IS THE LANDING PAGE (owner, 2026-09-23) and the forecast
    # sheet moves to /forecast. Until now the ARTICLE was the landing page, so
    # a piece written on a date sat at the front door looking current forever;
    # retiring a stale lead is now one flag in content/<city>/articles.toml.
    # PUBLISHING-BACKLOG §10.
    #
    # Keyed by the OUTPUT page: (source, the `__ONLY:<page>__` key whose spans
    # it keeps (`cut_spans`), the page's <title> or None to keep the source's,
    # the nav item it lights or None for its own name, the share-card
    # description or None for the site-wide card). The forecast sheet makes
    # every page below except the home page (owner's sweep, 2026-10-03, items
    # 10-11): /forecast holds the forecast alone; the parties' claims moved to
    # /claims; each article stands on its own page, listed on /commentary from
    # content/<city>/articles.toml.
    #
    # AN ARTICLE'S TITLE AND SHARE CARD ARE NOT HERE. Both come from its entry
    # in articles.toml (`article_meta`), the same entry /commentary and the
    # home page list it by, so the list and the page cannot name it
    # differently. An article entry that types either is refused.
    #
    # A share-card description carries no token: `statlib.render` writes
    # provenance markup, which cannot sit inside a `content="…"` attribute.
    "index.html": ("home.html", None, None, None, None),
    "forecast.html": ("forecast-sheet.html", "forecast", None, None, OG_DESCRIPTION),
    "claims.html": ("forecast-sheet.html", "claims",
                    "The parties' claims, tested", None,
                    "Public statements by the parties about November's result, "
                    "each tested against the model's simulations."),
    "commentary.html": ("forecast-sheet.html", "commentary",
                        "Commentary · Johannesburg 2026", None,
                        "Dated articles on the Johannesburg council election: "
                        "the seat law, turnout and who can govern."),
    "nobody-will-win.html": ("forecast-sheet.html", "nobody-will-win", None,
                             "commentary", None),
    "nobody-catches-the-votes.html": ("forecast-sheet.html", "nobody-catches-the-votes",
                                      None, "commentary", None),
    "minority-administrations.html": ("forecast-sheet.html", "minority-administrations",
                                      None, "commentary", None),
    "if-the-law-were-german.html": ("forecast-sheet.html", "if-the-law-were-german",
                                    None, "commentary", None),
    "laingsburg-2021.html": ("forecast-sheet.html", "laingsburg-2021",
                             None, "commentary", None),
}


def article_meta(city: str | None = None) -> dict[str, dict]:
    """Each article's articles.toml entry, keyed by its page (`<href>.html`),
    read by the one reader of that file (`render_home.load_articles`)."""
    import render_home
    city = city or cityconfig.active().slug
    return {f"{a['href']}.html": a
            for a in render_home.load_articles(REPO_ROOT / "content" / city)}


def plain_tokens(text: str, registry: dict, ctx: dict) -> str:
    """`text` with every {{token}} replaced by the figure alone, for a place
    provenance markup cannot go: an article's share card is a `content="…"`
    attribute. An unknown token is refused."""
    out, _drift, unresolved = statlib.render(text, registry, ctx, wrap=False)
    if unresolved:
        raise SystemExit(f"unresolved tokens in a share card: {unresolved}")
    return out


def artefact_head(output: str, spec: tuple, html: str,
                  articles: dict[str, dict], plain=None) -> tuple[str, str]:
    """An artefact page's <title> and share card (`og_meta`). The home page
    keeps the site-wide card at the site's root; every other page gets its own
    title, description, og:url and canonical, so a shared article shows its
    own card and a search engine does not fold it into the home page. An
    article's come from articles.toml; an ARTEFACTS entry that also types
    them is refused (two definitions of one title). `plain` renders the
    tokens in an article's standfirst as bare figures (`plain_tokens`); a
    standfirst with a token and no `plain` is refused."""
    from html import escape
    _src, _cut, title, _active, og = spec
    art = articles.get(output)
    if art is not None:
        if title or og:
            raise SystemExit(f"ARTEFACTS types a title or share card for "
                             f"{output}, an article: both come from its "
                             f"articles.toml entry")
        title, og = art["title"], " ".join(art["standfirst"].split())
        if "{{" in og:
            if plain is None:
                raise SystemExit(f"{output}: its standfirst has tokens and no "
                                 "renderer was given for its share card")
            og = plain(og)
    if title is None:
        m = re.search(r"<title>(.*?)</title>", html, re.S)
        if not m:
            raise SystemExit(f"{output}: its source has no <title> to keep")
        title = m.group(1).strip()
    else:
        title = escape(title, quote=False)
    if output == "index.html":
        return title, OG_META
    if not og:
        raise SystemExit(f"ARTEFACTS gives {output} no share-card description: "
                         "it would carry the home page's card and canonical")
    from html import unescape
    return title, page_og(og, unescape(title), output.removesuffix(".html"))

#: A span of a template that reaches only the page(s) it names.
_ONLY = re.compile(r"<!-- __ONLY:([a-z0-9,-]+)_(START|END)__ -->")


def cut_spans(html: str, keep: str | None) -> str:
    """The page `keep` cut from a template: every `__ONLY:<pages>__` span
    that names `keep` is kept, every other span is dropped, and every marker
    goes. `keep=None` drops no content and only strips the markers (the
    interactive page reads the forecast sheet's seat rows that way).

    Refuses a template whose markers do not pair or nest, and a `keep` that
    no span names: a page cut to nothing but the shared frame would publish
    as an empty page with a working nav."""
    stack: list[tuple[str, int]] = []
    spans: list[tuple[int, int, set[str]]] = []
    for m in _ONLY.finditer(html):
        if m.group(2) == "START":
            if stack:
                raise SystemExit(f"template nests __ONLY:{m.group(1)}__ inside "
                                 f"__ONLY:{stack[-1][0]}__: nothing safe to cut")
            stack.append((m.group(1), m.start()))
        else:
            if not stack or stack[-1][0] != m.group(1):
                raise SystemExit(f"template closes __ONLY:{m.group(1)}__ without "
                                 "opening it: nothing safe to cut")
            name, lo = stack.pop()
            spans.append((lo, m.end(), set(name.split(","))))
    if stack:
        raise SystemExit(f"template leaves __ONLY:{stack[-1][0]}__ unclosed: "
                         "nothing safe to cut")
    if keep is not None and not any(keep in names for _, _, names in spans):
        raise SystemExit(f"template has no __ONLY:{keep}__ span: the page "
                         "would be the shared frame alone")
    out, last = [], 0
    for lo, hi, names in spans:
        out.append(html[last:lo])
        if keep is None or keep in names:
            out.append(html[lo:hi])
            last = hi
        else:
            # a dropped span takes the line break after it, as a marker does
            last = hi + (html[hi:hi + 1] == "\n")
    out.append(html[last:])
    return re.sub(_ONLY.pattern + r"\n?", "", "".join(out))


#: Where /commentary's list of articles goes (forecast-sheet.html).
COMMENTARY_MARKER = "<!-- __COMMENTARY__ -->"


def fill_commentary(html: str, city: str | None = None) -> str:
    """/commentary's article list, written at build time from
    content/<city>/articles.toml by the same function that writes the home
    page's (`render_home._articles`), so the two lists cannot differ. Every
    entry is its own dated passage. A page without the marker is returned
    unchanged; a page with two is refused."""
    n = html.count(COMMENTARY_MARKER)
    if n == 0:
        return html
    if n > 1:
        raise SystemExit(f"{n} {COMMENTARY_MARKER} markers on one page")
    import render_home
    city = city or cityconfig.active().slug
    return html.replace(COMMENTARY_MARKER,
                        render_home._articles(REPO_ROOT / "content" / city).strip(), 1)


def page_og(og: str, page_title: str, href: str) -> str:
    """OG_META with this page's own share-card description, title, og:url and
    canonical. Only the policy pages pass one; every other page keeps the
    site-wide card."""
    from html import escape
    url = f"{SITE_URL}/{href}"
    out = re.sub(r'(<meta property="og:description" content=")[^"]*(">)',
                 lambda m: m.group(1) + escape(og) + m.group(2), OG_META, count=1)
    out = re.sub(r'(<meta property="og:title" content=")[^"]*(">)',
                 lambda m: m.group(1) + escape(page_title) + m.group(2), out, count=1)
    out = out.replace(f'<meta property="og:url" content="{SITE_URL}/">',
                      f'<meta property="og:url" content="{url}">', 1)
    out = out.replace(f'<link rel="canonical" href="{SITE_URL}/">',
                      f'<link rel="canonical" href="{url}">', 1)
    if out.count(url) != 2 or escape(og) not in out:
        raise SystemExit(f"OG_META no longer has the fields page_og rewrites ({href})")
    return out


def shell(title: str, kicker: str, masthead: str, body: str, generated_note: str,
          active_href: str = "", og: str | None = None) -> str:
    og_meta = page_og(og, title, active_href) if og else OG_META
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{og_meta}{SITE_HEAD}</head>
<body class="pg-doc">
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


def _md_html(text: str) -> str:
    """A document's Markdown as the site's HTML. `toc` gives every heading an
    id, so a link can land on a section (the home page's "How well it has
    done" lands on /methodology's "How accurate is it?")."""
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "smarty", "toc"],
                             extension_configs={"toc": {"slugify": _heading_id}})
    html = html.replace("<table>", '<div class="tablewrap"><table>')
    return html.replace("</table>", "</table></div>")


def _heading_id(value: str, separator: str) -> str:
    """A heading's id from its words. `toc` runs before tokens are filled in,
    so a token's name is dropped rather than let into the address
    ("### 8. Do it {{n_draws}} times" -> `8-do-it-times`)."""
    from markdown.extensions.toc import slugify
    return slugify(re.sub(r"\{\{[^}]*\}\}", " ", value), separator)


#: A table whose body cells after the first column are all figures (or empty).
_FIGURE_CELL = re.compile(r"^(?:<strong>)?[−+-]?\d")


def figure_tables(html: str) -> str:
    """Mark each table whose columns after the first hold only figures with
    the class `figures`, which right-aligns them in tabular digits and fixes
    the column widths (src/css/page-doc.css), so one city's table lines up
    with the next. Python-Markdown's own `|--:|` alignment writes an inline
    `style=`, which the site does not carry."""
    def mark(m: re.Match) -> str:
        table = m.group(0)
        body = table.split("</thead>", 1)[-1]
        cells = [re.sub(r"\s+", " ", c).strip()
                 for row in re.findall(r"<tr>(.*?)</tr>", body, re.S)
                 for c in re.findall(r"<td>(.*?)</td>", row, re.S)[1:]]
        if cells and all(not c or _FIGURE_CELL.match(c) for c in cells):
            return table.replace("<table>", '<table class="figures">', 1)
        return table
    return re.sub(r"<table>.*?</table>", mark, html, flags=re.S)


#: The scoring of the model against 2021, written whole by
#: src/build_validation.py (never by hand), and the line in
#: docs-public/methodology.md where the build puts it.
VALIDATION_SOURCE = REPO_ROOT / "docs-public" / "about-the-model.md"
VALIDATION_MARKER = "<!-- __VALIDATION__ -->"


def validation_html(source: Path = VALIDATION_SOURCE) -> str:
    """The validation section as HTML, inside a `VALIDATION` region.

    ⛔ THE REGION IS WHAT KEEPS ITS FIGURES SCRIPT-MADE. The file is generated,
    and its figures come from `data/processed/validation_<year>.json`; as its
    own page it was scanned with `generated_page=True`. Spliced into a
    hand-written page it would be scanned as prose, so it is wrapped in a
    region named in `stats.GENERATED_MARKERS`, where the scan lists its
    figures as generated and does not gate them. A file that does not open
    with the generator's marker is refused rather than exempted."""
    text = source.read_text(encoding="utf-8")
    head = re.match(r"\s*<!-- GENERATED by src/build_validation\.py.*?-->\s*", text, re.S)
    if not head:
        raise SystemExit(f"{source} does not open with src/build_validation.py's "
                         "GENERATED marker: its figures cannot be exempted as "
                         "script-made. Regenerate it (--from-json).")
    return ("<!-- __VALIDATION_START__ -->\n" + figure_tables(_md_html(text[head.end():]))
            + "\n<!-- __VALIDATION_END__ -->")


#: Any start or end marker of a script-made region (`stats.GENERATED_MARKERS`).
_GENERATED_MARKER = re.compile(
    r"__(%s)_(?:START|END)__" % "|".join(sorted(statlib.GENERATED_MARKERS)))


def typed_generated_markers(text: str) -> list[str]:
    """The script-made region markers a hand-written source carries. Markdown
    passes HTML comments through, so a document that typed
    `<!-- __VALIDATION_START__ -->` around a sentence would have its figures
    listed as generated and left out of the claim audit."""
    return sorted({m.group(0) for m in _GENERATED_MARKER.finditer(text)})


def render_doc(source: Path, kicker: str, standfirst: str, output: str = "",
               tech: str | None | bool = None, og: str | None = None,
               token: str | None = None) -> str:
    """`tech` names the technical record on GitHub that a reader edition is
    drawn from; None derives it from the file name, False says there is none
    (a page about the site, not the model). `og` is the page's own share-card
    description; None keeps the site-wide one. `token` is the Web Analytics
    token that picks the document's analytics blocks; None reads the
    module's."""
    raw = source.read_text(encoding="utf-8")
    typed = typed_generated_markers(raw)
    if typed:
        raise SystemExit(f"{source} types the script-made region marker(s) "
                         f"{', '.join(typed)}: a figure inside one is listed as "
                         "generated and does not block. Only a generator writes "
                         "them (methodology's VALIDATION is spliced in by "
                         "`validation_html` at the __VALIDATION__ line).")
    text = analytics_blocks(raw, token)
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

    # A dated piece leads with its date, above the headline, the way the claim
    # boxes do (owner, 2026-09-18). The date is taken from the document's own
    # `<div class="pubdate">…</div>` if it has one, so the markdown stays the
    # single source and the header stops carrying a second copy.
    published = ""
    m = re.search(r'<div class="pubdate">(.*?)</div>\s*', body_md, re.S)
    if m:
        published = f'  <div class="pubdate">{m.group(1).strip()}</div>\n'
        body_md = body_md[:m.start()] + body_md[m.end():]
    html = _md_html(body_md)
    if VALIDATION_MARKER in html:
        html = html.replace(VALIDATION_MARKER, validation_html(), 1)

    # An empty standfirst prints none: a page whose first paragraph already
    # says it needs no second copy above it (STYLE.md rule 9).
    masthead = published + f"  <h1>{title}</h1>"
    if standfirst:
        masthead += f'\n  <p class="standfirst">{standfirst}</p>'
    if tech is False:
        note = ("This page describes how the site is run. It is not part of "
                "the model or its record.")
    elif str(source).startswith("docs-public/"):
        tech = tech or source.name.replace(".md", "").upper() + ".md"
        note = (f"Reader edition, generated from {source} on "
                f"{date.today().isoformat()}. The full technical record, with "
                f"every URL, identifier and workaround, is "
                f'<a href="https://github.com/Psi-am-i/jhb-election-model/blob/main/{tech}">'
                f"{tech} on GitHub</a>.")
    else:
        note = (f"Generated from {source.name} by src/build_site.py on "
                f"{date.today().isoformat()} — the Markdown file in the project "
                f"repository is canonical; regenerate rather than editing this page.")
    return shell(f"Johannesburg 2026 — {title}", kicker, masthead, html, note,
                 active_href=output.removesuffix(".html"), og=og)




def _ledger_candidates(published: list[dict], ledger: dict, ident: dict,
                       now: str, *, reason: str | None,
                       change_class: str | None,
                       since: dict[str, str] | None = None):
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

    ``since`` is `publication.run_starts` over the ledger: when the last
    published value first appeared. Each change carries it twice, because the
    reader is owed both dates: ``previous_since`` (when the last published
    value first appeared) and ``since`` (when the value on the page first
    appeared — the same date when nothing moved, None when this build would
    publish it for the first time).
    """
    since = since or {}
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
            "previous_value": None if prev is None else prev.value,
            "previous_published_at": None if prev is None else prev.published_at,
            "previous_since": None if prev is None else since.get(name),
            "since": (since.get(name) if prev is not None
                      and movement in ("none", "rounding") else None),
            "fmt": occ.get("fmt"), "source": occ.get("source", ""),
            "mode": occ.get("mode"), "pages": pages[name],
        })
    return rows, changes


def audit_configs(registry: dict, ctx: dict) -> tuple[dict, dict]:
    """The settings EVERY page is audited and scanned with, in one place.

    ⛔ ONE DEFINITION. These were assembled inline in `main`, so anything else
    wanting to ask "would the build refuse this page?" — a test, a preview —
    had to retype the structural set, and a retyped copy answers a different
    question the moment the council changes size.

    `structural` is the council's own constants, read from the model's outputs
    and never typed here: the council size and the threshold as this run
    reports them, and the ward count. A number that IS the electoral system is
    not a model figure and must not be demanded as a token.

    Returns ``(audit_cfg, scan_cfg)`` — `scan_cfg` is the subset
    `stats.scan_numbers` takes, which is not the same set of keys. Neither
    names a page: every caller passes ``page=`` with the output path it is
    scanning, because a registered fact clears only on the pages it lists
    (`stats.for_page`).
    """
    audit_cfg = statlib.load_audit_config(registry)
    draw0 = (ctx.get("draws") or [{}])[0]
    structural = {str(draw0.get("council_size", "")), str(draw0.get("threshold", "")),
                  str(len(ctx.get("wards") or [])) if ctx.get("wards") else ""}
    structural |= {str(cityconfig.active().wards)} if hasattr(cityconfig.active(), "wards") else set()
    structural = {s for s in structural if s}
    scan_cfg = {"fixed": audit_cfg["fixed"], "structural": structural}
    return {**audit_cfg, "structural": structural}, scan_cfg


#: The Content-Type of every non-HTML file the site serves, by extension.
#:
#: Pages are served as UTF-8 HTML by a blanket `/*` rule, because their URLs
#: carry no extension (`/forecast`) — the sheet once shipped without a <head>
#: and mojibake'd every em-dash (review of the deployed site, 2026-08-04). That
#: rule also matched every other file, so `/draws/*.bin`, `/py/*.py` and any
#: `.js` module were served as text/html and ES modules refused to run (blind
#: review B1, 2026-09-30). Each extension below DETACHES the blanket type and
#: sets its own.
#:
#: ⛔ ONE RULE PER EXTENSION, NEVER ONE PER DIRECTORY AS WELL. Cloudflare applies
#: every matching rule and comma-joins a header two rules set, so `/draws/*`
#: beside `/*.json` would serve `draws/index.json` as
#: "application/octet-stream, application/json". `/draws/*`, `/py/*` and `/js/*`
#: are covered by their files' extensions. A file whose extension is not here
#: is served as HTML — `tests/test_site_headers.py` fails on one.
CONTENT_TYPES = {
    ".bin": "application/octet-stream",
    ".json": "application/json; charset=utf-8",
    ".py": "text/x-python; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".wasm": "application/wasm",
    ".css": "text/css; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".svg": "image/svg+xml",
}


#: Sent with every file (the `/*` rule). No `script-src`: /play/ runs Pyodide
#: (WebAssembly compiled in the page) and the Web Analytics beacon loads from
#: static.cloudflareinsights.com, so a script policy would break both. The CSP
#: only stops other sites framing these pages. HSTS carries no
#: `includeSubDomains` (nothing in this repository can show that every
#: whysoserious.city subdomain serves HTTPS) and no `preload`.
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "frame-ancestors 'self'",
    "Strict-Transport-Security": "max-age=31536000",
}


def headers_text() -> str:
    """The `_headers` file: HTML by default, each asset type by extension, the
    security headers on every file, and the working copies (`/dev/`,
    `/drafts/`) reachable but never indexed."""
    rules = ["/*\n  Content-Type: text/html; charset=utf-8\n"
             + "".join(f"  {k}: {v}\n" for k, v in SECURITY_HEADERS.items())]
    rules += [f"/*{ext}\n  ! Content-Type\n  Content-Type: {ctype}\n"
              for ext, ctype in CONTENT_TYPES.items()]
    rules += ["/dev/*\n  X-Robots-Tag: noindex, nofollow\n",
              "/drafts/*\n  X-Robots-Tag: noindex, nofollow\n"]
    return "".join(rules)


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
    parser.add_argument("--privacy-source", type=Path, default=None,
                        help="the privacy page whose OWNER line gates "
                             "--publish (default: docs-public/privacy.md). "
                             "Exists so a test can reach the refusals after "
                             "that one; the page rendered is always the real one.")
    cityconfig.add_city_argument(parser)
    args = parser.parse_args(argv)
    # Before anything is written anywhere, the ledger and --out included.
    if args.publish:
        privacy = args.privacy_source or PRIVACY_SOURCE
        blockers = publish_blockers(privacy.read_text(encoding="utf-8"))
        if blockers:
            raise SystemExit("refusing to publish: " + "; ".join(blockers))
    cityconfig.use(getattr(args, "city", None))
    args.processed = args.processed or cityconfig.use_target(
        getattr(args, "target", None)).processed

    args.out.mkdir(exist_ok=True)
    # The stylesheet and the site's scripts go first: every page links them,
    # and the script check below reads each script a page loads from disk.
    assets = site_assets.write(args.out)
    print(f"  wrote    {len(assets)} asset(s): {site_assets.CSS_PATH} and "
          f"{site_assets.JS_DIR}/*.js from src/css and src/js")
    registry = statlib.load_registry(args.stats) if args.stats.exists() else {}
    ctx = statlib.load_context(args.processed)
    audit_cfg, scan_cfg = audit_configs(registry, ctx)
    all_drift: list[dict] = []
    unresolved_all: list[str] = []
    audits: dict[str, tuple[list[str], list[str]]] = {}
    # Every number-shaped string on every page, for the committed review file.
    scans: dict[str, list[dict]] = {}
    generated: list[str] = []
    # Every token OCCURRENCE that reached a reader, in reading order. The
    # ledger needs the raw value AND the displayed string; see `stats.render`.
    published: list[dict] = []

    # The methodology page's "The judgement calls" section is regenerated from
    # the register's Plain fields before anything is rendered, so the page can
    # never be older than the register it is built beside. One source: the
    # field in JUDGEMENT-CALLS.md. Its words are a person's, so the region is
    # scanned as prose by the number gate like the rest of the page.
    import judgement_sheet
    if judgement_sheet.refresh_methodology():
        print("  refreshed docs-public/methodology.md 'The judgement calls' "
              "from JUDGEMENT-CALLS.md")

    for source, spec in DOCS.items():
        output, kicker, standfirst = spec[:3]
        tech = spec[3] if len(spec) > 3 else None
        og = spec[4] if len(spec) > 4 else None
        page = render_doc(Path(source), kicker, standfirst, output, tech, og)
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
            scans[output] = statlib.scan_numbers(page, page=output,
                                                 generated_page=True, **scan_cfg)
        else:
            # A script-made region (methodology's VALIDATION) is listed by the
            # scan as generated; the claim audit is for prose a person wrote.
            prose = statlib.REGION.sub(
                lambda m: " " if m.group(1) in statlib.GENERATED_MARKERS else m.group(0),
                page)
            audits[output] = statlib.audit(prose, page=output, **audit_cfg)
            scans[output] = statlib.scan_numbers(page, page=output, **scan_cfg)
        (args.out / output).write_text(page, encoding="utf-8")
        print(f"  rendered {source:<28s} -> site/{output}")

    articles = article_meta()
    for output, spec in ARTEFACTS.items():
        source, cut, _title, active, _og = spec
        href = active or ("./" if output == "index.html" else output.removesuffix(".html"))
        html = cut_spans(Path(source).read_text(encoding="utf-8"), cut)
        title, og_meta = artefact_head(
            output, spec, html, articles,
            plain=lambda t: plain_tokens(t, registry, ctx))
        html = re.sub(r"<title>.*?</title>", lambda _m: f"<title>{title}</title>",
                      html, count=1, flags=re.S)
        html = fill_commentary(html)
        html = inject_nav(html, href, og_meta)
        seen = []
        html, drift, unresolved = statlib.render(html, registry, ctx,
                                                 record=seen)
        published += [{**r, "page": output} for r in seen]
        all_drift += drift
        unresolved_all += [f"{source}: {u}" for u in unresolved]
        audits[output] = statlib.audit(html, page=output, **audit_cfg)
        scans[output] = statlib.scan_numbers(html, page=output, **scan_cfg)
        (args.out / output).write_text(html, encoding="utf-8")
        print(f"  nav+copy {source:<28s} -> site/{output}")

    # --- "play with the model" (/play/), Johannesburg's only ----------------
    # Assembled by build_play from interactive/model.html, then rendered,
    # audited and scanned HERE exactly like the pages above, so its first
    # paint is ledgered tokens and it enters the review stamp deploy_check
    # reads. Its scripts are held to the LIVE-writer contract below, with every
    # other page's (`statlib.script_writes`). The page runs on Johannesburg's
    # draws (site/draws/), so no other city's build writes it. Built by every
    # Johannesburg build since the draws ship (2026-10-01: export_draws writes
    # no local path and no internal poll note, so site/.assetsignore is gone).
    if cityconfig.active().slug == "joburg":
        import build_play
        written = build_play.write_assets(args.out, args.processed)
        html = build_play.assemble(site_head=page_og(build_play.OG_DESCRIPTION,
                                                     build_play.OG_TITLE, build_play.PLAY_HREF)
                                   + SITE_HEAD,
                                   nav=nav_for(build_play.PLAY_HREF), footer=FOOTER,
                                   processed=args.processed)
        seen = []
        html, drift, unresolved = statlib.render(html, registry, ctx, record=seen)
        published += [{**r, "page": build_play.PLAY_PAGE} for r in seen]
        all_drift += drift
        unresolved_all += [f"interactive/model.html: {u}" for u in unresolved]
        audits[build_play.PLAY_PAGE] = statlib.audit(
            html, page=build_play.PLAY_PAGE, **audit_cfg)
        scans[build_play.PLAY_PAGE] = statlib.scan_numbers(
            html, page=build_play.PLAY_PAGE, **scan_cfg)
        (args.out / build_play.PLAY_PAGE).write_text(html, encoding="utf-8")
        print(f"  play     interactive/model.html       -> site/{build_play.PLAY_PAGE} "
              f"(+{len(written)} files under site/{build_play.PLAY_DIR}/)")
        # "make your own forecast" (/make/), the same way: assembled by
        # build_make from interactive/make.html, rendered, audited and scanned
        # here; its scripts are held to the LIVE-writer contract like /play/'s.
        import build_make
        written = build_make.write_assets(args.out)
        html = build_make.assemble(site_head=page_og(build_make.OG_DESCRIPTION,
                                                     build_make.OG_TITLE, build_make.MAKE_HREF)
                                   + SITE_HEAD,
                                   nav=nav_for(build_make.MAKE_HREF), footer=FOOTER,
                                   cut_markers=cut_spans)
        seen = []
        html, drift, unresolved = statlib.render(html, registry, ctx, record=seen)
        published += [{**r, "page": build_make.MAKE_PAGE} for r in seen]
        all_drift += drift
        unresolved_all += [f"interactive/make.html: {u}" for u in unresolved]
        audits[build_make.MAKE_PAGE] = statlib.audit(
            html, page=build_make.MAKE_PAGE, **audit_cfg)
        scans[build_make.MAKE_PAGE] = statlib.scan_numbers(
            html, page=build_make.MAKE_PAGE, **scan_cfg)
        (args.out / build_make.MAKE_PAGE).write_text(html, encoding="utf-8")
        print(f"  make     interactive/make.html        -> site/{build_make.MAKE_PAGE} "
              f"(+{len(written)} files under site/{build_make.MAKE_DIR}/)")
    # EVERY PAGE THIS BUILD NO LONGER PRODUCES IS REMOVED, not just the one
    # somebody remembered. A single hard-coded `forecast.html` unlink stood here
    # for months while `plan.html` and, the moment the interactive was withheld,
    # `interactive.html` both stayed on the site — served, linked from nothing,
    # and describing a model that had moved on. A page nobody rebuilds is worse
    # than a missing one: it looks current and cannot be.
    produced = {"index.html"} | {spec[0] for spec in DOCS.values()} \
        | set(ARTEFACTS) | {"portal.html"}
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
    since = publication.run_starts(publication.history(city, root=ledger_root))
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
    # A generated token (`{{@name=…}}`) has no registry entry by design — it
    # carries its value inline — so "left the registry" is the wrong test for
    # it. What matters is whether the figure is still on a page this build
    # writes: gone from both the registry AND the pages, unretired, refuses.
    on_page = {r["token"] for r in published if r.get("token")}
    vanished = sorted(t for t, row in ledger.items()
                      if t not in registry and t not in on_page and not row.superseded_at)
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
    misdated = publication.misdated_figures(
        published, statlib.council_constant_tokens(registry))
    if misdated:
        refuse = True
        print("\nA DATED PASSAGE PRINTS A FIGURE THAT IS NOT OF ITS DATE — "
              "refusing:")
        for v in sorted({(v["token"], v["page"], v["asof"], v["why"])
                         for v in misdated}):
            print(f"  ✗ {v[0]} on {v[1]}, dated {v[2]}: {v[3]}")
        print("  Freeze the figure as published (a `pub*` token, mode fixed, "
              "`captured` the passage's date, `tracks` the live token), or "
              "move it out of the dated passage.")
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

    # --- the portal, built HERE so one command produces every page ---------
    # ⛔ IT USED TO BE A SEPARATE COMMAND, AND THAT IS HOW IT WENT STALE.
    # `build_portal.py` was edited on 2026-09-27 and the page it writes was not
    # regenerated for a whole batch, so the apex page would have shipped with a
    # claim the same batch had removed. Nothing objected, because the review's
    # stamp did not name it and `deploy_check` only hashes what the stamp names
    # — while `wrangler.toml` ships `./site` wholesale.
    #
    # Building it here means one command produces all nine pages, and the scan
    # below puts it in the stamp so the gate can see it. It is scanned as a
    # GENERATED page: every figure on it is read from a city's own
    # `forecast_summary.json` by `build_portal.city_card`, none is typed.
    import build_portal
    build_portal.main(["--out", str(args.out / "portal.html")])
    portal_page = (args.out / "portal.html").read_text(encoding="utf-8")
    scans["portal.html"] = statlib.scan_numbers(portal_page, page="portal.html",
                                                generated_page=True, **scan_cfg)
    generated.append("portal.html")

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
    # ⛔ NO INLINE CSS OR JS ON ANY PAGE (owner's sweep, 2026-10-03). Every
    # page this build wrote, at any depth, not just the ones the number review
    # stamps: `wrangler.toml` ships the directory whole.
    _pages, inline = site_assets.scan_site(args.out)
    if inline:
        print("\nINLINE CSS OR JS — refusing to build: styles belong in src/css "
              "(site/css/site.css) and scripts in .js files:")
        for w in inline[:40]:
            print(f"  ✗ {w}")
        if len(inline) > 40:
            print(f"  … and {len(inline) - 40} more")
        raise SystemExit(1)
    script_problems = [f"{page}: {w}" for page in sorted(scans)
                       if (args.out / page).is_file()
                       for w in statlib.script_writes(
                           (args.out / page).read_text(encoding="utf-8"),
                           page=args.out / page, root=args.out)]
    if script_problems:
        print("\nPAGE SCRIPT WRITES FIGURES — refusing to build: every figure must be "
              "rendered at build time as a token, where it has provenance, a ledger "
              "row and a scan:")
        for w in script_problems:
            print(f"  ✗ {w}")
        raise SystemExit(1)

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
            gate = statlib.is_blocking(h)
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
            "with no source. Register each figure as a {{token}} or an "
            "[[audit.fixed]] fact with its page and source; a claim in words "
            "that is historical fact, a statement of the rules, or reviewed "
            "static prose goes in [[audit.allow]] with its page.")

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
                                       change_class=args.change_class,
                                       since=since)
    summary = publication.summarise(rows)
    # ⛔ `new` IS NOT A MOVE, and treating it as one writes a lie into a record
    # that cannot be rewritten. `classify` returns "new" for a first
    # publication; if that counts as moved, the FIRST EVER --publish demands a
    # --change-class, and every founding row is then stamped `recompute` /
    # `mechanism` / `bugfix` — none of which describes a figure that was never
    # published before. Found in blind review 2026-08-31; the print two lines
    # below already counted new separately and this did not.
    moved = [c for c in changes if c["movement"] not in ("none", "new")]

    # THE ARROWS. The ledger has classified every figure against the last
    # publication since 2026-08-31, and nothing ever drew it: the reader-facing
    # half of "what changed" did not exist (found 2026-09-17). A figure that
    # moved visibly gets ▲/▼ (◆ when a string changed) and a tooltip naming what
    # it was and when; a first publication and a sub-precision move get nothing.
    import html as _html
    import re as _re
    arrows = {}
    for c in changes:
        if c["movement"] not in ("material", "minor", "nominal") or c["previous"] is None:
            continue
        try:
            glyph = "▲" if float(c["value"]) > float(c["previous_value"]) else "▼"
        except (TypeError, ValueError):
            glyph = "◆"
        was = f"Was {c['previous']}."
        arrows[c["token"]] = (glyph, was, {"▲": "up", "▼": "down"}.get(glyph, "changed"))
    # Every tooltip states the figure and what the published site last said,
    # so a reader hovering any number sees whether it changed (owner, 2026-09-17:
    # "if something changes, the change should be surfaced").
    now_date = now[:10]
    # ⛔ A BUILD IS NOT A PUBLICATION, AND TODAY IS NOT A PROVENANCE.
    # These tooltips used to date every never-published figure to whenever the
    # build ran — "First published in this edition (24 September 2026)" on a
    # figure that has been published nowhere, with the date changing each day
    # and, because the stamp is UTC, changing mid-evening in South Africa. Two
    # costs: the page asserted a publication that had not happened, and five
    # pages differed from a fresh build with no token moved and no visible text
    # changed, which `test_published_page` reported as a real difference
    # (2026-09-25). Outside a `--publish`, the tooltip states what it knows —
    # that the figure is new, or that it moved — and dates only what actually
    # has a date.
    publishing = bool(getattr(args, "publish", False))
    # TOOLTIP CONVENTION (owner, 2026-09-17): the brief statement first, then
    # dates and source. "{new}. Was {old}." for a live figure that moved;
    # "{old}. Is now {new}." for a frozen, as-published one.
    def _long(d):
        from datetime import date as _date
        try:
            y, m, dd = (int(x) for x in str(d)[:10].split("-"))
            return f"{dd} {_date(y, m, dd):%B %Y}"
        except (ValueError, TypeError):
            return str(d)
    history = {}
    display_now = {c["token"]: c["display"] for c in changes}
    registry_entries = {k: v for k, v in registry.items() if isinstance(v, dict)}
    for c in changes:
        tracked = (registry_entries.get(c["token"]) or {}).get("tracks")
        if tracked:
            # A FROZEN figure whose live counterpart has moved gets its own
            # muted marker: the reader should see that the published number has
            # since changed, without it being read as a move in this edition.
            now_disp = display_now.get(tracked)
            if now_disp and now_disp != c["display"]:
                def _num(s):
                    try:
                        return float(str(s).strip().rstrip("%").replace(",", ""))
                    except ValueError:
                        return None
                a, b = _num(c["display"]), _num(now_disp)
                arrows[c["token"]] = (("↗" if b > a else "↘") if None not in (a, b) else "◆",
                                      f"Is now {now_disp}.", "moved-since")
            when = _long((registry_entries[c["token"]] or {}).get("captured", ""))
            now = display_now.get(tracked)
            # "5,000. Is now 5,000." says nothing: an equal live figure is
            # not a change, so the frozen one states only when it was published.
            if now == c["display"]:
                now = None
            history[c["token"]] = (
                (f"{c['display']}. Is now {now}. " if now else f"{c['display']}. ")
                + f"Published {when}"
                + ((f"; now {_long(now_date)}." if publishing else "; changed since.")
                   if now else "."))
        elif c["previous"] is None:
            history[c["token"]] = (
                f"{c['display']}. First published in this edition "
                f"({_long(now_date)})." if publishing else
                f"{c['display']}. Not published before; new in this edition.")
        elif c["movement"] in ("none", "rounding"):
            # The first date of the unbroken run, not the latest row
            # (`publication.run_starts`; owner's sweep, 2026-10-03).
            history[c["token"]] = (f"{c['display']}. Unchanged since "
                                   f"{_long(c['since'])}.")
        else:
            history[c["token"]] = (
                f"{c['display']}. Was {c['previous']}. Published "
                f"{_long(c['previous_since'])}"
                + (f"; now {_long(now_date)}." if publishing else "; changed since."))
    if changes:
        for page in sorted({p for c in changes for p in c["pages"]}):
            f = args.out / page
            if not f.is_file():
                continue
            text = f.read_text(encoding="utf-8")
            # NO EDITION ARROWS ON /play/ (review 2026-10-02). There a ▲▼ means
            # "your settings against the published forecast" (play/js/model.js),
            # and the published twin carrying edition arrows in the same glyph
            # made an untouched page look moved. Its figures keep the history
            # tooltip; only the glyph is left off.
            import build_play as _bp
            glyphs = not page.startswith(f"{_bp.PLAY_DIR}/")

            def _mark(m):
                token = _re.search(r'data-token="([^"]+)"', m.group(0)).group(1)
                glyph, was, cls = arrows[token]
                return (m.group(0) + f'<span class="arrow mstat-move {cls}" '
                        f'data-prov="{_html.escape(was, quote=True)}">{glyph}</span>')
            def _prov(m):
                span = m.group(1)
                note = history.get(m.group(2))
                if note:
                    span = _re.sub(r'data-prov="([^"]*)"',
                                   lambda d: f'data-prov="{_html.escape(note, quote=True)} {d.group(1)}"',
                                   span, count=1)
                return (_mark(_re.match(r"(.*)", span, _re.S))
                        if glyphs and m.group(2) in arrows else span)
            text = _re.sub(r'(<span class="mstat"[^>]*data-token="([^"]+)"[^>]*>[^<]*</span>)',
                           _prov, text)
            f.write_text(text, encoding="utf-8")
        # the pages changed, so the number review's page stamp must follow them
        import hashlib as _hashlib
        stamp = _re.compile(r"<!-- built-pages: (.*?) blocking=(\d+) -->")
        body = review_path.read_text(encoding="utf-8")
        m = stamp.search(body)
        if m:
            shas = " ".join(
                f"{k}={_hashlib.sha256((args.out / k).read_bytes()).hexdigest()}"
                for k in (pair.split("=", 1)[0] for pair in m.group(1).split()))
            review_path.write_text(stamp.sub(
                f"<!-- built-pages: {shas} blocking={m.group(2)} -->", body, count=1),
                encoding="utf-8")
    # --- the seat-law counterfactuals, as a shippable artefact -------------
    # ⛔ THE FOUR REGIME RUNS EXIST ONLY ON THE MACHINE THAT MADE THEM.
    # `overhang_regimes.py` writes them into `data/processed/`, and `data/**`
    # is gitignored — so the control with the largest measured effect of any
    # candidate (the ANC at 67 under the shipped rule against 58 under pure
    # proportionality) had nothing a page could read. This lifts the four
    # summaries into one small file beside the pages.
    #
    # It is a REDUCTION, not a re-run: medians and bands off summaries already
    # produced at the published 5,000 draws. If a regime summary is missing the
    # file simply omits it and says which, because a seat-law control that
    # silently drops a law is worse than one that is absent.
    regimes = {}
    for rule, label in (("deduct", "Our law — the surplus is deducted from everyone else"),
                        ("expand", "Old Germany — the council grows to absorb the surplus"),
                        ("level", "Modern Germany — every party is topped up to proportionality"),
                        ("cap", "Germany 2023 — pure proportionality at a fixed council")):
        src = (args.processed / "forecast_summary.json" if rule == "deduct"
               else args.processed / f"regime_{rule}_summary.json")
        if not src.is_file():
            continue
        blob = json.loads(src.read_text(encoding="utf-8"))
        regimes[rule] = {
            "label": label,
            "parties": {k: {m: v.get(m) for m in ("median", "p5", "p95")}
                        for k, v in (blob.get("parties") or {}).items()
                        if isinstance(v, dict)},
            "p_excessive_any": blob.get("p_excessive_any"),
            "threshold_median": blob.get("threshold_median"),
            "structural": blob.get("structural") or {},
        }
    missing = [r for r in ("deduct", "expand", "level", "cap") if r not in regimes]
    (args.out / "regimes.json").write_text(
        json.dumps({"rules": regimes, "missing": missing,
                    "note": "Reduced from the published run's own summaries; "
                            "no regime was re-run to build this."},
                   indent=1), encoding="utf-8")
    print(f"  wrote    regimes.json ({len(regimes)} seat law(s)"
          + (f"; MISSING {', '.join(missing)} — run src/overhang_regimes.py" if missing else "")
          + ")")

    print(f"  arrows: {len(arrows)} figure(s) marked as moved since the last publication")

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

    (args.out / "_headers").write_text(headers_text(), encoding="utf-8")
    # No comment in robots.txt: it is public, and a line describing /dev/
    # tells every reader where the unreleased build is. The Disallow lines
    # stay; /dev/ and /drafts/ duplicate live content.
    (args.out / "robots.txt").write_text(
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
