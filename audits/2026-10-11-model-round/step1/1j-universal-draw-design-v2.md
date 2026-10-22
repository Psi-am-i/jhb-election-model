# 1j v2. One log-scale draw for every party: design, revised

Second version of `1j-universal-draw-design.md` (v1, kept unedited). It answers
the blind review `step2/2-review-1j.md` (ded5d5d) and the coordinator's
instructions of 2026-10-12. It also adds the owner's requirement of the same
day (PLAN.md): one consistent way to enter a judgement about a party's
strength. Read-only: nothing in `src/`, `tests/` or `data/` written; no model
run, no `compare_history`, no emit; no sub-delegation. Code at `ded5d5d`.

Where v1 still holds it is cited by section; everything stated here replaces
v1.

**Sources.** As v1: per-party rows and `pool_spec` centres of arm E's 24
backtest city-years and Johannesburg 2026 (`v2rows.json`, `levellift/ps.pkl`
`ps_after`, `review1b/cells.pkl`), and arm E's `arrays.npz`. New scripts are in
the session scratchpad, `uni2/` (`v2.py`, `a1`-`a5.py`); v1's are in `uni/`.
None is committed.

**Labels.** *Measured* = computed in this session from those files. *Argued* =
reasoning or code reading. *Citywide simulation* = my reimplementation of the
v2 draw. It covers the latent draw (normal own term, as specified), the shared
and arrival factors, normalisation, arm E's own pool-turnout draws for the
composition effect, and κ solved on an independent 4,000-draw calibration
sample, then applied to the run. It has no capacity water-fill, no IPF and no
ward path.

**Residual frame.** Unchanged from v1:
`r = log(realised/pool_spec centre) − log(block realised/block centre)`,
where the block is the parties with centre ≥ 20%. Weights are 1/(cases in the
party-cycle). Windows: the 2011, 2016 and 2021 backtests.

---

## Summary for the owner

The decision stands, and the revised draw does what it was meant to do. Each
party gets one draw on the log scale. Its width comes from how far real results
landed from the model's own centres in earlier elections, now estimated one way
throughout. The within-group split keeps only its role as the centre. Six
things changed after the independent review:

1. The party-specific part of the draw now has ordinary bell-shaped tails, not
   heavy ones. The heavy-tailed version had no well-defined centre to estimate
   against, and it doubled the number of extreme small-party draws.
2. The shared swing now applies only to parties under about 2%. The record
   shows no common movement among parties of 1-20%.
3. Widths below 5% come directly from each size band. The smooth curve
   overstated them.
4. National debutants do get a wider draw. v1's "like established parties" was
   a solver error.
5. The test for "the centre is kept" now allows for ordinary simulation noise.
   The old test fired in 7 of 20 clean runs.
6. Comparisons with the current model are now judged by resampling elections,
   not draws.

At Johannesburg 2026 (citywide simulation, 5,000 draws, four seeds), draws in
which a party that had under 1% last time exceeds 5% fall from 403 to 24. Small
parties' typical draw sits at about 0.62 of their centre instead of near zero.
The ANC's and DA's spreads narrow to about a third and a half of today's. On
the 2016 and 2021 backtests the large parties' accuracy improves over the two
years together (prediction score 0.15 points better, interval −0.31 to +0.02)
but covers 29 of 32 results instead of 32. Two weak points remain:

- **The middle of the ballot (5-20%).** Only five party-elections inform it, and
  it holds 38% of Johannesburg's 2026 vote. ActionSA and the EFF come out at
  half today's spread. A pre-registered variant using the middle band's own
  measured width puts them back at today's spread and shows what that costs.
- **The 2016 backtest.** The national-debutant width there comes from 2011
  alone, which is COPE's collapse. It makes the EFF's 2016 draws too wide, so
  the middle-party comparison is predicted to fail its must-not-worsen rule
  that year.

For parties the record cannot size (no record at all, or a collapse like
COPE's), there is now one rule. A declared judgement gives a centre and a
judged width. The judged centre replaces the model's. The width becomes the
record's width for a party of the judged size, combined with the judged width.
Backtests never carry judgements; a forecast reports its result with and
without them.

---

## 0. Every review finding: what changed

| # | finding | verdict | change |
|---|---|---|---|
| 1 | §8 used a normal own term, not the t7 specified | **accepted** | the own term is now normal (finding 2), and every §8 figure is recomputed under it (§8) |
| 2 | `o(σ)` does not exist for a t; half the kurtosis was the curve's misfit | **accepted** | normal own term, `o(σ) = −σ²/2` exact. Tail re-measured (§1.4); a t variant is a paired arm with its location set by calibration, never by a moment of `exp(t)` |
| 3 | conservation falsifier fires on noise | **accepted** | per-party z against the run's own standard error, Bonferroni over parties (§1.2). Measured: 0 false alarms in 20 clean seed pairs (fixed 5% rule: 7 of 20) |
| 4 | shared factor loads 1-20% parties without support | **accepted** | loading by size group with a complementary own term: `ρ(s)` 0.46 below 1%, 0.00 for 1-20% (2026), interpolated (§3) |
| 5 | curve misstates widths below 5%; cross-check used another estimator | **accepted** | one estimator throughout, the offset-aware quadratic root, per band below 5%. The 5-20% stretch is bridged in log size to the large anchor. The curve is withdrawn (§2) |
| 6 | debutant increments unstable; the 2016 value a solver failure | **accepted** | closed-form root, minimum 8 party-elections, one pooled debutant increment, intervals printed (§5). v1's 0.05 below 1% was also an artefact of the iteration: the closed form gives 0.39 |
| 7 | must-not-worsen intervals measured draw noise | **accepted** | bootstrap over party-city-years clustered by city-year; Monte Carlo error reported separately; coverage added to the middle row (§8.1) |
| 8 | seed width formula ambiguous | **accepted** | `ω_i² = σ(s_i)² + δ_seed² − σ_arr² − v_comp,i`, floored at 0 (§1.1, §5) |
| 9 | calibrated offset differs from the estimator's assumed offset | **accepted** | estimator and calibration iterate to a fixed point, with the model-internal location in the estimator (§2.3). Measured shift median +0.045, range −0.07 to +0.20; converges in two iterations |
| 10 | PA capacity prose wrong | **accepted** | the PA belongs to all four pools, so the water-fill cannot bind for it. The PA case is named among the group-share tripwire reports and among those the deferred concentration covariate would change (§1.3) |
| 11 | missed consumers | **accepted** | added to §6 and §9 |
| 12 | middle extrapolated twice | **accepted** | pre-registered middle-width arm using the band's own root, 0.62 (§8.4) |
| N1 | composition floors the DA's own term; covariance | **accepted** | `width_floored` carries the excess variance; the marginal-not-covariance limit is declared (§2.5) |
| N2 | shared-fraction estimand | **accepted** | one-way city-year decomposition about zero (the estimand for a one-city run) |
| N3 | trend read as a random factor | **accepted as a declaration** | cycle means of standardised residuals are monotone (−0.73 / +0.27 / +0.88); a drift in centre bias is a level-layer matter and is filed there (§8.3) |
| N4 | zero results dropped | **rejected** | rejected-claims table, end of §10 |
| N5 | single-member blocks | **accepted** | Buffalo City 2011 and Mangaung 2011 have one block member; the large anchor skips them (46 → 44 cases for 2026), so no identically-zero residual enters |
| N6 | large parties narrow in 2021, widen in 2016 under t7 | **superseded** | under the normal own term they narrow in both years (§8.2) |
| N7 | estimation, not tuning | noted | the fixed point of finding 9 reads no outcome |
| N8 | 2011 labelling on public pages | **accepted** | added to §9 |

### Why the coordinator's 1-5% width is 1.01 and mine and the reviewer's are 0.83

Measured on the same 35 cases (established, centre 1-5%, offset-aware
quadratic root):

| frame | weight unit | width | weighted mean residual |
|---|---|---|---|
| relative to block | party-cycle | 0.834 | −0.42 |
| raw `log(act/ps_after)` | party-cycle | 0.802 | −0.41 |
| relative to block | party (all cycles one unit) | 0.951 | −0.67 |
| raw | party | 0.925 | −0.66 |

The coordinator's mean of −0.65 matches clustering by **party** across cycles.
That gives ACDP's six 2011 cases and two 2021 cases one unit of weight between
them, where clustering by party-cycle gives them two. Under party clustering I
get 0.925 (raw frame) or 0.951 (relative frame). I could not locate the
remaining 0.06-0.09 to 1.01. Possibly the band was assigned on another centre
vector or a degrees-of-freedom factor differs; the coordinator's script would
settle it.

The design keeps party-cycle weights. The own term is drawn independently in
each election, so one party-cycle is one draw. Party clustering instead treats
a party's errors as persistent across cycles, which describes a centre bias,
not a width. Party clustering is printed as a sensitivity and declared (§7).

---

## 1. The draw

### 1.1 Formula

Per draw *d* and party *i*, with `c_i` the unshocked `pool_spec` centre:

    established, national debutant:
        x_id = σ_i·√ρ(s_i)·z_d  +  ω_i·ε_id
        ω_i² = σ_i²·(1 − ρ(s_i)) + δ_class² − v_comp,i        (δ = 0 established, δ_deb debutant)
    seeded arrival:
        x_id = σ_arr·a_d  +  ω_i·ε_id
        ω_i² = σ_i² + δ_seed² − σ_arr² − v_comp,i
    every ω_i² floored at 0, the excess recorded (§2.5)

    shocked_id = c_i·exp(κ_i + x_id) / Σ_j c_j·exp(κ_j + x_jd)

- `σ_i = σ(c_i)` is the width of §2 at the party's centre (or at a judged
  centre, §11).
- `z_d`, `a_d`, `ε_id` are independent standard normals.
- **The base vector is the `pool_spec` centre.** Today `base_c` is built from
  `centres`, the level vector (`montecarlo.py:3277`). v2 builds it from the
  `pool_spec` centre the draw conserves, so the starting κ is close to
  `−σ²/2` (review finding 11).
- **The individual path joins the same vector.** A party with a centre and no
  pool vector (reached by none today) enters the softmax with the same
  components. It no longer goes through `target[i] = centre * log_shock(...)`
  (`:3383`).
- v1 §1.1 otherwise stands: multinomial logit, reference-free; capacity
  water-fill, IPF, turnout weighting and `split = moved` after it; no mean
  floor. The ward link `ward_target = pr_target * ratio` (`:5770`) is
  unchanged.

### 1.2 Exact expectation and a noise-aware falsifier

The calibration pass is as v1 §1.2: `N_CAL` = 4,000 draws through the real
`draw_pools` path on `calib.*` streams, with recording off and counters reset.

**Falsifier.** For each party with centre ≥ 0.1%:

    z_i = (mean_d target_id / c_i − 1) / SE_i
    SE_i² = var_d(target_id/c_i)/D  +  var_cal(target_id/c_i)/N_CAL

The test fails when any `|z_i|` exceeds the Bonferroni threshold for a family
error of 0.01 over the m parties: 3.49 at m = 21 (Johannesburg 2026).

Measured (citywide simulation, Johannesburg 2026, 20 independent pairs of a
calibration sample and a 5,000-draw run):

- **noise:** median SE 0.020, largest 0.030;
- **false alarms:** fixed 5% rule 7 of 20; this rule 0 of 20;
- **power:** a mean error injected by multiplying one party's correction was
  detected as follows:

| injected mean error | party at 1.50% | party at 0.16% |
|---|---|---|
| ×1.1 | 9 of 10 | 7 of 10 |
| ×1.2 | 10 of 10 | 10 of 10 |

The run records `z_i`, `SE_i` and the threshold in `41_guards.mean_error`.

### 1.3 Capacity

The water-fill stays as v1 §1.3, counted in `ipf_clipped`. **Correction to
v1:** the PA at Johannesburg 2026 is a member of all four pools (0.802 of the
Coloured pool, 0.001 of each other pool; `cells.pkl`, measured). Its capacity
is the whole city and the water-fill cannot bind for it. What sees a large PA
draw is the group-share tripwire. Its PA|Black African and PA|White pairs are
named as pre-registered reports, since a 9% PA needs 2.2% of the non-Coloured
vote. The PA's widening (0.30 → 0.48, §8.2) comes from the size width at 5.8%.
The deferred pool-concentration covariate (1f §2.3) would narrow it; the PA is
named in §10 as a case it changes.

### 1.4 Tails: normal own term

| standardisation of own deviations (established, about their city-year mean) | n | excess kurtosis | 90% cluster bootstrap |
|---|---|---|---|
| v1 curve | 237 | 1.92 | 1.06-2.52 |
| each band's own sd (reviewer, `r13.py`) | 237 | 0.87 | 0.17-1.19 |
| v2 widths, all below 20% | 237 | 2.56 | 1.05-3.83 |
| v2 widths, below 5% | 225 | 1.62 | — |
| v2 widths, below 1% | 187 | 1.42 | — |

The measured tail depends on the width model used to standardise it. Under v2
widths the excess above 5% comes from five 2011 collapses and two Buffalo City
and Mangaung DA results set against the bridged middle width (standardised
residuals −2.23, −2.12, +3.27, +1.35; measured). That is the middle-width
question of §8.4, not a tail.

**Decision: a normal own term.** `o(σ) = −σ²/2` is exact, the estimator's
location exists, and the calibration starts at the right place. Below 1% the
record shows moderate excess kurtosis (0.9-1.4 depending on standardisation).
A Student-t own term with df from that kurtosis (about 8-11, `df = 4 + 6/κ`)
is pre-registered as a paired arm. Its estimator location is the calibrated
κ, never a moment of `exp(t)`. The plausibility check's joint feature and its
threshold-event rates decide between them.

### 1.5-1.7

Zeros (§1.5), streams (§1.6) and the class seam (§1.7) are as v1, with one
difference: there is no `level.chi` stream, because the own term is normal.
The stages are `level.z` (party), `level.shared` (`""`), `level.arrival`
(`""`) and `calib.*`. A t arm adds `level.chi` per party (1c's slot gamma).

---

## 2. The width function

### 2.1 One estimator throughout

For a set of residuals with weights `w`, the total width is the smaller root
of

    σ² = E_w[(r' + σ²/2)²],   r' = r − Δ_i

`Δ_i` is the model-internal location shift of §2.3 (0 in the first pass). This
is the offset-aware moment equation of 1b addendum 2. When it has no root, the
width is the weighted sd about the weighted mean, and the mean bias is filed
as a level report, never folded into the width.

- **Below 5%: per band.** Bands 1-5%, 0.3-1%, 0.1-0.3% and < 0.1%, each with at
  least `MIN_EFF` = 8 party-elections. A thinner band takes no value of its
  own.
- **Interpolation.** Each band's width sits at its geometric centre (2.24%,
  0.55%, 0.17%; 0.05% for the bottom band). The large anchor is the
  within-block residual and applies at 20% and above. Between anchors the
  width is linear in log size; beyond the ends it is constant. No step at any
  band edge.
- **5-20%.** It has 5 party-elections, below `MIN_EFF`, so it takes the
  log-linear bridge between the 1-5% anchor and the large anchor. Its own root
  (0.62) is the middle-width arm (§8.4).
- **The curve of v1 is withdrawn.** It was a tied-normal likelihood, a
  different estimator, and the < 0.1% band's level bias raised its floor
  (review finding 5).

### 2.2 Fitted widths, forward (measured, after the fixed point)

| target | 1-5% | 0.3-1% | 0.1-0.3% | < 0.1% | large anchor | 5-20% own root (arm only) |
|---|---|---|---|---|---|---|
| 2016 (from 2011) | thin (5 party-elections) | 0.956 (31 / 15) | 0.960 (10 / 8) | thin (2) | 0.058 (12) | 0.670 (5 / 4) |
| 2021 (2011-2016) | 0.823 (21 / 11) | 0.859 (64 / 25) | 0.810 (31 / 22) | 0.96, no root, mean +0.29 (14 / 13) | 0.046 (28) | 0.674 (5 / 4) |
| 2026 (2011-2021) | 0.840 (35 / 18) | 0.821 (88 / 35) | 0.901 (61 / 37) | 0.998, no root, mean +0.71 (41 / 34) | 0.053 (44) | 0.623 (12 / 5) |

Cells read width (cases / party-elections).

Width at a given centre, 2026 record:

| centre | 25% | 11.7% | 11.0% | 9% | 5.8% | 3% | 1.5% | 0.5% | 0.2% | 0.05% |
|---|---|---|---|---|---|---|---|---|---|---|
| σ | 0.053 | 0.247 | 0.269 | 0.340 | 0.498 | 0.734 | 0.834 | 0.828 | 0.891 | 0.998 |

For 2016 the 1-5% band is thin, so the bridge runs from the 0.3-1% anchor to
the large anchor: 0.71 at 1.5%, 0.37 at 5.8%, 0.19 at 11.7%.

### 2.3 The fixed point with the calibrated location (finding 9)

The draw's mean log residual relative to the block is not exactly `−σ²/2`.
The normaliser correlates with the shared factor, and the block carries its
own κ. The writer therefore iterates:

1. widths;
2. at each earlier city-year, the draw's own `E[log(s_i/c_i) − log(S_B/C_B)]`
   from the drawer with those widths. This is model-internal and reads no
   outcome;
3. `Δ_i` = that location plus `σ_i²/2`;
4. re-estimate the widths on `r − Δ`.

Measured with the citywide simulation (2,000 draws per city-year): `Δ` has a
median of +0.045 (range −0.068 to +0.195) for the 2026 record. The widths moved
by at most 0.025 in the first iteration and 0.002 in the second; two
iterations are specified, with a stop at a change below 0.01. `35_widths`
prints `Δ_i` per party.

### 2.4 Sensitivities the writer prints

- party-clustered weights (1-5%: 0.95, §0);
- observation weights;
- the block as "the two largest parties";
- each band with its cluster-bootstrap interval;
- the 5-20% own root.

A band root outside its bootstrap interval of the interpolated value stops the
writer; it is not merely reported (review finding 5).

### 2.5 Turnout composition (as v1 §2.5, with the excess carried)

`v_comp,i` is subtracted from each party's own variance. Where it exceeds the
budget, the own term is 0 and `41_guards.width_floored` records the excess
variance, not just a flag. Johannesburg 2026: DA excess 0.0026 in log
variance, because its composition log-sd 0.074 exceeds its whole width 0.053.
Subtracting per party keeps each party's marginal width. It does not
reproduce the covariance between parties of one pool that composition
induces; declared, argued.

### 2.6 Fallbacks and the record (as v1 §2.6-2.7)

- 2011 is untestable and uses 1b v3's fallback.
- Below `MIN_EFF` a band is interpolated.
- A target with no record stops the run.
- The writer is `src/width_record.py`, keyed as v1 §2.7, plus `MIN_EFF`, the
  band edges and anchors, and the iteration count.

---

## 3. Shared structure

### 3.1 Loading by size group (finding 4)

One-way city-year decomposition of standardised residuals
`u = (r' + σ²/2)/σ`, about zero (the estimand for a one-city run; review N2):

| target | shared share, < 1% (n) | shared share, 1-20% (n) | all below 20% |
|---|---|---|---|
| 2016 | 0.39 (43) | 0.00 (17) | 0.42 |
| 2021 | 0.37 (109) | 0.00 (26) | 0.34 |
| 2026 | 0.46 (190) | 0.00 (47) | 0.40 |

`ρ(s)` is `ρ_<1%` at 0.55% and below and `ρ_1-20%` at 2.24%, linear in log size
between; it falls to 0 at 20%. With `ρ_1-20%` at 0.00, the shared swing reaches
parties up to about 2%. At Johannesburg 2026: 0.46 below 0.55%, 0.13 at 1.5%, 0
from 2.24%.

The own term is complementary (`ω² = σ²(1−ρ) + …`), so each party's total stays
`σ_i` and the band totals reproduce the record by construction. v1's overshoot
(1.06 against 0.83) came from a loading without that complement.

Normalisation still makes the large block move against a small-party swing,
as v1 §3.1 argued. A shift common to every party remains inert.

### 3.2 Separation (as v1 §3.2, values above)

Seeded arrivals keep their own factor: between-city-year sd 0.726 (16
city-years, 2016 and 2021), carved out of the seed total (§1.1).

---

## 4. The citywide re-fit

As v1 §4: `party_width` replaces `level_shock_sd` as the draw's only width, for
pooled parties, the individual path and the poll blend (`:5641`). The θ size
line keeps feeding `theta_prior`'s own outputs.

**Correction (review finding 11):** `theta_residual.nll_t` and its
`kappa_star` describe "the predictive `log_shock` draws". After the change
those are not the draw's widths, so its docstring is corrected in the same
commit to say it scores the θ layer's own predictive law, which no longer
reaches the draw.

---

## 5. New parties

| class | treatment | 2026 value | evidence (measured, 2011-2021, closed-form root, party-cycle bootstrap of 2,000) |
|---|---|---|---|
| national debutant | established structure; own term widened by one pooled δ_deb | **0.47** | pooled 0.472 (87 cases, 35 party-elections), 90% interval 0.00-0.90, 27% of resamples at zero. Split for information: below 1% 0.385 (68 / 32, 0.00-0.88); 1% and over 0.692 (19 / 5, 0.00-1.07; below `MIN_EFF`, not used) |
| seeded arrival | arrival factor plus own term (§1.1) | δ_seed **0.84**, σ_arr **0.73** | 221 cases, 133 party-elections, 0.57-1.13 |

- **Solver.** The increment solves
  `Σ w[(r' + (σ² + δ²)/2)² − σ² − δ²] = 0`, which is a quadratic in `δ²`. The
  writer takes its smallest root that is ≥ 0. With no excess, δ is 0; with no
  real root, it records "no root", a level report, and the pooled value is not
  used. Forward values (pooled debutants, after the fixed point):
  - 2016: 0.787. That is 24 cases from 10 party-elections, and COPE 2011 is
    eight of them; the exact smaller root for COPE alone is 1.21.
  - 2021: 0.832.
  - 2026: 0.472.
- **Seeds for 2016.** There is no earlier seed record, so seeds take the
  debutant increment (declared).
- **Why pooled.** The ≥ 1% split has 5 party-elections. A split at 1% would
  also be a new line, and the two halves' intervals overlap almost entirely.
- **Bias reported, not corrected** (next round's centre sizing):
  - seed mean residual −1.16 (2016) and −0.59 (2026 pooled), after the shift;
  - debutant mean residual −0.22.
- **Collapses and parties with no record** that the record cannot size go
  through the judgement entry of §11, not through a special case.

---

## 6. What is removed, and every consumer

v1 §6 stands. Added or corrected (review finding 11):

| consumer | what it needs |
|---|---|
| `tests/test_roster_universe.py:130` (`run.guards["level_sd_at_size"]`) | reads `41_guards.width` |
| `tests/test_stage_estimation.py:1182-1186`, `2178-2196` (`test_the_width_ceiling_tripwire_exempts_only_what_the_drawer_records`) | rewritten against `41_guards.width`; the `sd_ceiling` tripwire no longer applies to the draw and is retired with a MODEL-LOG note |
| `interactive/tools/make_fixtures.py:249-250` (`dirichlet_scale` grid) | grid removed; fixture schema version bumped |
| `src/backtest.py:560` | `dirichlet_floor` sits in `NOT_FITTED` (v1 said `FITTED_ON_UNINSTRUMENTED`); deleted there |
| `src/backtest.py:570` | the `arrival_group_draw` text cites `dirichlet_scale`; reworded |
| `site/your-forecast/py/montecarlo.py` (+ `manifest.json` `code_ref`) | synced mirror; re-sync with the other copies |
| individual path `montecarlo.py:3383` | joins the latent vector (§1.1) |
| `base_c` at `:3277` | the `pool_spec` centre vector (§1.1) |
| `theta_residual.nll_t`, `kappa_star` docstrings | corrected (§4) |
| docstring mentions: `levels.py:937`, `src/fold.py:112` and its two mirrors, `tests/test_theta_prior.py:796`, `tests/test_solve_and_predict.py:374`, `pools.py:4179`, `compare_history.py:3944` | updated with the records |
| `LEVEL_DF` | no longer read by the draw (normal own term); kept for the t arm and `theta_residual`; register row amended |

---

## 7. Judgement calls for the owner

| call | value | evidence | how to check |
|---|---|---|---|
| width estimator | offset-aware quadratic root, per band below 5%, log-linear bridge 2.24% → 20% | §2; one estimator for widths, cross-checks and increments | writer stops on a band outside its interval |
| band edges and anchors | 1%, 0.3%, 0.1%; geometric centres; bottom band at 0.05% | interpolation removes steps | sensitivities printed |
| `MIN_EFF` | 8 party-elections | 5-20% has 5; 1-5% for 2016 has 5 | — |
| weight unit | party-cycle | §0 | party clustering printed (1-5%: 0.95) |
| block | centre ≥ 20% | v1 §1.1; single-member blocks skipped | two-largest variant printed |
| own-term family | normal | §1.4 | t arm pre-registered |
| shared loading | `ρ(s)`: group values 0.46 / 0.00 (2026), linear in log size between 0.55% and 2.24%, 0 at 20% | §3.1 | 1-20% shared share pre-registered as a measured quantity |
| debutant increment | one pooled value, 0.47 for 2026 | §5; interval 0.00-0.90 | split printed |
| seed increment, arrival factor | 0.84, 0.73 | §5 | — |
| location fixed point | two iterations, stop below 0.01 | §2.3 | `Δ` printed |
| falsifier | Bonferroni, family error 0.01 | §1.2 | false-alarm and power checks in the suite (§9) |
| middle width | bridge; band root as an arm | §8.4 | arm result |
| judgement entry | §11 | owner requirement | register guard |
| 2011 width, composition subtraction, `N_CAL`, minimum data, no concentration covariate, no second-election increment | as v1 §7 | | |

---

## 8. Predictions, must-not-worsen, and what will still fail

All figures come from the citywide simulation with the normal own term as
specified, the fixed-point widths, `ρ(s)`, pooled increments, and κ from an
independent calibration sample.

### 8.1 Must-not-worsen (form for the pre-registration)

Populations: 2016 and 2021. Intervals are a bootstrap over party-city-years
clustered by city-year (2,000 resamples). The Monte Carlo error of each
difference is reported beside it and is not part of the interval.

1. **Large parties** (centre ≥ 15%, 32 party-city-years):
   - the 90% upper bound of the mean CRPS difference (new minus incumbent) is
     at most +0.05 points;
   - at least 28 of 32 results fall inside the 90% band.
2. **Middle parties** (centre 5-15%, all classes, 14): the same two rules,
   with at least 12 of 14 inside the band.
3. **Seats:** as v1 §8.1.
4. **Plausibility:** as v1 §8.1.

Predicted:

| population | n | CRPS new / incumbent | difference [90% interval] | Monte Carlo sd of the difference | inside 90% band new / incumbent | rule |
|---|---|---|---|---|---|---|
| large, 2016 | 16 | 1.032 / 1.418 | −0.386 [−0.445, −0.330] | 0.017 | 16 / 16 | — |
| large, 2021 | 16 | 2.260 / 2.180 | +0.080 [−0.192, +0.352] | 0.029 | 13 / 16 | — |
| **large, both years** | 32 | | **−0.153 [−0.309, +0.019]** | | **29 / 32** | passes both, coverage by one |
| middle, established, 2021 | 7 | 1.122 / 1.490 | −0.368 [−0.665, −0.057] | 0.027 | 6 / 7 | — |
| middle, national debutants, 2016 (EFF) | 5 | 2.271 / 1.438 | +0.833 [+0.650, +0.967] | 0.040 | 5 / 5 | — |
| **middle, both years** | 14 | | **+0.129 [−0.165, +0.422]** | | **13 / 14** | **predicted to fail the CRPS rule** |

The middle failure comes from the 2016 debutant width (0.79, mostly COPE 2011)
applied to the EFF, which then landed above its centre. It is stated now as a
prediction and attributed: one cycle of debutant record.

### 8.2 Johannesburg 2026

| party (class) | centre | total σ | shared sd | own sd | drawn log-sd new / arm E | p5-p95 new | p5-p95 arm E |
|---|---|---|---|---|---|---|---|
| DA | 26.00% | 0.05 | 0 | 0 (floored) | 0.12 / 0.21 | 20.9-31.1% | 17.4-34.6% |
| ANC | 23.76% | 0.05 | 0 | 0.02 | 0.11 / 0.34 | 19.5-28.0% | 12.1-37.1% |
| ASA | 11.67% | 0.25 | 0 | 0.25 | 0.23 / 0.50 | 7.7-16.6% | 4.2-21.8% |
| EFF | 10.96% | 0.27 | 0 | 0.27 | 0.26 / 0.57 | 6.9-16.2% | 3.4-21.3% |
| MK (debutant) | 9.09% | 0.58 | 0 | 0.58 | 0.53 / 0.60 | 3.3-18.7% | 2.6-18.1% |
| PA | 5.82% | 0.50 | 0 | 0.47 | 0.48 / 0.30 | 2.4-11.8% | 3.3-8.4% |
| RISE (debutant) | 1.82% | 0.96 | 0.22 | 0.94 | 0.93 / 1.40 | 0.24-5.2% | 0.08-6.2% |
| IFP | 1.50% | 0.83 | 0.30 | 0.78 | 0.79 / 2.42 | 0.28-3.9% | 0.00-6.0% |
| ALJAMAAH | 0.88% | 0.83 | 0.46 | 0.63 | 0.80 / 0.65 | 0.17-2.4% | 0.25-2.0% |
| ATM | 0.43% | 0.84 | 0.57 | 0.62 | 0.80 / 3.65 | 0.08-1.17% | 0.00-2.58% |

| quantity (5,000 draws) | new, mean of 4 seeds (sd) | arm E | record |
|---|---|---|---|
| draws with an established party, previous share < 1%, above 5% (19 parties) | 24 (1.9) | 403 | — |
| the same above 3.48% (record's largest such result) | 94 (4.4) | 807 | — |
| rate above 2% per party-draw | 0.0057 | 0.0219 | 0.010 (1h) |
| party-draws keeping < 14.6% of previous share | 0.075 | 0.740 | 0.005 exchangeable |
| median retained share of previous | 0.62 | 0.003 | 0.78 (1h) |
| log-sd of their combined share | 0.58 | 0.75 | class-mass sd 0.59 (1h §4.4) |
| draws with any party of centre < 1% above 5% | 60 (8.3) | 853 | — |
| draws whose largest new party exceeds 18.12% | 292 (17) | 255 | — |
| mean combined share, centre < 1% | 8.13% | 8.65% | — |

Directions to pre-register:

- **Small parties:** widths about 0.8 in log in place of a spike. The typical
  draw is about 0.62 of the centre, and extreme draws fall by more than an
  order of magnitude. Mean shares fall 3-11% in log against arm E (conserved
  centre), which moves 0.52 points at Johannesburg 2026.
- **Middle parties:**
  - ActionSA and the EFF narrow by more than half;
  - the PA widens;
  - MK keeps about its width;
  - national debutants under 2% narrow sharply;
  - the largest-new-party feature exceeds the record somewhat more often.
- **Large parties:** narrower in both backtest years. Drawn log-sd median, new
  / arm E / realised RMS:
  - 2016: 0.092 / 0.144 / 0.040;
  - 2021: 0.084 / 0.182 / 0.114.

  So 2021 is now under-covered (13 of 16).
- **Seats** (list-only largest-remainder proxy, summed over each cycle's eight
  city-years):
  - wrong-party seats on mean seats: 71.8 → 72.5 (2016), 154.9 → 153.1 (2021);
  - expected seats of parties with centre < 1%: 75.6 → 72.4 against a
    realised 63 (2016), and 94.5 → 88.5 against 127 (2021).

### 8.3 What will still fail (as v1 §8.3, with v2 values)

| failure | predicted | cause |
|---|---|---|
| established sub-1% parties keeping < 14.6% of previous share | 0.075 of party-draws at JHB 2026; on the panel the rate stays far above 0.005 | centres at 0.82 / 0.73 of previous share (2016 / 2021, median); a residual width (0.82-0.90) wider than persistence (0.82); level |
| sub-1% established results outside the 90% band, 2021 | 82 cases, 0.82 inside (arm E 0.82); v1 counted 14 above the band | centres low in 2021; level |
| < 0.1% band: no root, mean residual +0.71 | — | level |
| cycle means of `u` monotone (−0.73 / +0.27 / +0.88) | — | a drift in centre bias, read by a zero-mean factor as noise; level (review N3) |
| seed centres high | mean −1.16 (2016) | sizing, next round |
| 2011 | untestable; flips to "too narrow" in the plausibility check | fallback width; scored on the 16 testable city-years |
| large parties under-covered in 2021 | 13 of 16 inside 90% | block movement in 2021 (mean −0.063, a level miss shared by all metros) |
| middle CRPS rule | fails, +0.129 upper +0.422 | 2016 debutant width (§8.1) |

### 8.4 The middle-width arm (finding 12)

Pre-registered, paired against the main draw. The 5-20% stretch takes the
band's own root (0.623 for 2026, 0.674 for 2021, 0.670 for 2016) as an anchor
at 6.3%, between the 1-5% anchor and the large anchor.

| quantity | main | middle arm | arm E |
|---|---|---|---|
| JHB 2026 log-sd ASA / EFF / MK / PA | 0.23 / 0.26 / 0.53 / 0.48 | 0.45 / 0.51 / 0.71 / 0.68 | 0.50 / 0.57 / 0.60 / 0.30 |
| JHB 2026 log-sd DA / ANC | 0.12 / 0.11 | 0.16 / 0.15 | 0.21 / 0.34 |
| JHB 2026 draws, largest new party > 18.12% | 292 | 478 | 255 |
| panel, large CRPS difference, both years | −0.153 [−0.309, +0.019] | −0.139 [−0.273, +0.008] | — |
| panel, middle CRPS difference, both years | +0.129 [−0.165, +0.422] | +0.395 [+0.145, +0.705] | — |
| panel, middle inside 90% | 13 / 14 | 14 / 14 | 13 / 14 |
| wrong-party seats on mean seats, 2016 / 2021 | 72.5 / 153.1 | 72.7 / 153.3 | 71.8 / 154.9 |

Seats are reported under both. On the backtests the arm scores worse in the
middle and gains one result in coverage.

---

## 9. Breakages and the writer's order

v1 §9 stands, with these changes:

- **Step 2** (`width_record.py`):
  - band roots, interpolation, the fixed point of §2.3, the closed-form
    increment solver, `ρ(s)`;
  - unit tests:
    - the quadratic solvers against constructed residuals (root, no-root,
      no-excess paths);
    - the fixed point converging on a constructed panel;
    - the stop rule of §2.4 firing on a constructed band outside its interval
      and quiet when reverted.
- **Step 3** (`montecarlo.py`): normal own term; the base vector is the
  `pool_spec` centre; the individual path joins the latent vector; the
  falsifier statistics go into `41_guards.mean_error`; `width_floored`
  carries the excess.
- **Step 4** adds:
  - `test_roster_universe`, `test_stage_estimation`, `make_fixtures`;
  - a falsifier test: 20 seed pairs, false alarms at most 1, and an injected
    ×1.2 error detected;
  - a judgement-entry test (§11): register ↔ judgements file, both
    directions.
- **Step 6** adds: the `theta_residual` docstring correction; JUDGEMENT-CALLS
  §J (§11); the `LEVEL_DF` row amended.
- **Step 8** pre-registers the main draw, the middle-width arm and the t arm.
- **Step 10** adds: the `site/your-forecast/py` mirror re-synced; any public
  page that shows 2011 backtest bands labels them untestable (review N8).

---

## 10. Rejected alternatives (v1 §10 stands; changes)

| alternative | evidence that rejected it |
|---|---|
| the v1 logistic curve below 5% | tied-normal likelihood, a different estimator from the band roots; the < 0.1% band's level bias (+0.71) raised its floor to 0.99 against band roots of 0.82-0.90 |
| Student-t own term with `o(σ) = −log E[e^x]` | the integral diverges (review, `r15.py`) |
| t7 by default | tail evidence depends on standardisation (excess kurtosis 0.87 to 2.56, §1.4); kept as an arm |
| shared loading proportional to σ for all sizes | 1-20% shared share 0.00 in 2021 and 2026 (§3.1) |
| separate debutant increments at 1% | 5 party-elections above 1%; intervals 0.00-0.88 and 0.00-1.07 overlap |
| fixed 5% conservation threshold | 7 of 20 false alarms with no defect |
| bootstrap over draws for must-not-worsen | measures Monte Carlo error, not the sample of elections |
| party clustering as the weight unit | it describes persistent centre bias, not the per-election own term; printed |
| the deferred concentration covariate now | as v1; it would narrow the PA (0.802 of the Coloured pool) |

**Rejected review claim:**

| claim | evidence that rejects it |
|---|---|
| N4: treat the 16 zero results as censored at half a vote | on the log scale, half a vote is `log(0.5 / expected votes)`. For a 0.05% party in a city of about a million valid votes that is about −6.9. One such case among the 41 in the < 0.1% band would add about 1.2 to the band's mean square, so the width would depend on the city's vote count, an arbitrary constant, and on how many such parties stand. All 16 had centres of 0.17% or less, and none could win a seat. They stay a reported count (`35_widths.zero_results`), with the rate (16 of 607) pre-registered as a plausibility quantity |

---

## 11. Entering a judgement about strength (owner requirement, 2026-10-12)

### 11.1 The rule

A **strength judgement** is a declared pair for one party at one target: a
judged centre and a judged width.

- **Centre.** Either `centre_share` (a list share) or `centre_ratio` (a
  multiplier on the model's own centre). Exactly one.
- **Width.** `sigma_j`, a log sd stating how uncertain the judgement itself
  is. Required; there is no default.

It applies the same way to any party, whatever its class:

1. **The judged centre replaces the model's.** It enters the level vector
   before `pool_spec`. The IPF places it in the party's pools, and every other
   party is rescaled by the normalisation, so mass leaves or arrives in
   proportion. That changes the other parties' centres, declared, and visible
   in `30_centres`.
2. **The width combines in variance:**

       σ_total² = σ(c_J)² + σ_J²

   - `σ(c_J)` is the record's width for a party of the judged size (§2). It
     says how far parties of that size move even when the centre is right. A
     judged collapse to 2% therefore inherits the width of a 2% party, not
     that of the size it fell from.
   - `σ_J` replaces the record's class increment (δ_deb or δ_seed). Those
     increments measure the error of the model's own centre rule for that
     class. Once the centre is judged, its error is what the judgement states.
3. **Shared structure follows the judged size.** The shared loading is
   `ρ(c_J)` and the own term takes the rest less composition. A seeded arrival
   keeps the arrival factor.
4. **The calibration pass conserves the judged centre.** The mean drawn share
   equals `c_J`, and the falsifier of §1.2 applies to it.

### 11.2 Where it is declared, and the guards

- **The entry.** A table `[strength.<PARTY>]` in the target's existing
  `judgements/<city>-<year>` file, with `centre_share` or `centre_ratio`,
  `sigma_j`, `reason`, `source` and `register`.
- **The register.** Each entry has a row in a new JUDGEMENT-CALLS section
  "§J · strength judgements" giving the value, the reason, the evidence the
  record cannot supply, and how to check it after the election.
- **Guards.**
  - `make_drawer` refuses an entry with no register row.
  - A test checks both directions: every register row has an entry, and every
    entry has a row.
  - No code path names a party.
- **Backtests carry none.** A judgement made after the election cannot be
  blind, so backtest targets refuse any `strength` table. The width record
  never sees one.
- **A forecast reports both.** Every forecast with judgements is also run
  without them, paired, and both results are recorded. A judgement is never
  set or revised from backtest scores. It would have none, and that is
  tuning.

### 11.3 Three entries, worked (hypothetical parties; 2026 widths)

Quantiles are of a mean-preserving lognormal on the total width. They describe
the party's own draw before normalisation and composition.

| case | entry | size width σ(c) | replaced increment | total | p5 / median / p95 |
|---|---|---|---|---|---|
| seeded arrival, no judgement (model centre 0.10%) | — | 0.94 | δ_seed 0.84 applies | 1.26 | 0.01 / 0.05 / 0.36% |
| seeded arrival, judged | `centre_share = 0.015`, `sigma_j = 0.8` | 0.83 | δ_seed replaced by 0.8 | 1.16 | 0.11 / 0.77 / 5.15% |
| national debutant, no judgement (centre 9%) | — | 0.34 | δ_deb 0.47 applies | 0.58 | 2.92 / 7.60 / 19.78% |
| national debutant, judged: centre kept, uncertainty stated | `centre_ratio = 1.0`, `sigma_j = 0.6` | 0.34 | δ_deb replaced by 0.6 | 0.69 | 2.28 / 7.10 / 22.06% |
| established, no judgement (centre 6%) | — | 0.49 | none | 0.49 | 2.40 / 5.33 / 11.85% |
| established, judged to be collapsing | `centre_ratio = 0.33` (to 1.98%), `sigma_j = 0.5` | 0.84 | none to replace; σ_J added | 0.98 | 0.25 / 1.23 / 6.12% |

The values are illustrations of the arithmetic, not proposals for any party.
Entries are the owner's to make.

---

## What I re-derived and what I did not

**Re-derived in this session (`uni2/`):**

- band roots, frames and weight units, including the coordinator's 1.01
  question;
- the fixed point of §2.3 at all three targets;
- the shared shares by size group;
- the increments by the closed-form root, with party-cycle bootstraps;
- tail kurtosis under v2 widths;
- the falsifier's false-alarm rate and power;
- the Johannesburg 2026 citywide simulation, main and middle arm, four seeds;
- panel CRPS and coverage with city-year bootstraps and Monte Carlo error;
- the list-seat proxy;
- the judgement-entry arithmetic.

**Taken from the review without re-deriving:** the divergence of `E[exp(t)]`
(`r15.py`); the PA's pool membership was checked against `cells.pkl`.

**Not done:**

- no model run: the capacity water-fill, the IPF, the ward path and the real
  calibration pass are argued;
- the location fixed point used the citywide simulation, not the drawer;
- seats are a list-only proxy;
- the t arm was specified and not simulated;
- whether any centre computation reads `_theta_sd` remains untraced, as in
  v1.
