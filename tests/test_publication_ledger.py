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

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import publication as P  # noqa: E402
from _support import run_module, skip  # noqa: E402


def _row(**kw):
    base = dict(token="t", value=0.87, display="87%", fmt="pct0", source="s",
                model_run_id="r1", run_at=None, as_of=None,
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


def test_run_identity_names_the_run_and_not_merely_the_date():
    """A timestamp says WHEN, not WHAT. Two runs a minute apart on different
    code are different runs, and a date cannot tell them apart — so the identity
    carries content hashes of the artefacts the figures were read from.

    Runs against the REAL processed directory: the production shapes are the
    point, and a hand-built dict would not have caught `_generated` being
    absent, which is the thing that made the 87% undetectable.
    """
    processed = Path("data/processed")
    if not (processed / "forecast_summary.json").is_file():
        skip("no forecast_summary.json to attribute")
    ident = P.run_identity(processed)
    assert ident["model_run_id"].startswith("r-"), ident
    assert ident["forecast_summary_sha256"], ident
    # `as_of` is VALID time and is currently the run time, LABELLED as a
    # stand-in. If someone later derives a real input cut-off, this label is
    # what tells them the old rows were not measured.
    assert "as_of" in ident and "as_of_is" in ident, ident


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


if __name__ == "__main__":
    run_module(globals())
