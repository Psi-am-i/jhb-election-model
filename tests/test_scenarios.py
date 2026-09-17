"""`scenarios.py` reads per-draw ward results back and finds the draws behind a
scenario. Inputs are CONSTRUCTED files, so nothing depends on today's forecast.
"""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import scenarios as S  # noqa: E402


def _write(tmp: Path):
    # three draws, two wards; draw 2 is the odd one out
    with (tmp / "ward_draws.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "W1", "W2"])
        w.writerows([[0, "ANC", "DA"], [1, "ANC", "DA"], [2, "DA", "DA"]])
    with (tmp / "seat_detail_draws.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["draw", "party", "ward_seats", "list_seats", "seats", "excessive"])
        w.writerows([[0, "ANC", 1, 0, 1, 1], [0, "DA", 1, 1, 2, 0],
                     [1, "ANC", 1, 1, 2, 0], [1, "DA", 1, 0, 1, 0],
                     [2, "DA", 2, 1, 3, 0]])


def test_a_condition_selects_exactly_its_draws_in_both_directions():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write(tmp)
        detail, winners, wards = S.load(tmp)
        assert sorted(detail) == [0, 1, 2] and wards == ["W1", "W2"]
        assert S.matching(detail, S.parse(["DA>=2"])) == [0, 2]
        assert S.matching(detail, S.parse(["DA>=2", "ANC>=1"])) == [0]
        # a party absent from a draw has zero seats there, not a missing value
        assert S.matching(detail, S.parse(["ANC==0"])) == [2]


def test_flips_are_measured_against_the_modal_winner():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write(tmp)
        detail, winners, wards = S.load(tmp)
        modal = S.modal_winners(winners, wards)
        assert modal == {"W1": "ANC", "W2": "DA"}
        assert S.flips(winners, modal, 2) == [("W1", "ANC", "DA")]
        assert S.flips(winners, modal, 0) == []


def test_the_excessive_flag_and_the_split_survive_the_round_trip():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        _write(tmp)
        detail, _, _ = S.load(tmp)
        assert detail[0]["ANC"] == {"wards": 1, "list": 0, "seats": 1, "excessive": True}
        assert detail[1]["ANC"]["excessive"] is False


def test_an_unreadable_condition_refuses():
    try:
        S.parse(["DA gets lots"])
    except SystemExit:
        return
    raise AssertionError("a malformed condition was accepted")
