# 1f: how uncertainty is applied across quantities and parties

Read-only audit for the 2026-10-11 model round. Nothing in `src/` or `data/`
written; no model run, no `compare_history`, no emit. Sources: `src/` at
`62dfded`; arm E (`data/arms/step11/E/*/arrays.npz`, `meta.json`, traces), 1,000
draws per backtest city-year and 5,000 at Johannesburg 2026; the pool specs those
runs read; the raw metro LGE files 2000-2021 through
`levels._citywide_and_roster`. Scripts in the session scratchpad
(`randaudit/paths.py`, `record.py`, `record2.py`, `aeff.py`, `bysize.py`,
`classtot.py`, `gaps.py`), not committed.

1c (`1c-paired-draws-design.md`) and its review answer whether draws are
reproducible and paired. This audit asks whether the uncertainty each party
receives is principled and consistent, and judges each difference against the
record: where parties of different kinds move differently in the record, a
different treatment is correct; where the difference comes only from the code
path, it is a defect.

Labels: **measured** = computed here from arm E or the record; **argued** = read
from code, not measured.

**Two reference measurements used throughout.**
- *Record movement*: log(list share at the next metro LGE / list share at the
  previous one), parties that stood at both, eight metros, transitions
  2000→2006 to 2016→2021. This is not the forecast's error (the forecast also
  uses the national result), but it is the real-world behaviour a party of a
  given size and history shows.
- *Realised error*: log(realised list share / the party's centre after
  `compress_levels`, renormalised), arm E, 24 backtest city-years, parties with
  a positive list share.

---

## 1. Every source of uncertainty in a run

In order of application. "All" means every party the run draws.

| # | quantity | applies to | family | width / parameter | source of the parameter | file:function |
|---|---|---|---|---|---|---|
| 1 | citywide turnout factor `z_common` | all pools | standard normal | 1 | none | `montecarlo.make_drawer.draw_pools` |
| 2 | pool turnout | each untied pool; tied pools share one draw | triangular via Gaussian copula, bounded | `(low, mode, high)` per pool; corr `turnout_correlation` 0.63 | band: `pools.turnout_band`, previous turnout ∓ largest observed logit spread (record); 0.63 measured (§B4, §A1 stale n); copula form §B5 | `correlated_triangular`, `_tri_ppf` |
| 2a | tied-pool band | pools sharing a `tie` | as 2 | arithmetic mean of members' `(low, mode, high)`, not weighted by size | argued; no register entry found | `draw_pools` |
| 3 | level shock, pooled parties | every pooled party except seeded arrivals | exp(Student-t, df 7), standardised to log-sd `sd` | `level_shock_sd`: θ size line at national share ("measured"), or at baseline share ("size") | size line fitted in `levels.theta_prior` (record), clamped to `[SD_FLOOR 0.15, SD_CEILING 1.20]` (§F, row `SD_FLOOR`); df §A18 | `log_shock`, `level_shock_sd`, `levels.size_sd` |
| 3a | seeded arrival level shock | seeded arrivals | none (sd 0) | 0 | §A50 | `make_drawer` `pool_sd_shock` |
| 4 | shocked centres normalised, water-filled under pool capacity | pooled parties | deterministic | `POOL_CAPACITY_MARGIN` 0.98; excess spread in proportion to mass held | §A28, §A27 | `capped_targets` |
| 5 | IPF balance of shocked centres into pool proportions | pooled parties | deterministic; `partial_balance` fallback | 200 passes | numerical (`PARTIAL_BALANCE_PASSES`) | `pools.balance_margins`, `partial_balance` |
| 6 | mean floor on pool proportions | pooled parties | deterministic clip | `dirichlet_floor` 1e-4 | §A30 | `draw_pools` (`mean_floor`) |
| 7 | within-pool split | every pool member | Dirichlet(`moved × A_g`) | `A_g` per pool × `dirichlet_scale` 1.0 | `pools.dirichlet_alpha`: method of moments over members ≥ `ALPHA_MIN_SHARE` 1% of the pool, size-weighted, clipped `[1, 200]`, fallback 12 (§B7, §F31) | `draw_pools` |
| 8 | individual-party draw | parties in `index` that are in no pool | centre × exp(t7) | `level_shock_sd` | as 3 | `draw_pools` |
| 9 | arrival-group total and split | named arrivals (switch off) | lognormal; Dirichlet | `total_log_sd`, `alpha` (fallback 4.0), cap 0.45 | `pools.arrival_group_record` (record); fallbacks §A45 | `draw_pools` |
| 10 | generic entrant slot | `ENTRANT` (present only in the 2011 runs) | Bernoulli × triangular, bounded at 12% | `entrant_prob` 0.25, `entrant_share` (0.01, 0.04, 0.12) | §A3, §A17 | `draw_pools`, `triangular` |
| 11 | turnout-pattern blend | all VDs | uniform ± jitter | 0.5 ± 0.25 | §A41 | `run_model` loop |
| 12 | per-VD turnout noise | each VD | lognormal | `turnout_noise_sd` 0.08; clipped to `[0.02, 0.95]` | §A41; clip §F34 | `run_model` loop |
| 13 | VD calibration to the drawn target | all | deterministic | `level_floor` 1e-6, `SHARE_FLOOR` 0.002 on deviations | §F19, §C4 | `solve_and_predict` |
| 14 | ward target | all | deterministic: PR target × party ratio | ratio clipped `[0.5, 2.0]` | §F35 | `run_model` |
| 15 | ward-tally noise | each ward × party | lognormal | `ward_noise_sd` 0.10 | §A38 (typed; standing refusal to widen) | `run_model` loop |
| 16 | seat lot | ties | hash-keyed lot | none | statutory | `seats.lot_order` |

Not drawn, but setting what the draws centre on: `blended_centres`,
`compress_levels` (lift defect, `1b-level-lift-defect.md`), by-election weights.
No uncertainty is drawn on the ward/list ratio (14): both ballots move together
in every draw.

---

## 2. Treatment by party path

### 2.1 The paths (argued from code; counts measured in arm E)

| path | who lands in it | width comes from | tail | parties, 24 backtest runs | parties, JHB 2026 |
|---|---|---|---|---|---|
| pooled, established | any party with a pool vector and no seed: big parties, small established parties, national debutants (MK, RISE, BOSA) | level shock (t7, size line) **plus** within-pool Dirichlet at `A_g × cell share` | t7 on the level; Dirichlet: a spike at zero when `A_g × share < 1` | 373 | 35 |
| pooled, seeded | arrivals with no record, sized by `pools.arrival_rules` | Dirichlet only (level sd 0, §A50) | spike at zero | 234 | 46 |
| individual | a party with a centre and no pool vector | level shock only | t7 | **0** | **0** |
| generic entrant | `ENTRANT` | Bernoulli × triangular | bounded at 12% | 8 (all 2011) | 0 |
| arrival group | named arrivals when the switch is on | lognormal × Dirichlet | lognormal | 0 (off) | 0 (off) |
| merged / splinter | sized in `pools.emit_pools`; drawn as pooled | as pooled | as pooled | in pooled | in pooled |
| planned unit class (1b v3 + 1% addendum) | established and national-debutant parties with previous result and centre below 1%, not seeded | logit-Gaussian: common cycle and metro factors + own term, widths from the record of residuals about the `pool_spec` centre | Gaussian (ν = ∞) | — | 24 |

The individual path exists in code and is reached by no party in any arm E run.
A party that reached it would get only the level shock (0.15-0.6 in log) where a
pooled party of the same size gets a Dirichlet spike. The orphan warning fires
only for a base share ≥ 1% (`make_drawer`), so a smaller orphan would take the
narrow path silently. Latent, inert today.

### 2.2 What each path draws, against the record (measured)

Medians over parties in each cell. "Central half" is the 25th-75th percentile of
the draws divided by the party's centre (for the record: of next / previous).
Record populations: parties that stood again.

| size of centre (record: previous share) | record central half | record P(< 0.1×) | record P(> 3×) | pooled established, panel: central half | P(< 0.1×) | P(> 3×) | seeded, panel: central half | P(< 0.1×) |
|---|---|---|---|---|---|---|---|---|
| ≥ 15% | 0.80-1.07× | 0 | 0 | 0.88-1.10× | 0 | 0 | — | — |
| 5-15% | 0.90-1.28× | 0 | 0 | 0.65-1.30× | 0.002 | 0.001 | (n 2) | — |
| 1-5% | 0.35-1.01× | 0.027 | 0.013 | 0.29-1.35× | 0.071 | 0.052 | (n 2) | — |
| 0.3-1% | 0.41-1.02× | 0 | 0.074 | 0.07-1.23× | 0.292 | 0.091 | 0.11-1.17× | 0.242 |
| 0.1-0.3% | 0.45-1.22× | 0.013 | 0.079 | 0.001-0.54× | 0.599 | 0.089 | 0.007-0.77× | 0.483 |
| < 0.1% | 0.66-2.11× | 0.027 | 0.108 | 0.002-0.03× | 0.800 | 0.066 | 0.001-0.15× | 0.722 |

Johannesburg 2026 is worse than the panel at every size below 5%: pooled
established 1-5% P(< 0.1×) 0.223, 0.3-1% 0.579, 0.1-0.3% 0.679; central half
for 0.3-1% is 0.000-0.65×.

Calibration of the same draws against the realised result (PIT of the result in
the party's own draws; 90% band = p5-p95, 50% band = p25-p75; a well-calibrated
draw puts 0.90 and 0.50 of results inside them):

| path | centre size | n | in 90% band | in 50% band | median PIT | realised rms log error | realised median abs error / 0.674 |
|---|---|---|---|---|---|---|---|
| pooled | ≥ 15% | 50 | 0.96 | 0.70 | 0.49 | 0.30 | 0.10 |
| pooled | 5-15% | 20 | 0.80 | 0.50 | 0.38 | 1.02 | 0.40 |
| pooled | 1-5% | 42 | 0.98 | 0.71 | 0.65 | 0.75 | 0.69 |
| pooled | 0.3-1% | 107 | 0.99 | 0.64 | 0.68 | 0.87 | 0.61 |
| pooled | 0.1-0.3% | 95 | 0.96 | 0.32 | 0.80 | 0.81 | 0.72 |
| pooled | < 0.1% | 56 | 0.79 | 0.02 | 0.91 | 1.14 | 0.96 |
| seeded | 0.3-1% | 14 | 0.93 | 0.57 | 0.41 | 1.84 | 2.17 |
| seeded | 0.1-0.3% | 104 | 0.92 | 0.63 | 0.69 | 1.52 | 1.83 |
| seeded | < 0.1% | 99 | 0.96 | 0.04 | 0.84 | 0.99 | 1.04 |

The four 5-15% results below their own p5 are COPE 2011 in Cape Town,
Johannesburg, Mangaung and Tshwane (log errors −1.45 to −2.19; PIT 0.01-0.04).
They, with COPE Ekurhuleni, IFP eThekwini and VF+ Tshwane 2011, are the 2011
collapses (§A2): a centre problem, not a width problem. Observations within a city-year share a
cycle and are not independent; the coverages are descriptive, not tests.

Reading of the two tables:
- **Above 5%** the drawn distributions sit close to the record and are slightly
  wide (≥ 15%: in 50% band 0.70).
- **Below 5% the shape is not the record's.** The record's central half of
  next/previous stays near 0.4-1.2× at every size down to 0.1%; the draws' central
  half collapses toward zero as size falls, because the Dirichlet concentration
  `A_g × share` falls below 1. The median draw of a 0.1-0.3% party is 0.035× its
  centre (panel) while the realised median is 0.84× it. The 90% band still covers
  because the draws put mass both at zero and in a long upper tail; the 50% band
  holds 2-32% of results below 0.3%.
- **The measured width source is overridden.** The level shock carries the θ
  size line (median 0.15 at ≥ 15%, 0.26 at 1-5%, 0.34 at 0.3-1%, 0.39-0.56 below).
  Below 5% the Dirichlet supplies most of the width (§B7 records 83-98% of drawn
  variance for every party except the ANC and DA).

### 2.3 Same size, same history, different width (measured, JHB 2026 arm E)

| comparison | party | centre | cell concentration `a_eff` (approx.) | median / centre | P(< 0.1× centre) |
|---|---|---|---|---|---|
| 0.7-0.9%, all established | ALJAMAAH | 0.88% | 4.2 | 0.95 | 0.004 |
| | VF+ | 0.88% | 0.50 | 0.53 | 0.203 |
| | ACDP | 0.73% | 0.38 | 0.49 | 0.173 |
| 6-12% | PA | 5.8% | 16.9 | 0.95 | 0.000 |
| | MK | 9.1% | 1.7 | 0.91 | 0.003 |
| | ASA | 11.7% | 2.3 | 0.94 | 0.000 |
| ~24-26% | DA | 26.0% | 13.1 | 0.97 | robust log-sd 0.20 |
| | ANC | 23.7% | 5.8 | 0.99 | robust log-sd 0.34 |
| ~0.075% | ECONOMIC_LIBERATORS (established, level sd 0.53) | 0.074% | 0.01 | 0.000 | 0.797 |
| | 22 seeded arrivals (level sd 0) | 0.071-0.078% | 0.01 | 0.000 | 0.80-0.82 |

`a_eff` = Σ over pools of (party's weight in the pool) × `A_g` × (party's share
of that pool), from the spec and the after-shrink centre; an approximation of
the post-IPF concentration.

The width a party receives depends on how large a cell it holds in one pool:
ALJAMAAH and VF+ are the same size with the same kind of history, and VF+ is
drawn below a tenth of its centre fifty times as often. Whether that is signal
was tested on the panel, holding size fixed (`gaps.py`, pooled established,
centres 0.3-20%, n 173):

| centre size | `a_eff` < 0.5 | 0.5-2 | ≥ 2 |
|---|---|---|---|
| 0.3-1%: realised median abs log error / drawn P(< 0.1×) | 0.46 / 0.336 (n 90) | 0.35 / 0.097 (n 16) | n 1 |
| 1-2% | 0.56 / 0.292 (n 15) | 0.37 / 0.054 (n 7) | — |
| 2-6% | 0.61 / 0.187 (n 3) | 0.41 / 0.026 (n 8) | 0.23 / 0.001 (n 11) |

Regression of realised abs log error on log size and log `a_eff`: coefficient on
log `a_eff` −0.24 (se 0.06). The same regressors on log(drawn median / centre):
+0.93. **Concentration carries real information: parties holding a large share
of one pool do move less, at a given size. The draws make the dependence several
times steeper than the record**: realised error falls by a factor of about
1.3-2.6 from the lowest to the highest concentration class, drawn P(< 0.1×) by a
factor of 3-190. Low-concentration parties also carry a negative mean error
(−0.45 to −0.54 in log at 0.3-2%), consistent with the `compress_levels` lift.

### 2.4 Seeded arrivals against established parties of the same size

The record separates them: realised error for seeded arrivals is rms 1.5-1.8 in
log at 0.1-1% against 0.8-0.9 for established parties (table 2.2), so a wider
treatment for parties with no record **follows from the record**. The code gives
both the same mechanism (the Dirichlet spike), with nearly identical draws at the
same size (2.3, last rows), so the difference the record shows is not
represented. The arrival record that sizes the seeds gives mean 0.29% against
median 0.09% for arrivals contesting about 99% of wards (`seed_notes`, 2026
spec), a mean-to-median ratio of about 3; at JHB 2026 the seeded arrivals
below 0.1% have a median draw of 0.001× their centre (median over 46 parties)
while their mean draw is close to the centre, a ratio near a thousand.

### 2.5 One backtest: Johannesburg 2021 (measured, arm E, 1,000 draws)

Fifteen largest centres. PIT is the share of draws below the result.

| party | path | centre | draw median | draws p25-p75 | level sd | `a_eff` | P(< 0.1×) | result | PIT |
|---|---|---|---|---|---|---|---|---|---|
| ANC | pooled | 38.42% | 38.69% | 33.88-43.81% | 0.15 | 15.3 | 0.000 | 33.22% | 0.217 |
| DA | pooled | 33.33% | 32.37% | 28.94-35.94% | 0.15 | 23.0 | 0.000 | 25.45% | 0.070 |
| EFF | pooled | 13.60% | 12.91% | 9.62-16.46% | 0.16 | 4.9 | 0.000 | 10.11% | 0.281 |
| ASA | seeded | 6.71% | 6.20% | 4.40-8.69% | 0 | 2.0 | 0.000 | 18.12% | 0.997 |
| IFP | pooled | 1.40% | 0.90% | 0.24-2.04% | 0.26 | 0.59 | 0.172 | 2.36% | 0.790 |
| VF+ | pooled | 0.88% | 0.62% | 0.27-1.23% | 0.29 | 0.85 | 0.060 | 1.33% | 0.768 |
| AIC | pooled | 0.71% | 0.27% | 0.04-1.02% | 0.42 | 0.30 | 0.317 | 0.69% | 0.684 |
| ACDP | pooled | 0.58% | 0.31% | 0.11-0.73% | 0.31 | 0.21 | 0.160 | 1.03% | 0.819 |
| GOOD | pooled | 0.36% | 0.12% | 0.03-0.39% | 0.37 | 0.13 | 0.289 | 0.33% | 0.715 |
| ATM | pooled | 0.31% | 0.06% | 0.01-0.27% | 0.39 | 0.09 | 0.412 | 0.32% | 0.781 |
| ALJAMAAH | pooled | 0.30% | 0.23% | 0.10-0.40% | 0.37 | 1.46 | 0.071 | 0.83% | 0.952 |
| PAC | pooled | 0.26% | 0.004% | 0.000-0.16% | 0.42 | 0.12 | 0.599 | 0.27% | 0.789 |
| BLF | pooled | 0.22% | 0.03% | 0.002-0.17% | 0.42 | 0.07 | 0.465 | 0.12% | 0.698 |
| UDM | pooled | 0.18% | 0.008% | 0.000-0.10% | 0.39 | 0.06 | 0.557 | 0.24% | 0.835 |
| PA | pooled | 0.075% | 0.03% | 0.002-0.11% | 0.62 | 0.39 | 0.340 | 2.96% | 1.000 |

Every party between 0.15% and 1.5% has a result above its draw median (PIT
0.68-0.95), and several land near their centre while the draw median sits at a
fraction of it (ATM, PAC, UDM). ASA, a seeded arrival with no level shock,
received 18.1% against a draw p95 of 12.7%; PA rose from 0.075% to 2.96%. 1b v3
§4 classes the ActionSA 2021 miss as a centre error, not a width error.

---

## 3. Duplication: parallel implementations and repeated constants

### 3.1 Samplers and width sources

| idea | implementations | agree? |
|---|---|---|
| draw a triangular | `triangular` (numpy `rng.triangular`) for the entrant and for pool turnout at `rho <= 0`; `correlated_triangular` (copula + `_tri_ppf`) otherwise | same law, different numpy calls; 1c merges them (`tri_from_z`) |
| a party's level width | `levels.size_sd` (θ size line), used by `theta_prior` and `level_shock_sd` | one definition; overridden below 5% by 3.1 next row |
| a pool member's width | `pools.dirichlet_alpha` × cell share | a second, independent width source for the same quantity (how far a party's share moves). The two are never reconciled; their combination is what a party gets |
| arrival-group concentration | `pools.arrival_group_record`: method of moments floored at 0.01 | a third concentration estimator; floor differs from `ALPHA_FLOOR` 1.0 for the same "a concentration below 1 is a spike" reason (switch off) |
| splinter width | `SPLIT_SD_FLOOR` 0.90 (§B3) | typed width outside the size line; feeds sizing, not the draw |
| turnout spread with one observation | 0.30 logits (§A32) | typed, outside `turnout_band`'s record |
| tied-pool turnout band | unweighted mean of member bands (`draw_pools`) | a band built differently from every single pool's |
| t standardisation | `log_shock` (`sqrt((df-2)/df)`); `theta_residual._calibrated_offset_t`, `_t_reference` own seeded t samplers | scoring only, same df convention; agree |
| Dirichlet switched off for ablation | `width_budget._MeanDirichletRNG` monkeypatches `np.random.default_rng` | 1c §2.5 replaces it |
| browser and Worker copies | `interactive/py/montecarlo.py`, `worker-api/seats-py/src/montecarlo.py` | byte-identical to `src/montecarlo.py` (checked with `cmp`). `node interactive/tools/sync_py.mjs --check` reports STALE: `interactive/py/entry.py` differs from the Worker's, `page/render_map.py` and `page/reweight.py` differ from source, `code_ref.py` does not name current sources; `interactive/py/reweight.py` carries the superseded `BOLDNESS` table (§N6 against §N10). Nothing in the browser draws, so this is a presentation-copy drift, not a randomness one |
| turnout | pool turnout (rows 1-2) and VD turnout (rows 11-12) | two independent models of one quantity; see §4.2 |

### 3.2 Constants for one purpose typed several times

"Keep a small share positive" or "stand in for a missing share":

| value | where | role |
|---|---|---|
| 1e-12 | `draw_pools` `base_c` | floor on centres before shocking |
| 1e-9 | `pool_spec` `R`; `compress_levels` kept fraction | floor on centres in the IPF seed; floor on kept fraction |
| 1e-6 | `level_floor`; `levels._centre_for` | level floor in the calibration; centre for a party with no baseline |
| 1e-5 | `levels.size_sd_raw` | size for a party with no baseline (the code notes the 1e-6/1e-5 pair: "two different floors for the same missing quantity") |
| 1e-4 | `DIRICHLET_FLOOR`, `DEFAULTS["dirichlet_floor"]`, local `mean_floor` | one value under three names |
| 1e-3, 1e-4 | `dirichlet_alpha` fallback member cut, upper cut | selection |
| 0.002 | `SHARE_FLOOR` (deviation floor; also the default `base_city` for a party missing from the baseline in `make_drawer`) | two roles for one constant |
| 0.01 | `ALPHA_MIN_SHARE`, `UNIT_LINE_SHARE` (planned), `BYE_CLASS_EDGE` (§A55), orphan warning threshold (inline `0.01` in `make_drawer`) | four "1%" lines; the first and the planned one decide width for the same parties from opposite sides |

Separately, `SD_FLOOR` 0.15 binds for the ANC, DA, EFF and MK at JHB 2026
(`10_theta_prior.at_the_floor`) and `SD_CEILING` 1.20 binds for many parties with
no national record; the record's ≥ 15% movement is sd 0.21 and the drawn width of
those four is 0.17-0.27 after the Dirichlet, so the floor is declared rather than
measured but costs nothing measurable.

None of these is a duplicated sampler. The finding is the one above: two width
sources (size line, pool concentration) for one quantity, combined without
either knowing about the other.

---

## 4. Correlation structure within a draw

### 4.1 What is shared (argued from code; measured where stated)

| shared element | who feels it | who does not |
|---|---|---|
| citywide turnout factor (corr 0.63) | every pooled party, through pool vote totals | individual path, entrant slot (neither turnout-weighted) |
| pool turnout | members of that pool, in proportion to their weight in it | as above |
| Dirichlet within a pool | members of that pool: negative correlation by construction | parties outside the pool |
| level shocks | independent per party | — |
| normalisation | every party: a small negative common factor | — |
| entrant share | every party scaled by `(1 − share)` | — |
| ward noise | independent per ward × party | — |

There is **no common swing factor for any party**. Measured: the mean pairwise
correlation of drawn log shares among established parties below 1% is 0.004
(median over city-years), 0.005 below 5%.

The record has one. Cycle means of log(next / previous), by previous size
(transitions ending 2006 / 2011 / 2016 / 2021):

| previous size | n | total sd | within-cycle sd | cycle means |
|---|---|---|---|---|
| ≥ 15% | 63 | 0.21 | 0.18 | −0.10 / +0.11 / −0.05 / −0.18 |
| 5-15% | 10 | 0.45 | 0.40 | −0.10 / −0.25 / — / +0.15 |
| 2-5% | 27 | 0.81 | 0.66 | −0.15 / −0.88 / −1.21 / −0.13 |
| 1-2% | 48 | 0.77 | 0.67 | −0.30 / −1.07 / −0.51 / −0.15 |
| 0.5-1% | 47 | 0.68 | 0.63 | −0.22 / −0.84 / −0.38 / −0.28 |
| 0.2-0.5% | 89 | 0.82 | 0.65 | −0.34 / −1.05 / −0.44 / +0.31 |
| 0.05-0.2% | 54 | 0.87 | 0.73 | +0.15 / −0.95 / −0.40 / +0.41 |
| < 0.05% | 15 | 0.90 | 0.74 | — / −1.12 / 0.00 / +0.71 |

Every band below 5% moves together within a cycle (2011: −0.84 to −1.12 in every
band), and the cycle accounts for roughly 15-40% of a small party's variance. Above
5% the cycle means are small. The combined share of established parties below 1%
moved with sd 0.86 in log (n 23 metro-transitions; cycle means −1.50 / −0.43 /
+0.30; this record counts a party that did not stand again as zero, which a
forecast with a known roster would not). The drawn class total has sd 0.59 at
JHB 2026 and 0.77 median over the panel, built from independent members rather
than a shared swing.

### 4.2 Two turnout layers that do not meet (measured)

Per draw, citywide votes implied by the pool turnouts (registered × drawn
turnout, summed over pools) against the votes the run counts (`pr_vote_draws`,
from per-VD turnout):

| run | pool layer, sd / mean | VD layer, sd / mean | correlation |
|---|---|---|---|
| JHB 2026 | 0.149 | 0.003 | 0.018 |
| JHB 2021 | 0.116 | 0.003 | −0.021 |

The pool turnout draw decides party shares (through `totals / cast`). The vote
counts and the ward tallies (`weight_cal = reg * t_draw`, `part_cast`) use a
separate per-VD turnout that does not read the pool draw. So the "correlated
citywide turnout shock" the code describes is a composition shock only: no draw
has a low-turnout city in its vote counts, and a draw where one pool turns out
heavily raises its parties everywhere through the calibration rather than in
that pool's VDs. §A41 records the VD layer's citywide effect as about 0.003; it
does not record that the two layers are independent. The effect on ward winners
is not measured.

---

## 5. Verdict and recommendations

### 5.1 Is uniform treatment the right target?

No, and the record says where not. Parties of different kinds do move
differently:
- **by size**: record width sd 0.21 at ≥ 15%, 0.45 at 5-15%, 0.68-0.90 from
  0.05% to 5% (table 4.1);
- **by history**: seeded arrivals' realised error is about twice established
  parties' at the same size (2.4);
- **by pool concentration**: real at a given size, but weaker than the code makes
  it (2.3);
- **by cycle**: everything below 5% shares a cycle swing; large parties barely do.

What the record does **not** show anywhere is a spike at zero: below 5% the
record's central half of next/previous stays at 0.35-2.1× at every size, and
P(< 0.1×) is at most 0.027. A uniform width for every party would be wrong. The
defects are differences the record does not support, and missing differences it
does.

### 5.2 Ranked inconsistencies

| # | inconsistency | severity | basis | proposed unification | this round? |
|---|---|---|---|---|---|
| 1 | Below 5%, width is set by the pool's concentration × the party's cell share, not by anything measured about parties of that size. Draws put 7-80% of mass below a tenth of the centre where the record puts 0-3%; 50% band holds 2-32% of results below 0.3% | changes forecast materially (1b v3: 473 of 5,000 JHB 2026 draws with an established party below the line above 5%) | record | one sampler for all parties below a size line, width from the record of residuals about the centre (1b v3's logit-Gaussian with record widths) | below 1% yes (1b + addendum); 1-5% next round |
| 2 | Parties at 1-5% (JHB 2026: IFP, RISE, BOSA, VF+, ACDP) keep the spike after the round, while parties just below 1% do not | changes forecast (1b v3: IFP, RISE, BOSA and VF+ together above 5% in 995 of 5,000 draws; the addendum adds ACDP above 5% in 75) | record: the 1-5% band behaves like the sub-1% band in width (0.77-0.81 against 0.68-0.90), cycle co-movement and tails (P(< 0.1×) 0.027, largest later share 10.8% from 2-5%) | extend the unit sampler's line to where the record's behaviour changes, about 5% (owner's judgement) | later; decide before the 1c streams are fixed, see 5.4 |
| 3 | No common swing in the draws for any party; the record has a strong one below 5% | changes forecast (joint tails: how many small parties win seats together) | record | 1b's `σ_cyc` factor for established unit parties; extend it to whatever line #2 settles | yes for < 1% (1b); with #2 later |
| 4 | Seeded arrivals get the same spike as established parties of the same size; the record says they are about twice as uncertain, with a mean-to-median ratio near 3, not hundreds | matters for honesty; affects which arrival wins a seat | record (that they differ); principle (one sampler) | draw seeded arrivals on the unit sampler, own term only, with σ from the arrival record about the seed (1b found debutant cycle means opposite in sign to established parties in two of three cycles, so no shared cycle factor) | later; 1b leaves seeded arrivals on the Dirichlet by design |
| 5 | Same size, different width by pool cell share (ALJAMAAH vs VF+; PA vs MK and ASA) | changes forecast for PA, whose width (robust log-sd 0.27 at 5.8%) is half MK's | record supports a dependence on concentration; its steepness is a code artefact (coefficient −0.24 in realised error against +0.93 in the drawn median) | once #1/#2 apply, width comes from size and history; concentration, if kept, enters as a measured covariate on the width, not through `A_g × share` | later |
| 6 | Two independent turnout models: the pool layer varies citywide turnout by 12-15%, the counted votes by 0.3%, correlation about 0 | matters for honesty (whatever reads `pr_vote_draws` carries no turnout uncertainty: `backtest`, `export_draws`, `reader_seats` found, not followed); ward effect unmeasured | record says city turnout varies (`TURNOUT_CORRELATION` comment: 2021 decided by abstention) | drive each VD's drawn turnout by its pools' drawn / central turnout ratio, so one draw has one turnout; deterministic transform, no new stream | later; measure ward-winner change first |
| 7 | Tail families differ by path: t7 for the level, Dirichlet gamma for the split, bounded triangular for pool turnout and the entrant (max 12%), Gaussian for the planned unit class | matters for honesty | principle; the record supports the unit class's choice: logit-Gaussian σ 0.94 gives P(> 3×) 0.12 and P(< 0.1×) 0.007 against the record's 0.07-0.11 and 0-0.03 below 1% (argued from the normal CDF) | state per quantity why its support is bounded or not; `log_shock`'s docstring argues against bounded supports that turnout and the entrant still use | later; register entries only |
| 8 | Individual path reachable but unused; it would give a level-shock-only width, and the orphan warning ignores parties below 1% | cosmetic now | principle | refuse a party with a centre and no pool vector at any size, or route it to the unit sampler | could be done in the round (one condition); not required |
| 9 | Floor and threshold zoo (3.2): one value under three names, 1e-6/1e-5 for one missing quantity, `SHARE_FLOOR` in two roles, four "1%" lines | cosmetic | principle (one definition) | name the shared ones once; `UNIT_LINE_SHARE` and `ALPHA_MIN_SHARE` should be read together in the register, since both decide width for the same parties | later |
| 10 | Tied-pool turnout band is an unweighted mean of member bands | cosmetic (argued; not measured) | principle | weight by registered voters, or fit the tie group's band from the record directly | later |
| 11 | `interactive/py` copies stale against `src` (3.1) | cosmetic for randomness (the browser does not draw) | principle | re-sync at step 9 as planned | step 9 |

`compress_levels`'s lift (every small party's centre × 1.20-1.40) is a level
defect already filed (`1b-level-lift-defect.md`); it applies equally to every
path and is not repeated here.

### 5.3 The owner's tiny-party class, judged against the record

| owner's claim or choice | what the record shows | verdict |
|---|---|---|
| tiny parties should be modelled as a class | they share a cycle swing (table 4.1) and have a common width (0.68-0.90) regardless of size from 0.05% to 5% | supported |
| their combined performance is more predictable | the class total moved with sd 0.86 in log against 0.68-0.90 for members: little more predictable as a total, because the swing is shared. What is predictable is the ceiling: 0 of 244 parties standing again from below 1% reached 5% | partly supported; the predictability is in the ceiling, not the total |
| the line at 1% | no change of behaviour at 1% in width, cycle or tails. The change is between 5% and 15% (sd 0.45, n 10) and again at 15% (0.21). The record neither forces 1% nor contradicts it; its cost is #2 | a judgement; the record would place the line nearer 5% |
| drawn outside the pool split | the pool split is what produces the spike the record does not show (2.2) | supported |

### 5.4 Effect on the paired-draws design (1c)

Nothing here changes 1c's design. 1b v3 §3.6 already specifies `unit.cycle`,
`unit.metro` and `unit.member` streams. Moving the line later (#2) or moving
seeded arrivals onto the unit sampler (#4) changes which parties read
`unit.member` instead of `split`; 1c §2.6 already states that a party moving
between paths is unpaired by design across that change. #6 is a deterministic
transform of existing streams. If the owner expects to move the line in the next
round, the arms comparing old and new lines will be unpaired for the parties that
change path, and the pre-registration should say so.

### 5.5 Rejected claims

| claim | evidence that rejects it here |
|---|---|
| Ranks 4-12 are drawn too narrow (§B7 record item 5: sd(z) 1.94 on the reference population, 2026-08-20) | arm E (current model) at 1-5%: 90% band 0.98, 50% band 0.71, median PIT 0.65 (over-wide); different model date and a rank-defined population. Not reconciled; the arm E figure describes today's draws |
| The level shock is where a party's measured width enters the draw | below 5% the Dirichlet supplies most of the drawn width (§B7: 83-98% of variance for every party except the ANC and DA); the level shock's 0.26-0.56 is not visible in draws whose central half spans 0.001-0.54× |
| Seeded arrivals and established parties get different uncertainty | at JHB 2026 the 22 seeded parties at 0.071-0.078% and the established ECONOMIC_LIBERATORS at 0.074% have P(< 0.1×) 0.80-0.82 and 0.80: the level shock the established party carries makes no visible difference |
| The citywide turnout shock moves the city's turnout | the counted votes vary by 0.3% per draw, uncorrelated with the pool turnout draw (4.2) |
