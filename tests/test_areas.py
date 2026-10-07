"""`areas.py` — the Soweto wards, generated from the raw files and checked.

The committed list in ``cities/joburg.toml`` ``[areas.soweto]`` is a derived
artefact, so the test REGENERATES it from the station addresses and the VD ->
ward crosswalk and compares (CLAUDE.md §4: regenerate, don't grep). The rule's
parts are tested on CONSTRUCTED inputs whose answers are worked by hand.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import areas as A  # noqa: E402
from _support import run_module, scanned  # noqa: E402


def _station(vd, address):
    return {"type": "Feature", "geometry": None,
            "properties": {"VOTINGDIST": vd, "ADDRESS": address}}


def _stations(tmp: Path, rows) -> Path:
    path = tmp / "stations.geojson"
    path.write_text(json.dumps({"type": "FeatureCollection",
                                "features": [_station(v, a) for v, a in rows]}))
    return path


def test_an_address_names_soweto_by_a_word_start_and_an_exclusion_wins():
    g, x = A.SOWETO_GAZETTEER, A.SOWETO_EXCLUDE
    assert A.address_in_area("12 MAIN RD  ORLANDO EAST  SOWETO", g, x)
    # a prefix of a longer word counts: Braamfischerville by its gazetteer term
    assert A.address_in_area("PHASE 2  BRAAMFISCHERVILLE  ROODEPOORT", g, x)
    # whitespace inside a two-word term is collapsed before matching
    assert A.address_in_area("1 ROAD  PROTEA   GLEN", g, x)
    # inside a word is not a match
    assert not A.address_in_area("3 KADUBE STREET  LENASIA", g, x)
    # an exclusion wins over a gazetteer term in the same address
    assert A.address_in_area("5 STREET  KLIPSPRUIT  SOWETO", g, x)
    assert not A.address_in_area("5 STREET  KLIPSPRUIT WEST  SOWETO", g, x)
    assert not A.address_in_area("CNR ROAD  ELDORADO PARK  SOWETO", g, x)
    assert not A.address_in_area("", g, x) and not A.address_in_area(None, g, x)
    # a street named after a township is not the township (the two real false
    # matches, 2026-10-07), but the township named elsewhere still counts
    assert not A.address_in_area("N12 MOROKA BYPASS  JHB  LENASIA", g, x)
    assert not A.address_in_area("6694 DLAMINI DRIVE  IVORY PARK  MIDRAND", g, x)
    assert not A.address_in_area("1 ORLANDO ST  ROSETTENVILLE", g, x)
    assert A.address_in_area("1 ORLANDO ST  ORLANDO EAST", g, x)
    assert A.address_in_area("12 VILAKAZI STREET  ORLANDO WEST  SOWETO", g, x)


def test_a_split_district_counts_by_part_and_the_cut_is_inclusive():
    # ward 1: 500 of 1000 inside -> exactly the cut -> in
    # ward 2: 499 of 1000 inside -> just under -> out
    # ward 3: split VD "S" puts 600 inside of 700 -> in
    parts = [("A", "1", 500), ("B", "1", 500),
             ("C", "2", 499), ("D", "2", 501),
             ("S", "3", 600), ("E", "3", 100), ("S", "2", 0)]
    inside = {"A", "C", "S"}
    assert A.area_wards(parts, inside, 0.5) == [1, 3]
    assert A.roll_share(parts, [1, 3]) == (1000 + 700) / 2700


def test_derive_reads_the_station_file_and_refuses_a_district_with_no_station():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        stations = _stations(tmp, [(1, "X  DUBE  SOWETO"), (2, "Y  SANDTON")])
        parts = [("1", "7", 10), ("2", "8", 10)]
        assert A.derive("joburg", "soweto", parts=parts, stations=stations) == [7]
        try:
            A.derive("joburg", "soweto", parts=parts + [("3", "8", 5)], stations=stations)
        except SystemExit as e:
            assert "no station" in str(e)
        else:
            raise AssertionError("a district with no station was placed silently")


def test_the_committed_soweto_wards_are_what_the_rule_gives_today():
    """Regenerate from data/raw/geo and data/processed and compare with the
    committed table, in both directions (list equality)."""
    have, derived = A.check("joburg", "soweto")
    assert have is not None, "cities/joburg.toml has no [areas.soweto]"
    # (1) it looked: a set that is neither empty nor the whole city, as a
    # fraction of the wards the crosswalk carries
    every = sorted({int(w) for _vd, w, _r in A.crosswalk_parts("joburg", "2026")})
    scanned(derived, of=every, low=0.05, high=0.6,
            what="Soweto wards derived", denominator="2026 wards in the crosswalk")
    assert have == derived, (have, derived)


def test_a_one_ward_change_to_the_committed_table_is_caught_and_reverting_clears_it():
    derived = A.derive("joburg", "soweto")
    outside = next(w for w in range(1, 200) if w not in derived)
    with tempfile.TemporaryDirectory() as tmp:
        cities = Path(tmp)
        shutil.copy(ROOT / "cities" / "joburg.toml", cities / "joburg.toml")
        for wrong in (sorted(derived + [outside]), derived[1:]):
            A.write("joburg", "soweto", wrong, cities / "joburg.toml")
            have, _ = A.check("joburg", "soweto", cities, derived=derived)
            assert have == wrong and have != derived
        A.write("joburg", "soweto", derived, cities / "joburg.toml")
        have, _ = A.check("joburg", "soweto", cities, derived=derived)
        assert have == derived
        # rewriting replaces the table rather than appending a second one
        assert (cities / "joburg.toml").read_text().count("[areas.soweto]") == 1


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
