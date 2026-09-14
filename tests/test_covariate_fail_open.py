"""⛔ TWO COVARIATES THAT FAILED OPEN INTO A PLAUSIBLE-LOOKING WRONG ANSWER.

Both defects in this module are one class: a function whose input is missing
returns a value that is *arithmetically valid*, so every stage below it carries
on and produces a different answer under the same name, with nothing in any
output saying the input was absent.

**1. ``benchmarks.roster_split`` and the ward-reach archive.**
``uniform-swing+roster`` is the opponent the model's margin is measured against
(``MODEL-LOG`` §1.231: model 723, this reference 837 over 24 rows). Its
newcomers are sized by ward reach and by nothing else, and its own docstring
calls reach "the record's own strongest covariate". ``pools._ward_reach``
returns ``{}`` when the archive is unreachable — the same value it returns when
a party genuinely has no ward rows — and with it empty ``newcomer_shares``
takes its ``fallback`` branch for **every** newcomer at once, the identical
weight cancels in the normalisation, and the arrival budget splits EVENLY.

⚠️ **AND THE ARCHIVE IS A DIFFERENT ONE FROM THE ROSTER'S.** The roster comes
through ``montecarlo.roster_for_target`` → ``pools.contesting_parties``, which
resolves ``city.path("raw","elections", template)``; reach comes through
``pools.metro_file``, which looks in ``data/raw/elections/_metros/`` and
``_reports/``. The two are present or absent independently, so the reference
fails CLOSED on the roster at the line above and then failed OPEN on the
covariate it actually depends on. Measured at joburg 2021 on 2026-09-14:
ActionSA 0.163835% and sixth of 32 becomes 0.061133% and equal-first, and the
allocated council moves by 12 of 270 seats.

**2. ``backtest.arrival_baseline`` and the preceding NPE file.** Its docstring
is emphatic that ``{}`` must never be returned, because an empty baseline does
not mean "nobody had a record", it means "everybody arrived" — and
``entrant_actual_for`` then relabels the model's generic ENTRANT onto the
largest party in the chamber. The guard covered two of the three routes to an
empty return: no ``previous_npe``, and the file not existing. It did not cover
the file existing and yielding no rows, which is what a zero-byte placeholder
or a header-only interrupted download is. ``fold.citywide({})`` returns ``{}``
rather than dividing by zero, and ``{}`` survives the ``> 0`` filter unchanged.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4's four parts:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS.** The claim is about every
   city-year at which these functions are reachable, which is
   ``backtest.runnable_targets`` per city — the same set ``backtest.TARGETS``
   gates ``benchmarks.build_context`` on. The scanned set is asserted equal to
   it in BOTH directions, so a scan that quietly stopped visiting cities cannot
   read as a pass.
1. **IT LOOKED.** Each population is bounded two-sidedly by ``_support.scanned``
   against a denominator computed from the tree, never a typed count.
2. **IT CAN SEE.** Four constructed violations — two routes into each defect —
   and after each, the detector is shown to go quiet with the live answer
   restored to the seat. ⚠️ **The header-only routes are the load-bearing
   ones**: a repair written as ``if metro_file(...) is None: raise`` or as a
   bare ``exists()`` check passes every other test here and fails those two.
   That is deliberate, because that repair was the one first proposed.
3. **CONSTRUCTED INPUT, NOT OBSERVED.** Every violation is injected. Nothing
   here is a property of a passing tree that expires the day the tree changes.

⚠️ **THREE OF THE FIVE TESTS HERE DO NOT WITNESS THE REPAIR, AND SAYING SO IS
the point of this paragraph.** The population tests describe the TREE — that the
archive is readable and the baselines are usable at every runnable city-year —
and they pass identically with the guards present and absent, as they should:
they exist so that the two detector tests cannot be satisfied by a tree that has
lost its inputs. Run against the pre-repair sources and against a
``metro_file``-path-only repair in a shadow tree on 2026-09-14, this module
reported 3 passed / 2 failed both times, and the two failures were the detector
tests. **A control that still passes after the repair it was written to witness
is worse than no control**, so read the split rather than the total.

⛔ **WHAT THIS FILE DOES NOT PROVE.** It does not show the degraded reference
scores worse against real results — that needs ``compare_history`` and is not
run here. It shows only that the two answers DIFFER while carrying one name,
which is the defect: a comparison that has stopped being made while still
printing a column.

⚠️ **AND IT CATCHES AN EMPTY ARCHIVE, NOT A PARTIAL ONE.** A metro file holding
half its wards, or an NPE file holding half its voting districts, yields a
non-empty map of plausible-looking numbers that every assertion here accepts.
That case is covered somewhere else and deliberately not duplicated here: both
archives are rows in ``data/archive_manifest.csv`` with a byte count and a
sha256, and ``tests/test_data_coverage.py`` checks the size on every run and the
hash under ``ARCHIVE_VERIFY_HASHES=1``. The two guards are complementary —
that one sees a file that changed, this one sees a covariate that vanished at
the point of use, on a machine whose manifest was never run.
"""

from __future__ import annotations

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path

from _support import declared_city_years, scanned

import backtest as BT
import benchmarks as BM
import cityconfig
import pools

DATA = Path("data/raw/elections")


@contextmanager
def _scratch():
    """A throwaway directory OUTSIDE the repository.

    ⛔ NOT under ``data/``. ``run_all.py`` runs these modules in parallel
    processes and says in as many words that what makes that safe is that every
    module bar the three it lists "writes only into temporary directories". An
    earlier draft of this file put its injected archives in ``data/processed/``,
    which is where the pool specs live and where an emit may be running; that
    would have made this module a fourth entry on the serial list for no gain.
    """
    path = Path(tempfile.mkdtemp(prefix="covariate_fail_open_"))
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


def _runnable() -> list[tuple[str, str]]:
    """Every (slug, year) these two functions can be reached at, COMPUTED.

    ``backtest.runnable_targets`` is the authority — ``backtest.TARGETS``
    raises ``KeyError`` outside it, which is what stops ``benchmarks`` being
    built at 2000 or 2006 (no council size, no γ fold). It is read per city
    because the answer is per city.
    """
    out = []
    for slug in sorted({s for s, _ in declared_city_years()}):
        for year in BT.runnable_targets(cityconfig.load(slug)):
            out.append((slug, str(year)))
    return out


# ---------------------------------------------------------------------------
# 0 + 1 — the population, and that the scan looked at all of it
# ---------------------------------------------------------------------------

def test_every_runnable_city_year_has_the_ward_reach_covariate():
    """⛔ THE POPULATION ASSERTION FOR DEFECT 1.

    If this ever fails it is not a test to relax: it means a city-year the
    panel scores has lost the only covariate ``uniform-swing+roster`` sizes
    newcomers by, and before the repair below that row would have been scored
    with the budget split evenly and nothing printed.
    """
    population = _runnable()
    seen: dict[tuple[str, str], int] = {}
    for slug, year in population:
        cityconfig.use(slug)
        seen[(slug, year)] = len(pools._ward_reach(cityconfig.active().code, year))

    # BOTH DIRECTIONS. A scan that visited fewer cities than it claims would
    # otherwise pass every bound below by having examined almost nothing.
    assert set(seen) == set(population), (
        f"the scan and the population disagree: scanned-not-runnable "
        f"{sorted(set(seen) - set(population))}, runnable-not-scanned "
        f"{sorted(set(population) - set(seen))}.")

    have = [k for k, n in seen.items() if n]
    scanned(have, of=population, low=1.0, high=1.0,
            what="runnable city-years whose ward-reach archive is readable",
            denominator="city-years backtest.runnable_targets can run")


def test_ward_reach_names_a_plausible_fraction_of_the_ballot():
    """A two-sided per-row bound, so a half-broken reader is not a pass.

    Reach is measured off the ward ballot and the roster off the whole result
    file, so reach ⊆ roster is structural and 1.0 is a real ceiling, not a
    tuned one. The floor is not structural: observed 0.958..1.000 across the 24
    runnable city-years on 2026-09-14, and set at 0.5 so that a reader which
    lost one ballot type, one province or one delimiter trips it while ordinary
    drift does not.
    """
    for slug, year in _runnable():
        cityconfig.use(slug)
        code = cityconfig.active().code
        reach = pools._ward_reach(code, year)
        roster = pools.contesting_parties(cityconfig.active(), year)
        assert set(reach) <= set(roster), (
            f"{slug} {year}: ward reach names parties absent from the ballot "
            f"roster — {sorted(set(reach) - set(roster))}. The two are read "
            f"from DIFFERENT archives (`pools.metro_file` vs "
            f"`city.path('raw','elections',...)`) and have gone out of step.")
        scanned(reach, of=roster, low=0.5, high=1.0,
                what=f"parties with measured ward reach at {slug} {year}",
                denominator=f"parties on the {year} ballot roster")


def test_every_runnable_city_year_has_a_usable_arrival_baseline():
    """⛔ THE POPULATION ASSERTION FOR DEFECT 2.

    ``arrival_baseline`` must return a non-empty map at every row the panel
    scores. ``None`` here would mean the preceding NPE is unreachable; ``{}``
    is the value the repair below makes unreachable by any route.
    """
    population = _runnable()
    seen: dict[tuple[str, str], int] = {}
    for slug, year in population:
        cityconfig.use(slug)
        target = cityconfig.Target(city=cityconfig.active(), year=year)
        base = BT.arrival_baseline(target, DATA)
        assert base is not None, (
            f"{slug} {year}: the preceding NPE ({target.previous_npe}) is "
            f"unreachable, so no row here can be scored for arrivals.")
        assert base != {}, (
            f"{slug} {year}: arrival_baseline returned {{}}, which its own "
            f"docstring says it must never return — an empty baseline reads "
            f"as EVERY party having arrived.")
        seen[(slug, year)] = len(base)

    assert set(seen) == set(population), (
        f"the scan and the population disagree: scanned-not-runnable "
        f"{sorted(set(seen) - set(population))}, runnable-not-scanned "
        f"{sorted(set(population) - set(seen))}.")

    scanned([k for k, n in seen.items() if n], of=population,
            low=1.0, high=1.0,
            what="runnable city-years with a readable preceding-NPE baseline",
            denominator="city-years backtest.runnable_targets can run")

    # Two-sided per row. Observed 0.574..1.889 of the target's ballot roster on
    # 2026-09-14; the band is set wide of that deliberately, because the two
    # counts are a national and a local ballot four to five years apart and
    # nothing makes them track. It still catches a file that yielded nothing
    # and a reader that double-counted.
    for slug, year in population:
        cityconfig.use(slug)
        roster = pools.contesting_parties(cityconfig.active(), year)
        scanned(seen[(slug, year)], of=roster, low=0.25, high=4.0,
                what=f"parties in the preceding-NPE baseline at {slug} {year}",
                denominator=f"parties on the {year} ballot roster")


# ---------------------------------------------------------------------------
# 2 + 3 — constructed violations, and the detector going quiet again
# ---------------------------------------------------------------------------

def _header_only(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Municipality,VD_Number,Ward,sPartyName,Party_Votes,"
                    "BallotType\n", encoding="utf-8")
    return path


def test_an_unreachable_reach_archive_is_REFUSED_by_both_routes():
    """⛔ THE CONSTRUCTED VIOLATION FOR DEFECT 1, TWICE.

    Route (a) is ``metro_file`` finding no candidate — an absent archive, or a
    wrong working directory, since both paths it builds are RELATIVE. Route (b)
    is a candidate existing and yielding no ward rows. They reached byte-
    identical degraded councils when measured on 2026-09-14, which is why the
    guard is on ``_ward_reach``'s RETURN and not on ``metro_file``.

    ⚠️ Route (b) is the whole point of this test. A repair written as
    ``if _pools.metro_file(...) is None: raise`` passes route (a), passes every
    other test in this file, and leaves route (b) exactly as it was.
    """
    cityconfig.use("joburg")
    ctx = BM.build_context(2021)
    live, _ = BM.uniform_swing_roster(ctx, draws=1)
    live = live[0]
    assert sum(live.values()) == ctx.council, (
        "the live reference does not fill the council, so this test is "
        "comparing against a broken baseline rather than a working one.")

    original = pools.metro_file
    with _scratch() as scratch:
        empty = _header_only(scratch / "reach_header_only.csv")
        routes = {
            "the archive is absent (metro_file finds no candidate)":
                lambda code, year: None,
            "a candidate exists and yields no ward rows (truncated download)":
                lambda code, year: empty,
        }
        try:
            for description, fake in routes.items():
                pools.metro_file = fake
                assert pools._ward_reach("JHB", "2021") == {}, (
                    f"the injection did not reproduce the fault "
                    f"({description}); this test is not exercising the "
                    f"detector.")
                try:
                    BM.uniform_swing_roster(ctx, draws=1)
                except SystemExit as exc:
                    assert "ward-reach archive" in str(exc), (
                        f"something refused, but not the reach guard: {exc}")
                else:
                    raise AssertionError(
                        f"uniform-swing+roster returned a council with NO ward "
                        f"reach at all ({description}). Every newcomer then "
                        f"takes `newcomer_shares`'s fallback, the weight "
                        f"cancels in the normalisation, and the arrival budget "
                        f"splits EVENLY — a different opponent under the same "
                        f"name, and this is the opponent the model's margin is "
                        f"measured against.")
                pools.metro_file = original
        finally:
            pools.metro_file = original

    # AND IT GOES QUIET AGAIN — to the seat, not merely without raising.
    back, _ = BM.uniform_swing_roster(ctx, draws=1)
    assert back[0] == live, (
        "the reference does not return to its live council once the injection "
        "is reverted, so the detector above is not what changed the answer.")


def test_an_npe_file_that_yields_no_rows_is_REFUSED_by_all_three_routes():
    """⛔ THE CONSTRUCTED VIOLATION FOR DEFECT 2.

    The third route — the file exists and yields nothing — is the one the
    original guard missed, and the assertion that it relabels onto the ANC is
    what makes this a test of consequence rather than of a return value.
    """
    cityconfig.use("joburg")
    target = cityconfig.Target(city=cityconfig.active(), year="2021")
    live = BT.arrival_baseline(target, DATA)
    assert live, "the live baseline is empty, so there is nothing to protect."

    actual, _winners = BT.actual_result(DATA / target.results("2021"),
                                        target.council, 2021,
                                        cityconfig.active().code)
    live_entrant = BT.entrant_actual_for_target(target, actual, DATA)
    assert live_entrant == "ASA", (
        f"the 2021 Johannesburg arrival is {live_entrant!r}, not ASA — this "
        f"test's premise has moved and its ANC assertion below means nothing.")

    # ⛔ WHAT THE UNGUARDED VALUE DOES, asserted rather than described. This is
    # the cost the guard buys, and it is measured, not argued.
    largest = max(actual.items(), key=lambda kv: (kv[1], kv[0]))[0]
    assert BT.entrant_actual_for(actual, {}) == largest == "ANC", (
        "an empty baseline no longer relabels ENTRANT onto the largest party "
        "in the chamber; the guard below may be protecting nothing.")

    real = cityconfig.resolve_path(DATA / target.results(target.previous_npe))
    with _scratch() as scratch:
        injected = scratch / real.relative_to(DATA)
        injected.parent.mkdir(parents=True, exist_ok=True)

        # Route 1: no previous_npe at all.
        class _NoNPE:
            previous_npe = None
        assert BT.arrival_baseline(_NoNPE(), DATA) is None

        # Route 2: the file is not there.
        assert BT.arrival_baseline(target, scratch) is None

        # Route 3: the file IS there and yields nothing. Both shapes an
        # interrupted fetch actually leaves behind.
        for description, body in (("a zero-byte placeholder", ""),
                                  ("a header-only truncation",
                                   "VD_Number,Ward,sPartyName,Party_Votes,"
                                   "BallotType\n")):
            injected.write_text(body, encoding="utf-8")
            assert cityconfig.resolve_path(injected).exists(), (
                f"the injection did not create the file ({description}); "
                f"this is testing route 2 again, not route 3.")
            got = BT.arrival_baseline(target, scratch)
            assert got is None, (
                f"arrival_baseline returned {got!r} for {description} of the "
                f"preceding NPE. Its docstring: an empty baseline means "
                f"EVERYBODY arrived, and entrant_actual_for then relabels the "
                f"model's generic ENTRANT onto {largest}, handing it a free "
                f"correct label on the largest party in the council.")
            assert BT.entrant_actual_for_target(
                target, actual, scratch) is None, (
                f"the caller relabelled an entrant off {description}.")

    # AND IT GOES QUIET AGAIN.
    assert BT.arrival_baseline(target, DATA) == live
    assert BT.entrant_actual_for_target(target, actual, DATA) == live_entrant


if __name__ == "__main__":
    import sys
    from _support import run_module
    sys.exit(run_module(globals()))
