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

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, election_files_read, run_module, scanned, skip  # noqa: E402
from test_chain import _votes_erased  # noqa: E402

import backtest as B  # noqa: E402
import benchmarks as BM  # noqa: E402
import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
TARGET = 2021          # the city-year the whole finding is about
NAME = "uniform-swing+roster"

# ---------------------------------------------------------------------------
# the figures the docstrings quote, in one place
# ---------------------------------------------------------------------------
#
# ⛔ THESE ARE NOT A GOLDEN AND THEY ARE NOT A STANDARD OF CORRECTNESS
# (CLAUDE.md §1). Nothing here says the reference is right. They are the
# numbers `benchmarks.uniform_swing_roster` and `benchmarks.canonical_order`
# QUOTE IN PROSE, pinned so the prose cannot go stale in silence — §2's rule,
# applied to a docstring that has already been wrong once: it claimed the
# reference was deterministic and that ActionSA "takes one seat", while the
# seat was a coin toss between two tied parties.
#
# Every one is a property of the reference's own pre-election inputs except
# the two marked ACTUAL, which are the published result and are quoted as the
# thing being missed.
ASA_WARDS_CONTESTED = 134       # of 135; the one ward it did not nominate in
JHB_2021_WARDS = 135
ASA_ENTRY_SHARE = 0.00163835    # budget x reach / sum(reach), to 6 s.f.
ASA_NEWCOMERS_STRICTLY_ABOVE = 5        # parties at reach 1.000
ASA_TIED_WITH = "CHANGE"                # same reach, same votes, same remainder
ASA_SEATS_IN_THE_REFERENCE = 1          # and it is the tie-break that says so
ASA_SEATS_ACTUAL = 44                   # ACTUAL
PA_SEATS_IN_THE_REFERENCE = 0
PA_SEATS_ACTUAL = 8                     # ACTUAL
WHOLE_BUDGET_SEATS = 5          # what ONE party holding all 1.9562% takes

# Hash seeds for the cross-process determinism test. 0 and 4 are the pair that
# DISAGREE with the tie-break removed (measured 2026-09-13), which is what makes
# the positive control sharp; they are tried first so it usually costs two
# interpreter starts rather than six.
HASH_SEEDS = ("0", "4", "1", "2", "3", "5")

# A child that prints one council as sorted JSON. `TIE_OFF` removes the
# canonical ordering and nothing else — the constructed violation.
_CHILD = """
import json, os, sys
sys.path.insert(0, "src")
import benchmarks as BM, cityconfig, montecarlo as M
if os.environ.get("TIE_OFF"):
    BM.canonical_order = dict           # the defect, restored exactly
city = cityconfig.use("%s")
M.apply_city(city)
ctx = BM.build_context(%d)
print(json.dumps(BM.uniform_swing_roster(ctx, draws=1)[0][0], sort_keys=True))
"""


def _council_in_a_fresh_process(script: Path, hashseed: str,
                                tie_off: bool = False) -> str:
    """One council, from a NEW interpreter at a stated ``PYTHONHASHSEED``.

    In-process repetition cannot see this defect: set iteration order is fixed
    for the life of an interpreter, so a loop inside one test agrees with
    itself perfectly while two runs from the shell disagree. That is exactly how
    the defect survived review, and it is why this costs a subprocess.

    ⛔ **A failed child FAILS, it does not skip.** The caller has already built a
    context in this process, so the archive is present and the venv works; a
    child that dies after that is a broken reference, and skipping on it would
    turn this test into one that reports green whatever happens.
    """
    env = {"PATH": "/usr/bin:/bin", "HOME": str(Path.home()),
           "PYTHONHASHSEED": hashseed}
    if tie_off:
        env["TIE_OFF"] = "1"
    proc = subprocess.run([str(ROOT / ".venv" / "bin" / "python"), str(script)],
                          cwd=ROOT, capture_output=True, text=True, env=env)
    assert proc.returncode == 0, (
        f"the reference died in a child process at PYTHONHASHSEED={hashseed} "
        f"(TIE_OFF={tie_off}):\n{proc.stderr.strip()[-600:]}")
    return proc.stdout.strip().splitlines()[-1]


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


# --------------------------------------------------------------------------
# 6. it is reproducible: the tie-break is a rule, not the interpreter
# --------------------------------------------------------------------------

def test_the_tally_is_ordered_the_same_way_whatever_order_it_arrives_in():
    """``canonical_order`` must be a function of the TALLY and nothing else.

    Constructed input, and the detector is a pure predicate, so requirement 2
    is mechanical: the same tally is built four times with its keys inserted in
    four different orders — which is what a differently-seeded interpreter hands
    ``seats.eligible_parties``, since that function iterates
    ``set(ward_votes) | set(pr_votes)`` — and the canonical order must be one
    order, while the unordered dict must be four.

    The tie is the point: ``B`` and ``A`` carry the SAME vote total, so
    ``seats.allocate``'s ``(-remainder, -combined)`` key cannot separate them
    and its stable sort falls back to insertion order. Name is the residual.
    """
    tally = {"A": 100, "B": 100, "C": 250, "D": 7}
    permutations = [("A", "B", "C", "D"), ("B", "A", "D", "C"),
                    ("D", "C", "B", "A"), ("C", "D", "A", "B")]
    built = [{k: tally[k] for k in order} for order in permutations]

    canonical = {tuple(BM.canonical_order(d)) for d in built}
    assert len(canonical) == 1, (
        f"`canonical_order` returned {len(canonical)} different orders for one "
        f"tally: {sorted(canonical)}. It is not canonical, so the last "
        f"largest-remainder seat is still decided by PYTHONHASHSEED.")
    assert tuple(BM.canonical_order(built[0])) == ("C", "A", "B", "D"), (
        "the rule is (most votes first, then by NAME). A tied pair must come "
        "out in name order or the residual tie-break has changed, and every "
        "figure quoted against this reference moves with it.")

    # THE CONSTRUCTED VIOLATION: the same dicts without the rule. If these
    # agree, the four permutations are not exercising the defect and the
    # assertion above is vacuous.
    unruled = {tuple(d) for d in built}
    assert len(unruled) == len(permutations), (
        f"the four constructed tallies produced only {len(unruled)} distinct "
        f"key orders, so they do not demonstrate the defect and the canonical "
        f"assertion above proves nothing. Fix the fixture, not the bound.")


def test_the_reference_returns_the_identical_council_in_every_fresh_process():
    """⛔ THE CLAIM THE DOCSTRING GOT WRONG: same inputs, same council, in a
    NEW interpreter, at any hash seed.

    This is the one that blocks a canonical measurement. Before
    ``canonical_order``, Johannesburg 2021 came back with a seat error of 128 or
    130 depending on how the interpreter hashed strings that morning — 8 runs to
    6 over fourteen starts — and the 24-city-year panel totalled 837, 839 or 841
    for the same reason. A reference that moves between runs cannot anchor
    anything, and agreement between two runs of it is not evidence of anything
    either.

    Requirement 2 is supplied per-test because the detector is a subprocess:
    the same harness runs the same child with ``canonical_order`` replaced by
    ``dict`` — the defect exactly — and that leg must produce two different
    councils, or this test cannot see what it claims to have ruled out.
    """
    _context()          # skips here rather than in a child if there is no data
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "one_council.py"
        script.write_text(_CHILD % (CITY, TARGET))

        fixed = {seed: _council_in_a_fresh_process(script, seed)
                 for seed in HASH_SEEDS[:3]}
        assert len(set(fixed.values())) == 1, (
            "the reference returned different councils from identical inputs "
            "in different processes:\n"
            + "\n".join(f"  PYTHONHASHSEED={s}: {c[:160]}"
                        for s, c in fixed.items())
            + "\n\n  Something in the path is still ordered by a set of "
              "strings. `canonical_order` covers `seats.eligible_parties`; a "
              "second source would have to be found the same way.")
        assert fixed[HASH_SEEDS[0]].count('"') > 4, (
            f"the child printed {fixed[HASH_SEEDS[0]]!r}, which is not a "
            f"council. Three identical empty answers are not determinism.")

        # the constructed violation, stopping as soon as it has disagreed
        broken: set[str] = set()
        for seed in HASH_SEEDS:
            broken.add(_council_in_a_fresh_process(script, seed, tie_off=True))
            if len(broken) > 1:
                break
    assert len(broken) > 1, (
        f"with `canonical_order` removed the reference STILL returned one "
        f"council across PYTHONHASHSEED {', '.join(HASH_SEEDS)}, so this test "
        f"has not been shown able to detect the defect it rules out and its "
        f"pass above means nothing.\n"
        f"\n"
        f"  The seeds are a fixture, not a fact: they were picked in 2026-09-13 "
        f"because 0 and 4 straddled the ActionSA/CHANGE tie. If the ballot, the "
        f"arrival budget or the party canon has moved, a different pair "
        f"straddles it now — re-pick them by running the child under "
        f"TIE_OFF=1 across a range of seeds. Do NOT delete this leg.")


def test_the_last_seat_is_an_exact_tie_and_the_name_rule_is_what_decides_it():
    """ActionSA's single seat in this reference is a coin toss that the
    tie-break froze, and the docstring now says so. This is what licenses that
    sentence — and bounds it.

    ``ASA`` and ``CHANGE`` both nominated in 134 of 135 wards, so
    :func:`benchmarks.newcomer_shares` gives them the SAME share, the flat
    geography gives them the SAME votes in every voting district, and the
    allocator's ``(-remainder, -combined)`` key cannot tell them apart. Exactly
    one of them takes the last seat of the shortfall.

    Constructed counterfactual rather than an observation: the rule is mirrored
    — same key, name descending — and the seat must move to the other party and
    nowhere else. If it does not move, the seat is not decided by the tie-break
    and the docstring's warning is wrong in the other direction.
    """
    ctx = _context()
    straight = BM.uniform_swing_roster(ctx, draws=1)[0][0]

    real = BM.canonical_order
    try:
        BM.canonical_order = lambda c: {p: c[p] for p in sorted(
            sorted(c, reverse=True), key=lambda p: -c[p])}
        mirrored = BM.uniform_swing_roster(ctx, draws=1)[0][0]
    finally:
        BM.canonical_order = real

    assert straight.get("ASA", 0) == ASA_SEATS_IN_THE_REFERENCE
    assert straight.get(ASA_TIED_WITH, 0) == 0
    assert mirrored.get("ASA", 0) == 0, (
        f"mirroring the NAME half of the tie-break left ActionSA on "
        f"{mirrored.get('ASA', 0)} seats. Either the tie with {ASA_TIED_WITH} "
        f"has gone — in which case the docstring's 'coin toss' warning is now "
        f"false and must be rewritten — or the mirror is not reaching the "
        f"allocator.")
    assert mirrored.get(ASA_TIED_WITH, 0) == ASA_SEATS_IN_THE_REFERENCE, (
        f"the seat ActionSA lost did not go to {ASA_TIED_WITH}. The pair is no "
        f"longer the straddling tie group and the quoted figures are about a "
        f"different election than the one this code runs.")

    moved = {p for p in set(straight) | set(mirrored)
             if straight.get(p, 0) != mirrored.get(p, 0)}
    assert moved == {"ASA", ASA_TIED_WITH}, (
        f"mirroring the tie-break moved {sorted(moved)}, not just the tied "
        f"pair. The arbitrary component of this reference is wider than the "
        f"one seat the docstring declares, and the declaration is now the "
        f"stale half.")
    assert sum(straight.values()) == sum(mirrored.values()) == ctx.council


# --------------------------------------------------------------------------
# 7. the ActionSA figures, pinned where they are quoted
# --------------------------------------------------------------------------

def test_the_action_sa_figures_quoted_in_the_docstring_are_the_measured_ones():
    """⛔ THE SECOND CLAIM THAT WAS WRONG. ``uniform_swing_roster`` said
    ActionSA "takes one seat" and left it there. It took one seat or none
    depending on the interpreter; it is sixth-EQUAL of 32 newcomers, not
    singular; and the PA, which actually won 8 seats, takes 0 while five shells
    take one each. All of that is now in the docstring and all of it is here.

    **This is a drift guard on PROSE, not a standard of correctness** — see the
    note beside the constants. Nothing here asserts the reference is right; the
    published result appears only as the thing being missed.

    Population and both directions (requirement 0): the claim is about the
    newcomer half of the roster split, so the newcomer set is what is scanned,
    bounded two-sidedly against the roster it came out of, and the ranking is
    asserted in both directions — how many parties are strictly above ActionSA
    AND how many are tied with it. Only the first was ever quoted, which is how
    "one seat" got written about a two-way tie.
    """
    ctx = _context()
    on_ballot, newcomers, reach = BM.roster_split(ctx)
    entry = BM.newcomer_shares(ctx, newcomers, reach)
    scanned(newcomers, of=len(on_ballot) + len(newcomers),
            low=0.2, high=0.7, what="roster newcomers at this target",
            denominator="every party on the target's ballot")

    assert abs(reach["ASA"] * JHB_2021_WARDS - ASA_WARDS_CONTESTED) < 1e-9, (
        f"ActionSA's ward reach is {reach['ASA']:.6f} of {JHB_2021_WARDS} "
        f"wards, not {ASA_WARDS_CONTESTED}. Every figure the docstring quotes "
        f"is downstream of this one.")
    assert abs(entry["ASA"] - ASA_ENTRY_SHARE) < 5e-8, (
        f"ActionSA enters at {entry['ASA']:.6%}, not {ASA_ENTRY_SHARE:.6%}. "
        f"The budget or the split has moved and the docstring's 0.1638% is "
        f"stale.")

    above = [p for p in newcomers if reach.get(p, 0.0) > reach["ASA"]]
    tied = [p for p in newcomers
            if p != "ASA" and reach.get(p, 0.0) == reach["ASA"]]
    assert len(above) == ASA_NEWCOMERS_STRICTLY_ABOVE, (
        f"{len(above)} newcomers now out-reach ActionSA, not "
        f"{ASA_NEWCOMERS_STRICTLY_ABOVE}: {sorted(above)}")
    assert tied == [ASA_TIED_WITH], (
        f"ActionSA is tied on reach with {tied}, not [{ASA_TIED_WITH!r}]. "
        f"'sixth-equal of 32' is the docstring's phrase and it is now wrong.")
    assert all(reach[p] == 1.0 for p in above), (
        "the parties ranked above ActionSA are no longer the full-slate ones, "
        "so the docstring's explanation of WHY it ranks sixth is stale even if "
        "the count is not.")

    seats = BM.uniform_swing_roster(ctx, draws=1)[0][0]
    actual, _winners = B.actual_result(
        Path("data/raw/elections") / ctx.spec["actual"], ctx.council)
    assert seats.get("ASA", 0) == ASA_SEATS_IN_THE_REFERENCE
    assert actual["ASA"] == ASA_SEATS_ACTUAL
    assert seats.get("PA", 0) == PA_SEATS_IN_THE_REFERENCE, (
        f"the PA takes {seats.get('PA', 0)} seats in this reference. The "
        f"docstring's statement that largest-remainder hands its seats to "
        f"shells is about a 0, and it is no longer a 0.")
    assert actual["PA"] == PA_SEATS_ACTUAL, (
        f"the PA won {actual['PA']} seats, not {PA_SEATS_ACTUAL}; the "
        f"docstring quotes the published figure and it does not match the "
        f"file.")
    shells = [p for p in newcomers if p != "ASA" and seats.get(p, 0) > 0]
    assert len(shells) == ASA_NEWCOMERS_STRICTLY_ABOVE, (
        f"{len(shells)} newcomers other than ActionSA take a seat, not "
        f"{ASA_NEWCOMERS_STRICTLY_ABOVE}: {sorted(shells)}. 'Six of those "
        f"thirty-two take a seat each' is the docstring's count.")


def test_the_whole_arrival_budget_is_five_seats_against_forty_four():
    """**The decisive argument, and the one the docstring now leads with.**

    The reference cannot size ActionSA because of the CEILING, not because of
    the split. The arrival budget is what every newcomer takes BETWEEN THEM, so
    the most any construction in this family can give one party is all of it —
    and measured through this same allocator that is
    ``WHOLE_BUDGET_SEATS`` seats of 270 against 44. No covariate, PR-list length
    included, moves a number that is bounded before the covariate is reached.

    Constructed, not observed: the party is synthetic and holds the budget by
    being the only newcomer, so the bound does not depend on which parties
    happened to be on this ballot. That is what makes it an argument about the
    family rather than about 2021.
    """
    ctx = _context()
    ghost = "ROSTER_ONLY_CEILING_PARTY"
    real = pools.contesting_parties
    try:
        pools.contesting_parties = lambda _city, _year: set(ctx.universe) | {ghost}
        seats = BM.uniform_swing_roster(ctx, draws=1)[0][0]
    finally:
        pools.contesting_parties = real

    actual, _winners = B.actual_result(
        Path("data/raw/elections") / ctx.spec["actual"], ctx.council)
    assert seats[ghost] == WHOLE_BUDGET_SEATS, (
        f"a single party holding the ENTIRE measured arrival budget "
        f"({BM.arrival_budget(ctx.target):.4%} of the city) takes "
        f"{seats[ghost]} seats, not {WHOLE_BUDGET_SEATS}. The docstring's "
        f"ceiling argument quotes this number.")
    assert seats[ghost] < actual["ASA"] / 8, (
        f"the ceiling is no longer an order of magnitude below ActionSA's "
        f"{actual['ASA']} seats, so 'even handing one party the entire budget "
        f"is 8x short' has stopped being true and the argument has to be "
        f"remade rather than re-worded.")



# ---------------------------------------------------------------------------
# MERGERS (F5) — the roster decides which partner inherits, and the transfer is
# r × P. audits/2026-09-29-mergers/SPEC.md §2, JUDGEMENT-CALLS §O1.
#
# ⚠️ WHY THESE ASSERT SHARES, NOT SEATS. The prereg's seat prediction ("RISE up
# 0 to 2 seats") is satisfied by a transfer of zero, so a seat check cannot
# tell a working merger from a silent no-op. Every test below asserts the
# moved share itself.
# ---------------------------------------------------------------------------
def _toy_merger(date="2020-01-01"):
    import datetime as _dt
    return pools.Merger(frozenset({"AAA", "BBB"}),
                        _dt.date.fromisoformat(date), "constructed")


def test_a_merger_moves_retention_times_the_predecessor_and_nothing_else():
    """r × P reaches the successor, (1 − r) × P stays, nothing else moves."""
    shares = {"AAA": 0.10, "BBB": 0.02, "CCC": 0.88}
    per_vd = {"v1": {"AAA": 0.2, "BBB": 0.05, "CCC": 0.75},
              "v2": {"BBB": 0.01, "CCC": 0.99}}
    moved = {}
    for r in (0.0, 0.5, 0.75, 1.0):
        out, vds, applied = pools.apply_mergers(
            shares, {"AAA", "CCC"}, "2021", per_vd=per_vd, retention=r,
            mergers=(_toy_merger(),))
        moved[r] = out["AAA"] - shares["AAA"]
        assert abs(moved[r] - r * shares["BBB"]) < 1e-15, (r, out)
        assert abs(out["BBB"] - (1 - r) * shares["BBB"]) < 1e-15, (r, out)
        assert out["CCC"] == shares["CCC"], "a non-partner moved"
        assert abs(sum(out.values()) - sum(shares.values())) < 1e-15
        # Per VD, the same fraction — including a VD where AAA polled nothing.
        assert abs(vds["v1"]["AAA"] - (0.2 + r * 0.05)) < 1e-15
        assert abs(vds["v2"].get("AAA", 0.0) - r * 0.01) < 1e-15
        assert len(applied) == 1 and abs(applied[0]["moved"] - r * 0.02) < 1e-15
    assert shares == {"AAA": 0.10, "BBB": 0.02, "CCC": 0.88}, "input mutated"
    # r = 0 is the no-op; each other r is distinguishable from it and from the
    # next. This is the discrimination the seat prediction lacks.
    assert moved[0.0] == 0.0
    assert len({round(v, 12) for v in moved.values()}) == 4, moved


def test_a_merger_never_creates_a_record_the_successor_lacks():
    """Owner, DESIGN-decided §10: only records the successor already holds."""
    lacks = {"BBB": 0.02, "CCC": 0.98}
    out, _, applied = pools.apply_mergers(
        lacks, {"AAA", "CCC"}, "2021", retention=0.75,
        mergers=(_toy_merger(),))
    assert out == lacks and applied == [], (
        "the successor had no record and was given one")
    # Reverted: the same call with a record to add to transfers.
    holds = {"AAA": 1e-6, **lacks}
    out, _, applied = pools.apply_mergers(
        holds, {"AAA", "CCC"}, "2021", retention=0.75,
        mergers=(_toy_merger(),))
    assert applied and abs(out["AAA"] - (1e-6 + 0.75 * 0.02)) < 1e-15


def test_the_roster_decides_which_partner_inherits():
    """No successor is named in code: swap the roster and the direction swaps."""
    shares = {"AAA": 0.10, "BBB": 0.02, "CCC": 0.88}
    m = (_toy_merger(),)
    one = pools.apply_mergers(shares, {"AAA"}, "2021", retention=1.0,
                              mergers=m)[2]
    other = pools.apply_mergers(shares, {"BBB"}, "2021", retention=1.0,
                                mergers=m)[2]
    assert [(a["predecessor"], a["successor"]) for a in one] == [("BBB", "AAA")]
    assert [(a["predecessor"], a["successor"]) for a in other] == [("AAA", "BBB")]
    for roster, why in (({"AAA", "BBB"}, "both on the ballot"),
                        ({"CCC"}, "neither on the ballot"),
                        (set(), "roster unknown")):
        out, _, applied = pools.apply_mergers(shares, roster, "2021",
                                              retention=1.0, mergers=m)
        assert out == shares and not applied, why
    # Dated on or after the target's polling day: not yet a merger.
    late = (_toy_merger(str(cityconfig.CALENDAR["2021"].date)),)
    assert not pools.apply_mergers(shares, {"AAA"}, "2021", retention=1.0,
                                   mergers=late)[2]
    # Two partners on the ballot and one off: refused, not guessed.
    import datetime as _dt
    three = (pools.Merger(frozenset({"AAA", "BBB", "CCC"}),
                          _dt.date(2020, 1, 1), "constructed"),)
    try:
        pools.apply_mergers(shares, {"AAA", "CCC"}, "2021", mergers=three)
    except pools.MergerRefused:
        pass
    else:
        raise AssertionError("an ambiguous merger was applied")


def test_the_declared_mergers_move_the_johannesburg_2026_baseline_by_r_times_p():
    """On the real 2024 baseline and the declared 2026 roster.

    RISE gains r × GOOD, ActionSA gains r × Forum 4 Service Delivery, and after
    the off-ballot drop no other party's share differs from the unmerged run.
    The predecessors are read off the declarations, not typed here.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.use_target("2026")
    roster = set(pools.declared_roster(city, target)["parties"])
    votes, _ = M.load(Path("data/raw/elections")
                      / target.results(target.previous_npe), None)
    raw = M.citywide(votes)
    r = pools.MERGER_RETENTION
    merged, _, applied = pools.apply_mergers(raw, roster, target.year)
    pairs = {(a["predecessor"], a["successor"]) for a in applied}
    expected = set()
    for m in pools.MERGERS:
        on = [p for p in m.parties if p in roster]
        off = [p for p in m.parties if p not in roster]
        if len(on) == 1 and off and raw.get(on[0], 0) > 0:
            expected |= {(p, on[0]) for p in off if raw.get(p, 0) > 0}
    assert pairs == expected and len(expected) == len(pools.MERGERS), (
        pairs, expected)
    for pred, succ in pairs:
        assert abs(merged[succ] - (raw[succ] + r * raw[pred])) < 1e-15
    import levels
    drop_raw = set(levels.absent_from_ballot(raw, roster))
    drop_merged = set(levels.absent_from_ballot(merged, roster))
    assert drop_raw == drop_merged, "the merger changed who is dropped"
    succs = {s for _, s in pairs}
    moved = [p for p in raw if p not in drop_raw and p not in succs
             and merged[p] != raw[p]]
    assert not moved, f"a party outside every merger moved: {moved}"


def _two_mergers_into_one_successor():
    """AAA on the ballot; BBB and CCC off it, each merged into AAA.

    Built through `apply_mergers`, so each row's ``moved`` is the real r × P
    and the helper's masses are on the footing `emit_pools` gives them.
    Vectors sum to 1, as fitted compositions do, so `merged_vector`'s
    renormalisation is the identity and cannot mask or fake a difference.
    """
    import datetime as _dt
    import numpy as np
    d = _dt.date(2020, 1, 1)
    m_b = pools.Merger(frozenset({"AAA", "BBB"}), d, "constructed")
    m_c = pools.Merger(frozenset({"AAA", "CCC"}), d, "constructed")
    shares = {"AAA": 0.10, "BBB": 0.04, "CCC": 0.06, "DDD": 0.80}
    vecs = {"AAA": np.array([0.7, 0.2, 0.1]),
            "BBB": np.array([0.1, 0.8, 0.1]),
            "CCC": np.array([0.1, 0.1, 0.8])}
    return m_b, m_c, shares, vecs


def _blend(order, shares, vecs, retention):
    _, _, applied = pools.apply_mergers(shares, {"AAA", "DDD"}, "2021",
                                        retention=retention, mergers=order)
    composition = {p: v.copy() for p, v in vecs.items()}
    merger_vectors = {m["predecessor"]: composition[m["predecessor"]]
                      for m in applied}
    pools.blend_merger_vectors(composition, dict(shares), merger_vectors,
                               applied)
    return composition["AAA"], applied


def test_two_mergers_into_one_successor_give_the_mass_weighted_average():
    """Ultra review 3 on PR #17: the second merger into one successor was
    blended against the successor's ORIGINAL share although its vector already
    carried the first transfer, so the second predecessor was over-weighted.

    The emitted vector must be the closed-form mass-weighted average of all
    three, (P_A·v_A + m_B·v_B + m_C·v_C) / (P_A + m_B + m_C), in either order.
    """
    import numpy as np
    m_b, m_c, shares, vecs = _two_mergers_into_one_successor()
    r = 0.75
    got_bc, applied = _blend((m_b, m_c), shares, vecs, r)
    got_cb, _ = _blend((m_c, m_b), shares, vecs, r)
    assert len(applied) == 2 and {a["successor"] for a in applied} == {"AAA"}
    assert all(a["vector_blended"] for a in applied), applied
    mb, mc = r * shares["BBB"], r * shares["CCC"]
    closed = ((shares["AAA"] * vecs["AAA"] + mb * vecs["BBB"]
               + mc * vecs["CCC"]) / (shares["AAA"] + mb + mc))
    assert np.allclose(got_bc, closed, atol=1e-12, rtol=0), (got_bc, closed)
    assert np.allclose(got_cb, got_bc, atol=1e-12, rtol=0), (got_cb, got_bc)

    # It can see: the pre-fix rule (every blend against the ORIGINAL share)
    # differs from the closed form on this input by far more than tolerance,
    # so this test would have gone red on it.
    old = vecs["AAA"]
    for pred, moved in (("BBB", mb), ("CCC", mc)):
        old = (shares["AAA"] * old + moved * vecs[pred]) / (shares["AAA"] + moved)
    assert np.abs(old - closed).max() > 1e-3, (old, closed)


def test_the_johannesburg_2026_mergers_have_distinct_successors():
    """The declared mergers do not exercise the running mass: each successor
    is visited once, so the blend equals a single `merged_vector` against its
    pre-merger share, exactly as before ultra review 3's fix."""
    import numpy as np
    city = cityconfig.use("joburg")
    target = cityconfig.use_target("2026")
    roster = set(pools.declared_roster(city, target)["parties"])
    votes, _ = M.load(Path("data/raw/elections")
                      / target.results(target.previous_npe), None)
    raw = M.citywide(votes)
    _, _, applied = pools.apply_mergers(raw, roster, target.year)
    succs = [a["successor"] for a in applied]
    assert applied and len(set(succs)) == len(succs), succs
    rng = np.random.default_rng(0)
    parties = set(succs) | {a["predecessor"] for a in applied}
    vecs = {p: (lambda v: v / v.sum())(rng.random(4)) for p in parties}
    composition = {p: v.copy() for p, v in vecs.items()}
    pools.blend_merger_vectors(
        composition, dict(raw), {a["predecessor"]: vecs[a["predecessor"]]
                                 for a in applied}, applied)
    for a in applied:
        single = pools.merged_vector(vecs[a["successor"]], raw[a["successor"]],
                                     vecs[a["predecessor"]], a["moved"])
        assert np.array_equal(composition[a["successor"]], single)


def test_every_consumer_the_spec_names_calls_apply_mergers():
    """The leak guard: one definition, called at every declared consumer.

    Scans `src/` for calls to `apply_mergers` and compares the enclosing
    functions with `pools.MERGER_CONSUMERS` in BOTH directions. A consumer that
    drops the call would forecast from an unmerged baseline while
    `theta_residual` (or the spec) measured a merged one, which is the two-
    baselines defect of MODEL-LOG §1.124.
    """
    import ast

    from collections import Counter

    def callers(sources: dict[str, str], name: str = "apply_mergers") -> Counter:
        """Calls to ``name`` per enclosing function (``module.function``).
        ONE matcher, used for the set, the counts and the self-checks."""
        found: Counter = Counter()
        for mod, text in sources.items():
            for fn in ast.walk(ast.parse(text)):
                if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for node in ast.walk(fn):
                    if isinstance(node, ast.Call):
                        f = node.func
                        called = (f.attr if isinstance(f, ast.Attribute)
                                  else getattr(f, "id", None))
                        if called == name:
                            found[f"{mod}.{fn.name}"] += 1
        return found

    src = ROOT / "src"
    sources = {p.stem: p.read_text() for p in sorted(src.glob("*.py"))}
    scanned(sources, of=len(list(src.glob("*.py"))), low=1.0, high=1.0,
            what="src modules parsed", denominator="src/*.py")
    got = callers(sources)
    assert set(got) == set(pools.MERGER_CONSUMERS), (
        f"declared, not calling: {sorted(set(pools.MERGER_CONSUMERS) - set(got))}; "
        f"calling, not declared: {sorted(set(got) - set(pools.MERGER_CONSUMERS))}")
    # PER CALL, not per function (F10 census, RESULTS.md): `run_model` makes
    # two calls, the national baseline and the preceding local result, and a
    # per-function set stayed green with either one removed. The counts are
    # the arity of each consumer's use, stated here because `pools.py` holds
    # the consumer list and editing it would re-key every spec. A call that
    # is present but disabled (`if False:`, a discarded result) is invisible
    # to any source scan; `test_the_run_model_mergers_reach_the_spine` is the
    # behavioural guard for that.
    expected_calls = {"montecarlo.run_model": 2, "pools.emit_pools": 1,
                      "theta_residual._residuals_cached": 1}
    assert dict(got) == expected_calls, (
        f"apply_mergers calls per consumer: {dict(got)}, expected {expected_calls}")
    # ... and emit_pools applies the vector blend, which nothing else checked.
    assert callers(sources, "blend_merger_vectors").get("pools.emit_pools") == 1, \
        "emit_pools no longer calls blend_merger_vectors"

    # It can see: remove a call from one consumer, remove ONE of run_model's
    # two calls, and add a call elsewhere.
    cut = dict(sources)
    cut["theta_residual"] = cut["theta_residual"].replace(
        "pools.apply_mergers(", "pools.dict_passthrough(")
    assert "theta_residual._residuals_cached" not in callers(cut)
    one = dict(sources)
    marker = "_pools_merge.apply_mergers(pc,"
    assert one["montecarlo"].count(marker) == 1, "the local-result call moved"
    one["montecarlo"] = one["montecarlo"].replace(marker, "_pools_merge.passthrough(pc,")
    assert callers(one)["montecarlo.run_model"] == 1
    extra = dict(sources)
    extra["sweep"] = extra.get("sweep", "") + (
        "\n\ndef _leaky():\n    return pools.apply_mergers({}, set(), '2026')\n")
    assert "sweep._leaky" in callers(extra)
    noblend = dict(sources)
    noblend["pools"] = noblend["pools"].replace(
        "    blend_merger_vectors(composition,", "    _no_blend(composition,")
    assert "pools.emit_pools" not in callers(noblend, "blend_merger_vectors")


_SPINE_PROBE = r"""
import argparse, contextlib, io, json, sys, tempfile
sys.path.insert(0, "src")
import cityconfig, montecarlo as M, pools
out = {}
for label, mergers in (("declared", pools.MERGERS), ("none", ())):
    pools.MERGERS = mergers
    city = cityconfig.use("joburg"); target = cityconfig.use_target("2026")
    M.apply_city(city)
    sc = M.load_scenario(argparse.Namespace(config=None, set=["seed=20261104"],
        draws=50, seed=None, city="joburg", target="2026"))
    with tempfile.TemporaryDirectory() as d, contextlib.redirect_stdout(io.StringIO()):
        M.run_model(target, sc, verbose=False, run_dir=d)
        lv = json.load(open(d + "/20_spine.json"))["level"]
    out[label] = {"RISE": lv.get("RISE"), "ASA": lv.get("ASA"),
                  "mergers": [m["successor"] for m in sc.get("_mergers") or []]}
print(json.dumps(out))
"""


def test_the_run_model_mergers_reach_the_spine():
    """Behavioural guard for both `apply_mergers` calls in `run_model`.

    A source scan cannot see a call that is present but disabled. So the
    model is run at Johannesburg 2026 with the declared mergers and with none,
    in a fresh process (it reads module globals), and the spine is read from
    the trace. RISE takes GOOD's transfer only through the NATIONAL call (it
    has no local record); ASA's spine level is its local level, so it moves
    only through the LOCAL call (MODEL-LOG §1.275, census C5 and C6). Both
    must differ. The census showed each call removed leaves its party's level
    unchanged.
    """
    r = subprocess.run([sys.executable, "-c", _SPINE_PROBE], cwd=ROOT,
                       capture_output=True, text=True,
                       env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"})
    assert r.returncode == 0, r.stderr[-2000:]
    got = json.loads(r.stdout.strip().splitlines()[-1])
    dec, none = got["declared"], got["none"]
    assert sorted(dec["mergers"]) == ["ASA", "RISE"] and none["mergers"] == [], got
    assert dec["RISE"] > none["RISE"], (
        f"RISE's spine level did not rise with the mergers ({none['RISE']} -> "
        f"{dec['RISE']}): the national-baseline call has no effect")
    assert dec["ASA"] > none["ASA"], (
        f"ASA's spine level did not rise with the mergers ({none['ASA']} -> "
        f"{dec['ASA']}): the preceding-local call has no effect")


def test_the_merger_mechanism_names_no_party():
    """DESIGN-decided §8: mergers are data; no party is singled out in code.

    No string literal in `apply_mergers` or `merged_vector` may be a party a
    declaration names. Constructed violation: the same scan over a copy of the
    function with one party typed into it must find it.
    """
    import ast
    import inspect
    import textwrap
    partners = {p for m in pools.MERGERS for p in m.parties}
    assert partners, "no declared merger: the scan would look at nothing"

    def literals(fn_source: str) -> set[str]:
        tree = ast.parse(textwrap.dedent(fn_source))
        body = tree.body[0]
        doc = ast.get_docstring(body)
        return {n.value for n in ast.walk(body)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value != doc}

    for fn in (pools.apply_mergers, pools.merged_vector):
        hit = literals(inspect.getsource(fn)) & partners
        assert not hit, f"{fn.__name__} names {sorted(hit)}"
    one = sorted(partners)[0]
    planted = inspect.getsource(pools.apply_mergers).replace(
        "out = dict(shares)", f"out = dict(shares); _x = {one!r}", 1)
    assert literals(planted) & partners == {one}
    lo, hi = pools.MERGER_RETENTION_RANGE
    assert lo <= pools.MERGER_RETENTION <= hi


def test_a_merged_vector_is_the_mass_weighted_blend_and_a_zero_transfer_is_a_no_op():
    import numpy as np
    succ = np.array([0.6, 0.2, 0.1, 0.1])
    pred = np.array([0.1, 0.4, 0.1, 0.4])
    assert np.array_equal(pools.merged_vector(succ, 0.015, pred, 0.0), succ)
    got = pools.merged_vector(succ, 0.015, pred, 0.005)
    want = (0.015 * succ + 0.005 * pred) / 0.020
    assert np.allclose(got, want, atol=1e-15) and abs(got.sum() - 1) < 1e-12


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
