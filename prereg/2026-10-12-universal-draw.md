# Pre-registration: paired streams, the universal draw (v4-L1), the small-party centre correction, the level-shrink arm and the census hold

Written 2026-10-12 at `3f2f1bb` on `remediation`, before any step-5 code
exists (`audits/2026-10-11-model-round/PLAN.md`, step 4). Not to be edited
after the first arm runs; it is scored as written, including what it
falsifies. An amendment is allowed only before any arm runs, dated, appended
at the end, in the form `prereg/2026-10-10-model-correction-batch.md` used.

## Summary in plain language

The model's random draw is being rebuilt in four pieces, applied one after
another by a single writer:

1. **Paired randomness.** Each party, pool and ward gets its own random
   stream, so two versions of the model run on the same seed see the same
   luck. Differences between versions then measure the change, not the dice.
   This must leave every party's spread exactly as it was.
2. **One spread rule for every party.** How wide a party's draw is comes from
   one smooth curve over party size, fitted to every party in every metro and
   every past election, with one extra term for parties new to a city. The
   systematic error in small parties' centres is measured but not put into the
   spread (option L1).
3. **A trial correction of small parties' centres** by that measured error,
   fitted only on elections before the one being predicted.
4. **Census:** the registration cap is removed, and a population group the
   wards cannot tell apart (reaching under 25% of every ward) is held at the
   city's own registration rate.

The design work predicts that piece 2 makes simulated elections look more
like real ones (fewer draws outside anything the record has shown on two or
more measures; far fewer small parties exploding to 5%), without scoring worse
on the ANC and DA. It also predicts what will still fail: too few small
parties climbing past 1%, the middle-party rule, and a wide draw for MK. Piece
3 is predicted **not** to help on the backtests, because the record's
small-party centre error changes sign between elections. Piece 4 is predicted
to change nothing at Johannesburg and to move Cape Town's and Mangaung's
Indian/Asian pools.

Every test is scored against real results of the 16 city-years of 2016 and
2021. The 2011 elections cannot be tested: the width record behind a 2011
forecast would have to come from elections before 2011, and there are none in
the record.

Three kinds of evidence are labelled where used: **measured** (a script
printed it, with its source), **read** (a file or the code says it),
**argued** (neither).

---

## 1. Measured before this was written

One computation, made for this document. Arithmetic only: no model run, no
emit, nothing written under `data/`.

**The centre correction at Johannesburg 2026, as arithmetic on a stale
vector.** Input: `data/arms/step11/E/joburg-2026/trace/30_centres.json`
`after_shrink`, normalised to sum 1 (arm E's centres, from the pre-round
specs). Each party below 20% multiplied by `exp(m(s))`, with
`m(s) = c1·L + c2·L²`, `L = min(log(s/0.20), 0)`, `s` clamped below at 0.016%,
and the 2026-record coefficients of v4 §1.1 (full record c1 +0.342,
c2 +0.075; without COPE and ActionSA +0.352, +0.076); then renormalised.

| party | centre before (% of list) | after, full fit | after, without COPE and ActionSA | m(s) at the centre, full fit |
|---|---|---|---|---|
| DA | 25.98 | 27.80 | 27.95 | 0 |
| ANC | 23.74 | 25.40 | 25.54 | 0 |
| ASA | 11.66 | 10.60 | 10.61 | −0.163 |
| EFF | 10.95 | 9.80 | 9.80 | −0.179 |
| MK | 9.09 | 7.78 | 7.76 | −0.223 |
| PA | 5.82 | 4.58 | 4.55 | −0.308 |
| RISE | 1.82 | 1.32 | 1.30 | −0.389 |
| IFP | 1.50 | 1.09 | 1.08 | −0.383 |
| 73 parties with centre < 1%, combined | 8.28 | 10.75 | 10.56 | — |
| 65 parties with centre < 0.2%, combined | 4.01 | 7.22 | 7.09 | — |

Limits, stated here: the vector is arm E's, not the step-7 specs'; the run
applies the correction to the `pool_spec` centre (which agrees with the
normalised centre to 0.02 points at this target, 1e §5.1); the IPF and the
capacity water-fill can move the result; and the backtests use forward fits
(§3.3), not this 2026 fit. These numbers size the Johannesburg 2026
prediction in §5.4 and nothing else.

Everything else quoted below was measured by the design documents of this
round, which the step-2 reviews reproduced, and is cited by section. Those
figures come from the **citywide simulation** (no IPF, no Dirichlet, no ward
or VD layer; v4 "Labels"), 1,000 draws per backtest city-year on one seed and
5,000 at Johannesburg 2026. The canonical run is the full model; where the
missing layers matter, the prediction says so.

---

## 2. The scored population and what judges it

* **Scored:** the 16 city-years of 2016 and 2021 in the eight metros
  (`compare_history.CITIES`). Each target is judged by real results only.
* **Not scored: 2011.** Its width would come from the 1b v3 fallback (v3
  addendum §3.2 row 21) because no earlier width record exists. 2011 rows are
  run and reported, labelled untestable, and enter no rule below, with one
  named exception (§5.5, the level-shrink arm, where 2011 is reported as the
  cycle 1e's mechanism lives in).
* **Johannesburg 2026:** a forecast with no result. Reported on the
  implausible-draw counts (§5.6) and the whole-vote features judged by all 32
  real transitions (1h §2.2), where level features are "beyond the local
  record" and never failures (1h §3.2 rule 4).
* **The plausibility record** for each target is the real transitions before
  it (strict mode: 2016 by 2000-2011, 2021 by 2000-2016; 1h §2.2).

---

## 3. Arms and how each is built

All arms run at one seed per city-year, the same seed in every arm, through
the keyed streams of 1c (as fixed by `step2/2-review-1c.md`). Backtests at
1,000 draws per city-year or more; Johannesburg 2026 at 5,000; the draw count
and seed are recorded in each run and equal across arms. Each arm runs
`run_model` in process with `--run-dir` traces kept; no bare `montecarlo.py`
run (CLAUDE.md §3).

**Width record: the full record.** No party is removed (owner, 2026-10-12:
nobody removed). The fit without COPE and ActionSA is not an arm; its design
figures are quoted for information. If the owner wants it as an arm, that is
an amendment before any run.

| arm | label | draw law | centres | census | code and specs |
|---|---|---|---|---|---|
| I | incumbent | today's: Student-t level shock and Dirichlet split, read from the keyed streams | as today | hold applied | final step-5 tree, final emit; the old draw law selected by a scenario switch |
| U | v4-L1 | v4 §1 width curve, one newness δ, location fitted and **not** carried in the draw (addendum §1, call 33) | as today | hold applied | final tree, final emit |
| UC | v4-L1 + centre correction | as U | every party with centre < 20% multiplied by `exp(m(s))`, `m` clamped at 0.016%, then renormalised | hold applied | final tree, final emit; scenario switch |
| US | v4-L1, `level_shrink = 0` | as U | as today with the shrink off (1e §2.5 step 1) | hold applied | final tree, final emit; scenario override |
| C0 | v4-L1 without the census change | as U | as U | **as shipped today** (`REGISTRATION_MAX`, no hold) | the commit **before** the census commit, with its own emit into an isolated worktree, run with that commit's code |

### 3.1 Why the census change is its own arm (C0), not folded

* **It cannot be switched off in the final tree.** `run_model` recomputes the
  pool geography from code at every run (`montecarlo.py` call to
  `_pools.pool_counts`, 1g §d), and `REGISTRATION_MAX` is deleted by the
  change. Saved specs run on the final code would still carry the new
  geography at run time. So the census-off arm is the whole tree before the
  census commit, with its own specs.
* **Folding would confound it with the draw on half the panel.** The hold
  touches the fits behind Cape Town, Mangaung, Ekurhuleni, Nelson Mandela Bay
  and Buffalo City targets (1g §c, reach < 25% row), roughly half of the 16
  scored city-years. Johannesburg 2026 is predicted unchanged.
* **Cost: a second emit**, an exception to "re-emit once" (CLAUDE.md §3). It
  runs in an isolated worktree into its own `data/processed`, is never copied
  into the main tree, and is finished before the canonical emit, so no
  measurement in the main tree runs while it writes.
* The writer's serial order (PLAN, step 5) puts the census change last, so
  "the commit before" contains streams, v4-L1 and the correction switch. If
  the writer's order changes, the C0 recipe is amended before any run.

### 3.2 What is paired with what

Pairing is bit-identity of the **primitives** a stage reads; drawn shares are
correlated, not identical (1c §2.6, risk 3).

| comparison | stages shared, so paired | not paired |
|---|---|---|
| U / UC / US | every stage | none, unless a party's tie or pool set differs |
| U / C0 | every stage, where the pool set and tie structure are unchanged (a held pool keeps its members) | a pool dropped or re-tied by the census change |
| I / U | `turnout.common`, `turnout.pool`, `entrant.*`, `vd_turnout.*`, `ward_noise`, and `level.z` if both laws read it | I's `level.chi` and `split`; U's `level.shared`, `level.arrival`, `calib.*` |

Every difference reported between arms carries its paired bootstrap Monte
Carlo error: one draw-index resample applied to both arms (1c review finding
7). For I against U the bootstrap is the only statement of how much pairing
survived. No difference is called "paired" without R2's measured correlation
(§6.3).

**Requirement this places on step 5:** the incumbent draw law stays
selectable by a scenario switch in the final code. Without it arm I cannot
exist and every comparison against the incumbent is against arm E, which is
unpaired.

### 3.3 The centre correction (UC), stated so it can be scored

* **Domain:** every party whose centre is below 20%, the domain where the
  joint fit defines `m(s)` (v4 §1). One rule, no party named. If the owner
  meant a narrower line, that is an amendment before any run.
* **Fit:** out of sample. The 2016 targets use `m` fitted on 2011 only; the
  2021 targets on 2011-2016; Johannesburg 2026 on 2011-2021. The same joint
  fit and fixed point as U's width; nothing is fitted to a model output.
* **Order:** after `compress_levels` (which stays at 0.35 in UC), applied to
  the `pool_spec` centre the draw conserves, before the calibration pass.
  Large parties (≥ 20%) are not multiplied; they move only through the
  renormalisation.
* **Clamp:** `s` evaluated at no less than 0.016% (review §1; addendum
  call 36).
* **Recorded:** the factor per party in the trace (`30_centres` or
  `35_widths`), and `m(s)` coefficients per target.

Classification: estimation. `m(s)` is the average size-related error of the
centres against real results of earlier elections, a property of the world
(CLAUDE.md §4), not a ratio against model output.

---

## 4. Instruments

| quantity | instrument | notes |
|---|---|---|
| whole-election features, envelope exceedance, event tests, joint `J`, randomised PIT | `src/plausibility.py` (1h §5), a step-5 deliverable | must be committed, with its four-part tests (1h §5.3), before any arm is scored; if it does not land, the 1h prototype (`plaus.py`) is committed under `audits/2026-10-11-model-round/` first and scored from there. Randomised PIT for count features, exceedance below and above separately (addendum §3.2) |
| CRPS per party | `score.crps_by_party` (fair) on `pr_share_draws` against `compare_history.actual_shares` | points of list share |
| interval on a pooled CRPS difference | `score.cluster_bootstrap`, clusters = city-years, statistic = mean over party-city-years, 90% level | the interval is evidence; the rule is the upper bound below (v2 §8.1) |
| inside the 90% band | 5th-95th percentile of the party's drawn list share contains the realised share | per party-city-year |
| seats given to the wrong party | `compare_history.coherent_seats` against `compare_history._actual_seats`; half the summed absolute error over the union of parties | the coherent statistic (1a Method), never the list-only proxy of the design tables |
| Johannesburg 2026 implausible-draw counts | 1a Part B's definitions, computed on `pr_share_draws` with previous shares from `compare_history.actual_shares` at 2021 | §5.6 |
| mean conservation | `41_guards.mean_error` (v2 §1.2) | U, UC, US, C0 |
| stream pairing | the suite tests of §6 and the trace field `41_guards.stream_keys` | |
| census pool level | `pools.pool_counts` in process, both trees | §7 |

Large parties: centre ≥ 15%, 32 party-city-years. Middle parties: centre
5-15%, 14 party-city-years (v2 §8.1). Centre = the `pool_spec` centre of arm
I, so every arm is scored on the same party sets.

---

## 5. Predictions, arm by arm

Each row: the prediction, the threshold that counts as confirmed, and
whether the failure was already predicted (addendum §3, "What still fails").
Design values are citywide-simulation figures; the full model adds IPF, VD
and ward layers, which move list shares by about 0.3% of a share (1f §4.2),
so the thresholds below are wider than the design values by that and by
Monte Carlo error at 1,000 draws.

### 5.1 Arm I, incumbent on keyed streams

Prediction: each party's distribution is unchanged from arm E's law (1c §2.1).
This is a tripwire for wiring (1c R1), never a judgement on the forecast.

| measure | design / baseline (source) | confirmed if |
|---|---|---|
| 7-feature `J ≥ 2`, share of backtest draws | 36.4% (v4 §2.1 "today") | 32-41% |
| sub-1% mass, realised inside central 90% (of 16) | 8 (addendum §3.1) | 6-10 |
| JHB 2026, established party with previous share < 1% above 5% (of 5,000 draws) | 403 (1a; v3 §8.2) | 300-500 |
| R1 KS and variance-ratio checks against the pre-change code | pass (1c R1) | the old-against-old reference passes first; then old-against-new passes |

A miss here means the stream wiring changed a distribution. Step 6 stops; no
other arm is read until it is explained.

### 5.2 Arm U, v4-L1 (the main change)

| # | measure (backtests, 16 city-years unless stated) | design value (addendum §3.1, v4-L1 full) | predicted, full model | confirmed if | already predicted to fail? |
|---|---|---|---|---|---|
| U1 | 7-feature `J ≥ 2`, share of draws | 27.5% vs 36.4% today | lower than arm I by at least 4 points | U − I ≤ −4 points, paired | no |
| U2 | expected number of elections with `J ≥ 2` against realised 4 | 4.4 | consistent with 4 | P(X ≤ 4) ≥ 0.05 and P(X ≥ 4) ≥ 0.05 | no |
| U3 | 8-feature `J ≥ 2` (with `w_top`), realised recomputed | not computed | lower than arm I | U − I < 0, paired; reported, not a rule | — |
| U4 | volatility, draws above the record | 7.5% vs 15.4% | lower than arm I | U < I | no |
| U5 | largest loss, draws above the record | 10.6% vs 20.4% | lower than arm I | U < I | no |
| U6 | sub-1% mass, realised inside central 90% (of 16) | 14 vs 8 | 12 or more | ≥ 12 | no |
| U7 | parties ≥ 1%: P(as many or more elections outside as realised) | 0.013 | below 0.05 | P < 0.05 | **yes** (addendum, item 1) |
| U8 | previously sub-1% parties reaching 1%: same test | 0.000 | below 0.05 | P < 0.05 | **yes** (addendum, item 1) |
| U9 | largest new party: expected elections outside against realised 3 | 3.4 | 2.5-4.5 | inside | no |
| U10 | large parties: mean CRPS difference U − I, 90% cluster-bootstrap upper bound | −0.159 [−0.293, −0.006] | passes | upper bound ≤ +0.05 points | no |
| U11 | large parties inside the 90% band (of 32) | 31 | 28 or more | ≥ 28 | no |
| U12 | large drawn log-sd, median 2016 / 2021 (realised RMS 0.040 / 0.114) | 0.106 / 0.106 | narrower than arm I in both years | U < I both | no |
| U13 | middle parties: mean CRPS difference, upper bound | +0.261, upper ~+0.62 | fails | upper bound > +0.05 | **yes** (addendum, item 2: the 2016 newness width from COPE 2011 applied to the EFF) |
| U14 | middle parties inside the 90% band (of 14) | 14 | 12 or more | ≥ 12 | no |
| U15 | seats given to the wrong party, summed over 2016 and 2021 (coherent) | list proxy moved −2.4 in 2021, +0.6 in 2016 | within ±5 of arm I | \|U − I\| ≤ 5 seats | no |
| U16 | 2021 large parties: under-coverage (v2 §8.3, block movement −0.063) | — | the 2021 large-party CRPS difference is the worse year | U − I larger in 2021 than in 2016 | — (reported) |

What each outcome would mean:

* **U1-U6 confirmed, U10-U11 pass:** the whole-vote claim holds on the full
  model. The draw is closer to the record and does not cost the large parties.
* **U10 fails:** the large-party gain in the simulation came from a layer the
  simulation lacks (IPF normalisation, the Dirichlet removal). The claim that
  v4-L1 is the only v4 option passing the rule (addendum, Reasons) is
  falsified.
* **U7 or U8 pass:** the full model's IPF or ward layers carry small parties
  past 1% where the simulation did not; the addendum's attribution to low
  centres is weakened, not confirmed.
* **U13 passes:** the middle-party failure was a simulation artefact; the
  COPE attribution is unsupported.
* **U2 fails low (P(X ≥ 4) < 0.05):** v4-L1 is now too narrow on the whole
  vote, which L1's dropping of the location was expected to risk for parties
  under about 3% (addendum, item 1).

### 5.3 Arm U, mechanism checks

| # | check | prediction | confirmed if |
|---|---|---|---|
| M1 | mean-conservation falsifier (v2 §1.2): per party with centre ≥ 0.1%, `z_i = (mean_d target_id/c_i − 1)/SE_i`, Bonferroni at family error 0.01 per run | quiet | at most one run of the 17 (16 backtests + JHB 2026) fires in each of U, UC, US, C0, and a re-run of a firing city-year at a second seed is quiet. Design: 0 false alarms in 20 clean runs; ×1.2 errors detected 10 of 10 (v2 §1.2) |
| M2 | the falsifier's own suite test | false alarms ≤ 1 in 20 seed pairs; an injected ×1.2 error on one party detected | as stated (v2 §9) |
| M3 | widths printed by the writer against v4 §1.1 (2026 record, full fit) | b 0.80-0.83, midpoint 8.0-9.1%, δ 0.84-0.90, c1 +0.31 to +0.36, c2 +0.07 to +0.08 | inside; outside means the fitted record or estimator differs from the design's, and step 6 explains it before any score is read |
| M4 | JHB 2026 drawn log-sd, DA / ANC / ASA / EFF / MK / PA | 0.16 / 0.16 / 0.27 / 0.30 / 0.86 / 0.58 (addendum §3.1) | each within ±0.05, MK within ±0.08 |
| M5 | the citywide width is replaced, not added to | no party's log-sd at JHB 2026 exceeds √(σ(s)² + δ²·new) by more than the composition and Monte Carlo allowance | every party within 0.05 of that bound or below |
| M6 | judgement overlay at JHB 2026 | number-neutral today: no judgements file declares `support` or `overperform` (v3 §11.2, re-check B1) | U with and without the overlay give bit-identical drawn arrays |

### 5.4 Arm UC, small-party centre correction

**Prediction: the correction does not improve the backtests.** The record
gives the reason. The forward fits put `m(0.5%)` at −0.87 (2011 record, used
for 2016) and −0.59 (2011-2016 record, used for 2021) (v4 §1.1), so UC lowers
the centres of parties around 0.3-12% at both backtest cycles. But the
cycle means of the small-party residual run −0.73 / +0.27 / +0.88 at
2011 / 2016 / 2021 (v2 §8.3): small parties realised **above** their centres
in both scored cycles. A correction fitted on earlier cycles moves them the
wrong way. The mass taken from them goes to the large block by
renormalisation, and in 2021 the large block was already over-forecast (v2
§8.3, block movement −0.063). Argued; no design measured this arm.

| # | measure, UC against U (paired) | prediction | confirmed if |
|---|---|---|---|
| C1 | CRPS, parties with centre < 5%, mean difference, 2016 and 2021 separately | worse in both | UC − U > 0 in both cycles |
| C2 | previously sub-1% parties reaching 1%: P(X ≥ obs) | still failing | P < 0.05 |
| C3 | parties ≥ 1%: P(X ≥ obs) | still failing, no better than U | P < 0.05 |
| C4 | large parties: CRPS difference UC − I, upper bound | worse than U's | UC's upper bound > U's |
| C5 | large parties, 2021 only: CRPS difference UC − U | worse | > 0 |
| C6 | JHB 2026 mean list share, DA / ANC (from §1) | +1.8 / +1.7 points against U | each between +1.0 and +2.6 |
| C7 | JHB 2026 combined mean share of parties with centre < 0.2% | 4.0% → 7.2% (§1) | rises by 1.5-4.5 points |
| C8 | JHB 2026, established party with previous share < 1% above 5% | no more than U | UC ≤ U + Monte Carlo allowance (paired) |

What each outcome would mean:

* **C1 confirmed:** the size-related bias is not stable across cycles, and a
  constant correction cannot be estimated out of sample from this record.
  `m(s)` stays information for next round's level layer, with the cycle drift
  as the obstacle.
* **C1 falsified (UC better in both cycles):** the size-related part of the
  error is stable enough to correct despite the drift in cycle means; the
  drift lives in the shared term.
* **C6 or C7 outside:** the IPF or capacity layer redistributes the
  correction; report where it went before reading anything else of UC.

### 5.5 Arm US, `level_shrink = 0`

1e's figures were computed against v3 at 1% on arm E's draws (1e §5). The
centre mechanism does not depend on the width law, so the directions carry
over; under v4 the calibration conserves the `pool_spec` centre, so the mean
change at Johannesburg 2026 equals the centre change.

| # | measure, US against U (paired) | prediction (1e §5) | confirmed if |
|---|---|---|---|
| S1 | JHB 2026 mean list share, DA / ANC | +1.78 / +1.50 | each within ±0.5 points |
| S2 | JHB 2026 combined mean share, parties with centre < 1% | falls about 2.1 points | falls 1.4-2.8 points |
| S3 | list MAE change (share-weighted, mean of 8 metros), 2016 / 2021 | +0.72 / +0.50 (worse) | both positive and within ±50% |
| S4 | seats given to the wrong party (coherent), per cycle | worse in 2016 and 2021 | a tie (0) in a cycle is reported as a tie, not agreement (1e §5.3) |
| S5 | large parties: CRPS difference US − U, upper bound | worse | upper bound > +0.05 |
| S6 | 2011, outside the scored population: list MAE change | −1.52 (better) | reported only; sign and range −2.3 to −0.8 as 1e falsifier 1 |

What it would mean: S3-S5 confirmed and S6 better says the shrink trades 2011
against 2016 and 2021, as 1e found. Key 1 cannot decide it (1e §2.4). The
result goes to the owner split by cycle.

### 5.6 Johannesburg 2026: implausible-draw counts (5,000 draws)

Definitions as 1a Part B: "established, previous < 1%" = stood at the 2021
local election with a list share above 0 and under 1%. The record: of 337
such cases, none reached 5% at the next election; two reached 2% (MODEL-LOG
§1.296).

| count (of 5,000 draws) | arm E (1a) | U design | I predicted | U predicted | UC, US predicted |
|---|---|---|---|---|---|
| a draw with an established party, previous < 1%, above 5% | 403 | 17.5 | 300-500 | ≤ 60 | ≤ U's count + 20 |
| a draw with any party of centre < 1% above 5% | 853 | 51.8 | 650-1,050 | ≤ 150 | — |
| a draw whose largest new party exceeds 18.12% (the record's largest) | 255 | 602 | 180-330 | 450-750 | — |
| 7-feature `J ≥ 2` share of draws (judged by 32 transitions) | 71.7% | 52.4% | 65-78% | 45-60% | — |

The largest-new-party count rising under U is already predicted (addendum,
item 3). It comes from the one newness δ, fitted mostly on about 200 small
arrivals and extrapolated to MK (log-sd about 0.85). The record does not call
it implausible: the realised largest new party fell outside the record's range
in 3 of 16 backtests against 3.4 expected under L1 (addendum §2). It is
disclosed, not a failure.

---

## 6. Stream pairing (1c, with the review's fixes)

Suite tests, constructed inputs, run before any arm.

### 6.1 Samplers exact (1c V1, review findings 1, 2, 5)

* Two-sample KS, N = 200,000 per side, reject at D > 0.00616.
* Slot gamma, **boosted at every shape**, against `rng.standard_gamma` at
  shapes 1e-4, 0.01, 0.1, 0.5, 0.99, 1, 1.01, 3.5, 10, 100, at J = 4 and J = 1.
* The fallback alone (J = 0, forced exhaustion) against `rng.standard_gamma`
  at shapes below and above 1.
* Student t as z/√(2G/df) at df 2.5, 4, 7, 30; the wrong constant z/√(G/df)
  must reject.
* Dirichlet per component: the vector with a member at
  `DIRICHLET_FLOOR × alpha` against `rng.dirichlet`; the vector with every
  α < 0.1 against a log-space boost-identity reference, not `rng.dirichlet`.
* Triangular from Φ(z) for three bands including a mode at an edge.
* Power rows: Gamma(1.05a) against Gamma(a) at shapes 0.01-100 must reject;
  t at 2·df against df at df 2.5, 4, 7 must reject.

### 6.2 Indexing and wiring (1c V2, review finding 6)

* `run_model` on one small real city-year at about 30 draws with
  `STREAM_CHUNK` 1, 7 and 256: every `*_draws` array byte-identical.
* `draws = 20` against `draws = 40`: the first 20 rows of `pr_share_draws`,
  `ward_winner_draws` and the seat draws identical.
* A read of an earlier draw raises; a second read with a different `k` raises.
* Two subprocesses at `PYTHONHASHSEED` 0 and 4 give identical first rows.
* `seats.stable_entropy("ANC") == 16408193524922255279`.

### 6.3 Pairing, constructed (1c V3) and on the real arms (1c R2)

* V3 arms (i)-(vi) as 1c, plus (vii): a centre change built so one pool
  member's Dirichlet shape crosses 1; its split gamma correlation exceeds
  0.99.
* V3.1 population: the compared key set equals what the spec implies, both
  directions, non-empty. V3.2 primitives bit-identical. V3.3 by capture of
  `log_shock` and `pool_split` inputs per party name.
* **V3.4 thresholds, set here as 1c asks** (argued from 1c §2.6's toy, which
  measured one normalisation only; 2,000 draws, constructed spec of two pools
  and seven parties): correlation of drawn list shares of unchanged parties,
  median ≥ 0.99 and minimum ≥ 0.95 for an added party at 0.1% and 1%; median
  ≥ 0.98 and minimum ≥ 0.93 at 5%; median ≥ 0.99 for a ×1.2 centre change.
* Tie keys by the declared label (`tie` or pool name) in both branches
  (review finding 3): a constructed arm that removes one member pool of a tie
  leaves the remaining pools' turnout primitives bit-identical.
* **R2 on the real arms**, Johannesburg 2021, Ekurhuleni 2021 and Mangaung
  2021: median over parties of the per-draw correlation of list shares,
  U/UC and U/US ≥ 0.98 at each city-year; U/C0 ≥ 0.98 where no pool is
  dropped. I/U is reported, not predicted. The paired bootstrap Monte Carlo
  error of a list-MAE difference between U and US is below 0.05 points per
  city-year, against the unpaired 0.19-0.20 of MODEL-LOG §1.296.

### 6.4 The detectors go red (1c V4 and review finding 6)

Each mutation fails the named test and the suite is green again when it is
reverted: `level` keyed by column position; `city` and `target` dropped from
the root; one key for every stage; entrant share drawn only when the gate
passes; `pool_split` replaced by `rng.dirichlet`; `stable_entropy` via
`hash()`; the stacked block drawn from one generator keyed by the `names`
tuple; the drawer ignoring the passed `d`; the boost applied only below shape
1 (must fail V3 (vii)).

### 6.5 Counted, not silent

`41_guards.gamma_fallbacks` with denominator `gamma_draws`. Predicted: under
20 fallbacks per 5,000-draw run at J = 4 (1c §2.4 estimates about 12). More
than 100 in any run is a finding about the shapes reached, reported before
any score.

---

## 7. Judgement entry and its hash (v3 §11, v3 addendum §2)

* **J1.** `support`, `overperform`, `sigma_j` and `register` are excluded from
  `_judgements_sha`: editing one leaves every spec's `artefact_key` unchanged.
  Test: edit a scratch copy, compare keys.
* **J2.** The run hashes the entries it applied (party, `support`,
  `overperform`, `sigma_j`, `register`, sorted) into `35_widths.judgements_sha`
  and the forecast artefacts' declarations. A constructed test edits `sigma_j`
  in a scratch copy; `declares.py --verify` and
  `tests/test_intermediates_are_current.py` report `~` (declared and wrong);
  both go quiet when the edit is reverted.
* **J3.** On every backtest the hash covers the empty set and
  `35_widths.judgements_ignored` lists any entry with its register row.
  Predicted at all 16 scored city-years: empty set hashed, no entry applied.
* **J4.** `make_drawer` refuses `support` or `overperform` without `sigma_j`
  and `register`; the register guard checks §J rows against entries in both
  directions.
* **J5.** Number-neutral today (M6).

A failure of any of J1-J4 blocks shipping: it is a path for a hand edit to
reach a forecast without a stale mark, or for a judgement to leak into a
backtest.

---

## 8. Census hold (1g §f; POOLS-REEMIT-QUEUE entry 31, amended)

The identification test is the reach test: a pool reaching under 25% of every
ward takes the city's own registration rate (owner, 2026-10-12, P_hold).

| # | falsifier (1g §f) | instrument | prediction | falsified if |
|---|---|---|---|---|
| K1 | an identified pool's registered split moves when its census column is scaled ×0.5 or ×1.5 | `pools.pool_counts` in process, every city-year fitted for the 16 targets | ≤ 0.10pp everywhere (1g §0: 0.10 at Johannesburg 2021, 0.06 at Cape Town 2016, unbounded) | > 0.1pp in any city-year |
| K2 | Johannesburg 2026 `registered` or `pool_shares_at_target` moves | the two trees' specs | unchanged within 0.1pp; nothing binds and nothing is held (1g run3) | > 0.5pp for any pool |
| K3 | paired backtest: net CRPS loss at the touched city-years with no change elsewhere | U against C0, `score.crps_by_party`, all parties, city-years whose fits hold a pool vs the rest | no net loss at the touched city-years beyond the paired Monte Carlo error | a net loss at touched city-years with \|change\| below Monte Carlo error at the untouched ones |
| K4 | the capacity scan gains a fatal cell in Cape Town's Indian/Asian pool | `tests/test_pool_bounds.py` capacity test | no fatal cell | any fatal cell |
| K5 | prereg 2026-09-25 P2 (the reach test makes it scorable) | `pools.pool_counts` | Cape Town Indian/Asian 2.7-2.9% of the roll at all three cycles (1g §b) | ≥ 5% at any cycle |
| K6 | Mangaung Indian/Asian registered share at every target | `pools.pool_counts` | about 0.6-0.7%, from 1.5-1.8% (1g §f) | outside 0.4-1.0% |
| K7 | the held set | the `unidentified` / `imputed["registration"]` fields | Indian/Asian only: Cape Town, Mangaung, Ekurhuleni 2006/2011, Nelson Mandela Bay 2006-2016, Buffalo City (1g §c) | a held Black African, Coloured or White pool, or a Johannesburg cell |

K1, K2, K4-K7 need no model run and are scored on the emitted trees before
any arm runs. K3 needs C0.

---

## 9. Decisions that follow

Applied in this order. "Owner" means the result goes to the owner unsplit with
the measurement, as CLAUDE.md §4.4 requires.

1. **Gates before anything is read.** §6 green; the four rows of §5.1 inside; M1-M3
   and J1-J4 pass; K1, K2, K4 hold. Any failure: nothing ships, step 6 finds
   the cause. These are tests of the code, not of the forecast.
2. **v4-L1 (U) ships as the draw** when U10 and U11 pass, U1 and U2 hold, and
   no failure appears that §5.2 did not predict. The predicted failures (U7,
   U8, U13; the largest-new-party count in §5.6) do not block: they are
   attributed in advance (ITERATING, "more honest usually ships").
3. **U does not ship** when U10 fails: worse on the large parties, and the
   design's explanation for the gain did not hold. Owner, with U's
   whole-vote rows.
4. **Owner** when U1 or U2 fails, when U15 shows more than 5 more seats given
   to the wrong party, or when any failure appears that §5.2 did not predict.
5. **UC ships in place of U** only if it passes U10's rule against I **and**
   improves on U, paired, in C1 at both cycles and in C2. Otherwise `m(s)` is
   filed as information for next round's level layer, with this result. The
   prediction is that it does not ship.
6. **US: owner**, split by cycle (1e §2.4). The default stays 0.35 until the
   owner decides.
7. **The census hold ships** when K1-K7 hold. K3 or K4 firing: owner, since
   either says the cap was carrying something §0 of 1g argued it was not.
8. **Johannesburg 2026** counts (§5.6) inform the owner's before/after view
   (PLAN, owner decision 5) and decide nothing alone.

---

## 10. Rejected claims

| claim | evidence that rejected it |
|---|---|
| Fold the census change into every arm | Its held cells sit behind about half the scored city-years (1g §c); folded, its CRPS effect cannot be separated from the draw's |
| Run the census-off arm on the final code with saved specs | `run_model` recomputes pool geography from code each run (1g §d), and the cap is deleted |
| Score against the citywide simulation's numbers | They are a different model; the full model is the measurement, the simulation sized the predictions |
| Treat I against U as fully paired | The two laws read different level and split stages (§3.2) |
| Use the list-only seat proxy for wrong-party seats | It is not the statistic `compare_history` scores (1a Method); a quantity redefined under a prediction voids it (QC §2) |
| Predict UC improves the small parties | The forward `m` is negative at 0.3-12% while the realised cycle means in 2016 and 2021 are positive (v4 §1.1, v2 §8.3) |
| Count 2011 in any rule | No earlier width record exists; its width is a fallback (v3 addendum row 21) |

---

## Amendment before any run (2026-10-12)

Appended before any step-5 code exists and before any arm runs.

1. **R1's recipe (gate 1, §5.1 last row and §9 rule 1).** The final tree's
   incumbent carries the census hold as well as the streams, and 1c R1's
   city-years include Ekurhuleni 2011 and Mangaung 2021, whose fits hold an
   Indian/Asian pool (1g §c). A KS failure there could not be attributed. R1
   is therefore two comparisons:
   * **streams alone:** the commit before the streams change against the
     first commit at which it lands, both on the incumbent law and the same
     specs on disk, at 1c R1's four city-years (Ekurhuleni 2011, Mangaung
     2021, Johannesburg 2021, Johannesburg 2026), with 1c R1's thresholds and
     its old-against-old reference run first;
   * **later commits left the old law alone:** the final tree's incumbent
     switch against that streams commit, at Johannesburg 2021 and 2026 only,
     which the census hold does not touch (1g §f; K2).
2. **§5.1's windows assume** the census hold moves arm I's pooled whole-vote
   rows by less than the window width. Only K3 checks the census effect on the
   panel; if a §5.1 row misses, K3's touched/untouched split is read before
   the miss is attributed to the streams.
3. **The width fit is the full record** (§3). The fit without COPE and
   ActionSA as an arm would be a further amendment before any run.

---

## Amendment 2, before any run (2026-10-12, step 6)

Appended after the step-6 diff review of the step-5 code and before any arm
runs. Nothing above is edited.

1. **C0's tree (§3 table, §3.1).** C0 is the FINAL tree with commit `c2edc60`
   (the census hold) reverted, not "the commit before the census commit". It
   is built in its own git worktree with `data/raw` copied in, and has its own
   re-emit, its own `group_share_record --emit` and its own
   `width_record --emit`, into that worktree's `data/processed`. Every later
   fix (streams, v4-L1, the correction switch, plausibility and the step-6
   fixes) is therefore in both C0 and U, so U − C0 is the census change alone.
   `src/arms.py` refuses C0 in a tree carrying the hold, and the other arms in
   a tree without it.
2. **US's width record (§3 table, §5.5).** US uses its own re-fitted
   width-record variant, built with `width_record.py --emit --set
   level_shrink=0`. Its comparison with U therefore measures the centre change
   and the re-fitted record together, not the centre change alone.
3. **§3.2's `level.arrival` stream** is not part of arm U: design v4 has no
   arrival factor, and the drawer reads no such stream. The U/I row of §3.2's
   table is read without it.
4. **The U1 feature set (§5.1 row 1, §5.2 U1 and U2, §5.6 row 4)** is the seven
   whole-vote features without `w_top`: `vol`, `max_gain`, `max_loss`,
   `d_enp`, `top2`, `n_ge5`, `tiny_max`, reported by `src/plausibility.py` as
   `J7_no_w_top`. U3 is the same seven plus `w_top`, reported as
   `J8_with_w_top`.
5. **The step-7 order** is the one in `POOLS-REEMIT-QUEUE.md`, "The model
   round's step 7" (backup; R1 on the pre-re-emit specs; re-emit; the two
   record emits; the C0 worktree; the post-emit checks; the arms through
   `src/arms.py`), with no edit to `montecarlo.py`, `levels.py`, `pools.py` or
   `width_record.py` between the record emits and the arms.
