"""A SPEC CARRIES ONE ROLL: `pool_shares_at_target` AND THE PROVENANCE COME FROM
THE VECTOR THE POOLS ARE SIZED FROM.

`pools[g].registered` is `registered_at_target` (the counted roll split by ward
composition). `pool_shares_at_target` and the provenance phrase used to come
from `projected_pool_shares`, a 2024 roll carried forward, so one 2026 spec
held two rolls and `build_play` showed the second as "Registered".

0. RIGHT THING: the source of `emit_pools` is read for the calls that derive the
   shares; the population is that one function.
1. IT LOOKED: the function's source is non-empty and contains the sizing call.
2. IT CAN SEE: a source with the old derivation put back is flagged
   (`test_the_detector_sees_the_old_derivation`).
3. CONSTRUCTED: the shares are computed from a constructed vector.
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module  # noqa: E402

import numpy as np  # noqa: E402
import pools  # noqa: E402


def test_shares_are_the_registered_vector_normalised():
    reg = np.array([100.0, 300.0, 600.0])
    shares, note = pools.pool_shares_of_roll(reg, "2026")
    assert np.allclose(shares, [0.1, 0.3, 0.6])
    assert abs(shares.sum() - 1.0) < 1e-12
    assert "carried" not in note and "2024" not in note, note
    assert "2026 roll" in note


def test_an_empty_roll_is_refused():
    try:
        pools.pool_shares_of_roll(np.zeros(3), "2026")
    except SystemExit:
        return
    raise AssertionError("a roll of zero registered voters was not refused")


def _derives_from_one_roll(src: str) -> list[str]:
    problems = []
    if "pool_shares_of_roll(registered" not in src:
        problems.append("emit_pools does not derive the shares from `registered`")
    if "= projected_pool_shares(" in src:
        problems.append("emit_pools still derives the shares from projected_pool_shares")
    return problems


def test_emit_pools_derives_the_shares_from_the_registered_vector():
    src = inspect.getsource(pools.emit_pools)
    assert len(src) > 1000, "scanned the wrong object"
    assert "pool_shares_at_target" in src
    assert _derives_from_one_roll(src) == []


def test_the_detector_sees_the_old_derivation():
    src = inspect.getsource(pools.emit_pools)
    old = src.replace("pool_shares_of_roll(registered, target.year)",
                      "projected_pool_shares(series, target.year)")
    assert old != src
    assert len(_derives_from_one_roll(old)) == 2


if __name__ == "__main__":
    run_module(globals())
