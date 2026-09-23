"""Golden-seed CHARACTERISATION of the citywide prior in ``montecarlo.py``.

``montecarlo.make_drawer`` returns a closure that produces one citywide PR
target vector per call. Everything downstream -- the VD solve, the ward races,
the seat draws, the published probabilities -- is conditioned on that vector,
so a change in its distribution moves every number the site publishes.

**This file records what the code does. It does not claim that what it does is
right.** Some of these assertions pin behaviour that is known to be wrong.

``draw_pools()`` distorts the configured pool bands in TWO separate places,
and they are easy to confuse because they act on the same numbers one after the
other. Re-record with ``--decompose`` to reproduce the current figures.

* **Plan item 3.1, OPEN — renormalisation.** ``draw_pools()`` builds each
  pool's total from its configured ratio triangular, fills in the individual
  parties, and then divides the whole vector by its own sum. Because the pieces
  are drawn independently and generally sum to more than one, that division
  pulls the realised distribution IN — from **both** ends, not one. The
  forecast is therefore more confident than any documented judgement supports,
  and most of that confidence is a low ceiling.

* **The entrant rescale.** Separately, and *after* renormalisation,
  ``target *= (1.0 - share)`` scales every established party down to make room
  for the hypothetical new entrant. Since the entrant draws a positive share on
  25% of draws, this shifts every pool DOWN. Whether it is a defect at all is a
  modelling judgement (an entrant's votes must come from somewhere), but it is a
  different step with a different fix, and attributing it to 3.1 would send
  whoever fixes 3.1 after a defect that is not there.

**PLAN ITEM 3.1 IS RESOLVED, 2026-08-15.** The test that asserted the
narrowing — ``test_the_realised_pool_prior_is_not_the_configured_one`` — failed
as it was designed to, and has been deleted per its own instruction rather than
loosened. The Black African pool's configured band is 50.87-63.08% and its
realised band 48.75-61.31%: a width of 12.21 points against 12.56, so the
distribution is no longer pulled in. The fix was not aimed at 3.1 — it is the
Gaussian copula in ``montecarlo.correlated_triangular``, which preserves each
pool's marginal exactly by construction, plus the per-party level shocks. The
entrant rescale below still shifts the pools down and is a separate thing.

Re-record after a deliberate change with:
    ./.venv/bin/python tests/test_drawer.py --record

Re-measure the A/B/C table above with:
    ./.venv/bin/python tests/test_drawer.py --decompose

Run:
    ./.venv/bin/python tests/test_drawer.py
    ./.venv/bin/python -m pytest tests/test_drawer.py -q
"""

from __future__ import annotations

import copy
import json
import csv
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

import cityconfig  # noqa: E402
import montecarlo as mc  # noqa: E402

CITY = "joburg"
SEED = 20261104          # the shipped seed; the drawer is exercised as configured
DRAWS = 2000             # enough for a stable p5/p95, ~0.2s to produce

# Percentage points. This is slack for a float difference, not for a real change
# in the prior: re-emitting the pools, or nudging a party's blended centre, moves
# these values well clear of it. A numpy UPGRADE can legitimately move them too
# (the RNG stream is versioned); that is a re-record, and should be noted as one
# in MODEL-LOG.md.
#
# THE DRAW IS BIT-FOR-BIT REPRODUCIBLE WITHIN A PROCESS, NOT ACROSS ONE. This
# comment used to claim the stronger thing. `levels.theta_record` iterates
# `set(before) & set(after)` and appends each party's observations in that
# order, so PYTHONHASHSEED changes the summation order and float addition is not
# associative. Measured 2026-08-18: three processes at one seed give three
# different hashes over `pr_share_draws`, and the largest difference in any
# party's mean share is 5.6e-17 — the last bit of a float64. Every scored metric
# is identical (five processes: coherent 92, CRPS 68.716, pr_mae 5.7793). So the
# tolerance below is doing real work, and a bit-level hash is not a valid
# instrument across processes. See MODEL-LOG §1.46.
TOL = 0.01

ELECTIONS = ROOT / "data" / "raw" / "elections"
PROCESSED = ROOT / "data" / "processed"

# RE-RECORDED 2026-09-23, deliberately: THE RE-EMIT WINDOW MOVED THE INPUT, NOT
# THE DRAWER. Every spec was re-emitted under two landed changes — the pool-seed
# fix (§1.249: an entrant with no measured vector is spread like the city rather
# than a quarter into every pool, which touches 45 of the micro-parties in the
# 2026 spec) and the declared ward slates (§1.252). The canonical artefact is
# `seat_abs_err_coherent=733/@2ac4c1eb/1000d/pools:7264a929/rows=24`.
#
# The movement, against the 2026-09-17 record: ANC mean 22.53% -> 22.29%,
# MK 9.52% -> 9.78%, ASA p95 22.66% -> 23.73%, Black African pool mean
# 50.15% -> 50.00%. Several exceed the ±0.01 tolerance, which is how the guard
# caught it — correctly, and it is the input that changed.
#
# ⚠️ ENTRANT IS STILL IN THIS BLOCK and the certified roster retired the generic
# slot at 2026 (§1.245). It survives because `build_inputs` assembles the
# drawer's inputs itself; the block records what the drawer does with what it is
# handed, not what the live forecast hands it. Worth a look, not a silent edit.
# RE-RECORDED 2026-09-17, deliberately: THE 2026 SPEC NOW COMES FROM THE CERTIFIED
# NOMINATION LIST. `pools_2026.json` was re-emitted 2026-09-16 from a declared,
# complete roster (82 parties, 27 dropped on the owner's confirmation, 46 named
# arrivals seeded, the generic ENTRANT slot retired) with the SACP sized by hand
# at 1.31% (JUDGEMENT-CALLS §L13). The prior moved with it — ANC p95 35.16% ->
# 35.76%, Black African pool mean 50.55% -> 50.15% at the first diff — and that
# is the input changing, not the drawer. A freeze is a tripwire: it fired, the
# cause is named here, and the backtest is untouched (2011-2021 specs unchanged).
# RE-RECORDED 2026-09-02, deliberately: THE CENSUS IS NOW REPROJECTED ONTO THE
# TARGET'S WARDS INSTEAD OF JOINED TO THEM BY WARD CODE (MODEL-LOG §1.160/§1.161).
#
# Wards are redrawn at every local election and their codes are REUSED, so the
# old join succeeded while attaching each ward's composition to a different
# polygon. The share of the 2026 target roll sitting in a voting district whose
# ward code changed since 2021 is not small, so this moves the live forecast.
#
# The movement, against the 2026-08-23 record:
#   DA   mean 26.05% -> 26.46%  (+0.42pp)   ANC  mean 22.40% -> 22.52%  (+0.12pp)
#   EFF  mean 10.28% -> 10.10%  (-0.17pp)   ASA  mean 12.72% -> 12.65%  (-0.07pp)
#   PA   mean  6.59% ->  6.45%  (-0.14pp)   MK   mean  9.79% ->  9.76%  (-0.03pp)
# and on the pools, which is where the change actually acts:
#   Black African mean 51.14% -> 50.55% (-0.59pp), p5 43.03% -> 42.26%
#   White         mean 32.56% -> 33.05% (+0.49pp), p95 39.34% -> 40.02%
# The two largest pools move in opposite directions and nearly cancel, which
# is what a REPROJECTION should do: it moves composition between wards, it
# does not create or destroy voters.
#
# ⛔ THIS IS NOT CLAIMED AS AN IMPROVEMENT TO THE 2026 FORECAST, and it cannot
# be: nothing scores 2026. It is claimed as a CORRECTNESS fix, and the evidence
# for it is on the backtest, where the same change takes the panel from 16
# city-years to 21 and stops Cape Town being fitted on twice everyone else's
# history. On the sixteen city-years common to both, CRPS 329.61 -> 331.59 and
# seat error 380 -> 378 — i.e. inside noise, which is what a correctness fix
# with no accuracy claim should look like.
#
# Recorded against pools_sha 86995c914b530216, all 26 specs re-emitted at one
# key. The two OPEN pool-capacity defects (§1.161 §5) are at 2011 Buffalo City /
# Nelson Mandela Bay and 2016 Mangaung, and touch no number in this file.

# RE-RECORDED 2026-08-23, deliberately: THIS GOLDEN HAD BEEN RED SINCE 22 AUG
# AND NOBODY RE-RECORDED IT. Two shipped changes moved the 2026 Johannesburg
# forecast and neither carried the golden with it, which is the failure
# CLAUDE.md names — "a silent re-record destroys the only guard on the prior",
# and leaving it red for a day destroys it just as thoroughly, because a test
# that is expected to fail is a test nobody reads.
#
# The movement, against the 2026-08-17 record:
#   ANC  mean 21.28% -> 22.82%  (+1.54pp)   ASA  mean 14.12% -> 12.54%  (-1.58pp)
#   DA   mean 24.51% -> 25.79%  (+1.28pp)   EFF  mean 10.42% -> 10.11%  (-0.31pp)
#   MK   mean 10.12% ->  9.76%  (-0.35pp)
#
# WHAT MOVED IT, and what could not be separated. Exactly one component is
# isolated, because the tree was measured on both sides of it (MODEL-LOG §1.75):
# restoring Mangaung's and Buffalo City's six deleted pre-2011 files is worth
# ANC +0.39pp, DA +0.33pp, ASA -0.40pp of the above. The REMAINDER — about
# +1.15pp ANC, +0.95pp DA, -1.18pp ASA — pools the sigma_poll rebuild and the
# single-house weight cap (§1.67-§1.69), which act directly on this forecast
# through the two SRF waves, with the five other metros' pre-2011 theta history
# (§1.70). Those two were NOT separated: doing it means running with the five
# metros' archives withheld, and moving files out of data/raw/elections is the
# operation §1.75 is about. The limit is stated rather than worked around.
#
# Nine/sixteen city-years: NOT AFFECTED BY THE RE-RECORD. The panel is 384
# coherent / CRPS 329.4 on sixteen and 280 on §1.70's nine, measured at 1500
# draws on the settled tree, identical to the committed history.json to the
# seat. This records where the 2026 forecast now is; it does not claim an
# improvement, and none is claimed.
# RE-RECORDED 2026-08-24: THE TWO-TERM sigma_poll IS NOW THE DEFAULT.
# Adopted by the owner on §1.88's measurement — the panel could not tell the
# difference (384 = 384, CRPS 329.4 -> 329.2, both inside their own intervals)
# and it ships on identifiability, not accuracy: the retired POLL_HOUSE_SD was
# a residual of the same nine 2016 readings that are the only metro-poll test
# cases the backtest has, while every replacement constant is cited.
#
# The 2026 forecast moves by about a seat: DA 79 -> 78, ANC 63 -> 64, ASA
# 24 -> 25. What matters more is invisible here — sigma no longer collapses
# toward certainty as houses are added (0.40pp -> 3.86pp at a hundred houses),
# and the DA's blend weight is now 0.484 by arithmetic rather than 0.500 pinned
# by a cap. MODEL-LOG §1.87, §1.88, §1.91.
# Recorded 2026-08-10 from data/processed/pools_2026.json, seed 20261104,
# 2000 draws, numpy 2.5.1. Values are percentages: (mean, p5, p95).
#
# RE-RECORDED 2026-08-17, deliberately: THE LEVEL SHOCK NOW SURVIVES THE
# BALANCE, IN EVERY DRAW. `draw_pools` shocked the centres, re-balanced them by
# IPF and wrapped the balance in `except Exception: pass`. The balance RAISED in
# 41.8% of this configuration's draws — the PA is a member of exactly one pool
# and its shocked centre asked for up to 254% of every Coloured vote cast in
# Johannesburg — and on every one of those draws the level shock was discarded
# for EVERY party, not just for the PA. It failed preferentially on the draws
# where the shock was largest. Nothing reported it. The shocked column targets
# are now water-filled under each party's own pool capacity before balancing
# (`montecarlo.capped_targets`, POOL_CAPACITY_MARGIN 0.98), which takes the rate
# to 0.0%, and the remaining fallback is counted onto ModelRun and printed.
# Nine city-years: NO BACKTEST CHANGE. The original note here claimed Nelson
# Mandela Bay 20 -> 16 and a total of 312 -> 308; that was measured at 400 draws
# and is draw noise. At 1500 draws, five seeds per arm, the two arms are 18.8 and
# 19.2 with a seed-to-seed spread of 2 in both, and the committed history.json
# gives NMB 20 and a total of 312. The re-record below is therefore justified by
# the 2026 forecast alone, where the mechanism was absent from 42.7% of draws and
# is now present in all of them. Corrected in MODEL-LOG 1.33 the same day.
#
# So these numbers move because a mechanism that was absent from two draws in
# five is now present in all of them: the top parties widen (DA p5 16.38 ->
# 14.72, p95 49.68 -> 49.14; ANC p5 8.04 -> 6.74, p95 39.33 -> 41.44) and the PA
# falls back toward what its pool can actually hold (mean 4.83 -> 5.03 here,
# 5.75% -> 6.02% of the PR ballot in the 600-draw forecast). The DA's realised
# sd(log) over the run goes 0.168 -> 0.189 against a measured 0.15-0.35.
# In the same change, `montecarlo.LEVEL_DF` stopped being inert: it was a
# default argument, evaluated once at import, so every sweep of it had measured
# 7.0 whatever value was set. That does NOT move these values (7.0 is unchanged)
# but it is why they can now be moved by it at all.
# RE-RECORDED 2026-08-13, deliberately, for three changes to the draw:
#   * a per-party level shock connected to the measured sd(log θ), drawn from a
#     Student-t rather than a bounded triangular (montecarlo.log_shock);
#   * one correlated citywide turnout factor across pools, ρ = 0.63 measured
#     (montecarlo.TURNOUT_CORRELATION);
#   * turnout bands built in logit space, so they are two-sided everywhere
#     (pools.turnout_band).
# RE-RECORDED 2026-08-17 (fourth and last today): THE COMPOSITION IS NORMALISED
# ON VOTES CAST. `PartyFit.composition(pool_votes)` was being handed a projected
# REGISTRATION-share vector while `montecarlo.pool_spec` sized the same pools
# from the counted roll times turnout — two denominators for one quantity, and a
# category error against the function's own signature. It made 5 of 339 emitted
# party-pool weights ARITHMETICALLY IMPOSSIBLE (Mangaung's ANC claimed 15.68% of
# its vote from a pool casting 1.54% of the ballots, 5.2x the maximum); 0 remain.
# At Nelson Mandela Bay the projected share of the Indian/Asian pool came out
# NEGATIVE and clipped to zero, so a pool of 9,596 registered voters at 86.5%
# turnout had no fitted members at all — the collapse the per-draw capacity
# guard was built for. It now carries 26 members, 2 identified. MODEL-LOG §1.42.
#
# Nine city-years: 312 -> 310, i.e. NOTHING. IPF pins the citywide levels
# whatever the seed composition says, so this moves only the ward and seat
# layer, and it nets to noise. It is a correctness fix and is not claimed as an
# improvement.
# RE-RECORDED 2026-08-17 (third time today): THE WEIGHT-AWARE CEILING WAS TRIED
# AND REVERTED. It scored 306 -> 486 over nine city-years (Mangaung 10 -> 112),
# because it bounds a composition the draw does not hold still. So these numbers
# are back where the second re-record left them, plus the pool-fit pass-through
# of MODEL-LOG 1.40, which does not move the 2026 artefact at all. The ceiling
# defect below is REAL and UNFIXED -- read it as an open problem, not a change.
#
# WHAT WAS TRIED: THE POOL-CAPACITY CEILING IS WEIGHT-AWARE. It was an INDICATOR — a membership of 0.00019 counted
# like one of 1.0 — so once `balance_within_bounds` began seeding every zeroed
# cell, 74 of 75 parties had a ceiling of exactly 1.0 at 2026 and the capacity
# guard could no longer fire for anyone. Its silence was reported as evidence
# the projection had removed the problem. It had not. MODEL-LOG 1.41.
#
# The movement here is the PA going back UNDER a bound it should always have
# been under: its true ceiling is 0.0689 of votes cast (it takes 99.18% of its
# vote from a pool casting 6.73% of the ballots) against a 2026 centre asking
# about 109% of that. The previous re-record, six hours earlier, celebrated the
# PA's p95 rising 7.24% -> 11.79% as "coming off a ceiling it should never have
# been on". Half of that was real — the corner solution was an artefact — and
# half was the guard going blind. This record puts the arithmetic bound back.
#
# The pool-fit pass-through (MODEL-LOG 1.40) does NOT move these numbers:
# pools_2026.json is byte-identical under it.
# RE-RECORDED 2026-08-17 (second time today), deliberately: THE DUNCAN-DAVIS
# BOUNDS ARE NOW ENFORCED. `fit_city` balances through `balance_within_bounds`,
# so no emitted rate sits outside the interval the ward arithmetic proves. The
# old code emitted ELEVEN forbidden rates across the ten (city, fitting-year)
# pairs a production emit uses — the worst being the DA at Nelson Mandela Bay
# 2016, Black African 0.0059 against a proven floor of 0.0312, with the
# difference parked in the White pool. MODEL-LOG 1.38.
#
# The movement here is the PA coming off a ceiling it should never have been on.
# Its Johannesburg fit was a corner solution (Coloured 0.5149, exactly 0.0000 on
# the other three pools) 10.5pp above its own arithmetic ceiling, which emitted
# as a single-pool vector and made its 2026 level unrepresentable: the party was
# held at its pool capacity in 39.2% of draws, worst ask 204% of capacity. After
# the fix NOTHING is held in any draw, and the PA's mean rises 5.03% -> 5.76%
# with its p95 7.24% -> 11.79%. The Coloured pool follows it (p95 12.16% ->
# 16.08%) and the top of the ballot gives a little back.
#
# Nine city-years: 312 -> 306 coherent seat error, which is INSIDE the +/-2 to 4
# draw noise and is NOT claimed as an improvement.
# RE-RECORDED 2026-08-17, deliberately: THE ARRIVAL GROUP TOTAL IS NOW HELD TO
# ITS RECORD. `pools.arrival_rules` sized each entrant at the MEDIAN of its
# reach-matched comparators and wrapped it in a band running to the 95th
# percentile -- a band `pool_spec`'s IPF then nullified, because IPF pins each
# party's mean to its centre. Entrants are now weighted by the reach-matched
# MEAN, where the reach signal lives, and the group is rescaled to the
# arrival-total record (median 1.64% over city-years before the target).
# Splitters are untouched. Nine city-years: coherent seat error 316 -> 312,
# beats-uniform-swing 6/9 -> 7/9, ranks 13+ -4.6pp -> -1.7pp. MODEL-LOG 1.32.
#
# The 2026 drift is SMALL and in the expected direction -- ANC mean -0.39pp,
# DA +0.21pp, ASA p95 +0.67pp -- because `pools_2026.json` carries no entrant
# seeds at all (no nomination roster exists yet), so what moved 2026 is the
# re-emit, not the mechanism. The mechanism is what moved the backtests.
# RE-RECORDED 2026-08-16: THE METRO POLLS NOW ACTUALLY FIRE FOR 2026. They had
# never run there -- a KeyError on 'house' was swallowed by a bare except, in
# the one channel with demonstrated skill and the one case it was built for.
# Two SRF waves are now aggregated by recency and blended once, moving the DA
# to 37.7%, the ANC to 23.3% and ActionSA to 13.4%. And earlier: the level shock now TRANSMITS. log_shock was
# handing every party the same t draw (size=None against an array of sds), so
# the shocks were perfectly correlated and cancelled under normalisation --
# the ANC realised sd(log) 0.08 against a measured 0.21. It is now applied to
# the CENTRES and balanced through by IPF, and realises 0.79-0.84 of measured
# for the top parties. And earlier the same day: the Dirichlet now floors its MEAN vector rather
# than its concentration, so E[X] is exactly the vector asked for and no mass
# is injected that no centre requested. And earlier the same day: the CENTRES
# NOW BIND. pool_spec balances the pool x
# party matrix by IPF (pools.balance_margins) so each party's expected citywide
# share IS its centre, instead of the centre only nudging its share of a pool.
# Johannesburg 2016's ANC error falls from +8.54pp to +1.51pp and the nine-city
# CRPS from 285.7 to 262.7. And previously, 2026-08-14, for the Dirichlet floor: it was 0.05, which is not a
# numerical guard but a claim. Measured with real levels at Johannesburg 2021,
# 44 of the Black African pool's 52 members were floored and their collective
# share went from 1.59% to 8.41% — several points of citywide vote manufactured
# for parties the model puts near zero. Now 1e-4, which is only what numpy
# needs. And previously, the same day, for two changes:
#   * parties NOT ON THE BALLOT are dropped at baseline-load time, before θ,
#     ρ, the spine or the pool fit see them. A party that is not standing
#     cannot take votes, and its share is not reapportioned by hand -- the
#     pools renormalise when drawn, so it goes to the parties drawing on the
#     same pools. (At 2026 there is no published nomination list yet, so this
#     is a no-op for the live spec and moves only the backtests.)
#   * the home splinter record is filtered to the target, so MK's 2024 split
#     no longer sizes an arrival at 2021. 2026 legitimately still sees it.
# And previously, for the by-election clamp fix: the clamp was
# anchored on the NATIONAL baseline, so it dragged ActionSA from the spine's
# 15.2% down to 12.1% using a bound derived from the very route task #22
# abandoned. Anchored on the spine level instead, ActionSA's central level
# rises to 16.6% and its median seats from 23 to 31.
# The earlier re-record's note, for the record: the prior moved as intended
# and by little: ANC mean 23.33% -> 23.15%, DA
# 27.69% -> 27.79%, EFF 9.94% -> 10.27%. The pool p5/p95 tightened at the White
# pool (25.18-36.51 -> 25.65-35.75) and loosened at Black African, which is the
# correlated turnout factor doing what it was added to do.
#
# For the record, alongside these: no realised pool band is the configured one,
# and two separate steps are responsible. See the A/B/C table in the module
# docstring — renormalisation for A-to-B (plan item 3.1), the entrant rescale
# for B-to-C.
# RE-RECORDED 2026-08-18, deliberately: THE LEVEL SHRINK IS ON.
# `montecarlo.compress_levels` now runs on the finished centre vector, pulling
# each party's central level down by its own size and giving the mass back by
# renormalising. This is the change of MODEL-LOG §1.44 and it is the largest
# single improvement this model has had: at nine city-years and 1500 draws,
# coherent seat error 312 -> 264, CRPS 264.8 -> 236.4, beats-uniform-swing
# 6/9 -> 8/9.
#
# The prior therefore MUST move, and it moves in the direction the mechanism
# claims: the big come down and the small go up. ANC mean 21.71% -> 20.72%
# (p5 6.59 -> 5.66, p95 40.46 -> 39.35), Al Jama-ah 1.25% -> 1.55% (p95
# 2.65 -> 3.20). A re-record where the ANC rose or Al Jama-ah fell would mean
# the shrink was wired backwards, so these signs are the guard, not noise.
#
# What is NOT a change: `level_shrink = 0.0` is exactly the identity in
# `compress_levels`, asserted by
# `test_the_level_shrink_is_exactly_the_identity_when_it_is_off`, so the
# previous prior is recoverable by that one override.
# RE-RECORDED 2026-08-19, deliberately, and this one is different in kind from
# the others above: THE FIXTURE WAS TESTING A LEVEL CONFIGURATION THE FORECAST
# NEVER RUNS.
#
# `build_inputs` loaded the pool spec and stopped. It never ran the spine and
# never built a theta prior, so every party reached `blended_centres` with
# neither, fell through the precedence chain, and took its centre from
# `theta_mode`, `individual_theta` or `f_other`. Those three were deleted on
# 2026-08-19 (§1.52) as dead — dead in the FORECAST, where the spine reaches
# every party at every target — and deleting them is what exposed this: the
# golden prior had been anchored on them, and on nothing the model uses.
#
# It also explains a silence. When §1.49 changed what `theta_prior` shrinks
# toward, these values did not move, and that was read as confirmation the
# change was inert. It was not confirmation: the fixture was not calling
# `theta_prior` at all.
#
# The fixture now builds the level the way `run_model` does. The prior moves a
# long way because it is a different code path, not because the model changed:
# ANC 21.71 -> 21.28 with a much tighter band (6.59-40.46 -> 10.19-34.53), DA
# 27.95 -> 24.51, ASA 12.48 -> 14.12, MK 7.25 -> 10.12. The spine's levels are
# better informed than a residual bucket of 1.30, so the bands narrow.
#
# The nine-city-year backtest is UNAFFECTED and was not re-run for this: it goes
# through `run_model`, which always built the level this way. This changes only
# what the golden test characterises.
# RE-RECORDED 2026-08-27, DELIBERATELY, AND THE REASON IS THE POINT.
#
# `projected_pool_shares` now trends on a RATE OF CHANGE rather than a
# difference (MODEL-LOG §1.102), which moved these by 0.02-0.11pp. A golden must
# never be re-recorded to accommodate a change that has not earned it, so this
# waited for evidence, and the evidence is §1.103: the same change is
# BIT-IDENTICAL across all sixteen backtest city-years on seats, CRPS and
# median_sum, with only 1e-6 float-summation noise in the MAE columns.
#
# That is not a null result. `_target_roll`, this projection and the census
# level bias all touch ONLY the target with no result file yet, because every
# backtest year reads its own published roll. So the change reaches the 2026
# forecast and nothing else — which is what it was built for, and the one case
# no backtest can adjudicate. **These goldens are the only guard on it.**
# RE-RECORDED 2026-09-01, DELIBERATELY. ONE CAUSE, AND IT IS ISOLATED: AN
# ENTRANT WITH NO MEASURED VECTOR NO LONGER DRAWS AN EVEN SHARE OF EVERY POOL.
#
# `emit_pools` gave a party it had never measured `np.full(n, 1/n)` — 25% of its
# vote from each of the four pools — as a deliberately visible non-judgement. It
# is not a neutral assumption but an impossible one: at Buffalo City 2016 that
# handed three parties a quarter each of an Indian/Asian pool casting about one
# vote, 228.93x more than the pool can cast, and at Mangaung 2016 the same pool
# casts EXACTLY ZERO and still carried weight. Such a party now spreads as
# `city_mix_for` — the city's own pool composition, the same vector the splinter
# blend already leaned on. For Johannesburg 2026 that is
# (0.5667, 0.0718, 0.0436, 0.3179) instead of (0.25, 0.25, 0.25, 0.25), applied
# to the 21 parties in the spec's `no_measured_vector`.
#
# **WHY THIS IS ATTRIBUTED RATHER THAN ASSUMED.** The specs were re-emitted in
# the same window as `reproject_counts` and a corrected `MUNI_HEAD`, and a
# re-record that guesses among three changes is worth nothing. The pre-emit
# specs were archived before the batch (`archive/pools-preemit-2026-08-31/`), so
# the fixture was rebuilt against the OLD `joburg_pools_2026.json` with
# everything else at today's tree. It reproduces the previous goldens EXACTLY —
# ANC 22.5952, DA 25.8249, ASA 12.7029, all nine to 4 dp — and `blended_centres`
# returns a byte-identical dict on both sides. So none of the movement is the
# level layer, the θ record or the ingest; all of it is the spec, and within the
# spec the only fields that moved are the entrant vectors and the `alpha` they
# imply. Diffed across all eighteen specs: **not one measured party's pool
# vector changed by more than 1e-12.**
#
# The movement, against the 2026-08-27 record:
#   ANC  mean 22.5952 -> 22.4032 (-0.1920)   DA   mean 25.8249 -> 26.0462 (+0.2213)
#   ASA  mean 12.7029 -> 12.7249 (+0.0220)   MK   mean  9.7307 ->  9.7879 (+0.0572)
#   Black African 49.9435 -> 51.1416 (+1.1981)   Coloured 11.4599 -> 10.6379 (-0.8220)
#   Indian/Asian   5.1370 ->  4.2938 (-0.8432)   White    32.1401 -> 32.5595 (+0.4194)
#
# **THE POOL SIGNS ARE THE GUARD, NOT NOISE.** Johannesburg's votes are far more
# Black African than a quarter and far less Indian/Asian, so moving the
# unmeasured parties off a uniform vector must raise the Black African total and
# cut the Indian/Asian one. A re-record with those signs reversed would mean the
# city mix had been wired in backwards.
#
# **THE PRIOR HOLD IS DISCHARGED, AND NOT BY WAITING IT OUT.** The docstring on
# `test_party_marginals_match_recorded` said do not re-record until the pre-2011
# ingest's 26-seat regression was disposed of. It has been: the seven metros'
# pre-2011 files are quarantined in `levels.HELD_BACK` pending diagnosis, and
# Johannesburg's — the only ones this fixture reads — were live throughout. The
# measurement above is what settles it rather than asserts it: with the old spec
# the goldens return to the digit, so the ingest reaches this fixture by no path
# at all.
#
# NOT RE-RUN FOR THIS, AND NOT CLAIMED: the sixteen-city-year panel. This
# records where the 2026 Johannesburg prior now is. No improvement is claimed
# and none is measured here.
GOLDEN_PARTIES: dict[str, tuple[float, float, float]] = {
    "ANC": (22.2875, 10.7889, 35.6798),
    "DA": (25.9431, 17.5981, 34.8131),
    "EFF": (10.1439, 2.9304, 20.3597),
    "ASA": (12.8348, 4.9102, 23.7333),
    "MK": (9.7843, 2.9457, 19.3101),
    "PA": (6.4693, 3.8250, 10.1637),
    "VFPLUS": (0.8705, 0.0061, 3.1078),
    "ALJAMAAH": (0.9284, 0.2365, 1.9056),
    "ENTRANT": (1.4183, 0.0000, 7.6156),
}
GOLDEN_POOLS = {
    "Black African": (50.0040, 41.9782, 57.7050),
    "Coloured": (10.3865, 7.7146, 14.2273),
    "Indian/Asian": (4.2782, 3.3381, 5.4242),
    "White": (32.3526, 25.9927, 38.9946),
}

WATCHED = ("ANC", "DA", "EFF", "ASA", "MK", "PA", "VFPLUS", "ALJAMAAH", "ENTRANT")


# --------------------------------------------------------------------------
# fixture: rebuild exactly the inputs montecarlo.main hands to make_drawer
# --------------------------------------------------------------------------

def build_inputs():
    """Return (scenario, base_city_d, centres, index) as ``main`` assembles them."""
    city = cityconfig.load(CITY)
    cityconfig.use(CITY)
    mc.apply_city(city)
    scenario = copy.deepcopy(mc.DEFAULTS)

    base_path = ELECTIONS / "npe2024_{CODE}_vd_party.csv"
    if not cityconfig.resolve_path(base_path).exists():
        skip(f"no national baseline for {CITY} at {base_path} — the prior "
             f"cannot be rebuilt without it")
    base_votes, _ = mc.load(base_path, None)
    base_city_d = mc.citywide(base_votes)

    universe = sorted(p for p in base_city_d if p not in (mc.INDEPENDENT, "IND"))
    if scenario["entrant_prob"] > 0:
        universe.append("ENTRANT")
    index = {party: i for i, party in enumerate(universe)}

    lge_path = ELECTIONS / "lge2021_{CODE}_vd_party_clean.csv"
    if not cityconfig.resolve_path(lge_path).exists():
        skip(f"no 2021 result file for {CITY} at {lge_path}")
    pr21, _ = mc.load(lge_path, "PR")
    share_2021 = mc.citywide(pr21)

    bye: dict[str, tuple[float, float]] = {}
    bye_path = PROCESSED / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                bye[row["party"]] = (float(row["weight_sum"]),
                                     float(row["weighted_delta"]))

    # The drawer has no engine without pools, so the fixture must load the
    # measured spec exactly as run_model does — otherwise this file would test
    # a configuration the forecast never runs.
    spec_path = city.processed / "pools_2026.json"
    if not spec_path.exists():
        skip(f"no pool spec at {spec_path} — run: python src/pools.py "
             f"--city {CITY} --target 2026 --emit")
    scenario["pools"] = json.loads(spec_path.read_text())["pools"]

    # THE LEVEL LAYER, as `run_model` builds it — added 2026-08-19.
    #
    # Until then this fixture loaded the pools and stopped, so every party
    # reached `blended_centres` with no spine level and no theta prior and fell
    # through to `theta_mode`, `individual_theta` and `f_other`. **The golden
    # prior was therefore characterising a level configuration the forecast
    # never runs** — the spine reaches every party at every real target — and it
    # was anchored on the three constants deleted in §1.52. It is also why the
    # goldens did not move when §1.49 changed `theta_prior`: they were not
    # using it.
    #
    # The comment ten lines above says this fixture must load the spec "exactly
    # as run_model does — otherwise this file would test a configuration the
    # forecast never runs". That was true of the pools and false of the level.
    import levels as _levels
    _target = cityconfig.use_target("2026")
    _prior, _groups = _levels.theta_prior(_target, base_city_d)
    if _prior:
        scenario["theta_prior"] = _prior
        scenario["_theta_sd"] = _groups.get("sd", {})
    _spine, _ = _levels.spine(_target, base_city_d, share_2021)
    if _spine:
        scenario["spine_level"] = _spine

    centres, _ = mc.blended_centres(scenario, base_city_d, share_2021, bye)
    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0
    return scenario, base_city_d, centres, index


_CACHE: dict[int, tuple] = {}


def draw_matrix(draws: int = DRAWS, cache: bool = True):
    """Return (matrix (draws x parties), index, scenario, base_city_d, centres).

    Cached per draw count so the suite reads the input files once rather than
    once per test; ``cache=False`` forces a genuinely fresh build, which is how
    the determinism test earns its keep.
    """
    if cache and draws in _CACHE:
        return _CACHE[draws]
    scenario, base_city_d, centres, index = build_inputs()
    rng = np.random.default_rng(SEED)
    draw = mc.make_drawer(scenario, base_city_d, centres, index, rng)
    matrix = np.array([draw() for _ in range(draws)])
    result = (matrix, index, scenario, base_city_d, centres)
    if cache:
        _CACHE[draws] = result
    return result


def marginals(column: np.ndarray) -> tuple[float, float, float]:
    return (float(column.mean() * 100),
            float(np.percentile(column, 5) * 100),
            float(np.percentile(column, 95) * 100))


def triangular_quantile(low: float, mode: float, high: float, p: float) -> float:
    """Exact quantile of Triangular(low, mode, high) -- no sampling noise."""
    mode = min(max(mode, low), high)
    split = (mode - low) / (high - low)
    if p <= split:
        return low + math.sqrt(p * (high - low) * (mode - low))
    return high - math.sqrt((1 - p) * (high - low) * (high - mode))


def _pools(scenario, base_city_d, centres, index):
    return mc.pool_spec(scenario, centres, index)


def configured_pool_band(name, scenario, base_city_d, centres, index):
    """Stage A: the 5th-95th percentile this pool's own configuration implies.

    A pool moves by a RATIO on its base, not by a shift in points, so the band
    is base x the ratio triangular's quantiles. Taken from ``mc.pool_spec`` so
    the mode is the one the sampler was actually asked for, including the
    one-sided-range reflection it applies.
    """
    spec = _pools(scenario, base_city_d, centres, index)
    _idx, registered, turnout, _props, _alpha, _names, _levels, _wts = spec[name]
    low, mode, high = turnout

    # A pool's SHARE, not its vote count. Registration is counted and turnout
    # is drawn, so the pool's share of the city is
    #     reg_g * t_g / sum_h(reg_h * t_h)
    # and the denominator moves with every pool. The band below holds the other
    # pools at their modal turnout and moves this one, which is the like-for-
    # like comparison against a sampled share. An earlier version multiplied a
    # registration count by a turnout quantile and reported a band of 59
    # million, having been written when the pool's base was a vote share.
    others = sum(spec[nm][1] * spec[nm][2][1] for nm in spec if nm != name)

    def share_at(quantile: float) -> float:
        t = triangular_quantile(low, mode, high, quantile)
        mine = registered * t
        return 100.0 * mine / (mine + others) if mine + others else 0.0

    return share_at(0.05), share_at(0.95), (low, mode, high)


def before_entrant_rescale(matrix: np.ndarray, index: dict) -> np.ndarray:
    """Stage B: the draws as they were before ``target *= (1.0 - share)``.

    The entrant rescale (montecarlo.py:665-669, and :621-625 in the pooled
    engine) is exactly invertible from the output: it scales every established
    party by ``1 - share`` and then parks ``share`` in the entrant's slot, so
    dividing the vector by ``1 - matrix[:, ENTRANT]`` and zeroing that slot
    recovers the post-renormalisation vector to floating-point precision. That
    is what lets this file attribute each distortion to the step that caused
    it without reimplementing ``draw()``.
    """
    entrant = index.get("ENTRANT")
    if entrant is None:
        return matrix.copy()
    share = matrix[:, entrant]
    out = matrix / (1.0 - share)[:, None]
    out[:, entrant] = 0.0
    return out


def pool_total(matrix: np.ndarray, index: dict, scenario, name: str) -> np.ndarray:
    """A pool's share of the vote, per draw.

    A party contributes to a pool in proportion to the share of its vote that
    comes from there, so this is the weighted sum -- not a membership count.
    """
    members = scenario["pools"][name]["members"]
    total = np.zeros(matrix.shape[0])
    for party, weight in members.items():
        if party in index:
            total += float(weight) * matrix[:, index[party]]
    return total


def pool_band(matrix, index, scenario, name: str) -> tuple[float, float]:
    total = pool_total(matrix, index, scenario, name)
    return (float(np.percentile(total, 5) * 100),
            float(np.percentile(total, 95) * 100))


def stages(name: str):
    """(A, B, C) bands for one pool, plus its ratio triangular."""
    matrix, index, scenario, base_city_d, centres = draw_matrix()
    a_p5, a_p95, spec = configured_pool_band(
        name, scenario, base_city_d, centres, index)
    b_p5, b_p95 = pool_band(before_entrant_rescale(matrix, index), index,
                            scenario, name)
    c_p5, c_p95 = pool_band(matrix, index, scenario, name)
    return (a_p5, a_p95), (b_p5, b_p95), (c_p5, c_p95), spec


# --------------------------------------------------------------------------
# tests
# --------------------------------------------------------------------------

def test_every_draw_is_a_probability_vector():
    matrix, _, _, _, _ = draw_matrix()
    sums = matrix.sum(axis=1)
    assert np.all(matrix >= 0), "a target vector contained a negative share"
    assert np.allclose(sums, 1.0, atol=1e-9), (
        f"target vectors do not sum to 1 (min {sums.min()}, max {sums.max()})")


def test_party_marginals_match_recorded():
    """The realised per-party marginals are what they were when recorded.

    **THE HOLD THAT STOOD HERE FROM 2026-08-22 IS DISCHARGED, 2026-09-01.**

    It said: do not re-record, because the pre-2011 ingest had enlarged the θ
    record from n=257 to n=370, moved the θ prior for every city-year, and cost
    26 coherent seats on the nine city-years that existed before it (254 → 280,
    §1.70) — a regression whose disposition was undecided, so a re-record would
    have frozen a prior that scored worse and erased the only signal that it
    moved.

    Two things closed it. The seven newly ingested metros are quarantined in
    `levels.HELD_BACK` pending a stated diagnosis — present and correct, not
    fed to the model — while Johannesburg's own pre-2011 files, the only ones
    this fixture reads, were live throughout and never held. And the hold was
    then tested rather than assumed: rebuilding this fixture against the
    archived pre-emit spec reproduces every previous golden to four decimal
    places with byte-identical centres, so the ingest reaches these values by no
    path at all. The reason for the re-record, and the measurement behind it,
    are with the GOLDEN_PARTIES block above.
    """
    if not GOLDEN_PARTIES:
        skip("no GOLDEN_PARTIES recorded — run: "
             "./.venv/bin/python tests/test_drawer.py --record")
    matrix, index, _, _, _ = draw_matrix()
    drift = []
    for party, want in sorted(GOLDEN_PARTIES.items()):
        assert party in index, (
            f"{party} has left the party universe; the prior has changed shape, "
            f"not just scale")
        got = marginals(matrix[:, index[party]])
        for label, a, b in zip(("mean", "p5", "p95"), got, want):
            if abs(a - b) > TOL:
                drift.append(f"{party} {label}: recorded {b:.4f}%, now {a:.4f}% "
                             f"({a - b:+.4f}pp)")
    assert not drift, (
        "the citywide prior has moved from its recorded behaviour:\n  "
        + "\n  ".join(drift)
        + "\n\nIf this change was deliberate, re-record with "
          "`./.venv/bin/python tests/test_drawer.py --record` and say so in "
          "MODEL-LOG.md. If it was not, something changed the forecast.")


def test_pool_marginals_match_recorded():
    if not GOLDEN_POOLS:
        skip("no GOLDEN_POOLS recorded — run: "
             "./.venv/bin/python tests/test_drawer.py --record")
    matrix, index, scenario, _, _ = draw_matrix()
    drift = []
    for name, want in sorted(GOLDEN_POOLS.items()):
        assert name in scenario["pools"], (
            f"pool {name} has left the spec; the prior has changed shape, not "
            f"just scale. Re-emit and re-record deliberately.")
        got = marginals(pool_total(matrix, index, scenario, name))
        for label, a, b in zip(("mean", "p5", "p95"), got, want):
            if abs(a - b) > TOL:
                drift.append(f"{name} {label}: recorded {b:.4f}%, now {a:.4f}% "
                             f"({a - b:+.4f}pp)")
    assert not drift, ("pool totals have moved from their recorded behaviour:\n  "
                       + "\n  ".join(drift))


def _largest_pool(scenario, base_city_d, centres, index) -> str:
    spec = _pools(scenario, base_city_d, centres, index)
    return max(spec, key=lambda name: spec[name][1])




def test_entrant_rescale_pushes_every_pool_down():
    """ATTRIBUTION GUARD — this one must survive the fix for plan item 3.1.

    Renormalisation pulls a band inward. The entrant rescale is a separate,
    later step that scales every established party by ``1 - share`` on the
    draws where the hypothetical entrant takes one, so it moves every pool
    DOWN. Read off the final output alone the two are indistinguishable, and
    fixing 3.1 will not close the part this step causes. This test exists so
    that the next person to read this file is not sent after a defect that is
    not there.
    
    This test carried a "FAILING DELIBERATELY SINCE 2026-08-22" note pointing at
    `test_party_marginals_match_recorded`'s hold. **It is passing, and was
    passing before that hold was discharged on 2026-09-01** — it asserts a
    DIRECTION, not a recorded number, so the θ prior moving underneath it never
    could have made it red. The note was inherited from the neighbouring
    docstring rather than observed, and it is removed so that a genuinely red
    result here is read as one. Note removed 2026-09-01.
    """
    _m, index, scenario, base_city_d, centres = draw_matrix()
    offenders = []
    for name in scenario["pools"]:
        (_a5, _a95), (b_p5, _b95), (c_p5, _c95), _spec = stages(name)
        if c_p5 - b_p5 >= 0:
            offenders.append(f"{name}: p5 moved {c_p5 - b_p5:+.3f}pp "
                             f"({b_p5:.2f}% -> {c_p5:.2f}%)")
    assert not offenders, (
        "the entrant rescale no longer pushes these pools' lower tails down:\n  "
        + "\n  ".join(offenders)
        + "\n\nIf entrant_prob or entrant_share changed this is expected and "
          "the docstring should be re-measured (`--decompose`); if they did "
          "not, the rescale step has changed behaviour.")


def test_drawer_is_deterministic_for_a_fixed_seed():
    """Same seed, same draws -- twice."""
    first, _, _, _, _ = draw_matrix(50, cache=False)
    second, _, _, _, _ = draw_matrix(50, cache=False)
    assert np.array_equal(first, second), (
        "make_drawer is not reproducible from its seed; every recorded value "
        "in this file, and every published forecast, is unrepeatable")


# --------------------------------------------------------------------------
# recording
# --------------------------------------------------------------------------

def record() -> None:
    matrix, index, scenario, base_city_d, centres = draw_matrix()
    print(f"# recorded from seed {SEED}, {DRAWS} draws, numpy {np.__version__}")
    print("GOLDEN_PARTIES = {")
    for party in WATCHED:
        if party not in index:
            continue
        m, lo, hi = marginals(matrix[:, index[party]])
        print(f'    "{party}": ({m:.4f}, {lo:.4f}, {hi:.4f}),')
    print("}")
    print("GOLDEN_POOLS = {")
    for name in scenario["pools"]:
        m, lo, hi = marginals(pool_total(matrix, index, scenario, name))
        print(f'    "{name}": ({m:.4f}, {lo:.4f}, {hi:.4f}),')
    print("}")
    decompose()


def decompose() -> None:
    """Print the A/B/C table in the module docstring, with the step deltas."""
    print(f"# decomposed from seed {SEED}, {DRAWS} draws, numpy {np.__version__}")
    _m, _i, scenario, _b, _c = draw_matrix()
    for name in scenario["pools"]:
        (a5, a95), (b5, b95), (c5, c95), spec = stages(name)
        print(f"# {name}  (ratio triangular {spec})")
        print(f"#   A as configured             {a5:7.4f} - {a95:7.4f}")
        print(f"#   B after renormalisation     {b5:7.4f} - {b95:7.4f}"
              f"   (p5 {b5 - a5:+.4f}, p95 {b95 - a95:+.4f})")
        print(f"#   C after the entrant rescale {c5:7.4f} - {c95:7.4f}"
              f"   (p5 {c5 - b5:+.4f}, p95 {c95 - b95:+.4f})")


if __name__ == "__main__":
    if "--record" in sys.argv:
        record()
        raise SystemExit(0)
    if "--decompose" in sys.argv:
        decompose()
        raise SystemExit(0)
    raise SystemExit(run_module(globals()))
