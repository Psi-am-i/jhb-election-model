# Review of `SCORES-FOR-2026-EVALUATION.md`

> ⛔ Every backtest figure dated before 2026-10-23 is in-sample and is not evidence of forecast accuracy (MODEL-LOG §1.333). Every `history.json` figure below is in-sample and is quoted as a fit diagnostic.

**Date:** 2026-10-23
**Standpoint:** election forecaster and survey methodologist (`pollster` skill). Read-only; no model run, test or sweep. Computation was limited to reading `data/processed/width_record.json` (generated 2026-10-21T09:31:22Z), the quarantine copy of `data/processed/history.json` (generated 2026-10-19T07:52:44Z, commit `a9754ed`, `git_dirty: true`, 1000 draws, seed 20261104), `pools_2026.json`, the quarantine `ORIGINALS.txt`, and listing files.

**Code and records read:** `src/width_record.py` (whole), `src/montecarlo.py` (`DEFAULTS`, `TURNOUT_CORRELATION`, `compress_levels`, `width_sigma`, `width_location`, `read_width_record`, `width_record_variant`, the generic-entrant gate at lines 6477–6510, `run_model`'s `drawer_inputs` return), `src/levels.py` (`SPINE_K`), `src/backtest.py` (`FITTED_ON`, `FITTED_ON_UNINSTRUMENTED`, `PROVENANCE_UNSETTLED`, `NOT_FITTED`), `src/compare_history.py` (`rank_band_of`, `calibration_columns`, `_band_splits`, the call at line 1939), `src/score.py` (`coverage`), `src/cityconfig.py` (`plan_bounds`), `cities/joburg.toml`, MODEL-LOG §1.44, §1.326, §1.327, §1.333, JUDGEMENT-CALLS §A59, the quarantine `README.md`, `ORIGINALS.txt`, `remove-originals.sh`.
**Not read:** `POLLSTER-ON-RECORD.md`, `PLAN.md`, `PLAN-REVIEW.md`, `INVENTORY.md`, `tests/test_levers_are_live.py`, MODEL-LOG §1.314/§1.316/§1.330. Claims resting only on those are marked "not checked".

---

## Summary

1. **The §2 coverage and PIT table is labelled as list-share coverage. It is seat coverage.** `compare_history.py:1939` builds `calibration` from `run.seat_draws` and `actual_seats`. Seats are integers, and a party forecast and realised at 0 seats is inside every interval. Three of §2's readings change: ranks 13+ over-coverage, the "0.77 inside 50%" figure, and "PIT near 1 is a level finding". The vote-error table in the same file (`bands`) does show a level miss at 2021 ranks 4–12. Its sign flips from 2011 to 2021, so it does not carry to 2026 as a class property.
2. **Every number in the σ and m tables re-derives exactly.** One description is imprecise: m(s) is the location parameter, and the mean residual is m(s) − σ(s)²/2. The reading of the location result needs one more qualification. In the block-relative frame the shrink lowers every sub-20% residual by arithmetic. "More negative with the shrink" is therefore mostly the shrink's own redistribution. §1.44 already records that cost.
3. **The §4b design is forward in intent and has no leak through the settings it names.** Four problems remain. Its three descriptions of the 2016 cycle disagree on whether a shrink applies there. The "declared" 2011 spine k (1.0) is the panel-selected value. The design cannot run as written, because `width_record.build` applies one setting list to every cycle and the variant key would accept a mixed record silently. Its limits also omit the Census 2022 composition at every past target.
4. **The quarantine table is mostly right, but §3 understates what remains readable.** 5,506 of the 5,515 originals are still in the repository tree, not just the three it names. The keep/delete recommendations need to say whether they apply to the copies, the originals or both.

---

## Section by section

### Summary and §1 table, settings that do not reach the 2026 forecast: agree

- **Generic entrant.** Re-derived: `pools_2026.json` `seeds` holds 46 entries, all above 0. `scenario["pool_seeds"] = spec.get("seeds", {})` (montecarlo.py line 6022), and the slot is appended only `if scenario["entrant_prob"] > 0 and not named_arrivals` (line 6509). The comment at lines 6504–6506 still says the 2026 target's "`seeds` are empty". That comment is stale.
- **Dirichlet scale.** `DEFAULTS["draw_law"] = "universal"` confirmed (line 428). I did not trace the read site of `dirichlet_scale` beyond its `DEFAULTS` comment ("READ ONLY UNDER…").
- **Slate growth.** Not checked (`test_levers_are_live.py` not read).

### §1 table, settings that reach the 2026 forecast: agree, with three corrections

- **Turnout correlation: agree that it is estimation.** One fact in §1c is wrong. The correlation is read inside `make_drawer` (montecarlo.py line 4400), and `run_model(stop_after="drawer_inputs")` returns before any drawer is built. The correlation therefore does not touch the `pool_spec` centres that the width record's residuals are measured against. It reaches the record only through the fixed point's Δ. Measured: the mean of `delta_shift` at the 2026 target is 0.0256 under the live variant, over 607 party-rows. "14 metro-transitions" across eight metros and two transitions (at most 16) is quoted from the code comment and not reconciled.
- **Level shrink: agree.** The §1.44 quotes match MODEL-LOG: 0.375 fitted on Johannesburg 2016 alone, 6 of 8 metros improved, 0.350 in all nine folds. The concern that a cycle in which the largest party holds would be biased against has measured support that the evaluation does not use. In `history.json` (shrink on), the signed list-vote error at ranks 1–3 summed over the eight metros is **−43.77 points at 2011** against **+32.37 points at 2021** (forecast − actual, `bands.signed_pp`). This is in-sample, and no shrink-off counterpart was read, so it shows the sign varies by cycle. It does not show the shrink's effect at 2011.
- **Spine k: agree as written, with a stronger caveat.** `PROVENANCE_UNSETTLED["spine_k"]` (FIX #39, open) says two provenance statements for k disagree and one of them is wrong: "three transitions on the archive reaches 2016->2021". Whether 2021 entered k's fit is therefore unknown, not only in-sample with respect to cycles.
- **By-election weight: agree, with one wording change.** The quotes match §1.326: Johannesburg's minimum at 0, rising monotonically; pooled slope 0.329. "Not a measured optimum" contradicts §1.326 and §A59, which both say ½ is the 2021 grid minimum on one cycle. The accurate statement is: the in-sample grid minimum over eight metros, one cycle, with every other setting in-sample. The Johannesburg magnitude belongs beside its direction: list-vote error 6.30 points at weight 0 against 6.58 at ½ (§1.326 arm R line). Leave-one-metro-out also picks 0.5 for Johannesburg (§1.326 instrument 2). §1.327 should be cited too: it corrects §1.326's slope-versus-grid explanation and shows `pr_mae` is vote-weighted. The stale `NOT_FITTED["w_bye"]` text ("Scoreable against a local result only by the 2026 one") is confirmed.
- **Missing from the table:** `FITTED_ON["plan_bounds"]`, "chosen knowing every result up to 2021". The bounds are set in `cities/joburg.toml` (`[judgements.plan_bounds]`, including MK [0.3, 1.0]). `cityconfig.plan_bounds`'s docstring says they are read only for a party missing from the θ prior and that "nothing reaches them on a city with its own history". That is argued in a docstring. I did not verify it for Johannesburg 2026. The owner's ActionSA centre (§1.330) also reaches the 2026 forecast and belongs in the table as a typed judgement.

### §1c width record, σ table: agree

Re-derived from `width_record.json` at target 2026, over 589 rows (590 for the scale-0.4 variant) from 237 party-elections, 95 established. Each value matches to three decimals, with σ in natural-log share:

| centre share | σ, shrink 0 | σ, shrink 0.35/0.04 | σ, shrink 0.35/0.4 |
|---|---|---|---|
| 0.5% | 0.810 | 0.813 | 0.812 |
| 2% | 0.780 | 0.797 | 0.795 |
| 5% | 0.614 | 0.661 | 0.662 |
| 10% | 0.323 | 0.346 | 0.352 |
| 25% (within block) | 0.083 | 0.076 | 0.080 |

The differences the evaluation quotes (−0.007 at 25%; +0.017, +0.047 and +0.023 at 2%, 5% and 10%) are correct. A point for §4a: the shrink alone moves σ by up to 0.047 at 5%. That is the same order as the forward-versus-live gap §4a hopes to measure (see §4 below).

### §1c width record, location: the numbers are right and the description is imprecise

Re-derived, target 2026: m(s) = c1·L + c2·L², L = min(log(s/0.20), 0). Live variant c1 = 0.3427, c2 = 0.0758; shrink-0 variant c1 = 0.2092, c2 = 0.0597. Every m value in the evaluation's table matches.

- **m is not "the average log error".** The likelihood (`joint_nll`) is r − Δ ~ N(m − σ²/2, σ²). m is the log of the mean ratio, and the mean log residual is m − σ²/2. With σ near 0.8 at small sizes, the two differ by about 0.3. At 0.5%, shrink 0, m = +0.041 while m − σ²/2 = −0.287. The direction of the shrink comparison holds on either quantity:

| centre share | m − σ²/2, shrink 0 | m − σ²/2, live |
|---|---|---|
| 0.5% | −0.287 | −0.564 |
| 2% | −0.469 | −0.705 |
| 5% | −0.364 | −0.548 |
| 10% | −0.169 | −0.261 |

- **"After the fixed point has removed the draw's own location": correct.** `fit_target` refits on r − Δ, and the stored `location` is the last iterate. Δ differs between variants but is small: mean `delta_shift` is 0.0156 (shrink 0) against 0.0256 (live) at target 2026. Δ does not explain the shift of about 0.22 in m.
- **The shift is close to what the shrink's arithmetic predicts.** For a sub-20% party, r = log(a/s) − log(A/P). The shrink raises s for small parties and lowers the block's P, and both lower r for the same realised result. An illustrative calculation (argued, with an assumed block of 40% + 30%) gives a shift of about −0.25 at 2%, against the measured −0.222. The evaluation's sentence "the renormalisation moves mass toward the sub-20% parties that were already over-centred against the block" is therefore mostly a restatement of what the shrink does. §1.44 itself records the same cost: ranks 13+ moved from −1.55 to +5.60 points signed. The evaluation should cite that and drop "unresolved" as a framing of a conflict.
- **The proposed separating measurement does not separate.** The evaluation proposes the location fitted on established rows only, with and without the shrink. That fit carries the same mechanical shift. The measurement that settles the question is the vote-weighted signed error in points by centre-size band, established and new rows separately, with and without the shrink. That is the unit of §1.44's claim, with bands set on the forecast side rather than by result.
- **The rank-by-result frame is selection on the outcome.** `rank_band_of` ranks by actual share, and `_band_splits` says so ("unlike the rank band itself, which `rank_band_of` assigns by ACTUAL share"). A party reaches ranks 4–12 partly by beating its forecast. The evaluation names the frames as "different populations". That they differ by outcome conditioning is the reason they diverge, and it should be stated.

### §2 direction rule: agree as a pooled, in-expectation statement; disagree class by class

Tuning lowers the pooled objective, not every class's error. §1.44's shrink raised ranks 13+ signed error from −1.55 to +5.60 points in-sample. "In-sample under-coverage of a class is a lower bound on its out-of-sample under-coverage" therefore does not follow for a class the tuning made worse.

### §2 coverage and PIT table: numbers right, label wrong

Every cell re-derives from `calibration.reference` (per-cycle row counts 24/60/29, 24/60/46, 24/68/135; overall 514; the 2011 summary 0.659/0.819/0.855). PIT for ranks 4–12 at 2021 is 0.724 over 68 rows with 0.206 above 0.95; ranks 1–3 at 2021 is 0.373 over 24. All match. The defects are these:

1. **Unit.** The intervals are central intervals of the **seat draws** and `hits` is the realised **seat count** inside them (`calibration_columns(run.seat_draws, actual_seats, …)`; `score.coverage`). The header "share of the realised list share inside the central interval" is wrong. The evaluation's "level finding, not a width finding" reading is a vote-level claim drawn from seat PIT.
2. **Discreteness.** `score.coverage`'s docstring states that a calibrated seat forecast over-covers by "a few points at the 50% level". At 2016 the 80% and 90% coverage are identical (0.957, 141 rows), which is the integer lattice showing. The overall 0.77 inside 50% is partly this effect. The rejected-claims row "bands too narrow throughout" should not lean on it. By the evaluation's own direction rule, in-sample over-coverage carries no out-of-sample weight anyway.
3. **Ranks 13+ and off-ballot rows.** A party forecast at 0 seats that wins 0 is inside every interval. The 0.99–1.00 at ranks 13+ is mostly that, and says nothing about share width. The 44 off-ballot rows are inside at 0.955. Excluding them, overall coverage is 0.751 / 0.898 / 0.917 over 470 rows, against 0.768 / 0.903 / 0.920 with them.
4. **The level miss is real on votes, and its sign depends on the cycle.** From `history.json` `bands.signed_pp` (forecast − actual, list vote, summed over eight metros, points):

| cycle | ranks 1–3 | ranks 4–12 | ranks 13+ |
|---|---|---|---|
| 2011 | −43.77 | +37.47 | +0.87 |
| 2016 | −4.96 | −4.65 | +9.61 |
| 2021 | +32.37 | −38.23 | +5.86 |

Seat PIT for ranks 4–12 follows the same pattern: 0.344 at 2011, 0.591 at 2016, 0.724 at 2021. The 2021 under-forecast is a vote-level miss, so the evaluation's level reading survives on vote evidence. It is not a class property, because the class is defined by result and the sign reverses across cycles.
5. **Concentration.** Of the 14 rows at 2021 ranks 4–12 with seat PIT above 0.95, five are the PA (Johannesburg, Tshwane, Ekurhuleni, Cape Town, Nelson Mandela Bay). The other nine are single-metro parties (Al Jama-ah, Cape Coloured Congress, Northern Alliance, DOP, and five others). This is one party's national surge plus local arrivals. "Out of sample, that class should be expected to be under-covered at least as badly" should be replaced with: the 2021 miss was the PA and local arrivals. For 2026 it bears on how the named arrivals and the PA's centre are set, which the class label hides.

**Provenance paragraph: agree.** The mixed provenance (in-sample centres, forward widths at 2016 and 2021, fallback at 2011) matches `FORWARD` and `FALLBACK_TARGETS`.

### §2 uses table: agree, with one addition

Comparisons of arms by rank band inherit the outcome conditioning above. Split by `p_any` or by centre size instead, which `_band_splits` already provides.

### §3 quarantined files: partly agree

- **Keep `history.json`/`.md` until a clean baseline exists: agree.** It is not the only in-sample run on the 24 city-years, though. The step-7 and step-11 arm `result.json` files are earlier ones.
- **Keep the arm summary files, drop the bulk: agree.** Counts re-derived from `ORIGINALS.txt` (5,515 lines): step 7, 1,680 per-arm files (`I`, `U`, `US`, `UC`, `C0`, 336 each), 10 compare/describe files and 5 plausibility verdicts; step 11, 3,791 arm files plus `data/arms/step11/measures.json`. The evaluation's 1,680 + 3,791 + 10 + 1 + 5 is exact. Size: the sum of file sizes in the quarantine folder by `stat`, including its own README, list and script, is 227,294,388 bytes. The evaluation says 225,843,991. The difference is plausibly the README and list, but I did not separate them.
- **Delete past-target seat draws and `validation_2021.json`: agree.**
- **"Deleting the folder does not give zero chance": agree, and understated.** 5,506 of the 5,515 originals still exist in the repository tree. Only the nine tracked files were removed. The remainder include `data/arms/step11` (3,990 files on disk), `.claude/step7-2026-10-13` (1,913 files) and the past-target tables under `data/processed/joburg/2016`, `joburg/2021` and `capetown/2021`, not only `sweep.json`, `width_budget.json` and `validation_2021.json`. Deleting the quarantine copy while the originals remain removes nothing that can be read. The recommendations need to name which copy each applies to.

### §4a forward width record: agree in principle; not runnable as written

- **Estimation, not tuning: agree.**
- **"Only the centres change; build with `width_record.py --out DIR`" is not true of the code.** `build(sets, …)` applies one `sets` list to every earlier cycle. `write` stores the record under `width_record_variant`, a key of `level_shrink` and `level_shrink_scale` only (line 3752). `read_width_record` refuses only a stale artefact key, a missing variant or a missing target. A per-cycle settings argument is a code change. A forward record written under the live variant would be accepted silently, a `~` artefact in `declares.py`'s terms. It should reach the draw through `run_model(width_override=…)`, in process, and never under the live key.
- **Shrink regime.** The forward record's earlier-cycle residuals sit about shrink-off centres (2011 and 2016 in §4b's chain), and the record is applied about shrink-on centres. The variants show the shrink alone moves σ by up to 0.047 at 5%. The forward-versus-live gap mixes this with selection optimism unless the chain applies a forward-fitted shrink at 2016 (see §4b).
- **Decision rule.** "If the forward σ is wider, the live bands are too narrow by that amount; if not, PLAN 0.7's sentence is withdrawn" needs a pre-registered threshold against the record's sampling error, for example a bootstrap over city-years within cycle. Otherwise a gap of 0.01 in σ decides the sentence either way.
- **Direction of the residual bias.** Forward centres use settings fitted on less data than the 2026 forecast's own settings. Forward residuals may therefore overstate 2026's errors slightly. This is argued, small, and conservative. It should be stated.

### §4b forward-chained 2021 rows: the design is forward, but internally inconsistent and incomplete

Leakage through the named settings: none found. Each setting is fitted on cycles strictly before the one it centres, and Δ reads no outcome. The defects:

1. **The 2016 cycle is described three ways.** §4a says 2016 centres use "settings fitted on rows up to 2011". §4b runs 2016 with shrink 0. §4c, for the 2016 rows, uses "settings fitted on the 2011 rows only", which would include a shrink fitted on 2011. One rolling-origin chain with an expanding window would make §4c a by-product of §4b: declared settings at 2011; every setting including the shrink fitted on 2011 and applied at 2016; refitted on 2011 and 2016 and applied at 2021. It would also remove the shrink-regime mismatch in the width record.
2. **The 2011 "declared" spine k is 1.0, the panel-selected value**, with provenance possibly including 2016→2021 (FIX #39). A declared value must come from outside the panel: a value fixed before the panel was seen, or fitted on transitions before 2011. It should also be bracketed. Turnout correlation "declared" needs a stated value for the same reason, though it reaches the centres only through Δ.
3. **2006→2011 transitions.** Buffalo City and Mangaung were not metros in 2006. "Where comparable" needs its rule stated in the pre-registration, with a fallback if fewer than some stated number of metros qualify. The same applies to spine k on "transitions ending at or before 2011".
4. **Limits it omits.** Both arms read Census 2022 composition at 2021 (`FITTED_ON["pools"]`), which post-dates the target. They also read the target's own contestation, which is public before polling day, so that one is acceptable, and `plan_bounds` if it binds. The gap cancels shared leaks, but the forward score is then not fully out-of-sample, and that belongs at the claim.
5. **Instrument.** Name the score exactly so both arms share a denominator: `pr_mae` (vote-weighted, §1.327), half the summed absolute seat error ("seats given to the wrong party"), CRPS, coverage and PIT. Split coverage and PIT by `p_any` or by centre size, not by result rank. Use common random numbers (same seed per row) and report Monte Carlo error on per-metro differences, which §1.326 did not measure.
6. **Shrink objective.** "Fitted to those unshrunk 2016 centres against the 2016 results, as §1.44" should name the loss (§1.44 used summed absolute list error, leave-one-city-year-out on cached mean vectors) and the grid. It should also say whether h is refitted or held at 0.04. §1.44 swept h from 0.02 to 0.40.

### §4c and §4d: agree

§4c folds into item 1 above. §4d (structure settled only by the sealed 4 November forecast) is right.

### Claims considered and rejected (the evaluation's table): agree with all rows but two

- "2026 bands too narrow throughout": the conclusion stands. Its evidence should drop the 0.77-inside-50% figure (seat discreteness, and over-coverage in-sample carries no weight under the evaluation's own rule). It should rest on the σ variants and the cycle-varying vote-level table.
- "The shrink is shown to correct a share vector whose spread is too wide": keep the rejection, but replace the evidence. The m shift is largely arithmetic. The real limits are outcome-conditioned rank bands and the 2011 sign (ranks 1–3 −43.77 points).

---

## This review's rejected-claims table (claims in the evaluation overturned here)

| Claim in the evaluation | Why rejected | Evidence |
|---|---|---|
| §2 coverage is "the realised list share inside the central interval" | It is the realised seat count inside the seat-draw interval | `compare_history.py:1939`; `score.coverage` |
| PIT near 1 at ranks 4–12 shows a level finding from that table | Seat PIT conflates vote level and translation. The vote table does show a level miss at 2021, but its sign reverses from 2011 | `history.json` `bands`: +37.47 (2011), −38.23 (2021) points |
| Ranks 4–12 should be expected to be under-covered out of sample at least as badly | The class is defined by result. Five of the 14 PIT>0.95 rows are one party (PA). Sign varies by cycle | `rank_band_of`; `_band_splits`; PIT 0.344 / 0.591 / 0.724 |
| The 2021 residuals are measured around centres shaped by the turnout correlation | The correlation is read in `make_drawer`, after `drawer_inputs` returns | montecarlo.py line 4400; `run_model` `stop_after` |
| m(s) is the average log error | Mean residual is m − σ²/2 | `joint_nll` |
| The location on established rows separates the explanations | The block-relative frame lowers every sub-20% r by the shrink's arithmetic | `residual_rows`; `compress_levels` |
| Only three untracked originals remain | 5,506 of 5,515 remain | `ORIGINALS.txt` checked against the tree |
| §4a needs only `width_record.py --out DIR` | One `sets` per build; the variant key would accept a mixed record | `build`, `write`, `read_width_record` |
| The by-election weight is not a measured optimum | It is the 2021 grid minimum, one cycle, other settings in-sample | §1.326 instrument 1; §A59 |

## Re-derived and not re-derived

**Re-derived:** every σ and m cell; m − σ²/2; mean `delta_shift`; row, party-election and established counts of the 2026 record; every cell of the §2 coverage and PIT table; overall coverage with and without off-ballot rows; the 14 PIT>0.95 rows; `bands.signed_pp` by cycle; the 46 seeds; ORIGINALS counts and presence; quarantine byte total (by my method).
**Quoted and matched to source, not re-derived:** §1.44 (0.375, 6 of 8, nine folds, +32.30/−36.20, ranks 13+ −1.55 → +5.60); §1.326 (grid, slope 0.329, Johannesburg 6.30/6.58); `SPINE_K` plateau; turnout correlation 0.63 over 14 transitions.
**Not checked:** slate growth inertness; `dirichlet_scale` read site; whether `plan_bounds` binds at Johannesburg 2026; arrival sizing (×0.21, 2.19%) beyond the pools.py "strictly before the target" docstrings; PLAN-REVIEW item 21; the source of the evaluation's byte total.

---

## Changes I would make

1. Relabel §2's table as seat coverage and seat PIT. Add the discreteness caveat from `score.coverage`. Drop the 0.77-inside-50% argument. Exclude off-ballot rows from the overall line, or show both lines (0.751/0.898/0.917 over 470 rows; 0.768/0.903/0.920 over 514).
2. Add the vote-level table by cycle (`bands.signed_pp`) beside the seat table, and rest the level reading on it.
3. Replace "ranks 4–12 should be expected under-covered out of sample" with the concentration finding: PA in five metros plus local arrivals. State that rank bands are assigned by result. Recommend `p_any` or centre-size splits for every coverage and PIT figure in §4b.
4. In §1c, describe m as the location parameter, give m − σ²/2, and state the block-relative arithmetic. Cite §1.44's recorded cost to ranks 13+. Replace the proposed separating measurement with vote-weighted signed error in points by centre-size band, established and new separately, shrink on and off.
5. Correct §1c's claim that the turnout correlation shapes the centres. It enters the record only through Δ, a mean of 0.0256 at target 2026.
6. Add `plan_bounds` and the owner's ActionSA centre to the §1 table, with whether each binds at 2026. `plan_bounds` is marked unverified until a `30_centres.json` trace shows it.
7. Use the 2011 row (ranks 1–3 −43.77 points, shrink on) as the measured instance behind the shrink row's "a cycle in which the largest party holds". Label it in-sample, with no shrink-off counterpart read.
8. Spine k: cite FIX #39 and say whether 2021 entered its fit is unknown.
9. By-election weight: replace "not a measured optimum" with "the in-sample 2021 grid minimum over eight metros, one cycle". Add the Johannesburg magnitude (6.30 against 6.58 points) and cite §1.327.
10. Rewrite §4a–§4c as one expanding-window rolling-origin chain, with the shrink fitted forward and applied at 2016. Give one rule for every cycle.
11. Replace the "declared" 2011 spine k of 1.0 with a value from outside the panel, and bracket it. State the turnout-correlation declared value and the comparability rule for 2006→2011.
12. State the code change §4a and §4b need: per-cycle settings in `width_record.build`, and the forward record passed by `width_override` in process, never written under the live variant key.
13. Pre-register §4a's decision threshold against a bootstrap of the record over city-years, so a gap within sampling error decides nothing.
14. Add to §4b's limits: Census 2022 composition at 2021 in both arms, and `plan_bounds` if it binds. Name the instruments exactly (`pr_mae`, half summed absolute seat error, CRPS), with common random numbers and Monte Carlo error reported.
15. In §3, state that 5,506 of 5,515 originals remain in the tree. Make each keep/delete line name the copy, the original or both. State how the byte total was measured (this review's `stat` sum of the folder, 227,294,388 bytes, differs from its 225,843,991).
16. Note that the comment at montecarlo.py lines 6504–6506 ("whose `seeds` are empty") is stale against `pools_2026.json`. That is a documentation fix for the model record, not for this evaluation.
