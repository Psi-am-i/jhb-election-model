"""THE PRIOR-LOCAL RECORD MUST FAIL CLOSED — POOLS-REEMIT-QUEUE entry 21.

**The claim: no run weighs a roster deletion against a record it could not
read.**

``pools._npe_citywide_for`` returned ``{}`` for **four causes the caller could
not tell apart** — no ``CALENDAR[year].results`` template; the file absent at
both candidate paths; the election in ``levels.HELD_BACK``; and a file that was
read and totalled zero. **Only the last means "read it, and the mass really is
zero".** Two consumers in :func:`pools.resolve_roster` then read that one value
in OPPOSITE directions:

* the ``complete = true`` deletion ceiling scored ``dropped_mass`` at **0.0**,
  so ``dropped_mass > ROSTER_DROP_CEILING`` was false and the refusal written to
  stop a half-typed nomination list **never fired**. Reproduced at joburg 2026
  on the top six of 2021 marked ``complete = true``: record reachable ->
  REFUSED, 48 parties holding 7.77% of the 2021 vote, five times the ceiling;
  record unreachable -> ADMITTED, printing "0.00%".
* the §K2 prior-local floor came out empty, so the incomplete-roster union
  re-admitted every party the floor had excluded.

This is the repository's own empty-record-vs-unreachable-record class, one layer
below ``tests/test_roster_fails_closed.py`` — which separates published /
not-yet-held / unreadable for ``contesting_parties``, the ROSTER path, and did
nothing of the kind for ``_npe_citywide_for``, the MASS path the deletion is
actually weighed on.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4's rule for an absence claim:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS.** The population is every target the
   emit loop issues, DERIVED — ``[structure.by_year]`` for the backtest targets
   plus each city's own ``[structure].election_date`` for the unheld one — and
   asserted EQUAL to what was scanned, not merely contained in it. *Forward*:
   every target resolves to state ``read``. *Reverse*: every cause the state enum
   can return is exercised by a case below, **iterated from
   ``pools.NPE_CITYWIDE_STATES`` rather than listed by hand**, because the
   register->code direction is the one this repository's guards keep missing.
1. **IT LOOKED.** ``_support.election_files_read`` watches the real I/O: the
   fitting year's file must actually be OPENED, twice in two calls (the helper is
   deliberately un-memoised, and this spy goes blind the day that changes), and
   the population is bounded **two-sidedly as a fraction of a computed
   denominator** — ``len(prior_local) / len(contesting_parties(city, fitting))``.
2. **IT CAN SEE — AND GOES QUIET WHEN REVERTED.** Four constructed causes. ⛔ The
   fourth is the discriminator: **a record that is read and genuinely empty must
   still ADMIT.** The naive repair — refuse whenever ``prior_local`` is empty —
   passes the first three and fails that one, and would have been certified by a
   guard without it.
3. **CONSTRUCTED INPUT, NOT OBSERVED.** Every failure is injected by redirecting
   ``CALENDAR[year].results`` or by a temporary CSV. Nothing under ``data/`` is
   moved: it is gitignored, shared with every other worker, and nothing restores
   it.

And the thing that is not in the rule and matters most here:
``test_resolve_roster_reads_the_state_through_the_checked_helper`` patches
``_npe_citywide_state`` to a sentinel state and asserts the refusal propagates.
Without it the helper could be perfectly correct and the ceiling still be weighed
on something else — and ``resolve_roster`` calls it directly rather than through
``_citywide_for``, so there is a real second path to get wrong.

⛔ **ASSERTS STATES, COUNTS AND MASSES — NEVER LOG TEXT.** Both consumers print a
cheerful message while doing the wrong thing.

⚠️ **What this guard cannot prove.** It exercises ``resolve_roster``, not
``emit_pools``. A spec emitted through a different path is not covered, and only
the window's own emit-and-diff closes that.

Run:
    ./.venv/bin/python tests/test_prior_local_fails_closed.py
    ./.venv/bin/python -m pytest tests/test_prior_local_fails_closed.py -q
"""

from __future__ import annotations

import contextlib
import dataclasses
import datetime
import io
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import election_files_read, run_module, scanned, skip  # noqa: E402

import cityconfig  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
TARGET = "2026"        # the live forecast: no result file, so a declared roster
FITTING = "2021"       # the year `resolve_roster` weighs the deletion against

# The share of the fitting ballot that shows up on the PR-only citywide read.
# Two-sided and as a FRACTION of a computed denominator, per `_support.scanned`:
# above 1.0 is arithmetically impossible (the PR parties are a subset of the
# ballot), and below the floor the `BallotType` filter has broken open. Measured
# 0.889-0.973 across the whole population when this was written.
PR_SHARE_LO, PR_SHARE_HI = 0.60, 1.00


# --------------------------------------------------------------------------
# the population, derived
# --------------------------------------------------------------------------

def _emit_population() -> set[tuple[str, str]]:
    """Every (city, target) the emit loop issues, taken from the configs.

    ⛔ **NEVER TYPED.** ``POOLS-REEMIT-QUEUE.md`` step 3 carried this as a count,
    the count went stale, and it sent an operator hunting a discrepancy that did
    not exist. Two sources, both of them the loop's own:

    * ``[structure.by_year.<year>]`` — the backtest targets, exactly what
      ``_support.declared_city_years`` reads.
    * ``[structure].election_date`` — the city's own unheld target.

    This is a SUPERSET of the loop as written (which emits the unheld target for
    two cities, not eight), and deliberately so: the forward claim is "every
    target reads a real record", and covering more targets than the loop can only
    strengthen it. A subset would not be safe; a superset is.
    """
    out: set[tuple[str, str]] = set()
    for path in sorted(cityconfig.CITIES_DIR.glob("*.toml")):
        raw = tomllib.loads(path.read_text())
        structure = raw.get("structure") or {}
        for year in (structure.get("by_year") or {}):
            out.add((path.stem, str(year)))
        when = structure.get("election_date")
        if when:
            out.add((path.stem,
                     str(datetime.date.fromisoformat(str(when)).year)))
    assert out, (
        f"no [structure] blocks in any of "
        f"{sorted(p.name for p in cityconfig.CITIES_DIR.glob('*.toml'))}. "
        f"The population this file scans is zero, so every claim below is "
        f"vacuous.")
    return out


def _fitting_year(slug: str, year: str) -> tuple[cityconfig.City, str]:
    """The city, and the year `emit_pools` weighs the deletion against.

    ``emit_pools`` computes ``year = from_year or target.previous_lge or
    target.year`` and hands it to ``resolve_roster``. Read from the same place
    rather than restated, so the two cannot drift.
    """
    city = cityconfig.load(slug)
    target = cityconfig.Target(city=city, year=year)
    return city, (target.previous_lge or target.year)


# --------------------------------------------------------------------------
# 0 + 1. the healthy state, over the whole population, watched at file level
# --------------------------------------------------------------------------

def test_every_emit_target_reads_a_real_prior_local_record():
    """THE FORWARD DIRECTION, AND THE POSITIVE CONTROL.

    Everything else here asserts that something bad does not happen. This
    asserts the mechanism RAN: for every target the loop issues, the fitting
    year's record resolves to state ``read``, comes back non-empty, and sums to
    one. "No deletion weighed on an unreachable record" is satisfied just as
    well by a model that never reads a record at all.

    The scanned set is asserted EQUAL to the derived population — not contained
    in it — which is the half §4 calls this repository's worst record.
    """
    population = _emit_population()
    scanned_set: set[tuple[str, str]] = set()
    for slug, year in sorted(population):
        city, fitting = _fitting_year(slug, year)
        shares, state = pools._npe_citywide_state(city.code, fitting)
        scanned_set.add((slug, year))
        assert state == "read", (
            f"{slug} {year}: the fitting year {fitting} resolved to state "
            f"{state!r}, not 'read'. Every deletion this run weighs is scored "
            f"against that record, and `resolve_roster` now REFUSES rather "
            f"than scoring it at zero — so this target cannot be emitted until "
            f"the record is restored.")
        assert shares, (
            f"{slug} {year}: the {fitting} record was read and came back EMPTY. "
            f"That is a legitimate state and it is not this panel's state; if "
            f"it is now, the PR filter or the file has changed.")
        assert abs(sum(shares.values()) - 1.0) < 1e-9, (
            f"{slug} {year}: the {fitting} citywide shares sum to "
            f"{sum(shares.values()):.9f}, not 1. They are read as a MASS and "
            f"compared against ROSTER_DROP_CEILING; a mass that does not "
            f"normalise makes that comparison meaningless.")
        # Two-sided, as a fraction of a denominator computed from the tree.
        scanned(len(shares), of=len(pools.contesting_parties(city, fitting)),
                low=PR_SHARE_LO, high=PR_SHARE_HI,
                what=f"{slug} {year}: parties on the {fitting} PR citywide read",
                denominator=f"parties on the whole {fitting} ballot")
    assert scanned_set == population, (
        f"the scan covered {sorted(scanned_set - population)} that the emit "
        f"loop does not issue, and missed {sorted(population - scanned_set)} "
        f"that it does. A guard whose population is not the claim's population "
        f"can be healthy and find nothing, in the wrong set.")


def test_the_prior_local_record_is_actually_opened_on_every_call():
    """IT LOOKED — and the spy must not go blind.

    The record is read through real file I/O, and this file's injections all
    work by making that read fail. A memo would make the second call skip the
    file, and every "the record is unreachable" injection below would then be
    asserting something about a cache. ``levels._citywide``'s docstring records
    why the memo was rejected; this asserts it, so the day someone adds one this
    test fails rather than quietly passing.
    """
    city = cityconfig.load(CITY)
    template = cityconfig.CALENDAR[FITTING].results
    if not template:
        skip(f"no {FITTING} result template in the calendar")
    name = Path(str(template).replace("{CODE}", city.code)).name

    with election_files_read() as seen:
        first, state_a = pools._npe_citywide_state(city.code, FITTING)
        opened_once = [p for _, _, p in seen if Path(p).name == name]
        second, state_b = pools._npe_citywide_state(city.code, FITTING)
    opened_twice = [p for _, _, p in seen if Path(p).name == name]

    assert state_a == state_b == "read" and first and first == second
    assert opened_once, (
        f"the {FITTING} record resolved WITHOUT OPENING {name}. Files seen: "
        f"{sorted({Path(p).name for _, _, p in seen})}")
    assert len(opened_twice) > len(opened_once), (
        f"{name} was opened {len(opened_once)} time(s) for the first call and "
        f"{len(opened_twice)} in total, so the second call did not read the "
        f"file. `_npe_citywide_state` has grown a memo — which blinds this spy "
        f"and every injection in this file, because a cached value survives the "
        f"cause being injected.")


# --------------------------------------------------------------------------
# 2. it can see — the four causes, and the discriminator
# --------------------------------------------------------------------------

@contextlib.contextmanager
def _declared(parties, *, complete: bool):
    """A constructed nomination list, WITHOUT writing into `judgements/`.

    Only the lineage path is redirected, so the real ``declared_roster`` and
    ``resolve_roster`` bodies execute. ``judgements/`` is tracked and shared.
    """
    tmp = Path(tempfile.mkdtemp()) / f"{CITY}-{TARGET}.toml"
    body = ", ".join(f'"{p}"' for p in parties)
    tmp.write_text(f"[roster]\nparties = [{body}]\n"
                   f"complete = {str(complete).lower()}\n")
    real = pools.lineage_path
    pools.lineage_path = lambda city, target: tmp
    try:
        yield tmp
    finally:
        pools.lineage_path = real


@contextlib.contextmanager
def _cause(state: str, tmpdir: Path):
    """Reach one of `_npe_citywide_state`'s states DELIBERATELY.

    Every injection redirects ``CALENDAR[FITTING].results``; nothing under
    ``data/`` is touched. The zero-total file is a real CSV whose ``BallotType``
    values miss the PR filter, which is the only way to reach ``read`` with an
    empty result.
    """
    calendar = cityconfig.CALENDAR
    original = calendar[FITTING]
    replace = dataclasses.replace
    if state == "read":
        new = original
    elif state == "no_template":
        new = replace(original, results=None)
    elif state == "absent":
        new = replace(original, results="not_in_this_checkout_{CODE}.csv")
    elif state == "held_back":
        new = original           # handled by patching the gate, below
    else:
        raise AssertionError(f"unhandled state {state!r}; the enum has grown")
    held = None
    if state == "held_back":
        import levels
        held = levels._held_back
        levels._held_back = lambda path: True
    calendar[FITTING] = new
    try:
        yield
    finally:
        calendar[FITTING] = original
        if held is not None:
            import levels
            levels._held_back = held


@contextlib.contextmanager
def _read_but_empty(tmpdir: Path):
    """A file that IS read and totals zero — the discriminating case."""
    csv_path = tmpdir / f"zero_{CITY}_{{CODE}}.csv"
    (tmpdir / f"zero_{CITY}_{cityconfig.load(CITY).code}.csv").write_text(
        "BallotType,sPartyName,Party_Votes\nWard,SOMEBODY,100\n")
    calendar = cityconfig.CALENDAR
    original = calendar[FITTING]
    calendar[FITTING] = dataclasses.replace(original, results=str(csv_path))
    try:
        yield
    finally:
        calendar[FITTING] = original


def _resolve(parties, *, complete: bool, composition, baseline):
    """Run the real `resolve_roster`. Returns a result or the refusal."""
    city = cityconfig.load(CITY)
    target = cityconfig.Target(city=city, year=TARGET)
    with _declared(parties, complete=complete):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                return pools.resolve_roster(city, target, FITTING,
                                            dict(composition), dict(baseline))
        except SystemExit as refusal:
            return refusal


def _inputs():
    """Composition and baseline built from the REAL fitting record.

    Read once through an unpatched path, so the mass the ceiling ought to see is
    known independently of whatever the injections do to the read.
    """
    city = cityconfig.load(CITY)
    truth, state = pools._npe_citywide_state(city.code, FITTING)
    if state != "read" or not truth:
        skip(f"no readable {FITTING} record for {CITY}")
    ranked = sorted(truth, key=lambda p: -truth[p])
    composition = {p: None for p in truth}
    return truth, ranked, composition


def test_every_unreachable_cause_refuses_and_goes_quiet_when_reverted():
    """IT CAN SEE — every cause the enum can return, iterated FROM the enum.

    ⛔ The list is not typed here. ``pools.NPE_CITYWIDE_UNREACHABLE`` is
    iterated, so a fifth cause added to the helper and not handled by
    ``resolve_roster`` turns this red instead of slipping through — the
    register->code direction §4 names as this repository's blindest.

    After each injection it is reverted and the ceiling must fire again
    IDENTICALLY: a detector that cannot go quiet is not a detector.
    """
    truth, ranked, composition = _inputs()
    declared = ranked[:6]
    baseline = dict(truth)
    tmpdir = Path(tempfile.mkdtemp())

    # The mass the ceiling ought to be weighing, computed from the unpatched
    # read — not from the message, and not from the run under test.
    deliberate = [p for p in composition if p not in declared
                  and p not in ("IND", "ENTRANT")]
    true_mass = sum(truth.get(p, 0.0) for p in deliberate)
    assert true_mass > pools.ROSTER_DROP_CEILING, (
        f"the constructed deletion holds {true_mass:.4%} of the {FITTING} "
        f"vote, at or below the {pools.ROSTER_DROP_CEILING:.1%} ceiling, so "
        f"the control below would not refuse even when healthy and every "
        f"injection here would prove nothing. Declare fewer parties.")

    control = _resolve(declared, complete=True, composition=composition,
                       baseline=baseline)
    assert isinstance(control, SystemExit), (
        f"THE CONTROL DID NOT FIRE. A `complete = true` roster deleting "
        f"{len(deliberate)} parties holding {true_mass:.4%} — above the "
        f"{pools.ROSTER_DROP_CEILING:.1%} ceiling — was ADMITTED with the "
        f"record reachable. Every injection below is vacuous.")

    assert pools.NPE_CITYWIDE_UNREACHABLE, "the unreachable enum is empty"
    for state in pools.NPE_CITYWIDE_UNREACHABLE:
        with _cause(state, tmpdir):
            shares, seen_state = pools._npe_citywide_state(
                cityconfig.load(CITY).code, FITTING)
            assert seen_state == state and not shares, (
                f"injecting {state!r} produced state {seen_state!r} with "
                f"{len(shares)} parties. The injection did not reach the branch "
                f"it names, so what follows tests nothing.")
            injected = _resolve(declared, complete=True,
                                composition=composition, baseline=baseline)
        assert isinstance(injected, SystemExit), (
            f"with the {FITTING} record UNREACHABLE ({state}), the "
            f"`complete = true` deletion of {len(deliberate)} parties holding "
            f"{true_mass:.4%} was ADMITTED. The ceiling scored it at 0.00% "
            f"because an unreachable record and an empty one were the same "
            f"value — POOLS-REEMIT-QUEUE entry 21, which is what this guard is.")
        # AND IT GOES QUIET: the identical control, after the revert.
        after = _resolve(declared, complete=True, composition=composition,
                         baseline=baseline)
        assert isinstance(after, SystemExit), (
            f"after reverting the {state!r} injection the ceiling stopped "
            f"firing, so the injection was not reverted.")


def test_a_record_that_is_read_and_genuinely_empty_still_admits():
    """⛔ THE DISCRIMINATOR, AND THE ROW THAT MAKES THIS GUARD WORTH WRITING.

    A record that was READ and genuinely holds no PR vote is not a record that
    could not be read. The naive repair — *refuse whenever ``prior_local`` is
    empty* — passes all three injections above and fails HERE, and a guard
    without this row would have certified it.

    The mass really is zero, so the deletion really is free, so the run really
    should admit it.
    """
    truth, ranked, composition = _inputs()
    declared = ranked[:6]
    tmpdir = Path(tempfile.mkdtemp())
    with _read_but_empty(tmpdir):
        shares, state = pools._npe_citywide_state(
            cityconfig.load(CITY).code, FITTING)
        assert state == "read" and not shares, (
            f"the constructed zero-total file resolved to ({len(shares)} "
            f"parties, {state!r}), not (0, 'read'). The discriminating case was "
            f"not reached: its whole point is a file that IS opened and parses "
            f"to nothing.")
        out = _resolve(declared, complete=True, composition=composition,
                       baseline=dict(truth))
    assert not isinstance(out, SystemExit), (
        f"a {FITTING} record that was READ and is genuinely empty was REFUSED: "
        f"{str(out).splitlines()[0]!r}. That is the naive repair — 'refuse on "
        f"empty' — and it deletes the distinction this entry is about.")
    roster, source, deliberate, prior_local = out
    assert source == "declared" and prior_local == {}
    expected = {p for p in composition
                if p not in declared and p not in ("IND", "ENTRANT")}
    assert deliberate == expected, (
        f"the admitted deletion covered {len(deliberate)} parties, not the "
        f"{len(expected)} outside the declared list.")


def test_the_k2_floor_refuses_on_an_unreachable_record_and_thins_on_an_empty_one():
    """THE SECOND CONSUMER, IN THE OPPOSITE DIRECTION.

    ``_local_thin`` is the §K2 floor: parties that contested the fitting year
    locally below ``PRIOR_LOCAL_FLOOR`` and polled nothing nationally are not
    assumed onto the ballot. With ``prior_local`` empty the set is empty too and
    an incomplete declared roster re-admits every one of them — a floor that
    cannot hold, from the same ``{}`` that made the ceiling unable to fire.

    Asserted on the roster SIZE, which is where the divergence shows, not on the
    message.
    """
    truth, ranked, composition = _inputs()
    # A baseline that holds only the large parties, so §K2 has something to
    # exclude: `_local_thin` needs parties present locally and absent nationally.
    baseline = {p: truth[p] for p in ranked[:8]}
    thinnable = [p for p in truth
                 if p not in baseline and truth[p] < pools.PRIOR_LOCAL_FLOOR]
    assert thinnable, (
        f"no party in the {FITTING} record is both outside the constructed "
        f"baseline and below PRIOR_LOCAL_FLOOR ({pools.PRIOR_LOCAL_FLOOR}), so "
        f"§K2 excludes nobody and this test cannot see its own subject.")

    healthy = _resolve(ranked[:6], complete=False, composition=composition,
                       baseline=baseline)
    assert not isinstance(healthy, SystemExit), str(healthy)
    thinned_roster = healthy[0]

    tmpdir = Path(tempfile.mkdtemp())
    with _read_but_empty(tmpdir):
        empty = _resolve(ranked[:6], complete=False, composition=composition,
                         baseline=baseline)
    assert not isinstance(empty, SystemExit), (
        "a READ-but-empty record must still thin normally, not refuse")
    unthinned_roster = empty[0]

    assert len(unthinned_roster) == len(thinned_roster) + len(thinnable), (
        f"with the {FITTING} record read and EMPTY the roster came to "
        f"{len(unthinned_roster)} parties against {len(thinned_roster)} on the "
        f"real record, a difference of "
        f"{len(unthinned_roster) - len(thinned_roster)} where §K2 excludes "
        f"{len(thinnable)}. The floor and the roster have stopped agreeing "
        f"about what it removes.")

    with _cause("absent", tmpdir):
        unreachable = _resolve(ranked[:6], complete=False,
                               composition=composition, baseline=baseline)
    assert isinstance(unreachable, SystemExit), (
        f"with the {FITTING} record UNREACHABLE the §K2 floor silently "
        f"re-admitted the {len(thinnable)} parties it had excluded, and the run "
        f"carried on. An absent record is not evidence that a floor excludes "
        f"nobody.")

    after = _resolve(ranked[:6], complete=False, composition=composition,
                     baseline=baseline)
    assert not isinstance(after, SystemExit), "the injection was not reverted"
    assert len(after[0]) == len(thinned_roster), (
        f"after the revert the roster is {len(after[0])} parties, not the "
        f"{len(thinned_roster)} the control gave.")


# --------------------------------------------------------------------------
# the thing that is not in the rule
# --------------------------------------------------------------------------

def test_resolve_roster_reads_the_state_through_the_checked_helper():
    """THE PROPAGATION TEST, without which the helper can be right and the
    ceiling still weighed on something else.

    ``resolve_roster`` calls ``_npe_citywide_state`` DIRECTLY — not through
    ``_citywide_for``, which tallies the same distinction into
    ``_TRANSITION_LEDGER`` and never hands it to a caller — so there is a real
    second path to get wrong. Patched to a sentinel unreachable state with
    perfectly good shares beside it: if ``resolve_roster`` is reading the shares
    and ignoring the state, it will sail through.
    """
    truth, ranked, composition = _inputs()
    real = pools._npe_citywide_state
    sentinel = pools.NPE_CITYWIDE_UNREACHABLE[0]
    pools._npe_citywide_state = lambda code, year: (dict(truth), sentinel)
    try:
        out = _resolve(ranked[:6], complete=True, composition=composition,
                       baseline=dict(truth))
    finally:
        pools._npe_citywide_state = real
    assert isinstance(out, SystemExit), (
        f"`resolve_roster` was handed state {sentinel!r} with a full set of "
        f"shares and carried on. It is reading the shares and ignoring the "
        f"state, so the repair does not reach the consumer it was written for.")

    # AND IT GOES QUIET. Asserted on BEHAVIOUR, not on the refusal's wording:
    # an INCOMPLETE roster is admitted on a reachable record and refused on an
    # unreachable one, so admitting it proves the sentinel is gone.
    after = _resolve(ranked[:6], complete=False, composition=composition,
                     baseline=dict(truth))
    assert not isinstance(after, SystemExit), (
        f"after restoring `_npe_citywide_state` an incomplete roster was still "
        f"refused ({str(after).splitlines()[0]!r}), so the patch was not "
        f"undone and every later test in this module is running against a "
        f"stub.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
