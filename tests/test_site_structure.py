"""The site's structure (owner's sweep of 2026-10-03, items 9-15): the nav, the
pages cut from the forecast sheet, /commentary and its articles, the old
article anchors, /about merged into /methodology, and the footer.

Each check that asserts an absence or a correspondence follows CLAUDE.md §4:
the population is computed and stated, it is bounded on both sides, a
constructed violation is caught (and the detector is quiet again without it),
and the detector cases are written here rather than read off a passing tree.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import build_play  # noqa: E402
import build_your_forecast  # noqa: E402
import build_site as B  # noqa: E402

SHEET = ROOT / "forecast-sheet.html"
ARTICLES = ROOT / "content" / "joburg" / "articles.toml"
#: The last commit before the sweep split the article off: the ids a shared
#: link to /nobody-will-win or /forecast could carry.
BEFORE_SPLIT = "a912197"

#: The owner's nav, in order (sweep of 2026-10-03, item 9).
NAV = ["our forecast", "your prediction", "commentary", "party claims",
       "methodology", "review", "corrections", "sources", "source code"]

#: The owner's footer, his words, with his two typos corrected
#: ("distribute" -> "distributed", "indpendant" -> "independent"), XXX filled
#: from SOURCES.md, the Municipal Demarcation Board added, and "(c)" set as ©.
FOOTER_CREDITS = (
    "Johannesburg · 2026 Local Government Election Model · All site text, "
    "images, charts and figures are distributed under Creative Commons BY 4.0 "
    "licence and are free to re-use with attribution and a link back. Census "
    "and Ward-level Small Area Population Estimates 2022 data from Stats SA. "
    "Ward and voting-district boundaries from the Municipal Demarcation Board. "
    "Raw election results from the IEC. Code on GitHub (MIT licence) · Privacy "
    "Policy · Model design by Psi · © 2026 whysoserious.city is part of picnic labs.")
FOOTER_INDEPENDENCE = (
    "This site is politically independent and unaligned. We do not accept "
    "donations, money or in-kind support from any political party, any "
    "candidate, any of their office-bearers, or any organisation they control "
    "or fund, or that campaigns for or against a party or candidate.")


def _text(html: str) -> str:
    """The words a reader sees in a run of inline markup."""
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", html))).strip()


def _ids(html: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', html))


def _produced() -> set[str]:
    """The pages build_site writes at the site root (the build's own sweep
    removes every other root page)."""
    return ({spec[0] for spec in B.DOCS.values()} | set(B.ARTEFACTS)
            | {"portal.html"})


def _sheet_pages() -> dict[str, str]:
    """Each page the build cuts from the forecast sheet, cut."""
    raw = SHEET.read_text(encoding="utf-8")
    return {out: B.cut_spans(raw, key) for out, (src, key, *_r) in B.ARTEFACTS.items()
            if src == SHEET.name}


# ---------------------------------------------------------------- the nav

def nav_problems(items) -> list[str]:
    produced = {p.removesuffix(".html") for p in _produced()}
    out = []
    labels = [label for _href, label in items]
    if labels != NAV:
        out.append(f"nav labels {labels} != the owner's {NAV}")
    for href, label in items:
        if href.startswith("https://"):
            continue
        if href == build_your_forecast.YF_HREF:
            continue
        if href not in produced:
            out.append(f"nav item {label!r} -> {href!r}, a page this build does not produce")
    return out


def test_the_nav_is_the_owners_and_every_item_is_a_built_page():
    assert nav_problems(B.NAV_ITEMS) == []
    # "your forecast" is the interactive page's own address, not a literal
    assert dict((lab, h) for h, lab in B.NAV_ITEMS)["your prediction"] == build_your_forecast.YF_HREF
    assert dict((lab, h) for h, lab in B.NAV_ITEMS)["source code"] == B.REPO_URL
    # the other direction: every reader-facing page of the model is in the nav
    in_nav = {h for h, _l in B.NAV_ITEMS}
    for page in ("forecast", "claims", "commentary", "methodology", "review",
                 "corrections", "sources"):
        assert page in in_nav, page
    html = B.nav_for("forecast")
    assert html.count('class="active"') == 1 and 'class="active" href="forecast"' in html


def test_the_nav_check_fires_on_each_constructed_violation():
    items = list(B.NAV_ITEMS)
    dead = [("about", "the model") if h == "methodology" else (h, l) for h, l in items]
    assert nav_problems(dead), "blind to a nav item pointing at a page nobody builds"
    assert nav_problems(items[1:]), "blind to a missing item"
    assert nav_problems(list(reversed(items))), "blind to the order"
    assert nav_problems(items) == []


# ---------------------------------------------------------------- cutting

TEMPLATE = """<head>
<!-- __ONLY:a_START__ -->
<meta name="a">
<!-- __ONLY:a_END__ -->
</head>
SHARED
<!-- __ONLY:b_START__ -->
B ONLY
<!-- __ONLY:b_END__ -->
<!-- __ONLY:a,b_START__ -->
A AND B
<!-- __ONLY:a,b_END__ -->
"""


def test_cut_spans_keeps_its_own_spans_and_nothing_else():
    a, b = B.cut_spans(TEMPLATE, "a"), B.cut_spans(TEMPLATE, "b")
    assert '<meta name="a">' in a and "A AND B" in a and "B ONLY" not in a
    assert "B ONLY" in b and "A AND B" in b and '<meta name="a">' not in b
    for page in (a, b, B.cut_spans(TEMPLATE, None)):
        assert "SHARED" in page and "__ONLY" not in page
    every = B.cut_spans(TEMPLATE, None)
    assert all(s in every for s in ('<meta name="a">', "B ONLY", "A AND B"))


def test_cut_spans_refuses_a_template_it_cannot_cut_safely():
    for bad, key in ((TEMPLATE.replace("<!-- __ONLY:b_END__ -->\n", ""), "a"),
                     (TEMPLATE.replace("<!-- __ONLY:a,b_START__ -->",
                                       "<!-- __ONLY:a,b_START__ -->\n<!-- __ONLY:b_START__ -->"), "a"),
                     (TEMPLATE.replace("<!-- __ONLY:a_END__ -->", "<!-- __ONLY:b_END__ -->"), "a"),
                     (TEMPLATE, "c")):
        try:
            B.cut_spans(bad, key)
        except SystemExit:
            continue
        raise AssertionError(f"cut_spans accepted a template it cannot cut ({key!r})")


def test_every_sheet_span_reaches_a_built_page_and_back():
    """Both directions: every key a span names is a page in ARTEFACTS, and
    every ARTEFACTS page cut from the sheet has spans of its own."""
    raw = SHEET.read_text(encoding="utf-8")
    keys = {k for m in re.finditer(r"<!-- __ONLY:([a-z0-9,-]+)_START__ -->", raw)
            for k in m.group(1).split(",")}
    cut_keys = {key for src, key, *_r in B.ARTEFACTS.values() if src == SHEET.name}
    assert 6 <= len(cut_keys) <= 20, cut_keys
    assert keys == cut_keys, (keys ^ cut_keys)
    assert {f"{k}.html" for k in cut_keys} == {out for out, (src, *_r) in B.ARTEFACTS.items()
                                               if src == SHEET.name}


def test_each_page_holds_its_own_content_only():
    pages = _sheet_pages()
    articles = {out for out, spec in B.ARTEFACTS.items() if spec[3] == "commentary"}
    heads = {out: _ids(pages[out]) & {"the-november-surprise", "nobody-catches",
                                      "minority", "other-pr", "laingsburg"}
             for out in pages}
    assert heads["nobody-will-win.html"] == {"the-november-surprise"}
    assert heads["nobody-catches-the-votes.html"] == {"nobody-catches"}
    assert heads["minority-administrations.html"] == {"minority"}
    assert heads["if-the-law-were-german.html"] == {"other-pr"}
    assert heads["laingsburg-2021.html"] == {"laingsburg"}
    for out in ("forecast.html", "claims.html", "commentary.html"):
        assert not heads[out], (out, heads[out])
    # the claims are on /claims and nowhere else; the forecast is on /forecast
    for out, html in pages.items():
        assert ('<article class="claim ' in html) == (out == "claims.html"), out
        assert ('id="coalitions"' in html) == (out == "forecast.html"), out
        assert ("<!-- __COMMENTARY__ -->" in html) == (out == "commentary.html"), out
        assert html.count("<h1") == 1, (out, html.count("<h1"))
        # the sheet's colophon and dateline describe the forecast's figures
        assert ('class="colophon"' in html) == (out == "forecast.html"), out
        assert ('class="dateline"' in html) == (out == "forecast.html"), out
    assert len(articles) == 5


# ---------------------------------------------------------------- commentary

def test_commentary_lists_exactly_the_article_pages():
    """articles.toml -> the article pages, and back. The index is written by
    the home page's own function, so the two lists cannot differ."""
    listed = [a["href"] for a in tomllib.loads(ARTICLES.read_text(encoding="utf-8"))["article"]]
    articles = {out.removesuffix(".html") for out, spec in B.ARTEFACTS.items()
                if spec[3] == "commentary"}
    assert sorted(h.split("#")[0] for h in listed) == sorted(articles), (listed, articles)
    assert not [h for h in listed if "#" in h], "an article still points into another page"
    page = B.fill_commentary(_sheet_pages()["commentary.html"], "joburg")
    hrefs = re.findall(r'<div class="t"><a href="([^"]+)">', page)
    assert sorted(hrefs) == sorted(listed)
    assert "<!-- __COMMENTARY__ -->" not in page
    # every entry is a dated passage, so a figure in a standfirst reads as history
    assert page.count('data-asof="') >= len(listed)


def _heads() -> dict[str, tuple[str, str]]:
    """Each cut page's <title> and share-card meta, as the build sets them."""
    articles = B.article_meta("joburg")
    pages = _sheet_pages()
    return {out: B.artefact_head(out, B.ARTEFACTS[out], html, articles, plain=_plain)
            for out, html in pages.items()}


def _plain(text: str) -> str:
    """The build's share-card renderer over the registry. Every token a
    standfirst may hold is fixed, so no simulation output is needed."""
    import stats as S
    return B.plain_tokens(text, S.load_registry(ROOT / "content/joburg/stats.toml"), {})


def _card(og_meta: str, prop: str) -> str:
    m = re.search(rf'<meta property="og:{prop}" content="([^"]*)">', og_meta)
    return unescape(m.group(1)) if m else ""


def test_each_article_page_is_titled_and_carded_from_its_list_entry():
    """articles.toml -> each article page's <title>, og:title and
    og:description, and every page but the home page has its own address."""
    listed = B.article_meta("joburg")
    heads = _heads()
    assert 4 <= len(listed) <= 12 and set(listed) <= set(heads), (listed, heads)
    for out, a in listed.items():
        title, og = heads[out]
        assert unescape(title) == a["title"], (out, title)
        assert _card(og, "title") == a["title"], out
        assert _card(og, "description") == " ".join(_plain(a["standfirst"]).split()), out
        assert "{{" not in _card(og, "description") and "<span" not in og, out
    urls = {out: _card(og, "url") for out, (_t, og) in heads.items()}
    assert len(set(urls.values())) == len(urls), urls
    for out, (_t, og) in heads.items():
        slug = out.removesuffix(".html")
        assert urls[out] == f"{B.SITE_URL}/{slug}", (out, urls[out])
        assert f'<link rel="canonical" href="{B.SITE_URL}/{slug}">' in og, out
    # the home page alone keeps the site-wide card at the root
    _t, og = B.artefact_head("index.html", B.ARTEFACTS["index.html"],
                             "<title>x</title>", listed)
    assert og == B.OG_META


def test_the_head_refuses_a_second_title_or_a_missing_card():
    articles = B.article_meta("joburg")
    pages = _sheet_pages()
    out = "laingsburg-2021.html"
    src, cut, _t, active, _og = B.ARTEFACTS[out]
    for spec in ((src, cut, "Laingsburg", active, None),
                 (src, cut, None, active, "A typed card.")):
        try:
            B.artefact_head(out, spec, pages[out], articles)
        except SystemExit:
            continue
        raise AssertionError(f"an article's head was typed twice: {spec}")
    src, cut, title, active, _og = B.ARTEFACTS["claims.html"]
    try:
        B.artefact_head("claims.html", (src, cut, title, active, None),
                        pages["claims.html"], articles)
    except SystemExit:
        pass
    else:
        raise AssertionError("a page with no card of its own was given the home page's")
    # quiet on the specs as they stand
    for out, html in pages.items():
        B.artefact_head(out, B.ARTEFACTS[out], html, articles, plain=_plain)


def test_fill_commentary_refuses_two_markers_and_leaves_other_pages_alone():
    assert B.fill_commentary("<p>x</p>", "joburg") == "<p>x</p>"
    try:
        B.fill_commentary("<!-- __COMMENTARY__ --><!-- __COMMENTARY__ -->", "joburg")
    except SystemExit:
        pass
    else:
        raise AssertionError("two article lists on one page were accepted")


# ---------------------------------------------------------------- old anchors

def _forward_map(html: str) -> tuple[dict[str, str], str | None]:
    m = re.search(r'<script defer src="js/forward.js"([^>]*)></script>', html)
    if not m:
        return {}, None
    attrs = dict(re.findall(r'(data-[a-z]+)="([^"]*)"', m.group(1)))
    pairs = dict(p.split(":", 1) for p in attrs.get("data-map", "").split() if ":" in p)
    return pairs, attrs.get("data-to")


def anchor_problems(pages: dict[str, str], old: dict[str, set[str]]) -> list[str]:
    """Every id an old page carried still lands: on the page itself, or by its
    forward map (followed through data-to) on a page that holds it."""
    out = []
    for page, ids in old.items():
        for i in sorted(ids):
            seen, here = set(), page
            while here not in seen:
                seen.add(here)
                html = pages.get(here, "")
                if i in _ids(html):
                    break
                pairs, to = _forward_map(html)
                nxt = pairs.get(i) or to
                if not nxt:
                    out.append(f"{page}#{i}: lost at {here}")
                    break
                here = nxt + ".html"
            else:
                out.append(f"{page}#{i}: forwards in a loop")
    return out


def _old_ids(page: str) -> set[str]:
    run = subprocess.run(["git", "show", f"{BEFORE_SPLIT}:site/{page}"], cwd=ROOT,
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    # pattern ids inside the map's <defs> are not anchors anyone links to
    return {i for i in _ids(run.stdout) if not i.startswith(("h_", "hx_"))}


def test_every_old_article_and_claims_anchor_still_lands():
    old = {"nobody-will-win.html": _old_ids("nobody-will-win.html"),
           "forecast.html": {"claims"} & _old_ids("forecast.html")}
    assert {"the-november-surprise", "nobody-catches", "minority", "other-pr",
            "laingsburg"} <= old["nobody-will-win.html"], old
    assert old["forecast.html"] == {"claims"}
    pages = _sheet_pages()
    assert anchor_problems(pages, old) == []


def test_the_anchor_check_fires_when_a_forward_is_lost():
    old = {"nobody-will-win.html": {"minority", "the-november-surprise"},
           "forecast.html": {"claims"}}
    pages = _sheet_pages()
    broken = dict(pages)
    broken["nobody-will-win.html"] = pages["nobody-will-win.html"].replace(
        " minority:minority-administrations", "")
    assert anchor_problems(broken, old), "blind to a dropped forward"
    broken = dict(pages)
    broken["claims.html"] = pages["claims.html"].replace('id="claims"', 'id="claimz"')
    assert anchor_problems(broken, old), "blind to the target losing its id"
    assert anchor_problems(pages, old) == []


# ---------------------------------------------------------------- /about

def test_about_is_part_of_methodology():
    assert "about.html" not in {spec[0] for spec in B.DOCS.values()}
    method = (ROOT / "docs-public" / "methodology.md").read_text(encoding="utf-8")
    assert method.count(B.VALIDATION_MARKER) == 1
    assert method.count("## How accurate is it?") == 1
    # no page links to the page that no longer exists
    linking = [p.name for p in (ROOT / "docs-public").glob("*.md")
               if re.search(r"\]\(about[)#]", p.read_text(encoding="utf-8"))]
    linking += [p for p in ("home.html", "forecast-sheet.html")
                if 'href="about' in (ROOT / p).read_text(encoding="utf-8")]
    assert not linking, linking
    html = B.render_doc(ROOT / "docs-public" / "methodology.md", "Methodology", "",
                        "methodology.html")
    assert html.count("<!-- __VALIDATION_START__ -->") == 1
    assert 'id="how-accurate-is-it"' in html     # the home page's link lands
    assert 'href="methodology#how-accurate-is-it"' in (ROOT / "home.html").read_text(encoding="utf-8")


def test_validation_is_refused_without_its_generator_marker():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        typed = Path(t) / "about.md"
        typed.write_text("### Scores\n\nThe model wins in 7 of 8 cities.\n", encoding="utf-8")
        try:
            B.validation_html(typed)
        except SystemExit:
            pass
        else:
            raise AssertionError("a hand-typed validation was exempted as script-made")
        made = Path(t) / "made.md"
        made.write_text("<!-- GENERATED by src/build_validation.py. x -->\n\n"
                        "### Scores\n\n7 of 8.\n", encoding="utf-8")
        html = B.validation_html(made)
        assert html.startswith("<!-- __VALIDATION_START__ -->")
        import stats
        hits = stats.scan_numbers(f"<p>x</p>{html}")
        assert hits and all(h["region"].startswith("generated:VALIDATION") for h in hits)
        assert not any(stats.is_blocking(h) for h in hits)
        # the same figures typed into prose would block
        assert any(stats.is_blocking(h) for h in stats.scan_numbers("<p>7 of 8.</p>"))


def test_a_document_cannot_type_a_script_made_region():
    """Markdown passes HTML comments through, so a hand-written document that
    typed a generated-region marker round a sentence would exempt its figures.
    `render_doc` refuses every such marker; without the markers the same
    sentence renders and its figure blocks."""
    import stats
    import tempfile
    sentence = "The ANC will win 61% of wards."
    wrapped = f"<!-- __VALIDATION_START__ -->\n{sentence}\n<!-- __VALIDATION_END__ -->"
    # what the guard prevents: the scan exempts the wrapped figure
    assert any(stats.is_blocking(h) for h in stats.scan_numbers(f"<p>{sentence}</p>"))
    assert not any(stats.is_blocking(h) for h in stats.scan_numbers(f"<p>{wrapped}</p>"))
    assert len(stats.GENERATED_MARKERS) >= 5
    with tempfile.TemporaryDirectory() as t:
        doc = Path(t) / "note.md"
        for name in sorted(stats.GENERATED_MARKERS):
            for body in (wrapped.replace("VALIDATION", name),
                         f"{sentence}\n<!-- __{name}_END__ -->"):
                doc.write_text(f"# Note\n\n{body}\n", encoding="utf-8")
                try:
                    B.render_doc(doc, "Note", "", "note.html", tech=False)
                except SystemExit:
                    continue
                raise AssertionError(f"a typed __{name}__ marker was accepted")
        # a marker that is not script-made, and no marker, both render
        for body in (sentence, f"<!-- __JUDGEMENTS_START__ -->\n{sentence}\n"
                               "<!-- __JUDGEMENTS_END__ -->"):
            doc.write_text(f"# Note\n\n{body}\n", encoding="utf-8")
            html = B.render_doc(doc, "Note", "", "note.html", tech=False)
            assert any(stats.is_blocking(h) for h in stats.scan_numbers(html))
    # every published document is free of them
    docs = sorted((ROOT / "docs-public").glob("*.md"))
    assert len(docs) >= 5
    assert [d.name for d in docs if B.typed_generated_markers(d.read_text(encoding="utf-8"))] == []


def test_figure_tables_marks_tables_of_figures_only():
    figures = B._md_html("| party | won | out by |\n|---|---|---|\n"
                         "| A | **91** | -14 |\n| B | 7 | |\n")
    words = B._md_html("| baseline | what it does |\n|---|---|\n| last | repeats 2021 |\n")
    mixed = B._md_html("| city | seats |\n|---|---|\n| X | 270 |\n| Y | n/a |\n")
    assert B.figure_tables(figures).count('<table class="figures">') == 1
    assert 'class="figures"' not in B.figure_tables(words)
    assert 'class="figures"' not in B.figure_tables(mixed)
    assert "style=" not in B.figure_tables(figures)
    # The validation section marks its figure tables and leaves its tables of
    # words alone. Constructed since 2026-10-23: the live section is the
    # withdrawal notice and holds no table
    # (audits/2026-10-23-site-sweep/BRIEF-step0-withdraw-scores.md).
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        made = Path(d) / "about.md"
        made.write_text("<!-- GENERATED by src/build_validation.py. x -->\n\n"
                        "| party | won | out by |\n|---|---|---|\n| A | 91 | -14 |\n\n"
                        "| baseline | what it does |\n|---|---|\n| last | repeats 2021 |\n",
                        encoding="utf-8")
        html = B.validation_html(made)
    assert html.count('<table class="figures">') == 1 and html.count("<table") == 2, html


def test_a_heading_id_carries_no_token_name():
    html = B._md_html("### 8. Do it {{n_draws}} times\n")
    assert 'id="8-do-it-times"' in html, html
    assert 'id="how-accurate-is-it"' in B._md_html("## How accurate is it?\n")


# ---------------------------------------------------------------- footer

def footer_problems(footer: str) -> list[str]:
    out = []
    credits = re.search(r'<p class="foot-credits">(.*?)</p>', footer, re.S)
    indep = re.search(r'<div class="foot-independence">\s*<p>(.*?)</p>', footer, re.S)
    if not credits or _text(credits.group(1)) != FOOTER_CREDITS:
        out.append("the credits block is not the owner's wording")
    if not indep or _text(indep.group(1)) != FOOTER_INDEPENDENCE:
        out.append("the independence block is not the owner's wording")
    if not re.search(r'<hr class="foot-rule">\s*<div class="foot-independence">', footer):
        out.append("no rule between the two blocks")
    if not re.search(r'<a class="foot-support" href="support">Support Our Work</a>', footer):
        out.append("no Support Our Work link to /support")
    for page in ("support", "privacy"):
        if f'href="{page}"' not in footer:
            out.append(f"{page} is not linked relatively")
    return out


def test_the_footer_is_the_owners():
    assert footer_problems(B.FOOTER) == []
    assert B.FOOTER == B.footer_for()


def test_the_footer_check_fires_on_each_constructed_violation():
    f = B.FOOTER
    for old, new in (("distributed", "distribute"),
                     ("independent", "indpendant"),
                     ('<hr class="foot-rule">', ""),
                     ('<a class="foot-support" href="support">', '<a class="x" href="support">'),
                     ('href="privacy"', 'href="https://whysoserious.city/privacy"'),
                     ("Municipal Demarcation Board", "MDB")):
        assert f.count(old) == 1, old
        assert footer_problems(f.replace(old, new)), f"blind to {new!r}"


def footer_layout_problems(footer: str, css: str) -> list[str]:
    """Owner, 2026-10-13: the text (credits, rule, independence statement) in
    one column at the left; the logo with "Support Our Work" beneath it at the
    right; one column at phone width."""
    out = []
    text = re.search(r'<div class="foot-text">(.*?)</div>\s*</div>\s*<div class="foot-side">(.*?)</div>\s*</footer>', footer, re.S)
    if not text:
        return ["no .foot-text column followed by .foot-side"]
    left, right = text.groups()
    if not (left.index('class="foot-credits"') < left.index('class="foot-rule"') < left.index('class="foot-independence"')):
        out.append("the text column is not the credits, the rule, the independence statement")
    if 'class="foot-umbrella"' in left or 'class="foot-support"' in left:
        out.append("the logo or the support link is in the text column")
    if not (right.find('class="foot-umbrella"') != -1 and right.find('class="foot-umbrella"') < right.find('class="foot-support"')):
        out.append("the side column is not the logo, then Support Our Work")
    flat = re.sub(r"\s+", "", css)
    if "grid-template-columns:minmax(0,1fr)auto" not in flat:
        out.append("the footer is not a text column and a logo column")
    if not re.search(r"@media\(max-width:760px\)\{\.sitefooter\{grid-template-columns:minmax\(0,1fr\)", flat):
        out.append("the footer does not stack at phone width")
    return out


def test_the_footer_is_one_text_column_with_the_logo_over_support_at_the_right():
    import site_assets as SA
    css = (SA.CSS_SRC / "chrome.css").read_text(encoding="utf-8")
    assert footer_layout_problems(B.FOOTER, css) == []
    f = B.FOOTER
    swapped = f.replace('<div class="foot-side">', '<div class="foot-side"><a class="foot-support" href="support">Support Our Work</a>', 1)
    assert footer_layout_problems(swapped, css)
    assert footer_layout_problems(f, css.replace("minmax(0,1fr) auto", "repeat(2,minmax(0,1fr))"))
    assert footer_layout_problems(f.replace('<div class="foot-text">', '<div>', 1), css)


def test_every_built_page_carries_the_footer_once():
    """The committed site/: every page at any depth, counted against what the
    build produces, carries the footer exactly once."""
    site = ROOT / "site"
    pages = sorted(site.rglob("*.html"))
    root_pages = {p.name for p in pages if p.parent == site}
    assert root_pages == _produced(), root_pages ^ _produced()
    assert len(_produced()) + 1 <= len(pages) <= len(_produced()) + 6, len(pages)
    for p in pages:
        html = p.read_text(encoding="utf-8")
        foot = re.findall(r'<footer class="sitefooter">.*?</footer>', html, re.S)
        assert len(foot) == 1, (p, len(foot))
        if p.parent == site:
            assert foot[0] == B.FOOTER, p
        else:  # /your-forecast/: the same footer re-pointed one level down
            assert foot[0] == build_play.one_level_down(B.FOOTER), p


# ---------------------------------------------------------------- strapline

STRAPLINE = ("Made for the benefit of all the residents, businesses, professional "
             "and civic organisations and political parties that make our city so "
             "interesting.")
#: the apex portal is the only built page with no city nav, so no strapline
NO_NAV = {"portal.html"}


def strapline_problems(html: str) -> list[str]:
    """The owner's strapline, once, directly under the nav bar."""
    out = []
    if _text(html).count(STRAPLINE) != 1:
        out.append(f"the strapline appears {_text(html).count(STRAPLINE)} times")
    if not re.search(r'</nav>\s*<p class="strapline">' + re.escape(STRAPLINE) + "</p>", html):
        out.append("the strapline is not directly under the nav")
    return out


def test_the_strapline_is_the_owners_and_sits_under_the_nav():
    assert B.STRAPLINE == STRAPLINE
    assert strapline_problems(B.nav_for("forecast")) == []


def test_the_strapline_check_fires_on_each_constructed_violation():
    nav = B.nav_for("forecast")
    assert strapline_problems(nav.replace("</nav>\n", "</nav>\n<p>x</p>"))
    assert strapline_problems(nav.replace("so interesting", "very interesting"))
    assert strapline_problems(nav + "<p>" + STRAPLINE + "</p>")
    assert strapline_problems(nav.split("<p class")[0])


def test_the_strapline_has_one_definition():
    """No page template types it: nav_for is its only source."""
    for f in (ROOT / "home.html", SHEET, ROOT / "interactive" / "your-forecast.html"):
        assert STRAPLINE not in _text(f.read_text(encoding="utf-8")), f


def test_every_built_page_with_the_nav_carries_the_strapline_once():
    site = ROOT / "site"
    pages = sorted(site.rglob("*.html"))
    assert len(_produced()) + 1 <= len(pages) <= len(_produced()) + 6, len(pages)
    seen = 0
    for p in pages:
        html = p.read_text(encoding="utf-8")
        if p.name in NO_NAV and p.parent == site:
            assert 'class="topnav"' not in html and STRAPLINE not in html, p
            continue
        assert html.count('<nav class="topnav">') == 1, p
        assert strapline_problems(html) == [], (p, strapline_problems(html))
        seen += 1
    assert seen == len(pages) - len(NO_NAV), seen


# ---------------------------------------------------------------- claims

def claim_colour_problems(html: str, css: str, codes) -> list[str]:
    """Every claim wears its own party's colour class and nothing else picks
    a party: the claims stylesheet reads --pc and names no party."""
    out = []
    # the claim's anchor (`id`) follows `data-party` since the claim cards
    # (2026-10-13); it is optional so a claim without one is still read
    arts = re.findall(r'<article class="claim([^"]*)" data-party="([^"]+)"(?: id="[^"]*")?>', html)
    if not arts:
        out.append("no claims")
    for classes, party in arts:
        if classes.split() != [f"pc-{party}"]:
            out.append(f"{party}: classes {classes!r}")
    if html.count('<article class="claim') != len(arts):
        out.append("a claim without its party")
    for code in codes:
        if re.search(rf"\b{re.escape(code)}\b", css):
            out.append(f"page-claims.css names {code}")
    return out


def test_every_claim_wears_its_own_partys_colour_and_none_is_singled_out():
    import render_sheet
    import site_assets as SA
    html = (ROOT / "site" / "claims.html").read_text(encoding="utf-8")
    css = re.sub(r"/\*.*?\*/", "", (SA.CSS_SRC / "page-claims.css").read_text(encoding="utf-8"), flags=re.S)
    codes = list(render_sheet.CHIPS)
    assert claim_colour_problems(html, css, codes) == []
    assert '<body class="pg-claims ' in html
    # it can see: a claim in another party's colour, one with none, a party named
    one = re.search(r'<article class="claim pc-(\w+)" data-party="\1"(?: id="[^"]*")?>', html)
    assert one
    wrong = "OTHER" if one.group(1) != "OTHER" else "DA"
    assert claim_colour_problems(html.replace(one.group(0), one.group(0).replace(f"pc-{one.group(1)}", f"pc-{wrong}"), 1), css, codes)
    assert claim_colour_problems(html.replace(one.group(0), f'<article class="claim" data-party="{one.group(1)}">', 1), css, codes)
    assert claim_colour_problems(html, css + ".claim.pc-ANC{border-width:9px}", codes)


def verdict_problems(html: str, step_of) -> list[str]:
    """Every claim's badge carries the class its verdict's step names, and
    nothing else picks its colour."""
    out = []
    badges = re.findall(r'<article class="claim pc-(\w+)" data-party="\1"(?: id="[^"]*")?>.*?'
                        r'<span class="verdict ([^"]*)">([^<]+)</span>', html, re.S)
    if not badges:
        out.append("no verdict badges")
    for party, classes, text in badges:
        want = step_of(text)
        if classes.split() != [want]:
            out.append(f"{party} {text!r}: classes {classes!r}, wanted {want!r}")
    if html.count('<span class="verdict') != len(badges):
        out.append("a verdict badge outside a claim")
    return out


def test_every_verdict_takes_its_step_on_the_one_scale_whatever_the_party():
    """Owner, 2026-10-05: the badge's colour is the verdict's, red false to
    grey open to green true, one scale for every party. Every verdict in
    claims.toml is on the scale; the mapping reads the verdict string and
    nothing else; the built page carries it; the stylesheet colours every
    step from a token in both palettes."""
    import inspect
    import tomllib
    import render_sheet as RS
    import site_assets as SA
    claims = tomllib.loads((ROOT / "content" / "joburg" / "claims.toml").read_text(encoding="utf-8"))["claim"]
    assert claims
    steps = set(RS.VERDICT_STEPS)
    assert set(RS.VERDICT_STEP.values()) == steps
    for c in claims:
        assert RS.verdict_class(c["verdict"]) in {f"v-{s}" for s in steps}, c["verdict"]
    # party-independent: the class is a function of the verdict string alone
    assert list(inspect.signature(RS.verdict_class).parameters) == ["verdict"]
    # the ends and the middle are where the owner put them
    assert RS.verdict_class("FALSE") == "v-false" and RS.verdict_class("TRUE") == "v-true"
    assert RS.verdict_class("COIN FLIP") == "v-open"
    assert RS.verdict_class("near  impossible") == "v-false"
    # it can see: a verdict off the scale stops the build, not a default colour
    try:
        RS.verdict_class("PROBABLY")
    except SystemExit:
        pass
    else:
        raise AssertionError("an unknown verdict took a colour")
    # the built page
    html = (ROOT / "site" / "claims.html").read_text(encoding="utf-8")
    assert verdict_problems(html, RS.verdict_class) == []
    one = re.search(r'<span class="verdict (v-\w+)">', html)
    assert one
    wrong = "v-true" if one.group(1) != "v-true" else "v-false"
    assert verdict_problems(html.replace(one.group(0), f'<span class="verdict {wrong}">', 1), RS.verdict_class)
    assert verdict_problems(html.replace(one.group(0), '<span class="verdict vfalse">', 1), RS.verdict_class)
    # every step has a rule reading its token, once, in the shared stylesheet
    # that /claims and the home page's claims list both take it from
    # (2026-10-06), and the token is in both palettes
    uncomment = lambda name: re.sub(r"/\*.*?\*/", "", (SA.CSS_SRC / name).read_text(encoding="utf-8"), flags=re.S)
    shared, css = uncomment("components.css"), uncomment("page-claims.css")
    tokens = (SA.CSS_SRC / "tokens.css").read_text(encoding="utf-8")
    dark = re.search(r":root\{color-scheme:dark;(.*?)\}", tokens, re.S).group(1)
    light = re.search(r':root\[data-theme="light"\]\{(.*?)\}', tokens, re.S).group(1)
    for s in steps:
        assert f".v-{s}{{--v:var(--v-{s});}}" in shared, s
        assert f".v-{s}{{" not in css, f"a second definition of the {s} step"
        assert f"--v-{s}:" in dark and f"--v-{s}:" in light, s
    assert "var(--c)" not in re.search(r"\.verdict\{[^}]*\}", css).group(0)


def test_the_chance_scale_puts_each_edge_on_the_side_nearer_a_coin_flip():
    """Owner, 2026-10-07: under 1% NEAR IMPOSSIBLE, 1-15% EXTREMELY UNLIKELY,
    15-45% QUITE UNLIKELY, 45-55% COIN FLIP, 55-75% QUITE LIKELY, 75-90% VERY
    LIKELY, over 90% NEAR CERTAIN. The documented edge rule: a chance exactly
    on an edge takes the band nearer a coin flip. Each edge is tested on, just
    under and just over (as printed: 1.0% / 0.9% / 1.1%, 15% / 14% / 16%)."""
    import render_sheet as RS
    cases = [
        (0.0, "NEAR IMPOSSIBLE"), (0.0002, "NEAR IMPOSSIBLE"),
        (0.009, "NEAR IMPOSSIBLE"), (0.01, "EXTREMELY UNLIKELY"), (0.011, "EXTREMELY UNLIKELY"),
        (0.14, "EXTREMELY UNLIKELY"), (0.15, "QUITE UNLIKELY"), (0.16, "QUITE UNLIKELY"),
        (0.44, "QUITE UNLIKELY"), (0.45, "COIN FLIP"), (0.46, "COIN FLIP"),
        (0.54, "COIN FLIP"), (0.55, "COIN FLIP"), (0.56, "QUITE LIKELY"),
        (0.74, "QUITE LIKELY"), (0.75, "QUITE LIKELY"), (0.76, "VERY LIKELY"),
        (0.89, "VERY LIKELY"), (0.90, "VERY LIKELY"), (0.91, "NEAR CERTAIN"),
        (0.999, "NEAR CERTAIN"), (1.0, "NEAR CERTAIN"),
        # judged as printed: 14.96% prints "15%", 0.996% prints "1.0%"
        (0.1496, "QUITE UNLIKELY"), (0.00996, "EXTREMELY UNLIKELY"),
    ]
    for p, want in cases:
        assert RS.scale_verdict(p) == want, (p, RS.scale_verdict(p), want)
    # every word on the scale is reached, and every one has a colour step
    assert {w for _e, w, _s in RS.CHANCE_SCALE} == {w for _p, w in cases}
    assert set(RS.VERDICT_STEP) == set(RS.SETTLED_VERDICTS) | {w for _e, w, _s in RS.CHANCE_SCALE}
    # the retired words are off the scale, so a stale label stops the build
    # (UNLIKELY and A COIN FLIP retired 2026-10-10 for the badges' words)
    for old in ("OUT OF REACH", "VERY UNLIKELY", "MORE LIKELY THAN NOT", "LIKELY", "UNLIKELY", "A COIN FLIP"):
        assert old not in RS.VERDICT_STEP, old


def test_a_verdict_that_disagrees_with_its_chance_is_refused():
    import render_sheet as RS
    vals = {"x": 0.30, "y": 0.86}
    why = "arithmetic, set out in the claim's steps"
    ok = [{"verdict": "QUITE UNLIKELY", "chance": "x"},
          {"verdict": "EXTREMELY UNLIKELY", "chance": "1 - y"},
          {"verdict": "FALSE", "settled": why},
          {"verdict": "TRUE", "settled": why}]
    for c in ok:
        assert RS.verdict_fault(c, vals) is None, c
    bad = [{"verdict": "QUITE LIKELY", "chance": "x"},          # wrong word
           {"verdict": "QUITE UNLIKELY", "chance": "1 - y"},           # complement ignored
           {"verdict": "NEAR CERTAIN", "chance": "y"},           # one band too far
           {"verdict": "QUITE UNLIKELY"},                              # no chance named
           {"verdict": "FALSE", "chance": "x", "settled": why},  # settled, yet rated
           {"verdict": "FALSE"},                                 # relabelled, no reason
           {"verdict": "TRUE", "settled": "yes"},                # a reason too short
           {"verdict": "PROBABLY", "chance": "x"}]               # off the scale
    for c in bad:
        assert RS.verdict_fault(c, vals), c
    # the form-only check (the home page's) sees the same structural faults
    assert RS.verdict_fault({"verdict": "FALSE"}, None)
    assert RS.verdict_fault({"verdict": "QUITE UNLIKELY"}, None)
    assert RS.verdict_fault({"verdict": "QUITE UNLIKELY", "chance": "x"}, None) is None
    # stops the build, not a TypeError: an unknown name, or a typed number
    for c in ({"verdict": "QUITE UNLIKELY", "chance": "nope"},
              {"verdict": "QUITE UNLIKELY", "chance": 0.3}):
        try:
            RS.verdict_fault(c, vals)
        except SystemExit:
            continue
        raise AssertionError(f"accepted: {c}")
    try:
        RS.claims_faults([{"verdict": "FALSE", "label": "z"}])
    except SystemExit:
        pass
    else:
        raise AssertionError("claims_faults let a reasonless FALSE through")


def test_the_holds_sentence_follows_the_verdict():
    """Owner, 2026-10-07: "Mashaba is very likely correct" is generated from
    the verdict, so it cannot outlive a verdict that moved; and text written
    only for the likely end (requires_at_least) is refused below it."""
    import render_sheet as RS
    words = {w for _e, w, _s in RS.CHANCE_SCALE} | set(RS.SETTLED_VERDICTS)
    assert set(RS.HOLDS) == words == set(RS.VERDICT_ORDER)
    want = {
        "NEAR CERTAIN": "Mashaba is almost certainly correct.",
        "VERY LIKELY": "Mashaba is very likely correct.",
        "QUITE LIKELY": "Mashaba is probably correct.",
        "COIN FLIP": "Mashaba is as likely right as wrong.",
        "QUITE UNLIKELY": "Mashaba is probably wrong.",
        "EXTREMELY UNLIKELY": "Mashaba is very likely wrong.",
        "NEAR IMPOSSIBLE": "Mashaba is almost certainly wrong.",
        "TRUE": "Mashaba is correct.",
        "FALSE": "Mashaba is wrong.",
    }
    c = {"holds_subject": "Mashaba", "label": "m"}
    for v, sentence in want.items():
        assert RS.holds_sentence(dict(c, verdict=v)) == sentence, v
    assert (RS.with_holds(dict(c, verdict="VERY LIKELY"), "**All told, [[holds]]** X")
            == "**All told, Mashaba is very likely correct.** X")
    assert RS.with_holds({"verdict": "QUITE UNLIKELY"}, "no placeholder") == "no placeholder"
    try:
        RS.with_holds({"verdict": "VERY LIKELY", "label": "m"}, "[[holds]]")
    except SystemExit:
        pass
    else:
        raise AssertionError("[[holds]] with no subject was accepted")
    # requires_at_least: at and above the floor passes; one step below is
    # refused, chance-rated or settled; a floor that is not a verdict is refused
    vals = {"x": 0.30, "y": 0.62, "z": 0.80}
    floor = {"requires_at_least": "QUITE LIKELY", "label": "m"}
    assert RS.verdict_fault(dict(floor, verdict="QUITE LIKELY", chance="y"), vals) is None
    assert RS.verdict_fault(dict(floor, verdict="VERY LIKELY", chance="z"), vals) is None
    assert RS.verdict_fault(dict(floor, verdict="QUITE UNLIKELY", chance="x"), vals)
    assert RS.verdict_fault(dict(floor, verdict="QUITE UNLIKELY", chance="x"), None)
    assert RS.verdict_fault(dict(floor, verdict="FALSE", settled="arithmetic, in the steps"), vals)
    assert RS.verdict_fault(dict(floor, verdict="TRUE", settled="arithmetic, in the steps"), vals) is None
    assert RS.verdict_fault({"verdict": "QUITE LIKELY", "chance": "y",
                             "requires_at_least": "PROBABLY"}, vals)
    # the live Mashaba claim carries the floor
    claims = tomllib.loads((ROOT / "content" / "joburg" / "claims.toml")
                           .read_text(encoding="utf-8"))["claim"]
    mashaba = [k for k in claims if k.get("holds_subject") == "Mashaba"]
    assert len(mashaba) == 1 and mashaba[0].get("requires_at_least") == "QUITE LIKELY"


def test_the_mashaba_coalitions_need_the_da_to_lead_and_count_every_party():
    """Owner, 2026-10-07: a realistic DA-led win is DA+ASA+PA or DA+ANC at the
    threshold with the DA strictly larger than each partner. The context
    figure adds every party outside the ANC, the EFF and MK that is smaller
    than the DA to DA+ASA+PA, and counts how many of those small parties,
    largest first, it needs. Constructed: threshold 11, three simulations,
    one Soweto ward."""
    import numpy as np
    import render_sheet as RS
    seats = {"DA": np.array([6, 6, 8]), "ASA": np.array([3, 5, 2]),
             "PA": np.array([1, 1, 1]), "ANC": np.array([5, 7, 1]),
             "EFF": np.array([2, 1, 4]), "X": np.array([2, 0, 4]),
             "Y": np.array([1, 0, 9])}
    thr = np.array([11, 11, 11])
    rows = [{"draw": "0"}, {"draw": "1"}, {"draw": "2"}]
    winners = {0: {"7": "ANC"}, 1: {"7": "DA"}, 2: {"7": "ANC"}}
    c = RS.da_coalitions(seats, thr, rows, winners, [7])
    # 0: DA+ASA+PA = 10 < 11; DA+ANC = 11, DA 6 > 5 -> ANC route only
    # 1: DA+ASA+PA = 12, DA 6 > 5 and > 1 -> yes; ANC 7 > DA -> no
    # 2: DA+ASA+PA = 11 -> yes; DA+ANC = 9 -> no
    assert list(c["partners.ASA+PA"]) == [False, True, True]
    assert list(c["partners.ANC"]) == [True, False, False]
    assert list(c["realistic"]) == [True, True, True]
    # with small parties (not the ANC; only those smaller than the DA):
    # 0: 10 + X 2 + Y 1 = 13, needs X only -> 1
    # 1: 12 already -> 0;  2: 11 already -> 0 (Y's 9 is not smaller than the
    # DA's 8, so Y is not a partner there)
    assert list(c["da_small"]) == [True, True, True]
    assert list(c["small_needed"]) == [1, 0, 0]
    assert list(c["none"]) == [True, False, True]
    # a DA no larger than ActionSA leads nothing with it, small parties or not
    seats["ASA"] = np.array([6, 6, 8])
    c = RS.da_coalitions(seats, thr, rows, winners, [7])
    assert list(c["partners.ASA+PA"]) == [False, False, False]
    assert list(c["da_small"]) == [False, False, False]
    assert list(c["small_needed"]) == [-1, -1, -1]
    # a Soweto ward missing from ward_draws.csv stops the build
    try:
        RS.da_coalitions(seats, thr, rows, winners, [7, 8])
    except SystemExit:
        pass
    else:
        raise AssertionError("a missing ward column was accepted")


def test_every_live_claim_passes_the_chance_scale_when_the_sheet_is_regenerated():
    """Every claim in claims.toml is either settled (FALSE/TRUE) or names its
    chance, and the build accepts every verdict: render_sheet regenerates a
    scratch copy of the sheet from today's simulations, and a disagreement
    stops it with a non-zero exit."""
    import shutil
    import tempfile
    import render_sheet as RS
    claims = tomllib.loads((ROOT / "content" / "joburg" / "claims.toml")
                           .read_text(encoding="utf-8"))["claim"]
    rated = [c for c in claims if c["verdict"] not in RS.SETTLED_VERDICTS]
    assert rated and all(c.get("chance") for c in rated), [c["label"] for c in rated]
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "forecast-sheet.html"
        shutil.copy(SHEET, copy)
        r = subprocess.run([str(ROOT / ".venv/bin/python"), str(ROOT / "src" / "render_sheet.py"),
                            "--sheet", str(copy)], capture_output=True, text=True, cwd=ROOT)
        assert r.returncode == 0, r.stdout[-800:] + r.stderr[-800:]



# -- one entry schema (guard G13, audits/2026-10-07-prediction-restructure) ----

#: Code that may name the retired placeholder ``worker-api/generated/
#: forecast.schema.json``, and why. Anything else naming it is a second schema
#: coming back.
SCHEMA_NAMERS = {
    "src/build_make.py": "its docstring records the retirement",
    "worker-api/src/forecasts.js": "its import comment records the retirement",
    "worker-api/tools/make_schema.mjs": "its header records the retirement",
    "worker-api/test/node/build.test.js": "asserts the file is absent",
    "tests/test_site_structure.py": "this guard",
}
#: The JavaScript modules that import a JSON file holding the entry schema: the
#: page's data file, whose ``schema`` the build writes (build_make).
SCHEMA_IMPORTERS = {"worker-api/src/forecasts.js", "worker-api/test/helpers.js",
                    "worker-api/test/node/consent-screen.test.js"}
_CODE = ("*.js", "*.mjs", "*.py", "*.json", "*.jsonc", "*.toml", "*.html")


def _tracked_code() -> list[str]:
    out = subprocess.run(["git", "ls-files", "--", *_CODE], cwd=ROOT, capture_output=True,
                         text=True, check=True).stdout.split()
    # a tracked file deleted in the working tree (not yet committed) is not code
    return [f for f in out if not f.startswith(("site/", "audits/")) and "/node_modules/" not in f
            and (ROOT / f).is_file()]


def schema_problems(files: dict[str, str]) -> list[str]:
    """Every way a second entry schema could exist, as sentences."""
    out = []
    named = {f for f, text in files.items() if "forecast.schema.json" in text}
    if named != set(SCHEMA_NAMERS):
        out.append(f"files naming forecast.schema.json: {sorted(named ^ set(SCHEMA_NAMERS))} "
                   f"differ from the declared list, one way or the other")
    imports = {f: re.findall(r'^import \w+ from "([^"]+\.json)"', text, re.M) for f, text in files.items()
               if f.endswith((".js", ".mjs"))}
    schemas = {f for f, paths in imports.items() if any(p.endswith("forecast.json") or "schema" in p for p in paths)}
    if schemas != SCHEMA_IMPORTERS:
        out.append(f"modules importing a schema file: {sorted(schemas ^ SCHEMA_IMPORTERS)} differ from the declared list")
    if (ROOT / "worker-api" / "generated" / "forecast.schema.json").exists():
        out.append("the retired placeholder schema exists again")
    return out


def test_one_entry_schema():
    files = {f: (ROOT / f).read_text(encoding="utf-8", errors="replace") for f in _tracked_code()}
    # it looked: the population is the repository's code, and holds the declared files
    assert len(files) > 100 and set(SCHEMA_NAMERS) | SCHEMA_IMPORTERS <= set(files), len(files)
    assert schema_problems(files) == []
    # it can see, both ways, and goes quiet again
    extra = dict(files, **{"interactive/js/x.js": 'fetch("../worker-api/generated/forecast.schema.json")'})
    assert schema_problems(extra)
    second = dict(files, **{"interactive/js/y.js": 'import s from "../fixtures/entry.schema.json";'})
    assert schema_problems(second)
    lost = {f: t for f, t in files.items() if f != "worker-api/test/helpers.js"}
    assert schema_problems(lost)
    assert schema_problems(files) == []

if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
