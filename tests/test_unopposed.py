"""G7: unopposed wards (Schedule 1 items 12(2), 13(1)(b), 16(5)).

A ward whose only candidate is elected unopposed holds no ward ballot, and the
statute counts the PR votes cast there for that candidate's party twice. The
model does not simulate such a ward: `montecarlo.run_model` refuses a target
that has one, and the seat law takes the doubled votes as an input
(`seats.eligible_parties(..., unopposed_pr=)`). JUDGEMENT-CALLS §Q7.

The scan below asserts the population on disk is empty. It meets CLAUDE.md
§4's four requirements: it states its population (every metro LGE result file
2000-2021 and every declared 2026 slate) and asserts the files scanned equal
it; each file's ward count is checked against the city's configured count
(exact for 2011-2021, a two-sided band for 2000 and 2006, which have no
configured count); a constructed violation is caught and the detector goes
quiet when it is reverted; and the detector's input there is constructed.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, scanned  # noqa: E402

import cityconfig  # noqa: E402
import levels  # noqa: E402
import montecarlo as M  # noqa: E402
from seats import allocate, eligible_parties  # noqa: E402

ELECTIONS = ROOT / "data" / "raw" / "elections"
CITIES = sorted(p.stem for p in (ROOT / "cities").glob("*.toml"))
HELD_LGES = sorted(y for y, e in cityconfig.CALENDAR.items()
                   if e.kind == "LGE" and e.results)


def test_no_metro_result_file_has_an_unopposed_ward():
    """The population: every metro × every held LGE. Each file's wards are
    counted against the city's configured ward count, so a reader that stopped
    seeing wards (or a ward column renamed) fails here rather than passing
    empty."""
    expected = {(slug, y) for slug in CITIES for y in HELD_LGES}
    seen, found = set(), {}
    banded = []
    for slug in CITIES:
        city = cityconfig.load(slug)
        for year in HELD_LGES:
            path = ELECTIONS / cityconfig.CALENDAR[year].results.format(
                CODE=city.code)
            ward_parties, all_wards = levels.ward_ballots(path)
            seen.add((slug, year))
            by_year = city.structure.get("by_year", {})
            if year in by_year:
                assert len(all_wards) == int(by_year[year]["wards"]), (
                    slug, year, len(all_wards), by_year[year]["wards"])
            else:
                # 2000 and 2006: no configured count. Delimitations move by a
                # fraction, so the 2011 count bounds them on both sides.
                scanned(all_wards, of=int(by_year["2011"]["wards"]),
                        low=0.6, high=1.4,
                        what=f"wards in {path.name}",
                        denominator=f"{slug}'s 2011 ward count")
                banded.append((slug, year))
            hits = levels.unopposed_in(ward_parties, all_wards)
            if hits:
                found[(slug, year)] = hits
    assert seen == expected, sorted(expected ^ seen)
    assert len(banded) == len(CITIES) * len(
        [y for y in HELD_LGES if y < "2011"]), banded
    assert not found, found


def test_no_declared_2026_slate_has_an_unopposed_ward():
    """Every 2026 judgement file with `[roster.wards]`. Its declared wards are
    counted against the city's configured ward count."""
    import pools

    checked = []
    for path in sorted((ROOT / "judgements").glob("*-2026.toml")):
        slug = path.stem.rsplit("-", 1)[0]
        cityconfig.use(slug)
        try:
            city = cityconfig.load(slug)
            target = cityconfig.Target(city=city, year="2026")
            declared = (pools.declared_roster(city, target) or {}).get("wards")
            if not declared:
                continue
            wards = {str(w).strip() for ws in declared.values() for w in ws}
            assert len(wards) == city.structure_for("2026")["wards"], (
                slug, len(wards))
            assert levels.unopposed_wards(target, city) == {}, slug
            checked.append(slug)
        finally:
            cityconfig.use("joburg")
    assert "joburg" in checked, checked


def test_the_detector_sees_a_constructed_unopposed_ward_and_goes_quiet():
    all_wards = {"W1", "W2", "W3"}
    stood = {"W1": {"AAA", "BBB"}, "W2": {"AAA", "BBB"}, "W3": {"BBB", "IND"}}
    assert levels.unopposed_in(stood, all_wards) == {}
    # one party in W1: caught, named
    stood["W1"] = {"AAA"}
    stood["W3"] = {"IND"}
    assert levels.unopposed_in(stood, all_wards) == {"W1": "AAA", "W3": "IND"}
    # a ward with PR rows only: caught, unnamed
    del stood["W1"]
    assert levels.unopposed_in(stood, all_wards) == {"W1": None, "W3": "IND"}
    # reverted: quiet
    stood.update({"W1": {"AAA", "BBB"}, "W3": {"BBB", "IND"}})
    assert levels.unopposed_in(stood, all_wards) == {}


def test_run_model_refuses_a_target_with_an_unopposed_ward():
    """The refusal fires on a constructed ward and names it; with the
    constructed ward removed the same target passes the check."""
    cityconfig.use("joburg")
    target = cityconfig.use_target("2021")
    real = levels.unopposed_wards
    levels.unopposed_wards = lambda t, c: {"79800007": "AAA"}
    try:
        try:
            M.run_model(target, M.load_scenario(_Args(10)), verbose=False)
        except SystemExit as exc:
            assert "12(2)" in str(exc) and "79800007" in str(exc), exc
        else:
            raise AssertionError("an unopposed ward did not refuse")
    finally:
        levels.unopposed_wards = real
        cityconfig.use("joburg")
    target = cityconfig.use_target("2021")
    try:
        run = M.run_model(target, M.load_scenario(_Args(10)), verbose=False)
    finally:
        cityconfig.use("joburg")
    assert run.seat_draws, "the reverted run produced no draws"


def test_the_seat_law_counts_an_unopposed_wards_pr_votes_twice():
    """Hand-computed. Ward and PR votes AAA 300+250, BBB 250+200; 10 seats.

    Without: A = 1000, quota 1000//10+1 = 101. AAA 550 → 5 r 45, BBB 450 → 4
    r 46; the last seat to BBB: 5-5.
    AAA won a ward unopposed where 100 PR votes were cast for it: AAA 650,
    A = 1100, quota 111. AAA 650 → 5 r 95, BBB 450 → 4 r 6; the last seat to
    AAA: 6-4. A key outside the pool (IND) changes nothing.
    """
    ward = {"AAA": 300, "BBB": 250}
    pr = {"AAA": 250, "BBB": 200}
    plain = allocate(eligible_parties(ward, pr), total_seats=10)
    assert plain.quota == 101 and plain.seats == {"AAA": 5, "BBB": 5}
    doubled = allocate(eligible_parties(ward, pr, {"AAA": 100}),
                       total_seats=10)
    assert doubled.quota == 111 and doubled.seats == {"AAA": 6, "BBB": 4}
    assert eligible_parties(ward, pr, {"IND": 50}) == eligible_parties(ward, pr)


class _Args:
    """The shape ``montecarlo.load_scenario`` expects from argparse."""

    def __init__(self, draws: int):
        self.config = None
        self.set = None
        self.draws = draws
        self.seed = None
