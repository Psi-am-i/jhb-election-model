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


def test_a_fixed_fact_must_contain_the_occurrence_not_sit_near_it():
    fixed = [{"value": "23%", "context": "laingsburg"}]
    assert _one("<p>the DA 23% forecast; see laingsburg</p>", fixed=fixed)[0][3] == "unreviewed"
    fixed = [{"value": "23%", "context": "on just 23% of the vote"}]
    assert _one("<p>three wards on just 23% of the vote</p>", fixed=fixed)[1][3] == "fixed"


def test_a_legacy_allow_entry_never_excuses_a_date():
    hits = _one("<p>Laingsburg is fine. The ANC will get 44% on 1 November 2026.</p>",
                allow=["Laingsburg"])
    assert ("date", "1 November 2026", "prose", "unreviewed") in hits, hits


def test_deploy_check_refuses_a_stale_review_and_unreviewed_numbers(tmp=None):
    import hashlib
    import tempfile
    import deploy_check as D
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        site = tmp / "site"
        site.mkdir()
        (site / "index.html").write_text("<p>page</p>")
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
    ):
        found = S.script_writes(bad)
        assert found and found[0].startswith(what), (bad, found)
