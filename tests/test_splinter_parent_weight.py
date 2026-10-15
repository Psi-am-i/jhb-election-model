"""A SPLINTER'S WEIGHT ON ITS PARENT IS THE DEFAULT UNLESS ITS SHEET ENTRY SAYS
OTHERWISE, ONE MECHANISM FOR EVERY PARTY (owner, 2026-10-15; JUDGEMENT-CALLS
§F6 and §SJ1).

0. RIGHT THING: the live judgements file is scanned for every `parent_weight`
   entry; the population is asserted both ways against the register guard.
1. IT LOOKED: the constructed arrival must be a split (its note says SPLIT) and
   the live file must hold at least the MK entry.
2. IT CAN SEE: a mutation that makes the reader ignore the key
   (`test_the_detector_sees_a_reader_that_ignores_the_key`) turns the
   key-moves-the-vector check red; restored it goes green.
3. CONSTRUCTED: the arrival record is synthetic, so it cannot expire.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import numpy as np  # noqa: E402
import cityconfig  # noqa: E402
import pools  # noqa: E402


def _kw():
    return dict(
        rates=np.array([[0.30, 0.10], [0.05, 0.40]]),
        universe=["ANC", "DA"],
        categories=["A", "B"],
        record=[(0.010, 0.5), (0.004, 0.4), (0.02, 0.6), (0.001, 0.3),
                (0.05, 0.7), (0.002, 0.45), (0.03, 0.55), (0.007, 0.5)],
        splinter_fractions=[0.10, 0.20, 0.15],
        pool_size=np.array([1000.0, 2000.0]),
        city_mix=np.array([0.2, 0.8]))


def _capture(body):
    lineage = {"NEWPARTY": dict(parent="ANC", **body)}
    rules, notes = pools.arrival_rules({"NEWPARTY"}, lineage, **_kw())
    assert "SPLIT from ANC" in notes["NEWPARTY"], notes["NEWPARTY"]
    cap = rules["NEWPARTY"]["capture"]
    return np.array([cap.get(g, 0.0) for g in range(2)]), notes["NEWPARTY"]


def _key_moves_the_vector() -> bool:
    """The key changes the vector, by the blend's arithmetic: linear in the
    weight between the pure-city (0) and pure-parent (1) vectors."""
    c0, _ = _capture({"parent_weight": 0.0})
    c1, _ = _capture({"parent_weight": 1.0})
    c9, note = _capture({"parent_weight": 0.9})
    plain, _ = _capture({})
    return (np.allclose(c9, 0.9 * c1 + 0.1 * c0)
            and not np.allclose(c9, plain)
            and "DECLARED" in note)


def test_the_key_moves_a_splinters_vector_by_the_blend_arithmetic():
    assert _key_moves_the_vector()


def test_without_the_key_the_default_is_used():
    plain, note = _capture({})
    explicit, _ = _capture({"parent_weight": pools.SPLINTER_PARENT_WEIGHT})
    assert np.allclose(plain, explicit)
    assert "DECLARED" not in note
    assert pools.splinter_parent_weight({}, "X") == pools.SPLINTER_PARENT_WEIGHT
    assert pools.splinter_parent_weight(None, "X") == pools.SPLINTER_PARENT_WEIGHT


def test_the_detector_sees_a_reader_that_ignores_the_key():
    """Mutation: the reader ignores the entry. The check goes red; restored, green."""
    real = pools.splinter_parent_weight
    pools.splinter_parent_weight = lambda rule, party="": float(pools.SPLINTER_PARENT_WEIGHT)
    try:
        assert not _key_moves_the_vector()
    finally:
        pools.splinter_parent_weight = real
    assert _key_moves_the_vector()


def test_an_out_of_range_or_non_numeric_weight_refuses():
    for bad in (-0.01, 1.01, "0.9", True, float("nan")):
        try:
            pools.splinter_parent_weight({"parent_weight": bad}, "X")
        except SystemExit:
            continue
        raise AssertionError(f"parent_weight = {bad!r} was not refused")
    for ok in (0, 0.0, 1, 0.9, 1.0):
        assert pools.splinter_parent_weight({"parent_weight": ok}, "X") == float(ok)


def _with_judgements(text, fn):
    real = pools.JUDGEMENTS_DIR
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "joburg-2026.toml").write_text(text)
        pools.JUDGEMENTS_DIR = Path(tmp)
        try:
            city = cityconfig.load("joburg")
            return fn(city, cityconfig.Target(city=city, year="2026"))
        finally:
            pools.JUDGEMENTS_DIR = real


def test_the_key_is_in_the_judgements_hash():
    base = '[party.X]\nparent = "ANC"\n'
    h = lambda t: _with_judgements(t, lambda c, g: pools._judgements_sha(c, g))
    a, b = h(base + "parent_weight = 0.9\n"), h(base + "parent_weight = 0.5\n")
    assert a != b and a != h(base)


def test_load_lineage_refuses_out_of_range_and_accepts_the_key():
    load = lambda t: _with_judgements(t, pools.load_lineage)
    assert load('[party.X]\nparent = "ANC"\nparent_weight = 0.9\n')["X"]["parent_weight"] == 0.9
    try:
        load('[party.X]\nparent = "ANC"\nparent_weight = 1.5\n')
    except SystemExit:
        return
    raise AssertionError("an out-of-range parent_weight loaded")


def test_without_judgements_drops_the_owner_calls_and_keeps_the_lineage():
    text = ('[party.X]\nparent = "ANC"\nparent_weight = 0.9\nregister = "§SJ1"\n'
            'support = 0.1\n[roster]\nparties = ["X"]\ncomplete = false\n')
    pools._WITHOUT_JUDGEMENTS = True
    try:
        got = _with_judgements(text, pools.load_lineage)["X"]
    finally:
        pools._WITHOUT_JUDGEMENTS = False
    assert got == {"parent": "ANC"}, got
    assert _with_judgements(text, pools.load_lineage)["X"]["parent_weight"] == 0.9
    assert _with_judgements(text, pools.declared_roster)["parties"] == ["X"]


def test_without_judgements_cannot_write_over_the_forecast():
    for argv in (["pools.py", "--emit", "--without-judgements"],
                 ["pools.py", "--without-judgements", "--out", "x"]):
        real = sys.argv
        sys.argv = argv
        try:
            pools.main()
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(f"{argv} was accepted")
        finally:
            sys.argv = real
            pools._WITHOUT_JUDGEMENTS = False


def test_the_live_sheet_holds_mks_call_and_the_register_row_exists():
    import tomllib
    doc = tomllib.loads((ROOT / "judgements" / "joburg-2026.toml").read_text(encoding="utf-8"))
    entries = {p: b for p, b in doc["party"].items() if "parent_weight" in b}
    assert set(entries) == {"MK"}, sorted(entries)
    assert entries["MK"]["parent_weight"] == 0.9 and entries["MK"]["parent"] == "ANC"
    text = (ROOT / "JUDGEMENT-CALLS.md").read_text(encoding="utf-8")
    assert "| §SJ1 | MK |" in text and entries["MK"]["register"] == "§SJ1"
    assert "owner" in text.split("| §SJ1 | MK |", 1)[1].split("\n", 1)[0].lower()
    assert "90% ANC resemblance" in text


if __name__ == "__main__":
    run_module(globals())
