"""THE 2026 ROLL IS THE IEC SNAPSHOT, ONE DEFINITION, AND NO BACKTEST SEES IT.

``build_concordance.apportion_roll`` places each VD wholly in one ward (the
committed assignment, ``archive/vd-ward-assignment-2026/``), scales the VDs of
ward w by ``Registered_snapshot[w] / sum(vd_registered of w's VDs)`` and writes
the result as ``part_registered_2026`` on the VD's assigned row, 0 on its other
parts (rule and city-total choice: JUDGEMENT-CALLS section T1). ``montecarlo.read_ward_crosswalk`` prefers that column when the file has
it; ``ward_parts``, ``pools._target_roll``, ``pools.vd_map`` and
``build_make.expected_ward_shares`` all reach it through that one reader.

What this file proves, per CLAUDE.md section 4:

0. THE RIGHT POPULATION. The wards compared are the snapshot's own and the
   crosswalk's own, asserted equal in both directions, not a typed 135.
1. IT LOOKED. The city total is computed from the snapshot file and compared
   with the recorded structure; nothing is typed.
2. IT CAN SEE. A snapshot with one ward changed moves that ward and no other; a
   crosswalk with the 2026 column removed turns the forecast-path check red
   (`test_the_forecast_path_check_goes_red_without_the_column`).
3. CONSTRUCTED INPUT. The split-VD arithmetic is hand-worked on a fixture.

Backtests: a held election resolves its wards from its own result file and never
opens the crosswalk; asserted by making the crosswalk reader raise.
"""

from __future__ import annotations

import csv
import sys
import tempfile
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import build_concordance  # noqa: E402
import cityconfig  # noqa: E402
import inputs_preflight  # noqa: E402
import montecarlo as M  # noqa: E402
import pools  # noqa: E402

ELECTIONS = ROOT / "data" / "raw" / "elections"
CROSSWALK = ROOT / "data" / "processed" / "vd_ward_2026.csv"


def _snapshot() -> dict[str, int]:
    snap = inputs_preflight.roll_snapshot("joburg")
    if snap is None:
        skip("no joburg registration snapshot")
    return inputs_preflight.read_roll_snapshot(snap)


def _crosswalk_rows() -> list[dict]:
    if not CROSSWALK.exists():
        skip(f"no crosswalk at {CROSSWALK}")
    with CROSSWALK.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@contextmanager
def _target(year: str):
    prev_city, prev_year = cityconfig.active().slug, cityconfig.target().year
    try:
        cityconfig.use("joburg")
        yield cityconfig.use_target(year)
    finally:
        cityconfig.use(prev_city)
        cityconfig.use_target(prev_year)


def _write(path: Path, rows: list[dict], drop: tuple[str, ...] = ()) -> None:
    fields = [f for f in rows[0] if f not in drop]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def _ward_totals(parts) -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    for _vd, ward, registered in parts:
        out[ward] += registered
    return dict(out)


def _forecast_roll_matches_snapshot(processed: Path) -> bool:
    """Does the roll the 2026 forecast path reads equal the snapshot, ward by
    ward? ``processed`` holds the crosswalk the path reads."""
    snap = _snapshot()
    with _target("2026") as target:
        parts, _ = M.ward_parts(target, ELECTIONS, processed)
        ids = {r["Ward_2026"]: r["WardID_2026"]
               for r in csv.DictReader((processed / "vd_ward_2026.csv")
                                       .open(encoding="utf-8", newline=""))}
    got = {ids[w]: n for w, n in _ward_totals(parts).items()}
    return got == snap


# --------------------------------------------------------------------------
# conservation, on the real files
# --------------------------------------------------------------------------

def test_every_ward_sums_to_the_snapshot_and_the_city_to_its_ward_rows():
    snap = _snapshot()
    rows = _crosswalk_rows()
    assert "part_registered_2026" in rows[0], (
        "vd_ward_2026.csv has no part_registered_2026; run "
        "src/build_concordance.py --city joburg")
    by_ward: dict[str, int] = defaultdict(int)
    for r in rows:
        by_ward[r["WardID_2026"]] += int(r["part_registered_2026"])
    # the population, both directions
    assert set(by_ward) == set(snap), (
        sorted(set(by_ward) ^ set(snap))[:10])
    assert 0 < len(snap)
    bad = {w: (by_ward[w], snap[w]) for w in snap if by_ward[w] != snap[w]}
    assert not bad, f"wards whose parts do not sum to the snapshot: {list(bad.items())[:5]}"
    # the city total is the sum of the ward rows, computed from the file
    assert sum(by_ward.values()) == sum(snap.values())
    with _target("2026") as target:
        assert sum(by_ward.values()) == int(target.structure["registered"]), (
            "cities/joburg.toml `registered` is not what src/derive_city.py prints")


def test_the_crosswalk_declares_the_snapshot_it_was_built_from():
    snap = inputs_preflight.roll_snapshot("joburg")
    declared = {r["roll_snapshot"] for r in _crosswalk_rows()}
    assert declared == {inputs_preflight.snapshot_label(snap)}, declared
    assert inputs_preflight.declared_roll_snapshot("joburg", "2026") \
        == inputs_preflight.snapshot_label(snap)


def test_the_forecast_path_reads_the_snapshot():
    assert _forecast_roll_matches_snapshot(CROSSWALK.parent)


def test_the_forecast_path_check_goes_red_without_the_column():
    """(2) IT CAN SEE: the same check, on a crosswalk with the 2026 columns
    stripped, must fail, because the reader then falls back to the MDB layer's
    registration."""
    rows = _crosswalk_rows()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write(d / "vd_ward_2026.csv", rows, drop=("part_registered_2026", "roll_snapshot"))
        assert not _forecast_roll_matches_snapshot(d), (
            "the check passes on a crosswalk without the snapshot's column, so "
            "it cannot tell the snapshot from the 2024 registration")
    assert _forecast_roll_matches_snapshot(CROSSWALK.parent), "and it goes green again"


def test_a_crosswalk_without_the_column_falls_back_to_the_mdb_registration():
    rows = _crosswalk_rows()
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "vd_ward_2026.csv"
        _write(p, rows, drop=("part_registered_2026", "roll_snapshot"))
        parts, _, _ = M.read_ward_crosswalk(p, "2026")
    assert [r for _v, _w, r in parts] == [int(r["part_registered"]) for r in rows]


# --------------------------------------------------------------------------
# the rule, on constructed input
# --------------------------------------------------------------------------

def _part(vd, ward_id, reg, whole=None):
    return {"VD_Number": vd, "WardID_2026": ward_id, "part_registered": str(reg),
            "vd_registered": str(reg if whole is None else whole)}


def _fixture():
    """VD A (1000) straddles wards 1 and 2 and is assigned to 1; C (500) is
    whole in 1; B (600) is whole in 2."""
    rows = [_part("A", "1", 600, 1000), _part("C", "1", 500),
            _part("A", "2", 400, 1000), _part("B", "2", 600)]
    return rows, {"A": "1", "B": "2", "C": "1"}


def _figures(rows):
    return {(r["VD_Number"], r["WardID_2026"]): int(r["part_registered_2026"]) for r in rows}


def test_a_split_vd_sits_wholly_on_its_assigned_ward_scaled_by_that_wards_ratio():
    """Ward 1 holds A(1000)+C(500)=1500 and the snapshot says 1800 (x1.2): A 1200,
    C 600. Ward 2 holds only B(600), snapshot 540: B 540. A's part in ward 2 is 0.
    Hand arithmetic."""
    rows, asg = _fixture()
    build_concordance.apportion_roll(rows, {"1": 1800, "2": 540}, asg)
    assert _figures(rows) == {("A", "1"): 1200, ("C", "1"): 600,
                              ("A", "2"): 0, ("B", "2"): 540}


def test_whole_numbers_by_largest_remainder_sum_exactly():
    rows = [_part("A", "1", 1), _part("B", "1", 1), _part("C", "1", 1)]
    build_concordance.apportion_roll(rows, {"1": 5}, {"A": "1", "B": "1", "C": "1"})
    got = [int(r["part_registered_2026"]) for r in rows]
    assert sum(got) == 5 and sorted(got) == [1, 2, 2]
    assert got == [2, 2, 1], "ties go to the earlier VD number"


def _raises(rows, roll, asg):
    try:
        build_concordance.apportion_roll(rows, roll, asg)
    except SystemExit as exc:
        return str(exc)
    return None


def test_inputs_that_cannot_be_apportioned_refuse():
    rows, asg = _fixture()
    roll = {"1": 1800, "2": 540}
    assert "sum to 0" in (_raises([_part("A", "1", 0)], {"1": 10}, {"A": "1"}) or "")
    only_snap = _raises([_part("A", "1", 5)], {"1": 10, "2": 3}, {"A": "1"})
    assert only_snap and "only in the snapshot" in only_snap
    only_xw = _raises([_part("A", "1", 5), _part("B", "2", 5)], {"1": 10}, {"A": "1", "B": "2"})
    assert only_xw and "only in the crosswalk" in only_xw
    gone = _raises(rows, roll, {"A": "1", "B": "2"})
    assert gone and "missing from the assignment" in gone and "C" in gone
    extra = _raises(rows, roll, {**asg, "Z": "1"})
    assert extra and "not in the crosswalk" in extra
    not_part = _raises(rows, roll, {**asg, "B": "1"})
    assert not_part and "not one of its parts" in not_part
    # ward 2 left with no VD
    rows2 = [_part("A", "1", 600, 1000), _part("A", "2", 400, 1000), _part("C", "1", 5)]
    nobody = _raises(rows2, {"1": 10, "2": 3}, {"A": "1", "C": "1"})
    assert nobody and "no VD is assigned" in nobody


# --------------------------------------------------------------------------
# the committed assignment, on the real files
# --------------------------------------------------------------------------

def _assignment() -> dict[str, str]:
    return build_concordance.read_assignment()


def test_every_vd_figure_sits_on_exactly_one_of_its_parts_its_assigned_ward():
    rows = _crosswalk_rows()
    asg = _assignment()
    by_vd: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_vd[r["VD_Number"]].append(r)
    assert set(by_vd) == set(asg), "population, both directions"
    assert 0 < len(by_vd)
    for vd, parts in by_vd.items():
        on = [p for p in parts if int(p["part_registered_2026"]) > 0]
        assert len(on) <= 1, vd
        assert all(p["WardID_2026"] == asg[vd] for p in on), vd
        assert asg[vd] in {p["WardID_2026"] for p in parts}, vd
        assert all(int(p["part_registered_2026"]) == 0
                   for p in parts if p["WardID_2026"] != asg[vd]), vd


def test_the_per_ward_ratio_of_snapshot_to_assigned_2024_registration_is_tight():
    """A property of the committed INPUT (the assignment), not a tuning target:
    sd of IEC_w / sum of vd_registered of w's VDs, over the snapshot's own
    wards. Proportional scaling gave a far larger spread."""
    snap = _snapshot()
    rows = _crosswalk_rows()
    asg = _assignment()
    base: dict[str, int] = defaultdict(int)
    seen = set()
    for r in rows:
        if r["VD_Number"] not in seen:
            seen.add(r["VD_Number"])
            base[asg[r["VD_Number"]]] += int(r["vd_registered"])
    assert set(base) == set(snap)
    ratios = [snap[w] / base[w] for w in snap]
    mean = sum(ratios) / len(ratios)
    sd = (sum((x - mean) ** 2 for x in ratios) / (len(ratios) - 1)) ** 0.5
    assert sd <= 0.07, sd


def test_the_committed_crosswalk_is_what_the_rule_makes_of_the_snapshot_and_assignment():
    snap, asg, rows = _snapshot(), _assignment(), _crosswalk_rows()
    copy = [{k: r[k] for k in ("VD_Number", "WardID_2026", "part_registered", "vd_registered")}
            for r in rows]
    build_concordance.apportion_roll(copy, snap, asg)
    assert [r["part_registered_2026"] for r in copy] == [r["part_registered_2026"] for r in rows]


def test_one_vds_assigned_ward_moves_those_two_wards_and_nothing_else():
    """(2) IT CAN SEE, on the real parts: one split VD moved to its other ward."""
    snap, asg, rows = _snapshot(), _assignment(), _crosswalk_rows()
    parts_of: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        parts_of[r["VD_Number"]].add(r["WardID_2026"])
    vd = sorted(v for v, w in parts_of.items() if len(w) > 1
                and any(int(r["vd_registered"]) > 0 for r in rows if r["VD_Number"] == v))[0]
    other = sorted(parts_of[vd] - {asg[vd]})[0]

    def run(assignment):
        copy = [{k: r[k] for k in ("VD_Number", "WardID_2026", "part_registered", "vd_registered")}
                for r in rows]
        build_concordance.apportion_roll(copy, snap, assignment)
        return [r["part_registered_2026"] for r in copy]

    base = run(asg)
    moved = run({**asg, vd: other})
    changed = {rows[i]["WardID_2026"] for i in range(len(rows)) if moved[i] != base[i]}
    assert {asg[vd], other} <= changed
    # nothing else: every changed row belongs to a VD of one of the two wards
    touched = {asg[vd], other}
    for i in range(len(rows)):
        if moved[i] != base[i]:
            assert rows[i]["WardID_2026"] in touched
    assert run(asg) == base, "and it goes quiet again"


# --------------------------------------------------------------------------
# one definition
# --------------------------------------------------------------------------

def test_target_roll_and_run_model_read_the_same_roll():
    """`pools._target_roll` keys by WardID, `montecarlo.ward_parts` (which
    `run_model` calls) by ward number; the mapping is taken from the file."""
    ids = {r["Ward_2026"]: r["WardID_2026"] for r in _crosswalk_rows()}
    with _target("2026") as target:
        parts, _ = M.ward_parts(target, ELECTIONS, target.processed)
        pooled = pools._target_roll(target.city, target)
    run_model_side = {ids[w]: n for w, n in _ward_totals(parts).items()}
    assert set(run_model_side) == set(pooled)
    assert all(abs(pooled[w] - run_model_side[w]) < 0.5 for w in pooled)
    assert {w: int(n) for w, n in pooled.items()} == _snapshot()


def test_pools_vd_map_registration_comes_from_the_same_reader():
    """`vd_map` for the unheld year sums each VD's reader parts."""
    with _target("2026") as target:
        _ward_of, reg = pools.vd_map(target.city, "2026")
    want: dict[str, float] = defaultdict(float)
    for r in _crosswalk_rows():
        want[r["VD_Number"].strip()] += int(r["part_registered_2026"])
    assert reg == dict(want)


def test_expected_ward_shares_reads_the_crosswalk_not_the_snapshot_directly():
    import build_make
    with _target("2026") as target:
        wards = sorted({r["Ward_2026"] for r in _crosswalk_rows()}, key=int)
        e0, prov = build_make.expected_ward_shares(target.city, "2026", wards)
        assert prov["roll"] == inputs_preflight.declared_roll_snapshot("joburg", "2026")
        rows = _crosswalk_rows()
        w0 = wards[0]
        for r in rows:
            if r["Ward_2026"] == w0:
                r["part_registered_2026"] = str(2 * int(r["part_registered_2026"]))
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            _write(d / "vd_ward_2026.csv", rows)
            e1, _ = build_make.expected_ward_shares(target.city, "2026", wards, processed=d)
            _write(d / "vd_ward_2026.csv", rows, drop=("roll_snapshot",))
            try:
                build_make.expected_ward_shares(target.city, "2026", wards, processed=d)
            except build_make.MakeBuildError as exc:
                assert "declares no registration snapshot" in str(exc)
            else:
                raise AssertionError("a crosswalk that declares no snapshot was accepted")
    assert e1[w0] > e0[w0]


# --------------------------------------------------------------------------
# the key and the preflight
# --------------------------------------------------------------------------

def test_the_preflight_calls_the_roll_used_only_when_the_crosswalk_declares_it():
    snap = inputs_preflight.roll_snapshot("joburg")
    row = {r["input"]: r for r in inputs_preflight._rows("joburg", "2026")}[
        "2026 voters' roll (registration)"]
    assert row["used"] is True
    rows = _crosswalk_rows()
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "vd_ward_2026.csv"
        _write(p, rows, drop=("roll_snapshot",))
        assert inputs_preflight.declared_roll_snapshot("joburg", "2026", p) is None
        _write(p, rows)
        assert inputs_preflight.declared_roll_snapshot("joburg", "2026", p) \
            == inputs_preflight.snapshot_label(snap)


# --------------------------------------------------------------------------
# backtests do not see any of it
# --------------------------------------------------------------------------

def test_a_held_election_never_opens_the_crosswalk():
    """2021 resolves its wards from its own result file. The crosswalk reader is
    replaced by one that raises; `ward_parts`, `_target_roll` and `vd_map` for
    2021 must still return, and return what they return with it in place."""
    with _target("2021") as target:
        before = (M.ward_parts(target, ELECTIONS, target.processed),
                  pools._target_roll(target.city, target),
                  pools.vd_map(target.city, "2021"))
        real = M.read_ward_crosswalk

        def _boom(*a, **k):
            raise AssertionError("a backtest opened the 2026 crosswalk")

        M.read_ward_crosswalk = _boom
        try:
            after = (M.ward_parts(target, ELECTIONS, target.processed),
                     pools._target_roll(target.city, target),
                     pools.vd_map(target.city, "2021"))
        finally:
            M.read_ward_crosswalk = real
    assert after == before
    assert before[0][0] and before[1] and before[2][0]


if __name__ == "__main__":
    run_module(globals())
