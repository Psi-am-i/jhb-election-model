# Judgement calls — what in these results is not from the record

Every number in this model is meant to be measured or declared. This is the list
of the **declared** ones: choices a person made that the data did not force. It
exists so that "the model measures its constants" can be audited rather than
believed.

Not to be confused with `judgements/<city>-<target>.toml`, which is the
*per-party* lineage and support file a forecaster fills in per city. This is the
register of **structural** calls in the code.

Status: 🔴 wants a second opinion · 🟡 defensible, bounded by evidence ·
🟢 forced by arithmetic or by an identity · ⚪ superseded or resolved ·
⚫ deleted or refused

## How to read this file

**RESTRUCTURED 2026-08-31. Nothing was re-judged: no value, status marker or
confidence colour was changed, and no history was deleted.** What changed is the
shape. Single table cells had grown to thousands of characters carrying five and
six dated amendments in sequence, so the *current* state of a constant could not
be read without parsing a paragraph of its history — and in three sections the
rows had more cells than the table header declared, which meant a renderer
silently dropped the last column and **the status marker was invisible** on
`SD_FLOOR`, `LEVEL_FLOOR`, `BLEND_W`, `FRESHNESS_GRACE_S`, `CELL_AREA_FACTOR`,
`REG_DRIFT_TOLERANCE` and eleven others. Three further rows carried an unescaped
`|` inside their prose and spilled across phantom columns.

So:

1. **The register below is the index.** One row per call: value, where it lives,
   its state *today* in one line, its status, and the entry that holds the
   detail. Read this to find something; read nothing else to find something.
2. **Sections A–I are the entries.** Each is `**Where**` · `**Now**` ·
   `**Record**, and where a call has been amended the record is a numbered chain
   in date order rather than one paragraph. `**Now**` is a summary of what the
   entry already says; where the entry no longer supports a single current
   reading, `**Now**` says so instead of inventing one.
3. **A finding belongs in `MODEL-LOG.md`, not here.** Entries cite §-numbers
   rather than restating the measurement.
4. ⚠️ **Eight entries carry a dated *restructure note*.** Each records a
   contradiction or a stale citation found while reorganising, left **unfixed**
   because fixing it is a judgement: §A4, §A7, §A21, §C3, §F21, §F29, §H10, §H16.

The section letters and their meanings are unchanged, because `MODEL-LOG.md`,
`MACHINERY.md` and `DATA-QUALITY.md` cite them. §E has been moved back into
alphabetical order; it was between §G and §H.

### The two guards

* `tests/test_register_matches_code.py::test_every_symbol_the_register_names_exists`
  — the **register → code** direction, which nothing checked before, and which
  is how `polling_lean`/`polling_span` sat here marked *"still wired"* for days
  after they were deleted.
* `tests/test_register_matches_code.py::test_the_register_cites_no_line_numbers`
  — so this cannot be reintroduced.

`test_every_tunable_constant_is_in_the_judgement_register` remains the **code →
register** direction. Both are needed; either alone passes while the register
lies. To find a constant, grep for its name:

    grep -n 'LEVEL_DF\|DIRICHLET_FLOOR\|entrant_prob' src/*.py

---

## The register

Every call, its value, and where it stands today. `+ §X` in the last column
means the same constant has a second entry — usually a range in §G or a
promotion note in §F.

### Named constants

| constant | value | where | current state | status | entry |
|---|---|---|---|---|---|
| `_LOG_FLOOR` | 1e-6 | `pools.py` | Unexercised and kept deliberately: every dimension declares exactly one census, so the branch never runs. A flat sweep of it is not a null about the value. | 🟡 | §A31 |
| `_SIGN_EPS` | 1e-9 | `theta_residual.py` | 1e-9, and it decides one of KEY 4's two failure triggers: six orders above the float dust a genuine no-op produced and six below the smallest real effect on record. | 🟡 | §F7 |
| `ALPHA_MIN_SHARE`, `ALPHA_FLOOR`, `ALPHA_CEILING`, `ALPHA_FALLBACK` | 0.01, 1.0, 200.0, 12.0 | `pools.dirichlet_alpha` | Promoted from inline literals 2026-08-22, number-neutral. They are the SELECTION RULE feeding the dominant width lever, and none has ever been swept. | 🔴 | §F31 |
| `alpha` per pool (and `dirichlet_scale`) | — | `pools.dirichlet_alpha` | The model's DOMINANT width lever, sweepable since §1.63 via `dirichlet_scale` and NOT retuned — the method-of-moments fit names 1.0. The ranks 4-12 half of the old 'a scalar cannot serve both bands' finding is WITHDRAWN. | 🟡 | §B7 |
| `apply_city` never resets `DEFAULTS` | — | `montecarlo.py` | Still true; harmless only while Johannesburg's sixteen scalars equal `DEFAULTS`, and guarded by a test that fails the moment they diverge. | 🔴 | §A43 |
| `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` | 0.25, 0.95 | — | 0.25 / 0.95, the triangular support of every seeded arrival. 25/95 rather than 10/90 or 5/95 is undefended and never swept. | 🔴 | §F32 |
| `arrival_group_draw` | False | `montecarlo.py`, read in `make_drawer` | Ships False. The rejection was re-run on the label-free referee 2026-08-29 and refuted again; the 254 → 348 figure is superseded and must not be quoted. | 🟢 | §A6 |
| `balance_margins` `iters` / `tol` | 2000 / 1e-12 | `pools.py` | 2000 / 1e-12. Nominally operational; registered because the cap is what turns an infeasible problem into an exception. 20,000 iterations move the failure rate 40.9% → 38.9%. | 🟡 | §F10 |
| `beta` | 1.0 | `score.energy_score` | 1.0. It is part of what "better" means, so `ITERATING.md` is arguably its proper home. | 🔴 | §H14 |
| `BINS` | 5 size bands | `theta_residual.py` | The size bands behind §1.59/§1.77. The '≥15% of the vote' cut this register quotes as though it were natural is a CHOSEN threshold. | 🔴 | §H15 |
| `BLEND_W` | 1.0 | `benchmarks.py`, `blended_swing` | 1.0, fitted leave-one-city-year-out to the boundary of the family: the optimal blend IS uniform swing. The one constant here legitimately fitted on the scoreboard, because it touches no forecast. | 🟢 | §D9 |
| `bye_local_cap`, `bye_tau_months` | 1.5, 18 | — | 1.5 / 18, inert in every backtest. | 🔴 | §F24 |
| `BYE_MIN_WEIGHT` | 30.0 | — | 30.0, the admission gate on the WHOLE by-election channel, promoted from a bare literal. Same reach into the published forecast, same untestability, same status as `w_bye`. | 🔴 | §F33 |
| `bye_weight_mode` | `"fixed"` | `montecarlo.py` | Defaults to `fixed`. `inverse_variance` is built and derives the weight; switching it moves the published 2026 forecast and no backtest can score either — the owner's call. | 🟡 | §A33 |
| `CAMPAIGN_WINDOW_DAYS` | 550 | — | 550, typed. | 🟡 | §F4 |
| `CELL_AREA_FACTOR` | — | `hex_cartogram.py` | Typed at 1.0. ARGUED, NOT TESTED, and a trade between two goods rather than right against wrong. Touches no forecast. | 🟡 | §D17 |
| `independent_wards` (C) in the forecast | 0, structurally | `montecarlo.run_model` | The forecast universe drops INDEPENDENT/IND, so no draw can seat an independent and C is always 0. The IEC records C=1 at eThekwini 2011 and C=4 at 2016, both SCORED — the model allocates those seats to parties and is charged for it. An ASSUMPTION, not a measurement; registered 2026-09-02 after being silent. | 🔴 | §1.166 |
| `CENSUS_COVERAGE_FLOOR` | 0.80 | `pools.py` | A WARNING in `pool_counts` and a REFUSAL in `registered_at_target`, on different denominators. Measured 2026-09-02: 0.9609-0.9979 at the refusal, so it binds nowhere and has never been exercised. The §J2 argument applies to it and has not been applied. | 🔴 | §J1 |
| `CENSUS_DRIFT_CEILING` | 0.05 | `pools.pool_counts` | The reprojection refusal: how far the CITYWIDE composition moves because of unmappable wards. Bounded by ablation (worst random loss 0.028, segregated loss ~0.28) on one city only. | 🟡 | §J2 |
| `contestation_expand` | 0.220 | `montecarlo.py`, applied in `levels.projected_cont… | Ships 0.220, live only where no backtest can reach it; superseded automatically the day the IEC publishes 2026 lists. | 🔴 | §A5 |
| `DIRICHLET_FLOOR` | 1e-4 | — | 1e-4 and inert as committed — but it has a SECOND consumer that floors a CONCENTRATION rather than a mean, and `PERTURB` sweeps it to 0.05 where that would bind. | 🟢 | §F1 |
| `dirichlet_floor`, `spine_k` (scenario keys) | — | — | Scenario keys mirroring the module constants so a sweep is reproducible. ⚠ This row also lists `poll_k`, which was DELETED on 2026-08-22 (§1.68) and is in no `DEFAULTS` — see the restructure note beneath. | 🟢 | §F21 |
| `entrant_prob` | 0.25 | `montecarlo.py` | Ships 0.25. Typed, but measurable since 2026-08-17 and the typed value survives the measurement; §G-R2 puts the defensible range at [0.25, 0.29]. | 🟡 | §A3 |
| `entrant_share` | `[0.01, 0.04, 0.12]` | `montecarlo.py` | Unchanged at [0.01, 0.04, 0.12]; with `entrant_prob` it puts an expected 1.42% of the vote on a generic newcomer in every run. | 🟡 | §A17 |
| `extrapolation_damping` | 0.6 | `config/dimensions.toml` | 0.6, and typed three more times as a fallback in `pools.py`. | 🔴 | §H8 |
| `extrapolation_max_years` / `max_extrapolation` | 8 / 8.0 | `dimensions.toml`, `pools.Config` | 8 / 8.0 — two copies of one number, one in TOML and one as a dataclass field. | 🔴 | §H9 |
| `FRESHNESS_GRACE_S` | — | `stats.py`, `freshness_problems` | Typed at 300s. ARGUED, NOT TESTED — the harness cannot score a publishing guard; the strong half of the check catches the 16-day defect with no window at all. | 🟡 | §D16 |
| `GAMMA_FOLD` | `{2026:1, 2021:1, 2016:3, 2011:4}` | `montecarlo.py` | The live 2026 forecast uses fold 1, and the code's own comment concedes the constraint does not pick one. A contestable choice on the published forecast. | 🔴 | §H6 |
| `GRID_MARGIN_CELLS` | — | `hex_cartogram.py` | Typed at 2 and purely operational: the Johannesburg optimum uses no cell in the outermost ring. | 🟢 | §D18 |
| `kappa_bye` | 0.25 | `turnout.py --kappa-bye` | 0.25. Same provenance and the same artefact problem as `w_recency`. | 🔴 | §H3 |
| `LEVEL_DF` | 7.0 | `montecarlo.py` | Ships 7.0, live since 2026-08-17 and swept. The sweep cannot distinguish 7 from 30; §F narrows it to ν ∈ [5, 15] on four constraints. | 🟡 | §A18 + §F8 |
| `LEVEL_DF` | 7.0 | — | BOUNDED 2026-08-29 to ν ∈ [5, 15] on four constraints, with the committed 7.0 in the middle. The honest label is no longer 'unmeasured' but 'not resolvable further on this panel'; a joint (κ, ν) fit was designed and NOT built. | 🟡 | §F8 + §A18 |
| `level_floor` | 1e-6 | — | 1e-6; separates the level floor from the deviation floor. | 🟢 | §F19 |
| `LEVEL_FLOOR` vs `SHARE_FLOOR` | — | `fold.py` | Two separate floors, deliberately. On its own it fixed nothing — the 42 phantom seats were the scale drift above it. | 🟢 | §C4 |
| `level_sd_default` | 0.45 | `montecarlo.py` | Declared in `DEFAULTS` since §1.63 and MEASURED inert: perturbed to 1.60 the output is byte-identical, because `theta_prior` gives every party in the baseline an sd. | 🟡 | §A29 |
| `level_shrink` (and `level_shrink_scale`) | 0.35 | `montecarlo.compress_levels`, run on the finished… | Adopted 2026-08-17 and unchanged; the largest single improvement this model has had. Two things keep it off green: an L1 form-selection leak, and a tail the uniform renormalisation over-feeds. | 🟡 | §A23 + §F20 |
| `level_shrink`, `level_shrink_scale` | 0.35, 0.04 | — | See §A. The scale is a SCALE, not a tuned constant — swept twentyfold with no cliff. | 🟡 | §F20 + §A23 |
| `LOG_CHI2_BIAS` | — | `levels.py`, documented and deliberately unused | Correct, derived, and DELIBERATELY NOT APPLIED: applying it makes the model worse on every metric, because the record it reproduces is marginal and this layer is conditional. | 🟢 | §C5 |
| `MAX_DISPLACEMENT_RADII` | — | `tests/test_hex_cartogram.py` | Typed at 5.0 radii — a regression guard rather than a claim, and it separates the optimal assignment (3.8) from the greedy one (8.8). | 🟡 | §D21 |
| `max_parties` | 12 | `coalitions.analyse` | 12. Operational in flavour, but it silently truncates the coalition space if a council ever seats more than twelve parties — which the 2026 ballot could. | 🔴 | §H13 |
| `MAX_SIGMA`, `MIN_SIGMA`, `NEW_PARTY_SIGMA` | 2.0, 0.15, 1.0 | — | Spread bounds for the `prior-lge-noise` BASELINE, not for the model. | 🟡 | §F28 |
| `METRO_CODES` widened 2 → 8 | — | `levels.py` | Eight metros. More evidence and no leakage, but it moves θ itself, so it is confounded with the spine in any before/after delta. | 🟡 | §B6 |
| `MIN_HOME_SPLITS` and the binary home/away | 2 | `pools.py` | Unchanged: a measured gradient (0.611 / 0.315 / 0.289 / 0.103) modelled as two buckets. | 🔴 | §A44 |
| `min_oos_gain` | 0.01 | `config/dimensions.toml` | 0.01, and it is upstream of every pool in the model: age and sex are rejected by this number. | 🔴 | §H7 |
| `MIN_SHARE`, `CLAIM_FRACTION`, `F_OTHER` | 0.005, 0.50, 1.30 | — | All three were filed under the wrong module once. `MIN_SHARE` is `gamma_recent.py`'s and is a CLAIM about the model, not reporting; `CLAIM_FRACTION` is `score.py`'s. ⚠ `F_OTHER` is no longer in `src/` at all — see the restructure note beneath. | 🟡 | §F29 |
| `OVERHANG_DEDUCT_MAX_ROUNDS_SLACK` | 2 | `montecarlo.py` | Derived, not chosen: any value ≥ 1 is equivalent. | 🟢 | §A39 |
| `OVERHANG_LEVEL_MAX_ROUNDS` | 200 | `montecarlo.py` | 200 rounds. Bounded on ROUNDS deliberately rather than on council size, because a magnitude off the real panel does not transfer to a toy. | 🟡 | §A40 |
| `NATIONAL_ONLY_FLOOR` | 0.001 | `pools.py` | The national share below which a party with no local record is NOT assumed onto an unheld ballot. Measured over 16 city-years: drops 158 of 226 such candidates for 0.10pp of vote. MK (12.2%) clears it. Owner's decision 2026-09-03; unreachable from any backtest. | 🟢 | §K1 |
| `PRIOR_LOCAL_FLOOR` | 0.001 | `pools.py` | The prior-LOCAL share below which a party with no national vote is not assumed onto an unheld ballot. Drops 112 of 189 such candidates for 0.038pp and ZERO seats. ⚠️ INERT until entry 3 lets a projected roster drive the off-ballot drop. | 🟢 | §K2 |
| `overhang_rule` | `"deduct"` | `montecarlo.DEFAULTS` | ⚖️ **STATUTE, reclassified 2026-09-02** — Act 3 of 2021 Schedule 1 item 16. NOT a lever and never swept: refused at the `--set` boundary, out of `PERTURB`. Never bound in 24 metro-years; tightest margin 2 seats. | ⚖️ | §H1 |
| `pa_contestation_uplift` | DELETED 2026-08-18 | — | DELETED 2026-08-18. The branch now falls back to the previous local election's measured contestation for every party, which makes it backtestable. | ⚪ | §F27 |
| `PAGE_SIZE` | — | — | Pagination. Reporting, not belief. | 🟢 | §F37 |
| `PARTIAL_BALANCE_PASSES` | 200 | — | 200. A convergence budget that is not a converging sequence, so the number chooses how close to the boundary it gets. | 🟡 | §F12 |
| `PLAN_BOUNDS` | 7 party ranges | `montecarlo.py` | Present for four of the sixteen panel city-years and absent for twelve, because six of eight metro configs have no `[judgements]` block — which makes the headline seat figure a mixture of two configurations. | 🔴 | §H5 |
| `poll_credence` | 1.0 | `montecarlo.DEFAULTS` → the metro-poll blend | Declared at 1.0, which is the identity, so it moves nothing. The value the backtest supports is UNMEASURED — the paired sweep is pre-registered and not run. | 🔴 | §A11 |
| `poll_deff_subsample` | 1.6 (standalone 1.2) | `montecarlo.DEFAULTS` → `polling.design_effect` | Declared at 1.6 (standalone 1.2) and unmeasured; measurable the day a house publishes its effective base. | 🔴 | §A10 |
| `poll_half_life_days` | 120.0 | `montecarlo.DEFAULTS`, mirrors `polling.POLL_HALF_… | A real constant since §1.67 and mirrored in `DEFAULTS`, so a sweep can now reach it. Still declared: no SA metro series is long enough to fit it. | 🔴 | §A14 |
| `POLL_HALF_LIFE_DAYS` | 120 | — | 120, declared. No SA metro series is long enough to fit it. | 🔴 | §F3 |
| `poll_house_k` | 1.0 | `montecarlo.DEFAULTS` → `polling.weight_cap` | INERT. The cap it drove was deleted 2026-08-24 with the two-term σ; a lone house is now bounded by the derived `polling.house_ceiling` instead. | 🔴 | §A12 |
| `poll_id`, `poll_weight`, `poll_k` | — | `polls.json` | DELETED 2026-08-22. The legacy path bypassed every admission rule in `polling.usable_for` and had never executed. | ⚪ | §F30 |
| `POLL_K` | — | — | DELETED 2026-08-22 with the legacy poll path. The shape survives as `poll_house_k`. | ⚪ | §F5 |
| `poll_min_n` | 300 | `polling.screen` | Declared at 300 and settable. Note it runs ahead of every scope test, so it also gates the national polls that drive the arrivals path. | 🔴 | §A16 |
| `poll_paths` | "all" | `montecarlo.py`, gates both live poll paths | Ships "all". On sixteen city-years the channel is worth −6 coherent seats — turning it off is better on seats and on CRPS. The 48-seat figure is RETRACTED. | 🟢 | §A8 |
| `POLL_RMS_ERROR` | ~~0.030~~ | — | DELETED 2026-08-28. Read by nothing; the constant the tests assert against is its neighbour `POLL_RMS_ERROR_2016`. | ⚫ deleted | §F2 |
| `poll_screen_sd`, `poll_drift_per_root_day`, `POLL_MIN_N` | 0.020 · 0.0010 · 300 | `montecarlo.DEFAULTS` → `polling.py` (`POLL_MIN_N`… | All three declared, none measured. The drift rate is fittable from the campaign's waves — pre-register that fit before running it. | 🔴 | §A13 |
| `polling_lean`, `polling_span` | — | DELETED, and this row said "still wired" for days… | DELETED. This row said "still wired" for days after they were gone, which is why the register → code guard exists. | ⚪ | §F26 |
| `POOL_CAPACITY_MARGIN` | 0.98 | `montecarlo.py` (`capped_targets`) | Ships 0.98, one full step clear of a measured cliff. It is the guard, not the cure — the cause is an upstream corner solution in the ecological fit. | 🔴 | §A28 + §F9 |
| `POOL_CAPACITY_MARGIN` | 0.98 | — | See §A — a judgement about what to do when two layers disagree, not a tolerance. | 🔴 | §F9 + §A28 |
| `PROJECTED_METRO_SHARE` | eight per-metro shares of the national vote, 2021 values | — | The last observed value, so nothing is extrapolated; n = 2 and it fires only where no backtest can check it. | 🔴 | §F36 |
| `REFERENCE_SHARE`, `REFERENCE_SLATE` | `REFERENCE_SHARE` = 0.0025 · `REFERENCE_SLATE` = 0.25 | `compare_history.reference_universe` | Both typed. The share cut is safe (below every metro's PR quota); the slate cut is the one to attack, and it moves no forecast — only which columns a width comparison is read on. | 🔴 | §D8 |
| `REG_DRIFT_TOLERANCE` | 0.30 | `build_concordance.py` | RECLASSIFIED 2026-08-24 from 🟢 reporting to 🔴: it reaches the forecast through `fold.suspect_vds` → `w_split` → γ. Declared, never measured, and not a `DEFAULTS` key, so no lever sweep can reach it. | 🔴 | §F38 |
| `RELIABILITY_HALF` | 0.002 | — | 0.002, a value inherited from the hard cut it replaced; only the smooth form is new, and it has never been swept. | 🟡 | §F16 |
| `SAFE` / `STRONG` / `LEAN` | — | `hex_cartogram.py` | Copies of `render_map.main`'s tiers, held in step by `test_the_two_maps_agree_on_the_confidence_tiers`. Not an independent judgement. | 🟢 | §D19 |
| `SD_FLOOR`, `SD_CEILING` | 0.15, 1.20 | `levels.py`, applied in `sd_for` | 🟡 at ≥15% of the vote. On the corrected harness the width in use is 0.151 against a measured 0.273 [0.136, 0.386] — inside the interval but near its bottom, at 1.81×, binding on 32 of 64. Below 15% every interval EXCLUDES it. | 🟡 (≥15%) | §F17 |
| `SHRINK` | 2.0 | `levels.py` | 2.0, measured optimal on forward-validated RMSE(log θ) and on the model's own three scores. Upgraded from 'pre-existing' — do not re-file it as untested. | 🟢 | §A24 + §F15 |
| `SHRINK` | 2.0 | — | Measured optimal 2026-08-17. Do not re-file it here as 'pre-existing'. | 🟢 | §F15 + §A24 |
| `SIGMA_COMMON` | 1.5pp | The industry-common poll bias | LIVE since 2026-08-24. 1.5pp, declared and sourced from outside this repository; never divided by the number of houses, which is the defect it exists to fix. | 🔴 declared, sourced | §H17 |
| `SIGMA_DRIFT_PER_ROOT_DAY` | 0.30 pp/√day | Opinion movement between fieldwork and polling day. | LIVE since 2026-08-24. 0.30 pp/√day, declared and sourced; the shipped `POLL_DRIFT_PP_PER_ROOT_DAY` of 0.10 is 2–4× too small. | 🔴 declared, sourced | §H19 |
| `SIGMA_IDIO` | 1.5pp | The house-specific part | LIVE since 2026-08-24. 1.5pp, declared and sourced; the ONLY term `h_eff` may divide. | 🔴 declared, sourced | §H18 |
| `SIGMA_VOLATILITY` | 0.8pp | A South Africa adjustment: +0.1pp per 1pp of avera… | LIVE since 2026-08-24. 0.8pp, declared and sourced — a South Africa adjustment for average party swing. | 🔴 declared, sourced | §H20 |
| `SIMULATION_BLOC` | container | `pools.py` | The reader-simulation bloc definition that `within_rate` sits in. | 🔴 | §H12 |
| `SOLVE_TOL` | 1e-9 | `pools.py` | Operational, and listed EXEMPT in the guard — named here so the exemption is visible in the register and not only in the test. | 🟢 | §F11 |
| `SPINE_K` | 1.0 | — | See §B. | 🔴 | §F14 + §B1 |
| `spine_k = 0` on a party with no θ evidence | `w_local = 0.0` | — | A CHOSEN limit (`w = 0`, pure national spine), inert at the shipped `spine_k = None` and reachable only by a sweep, which is what it exists for. | 🟡 | §F22 |
| `SPINE_K`, reciprocal form | — | `levels.py` | 1.0, fitted leave-one-metro-out on a curve that is flat 0.5–1.5. A step function scored better out of sample and was rejected on structural grounds — which is why this is 🔴 despite being fitted. | 🔴 | §B1 + §F14 |
| `SPLINTER_PARENT_WEIGHT` | 0.35 | — | 0.35, measured over 22 splinter-metro cases, no bootstrap, and stale since the archive grew (§A). | 🔴 | §F6 |
| `SPLIT_SD_FLOOR` | — | `pools.py` | 0.90, and it overrides its own measurement at target 2016 while binding at neither 2021 nor 2026 — real work in the one fold where it is least justified. | 🔴 | §B3 |
| the size-dependence of `sd_for` below 15% | a straight line in log(size) | `levels.py`, inside `theta_prior` | The model is UNCHANGED and the fault is the FORM, not the residual. ⛔ No further functional form may be tried against these two folds, and this row's numbers are Form A's and must not be quoted. | 🔴 | §F18 |
| `THETA_CENTRAL` | 6 party values | `leverage.py` | NOT LIVE. The plan's six typed party values, and the module holding them has since been retired out of `src/` — see the restructure note beneath. | 🟡 not live | §H16 |
| `theta_prior` and `_shrunk` | RESOLVED 2026-08-18 | `levels.py` (`theta_prior`, `_shrunk`) | RESOLVED 2026-08-18. Both shrink toward `size_centre`, they agree to 1e-16, and no forecast moved. | ⚪ | §A26 |
| `TIP_FLOOR` / `OTHER_FLOOR` | — | `hex_cartogram.py` | Same provenance and same drift guard as the tiers above. | 🟢 | §D20 |
| `top = 12` parties per table | — | `compare_history.py` | Cosmetic here — but it is what makes `validation_2021.json` not comparable. | — | §D13 |
| `total_seats` | 270 | `seats.allocate` | Johannesburg's 270 as a DEFAULT ARGUMENT in the shared allocator. The offending caller this row names was `leverage.py`, since retired — every `allocate` call left in `src/` passes it explicitly, so the trap is latent rather than live. | 🔴 | §H10 |
| `TURNOUT_CORRELATION` | — | `montecarlo.py` | 0.63 applied as ONE constant to every city and pool pair. It supplies 4–12% of drawn variance in the shape a pool-turnout mechanism should have; why it matters so little is still not explained. | 🟡 | §B4 + §F13 |
| `TURNOUT_CORRELATION` | 0.63 | — | 0.63, declared in `DEFAULTS` since §1.63 and asserted equal to the module constant at import. It MOVES the forecast, so it is a live lever. | 🟡 | §F13 + §B4 |
| TURNOUT_CORRELATION / SPLINTER_PARENT_WEIGHT / SPLIT_SD_FLOOR — the stale-`n` trio | `TURNOUT_CORRELATION` 0.63 · `SPLINTER_PARENT_WEIGHT` 0.35 · `SPLIT_SD_FLOOR` 0.90 | `montecarlo`, `pools` | Still NOT re-measured against the enlarged θ record, and deliberately so; quote none of their `n` values until the record question below is settled. | 🔴 | §A1 |
| `TURNOUT_DRAW_FLOOR`, `TURNOUT_DRAW_CEILING` | 0.02, 0.95 | — | 0.02 / 0.95, applied per draw. They contradict §C's claim that the turnout band 'removes caps rather than adding one'; whether the ceiling ever binds is unmeasured. | 🔴 | §F34 |
| `turnout_noise_sd`, `turnout_blend_jitter` | 0.08, 0.25 | — | Typed; ~0.003 citywide, i.e. nothing. | 🟡 | §F23 + §A41 |
| `turnout_pattern_blend` / `turnout_blend_jitter` / `turnout_noise_sd` | 0.5 / 0.25 / 0.08 | `montecarlo.py` | Typed. The citywide effect of the 0.08 is ~0.003, i.e. nothing — but see §G-R5: the turnout knobs move 46 ward wins, so the citywide null is not the whole story. | 🟡 | §A41 + §F23 |
| `w_bye` | 0.40 | `montecarlo.py` | Typed at 0.40, live in the 2026 forecast and inert in every backtest. Only the 2026 result can bound it. | 🔴 | §A35 |
| `w_bye_local_ward` / `w_bye_local_pr` | 0.0 / 0.0 | `montecarlo.py` | Built and disabled at 0.0 / 0.0. Untestable for the same reason as `w_bye`. | 🟡 | §A37 + §F25 |
| `w_bye_local_ward`, `w_bye_local_pr` | 0.0, 0.0 | — | Built, disabled, untestable. | 🟡 | §F25 + §A37 |
| `w_recency` | 0.70 | `turnout.py --w-recency` | 0.70, verbatim from the original plan. It reaches the model through 20 committed `turnout.csv` files that carry no artefact key, so changing it does nothing until someone re-runs the script. | 🔴 | §H2 |
| `w_split` | 0.6 | `fold.py --w-split` | 0.6, plan §3.5 'Basis: Judgement', baked into the fold parameter artefacts. | 🔴 | §H4 |
| `ward_noise_sd` | 0.10 | `montecarlo.py` | Typed at 0.10 on an audit, never measured and never bounded. | 🟡 | §A38 |
| `WARD_PR_RATIO_MIN`, `WARD_PR_RATIO_MAX` | 0.5, 2.0 | — | 0.5 / 2.0 — the clip that overrides the record §E says the ward/PR ratio comes from. How often it binds is unmeasured. | 🔴 | §F35 |
| `within_rate` | 0.90 | `pools.SIMULATION_BLOC`, `vote_located_bloc` | 0.90, and three copies of one number. | 🔴 | §H11 |

### Judgements with no symbol of their own

Structural calls the code makes without a constant to name them. They are the
easiest kind to lose, because nothing can grep for them.

| the call | where | current state | status | entry |
|---|---|---|---|---|
| the θ record pools a collapse, a split and a merger | `levels.theta_record` | Not implemented. The 2009→2011 transition is still pooled into θ; a structural-event filter is the proposed instrument and the decision is the owner's. | 🔴 | §A2 |
| retiring the generic entrant at nomination close | `montecarlo`, `cities/joburg.toml` | OPEN GAP. A one-off decision to be taken when the lists close on 16 September — explicitly NOT to be automated. Task A4. | 🔴 | §A4 |
| the published 2026 forecast is not the backtested configuration | `montecarlo`, `polling`, and the whole `EXPECTED_I… | Still true, and still the strongest criticism available to a reviewer: one house (SRF/Victory Research) decides the Johannesburg headline, now through the σ arithmetic rather than a cap. | 🔴 | §A7 |
| σ_poll, decomposed (`POLL_HOUSE_SD` and the calibration trio) | `polling.poll_sd` / `aggregate_sd` | The flat `POLL_RMS_ERROR` form is retired; the live sum is `polling._sigma_total` and `POLL_HOUSE_SD` survives only as the `n_eff == 0` fallback. | 🟡 | §A9 |
| the derivedness budget | `ITERATING.md`, "the only question" | Declared at 12 coherent seats and never topped up. Governance, not a code lever; it deliberately has no symbol in `src/`. | 🔴 | §A15 |
| how unplaced votes are spread over a party's zeroed pool cells | `pools.balance_within_bounds` | Pool-size proportional, and there is no constant in it — the quantity is derived. Argued, not tested: no backtest can separate the three candidate rules. | 🟡 | §A19 |
| the §3.5 θ sanity-range violations | see `montecarlo.py` | STILL UNACTED ON. The diagnostic prints against the model on every run and nothing reads it; nobody has decided whether the ranges or the draws are wrong. | 🔴 | §A20 |
| the width statistic the report quotes | `compare_history.pit_dispersion` | Probit-SD is what the report quotes, measured on a fixture and ~5-10% attenuated at this model's shift. Its stated successor `dispersion_ratio` is now IN `compare_history` and emitted — this row has not been re-read since. | 🟡 | §A21 |
| doc-vs-artefact tolerances | `compare_history`, and the test that enforces it | Unchanged, and deliberately tight enough that a legitimate re-run will demand the documents be updated. | 🟡 | §A22 |
| the blend weight ignores the ρ record | `levels.spine` | Deliberate, not an oversight: the symmetric form scores 338 against 312. | 🟢 | §A25 |
| the capacity redistribution rule | `montecarlo.py:capped_targets`, the `t[free] += ex… | Still proportional to mass held, and still unmeasured against the two defensible alternatives; the quantity moved is now counted on `capped_targets.moved`. | 🔴 | §A27 |
| the Dirichlet floor | `montecarlo.py` (`DIRICHLET_FLOOR`), applied at `1… | 1e-4 — a numerical guard only. The 0.05 that manufactured ~5pp of citywide vote is gone. | 🟢 | §A30 |
| turnout spread with one observation | `pools.py` | Typed at 0.30 logits, and it binds at every 2016 target. | 🟡 | §A32 |
| turnout-adjusted by-election weighting | — | CONSIDERED AND REFUSED 2026-08-28 with the measurement (leave-one-contest-out RMSE 36.46pp against uniform's 24.66pp). A per-party sensitivity is worth pre-registering; the uniform form is not. | ⚫ refused | §A34 |
| ward→PR conversion of the by-election delta | `montecarlo.py` | Adopted 2026-08-28 on out-of-sample evidence. Not a chosen number — it reuses the population and clip `ward_pr_ratios` already applies. | 🟡 | §A36 |
| the arrival boundary | `montecarlo`, by omission | Still nobody's choice. 16 of the 79 mid-ballot parties sit on the wrong side of it and carry +16.4pp of the −37.4pp band deficit. | 🔴 | §A42 |
| the arrival-group mechanism's five typed constants | `pools.arrival_group_spec`, `pools.arrival_group_r… | Declared 2026-08-29, none swept. The `n < 3` record drop is live on the INCUMBENT path at every target; the 0.45 cap's 'never binding' comment is wrong at 2026 (5.7e-03 per draw). | 🔴 | §A45 |
| the peer window that sizes every seeded arrival | `pools.arrival_rules.comparators` | Declared 2026-08-29. Live in every backtest and in the 2026 forecast, not gated by `arrival_group_draw`, and the frequency of its whole-record fallback is unmeasured. | 🔴 | §A46 |
| vote-weighted RMSE as the criterion | the #22 fit | Unchanged: the weighting chose the winner, and must be stated whenever the spine's 14% gain is quoted. | 🔴 | §B2 |
| Gaussian copula for pool turnout | `montecarlo.py:_tri_ppf` | Conventional and unchanged. It has no tail dependence, which is a substantive assumption nothing has tested. | 🟡 | §B5 |
| `Σ base·θ = 1` in the IPF | `fold.calibrate_theta` | Forced: predicted citywide shares are shares. | 🟢 | §C1 |
| splinter fraction capped at 1.0 of parent | `pools._band_from` | Forced: a party cannot take 117% of the vote its parent had. | 🟢 | §C2 |
| turnout band in logit space | `pools.turnout_band` | A scale choice, and the standard one. Note it REMOVES caps rather than adding them — which §F's `TURNOUT_DRAW_FLOOR`/`TURNOUT_DRAW_CEILING` row contradicts, and says so. | 🟢 | §C3 |
| ENTRANT relabelling | `diagnose.py` | In place, and asserted by `test_the_generic_entrant_is_relabelled_wherever_it_is_reported`. | — | §D1 |
| mean vs median as the point forecast | `compare_history.py` | Both are now shown; they differ ~5× for small parties. | — | §D2 |
| the "ruled out" threshold | `diagnose.py`, `p < 0.02` | Typed at p < 0.02. | — | §D3 |
| anomaly thresholds | `sweep.py` | All typed. | — | §D4 |
| signed-only rank bands | `compare_history.rank_bands`, until 2026-08-17 | Retired: both the signed and the absolute column are now printed. This row is why §D exists — a reporting choice, argued in a docstring, decided what four months of work looked at. | — | §D5 |
| phantom mass | `compare_history.rank_bands` | Now a column and a total; it was printed nowhere and was 6.53pp across the nine city-years. | — | §D6 |
| which columns test calibration | `compare_history.POPULATIONS` / `score.CLAIM_FRACT… | Four populations are reported. `reference` is the ONLY one a before/after comparison may be quoted on; `seat_holders` is outcome-selected, inflated, and labelled so wherever quoted. | — | §D7 |
| pooled AND per rank band | `compare_history.pooled_by_band` | Both are printed; a single city-year row is 4–15 columns of noise and is labelled as such. | — | §D10 |
| the pooled figure must not be read alone | `compare_history.pooled_by_band`, `ITERATING.md` r… | `ITERATING.md` rule 8. The pooled mean PIT was the average of two opposite faults; both coverage statistics are printed and the PIT-corrected one is labelled the width verdict. | 🟡 | §D11 |
| PIT seed derived per city-year | `compare_history._pit_seed` | Derived from the city-year name by CRC32; reproducible, and it cannot change a conclusion. | — | §D12 |
| seat error summed over all parties | `compare_history.py` | Unchanged; parties that won nothing contribute 0, so the wider denominator does not inflate it. | — | §D14 |
| modal ward winner as "the model's call" | `diagnose.py` | A defensible reading of a probabilistic forecast, and it is a reading. | — | §D15 |

---

## A. Not from the record at all

These have no measurement behind them. They are the ones to attack first.

### §A1 · three constants carry an `n` the new archive has changed, and none is re-measured — `TURNOUT_CORRELATION` 0.63 · `SPLINTER_PARENT_WEIGHT` 0.35 · `SPLIT_SD_FLOOR` 0.90 — 🔴

**Where.** `montecarlo`, `pools`

**Now.** Still NOT re-measured against the enlarged θ record, and deliberately so; quote none of their `n` values until the record question below is settled.

**Record**, oldest first:

1. **RAISED 2026-08-22 (§1.71) — the owner asked whether the derived values had been rechecked after the pre-2011 ingest, and the answer is only partly.** The θ record grew from n=257 over 18 metro-year clusters to **n=370 over four target LGEs**. Two quantities were re-measured and MOVED: forward-validated `sd(log θ)` at ≥15% of the vote went **0.138 [0.084, 0.171] → 0.208 [0.114, 0.299]**, and `SD_FLOOR` now binds on **26 of 64** observations there against 20 of 37 before (which is why `test_the_floor_binds_at_the_top_of_the_ballot_and_only_there` fails).
2. **Superseded 2026-08-23 (§1.77): on the restored tree the figure is 0.273 [0.136, 0.386] at n=403, the binding count is unchanged at 26 of 64, and that test now asserts the structural claim rather than the majority. §1.71's n=370 does not reproduce.** These three did not: `TURNOUT_CORRELATION` is registered as "measured over 14 metro-transitions" and more transitions now exist; `SPLINTER_PARENT_WEIGHT` as "measured over 22 splinter-metro cases" and more history now exists; `SPLIT_SD_FLOOR` was already known to override its own measurement at 2016. **They are deliberately NOT re-measured yet**, because re-deriving them against a θ record that §1.71 argues is contaminated by the 2009→2011 structural events would bake that contamination in. Quote none of their `n` values until the record question is settled

### §A2 · the θ record pools a collapse, a split and a merger as if they were retention — the 2009→2011 transition — 🔴

**Where.** `levels.theta_record`

**Now.** Not implemented. The 2009→2011 transition is still pooled into θ; a structural-event filter is the proposed instrument and the decision is the owner's.

**Record.** **MEASURED 2026-08-22 (§1.71) and it is the largest open modelling question.** θ dispersion for parties ≥5% of the national vote: 2004→2006 **0.226**, 2009→2011 **0.942**, 2014→2016 + 2019→2021 **0.200**. One transition is 4.7× its neighbours, and it is the one γ fold 3 requires, so the pre-2011 ingest imported seven metros' worth of it. The observations name themselves: **COPE at θ 0.115–0.282 across six metros** (formed Dec 2008, 7.4% nationally in 2009, gone by 2011), the **IFP at 0.465** (the NFP split away in Jan 2011), and the **DA at 1.378–1.577 across five** (the Independent Democrats merged into it in 2010). Excluding those takes the transition from **0.896 to 0.244**. The ANC rows were never the problem. This repository already has machinery for collapses, splits and arrivals (`SPLITS`, `splinter_record`, the arrivals path), so pooling these into θ **double-counts them** and inflates the common large-party dispersion — which is what widened the top of the ballot and cost §1.70's 26 seats. **A date cutoff is the wrong instrument** and cannot be built regardless: the record must be strictly pre-target, so a 2016 floor leaves a 2016 target with no record at all. What the measurement supports is a structural-event filter keyed on the tables the model already keeps. Not implemented; it moves every city-year and the decision is the owner's

### §A3 · `entrant_prob` — 0.25 — 🟡

**Where.** `montecarlo.py`

**Now.** Ships 0.25. Typed, but measurable since 2026-08-17 and the typed value survives the measurement; §G-R2 puts the defensible range at [0.25, 0.29].

**Record.** The probability that a party arrives from nothing. **A party arrived and won seats in 3 of the last 3 Johannesburg elections** — NFP 2 seats (2011), AIC 4 (2016), ActionSA 44 (2021), and in **7 of the 9 backtested city-years**, median 3 arrivals apiece. At 0.25 the model is silent in 75% of draws, so its *median* seat forecast for an arriving party is **0 whatever its vote share** — but the *mean*, which is what `coherent_seats` uses, is 0.25 × E[triangular(1%, 4%, 12%)] = **1.42%**. Until 2026-08-17 this constant was **unmeasurable twice over** (§1.31): the scoring never relabelled the generic slot onto the party that arrived, and `apply_city` overwrote any edit to `DEFAULTS`. Now measurable, and **the typed value survives the measurement**: on Johannesburg 2016 it drew 1.39% and 3.82 seats against the AIC's actual 1.62% and 4, and at 0.99 it overshoots to 5.35% and 14 seats. The 78% base rate answers a different question — how often *an* arrival wins a seat, not how big *the largest* one is. Downgraded 🔴 → 🟡: still typed, but now tested.

### §A4 · nothing retires the generic entrant when the ballot becomes known — `entrant_prob` stays 0.25 — 🔴

**Where.** `montecarlo`, `cities/joburg.toml`; the roster is available from `pools.contesting_parties` and is not consulted

**Now.** OPEN GAP. A one-off decision to be taken when the lists close on 16 September — explicitly NOT to be automated. Task A4.

**Record.** **RAISED BY THE OWNER 2026-08-22 and it is a real gap.** The `ENTRANT` column exists iff `entrant_prob > 0`, and **no code path reads a nomination roster to decide that.** The generic slot is a stand-in for not knowing the ballot; nomination lists close and are published on 16 September, and at that moment the ignorance it models is gone. Two cases and neither is automatic: if the lists carry a genuinely new party it should be **named and seeded** in `judgements/joburg-2026.toml` and `entrant_prob` set to 0, because otherwise the same arrival is counted twice; if they carry none, `entrant_prob` should be 0 because the modelled event is known not to have occurred. Measured cost of leaving it, Johannesburg 2026 at 500 draws: **DA 80 → 81, ANC 63 → 64** between 0.25 and 0. Small, and the wrong kind of small — the slot's MEDIAN is zero while its MEAN carries `0.25 × E[triangular(1%, 4%, 12%)]` ≈ **1.42% of the vote**, `coherent_seats` uses the mean, and largest remainder converts it. It is part of the **+6.54pp phantom** the backtest already reports. **Do NOT automate it as "roster known ⇒ no generic entrant"**: at every backtested target the roster is also known, and there the generic slot IS the forecast for the party that arrived — it is what gets relabelled onto the AIC at Johannesburg 2016. Naming arrivals individually instead is `arrival_group_draw`, measured at 254 → 348 and rejected (§1.63). So this is a decision to be taken once, at nomination close, not a rule. Task A4

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** The closing sentence quotes `arrival_group_draw` as *"measured at 254 → 348 and rejected"*. §A6 forbids exactly that quotation — *"do not quote it as the live rejection"* — because the baseline was superseded by §1.94 and the arm also deleted the splinter seed. The rejection itself stands on the 2026-08-29 re-run; the number does not.

### §A5 · `contestation_expand` — 0.220 — 🔴

**Where.** `montecarlo.py`, applied in `levels.projected_contestation`

**Now.** Ships 0.220, live only where no backtest can reach it; superseded automatically the day the IEC publishes 2026 lists.

**Record.** How much a party's ward slate grows between local elections, used **only where the target's nomination lists are not published** — every live forecast, no backtest. `now = was + expand·(1 − was)`. **It replaces an assumption made by omission**: `levels.contestation` reads who stood from the target's own result file, so at 2026 the correction was silently the identity, i.e. every party fields exactly the slate it fielded five years ago. **The default is measured**: across the eight metros and every consecutive LGE pair on disk (n=165 parties present at both) the median party moves **+0.220** of the way to a full slate and **65.5% expand**. The most recent transition alone (2016→2021) gives per-metro medians of +0.46 / +0.14 / +0.78 / +0.59 / +0.63 / +0.20 / +0.71 / +0.06 — about +0.5 — which is what a fragmenting party system looks like, and is why this is a lever and not a constant. **ARGUED, NOT TESTED, and live exactly where nothing can check it** — the same position `pa_contestation_uplift` was in, and that is why it is 🔴 rather than 🟡 despite a measured default. It acts on THIN SLATES, which is the intended asymmetry: at Johannesburg 2026 the PA (52 of 135 wards in 2021) goes 17 → 19 → 22 median seats at expand 0.0 / 0.220 / 0.5 with ward wins 4.0 → 6.0 → 8.6, while the DA gives up 83 → 81.5 → 80. **Superseded, not supplemented, by real lists**: when the IEC publishes 2026 candidate lists (task A4) `contestation` returns them, the projection is not called, and this lever goes inert — asserted in `tests/test_levers_are_live.py`. Backtests are bit-identical with it at any value. MODEL-LOG §1.60.

### §A6 · `arrival_group_draw` — False — 🟢

**Where.** `montecarlo.py`, read in **`make_drawer`** — **NOT `blended_centres`**, corrected 2026-08-29 (§1.136); `blended_centres` never touches the key, so the CENTRES are byte-identical across both arms and this lever cannot move a centre

**Now.** Ships False. The rejection was re-run on the label-free referee 2026-08-29 and refuted again; the 254 → 348 figure is superseded and must not be quoted.

**Record**, oldest first:

1. Whether an arriving party's size comes from the ARRIVAL-GROUP mechanism — a group total drawn from a fitted lognormal and split among named arrivals by a Dirichlet — or from the generic `ENTRANT` slot, a Bernoulli times a triangular.
2. **UNTIL 2026-08-20 THIS KEY DID NOT EXIST.** `blended_centres` read `scenario.get("arrival_group_draw")`, it was in no `DEFAULTS`, and both `parse_set` and `read_scenario_file` reject a key that is not already in the scenario — so `--set` and a config file could not create it either. The mechanism was not off, it was **unreachable**, and `MACHINERY.md` described it as *switched off*, which claims a switch that did not exist. Same class as `LEVEL_DF` bound as a default argument (§1.33). It escaped both lever guards for the one reason neither can catch: they iterate `DEFAULTS`. **And it was broken** — the branch raised `NameError: dirichlet_floor` on the first run that reached it, so the code comment scheduling a retry "by 2026" scheduled a crash, and the rejection measurement recorded against it was taken on code that has since drifted. Now declared, repaired and **measured on nine city-years, which the original Johannesburg-only rejection never was: coherent seat error 254 → 348 and CRPS 232.9 → 296.0, worse in six city-years and better in one.** The rejection is confirmed and strengthened. Ships False — what changed is that "off" is now true rather than merely written down. MODEL-LOG §1.63.
3. **⛔ AND IT DELETES THE SPLINTER CHANNEL (2026-08-29, §1.136).** `arrival_group_spec` is handed `sorted(arrivals)` — the full key set of `arrival_rules`, splits and entrants alike (`arrival_group_spec`'s call site in `pools.py`) — so all 32 seeded parties at Johannesburg 2021 are in its weights, ActionSA included, and `make_drawer` zeroes those columns before overwriting them: ActionSA actual **18.12%**, incumbent pool-splinter seed **6.85%**, challenger **0.18%**. So this is not "a fitted group replacing a typed slot"; it is that AND the removal of the seed carrying the largest arrival in the panel, and it cannot be read as a test of the group estimator while both are true. **The 254 → 348 above is a NINE-city-year figure scored through the outcome-favourable relabel, and §1.94 superseded that baseline (376 on sixteen) — do not quote it as the live rejection.** The fair re-run on the label-free referee (2026-08-29) refutes it again: 2 of 8 metros at 2021, pooled Σ|mass_err| 0.2714 → 0.5084, Key 2's level-free width 1.2000 → 1.3557.

### §A7 · the published 2026 forecast is not the configuration the backtest scores — 🔴

**Where.** `montecarlo`, `polling`, and the whole `EXPECTED_INERT` list

**Now.** Still true, and still the strongest criticism available to a reviewer: one house (SRF/Victory Research) decides the Johannesburg headline, now through the σ arithmetic rather than a cap.

**Record.** **MEASURED 2026-08-22 (§1.69), and it is the strongest criticism available to a reviewer.** The headline "254 coherent against uniform swing's 376" is scored on a configuration the live forecast does not run, in both directions. **What 2026 GAINS that no past target can score:** `w_bye` (the by-election window is 2022-06 to 2026-02, so no backtested target has any), `contestation_expand` (superseded by real nomination lists wherever a result file exists), and all six poll levers (the register holds no metro poll of Johannesburg declared for 2021). **What 2026 LOSES:** the arrivals poll path, worth **48 coherent seats** (§1.65) — see the row above. And the magnitude is not small. Johannesburg 2026 at `poll_paths` off against all, 600 draws: **DA 65 → 78 seats, ANC 68 → 63, ASA 31 → 25 — and the lead FLIPS**, from ANC-largest to DA-largest. `H_eff` still prints as **1.0** — the two admitted Johannesburg polls are both SRF/Victory Research — but **there is no longer a cap to sit on** (2026-08-24, §1.91). The influence is now set by the σ arithmetic and not by `poll_house_k`, which is the reverse of what this row said for a day. Measured on the shipped register at target date: DA σ **5.057pp** against a floor of **4.595pp**, ANC 4.922pp, MK 4.794, ASA 4.772, EFF 4.720. MEASURED on the settled tree (`tests/test_drawer.py`, re-recorded 2026-08-24): the DA's blend weight is now **0.484 by arithmetic** where the cap used to pin it at exactly 0.500, and the 2026 forecast moves by about a seat — **DA 79 → 78, ANC 63 → 64, ASA 24 → 25**. So the dependence on one house is essentially UNCHANGED in magnitude; what changed is that it is now set by the σ arithmetic and can be argued with, rather than by a typed constant. The 65 → 78 / 68 → 63 poll-on-vs-off figures below therefore still stand to within a seat. One house, two waves, decides the headline. Quote this beside the 254 wherever the 254 is quoted; it is not a defect to be fixed but a dependence to be disclosed

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** This entry quotes the arrivals poll path as *"worth **48 coherent seats**"* and points at "the row above". §A8 retracts that number in terms — *"The 48 must not be quoted; it was, twice"* — and measures the whole channel at **−6** coherent seats on sixteen city-years. The two entries have contradicted each other since 2026-08-25 and the later one says so. Nothing here reconciles them: which figure is right is a judgement, and it changes what a reader believes about the published forecast.

### §A8 · `poll_paths` — "all" — 🟢

**Where.** `montecarlo.py`, gates both live poll paths

**Now.** Ships "all". On sixteen city-years the channel is worth −6 coherent seats — turning it off is better on seats and on CRPS. The 48-seat figure is RETRACTED.

**Record**, oldest first:

1. Which poll paths run: `"off"` · `"arrivals"` (a national poll converted to the contested area, for parties with NO record) · `"all"` (adds the metro-poll inverse-variance blend).
2. **Added 2026-08-21 so the channel could be MEASURED for the first time** — until then the only way to switch it off was to empty `polls.json`, and nothing in `sweep.py`, `compare_history` or the tests scored it. ~~Nine city-years at 1500 draws: off 304 / arrivals 256 / all 254.~~
3. **REVERSED ON SIXTEEN, 2026-08-25 (§1.94).** Sixteen city-years, 1500 draws, paired on identical seeds: **off 376 coherent / CRPS 324.6 · arrivals 378 / 327.6 · all 382 / 329.0** — monotone the OTHER WAY. The channel is worth **−6 coherent seats**: turning it off is better, on seats and on CRPS. It fails two of Key 1's three conditions. **This is not the doubled panel** — on §1.65's own nine city-years it measures **−4**. What changed is that the model WITHOUT the channel improved sharply (Tshwane 2021 52→34, Ekurhuleni 38→28) while the model with it did not: the channel was patching a hole, and the hole was fixed. The 48 must not be quoted; it was, twice, after §1.70 instructed that every nine-city-year number be re-read here, and the metro path two more; **no city-year is made worse by either.** Ships at `"all"`, which is seat-identical to the committed artefact. **Two caveats that must travel with the number**: the whole arrivals effect is one party (ActionSA) in four metros of one cycle, so under rule 11 the effective sample is close to one; and the path is **dead at 2026** for want of a `NATIONAL_VOTES["2026"]` entry, so the 48 seats are measured on a channel the live forecast does not currently have. MODEL-LOG §1.65.

### §A9 · σ_poll, decomposed — `POLL_HOUSE_SD` 0.025 · `POLL_CAL_N_2016` 800 · `POLL_CAL_DEFF_2016` 1.3 · `POLL_RMS_ERROR_2016` 0.0303 — 🟡

**Where.** `polling.poll_sd` / `aggregate_sd`

**Now.** The flat `POLL_RMS_ERROR` form is retired; the live sum is `polling._sigma_total` and `POLL_HOUSE_SD` survives only as the `n_eff == 0` fallback.

**Record**, oldest first:

1. Replaces the flat `POLL_RMS_ERROR = 0.030` as the live weight. ~~`σ² = deff·p̂(1−p̂)/n + σ_house² + σ_screen² + (drift·√days)²`~~ —
2. **RETIRED as the live form on 2026-08-24 (§1.91).** The live sum is `polling._sigma_total`: `sampling + σ_common² + σ_idio²/H_eff + screen² + (drift·3)² + σ_volatility²`, of which **only `σ_idio` is divided by the number of houses** — the others are common by construction and do not average away. `POLL_HOUSE_SD` survives only as the `n_eff == 0` fallback.. **`POLL_HOUSE_SD` is MEASURED**: it is the residual of the 3.03pp Ipsos-2016 track record after the sampling term is removed, and it moves only from 2.16 to 2.77pp across a threefold range of the unrecorded n — which is why it survives the two declared rows beside it. **Screen and drift are EXCESS terms, not additions**: the 2.5pp residual is the TOTAL non-sampling error of polls with a disclosed method two days out, so charging every poll a screen term on top would count it twice. The decomposition reproduces its own calibration to **0.02pp** and `tests/test_polling_sd.py` asserts it. §1.67.

### §A10 · `poll_deff_subsample` (module defaults `POLL_DEFF_SUBSAMPLE`, `POLL_DEFF_STANDALONE`) — 1.6 (standalone 1.2) — 🔴

**Where.** `montecarlo.DEFAULTS` → `polling.design_effect`

**Now.** Declared at 1.6 (standalone 1.2) and unmeasured; measurable the day a house publishes its effective base.

**Record.** A ~500-person metro cut of a national sample carries the parent design's weighting loss and clustering, so its recorded `n` overstates the information. `n_eff = n/deff` turns the July 2026 SRF wave's **504 into 315**, i.e. ±5.5pp against the ±4.4pp the record's own `caveat` string claims. **DECLARED**, and measurable the day a house publishes its effective base. Note `n` was in the schema and read by NOTHING until now. §1.67.

### §A11 · `poll_credence` — 1.0 — 🔴

**Where.** `montecarlo.DEFAULTS` → the metro-poll blend

**Now.** Declared at 1.0, which is the identity, so it moves nothing. The value the backtest supports is UNMEASURED — the paired sweep is pre-registered and not run.

**Record.** **How much the forecast believes the metro polls, as a dial rather than a switch.** Multiplies the blend weight `w` before it is applied, clamped to [0, 1]. **1.0 is the identity**, so adopting it moved no number — `w * 1.0 == w`, and the seat draws came out bit-identical as expected. (Recorded as a fact, not as the justification: the reason the lever is acceptable is that 1.0 is the identity, NOT that it agrees with a previous output — see `CLAUDE.md`, "Nothing this model has ever produced is a standard of correctness", §1.96.) 0.0 ignores metro polls; above 1.0 leans in. **Why it exists**: polls do three jobs and the backtest scores one. As an INPUT the channel measures −6 coherent seats on sixteen city-years (§1.94); as an EXTERNAL CHECK that the model is in the ballpark they are the only independent reading available, and that is unscoreable by construction; and a reader in the interactive must be able to say how much they believe a given house. −6 is evidence the WEIGHTING is wrong, not that the polls are empty, and a binary switch cannot express that. **Scoped to the metro blend deliberately** — the arrivals path is a route precedence, not a blend, so credence has no meaning there and `poll_paths` remains its switch. **DECLARED at 1.0 as the incumbent, NOT as a recommendation**: the value the backtest supports has not been measured yet, and the paired sweep across the panel is pre-registered but not run. Quote it as unmeasured until it is

### §A12 · `poll_house_k` (module default `POLL_HOUSE_K`) — 1.0 — 🔴

**Where.** `montecarlo.DEFAULTS` → `polling.weight_cap`

**Now.** INERT. The cap it drove was deleted 2026-08-24 with the two-term σ; a lone house is now bounded by the derived `polling.house_ceiling` instead.

**Record.** Caps a poll's weight at `H_eff/(H_eff+K)` — **exactly 0.50 at one house**, 0.67 at two, 0.75 at three, →1.0 asymptotically. **Why 1.0**: it makes the cap a rule statable in a sentence — *a single unreplicated house is never worth more than the model itself* — and it is the value `SPINE_K` and `POLL_K` already carry, i.e. this repository's existing answer to "how much evidence before a competing estimate is trusted in full". It shipped at 1.4 for one day, putting the cap at 0.42 **for no stated reason**; that is a number chosen rather than argued and is what this register exists to catch. At 1.4 the cap overrode the variance arithmetic for the ANC as well as the DA (0.498 and 0.560 both pulled to 0.42); at 1.0 it binds only where a poll would otherwise outweigh the model. A tighter cap is available and deliberately NOT taken: encoding a view about one particular house in a global constant is the party-specific fiddle deleted twice here — discount a house explicitly if it needs it. **Inverse variance is only correct if both estimates are UNBIASED**, and one house with an undisclosed likely-voter screen is exactly where the bias term is unbounded and no variance formula can express it. Both admitted 2026 polls are the same house (SRF/Victory Research), whose staff and those of its service provider *"have had close associations with the DA"* (Daily Maverick, 2026-08-17) — an independent observation, not ours. **Where it binds today: NOWHERE.** The cap was deleted on 2026-08-24 with the adoption of the two-term σ — `montecarlo` sets `_cap = 1.0` under the switch — because `σ_common` already floors a single house and the cap would double-count it. What bounds one house now is `polling.house_ceiling`, a DERIVED ceiling rather than a chosen one: on the synthetic fixture a lone house saturates at **0.5761** and ten thousand waves do not cross it, while four polls from two houses do (§1.92). `H_eff` counts HOUSES, not waves, so ten SRF waves still give 1.0. **DECLARED**; with two or more houses the cross-house sd is directly estimable and would set it. One backtest city-year cannot, and a sweep over n=1 is not a measurement. §1.67.

### §A13 · `poll_screen_sd`, `poll_drift_per_root_day`, `POLL_MIN_N` (module defaults `POLL_SCREEN_SD_UNDISCLOSED`, `POLL_DRIFT_PP_PER_ROOT_DAY`) — 0.020 · 0.0010 · 300 — 🔴

**Where.** `montecarlo.DEFAULTS` → `polling.py` (`POLL_MIN_N` not yet settable)

**Now.** All three declared, none measured. The drift rate is fittable from the campaign's waves — pre-register that fit before running it.

**Record.** Excess error for a likely-voter screen nobody can inspect; opinion drift as a random walk (≈1.0pp over the 96 days from the July wave); and the floor below which a poll is recorded and never admitted — which exists because **readers will submit polls to the competition**. All **DECLARED**. The drift rate is fittable from three waves of two houses over the campaign; pre-register that fit before running it. §1.67.

### §A14 · `poll_half_life_days` — 120.0 — 🔴

**Where.** `montecarlo.DEFAULTS`, mirrors `polling.POLL_HALF_LIFE_DAYS`

**Now.** A real constant since §1.67 and mirrored in `DEFAULTS`, so a sweep can now reach it. Still declared: no SA metro series is long enough to fit it.

**Record.** **This row previously named a constant that did not exist.** It was a default argument on `polling.aggregate`, so neither `--set` nor a config file could reach it and no sweep could move it — the register documented something that was not there, and `test_every_tunable_constant_is_in_the_judgement_register` only checks code→register so it passed. Now a real constant, mirrored in `DEFAULTS`, with the two asserted equal at import. Still DECLARED: no South African metro polling series is long enough to fit it. §1.67.

### §A15 · the derivedness budget (governance, not a code lever — it deliberately has no symbol in `src/`) — 12 coherent seats — 🔴

**Where.** `ITERATING.md`, "the only question"

**Now.** Declared at 12 coherent seats and never topped up. Governance, not a code lever; it deliberately has no symbol in `src/`.

**Record.** The total predictive accuracy that may ever be traded away for derivedness, across all future changes, never topped up. **DECLARED, not measured, and deliberately so** — it is a risk appetite, not a property of the data. Its scale is argued: 12 is about 3% of the current 384 and well inside the margin over uniform swing (384 against 530), so spending the whole budget cannot cost the model its headline claim. It exists because "derived but slightly worse" is otherwise a ratchet that walks the model downhill one individually-defensible step at a time. Amended in by the owner 2026-08-23; the instrument it sits inside is §1.82.

### §A16 · `poll_min_n` — 300 — 🔴

**Where.** `polling.screen`

**Now.** Declared at 300 and settable. Note it runs ahead of every scope test, so it also gates the national polls that drive the arrivals path.

**Record.** Below this a poll is recorded and never admitted. It exists because **readers will submit polls to the competition**, so the register is an untrusted-input surface and a three-person "poll" must not be priced as evidence at all. **DECLARED**, and settable. Note the companion rule that had to be got right: a poll with **no published sample size** is a WARNING, not an error — Ipsos never published the metro cut sizes for the nine 2016 readings `POLL_HOUSE_SD` is calibrated on, and the first version of the validator made that fatal and refused our own calibration set. §1.68.

### §A17 · `entrant_share` — `[0.01, 0.04, 0.12]` — 🟡

**Where.** `montecarlo.py`

**Now.** Unchanged at [0.01, 0.04, 0.12]; with `entrant_prob` it puts an expected 1.42% of the vote on a generic newcomer in every run.

**Record.** The arriving party's size. With `entrant_prob` it puts an expected **1.42%** of the vote on a generic newcomer in every run — which matched the AIC's actual 1.62% in 2016 almost exactly (measured: 1.39% drawn, 3.82 seats, against 1.62% and 4), and was 30× short of ActionSA.

### §A18 · `LEVEL_DF` — 7.0 — 🟡

**Where.** `montecarlo.py`

**Now.** Ships 7.0, live since 2026-08-17 and swept. The sweep cannot distinguish 7 from 30; §F narrows it to ν ∈ [5, 15] on four constraints.

**Record**, oldest first:

1. Degrees of freedom of the Student-t level shock. Sets how heavy every party's level tail is. Nothing was measured; it was 4.0 until this branch, and 3 or 6 are equally arguable. Moved to 7 because `exp(t₄)` has no finite mean and the seat allocator takes a mean.
2. **Until 2026-08-17 it was INERT** — bound as `def log_shock(..., df: float = LEVEL_DF)`, evaluated once at import, so a sweep at 2.5 / 4 / 7 / 30 / 200 / 1000 returned byte-identical output and every "this constant does nothing" reading of it was measuring 7.0 (§1.33, and the same shape as `entrant_prob` in §1.31). Now read at call time and measurable, and **the typed value survives the first sweep**: nine city-years at 400 draws give coherent seat error 316 and 6/9 beats-uniform-swing at df=3, **308 and 7/9 at df=7**, 308 and 6/9 at df=30. **Read that carefully: only df=3 is distinguishable.** 308 against 308 is one number twice, and the 400-draw figures in that sweep are the same ones §1.33 had to retract as noise — the committed run at 1500 draws is 312. What the sweep establishes is that the constant is now *live* and that a heavy tail (df=3) is worse; it does not distinguish 7 from 30, and nothing here argues for 7 over 30 except that `exp(t₄)` has no finite mean and 7 is the incumbent. The effect is where the constant claims to act — Johannesburg 2026 over 3,000 draws, MK's maximum drawn share 46.2% / 37.5% / 33.8% at df 3 / 7 / 1000 and the DA's realised sd(log) 0.2395 / 0.1886 / 0.1835 — and it is NOT what makes MK's seat band wide (8–53 at df=2.5, 8–57 at df=1000; that band is the within-pool Dirichlet and the correlated turnout copula). Downgraded 🔴 → 🟡: still typed, now swept.

### §A19 · how unplaced votes are spread over a party's zeroed pool cells — pool-size proportional — 🟡

**Where.** `pools.balance_within_bounds`

**Now.** Pool-size proportional, and there is no constant in it — the quantity is derived. Argued, not tested: no backtest can separate the three candidate rules.

**Record.** **The trigger was stated wrongly until 2026-08-17.** It is NOT the Duncan-Davis ceiling. Seeding fires when the **raw NNLS fit's column falls short of the party's known total** — a property of least squares present at every fit, with or without a bound: at Ekurhuleni 2016 with the box provably inert, **15 of 25 parties are still seeded and 0.41% of the city is still unplaced**. The bound is a *separate* condition and binds at five of ten fits. Where the unbounded answer is already legal it is now returned unchanged, so five of ten production fits take the pass-through. When the shortfall does have to be placed, the remainder has to go somewhere, and every candidate cell the fit had zeroed is equally consistent with the ward table. Spread in proportion to pool size — the same maximum-entropy rule `balance_margins` already applied to an all-zero column, so it is a continuation rather than a new invention. **There is no constant here**: a cell gets the pool's share of `party_votes − (what the clipped fit can place)`, which for the PA at Johannesburg 2021 is **159** votes of 27,346 — derived, not chosen. (The figure was typed as 163 on 2026-08-17 and did not reproduce; 159.1 follows from the weight 0.99418 that the same row quotes as 0.9942. A typed figure that disagrees with its own adjacent number is the exact failure `stats.toml` tokens exist to prevent.) Measured to be **not a lever** for any party the ward data can see (PA non-Coloured 0.582% / 0.582% / 0.692% under pool-size / headroom / uniform), and **decisive for micro-parties with a wholly blank column** — up to 0.37 of composition for DISRUPT_PARTY, which `identified()` already reports as unmeasured. Argued, not tested: no backtest can separate these three rules.

### §A20 · the §3.5 θ sanity ranges are violated by most of the forecast, and nothing acts on it — 🔴

**Where.** see `montecarlo.py`

**Now.** STILL UNACTED ON. The diagnostic prints against the model on every run and nothing reads it; nobody has decided whether the ranges or the draws are wrong.

**Record.** The run prints `implied θ outside §3.5 sanity ranges (share of draws)` and on the shipped 2026 forecast reports **ANC 57.7%, EFF 53.2%, Al Jama-ah 47.7%, PA 34.0%**. Over half the ANC's draws fall outside the model's own declared plausible range for its retention, and this appears nowhere in `MODEL-LOG`, `MACHINERY` or this register — it is printed and passed over, which is the same shape as the orphaned stat tokens and the `except Exception: pass`. Either the ranges are wrong (they are the plan's, written before the spine replaced `theta_mode`, and never revised) or the draws are — and until someone decides which, **a diagnostic the model prints against itself is being ignored**. Pre-existing, not introduced by any change this week.

### §A21 · the width statistic the report quotes — probit-SD, `sd(Φ⁻¹(u))` — 🟡

**Where.** `compare_history.pit_dispersion`

**Now.** Probit-SD is what the report quotes, measured on a fixture and ~5-10% attenuated at this model's shift. Its stated successor `dispersion_ratio` is now IN `compare_history` and emitted — this row has not been re-read since.

**Record.** The PIT's own variance is **not** shift-invariant — on a fixture with width held exactly right it reads 0.0829 → 0.0450 → 0.0240 at shifts of 0/+2/+3 against a nominal 0.0833, so a pure LEVEL error reads as 3.5× under-dispersion. Recommending it would have repeated the exact fault it was meant to diagnose, and it was recommended, by a review and by this project, before being caught. Probit-SD translates under a shift instead of compressing. It is **measured on a fixture, not on the model**: exact at zero shift, ~5-10% attenuated at this model's shift, so the true over-width is a little above the quoted 1.35×. `dispersion_ratio` (exact `sd(z)`) supersedes it once the artefact carries per-column `z`.

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** `dispersion_ratio` is now defined in `compare_history` and its value is written to the artefact, so the successor this row describes as pending has at least partly arrived. Nothing in this pass re-read the row; flagged for whoever does.

### §A22 · doc-vs-artefact tolerances — n exact · mean PIT ±0.012 · coverage ±2pp · vote bands ±0.5pp — 🟡

**Where.** `compare_history`, and the test that enforces it

**Now.** Unchanged, and deliberately tight enough that a legitimate re-run will demand the documents be updated.

**Record.** How far a documented figure may drift from `data/processed/history.json` before the document counts as stale. Typed, not measured — it is a judgement about how much re-run drift is tolerable, not a property of the model. **Deliberately tight enough to fire on a legitimate re-run**: the Monte Carlo spread on the ranks 1-3 absolute band has been ~1.5pp between runs against a ±0.5pp tolerance, so a re-run will demand the documents be updated. That is the intent — three reviews found stale figures, and the failure mode being guarded against is a document that quietly stops matching the artefact.

### §A23 · `level_shrink = 0.35` (with `level_shrink_scale = 0.04`) — 0.35 — 🟡

**Where.** `montecarlo.compress_levels`, run on the finished centre vector

**Now.** Adopted 2026-08-17 and unchanged; the largest single improvement this model has had. Two things keep it off green: an L1 form-selection leak, and a tail the uniform renormalisation over-feeds.

**Record**, oldest first:

1. How hard a party's central level is pulled down by its own size, the freed mass returned by renormalising.
2. **Adopted 2026-08-17 on the largest single improvement this model has had**: at nine city-years and the protocol 1500 draws, coherent seat error 312 → 264, CRPS 264.8 → 236.4, beats-uniform-swing 6/9 → 8/9; repeated at 600 draws it gives 308 → 268 and improves 7 of 9 city-years. It exists because ranks 1-3 (+32.30pp) and ranks 4-12 (−36.20pp) are one fault, not two — a share vector too widely spread. **What chose the number is not the scoreboard**: fitted on Johannesburg 2016 alone it gives 0.375 and transfers to the eight 2021 metros improving 6 of 8; leave-one-city-year-out gives 0.350 in all nine folds. Corroborated by a statistic it was not fitted on — mean PIT moves 0.425 → 0.464 at ranks 1-3 and 0.750 → 0.675 at ranks 4-12. **Two things keep it off green.** The functional form was chosen by screening four candidates against these same nine city-years, which rule 10 does bite on. And the uniform renormalisation over-feeds the tail: ranks 13+ go from unbiased to over-forecast (+0.78 → +8.68pp in the offline screen, under 1pp per city-year in the model). Three targeted redistributions all scored worse. MODEL-LOG §1.44.

### §A24 · `SHRINK = 2.0` — 2.0 — 🟢

**Where.** `levels.py`

**Now.** 2.0, measured optimal on forward-validated RMSE(log θ) and on the model's own three scores. Upgraded from 'pre-existing' — do not re-file it as untested.

**Record**, oldest first:

1. How much of a party's own θ record it keeps: `weight = worth/(worth + SHRINK)`.
2. **Never fitted or swept until 2026-08-17 — and it turns out to be optimal.** Forward validation (predict each LGE from strictly earlier cycles) gives RMSE(log θ) of .7216 / **.7149** / .7184 / .7238 / .7430 at ridge 1 / 2 / 3 / 4 / 8. Scored on the model itself, 1.0 is worse on all three measures: coherent seat error **314 against 312**, beats-uniform-swing **5/9 against 6/9**, CRPS **268.3 against 264.8**. Note the criterion conflict, which is the same one already registered against the spine's fit: **vote-weighted** forward RMSE prefers 1.0 (.2200 against .2311). Resolved in favour of the unweighted result because the model scored it that way. Upgraded 🟡 'pre-existing' → measured. MODEL-LOG §1.43.

### §A25 · the blend weight ignores the ρ record's evidence — `w = k/(worth_θ + k)` — 🟢

**Where.** `levels.spine`

**Now.** Deliberate, not an oversight: the symmetric form scores 338 against 312.

**Record.** `_worth_r` is computed and discarded with an underscore, so a party with a rich local record and thin θ is still pushed onto the national route. Looked like an oversight; **it is correct**. Symmetric form `(worth_ρ + k)/(worth_ρ + worth_θ + 2k)` scores 338 against 312, 4/9 against 6/9, CRPS 280.8 against 264.8, ranks 4-12 −40.98 against −37.2. Now deliberate rather than accidental.

### §A26 · `theta_prior` and `_shrunk` are different estimators of the same quantity — RESOLVED 2026-08-18 — ⚪

**Where.** `levels.py` (`theta_prior`, `_shrunk`)

**Now.** RESOLVED 2026-08-18. Both shrink toward `size_centre`, they agree to 1e-16, and no forecast moved.

**Record.** `_shrunk` shrank toward `size_centre`; `theta_prior` toward the flat `mu_all`, on a comment claiming "the record says the trend does not vary with size" — which is false, and is why `size_centre` exists (median θ 1.31 under 0.2% of the vote against 0.94 above 15%). The flat one was the wrong one and now uses `size_centre` too; the two agree to 1e-16. **It changed no forecast**, because the divergent quantity is the mode and nothing reads it: the spine reaches every party at every target so the fallback branch never fires, and the by-election clamp reads `low/mid` and `high/mid`, from which a shift in the centre cancels. Verified by shifting the whole band ×3 — byte-identical seat draws at 2021 and 2026 — and by four city-years identical to every digit. MODEL-LOG §1.49.

### §A27 · the capacity redistribution rule — proportional to mass held — 🔴

**Where.** `montecarlo.py:capped_targets`, the `t[free] += excess * t[free] / room` line

**Now.** Still proportional to mass held, and still unmeasured against the two defensible alternatives; the quantity moved is now counted on `capped_targets.moved`.

**Record.** **The larger of the two judgements in that function, and it was unregistered until 2026-08-17 while the 0.98 beside it was argued at length.** The margin decides how much mass moves; this decides where it goes. Measured on the live 2026 forecast, 600 draws: a mean **0.445%** of the city moves sideways (median 0.000%, p90 1.462%, max **6.933%**), firing in 39.2% of draws and averaging 1.136% over those — about three seats on a 270-seat council. Because it is proportional to what parties already hold, **the DA collects roughly a third and the ANC a fifth**, so the guard transfers the PA's truncated upside to the band already measured as over-forecast (ranks 1-3 mean PIT 0.431, signed +32.50pp) — and correlates the DA's upside with the size of the PA's level shock. Two alternatives are equally defensible and **neither has been measured**: proportional to *headroom*, and proportional to *pool overlap with the offender* — the last being the only one of the three that respects where the displaced votes could have gone. Now counted on `capped_targets.moved`.

### §A28 · `POOL_CAPACITY_MARGIN` — 0.98 — 🔴

**Where.** `montecarlo.py` (`capped_targets`)

**Now.** Ships 0.98, one full step clear of a measured cliff. It is the guard, not the cure — the cause is an upstream corner solution in the ecological fit.

**Record**, oldest first:

1. How close to a party's own pool capacity the IPF may be asked to go before the excess is water-filled onto the parties that can hold it.
2. **The judgement here is not really the 0.98 — it is what to do when the level layer and the pool layer disagree, and until 2026-08-17 the answer was `except Exception: pass` and it fired in 41.8% of the live 2026 forecast's draws** (§1.33). The disagreement is real and is NOT fixed by this: the PA belongs to exactly one pool (Coloured, weight 1.0, `identified=False` at 2026), that pool casts ~66,700 votes, and the spine + by-election blend ask for ~68,000 (a third contributor, `pa_contestation_uplift`, was deleted 2026-08-18) — 102% of every Coloured vote in the city. The cause is upstream in the ecological fit (a corner solution 10.5pp above the PA's own Duncan-Davis ceiling, never projected back); this row is the guard, not the cure. 0.98 is a round number one full step clear of a cliff: measured on the 2026 forecast at 600 draws, the failure rate is 41.5% at margin 1.0000, 41.5% at 0.9999, 39.8% at 0.995, 37.0% at 0.991 and **0.0% at 0.990 and at 0.980**. The cliff means the last percent is a convergence-rate problem against `balance_margins`' 2000-iteration cap, not a feasibility one — so the safe margin is a function of that cap and 0.98 keeps a step in hand. Its cost is that a party pinned at capacity is forecast ~2% under the level the centres asked for.

### §A29 · `level_sd_default` — 0.45 — 🟡

**Where.** `montecarlo.py`

**Now.** Declared in `DEFAULTS` since §1.63 and MEASURED inert: perturbed to 1.60 the output is byte-identical, because `theta_prior` gives every party in the baseline an sd.

**Record**, oldest first:

1. The level spread for a party with no measured `sd(log θ)`. Typed. Narrower than it looks: `levels.theta_prior` gives every party in the baseline an `sd`, so this binds only on parties outside it.
2. **PROMOTED 2026-08-20 (§1.63), which was this row's own instruction.** It was read as `scenario.get("level_sd_default", 0.45)` and was in no `DEFAULTS`, so it was frozen at 0.45 and could not be moved by `--set` or a config file — the same defect as `arrival_group_draw` and `turnout_correlation`, all three found at once by the new `test_no_scenario_key_is_read_without_being_declared`. Declared at 0.45, so nothing moved. And the prediction in this row is now **confirmed by measurement**: perturbed to 1.60 it is byte-identical at 2021 and 2026, because the measured branch is taken for every party. It is in `EXPECTED_INERT` with that reason. A fallback that never fires is what you want; it matters only if the baseline ever stops covering the ballot.

### §A30 · Dirichlet floor — `1e-4` — 🟢

**Where.** `montecarlo.py` (`DIRICHLET_FLOOR`)

**Now.** 1e-4 — a numerical guard only. The 0.05 that manufactured ~5pp of citywide vote is gone.

**Record.** Was `0.05`, which was not a numerical guard but a claim: on Johannesburg 2021, 44 of the Black African pool's 52 members were floored and their collective share went from the 1.59% the model believed to **8.41%** — ~5pp of the citywide vote manufactured for parties the model itself puts near zero. Now floors only to keep the concentration positive, which is all numpy requires. **The register said `0.05` at `:863` for two days after the change.**

### §A31 · `_LOG_FLOOR` — 1e-6 — 🟡

**Where.** `pools.py`

**Now.** Unexercised and kept deliberately: every dimension declares exactly one census, so the branch never runs. A flat sweep of it is not a null about the value.

**Record.** The clip before the log in `composition_at`'s two-or-more-census interpolation. **UNEXERCISED, and kept deliberately** (owner, 2026-08-28): every dimension in `config/dimensions.toml` declares exactly one census, so the branch never executes — but it is capability a second census would need immediately, and the Stats SA correspondence is live on exactly that. A sweep of it returns flat because the branch is UNREACHABLE, which is not a null about the value. Invisible to `compare_history`'s serial-forcing guard (leading underscore) and correctly absent from `MODULE_CONSTANTS`. §1.119

### §A32 · turnout spread with one observation — `0.30` logits — 🟡

**Where.** `pools.py`

**Now.** Typed at 0.30 logits, and it binds at every 2016 target.

**Record.** When a city has only one prior local election, the turnout band's width is typed. **This is every 2016 target.**

### §A33 · `bye_weight_mode` — `"fixed"` — 🟡

**Where.** `montecarlo.py`

**Now.** Defaults to `fixed`. `inverse_variance` is built and derives the weight; switching it moves the published 2026 forecast and no backtest can score either — the owner's call.

**Record.** How the by-election reading is weighed against the spine. **`"fixed"` is `w_bye` above — typed, untested.** `"inverse_variance"` DERIVES it: combining two unbiased estimates, the minimum-variance weight on the second is `v₁/(v₁+v₂)`, with `v₁` from the θ band and `v₂ = sd²/n` from the contests. At joburg 2026 it runs **0.031 (ATM, 3 contests) to 0.722 (EFF, 11)** against the typed 0.40, moving **2.005pp** of centre — MK, whose 8 contests span a factor of 31, earns **0.216**. A measurement replacing a judgement, which is Key 3's currency. **Defaults to `fixed` because switching it moves the published 2026 forecast and NO backtest can score it** (`bye` is empty at all sixteen panel city-years). Adopted as a lever on the pollster's recommendation; the owner's call to enable. §1.121, §1.122

### §A34 · ~~turnout-adjusted by-election weighting~~ — ⚫ refused

**Where.** —

**Now.** CONSIDERED AND REFUSED 2026-08-28 with the measurement (leave-one-contest-out RMSE 36.46pp against uniform's 24.66pp). A per-party sensitivity is worth pre-registering; the uniform form is not.

**Record.** **CONSIDERED AND REFUSED 2026-08-28, with the measurement.** Leave-one-contest-out on the by-election data — the only out-of-sample test this channel will ever have before an election — gives RMSE **36.46pp against uniform's 24.66pp**. The aggregate hides the reason: it *helps* ANC, EFF, MK and AIC and is catastrophic for the **DA (47.30 → 78.98pp)**, because turnout sensitivity is **party-specific and signed** — DA **−0.925**, EFF **+0.842**, ANC **+0.720**. A uniform ratio applies one sign to every party. A PER-PARTY sensitivity is worth pre-registering; the uniform form is not. §1.122

### §A35 · `w_bye` — 0.40 — 🔴

**Where.** `montecarlo.py`

**Now.** Typed at 0.40, live in the 2026 forecast and inert in every backtest. Only the 2026 result can bound it.

**Record.** By-election blend weight. **Inert in every backtest** — `byelection_*.csv` only covers 2022-06-01 → 2026-02-25 — but live in the 2026 forecast, so it is untested by anything here.

### §A36 · ward→PR conversion of the by-election delta — ratio, clipped `[0.5, 2.0]`, above `pc > 0.001` — 🟡

**Where.** `montecarlo.py`

**Now.** Adopted 2026-08-28 on out-of-sample evidence. Not a chosen number — it reuses the population and clip `ward_pr_ratios` already applies.

**Record.** **Not a chosen number** — it reuses the population and clip `ward_pr_ratios` already applies. Adopted 2026-08-28 on out-of-sample evidence: over the 2016→2021 transition across eight metros the proportional conversion beats the additive one for parties above ~1% (RMSE 0.910 vs 1.096 at 1%, 1.107 vs 1.347 at 5%, 1.398 vs 1.677 size-weighted) and loses below it, because the ratio is then a quotient of two noisy numbers. §1.113, §1.114. Like `w_bye` itself, **no backtest can score it.**

### §A37 · `w_bye_local_ward` / `w_bye_local_pr` — 0.0 / 0.0 — 🟡

**Where.** `montecarlo.py`

**Now.** Built and disabled at 0.0 / 0.0. Untestable for the same reason as `w_bye`.

**Record.** Built, disabled. Untestable for the same reason.

### §A38 · `ward_noise_sd` — 0.10 — 🟡

**Where.** `montecarlo.py`

**Now.** Typed at 0.10 on an audit, never measured and never bounded.

**Record.** Lognormal noise on each ward×party tally before calling winners. Adopted on an audit, not measured.

### §A39 · `OVERHANG_DEDUCT_MAX_ROUNDS_SLACK` — 2 — 🟢

**Where.** `montecarlo.py`

**Now.** Derived, not chosen: any value ≥ 1 is equivalent.

**Record.** Slack on the `deduct` loop's round bound, which is `len(combined) + this`. The loop fixes at least one party per round and removes it from the pool, so it cannot outlast the parties; the slack covers the final round that fixes none. **DERIVED, not chosen** — the only free number is the slack, and any value ≥ 1 is equivalent.

### §A40 · `OVERHANG_LEVEL_MAX_ROUNDS` — 200 — 🟡

**Where.** `montecarlo.py`

**Now.** 200 rounds. Bounded on ROUNDS deliberately rather than on council size, because a magnitude off the real panel does not transfer to a toy.

**Record.** Round bound on the `level` rule's council growth, which had none and could not terminate (§1.97 F41, F44). **Bounded on ROUNDS deliberately, not on council size, and the first attempt proved why**: a cap of 4× `COUNCIL` was taken from the largest council a real regime run has produced (396 against a 270 base) and fired immediately on a 15-seat fixture where growing to ~150 is legitimate. A magnitude off the real panel does not transfer to a toy. Each round adds ≥1 seat and a converging case takes a handful, so 200 is far above any real path and carries no assumption about council size.

### §A41 · `turnout_pattern_blend` / `turnout_blend_jitter` / `turnout_noise_sd` — 0.5 / 0.25 / 0.08 — 🟡

**Where.** `montecarlo.py`

**Now.** Typed. The citywide effect of the 0.08 is ~0.003, i.e. nothing — but see §G-R5: the turnout knobs move 46 ward wins, so the citywide null is not the whole story.

**Record.** The per-VD turnout pattern. The review found `0.08` i.i.d. over 865 VDs (the review's figure of 855 matches no year — §1.93) contributes ~0.003 citywide, i.e. nothing.

### §A42 · the arrival boundary — "no baseline at all" — 🔴

**Where.** `montecarlo`, by omission

**Now.** Still nobody's choice. 16 of the 79 mid-ballot parties sit on the wrong side of it and carry +16.4pp of the −37.4pp band deficit.

**Record.** Which parties reach `pools.arrival_rules` rather than θ × baseline. A party with a *trace* in the preceding national election — 0.05–0.17% in that metro — is treated as a retention case, and θ near 0.9 pins it there. **16 of the 79 parties in ranks 4-12 are in this position and are under-forecast by more than 5×, carrying +16.4pp of the −37.4pp band deficit** (§1.31). The code already knows those records are worthless: `RELIABILITY_HALF = 0.002` gives a 0.07% baseline a reliability of 0.26. The arrival record for the same city-years says a typical arrival takes 1.64% (IQR 1.43–2.29%), which is close to what they got. **A boundary nobody chose is still a judgement call.**

### §A43 · `apply_city` never resets `DEFAULTS` — 🔴

**Where.** `montecarlo.py`

**Now.** Still true; harmless only while Johannesburg's sixteen scalars equal `DEFAULTS`, and guarded by a test that fails the moment they diverge.

**Record.** Six of the eight metro configs set no scalars, `cities/joburg.toml` sets sixteen, and `DEFAULTS` is a module global. So every city after Johannesburg in a multi-city run inherits Johannesburg's judgement values. Harmless **only** because those sixteen currently equal `DEFAULTS`. Guarded by `test_apply_city_does_not_leak_one_citys_scalars_into_the_next`, which fails the moment they diverge.

### §A44 · `MIN_HOME_SPLITS` + binary home/away — 2 — 🔴

**Where.** `pools.py`

**Now.** Unchanged: a measured gradient (0.611 / 0.315 / 0.289 / 0.103) modelled as two buckets.

**Record.** A splinter is either "at home" or "away", nothing between. ActionSA's fraction of the DA ran **0.611 / 0.315 / 0.289 / 0.103** across four metros — a gradient modelled as two buckets. This is why Tshwane's seed was 0.17% against an actual 9.28%.

### §A45 · the arrival-group mechanism's five typed constants — reach floor 0.02 · `total_log_sd` fallback 0.8 · α fallback 4.0 · group-total cap 0.45 · record row-drop n < 3 — 🔴

**Where.** `pools.arrival_group_spec`, `pools.arrival_group_record`, `montecarlo.make_drawer`

**Now.** Declared 2026-08-29, none swept. The `n < 3` record drop is live on the INCUMBENT path at every target; the 0.45 cap's 'never binding' comment is wrong at 2026 (5.7e-03 per draw).

**Record**, oldest first:

1. ⛔
2. **UNDECLARED UNTIL 2026-08-29** (§1.136). All five are **inline literals or `dict.get` defaults**, which `test_every_tunable_constant_is_in_the_judgement_register` is structurally blind to — the §1.86 widening covered parameter defaults, argparse, dataclass fields and top-level assigns, and stops there. **The `n < 3` drop is the most consequential**: it selects which metro-years enter the estimation record, so it sets `total_log_mean` (named `total_log_median` until 2026-09-06, when it held a mean), `total_log_sd`, `alpha` **and** `_arrival_total_prior`'s median — the last of which rescales every seeded arrival on the **INCUMBENT** path, so it is live at every target whether or not `arrival_group_draw` is on. The **0.02** reach floor decides what an arrival absent from the reach dict is worth. The **0.45** cap carries the code comment *"never binding"*, which was unmeasured: re-derived 2026-08-29, P(total > 0.45) = **9.4e-05** per draw on the 2021 specs, but **5.7e-03 at 2026**, where the record gains 2021's 19.99% and `total_log_sd` widens 0.928 → 1.154. So it is ~60× more likely to bind on the live forecast than on the panel it was checked against, and "never binding" should not be re-typed. The **0.8** fallback fires only at n=1 and never has. The **4.0** α fallback stands in for a record median of **4.357**. **ARGUED, NOT TESTED** — none has been swept, and until §1.136 the mechanism they parameterise had never produced a number.

### §A46 · the peer window that sizes every seeded arrival — ±0.25 of ward reach, minimum 8 comparators — 🔴

**Where.** `pools.arrival_rules.comparators`

**Now.** Declared 2026-08-29. Live in every backtest and in the 2026 forecast, not gated by `arrival_group_draw`, and the frequency of its whole-record fallback is unmeasured.

**Record.** Which historical arrivals count as comparable to this one, and therefore the size of **every seeded arrival** — the incumbent path, live in every backtest and in the 2026 forecast, **not** gated by `arrival_group_draw`. Falls back to the whole record when fewer than 8 peers are within the window, so the window's real effect is the frequency of that fallback, which is unmeasured. The register declares `ARRIVAL_BAND_LO`/`HI` — the band's *shape* — but not the rule choosing the observations the band is fitted to. Undeclared until 2026-08-29. **ARGUED, NOT TESTED.**

## B. Measured, but the form or the selection was chosen

The number came from data. The *shape* it was fitted in, or the criterion that
picked it, did not.

### §B1 · `SPINE_K = 1.0`, reciprocal form — 🔴

**Where.** `levels.py`

**Now.** 1.0, fitted leave-one-metro-out on a curve that is flat 0.5–1.5. A step function scored better out of sample and was rejected on structural grounds — which is why this is 🔴 despite being fitted.

**Record.** Fitted by leave-one-metro-out, and the curve is flat 0.5–1.5. But a **step function at `worth < 1.0` scored better out of sample (0.2300 against 0.2358)** and was rejected on structural grounds — a smooth weight was preferred to a cliff the data does not place anywhere. A better score overridden by an argument should not be self-certified.

### §B2 · Vote-weighted RMSE as the criterion — 🔴

**Where.** the #22 fit

**Now.** Unchanged: the weighting chose the winner, and must be stated whenever the spine's 14% gain is quoted.

**Record.** The spine's 14% gain is on **vote-weighted** RMSE(log). Unweighted it is roughly a wash (0.7092 against 0.7083). The weighting chose the winner, and should be stated whenever the 14% is quoted.

### §B3 · `SPLIT_SD_FLOOR = 0.90` — 🔴

**Where.** `pools.py`

**Now.** 0.90, and it overrides its own measurement at target 2016 while binding at neither 2021 nor 2026 — real work in the one fold where it is least justified.

**Record.** Floors the splinter band's log-spread. **Verified to override the measurement at target 2016** (pooled log-sd 0.286); it does not bind at 2021 (1.599) or 2026 (1.492). So the floor does real work in the one fold where it is least justified.

### §B4 · `TURNOUT_CORRELATION = 0.63` — 🟡

**Where.** `montecarlo.py`

**Now.** 0.63 applied as ONE constant to every city and pool pair. It supplies 4–12% of drawn variance in the shape a pool-turnout mechanism should have; why it matters so little is still not explained.

**Record.** Measured over 14 metro-transitions — but applied as **one constant to every city and every pool pair**, when the measurement itself shows +0.86…+0.91 among three pools and +0.21…+0.47 for the fourth. **The width budget (§1.48) finds the pool turnout copula supplies 4–12% of drawn variance**, most for the party most concentrated in one pool (PA ~94% Coloured, +0.124) and least for broad ones (ANC +0.050, DA +0.044) — the shape a pool-turnout mechanism should have, and evidence it works rather than merely runs. An earlier draft said "essentially nothing", which over-stated the precision and was wrong. **Why it matters so little is NOT explained.** The obvious hypothesis — that a common turnout factor divides out of a share — was tested and refuted: setting the correlation to 0.0 leaves the contribution unchanged (+0.055 against +0.050). Before this constant is argued over again, establish what it is supposed to move, and note that the ward layer is where the turnout knobs actually act.

### §B5 · Gaussian copula for pool turnout — 🟡

**Where.** `montecarlo.py:_tri_ppf`

**Now.** Conventional and unchanged. It has no tail dependence, which is a substantive assumption nothing has tested.

**Record.** The measurement gives a correlation; it does not give a dependence structure. A Gaussian copula is the conventional choice and has no tail dependence, which is a substantive assumption about whether pools collapse together.

### §B6 · `METRO_CODES` widened 2 → 8 — 🟡

**Where.** `levels.py`

**Now.** Eight metros. More evidence and no leakage, but it moves θ itself, so it is confounded with the spine in any before/after delta.

**Record.** θ and ρ are now read off eight metros rather than Johannesburg and Tshwane. More evidence, no leakage — but it changes θ itself, so it is **confounded with the spine** in any before/after backtest delta.

### §B7 · `alpha` per pool — 🟡

**Where.** `pools.dirichlet_alpha`

**Now.** The model's DOMINANT width lever, sweepable since §1.63 via `dirichlet_scale` and NOT retuned — the method-of-moments fit names 1.0. The ranks 4-12 half of the old 'a scalar cannot serve both bands' finding is WITHDRAWN.

**Record**, oldest first:

1. Fitted from historical within-pool concentration, then floored per party at `DIRICHLET_FLOOR` = 1e-4 (§A). Was 0.05, which was a claim rather than a guard.
2. **REGISTERED AS THE MODEL'S DOMINANT WIDTH LEVER, 2026-08-18 (§1.48):** the within-pool Dirichlet supplies **83–98% of drawn variance for every party except the ANC (67%) and DA (39%)**. It has been treated as a concentration guard and it is in fact what decides how wide the forecast is. Nothing has ever swept it against realised width.
3. **SWEEPABLE SINCE 2026-08-20** via `dirichlet_scale`, which multiplies every pool's fitted concentration (1.0 = the fit). Nine city-years at 600 draws: 0.5 gives 274 seats / CRPS 256.0, **1.0 gives 258 / 231.9**, 2.0 gives 260 / 222.1. It moves seat error, CRPS and both bands' width together, confirming §1.48's ablation was reading something real.
4. ~~**A scalar cannot serve both bands**: ranks 4-12 want 2.0 (sd(z) 0.974 against a nominal 1.0) and ranks 1-3 want about 1.0 (2.0 takes them from 0.844 to 1.191).~~
5. **The ranks 4-12 half is WITHDRAWN, 2026-08-20 (§1.56):** it was measured on the `claimed` population, which is forecast-selected and moves with this very lever (30 / 37 / 45 ranks 4-12 columns across the sweep). On the fixed `reference` population ranks 4-12 read sd(z) **1.553 / 1.940 / 2.267** — too NARROW, and getting worse as the scale rises. Ranks 1-3 are the same 27 columns in both populations and that half stands. The real trade is bulk against tail WITHIN ranks 4-12: sd(z) 1.940 with IQR-sd 0.595, and columns beyond|z|>3 going 3 → 4 → 9. Not retuned — CRPS prefers 2.0 and the seat difference is inside draw noise, but nothing OUTSIDE the scoreboard picks it and the method-of-moments fit names 1.0, so rule 10 applies. §1.55.

## C. Forced by arithmetic or identity — not judgement

### §C1 · `Σ base·θ = 1` in the IPF — 🟢

**Where.** `fold.calibrate_theta`

**Now.** Forced: predicted citywide shares are shares.

**Record.** Predicted citywide shares are shares. The iteration was otherwise scale-degenerate and drifted four orders of magnitude.

### §C2 · Splinter fraction capped at 1.0 of parent — 🟢

**Where.** `pools._band_from`

**Now.** Forced: a party cannot take 117% of the vote its parent had.

**Record.** A party cannot take 117% of the vote its parent had.

### §C3 · Turnout band in logit space — 🟢

**Where.** `pools.turnout_band`

**Now.** A scale choice, and the standard one. Note it REMOVES caps rather than adding them — which §F's `TURNOUT_DRAW_FLOOR`/`TURNOUT_DRAW_CEILING` row contradicts, and says so.

**Record.** A scale choice, but the standard one for a proportion, and it **removes** caps rather than adding one — no observed-maximum cap, no 1.0 cap.

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** §F34 registers `TURNOUT_DRAW_FLOOR` and `TURNOUT_DRAW_CEILING` — hard caps applied to turnout in every draw — and says in terms that they contradict this row. Both are left exactly as written: the contradiction is the finding, and resolving it is a judgement, not a tidy-up.

### §C4 · `LEVEL_FLOOR = 1e-6` vs `SHARE_FLOOR = 0.002` — 🟢

**Where.** `fold.py`

**Now.** Two separate floors, deliberately. On its own it fixed nothing — the 42 phantom seats were the scale drift above it.

**Record.** Separating the level floor from the deviation floor. Note it fixed **nothing** on its own — the 42 phantom seats were the scale drift above.

### §C5 · `LOG_CHI2_BIAS = 1.887365` — 🟢

**Where.** `levels.py`, **documented and deliberately unused**

**Now.** Correct, derived, and DELIBERATELY NOT APPLIED: applying it makes the model worse on every metric, because the record it reproduces is marginal and this layer is conditional.

**Record.** Not a choice at all: `exp(ψ(½)/−2 + …)`, i.e. `exp(1.270363/2)`, the exact factor by which recovering a dispersion from a least-squares line through `log(residual²)` understates it, since `E[log χ²₁] = ψ(½) + log 2 = −1.270363`. **It is correct and it is not applied**: applying it makes the model worse on every metric, because the record it would reproduce is a MARGINAL dispersion and this layer is CONDITIONAL. It is carried in the code so that the next person to notice the fit is too narrow finds the measurement instead of redoing it. §1.50.

## D. In the reporting, not the model

These shape what a reader concludes and are easy to mistake for findings.

### §D1 · ENTRANT relabelling

**Where.** `diagnose.py`

**Now.** In place, and asserted by `test_the_generic_entrant_is_relabelled_wherever_it_is_reported`.

**Record.** The model draws a *generic* entrant, so scoring maps it onto whichever party arrived from nothing. **The first version of `diagnose.py` did not do this** and reported Johannesburg 2016's AIC as 0.00% predicted against 1.62% actual (a total miss) *and* ENTRANT as 1.46% against 0.00% (pure phantom). They are the same forecast, and the model was within 0.17pp. Fixed; the corrected total PR vote error is 22.13pp, not 25.04pp.

### §D2 · Mean vs median as the point forecast

**Where.** `compare_history.py`

**Now.** Both are now shown; they differ ~5× for small parties.

**Record.** They differ ~5× for small parties. Reporting the median alone makes the model look far worse at the bottom of the ballot. Both are now shown.

### §D3 · "ruled out" threshold

**Where.** `diagnose.py`, `p < 0.02`

**Now.** Typed at p < 0.02.

**Record.** Separates a ward lost in a close contest from one the model excluded. The 2% is typed.

### §D4 · anomaly thresholds

**Where.** `sweep.py`

**Now.** All typed.

**Record.** `actual ≥ 3` seats for "missed entirely", `≥ 2` phantom seats, 10% of council for "does not add up", PIT ≤ 0.01 / ≥ 0.99. All typed.

### §D5 · signed-only rank bands

**Where.** `compare_history.rank_bands`, until 2026-08-17

**Now.** Retired: both the signed and the absolute column are now printed. This row is why §D exists — a reporting choice, argued in a docstring, decided what four months of work looked at.

**Record.** The band statistic was a SIGNED sum of per-party error, and its docstring defended the choice. The sign is a finding; a signed sum is not a measure of error. **Johannesburg 2021 ranks 1-3: +1.32pp signed, 26.50pp absolute** — ANC +6.53 and DA +7.39 cancelling ActionSA −12.59 — so the model's worst city-year on seats (104) was the band table's second-best row, and the nine-city-year total understated top-of-ballot error by 2.2× (+32.50 against 72.06). Both columns are now printed. This row is the reason §D exists: it was a reporting choice, it was argued in a docstring, and it decided what four months of work looked at.

### §D6 · phantom mass reported nowhere

**Where.** `compare_history.rank_bands`

**Now.** Now a column and a total; it was printed nowhere and was 6.53pp across the nine city-years.

**Record.** The bands iterate the parties that stood, so share given to a party that did not stand — including the generic `ENTRANT` where nobody arrived — fell outside all three bands and was printed nowhere. 6.53pp across the nine city-years, and the reason the signed bands summed to −6.53pp instead of zero. Now a column and a total.

### §D7 · which columns test calibration

**Where.** `compare_history.POPULATIONS` / `score.CLAIM_FRACTION` = 0.50

**Now.** Four populations are reported. `reference` is the ONLY one a before/after comparison may be quoted on; `seat_holders` is outcome-selected, inflated, and labelled so wherever quoted.

**Record.** **Four** populations are reported, not one, because the choice changes the answer and no single choice is neutral-and-undiluted. `reference` (INPUT-selected — fixed, and the only one a BEFORE/AFTER comparison may be quoted on) · `claimed` (forecast-selected: neutral for ONE forecaster, and the answer to "is this model calibrated") · `seat_holders` (outcome-selected: zero is the bottom of the support, so it reads high even for a perfect forecaster — **inflated, and labelled as such wherever quoted**) · `all` (mixed, diluted by ~200 parties correctly at zero). The 0.50 claim fraction is `score.py`'s and is itself typed. **`claimed` moves with the forecaster** — 58 / 67 / 81 columns across a `dirichlet_scale` sweep — and selects away from the model's worst columns, which is why `reference` exists. §1.56.

### §D8 · what puts a party in the `reference` population — `REFERENCE_SHARE` = 0.0025 · `REFERENCE_SLATE` = 0.25 — 🔴

**Where.** `compare_history.reference_universe`

**Now.** Both typed. The share cut is safe (below every metro's PR quota); the slate cut is the one to attack, and it moves no forecast — only which columns a width comparison is read on.

**Record.** The fixed calibration denominator: a party is in if it took ≥0.25% of the combined ward+PR vote at the **previous** local election, or stands in ≥25% of this election's wards. Both are ex-ante facts — a published result and a nomination list — so neither can move when a lever moves; measured, the population is **252 columns at every `dirichlet_scale` setting**, 225 of them with a defined `z`. **Both numbers are typed.** The share cut is the safer one: it sits below every metro's PR quota (Johannesburg's 270 seats put it near 0.37%), so no party that could take a PR seat on its previous showing is excluded. **The slate cut is the one to attack.** On a strict reading a party can win a WARD seat with one ward, so the principled threshold is "on the ballot at all" — which admits 24 to 57 parties a city-year, almost all zero on both sides, and reproduces exactly the dilution that makes `all` untestable. A quarter-slate is a judgement about plausibility, not a derivation. Sensitivity over the nine city-years: **252 columns at 0.25, 232 at 0.50, 211 at 0.75.** It moves no forecast — it decides which columns a width comparison is read on, which is how §1.55 came to record a backwards result. §1.56.

### §D9 · `BLEND_W` — 1.0 — 🟢

**Where.** `benchmarks.py`, `blended_swing`

**Now.** 1.0, fitted leave-one-city-year-out to the boundary of the family: the optimal blend IS uniform swing. The one constant here legitimately fitted on the scoreboard, because it touches no forecast.

**Record.** How much of the national swing the `blended-swing` reference carries: `prev + w · swing`, which is what Murphy's convex combination of persistence and uniform swing collapses to. **Fitted leave-one-city-year-out, and the answer is the boundary of the family** — coherent-comparable seat error is monotone decreasing in `w` across the whole interval (594 at 0.0, 456 at 0.5, 382 at 0.9, **376 at 1.0**), so the optimal blend IS uniform swing and no damping helps. The unconstrained grid optimum `w = 1.05` (372) is not a blend but an amplified swing, is worth 4 seats in 376, sits on a flat plateau, and **loses leave-one-out: 380 against 376.** This is the one constant in the repository legitimately fitted ON the scoreboard — rule 10 governs constants inside the MODEL, and a REFERENCE forecast should be as strong as it honestly can be before the model is measured against it. It touches no forecast. Its value is that it settles the "your baselines are strawmen" objection with a measurement rather than an argument. MODEL-LOG §1.57.

### §D10 · pooled AND per rank band, not pooled alone

**Where.** `compare_history.pooled_by_band`

**Now.** Both are printed; a single city-year row is 4–15 columns of noise and is labelled as such.

**Record.** Coverage and PIT are quoted POOLED over all nine city-years (n≈132 seat-holding columns). Per city-year they are four to fifteen columns and are noise — Johannesburg 2021 reads 12/62/75, Cape Town 57/100/100 — and are printed only for provenance, labelled as noise. A reader who quotes a single city-year row is quoting nothing.

### §D11 · the pooled figure must NOT be read alone — 🟡

**Where.** `compare_history.pooled_by_band`, `ITERATING.md` rule 8

**Now.** `ITERATING.md` rule 8. The pooled mean PIT was the average of two opposite faults; both coverage statistics are printed and the PIT-corrected one is labelled the width verdict.

**Record.** Added 2026-08-17 after the pooled mean PIT was found to be **the average of two opposite faults**: ranks 1-3 read 0.431 (over-forecast) and ranks 4-12 read 0.750 (under-forecast), pooling to 0.588 — and both cluster-bootstrap CIs exclude 0.50 in opposite directions. A signed average across bands with opposite errors is not a measure of bias, for exactly the reason a signed sum is not a measure of error — **and this project shipped both faults, two days apart, in two different statistics.** The width verdict is band-dependent too: at ranks 1-3 a nominal 50% interval covers 70%, at ranks 4-12 it covers 27% on the PIT-corrected measure. Note the two coverage statistics differ: `score.coverage`'s empirical quantile interval reports 0.462 for the same band, because on integer seats it must include whole endpoints and over-covers by 19 points where parties hold one to ten seats. The report prints both and labels the PIT-corrected one as the width verdict.

### §D12 · PIT seed derived per city-year

**Where.** `compare_history._pit_seed`

**Now.** Derived from the city-year name by CRC32; reproducible, and it cannot change a conclusion.

**Record.** `score.pit_values` defaults to one fixed seed, so every city-year would give its k-th column the same uniform and the pooled histogram would rest on nine draws rather than ~130. The seed is derived from the city-year name (CRC32) so the report stays reproducible and does not depend on which cities were run. Typed base, arbitrary, and it cannot change any conclusion — only the noise on it.

### §D13 · `top = 12` parties per table

**Where.** `compare_history.py`

**Now.** Cosmetic here — but it is what makes `validation_2021.json` not comparable.

**Record.** Cosmetic — but it is also what makes `validation_2021.json` **not comparable**: that file stores only 12 parties while these targets have 15–24 seat-winners, so its seat error is truncated.

### §D14 · seat error summed over all parties

**Where.** `compare_history.py`

**Now.** Unchanged; parties that won nothing contribute 0, so the wider denominator does not inflate it.

**Record.** The model's own figure spans all 69 parties; it contributes **0** from parties that won nothing, so the wider denominator does not inflate it.

### §D15 · modal ward winner = "the model's call"

**Where.** `diagnose.py`

**Now.** A defensible reading of a probabilistic forecast, and it is a reading.

**Record.** A defensible reading of a probabilistic forecast, but it is a reading.

### §D16 · `FRESHNESS_GRACE_S` = 300s — 🟡

**Where.** `stats.py`, `freshness_problems`

**Now.** Typed at 300s. ARGUED, NOT TESTED — the harness cannot score a publishing guard; the strong half of the check catches the 16-day defect with no window at all.

**Record.** How far a token's backing file may lag `forecast_summary.json` before the site build refuses to publish. **ARGUED, NOT TESTED — the harness cannot score a publishing guard.** It is not a tolerance for staleness: it exists because `overhang_regimes.py` writes each `regime_<rule>_summary.json` and only then re-runs the default rule to restore the reference, so on a correct build the copies legitimately lag by one Monte Carlo. `overhang_regimes.py` now re-stamps them afterwards, which is what makes a window this small safe; 300s absorbs filesystem timestamp granularity and a hand-run `cp`, and nothing longer. The defect it was written for was **16 days**, and the strong half of the check — extinct scenario keys — catches that one with no window at all. Typed. MODEL-LOG §1.89.

### §D17 · `CELL_AREA_FACTOR` = 1.0 — 🟡

**Where.** `hex_cartogram.py`

**Now.** Typed at 1.0. ARGUED, NOT TESTED, and a trade between two goods rather than right against wrong. Touches no forecast.

**Record.** How big each hexagon is, as a multiple of *city area / 135*. At 1.0 the tiles cover the geographic map's own footprint, which is what lets the two maps be toggled between rather than merely shown near each other; the cost is longer displacements, because the grid is as tight as it can be. Measured trade-off on Johannesburg: mean displacement 22.5px at 0.70, 28.1px at 0.85, **36.2px at 1.00**. **ARGUED, NOT TESTED** — the harness cannot score a figure, and the choice is between two goods (footprint fidelity against positional fidelity), not between right and wrong. It touches no forecast. MODEL-LOG §1.90.

### §D18 · `GRID_MARGIN_CELLS` = 2 — 🟢

**Where.** `hex_cartogram.py`

**Now.** Typed at 2 and purely operational: the Johannesburg optimum uses no cell in the outermost ring.

**Record.** How far the candidate hex grid extends past the wards' bounding box. It buys the assignment room to push a peripheral ward outward rather than displacing a whole chain inward. Purely operational: at the Johannesburg layout the optimum uses no cell in the outermost ring, so raising it changes nothing and lowering it to 0 would begin to bind. Typed.

### §D19 · `SAFE` / `STRONG` / `LEAN` = 0.90 / 0.75 / 0.60 — 🟢

**Where.** `hex_cartogram.py`

**Now.** Copies of `render_map.main`'s tiers, held in step by `test_the_two_maps_agree_on_the_confidence_tiers`. Not an independent judgement.

**Record.** The four confidence tiers. **These are NOT free here** — they are `render_map.main`'s, re-declared because they are inline in that function and cannot be imported, and `test_the_two_maps_agree_on_the_confidence_tiers` reads `render_map.py`'s source and fails if the two drift apart. The tiers themselves are a presentation call made in the 2026-08-06 user review; this row exists so that the copy is not mistaken for an independent judgement.

### §D20 · `TIP_FLOOR` = 0.05 · `OTHER_FLOOR` = 0.005 — 🟢

**Where.** `hex_cartogram.py`

**Now.** Same provenance and same drift guard as the tiers above.

**Record.** A party is named in a ward's tooltip at ≥5% of simulations, and the swept-up "other" remainder is shown at ≥0.5%. Same provenance and same drift guard as the tier thresholds above: typed in `render_map.main`, re-declared here, checked against that source.

### §D21 · `MAX_DISPLACEMENT_RADII` = 5.0 — 🟡

**Where.** `tests/test_hex_cartogram.py`

**Now.** Typed at 5.0 radii — a regression guard rather than a claim, and it separates the optimal assignment (3.8) from the greedy one (8.8).

**Record.** The bound at which a cartogram has stopped being a map: no hexagon may sit further than five hex radii from its ward's true centroid. In radii rather than pixels so it does not move with the figure's size. Johannesburg's worst ward is at 3.8 under the optimal assignment and **8.8 under the greedy one**, so the bound separates the two — which is what it is for. Typed, and a regression guard rather than a claim.

## E. What is genuinely from the record

For contrast, and because the list above is not the whole model: θ and ρ and
their shrinkage; the spine's blend weight; pool composition (Census 2022); pool
size (the published roll); the turnout **centre** (the city's last local
election); the turnout **correlation** (14 metro-transitions); the splinter
fractions; the arrival record; contestation (nomination lists); γ (the folds);
ward/PR split ratios; and the seat allocator, which is statute.

---

## F. The rest of the tunable constants

Added 2026-08-16 after an audit found **27 constants named in neither register**,
one hour after CLAUDE.md said the record changes in the same commit as the code.
`tests/test_regressions.py::test_every_tunable_constant_is_in_the_judgement_register`
now fails the build if any is missing, which is the only version of that rule
that survives contact with a long session.

### §F1 · `DIRICHLET_FLOOR` — 1e-4 — 🟢

**Now.** 1e-4 and inert as committed — but it has a SECOND consumer that floors a CONCENTRATION rather than a mean, and `PERTURB` sweeps it to 0.05 where that would bind.

**Record.** floor on the Dirichlet MEAN vector, so `E[X]` is exactly the vector asked for — **and it has a SECOND consumer that floors a CONCENTRATION, not a mean** (`make_drawer`'s arrival-group split). Inert at the committed 1e-4; `PERTURB` sweeps `dirichlet_floor` to 0.05, where it would bind on any group member sitting on the 0.02 reach floor and silently multiply its concentration. The *name* was corrected there and the *unit* was not. §1.136. Was 0.05, which manufactured ~5pp of citywide vote

### §F2 · ~~`POLL_RMS_ERROR`~~ — ~~0.030~~ — ⚫ deleted

**Now.** DELETED 2026-08-28. Read by nothing; the constant the tests assert against is its neighbour `POLL_RMS_ERROR_2016`.

**Record.** **DELETED 2026-08-28 (§1.119.)** Read by nothing in `src/`. This row previously kept it as "the CALIBRATION TARGET the decomposition is checked against" — **that was its neighbour**: `tests/test_polling_sd.py` asserts against `POLL_RMS_ERROR_2016` (0.0303), a different constant, which survives. The derivation (Ipsos's nine 2016 metro readings, RMS 3.03pp) is kept as a comment in `polling.py`, because `POLL_HOUSE_SD` is that number with the sampling term removed. Recorded in `tests/test_register_matches_code.py`'s `DELETED`.

### §F3 · `POLL_HALF_LIFE_DAYS` — 120 — 🔴

**Now.** 120, declared. No SA metro series is long enough to fit it.

**Record.** recency half-life for aggregating several waves. **No SA metro series is long enough to fit this**; declared, not measured

### §F4 · `CAMPAIGN_WINDOW_DAYS` — 550 — 🟡

**Now.** 550, typed.

**Record.** how long before polling day an undated poll may still describe the same election

### §F5 · ~~`POLL_K`~~ — ⚪

**Now.** DELETED 2026-08-22 with the legacy poll path. The shape survives as `poll_house_k`.

**Record.** **DELETED 2026-08-22 (§1.68)** with the legacy poll path it served. It keyed a poll's weight on how much θ HISTORY a party had, `m/(worth+m)`; §1.67 replaced that with how PRECISE the two estimates are. The shape survives in `poll_house_k`, keyed on how many independent HOUSES stand behind a poll rather than on the party.

### §F6 · `SPLINTER_PARENT_WEIGHT` — 0.35 — 🔴

**Now.** 0.35, measured over 22 splinter-metro cases, no bootstrap, and stale since the archive grew (§A).

**Record.** share of a splinter's starting vector taken from its parent; measured over 22 splinter-metro cases

### §F7 · `_SIGN_EPS` — 1e-9 — 🟡

**Where.** `theta_residual.py`

**Now.** 1e-9, and it decides one of KEY 4's two failure triggers: six orders above the float dust a genuine no-op produced and six below the smallest real effect on record.

**Record.** `theta_residual.py`, in `key4_delta`. **Below this a metro-year cluster mean is float noise rather than a direction**, and the sign count — one of KEY 4's two failure triggers — ignores it. Set six orders of magnitude above the 1.6e-14 dust a genuine no-op arm produced (`THETA_WINDOW=3` at 2016, which reported "2 of 8 metro-years worse" off `polyfit` summation order, §1.126) and six below the smallest real effect on record (`WINDOW=3` at 2021, 0.0062). Registered because it decides an UNTRADEABLE floor and would otherwise be the next unregistered number

### §F8 · `LEVEL_DF` — 7.0 — 🟡

**Now.** BOUNDED 2026-08-29 to ν ∈ [5, 15] on four constraints, with the committed 7.0 in the middle. The honest label is no longer 'unmeasured' but 'not resolvable further on this panel'; a joint (κ, ν) fit was designed and NOT built.

**Record**, oldest first:

1. degrees of freedom of the level shock. Was 4.0, which has no finite mean.
2. **Inert until 2026-08-17** (§1.33).
3. **BOUNDED 2026-08-29 (§1.130): ν ∈ [5, 15], and the committed 7.0 is in the middle of it.** Four constraints, none needing more panel than exists: `exp(t_ν)` needs ν > 1 for a finite mean and the allocator takes a mean; `mean z²` has finite sampling variance only for ν > 4, so ν ≤ 4 invalidates one of the instruments §1.127 leans on; the seat sweep in §A is flat above ~5 (**316 and 6/9 at df=3, 308 and 7/9 at df=7, 308 and 6/9 at df=30**), because the within-pool Dirichlet supplies 83–98% of drawn variance for every party but the ANC and DA so moving ν from 3 to 30 moves the 95th and 99th percentiles of the total shock by **under 1%**; and the scale-free shape ratio R rejects ν ≥ 15 at 2021 (p = 0.022). **A joint (κ, ν) fit was designed and NOT built** — simulated, its 95% profile interval at the true ν=7 is [2.80, ∞) and unbounded 66% of the time, its cluster bootstrap covers 45–58%, and `sd_for`'s per-bin width heterogeneity (spread of log κ* = 0.565 at 2016 against 0.069 at 2021) manufactures ν̂ ≈ 3–4 out of GAUSSIAN data. The honest label is no longer *unmeasured* but **measured to an interval that contains it and not resolvable further on this panel**

### §F9 · `POOL_CAPACITY_MARGIN` — 0.98 — 🔴

**Now.** See §A — a judgement about what to do when two layers disagree, not a tolerance.

**Record.** see §A — it is a judgement about what to do when two layers of the model disagree, not a tolerance

### §F10 · `balance_margins` `iters` / `tol` — 2000 / 1e-12 — 🟡

**Where.** `pools.py`

**Now.** 2000 / 1e-12. Nominally operational; registered because the cap is what turns an infeasible problem into an exception. 20,000 iterations move the failure rate 40.9% → 38.9%.

**Record.** `pools.py`. The IPF's budget and stopping rule. Nominally operational, registered because **the cap is what turns an infeasible problem into an exception** — and until 2026-08-17 that exception was swallowed on 41.8% of the 2026 forecast's draws. Slow convergence and infeasibility are not distinguishable from inside the function, and they were separated by measurement, not argument: 20,000 iterations at tol 1e-9 moved the failure rate 40.9% → 38.9%, i.e. essentially not at all

### §F11 · `SOLVE_TOL` — 1e-9 — 🟢

**Where.** `pools.py`

**Now.** Operational, and listed EXEMPT in the guard — named here so the exemption is visible in the register and not only in the test.

**Record.** `pools.py`. Tolerance on the gradient at the accepted ecological fit. Operational, and listed EXEMPT in `test_every_tunable_constant_is_in_the_judgement_register`; named here so the exemption is visible in the register and not only in the test

### §F12 · `PARTIAL_BALANCE_PASSES` — 200 — 🟡

**Now.** 200. A convergence budget that is not a converging sequence, so the number chooses how close to the boundary it gets.

**Record.** alternating row/column passes when the two margins cannot both hold. Operational (a convergence budget), but named here because it is not a converging sequence — it is approaching the boundary of an infeasible problem, so the number chooses how far it gets. Measured at Nelson Mandela Bay 2021 against 200: 30 passes differ by 186 votes of 364,000, 60 by 45.6, 100 by 16.7

### §F13 · `TURNOUT_CORRELATION` — 0.63 — 🟡

**Now.** 0.63, declared in `DEFAULTS` since §1.63 and asserted equal to the module constant at import. It MOVES the forecast, so it is a live lever.

**Record**, oldest first:

1. measured over 14 metro-transitions; applied as ONE constant to every city and pool pair.
2. **SWEEPABLE SINCE 2026-08-20 (§1.63)**: it was read as `scenario.get("turnout_correlation", TURNOUT_CORRELATION)` with no such key in `DEFAULTS`, so a registered constant carrying an acknowledged judgement could not be moved by `--set` or a config file. Now declared at 0.63 — the scenario key and the module constant are asserted equal at import, because two copies of one number is this repository's signature defect — and it MOVES the forecast, so it is a live lever rather than a frozen one

### §F14 · `SPINE_K` — 1.0 — 🔴

**Now.** See §B.

**Record.** see §B

### §F15 · `SHRINK` — 2.0 — 🟢

**Now.** Measured optimal 2026-08-17. Do not re-file it here as 'pre-existing'.

**Record.** **measured optimal 2026-08-17** on forward-validated RMSE(log θ) and on the model's own three scores; full entry in §A. Do not re-file it here as "pre-existing"

### §F16 · `RELIABILITY_HALF` — 0.002 — 🟡

**Now.** 0.002, a value inherited from the hard cut it replaced; only the smooth form is new, and it has never been swept.

**Record.** set to the hard 0.2% cut it replaced, so the *value* is inherited rather than chosen; the smooth form `share/(share + RELIABILITY_HALF)` is the change. Never swept

### §F17 · `SD_FLOOR`, `SD_CEILING` — 0.15, 1.20 — 🟡 (≥15%)

**Where.** `levels.py`, applied in `sd_for`

**Now.** 🟡 at ≥15% of the vote. On the corrected harness the width in use is 0.151 against a measured 0.273 [0.136, 0.386] — inside the interval but near its bottom, at 1.81×, binding on 32 of 64. Below 15% every interval EXCLUDES it.

**Record**, oldest first:

1. Clamps the size-fitted `sd(log θ)`.
2. **UNDERSTOOD 2026-08-18 (§1.50), and kept for a reason rather than a score.** It is not, as §1.45 read it, width hedging a level bias: the level bias was reduced twice (§1.44, §1.47) and the floor got MORE valuable, not less (off 268 seats / CRPS 234.5 against 258 / 231.9 at 0.15). It is roughly **the CONDITIONAL dispersion this layer should carry**, sitting between the raw fit (0.120 — too narrow, because recovering a dispersion from a line through log(residual²) is biased by a derivable exp(1.270363/2) = 1.8874) and the binned record (0.227 — too wide, because that is a MARGINAL dispersion and the within-pool Dirichlet independently supplies 39–98% of drawn variance). **Applying the derived correction makes the model worse on everything**: 258→268 seats, 231.9→246.8 CRPS, 7/9→6/9, ranks 4-12 sd(z) 0.856→0.522. Note also that it is not a top-of-ballot constant: ranks 1-3 want it OFF (sd(z) 0.952 against 0.844) and ranks 4-12 want it ON (0.856 against 0.786), and 0.15 is where that trade balances. Replacing it honestly needs a JOINT calibration of the layers against realised width, not a better θ dispersion.
3. **MEASURED 2026-08-20 (§1.59) — the assertion above is CORRECT, and it is the first time it has been tested.** `src/theta_residual.py` computes the forward-validated residual sd of log θ about the centre `theta_prior` actually used, cluster bootstrapped on metro-year: at or above 15% of the vote it is **0.138, 95% CI [0.084, 0.171]**, and the model uses 0.150 — inside the interval, against a marginal record of 0.222 and a chi-square-corrected fit of 0.260 which are both far outside. The floor binds on 20 of the 37 observations there and never below 5% of the vote, so it is a top-of-ballot constant that lands on the measurement — better defended than it was, still not derived. **🟢 for parties at or above 15%.** The confounding the review raised (applying the correction also stops the floor binding) does not touch the conclusion: 0.260 is refuted by an upper bound of 0.171 on its own.
4. **🟢 → 🟡 ON 2026-08-23 (§1.77): THE PROMOTION DOES NOT SURVIVE THE DOUBLED PANEL.** Re-measured on sixteen city-years and the tree restored per §1.75: at ≥15% of the vote the conditional sd is **0.273, 95% CI [0.136, 0.386]** over **64** observations, against 0.138 [0.084, 0.171] over 37 before, and the width in use is 0.158. The used width is still inside the interval — but the interval is now 0.250 wide instead of 0.087 and the model sits near its bottom rather than its middle, at a ratio of 1.73×. The floor binds on **26 of 64** rather than 20 of 37, a minority. Nothing about the prior changed; the panel did. This is the withdrawal of a claim, not evidence that the constant is wrong.
5. **RE-MEASURED 2026-08-28 (§1.124) AFTER THE HARNESS WAS CORRECTED TO USE `run_model`'s BASELINE** — it passed the raw citywide tally where the model drops off-ballot parties before `theta_prior`, which moves the fit for every party. The residual and its interval are unchanged (0.273 [0.136, 0.386], n=403); **the width in use at ≥15% is 0.151, not 0.158, the ratio is 1.81× and the floor binds on 32 of 64 rather than 26.** The correction narrows the top of the ballot and WIDENS everything below 5%, because the dropped parties sit at the small end of the size axis where the slope is steepest. Below 15% every one of the four intervals excludes the width in use. The 🟡 stands and the used width is still inside the ≥15% interval, near its bottom

### §F18 · the size-dependence of `sd_for` is wrong below 15% of the vote — a straight line in log(size) — 🔴

**Where.** `levels.py`, inside `theta_prior`

**Now.** The model is UNCHANGED and the fault is the FORM, not the residual. ⛔ No further functional form may be tried against these two folds, and this row's numbers are Form A's and must not be quoted.

**Record**, oldest first:

1. **MEASURED 2026-08-20 (§1.59), and it is the larger half of that entry.** The forward-validated conditional dispersion is **not monotone** in size — 0.915 / 0.737 / 0.448 / 0.663 / 0.138 across <0.2% / 0.2-1% / 1-5% / 5-15% / ≥15% — and a straight line cannot be right in the middle and at both ends. This one is anchored at the ends: **in all four bins below 15% the cluster-bootstrap interval EXCLUDES the width the model uses**, always too narrow, by 1.70× to 3.53×. The best-supported bins (n=96 and n=78) exclude it comfortably; the biggest ratio (5-15%) has n=14 and the widest interval and is the weakest of the four. Converges with §1.58, which measures the mid-ballot SEAT forecast as too narrow from completely different data. **The successor is a refit, not a new constant**: `sd_for` fits deviations from the COMMON centre and should fit the residual about the SHRUNK one. That is a fit to the forward-validated record, not to the scoreboard, so rule 10 permits it — and it will widen the mid-ballot, which CRPS will score as worse (§1.58: CRPS wants the forecast narrower all the way out). **REFIT BUILT AND REFUTED the same day (§1.62).** Two forms were tested against the pre-registered rule in §1.61 — the residual about the shrunk centre, leave-one-observation-out and leave-one-cycle-out — scored on held-out NLL at 2016 and 2021. The first loses BOTH folds; the second wins 2016 (0.682 against the committed 1.193) and loses 2021 (0.982 against 0.161), which the pre-registration calls undetermined. **The model is unchanged.** So the fault is the FORM, not the residual: the measured conditional dispersion is not monotone in size and a straight line in log(size) cannot be right in the middle and at both ends whatever it fits. **No further functional form may be tried against these two folds**
2. ⛔ **THE FIGURES IN THIS ROW ARE FORM A's** (Gaussian, without its ½log2π, on the raw baseline), and so is the 0.682/1.193/0.982/0.161 quartet above — the instrument was corrected on 2026-08-28 and the committed baselines are 1.1363 at 2016 and 1.1425 at 2021 (§1.124). The prohibition stands on its multiple-comparison reasoning, which does not depend on the numbers; the numbers must not be quoted. Re-measuring §1.62's two refits on the corrected instrument has NOT been done — two forms are already spent and a handful of trials makes a spurious two-of-two likely. Licensed next by more folds (ingest the pre-2011 archive for the other seven metros) or by a mechanism argument naming the shape in advance.

### §F19 · `level_floor` — 1e-6 — 🟢

**Now.** 1e-6; separates the level floor from the deviation floor.

**Record.** separates the level floor from the deviation floor

### §F20 · `level_shrink`, `level_shrink_scale` — 0.35, 0.04 — 🟡

**Now.** See §A. The scale is a SCALE, not a tuned constant — swept twentyfold with no cliff.

**Record.** the level shrink; see §A. The scale is a SCALE, not a tuned constant — swept twenty-fold, 0.02 to 0.40, the correction improves 7 of 9 at every value and there is no cliff

### §F21 · `dirichlet_floor`, `poll_k`, `spine_k` — 🟢

**Now.** Scenario keys mirroring the module constants so a sweep is reproducible. ⚠ This row also lists `poll_k`, which was DELETED on 2026-08-22 (§1.68) and is in no `DEFAULTS` — see the restructure note beneath.

**Record.** scenario keys mirroring the constants above, so a sweep is reproducible

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** `poll_k` was DELETED on 2026-08-22 (§F5, §F30) and is in no `DEFAULTS` — `montecarlo.DEFAULTS` carries `dirichlet_floor` and `spine_k` and not the third. This row still lists it as a live mirroring key, which is the `polling_lean` failure of §F26 repeated in the same section. The **register → code** guard cannot see it: `poll_k` sits in `test_register_matches_code.py`'s `DELETED` set, added so the obituary rows could name it, and that exemption is what licenses this row's false claim. Value and status left untouched.

### §F22 · `spine_k = 0` on a party with no θ evidence — `w_local = 0.0` — 🟡

**Now.** A CHOSEN limit (`w = 0`, pure national spine), inert at the shipped `spine_k = None` and reachable only by a sweep, which is what it exists for.

**Record.** **A CHOSEN LIMIT, not a derived one** (owner, 2026-08-28). `w = k / (worth + k)` is `0/0` when a party has both records and `worth = 0`, and it raised `ZeroDivisionError` (§1.97 F2). `w` weights the LOCAL route, so `k = 0` means "pure national spine". Taking `w = 0` keeps that meaning for **every** party. The limit from above — `w = 1` as `k → 0⁺` — was rejected: it would make `k = 0` mean pure-national for everyone *except* the parties with no θ evidence, which are precisely the ones the local route serves, so the lever would mean two things depending on who it was applied to. The owner's reasoning is on the record: *"ActionSA is a local party, the spine makes no sense there either."* **Inert at the shipped `spine_k = None` (k = 1.0), where `worth + k` is never zero** — it is reachable only by a sweep, which is what it exists for. Five parties at joburg 2026 are in this state: ASA, AHC, AFRICA_RESTORATION_ALLIANCE, BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA, FORUM_4_SERVICE_DELIVERY. §1.117

### §F23 · `turnout_noise_sd`, `turnout_blend_jitter` — 0.08, 0.25 — 🟡

**Now.** Typed; ~0.003 citywide, i.e. nothing.

**Record.** per-VD turnout pattern; the review measured `0.08` i.i.d. over 865 VDs (the review's figure of 855 matches no year — §1.93) as contributing ~0.003 citywide, i.e. nothing

### §F24 · `bye_local_cap`, `bye_tau_months` — 1.5, 18 — 🔴

**Now.** 1.5 / 18, inert in every backtest.

**Record.** by-election ward-local term; **inert in every backtest**

### §F25 · `w_bye_local_ward`, `w_bye_local_pr` — 0.0, 0.0 — 🟡

**Now.** Built, disabled, untestable.

**Record.** the ward-local by-election term: built, disabled, and untestable because no past target has by-election data at all

### §F26 · ~~`polling_lean`, `polling_span`~~ — ⚪

**Where.** **DELETED, and this row said "still wired" for days after they were gone (§1.69).** `grep -rn 'polling_lean\

**Now.** DELETED. This row said "still wired" for days after they were gone, which is why the register → code guard exists.

**Record.** polling_span' src/` returns only the comments recording their own deletion. This is exactly the failure the `poll_half_life_days` row already confesses to — *"this row previously named a constant that did not exist"* — repeated, and the guard could not catch it because `test_every_tunable_constant_is_in_the_judgement_register` only checks **code → register** and never **register → code**. `tests/test_register_matches_code.py` now checks the other direction.

### §F27 · `pa_contestation_uplift` — DELETED 2026-08-18 — ⚪

**Now.** DELETED 2026-08-18. The branch now falls back to the previous local election's measured contestation for every party, which makes it backtestable.

**Record.** a one-party constant: 1.25 on the PA's ward/PR ratio, in the `elif` for when the target's nomination lists are not published yet. **Live at 2026 and consumed by no backtest** — which was recorded here as a disclosure and is better read as the reason nothing could test it. Its observation was sound (the PA fought 52 of 135 wards while the model assumed 135) and is owed to every party, so the branch now falls back to the PREVIOUS local election's measured contestation for all of them. That makes it backtestable for the first time. MODEL-LOG §1.47

### §F28 · `MAX_SIGMA`, `MIN_SIGMA`, `NEW_PARTY_SIGMA` — 2.0, 0.15, 1.0 — 🟡

**Now.** Spread bounds for the `prior-lge-noise` BASELINE, not for the model.

**Record.** spread bounds for the `prior-lge-noise` BASELINE, not the model. A party with no earlier result gets 1.0 because a party that did not exist last cycle is the least predictable thing on the ballot

### §F29 · `MIN_SHARE`, `CLAIM_FRACTION`, `F_OTHER` — 0.005, 0.50, 1.30 — 🟡

**Now.** All three were filed under the wrong module once. `MIN_SHARE` is `gamma_recent.py`'s and is a CLAIM about the model, not reporting; `CLAIM_FRACTION` is `score.py`'s. ⚠ `F_OTHER` is no longer in `src/` at all — see the restructure note beneath.

**Record.** **All three were filed under the wrong module, and the row was corrected once without checking the other two (§1.69).** `CLAIM_FRACTION` = 0.50 is in `score.py` and selects the columns calibration is tested on (a seat in at least half this forecaster's draws) — corrected 2026-08-17. `MIN_SHARE` = 0.005 is in **`gamma_recent.py`**, not `stats.py`, and it is **not reporting**: a party below 0.5% gets no fitted γ and falls back to γ = 1.0, which is a claim about the model. `F_OTHER` = 1.30 is in **`leverage.py`**. Neither appears in `stats.py` or `benchmarks.py`, where this row put them from the day it was written

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** `F_OTHER` is no longer anywhere in `src/`. The module holding it was retired to `archive/retired-scripts/` on 2026-08-31 (MODEL-LOG §1.140) and the register was not revised in the same pass. The `MIN_SHARE` and `CLAIM_FRACTION` halves of this row still hold. Value and status left untouched.

### §F30 · ~~`poll_id`, `poll_weight`, `poll_k`~~ — ⚪

**Where.** `polls.json`

**Now.** DELETED 2026-08-22. The legacy path bypassed every admission rule in `polling.usable_for` and had never executed.

**Record.** **DELETED 2026-08-22 (§1.68).** The legacy path re-read `polls.json` directly and **bypassed `polling.usable_for` entirely** — no fieldwork-date check, no party-commissioned exclusion, no scope or city check, no election-declaration rule. `--set poll_id="da-internal-2026aug"` admitted the DA's own internal poll; `--set poll_id="ipsos-2016-lge-joburg"` at target 2021 admitted a five-year-stale one, which §1.66 measured at **+10.0 CRPS and +8 coherent seats**. It had also never executed — it referred to a local of `blended_centres` and raised `NameError` the instant `poll_weight` went above zero. Nothing is lost: letting a poll speak for a party the record cannot see is the arrivals path (48 coherent seats, §1.65), and applying a screened poll to every party is the metro path (§1.67).

### §F31 · `ALPHA_MIN_SHARE`, `ALPHA_FLOOR`, `ALPHA_CEILING`, `ALPHA_FALLBACK` — 0.01, 1.0, 200.0, 12.0 — 🔴

**Where.** `pools.dirichlet_alpha`

**Now.** Promoted from inline literals 2026-08-22, number-neutral. They are the SELECTION RULE feeding the dominant width lever, and none has ever been swept.

**Record.** `pools.dirichlet_alpha`. **The selection rule feeding what §B calls "the model's DOMINANT WIDTH LEVER"** (83–98% of drawn variance for every party except ANC and DA). `dirichlet_scale`, a multiplier on this function's OUTPUT, has been registered and swept for weeks; the four numbers deciding its INPUT were inline literals in the function body, where `test_every_tunable_constant_is_in_the_judgement_register` cannot see them — it reads module-level assignments and `DEFAULTS` only. The share cut is not a tidying detail and the function's own docstring says why: without it "every pool pinned to the 200 ceiling", i.e. the simulation far more confident than the evidence warrants. Promoted to module constants and resolved in the body 2026-08-22 (§1.69); **the promotion is number-neutral, verified at Johannesburg 2016 to every seat and CRPS figure.** Never swept

### §F32 · `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` — 0.25, 0.95 — 🔴

**Now.** 0.25 / 0.95, the triangular support of every seeded arrival. 25/95 rather than 10/90 or 5/95 is undefended and never swept.

**Record.** `pools`, consumed in `montecarlo` as `low, _, high = seed_band`. The triangular support of **every seeded arrival** — how wide an ActionSA-class party's band is. The long comment beside the code explains at length why the CENTRE moved from median to mean and why a `clip(reach, 0.05, 0.95)` was a disaster, and never mentions that the surviving percentile pair is itself a choice. 25/95 rather than 10/90 or 5/95 is undefended. Promoted §1.69

### §F33 · `BYE_MIN_WEIGHT` — 30.0 — 🔴

**Now.** 30.0, the admission gate on the WHOLE by-election channel, promoted from a bare literal. Same reach into the published forecast, same untestability, same status as `w_bye`.

**Record.** `montecarlo`, inside `blended_centres`. **The admission gate on the whole by-election channel.** `w_bye` = 0.40 is registered at 🔴 as live in the 2026 forecast and untested by anything here; the threshold deciding whether it fires *for a given party* sat beside it as a bare `30` and was not registered at all. Below this many weighted contests the by-election evidence is discarded silently. Same untestable branch, same reach into the published forecast, same status. Promoted §1.69

### §F34 · `TURNOUT_DRAW_FLOOR`, `TURNOUT_DRAW_CEILING` — 0.02, 0.95 — 🔴

**Now.** 0.02 / 0.95, applied per draw. They contradict §C's claim that the turnout band 'removes caps rather than adding one'; whether the ceiling ever binds is unmeasured.

**Record.** `montecarlo`. A hard floor and **ceiling on per-VD turnout in every draw**. Note what §C says about the turnout band: that it "**removes** caps rather than adding one — no observed-maximum cap, no 1.0 cap". These are caps, they are applied per draw, and the register did not know they existed. Promoted §1.69; whether the ceiling ever binds is not measured

### §F35 · `WARD_PR_RATIO_MIN`, `WARD_PR_RATIO_MAX` — 0.5, 2.0 — 🔴

**Now.** 0.5 / 2.0 — the clip that overrides the record §E says the ward/PR ratio comes from. How often it binds is unmeasured.

**Record.** `montecarlo`. Clip on the **ward/PR split-ticket ratio**, which multiplies the PR target to make the ward target and so drives ward wins and overhang. §E lists "ward/PR split ratios" as coming FROM THE RECORD — this is the clip that overrides the record where it disagrees, and it was undeclared. Promoted §1.69

### §F36 · `PROJECTED_METRO_SHARE` — eight per-metro shares of the national vote, 2021 values — 🔴

**Now.** The last observed value, so nothing is extrapolated; n = 2 and it fires only where no backtest can check it.

**Record.** `polling`. Makes `contested_share` resolve at a LIVE target, where neither half of its ratio exists — see §A. Two cycles is n = 2, so **nothing is extrapolated**: the projection is the last observed value and the 2016→2021 movement (−0.2% to −11.8% per metro) is the uncertainty on it. Fires only where no backtest can check it, exactly as `contestation_expand` does

### §F37 · `PAGE_SIZE` — 🟢

**Now.** Pagination. Reporting, not belief.

**Record.** pagination. Reporting, not belief

### §F38 · `REG_DRIFT_TOLERANCE` — 0.30 — 🔴

**Where.** `build_concordance.py`

**Now.** RECLASSIFIED 2026-08-24 from 🟢 reporting to 🔴: it reaches the forecast through `fold.suspect_vds` → `w_split` → γ. Declared, never measured, and not a `DEFAULTS` key, so no lever sweep can reach it.

**Record.** **RECLASSIFIED 2026-08-24 (§1.93). It was filed on this row as "the tolerance on a pinned stat before the site build warns — reporting, not belief", and it is nothing of the kind.** It is the threshold at which a VD *"is treated as possibly redrawn rather than assumed stable"*, and it reaches the model: `build_concordance.registration_drift` → the `registration_drift` flag → `vd_concordance.csv` → `fold.suspect_vds` → `fold.main`'s `w_split` weighting → the `w_split` down-weight → the fold parameter artefacts → γ → the forecast. `w_split` itself is 🔴 on this register, so the constant that decides WHICH VDs it applies to cannot be 🟢. **DECLARED, never measured, and never swept** — it is not a `DEFAULTS` key, so no lever sweep can reach it; it belongs in the never-swept batch (task #40). A green classification also priced it at ZERO in the Key 3 Derivedness Debt, which is the register's own stated purpose defeated. Its own comment says the looseness is deliberate because *"the flag feeds a down-weight, not an exclusion"* — that is an argument for the value, and an argument is exactly what this register exists to record rather than hide

## G. Allowable ranges — how far each call could defensibly move, and what sets the bound

Added 2026-08-22 at the owner's request. The register has always carried *value,
location and evidence*; it has never carried **how far the value could move
before it stopped being defensible**, which is the first thing a reviewer asks.

**The most useful column here is the empty one.** A constant with no defensible
range is not a constant with a wide range — it is a constant nobody has bounded,
and saying so is the point of this section. Roughly half of them are in that
state.

Ranges are grouped by **what kind of evidence bounds them**, because that is
what determines whether a range means anything:

| class | what it means |
|---|---|
| **R1 — interval** | measured with a confidence interval. The range IS the interval |
| **R2 — swept** | swept on the panel, and the range is where the score does not degrade |
| **R3 — forced** | arithmetic or an identity fixes it; there is no freedom |
| **R4 — record, no interval** | a point estimate off a record, with no bootstrap. A range would need one |
| **R5 — none** | typed. **No defensible range exists.** The row says what would create one |

### R1 — bounded by a measured interval

| call | value | allowable range | what sets it |
|---|---|---|---|
| `SD_FLOOR` | 0.15 | **[0.11, 0.30]** — *but see the caveat* | Forward-validated conditional sd(log θ) at ≥15% of the vote, cluster-bootstrapped on metro-year. §1.59 measured **0.138 [0.084, 0.171]** (n=37) on the old record. §1.77 re-measured **0.273 [0.136, 0.386]** (n=64) on sixteen city-years and the tree restored per §1.75. 0.15 is inside both. **§1.71's quoted 0.208 [0.114, 0.299] at n=370 DOES NOT REPRODUCE** — the residual count is 403 on the restored tree, with or without the Type A filter, while §1.71's own ≥15% binding count (26 of 64) matches today's exactly. It was measured against a tree state that cannot now be reconstructed, which is what §1.75 found had happened to `data/raw/elections/`. Quote §1.77's figures, not §1.71's** |
| `SPINE_K` | 1.0 | **[0.5, 1.5]** | Fitted leave-one-metro-out and the curve is **flat across that interval**. A flat optimum is a range, not a point — which is why the row is 🔴 despite being fitted |
| `POLL_HOUSE_SD` | 0.025 | **[0.022, 0.028]** | The non-sampling residual of Ipsos's nine 2016 metro readings, recomputed across a threefold range of assumed n: **2.16pp at n=500, 2.52 at 800, 2.77 at 1500**. The value is stable against the one thing about it that is unknown, which is what makes it quotable as measured |
| `level_shrink_scale` | 0.04 | **[0.02, 0.40]** | Swept twentyfold; the correction improves 7 of 9 city-years **at every value** and there is no cliff. A scale, not a tuned constant |

### R2 — bounded by a sweep on the panel

| call | value | allowable range | what sets it |
|---|---|---|---|
| `entrant_prob` | 0.25 | **[0.25, 0.29]**, and 0.25 is the only value that costs nothing | Two evidence sources disagree and the range is their disagreement. The arrival record gives **0.290** matching its median and **0.353** its mean (§1.31). The panel at 1500 draws gives **254 / 262 / 264** coherent seats at 0.25 / 0.290 / 0.353 and CRPS 232.7 / 234.3 / 236.1 (§1.69) — monotonically worse. *Worse does not ship* puts the ceiling at the incumbent. Above 0.35 is refuted; 0.55 is clearly worse (§1.31) |
| `dirichlet_scale` | 1.0 | **[1.0, 1.4]** on seats; unbounded above on CRPS | The method-of-moments fit names 1.0. Across 0.5 → 16 **CRPS falls monotonically 256.4 → 212.5 while coherent seats stay flat at 254–262**, then costs 4 seats at 1.4 and 8 at 2.0 (§1.55, §1.58). A width decision taken on CRPS alone runs to the end of the sweep — do not take one |
| `level_shrink` | 0.35 | **[0.2, 0.5]** | Chosen by leave-one-city-year-out. Its *functional form* was chosen by screening four candidates against all nine, which §1.44 records as an L1 leak — so the range is wider than the fit suggests |

### R3 — forced by arithmetic; no freedom

| call | value | bound | why |
|---|---|---|---|
| `dirichlet_floor` / `DIRICHLET_FLOOR` | 1e-4 | must be ≪ the smallest share | Floors the Dirichlet **mean** so `E[X]` is the vector asked for. Was 0.05, which manufactured ~5pp of citywide vote |
| `level_floor` | 1e-6 | numerical | separates the level floor from the deviation floor |
| `LEVEL_DF` | 7.0 | **> 2 for a finite mean, > 4 for finite kurtosis** | Was 4.0. Below 2 the level shock has no mean at all. Above ~30 it is Gaussian and the parameter stops meaning anything. **Never swept live** — it was frozen at four call sites until §1.33 |
| `POOL_CAPACITY_MARGIN` | 0.98 | (0, 1] | A judgement about what to do when two layers disagree, not a tolerance. Never swept |
| `SOLVE_TOL`, `PARTIAL_BALANCE_PASSES` | 1e-9, 200 | operational | 30 passes differ from 200 by 186 votes of 364,000; 60 by 45.6; 100 by 16.7 |

### R4 — a point off a record, with no interval

**Every row here would get a real range from one bootstrap.** None has had one.

| call | value | measured on | why there is no range yet |
|---|---|---|---|
| `TURNOUT_CORRELATION` | 0.63 | 14 metro-transitions | No bootstrap, and **the archive has grown since** — §1.71 flags it as stale. Applied as ONE constant to every city and pool pair |
| `SPLINTER_PARENT_WEIGHT` | 0.35 | 22 splinter-metro cases | No bootstrap, and stale for the same reason. **And the comparative literature says the covariate is wrong**: rump/splinter shares are predicted by the defecting-legislator share, not a flat fraction (§1.73) |
| `contestation_expand` | 0.220 | eight-metro slate record, median | Median of a distribution whose spread is not reported. 65.5% of parties expand |
| `SHRINK` | 2.0 | forward-validated RMSE(log θ) | Measured optimal, but on the record now under question |
| `RELIABILITY_HALF` | 0.002 | **inherited, not chosen** | Set to the hard 0.2% cut it replaced, so the *value* is inherited and only the smooth form is new. **Never swept** |
| `SPLIT_SD_FLOOR` | 0.90 | — | **Verified to OVERRIDE its own measurement at target 2016** (pooled log-sd 0.286). Does not bind at 2021 (1.599) or 2026 (1.492). So it does real work in the one fold where it is least justified |

### R5 — typed. No defensible range exists.

**This is the important table.** Each of these is a number somebody chose, and
the honest range is "unknown". The last column is what would produce one.

| call | value | what would create a range |
|---|---|---|
| `w_bye` | 0.40 | Nothing available. The by-election window is 2022-06 to 2026-02, so **no past target has any by-election data at all** — it is live in the 2026 forecast and inert in every backtest. Only the 2026 result can bound it |
| `w_bye_local_ward`, `w_bye_local_pr` | 0.0, 0.0 | Same, and they are switched off, so the gate is doing the work rather than the value |
| `bye_local_cap`, `bye_tau_months` | 1.5, 18 | Same again — inert in every backtest by construction |
| `BYE_MIN_WEIGHT` | 30.0 | The admission gate on the **whole** by-election channel, promoted from an inline literal §1.69. Never swept. A sweep at 2026 would at least show what it gates |
| `ALPHA_MIN_SHARE`, `ALPHA_FLOOR`, `ALPHA_CEILING`, `ALPHA_FALLBACK` | 0.01, 1.0, 200.0, 12.0 | The selection rule feeding the model's **dominant width lever** (83–98% of drawn variance). Its own docstring says that without the share cut "every pool pinned to the 200 ceiling", which bounds it below but not above. **Never swept** |
| `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` | 0.25, 0.95 | The triangular support of every seeded arrival. 25/95 rather than 10/90 or 5/95 is undefended. **Never swept** |
| `TURNOUT_DRAW_FLOOR`, `TURNOUT_DRAW_CEILING` | 0.02, 0.95 | Per-VD turnout caps in every draw. Whether the ceiling **ever binds** is not measured — that measurement is the first step |
| `WARD_PR_RATIO_MIN`, `WARD_PR_RATIO_MAX` | 0.5, 2.0 | The clip on the ward/PR split ratio, which §E lists as coming *from the record*. How often it binds is unmeasured |
| ~~`poll_house_k`~~ | 1.0 | **INERT since 2026-08-24 (§1.91): the cap it drove is deleted under `SIGMA_TWO_TERM`, which is now the default.** It is read only on the retired `SIGMA_TWO_TERM=0` path. Formerly: sets the cap `H/(H+k)`, so at one house the cap is exactly 0.50 — and the DA **sits on it** in the 2026 forecast, which means the cap and not the σ arithmetic decides the largest poll effect. Live at 2026, inert in every backtest |
| `poll_deff_subsample` | 1.6 (standalone 1.2) | A design effect asserted, not measured on any SA metro subsample |
| `poll_screen_sd`, `poll_drift_per_root_day` | 0.020, 0.0010 | Excess terms over the calibration case. Live at 2026 only |
| `poll_half_life_days` / `POLL_HALF_LIFE_DAYS` | 120 | **No SA metro poll series is long enough to fit this.** Declared, not measured |
| `poll_min_n` / `POLL_MIN_N` | 300 | An admission floor. The register's own smallest admitted poll is n=503, so any value in (0, 503] is observationally identical on the committed register. **It is not a metro-path lever.** The floor runs ahead of every scope test in `polling.screen`, so it also gates `ipsos-2021-lge-national` (n=1,501) and `ipsos-2016-lge-national` (n=3,142), which drive the ARRIVALS path — raising it above those admits nothing at all and moves a backtest. §1.76 |
| `CAMPAIGN_WINDOW_DAYS` | 550 | How long before polling day an undated poll may still describe the same election |
| `turnout_noise_sd`, `turnout_blend_jitter`, `turnout_pattern_blend` | 0.08, 0.25, 0.5 | The review measured 0.08 i.i.d. over 865 VDs (the review's figure of 855 matches no year — §1.93) as contributing ~0.003 citywide, i.e. nothing — but §1.48/§1.51 found the turnout knobs move **46 ward wins**, so the citywide null is not the whole story |
| `ward_noise_sd` | 0.10 | Live on the ward side (§1.37) and never bounded |
| `MIN_HOME_SPLITS` | 2 | And the binary itself is the problem: ActionSA ran **0.611 / 0.315 / 0.289 / 0.103** across four metros, a gradient in two buckets |
| `CLAIM_FRACTION` | 0.50 | Reporting — it selects which columns calibration is tested on. Changing it changes the population, not the model |
| `REFERENCE_SHARE`, `REFERENCE_SLATE` | 0.0025, 0.25 | What puts a party in the fixed comparison population |

### How to read this section

1. **R5 is 19 of the rows and it is where a reviewer will go first.** Nine of
   them are live at 2026 and inert in every backtest — the by-election family and
   the poll family — which means the panel cannot bound them **even in
   principle**. Only the 2026 result can.
2. **A flat sweep is a range, and this project has two** (`SPINE_K`,
   `level_shrink_scale`). A flat optimum should be reported as an interval, never
   as the point that happened to win.
3. **R4 is one afternoon's work away from being R1.** Six constants sit on
   records with no bootstrap. That is the cheapest defensibility gain available.
4. **Ranges do not compose.** Nothing here says what happens when two constants
   move together, and `poll_house_k` × `entrant_prob` × `contestation_expand` all
   act on the same 2026 forecast.

---

## H. The seventeen the register could not see until 2026-08-23

**These were not added because anyone decided to declare them. They were named
by a guard that could not see them until it was widened** (MODEL-LOG §1.86).
`test_every_tunable_constant_is_in_the_judgement_register` inspected 53 names —
top-level `ast.Assign`, single target, UPPERCASE, literal int/float — and was
structurally blind to numeric default arguments, argparse defaults, dataclass
fields, container constants, non-numeric `DEFAULTS` values, and every number in
a TOML file. That blindness is exactly how `poll_half_life_days` moved 5.6pp of
the live forecast through a default argument no sweep could reach (§1.84).

Every row here is 🔴 — typed, never swept, no interval — unless it says
otherwise. **None has been measured; several have never been moved at all.**

### §H1 · `overhang_rule` — `"deduct"` — ⚖️ STATUTE, NOT A JUDGEMENT CALL

⛔ **RECLASSIFIED 2026-09-02 (§1.165). This is not a lever and it must never be
swept.** It sat at 🔴 "typed, never swept, no interval" for its whole life, and
the sweep-order note above used to schedule it first. That was a category error:
the Municipal Structures Act Schedule 1 item 16, as amended by Act 3 of 2021, is
part of the DEFINITION of the outcome being forecast — the same category as the
council having a fixed size — and no backtest can arbitrate it.

**Where.** `montecarlo.DEFAULTS`, with its value refused at the `--set`
boundary by `montecarlo.STATUTORY_VALUES` and cross-checked in both directions
by `tests/test_levers_are_live.py::STATUTORY`.

**Why the key was not simply deleted.** `test_regressions`'s branch (e)
enumerates `DEFAULTS` and is the only route by which this entry enters the
code-to-register scan, so deleting the key would have orphaned §H1 — the
bidirectional-scan failure, committed in the name of register hygiene. The key
stays; the value is nailed down.

**The evidence, and it is not a score.** Computed from actual results over 24
metro-years: **the clause has never once bound.** Tightest margin over every
entitlement-pool party, by cycle — 2011 **+3**, 2016 **+5**, 2021 **+2** — with
the closest approaches being small concentrated parties (ALJAMAAH at
Johannesburg 2021, 1 ward against a 3-seat entitlement; the PA at Ekurhuleni
2021, 2 against 4), not the ANC. Nationally, Laingsburg WC051 2021 is the only
excessive-seat case found in ~65 IEC reports.

⚠️ **The nearest-miss figure of "4 wards" quoted on 2026-09-02 was the LARGEST
party's margin only.** Item 16 fires on any party, and the true minimum is 2.

⚠️ **THE PRIMARY SOURCES ARE NOT IN THE TREE.** The consolidated Structures Act,
the PMG copy of Act 3 of 2021 and the Laingsburg Seat Calculation Detail are
recorded in §1.17 as "copies in the session scratchpad". **Owner action: commit
them.** Until then the highest-stakes rule in the model has a citation chain that
cannot be re-checked from the repository.

**Record.** Four regimes — `cap` / `level` / `deduct` / `expand` — give different council sizes AND different majority thresholds. Chosen in §1.17. Reachable only behind `--counterfactual`, which `src/overhang_regimes.py` passes to build the comparison table

### §H2 · `w_recency` — 0.70 — 🔴

**Where.** `turnout.py --w-recency`

**Now.** 0.70, verbatim from the original plan. It reaches the model through 20 committed `turnout.csv` files that carry no artefact key, so changing it does nothing until someone re-runs the script.

**Record.** Weight on the 2021 vs 2016 turnout drop-off. **Verbatim from the original plan §3.5**, whose own text asks for a fold-2 sensitivity test that `MODEL-LOG` never records. Reaches the model through 20 committed `turnout.csv` files that carry **no artefact key**, so changing it does nothing until someone re-runs the script and nothing announces the mismatch

### §H3 · `kappa_bye` — 0.25 — 🔴

**Where.** `turnout.py --kappa-bye`

**Now.** 0.25. Same provenance and the same artefact problem as `w_recency`.

**Record.** The by-election tilt in projected turnout. Same provenance and same artefact problem as `w_recency`

### §H4 · `w_split` — 0.6 — 🔴

**Where.** `fold.py --w-split`

**Now.** 0.6, plan §3.5 'Basis: Judgement', baked into the fold parameter artefacts.

**Record.** Down-weight applied to VDs flagged as unstable by the concordance. Plan §3.5, "Basis: Judgement". Baked into the fold parameter artefacts

### §H5 · `PLAN_BOUNDS` — 7 party ranges — 🔴

**Where.** `montecarlo.py`

**Now.** Present for four of the sixteen panel city-years and absent for twelve, because six of eight metro configs have no `[judgements]` block — which makes the headline seat figure a mixture of two configurations.

**Record.** The plan's θ table, transcribed. Clamps the by-election channel and drives the §3.5 violation counter. **Six of eight metros have no `[judgements]` block at all**, so `apply_city` sets it to `{}` and the clamp is silently absent — four of sixteen panel city-years run with it, twelve without, which makes the 384 figure a mixture of two configurations

### §H6 · `GAMMA_FOLD` — `{2026:1, 2021:1, 2016:3, 2011:4}` — 🔴

**Where.** `montecarlo.py`

**Now.** The live 2026 forecast uses fold 1, and the code's own comment concedes the constraint does not pick one. A contestable choice on the published forecast.

**Record.** Which γ fold each target may read. The code's own comment concedes that for 2026 *"the constraint alone does not pick one"* — the live forecast uses fold 1, the 2014→2016 fold, over the 2019→2021 one. A contestable choice on the published forecast

### §H7 · `min_oos_gain` — 0.01 — 🔴

**Where.** `config/dimensions.toml`

**Now.** 0.01, and it is upstream of every pool in the model: age and sex are rejected by this number.

**Record.** **The bar a census dimension must clear to exist at all.** Age and sex are *rejected* by this number, so it is upstream of every pool in the model. `dimensions.toml` was not mentioned in this register once before today

### §H8 · `extrapolation_damping` — 0.6 — 🔴

**Where.** `config/dimensions.toml`

**Now.** 0.6, and typed three more times as a fallback in `pools.py`.

**Record.** Damping on ward composition extrapolated past Census 2022 — four years for the 2026 forecast. Typed three more times as a fallback in `pools.py`

### §H9 · `extrapolation_max_years` / `max_extrapolation` — 8 / 8.0 — 🔴

**Where.** `dimensions.toml`, `pools.Config`

**Now.** 8 / 8.0 — two copies of one number, one in TOML and one as a dataclass field.

**Record.** How far past the census the projection may reach. **Two copies of one number**, one in TOML and one as a dataclass field

### §H10 · `total_seats` — 270 — 🔴

**Where.** `seats.allocate`

**Now.** Johannesburg's 270 as a DEFAULT ARGUMENT in the shared allocator. The offending caller this row names was `leverage.py`, since retired — every `allocate` call left in `src/` passes it explicitly, so the trap is latent rather than live.

**Record.** **Johannesburg's council size as a DEFAULT ARGUMENT in the shared allocator.** Every serious caller passes it explicitly; `leverage.py` does not, so it allocates any city's votes into a 270-seat council. The right fix is to make the argument required — a `TypeError` instead of a silently wrong answer

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** Every `allocate` call left in `src/` passes `total_seats` explicitly (`backtest`, `montecarlo` three times, `validate_seats`, `fold` twice). The caller this row names as the offender left `src/` on 2026-08-31 (§1.140), so the trap is latent rather than live. The default argument itself is unchanged, and so is the recommended fix.

### §H11 · `within_rate` — 0.90 — 🔴

**Where.** `pools.SIMULATION_BLOC`, `vote_located_bloc`

**Now.** 0.90, and three copies of one number.

**Record.** What share of a located bloc's vote falls inside its own pool, in the reader simulation. Three copies of one number

### §H12 · `SIMULATION_BLOC` — container — 🔴

**Where.** `pools.py`

**Now.** The reader-simulation bloc definition that `within_rate` sits in.

**Record.** The reader-simulation bloc definition that `within_rate` sits in

### §H13 · `max_parties` — 12 — 🔴

**Where.** `coalitions.analyse`

**Now.** 12. Operational in flavour, but it silently truncates the coalition space if a council ever seats more than twelve parties — which the 2026 ballot could.

**Record.** The enumeration bound on coalition subsets. Operational in flavour, but it silently truncates the coalition space if a council ever seats more than twelve parties — which the 2026 ballot could

### §H14 · `beta` — 1.0 — 🔴

**Where.** `score.energy_score`

**Now.** 1.0. It is part of what "better" means, so `ITERATING.md` is arguably its proper home.

**Record.** The energy score's exponent. It is part of **what "better" means**, so `ITERATING.md` is arguably its proper home

### §H15 · `BINS` — 5 size bands — 🔴

**Where.** `theta_residual.py`

**Now.** The size bands behind §1.59/§1.77. The '≥15% of the vote' cut this register quotes as though it were natural is a CHOSEN threshold.

**Record.** The size bands that produce §1.59/§1.77's headline. **The "≥15% of the vote" cut this register quotes as though it were natural is a chosen threshold** — move it and the measured interval moves

### §H16 · `THETA_CENTRAL` — 6 party values — 🟡 not live

**Where.** `leverage.py`

**Now.** NOT LIVE. The plan's six typed party values, and the module holding them has since been retired out of `src/` — see the restructure note beneath.

**Record.** The original plan §3.5 *Default* column, verbatim. **`leverage.py` is imported by nothing**, so this does not reach a forecast — but §F lists its sibling `F_OTHER` beside two live constants without saying so

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** Same retirement as §F29: the module holding these six values left `src/` on 2026-08-31 (MODEL-LOG §1.140). The row's substantive claim — that it does not reach a forecast — is now true twice over.

### Added 2026-08-24 — the σ_poll replacement's four constants (§1.87/§1.88)

**Caught by the guard widened in §1.86, within a day of it being widened, on the
author's own new code.** **These were pre-registered and OFF by default. `SIGMA_TWO_TERM` was ADOPTED
as the default on 2026-08-24 (§1.91), so all four are LIVE**, and the rows above
that described the mechanism they replaced have been corrected in the same pass
(§1.93). The old form remains reachable with `SIGMA_TWO_TERM=0` for A/B only.

Every one is DECLARED **and sourced from outside this repository** — which is the
whole point of the replacement. The constants they retire (`POLL_HOUSE_SD`,
`POLL_SCREEN_SD_UNDISCLOSED`, `POLL_HOUSE_K`) were a residual of the same nine
2016 readings that are also the only metro-poll test cases the backtest has.

### §H17 · `SIGMA_COMMON` — 1.5pp — 🔴 declared, sourced

**Where.** The industry-common poll bias. **Never divided by the number of houses** — that is the defect it exists to fix.

**Now.** LIVE since 2026-08-24. 1.5pp, declared and sourced from outside this repository; never divided by the number of houses, which is the defect it exists to fix.

**Record.** Finland 1.25pp; The Economist's production code 1.30pp; Selb et al., *POQ* 87(4) 2023, 5,240 German polls, 1.5pp mean absolute bias; South Africa 2024, 1.66pp

### §H18 · `SIGMA_IDIO` — 1.5pp — 🔴 declared, sourced

**Where.** The house-specific part. The **only** term `h_eff` may divide.

**Now.** LIVE since 2026-08-24. 1.5pp, declared and sourced; the ONLY term `h_eff` may divide.

**Record.** Stoetzer prior N(0,1); Bon et al. ≈1.0; Jackman phone-only 1–3; SA 2024 1.71pp

### §H19 · `SIGMA_DRIFT_PER_ROOT_DAY` — 0.30 pp/√day — 🔴 declared, sourced

**Where.** Opinion movement between fieldwork and polling day.

**Now.** LIVE since 2026-08-24. 0.30 pp/√day, declared and sourced; the shipped `POLL_DRIFT_PP_PER_ROOT_DAY` of 0.10 is 2–4× too small.

**Record.** Band 0.20 (Ellis, NZ — *estimated* in a state-space model) to 0.41 (derived from Jennings & Wlezien's 4 / 3 / <2pp horizon profile). The shipped `POLL_DRIFT_PP_PER_ROOT_DAY = 0.10` is 2–4× too small

### §H20 · `SIGMA_VOLATILITY` — 0.8pp — 🔴 declared, sourced

**Where.** A South Africa adjustment: +0.1pp per 1pp of average party swing.

**Now.** LIVE since 2026-08-24. 0.8pp, declared and sourced — a South Africa adjustment for average party swing.

**Record.** Survey Methods; independently corroborated by Botten Ada's `kappa` growing with years since the last election

**Read these with §1.88's caveat.** They are not measured *here* and three
city-years with one house cannot check them. Their claim over the constants they
replace is **identifiability**, not accuracy: a residual of one house cannot be
checked and a citation can.

### What this section is for

Not to be read. It is here so that the next audit starts from seventeen known
gaps rather than from zero, and so that **B2's sweep has a list**: the
Derivedness Debt in `ITERATING.md`'s Key 3 is computed from this register, and a
register that cannot see a constant prices it at nothing.

**The order to sweep them in is not the order above.** `PLAN_BOUNDS` decides
the most and is the least defended; `w_recency` and
`kappa_bye` are the oldest unexamined inheritance; `min_oos_gain` is upstream of
everything.

## I. Added 2026-08-26, REMOVED 2026-08-27 — reconciling the roll with the census

> ⛔ **NONE OF THESE FOUR CONSTANTS EXISTS ANY MORE.** They were added by §1.100
> and removed by §1.102, which established that the census adult count is not an
> input this model needs — elections are decided by registered voters and the
> roll is a hard count, so a registration rate above 100% is a fact about the
> census, not a quantity to clamp. The section is kept as the record of a
> declared-and-withdrawn set, because a register that silently loses rows is
> worse than one that shows its history.
>
> What replaced them: nothing in the levels, and
> `projected_pool_shares` now trends on a RATE OF CHANGE, which is invariant to
> exactly the constant level bias these were trying to correct.

**These four exist because an impossibility was being reported and left
standing.** Splitting Johannesburg's 2021 roll across population groups gave
**560,217 registered white voters against 300,374 white adults — a 187%
registration rate** (`DATA-QUALITY.md` item 11). The policy was *"nesting
violations are reported, not clamped"*, on the good argument that clamping
would bury a public-record defect inside our numbers. But reporting it never
stopped it propagating: every party's fitted appeal rate in that pool was
computed against a denominator 1.87× too large.

The owner's ruling, 2026-08-26: *"the roll and census do not agree, so I would
blend them since they are both direct measures. But we should not allow anything
more than 100%. And nothing will ever be 100% let alone 156%."*

**All four are 🔴 — typed, never swept, no interval.** Three of them bound a
quantity rather than estimating one, which is why an interval is not obviously
meaningful; CENSUS_ROLL_BLEND is the exception and is the one worth sweeping
first.

The four were CENSUS_ROLL_BLEND (0.5), MAX_REGISTRATION_RATE (0.95),
MAX_CENSUS_LIFT (2.0) and MIN_TURNOUT_RATE (0.05). They are written here
without backticks-as-symbols deliberately: the register's guard checks that every
symbol it names still exists in the source, and naming a deleted one would make
this section fail that guard forever. Their definitions are in MODEL-LOG §1.100
if they are ever wanted again.

**How to check them.** `pools.rates` now carries `census_blend` (the lift
applied) and `census_blend_wanted` (the lift the roll asked for). Where the two
differ, MAX_CENSUS_LIFT bound and the residue is a live data-quality problem,
not a solved one. Johannesburg 2016 and 2021 both ask for ≈1.48×, which is a
stable group-and-city-specific discrepancy rather than an artefact of the fit —
Cape Town's white pool asks for no lift at all.

---

## J. Added 2026-09-02 — the two reprojection guards (§1.161)

Wards are redrawn at every local election, so a composition fitted on one
delimitation has to be moved onto the target's wards through voting districts
(`pools.reproject`). Two constants decide when that move is trusted. **They are
not a pair of thresholds on one quantity — one is a refusal and the other is
not, and they are not measured on the same denominator.**

### §J1 · `CENSUS_COVERAGE_FLOOR` — 0.80 — 🔴 typed, and it means two things

**Where.** `pools.py`, module level. Read at **two** sites that do different things:

* `pool_counts` — a **printed warning** only. The refusal there is §J2.
* `registered_at_target` — a **refusal** (`SystemExit`), with no drift test.

**Why it is not the refusal in the first place.** Coverage answers "how much of
the city failed to map"; the question that matters is "how far did the answer
move because of what was lost". Those come apart badly: eThekwini lost **one
ward of 111** — 0.8% of the city, 99.8% Black African — and a coverage-shaped
test refused the whole city-year over it, while the citywide composition it
induced moved **0.0023**. See §J2.

**Now.** Typed. ⚠️ NOT MEASURED — 0.80 is a guess at a proxy whose transfer
function to the quantity that matters is unknown.

**Measured 2026-09-02, and it binds nowhere.** Coverage at the
`registered_at_target` refusal, on the full emit path with the artefact write
stubbed so nothing on disk moved:

| city-year | fitted → target delimitation | covered |
|---|---|---|
| Cape Town 2011 | 2006 → 2011 | 0.9609 |
| Johannesburg 2011 | 2006 → 2011 | 0.9653 |
| Mangaung 2011 | 2006 → 2011 | 0.9771 |
| eThekwini 2011 | 2006 → 2011 | 0.9899 |
| **Johannesburg 2026 (live)** | 2021 → 2026 | **0.9979** |

Worst case is 16pp of headroom above the floor. At the `pool_counts` warning
site the same measure runs 0.9803–1.0000 across all 24 city-years. **So this
constant is inert everywhere it can currently be reached**, and its value has
never been exercised by anything.

**⛔ The inconsistency is known and is NOT resolved.** The §J2 argument — that
the harm is the induced shift, not the size of the loss — applies just as well
at `registered_at_target`, which still refuses on coverage and runs no drift
test. It is left alone because changing a refusal is a behaviour change to be
measured rather than tidied, and because it is inert today. It is owed the §J2
treatment. **How to check it:** re-run the probe above; the day any city-year
approaches 0.80, this becomes live and undefended in the same moment.

### §J2 · `CENSUS_DRIFT_CEILING` — 0.05 — 🟡 measured against an alternative

**Where.** `pools.pool_counts`. The refusal: the largest pool-share difference
between the citywide composition including and excluding the wards that fail to
reproject — **how far the city's own answer moves because of the loss**, not
how unlike the lost wards are.

**Why the distinction is the whole entry.** The metric this was first written
with measured how demographically *unlike* the lost wards were. It scored
eThekwini's single lost ward at **0.282** and refused a city-year over 0.8% of
its electorate. The induced citywide shift for that same loss is **0.0023** —
two orders smaller, and the honest number.

**Evidence for 0.05.** Randomly ablating Johannesburg's wards all the way down
to 60% coverage moves a pool share by at most **0.028**. So 0.05 is roughly
twice the worst random loss and an order of magnitude below the ~0.28 a
genuinely segregated loss of a large block produces: it separates the two cases
with margin on both sides.

**What it is not.** It is not fitted, and the ablation behind it was run on one
city. **How to check it:** re-run the ablation on Cape Town, whose reprojection
coverage is the worst on the panel. That would make it a measurement rather than
an argued bound.

## K. Added 2026-09-03 — who is assumed onto a ballot that has not been published (§1.175)

### §K1 · `NATIONAL_ONLY_FLOOR` — 0.001 — 🟢 measured, owner's decision

**Where.** `pools.py`, module level. Read **only** in the branch that runs when
no roster has been published — i.e. an unheld target. A held election has a real
roster and never reaches it, so **this constant cannot touch any backtest.**

**What it decides.** Whether a party that polled in the preceding NATIONAL
election, and has no preceding LOCAL record, is assumed onto the ballot of an
election that has not happened yet. Below 0.1% of the national vote, it is not.

**Why a floor exists at all.** The forecast has to exist before nomination lists
publish on 16 September, so the model must guess the roster. The rule was
`set(baseline) | set(composition)` — *everyone* with a national vote — and it had
never been scored.

⚠️ **One number that circulated during this decision is misleading and is
corrected here.** "The lowest preceding national share of any party that went on
to win a seat is 0.0138%" is true, but that party is in the **both** class — it
had a prior local record and is admitted regardless of any national floor. It
does not constrain this cut. **The binding figure is 0.0254%** (the PA at
Ekurhuleni 2016). The lower number would push a reader toward a floor lower than
the evidence requires.

**The evidence, 16 city-years (2016 and 2021, eight metros).** Splitting every
admitted candidate by where its evidence comes from:

| candidate class | n | won a seat | win rate | mean vote share |
|---|---|---|---|---|
| prior-local AND national | 189 | 125 | **66.1%** | **89.73%** |
| prior-local ONLY | 153 | 10 | 6.5% | 0.48% |
| **national ONLY** | **226** | 30 | **13.3%** | **5.12%** |
| genuinely new | 232 | — | — | 4.66% |

⚠️ **Independents are excluded from these shares.** `parties.canonical` folds
every independent into one `IND` pseudo-party; counting it puts the prior-local
class at 1.72% rather than 0.48%. Definitional, but the tables mean "parties".

Ninety per cent of the vote is in the class with both kinds of evidence. The
national-only class is 226 candidates for 5.12%.

**Why the value is 0.1% and not the class.** ⛔ **The class cannot be dropped:
MK is exactly it for 2026** — a 2024 national party with no 2021 local vector,
at 12.2% nationally in Johannesburg. So the limit is on SIZE. Ordering the 226:

| cut | dropped | **local vote lost** |
|---|---|---|
| 0.1% | **158 of 226** | **0.10pp** |
| 0.2% | 188 | 0.21pp |
| 1.0% | 216 | 0.88pp |

**0.1% removes 70% of the phantom candidates for one tenth of a percentage
point.** ⛔ **The first draft argued this from the transfer ratio of the LARGEST
national-only parties (11.51% → 11.64%, 10.13% → 10.93%) and that reasoning is
wrong** — it observes the ratio at the top and licenses a decision at the bottom.
Measured by band, the ratio is *higher and far more dispersed* at the cut point
than at the top:

| preceding national share | n | median local/national | mean | max |
|---|---|---|---|---|
| **< 0.10%** | 20 | **1.41** | **1.97** | 10.44 |
| 0.10–0.20% | 12 | 0.93 | 0.97 | 1.94 |
| 0.20–0.50% | 17 | 1.16 | 1.42 | 5.02 |
| > 2% | 9 | 1.11 | 1.18 | 1.45 |

Small parties MULTIPLY their share locally — textbook second-order election
behaviour (Reif & Schmitt: small, local and opposition parties gain at local
elections). **The tail is systematically UNDER-valued by the very quantity used
to cut it.** The chosen value survives, because the `local vote lost` column
already prices the realised ratio rather than the predicted one — but the
sentence was wrong reasoning that happened to reach a defensible number, and it
is struck rather than left for the next person to move the floor with.

**Chosen by the owner, 2026-09-03**, from the table above rather than from a
round number.

⛔ **0.2% was rejected on the wrong statistic.** The first draft said it "costs
twice the vote for 30 more dropped candidates" — but **vote share is not the loss
function; seats are, and seats are a step function.** Re-scored on seats, over
**three cycles / 24 city-years**:

| cut | seats lost | city-years with a deleted seat-winner | by cycle (2011/2016/2021) |
|---|---|---|---|
| **0.10%** | **2** | **2 of 24** | 0 / 2 / 0 |
| 0.20% | **12** | **11 of 24** | 6 / 3 / 3 |
| 0.50% | **25** | **16 of 24** | 8 / 4 / 13 |

The vote column makes 0.5% look nearly free at 0.61pp. **In seats it deletes a
real seat-winner in two-thirds of the panel**, and the harm replicates in every
cycle. This is much stronger evidence for 0.1% than the first draft had, and it
is the version that should be re-read in two years. *(The seat figures are a
LOWER bound: dropping a party also redistributes its vote and can flip
marginals.)*

**Measured effect on the live forecast.** At Johannesburg 2026 it drops **14**
parties; `no_measured_vector` goes 21 → 8. **MK (12.2%), ActionSA (6.2%), RISE
(1.6%) and BOSA (1.0%) all clear it**; what goes is XILUVA (0.025%),
BASIC_INCOME_GRANT_SA (0.078%) and eleven more of that size. 24 of 44 national
parties clear the floor.

**What it does NOT fix, and must not be read as fixing.** A genuinely new party —
no national vote, no local record — is still invisible.

⛔ **And calling ActionSA "the outlier of sixteen city-years, not the norm" was
wrong.** Split by cycle, the genuinely-new class is not a stable distribution
with one outlier; it is a regime change:

| cycle | mean city share | seats won |
|---|---|---|
| 2011 | 1.24% | 17 |
| 2016 | 1.56% | 20 |
| **2021** | **6.92%** | **114** |

**That class won 134 seats across the panel — nearly as many as the entire
national-only class this floor argues about (150).** Averaging a quiet cycle with
a rupture to get 4.66% is anti-conservative when **2026 follows a larger rupture
than either**. It is the same missing covariate `CLAUDE.md` already names for
`k*`: nothing in this model has a term for how turbulent a cycle is. The remedy for that is a **declared**
newcomer in `judgements/<slug>-<year>.toml`, which is a judgement the owner makes
and the model cannot.

### ⚠️ Three corrections and a cost, added 2026-09-03 after the first draft

**1. It is not the NATIONAL share. It is this metro's share of the national
election.** `baseline` reads the city's own result file for the preceding NPE
(`pools.py`, in `emit_pools` where `baseline` is built), so a party is judged on how it polled *in Johannesburg*
at the national election, not nationally. That is the better quantity — locally
relevant — but the first draft of this entry said "national share" throughout
and was wrong. Verified that the measurement used the same quantity as the code:
`baseline` and `_npe_citywide_for` agree to **0.00000** across all 44 parties,
because the NPE file carries only PR rows and the filter is a no-op.

**2. ⛔ IT WOULD HAVE REMOVED TWO REAL SEAT-WINNERS.** Tested against the record:

    joburg 2016      PA   0.0558% at the preceding NPE   won 1 seat   0.17% local
    ekurhuleni 2016  PA   0.0254% at the preceding NPE   won 1 seat   0.28% local

Both are the Patriotic Alliance, and both are the case the floor is structurally
worst at: **locally concentrated, nationally negligible.** Two seats out of the
~3,684 in the panel is the measured price of dropping 158 of 226 candidates —
but it is a price, it is not zero, and it has a demographic shape rather than
being spread at random. *(The PA is at 2.9% in 2024 and clears the floor
comfortably now; the exposure is to the NEXT locally-concentrated party.)*

**3. The boundary is crowded.** Seven parties sit within 0.05pp of the floor at
Johannesburg 2024 — UNITED_AFRICANS_TRANSFORMATION 0.150%, ALLIED_MOVEMENT_FOR_CHANGE
0.140%, COPE 0.121%, HOPE4SA 0.114%, DUDULA 0.107%, **AIC 0.1021%**, AHC 0.1006%
— against ACTION_ALLIANCE_DEVELOPMENT_PARTY at 0.0964% and AZAPO at 0.0875% just
below. **The AIC clears by two thousandths of a percentage point**, and the AIC
is one of the parties the roster rule was measured to MISS at 2016, worth
1.5–2.7% locally. A floor with that many parties adjacent to it is a knife-edge,
and small changes to the preceding NPE will move parties across it.

**How to check it.** Re-run the class table and the cut table on the next cycle's
record; if `national ONLY` stops being ~5% of the vote, or if the transfer ratio
of the large ones stops being ~1.0, the floor's justification has moved. **And
re-run the seat-winner falsifier** — if it starts removing more than a seat or
two, or removes one in a city where the margin is close, the floor is costing
more than it was chosen to cost.

### §K2 · `PRIOR_LOCAL_FLOOR` — 0.001 — 🟢 measured, and INERT TODAY

**Where.** `pools.py`, module level, same branch as §K1.

**What it decides.** Whether a party that contested the preceding LOCAL election
and polled nothing at the preceding NATIONAL one is assumed onto an unheld
ballot. Below 0.1% of its prior local share, it is not.

**Why it exists.** §K1's first draft filtered only the national-only class and
left this one — 153 of 568 admitted candidates — entirely unfiltered. A blind
review found it, and it is **the better bargain of the two**. Over three cycles,
189 such candidates (independents excluded) and **137 of them, 72%, never stand
again**:

| floor on prior local share | dropped | vote lost | **seats lost** |
|---|---|---|---|
| 0.05% | 73 | 0.019pp | **0** |
| **0.10%** | **112** | **0.038pp** | **0** |
| 0.20% | 148 | 0.147pp | **5** |
| 0.50% | 184 | 0.359pp | 16 |

**59% of the class removed at zero measured seat cost** — against the national
floor's 70% for two seats. The value is 0.1% for the same reason it is there:
0.2% costs five seats, one of them a party that won four on a 0.162% prior share.
The curve mirrors §K1's almost exactly, which is itself evidence the shape is
real rather than fitted.

### ⛔ IT WAS INERT WHEN MEASURED, AND THAT WAS STATED RATHER THAN DISCOVERED

At Johannesburg 2026 it removed **27 parties from the guessed roster and changed
nothing in the emitted spec**: `no_measured_vector` was 21 → 8 with or without
it, identical to §K1 acting alone. The reason was structural — those parties sit
in `composition`, so they were never in `no_vector`, and the branch that would
drop them from the ballot was gated on a single boolean that was False for an
unheld target.

**So this constant was a precondition, not a change** — measured and registered
before its consumer existed, the same pattern as `judgements_sha`.

⚠️ **UPDATED 2026-09-03: the consumer now exists.** That boolean was replaced by
the three states of `pools.resolve_roster` (§L1, §1.177). A *projected* roster
may now drop parties, and what it may drop is exactly what §K1 and §K2
deliberately excluded — so this floor is live at an unheld target from this
commit onward. It is no longer inert and the paragraph above is history.

**How to check it.** Re-run the table above on the next cycle. And at the post-
review emit, re-measure the spec diff: if this floor still changes nothing now
that the projected drop reaches it, the drop is not wired up and one of the two
is wrong.

## L. Added 2026-09-03 — the declared-nomination-list path (§1.177, §1.178)

⛔ **EVERYTHING IN THIS SECTION IS ARGUED, NOT TESTED, AND THE REASON IS
STRUCTURAL.** The path runs only for a target whose election has not been held.
Every one of the 24 backtested city-years has a published result file and takes
the `published` arm, so **no measurement the harness can make reaches any of
this.** It will run for the first time in production, on 16 September 2026, on
the live Johannesburg forecast. That is the whole reason it is written down
here rather than left to the code.

### §L1 · A declared roster ADDS always and DELETES only on `complete = true` — ⚖️ argued

**What.** `declared_roster` returns `complete: False` unless the judgement file
says otherwise, and `resolve_roster` licenses a deletion from the pools only
when it is True.

**Why it is a judgement.** Two facts, not one: *do we know the ballot* and *are
we allowed to remove parties from the pools*. Conflating them is a boolean, and
the boolean deletes **2.4-2.9% of a city's vote across 16-20 parties** when it
fires wrongly (§1.175) — funded out of the parties ranked 4th to 12th, which
are exactly the ones that win marginal seats. On the day, under time pressure,
a half-pasted list must fail safe, and the safe direction is *add*.

**How to check it.** After nomination lists publish, count the parties in
`pools_2026.json`'s composition against the IEC list. If `complete = true` was
set and the counts disagree, the deletion fired on a partial paste.

### §L2 · The declaration sets the LEVEL; the record sets the WIDTH — ⚖️ argued

**What.** For a party sized by declaration — `support`, or `overperform`, with
or without `weights` — the band is `[lo_e / base, 1.0, hi_e / base]` where
`base` is the **comparator mean**, never the adjusted centre.

**Why it is a judgement, and why the alternative is indefensible.** Until
2026-09-03 the divisor was the adjusted centre, so stating that a party is
larger than its comparators narrowed its band in exact proportion: ActionSA's
documented ×36 would have put its 95th percentile at **7.7% of its own mean**.
That is a forecast made 36× sharper by the act of admitting a guess, at the one
place in the model where least is known. The replacement is not measured —
nothing in the record says how uncertain a *declared* level is — but it is the
only reading under which the two inputs answer different questions.

**And the level has to survive the group budget.** `arrival_rules` rescales the
entrant group to the arrival-total record, and a declared party left inside that
budget has its declaration renormalised away — a declared 12% measured out at
0.3687%. A judged size therefore sits **outside** the budget, and is not netted
off it: the record is a prior over arrivals nobody has sized, and a cycle with a
12% arrival is not the cycle it describes. The undeclared group keeps the
record. §1.178.

⚠️ **What it does not claim.** That the comparator band's relative width is
*right* for a declared party. A hand-declared level may be far better informed
than the arrival record (a former mayor with a national profile) or far worse
(a name on a list). The model has no term for that and this makes no attempt to
add one; it only refuses to let the level silently set the width.

**How to check it.** After 4 November, score the declared parties' PIT. If they
cluster at the extremes the width is wrong; if they cluster near 0.5 the level
is doing the work and the width is defensible.

### §L3 · `PARTY_KEYS` is closed and an unknown key refuses — ⚖️ argued, and cheap

**What.** `[party.X]` accepts `parent`, `weights`, `support`, `overperform` and
`baseline_share`. Anything else raises, naming the file and listing the set.

⚠️ **A closed set is a promise about what is READ, and for one key it was not
one.** `overperform` was listed here and honoured only in the entrant branch:
declared beside `weights` it passed the refusal, sized nothing, and printed no
warning. Fixed 2026-09-06 — both branches now read `support` and `overperform`
the same way, and either makes the party `judged` and therefore held outside the
group budget (§L2). The lesson generalises: **admitting a key is not the same as
reading it, and this register is the only place that says which.** §1.195.

**Why.** `baseline_share` is informational and **nothing reads it**, while all
408 party tables in the tree carry it and nothing else — and three docstrings
plus the file template named it as the strength knob. The documented way to
size a declared party was a key with no reader. A closed set does not fix a
wrong document, but it does stop the next misspelling costing a forecast
instead of a run, and `suport = 0.12` costs nothing to type on a deadline.

**How to check it.** `test_an_unreadable_key_in_a_party_table_refuses_instead_of_being_ignored`
asserts both directions: every key the live files use is admitted, and a
constructed misspelling is refused.

### §L4 · `ROSTER_DROP_CEILING` — 0.015 — ⚖️ argued, from a measured cost

**What.** A `complete = true` roster that would delete parties holding more
than **1.5%** of the fitting year's vote refuses, names the parties and their
shares, and requires `confirm_drop = true`.

**Why that number.** §1.175 measured a wrongly-fired drop at **2.4-2.9%** of a
city's vote across 16-20 parties. The ceiling sits below the smallest of those,
so a real mis-paste trips it, and above the trivial corrections a genuine list
makes. Under largest remainder ~0.4% of the vote is a seat, so 1.5% is roughly
four seats — the point at which a human should look.

⚠️ **It is a tripwire, not a bound.** `confirm_drop = true` passes any mass. The
refusal buys a second pair of eyes on the one edit that has no second chance,
not a limit on what the ballot may be.

**How to check it.** After the lists publish, the accepted drop's mass should be
small and its parties should all be genuinely absent from the IEC list. If
`confirm_drop` had to be set, the reconciliation belongs in `MODEL-LOG.md`.

### §L5 · `MAX_POOL_CAPTURE` — 0.9 — 🔴 typed, and it binds SILENTLY

**What.** No party may be seeded to take more than 90% of any one pool.
`_capture_from_share` clips to it.

**Why it is 🔴.** It was a bare `0.9` literal inside a comprehension, in no
register entry, until 2026-09-03. Nothing measured it and nothing said when it
bound. Measured now on Johannesburg-like pool sizes:

| declaration | delivered | short |
|---|---|---|
| 18.12% flat (the ActionSA level) | 16.44% | 9% |
| 25% flat | 20.15% | 19% |
| **6% entirely in Indian/Asian** | **2.85%** | **53%** |

Second-order for a flat vector and severe for a **concentrated** one — which is
exactly what `weights` exists to express. The note beside it read
`Sized at a DECLARED 6.00% of the city` throughout.

**What is fixed and what is not.** `capture_shortfall` now measures the loss and
the note reports it, so the cap is no longer silent. **The value is still
undefended** — 0.9 was never measured against anything, and the honest
alternatives (refuse, renormalise onto the remaining pools, or raise the cap)
have not been scored. Registered here so it is visible rather than quietly
binding.

**How to check it.** `test_the_pool_capture_cap_says_when_it_binds` asserts it
does not bind on an ordinary flat declaration and does on a concentrated one.

### §L6 · `_arrival_total_prior` — pooled MEAN over entrants only — 🟢 measured, and a hypothesis withdrawn

**What.** The arrival group budget is the **mean** of the **entrants-only**
group total, **pooled** over every city-year strictly before the target. Not a
median, not the all-arrivals population, and not recency-weighted.

**Why mean.** The estimand argument, which stands alone: IPF pins each party's
mean to its centre, so whatever goes into a centre is an expectation by
construction (the 2026-08-17 correction, §1.179). It also scores better out of
sample — Σ|err| over the 2016 and 2021 targets is **2.6146% against the
median's 3.0777%** — but see the two warnings below before quoting that number
as though it settled anything.

⛔ **DO NOT IMPORT THE `k*` RMS-OVER-MEAN PRECEDENT HERE.** There the consumer
needed `E[k²]`, so the root-mean-square was the right statistic. Here the
consumer needs `E[X]`. The mean is correct and RMS is **not** the analogous
move — the analogy is about matching the statistic to the consumer, and the
consumers differ. Written down because the precedent is one page away and reads
as though it generalises.

**Why not recency.** It was the plan's own provisional position and it does not
survive measurement: recency-weighted scores **2.6893%** and last-cycle-only
**2.7746%**, both worse than the pooled mean. The gap is 0.08pp over two
targets — inside noise — so the claim is the weaker one: recency is **not
better**, and it costs a half-life parameter a panel with ~3 effective clusters
cannot support. **Parsimony decides it, not the score.**

⛔ **THE OUT-OF-SAMPLE INSTRUMENT HAS TWO EFFECTIVE OBSERVATIONS, AND EVERY
FIGURE ABOVE IS A TWO-POINT COMPARISON** (pollster review, 2026-09-06; §1.198).
The score is taken over the 2016 and 2021 targets, and every metro-cell inside a
target shares one prediction, so `Σ|err|` reduces exactly to
`|2.0424 − p| + |3.6131 − p|`. **"8 of 8 cells" is two year-level facts, not
eight independent confirmations**, and a backward-looking mean on a series that
dips then rises *must* under-predict — observing that it does is the mechanism
restating itself, not new evidence.

⛔ **AND THE CONSTANT THAT "BEATS" EVERY ESTIMATOR CANNOT LOSE.** A flat 2.8%
scores **1.5707%**, forty percent better than the shipped estimator — and for
two points, *every* constant in **[2.0424, 3.6131]** scores exactly 1.5707. It
is the L1 minimum attained on an interval, and 2.8 is the midpoint of the two
outcomes being scored, chosen with both of them in view. **The honest constant —
the one pickable before 2016, from 2000/2006/2011 — is 1.40, which is the
pooled mean this model already ships.** The estimator and the honest constant
are the same number. Anyone citing the 2.8% result as evidence against the
estimator is citing an in-sample fit with one parameter.

⚠️ **What is known to be wrong with it.** Every estimator tested under-predicts
at both scored targets. The entrants-only series runs 1.15 / 2.00 / **0.84**
/ 2.04 / 3.61% across 2000–2021 — not a trend, a dip at 2011 and a sharp rise
after — and no backward-looking statistic tracks that. **So the 2026 arrival
mass is more likely low than high**, and it should be said that way wherever it
is quoted. A trend term is NOT added: fitted on two scored targets it is the
`k*` error again, and the honest reading is the same one — this is not a
constant to estimate but a variable with a missing covariate (how fragmenting a
cycle is), for which the model has no term.

⚠️ **The population is a guarantee only from 2011.** `SPLITS` names six modern
parties and no pre-2011 one, so the seven rows the 2000/2006 widening adds have
`entrants == total` by construction — 24% of the 29-row panel — and the 2006
lists carry what look like genuine splits sized as entrants. *"Entrants only"*
is therefore a measured population after 2011 and a label before it. Populating
`SPLITS` for those cycles is a judgement call, it is cheap, and it would remove
the caveat.

**How to check it.** Re-run the out-of-sample table in §1.180 when 2026 lands.
It adds a third target — taking the instrument from two effective observations
to three, which is the first thing that could genuinely separate these four
estimators.

### §L7 · `len(arr) < 3` in `arrival_group_record` — 🔴 selects on the dependent variable

**What.** A metro-year with fewer than three arrivals is dropped from the
arrival record entirely.

**Why it exists, and why that is the wrong reason for one of its two
consumers.** A symmetric-Dirichlet concentration is not estimable below three
members, so `arrival_group_spec` needs the floor. **`_arrival_total_prior` needs
only the total and inherits the floor anyway** — and the floor selects on
arrival COUNT, which is correlated with arrival MASS, so the budget is
systematically inflated by excluding the quiet city-years.

Measured 2026-09-04. The three excluded rows are **MAN 2006 (0.330%), BUF 2006
(0.493%) and MAN 2011 (0.284%) — the three smallest arrival totals in the whole
record**, two of them in the cycle the widening adds:

| target | with the floor | without | effect |
|---|---|---|---|
| 2011 | 1.8769% | 1.5512% | **+17.4%** |
| 2016 | 1.3977% | 1.2048% | +13.8% |
| 2021 | 1.6433% | 1.4840% | +9.7% |
| 2026 | **2.1867%** | 2.0163% | +7.8% |

**Status: left in place, deliberately.** Removing it is forecast-moving and
belongs in a window with its own pre-registration, not in a commit fixing
something else. It is registered here so the inflation is a known quantity
rather than a discovery — `audits/BATCH-PLAN-2026-09-02.md` required this and it
had not been done.

⚠️ **It is the same defect one level down from the one §L6 fixes**: one record,
two consumers, and a rule that belongs to one of them applied to both.

### §L8 · `UNCLASSIFIED_FLOOR` — 0.005 — ⚖️ a REPORT, and it changes no number

**What.** A party with no measured pool vector, no entry in `SPLITS` and no
declared parent — so `classify_arrival` calls it *"arrived from nothing"* — is
listed in the emitted spec under `unclassified_with_national_record` if it held
at least **0.5%** at the preceding NATIONAL election.

**Why the national share and not the local one.** The local baseline of such a
party is zero by construction — that is what makes it an arrival — so a local
trigger can never fire. A party that plainly exists nationally and has no local
lineage is the case worth a second look: **it has probably split from someone
nobody has typed into `SPLITS`.** Getting that wrong once cost 0.1% against an
actual 18.12% (ActionSA, 2021).

**Emitted, not printed.** A warning printed during an emit is scrollback, and
the emit is the operation nobody re-runs. In the spec it is diffable, it
survives into `compare_history`, and a test can assert on it.

⚠️ **It changes no forecast number.** Nothing downstream reads the field; the
party is still sized as an entrant exactly as before. It is a flag for a human
before the emit, not a mechanism.

**What it finds today.** On the live Johannesburg 2026 roster it flags exactly
two — **RISE (1.56%)** and **BOSA (1.02%)**. BOSA is Mmusi Maimane's party,
founded after he was pushed out of the DA in October 2019, and it is treated as
arriving from nothing. On the evidence of §1.186 — where that departure cost the
DA two-thirds of the Coloured pool and half the Indian/Asian — that is very
likely a split whose parent should be declared. **Flagged, not decided:** naming
a parent is a judgement, it belongs in the judgement file, and it is the owner's.

**Why 0.5%.** Below it the list fills with the national tail: at 0.1% it would
flag fourteen more, all under 0.11%, none of them plausible splits. Above ~2% it
would miss both of the ones that matter. Chosen to make the list short enough to
read on the day. Undefended beyond that.

### §L9 · `REGISTRATION_MAX` — 2.0 — ⚖️ a runaway guard, not an estimate

**What.** `_nest` fits three levels with one solver. `adult_share` and `turnout`
are bounded at **1.0**, which they cannot exceed. **`registration` is bounded at
2.0**, because it can.

**Why it can exceed 1.** Registered voters are **counted**; census voting-age
population is **modelled**. `pool_counts` computes their ratio itself and files
it as `census_correction`, *"a property of the census, not of the model"* —
**1.206 Indian/Asian and 1.480 White at Johannesburg 2021**. `DATA-QUALITY`
item 11 records the 2022 census over-stating exactly those groups by 14% and
24%. From Phase 1a until 2026-09-05 the solver clipped that quantity to 1.0 and
pushed the surplus into the other pools: **Johannesburg's White share of the
registered roll read 20.0% against 25.2% unclipped.**

⛔ **THE EVIDENCE FIRST WRITTEN HERE WAS MEASURED WITH THE WRONG INSTRUMENT AND
THE VALUE 2.0 IS NOT YET DEFENDED. CORRECTED 2026-09-06.**

It said *"the only values above 2 are Mangaung Indian/Asian at 4.34 and 3.36"*
and cited Cape Town Indian/Asian at 1.82 / 1.92 / 1.72 as proof the guard admits
it. **That table was taken with the bound lifted on all three levels at once**,
which inflates `adult_share` and deflates the registration rate — the identical
error §1.189 diagnoses for its own P2 two paragraphs later and did not carry
back. Re-derived with the **shipped** instrument:

| city | pool | 2006 | 2011 | 2016 | 2021 |
|---|---|---|---|---|---|
| Johannesburg | White | 1.27 | 1.38 | 1.71 | 1.74 |
| **Cape Town** | **Indian/Asian** | 1.90 | **2.13** | **2.26** | 1.93 |
| Mangaung | Indian/Asian | — | — | 4.34 | 3.27 |

**Two of Cape Town's four cycles are ABOVE 2.0.** So the guard binds on **four
`registration` cells in two cities** — Cape Town 2011 and 2016, Mangaung 2016 and
2021 — two of which this entry cited as proof it binds on nothing but the
degenerate pool.

⚠️ **And the panel-wide picture is larger still: 24 fitted cells sit on a bound,
across four cities and 15 city-years** (§1.192) — 4 `registration`, 10
`adult_share` at 1.0, 5 `turnout` at 0.0, and the rest. **Johannesburg, Tshwane,
Ekurhuleni and eThekwini are clean.**

**Status: the per-level split is right and ships. The VALUE 2.0 is undefended**
and is deferred rather than defended — changing it forces another emit and the
evidence for any replacement must be re-measured on the corrected instrument
first. What is certain is that the old single bound of 1.0 clamped a quantity the
model separately computes as 1.48.

⛔ **It is a guard, not an estimate.** It does not say a registration rate of 2.0
is plausible; it says a fit that reaches 2.0 has stopped estimating. When it
binds, the pool is listed in the spec's `rates_on_a_bound`.

**And the clip is no longer silent.** `_nnls`'s docstring always promised the
caller *"must SAY SO rather than quietly using the clipped value"*; the
`unidentified` list it pointed at was computed and **read by nothing** — no
print, no field, no test. It is now emitted as `rates_on_a_bound`. Its message
also distinguishes the two causes: a pool reaching under 25% of any ward is
genuinely unidentifiable, while one reaching 77% is identifiable and its bound is
binding because the true value lies beyond it. The old message blamed the ward
table for both.

⚠️ **What this does NOT fix, measured and pre-registered as P3.** The DA/White
infeasibility is **unrelated**: fatal cells went 18 → 17, Buffalo City and Nelson
Mandela Bay unchanged, Cape Town marginally worse. That corner is a structural
failure of the ecological fit where one pool dominates — at Buffalo City 2011 the
DA is fitted taking 100% of three pools at once and still cannot reach its actual
20.26%. Separate work, §1.189.

**How to check it.** `test_the_registration_bound_is_per_level` asserts
`adult_share` and `turnout` stay within [0, 1] everywhere, that a rate above 1 is
admitted for registration, and that the guard binds on Mangaung's Indian/Asian
pool.

### §L11 · The CONTENDER rule — ⛔ SUPERSEDED 2026-09-07, ITS HEADLINE COMPARISON IS ACROSS TWO MODULES

⛔ **DO NOT APPLY THIS ENTRY. Its evidence table compares two parties that are
sized by different machinery, and the 2026 party it says it flags is on the side
the table does not describe.** `emit_pools` computes
`newcomers = {p for p in no_vector if baseline.get(p, 0.0) <= 0.0}`, so a party
with a preceding NATIONAL result never reaches `arrival_rules` at all:

| party | prior national (JHB) | sized by |
|---|---|---|
| **ActionSA** 2021 | **0.00%** | `pools.arrival_rules` |
| **Agang** 2016 | **0.52%** (NPE 2014) | `levels.spine`, route *national only* |
| **MK** 2026 | **12.22%** (NPE 2024) | `levels.spine`, same route |
| EFF 2016, COPE 2011 | 10.13%, 9.61% | `levels.spine`, same route |

**So the 600× ratio this entry rests on — ActionSA 18.12% against Agang 0.03% —
is a comparison across two populations**, and the "contender" class it defines
cuts across them. Most of the analysis behind it concerns parties the arrival
record does not size. **Sixth population error in the sequence §1.198–§1.204
names, and the only one in the register itself.**

⛔ **"Office held" is refuted on the population where it can be tested.** On the
eight first-local events, office-held geomean is **0.975** against no-office
**1.299** — the wrong direction — and **COPE, whose leaders were Minister of
Defence and a provincial Premier, is the worst event in the record at 0.179.**
Rupture does the work the office criterion was being credited with.

**Replaced by §L12**, which partitions on the line the code already draws.
Retained unedited below as the record of what was argued. §1.205.

### §L11 (superseded) · The CONTENDER rule — who is not chaff — ⚖️ argued, and not yet wired

**What.** A party arriving with no local record is treated as a **contender**
rather than as one of the thirty micro-parties on the ballot when **all three**
hold, judged on nomination day:

1. **Provenance** — it is new, or a split from an existing party.
2. **Standing** — its leader **has held elected or executive office**. Public,
   binary, and checkable before the lists close.
3. **No rupture** — no public leadership breakdown between the party's
   formation and polling day, recorded as a **dated event with a source**.

Everything else is chaff, however well known the founder. A contender is then
sized by three multipliers, strongest evidence first: the pool it lands in and
whether that pool's incumbent is shedding; its leader's home city; and its own
preceding national result where it has one.

**Why it is a judgement and cannot be derived.** Criterion 2 is not in any
result file. It is the one input that separates the two cases the record
otherwise cannot tell apart, and the separation is enormous:

| | leader | office held | first local result |
|---|---|---|---|
| **ActionSA**, Johannesburg 2021 | Mashaba | **Mayor of Johannesburg** | **18.12%** |
| **Agang**, Johannesburg 2016 | Ramphele | none | **0.03%** |

Both were new parties with nationally famous founders. A factor of six hundred
separates them, and nothing in the IEC's files predicts it. Ramphele was a
Black Consciousness founder, a vice-chancellor and a World Bank managing
director; she had never held political office. **Fame is not the bar. Office
is.**

**The evidence for each multiplier, and its strength.**

* ⭐ **The pool, contemporaneously — the strongest relationship in the arrival
  record.** A contender's size tracks the decline of the incumbent in the pool
  it lands in: **COPE 2011 corr −0.92** across eight metros (Nelson Mandela Bay
  ANC −15.5pp → COPE 4.88%; eThekwini ANC **+3.2pp** → COPE 0.40%), **EFF 2016
  corr −0.82**. ⚠️ **This EXPLAINS and does not FORECAST** — the incumbent's
  collapse and the contender's rise are the same event.
* **The pool, forecastably — real, weak, and the honest number.** Using only the
  decline in the cycle **before** the election: pooled **−0.47**, within-year
  **−0.31** across 17 city-years. Inside 2016 it inverts. It says whether the
  ground is fertile, not whether anyone plants in it — 2016 had fertile ground
  in every metro and no contender-grade leader, and its largest arrivals were
  0.09–2.74%.

⛔ **CONTROLLED FOR TURNOUT, THE PANEL-LEVEL VERSION OF THIS IS NOTHING**
(owner's control, 2026-09-07). A fall in the incumbent's SHARE mixes voters
switching away with voters staying home, and only the first leaves anything for
a contender to take. Measuring the ANC in **votes per registered voter** as well,
across 23 city-years:

| | pooled | **within-year** |
|---|---|---|
| ANC share decline | −0.13 | **−0.17** |
| ANC decline per registered voter | −0.32 | **−0.00** |
| turnout decline | −0.44 | **+0.05** |

**The whole relationship is a YEAR effect and there are three years**: turnout
+13.1% in 2011 with a mean biggest arrival of 1.01%; +0.6% in 2016 with 1.13%;
**−14.6% in 2021 with 5.33%**. Contenders broke through in the cycle turnout
collapsed and not in the cycle it rose.

**So the pool multiplier survives only in its narrow form** — one party across
cities in one year, which is what COPE's −0.92 and the EFF's −0.82 are. It does
NOT generalise to "how big is the biggest newcomer in this city-year", which has
no within-year relationship to what the incumbent shed.

⚠️ **And part of a contender's headline share is a shrinking denominator.**
ActionSA's **18.12% of votes cast is 7.54% of the registered roll**; Tshwane's
9.28% is 4.09%; Ekurhuleni's 7.36% is 3.13%. Johannesburg's turnout fell 56% →
41.6% in that cycle. Any figure quoted from this entry is a share of a
**smaller electorate** than the one that produced the comparison, and the model
draws turnout per pool precisely so that this is not assumed away.
* **The home city.** ActionSA 18.12% in Mashaba's Johannesburg, 9.28% / 7.36% /
  2.35% at increasing remove; GOOD 3.68% in De Lille's Cape Town and ≤0.49%
  everywhere else. The model already measures this — 0.611 of the parent at
  home against 0.103 away.
* **The national anchor, and rupture as its exception.** EFF kept 1.01–1.50× of
  its national share across eight metros, GOOD 1.07, PA 1.49, the ID 0.86 —
  **COPE 0.12–0.28 across five**, after the Lekota–Shilowa war. One bimodal
  split, and criterion 3 is what selects the branch.

**Landing, not crossing, is the mechanism.** Decomposing each contender's
fitted pool vector against its parent's: EFF **stayed** in the ANC's pool
(weight 0.69–1.12) and ActionSA **crossed out** of the DA's (0.13) — and both
succeeded, because both ended up in the pool that was shedding. Agang stayed in
a pool that was not.

⛔ **What this does NOT claim.**
* It rests on **four events** — COPE, the EFF, ActionSA, with Agang as the
  negative control — one of which supplies eight data points by standing
  everywhere at once. It is not a fitted model and must not be quoted as one.
* **Nothing is wired.** No code reads this entry. It changes no number today.
* Criterion 2 must be **written down before nomination day or it is hindsight**,
  and the temptation to award "standing" retrospectively to whoever did well is
  the whole failure mode.

**How to check it.** After 4 November: whether the parties flagged as contenders
before the lists closed behaved as contenders, and whether any party denied the
label beat 1% of a metro. **For 2026 the rule flags MK** — a split, led by a
former State President, no rupture on record, with a 12.22% Johannesburg
national result to anchor on. If a rupture occurs before polling day the rule
says COPE, not EFF, and nothing in the model would currently notice.

### §L10 · `gates_sha` — the artefact key records the resolved ENV gates

**What.** The key now carries a hash of `HELD_BACK_OFF`, the resulting size of
`levels.HELD_BACK`, and `THETA_WINDOW`.

**The hole it closes.** `_deps_sha` names `levels` as a dependency *because* it
carries `HELD_BACK`, "which decides whether a fitting election may be read at
all". But `HELD_BACK_OFF=1` empties that gate at import time and `_code_sha`
hashes a **syntax tree**, which an environment variable does not change.
Measured 2026-09-05: the gate goes from **14 entries to 0** while `deps_sha`
stays byte-identical at `53cedeb94115dd98`.

⚠️ **And `levels.py`'s own comment invites the run that does it** — *"`HELD_BACK_OFF=1`
lifts the gate for one run, so the diagnosis this entry is about can be
MEASURED"*. A spec emitted during such a run reported itself **current for
ever after**. That is precisely the silent staleness the key exists to close,
arriving through the one door it was not watching.

**Recorded, not refused.** A diagnostic emit is legitimate; what matters is that
the artefact says it was one. A later normal run compares and reports stale.

**How to check it.** `test_an_environment_gate_moves_the_artefact_key` flips the
resolved gate and asserts the key moves — and asserts the gate is non-empty by
default, so the constructed violation is not a change from nothing to nothing.

## Appendix — how this register has failed before

Kept because it is the argument for every guard above, and because a register
that loses the record of its own failures learns nothing from them.

Verified against the working tree on `splinter-rule-and-historical-tail`,
2026-08-16. Every line number and every claim below was re-checked by running
the code, not copied from a session narrative.

The 2026-08-14 pass said the same sentence and had already gone stale by the
16th: `LEVEL_DF` had moved 4.0 → 7.0, the Dirichlet floor 0.05 → 1e-4, and every
line number in §A was 10–190 lines out — and §A and §F contradicted each other on
two of them, because §F was written later and §A was never revisited. A register
that names the wrong line is worse than one that names none, because it is
checked and passes.

**THIS REGISTER NO LONGER CITES LINE NUMBERS, and that is a fix to the class
rather than to the instance (2026-08-22, MODEL-LOG §1.69).** The paragraph above
records the register going stale on the 16th, was rewritten to say every line had
been re-checked, and had gone stale again by the 22nd: an audit found **every one
of the 24 line citations in §A wrong, by 34 to 375 lines** — `LEVEL_DF` cited
roughly 90 lines above where it lives, `SHRINK` 34 above, `SPLIT_SD_FLOOR` 375
above, several pointing at blank lines. A line number is a fact about a file that changes every
time anything above it changes, so it decays on a timescale of hours and its
decay is invisible. **A NAME DOES NOT DRIFT.** Every row now cites the module and
the symbol, and two guards enforce it:
