"""The publication ledger — attribution, not re-derivability.

⛔ THE DEFECT THESE TESTS EXIST FOR. The published page said the DA finishes
first **87%** of the time for ELEVEN DAYS after the model settled on 71%, and
nothing could contradict it: the figure looked live, its tooltip claimed to be
live, and no artefact recorded which run any published figure came from. Ten
further claims were pinned to `run:turnout_tilt_da=1`, a lever the model no
longer has, so they could not be re-derived at all.

The owner's ruling (MODEL-LOG §1.140) replaced the rule rather than the claims:
a published figure must be **attributable** — what it was, when it was true,
which run produced it — and need not be **re-derivable**, because re-derivability
is a property of the current model's outputs and is incoherent as a demand on
the past.

⚠️ These tests use the PRODUCTION registry and the PRODUCTION artefacts wherever
the property is about the real tree. This project was bitten by a scoring
function that raised on every input for its entire life because its only test
handed it a type production never builds (§1.136); a ledger tested only against
hand-built fixtures would inherit exactly that.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import publication as P  # noqa: E402
from _support import run_module, skip  # noqa: E402


def _row(**kw):
    base = dict(token="t", value=0.87, display="87%", fmt="pct0", source="s",
                model_run_id="r1", run_at="2026-08-17T00:00:00Z", as_of=None,
                published_at="2026-08-17T00:00:00Z", change_class=None,
                reason=None, movement="new")
    base.update(kw)
    return P.Row(**base)


def test_the_six_movements_a_reader_can_experience():
    """Classification is from the READER's side, not the model's.

    `rounding` is the one that matters and the one that is easy to get wrong: a
    raw move that leaves the displayed glyph identical is invisible, so it must
    not be marked inline — but it must still be RECORDED, which is why a row
    carries both `value` and `display`.
    """
    prev = _row()
    assert P.classify(None, 0.71, "71%", 3) == "new"
    assert P.classify(prev, 0.71, "71%", 3) == "material"
    assert P.classify(prev, 0.86, "86%", 3) == "minor"
    assert P.classify(prev, 0.8712, "87%", 3) == "rounding"
    assert P.classify(prev, 0.87, "87%", 3) == "none"


def test_a_string_change_is_nominal_and_case_matters():
    """"the ANC" -> "the DA" can invert the sentence around it, not adjust it.

    And case is significant: "the ANC" and "The ANC" read differently on the
    page, so the difference is one a reader should be told about. Whitespace is
    not — that is a typesetting artefact, not a change of meaning.
    """
    prev = _row(value="the ANC", display="the ANC", fmt="raw")
    assert P.classify(prev, "the DA", "the DA") == "nominal"
    assert P.classify(prev, "the  ANC", "the ANC") == "none"
    assert P.classify(prev, "The ANC", "The ANC") == "nominal"


def test_one_tolerance_means_the_same_thing_under_both_storage_conventions():
    """⛔ THE REGISTRY STORES THE SAME QUANTITY TWO WAYS, AND THIS RESOLVES IT.

        claim_da_share_surged   value = 41       (a percentage, as points)
        p_da_largest            resolves to 0.7122  (a percentage, as a fraction)

    Before `display_scale`, "tolerance = 3" meant three points against the first
    and three HUNDRED points against the second — so every move on a free
    percentage classified as `minor` and no reader would ever have been told a
    figure changed. A wrong answer with no symptom, which is this project's
    characteristic failure.

    **Tolerance is now always in DISPLAY units** — the number a person would say
    out loud. The same 3 must give the same verdict on the same real move,
    whichever way the token happens to be stored.
    """
    frac = _row(token="p_da_largest", value=0.87, display="87%", fmt="pct0")
    pts = _row(token="claim_da_share_surged", value=41, display="41", fmt=None)

    # a 16-point move, and a 1-2 point move, under both conventions
    assert P.classify(frac, 0.71, "71%", 3) == "material"
    assert P.classify(pts, 57, "57", 3) == "material"
    assert P.classify(frac, 0.86, "86%", 3) == "minor"
    assert P.classify(pts, 43, "43", 3) == "minor"

    # seats and votes are already in display units and must not be scaled
    seats = _row(token="claim_da_median", value=97, display="97", fmt=None)
    assert P.classify(seats, 93, "93", 3) == "material"
    assert P.classify(seats, 95, "95", 3) == "minor"


def test_a_tolerance_written_in_fraction_units_is_refused_not_obeyed():
    """The remaining trap points the other way, and it is loud rather than
    silent — but still wrong. `0.03` on a percentage token would make a tenth of
    one point a "material revision" reported to readers."""
    frac = _row(token="p_da_largest", value=0.87, display="87%", fmt="pct0")
    try:
        P.classify(frac, 0.71, "71%", 0.03)
    except ValueError as exc:
        assert "display units" in str(exc).lower(), exc
    else:
        raise AssertionError(
            "a fraction-unit tolerance was accepted on a percentage token; a "
            "0.1-point move would be published as a material revision.")


def test_the_ledger_is_append_only_and_round_trips():
    """A row is never rewritten. Ordering is by `published_at`, so a failed
    close-out write cannot corrupt the page."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        P.append("joburg", [_row(published_at="2026-08-07T00:00:00Z",
                                 display="62%", value=0.62)], root=root)
        P.append("joburg", [_row(published_at="2026-08-17T00:00:00Z",
                                 display="87%", value=0.87)], root=root)
        P.append("joburg", [_row(published_at="2026-08-28T00:00:00Z",
                                 display="71%", value=0.71)], root=root)
        rows = P.history("joburg", root=root)
        assert [r.display for r in rows] == ["62%", "87%", "71%"], rows
        assert P.latest("joburg", root=root)["t"].display == "71%"
        # appended out of order, still ordered by publication
        P.append("joburg", [_row(published_at="2026-08-10T00:00:00Z",
                                 display="70%", value=0.70)], root=root)
        assert [r.display for r in P.history("joburg", root=root)] == [
            "62%", "70%", "87%", "71%"]


def test_a_superseded_figure_may_not_be_published_in_live_present_tense():
    """⛔ THE SECOND CLAUSE. Without it, attribution is a licence.

    Recording which dead run produced a figure makes it AUDITABLE. It does not
    make it TRUE today. A superseded figure may appear only in a dated context —
    "as of 7 August the model said …" — and publishing one in live present tense
    is worse than the refusal the build has been issuing since 17 August.
    """
    ledger = {"claim_short_by": _row(token="claim_short_by", value=39,
                                     display="39", fmt=None,
                                     superseded_at="2026-08-28T00:00:00Z")}
    bad = P.dated_context_violations(
        [{"token": "claim_short_by", "dated": False}], ledger)
    assert len(bad) == 1 and bad[0]["token"] == "claim_short_by", bad
    assert "dated context" in bad[0]["why"]
    ok = P.dated_context_violations(
        [{"token": "claim_short_by", "dated": True}], ledger)
    assert ok == [], ok


def test_the_dated_context_check_can_actually_fire():
    """⛔ THE GUARD THAT COULD NOT FIRE — found in review, in this module's own
    first commit.

    `dated_context_violations` enforces the second clause of the attribution
    rule and the module docstring calls it "meant to be fatal". But NOTHING set
    `superseded_at`: `append` writes rows verbatim, `Row` is frozen, and
    `latest()` returns the last row per token, which by construction has
    `superseded_at=None`. So the check was structurally incapable of firing —
    the exact defect this project spent the same day cataloguing four times
    over, written into the module that catalogues it.

    `retire()` is the only thing that sets the stamp. This test exists to prove
    the guard can act, not merely that it returns a list.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        P.append("joburg", [_row(token="claim_short_by", value=39,
                                 display="39", fmt=None)], root=root)
        # before retirement the check is silent, correctly
        assert P.dated_context_violations(
            [{"token": "claim_short_by", "dated": False}],
            P.latest("joburg", root=root)) == []

        P.retire("joburg", "claim_short_by",
                 reason="measured under turnout_tilt_da, a lever run_model no "
                        "longer has; it cannot be re-derived",
                 change_class="mechanism", root=root)

        ledger = P.latest("joburg", root=root)
        assert ledger["claim_short_by"].superseded_at, ledger
        # and NOW it fires
        bad = P.dated_context_violations(
            [{"token": "claim_short_by", "dated": False}], ledger)
        assert len(bad) == 1, (
            "a retired figure published in live present tense was not caught. "
            "The second clause of the attribution rule is unenforced and the "
            "ledger is a licence to publish stale numbers with a footnote.")
        # a dated context is still allowed
        assert P.dated_context_violations(
            [{"token": "claim_short_by", "dated": True}], ledger) == []


def test_a_retirement_owes_the_reader_a_reason_and_cannot_happen_twice():
    """Two supersession stamps make 'when did this stop being current'
    unanswerable, and a retirement with no reason is the evasion the
    `change_class` field exists to prevent."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        P.append("joburg", [_row(token="t2")], root=root)
        for kwargs, why in (
                (dict(reason=""), "no reason"),
                (dict(reason="x", change_class="because"), "bad class")):
            try:
                P.retire("joburg", "t2", root=root, **kwargs)
            except ValueError:
                pass
            else:
                raise AssertionError(f"retirement accepted with {why}")
        P.retire("joburg", "t2", reason="mechanism deleted", root=root)
        try:
            P.retire("joburg", "t2", reason="again", root=root)
        except ValueError:
            pass
        else:
            raise AssertionError("a token was retired twice")
        try:
            P.retire("joburg", "never_published", reason="x", root=root)
        except KeyError:
            pass
        else:
            raise AssertionError("retired a token that was never published")


def test_an_unattributable_row_is_refused_and_the_batch_is_not_half_written():
    """⛔ APPEND-ONLY MEANS A BAD ROW IS PERMANENT, SO THE ONLY GUARD IS REFUSAL.

    The owner's standard is that a published figure need not be re-derivable but
    must be ATTRIBUTABLE: what it was, when that was, and which model produced
    it. A row with `model_run_id="r-unknown-…"` or no `run_at` fails the third
    and the second, and nothing downstream can ever repair it — the ledger does
    not rewrite.

    The second half matters as much as the first. Validation used to sit inside
    the open file handle, so a refusal on the third row of a batch left the
    first two written — a permanent partial publication of a batch that never
    happened. The whole batch is checked before the file is touched.
    """
    import tempfile as _tf
    with _tf.TemporaryDirectory() as tmp:
        root = Path(tmp)
        good = _row(token="a")
        for bad, why in [
            (_row(token="b", model_run_id="r-unknown-8249ea50"), "unknown run"),
            (_row(token="c", run_at=None), "no run time"),
            (_row(token="d", published_at=""), "no transaction time"),
        ]:
            try:
                P.append("joburg", [good, bad], root=root)
            except P.Unattributable:
                pass
            else:
                raise AssertionError(
                    f"a row with {why} was accepted. It is now permanent.")
            assert not (root / "joburg" / "ledger.jsonl").exists(), (
                f"the batch was refused for {why} but the good row before it "
                f"was already written. A half-published batch cannot be undone "
                f"in an append-only ledger.")

        assert P.append("joburg", [good], root=root) == 1


def test_run_identity_names_the_run_and_not_merely_the_date():
    """⛔ THIS TEST PASSED IN THE FAILURE STATE, AND THAT IS THE POINT OF IT.

    It asserted only `model_run_id.startswith("r-")` while the actual id was
    `r-unknown-8249ea50` — every row would have attributed the live forecast to
    a run called *unknown*, permanently, because the ledger is append-only.
    Caught in blind review 2026-08-31. **When a test's name states a property,
    it must assert the property.**

    A timestamp says WHEN, not WHAT. Two runs a minute apart on different code
    are different runs and a date cannot tell them apart, so the id is built
    from the code (`git_commit`), the inputs (`pool_artefact_keys`) and the
    output's own CONTENT — not from a file whose bytes now include a wall-clock
    stamp.
    """
    processed = Path("data/processed")
    if not (processed / "forecast_summary.json").is_file():
        skip("no forecast_summary.json to attribute")
    import cityconfig
    cityconfig.use("joburg")
    ident = P.run_identity(processed)

    assert "unknown" not in ident["model_run_id"], (
        f"the run id is {ident['model_run_id']!r}. A row carrying it would "
        f"attribute a published figure to a run nobody can find, and rows are "
        f"append-only, so it could never be corrected.")
    assert ident["git_commit"], (
        "no git commit recorded. Without it there is no route from a published "
        "figure back to the code that produced it, which is the whole of "
        "attribution.")
    assert ident["forecast_content_sha256"], ident
    assert "as_of" in ident and ident["as_of_is"], (
        "`as_of` is VALID time and is currently a stand-in for it. The label is "
        "load-bearing: it is what tells a future session that these rows were "
        "not measured.")


def test_the_run_id_is_stable_across_identical_forecasts():
    """⛔ THE ID MUST ANSWER 'DID THE FORECAST CHANGE', AND THE FIRST ONE COULD NOT.

    It hashed `forecast_summary.json`'s BYTES — and that file now carries its
    own wall-clock `_generated` stamp, so two byte-identical forecasts produced
    a minute apart got different ids. An identifier that changes when nothing
    changed cannot distinguish a re-publication from a re-estimation, which is
    exactly the distinction the bitemporal schema exists to make.

    So the content hash is taken over the summary with its `_`-prefixed stamps
    REMOVED.
    """
    import tempfile as _tf
    processed = Path("data/processed")
    if not (processed / "forecast_summary.json").is_file():
        skip("no forecast_summary.json to attribute")
    import cityconfig
    cityconfig.use("joburg")
    blob = json.loads((processed / "forecast_summary.json").read_text())

    with _tf.TemporaryDirectory() as tmp:
        a, b = Path(tmp) / "a", Path(tmp) / "b"
        a.mkdir(); b.mkdir()
        # identical forecasts, different run stamps
        (a / "forecast_summary.json").write_text(
            json.dumps({**blob, "_generated": "2026-08-31T01:00:00Z"}))
        (b / "forecast_summary.json").write_text(
            json.dumps({**blob, "_generated": "2026-08-31T01:01:00Z"}))
        ia, ib = P.run_identity(a), P.run_identity(b)
        # ⛔ ASSERT THE ID ITSELF, NOT ONLY THE HASH IT IS BUILT FROM.
        # This test shipped asserting three things about
        # `forecast_content_sha256` and NOTHING about `model_run_id` — so
        # reintroducing the original defect verbatim (an id built from the
        # wall-clock stamp) left it GREEN. Proven by mutation in blind review,
        # 2026-08-31. The property in the name is a property of the ID.
        assert ia["model_run_id"] == ib["model_run_id"], (
            f"two identical forecasts got different run ids: "
            f"{ia['model_run_id']} vs {ib['model_run_id']}. The id cannot "
            f"answer whether anything moved, which is the only question it "
            f"exists for.")
        assert ia["forecast_content_sha256"] == ib["forecast_content_sha256"], (
            "two identical forecasts hashed differently. The stamp is leaking "
            "into the content hash and the id cannot answer whether anything "
            "actually moved.")

        # and a forecast that DID change must get a different hash
        moved = {**blob}
        moved["structural"] = {**moved.get("structural", {}), "_probe": 1}
        c = Path(tmp) / "c"; c.mkdir()
        (c / "forecast_summary.json").write_text(json.dumps(moved))
        assert P.run_identity(c)["model_run_id"] != ia["model_run_id"], (
            "a changed forecast got the SAME run id as the unchanged one.")
        assert P.run_identity(c)["forecast_content_sha256"] != ia[
            "forecast_content_sha256"], (
            "a changed forecast hashed the same as the unchanged one; the "
            "content hash is not covering the content.")


def test_every_change_class_is_one_a_reader_can_act_on():
    """"the model moved" and "we were wrong" are different sentences, and a
    reader is entitled to have them distinguished. Without this field a bug fix
    and a re-estimate produce identical supersession rows."""
    assert set(P.CHANGE_CLASSES) == {
        "recompute", "data_revision", "mechanism", "bugfix"}


def test_the_summary_separates_what_a_reader_sees_from_what_moved():
    """The 'what changed' section needs both: the figures whose displayed value
    changed, and the count that moved by less than their published precision.
    Reporting only the first is the silent suppression this module forbids;
    reporting the second inline would train readers to ignore marks."""
    rows = [_row(token="a", movement="material"),
            _row(token="b", movement="minor"),
            _row(token="c", movement="rounding"),
            _row(token="d", movement="rounding"),
            _row(token="e", movement="none")]
    s = P.summarise(rows)
    assert s["n_visible"] == 2, s
    assert s["n_rounding"] == 2, s
    assert s["by_movement"]["material"] == ["a"], s


# --------------------------------------------------------------------------
# the wiring: what the renderer records, and what the build makes of it
# --------------------------------------------------------------------------

def _reg():
    return {"live": {"source": "model:p", "format": "pct0"},
            "old": {"source": "model:q", "format": "pct0"}}


def test_recording_what_was_published_changes_nothing_that_is_published():
    """⛔ AN OBSERVER THAT MOVES THE THING IT OBSERVES IS NOT A RECORD.

    `stats.render` grew a `record` parameter so the ledger could learn what
    each token resolved to — the raw value AND the displayed string, neither of
    which is recoverable from the rendered HTML. The whole point is void if
    turning it on changes a page: the ledger would then be recording a
    different document from the one the reader gets.

    This is the same contract `montecarlo.py --run-dir` holds and `test_chain`
    asserts for it, for the same reason.
    """
    import stats as S
    txt = ('<p>Live {{live}}.</p>'
           '<span data-asof="2026-08-07">As of 7 August, {{old}}.</span>')
    ctx = {"summary": {"p": 0.87, "q": 0.54}}
    plain, _, _ = S.render(txt, _reg(), ctx)
    rec: list = []
    watched, _, _ = S.render(txt, _reg(), ctx, record=rec)
    assert plain == watched, (
        "recording changed the rendered page. The ledger would be describing a "
        "document the reader never saw.")
    assert len(rec) == 2 and {r["token"] for r in rec} == {"live", "old"}


def test_a_dated_context_is_declared_by_the_sentence_not_sniffed_from_it():
    """⛔ THE REFUSAL IT FEEDS IS FATAL, SO GUESSING HERE FAILS BOTH WAYS.

    `publication.dated_context_violations` refuses to publish a SUPERSEDED
    figure in live present tense, while allowing the same figure as history —
    "as of 7 August the model said the DA would be short by 39 seats". Only the
    sentence knows which it is. A regex hunting for a date near the token would
    fail OPEN on prose it cannot parse (publishing a dead number as current)
    and CLOSED on prose that is fine, and it would do both silently.

    So the author encloses the sentence in `data-asof`, and the dating is
    recorded PER OCCURRENCE — the same token is live on the forecast page and
    historical in a retrospective, which a registry-level flag could not tell
    apart. That per-occurrence behaviour is what this asserts: one token, two
    places, two answers.
    """
    import stats as S
    reg = {"t": {"source": "model:p", "format": "pct0"}}
    txt = ('<p>The model says {{t}}.</p>'
           '<div data-asof="2026-08-07">In August it said {{t}}.</div>')
    rec: list = []
    S.render(txt, reg, {"summary": {"p": 0.87}}, record=rec)
    assert [r["dated"] for r in rec] == [False, True], (
        f"dating came out as {[r['dated'] for r in rec]}. It must follow the "
        f"enclosing sentence, not the token, or one page's history licenses "
        f"another page's stale present tense.")


def test_one_token_on_three_pages_is_one_published_figure():
    """A token is resolved ONCE per build; the pages are where it appeared.

    Writing a row per occurrence would triple-count every headline figure in
    the history and make "what did we publish for this token" return three
    identical rows with the same stamp — noise that a reader and a reviewer
    both have to filter before they can see the actual sequence of values.
    """
    import build_site as B
    occ = [{"token": "t", "value": 0.87, "display": "87%", "fmt": "pct0",
            "source": "model:p", "mode": "free", "tolerance": None,
            "dated": False, "page": p}
           for p in ("index.html", "methodology.html", "review.html")]
    ident = {"model_run_id": "r-abc-1234", "run_at": "2026-08-31T00:00:00Z",
             "as_of": "2026-08-31T00:00:00Z"}
    rows, changes = B._ledger_candidates(occ, {}, ident, "2026-08-31T01:00:00Z",
                                         reason=None, change_class=None)
    assert len(rows) == 1 and len(changes) == 1, (
        f"{len(rows)} rows for one token on three pages.")
    assert changes[0]["pages"] == ["index.html", "methodology.html",
                                   "review.html"], changes[0]["pages"]


def test_one_token_rendering_as_two_values_is_a_refusal_not_a_choice():
    """⛔ IF THE PAGE SHOWS TWO NUMBERS, THE LEDGER CANNOT SAY WHICH WAS PUBLISHED.

    Picking the first, the last, or the majority would each be a silent answer
    to a question the build has no standing to answer — and would record one
    figure while a reader was shown another. It is a renderer bug and it stops
    the build.
    """
    import build_site as B
    occ = [{"token": "t", "value": 0.87, "display": "87%", "fmt": "pct0",
            "source": "model:p", "mode": "free", "tolerance": None,
            "dated": False, "page": "index.html"},
           {"token": "t", "value": 0.62, "display": "62%", "fmt": "pct0",
            "source": "model:p", "mode": "free", "tolerance": None,
            "dated": False, "page": "review.html"}]
    ident = {"model_run_id": "r-abc-1234", "run_at": "2026-08-31T00:00:00Z",
             "as_of": "2026-08-31T00:00:00Z"}
    try:
        B._ledger_candidates(occ, {}, ident, "2026-08-31T01:00:00Z",
                             reason=None, change_class=None)
    except SystemExit as exc:
        assert "87%" in str(exc) and "62%" in str(exc), (
            f"the refusal must name both values a reader could have seen; it "
            f"said: {exc}")
    else:
        raise AssertionError(
            "two values for one token were reconciled silently. The ledger now "
            "records a figure that was not on the page.")


def test_a_row_that_did_not_move_carries_no_reason_and_one_that_did_must():
    """"Why did this change" must not be answerable for something that didn't.

    Stamping the batch's reason onto every unchanged token would fill the
    history with rows claiming a mechanism change explained a figure that never
    moved — and the reader's "what changed" section is built from exactly these
    rows.
    """
    import build_site as B
    prev = _row(token="same", value=0.87, display="87%", fmt="pct0")
    occ = [{"token": "same", "value": 0.87, "display": "87%", "fmt": "pct0",
            "source": "model:p", "mode": "free", "tolerance": None,
            "dated": False, "page": "index.html"},
           {"token": "moved", "value": 0.62, "display": "62%", "fmt": "pct0",
            "source": "model:q", "mode": "free", "tolerance": None,
            "dated": False, "page": "index.html"}]
    ident = {"model_run_id": "r-abc-1234", "run_at": "2026-08-31T00:00:00Z",
             "as_of": "2026-08-31T00:00:00Z"}
    rows, _ = B._ledger_candidates(occ, {"same": prev}, ident,
                                   "2026-08-31T01:00:00Z",
                                   reason="re-ran the model",
                                   change_class="recompute")
    by = {r.token: r for r in rows}
    assert by["same"].movement == "none"
    assert by["same"].reason is None and by["same"].change_class is None, (
        "an unchanged token was given the batch's reason. Its history now "
        "claims an explanation for a move that never happened.")
    assert by["moved"].movement == "new"
    assert by["moved"].reason == "re-ran the model"


# --------------------------------------------------------------------------
# END TO END: the ledger block inside build_site.main(), which the unit tests
# above cannot reach
# --------------------------------------------------------------------------

def _build(tmp, *extra):
    """Run the real build into a throwaway site and a throwaway ledger."""
    import subprocess
    root = Path(__file__).resolve().parents[1]
    return subprocess.run(
        [str(root / ".venv/bin/python"), str(root / "src/build_site.py"),
         "--out", str(tmp / "site"), "--ledger-root", str(tmp / "led"),
         # The tree's live orphaned claims and stale source file are a REAL and
         # separate refusal (§1.142). They stop the build before it ever
         # reaches the ledger, which is exactly why this test exists — and why
         # it must step past them rather than be deleted.
         "--allow-orphans", "--allow-stale-sources", *extra],
        capture_output=True, text=True, cwd=root)


def test_the_ledger_block_in_the_real_build_actually_executes():
    """⛔ THE WIRING HAD NO TEST, AND DELETING IT WOULD HAVE FAILED NOTHING.

    Every other test in this file calls `_ledger_candidates` directly with
    hand-built dicts. That proves the function; it proves nothing about whether
    `main()` ever calls it — and `main()` raises `SystemExit(1)` at the orphan
    and stale-source refusals well ABOVE the ledger block, so on this tree the
    whole wired path ran zero times. Found in blind review, 2026-08-31.

    This is the fixture-of-the-wrong-shape defect one level up: the unit tests
    were right about the unit and silent about the integration. The suite stayed
    green while the feature was unreachable — the same shape as
    `arrival_group_score`, which raised on every city-year for its entire life
    (§1.136).
    """
    import tempfile as _tf
    with _tf.TemporaryDirectory() as tmp:
        r = _build(Path(tmp))
        assert "publication ledger (joburg)" in r.stdout, (
            "the build never reached the ledger block. Everything the unit "
            f"tests prove about `_ledger_candidates` is unreachable.\n"
            f"--- stdout tail ---\n{r.stdout[-1500:]}")
        assert (Path(tmp) / "site" / "changes.json").is_file(), (
            "no changes.json — the reader-facing 'what changed' record is not "
            "actually written by the build that claims to write it.")
        blob = json.loads(
            (Path(tmp) / "site" / "changes.json").read_text())
        assert blob["changes"] and blob["run"]["model_run_id"], blob.keys()
        assert "unknown" not in blob["run"]["model_run_id"], blob["run"]


def test_the_real_build_refuses_to_publish_an_unattributable_run():
    """The write path's refusal, exercised through `main()` rather than around it.

    ⛔ **THIS TEST USED TO RELY ON THE TREE BEING BROKEN, AND THE TREE GOT
    FIXED.** It asserted that the build refuses because
    `data/processed/forecast_summary.json` predated the `_generated` stamp — a
    true fact on 2026-08-31 morning and false by that afternoon, when
    `overhang_regimes.py` re-ran the model and stamped it. The test then failed
    for the best possible reason: **the defect it described was gone.**

    A test whose premise is a passing state of the repository expires without
    warning. So it now BUILDS the unattributable artefact itself, in a temp
    directory, and the guarantee is permanent: a forecast with no run time may
    not be published, whatever `data/processed` happens to contain today.
    """
    import json as _json
    import shutil as _sh
    import tempfile as _tf
    root = Path(__file__).resolve().parents[1]
    live = root / "data" / "processed" / "forecast_summary.json"
    if not live.is_file():
        skip("no forecast_summary.json")
    with _tf.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        proc = tmp / "processed"
        proc.mkdir()
        for f in (root / "data" / "processed").glob("*.json"):
            _sh.copy2(f, proc / f.name)
        for f in (root / "data" / "processed").glob("*.csv"):
            _sh.copy2(f, proc / f.name)
        # strip the run stamp: this is the artefact nothing can attribute
        blob = _json.loads((proc / "forecast_summary.json").read_text())
        blob.pop("_generated", None)
        (proc / "forecast_summary.json").write_text(_json.dumps(blob))

        r = _build(tmp, "--processed", str(proc), "--publish",
                   "--reason", "exercising the refusal",
                   "--change-class", "recompute")
        out = r.stdout + r.stderr
        assert r.returncode != 0, (
            f"the build published a forecast with no run time.\n{out[-1200:]}")
        # ⚠️ TWO REFUSALS NOW GUARD THE SAME ABSENT STAMP, AND THE FIRST WINS.
        # Since 2026-09-17 the footer carries `{{generated_date}}`, sourced from
        # `model:_generated`, so a summary with no run time is refused as an
        # unresolved token before the ledger's run-time check is reached. Either
        # refusal is the guarantee this test exists for; what it must not accept
        # is a refusal for some OTHER reason, so the message has to name the
        # missing stamp.
        assert r.returncode != 0 and (
            ("refusing to publish" in out and "run time" in out)
            or ("refusing to publish" in out and "model:_generated" in out)
        ), out[-1200:]
        assert not list((tmp / "led").rglob("*.jsonl")), (
            "a ledger file was created by a REFUSED publication. The ledger is "
            "append-only; whatever is in it now is permanent.")


def test_a_first_publication_is_not_reported_as_a_change():
    """⛔ `new` IS NOT A MOVE, and the ledger must not say it was.

    `--publish` refuses an undeclared move. `classify` returns "new" for a first
    publication, and the refusal used to count that as moved — so the FIRST EVER
    publish demanded a `--change-class`, and every founding row would have been
    stamped `recompute`, `mechanism` or `bugfix`. None of those describes a
    figure that was never published before, and an append-only record cannot
    take the label back.

    So a build with nothing but new tokens must get PAST the declaration
    refusal, and fail (if at all) only on attribution.
    """
    import tempfile as _tf
    with _tf.TemporaryDirectory() as tmp:
        r = _build(Path(tmp), "--publish")          # no reason, no class
        out = r.stdout + r.stderr
        assert "token(s) moved and the change is undeclared" not in out, (
            "a first publication was refused as an undeclared CHANGE. Nothing "
            "changed; there was nothing there before.")


# --------------------------------------------------------------------------
# THE PRE-LEDGER SEAM: the ledger starts empty and the site does not
# --------------------------------------------------------------------------

#: The archived page the ten `turnout_tilt_da` claims were actually published
#: on. A REAL artefact, tracked by git, containing the real tokens — not a
#: fixture. §1.136's lesson is that a fixture of a shape production never
#: builds proves nothing, and the shape that matters here is "a page whose
#: bytes we can still hash years later".
#:
#: Relative on purpose: `_support` pins the working directory to the repository
#: root, and a repo-relative path is what a real backfill row should RECORD —
#: an absolute path from one machine is not a place anyone else can look.
PAGE = Path("site/index.html")


def _preledger_row(page=PAGE, **kw):
    """A row for `claim_short_by` exactly as the live page published it.

    Built through `preledger_identity` on purpose: if a caller had to assemble
    the id and the provenance by hand, the id and the evidence could drift
    apart, which is the one thing `_preledger_defect` refuses.
    """
    ident = P.preledger_identity(page)
    base = dict(
        token="claim_short_by", value=39, display="39", fmt=None,
        source="run:turnout_tilt_da=1 — 136 minus DA median",
        model_run_id=ident["model_run_id"], run_at=ident["run_at"],
        as_of="2026-08-07", published_at="2026-08-07T00:00:00Z",
        change_class=None, reason=None, movement="new",
        provenance=ident["provenance"])
    prov = kw.pop("provenance", ...)
    base.update(kw)
    if prov is not ...:
        base["provenance"] = prov
    return P.Row(**base)


def test_a_figure_published_before_the_ledger_existed_can_be_entered_as_history():
    """⛔ THE SEAM: `retire()` COULD NOT TOUCH ITS OWN DECLARED FIRST CUSTOMERS.

    Ten front-page claims are pinned to `run:turnout_tilt_da=1`, a lever
    `run_model` no longer has. `retire()`'s docstring names them as what it was
    built for — and it raises `KeyError` on a token that was never published,
    which all ten were, because the ledger started empty while the site had
    weeks of history. So they could not be retired, `dated_context_violations`
    could not fire on them, and the publication path was blocked entirely
    (§1.142's open seam).

    `backfill` enters what the page actually SAID, keyed to the page's bytes
    because no run identity survives. Then `retire()` — **unmodified** — works
    on it, and the second clause of the attribution rule can finally act.

    This test is the whole chain in order, because each link was individually
    plausible and the chain was what was broken.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        assert PAGE.is_file(), (
            f"{PAGE} is missing. The backfill's evidence IS the archived page; "
            f"without it there is nothing to attribute these figures to.")
        row = _preledger_row()

        # 1. the id follows from the PAGE, computed here independently
        sha = hashlib.sha256(PAGE.read_bytes()).hexdigest()
        assert row.model_run_id == "r-preledger-" + sha[:12], (
            f"the run id is {row.model_run_id!r} but the page hashes to "
            f"{sha[:12]}…. The id must be derivable from the archived bytes by "
            f"anyone holding them, or it identifies nothing.")
        assert row.provenance["reconstructed_from"]["sha256"] == sha
        assert row.provenance["reconstructed_from"]["page"] == str(PAGE)
        assert "no run identity exists" in row.provenance["as_of_is"], (
            "the row does not say it was reconstructed. A future reader gets "
            "the row and nothing else, and would read this as a measured run.")

        # 2. it is accepted — and this is the ONE exemption from the refusal
        assert P.backfill("joburg", [row], root=root) == 1, (
            "a figure the site actually published could not be entered. The "
            "ten turnout_tilt_da claims stay unretirable and the build stays "
            "blocked.")
        assert P.latest("joburg", root=root)["claim_short_by"].display == "39"

        # 3. `retire()` is UNCHANGED and now works on it
        retired = P.retire(
            "joburg", "claim_short_by",
            reason="pinned to run:turnout_tilt_da=1, a lever run_model no "
                   "longer has; it cannot be re-derived under any mechanism "
                   "the model still has",
            change_class="mechanism", root=root)
        assert retired.superseded_at, retired

        # 4. and the second clause can finally act on it
        ledger = P.latest("joburg", root=root)
        bad = P.dated_context_violations(
            [{"token": "claim_short_by", "dated": False}], ledger)
        assert len(bad) == 1, (
            "a backfilled-then-retired claim published in live present tense "
            "was not caught. The backfill would then be a way to LAUNDER a "
            "dead figure into the record rather than a way to close it out.")
        assert P.dated_context_violations(
            [{"token": "claim_short_by", "dated": True}], ledger) == []


def test_the_preledger_exemption_cannot_be_claimed_by_saying_the_word():
    """⛔ THE CRUX. A REFUSAL THAT QUIETLY ACQUIRES A CASE STOPS BEING A REFUSAL.

    `_refuse_unattributable` is the only thing between the live build and a
    permanent row attributed to nothing, and this module has already produced
    four guards that read as working and could not fire. The exemption it now
    carries is the exact shape that goes wrong: a prefix on a string. So the
    prefix alone buys nothing — the row must carry the archived page's path AND
    its full sha256, and the id must FOLLOW from that sha.

    The first case is the one that matters most, and it is why the smuggle test
    was demanded before the feature was believed: a row with a `r-preledger-`
    id, no page, and a run time satisfies every one of the three original
    checks — the id does not say "unknown", `run_at` is present, `published_at`
    is present — so nothing but this refuses it.

    ⚠️ **AND THE LAST ASSERTION IS THE DESIGN, NOT A GAP.** A fully-evidenced
    pre-ledger row IS accepted by `append`, because `retire()` closes a token
    out by re-appending the row it is retiring: the retirement of a backfilled
    figure is a pre-ledger row arriving through `append`. A stricter version
    that also required `backfill` on the stack was written first, and it made
    the ten `turnout_tilt_da` claims backfillable and then UNRETIRABLE — the
    seam moved one step down rather than closed. The lock is the evidence.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sha = hashlib.sha256(PAGE.read_bytes()).hexdigest()

        for bad, why in [
            (_preledger_row(provenance=None, run_at="2026-08-07T00:00:00Z"),
             "a preledger id, a run time, and no page at all"),
            (_preledger_row(provenance={"as_of_is": "x"}),
             "a preledger id and provenance with no reconstructed_from"),
            (_preledger_row(provenance={
                "reconstructed_from": {"page": str(PAGE), "sha256": sha},
                "as_of_is": P.AS_OF_RECONSTRUCTED},
                model_run_id="r-preledger-deadbeefcafe"),
             "an id that does not follow from the sha it records"),
        ]:
            try:
                P.append("joburg", [bad], root=root)
            except P.Unattributable:
                pass
            else:
                raise AssertionError(
                    f"`append` accepted a row with {why}. Any row at all can "
                    f"now be written with no attribution by prefixing its id, "
                    f"and it is permanent.")
            assert not (root / "joburg" / "ledger.jsonl").exists(), (
                f"a row refused for {why} still reached the file.")

        # the door does not swing the other way: a row that CAN name its run
        # keeps that attribution rather than being labelled as having none
        try:
            P.backfill("joburg", [_row(token="live")], root=root)
        except P.Unattributable as exc:
            assert "append" in str(exc), exc
        else:
            raise AssertionError(
                "`backfill` accepted an ordinary row. It would be recorded as "
                "reconstructed from a page it never appeared on.")

        # ⛔ AND A WELL-FORMED PRE-LEDGER ROW STILL MAY NOT ENTER A NEW TOKEN
        # THROUGH `append`. This assertion was the reverse until 2026-08-31,
        # and it encoded the hole: a sha256 of arbitrary bytes plus a `page`
        # naming a file that had never existed was accepted here, and `retire()`
        # then laundered it into a supersession. Only id<->sha was enforced;
        # page<->sha was checked in `backfill`, which was optional.
        #
        # `backfill` is now the only door for a token the ledger has not seen,
        # because it is the only place the page can be checked against the
        # world. The lock is a property of the RECORD, not of the call stack —
        # a caller lock was tried and it made backfilled figures unretirable.
        try:
            P.append("joburg", [_preledger_row(token="never_seen")], root=root)
        except P.Unattributable as exc:
            assert "backfill" in str(exc), exc
        else:
            raise AssertionError(
                "`append` introduced a pre-ledger token the ledger had never "
                "seen. Its page is unverified and the row is permanent.")

        # ...but once `backfill` has vouched for it, ordinary appends work —
        # which is exactly what `retire()` does, and why a caller lock failed.
        P.backfill("joburg", [_preledger_row()], root=root)
        assert P.append("joburg", [_preledger_row()], root=root) == 1


def test_a_backfilled_row_must_earn_the_exemption_it_claims():
    """⛔ THE EVIDENCE LOCK, EXERCISED WHERE THE CALLER LOCK IS ALREADY OPEN.

    Every case here goes through `backfill`, so the caller check has already
    passed and the only thing that can refuse them is the evidence itself. If
    these were tested through `append` they would all be refused for the wrong
    reason and the sha requirement would be untested — the shape of defect
    §1.146 caught in this file's own stability test, which asserted the
    property's proxy rather than the property.

    The last two cases are the ones a hand-built row gets wrong: an id invented
    independently of the page, and a page that has moved on since the row was
    cut. The row's id is a claim ABOUT a document; if the document is gone or
    different, the claim is unverifiable and the moment to say so is now.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        page = Path(tmp) / "archived.html"
        page.write_text("<p>the DA is short by 39 seats</p>", encoding="utf-8")
        good = _preledger_row(page=page)
        sha = good.provenance["reconstructed_from"]["sha256"]

        cases = [
            (_preledger_row(page=page, provenance=None),
             "no provenance at all"),
            (_preledger_row(page=page, provenance={
                "reconstructed_from": {"page": str(page)},
                "as_of_is": P.AS_OF_RECONSTRUCTED}),
             "a page with no sha"),
            (_preledger_row(page=page, provenance={
                "reconstructed_from": {"page": str(page), "sha256": "beef"},
                "as_of_is": P.AS_OF_RECONSTRUCTED}),
             "a sha that is not a sha256"),
            (_preledger_row(page=page, provenance={
                "reconstructed_from": {"sha256": sha},
                "as_of_is": P.AS_OF_RECONSTRUCTED}),
             "a sha with no page path"),
            (_preledger_row(page=page, provenance={
                "reconstructed_from": {"page": str(page), "sha256": sha}}),
             "no as_of_is label"),
            (_preledger_row(page=page, model_run_id="r-preledger-000000000000"),
             "an id invented independently of the page sha"),
            (_preledger_row(page=page, run_at="2026-08-07T00:00:00Z"),
             "a run time it cannot have"),
            (_preledger_row(page=page, provenance={
                "reconstructed_from": {"page": str(Path(tmp) / "gone.html"),
                                       "sha256": sha},
                "as_of_is": P.AS_OF_RECONSTRUCTED}),
             "a page that is not on disk"),
        ]
        for bad, why in cases:
            try:
                P.backfill("joburg", [good, bad], root=root)
            except P.Unattributable:
                pass
            else:
                raise AssertionError(
                    f"a backfilled row with {why} was accepted. The exemption "
                    f"is then satisfied by asserting it, and any row at all "
                    f"can be written with no attribution.")
            assert not (root / "joburg" / "ledger.jsonl").exists(), (
                f"the batch was refused for {why} but the good row before it "
                f"was already written. An append-only ledger cannot take a "
                f"half-published batch back.")

        # the page moving after the row was cut is refused while it is still
        # possible to say so
        page.write_text("<p>the DA is short by 41 seats</p>", encoding="utf-8")
        try:
            P.backfill("joburg", [good], root=root)
        except P.Unattributable as exc:
            assert "hashes to" in str(exc), exc
        else:
            raise AssertionError(
                "a row was backfilled against a page that has since changed. "
                "Its id names a document nobody can produce, permanently.")

        # and with the page restored, the same row is fine
        page.write_text("<p>the DA is short by 39 seats</p>", encoding="utf-8")
        assert P.backfill("joburg", [good], root=root) == 1


def test_a_published_token_that_left_the_registry_stops_the_build():
    """⛔ THE DURABLE HALF. THE BACKFILL IS A CLEANUP; THIS IS THE FIX.

    The seam was never really "the ledger started empty". It is that a figure
    can stop being produced and simply VANISH — the lever deleted for a good
    reason by someone with no idea a front-page claim was pinned to it, the
    token dropped from the registry, and nothing anywhere recording that it
    stopped being current or when. That is precisely how the ten
    `turnout_tilt_da` claims happened.

    A vanished token also takes the guard with it: `retire()` is the only thing
    that sets `superseded_at`, and `dated_context_violations` is built entirely
    on that stamp — so a token deleted rather than retired leaves no row for the
    check to fire on. Backfilling ten rows fixes ten rows; this stops the
    eleventh.

    Run through the real `build_site.py`, because the unit is not the point:
    the ledger block sat wired and unreachable in `main()` for a day and every
    unit test stayed green (§1.146).
    """
    with tempfile.TemporaryDirectory() as tmp:
        led = Path(tmp) / "led"
        P.append("joburg", [_row(token="claim_from_a_deleted_lever", value=39,
                                 display="39", fmt=None,
                                 model_run_id="r-c0ffee123456-abcdef12")],
                 root=led)

        r = _build(Path(tmp))
        out = r.stdout + r.stderr
        assert r.returncode != 0, (
            "the build published while a token that had reached readers was "
            "dropped from the registry with no supersession stamp. Nothing "
            "will ever be able to tell a reader when it stopped being true.\n"
            f"--- stdout tail ---\n{r.stdout[-1500:]}")
        assert "claim_from_a_deleted_lever" in out, (
            f"the refusal did not NAME the token, so the builder cannot act on "
            f"it. It said:\n{out[-1500:]}")

        # the obligation is one call, and meeting it clears the refusal
        P.retire("joburg", "claim_from_a_deleted_lever",
                 reason="the lever that produced it was deleted from run_model",
                 change_class="mechanism", root=led)
        r2 = _build(Path(tmp))
        assert r2.returncode == 0, (
            f"the build still refuses after the token was properly retired. "
            f"The refusal has no route out and would block every build.\n"
            f"--- stdout tail ---\n{r2.stdout[-2000:]}")
        assert "LEFT THE REGISTRY UNRETIRED" not in (r2.stdout + r2.stderr)


if __name__ == "__main__":
    run_module(globals())
