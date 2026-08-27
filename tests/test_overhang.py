"""``allocate_with_overhang`` — the excessive-seats rule, pinned on hand-arithmetic.

**This function decides who sits on the council, and it has never had a value
test.** ``ARCHITECTURE.md`` ("Order of work", step A) names it as the first
seam to close, and ``src/freeze.py`` cites it by name as one of the paths where
"reproduce the old numbers" would have protected a defect. It is called once
per draw — 5,000 times on the published 2026 run, 1,500 × 16 on the backtest
panel — with a rule string read out of ``scenario`` and no validation anywhere
between the CLI and the branch.

WHAT IS ASSERTED, AND WHY IT IS NOT SELF-BENCHMARKING. Every expected number
here is derived by hand from Schedule 1 of the Municipal Structures Act, on a
council small enough to do the long division in the docstring, before it is
compared with the code:

* the quota is ``total_votes // seats_available + 1`` ("disregarding
  fractions"), the undistributed seats going by largest remainder;
* item 16(3) as amended by Act 3/2021 re-strikes the quota as
  ``(A − B) / (C − (D + E)) + 1`` — total votes less the excessive party's,
  over council size less the seats it was awarded;
* ``test_the_laingsburg_2021_requota_reproduces_the_published_quota`` is pinned
  to the IEC's own published Seat Calculation Detail for WC051 in 2021
  (A = 6,453, B = 1,530, C = 7, D = 3, quota 1,231, council stays 7) — a real
  election result, quoted in MODEL-LOG §1.17.

No expected value in this file was read off a run of this model. Where the
right answer is a property rather than a number — ``level``'s final council
size is a function of the search path, not of any statute — the property is
asserted and the docstring says so.

THREE DEFECTS ARE DOCUMENTED HERE RATHER THAN FIXED, per the phase-A rule that
this pass adds tests and changes no source:

* an unrecognised rule string silently applies ``expand``
  (``test_an_unrecognised_rule_string_silently_applies_expand``);
* the signature default is ``"expand"`` while the docstring says
  ``deduct`` (``test_no_call_site_relies_on_the_signature_default``);
* ``level`` is unbounded and dies inside ``seats.allocate`` rather than
  terminating when a ward winner's votes cannot fill the council it demands
  (``test_level_raises_instead_of_terminating_when_the_council_outgrows_the_votes``).

Run:
    ./.venv/bin/python tests/test_overhang.py
    ./.venv/bin/python -m pytest tests/test_overhang.py -q
"""

from __future__ import annotations

import ast
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import montecarlo as M  # noqa: E402
from seats import allocate  # noqa: E402

RULES = ("deduct", "expand", "cap", "level")


@contextmanager
def council_of(size: int):
    """Point ``montecarlo.COUNCIL`` at a hand-sized council and put it back.

    ``COUNCIL`` is a module global the allocator reads rather than a parameter,
    which is exactly what ``benchmarks.council_from_shares`` has to work around
    (it saves and restores it around every call). Doing the same here keeps the
    tests from leaking a 10-seat council into whatever runs next in the suite.
    """
    previous = M.COUNCIL
    try:
        M.COUNCIL = size
        yield
    finally:
        M.COUNCIL = previous


def call(votes: dict[str, int], wins: dict[str, int], size: int, rule: str):
    with council_of(size):
        return M.allocate_with_overhang(dict(votes), dict(wins), rule)


# --------------------------------------------------------------------------
# THE CONSTRUCTED COUNCILS
#
# MILD — ten seats, five wards, three parties, one party over its entitlement.
#
#   votes  A 450   B 250   C 300      total 1,000
#   quota  1,000 // 10 + 1 = 101
#   floors A 4 (450//101)   B 2   C 2      = 8, so two seats by remainder
#   rem.   A .4554   B .4752   C .9703  -> C and B take them
#   entitlement            A 4   B 3   C 3
#
# C wins 4 of the 5 wards on 30% of the vote, one more than its entitlement:
# item 16 fires. The four rules answer that differently, and all four answers
# below are long division, not output:
#
#   deduct  new quota (1000-300)//(10-4)+1 = 117; A 450//117=3 B 250//117=2,
#           one seat by remainder (A .846 > B .137) -> A 4, B 2, C keeps 4.
#           council 10.
#   expand  C 3+1 = 4, everyone else untouched, council 10+1 = 11.
#   cap     wins ignored entirely: A 4, B 3, C 3, council 10.
#   level   grow until C is covered: at 11 seats (quota 91) A 5 B 3 C 3 —
#           still short — at 12 (quota 84) A 5 B 3 C 4. council 12.
# --------------------------------------------------------------------------
MILD_VOTES = {"A": 450, "B": 250, "C": 300}
MILD_WINS = {"C": 4}
MILD_COUNCIL = 10
MILD_ENTITLEMENT = {"A": 4, "B": 3, "C": 3}

# EQUAL — seven seats, four wards, three parties. A wins exactly its
# entitlement, which item 16(1) reaches ("equal to or greater", MODEL-LOG
# §1.19). Nothing else triggers.
#
#   votes  A 100   B 200   C 600      total 900
#   quota  900 // 7 + 1 = 129
#   floors A 0   B 1   C 4    = 5, two seats by remainder
#   rem.   A .7752   B .5504   C .6512 -> A and C take them
#   entitlement            A 1   B 1   C 5      (and C wins 3 wards, under 5)
#
#   deduct  A excluded at 1 seat: (900-100)//(7-1)+1 = 134; B 200//134 = 1,
#           C 600//134 = 4, one seat by remainder — B .4925 beats C .4776 —
#           so B 2, C 4. **B has taken a seat off C** purely because an
#           exactly-at-entitlement party was excluded.
EQUAL_VOTES = {"A": 100, "B": 200, "C": 600}
EQUAL_WINS = {"A": 1, "C": 3}
EQUAL_COUNCIL = 7
EQUAL_ENTITLEMENT = {"A": 1, "B": 1, "C": 5}

# CASCADE — fifteen seats, seven wards, four parties, two rounds of item 16.
#
#   votes  A 98  B 851  C 1237  D 1519    total 3,705
#   quota  3705 // 15 + 1 = 248
#   floors A 0  B 3  C 4  D 6 = 13, two by remainder
#   rem.   A .3952  B .4315  C .9879  D .1250 -> C and B
#   entitlement            A 0  B 4  C 5  D 6
#
# A wins 4 wards on 2.6% of the vote (excess 4); B wins 3, one SHORT of its 4.
#   round 2: A excluded, (3705-98)//(15-4)+1 = 328; B 2, C 3, D 4 = 9, two by
#            remainder (C .7713, D .6311, B .5945) -> B 2, C 4, D 5.
#            **B now has 3 wins against 2 seats** — the squeeze pushed it over,
#            and its excess AT THIS ROUND is 1 (it was −1 at round one).
#   round 3: B excluded too, (3705-98-851)//(15-4-3)+1 = 345; C 3, D 4, one by
#            remainder (C .5855 > D .4029) -> C 4, D 4. Nobody left is over.
CASCADE_VOTES = {"A": 98, "B": 851, "C": 1237, "D": 1519}
CASCADE_WINS = {"A": 4, "B": 3}
CASCADE_COUNCIL = 15
CASCADE_ENTITLEMENT = {"A": 0, "B": 4, "C": 5, "D": 6}

# LAINGSBURG — the only real excessive-seat case on the IEC's record, WC051 in
# 2021. The published Excessive Seat Calculation block gives A = 6,453 total
# valid votes, B = 1,530 for the DA, C = 7 seats, D = 3 ward seats, new quota
# (6453 − 1530) / (7 − 3) + 1 = 1,231, council stays 7 (MODEL-LOG §1.17).
#
# The DA's 1,530 and the 6,453 total are the published figures. The split of
# the remaining 4,923 votes among the other parties is CONSTRUCTED, because the
# per-party totals are not recorded in this repository — and it is constructed
# to be diagnostic of the quota rather than agnostic to it: Q holds exactly one
# published quota (1,231) and R one vote less (1,230), so Q takes a seat in the
# first round and R only on remainder. Any denominator other than 7 − 3 = 4, or
# any numerator that still counted the DA's votes, moves a seat here.
#
#   at 7 seats: quota 6453//7+1 = 922; floors DA 1, P 2, Q 1, R 1 = 5, two by
#   remainder (P .6702, DA .6594) -> DA 2, P 3, Q 1, R 1. The DA's entitlement
#   is 2 against 3 wards won, exactly as published.
#   after exclusion: quota 1231; P 2, Q 1, R 0 = 3, one by remainder (R .9992)
#   -> P 2, Q 1, R 1. **P drops from 3 to 2** — this is the seat the Karoo
#   Democratic Force lost, and the reason "expand" is the wrong reading.
LAINGSBURG_VOTES = {"DA": 1530, "P": 2462, "Q": 1231, "R": 1230}
LAINGSBURG_WINS = {"DA": 3}
LAINGSBURG_COUNCIL = 7


# --------------------------------------------------------------------------
# the plain quota, before any of the four rules
# --------------------------------------------------------------------------

def test_the_constructed_entitlements_are_the_schedule_1_quota_arithmetic():
    """If this fails, every other expected value in the file is built on sand.

    It checks the four constructed councils against the Schedule 1 method done
    by hand in the block comments above — quota = total // seats + 1, floors,
    then the undistributed seats by largest remainder. It asserts nothing about
    the overhang rule; it establishes the baseline the overhang rule departs
    from, so that a later failure can be read as "the rule changed" rather than
    "the allocator changed".
    """
    for votes, size, expected in (
            (MILD_VOTES, MILD_COUNCIL, MILD_ENTITLEMENT),
            (EQUAL_VOTES, EQUAL_COUNCIL, EQUAL_ENTITLEMENT),
            (CASCADE_VOTES, CASCADE_COUNCIL, CASCADE_ENTITLEMENT)):
        got = allocate(dict(votes), total_seats=size)
        assert got.quota == sum(votes.values()) // size + 1, (
            f"quota for {votes} over {size} seats")
        assert got.seats == expected, (
            f"entitlement for {votes} over {size} seats: "
            f"{got.seats} != {expected}")

    laingsburg = allocate(dict(LAINGSBURG_VOTES), total_seats=LAINGSBURG_COUNCIL)
    assert sum(LAINGSBURG_VOTES.values()) == 6453, "published total valid votes"
    assert laingsburg.seats["DA"] == 2, (
        "the IEC's published record has the DA entitled to 2 seats on these "
        "votes and winning 3 wards; if the entitlement is not 2 the "
        "reconstruction no longer reproduces the case")


# --------------------------------------------------------------------------
# deduct — the statute
# --------------------------------------------------------------------------

def test_deduct_keeps_the_wards_holds_the_council_and_requotas_the_rest():
    """The statutory rule, whole. Broken, the model seats the wrong council.

    Amended Schedule 1 item 16(1),(3)–(9): the excessive party keeps its ward
    seats and gets no list seats; a new quota is struck over the remaining
    seats for everyone else; **the council does not grow**. On MILD that is
    (1000 − 300) // (10 − 4) + 1 = 117, giving A 4 and B 2, so B pays for C's
    fourth ward. A failure here means either the exclusion, the re-quota
    denominator, or the fixed council size has moved. MODEL-LOG §1.17.
    """
    seats, council, threshold, over = call(
        MILD_VOTES, MILD_WINS, MILD_COUNCIL, "deduct")
    assert seats == {"A": 4, "B": 2, "C": 4}, seats
    assert council == MILD_COUNCIL, "item 16 does not grow the council"
    assert threshold == 6, "a bare majority of ten"
    assert over == {"C": 1}, "C won one ward more than its entitlement of 3"


def test_the_laingsburg_2021_requota_reproduces_the_published_quota():
    """Pinned to a real election, not to this model. The precedent for `deduct`.

    Laingsburg WC051, LGE 2021, the only excessive-seat case found in ~65 IEC
    Seat Calculation Detail reports (MODEL-LOG §1.17). The published block
    strikes (6,453 − 1,530) / (7 − 3) + 1 = 1,231 and leaves the council at 7,
    with the DA on 3 ward seats and no list seat. This reconstruction puts one
    party on exactly 1,231 votes and another on 1,230 so that the outcome is
    sensitive to that quota: at any other denominator the last seat moves.

    If this fails the model is no longer applying the rule the Commission
    applied, and the published "council stays at 270, threshold 136" claim
    loses its only empirical support.
    """
    seats, council, threshold, over = call(
        LAINGSBURG_VOTES, LAINGSBURG_WINS, LAINGSBURG_COUNCIL, "deduct")
    assert council == 7, "the published calculation keeps the council at 7"
    assert threshold == 4, "a bare majority of seven"
    assert seats["DA"] == 3, "3 ward seats, no list seat"
    assert over == {"DA": 1}, "3 wards against an entitlement of 2"
    assert seats == {"DA": 3, "P": 2, "Q": 1, "R": 1}, (
        f"{seats} — P must fall from 3 to 2, which is the seat an 'expand' "
        f"reading would have preserved")
    assert sum(seats.values()) == 7


def test_a_party_at_exactly_its_entitlement_is_excluded_from_the_requota():
    """The equality trigger, and proof that it is not a no-op for the others.

    Item 16(1) reaches a party whose ward seats are "equal to or greater than"
    its entitlement. Both of this project's engines fired only on strictly
    greater until the second-round audit of 2026-08-06; MODEL-LOG §1.19 adopted
    the plain reading and recorded that excluding an exactly-at-quota party
    shifts a seat between the others in 4.2% of forced-equality cases.

    EQUAL is one of those cases, done by hand: A is entitled to 1 and wins 1.
    Excluding it re-strikes the quota at (900 − 100) // (7 − 1) + 1 = 134, and
    B's remainder (.4925) then beats C's (.4776), so **B takes a seat off C**.
    Without the equality trigger the answer would be the untouched entitlement
    A 1, B 1, C 5 — which is what the other three rules give, asserted below,
    so this test cannot pass by accident.
    """
    seats, council, threshold, over = call(
        EQUAL_VOTES, EQUAL_WINS, EQUAL_COUNCIL, "deduct")
    assert over == {"A": 0}, (
        "an exactly-equal party triggers item 16 with an excess of zero")
    assert seats == {"A": 1, "B": 2, "C": 4}, seats
    assert seats != EQUAL_ENTITLEMENT, (
        "if the equality trigger is lost this becomes the plain entitlement")
    assert council == EQUAL_COUNCIL and threshold == 4
    assert sum(seats.values()) == EQUAL_COUNCIL

    for rule in ("expand", "cap", "level"):
        other, _c, _t, _o = call(EQUAL_VOTES, EQUAL_WINS, EQUAL_COUNCIL, rule)
        assert other == EQUAL_ENTITLEMENT, (
            f"{rule} has nothing to do on a zero excess, so it must leave the "
            f"entitlement alone: {other}")


def test_a_party_with_no_wards_is_never_treated_as_excessive():
    """Guards the ``ward_wins[p] > 0`` half of the trigger.

    "Equal to or greater" applied without that guard makes every party with no
    wards and no entitlement excessive (0 >= 0), which would exclude it from
    the re-quota and, on a real 75-party universe, exclude most of the ballot.
    Item 16 is about a party that *has* ward seats; a party with none cannot
    have excessive ones. Here E appears in ``ward_wins`` with zero wins and
    must not reach ``over``, and the answer must be unchanged from MILD.
    """
    wins = dict(MILD_WINS)
    wins["E"] = 0
    seats, council, threshold, over = call(
        MILD_VOTES, wins, MILD_COUNCIL, "deduct")
    assert "E" not in over, over
    assert over == {"C": 1}
    assert (seats, council, threshold) == ({"A": 4, "B": 2, "C": 4}, 10, 6)


def test_deduct_runs_a_second_round_when_the_first_exclusion_squeezes_another_party():
    """The cascade. Item 16 says "repeat"; one round is not the rule.

    Excluding an excessive party removes more seats than votes — that is the
    whole squeeze — so a second party can be pushed under its own ward count by
    the first exclusion. On CASCADE, A (2.6% of the vote, 4 wards) is excluded
    at round one; the re-quota of 328 leaves B on 2 seats against 3 wards, so
    round two excludes B as well; round three settles at C 4, D 4. All three
    quotas are hand-computed in the block comment above.

    If the loop were run once, B would keep 2 seats while holding 3 wards — a
    council seating fewer councillors than were elected in wards.
    """
    seats, council, threshold, over = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "deduct")
    assert seats == {"A": 4, "B": 3, "C": 4, "D": 4}, seats
    assert council == CASCADE_COUNCIL, "still fifteen"
    assert threshold == 8, "a bare majority of fifteen"
    assert sum(seats.values()) == CASCADE_COUNCIL
    assert set(over) == {"A", "B"}, (
        f"both rounds' parties must be recorded as excessive: {over}")


def test_the_excess_recorded_for_a_cascade_party_is_the_one_at_the_round_it_was_fixed():
    """A behavioural claim in the docstring that nothing checked.

    ``allocate_with_overhang`` documents ``excessive_by_party`` as mapping each
    party "to its excess at the round it was fixed". For B on CASCADE those
    numbers differ and are distinguishable: at round one B held 3 wards against
    an entitlement of 4 — it was one seat SHORT and not excessive at all — and
    only at round two, after A's exclusion cut it to 2 seats, was it 1 over. So
    the recorded excess must be **1**, not −1 and not 0.

    This is what ``montecarlo`` counts into ``overhang_count`` and publishes as
    ``p_excessive_by_party`` (§1.19: "parties fixed in cascade re-allocation
    rounds now also count as excessive; they previously went unrecorded"), so a
    regression here silently understates how often the squeeze bites.
    """
    _seats, _council, _threshold, over = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "deduct")
    assert over == {"A": 4, "B": 1}, over
    assert CASCADE_WINS["B"] - CASCADE_ENTITLEMENT["B"] == -1, (
        "B was a seat short at the first round — so a 1 here can only have "
        "come from the round that actually fixed it")


def test_under_deduct_no_party_is_seated_below_the_wards_it_won():
    """The one thing item 16 never trades away: "a party keeps every ward".

    Item 16 squeezes list seats; it cannot unseat a ward councillor, who was
    elected in their own right. This is an invariant rather than a value, and
    it holds across all four constructed councils by construction of the loop
    — the loop only returns when nobody left is at or over their entitlement.
    It is asserted separately from the seat counts because it is the property a
    future rewrite of the loop must preserve even if the numbers move.
    """
    for votes, wins, size in (
            (MILD_VOTES, MILD_WINS, MILD_COUNCIL),
            (EQUAL_VOTES, EQUAL_WINS, EQUAL_COUNCIL),
            (CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL),
            (LAINGSBURG_VOTES, LAINGSBURG_WINS, LAINGSBURG_COUNCIL)):
        seats, _c, _t, _o = call(votes, wins, size, "deduct")
        for party, won in wins.items():
            assert seats.get(party, 0) >= won, (
                f"{party} won {won} wards and was seated "
                f"{seats.get(party, 0)} on {votes}")


# --------------------------------------------------------------------------
# expand, cap, level — the three counterfactuals
# --------------------------------------------------------------------------

def test_expand_grows_the_council_by_the_total_excess_and_moves_the_threshold():
    """The pre-2013 German reading, and this project's own pre-research one.

    ``expand`` is defined (src/overhang_regimes.py) as "the council grows by
    the excess": nobody is squeezed, the chamber absorbs it. So on CASCADE the
    entitlement is untouched, A is topped up from 0 to its 4 wards, the council
    is 15 + 4 = 19 and the majority bar moves with it to 10. It is kept as a
    labelled counterfactual for the regime table on the forecast sheet; if the
    council or the threshold stops moving, that table silently becomes three
    copies of the same law.
    """
    seats, council, threshold, over = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "expand")
    assert over == {"A": 4}, "only the first-round trigger; expand never loops"
    assert seats == {"A": 4, "B": 4, "C": 5, "D": 6}, seats
    assert council == CASCADE_COUNCIL + 4 == 19
    assert threshold == 10, "a bare majority of nineteen"
    assert sum(seats.values()) == council, (
        "the expanded council must be exactly the seats handed out")


def test_expand_leaves_every_other_party_on_its_untouched_entitlement():
    """What makes expand a different law and not a different rounding.

    Under expand the parties that did not trigger item 16 keep precisely the
    seats the plain Schedule 1 quota gave them — the excess is paid by the
    chamber, not by them. Under deduct on the same council B loses a seat and
    C and D lose two between them. Asserting both sides here is what stops the
    two rules quietly converging.
    """
    expanded, _c, _t, _o = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "expand")
    for party in ("B", "C", "D"):
        assert expanded[party] == CASCADE_ENTITLEMENT[party], party
    deducted, _c2, _t2, _o2 = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "deduct")
    assert deducted["C"] < CASCADE_ENTITLEMENT["C"]
    assert deducted["D"] < CASCADE_ENTITLEMENT["D"]


def test_cap_ignores_the_wards_and_seats_fewer_councillors_than_were_elected():
    """Cap's defining property, which is also the reason it is a counterfactual.

    ``cap`` is the Germany-2023 answer: pure proportionality at a fixed
    council, "a ward winner beyond its party's entitlement is simply not
    seated" (src/overhang_regimes.py). On CASCADE that means A holds 4 wards
    and is given **0** seats. That is not a bug in ``cap``; it is what ``cap``
    is, and it is the one rule of the four under which
    ``test_under_deduct_no_party_is_seated_below_the_wards_it_won`` must fail.
    Pinning it stops the rule being quietly "fixed" into another expand.
    """
    seats, council, threshold, over = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "cap")
    assert seats == CASCADE_ENTITLEMENT, "the untouched proportional answer"
    assert seats["A"] == 0 and CASCADE_WINS["A"] == 4, (
        "cap seats none of A's four ward winners")
    assert council == CASCADE_COUNCIL and threshold == 8
    assert sum(seats.values()) == CASCADE_COUNCIL


def test_cap_still_reports_the_item_16_trigger_it_declined_to_act_on():
    """A deliberate asymmetry worth pinning: cap adjusts nothing but reports.

    ``cap`` returns early with a fully populated ``over``. The caller
    (``montecarlo.run_model``) increments ``overhang_count`` and
    ``excessive_draws`` from it, so under ``cap`` the run still publishes
    ``p_excessive_by_party`` and ``p_excessive_any`` at their true rates even
    though no seat moved.

    That is defensible and is what §1.19 defines the statistic to mean — "the
    share of draws in which any party triggers item 16" — and it is what makes
    the number comparable across the four regime runs on the forecast sheet.
    Emptying ``over`` under ``cap`` would make the regime table's excessive-seat
    row read 0% and look like a finding. It also, however, means ``over`` under
    ``cap`` describes a squeeze that did not happen, so nothing downstream may
    infer a seat adjustment from it.
    """
    _seats, _council, _threshold, over = call(
        CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "cap")
    assert over == {"A": 4}, over
    mild_seats, _c, _t, mild_over = call(
        MILD_VOTES, MILD_WINS, MILD_COUNCIL, "cap")
    assert mild_over == {"C": 1}
    assert mild_seats == MILD_ENTITLEMENT, "and not one seat moved"


def test_level_grows_the_council_until_no_ward_winner_is_short():
    """The Ausgleichsmandate counterfactual: the chamber pays, nobody is squeezed.

    On MILD the loop is short enough to do by hand and is written out in the
    block comment: 10 seats leaves C one short, 11 (quota 91) still leaves it
    one short, 12 (quota 84) covers it at C 4. So the council is 12 and the
    threshold 7.

    The council size is pinned here because this particular walk is short and
    hand-checked; it is a property of the search (the loop steps by the current
    deficit) and NOT of any statute, so the invariant — every ward winner
    covered at the returned size — is asserted separately and is the thing that
    must survive a rewrite.
    """
    seats, council, threshold, over = call(
        MILD_VOTES, MILD_WINS, MILD_COUNCIL, "level")
    assert seats == {"A": 5, "B": 3, "C": 4}, seats
    assert council == 12 and threshold == 7
    assert sum(seats.values()) == council
    for party, won in MILD_WINS.items():
        assert seats.get(party, 0) >= won, "nobody is short at the end"
    assert over == {"C": 1}, (
        "``over`` under level is the trigger measured at the ORIGINAL council, "
        "not at the grown one — at 12 seats nobody is excessive at all")


def test_level_returns_the_original_council_when_the_only_trigger_is_an_equality():
    """The termination case that is provable rather than walked.

    An exactly-at-entitlement party is already covered — its wins equal its
    seats — so the deficit is zero on the first pass and ``level`` must return
    the untouched entitlement at the original council size. This is the one
    ``level`` answer that follows from the definition alone, with no search,
    which is why it is asserted as a value.
    """
    seats, council, threshold, over = call(
        EQUAL_VOTES, EQUAL_WINS, EQUAL_COUNCIL, "level")
    assert seats == EQUAL_ENTITLEMENT
    assert council == EQUAL_COUNCIL and threshold == 4
    assert over == {"A": 0}


# --------------------------------------------------------------------------
# invariants that must hold across the rules
# --------------------------------------------------------------------------

def test_the_four_rules_give_four_different_answers_on_one_council():
    """ARCHITECTURE.md's named first task, plus the fourth rule it left out.

    "A constructed council where deduct, expand and cap give three different
    answers, all three pinned." MILD is that council, and ``level`` — which
    appears only in an inline comment inside the function, not in its
    docstring's list of rules — gives a fourth. Every number below is the hand
    arithmetic in the block comment at the top of this file.

    The point is not the four tuples but that they are four: a branch that
    silently fell through to another rule would show up here as two equal rows,
    which is exactly how ``test_an_unrecognised_rule_string_silently_applies_expand``
    below found a real defect.
    """
    got = {rule: call(MILD_VOTES, MILD_WINS, MILD_COUNCIL, rule)[:3]
           for rule in RULES}
    assert got["deduct"] == ({"A": 4, "B": 2, "C": 4}, 10, 6), got["deduct"]
    assert got["expand"] == ({"A": 4, "B": 3, "C": 4}, 11, 6), got["expand"]
    assert got["cap"] == ({"A": 4, "B": 3, "C": 3}, 10, 6), got["cap"]
    assert got["level"] == ({"A": 5, "B": 3, "C": 4}, 12, 7), got["level"]
    assert len({repr(v) for v in got.values()}) == 4, (
        f"two rules returned the same council: {got}")


def test_seats_sum_to_the_council_the_function_reports_under_every_rule():
    """Conservation. A double-count here inflates or deflates a real council.

    Whatever the rule, the seats handed out must equal the council size
    returned alongside them — 270 under deduct and cap, 270 + Σexcess under
    expand, the grown size under level. ``deduct`` in particular merges two
    dicts (``{**sub.seats, **fixed}``) built over different seat pools, which
    is precisely the shape that loses or duplicates a seat when the pool
    bookkeeping drifts.
    """
    for votes, wins, size in (
            (MILD_VOTES, MILD_WINS, MILD_COUNCIL),
            (EQUAL_VOTES, EQUAL_WINS, EQUAL_COUNCIL),
            (LAINGSBURG_VOTES, LAINGSBURG_WINS, LAINGSBURG_COUNCIL)):
        for rule in RULES:
            seats, council, _t, _o = call(votes, wins, size, rule)
            assert sum(seats.values()) == council, (
                f"{rule} on {votes}: seats sum to {sum(seats.values())} "
                f"against a reported council of {council}")
            if rule in ("deduct", "cap"):
                assert council == size, (
                    f"{rule} must not move the council: {council} != {size}")


def test_the_threshold_is_always_a_bare_majority_of_the_reported_council():
    """The published majority bar. Wrong here, every coalition claim is wrong.

    ``threshold`` is what ``coalitions.report`` and the whole "who can govern"
    layer test against, and §1.17 turned on it: under the statute it is 136 of
    270, full stop, and the published "council grows to ~281, bar rises to
    ~141" narrative was wrong law. The rule is the smallest integer strictly
    above half — ``council // 2 + 1`` — which is 136 for 270, 6 for 10 and 11,
    7 for 12, 4 for 7. Asserted as the property, on every rule and council.
    """
    for votes, wins, size in (
            (MILD_VOTES, MILD_WINS, MILD_COUNCIL),
            (EQUAL_VOTES, EQUAL_WINS, EQUAL_COUNCIL),
            (CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL),
            (LAINGSBURG_VOTES, LAINGSBURG_WINS, LAINGSBURG_COUNCIL)):
        for rule in ("deduct", "expand", "cap"):
            _s, council, threshold, _o = call(votes, wins, size, rule)
            assert threshold * 2 > council, (
                f"{rule}: {threshold} is not a majority of {council}")
            assert (threshold - 1) * 2 <= council, (
                f"{rule}: {threshold} is more than the smallest majority of "
                f"{council}")


def test_no_overhang_means_the_plain_entitlement_under_every_rule():
    """The overwhelming majority of draws take this path; it must be inert.

    With no party at or over its entitlement, ``over`` is empty and all four
    rules must return the plain Schedule 1 answer at the unchanged council. If
    any rule moved a seat here it would be moving seats in draws where item 16
    never fired — which, at 5,000 draws a run, would be invisible in the
    aggregate and wrong in every one of them.
    """
    quiet = {"C": 2}          # C is entitled to 3 and wins 2
    for rule in RULES:
        seats, council, threshold, over = call(
            MILD_VOTES, quiet, MILD_COUNCIL, rule)
        assert over == {}, f"{rule}: {over}"
        assert seats == MILD_ENTITLEMENT, f"{rule}: {seats}"
        assert (council, threshold) == (MILD_COUNCIL, 6), rule


# --------------------------------------------------------------------------
# three defects, documented here and NOT fixed (phase A adds tests only)
# --------------------------------------------------------------------------

def test_an_unrecognised_rule_string_silently_applies_expand():
    """DEFECT, pinned as it behaves. A typo changes the law and says nothing.

    The function branches on ``rule`` with no ``else`` and no membership check:
    ``cap`` and an empty ``over`` return early, ``level`` and ``deduct`` return
    from their own blocks, and **everything else falls through to the expand
    block at the bottom**. So ``rule="dedcut"`` does not raise — it grows the
    council and moves the majority threshold.

    Nothing upstream catches it either: ``montecarlo.parse_set`` validates that
    a ``--set`` KEY exists in ``DEFAULTS`` and never looks at the value, and
    ``apply_city`` copies city-config scalars in the same way. So
    ``--set overhang_rule=expend`` runs the pre-research counterfactual under
    the name of the statute, and the only visible symptom is a council that is
    not 270 — in a summary that reports the council it was given.

    This test asserts the CURRENT behaviour so the defect is on the record with
    a reproduction. The fix is a membership check that raises; when it lands,
    this test should be rewritten to assert the raise, deliberately and with a
    note, not deleted.
    """
    bogus = call(CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "dedcut")
    expanded = call(CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "expand")
    assert bogus == expanded, (
        "an unrecognised rule is expected (wrongly) to behave as expand")
    assert bogus[1] == 19 != CASCADE_COUNCIL, (
        "and the damage is visible: a misspelt 'deduct' grew the council")


def test_no_call_site_relies_on_the_signature_default():
    """DEFECT in the declaration; this test guards the blast radius.

    ``def allocate_with_overhang(combined, ward_wins, rule="expand")`` — but
    the docstring one line below says 'Default rule "deduct"', and
    ``DEFAULTS["overhang_rule"]`` is ``"deduct"``, which is the statute
    (§1.17). The signature default is the legacy counterfactual and disagrees
    with both the prose and the model's own configuration.

    Today that is harmless only because both call sites pass the rule
    explicitly — ``montecarlo.run_model`` passes ``scenario["overhang_rule"]``
    and ``benchmarks.council_from_shares`` passes ``ctx.overhang_rule``. This
    test asserts that, because the moment somebody adds a two-argument call
    believing the docstring, they get the expand rule, a council that is not
    270 and a majority threshold that is not 136 — with no error anywhere.

    It also pins the configured default to ``"deduct"``, which is justified by
    the amended Act and the Laingsburg precedent, not by what the code returns.
    """
    assert M.DEFAULTS["overhang_rule"] == "deduct", (
        "the statute, adopted as the default in MODEL-LOG §1.17")
    assert M.allocate_with_overhang.__defaults__ == ("expand",), (
        "if this has changed, the signature default was edited — re-read the "
        "docstring and this test together rather than just re-recording it")

    offenders = []
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (func.attr if isinstance(func, ast.Attribute)
                    else func.id if isinstance(func, ast.Name) else None)
            if name != "allocate_with_overhang":
                continue
            supplied = len(node.args) + len(node.keywords)
            if supplied < 3:
                offenders.append(f"{path.name}:{node.lineno} ({supplied} args)")
    assert not offenders, (
        "these calls omit the rule and therefore silently take the signature "
        "default 'expand', not the documented and configured 'deduct':\n  "
        + "\n  ".join(offenders))


def test_level_raises_instead_of_terminating_when_the_council_outgrows_the_votes():
    """DEFECT, pinned as it behaves. ``level``'s loop has no bound and no exit.

    ``level`` grows the council by the current deficit until every ward winner
    is covered. Nothing bounds that. On CASCADE, A holds 4 of 7 wards on 2.6%
    of the vote, so covering it needs a council of roughly 4 / 0.0264 ≈ 150 —
    and long before that the council is large relative to the vote total,
    ``seats.allocate``'s largest-remainder shortfall exceeds the number of
    parties, and it raises

        ValueError: largest-remainder shortfall 5 exceeds party count 4
                    — vote totals too small for this council size

    from inside a loop whose caller is a per-draw Monte Carlo. The exception
    names the allocator, not the rule that demanded the council, so the report
    points at the wrong place.

    Two things make this survivable today rather than harmless: ``deduct`` is
    the default, and a real metro has ~75 parties and ~1.8M votes, where the
    shortfall stays far below the party count. ``level`` is nonetheless run for
    real by ``src/overhang_regimes.py`` to build the regime table on the
    forecast sheet. The honest fix is a cap on the growth with a named failure,
    not a wider ``except``.
    """
    try:
        call(CASCADE_VOTES, CASCADE_WINS, CASCADE_COUNCIL, "level")
    except ValueError as exc:
        assert "largest-remainder shortfall" in str(exc), exc
    else:
        raise AssertionError(
            "level no longer dies on this council — if it was given a bound, "
            "rewrite this test to assert the bound and say so here")


def test_a_ward_winner_absent_from_the_combined_vote_is_seated_nowhere_under_deduct():
    """DEFECT, latent. ``over`` names a party that ``deduct`` then never seats.

    The trigger is computed over ``ward_wins``, but the ``deduct`` loop only
    ever considers parties present in ``combined`` (``for p in list(votes)``).
    A ward winner missing from ``combined`` is therefore reported as excessive
    and given **no seats at all** — it does not appear in the returned dict —
    while ``expand`` hands it its full ward count and ``level`` cannot
    terminate at all, because its deficit can never be closed.

    ``montecarlo.run_model`` is safe: its universe excludes independents and a
    ward winner always has a positive ward tally, so it is always in
    ``combined``. ``benchmarks.council_from_shares`` is not obviously safe: it
    builds ``combined`` with ``seats.eligible_parties``, which drops any party
    with no PR votes, while its ``wins`` are taken unfiltered from the ward
    argmax. A party that contests wards with no PR list is exactly the
    Schedule 1 ``D`` term, and the right treatment is to take its ward seats
    out of the pool — not to report it excessive and seat it nowhere.

    Pinned as it behaves, so the divergence between the rules is on the record.
    """
    ghost_wins = {"Z": 2, "C": 1}
    deducted, council, _t, over = call(
        MILD_VOTES, ghost_wins, MILD_COUNCIL, "deduct")
    assert over == {"Z": 2}, over
    assert "Z" not in deducted, (
        f"Z is reported excessive and seated nowhere: {deducted}")
    assert sum(deducted.values()) == council == MILD_COUNCIL, (
        "the council still sums, so nothing downstream can notice")

    expanded, ex_council, _t2, _o2 = call(
        MILD_VOTES, ghost_wins, MILD_COUNCIL, "expand")
    assert expanded["Z"] == 2 and ex_council == 12, (
        "expand seats the same party twice over, which is the other half of "
        "the inconsistency")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
