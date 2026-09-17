"""The map's stripes: who gets one, and what a toss-up ward's pattern looks like.

Owner, 2026-09-17, looking at the rendered map: ward 65 (IFP 49% · MK 49%)
showed what looked like four stripes, because two thin lines sat on grey ground
and the grey read as bands of its own. And a party winning a ward one time in
sixteen is not a contender worth drawing. No test read the map's patterns at
all before this one.

Inputs are CONSTRUCTED shares; nothing depends on today's forecast.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import render_map as M  # noqa: E402


def _bands(svg: str) -> list[tuple[float, float, str]]:
    """(centre x, width, colour) for every line in a pattern."""
    return [(float(x), float(w), c) for x, c, w in re.findall(
        r'<line x1="([\d.]+)"[^>]*stroke="([^"]+)" stroke-width="([\d.]+)"', svg)]


def test_one_in_ten_is_drawn_and_one_in_sixteen_is_not():
    entries = [("ANC", 0.55), ("EFF", 0.10), ("PA", 0.0625), ("DA", 0.28)]
    got = [c for c, _ in M.stripe_parties(entries, winner="ANC")]
    assert got == ["DA", "EFF"], got
    # the rule is the threshold, not the slot count: drop it and PA appears
    old = M.STRIPE_MIN
    try:
        M.STRIPE_MIN = 0.05
        assert "PA" in [c for c, _ in M.stripe_parties(entries, winner="ANC", limit=3)]
    finally:
        M.STRIPE_MIN = old


def test_a_two_way_toss_up_is_two_equal_bands_with_no_ground_showing():
    pid, svg = M.toss_pattern([("IFP", 0.49), ("MK", 0.49)])
    bands = _bands(svg)
    assert len(bands) == 2, bands                        # one band per party
    assert {c for *_, c in bands} == {M.CHIPS["IFP"], M.CHIPS["MK"]}
    widths = [w for _, w, _ in bands]
    assert abs(widths[0] - widths[1]) < 0.01, widths     # equal shares, equal bands
    # the bands tile the step exactly: left edge 0, right edge 7, no gap
    edges = sorted((x - w / 2, x + w / 2) for x, w, _ in bands)
    assert abs(edges[0][0]) < 0.01 and abs(edges[-1][1] - 7.0) < 0.01, edges
    assert abs(edges[0][1] - edges[1][0]) < 0.01, edges


def test_a_three_way_toss_up_is_banded_in_proportion():
    _, svg = M.toss_pattern([("ANC", 0.45), ("DA", 0.35), ("EFF", 0.20)])
    widths = [w for _, w, _ in _bands(svg)]
    assert [round(w / 7.0, 2) for w in widths] == [0.45, 0.35, 0.20], widths


def test_fewer_than_two_contenders_draws_nothing():
    assert M.toss_pattern([("ANC", 0.55)]) is None
    assert M.toss_pattern([]) is None


def test_an_unknown_party_is_never_grey_on_grey():
    _, svg = M.toss_pattern([("SOMEBODY_NEW", 0.5), ("ANC", 0.5)])
    assert M.GREY not in svg, svg
