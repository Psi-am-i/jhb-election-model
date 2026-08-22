"""CLASS 16 — A REGISTER THAT LOSES A RECORD IN SILENCE.

`polling.usable_for` expressed two entirely different things with the same
`continue`: "this poll is about a different election", which is correct
behaviour, and "someone typed `Metro` instead of `metro`", which is a poll we
meant to count and silently did not. Neither printed anything, and there was no
way to tell them apart from the outside.

That is not a hypothetical failure. `ipsos-w2-2025-metros` is dropped by every
caller in this repository **and simultaneously offered as a one-click preset by
the interactive**. And the 2026 forecast rests on one house's two waves: losing
one of them to a typo would move a published number and print nothing at all.

So the two ideas are now separate — `validate` for malformed, `screen` for
inapplicable-with-a-reason — and these tests hold the line between them.

The line was drawn the hard way. The first validator made a missing sample size
fatal, and it **refused the committed register**: Ipsos never published the metro
cut sizes for the nine 2016 readings `POLL_HOUSE_SD` is calibrated on. A rule
strict enough to reject its own calibration set is measuring the author's wishes
rather than the data, so absence-of-published-detail is a warning and only
malformation is an error.

MODEL-LOG §1.68.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import polling as PG  # noqa: E402


def test_the_committed_register_is_well_formed():
    """The whole point: a broken record must stop a run, so ours must not be."""
    problems = PG.validate()
    errors = [p for p in problems if p.severity == "error"]
    assert not errors, (
        "the committed `polls.json` has malformed records:\n  "
        + "\n  ".join(str(p) for p in errors)
        + "\nEvery run now calls `validate_or_die`, so this fails the whole "
          "forecast rather than quietly using fewer polls.")
    # and the warnings must stay warnings, or the register becomes unusable
    PG.validate_or_die()


def test_a_typo_is_fatal_and_a_missing_sample_size_is_not():
    """The distinction the first version of this validator got wrong."""
    typo = [{"id": "x", "house": "H", "scope": "Metro", "city": "joburg",
             "fieldwork_end": "2026-09-01", "n": 800, "numbers": {"DA": 0.4}}]
    assert any(p.severity == "error" and p.field == "scope"
               for p in PG.validate(typo)), (
        "`scope: \"Metro\"` is accepted. Case matters — the callers filter on "
        "the exact string 'metro', so this record would be recorded, look "
        "correct to a human, and never be used by anything.")
    try:
        PG.validate_or_die(typo)
    except PG.PollRegisterError:
        pass
    else:
        raise AssertionError("validate_or_die accepted a malformed scope")

    no_n = [{"id": "y", "house": "Ipsos", "scope": "metro", "city": "joburg",
             "fieldwork_end": "2016-08-01", "numbers": {"ANC": 0.46}}]
    assert all(p.severity == "warn" for p in PG.validate(no_n)), (
        "a poll with no published sample size is treated as malformed. It is "
        "not: Ipsos never published the metro cut sizes for the nine 2016 "
        "readings POLL_HOUSE_SD is calibrated on, so this rule would refuse "
        "our own calibration set.")
    PG.validate_or_die(no_n)          # must not raise


def test_percentages_masquerading_as_fractions_are_caught():
    """The mistake a reader submitting a poll will actually make."""
    pct = [{"id": "z", "house": "H", "scope": "metro", "city": "joburg",
            "fieldwork_end": "2026-09-01", "n": 800,
            "numbers": {"DA": 42, "ANC": 18}}]
    assert any(p.severity == "error" and p.field == "numbers"
               for p in PG.validate(pct)), (
        "shares of 42 and 18 are accepted as fractions. Entered into the blend "
        "they are 4200% and 1800%; the register stores fractions and a reader "
        "typing what the newspaper printed is the expected input.")


def test_a_three_person_poll_is_refused():
    """POLL_MIN_N exists because readers will submit polls to the competition.

    **The guarantee is unchanged; where it is enforced moved (MODEL-LOG §1.69).**
    This used to assert that `validate` returned an *error* on `n`, i.e. that a
    small poll is MALFORMED. It is not: a poll with a published, positive,
    too-small sample is the definition of well-formed-but-inadmissible, and
    filing it as malformed had two costs — `validate_or_die` killed the whole
    run when `poll_min_n` was swept above the shipped register's smallest poll,
    so the lever could not be measured at all; and a reader submitting a small
    poll would have been told their record was broken rather than small.

    So the floor is a SCREEN rule now, and this test asserts the thing that
    actually matters: **a three-person poll does not reach the forecast**, and
    it is declined with a reason a human can read.
    """
    tiny = {"id": "t", "house": "H", "scope": "metro", "city": "joburg",
            "fieldwork_end": "2026-09-01", "n": 3, "numbers": {"DA": 0.9}}
    assert not any(p.severity == "error" for p in PG.validate([tiny])), (
        "a three-person poll is well-formed — small, but not malformed. Making "
        "it fatal is what stopped `poll_min_n` being sweepable.")
    target = cityconfig.use_target("2026")
    kept, declined = PG.screen(target, [tiny])
    assert not kept, (
        f"a poll of three people is admitted. POLL_MIN_N is {PG.POLL_MIN_N} and "
        f"it is the floor below which a submission is recorded and never priced "
        f"as evidence at all.")
    assert any(x.rule == "under-min-n" and "3" in x.detail for x in declined), (
        f"the poll was dropped without naming the floor as the reason: "
        f"{[str(x) for x in declined]}")


def test_every_exclusion_carries_a_reason_a_human_can_read():
    """`screen` must explain itself; that is the entire reason it exists."""
    target = cityconfig.use_target("2026")
    kept, declined = PG.screen(target)
    assert kept, "no polls admitted at 2026 — the register or the rules moved"
    assert declined, (
        "nothing was declined at 2026, but the register holds a "
        "party-commissioned poll and several declared for other elections. "
        "Either they are being admitted, or `screen` has stopped reporting.")
    for exclusion in declined:
        assert exclusion.rule and exclusion.detail, (
            f"an exclusion with no reason: {exclusion!r}. A silent drop is what "
            f"this class of test exists to prevent.")
        assert exclusion.poll_id != "<no id>", (
            "an exclusion that cannot name the poll it excluded")
    # the two the register documents as deliberately excluded must be among them
    rules = {e.poll_id: e.rule for e in declined}
    assert rules.get("da-internal-2026aug") == "commissioned", (
        f"the DA's own internal poll is not excluded as commissioned "
        f"(got {rules.get('da-internal-2026aug')!r}). It is the evidence for "
        f"the exclusion rule, not evidence about the election.")


def test_usable_for_still_agrees_with_screen():
    """`usable_for` is now a thin wrapper; it must not drift from the thing it wraps."""
    for year in ("2016", "2021", "2026"):
        target = cityconfig.use_target(year)
        assert ([q["id"] for q in PG.usable_for(target)]
                == [q["id"] for q in PG.screen(target)[0]]), (
            f"at {year} `usable_for` and `screen` admit different polls. They "
            f"are one rule and one of them has grown a second copy.")


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
