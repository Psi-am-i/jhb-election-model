"""#11 — THE ROSTER-AWARE REFERENCE MUST SEE THE BALLOT AND NEVER THE RESULT.

``benchmarks.uniform_swing_roster`` exists because the comparison it replaces
was not a comparison. ``montecarlo.run_model`` reads
``pools.contesting_parties(target.city, target.year)`` and uses it to drop
baseline parties that did not stand and to seed the ones that did and had no
prior result; ``benchmarks.build_context`` builds its universe out of prior
results alone. At Johannesburg 2021 that meant the model knew ActionSA was on
the ballot and uniform swing could not represent it at all — no prior local
vote, no prior national vote, nothing to swing — so it forecast zero against 44
seats, and because seat totals are conserved every one of those seats was handed
to a party that did not win it.

Reading the roster is legitimate and reading the result is not, and **the two
live in the same file**. That is what makes this module necessary rather than
decorative: the honest-looking version of this reference and the cheating
version differ by which COLUMN of ``lge2021_JHB_vd_party_clean.csv`` they touch,
and no filename-level check can tell them apart.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4's rule for a test that asserts
an absence — here the absence of any dependence on the target's votes:

0. **THE RIGHT POPULATION, AND BOTH DIRECTIONS.** The claim is about every
   quantity this reference takes from the target's own file: the roster, the
   newcomer set, and ward reach. All three are compared, and the newcomer set is
   asserted non-empty in the direction that matters (a reference that found no
   newcomers would pass a vote-blindness test perfectly and fix nothing).
1. **IT LOOKED.** ``_support.election_files_read`` watches the real I/O, and
   ``_support.scanned`` bounds the populations two-sidedly against denominators
   read off the tree — the roster's own size and the count of runnable targets.
2. **IT CAN SEE.** Two constructed violations, one per detector. A deliberately
   leaky roster rule (filter the ballot to parties with votes) must be caught by
   the erasure comparison; ``arrival_group_record`` with its cutoff removed must
   be caught by the temporal spy. A detector is only evidence once something has
   been pushed through it and come out the other side.
3. **CONSTRUCTED INPUT, NOT OBSERVED.** Both violations are injected. Nothing
   here asserts a property of the tree that expires the day someone fixes
   something unrelated.

The erasure harness is ``test_chain._votes_erased`` — imported, not copied. It
rewrites every ``Party_Votes`` to ``"0"`` and leaves the rows alone, so anything
counting votes collapses and anything counting ballot lines is untouched. It is
the strongest test in this repository and there must be exactly one of it.

⛔ **AND `uniform-swing` MUST NOT MOVE.** The panel's comparison to every earlier
measurement runs through it. ``test_the_new_reference_is_uniform_swing_plus_the
_roster_and_nothing_else`` pins that structurally rather than by a golden: given
a roster containing everyone already in the universe, the new reference must
return the old one's output exactly, because every term it adds is then empty.

Run:
    ./.venv/bin/python tests/test_roster_aware_baseline.py
    ./.venv/bin/python -m pytest tests/test_roster_aware_baseline.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import election_files_read, run_module, scanned, skip  # noqa: E402
from test_chain import _votes_erased  # noqa: E402

import backtest as B  # noqa: E402
import benchmarks as BM  # noqa: E402
import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
TARGET = 2021          # the city-year the whole finding is about
NAME = "uniform-swing+roster"


def _context(target: int = TARGET):
    """An active city and a built context, or a skip if the archive is absent.

    ``build_context`` reads four election files. When the repository is checked
    out without ``data/``, every test here has nothing to say and says so rather
    than weakening what it asserts.
    """
    city = cityconfig.use(CITY)
    M.apply_city(city)
    try:
        return BM.build_context(target)
    except (FileNotFoundError, SystemExit) as exc:
        skip(f"no archive for {CITY} {target}: {exc}")


# --------------------------------------------------------------------------
# 1. the registry contract
# --------------------------------------------------------------------------

def test_the_reference_is_registered_under_the_contracted_name():
    """``compare_history`` derives its opponent list from ``BENCHMARKS``, so the
    key is the interface. Asserted by name because a rename would silently drop
    the column out of every table rather than fail anything.

    The other half is the one that would be left out: ``uniform-swing`` must
    still be registered, and still bound to the function it was bound to.
    """
    assert NAME in BM.BENCHMARKS, (
        f"{NAME!r} is not in benchmarks.BENCHMARKS, so `compare_history` will "
        f"not score it and the panel keeps the comparison this fixes")
    assert BM.BENCHMARKS[NAME] is BM.uniform_swing_roster
    assert BM.BENCHMARKS["uniform-swing"] is BM.uniform_swing, (
        "the existing reference has been re-pointed. Every measurement quoted "
        "against `uniform-swing` before today is then incomparable.")
    scanned(BM.BENCHMARKS, of=("last-lge", "uniform-swing", "blended-swing",
                               NAME, "prior-lge-noise"),
            low=1.0, high=1.6, what="registered benchmarks",
            denominator="the references this file knows about")


# --------------------------------------------------------------------------
# 2. it looked: the roster half of the reference actually fires
# --------------------------------------------------------------------------

def test_the_roster_split_finds_both_the_absent_and_the_arrived():
    """THE POSITIVE CONTROL, and the one that stops everything below being
    vacuous.

    A reference that resolved an empty roster would drop nobody, admit nobody,
    and pass every vote-blindness check in this file while being exactly the
    unfixed ``uniform-swing``. So assert the mechanism produced something in
    BOTH directions — parties removed because they did not stand, and parties
    admitted because they did — and bound each against a denominator read off
    the ballot rather than typed.

    ActionSA is named because it is the finding: it is the party the unfixed
    reference could not represent, and if it is not in the newcomer set then
    this reference is not addressing the case it was built for.
    """
    ctx = _context()
    on_ballot, newcomers, reach = BM.roster_split(ctx)
    roster = pools.contesting_parties(cityconfig.active(), str(TARGET))
    absent = set(ctx.universe) - set(on_ballot)

    assert "ASA" in newcomers, (
        f"ActionSA is not among the {len(newcomers)} parties this reference "
        f"treats as arriving at {TARGET}. It is the entire finding — no prior "
        f"local vote, no prior national vote, 44 seats — so either the roster "
        f"or the universe has changed shape and this reference is no longer "
        f"doing the thing it was built to do.")
    assert absent, (
        f"no party in the {len(ctx.universe)}-party baseline universe is off "
        f"the {TARGET} ballot. The off-ballot drop has gone inert and half the "
        f"reference is no longer running.")

    scanned(newcomers, of=roster, low=0.10, high=0.90,
            what="parties on the ballot with no prior result of any kind",
            denominator="the target's nomination roster")
    scanned(absent, of=ctx.universe, low=0.10, high=0.90,
            what="baseline parties dropped for not standing",
            denominator="the prior-results party universe")
    scanned(reach, of=newcomers, low=0.5, high=1.0,
            what="newcomers whose ward reach could be measured",
            denominator="the newcomers")


# --------------------------------------------------------------------------
# 3. it never read the result: the erasure comparison
# --------------------------------------------------------------------------

def test_the_roster_split_is_identical_with_every_vote_erased():
    """THE CLAIM, ASKED THE ONLY HONEST WAY.

    Who stood, who is new, and how many wards each fielded a candidate in are
    all properties of the nomination list. Erase every ``Party_Votes`` in the
    repository and all three must come back byte-identical; anything that had
    quietly started counting votes collapses to nothing and the comparison
    fails.

    This is what separates a legitimate read of the target's file from an
    illegitimate one. Both open ``lge2021_JHB_vd_party_clean.csv``; they differ
    by which column they touch, which no filename-level spy can see.
    """
    ctx = _context()
    measured = BM.roster_split(ctx)
    with _votes_erased():
        blind = BM.roster_split(ctx)

    assert blind[0] == measured[0], (
        "the on-ballot universe changed when every vote was erased, so the "
        "roster drop is reading the result: "
        + str(sorted(set(blind[0]) ^ set(measured[0]))[:6]))
    assert blind[1] == measured[1], (
        "the newcomer set changed when every vote was erased, so who counts as "
        "a new party is being decided by the result: "
        + str(sorted(set(blind[1]) ^ set(measured[1]))[:6]))
    assert blind[2] == measured[2], (
        "ward reach changed when every vote was erased, so it is counting the "
        "wards a party SCORED in rather than the wards it stood in: "
        + str(sorted(p for p in set(blind[2]) | set(measured[2])
                     if blind[2].get(p) != measured[2].get(p))[:6]))


def test_the_erasure_comparison_catches_a_roster_rule_that_reads_votes():
    """CAN THE DETECTOR SEE? A constructed violation, through the same harness.

    The failure this guards against is not hypothetical and not exotic: it is
    one line. ``levels.contestation`` and ``pools._ward_reach`` both shipped it —
    they counted the wards a party won votes in and called it the wards it
    stood in, turning Royal Loyal Progress's full 135-ward slate into 59% of a
    slate (MODEL-LOG §1.47).

    So build that defect deliberately — a roster filtered to parties with a
    positive vote — push it through the identical comparison, and require the
    comparison to fail. If it passes, the test above proves nothing.
    """
    ctx = _context()

    def leaky_roster() -> set[str]:
        """A roster taken from who SCORED rather than who STOOD."""
        from fold import citywide, load
        path = Path("data/raw/elections") / ctx.spec["actual"]
        votes, _ = load(path, None)
        return {p for p, share in citywide(votes).items() if share > 0}

    honest = leaky_roster()
    with _votes_erased():
        try:
            blind = leaky_roster()
        except ZeroDivisionError:
            # Even louder than a difference: with no votes anywhere there is no
            # denominator. The constructed defect cannot survive the harness,
            # which is the property being demonstrated.
            blind = None

    assert blind != honest, (
        "a roster rule that filters on VOTES survived having every vote "
        "erased, so `_votes_erased` is not reaching the reader this reference "
        "uses and the blindness test above is inert. Check that "
        "`csv.DictReader` and `ingest_lge.read_municipality` are still the two "
        "routes into the target's result file.")
    assert len(honest) > 1, \
        "the constructed violation read nothing, so it demonstrates nothing"


# --------------------------------------------------------------------------
# 4. the arrival prior predates its target
# --------------------------------------------------------------------------

def test_the_arrival_budget_reads_no_election_at_or_after_its_target():
    """The newcomer LEVEL is measured, so it is the half that can leak.

    ``arrival_budget`` averages the group total that arrivals took in each metro
    -year strictly before the target. The cutoff is one line inside
    ``pools.arrival_group_record`` — ``if before_year and int(year) >=
    int(before_year): continue`` — and a test that restated it would be true of
    the calendar whatever the code read. So watch the reads instead: every
    result file this repository consumes is named for its election, so a
    forecast for 2016 that opens ``lge2021_...`` has read the future whatever
    the loop believed.

    Run at every runnable target, not at one, because a cutoff that is right
    at 2021 and wrong at 2011 is a cutoff nobody checked at 2011.
    """
    city = cityconfig.use(CITY)
    M.apply_city(city)
    targets = B.runnable_targets(city)
    if not targets:
        skip(f"{CITY} has no runnable targets")

    checked = []
    for year in targets:
        with election_files_read() as reads:
            try:
                budget = BM.arrival_budget(int(year))
            except (FileNotFoundError, SystemExit) as exc:
                skip(f"no arrival archive before {year}: {exc}")
        late = sorted({(y, kind) for y, kind, _ in reads
                       if int(y) >= int(year)})
        assert not late, (
            f"the arrival budget for target {year} opened {late}. That is the "
            f"election being predicted, or one after it, and the newcomer "
            f"level is then fitted to the thing it forecasts.")
        assert reads, (
            f"the arrival budget for {year} opened no election file at all, so "
            f"'it read nothing late' is vacuous. The record has gone empty or "
            f"the spy has stopped seeing the reader.")
        assert 0.0 < budget < 0.5, (
            f"the arrival budget at {year} is {budget!r}, which is not a share "
            f"of a city's vote")
        checked.append(year)

    scanned(checked, of=targets, low=1.0, high=1.0,
            what="targets whose arrival budget was watched",
            denominator="backtest.runnable_targets for this city")


def test_the_temporal_spy_catches_an_arrival_record_with_no_cutoff():
    """CAN THE DETECTOR SEE? The same record, with its cutoff removed.

    ``arrival_group_record(before_year=None)`` is the production function's own
    documented "whole record" mode, so the violation is constructed out of real
    behaviour rather than a stub that might not resemble it. Against target
    2016 it must read at least one election dated 2016 or later, and the spy
    must report it.
    """
    city = cityconfig.use(CITY)
    M.apply_city(city)
    with election_files_read() as reads:
        try:
            whole = pools.arrival_group_record(before_year=None)
        except (FileNotFoundError, SystemExit) as exc:
            skip(f"no arrival archive: {exc}")
    late = sorted({(y, kind) for y, kind, _ in reads if int(y) >= 2016})
    assert late, (
        "the uncut arrival record read nothing dated 2016 or later, so the "
        "temporal spy above cannot distinguish a cutoff that works from one "
        "that was never needed. Either the archive has shrunk to pre-2016 or "
        "the spy is no longer watching this reader.")
    assert len(whole) > len(pools.arrival_group_record(before_year="2016")), \
        "the uncut record is no larger than the cut one; the cutoff is inert"


def test_the_reference_opens_nothing_dated_after_its_target():
    """The whole reference, watched end to end.

    The target's own result file IS opened, and legitimately: the roster and
    ward reach come from it, both nomination facts, and the votes beside them
    are proved untouched by the erasure test above. Nothing dated LATER may be
    opened by any route, including helpers nobody thought to check — which is
    the class of leak this spy exists for.
    """
    ctx = _context()
    with election_files_read() as reads:
        try:
            BM.uniform_swing_roster(ctx, draws=1)
        except (FileNotFoundError, SystemExit) as exc:
            skip(f"no archive for {CITY} {TARGET}: {exc}")

    late = sorted({(y, kind) for y, kind, _ in reads if int(y) > TARGET})
    assert not late, f"the reference for {TARGET} opened {late}"
    at_target = sorted({path for y, _kind, path in reads if int(y) == TARGET})
    assert at_target, (
        f"the reference opened no {TARGET} file at all, so it read no roster "
        f"and the whole fix is inert")
    before = {y for y, _kind, _p in reads if int(y) < TARGET}
    assert before, (
        "the reference opened no earlier election, so its newcomer level came "
        "from nowhere")


# --------------------------------------------------------------------------
# 5. the existing reference does not move
# --------------------------------------------------------------------------

def test_the_new_reference_is_uniform_swing_plus_the_roster_and_nothing_else():
    """Structural, not a golden — this project bars judging a change by whether
    it reproduces an earlier output of its own.

    Every term the new reference adds is keyed on the roster: parties dropped
    for being absent from it, parties admitted for being new to it. Hand it a
    roster that already contains the whole baseline universe and both terms are
    empty by construction, so it must return ``uniform_swing``'s output
    exactly. If it does not, it has changed the swing itself, and every figure
    ever quoted against ``uniform-swing`` has become incomparable.

    The second half is the positive control: with the REAL roster the two must
    differ, or the roster terms are inert and the first half passed for the
    wrong reason.
    """
    ctx = _context()
    expected_seats, expected_wards = BM.uniform_swing(ctx, draws=1)

    real = pools.contesting_parties
    try:
        pools.contesting_parties = lambda _city, _year: set(ctx.universe)
        seats, wards = BM.uniform_swing_roster(ctx, draws=1)
    finally:
        pools.contesting_parties = real

    assert seats == expected_seats, (
        "with a roster that excludes nobody and admits nobody, the roster-aware "
        "reference did not reproduce `uniform_swing`. It is not the old "
        "reference plus the roster; it has moved the swing.\n"
        + str(sorted((p, expected_seats[0].get(p), seats[0].get(p))
                     for p in set(expected_seats[0]) | set(seats[0])
                     if expected_seats[0].get(p) != seats[0].get(p))[:8]))
    assert wards == expected_wards, \
        "the ward winners moved under a roster that changes nothing"

    live_seats, _ = BM.uniform_swing_roster(ctx, draws=1)
    assert live_seats != expected_seats, (
        f"with the REAL {TARGET} roster the reference returns exactly what "
        f"`uniform_swing` returns, so neither the off-ballot drop nor the "
        f"newcomer entry is doing anything and the test above passed "
        f"vacuously.")


def test_a_party_left_off_the_roster_cannot_appear_in_the_forecast():
    """THE DROP IS ASSERTED WHERE IT LANDS, not where it is decided.

    ⛔ WRITTEN BECAUSE THE FIRST VERSION OF THIS FILE MISSED IT. Replacing the
    kept-column index with ``list(range(len(ctx.universe)))`` — the off-ballot
    drop disabled outright, half the reference inert — left all nine tests
    green. ``test_the_roster_split_finds_both_the_absent_and_the_arrived``
    proves the drop is DECIDED and says nothing about whether it is APPLIED,
    and asserting "no off-ballot party won a seat" would pass vacuously, since
    the thirty parties in question hold 0.42% of the baseline between them and
    need not win one anyway.

    So construct the case instead: take the largest party in the baseline, say
    it did not stand, and require it to be absent from the council. A party
    that big cannot fail to win seats by accident, so the assertion cannot pass
    for the wrong reason.
    """
    ctx = _context()
    biggest = max(ctx.universe, key=lambda p: ctx.prior_lge_city.get(p, 0.0))
    assert ctx.prior_lge_city.get(biggest, 0.0) > 0.05, (
        f"the largest party in the {CITY} baseline is {biggest} on "
        f"{ctx.prior_lge_city.get(biggest, 0.0):.2%}, which is too small for "
        f"this test's premise — it must be a party that cannot miss the "
        f"council by chance")

    real = pools.contesting_parties
    try:
        pools.contesting_parties = (
            lambda _city, _year: set(ctx.universe) - {biggest})
        seats, winners = BM.uniform_swing_roster(ctx, draws=1)
    finally:
        pools.contesting_parties = real

    assert biggest not in seats[0], (
        f"{biggest} was declared off the {TARGET} ballot and still took "
        f"{seats[0][biggest]} seats. The off-ballot drop is decided and never "
        f"applied, so the reference is scoring parties that did not stand — "
        f"which is the defect it exists to remove.")
    assert biggest not in set(winners[0].values()), \
        f"{biggest} was declared off the ballot and still won wards"
    assert sum(seats[0].values()) == ctx.council, (
        f"the council came back with {sum(seats[0].values())} seats against "
        f"{ctx.council}; dropping a party has broken the allocation rather "
        f"than redistributing it")


def test_a_roster_newcomer_reaches_the_council_with_its_declared_share():
    """The other half, and the same argument: the newcomer block must be
    APPLIED, not merely computed.

    Constructed, because no real newcomer at this target is large enough to be
    a reliable witness — that is the finding, not an accident. A synthetic party
    on the roster and nowhere else has no measured reach, so it takes the whole
    arrival budget, which at every runnable target is near 1.9% of the city and
    therefore several seats. If it is absent from the council the insertion is
    inert.
    """
    ctx = _context()
    ghost = "ROSTER_ONLY_TEST_PARTY"
    real = pools.contesting_parties
    try:
        pools.contesting_parties = lambda _city, _year: set(ctx.universe) | {ghost}
        seats, _winners = BM.uniform_swing_roster(ctx, draws=1)
    finally:
        pools.contesting_parties = real

    budget = BM.arrival_budget(ctx.target)
    assert ghost in seats[0], (
        f"a party on the roster with no prior result took no seat at all, "
        f"while holding the entire measured arrival budget ({budget:.3%} of "
        f"the city). The newcomer columns are being computed and discarded, "
        f"and the reference still forecasts a structural zero for every party "
        f"that arrives — the thing it was built to stop.")
    assert sum(seats[0].values()) == ctx.council, (
        f"admitting a newcomer returned {sum(seats[0].values())} seats against "
        f"a council of {ctx.council}")


def test_a_newcomer_with_no_measured_reach_is_not_given_a_reach_of_one():
    """``pools.entrant_record`` records why this is worth a test of its own: an
    unmeasured reach defaulted to 1.0 is a fabricated covariate at its most
    consequential value, and it lands the party in the bucket that sizes the
    arrivals which win seats. Zero is the other tempting answer and it deletes a
    party that is on the ballot — the defect this whole reference removes.

    Constructed, so it does not depend on the tree happening to contain such a
    party: one newcomer is given a reach and one is not, and the one without
    must be sized at the MEDIAN of the ones with, which here is the only other
    party's value.
    """
    ctx = _context()
    newcomers = ["WIDE", "UNKNOWN", "NARROW"]
    reach = {"WIDE": 1.0, "NARROW": 0.2}
    shares = BM.newcomer_shares(ctx, newcomers, reach)

    assert set(shares) == set(newcomers), \
        "a newcomer was dropped rather than sized"
    assert shares["UNKNOWN"] < shares["WIDE"], (
        "the party with no measured reach was sized at or above the full-slate "
        "party, which is the fabricated-covariate defect")
    assert shares["UNKNOWN"] > shares["NARROW"], (
        "the party with no measured reach was sized at or below the narrowest "
        "measured one, which is the silent-deletion defect")
    assert abs(shares["WIDE"] / shares["NARROW"] - 5.0) < 1e-9, (
        "the split between newcomers is no longer proportional to ward reach, "
        "so the only covariate this reference uses has stopped being used")

    total = sum(shares.values())
    budget = BM.arrival_budget(ctx.target)
    assert abs(total - budget) < 1e-12, (
        f"the newcomer shares sum to {total:.6%} against a measured arrival "
        f"budget of {budget:.6%}. The budget is the level and reach is only "
        f"the split; if they disagree the level has become a free parameter.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
