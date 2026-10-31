# DRAFT pre-registration: Step 4 stop gap (settings from earlier elections, per target)

> **DRAFT. Not committed under `prereg/`. To be reviewed blind before any fit or run.** After review it is copied to `prereg/2026-10-2x-stopgap-rolling-settings.md`, committed, and never edited again; it is scored as written.

**Specification:** `rounds/2026-10-23-out-of-sample/stopgap/SPEC.md` (the estimators, the arms, the contamination check, the scorer).
**Plan:** `rounds/2026-10-23-out-of-sample/PLAN.md` Step 4.
**Written:** 2026-10-28, read-only, at `99556398`.

---

## 1. The question

For each backtest target T (2011, 2016, 2021), when turnout correlation, the level shrink and its scale, and spine k are set only from elections before T (declared at 2011, with new-party chance and size), and the width record is rebuilt on centres built that way, what are the fitted values, and how do the 24 rows' scores differ from the same tree run with the current settings?

The answer is a measurement of how much of the current backtest score came from those settings having seen the scored elections. It is not an out-of-sample score: every other setting, the switches and the model's structure were chosen with these rows in view (SPEC §7).

## 2. Disclosure: what the author had read before writing this

Predictions below were written with these in view. A reviewer should treat any prediction that leans on them as weaker.

1. `data/processed/history.json` (2026-10-19, tree a9754ede): the 24 per-row CRPS totals, coherent seat errors and the reference forecasters' seat errors.
2. `audits/2026-10-17-turnout-review/pollster/report.md:12`: mean model-minus-actual list share by cycle at tree 4fb8002, with the shrink at 0.35: 2011 DA −5.67, ANC −5.75 points; 2016 DA +0.90, ANC +0.06; 2021 DA +2.96, ANC +1.56.
3. MODEL-LOG §1.44 (how c and h were chosen), §1.30's calibration section (ρ = 0.63 on 14 metro-transitions), §1.315 (Johannesburg 2026, ρ 0.63 → 0: largest mean list-share move DA +0.015 points; DA share sd +18.5%; DA seat p5-p95 +4).
4. The `levels.py` docstring's spine-k plateau (0.2377, 0.2358, 0.2387 at k = 0.5, 1.0, 1.5; in-sample).
5. Read-only probes, counts only: pool-turnout moves available before 2011, 2016, 2021 are 4, 34 and 64 (`pools.panel_turnout_spread(cfg, before)[1]`); every 2011 pool spec has no named arrival; `entrant_record` is empty in the 2011 specs read; Johannesburg 2006's only arrival from nothing at ≥ 0.5% is the Independent Democrats at 1.94%.
6. No refit value was computed. No correlation, k, c or h at any origin was evaluated before writing.

## 3. Arms, population, instrument

- **OLD:** shipped `DEFAULTS`, width record rebuilt outside `data/` with no overrides. 24 rows.
- **NEW:** per-target settings (SPEC §2), width record rebuilt per target. 24 rows.
- **Brackets, 2011 only:** B-c (c 0.35), B-k-lo (k 0.5), B-k-hi (k 2.0), B-rho-0 (ρ 0), B-rho-1 (ρ 1), B-ent-0 (entrant chance 0), B-ent-hi (entrant chance 0.5). 8 rows each.
- **Instrument:** `compare_history.run_city_year`, 1000 draws, seed `DEFAULTS["seed"]` per row in every arm, one tree.
- **Headline population:** the 16 rows at 2016 and 2021. The 8 rows at 2011 are reported beside them, labelled "settings declared, not fitted". Per-cycle totals are reported for every score.
- **Scores:** summed CRPS (headline), coherent seat error and its half ("seats given to the wrong party"), list and ward mean absolute error, rows beating uniform swing.
- **Noise:** the paired Monte Carlo error of each NEW − OLD difference, by one draw-index resample of both arms (SPEC §7). A difference inside twice that error is "no measured difference".

## 4. Predictions about the fitted settings

Each is stated against the world and the mechanism. The current value appears only as the point the refit is compared with, because the question is how far it moves.

### 4.1 Turnout correlation ρ̂

Mechanism: ρ̂ is a Pearson correlation across metro-transitions of the four pools' log turnout changes. Pearson removes the mean, so within one cycle a national rise shared by every metro contributes nothing; only metro-to-metro co-movement does. Pooling two cycles with different mean moves adds the between-cycle difference, which every pool shares. The current 0.63 pooled 2011→2016 (flat nationally) with 2016→2021 (a fall in every pool).

- **T1. 2011 is declared.** One metro-transition before 2011; `N_MIN` is not met. Falsified if the fit code reports `n ≥ 8` before 2011.
- **T2. ρ̂_2016 is below 0.63**, in [0.0, 0.6]. Its sample is essentially one cycle (2006→2011, eight metros, plus Johannesburg 2000→2006), so it measures metro-level co-movement only. Ecological noise in pool rates (Census 2022 composition held flat back to 2006) attenuates it toward 0. Falsified if ρ̂_2016 is outside [0.0, 0.6], or if the setting is declared at 2016 under SPEC §2.2's matrix rule.
- **T3. ρ̂_2021 > ρ̂_2016.** Adding 2011→2016 to 2006→2011 adds a between-cycle mean difference (2006→2011 rose nationally; 2011→2016 did not). Falsified if ρ̂_2021 ≤ ρ̂_2016.
- **T4. ρ̂_2021 is in [0.2, 0.75].** Falsified outside it.
- **T5. Excluding Mangaung and Buffalo City's 2006→2011 moves** (the demarcation crossing) changes ρ̂_2016 by less than 0.15. Falsified if it moves more.

### 4.2 Spine k̂

Mechanism: k only moves parties with both routes and some θ evidence; a party with none takes the local route at any k > 0. The objective was flat around 1 in-sample (disclosed, item 4), and a flat objective on a smaller sample gives an argmin with high variance.

- **K1. k̂_2016 and k̂_2021 are both in [0.25, 4]** and neither sits at a grid end (0 or 8). Falsified otherwise.
- **K2. The objective is flat:** at each origin, the loss at k = 0.5 and at k = 1.5 is within 3% of the loss at k̂. Falsified if either differs by more.
- **K3. k moves centres little:** at each 2016 and 2021 row, the largest change in any party's `pool_spec` centre between k̂ and k = 1 (other settings equal) is under 1.5 points. Falsified if any row exceeds it.

### 4.3 Level shrink ĉ and scale ĥ

Mechanism: a shrink pays where the vector of estimated levels is wider than the truth (estimation noise inflates differences between parties). It costs where the large parties are under-forecast before the shrink, because it pulls them down further. Disclosed item 2 says that, at an earlier tree and with the shrink on, the ANC and DA were each under-forecast by about 5.7 points at 2011 and roughly unbiased (2016) or over-forecast (2021) later. Predictions C1-C3 lean on that figure.

- **C1. ĉ_2016 ≤ 0.10.** Fitted on the 2011 rows, where the largest parties were already below their results before any shrink. Falsified if ĉ_2016 > 0.10.
- **C2. ĉ_2016 ≤ ĉ_2021 < 0.35.** Adding the 2016 rows, where pre-shrink centres over-forecast the largest parties, pulls ĉ up, but not to the current value, which was fitted mostly on 2021. Falsified if ĉ_2021 < ĉ_2016 or ĉ_2021 ≥ 0.35.
- **C3. ĥ is weakly identified:** at ĉ, the loss varies by less than 2% across the h grid whenever ĉ ≥ 0.05; at ĉ = 0, h is inert by construction and is reported as such. Falsified if the h curve varies by more than 2% at ĉ ≥ 0.05.
- **C4. The offline exactness control passes on every training row** (SPEC §2.3). Falsified if any row fails; the failure is reported, not repaired silently.

### 4.4 Width record

- **W1. Every NEW width record builds without refusal** (`MIN_ESTABLISHED`, calibration convergence). Falsified by any refusal.
- **W2. No direction is predicted for the widths.** The OLD shrink was fitted on Johannesburg 2016 and the 2021 metros, so it did not see the 2011 rows behind the target-2016 record and saw one of the sixteen rows behind the target-2021 record; the record's residuals for the largest parties are measured within the block of parties at ≥ 20%, which a common shrink moves little. Magnitude only: |σ_NEW(s) − σ_OLD(s)| < 0.05 at s = 0.02, 0.10 and 0.25, at both targets. Falsified if any exceeds 0.05.

## 5. Predictions about the scores

Mechanism for the direction: settings that saw the scored rows fit them better than settings that did not (the in-sample optimism the literature expects; POLLSTER-ON-RECORD §(2)). Mechanism for the size: §1.315 shows ρ moves mean shares by hundredths of a point, so ρ moves CRPS little; k moves centres little (K3); c moves the largest parties by points (§1.44, §1.315's positive control). So c dominates the score change.

- **S1. Headline (16 rows): NEW summed CRPS ≥ OLD summed CRPS − the paired MC error.** NEW is not better than OLD by more than noise. Falsified if NEW is lower than OLD by more than twice the paired MC error.
- **S2. 2021 rows: NEW worse than OLD by more than twice the paired MC error on summed CRPS.** Disclosed item 2: the largest parties were over-forecast at 2021 with the shrink on; a smaller ĉ (C2) raises them further. Falsified if not.
- **S3. 2011 rows: NEW better than OLD on summed CRPS by more than twice the paired MC error.** Disclosed item 2: the largest parties were under-forecast at 2011 with the shrink on; NEW declares c = 0. Falsified if not.
- **S3b. 2016 rows: NEW worse than OLD on summed CRPS** (any margin). Disclosed item 2: with the shrink on, the largest parties were roughly unbiased at 2016; ĉ_2016 ≤ 0.10 (C1) raises them. Falsified if NEW summed CRPS at 2016 is lower than OLD's.
- **S4. Coherent seat error moves in the same direction as CRPS in each cycle** (2011, 2016, 2021). Falsified in any cycle where the signs differ and both differences exceed twice their MC error.
- **S5. Rows beating uniform swing on CRPS (16-row headline): NEW ≤ OLD.** Falsified if NEW > OLD.
- **S6. The change concentrates in the largest parties:** over the 16 rows, the parties with centre ≥ 15% carry more than half of the summed absolute per-party CRPS difference NEW − OLD. Falsified otherwise.

## 6. Predictions about the 2011 brackets

- **B1. B-c moves 2011 CRPS more than any other bracket** (largest |B − NEW-2011| summed over the 8 rows). Falsified if another bracket moves it more.
- **B2. B-rho-0 and B-rho-1 each move summed 2011 CRPS by less than twice the paired MC error.** Mechanism: §1.315 (mean shares barely move with ρ). Falsified if either exceeds it.
- **B3. B-rho-0 widens the 90% seat band of the party most concentrated in one pool**, and B-rho-1 narrows it, in a majority of the 8 rows. Mechanism: §1.315 (ρ 0.63 → 0 widened the DA's share sd at Johannesburg 2026). Falsified if not in a majority.
- **B4. B-k-lo and B-k-hi each move summed 2011 CRPS by less than twice the paired MC error.** Falsified if either exceeds it.
- **B5. B-ent-0 worsens 2011 CRPS in the row with the largest realised 2011 arrival and changes the others by less than twice the paired MC error.** Falsified if not.

## 7. What would void this pre-registration

- A fit or a row opens a file the contamination check rejects (SPEC §5), or the isolated regeneration of a spec or intermediate opens a file not allowed for its target, or differs structurally from `data/processed` (SPEC §5.3: parties, pools, seeds, `fitted_on`, `provenance`; a numeric-only difference is reported, not voiding).
- Any setting file is written or changed after a row at its target or a later one has been scored.
- Any edit to `src/` between the first record build and the last row.
- Scoring with any instrument other than `compare_history.run_city_year` at the registered draws and seed.

## 8. How it will be reported

Every prediction scored as held, falsified or void, including those that fail. Scores published as three columns (as published, OLD, NEW) with the paired MC error, per cycle and summed, the 2011 rows labelled "settings declared, not fitted", and the list of what remains in-sample (SPEC §7). The result is never called out-of-sample.
