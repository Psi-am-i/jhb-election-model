# Step 4 stop gap: specification

**Status:** specification for review. Nothing here has been run. Written read-only at `99556398` (branch `site-sweep-1`) on 2026-10-28, with another agent's uncommitted wording edits in `src/` (see §0).
**Plan:** `rounds/2026-10-23-out-of-sample/PLAN.md` Step 4, Definitions, Step 3, Order. **Pollster:** `POLLSTER-ON-RECORD.md` in this directory.
**Pre-registration:** `PREREG-DRAFT.md` beside this file, which must be reviewed blind and committed under `prereg/` before any fit or run below.

What the stop gap does, in one line: for each target T in 2011, 2016, 2021, the four settings Step 4 names are set from data before T (or declared, where there is too little), the universal draw's width record is rebuilt per target outside `data/`, and all 24 backtest rows are run twice on one tree (current settings and stop-gap settings) and scored by the same instrument. It never re-emits a pool spec and writes nothing under `data/`.

---

## 0. Preconditions found while writing this

| # | Finding | Evidence | Consequence |
|---|---|---|---|
| P1 | The live width record is current against the settled wording edits. | Re-checked 2026-10-29 after the wording writer reverted its key-moving edits: `M.width_record_key()` equals `data/processed/width_record.json`'s `artefact_key` in every field (0 differ); `pools._code_sha` of HEAD against the working tree is the same for `montecarlo.py`, `theta_residual.py`, `levels.py`, `pools.py`, `compare_history.py`, `width_record.py`, and differs only for `benchmarks.py` and `turnout.py` (message strings), which no artefact key hashes. The earlier reading of this row (montecarlo and theta_residual differing) was taken mid-edit. | None for the stop gap beyond P2. The OLD arm still rebuilds its record outside `data/` so both arms are built the same way. |
| P2 | The stop gap must run on a settled tree. | CLAUDE.md §3; `width_record_key` hashes `montecarlo.py`, `levels.py`, `width_record.py`, `compare_history.py` and `theta_residual.py` (montecarlo.py:3922-3932). | Order: the wording edits are committed, then this spec's code changes are committed, then every record is built, then rows run. Any `src/` edit after a record build stales it. |
| P3 | `data/processed/history.json` is still on disk (generated 2026-10-19T07:52:44Z, `git_commit` a9754ede, `git_dirty` true, 24 rows, 1000 draws, seed 20261104). | Its `manifest`; MODEL-LOG §1.337 says the originals stay in the project. | It is the readable source of the old scores (§7). It must never be opened by a fit or a row (§5 denylist). |

---

## 1. The 24 rows and the harness

### 1.1 Enumeration

- Cities: `compare_history.CITIES` (compare_history.py:117): joburg, tshwane, ekurhuleni, ethekwini, capetown, mangaung, nelsonmandelabay, buffalocity.
- Years per city: `compare_history.runnable(city)` (compare_history.py:241), which filters `backtest.runnable_targets(city)` (backtest.py:89) by a pool spec on disk and a γ fold file. All 8 × {2011, 2016, 2021} are runnable today: `history.json` holds 24 records.
- The loop that builds the job list: compare_history.py:4445-4453.
- `arms.population` (arms.py:271) enumerates the same set from `compare_history.CITIES × arms.BACKTEST_YEARS` (arms.py:118), plus Johannesburg 2026, which the stop gap does not run.

### 1.2 Which harness

`compare_history.run_city_year` (compare_history.py:1718). It is the instrument that produced every withdrawn score (CRPS, coherent seats, list and ward error, the four reference forecasters, calibration, ward winners), so the old and new numbers come from one scorer. It calls `montecarlo.run_model` in process (compare_history.py:1734) and writes nothing itself; only its `main` writes, to `--json` and `--md` (defaults `data/processed/history.json`/`.md`, compare_history.py:4416-4417).

`arms.run_city_year` (arms.py:316) is not used for scoring: it computes none of compare_history's reference forecasters or coherent seats. `run_model` alone has no scorer.

### 1.3 What writes into `data/` today, and the redirect

| writer | default target | redirect |
|---|---|---|
| `compare_history.main` | `data/processed/history.json`, `history.md` | `--json OUT/... --md OUT/...` |
| `compare_history --run-dir` | none (opt-in trace) | `--run-dir OUT/...` |
| `run_model` reading the width record | reads `data/processed/width_record.json` (stale, P1) | `width_override` (montecarlo.py:5925, 7228-7236), via the change in §6 C1 |
| `width_record.py --emit` | `data/processed/width_record.json` | never `--emit`; build in process and write to `OUT` (§4) |
| `montecarlo.py` as a script | the city-year's forecast artefacts | never run as a script |

`OUT` is `rounds/2026-10-23-out-of-sample/stopgap/out/` or the session scratchpad; `arms.check_out` (arms.py:243) is the refusal for a path inside `data/` and the harness calls it.

### 1.4 How each row runs

One process per (arm, target), BLAS pinned to one thread (`VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`), `PYTHONHASHSEED=0`:

    .venv/bin/python src/compare_history.py --target T \
        --config OUT/settings/<arm>/T.json \
        --width-record OUT/width/<arm>/T/width_record.json \
        --trace-detail --run-dir OUT/trace/<arm>/T \
        --json OUT/scores/<arm>/T.json --md OUT/scores/<arm>/T.md --jobs 8

`--config`, `--width-record` and `--trace-detail` are the flags §6 C1 adds. The seed is `DEFAULTS["seed"]` (compare_history passes `seed=None`), so every arm is paired on one seed per row; draws 1000 (compare_history's default and `arms.BACKTEST_DRAWS`).

`load_scenario` (montecarlo.py, `def load_scenario`) copies `DEFAULTS` after `apply_city` has written the city TOML over it, then applies `--config`, then `--set`. So a settings file overrides `cities/joburg.toml:104-105` and `cities/tshwane.toml:143-144` (`entrant_prob`, `entrant_share`). Verified by reading the function.

### 1.5 The arms

| arm | rows | settings | width record |
|---|---|---|---|
| **OLD** | 24 | `DEFAULTS` as shipped (empty settings file) | rebuilt outside `data/` for 2011, 2016, 2021 with no overrides (P1 makes the live one unusable) |
| **NEW** | 24 | per target, §2-§3 | rebuilt per target with that target's settings (§4) |
| **B-c**, **B-k-lo**, **B-k-hi**, **B-rho-0**, **B-rho-1**, **B-ent-0**, **B-ent-hi** | 8 each (2011 only) | NEW-2011 with one declared value moved to a bracket (§2.5) | the 2011 fallback, which reads no centre (width_record.py:504); built once per bracket arm only so the file carries that arm's variant key (seconds) |

OLD against NEW on one tree and one seed isolates what the four settings and the width record are worth. The published figures sit beside them as a third column, labelled with their tree (§7).

---

## 2. The four settings

Population of "settings Step 4 names": `turnout_correlation`; `level_shrink` and `level_shrink_scale`; `spine_k`; and, at 2011 only, `entrant_prob` and `entrant_share`. All six are `DEFAULTS` keys, so every value is delivered through a scenario file and no module constant is touched.

### 2.1 One rule for "too little earlier data"

A setting is **fitted** at target T when its estimator has at least `N_MIN = 8` independent units strictly before T, where the unit is a metro-election (one metro at one earlier election; one full cycle of the eight metros is 8). Below `N_MIN` it is **declared**: it takes the value in §2.5's table, written in `JUDGEMENT-CALLS.md` before the run, the row is labelled "settings declared, not fitted", and bracketing arms are run. A fit on a single earlier cycle is labelled "fitted on one cycle". `N_MIN` is a judgement and goes in `JUDGEMENT-CALLS.md` (owner question Q2).

Every fit records, in `OUT/settings/<arm>/T.json`: the value; `n` (units); the elections read (computed by the fit code from the files it opened, never typed); the objective curve over the grid; and `derived_from` (the list of LGE years whose results it read), which `backtest.check_derived_from` (backtest.py:729) refuses if any year is ≥ T.

### 2.2 `TURNOUT_CORRELATION`

- **Defined:** montecarlo.py:793 (`TURNOUT_CORRELATION = 0.63`), copied into `DEFAULTS["turnout_correlation"]` at montecarlo.py:364 with an import-time equality assert at montecarlo.py:806. Read once per run at montecarlo.py:4497 and used as the Gaussian copula's common correlation across pool turnouts.
- **Fitted on:** "the mean off-diagonal correlation between pools' log turnout changes … over 14 metro-transitions (eight metros, 2011→2016 and 2016→2021)" (montecarlo.py:780-792; MODEL-LOG §1.30's calibration section at MODEL-LOG.md:1844; register `FITTED_ON_UNINSTRUMENTED["turnout_correlation"]`, backtest.py:436-447). No fitting code exists in `src/`. MODEL-LOG §1.71 (MODEL-LOG.md:7744) records it as stale and not re-measured.
- **Estimator.** For each metro and each pair of consecutive LGEs (a, b) with b < T: each pool's turnout rate at a and b, from `pools._pool_counts_or_loss(...).rates["turnout"]`, with the two exclusions `pools.panel_turnout_spread` applies (a pool held at the city fallback at either end; a rate within `_RATE_BOUND_EPS` of 0 or 1, pools.py:1036). The observation is the vector of four `log(t_b / t_a)`. ρ̂_T = the unweighted mean of the off-diagonal entries of the pairwise-complete Pearson correlation matrix across observations. **`N_MIN` for a matrix:** a pool pair with fewer than `N_MIN` aligned observations is dropped from the mean; if fewer than three of the six pairs remain, or the Black African pair set (the pool holding most of the roll) is empty, the setting is declared. Log, because that is the constant's stated definition; the logit version is reported beside it.
- **Why not reuse `panel_turnout_spread` directly:** it flattens moves per pool and discards which metro-transition each came from (pools.py:2776-2797), so a correlation cannot be read off it. Changing it moves `pools_sha` and stales every spec (CLAUDE.md §3). So the estimator lives outside `pools.py` (§6 C2), and a test asserts its count of pool-moves equals `panel_turnout_spread(cfg, before=T)[1]` at each T, so the two filters cannot drift apart unnoticed. Folding it into `pools.py` joins `POOLS-REEMIT-QUEUE.md` for the next batched window.
- **Available before each target (measured read-only, counts only, `panel_turnout_spread(cfg, before)[1]` on this tree):** 4 pool-moves before 2011, 34 before 2016, 64 before 2021. `pools.turnout_record(city, cfg, before="2021")` returns 2000, 2006, 2011, 2016 for Johannesburg and 2006, 2011, 2016 for the other seven. So:
  - **2011:** one metro-transition (Johannesburg 2000→2006). Below `N_MIN`: **declared**.
  - **2016:** about nine metro-transitions: Johannesburg 2000→2006 and the eight metros' 2006→2011. **Fitted on one cycle.**
  - **2021:** about seventeen: the above plus the eight metros' 2011→2016.
  The exact `n` per pool pair is whatever the fit records.
- **Estimation or tuning:** estimation. It is a property of turnout in the world, measured with no reference to any forecast. Caveats, stated where the value is published: pool turnout is an ecological fit on Census 2022 composition held flat (the declared ex-post exception), and Mangaung and Buffalo City's 2006→2011 transitions cross the 2011 demarcation (levels.py:604-607, off by default), which the fit keeps, as the model does, and reports without them beside it.

### 2.3 `compress_levels`: `level_shrink` (c) and `level_shrink_scale` (h)

- **Defined:** `compress_levels` at montecarlo.py:3181; values `DEFAULTS["level_shrink"] = 0.35`, `["level_shrink_scale"] = 0.04` (montecarlo.py:414-415). Applied as the last step of `blended_centres` (montecarlo.py:3142).
- **Fitted on:** MODEL-LOG §1.44 (MODEL-LOG.md:4498): four functional forms screened on nine city-years (Johannesburg 2016 and the eight metros at 2021); c fitted on summed absolute list-share error of cached mean vectors (Johannesburg 2016 alone gives 0.375; leave-one-city-year-out over the nine gives 0.350); h chosen by a 0.02-0.40 sweep on the same nine. Register: backtest.py:389-400.
- **Estimator.** At origin T, for every earlier backtest city-year (city, t), t < T: `inp = run_model(target_t, scenario_T with level_shrink=0, stop_after="drawer_inputs")`, where `scenario_T` carries origin T's other settings (k̂_T). For each grid point (c, h): `centres = compress_levels(inp.centres, {c, h})`, `spec = M.pool_spec(inp.scenario, centres, inp.index)`, `s = M.pool_spec_centres(spec)`; loss = Σ over rows and pooled parties of |s_p − a_p|, a = `compare_history.actual_shares(target_t, DATA)[0]` (list ballot). (ĉ_T, ĥ_T) = argmin over c ∈ {0, 0.05, …, 0.60}, h ∈ {0.02, 0.04, 0.06, 0.10, 0.20, 0.40}. The objective is §1.44's (summed absolute list error), on the centre the universal draw conserves (`pool_spec_centres`, montecarlo.py:3820), which is the drawn mean.
  - **Exactness control, per training row:** `pool_spec_centres` from a `drawer_inputs` run at (0.35, 0.04) must equal the offline application to the c = 0 inputs to 1e-12. If any row fails, the offline shortcut is invalid for that row and the fit runs `drawer_inputs` per grid point there.
  - The convention that the training rows are built with origin T's settings is the one `width_record.build` already uses (one `sets` for every earlier year, width_record.py:563-574). The alternative (each training row at its own origin's settings) is reported as a sensitivity.
- **Available:** 2011: no earlier backtest row (no pool spec before 2011): **declared c = 0**, the identity. 2016: the eight 2011 rows: **fitted on one cycle**. 2021: the sixteen 2011 and 2016 rows.
- **Estimation or tuning:** estimation, on the same footing as the width record's location m(s), which `montecarlo` describes as "the centres' average size-related error against real results of earlier elections" (`DEFAULTS["centre_correction"]` comment). The loss is error against real list shares, not a realised-over-predicted ratio. What stays in-sample: the **functional form** was chosen on the nine city-years (§1.44 says so). The stop gap refits the parameters inside the chain, not the form; the form is listed with the switches in §7.

### 2.4 `SPINE_K`

- **Defined:** levels.py:193 (`SPINE_K = 1.0`); `DEFAULTS["spine_k"] = None` (montecarlo.py:404) resolves to it at call time (levels.py:1703; montecarlo.py:7137-7150). The local route's weight is k / (worth + k) (levels.py:1777).
- **Fitted on:** "leave-one-metro-out over 180 party-city-years … eight metros and three transitions", flat between 0.5 and 1.5 (levels.py:69-93, 187-192). No fitting code in `src/`. Register `PROVENANCE_UNSETTLED["spine_k"]` (backtest.py:465-480), FIX #39 open. The stop gap settles provenance by fitting it in code per target.
- **Estimator.** At origin T, for every metro and earlier LGE t < T whose θ and ρ records before t are both non-empty: `inp = run_model(target_t, …, stop_after="drawer_inputs")`; `inp.scenario["_spine_info"]["detail"]` (montecarlo.py:7171) gives, per party, `national`, `local` and `worth`. Those do not depend on k. For each party with both routes and a realised share a > 0: level(k) = exp(w·log local + (1 − w)·log national), w = k / (worth + k) (w = 0 when worth + k ≤ 0, same line). Loss = vote-weighted RMSE of log(level / a), weight a. k̂_T = argmin over {0, 0.125, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 4, 8}; the curve is published.
- **Available:** 2011: the only candidate t is 2006, whose ρ record is empty (the first LGE pair ends in 2006) and which has no pool spec for `drawer_inputs`: **declared k = 1.0** (the pollster's value: the routes equal at one unit of θ evidence). 2016: t = 2011, eight metros: **fitted on one cycle**. 2021: t ∈ {2011, 2016}.
- **Estimation or tuning:** estimation (a combination weight fitted on error against real local results of earlier elections). It is not a ratio to the model's own spread.

### 2.5 New-party chance and size at 2011, and every declared value

`entrant_prob` 0.25 and `entrant_share` [0.01, 0.04, 0.12] (montecarlo.py:366-367; the same values in the two city TOMLs) act only where no arrival is named: `if scenario["entrant_prob"] > 0 and not named_arrivals` (montecarlo.py:6606). Read-only: every 2011 spec's `seeds` is empty and every 2016 and 2021 spec names arrivals, so the generic slot exists in the eight 2011 rows only. That is what "declared at 2011" covers.

Their provenance: typed from the plan; "kept after a sweep on 9 backtests" (`FITTED_ON_UNINSTRUMENTED["entrant_prob"]`, backtest.py:417-432; JUDGEMENT-CALLS §A3 and §A17). The pre-2011 arrival record the code can read is empty: `entrant_record` is `[]` in `data/processed/pools_2011.json` and `capetown/pools_2011.json`, and `pools._citywide_for` returns nothing for 2000 and 2006 outside Johannesburg (read-only probe). Johannesburg 2006's one arrival from nothing at ≥ 0.5% is the Independent Democrats at 1.94%. No estimator has data, so both are declared.

**Declared values at 2011 (JUDGEMENT-CALLS before the run; the owner confirms, Q3):**

| setting | declared at 2011 | reason | bracket arms |
|---|---|---|---|
| `level_shrink` | 0 (h = 0.04, inert at c = 0) | the identity; nothing earlier to fit on | B-c: 0.35 |
| `spine_k` | 1.0 | the routes equal at one unit of θ evidence (pollster) | B-k-lo 0.5, B-k-hi 2.0 |
| `turnout_correlation` | 0.5 | one metro-transition before 2011; no outside source; the midpoint of the defensible extremes | B-rho-0 0, B-rho-1 1 |
| `entrant_prob` | 0.25 | typed; the pre-2011 record the code reads is empty | B-ent-0 0, B-ent-hi 0.5 |
| `entrant_share` | [0.01, 0.04, 0.12] | typed, as above | none |

The declared 0.25 and its share range were typed by people who knew the 2011-2021 arrivals; the row says so.

### 2.6 Settings that cannot be refit without tuning

None of the four. The parts that remain chosen on the scored rows (§1.44's functional form; the switches) are listed in §7, not refit.

---

## 3. Cycle order

"Cycle order" here means: every setting for a target is fixed, written and committed (hash recorded) before any row at that target or a later one is scored, and no fit reads a score. The fits read drawer inputs and real results of earlier elections only.

1. Pre-registration committed under `prereg/` (after blind review).
2. Wording edits committed; this spec's code changes committed; `src/` clean.
3. Settings: 2011 declared; 2016 (k̂, then ĉ and ĥ given k̂, then ρ̂); 2021 the same. Written to `OUT/settings/NEW/{2011,2016,2021}.json`; `OUT/settings/OLD/*.json` are `{}` with `derived_from` absent.
4. Width records (§4), OLD and NEW.
5. Contamination checks (§5), before any score is read.
6. Rows: 2011 (OLD, NEW, brackets), then 2016, then 2021.
7. Comparison and write-up.

---

## 4. The width record per arm

- **How it is built:** `width_record.build(sets, cities, targets)` (width_record.py:563). For each target in `FORWARD` (width_record.py:80: 2016 ← 2011; 2021 ← 2011, 2016), it calls `drawer_inputs(city, year, sets)` (width_record.py:537: `run_model(stop_after="drawer_inputs")`, no draw) at every earlier city-year, takes `pool_spec_centres` and the realised list shares (`case_for`, width_record.py:546), forms residual rows (width_record.py:156), fits the curve, location and δ by weighted likelihood, and iterates the location fixed point, which draws `FIXED_POINT_DRAWS` (2000) at each earlier city-year (`location_shift`, width_record.py:431). 2011 takes `fallback_record` (width_record.py:504): the RMS of the forward θ residual at target 2006, read through `theta_residual.residuals()`.
- **Reads:** the pool specs at the earlier years (`record_specs`), their realised result files (`record_result_files`), the raw files the 2011 fallback can read (`fallback_files`), the group-share record, and everything `run_model` reads at those city-years.
- **Per arm, outside `data/`:** never the CLI (`--emit --out` writes `data/`; memory note and width_record.py:637). In the harness, one process per (arm, T):

      rec = width_record.build(sets_T, targets=(T,))
      width_record.write(rec, OUT / "width" / arm / T / "width_record.json")

  `sets_T` is the target's settings as `key=json` strings. `write` stamps `M.width_record_key()` (hashes over the repository's `data/processed`, which the build read). The variant key `M.width_record_variant(scenario)` (montecarlo.py:3845) encodes only c and h; the run passes the record with `width_override` (§6 C1), so the variant only has to match within one file.
- **NEW:** `build(sets_2016, targets=("2016",))` reads 2011 cases built with origin-2016 settings; `build(sets_2021, targets=("2021",))` reads 2011 and 2016 cases built with origin-2021 settings; 2011 is the fallback.
- **OLD:** `build([], targets=("2011", "2016", "2021"))`.
- **Refusals that stay on:** `MIN_ESTABLISHED` (width_record.py:88); a stale key (§6 C1 check); the calibration pass's convergence (the run's `kappa_converged`).

---

## 5. Contamination guard

### 5.1 What each row reads, and the latest election each embodies

T is the target; P = the preceding LGE (2006 / 2011 / 2016); N = the preceding NPE (2009 / 2014 / 2019).

| input | where | latest election embodied | status |
|---|---|---|---|
| pool spec `pools_T.json` | `<city processed>/pools_T.json` | P (`fitted_on`), plus T's roll and ward-ballot presence (`provenance`: "pools sized by the T roll … reach T ward ballot") | clean by Definitions (roll, nominations); embeds Step 3.1 constants |
| baseline | `data/raw/elections/npe{N}_{CODE}_vd_party.csv` (montecarlo.py, `target.previous_npe`) | N | clean |
| previous local result | `lge{P}_{CODE}_vd_party_clean.csv` | P | clean |
| θ, ρ records, size windows | raw LGE/NPE files with year < T (levels.py:713, 894) | < T | clean by construction |
| γ | `fold{GAMMA_FOLD[T]}_parameters.csv` (montecarlo.py:1183: 2011→4, 2016→3, 2021→1) | 2006 / 2011 / 2016 | clean; fold calibration is a Step 3.1 constant |
| γ fallback | `<city>/T/gamma_recent.csv` | P→N (gamma_recent.py) | clean |
| turnout | `<city>/T/turnout.csv` | λ pairs before T | clean; `w_recency`, `kappa_bye` are Step 3.1 constants |
| roll, ward layer | target's own result file, read for registration and ballot only (`ward_parts`; `levels.ballot_roster`, `contestation`) | T (pre-election facts) | clean by Definitions |
| census composition | `config/dimensions.toml`, Census 2022 | 2022 | **ex-post exception**, labelled on every row |
| VD concordance, party crosswalk | `vd_concordance.csv`, `party_crosswalk.csv` | built across all elections | structural; crosswalk is a Step 3.1 item |
| group-share record | `data/processed/group_share_record.json` | < T per target (its `sources`) | tripwire only, changes no number |
| width record | **OUT** file per arm and target | < T (cases) / 2006 (2011 fallback) | rebuilt |
| settings | `OUT/settings/<arm>/T.json` | its `derived_from` | NEW: < T; OLD: in-sample |
| reference forecasters | P, N, the NPE before P, the LGE before P (`benchmarks.sources_for`, benchmarks.py:91) | < T | clean |
| scorer | target's result file via `actual_shares`, `_actual_seats` | T | scoring only; `relabel_run` names the 2011 generic slot with the outcome in hand (existing, same in every arm) |
| by-election files, `bye_value.json` | `<processed>/byelection_*` | 2022-2026 | must not be opened at any past target |

### 5.2 The check: an `open` audit hook per process, and a classifier

**The hook must reach the workers.** compare_history `--jobs N` runs rows in a `ProcessPoolExecutor`; on macOS the start method is `spawn`, so a hook installed in the parent does not exist in the workers that call `run_model`. The hook is therefore installed by a `sitecustomize.py` in `OUT/hook/`, which the harness prepends to `PYTHONPATH` for every process it launches (fits, record builds, rows, and their workers): each interpreter runs it at start-up and calls `sys.addaudithook`, writing `OUT/opens/<arm>/T/<pid>.jsonl`, one line per `open` event with the resolved path and the innermost `src/` frame (module.function). The harness records the PIDs it and the pools spawned; part 0 below compares that set with the PIDs that logged. After each process, the classifier (§6 C4) decides each path:

- `data/raw/elections/{lge,npe}YYYY*`: allowed if YYYY < T. YYYY = T is allowed only from the named readers: the roll and ward layer (`montecarlo.ward_parts`, `levels.ballot_roster`, `levels.contestation`, `levels._result_ballots`, `levels.ward_ballots`, `levels.has_result_file`) and the scorer (`compare_history.actual_shares`, `compare_history._actual_seats`, `benchmarks.build_context` for roll and boundaries). YYYY > T fails anywhere in a row or a fit.
- `<city>/YYYY/` intermediates and `pools_YYYY.json`: YYYY must equal T for a row; for a width record or a fit, YYYY ∈ the declared training years.
- `fold{N}_parameters.csv`: `M.fold_target_year(N)` < T.
- **Denylist, anywhere:** `data/processed/width_record.json`, `history.json`/`.md`, `validation_2021.json`, `sweep.json`, `regime_*`, `width_budget.json`, every past target's `seat_draws.csv`, `ward_winner_probs.csv`, `coalition_*.csv`, `forecast_frozen.json`, `bye_value.json`, any `byelection_*` at a past target, anything under `reports/model-changes/`, `audits/`, `prereg/`.
- **Named exception:** `width_record.fallback_record` → `theta_residual.residuals()` computes every target and filters to 2006, so the 2011 record build opens later result files. Allowed only with that frame on the stack, and only in the record-build process; the record's content is checked separately (its `fallback.n_*` must equal the 2006 counts recomputed).

The check passes only if all four parts of CLAUDE.md §4 hold:
0. **Right population:** the PIDs that logged equal the PIDs the harness and its pools spawned (both directions), and each row's opened set includes its own spec, baseline, previous LGE and settings file.
1. **It looked:** each process logged between a lower and an upper bound of opens, as a fraction of the files `run_model` is known to read (two-sided).
2. **It can see:** a planted violation inside `run_model`'s path in a pool worker (a row that additionally reads `lge{T+5}` through `levels._citywide`), and one in a fit (a read of `history.json`), are each caught, and the check goes quiet when they are reverted. The worker plant is what proves the hook reaches the workers.
3. **Constructed input:** the classifier's unit test feeds constructed open logs, not a copy of a passing run.

### 5.3 The settings and the precomputed artefacts

- **Settings:** each NEW settings file's `derived_from` is computed by the fit from its own open log, and `backtest.check_derived_from` refuses any year ≥ T. A test plants a 2016 year in the 2016 file and expects refusal.
- **Precomputed artefacts (the owner's "earlier data that is contaminated"):** the hook cannot see an emit that ran weeks ago. So, in an isolated worktree (`git worktree add` plus a full copy of `data/`) and under the same hook: re-emit every past target's spec (`pools.py --city X --target Y --emit`, the 24-invocation subset of `POOLS-REEMIT-QUEUE.md`'s loop) and regenerate each `turnout.csv` (`turnout.py --out`), `gamma_recent.csv` and the three γ folds (`fold.py --out`). **Pass/fail is the open classification**: every regeneration opens only files allowed for its target. The comparison with `data/processed` is reported, not gated, because byte identity on re-emit is not guaranteed here (MODEL-LOG §1.279 records a placebo set of 13, not 16, from float drift). A byte mismatch is followed by comparing `artefact_key` and the structural fields (parties, pools, seeds, `fitted_on`, `provenance`) and reporting the largest numeric difference per field; a structural difference stops the stop gap and goes to the owner. This regenerates in an isolated tree; it is not a re-emit into `data/`.
- **What no check reaches:** constants. They have no mechanical proof (PLAN 3.4); §7 lists them.

---

## 6. Minimal code changes

| # | where | what | size |
|---|---|---|---|
| C1 | `compare_history.run_city_year` and `main` | Three keyword arguments and flags. `config`: passed to `load_scenario`'s `config`; its metadata read with `M.read_scenario_file` and validated with `B.check_derived_from`; its keys become `declared_clean` in `B.contaminated(year, declared_clean, …)`, which replaces `set()` (compare_history.py:1788). `width_record`: a path; the file's `artefact_key` must equal `M.width_record_key()` (else SystemExit naming the stale keys), then `blob["variants"][M.width_record_variant(scenario)]["targets"][year]` is passed as `run_model(..., width_override=...)`. `trace_detail`: passed to `run_model`, so `42_pr_share_draws` and `44_seat_draws` reach the trace for the paired Monte Carlo error. The job tuple (compare_history.py:4452) carries all three. | ~30 lines |
| C2 | new `src/rolling_settings.py` (import-only, no `__main__`) | `fit_spine_k(T, sets)`, `fit_level_shrink(T, sets)`, `turnout_moves(cfg, before)` and `fit_turnout_correlation(T)`, `declared(T)`; each returns value, n, the elections read, the curve, and whether the fallback fired. Uses `run_model(stop_after="drawer_inputs")`, `compress_levels`, `pool_spec`, `pool_spec_centres`, `actual_shares`, `pools._pool_counts_or_loss`; defines no second copy of an estimator the model already has. | ~200 lines |
| C3 | new `tests/test_rolling_settings.py` | Constructed fixtures: each fit recovers a planted k, (c, h) and ρ; each refuses an input at or after T; `turnout_moves`' count equals `panel_turnout_spread(cfg, before)[1]` at 2011, 2016, 2021; the offline (c, h) path equals the run's at one constructed point; the classifier (C4) catches a planted open and is quiet without it. | |
| C4 | `rounds/2026-10-23-out-of-sample/stopgap/run.py` and `check_opens.py` (not `src/`) | The harness (§3 order, one process per (arm, T), `arms.check_out`, the audit hook, settings and record writing, compare_history invocations, the comparison table) and the classifier of §5.2. The precedent is `prefreeze/run_arms.py`. | |
| C5b | `backtest.py` registers | `declared_clean` reaches `FITTED_ON_UNINSTRUMENTED` (backtest.py:722) but not `PROVENANCE_UNSETTLED` (backtest.py:682), so NEW rows would still name `spine_k`. Once C2 fits it in code, move `spine_k` out of `PROVENANCE_UNSETTLED` into `FITTED_ON_UNINSTRUMENTED` with the years the 2016-2021 fit read for the live default (FIX #39's deliverable). `backtest.py` is not in `width_record_key`. | ~10 lines |
| C5 | none in `montecarlo.py`, `pools.py`, `levels.py`, `width_record.py` | So no spec goes stale and no re-emit is needed. C1 changes `compare_history.py`, which `width_record_key` hashes (montecarlo.py:3931), so records are built after C1 is committed. | |
| C6 | documents, same commit as the code | `JUDGEMENT-CALLS.md`: `N_MIN`, the 2011 declared values, the grids. `MACHINERY.md`: the rolling estimators. `MODEL-LOG.md`: the result (append). `python src/model_index.py` before the suite run (QC.md §4). | |

Alternative to C1 with no change to `src/`: the harness replaces `montecarlo.read_width_record` and post-processes `contaminated` in process, as `prefreeze/run_arms.py` replaced `load_parameters`. Rejected here: it leaves the row's own provenance field wrong in the artefact and depends on patch scope.

---

## 7. Scoring and the side-by-side

**Scores, per row and summed** (all from compare_history's record): `crps` (headline), `seat_abs_err_coherent` (and half of it, labelled "seats given to the wrong party"), `pr_mae`, `ward_mae`, the four reference forecasters in `opponents` (last-lge, uniform-swing, prior-lge-noise, uniform-swing+roster) and the count of rows beating uniform swing, `calibration`, `wards`. Murphy's (1992) combination (PLAN 3.6) does not exist in `benchmarks.BENCHMARKS`; it is not added by the stop gap (Q5).

**Populations:** headline on the 16 rows at 2016 and 2021; the 8 rows at 2011 beside them, labelled "settings declared, not fitted". Per-cycle totals as well as the sum, because 2011, 2016 and 2021 each share one national swing.

**Paired Monte Carlo error** of each NEW − OLD difference: one draw-index resample applied to both arms, from the traced draws, with `score.crps_by_party` (score.py:450), the function `arms.compare` uses.

**Where the old scores can be read:**

| source | what | label |
|---|---|---|
| `data/processed/history.json` (P3) | 24 records as of 2026-10-19, tree a9754ede (dirty), 1000 draws, seed 20261104 | in-sample, older tree |
| `data/processed/validation_2021.json` | the 2021 validation behind the `validation:` tokens, generated 2026-09-30 | in-sample |
| `site/` at `51d13ce1` (the parent of the withdrawal commit `7de91bb9`), via `git show` | the figures as published | in-sample, as published |
| `reports/model-changes/*/backtest.json` (seven, each with a banner) | per-round panels | in-sample |
| OLD arm (this run) | current settings, this tree, same seed | in-sample |

The published table has three score columns per row: as published (`history.json`), OLD, NEW. OLD − NEW is the measured optimism from the four settings and the width record. As published − OLD is tree drift and is labelled so.

**Still in-sample, listed beside every score:**
- Step 3.1's constants: `SPLINTER_PARENT_WEIGHT`, `SD_FLOOR`, `RHO_ANCHOR_LO/HI`, `LOCATION_CLAMP`, `WIDTH_BLOCK`, `plan_bounds`, `entrant_geography`, `turnout.py`'s `w_recency` and `kappa_bye`, `TYPE_A_EVENTS` and `THETA_EXCLUDE_TARGETS`, `pools.SPLITS` (typed with NFP, EFF, ActionSA, GOOD and MK as splits), the fold calibration, `party_crosswalk.csv`, `ward_noise_sd`, `level_floor`, `dirichlet_floor`, and the pool specs' emitted constants.
- Arrivals' size (Step 3.2): the named seeds at 2016 and 2021.
- The switches (Step 3.3): the draw law (universal), `newness_width = "by_anchor"`, `centre_correction` off, `arrival_group_draw` off, polls off (owner design decision; not a leak), and `compress_levels`' functional form.
- The Census 2022 composition (ex-post exception), and the ENTRANT relabel in scoring.
- The model structure itself, chosen over many iterations judged on these rows (POLLSTER-ON-RECORD §3).

Never described as out-of-sample. compare_history's `in_sample` verdict stays IN-SAMPLE for NEW rows, because `FITTED_ON["pools"]` (backtest.py:213) lists all three years; that verdict is correct.

---

## 8. Runtime

**Measured bases.**
- Arm U, 24 backtest rows at 1000 draws plus Johannesburg 2026 at 5000, three arms running concurrently, Atlas, 2026-10-13: 07:06:36 → 07:22:16 for the 24 rows, i.e. 15 min 40 s, about 20-30 s per 2011 row, 30-55 s per 2016 row, 50-70 s per 2021 row (`.claude/step7-2026-10-13/arms/U/*/meta.json` mtimes; `commands.log` lines 177-184).
- `width_record.py --emit`, four targets: 19 min 34 s, 21 min 51 s, 19 min 14 s, 19 min 52 s (`commands.log` lines 103-106, 164-167).
- `run_model` fixed cost, Johannesburg 2026, one BLAS thread: 14.79 s; 21.6 ms per draw (MODEL-LOG.md:26978-26983).
- Re-emit of 27 specs: 1,593 s serial (MODEL-LOG §1.279).
- compare_history's extra cost per row (reference forecasters, PIT redraws) is not recorded anywhere found. **The first row's wall time is reported before the batch continues** (QC.md §4b item 4).

**Estimate on Scout (Apple M4, 10 cores, 24 GB), 8 workers, one BLAS thread each:**

| stage | work | wall |
|---|---|---|
| fits | per training row, `drawer_inputs` three times (k fit; at k̂ with c = 0; at (0.35, 0.04) for the exactness control): 24 at origin 2016, 48 at 2021, about 70 calls at ~15 s, plus grid arithmetic | 3-8 min |
| width records | OLD three targets (≈ half a four-target build) ∥ NEW 2016 ∥ NEW 2021 | 10-15 min |
| isolated regeneration (§5.3) | 24 spec emits + intermediates, parallel by city | 5-10 min |
| rows | 24 OLD + 24 NEW + 56 bracket rows at 2011 = 104 rows at 1-2.5 min each including scoring | 15-35 min |
| total | | about 35-65 min, plus review stops |

Parallel only within a cycle; cycles in order (§3). One writer under `OUT`, nothing under `data/`. **Concurrent processes × `--jobs` ≤ 8** (ten cores, 24 GB): e.g. the nine 2011 arms run as nine invocations with `--jobs 1` or in sequence with `--jobs 8`, never nine at `--jobs 8`.

---

## 9. Risks and questions for the owner

| # | | |
|---|---|---|
| Q1 | Label | A stop-gap row is neither "in-sample" nor "forward-chained" (PLAN 0.3, `tests/test_quarantine.py`). Proposed: "in-sample", with the sentence "four settings and the ranges set from earlier elections only; the rest of the model in-sample". |
| Q2 | `N_MIN = 8` | One threshold for every setting. 2016 is fitted on a single cycle for all three settings. |
| Q3 | Declared 2011 values | §2.5's table; in particular ρ = 0.5 has no source. |
| Q4 | Headline | 16 rows (2016, 2021) with 2011 beside, as the pollster recommends, or all 24. |
| Q5 | Murphy's baseline | Not in the stop gap. |
| Q6 | Training-row convention | Training rows at origin T's settings (as `width_record.build` does) or at their own origin's. The first is proposed; the second is reported as a sensitivity. |
| R1 | Stale live record | P1 is for the freeze and the live site, not the stop gap. |
| R2 | Thin samples | Every fitted value at 2016 rests on one cycle; flat objectives (k) give a noisy argmin, so the curve is published with it. |
| R3 | Demarcation | Mangaung and Buffalo City 2006→2011 turnout moves compare different areas; reported both ways. |
| R4 | Freeze | Step 5.1's freeze is built (MODEL-LOG §1.336); nothing here touches `data/` or the frozen artefacts. |
