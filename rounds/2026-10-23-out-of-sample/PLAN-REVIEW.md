# Pollster review of PLAN.md (backtests from earlier data only)

**Date:** 2026-10-23
**Reviewer standpoint:** election forecaster and survey methodologist (`pollster` skill). Read-only; nothing was run. This file is the only write.
**Read:** `PLAN.md`, `INVENTORY.md`, `POLLSTER-ON-RECORD.md`, `OWNER-DECISIONS-ANSWERED.md` items 27–30, and in the code: `src/backtest.py` (the four registers), `src/montecarlo.py` (`TURNOUT_CORRELATION`, `GAMMA_FOLD`, `MODULE_CONSTANTS`, the width-block constants, `pool_spec_centres`, turnout-pattern loading), `src/levels.py` (docstring, `SD_FLOOR`, `SHRINK`, `RELIABILITY_HALF`, `SPINE_K`), `src/pools.py` (`reproject`, `composition_at`, `SPLINTER_PARENT_WEIGHT`, `SPLITS`), `src/width_record.py` (docstring, `FORWARD`), `src/turnout.py`, `src/bye_value.py` (header), `src/fold.py` (`FOLDS`), `src/stats.py` (history.json reader).
**Not read:** MODEL-LOG.md sections beyond what the code comments quote, `src/compare_history.py` scoring code, `pools.ARRIVAL_DEFINITIONS` in full, the judgements files. Claims about those are marked *not verified*.

Numbers below are quoted from the code comment or file named beside them, with their window. "Coherent seat error" is the project's summed absolute seat error across parties from one consistent vote vector.

---

## Summary

The plan has the right shape: rolling origin by cycle, settings refit per target, a sealed 2026 forecast, and the census as a labelled ex-post covariate. It has four defects that would each let a later result into a backtest that is then published as clean:

1. **Its list of settings is the owner's six-row table, not the model's parameter set.** At least six further constants in source were chosen or measured with 2016 or 2021 results in view and are in no register (table under Q1).
2. **Step 4 refits three scenario keys but not the width record**, whose 2016 and 2021 widths are fitted on residuals about centres produced with the contaminated level shrink and spine k. Step 4 as written would publish a score that still reads 2016 and 2021 through the widths.
3. **The step 3.3 audit hook cannot be the proof.** It sees file opens, not constants, not how a precomputed artefact was derived, and not self-declared `period_end` labels. And the census exception, as the code implements it, opens the 2021 LGE result file at every earlier target, so the hook must either fail every run or whitelist a result file.
4. **Step 0 does not meet "exactly zero chance they are read".** It quarantines a named list of files; the in-sample figures also sit in backtest outputs it omits, in committed documents and code comments (213 files under `src tests *.md audits prereg reports` match "coherent" and 181 match "city-years"; 13 auto-memory files match `coherent|city-year|backtest`; grep, 2026-10-23). These counts are upper bounds on files quoting a panel score, since the patterns also match files that only mention one.

The ordering also needs to change: step 5.1 depends on steps 1–3, which depend on IEC and Stats SA requests that cannot complete by 4 November. The 2026 forecast should be frozen on the current settings, which are legitimate for 2026 (`POLLSTER-ON-RECORD.md`), and the full chain is a post-election deliverable.

---

## Answers to the plan's six questions

### 1. Is anything still in-sample, or any clean input wrongly excluded?

**Still in-sample (not in the plan).** Each is a constant in source, so neither the registers (which enumerate `montecarlo.DEFAULTS` keys only) nor the audit hook (which sees files) can see it.

| Constant | Where | What it read | Targets reached |
|---|---|---|---|
| `SPLINTER_PARENT_WEIGHT = 0.35` | `src/pools.py` | "fitting each splinter's vector at its first election … over 22 metro-cases gives a median of 0.35 — EFF 0.89, GOOD 0.28, ActionSA about 0.02" (code comment). ActionSA's first election is LGE 2021. `splinter_parent_weight` returns the literal unless a judgements entry overrides it; it does not re-derive per target. | Every target that reads the default weight. The leak is the single literal: its median over 22 cases includes GOOD (first election NPE 2019) and ActionSA (LGE 2021), so a 2016 or 2021 target reads a value computed with post-target cases in it, whichever splinter it is applied to |
| `SD_FLOOR = 0.15` | `src/levels.py` | Kept after the derived bias correction "makes the model worse, measured over nine city-years at 600 draws: coherent seat error 258 -> 268" (code comment). Typed, then confirmed on the panel: class 2 of `POLLSTER-ON-RECORD.md`. | All |
| `RHO_ANCHOR_LO = 0.00548`, `RHO_ANCHOR_HI = 0.0224` | `src/montecarlo.py` | "The geometric centres of the two groups' rows in the 2026 record" (code comment). The 2026 record is fitted on 2011–2021. | 2016, 2021 (universal draw) |
| `LOCATION_CLAMP = 0.00016` | `src/montecarlo.py` | "the record's 1st-percentile centre" (code comment); which target's record is not stated. *Not verified.* | 2016, 2021 if from the 2026 record |
| `--w-recency 0.70`, `--kappa-bye 0.25` | `src/turnout.py` defaults | Typed from the plan ("range 0.50-0.90"). Undefended rather than leaked; the plan's authors knew the 2016 and 2021 turnout drop. | All (`w_recency`); `kappa_bye` none at past targets (no per-target by-election turnout file) |
| Curated event lists: `levels.TYPE_A_EVENTS`, `KNOWN_ABSENT`, `DEMARCATION_CROSSING`, `THETA_EXCLUDE_TARGETS`, `HELD_BACK`; `pools.SPLITS`, `MERGERS`, `ARRIVAL_DEFINITIONS` | `src/levels.py`, `src/pools.py` | Filtered by target year at read time (for `SPLITS`, enforced in code). *Which* events are listed, and which records are excluded, was decided with the whole record in view. | All |
| `plan_bounds`, `entrant_geography` | `backtest.FITTED_ON` | Already registered with years 2006–2021; the plan's 3.1 list omits them. | All |

`montecarlo.MODULE_CONSTANTS` already enumerates the module constants each run records (17 in `montecarlo`, 16 in `levels`, by count of the tuple entries read on 2026-10-23), and the comment block "DELIBERATELY NOT DECLARED" below it lists the artefact-borne constants read only at emit time (`pools.SPLINTER_PARENT_WEIGHT`, `SPLITS`, `MIN_HOME_SPLITS`, the `ALPHA_*` constants, `fold.SHARE_FLOOR`/`LEVEL_FLOOR`, everything in `turnout.py`). Together these are the population for 3.1: every entry in both, plus every key in the four `backtest.py` registers, gets a provenance class (fitted on results / typed then confirmed on the panel / mechanism or statute / numerical). `RHO_ANCHOR_LO/HI` and `LOCATION_CLAMP` are in neither list as read; the completeness guard that runs DEFAULTS → registers should be extended to all module-level constants in `montecarlo`, `levels`, `pools`, `fold`, `turnout` and `width_record`, so a constant absent from both lists turns the suite red.

**Structural selection.** One concrete instance: the `GAMMA_FOLD` comment in `montecarlo.py` records "fit on fold 1, validate on fold 2", fold 2 being 2019→2021. The 2021 target reads fold 1's values (clean), but γ's form was validated on 2021. Step 3.2's classification should name it. More generally, the model's form was chosen over more than two hundred iterations judged on the same panel (`POLLSTER-ON-RECORD.md` §3). Refitting constants removes the constants' leak and not this one (Leamer 1983, high confidence; Lauderdale & Linzer 2015, high). No step of the plan removes it; only the sealed 2026 score does. The page that publishes the re-scored panel must say so where the score is printed.

**The width record inside the backtest.** `width_record.py` fits each target's widths on earlier cycles (`FORWARD = {"2016": ("2011",), "2021": ("2011", "2016")}`), but the residual `r_i` is the realised share minus `montecarlo.pool_spec_centres`, and the centres come from `run_model(..., stop_after="drawer_inputs")` under DEFAULTS, which applies `compress_levels` (montecarlo.py line 3045) with the level shrink fitted on 2016 and 2021, and the spine with k of unsettled provenance. So the 2016 widths read 2011 residuals about centres shaped by 2016 and 2021 results. Step 3.4 rebuilds the record from the chain and fixes this; step 4 does not (see Q6).

**Clean inputs wrongly excluded or at risk of exclusion.**

- **The target's own pre-election facts** (certified roll per VD, ward ballot lists, VD→ward delimitation, council size) are clean and must stay in. As implemented they are read out of the target's result file, which a file-level hook will reject. The fix is in Q5.
- **2016–21 by-elections at the 2021 target** are clean (dated 2016-11-09 to 2021-05-19, `INVENTORY.md`) and the 2026 forecast uses the by-election channel, so the 2021 backtest should too for parity. Two conditions, neither in the plan: (a) the gate `GATES['bye_deltas_absent']` is opened deliberately and the `NOT_FITTED["w_bye"]` reasoning ("its evidence window POST-DATES every past target") is rewritten, since it becomes false; (b) `src/bye_value.py` is made target-aware first. It is hard-wired to `BASE_LGE, BASE_NPE = "2021", "2019"` with outcome NPE 2024, so reading the current `bye_value.json` at a 2021 target imports the 2024 result. At 2021 the analogue would be 2016–19 contests against NPE 2019; Johannesburg's last 2016–21 contest is 2019-07-24 (`INVENTORY.md`), so the Johannesburg sample is the 12 contests dated 2017-04-05 to 2019-07-24, of which those before 2019-05-08 predict NPE 2019.
- **Census 2001 by ward** is the clean covariate for the 2006 and 2011 targets and is not requested. Census 2011 (enumerated October 2011, first results released October 2012; high confidence on the month of enumeration, medium on the release month) post-dates LGE 2011 (18 May 2011), so it is ex-post at a 2011 target and clean at 2016 and 2021. Step 1.7 should request 2001 and 2011 together.
- **Community Survey 2016** (Stats SA): municipal-level population group, released before LGE 2016 by my recollection (June 2016; low-medium confidence). Not ward level, but it would give a clean citywide composition check for the 2016 target. Worth one line in 1.7.

### 2. Is the census the only acceptable exception?

**Yes, as an exception.** Everything else the literature accepts is not an exception but ordinary pre-election information: nomination lists, the certified roll, the delimitation, the party register, and polls with machine-readable fieldwork dates before polling day. The real-time data literature requires the vintage available at the origin (Croushore & Stark 2001, high confidence); the ex-ante/ex-post distinction allows a realised covariate only when the score is labelled ex-post and is read as a test of structure, not of forecast accuracy (Hyndman & Athanasopoulos 2021, high; Clements & Hendry 1998, medium). The 2024 roll at a 2021 target is correctly refused.

Two corrections to the plan's definitions:

1. **"Clean input: … period ends strictly before polling day, *or* published before it" must be AND.** A table whose reference period ended before the target but which was published after (Census 2011 at a 2011 target is the live case) was not available to a forecaster. The test is: the information was public before polling day. Nomination lists and the roll satisfy both conditions; the census does not and is the declared exception.
2. **The census exception must be defined to include what it needs to join.** `pools.composition_at` reprojects Census 2022 (2021 delimitation) onto an earlier target's wards through `pools.reproject`, which calls `vd_map(city, "2021")`, which reads the 2021 LGE result file for its VD→ward map. The VD→ward map is a delimitation fact, published before 2021; the vote columns in the same file are not. The exception should read "Census 2022 ward composition and the 2021 VD→ward delimitation used to place it", and the delimitation should be extracted to its own file so nothing else in the 2021 result file is opened (Q5).

**Persons, not voters.** Census counts persons of all ages and citizenship; voters are registered adult citizens, and registration rates differ by group. This is a property of the covariate at every target including 2026, not part of the exception, and belongs in `DATA-QUALITY.md` with the Census 2022 undercount. I recall the post-enumeration survey put the net undercount at about 31% nationally (low confidence on the figure, as on record); a group-differential undercount biases composition independently of timing.

### 3. Is 2.3 (fixed 2022 composition) acceptable, and how should it be labelled?

**Acceptable for description, with two labels; not acceptable as a measured group behaviour change.**

Holding composition at 2022 for every pair means any change in a ward's composition between the pair's two elections is attributed to a change in group behaviour. Johannesburg's population grew between censuses and the growth was concentrated (informal settlements, new suburbs), and those are the wards where turnout and shares moved. So a fixed-composition ecological estimate of "group X's change" is composition change plus behaviour change, not separable on this data.

Labels, at the point each number appears:

- "ecological estimate; aggregate data do not identify individual behaviour" — and report the Duncan–Davis bounds beside every point estimate (Duncan & Davis 1953, high confidence; the argument for bounds over point estimates is King 1997 and the critique of treating EI point estimates as known is Freedman et al. 1998, both high).
- "composition fixed at Census 2022; change includes composition change since the pair's first election (N years before the census)". For pairs ending before Census 2022 fieldwork (February 2022), add "ex-post input".

Once Census 2011 arrives, pairs ending by 2016 use it, and the 2016→21 pair can be bracketed by running it on 2011 and on 2022 composition: the difference is the measured size of the fixed-composition error for that pair.

### 4. Is the threshold approach in 2.1 sound, or should polygons come first?

**VD linking first; polygons are not a prerequisite.** VDs are the electoral atoms, every result file maps them to its own wards, and `fold.py`'s comment records VD identifiers as stable back to 1999. Registration-weighted VD linking is areal interpolation with population weights, which is more defensible for electoral data than area weighting of polygons (Goodchild & Lam 1980, medium confidence; Tobler 1979's pycnophylactic interpolation, medium). Polygons only help the VDs the VD join cannot place (the Johannesburg concordance has 79 unmatched VDs, `INVENTORY.md`), and historic VD polygons are not published (`INVENTORY.md`), so polygon overlay would be ward-on-ward area weighting, which is worse.

Conditions:

1. **Reuse `pools.reproject`.** It already does registration-weighted VD linking and returns the mapped fraction. A second implementation in step 2 is a duplicated definition (project rule) and would let step 2's tables and the model's pools disagree about which ward a VD is in.
2. **Declare the threshold before the run**, in `JUDGEMENT-CALLS.md`, with the precedent stated: `pools.CENSUS_COVERAGE_FLOOR = 0.80`, whose comment calls it "A CHOSEN NUMBER, NOT A MEASURED ONE". The plan says "a stated threshold" and states none.
3. **Report the distribution of linked shares for every pair**, not only the count below the threshold, and repeat the headline tables at a second threshold. A one-sided threshold ratchets.
4. **VD numbers are matched by number or station name, without geometry** (`INVENTORY.md`), so a reused VD number linking two different places passes silently. Report per pair how many links rest on name rather than number.
5. **Step 1.4 has an error.** NPE 1999 has no preceding LGE on disk; its VDs must take LGE 2000's VD→ward. That is geography, not a result, but it is the *following* election's delimitation and the row should say so.

### 5. Is the 3.3 audit hook sufficient proof, and what would it miss?

**No. It is a necessary tripwire, not a proof.** It misses:

| Gap | Example in this repository |
|---|---|
| Constants and curated dicts in source | `SPLINTER_PARENT_WEIGHT`, `SD_FLOOR`, `RHO_ANCHOR_*`, `SPINE_K`, the event lists (Q1 table) |
| Precomputed artefacts whose derivation read later data, though the artefact's own label is clean | `pools_*.json` emitted by code carrying `SPLINTER_PARENT_WEIGHT`; `width_record.json` (residuals about contaminated centres); `fold*_parameters.csv` (`theta_calibrated` column, calibration source *not verified*) |
| `period_end` is self-declared metadata | A mislabelled artefact passes. A derived table's `period_end` must be computed as the maximum over its inputs, by the code that writes it, not typed |
| File-level granularity | The target's result file must be opened for roll, ballot lists and delimitation; the 2021 file must be opened for the census reprojection. Either the hook fails every run or it whitelists result files, which defeats it for the files that matter most |
| In-process caches | A module-level cache filled by a later target in the same process is not reopened. `CLAUDE.md` already records that the suite imports in-process |
| Opens outside `builtins.open`/`os.open` | C-level readers (sqlite3 has its own audit event; pyarrow and other C readers may not raise `open`) |
| Environment switches | `HELD_BACK_OFF`, `FILTER_TYPE_A`, `THETA_WINDOW`, `--retrospective-home` |
| Model structure chosen on the panel | No mechanism can see it (Q1) |

**What makes it a proof.** Three things together:

1. **Pre-election extracts.** For each target, write `data/pre_election/<city>/<year>/` from the result file once, by a reviewed script: roll per VD, VD→ward, ward ballot presence, council size. Extract every delimitation's VD→ward map to its own file. The run then opens no result file at or after its target, and the hook runs with no whitelist except the census and the 2021 delimitation file. Scoring (`compare_history`) runs in a separate process after the forecast artefacts are written and hashed.
2. **Regeneration in an isolated tree.** For each target, a fresh checkout whose `data/raw` holds only files dated before the target plus the census and the delimitation extracts; every artefact (specs, turnout, folds, width record) is rebuilt there, one process per target, under the hook. If a later file is needed, the build fails with a missing file rather than reading it. This is the project's own rule ("regenerate, don't grep") applied to provenance. Run `src/backup_ignored.py` first.
3. **The four-part absence test** (`CLAUDE.md` §4): state the population of files each run may open; assert the hook saw a non-empty set within a two-sided bound; plant a violation (a 2016 run that opens `lge2021_JHB_vd_party_clean.csv`) and see it fail, then revert and see it pass; and build the planted case, not observe it.

Constants get no mechanical proof. Each one in the extended register carries its provenance class and, for anything fitted or panel-confirmed, a target-aware recomputation or a declared value with bracketing arms.

### 6. Step 4: worth publishing, or misleading while step 3 is pending?

**Worth running; publish only with its remaining in-sample parts listed on the page, and not as "out-of-sample".** As written it refits three scenario keys (turnout correlation, level shrink and scale, spine k). It leaves in-sample: the width record for 2016 and 2021, the constants in the Q1 table, the draw-law choice, and model structure. Published as "settings from earlier elections only", it would repeat the error the owner is correcting.

Two changes make it honest and still feasible before the freeze:

1. **Rebuild the width record per arm.** Spine k, level shrink and turnout correlation are run-time scenario keys (`montecarlo.py` resolves `spine_k` at line 7051; `compress_levels` runs in `run_model`), so step 4 needs no pools re-emit. The width record does need rebuilding with the refit settings, into a directory outside `data/` (`width_record.py --out DIR` with the width override; memory note "Width record: --emit beats --out" says `--emit --out` writes `data/`).
2. **Publish the old and new scores side by side** (`POLLSTER-ON-RECORD.md` §4.2) with the three-class table on the page. The gap between them is the measured optimism of the in-sample figures for the three keys; the page says that the remaining items are not yet refit.

If (1) cannot be done before the freeze, run step 4 internally and publish only the withdrawal notice and the sealed-forecast hash.

---

## Anything else that would let a target or later result into a backtest

| Path | How the result gets in | Fix |
|---|---|---|
| `pools.reproject` → `vd_map(city, "2021")` | Opens the 2021 LGE result file at every earlier target to place Census 2022 | Extract the 2021 delimitation to its own file; narrow the exception to it (Q2) |
| `montecarlo.read_width_record` at 2016/2021 | Widths fitted on residuals about centres compressed by a shrink fitted on 2016+2021 | Rebuild from the chain (3.4) and in step 4 |
| `pools.SPLINTER_PARENT_WEIGHT` | Median over 22 metro-cases including ActionSA 2021 | Make target-aware: fit on splinters whose first election precedes the target; at 2011, declare |
| `montecarlo.RHO_ANCHOR_LO/HI`, `LOCATION_CLAMP` | Taken from the 2026 record | Read from the target's own record in `width_record.json` |
| `levels.SD_FLOOR` | Retained on a nine-city-year comparison | Declare and bracket per target, or refit inside the rolling origin |
| `bye_value.py` / `bye_value.json` | Hard-wired to 2021 base and NPE 2024 outcome; harmless only while the gate keeps by-elections out of past targets | Target-aware before 2.5's by-elections enter any backtest |
| Arrivals seeded by name (`pools.ARRIVAL_DEFINITIONS`; gate `arrivals_are_named`, open at 2011 per `backtest.py`) | At 2016 and 2021 the model is told which new party arrives. Presence is clean (nominations). Size is not: `entrant_share` is "a check against the AIC's 1.62% in 2016 and against ActionSA in 2021" (`backtest.py` register) | 3.1 must separate arrival presence (clean, from nominations) from arrival size (refit or declared per target) |
| Curated event lists (Q1) | Chosen seeing outcomes | Each entry carries the dated source that made it knowable before the target; entries without one are listed as judgement |
| `data/processed/fold*_parameters.csv` `theta_calibrated` | Calibration source not verified | Check what calibrates it; `gamma_fold_for` checks the fold, not the calibration |
| `data/processed/party_crosswalk.csv` | Party identity across names, built in 2026 | Clean if each mapping is a pre-target fact (registered name change, merger notice); spot-check the splinter and merger rows |
| Step 1.9 and the inventory's inconsistency 5 | "ActionSA 6.22% on the 2024 national ballot" is a provincial-ballot figure (*inferred*) | Not a leak at a backtest target; a wrong label on a 2026 input. Fix with 1.2 |

---

## Do the step 2 measurements answer the owner's request as written?

The owner asked (item 29): complete national, provincial, local and by-election results for the eight metros; every pair local–local, national–local, local–national at city and ward level, for vote, turnout and population-group variation; per-party shrink, vote change and turnout change for every ward in every pair, with the exact reason where it cannot be done; how the changes themselves change; every by-election against the elections before and after it and its correlation with the next; and the backtest from data dated before each election only. Item 28 adds "if every party % shrinks where do the missing % of votes go?" and "how is the cap applied?"

Covered: the pair list (2.1), per-ward per-party share and ratio (2.1), turnout and registration change (2.1), second-order change (2.4), by-elections both directions with the next-election correlation (2.5), the reason for each blank cell (2.6).

Missing or wrong:

1. **National vs provincial is not specified.** The owner named both; only the provincial ballot is held (`INVENTORY.md`), and 1.1/1.2 add the national. Step 2 should run every national→local and local→national pair on both ballots and report which predicts the local result better on pre-target pairs only. That is estimation of a property of the world, so it is permitted, and it settles which ballot the model's national route should read.
2. **"Vote change" is not in 2.1.** 2.1 lists votes and shares; the owner asked for per-party vote change, which is the quantity that answers item 28's question. Add Δvotes per party per ward.
3. **2.2 answers item 28's question in the wrong unit.** Shares sum to one at both elections, so they cannot all shrink; the question only has an answer in votes. Decompose each party's vote change per ward into registration change, turnout change and share change (an exact additive split such as the Shapley decomposition of votes = registered × turnout × share). Then "where the missing votes go" is: into abstention, read off the turnout term. Attribution of share lost by one named party to another named party is not identified from aggregate data; 2.2 can report net flows and bounds, and must say that gross party-to-party flows are an ecological estimate (Duncan & Davis 1953; King 1997).
4. **"How is the cap applied?" is not answered anywhere in the plan.** It is a factual question about the existing by-election cap (`bye_local_cap`, read in `src/montecarlo.py`, registered in `src/backtest.py`). The answer belongs in the plan or in `OWNER-DECISIONS.md` with the code path.
5. **By-election turnout change cannot be computed from what is held.** The by-election files carry no registered, spoilt or votes cast (`INVENTORY.md`); 1.5 is a prerequisite for that cell and 2.5 should say so.
6. **Population-group variation (2.3)** needs bounds and the composition label (Q3), and the 2001 and 2011 censuses as the covariate for the pairs they precede.
7. **Every table needs `period_end` computed from its inputs**, so the backtest's loader can refuse it mechanically; 2.1 says "each row carrying the pair and its period_end" but not how it is computed.
8. **National→national pairs** were not asked for and are not needed for the backtest. They would measure national trend, which the spine's θ route assumes; leave them out unless the owner asks.

---

## Order of work, given polling day 4 November 2026 and today 23 October 2026

The fixed point is the sealed 2026 forecast. It is the only clean out-of-sample number this model will have, and it can be taken only once. Special votes are cast in the two days before polling day (my recollection of IEC practice; confirm the 2026 timetable), so the hash should be published before special voting opens.

| When | Work | Why here |
|---|---|---|
| 23–24 Oct | Send the Stats SA request (Census 2001 and 2011 by ward, population group) and test the IEC dashboard for pre-2016 by-elections (1.5, 1.7) | Third-party lead times; nothing else depends on them before the election |
| 23–26 Oct | Step 0 in this order: retire the `backtest_*` tokens and the pages that print them (`src/stats.py` builds them from `history.json`, so quarantining first breaks the build); then quarantine the data outputs; then the MODEL-LOG entry, the memory note and the label test (changes 8–11 below). Ship 6.1 with the pending tooltip release | Removes the risk the owner named; the page needs a withdrawal notice before polling day |
| 24–29 Oct | Step 4 with the width record rebuilt per arm, pre-registered; publish only as Q6 says | No pools re-emit needed; feasible in the window |
| 24–29 Oct | 6.3 (ActionSA retention) only if the QC §4c old-vs-new report reaches the owner by 29 October; otherwise after the election | It moves the forecast; nothing moves after the freeze |
| by 31 Oct | Freeze code, settings, specs and inputs; run `src/inputs_preflight.py --strict`; publish the dated hash (5.2) | Before special voting; the freeze runs on current settings, which are legitimate for 2026 |
| after 4 Nov | Score the frozen forecast and publish it whatever it shows | The clean number |
| after 4 Nov | Steps 1, 2, 3 for Johannesburg; then 5.1's chain-derived settings for the next forecast; then the other metros | 5.1 as written needs step 3, which needs 1–2 and the third-party data |
| after 4 Nov | 6.2 (DA scenario) | Presentation, not a forecast input; nothing blocks on it |

---

## Changes to the plan

1. **Definitions, "Clean input":** replace "or published before it" with "and public before polling day". Add: a derived table's `period_end` is computed by the code that writes it as the maximum over its inputs.
2. **Definitions, "Exception":** extend to "Census 2022 ward composition, and the 2021 VD→ward delimitation used to place it on earlier wards". Add "Census 2011 is ex-post at a 2011 target and clean at 2016 and 2021; Census 2001 is clean at 2006 and 2011".
3. **Step 3.1:** replace the list of settings with "every entry of `montecarlo.MODULE_CONSTANTS`, every constant in its DELIBERATELY NOT DECLARED block, every other module-level constant in `montecarlo`, `levels`, `pools`, `fold`, `turnout` and `width_record`, and every key in the four `backtest.py` registers, each classified as fitted on results / typed then confirmed on the panel / mechanism or statute / numerical". Name at least `SPLINTER_PARENT_WEIGHT`, `SD_FLOOR`, `RHO_ANCHOR_LO/HI`, `LOCATION_CLAMP`, `plan_bounds`, `entrant_geography`, `turnout.py`'s `w_recency` and `kappa_bye`, and the curated event lists. Extend the completeness guard from DEFAULTS → registers to all module-level constants in those modules → registers.
4. **Step 3.1:** separate arrival presence (clean, from nominations) from arrival size (refit per target or declared).
5. **Step 3.3:** replace "Mechanical proof" with three parts: pre-election extracts per target and per delimitation, so the run opens no result file at or after its target; regeneration of every artefact in an isolated tree per target, one process per target, under the hook; a planted-violation test that fails, then passes when reverted. State that constants have no mechanical proof and are covered by change 3.
6. **Step 3.4:** add "`bye_value.py` is made target-aware, and the `w_bye` register reasoning rewritten, before any by-election enters a backtest; at 2021 the weight is fitted on 2016–19 contests against NPE 2019 or declared".
7. **Step 3.5:** add the Murphy (1992) optimal combination of persistence and climatology as a baseline beside uniform swing and persistence (high confidence on the paper; medium on the exact title), headline on a proper score (CRPS; Gneiting & Raftery 2007, high), and print beside each score the number of alternatives tried for each score-chosen decision (White 2000, high).
8. **Step 0.1:** add `data/processed/<city>/2016|2021/seat_draws.csv`, `ward_winner_probs.csv`, `coalition_*.csv`, `regime_*_seat_draws.csv`, `width_budget.json`, and the `prereg/` and `audits/` score tables. Order: retire tokens and pages first, quarantine second.
9. **Step 0.2:** put the quarantine outside the repository (an agent's grep reaches a gitignored folder inside it). As worded, the plan's test ("fails if any code path … references a quarantined file") would forbid `compare_history` from writing `history.json`, which step 4 needs. The test must forbid reading the quarantined copy or printing an unlabelled score, not the filename. The new test asserts that any backtest score printed on a page or held in a token carries a label naming it in-sample or forward-chained, and that no token reads a quarantined path; it is built with a planted unlabelled score that fails.
10. **Step 0, new item:** state the population of committed text that quotes in-sample figures (the grep counts in this review's summary, re-run at implementation), and state it as an upper bound, refined by a grep for digits beside those terms, and handle it by a single banner at the top of `MODEL-LOG.md`, `JUDGEMENT-CALLS.md` and `POLLSTER-ON-RECORD.md`, not by editing entries. Code comments that justify a constant by a panel score are tagged at the constant when change 3 reclassifies it.
11. **Step 0, new item:** add an entry to the auto-memory index and a superseding MemPalace KG fact (`kg_invalidate` then `kg_add`) saying that every backtest score dated before 2026-10-23 is in-sample. 13 memory files match `coherent|city-year|backtest` (grep, 2026-10-23, an upper bound); the population is stated at implementation by a grep for digits beside those terms.
12. **Step 0.3:** remove "Per the owner, no corrections entry is required for the withdrawal itself". Item 30's "no corrections entry" answered the tooltip question, where no published figure was wrong. Item 26's answer is "post corrections" for each error that was live. The published backtest figures were live statements of out-of-sample accuracy that were wrong, so item 26 applies: a corrections entry in the agreed format, unless the owner says otherwise. If the author reads it differently, put it to the owner in `OWNER-DECISIONS.md`.
13. **Step 0.5:** restate the reason. For the 2026 forecast the width record is not a leak (all its inputs pre-date 2026); it is optimistic, because it is fitted on residuals about in-sample centres, so its widths are likely too narrow. The page wording should say that. Keep it live.
14. **Step 1.4:** NPE 1999 takes LGE 2000's VD→ward (the following election), labelled.
15. **Step 1.7:** request Census 2001 and 2011 by ward together; add Community Survey 2016 at municipality level as a clean citywide check for 2016.
16. **Step 2.1:** add per-party vote change; reuse `pools.reproject` for ward linking; declare the link threshold in `JUDGEMENT-CALLS.md` before the run; report the distribution of linked shares and a second threshold; report links resting on station name.
17. **Step 2.2:** decompose vote change into registration, turnout and share terms; report net flows and Duncan–Davis bounds; label gross party-to-party flows as ecological estimates.
18. **Step 2.3:** add bounds beside point estimates and the composition label (Q3); use Census 2001/2011 for the pairs they precede once held.
19. **Step 2, national/provincial:** run every national↔local pair on both ballots; report which predicts the local result better, on pre-target pairs only.
20. **Step 2.5:** state that by-election turnout needs 1.5's registration and votes-cast fields.
21. **Step 4:** add the width-record rebuild per arm, outside `data/`; publish old and new side by side with the remaining in-sample items listed; do not call it out-of-sample. If the rebuild cannot finish before the freeze, publish only the withdrawal and the hash.
22. **Step 5.1:** move after polling day. The frozen 2026 forecast runs on the current settings.
23. **Step 5.2:** freeze and publish the hash by 31 October, before special voting; run `inputs_preflight.py --strict` before freezing.
24. **Step 6.1:** use the owner's text in full; the plan drops his third sentence. It is: "This Model expects a median of 1,013,993 votes on each ballot, so 490,000 is 48%. The DA reaches 490,000 on both ballots in 0 of 5,000 simulations. If the DA did in fact win 48% that would take some of the ANC's wards." The two figures come from `stats.toml` tokens, not typed.
25. **Step 6.2:** pre-register a feasibility check first: whether turnout in the DA's strongest groups can reach 490,000 DA votes on each ballot at turnouts at or below the highest on record for those VDs (`turnout.py`'s `thi_pattern`). If it cannot, the scenario needs a share shift as well, and the page says so.
26. **Step 6.3:** state the sample: parties with a first and a second local election both by 2021 (by my count COPE, NFP, AIC, EFF; *not verified* against the files), across eight metros, so the effective sample is the number of parties, not party-metros; report the spread per party, cluster by party, and do not report a single median for a bimodal record. Answer the owner's "how is the cap applied?" in the same item.
27. **"Order and what blocks what":** replace with the table above.

---

## Rejected claims

| Claim | Why rejected | Evidence |
|---|---|---|
| The audit hook on `open` proves a run read nothing from the target or later | It does not see constants, artefact derivations or self-declared labels, and the census reprojection must open the 2021 result file | Q5 table; `pools.reproject` |
| Step 4 uses only data from earlier elections | The 2016 and 2021 widths are fitted on residuals about centres compressed by a shrink fitted on 2016 and 2021 | `width_record.py` docstring; `montecarlo.py` line 3045 |
| The width record contaminates the live 2026 forecast | Every input pre-dates 2026; the defect is optimism (narrow widths), not leakage | `width_record.FORWARD["2026"] = ("2011", "2016", "2021")` |
| Polygons must come before ward linking | VDs are the electoral atoms and historic VD polygons are not published; polygon overlay would be area-weighted ward-on-ward, which is worse | `INVENTORY.md` boundary links |
| The owner waived a corrections entry for the withdrawal | Item 30 is about tooltips, where no figure was wrong; item 26 asks for corrections of each live error | `OWNER-DECISIONS-ANSWERED.md` items 26 and 30 |
| 5.1 can deliver chain-derived 2026 settings before the freeze | It needs step 3, which needs steps 1–2 and Stats SA and IEC data | Plan's own dependency order |
| A median second-election retention measures ActionSA's expected retention | The pre-2021 new parties include collapses and growth; a median of a bimodal record over a handful of parties is not a forecast for a city-based party with a mayoral leader | Plan 6.3; owner item 28 |

---

## Sources and confidence

Already on record in `POLLSTER-ON-RECORD.md` with their confidence: Tashman 2000; Hyndman & Athanasopoulos 2021; Clements & Hendry 1998; Croushore & Stark 2001; Leamer 1983; White 2000; Lauderdale & Linzer 2015; Gneiting & Raftery 2007.

Added here:

| Source | Used for | Confidence |
|---|---|---|
| Duncan, O.D. & Davis, B. (1953). An alternative to ecological correlation. *American Sociological Review* 18(6). | Bounds on group behaviour from aggregate data | High |
| King, G. (1997). *A Solution to the Ecological Inference Problem*. Princeton. | Bounds plus a model; EI as estimate, not measurement | High |
| Freedman, D.A., Klein, S.P., Ostland, M. & Roberts, M.R. (1998). Review of *A Solution to the Ecological Inference Problem*. *JASA* 93(444). | EI point estimates treated as known understate uncertainty | High on the critique, medium on the citation details |
| Murphy, A.H. (1992). Climatology, persistence, and their linear combination as standards of reference in skill scores. *Weather and Forecasting* 7(4). | The optimal persistence–climatology baseline | High on the result, medium on the exact title |
| Goodchild, M.F. & Lam, N.S-N. (1980). Areal interpolation: a variant of the traditional spatial problem. *Geo-Processing* 1. | Population-weighted areal interpolation | Medium |
| Tobler, W.R. (1979). Smooth pycnophylactic interpolation for geographical regions. *JASA* 74(367). | Areal interpolation alternatives | Medium |
| Stats SA release dates (Census 2011 results October 2012; Community Survey 2016 mid-2016) | Which census was public before which target | Medium on Census 2011, low-medium on CS 2016; check before citing |
