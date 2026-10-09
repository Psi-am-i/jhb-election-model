"""G8: the target's roster against the run's parties, in both directions.

Model correction batch item 8 (2026-10-09). A roster party whose only record
is the previous LGE was in no input the run read, so it was not forecast;
seven certified Johannesburg 2026 parties fell through that gap.
`levels.local_record_only` is the one classifier that enters them, and
`montecarlo.roster_universe_check` is the guard.

The guard is scan-shaped and meets CLAUDE.md §4's four requirements here: its
population (the roster, independents excluded) is stated and the classes are
asserted to partition it; it looks in both directions; each constructed
violation is caught and the guard goes quiet when it is reverted; and every
input below is constructed, apart from one in-process run that checks the
seven reach the real universe.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module  # noqa: E402

import cityconfig  # noqa: E402
import levels  # noqa: E402
import montecarlo as M  # noqa: E402

ROSTER = {"AAA", "BBB", "LOCAL", "SEEDED", "NOREC", "IND"}
BASELINE = {"AAA": 0.5, "BBB": 0.3}
PREV_LOCAL = {"AAA": 0.45, "BBB": 0.35, "LOCAL": 0.01, "GONE": 0.02}
SEEDS = {"SEEDED": 0.004}


def _check(universe, *, state="published", has_result=True, roster=ROSTER):
    return M.roster_universe_check(roster, state, universe, PREV_LOCAL, SEEDS,
                                   BASELINE, has_result=has_result)


def _refuses(**kw):
    try:
        _check(**kw)
    except SystemExit as exc:
        return str(exc)
    return None


def test_the_classifier_takes_exactly_the_local_record_only_parties():
    got = levels.local_record_only(ROSTER, BASELINE, PREV_LOCAL, SEEDS)
    assert got == ["LOCAL"], got
    # a seed, a baseline, an independent or a zero local vote each excludes
    assert levels.local_record_only({"LOCAL"}, {"LOCAL": 0.01}, PREV_LOCAL,
                                    {}) == []
    assert levels.local_record_only({"LOCAL"}, {}, PREV_LOCAL,
                                    {"LOCAL": 0.001}) == []
    assert levels.local_record_only({"IND"}, {}, {"IND": 0.02}, {}) == []
    assert levels.local_record_only({"LOCAL"}, {}, {"LOCAL": 0.0}, {}) == []
    # GONE has a local record and is not on the roster: not entered
    assert "GONE" not in got


def test_a_healthy_universe_passes_and_the_classes_partition_the_roster():
    universe = ["AAA", "BBB", "LOCAL", "SEEDED"]
    out = _check(universe)
    assert out["missing_with_record"] == [] and out["extra"] == []
    assert out["unrepresented_no_record"] == ["NOREC"]
    # population: the roster less the independent, and nothing else
    assert out["population"] == len(ROSTER - {"IND"})
    with_record = {p for p in ROSTER - {"IND"}
                   if PREV_LOCAL.get(p, 0) > 0 or BASELINE.get(p, 0) > 0
                   or SEEDS.get(p, 0) > 0}
    assert with_record | set(out["unrepresented_no_record"]) == ROSTER - {"IND"}
    assert not with_record & set(out["unrepresented_no_record"])
    # ENTRANT is the one universe party allowed off the roster
    assert _check(universe + ["ENTRANT"])["extra"] == []


def test_a_with_record_party_missing_from_the_run_refuses_and_goes_quiet():
    msg = _refuses(universe=["AAA", "BBB", "SEEDED"])        # LOCAL missing
    assert msg and "LOCAL" in msg, msg
    assert _refuses(universe=["AAA", "BBB", "LOCAL", "SEEDED"]) is None


def test_an_extra_party_refuses_on_a_real_roster_and_goes_quiet():
    healthy = ["AAA", "BBB", "LOCAL", "SEEDED"]
    for state in ("published", "projected"):
        msg = _refuses(universe=healthy + ["GONE"], state=state)
        assert msg and "GONE" in msg, (state, msg)
        assert _refuses(universe=healthy, state=state) is None


def test_a_no_record_party_refuses_only_at_a_live_forecast():
    healthy = ["AAA", "BBB", "LOCAL", "SEEDED"]
    assert _refuses(universe=healthy, has_result=True) is None
    msg = _refuses(universe=healthy, has_result=False)
    assert msg and "NOREC" in msg, msg
    # reverted: NOREC off the roster, the live forecast passes
    assert _refuses(universe=healthy, has_result=False,
                    roster=ROSTER - {"NOREC"}) is None


def test_a_target_with_no_roster_is_not_checked():
    out = _check(["AAA", "GONE"], state="not_yet_held", has_result=False)
    assert out["unrepresented_no_record"] == "not_checked"


def test_the_seven_certified_parties_reach_the_2026_run():
    """In-process, Johannesburg 2026, 20 draws: the seven roster parties with
    only a 2021 local record are in the run's universe and in no guard
    refusal."""
    seven = {"AMALGAMATED_RAINBOW_MOVEMENT", "CHANGE",
             "ECONOMIC_EMANCIPATION_FORUM",
             "INTERNATIONAL_REVELATION_CONGRESS",
             "SHOSHOLOZA_PROGRESSIVE_PARTY",
             "THE_ORGANIC_HUMANITY_MOVEMENT", "UIM"}
    cityconfig.use("joburg")
    target = cityconfig.use_target("2026")
    try:
        run = M.run_model(target, M.load_scenario(_Args(20)), verbose=False)
    finally:
        cityconfig.use("joburg")
    assert seven <= set(run.universe), sorted(seven - set(run.universe))
    assert set(run.scenario["_local_record_only"]) == seven
    assert run.guards["roster_unrepresented"] == []
    # Item 17 (R2.2): every item-8 party has a 2021 local share, so it is
    # drawn at its size group's width at that share, and the drawer's record
    # says so; the record names only parties the run draws. (The typed
    # fallback width it replaced was deleted 2026-10-09, M3 review row 7.)
    at_size = run.guards["level_sd_at_size"]
    assert set(run.scenario["_local_record_only"]) <= set(at_size), run.guards
    assert set(at_size) <= set(run.universe)


class _Args:
    """The shape ``montecarlo.load_scenario`` expects from argparse."""

    def __init__(self, draws: int):
        self.config = None
        self.set = None
        self.draws = draws
        self.seed = None


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
