"""A rate the ward arithmetic forbids must never leave the fit.

``pools.bounds`` is the Duncan-Davis method of bounds: no model, no estimate,
just the interval each party's rate in each pool can arithmetically lie in
given the ward table. It has been computed on every fit since the joint fit was
written — and it was read at exactly one place, ``PartyFit.identified``, to set
a display flag. **Nothing projected onto it.**

What that cost, traced end to end at Johannesburg 2021:

* ``fit_joint`` returned a corner for the PA — Black African 0.0000, Coloured
  0.5149, Indian/Asian 0.0000, White 0.0000 — and 0.5149 is 10.5pp above that
  party's own Duncan-Davis ceiling of 0.4097. It is not the optimiser: plain
  NNLS lands on 0.5421 and the same three zeros. It is the ecological
  inference problem itself, where a rate of 0.003 on a pool casting 523,499
  votes manufactures more squared error than it buys.
* ``balance_margins`` walked it to 0.4121 — still outside, because IPF is
  multiplicative and a cell at exactly zero is a fixed point, so the only cell
  it could scale was the one already at the ceiling.
* the emitted vector was therefore Coloured **1.0000**, and at the 2026 target
  that party's level is about 102% of every vote the Coloured pool casts. The
  per-draw balance cannot solve that, and until a capacity cap was added it was
  swallowed by a bare ``except Exception: pass`` in 42.7% of the live
  forecast's draws — discarding the level shock for *every* party in the draw.

The capacity cap takes the failure rate to zero and its own write-up says it is
a guard, not a cure. This file holds the cure: the assertion below is one line,
it is about the fit rather than about any downstream repair, and before
``balance_within_bounds`` existed it failed.

``test_the_three_known_things_hold_at_once`` is the necessary companion. A
"projection" that satisfied the bounds by abandoning a margin would pass the
first test and be worse than what it replaced, and a projection followed by a
rescale is not a projection — that is exactly how 0.5149 became 0.4121 instead
of 0.4097. So both margins are asserted on the same matrix, at the same
tolerance the unbounded balance is held to.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import pools  # noqa: E402

# Every (city, fitting year) a production emit actually uses. The rates are
# fitted on the election BEFORE the target, so this is the target list from the
# brief translated one election back: joburg at 2016/2021/2026 fits 2011/2016/
# 2021, and the seven other metros at 2021 fit 2016.
FITS: list[tuple[str, str]] = [
    ("joburg", "2011"), ("joburg", "2016"), ("joburg", "2021"),
    ("tshwane", "2016"), ("ekurhuleni", "2016"), ("ethekwini", "2016"),
    ("capetown", "2016"), ("mangaung", "2016"),
    ("nelsonmandelabay", "2016"), ("buffalocity", "2016"),
]

_CACHE: dict[tuple[str, str], tuple] = {}


def _fit(slug: str, year: str):
    if (slug, year) not in _CACHE:
        _CACHE[(slug, year)] = pools.fit_city(
            cityconfig.load(slug), year, pools.load_config())
    return _CACHE[(slug, year)]


def test_no_fitted_rate_falls_outside_its_duncan_davis_interval():
    """Every city, every fitting year, every party, every pool.

    The bounds are arithmetic on the same ward table the margins come from, so
    the true cross-tabulation satisfies all of it and there is no tolerance to
    argue about beyond floating point. Before the fix this failed with three
    cells at Johannesburg 2021 alone (PA/Coloured +0.0024 over its ceiling,
    Al Jama-ah/Indian +0.0011, PA/Black African -0.0002 under its floor).
    """
    worst: list[str] = []
    for slug, year in FITS:
        fits, ctx = _fit(slug, year)
        cats = list(ctx["categories"])
        for party, fit in fits.items():
            lo, hi = fit.bounds[:, 0], fit.bounds[:, 1]
            bad = (fit.rates < lo - 1e-9) | (fit.rates > hi + 1e-9)
            for g in np.flatnonzero(bad):
                over = max(lo[g] - fit.rates[g], fit.rates[g] - hi[g])
                worst.append(
                    f"{slug} {year} {party} {cats[g]}: rate {fit.rates[g]:.4f} "
                    f"outside [{lo[g]:.4f}, {hi[g]:.4f}] by {over:.4f}")
    assert not worst, (
        f"{len(worst)} fitted rates the ward arithmetic forbids:\n  "
        + "\n  ".join(worst[:12]))
    print(f"  {len(FITS)} city-years, every rate inside its bounds")


def test_the_three_known_things_hold_at_once():
    """Pool totals, party totals AND the bounds — on one matrix.

    Enforcing the bounds is only an improvement if the two margins survive it.
    They are not modelling choices: each pool holds a counted number of voters
    and each party won a counted number of votes.
    """
    for slug, year in FITS:
        fits, ctx = _fit(slug, year)
        pool_votes = ctx["pool_votes"]
        total = pool_votes.sum()
        parties = ctx["parties"]
        R = np.column_stack([fits[p].rates for p in parties])

        rows = R.sum(axis=1)
        assert np.allclose(rows, 1.0, atol=1e-9), (
            f"{slug} {year}: pool rates sum to {rows}, not 1 — the bounded "
            f"balance bought its bounds by losing a pool's voters")

        off = max(abs(float(f.rates @ pool_votes) / total - f.citywide)
                  for f in fits.values())
        assert off < 1e-9, (
            f"{slug} {year}: a party's implied citywide share is off by "
            f"{off:.2e} — the bounded balance lost the party margin")


def test_the_pa_is_no_longer_a_single_pool_party():
    """The case that motivated all of it, named and numbered.

    A one-pool vector is not a finding about the PA, it is a corner: 28.1% of
    that party's Johannesburg vote arises in wards under 30% Coloured, and in
    the 89 wards under 2% Coloured it polled 1,173 votes against 392,961 Black
    African votes cast. What the *bounds* force is smaller than that geography
    suggests — arithmetic alone cannot rule out that all 1,173 came from those
    wards' 6,674 Coloured voters, which is why the Duncan-Davis floor is
    0.00016 and not 0.00299 — but it is not zero, and zero is what shipped.

    Asserted loosely and from below. The point is that the vector is not a
    single pool; the exact split is a measurement that may move.
    """
    fits, ctx = _fit("joburg", "2021")
    comp = fits["PA"].composition(ctx["pool_votes"])
    g = list(ctx["categories"]).index("Coloured")
    assert comp[g] < 1.0 - 1e-4, (
        f"the PA is emitted as a single-pool party again (Coloured "
        f"{comp[g]:.6f}); it needs ~102% of that pool's 2026 votes to reach "
        f"its own level, which is the defect this file exists for")
    print(f"  PA at joburg 2021: Coloured {comp[g]:.4f}, "
          f"elsewhere {1 - comp[g]:.4f}")


def test_a_zero_cell_can_still_be_reached():
    """The seeding half of the fix, on its own.

    IPF is multiplicative, so a cell at exactly 0.0 is a fixed point and no
    number of iterations moves it. That is why the bounds could not simply be
    added to ``balance_margins``: with the PA capped at the Coloured pool's
    27,183-vote ceiling and zeroed everywhere else, its column can only ever
    account for 27,183 of its 27,346 votes and the party margin never closes —
    measured, the iteration runs to its cap and raises.

    So a zero is treated as "the fit stopped here", not as a measurement, and
    seeded with the pool's share of the votes the clipped fit could not place.
    This test is the minimal statement of that: one pool saturated at its
    ceiling, one party needing more than that ceiling can give.
    """
    electorate = np.array([1000.0, 100.0])
    party_votes = np.array([50.0, 1050.0])
    # The corner: party 0 is given the whole of its share out of pool 1, and
    # nothing at all out of pool 0.
    R = np.array([[0.0, 1.0],
                  [0.40, 0.60]])
    lo = np.array([[0.0, 0.0], [0.0, 0.0]])
    hi = np.array([[1.0, 1.0], [0.40, 1.0]])   # party 0 capped at 40% of pool 1

    out = pools.balance_within_bounds(R, electorate, party_votes, lo, hi)
    assert out[0, 0] > 0, (
        "a cell the fit zeroed was never reached — the balance can only "
        "rescale what is already non-zero, which is the whole defect")
    assert out[1, 0] <= 0.40 + 1e-9, "the ceiling was not respected"
    assert abs(float(out[:, 0] @ electorate) - 50.0) < 1e-6, \
        "the party margin did not close"
    assert np.allclose(out.sum(axis=1), 1.0, atol=1e-9), \
        "a pool stopped adding to one voter per voter"


def test_an_infeasible_system_is_refused_rather_than_approximated():
    """Bounds and margins that cannot both hold mean an input is not what it
    claims to be. Saying so beats iterating to a cap and returning a matrix
    that satisfies neither — which is how the original defect stayed invisible.
    """
    electorate = np.array([100.0, 100.0])
    party_votes = np.array([150.0, 50.0])
    R = np.array([[0.75, 0.25], [0.75, 0.25]])
    lo = np.zeros((2, 2))
    hi = np.array([[0.5, 1.0], [0.5, 1.0]])    # party 0 can win at most 100
    try:
        pools.balance_within_bounds(R, electorate, party_votes, lo, hi)
    except RuntimeError as exc:
        assert "bounds" in str(exc), f"refused, but not clearly: {exc}"
    else:
        raise AssertionError(
            "an impossible system was balanced anyway; the result satisfies "
            "neither the bounds nor the margins and nothing would say so")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
