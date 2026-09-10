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
from _support import ROOT, skip, run_module  # noqa: E402

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


# The first target election that has not been held, so has no result to be
# checked against. Not a coverage gap: a property of the calendar.
_FIRST_UNHELD_TARGET = 2026

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


def test_a_legal_unbounded_answer_is_returned_untouched():
    """Enforcing a constraint is not the same as replacing the solver.

    Half of what ``balance_within_bounds`` does is seeding, and the seeding
    fires on a condition the bounds have NO part in: ``unplaced`` compares a
    party's known total against its raw NNLS column, and NNLS was never asked
    to reproduce a party total. Measured at Ekurhuleni 2016 with the box
    removed entirely (lo=0, hi=1, so the clip is inert), 15 of 25 parties are
    still seeded and 3,716 votes — 0.41% of the city — are still unplaced,
    with no bound binding anywhere.

    So the bounded path used to move fits that had no violation to move, and it
    moved them the wrong way: Ekurhuleni 2016 has ZERO violations, and paid
    +0.61% of ward SSE, taking the DA's Indian/Asian rate from 1.00 to 0.90.
    ``balance_margins``' answer there is feasible, is a strictly better ward
    fit, AND is a fixed point of the bounded iteration (one full sweep moves it
    by 2.8e-12) — the iteration only left it because the seeding moved the
    starting point.

    This asserts the rule that fixes it, on the case that motivated it: where
    the unbounded balance already satisfies every Duncan-Davis bound, that is
    the answer. Five of the ten production fits take this path.
    """
    unchanged, moved = [], []
    for slug, year in FITS:
        fits, ctx = _fit(slug, year)
        parties = ctx["parties"]
        pool_votes = ctx["pool_votes"]
        raw = ctx["raw_rates"]
        R = np.column_stack([fits[p].rates for p in parties])
        party_votes = (ctx["Y"] * ctx["votes"][:, None]).sum(axis=0)
        lo = np.column_stack([fits[p].bounds[:, 0] for p in parties])
        hi = np.column_stack([fits[p].bounds[:, 1] for p in parties])

        plain = pools.balance_margins(raw.copy(), pool_votes, party_votes)
        legal = bool((plain >= lo - 1e-9).all() and (plain <= hi + 1e-9).all())
        drift = float(np.abs(R - plain).max())
        if legal:
            # Not bit-identical: the pass-through stops IPF at 1e-15 rather
            # than 1e-12 and rescales the party margin exactly once, which is
            # how it keeps BOTH margins at least as tight as the bounded path.
            # Anything above float noise means the projection ran anyway.
            unchanged.append((slug, year, drift))
            assert drift < 1e-9, (
                f"{slug} {year}: the unbounded balance violates no bound, yet "
                f"the emitted fit differs from it by {drift:.2e}. The bounded "
                f"path is running on a fit with nothing to correct, and it is "
                f"not free — it cost Ekurhuleni 2016 0.61% of ward SSE")
        else:
            moved.append((slug, year, drift))

    assert unchanged, (
        "no fit passed through unchanged, which cannot be right: five of the "
        "ten have no violation at all")
    assert moved, (
        "every fit passed through unchanged, so the projection is now dead "
        "code — joburg 2021, ethekwini/capetown/nelsonmandelabay/buffalocity "
        "2016 all have rates the ward arithmetic forbids")
    print(f"  {len(unchanged)} fits pass through untouched "
          f"({', '.join(s + ' ' + y for s, y, _ in unchanged)}); "
          f"{len(moved)} are projected")


def test_the_seeding_is_not_triggered_by_the_bounds():
    """The record said otherwise, and the record was wrong.

    MODEL-LOG §1.38 claimed *"the bound is what creates unplaced votes; the
    seed is only what lets a multiplicative iteration place them"*, and
    JUDGEMENT-CALLS gave the trigger as *"when the Duncan-Davis ceiling stops a
    cell absorbing a party's whole total"*. Neither is the code. Two separate
    conditions fire two separate mechanisms:

    * **seeding** fires when the raw NNLS fit's column does not reach the
      party's known total — which it generally does not, because nothing in
      the least-squares problem ties a column sum to a party total;
    * **the box** binds when a cell would leave its Duncan-Davis interval.

    A ceiling can enlarge the first by clipping a cell before the comparison.
    It is not what creates it. This test states that separately, so nobody
    re-derives the wrong causal story from the code.
    """
    slug, year = "ekurhuleni", "2016"
    _, ctx = _fit(slug, year)
    raw, pv = ctx["raw_rates"], ctx["pool_votes"]
    qv = (ctx["Y"] * ctx["votes"][:, None]).sum(axis=0)

    counts = raw * pv[:, None]
    target_cols = qv.astype(float) * (pv.sum() / qv.sum())
    # The box removed entirely: hi = 1 means the clip cannot bite.
    open_hi = pv[:, None] * np.ones_like(counts)
    unplaced = np.maximum(
        target_cols - np.minimum(counts, open_hi).sum(axis=0), 0.0)

    assert (counts > open_hi + 1e-9).sum() == 0, \
        "the open box clipped something; then this measures nothing"
    assert (unplaced > 0).sum() > 0, (
        "with no bound anywhere, no party's votes are unplaced — then §1.38's "
        "causal claim would have been right and this test should be deleted")
    print(f"  {slug} {year}: with lo=0, hi=1, "
          f"{int((unplaced > 0).sum())} of {counts.shape[1]} parties are still "
          f"seeded and {unplaced.sum():,.0f} votes "
          f"({100 * unplaced.sum() / pv.sum():.2f}% of the city) unplaced — "
          f"no bound binds anywhere")


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


def test_no_emitted_composition_weight_is_arithmetically_impossible():
    """A party cannot draw more from a pool than the pool casts.

    `w_pg <= poolshare_g / s_p` is the ceiling of a party taking **100%** of pool
    g, so a weight above it describes an election that cannot happen. Until
    2026-08-17 five of 339 party-pairs across the nine city-years were above it,
    worst the ANC at Mangaung 2021 claiming 15.68% of its vote from a pool
    casting 1.54% of the ballots — **5.2x the maximum**.

    The cause was two denominators for one quantity: `PartyFit.composition` was
    handed a projected REGISTRATION-share vector while `montecarlo.pool_spec`
    sized the same pools from the counted roll times turnout (MODEL-LOG §1.42).

    Nothing caught it because everything downstream absorbed it — IPF forced the
    pool margin every draw so the levels came out right, `identified()` reported
    the one wholly-collapsed pool as merely unmeasured, and the capacity guard's
    failure at Nelson Mandela Bay was attributed to a row-side infeasibility
    rather than to its cause. **This test needs no backtest and no draw:** it is
    arithmetic on the emitted artefact.
    """
    import json

    # (city, target) -> the emitted artefact, which is what the model reads.
    # ⛔ DERIVED FROM THE ARTEFACT, NEVER TYPED. This was a hand-written list of
    # nine city-years, written when nine specs existed. §1.69 emitted seven more
    # on 2026-08-22 and the list never moved, so the guard scanned 9 of 16 —
    # 368 of 667 party-pool pairs — and **the unscanned 45% contains real
    # violations**, including one at 228.93x against the 5.2x that prompted this
    # test in the first place (§1.42). The scan was healthy, the detector
    # worked, and it found nothing IN THE WRONG SET.
    # ⛔ AND IT HAPPENED AGAIN, ONE LAYER UP (§1.162 §4). Deriving the
    # population from `history.json` fixed the typed list and replaced it with
    # the SCORED set, while the claim this test makes covers the EMITTED set.
    # On 2026-09-02 three 2011 specs were emitted and never scanned because
    # they failed to score, and one of them — Cape Town 2011 DA in White at
    # 1.26x — was a real violation nothing had ever reported.
    #
    # The population is now the emitted specs, and a spec that cannot be
    # checked is NAMED rather than skipped: an unscannable member is a hole in
    # the claim, and a hole nobody is told about is how this test has now been
    # wrong twice about the same thing in two different ways.
    hist_path = ROOT / "data/processed/history.json"
    if not hist_path.exists():
        skip("no data/processed/history.json — run compare_history first")
    import compare_history as ch
    hist = {r["slug"] + str(r["year"]): r
            for r in ch.load_history(hist_path)[1]}

    emitted = set()
    for spec in sorted((ROOT / "data/processed").glob("**/pools_*.json")):
        year = spec.stem.replace("pools_", "").split("_")[0]
        if not year.isdigit():
            continue
        if spec.stem.endswith("_simulation"):
            continue
        parent = spec.parent.name
        slug = parent if parent != "processed" else "joburg"
        emitted.add((slug, year))

    # A future target has no result to be checked against; that is a property
    # of the world, not a gap in coverage.
    future = {(s, y) for s, y in emitted if s + y not in hist
              and int(y) >= _FIRST_UNHELD_TARGET}
    unscannable = sorted({(s, y) for s, y in emitted
                          if s + y not in hist} - future)
    assert not unscannable, (
        f"these pool specs are EMITTED and cannot be checked, so the claim "
        f"this test makes does not cover them: {unscannable}.\n"
        f"  They are backtest targets with no row in history.json. Either "
        f"re-run compare_history so they are scored, or establish why they "
        f"cannot be — but do not let them sit outside the scan silently, "
        f"which is how Cape Town 2011's 1.26x went unreported (§1.162 §4).")

    targets = sorted(emitted - future)
    # (1) IT LOOKED, and the bound is two-sided against a computed denominator
    # rather than a floor that ratchets down when it trips.
    assert len(targets) >= 0.75 * len(emitted), (
        f"only {len(targets)} of {len(emitted)} emitted specs are being "
        f"scanned; the claim covers the emitted set.")

    bad, straining = [], []
    for slug, year in targets:
        city = cityconfig.load(slug)
        spec_path = city.processed / f"pools_{year}.json"
        if not spec_path.exists() or (slug + year) not in hist:
            continue
        spec = json.loads(spec_path.read_text())
        actual = {p: a for p, _md, _mn, a, *_ in hist[slug + year]["votes"]
                  if a == a and a > 0}
        pools_ = spec["pools"]
        names = list(pools_)
        votes = {nm: pools_[nm].get("registered", 0.0)
                 * float((pools_[nm].get("turnout") or [0, 1, 0])[1])
                 for nm in names}
        total = sum(votes.values())
        if total <= 0:
            continue
        share = {nm: votes[nm] / total for nm in names}
        for party, s_p in actual.items():
            if s_p <= 0:
                continue
            w = {nm: float((pools_[nm].get("members") or {}).get(party, 0.0))
                 for nm in names}
            wsum = sum(w.values())
            if wsum <= 0:
                continue
            for nm in names:
                if w[nm] <= 0:
                    continue
                # ⛔ TESTED AT THE POOL'S OWN TOP-OF-BAND TURNOUT, NOT THE MIDDLE.
                #
                # Turnout is DRAWN per pool, not fixed, and the pools have
                # separate turnout levers — so a composition that will not fit at
                # the central turnout may fit perfectly at a draw the model
                # actually makes. Testing the middle alone condemned four
                # city-years the model can legitimately reach.
                #
                # ⚠️ AND RAISING EVERY POOL TOGETHER IS THE WRONG TEST, which is
                # how this was first got wrong: lifting all pools lifts the CITY
                # total too, so a pool's SHARE can fall and the ceiling gets
                # tighter rather than looser. The question is what ONE pool can
                # cast when its own turnout is at the top of its band and the
                # others sit at theirs — which is what a per-group lever does.
                # ⛔ COMPARED IN VOTES, NOT IN SHARES OF A SHIFTING TOTAL.
                # A ratio against `pool_share / party_share` lets the CITY total
                # grow when this pool's turnout rises, which silently inflates
                # the party's implied vote count on the other side of the
                # inequality. The party's vote is a FIXED, OBSERVED number; only
                # the pool's capacity is being flexed. So: hold the party's
                # votes at the central-turnout city size and ask whether this
                # pool can cast that many.
                party_votes = s_p * total
                pool_hi = (pools_[nm].get("registered", 0.0)
                           * float((pools_[nm].get("turnout") or [0, 1, 0])[2]))
                if share[nm] <= 0:
                    # A pool that casts NOTHING, with a party weighted into it.
                    # The shipped test divided by this and raised
                    # ZeroDivisionError — an error, not a finding, so it read as
                    # a broken test rather than a broken spec.
                    bad.append(f"{slug} {year} {party} in {nm}: the pool casts "
                               f"ZERO votes and still carries weight "
                               f"{w[nm] / wsum:.4f}")
                    continue
                rel = w[nm] / wsum
                # FATAL only if it cannot fit even when this pool's own turnout
                # is at the top of its band — i.e. more of the party's vote than
                # the pool can cast under ANY draw the model makes. That is the
                # owner's constraint: no party can take more votes from a pool
                # than the pool has voters.
                need = rel * party_votes
                if pool_hi > 0 and need > pool_hi * (1.0 + 1e-9):
                    bad.append(
                        f"{slug} {year} {party} in {nm}: needs {need:,.0f} votes "
                        f"from a pool that casts at most {pool_hi:,.0f} even at "
                        f"the TOP of its turnout band — {need - pool_hi:,.0f} "
                        f"more votes than that pool has voters ({need/pool_hi:.2f}x)")
                elif rel > (share[nm] / s_p) * (1.0 + 1e-9):
                    # Straining but reachable: impossible at central turnout,
                    # possible at the top of this pool's band. Recorded, not
                    # fatal — the model draws there.
                    straining.append(
                        f"{slug} {year} {party} in {nm}: {rel:.4f} against "
                        f"{share[nm]/s_p:.4f} at central turnout, but fits at "
                        f"the top of the band")
    assert not bad, (
        "these emitted pool weights describe an election that cannot happen — "
        "the party is SEEDED to draw more from the pool than the pool "
        "casts:\n  "
        + "\n  ".join(bad)
        + "\n\n  ⚠️ THIS IS NOT AN IMPOSSIBLE ELECTION, and this message said "
          "it was until 2026-09-02. `montecarlo.pool_spec` re-fits the "
          "composition by iterative proportional fitting on EVERY draw, "
          "imposing each pool's counted voters and the party's drawn citywide "
          "level as hard margins. Verified: Buffalo City 2011 DA/White is "
          "repaired 0.575 -> 0.374 before draw one. THE MODEL NEVER ALLOCATES "
          "A PARTY MORE VOTES THAN A POOL CASTS.\n"
          "\n  What this DOES report is a seed that IPF has to drag a long "
          "way, which moves the composition away from what was measured. "
          "Check that `PartyFit.composition` is handed VOTES CAST "
          "(registered x turnout), the same vector `pool_spec` builds, and "
          "not a registration or projected-share vector. Do NOT propose a "
          "fit-time capacity constraint on the strength of this message "
          "alone: one was built, measured and reverted (MODEL-LOG §1.41, "
          "coherent seat error 306 -> 486).")


def test_the_registration_bound_is_per_level():
    """One solver, three levels, and only one of them may exceed 1.

    Phase 1a bounded all three at 1.0 because "a value above 1.0 is not a rate
    at all". True of `adult_share` (adults per person) and `turnout` (voters
    per registered). FALSE of `registration`: registered voters are counted and
    census voting-age population is modelled, and `pool_counts` computes their
    ratio separately as `census_correction` — 1.480 for White at Johannesburg
    2021 — while the solver clipped the same quantity to 1.0. JUDGEMENT-CALLS
    §L9, MODEL-LOG §1.189.
    """
    import numpy as np

    seen_above_one = False
    for slug, year in FITS:
        counts = pools.pool_counts(cityconfig.load(slug), year,
                                   pools.load_config())
        rates = counts.rates

        # (1) THE TWO THAT CANNOT EXCEED 1 STILL CANNOT.
        for level in ("adult_share", "turnout"):
            r = rates[level]
            assert np.all(r <= 1.0 + 1e-9), (
                f"{slug} {year}: {level} reached {float(np.max(r)):.4f}. "
                f"Adults cannot exceed people and voters cannot exceed "
                f"registered; only `registration` may pass 1.")
            assert np.all(r >= -1e-9), f"{slug} {year}: {level} went negative"

        # (2) REGISTRATION IS BOUNDED BY THE GUARD, NOT BY 1.
        reg = rates["registration"]
        assert np.all(reg <= pools.REGISTRATION_MAX + 1e-9), (
            f"{slug} {year}: registration reached {float(np.max(reg)):.4f}, "
            f"above REGISTRATION_MAX")
        if np.any(reg > 1.0 + 1e-6):
            seen_above_one = True

    # (3) IT LOOKED. If nothing anywhere exceeds 1, the whole change is inert
    #     and this test is guarding a situation that does not arise.
    assert seen_above_one, (
        "no registration rate anywhere in the panel exceeds 1.0, so lifting "
        "the bound changed nothing and §L9 is defending an empty case. "
        "Johannesburg White measured 1.74 when this was written.")

    # (4) AND THE GUARD BINDS WHERE THE MODEL IS KNOWN TO BE BROKEN — Mangaung's
    #     Indian/Asian pool, which also carries a fitted turnout of exactly 0.
    man = pools.pool_counts(cityconfig.load("mangaung"), "2016",
                            pools.load_config())
    assert man.unidentified, (
        "Mangaung 2016 reports no rate on a bound. Its Indian/Asian pool has "
        "3,531 registered voters and a fitted turnout of exactly 0.0000; if "
        "nothing is reported, the detector has stopped seeing it.")


if __name__ == "__main__":
    # `run_module`, NOT a hand-rolled loop. Until 2026-08-23 this file ended with
    # `for name, fn in sorted(globals().items()): ... fn()`, which catches
    # neither `SkipTest` nor `SystemExit` — so the FIRST skip aborted the run and
    # every later test in the file silently never executed, and no summary was
    # printed. Five files were in that state; `test_regressions` alone has five
    # `skip(` calls. Under `run_all.py` they were fine, because the suite calls
    # `run_module(vars(module))` itself — the suite hid it. MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))