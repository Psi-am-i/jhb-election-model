"""`score_forecasts`: the one scorer, run on the 2021 Johannesburg result as if it
were 2026.

What this module proves:

1. SELF-SCORE. The 2021 result, written as a stored forecast (its own combined
   shares, its own ward winners), scores perfectly on all three ranking keys
   and on the reported split, against the computed council and against the
   IEC's official table.
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
6. OUR PREDICTION. `model_forecast` is rule A (`src/prediction.py`): the
   ward each party wins in the most draws (a tie to the code first in string
   order, whatever the column order), each party's mean whole votes on each
   ballot; off-roster votes refused and recorded (`outside_roster`).
7. RANKING. The owner's keys (DESIGN-decided §13) in his order: forecasts
   built on the 2021 result that differ on one key at a time, ranked by hand;
   a forecast better on a later key and worse on an earlier one ranks lower;
   shared ranks; the earlier-save tie-break; an unscorable forecast refused.

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


def _list_points(result: dict) -> dict:
    """Each party's share of the PR ballot in points, read from the file here,
    not from ``ingest_result``'s ``list_share``."""
    votes: dict[str, int] = {}
    with RESULT.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["BallotType"].strip().upper() == "PR":
                code = result["names"][r["sPartyName"]]
                votes[code] = votes.get(code, 0) + int(r["Party_Votes"])
    total = sum(votes.values())
    return {c: 100.0 * v / total for c, v in votes.items()}


def _vote_gap_by_hand(result: dict, forecast: dict, schema: dict) -> float:
    """Key 3 by a loop: every party in the forecast or on the list ballot."""
    scale = schema["x-share-sum"]["target"]
    actual = _list_points(result)
    mine = {c: 100.0 * v / scale for c, v in forecast["combined_share"].items()}
    return sum(abs(mine.get(c, 0.0) - actual.get(c, 0.0)) for c in set(mine) | set(actual))


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
        assert got["ward_count_error"] == 0, got["ward_count_error_by_party"]
        # rule 0: ward counts compared over exactly the ward-winning parties
        assert set(got["ward_count_error_by_party"]) == \
            set(result["wards"].values())
        assert got["wards_called"] == got["wards"] == len(result["wards"])
        assert got["wards_missed"] == []
        # rule 0: the split was judged over exactly the seat holders, both ways
        assert set(got["split_by_party"]) == holders
        assert got["split_correct"] == got["split_parties"] == len(holders)
        # the vote is scored on the list ballot: exact on the combined vote,
        # the forecast still carries the gap between the two ballots
        assert abs(got["list_vote_error"] - _vote_gap_by_hand(result, forecast, schema)) < 1e-9
        assert got["list_vote_error"] > 0
    # a forecast of the list ballot itself scores zero on it
    listed = dict(forecast, combined_share={
        c: v * schema["x-share-sum"]["target"] / 100.0 for c, v in _list_points(result).items()})
    for c in schema["x-seat-context"]["parties"]:
        listed["combined_share"].setdefault(c, 0.0)
    got = S.score(listed, schema, result, seat_source="computed")
    assert got["ok"], got["errors"]
    assert got["list_vote_error"] < 1e-9, got["list_vote_error_by_party"]


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

    Total: seat error 4, ward-count error 2 (ANC −1, IFP +1), wards called
    one fewer, splits correct four fewer.
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
    assert got["ward_count_error"] == 2
    assert {p: e for p, e in got["ward_count_error_by_party"].items() if e} \
        == {"ANC": -1, "IFP": 1}
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


def _ballot_votes(result: dict, ballot: str) -> dict:
    """Each party's whole votes on one ballot (``"PR"`` or ``"Ward"``), read
    from the file here."""
    votes: dict[str, int] = {}
    with RESULT.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["BallotType"].strip().upper() == ballot.upper():
                code = result["names"][r["sPartyName"]]
                votes[code] = votes.get(code, 0) + int(r["Party_Votes"])
    return votes


def _rule_a_inputs(result: dict, schema: dict, parties: list[str]):
    """Constructed draws, four of them, whose rule-A answer is the 2021 result.

    Each ballot's draws alternate the actual votes minus and plus half of
    themselves, so the exact mean is the actual vote and no single draw is.
    Every ward is won by its actual winner in all four draws, except the first,
    which is tied two-two between its actual winner and a second party.
    ``parties`` is the column order (any permutation of the roster).
    """
    import numpy as np
    roster = schema["x-seat-context"]["parties"]
    wards = schema["x-ward-ids"]
    ward_v, list_v = _ballot_votes(result, "Ward"), _ballot_votes(result, "PR")
    assert set(ward_v) | set(list_v) <= set(roster)
    W = np.array([ward_v.get(p, 0) for p in parties], dtype=np.int64)
    L = np.array([list_v.get(p, 0) for p in parties], dtype=np.int64)
    sign = np.array([-1, 1, -1, 1])[:, None]
    ward_draws, list_draws = W + sign * (W // 2), L + sign * (L // 2)
    actual = result["wards"][wards[0]]
    rival = "DA" if actual != "DA" else "ANC"
    winners = np.array([[parties.index(result["wards"][w]) for w in wards]] * 4)
    winners[:, 0] = [parties.index(actual), parties.index(actual),
                     parties.index(rival), parties.index(rival)]
    return winners, ward_draws, list_draws, (actual, rival), ward_v, list_v


def test_the_model_forecast_is_rule_a():
    import prediction
    result = _result()
    schema = _schema(result)
    roster = schema["x-seat-context"]["parties"]
    wards = schema["x-ward-ids"]
    truth = _self_forecast(result, schema)
    scale = schema["x-share-sum"]["target"]
    winners, wv, lv, pair, ward_v, list_v = _rule_a_inputs(result, schema, roster)
    got = S.model_forecast(winners, roster, wards, wv, lv, roster, schema)

    # the tie goes to the code first in string order, and the rest are the
    # actual winners
    assert got["ward_calls"][0] == min(pair)
    assert got["ward_calls"][1:] == truth["ward_calls"][1:]
    # the votes are the exact means, every roster party kept, zero included
    assert got["ward_votes"] == {p: ward_v.get(p, 0) for p in roster}
    assert got["list_votes"] == {p: list_v.get(p, 0) for p in roster}
    assert got["outside_roster"] == {"ward": 0, "list": 0}

    # with the tied ward given to its actual winner, the prediction's council
    # is the result's own, by the one seat law
    untouched = dict(got, ward_calls=[result["wards"][wards[0]]] + got["ward_calls"][1:])
    seated = prediction.seats_of(untouched, schema["x-seat-context"]["council"], order=roster)
    assert {p: v["total"] for p, v in seated["seats"].items()} == \
        {p: v["total"] for p, v in result["computed_seats"].items() if v["total"] > 0}
    # INTERIM (slice B deletes it): the combined share sums to the scale
    assert abs(sum(got["combined_share"].values()) - scale) < 1e-9 * scale

    # the column order does not matter: reversed, and the tie still falls to
    # the string-first code, where an order-based rule would follow the columns
    rev = list(reversed(roster))
    w2, wv2, lv2, *_ = _rule_a_inputs(result, schema, rev)
    again = S.model_forecast(w2, rev, wards, wv2, lv2, rev, schema)
    assert again["ward_calls"] == got["ward_calls"]
    assert again["ward_votes"] == got["ward_votes"] and again["list_votes"] == got["list_votes"]
    # control: in one of the two orders, the first-listed tied party is not
    # the string-first one, so the test separates the rules
    assert {min(pair, key=roster.index), min(pair, key=rev.index)} == set(pair)

    # a roster party absent from the columns is refused
    short = [p for p in roster if p != roster[-1]]
    keep = [roster.index(p) for p in short]
    try:
        S.model_forecast(winners, roster, wards, wv[:, keep], lv[:, keep], short, schema)
    except ValueError as exc:
        assert roster[-1] in str(exc)
    else:
        raise AssertionError("a roster party missing from the vote blocks was accepted")


def test_model_forecast_records_outside_roster_mass_and_refuses_it():
    """G4's record: votes on a column off the roster are refused, naming it;
    the same column with no vote is accepted and recorded as zero per ballot."""
    import numpy as np
    result = _result()
    schema = _schema(result)
    roster = schema["x-seat-context"]["parties"]
    wards = schema["x-ward-ids"]
    winners, wv, lv, *_ = _rule_a_inputs(result, schema, roster)
    cols = roster + ["ZZ_OFF_ROSTER"]
    zero = np.zeros((wv.shape[0], 1), dtype=np.int64)
    ok = S.model_forecast(winners, cols, wards, np.hstack([wv, zero]),
                          np.hstack([lv, zero]), cols, schema)
    assert ok["outside_roster"] == {"ward": 0, "list": 0}
    assert "ZZ_OFF_ROSTER" not in ok["list_votes"]
    try:
        S.model_forecast(winners, cols, wards, np.hstack([wv, zero]),
                         np.hstack([lv, zero + 7]), cols, schema)
    except ValueError as exc:
        assert "ZZ_OFF_ROSTER" in str(exc)
    else:
        raise AssertionError("votes off the roster were accepted")


# ------------------------------------------------------------- 7. ranking


def _swap_calls(forecast, schema, result, pairs):
    """Swap the calls of ``pairs`` of (ward, ward): ward counts are unchanged,
    every swapped ward is a miss, and no share moves."""
    out = copy.deepcopy(forecast)
    ids = schema["x-ward-ids"]
    for a, b in pairs:
        ia, ib = ids.index(a), ids.index(b)
        out["ward_calls"][ia], out["ward_calls"][ib] = \
            result["wards"][b], result["wards"][a]
    return out


def test_the_owners_ranking_on_constructed_forecasts_by_hand():
    """JUDGEMENT-CALLS §N4: seat total error, then correct ward calls, then
    the list-ballot vote error. Six forecasts on the 2021 result, W the ward
    count, v the self forecast's vote error (the gap between the ballots):

    ======  ===============================================  =================
    id      edit to the result-as-forecast                   key (by hand)
    ======  ===============================================  =================
    self    none                                             (0, -W, v)
    vote    a sliver of share moved, no seat or call moved   (0, -W, v + gap)
    ifp     one ANC ward called for the IFP                  (0, -(W-1), v)
    swap1   one ANC ward and one DA ward swap their calls    (0, -(W-2), v)
    swap2   a different ANC/DA pair swaps                    (0, -(W-2), v)
    quota   2 quotas of votes moved EFF -> DA, calls as won  (4, -W, v')
    ======  ===============================================  =================

    Swaps and the IFP call move no share, so no seat total and no vote error
    moves (the IFP ward is §2's edit A). The quota move is §2's edit B: DA +2,
    EFF −2.

    By hand: self 1; vote 2; ifp 3; swap1 and swap2 share 4; quota 6.
    ``vote`` loses to ``ifp`` on key 3 and beats it on key 2, so it ranks
    higher; ``quota`` beats the swaps on key 2 and loses on key 1, so it ranks
    lower. The old order (ward-count error second) put the swaps above ifp;
    the test fails under it.
    """
    result, official = _result(), _official()
    schema = _schema(result)
    total = schema["x-total-votes"]
    scale = schema["x-share-sum"]["target"]
    ids = schema["x-ward-ids"]
    W = len(ids)
    base = _self_forecast(result, schema)
    anc = [w for w in ids if result["wards"][w] == "ANC"]
    da = [w for w in ids if result["wards"][w] == "DA"]
    assert len(anc) >= 3 and len(da) >= 2

    ifp = copy.deepcopy(base)
    ifp["ward_calls"][ids.index(anc[2])] = "IFP"
    quota = copy.deepcopy(base)
    shift = 2 * official["quota"] / total * scale
    quota["combined_share"]["DA"] += shift
    quota["combined_share"]["EFF"] -= shift
    # a sliver, far under a quota, moved in the direction that widens both
    # parties' gap to the list ballot
    listed = _list_points(result)
    sliver = 0.01 * official["quota"] / total * scale
    vote = copy.deepcopy(base)
    for c in ("DA", "EFF"):
        up = vote["combined_share"][c] * 100.0 / scale >= listed[c]
        vote["combined_share"][c] += sliver if up else -sliver
    forecasts = {"self": base, "vote": vote, "ifp": ifp,
                 "swap1": _swap_calls(base, schema, result, [(anc[0], da[0])]),
                 "swap2": _swap_calls(base, schema, result, [(anc[1], da[1])]),
                 "quota": quota}
    scores = {i: S.score(f, schema, result, seat_source="computed")
              for i, f in forecasts.items()}
    assert all(s["ok"] for s in scores.values()), \
        {i: s["errors"] for i, s in scores.items() if not s["ok"]}

    v = _vote_gap_by_hand(result, base, schema)
    by_hand = {"self": (0, -W, v), "ifp": (0, -(W - 1), v),
               "swap1": (0, -(W - 2), v), "swap2": (0, -(W - 2), v),
               "vote": (0, -W, _vote_gap_by_hand(result, vote, schema)),
               "quota": (4, -W, _vote_gap_by_hand(result, quota, schema))}
    got = {i: S.rank_key(s) for i, s in scores.items()}
    for i, key in by_hand.items():
        assert got[i][:2] == key[:2] and abs(got[i][2] - key[2]) < 1e-9, (i, got[i], key)
    assert abs(by_hand["vote"][2] - v - 2 * sliver * 100.0 / scale) < 1e-9
    # the ward count and the split are reported, and in no key: the swaps
    # get every party's split right and ifp does not, and ifp still ranks first
    assert scores["swap1"]["split_correct"] == scores["swap1"]["split_parties"]
    assert scores["ifp"]["split_correct"] < scores["ifp"]["split_parties"]
    assert scores["ifp"]["ward_count_error"] > scores["swap1"]["ward_count_error"] == 0

    ranked = S.rank(scores)
    assert [(r, i) for r, i, _ in ranked] == [
        (1, "self"), (2, "vote"), (3, "ifp"), (4, "swap1"), (4, "swap2"), (6, "quota")]

    # the order of the keys matters: by the vote alone, ifp and the swaps
    # would tie self and beat vote; with the ward count second (the rule
    # before 2026-10-03), the swaps would beat ifp. Neither is what rank returns.
    assert sorted(scores, key=lambda i: scores[i]["list_vote_error"])[-2:] in (
        ["vote", "quota"], ["quota", "vote"])
    old = sorted(("ifp", "swap1"), key=lambda i: (scores[i]["seat_error"],
                 scores[i]["ward_count_error"], -scores[i]["wards_called"]))
    assert old == ["swap1", "ifp"]

    # the earlier save names the single winner among a tie, and the rank is
    # still shared; a tied forecast with no save time goes after
    tie = S.rank(scores, saved_at={"swap1": "2026-11-03T10:00",
                                   "swap2": "2026-11-01T10:00"})
    assert [(r, i) for r, i, _ in tie][3:5] == [(4, "swap2"), (4, "swap1")]
    tie = S.rank(scores, saved_at={"swap1": "2026-11-03T10:00"})
    assert [(r, i) for r, i, _ in tie][3:5] == [(4, "swap1"), (4, "swap2")]


def test_the_ranking_keys_in_order_on_bare_scores():
    """The key and the ranks on constructed scores, one key at a time:
    b is better than every other on keys 2 and 3 but worst on key 1, so it
    ranks last; c is better than a on key 2 but worse on key 3, so it ranks
    higher; d and e tie on all three and share a rank; the ward-count error
    and split_correct, not keys, differ between d and e and change nothing."""
    s = lambda e, w, v, wc=0, sp=0: {"ok": True, "seat_error": e,
                                     "wards_called": w, "list_vote_error": v,
                                     "ward_count_error": wc, "split_correct": sp}
    scores = {"a": s(2, 100, 1.0), "b": s(3, 135, 0.0),
              "c": s(2, 130, 9.0), "d": s(2, 90, 5.0, wc=1, sp=1),
              "e": s(2, 90, 5.0, wc=9, sp=9), "f": s(0, 80, 20.0)}
    ranked = S.rank(scores)
    assert [(r, i) for r, i, _ in ranked] == [
        (1, "f"), (2, "c"), (3, "a"), (4, "d"), (4, "e"), (6, "b")]
    assert S.MEASURES == ("seat_error", "wards_called", "list_vote_error")
    assert "ward_count_error" in S.REPORTED
    assert S.rank({}) == []


def test_the_measures_score_every_row_of_an_actual_array_by_hand():
    """The three measures over a leading axis of rows (the page passes one
    row per published simulation), on constructed values worked by hand."""
    cols = ["A", "B", "OTHER"]
    actual = [[10, 5, 0], [7, 8, 0], [12, 3, 0]]
    # C has no column: the actual side has none of it, so its seats are error
    mine = {"A": 9, "B": 6, "C": 2}
    by_hand = [1 + 1 + 0 + 2, 2 + 2 + 0 + 2, 3 + 3 + 0 + 2]
    assert S.seat_error(mine, cols, actual).tolist() == by_hand
    # a party the forecast never names is a forecast of zero
    assert S.seat_error({"A": 10}, cols, actual).tolist() == [5, 3 + 8, 2 + 3]
    pts = [[40.0, 35.5, 24.5], [42.0, 30.0, 28.0]]
    assert abs(S.list_vote_error({"A": 41.0, "B": 33.0, "OTHER": 26.0}, cols, pts)[1]
               - (1.0 + 3.0 + 2.0)) < 1e-12
    calls = ["A", "B", "A", "C"]
    winners = [["A", "B", "A", "C"], ["B", "B", "B", "A"], ["A", "A", "B", "C"]]
    assert S.wards_called(calls, winners).tolist() == [4, 1, 2]
    # integer codes, as the page holds them: a call off the code list never matches
    assert S.wards_called([0, 1, -1], [[0, 1, 2], [1, 1, 2]]).tolist() == [2, 1]
    for bad in (lambda: S.seat_error(mine, cols, [[1, 2]]),
                lambda: S.wards_called(calls, [["A", "B"]])):
        try:
            bad()
        except ValueError:
            pass
        else:
            raise AssertionError("a misaligned actual array was scored")


def test_an_unscorable_forecast_stops_the_ranking_and_is_named():
    good = {"ok": True, "seat_error": 0, "wards_called": 1,
            "list_vote_error": 0.0}
    scores = {"good": good,
              "bad": {"ok": False, "errors": ["cannot be seated: x"]},
              "worse": {"ok": False, "errors": ["ward calls: y"]}}
    try:
        S.rank(scores)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("an unscorable forecast was ranked or dropped")
    assert "2 forecast(s)" in message
    assert "'bad'" in message and "'worse'" in message
    assert "cannot be seated: x" in message and "'good'" not in message
    # control: remove them and the same call ranks
    assert S.rank({"good": good}) == [(1, "good", (0, -1, 0.0))]


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
