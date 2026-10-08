"""Score ANY forecast of a council — the model's and every reader's — against the
election result, and rank them by the owner's three keys.

``DESIGN-decided.md`` §5 (owner, 2026-09-27): *"we have a result and thousands
of forecasts. some are objectively superior to others."* The ranking is the
owner's competition order of 2026-10-03, seats, then ward calls, then vote
(``JUDGEMENT-CALLS.md`` §N4, which supersedes ``DESIGN-decided.md`` §13's
ward-count key).
Integration contract: ``audits/2026-09-28-interactive-architecture/INTEGRATION.md``
§3e. ⛔ This module and the rule in it must be frozen (committed, code hash
recorded) before polls open on 4 November; a rule written once the result is
known is not a scoring rule.

The ranking keys, the owner's, in his order (JUDGEMENT-CALLS §N4)
=================================================================

1. **Seat total error** (:func:`seat_error`) — for every party holding a seat
   in the forecast OR the result, ``|forecast seats − actual seats|``, summed.
   A party the forecast never names is a forecast of zero. Lower is better.
2. **Correct ward calls** (:func:`wards_called`) — the wards whose forecast
   winner is the actual winner. *Where* a party wins, not only how many. An
   actual winner that is not on the reader's roster (an independent, while
   the reader roster lacks one) is a miss for every reader, the same for all
   of them. Higher is better.
3. **List-ballot vote error** (:func:`list_vote_error`) — for every party
   with a share in the entry OR on the result's LIST (PR) ballot,
   ``|entry share − actual list-ballot share|`` in percentage points,
   summed. The entry's share is its ``list_votes`` as a share of its own
   list-ballot total: list against list, so the ward ballot never enters key
   3 (guard G15). /your-forecast/ scores a reader against every published
   simulation by these same functions. Lower is better.

:func:`rank_key` is exactly ``(key 1, −key 2, key 3)``, compared
lexicographically: one seat of total error outranks any number of correct
calls, and one correct call outranks any vote error. Forecasts equal on all
three share a rank (competition ranking: 1, 2, 2, 4). Where one winner must
be named, the earlier save before the lock (07:00 SAST, 4 November) wins:
:func:`rank` takes the save times for that and uses nothing else. No weight
appears anywhere, so none can be chosen after the result.

The three measures are array functions over a last axis of parties (or
wards), so one definition scores one result here and every published
simulation on /your-forecast/ (``interactive/pyboot/page.py``'s
``analyse``). That is why this module imports ``reader_seats`` only inside
the functions that seat a council: the page imports this module and must
not carry the seat code.

**Reported, not ranked:** the ward-count error (``ward_count_error``, for
every party winning a ward in the forecast OR the result, ``|forecast wards
won − actual wards won|`` summed; a key under DESIGN-decided §13 until
2026-10-03) and the ward/list split per party (``split_correct``,
``split_by_party``), which, party by party, is implied by the seat and ward
figures: list seats are seats minus wards.

Coalition and mayor are part of a stored forecast and are **not** scored.

**An unscorable forecast is an error, not an exclusion.** The seat service
refuses at save (HTTP 422) a forecast the seat law cannot seat, so none should
reach the ranking; :func:`rank` refuses the whole ranking, naming every such
forecast, rather than rank the rest in silence.

What an entry is
================

An entry is a reader's PREDICTION (STYLE.md rule 11: one complete result), and
it is **exactly the value the site Worker stores** (``src/share-edge.js``
``entryRow``, checked by ``worker-api/src/validate.js`` against the schema
``build_make`` writes into ``your-forecast/forecast.json``), entry version 2
(``interactive/js/make-state.js`` ``FORMAT``, carried by the schema as
``properties.v.const``): ``v``, ``ward_calls`` positional over the schema's
``x-ward-ids``, ``ward_votes`` and ``list_votes`` (``{party: whole votes}`` on
each ballot, every roster party), plus ``coalition``, ``mayor``,
``model_ref``, ``display_name``. Its seats are **recomputed here** through
:func:`reader_seats.reader_seats` on its two ballots — never read from the
record, so a stored number cannot score itself. An entry of any other version
is refused by name (:func:`seat_forecast`, guard G12): version 1 held one
combined share and is retired, not read (BRIEF, no backward compatibility).

**The model is scored by its PREDICTION** (STYLE.md rule 11: one complete
result, not the forecast's ranges). :func:`model_forecast` is rule A, from
``src/prediction.py``, the one definition: each ward to the party that wins it
in the most simulations (a tie to the code first in string order), and each
party's mean ward-ballot and mean list-ballot whole votes across the
simulations; seats then follow by the seat law (``prediction.seats_of``).
JUDGEMENT-CALLS §Q is the choice and MODEL-LOG §1.290 the backtest behind it.
The build's start (``build_make.start_state``) and the page's hand-off call the
same function, so an untouched reader and the model hold one prediction.

Our prediction is held in the entry's own shape (``v``, ``ward_calls``,
``ward_votes``, ``list_votes``), so :func:`score` scores it exactly as it scores
a reader's.

The result
==========

:func:`ingest_result` reads a CLEANED IEC VD-level result file (the layout of
``data/raw/elections/lge2021_JHB_vd_party_clean.csv``, produced by
``ingest_lge.py`` from the IEC download; the raw download is not the input) and
returns ward winners, combined votes and the council:

* **Party names** go ``aliases`` (IEC string → the roster's spelling) →
  :func:`parties.canonical`. ``canonical`` never refuses — it derives a code
  for any string — so an unfamiliar IEC spelling silently becomes a NEW party
  (``UMKHONTO WESIZWE PARTY`` → ``UMKHONTO_WESIZWE_PARTY``, not ``MK``;
  ``HANDOVER.md``'s nomination runbook). Every mapped code must therefore be a
  code of the certified ``roster``; anything else is REFUSED, listing every
  offending IEC string and what it became. Nothing is dropped.
* **Wards** are the IEC's MDB identifiers (``79800001``) in the file and ward
  numbers (``"1"``) in a forecast. The city's ``ward_prefix`` is stripped; an
  identifier without it is refused.
* **Ward winners** are the top party on the ward ballot. An exact tie is
  refused, not broken (the IEC settles it; the file cannot).
* **The council** comes from the project's seat law on the actual ward and
  list votes and ward winners — the same :func:`reader_seats.reader_seats`
  path an entry takes, so the result and the entries are seated by one code
  path. Parties with ward votes and no PR votes (independents included) are
  the context's ``no_pr_list``, which routes their ward seats through the C
  and D terms.
* **An official seat table** (:func:`official_seats.read`'s shape), if given,
  is mapped through the same names and compared party by party, with the
  chamber size, C and D. Every disagreement is recorded on the result, and
  :func:`score` then REFUSES until the caller names ``seat_source``
  (``"computed"`` or ``"official"``). Neither is preferred in silence.

⚠️ ``C`` from a result file is an upper bound: the IEC merges every independent
in a VD into one row (``DATA-QUALITY.md`` item 12). The official table's C is
the check on it, reported as a disagreement like any other.

The raw reader here is a third reader of the cleaned layout, beside
``fold.load`` and ``validate_seats.load_votes``. It exists because both of
those canonicalise names on read (``fold.load``) or keep no per-ward tally
(``validate_seats``), so neither can refuse an unmapped IEC name or see a
tied ward. It reads the four columns scoring needs and, for
``build_make.editor_bounds`` (``roll=True``), the three that carry each VD's
ward and roll: one reader of the cleaned layout, not a second.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

import parties as P

# The ranking keys, in the owner's order (JUDGEMENT-CALLS §N4).
MEASURES = ("seat_error", "wards_called", "list_vote_error")
# Computed and reported for information; not ranking keys.
REPORTED = ("ward_count_error", "split_correct")
SEAT_SOURCES = ("computed", "official")


# --------------------------------------------------------------------------
# names and wards


def name_map(names, roster_codes, aliases=None, *,
             every_alias_used=True) -> dict[str, str]:
    """``{IEC string: roster code}`` for every name, or a refusal listing all.

    ``aliases`` maps an IEC string to the spelling the roster uses; it is
    applied before :func:`parties.canonical`. A name whose code is not a code
    of ``roster_codes`` is refused — every one of them, in one message.
    With ``every_alias_used`` an alias naming no string in ``names`` is refused
    too: a stale alias hides the next respelling.
    """
    aliases = {P.normalise(k): v for k, v in (aliases or {}).items()}
    roster_codes = set(roster_codes)
    out, bad = {}, []
    for raw in sorted(set(names)):
        spelled = aliases.get(P.normalise(raw), raw)
        code = P.canonical(spelled)
        if code in roster_codes:
            out[raw] = code
        else:
            bad.append(f"{raw!r} -> {code}")
    if bad:
        raise ValueError(
            f"{len(bad)} party name(s) do not map onto the certified roster: "
            f"{bad}. parties.canonical derives a code for any string, so an "
            f"IEC respelling becomes a NEW party in silence. Check each "
            f"against the roster and pass the IEC string -> roster spelling "
            f"in `aliases`; do not drop it.")
    unused = sorted(set(aliases) - {P.normalise(n) for n in names})
    if unused and every_alias_used:
        raise ValueError(f"aliases name IEC strings the file does not carry: "
                         f"{unused}. A stale alias hides the next respelling.")
    return out


def ward_number(mdb_id: str, prefix: str) -> str:
    """``79800001`` -> ``"1"`` for a city whose ward prefix is ``798``."""
    mdb_id = str(mdb_id).strip()
    rest = mdb_id[len(prefix):]
    if not mdb_id.startswith(prefix) or not rest.isdigit():
        raise ValueError(f"ward {mdb_id!r} does not carry this city's ward "
                         f"prefix {prefix!r}")
    return str(int(rest))


def certified_roster(city: str, target: str) -> list[str]:
    """The canonical codes of ``[roster] parties`` in ``judgements/<city>-<target>.toml``.

    Delegates to :func:`pools.declared_roster` (imported here, not at module
    level: ``pools`` is the model's largest module and is not needed to score).
    Refuses a roster that is absent or not declared ``complete`` — scoring
    against a partial list would refuse real parties as unmapped.
    """
    import cityconfig
    import pools

    c = cityconfig.load(city)
    block = pools.declared_roster(c, cityconfig.Target(city=c, year=str(target)))
    if not block or not block.get("parties"):
        raise ValueError(f"no [roster] parties declared for {city} {target}")
    if not block.get("complete"):
        raise ValueError(f"the [roster] for {city} {target} is not declared "
                         f"complete; a partial list cannot certify a result")
    return list(dict.fromkeys(block["parties"]))


# --------------------------------------------------------------------------
# the result


#: The columns of the cleaned layout that carry a VD's ward and roll, read only
#: when a caller asks for the roll (``build_make.editor_bounds``).
ROLL_COLUMNS = ("VD_Number", "Registered_Population", "Total_Valid_Votes")


def _read_rows(path: Path, *, roll: bool = False):
    """``(ward_votes, pr_votes, names, vd_roll)`` from a cleaned IEC VD-level file.

    ``ward_votes`` is ``{mdb ward: {IEC name: votes}}`` on the ward ballot;
    ``pr_votes`` is ``{IEC name: votes}`` on the PR ballot. ``vd_roll`` is
    ``{vd: (mdb ward, registered, valid ward-ballot votes)}`` from each VD's
    ward-ballot rows when ``roll`` is true (the :data:`ROLL_COLUMNS` are then
    required, and a VD whose ward rows disagree on any of the three is
    refused), else ``None``.
    """
    ward_votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    pr_votes: dict[str, int] = defaultdict(int)
    names: set[str] = set()
    vd_roll: dict[str, tuple[str, int, int]] | None = {} if roll else None
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        need = {"Ward", "BallotType", "sPartyName", "Party_Votes"}
        if roll:
            need |= set(ROLL_COLUMNS)
        missing = need - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: not a cleaned IEC VD result file; "
                             f"missing columns {sorted(missing)}")
        for row in reader:
            name, ballot = row["sPartyName"], row["BallotType"].strip().upper()
            votes = int(row["Party_Votes"])
            names.add(name)
            if ballot == "WARD":
                ward_votes[row["Ward"].strip()][name] += votes
                if roll:
                    vd = row["VD_Number"].strip()
                    raw = str(row["Registered_Population"]).strip()
                    if raw == "":
                        raise ValueError(f"{path}: VD {vd} has a blank "
                                         f"Registered_Population")
                    seen = (row["Ward"].strip(), int(float(raw)),
                            int(row["Total_Valid_Votes"]))
                    if vd_roll.setdefault(vd, seen) != seen:
                        raise ValueError(f"{path}: VD {vd}'s ward rows disagree "
                                         f"on its ward or roll: {vd_roll[vd]} "
                                         f"and {seen}")
            elif ballot == "PR":
                pr_votes[name] += votes
            else:
                raise ValueError(f"{path}: unknown BallotType {ballot!r}")
    return ward_votes, dict(pr_votes), names, vd_roll


def ingest_result(path, *, city: str, target: str, roster, aliases=None,
                  official=None) -> dict:
    """The actual result of one city-year, seated by the project's seat law.

    ``roster`` is the certified list (IEC strings or codes; each is
    canonicalised) — :func:`certified_roster` for 2026. ``official`` is
    :func:`official_seats.read`'s dict, or None.

    Returns ``{"city", "target", "wards": {ward number: code},
    "ward_votes", "list_votes": {code: votes} on each ballot,
    "combined": {code: votes}, "list_share": {code: percentage points of
    the PR ballot}, "no_pr_list", "roster_codes", "names",
    "council", "seats": {code: {"ward","pr","total"}}, "computed_seats",
    "official_seats", "disagreements": [...]}``. ``seats`` is the computed
    council; the official one, when given, is ``official_seats``.
    """
    import cityconfig
    import reader_seats as R

    city_cfg = cityconfig.load(city)
    roster_codes = list(dict.fromkeys(P.canonical(r) for r in roster))
    ward_raw, pr_raw, names, _roll = _read_rows(path)
    codes = name_map(names, roster_codes, aliases)

    # Ward winners, on canonical codes (two IEC strings of one party add up).
    wards: dict[str, str] = {}
    ties = []
    ward_total: dict[str, int] = defaultdict(int)
    for mdb, counts in ward_raw.items():
        by_code: dict[str, int] = defaultdict(int)
        for name, n in counts.items():
            by_code[codes[name]] += n
            ward_total[codes[name]] += n
        top = max(by_code.values())
        leaders = sorted(c for c, n in by_code.items() if n == top)
        number = ward_number(mdb, city_cfg.ward_prefix)
        if number in wards:
            raise ValueError(f"ward {number} appears under two identifiers")
        if len(leaders) != 1:
            ties.append((number, leaders))
        wards[number] = leaders[0]
    if ties:
        raise ValueError(f"exact ties on the ward ballot: {ties}. The IEC "
                         f"settles these; the result file cannot.")

    pr_total: dict[str, int] = defaultdict(int)
    for name, n in pr_raw.items():
        pr_total[codes[name]] += n
    pr_sum = sum(pr_total.values())
    list_share = {c: 100.0 * n / pr_sum for c, n in pr_total.items()} if pr_sum else {}
    combined = {c: ward_total.get(c, 0) + pr_total.get(c, 0)
                for c in dict.fromkeys(list(ward_total) + list(pr_total))}
    no_pr_list = sorted(c for c in combined if not pr_total.get(c, 0) > 0)
    ward_list = sorted(wards, key=int)
    context = R.context_for(city, str(target), roster_codes, ward_list,
                            no_pr_list)

    # The two ballots as counted: nothing to round, so no round trip to check.
    seated = R.reader_seats(dict(ward_total), dict(pr_total), wards, context)
    if not seated["ok"]:
        raise ValueError(f"the seat law refused the actual result: "
                         f"{seated['errors']}")
    computed = {c: dict(v) for c, v in seated["seats"].items()}

    result = {"city": city, "target": str(target), "wards": wards,
              "ward_votes": dict(ward_total), "list_votes": dict(pr_total),
              "combined": combined, "list_share": list_share,
              "no_pr_list": no_pr_list,
              "roster_codes": roster_codes, "names": codes,
              "council": seated["council"], "seats": computed,
              "computed_seats": computed, "official_seats": None,
              "independent_wards": seated["independent_wards"],
              "no_pr_list_wards": seated["no_pr_list_wards"],
              "disagreements": []}
    if official is not None:
        result["official_seats"], result["disagreements"] = _compare_official(
            official, computed, seated, roster_codes, aliases)
    return result


def _compare_official(official, computed, seated, roster_codes, aliases):
    """Map an official table onto codes and list every disagreement."""
    table = official.get("parties") or {}
    # An alias written for the result file need not appear in the table.
    codes = name_map(table, roster_codes, aliases, every_alias_used=False)
    totals: dict[str, int] = defaultdict(int)
    for name, row in table.items():
        totals[codes[name]] += int(row["seats"])
    official_seats = {c: n for c, n in totals.items() if n > 0}
    got = {c: v["total"] for c, v in computed.items()}
    out = []
    for c in sorted(set(official_seats) | set(got)):
        if official_seats.get(c, 0) != got.get(c, 0):
            out.append(f"{c}: official {official_seats.get(c, 0)} vs computed "
                       f"{got.get(c, 0)}")
    checks = (("seats", seated["council"], "council"),
              ("independents", seated["independent_wards"], "C"),
              ("no_list", seated["no_pr_list_wards"], "D"))
    for key, mine, label in checks:
        if key in official and int(official[key]) != mine:
            out.append(f"{label}: official {official[key]} vs computed {mine}")
    return official_seats, out


# --------------------------------------------------------------------------
# forecasts


def schema_context(schema: dict) -> tuple[dict, list[str]]:
    """``(context, ward_ids)`` from the generated entry schema (``build_make``'s
    ``forecast.json`` ``schema``). Nothing is typed here."""
    return dict(schema["x-seat-context"]), [str(w) for w in schema["x-ward-ids"]]


def entry_version(schema: dict) -> str:
    """The entry version the schema reads: ``properties.v.const``, written
    from ``interactive/js/make-state.js`` ``FORMAT`` (the one definition)."""
    return str(schema["properties"]["v"]["const"])


def version_errors(entry: dict, schema: dict) -> list[str]:
    """``[]``, or the sentence refusing an entry of a version this scorer does
    not read (guard G12). Version 1 (one combined share) is retired."""
    v = entry.get("v") if isinstance(entry, dict) else None
    if v is None or str(v) != entry_version(schema):
        return [f"entry version {v} is not read by this scorer (it reads "
                f"version {entry_version(schema)})"]
    return []


def seat_forecast(entry: dict, schema: dict) -> dict:
    """A stored entry's council, by :func:`reader_seats.reader_seats` on its
    two ballots. Refuses an entry of another version by name
    (:func:`version_errors`). A ``seats`` key on the record is ignored."""
    import reader_seats as R

    refused = version_errors(entry, schema)
    if refused:
        return {"ok": False, "errors": refused}
    context, ward_ids = schema_context(schema)
    calls = entry["ward_calls"]
    if len(calls) != len(ward_ids):
        return {"ok": False, "errors": [
            f"{len(calls)} ward calls for {len(ward_ids)} wards"]}
    winners = dict(zip(ward_ids, calls))
    seated = R.reader_seats(entry["ward_votes"], entry["list_votes"], winners,
                            context)
    seated["ward_winners"] = winners
    return seated


def model_forecast(ward_winners, ward_parties, wards, ward_votes, list_votes,
                   columns, schema: dict) -> dict:
    """Our prediction, as the scorer holds it (module docstring): rule A,
    in the entry's own shape (version 2), so :func:`score` reads it as it
    reads a reader's.

    ``ward_winners`` is ``(draws, wards)`` of indices into ``ward_parties``,
    columns in ``wards`` order (the draw file's ``ward_winner`` block, or
    ``ModelRun.ward_winner_draws`` with the universe). ``ward_votes`` and
    ``list_votes`` are ``(draws, len(columns))`` whole votes per ballot (the
    ``ward_vote`` and ``list_vote`` blocks). Calls :func:`prediction.rule_a`
    with the schema's ``x-ward-ids`` order.

    Refuses (``ValueError``, naming them): a roster party missing from
    ``columns``; a column off the roster with a rule-A vote above zero on
    either ballot; a ward called for a party off the roster; wards that are not
    the schema's. A column off the roster with no vote is accepted, and its
    vote is recorded per ballot in ``outside_roster`` (zero whenever this
    returns), so "no mass outside the roster" is a field, not an inference.
    """
    import prediction

    context, ward_ids = schema_context(schema)
    roster = list(context["parties"])
    columns = [str(c) for c in columns]
    lacking = sorted(set(roster) - set(columns))
    if lacking:
        raise ValueError(f"the vote blocks lack roster parties {lacking}")
    if sorted(map(str, wards)) != sorted(ward_ids):
        raise ValueError("the ward winners are not over the schema's wards")
    pred = prediction.rule_a(ward_winners, ward_parties, wards, ward_votes,
                             list_votes, columns, ward_ids=ward_ids)
    off = [c for c in columns if c not in set(roster)]
    outside = {"ward": sum(pred["ward_votes"][c] for c in off),
               "list": sum(pred["list_votes"][c] for c in off)}
    voted = sorted(c for c in off if pred["ward_votes"][c] > 0 or pred["list_votes"][c] > 0)
    if voted:
        raise ValueError(f"parties off the roster carry votes {voted}; they would "
                         f"leave the seat law's pool unseen")
    stray = sorted({p for p in pred["ward_calls"] if p not in set(roster)})
    if stray:
        raise ValueError(f"wards are called for parties off the roster {stray}")
    ward_v = {p: pred["ward_votes"][p] for p in roster}
    list_v = {p: pred["list_votes"][p] for p in roster}
    empty = [b for b, v in (("ward", ward_v), ("list", list_v)) if not sum(v.values()) > 0]
    if empty:
        raise ValueError(f"rule A gives no vote on the {' or '.join(empty)} ballot")
    return {"v": entry_version(schema), "model_ref": None,
            "ward_calls": pred["ward_calls"],
            "ward_votes": ward_v, "list_votes": list_v,
            "outside_roster": outside,
            "coalition": [], "mayor": None, "display_name": None}


# --------------------------------------------------------------------------
# the three measures: one definition, for one result or for every simulation


def aligned(forecast: dict, columns, actual) -> tuple[list, np.ndarray, np.ndarray]:
    """``(parties, f, a)``: a forecast ``{party: value}`` and actual values
    whose last axis is ``columns``, on the UNION of the two party sets. A party
    absent from one side is zero there: a party the forecast never names is a
    forecast of zero, and a party with no column has nothing on the actual
    side. ``actual`` may carry leading axes (one row per simulation)."""
    columns = list(columns)
    extra = sorted(p for p in forecast if p not in columns)
    a = np.asarray(actual, dtype=float)
    if a.shape[-1] != len(columns):
        raise ValueError(f"{a.shape[-1]} actual values for {len(columns)} columns")
    a = np.concatenate([a, np.zeros(a.shape[:-1] + (len(extra),))], axis=-1)
    parties = columns + extra
    return parties, np.array([float(forecast.get(p, 0.0)) for p in parties]), a


def _total_gap(forecast: dict, columns, actual) -> np.ndarray:
    _parties, f, a = aligned(forecast, columns, actual)
    return np.abs(a - f).sum(axis=-1)


def seat_error(forecast_seats: dict, columns, actual_seats) -> np.ndarray:
    """Key 1: ``Σ_p |forecast seats − actual seats|`` over every party in
    either (:func:`aligned`), per row of ``actual_seats``."""
    return _total_gap(forecast_seats, columns, actual_seats)


def wards_called(calls, actual_winners) -> np.ndarray:
    """Key 2: the wards whose call is the actual winner, per row of
    ``actual_winners`` (last axis the wards, in the order of ``calls``)."""
    calls = np.asarray(calls)
    actual = np.asarray(actual_winners)
    if actual.shape[-1] != calls.shape[-1]:
        raise ValueError(f"{actual.shape[-1]} actual winners for {calls.shape[-1]} calls")
    return (actual == calls).sum(axis=-1)


def list_vote_error(forecast_points: dict, columns, actual_list_points) -> np.ndarray:
    """Key 3, THE LIST BALLOT: ``Σ_p |entry share − actual list-ballot
    share|`` in percentage points over every party in either
    (:func:`aligned`), per row of ``actual_list_points``. The entry's share is
    its list votes over its own list-ballot total (module docstring)."""
    return _total_gap(forecast_points, columns, actual_list_points)


# --------------------------------------------------------------------------
# scoring


def score(forecast: dict, schema: dict, result: dict, *,
          seat_source: str | None = None) -> dict:
    """Score one stored entry (version 2) against one ingested result.

    Returns ``{"ok", "errors", "seat_error", "seat_error_by_party",
    "wards_called", "wards", "wards_missed", "list_vote_error",
    "list_vote_error_by_party", "ward_count_error",
    "ward_count_error_by_party", "split_correct", "split_parties",
    "split_by_party", "seat_source", "seats"}``. The keys named in
    :data:`MEASURES` rank; the split is reported only. ``ok`` is
    False, with ``errors``, when the forecast cannot be seated or the result
    is not usable as it stands; nothing is scored then.
    """
    out = {"ok": False, "errors": []}
    if result["disagreements"] and seat_source is None:
        out["errors"] = [
            "the computed and official councils disagree "
            f"({result['disagreements']}); name seat_source as one of "
            f"{SEAT_SOURCES} — neither is preferred in silence"]
        return out
    source = seat_source or "computed"
    if source not in SEAT_SOURCES:
        out["errors"] = [f"seat_source {source!r} is not one of {SEAT_SOURCES}"]
        return out
    if source == "official" and result["official_seats"] is None:
        out["errors"] = ["seat_source 'official' but no official table given"]
        return out

    refused = version_errors(forecast, schema)
    if refused:
        out["errors"] = refused
        return out
    context, ward_ids = schema_context(schema)
    off_roster = sorted(set(context["parties"]) - set(result["roster_codes"]))
    if off_roster:
        out["errors"].append(
            f"forecast roster parties {off_roster} are not on the result's "
            f"certified roster: a name mapping has failed on one side")
    if set(ward_ids) != set(result["wards"]):
        out["errors"].append(
            f"ward sets differ: forecast only "
            f"{sorted(set(ward_ids) - set(result['wards']), key=int)[:10]}, "
            f"result only "
            f"{sorted(set(result['wards']) - set(ward_ids), key=int)[:10]}")
    if out["errors"]:
        return out

    seated = seat_forecast(forecast, schema)
    if not seated["ok"]:
        out["errors"] = ["the forecast cannot be seated by the statute: "
                         + "; ".join(seated["errors"])]
        return out
    f_seats = seated["seats"]

    actual_ward: dict[str, int] = defaultdict(int)
    for party in result["wards"].values():
        actual_ward[party] += 1
    forecast_ward: dict[str, int] = defaultdict(int)
    for party in seated["ward_winners"].values():
        forecast_ward[party] += 1
    ward_count = {p: forecast_ward.get(p, 0) - actual_ward.get(p, 0)
                  for p in sorted(set(forecast_ward) | set(actual_ward))}
    if source == "official":
        a_total = dict(result["official_seats"])
    else:
        a_total = {c: v["total"] for c, v in result["computed_seats"].items()}

    parties = sorted(set(f_seats) | {c for c, n in a_total.items() if n > 0})
    by_party = {p: f_seats.get(p, {}).get("total", 0) - a_total.get(p, 0)
                for p in parties}
    split = {}
    for p in parties:
        fw = f_seats.get(p, {}).get("ward", 0)
        fp = f_seats.get(p, {}).get("pr", 0)
        aw = actual_ward.get(p, 0)
        ap = a_total.get(p, 0) - aw
        split[p] = {"forecast": (fw, fp), "actual": (aw, ap),
                    "correct": (fw, fp) == (aw, ap)}
    missed = [w for w in ward_ids
              if seated["ward_winners"][w] != result["wards"][w]]
    # Key 3 reads the list ballot only (guard G15): the entry's list votes as
    # a share of its own list total.
    list_total = sum(forecast["list_votes"].values())
    f_points = {p: 100.0 * v / list_total for p, v in forecast["list_votes"].items()}
    actual_points = result["list_share"]
    vote_parties = sorted(set(f_points) | set(actual_points))
    vote_by_party = {p: f_points.get(p, 0.0) - actual_points.get(p, 0.0)
                     for p in vote_parties}
    a_cols = sorted(a_total)

    out.update(ok=True, seat_source=source, seats=f_seats,
               seat_error=int(round(float(seat_error(
                   {p: v.get("total", 0) for p, v in f_seats.items()}, a_cols,
                   [[a_total[c] for c in a_cols]])[0]))),
               seat_error_by_party=by_party,
               wards_called=int(wards_called(
                   [seated["ward_winners"][w] for w in ward_ids],
                   [[result["wards"][w] for w in ward_ids]])[0]),
               wards=len(ward_ids), wards_missed=missed,
               list_vote_error=float(list_vote_error(
                   f_points, list(actual_points),
                   [[actual_points[c] for c in actual_points]])[0]),
               list_vote_error_by_party=vote_by_party,
               ward_count_error=sum(abs(v) for v in ward_count.values()),
               ward_count_error_by_party=ward_count,
               split_correct=sum(v["correct"] for v in split.values()),
               split_parties=len(split), split_by_party=split)
    return out


def rank_key(scored: dict) -> tuple:
    """The owner's ordering (JUDGEMENT-CALLS §N4): lower sorts first.

    Seat total error ascending, then correct ward calls descending, then the
    list-ballot vote error ascending. The ward-count error and the ward/list
    split are not in it.
    """
    return (scored["seat_error"], -scored["wards_called"],
            scored["list_vote_error"])


def rank(scores: dict, saved_at: dict | None = None) -> list[tuple]:
    """``[(rank, id, rank_key)]`` over every forecast in ``scores``.

    Competition ranking: equal keys share a rank and the next rank skips.
    With ``saved_at`` (``{id: sortable time}``), equal keys are ORDERED by
    the earlier save, so where one winner must be named it is the first entry
    of the first rank; they still share their rank. A tied forecast with no
    save time sorts after those with one.

    An unscorable forecast (``ok`` False) is REFUSED, not left out: the seat
    service returns 422 for a forecast the seat law cannot seat, so one here
    means a forecast got past the save check or the result was not usable.
    Every such id is named, with its errors, in one ``ValueError``.
    """
    bad = {i: s.get("errors") for i, s in scores.items() if not s.get("ok")}
    if bad:
        raise ValueError(
            f"{len(bad)} forecast(s) could not be scored and cannot be ranked "
            f"or left out in silence: {bad}. The seat service refuses an "
            f"unseatable forecast at save; find out how these got through.")
    saved_at = saved_at or {}
    ok = [(rank_key(s), saved_at.get(i), i) for i, s in scores.items()]
    ok.sort(key=lambda t: (t[0], t[1] is None, t[1] if t[1] is not None
                           else "", str(t[2])))
    out, prev, current = [], None, 0
    for position, (key, _when, ident) in enumerate(ok, start=1):
        if key != prev:
            current, prev = position, key
        out.append((current, ident, key))
    return out
