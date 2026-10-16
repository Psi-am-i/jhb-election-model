# Pre-registration: turnout enters the vote (owner decision, 2026-10-16)

Written 2026-10-16 on `remediation` at `45048ae`, before any arm below runs and before
any model code is changed. Not edited after a result is read: scoring goes in
MODEL-LOG and in the README row.

## The change being tested (owner decision, not an option)

Turnout must change the vote the way it does in reality. The mechanism that
redistributes a fixed citywide total over districts by turnout weights is deleted.
Order: preliminary citywide vote → turnout applied per population group in every
district → citywide vote recomputed as the sum of the turnout-adjusted district
votes, and that sum used for shares, wards and seats. Nothing re-pins it to the
preliminary vote. Design: the session's turnout-design specification §2b
(steps 1-3) and §2c, and MODEL-LOG §1.315 for the three locks it removes (the pool
re-fit at the band mode, κ calibrated over drawn turnout, `solve_and_predict`
pinning the citywide share to the drawn target).

**The reference turnout is the owner's call (2026-10-16):** the preliminary vote
is the vote at the turnout the model already uses as its centre, each pool's
band mode (`turnout[1]`, its turnout at the city's last local election) and the
matching district projection from `turnout.csv` (the centre of the pattern
blend, no jitter, no noise). Only a difference between a draw's, a scenario's or
a realised turnout and that centre moves votes. The θ-implied reference of the
specification is not built.

Choices the design leaves open, fixed here before any run (each will be a
declared entry in `JUDGEMENT-CALLS.md`):

- **District pool composition** `c_vg`: registered composition by pool of each
  district's ward at the fitting election (`pools.pool_counts(...).composition
  ("registered")` through `pools.vd_map`), computed at run time beside the
  existing voted composition; a district with no mapped ward takes the citywide
  registered composition. Checked before this file was written (no outcome read):
  the roll-weighted sum matches each spec's pool shares of the roll within 0.006
  at 23 of 24 city-years and 0.0101 at Mangaung 2016 (17.5% of its roll unmapped).
- **District pool turnout per draw**: `T_vg(d) = t_v(d) · T_g / Σ_h c_vh T_h · k_g(d)`,
  `T_g` the band mode, `t_v(d)` today's district draw (pattern blend with jitter,
  lognormal noise), `k_g(d) = drawn pool turnout / band mode` from today's copula;
  clipped to `TURNOUT_DRAW_FLOOR`/`CEILING`. A district with no projection of its
  own takes `T_g` scaled to the city's projected level. The reference `T_ref,vg`
  is the same formula at `k = 1`, the blend centre and no noise.
- **Within-district pool split**: per district, a two-margin IPF of the map's
  shares at reference weights over pools, seeded with the draw's pool split
  `R(d)`; a party in no pool (ENTRANT at the 2011 targets; no individual-path
  party exists at any of the 25 city-years) is seeded evenly across pools.
- **Width record** re-fitted on residuals about each earlier target's centre
  carried to that target's realised pool turnout (`pools.pool_counts` at that
  year); `composition_variance` and `v_comp` deleted.

## Arms (oracle arms are ORACLE DIAGNOSTICS, never forecasts)

All 24 city-years (8 metros × 2011, 2016, 2021), `compare_history.run_city_year`
in process (the canonical scorer, which writes nothing; never `compare_history`'s
main), 1,000 draws, seed 20261104 per city-year in every arm, outputs outside
`data/`. Instruments: list-share MAE (`pr_mae`, `compare_history.vote_mae` on draw
means, points), wards called wrong (`n_wards − wards.called`), seats given to the
wrong party (`seat_abs_err_coherent / 2`).

| arm | code | turnout fed |
|---|---|---|
| C-P | current (`45048ae`) | projected, as shipped |
| C-O | current | ORACLE: realised counted district turnout (target result file, `turnout.read_turnout`) as both turnout patterns, noise and jitter 0; each pool band degenerate at the target's realised pool turnout (`pools.pool_counts` at the target year) |
| N-P | new | projected, as shipped |
| N-Opool | new | ORACLE: district pool turnout = reference × (realised pool turnout / band mode), the same factor in every district; noise, jitter and pool shock off |
| N-Ovd | new | ORACLE: district pool turnout = reference × (realised counted district turnout / projected district centre), the same factor for every pool in a district; noise, jitter and pool shock off |

A district absent from the target's result file keeps factor 1.

## Predictions

Arithmetic already in hand before this file (pool level, no draws, no outcome
read): moving every pool from its band mode to its band mean (the drawn
pool turnout's own mean) moves the DA's centre by −0.2 to −0.7 points and the ANC's
by +0.2 to +0.5 at 19 of 24 city-years (the exceptions: eThekwini 2011 and 2016,
Mangaung 2011, Buffalo City 2011, near zero; Nelson Mandela Bay 2011 DA +0.28);
Johannesburg 2026 DA −0.31, ANC +0.21, EFF +0.08, MK +0.07, ActionSA +0.05
(scratchpad `turnout-build/skew.py`, `skew.txt`). Under the change this skew
reaches the mean (the draws' expected turnout differs from the centre); today κ
re-pins it.

**P1 (control). C-O − C-P:** list MAE equal within 0.10 points at all 24
city-years (current code cannot see turnout in the citywide share: the solve pins
it, κ re-pins the pool layer; the residual difference is Monte Carlo through the
changed width budget, since `v_comp` is 0 for a degenerate band). Wards called
may change by up to 5 at a city-year. Falsified if any city-year moves by more
than 0.10.

**P2. N-P − C-P (the canonical change):** the DA's mean list share lower and the
ANC's higher at 19 of 24 city-years by the skew arithmetic ± 0.25 points; pooled
list MAE change within ±0.25 points; no sign predicted for the pooled list MAE.
Wards called: pooled change within ±15 of 2,183. Wrong-party seats: pooled change
within ±10% of C-P's total. The DA's list-share sd at Johannesburg 2021 within
±30% of C-P's (the floored own term is gone; turnout now adds spread through
votes).

**P3. N-Ovd − N-P (the test of the owner's mechanism with counted turnout):**
pooled list MAE lower, by 0.05 to 0.5 points; lower at ≥ 13 of 24 city-years.
Falsifier: pooled list MAE not lower. Read with P4: if N-Ovd improves and N-Opool
does not, the ecological pool turnout estimate is the defect (mechanism i of the
design); if neither improves, within-pool preference covaries with turnout
(mechanism ii).

**P4. N-Opool − N-P:** pooled list MAE higher (the pool-level centre arithmetic
went 3.039 → 3.721 points, better in 6 of 24); better at ≤ 9 of 24.

**P5. Wards:** wards called wrong differ between N-Ovd and N-P by at least 10
pooled (counted district turnout reaches wards in both codes). No sign.

**P6. Johannesburg 2026, N-P against C-P (5,000 draws, seed 20261104):** mean list
share DA −0.1 to −0.6 points, ANC +0.05 to +0.45, EFF and MK each 0 to +0.2;
mean seats DA −0.3 to −2.0, ANC +0.1 to +1.5; P(largest party) moves by under 5
points for every party; ward favourites changed in ≤ 4 of 135 wards.

**P7. Fixture** (constructed in the test, not read from `data/`): two pools A, B
(100 registered each), two parties X, Y, two districts each half A and half B,
flat geography, pool split R = [[0.8, 0.2], [0.1, 0.9]], reference and expected
turnout 0.5 for both pools, width 0. Baseline X = 0.45 within 1e-9. A's turnout
0.5 → 0.3: X = 29/80 = 0.3625 and Y = 0.6375 within 1e-9, each district's votes
50 → 40. Second case, every district without a projection of its own: the same
citywide result as the pool arithmetic `Σ reg_g T_g R_gp / Σ reg_g T_g`, and a
pure-pool ward's tally scales by its pool's turnout. Each of the three locks put
back by hand (κ calibrated over drawn turnout; `pool_votes` from the band; the
solve at drawn-turnout weights) returns X to 0.45 and turns the test red; reverting
turns it green.

## What would stop the round

If N-P scores worse than C-P on list MAE and wrong-party seats together and N-Ovd
does not score better than N-P (the mechanism explains nothing measurable), the
compare_history commit is not made and the result goes to the owner.
