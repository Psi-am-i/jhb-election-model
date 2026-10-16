"""A party with no national geography is placed by its pool vector, and the
placement survives to ``dev``.

``montecarlo.place_by_pool`` wrote ``max(place * base_city, SHARE_FLOOR)`` and
the deviation was then clipped at ``SHARE_FLOOR`` too. Every such party at
Johannesburg 2026 has a citywide base under that floor, so every district got
the floor and ``dev`` was 0 everywhere: the fitted pool vector was computed and
erased (MODEL-LOG, 2026-10-15). Constructed inputs only, except the last test,
which runs the model in process and writes nothing.

    ./.venv/bin/python tests/test_pool_placement.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module  # noqa: E402

import montecarlo as M  # noqa: E402

LEVEL = M.DEFAULTS["level_floor"]
# Three districts: pool "a" is large in the first, small in the last.
VD_POOL = {"v1": {"a": 0.8, "b": 0.2}, "v2": {"a": 0.5, "b": 0.5},
           "v3": {"a": 0.1, "b": 0.9}}


def _place(base, floor=LEVEL, weights=None):
    sh: dict = {v: {} for v in VD_POOL}
    placed = M.place_by_pool(sh, ["SEED"], {"SEED": {"a": 1.0} if weights is None else weights},
                             {"SEED": base}, VD_POOL, floor)
    return sh, placed


def _dev(sh, base, placed):
    vds = sorted(sh)
    local = np.array([[sh[v].get("SEED", 0.0)] for v in vds])
    cols = [0] if placed else []
    return M.placement_deviation(local, np.array([base]), cols, LEVEL)[:, 0]


def test_a_small_seeded_party_has_geography():
    """Base 0.001 is under SHARE_FLOOR; the party must still follow its pool."""
    assert 0.001 < M.SHARE_FLOOR, "premise: the base is under the old floor"
    sh, placed = _place(0.001)
    dev = _dev(sh, 0.001, placed)
    assert dev[0] > dev[1] > dev[2], f"geography lost or reordered: {dev}"
    assert np.ptp(dev) > 1.0, f"geography is flat: {dev}"
    assert abs(sh["v1"]["SEED"] - 0.8 * 0.001) < 1e-12, "placed value changed"


def test_the_old_floor_flattens_it():
    """Mutation: restoring `max(.., SHARE_FLOOR)` and the old clip is red."""
    sh, placed = _place(0.001, floor=M.SHARE_FLOOR)
    local = np.array([[sh[v]["SEED"]] for v in sorted(sh)])
    old = M.placement_deviation(local, np.array([0.001]), [], LEVEL)[:, 0]
    assert np.allclose(old, 0.0), "the old path should read as flat"
    new = _dev(*_place(0.001)[:1], 0.001, placed)
    assert not np.allclose(new, 0.0), "the fixed path is flat (detector blind)"


def test_a_party_with_a_national_record_is_unchanged():
    """Its column is clipped at SHARE_FLOOR exactly as before, byte for byte."""
    rng = np.random.default_rng(1)
    local = rng.uniform(0.0, 0.2, size=(40, 3))
    local[:, 1] = rng.uniform(0.0, 0.003, size=40)      # straddles the floor
    local[:, 2] = rng.uniform(0.0, 0.0015, size=40)
    base = np.array([0.1, 0.0015, 0.0008])
    old = M.logit(local) - M.logit(base)[None, :]
    new = M.placement_deviation(local, base, [], LEVEL)
    assert np.array_equal(old, new), "a national-record column moved"
    mixed = M.placement_deviation(local, base, [2], LEVEL)
    assert np.array_equal(old[:, :2], mixed[:, :2]), \
        "pool-placing one party moved another party's column"
    assert not np.array_equal(old[:, 2], mixed[:, 2])


def test_a_party_with_no_pool_weights_is_not_placed():
    sh, placed = _place(0.001, weights={})
    assert not placed and all("SEED" not in d for d in sh.values())


def test_the_ward_mask_zeroes_a_party_outside_its_wards_and_still_hits_its_target():
    base = np.array([0.6, 0.39, 0.01])
    target = np.array([0.6, 0.39, 0.01])
    dev = np.zeros((4, 3))
    mask = np.ones((4, 3))
    mask[2:, 2] = 0.0                       # party 3 stands in VDs 0 and 1 only
    out = M.solve_and_predict(dev, base, target, np.ones(3), np.ones(4),
                              mask=mask)
    assert (out[2:, 2] == 0).all(), "share outside the party's wards"
    assert np.allclose(out.sum(axis=1), 1.0)
    assert abs(out[:, 2].mean() - 0.01) < 1e-5, "citywide target missed"
    assert out[0, 2] > 0.015, "target was not concentrated on its wards"


def test_joburg_2026_pool_placed_parties_are_not_flat():
    """In process, 40 draws, nothing written: the wiring from run_model to dev."""
    import cityconfig
    from test_chain import TARGET, _Args, _city
    _city()
    seen = {}
    real = M.placement_deviation

    def spy(local, base_city, cols, floor):
        out = real(local, base_city, cols, floor)
        seen.update(dev=out, cols=list(cols), n=local.shape[1])
        return out

    M.placement_deviation = spy
    try:
        scenario = M.load_scenario(_Args(draws=40))
        M.run_model(cityconfig.use_target(TARGET), scenario, verbose=False,
                    stop_after="drawer_inputs")
    finally:
        M.placement_deviation = real
    placed = seen["cols"]
    if not placed:
        return
    ranges = np.ptp(seen["dev"][:, placed], axis=0)
    assert (ranges > 0).any(), "every pool-placed party is still flat"


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
