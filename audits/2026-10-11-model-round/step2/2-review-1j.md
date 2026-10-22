# 2. Review of 1j (one log-scale draw for every party)

Independent review of `step1/1j-universal-draw-design.md` at `2cff20d`
(`remediation`). Read-only on code: no model run, no `compare_history`, no emit,
nothing under `data/` written, no sub-delegation. My scripts are in the session
scratchpad, `review1j/` (`base.py`, `r1`–`r15.py`, `sim.py`). They read the same
row files as the designer (`v2rows.json`, `levellift/ps.pkl` `ps_after`,
`review1b/cells.pkl`) and arm E's `arrays.npz`. None of the designer's `uni/`
code is imported.

**Labels.** *Measured* = computed by my scripts from those files. *Argued* =
reasoning or code reading. *Citywide simulation* = my own reimplementation of
the proposed draw at citywide level (latent draw, normalisation, arm E pool
turnout for the composition effect, κ solved on the run's own sample; no
capacity water-fill, IPF or ward path). Residual frame, block (centre ≥ 20%)
and cluster weights as the design defines them. Windows: backtests 2011, 2016,
2021 (8 metros each).

## Verdict

**Implement with listed fixes.** Do not write the §8 pre-registration until §8
is regenerated under the own-term family §1.4 finally specifies. Three findings
block (1-3); they are cheap to fix. The core decisions (one log-scale draw,
widths estimated from realised residuals about the conserved centre, the split
kept as centre only, seeds and debutants treated apart) survive re-derivation.
The width function and the shared loading need the changes in 4-6 before the
canonical run, because they move the middle of the ballot.

---

## Findings

### 1. §8 predictions were computed with a normal own term, not the t7 the design specifies. **Blocking (for step 8, pre-registration).**

Evidence (code reading): the designer's simulator draws the own term as
`zi=g.standard_normal((D,P))` (`uni/model2.py`, `simulate`); `final.py`,
`u11.py` and `u12.py` inherit it. §1.4 specifies Student-t, 7 df.

Measured (citywide simulation, Johannesburg 2026, 5,000 draws, mean of seeds
7-10, same widths, ρ_s = 0.44):

| quantity | design §8.2 (normal) | mine, normal | mine, t7 as specified | arm E | record, 24 backtest city-years |
|---|---|---|---|---|---|
| draws with an established party, previous share < 1%, above 5% | 35 | 42.5 | **86.5** | 403 | largest such result 3.48% |
| draws with any party of centre < 1% above 5% | 90 | 94.5 | **240** | 853 | 0 of 24 city-years have one |
| RISE p99 list share | — | 9.9% | 10.8% | — | — |
| IFP p99 | — | 7.4% | 8.8% | — | — |
| large parties, drawn log-sd, 2016 backtests (16 party-city-years, median) | — | 0.129 | **0.164** | 0.144 | realised RMS 0.040 |

Under the specified family about half of the claimed reduction in small-party
explosions goes, and in 2016 the large parties come out wider than arm E, not
narrower as the summary states.

Fix: regenerate every §8 figure, and the summary's headline counts, under the
family §1.4 ends up choosing (see finding 2), before anything is pre-registered.

### 2. `o(σ)` does not exist for a Student-t own term; and half the kurtosis that motivated t7 is the curve's misfit. **Blocking (the estimator as specified cannot be implemented).**

The design says the estimator's location is `o(σ) = −log E[e^x]` "by
quadrature" for the t own term (§1.4, §2.2), and that the estimator and draw then
agree on location. The moment generating function of any Student-t diverges, so
this integral is infinite. Measured (`r15.py`, trapezoid on a truncated range,
σ = 1, t7 scaled to unit variance): `−log E[e^x]` = −0.62 at |t| ≤ 10, −1.30 at
≤ 20, −11.6 at ≤ 40, −39.7 at ≤ 80, −102 at ≤ 160. It has no limit. The "−0.08
from the fourth cumulant" is a term of a series that does not converge. The
designer's own fits used `−σ²/2` throughout (`uni/curve.py`, `nll`).

The evidence for t7 is also weaker than stated. Measured (`r13.py`, own
deviations of 237 established sub-20% residuals about their city-year mean):

| standardisation | excess kurtosis | 90% cluster bootstrap (city-years) | share beyond 2.5 sd | beyond 3 sd |
|---|---|---|---|---|
| by the 2026 curve σ(s) (design's method) | 1.92 | design: 1.06-2.52 | 0.042 | 0.013 |
| by each size band's own sd | 0.87 | 0.17-1.19 | 0.038 | 0.008 |
| t7, unit variance (theory/simulation) | 2.00 | — | 0.021 | 0.009 |
| normal | 0 | — | 0.012 | 0.003 |

Own-deviation sd by band (measured, same rows): 0.59 (5-20%, n 12), 0.63
(1-5%, 35), 0.47 (0.3-1%, 88), 0.73 (0.1-0.3%, 61), 0.87 (< 0.1%, 41). The curve
gives these one flat value, and standardising a mixture of widths by one width
manufactures kurtosis. With band widths allowed, the kurtosis interval excludes
t7's 2.0; the 2.5-sd exceedance (9 of 237) is still above both t7 and normal, so
the tail is not resolved by these data in either direction.

Fix: choose one of (a) a normal own term, where `o(σ) = −σ²/2` is exact and the
estimator is consistent; or (b) a t with df from the band-standardised kurtosis
(about 11 at 0.87, declared as a judgement call) and the estimator's location
defined as the median offset or the calibrated κ of finding 9, never as a
moment of `exp(t)`. Either way, re-measure the tail after finding 5's width
change and state it in JUDGEMENT-CALLS.

### 3. The mean-conservation falsifier fires on Monte Carlo noise. **Blocking (for the test and the pre-registration).**

§1.2 sets the falsifier at "a mean drawn share more than 5% relative from its
`pool_spec` centre for any party with centre ≥ 0.1%", described as about three
Monte Carlo standard errors. Measured (`r12.py`, Johannesburg 2026, t7 own term,
κ solved on an independent 4,000-draw calibration sample, then applied to a
5,000-draw run):

- 21 parties have centre ≥ 0.1%;
- the standard error of the relative mean error (run plus calibration) is 0.027
  at the median party and 0.072 at the worst (UDM, 0.16%);
- the falsifier is breached in **7 of 10** independent seed pairs, with no
  defect in the code.

Fix: a per-party threshold of 3 × the run's own measured standard error
(computed from the run's draws and the calibration sample), with a
multiplicity correction across parties; or restrict the falsifier to centres
≥ 1% and raise `N_CAL` for the rest. State it in the pre-registration in that
form.

### 4. The shared factor loads the 1-20% parties with no support in the record. **Should-fix.**

§3.1 argues correctly that a uniform loading cancels under normalisation
(argued; the algebra is one line). It does not follow that the loading must be
proportional to σ(s). Measured (`r5.py`, one-way random effects by city-year on
standardised residuals `u` of established sub-20% parties, about zero):

| target | between-city-year share, < 1% parties | between-city-year share, 1-20% parties | corr of city-year means, < 1% vs 1-20% |
|---|---|---|---|
| 2021 | 0.31 (n 109) | 0.00 (n 26) | 0.54 (13 city-years) |
| 2026 | 0.47 (n 190) | 0.00 (n 47) | 0.48 (21 city-years) |

The 1-20% band shows no common city-year component beyond sampling noise, yet
the design gives ASA a shared sd of 0.19 of a 0.28 total at Johannesburg 2026.
§3.3 and §10 reject a size-dependent loading because band totals then
overshoot (1.06 against 0.83 for 1-5%). That overshoot belonged to a
construction that did not shrink the own term to compensate. With a
complementary form, `x = σ(s)(√ρ(s)·z + √(1−ρ(s))·ε)`, the total stays σ(s) by
construction. Measured (`r11.py`, ρ fading from 0.44 at 1% to 0 at 5%,
complementary own term, t7): no overshoot. ASA's log-sd goes 0.23 → 0.30, EFF
0.25 → 0.33, the DA 0.21 → 0.18, and the block sum's log-sd 0.191 → 0.167.

Fix: estimate ρ by size band (complementary own term), declare the loading
function as a judgement call, print both versions, and pre-register the 1-20%
shared share as a measured quantity.

### 5. The width curve's flat lower asymptote is set by the < 0.1% band's level bias; the "same estimator" cross-check uses a different estimator. **Should-fix.**

Reproduced exactly (`r1.py`): 2026 curve a 0.029, b 0.991, m 7.82%, k 2.58
(n 283, 95 party-elections); 2021 and 2016 match to the optimiser's bounds.

The design says band estimates "agree" with the curve. They do not below 5%.
Measured (`r2.py`, `r3.py`, 2011-2021):

| band | moment root (design's band estimator) | curve σ there | standardised E[u²] under the 2026 curve | cluster-weighted mean r |
|---|---|---|---|---|
| 1-5% | 0.834 | 0.94 | 0.77 | −0.42 |
| 0.3-1% | 0.817 | 0.99 | 0.64 | −0.54 |
| 0.1-0.3% | 0.910 | 0.99 | 0.89 | −0.13 |
| < 0.1% | no root | 0.99 | 2.57 | +0.75 |

A 0.99 width where the band measures 0.82 is 1.46 times the variance, applied to
most of Johannesburg's small parties, and it lowers their drawn median from
0.71 to 0.61 of centre. Two causes:

- **Different estimators.** The curve is tied-normal maximum likelihood,
  `r ~ N(−σ²/2, σ²)`. The bands use the moment equation's smaller root. They
  coincide only when the mean really is −σ²/2. Here the mean is not −σ²/2, and
  ML gives about 0.88 where the moment root gives 0.82 at 0.3-1% (argued, worked
  by hand on the band's mean and sd).
- **The asymptote.** The < 0.1% band (mean residual +0.75, which §8.3 calls a
  level defect) pulls `b` up. The logistic form cannot rise again below 0.3%, so
  the excess spreads to 0.3-5%. Excluding < 0.1% gives b 0.93 (measured,
  `r4.py`).

Fix: one estimator for curve and cross-check, named; let the width fall below
1% (a band-wise width under 5% with the curve only bridging 5-20% is the
simplest), or carry a band mean term so a level defect is not read as width;
print the curve against band roots with cluster-bootstrap intervals, as §7
already proposes, and make a miss a stop rather than a report.

### 6. National-debutant increments: unstable, and the 2016 value is a solver failure. **Should-fix.**

Reproduced (`r6.py`, `r7.py`): 2026 debutants < 1% 0.05 (68 cases, 32
party-elections); ≥ 1% 0.58 (19, 5); seeds 0.77 (221, 133; design 217/132);
arrival factor 0.73 (16 city-years).

- **< 1% is not "like established".** By cycle (2026 curve): 2011 0.46, 2016
  0.69, 2021 0.00. The forward 2021 target gives 0.60. Cluster bootstrap over
  party-elections (2,000 resamples): 90% interval 0-0.76, 52% of resamples at
  zero. The 0.05 rests on 2021's 40 of 68 cases, a cycle in which every small
  band rose.
- **≥ 1%**: 0.58, bootstrap 90% interval 0-1.01, 33% at zero.
- **2016.** The designer's fixed-point iteration does not converge on the
  COPE-only class. It oscillates between d² = 2.934 and 0, and returns either
  depending on the iteration count. The exact smaller root is 1.195, an increment of 1.09. `final.py` hardcodes
  `DEB['2016']=(0.0, None)`, while `u11.py` used the pooled all-debutant 0.56.
  §8.1's account of the 2016 debutant row ("width comes from 2011 alone, which
  is COPE's collapse") is therefore not what was simulated.

Fix: the writer solves the quadratic in closed form (smaller root, floored at
0, "no root" reported); a minimum party-election count for increments as for
the curve (§2.6), with a declared fallback; and either one debutant increment
(pooled 0.28) or the < 1% / ≥ 1% split with both intervals printed. The
0.3%-3% interpolation band is a judgement call on 5 and 32 party-elections and
should say so.

### 7. Must-not-worsen comparisons measure draw noise, not the world's sampling. **Should-fix.**

§8.1 compares new against incumbent "using paired runs on 1c streams, with a
paired bootstrap over draws". §1.6 says this change is unpaired by design:
every party changes path. Even where draws are paired, a bootstrap over draws
gives the Monte Carlo error of each CRPS, not the uncertainty from having 32
large-party cases or about 16 middle-party cases. The upper bound "+0.05
points" would then be a point comparison. The tests are stated against real
results, which is correct. Their interval is not.

Fix: bootstrap over party-city-years, clustered by city-year (and by party for
the middle band); report Monte Carlo error separately; fix the thresholds in the
pre-registration before the canonical run. Add 90% coverage to the middle-party
row, since CRPS alone can improve while coverage collapses.

### 8. Seeded-arrival width formula is ambiguous in a way that double-counts. **Should-fix.**

§1.1 writes `x = σ_arr·a + ω·ε` and §5 says the own term is "the established
curve plus increment δ_seed", with the arrival factor listed beside it. δ_seed
was estimated as the excess of seeds' total residual variance (including its
between-city-year part) over σ(s)². Read literally, the text adds the arrival
factor on top. The designer's simulator carves it out instead (`uni/model2.py`
`comps`: `tot2 = t² + d_seed²`, `own² = tot2 − sa² − vcomp`).

Fix: state `ω_i² = σ(s_i)² + δ_seed² − σ_arr² − v_comp,i`, floored at 0, in §1.1
and §5.

### 9. The calibrated offset is not the offset the estimator assumed. **Should-fix.**

§1.2 calibrates κ to conserve the mean through the normaliser; §2.2 fits widths
assuming the drawn residual's location is −σ²/2. They differ, because the
normaliser is correlated with the shared factor. Measured (citywide simulation,
normal own term, κ relative to the block's κ, established parties < 1%):
+0.063 (Johannesburg 2016), +0.051 (Johannesburg 2021), +0.056 (Tshwane 2021),
+0.043 (Cape Town 2021), +0.103 (Johannesburg 2026, where 50% of the centre lies
outside the block). The draws place small parties' median about 5-11% higher,
relative to the block, than the estimator assumed.

Fix: iterate estimator and calibration to a fixed point, with κ as the location
(model-internal, reads no outcome, so still estimation), or report the gap per
city-year in `35_widths`.

### 10. PA capacity prose is wrong; the PA widening is a size-curve artefact. **Should-fix.**

§1.3 says the water-fill will bind more for the PA "against a Coloured-pool
capacity". Measured (`cells.pkl`, Johannesburg 2026): the PA is a member of all
four pools (0.802 of Coloured, 0.001 in each of the other three), so its
capacity is the whole city and the water-fill never binds (P = 0.000 in the
simulation). A PA draw of 9% needs 2.2% of the non-Coloured vote, and in the
proposed draw P(PA > 7%) = 0.27 and P(PA > 9%) = 0.14 (arm E: 0.16 above 7%).
The instrument that sees this is the group-share tripwire, not `ipf_clipped`.
The widening (0.30 → 0.56) comes from the size curve at 5.8%; the pool
concentration 1f measured (coefficient −0.24) is deferred.

Fix: correct §1.3 and §8.2. Name the tripwire's PA|Black African and PA|White
pairs as a pre-registered report. List the PA among the cases the deferred
concentration covariate would change.

### 11. Consumers and breakages §6/§9 miss. **Should-fix.**

Checked by `git grep` at `2cff20d`. The design's line citations are right
(`montecarlo.py` 528, 2830, 2926, 3110, 3152-3158, 3288, 3376, 5641, 5770,
5937-5939; `pools.py` 3510, 4196-4199, 6401). Missed:

- `tests/test_roster_universe.py:130` reads `run.guards["level_sd_at_size"]`;
- `tests/test_stage_estimation.py:1182-1186` and `2178-2196`
  (`test_the_width_ceiling_tripwire_exempts_only_what_the_drawer_records`)
  read `41_guards.level_sd_at_size` against `sd_ceiling`;
- `interactive/tools/make_fixtures.py:249-250` carries a `dirichlet_scale`
  grid in the fixture schema;
- `src/backtest.py:560`: `dirichlet_floor` sits in `NOT_FITTED`, not in
  `FITTED_ON_UNINSTRUMENTED` as §6 says; `backtest.py:570` cites
  `dirichlet_scale` in the `arrival_group_draw` text;
- `site/your-forecast/py/montecarlo.py` (24 hits) is the synced mirror with a
  `code_ref` hash in `manifest.json`. §9 step 10 covers the re-sync but §6 does
  not list it;
- the individual path (`montecarlo.py:3383`, `target[i] = centre *
  log_shock(rng, sd)`) gets no shared term or κ in the design; `party_width`
  alone does not make it the same draw;
- `base_c` at the draw is built from `centres` (the levels' centres), not the
  `pool_spec` centre the design conserves. The calibration absorbs this, but
  §1.1 should name the vector;
- `theta_residual.nll_t` and its `kappa_star` score the θ layer under
  "the predictive `log_shock` draws". After the change those are not the
  draw's widths, so its docstring claim goes stale (§6 says "references stay
  valid");
- docstring-only mentions to update with the records: `levels.py:937`,
  `src/fold.py:112` and its mirror, `tests/test_theta_prior.py:796`,
  `tests/test_solve_and_predict.py:374`, `pools.py:4179`,
  `compare_history.py:3944`.

### 12. The middle of the ballot is extrapolated twice at Johannesburg 2026. **Should-fix (declare and run an arm).**

The design names 5-20% as its weakest point. Measured:

- the band's own moment root is 0.615 (12 cases, 5 party-elections), against a
  curve value of 0.28 at ASA's 11.67% and 0.31 at the EFF's 10.96%;
- under the curve, standardised E[u²] is 1.25 in 10-20% (8 cases) and 1.15 in
  5-10% (4);
- with cluster weights, the whole 5-20% stretch carries 5 units of weight out of
  95;
- the share of the centre outside the ≥ 20% block is 0.50 at Johannesburg 2026,
  against 0.08-0.41 across the 24 backtest city-years (2016 range 0.08-0.16).
  So the ANC's and DA's emergent widths at Johannesburg 2026 come from a region
  the record does not reach.

Fix: pre-register a width-variant arm for the middle (e.g. the band root, or
1f's record-movement 0.45 at 5-15%) and report seats under both. It is paired
against the new draw (§1.6), so it costs a run, not a design.

### Notes

- **N1. Composition floors the DA's own term.** Measured: DA composition log-sd
  0.074, which exceeds both its own-term budget (0.07² × 0.56 = 0.0027 in
  variance) and the record's within-block residual (0.05). Composition is also
  correlated across co-pool parties, so subtracting it from each party's own
  variance preserves marginal widths, not the covariance. `width_floored` should
  carry the excess, not just a flag.
- **N2. Shared fraction method.** My one-way city-year decomposition gives 0.40
  about zero (0.36 about the grand mean) for 2026 and 0.29 for 2021. The design's
  cycle-plus-metro method gives 0.44 and 0.35. This is a method difference, not
  an error. For a one-city run the estimand is the city-year share, which is the
  one-way figure.
- **N3. Trend read as a random factor.** Cycle means of `u`: −0.48 / +0.36 /
  +0.89 (mine) and −0.73 / +0.27 / +0.88 (design). They are monotone. A zero-mean
  shared factor treats a drift in centre bias as noise, which is the level
  layer's problem. The width cannot centre it.
- **N4. Zero results are dropped.** 16 roster parties got no votes and have no
  log residual. They are lower-tail information for seeds and tiny parties.
  Treat them as censored at half a vote rather than excluding them.
- **N5. Single-member block.** Buffalo City 2011 and Mangaung 2011 have only the
  ANC above 20%, so its within-block residual is identically 0. The effect is
  negligible under cluster weights; say so.
- **N6. Large parties, measured.** Realised log(realised/centre), established
  ≥ 15%: RMS 0.118 over 48 (2011-2021), 0.040 in 2016, 0.114 in 2021 (mean
  −0.074, a level miss). This confirms the design's 0.12. "The new draw narrows
  them" holds for 2021 (0.126 against arm E 0.182) and fails for 2016 under t7
  (0.164 against 0.144).
- **N7. Estimation vs tuning.** No outcome-derived ratio, coverage or seat width
  enters any width. The block definition, composition variance and calibration
  read no result. The `level_shrink` selection caveat (2-recheck-1b-v2 N6) is
  declared and carries over. Clean.
- **N8. 2011.** Eight of the 24 backtest city-years are untestable by
  construction, and the design predicts they flip to failing "too narrow". The
  labelling is honest. Any public page that shows 2011 backtest bands should
  carry the same label.

---

## Decisive numbers

| quantity (window, method) | design | mine | note |
|---|---|---|---|
| curve 2026 (a, b, m, k), cluster-weighted tied-normal ML | 0.029, 0.991, 7.82%, 2.58 | 0.029, 0.991, 7.82%, 2.58 | reproduced |
| curve 2021 | 0.023, 0.994, 9.43%, 2.86 | identical | reproduced |
| curve 2016 | 0.005, 1.231, 5.70%, 1.64 | 0.003, 1.234, 5.67%, 1.61 | optimiser bound |
| σ at 0.3-1% (2011-21): curve / band moment root | 0.99 / 0.82 | 0.99 / 0.817 | finding 5 |
| σ at 1-5%: curve / band root | ~0.92-0.98 / 0.83 | 0.94 (mean over rows) / 0.834 | finding 5 |
| σ in 5-20%: band root (5 party-elections) | not computed (below minimum) | 0.615 | finding 12 |
| large parties, realised RMS, ≥ 15%, 48 cases | 0.12 | 0.118 | reproduced |
| within-block residual, ≥ 20% | 0.05 | 0.05 (wsd, 46 cases) | reproduced |
| shared fraction 2026 | 0.44 (cycle 0.38 + metro 0.06) | 0.40 (one-way city-year, about zero) | N2 |
| shared share, 1-20% band only | not measured | 0.00 (2021 and 2026) | finding 4 |
| own-term excess kurtosis | 1.92 (curve-standardised) | 1.92 curve / **0.87** band (90% 0.17-1.19) | finding 2 |
| debutant increment < 1%, 2026 | 0.05 | 0.05; bootstrap 90% 0-0.76; by cycle 0.46/0.69/0.00 | finding 6 |
| debutant increment ≥ 1%, 2026 | 0.58 | 0.58; bootstrap 90% 0-1.01 | finding 6 |
| debutant increment ≥ 1%, 2016 (COPE only) | ran with 0.0 | 1.09 (exact smaller root) | finding 6 |
| seed increment / arrival factor, 2026 | 0.76 / 0.73 | 0.77 / 0.73 | reproduced |
| JHB 2026: draws, established prev < 1% above 5% | 35 | 42.5 normal / **86.5 t7** | finding 1 |
| JHB 2026: draws, any centre < 1% above 5% | 90 | 94.5 normal / **240 t7** | finding 1 |
| JHB 2026 composition log-sd DA / ANC / EFF / PA | 0.074 / 0.049 / 0.047 / 0.150 | identical | reproduced |
| mean-conservation falsifier false-alarm rate | "about 3 SE" | 7 of 10 seed pairs | finding 3 |
| calibrated minus assumed offset, sub-1%, JHB 2026 | 0 (assumed) | +0.10 | finding 9 |

## What I checked and did not

**Checked (measured):** residual frame and block; the curve and its forward fits
under cluster and observation weights, tied and free location; band roots; the
curve's standardised second moment by band; large-party realised spread and
block movement; shared fractions by one-way decomposition, overall and by band;
own-term kurtosis under two standardisations with a cluster bootstrap; debutant
and seed increments by closed form and by the designer's iteration, with
bootstraps and by cycle; the arrival factor; a citywide simulation of all 16
testable backtest city-years and Johannesburg 2026 under normal and t7 own
terms and a faded loading; calibration error against the falsifier; calibrated
offsets; PA pool membership and capacity; the divergence of `E[exp(t)]`.

**Checked (code reading):** every line citation in §1, §6 and §9; the draw path
`make_drawer` → `draw_pools` (shock, water-fill, IPF to fixed `pool_votes`,
turnout reweighting, Dirichlet, individual path, entrant); consumers by
`git grep` across `src/`, `tests/`, `interactive/`, `site/`.

**Argued, not tested:** the §3.1 cancellation algebra (one line, true); the ML
versus moment-root gap at 0.3-1%.

**Not done:** no model run, so the IPF, the water-fill, the ward path and the
calibration pass through the real drawer are untested here, as in the design;
seats (the design's list-only proxy was not re-derived); the 2011 fallback's
0.30 coverage, 1f's record-movement table and 1h's envelopes are taken from
those documents; the literature (1i) was not re-read; whether any centre
computation reads `_theta_sd` was not traced.
