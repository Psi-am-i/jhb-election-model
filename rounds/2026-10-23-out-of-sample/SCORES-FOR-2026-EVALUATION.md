# The in-sample scores and the 2026 forecast: what is sound

> ⛔ **Every backtest figure dated before 2026-10-23 is in-sample and is not evidence of forecast accuracy** (MODEL-LOG §1.333). Figures from the quarantine copy below are quoted as fit diagnostics, each labelled in-sample.

**Date:** 2026-10-23
**Standpoint:** election forecaster and survey methodologist (the `pollster` skill). Read-only. No model run, test or sweep. The only computation was reading two JSON files and aggregating them (`width_record.json` in `data/processed/`, and `history.json` in the quarantine copy).

**The owner's point, verbatim:**

> For predicting 2026 scores should include 2021, so these scores are possibly useful. I need an evaluation with a review on that.

**Evidence read:** `POLLSTER-ON-RECORD.md`, `PLAN.md`, `PLAN-REVIEW.md`, `INVENTORY.md`; `src/backtest.py` (the four registers); `src/montecarlo.py` (`DEFAULTS`, `TURNOUT_CORRELATION`, `compress_levels`, `pool_spec_centres`, `width_record_variant`, the generic-entrant gate near line 6507); `src/levels.py` (`SPINE_K`); `src/width_record.py` (docstring, `FORWARD`, `case_for`, `build`); `tests/test_levers_are_live.py` (the `real_contestation_lists` gate); `data/processed/pools_2026.json` (`seeds`, `roster_source`); `data/processed/width_record.json`; MODEL-LOG §1.44 (as quoted in the `compress_levels` docstring and `POLLSTER-ON-RECORD.md`), §1.326, §1.333; `JUDGEMENT-CALLS.md` §A59; the quarantine `README.md`, `ORIGINALS.txt`, `remove-originals.sh` and `data/processed/history.json`.

**Three kinds of statement are kept apart:**

- **Measured here**: read or computed this session from a named file, and labelled with the file, its generation date and its population.
- **Quoted**: a figure from a MODEL-LOG section, a docstring or a register, with its location.
- **Argued**: reasoning without a measurement behind it. Each one names the measurement that would settle it.

---

## Summary

1. **Settings.** Every setting the 2026 forecast reads was chosen on data from before 2026, so none of them leaks into the 2026 forecast. Using 2021 to set them is correct, as the owner says. Leakage is not the 2026 problem. Selection optimism is: a value picked by minimising a score on the 2011–2021 panel, or kept because it scored best there, will on average help less in 2026 than it helped on that panel. This applies to the level shrink and its scale and to spine k across cycles (both picked by a score), to the by-election weight (declared by the owner, then confirmed on 2021), and to the structural choices (the draw law, the newcomer width). It does not apply to the turnout correlation, which estimates a property of the world. Three settings in the owner's list do not reach the Johannesburg 2026 forecast at all.
2. **The in-sample scores.** They cannot estimate 2026 accuracy, because 2026 is a cycle the fit has not seen, and the in-sample score measures fit to cycles it has seen. Some uses are sound: as a catalogue of where the model fails even after tuning; in-sample under-coverage read as a lower bound on out-of-sample under-coverage, in expectation; and as the in-sample side of a measured optimism gap. Unsound uses: any accuracy, coverage or margin-over-baseline claim for 2026, and treating in-sample over-coverage as evidence that the bands are too wide.
3. **Quarantined files.** The 2026 forecast reads none of them. `history.json` is the only existing in-sample baseline on the 24 city-years. The arm outputs record how many alternatives were tried for each decision, which plan step 3.6 needs. Neither should be deleted before the forward-chained run exists. The remaining files can be regenerated or are superseded.
4. **A sound evaluation before 31 October.** Three parts, in order of value. (a) Rebuild the 2026 width record from forward-chained residuals; this is estimation, not tuning. (b) Run the eight 2021 rows with settings refitted on data up to 2016, against a baseline regenerated on a clean tree; the gap is the measured optimism for one cycle. (c) Do the same for the 2016 rows if time allows. The structural selection can be measured only by the 4 November result.

---

## 1. Setting by setting, for the 2026 forecast

### Two different questions

- **Leak**: did the setting read anything at or after the target? For 2026 the answer is no for every setting. Each was chosen in 2026 on elections up to 2021 and on by-elections up to June 2026, before the target's polling day.
- **Selection optimism**: was the value chosen by minimising a score on the elections the model is judged against? If so, its in-sample gain is an overestimate of its expected gain on a new cycle (White 2000; Cawley & Talbot 2010). The chosen value is still the best available point estimate for 2026. The fault lies in treating it as known: no uncertainty about it reaches the 2026 draws, and the widths are measured around centres it shaped (§1c).

A setting that was estimated, not selected (it measures a property of the realised world, and no score enters), has sampling error but no selection optimism.

### Settings that do not reach the Johannesburg 2026 forecast

| Setting | Gate | Kind of evidence |
|---|---|---|
| New-party chance 0.25, size [1%, 4%, 12%] (`entrant_prob`, `entrant_share`) | The generic `ENTRANT` slot is added only when `not named_arrivals` (`montecarlo.py`, the gate after the comment "THE GENERIC SLOT IS A STAND-IN"). `pools_2026.json` carries 46 named seeds, all above 0. | Measured here (count of `seeds`) + code read |
| Dirichlet scale 1.0 | Read only under `draw_law = "incumbent"`. `DEFAULTS["draw_law"]` is `"universal"`. | Code read |
| Slate growth 0.22 (`contestation_expand`) | `levels.projected_contestation` is used only where there are no real lists. At Johannesburg 2026 the certified ward slates come from `judgements/joburg-2026.toml` (`complete = true`). Three runs at 0.0, 0.22 and 0.5 gave one fingerprint. | Quoted: `tests/test_levers_are_live.py`, `real_contestation_lists` 2026 entry, measured 2026-09-23 |

The 2026 arrivals are sized from the record of past arrivals instead. The seed notes in `pools_2026.json` say each is "sized at the EXPECTED result for the 121 arrivals that contested about as much of a city", and the group is rescaled ×0.21 to "an arrival-total record of 2.19%". That is estimation from arrivals before 2026. It reads no score. It does carry the newcomer width δ from the width record (§1c).

### Settings that reach the 2026 forecast

| Setting (value) | Chosen on | Kind | Sound for 2026? | What would bias the 2026 forecast |
|---|---|---|---|---|
| **Turnout correlation (0.63)** | Mean off-diagonal correlation of pools' log turnout changes, over 14 metro-transitions, 2011→2016 and 2016→2021 (quoted: `montecarlo.py` comment beside `TURNOUT_CORRELATION`) | Estimation of a property of the world. No score enters. | **Yes.** Fitting it on 2021 is correct for 2026. | Sampling error only: two cycles. 2016→2021 includes the 2021 turnout fall, so the value may be specific to that cycle (argued). Bracket it with the value from the 2011→2016 transitions alone, which the forward-chained run computes anyway (§4b). |
| **Level shrink (0.35) and scale (0.04)** | Strength chosen by leave-one-city-year-out over nine city-years (Johannesburg 2016 plus the eight metros at 2021); the form and the scale chosen with all nine in view (quoted: `compress_levels` docstring; `FITTED_ON_UNINSTRUMENTED["level_shrink"]`) | A correction fitted to the model's own errors, selected on the panel | **Defensible as a point value; its 2026 effect is likely smaller than its panel effect.** | (i) Selection optimism. The form and scale were chosen with the 2021 rows in view. (ii) One cycle dominates: 8 of the 9 rows are 2021. The forward evidence is one city-year: fitted on Johannesburg 2016 alone it gives 0.375 and improved 6 of 8 metros at 2021 (quoted, §1.44, offline reconstruction, not a full run). Both 2016 and 2021 saw the largest party fall, so whether the over-forecast of the top of the ballot is structural or belongs to those cycles cannot be told apart on this panel (argued). A 2026 cycle in which the largest party holds would be biased against by the shrink. (iii) On the width record's size frame, the shrink makes the sub-20% parties' average error relative to the large block more negative. Whether that conflicts with the shrink's stated reason is unresolved (§1c, measured). |
| **Spine k (1.0)** | Leave-one-metro-out over 180 party-city-years, eight metros, "three transitions" (quoted: `levels.py` beside `SPINE_K`). Provenance unsettled (`PROVENANCE_UNSETTLED["spine_k"]`). | Selected on predictive error, cross-validated across cities | **Yes as a value.** The plateau (0.2377, 0.2358, 0.2387 at k = 0.5, 1.0, 1.5; unit not stated in the docstring) means the choice within the plateau matters little. | Its cross-validation folds are cities within cycles, so the plateau is in-sample with respect to cycles (argued). Cycles are the dependence that matters for 2026. Refitting per target in the forward chain measures this. |
| **By-election weight (0.5, every party)** | Owner's declaration 2026-10-17, kept after a grid on the eight 2021 metros fed the 2016–21 by-elections (quoted: JUDGEMENT-CALLS §A59; MODEL-LOG §1.326) | Typed, then confirmed on one cycle | **Defensible as a declared value.** It is not a measured optimum. | One cycle. Johannesburg's own minimum on that grid was at 0, rising monotonically with the weight (quoted, §1.326). The pooled least-squares slope was 0.33 (§1.326). The 0.5 rests on the other metros, so for Johannesburg the 2026 centre is pulled halfway toward its by-elections on evidence that, in Johannesburg's own 2021 test, pointed the other way (argued from quoted figures). Labelled 🔴 in §A59 already. The register entry `NOT_FITTED["w_bye"]` says the weight is "scoreable against a local result only by the 2026 one". Since §1.325–§1.326 scored it off-panel on 2021, that phrase is out of date (its gate reasoning for the default backtest run still holds). |
| **Draw law (universal) and newcomer width by anchor class** | Chosen by comparing arms on the 24 city-years (step-7 arms; MODEL-LOG §1.314, §1.316) | Structural selection | **The best available choice; no per-target refit removes the selection.** | Model-structure selection made with all rows in view, plus more than two hundred iterations judged on the panel (`POLLSTER-ON-RECORD.md`, "The selection no per-setting fix removes"). Only the 4 November result measures this. Re-choosing the law inside the chain before the freeze is not recommended: it cannot finish in time, and it would change the live forecast on a measurement still in progress. |
| **Ward noise sd (0.10), level floor (1e-6)** | Typed at audit; kept because headlines were stable (quoted: `DEFAULTS` comments) | Typed, then confirmed | Yes. Low stakes. | Unbounded (ward noise, JUDGEMENT-CALLS §A38). Bracket it in the forward run; do not fit it. |
| **Polls off** | Owner design decision, pre-registered before both arms ran (quoted: §1.225) | Mechanism/design | Yes | None from selection. |
| **Census 2022 composition** | Census taken 2022 | Ex-post covariate at every past target; **a pre-target covariate at 2026** | **Yes.** For 2026 it is four years old, an ordinary input. | None for 2026. Its exception status concerns the backtest only (`POLLSTER-ON-RECORD.md` §1). |

### 1c. Where the bias does reach 2026: the width record

The live forecast takes every party's width from `width_record.json`, target 2026, fitted on residuals at 2011, 2016 and 2021 (`width_record.FORWARD["2026"]`). This is not a leak. The residual is the realised share against `pool_spec_centres`, and those centres are computed under `DEFAULTS` (`case_for` → `drawer_inputs` → `run_model(..., stop_after="drawer_inputs")`). So the 2021 residuals are measured around centres produced with a level shrink, a spine k and a turnout correlation that were chosen with 2021 in view. Residuals around centres tuned on those same elections are smaller, in expectation, than the 2026 forecast's own errors will be. That is the textbook route by which in-sample fitting narrows a forecast's bands (argued; standard).

**Measured here: how much the shrink moves the 2026 widths.** `width_record.json` (generated 2026-10-21T09:31:22Z) holds three variants. Width σ is the standard deviation of a party's log share (natural log): relative to the large block for a party whose centre is below 20% (`WIDTH_BLOCK`), and within the block for a member of it, so the 25% row is a within-block width. It comes from the record's curve σ(s) = a + (b − a)/(1 + exp(k(log s − log s_mid))). Values at the 2026 target, fitted on 2011–2021, 589–590 residual rows from 237 party-elections:

| party's centre share | σ, shrink 0 | σ, shrink 0.35 / scale 0.04 (live) | σ, shrink 0.35 / scale 0.4 |
|---|---|---|---|
| 0.5% | 0.810 | 0.813 | 0.812 |
| 2% | 0.780 | 0.797 | 0.795 |
| 5% | 0.614 | 0.661 | 0.662 |
| 10% | 0.323 | 0.346 | 0.352 |
| 25% | 0.083 | 0.076 | 0.080 |

The shrink narrows the width of parties at about 25% by 0.007 in σ, and widens parties at 2–10% by 0.017 to 0.047. **For the shrink alone, then, the 2026 bands are not uniformly too narrow.** They are narrower at the top and wider in the middle than with no shrink. The variants say nothing about the turnout correlation, spine k, the by-election weight or the structural selection, because none of those has a variant in the file.

**Measured here: the location curve against the shrink's stated reason.** The record also fits a location m(s): the average log error, by size, of a sub-20% party's realised share relative to the large block, **after the fixed point has removed the draw's own model-internal location** (`fit_target` re-fits on residuals less `location_shift`'s Δ, stored per row as `delta_shift`; the stored `location` is the post-fixed-point fit). It is recorded and not carried in the draw (design L1). At the 2026 target:

| centre share | m(s), shrink 0 | m(s), shrink 0.35 / 0.04 (live) |
|---|---|---|
| 0.5% | +0.041 | −0.233 |
| 2% | −0.165 | −0.387 |
| 5% | −0.175 | −0.329 |
| 10% | −0.116 | −0.201 |

Negative means that on 2011–2021, parties of that size realised less, relative to the large block, than their centres said. Turning the shrink on makes this more negative at every size shown. In this frame, the renormalisation moves mass toward the sub-20% parties that were already over-centred against the block. The shrink's docstring states the opposite fault, on rank bands over nine city-years: ranks 1–3 over-forecast by +32.30 points summed and ranks 4–12 under by −36.20 points (quoted). The two use different populations (size by centre in the record, rank by result in the docstring) and a different frame (relative to the block, against absolute points). They need not contradict. New parties are one candidate: the size frame mixes them with established ones, and ActionSA in 2021 and the EFF in 2016 sit in ranks 4–12. **This is unresolved.** The measurement that would separate the explanations is the location fitted on established rows only, with and without the shrink. Until it exists, the claim that the shrink fixes a vector "whose spread is too wide" is argued for the size frame, not measured.

---

## 2. What the in-sample scores can still tell us about 2026

### The direction rule

Fitting can only bring in-sample errors closer to the outcomes. So, **in expectation**:

- in-sample error is a lower bound on out-of-sample error, and in-sample skill an upper bound on out-of-sample skill;
- **in-sample under-coverage is a lower bound on out-of-sample under-coverage**: a band too narrow on elections it was tuned to will be at least as narrow on an unseen one;
- **in-sample over-coverage says nothing** about out-of-sample coverage: the gap could close or flip once the tuning no longer helps.

These hold on average across cycles. 2026 is one cycle and can score better than the in-sample panel by luck, so none of them bounds 2026's realised score.

### Measured here: in-sample coverage and PIT on the 24 city-years

Source: quarantine copy of `data/processed/history.json`, generated 2026-10-19T07:52:44Z, git commit `a9754ed` with `git_dirty: true`, 1000 draws, seed 20261104, universal draw, level shrink 0.35, newcomer width by anchor class. Population: each record's `calibration.reference` set, a party-row per party in the reference set, off-ballot rows included, bands by the record's own rank labels. `hits` is read as [50%, 80%, 90%], which matches the `coverage` summary at 2011 (0.659 / 0.819 / 0.855 from both). Rows within a city-year are not independent, and the eight metros within a cycle share one national swing. The effective sample is closer to three cycles than to the row counts. **The provenance is mixed.** The centres are in-sample at every row. The widths at 2016 and 2021 come from the record's forward fit (2016 from 2011; 2021 from 2011–2016), measured about in-sample centres. The 2011 widths are the fallback. So these are forward widths around tuned centres. That makes the direction rule apply with more force, because the centres are the in-sample part.

Share of the realised list share inside the central interval:

| cycle | rank band | party-rows | inside 50% | inside 80% | inside 90% |
|---|---|---|---|---|---|
| 2011 | 1–3 | 24 | 0.25 | 0.67 | 0.79 |
| 2011 | 4–12 | 60 | 0.58 | 0.75 | 0.78 |
| 2011 | 13+ | 29 | 0.90 | 0.97 | 0.97 |
| 2016 | 1–3 | 24 | 0.83 | 1.00 | 1.00 |
| 2016 | 4–12 | 60 | 0.80 | 0.92 | 0.92 |
| 2016 | 13+ | 46 | 1.00 | 1.00 | 1.00 |
| 2021 | 1–3 | 24 | 0.50 | 0.83 | 0.96 |
| 2021 | 4–12 | 68 | 0.54 | 0.79 | 0.79 |
| 2021 | 13+ | 135 | 0.91 | 0.99 | 1.00 |
| all | all, incl. off-ballot | 514 | 0.77 | 0.90 | 0.92 |

PIT (the forecast's probability below the realised share; 0.5 is unbiased), ranks 4–12 at 2021: mean 0.724 over 68 party-rows, with 0.206 of them above 0.95. Ranks 1–3 at 2021: mean 0.373 over 24.

Under the direction rule:

- **Ranks 4–12 at 2021 are under-covered in-sample** (0.79 inside the 90% interval), with PIT showing the cause: the middle of the ballot was under-forecast in level, even after the shrink and with settings tuned on 2021. This is a sound fit diagnostic. Out of sample, that class should be expected to be under-covered at least as badly. It is a level finding (PIT piled near 1), not a width finding, and it bears on the 2026 forecast's mid-ranked parties.
- **The 2011 rows are under-covered at ranks 1–3 and 4–12** (0.79 and 0.78 inside 90%). Ranks 13+ at 2011 are not (0.97). Their widths are the untestable fallback (`width_record.py` docstring), so this is evidence against the fallback width. It carries little for 2026, which does not use the fallback.
- **Ranks 13+ (0.99–1.00 inside 80%) and 2016 generally are over-covered in-sample.** By the direction rule, this is not evidence that the 2026 bands are too wide.
- **PLAN step 0.7 and the forecast page say the widths are "likely too narrow".** The evidence above supports that for mid-ranked parties and does not establish it for the forecast as a whole. Overall in-sample coverage is 0.77 inside the 50% interval, which is over-coverage at the centre.

**Provenance limit.** `history.json` was produced on a dirty tree at `a9754ed` on 2026-10-19, before the changes recorded in MODEL-LOG §1.325–§1.332 and before the 21 October width record. It describes a model close to the live one, not the live one. That is enough for the diagnostics above. It is not enough to serve as the in-sample side of an optimism gap (§4b).

### Uses of the in-sample scores

| Use | Sound? | Why |
|---|---|---|
| Accuracy, coverage or "beats uniform swing" claims for 2026 | **No** | 2026 is an unseen cycle; the score measures fit to seen ones. Against uniform swing, which fits nothing, the margin is overstated specifically (`POLLSTER-ON-RECORD.md`). |
| A catalogue of where the model fails even after tuning (classes, cycles, cities) | **Yes** | A failure that survives tuning is real. The ranks 4–12 level miss at 2021 is one. |
| An upper bound on skill | **Yes, in expectation only** | Not a bound on the realised 2026 score. |
| Comparing two settings or arms on the panel | **Biased toward the incumbent configuration** | The other settings were tuned while the incumbent arm was in place, so the panel favours it. A comparison of two arms that differ only in a choice made on mechanism grounds (polls off, pre-registered) is the least biased kind, but it still sits on tuned centres. Use only as a screen to be confirmed forward. |
| The width record as "the realised dispersion of the vote" | **Partly** | At 2026 it is fitted on pre-2026 cycles (sound), but around centres tuned on those cycles, so it measures in-sample residual dispersion. §4a replaces it with the forward version. |
| The in-sample side of a measured optimism gap | **Yes, regenerated on a clean tree** | See §4b. |

---

## 3. The quarantined files

The 2026 forecast reads none of them. The live run reads `data/processed/seat_draws.csv`, `ward_winner_probs.csv`, `width_record.json`, `regime_*` and `pools_2026.json` at the top level. The quarantined seat draws are per past target (`joburg/2016`, `joburg/2021`, `capetown/2021`), and `tests/test_quarantine.py` forbids any reference to the folder. The axis below is whether each file is needed for the out-of-sample work and whether it can be regenerated.

| Group (from the quarantine `README.md`) | Files | Needed for 2026? | Useful for the out-of-sample work? | Recommendation |
|---|---|---|---|---|
| `history.json`, `history.md` | 2 | No | **Yes.** The only existing run of a near-current model on all 24 city-years, with per-row `constants_read`, `contaminated` and `scenario_defaults`. The in-sample comparator until a clean-tree baseline exists. | **Keep** until the clean-tree baseline (§4b) and the forward run both exist. |
| `reports/model-changes/*/backtest.json` | 7 | No | Yes, as the record of what each published report said, which the corrections convention needs | Keep (already in git history; see below) |
| Arm outputs, step 7 (`I`, `U`, `US`, `UC`, `C0`) and step 11 (`A`–`E`, `B0`/`B6`/`B8`, `C16`, `D0`), their `compare_*`, `describe_*`, `measures.json`, plausibility verdicts | 1,680 + 3,791 + 10 + 1 + 5 | No | **Yes, as a count.** They record the alternatives tried for the draw-law and newcomer decisions. Plan step 3.6 requires that count beside each score (White 2000). `US` is the in-sample shrink-off arm under the universal draw. | **Keep the `result.json`, compare, describe, measures and plausibility files.** The `arrays.npz` and `trace/` bulk can go once the count is taken, if space matters. The whole folder is 225,843,991 bytes. |
| Past targets' `seat_draws.csv`, `ward_winner_probs.csv`, `coalition_*.csv` | 16 | No | Little. Regenerable by `compare_history`, and superseded by any new run | Can be deleted |
| `validation_2021.json` | 1 | No | Little; its numbers are in `history.json` and MODEL-LOG | Can be deleted |
| `sweep.json`, `width_budget.json` | 2 | No | `sweep.json`: part of the alternatives-tried count. `width_budget.json`: the ablation behind MODEL-LOG §1.48, useful when designing §4a | Keep both (24 KB) until the count is taken |

**Deleting the folder does not give "zero chance they are read".**

- The nine tracked originals (`history.json`, `history.md` and the seven `backtest.json`) remain in git history, whatever happens to the copy.
- The untracked originals of `sweep.json`, `width_budget.json` and `validation_2021.json` are still in `data/processed/`: `ls` this session found all three, while `history.json` there is gone. MODEL-LOG §1.333 says their removal waits for the owner to run `remove-originals.sh`.
- The guard against reading them is `tests/test_quarantine.py` plus the labelling rule, not the deletion.

---

## 4. A sound evaluation of the 2026 settings, within the data held

The rule throughout (CLAUDE.md §4): **fit to the dispersion of real results about forward centres (estimation), never to coverage, PIT or a realised-over-predicted ratio (tuning).** Each part is pre-registered under `prereg/` before it runs, one heavy process at a time.

### 4a. The 2026 width record from forward-chained residuals (largest effect on the live forecast)

**What.** Rebuild the 2026 target's record on residuals where each cycle's centres were computed with settings fitted strictly before that cycle:

- 2011 centres with the declared settings (shrink 0, k declared, turnout correlation declared and bracketed);
- 2016 centres with settings fitted on rows up to 2011;
- 2021 centres with settings fitted on rows up to 2016.

The likelihood, curve form and fixed point stay as they are. Only the centres change. Build with `width_record.py --out DIR`, outside `data/` (memory note: `--emit --out` writes `data/`).

**Why it is sound.** It is the same estimator, fed residuals that look like the 2026 forecast's own situation: centres from settings that have not seen the cycle being measured. That is estimation of the world's dispersion about a forward centre, not tuning.

**What it measures.** The σ curve and δ against the live record (table in §1c) give the measured width optimism for 2026, at each size, in σ of log share. If the forward σ is wider, the live bands are too narrow by that amount. If not, PLAN 0.7's sentence is withdrawn.

**What it does not do.** The draw law and the newcomer classes stay as chosen. The structural selection stays inside the record.

**Decision needed.** Adopting the forward record for the frozen forecast moves forecast numbers before the freeze. It needs the owner's yes, and it is the kind of change an ultra review is for (CLAUDE.md §4: the owner decides whether to spend one). The alternative is to freeze on the live record and publish the forward record beside it, labelled.

### 4b. Forward-chained 2021 rows: the measured optimism, one cycle

1. **Baseline, in-sample, clean tree.** Run the eight 2021 rows on the current committed tree at current `DEFAULTS`, 1000 draws, seed 20261104, into a directory outside `data/`. This replaces the dirty-tree `history.json` as the in-sample side, so that the two arms differ only in their settings.
2. **Forward arm, nested.** The same eight rows, with settings built in cycle order so that no centre is produced by a setting that saw its own cycle:
   - **2011 settings (declared):** shrink 0, k declared at 1.0, turnout correlation declared and bracketed.
   - **2016 settings, from data up to 2011:** turnout correlation on the 2006→2011 transitions where comparable (else declared); spine k on transitions ending at or before 2011. The 2016 rows are then run with **shrink 0** under these settings, and the shrink strength and scale are fitted to those unshrunk 2016 centres against the 2016 results, as §1.44 fitted on unshrunk centres. The form is held, because re-choosing it is structure. The fitted pair is a 2021 setting; it is not applied back to the 2016 rows.
   - **2021 settings, from data up to 2016:** turnout correlation on the 2011→2016 transitions; spine k on transitions ending at or before 2016; the shrink pair from the previous step.
   - **The 2021 width record** from 2011 residuals about centres under the 2011 settings, and 2016 residuals about centres under the 2016 settings (each with the shrink in force at that cycle, which is 0 at both). PLAN-REVIEW item 21 requires this rebuild. A single 2021 setting applied to both earlier cycles would leave the 2016 centres in-sample for 2016, and is not this arm.
3. **Score both** on votes (list-vote error, CRPS) and seats (seats given to the wrong party), with coverage and PIT by rank band. Score against uniform swing and persistence, which fit nothing.
4. **The gap**, baseline minus forward, is the measured optimism of these constants for one cycle. The forward score is the honest estimate of how this method does when fitted on everything before the target, which is the 2026 forecast's situation.

Its limits, stated at the claim:

- eight rows of one national swing, so a single draw of a cycle;
- the 2011-row settings inside the fit are declared, not fitted;
- the forward score is still an upper bound on skill, because the structure was selected on these rows;
- the 2026 forecast reads inputs that no 2021 row tests in the default run: by-elections at weight 0.5 (absent at past targets, `GATES['bye_deltas_absent']`), the September 2026 roll, the named-arrival seeds, and the owner's ActionSA centre (§1.330). For parity on by-elections, PLAN-REVIEW's condition applies: `bye_value.py` made target-aware first, or the weight declared.

### 4c. Forward-chained 2016 rows (if time allows)

Settings fitted on the 2011 rows only, with the 2016 width record from 2011 residuals. This is thinner: one earlier cycle, whose own settings are declared. It gives a second cycle's gap. Two cycles of gap are the minimum before an optimism figure is quoted as typical rather than as one cycle's.

### 4d. Settled only by 4 November

The structural selection (draw law, newcomer classes, the iterations judged on the panel) can be measured only by the sealed forecast: freeze, publish a dated hash, and score the frozen forecast against the certified result whatever it shows (`POLLSTER-ON-RECORD.md` §3; PLAN 5.1).

### Order before 31 October

| Order | Work | Changes the live forecast? |
|---|---|---|
| 1 | Pre-register 4a and 4b together | No |
| 2 | 4b step 1 (clean baseline, 2021 rows) | No |
| 3 | The nested refits (2016 settings from data up to 2011, 2021 settings from data up to 2016); 4b step 2 including its 2021 width record | No |
| 4 | 4a (the 2026 record from forward residuals) | Only if the owner adopts it |
| 5 | Old and new side by side on one page, never called out-of-sample, with the remaining in-sample items listed | No |
| 6 | 4c if time remains; otherwise after 4 November | No |

If 3 or 4 cannot finish before the freeze, freeze on the live record, publish the withdrawal and the hash, and run 4a–4c afterwards as the first steps of plan step 3.

---

## Claims considered and rejected

| Claim | Why rejected | Evidence |
|---|---|---|
| Because the 2026 settings rightly include 2021, the in-sample 2021 score estimates 2026 accuracy | The 2026 forecast is scored on a cycle the fit has not seen. The in-sample score measures fit to a cycle it has. The 2026 analogue is the forward-chained score (§4b). | Direction rule, §2 |
| The width record leaks into the 2026 forecast | Every cycle it reads is before 2026. The fault is optimism through tuned centres, not leakage. | `width_record.FORWARD["2026"]`; PLAN-REVIEW rejected-claims table |
| The 2026 bands are too narrow throughout | The shrink alone narrows the top (σ 0.083 → 0.076 at 25%) and widens 2–10% parties (0.780 → 0.797 at 2%, 0.614 → 0.661 at 5%). In-sample coverage is 0.77 inside the 50% interval overall. Under-coverage is measured for ranks 4–12 at 2021 only. | `width_record.json` variants; quarantine `history.json`; §1c, §2 |
| In-sample over-coverage of ranks 13+ shows the 2026 bands are too wide for small parties | Over-coverage in-sample carries no out-of-sample implication. | Direction rule, §2 |
| The new-party chance and size bias the Johannesburg 2026 forecast | The generic slot is not added when arrivals are named, and 46 are named. | `montecarlo.py` gate; `pools_2026.json` `seeds` |
| The Dirichlet scale or the slate growth bias the 2026 forecast | Unread under the universal draw; inert under the certified ward slates (one fingerprint across 0.0, 0.22 and 0.5) | `DEFAULTS["draw_law"]`; `test_levers_are_live.py` 2026 entry |
| The turnout correlation, being fitted on 2021, is biased for 2026 | It estimates a property of realised turnout; no score enters. Its limit is two cycles of sampling error. | `montecarlo.py` comment; `FITTED_ON_UNINSTRUMENTED["turnout_correlation"]` |
| Leave-one-metro-out (spine k; by-election weight) is out-of-sample evidence for 2026 | The folds are cities within a cycle, and the metros share a cycle's swing. Folds must be blocked by cycle. | `POLLSTER-ON-RECORD.md` §1; §1.326 instrument 2 |
| Forward-chained 2021 rows give 2026's skill | They give the skill of the method with its constants fitted forward. The structure was selected on those rows, and 2026 reads inputs those rows do not (by-elections, the 2026 roll, named seeds, the ActionSA call). | §4b limits |
| Deleting the quarantine folder gives zero chance the scores are read | Tracked originals remain in git history; three untracked originals remain in `data/processed/` | `ls` this session; MODEL-LOG §1.333 |
| The by-election weight 0.5 is scoreable only against 2026 | It was scored off-panel on 2021 with the 2016–21 by-elections. Johannesburg's own minimum there was at 0. | MODEL-LOG §1.325–§1.326; `NOT_FITTED["w_bye"]` |
| The shrink is shown to correct a share vector whose spread is too wide | Measured on rank bands over nine city-years. On the width record's size frame, the shrink makes sub-20% parties' average error relative to the block more negative (m at 2%: −0.165 → −0.387). Unresolved until the location is fitted on established rows only. | `compress_levels` docstring; `width_record.json` location; §1c |

## Sources

As in `POLLSTER-ON-RECORD.md`, with the confidence given there: White (2000) and Cawley & Talbot (2010) on selection optimism; Tashman (2000) and Hyndman & Athanasopoulos (2021) on rolling-origin evaluation; Roberts et al. (2017) on blocking folds by the dependence. Not in that list: Gneiting, T., Balabdaoui, F. & Raftery, A.E. (2007), Probabilistic forecasts, calibration and sharpness, *JRSS B* 69(2), on calibration before sharpness (confidence high).
