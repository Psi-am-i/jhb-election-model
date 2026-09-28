"""The browser's citywide table stays an output of the function it replaces.

`src/citywide_table.py` records what `levels._citywide_and_roster` returned in
one native run and lets the browser engine look it up instead of parsing 65
election files. Its docstring carries the argument; the blind review that set
these conditions is `audits/2026-09-28-route-b/`. Each test below is one item of
that review's completion predicate and goes red when the item stops being true:

1. regeneration — the table on disk is byte-equal to a fresh build, and the
   comparison can see a one-ulp change;
2. key coverage — every path the model asks for, under the default scenario and
   each control the page ships, is in the table, and nothing in the table goes
   unasked;
3. temporal lock — a table holding an election dated at or after its target is
   refused, as is any other target;
4. miss — a table missing one entry stops the run instead of falling back;
5. equivalence — loaded from the JSON file, the table reproduces every drawn
   array of a native run on the same seed, in the same interpreter;
6. provenance — a table naming code that is not the live code is refused;
   and the list of environment gates still equals what `levels.py` reads.

Runs the model several times; each run is cheap at a few draws but the setup
is not, so this module takes minutes, not seconds.
"""

from __future__ import annotations

import copy
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import citywide_table as CT  # noqa: E402
import cityconfig  # noqa: E402
import levels  # noqa: E402
import montecarlo as M  # noqa: E402

CITY, TARGET = "joburg", "2026"
DRAWS = 12
SEEDS = (20261104, 7)

#: The controls the interactive ships that re-enter the model. The seat law is
#: not here: the page reads it from the published 5,000-draw regimes and never
#: runs the engine for it. Add a control here when it lands (review finding 4).
LEVER_SETTINGS = (
    (),
    ("dirichlet_scale=0.5",),
    ("dirichlet_scale=2.0",),
    ("w_bye=0.0",),
    ("w_bye=1.0",),
    ("poll_paths=all", "poll_credence=1.0"),
)

_real = levels._citywide_and_roster


class _Args:
    def __init__(self, sets=(), draws=DRAWS, seed=None):
        self.config = None; self.set = list(sets)  # noqa: E702
        self.draws = draws; self.seed = seed        # noqa: E702


def _target():
    cityconfig.use(CITY)
    return cityconfig.use_target(TARGET)


def _on_disk() -> dict:
    p = CT.table_path(_target())
    if not p.exists():
        raise AssertionError(
            f"{p.relative_to(ROOT)} does not exist. Build it: "
            f".venv/bin/python src/citywide_table.py --city {CITY} --target {TARGET}")
    return json.loads(p.read_text())


def _run(sets=(), seed=None):
    return M.run_model(_target(), M.load_scenario(_Args(sets, seed=seed)),
                       verbose=False)


def _draw_arrays(run) -> dict:
    import numpy as np
    return {n: np.asarray(getattr(run, n)) for n in dir(run)
            if n.endswith("draws") and not n.startswith("_")}


# -- 1 ----------------------------------------------------------------------

def test_the_table_on_disk_is_a_fresh_build_byte_for_byte():
    fresh = CT.dumps(CT.build(CITY, TARGET))
    on_disk = CT.table_path(_target()).read_text()
    assert on_disk == fresh, (
        "data/processed/citywide_2026.json differs from a fresh build: the "
        "raw files, levels.py or parties.py moved since it was built. Rebuild "
        "it and re-ship the page's copy.")

    # CAN IT SEE: one share moved by one ulp must break the comparison, and
    # the unmoved table must not.
    table = json.loads(fresh)
    k = sorted(table["entries"])[0]
    p = sorted(table["entries"][k]["shares"])[0]
    moved = copy.deepcopy(table)
    v = moved["entries"][k]["shares"][p]
    moved["entries"][k]["shares"][p] = math.nextafter(v, 1.0)
    assert CT.dumps(moved) != fresh, "a one-ulp change survived dumps()"
    assert CT.dumps(json.loads(fresh)) == fresh, "dumps() does not round-trip"


# -- 2 ----------------------------------------------------------------------

def test_every_control_asks_for_exactly_the_tables_files():
    table = _on_disk()
    keys = set(table["entries"])
    checked = []
    for sets in LEVER_SETTINGS:
        asked: set[str] = set()

        def spy(path):
            asked.add(CT._key(path))
            return _real(path)

        levels._citywide_and_roster = spy
        try:
            M.run_model(_target(), M.load_scenario(_Args(sets, draws=2)),
                        verbose=False)
        finally:
            levels._citywide_and_roster = _real
        scanned(asked, of=keys, low=0.9, high=1.1,
                what=f"paths asked for under {sets or 'the default'}",
                denominator="entries in the citywide table")
        assert not asked - keys, (
            f"under {sets or 'the default scenario'} the model asks for "
            f"{sorted(asked - keys)[:3]}, which the table lacks; the browser "
            f"would refuse that control")
        assert not keys - asked, (
            f"under {sets or 'the default scenario'} the table carries "
            f"{sorted(keys - asked)[:3]}, which the model never asked for")
        checked.append(sets)
    scanned(checked, of=LEVER_SETTINGS, low=1.0, high=1.0,
            what="control settings watched", denominator="LEVER_SETTINGS")


# -- 3 ----------------------------------------------------------------------

def test_a_table_holding_the_target_election_is_refused():
    table = _on_disk()
    assert CT.stale_reason(table, TARGET) is None, CT.stale_reason(table, TARGET)
    assert max(CT.election_year(k) for k in table["entries"]) < int(TARGET)

    late = copy.deepcopy(table)
    k = f"data/raw/elections/lge{TARGET}_JHB_vd_party.csv"
    late["entries"][k] = {"shares": {"ANC": 1.0}, "roster": ["ANC"]}
    late["artefact_key"]["inputs"][k] = "0" * 64
    why = CT.stale_reason(late, TARGET)
    assert why and "dated at or after" in why, why
    _assert_refused(late, TARGET)


def test_a_table_is_locked_to_its_own_target():
    table = _on_disk()
    why = CT.stale_reason(table, "2021")
    assert why and "locked to its own target" in why, why
    _assert_refused(table, "2021")


# -- 4 ----------------------------------------------------------------------

def test_a_missing_entry_stops_the_run_instead_of_falling_back():
    table = _on_disk()
    short = copy.deepcopy(table)
    gone = sorted(short["entries"])[len(short["entries"]) // 2]
    del short["entries"][gone]
    del short["artefact_key"]["inputs"][gone]
    CT.install(short, TARGET)
    try:
        _run()
    except CT.TableRefusal as exc:
        assert gone in str(exc), exc
    else:
        raise AssertionError(
            f"the run completed without {gone}: a miss fell back to something "
            f"instead of refusing")
    finally:
        levels._citywide_and_roster = _real


# -- 5 ----------------------------------------------------------------------

def test_the_table_reproduces_every_drawn_array_of_a_native_run():
    import numpy as np
    table = json.loads(CT.table_path(_target()).read_text())
    compared = []
    per_run = 0
    for seed in SEEDS:
        native = _draw_arrays(_run(seed=seed))
        CT.install(table, TARGET)
        try:
            browser = _draw_arrays(_run(seed=seed))
        finally:
            levels._citywide_and_roster = _real
        assert set(native) == set(browser)
        per_run = len(native)
        for name in native:
            assert np.array_equal(native[name], browser[name]), (
                f"seed {seed}: {name} differs between parsing the files and "
                f"reading the table")
            compared.append((seed, name))
    scanned(compared, of=len(SEEDS) * per_run, low=1.0, high=1.0,
            what="drawn arrays compared", denominator="seeds x draw arrays")


# -- 6 ----------------------------------------------------------------------

def test_a_table_from_other_code_is_refused():
    table = _on_disk()
    for field in ("levels_sha", "parties_sha"):
        other = copy.deepcopy(table)
        other["artefact_key"][field] = "0" * 16
        why = CT.stale_reason(other, TARGET)
        assert why and field in why, why
        _assert_refused(other, TARGET)


def test_the_gate_list_is_every_gate_levels_reads():
    read = set(re.findall(r'environ\.get\(\s*"([A-Z_]+)"',
                          (ROOT / "src" / "levels.py").read_text()))
    assert read, "found no environment gate in levels.py; the scan is blind"
    assert read == set(CT.GATES), (
        f"levels.py reads {sorted(read)}, citywide_table.GATES names "
        f"{sorted(CT.GATES)}; a gate the table does not refuse can change "
        f"which files are asked for")


def _assert_refused(table, target):
    try:
        CT.install(table, target)
    except CT.TableRefusal:
        return
    finally:
        levels._citywide_and_roster = _real
    raise AssertionError("install accepted a table it should have refused")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
