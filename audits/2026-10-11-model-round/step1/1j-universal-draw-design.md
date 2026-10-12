# 1j. One log-scale draw for every party: design

Owner's decision of 2026-10-12 (MODEL-LOG §1.297), evaluated and specified.
Read-only: nothing in `src/`, `tests/` or `data/` written; no model run, no
`compare_history`, no emit; no sub-delegation. Code read at `0c01313`
(`remediation`).

**Sources.** Realised list shares and the `pool_spec` centres of every party in
arm E's 24 backtest city-years and Johannesburg 2026 (the per-party rows and
centres the 1b and 1e work built and checked: `v2rows.json`, `levellift/ps.pkl`,
`review1b/cells.pkl`, all reproduced from `data/arms/step11/E/*` and the pool
specs whose `artefact_key` matched each run). Arm E draws
(`arrays.npz`: `pr_share_draws`, `pool_turnout_draws`). Scripts in the session
scratchpad, `uni/` (`u1`-`u12.py`, `widths.py`, `curve.py`, `model3.py`,
`final.py`); not committed.

**Labels.** *Measured* = computed in this session from those files. *Argued* =
reasoning or code reading, not tested. *Citywide simulation* = my
reimplementation of the proposed draw at citywide level: the latent draw,
normalisation, and arm E's own pool-turnout draws for the composition effect;
no capacity water-fill, no IPF, no ward ballot. It predicts directions and
sizes; the canonical run measures them.

**The residual.** Throughout, a party's residual is
`r = log(realised list share / pool_spec centre) − log(block realised / block centre)`,
where the block is the parties whose centre is at least 20% in that city-year
(the ANC and DA, except Buffalo City 2011 and Mangaung 2011, where the DA's centre was 15.1% and 19.9%). §1.1 says why the block is
the reference. Windows: the 2011, 2016 and 2021 backtests (eight metros each);
2006 does not enter, because no 2006 backtest exists to give a centre.

---

## Summary for the owner

Today a party's spread comes from two places that ignore each other: a size
line for its overall level, and the within-group split, whose spread depends on
how big a slice of one voter group the party holds. The second one gives small
parties a spike at zero and occasional explosions. This design removes the
split's randomness and gives every party one draw on the log scale, the same
draw the model already uses for a party's overall level, with its width taken
from how far real results landed from the model's own centres in earlier
elections. The width falls smoothly with size, with no line anywhere. Small and
middle parties move together through a shared swing that leaves the largest
parties anchored, and new parties get a wider draw where the record says they
need one. The voter-group split stays as the centre: the drawn citywide shares
are spread over the groups by the existing balancing step, and the only
randomness left between groups is turnout. Measured against the record, most of
the decision stands. Four points do not stand as worded. (1) "Large parties
already match the record" is half true: their draws today are wider than their
real misses (log spread 0.17 drawn against 0.12 realised, 48 cases, 2011-2021),
so the new draw narrows them. (2) A swing applied equally to every party
cancels out when shares are rescaled to 100%; it has to weaken as parties get
bigger, and the record shows this. (3) The wider treatment for new parties is
clearly supported for parties with no record at all, but not for national
debutants below 1%, who behave like established parties. Above 1%, MK, RISE
and BOSA rest on five precedents. (4) The re-fit of the citywide spread is a
replacement: the new width is measured in the frame the draw uses, so nothing
is left for the split to supply. The weakest point is the middle of the ballot
(5-20%). Only five party-elections inform it, and in 2026 that band holds about
38% of Johannesburg's vote. The fitted widths narrow ActionSA and the EFF
sharply, and that is an extrapolation. At Johannesburg 2026 (citywide
simulation, 5,000 draws, four seeds), draws in which a party that had under 1%
last time exceeds 5% fall from 403 to about 35. Small parties keep a typical
draw near two-thirds of their centre instead of near zero. The ANC's spread
halves.

---

## 0. The decision, point by point, against the record

| part of the decision | verdict | evidence (measured unless marked) |
|---|---|---|
| one log-scale draw for every party, no size line | supported | 1f §2.2: below 5% the Dirichlet puts 7-80% of draws below a tenth of the centre where the record puts 0-3%; the literature (1i §4) uses one per-party log-ratio draw |
| spreads from the record by size and history | supported, with a smooth curve rather than bands | residual width rises from 0.07 at 25% of the vote to about 0.99 below 1% (§2.3); the record has too few middle-sized cases for bands to stand alone |
| a shared cycle swing | supported **only with a loading that falls with size** | a common log shift on every party is undone by normalisation (argued, algebra). The record's swing is small parties against the large block: cycle means of `r` by centre band, 2011 −0.41 to −1.16, 2021 −0.07 to +1.01 (§3.1) |
| a metro factor | supported, small | between-metro share of standardised residual variance 0.06 (§2.4); it loads like the cycle factor, so within one city the two are one draw |
| each party's own term | supported; heavy-tailed | own-term excess kurtosis 1.92, cluster bootstrap 90% interval 1.06-2.52 (Student-t with 7 df: 2.0) |
| a separate, wider treatment for parties new to the city | **supported for seeded arrivals, not for national debutants below 1%; thin above 1%** | added width over the established curve (2026 record): seeded arrivals 0.76 (217 cases, 132 party-elections); national debutants under 1% 0.05 (68, 32); national debutants at 1% and over 0.58 (19 cases, 5 party-elections: COPE 2011, AIC and EFF 2016, GOOD and PA 2021) |
| re-fit the citywide spread in the same change | supported, as a **replacement** | today's width is the θ size line (`level_shock_sd`), set narrow because the split carried the rest (MACHINERY §1.50, JUDGEMENT-CALLS §B7: the split supplies 83-98% of drawn variance for every party except the ANC and DA). The new width is the record's residual about the centre the draw conserves, so it already contains what the split supplied (§4) |
| each group's split stays as the centre; only its randomness goes | supported | the pool split reaches nothing but the citywide target, the turnout record and the group-share tripwire: `draw_target` returns one citywide vector and the wards are built from it by `solve_and_predict` (`montecarlo.py:5760-5809`, read) |
| 5% line withdrawn; class pooling later | supported; seam in §1.7 | — |
| "large parties already match the record" | **half true** | arm E, established parties with centre ≥ 15%: drawn log-sd median 0.17 (IQR-based; n 48) against a realised residual sd of 0.12 about the same centres; 1f: 50% band holds 0.70 of results; 1h §4.3: 10.7% of their party-draws fall below the record's lowest retained ratio against 2.1% exchangeable |
| "creating 5000 plausible simulations" | moved toward, not reached | §8.3 lists the plausibility failures that remain, with their cause |

---

## 1. The draw

### 1.1 Scale: latent log level per party, closed by normalisation

Per draw *d* and party *i* with conserved centre `c_i` (the unshocked
`pool_spec` centre):

    x_id = σ_i · ( √ρ_s · z_d  +  √(1 − ρ_s) · ε_id )           established, national debutants
    x_id = σ_arr · a_d  +  ω_i · ε_id                              seeded arrivals
    shocked_id = c_i · exp(κ_i + x_id) / Σ_j c_j · exp(κ_j + x_jd)

- `σ_i` is the width function of §2 at the party's centre, plus the newness
  increment of §5 in the own term; `ρ_s` is the shared fraction (§2.4); `z_d`
  is the one shared normal of the draw; `a_d` the arrival factor; `ε_id` the
  own term.
- **Why the multinomial logit (latent log level, divided by the sum).** It
  needs no reference party; additive log-ratios depend on the reference
  unless the covariance is full (Selb & Chen 2023, fn. 1; 1i §4.3, cited). It
  bounds every share in (0, 1) without clipping. And it is the slot the model
  already uses: `shocked = base_c * log_shock(rng, sds)` then
  `shocked / shocked.sum()` (`montecarlo.py:3288-3290`, read). A per-party
  logit followed by renormalisation was rejected (§10).
- **Why the large block is the reference in the estimator.** Under this
  normalisation the movement of a party carrying 25-60% of the vote is set
  mostly by everyone else's draws; its own latent term is what is left. The
  record agrees: inside the block the residual is 0.05 (within-block log
  residual, 46 cases, 2011-2021), and the block as a whole moves with the rest
  (block log(realised/centre) cycle means +0.11 / −0.01 / −0.06 while the parties
  below 20% moved −0.4 to −1.2 / −0.3 to +0.4 / −0.1 to +1.0). Measuring the
  others' residual relative to the block puts the record in the frame the draw
  produces.

**The ward link is unchanged.** `ward_target = pr_target * ratio`
(`montecarlo.py:5770`) stays as it is. The drawn citywide vector is the only
input the ward path takes from this change.

**Path after the draw (unchanged code, argued).** `capped_targets` water-fills
the shocked shares under each party's pool capacity; `_balance` (IPF) turns
them into per-pool proportions; each pool's vote is its registration times its
drawn turnout; the citywide target is the turnout-weighted sum of the pool
proportions. The within-pool split becomes `split = moved` (the post-IPF
proportions): no Dirichlet, and no mean floor, because the floor existed only
to keep Dirichlet concentrations positive (`montecarlo.py:3359-3375`, comment)
and flooring a deterministic split would add mass no centre asked for.

### 1.2 Exact expectation: a calibration pass through the real path

1b's correction was per cell and analytic because its cells bypassed the
balance. Here every party passes through the capacity water-fill, the IPF and
the turnout weighting, which are not linear. Two options were weighed:

- (a) **calibration pass (recommended).** Before the run's draws, `make_drawer`
  runs `N_CAL` draws through the same `draw_pools` code on a dedicated set of
  keyed calibration streams (§1.6), starting at `κ_i = o(σ_i)` (the family's
  own log-mean offset, `−σ_i²/2` for a normal), and iterates
  `κ_i ← κ_i + log(c_i / mean_d target_id)` until the largest relative error
  is below `KAPPA_TOL`. `κ` is then fixed for the run. Because the streams are
  keyed and fixed, `κ` is deterministic for a given run identity, and a
  1,000-draw and a 5,000-draw run share it.
- (b) declare conservation approximate. Today's `log_shock` has no mean
  correction at all, so (b) is not a regression. It fails the decision's
  wording, though: the group split is supposed to stay as the centre.

Cost of (a) (argued from 1c §2.8's per-draw figures, not measured on the
model): IPF about 0.15 ms per draw; `N_CAL` = 4,000 with about five iterations
is 20,000 drawer calls, about 5-10 s per city-year. Residual Monte Carlo error
of a run mean against `c_i`, at width 1.0 and 5,000 draws: about 2% relative.
The run records the calibration's final error per party
(`41_guards.kappa_error`) and the run's own mean error
(`41_guards.mean_error`). The falsifier is a mean drawn share more than 5%
relative from its `pool_spec` centre for any party with centre ≥ 0.1%: 1b's
falsifier 2, about three Monte Carlo standard errors.

**The calibration pass records nothing.** `draw_pools` appends to
`turnout_record` and `split_record` and increments `ipf_stats` on every call.
The calibration draws run with recording off, and every counter is reset
before draw 0. Otherwise `pool_turnout_draws` gains `N_CAL` rows, which breaks
`test_draw_record` check 2 and the interactive's reweighting, and
`ipf_clipped` and `balances` are inflated. A test asserts
`len(turnout_record) == draws` and that the counters equal a run without the
pass.

### 1.3 Renormalisation and capacity

Shares close by the normalisation in §1.1. The capacity water-fill fires when a
shocked share asks for more than 98% of the pools a party belongs to
(`POOL_CAPACITY_MARGIN`, §A28). It is counted in `ipf_stats["clipped"]` as now,
and the calibration pass absorbs its effect on the mean. Expected to bind more
often for a party concentrated in one pool whose width rises. The PA at
Johannesburg 2026 is the case: its width goes from 0.30 to 0.56 (§8.2) against
a Coloured-pool capacity. Its firing rate is a reported quantity.

### 1.4 Tails

| term | family | evidence |
|---|---|---|
| own term `ε` | Student-t, `LEVEL_DF` = 7, standardised to unit variance (as `log_shock` does) | own-term deviations of established parties below 20% about their metro-cycle mean, standardised by `σ(s)` (237 cases): excess kurtosis 1.92 (cluster bootstrap over metro-cycles, 90% interval 1.06-2.52); 4.2% beyond 2.5 sd (normal 1.2%), 1.3% beyond 3 (normal 0.27%); skew +0.51. Measured |
| shared factor `z`, arrival factor `a` | normal | three cycles and 16 seeded city-years cannot resolve a factor's tails (argued) |

The literature's warning (Gelman et al. 2020, 1i §4.3, cited) is that
independent long tails per unit lower effective correlation. Here the own
term's tail is the record's own tail, measured after the size curve and the
shared factor are taken out. Some of the measured kurtosis may be party-level
width differences the size curve does not carry. The two causes are not
separated here. Either way, the draws need that rate of large single-party
surprises to match the record. The plausibility check's joint feature (`J`) is
the test. Because shares are bounded, a t own term has a finite mean share, so
the calibration pass of §1.2 works. `o(σ)` for the t is computed by quadrature.
At σ = 1 it differs from `−σ²/2` by about −0.08 (argued from the fourth
cumulant), and the estimator of §2 uses the same `o(σ)`.

### 1.5 Zeros and withdrawal

The logistic-normal has no mass at zero. In the backtests, 16 of 607 parties on
the roster received no votes. All had centres of 0.17% or less, and 13 were
seeded arrivals (measured). None could win a seat at that size. No zero
component is added. A withdrawal is a roster fact, handled by the roster
(`roster_for_target`), not by the draw.

### 1.6 Random streams (under 1c, with its review's fixes)

| stage | name | kind, values per draw | transform |
|---|---|---|---|
| `level.z` | party | z, 1 | own term numerator (as 1c) |
| `level.chi` | party | z, J and u, J+1 | t denominator, `log_gamma_slots(df/2, …)`, boosted at every shape (2-review-1c finding 1) |
| `level.shared` | `""` | z, 1 | `z_d` |
| `level.arrival` | `""` | z, 1 | `a_d` |
| `calib.<stage>` for each of the four above, `calib.turnout.common`, `calib.turnout.pool` | as the stage | as the stage, rows 0 … `N_CAL` − 1 | calibration pass only |

- The own term keeps 1c's `level.z` / `level.chi` keys, so an arm comparison
  against a 1c-based baseline stays paired in the own primitives.
- `split` streams are no longer read. `arrival.*` and `entrant.*` are
  unchanged.
- The cycle and metro factors are estimated apart (§2.4), but within one
  city-year their loadings are the same vector (`σ_i·√ρ`), so one stream
  carries their sum. Keying them apart would buy nothing in a run and would add
  a stream the tests must account for.
- Pairing across this change: every party changes path (split to none), so the
  change itself is unpaired by design (1c §2.6). Arms built on it, such as a
  width variant or a pooled class, are paired.

### 1.7 The seam for a pooled small-party class

A pooled class is a set of parties that share one `level.z` / `level.chi` key
(the class label) and draw their own term from one class width; the shared
factor, the calibration pass and everything downstream are unchanged. Not
designed here.

---

## 2. The width function

### 2.1 What it depends on

- **Size**: the party's `pool_spec` centre, through one smooth curve. No bands
  in the draw.
- **History**: established (stood at the previous local election in this
  city), national debutant (no previous local result, a result at the
  preceding national election in this city), seeded arrival (neither). §5.
- **Not used**: pool concentration. 1f §2.3 measured it as real (realised abs
  log error falls with log `a_eff`, coefficient −0.24, se 0.06). Adding it
  would bring pool structure back into the width. Deferred; §10.

### 2.2 The curve and its estimator

    σ(s) = a + (b − a) / (1 + exp(k · (log s − log m)))

Fitted per target year by weighted maximum likelihood over established parties
in earlier backtest cycles, all sizes (large-block members enter with their
within-block residual):

    r_i ~ Normal( o(σ(s_i)),  σ(s_i)² ),   weight w_i = 1 / (metros the party stood in, that cycle)

The normal is a working likelihood for the second moment. The mean is the
drawn family's own offset `o(σ)` (t7 own term, normal shared factor, §1.4), so
the estimator and the draw agree on the location. The figures below used
`−σ²/2`; the writer uses `o(σ)` by quadrature, a difference of about 0.08 in
the offset at σ = 1 (argued).

- **Mean offset `o(σ)`, not zero.** A mean-preserving draw implies a mean log
  residual of `o(σ)` (`−σ²/2` for a normal), not 0 (1b addendum 2, adopted).
  Measuring spread about zero counts the draw's own offset as uncertainty.
- **Cluster weights.** One party in eight metros in one cycle is one event for
  its own term. Observation weights let the national parties dominate.
  Section 2.3 reports both.
- **Out of sample.** Target 2016 from the 2011 backtests; 2021 from 2011 and
  2016; 2026 from all three.
- **Estimation, not tuning (CLAUDE.md §4).** The target is the realised
  dispersion of the vote about a centre that does not depend on any width
  (the draw conserves it). No coverage, PIT, seat width or realised-over-
  predicted ratio enters. The caveat from 1b (2-recheck-1b-v2, N6) carries
  over: `level_shrink` was chosen on Johannesburg 2016 and the 2021 panel, so
  the 2021 and 2026 widths are residuals about centres partly selected on
  those outcomes.

### 2.3 Fitted widths (measured)

| target | `a` | `b` | `m` | `k` | n / party-elections | σ at 25% | 10% | 5.8% | 3% | 1.5% | 0.5% | 0.05% |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 0.005 | 1.231 | 5.70% | 1.64 | 74 / 24 | 0.10 | 0.35 | 0.61 | 0.91 | 1.11 | 1.21 | 1.23 |
| 2021 | 0.023 | 0.994 | 9.43% | 2.86 | 165 / 54 | 0.08 | 0.47 | 0.80 | 0.96 | 0.99 | 0.99 | 0.99 |
| 2026 | 0.029 | 0.991 | 7.82% | 2.58 | 283 / 95 | 0.07 | 0.36 | 0.69 | 0.92 | 0.98 | 0.99 | 0.99 |
| 2026, observation weights | 0.023 | 0.870 | 7.64% | 2.21 | 283 | 0.08 | 0.32 | 0.57 | 0.77 | 0.85 | 0.87 | 0.87 |

Cross-checks (measured, same residual frame, 2011-2021):

- **Band estimates.** The same offset-aware estimator per band: 1-5% 0.83 (35
  cases, 18 party-elections); 0.3-1% 0.82 (88, 35); 0.1-0.3% 0.91 (61, 37);
  below 0.1% 0.995 (41, 34; no root: the band's mean residual is +0.75, so its
  centres sit far below results and the excess is a level report, §8.3).
- **The thin middle.** 5-20% has 12 cases from 5 party-elections: IFP and the
  Minority Front in eThekwini 2011 and VF+ Tshwane 2011 (collapses, residuals
  −0.34 to −1.31), the DA in Buffalo City and Mangaung 2011 (centres 15.1% and
  19.9%, residuals +0.19 and +0.18), and the EFF 2021 in seven metros
  (residuals −0.24 to +0.07).
  Its own band estimate is not computable at a minimum of 8 party-elections.
  The curve's 8-15% stretch is pinned by EFF 2021 and the large block.
- **Earlier measurements agree in level.** 1b addendum 2's established width
  below 1% for 2026 was 1.002. 1f §4.1's record movement (next over previous
  share) is 0.21 at ≥ 15%, 0.45 at 5-15% and 0.68-0.90 below 5%.

### 2.4 Shared fractions (measured)

Standardised residuals `u = (r − o(σ(s)))/σ(s)` of established parties below
20%. The cycle component is the mean over cycles of (cycle mean of `u`)²,
less its sampling noise; the metro component comes from a one-way ANOVA within
cycles; the rest is the own term.

| target | cycle share | metro share | own share | cycle means of `u` |
|---|---|---|---|---|
| 2016 | 0.14 | 0.07 | 0.79 | 2011 −0.72 |
| 2021 | 0.27 | 0.08 | 0.65 | −0.77 / +0.24 |
| 2026 | 0.38 | 0.06 | 0.56 | −0.73 / +0.27 / +0.88 |

`ρ_s` = cycle + metro share (0.44 for 2026). 1f §4.1 put the cycle at 15-40%
of a small party's variance on a different frame (record movement). The cycle
component rests on two, two and three cycles. For 2016 the curve and the cycle
mean come from the same single cycle, so the 0.14 is low by construction
(argued).

### 2.5 The turnout composition is subtracted, not added

The one source of between-group randomness that stays is pool turnout. It moves
party shares through the group mix. Composition-only log-sd (unshocked pool
proportions, arm E's own pool-turnout draws, measured): medians 0.040 at ≥ 15%,
0.025 at 5-15%, 0.012-0.030 below 5%. JHB 2026: DA 0.074, ANC 0.049, EFF
0.047, PA 0.150. This is the size of the large parties' own term (0.05), so it
cannot be ignored. The record residuals already contain real differential
turnout. Each party's own-term variance is therefore
`σ_own,i² = max(σ_i²·(1 − ρ_s) − v_comp,i, 0)`, with `v_comp,i` computed from
the run's own turnout bands (no outcome read). This is MACHINERY's existing
rule that each layer carries a conditional share (§1.50). A party at the zero
floor is listed in `41_guards.width_floored`.

### 2.6 Fallbacks

- **2011: no earlier backtest.** The writer uses 1b v3's fallback (forward θ
  residual of target 2006: 0.27 with θ history, 0.48 without), labels 2011
  "width not testable" in every report, and excludes it from every coverage
  falsifier. That fallback is measured about `theta_prior`'s centre, which
  lacks the `compress_levels` lift and the 2011 local-route collapse. The 2011
  bands are therefore too narrow by construction, and now nothing else widens
  them. 1b v3 measured 2011 coverage at 0.30 under that fallback.
  Alternatives are listed for the owner in §7.
- **Too little data for the curve.** If a target has fewer than 20 established
  party-elections, the curve takes the previous target's record. A target with
  no previous record stops the run, as `level_shock_sd` does today. No typed
  fallback (§A29's rule).
- **Seeded arrivals for 2016.** The 2011 backtests carried the `ENTRANT` slot,
  not seeds, so there is no earlier seed record. The 2016 seed increment takes
  the national-debutant increment, declared.

### 2.7 Where the widths live

The 1b writer is generalised: `src/width_record.py --emit` writes
`data/processed/width_record.json`. Per target year it holds the curve
parameters, the shared fractions, the newness increments, the arrival factor,
n and party-elections for each, the cycle means, the band cross-checks, cluster
bootstrap intervals, and every fallback row, labelled. It computes earlier
targets' `pool_spec` centres through the functions `run_model` uses, with no
draws. Its artefact key covers the centres' inputs, `level_shrink` and
`level_shrink_scale`, the source hash of `compress_levels` (1b addendum 2 §5),
and the residual block's definition. `make_drawer` refuses a missing record, a
stale one, or one whose key does not match the run's scenario. Couplings:

- run it in a re-emit window;
- name it in CLAUDE.md §5 and `ENTRY_POINTS`;
- it replaces the planned `unit_width_record.py`, which was never written
  (`src/unit_width_record.py` does not exist, checked).

---

## 3. Shared structure

### 3.1 The cycle swing is fragmentation against the large block

Cycle means of `r` by centre band, established parties (measured):

| cycle | 5-20% | 1-5% | 0.3-1% | 0.1-0.3% | < 0.1% | large block, log(realised/centre) |
|---|---|---|---|---|---|---|
| 2011 | −0.41 (n 5) | −0.83 (12) | −1.02 (31) | −1.16 (10) | −0.66 (2) | +0.109 |
| 2016 | — | −0.16 (9) | −0.33 (33) | −0.14 (21) | +0.43 (12) | −0.012 |
| 2021 | −0.07 (7) | +0.01 (14) | +0.21 (24) | +0.41 (30) | +1.01 (27) | −0.063 |

Every band below 20% moves together within a cycle, and the large block moves
the other way. The swing also grows as size falls, which a loading
proportional to `σ(s)` gives: the shared term is `σ_i·√ρ_s·z`, so the ANC and
DA load about 0.07 × 0.66 and a 0.3% party about 0.99 × 0.66 (2026 values).
Large parties then move through the normalisation alone. Loading every party
equally would be inert (argued: a common shift `x_i + δ` leaves
`c_i e^{x_i+δ} / Σ c_j e^{x_j+δ}` unchanged).

### 3.2 How the variances are separated

| component | estimated from | value for 2026 |
|---|---|---|
| total width by size | the curve (§2.2) | §2.3 |
| cycle | mean square of standardised cycle means, less sampling noise | 0.38 of each party's variance |
| metro | between-metro variance of standardised residuals within a cycle | 0.06 |
| own | the rest, less turnout composition (§2.5) | 0.56 |
| seeded arrivals' shared factor | between-city-year sd of seed residuals (16 city-years, 2016 and 2021) | 0.73 |

### 3.3 Does the shared factor scale with size

Yes, through `σ(s)`, for the reason in §3.1. A separate loading function was
tried during this design: weight 1 below 5%, 0 above 20%, linear in log size
between. It was dropped. Band totals built from it overshot the record: for
1-5% parties the components summed to 1.06 against a measured band width of
0.83, because the swing estimated mostly on parties below 1% was applied at
full weight to larger ones (§10).

---

## 4. The citywide re-fit

**What is replaced.** `level_shock_sd`'s two rules, the θ size line at the
party's national share ("measured") and at its baseline share ("size"), stop
being the draw's width. They were clamped to `[SD_FLOOR 0.15, SD_CEILING 1.20]`
and set as a conditional share on the assumption that the split supplied the
rest. JUDGEMENT-CALLS §B7 records that the split supplied 83-98% of drawn
variance for every party except the ANC and DA.

**What replaces it.** `party_width(party, scenario, base_city_d)`, one
definition, reading `width_record.json`: the curve at the party's centre, the
newness increment, the shared fraction, and the run's composition variance. It
is the only width source for every pooled party, every individual-path party
(1f §2.1 row 3, reached by none today) and the poll blend's model sd
(`montecarlo.py:5641`, which today calls `level_shock_sd`; polls are off,
§A8, but the code path must read the same width).

**Why nothing is counted twice.**

- The new width is measured as realised dispersion about the very centre the
  draw conserves, so it already contains every real source of movement: the
  part the θ line carried, the part the split supplied, differential turnout,
  and centre error (the E[k²] reading, CLAUDE.md §4).
- Of the remaining random layers, turnout composition is subtracted (§2.5).
  The VD layer and ward noise move the citywide list share by about 0.3%
  (1f §4.2, `pr_vote_draws` sd/mean 0.003). That is negligible against widths
  of 0.05-1.0 and is left in, declared.
- The entrant slot (2011 only) rescales everyone by `1 − share`. It is a
  separate party and keeps its own band.

**What stays.** `levels.size_sd`, `SD_FLOOR` and `SD_CEILING` still feed
`theta_prior`'s own outputs (`levels.py:1136`, the per-party `sd` and the
trace's spread). The writer checks whether any centre computation reads
`_theta_sd`. If only the drawer and the poll blend do, both register rows say
"no longer a draw width". Changing them is out of scope.

---

## 5. New parties

| class | who | treatment | value for 2026 | evidence (measured, 2011-2021 backtests, cluster-weighted) |
|---|---|---|---|---|
| national debutant | no previous local result here; a result at the preceding national election here (MK, RISE, BOSA at JHB 2026) | established structure, plus an own-term increment δ_deb(s) | δ_deb 0.05 below 0.3%, 0.58 at 3% and above, linear in log size between | under 1%: 68 cases, 32 party-elections, increment 0.05, mean residual −0.15. At 1% and over: 19 cases, 5 party-elections, increment 0.58, mean −0.21. Precedents: COPE 2011 (−1.38 to −2.33 in eight metros), EFF 2016 (+0.15 to +0.44), AIC NMB 2016 (+0.38), GOOD CPT 2021 (+0.22), PA MAN 2021 (−0.02) |
| seeded arrival | no record of any kind in this city (sized by `pools.arrival_rules`) | no load on the established swing; a shared arrival factor among seeds; own term from the established curve plus increment δ_seed | δ_seed 0.76, arrival factor sd 0.73 | 217 cases, 132 party-elections, two cycles |

- **Why not one new-party width.** Pooled over all new parties, the 2026
  increment is 0.28, but it is two populations: seeds (0.76) and national
  debutants (0.05 below 1%). One value would widen small debutants the record
  says behave like established parties, and narrow seeds.
- **MK, RISE and BOSA rest on five precedents.** One of them collapsed
  sevenfold (COPE). The rest landed near or above their centres. A symmetric
  log draw cannot carry that shape, mostly modest gains with an occasional
  collapse. With σ about 0.66 in MK's own term, the citywide simulation puts
  MK's median at 7.9% against a centre of 9.1%, and its p99 at 28.9% against
  arm E's 22.7%.
- **Centre handling is next round.** Two biases are reported here and not
  corrected:
  - seed centres are too high in the mean: seed residual mean −1.07 (2016,
    n 68) and −0.24 (2021, n 153);
  - debutants at 1% and over: mean residual −0.21.

  The offset-aware estimator found a root for the seed class, so part of the
  2016 bias sits inside δ_seed and the arrival factor. When the seed centres
  are corrected, the width record's key forces a re-estimate.
- **No zero component, no withdrawal draw** (§1.5).
- **The `ENTRANT` slot** (2011 runs only) is unchanged.
- **Splinters and merged parties** inherit their history class from
  `pools.emit_pools`' lineage: a splinter with a parent vector is established
  if its code stood at the previous local election, otherwise a national
  debutant or a seed. Argued; the writer lists every party's class in the
  trace.

---

## 6. What is removed, and what every consumer needs

| removed | where | consumer | what it needs |
|---|---|---|---|
| the within-pool Dirichlet as randomness | `montecarlo.py:3376` `rng.dirichlet(moved * alpha)` | `draw_pools` | `split = moved`; `alpha` no longer read |
| the mean floor on pool proportions | `:3374-3375`, `DIRICHLET_FLOOR`, scenario key `dirichlet_floor` | `draw_pools`; `test_levers_are_live` (`dirichlet_floor` 0.05 entry); `backtest.FITTED_ON_UNINSTRUMENTED["dirichlet_floor"]`; the delivery note `note_value(..., "dirichlet_floor", ...)` | delete the constant, the key and the note; JUDGEMENT-CALLS §A30, §F1 and the `dirichlet_floor` half of §F21 marked deleted with the reason. The arrival-group branch (off) keeps its own floor as a local literal registered under §A45, or reads a renamed constant |
| `dirichlet_scale` | `DEFAULTS`, `_dirichlet_scale`, `pool_spec` (`:2830`), arrival group (`:3110`) | `test_citywide_table` (`dirichlet_scale=0.5`, `2.0` cases); `test_levers_are_live` (2.0 entry and the 1965 dict); `backtest.py:400`; `compare_history.py:610, 2335-2423` text; `test_calibration_report.py:1486-1532` docstrings | delete the key and `_dirichlet_scale`; the arrival group reads `group["alpha"]` raw; tests drop the cases; prose that cites the lever is updated to say it is gone (§B7 retired) |
| `pools.dirichlet_alpha` as a width source | `pools.py:3510`, constants `ALPHA_*` (`:4196-4199`), spec field `alpha` (`:6401`) | the draw (no longer) | **not deleted in this change.** Deleting it changes `pools.py` code, which invalidates every spec hash (CLAUDE.md §3). The deletion goes into `POOLS-REEMIT-QUEUE.md` for the next batched re-emit; until then the spec field is emitted and unread, and §F31 and §B7 say so. `make_drawer` asserts it never reads `alpha` (a test patches the field to NaN and the run must be unchanged) |
| zero level shock for seeds | `pool_sd_shock` (`:3152-3158`), §A50 | `make_drawer` | seeds get the seed treatment of §5; §A50 retired |
| `level_shock_sd` as the draw width | `:2926` | `make_drawer`, poll blend `:5641`, `tests/test_spine.py:570-605` | replaced by `party_width`; `test_spine`'s four assertions become assertions on `party_width` for the four history classes |
| `level_sd_at_size` guard | `:3035`, `41_guards` (`:5937`) | `test_stage_realisation` `GUARD_KEYS` | replaced by `41_guards.width` (per party: σ, class, composition variance, floored flag) |
| `log_shock` as the level sampler | `:528` | `width_budget.py`, `test_regressions.py:207`, `test_ipf_feasibility.py:348-371`, `theta_residual.py:547,806` (scoring, own sampler) | under 1c it becomes `log_shock(sd, z, log_chi, df)` and is the own term's transform; the shared and arrival terms are added before `exp`; `theta_residual`'s references stay valid (same t law) |

**`split_record` and the group-share tripwire.** `split_record` keeps recording
each pool's split, which is now the post-IPF proportion. It is deterministic
given the citywide draw and the turnout. The tripwire still means what it
says, because a party whose citywide draw exceeds what its pool vector allows
still shows in its pool share. Its firing rates change. The PA|Coloured case
should fire more often, since the PA widens (§8.2).

**`src/width_budget.py`.** The Dirichlet arm measures nothing after the change,
and its global `np.random.default_rng` wrapper must be deleted (2-review-1c
finding 4). New arms: "shared factor off" (`ρ_s` = 0, own term restored to the
full width), "own term off", "turnout composition off" (existing), "calibration
correction off" (`κ = o(σ)`). The noise-floor paragraph is rewritten once the
ablations are paired.

**Trace keys.** New stage `35_widths` per party: centre, class, σ(s), δ,
composition variance, own sd, loading, κ, calibration error. `41_guards`:
`kappa_error`, `mean_error`, `width`, `width_floored`, capacity-firing counts by
party (existing `ipf_clipped`). `_index.json` and `test_stage_realisation`
change with them.

---

## 7. Judgement calls for the owner

| call | value | evidence | how to check it |
|---|---|---|---|
| width curve form | logistic in log size, 4 parameters | smooth, monotone, no line; borrows strength across the thin 5-20% region; band estimates agree where data exist (§2.3) | the writer prints band estimates beside the curve each cycle; a band more than 2 cluster-bootstrap se off the curve is a report |
| weighting | 1 / (metros the party stood in, that cycle) | one party-cycle is one event for its own term; observation weights narrow small parties (0.87 against 0.99 at 0.5%) | both printed |
| residual reference block | parties with centre ≥ 20% in the city-year | the large block's internal residual is 0.05 while it moves against the rest (§1.1). Alternative: the two largest parties (identical in 22 of 24 city-years; Buffalo City 2011 and Mangaung 2011 differ) | writer prints the widths under both |
| mean offset | `o(σ)` of the drawn family (t7 own, normal shared) | 1b addendum 2 (simulation: the about-zero estimator is biased up by about 0.15) | both estimators printed |
| own-term family | Student-t, 7 df | own-term excess kurtosis 1.92 (90% interval 1.06-2.52) | the writer re-measures kurtosis each cycle |
| shared-factor family | normal | three cycles | — |
| one stream for cycle and metro | sum of the two shares | identical loadings within a run | — |
| newness increments | national debutant 0.05 below 0.3%, 0.58 at 3% and above, linear in log size between; seed 0.76 with arrival factor 0.73 | §5 | regenerated by the writer; MK's width rests on five precedents |
| debutant interpolation band | 0.3% to 3% | below 1% 32 party-elections show no increment; at 1% and over 5 show 0.58; a step at 1% would be a new line | the trace lists debutants inside the band |
| composition subtraction | own variance less the run's composition variance, floored at 0 | MACHINERY §1.50 conditional-share rule; composition is as large as the large parties' own term (§2.5) | `41_guards.width_floored` |
| 2011 width | 1b v3 fallback (0.27 / 0.48), labelled untestable, excluded from falsifiers | no earlier backtest. Alternatives for the owner: (i) the 2016 target's widths, which are fitted on 2011 itself, leak declared; (ii) record movement 2000→2006, a different frame and data that `levels.HELD_BACK` withholds from the model | the 2011 rows carry the label in every report |
| `N_CAL`, `KAPPA_TOL` | 4,000; 1e-3 relative | numerical; distribution-neutral in law, they change only the precision of the mean | registered as numerical constants (1c's `GAMMA_SLOTS` precedent) |
| minimum data for a curve | 20 established party-elections | 2016 has 24 | writer refuses below it |
| no pool-concentration covariate | — | 1f §2.3: real effect, coefficient −0.24 (se 0.06) | deferred, §10 |
| no extra width for a second local election | — | the only precedent at ≥ 5% is EFF 2021 (residuals −0.24 to +0.07). ASA and the PA at JHB 2026 are second-election parties | flagged; the writer lists second-election parties in the trace |

---

## 8. Large parties, predicted directions, and what will still fail

### 8.1 Must-not-worsen (to be pre-registered; numbers are the test's form, the pre-registration fixes thresholds)

Populations are the testable years only (2016, 2021). 2011 is reported and
excluded. Comparisons use paired runs on 1c streams, with a paired bootstrap
over draws (2-review-1c finding 7).

1. **Large parties** (established, centre ≥ 15%; 32 party-city-years):
   - mean CRPS of list share (points), new minus incumbent: the paired 95%
     upper bound must not exceed +0.05;
   - at least 28 of 32 realised shares inside the central 90% band.
2. **Middle parties** (centre 5-15%, any class; about 16 party-city-years):
   the same CRPS rule, reported per class. This is the extrapolated region
   (§2.3), so it is a must-not-worsen row and not only a prediction.
3. **Seats.** Summed coherent seat error (`seat_abs_err_coherent`) over the 16
   testable city-years must not rise by more than the paired Monte Carlo
   interval R2 measures (1c).
4. **Plausibility (1h).** No new failure in the 10-30% or 30%-and-over rows.

Predicted by the citywide simulation (measured on the simulation, not the
model):

| | 2016 new / incumbent | 2021 new / incumbent |
|---|---|---|
| large: mean CRPS (points) | 1.070 / 1.418 | 2.257 / 2.180 |
| large: inside 90% band | 16 / 16 of 16 | 15 / 16 of 16 |
| large: inside 50% band | 13 / 16 | 6 / 12 |
| established 5-20%: mean CRPS | — | 1.189 / 1.490 (n 7) |
| national debutants 5-20%: mean CRPS | 2.037 / 1.438 (n 5, EFF 2016) | — |

The large-party CRPS worsens in 2021: the narrower bands miss the 2021
Johannesburg DA (residual −0.27) and Tshwane EFF (−0.30) by more. Over both
years it improves (1.66 against 1.80 points). The 2016 national-debutant row
worsens. That width comes from 2011 alone, which is COPE's collapse, and EFF
then landed above its centre. Both are predicted failures of rule 2 in a
single year, stated now.

### 8.2 Predicted direction by size (Johannesburg 2026, citywide simulation, 5,000 draws; figures from one seed, counts the mean of four)

| party (class) | centre | log-sd new / arm E | p5-p95 new | p5-p95 arm E |
|---|---|---|---|---|
| DA (established) | 26.00% | 0.18 / 0.21 | 18.5-33.4% | 17.4-34.6% |
| ANC | 23.76% | 0.17 / 0.34 | 17.2-30.0% | 12.1-37.1% |
| ASA | 11.67% | 0.21 / 0.50 | 8.1-15.9% | 4.2-21.8% |
| EFF | 10.96% | 0.23 / 0.57 | 7.2-15.5% | 3.4-21.3% |
| MK (national debutant) | 9.09% | 0.61 / 0.60 | 2.7-20.0% | 2.6-18.1% |
| PA | 5.82% | 0.56 / 0.30 | 2.0-12.4% | 3.3-8.4% |
| RISE (national debutant) | 1.82% | 0.96 / 1.40 | 0.23-5.5% | 0.08-6.2% |
| IFP | 1.50% | 0.85 / 2.42 | 0.25-4.3% | 0.00-6.0% |
| ATM | 0.43% | 0.88 / 3.65 | 0.07-1.21% | 0.00-2.58% |

| quantity | new (mean of 4 seeds) | arm E |
|---|---|---|
| draws in which an established party with a previous share under 1% exceeds 5% (19 parties) | 35 (seed sd 3.5) | 403 |
| the same, above the record's largest such result (3.48%) | 129 | 807 |
| rate above 2% per party-draw, same parties | 0.0068 | 0.0219 (record 0.010; 1h) |
| share of those party-draws keeping under 14.6% of the previous share (the record's lowest) | 0.063 | 0.740 |
| median retained share of previous, same parties | 0.65 | 0.003 |
| log-sd of their combined share | 0.55 | 0.75 (record class-mass sd 0.59, 1h §4.4) |
| draws with any party of centre under 1% above 5% | 90 | 853 |
| draws whose largest new party exceeds 18.12% (the record's largest new party) | 372 | 255 |
| mean combined list share of parties with centre under 1% | 8.22% | 8.65% |

Directions to pre-register:

- **Small (under 1%):**
  - widths rise from a spike to about 0.86-0.89 in log;
  - the typical draw moves from near zero to about 0.65 of the centre;
  - extreme draws fall by about an order of magnitude;
  - mean shares fall 3-11% in log against arm E, because the centre is
    conserved and arm E's floor and renormalisation lifted them (2-recheck-1b-v2
    N2). At JHB 2026 that moves 0.43 points to larger parties.
- **Middle (1-20%):**
  - established parties below 5% and every national debutant narrow sharply;
  - ASA and EFF narrow by more than half;
  - the PA widens (0.30 to 0.56), because arm E's PA sat in one concentrated
    pool cell;
  - MK is about unchanged in width, with a longer upper tail;
  - the largest-new-party feature exceeds the record more often (372 against
    255 draws of 5,000).
- **Large:** narrower. The ANC halves (0.34 to 0.17); the DA 0.21 to 0.18.
- **Seats (list-only largest-remainder proxy on the council size, citywide
  simulation, summed over the eight city-years of a cycle):**
  - wrong-party seats on mean seats: 71.8 → 72.2 (2016) and 154.9 → 153.0
    (2021), about unchanged;
  - expected seats of parties with centre under 1%: 75.6 → 71.2 against a
    realised 63 (2016), and 94.5 → 87.7 against 127 (2021);
  - in 2021 the shape change moves small parties' seats away from the result,
    because their centres were low that year.

### 8.3 What the plausibility check will still fail (declared now)

| failure | predicted | cause |
|---|---|---|
| established sub-1% parties keeping under 14.6% of previous share | panel 0.22 (2016), 0.12 (2021) of party-draws, against 0.005 exchangeable (arm E 0.44, 0.59) | two level-layer facts. (1) Centres sit at 0.82 (2016) and 0.73 (2021) of the previous share (median, measured). (2) For these parties the residual about the centre (σ about 0.99) is wider than plain persistence: the record's next/previous log spread is about 0.82 (1h §2.1). The centres predict small parties worse than their previous result does. A width cannot fix that; it goes to the level layer as a report |
| 2021 sub-1% results above the 90% band | 14 of 82 (arm E 14) | centres low in 2021 (cycle mean +0.41 to +1.01 below 0.3%); level |
| below-0.1% band mean residual +0.75 | no root in the band estimator | tiny centres far below results; level |
| seed centres high | mean residual −1.07 (2016), −0.24 (2021) | seed sizing; next round |
| 2011 coverage | about 0.30 | the fallback width (§2.6) |
| 2011 under the plausibility check | the eight 2011 city-years move from failing the "too wide" tail to failing the "too narrow" tail (`P(X ≥ obs)`) on most features | the fallback width. The pre-registration scores plausibility on the 16 testable city-years and reports 2011 separately, labelled untestable |
| largest new party above the record | 372 of 5,000 JHB 2026 draws | MK's debutant width on five precedents (§5) |

---

## 9. Breakages and the writer's order

One writer; nobody runs the model, `compare_history` or a sweep while it lands
(CLAUDE.md §3). 1c (paired streams) lands first.

1. **1c paired streams**, with 2-review-1c's fixes. Its `split` stage is built
   and then left unread by step 4. Doing 1c first keeps the own term's keys
   (`level.z`, `level.chi`) stable across this change.
2. **`src/width_record.py`** (new):
   - estimator §2.2-2.5, artefact key §2.7, `--out` and scenario override;
   - unit tests on constructed residuals: four-part rule, offset estimator
     against a simulated mean-preserving draw, cluster weights, the no-root
     path, refusal below the minimum;
   - `ENTRY_POINTS`, CLAUDE.md §5.
3. **`src/montecarlo.py`**:
   - `party_width` replaces `level_shock_sd`;
   - `make_drawer`: the latent draw §1.1, calibration pass §1.2, seeds §5,
     `split = moved`, mean floor removed, `dirichlet_scale` and
     `dirichlet_floor` deleted, trace `35_widths`, guards §6;
   - the poll blend reads `party_width`;
   - `run_model` passes the record.
4. **Tests that move:**
   - `test_pool_conservation`: expectation of the target against `pool_spec`
     centres via the calibration pass, not Dirichlet means;
   - `test_drawer` goldens: re-recorded deliberately, reason in MODEL-LOG;
   - `test_spine:570-605`;
   - `test_ipf_feasibility`, `test_regressions:207` (1c ports);
   - `test_stage_realisation` (`GUARD_KEYS`, denominators for
     `width_floored`, capacity counts);
   - `test_citywide_table` (drop `dirichlet_scale` cases);
   - `test_levers_are_live` (drop the two deleted levers; add `N_CAL`,
     `KAPPA_TOL` as numerical);
   - `test_reweight` and `test_draw_record` (signature, and the shelf life of
     check 2);
   - `test_group_share_tripwire` (values);
   - `test_register_matches_code` (new constants, deleted ones);
   - `test_standalone_modules` (new entry);
   - 1c's V3.1 population test: the spec-implied key set drops every
     `pool|member` `split` key and gains `level.shared`, `level.arrival` and
     the `calib.*` keys;
   - new: a run-level test that `alpha` is unread (NaN patch, identical
     output).
5. **`src/width_budget.py`**: new arms (§6), global wrapper deleted.
6. **Records, same commit as the code (CLAUDE.md §2):**
   - MACHINERY "Where the forecast's width comes from" and the conditional-
     share rule, rewritten;
   - JUDGEMENT-CALLS: §B7, §F31, §A30, §F1, §A50 retired; §7's rows added;
     `SD_FLOOR` row amended;
   - `level_shock_sd` docstrings;
   - `POOLS-REEMIT-QUEUE.md` entry for deleting `dirichlet_alpha`.
7. **Re-emit window:** `width_record.py --emit` (default, and
   `level_shrink = 0` if the 1e paired arm runs), `group_share_record.py`
   if its key covers centres.
8. **Pre-registration** under `prereg/`, from §8, before any run.
9. **Canonical paired run** (24 city-years plus JHB 2026), the plausibility
   instrument (1h) on its arrays, scoring.
10. **Interactive and Worker copies** re-synced, draws re-exported, re-freeze:
    step 9 of the round, unchanged by this design.

---

## 10. Rejected alternatives

| alternative | evidence that rejected it |
|---|---|
| keep the Dirichlet above a size line (1b v3 at 1%, or 5%) | 1i §4.1 and 1b's own table: VF+, IFP, RISE and BOSA above 5% in about a fifth of JHB 2026 draws; the owner withdrew the line |
| per-party logit draw, then renormalise | the renormalisation re-couples parties in a way the logit's widths do not describe; the multinomial logit does the same job with one normalisation and no reference (argued); 1b's per-cell logit needed a guard that fired in 1.35e-4 of draws |
| additive log-ratio with a reference party | reference-dependent unless the covariance is full (Selb & Chen 2023 fn. 1; 1i §4.3) |
| widths in size bands only | the 5-20% band has 5 party-elections; a band edge is a line; the curve agrees with the bands where they exist (§2.3) |
| spread measured about zero (`RMS of cycle means`) | biased up by about 0.15 in simulation (1b addendum 2); counts the draw's own offset as cycle movement |
| observation weights | one party in eight metros is one own-term event; weights by party-cycle change the sub-1% width by 0.12 (§2.3) |
| a separate size loading for the shared factor (1 below 5%, 0 above 20%) | components summed to 1.06 for 1-5% parties against a measured band width of 0.83 (measured, `u8`/`widths.py`) |
| one width for all new parties | two populations: seeds 0.76, national debutants under 1% 0.05 (§5); the pooled 0.28 misdescribes both |
| new-party width as its own band estimate at 1% and over (no curve) | 1.40 in own sd (observation-weighted) from three parties dominated by COPE's eight-metro collapse; JHB 2026 MK p95 35%, p99 62% in the citywide simulation |
| simulated method of moments over the full drawer to match each band's residual spread | it fits the model's predicted spread to the realised spread, which is the realised-over-predicted ratio CLAUDE.md §4 bars; the closed-form estimator with composition subtracted stays on the estimation side |
| Gaussian own term (1b's choice) | own-term excess kurtosis 1.92, interval excludes 0; 1b chose Gaussian because `exp` of a t has no mean, which bounded shares and the calibration pass remove |
| t tails on the shared factors | three cycles cannot resolve them; the literature puts heavy tails there only if the record supports it (1i §4.3) |
| pool concentration as a width covariate now | real (coefficient −0.24, se 0.06, 1f §2.3) but it brings pool structure back into the width the change removes; deferred until the universal draw is measured |
| delete `pools.dirichlet_alpha` in this change | changes `pools.py` code, invalidating every spec (CLAUDE.md §3); batched instead |
| analytic κ per party (`−σ²/2`) without a calibration pass | ignores the capacity water-fill, the IPF and the normaliser's correlation with the shared factor; conservation of the group split as the centre would not hold |
| a zero-mass component for withdrawal | 16 of 607 roster parties got no votes, all at centres ≤ 0.17%; a roster fact, not a draw |

---

## What I re-derived and what I did not

**Re-derived in this session (scripts in `uni/`):**

- residuals by class and size band (`u1`);
- the large block's internal residual and the block's movement (`u2`);
- turnout-composition variance per party (`u4`);
- arm E's drawn widths by band and at JHB 2026 (`u5`);
- band totals, the curve and its forward fits, the shared fractions and the
  newness increments (`widths.py`, `curve.py`, `model3.py`, `u8`, `u10`);
- own-term kurtosis with a cluster bootstrap;
- the JHB 2026 citywide simulation over four seeds (`final.py`);
- panel coverage and CRPS against arm E (`u11`);
- the list-seat proxy (`u12`);
- the centre-over-previous ratios of §8.3.

**Taken from earlier documents without re-deriving:**

- 1f's record-movement table and pool-concentration regression;
- 1h's plausibility baselines and record envelopes;
- 1b v3's 2011 fallback and its 0.30 coverage;
- 2-recheck-1b-v2's mean-share shift against arm E;
- 1c's runtime figures;
- the literature (1i).

**Not done:**

- no run of the model with the change, so the capacity water-fill, the IPF,
  the ward path and the calibration pass are argued, not measured;
- the citywide simulation uses the composition factor on unshocked pool
  proportions and solves κ on its own sample;
- seat effects are a list-only proxy, not `allocate_with_overhang`;
- whether any centre computation reads `_theta_sd` was not traced beyond the
  drawer and the poll blend.
