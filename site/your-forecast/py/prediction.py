"""Our prediction: the forecast reduced to one complete result, by rule A.

The forecast is many simulations; a prediction is one result that could
happen, with what an election produces: a winner in every ward, a vote for
every party on the ward ballot and on the list ballot, and the seats the law
gives from those (STYLE.md rule 11). Rule A, in three sentences a reader can
check:

1. Each ward goes to the party that wins it in the most simulations.
2. Each party gets its mean ward-ballot vote and its mean list-ballot vote
   across the simulations, in whole votes.
3. Seats follow from those wards and votes by the seat law
   (:func:`seats_of`: ``seats.eligible_parties``, ``seats.outside_pool_wards``
   and ``montecarlo.allocate_with_overhang`` under the statutory rule).

**One definition.** The build (``build_make.start_state``, through
``score_forecasts.model_forecast``), the page's hand-off
(``interactive/pyboot/page.py``'s ``handoff``, with the reader's weights) and
the page's ward map (``page._ward_calls``) all call this module, and so do
the ward calls made from a ward's counts or probabilities rather than the draws
(:func:`top_party`: ``scenarios.modal_winners``, ``diagnose``,
``score.score_wards``). ``tests/test_prediction_rule.py`` scans every module
for any other modal or mean reduction over the draws' ward winners or votes,
following renamed copies of them, and fails on one it was not told about; its
``EXEMPT`` table lists, with reasons, the sites that are not a second rule A.

**Ties.** A ward whose top count is shared goes to the party the seeded lot
draws (``seats.lot_order``) under the ward's key ``seats.ward_key(lot, ward)``,
where ``lot`` is the run's identity (``seats.lot_identity``: city, target,
seed; no party name). Schedule 1 item 8(2) settles a real ward tie by lot; this
is the same rule for a tie in the count of simulations. With unit weights the
counts are integers and a tie is exact; with other weights a tie is exact
equality of two weighted sums computed by the same arithmetic, so it is
deterministic. A tie with no key raises :class:`RuleAError`. An exact tie at
the last seat in :func:`seats_of` is drawn the same way under
``seats.seat_key(lot, round)``. JUDGEMENT-CALLS §Q2, §Q6. (Until 2026-10-09 a ward
tie went to the code first in string order, which favoured the same names at
every tie.)

**Rounding.** A mean is rounded to a whole vote, half to even. With unit
weights (none given, or every weight equal, which is what the page's untouched
setting passes: ``reweight.uniform``) the mean is computed in exact integer
arithmetic, so the build and the untouched hand-off take one path by
construction. Other weights: the weighted mean in floating point, then
Python's ``round`` (also half to even). JUDGEMENT-CALLS §Q3.

**No party is summed or dropped.** Every column of the draws' vote blocks
enters the prediction under its own code, zero included, and the seat law
decides who is in the pool. "Others" is a display grouping only; summing small
parties into one column before the law would seat them differently
(JUDGEMENT-CALLS §Q4, ``test_no_party_is_summed_and_summing_would_seat_differently``).

The rule is the owner's choice of 2026-10-08 (JUDGEMENT-CALLS §Q1), with the
backtest of MODEL-LOG §1.290 as its evidence. It replaced the seat-first start
(``start_rule.py``, retired).

Imports: ``numpy`` only at module level. This file ships to the
page under Pyodide (``interactive/tools/sync_py.mjs`` PAGE_FILES) and, through
``reader_seats``, to the seat Worker; :func:`seats_of` imports the seat law
when it is called, so the page's ward map does not load the model.
:func:`top_party` imports ``seats`` (standard library only) when a tie needs
the lot.
"""
from __future__ import annotations

import numpy as np


class RuleAError(ValueError):
    """The draws cannot give a prediction by rule A; the message says why."""


def _weights(weights, n: int):
    """``None`` for unit weights (none given, or all equal); else the checked array."""
    if weights is None:
        return None
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1 or w.shape[0] != n:
        raise RuleAError(f"weights have shape {w.shape}, not ({n},): one per draw")
    if not np.all(np.isfinite(w)):
        raise RuleAError("weights are not all finite")
    if np.any(w < 0):
        raise RuleAError("a weight is negative")
    if not w.sum() > 0:
        raise RuleAError("the weights sum to zero: no draw counts")
    if np.all(w == w[0]):
        return None
    return w


def _round_half_even(numerator: int, denominator: int) -> int:
    """``numerator / denominator`` to the nearest whole number, half to even, in integers."""
    q, r = divmod(numerator, denominator)
    twice = 2 * r
    if twice > denominator or (twice == denominator and q % 2 == 1):
        q += 1
    return q


def top_party(scores, *, lot: str | None = None) -> str:
    """The party with the largest score; a tie drawn by the seeded lot.

    ``scores`` is ``{party: count, weight or probability}``. ``lot`` is the
    event's own key (a ward's is ``seats.ward_key(run_lot, ward)``; module
    docstring). The one tie rule for every ward call: :func:`ward_calls` uses
    it, and so do the callers that hold a ward's counts or probabilities rather
    than the draws (``scenarios.modal_winners``, ``score.score_wards``,
    ``diagnose``, ``montecarlo.main``'s winner column). A tie with
    ``lot=None`` raises :class:`RuleAError`; an untied call never reads ``lot``.
    """
    if not scores:
        raise RuleAError("no party to call: the scores are empty")
    top = max(scores.values())
    tied = [str(p) for p, v in scores.items() if v == top]
    if len(tied) == 1:
        return tied[0]
    if not lot:
        raise RuleAError(f"a tie at the top between {sorted(tied)} and no lot "
                         f"key to draw it (JUDGEMENT-CALLS §Q2)")
    import seats
    return seats.lot_order(tied, lot)[0]


def _ward_key(lot: str, ward) -> str:
    """``seats.ward_key``, imported when a lot is given (module docstring)."""
    import seats
    return seats.ward_key(lot, ward)


def ward_calls(ward_winners, ward_parties, wards, weights=None, *,
               lot: str | None = None) -> dict[str, str]:
    """``{ward: party}``: each ward's party with the most (weighted) wins.

    ``ward_winners`` is ``(draws, wards)`` of indices into ``ward_parties``,
    columns in ``wards`` order. A tie is drawn by the seeded lot under
    ``seats.ward_key(lot, ward)``, ``lot`` being the run's identity (module
    docstring); with ``lot=None`` a tie raises.
    """
    winners = np.asarray(ward_winners)
    parties = [str(p) for p in ward_parties]
    wards = [str(x) for x in wards]
    if winners.ndim != 2 or winners.shape[1] != len(wards):
        raise RuleAError(f"ward winners have shape {winners.shape}, not "
                         f"(draws, {len(wards)})")
    if winners.shape[0] == 0:
        raise RuleAError("there are no draws")
    if winners.dtype.kind not in "iu":
        raise RuleAError(f"ward winners are {winners.dtype}, not party indices")
    if winners.size and (winners.min() < 0 or winners.max() >= len(parties)):
        raise RuleAError(f"a ward winner indexes outside the {len(parties)} "
                         f"ward parties")
    w = _weights(weights, winners.shape[0])
    out = {}
    for j, ward in enumerate(wards):
        counts = np.bincount(winners[:, j].astype(np.int64), weights=w,
                             minlength=len(parties))
        out[ward] = top_party(dict(zip(parties, counts.tolist())),
                              lot=None if lot is None else _ward_key(lot, ward))
    return out


def mean_votes(votes, columns, weights=None, *, name: str = "votes") -> dict[str, int]:
    """``{party: whole votes}``: each column's mean over the draws (module docstring).

    ``votes`` is ``(draws, len(columns))`` of non-negative integers. Every
    column is kept, zero included, in ``columns`` order.
    """
    if votes is None:
        raise RuleAError(f"the draws carry no {name} block")
    v = np.asarray(votes)
    columns = [str(c) for c in columns]
    if v.ndim != 2:
        raise RuleAError(f"{name} is {v.ndim}-dimensional, not (draws, parties)")
    if v.shape[1] != len(columns):
        raise RuleAError(f"{name} has {v.shape[1]} columns for {len(columns)} parties")
    if v.shape[0] == 0:
        raise RuleAError(f"{name} has no draws")
    if v.dtype.kind not in "iu":
        raise RuleAError(f"{name} is {v.dtype}, not whole votes")
    if v.size and v.min() < 0:
        raise RuleAError(f"{name} holds a negative vote")
    n = v.shape[0]
    w = _weights(weights, n)
    if w is None:
        # int64 accumulates exactly: a column of 5,000 draws of a million votes
        # is 5e9, far inside it, where a uint32 accumulator would wrap
        sums = v.astype(np.int64).sum(axis=0)
        return {c: _round_half_even(int(s), n) for c, s in zip(columns, sums)}
    total = float(w.sum())
    return {c: int(round(float(w @ v[:, j].astype(float)) / total))
            for j, c in enumerate(columns)}


def rule_a(ward_winners, ward_parties, wards, ward_votes, list_votes, columns,
           *, weights=None, ward_ids=None, lot: str | None = None) -> dict:
    """The prediction object: rule A on the draws (module docstring).

    ``lot`` is the run's identity (``seats.lot_identity``); a tied ward is
    drawn under ``seats.ward_key(lot, ward)``.

    Returns ``{"ward_calls": [party, ...] in ward_ids order (default: wards),
    "ward_votes": {party: int}, "list_votes": {party: int}}``, every column of
    ``columns`` in both vote dicts. Seats are not in it: they are derived
    (:func:`seats_of`), never stored as an input.

    Refuses (:class:`RuleAError`, saying why): a missing vote block; a block
    that fails :func:`mean_votes`' checks; two blocks equal in every cell (one
    ballot is a copy of the other); ``ward_ids`` that are not the wards
    reordered; bad weights; a ward called for a party the vote blocks do not
    carry.
    """
    if ward_votes is None:
        raise RuleAError("the draws carry no ward_vote block")
    if list_votes is None:
        raise RuleAError("the draws carry no list_vote block")
    wv, lv = np.asarray(ward_votes), np.asarray(list_votes)
    if wv is lv or (wv.shape == lv.shape and np.array_equal(wv, lv)):
        raise RuleAError("the ward_vote and list_vote blocks are equal in every "
                         "cell: one ballot is a copy of the other")
    wards = [str(x) for x in wards]
    order = wards if ward_ids is None else [str(x) for x in ward_ids]
    if sorted(order) != sorted(wards) or len(set(order)) != len(order):
        raise RuleAError("ward_ids are not the draws' wards reordered")
    calls = ward_calls(ward_winners, ward_parties, wards, weights, lot=lot)
    columns = [str(c) for c in columns]
    absent = sorted({p for p in calls.values() if p not in columns})
    if absent:
        raise RuleAError(f"wards are called for {absent}, which the vote blocks "
                         f"do not carry")
    return {"ward_calls": [calls[x] for x in order],
            "ward_votes": mean_votes(wv, columns, weights, name="ward_vote"),
            "list_votes": mean_votes(lv, columns, weights, name="list_vote")}


def seats_of(prediction: dict, council: int, *, order=None,
             lot: str | None = None) -> dict:
    """The council the seat law gives a prediction: the one composition of
    the seat law for a prediction or a reader's forecast (``reader_seats``
    calls it). Two others exist and are not predictions: ``run_model``'s draw
    loop, and ``benchmarks.council_from_shares``, which seats the naive
    baselines the backtest compares the model with.

    ``prediction`` carries ``ward_calls`` (one party per ward), ``ward_votes``
    and ``list_votes`` (``{party: whole votes}``; ``ward_votes`` may be empty).
    ``seats.eligible_parties`` decides the pool, which is then re-keyed in
    ``order`` (default: the key order of ``list_votes``); the order fixes how
    the pool is listed and decides nothing, because an exact tie at the last
    seat is drawn by the seeded lot under ``seats.seat_key(lot, round)``
    (``lot`` is the run's identity; ``None`` raises on such a tie);
    ``seats.outside_pool_wards``
    takes out the C and D wards; ``montecarlo.allocate_with_overhang`` under
    ``montecarlo.STATUTORY_VALUES["overhang_rule"]`` strikes the quota and
    applies item 16, with ``montecarlo.COUNCIL`` set to ``council`` for the
    call and restored afterwards.

    Returns ``{"seats": {party: {"ward", "pr", "total"}}`` (every party with a
    seat, outside-pool ward winners included), ``"council"``, ``"majority"``,
    ``"excessive"``, ``"excessive_fired"``, ``"independent_wards"``,
    ``"no_pr_list_wards"``, ``"pool"`` (the pool's codes in order)}. The
    law's ``ValueError`` and ``RuntimeError`` propagate unchanged.
    """
    import montecarlo as M
    from seats import council_seats, eligible_parties, outside_pool_wards

    ward_votes = dict(prediction.get("ward_votes") or {})
    list_votes = dict(prediction["list_votes"])
    pooled = eligible_parties(ward_votes, list_votes)
    keys = list(list_votes) if order is None else list(order)
    combined = {p: pooled[p] for p in keys if p in pooled}
    for p in sorted(set(pooled) - set(combined)):
        combined[p] = pooled[p]

    wins: dict[str, int] = {}
    for party in prediction["ward_calls"]:
        wins[party] = wins.get(party, 0) + 1
    c_wards, d_wards, pool_wins = outside_pool_wards(dict(wins), combined)

    previous = M.COUNCIL
    try:
        # `allocate_with_overhang` reads the council from this module global,
        # as `benchmarks.council_from_shares` sets it; put back afterwards.
        M.COUNCIL = int(council)
        seats, size, majority, over = M.allocate_with_overhang(
            combined, pool_wins, M.STATUTORY_VALUES["overhang_rule"],
            independent_wards=c_wards, no_pr_list_wards=d_wards, lot=lot)
    finally:
        M.COUNCIL = previous

    # The whole chamber: the pool plus every ward seat that left it (C, D),
    # one definition with the simulation's draws (`seats.council_seats`).
    chamber = council_seats(seats, wins, combined, size)
    out: dict[str, dict[str, int]] = {}
    for party in list(seats) + [p for p in chamber if p not in seats]:
        ward = wins.get(party, 0)
        total = chamber.get(party, 0)
        if total:
            out[party] = {"ward": ward, "pr": total - ward, "total": total}
    return {"seats": out, "council": size, "majority": majority,
            "excessive": dict(over), "excessive_fired": bool(over),
            "independent_wards": c_wards, "no_pr_list_wards": d_wards,
            "pool": list(combined)}

