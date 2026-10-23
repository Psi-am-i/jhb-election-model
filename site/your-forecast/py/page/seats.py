"""Seat allocation for a metro council, per Municipal Structures Act Schedule 1.

**This contradicts plan §0 and is the most important correction to the model's
target quantity.** §0 asserts that a party's total seat count is determined by
its citywide *PR ballot* share. It is not. The IEC's own "Seat Calculation
Detail" report states the formula:

    Q = (A / (B - C - D)) + 1, disregarding fractions

    A  total valid votes cast for all parties, WARD AND PR BALLOTS ADDED TOGETHER
    B  total seats available in the municipality (270 for CoJ)
    C  independent ward councillors elected
    D  ward councillor seats from parties with no PR list

Seats are then ``floor(votes / Q)`` per party, with the undistributed remainder
allocated by largest remainder.

So the seat-determining quantity is a party's share of the *combined* ward + PR
vote, and the ward ballot is roughly half of it. Ward-level modelling is
therefore not the secondary concern §0 describes -- it is half the target.

Two exclusions from A, both verified exactly against CoJ 2021:

* independents (they take seats out of the pool via C rather than earning an
  entitlement);
* parties that contested a ward but registered no PR list (their ward seats come
  out via D).

CoJ 2021 check: 1,846,189 combined valid votes - 11,904 independent
- 24 Sakhisizwe Convention - 1 African Covenant = 1,834,260 = A as published.

**Surpluses are whole votes, and an equal surplus goes to the higher vote.**
Schedule 1 item 13(2)(a) fills the undistributed seats by the highest surplus,
the votes left over after each party's whole quotas, and 13(2)(b) (16(4)(c) in
the excessive-seats re-allocation) gives an equal surplus to the party with
more valid votes. :func:`allocate` ranks on the integer surplus
``votes - floor(votes / quota) * quota`` and then on votes. Until 2026-10-09 it
ranked the float ``votes / quota - floor``, so float rounding could separate two
equal surpluses before the vote count was read (law summary D3,
``audits/2026-10-09-site-batch/law/SUMMARY.md``).

**Equal surplus and equal votes: a seeded lot.** The statute says nothing beyond
the higher vote. When parties equal on both straddle the last seat, the seats
falling to them go in the order :func:`lot_order` draws for the caller's key, a
hash of the run's identity and the allocation round with no party name in it
(:func:`lot_identity`; the key forms are in ``JUDGEMENT-CALLS.md`` §Q2 and §Q6).
A call that meets such a tie without a key raises rather than falling back to
input order, which is what decided ties before (a set's order, and so
``PYTHONHASHSEED``). Ward ties in the simulations use the same lot
(``prediction.top_party``), as Schedule 1 item 8(2) does for a real ward tie.

Standard library only: this module ships to the page under Pyodide and to the
seat Worker.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

INDEPENDENT = "INDEPENDENT"


def is_independent(party: str) -> bool:
    """An independent candidate: :data:`INDEPENDENT`, or ``IND``, the row the
    published result files merge every independent in a voting district into
    (``DATA-QUALITY.md`` item 12). The one test, read by
    :func:`outside_pool_seats` (C) and ``backtest.entrant_actual_for`` (an
    independent is never an arrival, ``ARRIVED_VS_NATIONAL``'s ``party != IND``).
    """
    return party in (INDEPENDENT, "IND")


class TieWithoutLot(ValueError):
    """An exact tie straddles the last seat and the call passed no lot key."""


def stable_entropy(text: str) -> int:
    """A stable 64-bit integer from a string: blake2b-64 of its UTF-8, big-endian.

    THE ONE DEFINITION of the project's string-to-entropy key. Two users: the
    PIT column key (``score._column_entropy`` delegates here, and its pinned
    value ``16408193524922255279`` for ``"ANC"`` is this function's) and the
    keyed draw streams (``montecarlo.DrawStreams``), whose every stream is
    seeded from the run identity, the stage and the entity through it.

    ⛔ **NOT** ``hash()``: Python salts string hashing per process, and
    ``montecarlo.fix_hash_seed`` runs only under ``__main__``, so an importing
    caller would get a different key per process (MODEL-LOG §1.145). Standard
    library only, because this module ships to Pyodide and the seat Worker.
    """
    return int.from_bytes(
        hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest(), "big")


def lot_identity(city: str, target: str, seed) -> str:
    """The run's identity for the lot: ``f"{city}|{target}|{seed}"``.

    No party enters it. Every key the lot reads is built from this by
    :func:`ward_key`, :func:`draw_key` and :func:`seat_key`, the one key
    scheme (``JUDGEMENT-CALLS.md`` §Q2 and §Q6), so a repeat of a run gives the
    same answer and a different seed may give a different one. Refuses a part
    that is ``None`` or empty: ``"None|2026|7"`` would be a key nobody chose.
    """
    parts = {"city": city, "target": target, "seed": seed}
    empty = [k for k, v in parts.items() if v is None or str(v) == ""]
    if empty:
        raise ValueError(f"the lot's identity lacks {empty}: a run's lot names "
                         f"its city, target and seed")
    return f"{city}|{target}|{seed}"


def _need(lot: str) -> str:
    if not isinstance(lot, str) or not lot:
        raise ValueError(f"lot {lot!r} is not a run identity "
                         f"(seats.lot_identity): no key can be built from it")
    return lot


def ward_key(lot: str, ward) -> str:
    """The key for a tied ward call: ``f"{lot}|ward|{ward}"``."""
    return f"{_need(lot)}|ward|{ward}"


def draw_key(lot: str, d: int) -> str:
    """The run identity of draw ``d``: ``f"{lot}|draw{d}"``. Seat keys inside
    that draw are :func:`seat_key` of it."""
    return f"{_need(lot)}|draw{d}"


def seat_key(lot: str, round_: int) -> str:
    """The key for an exact tie at the last seat in allocation round
    ``round_``: ``f"{lot}|seat|{round_}"``."""
    return f"{_need(lot)}|seat|{round_}"


def lot_order(tied, key: str) -> list[str]:
    """The tied codes in the order the lot draws them, for ``key``.

    The codes are numbered in string order (``sorted``), which only enumerates
    them; ticket ``i`` is ``sha256(f"{key}#{i}")`` and the codes are returned in
    the order of their tickets. Which number draws first is decided by the key,
    so over many keys each tied code comes first equally often, whatever the
    codes are. For one fixed key the answer is fixed, which is what makes a
    re-run reproduce it.
    """
    if not key:
        raise ValueError("the lot needs a key: a hash of the run's identity "
                         "and the event, never a party name")
    canon = sorted({str(p) for p in tied})
    tickets = [hashlib.sha256(f"{key}#{i}".encode("utf-8")).digest()
               for i in range(len(canon))]
    return [p for _, p in sorted(zip(tickets, canon))]


@dataclass
class Allocation:
    """The outcome of a seat calculation."""

    quota: int
    total_votes: int
    seats_available: int
    seats: dict[str, int] = field(default_factory=dict)
    round_one: dict[str, int] = field(default_factory=dict)
    #: ``surpluses[p] / quota``, for display; the ranking reads ``surpluses``.
    remainders: dict[str, float] = field(default_factory=dict)
    #: whole votes left after each party's whole quotas (item 13(2)(a))
    surpluses: dict[str, int] = field(default_factory=dict)
    #: every party in the order the undistributed seats are offered: surplus,
    #: then votes, then the lot for a tie straddling the last seat
    ranking: list[str] = field(default_factory=list)

    def top(self, n: int = 12) -> list[tuple[str, int]]:
        ranked = sorted(self.seats.items(), key=lambda kv: -kv[1])
        return [(party, count) for party, count in ranked[:n] if count]


def eligible_parties(
    ward_votes: dict[str, int], pr_votes: dict[str, int],
    unopposed_pr: dict[str, int] | None = None,
) -> dict[str, int]:
    """Return combined ward+PR votes for parties that count towards the quota.

    Excludes independents and any party with no PR list, both of which are
    handled through ``C`` and ``D`` rather than through the entitlement pool.

    ``unopposed_pr`` is ``{party: its PR votes in the wards its candidate won
    unopposed}``. Schedule 1 item 12(2) counts each of those votes twice for
    factor A, and item 13(1)(b) twice for the party's entitlement, so they are
    added once more to the party's combined votes; item 16(5) (as substituted
    by Act 3 of 2021) follows because the excessive-seats re-quota reads the
    same combined tally. A key outside
    the pool is ignored: an independent or a party with no list never enters
    it. No result file on disk has an unopposed ward, so every caller passes
    nothing today (``levels.unopposed_wards``).
    """
    extra = unopposed_pr or {}
    return {
        party: ward_votes.get(party, 0) + pr_votes.get(party, 0)
        + extra.get(party, 0)
        for party in set(ward_votes) | set(pr_votes)
        if party != INDEPENDENT and pr_votes.get(party, 0) > 0
    }


def outside_pool_wards(
    ward_wins: dict[str, int], combined: dict[str, int]
) -> tuple[int, int, dict[str, int]]:
    """Split ward wins into the entitlement pool and the C and D terms.

    Returns ``(independent_wards, no_pr_list_wards, pool_wins)``.

    Schedule 1 takes two kinds of ward seat out of the pool BEFORE the quota is
    struck, because the councillor leaves with the seat: independents (C) and
    the winners of wards contested by a party that registered no PR list (D).
    Everything else stays in and earns an entitlement.

    ONE DEFINITION, because there were about to be three. ``backtest`` computed
    this inline for the ground truth, ``benchmarks`` did not compute it at all,
    and ``montecarlo`` had no notion of C or D whatsoever — so the forecast
    allocated over the whole council while the record it is scored against
    allocated over ``council - C - D``. They agree at 22 of 24 real metro-years
    and differ at eThekwini 2011 (C=1) and 2016 (C=4), both of them scored.
    MODEL-LOG §1.163.

    ⚠️ ``IND`` is matched as well as :data:`INDEPENDENT` because the published
    result files merge every independent in a voting district into one row of
    that name; ``DATA-QUALITY.md`` item 12 has why that count is an upper bound
    and why the IEC's published C is preferred wherever a report exists.
    """
    outside = outside_pool_seats(ward_wins, combined)
    independent_wards = sum(n for p, n in outside.items()
                            if p in (INDEPENDENT, "IND"))
    no_pr_list_wards = sum(n for p, n in outside.items()
                           if p not in (INDEPENDENT, "IND"))
    pool_wins = {p: n for p, n in ward_wins.items() if p not in outside}
    return independent_wards, no_pr_list_wards, pool_wins


def outside_pool_seats(
    ward_wins: dict[str, int], combined: dict[str, int]
) -> dict[str, int]:
    """The ward seats that leave the pool, keyed by who holds them.

    THE ONE MEMBERSHIP TEST for C and D: an independent (``INDEPENDENT`` or the
    result files' merged ``IND``) or a party absent from ``combined`` — which
    :func:`eligible_parties` builds only from parties with list votes, so
    "absent" means a party that contested wards with no PR list. Used by
    :func:`outside_pool_wards` for the counts and by :func:`council_seats` for
    the seats themselves, so the two cannot disagree about who left.
    """
    return {p: n for p, n in ward_wins.items()
            if is_independent(p) or p not in combined}


def council_seats(
    pool_seats: dict[str, int], ward_wins: dict[str, int],
    combined: dict[str, int], council: int,
) -> dict[str, int]:
    """THE WHOLE CHAMBER: the pool's seats plus every seat that left the pool.

    Schedule 1 deducts C and D from the council before the quota is struck
    (:func:`allocate`), so an allocation returns ``council - C - D`` seats. The
    councillors behind C and D still sit in the council: each ward won by an
    independent or by a party with no PR list is that winner's seat, and only
    a ward seat (it has no list to draw on). This returns ``pool_seats`` with
    those seats added as their own entries, so a seat vector produced here
    always holds the full council:

        sum(pool seats) + sum(outside seats) == council

    and raises ``ValueError`` if it does not, or if a party is in both halves
    (it cannot be: the pool is ``combined`` and the outside set is everything
    not in it). ``council`` is the size the overhang rule returned (270 under
    ``deduct`` and ``cap``; grown under ``expand`` and ``level``).

    One definition for every per-draw seat vector: ``montecarlo.run_model``'s
    ``seat_draws``, ``prediction.seats_of`` (the reader's council) and
    ``benchmarks.council_from_shares`` (the naive baselines). MODEL-LOG §1.308.
    """
    outside = {p: n for p, n in outside_pool_seats(ward_wins, combined).items()
               if n > 0}
    both = sorted(p for p in outside if pool_seats.get(p, 0))
    if both:
        raise ValueError(f"{both} hold pool seats AND ward seats outside the "
                         f"pool; the pool is `combined` and the outside set is "
                         f"everything not in it, so the inputs disagree")
    seats = {**pool_seats, **outside}
    total = sum(seats.values())
    if total != council:
        raise ValueError(
            f"the chamber does not add up: {sum(pool_seats.values())} pool "
            f"seats + {sum(outside.values())} ward seats outside the pool "
            f"({outside}) = {total}, council {council}. The pool must have been "
            f"allocated over council - C - D (seats.allocate), with C and D "
            f"from seats.outside_pool_wards on these same ward wins.")
    return seats


def allocate(
    combined: dict[str, int],
    total_seats: int = 270,
    independent_wards: int = 0,
    no_pr_list_wards: int = 0,
    *,
    lot: str | None = None,
) -> Allocation:
    """Allocate council seats by the Schedule 1 quota-and-highest-surplus method.

    Undistributed seats go by the integer surplus, an equal surplus to the
    higher vote (items 13(2)(a),(b); module docstring). Parties equal on both
    that straddle the last seat are ordered by :func:`lot_order` under ``lot``;
    with ``lot=None`` such a tie raises ``ValueError`` naming the codes. An
    allocation with no tie at the cut never reads ``lot``.
    """
    available = total_seats - independent_wards - no_pr_list_wards
    if available <= 0:
        raise ValueError(f"no seats left to allocate ({available})")

    total_votes = sum(combined.values())
    # "disregarding fractions" -- floor the division, then add one.
    quota = total_votes // available + 1

    round_one = {party: votes // quota for party, votes in combined.items()}
    surpluses = {party: votes - round_one[party] * quota
                 for party, votes in combined.items()}
    remainders = {party: surpluses[party] / quota for party in combined}

    seats = dict(round_one)
    shortfall = available - sum(round_one.values())
    ranked = sorted(combined, key=lambda p: (-surpluses[p], -combined[p]))
    if shortfall > len(ranked):
        raise ValueError(
            f"largest-remainder shortfall {shortfall} exceeds party count "
            f"{len(ranked)} — vote totals too small for this council size")
    if 0 < shortfall < len(ranked):
        edge = ranked[shortfall - 1]
        level = (surpluses[edge], combined[edge])
        group = [p for p in ranked if (surpluses[p], combined[p]) == level]
        first = ranked.index(group[0])          # the group is contiguous
        if first + len(group) > shortfall:      # it straddles the cut
            if lot is None:
                raise TieWithoutLot(
                    f"an exact tie straddles the last seat: {sorted(group)} are "
                    f"equal on surplus ({level[0]}) and on votes ({level[1]}), "
                    f"and {shortfall - first} seat(s) fall to these "
                    f"{len(group)} parties. Schedule 1 item 13(2)(b) gives an equal "
                    f"surplus to the higher vote and says nothing beyond it; "
                    f"this project draws a seeded lot (seats.lot_order), and "
                    f"this call passed no key.")
            ranked = (ranked[:first] + lot_order(group, lot)
                      + ranked[first + len(group):])
    for party in ranked[:shortfall]:
        seats[party] += 1

    return Allocation(
        quota=quota,
        total_votes=total_votes,
        seats_available=available,
        seats=seats,
        round_one=round_one,
        remainders=remainders,
        surpluses=surpluses,
        ranking=list(ranked),
    )


def pr_seats(allocation: Allocation, ward_wins: dict[str, int]) -> dict[str, int]:
    """Split each party's entitlement into ward and PR councillors.

    Ward seats are deducted from the total entitlement -- winning a ward does not
    add a seat, it decides which entitled seat is filled by a ward councillor
    (plan §0). A negative result is overhang: the party won more wards than its
    entitlement and keeps them. Under the law (item 16, ``overhang_rule =
    "deduct"``) the council stays at ``total_seats`` and the other parties share
    the list seats that remain; the council grows only under the labelled
    ``expand`` and ``level`` counterfactuals. (Until 2026-10-23 this said the
    surplus pushes the council above ``total_seats``.)
    """
    return {
        party: allocation.seats.get(party, 0) - ward_wins.get(party, 0)
        for party in set(allocation.seats) | set(ward_wins)
    }


def overhang(allocation: Allocation, ward_wins: dict[str, int]) -> dict[str, int]:
    """Return the parties whose ward wins exceed their entitlement, and by how much."""
    return {
        party: -deficit
        for party, deficit in pr_seats(allocation, ward_wins).items()
        if deficit < 0
    }
