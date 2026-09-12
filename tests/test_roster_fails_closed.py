"""F7 — THE BALLOT ROSTER MUST FAIL CLOSED.

``run_model`` resolved the target's ballot roster as::

    try:
        import pools as _pools
        _roster = _pools.contesting_parties(target.city, target.year)
    except Exception:
        _roster = set()

and an empty roster is the value meaning **drop nobody**. So every defect inside
``contesting_parties`` — a renamed ``sPartyName`` column, a moved archive file, a
wrong working directory (the path it builds is relative) — silently disabled the
off-ballot drop, the mechanism that removes baseline parties which did not stand.
``run_model``'s own comment prices that at *"of the order of one invented seat,
funded out of the parties ranked 4th to 12th"*: Johannesburg 2021, thirteen
parties in the 2019 baseline not on the ballot, holding 0.42% between them.

**The empty set was also the legitimate answer for a target that has not been
held yet**, which is the state of the live 2026 forecast, so the failure was not
merely silent — it was *indistinguishable from correct behaviour*, and no
downstream consumer could have told. That is this repository's
empty-record-vs-unreachable-record class, and ``pools.stale_reason`` is handled
for it a hundred lines further down the same file with an explicit refusal to
fail open. The file held two opposite policies for one failure mode.

:func:`montecarlo.roster_for_target` now separates three states — published,
not-yet-held, and unreadable (which raises) — and records which one occurred on
``ModelRun``.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4's rule for a test that asserts
an absence. The claim "no run reaches the drawing stage with a silently empty
roster" is an absence claim, and three of the four requirements are where such
tests fail:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS.** The claim covers every target this
   harness can run, not Johannesburg. ``test_every_runnable_city_year...``
   asserts *published* over all 24 city-years ``backtest.runnable_targets``
   offers, and *not_yet_held* over every calendar LGE with no result file — the
   direction that would otherwise let the guard pass by refusing everything.
1. **IT LOOKED.** ``_support.election_files_read`` watches the real I/O of the
   real function: the target's own result file must actually be OPENED and the
   roster must come back non-empty. This is the half that stops the guard going
   blind, and it is what the exemplar (the temporal spy) adds.
   ``pools.contesting_parties`` is not memoised — it opens the file on every
   call — which is the property the spy depends on.
2. **IT CAN SEE.** Fault injection: ``contesting_parties`` is monkeypatched to
   raise, and separately to return an empty set, and the run must refuse both
   times. The spy is then re-run against the real function so a test that
   disabled the mechanism cannot leave it disabled.
3. **CONSTRUCTED INPUT, NOT AN OBSERVED ONE.** Every failure here is injected.
   Nothing asserts a property of the tree that would expire the day someone
   fixes something else.

A fourth thing, which is not in the rule and is the one that matters most here:
``test_run_model_resolves_its_roster_through_the_checked_path`` patches the
helper to a sentinel and asserts ``run_model`` propagates it. Without that, the
helper could be perfectly correct and the model still unguarded.

⛔ **ASSERTS STATES AND COUNTS, NEVER LOG TEXT.** A test pinned to a message
stays green while the arithmetic beside it is broken.

Run:
    ./.venv/bin/python tests/test_roster_fails_closed.py
    ./.venv/bin/python -m pytest tests/test_roster_fails_closed.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import election_files_read, run_module, scanned, skip  # noqa: E402

import backtest as B  # noqa: E402
import cityconfig  # noqa: E402
import levels  # noqa: E402
import montecarlo as M  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
HELD = "2021"          # a past election: a result file exists, so a roster does
UNHELD = "2026"        # the live forecast: CALENDAR[...].results is None

PUBLISHED = "published"
NOT_YET_HELD = "not_yet_held"


class Sentinel(Exception):
    """Raised by a stubbed ``roster_for_target`` and by nothing else."""


class _Args:
    """The shape ``montecarlo.load_scenario`` expects from argparse."""

    def __init__(self, draws: int):
        self.config = None
        self.set = None
        self.draws = draws
        self.seed = None


def _city():
    cityconfig.use(CITY)
    return cityconfig.load(CITY)


def _target(year: str):
    return cityconfig.Target(city=_city(), year=year)


def _roster_path(city, year: str):
    """Where ``contesting_parties`` would look, or None if nowhere."""
    template = cityconfig.CALENDAR[year].results
    return city.path("raw", "elections", template) if template else None


# --------------------------------------------------------------------------
# 1. the healthy state, watched at the file level
# --------------------------------------------------------------------------

def test_the_published_roster_is_read_from_the_targets_own_file():
    """THE POSITIVE CONTROL. A roster that is read, from the right file.

    Everything else in this file asserts that something bad does not happen.
    This asserts that the mechanism RAN — the file was opened and the answer was
    not empty — because "no silently empty roster" is satisfied just as well by a
    model that never consults a roster at all.

    The two extra checks are the ones the scan-shaped-test rule asks for:

    * **the RIGHT file.** Not "some election file was read": the target's own,
      and no other. `contesting_parties` reading `lge2016_...` while claiming to
      describe the 2021 ballot would be a leak in the opposite direction, and a
      bare "something was opened" assertion cannot see it.
    * **a second, independent reader agrees.** `levels.ballot_roster` parses the
      same file by a different route (one pass, shares and names together, for
      `theta_residual`). The two must return the same set or `run_model`'s
      baseline and `theta_residual`'s are built from different ballots — the
      defect MODEL-LOG §1.124 records. Verified equal at 22/28/57 parties for
      2011/2016/2021 when this was written.
    """
    city = _city()
    path = _roster_path(city, HELD)
    if path is None or not path.exists():
        skip(f"no {HELD} result file for {CITY} on disk")

    with election_files_read() as seen:
        roster, state = M.roster_for_target(_target(HELD))

    assert state == PUBLISHED, (
        f"a held election with a result file on disk resolved to state "
        f"{state!r}, not {PUBLISHED!r}")
    assert roster, (
        f"IT LOOKED: the {HELD} roster came back EMPTY with {path} on disk. "
        f"Every assertion in this file about the drop being disabled 'only when "
        f"there is no roster' is vacuous if this is empty.")

    opened = [p for _, _, p in seen if Path(p).name == path.name]
    assert opened, (
        f"the roster was resolved WITHOUT OPENING {path.name}. Either "
        f"`contesting_parties` grew a memo — which blinds this spy, and is why "
        f"`levels._citywide` is deliberately left un-memoised — or the roster "
        f"now comes from somewhere this test does not know about. Files seen: "
        f"{sorted({Path(p).name for _, _, p in seen})}")
    wandered = sorted({Path(p).name for _, _, p in seen
                       if Path(p).name != path.name})
    assert not wandered, (
        f"resolving the {HELD} roster opened election files other than the "
        f"target's own: {wandered}. Names on the ballot are public before "
        f"polling day and that is what makes reading this file legitimate; "
        f"reading any other election here is not covered by that argument.")

    # A SECOND READER, OUTSIDE THE SPY so it cannot satisfy the assertions above.
    assert roster == levels.ballot_roster(path), (
        f"`pools.contesting_parties` and `levels.ballot_roster` disagree about "
        f"the {HELD} ballot: {len(roster)} parties against "
        f"{len(levels.ballot_roster(path))}. `run_model` drops absent parties "
        f"by the first and `theta_residual.residuals` reproduces the baseline "
        f"with the second, so they are one definition or they are two models.")


def test_every_runnable_city_year_is_in_the_published_state():
    """THE POPULATION THE CLAIM COVERS, AND BOTH DIRECTIONS OF IT.

    A guard that refused everything would pass every other test in this file.
    The two halves here are what stop that:

    * every city-year the harness can actually run resolves to ``published``
      with a non-empty roster — 24 of 24 when this was written (eight metros x
      2011/2016/2021), so the new refusal fires on nothing in the current tree;
    * every calendar LGE with no result file resolves to ``not_yet_held`` with
      an empty roster, which is the live 2026 forecast's state and must stay
      legitimate.

    The denominator is ``runnable_targets`` itself rather than a typed number,
    so adding a city or a cycle moves both sides together.
    """
    cities = sorted(p.stem for p in cityconfig.CITIES_DIR.glob("*.toml"))
    if not cities:
        skip("no cities/*.toml on disk")

    runnable, published, empty_file = [], [], []
    for slug in cities:
        city = cityconfig.load(slug)
        for year in B.runnable_targets(city):
            path = _roster_path(city, year)
            if path is None or not path.exists():
                empty_file.append(f"{slug}/{year}")
                continue
            runnable.append(f"{slug}/{year}")
            roster, state = M.roster_for_target(
                cityconfig.Target(city=city, year=year))
            if state == PUBLISHED and roster:
                published.append(f"{slug}/{year}")
    cityconfig.use(CITY)

    if not runnable:
        skip("no result files on disk for any runnable city-year")

    # (1) IT LOOKED, two-sided: every runnable city-year with its file on disk
    #     was examined, and none more.
    scanned(published, of=runnable, low=1.0, high=1.0,
            what="runnable city-years resolving to a non-empty published roster",
            denominator="runnable city-years with a result file on disk")

    # (0) THE OTHER DIRECTION. Without this the guard could refuse every unheld
    #     target — which would stop the live forecast — and still pass above.
    not_held = []
    for slug in cities:
        city = cityconfig.load(slug)
        for year, election in cityconfig.CALENDAR.items():
            if election.kind != "LGE" or election.results is not None:
                continue
            roster, state = M.roster_for_target(
                cityconfig.Target(city=city, year=year))
            assert state == NOT_YET_HELD and not roster, (
                f"{slug}/{year} has no result file in the calendar, so it "
                f"cannot have a roster, and it resolved to {state!r} with "
                f"{len(roster)} parties. An election that has not happened must "
                f"be allowed to run with the off-ballot drop disabled.")
            not_held.append(f"{slug}/{year}")
    cityconfig.use(CITY)

    scanned(not_held, of=cities, low=1.0, high=4.0,
            what="city-years with no result file in the calendar",
            denominator="cities on disk")

    assert PUBLISHED != NOT_YET_HELD, "the two states are one string"
    assert empty_file == [], (
        f"runnable city-years whose result file is missing from data/raw: "
        f"{empty_file}. These are now REFUSALS rather than silent runs, which "
        f"is the point of F7 — but a target the harness offers and cannot feed "
        f"is a data problem to fix, not a test to relax.")


# --------------------------------------------------------------------------
# 2. the constructed violations — fault injection
# --------------------------------------------------------------------------

def test_an_unreadable_roster_refuses_instead_of_returning_empty():
    """CAN THE GUARD SEE? Break `contesting_parties` and watch what happens.

    Two constructed faults, because the old code fused two different failures
    into the same empty set:

    * it RAISES — a `KeyError` is what a renamed `sPartyName` column produces,
      and it is named in `contesting_parties`' own call chain. The old
      `except Exception` swallowed it. It must now propagate.
    * it RETURNS EMPTY where a result file exists — the silent half, which no
      exception handler can catch and which reads exactly like an unheld
      election. It must refuse.

    A test that only observed the healthy tree would pass with the `except
    Exception` still in place, which is why neither of these is optional.
    """
    city = _city()
    path = _roster_path(city, HELD)
    if path is None:
        skip(f"{HELD} has no result template; this test's premise has changed")
    if not path.exists():
        # The final check below re-runs the REAL function and requires it to
        # work, which is what proves the stub was removed. Without the file
        # there is nothing to restore it to.
        skip(f"no {HELD} result file for {CITY} on disk")
    target = _target(HELD)
    real = pools.contesting_parties

    def raises(_city, _year):
        raise KeyError("sPartyName")

    try:
        pools.contesting_parties = raises
        try:
            roster, state = M.roster_for_target(target)
        except KeyError:
            pass                       # the defect propagates, as it must
        else:
            raise AssertionError(
                f"`contesting_parties` raised and the roster resolved anyway, "
                f"to {len(roster)} parties in state {state!r}. THIS IS FAILING "
                f"OPEN: an empty roster disables the off-ballot drop and is "
                f"indistinguishable from a target that has not been held.")

        pools.contesting_parties = lambda _city, _year: set()
        try:
            roster, state = M.roster_for_target(target)
        except SystemExit:
            pass                       # the silent half, refused
        else:
            raise AssertionError(
                f"a result file exists for {HELD} and the roster came back "
                f"EMPTY, and the run continued in state {state!r} with "
                f"{len(roster)} parties. Empty is the value meaning 'drop "
                f"nobody', so this run would forecast every non-standing party "
                f"a share of the ballot and nothing downstream could tell.")
    finally:
        pools.contesting_parties = real

    # THE MECHANISM IS STILL LIVE. A test that monkeypatches the thing under
    # test must prove it put it back, or every test scheduled after it in this
    # process is measuring a stub.
    with election_files_read() as seen:
        roster, state = M.roster_for_target(target)
    assert state == PUBLISHED and roster and seen, (
        f"after restoring `contesting_parties` the roster resolved to "
        f"{len(roster)} parties in state {state!r} with {len(seen)} election "
        f"files opened. The stub was not removed.")


def test_run_model_resolves_its_roster_through_the_checked_path():
    """THE CALL SITE, not the helper. The half that makes the rest matter.

    `roster_for_target` can be flawless and `run_model` still resolve its roster
    with a bare `contesting_parties` call and an `except Exception` — which is
    precisely the state this file exists to end. So: stub the helper to raise a
    sentinel and require the model to die of it.

    It also proves the helper is consulted UNCONDITIONALLY. The target here is
    the unheld one, where the roster is legitimately empty and a `if
    target.is_held` shortcut would be tempting; a shortcut would leave the live
    forecast on the unguarded path, which is where it has always been.
    """
    city = _city()
    spec = city.processed / f"pools_{UNHELD}.json"
    if not spec.exists():
        skip(f"no pool spec at {spec}")
    target = cityconfig.use_target(UNHELD)
    real = M.roster_for_target

    def sentinel(_target):
        raise Sentinel("roster_for_target was called")

    try:
        M.roster_for_target = sentinel
        try:
            M.run_model(target, M.load_scenario(_Args(draws=10)), verbose=False)
        except Sentinel:
            return
    finally:
        M.roster_for_target = real
        cityconfig.use(CITY)
    raise AssertionError(
        "`run_model` produced a forecast with `roster_for_target` raising, so "
        "it is not resolving its roster through the checked path — either the "
        "call site has moved or something is catching the failure. An "
        "unreadable roster must stop the run, not be absorbed by it.")


# --------------------------------------------------------------------------
# 3. the state reaches the run's own output
# --------------------------------------------------------------------------

def test_the_run_records_which_roster_state_it_was_in():
    """A state nobody can read is not a distinction.

    The point of F7 is that a consumer — `compare_history`'s scoreboard, a
    published summary, a person — can tell a KNOWINGLY disabled off-ballot drop
    from a broken one. That requires the state to leave `run_model`, so this
    runs the model and reads it off `ModelRun`.

    Run at the unheld target because that is the state the live forecast is in
    today, and because a run that legitimately drops nobody is exactly the one
    the old code was indistinguishable from.

    It also checks the guard board that came out with it. `run.guards` is the
    payload of the trace's `41_guards`, which until now existed only inside a
    `--run-dir` dump and in locals: `_solve_stats` is a local of `run_model`, so
    solve non-convergence and the level floor's injected mass had no route to a
    consumer at all. The cross-check against the typed fields is the positive
    control — it cannot pass on an empty dict, and it cannot pass if the board
    and the fields are computed from different quantities.
    """
    city = _city()
    spec = city.processed / f"pools_{UNHELD}.json"
    if not spec.exists():
        skip(f"no pool spec at {spec}")
    target = cityconfig.use_target(UNHELD)
    try:
        run = M.run_model(target, M.load_scenario(_Args(draws=20)),
                          verbose=False)
    finally:
        cityconfig.use(CITY)

    assert run.roster_state == NOT_YET_HELD, (
        f"the {UNHELD} run recorded roster state {run.roster_state!r}. "
        f"`CALENDAR[{UNHELD!r}].results` is None, so there is no roster to "
        f"read and the drop is disabled legitimately — the run must SAY so, "
        f"because an empty roster it could not read looks identical.")
    assert run.roster_size == 0 and run.roster_dropped == [], (
        f"the {UNHELD} run reports {run.roster_size} parties on the ballot and "
        f"dropped {run.roster_dropped}. Nothing may be dropped on a roster that "
        f"does not exist: `levels.absent_from_ballot` returns [] for an empty "
        f"roster precisely because dropping the whole baseline over a missing "
        f"file would be catastrophic rather than conservative.")
    assert run.scenario.get("_roster_state") == NOT_YET_HELD, (
        "the roster state did not reach the scenario, so it will not reach "
        "forecast_summary.json, where `_pools_stale` — the same kind of fact "
        "about the same kind of input — already is.")

    # THE GUARD BOARD. Cross-checked against the typed fields that already have
    # consumers, so an empty or differently-computed board fails here.
    for name in ("ipf_failures", "ipf_balances", "cap_undershoots", "cap_moved",
                 "bounds_checked", "excessive_draws"):
        assert run.guards[name] == getattr(run, name), (
            f"`run.guards[{name!r}]` is {run.guards[name]!r} and "
            f"`run.{name}` is {getattr(run, name)!r}. They are the same "
            f"quantity read twice; two values for one counter is how a "
            f"scoreboard and a trace come to disagree about what a run did.")
    assert run.guards["overhang_count"] == run.overhang_count
    assert run.guards["bounds_violations"] == run.bounds_violations

    # The counters that had NO route out before this. Asserted by name, because
    # their values are what a consumer is for; a value assertion here would
    # pin a number this file has no standard for.
    orphans = {"solve_calls", "solve_rounds", "solve_nonconvergent",
               "solve_nonconvergent_reachable", "solve_worst_gap",
               "solve_worst_gap_reachable", "solve_unreachable_parties",
               "solve_floor_injected_mean", "solve_floor_injected_worst",
               "solve_identity_hits"}
    missing = sorted(orphans - set(run.guards))
    assert not missing, (
        f"the guard board reached `ModelRun` without {missing}. These are the "
        f"counters `compare_history` cannot otherwise see — `_solve_stats` is a "
        f"local of `run_model` — and they are the reason the board is carried "
        f"at all.")
    scanned(run.guards, of=orphans, low=1.0, high=3.0,
            what="guard counters carried on the run",
            denominator="the counters that had no route out before F7")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
