"""`score_forecasts`: the one scorer, run on the 2021 Johannesburg result as if it
were 2026.

What this module proves:

1. SELF-SCORE. The 2021 result, written as a stored forecast (its own combined
   shares, its own ward winners), scores perfectly on all three measures,
   against the computed council and against the IEC's official table.
2. KNOWN ERRORS, BY HAND. A forecast that moves one ANC ward to the IFP and two
   quotas of votes from the EFF to the DA scores exactly what the paper
   arithmetic below says. The quota is read from the IEC's own report, not
   from the code under test.
3. NAMES. An IEC respelling (`UMKHONTO WESIZWE PARTY` against a roster that
   says `UMKHONTO WESIZWE`) is refused and named; the alias resolves it to the
   party's own code; a stale alias and a name missing from the roster are
   refused.
4. ABSENCE, WITH CLAUDE.md §4's FOUR PROOFS. "Computed and official councils
   do not disagree" and "the result scored against itself has no error" are
   absence claims. Each states its population and checks it equals what was
   compared, in both directions (0); bounds the population two-sided against
   a computed denominator (1); is shown to catch a constructed violation and
   to go quiet when it is reverted (2); and runs on constructed inputs (3).
5. REFUSALS. A tied ward, a ward without the city prefix, a ward-set
   mismatch, an official disagreement with no `seat_source`, a forecast the
   statute cannot seat.
6. THE MODEL AS A READER. `model_forecast` takes the modal ward winner (ties
   to the earlier roster party) and the median combined share.
7. RANKING. The proposed lexicographic key, competition ranks, the save-time
   tie-break.

No model run: every input is the result file, the IEC report or a construction.
"""

from __future__ import annotations

import copy
import csv
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import official_seats  # noqa: E402
import score_forecasts as S  # noqa: E402

CITY, AS_IF = "joburg", "2026"
RESULT = ROOT / "data/raw/elections/lge2021_JHB_vd_party_clean.csv"
SCHEMA = ROOT / "worker-api/generated/forecast.schema.json"

_CACHE: dict = {}


def _names() -> list[str]:
    with RESULT.open(encoding="utf-8", newline="") as fh:
        return sorted({r["sPartyName"] for r in csv.DictReader(fh)})


def _official() -> dict:
    if "official" not in _CACHE:
        _CACHE["official"] = official_seats.read("JHB", 2021)
    return copy.deepcopy(_CACHE["official"])


def _result() -> dict:
    """2021, as if 2026: the certified roster is the 2021 ballot itself."""
    if "result" not in _CACHE:
        _CACHE["result"] = S.ingest_result(
            RESULT, city=CITY, target=AS_IF, roster=_names(),
            official=_official())
    return copy.deepcopy(_CACHE["result"])


def _schema(result: dict) -> dict:
    """A schema in the generated file's shape, over the result's roster.

    The share scale and tolerance are the generated schema's own, so the test
    types no number the backend owns.
    """
    real = json.loads(SCHEMA.read_text())
    pooled = {c: v for c, v in result["combined"].items()
              if c not in result["no_pr_list"] and v > 0}
    wards = sorted(result["wards"], key=int)
    return {
        "x-seat-context": {"city": CITY, "target": AS_IF,
                           "council": result["council"], "wards": wards,
                           "parties": list(result["roster_codes"]),
                           "no_pr_list": list(result["no_pr_list"])},
        "x-total-votes": sum(pooled.values()),
        "x-share-sum": real["x-share-sum"],
        "x-ward-ids": wards,
    }


def _self_forecast(result: dict, schema: dict) -> dict:
    total = schema["x-total-votes"]
    scale = schema["x-share-sum"]["target"]
    pooled = {c: v for c, v in result["combined"].items()
              if c not in result["no_pr_list"] and v > 0}
    return {"model_ref": "test", "coalition": [], "mayor": None,
            "display_name": None,
            "ward_calls": [result["wards"][w] for w in schema["x-ward-ids"]],
            "combined_share": {c: pooled.get(c, 0) / total * scale
                               for c in schema["x-seat-context"]["parties"]}}


def _seat_holders(result: dict) -> set[str]:
    return {c for c, v in result["computed_seats"].items() if v["total"] > 0}


# ----------------------------------------------------------------- 1. self


def test_the_result_scored_against_itself_is_perfect_on_every_measure():
    result = _result()
    schema = _schema(result)
    forecast = _self_forecast(result, schema)
    holders = _seat_holders(result)
    for source in S.SEAT_SOURCES:
        got = S.score(forecast, schema, result, seat_source=source)
        assert got["ok"], got["errors"]
        assert got["seat_error"] == 0, got["seat_error_by_party"]
        assert got["wards_called"] == got["wards"] == len(result["wards"])
        assert got["wards_missed"] == []
        # rule 0: the split was judged over exactly the seat holders, both ways
        assert set(got["split_by_party"]) == holders
        assert got["split_correct"] == got["split_parties"] == len(holders)


def test_the_computed_council_is_the_one_the_iec_published():
    """Absence of disagreement, with the four proofs (CLAUDE.md §4)."""
    result, official = _result(), _official()
    # 0. the right population, both directions: every official seat holder
    #    and every computed one was compared.
    compared = set(result["official_seats"]) | _seat_holders(result)
    assert set(result["official_seats"]) == _seat_holders(result), compared
    # 1. it looked: the seat holders are a two-sided fraction of the parties
    #    in the IEC's table (the table lists every party with a PR vote).
    scanned(compared, of=official["parties"], low=0.1, high=0.9,
            what="seat-holding parties compared",
            denominator="parties in the IEC seat table")
    assert result["disagreements"] == []

    # 2 + 3. a constructed disagreement is caught, and quiet when reverted.
    names = S.name_map(official["parties"], result["roster_codes"])
    da = next(n for n, c in names.items() if c == "DA")
    moved = copy.deepcopy(official)
    moved["parties"][da]["seats"] += 1
    moved["seats"] += 1
    caught = S.ingest_result(RESULT, city=CITY, target=AS_IF, roster=_names(),
                             official=moved)
    assert any(d.startswith("DA:") for d in caught["disagreements"])
    assert any(d.startswith("council:") for d in caught["disagreements"])
    moved["parties"][da]["seats"] -= 1
    moved["seats"] -= 1
    again = S.ingest_result(RESULT, city=CITY, target=AS_IF, roster=_names(),
                            official=moved)
    assert again["disagreements"] == []


def test_a_disagreement_is_refused_until_the_caller_names_a_seat_source():
    result = _result()
    schema = _schema(result)
    forecast = _self_forecast(result, schema)
    result["disagreements"] = ["DA: official 72 vs computed 71"]
    result["official_seats"]["DA"] += 1
    refused = S.score(forecast, schema, result)
    assert not refused["ok"] and "seat_source" in refused["errors"][0]
    computed = S.score(forecast, schema, result, seat_source="computed")
    official = S.score(forecast, schema, result, seat_source="official")
    assert computed["seat_error"] == 0
    assert official["seat_error"] == 1
    assert official["seat_error_by_party"]["DA"] == -1
    assert not S.score(forecast, schema, result, seat_source="both")["ok"]


# ----------------------------------------------------------- 2. by hand


def test_a_constructed_forecast_gets_the_hand_computed_score():
    """By hand, with Q the IEC's published quota for 2021.

    Edit A: one ward the ANC won is called for the IFP. Wards called falls by
    exactly one. Neither party's entitlement moves (shares are untouched), so
    no total changes: ANC goes from (w, p) to (w-1, p+1), IFP from (w, p) to
    (w+1, p-1). Two splits wrong, seat error unchanged.

    Edit B: 2Q votes move from the EFF to the DA. The combined total, and so
    the quota, is unchanged. Each party's votes move by an exact multiple of
    Q, so its remainder — and the largest-remainder order — is unchanged, and
    its round-one seats move by exactly 2: DA +2, EFF -2. Both on the list
    (neither party's ward count changes). Seat error 4; two more splits
    wrong.

    Total: seat error 4, wards called one fewer, splits correct four fewer.
    The premises the paper leans on are asserted, not assumed.
    """
    result, official = _result(), _official()
    schema = _schema(result)
    total = schema["x-total-votes"]
    scale = schema["x-share-sum"]["target"]
    quota = official["quota"]
    assert total // (result["council"] - result["independent_wards"]
                     - result["no_pr_list_wards"]) + 1 == quota
    assert result["combined"]["EFF"] > 2 * quota

    forecast = _self_forecast(result, schema)
    ward = next(w for w in schema["x-ward-ids"] if result["wards"][w] == "ANC")
    forecast["ward_calls"][schema["x-ward-ids"].index(ward)] = "IFP"
    shift = 2 * quota / total * scale
    forecast["combined_share"]["DA"] += shift
    forecast["combined_share"]["EFF"] -= shift

    seated = S.seat_forecast(forecast, schema)
    assert seated["ok"] and not seated["excessive_fired"]
    got = S.score(forecast, schema, result, seat_source="computed")
    assert got["ok"], got["errors"]
    assert got["seat_error"] == 4
    assert {p: e for p, e in got["seat_error_by_party"].items() if e} == \
        {"DA": 2, "EFF": -2}
    assert got["wards_called"] == len(result["wards"]) - 1
    assert got["wards_missed"] == [ward]
    wrong = {p for p, v in got["split_by_party"].items() if not v["correct"]}
    assert wrong == {"ANC", "IFP", "DA", "EFF"}
    assert got["split_correct"] == got["split_parties"] - 4
    a = result["computed_seats"]
    assert got["split_by_party"]["ANC"]["forecast"] == (
        a["ANC"]["ward"] - 1, a["ANC"]["pr"] + 1)
    assert got["split_by_party"]["IFP"]["forecast"] == (
        a["IFP"]["ward"] + 1, a["IFP"]["pr"] - 1)
    assert got["split_by_party"]["DA"]["forecast"] == (
        a["DA"]["ward"], a["DA"]["pr"] + 2)


def test_a_party_the_forecast_never_names_counts_its_actual_seats_as_error():
    """A forecast of zero is a forecast. Give the EFF's votes to the DA and
    drop the EFF from the roster: the EFF's actual seats are all error."""
    result = _result()
    schema = _schema(result)
    forecast = _self_forecast(result, schema)
    eff = forecast["combined_share"].pop("EFF")
    forecast["combined_share"]["DA"] += eff
    schema["x-seat-context"]["parties"].remove("EFF")
    got = S.score(forecast, schema, result, seat_source="computed")
    assert got["ok"], got["errors"]
    assert got["seat_error_by_party"]["EFF"] == \
        -result["computed_seats"]["EFF"]["total"]


# ---------------------------------------------------------------- 3. names


def test_an_iec_respelling_is_refused_and_named_then_resolved_by_alias():
    roster = ["UMKHONTO WESIZWE", "VRYHEIDSFRONT PLUS", "DEMOCRATIC ALLIANCE"]
    codes = [S.P.canonical(r) for r in roster]
    iec = ["UMKHONTO WESIZWE PARTY", "VRYHEIDSFRONT PLUS | FREEDOM FRONT PLUS",
           "DEMOCRATIC ALLIANCE"]
    try:
        S.name_map(iec, codes)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("an IEC respelling was accepted")
    assert "UMKHONTO WESIZWE PARTY" in message
    assert "VRYHEIDSFRONT PLUS | FREEDOM FRONT PLUS" in message
    assert "DEMOCRATIC ALLIANCE'" not in message   # the good name is not listed

    aliases = {"UMKHONTO WESIZWE PARTY": "UMKHONTO WESIZWE",
               "VRYHEIDSFRONT PLUS | FREEDOM FRONT PLUS": "VRYHEIDSFRONT PLUS"}
    mapped = S.name_map(iec, codes, aliases)
    assert mapped == {"UMKHONTO WESIZWE PARTY": "MK",
                      "VRYHEIDSFRONT PLUS | FREEDOM FRONT PLUS": "VFPLUS",
                      "DEMOCRATIC ALLIANCE": "DA"}

    stale = dict(aliases, **{"CHANGE PARTY": "CHANGE"})
    try:
        S.name_map(iec, codes, stale)
    except ValueError as exc:
        assert "CHANGE PARTY" in str(exc)
    else:
        raise AssertionError("a stale alias was accepted")


def test_a_result_name_missing_from_the_roster_is_refused_not_dropped():
    names = _names()
    short = [n for n in names if n != "GOOD"]
    try:
        S.ingest_result(RESULT, city=CITY, target=AS_IF, roster=short)
    except ValueError as exc:
        assert "'GOOD' -> GOOD" in str(exc) and "1 party name" in str(exc)
    else:
        raise AssertionError("a result party off the roster was dropped")


def test_every_2021_name_maps_and_none_collide():
    """Absence of unmapped names on the real file, with the four proofs."""
    names = _names()
    result = _result()
    mapped = result["names"]
    # 0. the population mapped is exactly the names in the file, both ways
    assert set(mapped) == set(names)
    # 1. it looked: codes are a two-sided fraction of the names (distinct
    #    names -> distinct codes here, so the ratio is one)
    scanned(set(mapped.values()), of=names, low=0.9, high=1.0,
            what="distinct party codes", denominator="IEC party names")
    # 2 + 3. a constructed roster missing one name is caught; restored, quiet
    try:
        S.name_map(names, [c for c in result["roster_codes"] if c != "UIM"])
    except ValueError:
        pass
    else:
        raise AssertionError("the name check did not see a missing code")
    assert S.name_map(names, result["roster_codes"]) == mapped


# ------------------------------------------------------------- 5. refusals


def _write(rows, path):
    cols = ["Province", "Municipality", "Ward", "VD_Number", "VS_Name",
            "BallotType", "Registered_Population", "Spoilt_Votes",
            "Total_Valid_Votes", "sPartyName", "Party_Votes"]
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for ward, ballot, party, votes in rows:
            w.writerow({"Province": "Gauteng", "Municipality": "JHB", "Ward": ward,
                        "VD_Number": "1", "VS_Name": "x", "BallotType": ballot,
                        "Registered_Population": "0", "Spoilt_Votes": "0",
                        "Total_Valid_Votes": "0", "sPartyName": party,
                        "Party_Votes": str(votes)})


def test_a_tied_ward_and_a_foreign_ward_are_refused():
    roster = ["DEMOCRATIC ALLIANCE", "AFRICAN NATIONAL CONGRESS"]
    with tempfile.TemporaryDirectory() as tmp:
        tied = Path(tmp) / "tied.csv"
        _write([("79800001", "Ward", "DEMOCRATIC ALLIANCE", 5),
                ("79800001", "Ward", "AFRICAN NATIONAL CONGRESS", 5)], tied)
        try:
            S.ingest_result(tied, city=CITY, target=AS_IF, roster=roster)
        except ValueError as exc:
            assert "exact ties" in str(exc) and "'1'" in str(exc)
        else:
            raise AssertionError("a tied ward was given a winner")
        # control: break the tie and the tie refusal goes quiet (the file
        # then fails later, on having one ward of the city's many)
        _write([("79800001", "Ward", "DEMOCRATIC ALLIANCE", 6),
                ("79800001", "Ward", "AFRICAN NATIONAL CONGRESS", 5)], tied)
        try:
            S.ingest_result(tied, city=CITY, target=AS_IF, roster=roster)
        except (ValueError, SystemExit) as exc:
            assert "exact ties" not in str(exc)
    assert S.ward_number("79800094", "798") == "94"
    for bad in ("79900094", "798X", "94"):
        try:
            S.ward_number(bad, "798")
        except ValueError:
            continue
        raise AssertionError(f"ward {bad!r} accepted")


def test_ward_set_mismatch_and_an_unseatable_forecast_are_refused():
    result = _result()
    schema = _schema(result)
    forecast = _self_forecast(result, schema)
    assert S.score(forecast, schema, result)["ok"]

    fewer = copy.deepcopy(result)
    dropped = next(iter(fewer["wards"]))
    del fewer["wards"][dropped]
    got = S.score(forecast, schema, fewer)
    assert not got["ok"] and "ward sets differ" in got["errors"][0]

    # a ward won by a party with a zero share: the statute cannot seat it
    bad = copy.deepcopy(forecast)
    bad["ward_calls"][0] = "GOOD"
    share = bad["combined_share"].pop("GOOD")
    bad["combined_share"]["DA"] += share
    bad["combined_share"]["GOOD"] = 0
    got = S.score(bad, schema, result)
    assert not got["ok"] and "cannot be seated" in got["errors"][0]

    # a forecast roster party the result's roster does not know
    odd = copy.deepcopy(schema)
    odd["x-seat-context"]["parties"].append("UMKHONTO_WESIZWE_PARTY")
    got = S.score(forecast, odd, result)
    assert not got["ok"] and "UMKHONTO_WESIZWE_PARTY" in got["errors"][0]


# ------------------------------------------------------ 6. model as reader


def test_the_model_forecast_is_the_modal_ward_and_the_median_share():
    result = _result()
    schema = _schema(result)
    roster = schema["x-seat-context"]["parties"]
    wards = schema["x-ward-ids"]
    truth = _self_forecast(result, schema)
    scale = schema["x-share-sum"]["target"]

    # counts: the actual winner leads every ward, except the first, where
    # two parties tie at the top and the earlier roster party must win.
    counts = [[0] * len(roster) for _ in wards]
    for i, w in enumerate(wards):
        counts[i][roster.index(result["wards"][w])] = 3
    first = sorted((result["wards"][wards[0]], "ANC"), key=roster.index)
    if first[0] == first[1]:
        first = ["ANC", "DA"] if roster.index("ANC") < roster.index("DA") \
            else ["DA", "ANC"]
    counts[0] = [0] * len(roster)
    counts[0][roster.index(first[0])] = counts[0][roster.index(first[1])] = 3

    # share draws whose per-party median is the actual share and whose MEAN
    # is not: the third draw lifts the DA alone, so a mean would move the
    # DA's share relative to every other party's.
    base = [truth["combined_share"][p] / scale for p in roster]
    draws = [[x * f for x in base] for f in (0.5, 1.0)]
    draws.append([x * (3.0 if p == "DA" else 1.5) for x, p in zip(base, roster)])
    got = S.model_forecast(counts, roster, wards, draws, roster, schema)
    assert got["ward_calls"][0] == first[0]
    assert got["ward_calls"][1:] == truth["ward_calls"][1:]
    assert all(abs(got["combined_share"][p] - truth["combined_share"][p])
               < 1e-9 * scale for p in roster)

    # an untouched reader equals the model: its calls, apart from the tied
    # first ward, and its shares score perfectly through the one scorer
    untouched = dict(got, ward_calls=[result["wards"][wards[0]]]
                     + got["ward_calls"][1:])
    scored = S.score(untouched, schema, result, seat_source="computed")
    assert scored["ok"], scored["errors"]
    assert (scored["seat_error"], scored["wards_called"],
            scored["split_correct"]) == (0, scored["wards"],
                                         scored["split_parties"])

    # the order of the columns does not matter; the roster order does
    rev = list(reversed(roster))
    counts_rev = [list(reversed(row)) for row in counts]
    draws_rev = [list(reversed(d)) for d in draws]
    again = S.model_forecast(counts_rev, rev, wards, draws_rev, rev, schema)
    assert again["ward_calls"] == got["ward_calls"]

    # a party off the roster is refused, not renormalised away
    try:
        S.model_forecast(counts, roster[:-1] + ["OTHER"], wards, draws,
                         roster, schema)
    except ValueError as exc:
        assert "OTHER" in str(exc)
    else:
        raise AssertionError("an off-roster party was accepted")


# ------------------------------------------------------------- 7. ranking


def test_the_proposed_ranking_is_lexicographic_with_shared_ranks():
    s = lambda e, w, sp: {"ok": True, "seat_error": e, "wards_called": w,
                          "split_correct": sp}
    scores = {"a": s(4, 100, 10), "b": s(2, 90, 5), "c": s(2, 120, 3),
              "d": s(2, 120, 3), "e": s(2, 120, 4), "x": {"ok": False}}
    ranked = S.rank(scores)
    assert [(r, i) for r, i, _ in ranked] == [
        (1, "e"), (2, "c"), (2, "d"), (4, "b"), (5, "a")]
    tie = S.rank(scores, saved_at={"c": "2026-11-03T10", "d": "2026-11-01T10"})
    assert [(r, i) for r, i, _ in tie][1:3] == [(2, "d"), (2, "c")]


def test_the_certified_roster_covers_every_party_a_reader_can_pick():
    """On the night, `score` refuses a reader roster party the certified roster
    lacks. Checked now, while the schema and the `[roster]` can still be
    fixed: every code a reader can pick is a certified code. A city-year with
    no declared roster is refused, not read as an empty ballot."""
    schema = json.loads(SCHEMA.read_text())
    context = S.schema_context(schema)[0]
    roster = S.certified_roster(context["city"], context["target"])
    assert set(roster) >= set(context["parties"]), \
        sorted(set(context["parties"]) - set(roster))
    scanned(context["parties"], of=roster, low=0.05, high=1.0,
            what="reader-pickable parties checked",
            denominator="certified roster codes")
    try:
        S.certified_roster(CITY, "2021")
    except ValueError as exc:
        assert "no [roster]" in str(exc)
    else:
        raise AssertionError("a city-year with no [roster] was accepted")


def test_the_generated_schema_carries_what_the_scorer_reads():
    """The scorer and the Worker read one schema: the seat context's roster
    is the ward-call roster, both directions, and its wards are x-ward-ids."""
    schema = json.loads(SCHEMA.read_text())
    context, total, target, tolerance, wards = S.schema_context(schema)
    assert set(context["parties"]) == set(
        schema["properties"]["ward_calls"]["items"]["enum"])
    assert list(context["wards"]) == wards
    assert total > 0 and target > 0 and 0 <= tolerance < target


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
