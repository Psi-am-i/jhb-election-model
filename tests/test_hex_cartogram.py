"""The hex cartogram must be honest about seats, and must be the same object
as the geographic map.

``src/hex_cartogram.py`` exists because of a measured defect in the geographic
choropleth: ward area carries no information -- every ward returns exactly one
councillor -- but area is what the eye reads, and Johannesburg's ward areas
are wildly unequal in a way that correlates with party. The DA's wards are
large, low-density and northern; the ANC's and MK's are small and dense.

So the headline test here is not "the SVG parses". It is the distortion table
itself, recomputed from the *emitted* polygons rather than from the layout the
code believes it produced: group the drawn ink by predicted winner and demand
that every party's share of it equals its share of the 135 seats. And -- so
that the test cannot pass by measuring nothing -- the same instrument is run
over the real ward polygons in the same test, where it must *fail*
proportionality by a wide margin. A measurement that cannot detect the defect
it was written for is not a measurement.

The second thing under test is drift. The cartogram borrows the geographic
map's colours by importing them, which cannot drift; it cannot borrow the four
confidence tiers, because those are inline in ``render_map.main``. Those are
checked against that module's source text instead.

Run:
    ./.venv/bin/python tests/test_hex_cartogram.py
    ./.venv/bin/python -m pytest tests/test_hex_cartogram.py -q
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import numpy as np  # noqa: E402

PATHS = ROOT / "data" / "processed" / "ward_paths.json"
PROBS = ROOT / "data" / "processed" / "ward_winner_probs.csv"

# How far a hexagon may sit from its ward's true centroid before the layout has
# stopped being a map. Expressed in hex radii so it does not move with the
# figure's size. Declared, not derived -- JUDGEMENT-CALLS.md.
MAX_DISPLACEMENT_RADII = 5.0

_CELL = re.compile(r'<polygon id="hexcell" points="([^"]+)"')
_USE = re.compile(r'<use href="#(\w+)"[^>]*?data-tip="([^"]*)"')


def _inputs():
    if not PATHS.exists() or not PROBS.exists():
        skip(f"needs {PATHS.name} and {PROBS.name}; run render_map.py and a "
             f"Monte Carlo first")
    ward_paths = json.loads(PATHS.read_text(encoding="utf-8"))
    with PROBS.open(encoding="utf-8", newline="") as fh:
        probs = {r["ward"]: r for r in csv.DictReader(fh)}
    return ward_paths, probs


def _shoelace(pts):
    a = 0.0
    for i in range(len(pts)):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % len(pts)]
        a += x0 * y1 - x1 * y0
    return abs(a) / 2.0


def _drawn_tiles(svg: str):
    """Every ward tile the SVG actually draws: (ward number, drawn area).

    Reads the emitted markup, not the layout object, so a renderer that scaled
    or dropped a hexagon is caught. The tiles are ``<use>`` references to a
    single ``#hexcell`` polygon, so the area is measured off that polygon and
    every reference to it is checked -- a ``<use>`` pointing at some other
    shape, or carrying a ``transform`` that would rescale it, fails here. Hatch
    overlays carry no ``data-tip`` and are therefore not counted twice.
    """
    cells = _CELL.findall(svg)
    assert len(cells) == 1, f"expected one #hexcell definition, found {len(cells)}"
    pts = [tuple(float(v) for v in p.split(",")) for p in cells[0].split()]
    area = _shoelace(pts)
    for tag in re.findall(r"<use\b[^>]*>", svg):
        assert "transform=" not in tag, f"a transform could rescale a tile: {tag}"
    out = []
    for ref, tip in _USE.findall(svg):
        assert ref == "hexcell", f"tile references #{ref}, not #hexcell"
        out.append((re.match(r"Ward (\S+)", tip).group(1), area))
    return out


# --------------------------------------------------------------------------
# the headline
# --------------------------------------------------------------------------

def test_the_cartogram_ink_is_proportional_to_seats():
    """Every party's share of the drawn ink equals its share of the seats.

    This is the whole point of the exercise. The tolerance is 1e-9, not a
    percentage point: the hexagons are identical by construction, so anything
    that moves this at all is a bug, not a rounding difference.

    The same instrument is then pointed at the geographic map's real ward
    polygons, where the DA must come out at well over 1.4x its seat share --
    otherwise the check above is measuring nothing and would pass on a broken
    renderer.
    """
    import hex_cartogram as hc

    ward_paths, probs = _inputs()
    layout = hc.build_layout(ward_paths)
    svg = hc.render(layout, probs)

    drawn = _drawn_tiles(svg)
    assert len(drawn) == len(probs), f"{len(drawn)} tiles for {len(probs)} wards"
    areas = {ward: area for ward, area in drawn}
    after = hc.ink_table(areas, probs)
    for party, row in after.items():
        assert abs(row["distortion"] - 1.0) < 1e-9, (
            f"{party}: {row['ink_share']:.6f} of the ink for "
            f"{row['seat_share']:.6f} of the seats ({row['distortion']:.4f}x)")

    before = hc.ink_table(layout.areas, probs)
    assert before["DA"]["distortion"] > 1.4, (
        "the geographic map is supposed to over-draw the DA badly; this "
        f"instrument reports {before['DA']['distortion']:.2f}x, so it is not "
        "measuring what the cartogram was built to fix")
    assert before["MK"]["distortion"] < 0.4, (
        f"MK under-drawn by only {before['MK']['distortion']:.2f}x")


# --------------------------------------------------------------------------
# the layout is a layout
# --------------------------------------------------------------------------

def test_every_ward_appears_exactly_once():
    import hex_cartogram as hc

    ward_paths, probs = _inputs()
    layout = hc.build_layout(ward_paths)
    assert sorted(layout.cells) == sorted(ward_paths["paths"])
    tips = [w for w, _ in _drawn_tiles(hc.render(layout, probs))]
    assert sorted(tips) == sorted(ward_paths["paths"])
    assert len(set(tips)) == len(tips)


def test_no_two_wards_share_a_cell():
    import hex_cartogram as hc

    ward_paths, _ = _inputs()
    layout = hc.build_layout(ward_paths)
    cells = [(round(x, 6), round(y, 6)) for x, y in layout.cells.values()]
    assert len(set(cells)) == len(cells)


def test_every_hexagon_is_identical_and_none_overlap():
    """Equal tiles is the claim; equal tiles that overlap would still lie."""
    import hex_cartogram as hc

    ward_paths, probs = _inputs()
    layout = hc.build_layout(ward_paths)
    svg = hc.render(layout, probs)
    areas = [a for _, a in _drawn_tiles(svg)]
    assert max(areas) - min(areas) == 0.0, "hexagons differ in size"
    ideal = 1.5 * math.sqrt(3.0) * layout.radius ** 2
    # the shared shape is written to six decimals, so it is the ideal
    # hexagon to within the rounding of one coordinate, not to the bit
    assert abs(areas[0] - ideal) / ideal < 1e-6, (areas[0], ideal)

    pts = np.array(list(layout.cells.values()))
    d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
    np.fill_diagonal(d, np.inf)
    pitch = math.sqrt(3.0) * layout.radius
    assert d.min() > pitch - 1e-6, f"cells {d.min():.3f}px apart, pitch {pitch:.3f}px"


def test_each_hexagon_sits_near_its_real_ward():
    """A cartogram that has stopped being a map is a bar chart in disguise."""
    import hex_cartogram as hc

    ward_paths, _ = _inputs()
    layout = hc.build_layout(ward_paths)
    disp = layout.displacements() / layout.radius
    worst = max(zip(disp, layout.cells), key=lambda t: t[0])
    assert worst[0] < MAX_DISPLACEMENT_RADII, (
        f"ward {worst[1]} is {worst[0]:.1f} hex radii from its centroid")


# --------------------------------------------------------------------------
# determinism
# --------------------------------------------------------------------------

def test_the_svg_is_byte_identical_on_a_rebuild():
    import hex_cartogram as hc

    ward_paths, probs = _inputs()
    a = hc.render(hc.build_layout(ward_paths), probs)
    b = hc.render(hc.build_layout(json.loads(PATHS.read_text(encoding="utf-8"))), probs)
    assert a == b, "the cartogram is not deterministic"
    assert a.encode("utf-8") == b.encode("utf-8")


def test_the_greedy_layout_is_deterministic_too():
    import hex_cartogram as hc

    ward_paths, _ = _inputs()
    a = hc.build_layout(ward_paths, method="greedy").cells
    b = hc.build_layout(ward_paths, method="greedy").cells
    assert a == b


# --------------------------------------------------------------------------
# the assignment algorithm
# --------------------------------------------------------------------------

def test_the_assignment_matches_brute_force():
    """The Jonker-Volgenant implementation, against every permutation.

    scipy is not installed in this venv, so ``linear_sum_assignment`` had to be
    written out. Forty lines of potentials and augmenting paths is exactly the
    kind of code that is subtly wrong and still looks plausible on a real map,
    so it is checked against exhaustive search on small rectangular matrices.
    """
    import hex_cartogram as hc

    rng = random.Random(20260823)
    for n, m in ((1, 1), (2, 3), (3, 3), (4, 6), (5, 5), (6, 9)):
        for _ in range(12):
            cost = np.array([[rng.randrange(0, 20) for _ in range(m)]
                             for _ in range(n)], dtype=float)
            got = hc.assign_optimal(cost)
            assert len(set(got.tolist())) == n
            mine = cost[np.arange(n), got].sum()
            best = min(sum(cost[i][cols[i]] for i in range(n))
                       for cols in itertools.permutations(range(m), n))
            assert abs(mine - best) < 1e-9, f"{mine} vs optimum {best}\n{cost}"


def test_the_assignment_beats_greedy_on_the_real_city():
    """The reason ``optimal`` is the default and ``greedy`` is only kept."""
    import hex_cartogram as hc

    ward_paths, _ = _inputs()
    opt = hc.build_layout(ward_paths, method="optimal").displacements()
    greedy = hc.build_layout(ward_paths, method="greedy").displacements()
    assert opt.mean() < greedy.mean()
    assert opt.max() < greedy.max()


def test_the_assignment_refuses_more_wards_than_cells():
    import hex_cartogram as hc

    try:
        hc.assign_optimal(np.zeros((4, 3)))
    except ValueError:
        return
    raise AssertionError("assigned 4 wards to 3 cells without complaint")


# --------------------------------------------------------------------------
# one visual language, two maps
# --------------------------------------------------------------------------

def test_the_two_maps_agree_on_the_confidence_tiers():
    """The tiers are inline in ``render_map.main`` and cannot be imported.

    So they are read out of its source. If someone retunes the geographic map's
    thresholds, this fails until the cartogram is retuned with it -- which is
    the only thing standing between "the same object drawn two ways" and two
    maps that quietly disagree about which wards are safe.
    """
    import hex_cartogram as hc
    import render_map

    src = (ROOT / "src" / "render_map.py").read_text(encoding="utf-8")
    for label, value in (("safe", hc.SAFE), ("strong", hc.STRONG), ("lean", hc.LEAN)):
        assert re.search(rf"pw >= {value:.2f}\b", src), (
            f"render_map no longer thresholds {label} at {value}; "
            f"hex_cartogram.{label.upper()} is stale")
    assert re.search(rf"v >= {hc.TIP_FLOOR:.2f}\b", src), "tooltip floor drifted"
    assert re.search(rf"other >= {hc.OTHER_FLOOR:.3f}\b", src), "other floor drifted"
    assert hc.CHIPS is render_map.CHIPS and hc.NAMES is render_map.NAMES
    assert hc.GREY == render_map.GREY


def test_the_markers_do_not_collide_with_the_geographic_map():
    import hex_cartogram as hc
    import render_map

    for a, b in ((hc.MARK_START, render_map.MARK_START),
                 (hc.MARK_END, render_map.MARK_END)):
        assert a != b and a not in b and b not in a, f"{a!r} collides with {b!r}"


def test_the_tooltip_names_every_party_above_five_percent():
    """Same content as the geographic map's: winner, verdict, every party at
    >= 5% of simulations, and an ``other`` remainder."""
    import hex_cartogram as hc

    _, probs = _inputs()
    checked = 0
    for ward, row in probs.items():
        entries = [(c.split(":")[0], float(c.split(":")[1]))
                   for c in row["dist"].split("|")]
        tip = hc.classify(row)["tip"]
        assert tip.startswith(f"Ward {ward} · ")
        for party, share in entries:
            named = hc.NAMES.get(party, party.title())
            if share >= hc.TIP_FLOOR:
                assert f"{named} {share:.0%}" in tip, f"ward {ward}: {named} missing"
                checked += 1
        other = sum(v for _, v in entries if v < hc.TIP_FLOOR)
        assert (f"other {other:.0%}" in tip) == (other >= hc.OTHER_FLOOR)
    assert checked > 200, "too few parties exercised to mean anything"


def test_the_four_tiers_are_all_exercised_and_grey_is_reserved_for_tossups():
    import hex_cartogram as hc

    _, probs = _inputs()
    seen = {}
    for row in probs.values():
        info = hc.classify(row)
        seen[info["cls"]] = seen.get(info["cls"], 0) + 1
        if info["cls"] == "grey":
            assert float(row["p_win"]) < hc.LEAN
            assert info["fill"] == hc.GREY
        else:
            assert float(row["p_win"]) >= hc.LEAN
    assert set(seen) == {"solid", "strong", "lean", "grey"}, seen


# --------------------------------------------------------------------------
# the geometry helpers
# --------------------------------------------------------------------------

def test_the_path_parser_recovers_a_known_area_and_hole():
    """A 10x10 square with a 4x4 hole: area 84, centroid still at the centre."""
    import hex_cartogram as hc

    outer = "M0.0 0.0L10.0 0.0L10.0 10.0L0.0 10.0Z"
    hole = "M3.0 3.0L3.0 7.0L7.0 7.0L7.0 3.0Z"
    area, cx, cy = hc.polygon_area_centroid(outer + hole)
    assert abs(area - 84.0) < 1e-9, area
    assert abs(cx - 5.0) < 1e-9 and abs(cy - 5.0) < 1e-9
    area, _, _ = hc.polygon_area_centroid(outer)
    assert abs(area - 100.0) < 1e-9


def test_a_hexagon_has_the_area_the_layout_thinks_it_has():
    import hex_cartogram as hc

    r = 24.6
    pts = hc.hex_vertices(11.0, -3.0, r)
    assert len(pts) == 6
    assert abs(_shoelace(pts) - 1.5 * math.sqrt(3.0) * r * r) < 1e-9


def test_the_hexagons_together_cover_about_the_real_city():
    """The tiles are sized so the cartogram sits on the geographic map's own
    footprint -- that is what makes a toggle between the two legible."""
    import hex_cartogram as hc

    ward_paths, _ = _inputs()
    layout = hc.build_layout(ward_paths)
    hex_total = 1.5 * math.sqrt(3.0) * layout.radius ** 2 * len(layout.cells)
    assert abs(hex_total / sum(layout.areas.values()) - 1.0) < 1e-9


if __name__ == "__main__":
    raise SystemExit(run_module(vars(sys.modules[__name__])))
