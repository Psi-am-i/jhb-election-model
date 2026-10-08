"""A reader's prediction, turned into council seats by the statute alone.

DESIGN-decided §9 (owner, 2026-09-28), with the two ballots of the
prediction restructure (``audits/2026-10-07-prediction-restructure/``, slice
B; BRIEF change 13, owner 2026-10-08). A reader's prediction holds what an
election produces: a winner for every ward, and each party's whole votes on
the WARD ballot and on the LIST ballot. Seats then follow from Municipal
Structures Act Schedule 1 **as this project implements it**, and from nothing
else: no model level, band, pool or geography constrains the reader. This
module is that arithmetic, written to run in the browser under Pyodide.

**It calls the project's seat law; it does not restate it.** The composition
is :func:`prediction.seats_of`, the one composition of the seat law for a
prediction or a reader's entry (``run_model``'s draw loop and
``benchmarks.council_from_shares`` are the two others), which calls in turn:

* :func:`seats.eligible_parties` decides who earns an entitlement, on the
  two ballots as given: a party is in the pool when it has a list vote, and
  its entitlement is its ward plus list votes (the combined vote the statute
  counts; ``seats.py``'s docstring);
* :func:`seats.outside_pool_wards` takes the C and D ward seats out of the pool
  before the quota is struck;
* :func:`montecarlo.allocate_with_overhang` strikes the quota
  (:func:`seats.allocate`) and applies item 16, the excessive-seats clause,
  under the rule in :data:`montecarlo.STATUTORY_VALUES` — the rule the model
  itself is refused permission to leave without ``--counterfactual``.

**Whole votes on each ballot, with no conversion.** The two ballots are the
statute's own arguments, so a model draw's recorded votes
(``ModelRun.ward_vote_draws``, ``pr_vote_draws``: the integers that draw's
``eligible_parties`` read) and its ward winners reproduce that draw's seats
exactly (``tests/test_reader_seats.py``). The ballot totals are the sums of
the votes given: a prediction states its own (no total is fixed by a schema).

What was: until 2026-10-08 the input was each party's share of the COMBINED
vote and a fixed ``total_votes``, rounded to whole votes by largest remainder
and handed to the law as list votes alone. The retired form could not say
which ballot a vote was cast on, so the list ballot a reader is scored on
(``score_forecasts`` key 3) was not something the reader set.

**Inputs, and why each is required**

``ward_votes``, ``list_votes``
    ``{party: whole votes}`` on each ballot, over the context's roster. A
    roster party that is absent is taken as zero (absence from a count means
    no votes). An unknown party is refused, and so is any value that is not a
    non-negative integer (``bool`` included). Each ballot must total at least
    one vote.
``ward_winners``
    ``{ward: party}`` for EVERY ward in the context. Missing and unknown wards
    are both refused; nothing is filled in.
``context``
    The city-year's facts, built at build time by :func:`context_for` (or
    :func:`context_from_run`) and shipped as a small JSON: ``city``,
    ``target``, ``council`` and ``wards`` from the city config, the roster
    ``parties``, and ``no_pr_list`` — the roster parties with no PR list,
    independents included. Nothing is read from disk at call time.

**What it refuses, rather than guessing:** a malformed context; vote maps that
are not mappings of roster parties to whole votes; a ballot with no vote; a
list vote for a party the context lists with no PR list; missing or unknown
wards; a ward won by a party off the roster; and the two refusals of BRIEF
change 13 (owner, 2026-10-08), which are the only ones a reader's choices can
reach:

* **R1** a ward winner with no ward vote (a party that wins a ward has votes
  on that ballot);
* **R2** a ward winner the context does not list as having no PR list, with
  no list vote: ``eligible_parties`` would leave it out of the pool and
  ``outside_pool_wards`` would move its wards to the D term, a silent
  reclassification of a party the reader meant to seat (guard G14).

A ward winner and its citywide ward vote are set separately, so an entry can
be impossible as a whole (130 wards on 5% of the ward vote). That is allowed:
the editor bounds (``build_make.editor_bounds``) constrain the page's editor
and never validity here. A party with a ward vote and no list vote that wins
no ward is not refused either: the statute leaves it out of the pool, which is
what a party with no list on the ballot paper is.

**Ties.** ``seats.allocate`` breaks an exact tie — equal remainder AND equal
votes — by the order of its input, where Schedule 1 says "by lot". This module
passes the pool in the context's roster order, so a given input always gives
the same council. (A model draw's order comes from a set and so from
``PYTHONHASHSEED``; see ``benchmarks.canonical_order``.)

**No party is special-cased** (DESIGN-decided §8). Which parties sit outside the
pool is a property of the roster in the context and of the votes given, not of
this code. "Others" on a page or card is a display grouping only: every party
reaches this function under its own code (JUDGEMENT-CALLS §Q4).

**Pyodide.** Importing this module imports ``prediction`` (the composition,
:func:`prediction.seats_of`), ``montecarlo`` and what it imports at
module level — ``cityconfig``, ``coalitions``, ``fold``, ``parties``,
``polling``, ``seats`` — all numpy and the standard library, with no file read
at import or at call. :func:`context_for` reads the city TOML and is build-time
only. The page therefore ships those modules from ``src/``; that is the cost of
item 16 living in ``montecarlo`` rather than in ``seats``.
"""

from __future__ import annotations

# ⚠️ `montecarlo` and `seats` are imported here although only `prediction`
# calls them. The seat Worker's files (worker-api/tools/sync_seats_py.mjs FILES)
# are held equal to this module's import closure MEASURED in a fresh
# interpreter (tests/test_reader_seats.py). `prediction.seats_of` imports the
# seat law lazily, because `prediction.py` also ships to the page; without these
# two lines the measured closure would lose montecarlo, seats, coalitions,
# fold and polling, the test would ask for them to be dropped from FILES, and
# the Worker would ship without the seat law.
import montecarlo as M  # noqa: F401
import prediction
from seats import eligible_parties, outside_pool_wards  # noqa: F401

#: What the input means and how it is seated, carried in every result so the page
#: cannot show seats without it.
ASSUMPTION = ("Each party's votes are given on the ward ballot and on the list "
              "ballot; wards are taken as picked; a party with a list vote "
              "earns an entitlement from its votes on both ballots together, "
              "which is what the statute counts; list seats fill entitlements "
              "under the excessive-seats clause.")


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


def _is_count(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def _vote_errors(ward_votes, list_votes, roster, no_list) -> list[str]:
    errors = []
    for name, votes in (("ward_votes", ward_votes), ("list_votes", list_votes)):
        if not isinstance(votes, dict):
            errors.append(f"{name} is not a mapping of party to whole votes")
            continue
        unknown = sorted(str(p) for p in set(votes) - set(roster))
        if unknown:
            errors.append(f"unknown parties in {name}: {unknown}")
        bad = sorted(str(p) for p, v in votes.items() if not _is_count(v))
        if bad:
            errors.append(f"{name} that are not whole non-negative numbers of "
                          f"votes: {bad}")
        elif not sum(votes.values()) >= 1:
            errors.append(f"{name} hold no vote: each ballot needs at least one")
    if errors:
        return errors
    listless = sorted(p for p in no_list if list_votes.get(p, 0) > 0)
    if listless:
        errors.append(f"list votes for parties the roster says have no PR list: "
                      f"{listless}. A list-less party's votes are ward votes "
                      f"only and its wards leave the pool (the D term)")
    return errors


def _ward_errors(ward_winners, wards, roster, no_list, ward_votes,
                 list_votes) -> list[str]:
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
    winners = {p for p in ward_winners.values() if p in roster}
    no_ward_vote = sorted(p for p in winners if not ward_votes.get(p, 0) > 0)
    if no_ward_vote:
        errors.append(
            f"wards won by parties with no ward vote: {no_ward_vote}. A party "
            f"that wins a ward has votes on the ward ballot (R1)")
    no_list_vote = sorted(p for p in winners
                          if p not in no_list and not list_votes.get(p, 0) > 0)
    if no_list_vote:
        errors.append(
            f"wards won by parties with no list vote: {no_list_vote}. The "
            f"statute's pool admits a party by its list vote, so its wards "
            f"would leave the pool through the D term in silence; give it a "
            f"list vote, or the roster must list it as having no PR list (R2)")
    return errors


def reader_seats(ward_votes: dict, list_votes: dict, ward_winners: dict,
                 context: dict) -> dict:
    """Council seats for a reader's votes on both ballots and ward picks, by
    the statute alone.

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
    ``pool``
        ``{party: combined votes}``, ward plus list, for every party the
        statute's pool test admitted, in the order the law was given them.
    ``assumption``
        :data:`ASSUMPTION`, verbatim.
    """
    result = {"ok": False, "errors": [], "seats": {}, "council": None,
              "majority": None, "excessive": {}, "excessive_fired": False,
              "independent_wards": 0, "no_pr_list_wards": 0,
              "pool": {}, "assumption": ASSUMPTION}

    errors = context_errors(context)
    if errors:
        result["errors"] = errors
        return result
    roster, wards = context["parties"], context["wards"]
    no_list = set(context["no_pr_list"])

    errors = _vote_errors(ward_votes, list_votes, roster, no_list)
    if not errors:
        errors = _ward_errors(ward_winners, wards, roster, no_list,
                              ward_votes, list_votes)
    if errors:
        result["errors"] = errors
        return result

    ward = {p: ward_votes.get(p, 0) for p in roster}
    lst = {p: list_votes.get(p, 0) for p in roster}
    try:
        seated = prediction.seats_of(
            {"ward_calls": [ward_winners[w] for w in wards], "ward_votes": ward,
             "list_votes": lst},
            context["council"], order=list(roster))
    except (ValueError, RuntimeError) as exc:
        result["errors"] = [f"the seat law could not complete this allocation: "
                            f"{exc}"]
        return result

    result.update(ok=True, seats=seated["seats"], council=seated["council"],
                  majority=seated["majority"], excessive=seated["excessive"],
                  excessive_fired=seated["excessive_fired"],
                  independent_wards=seated["independent_wards"],
                  no_pr_list_wards=seated["no_pr_list_wards"],
                  pool={p: ward[p] + lst[p] for p in seated["pool"]})
    return result
