"""A stage observer for the ESTIMATION segment: 10_theta_prior -> 20_spine -> 30_centres.

WHAT THIS FILE IS. ``run_model`` emits every stage as JSON under ``--run-dir``
(:class:`montecarlo.Trace`, opt-in, byte-identical with and without it). Three of
those stages are a chain of estimates, each consuming the last:

  ``10_theta_prior``  per-party retention band and width, from the archive
  ``20_spine``        per-party central level, blending the national and local routes
  ``30_centres``      the level vector handed forward, before and after the shrink

The interesting properties are BETWEEN them: what must agree, what must be
conserved, and what may legitimately move. Nothing in the suite checked any of
it — ``test_theta_prior``, ``test_spine`` and ``test_blended_centres`` all call
the FUNCTIONS with constructed inputs, which is a different question from "is the
trace a faithful and self-consistent record of what the run did". A trace that is
read as evidence and is quietly wrong is worse than no trace, because it is
quoted.

⛔ THE SHAPE OF THIS FILE IS DELIBERATE, AND IT IS THE PART TO PRESERVE.

1. Every check is a **pure predicate over one stage payload**: a plain dict in,
   a list of human-readable faults out. No data, no model, no I/O. That is what
   lets each one be exercised against a CONSTRUCTED healthy payload and a
   CONSTRUCTED corrupted one.
2. **Every predicate carries a positive control.** ``CORRUPTIONS`` holds at
   least one constructed violation per registered predicate, and
   ``test_every_predicate_has_a_constructed_violation`` fails if a predicate is
   added without one. This repository has already shipped an observer that
   could not see — ``arrival_reconciliation`` was blind at 20 of 24 rows while
   reporting nothing amiss, because it inspected the post-relabel index. An
   observer that cannot demonstrate it can see is worse than none.
3. **The fixtures are constructed, not observed.** CLAUDE.md's requirement (3):
   a test whose premise is a passing state of the tree expires in silence.
   ``test_the_constructed_payloads_open_no_file`` proves the healthy payloads
   are built here rather than read off disk, and
   ``test_the_constructed_payloads_carry_a_real_trace_s_fields`` pins them to
   the shape a real run emits so they cannot drift apart from it.
4. **The population is bounded on both sides.** The predicate count is scanned
   against the number of fields the three stages emit, so a stage that grows a
   field it has no check for eventually trips the band rather than passing in
   silence.

WHAT A READER OF THESE STAGES MUST KNOW BEFORE QUOTING ONE. All four caught
somebody out while this file was written; the durable version is in
``skills/forecast-stage-estimation/SKILL.md``.

* ``30_centres`` holds TWO different vectors — ``before_shrink`` and
  ``after_shrink`` — and ``compress_levels`` renormalises over the membership of
  ``centres``. The TOTAL is conserved and no individual level is. A check on the
  wrong one of those is silent or screams forever.
* ``20_spine``'s ``level`` IS NOT the centre. Four routes can set a centre and
  the spine is only one of them: at joburg 2021, 32 of 55 parties (8.48pp of
  111.68pp of level) take the seeded-arrival route and sit at exactly
  ``spine_level / theta_centre``. ActionSA is the famous one — 5.85% in
  ``20_spine``, 6.84% in ``30_centres``.
* ``20_spine``'s ``detail[p]["national"]`` is not the party's national vote
  share. It is that share already multiplied by ``exp(mu_theta)``; ``local`` is
  likewise already through rho. Both are LEVELS, and the blend is between them.
* ``30_centres`` is not a share vector. It does not sum to one and is not meant
  to: it summed to 0.9952 at joburg 2011 and 1.1360 at joburg 2026, and
  ``pool_spec`` normalises it (``want = want / want.sum()``) at the next stage.
  So the total ``compress_levels`` conserves is discarded immediately afterwards
  — conservation is a property of the shrink, not of the forecast.

WHAT THIS FILE DOES NOT CHECK, stated so nobody reads its silence as coverage:

* **Whether the estimates are RIGHT.** Every predicate here is internal
  consistency. The only standard of correctness in this repository is a backtest
  against real election results (CLAUDE.md §1), and nothing in a trace can
  substitute for one.
* **The route that set each centre.** ``blended_centres`` computes a four-valued
  ``route`` local and the trace keeps it only where a note was written — the
  poll route and the by-election tilt. At every backtest target ``route_notes``
  is EMPTY, so the trace cannot say which route placed any party. See the report
  in SKILL.md; recording it is a change to ``montecarlo.py`` and is not this
  file's to make.
* **Anything downstream of ``30_centres``.** The centres are still mutated after
  the stage is written (the metro-poll blend, and ``centres["ENTRANT"] = 0.0``),
  so ``after_shrink`` is not necessarily the vector the drawer received.
"""

from __future__ import annotations

import argparse
import atexit
import builtins
import copy
import json
import math
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import (ROOT, election_files_read, run_module,   # noqa: E402
                      scanned, skip)

import cityconfig                                              # noqa: E402
import levels                                                  # noqa: E402
import montecarlo as mc                                        # noqa: E402

# The 10th/90th percentile z used by `levels.theta_prior` to turn a log-mean and
# a log-sd into the (low, mode, high) band. Named here because every band check
# below inverts it; it is not a tunable and has no register entry.
Z90 = 1.2816

# Two model runs, one per cycle. 2011 and 2021 are chosen because the cycle
# difference is the most interesting thing in this segment: the level shrink is
# cycle-blind, and the two cycles have OPPOSITE measured sign error at the top
# of the ballot. See `test_the_level_shrink_is_cycle_blind_by_construction`.
TRACE_YEARS = ("2011", "2021")
CITY = "joburg"
DRAWS = 40
SEED = 20261104


# ==========================================================================
# 10_theta_prior — the retention band and the width
# ==========================================================================
#
# FIELDS, and their units.
#   prior        {party: [low, mode, high]} — theta, a RATIO of a local share to
#                the national share it is measured off. Dimensionless. The band
#                is the 10th to 90th percentile of LogNormal(log mode, sd).
#   sd           {party: float} — sd(log theta) for that party, AFTER the
#                [sd_floor, sd_ceiling] clamp. The width the draw actually uses
#                (`make_drawer` reads `scenario["_theta_sd"]`, which is this).
#   worth        {party: float} — what the party's own theta record is worth, on
#                `_reliability`'s 0-1-per-observation scale. Keyed on parties
#                with a RECORD, so it is a subset of `prior`.
#   centre       {n, weighted_geomean, effective_n} — the record: how many
#                observations, their reliability-weighted geometric mean theta,
#                and the weight sum. NOT a median, despite the old name (§1.97).
#   spread       sd_for() evaluated at four sizes: 0.1%, 1%, 10%, 40%.
#   sd_floor,    the clamp, from `levels.SD_FLOOR` / `SD_CEILING` (0.15, 1.20).
#   sd_ceiling
#   at_the_floor the parties the FLOOR bound. There is no `at_the_ceiling`, and
#                the ceiling binds on far more parties — 21 of 44 at joburg
#                2021, 35 of 79 at 2026 — every one of them a party with no
#                national baseline, and so none of them carrying a centre.

def theta_the_band_is_the_measured_width(stage: dict) -> list[str]:
    """``log(high/low) / (2 * 1.2816)`` must be the party's own recorded ``sd``.

    The band and the width are two views of one lognormal, and they are written
    to the trace by different expressions. If they disagree, one of them is not
    the quantity the draw used — and `make_drawer` takes the WIDTH, so a reader
    quoting the band would be quoting the discarded one. §1.45 is the standing
    case: the draw was taking its spread from the band's endpoints squeezed into
    a triangular while the measurement sat beside it unused.
    """
    faults, prior, sd = [], stage.get("prior") or {}, stage.get("sd") or {}
    for party, band in prior.items():
        if not (isinstance(band, (list, tuple)) and len(band) == 3):
            faults.append(f"{party}: the prior is not a (low, mode, high) triple: {band!r}")
            continue
        low, mode, high = band
        if not all(_finite(v) and v > 0 for v in (low, mode, high)):
            faults.append(f"{party}: a non-positive or non-finite band {band!r}")
            continue
        if party not in sd:
            faults.append(f"{party}: has a band and no measured sd")
            continue
        implied = math.log(high / low) / (2 * Z90)
        if _rel(implied, sd[party]) > 1e-9:
            faults.append(
                f"{party}: the band implies sd(log theta) {implied:.6f} and the "
                f"recorded sd is {sd[party]:.6f}. The draw uses the RECORDED one.")
    return faults


def theta_the_mode_is_the_geometric_centre_of_its_band(stage: dict) -> list[str]:
    """``mode == sqrt(low * high)``, and ``low <= mode <= high``.

    A lognormal's 10th and 90th percentiles are symmetric in log space about its
    median, so the mode must sit exactly at their geometric mean. A mode that has
    drifted off the band it is quoted with is a shrink applied to one and not the
    other — §1.49 changed the shrink target and the whole suite failed to notice.
    """
    faults = []
    for party, band in (stage.get("prior") or {}).items():
        if not (isinstance(band, (list, tuple)) and len(band) == 3):
            continue
        low, mode, high = band
        if not all(_finite(v) and v > 0 for v in (low, mode, high)):
            continue
        if not low <= mode <= high:
            faults.append(f"{party}: the band is not ordered: {low:.6g}, {mode:.6g}, {high:.6g}")
        centre = math.sqrt(low * high)
        if _rel(centre, mode) > 1e-9:
            faults.append(
                f"{party}: mode {mode:.6g} is not the geometric centre of its "
                f"band ({centre:.6g}); the band and the mode came from different "
                f"log-means.")
    return faults


def theta_every_band_carries_a_width_and_every_record_a_band(stage: dict) -> list[str]:
    """``prior`` and ``sd`` cover exactly the same parties; ``worth`` is inside them.

    BOTH DIRECTIONS, deliberately. CLAUDE.md's requirement (0) is the one with
    the worst record here: the register guard checked code->register and never
    register->code, so a deleted lever sat in the register for days. A party with
    a band and no width reaches `sd_measured.get(party, sd_default)` and is drawn
    at a TYPED default; a party with a width and no band is a width computed for
    nobody.
    """
    faults = []
    prior, sd = set(stage.get("prior") or {}), set(stage.get("sd") or {})
    worth = set(stage.get("worth") or {})
    if prior - sd:
        faults.append(f"a band with no measured width: {sorted(prior - sd)[:6]}")
    if sd - prior:
        faults.append(f"a measured width with no band: {sorted(sd - prior)[:6]}")
    if worth - prior:
        faults.append(
            f"a party whose theta record is worth something and which has no "
            f"prior at all: {sorted(worth - prior)[:6]}")
    return faults


def theta_the_widths_lie_inside_the_declared_clamp(stage: dict) -> list[str]:
    """Every ``sd`` and every ``spread`` value is inside ``[sd_floor, sd_ceiling]``.

    `sd_for` IS `clip(sd_raw, SD_FLOOR, SD_CEILING)`, so a value outside the pair
    the trace declares means the clamp and the declaration have come apart — the
    reader would then be told the width is bounded when it is not.
    """
    low, high = stage.get("sd_floor"), stage.get("sd_ceiling")
    if not (_finite(low) and _finite(high) and 0 < low < high):
        return [f"the clamp is not an ordered positive pair: {low!r}, {high!r}"]
    faults = []
    for party, value in (stage.get("sd") or {}).items():
        if not _finite(value) or value < low - 1e-12 or value > high + 1e-12:
            faults.append(f"{party}: sd {value!r} outside the declared clamp [{low}, {high}]")
    for name, value in (stage.get("spread") or {}).items():
        if not _finite(value) or value < low - 1e-12 or value > high + 1e-12:
            faults.append(f"spread {name} = {value!r} outside the clamp [{low}, {high}]")
    return faults


def theta_the_floor_census_is_exact_in_both_directions(stage: dict) -> list[str]:
    """``at_the_floor`` is EXACTLY the parties whose ``sd`` equals ``sd_floor``.

    This is the one field in the stage that is a claim about a set, and a claim
    about a set is where this repository's scans have gone wrong: the calibration
    audit parsed one marked table and not the docstrings beside it, and reported
    nothing because it scanned the wrong population. Named-but-not-at-it and
    at-it-but-not-named are different defects and both are checked.

    It matters because §1.59 measured that the FLOOR, not the fit, sets the width
    for the top of the ballot — so this list is the account of which parties'
    width is a constant. At joburg 2021 it is exactly {ANC, DA}.
    """
    floor, sd = stage.get("sd_floor"), stage.get("sd") or {}
    if not _finite(floor):
        return [f"sd_floor is not a number: {floor!r}"]
    named = set(stage.get("at_the_floor") or [])
    actual = {p for p, v in sd.items() if _finite(v) and abs(v - floor) < 1e-12}
    faults = []
    if named - actual:
        faults.append(f"named at the floor and not at it: {sorted(named - actual)[:6]}")
    if actual - named:
        faults.append(f"at the floor and not named: {sorted(actual - named)[:6]}")
    return faults


def theta_the_dispersion_curve_falls_with_size(stage: dict) -> list[str]:
    """``spread`` is one monotone curve: at 0.1% >= at 1% >= at 10% >= at 40%.

    Two facts, and only the second is a judgement. STRUCTURALLY, `sd_for` is
    ``clip(exp(a + b*log size))`` — monotone in size by construction — so four
    values that are not monotone cannot have come from one call of it, whatever
    the slope. EMPIRICALLY the slope is negative: the archive says small parties
    are more volatile (0.476 / 0.288 / 0.174 / 0.150 at joburg 2021), which is
    Reif and Schmitt's second-order effect showing up as dispersion.

    If this fires, the dispersion fit has inverted — the model would be claiming
    to know a micro-party's local swing more precisely than the ANC's — and that
    is a finding to go and look at, not a flake to relax.
    """
    spread = stage.get("spread") or {}
    keys = ["at_0.1%", "at_1%", "at_10%", "at_40%"]
    if not all(k in spread for k in keys):
        return [f"spread is not the four-point curve: {sorted(spread)}"]
    faults = []
    for lo_key, hi_key in zip(keys, keys[1:]):
        a, b = spread[lo_key], spread[hi_key]
        if not (_finite(a) and _finite(b)):
            faults.append(f"spread {lo_key}/{hi_key} is not finite: {a!r}, {b!r}")
        elif b > a + 1e-12:
            faults.append(
                f"sd(log theta) RISES with size: {lo_key} = {a:.4f} is below "
                f"{hi_key} = {b:.4f}. The dispersion fit has inverted.")
    return faults


def theta_the_record_is_counted_consistently(stage: dict) -> list[str]:
    """``centre``: a positive count, a positive geometric mean, ``effective_n <= n``.

    ``effective_n`` is the sum of `_reliability(share)`, which is bounded above
    by 1 per observation, so it can never exceed ``n``. If it does, the weights
    are not reliabilities any more and every shrinkage keyed on them has moved.
    """
    centre = stage.get("centre") or {}
    n, eff, geo = centre.get("n"), centre.get("effective_n"), centre.get("weighted_geomean")
    faults = []
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        faults.append(f"centre.n is not a positive count of observations: {n!r}")
    if not _finite(eff) or eff <= 0:
        faults.append(f"centre.effective_n is not positive: {eff!r}")
    elif isinstance(n, int) and not isinstance(n, bool) and eff > n + 1e-9:
        faults.append(
            f"centre.effective_n {eff:.4f} exceeds centre.n {n}: a reliability "
            f"weight above 1, so the record is worth more than it holds.")
    if not _finite(geo) or geo <= 0:
        faults.append(f"centre.weighted_geomean is not a positive ratio: {geo!r}")
    return faults


THETA_PREDICATES = {fn.__name__: fn for fn in (
    theta_the_band_is_the_measured_width,
    theta_the_mode_is_the_geometric_centre_of_its_band,
    theta_every_band_carries_a_width_and_every_record_a_band,
    theta_the_widths_lie_inside_the_declared_clamp,
    theta_the_floor_census_is_exact_in_both_directions,
    theta_the_dispersion_curve_falls_with_size,
    theta_the_record_is_counted_consistently,
)}


# ==========================================================================
# 20_spine — the two records, weighted by which one the party has
# ==========================================================================
#
# FIELDS, and their units.
#   level        {party: float} — the blended CENTRAL CITYWIDE SHARE, 0-1. Not
#                a ratio: theta and rho have already been applied.
#   k            the blend constant actually used (`SPINE_K` = 1.0 unless swept).
#   n_theta,     the size of each record, in observations. `n_theta` is the same
#   n_rho        number as `10_theta_prior`'s `centre.n`.
#   theta_centre exp of the reliability-weighted mean of log theta over the whole
#                record — the same number as `10_theta_prior`'s
#                `centre.weighted_geomean`, computed by a different function.
#   rho_centre   the same for the local-to-local record.
#   detail       {party: {w_local, worth, route, national, local}}.
#                ⚠ `national` and `local` are LEVELS, not the party's raw shares:
#                each is already its share times exp(its route's log-mean).
#                `w_local` is the weight on the LOCAL route = k / (worth + k).
#   absorption   routes census, the blend's disagreement accounting, the names of
#                the parties dropped and of those whose level nothing can read,
#                and each route's shrink account. Write-only in the model.

def _spine_rows(stage: dict):
    return (stage.get("detail") or {}), (stage.get("level") or {})


def spine_every_level_has_a_detail_row(stage: dict) -> list[str]:
    """``level`` and ``detail`` cover exactly the same parties, and rows are whole.

    ``detail`` is how a reader answers "why is this party at this number?". A
    level with no row is a number with no account of itself; a row with no level
    is an account of something the model did not keep.
    """
    detail, level = _spine_rows(stage)
    faults = []
    if set(detail) != set(level):
        faults.append(
            f"level and detail disagree: level with no row "
            f"{sorted(set(level) - set(detail))[:6]}, row with no level "
            f"{sorted(set(detail) - set(level))[:6]}")
    for party, row in detail.items():
        missing = [k for k in ("w_local", "worth", "route", "national", "local")
                   if k not in row]
        if missing:
            faults.append(f"{party}: the detail row is missing {missing}")
    return faults


def spine_the_level_is_the_geometric_blend_of_its_two_routes(stage: dict) -> list[str]:
    """``level == local**w * national**(1-w)``, exactly, on every row.

    This is the whole arithmetic of the stage, checked against the three numbers
    the row reports rather than re-derived from the archive. A row whose level is
    not the blend of the routes it names is reporting an arithmetic that did not
    happen, and the detail block exists precisely to be believed.

    The degenerate rows are checked too: a national-only party must sit exactly
    on its national route, a local-only party exactly on its local one.
    """
    detail, level = _spine_rows(stage)
    faults = []
    for party, row in detail.items():
        if party not in level:
            continue
        try:
            w, loc, nat, got = (float(row["w_local"]), float(row["local"]),
                                float(row["national"]), float(level[party]))
        except (KeyError, TypeError, ValueError):
            faults.append(f"{party}: the row is not numeric: {row!r}")
            continue
        if loc > 0 and nat > 0:
            want = math.exp(w * math.log(loc) + (1 - w) * math.log(nat))
        elif nat > 0:
            want = nat
        elif loc > 0:
            want = loc
        else:
            faults.append(f"{party}: carries a level {got:.6g} with neither route")
            continue
        if _rel(want, got) > 1e-9:
            faults.append(
                f"{party}: level {got:.8g}, but the blend of the routes the row "
                f"reports (local {loc:.6g}, national {nat:.6g}, w_local {w:.4f}) "
                f"is {want:.8g}")
    return faults


def spine_a_blended_level_is_bracketed_by_its_routes(stage: dict) -> list[str]:
    """A blend is a compromise: ``min(routes) <= level <= max(routes)``.

    Implied by the geometric blend above and stated separately on purpose. It is
    the READER's invariant — the one property that survives a change to the
    blend's functional form — so it must keep failing if the form is replaced by
    something that can leave the interval.
    """
    detail, level = _spine_rows(stage)
    faults = []
    for party, row in detail.items():
        loc, nat = row.get("local", 0.0), row.get("national", 0.0)
        if loc > 0 and nat > 0 and party in level:
            low, high = min(loc, nat), max(loc, nat)
            if not low - 1e-12 <= level[party] <= high + 1e-12:
                faults.append(
                    f"{party}: level {level[party]:.6g} is outside its two routes "
                    f"[{low:.6g}, {high:.6g}] — that is a selection, not a blend")
    return faults


def spine_the_route_label_describes_the_arithmetic(stage: dict) -> list[str]:
    """The label must say what HAPPENED, not which branch ran (§1.97 F7).

    A party with both records and no theta evidence gets ``w = 1.0`` — one
    hundred per cent its own last local result, nothing blended — and was
    labelled "blend" anyway. For ActionSA at 2026 the label said the national
    route was contributing when it was not, and the label is exactly what a
    reader checks when asking why a party sits where it does.

    Checked both ways round: the label must follow the numbers AND the numbers
    must follow the label.
    """
    detail, _ = _spine_rows(stage)
    faults = []
    for party, row in detail.items():
        w, loc, nat = row.get("w_local"), row.get("local"), row.get("national")
        route = str(row.get("route", ""))
        if not (_finite(w) and _finite(loc) and _finite(nat)):
            faults.append(f"{party}: non-numeric row {row!r}")
            continue
        if not -1e-12 <= w <= 1 + 1e-12:
            faults.append(f"{party}: w_local {w} is not a weight in [0, 1]")
        both, nat_only, loc_only = (loc > 0 and nat > 0), (nat > 0 >= loc), (loc > 0 >= nat)
        if both and not route.startswith("blend"):
            faults.append(f"{party}: has both records and is labelled {route!r}")
        if nat_only:
            if not route.startswith("national only"):
                faults.append(f"{party}: has a national record only and is labelled {route!r}")
            if w != 0.0:
                faults.append(f"{party}: national-only route carrying local weight {w}")
        if loc_only:
            if not route.startswith("local only"):
                faults.append(f"{party}: has a local record only and is labelled {route!r}")
            if w != 1.0:
                faults.append(f"{party}: local-only route at local weight {w}, not 1.0")
        if both:
            full_local, full_national = w >= 1.0, w <= 0.0
            if full_local != ("full local" in route):
                faults.append(
                    f"{party}: w_local {w:.4f} and the label {route!r} disagree "
                    f"about whether the national route contributed anything")
            if full_national != ("full national" in route):
                faults.append(
                    f"{party}: w_local {w:.4f} and the label {route!r} disagree "
                    f"about whether the local route contributed anything")
    return faults


def spine_the_blend_weight_is_keyed_on_what_the_record_is_worth(stage: dict) -> list[str]:
    """``w_local == k / (worth + k)``, with ``w = 0`` when ``worth + k <= 0``.

    Two shipped defects live in this one line. F1: ``scenario.get("spine_k") or
    SPINE_K`` made ``spine_k = 0`` undeliverable, so a whole sweep of it measured
    the default at every value. F2: ``k / (worth + k)`` is 0/0 for a party with
    both records and no theta evidence, and it raised out of the middle of
    ``run_model`` for five parties at joburg 2026. The limit taken there is a
    registered JUDGEMENT CALL, not a derivation — ``w = 0`` keeps "k = 0 means
    pure national spine" true for every party — so it is pinned here.
    """
    detail, _ = _spine_rows(stage)
    k = stage.get("k")
    if not _finite(k) or k < 0:
        return [f"the recorded k is not a non-negative number: {k!r}"]
    faults = []
    for party, row in detail.items():
        if not (row.get("local", 0) > 0 and row.get("national", 0) > 0):
            continue
        worth = row.get("worth")
        if not _finite(worth) or worth < 0:
            faults.append(f"{party}: worth {worth!r} is not a non-negative weight")
            continue
        want = 0.0 if (worth + k) <= 0 else k / (worth + k)
        if abs(want - row["w_local"]) > 1e-9:
            faults.append(
                f"{party}: w_local {row['w_local']:.6f}, but k/(worth+k) with the "
                f"k and worth this row reports (k={k}, worth={worth:.4f}) is "
                f"{want:.6f}. The weight is keyed on something else.")
    return faults


def spine_the_route_census_matches_the_rows(stage: dict) -> list[str]:
    """``absorption.routes`` is a census OF ``detail``, and the dropped are absent.

    The counters and the rows are built in the same loop and can still come
    apart — ``routes["blend"]`` deliberately counts a row labelled "blend at full
    local", because that counter is about WHICH RECORDS the party has. This
    pins that decision so it cannot be silently reversed, and checks the two
    name lists against the rows they describe.
    """
    detail, level = _spine_rows(stage)
    absorption = stage.get("absorption") or {}
    routes = absorption.get("routes") or {}
    faults, seen = [], {"blend": 0, "national_only": 0, "local_only": 0}
    for party, row in detail.items():
        route = str(row.get("route", ""))
        if route.startswith("blend"):
            seen["blend"] += 1
        elif route.startswith("national only"):
            seen["national_only"] += 1
        elif route.startswith("local only"):
            seen["local_only"] += 1
        else:
            faults.append(f"{party}: route {route!r} belongs to no counted class")
    for key, count in seen.items():
        if routes.get(key) != count:
            faults.append(f"routes[{key}] says {routes.get(key)!r}; the rows hold {count}")
    dropped = absorption.get("dropped_parties") or []
    if routes.get("dropped") != len(dropped):
        faults.append(
            f"routes[dropped] says {routes.get('dropped')!r} and "
            f"{len(dropped)} parties are named")
    for party in dropped:
        if party in level or party in detail:
            faults.append(f"{party} is named as dropped and is also carried")
    for party in (absorption.get("local_only_unused") or []):
        if party not in detail:
            faults.append(f"{party} is named local_only_unused and has no row")
        elif not str(detail[party].get("route", "")).startswith("local only"):
            faults.append(
                f"{party} is named local_only_unused and its route is "
                f"{detail[party].get('route')!r}")
    return faults


def spine_the_disagreement_account_adds_up(stage: dict) -> list[str]:
    """The blend's absorption block must be arithmetic, not decoration.

    ``moved_from_national + moved_from_local == disagreement`` (the weight splits
    the gap and loses none of it), ``share_local`` is the quotient it claims to
    be, the finite and non-finite rows account for every blend row, and the two
    saturation counts are censuses of the rows.

    This block is the only thing that can distinguish "changing the national
    route did not move the forecast" from "the national route was never worth
    anything here" (NULL-RESULTS.md 4.3). It is write-only in the model, which
    is exactly why nothing else would notice it going wrong.
    """
    detail, _ = _spine_rows(stage)
    absorption = stage.get("absorption") or {}
    blend, routes = absorption.get("blend") or {}, absorption.get("routes") or {}
    if not blend:
        return ["the blend absorption block is missing"]
    faults = []
    gap, from_nat, from_loc = (blend.get("disagreement"),
                               blend.get("moved_from_national"),
                               blend.get("moved_from_local"))
    for name, value in (("disagreement", gap), ("moved_from_national", from_nat),
                        ("moved_from_local", from_loc)):
        if not _finite(value) or value < -1e-12:
            faults.append(f"blend.{name} is not a non-negative total: {value!r}")
    if faults:
        return faults
    if gap > 0 and _rel(from_nat + from_loc, gap) > 1e-9:
        faults.append(
            f"the disagreement does not split: moved_from_national {from_nat:.6f} "
            f"+ moved_from_local {from_loc:.6f} != disagreement {gap:.6f}")
    want_share = (from_nat / gap) if gap > 0 else 0.0
    if abs(want_share - blend.get("share_local", -1.0)) > 1e-9:
        faults.append(
            f"share_local {blend.get('share_local')!r} is not "
            f"moved_from_national/disagreement ({want_share:.6f})")
    if blend.get("n", 0) + blend.get("nonfinite", 0) != routes.get("blend"):
        faults.append(
            f"blend accounted for {blend.get('n')} finite + "
            f"{blend.get('nonfinite')} non-finite rows against "
            f"{routes.get('blend')!r} blend-route parties")
    full_local = sum(1 for r in detail.values()
                     if r.get("local", 0) > 0 and r.get("national", 0) > 0
                     and r.get("w_local", 0) >= 1.0)
    full_national = sum(1 for r in detail.values()
                        if r.get("local", 0) > 0 and r.get("national", 0) > 0
                        and r.get("w_local", 1) <= 0.0)
    if blend.get("at_full_local") != full_local:
        faults.append(f"at_full_local {blend.get('at_full_local')!r}; {full_local} rows sit at w=1")
    if blend.get("at_full_national") != full_national:
        faults.append(
            f"at_full_national {blend.get('at_full_national')!r}; "
            f"{full_national} rows sit at w=0")
    return faults


def spine_the_shrink_accounts_are_bounded(stage: dict) -> list[str]:
    """``0 <= absorbed <= offered``, ``share == absorbed/offered``, target is named.

    The shrink can take back at most what the parties' own evidence offered. An
    ``absorbed`` above ``offered`` is a stage reporting that it ate more than it
    was given, which would make every ``ABSORBED:`` label downstream of it wrong.
    """
    absorption = stage.get("absorption") or {}
    faults = []
    for name in ("theta_shrink", "rho_shrink"):
        block = absorption.get(name) or {}
        if not block:
            faults.append(f"{name} is missing from the absorption account")
            continue
        offered, absorbed, share = (block.get("offered"), block.get("absorbed"),
                                    block.get("share"))
        if not (_finite(offered) and _finite(absorbed) and _finite(share)):
            faults.append(f"{name}: the account is not numeric: {block!r}")
            continue
        if absorbed < -1e-12 or offered < -1e-12 or absorbed > offered + 1e-9:
            faults.append(
                f"{name}: absorbed {absorbed:.6f} is outside [0, offered "
                f"{offered:.6f}] — the stage ate more than it was offered")
        want = (absorbed / offered) if offered > 0 else 0.0
        if abs(want - share) > 1e-9:
            faults.append(f"{name}: share {share!r} is not absorbed/offered ({want:.6f})")
        if block.get("target") not in ("size_centre", "flat_common_centre", None):
            faults.append(f"{name}: unknown shrink target {block.get('target')!r}")
    return faults


def spine_the_levels_and_the_group_centres_are_positive(stage: dict) -> list[str]:
    """Every level is a positive share; both group centres are positive ratios.

    A level of zero or below is not a small party, it is a party the blend lost:
    the blend is taken in logs, so a zero on either route would propagate as a
    ``-inf`` and arrive here as a 0.0 that reads like an estimate.
    """
    faults = []
    for name in ("theta_centre", "rho_centre"):
        value = stage.get(name)
        if not _finite(value) or value <= 0:
            faults.append(f"{name} is not a positive retention ratio: {value!r}")
    for name in ("n_theta", "n_rho"):
        value = stage.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            faults.append(f"{name} is not a count of observations: {value!r}")
    for party, value in (stage.get("level") or {}).items():
        if not _finite(value) or value <= 0:
            faults.append(f"{party}: level {value!r} is not a positive share")
    return faults


SPINE_PREDICATES = {fn.__name__: fn for fn in (
    spine_every_level_has_a_detail_row,
    spine_the_level_is_the_geometric_blend_of_its_two_routes,
    spine_a_blended_level_is_bracketed_by_its_routes,
    spine_the_route_label_describes_the_arithmetic,
    spine_the_blend_weight_is_keyed_on_what_the_record_is_worth,
    spine_the_route_census_matches_the_rows,
    spine_the_disagreement_account_adds_up,
    spine_the_shrink_accounts_are_bounded,
    spine_the_levels_and_the_group_centres_are_positive,
)}


# ==========================================================================
# 30_centres — the level vector, before and after the shrink
# ==========================================================================
#
# FIELDS, and their units.
#   before_shrink  {party: float} — the central citywide level per party, 0-1,
#                  as the four routes of `blended_centres` left it. NOT
#                  normalised: it summed to 0.9952 at joburg 2011 and 1.1360 at
#                  joburg 2026, and `pool_spec` divides by that total later.
#   after_shrink   the same vector after `compress_levels`. THIS IS A DIFFERENT
#                  VECTOR and confusing the two is this project's recurring
#                  defect.
#   ratio          after/before per party, or null where before is 0.
#   level_shrink   `c` in `1 - c*s/(s+h)`; ships at 0.35.
#   level_shrink_scale  `h`, the share at which the pull is half strength; 0.04.
#   route_notes    per-party prose, written ONLY on the poll route and the
#                  by-election tilt. Empty at every backtest target, so the trace
#                  cannot say which route placed a party. See the module
#                  docstring.

def centres_the_three_vectors_cover_the_same_parties(stage: dict) -> list[str]:
    """``before_shrink``, ``after_shrink`` and ``ratio`` are keyed alike; notes are inside.

    ``compress_levels`` renormalises over the MEMBERSHIP of ``centres`` — ``total``
    and ``freed`` are both sums over it — so one extra key rescales every party.
    ``blended_centres`` raises rather than let the membership move, and this is
    the same claim made about what was written down.
    """
    before = stage.get("before_shrink") or {}
    after = stage.get("after_shrink") or {}
    ratio = stage.get("ratio") or {}
    faults = []
    if set(before) != set(after):
        faults.append(f"before/after cover different parties: {sorted(set(before) ^ set(after))[:6]}")
    if set(before) != set(ratio):
        faults.append(f"before/ratio cover different parties: {sorted(set(before) ^ set(ratio))[:6]}")
    for name, vector in (("before", before), ("after", after)):
        for party, value in vector.items():
            if not _finite(value) or value < 0:
                faults.append(f"{party}: {name}_shrink is not a non-negative level: {value!r}")
    stray = set(stage.get("route_notes") or {}) - set(before)
    if stray:
        faults.append(f"a route note for a party with no centre: {sorted(stray)[:6]}")
    return faults


def centres_the_shrink_conserves_the_total(stage: dict) -> list[str]:
    """The TOTAL is conserved; no individual level is.

    ``compress_levels`` pulls each party down by ``1 - c*s/(s+h)`` and returns the
    freed mass by renormalising to the ORIGINAL total. So this is the only
    quantity the stage conserves, and an observer that checked individual levels
    instead would scream on every run while one that checked nothing would be
    silent. Equivalently: the SIZE-WEIGHTED mean of ``ratio`` is exactly 1, which
    is why the largest party's ratio can never exceed 1.

    ⚠ The total conserved here is discarded at the next stage — ``pool_spec``
    does ``want = want / want.sum()``. Conservation is a property of the shrink,
    not a claim that the level vector is a ballot.
    """
    before = stage.get("before_shrink") or {}
    after = stage.get("after_shrink") or {}
    total_before = sum(v for v in before.values() if _finite(v) and v > 0)
    total_after = sum(v for v in after.values() if _finite(v) and v > 0)
    if total_before <= 0:
        return ["the centres before the shrink hold no positive mass at all"]
    if _rel(total_before, total_after) > 1e-12:
        return [f"the shrink moved the total: {total_before:.12f} -> "
                f"{total_after:.12f} ({(total_after - total_before) * 100:+.6f}pp). "
                f"compress_levels renormalises to the original total, so this is "
                f"mass created or destroyed."]
    return []


def centres_the_total_is_a_plausible_ballot(stage: dict) -> list[str]:
    """Two-sided bound on the level vector's total: ``0.5 <= sum <= 2.0``.

    CLAUDE.md requirement (1), and it is not decoration here. The total is NOT
    constrained to 1 — each party's level is estimated on its own and nothing
    adds them up — so it drifts with how fragmented the ballot is: 0.9952 (11
    parties, 2011), 1.0567 (24, 2016), 1.1168 (55, 2021), 1.1360 (44, 2026). The
    next stage divides by it, so that drift is an unlabelled per-cycle deflation
    of the whole vector.

    The band exists to catch the two states that would otherwise pass in silence:
    a centres vector that has lost most of its parties, and one that has been
    handed a second copy of them.
    """
    before = stage.get("before_shrink") or {}
    total = sum(v for v in before.values() if _finite(v) and v > 0)
    if not 0.5 <= total <= 2.0:
        return [f"the level vector totals {total:.4f}, outside [0.5, 2.0]. It is "
                f"not normalised and is not expected to be exactly 1, but this "
                f"far out it has either lost its parties or gained a duplicate set."]
    return []


def centres_the_recorded_ratio_is_after_over_before(stage: dict) -> list[str]:
    """``ratio[p] == after[p] / before[p]``, and ``null`` exactly where before is 0.

    The ratio is the field a reader actually looks at, and it is computed by a
    third expression rather than taken from either vector. A ratio that has come
    apart from the pair would misreport the direction of the shrink for every
    party at once.
    """
    before = stage.get("before_shrink") or {}
    after = stage.get("after_shrink") or {}
    ratio = stage.get("ratio") or {}
    faults = []
    for party, value in before.items():
        if party not in after or party not in ratio:
            continue
        if value > 0:
            want = after[party] / value
            if ratio[party] is None or _rel(want, ratio[party]) > 1e-12:
                faults.append(f"{party}: ratio {ratio[party]!r} is not after/before ({want:.12f})")
        elif ratio[party] is not None:
            faults.append(f"{party}: before is {value!r} and the ratio is {ratio[party]!r}, not null")
    return faults


def centres_the_pull_is_monotone_in_size(stage: dict) -> list[str]:
    """A bigger party never keeps more of its level than a smaller one.

    ``1 - c*s/(s+h)`` is monotone decreasing in ``s`` and the renormalisation is a
    single common factor, so the ordering is exact and is the mechanism's whole
    claim. A hard threshold was measured first and rejected because where the
    line falls decides the answer (−13.2% at 5%, −5.6% at 8%, −0.8% at 15%); this
    form has no line, and if a line ever reappears this is what sees it.

    It is also what catches ``before_shrink`` and ``after_shrink`` being recorded
    on the wrong sides of ``compress_levels``: swapping them inverts every ratio.
    """
    before = stage.get("before_shrink") or {}
    ratio = stage.get("ratio") or {}
    rows = sorted((v, p) for p, v in before.items()
                  if _finite(v) and v > 0 and _finite(ratio.get(p)))
    faults = []
    for (small_v, small_p), (big_v, big_p) in zip(rows, rows[1:]):
        if ratio[big_p] > ratio[small_p] + 1e-9:
            faults.append(
                f"the bigger party kept MORE: {small_p} at {small_v:.5f} kept "
                f"{ratio[small_p]:.4f}, {big_p} at {big_v:.5f} kept {ratio[big_p]:.4f}")
    return faults


def centres_the_shrink_takes_from_the_top_and_gives_to_the_bottom(stage: dict) -> list[str]:
    """The largest party is pulled down and the smallest lifted — AT EVERY CYCLE.

    ⛔ THIS PASSING IS THE STATEMENT OF A LIVE DEFECT, NOT A CLEAN BILL. The
    shrink is unconditional and cycle-blind, and the measured signed vote-share
    error for ranks 1-3 summed over eight metros is **−40.81pp at 2011, −7.45 at
    2016, +24.76 at 2021**. A non-negative shrink is therefore applied to a cycle
    where the top of the ballot is already UNDER-forecast by forty points. Fix
    #16; not this file's to make.

    What the assertion buys is that the sign is visible and pinned: if somebody
    makes the shrink cycle-aware, this fails and forces the documentation to move
    with it (CLAUDE.md §2). ``test_the_level_shrink_is_cycle_blind_by_construction``
    prints the per-cycle magnitude on real traces.
    """
    before = stage.get("before_shrink") or {}
    ratio = stage.get("ratio") or {}
    c, h = stage.get("level_shrink") or 0.0, stage.get("level_shrink_scale") or 0.0
    rows = sorted((v, p) for p, v in before.items()
                  if _finite(v) and v > 0 and _finite(ratio.get(p)))
    if len(rows) < 2:
        return []
    smallest, biggest = rows[0][1], rows[-1][1]
    if c <= 0 or h <= 0:
        return []
    faults = []
    if ratio[biggest] > 1.0 + 1e-12:
        faults.append(
            f"the largest party {biggest} was LIFTED by the shrink (ratio "
            f"{ratio[biggest]:.4f}). The mechanism's direction has reversed.")
    if ratio[smallest] < 1.0 - 1e-12:
        faults.append(
            f"the smallest party {smallest} was PULLED DOWN by the shrink (ratio "
            f"{ratio[smallest]:.4f}). The freed mass is not being returned.")
    return faults


def centres_the_off_switch_is_the_identity(stage: dict) -> list[str]:
    """With ``level_shrink`` or its scale at zero, nothing moved AT ALL.

    ``compress_levels`` returns its input object untouched on the off path, so
    "off" means bit-for-bit identical and not "identical to a rounding error". If
    the off path ever renormalised a copy, every committed forecast would move
    for a logging change.
    """
    before = stage.get("before_shrink") or {}
    after = stage.get("after_shrink") or {}
    c, h = stage.get("level_shrink") or 0.0, stage.get("level_shrink_scale") or 0.0
    if c > 0 and h > 0:
        return []
    return [f"{party}: the shrink is off (c={c!r}, h={h!r}) and the centre moved "
            f"{value!r} -> {after.get(party)!r}"
            for party, value in before.items() if after.get(party) != value]


def centres_the_recorded_levers_reproduce_the_shrink(stage: dict) -> list[str]:
    """``compress_levels(before, {c, h}) == after``, using the c and h RECORDED here.

    The sharpest check in the segment, and the one that needs the shipped
    function rather than a copy of its arithmetic: it pins the emitted pair to
    the levers the stage claims produced it. It fails if the recorded levers are
    not the ones the run used — the lever-reporting class ``test_levers_are_live``
    exists for, where ``scenario.get("spine_k") or SPINE_K`` made a swept value
    undeliverable while the sweep dutifully reported rows.

    It is NOT a re-derivation of the model's answer: the input is the model's own
    ``before_shrink``, so this asserts the record is internally coherent, not that
    the shrink is right.
    """
    before = stage.get("before_shrink") or {}
    after = stage.get("after_shrink") or {}
    if not before:
        return []
    scenario = {"level_shrink": stage.get("level_shrink"),
                "level_shrink_scale": stage.get("level_shrink_scale")}
    want = mc.compress_levels(dict(before), scenario)
    faults = []
    for party, value in want.items():
        got = after.get(party)
        if got is None or _rel(value, got) > 1e-12:
            faults.append(
                f"{party}: compress_levels on the recorded before_shrink with the "
                f"recorded levers (c={scenario['level_shrink']!r}, "
                f"h={scenario['level_shrink_scale']!r}) gives {value:.12g}; the "
                f"trace recorded {got!r}")
    return faults[:8]


CENTRES_PREDICATES = {fn.__name__: fn for fn in (
    centres_the_three_vectors_cover_the_same_parties,
    centres_the_shrink_conserves_the_total,
    centres_the_total_is_a_plausible_ballot,
    centres_the_recorded_ratio_is_after_over_before,
    centres_the_pull_is_monotone_in_size,
    centres_the_shrink_takes_from_the_top_and_gives_to_the_bottom,
    centres_the_off_switch_is_the_identity,
    centres_the_recorded_levers_reproduce_the_shrink,
)}


# ==========================================================================
# between the stages — the part nothing else can see
# ==========================================================================

def cross_the_two_stages_read_one_theta_record(payloads) -> list[str]:
    """``20_spine.theta_centre`` IS ``10_theta_prior.centre.weighted_geomean``.

    Both are ``exp`` of the reliability-weighted mean of ``log theta`` over the
    whole record, and they are computed by two different functions —
    ``theta_prior`` inline, ``spine`` through ``_shrunk``. §1.49 is the standing
    warning: these two estimators shrank toward DIFFERENT centres for weeks
    (ANC 0.869 against 0.862, PA 1.115 against 1.197) and the register carried it
    at red as "at least one is wrong". ``n_theta`` against ``centre.n`` is the
    same claim about the record's size.

    If this fires, the two stages are looking at different archives — a
    ``THETA_WINDOW`` or an exclusion applied on one path and not the other — and
    every downstream comparison between them is meaningless.
    """
    theta, spine, _ = payloads
    faults = []
    geo = (theta.get("centre") or {}).get("weighted_geomean")
    centre = spine.get("theta_centre")
    if _finite(geo) and _finite(centre) and _rel(geo, centre) > 1e-12:
        faults.append(
            f"one quantity, two answers: 10_theta_prior's weighted geomean is "
            f"{geo:.12f} and 20_spine's theta_centre is {centre:.12f}")
    n = (theta.get("centre") or {}).get("n")
    if isinstance(n, int) and not isinstance(n, bool) and spine.get("n_theta") != n:
        faults.append(
            f"the theta record is {n} observations at 10_theta_prior and "
            f"{spine.get('n_theta')!r} at 20_spine")
    return faults


def cross_the_blend_weight_and_the_shrink_use_one_worth(payloads) -> list[str]:
    """``detail[p]["worth"]`` IS ``10_theta_prior.worth[p]``, both directions.

    ``levels.py`` claims this in a comment — "reported rather than recomputed so
    the weight and the shrinkage can never be keyed on different numbers" — and
    nothing asserted it. It is the quantity the spine's blend weight is keyed on
    AND the quantity ``theta_prior``'s shrinkage is keyed on, so a divergence
    would move every blended party and every band at once.

    The reverse direction matters as much: a row reporting positive worth for a
    party with no theta record at all means the two stages disagree about who has
    a record, not merely about how much it is worth.
    """
    theta, spine, _ = payloads
    worth, detail = theta.get("worth") or {}, spine.get("detail") or {}
    faults, shared = [], 0
    for party, row in detail.items():
        own = row.get("worth")
        if party in worth:
            shared += 1
            if _rel(worth[party], own) > 1e-12:
                faults.append(
                    f"{party}: theta worth {worth[party]:.9f} at 10_theta_prior "
                    f"and {own!r} at 20_spine")
        elif _finite(own) and own > 0:
            faults.append(
                f"{party}: 20_spine says its theta record is worth {own:.4f} and "
                f"10_theta_prior has no record for it at all")
    if worth and detail and shared == 0:
        faults.append(
            "no party carries a theta worth in both stages: the two are keyed on "
            "different party names, and the agreement above is vacuous")
    return faults


def cross_every_centre_has_a_level_behind_it(payloads) -> list[str]:
    """Every party in ``30_centres`` has a spine level or a theta prior.

    ``blended_centres`` has four routes and a raising ``else``: a party with a
    national baseline, no spine level, no theta prior and no arrival seed used to
    be absorbed by a per-party typed constant and there is no longer one
    (§1.52). A seeded arrival reaches the spine too, because the seed loop adds
    it to the baseline before ``spine`` is called. So a centre with neither
    record behind it means a fifth route has appeared with nothing recorded about
    where its number came from.
    """
    theta, spine, centres = payloads
    before = centres.get("before_shrink") or {}
    known = set(spine.get("level") or {}) | set(theta.get("prior") or {})
    orphans = sorted(set(before) - known)
    if orphans:
        return [f"a centre with no spine level and no theta prior behind it: {orphans[:8]}"]
    return []


def cross_the_spine_still_reaches_the_centres(payloads) -> list[str]:
    """At least one in six centres sits EXACTLY on its spine level.

    A positive control on the seam, and the F37 concern made checkable: an absent
    spine and a spine that reached nobody both degrade every party to the theta
    route in silence, and a run with no spine at all was indistinguishable from
    one where the spine reached everyone.

    The share is genuinely low and genuinely variable — 100% at joburg 2011, 42%
    at joburg 2021, 40% at cape town 2021, 80% at joburg 2026 — because the other
    three routes (poll, seed, by-election tilt) legitimately override it. The
    floor is set well under the observed minimum; what it catches is the seam
    going to ZERO, which is the failure that reads as a working model.
    """
    _, spine, centres = payloads
    level = spine.get("level") or {}
    before = centres.get("before_shrink") or {}
    shared = [p for p in before if p in level]
    if not shared:
        return ["no party in 30_centres appears in 20_spine at all: the two "
                "stages are keyed on different party names"]
    on_spine = [p for p in shared if abs(before[p] - level[p]) <= 1e-12 * max(1.0, abs(level[p]))]
    if len(on_spine) < max(1, len(shared) // 6):
        return [f"only {len(on_spine)} of {len(shared)} centres sit on their spine "
                f"level. The spine has stopped reaching the level chain, and every "
                f"party would still get a number."]
    return []


def cross_no_party_with_a_centre_is_drawn_at_the_width_ceiling(payloads) -> list[str]:
    """A party carrying a forecast level is never at ``SD_CEILING``.

    A TRIPWIRE, and if it fires it is a finding rather than a flake. The ceiling
    binds on a lot of the prior — 21 of 44 parties at joburg 2021, 35 of 79 at
    2026 — and on inspection every one of them is a party with a theta record and
    NO national baseline, whose width is the fit extrapolated to ``log(1e-5)``.
    Those parties carry no centre and reach no forecast number, so the ceiling's
    absorption is real and inert.

    The moment a party with a level lands on the ceiling, that changes: its width
    would be set by a clamp rather than by the fit, and the sd sweep would be
    measuring a constant for it. Go and look; do not relax this.
    """
    theta, _, centres = payloads
    ceiling, sd = theta.get("sd_ceiling"), theta.get("sd") or {}
    if not _finite(ceiling):
        return []
    before = centres.get("before_shrink") or {}
    pinned = sorted(p for p, v in sd.items()
                    if _finite(v) and abs(v - ceiling) < 1e-12 and p in before)
    if pinned:
        return [f"a party with a forecast level is drawn at the width CEILING "
                f"{ceiling}: {pinned[:6]}. Its width is a clamp, not a measurement."]
    return []


CROSS_PREDICATES = {fn.__name__: fn for fn in (
    cross_the_two_stages_read_one_theta_record,
    cross_the_blend_weight_and_the_shrink_use_one_worth,
    cross_every_centre_has_a_level_behind_it,
    cross_the_spine_still_reaches_the_centres,
    cross_no_party_with_a_centre_is_drawn_at_the_width_ceiling,
)}

ALL_PREDICATES = {**THETA_PREDICATES, **SPINE_PREDICATES,
                  **CENTRES_PREDICATES, **CROSS_PREDICATES}


def faults_in(theta: dict, spine: dict, centres: dict) -> list[tuple[str, str]]:
    """Every predicate against one set of stage payloads. ``(predicate, fault)``."""
    found: list[tuple[str, str]] = []
    for name, fn in THETA_PREDICATES.items():
        found += [(name, text) for text in fn(theta)]
    for name, fn in SPINE_PREDICATES.items():
        found += [(name, text) for text in fn(spine)]
    for name, fn in CENTRES_PREDICATES.items():
        found += [(name, text) for text in fn(centres)]
    for name, fn in CROSS_PREDICATES.items():
        found += [(name, text) for text in fn((theta, spine, centres))]
    return found


# ==========================================================================
# the constructed healthy payloads
# ==========================================================================
#
# Built arithmetically so every invariant holds BY CONSTRUCTION rather than by
# having been copied out of a run that happened to be healthy. CLAUDE.md
# requirement (3): a test whose premise is a passing state of the tree expires in
# silence the day that state changes.

_FLOOR, _CEILING = 0.15, 1.20
_K = 1.0


def healthy_theta_prior() -> dict:
    """A theta-prior payload with one party on the floor and one off it."""
    # ZEROED is here because `30_centres` carries it: a party present at exactly
    # zero, which every centres predicate has to route around and which must
    # still have a record behind it.
    sd = {"BIG": _FLOOR, "MID": 0.31, "SMALL": 0.62, "ZEROED": 0.45}
    mode = {"BIG": 0.86, "MID": 0.97, "SMALL": 1.24, "ZEROED": 1.01}
    prior = {p: [mode[p] * math.exp(-Z90 * sd[p]), mode[p],
                 mode[p] * math.exp(Z90 * sd[p])] for p in sd}
    return {
        "prior": prior,
        "sd": dict(sd),
        # `worth` is keyed on parties with a RECORD, so it is a strict subset.
        "worth": {"BIG": 21.4, "MID": 3.2},
        "centre": {"n": 40, "weighted_geomean": 0.87, "effective_n": 28.5},
        "spread": {"at_0.1%": 0.48, "at_1%": 0.29, "at_10%": 0.17, "at_40%": _FLOOR},
        "sd_floor": _FLOOR,
        "sd_ceiling": _CEILING,
        "at_the_floor": ["BIG"],
    }


def healthy_spine() -> dict:
    """A spine payload with one row of each route, plus a full-local blend."""
    rows = {
        # party        national level, local level, own theta worth
        "BIG":        (0.4400, 0.4700, 21.4),
        "MID":        (0.0510, 0.0190, 3.2),
        "FULLLOCAL":  (0.0620, 0.1520, 0.0),    # both records, no theta evidence
        "NATONLY":    (0.0043, 0.0,    0.0),
        "LOCONLY":    (0.0,    0.0021, 0.0),
    }
    level, detail = {}, {}
    blend_n = gap_total = from_national = from_local = 0
    at_full_local = at_full_national = 0
    for party, (nat, loc, worth) in rows.items():
        if nat > 0 and loc > 0:
            w = 0.0 if (worth + _K) <= 0 else _K / (worth + _K)
            value = math.exp(w * math.log(loc) + (1 - w) * math.log(nat))
            route = "blend"
            if w >= 1.0:
                route, at_full_local = "blend at full local (no theta evidence)", at_full_local + 1
            elif w <= 0.0:
                route, at_full_national = "blend at full national (k=0)", at_full_national + 1
            gap = abs(math.log(loc) - math.log(nat))
            blend_n, gap_total = blend_n + 1, gap_total + gap
            from_national, from_local = from_national + w * gap, from_local + (1 - w) * gap
        elif nat > 0:
            w, value, route = 0.0, nat, "national only (first local election)"
        else:
            w, value, route = 1.0, loc, "local only (no national record)"
        level[party] = value
        detail[party] = {"w_local": w, "worth": worth, "route": route,
                         "national": nat, "local": loc}
    routes = {"blend": blend_n, "dropped": 1,
              "national_only": sum(1 for n, l, _ in rows.values() if n > 0 >= l),
              "local_only": sum(1 for n, l, _ in rows.values() if l > 0 >= n)}
    return {
        "k": _K,
        "n_theta": 40,
        "n_rho": 28,
        "theta_centre": 0.87,
        "rho_centre": 0.60,
        "level": level,
        "detail": detail,
        "absorption": {
            "routes": routes,
            "dropped_parties": ["VANISHED"],
            "local_only_unused": ["LOCONLY"],
            "blend": {"n": blend_n, "nonfinite": 0, "disagreement": gap_total,
                      "moved_from_national": from_national,
                      "moved_from_local": from_local,
                      "at_full_local": at_full_local,
                      "at_full_national": at_full_national,
                      "share_local": (from_national / gap_total) if gap_total else 0.0},
            "centre_fallback": {"theta": 2, "rho": 1},
            "theta_shrink": {"n": 2, "target": "size_centre", "offered": 1.8,
                             "absorbed": 0.9, "share": 0.5, "empty": False},
            "rho_shrink": {"n": 2, "target": "size_centre", "offered": 2.0,
                           "absorbed": 1.4, "share": 0.7, "empty": False},
        },
    }


def healthy_centres() -> dict:
    """A centres payload whose ``after`` is the SHIPPED shrink applied to ``before``.

    ``compress_levels`` is called rather than copied. A second implementation of
    the shrink's arithmetic here would be the duplication CLAUDE.md forbids, and
    it would agree with a broken original by construction.
    """
    before = {"BIG": 0.4400, "MID": 0.1500, "FULLLOCAL": 0.0684, "NATONLY": 0.0050,
              "LOCONLY": 0.0021, "ZEROED": 0.0}
    scenario = {"level_shrink": 0.35, "level_shrink_scale": 0.04}
    after = mc.compress_levels(dict(before), scenario)
    return {
        "before_shrink": before,
        "after_shrink": after,
        "ratio": {p: (after[p] / v if v else None) for p, v in before.items()},
        "level_shrink": scenario["level_shrink"],
        "level_shrink_scale": scenario["level_shrink_scale"],
        "route_notes": {"MID": "level from poll: 15.00%"},
    }


def healthy_payloads() -> tuple[dict, dict, dict]:
    return healthy_theta_prior(), healthy_spine(), healthy_centres()


# ==========================================================================
# the positive controls — one constructed violation per predicate
# ==========================================================================
#
# ⛔ EVERY PREDICATE NEEDS AN ENTRY HERE. This is the "it can see" half of
# CLAUDE.md's rule on tests that assert absence, and it is enforced rather than
# recommended: `test_every_predicate_has_a_constructed_violation` fails on a
# predicate with no corruption and on a corruption naming no predicate.
#
# Each entry is (predicate, what the corruption is, which payload, mutation).
# The mutation receives a deep copy and edits it in place.

#
# ⚠ EVERY MUTATION ADDRESSES THE PAYLOAD, NEVER A PARTY BY NAME. The first
# version of this table named the fixture's parties, and thirteen of its
# twenty-nine corruptions could not be applied to a real trace at all — they
# raised KeyError on a party that does not exist outside this file, and the
# replay `test_a_corrupted_real_trace_is_caught` reported them as unseen. A
# control that only works on the fixture proves the predicate can see the
# FIXTURE.

def _a_theta_party(stage) -> str:
    """A party carrying both a band and a width. Deterministic."""
    return sorted(set(stage["prior"]) & set(stage["sd"]))[0]


def _set_band(stage, party, sd) -> None:
    """Put ``party`` at width ``sd`` with the band that width implies."""
    mode = stage["prior"][party][1]
    stage["sd"][party] = sd
    stage["prior"][party] = [mode * math.exp(-Z90 * sd), mode,
                             mode * math.exp(Z90 * sd)]


def _a_blend_party(stage) -> str:
    """A party the spine blended — both routes positive. Deterministic."""
    return sorted(p for p, r in stage["detail"].items()
                  if r.get("local", 0) > 0 and r.get("national", 0) > 0)[0]


def _biggest_centre(stage) -> str:
    return max(stage["before_shrink"], key=lambda p: stage["before_shrink"][p])


def _reshrink(stage) -> None:
    """Re-apply the SHIPPED shrink to ``before_shrink`` and rewrite after/ratio.

    Used by the mutations that change the level vector itself, so that the only
    predicate left disagreeing is the one the row is about.
    """
    before = stage["before_shrink"]
    after = mc.compress_levels(dict(before), stage)
    stage["after_shrink"] = after
    stage["ratio"] = {p: (after[p] / v if v else None) for p, v in before.items()}


def _corrupt_theta_band(s):
    s["prior"][_a_theta_party(s)][2] *= 1.4     # widen the band, leave the sd alone


def _corrupt_theta_mode(s):
    s["prior"][_a_theta_party(s)][1] *= 1.05    # move the mode off its band's centre


def _corrupt_theta_keys(s):
    del s["sd"][_a_theta_party(s)]              # a band with no width takes the default


def _corrupt_theta_clamp(s):
    _set_band(s, _a_theta_party(s), s["sd_ceiling"] * 1.5)


def _corrupt_theta_floor_named(s):
    # Named at the floor and not at it. Always applicable: the name need not
    # exist in the payload at all, which is the point — the census must be a
    # census.
    s["at_the_floor"] = sorted(set(s["at_the_floor"]) | {"__NOT_AT_THE_FLOOR__"})


def _corrupt_theta_floor_unnamed(s):
    # At the floor and not named — the direction a one-way scan misses.
    party = _a_theta_party(s)
    _set_band(s, party, s["sd_floor"])
    s["at_the_floor"] = sorted(set(s["at_the_floor"]) - {party})


def _corrupt_theta_curve(s):
    s["spread"]["at_40%"] = s["spread"]["at_0.1%"] * 2      # dispersion RISES with size


def _corrupt_theta_record(s):
    s["centre"]["effective_n"] = s["centre"]["n"] * 2 + 1.0  # weight above 1 per row


def _corrupt_spine_keys(s):
    del s["detail"][sorted(s["detail"])[0]]     # a level with no account of itself


def _corrupt_spine_blend(s):
    s["level"][sorted(s["level"])[0]] *= 1.02   # a level that is not the blend it reports


def _corrupt_spine_bracket(s):
    party = _a_blend_party(s)
    row = s["detail"][party]
    s["level"][party] = max(row["national"], row["local"]) * 1.10


def _corrupt_spine_label(s):
    # A party with BOTH records labelled as having only one — the §1.97 F7 shape:
    # the label a reader checks, saying a route contributed when it did not.
    s["detail"][_a_blend_party(s)]["route"] = "national only (first local election)"


def _corrupt_spine_weight(s):
    party = _a_blend_party(s)
    row = s["detail"][party]
    w = 0.5 if abs(row["w_local"] - 0.5) > 1e-3 else 0.25
    row["w_local"] = w
    # The level is recomputed so the blend predicate still passes and the fault
    # is attributable to the weight alone.
    s["level"][party] = math.exp(w * math.log(row["local"])
                                 + (1 - w) * math.log(row["national"]))


def _corrupt_spine_census(s):
    s["absorption"]["routes"]["blend"] -= 1     # a counter that stopped counting


def _corrupt_spine_account(s):
    # The disagreement no longer splits into the two routes' shares, and
    # `share_local` no longer describes it either.
    s["absorption"]["blend"]["disagreement"] = (
        (s["absorption"]["blend"].get("disagreement") or 0.0) + 2.0)


def _corrupt_spine_shrink(s):
    block = s["absorption"]["theta_shrink"]
    block["absorbed"] = (block.get("offered") or 0.0) * 2 + 1.0   # ate more than offered


def _corrupt_spine_positive(s):
    s["level"][sorted(s["level"])[0]] = 0.0     # a party the blend lost, reading as a level


def _corrupt_centres_keys(s):
    s["after_shrink"]["__EXTRA__"] = 0.01       # one extra key rescales every party


def _corrupt_centres_total(s):
    party = _biggest_centre(s)
    s["after_shrink"][party] *= 1.02            # mass created by the shrink
    s["ratio"][party] = s["after_shrink"][party] / s["before_shrink"][party]


def _corrupt_centres_ballot(s):
    # The level vector has lost nine tenths of itself. Re-shrunk so the total is
    # the only thing wrong with it.
    s["before_shrink"] = {p: v * 0.1 for p, v in s["before_shrink"].items()}
    _reshrink(s)


def _corrupt_centres_ratio(s):
    party = _biggest_centre(s)
    s["ratio"][party] = (s["ratio"][party] or 1.0) * 1.1   # describes neither vector


def _corrupt_centres_monotone(s):
    # Swap the two vectors: the shrink now reads as having been applied backwards,
    # which is the recurring before/after confusion in its purest form.
    s["before_shrink"], s["after_shrink"] = s["after_shrink"], s["before_shrink"]
    s["ratio"] = {p: (s["after_shrink"][p] / v if v else None)
                  for p, v in s["before_shrink"].items()}


def _corrupt_centres_direction(s):
    # The shrink run with its sign reversed: the top of the ballot is LIFTED and
    # the bottom pulled down, with the total still conserved.
    before = s["before_shrink"]
    c, h = s["level_shrink"] or 0.0, s["level_shrink_scale"] or 0.0
    total = sum(v for v in before.values() if v > 0)
    kept = {p: (v * (1.0 + c * v / (v + h)) if v > 0 else v) for p, v in before.items()}
    freed = sum(v for v in kept.values() if v > 0)
    s["after_shrink"] = {p: (v * total / freed if v > 0 else v) for p, v in kept.items()}
    s["ratio"] = {p: (s["after_shrink"][p] / v if v else None) for p, v in before.items()}


def _corrupt_centres_off_switch(s):
    s["level_shrink"] = 0.0                     # off, and the vector moved anyway


def _corrupt_centres_levers(s):
    s["level_shrink_scale"] = (s["level_shrink_scale"] or 0.04) * 2.5


def _corrupt_cross_record(s):
    s[1]["theta_centre"] *= 1.03                # two answers for one quantity


def _corrupt_cross_worth(s):
    party = sorted(set(s[0]["worth"]) & set(s[1]["detail"]))[0]
    s[1]["detail"][party]["worth"] += 1.0       # the weight and the shrink diverge


def _corrupt_cross_orphan(s):
    s[2]["before_shrink"]["__GHOST__"] = 0.02   # a centre with no record behind it
    _reshrink(s[2])


def _corrupt_cross_seam(s):
    # Every centre nudged off its spine level: the spine has stopped reaching the
    # level chain and every party still gets a number.
    s[2]["before_shrink"] = {p: v * 1.07 for p, v in s[2]["before_shrink"].items()}
    _reshrink(s[2])


def _corrupt_cross_ceiling(s):
    party = sorted(set(s[0]["sd"]) & set(s[2]["before_shrink"]))[0]
    _set_band(s[0], party, s[0]["sd_ceiling"])  # a party with a level, at the clamp
    s[0]["at_the_floor"] = sorted(set(s[0]["at_the_floor"]) - {party})


CORRUPTIONS = [
    ("theta_the_band_is_the_measured_width", "widen a band without moving its sd",
     "theta", _corrupt_theta_band),
    ("theta_the_mode_is_the_geometric_centre_of_its_band", "move a mode off its band",
     "theta", _corrupt_theta_mode),
    ("theta_every_band_carries_a_width_and_every_record_a_band", "a band with no width",
     "theta", _corrupt_theta_keys),
    ("theta_the_widths_lie_inside_the_declared_clamp", "a width above the ceiling",
     "theta", _corrupt_theta_clamp),
    ("theta_the_floor_census_is_exact_in_both_directions", "a name in the census that is not at the floor",
     "theta", _corrupt_theta_floor_named),
    ("theta_the_floor_census_is_exact_in_both_directions", "a party at the floor that the census does not name",
     "theta", _corrupt_theta_floor_unnamed),
    ("theta_the_dispersion_curve_falls_with_size", "the dispersion fit inverted",
     "theta", _corrupt_theta_curve),
    ("theta_the_record_is_counted_consistently", "effective_n above n",
     "theta", _corrupt_theta_record),
    ("spine_every_level_has_a_detail_row", "a level with no detail row",
     "spine", _corrupt_spine_keys),
    ("spine_the_level_is_the_geometric_blend_of_its_two_routes", "a level off its own blend",
     "spine", _corrupt_spine_blend),
    ("spine_a_blended_level_is_bracketed_by_its_routes", "a level outside both routes",
     "spine", _corrupt_spine_bracket),
    ("spine_the_route_label_describes_the_arithmetic", "a full-local row labelled blend",
     "spine", _corrupt_spine_label),
    ("spine_the_blend_weight_is_keyed_on_what_the_record_is_worth", "a weight not from worth",
     "spine", _corrupt_spine_weight),
    ("spine_the_route_census_matches_the_rows", "a route counter off by one",
     "spine", _corrupt_spine_census),
    ("spine_the_disagreement_account_adds_up", "the disagreement no longer splits",
     "spine", _corrupt_spine_account),
    ("spine_the_shrink_accounts_are_bounded", "absorbed above offered",
     "spine", _corrupt_spine_shrink),
    ("spine_the_levels_and_the_group_centres_are_positive", "a level at zero",
     "spine", _corrupt_spine_positive),
    ("centres_the_three_vectors_cover_the_same_parties", "an extra key in after_shrink",
     "centres", _corrupt_centres_keys),
    ("centres_the_shrink_conserves_the_total", "mass created by the shrink",
     "centres", _corrupt_centres_total),
    ("centres_the_total_is_a_plausible_ballot", "the level vector lost its parties",
     "centres", _corrupt_centres_ballot),
    ("centres_the_recorded_ratio_is_after_over_before", "a ratio that describes nothing",
     "centres", _corrupt_centres_ratio),
    ("centres_the_pull_is_monotone_in_size", "before and after recorded the wrong way round",
     "centres", _corrupt_centres_monotone),
    ("centres_the_shrink_takes_from_the_top_and_gives_to_the_bottom", "the shrink's sign reversed",
     "centres", _corrupt_centres_direction),
    ("centres_the_off_switch_is_the_identity", "off, and the vector moved",
     "centres", _corrupt_centres_off_switch),
    ("centres_the_recorded_levers_reproduce_the_shrink", "the recorded lever is not the applied one",
     "centres", _corrupt_centres_levers),
    ("cross_the_two_stages_read_one_theta_record", "two answers for one theta centre",
     "all", _corrupt_cross_record),
    ("cross_the_blend_weight_and_the_shrink_use_one_worth", "the two worths diverge",
     "all", _corrupt_cross_worth),
    ("cross_every_centre_has_a_level_behind_it", "a centre with no record behind it",
     "all", _corrupt_cross_orphan),
    ("cross_the_spine_still_reaches_the_centres", "the spine stopped reaching the centres",
     "all", _corrupt_cross_seam),
    ("cross_no_party_with_a_centre_is_drawn_at_the_width_ceiling", "a forecast party at the clamp",
     "all", _corrupt_cross_ceiling),
]


# ==========================================================================
# helpers
# ==========================================================================

def _finite(x) -> bool:
    return (isinstance(x, (int, float)) and not isinstance(x, bool)
            and math.isfinite(x))


def _rel(a, b) -> float:
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


@contextmanager
def _files_opened():
    """Record every path opened inside the block — ANY file, not only elections.

    ``_support.election_files_read`` answers a different question (did a fit read
    an election at or after its target) and its regex ignores everything else, so
    it cannot prove a fixture opened NOTHING. This is the smaller instrument for
    the smaller claim, and it exists because CLAUDE.md requirement (3) — the
    input is constructed, not observed — is otherwise an assertion about the
    author's intentions rather than about the code.
    """
    seen: list[str] = []
    real_open, real_path_open = builtins.open, Path.open

    def spy_open(file, *args, **kwargs):
        seen.append(str(file))
        return real_open(file, *args, **kwargs)

    def spy_path_open(self, *args, **kwargs):
        seen.append(str(self))
        return real_path_open(self, *args, **kwargs)

    builtins.open, Path.open = spy_open, spy_path_open
    try:
        yield seen
    finally:
        builtins.open, Path.open = real_open, real_path_open


_TRACES: dict[str, Path] = {}
_TRACE_ROOT: Path | None = None


def _trace_dir(year: str) -> Path:
    """A real trace for ``year``, run once per process and cleaned up at exit.

    The run is at 40 draws with ``--run-dir``, which changes no number
    (``test_chain.py::test_passing_a_run_directory_changes_no_drawn_number``) and
    publishes nothing: ``main`` refuses to rewrite ``data/processed`` when a run
    directory is given, and this calls ``run_model`` rather than ``main`` anyway.
    ``STAGE_TRACE_DIR`` in the environment points the integration tests at a
    trace that already exists instead, for a human chasing one by hand.
    """
    global _TRACE_ROOT
    import os
    override = os.environ.get("STAGE_TRACE_DIR")
    if override:
        path = Path(override) / year
        if not (path / "30_centres.json").exists():
            path = Path(override)
        if not (path / "30_centres.json").exists():
            skip(f"STAGE_TRACE_DIR={override} holds no trace for {year}")
        return path
    if year in _TRACES:
        return _TRACES[year]
    if _TRACE_ROOT is None:
        _TRACE_ROOT = Path(tempfile.mkdtemp(prefix="stage-estimation-"))
        atexit.register(shutil.rmtree, _TRACE_ROOT, True)
    run_dir = _TRACE_ROOT / year
    try:
        city = cityconfig.use(CITY)
        target = cityconfig.use_target(year)
        mc.apply_city(city)
        scenario = mc.load_scenario(argparse.Namespace(
            config=None, set=[], draws=DRAWS, seed=SEED, city=CITY, target=year))
        mc.run_model(target, scenario, ROOT / "data/raw/elections",
                     verbose=False, run_dir=run_dir)
    except (FileNotFoundError, SystemExit) as exc:
        skip(f"no {CITY} {year} run is possible here, so no trace to observe: "
             f"{type(exc).__name__}: {exc}")
    _TRACES[year] = run_dir
    return run_dir


def _stages(year: str) -> tuple[dict, dict, dict]:
    run_dir = _trace_dir(year)
    out = []
    for name in ("10_theta_prior", "20_spine", "30_centres"):
        path = run_dir / f"{name}.json"
        if not path.exists():
            skip(f"the {year} run wrote no {name}.json; the stage has been "
                 f"renamed or the emission removed, and this observer must be "
                 f"rewritten against the new name rather than dropped")
        out.append(json.loads(path.read_text()))
    return tuple(out)                                        # type: ignore[return-value]


def _apply(corruption, payloads):
    """Deep-copy the payloads and apply one corruption. Returns the new triple."""
    _name, _what, which, mutate = corruption
    theta, spine, centres = (copy.deepcopy(p) for p in payloads)
    if which == "theta":
        mutate(theta)
    elif which == "spine":
        mutate(spine)
    elif which == "centres":
        mutate(centres)
    else:
        mutate((theta, spine, centres))
    return theta, spine, centres


# ==========================================================================
# the tests
# ==========================================================================

def test_a_constructed_healthy_payload_passes_every_predicate():
    """The floor of the whole file: a clean trace must read as clean.

    If this fails, every "no faults" result below is meaningless, because the
    predicates are rejecting a payload built to satisfy them.
    """
    found = faults_in(*healthy_payloads())
    assert not found, (
        "the constructed healthy payloads are rejected by this file's own "
        "predicates:\n  " + "\n  ".join(f"{n}: {t}" for n, t in found))


def test_every_predicate_has_a_constructed_violation():
    """⛔ The "it can see" control, enforced rather than recommended.

    ``arrival_reconciliation`` was blind at 20 of 24 rows while reporting nothing
    amiss. A predicate with no constructed violation is in that position by
    default: it returns an empty list and nobody can tell whether that is because
    the payload is healthy or because it never looks.

    Both directions: a predicate with no corruption, and a corruption naming a
    predicate that does not exist (a rename that silently disarmed the control).
    """
    covered = {name for name, *_ in CORRUPTIONS}
    registered = set(ALL_PREDICATES)
    assert not registered - covered, (
        f"predicate(s) with no constructed violation: {sorted(registered - covered)}\n"
        f"Add one to CORRUPTIONS. A check that has never been shown to fire is "
        f"not a check.")
    assert not covered - registered, (
        f"CORRUPTIONS names predicate(s) that do not exist: "
        f"{sorted(covered - registered)}. A rename has disarmed the control.")

    # (1) IT LOOKED. The predicate count is bounded on both sides against the
    # number of fields the three stages actually emit, taken from the constructed
    # payloads — which `test_the_constructed_payloads_carry_a_real_trace_s_fields`
    # pins to a real run. BELOW the band a stage has grown fields nothing checks;
    # ABOVE it, the registry has filled with variations on one claim.
    fields = sum(len(p) for p in healthy_payloads())
    scanned(registered, of=fields, low=0.6, high=2.5,
            what="registered stage predicates",
            denominator="top-level fields across the three stage payloads")


def test_each_constructed_violation_is_caught_by_the_predicate_that_owns_it():
    """Every corruption fires its own predicate, and something always fires.

    The honest name for this is mutation testing: change one thing and watch the
    suite go red. CLAUDE.md's four-part rule is the cheap approximation of it,
    and this is the part of the rule that actually holds a check up.

    Two assertions per row, deliberately. The NAMED predicate must fire — a
    corruption caught only by a neighbour proves the neighbour can see and leaves
    the owner unproven — and at least one must fire, which catches the case where
    the corruption itself is inert.
    """
    healthy = healthy_payloads()
    for corruption in CORRUPTIONS:
        name, what, _which, _mutate = corruption
        found = faults_in(*_apply(corruption, healthy))
        fired = {n for n, _ in found}
        assert found, (
            f"the corruption {what!r} ({name}) produced NO fault at all. Either "
            f"the mutation does not change anything the predicates read, or the "
            f"predicate is blind.")
        assert name in fired, (
            f"the corruption {what!r} was not caught by {name}, which owns it. "
            f"Caught instead by: {sorted(fired)}. A check proven only through a "
            f"neighbour is not proven.")


def test_the_constructed_payloads_open_no_file():
    """The fixtures are CONSTRUCTED, not read off a passing tree.

    CLAUDE.md requirement (3). A test whose premise is the current state of
    ``data/`` expires the day that state changes and does so in silence — one
    here asserted the build refuses an unattributable run and broke the day that
    defect was fixed.

    ``compress_levels`` is called while building the centres fixture and opens
    nothing; if it ever starts reading a file, that is worth knowing too.
    """
    with _files_opened() as seen:
        payloads = healthy_payloads()
    assert all(p for p in payloads), "the fixture builders returned nothing"
    assert not seen, (
        f"building the 'constructed' payloads opened {len(seen)} file(s): "
        f"{seen[:5]}. They are observed, not constructed, and they will expire "
        f"silently when what they observed changes.")


def test_the_predicates_hold_on_a_real_trace():
    """The whole registry against a real run, at two cycles.

    The predicates are pure and are proven against constructed payloads above;
    this is what connects them to the model. It runs the forecast at 40 draws
    with a run directory — which changes no drawn number and publishes nothing —
    and reads the three stages back off disk exactly as a human would.
    """
    for year in TRACE_YEARS:
        theta, spine, centres = _stages(year)
        found = faults_in(theta, spine, centres)
        assert not found, (
            f"the estimation segment of the {CITY} {year} run is not "
            f"self-consistent:\n  "
            + "\n  ".join(f"{n}: {t}" for n, t in found[:12]))


def test_the_real_trace_is_substantial_enough_to_have_been_examined():
    """(1) IT LOOKED — on the REAL payloads, not only on the fixtures.

    A trace whose stages are empty dicts passes every predicate above in perfect
    silence: no band to check, no row to blend, no total to conserve. So the
    populations are bounded on both sides against a denominator that moves with
    the model — the number of parties carrying a central level.

    The archive supports the band: joburg 2011 carried 11 centres against 22
    priors and 20 spine levels; joburg 2021, 55 against 44 and 65.
    """
    for year in TRACE_YEARS:
        theta, spine, centres = _stages(year)
        parties = centres.get("before_shrink") or {}
        assert parties, f"{year}: the centres stage carries no party at all"
        scanned(theta.get("prior") or {}, of=parties, low=0.5, high=8.0,
                what=f"{year}: parties carrying a theta band",
                denominator="parties carrying a central level")
        scanned(spine.get("level") or {}, of=parties, low=0.5, high=8.0,
                what=f"{year}: parties carrying a spine level",
                denominator="parties carrying a central level")
        scanned(theta.get("worth") or {}, of=parties, low=0.1, high=8.0,
                what=f"{year}: parties with a theta record of their own",
                denominator="parties carrying a central level")


def test_a_corrupted_real_trace_is_caught():
    """The "it can see" control for the INTEGRATION path, not only the fixtures.

    The predicates could pass on a real trace because the trace is healthy or
    because the real payload has a shape they silently skip over — a key named
    differently, a list where a dict was expected. Pushing a constructed
    violation through the REAL payload settles which.

    Every corruption is replayed, because the real payload is where a silent skip
    would hide, and a single sample would only prove one predicate reaches it.
    """
    real = _stages(TRACE_YEARS[-1])
    unseen = []
    for corruption in CORRUPTIONS:
        name, what, _which, _mutate = corruption
        try:
            found = faults_in(*_apply(corruption, real))
        except (KeyError, IndexError, TypeError) as exc:
            # A corruption addressing a fixture-only party cannot be applied to a
            # real payload; that is a fact about the corruption, not a failure of
            # the predicate, and it is reported rather than skipped.
            unseen.append(f"{name}: {what} could not be applied ({exc!r})")
            continue
        if name not in {n for n, _ in found}:
            unseen.append(f"{name}: {what} passed unnoticed on the real trace")
    assert not unseen, (
        "constructed violations that the predicates did NOT see on a real "
        "payload — they are passing on shape, not on content:\n  "
        + "\n  ".join(unseen))


def test_the_constructed_payloads_carry_a_real_trace_s_fields():
    """The fixtures have the same top-level fields as the run emits.

    This is what stops the constructed payloads drifting away from the thing they
    stand in for. It is also the link that makes the predicate-count band in
    ``test_every_predicate_has_a_constructed_violation`` mean something: a stage
    that grows a field fails HERE first, the fixture is updated, the denominator
    moves, and the band then asks whether the new field has a check.
    """
    for year in TRACE_YEARS:
        for stage_name, real, built in zip(
                ("10_theta_prior", "20_spine", "30_centres"),
                _stages(year), healthy_payloads()):
            missing = sorted(set(real) - set(built))
            extra = sorted(set(built) - set(real))
            assert not missing and not extra, (
                f"{year} {stage_name}: the constructed payload no longer matches "
                f"the emitted one. Emitted and not constructed: {missing}; "
                f"constructed and not emitted: {extra}.\n"
                f"Update the fixture AND add a predicate for any new field — a "
                f"field nothing reads is a field nothing guards.")


def test_the_level_shrink_is_cycle_blind_by_construction():
    """The shrink takes mass off the top of the ballot at EVERY cycle, by the same rule.

    ⛔ THIS IS A LIVE MODELLING DEFECT MADE VISIBLE, NOT A PASSING GRADE.
    ``level_shrink`` = 0.35 is applied identically whatever the cycle, and the
    measured signed vote-share error for ranks 1-3, summed over eight metros,
    runs **−40.81pp at 2011, −7.45 at 2016, +24.76 at 2021**. So at 2011 a
    non-negative shrink pushes an already 40-point-under-forecast top of the
    ballot further down. Fix #16.

    Measured here on the traces: the shrink moves −1.47pp off ranks 1-3 at joburg
    2011 and −3.00pp at joburg 2021 — same sign, different size, and the size
    tracks how fragmented the ballot is rather than anything about the cycle.

    The assertion is the cycle-blindness itself. If somebody makes the shrink
    conditional on the cycle, this fails, and CLAUDE.md §2 then requires the
    documentation to move in the same commit.
    """
    moved = {}
    for year in TRACE_YEARS:
        _theta, _spine, centres = _stages(year)
        before, after = centres["before_shrink"], centres["after_shrink"]
        if not (centres.get("level_shrink") or 0) > 0:
            skip(f"level_shrink is off at {year}; there is no direction to check")
        top = sorted(before, key=lambda p: -before[p])[:3]
        moved[year] = sum(after[p] - before[p] for p in top) * 100
    for year, pp in moved.items():
        assert pp < 0, (
            f"{year}: the shrink ADDED {pp:+.2f}pp to ranks 1-3. The mechanism's "
            f"direction is no longer the same at every cycle — which may be the "
            f"fix for #16, in which case update MACHINERY.md and this docstring "
            f"in the same commit.")
    assert len({pp < 0 for pp in moved.values()}) == 1, (
        f"the shrink now moves the top of the ballot in different directions at "
        f"different cycles: {moved}")


def test_the_spine_reads_no_election_at_or_after_its_target():
    """Both of the spine's records stop strictly before the target — watched at the file.

    ``test_chain.py`` spies on ``theta_record`` alone. ``spine`` reads a SECOND
    archive, ``local_record``, and nothing watched it: a rho measured across the
    election being forecast would place every party on its own answer and the
    resulting backtest would look excellent.

    The guard is the open-spy rather than a restatement of the loop's own
    condition, because a restatement is true of the calendar whatever the code
    reads and passes with the guard deleted — which is how
    ``test_the_level_prior_reads_no_election_at_or_after_its_target`` came to
    assert nothing at all about the level prior.

    ``baseline`` and ``prev_local`` are empty: both records are read before either
    is consulted, so the file reads are exercised in full while the party loop
    does nothing. ``n_theta`` and ``n_rho`` are the positive control — "no late
    file" is evidence only if something was read at all.
    """
    # Named rather than inherited: `cityconfig.use` is process-global and the
    # suite reuses workers, so `active()` here would be whatever the previous
    # module left behind. `_support.run_module` puts it back after every test.
    # (`theta_record` and `local_record` read `target.year` and the metro codes
    # and never `target.city`, so the answer is city-independent — but a test
    # that depends on that being true without saying so is one rename away from
    # being about a different city.)
    city = cityconfig.use(CITY)
    for year in TRACE_YEARS:
        target = cityconfig.Target(city=city, year=year)
        with election_files_read() as reads:
            _level, info = levels.spine(target, {}, {})
        assert info, f"levels.spine returned no diagnostic block at {year}"
        assert info.get("n_theta", 0) > 0 and info.get("n_rho", 0) > 0, (
            f"the spine at {year} read {info.get('n_theta')} theta and "
            f"{info.get('n_rho')} rho observations. With an empty record the "
            f"'no late file' result below is vacuous.")
        assert reads, (
            f"the spine at {year} opened no election file at all; the spy is "
            f"watching the wrong thing")
        late = sorted({(y, kind) for y, kind, _ in reads if int(y) >= int(year)})
        assert not late, (
            f"the spine for target {year} read {late} — a retention ratio "
            f"measured across the election being forecast")


if __name__ == "__main__":
    # `run_module`, not a hand-rolled loop: it catches SkipTest and SystemExit,
    # and it restores the active city after every test. See _support.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
