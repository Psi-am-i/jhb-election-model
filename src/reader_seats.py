"""A reader's own forecast, turned into council seats by the statute alone.

DESIGN-decided §9 (owner, 2026-09-28). A reader starts from a model state and
then makes two edits only: the citywide PR vote shares, and the winner of any
ward. Seats then follow from Municipal Structures Act Schedule 1 **as this
project implements it**, and from nothing else: no model level, band, pool or
geography constrains the reader. This module is that arithmetic, written to run
in the browser under Pyodide.

**It calls the project's seat law; it does not restate it.**

* :func:`seats.eligible_parties` decides who earns an entitlement (the pool
  membership test the ground truth uses);
* :func:`seats.outside_pool_wards` takes the C and D ward seats out of the pool
  before the quota is struck;
* :func:`montecarlo.allocate_with_overhang` strikes the quota
  (:func:`seats.allocate`) and applies item 16, the excessive-seats clause,
  under the rule in :data:`montecarlo.STATUTORY_VALUES` — the rule the model
  itself is refused permission to leave without ``--counterfactual``.

So the one thing that differs from a model draw is the INPUT, and the input
carries one stated assumption (JUDGEMENT-CALLS.md, "a reader's PR shares
stand for both ballots"):

    **The reader's PR shares stand for both ballots when sizing entitlements.**
    Schedule 1 sizes each party's entitlement from the COMBINED ward + PR vote
    (``seats.py``'s docstring; the plan's PR-only premise was wrong). A reader
    supplies one vote and a set of ward winners, not two ballots, so each
    party's combined vote is taken as ``share × total_votes``. Wards are taken
    as picked, and list seats fill each entitlement under item 16 exactly as the
    model's allocation does.

A model draw does not satisfy this assumption: its ward ballot differs from its
PR ballot party by party (the ward/PR ratios). Feeding a draw's PR-ballot share
here therefore does not reproduce that draw's seats at every draw; feeding its
COMBINED share with its combined total does, exactly
(``tests/test_reader_seats.py``).

**Inputs, and why each is required**

``pr_shares``
    ``{party: share}``, a distribution over the context's roster. A roster party
    that is absent is taken as zero — that is what absence from a distribution
    means. An unknown party is refused.
``ward_winners``
    ``{ward: party}`` for EVERY ward in the context. Missing and unknown wards
    are both refused; nothing is filled in.
``context``
    The city-year's facts, built at build time by :func:`context_for` (or
    :func:`context_from_run`) and shipped as a small JSON: ``city``,
    ``target``, ``council`` and ``wards`` from the city config, the roster
    ``parties``, and ``no_pr_list`` — the roster parties with no PR list,
    independents included. Nothing is read from disk at call time.
``total_votes``
    The combined valid vote the shares are scaled to. It is REQUIRED because
    shares alone do not fix seats: the quota is ``total // available + 1``
    ("disregarding fractions"), so the scale moves a party that sits on a
    remainder boundary. The page supplies it from the model state the reader
    started from. It is not defaulted to a typed number.

**What it refuses, rather than guessing:** a malformed context; a
``total_votes`` that is not a positive integer; shares that are negative, not
finite, or do not sum to one within ``tolerance``; unknown parties; missing or
unknown wards; a ward won by a party outside the roster; a ward won by a party
with a zero share that the context does not list as having no PR list (the
statute would route it out of the pool as a no-list party — a silent
reclassification); a positive share for a party the context says has no PR
list, or one that the statute's pool test excludes anyway, or one too small to
be a single vote at ``total_votes`` (its votes would vanish); and an allocation
the seat law itself cannot complete.

**Ties.** ``seats.allocate`` breaks an exact tie — equal remainder AND equal
votes — by the order of its input, where Schedule 1 says "by lot". This module
passes the pool in the order of ``pr_shares``, so a given input always gives the
same council; the caller owns that order. (A model draw's order comes from a
set and so from ``PYTHONHASHSEED``; see ``benchmarks.canonical_order``.)

**No party is special-cased** (DESIGN-decided §8). Which parties sit outside the
pool is a property of the roster in the context, not of this code.

**Pyodide.** Importing this module imports ``montecarlo`` and what it imports at
module level — ``cityconfig``, ``coalitions``, ``fold``, ``parties``,
``polling``, ``seats`` — all numpy and the standard library, with no file read
at import or at call. :func:`context_for` reads the city TOML and is build-time
only. The page therefore ships those modules from ``src/``; that is the cost of
item 16 living in ``montecarlo`` rather than in ``seats``.
"""

from __future__ import annotations

import math

import montecarlo as M
from seats import eligible_parties, outside_pool_wards

#: The assumption this arithmetic rests on, carried in every result so the page
#: cannot show seats without it.
ASSUMPTION = ("The reader's PR shares stand for both ballots when sizing each "
              "party's entitlement; wards are taken as picked; list seats fill "
              "entitlements under the excessive-seats clause.")


def context_for(city: str, target: str, parties, wards,
                no_pr_list=()) -> dict:
    """Build the call-time context for one city-year. BUILD TIME ONLY.

    Council size and ward count come from ``cities/<city>.toml`` through
    :meth:`cityconfig.City.structure_for`, never from a typed number, and the
    ward list must have exactly the configured count — a list from another
    delimitation is refused here rather than allocated.
    """
    import cityconfig  # reads a TOML: never at call time in the browser

    structure = cityconfig.load(city).structure_for(str(target))
    wards = [str(w) for w in wards]
    if len(wards) != int(structure["wards"]):
        raise ValueError(
            f"{city} {target}: {len(wards)} wards given, the city config says "
            f"{structure['wards']}")
    context = {
        "city": city,
        "target": str(target),
        "council": int(structure["council"]),
        "wards": wards,
        "parties": [str(p) for p in parties],
        "no_pr_list": [str(p) for p in no_pr_list],
    }
    problems = context_errors(context)
    if problems:
        raise ValueError("; ".join(problems))
    return context


def context_from_run(run, no_pr_list=()) -> dict:
    """The context for the city-year a :class:`montecarlo.ModelRun` forecast.

    The roster is the run's universe and the wards are the run's wards, so a
    reader edits exactly the parties and wards the model drew.
    """
    target = run.target
    return context_for(target.city.slug, str(target.year), run.universe,
                       run.wards, no_pr_list)


def context_errors(context) -> list[str]:
    """Everything wrong with a context, as sentences. Empty means usable."""
    if not isinstance(context, dict):
        return ["context is not a mapping"]
    errors = []
    for key in ("city", "target", "council", "wards", "parties", "no_pr_list"):
        if key not in context:
            errors.append(f"context has no {key!r}")
    if errors:
        return errors
    council, wards, parties = (context["council"], context["wards"],
                               context["parties"])
    if not isinstance(council, int) or isinstance(council, bool) or council <= 0:
        errors.append(f"council {council!r} is not a positive integer")
    if not wards:
        errors.append("the context lists no wards")
    if len(set(wards)) != len(wards):
        errors.append("the context lists a ward twice")
    if not parties:
        errors.append("the context lists no parties")
    if len(set(parties)) != len(parties):
        errors.append("the context lists a party twice")
    stray = sorted(set(context["no_pr_list"]) - set(parties))
    if stray:
        errors.append(f"no_pr_list names parties not on the roster: {stray}")
    if (isinstance(council, int) and not errors and len(wards) > council):
        errors.append(f"{len(wards)} wards cannot fit a council of {council}")
    return errors


def _share_errors(pr_shares, roster, no_list, tolerance) -> list[str]:
    if not isinstance(pr_shares, dict):
        return ["pr_shares is not a mapping of party to share"]
    errors = []
    unknown = sorted(str(p) for p in set(pr_shares) - set(roster))
    if unknown:
        errors.append(f"unknown parties in pr_shares: {unknown}")
    bad = []
    for party, share in pr_shares.items():
        if (isinstance(share, bool) or not isinstance(share, (int, float))
                or not math.isfinite(share) or share < 0):
            bad.append(party)
    if bad:
        errors.append(f"shares that are not finite non-negative numbers: "
                      f"{sorted(map(str, bad))}")
        return errors
    total = math.fsum(pr_shares.values())
    if abs(total - 1.0) > tolerance:
        errors.append(f"shares sum to {total!r}, not 1 (tolerance {tolerance})")
    listless = sorted(p for p in no_list if pr_shares.get(p, 0) > 0)
    if listless:
        errors.append(f"a PR share for parties the roster says have no PR "
                      f"list: {listless}")
    return errors


def _ward_errors(ward_winners, wards, roster, no_list, pr_shares) -> list[str]:
    if not isinstance(ward_winners, dict):
        return ["ward_winners is not a mapping of ward to party"]
    errors = []
    missing = [w for w in wards if w not in ward_winners]
    if missing:
        errors.append(f"{len(missing)} ward(s) have no winner: {missing[:10]}"
                      + (" …" if len(missing) > 10 else ""))
    unknown = sorted(str(w) for w in set(ward_winners) - set(wards))
    if unknown:
        errors.append(f"unknown wards: {unknown[:10]}"
                      + (" …" if len(unknown) > 10 else ""))
    strangers = sorted({str(p) for p in ward_winners.values()} - set(roster))
    if strangers:
        errors.append(f"wards won by parties not on the roster: {strangers}")
    voteless = sorted({p for p in ward_winners.values()
                       if p in roster and p not in no_list
                       and not pr_shares.get(p, 0) > 0})
    if voteless:
        errors.append(
            f"wards won by parties with a zero share: {voteless}. Under the "
            f"stated assumption a party's share is its vote on both ballots, so "
            f"a ward winner must have one — unless the roster lists it as "
            f"having no PR list")
    return errors


def reader_seats(pr_shares: dict, ward_winners: dict, context: dict,
                 total_votes: int, *, tolerance: float = 1e-9) -> dict:
    """Council seats for a reader's PR shares and ward picks, by the statute alone.

    Returns a dict:

    ``ok``
        False when anything was refused; ``errors`` then says what, and no
        seats are given.
    ``seats``
        ``{party: {"ward": n, "pr": n, "total": n}}`` for every party holding a
        seat, outside-pool ward winners (C and D) included, so the totals sum
        to ``council``.
    ``council``, ``majority``
        As :func:`montecarlo.allocate_with_overhang` returns them under the
        statutory rule.
    ``excessive``
        ``{party: excess}`` for each party item 16 fixed at its ward seats
        (0 for a party whose wins exactly equal its entitlement, which item
        16(1)'s "equal to or greater" includes). Empty when the clause did not
        fire; ``excessive_fired`` says the same as a bool.
    ``independent_wards``, ``no_pr_list_wards``
        The C and D terms.
    ``assumption``
        :data:`ASSUMPTION`, verbatim.
    """
    result = {"ok": False, "errors": [], "seats": {}, "council": None,
              "majority": None, "excessive": {}, "excessive_fired": False,
              "independent_wards": 0, "no_pr_list_wards": 0,
              "assumption": ASSUMPTION}

    errors = context_errors(context)
    if errors:
        result["errors"] = errors
        return result
    roster, wards = context["parties"], context["wards"]
    no_list = set(context["no_pr_list"])

    if (not isinstance(total_votes, int) or isinstance(total_votes, bool)
            or total_votes <= 0):
        errors.append(f"total_votes {total_votes!r} is not a positive integer")
    errors += _share_errors(pr_shares, roster, no_list, tolerance)
    if not errors:
        errors += _ward_errors(ward_winners, wards, roster, no_list, pr_shares)
    if errors:
        result["errors"] = errors
        return result

    # The combined vote, under the stated assumption, in the caller's order.
    votes = {p: int(round(s * total_votes)) for p, s in pr_shares.items() if s > 0}
    # Every vote goes in as a PR vote: the pool test is "has a PR vote", and
    # under the assumption a positive share IS one. Splitting it into two
    # halves would change nothing but the rounding.
    pooled = eligible_parties({}, votes)
    dropped = sorted(p for p in votes if p not in pooled)
    if dropped:
        result["errors"] = [
            f"positive shares the statute's pool excludes, or too small to be "
            f"one vote of {total_votes}: {dropped}. Their votes would vanish "
            f"rather than earn an entitlement"]
        return result
    # `eligible_parties` builds its dict from a set; restore the caller's order
    # so an exact tie falls the same way every time (module docstring, Ties).
    combined = {p: pooled[p] for p in votes}

    wins: dict[str, int] = {}
    for ward in wards:
        party = ward_winners[ward]
        wins[party] = wins.get(party, 0) + 1
    c_wards, d_wards, pool_wins = outside_pool_wards(dict(wins), combined)

    previous = M.COUNCIL
    try:
        # `allocate_with_overhang` reads the council from this module global,
        # as `benchmarks.council_from_shares` sets it; put back afterwards.
        M.COUNCIL = context["council"]
        seats, council, majority, over = M.allocate_with_overhang(
            combined, pool_wins, M.STATUTORY_VALUES["overhang_rule"],
            independent_wards=c_wards, no_pr_list_wards=d_wards)
    except (ValueError, RuntimeError) as exc:
        result["errors"] = [f"the seat law could not complete this allocation: "
                            f"{exc}"]
        return result
    finally:
        M.COUNCIL = previous

    out: dict[str, dict[str, int]] = {}
    for party in list(seats) + [p for p in wins if p not in seats]:
        ward = wins.get(party, 0)
        total = seats.get(party, 0) if party in combined else ward
        if total:
            out[party] = {"ward": ward, "pr": total - ward, "total": total}

    result.update(ok=True, seats=out, council=council, majority=majority,
                  excessive=dict(over), excessive_fired=bool(over),
                  independent_wards=c_wards, no_pr_list_wards=d_wards)
    return result
