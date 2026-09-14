"""A CENSUS REFUSAL MAY NOT BE SWALLOWED — POOLS-REEMIT-QUEUE entry 22.

**The claim: no city-year leaves a pool record without the run saying which one
and why.**

⚠️ Note the shape. This is **not** "no city-year is ever dropped" — dropping a
genuinely absent election is correct. It is that **silence is forbidden**, and
that reframing is what makes the claim testable.

``pools.pool_counts`` raises three refusals written to STOP a wrong census join.
Every historical caller already carried ``except SystemExit: continue``, so each
of them instead DELETED that city-year with no output:
``registration_series``'s clause said *"that election is not on disk for this
city"* while joburg 1999, and 2004 and 2019 in all eight cities, have their
result files on disk and fail the census join; the pre-2011 years in the other
seven are held back. Its docstring promised ten cycles and it returned eight.

**The harm's SIZE depends on which year falls, and the two magnitudes differ by
two orders of magnitude.** ``turnout_band`` centres on ``arr[-1]``:

* drop the MOST RECENT LGE and the forecast is RE-CENTRED — a forced Tshwane
  2016 refusal moved the turnout centre by **-0.4919 (63.3% -> 14.1%)** with
  zero output;
* drop any EARLIER one and the band NARROWS — a forced joburg 2000 refusal took
  pool 2's width **0.7511 -> 0.5777 (-23.1%)** with the centre unmoved.

A silently narrowed band is the worse of the two in practice: an overconfident
forecast with no trace, and calibration damage is invisible in a point score.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS.** Computed as ``CALENDAR`` x the
   cities, testing for the file, and asserted EQUAL to what was scanned. Forward:
   every city-year a record serves is in the record. Reverse: every city-year it
   refuses is in a stated loss list carrying a cause, and the causes PARTITION
   the refused set with no residue.
1. **IT LOOKED.** ``len(series) / len(years with a file on disk)`` bounded
   two-sidedly per city, and the refused set asserted non-empty AND bounded
   above. ⚠️ Today's refused set is an OBSERVED property of the tree, so it is
   the DENOMINATOR only; the detector is proved by §2. If ``DATA-QUALITY.md``
   item 18's ``vd_map`` repair is taken the refused set legitimately shrinks and
   this bound must move with it.
2. **IT CAN SEE — AND GOES QUIET WHEN REVERTED.** One injection per refusal,
   each reverted, and the reasons collected are asserted EQUAL to
   ``pools.CENSUS_UNSAFE_REASONS`` so a fifth refusal added to ``pool_counts``
   and not classified turns this red. The discriminators: a genuinely absent
   file must still drop QUIETLY as ``not_on_disk`` (a repair that makes every
   refusal fatal fails there), and a real ``TypeError`` must PROPAGATE.
3. **CONSTRUCTED INPUT, NOT OBSERVED.** Every injection is a constructed
   parameter, a patched reader or a redirected path. Nothing asserts a property
   of the census files themselves, and nothing under ``data/`` is moved.

⛔ **ASSERTS STATES, COUNTS AND WIDTHS — NEVER LOG TEXT.**

⚠️ **What this guard cannot prove.** It cannot prove the ``:1539`` fail-open was
unreachable. A panel scan over all eight cities x every calendar year found the
drift unmeasurable at 2004 and 2019 everywhere and at joburg 1999, and **every
one of those is refused by the 50% guard two lines later** — so on this tree the
old "shift nan" message was a false statement rather than an open hole, and the
new refusal is number-neutral. That is a property of the current coupling. If
the ``vd_map`` repair lands, re-derive it.

Run:
    ./.venv/bin/python tests/test_census_refusal_is_not_swallowed.py
    ./.venv/bin/python -m pytest tests/test_census_refusal_is_not_swallowed.py -q
"""

from __future__ import annotations

import contextlib
import dataclasses
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module, scanned, skip  # noqa: E402

import cityconfig  # noqa: E402
import numpy as np  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"

# A year whose delimitation MATCHES the census's, so no reprojection runs and
# the ward-key injections below reach their own guards rather than the drift
# ceiling. Asserted, not assumed, in the test that uses it.
JOIN_YEAR = "2021"
# The year the drift-ceiling injection makes trip. It is also the year whose
# delimitation DIFFERS from the census's and whose reprojection LOSES wards, so
# it is the one year in this city where `_reprojection_drift` runs its
# measurement all the way through — which the unmeasurable case needs. Its
# measured drift is the
# smallest non-zero one in Johannesburg's record, which is why lowering the
# ceiling reaches it first.
CEILING_YEAR = "2000"

# How much of a city's on-disk calendar a record may lose and still be a record.
# Two-sided as `_support.scanned` requires: below the floor the reader has
# broken, above the ceiling the record is not a record. Measured 8 of 11 for
# Johannesburg when this was written.
SERVED_LO, SERVED_HI = 0.50, 1.00


def _cfg():
    return pools.load_config()


def _on_disk(city) -> set[str]:
    """Every calendar year whose result file is actually on disk for this city.

    The denominator, computed from the tree rather than typed — the population
    the claim covers.
    """
    out = set()
    for year, election in cityconfig.CALENDAR.items():
        if not election.results:
            continue
        if city.path("raw", "elections", election.results).exists():
            out.add(year)
    return out


@contextlib.contextmanager
def _quiet():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


# --------------------------------------------------------------------------
# 0 + 1. the population, both directions
# --------------------------------------------------------------------------

def test_every_on_disk_city_year_is_either_served_or_named_with_a_cause():
    """BOTH DIRECTIONS OVER ONE CITY'S WHOLE CALENDAR.

    ``registration_series`` is the record that iterates every election kind, so
    it is where the full calendar population can be scanned. Forward: every year
    it served is in the series. Reverse: every year it did not serve is in the
    loss ledger with a cause, the two sets PARTITION the on-disk population, and
    every cause is one of ``pools.POOL_LOSS_CAUSES``.

    A refusal with no cause, or a cause outside the enum, fails here — that is
    the residue the old single ``except SystemExit`` created.
    """
    city = cityconfig.load(CITY)
    population = _on_disk(city)
    assert population, f"no result files on disk for {CITY}"

    with _quiet():
        series = pools.registration_series(city, _cfg())
    losses = pools.pool_losses("registration_series", CITY).get(
        ("registration_series", CITY), {})

    served, refused = set(series), set(losses)
    assert served <= population, (
        f"{sorted(served - population)} reached the registration series with "
        f"no result file on disk. The reader is serving a year from somewhere "
        f"this test does not know about.")
    assert served | refused == population, (
        f"{sorted(population - (served | refused))} are on disk and appear "
        f"NEITHER in the series NOR in the loss ledger. That is the defect this "
        f"guard is named for: a city-year that left the record in silence.")
    assert not (served & refused), (
        f"{sorted(served & refused)} are recorded as both served and lost.")
    unknown = sorted(c for c in losses.values() if c not in pools.POOL_LOSS_CAUSES)
    assert not unknown, (
        f"losses carry causes {unknown} that are not in POOL_LOSS_CAUSES "
        f"{list(pools.POOL_LOSS_CAUSES)}. A cause outside the enum does not "
        f"partition anything.")

    # IT LOOKED, two-sidedly, against a denominator computed from the tree.
    scanned(len(served), of=len(population), low=SERVED_LO, high=SERVED_HI,
            what=f"{CITY} elections that reached the registration series",
            denominator=f"{CITY} elections with a result file on disk")
    assert refused, (
        f"{CITY} lost nothing from its registration series, so the reverse "
        f"direction above scanned an empty set and proves nothing. That is a "
        f"legitimate state of the tree — DATA-QUALITY.md item 18's vd_map "
        f"repair would produce it — and this bound must then move with it.")
    assert len(refused) < len(population), (
        f"{CITY} lost all {len(refused)} of its on-disk elections. The guard "
        f"cannot pass by everything failing.")


def test_the_panel_sweep_names_its_losses_in_every_city():
    """THE SAME CLAIM ACROSS THE PANEL, on the LGE years the sweep reads.

    ``panel_turnout_spread`` is the third caller and the one whose ``except
    (Exception, SystemExit)`` also swallowed real bugs. Scanned over all eight
    cities at once because that is the population IT covers; the test above
    covers one city's whole calendar, which is the population
    ``registration_series`` covers. Between them both directions are asserted
    over every kind of election and every city.
    """
    cfg = _cfg()
    pools._PANEL_SPREAD_CACHE.clear()      # the ledger fills on a real sweep
    with _quiet():
        pools.panel_turnout_spread(cfg)
    ledger = pools.pool_losses("panel_turnout_spread")
    assert ledger, (
        "the panel sweep recorded no losses at all, for any city. Either every "
        "LGE now joins the census — in which case this bound moves — or the "
        "sweep stopped filing them and the reverse direction is blind.")

    slugs = sorted(p.stem for p in cityconfig.CITIES_DIR.glob("*.toml"))
    covered = sorted({slug for (_record, slug) in ledger})
    assert covered == slugs, (
        f"the sweep filed losses for {covered}, and the cities on disk are "
        f"{slugs}. A city missing from the ledger was never swept, so nothing "
        f"here says anything about it.")
    for (_record, slug), losses in sorted(ledger.items()):
        city = cityconfig.load(slug)
        lge_on_disk = {y for y in _on_disk(city)
                       if cityconfig.CALENDAR[y].kind == "LGE"}
        stray = sorted(set(losses) - lge_on_disk)
        assert not stray, (
            f"{slug}: the sweep filed losses for {stray}, which have no LGE "
            f"result file on disk — so it is reporting a loss it never had.")
        unknown = sorted(c for c in losses.values()
                         if c not in pools.POOL_LOSS_CAUSES)
        assert not unknown, f"{slug}: causes {unknown} outside the enum"


# --------------------------------------------------------------------------
# 2. it can see — one injection per refusal, each reverted
# --------------------------------------------------------------------------

def _pool_counts_reason(city, year, cfg) -> str | None:
    """Run `pool_counts` and return the refusal's REASON, or None if it served."""
    try:
        with _quiet():
            pools.pool_counts(city, year, cfg)
        return None
    except pools.PoolCountsUnsafe as unsafe:
        return unsafe.reason


def test_every_census_refusal_is_reachable_named_and_reverts():
    """IT CAN SEE — and the reasons are iterated FROM the enum, both directions.

    One constructed injection per refusal site. The set of reasons observed must
    EQUAL ``pools.CENSUS_UNSAFE_REASONS``: a refusal in ``pool_counts`` with no
    case here, or a case here for a reason the module no longer raises, fails.
    That is the register->code direction §4 names as this repository's blindest,
    and it is the one a hand-written list cannot give.

    Every injection is reverted and the same call must then SERVE the year.
    """
    city = cityconfig.load(CITY)
    cfg = _cfg()
    observed: dict[str, str] = {}

    # The control: both years serve before anything is injected.
    assert pools.delimitation_for(JOIN_YEAR) == int(
        cfg.base().censuses[-1].delimitation), (
        f"{JOIN_YEAR} is no longer on the census's own delimitation, so the "
        f"ward-key injections below would hit the reprojection guards first and "
        f"prove nothing about the guards they name.")
    assert _pool_counts_reason(city, JOIN_YEAR, cfg) is None, (
        f"{CITY} {JOIN_YEAR} does not serve even before an injection; every "
        f"case below would be measuring something else.")

    # (a) the drift ceiling: lower it until a real city-year trips.
    original = pools.CENSUS_DRIFT_CEILING
    pools.CENSUS_DRIFT_CEILING = 0.003
    try:
        observed["a"] = _pool_counts_reason(city, CEILING_YEAR, cfg)
    finally:
        pools.CENSUS_DRIFT_CEILING = original
    assert observed["a"] == "census_drift", (
        f"lowering CENSUS_DRIFT_CEILING to 0.003 gave {observed['a']!r} at "
        f"{CITY} {CEILING_YEAR}, not 'census_drift'. Its measured drift was "
        f"0.0042 when this was written; if it has moved, choose a ceiling that "
        f"trips it rather than deleting the case.")
    assert _pool_counts_reason(city, CEILING_YEAR, cfg) is None, (
        f"{CITY} {CEILING_YEAR} is still refused after the ceiling was "
        f"restored. The detector cannot go quiet, so it is not a detector.")

    # (b) the drift that could not be MEASURED — its own sentinel since
    #     2026-09-14, and it used to share `None` with "nothing was lost".
    #
    # ⛔ THE REAL PRODUCER RUNS, NOT A STUB RETURNING THE SENTINEL. The first
    # version of this case patched `_reprojection_drift` to hand back
    # `DRIFT_UNMEASURABLE` directly — and it stayed GREEN when the producer was
    # mutated back to returning `None`, because the constant still existed and
    # the call site still refused on it. That is the live control this
    # repository found the same week: a check that passes under the defect AND
    # under its fix. So the REAL function body executes and its own census read
    # is blinded for the length of the call, which is what makes the mixes come
    # out empty.
    real_drift = pools._reprojection_drift

    def blind_census_drift(*args, **kwargs):
        real_read = pools.read_census
        pools.read_census = lambda *a, **k: {}
        try:
            return real_drift(*args, **kwargs)
        finally:
            pools.read_census = real_read

    pools._reprojection_drift = blind_census_drift
    try:
        assert blind_census_drift(city, str(cfg.base().censuses[-1].delimitation),
                                  CEILING_YEAR, cfg) is pools.DRIFT_UNMEASURABLE, (
            f"the real `_reprojection_drift` did not return DRIFT_UNMEASURABLE "
            f"at {CITY} {CEILING_YEAR} with its census read blinded, so the "
            f"producer of the sentinel is not being exercised and this case "
            f"would pass with the sentinel deleted.")
        observed["b"] = _pool_counts_reason(city, CEILING_YEAR, cfg)
    finally:
        pools._reprojection_drift = real_drift
    assert observed["b"] == "census_drift_unmeasurable", (
        f"an unmeasurable drift at {CITY} {CEILING_YEAR} gave "
        f"{observed['b']!r}. If it served, the sentinel is being read as the "
        f"safe `None` again — which is the fail-open this entry closed.")
    assert _pool_counts_reason(city, CEILING_YEAR, cfg) is None, (
        f"{CITY} {CEILING_YEAR} is still refused after the patch was removed.")

    # (c) fewer than half the election's wards find a census population.
    real_pop = pools.read_census_population
    pools.read_census_population = lambda *a, **k: {"no_such_ward": 1.0}
    try:
        observed["c"] = _pool_counts_reason(city, JOIN_YEAR, cfg)
    finally:
        pools.read_census_population = real_pop
    assert observed["c"] == "census_wards_unmatched", (
        f"a census population keyed on wards this city does not have gave "
        f"{observed['c']!r}, not 'census_wards_unmatched'.")

    # (d) no ward joins at all: the composition comes back empty while the
    #     population still matches, so (c)'s guard passes and (d)'s fires.
    real_comp = pools.composition_at
    pools.composition_at = lambda *a, **k: ({}, None)
    try:
        observed["d"] = _pool_counts_reason(city, JOIN_YEAR, cfg)
    finally:
        pools.composition_at = real_comp
    assert observed["d"] == "census_no_join", (
        f"an empty ward composition gave {observed['d']!r}, not "
        f"'census_no_join'.")

    assert _pool_counts_reason(city, JOIN_YEAR, cfg) is None, (
        f"{CITY} {JOIN_YEAR} is still refused after both readers were "
        f"restored.")

    assert set(observed.values()) == set(pools.CENSUS_UNSAFE_REASONS), (
        f"the injections reached {sorted(set(observed.values()))} and "
        f"`pool_counts` declares {sorted(pools.CENSUS_UNSAFE_REASONS)}. A "
        f"refusal the module can raise and this file cannot reach is an "
        f"unguarded refusal; a case here for a reason the module no longer "
        f"raises is a guard watching a door that has moved.")


def test_a_genuinely_absent_file_is_dropped_quietly_as_not_on_disk():
    """⛔ THE DISCRIMINATOR. A repair that makes every refusal fatal fails here.

    "Not on disk" is a legitimate reason to pass over an election and the record
    must carry on. What it may not do is call it something else, or say nothing:
    the loss is filed as ``not_on_disk`` and the series is one year shorter with
    the reason recorded.
    """
    city = cityconfig.load(CITY)
    cfg = _cfg()
    calendar = cityconfig.CALENDAR
    victim = JOIN_YEAR
    original = calendar[victim]

    with _quiet():
        before = set(pools.registration_series(city, cfg))
    assert victim in before, (
        f"{victim} is not in {CITY}'s registration series to begin with, so "
        f"removing its file proves nothing.")

    calendar[victim] = dataclasses.replace(
        original, results="not_in_this_checkout_{CODE}.csv")
    try:
        with _quiet():
            during = set(pools.registration_series(city, cfg))
        losses = pools.pool_losses("registration_series", CITY)[
            ("registration_series", CITY)]
    finally:
        calendar[victim] = original

    assert victim not in during, f"{victim} survived its file being removed"
    assert losses.get(victim) == "not_on_disk", (
        f"a file that is genuinely not on disk was filed as "
        f"{losses.get(victim)!r}. Either it is unclassified — the silence this "
        f"guard forbids — or every refusal has been made fatal, which would "
        f"block eight cities from emitting on a defect that has been present "
        f"all along.")

    with _quiet():
        after = set(pools.registration_series(city, cfg))
    assert after == before, (
        f"after restoring the file the series is {sorted(after)}, not the "
        f"{sorted(before)} it started as.")


def test_a_real_typeerror_inside_pool_counts_propagates():
    """A BUG IS NOT A LOSS.

    ``panel_turnout_spread`` carried ``except (Exception, SystemExit)``, so a
    genuine ``TypeError`` or ``KeyError`` inside ``pool_counts`` was
    indistinguishable from a missing file — across the whole panel sweep, in
    silence. Both survivors of that clause are asserted here: the sweep and the
    registration series.
    """
    city = cityconfig.load(CITY)
    cfg = _cfg()

    class Boom(TypeError):
        """Raised by the stub and by nothing else."""

    real = pools.ward_totals

    def explode(*a, **k):
        raise Boom("a real bug, not a missing file")

    pools.ward_totals = explode
    try:
        for label, call in (
                ("registration_series",
                 lambda: pools.registration_series(city, cfg)),
                ("panel_turnout_spread",
                 lambda: (pools._PANEL_SPREAD_CACHE.clear(),
                          pools.panel_turnout_spread(cfg))),
        ):
            try:
                with _quiet():
                    call()
            except Boom:
                continue
            raise AssertionError(
                f"{label} swallowed a TypeError raised inside `pool_counts` "
                f"and carried on. A refusal is a loss; a bug is a bug, and the "
                f"old `except (Exception, SystemExit)` could not tell them "
                f"apart.")
    finally:
        pools.ward_totals = real
        pools._PANEL_SPREAD_CACHE.clear()


# --------------------------------------------------------------------------
# the CONSEQUENCE, not only the membership
# --------------------------------------------------------------------------

def test_a_swallowed_refusal_narrows_the_turnout_band():
    """⛔ ASSERT THE CONSEQUENCE. A guard that checks only which years are in the
    dict would stay green if the record were right and the band were computed
    from something else.

    The measured harm is a band that narrows with the centre unmoved: a forced
    joburg 2000 refusal took pool 2's width 0.7511 -> 0.5777, -23.1%. The widths
    are asserted here, and asserted to return EXACTLY on revert.
    """
    city = cityconfig.load(CITY)
    cfg = _cfg()

    # Called exactly as `emit_pools` calls it — the record, the panel spread and
    # the categories — so this measures the band the emit would produce and not
    # a differently-parameterised lookalike.
    categories = tuple(cfg.base().categories)

    def band():
        with _quiet():
            record = pools.turnout_record(city, cfg, kind="LGE")
            spread, _n_obs = pools.panel_turnout_spread(cfg)
        n = len(next(iter(record.values())))
        return record, pools.turnout_band(record, n, panel_spread=spread,
                                          categories=categories)

    before_record, before_band = band()
    if CEILING_YEAR not in before_record:
        skip(f"{CITY} {CEILING_YEAR} is not in the turnout record to begin with")

    original = pools.CENSUS_DRIFT_CEILING
    pools.CENSUS_DRIFT_CEILING = 0.003
    try:
        during_record, during_band = band()
    finally:
        pools.CENSUS_DRIFT_CEILING = original

    assert CEILING_YEAR not in during_record, (
        f"lowering the drift ceiling did not remove {CEILING_YEAR} from the "
        f"turnout record, so the consequence below is not the one being "
        f"measured.")
    assert set(before_record) - set(during_record) == {CEILING_YEAR}, (
        f"the injection removed {sorted(set(before_record) - set(during_record))}, "
        f"not just {CEILING_YEAR}.")

    widths_before = [hi - lo for lo, _mode, hi in before_band]
    widths_during = [hi - lo for lo, _mode, hi in during_band]
    modes_before = [m for _lo, m, _hi in before_band]
    modes_during = [m for _lo, m, _hi in during_band]

    assert any(w1 < w0 - 1e-9 for w0, w1 in zip(widths_before, widths_during)), (
        f"losing {CEILING_YEAR} left every band width at or above its original "
        f"({widths_before} -> {widths_during}). The measured effect is a band "
        f"that NARROWS — if it no longer does, the width is being computed from "
        f"something other than the record and this guard is watching the wrong "
        f"quantity.")
    assert np.allclose(modes_before, modes_during), (
        f"the band CENTRE moved ({modes_before} -> {modes_during}) when an "
        f"EARLIER election was dropped. The centre is `arr[-1]`, the most "
        f"recent LGE, so only losing THAT should re-centre it — the -0.4919 "
        f"Tshwane 2016 case. A centre that moves here means the two failure "
        f"magnitudes have stopped being distinguishable.")

    after_record, after_band = band()
    assert set(after_record) == set(before_record), (
        f"after restoring the ceiling the record is {sorted(after_record)}, not "
        f"{sorted(before_record)}.")
    assert np.allclose([hi - lo for lo, _m, hi in after_band], widths_before), (
        "the band widths did not return exactly on revert, so the detector "
        "cannot go quiet.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
