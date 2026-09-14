"""A stage observer for the REALISATION segment: draws -> shares -> seats.

``run_model`` emits thirteen stages under ``--run-dir``. The last six are this
file's subject::

    40_draws  41_guards  42_pr_share_draws  43_ward_share_draws
    44_seat_draws  45_delivered

They are where a distribution becomes a council. Seats are a step function of
votes through a quota, so a vote error is amplified at the quota and rounded
away below it — which means almost everything that must be true here is
conservation or arithmetic identity, and is therefore checkable exactly rather
than approximately. That is the reason this segment gets an observer first.

WHAT THIS FILE IS. Every check is a **pure predicate over one stage payload**,
returning a list of complaints. Each predicate is exercised three ways:

1. against a **constructed healthy payload**, which must produce no complaint;
2. against a **constructed corrupted payload**, which must produce the right
   complaint — the positive control, without which the predicate is an
   `arrival_reconciliation`: an observer blind at 20 of 24 rows that reported
   nothing wrong, and was worse than no observer at all;
3. against a **real trace**, generated here at 40 draws, which is what proves
   the constructed payloads have the shape the model actually emits.

WHY THE PREDICATES TAKE PAYLOADS AND NOT A RUN. A test that can only run when
the archive is on disk is a test that stops running, and a fixture built from a
passing tree expires the day the tree changes. The predicates need no data at
all; only the integration test does, and it skips loudly rather than quietly
weakening what it asserts.

THE THREE FACTS A READER OF THIS SEGMENT NEEDS, none of them obvious:

* **42 and 43 are UNLABELLED.** They are bare ``(draws, parties)`` arrays with
  no party names anywhere in the file. They are readable only because
  ``universe`` is built with ``sorted(...)`` and ``Trace.put`` dumps with
  ``sort_keys=True``, so column *i* is ``sorted(40_draws["pr_mean"])[i]``. Two
  independent implementation details, coupled, with nothing asserting it.
  :func:`faults_between_summary_and_detail` is that assertion.
* **"Sums to the council" is the WRONG invariant in general.** Schedule 1 takes
  independent ward winners (``C``) and the ward winners of parties with no PR
  list (``D``) out of the pool before the quota is struck, so a draw may
  legitimately fill ``council - C - D``. The observable invariant is that the
  fill is *accounted for*, not that it is 270.
* **A per-party median over draws is not a council.** Measured here, joburg
  2021, 400 draws: the marginal medians sum to 254 and the means sum to exactly
  270. Storing one under the other's name is a defect this project has had
  twice; :func:`faults_between_summary_and_detail` is what catches it.

Run:
    ./.venv/bin/python tests/test_stage_realisation.py
    ./.venv/bin/python -m pytest tests/test_stage_realisation.py -q

See ``skills/forecast-stage-realisation/SKILL.md`` for the field inventory, the
units, and the list of things this file could NOT check.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import statistics
import sys
import tempfile
from argparse import Namespace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned, skip  # noqa: E402

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402
from seats import allocate, eligible_parties  # noqa: E402


# --------------------------------------------------------------------------
# the contracts
# --------------------------------------------------------------------------

# EVERY KEY `41_guards` CARRIES, written out rather than read from the payload.
#
# This is the point of the list. A guard counter that nothing reads is a guard
# nobody is checking, and until this week these had no route out of `run_model`
# at all. Checking the payload against itself would pass on an empty payload;
# checking it against a literal fails in BOTH directions — a counter deleted
# from `run_model` and a counter added to it without being declared here. The
# second direction is the one with the worse record in this repository (the
# register guard checked code->register and never register->code, and a deleted
# lever sat in the register for days).
#
# `ipf_worst` is DELIBERATELY ABSENT and that is a finding, not an omission:
# `ModelRun` carries `ipf_worst` as a typed field but `41_guards` does not
# carry the key, so the "whole board" the `ModelRun.guards` docstring promises
# is one counter short of whole. See the SKILL.
GUARD_KEYS = frozenset({
    "bounds_checked", "bounds_violations",
    "cap_moved", "cap_undershoots",
    "excessive_draws", "overhang_count",
    "ipf_balances", "ipf_failures", "ipf_clipped", "ipf_headroom",
    "solve_calls", "solve_rounds",
    "solve_nonconvergent", "solve_nonconvergent_reachable",
    "solve_worst_gap", "solve_worst_gap_reachable",
    "solve_unreachable_parties",
    "solve_floor_injected_mean", "solve_floor_injected_worst",
    "solve_identity_hits",
})

# Counters that are COUNTS OF DRAWS, and the denominator each is a fraction of.
# A rate quoted without its denominator is the defect this table exists against.
GUARD_DENOMINATORS = {
    "bounds_violations": "bounds_checked",
    "ipf_clipped": "ipf_balances",
    "overhang_count": "bounds_checked",
}

# The three denominators. If any is zero the whole board is unreadable: every
# rate computed from it is 0/0, and a payload of zeros is indistinguishable
# from a run in which nothing was counted. THIS IS THE POSITIVE CONTROL ON THE
# OBSERVER ITSELF.
GUARD_DENOMINATOR_KEYS = ("bounds_checked", "ipf_balances", "solve_calls")

# `note_value`'s vocabulary. `consulted` is the only one that proves a value
# reached a computation; `resolved` proves only that the process held it, and
# §1.68 was burned by reporting a `resolved` record as evidence a lever was
# inert. A log carrying no `consulted` record at all has proved nothing.
DELIVERY_KINDS = frozenset(
    {"consulted", "resolved", "resolved-frozen", "not-imported", "missing"})

DELIVERY_RECORD_KEYS = frozenset(
    {"values", "where", "kinds", "who", "reads", "dropped"})

# The overhang rules under which the chamber may grow past `council`. Under
# `deduct` (the shipped rule) and `cap` it may not; the quota is recomputed
# over the seats that are left and the council stays where the statute put it.
EXPANDING_RULES = frozenset({"expand", "level"})


# --------------------------------------------------------------------------
# the predicates — pure, and they need no data
# --------------------------------------------------------------------------

def faults_in_share_matrix(matrix, *, name="shares", draws=None, parties=None,
                           tol=1e-9) -> list[str]:
    """Complaints about a ``42``/``43`` payload: a (draws, parties) share array.

    Units: each row is one draw's CITYWIDE share of one ballot, normalised in
    ``run_model`` by ``votes / max(votes.sum(), 1e-12)``. So every row sums to
    one to floating point, and every entry is in [0, 1].

    A row summing to zero is the signature this is written to catch: the arrays
    are pre-allocated with ``np.zeros((draws, npar))`` and filled inside the
    draw loop, so a loop that ended early leaves ALL-ZERO ROWS and a summary
    computed over them is diluted towards zero rather than absent. There is no
    other way to see that from outside the run.
    """
    out: list[str] = []
    arr = np.asarray(matrix, dtype=float)
    if arr.ndim != 2:
        return [f"{name}: expected a 2-D (draws, parties) array, got shape "
                f"{arr.shape}"]
    if arr.size == 0:
        return [f"{name}: the array is empty, so nothing was drawn or nothing "
                f"was recorded; those are different and this cannot tell them "
                f"apart"]
    if draws is not None and arr.shape[0] != draws:
        out.append(f"{name}: {arr.shape[0]} rows against {draws} draws — the "
                   f"array is not one row per draw")
    if parties is not None and arr.shape[1] != parties:
        out.append(f"{name}: {arr.shape[1]} columns against {parties} parties "
                   f"in the universe")
    if not np.isfinite(arr).all():
        out.append(f"{name}: {int((~np.isfinite(arr)).sum())} non-finite "
                   f"entries")
        return out
    if arr.min() < -tol:
        out.append(f"{name}: a negative share ({arr.min():.3g}); a share is a "
                   f"fraction of a ballot and cannot be below zero")
    if arr.max() > 1.0 + tol:
        out.append(f"{name}: a share above one ({arr.max():.6g})")
    sums = arr.sum(axis=1)
    bad = np.flatnonzero(np.abs(sums - 1.0) > tol)
    if bad.size:
        zero = np.flatnonzero(sums <= tol)
        out.append(
            f"{name}: {bad.size} of {arr.shape[0]} rows do not sum to one "
            f"(worst {sums[bad][np.argmax(np.abs(sums[bad] - 1.0))]:.6g} at "
            f"draw {int(bad[np.argmax(np.abs(sums[bad] - 1.0))])})"
            + (f"; {zero.size} of them are ALL ZERO, which is an unfilled "
               f"row and means the draw loop did not reach them"
               if zero.size else ""))
    return out


def faults_in_draws_summary(payload, *, draws=None, universe=None) -> list[str]:
    """Complaints about a ``40_draws`` payload, judged on its own.

    Fields, all dicts keyed by party:

    ``pr_mean`` ``pr_p5`` ``pr_p95``  citywide PR-ballot share, mean and the
        5th/95th marginal percentiles over draws. Units: fraction of the
        ballot, so the two means sum to one and the percentiles do not.
    ``ward_mean``  the same for the ward ballot.
    ``ward_win_sum``  ward wins SUMMED OVER ALL DRAWS. Units: ward-draws, so it
        sums to ``draws x wards`` and not to ``wards``. Every draw seats every
        ward (``argmax`` always returns something), so this total is conserved
        by construction — a violation means a ward was skipped or counted
        twice, which is the only way it can move.
    ``seat_mean``  mean council seats per party over draws. Units: seats.

    NOT ASSERTED, deliberately: that the mean lies inside [p5, p95]. Measured
    at joburg 2021: AGANG's mean sits above its own 95th percentile, because
    the entrant distribution is right-skewed enough that the top 5% carries the
    mean. That is a property of the distribution, not a defect, and a test
    asserting otherwise would be a test of skewness dressed up as an invariant.
    """
    out: list[str] = []
    required = {"pr_mean", "pr_p5", "pr_p95", "ward_mean", "ward_win_sum",
                "seat_mean"}
    missing = sorted(required - set(payload))
    if missing:
        return [f"40_draws is missing {missing}"]
    extra = sorted(set(payload) - required)
    if extra:
        out.append(f"40_draws carries undeclared field(s) {extra}; a new "
                   f"quantity in this stage must be declared to its observer "
                   f"or nothing is checking it")

    share_fields = ("pr_mean", "pr_p5", "pr_p95", "ward_mean")
    key_sets = {f: set(payload[f]) for f in share_fields}
    base = key_sets["pr_mean"]
    if not base:
        return out + ["40_draws.pr_mean is empty: no party was drawn"]
    for field, keys in key_sets.items():
        if keys != base:
            out.append(
                f"40_draws.{field} covers a different party set from pr_mean "
                f"(only in {field}: {sorted(keys - base)[:4]}; only in "
                f"pr_mean: {sorted(base - keys)[:4]}). All four are taken from "
                f"one `universe` in one comprehension, so they cannot differ "
                f"unless the party set moved between them")
    if universe is not None and base - set(universe):
        out.append(f"40_draws names parties outside the universe: "
                   f"{sorted(base - set(universe))[:6]}")

    for field in ("pr_mean", "ward_mean"):
        total = sum(payload[field].values())
        if abs(total - 1.0) > 1e-9:
            out.append(f"40_draws.{field} sums to {total:.9g}, not one; it is "
                       f"a mean over rows that each sum to one, so it must")
    for party in sorted(base):
        lo, hi = payload["pr_p5"][party], payload["pr_p95"][party]
        if not (math.isfinite(lo) and math.isfinite(hi)):
            out.append(f"40_draws: {party}'s band is not finite ({lo}, {hi})")
        elif lo > hi:
            out.append(f"40_draws: {party}'s 5th percentile {lo:.6g} exceeds "
                       f"its 95th {hi:.6g}; the two are swapped")
        elif lo < 0 or hi > 1:
            out.append(f"40_draws: {party}'s band [{lo:.6g}, {hi:.6g}] leaves "
                       f"[0, 1], which no share can")

    if set(payload["seat_mean"]) - base:
        out.append(f"40_draws.seat_mean names parties absent from pr_mean: "
                   f"{sorted(set(payload['seat_mean']) - base)[:6]}; a party "
                   f"cannot be seated without being drawn")
    if set(payload["ward_win_sum"]) - base:
        out.append(f"40_draws.ward_win_sum names parties absent from pr_mean: "
                   f"{sorted(set(payload['ward_win_sum']) - base)[:6]}")
    if any(v < 0 for v in payload["ward_win_sum"].values()):
        out.append("40_draws.ward_win_sum holds a negative count")
    if any(v < 0 for v in payload["seat_mean"].values()):
        out.append("40_draws.seat_mean holds a negative seat count")

    wins = sum(payload["ward_win_sum"].values())
    if wins <= 0:
        out.append("40_draws.ward_win_sum totals zero: no ward was won in any "
                   "draw, which `argmax` cannot produce")
    elif draws is not None:
        if wins % draws:
            out.append(
                f"40_draws.ward_win_sum totals {wins}, which is not a whole "
                f"multiple of {draws} draws. Every draw seats every ward, so "
                f"the total is draws x wards exactly; a remainder of "
                f"{wins % draws} means a ward was skipped or double-counted")
    return out


def chamber_fill(seat_draws, council: int) -> dict[int, int]:
    """``{seats actually filled: how many draws filled that many}``.

    **This flags rather than corrects, and "sums to the council" is the wrong
    invariant.** Schedule 1 strikes the quota over ``council - C - D``: ``C``
    independent ward winners and ``D`` ward winners from parties with no PR
    list leave the pool WITH the councillor. A forecaster's draws may therefore
    legitimately fill fewer than ``council`` seats, and the shortfall is
    ``C + D``, not an error. What would be an error is a shortfall nobody can
    account for, or a chamber larger than the statute allows under a rule that
    does not grow it.
    """
    fill: dict[int, int] = {}
    for draw in seat_draws:
        total = int(sum(draw.values()))
        fill[total] = fill.get(total, 0) + 1
    return dict(sorted(fill.items()))


def faults_in_seat_draws(seat_draws, *, council: int, draws=None,
                         universe=None, rule="deduct",
                         outside_pool=0) -> list[str]:
    """Complaints about a ``44_seat_draws`` payload: one seat dict per draw.

    Units: whole councillors. Each dict is a party's TOTAL entitlement (ward
    councillors and list councillors together), which is what Schedule 1
    allocates — not the list half.

    THE CONSERVATION CLAIM IS ``sum(seats) == council - C - D``, and it holds
    on EVERY branch of ``allocate_with_overhang`` — `deduct` returns
    ``{**sub.seats, **fixed}`` over ``COUNCIL - sum(fixed)``, `expand` adds the
    excess to a council grown by the same amount, `level` allocates over the
    grown total. The council moves; the identity does not.

    ``rule`` and ``outside_pool`` are arguments rather than assumptions because
    neither ``C``, ``D`` nor the per-draw council reaches any stage payload —
    an observer cannot recover them and must be told. ``outside_pool`` DEFAULTS
    TO ZERO, which is a statement about this model and not a convenience:
    ``run_model``'s universe drops INDEPENDENT and IND, so no draw can seat an
    independent and ``C`` is structurally zero (registered in
    JUDGEMENT-CALLS.md — the IEC records ``C = 1`` at eThekwini 2011 and
    ``C = 4`` at 2016, and the model is charged for both). ``D`` needs a ward
    winner whose citywide PR total rounds to zero. Pass ``outside_pool=None``
    to check only that the chamber is non-empty.
    """
    out: list[str] = []
    if not isinstance(seat_draws, list):
        return [f"44_seat_draws should be a list of per-draw dicts, got "
                f"{type(seat_draws).__name__}"]
    if not seat_draws:
        return ["44_seat_draws is empty: the run recorded no draw"]
    if draws is not None and len(seat_draws) != draws:
        out.append(f"44_seat_draws holds {len(seat_draws)} draws against "
                   f"{draws} asked for")

    for i, draw in enumerate(seat_draws):
        if not isinstance(draw, dict):
            out.append(f"44_seat_draws[{i}] is not a dict")
            break
        for party, n in draw.items():
            if isinstance(n, bool) or not isinstance(n, int):
                out.append(f"44_seat_draws[{i}]: {party} holds {n!r}, which is "
                           f"not a whole seat. Seats are indivisible; a float "
                           f"here means a mean or a median was stored where a "
                           f"draw belongs")
                break
            if n < 0:
                out.append(f"44_seat_draws[{i}]: {party} holds {n} seats")
                break
        else:
            continue
        break

    if universe is not None:
        seen = {p for draw in seat_draws for p in draw}
        if seen - set(universe):
            out.append(f"44_seat_draws seats parties outside the universe: "
                       f"{sorted(seen - set(universe))[:6]}")

    fill = chamber_fill(seat_draws, council)
    if any(n <= 0 for n in fill):
        out.append("44_seat_draws: a draw seats nobody at all")
    if outside_pool is None:
        return out
    expected = council - outside_pool
    if rule in EXPANDING_RULES:
        short = {n: c for n, c in fill.items() if n < expected}
        if short:
            out.append(
                f"44_seat_draws: under the {rule!r} rule the council can only "
                f"GROW from {council}, and with C + D = {outside_pool} no draw "
                f"can fill fewer than {expected} seats — "
                f"{sum(short.values())} do ({sorted(short)[:4]})")
    else:
        wrong = {n: c for n, c in fill.items() if n != expected}
        if wrong:
            out.append(
                f"44_seat_draws: {sum(wrong.values())} of {len(seat_draws)} "
                f"draw(s) fill {sorted(wrong)[:4]} seats, not the {expected} "
                f"that `council - C - D` requires (council {council}, "
                f"C + D = {outside_pool}). The {rule!r} rule recomputes the "
                f"quota over the seats that are left and does NOT move the "
                f"chamber, so every branch of `allocate_with_overhang` returns "
                f"exactly this total. Either a seat went missing, or C + D is "
                f"no longer zero — and C is only zero because the universe "
                f"drops INDEPENDENT and IND, which is a registered assumption "
                f"rather than a law")
    return out


def faults_between_summary_and_detail(payload, pr, wd, seat_draws,
                                      tol=1e-9) -> list[str]:
    """Is ``40_draws`` actually a summary of ``42``, ``43`` and ``44``?

    This is the cross-stage identity and it is the most valuable check in the
    file, because it catches three separate defect classes with one comparison:

    * a summary computed from a DIFFERENT array than the one recorded, which
      is what a stale or re-ordered intermediate looks like from outside;
    * a statistic stored under another statistic's name — a per-party MEDIAN
      under ``seat_mean``. Those are different numbers and only one of them is
      a council: measured at joburg 2021, 400 draws, the marginal medians sum
      to 254 and the means to exactly 270. This project has stored one under
      the other's name twice;
    * COLUMN MISALIGNMENT. ``42`` and ``43`` carry no party names at all. The
      only thing that makes them readable is that ``universe`` is built with
      ``sorted(...)`` and ``Trace.put`` dumps with ``sort_keys=True``, so
      column *i* belongs to ``sorted(payload["pr_mean"])[i]``. Break either and
      every party's band silently belongs to another party. Comparing
      POSITIONALLY, as this does, is what makes that visible.
    """
    out: list[str] = []
    names = sorted(payload["pr_mean"])
    for label, arr, fields in (
            ("42_pr_share_draws", pr,
             (("pr_mean", lambda a: a.mean(axis=0)),
              ("pr_p5", lambda a: np.percentile(a, 5, axis=0)),
              ("pr_p95", lambda a: np.percentile(a, 95, axis=0)))),
            ("43_ward_share_draws", wd,
             (("ward_mean", lambda a: a.mean(axis=0)),))):
        arr = np.asarray(arr, dtype=float)
        if arr.ndim != 2 or arr.shape[1] != len(names):
            out.append(f"{label}: shape {arr.shape} cannot be read against the "
                       f"{len(names)} parties named in 40_draws")
            continue
        for field, stat in fields:
            want = np.array([payload[field][n] for n in names])
            got = np.asarray(stat(arr), dtype=float)
            gap = float(np.abs(got - want).max())
            if gap > tol:
                worst = names[int(np.argmax(np.abs(got - want)))]
                out.append(
                    f"40_draws.{field} is not the {field.split('_')[-1]} of "
                    f"{label}: worst gap {gap:.3g} at {worst} (recorded "
                    f"{payload[field][worst]:.6g}, recomputed "
                    f"{float(got[names.index(worst)]):.6g}). Either the "
                    f"summary was taken from a different array, or the "
                    f"columns no longer line up with sorted(pr_mean)")

    parties = sorted(payload["seat_mean"])
    if seat_draws:
        mean = {p: float(np.mean([s.get(p, 0) for s in seat_draws]))
                for p in parties}
        gap = max((abs(mean[p] - payload["seat_mean"][p]) for p in parties),
                  default=0.0)
        if gap > tol:
            worst = max(parties, key=lambda p: abs(mean[p]
                                                   - payload["seat_mean"][p]))
            median = {p: float(statistics.median(
                [s.get(p, 0) for s in seat_draws])) for p in parties}
            hint = ""
            if abs(median[worst] - payload["seat_mean"][worst]) <= tol:
                hint = (f" — and it IS the per-party MEDIAN, which is a "
                        f"different statistic and does not sum to a council "
                        f"(medians {sum(median.values()):.0f}, means "
                        f"{sum(mean.values()):.0f})")
            out.append(
                f"40_draws.seat_mean is not the mean of 44_seat_draws: worst "
                f"gap {gap:.3g} at {worst}{hint}")
    return out


def faults_in_guards(guards, *, draws=None, universe=None) -> list[str]:
    """Complaints about a ``41_guards`` payload: twenty counters and their bounds.

    A guard counter nobody reads is a guard nobody is checking, and every one
    of these had no route out of ``run_model`` until this week. The checks are
    of three kinds and the third is the one that matters:

    1. **the board is whole** — the key set equals :data:`GUARD_KEYS` in both
       directions, so a counter deleted from the model and a counter added to
       it without being declared here both fail;
    2. **the counters are bounded by their own denominators** — a count of
       draws cannot exceed the draws;
    3. **THE DENOMINATORS ARE NON-ZERO.** This is the positive control on the
       observer. A board of zeros is what a healthy run and a run in which
       nothing was counted both look like, and `arrival_reconciliation` is the
       precedent: blind at 20 of 24 rows, reporting nothing wrong.
    """
    out: list[str] = []
    keys = set(guards)
    missing = sorted(GUARD_KEYS - keys)
    if missing:
        out.append(f"41_guards is missing counter(s) {missing}: the observer "
                   f"declares them and the run did not emit them")
    undeclared = sorted(keys - GUARD_KEYS)
    if undeclared:
        out.append(
            f"41_guards emits counter(s) {undeclared} that this observer does "
            f"not declare. A new counter must be added to GUARD_KEYS with a "
            f"bound, or it joins the class this file exists against: computed, "
            f"written, and read by nobody")

    for key in GUARD_DENOMINATOR_KEYS:
        if key in guards and not guards[key]:
            out.append(
                f"41_guards.{key} is zero, so every rate taken against it is "
                f"0/0 and the whole board is unreadable. This is not a clean "
                f"run; it is a run that counted nothing")

    for key, value in sorted(guards.items()):
        if isinstance(value, dict):
            for party, n in value.items():
                if not isinstance(n, (int, float)) or isinstance(n, bool):
                    out.append(f"41_guards.{key}[{party}] is {n!r}")
                elif n < 0 or not math.isfinite(n):
                    out.append(f"41_guards.{key}[{party}] is {n}")
            if universe is not None and set(value) - set(universe):
                out.append(f"41_guards.{key} names parties outside the "
                           f"universe: {sorted(set(value) - set(universe))[:6]}")
        elif isinstance(value, bool) or not isinstance(value, (int, float)):
            out.append(f"41_guards.{key} is {value!r}, not a number")
        elif not math.isfinite(value) or value < 0:
            out.append(f"41_guards.{key} is {value}; every counter here is a "
                       f"non-negative, finite quantity")

    for counter, denom_key in GUARD_DENOMINATORS.items():
        denom = guards.get(denom_key)
        table = guards.get(counter)
        if not isinstance(table, dict) or not isinstance(denom, (int, float)):
            continue
        for party, n in sorted(table.items()):
            if n > denom:
                out.append(
                    f"41_guards.{counter}[{party}] is {n}, above its own "
                    f"denominator {denom_key}={denom}. A count of draws cannot "
                    f"exceed the draws it was counted over, so the two are not "
                    f"measuring the same population")

    def _le(small, big, why):
        a, b = guards.get(small), guards.get(big)
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) and a > b:
            out.append(f"41_guards.{small}={a} exceeds {big}={b}: {why}")

    _le("ipf_failures", "ipf_balances",
        "a balance cannot fail more often than it was attempted")
    _le("solve_nonconvergent", "solve_calls",
        "a solve cannot fail to converge more often than it ran")
    _le("solve_nonconvergent_reachable", "solve_nonconvergent",
        "the reachable subset cannot be larger than the whole")
    _le("solve_calls", "solve_rounds",
        "every solve runs at least one round")
    _le("solve_worst_gap_reachable", "solve_worst_gap",
        "the worst gap over a subset cannot exceed the worst over everything")
    _le("solve_floor_injected_mean", "solve_floor_injected_worst",
        "a mean cannot exceed the worst case it is a mean of")

    if draws is not None:
        for key in ("bounds_checked", "ipf_balances", "excessive_draws"):
            n = guards.get(key)
            if isinstance(n, (int, float)) and n > draws:
                out.append(f"41_guards.{key}={n} exceeds the {draws} draws")
        if guards.get("bounds_checked") not in (None, draws):
            out.append(
                f"41_guards.bounds_checked={guards['bounds_checked']} is not "
                f"the {draws} draws. It is incremented exactly once per draw, "
                f"so it IS the draw count — and it is the only thing tying "
                f"this payload to the draws it claims to describe")

    excessive = guards.get("excessive_draws")
    over = guards.get("overhang_count")
    if isinstance(excessive, int) and isinstance(over, dict):
        if sum(over.values()) < excessive:
            out.append(
                f"41_guards: overhang_count sums to {sum(over.values())} while "
                f"excessive_draws is {excessive}. The first counts "
                f"(draw, party) pairs and the second counts draws with any "
                f"such party, so the first can only be the larger")
        if excessive and not over:
            out.append("41_guards: excessive_draws is non-zero and "
                       "overhang_count is empty, so a draw triggered item 16 "
                       "and no party is named as having triggered it")

    # THE CAPACITY REPORT AND THE DRAWS MUST BE ABOUT THE SAME PARTIES.
    # `ipf_headroom` is the pre-draw ratio of what each party's centre asks for
    # to what its pools can hold — the one counter that says who was ALREADY
    # near the ceiling before any shock. It is built over the union of pool
    # MEMBERS, which is not obliged to be the whole universe, so the bound is
    # two-sided rather than an equality: a headroom map covering a handful of
    # parties is a map of a different model.
    headroom = guards.get("ipf_headroom")
    if isinstance(headroom, dict) and universe is not None and universe:
        if headroom and len(headroom) < 0.5 * len(universe):
            out.append(
                f"41_guards.ipf_headroom covers {len(headroom)} of "
                f"{len(universe)} parties in the universe. It is the only "
                f"pre-draw view of who is near their pool ceiling, and over a "
                f"fraction of the ballot it reports on a party set the draws "
                f"are not about")

    if isinstance(guards.get("ipf_balances"), int) and guards["ipf_balances"]:
        if guards.get("ipf_failures") == guards["ipf_balances"]:
            out.append(
                "41_guards: every IPF balance failed, so the level shock was "
                "degraded to a partial balance in every draw and the model's "
                "central mechanism did not run once")
    if isinstance(guards.get("cap_undershoots"), int) \
            and guards["cap_undershoots"]:
        out.append(
            f"41_guards.cap_undershoots is {guards['cap_undershoots']}: "
            f"`capped_targets` took the branch where every party at its own "
            f"capacity still cannot fill the city. It then returns a vector "
            f"with EVERY element above its cap — the opposite of the "
            f"function's name — and the caller's fallback is what reports it")
    return out


def faults_in_delivery_log(payload) -> list[str]:
    """Complaints about a ``45_delivered`` payload: the value-bearing read log.

    Each record is ``{values, where, kinds, who, reads, dropped}``. ``reads``
    counts every read; the four lists are de-duplicated and capped at
    ``montecarlo.DELIVERY_MAX_VALUES``, with ``dropped`` counting what the cap
    refused — so ``dropped > 0`` is only coherent when the list is full.

    The claim strength lives in ``kinds`` and it is the whole point of the
    stage: ``consulted`` is recorded AT the site that reads a value and is a
    delivery proof; ``resolved`` says only that this process held the value,
    and §1.68 was burned by reporting a ``resolved`` record as evidence that a
    lever was inert.
    """
    out: list[str] = []
    if not isinstance(payload, dict):
        return [f"45_delivered should be a dict of records, got "
                f"{type(payload).__name__}"]
    if not payload:
        return ["45_delivered is empty: the run recorded no read at all, so "
                "nothing it did can be attributed to a value"]
    for name, rec in sorted(payload.items()):
        if not isinstance(rec, dict):
            out.append(f"45_delivered[{name}] is not a record")
            continue
        if set(rec) != DELIVERY_RECORD_KEYS:
            out.append(f"45_delivered[{name}] has fields {sorted(rec)}, not "
                       f"{sorted(DELIVERY_RECORD_KEYS)}")
            continue
        reads, dropped = rec["reads"], rec["dropped"]
        if not isinstance(reads, int) or reads < 1:
            out.append(f"45_delivered[{name}].reads is {reads!r}; a record "
                       f"exists only because a read created it, so it is at "
                       f"least one")
        for field in ("values", "where", "kinds", "who"):
            items = rec[field]
            if not isinstance(items, list):
                out.append(f"45_delivered[{name}].{field} is not a list")
                continue
            if len(items) > M.DELIVERY_MAX_VALUES:
                out.append(f"45_delivered[{name}].{field} holds {len(items)} "
                           f"entries, above the cap "
                           f"{M.DELIVERY_MAX_VALUES}")
            if field != "values":
                seen = [json.dumps(i, sort_keys=True, default=repr)
                        for i in items]
                if len(set(seen)) != len(seen):
                    out.append(f"45_delivered[{name}].{field} repeats an "
                               f"entry; the log de-duplicates on append")
        if isinstance(reads, int) and isinstance(rec["values"], list) \
                and reads < len(rec["values"]):
            out.append(
                f"45_delivered[{name}] records {len(rec['values'])} distinct "
                f"values from {reads} read(s); each read can add at most one")
        if isinstance(dropped, int) and dropped > 0 \
                and len(rec["values"]) < M.DELIVERY_MAX_VALUES:
            out.append(
                f"45_delivered[{name}] dropped {dropped} value(s) while its "
                f"list holds only {len(rec['values'])} of "
                f"{M.DELIVERY_MAX_VALUES}; the cap is the only thing that "
                f"drops, so it cannot have")
        kinds = set(rec["kinds"]) if isinstance(rec["kinds"], list) else set()
        if not kinds:
            out.append(f"45_delivered[{name}] carries no kind, so the strength "
                       f"of its claim is unstated")
        elif kinds - DELIVERY_KINDS:
            out.append(f"45_delivered[{name}] uses unknown kind(s) "
                       f"{sorted(kinds - DELIVERY_KINDS)}")
    return out


def absent_constants(payload) -> list[str]:
    """Names the delivery log records as NOT THERE TO READ.

    ``note_module_constants`` writes ``not-imported`` when a declared module
    was never imported and ``missing`` when the name is not on it. Both are
    legitimate records and neither is a malformed one — which is exactly why
    they are reported separately from :func:`faults_in_delivery_log` rather
    than folded into it. A renamed constant shows up here as an absence
    instead of as silence.
    """
    return sorted(
        name for name, rec in payload.items()
        if isinstance(rec, dict)
        and set(rec.get("kinds") or []) & {"not-imported", "missing"})


# --------------------------------------------------------------------------
# the tie detector
# --------------------------------------------------------------------------

def tie_at_the_cut(combined, total_seats, independent_wards=0,
                   no_pr_list_wards=0):
    """The pair straddling the largest-remainder cut when it is an EXACT tie.

    Returns ``(inside, outside, votes, shortfall)`` or ``None``.

    ``seats.allocate`` ranks remainders by ``(-remainder, -combined)``. For two
    parties with the same combined vote total that key is IDENTICAL, Python's
    sort is stable, and the seat therefore goes to whichever party came first
    in the dict — which for a dict built by ``seats.eligible_parties`` is a
    SET-OF-STRINGS iteration order, i.e. a function of how the party's NAME
    hashes and of nothing electoral whatsoever.

    Schedule 1 breaks an exact tie by lot. `allocate`'s docstring says float
    remainders make an exact tie unreachable; they do not, because equal
    integer vote totals give bit-identical remainders. Measured at joburg 2021,
    400 draws: three allocations hit this, and reversing the key order moved a
    seat between ALJAMAAH and UIM in one of them.
    """
    available = total_seats - independent_wards - no_pr_list_wards
    if available <= 0 or not combined:
        return None
    total = sum(combined.values())
    quota = total // available + 1
    round_one = {p: v // quota for p, v in combined.items()}
    remainders = {p: v / quota - round_one[p] for p, v in combined.items()}
    shortfall = available - sum(round_one.values())
    if shortfall <= 0 or shortfall >= len(remainders):
        return None
    ranked = sorted(remainders, key=lambda p: (-remainders[p], -combined[p]))
    inside, outside = ranked[shortfall - 1], ranked[shortfall]
    if (remainders[inside], combined[inside]) \
            == (remainders[outside], combined[outside]):
        return (inside, outside, combined[inside], shortfall)
    return None


def allocation_outcomes_over_orderings(combined, *, total_seats,
                                       independent_wards=0, no_pr_list_wards=0,
                                       orderings=24):
    """Distinct seat vectors ``seats.allocate`` gives over key permutations.

    More than one means the allocation is decided by dict order rather than by
    votes. The permutations are the detector; the input is constructed, so this
    does not expire when the tree changes.
    """
    parties = list(combined)
    seen = set()
    for i, order in enumerate(itertools.permutations(parties)):
        if i >= orderings:
            break
        shuffled = {p: combined[p] for p in order}
        alloc = allocate(shuffled, total_seats=total_seats,
                         independent_wards=independent_wards,
                         no_pr_list_wards=no_pr_list_wards)
        seen.add(tuple(sorted(alloc.seats.items())))
    return seen


# --------------------------------------------------------------------------
# constructed payloads — healthy, and corrupted one field at a time
# --------------------------------------------------------------------------

PARTIES = ["AAA", "BBB", "CCC", "DDD"]
DRAWS = 6
WARDS = 5
COUNCIL = 10


def healthy_shares(seed=1):
    rng = np.random.default_rng(seed)
    arr = rng.dirichlet([40.0, 25.0, 8.0, 2.0], size=DRAWS)
    return arr / arr.sum(axis=1, keepdims=True)


def healthy_seat_draws(pr):
    """Seat draws that really are an allocation of ``pr``, filling ``COUNCIL``."""
    out = []
    for row in pr:
        votes = {p: int(round(float(v) * 100_000)) for p, v in zip(PARTIES, row)}
        alloc = allocate(votes, total_seats=COUNCIL)
        out.append({p: int(alloc.seats.get(p, 0)) for p in PARTIES})
    return out


def healthy_draws_summary(pr, wd, seat_draws, wins=None):
    wins = wins or {PARTIES[0]: DRAWS * WARDS - DRAWS, PARTIES[1]: DRAWS}
    return {
        "pr_mean": {p: float(pr[:, i].mean()) for i, p in enumerate(PARTIES)},
        "pr_p5": {p: float(np.percentile(pr[:, i], 5))
                  for i, p in enumerate(PARTIES)},
        "pr_p95": {p: float(np.percentile(pr[:, i], 95))
                   for i, p in enumerate(PARTIES)},
        "ward_mean": {p: float(wd[:, i].mean()) for i, p in enumerate(PARTIES)},
        "ward_win_sum": dict(wins),
        "seat_mean": {p: float(np.mean([s.get(p, 0) for s in seat_draws]))
                      for p in {q for s in seat_draws for q in s}},
    }


def healthy_guards():
    return {
        "bounds_checked": DRAWS,
        "bounds_violations": {"AAA": 2},
        "cap_moved": 12.5,
        "cap_undershoots": 0,
        "excessive_draws": 1,
        "overhang_count": {"AAA": 1},
        "ipf_balances": DRAWS,
        "ipf_failures": 0,
        "ipf_clipped": {"DDD": 3},
        "ipf_headroom": {p: 0.2 for p in PARTIES},
        "solve_calls": 2 * DRAWS,
        "solve_rounds": 80 * DRAWS,
        "solve_nonconvergent": 2 * DRAWS,
        "solve_nonconvergent_reachable": 2 * DRAWS,
        "solve_worst_gap": 1.2e-5,
        "solve_worst_gap_reachable": 1.2e-5,
        "solve_unreachable_parties": 1,
        "solve_floor_injected_mean": 1.4e-5,
        "solve_floor_injected_worst": 2.7e-5,
        "solve_identity_hits": 0,
    }


def healthy_delivery_log():
    return {
        "montecarlo.COUNCIL": {"values": [COUNCIL], "where": ["m:run_model"],
                               "kinds": ["consulted"], "who": ["(all)"],
                               "reads": 1, "dropped": 0},
        "levels.SHRINK": {"values": [0.35], "where": ["m:run_model"],
                          "kinds": ["resolved"], "who": ["(all)"],
                          "reads": 1, "dropped": 0},
    }


def _payloads():
    pr = healthy_shares(1)
    wd = healthy_shares(2)
    seat_draws = healthy_seat_draws(pr)
    return pr, wd, seat_draws, healthy_draws_summary(pr, wd, seat_draws)


# --------------------------------------------------------------------------
# 42 / 43 — the share matrices
# --------------------------------------------------------------------------

def test_a_healthy_share_matrix_draws_no_complaint():
    pr, wd, _, _ = _payloads()
    assert not faults_in_share_matrix(pr, draws=DRAWS, parties=len(PARTIES))
    assert not faults_in_share_matrix(wd, draws=DRAWS, parties=len(PARTIES))


def test_an_unfilled_row_is_caught():
    """The signature of a draw loop that ended early, and the only way to see it.

    ``pr_share_draws`` is ``np.zeros((draws, npar))`` filled inside the loop.
    A loop that stopped leaves zero rows behind, and every summary taken over
    them is diluted towards zero rather than absent — which reads as a quiet
    forecast, not as a broken one.
    """
    pr, _, _, _ = _payloads()
    broken = pr.copy()
    broken[3] = 0.0
    faults = faults_in_share_matrix(broken, draws=DRAWS, parties=len(PARTIES))
    assert faults, "an all-zero row passed the share check"
    assert "ALL ZERO" in " ".join(faults), faults


def test_a_row_that_does_not_sum_to_one_is_caught():
    pr, _, _, _ = _payloads()
    broken = pr.copy()
    broken[1, 0] += 0.01
    faults = faults_in_share_matrix(broken, draws=DRAWS, parties=len(PARTIES))
    assert faults and "sum to one" in " ".join(faults), faults


def test_a_negative_share_and_a_wrong_shape_are_caught():
    pr, _, _, _ = _payloads()
    broken = pr.copy()
    spill = broken[0, 0] + 0.05          # drive one column strictly below zero
    broken[0, 0] -= spill
    broken[0, 1] += spill
    assert broken[0, 0] < 0, broken[0, 0]
    assert any("negative" in f for f in faults_in_share_matrix(broken)), \
        faults_in_share_matrix(broken)
    assert faults_in_share_matrix(pr[:, :2], parties=len(PARTIES))
    assert faults_in_share_matrix(pr, draws=DRAWS + 1)
    assert faults_in_share_matrix(np.zeros((0, 4)))


# --------------------------------------------------------------------------
# 40 — the summary
# --------------------------------------------------------------------------

def test_a_healthy_draws_summary_draws_no_complaint():
    _, _, _, payload = _payloads()
    assert not faults_in_draws_summary(payload, draws=DRAWS, universe=PARTIES)


def test_a_summary_whose_means_do_not_sum_to_one_is_caught():
    _, _, _, payload = _payloads()
    payload["pr_mean"]["AAA"] += 0.05
    faults = faults_in_draws_summary(payload, draws=DRAWS)
    assert faults and "sums to" in " ".join(faults), faults


def test_a_swapped_percentile_band_is_caught():
    _, _, _, payload = _payloads()
    party = PARTIES[0]
    payload["pr_p5"][party], payload["pr_p95"][party] = (
        payload["pr_p95"][party], payload["pr_p5"][party])
    faults = faults_in_draws_summary(payload, draws=DRAWS)
    assert faults and "swapped" in " ".join(faults), faults


def test_a_party_set_that_drifted_between_fields_is_caught():
    _, _, _, payload = _payloads()
    payload["ward_mean"]["EEE"] = payload["ward_mean"].pop(PARTIES[-1])
    faults = faults_in_draws_summary(payload, draws=DRAWS)
    assert faults and "different party set" in " ".join(faults), faults


def test_a_ward_win_total_that_is_not_a_multiple_of_the_draws_is_caught():
    """Every draw seats every ward, so the total is draws x wards exactly.

    `argmax` over a ward's tally always returns something, so ward wins are
    conserved by construction. A total that is not a whole multiple of the
    draws means a ward was skipped or counted twice — which is the only way
    this quantity can move at all, and therefore the only thing worth asserting
    about it.
    """
    _, _, _, payload = _payloads()
    assert not faults_in_draws_summary(payload, draws=DRAWS)
    payload["ward_win_sum"][PARTIES[0]] -= 1
    faults = faults_in_draws_summary(payload, draws=DRAWS)
    assert faults and "whole multiple" in " ".join(faults), faults


def test_an_undeclared_field_in_the_summary_is_caught():
    _, _, _, payload = _payloads()
    payload["seat_median"] = {p: 1 for p in PARTIES}
    faults = faults_in_draws_summary(payload, draws=DRAWS)
    assert faults and "undeclared" in " ".join(faults), faults


# --------------------------------------------------------------------------
# 44 — the seat draws
# --------------------------------------------------------------------------

def test_healthy_seat_draws_draw_no_complaint():
    _, _, seat_draws, _ = _payloads()
    assert chamber_fill(seat_draws, COUNCIL) == {COUNCIL: DRAWS}
    assert not faults_in_seat_draws(seat_draws, council=COUNCIL, draws=DRAWS,
                                    universe=PARTIES, rule="deduct")


def test_a_chamber_larger_than_the_statute_is_caught_under_deduct():
    _, _, seat_draws, _ = _payloads()
    seat_draws[2][PARTIES[0]] += 1
    faults = faults_in_seat_draws(seat_draws, council=COUNCIL, rule="deduct")
    assert faults and "does NOT move the chamber" in " ".join(faults), faults


def test_an_underfilled_chamber_is_reported_not_refused():
    """``council - C - D`` is a legitimate fill and the wrong thing to refuse.

    Schedule 1 takes independent ward winners and the ward winners of parties
    with no PR list out of the pool WITH the councillor. A draw that seats
    ``council - C - D`` is correct, so `chamber_fill` exists to flag it and
    `faults_in_seat_draws` deliberately does not complain — while the same
    shortfall under an EXPANDING rule is impossible and is refused.
    """
    _, _, seat_draws, _ = _payloads()
    for draw in seat_draws:
        draw[PARTIES[0]] -= 2               # C + D = 2 in every draw
    assert chamber_fill(seat_draws, COUNCIL) == {COUNCIL - 2: DRAWS}
    # FLAGGED, not corrected: told what C + D is, the observer is content.
    assert not faults_in_seat_draws(seat_draws, council=COUNCIL, rule="deduct",
                                    outside_pool=2)
    # Not told at all, it declines to judge the fill and says nothing about it.
    assert not faults_in_seat_draws(seat_draws, council=COUNCIL, rule="deduct",
                                    outside_pool=None)
    # Told that C + D is zero — the truth for this model — an unexplained
    # shortfall is a missing seat and is refused.
    faults = faults_in_seat_draws(seat_draws, council=COUNCIL, rule="deduct")
    assert faults and "council - C - D" in " ".join(faults), faults
    faults = faults_in_seat_draws(seat_draws, council=COUNCIL, rule="expand")
    assert faults and "can only" in " ".join(faults), faults


def test_a_fractional_seat_is_caught():
    """A float in a seat draw is a mean or a median stored where a draw belongs."""
    _, _, seat_draws, _ = _payloads()
    seat_draws[1][PARTIES[0]] = 4.5
    faults = faults_in_seat_draws(seat_draws, council=COUNCIL, rule="deduct")
    assert faults and "not a whole seat" in " ".join(faults), faults


def test_a_party_outside_the_universe_is_caught():
    _, _, seat_draws, _ = _payloads()
    seat_draws[0]["GHOST"] = 0
    faults = faults_in_seat_draws(seat_draws, council=COUNCIL, universe=PARTIES,
                                  rule="deduct")
    assert faults and "outside the universe" in " ".join(faults), faults


# --------------------------------------------------------------------------
# the cross-stage identity — 40 against 42, 43 and 44
# --------------------------------------------------------------------------

def test_a_healthy_summary_agrees_with_its_own_detail():
    pr, wd, seat_draws, payload = _payloads()
    assert not faults_between_summary_and_detail(payload, pr, wd, seat_draws)


def test_the_marginal_median_stored_as_the_mean_is_caught():
    """The defect this project has had twice, and it is not a rounding one.

    A per-party median over draws does not sum to a council; an apportionment
    of the mean vector does. Measured on the real trace generated below
    (joburg 2021, 400 draws): medians 254, means exactly 270. So the two are
    tens of seats apart and a reader cannot tell which they are holding from
    the number alone — only from the name it is stored under.
    """
    pr, wd, seat_draws, payload = _payloads()
    parties = sorted(payload["seat_mean"])
    payload["seat_mean"] = {
        p: float(statistics.median([s.get(p, 0) for s in seat_draws]))
        for p in parties}
    faults = faults_between_summary_and_detail(payload, pr, wd, seat_draws)
    assert faults, "a median stored under `seat_mean` passed unnoticed"
    assert "MEDIAN" in " ".join(faults), faults


def test_columns_rolled_by_one_are_caught():
    """42 and 43 carry NO party names; the column order is the whole labelling.

    ``universe`` is `sorted(...)` and `Trace.put` dumps with `sort_keys=True`,
    so column *i* is `sorted(pr_mean)[i]`. Those are two independent decisions
    in two different places, and if either moves, every party's band silently
    belongs to its neighbour with no error anywhere. Rolling the array by one
    column is exactly that failure.
    """
    pr, wd, seat_draws, payload = _payloads()
    faults = faults_between_summary_and_detail(payload, np.roll(pr, 1, axis=1),
                                               wd, seat_draws)
    assert faults and "line up" in " ".join(faults), faults


def test_a_summary_taken_from_a_different_array_is_caught():
    pr, wd, seat_draws, payload = _payloads()
    faults = faults_between_summary_and_detail(payload, healthy_shares(9), wd,
                                               seat_draws)
    assert faults and "pr_mean" in " ".join(faults), faults


# --------------------------------------------------------------------------
# 41 — the guards
# --------------------------------------------------------------------------

def test_a_healthy_guard_board_draws_no_complaint():
    assert not faults_in_guards(healthy_guards(), draws=DRAWS, universe=PARTIES)


def test_the_declared_board_is_neither_short_nor_long():
    """Bidirectional, because one direction is the class with the worst record.

    A counter deleted from `run_model` must fail here, and so must a counter
    ADDED to it without being declared — the register guard checked
    code->register and never register->code, and a deleted lever sat in the
    register for days while the scan stayed green.
    """
    guards = healthy_guards()
    assert set(guards) == set(GUARD_KEYS)
    scanned(GUARD_KEYS, of=guards, low=1.0, high=1.0,
            what="declared guard counters",
            denominator="counters in a 41_guards payload")
    short = {k: v for k, v in guards.items() if k != "ipf_failures"}
    assert any("missing" in f for f in faults_in_guards(short)), short
    long = dict(guards, ipf_something_new=3)
    assert any("does not declare" in f for f in faults_in_guards(long))


def test_a_zero_denominator_makes_the_whole_board_unreadable():
    """THE POSITIVE CONTROL ON THE OBSERVER.

    `arrival_reconciliation` was blind at 20 of 24 rows while reporting nothing
    wrong, because it read an index that no longer held what it thought. A
    board of zeros looks exactly like a clean run. The denominators are what
    separate "nothing fired" from "nothing was counted", so they are asserted
    non-zero before any rate taken against them is believed.
    """
    for key in GUARD_DENOMINATOR_KEYS:
        guards = dict(healthy_guards(), **{key: 0})
        faults = faults_in_guards(guards)
        assert any("unreadable" in f for f in faults), (key, faults)


def test_a_counter_above_its_own_denominator_is_caught():
    guards = healthy_guards()
    guards["bounds_violations"]["AAA"] = guards["bounds_checked"] + 1
    faults = faults_in_guards(guards, draws=DRAWS)
    assert faults and "above its own denominator" in " ".join(faults), faults


def test_the_orderings_between_guard_counters_are_enforced():
    pairs = [("ipf_failures", "ipf_balances"),
             ("solve_nonconvergent", "solve_calls"),
             ("solve_nonconvergent_reachable", "solve_nonconvergent"),
             ("solve_worst_gap_reachable", "solve_worst_gap"),
             ("solve_floor_injected_mean", "solve_floor_injected_worst")]
    for small, big in pairs:
        guards = healthy_guards()
        guards[small] = guards[big] * 2 + 1
        faults = faults_in_guards(guards, draws=DRAWS)
        assert any(f"{small}" in f and "exceeds" in f for f in faults), \
            (small, big, faults)


def test_bounds_checked_is_the_draw_count_and_ties_the_board_to_the_draws():
    """The only field tying `41_guards` to the draws it claims to describe.

    `bounds_checked` is incremented exactly once per draw, so it IS the draw
    count. Nothing else in the payload is — every other counter is a count of
    events that may or may not have happened — so a guards payload from one run
    read beside another run's draws is invisible without it.
    """
    guards = healthy_guards()
    assert not faults_in_guards(guards, draws=DRAWS)
    faults = faults_in_guards(guards, draws=DRAWS + 1)
    assert faults and "is not the" in " ".join(faults), faults


def test_an_overhang_count_that_cannot_explain_its_own_draws_is_caught():
    guards = healthy_guards()
    guards["excessive_draws"] = 4
    guards["overhang_count"] = {}
    faults = faults_in_guards(guards, draws=DRAWS)
    assert faults and "no party is named" in " ".join(faults), faults
    guards["overhang_count"] = {"AAA": 1}
    assert any("sums to" in f for f in faults_in_guards(guards, draws=DRAWS))


def test_a_total_ipf_failure_and_a_capacity_undershoot_are_caught():
    guards = dict(healthy_guards(), ipf_failures=DRAWS)
    faults = faults_in_guards(guards, draws=DRAWS)
    assert any("central mechanism did not run" in f for f in faults), faults
    guards = dict(healthy_guards(), cap_undershoots=2)
    faults = faults_in_guards(guards, draws=DRAWS)
    assert any("opposite of the" in f for f in faults), faults


def test_a_headroom_map_covering_a_fraction_of_the_ballot_is_caught():
    """The pre-draw capacity report must be about the party set that was drawn.

    `ipf_headroom` is the only sight of who was ALREADY at their pools'
    ceiling before any shock — the thing that, until 2026-08-17, nobody found
    out about until the balance raised. A map over a handful of parties is a
    map of a different model, and it fails in the direction that looks healthy:
    fewer entries, none of them alarming.
    """
    guards = healthy_guards()
    assert not faults_in_guards(guards, draws=DRAWS, universe=PARTIES)
    guards["ipf_headroom"] = {PARTIES[0]: 0.2}
    faults = faults_in_guards(guards, draws=DRAWS, universe=PARTIES)
    assert faults and "covers 1 of 4" in " ".join(faults), faults


def test_a_negative_or_non_finite_counter_is_caught():
    assert faults_in_guards(dict(healthy_guards(), ipf_balances=-1))
    assert faults_in_guards(dict(healthy_guards(),
                                 solve_worst_gap=float("nan")))
    guards = healthy_guards()
    guards["ipf_clipped"] = {"GHOST": 1}
    assert any("outside the universe" in f
               for f in faults_in_guards(guards, universe=PARTIES))


# --------------------------------------------------------------------------
# 45 — the delivery proof
# --------------------------------------------------------------------------

def test_a_healthy_delivery_log_draws_no_complaint():
    assert not faults_in_delivery_log(healthy_delivery_log())
    assert absent_constants(healthy_delivery_log()) == []


def test_a_record_with_more_values_than_reads_is_caught():
    log = healthy_delivery_log()
    log["montecarlo.COUNCIL"]["values"] = [1, 2, 3]
    faults = faults_in_delivery_log(log)
    assert faults and "each read can add at most one" in " ".join(faults)


def test_a_drop_without_a_full_list_is_caught():
    log = healthy_delivery_log()
    log["montecarlo.COUNCIL"]["dropped"] = 3
    faults = faults_in_delivery_log(log)
    assert faults and "the cap is the only thing that drops" in " ".join(faults)


def test_an_unknown_or_missing_kind_is_caught():
    log = healthy_delivery_log()
    log["montecarlo.COUNCIL"]["kinds"] = ["believed"]
    assert any("unknown kind" in f for f in faults_in_delivery_log(log))
    log["montecarlo.COUNCIL"]["kinds"] = []
    assert any("carries no kind" in f for f in faults_in_delivery_log(log))


def test_a_malformed_record_and_an_empty_log_are_caught():
    log = healthy_delivery_log()
    del log["levels.SHRINK"]["who"]
    assert faults_in_delivery_log(log)
    assert faults_in_delivery_log({})
    assert faults_in_delivery_log([])


def test_an_absent_constant_is_named_rather_than_silent():
    """A renamed constant must show up as an absence, not as silence."""
    log = healthy_delivery_log()
    log["montecarlo.GONE"] = {"values": [None], "where": ["m"],
                              "kinds": ["missing"], "who": ["(all)"],
                              "reads": 1, "dropped": 0}
    assert not faults_in_delivery_log(log), "a `missing` record is well-formed"
    assert absent_constants(log) == ["montecarlo.GONE"]


# --------------------------------------------------------------------------
# the tie — a CHARACTERISATION test, recording a live defect
# --------------------------------------------------------------------------

def test_the_tie_detector_can_see_a_tie_and_stays_quiet_without_one():
    """Positive control on the detector, before anything is claimed with it."""
    tied = {"BIG1": 101, "BIG2": 101, "AAA": 49, "BBB": 49}
    found = tie_at_the_cut(tied, 3)
    assert found is not None, "the detector missed a constructed exact tie"
    assert set(found[:2]) == {"AAA", "BBB"} and found[2] == 49, found
    untied = dict(tied, BBB=48)
    assert tie_at_the_cut(untied, 3) is None, tie_at_the_cut(untied, 3)


def test_largest_remainder_is_decided_by_dict_order_at_an_exact_tie():
    """⛔ CHARACTERISATION, NOT AN INVARIANT: this records a DEFECT.

    ``seats.allocate`` ranks remainders by ``(-remainder, -combined)``. Two
    parties with equal combined votes produce a bit-identical key, Python's
    sort is stable, and the last seat therefore goes to whoever came first in
    the dict. ``seats.eligible_parties`` builds that dict by iterating
    ``set(ward_votes) | set(pr_votes)``, so the order is a function of how the
    party NAME hashes — nothing electoral. Schedule 1 breaks an exact tie BY
    LOT; `allocate`'s own docstring asserts float remainders make an exact tie
    unreachable, and equal integer vote totals reach it directly.

    ``montecarlo.fix_hash_seed`` pins ``PYTHONHASHSEED=0`` at seven entry
    points, so the shipped runs are at least repeatable — but repeatable is not
    the same as correct, and the residue is that RENAMING A PARTY can move a
    seat while nothing else changes.

    **WHEN THIS TEST FAILS, THE DEFECT HAS BEEN FIXED.** Delete it and assert
    the invariant instead: one seat vector over every ordering.

    ⛔ **THREE SIBLING CONTROLS MUST BE RE-POINTED IN THE SAME COMMIT**, and
    they are listed here because they will each announce themselves separately
    and look like three unrelated regressions:

    * ``tests/test_roster_aware_baseline.py:117`` restores the defect with
      ``BM.canonical_order = dict`` — once the order no longer comes from a set,
      that monkeypatch stops restoring anything and the control is testing the
      fixed path while claiming to test the broken one;
    * ``test_eligible_parties_hands_the_allocator_a_set_ordered_dict`` below,
      whose bound is written as the negation of each plausible repair
      **precisely so that it fires here**;
    * this test, the exact-tie mirror.
    """
    tied = {"BIG1": 101, "BIG2": 101, "AAA": 49, "BBB": 49}
    outcomes = allocation_outcomes_over_orderings(tied, total_seats=3)
    assert len(outcomes) > 1, (
        "seats.allocate is now order-invariant at an exact tie, which is what "
        "this repository wants. Replace this characterisation test with the "
        "invariant and note the change in MODEL-LOG.")
    untied = dict(tied, BBB=48)
    assert len(allocation_outcomes_over_orderings(untied, total_seats=3)) == 1


def _output_orders(builder, names, votes):
    """Every distinct output ORDER ``builder`` produces over all permutations of
    its inputs, plus how many of them came back in the caller's own order.

    THE PREDICATE, and it is run three ways below: on the production
    ``eligible_parties``, and on each of the two repairs anybody would plausibly
    write. A characterisation test is only a characterisation if the same
    instrument says something different about the repaired state.
    """
    orders = list(itertools.permutations(names))
    distinct, preserved = set(), 0
    for order in orders:
        ward = {p: votes[p] for p in order}
        out = tuple(builder(ward, {p: 1 for p in order}))
        assert set(out) == set(names), out
        distinct.add(out)
        preserved += (list(out) == list(order))
    return distinct, preserved, len(orders)


def test_eligible_parties_hands_the_allocator_a_set_ordered_dict():
    """The mechanism behind the tie, asserted where it actually lives.

    CHARACTERISATION, like the test above: ``eligible_parties`` builds its dict
    by iterating ``set(ward_votes) | set(pr_votes)``, so the insertion order the
    allocator inherits is a string-hash order carrying nothing from the inputs.

    ⛔ **WHAT THIS ASSERTED UNTIL 2026-09-14 COULD NOT TELL THE TWO STATES
    APART, AND WOULD HAVE CERTIFIED THE FIX IT NEVER TESTED.** The bound was
    ``preserved < len(orders)`` — the number of permutations whose output order
    equals the input order. Measured at ``PYTHONHASHSEED=0`` that count is
    **1**, and under a ``sorted(...)`` repair it is **1 as well**: an output
    order that is CONSTANT matches exactly one of the 24 inputs whichever
    constant it is. ``1 < 24`` passes in both states. **That is requirement 2 of
    CLAUDE.md §4 broken inside a control written to satisfy requirement 2** —
    inert would have been better, because a positive control that cannot fail
    is read as evidence that it can.

    So the bound is now the negation of each repair, checked by running the
    repairs through the same predicate:

    * a ``sorted(...)`` fix makes the constant order the SORTED one;
    * an input-order-preserving fix makes the order distinct for all 24.

    ⚠️ **AND THE DEFECT IS WORSE THAN THIS TEST USED TO SAY.** Its old docstring
    claimed the output order "carries no information from its inputs" and that
    "reversing the input order changes nothing". That is true at
    ``PYTHONHASHSEED=0`` and **false at other seeds**: measured at
    ``PYTHONHASHSEED=12345`` the same four names yield **two** different output
    orders over the 24 permutations, because a small set's iteration order stops
    being insertion-independent once two keys collide on a slot. So the order is
    a function of the hash seed AND, at some seeds, of the input order — and at
    12345 ``preserved`` is **0**, which the old one-sided bound would also have
    passed. The seat handed out at an exact tie moves with both.

    That is why this pins the seed rather than asserting across whatever seed it
    inherits: the claim is only well defined at a fixed one. ``run_all.py``
    re-execs the suite under ``PYTHONHASHSEED=0`` via ``montecarlo.fix_hash_seed``
    before anything is imported, so under the suite this always runs.
    """
    if os.environ.get("PYTHONHASHSEED") != "0":
        skip(f"PYTHONHASHSEED is {os.environ.get('PYTHONHASHSEED')!r}, not '0'. "
             f"Set iteration order — the whole subject of this test — is a "
             f"function of it, and at some seeds this fixture produces two "
             f"output orders rather than one. Run under tests/run_all.py, "
             f"which re-execs under a pinned seed.")

    names = ["AAA", "BBB", "BIG1", "BIG2"]
    votes = {"AAA": 49, "BBB": 49, "BIG1": 101, "BIG2": 101}
    in_sorted_order = tuple(sorted(names))

    distinct, preserved, n = _output_orders(eligible_parties, names, votes)

    assert len(distinct) < n, (
        f"eligible_parties produced a different output order for every one of "
        f"the {n} input permutations, so its output order now IS derived from "
        f"its inputs. That is what this repository wants — the seat handed out "
        f"at an exact tie would follow the caller's ordering rather than a "
        f"string hash. Delete this characterisation and "
        f"`test_largest_remainder_is_decided_by_dict_order_at_an_exact_tie` "
        f"and assert the invariant: one seat vector over every ordering.")
    assert distinct != {in_sorted_order}, (
        f"eligible_parties now hands the allocator a SORTED dict "
        f"({in_sorted_order}), so the tie-break is no longer decided by a "
        f"string hash. The defect is fixed. Replace this and the tie-break "
        f"test above with the invariant, and re-point the three sibling "
        f"controls listed in this test's module docstring.")

    # ⛔ CAN THE BOUND SEE A REPAIR? Both plausible fixes, through the SAME
    #    predicate. If either got past it, everything above is decoration.
    def sorted_fix(ward, pr):
        return {p: ward.get(p, 0) + pr.get(p, 0)
                for p in sorted(set(ward) | set(pr)) if pr.get(p, 0) > 0}

    def input_order_fix(ward, pr):
        keys = list(ward) + [p for p in pr if p not in ward]
        return {p: ward.get(p, 0) + pr.get(p, 0)
                for p in keys if pr.get(p, 0) > 0}

    fixed_distinct, fixed_preserved, _ = _output_orders(sorted_fix, names, votes)
    assert fixed_distinct == {in_sorted_order}, fixed_distinct
    assert fixed_preserved == preserved == 1, (
        f"the OLD bound compared `preserved` ({preserved}) against {n}, and a "
        f"sorted repair gives {fixed_preserved}. If these two ever differ, say "
        f"so — the whole reason this test was rewritten is that they do not.")

    kept_distinct, kept_preserved, _ = _output_orders(input_order_fix, names,
                                                      votes)
    assert len(kept_distinct) == n and kept_preserved == n, (
        f"an input-order-preserving `eligible_parties` produced "
        f"{len(kept_distinct)} distinct orders over {n} permutations, so the "
        f"`len(distinct) < n` bound above could not see that repair either.")


# --------------------------------------------------------------------------
# the integration test — the same predicates, against a REAL trace
# --------------------------------------------------------------------------

TRACE_DRAWS = 40
_TRACE: dict = {}


def real_trace():
    """Run the model once, at 40 draws, and return ``(payloads, ModelRun)``.

    Generated rather than discovered, deliberately. A test whose premise is a
    trace somebody left on disk expires silently the first time nobody leaves
    one, and this repository has already shipped a test whose premise was a
    passing state of the tree. ``run_model`` READS the processed directory and
    never writes to it — only ``main`` publishes — so this is safe against the
    real inputs and writes only into a temporary directory.

    Skips loudly, with the reason, when the inputs are not on disk.
    """
    if _TRACE:
        return _TRACE["payloads"], _TRACE["run"]
    processed = ROOT / "data" / "processed" / "joburg" / "2021"
    spec = ROOT / "data" / "processed" / "pools_2021.json"
    for path in (processed / "turnout.csv", spec):
        if not path.exists():
            skip(f"no realisation trace can be generated: {path} is not on "
                 f"disk, so the model cannot run. This test is not weakened "
                 f"to compensate — it does not run at all.")
    city = cityconfig.use("joburg")
    target = cityconfig.use_target("2021")
    M.apply_city(city)
    scenario = M.load_scenario(Namespace(
        config=None, set=[f"draws={TRACE_DRAWS}", "seed=20260913"],
        counterfactual=False, draws=TRACE_DRAWS, seed=20260913))

    # THE TIE PROBE, installed around the REAL allocator for the duration of
    # this one run. `combined` is a per-draw local of `run_model` and reaches
    # no stage payload, so a tie can be counted here or nowhere — and counting
    # it from a reconstruction of the vote totals would be measuring the
    # reconstruction. The wrapper delegates and changes no number.
    ties: list[tuple] = []
    calls = [0]
    original = M.allocate

    def probe(combined, total_seats=270, independent_wards=0,
              no_pr_list_wards=0):
        calls[0] += 1
        hit = tie_at_the_cut(combined, total_seats, independent_wards,
                             no_pr_list_wards)
        if hit:
            ties.append(hit)
        return original(combined, total_seats=total_seats,
                        independent_wards=independent_wards,
                        no_pr_list_wards=no_pr_list_wards)

    M.allocate = probe
    try:
        with tempfile.TemporaryDirectory() as tmp:
            run = M.run_model(target, scenario,
                              ROOT / "data" / "raw" / "elections", processed,
                              run_dir=Path(tmp), trace_detail=True,
                              verbose=False)
            payloads = {}
            for name in ("40_draws", "41_guards", "42_pr_share_draws",
                         "43_ward_share_draws", "44_seat_draws",
                         "45_delivered", "_index"):
                with (Path(tmp) / f"{name}.json").open(encoding="utf-8") as fh:
                    payloads[name] = json.load(fh)
    finally:
        # `run_all` reuses worker processes across modules, so a patch left
        # installed would follow this module into somebody else's.
        M.allocate = original
    _TRACE.update(payloads=payloads, run=run, ties=ties, allocations=calls[0])
    return payloads, run


def test_the_realisation_segment_emits_every_stage_it_claims_to():
    payloads, _ = real_trace()
    written = set(payloads["_index"]["written"])
    segment = {"40_draws", "41_guards", "42_pr_share_draws",
               "43_ward_share_draws", "44_seat_draws", "45_delivered"}
    assert segment <= written, (
        f"the trace index does not list {sorted(segment - written)}. A stage "
        f"that wrote a `(FAILED: ...)` entry is listed here with the reason; "
        f"one that is absent never ran.")
    assert not [w for w in written if "FAILED" in w], written


def test_the_unlabelled_arrays_are_readable_at_all():
    """``universe`` sorted is the ONLY thing labelling 42 and 43. Assert it.

    Nothing else in the repository does. `Trace.put` dumps `40_draws` with
    `sort_keys=True`, so its party order is alphabetical; the arrays' columns
    are in `universe` order; and the two agree only because
    ``universe = sorted(...)``. Neither half is obliged to the other by
    anything but this test.
    """
    _, run = real_trace()
    assert run.universe == sorted(run.universe), (
        "`universe` is no longer sorted, so 42_pr_share_draws and "
        "43_ward_share_draws — which carry no party names at all — can no "
        "longer be read against 40_draws' alphabetical keys. Every band now "
        "belongs to a different party and nothing else would say so.")
    assert len(run.universe) == len(set(run.universe))


def test_a_real_trace_passes_every_predicate_in_this_file():
    """The predicates and the model must agree about the shape of the stages.

    This is what stops the constructed payloads above from drifting into a
    private dialect: every one of them is checked here against what
    ``run_model`` actually writes, with the same functions.
    """
    payloads, run = real_trace()
    draws = len(payloads["44_seat_draws"])
    universe = run.universe
    council = int(run.target.council)
    rule = run.scenario["overhang_rule"]

    complaints: list[str] = []
    complaints += faults_in_share_matrix(
        payloads["42_pr_share_draws"], name="42_pr_share_draws", draws=draws,
        parties=len(universe))
    complaints += faults_in_share_matrix(
        payloads["43_ward_share_draws"], name="43_ward_share_draws",
        draws=draws, parties=len(universe))
    complaints += faults_in_draws_summary(payloads["40_draws"], draws=draws,
                                          universe=universe)
    complaints += faults_in_seat_draws(payloads["44_seat_draws"],
                                       council=council, draws=draws,
                                       universe=universe, rule=rule)
    complaints += faults_between_summary_and_detail(
        payloads["40_draws"], payloads["42_pr_share_draws"],
        payloads["43_ward_share_draws"], payloads["44_seat_draws"])
    complaints += faults_in_guards(payloads["41_guards"], draws=draws,
                                   universe=universe)
    complaints += faults_in_delivery_log(payloads["45_delivered"])
    assert not complaints, "\n".join(complaints)


def test_the_guard_board_on_a_real_run_can_prove_it_looked():
    """Not "no guard fired" — "the guards were in a position to fire".

    Three counters are denominators rather than events: `bounds_checked` is
    incremented once per draw, `ipf_balances` once per shocked draw and
    `solve_calls` twice per draw. If any is zero, every rate on the board is
    0/0 and the silence of the event counters means nothing at all. This is the
    check `arrival_reconciliation` did not have.
    """
    payloads, _ = real_trace()
    guards = payloads["41_guards"]
    draws = len(payloads["44_seat_draws"])
    assert guards["bounds_checked"] == draws, guards["bounds_checked"]
    assert guards["ipf_balances"] > 0, (
        "no IPF balance was attempted, so the level shock never reached the "
        "pools in any draw and every ipf_* counter below is vacuous")
    assert guards["solve_calls"] >= draws, guards["solve_calls"]
    drawn = set(payloads["40_draws"]["pr_mean"])
    assert set(guards["ipf_headroom"]) <= drawn, (
        f"ipf_headroom names parties that were never drawn: "
        f"{sorted(set(guards['ipf_headroom']) - drawn)[:6]}")
    scanned(guards["ipf_headroom"], of=drawn, low=0.5, high=1.0,
            what="parties with a pre-draw pool-capacity headroom",
            denominator="parties in the drawn universe")


def test_the_real_boards_counters_are_bounded_by_the_real_draws():
    """Each dict-valued counter against the denominator it is a fraction of."""
    payloads, _ = real_trace()
    guards = payloads["41_guards"]
    for counter, denom in GUARD_DENOMINATORS.items():
        for party, n in sorted(guards[counter].items()):
            assert n <= guards[denom], (counter, party, n, guards[denom])
    assert sum(guards["overhang_count"].values()) >= guards["excessive_draws"]


def test_the_real_seat_draws_fill_a_lawful_chamber():
    """And the fill is REPORTED, because `council - C - D` is lawful too."""
    payloads, run = real_trace()
    council = int(run.target.council)
    fill = chamber_fill(payloads["44_seat_draws"], council)
    assert fill, "no seat draw was recorded"
    assert max(fill) <= council, (
        f"the shipped rule {run.scenario['overhang_rule']!r} does not grow the "
        f"chamber, and a draw seats {max(fill)} of {council}: {fill}")
    assert all(n > council // 2 for n in fill), fill


def test_the_real_seat_mean_is_a_mean_and_the_marginal_median_is_not_a_council():
    """Both numbers, side by side, so neither can be mistaken for the other.

    The mean vector apportions to the chamber; the per-party median over draws
    does not and is not meant to. Storing one under the other's name is a
    defect this project has had twice, most recently this week.
    """
    payloads, run = real_trace()
    seat_draws = payloads["44_seat_draws"]
    parties = sorted(payloads["40_draws"]["seat_mean"])
    mean_total = sum(payloads["40_draws"]["seat_mean"].values())
    median_total = sum(statistics.median([s.get(p, 0) for s in seat_draws])
                       for p in parties)
    council = int(run.target.council)
    # THE MEAN OF THE FILLS, not the council: `council - C - D` is lawful, so
    # pinning this to 270 would fail correctly-modelled eThekwini 2011 (C = 1)
    # and 2016 (C = 4) the day either is drawn with independents in the
    # universe. What must hold is that the mean vector apportions to the
    # chamber the draws actually filled.
    fill = chamber_fill(seat_draws, council)
    want = sum(n * c for n, c in fill.items()) / len(seat_draws)
    assert abs(mean_total - want) < 1e-6, (
        f"40_draws.seat_mean sums to {mean_total} while the draws fill a mean "
        f"{want} seats; a mean of vectors cannot sum to something other than "
        f"the mean of their sums")
    assert mean_total <= council + 1e-9, (mean_total, council, fill)
    assert median_total <= mean_total, (median_total, mean_total)
    print(f"    seat totals: mean vector {mean_total:.1f}, marginal medians "
          f"{median_total:.0f}, chamber {council}")


def test_the_real_delivery_log_proves_something_was_actually_read():
    """A log of only `resolved` records has proved nothing. §1.68.

    `resolved` says this process HELD a value; `consulted` says a computation
    read it. The second is the delivery proof and the first was once reported
    as one — "that null was measured WITH THE GATE SHUT". So the population of
    `consulted` records is bounded from BELOW as well as above: too few and
    the log attests to nothing, all of them and the distinction has collapsed.
    """
    payloads, _ = real_trace()
    log = payloads["45_delivered"]
    consulted = [n for n, rec in log.items() if "consulted" in rec["kinds"]]
    scanned(consulted, of=log, low=0.05, high=0.95,
            what="reads recorded as `consulted` (a delivery proof)",
            denominator="all records in 45_delivered")
    assert absent_constants(log) == [], (
        f"45_delivered reports declared constant(s) that were not there to "
        f"read: {absent_constants(log)}. A renamed or deleted constant shows "
        f"up here as an absence rather than as silence; fix the declaration "
        f"or the name.")


def test_the_real_trace_names_a_tie_rate_rather_than_assuming_there_is_none():
    """How often is a seat decided by the key order, on a real city-year?

    The detector is proved on constructed input above; here it is pointed at
    the real thing. Two allocations happen per draw at most (one, plus one per
    `deduct` round), and the population it scanned is asserted so the answer
    "no ties" cannot come from having looked at nothing.

    MEASURED, joburg 2021, 400 draws, seed 12345: three allocations hit an
    exact tie at the cut (ATM/UNITED_CULTURAL_MOVEMENT twice at 3,409 combined
    votes, UIM/ALJAMAAH once at 4,371), and reversing the key order moved a
    seat in one draw of the four hundred. It is rare here and it is not rare
    everywhere: a sibling reference that gives identically-reached parties
    identical shares manufactures whole GROUPS of exact ties.
    """
    payloads, _ = real_trace()
    draws = len(payloads["44_seat_draws"])
    calls, ties = _TRACE["allocations"], _TRACE["ties"]
    # (0) IT SCANNED THE RIGHT THING. Every seat draw comes from at least one
    # `allocate`, and the `deduct` rule re-allocates once per fixed party, so
    # the call count is bounded below by the draws and above by a small
    # multiple of them. Outside that band the probe was not on the path the
    # seats came from, and "no ties found" would be a statement about nothing.
    scanned(calls, of=draws, low=1.0, high=6.0,
            what="allocate() calls the tie probe intercepted",
            denominator="seat draws in the trace")
    # REPORTED, NOT REFUSED. Whether two parties draw exactly equal vote totals
    # is a property of the draw, not a defect; what the repository should not
    # do is believe there are none without having looked.
    print(f"    tie_at_the_cut fired on {len(ties)} of {calls} real "
          f"allocations" + (f": {ties[:3]}" if ties else ""))


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
