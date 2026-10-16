"""Turnout changes the vote (owner decision, 2026-10-16).

The draw makes the preliminary vote at the reference turnout; each district's
vote is its registration times each pool's composition, turnout and split; the
citywide vote is the sum of the districts' votes and nothing re-pins it to the
preliminary vote. Pre-registration `prereg/2026-10-16-turnout-enters-the-vote.md`
P7; MODEL-LOG §1.315 for the three locks this removed.

EVERY INPUT IS CONSTRUCTED in this file, not read from `data/`: two pools A and
B (100 registered each), two parties X and Y, two districts each half A and
half B with flat geography, a zero-width record, pool split
R = [[0.8, 0.2], [0.1, 0.9]], reference turnout 0.5 for both pools. The test
drives the production pieces in run_model's order: `make_drawer` (pool_spec,
the calibration pass, the preliminary vote and the pool split), the drawer's
`pool_turnouts`, `reference_district_turnout`, `drawn_district_turnout`,
`district_frame` and `realise_draw` (the map at reference weights and the
district votes).

The four-part rule (CLAUDE.md §4): the checked set is every party's citywide
share, both districts' votes and both wards' tallies, asserted equal to the
universe; the baseline is 0.45 within 1e-9 on both sides; each of the three
locks put back by hand (κ calibrated over drawn turnout, the pool votes taken
from the band, the citywide share solved back to the preliminary vote) turns
`test_a_pool_turnout_drop_moves_the_citywide_vote` red, and reverting turns it
green (recorded in MODEL-LOG with the values each mutation gave).
"""

from __future__ import annotations

import contextlib
import copy
import io
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import montecarlo as M  # noqa: E402

PARTIES = ("X", "Y")
R = np.array([[0.8, 0.2], [0.1, 0.9]])
CENTRES = {"X": 0.45, "Y": 0.55}
ZERO_WIDTH = {"kind": "fit",
              "curve": {"a": 0.0, "b": 0.0, "log_mid": math.log(0.1), "k": 1.0},
              "delta": 0.0, "location": {"c1": 0.0, "c2": 0.0},
              "rho": {"lo": 0.0, "hi": 0.0},
              "delta_by_class": {"anchored": {"delta": 0.0, "source": "fit"},
                                 "unanchored": {"delta": 0.0, "source": "fit"}}}


def members():
    """Pool membership weights whose pool_spec seed IS R: w_gp ∝ R_gp / c_p,
    normalised per party. R already satisfies both margins (rows sum to one;
    50·0.8 + 50·0.1 = 45 of 100 reference votes for X), so the IPF leaves it."""
    raw = {g: {p: R[i, j] / CENTRES[p] for j, p in enumerate(PARTIES)}
           for i, g in enumerate("AB")}
    out = {g: {} for g in "AB"}
    for p in PARTIES:
        tot = sum(raw[g][p] for g in "AB")
        for g in "AB":
            out[g][p] = raw[g][p] / tot
    return out


def scenario(band_a=0.5):
    """``band_a`` is pool A's turnout (a degenerate band: the scenario's turnout,
    lo = mode = hi); the reference stays 0.5 for both pools."""
    w = members()
    sc = copy.deepcopy(M.DEFAULTS)
    sc["pools"] = {
        "A": {"members": w["A"], "registered": 100.0,
              "turnout": [band_a, band_a, band_a], "alpha": 1.0},
        "B": {"members": w["B"], "registered": 100.0,
              "turnout": [0.5, 0.5, 0.5], "alpha": 1.0},
    }
    sc["_turnout_reference"] = {"A": 0.5, "B": 0.5}
    sc["_theta_sd"] = {p: 0.3 for p in PARTIES}
    sc["entrant_prob"] = 0.0
    sc["draw_law"] = "universal"
    sc["_width"] = dict(ZERO_WIDTH)
    sc["_new_parties"] = []
    sc["_baseline_before_seeds"] = dict(CENTRES)
    sc["_strength_applied"] = []
    return sc


def one_draw(band_a=0.5, own_projection=True):
    """One draw through the production pieces, in run_model's order. Returns
    the citywide shares, each district's votes, each ward's tally (ward v is
    district v) and the universe."""
    index = {p: i for i, p in enumerate(PARTIES)}
    sc = scenario(band_a)
    with contextlib.redirect_stdout(io.StringIO()):
        drawer = M.make_drawer(sc, dict(CENTRES), dict(CENTRES), index,
                               M.DrawStreams("fixture|turnout|1", 4))
    pr_target = drawer(0)
    pools = list(drawer.turnout_pools)
    comp = np.array([[0.5, 0.5], [0.5, 0.5]])
    reg = np.array([100.0, 100.0])
    own = np.array([own_projection] * 2)
    # The district projection's centre: the pools' reference at this
    # composition (0.5); a district without one takes the pools' turnout.
    centre = np.array([0.5, 0.5])
    t_ref = np.array([drawer.pool_reference[g] for g in pools])
    turnout_ref, scale = M.reference_district_turnout(centre, own, comp, t_ref, reg)
    drawn = drawer.pool_turnouts(0)
    # The draw's district level, as run_model makes it with no noise: the
    # projection's centre (a pool band does not move it), or the pools'
    # reference applied equally where a district has no projection.
    level = np.where(own, centre, scale * (comp @ t_ref))
    turnout = M.drawn_district_turnout(level, comp, t_ref,
                                       [drawn[g] for g in pools])
    frame = M.district_frame(reg, comp, turnout_ref, np.array([0.45, 0.55]),
                             np.zeros((2, 2)), np.zeros((2, 2)), np.ones(2),
                             np.ones(2), None, None, M.DEFAULTS["level_floor"])
    pr_target, ward_target = M.ballot_targets(pr_target, np.ones(2),
                                              np.zeros(2, bool), np.zeros(2, bool))
    n, pr_mix, wd_mix = M.realise_draw(pr_target, ward_target, drawer.pool_split,
                                       turnout, frame)
    votes = (reg * n)[:, None] * pr_mix
    ward_tally = (reg * n)[:, None] * wd_mix
    city = votes.sum(axis=0) / votes.sum()
    return city, votes, ward_tally, list(index)


def test_the_baseline_returns_the_preliminary_vote_exactly():
    city, votes, ward, universe = one_draw(0.5)
    assert universe == list(PARTIES)
    assert city.shape == (len(PARTIES),)
    assert abs(city[0] - 0.45) < 1e-9 and abs(city[1] - 0.55) < 1e-9
    assert np.allclose(votes.sum(axis=1), [50.0, 50.0], atol=1e-9)
    assert np.allclose(ward, votes, atol=1e-9)


def test_a_pool_turnout_drop_moves_the_citywide_vote():
    """A's turnout 0.5 → 0.3: X = (2·50·0.3·0.8 + 2·50·0.5·0.1) / 80 = 0.3625."""
    city, votes, ward, universe = one_draw(0.3)
    checked = {p: city[i] for i, p in enumerate(universe)}
    assert set(checked) == set(PARTIES)
    assert abs(checked["X"] - 29 / 80) < 1e-9, checked
    assert abs(checked["Y"] - 51 / 80) < 1e-9, checked
    assert np.allclose(votes.sum(axis=1), [40.0, 40.0], atol=1e-9)
    assert np.allclose(ward[:, 0], [14.5, 14.5], atol=1e-9)
    assert np.allclose(ward[:, 1], [25.5, 25.5], atol=1e-9)


def test_a_citywide_only_turnout_matches_the_pool_arithmetic():
    """No district projection: the pools' turnout applied equally gives the
    pool arithmetic Σ reg_g T_g R_gp / Σ reg_g T_g, and each district's
    tally scales with its pools' turnout."""
    city, votes, ward, _u = one_draw(0.3, own_projection=False)
    T = np.array([0.3, 0.5])
    hand = (100 * T) @ R / (100 * T).sum()
    assert np.allclose(city, hand, atol=1e-9), (city, hand)
    assert np.allclose(votes.sum(axis=1), [40.0, 40.0], atol=1e-9)


def test_the_pool_split_is_exact_at_the_reference_and_keeps_rows_whole():
    """`district_split` on a constructed mixed district: the map's shares
    come back exactly at the reference composition, and each pool's row sums
    to one; a party in no pool is carried by every pool."""
    share = np.array([[0.45, 0.50, 0.05]])
    seed = np.array([[0.8, 0.2, 0.0], [0.1, 0.9, 0.0]])
    q = np.array([[0.5, 0.5]])
    st: dict = {}
    pi = M.district_split(share, seed, q, st)
    assert np.allclose(np.einsum("vg,gvp->vp", q, pi), share, atol=1e-12)
    assert np.allclose(pi.sum(axis=2), 1.0, atol=1e-6)
    assert (pi[:, 0, 2] > 0).all()
    assert st["calls"] == 1 and st["rounds"] >= 1
