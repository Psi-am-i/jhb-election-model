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
| `build_make` | `_allowance` | `city`, `ward` |
| `build_make` | `_extremes_by_bin` | `city`, `npe_city`, `npe_ward`, `ward` |
| `build_make` | `_sha` | `roll_sha256`, `turnout_sha256` |
| `build_make` | `dumps` | `geometry`, `model` |
| `build_play` | `group` | `code`, `median`, `name`, `p5`, `p95` |
| `build_validation` | `grab` | `brier`, `council`, `crps`, `seat_mae`, `wards`, `wards_called` |
| `build_your_forecast` | `one_level_down` | `<!-- __YFFOOT__ -->`, `<!-- __YFHEAD__ -->`, `<!-- __YFNAV__ -->` |
| `citywide_table` | `_code_sha` | `levels_sha`, `parties_sha` |
| `compare_history` | `_stats` | `ge_half`, `lt_half` |
| `compare_history` | `seat_abs_err` | `seat_abs_err`, `seat_abs_err_coherent` |
| `compare_history` | `vote_mae` | `pr_mae`, `pr_mae_median`, `ward_mae`, `ward_mae_median` |
| `diagnose` | `seat_abs_err` | `coherent_err`, `marginal_err` |
| `levels` | `sd_for` | `at_0.1%`, `at_1%`, `at_10%`, `at_40%` |
| `prediction` | `mean_votes` | `list_votes`, `ward_votes` |
| `publication` | `_sha` | `forecast_summary_sha256`, `seat_draws_sha256` |
| `render_home` | `_word` | `lede_coalition`, `lede_first`, `lede_overhang_party`, `lede_race`, `lede_second` |
| `render_home` | `chance` | `lede_p_alone`, `lede_p_first`, `lede_p_overhang`, `lede_p_second` |
| `render_home` | `tok` | `lede_overhang_seats`, `lede_overhang_votes` |
| `render_sheet` | `chance` | `anc_alone_share`, `anc_largest_share`, `anc_left_share`, `anc_side_share`, `da_alone_share`, `da_largest_share`, `grand_share`, `largest_tied_share`, `mk_largest_share`, `no_red_share`, `three_share` |
| `render_sheet` | `chance` | `anc_given_none`, `asa_pa_given_none`, `realistic_given_none` |
| `render_sheet` | `chance` | `da_small_share`, `soweto_none_share`, `soweto_some_share` |
| `render_sheet` | `seats` | `hi`, `lo`, `seats` |
| `render_sheet` | `tok` | `anc_alone_count`, `anc_best`, `anc_left_median`, `anc_median`, `da_alone_count`, `da_median`, `mk_median`, `mk_p95`, `no_red_median`, `three_median`, `three_median_when_wins`, `wall_count`, `wall_flips` |
| `render_sheet` | `tok` | `soweto_roll_share`, `soweto_wards_n` |
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
| `DATA` | `build_make`, `freeze`, `width_budget` | `REPO / 'data/raw/elections'`, `str 'forecast.json'` | NO |
| `DRAWS` | `build_make`, `build_play` | `REPO_ROOT / 'site' / 'draws'` | yes |
| `ELECTIONS` | `build_concordance`, `build_crosswalk`, `turnout` | `dict[11]`, `dict[6]`, `{year: (e.results, e.two_ballot) for year, e in sorted(cityconfig.CALEND` | NO |
| `INTERACTIVE` | `build_make`, `build_play`, `build_your_forecast` | `REPO_ROOT / 'interactive'` | yes |
| `MARK_END` | `hex_cartogram`, `render_map` | `str '<!-- __HEXMAP_END__ -->'`, `str '<!-- __MAP_END__ -->'` | NO |
| `MARK_START` | `hex_cartogram`, `render_map` | `str`, `str '<!-- __MAP_START__ -->'` | NO |
| `METRO_CODES` | `levels`, `pools` | `tuple[8]` | yes |
| `NAMES` | `render_map`, `render_sheet` | `dict[15]`, `dict[8]` | NO |
| `OG_DESCRIPTION` | `build_leaderboard`, `build_site`, `build_your_forecast` | `str` | yes |
| `OG_TITLE` | `build_leaderboard`, `build_site`, `build_your_forecast` | `str` | yes |
| `OUTPUT` | `judgement_sheet`, `model_index` | `ROOT / 'JUDGEMENT-SHEET.md'`, `ROOT / 'MODEL-INDEX.md'` | NO |
| `PROCESSED` | `declares`, `overhang_regimes` | `Path('data/processed')`, `REPO / 'data' / 'processed'` | NO |
| `REGISTER` | `judgement_sheet`, `polling` | `Path('polls.json')`, `ROOT / 'JUDGEMENT-CALLS.md'` | NO |
| `REPO` | `citywide_table`, `declares`, `freeze`, `width_budget` | `Path(__file__).resolve().parents[1]` | yes |
| `REPORTS` | `derive_city`, `official_seats` | `Path('data/raw/elections/_reports')` | yes |
| `REPO_ROOT` | `build_leaderboard`, `build_make`, `build_play`, `build_site`, `build_your_forecast`, `rank_entries`, `site_assets` | `Path(__file__).resolve().parents[1]` | yes |
| `ROOT` | `areas`, `backup_ignored`, `deploy_check`, `edit_mode`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_home`, `site_text` | `Path(__file__).resolve().parent.parent`, `Path(__file__).resolve().parents[1]`, `site_text.ROOT` | NO |
| `Row` | `declares`, `publication` | `?` | yes |
| `SCHEMA` | `citywide_table`, `publication` | `int 1` | yes |
| `SHARE_FLOOR` | `benchmarks`, `fold`, `montecarlo` | `float 0.002` | yes |
| `SRC` | `judgement_sheet`, `model_index` | `ROOT / 'src'` | yes |
| `USER_AGENT` | `fetch_boundaries`, `fetch_byelections`, `fetch_iec` | `str` | yes |
| `assemble` | `build_leaderboard`, `build_your_forecast` | `?` | yes |
| `audit` | `declares`, `stats` | `?` | yes |
| `build` | `citywide_table`, `export_draws`, `judgement_sheet`, `model_index` | `?` | yes |
| `check` | `areas`, `deploy_check` | `?` | yes |
| `citywide` | `fold`, `turnout` | `?` | yes |
| `classify` | `hex_cartogram`, `publication` | `?` | yes |
| `cluster_bootstrap` | `score`, `theta_residual` | `?` | yes |
| `expit` | `fold`, `montecarlo` | `?` | yes |
| `export` | `export_draws`, `site_text` | `?` | yes |
| `load` | `cityconfig`, `fold`, `polling`, `scenarios` | `?` | yes |
| `logit` | `fold`, `montecarlo` | `?` | yes |
| `normalise` | `parties`, `prep_logos` | `?` | yes |
| `parse` | `scenarios`, `sweep` | `?` | yes |
| `plan` | `build_all`, `site_text` | `?` | yes |
| `read_municipality` | `ingest_lge`, `ingest_npe` | `?` | yes |
| `render` | `build_portal`, `compare_history`, `hex_cartogram`, `judgement_sheet`, `stats` | `?` | yes |
| `report` | `coalitions`, `contested_area`, `declares`, `theta_residual` | `?` | yes |
| `resolve_path` | `cityconfig`, `edit_mode` | `?` | yes |
| `run` | `build_all`, `build_validation`, `diagnose`, `width_budget` | `?` | yes |
| `runnable` | `compare_history`, `sweep` | `?` | yes |
| `stale_reason` | `citywide_table`, `pools` | `?` | yes |
| `summarise` | `iec_csv`, `publication` | `?` | yes |
| `ward_number` | `iec_csv`, `score_forecasts` | `?` | yes |
| `ward_parts` | `build_concordance`, `montecarlo` | `?` | yes |
| `write` | `areas`, `site_assets`, `site_text` | `?` | yes |
| `write_assets` | `build_leaderboard`, `build_your_forecast` | `?` | yes |

### 1.3 One value, typed under two names

| value | names |
|---|---|
| 0.001 | `polling.POLL_DRIFT_PP_PER_ROOT_DAY`, `pools.NATIONAL_ONLY_FLOOR`, `pools.PRIOR_LOCAL_FLOOR` |
| 0.002 | `benchmarks.SHARE_FLOOR`, `fold.SHARE_FLOOR`, `levels.RELIABILITY_HALF`, `montecarlo.SHARE_FLOOR` |
| 0.005 | `gamma_recent.MIN_SHARE`, `levels.SIZE_WINDOW_TIE`, `pools.UNCLASSIFIED_FLOOR`, `render_map.OTHER_FLOOR` |
| 0.01 | `build_make.VANISH_MIN`, `pools.ALPHA_MIN_SHARE` |
| 0.015 | `polling.SIGMA_COMMON`, `polling.SIGMA_IDIO`, `pools.ROSTER_DROP_CEILING` |
| 0.02 | `build_make.COLLAPSE_FROM`, `montecarlo.TURNOUT_DRAW_FLOOR`, `polling.POLL_SCREEN_SD_UNDISCLOSED`, `scenarios.EXCESSIVE_FLOOR` |
| 0.05 | `build_make.SPLIT_MIN`, `pools.CENSUS_DRIFT_CEILING`, `render_map.TIP_FLOOR` |
| 0.25 | `build_make.COLLAPSE_KEEP`, `compare_history.REFERENCE_SLATE` |
| 0.5 | `areas.SOWETO_CUT`, `build_make.CORRELATION_MIN`, `build_make.RUNNER_UP_MAX`, `montecarlo.WARD_PR_RATIO_MIN`, `score.CLAIM_FRACTION` |
| 0.9 | `pools.MAX_POOL_CAPTURE`, `pools.SPLIT_SD_FLOOR`, `render_map.SAFE` |
| 12 | `montecarlo.DELIVERY_MAX_VALUES`, `pools.ALPHA_FALLBACK`, `stats.DECLARATION_MIN_CHARS` |
| 2.0 | `benchmarks.MAX_SIGMA`, `build_make.MIN_RECORD_EVENTS`, `hex_cartogram.GRID_MARGIN_CELLS`, `levels.SHRINK`, `montecarlo.OVERHANG_DEDUCT_MAX_ROUNDS_SLACK`, `montecarlo.WARD_PR_RATIO_MAX`, `pools.MIN_HOME_SPLITS`, `pools.REGISTRATION_MAX`, `reweight.ANALYSIS_SEAT_BAND`, `reweight.ANALYSIS_SHARE_BAND_POINTS` |
| 200 | `montecarlo.OVERHANG_LEVEL_MAX_ROUNDS`, `montecarlo.PARTIAL_BALANCE_PASSES`, `pools.ALPHA_CEILING`, `reweight.MIN_EFFECTIVE_DRAWS` |
| 30.0 | `montecarlo.BYE_MIN_WEIGHT`, `render_sheet.WALL_FLIPS` |
| 300 | `polling.POLL_MIN_N`, `stats.FRESHNESS_GRACE_S` |
| 6 | `build_play.BANNER_PARTIES`, `model_index.MIN_GLOB_FRAGMENT` |
| 7.0 | `montecarlo.LEVEL_DF`, `render_map.TOSS_STEP` |

### 1.4 Apportionment sites — the same job, written more than once

Matched on the SHAPE of largest-remainder apportionment (a whole part, an ordering, a shortfall handed out), not on the phrase, which appears in the docstrings of modules that only discuss it.

| function | orders the shortfall by | summary |
|---|---|---|
| `compare_history.coherent_seats` | `argsort(-(exact - base` | A point forecast that IS a council: largest remainder on the mean vector. |
| `pools.panel_turnout_spread` | `sorted((split_bloc or {}).items(` | How far EACH pool's turnout moves between local elections, panel-wide. |
| `rank_entries.rank_entries` | `sorted({r[''] for r in rows} - set(forecasts` | The leaderboard artefact for ``rows`` against ``result``. |
| `render_sheet.round_to_total` | `sorted(vals, key=lambda q: floors[q] - vals[q])[:max(rem, 0)]` | -- |
| `scenarios.main` | `sorted(detail[d].items(), key=lambda kv: -kv[1]['']` | -- |
| `seats.allocate` | `sorted(combined, key=lambda p: (-surpluses[p], -combined[p]` | Allocate council seats by the Schedule 1 quota-and-highest-surplus method. |
| `validate_seats.main` | `sorted(official[''].items(), key=lambda kv: -kv[1]['']` | -- |

### 1.5 Shadow pairs — a scenario key and a module constant of one name

`tied` means some `assert` in `src/` names both, so they cannot silently disagree. An untied shadow is one number in two places.

| lever | shadow constant | tied |
|---|---|---|
| `dirichlet_floor` | `montecarlo.DIRICHLET_FLOOR` | NO |
| `draws` | `build_make.DRAWS, build_play.DRAWS` | NO |
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
| `ARRIVAL_BAND_HI` | yes | -- |
| `ARRIVAL_BAND_LO` | yes | -- |
| `DA_LED_COALITION` | NO | -- |
| `F_OTHER` | yes | -- |
| `POLL_K` | yes | -- |
| `POLL_RMS_ERROR` | yes | -- |
| `THETA_CENTRAL` | yes | -- |
| `canonical_order` | yes | -- |
| `census_blend` | yes | -- |
| `census_blend_wanted` | yes | -- |
| `combined_shares` | yes | -- |
| `pa_contestation_uplift` | yes | -- |
| `poll_id` | NO | `build_play`, `polling` |
| `poll_k` | yes | -- |
| `poll_weight` | yes | -- |
| `polling_lean` | yes | -- |
| `polling_span` | NO | -- |
| `seed_bands` | yes | -- |
| `test_the_pr_ballot_assumption_is_measured_not_asserted` | yes | -- |
| `theta_mode` | yes | `build_interactive` |
| `total_log_median` | yes | -- |

### 2.2 Deleted from the model, still read somewhere in `src/`

| name | present | read in |
|---|---|---|
| `OTHER` | yes | `build_play`, `export_draws`, `export_interactive`, `render_map`, `render_sheet`, `reweight` |
| `f_other` | yes | `build_interactive` |
| `individual_theta` | yes | `build_interactive` |
| `turnout_tilt_da` | yes | `build_interactive` |

### 2.3 Entry points — modules exempted from the dead-code rule

An entry point that has acquired an importer no longer needs the exemption: the importer proves it alive on its own.

| module | exemption still load-bearing | importers |
|---|---|---|
| `arrivals` | yes | -- |
| `backup_ignored` | yes | -- |
| `build_crosswalk` | yes | -- |
| `build_geo` | yes | -- |
| `build_interactive` | yes | -- |
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

`archive.BY_FILENAME`, `archive.PROVENANCE`, `areas.SOWETO_CUT`, `areas.STREET_TYPES`, `backup_ignored.BACKUPS`, `backup_ignored.SKIP_PREFIXES`, `backup_ignored.SKIP_SUFFIXES`, `benchmarks.BLEND_W`, `benchmarks.MAX_SIGMA`, `benchmarks.MIN_SIGMA`, `benchmarks.NEW_PARTY_SIGMA`, `build_concordance.REG_DRIFT_TOLERANCE`, `build_geo.GDB_LAYERS`, `build_leaderboard.BODY`, `build_leaderboard.SCRIPT`, `build_make.CORRELATION_MIN`, `build_make.SHAPE_DIRECTION`, `build_make.SWING_BINS`, `build_play.GROUP_TONE_CLASSES`, `build_play.READER_NAMES`, `build_play.REFUSED_AS`, `build_portal.ELECTION`, `build_site.CF_WEB_ANALYTICS_TOKEN`, `build_site.COMMENTARY_MARKER`, `build_site.CONTENT_TYPES`, `build_site.IEC_RESULTS_URL`, `build_site.MDB_URL`, `build_site.MODEL_DOCS`, `build_site.NAV_FIRST_GROUP_ENDS`, `build_site.OWNER_PLACEHOLDER`, `build_site.SECURITY_HEADERS`, `build_site.SITE_NAME`, `build_site.STATSSA_URL`, `build_site.VALIDATION_SOURCE`, `build_validation.DISPLAY`, `build_your_forecast.CSS`, `build_your_forecast.JS`, `build_your_forecast.PYBOOT`, `build_your_forecast.SOURCE`, `citywide_table.HERE`, `compare_history.GAUTENG`, `compare_history.REFERENCE_SHARE`, `compare_history.REFERENCE_SLATE`, `contested_area.TRANSITIONS`, `declares.REPORT_ORDER`, `declares.UNDECLARED`, `edit_mode.LOOPBACK`, `edit_mode.OVERLAY_DIR`, `edit_mode.OVERLAY_FILES`, `edit_mode.WORD`, `export_draws.CENTRES_STAGE`, `export_draws.POLL_CAVEATS`, `export_interactive.PAGE_PARTIES`, `fetch_boundaries.FGDB_ITEMS`, `fetch_boundaries.LAYERS`, `fetch_boundaries.PAGE_SIZE`, `fetch_byelections.DASH`, `fetch_iec.LGE_REPORTS`, `fetch_iec.MUNI`, `fold.LEVEL_FLOOR`, `gamma_recent.MIN_SHARE`, `hex_cartogram.CELL_AREA_FACTOR`, `hex_cartogram.GRID_MARGIN_CELLS`, `hex_cartogram.PREVIEW`, `iec_csv.BOMS`, `iec_csv.ENCODINGS`, `ingest_historic.LGE_COLUMNS`, `ingest_historic.METRO_BALLOTS`, `ingest_historic.NPE_COLUMNS`, `ingest_historic.OUT_DIR`, `ingest_historic.SOURCE_DIR`, `inputs_preflight.ADVISORY`, `judgement_sheet.LIVE_TARGET_KEY`, `judgement_sheet.REGISTER_URL`, `judgement_sheet.SECTION_END`, `judgement_sheet.SECTION_HEADING`, `judgement_sheet.SECTION_START`, `model_index.JUDGEMENT_REGISTER`, `model_index.MEASUREMENT_ROOT`, `model_index.MODEL_ROOT`, `model_index.SPAN_MARKERS`, `montecarlo.DIRICHLET_FLOOR`, `montecarlo.OVERHANG_DEDUCT_MAX_ROUNDS_SLACK`, `montecarlo.OVERHANG_LEVEL_MAX_ROUNDS`, `montecarlo.PARTIAL_BALANCE_PASSES`, `montecarlo.POOL_CAPACITY_MARGIN`, `montecarlo.SCENARIO_METADATA`, `montecarlo.TURNOUT_CORRELATION`, `montecarlo.TURNOUT_DRAW_FLOOR`, `montecarlo.WARD_PR_RATIO_MIN`, `official_seats.LABELS`, `polling.POLL_SCREEN_SD_UNDISCLOSED`, `polling.SCOPES`, `pools.ALPHA_CEILING`, `pools.ALPHA_FALLBACK`, `pools.ALPHA_FLOOR`, `pools.ALPHA_MIN_SHARE`, `pools.CENSUS_COVERAGE_FLOOR`, `pools.KNOWN_PARTY_CODES`, `pools.LOCK_PATH`, `pools.MAX_POOL_CAPTURE`, `pools.NPE_CITYWIDE_STATES`, `pools.ROSTER_KEYS`, `pools.SPLINTER_PARENT_WEIGHT`, `pools.SPLIT_SD_FLOOR`, `prep_logos.CODES`, `publication.MOVEMENTS`, `publication.PRELEDGER_PREFIX`, `render_home.HEAD_TO_HEAD_ORDER`, `render_home.LABEL`, `render_home.LEDE_PLACEHOLDERS`, `render_home.NAMED`, `render_map.KEY_PARTIES`, `render_map.KEY_SOLID`, `render_map.KEY_STRIPE_A`, `render_map.KEY_STRIPE_B`, `render_map.REST`, `render_map.UNKNOWN_CHIP`, `render_sheet.ALLIANCE_8`, `render_sheet.CHART_PARTIES`, `render_sheet.COALITION_KEY_ORDER`, `render_sheet.DA_CORE_PARTNERS`, `render_sheet.REALISTIC_PARTNERS`, `render_sheet.WALL_FLIPS`, `render_sheet.ZILLE_RED_LINES`, `reweight.PUBLISHED_LAW`, `scenarios.BAND`, `scenarios.COND`, `scenarios.OPS`, `score_forecasts.ROLL_COLUMNS`, `site_assets.FONT_DIR`, `site_assets.FONT_RANGE`, `site_assets.INLINE`, `site_assets.JS_SRC`, `site_text.ARTICLE_FIELDS`, `site_text.BLOCK_ID`, `site_text.CLAIM_FIELDS`, `site_text.GENERATED_MD`, `site_text.LEDE_FIELDS`, `site_text.MD_DIR`, `site_text.OPAQUE`, `site_text.VOID`, `stats.ATTRS`, `stats.CHROME_CLASSES`, `stats.COUNCIL_CONSTANT_SOURCES`, `stats.FRESHNESS_REMEDY`, `stats.HISTORICAL`, `stats.LIVE_ATTR`, `stats.SCRIPTS`, `stats.SCRIPT_FORBIDDEN`, `stats.TOKEN`, `stats.WRITER_FORBIDDEN`, `sweep.PARTY_ROW`, `turnout.LAMBDA_PAIRS`

## 3 · Declared producers against the code

The intermediates register names the script that writes each artefact. `agrees` is false when the module it names does not so much as mention the artefact.

| artefact | register claims | modules naming it | agrees |
|---|---|---|---|
| `citywide_*.json` | `citywide_table` | `archive`, `citywide_table`, `declares`, `export_interactive`, `fold`, `levels`, `pools`, `theta_residual` | yes |
| `forecast_frozen.json` | `freeze` | `compare_history`, `declares`, `freeze`, `montecarlo` | yes |
| `forecast_summary.json` | `montecarlo` | `build_interactive`, `build_portal`, `build_site`, `coalitions`, `declares`, `freeze`, `levels`, `montecarlo`, `overhang_regimes`, `publication`, `render_home`, `render_sheet`, `scenarios`, `stats` | yes |
| `history.json` | `compare_history` | `compare_history`, `declares`, `freeze`, `score` | yes |
| `history.md` | `compare_history` | `compare_history` | yes |
| `interactive_data.json` | `build_site` | `build_interactive`, `declares`, `export_interactive` | NO |
| `pools_*.json` | `pools` | `archive`, `arrivals`, `build_play`, `cityconfig`, `compare_history`, `declares`, `export_interactive`, `fold`, `freeze`, `montecarlo`, `pools`, `stats`, `sweep` | yes |
| `regime_*_summary.json` | `overhang_regimes` | `archive`, `build_interactive`, `build_portal`, `build_site`, `coalitions`, `declares`, `freeze`, `levels`, `montecarlo`, `overhang_regimes`, `publication`, `render_home`, `render_sheet`, `scenarios`, `stats` | yes |
| `sweep.json` | `sweep` | `declares`, `sweep` | yes |
| `validation_*.json` | `montecarlo` | `archive`, `backup_ignored`, `build_site`, `build_validation`, `compare_history`, `declares`, `score`, `stats` | NO |
| `ward_hex_layout.json` | `hex_cartogram` | `build_make`, `hex_cartogram` | yes |
| `ward_paths.json` | `render_map` | `build_all`, `build_make`, `build_play`, `build_your_forecast`, `export_interactive`, `hex_cartogram`, `render_map` | yes |
| `width_budget.json` | `montecarlo` | `declares`, `width_budget` | NO |

## 4 · Levers

Every key of `montecarlo.DEFAULTS`, against every register that classifies it. `provenance` is the backtest's leak class; `inert at` and `conditional at` are the targets where the lever has been certified dead or measured live; `registered` is whether `JUDGEMENT-CALLS.md` names it.

| lever | default | provenance | inert at | conditional at | registered | read in |
|---|---|---|---|---|---|---|
| `arrival_group_draw` | `False` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `bye_local_cap` | `1.5` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `bye_tau_months` | `18.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `bye_weight_mode` | `'fixed'` | `NOT_FITTED` | `2021` | -- | yes | `backtest`, `montecarlo` |
| `contestation_expand` | `0.22` | `FITTED_ON_UNINSTRUMENTED` | `2021`, `2026` | -- | yes | `backtest`, `montecarlo` |
| `dirichlet_floor` | `0.0001` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `dirichlet_scale` | `1.0` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `draws` | `5000` | `NOT_FITTED` | -- | -- | NO | `arrivals`, `backtest`, `benchmarks`, `build_make`, `build_play`, `build_site`, `build_validation`, `citywide_table`, `coalitions`, `compare_history`, `declares`, `diagnose`, `export_draws`, `freeze`, `montecarlo`, `publication`, `render_home`, `reweight`, `score`, `stats`, `sweep`, `theta_residual`, `width_budget` |
| `entrant_geography` | `dict[0]` | `FITTED_ON` | `2021`, `2026` | -- | NO | `backtest`, `montecarlo` |
| `entrant_prob` | `0.25` | `FITTED_ON_UNINSTRUMENTED` | `2021`, `2026` | -- | yes | `backtest`, `build_interactive`, `compare_history`, `montecarlo` |
| `entrant_share` | `list[3]` | `FITTED_ON_UNINSTRUMENTED` | `2021`, `2026` | -- | yes | `backtest`, `build_interactive`, `compare_history`, `montecarlo` |
| `level_floor` | `1e-06` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `level_sd_default` | `0.45` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `level_shrink` | `0.35` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `level_shrink_scale` | `0.04` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `overhang_rule` | `'deduct'` | `NOT_FITTED` | -- | -- | yes | `backtest`, `benchmarks`, `montecarlo`, `prediction` |
| `poll_credence` | `1.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_deff_subsample` | `1.6` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_drift_per_root_day` | `0.001` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_half_life_days` | `120.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_house_k` | `1.0` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `poll_min_n` | `300` | `NOT_FITTED` | `2021`, `2026` | `2021`, `2026` | yes | `backtest`, `montecarlo`, `reweight` |
| `poll_paths` | `'off'` | `NOT_FITTED` | -- | -- | yes | `backtest`, `export_draws`, `montecarlo` |
| `poll_screen_sd` | `0.02` | `NOT_FITTED` | `2021`, `2026` | `2026` | yes | `backtest`, `montecarlo` |
| `pools` | `dict[0]` | `FITTED_ON` | -- | -- | yes | `backtest`, `build_play`, `citywide_table`, `declares`, `export_interactive`, `model_index`, `montecarlo`, `pools`, `score_forecasts`, `theta_residual` |
| `seed` | `20261104` | `NOT_FITTED` | -- | -- | NO | `backtest`, `benchmarks`, `build_make`, `build_validation`, `citywide_table`, `compare_history`, `declares`, `export_draws`, `freeze`, `montecarlo`, `scenarios`, `score`, `seats`, `width_budget` |
| `spine_k` | `None` | `PROVENANCE_UNSETTLED` | -- | -- | yes | `backtest`, `montecarlo` |
| `turnout_blend_jitter` | `0.25` | `NOT_FITTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `turnout_correlation` | `0.63` | `FITTED_ON_UNINSTRUMENTED` | -- | -- | yes | `backtest`, `montecarlo` |
| `turnout_noise_sd` | `0.08` | `NOT_FITTED` | -- | -- | yes | `backtest`, `build_interactive`, `montecarlo` |
| `turnout_pattern_blend` | `0.5` | `NOT_FITTED` | -- | -- | yes | `backtest`, `build_interactive`, `montecarlo` |
| `w_bye` | `0.4` | `NOT_FITTED` | `2021` | -- | yes | `backtest`, `build_interactive`, `build_play`, `export_draws`, `montecarlo` |
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
| `areas.ROOT` | Path(__file__).resolve().parent.parent | NO | NO | NO | `backup_ignored`, `deploy_check`, `edit_mode`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_home`, `render_sheet`, `site_text` |
| `areas.SOWETO_GAZETTEER` | tuple[44] | NO | NO | yes | -- |
| `areas.SOWETO_EXCLUDE` | tuple[2] | NO | NO | yes | -- |
| `areas.STREET_TYPES` | tuple[14] | NO | NO | yes | -- |
| `areas.SOWETO_CUT` | float 0.5 | NO | NO | yes | -- |
| `areas.AREAS` | {('joburg', 'soweto'): {'label': 'Soweto', 'stations': 'data/raw/geo/vot | NO | NO | NO | `render_sheet` |
| `arrivals.CITIES` | list[8] | NO | NO | NO | `build_validation`, `compare_history`, `judgement_sheet`, `sweep` |
| `backtest.TARGETS` | _Targets() | NO | NO | NO | `benchmarks` |
| `backtest.FITTED_ON` | dict[9] | NO | NO | NO | `model_index` |
| `backtest.FITTED_ON_UNINSTRUMENTED` | dict[7] | NO | NO | NO | `model_index` |
| `backtest.PROVENANCE_UNSETTLED` | dict[1] | NO | NO | NO | `model_index` |
| `backtest.NOT_FITTED` | dict[25] | NO | NO | NO | `model_index` |
| `backup_ignored.ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `areas`, `deploy_check`, `edit_mode`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_home`, `render_sheet`, `site_text` |
| `backup_ignored.BACKUPS` | ROOT / 'backups' | NO | NO | NO | -- |
| `backup_ignored.SKIP_PREFIXES` | tuple[5] | NO | NO | NO | -- |
| `backup_ignored.SKIP_SUFFIXES` | tuple[2] | NO | NO | NO | -- |
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
| `build_leaderboard.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_make`, `build_play`, `build_site`, `build_your_forecast`, `rank_entries`, `site_assets` |
| `build_leaderboard.LB_DIR` | str 'leaderboard' | NO | NO | NO | `build_site` |
| `build_leaderboard.LB_PAGE` | f'{LB_DIR}/index.html' | NO | NO | NO | `build_site` |
| `build_leaderboard.LB_HREF` | f'{LB_DIR}/' | NO | NO | NO | `build_site` |
| `build_leaderboard.SCRIPT` | REPO_ROOT / 'interactive' / 'js' / 'leaderboard.js' | NO | NO | NO | -- |
| `build_leaderboard.OG_TITLE` | str | NO | NO | NO | `build_site`, `build_your_forecast` |
| `build_leaderboard.OG_DESCRIPTION` | str | NO | NO | NO | `build_site`, `build_your_forecast` |
| `build_leaderboard.BODY` | str | NO | NO | NO | -- |
| `build_make.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_leaderboard`, `build_play`, `build_site`, `build_your_forecast`, `rank_entries`, `site_assets` |
| `build_make.INTERACTIVE` | REPO_ROOT / 'interactive' | NO | NO | NO | `build_play`, `build_your_forecast` |
| `build_make.DRAWS` | REPO_ROOT / 'site' / 'draws' | NO | NO | NO | `build_play` |
| `build_make.WORKER_SRC` | REPO_ROOT / 'worker-api' / 'src' | NO | NO | NO | `build_your_forecast` |
| `build_make.WORKER_API_JS` | tuple[3] | NO | NO | NO | `build_your_forecast` |
| `build_make.SEATS_LINE` | tuple[2] | NO | NO | NO | `build_your_forecast` |
| `build_make.DATA` | str 'forecast.json' | NO | NO | NO | `build_your_forecast`, `freeze`, `width_budget` |
| `build_make.EDITOR_WIDEN_PP` | float 5.0 | NO | NO | yes | -- |
| `build_make.RUNNER_UP_MAX` | float 0.5 | NO | NO | yes | -- |
| `build_make.SWING_BINS` | tuple[5] | NO | NO | yes | -- |
| `build_make.MIN_RECORD_EVENTS` | int 2 | NO | NO | yes | -- |
| `build_make.VANISH_MIN` | float 0.01 | NO | NO | yes | -- |
| `build_make.SPLIT_MIN` | float 0.05 | NO | NO | yes | -- |
| `build_make.COLLAPSE_FROM` | float 0.02 | NO | NO | yes | -- |
| `build_make.COLLAPSE_KEEP` | float 0.25 | NO | NO | yes | -- |
| `build_make.CORRELATION_MIN` | float 0.5 | NO | NO | yes | -- |
| `build_make.APPROXIMATE` | str '_approx_' | NO | NO | yes | -- |
| `build_make.SHAPE_DIRECTION` | dict[4] | NO | NO | NO | -- |
| `build_play.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_leaderboard`, `build_make`, `build_site`, `build_your_forecast`, `rank_entries`, `site_assets` |
| `build_play.INTERACTIVE` | REPO_ROOT / 'interactive' | NO | NO | NO | `build_make`, `build_your_forecast` |
| `build_play.SHEET` | REPO_ROOT / 'forecast-sheet.html' | NO | NO | NO | -- |
| `build_play.DRAWS` | REPO_ROOT / 'site' / 'draws' | NO | NO | NO | `build_make` |
| `build_play.DRAWS_LINE` | tuple[2] | NO | NO | NO | `build_your_forecast` |
| `build_play.FILL` | tuple[14] | NO | NO | NO | -- |
| `build_play.BANNER_PARTIES` | int 6 | NO | NO | NO | -- |
| `build_play.SEGMENT_LABEL_MIN` | float 0.12 | NO | NO | NO | -- |
| `build_play.GROUP_TONE_CLASSES` | tuple[4] | NO | NO | NO | -- |
| `build_play.REFUSED_AS` | dict[5] | NO | NO | NO | -- |
| `build_play.READER_NAMES` | dict[16] | NO | NO | NO | -- |
| `build_portal.ELECTION` | str '4 November 2026' | NO | NO | NO | -- |
| `build_portal.DEFAULT_ACCENT` | str '#a8621f' | NO | NO | NO | `site_assets` |
| `build_site.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_leaderboard`, `build_make`, `build_play`, `build_your_forecast`, `rank_entries`, `site_assets` |
| `build_site.REPO_URL` | str | NO | NO | NO | -- |
| `build_site.NAV_ITEMS` | [('forecast', 'our forecast'), (build_your_forecast.YF_HREF, 'your forec | NO | NO | NO | -- |
| `build_site.SITE_NAME` | str 'joburg.whysoserious.city' | NO | NO | NO | -- |
| `build_site.LOGO_NAME` | f'Johannesburg election forecast — {SITE_NAME}' | NO | NO | NO | -- |
| `build_site.STRAPLINE` | str | NO | NO | NO | -- |
| `build_site.NAV_FIRST_GROUP_ENDS` | str 'claims' | NO | NO | NO | -- |
| `build_site.CF_WEB_ANALYTICS_TOKEN` | str | NO | NO | NO | -- |
| `build_site.SITE_HEAD` | site_assets.head() + analytics_head() | NO | NO | NO | `build_portal` |
| `build_site.OG_TITLE` | str | NO | NO | NO | `build_leaderboard`, `build_your_forecast` |
| `build_site.OG_DESCRIPTION` | str | NO | NO | NO | `build_leaderboard`, `build_your_forecast` |
| `build_site.OG_META` | f'<meta property="og:site_name" content="Johannesburg 2026 Election Mode | NO | NO | NO | -- |
| `build_site.SITE_URL` | str | NO | NO | NO | -- |
| `build_site.IEC_RESULTS_URL` | str | NO | NO | NO | -- |
| `build_site.STATSSA_URL` | str | NO | NO | NO | -- |
| `build_site.MDB_URL` | str | NO | NO | NO | -- |
| `build_site.FOOTER` | footer_for() | NO | NO | NO | `build_portal` |
| `build_site.MODEL_DOCS` | dict[4] | NO | NO | NO | -- |
| `build_site.POLICY_DOCS` | dict[2] | NO | NO | NO | -- |
| `build_site.DOCS` | {**MODEL_DOCS, **POLICY_DOCS} | NO | NO | NO | `edit_mode` |
| `build_site.PRIVACY_SOURCE` | REPO_ROOT / 'docs-public' / 'privacy.md' | NO | NO | NO | -- |
| `build_site.OWNER_PLACEHOLDER` | re.compile('^OWNER:', re.M) | NO | NO | NO | -- |
| `build_site.ARTEFACTS` | {'index.html': ('home.html', None, None, None, None), 'forecast.html': ( | NO | NO | NO | `edit_mode`, `site_text` |
| `build_site.COMMENTARY_MARKER` | str '<!-- __COMMENTARY__ -->' | NO | NO | NO | -- |
| `build_site.MD_EXTENSIONS` | tuple[4] | NO | NO | NO | `edit_mode`, `site_text` |
| `build_site.VALIDATION_SOURCE` | REPO_ROOT / 'docs-public' / 'about-the-model.md' | NO | NO | NO | -- |
| `build_site.VALIDATION_MARKER` | str '<!-- __VALIDATION__ -->' | NO | NO | NO | -- |
| `build_site.CONTENT_TYPES` | dict[12] | NO | NO | NO | -- |
| `build_site.SECURITY_HEADERS` | dict[4] | NO | NO | NO | -- |
| `build_validation.CITIES` | list[8] | NO | NO | NO | `arrivals`, `compare_history`, `judgement_sheet`, `sweep` |
| `build_validation.DISPLAY` | dict[26] | NO | NO | NO | -- |
| `build_validation.BASELINES` | dict[3] | NO | NO | NO | `diagnose` |
| `build_your_forecast.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_leaderboard`, `build_make`, `build_play`, `build_site`, `rank_entries`, `site_assets` |
| `build_your_forecast.INTERACTIVE` | REPO_ROOT / 'interactive' | NO | NO | NO | `build_make`, `build_play` |
| `build_your_forecast.SOURCE` | INTERACTIVE / 'your-forecast.html' | NO | NO | NO | -- |
| `build_your_forecast.YF_DIR` | str 'your-forecast' | NO | NO | NO | `build_site` |
| `build_your_forecast.YF_PAGE` | f'{YF_DIR}/index.html' | NO | NO | NO | `build_site` |
| `build_your_forecast.YF_HREF` | f'{YF_DIR}/' | NO | NO | NO | `build_site` |
| `build_your_forecast.RETIRED` | tuple[2] | NO | NO | NO | -- |
| `build_your_forecast.OG_TITLE` | str | NO | NO | NO | `build_leaderboard`, `build_site` |
| `build_your_forecast.OG_DESCRIPTION` | str | NO | NO | NO | `build_leaderboard`, `build_site` |
| `build_your_forecast.JS` | tuple[23] | NO | NO | NO | -- |
| `build_your_forecast.CSS` | tuple[3] | NO | NO | NO | -- |
| `build_your_forecast.PYBOOT` | tuple[2] | NO | NO | NO | -- |
| `build_your_forecast.BLOCKLIST_LINE` | tuple[2] | NO | NO | NO | -- |
| `cityconfig.CITIES_DIR` | Path('cities') | NO | NO | NO | `pools` |
| `cityconfig.DEFAULT_CITY` | str 'joburg' | NO | NO | NO | `areas` |
| `cityconfig.CALENDAR` | {'1999': Election('1999', 'NPE', _date(1999, 6, 2), 'npe1999_approx_{COD | NO | NO | NO | `backtest`, `benchmarks`, `build_make`, `build_play`, `byelections`, `levels`, `montecarlo`, `pools`, `theta_residual`, `turnout` |
| `citywide_table.HERE` | Path(__file__).resolve().parent | NO | NO | NO | -- |
| `citywide_table.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `declares`, `freeze`, `width_budget` |
| `citywide_table.GATES` | tuple[5] | NO | NO | NO | `model_index` |
| `citywide_table.SCHEMA` | int 1 | NO | NO | NO | `publication` |
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
| `declares.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `citywide_table`, `freeze`, `width_budget` |
| `declares.PROCESSED` | REPO / 'data' / 'processed' | NO | NO | NO | `overhang_regimes` |
| `declares.DECLARED` | tuple[3] | NO | NO | NO | -- |
| `declares.LYING` | tuple[3] | NO | NO | NO | -- |
| `declares.UNDECLARED` | tuple[3] | NO | NO | NO | -- |
| `declares.KINDS` | {'spec': Kind('spec', ('code', 'config', 'scope', 'inputs'), '§1.173 — a | NO | NO | NO | -- |
| `declares.REPORT_ORDER` | tuple[5] | NO | NO | NO | -- |
| `deploy_check.ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `areas`, `backup_ignored`, `edit_mode`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_home`, `render_sheet`, `site_text` |
| `deploy_check.SHIPPED_UNCOMMITTED` | set[1] | NO | NO | NO | -- |
| `derive_city.REPORTS` | Path('data/raw/elections/_reports') | NO | NO | NO | `build_make`, `official_seats` |
| `derive_city.LGE_YEARS` | tuple[3] | NO | NO | NO | -- |
| `diagnose.BASELINES` | scored_opponents() | NO | NO | NO | `build_validation` |
| `diagnose.VERDICT_STATISTIC` | str 'seat_abs_err_coherent' | NO | NO | NO | -- |
| `edit_mode.ROOT` | site_text.ROOT | NO | NO | NO | `areas`, `backup_ignored`, `deploy_check`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_home`, `render_sheet`, `site_text` |
| `edit_mode.SITE` | ROOT / 'site' | NO | NO | NO | -- |
| `edit_mode.PORT` | int 8801 | NO | NO | NO | -- |
| `edit_mode.LOOPBACK` | str '127.0.0.1' | NO | NO | NO | -- |
| `edit_mode.OVERLAY_DIR` | ROOT / 'src' / 'edit' | NO | NO | NO | -- |
| `edit_mode.OVERLAY_FILES` | tuple[2] | NO | NO | NO | -- |
| `edit_mode.URL_PREFIX` | str '/__edit/' | NO | NO | NO | -- |
| `edit_mode.BLOCK_ATTR` | str 'data-edit-block' | NO | NO | NO | -- |
| `edit_mode.WORD` | re.compile('<span[^>]*data-word="[^"]*"[^>]*>.*?</span>', re.S) | NO | NO | NO | -- |
| `export_draws.CENTRES_STAGE` | tuple[2] | NO | NO | NO | -- |
| `export_draws.VOTE_BLOCKS` | dict[4] | NO | NO | NO | -- |
| `export_draws.LAWS` | tuple[4] | NO | NO | NO | -- |
| `export_draws.PRIVATE_KEYS` | tuple[1] | NO | NO | NO | -- |
| `export_draws.POLL_CAVEATS` | Path(__file__).resolve().parents[1] / 'content' / '{city}' / 'poll-cavea | NO | NO | NO | -- |
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
| `freeze.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `citywide_table`, `declares`, `width_budget` |
| `freeze.DATA` | REPO / 'data/raw/elections' | NO | NO | NO | `build_make`, `build_your_forecast`, `width_budget` |
| `freeze.FROZEN` | REPO / 'data/processed/forecast_frozen.json' | NO | NO | NO | -- |
| `freeze.ENV_SWITCHES` | tuple[9] | NO | NO | NO | `model_index` |
| `freeze.ENV_NOT_RECORDED` | dict[2] | NO | NO | NO | -- |
| `gamma_recent.MIN_SHARE` | float 0.005 | NO | NO | yes | -- |
| `hex_cartogram.MARK_START` | str | NO | NO | NO | `build_play`, `render_map` |
| `hex_cartogram.MARK_END` | str '<!-- __HEXMAP_END__ -->' | NO | NO | NO | `build_play`, `render_map` |
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
| `inputs_preflight.ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `areas`, `backup_ignored`, `deploy_check`, `edit_mode`, `export_draws`, `judgement_sheet`, `model_index`, `render_home`, `render_sheet`, `site_text` |
| `inputs_preflight.SNAPSHOT_STALE_DAYS` | int 21 | NO | NO | NO | -- |
| `inputs_preflight.REQUIRED` | tuple[2] | NO | NO | NO | -- |
| `inputs_preflight.ADVISORY` | tuple[2] | NO | NO | NO | -- |
| `judgement_sheet.ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `areas`, `backup_ignored`, `deploy_check`, `edit_mode`, `export_draws`, `inputs_preflight`, `model_index`, `render_home`, `render_sheet`, `site_text` |
| `judgement_sheet.SRC` | ROOT / 'src' | NO | NO | NO | `model_index`, `render_sheet` |
| `judgement_sheet.CITIES` | ROOT / 'cities' | NO | NO | NO | `arrivals`, `build_validation`, `compare_history`, `sweep` |
| `judgement_sheet.REGISTER` | ROOT / 'JUDGEMENT-CALLS.md' | NO | NO | NO | `montecarlo`, `polling` |
| `judgement_sheet.OUTPUT` | ROOT / 'JUDGEMENT-SHEET.md' | NO | NO | NO | `model_index` |
| `judgement_sheet.LIVE_TARGET_KEY` | str 'by_year' | NO | NO | NO | -- |
| `judgement_sheet.METHODOLOGY` | ROOT / 'docs-public' / 'methodology.md' | NO | NO | NO | -- |
| `judgement_sheet.SECTION_START` | str | NO | NO | NO | -- |
| `judgement_sheet.SECTION_END` | str | NO | NO | NO | -- |
| `judgement_sheet.SECTION_HEADING` | str 'The judgement calls' | NO | NO | NO | -- |
| `judgement_sheet.REGISTER_URL` | str | NO | NO | NO | -- |
| `levels.SD_FLOOR` | tuple[2] | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.SD_CEILING` | tuple[2] | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.LOG_CHI2_BIAS` | float 1.8873652674492816 | NO | NO | yes | `theta_residual` |
| `levels.SHRINK` | float 2.0 | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.RELIABILITY_HALF` | float 0.002 | yes | NO | yes | `montecarlo`, `theta_residual` |
| `levels.SPINE_K` | float 1.0 | yes | NO | yes | `montecarlo` |
| `levels.SIZE_WINDOW_GRID` | (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, float('inf')) | yes | NO | yes | `montecarlo` |
| `levels.SIZE_WINDOW_MIN_SCORED` | int 20 | yes | NO | yes | `montecarlo` |
| `levels.SIZE_WINDOW_TIE` | float 0.005 | yes | NO | yes | `montecarlo` |
| `levels.METRO_CODES` | tuple[8] | yes | NO | yes | `contested_area`, `montecarlo`, `polling`, `pools`, `theta_residual` |
| `levels.HELD_BACK` | {} if _HELD_BACK_OFF else {(tag, code): 'pre-2011 history, ingested and  | NO | NO | yes | `pools` |
| `levels.KNOWN_ABSENT` | dict[0] | yes | NO | NO | `montecarlo` |
| `levels.THETA_EXCLUDE_TARGETS` | frozenset((y for y in _os.environ.get('THETA_EXCLUDE_TARGETS', '').split | yes | NO | NO | `citywide_table`, `freeze`, `montecarlo`, `theta_residual` |
| `levels.TYPE_A_EVENTS` | dict[3] | yes | NO | NO | `montecarlo`, `theta_residual` |
| `levels.FILTER_TYPE_A` | _os.environ.get('FILTER_TYPE_A', '').lower() in ('1', 'true', 'yes') | yes | NO | NO | `citywide_table`, `freeze`, `montecarlo`, `theta_residual` |
| `levels.DEMARCATION_CROSSING` | frozenset({('MAN', '2011'), ('BUF', '2011')}) | yes | NO | NO | `montecarlo`, `theta_residual` |
| `levels.EXCLUDE_DEMARCATION_CROSSING` | _os.environ.get('EXCLUDE_DEMARCATION_CROSSING', '').lower() in ('1', 'tr | yes | NO | NO | `citywide_table`, `freeze`, `montecarlo`, `theta_residual` |
| `levels.THETA_WINDOW` | int(_os.environ.get('THETA_WINDOW', '0') or 0) | yes | NO | yes | `citywide_table`, `freeze`, `montecarlo`, `theta_residual` |
| `model_index.ROOT` | Path(__file__).resolve().parent.parent | NO | NO | NO | `areas`, `backup_ignored`, `deploy_check`, `edit_mode`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `render_home`, `render_sheet`, `site_text` |
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
| `montecarlo.COUNCIL` | int 270 | yes | NO | yes | `benchmarks`, `prediction` |
| `montecarlo.DIRICHLET_FLOOR` | float 0.0001 | yes | NO | yes | -- |
| `montecarlo.PLAN_BOUNDS` | dict[0] | yes | NO | yes | `export_interactive` |
| `montecarlo.DEFAULTS` | {'draws': 5000, 'seed': 20261104, 'w_bye': 0.4, 'bye_weight_mode': 'fixe | NO | NO | yes | `backtest`, `benchmarks`, `build_validation`, `compare_history`, `export_draws`, `export_interactive`, `freeze`, `judgement_sheet`, `model_index`, `reweight`, `stats` |
| `montecarlo.BYE_MIN_WEIGHT` | float 30.0 | yes | yes | yes | `export_draws` |
| `montecarlo.TURNOUT_DRAW_FLOOR` | float 0.02 | yes | NO | yes | -- |
| `montecarlo.TURNOUT_DRAW_CEILING` | float 0.95 | yes | yes | yes | -- |
| `montecarlo.WARD_PR_RATIO_MIN` | float 0.5 | yes | NO | yes | -- |
| `montecarlo.WARD_PR_RATIO_MAX` | float 2.0 | yes | NO | yes | -- |
| `montecarlo.LEVEL_DF` | float 7.0 | yes | yes | yes | `theta_residual` |
| `montecarlo.POOL_CAPACITY_MARGIN` | float 0.98 | yes | NO | yes | -- |
| `montecarlo.PARTIAL_BALANCE_PASSES` | int 200 | yes | NO | yes | -- |
| `montecarlo.TURNOUT_CORRELATION` | float 0.63 | yes | NO | yes | -- |
| `montecarlo.GAMMA_FOLD` | dict[4] | yes | NO | yes | `compare_history` |
| `montecarlo.STATUTORY_VALUES` | dict[1] | NO | NO | NO | `prediction` |
| `montecarlo.SCENARIO_METADATA` | tuple[1] | NO | NO | NO | -- |
| `montecarlo.HASH_SEED` | str '0' | yes | NO | NO | `export_draws`, `freeze` |
| `montecarlo.DELIVERY_MAX_VALUES` | int 12 | NO | NO | NO | -- |
| `montecarlo.DELIVERY_MAX_CHARS` | int 2000 | NO | NO | NO | -- |
| `montecarlo.MODULE_CONSTANTS` | dict[5] | NO | NO | yes | `model_index` |
| `montecarlo.FROZEN_DEFAULTS` | frozenset({('levels', 'METRO_CODES'), ('polling', 'REGISTER')}) | NO | NO | NO | -- |
| `montecarlo.OVERHANG_RULES` | tuple[4] | NO | NO | NO | -- |
| `montecarlo.OVERHANG_DEDUCT_MAX_ROUNDS_SLACK` | int 2 | NO | NO | yes | -- |
| `montecarlo.OVERHANG_LEVEL_MAX_ROUNDS` | int 200 | NO | NO | yes | -- |
| `official_seats.REPORTS` | Path('data/raw/elections/_reports') | NO | NO | NO | `build_make`, `derive_city` |
| `official_seats.LABELS` | dict[5] | NO | NO | NO | -- |
| `overhang_regimes.PROCESSED` | Path('data/processed') | NO | NO | NO | `declares` |
| `overhang_regimes.RULES` | tuple[3] | NO | NO | NO | -- |
| `parties.PARTIES` | dict[9] | NO | NO | NO | `build_crosswalk`, `build_play`, `pools` |
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
| `pools.MERGER_RETENTION` | float 0.75 | NO | NO | yes | `backtest`, `montecarlo`, `theta_residual` |
| `pools.MERGER_RETENTION_RANGE` | tuple[2] | NO | NO | yes | -- |
| `pools.MERGERS` | (Merger(frozenset({'GOOD', 'RISE'}), _date(2026, 5, 25), 'GOOD and RISE  | NO | NO | NO | `theta_residual` |
| `pools.MERGER_CONSUMERS` | frozenset({'montecarlo.run_model', 'pools.emit_pools', 'theta_residual._ | NO | NO | NO | -- |
| `pools.ARRIVAL_DEFINITIONS` | {'ARRIVED_VS_NATIONAL': ArrivalDefinition(predicate='local share > 0 and | NO | NO | NO | `model_index` |
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
| `prep_logos.MISSING` | list[4] | NO | NO | NO | `inputs_preflight` |
| `publication.SCHEMA` | int 1 | NO | NO | NO | `citywide_table` |
| `publication.LEDGER_ROOT` | Path('publications') | NO | NO | NO | `build_site` |
| `publication.CHANGE_CLASSES` | tuple[4] | NO | NO | NO | `build_site` |
| `publication.PRELEDGER_PREFIX` | str 'r-preledger-' | NO | NO | NO | -- |
| `publication.AS_OF_RECONSTRUCTED` | str | NO | NO | NO | -- |
| `publication.MOVEMENTS` | tuple[6] | NO | NO | NO | -- |
| `rank_entries.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_leaderboard`, `build_make`, `build_play`, `build_site`, `build_your_forecast`, `site_assets` |
| `rank_entries.EDGE` | REPO_ROOT / 'src' / 'share-edge.js' | NO | NO | NO | -- |
| `rank_entries.ID_CHARS` | tuple[2] | NO | NO | NO | -- |
| `rank_entries.ANON_CHARS` | tuple[2] | NO | NO | NO | -- |
| `rank_entries.VOTE_DP` | int 1 | NO | NO | NO | -- |
| `rank_entries.WRANGLER` | REPO_ROOT / 'wrangler.toml' | NO | NO | NO | -- |
| `reader_seats.ASSUMPTION` | str | NO | NO | NO | -- |
| `render_home.ROOT` | Path(__file__).resolve().parent.parent | NO | NO | NO | `areas`, `backup_ignored`, `deploy_check`, `edit_mode`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_sheet`, `site_text` |
| `render_home.PAGE` | ROOT / 'home.html' | NO | NO | NO | -- |
| `render_home.HEAD_TO_HEAD_ORDER` | tuple[2] | NO | NO | NO | -- |
| `render_home.NAMED` | tuple(_scenarios.NAMED_PARTIES) | NO | NO | NO | -- |
| `render_home.LABEL` | _sheet.NAMES | NO | NO | NO | -- |
| `render_home.LEDE_PLACEHOLDERS` | dict[11] | NO | NO | NO | -- |
| `render_map.CHIPS` | dict[11] | NO | NO | NO | `build_play`, `render_sheet`, `site_assets` |
| `render_map.NAMES` | dict[8] | NO | NO | NO | `build_play`, `render_home`, `render_sheet` |
| `render_map.GREY` | str '#9aa09a' | NO | NO | NO | `hex_cartogram` |
| `render_map.MARK_START` | str '<!-- __MAP_START__ -->' | NO | NO | NO | `build_play`, `hex_cartogram` |
| `render_map.MARK_END` | str '<!-- __MAP_END__ -->' | NO | NO | NO | `build_play`, `hex_cartogram` |
| `render_map.STRIPE_MIN` | float 0.1 | NO | NO | NO | -- |
| `render_map.UNKNOWN_CHIP` | str '#5f6660' | NO | NO | NO | -- |
| `render_map.REST` | str '__rest__' | NO | NO | NO | -- |
| `render_map.TOSS_STEP` | float 7.0 | NO | NO | NO | `build_play` |
| `render_map.TOSS_ROTATE` | int 45 | NO | NO | NO | `build_play` |
| `render_map.SAFE` | float 0.9 | NO | NO | yes | -- |
| `render_map.TIP_FLOOR` | float 0.05 | NO | NO | yes | -- |
| `render_map.OTHER_FLOOR` | float 0.005 | NO | NO | yes | -- |
| `render_map.KEY_SOLID` | tuple[3] | NO | NO | NO | -- |
| `render_map.KEY_STRIPE_A` | tuple[3] | NO | NO | NO | -- |
| `render_map.KEY_STRIPE_B` | tuple[3] | NO | NO | NO | -- |
| `render_map.KEY_PARTIES` | tuple[8] | NO | NO | NO | -- |
| `render_sheet.CHIPS` | dict[12] | NO | NO | NO | `build_play`, `render_map`, `site_assets` |
| `render_sheet.OTHER_CHIP` | str '#8b918b' | NO | NO | NO | `build_play`, `site_assets` |
| `render_sheet.VERDICT_STEPS` | tuple[5] | NO | NO | NO | -- |
| `render_sheet.CHANCE_SCALE` | tuple[7] | NO | NO | yes | -- |
| `render_sheet.SETTLED_VERDICTS` | dict[2] | NO | NO | NO | -- |
| `render_sheet.VERDICT_STEP` | {**SETTLED_VERDICTS, **{word: step for _edge, word, step in CHANCE_SCALE | NO | NO | NO | -- |
| `render_sheet.HOLDS` | dict[9] | NO | NO | NO | -- |
| `render_sheet.VERDICT_ORDER` | ('FALSE',) + tuple((w for _e, w, _s in CHANCE_SCALE)) + ('TRUE',) | NO | NO | NO | -- |
| `render_sheet.NAMES` | dict[15] | NO | NO | NO | `build_play`, `render_home`, `render_map` |
| `render_sheet.SEAT_LAWS` | tuple[4] | NO | NO | NO | `build_play` |
| `render_sheet.COALITION_KEY_ORDER` | tuple[6] | NO | NO | NO | -- |
| `render_sheet.CHART_PARTIES` | list(_scenarios.NAMED_PARTIES) | NO | NO | NO | -- |
| `render_sheet.ALLIANCE_8` | tuple[8] | NO | NO | NO | -- |
| `render_sheet.WALL_FLIPS` | int 30 | NO | NO | yes | -- |
| `render_sheet.ZILLE_RED_LINES` | tuple[2] | NO | NO | yes | -- |
| `render_sheet.REALISTIC_PARTNERS` | tuple[2] | NO | NO | yes | -- |
| `render_sheet.DA_CORE_PARTNERS` | tuple[2] | NO | NO | yes | -- |
| `reweight.MIN_EFFECTIVE_DRAWS` | int 200 | NO | NO | yes | -- |
| `reweight.MAX_FIGURE_SE_SEATS` | float 2.5 | NO | NO | yes | `build_play` |
| `reweight.ANALYSIS_SEAT_BAND` | int 2 | NO | NO | yes | -- |
| `reweight.ANALYSIS_SHARE_BAND_POINTS` | float 2.0 | NO | NO | yes | -- |
| `reweight.PUBLISHED_LAW` | str 'deduct' | NO | NO | NO | -- |
| `reweight.BOLDNESS` | tuple[3] | NO | NO | NO | -- |
| `reweight.POLL_LABEL` | str | NO | NO | NO | -- |
| `reweight.FORMAT` | str 'draws-columnar-v1' | NO | NO | NO | `export_draws` |
| `reweight.DUAL_ROUNDING` | 64 * float(np.finfo(float).eps) | NO | NO | NO | -- |
| `scenarios.OPS` | {'>=': operator.ge, '<=': operator.le, '>': operator.gt, '<': operator.l | NO | NO | NO | -- |
| `scenarios.COND` | re.compile('^\\s*([A-Za-z_]+)\\s*(>=|<=|==|>|<)\\s*(\\d+)\\s*$') | NO | NO | NO | -- |
| `scenarios.BAND` | tuple[2] | NO | NO | NO | -- |
| `scenarios.BAND_SHARE` | (BAND[1] - BAND[0]) / 100 | NO | NO | NO | `render_home`, `render_sheet` |
| `scenarios.NAMED_PARTIES` | tuple[10] | NO | NO | NO | `render_home`, `render_sheet` |
| `scenarios.EXCESSIVE_FLOOR` | float 0.02 | NO | NO | NO | -- |
| `score.CLAIM_FRACTION` | float 0.5 | NO | NO | yes | `compare_history` |
| `score_forecasts.MEASURES` | tuple[3] | NO | NO | yes | -- |
| `score_forecasts.REPORTED` | tuple[2] | NO | NO | NO | -- |
| `score_forecasts.SEAT_SOURCES` | tuple[2] | NO | NO | NO | `rank_entries` |
| `score_forecasts.ROLL_COLUMNS` | tuple[3] | NO | NO | NO | -- |
| `seat_table.SEAT_SCALE` | int 125 | NO | NO | NO | `build_make`, `build_play` |
| `seat_table.SEAT_TICKS` | tuple[6] | NO | NO | NO | `build_make`, `build_play` |
| `seat_table.HEAD` | tuple[4] | NO | NO | NO | `build_play`, `build_validation`, `compare_history`, `declares`, `export_draws`, `freeze`, `publication` |
| `seat_table.HEAD_COUNCIL` | tuple[4] | NO | NO | NO | `build_make` |
| `seats.INDEPENDENT` | str 'INDEPENDENT' | NO | NO | yes | `backtest`, `benchmarks`, `build_make`, `montecarlo`, `parties`, `validate_seats` |
| `site_assets.REPO_ROOT` | Path(__file__).resolve().parents[1] | NO | NO | NO | `build_leaderboard`, `build_make`, `build_play`, `build_site`, `build_your_forecast`, `rank_entries` |
| `site_assets.CSS_SRC` | REPO_ROOT / 'src' / 'css' | NO | NO | NO | `build_site` |
| `site_assets.JS_SRC` | REPO_ROOT / 'src' / 'js' | NO | NO | NO | -- |
| `site_assets.FONT_SRC` | REPO_ROOT / 'src' / 'fonts' | NO | NO | NO | -- |
| `site_assets.CSS_PATH` | str 'css/site.css' | NO | NO | NO | `build_site` |
| `site_assets.JS_DIR` | str 'js' | NO | NO | NO | `build_site` |
| `site_assets.FONT_DIR` | str 'fonts' | NO | NO | NO | -- |
| `site_assets.BRAND_SRC` | REPO_ROOT / 'src' / 'brand' | NO | NO | NO | -- |
| `site_assets.LOGO` | str 'logo.svg' | NO | NO | NO | `build_site` |
| `site_assets.LOGO_VIEWBOX` | str '19 87 2826 1296' | NO | NO | NO | `build_site` |
| `site_assets.UMBRELLA` | str 'whysoserious.svg' | NO | NO | NO | -- |
| `site_assets.UMBRELLA_VIEWBOX` | str '440 272 1984 1016' | NO | NO | NO | -- |
| `site_assets.APEX_URL` | str | NO | NO | NO | `build_site` |
| `site_assets.BRAND_FILES` | tuple[6] | NO | NO | NO | -- |
| `site_assets.CSS_FILES` | tuple[16] | NO | NO | NO | -- |
| `site_assets.PAGE_CSS` | re.compile('page-([a-z]+(?:-[a-z]+)*)\\.css') | NO | NO | NO | `build_site` |
| `site_assets.FONT_FACES` | tuple[3] | NO | NO | NO | -- |
| `site_assets.FONT_RANGE` | str | NO | NO | NO | -- |
| `site_assets.INLINE` | (('a <style> element', re.compile('<style\\b', re.I)), ('a style attribu | NO | NO | NO | -- |
| `site_text.ROOT` | Path(__file__).resolve().parent.parent | NO | NO | NO | `areas`, `backup_ignored`, `deploy_check`, `edit_mode`, `export_draws`, `inputs_preflight`, `judgement_sheet`, `model_index`, `render_home`, `render_sheet` |
| `site_text.OUT` | ROOT / 'SITE-TEXT.md' | NO | NO | NO | -- |
| `site_text.STATS` | ROOT / 'content' / 'joburg' / 'stats.toml' | NO | NO | NO | `edit_mode` |
| `site_text.REBUILD` | str | NO | NO | NO | `edit_mode` |
| `site_text.CUT_KINDS` | frozenset((spec[1] for spec in build_site.ARTEFACTS.values() if spec[1]) | NO | NO | NO | -- |
| `site_text.GENERATED` | re.compile('<!--\\s*__(?!(?:' + '|'.join(sorted(CUT_KINDS)) + ')_START__ | NO | NO | NO | -- |
| `site_text.GENERATED_MD` | GENERATED | NO | NO | NO | -- |
| `site_text.PLACEHOLDER` | re.compile('|'.join((stats.GEN_TOKEN.pattern, '\\{\\{\\w+\\}\\}', '\\[\\ | NO | NO | NO | `edit_mode` |
| `site_text.BLOCK_ID` | re.compile('^<!-- block (\\w+) -->$', re.M) | NO | NO | NO | -- |
| `site_text.CLAIM_FIELDS` | tuple[6] | NO | NO | NO | -- |
| `site_text.ARTICLE_FIELDS` | tuple[2] | NO | NO | NO | -- |
| `site_text.LEDE_FIELDS` | tuple[2] | NO | NO | NO | -- |
| `site_text.INLINE_TAGS` | frozenset('a abbr b bdi bdo br cite code data dfn em i img kbd mark q s  | NO | NO | NO | `edit_mode` |
| `site_text.OPAQUE` | frozenset('script style svg head title select textarea template noscript | NO | NO | NO | -- |
| `site_text.VOID` | frozenset('area base br col embed hr img input link meta source track wb | NO | NO | NO | -- |
| `site_text.HTML_SOURCES` | tuple[2] | NO | NO | NO | -- |
| `site_text.MD_DIR` | str 'docs-public' | NO | NO | NO | -- |
| `site_text.TOML_SOURCES` | {'content/joburg/articles.toml': ('article', ARTICLE_FIELDS, ()), 'conte | NO | NO | NO | -- |
| `site_text.TAG` | re.compile('<!--.*?-->|<(/?)([a-zA-Z][\\w-]*)[^>]*?>', re.S) | NO | NO | NO | `edit_mode` |
| `stats.UNVERIFIABLE` | str 'unverifiable' | NO | NO | NO | -- |
| `stats.DECLARATION_MIN_CHARS` | int 12 | NO | NO | NO | `edit_mode` |
| `stats.HISTORICAL` | str 'historical' | NO | NO | NO | -- |
| `stats.TOKEN` | re.compile('\\{\\{([a-z0-9_]+)\\}\\}') | NO | NO | NO | -- |
| `stats.GEN_TOKEN` | re.compile('\\{\\{@([A-Za-z0-9_.+\\-]+)=([^;{}]*);([a-z0-9_]*);([^{}]*)\ | NO | NO | NO | `edit_mode`, `site_text` |
| `stats.LIVE_ATTR` | str 'data-live' | NO | NO | NO | -- |
| `stats.LIVE_NAME` | re.compile('^[a-z][a-z0-9-]*$') | NO | NO | NO | -- |
| `stats.LIVE_WRITERS` | {'your-forecast/js/model.js': frozenset({'engine', 'busy', 'banner', 're | NO | NO | NO | -- |
| `stats.REFERENCE_ARTEFACT` | str 'forecast_summary.json' | NO | NO | NO | -- |
| `stats.FRESHNESS_GRACE_S` | float 300.0 | NO | NO | yes | -- |
| `stats.FRESHNESS_REMEDY` | dict[1] | NO | NO | NO | -- |
| `stats.COUNCIL_CONSTANT_SOURCES` | tuple[2] | NO | NO | NO | -- |
| `stats.SOURCED` | re.compile('<span[^>]*data-token="[^"]*".*?</span>', re.S) | NO | NO | NO | `edit_mode` |
| `stats.TAGS` | re.compile('<[^>]+>') | NO | NO | NO | `edit_mode`, `site_text` |
| `stats.SCRIPTS` | re.compile('<(script|style)[^>]*>.*?</\\1>', re.S) | NO | NO | NO | -- |
| `stats.NUMBERISH` | re.compile(f'(?P<date>\\b\\d{{1,2}}\\s(?:{_MONTHS})\\s\\d{{4}}\\b|\\b\\d | NO | NO | NO | `edit_mode` |
| `stats.GATING` | tuple[3] | NO | NO | NO | `edit_mode` |
| `stats.GENERATED_MARKERS` | frozenset({'MAP', 'HEXMAP', 'BALLOTS', 'REGIMES', 'VALIDATION'}) | NO | NO | NO | `build_site` |
| `stats.REGION` | re.compile('<!-- __([A-Z]+)_START__ -->(.*?)<!-- __\\1_END__ -->', re.S) | NO | NO | NO | `build_site` |
| `stats.ATTRS` | re.compile('\\b(?:title|data-tip|aria-label|alt|content)="([^"]*)"') | NO | NO | NO | -- |
| `stats.ALL_PAGES` | str '*' | NO | NO | NO | -- |
| `stats.CHROME_CLASSES` | tuple[7] | NO | NO | NO | -- |
| `stats.SCRIPT_FORBIDDEN` | (('a data block', re.compile('\\b(?:const|let|var)\\s+[A-Za-z_$][\\w$]*\ | NO | NO | NO | -- |
| `stats.WRITER_FORBIDDEN` | (('HTML injection', re.compile('\\.(?:innerHTML|outerHTML)\\b|insertAdja | NO | NO | NO | -- |
| `stats.ANALYTICS_BEACON` | str | NO | NO | NO | `build_site` |
| `stats.CLAIM_PATTERNS` | tuple[10] | NO | NO | NO | -- |
| `sweep.CITIES` | list[8] | NO | NO | NO | `arrivals`, `build_validation`, `compare_history`, `judgement_sheet` |
| `sweep.PARTY_ROW` | re.compile("^\\s{2}([A-Z][A-Z0-9_']*)\\s+(\\d+)\\s+(\\d+)\\s+([\\d.]+)\\ | NO | NO | NO | -- |
| `theta_residual.BINS` | tuple[5] | NO | NO | yes | -- |
| `theta_residual.BOOT` | int 4000 | NO | NO | NO | -- |
| `theta_residual.BOOT_SEED` | int 20211101 | NO | NO | NO | -- |
| `theta_residual.SIM_DRAWS` | int 4000000 | NO | NO | NO | -- |
| `theta_residual.NULL_REPS` | int 20000 | NO | NO | NO | -- |
| `turnout.ELECTIONS` | {year: (e.results, e.two_ballot) for year, e in sorted(cityconfig.CALEND | NO | NO | NO | `build_concordance`, `build_crosswalk` |
| `turnout.LAMBDA_PAIRS` | {year: (cityconfig.preceding(year, 'NPE'), year) for year, e in sorted(c | NO | NO | NO | -- |
| `width_budget.REPO` | Path(__file__).resolve().parents[1] | NO | NO | NO | `citywide_table`, `declares`, `freeze` |
| `width_budget.DATA` | REPO / 'data/raw/elections' | NO | NO | NO | `build_make`, `build_your_forecast`, `freeze` |

## 6 · Folds and windows

Every name that declares a SPAN — of folds, of history, of recency — matched on the name and then read off the object.

| name | where | value | spans |
|---|---|---|---|
| `bye_tau_months` | `montecarlo.DEFAULTS` | 18.0 | -- |
| `poll_half_life_days` | `montecarlo.DEFAULTS` | 120.0 | -- |
| `LGE_YEARS` | `derive_city` | tuple[3] | -- |
| `FOLDS` | `fold` | dict[5] | -- |
| `SNAPSHOT_STALE_DAYS` | `inputs_preflight` | int 21 | -- |
| `SIZE_WINDOW_GRID` | `levels` | (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, float('inf')) | -- |
| `SIZE_WINDOW_MIN_SCORED` | `levels` | int 20 | -- |
| `SIZE_WINDOW_TIE` | `levels` | float 0.005 | -- |
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
| `backtest.register` | measurement | ``FITTED_ON`` and ``FITTED_ON_UNINSTRUMENTED`` as one mapping. | `build_play`, `edit_mode`, `model_index`, `tests/test_chain`, `tests/test_edit_mode`, `tests/test_intermediates_are_current`, `tests/test_levers_are_live`, `tests/test_register_matches_code`, `tests/test_reweight`, `tests/test_served_draws`, `tests/test_stage_estimation` |
| `backtest.unsettled` | measurement | :data:`PROVENANCE_UNSETTLED` keys this run held that could bite here. | `tests/test_levers_are_live`, `tests/test_stage_inputs` |
| `backtest.contaminated` | measurement | ``FITTED_ON`` keys that read this target or later, minus declared ones. | `compare_history`, `tests/test_chain`, `tests/test_levers_are_live`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs` |
| `backtest.check_derived_from` | measurement | Validate a scenario's ``derived_from`` list; return it as strings. | -- |
| `backtest.in_sample_banner` | measurement | The warning (or the all-clear) for one scenario at one target. | `compare_history`, `tests/test_levers_are_live` |
| `backtest.relabel_entrant` | measurement | Rename the generic ``ENTRANT`` to the party that actually arrived. | `tests/test_regressions` |
| `backtest.ward_structure` | measurement | VD -> ward and VD -> registered, from the target's own result file. | `benchmarks` |
| `backtest.actual_result` | measurement | The real council and the real ward winners, checked against the IEC. | `arrivals`, `benchmarks`, `compare_history`, `diagnose`, `tests/test_covariate_fail_open`, `tests/test_prediction_rule`, `tests/test_roster_aware_baseline` |
| `backtest.arrival_baseline` | measurement | **THE ONE DEFINITION OF "HAS A BASELINE" IN THIS REPOSITORY.** | `compare_history`, `tests/test_covariate_fail_open`, `tests/test_panel_wiring` |
| `backtest.entrant_actual_for_target` | measurement | Which party arrived from nothing at ``target``. **The one call path.** | `compare_history`, `diagnose`, `tests/test_covariate_fail_open`, `tests/test_panel_wiring` |
| `backtest.entrant_actual_for` | measurement | Which party actually arrived from nothing, if any. | `tests/test_covariate_fail_open`, `tests/test_panel_wiring`, `tests/test_regressions` |
| `backtest.arrival_group_score` | measurement | Score the arrival channel as a GROUP, with **no per-party label**. | `compare_history`, `tests/test_calibration_report`, `tests/test_panel_wiring` |
| `backtest.relabel_run` | measurement | Rename the generic ``ENTRANT`` **on the run itself**, once, in place. | `compare_history`, `tests/test_calibration_report`, `tests/test_regressions` |
| `benchmarks.sources_for` | measurement | Files each baseline needs that the backtest's TARGETS table does not name. | -- |
| `benchmarks.council_size` | measurement | Seats in the target's council, from the city config's per-year structure. | `build_play`, `build_site`, `coalitions`, `export_draws`, `montecarlo`, `render_home`, `render_map`, `render_sheet`, `scenarios`, `stats`, `tests/test_draw_record`, `tests/test_export_draws`, `tests/test_home_page`, `tests/test_prediction_rule`, `tests/test_provenance_dates`, `tests/test_reweight`, `tests/test_scenarios` |
| `benchmarks.build_context` | measurement | Gather every pre-election input the baselines need. | `compare_history`, `diagnose`, `tests/test_covariate_fail_open`, `tests/test_roster_aware_baseline` |
| `benchmarks.benchmark_lot` | measurement | The seeded lot's key for one baseline at one city-year: | `compare_history`, `tests/test_roster_aware_baseline` |
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
| `benchmarks.ward_probabilities` | measurement | ``{ward: {party: P(win)}}`` from a list of per-draw winner maps. | `backtest`, `compare_history`, `diagnose`, `montecarlo`, `tests/test_prediction_rule` |
| `cityconfig.preceding` | model+measurement | The last election of `kind` strictly before `year`, or None. | `benchmarks`, `build_make`, `levels`, `pools`, `tests/test_chain`, `tests/test_data_coverage`, `tests/test_levels_dispersion`, `tests/test_share`, `tests/test_theta_prior`, `tests/test_your_forecast_page`, `theta_residual`, `turnout` |
| `cityconfig.load` | model+measurement | -- | `areas`, `arrivals`, `backtest`, `benchmarks`, `build_geo`, `build_interactive`, `build_play`, `build_portal`, `compare_history`, `diagnose`, `export_interactive`, `fetch_boundaries`, `fold`, `gamma_recent`, `inputs_preflight`, `montecarlo`, `polling`, `pools`, `reader_seats`, `render_map`, `render_sheet`, `scenarios`, `score_forecasts`, `stats`, `sweep`, `tests/test_artefact_key_discriminates`, `tests/test_build_all`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_draw_record`, `tests/test_drawer`, `tests/test_inputs_preflight`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_reader_seats`, `tests/test_regressions`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scenarios`, `tests/test_scoreboard_disclosure`, `tests/test_served_draws`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_temporal`, `tests/test_unopposed`, `tests/test_ward_pr_ratios`, `theta_residual` |
| `cityconfig.use` | model+measurement | Set the active city for this process. | `arrivals`, `backtest`, `benchmarks`, `build_all`, `build_concordance`, `build_crosswalk`, `build_geo`, `build_site`, `byelections`, `citywide_table`, `coalitions`, `compare_history`, `diagnose`, `export_draws`, `export_interactive`, `fold`, `freeze`, `gamma_recent`, `ingest_historic`, `ingest_lge`, `ingest_npe`, `montecarlo`, `pools`, `rank_entries`, `render_home`, `render_map`, `render_sheet`, `scenarios`, `site_text`, `tests/_support`, `tests/test_build_all`, `tests/test_calibration_report`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_covariate_fail_open`, `tests/test_data_coverage`, `tests/test_declared_ward_slates`, `tests/test_drawer`, `tests/test_export_draws`, `tests/test_ipf_feasibility`, `tests/test_levers_are_live`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_provenance_dates`, `tests/test_publication_ledger`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_unopposed`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `tests/test_your_forecast_page`, `turnout`, `validate_seats`, `width_budget` |
| `cityconfig.active` | model+measurement | -- | `backtest`, `benchmarks`, `build_crosswalk`, `build_make`, `build_site`, `diagnose`, `export_interactive`, `fold`, `iec_csv`, `ingest_lge`, `ingest_npe`, `montecarlo`, `publication`, `rank_entries`, `tests/_support`, `tests/test_covariate_fail_open`, `tests/test_pool_conservation`, `tests/test_roster_aware_baseline`, `tests/test_share`, `tests/test_site_structure`, `tests/test_spine`, `tests/test_theta_prior`, `tests/test_ward_parts`, `tests/test_your_forecast_page`, `turnout`, `validate_seats` |
| `cityconfig.use_target` | model+measurement | Set the active target election; None means the active city's next one. | `arrivals`, `backtest`, `build_site`, `byelections`, `citywide_table`, `coalitions`, `compare_history`, `diagnose`, `export_draws`, `export_interactive`, `freeze`, `gamma_recent`, `montecarlo`, `pools`, `render_sheet`, `scenarios`, `site_text`, `tests/test_calibration_report`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_declared_ward_slates`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_provenance_dates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_unopposed`, `tests/test_ward_parts`, `theta_residual`, `turnout`, `width_budget` |
| `cityconfig.target` | model+measurement | -- | `areas`, `arrivals`, `backtest`, `backup_ignored`, `benchmarks`, `build_concordance`, `build_make`, `build_play`, `build_site`, `build_validation`, `byelections`, `citywide_table`, `coalitions`, `compare_history`, `declares`, `diagnose`, `export_draws`, `export_interactive`, `fold`, `freeze`, `gamma_recent`, `inputs_preflight`, `judgement_sheet`, `levels`, `model_index`, `montecarlo`, `polling`, `pools`, `rank_entries`, `reader_seats`, `render_map`, `render_sheet`, `reweight`, `scenarios`, `score_forecasts`, `seats`, `sweep`, `tests/_support`, `tests/test_artefact_key_discriminates`, `tests/test_calibration_report`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates`, `tests/test_draw_record`, `tests/test_inputs_preflight`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_panel_wiring`, `tests/test_polling_register`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prediction_rule`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_reader_seats`, `tests/test_regressions`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_score_forecasts`, `tests/test_scoreboard_disclosure`, `tests/test_served_draws`, `tests/test_site_text`, `tests/test_solve_and_predict`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_temporal`, `tests/test_theta_prior`, `tests/test_unopposed`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `tests/test_your_forecast_page`, `theta_residual`, `turnout` |
| `cityconfig.resolve_path` | model+measurement | Substitute {CODE}/{SLUG} in a path or filename. | `backtest`, `build_concordance`, `build_crosswalk`, `build_geo`, `build_make`, `byelections`, `compare_history`, `edit_mode`, `fold`, `montecarlo`, `render_map`, `tests/test_covariate_fail_open`, `tests/test_drawer`, `tests/test_edit_mode`, `tests/test_ipf_feasibility`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `tests/test_your_forecast_page`, `turnout` |
| `cityconfig.add_city_argument` | model+measurement | Standard ``--city`` flag; every script defaults to Johannesburg so | `areas`, `backtest`, `benchmarks`, `build_all`, `build_concordance`, `build_crosswalk`, `build_geo`, `build_interactive`, `build_site`, `byelections`, `coalitions`, `export_draws`, `export_interactive`, `fold`, `gamma_recent`, `ingest_historic`, `ingest_lge`, `ingest_npe`, `montecarlo`, `pools`, `rank_entries`, `render_home`, `render_map`, `render_sheet`, `scenarios`, `turnout`, `validate_seats` |
| `cityconfig.add_target_argument` | model+measurement | Standard ``--target`` flag: which election is being built. | `byelections`, `export_draws`, `gamma_recent`, `montecarlo`, `pools`, `turnout` |
| `coalitions.subset_totals` | model+measurement | Seat totals for every subset. seats: (draws, n) -> (2**n, draws). | -- |
| `coalitions.minimal_winning` | model+measurement | Mask -> boolean per draw: is this subset a *minimal* winning coalition. | -- |
| `coalitions.banzhaf` | model+measurement | Banzhaf index per party per draw, normalised to sum to 1. | -- |
| `coalitions.shapley_shubik` | model+measurement | Shapley–Shubik index per party per draw. | -- |
| `coalitions.minority_viable` | model+measurement | Arithmetic viability of a minority administration, per draw. | -- |
| `coalitions.mask_label` | model+measurement | -- | -- |
| `coalitions.analyse` | model+measurement | Run the full §3.8 suite. Returns a dict of result tables. | `montecarlo`, `tests/test_your_forecast_page` |
| `coalitions.report` | model+measurement | -- | `contested_area`, `declares`, `export_draws`, `fetch_iec`, `fold`, `levels`, `montecarlo`, `tests/test_published_page`, `tests/test_regressions`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe`, `tests/test_stat_freshness`, `tests/test_temporal`, `tests/test_theta_prior`, `theta_residual` |
| `coalitions.write_outputs` | model+measurement | -- | `montecarlo` |
| `compare_history.scored_opponents` | measurement | Every reference in `benchmarks.BENCHMARKS` bar those explicitly refused. | `diagnose`, `tests/test_scoreboard_disclosure` |
| `compare_history.opponent_columns` | measurement | The reference columns a REPORT prints: the scored set, plus the artefact's. | `tests/test_scoreboard_disclosure` |
| `compare_history.runnable` | measurement | Targets this city can actually run, AND why each other one cannot. | `backtest`, `benchmarks`, `fold`, `sweep`, `tests/test_roster_fails_closed`, `tests/test_standalone_modules`, `tests/test_temporal` |
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
| `compare_history.render` | measurement | -- | `build_interactive`, `build_portal`, `build_site`, `edit_mode`, `hex_cartogram`, `judgement_sheet`, `stats`, `tests/test_build_all`, `tests/test_calibration_report`, `tests/test_hex_cartogram`, `tests/test_home_page`, `tests/test_provenance_dates`, `tests/test_publication_ledger`, `tests/test_published_page`, `tests/test_scoreboard_disclosure` |
| `compare_history.moved_module_constants` | measurement | ``(moved, unwatched)`` — what would not survive a fork, and what is blind. | -- |
| `compare_history.build_manifest` | measurement | What produced this scoreboard, assembled from `freeze`'s existing code. | `tests/test_provenance_gates` |
| `compare_history.load_history` | measurement | Read a scoreboard artefact, and REFUSE the pre-manifest shape. | `tests/test_calibration_report`, `tests/test_pool_bounds`, `tests/test_scoreboard_disclosure` |
| `fold.logit` | model+measurement | -- | `montecarlo`, `tests/test_solve_and_predict` |
| `fold.load` | model+measurement | Return VD -> canonical party -> votes, and VD -> ward. | `areas`, `arrivals`, `backtest`, `benchmarks`, `build_geo`, `build_interactive`, `build_play`, `build_portal`, `cityconfig`, `compare_history`, `diagnose`, `export_interactive`, `fetch_boundaries`, `gamma_recent`, `inputs_preflight`, `montecarlo`, `polling`, `pools`, `reader_seats`, `render_map`, `render_sheet`, `scenarios`, `score_forecasts`, `stats`, `sweep`, `tests/test_artefact_key_discriminates`, `tests/test_build_all`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_draw_record`, `tests/test_drawer`, `tests/test_inputs_preflight`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_reader_seats`, `tests/test_regressions`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scenarios`, `tests/test_scoreboard_disclosure`, `tests/test_served_draws`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_temporal`, `tests/test_unopposed`, `tests/test_ward_pr_ratios`, `theta_residual` |
| `fold.shares` | model+measurement | -- | `benchmarks`, `build_make`, `citywide_table`, `export_interactive`, `gamma_recent`, `levels`, `montecarlo`, `pools`, `reweight`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_panel_wiring`, `tests/test_pool_bounds`, `tests/test_prior_local_fails_closed`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_scoreboard_disclosure`, `tests/test_stage_realisation` |
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
| `freeze.resolved_switches` | measurement | What the switches were, as the modules RESOLVED them. | `compare_history`, `export_draws` |
| `freeze.pool_artefact_keys` | measurement | The `artefact_key` of every emitted spec for this city. | `build_site`, `compare_history`, `declares`, `export_draws`, `publication`, `tests/test_export_draws`, `tests/test_provenance_gates`, `tests/test_served_draws` |
| `freeze.run_forecast` | measurement | -- | -- |
| `freeze.bundle` | measurement | -- | `tests/test_stage_realisation` |
| `iec_csv.active_muni_code` | model+measurement | The active city's IEC municipality code — the row filter for every | `ingest_lge`, `ingest_npe` |
| `iec_csv.sniff_encoding` | model+measurement | Return an encoding that decodes ``src``: its BOM if it has one, else a guess. | `derive_city`, `ingest_lge`, `ingest_npe` |
| `iec_csv.normalise_header` | model+measurement | Fold a raw header cell to an upper-snake-case key. | `ingest_lge`, `ingest_npe` |
| `iec_csv.is_int` | model+measurement | -- | `ingest_npe` |
| `iec_csv.muni_code` | model+measurement | -- | `ingest_lge`, `ingest_npe` |
| `iec_csv.ward_number` | model+measurement | Reduce ``Ward 79800001`` to ``79800001``; pass anything else through. | `build_make`, `ingest_lge`, `score_forecasts`, `tests/test_score_forecasts` |
| `iec_csv.write_csv` | model+measurement | -- | `ingest_lge`, `ingest_npe` |
| `iec_csv.summarise` | model+measurement | Format a turnout and party-share summary, for eyeballing against plan §8. | `build_site`, `ingest_lge`, `ingest_npe`, `publication`, `tests/test_publication_ledger` |
| `ingest_lge.read_municipality` | model+measurement | Return the rows of ``src`` for one municipality, with canonical columns. | `contested_area`, `ingest_npe`, `polling`, `pools`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach` |
| `levels.ballot_roster` | model+measurement | The party NAMES on one result file's ballot. Names only, never votes. | `tests/test_levels_dispersion`, `tests/test_roster_fails_closed` |
| `levels.absent_from_ballot` | model+measurement | Parties holding baseline share that are NOT standing at the target. | `montecarlo`, `tests/test_levels_dispersion`, `tests/test_projected_roster_declaration`, `tests/test_roster_aware_baseline`, `theta_residual` |
| `levels.theta_record` | model+measurement | Every observed national-to-local retention ratio before the target. | `montecarlo`, `tests/test_chain`, `tests/test_regressions`, `tests/test_spine`, `tests/test_temporal`, `tests/test_theta_prior`, `theta_residual` |
| `levels.result_path` | model+measurement | Where this city-year's VD result file would be, or None if unscheduled. | `tests/test_declared_ward_slates` |
| `levels.has_result_file` | model+measurement | Has this election been held and ingested? | `montecarlo`, `tests/test_declared_ward_slates` |
| `levels.declared_contestation` | model+measurement | The ward slates a NOMINATION LIST declares, and whether it is the whole | `montecarlo`, `tests/test_declared_ward_slates` |
| `levels.projected_contestation` | model+measurement | A slate for a target whose nomination lists are not published yet. | `montecarlo` |
| `levels.local_record` | model+measurement | Every observed LOCAL-to-LOCAL retention ratio before the target. | `montecarlo`, `tests/test_regressions`, `tests/test_spine`, `tests/test_temporal` |
| `levels.theta_prior` | model+measurement | Per-party (low, mode, high) on θ, and the groups they were drawn from. | `montecarlo`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_theta_prior`, `theta_residual` |
| `levels.size_centre` | model+measurement | The centre θ shrinks TOWARD, as a function of how big the party is. | `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_theta_prior`, `theta_residual` |
| `levels.size_window` | model+measurement | The size window ``h`` for one record at ``target``, derived from data. | `montecarlo`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_temporal` |
| `levels.spine` | model+measurement | Each party's central level at the target, from BOTH of its records. | `backtest`, `montecarlo`, `tests/test_blended_centres`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_stage_inputs` |
| `levels.ward_pr_ratios` | model+measurement | Each party's ward-ballot share over its PR share, from the last LGE. | `montecarlo`, `tests/test_ward_pr_ratios` |
| `levels.contestation` | model+measurement | The fraction of wards each party fields a ward candidate in. | `backtest`, `compare_history`, `montecarlo`, `pools`, `tests/test_chain`, `tests/test_declared_ward_slates`, `tests/test_levers_are_live` |
| `levels.slate_coverage` | model+measurement | Each party's slate, weighted by where its own list vote lies. | `montecarlo`, `tests/test_declared_ward_slates` |
| `levels.unopposed_in` | model+measurement | The unopposed wards in one election, from who stood in each ward. | `backtest`, `tests/test_unopposed` |
| `levels.ward_ballots` | model+measurement | Every ward a result file covers, and the parties on each ward ballot. | `backtest`, `tests/test_unopposed` |
| `levels.unopposed_wards` | model+measurement | ``{ward: party}`` for each unopposed ward at ``target``. | `montecarlo`, `tests/test_unopposed` |
| `levels.unopposed_pr_votes` | model+measurement | ``{party: its PR votes in the wards it won unopposed}``, from a result file. | `backtest` |
| `levels.local_record_only` | model+measurement | Roster parties whose only record is the previous local election. | `montecarlo`, `tests/test_roster_universe` |
| `montecarlo.logit` | model+measurement | -- | `fold`, `tests/test_solve_and_predict` |
| `montecarlo.expit` | model+measurement | -- | `fold` |
| `montecarlo.triangular` | model+measurement | -- | -- |
| `montecarlo.log_shock` | model+measurement | exp of a Student-t scaled to have log-sd exactly ``sd``. Median 1. | `tests/test_ipf_feasibility`, `tests/test_regressions`, `width_budget` |
| `montecarlo.capped_targets` | model+measurement | Hold every column target under its cap WITHOUT changing the total. | `tests/test_ipf_feasibility` |
| `montecarlo.partial_balance` | model+measurement | Alternating scaling for margins that CANNOT both hold. Ends on the rows. | `tests/test_ipf_feasibility` |
| `montecarlo.correlated_triangular` | model+measurement | A triangular draw pushed by a shared standard normal. | `tests/test_draw_record`, `width_budget` |
| `montecarlo.months_before_election` | model+measurement | How long before election day a by-election was held, in months. | -- |
| `montecarlo.fold_target_year` | model+measurement | The year of the LGE a fold predicts, read off its target filename. | -- |
| `montecarlo.gamma_fold_for` | model+measurement | The fold supplying γ for this target, checked to precede it. | `backtest` |
| `montecarlo.read_ward_crosswalk` | model+measurement | The VD→ward crosswalk: ``([(vd, ward, part_registered), ...], vds, split)``. | `areas`, `export_interactive`, `pools`, `tests/test_ward_parts` |
| `montecarlo.ward_parts` | model+measurement | VD → ward parts and their registration: ``[(vd, ward, registered), ...]``. | `build_concordance`, `build_make`, `tests/test_ward_parts`, `tests/test_your_forecast_page` |
| `montecarlo.solve_and_predict` | model+measurement | Solve for θ reaching `target` citywide through the model; return VD shares. | `tests/test_solve_and_predict` |
| `montecarlo.parse_set` | model+measurement | Apply --set key=value overrides; values parsed as JSON where possible. | -- |
| `montecarlo.apply_city` | model+measurement | Point the module's constants at this city, from a CLEAN baseline. | `arrivals`, `backtest`, `benchmarks`, `compare_history`, `diagnose`, `export_draws`, `freeze`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levers_are_live`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `width_budget` |
| `montecarlo.fix_hash_seed` | model+measurement | Re-exec this process once under a fixed ``PYTHONHASHSEED``. | `backtest`, `compare_history`, `diagnose`, `export_draws`, `freeze`, `overhang_regimes`, `sweep`, `tests/run_all`, `tests/test_calibration_report`, `tests/test_provenance_gates` |
| `montecarlo.note_value` | model+measurement | Record that ``name`` was consulted AT ``value``, and return ``value``. | `tests/test_delivery_proof` |
| `montecarlo.note_module_constants` | model+measurement | Record what THIS PROCESS holds for every declared module constant. | `tests/test_delivery_proof` |
| `montecarlo.delivery_log` | model+measurement | The value-bearing read log of a run, from whatever holds it. | `backtest` |
| `montecarlo.assert_delivered` | model+measurement | Prove that ``name`` reached the run, at ``expected``. Raise if it did not. | `tests/test_delivery_proof` |
| `montecarlo.note_constant` | model+measurement | Record that a hand-typed constant was actually consumed by this run. | -- |
| `montecarlo.read_scenario_file` | model+measurement | ``(overrides, metadata)`` from a scenario JSON, unknown keys rejected. | `backtest` |
| `montecarlo.blend_poll_centre` | model+measurement | Blend a poll reading into a modelled centre. Returns ``(centre, w)``. | `tests/test_blended_centres`, `tests/test_regressions` |
| `montecarlo.apply_overrides` | model+measurement | Merge a validated override dict into a scenario, dicts key by key. | `backtest` |
| `montecarlo.load_scenario` | model+measurement | -- | `arrivals`, `citywide_table`, `compare_history`, `diagnose`, `export_draws`, `freeze`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_levers_are_live`, `tests/test_pool_conservation`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_unopposed`, `width_budget` |
| `montecarlo.blended_centres` | model+measurement | Central citywide level per party at the target, from θ modes tilted by evidence. | `tests/test_blended_centres`, `tests/test_drawer`, `tests/test_ipf_feasibility` |
| `montecarlo.compress_levels` | model+measurement | Pull each central level down by its own size, then give the mass back. | `tests/test_chain`, `tests/test_stage_estimation` |
| `montecarlo.pool_spec` | model+measurement | Build the per-pool draw specification for the weighted engine (§1.29). | `tests/test_drawer`, `tests/test_pool_conservation` |
| `montecarlo.make_drawer` | model+measurement | Return a function drawing one citywide PR target vector. | `tests/test_draw_record`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_conservation` |
| `montecarlo.allocate_with_overhang` | model+measurement | Schedule 1 allocation with the excessive-seats treatment. | `benchmarks`, `prediction`, `tests/test_overhang`, `tests/test_seats` |
| `montecarlo.roster_for_target` | model+measurement | Who is on ``target``'s ballot, and WHICH of four states that answer is in. | `benchmarks`, `tests/test_projected_roster_declaration`, `tests/test_roster_fails_closed` |
| `montecarlo.slate_change_ratio` | model+measurement | A party's ward/PR ratio moved by the change in its slate (item 6). | `tests/test_declared_ward_slates` |
| `montecarlo.roster_universe_check` | model+measurement | Check the target's roster against the run's parties, both ways (G8). | `tests/test_roster_universe` |
| `montecarlo.run_model` | model+measurement | Run the forecast for one target election. | `arrivals`, `backtest`, `citywide_table`, `compare_history`, `diagnose`, `export_draws`, `freeze`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_levers_are_live`, `tests/test_pool_conservation`, `tests/test_prediction_rule`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_unopposed`, `tests/test_ward_pr_ratios`, `width_budget` |
| `montecarlo.published_ward_winner` | model+measurement | The winner column of ``ward_winner_probs.csv`` for one ward: rule A's | `tests/test_prediction_rule` |
| `official_seats.read` | measurement | Official figures for one municipality-year, or None if not on disk. | `archive`, `backtest`, `build_crosswalk`, `build_make`, `compare_history`, `edit_mode`, `fetch_boundaries`, `fetch_byelections`, `fetch_iec`, `pools`, `rank_entries`, `tests/run_all`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_data_coverage`, `tests/test_entries`, `tests/test_freeze`, `tests/test_prior_local_fails_closed`, `tests/test_score_forecasts`, `tests/test_scoreboard_disclosure`, `tests/test_seats`, `tests/test_stage_inputs`, `tests/test_your_forecast_page`, `validate_seats` |
| `parties.normalise` | model+measurement | Fold a raw party string: upper case, collapsed whitespace, tidy dashes. | `prep_logos`, `score_forecasts` |
| `parties.canonical` | model+measurement | Return the canonical code for a raw party string. | `backtest`, `build_crosswalk`, `build_make`, `byelections`, `contested_area`, `fold`, `freeze`, `levels`, `pools`, `score_forecasts`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates`, `tests/test_freeze`, `tests/test_score_forecasts`, `tests/test_your_forecast_page` |
| `parties.display_name` | model+measurement | -- | `build_crosswalk`, `score_forecasts`, `tests/test_score_forecasts` |
| `parties.is_modelled` | model+measurement | True if the party carries its own theta parameter in plan §3.5. | `build_crosswalk` |
| `polling.design_effect` | model+measurement | How much of the recorded ``n`` is real information. | `tests/test_polling_sd` |
| `polling.effective_n` | model+measurement | ``n / deff`` — the sample size that is actually doing work. | `levels`, `tests/test_polling_sd`, `tests/test_stage_estimation`, `tests/test_theta_prior` |
| `polling.poll_sd` | model+measurement | Total error on one poll's reading of one party, in share units. | `reweight`, `tests/test_polling_sd`, `tests/test_reweight` |
| `polling.sd_components` | model+measurement | The same four numbers, unsummed, so they can be printed and traced. | `tests/test_polling_sd` |
| `polling.effective_houses` | model+measurement | Kish effective count of independent HOUSES, over recency weights. | `montecarlo`, `tests/test_polling_sd`, `tests/test_polling_synthetic` |
| `polling.weight_cap` | model+measurement | The most weight a poll may take, given how many houses stand behind it. | `montecarlo`, `tests/test_polling_sd`, `tests/test_polling_synthetic` |
| `polling.blend_weight` | model+measurement | Inverse-variance weight on the poll. The professional mechanism. | `montecarlo`, `tests/test_polling_synthetic` |
| `polling.load` | model+measurement | -- | `areas`, `arrivals`, `backtest`, `benchmarks`, `build_geo`, `build_interactive`, `build_play`, `build_portal`, `cityconfig`, `compare_history`, `diagnose`, `export_interactive`, `fetch_boundaries`, `fold`, `gamma_recent`, `inputs_preflight`, `montecarlo`, `pools`, `reader_seats`, `render_map`, `render_sheet`, `scenarios`, `score_forecasts`, `stats`, `sweep`, `tests/test_artefact_key_discriminates`, `tests/test_build_all`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_draw_record`, `tests/test_drawer`, `tests/test_inputs_preflight`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_reader_seats`, `tests/test_regressions`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scenarios`, `tests/test_scoreboard_disclosure`, `tests/test_served_draws`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_temporal`, `tests/test_unopposed`, `tests/test_ward_pr_ratios`, `theta_residual` |
| `polling.validate` | model+measurement | Every way a poll record is BROKEN, as opposed to inapplicable. | `tests/test_polling_register`, `validate_seats` |
| `polling.validate_or_die` | model+measurement | Load and validate, or raise. The entry point everything else uses. | `montecarlo`, `reweight`, `tests/test_polling_register` |
| `polling.screen` | model+measurement | Admitted polls, and every exclusion WITH ITS REASON. | `build_play`, `montecarlo`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_polling_sd`, `tests/test_reweight` |
| `polling.metro_polls` | model+measurement | The admitted polls that are a reading OF THIS CITY. One definition. | `reweight` |
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
| `pools.artefact_key` | model+measurement | What an emitted spec was built FROM, so staleness can be detected. | `build_make`, `citywide_table`, `declares`, `export_draws`, `freeze`, `montecarlo`, `tests/test_artefact_key_discriminates`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_export_draws`, `tests/test_prediction_rule`, `tests/test_provenance_gates`, `tests/test_served_draws`, `tests/test_stage_inputs` |
| `pools.stale_reason` | model+measurement | Why this spec should not be trusted for this run, or None. | `citywide_table`, `montecarlo`, `tests/test_artefact_key_discriminates`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_stage_inputs` |
| `pools.load_config` | model+measurement | -- | `montecarlo`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.read_census` | model+measurement | One census: ward -> composition over this dimension, summing to 1. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.read_census_population` | model+measurement | Ward -> the population this dimension's categories are counted over. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.vote_located_bloc` | model+measurement | Locate a voter bloc the census cannot see, using a party that only it votes for. | `tests/test_chain` |
| `pools.ward_totals` | model+measurement | Ward -> registered voters, and ward -> votes cast. Both published. | `benchmarks`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain` |
| `pools.pool_counts` | model+measurement | Build the four nested levels for one city and election. | `montecarlo`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.pool_losses` | model+measurement | Every city-year a pool record dropped since this process started. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.registration_series` | model+measurement | Each pool's share of the registered roll, at every election on disk. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.projected_pool_shares` | model+measurement | Carry each pool's share of the roll forward to the target election. | -- |
| `pools.vd_map` | model+measurement | VD -> ward, and VD -> registered voters, as at one election. | `levels`, `montecarlo`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates` |
| `pools.reproject` | model+measurement | Move a ward-level composition from one delimitation onto another. | -- |
| `pools.delimitation_for` | model+measurement | Which delimitation an election was fought on. | `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain` |
| `pools.reproject_counts` | model+measurement | Move a ward-level COUNT from one delimitation onto another. | `tests/test_chain` |
| `pools.composition_at` | model+measurement | Ward composition interpolated to a decimal year. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.polling_decimal_year` | model+measurement | Polling day as a decimal year, without demanding council structure. | -- |
| `pools.ward_party_shares` | model+measurement | Ward -> {party: share}, and ward -> votes cast. | -- |
| `pools.fit_joint` | model+measurement | Fit every party's pool rates at once, subject to what must be true. | `tests/test_chain` |
| `pools.balance_margins` | model+measurement | Force both margins of the party x pool vote matrix to their known totals. | `montecarlo`, `tests/test_pool_bounds` |
| `pools.balance_within_bounds` | model+measurement | :func:`balance_margins`, with the method of bounds as a third truth. | `tests/test_pool_bounds` |
| `pools.bounds` | model+measurement | Duncan-Davis method of bounds: what the arithmetic alone allows. | `build_interactive`, `build_make`, `export_interactive`, `tests/test_blended_centres`, `tests/test_pool_bounds` |
| `pools.fit_city` | model+measurement | Fit every party's pool vector from one city's ward results. | `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.metro_file` | model+measurement | -- | `contested_area`, `polling`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach` |
| `pools.metro_citywide` | model+measurement | One metro's citywide party shares, through the same cleaner the city | `tests/test_chain`, `tests/test_temporal` |
| `pools.turnout_record` | model+measurement | Turnout per pool at every prior election of one kind. | `montecarlo`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_draw_record` |
| `pools.turnout_band` | model+measurement | (low, mode, high) turnout per pool: last election, widened by history. | `tests/test_census_refusal_is_not_swallowed` |
| `pools.panel_turnout_spread` | model+measurement | How far EACH pool's turnout moves between local elections, panel-wide. | `tests/test_census_refusal_is_not_swallowed`, `tests/test_pool_bounds` |
| `pools.turnout_limits` | model+measurement | What a reader may set turnout to, and the rule tying the two sliders. | `export_interactive` |
| `pools.constrain_pool_turnout` | model+measurement | Project a reader's per-pool turnouts back inside the citywide range. | `tests/test_regressions` |
| `pools.registered_at_target` | model+measurement | How many registered voters each pool holds at the target. | -- |
| `pools.pool_totals` | model+measurement | Each pool's share of the total vote. | -- |
| `pools.lge_transitions` | model+measurement | Consecutive local-election pairs, optionally ending before a target. | `tests/test_chain` |
| `pools.measure_pool_ratios` | model+measurement | How much a pool's vote total moves between elections, IN ONE CITY. | `tests/test_chain` |
| `pools.dirichlet_alpha` | model+measurement | Method of moments: alpha + 1 = m(1-m)/Var, over members that matter. | -- |
| `pools.apply_mergers` | model+measurement | Move ``retention × predecessor`` to the partner on the ballot. | `montecarlo`, `tests/test_roster_aware_baseline`, `theta_residual` |
| `pools.merged_vector` | model+measurement | The successor's pool vector after a merger: the MASS-WEIGHTED blend. | `tests/test_roster_aware_baseline` |
| `pools.blend_merger_vectors` | model+measurement | Blend each applied merger's predecessor vector into its successor's. | `tests/test_roster_aware_baseline` |
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
| `pools.lineage_path` | model+measurement | -- | `tests/test_artefact_key_discriminates`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates`, `tests/test_pool_bounds`, `tests/test_prior_local_fails_closed` |
| `pools.declared_roster` | model+measurement | A nomination list declared by hand, from `[roster]` in the judgement file. | `levels`, `score_forecasts`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_roster_aware_baseline`, `tests/test_unopposed` |
| `pools.load_lineage` | model+measurement | -- | `tests/test_chain` |
| `pools.write_lineage_template` | model+measurement | Ask for the judgements the model cannot make, with defaults filled in. | `tests/test_pool_bounds` |
| `pools.city_mix_for` | model+measurement | The city's own pool composition — where this city's votes actually are. | -- |
| `pools.resolve_roster` | model+measurement | Who is on the ballot at ``target``, and who may be deleted from the pools. | `tests/test_chain`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration` |
| `pools.emit_pools` | model+measurement | Build the ``scenario["pools"]`` structure from measurement. | `tests/test_chain`, `tests/test_pool_bounds` |
| `pools.gate` | model+measurement | Fit on one city, predict another, and see whether a tilt helped. | `build_site`, `edit_mode`, `model_index`, `tests/test_levers_are_live` |
| `prediction.top_party` | model+measurement | The party with the largest score; a tie drawn by the seeded lot. | `benchmarks`, `diagnose`, `montecarlo`, `scenarios`, `score`, `tests/test_prediction_rule`, `tests/test_served_draws` |
| `prediction.ward_calls` | model+measurement | ``{ward: party}``: each ward's party with the most (weighted) wins. | `build_make`, `reader_seats`, `score_forecasts`, `tests/test_chain`, `tests/test_entries`, `tests/test_prediction_rule`, `tests/test_rank_entries`, `tests/test_score_forecasts`, `tests/test_your_forecast_page` |
| `prediction.mean_votes` | model+measurement | ``{party: whole votes}``: each column's mean over the draws (module docstring). | `tests/test_prediction_rule` |
| `prediction.rule_a` | model+measurement | The prediction object: rule A on the draws (module docstring). | `score_forecasts`, `tests/test_export_draws`, `tests/test_prediction_rule`, `tests/test_your_forecast_page` |
| `prediction.seats_of` | model+measurement | The council the seat law gives a prediction: the one composition of | `build_make`, `reader_seats`, `tests/test_chain`, `tests/test_export_draws`, `tests/test_prediction_rule`, `tests/test_score_forecasts`, `tests/test_your_forecast_page` |
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
| `score.score_wards` | measurement | Everything ward-shaped in one call: Brier, reliability table, hit rate. | `backtest`, `benchmarks`, `compare_history`, `tests/test_prediction_rule` |
| `score.energy_score` | measurement | Energy score of the *joint* seat vector. **Lower is better.** | `tests/test_scored_universe` |
| `score.variogram_score` | measurement | Variogram score of order p on the joint seat vector. **Lower is better.** | `tests/test_scored_universe` |
| `score.score_seats` | measurement | Score a seat forecast end to end. Returns a dict; see :func:`format_report`. | `backtest`, `benchmarks`, `compare_history`, `tests/test_chain`, `tests/test_panel_wiring`, `tests/test_regressions`, `tests/test_scored_universe` |
| `score.format_report` | measurement | Human-readable block for a :func:`score_seats` / :func:`score_wards` pair. | `backtest`, `benchmarks`, `tests/test_regressions` |
| `seats.lot_identity` | model+measurement | The run's identity for the lot: ``f"{city}|{target}|{seed}"``. | `backtest`, `benchmarks`, `build_make`, `montecarlo`, `scenarios`, `score_forecasts`, `tests/test_export_draws`, `tests/test_prediction_rule`, `tests/test_roster_aware_baseline`, `tests/test_seats`, `tests/test_served_draws`, `validate_seats` |
| `seats.ward_key` | model+measurement | The key for a tied ward call: ``f"{lot}|ward|{ward}"``. | `benchmarks`, `diagnose`, `montecarlo`, `prediction`, `scenarios`, `score`, `tests/test_prediction_rule`, `tests/test_score_forecasts`, `tests/test_seats`, `tests/test_served_draws` |
| `seats.draw_key` | model+measurement | The run identity of draw ``d``: ``f"{lot}|draw{d}"``. Seat keys inside | `benchmarks`, `montecarlo`, `tests/test_chain`, `tests/test_reader_seats`, `tests/test_seats` |
| `seats.seat_key` | model+measurement | The key for an exact tie at the last seat in allocation round | `montecarlo`, `tests/test_seats` |
| `seats.lot_order` | model+measurement | The tied codes in the order the lot draws them, for ``key``. | `prediction`, `tests/test_prediction_rule`, `tests/test_roster_aware_baseline`, `tests/test_score_forecasts`, `tests/test_seats`, `tests/test_stage_realisation` |
| `seats.eligible_parties` | model+measurement | Return combined ward+PR votes for parties that count towards the quota. | `backtest`, `benchmarks`, `fold`, `montecarlo`, `prediction`, `tests/test_export_draws`, `tests/test_seats`, `tests/test_stage_realisation`, `tests/test_unopposed`, `validate_seats` |
| `seats.outside_pool_wards` | model+measurement | Split ward wins into the entitlement pool and the C and D terms. | `benchmarks`, `montecarlo`, `prediction`, `tests/test_seats` |
| `seats.allocate` | model+measurement | Allocate council seats by the Schedule 1 quota-and-highest-surplus method. | `backtest`, `fold`, `montecarlo`, `tests/test_overhang`, `tests/test_roster_aware_baseline`, `tests/test_seats`, `tests/test_stage_realisation`, `tests/test_unopposed`, `validate_seats` |
| `seats.pr_seats` | model+measurement | Split each party's entitlement into ward and PR councillors. | `tests/test_seats` |
| `seats.overhang` | model+measurement | Return the parties whose ward wins exceed their entitlement, and by how much. | `tests/test_seats` |
| `turnout.read_turnout` | model+measurement | Return VD -> (registered, votes cast). | `fold` |
| `turnout.turnout_series` | model+measurement | Return election -> VD -> turnout, plus the citywide figure per election. | -- |
| `turnout.citywide` | model+measurement | -- | `arrivals`, `backtest`, `benchmarks`, `build_concordance`, `compare_history`, `diagnose`, `export_interactive`, `fold`, `gamma_recent`, `montecarlo`, `pools`, `tests/test_chain`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_pool_bounds`, `tests/test_roster_aware_baseline`, `tests/test_ward_pr_ratios` |

## 8 · Modules

| module | path | entry point | importers | summary |
|---|---|---|---|---|
| `archive` | neither | NO | `tests/test_data_coverage` | Inventory every raw input with a checksum and its provenance. |
| `areas` | neither | NO | `src/render_sheet`, `tests/test_areas` | Named groups of a city's wards, generated from raw files and checked. |
| `arrivals` | neither | yes | -- | Every party that arrived from nothing, and what the model said about it. |
| `backtest` | measurement | NO | `src/arrivals`, `src/benchmarks`, `src/compare_history`, `src/diagnose`, `src/sweep`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_levers_are_live`, `tests/test_panel_wiring`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_scoreboard_disclosure`, `tests/test_stage_inputs` | Score the forecast model against an election that has already happened. |
| `backup_ignored` | neither | yes | -- | Back up every gitignored file, because git will not. |
| `benchmarks` | measurement | NO | `src/compare_history`, `src/diagnose`, `tests/test_covariate_fail_open`, `tests/test_diagnose_baselines`, `tests/test_roster_aware_baseline`, `tests/test_scoreboard_disclosure` | Naive forecasters, so the model has something to beat. |
| `build_all` | neither | NO | `tests/test_build_all` | Build one city end to end, then the site around it. |
| `build_concordance` | neither | NO | `tests/test_ward_parts` | Build the VD concordance and the VD -> 2026 ward apportionment (plan §2, steps 2 and 5). |
| `build_crosswalk` | neither | yes | -- | Build and check the party crosswalk across every source file. |
| `build_geo` | neither | yes | -- | Extract the CoJ subsets from the downloaded boundaries and check them. |
| `build_interactive` | neither | yes | -- | Assemble forecast-interactive.html from the template and the data packs. |
| `build_leaderboard` | neither | NO | `src/build_site`, `tests/test_rank_entries` | Build ``/leaderboard/``: every sealed forecast ranked against the result. |
| `build_make` | neither | NO | `src/build_your_forecast`, `tests/test_prediction_rule`, `tests/test_share`, `tests/test_worker_routing`, `tests/test_your_forecast_page` | Section 2 of "your forecast" ("Break the model"): its data and its start. |
| `build_play` | neither | NO | `src/build_make`, `src/build_site`, `src/build_your_forecast`, `tests/test_seat_table`, `tests/test_share`, `tests/test_site_structure`, `tests/test_worker_routing`, `tests/test_your_forecast_page` | Section 1 of "your forecast" ("Adjust the model"): its published figures. |
| `build_portal` | neither | NO | `src/build_site`, `src/site_assets`, `tests/test_build_all` | Build the portal at whysoserious.city — one card per city. |
| `build_site` | neither | NO | `src/build_portal`, `src/deploy_check`, `src/edit_mode`, `src/site_text`, `tests/test_edit_mode`, `tests/test_home_page`, `tests/test_number_scan`, `tests/test_provenance_dates`, `tests/test_publication_ledger`, `tests/test_published_page`, `tests/test_rank_entries`, `tests/test_site_assets`, `tests/test_site_headers`, `tests/test_site_structure`, `tests/test_stat_freshness`, `tests/test_your_forecast_page` | Build the public site (joburg.whysoserious.org) into ./site. |
| `build_validation` | neither | yes | -- | Run the validation across every metro and write the section that reports it. |
| `build_your_forecast` | neither | NO | `src/build_site`, `tests/test_edit_mode`, `tests/test_provenance_dates`, `tests/test_site_assets`, `tests/test_site_structure`, `tests/test_your_forecast_page` | Build "your forecast" (``/your-forecast/``) from ``interactive/`` into the site. |
| `byelections` | neither | yes | -- | By-election evidence for the target election (plan §3.6, §3.3 covariate). |
| `cityconfig` | model+measurement | NO | `src/areas`, `src/arrivals`, `src/backtest`, `src/benchmarks`, `src/build_all`, `src/build_concordance`, `src/build_crosswalk`, `src/build_geo`, `src/build_interactive`, `src/build_make`, `src/build_play`, `src/build_portal`, `src/build_site`, `src/byelections`, `src/citywide_table`, `src/coalitions`, `src/compare_history`, `src/diagnose`, `src/export_draws`, `src/export_interactive`, `src/fold`, `src/freeze`, `src/gamma_recent`, `src/iec_csv`, `src/ingest_historic`, `src/ingest_lge`, `src/ingest_npe`, `src/inputs_preflight`, `src/levels`, `src/montecarlo`, `src/polling`, `src/pools`, `src/publication`, `src/rank_entries`, `src/reader_seats`, `src/render_home`, `src/render_map`, `src/render_sheet`, `src/scenarios`, `src/score_forecasts`, `src/site_text`, `src/sweep`, `src/theta_residual`, `src/turnout`, `src/validate_seats`, `src/width_budget`, `tests/_support`, `tests/test_artefact_key_discriminates`, `tests/test_build_all`, `tests/test_calibration_report`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_covariate_fail_open`, `tests/test_data_coverage`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates`, `tests/test_drawer`, `tests/test_export_draws`, `tests/test_inputs_preflight`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_pool_bounds`, `tests/test_pool_conservation`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_dates`, `tests/test_provenance_gates`, `tests/test_publication_ledger`, `tests/test_reader_seats`, `tests/test_regressions`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_scoreboard_disclosure`, `tests/test_share`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_temporal`, `tests/test_theta_prior`, `tests/test_unopposed`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `tests/test_your_forecast_page` | The city and the target election are parameters, not assumptions. |
| `citywide_table` | neither | NO | `src/declares`, `tests/test_citywide_table` | The browser engine's stand-in for re-reading 65 election files. |
| `coalitions` | model+measurement | NO | `src/montecarlo` | Coalition arithmetic over Monte Carlo seat draws (plan §3.8). |
| `compare_history` | measurement | NO | `src/diagnose`, `tests/test_calibration_report`, `tests/test_diagnose_baselines`, `tests/test_panel_wiring`, `tests/test_pool_bounds`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_scoreboard_disclosure`, `tests/test_scored_universe`, `tests/test_temporal` | Every past election we can run, as votes and as seats, against every opponent. |
| `contested_area` | neither | yes | -- | Validate the contested-area conversion — the table `polling.py` asserted. |
| `declares` | neither | NO | `tests/test_export_draws`, `tests/test_provenance_gates` | Does every artefact declare what produced it? One table, at a glance. |
| `deploy_check` | neither | NO | `tests/test_edit_mode`, `tests/test_number_scan`, `tests/test_rank_entries`, `tests/test_your_forecast_page` | Refuse a Cloudflare deploy of a site whose numbers were not reviewed. |
| `derive_city` | neither | yes | -- | Propose a city's config from its own IEC files. |
| `diagnose` | neither | NO | `tests/test_diagnose_baselines`, `tests/test_scoreboard_disclosure` | One election, laid out so a fault can be ISOLATED rather than summarised. |
| `edit_mode` | neither | NO | `src/deploy_check`, `tests/test_edit_mode` | Edit the site's words on the site itself, locally, and write them back to |
| `export_draws` | neither | NO | `tests/test_export_draws`, `tests/test_served_draws` | Export the published run's draws for the interactive: one binary file and its manifest. |
| `export_interactive` | neither | yes | -- | Export the data pack for the interactive forecast page. |
| `fetch_boundaries` | neither | yes | -- | Download CoJ ward and voting-district boundaries from the MDB Spatial Knowledge Hub. |
| `fetch_byelections` | neither | yes | -- | Download every municipal by-election result since the 2021 LGE, at VD level. |
| `fetch_iec` | neither | yes | -- | Download every IEC report the model needs that is reachable without a browser. |
| `fold` | model+measurement | NO | `src/arrivals`, `src/backtest`, `src/benchmarks`, `src/compare_history`, `src/diagnose`, `src/export_interactive`, `src/gamma_recent`, `src/montecarlo`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_ward_pr_ratios` | Backtest a national/provincial baseline against a local-government target (plan §4). |
| `freeze` | measurement | NO | `src/compare_history`, `src/declares`, `src/export_draws`, `src/publication`, `tests/test_export_draws`, `tests/test_freeze`, `tests/test_provenance_gates` | Freeze a stage-1 forecast, and hash everything that could move it. |
| `gamma_recent` | neither | yes | -- | Fit γ on the last LGE→NPE transition for parties fold 1 never saw (review A4). |
| `hex_cartogram` | neither | NO | `tests/test_hex_cartogram`, `tests/test_home_page` | An equal-area hex tile cartogram: one hexagon per ward, one ward per hexagon. |
| `iec_csv` | model+measurement | NO | `src/derive_city`, `src/ingest_lge`, `src/ingest_npe` | Shared helpers for reading IEC result CSVs. |
| `ingest_historic` | neither | NO | `tests/test_data_coverage` | Ingest the pre-2011 IEC bulk archives into the project's canonical VD files. |
| `ingest_lge` | model+measurement | NO | `src/contested_area`, `src/polling`, `src/pools`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach` | Ingest IEC local-government election results to a JHB VD-level subset. |
| `ingest_npe` | neither | yes | -- | Ingest IEC national/provincial election bulk result files to a JHB VD-level subset. |
| `inputs_preflight` | neither | NO | `src/build_make`, `tests/test_inputs_preflight`, `tests/test_your_forecast_page` | Are the inputs for a forecast of THIS election actually in hand, and current? |
| `judgement_sheet` | neither | NO | `src/build_site`, `tests/test_judgement_sheet` | The judgement calls, laid out for a person rather than for a grep. |
| `levels` | model+measurement | NO | `src/backtest`, `src/citywide_table`, `src/compare_history`, `src/contested_area`, `src/freeze`, `src/montecarlo`, `src/pools`, `src/theta_residual`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_data_coverage`, `tests/test_declared_ward_slates`, `tests/test_delivery_proof`, `tests/test_drawer`, `tests/test_ipf_feasibility`, `tests/test_levels_dispersion`, `tests/test_levers_are_live`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_spine`, `tests/test_stage_estimation`, `tests/test_temporal`, `tests/test_theta_prior`, `tests/test_unopposed`, `tests/test_ward_pr_ratios` | How big each party will be, measured instead of typed. |
| `model_index` | neither | NO | `src/judgement_sheet`, `tests/test_judgement_sheet`, `tests/test_model_index` | One index of every lever, constant, fold, window and method, JOINED. |
| `montecarlo` | model+measurement | NO | `src/areas`, `src/arrivals`, `src/backtest`, `src/benchmarks`, `src/build_make`, `src/build_validation`, `src/citywide_table`, `src/compare_history`, `src/diagnose`, `src/export_draws`, `src/export_interactive`, `src/freeze`, `src/overhang_regimes`, `src/pools`, `src/prediction`, `src/reader_seats`, `src/reweight`, `src/stats`, `src/sweep`, `src/theta_residual`, `src/width_budget`, `tests/run_all`, `tests/test_blended_centres`, `tests/test_calibration_report`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_citywide_table`, `tests/test_declared_ward_slates`, `tests/test_delivery_proof`, `tests/test_draw_record`, `tests/test_drawer`, `tests/test_export_draws`, `tests/test_freeze`, `tests/test_ipf_feasibility`, `tests/test_levers_are_live`, `tests/test_overhang`, `tests/test_pool_conservation`, `tests/test_prediction_rule`, `tests/test_projected_roster_declaration`, `tests/test_reader_seats`, `tests/test_regressions`, `tests/test_reweight`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_roster_universe`, `tests/test_scoreboard_disclosure`, `tests/test_seats`, `tests/test_solve_and_predict`, `tests/test_stage_estimation`, `tests/test_stage_inputs`, `tests/test_stage_realisation`, `tests/test_stat_freshness`, `tests/test_unopposed`, `tests/test_ward_parts`, `tests/test_ward_pr_ratios`, `tests/test_your_forecast_page` | Monte Carlo forecast of a metro council (plan §3.4–§3.8, review fixes). |
| `official_seats` | measurement | NO | `src/backtest`, `src/build_crosswalk`, `src/build_make`, `src/rank_entries`, `src/validate_seats`, `tests/test_score_forecasts`, `tests/test_seats` | Read the IEC's own Seat Calculation Detail as the validation ground truth. |
| `overhang_regimes` | neither | yes | -- | Run the excessive-seats counterfactuals for the regime-comparison table. |
| `parties` | model+measurement | NO | `src/backtest`, `src/build_crosswalk`, `src/build_make`, `src/build_play`, `src/byelections`, `src/contested_area`, `src/fold`, `src/ingest_historic`, `src/levels`, `src/pools`, `src/score_forecasts`, `tests/test_chain`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates`, `tests/test_delivery_proof`, `tests/test_your_forecast_page` | Party name normalisation: many ballot spellings, one code per party. |
| `polling` | model+measurement | NO | `src/build_play`, `src/contested_area`, `src/freeze`, `src/montecarlo`, `src/reweight`, `tests/test_delivery_proof`, `tests/test_levers_are_live`, `tests/test_polling_register`, `tests/test_polling_sd`, `tests/test_polling_synthetic`, `tests/test_reweight`, `tests/test_served_draws` | Polls, filtered by date and converted from national numbers to metro ones. |
| `pools` | model+measurement | NO | `src/benchmarks`, `src/citywide_table`, `src/compare_history`, `src/contested_area`, `src/declares`, `src/levels`, `src/montecarlo`, `src/polling`, `src/score_forecasts`, `src/theta_residual`, `tests/run_all`, `tests/test_artefact_key_discriminates`, `tests/test_census_refusal_is_not_swallowed`, `tests/test_chain`, `tests/test_covariate_fail_open`, `tests/test_declared_reach_matches_ward_reach`, `tests/test_declared_ward_slates`, `tests/test_delivery_proof`, `tests/test_panel_wiring`, `tests/test_pool_bounds`, `tests/test_prior_local_fails_closed`, `tests/test_projected_roster_declaration`, `tests/test_provenance_gates`, `tests/test_regressions`, `tests/test_roster_aware_baseline`, `tests/test_roster_fails_closed`, `tests/test_stage_inputs`, `tests/test_temporal`, `tests/test_unopposed`, `tests/test_ward_parts` | Voter pools: what a party talks to, measured rather than asserted. |
| `prediction` | model+measurement | NO | `src/benchmarks`, `src/build_make`, `src/diagnose`, `src/montecarlo`, `src/reader_seats`, `src/scenarios`, `src/score`, `src/score_forecasts`, `tests/test_chain`, `tests/test_export_draws`, `tests/test_prediction_rule`, `tests/test_score_forecasts`, `tests/test_served_draws`, `tests/test_your_forecast_page` | Our prediction: the forecast reduced to one complete result, by rule A. |
| `prep_logos` | neither | yes | -- | Normalise party logos into consistent square badges. |
| `publication` | neither | NO | `src/build_site`, `src/export_draws`, `tests/test_export_draws`, `tests/test_provenance_dates`, `tests/test_publication_ledger`, `tests/test_served_draws` | The publication ledger: what this page said, when, and which model said it. |
| `rank_entries` | neither | NO | `tests/test_rank_entries` | Results night: rank every sealed forecast against the result (owner, 2026-10-03). |
| `reader_seats` | neither | NO | `src/score_forecasts`, `tests/test_reader_seats` | A reader's prediction, turned into council seats by the statute alone. |
| `render_home` | neither | NO | `src/build_site`, `tests/test_home_page` | Fill the home page's generated regions from the run that produced them. |
| `render_map` | neither | NO | `src/build_play`, `src/hex_cartogram`, `tests/test_hex_cartogram`, `tests/test_home_page`, `tests/test_map_stripes`, `tests/test_your_forecast_page` | Render the ward-winner map into the forecast pages. |
| `render_sheet` | neither | NO | `src/build_play`, `src/render_home`, `src/site_assets`, `tests/test_published_page`, `tests/test_site_assets`, `tests/test_site_structure`, `tests/test_your_forecast_page` | Regenerate forecast-sheet.html's data block from the model outputs. |
| `reweight` | neither | NO | `src/build_make`, `src/build_play`, `src/export_draws`, `src/render_home`, `src/render_sheet`, `src/stats`, `tests/test_export_draws`, `tests/test_prediction_rule`, `tests/test_reader_seats`, `tests/test_reweight`, `tests/test_served_draws`, `tests/test_your_forecast_page` | Re-weight the published draws: the interactive's engine, and the draw file's format. |
| `scenarios` | neither | NO | `src/render_home`, `src/render_map`, `src/render_sheet`, `tests/test_home_page`, `tests/test_prediction_rule`, `tests/test_scenarios` | Which simulations make a scenario, and what their wards did. |
| `score` | measurement | NO | `src/backtest`, `src/benchmarks`, `src/compare_history`, `tests/test_calibration_report`, `tests/test_chain`, `tests/test_panel_wiring`, `tests/test_prediction_rule`, `tests/test_regressions`, `tests/test_scored_universe` | Proper scoring rules for a distributional forecast of a council. |
| `score_forecasts` | neither | NO | `src/build_make`, `src/rank_entries`, `tests/test_entries`, `tests/test_prediction_rule`, `tests/test_rank_entries`, `tests/test_score_forecasts`, `tests/test_your_forecast_page` | Score ANY forecast of a council — the model's and every reader's — against the |
| `seat_table` | neither | NO | `src/build_make`, `src/build_play`, `src/render_home`, `src/render_sheet`, `tests/test_seat_table` | The seat table: ONE component for every list of party seats on the site. |
| `seats` | model+measurement | NO | `src/backtest`, `src/benchmarks`, `src/build_make`, `src/diagnose`, `src/fold`, `src/levels`, `src/montecarlo`, `src/prediction`, `src/reader_seats`, `src/scenarios`, `src/score`, `src/score_forecasts`, `src/validate_seats`, `tests/test_chain`, `tests/test_export_draws`, `tests/test_overhang`, `tests/test_prediction_rule`, `tests/test_reader_seats`, `tests/test_roster_aware_baseline`, `tests/test_score_forecasts`, `tests/test_seats`, `tests/test_served_draws`, `tests/test_stage_realisation`, `tests/test_unopposed` | Seat allocation for a metro council, per Municipal Structures Act Schedule 1. |
| `site_assets` | neither | NO | `src/build_portal`, `src/build_site`, `src/deploy_check`, `tests/test_edit_mode`, `tests/test_site_assets`, `tests/test_site_structure` | The site's one stylesheet and its scripts, and the gate that keeps them out |
| `site_text` | neither | NO | `src/edit_mode`, `tests/test_edit_mode`, `tests/test_site_text` | Export the site's editable prose to one markdown file, and apply it back. |
| `stats` | neither | NO | `src/build_interactive`, `src/build_site`, `src/edit_mode`, `src/render_home`, `src/render_sheet`, `src/scenarios`, `src/site_text`, `tests/test_home_page`, `tests/test_judgement_sheet`, `tests/test_number_scan`, `tests/test_provenance_dates`, `tests/test_publication_ledger`, `tests/test_published_page`, `tests/test_rank_entries`, `tests/test_reweight`, `tests/test_site_structure`, `tests/test_stat_freshness`, `tests/test_your_forecast_page` | The stat registry: no model result is ever typed into prose by hand. |
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
| `DEFAULTS` | `montecarlo` | `test_blended_centres`, `test_census_refusal_is_not_swallowed`, `test_chain`, `test_drawer`, `test_freeze`, `test_ipf_feasibility`, `test_judgement_sheet`, `test_levers_are_live`, `test_model_index`, `test_overhang`, `test_pool_conservation`, `test_regressions`, `test_reweight`, `test_scoreboard_disclosure`, `test_solve_and_predict`, `test_stage_inputs`, `test_stat_freshness` |
| `DELETED` | `test_register_matches_code` | `test_judgement_sheet`, `test_model_index`, `test_register_matches_code` |
| `ENTRY_POINTS` | `test_standalone_modules` | `test_model_index`, `test_standalone_modules` |
| `ENV_SWITCHES` | `freeze` | `test_freeze` |
| `EXPECTED_INERT` | `test_levers_are_live` | `test_levers_are_live` |
| `FITTED_ON` | `backtest` | `test_chain`, `test_levers_are_live`, `test_scoreboard_disclosure`, `test_stage_inputs` |
| `FITTED_ON_UNINSTRUMENTED` | `backtest` | `test_levers_are_live`, `test_scoreboard_disclosure`, `test_stage_inputs` |
| `FOLDS` | `fold` | `test_regressions` |
| `GATES` | `test_levers_are_live` | `test_citywide_table`, `test_levers_are_live` |
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
