# The model index

⛔ **GENERATED. Do not edit.** `src/model_index.py` writes this file and `tests/test_model_index.py` regenerates it into a scratch path and compares, so a hand edit fails the suite.

Every register this repository keeps, joined on the names they share. A name in one register and not another is the finding; the sections below are ordered so the joins come before the inventories.

Read `model` and `measurement` as membership of the import closure of `montecarlo` and of `compare_history` — what a forecast runs through, and what scores one. `neither` is not an accusation: a build script is correctly in neither.

## 1 · Collisions

### 1.1 One computation, several reported names

⛔ THIS IS THE `seat_abs_err` SHAPE, and it is why the detector exists: a
reported key whose value is a call to a function of the SAME NAME, sitting
beside a second key calling the same function on a DIFFERENT argument. The
two keys are then two statistics wearing one name plus a suffix, and a
summary that adds them, or quotes one as the other, is wrong in a way no
arithmetic test can see.

| module | function | reported as |
|---|---|---|
| `backtest` | `results` | `actual`, `base`, `prior_lge` |
| `build_validation` | `grab` | `brier`, `council`, `crps`, `seat_mae`, `wards`, `wards_called` |
| `compare_history` | `_stats` | `ge_half`, `lt_half` |
| `compare_history` | `seat_abs_err` | `seat_abs_err`, `seat_abs_err_coherent` |
| `compare_history` | `vote_mae` | `pr_mae`, `pr_mae_median`, `ward_mae`, `ward_mae_median` |
| `diagnose` | `seat_abs_err` | `coherent_err`, `marginal_err` |
| `levels` | `sd_for` | `at_0.1%`, `at_1%`, `at_10%`, `at_40%` |
| `publication` | `_sha` | `forecast_summary_sha256`, `seat_draws_sha256` |
| `render_sheet` | `tok` | `da_alone_count`, `wall_count` |
| `score` | `coverage` | `coverage`, `coverage_all` |
| `theta_residual` | `anderson_darling` | `ad_candidate`, `ad_incumbent` |

### 1.2 One name, defined in more than one module

| name | modules | kinds | same kind |
|---|---|---|---|
| `BASE` | `fetch_boundaries`, `fetch_iec` | `str` | yes |
| `BASELINES` | `build_validation`, `diagnose` | `dict[3]`, `scored_opponents()` | NO |
| `CHIPS` | `render_map`, `render_sheet` | `dict[11]`, `dict[12]` | NO |
| `CITIES` | `arrivals`, `build_validation`, `compare_history`, `judgement_sheet`, `sweep` | `ROOT / 'cities'`, `list[8]` | NO |
| `COLUMNS` | `archive`, `fetch_byelections`, `ingest_lge`, `ingest_npe` | `list[10]`, `list[11]`, `list[14]`, `list[5]` | NO |
| `DATA` | `freeze`, `width_budget` | `REPO / 'data/raw/elections'` | yes |
| `ELECTIONS` | `build_concordance`, `build_crosswalk`, `turnout` | `dict[11]`, `dict[6]`, `{year: (e.results, e.two_ballot) for year, e in sorted(cityconfig.CALEND` | NO |
| `MARK_END` | `hex_cartogram`, `render_map` | `str '<!-- __HEXMAP_END__ -->'`, `str '<!-- __MAP_END__ -->'` | NO |
| `MARK_START` | `hex_cartogram`, `render_map` | `str`, `str '<!-- __MAP_START__ -->'` | NO |
| `METRO_CODES` | `levels`, `pools` | `tuple[8]` | yes |
| `NAMES` | `render_map`, `render_sheet` | `dict[15]`, `dict[8]` | NO |
| `NAV_CSS` | `build_site`, `build_site` | `NAV_CSS.replace('{FOOTER_CSS_PLACEHOLDER}', FOOTER_CSS)`, `str` | NO |
| `OUTPUT` | `judgement_sheet`, `model_index` | `ROOT / 'JUDGEMENT-SHEET.md'`, `ROOT / 'MODEL-INDEX.md'` | NO |
| `PROCESSED` | `declares`, `overhang_regimes` | `Path('data/processed')`, `REPO / 'data' / 'processed'` | NO |
| `REGISTER` | `judgement_sheet`, `polling` | `Path('polls.json')`, `ROOT / 'JUDGEMENT-CALLS.md'` | NO |
| `REPO` | `declares`, `freeze`, `width_budget` | `Path(__file__).resolve().parents[1]` | yes |
| `REPORTS` | `derive_city`, `official_seats` | `Path('data/raw/elections/_reports')` | yes |
| `ROOT` | `deploy_check`, `judgement_sheet`, `model_index` | `Path(__file__).resolve().parent.parent`, `Path(__file__).resolve().parents[1]` | NO |
| `Row` | `declares`, `publication` | `?` | yes |
| `SHARE_FLOOR` | `benchmarks`, `fold`, `montecarlo` | `float 0.002` | yes |
| `SRC` | `judgement_sheet`, `model_index` | `ROOT / 'src'` | yes |
| `USER_AGENT` | `fetch_boundaries`, `fetch_byelections`, `fetch_iec` | `str` | yes |
| `audit` | `declares`, `stats` | `?` | yes |
| `build` | `judgement_sheet`, `model_index` | `?` | yes |
| `citywide` | `fold`, `turnout` | `?` | yes |
| `classify` | `hex_cartogram`, `publication` | `?` | yes |
| `cluster_bootstrap` | `score`, `theta_residual` | `?` | yes |
| `expit` | `fold`, `montecarlo` | `?` | yes |
| `load` | `cityconfig`, `fold`, `polling`, `scenarios` | `?` | yes |
| `logit` | `fold`, `montecarlo` | `?` | yes |
| `normalise` | `parties`, `prep_logos` | `?` | yes |
| `parse` | `scenarios`, `sweep` | `?` | yes |
| `read_municipality` | `ingest_lge`, `ingest_npe` | `?` | yes |
| `render` | `build_portal`, `compare_history`, `hex_cartogram`, `judgement_sheet`, `stats` | `?` | yes |
| `report` | `coalitions`, `contested_area`, `declares`, `theta_residual` | `?` | yes |
| `run` | `build_all`, `build_validation`, `diagnose`, `width_budget` | `?` | yes |
| `runnable` | `compare_history`, `sweep` | `?` | yes |
| `summarise` | `iec_csv`, `publication` | `?` | yes |
| `ward_parts` | `build_concordance`, `montecarlo` | `?` | yes |

### 1.3 One value, typed under two names

| value | names |
|---|---|
| 0.001 | `polling.POLL_DRIFT_PP_PER_ROOT_DAY`, `pools.NATIONAL_ONLY_FLOOR`, `pools.PRIOR_LOCAL_FLOOR` |
| 0.002 | `benchmarks.SHARE_FLOOR`, `fold.SHARE_FLOOR`, `levels.RELIABILITY_HALF`, `montecarlo.SHARE_FLOOR` |
| 0.005 | `gamma_recent.MIN_SHARE`, `pools.UNCLASSIFIED_FLOOR`, `render_map.OTHER_FLOOR` |
| 0.015 | `polling.SIGMA_COMMON`, `polling.SIGMA_IDIO`, `pools.ROSTER_DROP_CEILING` |
| 0.02 | `montecarlo.TURNOUT_DRAW_FLOOR`, `polling.POLL_SCREEN_SD_UNDISCLOSED` |
| 0.05 | `pools.CENSUS_DRIFT_CEILING`, `render_map.TIP_FLOOR` |
| 0.25 | `compare_history.REFERENCE_SLATE`, `pools.ARRIVAL_BAND_LO` |
| 0.5 | `montecarlo.WARD_PR_RATIO_MIN`, `score.CLAIM_FRACTION` |
| 0.9 | `pools.MAX_POOL_CAPTURE`, `pools.SPLIT_SD_FLOOR`, `render_map.SAFE` |
| 0.95 | `montecarlo.TURNOUT_DRAW_CEILING`, `pools.ARRIVAL_BAND_HI` |
| 12 | `montecarlo.DELIVERY_MAX_VALUES`, `pools.ALPHA_FALLBACK`, `stats.DECLARATION_MIN_CHARS` |
| 2.0 | `benchmarks.MAX_SIGMA`, `hex_cartogram.GRID_MARGIN_CELLS`, `levels.SHRINK`, `montecarlo.OVERHANG_DEDUCT_MAX_ROUNDS_SLACK`, `montecarlo.WARD_PR_RATIO_MAX`, `pools.MIN_HOME_SPLITS`, `pools.REGISTRATION_MAX` |
| 200 | `montecarlo.OVERHANG_LEVEL_MAX_ROUNDS`, `montecarlo.PARTIAL_BALANCE_PASSES`, `pools.ALPHA_CEILING` |
| 300 | `polling.POLL_MIN_N`, `stats.FRESHNESS_GRACE_S` |

### 1.4 Apportionment sites — the same job, written more than once

Matched on the SHAPE of largest-remainder apportionment (a whole part, an ordering, a shortfall handed out), not on the phrase, which appears in the docstrings of modules that only discuss it.

| function | orders the shortfall by | summary |
|---|---|---|
| `compare_history.coherent_seats` | `argsort(-(exact - base` | A point forecast that IS a council: largest remainder on the mean vector. |
| `pools.panel_turnout_spread` | `sorted((split_bloc or {}).items(` | How far EACH pool's turnout moves between local elections, panel-wide. |
| `render_sheet.round_to_total` | `sorted(vals, key=lambda q: floors[q] - vals[q])[:max(rem, 0)]` | -- |
| `scenarios.main` | `sorted(detail[d].items(), key=lambda kv: -kv[1]['']` | -- |
| `seats.allocate` | `sorted(remainders, key=lambda p: (-remainders[p], -combined[p]` | Allocate council seats by the Schedule 1 quota-and-largest-remainder method. |
| `validate_seats.main` | `sorted(official[''].items(), key=lambda kv: -kv[1]['']` | -- |

### 1.5 Shadow pairs — a scenario key and a module constant of one name

`tied` means some `assert` in `src/` names both, so they cannot silently disagree. An untied shadow is one number in two places.

| lever | shadow constant | tied |
|---|---|---|
| `dirichlet_floor` | `montecarlo.DIRICHLET_FLOOR` | NO |
| `level_floor` | `fold.LEVEL_FLOOR` | NO |
| `poll_deff_subsample` | `polling.POLL_DEFF_SUBSAMPLE` | NO |
| `poll_half_life_days` | `polling.POLL_HALF_LIFE_DAYS` | yes |
| `poll_house_k` | `polling.POLL_HOUSE_K` | NO |
| `poll_min_n` | `polling.POLL_MIN_N` | NO |
| `spine_k` | `levels.SPINE_K` | NO |
| `turnout_correlation` | `montecarlo.TURNOUT_CORRELATION` | yes |

## 2 · Exemptions, and whether they still exempt anything

### 2.1 Deleted levers the judgement register is allowed to discuss

`named by register` is what the exemption is FOR. An entry the register never names excuses nothing today and is waiting to excuse the next name that collides with it.

| name | named by register | still referenced in src |
|---|---|---|
| `DA_LED_COALITION` | NO | -- |
| `F_OTHER` | yes | -- |
| `POLL_K` | yes | -- |
| `POLL_RMS_ERROR` | yes | -- |
| `THETA_CENTRAL` | yes | -- |
| `census_blend` | yes | -- |
| `census_blend_wanted` | yes | -- |
| `pa_contestation_uplift` | yes | -- |
| `poll_id` | NO | `polling` |
| `poll_k` | yes | -- |
| `poll_weight` | yes | -- |
| `polling_lean` | yes | -- |
| `polling_span` | NO | -- |
| `theta_mode` | yes | `build_interactive` |
| `total_log_median` | yes | -- |

### 2.2 Deleted from the model, still read somewhere in `src/`

| name | present | read in |
|---|---|---|
| `OTHER` | yes | `export_interactive`, `render_map`, `render_sheet` |
| `f_other` | yes | `build_interactive` |
| `individual_theta` | yes | `build_interactive` |
| `turnout_tilt_da` | yes | `build_interactive` |

### 2.3 Entry points — modules exempted from the dead-code rule

An entry point that has acquired an importer no longer needs the exemption: the importer proves it alive on its own.

| module | exemption still load-bearing | importers |
|---|---|---|
| `arrivals` | yes | -- |
| `build_crosswalk` | yes | -- |
| `build_geo` | yes | -- |
| `build_interactive` | yes | -- |
| `build_portal` | yes | -- |
| `build_validation` | yes | -- |
| `byelections` | yes | -- |
| `contested_area` | yes | -- |
| `derive_city` | yes | -- |
| `export_interactive` | yes | -- |
| `fetch_boundaries` | yes | -- |
| `fetch_byelections` | yes | -- |
| `fetch_iec` | yes | -- |
| `gamma_recent` | yes | -- |
| `ingest_npe` | yes | -- |
| `overhang_regimes` | yes | -- |
| `prep_logos` | yes | -- |
| `render_sheet` | yes | -- |
| `sweep` | yes | -- |
| `validate_seats` | yes | -- |
| `width_budget` | yes | -- |

### 2.4 The rest of the dead

| what | which |
|---|---|
| register sections still making a live claim on a deleted lever | `§F21`, `§F29` |
| gates declared and named by no inert entry | -- |
| gates recorded OPEN at a target | `arrivals_are_named@2011` |
| modules imported by nothing and not declared entry points | -- |

### 2.5 Module constants nothing outside their own module reads

Not dead by itself — a constant read only where it is defined is ordinary. Dead is this list crossed with a module in `neither` closure, and with §4's delivery table.

`archive.BY_FILENAME`, `archive.PROVENANCE`, `benchmarks.BLEND_W`, `benchmarks.MAX_SIGMA`, `benchmarks.MIN_SIGMA`, `benchmarks.NEW_PARTY_SIGMA`, `build_concordance.REG_DRIFT_TOLERANCE`, `build_geo.GDB_LAYERS`, `build_portal.ELECTION`, `build_portal.PORTAL_CSS`, `build_site.FOOTER_CSS`, `build_site.NAV_CSS`, `build_site.NAV_CSS`, `build_site.NAV_ITEMS`, `build_site.OG_META`, `build_site.REPO_ROOT`, `build_validation.DISPLAY`, `cityconfig.DEFAULT_CITY`, `compare_history.GAUTENG`, `compare_history.REFERENCE_SHARE`, `compare_history.REFERENCE_SLATE`, `contested_area.TRANSITIONS`, `declares.KINDS`, `declares.UNDECLARED`, `export_interactive.PAGE_PARTIES`, `fetch_boundaries.FGDB_ITEMS`, `fetch_boundaries.LAYERS`, `fetch_boundaries.PAGE_SIZE`, `fetch_byelections.DASH`, `fetch_iec.LGE_REPORTS`, `fetch_iec.MUNI`, `fold.LEVEL_FLOOR`, `gamma_recent.MIN_SHARE`, `hex_cartogram.CELL_AREA_FACTOR`, `hex_cartogram.GRID_MARGIN_CELLS`, `hex_cartogram.PREVIEW`, `iec_csv.BOMS`, `iec_csv.ENCODINGS`, `ingest_historic.LGE_COLUMNS`, `ingest_historic.METRO_BALLOTS`, `ingest_historic.NPE_COLUMNS`, `ingest_historic.OUT_DIR`, `ingest_historic.SOURCE_DIR`, `judgement_sheet.LIVE_TARGET_KEY`, `model_index.JUDGEMENT_REGISTER`, `model_index.MEASUREMENT_ROOT`, `model_index.MODEL_ROOT`, `model_index.SPAN_MARKERS`, `montecarlo.DIRICHLET_FLOOR`, `montecarlo.OVERHANG_DEDUCT_MAX_ROUNDS_SLACK`, `montecarlo.OVERHANG_LEVEL_MAX_ROUNDS`, `montecarlo.PARTIAL_BALANCE_PASSES`, `montecarlo.POOL_CAPACITY_MARGIN`, `montecarlo.SCENARIO_METADATA`, `montecarlo.TURNOUT_CORRELATION`, `montecarlo.TURNOUT_DRAW_FLOOR`, `montecarlo.WARD_PR_RATIO_MIN`, `official_seats.LABELS`, `polling.POLL_SCREEN_SD_UNDISCLOSED`, `polling.SCOPES`, `pools.ALPHA_CEILING`, `pools.ALPHA_FALLBACK`, `pools.ALPHA_FLOOR`, `pools.ALPHA_MIN_SHARE`, `pools.CENSUS_COVERAGE_FLOOR`, `pools.KNOWN_PARTY_CODES`, `pools.LOCK_PATH`, `pools.MAX_POOL_CAPTURE`, `pools.NPE_CITYWIDE_STATES`, `pools.ROSTER_KEYS`, `pools.SPLINTER_PARENT_WEIGHT`, `pools.SPLIT_SD_FLOOR`, `prep_logos.CODES`, `prep_logos.MISSING`, `publication.MOVEMENTS`, `publication.PRELEDGER_PREFIX`, `render_map.ANG`, `render_map.COS`, `render_map.DISTRICTS`, `render_map.KEY_PARTIES`, `render_map.KEY_SOLID`, `render_map.KEY_STRIPE_A`, `render_map.KEY_STRIPE_B`, `render_map.REST`, `render_map.UNKNOWN_CHIP`, `render_sheet.ALLIANCE_8`, `render_sheet.CHART_PARTIES`, `scenarios.COND`, `scenarios.OPS`, `stats.ATTRS`, `stats.CHROME_CLASSES`, `stats.FRESHNESS_REMEDY`, `stats.GENERATED_MARKERS`, `stats.GEN_TOKEN`, `stats.HISTORICAL`, `stats.NUMBERISH`, `stats.REGION`, `stats.SCRIPTS`, `stats.SCRIPT_FORBIDDEN`, `stats.SOURCED`, `stats.STAT_CSS`, `stats.TAGS`, `stats.TOKEN`, `sweep.PARTY_ROW`, `turnout.LAMBDA_PAIRS`

## 3 · Declared producers against the code

The intermediates register names the script that writes each artefact. `agrees` is false when the module it names does not so much as mention the artefact.

| artefact | register claims | modules naming it | agrees |
|---|---|---|---|
| `forecast_frozen.json` | `freeze` | `compare_history`, `declares`, `freeze`, `montecarlo` | yes |
| `forecast_summary.json` | `montecarlo` | `build_interactive`, `build_portal`, `coalitions`, `declares`, `freeze`, `levels`, `montecarlo`, `overhang_regimes`, `publication`, `render_sheet`, `stats` | yes |
| `history.json` | `compare_history` | `compare_history`, `declares`, `freeze`, `score` | yes |
| `history.md` | `compare_history` | `compare_history` | yes |
| `interactive_data.json` | `build_site` | `build_interactive`, `declares`, `export_interactive` | NO |
| `pools_*.json` | `pools` | `archive`, `arrivals`, `cityconfig`, `compare_history`, `declares`, `export_interactive`, `fold`, `freeze`, `montecarlo`, `pools`, `stats`, `sweep` | yes |
| `regime_*_summary.json` | `overhang_regimes` | `archive`, `build_interactive`, `build_portal`, `build_site`, `coalitions`, `declares`, `freeze`, `levels`, `montecarlo`, `overhang_regimes`, `publication`, `render_sheet`, `stats` | yes |
| `sweep.json` | `sweep` | `declares`, `sweep` | yes |
| `validation_*.json` | `montecarlo` | `archive`, `build_validation`, `compare_history`, `declares`, `score` | NO |
| `ward_hex_layout.json` | `hex_cartogram` | `hex_cartogram` | yes |
| `ward_paths.json` | `render_map` | `build_all`, `export_interactive`, `hex_cartogram`, `render_map` | yes |
| `width_budget.json` | `montecarlo` | `declares`, `width_budget` | NO |

## 4 · Levers

Every key of `montecarlo.DEFAULTS`, against every register that classifies it. `provenance` is the backtest's leak class; `inert at` and `conditional at` are the targets where the lever has been certified dead or measured live; `registered` is whether `JUDGEMENT-CALLS.md` names it.

| lever | default | provenance | inert at | conditional at | registered | read in |
|---|---|---|---|---|---|---|
| `arrival_group_draw` | `False` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `bye_local_cap` | `1.5` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `bye_tau_months` | `18.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `bye_weight_mode` | `'fixed'` | `NOT_FITTED` | `2021` | -- | yes | `backtest`, `montecarlo` |
| `contestation_expand` | `0.22` | `FITTED_ON_UNINSTRUMENTED` | `2021` | -- | yes | `backtest`, `montecarlo` |
| `dirichlet_floor` | `0.0001` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `dirichlet_scale` | `1.0` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `draws` | `5000` | `NOT_FITTED` | -- | -- | NO | `arrivals`, `backtest`, `benchmarks`, `build_site`, `build_validation`, `coalitions`, `compare_history`, `declares`, `diagnose`, `freeze`, `montecarlo`, `publication`, `score`, `stats`, `sweep`, `theta_residual`, `width_budget` |
| `entrant_geography` | `dict[0]` | `FITTED_ON` | `2021`, `2026` | -- | NO | `backtest`, `montecarlo` |
| `entrant_prob` | `0.25` | `FITTED_ON_UNINSTRUMENTED` | `2021`, `2026` | -- | yes | `backtest`, `build_interactive`, `compare_history`, `montecarlo` |
| `entrant_share` | `list[3]` | `FITTED_ON_UNINSTRUMENTED` | `2021`, `2026` | -- | yes | `backtest`, `build_interactive`, `compare_history`, `montecarlo` |
| `level_floor` | `1e-06` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `level_sd_default` | `0.45` | `NOT_FITTED` | `2021`, `2026` | -- | yes | `backtest`, `montecarlo` |
| `level_shrink` | `0.35` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `level_shrink_scale` | `0.04` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `overhang_rule` | `'deduct'` | `NOT_FITTED` | -- | -- | yes | `backtest`, `benchmarks`, `montecarlo` |
| `poll_credence` | `1.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_deff_subsample` | `1.6` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_drift_per_root_day` | `0.001` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_half_life_days` | `120.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_house_k` | `1.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_min_n` | `300` | `NOT_FITTED` | `2021`, `2026` | `2021`, `2026` | yes | `backtest`, `montecarlo` |
| `poll_paths` | `'off'` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `poll_screen_sd` | `0.02` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `pools` | `dict[0]` | `FITTED_ON` | -- | -- | yes | `backtest`, `declares`, `export_interactive`, `model_index`, `montecarlo`, `pools` |
| `seed` | `20261104` | `NOT_FITTED` | -- | -- | NO | `backtest`, `benchmarks`, `compare_history`, `declares`, `freeze`, `montecarlo`, `score`, `width_budget` |
| `spine_k` | `None` | `PROVENANCE_UNSETTLED` | -- | -- | yes | `backtest`, `montecarlo` |
| `turnout_blend_jitter` | `0.25` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `turnout_correlation` | `0.63` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `turnout_noise_sd` | `0.08` | `NOT_FITTED` | -- | -- | yes | `backtest`, `build_interactive`, `montecarlo` |
| `turnout_pattern_blend` | `0.5` | `NOT_FITTED` | -- | -- | yes | `backtest`, `build_interactive`, `montecarlo` |
| `w_bye` | `0.4` | `NOT_FITTED` | `2021` | -- | yes | `backtest`, `build_interactive`, `montecarlo` |
| `w_bye_local_pr` | `0.0` | `NOT_FITTED` | `2021` | -- | yes | `backtest`, `montecarlo` |
| `w_bye_local_ward` | `0.0` | `NOT_FITTED` | `2021` | -- | yes | `backtest`, `montecarlo` |
| `ward_noise_sd` | `0.1` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |

## 5 · Module constants

`delivered` is membership of `montecarlo.MODULE_CONSTANTS` — the table of names resolved into the run record. `swept` is `MODULE_PERTURB`. `registered` is `JUDGEMENT-CALLS.md`.

| constant | kind | delivered | swept | registered | read elsewhere |
|---|---|---|---|---|---|
| `archive.MANIFEST` | Path('data/archive_manifest.csv') | NO | NO | NO | -- |
| `archive.COLUMNS` | list[5] | NO | NO | NO | `fetch_byelections`, `ingest_lge`, `ingest_npe` |
| `archive.PROVENANCE` | dict[48] | NO | NO | NO | -- |
| `archive.BY_FILENAME` | tuple[22] | NO | NO | NO | -- |
| `arrivals.CITIES` | list[8] | NO | NO | NO | `build_validation`, `compare_history`, `judgement_sheet`, `sweep` |
| `backtest.TARGETS` | _Targets() | NO | NO | NO | `benchmarks` |
| `backtest.FITTED_ON` | dict[8] | NO | NO | NO | `model_index` |
| `backtest.FITTED_ON_UNINSTRUMENTED` | dict[7] | NO | NO | NO | `model_index` |
| `backtest.PROVENANCE_UNSETTLED` | dict[1] | NO | NO | NO | `model_index` |
| `backtest.NOT_FITTED` | dict[25] | NO | NO | NO | `model_index` |
| `benchmarks.SHARE_FLOOR` | float 0.002 | NO | NO | yes | `fold`, `montecarlo` |
| `benchmarks.NEW_PARTY_SIGMA` | float 1.0 | NO | NO | yes | -- |
| `benchmarks.MIN_SIGMA` | float 0.15 | NO | NO | yes | -- |
| `benchmarks.MAX_SIGMA` | float 2.0 | NO | NO | yes | -- |
| `benchmarks.BLEND_W` | float 1.0 | NO | NO | yes | -- |
| `benchmarks.BENCHMARKS` | {'last-lge': last_lge, 'uniform-swing': uniform_swing, 'blended-swing':  | NO | NO | NO | `compare_history` |
| `build_concordance.ELECTIONS` | dict[11] | NO | NO | NO | `build_crosswalk`, `turnout` |
| `build_concordance.REG_DRIFT_TOLERANCE` | float 0.3 | NO | NO | yes | -- |
| `build_crosswalk.ELECTIONS` | dict[6] | NO | NO | NO | `build_concordance`, `turnout` |
| `build_geo.GDB_LAYERS` | dict[2] | NO | NO | NO | -- |
| `build_portal.ELECTION` | str '4 November 2026' | NO | NO | NO | -- |
| `build_portal.PORTAL_CSS` | str | NO | NO | NO | -- |
| `build_site.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | -- |
| `build_site.STYLE` | str | NO | NO | NO | `build_portal` |
| `build_site.NAV_ITEMS` | list[7] | NO | NO | NO | -- |
| `build_site.NAV_CSS` | str | NO | NO | NO | -- |
| `build_site.OG_META` | str | NO | NO | NO | -- |
| `build_site.FOOTER` | str | NO | NO | NO | `build_portal` |
| `build_site.FOOTER_CSS` | str | NO | NO | NO | -- |
| `build_site.NAV_CSS` | NAV_CSS.replace('{FOOTER_CSS_PLACEHOLDER}', FOOTER_CSS) | NO | NO | NO | -- |
| `build_site.DOCS` | dict[5] | NO | NO | NO | -- |
| `build_site.ARTEFACTS` | dict[1] | NO | NO | NO | -- |
| `build_validation.CITIES` | list[8] | NO | NO | NO | `arrivals`, `compare_history`, `judgement_sheet`, `sweep` |
| `build_validation.DISPLAY` | dict[26] | NO | NO | NO | -- |
| `build_validation.BASELINES` | dict[3] | NO | NO | NO | `diagnose` |
| `cityconfig.CITIES_DIR` | Path('cities') | NO | NO | NO | `pools` |
| `cityconfig.DEFAULT_CITY` | str 'joburg' | NO | NO | NO | -- |
| `cityconfig.CALENDAR` | {'1999': Election('1999', 'NPE', _date(1999, 6, 2), 'npe1999_approx_{COD | NO | NO | NO | `backtest`, `benchmarks`, `byelections`, `levels`, `montecarlo`, `pools`, `theta_residual`, `turnout` |
| `compare_history.CITIES` | list[8] | NO | NO | NO | `arrivals`, `build_validation`, `judgement_sheet`, `sweep` |
| `compare_history.GAUTENG` | frozenset({'joburg', 'tshwane', 'ekurhuleni'}) | NO | NO | NO | -- |
| `compare_history.OPPONENT_ORDER` | tuple[3] | NO | NO | NO | -- |
| `compare_history.OPPONENTS_NOT_SCORED` | dict[1] | NO | NO | NO | -- |
| `compare_history.BAND_LABELS` | tuple[3] | NO | NO | NO | -- |
| `compare_history.LEVELS` | tuple[3] | NO | NO | NO | -- |
| `compare_history.POPULATIONS` | tuple[4] | NO | NO | NO | -- |
| `compare_history.REFERENCE_SHARE` | float 0.0025 | NO | NO | yes | -- |
| `compare_history.REFERENCE_SLATE` | float 0.25 | NO | NO | yes | -- |
| `compare_history.HISTORY_SCHEMA` | int 3 | NO | NO | NO | -- |
| `contested_area.TRANSITIONS` | tuple[2] | NO | NO | NO | -- |
| `declares.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `freeze`, `width_budget` |
| `declares.PROCESSED` | REPO / 'data' / 'processed' | NO | NO | NO | `overhang_regimes` |
| `declares.DECLARED` | tuple[3] | NO | NO | NO | -- |
| `declares.LYING` | tuple[3] | NO | NO | NO | -- |
| `declares.UNDECLARED` | tuple[3] | NO | NO | NO | -- |
| `declares.KINDS` | {'spec': Kind('spec', ('code', 'config', 'scope', 'inputs'), '§1.173 — a | NO | NO | NO | -- |
| `deploy_check.ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `judgement_sheet`, `model_index` |
| `derive_city.REPORTS` | Path('data/raw/elections/_reports') | NO | NO | NO | `official_seats` |
| `derive_city.LGE_YEARS` | tuple[3] | NO | NO | NO | -- |
| `diagnose.BASELINES` | scored_opponents() | NO | NO | NO | `build_validation` |
| `diagnose.VERDICT_STATISTIC` | str 'seat_abs_err_coherent' | NO | NO | NO | -- |
| `export_interactive.PAGE_PARTIES` | list[12] | NO | NO | NO | -- |
| `fetch_boundaries.BASE` | str | NO | NO | NO | `fetch_iec` |
| `fetch_boundaries.LAYERS` | dict[4] | NO | NO | NO | -- |
| `fetch_boundaries.FGDB_ITEMS` | dict[2] | NO | NO | NO | -- |
| `fetch_boundaries.USER_AGENT` | str | NO | NO | NO | `fetch_byelections`, `fetch_iec` |
| `fetch_boundaries.PAGE_SIZE` | int 1000 | NO | NO | yes | -- |
| `fetch_byelections.DASH` | str | NO | NO | NO | -- |
| `fetch_byelections.USER_AGENT` | str | NO | NO | NO | `fetch_boundaries`, `fetch_iec` |
| `fetch_byelections.COLUMNS` | list[14] | NO | NO | NO | `archive`, `ingest_lge`, `ingest_npe` |
| `fetch_iec.BASE` | str | NO | NO | NO | `fetch_boundaries` |
| `fetch_iec.USER_AGENT` | str | NO | NO | NO | `fetch_boundaries`, `fetch_byelections` |
| `fetch_iec.LGE_ELECTIONS` | dict[3] | NO | NO | NO | -- |
| `fetch_iec.LGE_REPORTS` | list[5] | NO | NO | NO | -- |
| `fetch_iec.PROVINCE` | str 'GP' | NO | NO | NO | `ingest_historic`, `ingest_lge`, `ingest_npe` |
| `fetch_iec.MUNI` | str 'JHB' | NO | NO | NO | -- |
| `fold.FOLDS` | dict[5] | NO | NO | NO | `model_index`, `montecarlo` |
| `fold.SHARE_FLOOR` | float 0.002 | NO | NO | yes | `benchmarks`, `montecarlo` |
| `fold.LEVEL_FLOOR` | float 1e-06 | NO | NO | yes | -- |
| `freeze.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `declares`, `width_budget` |
| `freeze.DATA` | REPO / 'data/raw/elections' | NO | NO | NO | `width_budget` |
| `freeze.FROZEN` | REPO / 'data/processed/forecast_frozen.json' | NO | NO | NO | -- |
| `freeze.ENV_SWITCHES` | tuple[9] | NO | NO | NO | `model_index` |
| `freeze.ENV_NOT_RECORDED` | dict[1] | NO | NO | NO | -- |
| `gamma_recent.MIN_SHARE` | float 0.005 | NO | NO | yes | -- |
| `hex_cartogram.MARK_START` | str | NO | NO | NO | `render_map` |
| `hex_cartogram.MARK_END` | str '<!-- __HEXMAP_END__ -->' | NO | NO | NO | `render_map` |
| `hex_cartogram.CELL_AREA_FACTOR` | float 1.0 | NO | NO | yes | -- |
| `hex_cartogram.GRID_MARGIN_CELLS` | int 2 | NO | NO | yes | -- |
| `hex_cartogram.PREVIEW` | str | NO | NO | NO | -- |
| `iec_csv.ENCODINGS` | tuple[2] | NO | NO | NO | -- |
| `iec_csv.BOMS` | tuple[2] | NO | NO | NO | -- |
| `ingest_historic.SOURCE_DIR` | Path('data/raw/elections/_source') | NO | NO | NO | -- |
| `ingest_historic.OUT_DIR` | Path('data/raw/elections') | NO | NO | NO | -- |
| `ingest_historic.SPECS` | dict[6] | NO | NO | NO | -- |
| `ingest_historic.METRO_BALLOTS` | dict[2] | NO | NO | NO | -- |
| `ingest_historic.NPE_COLUMNS` | list[10] | NO | NO | NO | -- |
| `ingest_historic.LGE_COLUMNS` | list[11] | NO | NO | NO | -- |
| `ingest_historic.MUNI_HEAD` | dict[5] | NO | NO | NO | -- |
| `ingest_lge.COLUMNS` | list[11] | NO | NO | NO | `archive`, `fetch_byelections`, `ingest_npe` |
| `ingest_npe.COLUMNS` | list[10] | NO | NO | NO | `archive`, `fetch_byelections`, `ingest_lge` |
| `judgement_sheet.ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `deploy_check`, `model_index` |
| `judgement_sheet.SRC` | ROOT / 'src' | NO | NO | NO | `model_index`, `render_sheet` |
| `judgement_sheet.CITIES` | ROOT / 'cities' | NO | NO | NO | `arrivals`, `build_validation`, `compare_history`, `sweep` |
| `judgement_sheet.REGISTER` | ROOT / 'JUDGEMENT-CALLS.md' | NO | NO | NO | `montecarlo`, `polling` |
| `judgement_sheet.OUTPUT` | ROOT / 'JUDGEMENT-SHEET.md' | NO | NO | NO | `model_index` |
| `judgement_sheet.LIVE_TARGET_KEY` | str 'by_year' | NO | NO | NO | -- |
| `levels.SD_FLOOR` | tuple[2] | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.SD_CEILING` | tuple[2] | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.LOG_CHI2_BIAS` | float 1.8873652674492816 | NO | NO | yes | `theta_residual` |
| `levels.SHRINK` | float 2.0 | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.RELIABILITY_HALF` | float 0.002 | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.SPINE_K` | float 1.0 | yes | NO | yes | `montecarlo` |
| `levels.METRO_CODES` | tuple[8] | yes | NO | yes | `contested_area`, `montecarlo`, `polling`, `pools`, `theta_residual` |
| `levels.HELD_BACK` | {} if _HELD_BACK_OFF else {(tag, code): 'pre-2011 history, ingested and  | NO | NO | yes | `pools` |
| `levels.KNOWN_ABSENT` | dict[0] | yes | NO | NO | `montecarlo` |
| `levels.THETA_EXCLUDE_TARGETS` | frozenset((y for y in _os.environ.get('THETA_EXCLUDE_TARGETS', '').split | yes | NO | NO | `freeze`, `montecarlo`, `theta_residual` |
| `levels.TYPE_A_EVENTS` | dict[3] | yes | NO | NO | `montecarlo`, `theta_residual` |
| `levels.FILTER_TYPE_A` | _os.environ.get('FILTER_TYPE_A', '').lower() in ('1', 'true', 'yes') | yes | NO | NO | `freeze`, `montecarlo`, `theta_residual` |
| `levels.DEMARCATION_CROSSING` | frozenset({('MAN', '2011'), ('BUF', '2011')}) | yes | NO | NO | `montecarlo`, `theta_residual` |
| `levels.EXCLUDE_DEMARCATION_CROSSING` | _os.environ.get('EXCLUDE_DEMARCATION_CROSSING', '').lower() in ('1', 'tr | yes | NO | NO | `freeze`, `montecarlo`, `theta_residual` |
| `levels.THETA_WINDOW` | int(_os.environ.get('THETA_WINDOW', '0') or 0) | yes | NO | yes | `freeze`, `montecarlo`, `theta_residual` |
| `model_index.ROOT` | Path(__file__).resolve().parent.parent | NO | NO | NO | `deploy_check`, `judgement_sheet` |
| `model_index.SRC` | ROOT / 'src' | NO | NO | NO | `judgement_sheet`, `render_sheet` |
| `model_index.TESTS` | ROOT / 'tests' | NO | NO | NO | -- |
| `model_index.JUDGEMENT_REGISTER` | ROOT / 'JUDGEMENT-CALLS.md' | NO | NO | NO | -- |
| `model_index.OUTPUT` | ROOT / 'MODEL-INDEX.md' | NO | NO | NO | `judgement_sheet` |
| `model_index.MODEL_ROOT` | str 'montecarlo' | NO | NO | NO | -- |
| `model_index.MEASUREMENT_ROOT` | str 'compare_history' | NO | NO | NO | -- |
| `model_index.MAX_APPORTIONMENT_CHARS` | int 3000 | NO | NO | NO | -- |
| `model_index.MAX_EXPRESSION_CHARS` | int 72 | NO | NO | NO | -- |
| `model_index.MIN_GLOB_FRAGMENT` | int 6 | NO | NO | NO | -- |
| `model_index.SPAN_MARKERS` | tuple[12] | NO | NO | NO | -- |
| `montecarlo.SHARE_FLOOR` | float 0.002 | yes | yes | yes | `benchmarks`, `fold` |
| `montecarlo.COUNCIL` | int 270 | yes | NO | yes | `benchmarks` |
| `montecarlo.DIRICHLET_FLOOR` | float 0.0001 | yes | NO | yes | -- |
| `montecarlo.PLAN_BOUNDS` | dict[0] | yes | NO | yes | `export_interactive` |
| `montecarlo.DEFAULTS` | {'draws': 5000, 'seed': 20261104, 'w_bye': 0.4, 'bye_weight_mode': 'fixe | NO | NO | yes | `backtest`, `benchmarks`, `compare_history`, `export_interactive`, `freeze`, `judgement_sheet`, `model_index`, `stats` |
| `montecarlo.BYE_MIN_WEIGHT` | float 30.0 | yes | yes | yes | -- |
| `montecarlo.TURNOUT_DRAW_FLOOR` | float 0.02 | yes | NO | yes | -- |
| `montecarlo.TURNOUT_DRAW_CEILING` | float 0.95 | yes | yes | yes | -- |
| `montecarlo.WARD_PR_RATIO_MIN` | float 0.5 | yes | NO | yes | -- |
| `montecarlo.WARD_PR_RATIO_MAX` | float 2.0 | yes | NO | yes | -- |
| `montecarlo.LEVEL_DF` | float 7.0 | yes | yes | yes | `theta_residual` |
| `montecarlo.POOL_CAPACITY_MARGIN` | float 0.98 | yes | NO | yes | -- |
| `montecarlo.PARTIAL_BALANCE_PASSES` | int 200 | yes | NO | yes | -- |
| `montecarlo.TURNOUT_CORRELATION` | float 0.63 | yes | NO | yes | -- |
| `montecarlo.GAMMA_FOLD` | dict[4] | yes | NO | yes | `compare_history` |
| `montecarlo.STATUTORY_VALUES` | dict[1] | NO | NO | NO | -- |
| `montecarlo.SCENARIO_METADATA` | tuple[1] | NO | NO | NO | -- |
| `montecarlo.HASH_SEED` | str '0' | yes | NO | NO | `freeze` |
| `montecarlo.DELIVERY_MAX_VALUES` | int 12 | NO | NO | NO | -- |
| `montecarlo.DELIVERY_MAX_CHARS` | int 2000 | NO | NO | NO | -- |
| `montecarlo.MODULE_CONSTANTS` | dict[5] | NO | NO | yes | `model_index` |
| `montecarlo.FROZEN_DEFAULTS` | frozenset({('levels', 'METRO_CODES'), ('polling', 'REGISTER')}) | NO | NO | NO | -- |
| `montecarlo.OVERHANG_RULES` | tuple[4] | NO | NO | NO | -- |
| `montecarlo.OVERHANG_DEDUCT_MAX_ROUNDS_SLACK` | int 2 | NO | NO | yes | -- |
| `montecarlo.OVERHANG_LEVEL_MAX_ROUNDS` | int 200 | NO | NO | yes | -- |
| `official_seats.REPORTS` | Path('data/raw/elections/_reports') | NO | NO | NO | `derive_city` |
| `official_seats.LABELS` | dict[5] | NO | NO | NO | -- |
| `overhang_regimes.PROCESSED` | Path('data/processed') | NO | NO | NO | `declares` |
| `overhang_regimes.RULES` | tuple[3] | NO | NO | NO | -- |
| `parties.PARTIES` | dict[9] | NO | NO | NO | `build_crosswalk`, `pools` |
| `parties.ALIASES` | dict[17] | yes | NO | NO | `montecarlo`, `pools` |
| `parties.MINOR_ALIASES` | dict[22] | yes | NO | NO | `build_crosswalk`, `montecarlo`, `pools` |
| `polling.REGISTER` | Path('polls.json') | yes | NO | NO | `judgement_sheet`, `montecarlo` |
| `polling.POLL_RMS_ERROR_2016` | float 0.0303 | NO | NO | yes | -- |
| `polling.POLL_CAL_N_2016` | int 800 | NO | NO | yes | -- |
| `polling.POLL_CAL_DEFF_2016` | float 1.3 | NO | NO | yes | -- |
| `polling.POLL_HOUSE_SD` | float 0.025 | yes | NO | yes | `montecarlo` |
| `polling.POLL_DEFF_SUBSAMPLE` | float 1.6 | NO | NO | yes | -- |
| `polling.POLL_DEFF_STANDALONE` | float 1.2 | yes | NO | yes | `montecarlo` |
| `polling.POLL_SCREEN_SD_UNDISCLOSED` | float 0.02 | NO | NO | yes | -- |
| `polling.POLL_DRIFT_PP_PER_ROOT_DAY` | float 0.001 | yes | NO | yes | `montecarlo` |
| `polling.SIGMA_COMMON` | float 0.015 | yes | NO | yes | `montecarlo` |
| `polling.SIGMA_IDIO` | float 0.015 | yes | NO | yes | `montecarlo` |
| `polling.SIGMA_DRIFT_PER_ROOT_DAY` | float 0.003 | yes | NO | yes | `montecarlo` |
| `polling.SIGMA_VOLATILITY` | float 0.008 | yes | NO | yes | `montecarlo` |
| `polling.SIGMA_TWO_TERM` | _os.environ.get('SIGMA_TWO_TERM', '1').lower() in ('1', 'true', 'yes') | yes | yes | yes | `freeze`, `montecarlo` |
| `polling.POLL_HOUSE_K` | float 1.0 | yes | NO | yes | `montecarlo` |
| `polling.POLL_MIN_N` | int 300 | yes | NO | yes | `montecarlo` |
| `polling.POLL_HALF_LIFE_DAYS` | float 120.0 | yes | NO | yes | `montecarlo` |
| `polling.CAMPAIGN_WINDOW_DAYS` | int 550 | yes | NO | yes | `montecarlo` |
| `polling.NATIONAL_VOTES` | {'2016': int(26333353 * 0.5794), '2021': int(26204579 * 0.4579)} | yes | NO | NO | `contested_area`, `montecarlo` |
| `polling.PROJECTED_METRO_SHARE` | dict[8] | yes | NO | yes | `montecarlo` |
| `polling.SCOPES` | frozenset({'national', 'metro', 'metro-aggregate', 'province'}) | NO | NO | NO | -- |
| `pools.LOCK_PATH` | Path('data/processed/.pools.lock') | NO | NO | NO | -- |
| `pools.CONFIG` | Path('config/dimensions.toml') | NO | NO | NO | -- |
| `pools.SOLVE_TOL` | float 1e-09 | NO | NO | yes | -- |
| `pools.SIMULATION_BLOC` | dict[4] | NO | NO | yes | -- |
| `pools.REGISTRATION_MAX` | float 2.0 | NO | NO | yes | -- |
| `pools.NATIONAL_ONLY_FLOOR` | float 0.001 | NO | NO | yes | -- |
| `pools.PRIOR_LOCAL_FLOOR` | float 0.001 | NO | NO | yes | -- |
| `pools.POOL_LOSS_CAUSES` | tuple[4] | NO | NO | NO | -- |
| `pools.CENSUS_UNSAFE_REASONS` | tuple[4] | NO | NO | NO | -- |
| `pools.CENSUS_COVERAGE_FLOOR` | float 0.8 | NO | NO | yes | -- |
| `pools.CENSUS_DRIFT_CEILING` | float 0.05 | NO | NO | yes | -- |
| `pools.DRIFT_UNMEASURABLE` | _DriftUnmeasurable() | NO | NO | NO | -- |
| `pools.METRO_CODES` | tuple[8] | yes | NO | yes | `contested_area`, `levels`, `montecarlo`, `polling`, `theta_residual` |
| `pools.MIN_HOME_SPLITS` | int 2 | NO | NO | yes | -- |
| `pools.SPLINTER_PARENT_WEIGHT` | float 0.35 | NO | NO | yes | -- |
| `pools.SPLITS` | {'COPE': Split('ANC', ('2004', '2009'), "Lekota and Shilowa, after the A | NO | NO | yes | -- |
| `pools.ARRIVAL_DEFINITIONS` | {'ARRIVED_VS_NATIONAL': ArrivalDefinition(predicate='local share > 0 and | NO | NO | NO | `model_index` |
| `pools.ARRIVAL_BAND_LO` | float 0.25 | NO | NO | yes | -- |
| `pools.ARRIVAL_BAND_HI` | float 0.95 | NO | NO | yes | -- |
| `pools.ALPHA_MIN_SHARE` | float 0.01 | NO | NO | yes | -- |
| `pools.ALPHA_FLOOR` | float 1.0 | NO | NO | yes | -- |
| `pools.ALPHA_CEILING` | float 200.0 | NO | NO | yes | -- |
| `pools.ALPHA_FALLBACK` | float 12.0 | NO | NO | yes | -- |
| `pools.SPLIT_SD_FLOOR` | float 0.9 | NO | NO | yes | -- |
| `pools.NPE_CITYWIDE_STATES` | tuple[4] | NO | NO | NO | -- |
| `pools.NPE_CITYWIDE_UNREACHABLE` | tuple((s for s in NPE_CITYWIDE_STATES if s != 'read')) | NO | NO | NO | -- |
| `pools.MAX_POOL_CAPTURE` | float 0.9 | NO | NO | yes | -- |
| `pools.UNCLASSIFIED_FLOOR` | float 0.005 | NO | NO | yes | -- |
| `pools.ROSTER_DROP_CEILING` | float 0.015 | NO | NO | yes | -- |
| `pools.ROSTER_KEYS` | dict[5] | NO | NO | NO | -- |
| `pools.KNOWN_PARTY_CODES` | set(P.PARTIES) | set(P.ALIASES.values()) | set(P.MINOR_ALIASES.values()) | NO | NO | NO | -- |
| `pools.LINEAGE_TABLES` | set[2] | NO | NO | NO | -- |
| `pools.PARTY_KEYS` | dict[5] | NO | NO | yes | -- |
| `prep_logos.CODES` | dict[12] | NO | NO | NO | -- |
| `prep_logos.MISSING` | list[4] | NO | NO | NO | -- |
| `publication.SCHEMA` | int 1 | NO | NO | NO | -- |
| `publication.LEDGER_ROOT` | Path('publications') | NO | NO | NO | `build_site` |
| `publication.CHANGE_CLASSES` | tuple[4] | NO | NO | NO | `build_site` |
| `publication.PRELEDGER_PREFIX` | str 'r-preledger-' | NO | NO | NO | -- |
| `publication.AS_OF_RECONSTRUCTED` | str | NO | NO | NO | -- |
| `publication.MOVEMENTS` | tuple[6] | NO | NO | NO | -- |
| `render_map.CHIPS` | dict[11] | NO | NO | NO | `render_sheet` |
| `render_map.NAMES` | dict[8] | NO | NO | NO | `render_sheet` |
| `render_map.GREY` | str '#9aa09a' | NO | NO | NO | `hex_cartogram` |
| `render_map.MARK_START` | str '<!-- __MAP_START__ -->' | NO | NO | NO | `hex_cartogram` |
| `render_map.MARK_END` | str '<!-- __MAP_END__ -->' | NO | NO | NO | `hex_cartogram` |
| `render_map.DISTRICTS` | [(d['name'], float(d['lon']), float(d['lat'])) for d in _MAP.get('labels | NO | NO | NO | -- |
| `render_map.W` | float(_MAP.get('width', 840.0)) | NO | NO | NO | `hex_cartogram` |
| `render_map.COS` | float(_MAP.get('cos_lat', 0.898)) | NO | NO | NO | -- |
| `render_map.ANG` | math.radians(float(_MAP.get('rotate_deg', 40))) | NO | NO | NO | -- |
| `render_map.STRIPE_MIN` | float 0.1 | NO | NO | NO | -- |
| `render_map.UNKNOWN_CHIP` | str '#5f6660' | NO | NO | NO | -- |
| `render_map.REST` | str '__rest__' | NO | NO | NO | -- |
| `render_map.SAFE` | float 0.9 | NO | NO | yes | -- |
| `render_map.TIP_FLOOR` | float 0.05 | NO | NO | yes | -- |
| `render_map.OTHER_FLOOR` | float 0.005 | NO | NO | yes | -- |
| `render_map.KEY_SOLID` | tuple[3] | NO | NO | NO | -- |
| `render_map.KEY_STRIPE_A` | tuple[3] | NO | NO | NO | -- |
| `render_map.KEY_STRIPE_B` | tuple[3] | NO | NO | NO | -- |
| `render_map.KEY_PARTIES` | tuple[8] | NO | NO | NO | -- |
| `render_sheet.CHIPS` | dict[12] | NO | NO | NO | `render_map` |
| `render_sheet.NAMES` | dict[15] | NO | NO | NO | `render_map` |
| `render_sheet.CHART_PARTIES` | list[10] | NO | NO | NO | -- |
| `render_sheet.ALLIANCE_8` | tuple[8] | NO | NO | NO | -- |
| `scenarios.OPS` | {'>=': operator.ge, '<=': operator.le, '>': operator.gt, '<': operator.l | NO | NO | NO | -- |
| `scenarios.COND` | re.compile('^\\s*([A-Za-z_]+)\\s*(>=|<=|==|>|<)\\s*(\\d+)\\s*$') | NO | NO | NO | -- |
| `score.CLAIM_FRACTION` | float 0.5 | NO | NO | yes | `compare_history` |
| `seats.INDEPENDENT` | str 'INDEPENDENT' | NO | NO | NO | `backtest`, `benchmarks`, `montecarlo`, `parties`, `validate_seats` |
| `stats.UNVERIFIABLE` | str 'unverifiable' | NO | NO | NO | -- |
| `stats.DECLARATION_MIN_CHARS` | int 12 | NO | NO | NO | -- |
| `stats.HISTORICAL` | str 'historical' | NO | NO | NO | -- |
| `stats.TOKEN` | re.compile('\\{\\{([a-z0-9_]+)\\}\\}') | NO | NO | NO | -- |
| `stats.GEN_TOKEN` | re.compile('\\{\\{@([A-Za-z0-9_.+\\-]+)=([^;{}]*);([a-z0-9_]*);([^{}]*)\ | NO | NO | NO | -- |
| `stats.REFERENCE_ARTEFACT` | str 'forecast_summary.json' | NO | NO | NO | -- |
| `stats.FRESHNESS_GRACE_S` | float 300.0 | NO | NO | yes | -- |
| `stats.FRESHNESS_REMEDY` | dict[1] | NO | NO | NO | -- |
| `stats.SOURCED` | re.compile('<span[^>]*data-token="[^"]*".*?</span>', re.S) | NO | NO | NO | -- |
| `stats.TAGS` | re.compile('<[^>]+>') | NO | NO | NO | -- |
| `stats.SCRIPTS` | re.compile('<(script|style)[^>]*>.*?</\\1>', re.S) | NO | NO | NO | -- |
| `stats.NUMBERISH` | re.compile(f'(?P<date>\\b\\d{{1,2}}\\s(?:{_MONTHS})\\s\\d{{4}}\\b|\\b\\d | NO | NO | NO | -- |
| `stats.GATING` | tuple[3] | NO | NO | NO | `build_site` |
| `stats.GENERATED_MARKERS` | frozenset({'MAP', 'HEXMAP', 'BALLOTS', 'REGIMES'}) | NO | NO | NO | -- |
| `stats.REGION` | re.compile('<!-- __([A-Z]+)_START__ -->(.*?)<!-- __\\1_END__ -->', re.S) | NO | NO | NO | -- |
| `stats.ATTRS` | re.compile('\\b(?:title|data-tip|aria-label|alt|content)="([^"]*)"') | NO | NO | NO | -- |
| `stats.CHROME_CLASSES` | tuple[5] | NO | NO | NO | -- |
| `stats.SCRIPT_FORBIDDEN` | (('a data block', re.compile('\\b(?:const|let|var)\\s+[A-Za-z_$][\\w$]*\ | NO | NO | NO | -- |
| `stats.CLAIM_PATTERNS` | tuple[10] | NO | NO | NO | -- |
| `stats.STAT_CSS` | str | NO | NO | NO | -- |
| `sweep.CITIES` | list[8] | NO | NO | NO | `arrivals`, `build_validation`, `compare_history`, `judgement_sheet` |
| `sweep.PARTY_ROW` | re.compile("^\\s{2}([A-Z][A-Z0-9_']*)\\s+(\\d+)\\s+(\\d+)\\s+([\\d.]+)\\ | NO | NO | NO | -- |
| `theta_residual.BINS` | tuple[5] | NO | NO | yes | -- |
| `theta_residual.BOOT` | int 4000 | NO | NO | NO | -- |
| `theta_residual.BOOT_SEED` | int 20211101 | NO | NO | NO | -- |
| `theta_residual.SIM_DRAWS` | int 4000000 | NO | NO | NO | -- |
| `theta_residual.NULL_REPS` | int 20000 | NO | NO | NO | -- |
| `turnout.ELECTIONS` | {year: (e.results, e.two_ballot) for year, e in sorted(cityconfig.CALEND | NO | NO | NO | `build_concordance`, `build_crosswalk` |
| `turnout.LAMBDA_PAIRS` | {year: (cityconfig.preceding(year, 'NPE'), year) for year, e in sorted(c | NO | NO | NO | -- |
| `width_budget.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `declares`, `freeze` |
| `width_budget.DATA` | REPO / 'data/raw/elections' | NO | NO | NO | `freeze` |

## 6 · Folds and windows

Every name that declares a SPAN — of folds, of history, of recency — matched on the name and then read off the object.

| name | where | value | spans |
|---|---|---|---|
| `bye_tau_months` | `montecarlo.DEFAULTS` | 18.0 | -- |
| `poll_half_life_days` | `montecarlo.DEFAULTS` | 120.0 | -- |
| `LGE_YEARS` | `derive_city` | tuple[3] | -- |
| `FOLDS` | `fold` | dict[5] | -- |
| `THETA_WINDOW` | `levels` | int(_os.environ.get('THETA_WINDOW', '0') or 0) | -- |
| `SPAN_MARKERS` | `model_index` | tuple[12] | -- |
| `GAMMA_FOLD` | `montecarlo` | dict[4] | -- |
| `POLL_HALF_LIFE_DAYS` | `polling` | float 120.0 | -- |
| `CAMPAIGN_WINDOW_DAYS` | `polling` | int 550 | -- |
| `FOLDS[1]` | `fold` | -- | base=('npe2014_{CODE}_vd_party.csv', None); lambda_pair=('2009', '2011'); prior_lge='2011'; target=('lge2016_{CODE}_vd_party_clean.csv', True) |
| `FOLDS[2]` | `fold` | -- | base=('npe2019_{CODE}_vd_party.csv', None); lambda_pair=('2014', '2016'); prior_lge='2016'; target=('lge2021_{CODE}_vd_party_clean.csv', True) |
| `FOLDS[3]` | `fold` | -- | base=('npe2009_{CODE}_vd_party.csv', None); lambda_pair=('2004', '2006'); prior_lge='2006'; target=('lge2011_{CODE}_vd_party_clean.csv', True) |
| `FOLDS[4]` | `fold` | -- | base=('npe2004_{CODE}_vd_party.csv', None); lambda_pair=('1999', '2000'); prior_lge='2000'; target=('lge2006_{CODE}_vd_party_clean.csv', True) |
| `FOLDS[5]` | `fold` | -- | base=('npe1999_approx_{CODE}_vd_party.csv', None); lambda_pair=None; prior_lge=None; target=('lge2000_{CODE}_vd_party_clean.csv', True) |
| `ARRIVED_VS_LOCAL_EXCLUDING_SPLITS_WITH_REACH` | `pools.ARRIVAL_DEFINITIONS` | -- | predicate='preceding-LGE share <= 1e-4 < share, party not in SPLITS, and the party has a MEASURED ward reach'; population='consecutive LGE pairs; a party with a national record but no local one IS an arrival here and is NOT one above'; splits='EXCLUDED'; computed_in='entrant_record'; consumed_by='comparators(): the per-entrant SIZE record' |
| `ARRIVED_VS_NATIONAL` | `pools.ARRIVAL_DEFINITIONS` | -- | predicate='local share > 0 and preceding-NPE share <= 0, party != IND'; population='every metro x every LGE year that has a preceding NPE'; splits='INCLUDED'; computed_in='arrival_group_record -> total'; consumed_by='arrival_group_spec: the group TOTAL and its Dirichlet a' |
| `ARRIVED_VS_NATIONAL_EXCLUDING_SPLITS` | `pools.ARRIVAL_DEFINITIONS` | -- | predicate='ARRIVED_VS_NATIONAL and party not in SPLITS'; population='the same rows; a strictly smaller set within each'; splits='EXCLUDED'; computed_in='arrival_group_record -> entrants'; consumed_by='_arrival_total_prior: the group BUDGET, which arrival_rules spends only over entrant_sizes' |
| `SEEDABLE_AT_TARGET` | `pools.ARRIVAL_DEFINITIONS` | -- | predicate='on the roster, absent from the fitted composition, not IND or ENTRANT, and preceding-NPE baseline <= 0'; population='one target city-year; a forecast set, not a record'; splits='INCLUDED (a split is seeded, then SIZED off its parent)'; computed_in='emit_pools -> newcomers'; consumed_by='arrival_rules: who actually receives a seed' |
| `UNCLASSIFIED_WITH_NATIONAL_RECORD` | `pools.ARRIVAL_DEFINITIONS` | -- | predicate='on the roster, absent from the fitted composition, no parent from classify_arrival, and preceding-NPE baseline >= UNCLASSIFIED_FLOOR'; population='one target city-year; DISJOINT from SEEDABLE_AT_TARGET by construction, since one needs baseline <= 0 and the other baseline > 0'; splits='n/a - by construction these have no declared lineage'; computed_in='emit_pools -> unclassified'; consumed_by="the emitted spec's `unclassified_with_national_record`: the nomination-day flag, not a size" |

## 7 · Methods on the model and measurement paths

Every public function in the import closure of `montecarlo` or of `compare_history`. A statistic that is not here is not invoked by a forecast or by the scoring of one, whatever its name suggests.

| function | path | summary | callers |
|---|---|---|---|
| `backtest.runnable_targets` | measurement | Past local elections this harness can actually run, for one city. | `arrivals`, `benchmarks`, `compare_history`, `sweep`, `tests/test_covariate_fail_open`, `tests/test_levers_are_live`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed` |
| `backtest.register` | measurement | ``FITTED_ON`` and ``FITTED_ON_UNINSTRUMENTED`` as one mapping. | `model_index`, `tests/test_chain`, `tests/test_intermediates_are_current`, `tests/test_levers_are_live`, `tests/test_register_matches_code`, `tests/test_stage_estimation` |
| `backtest.unsettled` | measurement | :data:`PROVENANCE_UNSETTLED` keys this run held that could bite here. | `tests/test_levers_are_live`, `tests/test_stage_inputs` |
| `backtest.contaminated` | measurement | ``FITTED_ON`` keys that read this target or later, minus declared ones. | `compare_history`, `tests/test_chain`, `tests/test_levers_are_live`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs` |
| `backtest.check_derived_from` | measurement | Validate a scenario's ``derived_from`` list; return it as strings. | -- |
| `backtest.in_sample_banner` | measurement | The warning (or the all-clear) for one scenario at one target. | `compare_history`, `tests/test_levers_are_live` |
| `backtest.relabel_entrant` | measurement | Rename the generic ``ENTRANT`` to the party that actually arrived. | `tests/test_regressions` |
| `backtest.ward_structure` | measurement | VD -> ward and VD -> registered, from the target's own result file. | `benchmarks` |
| `backtest.actual_result` | measurement | The real council and the real ward winners, checked against the IEC. | `arrivals`, `benchmarks`, `compare_history`, `diagnose`, `tests/test_covariate_fail_open`, `tests/test_roster_aware_baseline` |
| `backtest.arrival_baseline` | measurement | **THE ONE DEFINITION OF "HAS A BASELINE" IN THIS REPOSITORY.** | `compare_history`, `tests/test_covariate_fail_open`, `tests/test_panel_wiring` |
| `backtest.entrant_actual_for_target` | measurement | Which party arrived from nothing at ``target``. **The one call path.** | `compare_history`, `diagnose`, `tests/test_covariate_fail_open`, `tests/test_panel_wiring` |
| `backtest.entrant_actual_for` | measurement | Which party actually arrived from nothing, if any. | `tests/test_covariate_fail_open`, `tests/test_panel_wiring`, `tests/test_regressions` |
| `backtest.arrival_group_score` | measurement | Score the arrival channel as a GROUP, with **no per-party label**. | `compare_history`, `tests/test_calibration_report`, `tests/test_panel_wiring` |
| `backtest.relabel_run` | measurement | Rename the generic ``ENTRANT`` **on the run itself**, once, in place. | `compare_history`, `tests/test_calibration_report`, `tests/test_regressions` |
| `benchmarks.sources_for` | measurement | Files each baseline needs that the backtest's TARGETS table does not name. | -- |
| `benchmarks.council_size` | measurement | Seats in the target's council, from the city config's per-year structure. | `build_site`, `coalitions`, `montecarlo`, `render_map`, `render_sheet`, `stats` |
| `benchmarks.build_context` | measurement | Gather every pre-election input the baselines need. | `compare_history`, `diagnose`, `tests/test_covariate_fail_open`, `tests/test_roster_aware_baseline` |
| `benchmarks.canonical_order` | measurement | The same tally, ordered ``(most votes first, then by NAME)``. | `tests/test_roster_aware_baseline` |
| `benchmarks.council_from_shares` | measurement | Turn VD-level ballot shares into ``({party: seats}, {ward: winner})``. | -- |
| `benchmarks.last_lge` | measurement | "The last local election happens again." Deterministic. | -- |
| `benchmarks.uniform_swing` | measurement | The last local election, shifted by the national swing that bracketed it. | `tests/test_roster_aware_baseline` |
| `benchmarks.blended_swing` | measurement | Uniform swing DAMPED toward persistence — the professional reference. | -- |
| `benchmarks.roster_split` | measurement | Who on the target's ballot the baseline already has, and who is new. | `tests/test_roster_aware_baseline` |
| `benchmarks.arrival_budget` | measurement | What parties arriving in one metro take BETWEEN THEM, measured before | `tests/test_roster_aware_baseline` |
| `benchmarks.newcomer_shares` | measurement | The declared prior each roster newcomer enters at. Pre-target only. | `tests/test_roster_aware_baseline` |
| `benchmarks.uniform_swing_roster` | measurement | ``uniform-swing``, given the ballot. The honest opponent at 2021. | `tests/test_covariate_fail_open`, `tests/test_roster_aware_baseline` |
| `benchmarks.prior_lge_noise` | measurement | ``last-lge`` with a spread calibrated on the previous local transition. | -- |
| `benchmarks.run_one` | measurement | Seat draws only -- the shape ``score.score_seats`` takes. | `diagnose` |
| `benchmarks.run_with_wards` | measurement | ``(seat_draws, ward_winner_draws)``. | `compare_history`, `tests/test_panel_wiring` |
| `benchmarks.ward_probabilities` | measurement | ``{ward: {party: P(win)}}`` from a list of per-draw winner maps. | `backtest`, `compare_history`, `diagnose`, `montecarlo` |
| `cityconfig.preceding` | model+measurement | The last election of `kind` strictly before `year`, or None. | `benchmarks`, `levels`, `pools`, `tests/test_chain`, `tests/test_data_coverage`, `tests/test_levels_dispersion`, `tests/test_theta_prior`, `theta_residual`, `turnout` |
| `cityconfig.load` | model+measurement | -- | `arrivals`, `backtest`, `benchmarks`, `build_geo`, `build_interactive`, `build_portal`, `compare_history`, `diagnose`, `export_interactive`, `fetch_boundaries`, `fold`, `gamma_recent`, `montecarlo`, `polling`, `pools`, `render_map`, `render_sheet`, `scenarios`, `stats`, `sweep`, `tests/test_artefact_key_discriminates`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scenarios`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_ward_pr_ratios`, `theta_residual` |
| `cityconfig.use` | model+measurement | Set the active city for this process. | `arrivals`, `backtest`, `benchmarks`, `build_all`, `build_concordance`, `build_crosswalk`, `build_geo`, `build_site`, `byelections`, `coalitions`, `compare_history`, `diagnose`, `export_interactive`, `fold`, `freeze`, `gamma_recent`, `ingest_historic`, `ingest_lge`, `ingest_npe`, `montecarlo`, `pools`, `render_map`, `render_sheet`, `scenarios`, `tests/_support`, `tests/test_build_all`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_data_coverage`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levers_are_live`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_publication_ledger`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `turnout`, `validate_seats`, `width_budget` |
| `cityconfig.active` | model+measurement | -- | `backtest`, `benchmarks`, `build_crosswalk`, `build_site`, `diagnose`, `export_interactive`, `fold`, `iec_csv`, `ingest_lge`, `ingest_npe`, `montecarlo`, `publication`, `tests/_support`, `tests/test_covariate_fail_open`, `tests/test_pool_conservation`, `tests/test_roster_aware_baseline`, `tests/test_spine`, `tests/test_theta_prior`, `tests/test_ward_parts`, `turnout`, `validate_seats` |
| `cityconfig.use_target` | model+measurement | Set the active target election; None means the active city's next one. | `arrivals`, `backtest`, `build_site`, `byelections`, `coalitions`, `compare_history`, `diagnose`, `export_interactive`, `freeze`, `gamma_recent`, `montecarlo`, `pools`, `render_sheet`, `scenarios`, `tests/test_chain`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_fails_closed`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_ward_parts`, `theta_residual`, `turnout`, `width_budget` |
| `cityconfig.target` | model+measurement | -- | `arrivals`, `backtest`, `benchmarks`, `build_concordance`, `build_site`, `build_validation`, `byelections`, `coalitions`, `compare_history`, `declares`, `diagnose`, `export_interactive`, `fold`, `freeze`, `gamma_recent`, `judgement_sheet`, `levels`, `model_index`, `montecarlo`, `polling`, `pools`, `render_map`, `render_sheet`, `scenarios`, `sweep`, `tests/_support`, `tests/test_artefact_key_discriminates`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_panel_wiring`, `tests/test_polling_register`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scoreboard_disclosure`, `tests/test_solve_and_predict`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_theta_prior`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `theta_residual`, `turnout` |
| `cityconfig.resolve_path` | model+measurement | Substitute {CODE}/{SLUG} in a path or filename. | `backtest`, `build_concordance`, `build_crosswalk`, `build_geo`, `byelections`, `compare_history`, `fold`, `montecarlo`, `render_map`, `tests/test_covariate_fail_open`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `turnout` |
| `cityconfig.add_city_argument` | model+measurement | Standard ``--city`` flag; every script defaults to Johannesburg so | `backtest`, `benchmarks`, `build_all`, `build_concordance`, `build_crosswalk`, `build_geo`, `build_interactive`, `build_site`, `byelections`, `coalitions`, `export_interactive`, `fold`, `gamma_recent`, `ingest_historic`, `ingest_lge`, `ingest_npe`, `montecarlo`, `pools`, `render_map`, `render_sheet`, `scenarios`, `turnout`, `validate_seats` |
| `cityconfig.add_target_argument` | model+measurement | Standard ``--target`` flag: which election is being built. | `byelections`, `gamma_recent`, `montecarlo`, `pools`, `turnout` |
| `coalitions.subset_totals` | model+measurement | Seat totals for every subset. seats: (draws, n) -> (2**n, draws). | -- |
| `coalitions.minimal_winning` | model+measurement | Mask -> boolean per draw: is this subset a *minimal* winning coalition. | -- |
| `coalitions.banzhaf` | model+measurement | Banzhaf index per party per draw, normalised to sum to 1. | -- |
| `coalitions.shapley_shubik` | model+measurement | Shapley–Shubik index per party per draw. | -- |
| `coalitions.minority_viable` | model+measurement | Arithmetic viability of a minority administration, per draw. | -- |
| `coalitions.mask_label` | model+measurement | -- | -- |
| `coalitions.analyse` | model+measurement | Run the full §3.8 suite. Returns a dict of result tables. | `montecarlo` |
| `coalitions.report` | model+measurement | -- | `contested_area`, `declares`, `fetch_iec`, `fold`, `levels`, `montecarlo`, `tests/test_published_page`, `tests/test_regressions`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe`, `tests/test_stat_freshness`, `theta_residual` |
| `coalitions.write_outputs` | model+measurement | -- | `montecarlo` |
| `compare_history.scored_opponents` | measurement | Every reference in `benchmarks.BENCHMARKS` bar those explicitly refused. | `diagnose`, `tests/test_scoreboard_disclosure` |
| `compare_history.opponent_columns` | measurement | The reference columns a REPORT prints: the scored set, plus the artefact's. | `tests/test_scoreboard_disclosure` |
| `compare_history.runnable` | measurement | Targets this city can actually run, AND why each other one cannot. | `backtest`, `benchmarks`, `fold`, `sweep`, `tests/test_roster_fails_closed`, `tests/test_standalone_modules` |
| `compare_history.actual_shares` | measurement | The target's own citywide PR and ward shares. Scoring only. | `backtest` |
| `compare_history.vote_table` | measurement | Per-party predicted vs actual on both ballots, MEAN AND MEDIAN. | -- |
| `compare_history.rank_band_of` | measurement | ``party -> rank band``, ranked by the party's ACTUAL citywide PR share. | `tests/test_calibration_report` |
| `compare_history.rank_bands` | measurement | Error by where a party sits on the ballot, which is where it fails. | `tests/test_calibration_report` |
| `compare_history.pit_dispersion` | measurement | Width, with the LEVEL divided out: ``sd(Phi^-1(u))``. **1.0 is right.** | `tests/test_calibration_report` |
| `compare_history.dispersion_ratio` | measurement | The exact level-free width statistic: ``sd`` of the standardised error. | -- |
| `compare_history.reference_universe` | measurement | The calibration population, selected on INPUTS ONLY. | -- |
| `compare_history.calibration_columns` | measurement | Per-column PIT values and interval hits, UNPOOLED, for one city-year. | `tests/test_calibration_report`, `tests/test_scoreboard_disclosure` |
| `compare_history.redraw_pits` | measurement | PIT values redrawn ``replicates`` times from the stored jump intervals. | `tests/test_calibration_report`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe` |
| `compare_history.exact_mean_pit` | measurement | The mean PIT over the randomisation, in closed form: ``mean(lo + w/2)``. | `tests/test_calibration_report` |
| `compare_history.pooled_calibration` | measurement | Coverage and PIT summed over every city-year, pooled AND split by rank. | `tests/test_calibration_report`, `tests/test_scoreboard_disclosure` |
| `compare_history.pooled_by_band` | measurement | The pooled calibration of one population, SPLIT BY ACTUAL PR RANK. | `tests/test_calibration_report`, `tests/test_scoreboard_disclosure` |
| `compare_history.vote_mae` | measurement | Mean absolute error on citywide share, in percentage points. | -- |
| `compare_history.seats_from_draws` | measurement | Median seats per party over a list of {party: seats} dicts. | `diagnose`, `tests/test_diagnose_baselines`, `tests/test_scoreboard_disclosure` |
| `compare_history.coherent_seats` | measurement | A point forecast that IS a council: largest remainder on the mean vector. | `diagnose`, `tests/test_diagnose_baselines`, `tests/test_regressions`, `tests/test_scoreboard_disclosure` |
| `compare_history.seat_abs_err` | measurement | Total absolute seat error over the UNION of the two party sets. | `diagnose`, `tests/test_calibration_report`, `tests/test_scoreboard_disclosure` |
| `compare_history.chamber_fill` | measurement | What a forecaster's OWN draws fill, before apportionment rescales them. | `diagnose`, `tests/test_scoreboard_disclosure`, `tests/test_stage_realisation` |
| `compare_history.ward_winner_accuracy` | measurement | How many ward contests were called right. **THE GEOGRAPHY-SENSITIVE KEY.** | -- |
| `compare_history.run_city_year` | measurement | -- | `tests/test_calibration_report`, `tests/test_panel_wiring`, `tests/test_scoreboard_disclosure` |
| `compare_history.render_calibration` | measurement | The calibration block: pooled over city-years, SPLIT BY RANK BAND. | `tests/test_calibration_report`, `tests/test_scoreboard_disclosure` |
| `compare_history.render_wards` | measurement | The ward-winner table — the only key in this report that sees geography. | `tests/test_scoreboard_disclosure` |
| `compare_history.render` | measurement | -- | `build_interactive`, `build_portal`, `build_site`, `hex_cartogram`, `judgement_sheet`, `stats`, `tests/test_calibration_report`, `tests/test_hex_cartogram`, `tests/test_publication_ledger`, `tests/test_published_page`, `tests/test_scoreboard_disclosure` |
| `compare_history.moved_module_constants` | measurement | ``(moved, unwatched)`` — what would not survive a fork, and what is blind. | -- |
| `compare_history.build_manifest` | measurement | What produced this scoreboard, assembled from `freeze`'s existing code. | `tests/test_provenance_gates` |
| `compare_history.load_history` | measurement | Read a scoreboard artefact, and REFUSE the pre-manifest shape. | `tests/test_calibration_report`, `tests/test_pool_bounds`, `tests/test_scoreboard_disclosure` |
| `fold.logit` | model+measurement | -- | `montecarlo`, `tests/test_solve_and_predict` |
| `fold.load` | model+measurement | Return VD -> canonical party -> votes, and VD -> ward. | `arrivals`, `backtest`, `benchmarks`, `build_geo`, `build_interactive`, `build_portal`, `cityconfig`, `compare_history`, `diagnose`, `export_interactive`, `fetch_boundaries`, `gamma_recent`, `montecarlo`, `polling`, `pools`, `render_map`, `render_sheet`, `scenarios`, `stats`, `sweep`, `tests/test_artefact_key_discriminates`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scenarios`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_ward_pr_ratios`, `theta_residual` |
| `fold.shares` | model+measurement | -- | `benchmarks`, `export_interactive`, `gamma_recent`, `levels`, `montecarlo`, `pools`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_panel_wiring`, `tests/test_prior_local_fails_closed`, `tests/test_roster_aware_baseline`, `tests/test_scoreboard_disclosure`, `tests/test_stage_realisation` |
| `fold.citywide` | model+measurement | -- | `arrivals`, `backtest`, `benchmarks`, `build_concordance`, `compare_history`, `diagnose`, `export_interactive`, `gamma_recent`, `montecarlo`, `pools`, `tests/test_chain`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_roster_aware_baseline`, `tests/test_ward_pr_ratios`, `turnout` |
| `fold.fit_gamma` | model+measurement | Regress target logit-deviation on baseline logit-deviation, through the origin. | `gamma_recent` |
| `fold.expit` | model+measurement | -- | `montecarlo` |
| `fold.predict` | model+measurement | Apply the §3.4(b) share model, renormalised within each VD. | `tests/test_regressions`, `turnout` |
| `fold.predicted_citywide` | model+measurement | -- | `tests/test_regressions` |
| `fold.calibrate_theta` | model+measurement | Solve for the θ that reproduces the target's citywide shares *through* the model. | `tests/test_regressions` |
| `fold.load_parameters` | model+measurement | Read a fold's fitted parameters back in, for out-of-sample transfer. | `export_interactive`, `montecarlo` |
| `fold.turnout_weights` | model+measurement | Votes cast per VD in the target election, under one turnout specification. | -- |
| `fold.suspect_vds` | model+measurement | VDs flagged as possibly redrawn for a given election (see build_concordance). | -- |
| `fold.citywide_counts` | model+measurement | -- | -- |
| `freeze.resolved_switches` | measurement | What the switches were, as the modules RESOLVED them. | `compare_history` |
| `freeze.pool_artefact_keys` | measurement | The `artefact_key` of every emitted spec for this city. | `build_site`, `compare_history`, `declares`, `publication`, `tests/test_provenance_gates` |
| `freeze.run_forecast` | measurement | -- | -- |
| `freeze.bundle` | measurement | -- | -- |
| `iec_csv.active_muni_code` | model+measurement | The active city's IEC municipality code — the row filter for every | `ingest_lge`, `ingest_npe` |
| `iec_csv.sniff_encoding` | model+measurement | Return an encoding that decodes ``src``: its BOM if it has one, else a guess. | `derive_city`, `ingest_lge`, `ingest_npe` |
| `iec_csv.normalise_header` | model+measurement | Fold a raw header cell to an upper-snake-case key. | `ingest_lge`, `ingest_npe` |
| `iec_csv.is_int` | model+measurement | -- | `ingest_npe` |
| `iec_csv.muni_code` | model+measurement | -- | `ingest_lge`, `ingest_npe` |
| `iec_csv.ward_number` | model+measurement | Reduce ``Ward 79800001`` to ``79800001``; pass anything else through. | `ingest_lge` |
| `iec_csv.write_csv` | model+measurement | -- | `ingest_lge`, `ingest_npe` |
| `iec_csv.summarise` | model+measurement | Format a turnout and party-share summary, for eyeballing against plan §8. | `build_site`, `ingest_lge`, `ingest_npe`, `publication`, `tests/test_publication_ledger` |
| `ingest_lge.read_municipality` | model+measurement | Return the rows of ``src`` for one municipality, with canonical columns. | `contested_area`, `ingest_npe`, `polling`, `pools`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach` |
| `levels.ballot_roster` | model+measurement | The party NAMES on one result file's ballot. Names only, never votes. | `tests/test_levels_dispersion`, `tests/test_roster_fails_closed` |
| `levels.absent_from_ballot` | model+measurement | Parties holding baseline share that are NOT standing at the target. | `montecarlo`, `tests/test_levels_dispersion`, `tests/test_projected_roster_declaration`, `theta_residual` |
| `levels.theta_record` | model+measurement | Every observed national-to-local retention ratio before the target. | `tests/test_chain`, `tests/test_regressions`, `tests/test_spine`, `tests/test_theta_prior`, `theta_residual` |
| `levels.projected_contestation` | model+measurement | A slate for a target whose nomination lists are not published yet. | `montecarlo` |
| `levels.local_record` | model+measurement | Every observed LOCAL-to-LOCAL retention ratio before the target. | `tests/test_regressions`, `tests/test_spine` |
| `levels.theta_prior` | model+measurement | Per-party (low, mode, high) on θ, and the groups they were drawn from. | `montecarlo`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_theta_prior`, `theta_residual` |
| `levels.size_centre` | model+measurement | The centre θ shrinks TOWARD, as a function of how big the party is. | `tests/test_spine`, `tests/test_stage_estimation`, `theta_residual` |
| `levels.spine` | model+measurement | Each party's central level at the target, from BOTH of its records. | `backtest`, `montecarlo`, `tests/test_blended_centres`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_stage_inputs` |
| `levels.ward_pr_ratios` | model+measurement | Each party's ward-ballot share over its PR share, from the last LGE. | `montecarlo`, `tests/test_ward_pr_ratios` |
| `levels.contestation` | model+measurement | The fraction of wards each party fields a ward candidate in. | `backtest`, `compare_history`, `montecarlo`, `pools`, `tests/test_chain`, `tests/test_levers_are_live` |
| `montecarlo.logit` | model+measurement | -- | `fold`, `tests/test_solve_and_predict` |
| `montecarlo.expit` | model+measurement | -- | `fold` |
| `montecarlo.triangular` | model+measurement | -- | -- |
| `montecarlo.log_shock` | model+measurement | exp of a Student-t scaled to have log-sd exactly ``sd``. Median 1. | `tests/test_ipf_feasibility`, `tests/test_regressions`, `width_budget` |
| `montecarlo.capped_targets` | model+measurement | Hold every column target under its cap WITHOUT changing the total. | `tests/test_ipf_feasibility` |
| `montecarlo.partial_balance` | model+measurement | Alternating scaling for margins that CANNOT both hold. Ends on the rows. | `tests/test_ipf_feasibility` |
| `montecarlo.correlated_triangular` | model+measurement | A triangular draw pushed by a shared standard normal. | `width_budget` |
| `montecarlo.months_before_election` | model+measurement | How long before election day a by-election was held, in months. | -- |
| `montecarlo.fold_target_year` | model+measurement | The year of the LGE a fold predicts, read off its target filename. | -- |
| `montecarlo.gamma_fold_for` | model+measurement | The fold supplying γ for this target, checked to precede it. | `backtest` |
| `montecarlo.read_ward_crosswalk` | model+measurement | The VD→ward crosswalk: ``([(vd, ward, part_registered), ...], vds, split)``. | `export_interactive`, `pools`, `tests/test_ward_parts` |
| `montecarlo.ward_parts` | model+measurement | VD → ward parts and their registration: ``[(vd, ward, registered), ...]``. | `build_concordance`, `tests/test_ward_parts` |
| `montecarlo.solve_and_predict` | model+measurement | Solve for θ reaching `target` citywide through the model; return VD shares. | `tests/test_solve_and_predict` |
| `montecarlo.parse_set` | model+measurement | Apply --set key=value overrides; values parsed as JSON where possible. | -- |
| `montecarlo.apply_city` | model+measurement | Point the module's constants at this city, from a CLEAN baseline. | `arrivals`, `backtest`, `benchmarks`, `compare_history`, `diagnose`, `freeze`, `tests/test_chain`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levers_are_live`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `width_budget` |
| `montecarlo.fix_hash_seed` | model+measurement | Re-exec this process once under a fixed ``PYTHONHASHSEED``. | `backtest`, `compare_history`, `diagnose`, `freeze`, `overhang_regimes`, `sweep`, `tests/run_all`, `tests/test_calibration_report`, `tests/test_provenance_gates` |
| `montecarlo.note_value` | model+measurement | Record that ``name`` was consulted AT ``value``, and return ``value``. | `tests/test_delivery_proof` |
| `montecarlo.note_module_constants` | model+measurement | Record what THIS PROCESS holds for every declared module constant. | `tests/test_delivery_proof` |
| `montecarlo.delivery_log` | model+measurement | The value-bearing read log of a run, from whatever holds it. | `backtest` |
| `montecarlo.assert_delivered` | model+measurement | Prove that ``name`` reached the run, at ``expected``. Raise if it did not. | `tests/test_delivery_proof` |
| `montecarlo.note_constant` | model+measurement | Record that a hand-typed constant was actually consumed by this run. | -- |
| `montecarlo.read_scenario_file` | model+measurement | ``(overrides, metadata)`` from a scenario JSON, unknown keys rejected. | `backtest` |
| `montecarlo.blend_poll_centre` | model+measurement | Blend a poll reading into a modelled centre. Returns ``(centre, w)``. | `tests/test_blended_centres`, `tests/test_regressions` |
| `montecarlo.apply_overrides` | model+measurement | Merge a validated override dict into a scenario, dicts key by key. | `backtest` |
| `montecarlo.load_scenario` | model+measurement | -- | `arrivals`, `compare_history`, `diagnose`, `freeze`, `tests/test_chain`, `tests/test_levers_are_live`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_fails_closed`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `width_budget` |
| `montecarlo.blended_centres` | model+measurement | Central citywide level per party at the target, from θ modes tilted by evidence. | `tests/test_blended_centres`, `tests/test_drawer`, `tests/test_ipf_feasibility` |
| `montecarlo.compress_levels` | model+measurement | Pull each central level down by its own size, then give the mass back. | `tests/test_chain`, `tests/test_stage_estimation` |
| `montecarlo.pool_spec` | model+measurement | Build the per-pool draw specification for the weighted engine (§1.29). | `tests/test_drawer`, `tests/test_pool_conservation` |
| `montecarlo.make_drawer` | model+measurement | Return a function drawing one citywide PR target vector. | `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_conservation` |
| `montecarlo.allocate_with_overhang` | model+measurement | Schedule 1 allocation with the excessive-seats treatment. | `benchmarks`, `tests/test_overhang` |
| `montecarlo.roster_for_target` | model+measurement | Who is on ``target``'s ballot, and WHICH of four states that answer is in. | `benchmarks`, `tests/test_projected_roster_declaration`, `tests/test_roster_fails_closed` |
| `montecarlo.run_model` | model+measurement | Run the forecast for one target election. | `arrivals`, `backtest`, `compare_history`, `diagnose`, `freeze`, `tests/test_chain`, `tests/test_levers_are_live`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_fails_closed`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_ward_pr_ratios`, `width_budget` |
| `official_seats.read` | measurement | Official figures for one municipality-year, or None if not on disk. | `archive`, `backtest`, `build_crosswalk`, `compare_history`, `fetch_boundaries`, `fetch_byelections`, `fetch_iec`, `pools`, `tests/run_all`, `tests/test_chain`, `tests/test_data_coverage`, `tests/test_freeze`, `tests/test_prior_local_fails_closed`, `tests/test_scoreboard_disclosure`, `tests/test_seats`, `tests/test_stage_inputs`, `validate_seats` |
| `parties.normalise` | model+measurement | Fold a raw party string: upper case, collapsed whitespace, tidy dashes. | `prep_logos` |
| `parties.canonical` | model+measurement | Return the canonical code for a raw party string. | `backtest`, `build_crosswalk`, `byelections`, `contested_area`, `fold`, `freeze`, `levels`, `pools`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_freeze`, `tests/test_roster_aware_baseline` |
| `parties.display_name` | model+measurement | -- | `build_crosswalk` |
| `parties.is_modelled` | model+measurement | True if the party carries its own theta parameter in plan §3.5. | `build_crosswalk` |
| `polling.design_effect` | model+measurement | How much of the recorded ``n`` is real information. | `tests/test_polling_sd` |
| `polling.effective_n` | model+measurement | ``n / deff`` — the sample size that is actually doing work. | `levels`, `tests/test_polling_sd`, `tests/test_stage_estimation`, `tests/test_theta_prior` |
| `polling.poll_sd` | model+measurement | Total error on one poll's reading of one party, in share units. | `tests/test_polling_sd` |
| `polling.sd_components` | model+measurement | The same four numbers, unsummed, so they can be printed and traced. | `tests/test_polling_sd` |
| `polling.effective_houses` | model+measurement | Kish effective count of independent HOUSES, over recency weights. | `montecarlo`, `tests/test_polling_sd`, `tests/test_polling_synthetic` |
| `polling.weight_cap` | model+measurement | The most weight a poll may take, given how many houses stand behind it. | `montecarlo`, `tests/test_polling_sd`, `tests/test_polling_synthetic` |
| `polling.blend_weight` | model+measurement | Inverse-variance weight on the poll. The professional mechanism. | `montecarlo`, `tests/test_polling_synthetic` |
| `polling.load` | model+measurement | -- | `arrivals`, `backtest`, `benchmarks`, `build_geo`, `build_interactive`, `build_portal`, `cityconfig`, `compare_history`, `diagnose`, `export_interactive`, `fetch_boundaries`, `fold`, `gamma_recent`, `montecarlo`, `pools`, `render_map`, `render_sheet`, `scenarios`, `stats`, `sweep`, `tests/test_artefact_key_discriminates`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scenarios`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_ward_pr_ratios`, `theta_residual` |
| `polling.validate` | model+measurement | Every way a poll record is BROKEN, as opposed to inapplicable. | `tests/test_polling_register` |
| `polling.validate_or_die` | model+measurement | Load and validate, or raise. The entry point everything else uses. | `montecarlo`, `tests/test_polling_register` |
| `polling.screen` | model+measurement | Admitted polls, and every exclusion WITH ITS REASON. | `montecarlo`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_polling_sd` |
| `polling.metro_polls` | model+measurement | The admitted polls that are a reading OF THIS CITY. One definition. | `tests/test_regressions` |
| `polling.national_polls` | model+measurement | The admitted polls that are a reading of the country. See metro_polls. | `montecarlo` |
| `polling.usable_for` | model+measurement | Polls whose fieldwork ended before this target's polling day. | `tests/test_polling_register` |
| `polling.aggregate` | model+measurement | One set of numbers from several polls, weighted by recency. | `montecarlo` |
| `polling.sigma_floor` | model+measurement | The sigma these polls cannot cross however much fieldwork is added. | `tests/test_polling_synthetic` |
| `polling.house_ceiling` | model+measurement | The most of the blend these houses can ever take, at any sample size. | `tests/test_polling_synthetic` |
| `polling.aggregate_sd` | model+measurement | Total error on the AGGREGATE's reading of one party. | `montecarlo`, `tests/test_polling_synthetic` |
| `polling.contested_share` | model+measurement | What fraction of the national roll sits in the municipalities listed. | -- |
| `polling.votes_by_metro` | model+measurement | Votes cast per metro on the PR ballot, from the published result files. | `contested_area`, `montecarlo` |
| `polling.metro_estimate` | model+measurement | A national poll number converted to a share of each contested metro. | `montecarlo` |
| `pools.artefact_lock` | model+measurement | Hold the pool-artefact lock. ``mode`` is "emit" (exclusive) or "read". | `compare_history`, `tests/run_all` |
| `pools.artefact_key` | model+measurement | What an emitted spec was built FROM, so staleness can be detected. | `declares`, `freeze`, `montecarlo`, `tests/test_artefact_key_discriminates`, `tests/test_chain`, `tests/test_provenance_gates`, `tests/test_stage_inputs` |
| `pools.stale_reason` | model+measurement | Why this spec should not be trusted for this run, or None. | `montecarlo`, `tests/test_artefact_key_discriminates`, `tests/test_chain`, `tests/test_stage_inputs` |
| `pools.load_config` | model+measurement | -- | `montecarlo`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.read_census` | model+measurement | One census: ward -> composition over this dimension, summing to 1. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.read_census_population` | model+measurement | Ward -> the population this dimension's categories are counted over. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.vote_located_bloc` | model+measurement | Locate a voter bloc the census cannot see, using a party that only it votes for. | `tests/test_chain` |
| `pools.ward_totals` | model+measurement | Ward -> registered voters, and ward -> votes cast. Both published. | `benchmarks`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain` |
| `pools.pool_counts` | model+measurement | Build the four nested levels for one city and election. | `montecarlo`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.pool_losses` | model+measurement | Every city-year a pool record dropped since this process started. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.registration_series` | model+measurement | Each pool's share of the registered roll, at every election on disk. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.projected_pool_shares` | model+measurement | Carry each pool's share of the roll forward to the target election. | -- |
| `pools.vd_map` | model+measurement | VD -> ward, and VD -> registered voters, as at one election. | `montecarlo`, `tests/test_declared_reach_matches_ward_reach` |
| `pools.reproject` | model+measurement | Move a ward-level composition from one delimitation onto another. | -- |
| `pools.delimitation_for` | model+measurement | Which delimitation an election was fought on. | `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain` |
| `pools.reproject_counts` | model+measurement | Move a ward-level COUNT from one delimitation onto another. | `tests/test_chain` |
| `pools.composition_at` | model+measurement | Ward composition interpolated to a decimal year. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.polling_decimal_year` | model+measurement | Polling day as a decimal year, without demanding council structure. | -- |
| `pools.ward_party_shares` | model+measurement | Ward -> {party: share}, and ward -> votes cast. | -- |
| `pools.fit_joint` | model+measurement | Fit every party's pool rates at once, subject to what must be true. | `tests/test_chain` |
| `pools.balance_margins` | model+measurement | Force both margins of the party x pool vote matrix to their known totals. | `montecarlo`, `tests/test_pool_bounds` |
| `pools.balance_within_bounds` | model+measurement | :func:`balance_margins`, with the method of bounds as a third truth. | `tests/test_pool_bounds` |
| `pools.bounds` | model+measurement | Duncan-Davis method of bounds: what the arithmetic alone allows. | `build_interactive`, `export_interactive`, `tests/test_blended_centres`, `tests/test_pool_bounds` |
| `pools.fit_city` | model+measurement | Fit every party's pool vector from one city's ward results. | `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.metro_file` | model+measurement | -- | `contested_area`, `polling`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach` |
| `pools.metro_citywide` | model+measurement | One metro's citywide party shares, through the same cleaner the city | `tests/test_chain`, `tests/test_temporal` |
| `pools.turnout_record` | model+measurement | Turnout per pool at every prior election of one kind. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.turnout_band` | model+measurement | (low, mode, high) turnout per pool: last election, widened by history. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.panel_turnout_spread` | model+measurement | How far EACH pool's turnout moves between local elections, panel-wide. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.turnout_limits` | model+measurement | What a reader may set turnout to, and the rule tying the two sliders. | `export_interactive` |
| `pools.constrain_pool_turnout` | model+measurement | Project a reader's per-pool turnouts back inside the citywide range. | `tests/test_regressions` |
| `pools.registered_at_target` | model+measurement | How many registered voters each pool holds at the target. | -- |
| `pools.pool_totals` | model+measurement | Each pool's share of the total vote. | -- |
| `pools.lge_transitions` | model+measurement | Consecutive local-election pairs, optionally ending before a target. | `tests/test_chain` |
| `pools.measure_pool_ratios` | model+measurement | How much a pool's vote total moves between elections, IN ONE CITY. | `tests/test_chain` |
| `pools.dirichlet_alpha` | model+measurement | Method of moments: alpha + 1 = m(1-m)/Var, over members that matter. | -- |
| `pools.classify_arrival` | model+measurement | SPLIT OR ENTRANT — the definition, and the only place that decides. | `tests/test_chain` |
| `pools.entrant_record` | model+measurement | Every share won by a party that arrived FROM NOTHING. | `tests/test_chain` |
| `pools.home_splinter_record` | model+measurement | What each split took OF ITS PARENT, measured in its leader's own city. | `tests/test_regressions` |
| `pools.splinter_record` | model+measurement | What share of its parent's vote each known splinter took, measured. | `tests/test_chain`, `tests/test_regressions` |
| `pools.pooled_splinter_record` | model+measurement | Every away-splinter fraction observed in any metro, for the spread. | -- |
| `pools.arrival_group_record` | model+measurement | What ARRIVALS TAKE AS A GROUP in a metro, and how concentrated it is. | `benchmarks`, `tests/test_chain`, `tests/test_roster_aware_baseline` |
| `pools.arrival_group_spec` | model+measurement | The group total to draw, and how to split it between named arrivals. | `tests/test_declared_reach_matches_ward_reach` |
| `pools.metro_roster` | model+measurement | Who stood in ONE metro, by IEC code. Names only, never votes. | `montecarlo`, `tests/test_temporal` |
| `pools.contesting_parties` | model+measurement | Who is on the ballot at the target. Names only, never votes. | `montecarlo`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_prior_local_fails_closed`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed` |
| `pools.arrival_rules` | model+measurement | How a party that was not here last time takes its votes. | `tests/test_chain` |
| `pools.capture_shortfall` | model+measurement | How much of ``share`` the ``MAX_POOL_CAPTURE`` clip silently removed. | `tests/test_chain` |
| `pools.lineage_path` | model+measurement | -- | `tests/test_artefact_key_discriminates`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_prior_local_fails_closed` |
| `pools.declared_roster` | model+measurement | A nomination list declared by hand, from `[roster]` in the judgement file. | `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach` |
| `pools.load_lineage` | model+measurement | -- | `tests/test_chain` |
| `pools.write_lineage_template` | model+measurement | Ask for the judgements the model cannot make, with defaults filled in. | -- |
| `pools.city_mix_for` | model+measurement | The city's own pool composition — where this city's votes actually are. | -- |
| `pools.resolve_roster` | model+measurement | Who is on the ballot at ``target``, and who may be deleted from the pools. | `tests/test_chain`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration` |
| `pools.emit_pools` | model+measurement | Build the ``scenario["pools"]`` structure from measurement. | `tests/test_chain` |
| `pools.gate` | model+measurement | Fit on one city, predict another, and see whether a tilt helped. | `build_site`, `model_index`, `tests/test_levers_are_live` |
| `score.seat_matrix` | measurement | ``(parties, samples[n_draws, n_parties], actual[n_parties])``. | `compare_history`, `montecarlo`, `tests/test_calibration_report`, `tests/test_chain` |
| `score.relevant_parties` | measurement | A candidate party universe covering several forecasters. | `benchmarks` |
| `score.hold_universe` | measurement | The column set several forecasters are to be COMPARED on. | `compare_history`, `tests/test_panel_wiring`, `tests/test_scored_universe` |
| `score.universe_key` | measurement | A stable fingerprint of a scored column SET, order-insensitive. | `compare_history`, `tests/test_panel_wiring`, `tests/test_scored_universe` |
| `score.comparable` | measurement | Were these forecasters scored on the same columns? **The #13 predicate.** | `compare_history`, `tests/test_panel_wiring`, `tests/test_scored_universe` |
| `score.crps_sample` | measurement | Continuous Ranked Probability Score of one marginal. **Lower is better.** | -- |
| `score.crps_by_party` | measurement | Per-party CRPS plus the mean and total. **Lower is better.** | `tests/test_scored_universe` |
| `score.column_rng` | measurement | THE PIT column key. One definition, because two would drift. | `compare_history` |
| `score.pit_intervals` | measurement | The jump each randomised PIT lands inside: ``(F(y⁻), F(y) − F(y⁻))``. | `compare_history`, `tests/test_calibration_report` |
| `score.pit_values` | measurement | Randomised probability integral transform, one value per party. | `compare_history`, `tests/test_calibration_report` |
| `score.chi2_crit_95` | measurement | χ²(0.95) at a possibly FRACTIONAL ``dof``. One table, extended. | `compare_history`, `tests/test_calibration_report`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe` |
| `score.pit_histogram` | measurement | Bin the PIT values and say what the shape means. **Flat is the target.** | `compare_history`, `tests/test_calibration_report` |
| `score.cluster_bootstrap` | measurement | Percentile interval for a pooled statistic, resampling CLUSTERS. | `compare_history`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe`, `theta_residual` |
| `score.chi2_clustered` | measurement | Is the pooled PIT histogram flatter than CLUSTERED noise? **The test.** | `compare_history`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe` |
| `score.coverage` | measurement | Empirical coverage of central intervals. **Match the nominal level** — | `backtest`, `benchmarks`, `compare_history`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_scoreboard_disclosure` |
| `score.ward_events` | measurement | Flatten ward forecasts to binary events: "party P wins ward W". | -- |
| `score.brier_score` | measurement | Mean squared error of binary probability forecasts. **Lower is better.** | -- |
| `score.brier_multicategory` | measurement | Per-ward multi-category Brier, summed over parties. **Lower is better.** | `backtest`, `benchmarks`, `compare_history`, `tests/test_scoreboard_disclosure` |
| `score.reliability_table` | measurement | Predicted-probability bucket vs observed frequency. **Diagonal is right.** | -- |
| `score.brier_decomposition` | measurement | Murphy decomposition ``BS = reliability - resolution + uncertainty``. | -- |
| `score.score_wards` | measurement | Everything ward-shaped in one call: Brier, reliability table, hit rate. | `backtest`, `benchmarks`, `compare_history` |
| `score.energy_score` | measurement | Energy score of the *joint* seat vector. **Lower is better.** | `tests/test_scored_universe` |
| `score.variogram_score` | measurement | Variogram score of order p on the joint seat vector. **Lower is better.** | `tests/test_scored_universe` |
| `score.score_seats` | measurement | Score a seat forecast end to end. Returns a dict; see :func:`format_report`. | `backtest`, `benchmarks`, `compare_history`, `tests/test_chain`, `tests/test_panel_wiring`, `tests/test_regressions`, `tests/test_scored_universe` |
| `score.format_report` | measurement | Human-readable block for a :func:`score_seats` / :func:`score_wards` pair. | `backtest`, `benchmarks`, `tests/test_regressions` |
| `seats.eligible_parties` | model+measurement | Return combined ward+PR votes for parties that count towards the quota. | `backtest`, `benchmarks`, `fold`, `montecarlo`, `tests/test_seats`, `tests/test_stage_realisation`, `validate_seats` |
| `seats.outside_pool_wards` | model+measurement | Split ward wins into the entitlement pool and the C and D terms. | `benchmarks`, `montecarlo` |
| `seats.allocate` | model+measurement | Allocate council seats by the Schedule 1 quota-and-largest-remainder method. | `backtest`, `fold`, `montecarlo`, `tests/test_overhang`, `tests/test_seats`, `tests/test_stage_realisation`, `validate_seats` |
| `seats.pr_seats` | model+measurement | Split each party's entitlement into ward and PR councillors. | -- |
| `seats.overhang` | model+measurement | Return the parties whose ward wins exceed their entitlement, and by how much. | `tests/test_regressions` |
| `turnout.read_turnout` | model+measurement | Return VD -> (registered, votes cast). | `fold` |
| `turnout.turnout_series` | model+measurement | Return election -> VD -> turnout, plus the citywide figure per election. | -- |
| `turnout.citywide` | model+measurement | -- | `arrivals`, `backtest`, `benchmarks`, `build_concordance`, `compare_history`, `diagnose`, `export_interactive`, `fold`, `gamma_recent`, `montecarlo`, `pools`, `tests/test_chain`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_roster_aware_baseline`, `tests/test_ward_pr_ratios` |

## 8 · Modules

| module | path | entry point | importers | summary |
|---|---|---|---|---|
| `archive` | neither | NO | `tests/test_data_coverage` | Inventory every raw input with a checksum and its provenance. |
| `arrivals` | neither | yes | -- | Every party that arrived from nothing, and what the model said about it. |
| `backtest` | measurement | NO | `src/arrivals`, `src/benchmarks`, `src/compare_history`, `src/diagnose`, `src/sweep`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_levers_are_live`, `tests/test_panel_wiring`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs` | Score the forecast model against an election that has already happened. |
| `benchmarks` | measurement | NO | `src/compare_history`, `src/diagnose`, `tests/test_covariate_fail_open`, `tests/test_diagnose_baselines`, `tests/test_roster_aware_baseline`, `tests/test_scoreboard_disclosure` | Naive forecasters, so the model has something to beat. |
| `build_all` | neither | NO | `tests/test_build_all` | Build one city end to end, then the site around it. |
| `build_concordance` | neither | NO | `tests/test_ward_parts` | Build the VD concordance and the VD -> 2026 ward apportionment (plan §2, steps 2 and 5). |
| `build_crosswalk` | neither | yes | -- | Build and check the party crosswalk across every source file. |
| `build_geo` | neither | yes | -- | Extract the CoJ subsets from the downloaded boundaries and check them. |
| `build_interactive` | neither | yes | -- | Assemble forecast-interactive.html from the template and the data packs. |
| `build_portal` | neither | yes | -- | Build the portal at whysoserious.city — one card per city. |
| `build_site` | neither | NO | `src/build_portal`, `tests/test_publication_ledger`, `tests/test_published_page`, `tests/test_stat_freshness` | Build the public site (joburg.whysoserious.org) into ./site. |
| `build_validation` | neither | yes | -- | Run the validation across every metro and write the page that reports it. |
| `byelections` | neither | yes | -- | By-election evidence for the target election (plan §3.6, §3.3 covariate). |
| `cityconfig` | model+measurement | NO | `src/arrivals`, `src/backtest`, `src/benchmarks`, `src/build_all`, `src/build_concordance`, `src/build_crosswalk`, `src/build_geo`, `src/build_interactive`, `src/build_portal`, `src/build_site`, `src/byelections`, `src/coalitions`, `src/compare_history`, `src/diagnose`, `src/export_interactive`, `src/fold`, `src/freeze`, `src/gamma_recent`, `src/iec_csv`, `src/ingest_historic`, `src/ingest_lge`, `src/ingest_npe`, `src/levels`, `src/montecarlo`, `src/polling`, `src/pools`, `src/publication`, `src/render_map`, `src/render_sheet`, `src/scenarios`, `src/sweep`, `src/theta_residual`, `src/turnout`, `src/validate_seats`, `src/width_budget`, `tests/_support`, `tests/test_artefact_key_discriminates`, `tests/test_build_all`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_data_coverage`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_publication_ledger`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scoreboard_disclosure`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_theta_prior`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios` | The city and the target election are parameters, not assumptions. |
| `coalitions` | model+measurement | NO | `src/montecarlo` | Coalition arithmetic over Monte Carlo seat draws (plan §3.8). |
| `compare_history` | measurement | NO | `src/diagnose`, `tests/test_calibration_report`, `tests/test_diagnose_baselines`, `tests/test_panel_wiring`, `tests/test_pool_bounds`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe` | Every past election we can run, as votes and as seats, against every opponent. |
| `contested_area` | neither | yes | -- | Validate the contested-area conversion — the table `polling.py` asserted. |
| `declares` | neither | NO | `tests/test_provenance_gates` | Does every artefact declare what produced it? One table, at a glance. |
| `deploy_check` | neither | NO | `tests/test_number_scan` | Refuse a Cloudflare deploy of a site whose numbers were not reviewed. |
| `derive_city` | neither | yes | -- | Propose a city's config from its own IEC files. |
| `diagnose` | neither | NO | `tests/test_diagnose_baselines`, `tests/test_scoreboard_disclosure` | One election, laid out so a fault can be ISOLATED rather than summarised. |
| `export_interactive` | neither | yes | -- | Export the data pack for the interactive forecast page. |
| `fetch_boundaries` | neither | yes | -- | Download CoJ ward and voting-district boundaries from the MDB Spatial Knowledge Hub. |
| `fetch_byelections` | neither | yes | -- | Download every municipal by-election result since the 2021 LGE, at VD level. |
| `fetch_iec` | neither | yes | -- | Download every IEC report the model needs that is reachable without a browser. |
| `fold` | model+measurement | NO | `src/arrivals`, `src/backtest`, `src/benchmarks`, `src/compare_history`, `src/diagnose`, `src/export_interactive`, `src/gamma_recent`, `src/montecarlo`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_ward_pr_ratios` | Backtest a national/provincial baseline against a local-government target (plan §4). |
| `freeze` | measurement | NO | `src/compare_history`, `src/declares`, `src/publication`, `tests/test_freeze`, `tests/test_provenance_gates` | Freeze a stage-1 forecast, and hash everything that could move it. |
| `gamma_recent` | neither | yes | -- | Fit γ on the last LGE→NPE transition for parties fold 1 never saw (review A4). |
| `hex_cartogram` | neither | NO | `tests/test_hex_cartogram` | An equal-area hex tile cartogram: one hexagon per ward, one ward per hexagon. |
| `iec_csv` | model+measurement | NO | `src/derive_city`, `src/ingest_lge`, `src/ingest_npe` | Shared helpers for reading IEC result CSVs. |
| `ingest_historic` | neither | NO | `tests/test_data_coverage` | Ingest the pre-2011 IEC bulk archives into the project's canonical VD files. |
| `ingest_lge` | model+measurement | NO | `src/contested_area`, `src/polling`, `src/pools`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach` | Ingest IEC local-government election results to a JHB VD-level subset. |
| `ingest_npe` | neither | yes | -- | Ingest IEC national/provincial election bulk result files to a JHB VD-level subset. |
| `judgement_sheet` | neither | NO | `tests/test_judgement_sheet` | The judgement calls, laid out for a person rather than for a grep. |
| `levels` | model+measurement | NO | `src/compare_history`, `src/contested_area`, `src/freeze`, `src/montecarlo`, `src/pools`, `src/theta_residual`, `tests/test_chain`, `tests/test_data_coverage`, `tests/test_delivery_proof`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_fails_closed`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_theta_prior`, `tests/test_ward_pr_ratios` | How big each party will be, measured instead of typed. |
| `model_index` | neither | NO | `src/judgement_sheet`, `tests/test_judgement_sheet`, `tests/test_model_index` | One index of every lever, constant, fold, window and method, JOINED. |
| `montecarlo` | model+measurement | NO | `src/arrivals`, `src/backtest`, `src/benchmarks`, `src/compare_history`, `src/diagnose`, `src/export_interactive`, `src/freeze`, `src/overhang_regimes`, `src/pools`, `src/stats`, `src/sweep`, `src/theta_residual`, `src/width_budget`, `tests/run_all`, `tests/test_blended_centres`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_delivery_proof`, `tests/test_drawer`, `tests/test_freeze`, `tests/test_ipf_feasibility`, `tests/test_levers_are_live`, `tests/test_overhang`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scoreboard_disclosure`, `tests/test_solve_and_predict`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_stat_freshness`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios` | Monte Carlo forecast of a metro council (plan §3.4–§3.8, review fixes). |
| `official_seats` | measurement | NO | `src/backtest`, `src/build_crosswalk`, `src/validate_seats`, `tests/test_seats` | Read the IEC's own Seat Calculation Detail as the validation ground truth. |
| `overhang_regimes` | neither | yes | -- | Run the excessive-seats counterfactuals for the regime-comparison table. |
| `parties` | model+measurement | NO | `src/backtest`, `src/build_crosswalk`, `src/byelections`, `src/contested_area`, `src/fold`, `src/ingest_historic`, `src/levels`, `src/pools`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_delivery_proof` | Party name normalisation: many ballot spellings, one code per party. |
| `polling` | model+measurement | NO | `src/contested_area`, `src/freeze`, `src/montecarlo`, `tests/test_delivery_proof`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_polling_sd`, `tests/test_polling_synthetic` | Polls, filtered by date and converted from national numbers to metro ones. |
| `pools` | model+measurement | NO | `src/benchmarks`, `src/compare_history`, `src/contested_area`, `src/declares`, `src/montecarlo`, `src/polling`, `tests/run_all`, `tests/test_artefact_key_discriminates`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_delivery_proof`, `tests/test_panel_wiring`, `tests/test_pool_bounds`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_stage_inputs`, `tests/test_temporal`, `tests/test_ward_parts` | Voter pools: what a party talks to, measured rather than asserted. |
| `prep_logos` | neither | yes | -- | Normalise party logos into consistent square badges. |
| `publication` | neither | NO | `src/build_site`, `tests/test_publication_ledger` | The publication ledger: what this page said, when, and which model said it. |
| `render_map` | neither | NO | `src/hex_cartogram`, `tests/test_hex_cartogram`, `tests/test_map_stripes` | Render the ward-winner map into the forecast pages. |
| `render_sheet` | neither | yes | -- | Regenerate forecast-sheet.html's data block from the model outputs. |
| `scenarios` | neither | NO | `src/render_map`, `src/render_sheet`, `tests/test_scenarios` | Which simulations make a scenario, and what their wards did. |
| `score` | measurement | NO | `src/backtest`, `src/benchmarks`, `src/compare_history`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_panel_wiring`, `tests/test_regressions`, `tests/test_scored_universe` | Proper scoring rules for a distributional forecast of a council. |
| `seats` | model+measurement | NO | `src/backtest`, `src/benchmarks`, `src/fold`, `src/levels`, `src/montecarlo`, `src/validate_seats`, `tests/test_overhang`, `tests/test_seats`, `tests/test_stage_realisation` | Seat allocation for a metro council, per Municipal Structures Act Schedule 1. |
| `stats` | neither | NO | `src/build_interactive`, `src/build_site`, `tests/test_number_scan`, `tests/test_publication_ledger`, `tests/test_published_page`, `tests/test_stat_freshness` | The stat registry: no model result is ever typed into prose by hand. |
| `sweep` | neither | yes | -- | Run the model over every metro-year we can score, and hunt for anomalies. |
| `theta_residual` | neither | NO | `tests/test_levels_dispersion` | The CONDITIONAL dispersion of log θ — the quantity `SD_FLOOR` claims to be. |
| `turnout` | model+measurement | NO | `src/fold` | VD-level turnout series and the λ drop-off factors (plan §3.3). |
| `validate_seats` | neither | yes | -- | Check :mod:`seats` against the IEC's published seat calculation. |
| `width_budget` | neither | yes | -- | Attribute the forecast's realised width to the layers that produce it. |

## 9 · Registers, and which test modules name them

A mention is not a check. It is the cheap half of the question, and it is enough to see a register no test names at all.

| register | defined in | named by tests |
|---|---|---|
| `ARRIVAL_DEFINITIONS` | `pools` | `test_chain`, `test_panel_wiring` |
| `CONDITIONAL` | `test_levers_are_live` | `test_levers_are_live` |
| `DEFAULTS` | `montecarlo` | `test_blended_centres`, `test_chain`, `test_drawer`, `test_freeze`, `test_ipf_feasibility`, `test_judgement_sheet`, `test_levers_are_live`, `test_model_index`, `test_overhang`, `test_pool_conservation`, `test_regressions`, `test_scoreboard_disclosure`, `test_solve_and_predict`, `test_stage_inputs`, `test_stat_freshness` |
| `DELETED` | `test_register_matches_code` | `test_judgement_sheet`, `test_model_index`, `test_register_matches_code` |
| `ENTRY_POINTS` | `test_standalone_modules` | `test_model_index`, `test_standalone_modules` |
| `ENV_SWITCHES` | `freeze` | `test_freeze` |
| `EXPECTED_INERT` | `test_levers_are_live` | `test_levers_are_live` |
| `FITTED_ON` | `backtest` | `test_chain`, `test_levers_are_live`, `test_scoreboard_disclosure`, `test_stage_inputs` |
| `FITTED_ON_UNINSTRUMENTED` | `backtest` | `test_levers_are_live`, `test_scoreboard_disclosure`, `test_stage_inputs` |
| `FOLDS` | `fold` | `test_regressions` |
| `GATES` | `test_levers_are_live` | `test_levers_are_live` |
| `GATE_OPEN_AT` | `test_levers_are_live` | `test_levers_are_live` |
| `MODULE_CONSTANTS` | `montecarlo` | `test_delivery_proof` |
| `MODULE_PERTURB` | `test_levers_are_live` | `test_levers_are_live` |
| `NOT_FITTED` | `backtest` | `test_levers_are_live`, `test_stage_inputs` |
| `NOT_GENERATED_HERE` | `test_intermediates_are_current` | `test_intermediates_are_current` |
| `NOT_REGENERATED_HERE` | `test_intermediates_are_current` | `test_intermediates_are_current`, `test_model_index` |
| `PROVENANCE_UNSETTLED` | `backtest` | `test_levers_are_live`, `test_stage_inputs` |
| `STILL_IN_THE_TREE` | `test_register_matches_code` | `test_register_matches_code` |
| `TRANSIENT` | `test_intermediates_are_current` | `test_intermediates_are_current` |
| `UNRESOLVED_LIVE_CLAIMS` | `test_register_matches_code` | `test_register_matches_code` |
