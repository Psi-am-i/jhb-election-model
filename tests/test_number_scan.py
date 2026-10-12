"""`stats.scan_numbers` — every number a reader can see is a token, a registered
fixed fact, or flagged for review.

Owner, 2026-09-17: "even when we type in by hand, we should be able to scrape
things that look like numbers ... and flag them for tracking and manual review."
The audit it replaces excused a list of bare numbers (0-12, 50, 100, 135, 136,
270, election years), which is how "just 7 seats" reached the live page wrong.

Every input here is CONSTRUCTED, so nothing depends on what the site says today.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import build_site  # noqa: E402
import stats as S  # noqa: E402

PAGE = (
    "<p>Note the ANC's list bar: just 7 seats. The DA won 23% in Laingsburg on "
    "6 August 2026, three of four wards, back in 2021.</p>"
    '<span class="mstat" data-token="x">55%</span>'
    "<script>const GEN = {n: 999};</script>"
    "<!-- __MAP_START__ --><div>Ward 12 · safe DA — DA over 99%</div><!-- __MAP_END__ -->"
)


def _hits(**kw):
    return S.scan_numbers(PAGE, **kw)


def test_it_sees_every_kind_and_the_population_is_what_the_page_holds():
    hits = _hits()
    prose = [(h["kind"], h["value"]) for h in hits if h["region"] == "prose"]
    # The whole population, both directions: nothing missed, nothing invented.
    assert sorted(prose) == sorted([
        ("num", "7"), ("num", "23%"), ("date", "6 August 2026"),
        ("word", "three"), ("wnum", "four"), ("year", "2021")]), prose


def test_the_small_number_the_old_whitelist_excused_is_now_caught():
    numbers, _ = S.audit("<p>Note the ANC's list bar: just 7 seats.</p>")
    assert len(numbers) == 1 and "'7'" in numbers[0], numbers


def test_a_token_a_script_and_a_generated_region_are_not_prose():
    hits = _hits()
    values = {h["value"] for h in hits}
    assert "55%" not in values, "a token span was scanned as typed prose"
    assert "999" not in values, "script contents are not reader-visible"
    gen = [h for h in hits if h["region"] == "generated:MAP"]
    assert [h["value"] for h in gen] == ["12", "99%"], gen


def test_a_fixed_fact_clears_only_its_own_value_in_its_own_context():
    fixed = [{"value": "23%", "context": "won 23% in laingsburg"}]
    by_value = {h["value"]: h["status"] for h in _hits(fixed=fixed)}
    assert by_value["23%"] == "fixed"
    # the detector goes quiet only where registered: same context, other value
    assert by_value["7"] == "unreviewed"
    # and a registered value in the wrong context is not cleared
    other = S.scan_numbers("<p>ActionSA took 23% nationally.</p>", fixed=fixed)
    assert [h["status"] for h in other] == ["unreviewed"]


def test_only_prose_digits_dates_and_counting_words_block():
    numbers, _ = S.audit(PAGE)
    blocked = sorted(n.split("  ")[0] for n in numbers)
    # "three" stays review-only; "four wards" counts something, so it blocks
    assert blocked == sorted(["'7'", "'23%'", "'6 August 2026'", "'four'"]), blocked


# --- the holes a blind review found on 2026-09-17, each with its own input ---

def _one(html, **kw):
    return [(h["kind"], h["value"], h["region"], h["status"])
            for h in S.scan_numbers(html, **kw)]


def test_attribute_text_is_scanned():
    assert _one('<p title="ANC 41%">x</p>') == [("num", "41%", "prose:attr", "unreviewed")]


def test_a_number_glued_to_letters_is_still_a_number():
    assert [v for _, v, *_ in _one("<p>R1.2bn and ward7</p>")] == ["1.2", "7"]


def test_a_number_word_that_counts_something_blocks():
    numbers, _ = S.audit("<p>Note the ANC's list bar: just seven seats.</p>")
    assert len(numbers) == 1 and "'seven'" in numbers[0], numbers


def test_a_year_that_counts_votes_is_a_number():
    assert _one("<p>1998 votes higher</p>")[0][:2] == ("num", "1998")


def test_an_invented_marker_does_not_exempt_prose():
    html = "<!-- __ANYTHING_START__ --><p>44%</p><!-- __ANYTHING_END__ -->"
    assert _one(html)[0][2] == "prose"
    numbers, _ = S.audit(html)
    assert numbers, "a hand-typed marker exempted a number from the gate"


def test_only_the_exact_footnote_marker_is_chrome():
    """A footnote marker counts nothing; a class merely NAMED "fn" exempts
    nothing (code review, 2026-10-02: ``\\bfn\\b`` matched "pl-fn" and
    "fn-wrap" and cleared every figure inside them)."""
    marker = '<p>Turnout moves.<sup class="fn"><a href="#note-turnout">2</a></sup></p>'
    assert [(v, r) for _, v, r, _ in _one(marker)] == [("2", "prose:chrome")]
    assert not S.audit(marker)[0]
    for html in ('<p class="fn">The DA wins 71 seats.</p>',
                 '<p class="pl-fn">The DA wins 71 seats.</p>',
                 '<div class="note fn-wrap">The DA wins 71 seats.</div>',
                 '<sup class="fn">71</sup>',
                 '<sup class="fn"><a href="#note-x">71 seats</a></sup>'):
        numbers, _ = S.audit(html)
        assert numbers and "'71'" in numbers[0], (html, numbers)
    # and the marker shape is what clears it: the same digit outside it blocks
    assert S.audit('<p>Turnout moves 2.</p>')[0]


def test_a_fixed_fact_must_contain_the_occurrence_not_sit_near_it():
    fixed = [{"value": "23%", "context": "laingsburg"}]
    assert _one("<p>the DA 23% forecast; see laingsburg</p>", fixed=fixed)[0][3] == "unreviewed"
    fixed = [{"value": "23%", "context": "on just 23% of the vote"}]
    assert _one("<p>three wards on just 23% of the vote</p>", fixed=fixed)[1][3] == "fixed"


def test_an_allow_phrase_excuses_no_number_at_all():
    """An `[[audit.allow]]` phrase excuses a claim in words. It used to clear
    any "NN%" within sixty characters of it, which is how ActionSA's 18% and
    Laingsburg's 23% went unregistered (owner's sweep, 2026-10-03)."""
    html = "<p>Laingsburg is fine. The ANC will get 44% on 1 November 2026.</p>"
    numbers, _ = S.audit(html, allow=["Laingsburg"])
    assert sorted(n.split("  ")[0] for n in numbers) == ["'1 November 2026'", "'44%'"], numbers


def test_deploy_check_refuses_a_stale_review_and_unreviewed_numbers(tmp=None):
    import hashlib
    import tempfile
    import deploy_check as D
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        site = tmp / "site"
        site.mkdir()
        (site / "index.html").write_text("<p>page</p>")
        (site / "_headers").write_text(build_site.headers_text())   # the gate checks it
        sha = hashlib.sha256((site / "index.html").read_bytes()).hexdigest()
        review = tmp / "NUMBERS-REVIEW.md"

        def write(blocking, rows):
            review.write_text(f"# x\n<!-- built-pages: index.html={sha} blocking={blocking} -->\n"
                              + "".join(f"| BLOCKS | num | prose | `7` | … |\n" for _ in range(rows)))
        write(0, 0)
        assert D.check("joburg", site, preview=False, review=review) == []
        write(1, 1)
        assert D.check("joburg", site, preview=False, review=review), "unreviewed number shipped"
        assert D.check("joburg", site, preview=True, review=review) == [], "a preview is allowed"
        write(0, 1)
        assert any("edited by hand" in p for p in D.check("joburg", site, False, review=review))
        write(0, 0)
        (site / "index.html").write_text("<p>a different page</p>")
        assert any("not the page" in p for p in D.check("joburg", site, True, review=review)), (
            "an old review cleared a new build")


def test_a_page_script_may_not_carry_or_inject_figures():
    clean = ("<script>var t = e.target.getAttribute('data-tip'); tip.textContent = t;"
             " b.textContent = anyOpen ? 'expand all' : 'collapse all';</script>")
    assert S.script_writes(clean) == []
    for bad, what in (
        ('<script>const GEN = {"tiles": [1]};</script>', "a data block"),
        ("<script>el.innerHTML = rows;</script>", "HTML injection"),
        ("<script>el.textContent = `${p.med} seats`;</script>", "template interpolation"),
        ("<script>fetch('/x.json').then(r => r.json()).then(d => el.textContent = d.n);</script>",
         "a data source"),
    ):
        found = S.script_writes(bad)
        assert found and found[0].startswith(what), (bad, found)


# --- LIVE regions (owner's decision 1, 2026-09-30; SPEC-v2 Lane G) ------------
# A figure computed in the reader's browser may appear only inside an element
# marked `data-live="<name>"`, which must hold NO build-time digit. Every input
# is constructed; each check is shown to fire and to go quiet when reverted.

def _blocking(html, **kw):
    return [(h["value"], h["region"]) for h in S.scan_numbers(html, **kw)
            if S.is_blocking(h)]


def test_a_typed_digit_in_a_live_region_blocks_and_an_empty_one_does_not():
    outside = "<p>The page says just 7 seats.</p>"
    bad = outside + '<p>You get <output data-live="seats-da">41 seats</output>.</p>'
    ok = outside + '<p>You get <output data-live="seats-da"></output>.</p>'
    # scanned the right thing: the prose outside is still prose, both times
    assert sorted(_blocking(bad)) == [("41", "live:seats-da"), ("7", "prose")], _blocking(bad)
    assert _blocking(ok) == [("7", "prose")], _blocking(ok)
    numbers, _ = S.audit(bad)
    assert any("'41'" in n for n in numbers), numbers
    assert not any("'41'" in n for n in S.audit(ok)[0])


def test_nothing_clears_a_digit_inside_a_live_region():
    fixed = [{"value": "41", "context": "you get 41"}]
    token = ('<span class="mstat" data-mode="free" data-token="x" data-current="55%"'
             ' data-prov="Source: x">55%</span>')
    for inner, kw in (("You get 41", {"fixed": fixed}),
                      ("270 seats", {"structural": ["270"]}),
                      (token, {}),
                      ("<h3>Step 2</h3>", {}),
                      ('<span title="ANC 41%">x</span>', {})):
        page = f'<div data-live="mine">{inner}</div>'
        assert _blocking(page, **kw), f"a digit inside a LIVE region was cleared: {inner}"
        assert _blocking('<div data-live="mine"></div>', **kw) == []
    # and the same clearances still work outside a region
    assert _blocking("<p>You get 41</p>", fixed=fixed) == []
    assert _blocking(f"<p>{token}</p>") == []


def test_a_token_spans_own_data_live_is_not_a_region():
    """`stats._span` writes `data-live="<current value>"` on pinned tokens. That
    attribute must not turn every token into a LIVE region full of digits."""
    page = ('<p><span class="mstat" data-mode="fixed" data-token="x" data-live="5,000"'
            ' data-prov="Source: x">5,000</span> draws</p>')
    assert S._live_scan(page) == ([], [])
    assert _blocking(page) == []
    # the detector is not simply off: the same attribute on a non-token is a region
    assert S._live_scan('<p data-live="draws">5,000</p>')[0]


def test_a_malformed_live_marker_blocks():
    for bad in ('<div data-live="seats">never closed',
                '<div data-live="Seats 1">x</div>',
                '<div data-live="">x</div>',
                '<br data-live="seats"/>'):
        hits = S.scan_numbers("<p>ok</p>" + bad)
        assert any(h["kind"] == "malformed" and S.is_blocking(h) for h in hits), (bad, hits)
    assert not any(h["kind"] == "malformed"
                   for h in S.scan_numbers('<p>ok</p><div data-live="seats"></div>'))


def test_live_is_not_a_generated_marker_and_applies_on_every_page_kind():
    assert "LIVE" not in S.GENERATED_MARKERS
    page = '<div data-live="seats">12</div>'
    assert _blocking(page, generated_page=True) == [("12", "live:seats")]
    inside_map = f"<!-- __MAP_START__ -->{page}<!-- __MAP_END__ -->"
    assert _blocking(inside_map) == [("12", "live:seats")]
    dated = f'<section data-asof="2026-08-07">{page}</section>'
    assert _blocking(dated) == [("12", "live:seats")]
    assert _blocking('<section data-asof="2026-08-07"><div data-live="seats"></div></section>') == []


def _site(tmp, files):
    import textwrap
    for rel, body in files.items():
        f = tmp / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(textwrap.dedent(body))
    return tmp


def _writes(tmp, page="play/index.html", writers=None):
    return S.script_writes((tmp / page).read_text(), page=tmp / page, root=tmp,
                           writers=writers or {})


PAGE_LOADS = ('<div data-live="seats"></div>'
              '<script type="module" src="js/main.js"></script>')
WRITER = """
    import { draw } from "./engine.js";
    const out = document.querySelector('[data-live="seats"]');
    const res = await fetch("/draws/index.json");
    out.textContent = `${(await res.json()).n} seats`;
"""


def test_an_unlisted_module_writing_figures_is_blocked():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        tmp = _site(Path(t), {"play/index.html": PAGE_LOADS,
                              "play/js/main.js": WRITER,
                              "play/js/engine.js": "export function draw() { return 1; }\n"})
        found = _writes(tmp)
        kinds = {w.split(": ")[1] for w in found}
        assert {"a data source", "template interpolation"} <= kinds, found
        # listed, the same module is allowed
        assert _writes(tmp, writers={"play/js/main.js": frozenset({"seats"})}) == []
        # an inert module is quiet unlisted
        (tmp / "play/js/main.js").write_text("document.body.classList.add('js');\n")
        assert _writes(tmp) == []
        # a page given no path cannot have its scripts read, so it is refused
        assert S.script_writes(PAGE_LOADS), "an unread script passed"


def test_an_imported_module_is_read_too():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        tmp = _site(Path(t), {"play/index.html": PAGE_LOADS,
                              "play/js/main.js": 'import "./ui.js";\n',
                              "play/js/ui.js": "el.innerHTML = rows;\n"})
        found = _writes(tmp)
        assert found and found[0].startswith("play/js/ui.js: HTML injection"), found
        (tmp / "play/js/ui.js").write_text("el.classList.toggle('open');\n")
        assert _writes(tmp) == []
        (tmp / "play/js/main.js").write_text('import "./gone.js";\n')
        assert any("does not exist" in w for w in _writes(tmp))
        (tmp / "play/js/main.js").write_text('import x from "lodash";\n')
        assert any("bare module" in w for w in _writes(tmp))
        (tmp / "play/index.html").write_text('<script src="https://cdn.example/x.js"></script>')
        assert any("remote" in w for w in _writes(tmp))


def test_a_listed_module_may_write_only_into_its_live_regions():
    import tempfile
    listed = {"play/js/main.js": frozenset({"seats"})}
    with tempfile.TemporaryDirectory() as t:
        tmp = _site(Path(t), {"play/index.html": PAGE_LOADS,
                              "play/js/main.js": WRITER,
                              "play/js/engine.js": "export const k = 1;\n"})
        assert _writes(tmp, writers=listed) == []
        for escape, what in (
            ("document.querySelector('#headline').textContent = n;", "not a LIVE selector"),
            ("document.getElementById('seats').textContent = n;", "not a LIVE selector"),
            ("document.querySelector('[data-live=\"seats\"], p').textContent = n;",
             "not a LIVE selector"),
            ("document.querySelector('[data-live=\"seats\"]' + ', p').textContent = n;",
             "not a LIVE selector"),
            ("document.querySelector('[data-live=\"other\"]').textContent = n;", "not listed for"),
            ("out.parentNode.textContent = n;", "traversal out of the region"),
            ("out.after(n);", "insertion beside the region"),
            ("out.innerHTML = n;", "HTML injection"),
            ("document.title = n;", "a document-level handle"),
            ("e.target.textContent = n;", "a write through an event target"),
            ("import('./late.js');", "an import this check cannot follow"),
            # code review 2026-10-01: a combinator after the region selects
            # outside it, and `.form` / `document[...]` reach outside it too
            ("document.querySelector('[data-live=\"seats\"] ~ main p').textContent = n;",
             "not a LIVE selector"),
            ("document.querySelector('[data-live=\"seats\"] + p').textContent = n;",
             "not a LIVE selector"),
            ("document.querySelector('[data-live=\"seats\"] > p').textContent = n;",
             "not a LIVE selector"),
            ("out.form.textContent = n;", "traversal out of the region"),
            ("out.offsetParent.textContent = n;", "traversal out of the region"),
            ('document["body"].append(n);', "a document-level handle"),
        ):
            (tmp / "play/js/main.js").write_text(WRITER + escape + "\n")
            found = _writes(tmp, writers=listed)
            assert any(what in w for w in found), (escape, found)
            (tmp / "play/js/main.js").write_text(WRITER)
            assert _writes(tmp, writers=listed) == [], escape


def test_a_module_listed_for_no_region_may_hold_no_data_and_load_none():
    """A writer listed for NO region (play-card.js, the share image) draws
    figures only from the result it is handed: it is refused a data block and
    a data source as a non-writer is, while a writer with regions keeps the
    writer contract alone (code review 2026-10-01)."""
    import tempfile
    card = ("export function card(r) {\n"
            "  return `<text>${r.seats}</text>`;\n}\n")
    page = PAGE_LOADS
    with tempfile.TemporaryDirectory() as t:
        tmp = _site(Path(t), {"play/index.html": page,
                              "play/js/main.js": WRITER + 'import { card } from "./card.js";\n',
                              "play/js/engine.js": "export const k = 1;\n",
                              "play/js/card.js": card})
        listed = {"play/js/main.js": frozenset({"seats"}), "play/js/card.js": frozenset()}
        assert _writes(tmp, writers=listed) == []
        for extra, what in (("export const D = [412, 38];", "a data block"),
                            ('fetch("../draws/index.json");', "a data source"),
                            ('document["body"].append("97 seats");', "a document-level handle"),
                            ("document.querySelector('[data-live=\"seats\"] p').textContent = 1;",
                             "a LIVE region it is not listed for")):
            (tmp / "play/js/card.js").write_text(card + extra + "\n")
            found = _writes(tmp, writers=listed)
            assert any(w.startswith("play/js/card.js (LIVE writer): " + what) for w in found), (extra, found)
            (tmp / "play/js/card.js").write_text(card)
            assert _writes(tmp, writers=listed) == [], extra


def test_the_registry_names_served_modules_and_region_names():
    """`LIVE_WRITERS` maps a module's path under the site root to the LIVE
    region names it may write. Checked for every entry it holds, whatever that
    number is. An EMPTY set is allowed: a module that builds figures but
    reaches no region of the page (play-card.js, the share image) is held to
    the writer contract with nothing it may select; at least one entry must
    name regions, or no figure could reach a page at all."""
    assert isinstance(S.LIVE_WRITERS, dict)
    for rel, names in S.LIVE_WRITERS.items():
        assert not rel.startswith("/") and rel.endswith((".js", ".mjs")), rel
        assert isinstance(names, frozenset) and all(S.LIVE_NAME.match(n) for n in names), (rel, names)
    assert any(S.LIVE_WRITERS.values())


def test_deploy_check_scans_nested_pages():
    import hashlib
    import tempfile
    import deploy_check as D
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        site = tmp / "site"
        (site / "play").mkdir(parents=True)
        (site / "index.html").write_text("<p>page</p>")
        (site / "_headers").write_text(build_site.headers_text())   # the gate checks it
        (site / "play" / "index.html").write_text("<p>nested</p>")
        review = tmp / "NUMBERS-REVIEW.md"

        def sha(rel):
            return hashlib.sha256((site / rel).read_bytes()).hexdigest()

        review.write_text(f"<!-- built-pages: index.html={sha('index.html')} blocking=0 -->\n")
        found = D.check("joburg", site, preview=False, review=review)
        assert any("play/index.html" in p for p in found), found
        review.write_text(f"<!-- built-pages: index.html={sha('index.html')} "
                          f"play/index.html={sha('play/index.html')} blocking=0 -->\n")
        assert D.check("joburg", site, preview=False, review=review) == []
        (site / "play" / "index.html").write_text("<p>changed</p>")
        assert any("site/play/index.html is not the page" in p
                   for p in D.check("joburg", site, preview=False, review=review))


def test_the_analytics_beacon_is_the_only_remote_script_a_page_may_load():
    """Web Analytics (owner, 2026-09-30) is emitted only when a site token is
    set, and `script_writes` passes that exact tag and no other remote script."""
    import tempfile
    assert build_site.analytics_head("") == ""
    tag = build_site.analytics_head("0123456789abcdef0123456789abcdef")
    assert tag.count("<script") == 1 and S.ANALYTICS_BEACON in tag
    try:
        build_site.analytics_head("not-a-token")
    except SystemExit:
        pass
    else:
        raise AssertionError("a malformed site token was emitted")
    with tempfile.TemporaryDirectory() as t:
        tmp = _site(Path(t), {"index.html": tag})
        assert _writes(tmp, page="index.html") == []
        for other in (S.ANALYTICS_BEACON + "?x=1",
                      "https://static.cloudflareinsights.com/other.js"):
            (tmp / "index.html").write_text(f'<script defer src="{other}"></script>')
            assert any("remote" in w for w in _writes(tmp, page="index.html")), other
        # the beacon's URL does not excuse an inline body carried on the same tag
        (tmp / "index.html").write_text(
            f'<script src="{S.ANALYTICS_BEACON}">el.innerHTML = rows;</script>')
        assert _writes(tmp, page="index.html"), "an inline body rode on the beacon"


def test_the_policy_pages_ship_in_both_analytics_states():
    """/privacy and /support, and the footer line linking them, are published
    whether or not the Web Analytics token is set (final review, 2026-10-01).
    Only privacy.md's Web Analytics paragraph, and the beacon, follow the
    token. Both states are rendered, not just today's."""
    tok = "0123456789abcdef0123456789abcdef"
    policy = {"support.html", "privacy.html"}
    assert policy <= {spec[0] for spec in build_site.DOCS.values()}
    foot = build_site.footer_for()
    for page in ("support", "privacy"):
        assert f'href="{page}"' in foot and "whysoserious.city/" + page not in foot
    assert build_site.FOOTER == foot
    root = Path(build_site.__file__).parents[1]
    src = "docs-public/privacy.md"
    output, kicker, standfirst, tech, og = build_site.POLICY_DOCS[src]
    pages = {state: build_site.render_doc(root / src, kicker, standfirst, output,
                                          tech, og, token=t)
             for state, t in (("off", ""), ("on", tok))}
    for state, html in pages.items():
        assert "<!-- analytics" not in html and "<!-- /" not in html, state
        assert "Workers Logs" in html and "Information Regulator" in html, state
    assert "Cloudflare Web Analytics" in pages["on"]
    assert "Cloudflare Web Analytics" not in pages["off"]
    assert "no analytics script" in pages["off"]
    assert "no analytics script" not in pages["on"]
    assert build_site.analytics_head("") == "" and build_site.analytics_head(tok)


def test_analytics_blocks_fires_and_quiets():
    text = ("a\n<!-- analytics -->\nWITH\n<!-- /analytics -->\n"
            "<!-- no-analytics -->\nWITHOUT\n<!-- /no-analytics -->\nb\n")
    assert build_site.analytics_blocks(text, "x" * 32) == "a\nWITH\nb\n"
    assert build_site.analytics_blocks(text, "") == "a\nWITHOUT\nb\n"
    assert build_site.analytics_blocks("plain\n", "") == "plain\n"


def test_publish_refuses_while_the_privacy_owner_placeholder_is_present():
    """POPIA needs the responsible party's identity and address. `--publish`
    refuses while privacy.md carries the `OWNER:` line, before writing
    anything; a build without --publish is not stopped by it."""
    import tempfile
    filled = "## Who is responsible\n\nA. Person, 1 Some Street, Johannesburg.\n"
    placeholder = "## Who is responsible\n\nOWNER: legal name and physical address\n"
    assert build_site.publish_blockers(filled) == []
    assert build_site.publish_blockers(placeholder)
    # a mention of the word mid-line is not the placeholder
    assert build_site.publish_blockers("The OWNER: line was filled.\n") == []
    saved = build_site.PRIVACY_SOURCE
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        priv = tmp / "privacy.md"
        priv.write_text(placeholder, encoding="utf-8")
        out, ledger = tmp / "site", tmp / "ledger"
        build_site.PRIVACY_SOURCE = priv
        try:
            build_site.main(["--publish", "--out", str(out),
                             "--ledger-root", str(ledger)])
        except SystemExit as exc:
            assert "OWNER" in str(exc.code), exc.code
        else:
            raise AssertionError("--publish ran with the OWNER placeholder present")
        finally:
            build_site.PRIVACY_SOURCE = saved
        assert not out.exists() and not ledger.exists(), "the refusal wrote something"


def test_a_policy_page_carries_its_own_share_card_and_a_reader_note():
    """No maintainer colophon pointing at a GitHub record that does not exist,
    and a share card that describes the page rather than the forecast."""
    for source, spec in build_site.POLICY_DOCS.items():
        output, kicker, standfirst, tech, og = spec
        html = build_site.render_doc(Path(build_site.__file__).parents[1] / source,
                                     kicker, standfirst, output, tech, og)
        slug = output.removesuffix(".html")
        assert "Reader edition" not in html and "regenerate rather" not in html
        assert "describes how the site is run" in html
        assert f'<link rel="canonical" href="https://joburg.whysoserious.city/{slug}">' in html
        assert f'<meta property="og:url" content="https://joburg.whysoserious.city/{slug}">' in html
        assert html.count('property="og:description"') == 1
        assert "5,000 simulations" not in html and og.split(":")[0] in html
        assert not any(ch.isdigit() for ch in og.replace("2026", "")), og  # no model figure
