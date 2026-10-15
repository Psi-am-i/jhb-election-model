"""The owner's ward-contest rule (2026-10-15).

    "for people running only for a ward seat - a. they should be omitted from
    any citywide machinery and vote calculation b. their chances of a win
    should be within the specific ward they are contesting and no other."

Three properties, each with the detector shown to see a violation:

* every slated party, national record or not, has ward votes only in the wards
  it contests, and its citywide ward target is still met (``ballot_masks``,
  ``solve_and_predict(mask=)``);
* a ward-only party (a slate, no PR list) has zero list share everywhere and
  no list seat; its ward win leaves the pool through the D term
  (``ballot_masks``' PR mask, ``ballot_targets``, ``seats.eligible_parties``);
* there is one slate definition, ``levels.ballots``, read by ``levels`` and
  ``montecarlo`` alike.

Constructed inputs, except the last test, which runs the model in process to
the drawer seam and writes nothing. MODEL-LOG §1.306.

    ./.venv/bin/python tests/test_ward_contest_rule.py
"""

from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

import levels  # noqa: E402
import montecarlo as M  # noqa: E402
import seats as S  # noqa: E402

# Two wards of two districts each. The run keys wards by NUMBER, slates by
# WardID, as at an unheld target.
WARDS = ["1", "2"]
WARD_ID = {"1": "79800001", "2": "79800002"}
PART_VD = np.array([0, 1, 2, 3])
PART_WARD = np.array([0, 0, 1, 1])
NVD = 4
UNIVERSE = ["BIG", "NAT", "LISTONLY", "WARDONLY"]
WEIGHT = np.array([1000.0, 1000.0, 1000.0, 1000.0])


def _ballots(pr=frozenset({"BIG", "NAT", "LISTONLY"}), complete=True):
    """BIG everywhere; NAT (a national-record party) and WARDONLY in ward 1
    only; LISTONLY on the list ballot only."""
    wards = {"BIG": frozenset(WARD_ID.values()),
             "NAT": frozenset({"79800001"}),
             "WARDONLY": frozenset({"79800001"})}
    return levels.Ballots(
        wards=wards, pr=pr, parties=frozenset(UNIVERSE), complete=complete,
        ward_ballot=frozenset(WARD_ID.values()), source="declared")


def _masks(ballots=None, ward_id=WARD_ID):
    return M.ballot_masks(UNIVERSE, WARDS, ward_id, PART_VD, PART_WARD, NVD,
                          ballots or _ballots())


def _solve(target, mask, dev=None):
    dev = np.zeros((NVD, len(UNIVERSE))) if dev is None else dev
    base = np.array([0.7, 0.2, 0.05, 0.05])
    return M.solve_and_predict(dev, base, target, np.ones(len(UNIVERSE)),
                               WEIGHT, mask=mask)


# ---------------------------------------------------------------------------
# (a) a national-record party stands only where its slate says
# ---------------------------------------------------------------------------

def test_a_slated_national_party_has_no_ward_vote_outside_its_wards():
    m = _masks()
    nat, lo = UNIVERSE.index("NAT"), UNIVERSE.index("LISTONLY")
    assert "NAT" in m["masked"], "a national-record party was not masked"
    target = np.array([0.7, 0.2, 0.0, 0.1])
    out = _solve(target, m["ward_mask_vd"])
    assert (out[2:, nat] == 0).all(), f"NAT outside ward 1: {out[2:, nat]}"
    assert (out[:, lo] == 0).all(), "a list-only party has a ward vote"
    got = (WEIGHT / WEIGHT.sum()) @ out
    assert abs(got[nat] - 0.2) < 1e-5, f"NAT's ward target missed: {got[nat]}"
    assert out[0, nat] > 0.35, "the target was not met on its own wards"
    assert m["ward_absent"][lo] and not m["ward_absent"][nat]


def test_without_the_mask_the_party_leaks_outside_its_wards():
    """Detector: the same solve with no mask puts NAT in ward 2."""
    out = _solve(np.array([0.7, 0.2, 0.0, 0.1]), None)
    assert (out[2:, UNIVERSE.index("NAT")] > 0.1).all()


def test_a_partial_declaration_leaves_an_unnamed_party_unmasked():
    m = _masks(_ballots(complete=False))
    lo = UNIVERSE.index("LISTONLY")
    assert "LISTONLY" not in m["masked"]
    assert (m["ward_mask_vd"][:, lo] == 1).all()


def test_slates_in_another_key_space_refuse():
    """MODEL-LOG §1.306: WardIDs compared with ward numbers matched nothing
    and zeroed every masked party's ward ballot. Now it refuses."""
    try:
        _masks(ward_id={w: w for w in WARDS})
    except SystemExit as exc:
        assert "key spaces" in str(exc)
    else:
        raise AssertionError("ward numbers against WardID slates did not refuse")


def test_ward_ids_maps_the_crosswalk_number_to_its_id():
    import cityconfig
    cityconfig.use("joburg")
    t = cityconfig.use_target("2026")
    if not (t.crosswalk.parent / t.crosswalk.name).exists():
        return
    ids = M.ward_ids(t, ["1", "94"], t.crosswalk.parent)
    assert ids == {"1": "79800001", "94": "79800094"}, ids


# ---------------------------------------------------------------------------
# (b) a ward-only party is out of the citywide vote and has no list seat
# ---------------------------------------------------------------------------

def test_a_ward_only_party_has_no_list_share_and_no_list_seat():
    m = _masks()
    wo = UNIVERSE.index("WARDONLY")
    assert m["ward_only"] == ["WARDONLY"] and m["pr_absent"][wo]
    drawn = np.array([0.6, 0.2, 0.1, 0.1])
    ratio = np.array([1.0, 1.0, 0.0, 1.2])
    pr_t, ward_t = M.ballot_targets(drawn, ratio, m["pr_absent"],
                                    m["ward_absent"])
    assert pr_t[wo] == 0 and abs(pr_t.sum() - 1) < 1e-12
    others = [i for i in range(len(UNIVERSE)) if i != wo]
    assert np.allclose(pr_t[others], drawn[others] / drawn[others].sum()), \
        "the list mass was not returned pro rata"
    assert ward_t[wo] > 0, "the ward-only party lost its ward ballot"
    assert ward_t[UNIVERSE.index("LISTONLY")] == 0
    pr = _solve(pr_t, m["pr_mask_vd"])
    assert (pr[:, wo] == 0).all(), f"list share {pr[:, wo]}"
    wd = _solve(ward_t, m["ward_mask_vd"])
    pr_votes = {p: int(round(v)) for p, v in zip(UNIVERSE, WEIGHT @ pr)}
    ward_votes = {p: int(round(v)) for p, v in zip(UNIVERSE, WEIGHT @ wd)}
    combined = S.eligible_parties(ward_votes, pr_votes)
    assert "WARDONLY" not in combined
    c, d, pool = S.outside_pool_wards({"BIG": 1, "WARDONLY": 1}, combined)
    assert (c, d) == (0, 1) and "WARDONLY" not in pool
    alloc = S.allocate(combined, total_seats=10, no_pr_list_wards=d)
    assert alloc.seats.get("WARDONLY", 0) == 0
    assert sum(alloc.seats.values()) == 9


def test_without_the_pr_mask_a_ward_only_party_keeps_a_list_share():
    """Detector: a zero target alone leaves the floor's share in the column,
    so the PR mask is what makes the list share exactly zero."""
    m = _masks()
    wo = UNIVERSE.index("WARDONLY")
    pr_t, _w = M.ballot_targets(np.array([0.6, 0.2, 0.1, 0.1]),
                                np.ones(4), m["pr_absent"], m["ward_absent"])
    assert (_solve(pr_t, None)[:, wo] > 0).all()


def test_without_pr_lists_nobody_is_ward_only():
    m = _masks(_ballots(pr=None))
    assert m["ward_only"] == [] and m["pr_mask_vd"] is None


def test_a_pr_list_that_disagrees_with_the_roster_refuses():
    """A spelling in `pr` that is not in `parties` would make the real party
    ward-only and delete its list vote."""
    import cityconfig
    import pools
    cityconfig.use("joburg")
    t = cityconfig.use_target("2026")
    body = ('[roster]\nparties = ["ANC", "DA"]\npr = ["ANC", "DEMOCRATIC ALLAINCE"]\n'
            '[roster.wards]\n"ANC" = ["79800001"]\n')
    real = pools.lineage_path
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "x.toml"
        path.write_text(body)
        pools.lineage_path = lambda city, target: path
        try:
            try:
                pools.declared_roster(t.city, t)
            except SystemExit as exc:
                assert "DEMOCRATIC_ALLAINCE" in str(exc) and "'DA'" in str(exc)
            else:
                raise AssertionError("a misspelt PR list was accepted")
            path.write_text(body.replace("ALLAINCE", "ALLIANCE"))
            got = pools.declared_roster(t.city, t)
            assert got["pr"] == ["ANC", "DA"], got["pr"]
        finally:
            pools.lineage_path = real


def test_the_declared_2026_lists_cover_the_roster_both_ways():
    import cityconfig
    cityconfig.use("joburg")
    t = cityconfig.use_target("2026")
    b = levels.ballots(t, t.city)
    assert b.source == "declared" and b.pr is not None
    assert b.parties == frozenset(b.wards) | b.pr
    assert "UDM" in b.ward_only(), "a national-record ward-only party"
    assert "IND" not in b.ward_only()


# ---------------------------------------------------------------------------
# (c) one slate definition
# ---------------------------------------------------------------------------

def _slate_reads(tree: ast.AST) -> list[str]:
    """Functions that read slates other than through `levels.ballots`: a call
    to the result-file reader, or `declared_roster(...)` followed by
    `.get("wards")` / `["wards"]`."""
    hits = []
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and getattr(
                    node.func, "id", getattr(node.func, "attr", "")) in (
                    "_result_ballots", "_result_slates"):
                hits.append(fn.name)
            if (isinstance(node, ast.Call)
                    and getattr(node.func, "attr", "") == "get"
                    and node.args and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value == "wards"
                    and "declared_roster" in ast.unparse(node.func.value)):
                hits.append(fn.name)
    return hits


def test_levels_and_montecarlo_read_slates_only_through_ballots():
    population = {}
    for name in ("levels.py", "montecarlo.py", "inputs_preflight.py"):
        src = (ROOT / "src" / name).read_text(encoding="utf-8")
        population[name] = _slate_reads(ast.parse(src))
    assert population["levels.py"] == ["ballots"], population
    assert population["montecarlo.py"] == [], population
    assert population["inputs_preflight.py"] == [], population
    lv = (ROOT / "src" / "levels.py").read_text(encoding="utf-8")
    tree = ast.parse(lv)
    callers = {fn.name for fn in ast.walk(tree)
               if isinstance(fn, ast.FunctionDef)
               and any(isinstance(n, ast.Call) and getattr(n.func, "id", "") == "ballots"
                       for n in ast.walk(fn))}
    want = {"contestation", "declared_contestation", "slate_coverage",
            "unopposed_wards"}
    assert want <= callers, f"not reading levels.ballots: {want - callers}"
    mc = ast.unparse(ast.parse((ROOT / "src" / "montecarlo.py").read_text()))
    assert "_levels.ballots(target, target.city)" in mc


def test_the_slate_scan_sees_a_second_copy():
    """Detector: the copy montecarlo carried until §1.306 is caught, and the
    scan goes quiet on the same function without it."""
    copy = ('def run_model(target):\n'
            '    s = (pools.declared_roster(c, t) or {}).get("wards") or {}\n'
            '    w, seen = levels._result_slates(p)\n')
    assert _slate_reads(ast.parse(copy)) == ["run_model", "run_model"]
    clean = 'def run_model(target):\n    b = levels.ballots(target, c)\n'
    assert _slate_reads(ast.parse(clean)) == []


def test_run_model_and_slate_coverage_read_the_same_function():
    """In process to the drawer seam at Johannesburg 2026, nothing written.
    Both consumers must call `levels.ballots` for the target."""
    import inspect

    import cityconfig
    from test_chain import _Args
    cityconfig.use("joburg")
    t = cityconfig.use_target("2026")
    real = levels.ballots
    seen: list[tuple[str, str]] = []

    def spy(target, city):
        seen.append((inspect.stack()[1].function, str(target.year)))
        return real(target, city)

    levels.ballots = spy
    try:
        M.run_model(cityconfig.use_target("2026"), M.load_scenario(_Args(draws=4)),
                    verbose=False, stop_after="drawer_inputs")
    finally:
        levels.ballots = real
        cityconfig.use_target("2026")
    callers = {c for c, y in seen if y == "2026"}
    assert {"slate_coverage", "run_model"} <= callers, seen


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
