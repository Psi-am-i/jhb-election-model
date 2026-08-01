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
"""

from __future__ import annotations

from dataclasses import dataclass, field

INDEPENDENT = "INDEPENDENT"


@dataclass
class Allocation:
    """The outcome of a seat calculation."""

    quota: int
    total_votes: int
    seats_available: int
    seats: dict[str, int] = field(default_factory=dict)
    round_one: dict[str, int] = field(default_factory=dict)
    remainders: dict[str, float] = field(default_factory=dict)

    def top(self, n: int = 12) -> list[tuple[str, int]]:
        ranked = sorted(self.seats.items(), key=lambda kv: -kv[1])
        return [(party, count) for party, count in ranked[:n] if count]


def eligible_parties(
    ward_votes: dict[str, int], pr_votes: dict[str, int]
) -> dict[str, int]:
    """Return combined ward+PR votes for parties that count towards the quota.

    Excludes independents and any party with no PR list, both of which are
    handled through ``C`` and ``D`` rather than through the entitlement pool.
    """
    return {
        party: ward_votes.get(party, 0) + pr_votes.get(party, 0)
        for party in set(ward_votes) | set(pr_votes)
        if party != INDEPENDENT and pr_votes.get(party, 0) > 0
    }


def allocate(
    combined: dict[str, int],
    total_seats: int = 270,
    independent_wards: int = 0,
    no_pr_list_wards: int = 0,
) -> Allocation:
    """Allocate council seats by the Schedule 1 quota-and-largest-remainder method."""
    available = total_seats - independent_wards - no_pr_list_wards
    if available <= 0:
        raise ValueError(f"no seats left to allocate ({available})")

    total_votes = sum(combined.values())
    # "disregarding fractions" -- floor the division, then add one.
    quota = total_votes // available + 1

    round_one = {party: votes // quota for party, votes in combined.items()}
    remainders = {
        party: votes / quota - round_one[party] for party, votes in combined.items()
    }

    seats = dict(round_one)
    shortfall = available - sum(round_one.values())
    # Largest remainder, breaking ties on the larger vote total.
    ranked = sorted(remainders, key=lambda p: (-remainders[p], -combined[p]))
    for party in ranked[:shortfall]:
        seats[party] += 1

    return Allocation(
        quota=quota,
        total_votes=total_votes,
        seats_available=available,
        seats=seats,
        round_one=round_one,
        remainders=remainders,
    )


def pr_seats(allocation: Allocation, ward_wins: dict[str, int]) -> dict[str, int]:
    """Split each party's entitlement into ward and PR councillors.

    Ward seats are deducted from the total entitlement -- winning a ward does not
    add a seat, it decides which entitled seat is filled by a ward councillor
    (plan §0). A negative result is overhang: the party won more wards than its
    entitlement and keeps them, which pushes the council above ``total_seats``.
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
