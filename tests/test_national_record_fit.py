"""A PARTY ABSENT FROM THE FITTING ELECTION BUT WITH ITS OWN NATIONAL RECORD IS
FITTED ON THAT RECORD, NOT INHERITED (owner, 2026-10-15, "option A";
JUDGEMENT-CALLS §F6 and §SJ1, MODEL-LOG §1.307).

`pools.place_vectorless` chooses the pool vector for every party with no vector
from the fitting (local) election. Precedence: its own national fit when that
fit identifies a pool > judged `weights` > the splinter blend (`parent_weight`
or `SPLINTER_PARENT_WEIGHT`) > the city mix.

* CONSTRUCTED: the fits are built here from chosen rates and intervals, so the
  premise cannot expire with the data.
* IT CAN SEE: `test_the_detector_sees_the_national_path_disabled` disables the
  national path and the fitted-vector check goes red; restored, green.
* The NPE reader is tested on a constructed file with no BallotType column and
  blank wards, the 2019/2024 layout that made a national fit impossible.
* One live check (labelled): MK's Johannesburg 2024 fit is identified, so the
  §SJ1 `parent_weight` is not what places MK in the 2026 spec.
"""
from __future__ import annotations

import csv
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import numpy as np  # noqa: E402
import cityconfig  # noqa: E402
import pools  # noqa: E402

CATS = ["A", "B", "C"]
POOL_VOTES = np.array([6000.0, 3000.0, 1000.0])
CITY_MIX = POOL_VOTES / POOL_VOTES.sum()
PARENT = np.array([0.9, 0.07, 0.03])


def _fit(rates, bounds, citywide=0.1):
    return pools.PartyFit(party="NEW", citywide=citywide,
                          rates=np.array(rates, dtype=float),
                          bounds=np.array(bounds, dtype=float))


# identified in A (narrow interval, rate above the floor) and nowhere else
GOOD = _fit([0.20, 0.01, 0.0], [[0.12, 0.21], [0.0, 0.40], [0.0, 0.45]])
# identified nowhere: every interval wider than 0.25
WIDE = _fit([0.20, 0.10, 0.05], [[0.0, 0.60], [0.0, 0.70], [0.0, 0.80]])
# identified nowhere: every rate on the floor
FLOOR = _fit([0.001, 0.0, 0.0], [[0.0, 0.01], [0.0, 0.01], [0.0, 0.01]])


def _place(rule, own_fit, *, national=0.12, nat_available=True):
    return pools.place_vectorless(
        "NEW", rule, rule.get("parent", ""), composition={"ANC": PARENT},
        city_mix=CITY_MIX, categories=CATS, own_fit=own_fit,
        pool_votes=POOL_VOTES, npe="2024", nat_source="fixture 2024",
        nat_available=nat_available, national=national)


def _splinter(alpha):
    v = alpha * PARENT + (1 - alpha) * CITY_MIX
    return v / v.sum()


def _fitted_vector_is_used() -> bool:
    vec, note, fitted, refused = _place({"parent": "ANC", "parent_weight": 0.9}, GOOD)
    want = GOOD.rates * POOL_VOTES / (GOOD.rates * POOL_VOTES).sum()
    return (np.allclose(vec, want) and not np.allclose(vec, _splinter(0.9))
            and fitted is not None and fitted["identified"] == ["A"]
            and fitted["superseded"] == ["parent_weight"]
            and fitted["election"] == "2024" and refused is None
            and note.startswith("fitted on the 2024 national election"))


def test_a_party_with_an_identified_national_fit_takes_that_vector():
    assert _fitted_vector_is_used()


def test_the_fitted_vector_supersedes_judged_weights_too():
    rule = {"parent": "ANC", "weights": [0.0, 0.0, 1.0]}
    vec, note, fitted, _ = _place(rule, GOOD)
    assert fitted is not None and fitted["superseded"] == ["weights"]
    assert not np.allclose(vec, [0.0, 0.0, 1.0])
    # with no fit, the judged weights win over the splinter rule
    vec, note, fitted, _ = _place(rule, None, national=0.0)
    assert fitted is None and note == "judged weights"
    assert np.allclose(vec, [0.0, 0.0, 1.0])


def test_a_fit_that_identifies_no_pool_falls_back_to_the_splinter_rule():
    for unidentified in (WIDE, FLOOR):
        vec, note, fitted, refused = _place(
            {"parent": "ANC", "parent_weight": 0.9}, unidentified)
        assert fitted is None
        assert np.allclose(vec, _splinter(0.9)), vec
        assert refused == "its 2024 national fit identifies no pool"
        assert note.startswith("splinter of ANC, 90% its vector")
        assert note.endswith("(not fitted: its 2024 national fit identifies no pool)")
    # and with no declared weight, the default (§F6)
    vec, _, _, _ = _place({"parent": "ANC"}, WIDE)
    assert np.allclose(vec, _splinter(pools.SPLINTER_PARENT_WEIGHT))


def test_no_national_election_falls_back_and_says_why():
    vec, note, fitted, refused = _place({}, None, nat_available=False)
    assert fitted is None and np.allclose(vec, CITY_MIX)
    assert refused == "fixture 2024" and "(not fitted: fixture 2024)" in note
    # a party with no national record at all is not "refused": nothing to fit
    vec, note, fitted, refused = _place({}, None, national=0.0)
    assert refused is None and "not fitted" not in note


def test_the_detector_sees_the_national_path_disabled():
    """Mutation: the national path returns nothing. Red; restored, green."""
    real = pools.vector_from_own_record
    pools.vector_from_own_record = lambda fit, pool_votes: (None, [])
    try:
        assert not _fitted_vector_is_used()
    finally:
        pools.vector_from_own_record = real
    assert _fitted_vector_is_used()


def test_identification_is_at_least_one_pool_through_partyfit_identified():
    vec, ident = pools.vector_from_own_record(GOOD, POOL_VOTES)
    assert ident == [0] and np.isclose(vec.sum(), 1.0)
    assert pools.vector_from_own_record(WIDE, POOL_VOTES) == (None, [])
    assert pools.vector_from_own_record(FLOOR, POOL_VOTES) == (None, [])
    assert pools.vector_from_own_record(None, POOL_VOTES) == (None, [])
    assert pools.vector_from_own_record(_fit([0.2, 0.0, 0.0], GOOD.bounds, citywide=0.0),
                                        POOL_VOTES) == (None, [])


class _FakeCity:
    slug, code = "fake", "FAK"

    def __init__(self, path):
        self._path = path

    def path(self, *parts, root="data"):
        return self._path


def test_the_party_table_reads_the_national_layout():
    """No BallotType column and blank wards (NPE 2019/2024): every row is read
    and placed in a ward through the preceding LGE's VD map. Before
    `_ward_resolver`, `ward_party_shares` dropped every such row."""
    rows = [("1001", "X", 30), ("1001", "Y", 10), ("1002", "X", 5),
            ("1002", "Y", 15), ("1003", "Y", 9)]
    real_map = pools.vd_map
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "npe.csv"
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["Ward", "VD_Number", "Registered_Population",
                        "sPartyName", "Party_Votes"])
            for vd, party, votes in rows:
                w.writerow(["", vd, 100, party, votes])
        pools.vd_map = lambda city, year: ({"1001": "W1", "1002": "W1",
                                            "1003": "W2"}, {})
        try:
            shares, votes = pools.ward_party_shares(_FakeCity(path), "2024")
            reg, cast = pools.ward_totals(_FakeCity(path), "2024")
        finally:
            pools.vd_map = real_map
    assert votes == {"W1": 60.0, "W2": 9.0}, votes
    assert cast == {"W1": 60.0, "W2": 9.0}, cast       # the same wards, one resolver
    assert reg == {"W1": 200.0, "W2": 100.0}, reg
    canon = {pools.P.canonical("X"), pools.P.canonical("Y")}
    assert set(shares["W1"]) == canon
    assert np.isclose(shares["W1"][pools.P.canonical("X")], 35 / 60)


def test_live_mk_2024_fit_is_identified_so_sj1_is_not_read():
    """LIVE (observed, not constructed): Johannesburg's 2024 national fit
    identifies MK, so `place_vectorless` places MK by its fit and the §SJ1
    `parent_weight` (still on the sheet, `test_splinter_parent_weight`) is
    superseded. If this goes red, the 2026 spec is back on the 0.9 blend."""
    city = cityconfig.load("joburg")
    target = cityconfig.Target(city=city, year="2026")
    cfg = pools.load_config()
    cats = list(pools.pool_counts(city, "2021", cfg).categories)
    fits, source = pools.national_fits(city, target, cfg, cats)
    assert "MK" in fits, source
    vec, ident = pools.vector_from_own_record(fits["MK"], np.ones(len(cats)))
    assert vec is not None and ident, fits["MK"].bounds
    rule = pools.load_lineage(city, target)["MK"]
    assert rule.get("parent_weight") == 0.9
    _, _, fitted, _ = pools.place_vectorless(
        "MK", rule, "ANC", composition={"ANC": np.full(len(cats), 1 / len(cats))},
        city_mix=np.full(len(cats), 1 / len(cats)), categories=cats,
        own_fit=fits["MK"], pool_votes=np.ones(len(cats)), npe="2024",
        nat_source=source, nat_available=True, national=0.12)
    assert fitted is not None and fitted["superseded"] == ["parent_weight"]


if __name__ == "__main__":
    run_module(globals())
