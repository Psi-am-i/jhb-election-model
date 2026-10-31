# Pollster review: Step 4 stop gap (SPEC.md, PREREG-DRAFT.md)

**Date:** 2026-10-29. **Standpoint:** election forecaster and survey methodologist (`pollster` skill). Read-only; nothing was run except read-only greps and JSON reads of `data/processed/**/pools_20*.json`. Line numbers are at the working tree on `site-sweep-1` (HEAD `99556398` plus uncommitted edits).

## Verdict: proceed with changes

The four settings are estimated, not tuned. The level shrink minimises error against real list shares of earlier elections, spine k minimises error against real local results, and the width record reads no coverage, PIT or realised-over-predicted ratio. The κ pass (`montecarlo.py:4971`) conserves the drawn mean and reads no outcome. No setting in the design is fitted to a ratio defined on the model's own output.

The design cannot run as written. Its contamination check will reject every row on a read the owner has sanctioned (change 1). Its noise rule is computed on a different quantity from the headline score (change 2). Five predictions are scored against an earlier output of this model (change 3). Changes 1 to 7 must be made before the pre-registration is frozen, because each one alters what the frozen text means.

---

## Required changes

### 1. The open classifier rejects the sanctioned delimitation read in every row, fit and regeneration

**Evidence.** Every row calls `pools.pool_counts(target.city, spec["fitted_on"], _cfg)` (`montecarlo.py:6132`). `pool_counts` calls `composition_at` (`pools.py:1268-1270`). Census 2022 is declared on the 2021 delimitation (`config/dimensions.toml:70-71`), so `composition_at` reprojects through `reproject` → `vd_map(city, "2021")` (`pools.py:1612-1613`). `vd_map` opens the LGE 2021 result file (`pools.py:1543-1544`). `_reprojection_drift` does the same, and also weights wards by the 2021 roll (`pools.py:1726-1738`). The ρ fit (`pools._pool_counts_or_loss`) and the §5.3 spec regeneration both go through `pool_counts`.

SPEC §5.2 allows a file from year T only through a named list of readers, and `pools.vd_map` is not on it. It rejects any file after T "anywhere in a row or a fit". The result:
- every 2011 and 2016 row opens `lge2021_*` (after T), and fails;
- every 2021 row opens it through an unlisted reader, and fails;
- the 2016 settings' `derived_from`, "computed by the fit from its own open log" (SPEC §2.1, §5.3), will contain 2021, so `backtest.check_derived_from` (`backtest.py:729-748`) refuses the file.

PREREG §7 voids the run on the first of these. If the exemption is added after the first failure, the guard has been edited after seeing its result.

**Fix (measurement).**
- (a) Before the freeze, name `pools.vd_map`, reached through `reproject`, `_reprojection_drift` or `composition_at`, as the delimitation-exception reader of the LGE 2021 file. Exclude that read from `derived_from`.
- (b) Tell the owner that `_reprojection_drift` reads the 2021 **roll** as well as the 2021 VD→ward map. That goes slightly beyond PLAN's Definitions ("the 2021 VD→ward delimitation"). It decides admission only and moves no number, but it is a read of a post-target figure, and the owner should agree to it.
- (c) A stack-frame check shows which function opened a file. It does not show which columns left it. The owner asked for absolute certainty about data, so add a **vote-scramble control**. In the isolated tree of §5.3, replace the vote columns of every result file at or after T with random values, keeping the roll, ward, VD and ballot-presence columns. Regenerate that target's specs and intermediates, run one row per target, and require the traced draws (`42_pr_share_draws`, `44_seat_draws`) to be bit-identical to the unscrambled run. This proves that no vote count from T or later reaches a draw, through any reader, the named exceptions included (`theta_residual.residuals()`, `vd_map`).
- (d) Run part 2 of §4 on the control. A planted read of a scrambled vote column must break the identity, and the identity must return when the plant is removed.

**What it forecloses.** The criticism "your guard listed files, not information". Constants stay outside every mechanical proof (change 8). The write-up must say so in its first paragraph, not only in §7's list.

### 2. The Monte Carlo error is computed on a different quantity from the headline

**Evidence.** The headline `crps` is **seat** CRPS: `S.score_seats(run.seat_draws, actual_seats, entrant_actual=..., universe=held)` (`compare_history.py:1980-1982`), on the held universe from `hold_universe` (`compare_history.py:1902`). SPEC §7 says the paired error comes from `score.crps_by_party`, "the function `arms.compare` uses". `arms.compare` resamples **list-share** draws (`_crps(Sb[idx], act, parties)` on share arrays, `arms.py:800-814`) on its own party set, which leaves out actual parties that neither arm drew (`arms.py:780-782`). A seat-unit difference judged against a share-unit error compares two different quantities as if they were one.

**Fix.**
- Resample `44_seat_draws` by draw index, using the same indices for both arms, and rescore each replicate with `score_seats` on the same held universe and the same `entrant_actual`.
- State `MC_RESAMPLES` (200) and `MC_SEED` (`arms.py:130-131`) in the pre-registration.
- State how the error of a 16-row or per-cycle sum is formed: resample each row independently, sum the per-row differences within each replicate, and take the SD across replicates.
- Require OLD and NEW to have equal `universe_key` in every row. Where they differ, rescore both arms on the union. `hold_universe`'s claim that the union is "free" (`score.py:285`) holds only for a column the other arm never draws a seat in, and an arm can draw seats in a column it does not claim.
- Report the per-draw correlation of the two arms per row (`arms` R2), so that a reader can check the pairing.
- State the unit of every CRPS figure (seats) in PREREG §3, where it is currently missing.

### 3. Five predictions are scored against a previous output of this model

**Evidence.** C1, C2, S2, S3 and S3b each cite disclosed item 2 (PREREG §2 item 2, §4.3, §5). Item 2 is the model's own model-minus-actual list share at tree `4fb8002`, measured with the shrink on. CLAUDE.md §4 says to predict "against the world and the mechanism — never against a prior output". The C1 mechanism text says the largest parties "were already below their results before any shrink". Item 2 was measured **with** the shrink on. My reconstruction from `compress_levels` (`montecarlo.py:3229-3238`) on a constructed vector (ANC 60%, DA 30%, two parties at 5%) moves the top party by about −1.7 points and the second by about 0. The pre-shrink sign at 2011 is therefore plausible, but nothing in the record states it.

**Fix (mechanism, clean).** The fit already produces the observable these predictions need. The c = 0 `drawer_inputs` at each training row gives the pre-shrink centre bias of the largest parties at **earlier** elections. Restate the predictions as conditionals on that bias:
- C1/C2: "ĉ_T ≤ 0.10 if the training rows' vote-weighted pre-shrink bias of parties with centre ≥ 20% is negative; ĉ_T ≥ 0.10 if it is positive."
- S2/S3/S3b: "NEW beats OLD in a cycle if OLD's centres at that cycle's rows under-forecast the parties with centre ≥ 20%." This is scored after the run from OLD's trace, so it reads no earlier output.

If the item-2 versions stay, move them to a separate section headed "conditioned on a disclosed earlier output". Score them there, and do not count a held one as evidence about the mechanism.

### 4. At 2016, ρ̂ measures a different quantity from the one the copula uses

**Evidence.** The constant's own comment gives its job: "It matters because it sets how variable the CITY's turnout is, which is the thing 2021 actually moved" (`montecarlo.py:788-792`). That is the shared move of a city's pools. Within one cycle, the centred Pearson correlation across metro-transitions (SPEC §2.2) subtracts each pool's mean move across the metros, which is the national shock that moves all of a city's pools together. PREREG T2's mechanism concedes this ("measures metro-level co-movement only"). SPEC §2.2 still calls the 2016 value "a property of turnout in the world" without qualification. ρ̂_2016 is therefore lower by construction, not only noisier, and OLD − NEW at 2016 mixes the cost of less data with a change of estimand.

**Fix.** Say this where the 2016 value is reported. Pre-register a variant that keeps the common component and report it beside the centred value: either the uncentred correlation of log changes about zero, or the correlation of each pool's turnout error against its `turnout.csv` projection (realised world against a component input, which is estimation). Name in advance which of the two NEW uses, so the choice is not made after the scores are seen.

### 5. Freeze SPEC.md with the pre-registration

**Evidence.** PREREG §1, §3, §4.3, §7 and §8 define the estimators, grids, exactness control, classifier and void conditions by pointing to SPEC sections. PREREG §3 says the pre-registration is "never edited again", but SPEC is not frozen.

**Fix.** Record SPEC.md's commit hash in the frozen pre-registration. Any later edit to SPEC is an amendment: dated, logged and listed in the write-up.

### 6. Predictions that cannot be scored as written, and checks counted as predictions

| item | defect | fix |
|---|---|---|
| B3 | "the party most concentrated in one pool" has no operational definition | define it from `pool_spec` (for example, the party with centre ≥ 5% whose largest single pool weight is highest), and define the band as drawn seats p95 − p5 |
| B5 | "the row with the largest realised 2011 arrival" has no definition | define it as the row with the largest actual share of compare_history's `entrant_actual` |
| W2 | σ has no unit | name the field and unit in `width_record.json` (log-share residual sd, per the module docstring) |
| S6 | "parties with centre ≥ 15%" does not say whose centre | OLD's `pool_spec_centres`, as `arms.compare` uses `classify_by` |
| K3 | needs a k = 1 run at 2016 and 2021 targets that is not in §1.5's arm list or §8's runtime | add it to the run list |
| T1, C4, W1 | process checks, not predictions (T1 is already settled by the disclosed count of 4 pool-moves) | label them "checks" and leave them out of the held/falsified tally |
| B1, B5 | close to true by construction. At 2011, B-c differs from OLD only in ρ (0.5 against 0.63), so B1 restates S3. Under B-ent-0 the relabel never fires, so the arriving party is scored at zero seats | keep them, labelled "mechanical" |

### 7. The "as published" column is not what was published, and conflicts with PLAN Step 0

**Evidence.** PREREG §8 and SPEC §7 label the `history.json` column "as published". `history.json` is a 2026-10-19 run on dirty tree `a9754ede` (SPEC P3). The figures that were published are on the site at `51d13ce1`, which SPEC §7's own table lists separately. PLAN Step 0.2 orders `history.json` moved to quarantine "so there is zero chance they are read" (PLAN lines 3-6, 36-42), and SPEC P3 records that it is still on disk. Step 4 asks for old and new scores side by side, which the OLD arm provides: current settings, this tree, the same seed.

**Fix.** The headline comparison is OLD against NEW. If a third column is kept, take it from `site/` at `51d13ce1`, label it "withdrawn, in-sample, as published", and get the owner's yes, because it brings quarantined figures back into a new document.

---

## Changes required in the write-up

### 8. The in-sample list leaves out three items, and one artefact label is wrong

- **Add `MIN_HOME_SPLITS` and the home/away splinter rule.** `pools.py:3785-3797` and `4553-4561` record that the rule exists because sizing ActionSA from one home split "gave 1.87% against an actual 16.1%". It was chosen after the 2021 result. `pools.SPLITS` is listed and this rule is not.
- **Add `judgements/<city>-{2011,2016,2021}.toml` to SPEC §5.1 and to the classifier's allowed set.** They are read per target and are missing from the input table. I checked all 24: every non-comment line is a `[party.X]` header, a `baseline_share` or an empty `parent`, so they carry no override. Record that finding and the command that produced it.
- **Add the generic-entrant setting in the training rows.** Under the origin-T convention, the 2011 training rows behind the 2016 and 2021 c-fits and width records carry `entrant_prob` 0.25 and `entrant_share` [0.01, 0.04, 0.12], both typed by people who knew the outcomes. The c-fit loss also needs a rule for the ENTRANT column and for actual parties absent from the spec (apply `relabel_run` with that row's `entrant_actual`, or exclude both, and say which).
- **The `RETROSPECTIVE: not all precede this target` label is wrong in the clean direction.** It is a static string printed at every home-city split (`pools.py:4566-4567`). The markers in every `pools_2021.json` read GOOD (2019) and NFP (2014), both before 2021, and every `pools_2016.json` reads NFP (2014). Both are filtered by `home_cutoff = target.year` (`pools.py:5988`). An auditor following the owner's instruction would reject a clean artefact on this label. Correcting it is a `pools.py` string change, so it joins `POOLS-REEMIT-QUEUE.md`. It does not need to block the stop gap.

### 9. The 2016 width record measures residuals on the rows that fitted ĉ_2016

**Evidence.** ĉ_2016 is fitted on the eight 2011 rows (SPEC §2.3). The 2016 width record is then measured on residuals of the same rows after that shrink (SPEC §4). The shrink was chosen to make those residuals small, so the record's widths for the largest parties are biased narrow. OLD's c was fitted on Johannesburg 2016 and the 2021 metros and saw none of these rows. The same holds at 2021 for k̂ and ĉ against the 2011 and 2016 training rows.

**Answer to Q6.** Neither convention lets data from T or later into a row. The own-origin convention matches what a width record claims to measure, which is the real-time forecast error at earlier elections. Keep origin-T as primary so OLD and NEW are built the same way, and pre-register a direction for the sensitivity: own-origin block widths ≥ origin-T block widths at s ≥ 0.20, at both targets. State the narrowing at the point where NEW's calibration is reported.

### 10. The declared 2011 values and N_MIN: what the owner should be told

- **N_MIN = 8 is a rule that fits once one complete earlier cycle exists.** The eight metros in one cycle share one national swing (POLLSTER-ON-RECORD line 62), so they are not "independent units" (SPEC §2.1). Rename the rule to say that. At 2016 every fitted value rests on one cycle, and its between-cycle error cannot be identified from the data. Publish each 2016 curve, and give a within-cycle leave-one-metro-out spread as a lower bound on that error. The defensible alternative is to declare at 2016 as well and fit only at 2021, on two cycles. That is the owner's choice (Q2).
- **c = 0 at 2011** is the identity and needs no data. It is defensible.
- **k = 1.0 at 2011 is the value fitted in-sample**, and the B-k brackets (0.5, 2.0) are the ends of the in-sample plateau (`levels.py:187-193`). "Routes equal at one unit of θ evidence" depends on the unit chosen for θ evidence, so it is not a neutral value. Keep 1.0 if the owner accepts it, label it "equals the in-sample value", and add brackets at k = 0 (pure NPE route) and k = 8 (close to pure local route). Those extremes come from the structure of the blend, not from the panel.
- **ρ = 0.5 at 2011 has no source.** Clean data may exist. The NPE 2004→2009 transitions for the eight metros come before 2011 and measure the same group co-movement in a different kind of election. I did not check whether `pool_counts` accepts NPE years (it reads `ward_totals` and `vd_map` from `CALENDAR[year].results`). Check that before the owner is told there is no source. If it works, report the NPE estimate beside the declared 0.5.
- **New-party chance and size at 2011.** The chance is bracketed; the size `entrant_share` is not. Chance and size are separate questions, and the size range was typed by people who knew the 2011 arrivals. Add one size bracket, low and high (for example, the range scaled ×0.5 and ×2), or state in the row label that the size is unbracketed. SPEC §2.5 says "the pre-2011 record the code can read is empty". That should read "unread": the 2000 and 2006 files are on disk for all eight metro codes (POLLSTER-ON-RECORD table at line 86), and `_citywide_for` does not resolve them outside Johannesburg.

### 11. Labels and noise in the reporting plan

- **State the noise rule's scope where the rule is stated.** "Inside twice the paired MC error is no measured difference" (PREREG §3) describes simulation noise only. The headline covers two cycles, so no sampling interval exists across elections, and a difference larger than MC noise is still one realisation of two national swings. Report per cycle, as planned, and say this beside the rule.
- **At 2011, OLD − NEW measures "settings fitted on later elections against settings declared"**, not optimism. Label that column so.
- **Q1 label.** "In-sample, with the sentence…" is correct. compare_history's IN-SAMPLE verdict should stay on NEW rows (SPEC §7).

---

## Optional

1. **Tshwane at 2011.** My understanding, at medium confidence, is that Metsweding's municipalities were incorporated into Tshwane at the 2011 elections. `DEMARCATION_CROSSING` lists only Mangaung and Buffalo City (`levels.py:604-607`), and SPEC R3 and PREREG T5 follow it. Check Tshwane's 2006 municipality code and footprint, and include TSH 2006→2011 in the T5 exclusion if the footprint changed.
2. **Murphy (1992) baseline.** It is absent (Q5). Persistence (`last-lge`) and uniform swing are present. Without Murphy the headline is a margin over the floor, not over the bar; say so beside "rows beating uniform swing".
3. **Number of alternatives tried.** PLAN 3.6 asks for the number of alternatives tried beside each score-chosen decision. The stop gap could carry the counts from MODEL-LOG for the shrink's form (four forms screened, §1.44) and for the draw law, to show the size of the selection that remains.
4. **Brackets at 2016.** The 2016 values rest on one cycle, and only 2011 is bracketed. The published objective curves cover part of this. One ĉ bracket at 2016 (the fit's value ± the within-cycle leave-one-metro-out range) would show how much the headline depends on that cycle.
5. **Part 1 of the "it looked" check.** SPEC §5.2 bounds each process's opens "as a fraction of the files `run_model` is known to read". Say how that denominator is computed. If it comes from the same open logs, the check is circular.

---

## Claims considered and rejected

| claim | why rejected | evidence |
|---|---|---|
| The level-shrink fit is tuning because its loss is defined on the model's own centres | Its loss is error against real list shares of earlier elections, which is estimation of a point-forecast correction. The barred class is a ratio of realised to predicted spread (CLAUDE.md §4) | SPEC §2.3; `montecarlo.py:3181-3238` |
| The κ calibration pass in the width record is a k*-type ratio | It rescales the draw to conserve its own mean and reads no outcome | `montecarlo.py:4954-4976` |
| The named-arrival seeds at 2021 are sized from post-target home splits | Filtered by target year; the markers in the specs show only pre-target measurements | `pools.py:5988`, `3815-3820`; `pools_2021.json` `splinter_home` |
| By-election files reach past targets | Read from the target's processed directory, which holds no `byelection_*` file for 2011-2021 | `montecarlo.py:5957-5961`, `7039`; `data/processed/joburg/2021/` listing |
| The width record is read before `drawer_inputs`, so fits would open the denylisted live record | It is read lazily, and only by the poll blend (off) or the draw, both after the `drawer_inputs` return | `montecarlo.py:7228-7237`, `7388-7393` |
| Past-target judgement files carry hand-typed outcome-aware overrides | Every non-comment line is a template field | grep over the 24 files (change 8) |
