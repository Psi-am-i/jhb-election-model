"""Score ANY forecast of a council — the model's and every reader's — against the
election result, by the owner's three measures.

``DESIGN-decided.md`` §5 (owner, 2026-09-27): *"we have a result and thousands
of forecasts. some are objectively superior to others."* Integration contract:
``audits/2026-09-28-interactive-architecture/INTEGRATION.md`` §3e. ⛔ This
module and the rule in it must be frozen (committed, code hash recorded) before
polls open on 4 November; a rule written once the result is known is not a
scoring rule.

The three measures, the owner's
===============================

1. **Seat error** — for every party holding a seat in the forecast OR the
   result, ``|forecast seats − actual seats|``, summed. A party the forecast
   never names is a forecast of zero. Lower is better.
2. **Wards called** — the wards whose forecast winner is the actual winner, of
   all the wards. An actual winner that is not on the reader's roster (an
   independent, while the reader roster lacks one) is a miss for every reader, the
   same for all of them. Higher is better.
3. **Split correct** — for every party holding a seat in the forecast OR the
   result, whether BOTH its ward seats and its list seats match. This is where
   the excessive-seats clause (item 16) lives: a forecast can have a party's
   total right and its ward/list split wrong. Reported as a count of parties
   over the union, with the per-party pairs. Higher is better.

Coalition and mayor are part of a stored forecast and are **not** scored; they
are not among the three measures.

⚖️ PROPOSED OVERALL RANKING — FOR THE OWNER TO DECIDE, NOT DECIDED
===================================================================

**Lexicographic, in the owner's own order:** lowest seat error first; among
equal seat errors, most wards called; among those, most parties with the split
correct. :func:`rank_key` is exactly that tuple. Forecasts equal on all three
share a rank (competition ranking: 1, 2, 2, 4). **Tie-break, proposed:** where a
single winner must be named, the earlier save before the lock (07:00 SAST,
4 November) wins; :func:`rank` takes the save times for that and uses nothing
else.

*Why lexicographic and not a weighted sum:* a sum needs weights, and weights
chosen after the result is known are tuned to the result. The lexicographic
order needs no number and follows the order the owner listed the measures in.
*What it costs:* seat error dominates — one seat of error outranks any number of
wards called. If the owner wants the ward measure to trade against seats, that
is a weight, and it must be written down before 4 November.

What a forecast is
==================

A reader's forecast is **exactly the value the backend stores**
(``worker-api/src/validate.js``, ``worker-api/generated/forecast.schema.json``):
``ward_calls`` positional over the schema's ``x-ward-ids``, ``combined_share``
in the schema's percent scale (``x-share-sum.target``), plus ``coalition``,
``mayor``, ``model_ref``, ``display_name``. Its seats are **recomputed here**
through :func:`reader_seats.reader_seats` at the schema's ``x-total-votes`` —
never read from the record, so a stored number cannot score itself.

**The model is scored as a reader who saved the model's central state
untouched** (:func:`model_forecast`): the MODAL winner of each ward, and each
roster party's MEDIAN combined share, renormalised, then seated by the same
statute path at the same ``x-total-votes``. Why these two:

* *modal winner* — the call that maximises the model's expected number of wards
  called (measure 2), one ward at a time; an exact tie in the draw counts
  falls to the earlier party in the schema roster;
* *median share* — each party's own central vote, robust to the long tails the
  draws carry, and a vote vector the statute can seat. The model's per-party
  MEDIAN SEATS are not used: they need not sum to the council and carry no
  ward/list split, so they are not a council and measure 3 could not be
  scored on them.

⚠️ This council can differ from the published per-party median seats, and the
modal-ward vector with the median shares need not be any single draw. The
page's untouched start state (``interactive/js/model.js``, today a weighted
MEAN of the placeholder ``pr`` share) must be built by this one definition,
or an untouched reader and the model would score differently.

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
* **The council** comes from the project's seat law on the actual combined
  votes and ward winners — the same :func:`reader_seats.reader_seats` path a
  reader's forecast takes, so the result and the forecasts are seated by one
  code path. Parties with ward votes and no PR votes (independents included)
  are the context's ``no_pr_list``, which routes their ward seats through the
  C and D terms.
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
tied ward. It reads only the four columns scoring needs.
"""

from __future__ import annotations

import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path

import parties as P
import reader_seats as R

MEASURES = ("seat_error", "wards_called", "split_correct")
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


def _read_rows(path: Path):
    """``(ward_votes, pr_votes, names)`` from a cleaned IEC VD-level file.

    ``ward_votes`` is ``{mdb ward: {IEC name: votes}}`` on the ward ballot;
    ``pr_votes`` is ``{IEC name: votes}`` on the PR ballot.
    """
    ward_votes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    pr_votes: dict[str, int] = defaultdict(int)
    names: set[str] = set()
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        need = {"Ward", "BallotType", "sPartyName", "Party_Votes"}
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
            elif ballot == "PR":
                pr_votes[name] += votes
            else:
                raise ValueError(f"{path}: unknown BallotType {ballot!r}")
    return ward_votes, dict(pr_votes), names


def ingest_result(path, *, city: str, target: str, roster, aliases=None,
                  official=None) -> dict:
    """The actual result of one city-year, seated by the project's seat law.

    ``roster`` is the certified list (IEC strings or codes; each is
    canonicalised) — :func:`certified_roster` for 2026. ``official`` is
    :func:`official_seats.read`'s dict, or None.

    Returns ``{"city", "target", "wards": {ward number: code},
    "combined": {code: votes}, "no_pr_list", "roster_codes", "names",
    "council", "seats": {code: {"ward","pr","total"}}, "computed_seats",
    "official_seats", "disagreements": [...]}``. ``seats`` is the computed
    council; the official one, when given, is ``official_seats``.
    """
    import cityconfig

    city_cfg = cityconfig.load(city)
    roster_codes = list(dict.fromkeys(P.canonical(r) for r in roster))
    ward_raw, pr_raw, names = _read_rows(path)
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
    combined = {c: ward_total.get(c, 0) + pr_total.get(c, 0)
                for c in dict.fromkeys(list(ward_total) + list(pr_total))}
    no_pr_list = sorted(c for c in combined if not pr_total.get(c, 0) > 0)
    ward_list = sorted(wards, key=int)
    context = R.context_for(city, str(target), roster_codes, ward_list,
                            no_pr_list)

    pooled = {c: v for c, v in combined.items() if c not in no_pr_list and v > 0}
    total = sum(pooled.values())
    seated = R.reader_seats({c: v / total for c, v in pooled.items()},
                            wards, context, total)
    if not seated["ok"]:
        raise ValueError(f"the seat law refused the actual result: "
                         f"{seated['errors']}")
    if seated["votes"] != pooled:
        drift = {c: (pooled.get(c), seated["votes"].get(c))
                 for c in set(pooled) | set(seated["votes"])
                 if pooled.get(c) != seated["votes"].get(c)}
        raise ValueError(f"the actual votes did not survive the share "
                         f"round trip: {drift}")
    computed = {c: dict(v) for c, v in seated["seats"].items()}

    result = {"city": city, "target": str(target), "wards": wards,
              "combined": combined, "no_pr_list": no_pr_list,
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


def schema_context(schema: dict) -> tuple[dict, int, float, float, list[str]]:
    """``(context, total_votes, share_target, share_tolerance, ward_ids)``
    from a generated ``forecast.schema.json``. Nothing is typed here."""
    context = dict(schema["x-seat-context"])
    share = schema["x-share-sum"]
    return (context, int(schema["x-total-votes"]), float(share["target"]),
            float(share["tolerance"]), [str(w) for w in schema["x-ward-ids"]])


def seat_forecast(forecast: dict, schema: dict) -> dict:
    """A stored forecast's council, by :func:`reader_seats.reader_seats`.

    The ``combined_share`` percentages become fractions of the schema's
    ``x-share-sum.target``, and the share tolerance the backend accepted is
    passed on, so a forecast the Worker stored is not refused for a sum the
    Worker allowed. A ``seats`` key on the record is ignored.
    """
    context, total, target, tolerance, ward_ids = schema_context(schema)
    calls = forecast["ward_calls"]
    if len(calls) != len(ward_ids):
        return {"ok": False, "errors": [
            f"{len(calls)} ward calls for {len(ward_ids)} wards"]}
    winners = dict(zip(ward_ids, calls))
    shares = {p: v / target for p, v in forecast["combined_share"].items()}
    seated = R.reader_seats(shares, winners, context, total,
                            tolerance=tolerance / target)
    seated["ward_winners"] = winners
    return seated


def model_forecast(ward_winner_counts, count_parties, count_wards,
                   combined_share_draws, share_parties, schema: dict) -> dict:
    """The model's central state as a stored forecast (module docstring).

    ``ward_winner_counts`` is ``(wards, parties)`` in ``count_wards`` ×
    ``count_parties`` order (``ModelRun.ward_winner_counts``);
    ``combined_share_draws`` is ``(draws, parties)`` combined-ballot shares in
    ``share_parties`` order. Both party lists must be the schema roster
    exactly; a modal winner off the roster, or a share for a party off it, is
    refused rather than renormalised away.
    """
    context, _total, target, _tol, ward_ids = schema_context(schema)
    roster = list(context["parties"])
    for label, got in (("ward winner counts", count_parties),
                       ("combined share draws", share_parties)):
        if set(got) != set(roster):
            raise ValueError(
                f"{label} carry parties {sorted(set(got) - set(roster))} off "
                f"the roster and lack {sorted(set(roster) - set(got))}")
    if sorted(map(str, count_wards)) != sorted(ward_ids):
        raise ValueError("the ward winner counts are not over the schema's wards")

    order = {p: i for i, p in enumerate(roster)}
    col = {p: j for j, p in enumerate(count_parties)}
    row = {str(w): i for i, w in enumerate(count_wards)}
    calls = []
    for w in ward_ids:
        counts = {p: ward_winner_counts[row[w]][col[p]] for p in roster}
        top = max(counts.values())
        calls.append(min((p for p in roster if counts[p] == top),
                         key=order.__getitem__))

    j = {p: k for k, p in enumerate(share_parties)}
    median = {p: statistics.median(float(d[j[p]]) for d in combined_share_draws)
              for p in roster}
    scale = math.fsum(median.values())
    return {"model_ref": None, "ward_calls": calls,
            "combined_share": {p: median[p] / scale * target for p in roster},
            "coalition": [], "mayor": None, "display_name": None}


# --------------------------------------------------------------------------
# scoring


def score(forecast: dict, schema: dict, result: dict, *,
          seat_source: str | None = None) -> dict:
    """Score one stored forecast against one ingested result.

    Returns ``{"ok", "errors", "seat_error", "seat_error_by_party",
    "wards_called", "wards", "wards_missed", "split_correct",
    "split_parties", "split_by_party", "seat_source", "seats"}``. ``ok`` is
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

    context, *_rest, ward_ids = schema_context(schema)
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

    out.update(ok=True, seat_source=source, seats=f_seats,
               seat_error=sum(abs(v) for v in by_party.values()),
               seat_error_by_party=by_party,
               wards_called=len(ward_ids) - len(missed), wards=len(ward_ids),
               wards_missed=missed,
               split_correct=sum(v["correct"] for v in split.values()),
               split_parties=len(split), split_by_party=split)
    return out


def rank_key(scored: dict) -> tuple:
    """The PROPOSED ordering (module docstring): lower sorts first.

    ⚖️ FOR THE OWNER TO DECIDE. Seat error ascending, then wards called
    descending, then parties with the split correct descending.
    """
    return (scored["seat_error"], -scored["wards_called"],
            -scored["split_correct"])


def rank(scores: dict, saved_at: dict | None = None) -> list[tuple]:
    """``[(rank, id, rank_key)]`` over the scorable forecasts in ``scores``.

    Competition ranking: equal keys share a rank and the next rank skips.
    With ``saved_at`` (``{id: sortable time}``), equal keys are ORDERED by
    the earlier save — the proposed single-winner tie-break — but still share
    their rank. Unscorable forecasts (``ok`` False) are not ranked; the caller
    reports them. ⚖️ That exclusion is itself a ranking decision for the owner
    (rank last, exclude, or refuse at save): ``validate.js`` stores forecasts
    the statute cannot seat, such as a ward won by a party with a zero share.
    """
    saved_at = saved_at or {}
    ok = [(rank_key(s), saved_at.get(i), i) for i, s in scores.items()
          if s.get("ok")]
    ok.sort(key=lambda t: (t[0], t[1] is None, t[1] if t[1] is not None
                           else "", str(t[2])))
    out, prev, current = [], None, 0
    for position, (key, _when, ident) in enumerate(ok, start=1):
        if key != prev:
            current, prev = position, key
        out.append((current, ident, key))
    return out
