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
import build_site as B  # noqa: E402

SHEET = ROOT / "forecast-sheet.html"
ARTICLES = ROOT / "content" / "joburg" / "articles.toml"
#: The last commit before the sweep split the article off: the ids a shared
#: link to /nobody-will-win or /forecast could carry.
BEFORE_SPLIT = "a912197"

#: The owner's nav, in order (sweep of 2026-10-03, item 9).
NAV = ["our forecast", "your forecast", "commentary", "party claims tested",
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
        if href == build_play.PLAY_HREF:
            continue
        if href not in produced:
            out.append(f"nav item {label!r} -> {href!r}, a page this build does not produce")
    return out


def test_the_nav_is_the_owners_and_every_item_is_a_built_page():
    assert nav_problems(B.NAV_ITEMS) == []
    # "your forecast" is the interactive page's own address, not a literal
    assert dict((lab, h) for h, lab in B.NAV_ITEMS)["your forecast"] == build_play.PLAY_HREF
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
        assert ('<article class="claim"' in html) == (out == "claims.html"), out
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
    return {out: B.artefact_head(out, B.ARTEFACTS[out], html, articles)
            for out, html in pages.items()}


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
        assert _card(og, "description") == " ".join(a["standfirst"].split()), out
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
        B.artefact_head(out, B.ARTEFACTS[out], html, articles)


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
    html = B.validation_html()
    assert 4 <= html.count('<table class="figures">') <= html.count("<table") - 1


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
                     ('class="foot-support"', 'class="x"'),
                     ('href="privacy"', 'href="https://whysoserious.city/privacy"'),
                     ("Municipal Demarcation Board", "MDB")):
        assert f.count(old) == 1, old
        assert footer_problems(f.replace(old, new)), f"blind to {new!r}"


def test_every_built_page_carries_the_footer_once():
    """The committed site/: every page at any depth, counted against what the
    build produces, carries the footer exactly once."""
    site = ROOT / "site"
    pages = sorted(site.rglob("*.html"))
    root_pages = {p.name for p in pages if p.parent == site}
    assert root_pages == _produced(), root_pages ^ _produced()
    assert len(_produced()) + 2 <= len(pages) <= len(_produced()) + 6, len(pages)
    for p in pages:
        html = p.read_text(encoding="utf-8")
        foot = re.findall(r'<footer class="sitefooter">.*?</footer>', html, re.S)
        assert len(foot) == 1, (p, len(foot))
        if p.parent == site:
            assert foot[0] == B.FOOTER, p
        else:  # /play/, /make/: the same footer re-pointed one level down
            assert foot[0] == build_play.one_level_down(B.FOOTER), p


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
