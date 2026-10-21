# Turnout in the model: chain, consistency, defects

Repository `atlas-jhb-election-model`, branch `remediation`, HEAD `3fe9f1f`, host Atlas. Read-only audit, 2026-10-17. No tracked file edited, nothing under `data/` written, no `montecarlo.py`/`compare_history.py` script run, no sweep, no emit.

**Evidence labels used throughout.**
- **[code]**: read in the source at the cited line.
- **[run]**: measured by me in process (`run_model` imported, Johannesburg 2026 unless stated, seed 20261104, paired by draw index). Scripts and outputs are in this directory: `run1.py`, `decomp.py`, `clip.py`, `largest.py`, `levels.py`, `cover.py`, `diff.py`, `notes.py`. One seed, 400 to 2,000 draws. Treat the small moves as indicative, not settled.
- **[doc]**: what a document claims. I did not re-derive it unless I say so.

---

## 1. The turnout forecast chain, raw files to per-draw turnout

### Step 1. VD turnout series: `turnout.read_turnout`, `turnout.turnout_series`
- **What it computes [code].** VD → (registered, cast). Cast is valid plus spoilt. At an LGE it takes the higher of the ward and PR ballots (`src/turnout.py:83-105`). VD-years above 105% are dropped (`:137-145`). Only elections strictly before the target are read (`:195`).
- **Data.** IEC result CSVs in `data/raw/elections`.
- **Judged.** The 1.05 drop threshold. Using registered voters as the denominator without MEC7. The docstring says this runs about 0.5 points under the IEC headline (`:22-29`) [doc].
- **Tested.** No accuracy test applies. It is a count.

### Step 2. λ drop-off per VD and the projection: `turnout.main`
- **What it computes [code].**
  - λ_y(i) = T_LGE(i) / T_preceding-NPE(i), for the last two measurable LGE/NPE pairs (`:207-243`). VDs whose NPE turnout is ≤ 0.05 are ignored (`:223`).
  - λ̂ = w·λ_recent + (1−w)·λ_prior, with w = `--w-recency` 0.70. A VD with only one cycle falls back to that cycle (`:399-403`).
  - By-election tilt: ×(1 + κ_bye·(ratio−1)) with κ_bye = 0.25 (`:355-384`, `:405`).
  - `turnout_<T>_projected` = min(T_previousNPE · λ̂ · tilt, 1) (`:405`).
  - `turnout_<T>_level` = the previous LGE's VD turnout, rescaled to the projection's citywide level (`:429-446`).
  - Output is `turnout.csv`, which carries no artefact key.
- **Data.** For Johannesburg 2026: λ_2016 (2016/2014) and λ_2021 (2021/2019), applied to T_2024. These are the columns of `data/processed/turnout.csv` [run: header read].
- **Judged.** w_recency 0.70 and κ_bye 0.25 are argparse defaults. MODEL-LOG (line ~9608) already records that both are verbatim from the plan, that their sensitivity test was never run, and that they reach the model through a keyless file. The 0.05 and the 1.0 cap are also judged.
- **Tested against real elections.**
  - MODEL-LOG §1.2 [doc]: at the VD level, the previous-LGE pattern beats the ratio form at predicting 2021 VD turnout (MAE 0.0409 against 0.0592) and 2016 (0.0527; the ratio form could not be computed). `turnout.py` re-prints this mini-backtest on every run (`:282-350`).
  - MODEL-LOG §1.8 [doc]: with θ fixed, even the oracle turnout weighting did not improve seats.
  - **The projected citywide level has no written score that I could find** (grep of MODEL-LOG). I scored it [run, `levels.py`]. Each row is the roll-weighted `turnout_<T>_projected` against the realised cast turnout, both on `turnout.py`'s definition:

    | target | projection minus realised, 8 metros |
    |---|---|
    | 2011 | −7.4 to −16.7 points (projection below reality at all 8) |
    | 2016 | −3.9 to −11.4 points (below at all 8) |
    | 2021 | +2.4 to +11.4 points (above at all 8) |

### Step 3. Pool turnout at each LGE: `pools.pool_counts` (ecological)
- **What it computes [code].** The model nests four levels: people ⊇ adults ⊇ registered ⊇ voted, ward × pool (`src/pools.py:1318-1600`).
  - Turnout is `_nest_holding_silent(registered, votes_by_ward)` (`:1561`).
  - That fits **one non-negative rate per pool across all wards** by bounded least squares, `_nnls` (`:975`): observed_w ≈ Σ_g registered_wg·r_g, unweighted on counts.
  - It then scales every ward so its pools sum to the observed votes (`_nest`, `:955-972`). Within a ward, every pool's turnout is therefore r_g times a ward factor.
  - `rates["turnout"]` is the regression coefficient r_g, not the aggregated voted/registered ratio.
- **Data.** Census 2022 composition moved onto each election's wards. IEC registered voters per ward. **Votes are PR-ballot valid party votes only** (`ward_totals`, `ballot="PR"` default, `:1263`, `:1314`). Spoilt ballots are excluded and the higher-ballot rule is not applied.
- **Judged.** A pool driven to the 0.0 corner is held at the city's rate (§L14). Registration is capped at 2.0 (§L9). Johannesburg's White registration rate exceeds 1, which the docstring calls impossible (`:739-760`).
- **Uncertainty.** None is computed or carried. No standard error, no resampling. A point estimate travels everywhere.
- **Tested.** No comparison with any count. Several realised rates are identification failures. Realised over previous-LGE pool turnout reaches ×16.6 (Coloured) and ×11.9 (Indian/Asian) at Buffalo City 2011, and ×4.49 at Tshwane 2016 Indian/Asian [run, `diff.py`]. `_spread`'s docstring describes the same failure (`:3175-3196`).

### Step 4. The pool turnout band: `pools.turnout_record`, `panel_turnout_spread`, `turnout_band`
- **Record [code].** `turnout_record` holds each prior LGE's `rates["turnout"]` (`:2913-2953`).
- **Band [code].** `turnout_band` (`:2956-3064`):
  - centre = the **last LGE's** pool rate;
  - spread = max(panel spread, the city's own logit range);
  - low and high = expit(logit(centre) ∓ spread).
  - This is emitted as `(low, mode, high)` in the spec (`:6413-6421`).
- **Panel spread [code].** The 0.90 quantile of |Δlogit| over all metros' consecutive-LGE transitions before the target (`:3067-3232`). The top point is winsorised when n ≥ 6. The pooled value is a floor only below 4 own observations. 0.30 logits is the fallback (`_PANEL_SPREAD_FALLBACK`, `:1146`; §A32).
- **Johannesburg 2026 bands [run, `data/processed/pools_2026.json`]:**

  | pool | low | mode | high |
  |---|---|---|---|
  | Black African | 0.231 | 0.364 | 0.521 |
  | Coloured | 0.241 | 0.543 | 0.816 |
  | Indian/Asian | 0.085 | 0.408 | 0.836 |
  | White | 0.315 | 0.527 | 0.729 |

- **Judged.** The centre is the last LGE (no trend, no NPE information). The 0.90 quantile, the one-point winsorisation, the thresholds 4, 6 and 12, and the 0.30 fallback. The triangular shape. Note that the band is symmetric in logit and then drawn as a **triangular in turnout space**.
- **Tested.** MODEL-LOG §1.162 §9 [doc]: before the panel spread existed, the band excluded realised citywide turnout at 11 of 24 city-years. The panel spread was the repair. No coverage test of the repaired band is recorded in the entries I read. My probes are in §3, defects D3 and D4.

### Step 5. The pool draw: `make_drawer.pool_turnouts`, `correlated_triangular`
- **[code]** One draw per pool per draw index d. The Gaussian copula is z = √ρ·z_common + √(1−ρ)·z_own, mapped through the triangular's inverse CDF (`src/montecarlo.py:940-962`, `:4695-4725`). ρ = `TURNOUT_CORRELATION` 0.63 (`:789`). It was measured as the mean off-diagonal correlation of pool log-turnout changes over 14 metro transitions (comment `:776-788`; §B5 for the copula form).
- A tied group draws one value from the averaged band and gives every member that same absolute turnout (`:4714-4723`). No emitted spec declares a tie [run: every `pools_*.json` checked].
- The draw is recorded in `turnout_record` and has no effect on the preliminary vote (`:4697-4701`).
- **[run]** Johannesburg 2026 pool turnout over 400 draws:

  | pool | mean | sd | mean ÷ mode |
  |---|---|---|---|
  | Black African | 0.3707 | 0.0585 | 1.019 |
  | Coloured | 0.5409 | 0.1111 | 0.996 |
  | Indian/Asian | 0.4449 | 0.1471 | 1.089 |
  | White | 0.5250 | 0.0812 | 0.997 |

### Step 6. The reference: `run_model` → `scenario["_turnout_reference"]`, `pool_spec`
- **[code]** The reference is `pools.pool_counts(city, spec["fitted_on"]).rates["turnout"]`, the same quantity as the band mode (`:6218-6235`).
- `pool_spec` sets each pool's preliminary-vote weight to registered_at_target × reference (`:3390-3396`) and fits the pool × party matrix R by IPF to those pool votes and the centres (`:3518`).
- `draw_pools` returns the preliminary vote at those weights (`:4795-4800`, `:4806-4822`).
- §V1 marks the reference as an owner's call.
- **[run]** Reference equals band mode exactly at Johannesburg 2026 (`41_guards.turnout_reference`).

### Step 7. The district level: `run_model` turnout patterns
- **[code]** Per VD:
  - t_ratio = `turnout_<T>_projected`;
  - t_level = the raw `turnout_<prevLGE>` column, rescaled in place to the projection's roll-weighted mean on the target roll (`:6898-6936`). It does **not** read `turnout.py`'s `turnout_<T>_level` column.
  - A VD missing either pattern takes the city's roll-weighted mean of that pattern (§A49).
- **[run]** 47 VDs (1.98% of the roll) have no projection; 825 VDs have one. Mean projected 0.4194, mean previous-LGE 0.4272 (`notes.py`).
- Reference district turnout (`reference_district_turnout`, `:1678-1698`):
  - level = (1−b)·t_ratio + b·t_level, with b = `turnout_pattern_blend` 0.5;
  - a VD with no projection takes scale × Σ_g c_vg·t_ref_g, with scale set so those VDs sit on the projected level;
  - the level is split over pools as T_vg = level_v·t_g / Σ_h c_vh·t_h (`district_pool_turnout`, `:1658-1675`);
  - the result is clipped to [0.02, 0.95].
- c_vg is the VD's ward's **registered** composition at the fitting election (`:6224-6231`, `:7532-7543`).

### Step 8. Per-draw district turnout: the draw loop
- **[code]** (`:7616-7648`)
  - blend_d = clip(0.5 + U(−1,1)·0.25, 0, 1);
  - noise is i.i.d. lognormal per VD with σ = 0.08 and mean 1;
  - t_draw = clip(level(blend_d)·noise, 0.02, 0.95);
  - each pool column is then multiplied by k_g = drawn_g / reference_g and clipped again (`drawn_district_turnout`, `:1701-1711`).
- The district total per draw is therefore level_v · Σ_g c_vg·t_g·k_g / Σ_g c_vg·t_g.
- **Judged** (§A41, §F23): 0.5, 0.25, 0.08, and the 0.02/0.95 clip (§F34).
- **[run]** Johannesburg 2026 citywide drawn turnout over 500 draws: mean 42.6%, sd 6.2 points, p5 32.4%, p95 52.8%. Reference 41.9%. The ceiling clip binds on 0.28% of roll×pool weight per draw and removes 0.03 turnout points on average. The floor never binds (`clip.py`).

---

## 2. From drawn turnout to the vote, wards and seats (HEAD)

1. **Preliminary vote** `pr_target = draw_target(d)`: party shares at the reference turnout (`:7601`).
2. **Map at reference weights** (`realise_draw`, `:1817-1836`). `solve_and_predict` places each ballot's preliminary vote on VDs with weights w_ref = reg × Σ_g c_vg·T_ref,vg (`district_frame`, `:1800-1814`). At the reference, the citywide share equals `pr_target`.
3. **District pool split** (`district_split`, `:1714-1758`). An IPF per VD, seeded with the draw's pool split R(d). It has two margins: each pool row sums to 1, and Σ_g q_vg·π_gvp = map share, where q is the reference voter composition. It stops at 60 rounds or a 1e-6 row error, ending on the party margin.
4. **District votes** (`district_votes`, `:1761-1776`).
   - n_v = Σ_g c_vg·T_vg(d), votes per registered voter;
   - mix_v = Σ_g c_vg·T_vg(d)·π_gv, normalised;
   - π is computed once per draw from reference quantities and **does not change with T**. Both ballots use one n (§V7).
5. **Citywide** (`:7651-7659`): pr_votes = (reg·n) @ pr_mix, and shares are pr_votes / Σ. Nothing re-solves the total to `pr_target`.
6. **Wards** (`:7661-7682`): part_cast = part_reg·n[part_vd]; the tally is part_cast × the ward mix, masked per part; lognormal ward noise is applied; the winner is the argmax.
7. **Seats** (`:7696-7720`): whole votes per ballot, then `eligible_parties`, `outside_pool_wards`, `allocate_with_overhang` and `council_seats`.

**Consequence derived from the code [code, argued].** Scaling every VD's n by one factor leaves shares, ward argmaxes and seat quotas unchanged. Only the 0.95 clip breaks that, and it is negligible per step 8. So the citywide **level** of the turnout forecast (λ̂ × T_NPE) does not reach shares or seats. Three things do:
- the **spatial pattern** of n (w_ref, and the per-draw blend and noise);
- the **relative** pool shocks k_g;
- the mean of k_g against its mode (§V6).

---

## 3. Inconsistencies and defects

Each item: evidence, then severity for the published forecast, then fix. Severity is my judgement, ordered by what moves published numbers.

### D1. The §V6 skew is an artefact of the band's construction, and it is the only turnout effect on the published means
- **Mechanism [code + arithmetic].** `turnout_band` builds endpoints symmetric in logit. For a centre below 0.5, expit makes the turnout interval right-skewed; above 0.5, left-skewed. The draw is a triangular in turnout space, whose mean is (a+m+b)/3. So E[k_g] = mean/mode is above 1 for every pool whose last-LGE turnout was below 50% and below 1 otherwise.
  - Johannesburg 2026: Black African ×1.022, Indian/Asian ×1.086, Coloured ×0.982, White ×0.994 (from the spec bands).
  - The sign is fixed by which side of 50% the pool sat in 2021. No measurement of turnout direction enters.
- **The record runs the other way [run, `diff.py`; ecological estimates, not counts].** For log(k_BA/k_White), the model's median is +0.005 to +0.037 at every backtest city-year. The realised value (pool_counts at the target over the reference) is negative at 18 of 24 city-years.
- **Size at Johannesburg 2026 [run, `decomp.py`, 1,000 paired draws; `largest.py`, 2,000].** Removing only the skew (each draw rescaled so the pool mean equals the mode, arm `meanfix`):

  | quantity (Johannesburg 2026) | base (HEAD) | skew removed |
  |---|---|---|
  | DA mean list share | 26.03% | 26.31% |
  | ANC mean list share | 24.06% | 23.88% |
  | PA mean list share | 5.61% | 5.72% |
  | DA mean seats | 69.68 | 70.29 |
  | ANC mean seats | 72.83 | 72.73 |
  | PA mean seats | 14.87 | 15.12 |
  | P(ANC largest alone) | 60.8% | 58.0% |
  | P(DA largest alone) | 31.5% | 34.1% |

  - `turnout_moved` at HEAD is DA −0.247, ANC +0.163, PA −0.076 points. With the skew removed it is DA +0.038, ANC −0.023. The skew is the whole of `turnout_moved`.
  - The prereg arithmetic in §V6 (DA −0.31, ANC +0.21) and MODEL-LOG §1.317's 5,000-draw `turnout_moved` (DA −0.26, ANC +0.18, PA −0.12) agree in sign and size.
  - §1.317's old → new movement (P(ANC largest) 56.1% → 60.6%) also includes the width-record re-fit, so it is not attributable to the skew alone.
- **Backtest.** §1.317 attributes the N-P means movement to this skew ("DA fell and ANC rose at 20 of 24, within 0.25 of the pool arithmetic at 24 of 24"). The canonical list-MAE improvement 3.212 → 3.152 therefore comes from an artefact that pushes DA down, against the sign of the record's realised pool differential.
- **§V6's justification** ("the band is the model's forecast of turnout") does not hold. The band's level never sets any district's turnout (D2). Only its mean/mode ratio does.
- **Severity: high for a published forecast.** It moves the headline "who is largest" probability by about 3 points and DA seats by about 0.6, with no evidence behind its direction.
- **Fix.** State the centre as a median and draw in logit space: z → expit(logit(m) + h·T(z)), which keeps the median at m. Or normalise k_g to mean 1. Then re-score the backtest and report the MAE change honestly. Do not keep the change because it scores; §1.317 already shows the better score comes from the artefact.

### D2. Two different turnout forecasts are combined; the band's level is used only as a denominator
- **[code].** The reference district total is the λ̂ projection blend (`:1678-1698`, `:7546-7550`). Pool ratios within a district are the pool_counts rates at the fitting LGE. The per-draw shock is drawn/reference. The band's centre therefore never sets a level: drawn citywide turnout = projection × E_roll[k].
- **The two forecasts differ in election, method and definition.**
  - Election: NPE × λ̂ against last-LGE pool rates.
  - Method: VD-level ratio against a pool regression coefficient.
  - Definition: max-ballot cast incl. spoilt (`turnout.py:102-105`) against PR valid votes (`pools.py:1263-1314`).
- **Level agreement by city-year [run, `levels.py`].** They agree at Johannesburg 2026 only by coincidence (projection 0.419, pool reference 0.418, `turnout_scale` 1.002). Elsewhere they differ by 4 to 9 points:

  | city-year | projection | pool reference |
  |---|---|---|
  | Johannesburg 2016 | 0.496 | 0.544 |
  | Mangaung 2021 | 0.474 | 0.560 |
  | Buffalo City 2021 | 0.480 | 0.545 |

- **What the districts carry where they disagree [run, `largest.py`].**
  - Johannesburg 2016: `turnout_scale` 0.914. Districts carry Black African 0.463 against a reference of 0.508, and White 0.594 against 0.643. 132 VDs have no projection.
  - Mangaung 2021: scale 0.852; Black African 0.455 against 0.532.
  - **Ratios between pools are preserved** (BA/White 0.791 → 0.779 at Johannesburg 2016; 0.809 → 0.819 at Mangaung 2021). The level mismatch therefore barely reaches shares (§2 consequence).
  - The IPF's pool votes (pool_spec) sit at the pool-reference level while the districts sit at the projection level. The reference's own documentation (MACHINERY "Turnout enters the vote" step 1, §V1) describes them as one "centre".
- **Severity: low for shares and seats. Medium for anything that publishes a turnout figure or a band.**
  - The published turnout is the projection × skew.
  - The band was validated (§1.162) as a level interval around the last LGE, but it is now applied as a ratio around a different centre.
- **Fix.** Pick one turnout forecast. Either derive pool shocks relative to the projection's implied pool turnout, or set the district level from the pools. Put both on one turnout definition. Re-state §V1.

### D3. The band is narrower than the record it is built from, by construction
- **[code + arithmetic].** The 0.90 quantile of observed |Δlogit| is used as the triangular's **support half-width** (`pools.py:3056-3060`). A symmetric triangular on [m−h, m+h] puts 90% of its mass inside ±0.684h. A movement equal to the panel's q90 therefore sits at the support edge (zero density), and the band's own 90% interval reaches only 0.68 × q90. This is **derived; I did not compute the exact coverage of the band's quantiles against the movement record**.
- **[run, `cover.py`].** It simulates the copula on spec bands times the projection. It omits VD noise, which `decomp.py` shows is negligible citywide.
  - Realised citywide turnout falls inside the drawn 90% interval at 13 of 24 city-years: 9 above p95 (7 of them at 2011) and 2 below p5.
  - For Johannesburg 2026 the simulation gives p5 31.8%, p50 42.4%, p95 53.3%, against the full run's 32.4%, 42.6% (mean) and 52.8%.
- **[run, `diff.py`, ecological].** The differential log(k_BA/k_White) falls inside the 90% interval at 15 of 24, with 8 below p5.
- **Severity: medium.** This affects width, not means. The differential matters more than the level, because it is the part that reaches party shares.
- **Fix.** Fit a dispersion, not a support. For example, a logit-normal or logit-t with sd estimated from the panel Δlogit. Fit the differential's correlation (ρ) from the same record, then test coverage on a held-out cycle.

### D4. Given the true turnout, the mechanism moves the vote the wrong way; the published width and every turnout scenario rest on it
- **[doc, MODEL-LOG §1.317].** Feeding counted district turnout (N-Ovd) raises pooled list MAE by 0.478 (better at 6 of 24). Feeding ecological pool turnout (N-Opool) raises it by 0.672 (better at 8 of 24). P3 is falsified. §1.317 names three explanations and says the separating measurement does not exist:
  - (i) the ecological pool turnout is biased;
  - (ii) preference covaries with turnout within a pool (D6);
  - (iii) θ already carries LGE turnout behaviour (D7).
- **[run].** The pool shock widens DA list sd from 3.77 (k ≡ 1, arm `mode`) to 4.20 points at HEAD, and ANC from 3.44 to 3.58. VD noise and jitter add nothing (D9). The same mechanism drives the interactive's turnout control: §1.315 records Black African +5 points → DA −4.1 seats through `reweight.turnout_tilt` (`src/reweight.py:387`). §1.317's debt paragraph says the record calls this too large in DA's favour when Black African turnout falls.
- **Severity: medium for published bands. High for any turnout scenario shown to readers.**
- **Fix.** Run the separating measurement §1.317 names: N-Ovd on θ estimated from turnout-standardised shares. Until it exists, label turnout scenarios as unvalidated, or withdraw them.

### D5. The district IPF does not converge; the register states a figure 80× smaller
- **[run].** `41_guards.district_ipf` at Johannesburg 2026: `rounds_mean` 59.9 against the 60-round cap, `worst_row_error` 0.047 (400, 1,000 and 2,000 draws). §1.317 [doc] records 0.056 at 5,000 draws with the cap reached on most calls.
- **[doc].** JUDGEMENT-CALLS §V4 says "one Johannesburg 2026 draw: worst row error 6e-4 at 60 rounds, 9e-8 at 145".
- **Effect.** At the reference the error cancels exactly, because the IPF ends on the party margin. [run] Arm `mode` (k ≡ 1) gives `turnout_moved` 0.000 for every party. Off the reference, a pool row summing to 1.047 over-weights that pool's voters by up to 4.7% in some VD when its shock is applied. The size on citywide shares is unmeasured; it is bounded by about 5% of a turnout effect that is itself at most about 0.3 points.
- **Severity: low numerically; a register defect.**
- **Fix.** Raise `DISTRICT_IPF_ROUNDS` (§V4 itself reports 145 rounds → 9e-8), or iterate to tolerance with a reported cap hit. Correct §V4.

### D6. Within-pool preference is held fixed as turnout moves (question e)
- **Where it is assumed [code].**
  - `district_votes`: π_gv is computed once at reference quantities and multiplied by the drawn T_vg (`:1761-1776`; `district_split` `:1714-1758`).
  - `pool_spec_centres(spec, turnout=)`: the fixed per-pool split R is re-weighted by pool turnout (`:3920-3936`).
  - `pool_turnouts`' docstring: turnout does not enter the preliminary vote (`:4697-4701`).
  - `reweight.turnout_tilt`.
- **[doc].** §V3 and §V4 register the split, not this behavioural assumption. §1.317 explanation (ii) names it. `PoolCounts`' docstring says "the 2021 ANC collapse was 587k abstentions, not switches" (`pools.py:762`). That is a partisan differential *within* the Black African pool, which this mechanism cannot express: a Black African turnout fall removes that pool's voters in proportion to every party they support.
- **Severity: medium (conceptual). It is one of the three candidate causes of D4.**
- **Fix.** Allow a party-specific turnout elasticity within a pool, estimated from VD-level turnout and share changes across cycles. Or test (ii) against (iii) as §1.317 specifies.

### D7. Turnout may be counted twice through θ and the centres (question f)
- **[doc].** §1.317 (iii) is the hypothesis that the centre's θ already carries the cycle's LGE turnout behaviour. MODEL-LOG §1.8 had the same finding in August and §1.317 does not cite it. §1.8 says the oracle turnout weighting did not improve seats, and "fold 1's θ was itself calibrated under baseline weighting… switching introduces a mismatch".
- **[code].** The width record strips realised pool turnout from σ (`width_record.case_for`, `:558-581`, §V5). Nothing strips it from the centres: θ is estimated on realised local and national shares.
- **[run, `diff.py`, ecological].** Black African turnout fell relative to White at 18 of 24 transitions. A θ learned from LGE results would embed that regularity.
- **Severity: medium. It is a candidate cause of D4; unresolved.**
- **Fix.** The measurement §1.317 names: θ on turnout-standardised shares, then N-Ovd.

### D8. The width record carries turnout to the vote by a second, different mechanism
- **[code].** `case_for` carries each earlier centre to realised pool turnout through `pool_spec_centres`: a citywide re-weighting of the fixed R. The draw carries turnout through the district IPF and the district map (`district_votes`). These are two definitions of "how turnout moves the vote", which conflicts with CLAUDE.md's no-duplicated-logic rule.
- §V5 [doc] notes that this carrying made the centre's list error *worse* on the record.
- σ is therefore measured about a turnout-adjusted centre whose adjustment adds error, and drawn turnout then adds width again. Turnout-related error may be counted in both σ and k. This is unmeasured.
- **Severity: medium (width).**
- **Fix.** Carry the record's centres with the same function the draw uses (the district path at realised district and pool turnout), or document why they must differ. Measure σ with and without the carry.

### D9. The noise and jitter claims in the register come from the old mechanism
- **[doc].** §A41 and §F23 say the 0.08 noise has "~0.003 citywide, i.e. nothing", and §A41 cites "46 ward wins". Both come from the redistribution mechanism deleted on 2026-10-16. MACHINERY §5 says the effect is "not yet measured".
- **[run, `decomp.py`, 1,000 paired draws].** Setting noise to 0 and jitter to 0 changes mean list shares by at most 0.002 points and sd by at most 0.001 points. Mean ward wins change by at most 0.03 wards per draw (ANC 71,125 against 71,095 summed over 1,000 draws).
  - Mechanism [code]: noise scales a VD's level uniformly across its pools, so it leaves the VD's mix unchanged and only re-weights VDs. 825 i.i.d. factors average out.
- **Severity: low (documentation).**
- **Fix.** Re-record §A41, §F23 and MACHINERY §5 with this measurement, or a better-powered one.

### D10. The §C3/§F34 contradiction is now measured
- **[run].** The 0.95 ceiling binds on 0.28% of roll×pool weight per draw and removes 0.03 turnout points. The 0.02 floor never binds. In the reference, 0.12% of roll×pool is above the ceiling.
- **Severity: low.**
- **Fix.** Record the measurement under §F34 and resolve the contradiction with §C3.

### D11. Turnout definitions are inconsistent
- **[code].** Pool rates use PR valid votes over registered (`pools.py:1263-1314`). District levels use max-ballot cast including spoilt over registered (`turnout.py:102-105`). The district votes generated (reg·n) are used as valid party votes (`:7696-7700`), so whole-vote totals carry spoilt ballots.
- **[run].** Johannesburg 2026: previous-LGE cast turnout 0.427 against pool reference 0.418. I did not separate the definitional part from the weighting part (registered_at_target).
- **Severity: low.** Shares and seat quotas are invariant to a uniform scale.
- **Fix.** Use one definition throughout.

### D12. Tied groups do not move by one ratio (latent)
- **[code] `:4714-4723`.** The group draws a turnout from the members' averaged band and gives that absolute value to each member. k = shock / reference_member then differs by member and erases the members' turnout differences. The comment above the block says "one RATIO for the group".
- No emitted spec has a tie [run].
- **Severity: latent.**
- **Fix.** Draw one ratio and apply it to each member's own reference.

### D13. The level pattern is computed twice
- **[code].** `turnout.py:429-446` writes `turnout_<T>_level`, normalised on previous-NPE registration, and `export_interactive.py:193-196` reads it with the year hardcoded (`turnout_2026_level`). `montecarlo.run_model` (`:6899`, `:6933-6936`) ignores that column and rescales the raw `turnout_<prevLGE>` on the target roll.
- **Severity: low.** The interactive and the model may show different level patterns.
- **Fix.** One definition, imported by both.

### D14. Smaller register defects
- **§A32.** "Now" says the one-prior-election case is 2011, not 2016. "Record" still says "This is every 2016 target." The entry contradicts itself.
- **§A49.** 47 VDs (1.98% of the Johannesburg 2026 roll) take the city mean, recorded per run. At Johannesburg 2016, 132 VDs have no projection; I did not compute their roll share.
- **§B5** cites `montecarlo.py:_tri_ppf`. The copula lives in `correlated_triangular`.

---

## 4. The questions, answered directly

- **a. Are the two forecasts consistent?** No; see D2.
  - The VD projection (NPE × λ̂, max-ballot cast) sets every district's total.
  - The pool band (last-LGE ecological rate, PR valid) sets only the within-district pool ratios and the shock denominator.
  - Where they disagree, the district total is the projection and the pool ratios are the band's. `turnout_scale` and `districts_carry` record the gap: Johannesburg 2016 scale 0.914; Mangaung 2021 0.852.
  - Ratios survive, so shares barely move. The citywide level of either forecast does not reach shares (§2).
- **b. §V6.** Johannesburg 2026: DA −0.28 points, ANC +0.19, PA −0.10; DA −0.6 seats; P(ANC largest alone) +2.8 points. The sign is set by whether each pool's 2021 turnout was below or above 50% under a logit-symmetric band drawn as a linear-scale triangular. It is an artefact of the band's shape. The record's realised differential has the opposite sign at 18 of 24 city-years. See D1.
- **c. Pool turnouts.**
  - Estimated as one bounded-least-squares rate per pool across wards, with wards rescaled to the observed totals (`pools._nnls`, `_nest`).
  - No uncertainty is computed or carried, apart from what panel-wide movement of these same point estimates contributes to band width. Estimation noise inflates that movement partly, and bias does not show in it.
  - Some rates are identification failures (Buffalo City, Tshwane Indian/Asian).
- **d. §V3.** Nothing is measured. The same assumption (pool ratios fixed within a ward, one citywide rate per pool) is built into `pool_counts`' estimator. The application is therefore consistent with the estimate, and that consistency is not evidence.
- **e.** Held fixed in `district_votes`, `pool_spec_centres` and `reweight.turnout_tilt`. See D6.
- **f.** See D7 (θ), D8 (width record), D2 (2024 NPE feeds only the level and the VD pattern, never the pool ratios), D11 (MEC7 and definitions), §A49 fallback VDs, D10 clipping. The 2024 national turnout reaches 2026 only through T_2024 × λ̂. It sets the citywide level, which does not reach shares, and the VD pattern, which places the map at reference weights.

## 5. Owner-level summary

| defect (short name) | moves published means? | size (Johannesburg 2026; [run] or [doc]) | severity |
|---|---|---|---|
| D1 skew artefact | yes | DA −0.28 pts, −0.6 seats; P(ANC largest) +2.8 pts [run] | high |
| D4 mechanism wrong-signed given true turnout | width and scenarios | list MAE +0.48 with counted turnout [doc §1.317]; DA sd +0.42 pts [run] | medium / high for scenarios |
| D3 band narrower than its record | width | 13/24 citywide, 15/24 differential inside a 90% interval [run] | medium |
| D6/D7 preference fixed; θ double count | via D4 | unresolved; measurement named in §1.317 | medium |
| D8 width record uses a second mechanism | width | unmeasured | medium |
| D2 two forecasts | barely | scale 0.85-1.00; ratios preserved [run] | low (medium if turnout is published) |
| D5 IPF non-convergence | no (exact at reference) | worst row 0.047 vs register 6e-4 [run] | low + register |
| D9-D14 | no | see items | low |
