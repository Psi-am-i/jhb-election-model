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

⚠️ **[16-panel] — evidence pinned to a retired panel (flagged 2026-09-11, not
re-judged).** The backtest panel grew past sixteen city-years on 2026-09-01/02
(MODEL-LOG §1.160–§1.161). A row tagged **[16-panel]** rests on a measurement
taken on the sixteen; its figures describe that panel, not today's, and have
not been re-measured. Tagging changed no value, status or colour.

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
5. **A *Plain* field is the reader's version of an entry** (added 2026-10-02,
   owner: "omit all judgement calls that aren't an opinion on machinery"). Only
   calls a lay reader can follow and might dispute carry one: what was chosen,
   why, what the alternative changes, and whether /your-forecast/ can move it. It opens
   the entry, directly under the heading. `src/judgement_sheet.py` copies every
   one, in register order, into the section of `docs-public/methodology.md`
   headed "The judgement calls", and the site build refreshes it; edit the field
   here, never that section. No backticks inside a field (the register→code
   guard would read them as symbols); a figure in one must be the entry's own
   and is cleared for the site by an `[[audit.fixed]]` row citing the entry.
   Which calls carry one, and why the rest do not:
   `audits/2026-10-02-judgement-public/SELECTION.md`.

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
| `ANALYSIS_SEAT_BAND`, `ANALYSIS_SHARE_BAND_POINTS` | 2, 2.0 | `reweight.py`, `within_band`, read by `pyboot/page.py` `analyse` | Typed 2026-10-03 for "Analyse my forecast" on /your-forecast/: how near a reader's seats (seats) and vote (list-ballot points) a simulation must land to count. With them, the definition of "this outcome" (`council_outcome`: the largest party, a majority alone, the chosen coalition). Moves no forecast; decides which chance the analysis prints. | 🟡 | §N3 |
| `apply_city` never resets `DEFAULTS` | — | `montecarlo.py` | **AMENDED 2026-09-24 (register audit).** FIXED: `apply_city` clears `DEFAULTS` and restores a pristine copy before applying a city (since 2026-08-18), guarded by `test_apply_city_does_not_leak_one_citys_scalars_into_the_next`. Johannesburg declares 11 scalars, not sixteen. Status marker left for the owner. | 🔴 | §A43 |
| `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` | ~~0.25, 0.95~~ | — | DELETED 2026-10-09 with the arrival band, which nothing drew from (item9/FINDINGS.md Q5). | ⚫ deleted | §F32 |
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
| `contestation_expand` | 0.220 | `montecarlo.py`, applied in `levels.projected_cont… | **AMENDED 2026-09-24 (register audit).** Ships 0.220 and is INERT at 2026 since the declared ward slates reached the correction (MODEL-LOG §1.252; `EXPECTED_INERT[("contestation_expand", "2026")]`), for as long as the roster is `complete = true`. It acts at no backtest target either (§1.60). | 🔴 | §A5 |
| `DIRICHLET_FLOOR` | 1e-4 | — | 1e-4 and inert as committed — but it has a SECOND consumer that floors a CONCENTRATION rather than a mean, and `PERTURB` sweeps it to 0.05 where that would bind. | 🟢 | §F1 |
| `dirichlet_floor`, `spine_k` (scenario keys) | — | — | Scenario keys mirroring the module constants so a sweep is reproducible. ⚠ This row also lists `poll_k`, which was DELETED on 2026-08-22 (§1.68) and is in no `DEFAULTS` — see the restructure note beneath. | 🟢 | §F21 |
| `entrant_prob` | 0.25 | `montecarlo.py` | Ships 0.25. Typed, but measurable since 2026-08-17 and the typed value survives the measurement; §G-R2 puts the defensible range at [0.25, 0.29]. | 🟡 | §A3 |
| `entrant_share` | `[0.01, 0.04, 0.12]` | `montecarlo.py` | **AMENDED 2026-09-24 (register audit).** Unchanged at [0.01, 0.04, 0.12]. It acts only where no arrival is named — of the backtest targets, 2011 alone. At 2016, 2021 and 2026 the named seeds retire the generic slot (§A4), so the "1.42% of the vote in every run" this row used to state holds nowhere the forecast is published. | 🟡 | §A17 |
| `extrapolation_damping` | 0.6 | `config/dimensions.toml` | **AMENDED 2026-09-24 (register audit).** 0.6. Two other copies in `pools.py`, neither a live fallback: the `Config` dataclass default (marked unreachable — `load_config` refuses a TOML without the key) and `projected_pool_shares`' default argument. | 🔴 | §H8 |
| `extrapolation_max_years` / `max_extrapolation` | 8 / 8.0 | `dimensions.toml`, `pools.Config` | 8 / 8.0 — two copies of one number, one in TOML and one as a dataclass field. | 🔴 | §H9 |
| `FRESHNESS_GRACE_S` | — | `stats.py`, `freshness_problems` | Typed at 300s. ARGUED, NOT TESTED — the harness cannot score a publishing guard; the strong half of the check catches the 16-day defect with no window at all. | 🟡 | §D16 |
| `GAMMA_FOLD` | `{2026:1, 2021:1, 2016:3, 2011:4}` | `montecarlo.py` | The live 2026 forecast uses fold 1, and the code's own comment concedes the constraint does not pick one. A contestable choice on the published forecast. | 🔴 | §H6 |
| `GRID_MARGIN_CELLS` | — | `hex_cartogram.py` | Typed at 2 and purely operational: the Johannesburg optimum uses no cell in the outermost ring. | 🟢 | §D18 |
| `kappa_bye` | 0.25 | `turnout.py --kappa-bye` | 0.25. Same provenance and the same artefact problem as `w_recency`. | 🔴 | §H3 |
| `LEVEL_DF` | 7.0 | `montecarlo.py` | Ships 7.0, live since 2026-08-17 and swept. The sweep cannot distinguish 7 from 30; §F narrows it to ν ∈ [5, 15] on four constraints. | 🟡 | §A18 + §F8 |
| `LEVEL_DF` | 7.0 | — | BOUNDED 2026-08-29 to ν ∈ [5, 15] on four constraints, with the committed 7.0 in the middle. The honest label is no longer 'unmeasured' but 'not resolvable further on this panel'; a joint (κ, ν) fit was designed and NOT built. | 🟡 | §F8 + §A18 |
| `level_floor` | 1e-6 | — | 1e-6; separates the level floor from the deviation floor. | 🟢 | §F19 |
| `LEVEL_FLOOR` vs `SHARE_FLOOR` | — | `fold.py` | Two separate floors, deliberately. On its own it fixed nothing — the 42 phantom seats were the scale drift above it. | 🟢 | §C4 |
| `level_sd_default` | ~~0.45~~ | — | DELETED 2026-10-09 (owner, M3 review row 7). After item 17 it bound for no drawn party at any emitted city-year; a drawn party with no measured width, no size and no θ fit now stops the run (`montecarlo.level_shock_sd`). | ⚫ deleted | §A29 |
| `level_shrink` (and `level_shrink_scale`) | 0.35 | `montecarlo.compress_levels`, run on the finished… | Adopted 2026-08-17 and unchanged; the largest single improvement this model has had. Two things keep it off green: an L1 form-selection leak, and a tail the uniform renormalisation over-feeds. | 🟡 | §A23 + §F20 |
| `level_shrink`, `level_shrink_scale` | 0.35, 0.04 | — | See §A. The scale is a SCALE, not a tuned constant — swept twentyfold with no cliff. | 🟡 | §F20 + §A23 |
| `LOG_CHI2_BIAS` | — | `levels.py`, documented and deliberately unused | Correct, derived, and DELIBERATELY NOT APPLIED: applying it makes the model worse on every metric, because the record it reproduces is marginal and this layer is conditional. | 🟢 | §C5 |
| `MAX_DISPLACEMENT_RADII` | — | `tests/test_hex_cartogram.py` | Typed at 5.0 radii — a regression guard rather than a claim, and it separates the optimal assignment (3.8) from the greedy one (8.8). | 🟡 | §D21 |
| `max_parties` | 12 | `coalitions.analyse` | 12. Operational in flavour, but it silently truncates the coalition space if a council ever seats more than twelve parties — which the 2026 ballot could. | 🔴 | §H13 |
| `MAX_SIGMA`, `MIN_SIGMA`, `NEW_PARTY_SIGMA` | 2.0, 0.15, 1.0 | — | Spread bounds for the `prior-lge-noise` BASELINE, not for the model. | 🟡 | §F28 |
| `METRO_CODES` widened 2 → 8 | — | `levels.py` | Eight metros. More evidence and no leakage, but it moves θ itself, so it is confounded with the spine in any before/after delta. | 🟡 | §B6 |
| `min_clusters` | 8 | `score.chi2_clustered` | Typed. The floor below which the clustered uniformity test prints `not established` instead of a χ². Moves no forecast; decides whether a calibration verdict is a number or a refusal. Under a known null δ̄ is unbiased at every k from 3 to 24 and its noise is SMOOTH in k, so there is no cliff at 8 — any floor is a line on a continuum. | 🔴 | §D22 |
| `MIN_EFFECTIVE_DRAWS` | 200 | `reweight.py`, `require_effective` | Typed, from PLAN.md build step S4. The fewest effective draws a re-weighted figure on the interactive may rest on; below it the control greys out. Moves no forecast: it decides whether the page shows a number or a refusal. | 🟡 | §N1 |
| `MAX_FIGURE_SE_SEATS` | 2.5 | `reweight.py`, `figure` / `within_precision` | Owner, 2026-09-30. The largest Monte Carlo standard error, in seats, a figure on the interactive may carry; above it the figure is withheld and the control that caused it stops. Moves no forecast. With it, the poll dial's width `poll_sd / trust`. | ⚖️ | §N2 |
| `MIN_HOME_SPLITS` and the binary home/away | 2 | `pools.py` | Unchanged: a measured gradient (0.611 / 0.315 / 0.289 / 0.103) modelled as two buckets. | 🔴 | §A44 |
| `min_oos_gain` | 0.01 | `config/dimensions.toml` | 0.01, and it is upstream of every pool in the model: age and sex are rejected by this number. | 🔴 | §H7 |
| `MIN_SHARE`, `CLAIM_FRACTION`, `F_OTHER` | 0.005, 0.50, 1.30 | — | All three were filed under the wrong module once. `MIN_SHARE` is `gamma_recent.py`'s and is a CLAIM about the model, not reporting; `CLAIM_FRACTION` is `score.py`'s. ⚠ `F_OTHER` is no longer in `src/` at all — see the restructure note beneath. | 🟡 | §F29 |
| `OVERHANG_DEDUCT_MAX_ROUNDS_SLACK` | 2 | `montecarlo.py` | Derived, not chosen: any value ≥ 1 is equivalent. | 🟢 | §A39 |
| `OVERHANG_LEVEL_MAX_ROUNDS` | 200 | `montecarlo.py` | 200 rounds. Bounded on ROUNDS deliberately rather than on council size, because a magnitude off the real panel does not transfer to a toy. | 🟡 | §A40 |
| `NATIONAL_ONLY_FLOOR` | 0.001 | `pools.py` | The national share below which a party with no local record is NOT assumed onto an unheld ballot. **[16-panel]** Measured over 16 city-years: drops 158 of 226 such candidates for 0.10pp of vote. MK (12.2%) clears it. Owner's decision 2026-09-03; unreachable from any backtest. | 🟢 | §K1 |
| `PRIOR_LOCAL_FLOOR` | 0.001 | `pools.py` | The prior-LOCAL share below which a party with no national vote is not assumed onto an unheld ballot. Drops 112 of 189 such candidates for 0.038pp and ZERO seats. ⚠️ **AMENDED 2026-09-24 (register audit).** INERT at 2026 for a different reason: the floor filters only the projected roster, and a complete declared roster does not use it (argued from `pools.py`, not perturbed). | 🟢 | §K2 |
| `overhang_rule` | `"deduct"` | `montecarlo.DEFAULTS` | ⚖️ **STATUTE, reclassified 2026-09-02** — Act 3 of 2021 Schedule 1 item 16. NOT a lever and never swept: refused at the `--set` boundary, out of `PERTURB`. Never bound in 24 metro-years; tightest margin 2 seats. | ⚖️ | §H1 |
| `pa_contestation_uplift` | DELETED 2026-08-18 | — | DELETED 2026-08-18. The branch now falls back to the previous local election's measured contestation for every party, which makes it backtestable. | ⚪ | §F27 |
| `PAGE_SIZE` | — | — | Pagination. Reporting, not belief. | 🟢 | §F37 |
| `PARTIAL_BALANCE_PASSES` | 200 | — | 200. A convergence budget that is not a converging sequence, so the number chooses how close to the boundary it gets. | 🟡 | §F12 |
| `PLAN_BOUNDS` | 7 party ranges | `montecarlo.py` | **AMENDED 2026-09-24 (register audit).** Only Johannesburg carries `[judgements.plan_bounds]` (Tshwane's were deleted 2026-08-31), and the clamp needs a by-election file, which exists only for Johannesburg 2026 — so it reads on none of the 24 panel rows and the panel is not a mixture of configurations. Whether it binds at 2026 is unmeasured. | 🔴 | §H5 |
| `poll_credence` | 1.0 | `montecarlo.DEFAULTS` → the metro-poll blend | Declared at 1.0, which is the identity, so it moves nothing. The value the backtest supports is UNMEASURED — the paired sweep is pre-registered and not run. | 🔴 | §A11 |
| `poll_deff_subsample` | 1.6 (standalone 1.2) | `montecarlo.DEFAULTS` → `polling.design_effect` | Declared at 1.6 (standalone 1.2) and unmeasured; measurable the day a house publishes its effective base. | 🔴 | §A10 |
| `poll_half_life_days` | 120.0 | `montecarlo.DEFAULTS`, mirrors `polling.POLL_HALF_… | A real constant since §1.67 and mirrored in `DEFAULTS`, so a sweep can now reach it. Still declared: no SA metro series is long enough to fit it. | 🔴 | §A14 |
| `POLL_HALF_LIFE_DAYS` | 120 | — | 120, declared. No SA metro series is long enough to fit it. | 🔴 | §F3 |
| `poll_house_k` | 1.0 | `montecarlo.DEFAULTS` → `polling.weight_cap` | INERT. The cap it drove was deleted 2026-08-24 with the two-term σ; a lone house is now bounded by the derived `polling.house_ceiling` instead. | 🔴 | §A12 |
| `poll_id`, `poll_weight`, `poll_k` | — | `polls.json` | DELETED 2026-08-22. The legacy path bypassed every admission rule in `polling.usable_for` and had never executed. | ⚪ | §F30 |
| `POLL_K` | — | — | DELETED 2026-08-22 with the legacy poll path. The shape survives as `poll_house_k`. | ⚪ | §F5 |
| `poll_min_n` | 300 | `polling.screen` | Declared at 300 and settable. Note it runs ahead of every scope test, so it also gates the national polls that drive the arrivals path. | 🔴 | §A16 |
| `poll_paths` | **"off"** | `montecarlo.py`, gates both live poll paths | **SHIPS "off" SINCE 2026-09-12 — the forecast uses no poll at all.** The owner's decision, on design grounds; see §A8 and MODEL-LOG §1.225. Measured on 24 city-years: removing the channel moves coherent seat error 725 → 723 and CRPS 545.8 → 541.4, i.e. **not distinguishable from zero**. Every other poll lever below is inert by configuration while this stands. | 🟢 | §A8 |
| `POLL_RMS_ERROR` | ~~0.030~~ | — | DELETED 2026-08-28. Read by nothing; the constant the tests assert against is its neighbour `POLL_RMS_ERROR_2016`. | ⚫ deleted | §F2 |
| `poll_screen_sd`, `poll_drift_per_root_day`, `POLL_MIN_N` | 0.020 · 0.0010 · 300 | `montecarlo.DEFAULTS` → `polling.py` (`POLL_MIN_N`… | All three declared, none measured. The drift rate is fittable from the campaign's waves — pre-register that fit before running it. | 🔴 | §A13 |
| `polling_lean`, `polling_span` | — | DELETED, and this row said "still wired" for days… | DELETED. This row said "still wired" for days after they were gone, which is why the register → code guard exists. | ⚪ | §F26 |
| `POOL_CAPACITY_MARGIN` | 0.98 | `montecarlo.py` (`capped_targets`) | Ships 0.98, one full step clear of a measured cliff. It is the guard, not the cure — the cause is an upstream corner solution in the ecological fit. | 🔴 | §A28 + §F9 |
| `POOL_CAPACITY_MARGIN` | 0.98 | — | See §A — a judgement about what to do when two layers disagree, not a tolerance. | 🔴 | §F9 + §A28 |
| `PROJECTED_METRO_SHARE` | eight per-metro shares of the national vote, 2021 values | — | The last observed value, so nothing is extrapolated; n = 2 and it fires only where no backtest can check it. | 🔴 | §F36 |
| `REFERENCE_SHARE`, `REFERENCE_SLATE` | `REFERENCE_SHARE` = 0.0025 · `REFERENCE_SLATE` = 0.25 | `compare_history.reference_universe` | Both typed. The share cut is safe (below every metro's PR quota); the slate cut is the one to attack, and it moves no forecast — only which columns a width comparison is read on. | 🔴 | §D8 |
| `REG_DRIFT_TOLERANCE` | 0.30 | `build_concordance.py` | RECLASSIFIED 2026-08-24 from 🟢 reporting to 🔴: it reaches the forecast through `fold.suspect_vds` → `w_split` → γ. Declared, never measured, and not a `DEFAULTS` key, so no lever sweep can reach it. | 🔴 | §F38 |
| `RELIABILITY_HALF` | 0.002 | — | 0.002, a value inherited from the hard cut it replaced; only the smooth form is new, and it has never been swept. | 🟡 | §F16 |
| `SAFE` | — | `render_map.py` | **AMENDED 2026-09-24 (register audit).** One definition: `SAFE` lives in `render_map.py` and `hex_cartogram.py` imports it. The STRONG and LEAN tiers were removed by the owner on 2026-09-17 and exist nowhere in `src/`. Not an independent judgement. | 🟢 | §D19 |
| `SD_FLOOR`, `SD_CEILING` | 0.15, 1.20 | `levels.py`, applied in `sd_for` | 🟡 at ≥15% of the vote. On the corrected harness the width in use is 0.151 against a measured 0.273 [0.136, 0.386] — inside the interval but near its bottom, at 1.81×, binding on 32 of 64. Below 15% every interval EXCLUDES it. | 🟡 (≥15%) | §F17 |
| `SHRINK` | 2.0 | `levels.py` | 2.0, measured optimal on forward-validated RMSE(log θ) and on the model's own three scores. Upgraded from 'pre-existing' — do not re-file it as untested. | 🟢 | §A24 + §F15 |
| `SHRINK` | 2.0 | — | Measured optimal 2026-08-17. Do not re-file it here as 'pre-existing'. | 🟢 | §F15 + §A24 |
| `SIGMA_COMMON` | 1.5pp | The industry-common poll bias | LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 1.5pp, declared and sourced from outside this repository; never divided by the number of houses, which is the defect it exists to fix. | 🔴 declared, sourced | §H17 |
| `SIGMA_DRIFT_PER_ROOT_DAY` | 0.30 pp/√day | Opinion movement between fieldwork and polling day. | LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 0.30 pp/√day, declared and sourced; the shipped `POLL_DRIFT_PP_PER_ROOT_DAY` of 0.10 is 2–4× too small. | 🔴 declared, sourced | §H19 |
| `SIGMA_IDIO` | 1.5pp | The house-specific part | LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 1.5pp, declared and sourced; the ONLY term `h_eff` may divide. | 🔴 declared, sourced | §H18 |
| `SIGMA_VOLATILITY` | 0.8pp | A South Africa adjustment: +0.1pp per 1pp of avera… | LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 0.8pp, declared and sourced — a South Africa adjustment for average party swing. | 🔴 declared, sourced | §H20 |
| `SIMULATION_BLOC` | container | `pools.py` | The reader-simulation bloc definition that `within_rate` sits in. | 🔴 | §H12 |
| `SOLVE_TOL` | 1e-9 | `pools.py` | Operational, and listed EXEMPT in the guard — named here so the exemption is visible in the register and not only in the test. | 🟢 | §F11 |
| `SPINE_K` | 1.0 | — | See §B. | 🔴 | §F14 + §B1 |
| `spine_k = 0` on a party with no θ evidence | `w_local = 0.0` | — | A CHOSEN limit (`w = 0`, pure national spine), inert at the shipped `spine_k = None` and reachable only by a sweep, which is what it exists for. | 🟡 | §F22 |
| `SPINE_K`, reciprocal form | — | `levels.py` | 1.0, fitted leave-one-metro-out on a curve that is flat 0.5–1.5. A step function scored better out of sample and was rejected on structural grounds — which is why this is 🔴 despite being fitted. | 🔴 | §B1 + §F14 |
| `SPLINTER_PARENT_WEIGHT` | 0.35 | — | 0.35, measured over 22 splinter-metro cases, no bootstrap, and stale since the archive grew (§A). | 🔴 | §F6 |
| `SPLIT_SD_FLOOR` | — | `pools.py` | 0.90, and it overrides its own measurement at target 2016 while binding at neither 2021 nor 2026 — real work in the one fold where it is least justified. | 🔴 | §B3 |
| the `home` city and `measured_from` pair of each entry in `SPLITS` | ASA→JHB · GOOD→CPT · MK→ETH · NFP→ETH · COPE and EFF→**None** | `pools.SPLITS`, read by `home_splinter_record` | Six typed biographical claims that select WHICH record sizes a splinter. ActionSA's is the single assignment behind the panel's largest error, and the two unset ones announce nothing at all. Declared 2026-09-13, never swept. | 🔴 | §A47 |
| the size-dependence of `sd_for` below 15% | a straight line in log(size) | `levels.py`, inside `theta_prior` | The model is UNCHANGED and the fault is the FORM, not the residual. ⛔ No further functional form may be tried against these two folds, and this row's numbers are Form A's and must not be quoted. | 🔴 | §F18 |
| `THETA_CENTRAL` | 6 party values | `leverage.py` | NOT LIVE. The plan's six typed party values, and the module holding them has since been retired out of `src/` — see the restructure note beneath. | 🟡 not live | §H16 |
| `theta_prior` and `_shrunk` | RESOLVED 2026-08-18 | `levels.py` (`theta_prior`, `_shrunk`) | RESOLVED 2026-08-18. Both shrink toward `size_centre`, they agree to 1e-16, and no forecast moved. | ⚪ | §A26 |
| `TIP_FLOOR` / `OTHER_FLOOR` | — | `render_map.py` | **AMENDED 2026-09-24 (register audit).** One definition in `render_map.py`, imported by `hex_cartogram.py`; 0.05 and 0.005, unchanged. | 🟢 | §D20 |
| `top = 12` parties per table | — | `compare_history.py` | Cosmetic here — but it is what makes `validation_2021.json` not comparable. | — | §D13 |
| `total_seats` | 270 | `seats.allocate` | **AMENDED 2026-09-24 (register audit).** Johannesburg's 270 as a DEFAULT ARGUMENT in the shared allocator. This row said every remaining call passes it explicitly; it was wrong. Both `allocate` calls in `fold.py` omit it, so `fold.py`'s printed seat diagnostic allocates 270 seats whatever the city. They feed that printout only, not the γ parameters the forecast reads, so no forecast number is affected. | 🔴 | §H10 |
| `TURNOUT_CORRELATION` | — | `montecarlo.py` | 0.63 applied as ONE constant to every city and pool pair. It supplies 4–12% of drawn variance in the shape a pool-turnout mechanism should have; why it matters so little is still not explained. | 🟡 | §B4 + §F13 |
| `TURNOUT_CORRELATION` | 0.63 | — | 0.63, declared in `DEFAULTS` since §1.63 and asserted equal to the module constant at import. It MOVES the forecast, so it is a live lever. | 🟡 | §F13 + §B4 |
| TURNOUT_CORRELATION / SPLINTER_PARENT_WEIGHT / SPLIT_SD_FLOOR — the stale-`n` trio | `TURNOUT_CORRELATION` 0.63 · `SPLINTER_PARENT_WEIGHT` 0.35 · `SPLIT_SD_FLOOR` 0.90 | `montecarlo`, `pools` | Still NOT re-measured against the enlarged θ record, and deliberately so; quote none of their `n` values until the record question below is settled. | 🔴 | §A1 |
| `TURNOUT_DRAW_FLOOR`, `TURNOUT_DRAW_CEILING` | 0.02, 0.95 | — | 0.02 / 0.95, applied per draw. They contradict §C's claim that the turnout band 'removes caps rather than adding one'; whether the ceiling ever binds is unmeasured. | 🔴 | §F34 |
| `turnout_noise_sd`, `turnout_blend_jitter` | 0.08, 0.25 | — | Typed; ~0.003 citywide, i.e. nothing. | 🟡 | §F23 + §A41 |
| `turnout_pattern_blend` / `turnout_blend_jitter` / `turnout_noise_sd` | 0.5 / 0.25 / 0.08 | `montecarlo.py` | Typed. The citywide effect of the 0.08 is ~0.003, i.e. nothing — but see §G-R5: the turnout knobs move 46 ward wins, so the citywide null is not the whole story. | 🟡 | §A41 + §F23 |
| `w_bye` | None (derived) | `montecarlo.py` | **SUPERSEDED 2026-10-10 by §A55.** Each party's by-election weight is its size class's weight from `bye_value.json`; a number in `w_bye` is a sweep override for every party, recorded. Was: typed at 0.40. | — | §A35 |
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
| retiring the generic entrant at nomination close | `montecarlo`, `cities/joburg.toml` | **AMENDED 2026-09-24 (register audit).** CLOSED by the certified roster rather than by a decision: the ENTRANT slot is added only when no arrival is named (`montecarlo.run_model`, the `named_arrivals` guard) and the 2026 spec names 46 (`pools_2026.json` → `seeds`, `roster_source: declared`); `EXPECTED_INERT` certifies the entrant levers inert at 2026. MODEL-LOG §1.245. Was: OPEN GAP, a decision for 16 September. Status marker left for the owner. | 🔴 | §A4 |
| the published 2026 forecast is not the backtested configuration | `montecarlo`, `polling`, and the whole `EXPECTED_I… | **AMENDED 2026-09-24 (register audit).** `contestation_expand` and the generic entrant are both inert at 2026 now (§A4, §A5). What no backtest row can score is the by-election channel (`w_bye`), `GAMMA_FOLD`'s 2026 entry and the declared-roster path (§L). The DA/ANC figures quoted after this are §1.226's, on specs superseded by the 16 and 23 September emits. **AMENDED 2026-09-12.** No house decides the headline any more — the poll channel is OFF (§A8, MODEL-LOG §1.225). The criticism is REDUCED, not answered: the live forecast still runs `w_bye` and `contestation_expand`, which no backtest row can score, so it went from three unscoreable channels to two. Measured effect of the switch on the headline: DA 79 → 68, and the largest-party call becomes a **dead heat** (ANC 47.3% / DA 47.0%) rather than DA 71.4%. §1.226. | 🔴 | §A7 |
| σ_poll, decomposed (`POLL_HOUSE_SD` and the calibration trio) | `polling.poll_sd` / `aggregate_sd` | The flat `POLL_RMS_ERROR` form is retired; the live sum is `polling._sigma_total` and `POLL_HOUSE_SD` survives only as the `n_eff == 0` fallback. | 🟡 | §A9 |
| the derivedness budget | `ITERATING.md`, "the only question" | Declared at 12 coherent seats and never topped up. Governance, not a code lever; it deliberately has no symbol in `src/`. | 🔴 | §A15 |
| how unplaced votes are spread over a party's zeroed pool cells | `pools.balance_within_bounds` | Pool-size proportional, and there is no constant in it — the quantity is derived. Argued, not tested: no backtest can separate the three candidate rules. | 🟡 | §A19 |
| the §3.5 θ sanity-range violations | see `montecarlo.py` | STILL UNACTED ON. The diagnostic prints against the model on every run and nothing reads it; nobody has decided whether the ranges or the draws are wrong. | 🔴 | §A20 |
| the width statistic the report quotes | `compare_history.pit_dispersion` | Probit-SD is what the report quotes, measured on a fixture and ~5-10% attenuated at this model's shift. Its stated successor `dispersion_ratio` is now IN `compare_history` and emitted — this row has not been re-read since. | 🟡 | §A21 |
| doc-vs-artefact tolerances | `compare_history`, and the test that enforces it | Unchanged, and deliberately tight enough that a legitimate re-run will demand the documents be updated. | 🟡 | §A22 |
| the blend weight ignores the ρ record | `levels.spine` | Deliberate, not an oversight: the symmetric form scores 338 against 312. | 🟢 | §A25 |
| the capacity redistribution rule | `montecarlo.py:capped_targets`, the `t[free] += ex… | Still proportional to mass held, and still unmeasured against the two defensible alternatives; the quantity moved is now counted on `capped_targets.moved`. | 🔴 | §A27 |
| the Dirichlet floor | `montecarlo.py` (`DIRICHLET_FLOOR`), applied at `1… | 1e-4 — a numerical guard only. The 0.05 that manufactured ~5pp of citywide vote is gone. | 🟢 | §A30 |
| turnout spread with one observation | `pools.py` | **AMENDED 2026-09-24 (register audit).** 0.30 logits survives only as `_PANEL_SPREAD_FALLBACK`, for a category with no panel measure (and the empty-record default); since §1.162 the width comes from `panel_spread`. The one-prior-election case was 2011, not 2016. Where the fallback still binds is unmeasured. | 🟡 | §A32 |
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
| a reader edits the combined vote | `reader_seats.reader_seats` | **AMENDED 2026-10-09.** An equal surplus goes to the higher vote (Schedule 1 items 13(2)(b), 16(4)(c)); only an equal surplus AND an equal vote reach a tie, and that is drawn by the seeded lot under the context's `lot` (§Q6), where the statute is silent. Roster order decides nothing. The text below said such a tie falls by roster order "where Schedule 1 says by lot"; Schedule 1 gives an equal surplus to the higher vote and has no lot for seats. Was: Owner's decision (DESIGN-decided §10, replacing §9's "PR shares stand for both ballots"). The reader's slider is each party's share of all votes on both ballots together (`combined_shares`), what Schedule 1 counts, with no conversion. What remains a choice: `total_votes` is the start state's combined total (the start is our prediction since 2026-10-08, see §Q), and an exact tie falls by roster order where Schedule 1 says "by lot". The retired assumption's cost: `tests/test_reader_seats.py` prints it. | ⚖️ argued | §M1 |
| γ for a party with no fitted γ | `montecarlo.run_model`, the γ block | 1.0, typed; who takes it is recorded per run (`gamma.default_1.0`). Registered 2026-10-09. | 🔴 | §A48 |
| a VD with no turnout of its own | `montecarlo.run_model`, turnout patterns | The city's roll-weighted mean, typed; the VDs and their roll share are recorded per run (`turnout.mean_fallback_vds`). Registered 2026-10-09. | 🔴 | §A49 |
| an unopposed ward | `seats.eligible_parties`, `levels.unopposed_wards`, `montecarlo.run_model` | Statute in the seat law (PR votes counted twice); the draws refuse a target with one. None on disk or declared. | ⚖️ | §Q7 |
| zero level shock for a seeded arrival | `montecarlo.make_drawer`, `pool_sd_shock` | 0; the width is the within-pool split. Registered 2026-10-09 with item 9's measurement. | 🟡 | §A50 |
| the size the shrink target is evaluated at | `levels._shrink_one` (via `_shrunk`, `theta_prior`) | The party's current size on the route (national share for θ, previous local share for ρ), for every party. Owner's decision 2026-10-09 (BRIEF item 11); was the size its own ratios were measured off. | ⚖️ | §A51 |
| `SIZE_WINDOW_GRID`, `SIZE_WINDOW_MIN_SCORED`, `SIZE_WINDOW_ALPHA` | 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, ∞ · 20 · 0.05 one-sided | `levels.size_window` | The grid the size window `h` is chosen from, the scored-observation minimum below which no window is chosen (∞), and the one-sided level at which a wider window is measurably worse than the best in a cycle-clustered paired comparison; `h` is the widest grid value not measurably worse. Typed; the window itself is measured per target and route. BRIEF item 16, 2026-10-09; the tie tolerance it replaced (0.005) was deleted 2026-10-09 (owner, M3 review). | 🟡 | §A52 |
| a party with no record of its own | `levels._shrunk` (average), `levels.size_sd` via `montecarlo.level_shock_sd` (range) | Its size group's average (the size centre) and range (the size-group width) at its current size, for every party. Owner's decision 2026-10-09 (BRIEF item 17). | ⚖️ | §A53 |
| `GROUP_SHARE_TRIPWIRE_DRAWS`, the tripwire threshold | 0.05 · record + largest one-cycle rise | `montecarlo.group_share_tripwire`, `group_share_record.py` | The group-share tripwire reports a (party, pool) pair whose drawn share of the pool exceeds its record plus the pool's largest real rise in more than 5% of draws. Reports only; changes no number. Item 7's specification, BRIEF item 12. | 🟡 | §A54 |
| `BYE_CLASS_EDGE`, `BYE_VALUE_MIN_PAIRS`, `BYE_VALUE_PERCENTILE`, `BYE_VALUE_RESAMPLES`, `BYE_VALUE_SEED`, `TAU_MONTHS` | 1% · 10 · 5th · 2,000 · 20261010 · 18 months | `byelections.size_class`, `bye_value.evaluate` | The by-election value test (BRIEF item 19): two size classes split at 1% of the previous local list, each weighted by its leave-one-metro-out gain in predicting the 2024 provincial ballot beyond the model's baseline; a class is admitted only if the 5th percentile of 2,000 metro-cluster bootstrap gains is above 0, and takes 0 under 10 pairs. Typed; the weights are measured. A cross-ballot test on the whole record. | 🟡 | §A55 |
| `GAMMA_SLOTS`, `STREAM_CHUNK` | 4 · 256 | `montecarlo.DrawStreams`, `montecarlo.log_gamma_slots` | Numerical constants of the keyed draw streams (design 1c). Distribution-neutral: a gamma is the first accepted of `GAMMA_SLOTS` Marsaglia-Tsang trials, an exhausted draw takes an exact counted fallback (`41_guards.gamma_fallbacks`), and `STREAM_CHUNK` is a buffer length that changes no row. | 🟢 | §A56 |
| `draw_law`, `centre_correction`, `WIDTH_BLOCK`, `RHO_ANCHOR_LO`, `RHO_ANCHOR_HI`, `RHO_GROUP_EDGE`, `LOCATION_CLAMP`, `N_CAL`, `KAPPA_TOL`, `KAPPA_MAX_ITER`, `FALSIFIER_FAMILY_ERROR`, `FALSIFIER_MIN_CENTRE`, `MIN_ESTABLISHED`, `FIXED_POINT_ITERS`, `FIXED_POINT_TOL`, `FIXED_POINT_DRAWS`, `FIXED_POINT_SIZES`, `DIAGNOSTIC_MIN_EFF` | "universal" · 20% · 0.548%, 2.24%, 1% · 0.016% · 4,000, 1e-3, 30 · 0.01, 0.1% · 20 · 2, 0.01, 2,000 | `montecarlo.make_drawer`, `montecarlo.party_width`, `width_record.py` | The universal draw (design 1j v4, option L1, owner 2026-10-12): one log-scale draw for every party, its width one logistic curve in size with one newness term, fitted jointly with a location curve by weighted ML on every earlier party-election; the location is not carried in the draw. The typed values are listed with their evidence in §A57. | 🟡 | §A57 |
| `CHANCE_SCALE` | 1, 15, 45, 55, 75, 90% | `render_sheet.scale_verdict` | Owner's verdict scale for claims rated by chance, 2026-10-07. An edge takes the band nearer a coin flip; judged on the printed chance. The build refuses a verdict that disagrees. Presentation: it moves no draw, seat or probability. | ⚖️ | §P1 |
| `SOWETO_GAZETTEER`, `SOWETO_EXCLUDE`, `SOWETO_CUT` | the place list, two exclusions, 0.5 | `areas.derive` | Owner-accepted 2026-10-07. Which 2026 wards are Soweto's, from voting-station addresses; generated into `cities/joburg.toml` and regenerated by `tests/test_areas.py`. Reaches no draw: only the Mashaba claim reads it. | ⚖️ | §P2 |
| `REALISTIC_PARTNERS`, `ZILLE_RED_LINES` | ActionSA with the PA, or the ANC; the EFF and MK ruled out | `render_sheet.da_coalitions` | Owner's definition of a DA win for the Mashaba claim, 2026-10-07: a realistic coalition the DA leads. The every-party coalition is printed as context, not rated. Reaches no draw. | ⚖️ | §P3 |
| `MERGER_RETENTION` (range `MERGER_RETENTION_RANGE`) | 0.75, range [0.5, 0.9] | `pools.apply_mergers` | Owner's decision 2026-09-28. The share of an off-ballot merger partner's baseline moved to the partner on the ballot, only onto records the successor already holds. Not measured: no merger in the archive is identifiable. Swept at 0, 0.5, 0.75 and 1.0 on Johannesburg 2026 (MODEL-LOG §1.275). | 🔴 | §O1 |

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

**Now.** **AMENDED 2026-09-24 (register audit).** CLOSED by the certified roster rather than by a decision: the ENTRANT slot is added only when no arrival is named (`montecarlo.run_model`, the `named_arrivals` guard) and the 2026 spec names 46 (`pools_2026.json` → `seeds`, `roster_source: declared`); `EXPECTED_INERT` certifies the entrant levers inert at 2026. MODEL-LOG §1.245. Was: OPEN GAP, a decision for 16 September. Status marker left for the owner.

**Record.** **RAISED BY THE OWNER 2026-08-22 and it is a real gap.** The `ENTRANT` column exists iff `entrant_prob > 0`, and **no code path reads a nomination roster to decide that.** The generic slot is a stand-in for not knowing the ballot; nomination lists close and are published on 16 September, and at that moment the ignorance it models is gone. Two cases and neither is automatic: if the lists carry a genuinely new party it should be **named and seeded** in `judgements/joburg-2026.toml` and `entrant_prob` set to 0, because otherwise the same arrival is counted twice; if they carry none, `entrant_prob` should be 0 because the modelled event is known not to have occurred. Measured cost of leaving it, Johannesburg 2026 at 500 draws: **DA 80 → 81, ANC 63 → 64** between 0.25 and 0. Small, and the wrong kind of small — the slot's MEDIAN is zero while its MEAN carries `0.25 × E[triangular(1%, 4%, 12%)]` ≈ **1.42% of the vote**, `coherent_seats` uses the mean, and largest remainder converts it. It is part of the **+6.54pp phantom** the backtest already reports. **Do NOT automate it as "roster known ⇒ no generic entrant"**: at every backtested target the roster is also known, and there the generic slot IS the forecast for the party that arrived — it is what gets relabelled onto the AIC at Johannesburg 2016. Naming arrivals individually instead is `arrival_group_draw`, measured at 254 → 348 and rejected (§1.63). So this is a decision to be taken once, at nomination close, not a rule. Task A4

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** The closing sentence quotes `arrival_group_draw` as *"measured at 254 → 348 and rejected"*. §A6 forbids exactly that quotation — *"do not quote it as the live rejection"* — because the baseline was superseded by §1.94 and the arm also deleted the splinter seed. The rejection itself stands on the 2026-08-29 re-run; the number does not.

### §A5 · `contestation_expand` — 0.220 — 🔴

**Where.** `montecarlo.py`, applied in `levels.projected_contestation`

**Now.** **AMENDED 2026-09-24 (register audit).** Ships 0.220 and is INERT at 2026 since the declared ward slates reached the correction (MODEL-LOG §1.252; `EXPECTED_INERT[("contestation_expand", "2026")]`), for as long as the roster is `complete = true`. It acts at no backtest target either (§1.60).

✅ **TRUE AT 2026 SINCE 2026-09-23 — MODEL-LOG §1.252.** It was FALSE for a week: the lists were pasted on 16 September and nothing wired them into `levels.contestation`, so the lever went on projecting slates it could have read (§1.251). `contestation` now reads the declared `[roster.wards]`, the lever is inert at 2026 (one fingerprint across expand 0.0/0.22/0.5), and `tests/test_levers_are_live.py` finally carries a 2026 entry. ⚠️ An INCOMPLETE declaration revives the lever on the parties it does not name, by design.

**Record.** How much a party's ward slate grows between local elections, used **only where the target's nomination lists are not published** — every live forecast, no backtest. `now = was + expand·(1 − was)`. **It replaces an assumption made by omission**: `levels.contestation` reads who stood from the target's own result file, so at 2026 the correction was silently the identity, i.e. every party fields exactly the slate it fielded five years ago. **The default is measured**: across the eight metros and every consecutive LGE pair on disk (n=165 parties present at both) the median party moves **+0.220** of the way to a full slate and **65.5% expand**. The most recent transition alone (2016→2021) gives per-metro medians of +0.46 / +0.14 / +0.78 / +0.59 / +0.63 / +0.20 / +0.71 / +0.06 — about +0.5 — which is what a fragmenting party system looks like, and is why this is a lever and not a constant. **ARGUED, NOT TESTED, and live exactly where nothing can check it** — the same position `pa_contestation_uplift` was in, and that is why it is 🔴 rather than 🟡 despite a measured default. It acts on THIN SLATES, which is the intended asymmetry: at Johannesburg 2026 the PA (52 of 135 wards in 2021) goes 17 → 19 → 22 median seats at expand 0.0 / 0.220 / 0.5 with ward wins 4.0 → 6.0 → 8.6, while the DA gives up 83 → 81.5 → 80. **Superseded, not supplemented, by real lists**: when the IEC publishes 2026 candidate lists (task A4) `contestation` returns them, the projection is not called, and this lever goes inert — asserted in `tests/test_levers_are_live.py`. Backtests are bit-identical with it at any value. MODEL-LOG §1.60.

### §A6 · `arrival_group_draw` — False — 🟢

**Where.** `montecarlo.py`, read in **`make_drawer`** — **NOT `blended_centres`**, corrected 2026-08-29 (§1.136); `blended_centres` never touches the key, so the CENTRES are byte-identical across both arms and this lever cannot move a centre

**Now.** Ships False. The rejection was re-run on the label-free referee 2026-08-29 and refuted again; the 254 → 348 figure is superseded and must not be quoted.

**Record**, oldest first:

1. Whether an arriving party's size comes from the ARRIVAL-GROUP mechanism — a group total drawn from a fitted lognormal and split among named arrivals by a Dirichlet — or from the generic `ENTRANT` slot, a Bernoulli times a triangular.
2. **UNTIL 2026-08-20 THIS KEY DID NOT EXIST.** `blended_centres` read `scenario.get("arrival_group_draw")`, it was in no `DEFAULTS`, and both `parse_set` and `read_scenario_file` reject a key that is not already in the scenario — so `--set` and a config file could not create it either. The mechanism was not off, it was **unreachable**, and `MACHINERY.md` described it as *switched off*, which claims a switch that did not exist. Same class as `LEVEL_DF` bound as a default argument (§1.33). It escaped both lever guards for the one reason neither can catch: they iterate `DEFAULTS`. **And it was broken** — the branch raised `NameError: dirichlet_floor` on the first run that reached it, so the code comment scheduling a retry "by 2026" scheduled a crash, and the rejection measurement recorded against it was taken on code that has since drifted. Now declared, repaired and **measured on nine city-years, which the original Johannesburg-only rejection never was: coherent seat error 254 → 348 and CRPS 232.9 → 296.0, worse in six city-years and better in one.** The rejection is confirmed and strengthened. Ships False — what changed is that "off" is now true rather than merely written down. MODEL-LOG §1.63.
3. **⛔ AND IT DELETES THE SPLINTER CHANNEL (2026-08-29, §1.136).** `arrival_group_spec` is handed `sorted(arrivals)` — the full key set of `arrival_rules`, splits and entrants alike (`arrival_group_spec`'s call site in `pools.py`) — so all 32 seeded parties at Johannesburg 2021 are in its weights, ActionSA included, and `make_drawer` zeroes those columns before overwriting them: ActionSA actual **18.12%**, incumbent pool-splinter seed — `seeds["ASA"]` in the emitted spec, **not typed here** — replaced by a challenger-sized **0.18%**. ⚠️ (2026-09-13: this row said "6.85%". That was the seed in the spec current on 2026-08-29; the 2026-09-02 archive holds 6.756% and the live `data/processed/pools_2021.json` holds 6.840%. Three documents typed the same emitted value and all three disagreed — read it from the spec for the run being described.) So this is not "a fitted group replacing a typed slot"; it is that AND the removal of the seed carrying the largest arrival in the panel, and it cannot be read as a test of the group estimator while both are true. **The 254 → 348 above is a NINE-city-year figure scored through the outcome-favourable relabel, and §1.94 superseded that baseline (376 on sixteen) — do not quote it as the live rejection.** The fair re-run on the label-free referee (2026-08-29) refutes it again: 2 of 8 metros at 2021, pooled Σ|mass_err| 0.2714 → 0.5084, Key 2's level-free width 1.2000 → 1.3557.

### §A7 · the published 2026 forecast is not the configuration the backtest scores — 🔴

**Where.** `montecarlo`, `polling`, and the whole `EXPECTED_INERT` list

**Now.** **AMENDED 2026-09-24 (register audit).** `contestation_expand` and the generic entrant are both inert at 2026 (§A4, §A5); what no backtest row can score is `w_bye`, `GAMMA_FOLD`'s 2026 entry and the declared-roster path (§L). Figures below are §1.226's, on superseded specs. ⛔ **AMENDED 2026-09-12 — THE "ONE HOUSE DECIDES THE HEADLINE" CLAIM
IS RETIRED. NO POLL REACHES THE FORECAST AT ALL** (`poll_paths="off"`, §A8,
MODEL-LOG §1.225). Confirmed against a `--run-dir` trace of both targets: neither
`poll_level` (arrivals) nor `metro_poll` (metro blend) appears in
`_constants_read` at 2021 or 2026, so the poll levers are now unscoreable at
NEITHER target rather than at 2026 only.

**The criticism is REDUCED, NOT ANSWERED, and this entry stays 🔴.** The live
forecast still runs machinery no backtest row can score, and the same trace
names what is left: the **by-election channel** (`w_bye`, `bye_weight_mode`,
`BYE_MIN_WEIGHT`, and the ward-local variants — `byelection_party_deltas.csv`
exists only at 2026, and `30_centres.route_notes` carries nine parties at 2026
against **zero** at 2021), **`contestation_expand`** via
`levels.projected_contestation`, the **generic `ENTRANT` slot** and its three
levers, and `GAMMA_FOLD`'s 2026 entry. So the count went from three such
channels to two, and the largest single block — the seven poll levers — is gone.

⚠️ **This "Now." line said the opposite for the first hours of 2026-09-12**,
after the summary table row above had already been corrected. `CLAUDE.md` §2
requires the record to change in the same commit as the model; the table moved
and the prose did not, which is the same one-copy-updated failure the file
warns about. Found by a trace audit, not by a test — nothing checks this line.

**Record.** **MEASURED 2026-08-22 (§1.69), and it is the strongest criticism available to a reviewer.** The headline "254 coherent against uniform swing's 376" is scored on a configuration the live forecast does not run, in both directions. **What 2026 GAINS that no past target can score:** `w_bye` (the by-election window is 2022-06 to 2026-02, so no backtested target has any), `contestation_expand` (superseded by real nomination lists wherever a result file exists), and all six poll levers (the register holds no metro poll of Johannesburg declared for 2021). **What 2026 LOSES:** the arrivals poll path, worth **48 coherent seats** (§1.65) — see the row above. And the magnitude is not small. Johannesburg 2026 at `poll_paths` off against all, 600 draws: **DA 65 → 78 seats, ANC 68 → 63, ASA 31 → 25 — and the lead FLIPS**, from ANC-largest to DA-largest. `H_eff` still prints as **1.0** — the two admitted Johannesburg polls are both SRF/Victory Research — but **there is no longer a cap to sit on** (2026-08-24, §1.91). The influence is now set by the σ arithmetic and not by `poll_house_k`, which is the reverse of what this row said for a day. Measured on the shipped register at target date: DA σ **5.057pp** against a floor of **4.595pp**, ANC 4.922pp, MK 4.794, ASA 4.772, EFF 4.720. MEASURED on the settled tree (`tests/test_drawer.py`, re-recorded 2026-08-24): the DA's blend weight is now **0.484 by arithmetic** where the cap used to pin it at exactly 0.500, and the 2026 forecast moves by about a seat — **DA 79 → 78, ANC 63 → 64, ASA 24 → 25**. So the dependence on one house is essentially UNCHANGED in magnitude; what changed is that it is now set by the σ arithmetic and can be argued with, rather than by a typed constant. The 65 → 78 / 68 → 63 poll-on-vs-off figures below therefore still stand to within a seat. One house, two waves, decides the headline. Quote this beside the 254 wherever the 254 is quoted; it is not a defect to be fixed but a dependence to be disclosed

⚠️ **Restructure note, 2026-08-31 — flagged, not resolved.** This entry quotes the arrivals poll path as *"worth **48 coherent seats**"* and points at "the row above". §A8 retracts that number in terms — *"The 48 must not be quoted; it was, twice"* — and measures the whole channel at **−6** coherent seats on sixteen city-years. The two entries have contradicted each other since 2026-08-25 and the later one says so. Nothing here reconciles them: which figure is right is a judgement, and it changes what a reader believes about the published forecast.

✅ **RECONCILED 2026-09-12 (§1.225), and neither figure survives as stated.** The
24-row panel decomposes the channel EXACTLY, because the two paths fire on
disjoint city-years — the register holds no admissible metro poll for 2021, and
the 2016 national poll names only ANC/DA/EFF, every one of which has a baseline,
so arrivals cannot fire at 2016:

| path | rows it acts on | Δ seats (off − on) | Δ CRPS |
|---|---|---|---|
| metro blend | the three 2016 metro-poll cities | **−4** | −1.74 |
| arrivals | the four 2021 ActionSA metros | **+2** | −2.72 |

So the arrivals path is worth **+2 coherent seats**, not 48 and not −6: the panel
seat metric mildly prefers to KEEP it, while CRPS prefers to lose it. The −6 of
§1.94 was the two paths summed on a smaller panel. **Both quoted figures were
aggregates of two mechanisms that move in opposite directions**, which is why
neither replicated. ⚠️ Under rule 11 the effective sample is close to two events
— ActionSA's 2021 arrival seen in four metros of one cycle, and the three Ipsos
2016 metro polls — so none of these three numbers should be quoted as a rate.

### §A8 · `poll_paths` — **"off"** — 🟢

**Plain — No poll is used.** There is no designed rule yet for how several polls
combine. With polls in, the forecast moves toward the polls the rules admit;
what that was worth when measured is under *Where polls fit*, below. On [your
forecast](your-forecast/) you can pick one poll at a time and choose how far to
believe it.

**Where.** `montecarlo.py`, gates both live poll paths

**Now.** ⛔ **SHIPS "off" SINCE 2026-09-12. THE FORECAST USES NO POLL AT ALL.**
The owner's decision, taken on design grounds rather than on score — we had no
designed answer to how several polls should combine, so the channel is off
until that is settled and a per-poll reader control is built. Nothing is
deleted and `--set poll_paths=all` restores the previous forecast exactly.
MODEL-LOG §1.225; pre-registration
`prereg/2026-09-12-polls-out-of-the-forecast.md`.

⚠️ **While this ships "off", EVERY other poll lever in this register is inert
by configuration** — `poll_credence`, `poll_house_k`, `poll_deff_subsample`,
`poll_screen_sd`, `poll_drift_per_root_day`, `poll_min_n`,
`poll_half_life_days`. Their rows below describe what they do when the channel
is on, which is the state this project intends to return to. They are **not**
dead: `tests/test_levers_are_live.py` carries a `CONDITIONAL` entry for each
that opens the gate and asserts the lever still moves the forecast, so the
machinery cannot rot while it is switched off.

**Record**, oldest first:

1. Which poll paths run: `"off"` · `"arrivals"` (a national poll converted to the contested area, for parties with NO record) · `"all"` (adds the metro-poll inverse-variance blend).
2. **Added 2026-08-21 so the channel could be MEASURED for the first time** — until then the only way to switch it off was to empty `polls.json`, and nothing in `sweep.py`, `compare_history` or the tests scored it. ~~Nine city-years at 1500 draws: off 304 / arrivals 256 / all 254.~~
3. **REVERSED ON SIXTEEN, 2026-08-25 (§1.94).** Sixteen city-years, 1500 draws, paired on identical seeds: **off 376 coherent / CRPS 324.6 · arrivals 378 / 327.6 · all 382 / 329.0** — monotone the OTHER WAY. The channel is worth **−6 coherent seats**: turning it off is better, on seats and on CRPS. It fails two of Key 1's three conditions. **This is not the doubled panel** — on §1.65's own nine city-years it measures **−4**. What changed is that the model WITHOUT the channel improved sharply (Tshwane 2021 52→34, Ekurhuleni 38→28) while the model with it did not: the channel was patching a hole, and the hole was fixed. The 48 must not be quoted; it was, twice, after §1.70 instructed that every nine-city-year number be re-read here, and the metro path two more; **no city-year is made worse by either.** Ships at `"all"`, which is seat-identical to the committed artefact. **Two caveats that must travel with the number**: the whole arrivals effect is one party (ActionSA) in four metros of one cycle, so under rule 11 the effective sample is close to one; and the path is **dead at 2026** for want of a `NATIONAL_VOTES["2026"]` entry, so the 48 seats are measured on a channel the live forecast does not currently have. MODEL-LOG §1.65.
4. **SWITCHED OFF, 2026-09-12 (§1.225).** Twenty-four city-years, 1000 draws:
   **all 725 coherent / CRPS 545.84 · off 723 / 541.39**, margin over uniform
   swing 18.1% → 18.3%. Every headline prefers "off" and none of them by much.
   ⛔ **The −2 is the residue of +6, −4 and −4**: seven rows moved, seventeen
   were identical, and ekurhuleni 2021 moved six seats *against* the change.
   **Do not quote −2 as the value of the channel** — the honest statement is
   that its contribution to seat error is not distinguishable from zero on 24
   rows, and that §1.94's −6 on sixteen and this −2 on 24 are both inside the
   swing of a single city-year. The decision was not taken on this number and
   this number does not support or contradict it; it rests on the design
   argument in §1.225. Every 2011 row moved by exactly zero, which is what
   establishes that the switch turns off what it claims to: the register holds
   no 2011 poll.

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

**Now.** **AMENDED 2026-09-24 (register audit).** Unchanged at [0.01, 0.04, 0.12]. It acts only where no arrival is named — of the backtest targets, 2011 alone. At 2016, 2021 and 2026 the named seeds retire the generic slot (§A4), so the "1.42% of the vote in every run" this row used to state holds nowhere the forecast is published.

**Record.** The arriving party's size. With `entrant_prob` it puts an expected **1.42%** of the vote on a generic newcomer in every run — which matched the AIC's actual 1.62% in 2016 almost exactly (measured: 1.39% drawn, 3.82 seats, against 1.62% and 4), and was 30× short of ActionSA.

### §A18 · `LEVEL_DF` — 7.0 — 🟡

**Plain — Large surprises are allowed.** Each party's simulated support is drawn
with heavier tails than a bell curve, so a large miss in either direction comes
up more often than a bell curve gives. The record does not fix how heavy.
Lighter tails make extreme results rarer and scored the same against past
elections; much heavier tails scored worse. It cannot be changed on [your forecast](your-forecast/).

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

**Plain — The largest parties are pulled down.** Before the simulations are
drawn, each party's expected share is cut by an amount that grows with its size,
and the vote freed is returned to all parties in proportion to their share.
Without the cut, forecasts of past elections gave the largest parties too much
and the middle-sized parties too little; adding it was the largest single
improvement the model has had. The smallest parties are now forecast slightly
too high. It cannot be changed on [your forecast](your-forecast/).

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

### §A29 · `level_sd_default` — ~~0.45~~ — ⚫ deleted

**Where.** `montecarlo.py`

**Now.** DELETED 2026-10-09 (record 6). `montecarlo.level_shock_sd` has two rules, the measured width and the size group's width at the party's size; a drawn party with neither stops the run.

**Record**, oldest first:

1. The level spread for a party with no measured `sd(log θ)`. Typed. Narrower than it looks: `levels.theta_prior` gives every party in the baseline an `sd`, so this binds only on parties outside it.
2. **PROMOTED 2026-08-20 (§1.63), which was this row's own instruction.** It was read as `scenario.get("level_sd_default", 0.45)` and was in no `DEFAULTS`, so it was frozen at 0.45 and could not be moved by `--set` or a config file — the same defect as `arrival_group_draw` and `turnout_correlation`, all three found at once by the new `test_no_scenario_key_is_read_without_being_declared`. Declared at 0.45, so nothing moved. And the prediction in this row is now **confirmed by measurement**: perturbed to 1.60 it is byte-identical at 2021 and 2026, because the measured branch is taken for every party. It is in `EXPECTED_INERT` with that reason. A fallback that never fires is what you want; it matters only if the baseline ever stops covering the ballot.

3. **THE BASELINE STOPPED COVERING THE BALLOT, 2026-09-16 — the case item 2 said it "matters only if".** The declared certified roster names 82 parties; the lever harness's fallback gate reports 74 parties in the 2026 index, all pool members, and 44 with no measured sd — EXPOSED TO THE FALLBACK. The `EXPECTED_INERT` excuse at 2026 was removed in the same commit. **⛔ CORRECTED THE SAME NIGHT, BY MEASUREMENT.** The line above was written from the gate's report, and the suite then perturbed the lever: nothing moved. The gate was wrong — it asked whether a metro poll exists, not whether polls are on — and is fixed. So 0.45 does NOT shape tonight's forecast; it would shape 44 small parties' level spread if `poll_paths` returns to "all". How to check it then: the arrival record's own dispersion for comparable parties. 🟡.

4. **AMENDED 2026-10-09 (model correction batch, item 8): it now binds in the draws, outside the poll blend.** The roster parties whose only record is the previous LGE (`levels.local_record_only`) enter the run after `levels.theta_prior` has run, and `make_drawer` gives them `level_sd_default`. Where `theta_prior` does emit an sd for one (a party in the θ record with no national baseline), it is the size line evaluated at the 1e-5 size floor, a width at a size the party does not have, and for some of them it is `SD_CEILING` (the estimation width-ceiling tripwire caught one at joburg 2011). `make_drawer` does not use it for these parties. This departs from SPEC §1.7 step 6, which assumed they were absent from `theta_prior`'s output (SPEC R3.7). Which parties took it is named per run in `41_guards.level_sd_default_parties`. Item 17 (a later step of the same batch) replaces it for them with the size-group width; after that it binds only where no size exists.

5. **AMENDED 2026-10-09 (item 17, SPEC R2.2).** A party with no measured width (absent from `theta_prior`'s `sd`, or an item-8 party) now takes the size group's width at its own size in the run's baseline, `levels.size_sd` on `theta_prior`'s fit, through `montecarlo.level_shock_sd` (one rule for the drawer and the poll blend). `level_sd_default` binds only where the party has no size (base ≤ 0) or the run has no θ fit. The item-8 parties are recorded with their drawn width in `41_guards.level_sd_at_size`. Whether the lever is now inert again at 2021 and 2026 is `test_levers_are_live`'s to say (run after this batch's last commit). §A53.

6. **DELETED 2026-10-09 (owner, M3 review row 7): "If the old constant has been replaced with new machinery it should be deleted."** Evidence it bound nowhere: an in-process scan (`run_model`, 20 draws, the M3 review's window rule in place) at every emitted city-year, the eight metros at 2011, 2016 and 2021 and Johannesburg and Tshwane at 2026, wrapped `level_shock_sd` and recorded every call: no party the run draws reached the fallback. Pool members outside the run's universe did reach it at 2011 (they have no baseline size); their widths were computed and never used, since the IPF draws only members in the run's index. `make_drawer` now asks only for those members, and `level_shock_sd` raises `SystemExit` where a drawn party has no measured width, no size and no θ fit. The `41_guards.level_sd_default_parties` field and its checks went with it. The name is in `tests/test_register_matches_code.py`'s `DELETED`.

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

**Now.** **AMENDED 2026-09-24 (register audit).** 0.30 logits survives only as `_PANEL_SPREAD_FALLBACK`, for a category with no panel measure (and the empty-record default); since §1.162 the width comes from `panel_spread`. The one-prior-election case was 2011, not 2016. Where the fallback still binds is unmeasured.

**Record.** When a city has only one prior local election, the turnout band's width is typed. **This is every 2016 target.**

### §A33 · `bye_weight_mode` — `"fixed"` — 🟡

**Where.** `montecarlo.py`

**Now.** Defaults to `fixed`. `inverse_variance` is built and derives the weight; switching it moves the published 2026 forecast and no backtest can score either — the owner's call.

**Record.** How the by-election reading is weighed against the spine. **`"fixed"` is `w_bye` above — typed, untested.** `"inverse_variance"` DERIVES it: combining two unbiased estimates, the minimum-variance weight on the second is `v₁/(v₁+v₂)`, with `v₁` from the θ band and `v₂ = sd²/n` from the contests. At joburg 2026 it runs **0.031 (ATM, 3 contests) to 0.722 (EFF, 11)** against the typed 0.40, moving **2.005pp** of centre — MK, whose 8 contests span a factor of 31, earns **0.216**. A measurement replacing a judgement, which is Key 3's currency. **Defaults to `fixed` because switching it moves the published 2026 forecast and NO backtest can score it** (`bye` is empty at all sixteen panel city-years). Adopted as a lever on the pollster's recommendation; the owner's call to enable. §1.121, §1.122

### §A34 · ~~turnout-adjusted by-election weighting~~ — ⚫ refused

**Where.** —

**Now.** CONSIDERED AND REFUSED 2026-08-28 with the measurement (leave-one-contest-out RMSE 36.46pp against uniform's 24.66pp). A per-party sensitivity is worth pre-registering; the uniform form is not.

**Record.** **CONSIDERED AND REFUSED 2026-08-28, with the measurement.** Leave-one-contest-out on the by-election data — the only out-of-sample test this channel will ever have before an election — gives RMSE **36.46pp against uniform's 24.66pp**. The aggregate hides the reason: it *helps* ANC, EFF, MK and AIC and is catastrophic for the **DA (47.30 → 78.98pp)**, because turnout sensitivity is **party-specific and signed** — DA **−0.925**, EFF **+0.842**, ANC **+0.720**. A uniform ratio applies one sign to every party. A PER-PARTY sensitivity is worth pre-registering; the uniform form is not. §1.122

### §A35 · `w_bye` — 0.40 — SUPERSEDED 2026-10-10 by §A55

**SUPERSEDED 2026-10-10 (BRIEF item 19).** `DEFAULTS["w_bye"]` is `None`: each party's by-election evidence is weighted by its size class's weight, measured by `src/bye_value.py` and read from `data/processed/bye_value.json` (§A55). A number in `w_bye` remains as an override for sweeps and for the reader page's cells; it applies to every party and is recorded as `w_bye.override`. A missing or stale `bye_value.json` at a target that reads by-elections stops the run. The text below describes the typed 0.40 it replaced; the reader-facing paragraph is the site's and changes with the next publication.

*(Its reader-facing Plain field moved to §A55 on 2026-10-10: a retired call is not shown to a reader as a live choice.)*

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

⛔ **STANDING REFUSAL (owner, 2026-09-12): `ward_noise_sd` IS NEVER WIDENED TO
COVER A CITYWIDE LEVEL ERROR.** Recorded as a rule because it is the tempting fix
and it will be proposed again.

**What prompts it.** The Johannesburg 2021 backtest called 127 of 135 wards
correctly, and two of the eight misses — wards 79800017 and 79800018, won by the
Patriotic Alliance — were called at `P(DA) = 1.000`. A probability of exactly one
on an outcome that did not happen is an infinite log score, so the instinct is to
widen the ward noise until the model stops being certain.

**Why that is the wrong repair, with the arithmetic.** The PA was forecast at a
citywide PR **mean of 0.09% against 2.96% actual — a 32× level miss** (on the
median, 0.03% against 2.96%, a 100× miss). The ward layer
placed a correct citywide total; there was no citywide total to place. Widening
`ward_noise_sd` far enough to make that 32× level error survivable would spend the
**96.8% pooled ward hit rate** — the model's one result that beats every naive
reference in all three cycles — to buy two wards. That is treating the symptom,
and it would degrade the layer that is working to disguise a failure in the layer
that is not.

**What the honest repairs are instead.** (1) The ward ceiling is a *reporting*
artefact: at 2000 draws any probability below 1/2000 is unrepresentable, so
`1.000` is partly draw-count. Report `1 − 1/N` and publish the reliability table
(fix #23). (2) The three seat columns with `p_any = 0.0` on parties that won
seats — ALJAMAAH 2011, OKM 2011, ALJAMAAH 2016 — have **no column at all**,
because the run's universe is the NPE baseline plus seeds; the repair is
`universe = baseline ∪ roster` (fix #22). Neither touches ward noise. (3) The
PA's level is an arrival-channel defect and belongs to the arrival work.

⚠️ **The figures above are from `data/processed/history.json`, joburg 2021** —
the PA's row in that record's `votes` table, which is a POSITIONAL list carrying
no field names of its own:
PR median `votes[1]` = 0.0297%,
PR mean `votes[2]` = 0.0913%,
PR actual `votes[3]` = 2.9604%.
They are not from a
`diagnose` run — two runs at different draw counts give slightly different
means, and a figure in prose has to say which one it came from. This entry said
"0.09% ... a 33× miss" until 2026-09-12: 0.09% was a *truncation* of 0.0969%
(it rounds to 0.10%), and the 33× was then computed from the truncated value
rather than from the data. Both halves of `CLAUDE.md` §2's "never type a model
figure into prose" — quoted here, inside a rule about discipline, by me.
⛔ **AND A THIRD COPY OF THE SAME NUMBER SURVIVED THE FIX UNTIL 2026-09-13.** The
"33×" was corrected in the sentence that derives it and left standing in the
sentence that argues from it, four paragraphs later — so this entry carried 30×,
79× **and** 33× for one quantity at once. Re-derived from the artefact
(Atlas, read-only, 2026-09-13; RE-QUOTED 2026-09-18 after the panel grew to 24
city-years, which moved both the mean and the median): `votes[3]/votes[2]` =
2.9604/0.0913 = **32.4×** and `votes[3]/votes[1]` = 2.9604/0.0297 = **99.8×**;
there is no 33, and the earlier 30.5×/78.9× were right for the artefact as it
stood on 13 September. **RE-QUOTED AGAIN 2026-09-23** from the window's
artefact (`seat_abs_err_coherent=733/@2ac4c1eb/1000d/pools:7264a929/rows=24`),
which re-emitted every spec: the mean moved 0.0937% → 0.0913% and both ratios
were recomputed from it rather than carried across, 31.6× → 32.4× and
99.6× → 99.8×. *Correcting
a figure means correcting every copy of it, and the copies are where the rule
actually bites.*

⚠️ **And the citation names a POSITION, because there is no field to name.** The
first version of this line cited the three numbers as pr_median, pr_mean and
pr_actual in backticks, as though they were keys of the artefact. They are not:
`vote_table` returns unnamed tuples and the record stores them as bare lists, so
two of those three names exist nowhere in this repository and the third exists
only in `montecarlo.py` as a key of a different structure — which is why a
name-level check waved it through. `test_every_symbol_the_register_names_exists`
caught the other two on the day they were written. **Invented names are the same
defect as a stale line number**: they are checkable-looking and they check
nothing, so cite the position, which the artefact actually has.

**Status: argued, not tested.** No measurement is offered for the refusal itself;
it is a statement about which layer owns the error, and the evidence is the
decomposition above. If someone believes a ward-layer change is warranted, the
bar is a measurement showing the ward layer mis-places a level it was given
correctly — not a ward that was lost because the level was wrong.

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

**Note, 2026-10-09 (model correction batch, item 8).** A roster party with a previous-LGE list vote and no national baseline is no longer outside the run: `levels.local_record_only` enters it at its previous-LGE list share, sized on the spine's local route. The residual, roster parties with no record at all, is named per run in `41_guards.roster_unrepresented` (`montecarlo.roster_universe_check`) and refuses a live forecast.

### §A43 · `apply_city` never resets `DEFAULTS` — 🔴

**Where.** `montecarlo.py`

**Now.** **AMENDED 2026-09-24 (register audit).** FIXED: `apply_city` clears `DEFAULTS` and restores a pristine copy before applying a city (since 2026-08-18), guarded by `test_apply_city_does_not_leak_one_citys_scalars_into_the_next`. Johannesburg declares 11 scalars, not sixteen. Status marker left for the owner.

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

### §A47 · which city is a splinter's home, and which pair of elections it is measured across — `SPLITS`: ASA→JHB · GOOD→CPT · MK→ETH · NFP→ETH · COPE→None · EFF→None — 🔴

**Where.** `pools.SPLITS`, read by `pools.home_splinter_record` (which record) and by `pools.arrival_rules` (which record sizes a given party in a given city). Distinct from §A44, which registers the THRESHOLD (`MIN_HOME_SPLITS`) and the binary shape; this registers the six per-party assignments those mechanisms are applied to, and it is upstream of them — the threshold only matters once a party has been called *at home*.

**Now.** Six typed assignments, none derived, none swept, and no test constructs a violation of any of them. Two of the six carry no home city at all and are therefore invisible in every artefact: a party with no home city produces no marker, no note and no banner line.

**Record.**

1. **What a `home` is.** A biographical claim: the city where the splitting leader's own following is. Nothing in the data derives it, and nothing could — it is a fact about a person, asserted. `home_splinter_record` uses it twice: to decide which historical splits count as *home* observations at all, and (through `arrival_rules`) to decide whether the party being sized is at home in the city being forecast. **Both branches are selected by these six literals.**

2. ⛔ **ASA→JHB IS THE SINGLE ASSIGNMENT BEHIND THE PANEL'S LARGEST ERROR.** It is what routes ActionSA to the home record at Johannesburg and to the away record everywhere else, and the home record is what the emitted 2021 spec's `seed_notes["ASA"]` names as the source of its band. Flip that one literal and Johannesburg's largest arrival is sized from a different record. It has never been varied.

3. ⚠️ **`home = None` IS ALSO A JUDGEMENT, AND IT IS THE ONE NOTHING CAN SEE.** COPE and the EFF are declared to have had no home city. That is arguable in both cases and it is asserted in neither direction by any measurement. An unset home costs a party its home branch everywhere, which means it is sized from the away record **in its own home city if it has one**, silently — there is no marker, no note and no banner line for a home that was never declared. The other four assignments at least announce themselves through the spec's `splinter_home` marker. These two announce nothing, which makes them strictly harder to audit than the ones that are wrong out loud.

4. **`measured_from` is the second half of the same call.** It names the pair of elections each split is measured across — the parent's share before, the splinter's after — and it is what the target cutoff filters on (MODEL-LOG §1.232). **ASA's is unset**, which is deliberate and load-bearing: ActionSA contributes no row to the home record and so cannot size itself. `home_splinter_record`'s `exclude` argument enforces the same thing a second way for every caller.

5. **The measured consequence is §A44's and is not restated here.** The gradient across metros that the binary home/away bucketing flattens, and the Tshwane seed it produced, are in §A44. What §A44 does not cover is that the bucket a party lands in is *chosen per party*, by this table.

6. **How to check it.** The assignments themselves:

       .venv/bin/python -c "import sys; sys.path.insert(0,'src'); import pools; \
         [print(k, v.parent, v.home, v.measured_from) for k, v in sorted(pools.SPLITS.items())]"

   What each target actually uses, which is the quantity that reaches a forecast — `pools.home_splinter_record(before_year=<target>)`, or the `splinter_home` marker in the emitted spec, which records it per run.

7. **Declared 2026-09-13**, on the round that corrected `backtest.FITTED_ON["splinter_home"]` (MODEL-LOG §1.232). Until then `splinter_home` appeared nowhere in this register at all: the mechanism was in §A44 and the per-party assignment it applies to was in neither.


### §A48 · γ for a party with no fitted γ — 1.0 — 🔴

**Where.** `montecarlo.run_model`, the γ block: a party's γ comes from the fold's parameters, else from `gamma_recent.csv`, else 1.0.

**Now.** A party with neither fitted γ takes 1.0, meaning its share deviates from the city mean across VDs exactly as the baseline's pattern does. Typed, never swept. Which parties took it is recorded per run as the delivery note `gamma.default_1.0` (the list of parties), so the count is read from a run, not from here.

**Record.**

1. Registered 2026-10-09 (BRIEF item 10, integrity review): the default was in the code and in `MACHINERY.md` §4 as JUDGED, and in no register entry.

**How to check it.** The `gamma.default_1.0` note in a run's delivery log; a sweep of the default over the parties that take it, scored on the panel.

### §A49 · a VD with no turnout of its own takes the city's roll-weighted mean — 🔴

**Where.** `montecarlo.run_model`, the turnout patterns: a VD missing from `turnout.csv`'s projected ratio or previous-LGE level takes the city's mean of that pattern, weighted by registered voters.

**Now.** A typed fallback: a VD with no history is treated as an average VD. How many VDs took it, and their share of the roll, is recorded per run as the delivery note `turnout.mean_fallback_vds`.

**Record.**

1. Registered 2026-10-09 (BRIEF item 10, integrity review): unregistered until then.

**How to check it.** The `turnout.mean_fallback_vds` note in a run's delivery log. A material roll share there is the case to measure against an alternative fill (the ward's mean, or the VD's neighbours).


### §A50 · zero level shock for a seeded arrival — 0 — 🟡

**Since 2026-10-12 read only under `draw_law = "incumbent"`** (§A57); the shipped universal draw does not read it.

**Where.** `montecarlo.make_drawer`, `pool_sd_shock`: every pooled party takes its own level-shock sd except a seeded arrival, which takes 0.

**Now.** Value 0. A seeded arrival's draw-to-draw width comes from the within-pool Dirichlet split (member concentration α = m·A_pool), not from a level shock and not from a band. Called "the owner's decision" in MODEL-LOG §1.198 and registered nowhere until 2026-10-09.

**Why.** Adding the shock changes almost nothing measurable. Item 9's shock variant gave the seeded parties a level-shock sd from the size line fitted to the non-seeded pooled parties: median generic P(≥1 seat) 0.059 → 0.064, median generic q95 0.234% → 0.296%, and the six largest parties' seat means moved by at most 0.46 (item9/FINDINGS.md finding 4, Johannesburg 2026, 5,000 draws). Where the existing width misfits the record it is too wide, not too narrow (findings 1, 2, 5), so Occam, as the owner framed it, keeps zero and adds no source.

**Limits.** The within-pool split's shape is the open question: a spike near zero for small members (finding 1) and a too-wide SACP (finding 5). That is the scheduled within-pool split reformulation, not this entry.

**How to check it.** Re-run item 9's `shock` variant (`audits/2026-10-09-model-fixes/item9/scripts/`) on the current tree and compare P(≥1 seat) and q95 for the seeded parties.


### §A51 · the size the shrink target is evaluated at — the party's current size — ⚖️

**Where.** `levels._shrink_one`, the per-party body of `_shrunk` (the spine's θ and ρ routes) and of `theta_prior`.

**Now.** The size centre (`size_centre`, fitted on the sizes the ratios were measured off) is evaluated at the party's size at the target: its share of the national baseline for θ, its previous local share for ρ. Every party. A party in a record with no current size on that route keeps the reliability-weighted size of its own observations and is counted (`size_fallback` in the shrink report); no level reads such a party.

**Why.** The owner, 2026-10-09: "growth changes by size for sure and you seem to have modelled that. so yes, lets do that for everyone and see what happens" (BRIEF item 11). The size centre says how parties of a given size retain their vote, and the size that governs the forecast is the one the party has now. The previous rule took it at the size the party's own ratios were measured off, which gives a party that has grown the multiplier of the party it used to be (item7/FINDINGS.md: the PA's θ observations at 0.014%–0.29% against a current 2.9%).

**Limits.** This is the evaluation point only. The party's own record keeps its weight `worth/(worth+SHRINK)`, so a party whose own ratios come from another size still carries them (BRIEF item 16 is the separate change that limits them). The spec's spine-level computation for Johannesburg 2026 moved the PA from 6.43% to 6.05% (SPEC §0 O1, `item11_spine.py`); the effect on the draws is pre-registered (SPEC §6 P11, arm C) and not yet measured.

**How to check it.** Arm C against arm B in the batch's measurement (SPEC R2.5). Unit level: `tests/test_theta_prior.py::test_two_parties_with_one_record_and_different_current_sizes_differ` and `::test_the_shrink_target_is_taken_at_the_partys_current_size`.


### §A52 · the size window on a party's own record — `SIZE_WINDOW_GRID` 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, ∞ · `SIZE_WINDOW_MIN_SCORED` 20 · `SIZE_WINDOW_ALPHA` 0.05 one-sided — 🟡

**Where.** `levels.size_window` derives `h`; `levels._in_window` and `_shrink_one` apply it, in `_shrunk` (both spine routes) and `theta_prior`; `montecarlo.run_model` derives one window per route per run and passes the θ window to both estimators.

**Now.** A party's own θ (ρ) observations count only where measured off a national (previous local) share within `h` natural-log units of its current one. Where none survive, its own record is empty on that route: worth 0, centre = the size centre at its current size. `h` is measured, per target and per route, by this rule (written down 2026-10-09, before it was run on the archive):

1. **The walk.** For each LGE target up to the target, the new observations there (its record minus the previous LGE target's) are predicted from each party's record at the previous LGE target by `_shrink_one` at the observation's size, for every grid value of `h`. The new observations of one step are one **cycle**, the cluster.
2. **The score.** At each `h`, the reliability-weighted mean absolute error in `ln r`. `best` is the grid value with the lowest score.
3. **The paired difference.** For each grid value `h ≥ best`, per observation `d_i = |e_i(h)| − |e_i(best)|`; `D` is its reliability-weighted mean and `se` its cluster-robust (CR1) standard error over the `G` cycles, `se² = G/(G−1) · Σ_g (Σ_{i∈g} w_i (d_i − D))² / (Σ w_i)²`.
4. **Measurably worse** means the one-sided lower bound `D − t·se` is above 0, where `t` is the upper 5% quantile of Student's t on `G − 1` degrees of freedom.
5. **The window** is the widest grid value `≥ best` that is not measurably worse.
6. **Underdetermined.** Under 20 scored observations, or fewer than 2 cycles, gives ∞.

What is typed: the grid (natural-log units of size; 1.0 is a factor of about 2.7), the 20, and the level 0.05 with its one-sidedness (a wider window is set aside only for being worse, never for being better). Forced by arithmetic, not judgement: the 2-cycle minimum (a cluster-robust error on one cluster has no degrees of freedom), the CR1 factor and the t quantile (`levels._t_upper`, checked against the published table by `tests/test_spine.py::test_the_t_quantile_is_the_published_one`).

**Why.** The owner, 2026-10-09: "PA fix agree - no growth record we should have size ranges and maintain averages for each" (BRIEF item 16). The PA's θ multipliers were measured during its emergence, off 0.014%–0.29% of the vote, and applied to its 2.9% (item7/FINDINGS.md). The rule applies to every party; the window is derived so it is not a number chosen to remove one party's record. The paired rule replaced a typed tie tolerance (0.005) on the owner's decision of 2026-10-09 (`audits/2026-10-09-model-fixes/reviews/M3-SUMMARY.md`, row 2): the M3 review found the PA's outcome turned on that number, so the tie is settled by measuring the uncertainty of the difference instead.

**Values.** Each run records its windows, the error table, `best`, the paired block and the cycle count in the `20_spine` trace (`size_window`) and its delivery log (`levels.size_window.theta`, `.rho`). The values on the archive at the batch's re-run are in that batch's MODEL-LOG entry. They are not copied here.

**Limits.** Stated before the rule was run.
- **Few cycles make every difference unmeasurable.** At `G = 2` the critical value is t on 1 degree of freedom (about 6.3), so almost no wider window can be measurably worse and the rule returns ∞ or near it wherever only two cycles exist. Cycles grow by one per election, so the window can tighten as the archive lengthens. This is the rule working: with two cycles the archive cannot tell the windows apart.
- **Not monotone.** A wider value that is not measurably worse wins even where a value between it and `best` is measurably worse; the rule as decided is "the widest not measurably worse", and it is applied literally.
- **The cluster is the cycle only.** Observations of one party across metros within a cycle are correlated and sit in the same cluster; a party's observations in different cycles are treated as independent. A party-and-cycle two-way clustering is not done.
- The grid is coarse at the top (3.0 to ∞). The error is in `ln r` of the next observed ratio, which is what the shrunk mean predicts; it is not a score of the forecast.

**How to check it.** Arm C16 against arm C (SPEC R2.5, P16). Unit level: `tests/test_theta_prior.py::test_only_observations_from_a_similar_size_enter_a_partys_own_mean` (G19), `tests/test_spine.py::test_the_size_window_derivation_can_see` (G20), `tests/test_temporal.py::test_the_size_window_reads_no_election_at_or_after_its_target` (G21); `tests/test_stage_estimation.py::spine_the_size_windows_follow_their_own_rule` re-derives each run's choice from its report.


### §A53 · a party with no record of its own takes its size group's average and range — ⚖️

**Where.** Average: `levels._shrunk` returns a party in `current` with no observations on that route at the size centre for its current size (where the size fit exists), so `spine` no longer hands it the flat common mean. Range: `montecarlo.level_shock_sd` gives a party with no measured width, or an item-8 party, `levels.size_sd(base, sd_fit)`: the size-group width at its own baseline share, from the same fit `theta_prior` uses for every party with a baseline.

**Now.** Every party, no exception. Seeded arrivals keep a zero level shock (§A50); item 17 does not reach them. A drawn party with no size and no θ fit stops the run; the typed fallback was deleted (§A29).

**Why.** The owner, 2026-10-09: "no growth record we should have size ranges and maintain averages for each" (BRIEF item 17). The average was already `theta_prior`'s rule for such a party; the spine disagreed (SPEC §0 O2). The range replaces a typed 0.45 with the measured width at the party's size.

**Limits.** The size-group width is the size line of the θ record, fitted against the common centre; for a party far below the record's sizes it is an extrapolation, clamped at `SD_CEILING`. The SPEC's spine-level computation (`item11_spine.py`, Johannesburg 2026) moved MK from 11.31% to 9.93% and small national-only parties up by +0.24 to +0.30 in log (SPEC §0 O2); the draws are the measurement's (arm D, P17).

**How to check it.** Arm D against arm C16 (SPEC R2.5, P17). Unit level: `tests/test_spine.py::test_a_no_record_party_takes_its_size_groups_average_and_range` (G22) and `::test_a_first_local_election_party_gets_the_size_centre_at_its_current_size`.


### §A54 · the group-share tripwire's threshold — record + the largest real one-cycle rise, in more than `GROUP_SHARE_TRIPWIRE_DRAWS` = 0.05 of draws — 🟡

**Where.** `montecarlo.group_share_tripwire` (the count and the 0.05), `src/group_share_record.py` (the record and the margin), `41_guards.group_share_tripwire`.

**Now.** A pair is reported when the party's drawn share of the pool's vote exceeds `record + margin` in more than 5% of draws. `record`: the party's largest Duncan-Davis upper bound in that pool in this city's real results before the target (local elections, and national ones on the preceding local election's wards and composition). `margin`: the largest one-cycle rise of a fitted pool rate by any party in any metro before the target. Typed: the 5%, the choice of the upper bound for the record, and the choice of the fitted-rate rise for the margin. A party with no record in a pool has record 0.

**Why.** The owner, 2026-10-09: "tripwire just tells us but doesnt stop it? if so yes" (BRIEF item 12). The capacity cap cannot see a party taking more of a group than history allows (integrity review F2). Item 7 specified this threshold and measured it: against Johannesburg's real 2021 results it flags 12 of 1,252 outcomes, and on the published 2026 forecast PA/Coloured fires in 69% of draws (item7/FINDINGS.md; those figures are from item 7's probe, not from this code).

**Limits.** It reports and changes nothing; a firing pair is a question for a person. The margin is taken from fitted rates, which are noisy in small pools (the Indian/Asian margin is large), so the tripwire is least sensitive there. At a target with one fitted local election before it there is no cycle and the margin is 0. National-election composition is carried forward from the preceding local election (argued).

**How to check it.** `tests/test_stage_realisation.py::test_the_group_share_tripwire_can_see_and_goes_quiet` and `::test_the_group_share_tripwire_scans_every_member_of_a_real_run` (G14); `tests/test_intermediates_are_current.py::test_the_group_share_record_is_a_fresh_build` and `::test_the_group_share_freshness_check_can_see_a_real_stale_record` (G15). The firing rate per arm is the batch's measurement (SPEC §6 item 12, P16).


### §A55 · the by-election value test — `BYE_CLASS_EDGE` 1% · leave one metro out · 5th percentile of `BYE_VALUE_RESAMPLES` 2,000 · `BYE_VALUE_MIN_PAIRS` 10 — 🟡

**Plain — How much recent by-elections count.** A party's swing in the
by-elections held since the last local election can move its expected share.
How far is measured, not chosen. We checked whether by-election swings before
the 2024 national election predicted that election's result better than the
model did without them, separately for small parties and larger ones. A group of parties gets weight only if
the improvement held when each metro was left out in turn and across resampled
sets of metros; otherwise its by-elections count for nothing. By-elections are
ward contests and the 2024 result was a national and provincial list vote, so
this is the only test the record allows, and a weak one. On
[your forecast](your-forecast/) you can make by-elections count not at all or
fully.

**Where.** `src/bye_value.py` measures; `byelections.size_class` and `byelections.BYE_CLASS_EDGE` define the classes for the test and for the model; `byelections.weighted_deltas`, `byelections.delta_pr` and `levels.trusted_ward_pr` are the deltas and their list-scale conversion, one definition each with the model's.

**Now.** For every (party, metro) pair with a by-election in the metro between the 2021 LGE and 2024-05-29 and a list vote at the 2021 LGE or on the 2024 provincial ballot: the residual `e = actual_2024 − B`, where `B = s_2021 / exp(mu_θ)` is the model's own baseline (its 2021 list share through `levels._shrunk` on the θ record before 2024, at its 2019 national share, with `size_window`'s window), and `δ_pr` is the party's weighted by-election delta in the metro on the list scale. Typed, all fixed in `prereg/2026-10-10-byelection-value-test.md` before the first run:

1. **Two classes**, by the 2021 list share in that metro: under 1% (including none), and 1% or more (`BYE_CLASS_EDGE` = 0.01). Each class has its own weight.
2. **Leave one metro out.** A class's weight for metro `m` is the least-squares slope of `e` on `δ_pr` through the origin over the other seven metros, floored at 0. The gain `G = mean|e| − mean|e − w_(−m)·δ_pr|`, pooled over the class's pairs, in points of share.
3. **The 5th-percentile rule.** 2,000 bootstrap resamples of the metros (the cluster), hold-out by metro identity, seed 20261010; a class is admitted only if the 5th percentile of its `G` is above 0, and then takes the slope fitted on all its pairs. Otherwise its weight is 0.
4. **The 10-pair floor.** A class with fewer than 10 pairs takes 0, "not measurable".
5. **`TAU_MONTHS`** = 18, the recency half-life `byelections.py` has always used (plan §3.5), now one named constant for the delta file and the test.

**Why.** The owner, 2026-10-09: "by elections we need to use history as the judge of whether they predicted anything not already predicted by model... lets see" (BRIEF decision 19). This replaces item 14's minimum (SPEC R2.4). The weight is the measured increment out of sample, against the model's own baseline; if none is measurable it is zero. Every party, the same rule.

**Values.** The test's output, both classes' slopes, gains, intervals, pair counts and verdicts, and every pair, is `data/processed/bye_value.json` (`artefact_key`: `byelections.bye_value_key`). The values at the batch's run are in that batch's MODEL-LOG entry. They are not copied here.

**Limits.** Stated where the test's result is quoted.
- **Cross-ballot, on the whole record.** By-elections are local ward contests from 2022-02; the only real result after them is the 2024 provincial ballot, a national-provincial list ballot. A weight measured against that ballot is applied to a local list ballot.
- **At most eight clusters.** The bootstrap resamples the metros that hold a pair, so the interval is coarse.
- **The test and the model weigh δ differently.** The test's augmented prediction is `B + w·δ_pr`. The model's centre is `(1 − w)·level + w·clamp(prior_pr + δ_pr)`, so `w` also pulls the centre toward the previous list share and the clamp bounds it. The test measures the delta's increment, not the whole blend. Argued, not tested.
- **No admission gate in the test.** `BYE_MIN_WEIGHT` gates the model's use of a party's evidence; the test scores every pair (each pair's weight sum is in the artefact).
- **A label that is not a party.** Independent candidates canonicalise to one label; where the 2024 provincial ballot carried independents, that label has a list vote and enters the population. The pre-registration said it would fall out; it did not, and the population stays as registered. Its effect with the label removed is MODEL-LOG §1.295 (the verdict does not move).
- **`B` is a stand-in for the 2026 spine.** It is the 2021 list share through the θ record at the 2019 national share. Its residuals carry a party-signed bias (one party's `e` positive in every metro where it is in the population, another's negative in every one, MODEL-LOG §1.295), which the slope reads as by-election signal or noise alike.
- **One pair dominates the 1%-or-more class**: eThekwini's largest party at the 2021 LGE, whose 2024 loss to a new party is far larger than any other residual and opposite in sign to its by-election delta. MODEL-LOG §1.295 gives the class without it; the verdict does not move.
- **The recorded weight is the class weight, not always the weight used.** `scenario["_bye_weight"]` (and the trace's `bye_weight`) records the class weight for a party that `BYE_MIN_WEIGHT` then gates out, and the class weight `w` rather than the derived `w_used` under `bye_weight_mode = "inverse_variance"`. Invisible while both class weights are 0.

**In the model (2026-10-10).** `montecarlo.blended_centres` gives each party with by-election evidence the weight of its class (`montecarlo.bye_weight`), read at `montecarlo.bye_class_size`: its previous-LGE list share, or with none its share in the run's baseline (the national election before the target; a seeded arrival's seed). `run_model` reads the file once through `montecarlo.read_bye_value` wherever the target reads by-elections and `w_bye` is `None`, and refuses a missing file or an `artefact_key` other than the live `byelections.bye_value_key`. A city file may not set `w_bye`: it is in `montecarlo.DERIVED_NOT_CITY`, and `apply_city` refuses a city whose `[judgements.scalars]` sets it. `BYE_MIN_WEIGHT` still gates admission (§F33). A class weight of 0 switches the party's by-election term off, `bye_weight_mode` included. The weight each party was given is in the `30_centres` trace (`bye_weight`) and `export_draws` reports it beside `reaches_model`. Supersedes §A35.

**How to check it.** `tests/test_blended_centres.py::test_each_class_takes_its_own_weight_from_the_file`, `::test_no_city_file_sets_a_derived_lever_and_apply_city_refuses_one`, `::test_a_missing_or_stale_bye_value_file_refuses`, `::test_an_override_needs_no_file_and_is_recorded`, `::test_the_class_edge_is_the_one_constant_both_sides_use` (G24); `tests/test_export_draws.py::test_the_reported_bye_weight_is_the_one_blended_centres_applied` (G26); `tests/test_bye_value.py` (G23: an exact half increment is admitted at 0.5; an independent residual earns 0; nine pairs are not measurable; the hold-out by identity; the bootstrap resamples metros, not pairs; the slope; the edge); `tests/test_temporal.py::test_the_byelection_value_test_reads_no_byelection_or_result_from_its_outcome_on` (G25); `tests/test_intermediates_are_current.py::test_the_bye_value_record_is_a_fresh_build` and `::test_the_bye_value_freshness_check_can_see_a_real_stale_record`; `tests/test_bye_value.py::test_the_key_covers_the_raw_election_files_and_the_city_files` (one byte in a raw election file or a city file makes `read_bye_value` refuse).


### §A56 · the keyed draw streams' numerical constants — `GAMMA_SLOTS` = 4 · `STREAM_CHUNK` = 256 — 🟢

**Where.** `montecarlo.DrawStreams` (both), `montecarlo.log_gamma_slots` (the slots).

**Now.** Every random quantity in a run reads its own stream, keyed by the run identity (`seats.lot_identity`), the stage and the entity, through `seats.stable_entropy`. A gamma (the Student-t's chi-square half under `level.chi`, a Dirichlet component under `split`) is Marsaglia-Tsang on shape + 1 with the boost U^(1/shape) at every shape, from `GAMMA_SLOTS` fixed (normal, uniform) trials per draw; the first accepted trial is the value. A draw whose every trial rejects takes an exact fallback from a generator keyed by the stream and the draw, and is counted in `41_guards.gamma_fallbacks` out of `gamma_draws`. `STREAM_CHUNK` is how many draws of a stream are generated at once.

**Why.** Owner decision 1 of 2026-10-11 (paired draws across arms; `audits/2026-10-11-model-round/PLAN.md`), design `step1/1c-paired-draws-design.md` as fixed by `step2/2-review-1c.md`.

**Neither moves a distribution.** Rejection sampling on iid trials is exact and the fallback is any independent exact sampler, so `GAMMA_SLOTS` changes only how often the fallback runs; a fallback value is the one value in a run that is not paired across arms. `STREAM_CHUNK` changes no drawn value: a stream's row `d` is row `d` of one sequential fill.

**How to check it.** `tests/test_draw_streams.py`: the slot gamma at four slots and at one against numpy, the fallback alone, the power rows (V1); `::test_the_chunk_size_changes_no_drawn_number_in_a_real_run` and `::test_chunk_size_changes_no_row_and_reads_are_forward_only` (V2).


### §A57 · the universal draw (design 1j v4-L1) — 🟡

**Where.** `montecarlo.make_drawer` (the draw, the calibration pass, the composition subtraction), `montecarlo.party_width`, `width_sigma`, `width_location`, `width_rho`, `pool_spec_centres`, `mean_conservation`; `src/width_record.py` (the record); scenario key `draw_law`.

**Now.** Each drawn party gets one latent log level `x = √ρ(s)·σ(s)·z + ω·ε`, `ω² = σ(s)²(1 − ρ(s)) + δ²·new − v_comp`, floored at 0 with the excess in `41_guards.width_floored`; shares are `c·exp(κ + x)` normalised, with `c` the party's `pool_spec` centre and κ set by a calibration pass so the mean drawn share is `c`. The within-pool split is the post-IPF centre (no Dirichlet, no mean floor). `σ(s) = a + (b − a)/(1 + exp(k(log s − log s_mid)))` and the newness δ are fitted jointly with a location `m(s) = c1·L + c2·L²`, `L = min(log(s/20%), 0)`, by weighted ML, one unit per party-cycle, on the backtests before the target. The location is NOT in the draw (option L1). The judgement calls, each the design's:

| # (v4 and v3 addenda) | call | value | evidence | how checked |
|---|---|---|---|---|
| 32 | one width curve over all sizes | logistic in log size, joint ML, offset-aware | owner direction 2026-10-12; v4 §1 | band roots printed as diagnostics (`DIAGNOSTIC_BANDS`, `DIAGNOSTIC_MIN_EFF` = 8) |
| 33 | level error | L1: fitted and not in the draw; `m(s)` recorded for the centre-correction arm | v4 addendum §1, §3: L2 and L2′ fail the large-party rule | prereg arm UC |
| 34, 37 | newness | one δ for every party new to the city (no result at the previous local election here) | v4 §1.4; addendum §2: no size-dependent term is supported or rejected | MK's width is disclosed; the §SJ overlay is reported with and without |
| 36 | `LOCATION_CLAMP` | `m(s)` at no less than 0.016%, the record's 1st-percentile centre | review 2-review-1j-v4 §1 | — |
| 9 | `WIDTH_BLOCK` | the residual reference block: centre ≥ 20%; `m(s)` is 0 from here up | v1 §1.1 | — |
| 11 | shared loading | ρ measured for established parties under 1% (`RHO_GROUP_EDGE`) and 1-20% by one-way city-year decomposition about zero; applied at `RHO_ANCHOR_LO` = 0.548% and `RHO_ANCHOR_HI` = 2.24%, linear in log size between, 0 at 20% | v2 §3.1 | the 1-20% shared share is a pre-registered measured quantity |
| 15 | location fixed point | `FIXED_POINT_ITERS` = 2, stop when no width at `FIXED_POINT_SIZES` moves by `FIXED_POINT_TOL` = 0.01; `FIXED_POINT_DRAWS` = 2,000 per earlier city-year | v2 §2.3 | `width_record.json` carries the iterations |
| 16 | turnout composition | subtracted from each party's own variance, measured on the run's own turnout draws (the calibration streams), floored, excess recorded | v1 §2.5, v2 N1 | `41_guards.width_floored`; `test_universal_draw` |
| 17 | mean-conservation falsifier | per party with centre ≥ `FALSIFIER_MIN_CENTRE` (0.1%), z on the run's own and the calibration's standard errors, Bonferroni at `FALSIFIER_FAMILY_ERROR` = 0.01; it reports | v2 §1.2 | `test_universal_draw::test_the_falsifier_is_quiet_on_clean_runs_and_sees_a_twenty_percent_error` (prereg M2) |
| 18 | `N_CAL`, `KAPPA_TOL`, `KAPPA_MAX_ITER` | 4,000 · 1e-3 relative · 30 | numerical: they change the precision of the mean, not the law | `41_guards.kappa_error` |
| 20 | `MIN_ESTABLISHED` | a target's record needs 20 established party-elections, or the writer refuses | v1 §2.6 | `test_universal_draw::test_the_fit_refuses_a_record_too_thin_to_fit` |
| 21 | 2011 width | the 1b v3 fallback: RMS of the forward θ residual at target 2006 (`theta_residual.residuals`), with and without θ history; no shared or newness term; UNTESTABLE | no earlier backtest | the record labels it `untestable`; 2011 enters no rule (prereg §2) |
| 22 | no pool-concentration covariate | — | real (1f §2.3); deferred; it would narrow the PA | — |
| 23 | no extra width for a second local election | — | v1 §7 | — |
| — | the incumbent law kept selectable | `draw_law` = "incumbent": the Student-t level shock and the Dirichlet split on the keyed streams | prereg §3.2 (arm I) | `test_levers_are_live` CONDITIONAL entries |
| — | the small-party centre correction (arm UC) | `centre_correction`, off by default: every party with `pool_spec` centre below `WIDTH_BLOCK` multiplied by exp(m(s)), m this target's record location (earlier cycles only), s clamped at `LOCATION_CLAMP`, renormalised before the calibration pass; widths stay at the uncorrected centre | prereg §3.3; owner checkpoint 2026-10-12. The width-at-uncorrected-centre choice is this writer's reading of "draw law as U" | `test_universal_draw::test_the_centre_correction_is_the_records_location_below_the_block` |

**Values.** The fitted curve, δ, location, ρ, the fixed point and the band diagnostics per target are in `data/processed/width_record.json` (`artefact_key`: `montecarlo.width_record_key`). The values at the round's re-emit are in that round's MODEL-LOG entry. They are not copied here.

**Limits.** The 2011 width is untestable and too narrow by construction (v1 §2.6). The record's centres are today's code's, whose `level_shrink` was chosen on Johannesburg 2016 and the 2021 panel (v1 §2.2, 2-recheck-1b-v2 N6). Composition is subtracted per party, which keeps marginal widths and not the covariance between members of one pool (v2 §2.5, argued). The individual path joins the same latent vector and is reached by no party today.

**How to check it.** `tests/test_universal_draw.py` (curves, one party's width, the fit recovering simulated parameters, the shared share found where it was put, the block frame, calibration conservation and its records, alpha unread, the own-term budget, the falsifier, judgements, the record's refusals); `tests/test_stage_realisation.py::faults_in_widths`; `tests/test_draw_streams.py::test_the_universal_law_pairs_the_same_arms`.

## SJ. Strength judgements (design 1j v3 §11)

A strength judgement states one party's centre and how uncertain the judgement is, for a party the record cannot size (no record, or a collapse). It is entered in the target's `judgements/<city>-<year>.toml` under `[party.<CODE>]`:

* `support` (a list share; it replaces the model's centre) and/or `overperform` (a multiplier on `support`, or on the model's centre); the judged centre is `c_J = (support or the model's centre share) × overperform`;
* `sigma_j` (required with either): a log sd, the judgement's uncertainty BEYOND the model's own centre error for an established party of the judged size. `sigma_j = 0` states a judgement as reliable as the model's own centre. It REPLACES the newness term, never adds to it;
* `register`: the row of this section that declares it.

Read at run time (`montecarlo.strength_judgements`) and excluded from the pool spec's hash; the forecast declares the hash of the entries it applied (`judgements_applied_sha`). A backtest ignores every entry and records it in `35_widths.judgements_ignored`. A forecast with judgements is also run with `apply_judgements` off, and both are reported.

Each row: `§SJ<n>` · party · target · `support` / `overperform` / `sigma_j` · the reason · the evidence the record cannot supply · the date the judgement was made · how to check it after the election.

| row | party | target | entry | reason | evidence | date | check |
|---|---|---|---|---|---|---|---|

*(No strength judgement is entered. `tests/test_universal_draw.py::test_every_strength_entry_has_a_register_row_and_every_row_an_entry` checks both directions.)*

## B. Measured, but the form or the selection was chosen

The number came from data. The *shape* it was fitted in, or the criterion that
picked it, did not.

### §A58 · the arm runner's constants — `BACKTEST_DRAWS` 1,000 · `FORECAST_DRAWS` 5,000 · `LARGE_MIN` 15% · `MIDDLE_MIN` 5% · `CLUSTER_LEVEL` 0.90 · `R2_MIN_MEDIAN` 0.98 · `MC_RESAMPLES` 200 · `MC_SEED` — ⚖️ typed (2026-10-12)

**Where.** `src/arms.py` (the runner and comparison of the 2026-10-11 round's pre-registered arms). `ARMS` is the arms' scenario overrides, the prereg §3 table as code (I: `draw_law` incumbent; U and C0: none; UC: `centre_correction` on; US: `level_shrink` 0).

**Now.** The draw counts, the size classes (by the classifying arm's `pool_spec` centre), the 90% cluster-bootstrap level and R2's bar on the median per-draw correlation are the pre-registration's (`prereg/2026-10-12-universal-draw.md` §3, §4, §6.3), copied as code so the runner applies them; the prereg is where they were set. `MC_RESAMPLES` (draw-index resamples behind each paired Monte Carlo error) and `MC_SEED` are numerical: they set the precision of an error estimate, not the error.

**Why.** Typed. The prereg fixes the first six; the resample count is this writer's, sized so the error of a standard deviation from 200 resamples is about 5% of it.

**How to check it.** `tests/test_arms.py` (identical arms give zero difference and zero Monte Carlo error; a shifted arm stays paired above `R2_MIN_MEDIAN`; an independent one does not).

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

**Plain — Turnout moves together across population groups.** In each simulation,
turnout in the four population groups rises and falls together, to one degree
for every pair: the average of how closely each pair's turnout moved between
past local elections in the metros. Black African, Coloured and White turnout
have moved closely together, and Indian/Asian turnout much less. Separate
figures for each pair have not been tried. Removing the link was tested and
changed the forecast's spread very little, and why it matters so little is not
yet explained. It cannot be changed on [your forecast](your-forecast/).

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

**Since 2026-10-12 read only under `draw_law = "incumbent"`** (§A57): the shipped universal draw has no within-pool Dirichlet, and `alpha` and `dirichlet_scale` reach no run of it. The spec field is still emitted; deleting `pools.dirichlet_alpha` is a `pools.py` code change and is queued (POOLS-REEMIT-QUEUE.md).

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

**Now.** **AMENDED 2026-09-24 (register audit).** One definition: `SAFE` lives in `render_map.py` and `hex_cartogram.py` imports it. The STRONG and LEAN tiers were removed by the owner on 2026-09-17 and exist nowhere in `src/`. Not an independent judgement.

**Record.** The four confidence tiers. **These are NOT free here** — they are `render_map.main`'s, re-declared because they are inline in that function and cannot be imported, and `test_the_two_maps_agree_on_the_confidence_tiers` reads `render_map.py`'s source and fails if the two drift apart. The tiers themselves are a presentation call made in the 2026-08-06 user review; this row exists so that the copy is not mistaken for an independent judgement.

### §D20 · `TIP_FLOOR` = 0.05 · `OTHER_FLOOR` = 0.005 — 🟢

**Where.** `hex_cartogram.py`

**Now.** **AMENDED 2026-09-24 (register audit).** One definition in `render_map.py`, imported by `hex_cartogram.py`; 0.05 and 0.005, unchanged.

**Record.** A party is named in a ward's tooltip at ≥5% of simulations, and the swept-up "other" remainder is shown at ≥0.5%. Same provenance and same drift guard as the tier thresholds above: typed in `render_map.main`, re-declared here, checked against that source.

### §D21 · `MAX_DISPLACEMENT_RADII` = 5.0 — 🟡

**Where.** `tests/test_hex_cartogram.py`

**Now.** Typed at 5.0 radii — a regression guard rather than a claim, and it separates the optimal assignment (3.8) from the greedy one (8.8).

**Record.** The bound at which a cartogram has stopped being a map: no hexagon may sit further than five hex radii from its ward's true centroid. In radii rather than pixels so it does not move with the figure's size. Johannesburg's worst ward is at 3.8 under the optimal assignment and **8.8 under the greedy one**, so the bound separates the two — which is what it is for. Typed, and a regression guard rather than a claim.

### §D23 · `WALL_FLIPS` = 30 — ⚖️ argued, and it names a scenario rather than measuring one

**Where.** `render_sheet.py`

**Now.** Typed at 30, and registered on 2026-09-25 when the guard caught it as a
new tunable constant. **It moves no forecast** — no draw, share or seat reads
it. It selects which of the DA-majority simulations the "since then" box calls
*breaking the ANC's ward wall*, and the page prints the same figure beside the
count as the token `claim.da_alone.wall_flips`.

**Record.** How many ANC wards a DA-majority simulation has to take before the
narrative treats it as the wall breaking rather than an odd draw. There is no
quantity in the world this estimates: a ward wall has no threshold, and the only
question the figure answers is which simulations a sentence is allowed to
describe. So it is **argued, not measured**, and the honest defence is that it
is well inside the gap between the two kinds of draw the box distinguishes — the
wall-breaking route and the rivals-collapse route.

⛔ **IT WAS A SECOND COPY UNTIL 2026-09-25, WHICH IS WHY IT IS HERE.**
`content/joburg/claims.toml` said *"take at least 30 of the ANC's usual wards"*
while `render_sheet` selected those simulations with a literal `>= 30`. Two
copies of one threshold, a sentence and a filter, either of which could be
edited alone — after which the box would have described a different scenario
from the number standing next to it, with nothing red. Naming the constant is
what exposed it to this register's guard; the typed figure had been invisible to
it for as long as it sat in prose.

### §D22 · `min_clusters` — 8 — 🔴

**Where.** `score.chi2_clustered`

**Now.** Typed at 8: the number of clusters below which the clustered uniformity test refuses to estimate a design effect and returns `estimable: False` with a `not established` verdict instead of a χ². **It moves no forecast** — no draw, share or seat reads it, and it is not one of `ITERATING.md`'s four keys — but it decides whether this repository's calibration verdict at a given cluster level is a number or a refusal, and the committed `data/processed/history.md` prints both the verdict and the value of this constant in words.

**Record.**

1. **Registered 2026-09-13, number-neutral.** It was a bare `if k < 8` in the function body, a shape the 2026-08-23 widening cannot see — that scan reads default arguments, module constants, dataclass fields, `DEFAULTS` and TOML, not in-body literals. Hoisting it to a default argument is what made it visible to `test_every_tunable_constant_is_in_the_judgement_register`, and the guard caught it immediately. The value is unchanged, so no reported figure moves.

2. **8 is a round number.** Nothing in `src/`, `MODEL-LOG.md` or `MACHINERY.md` derives it. The function's own argument — *"three clusters cannot estimate ten cell design effects"* — argues for **a** floor and not for **this** floor. It is not the survey literature's number either: the usual rules of thumb for cluster-robust inference are 30–50 clusters, which would refuse this panel's own k=24 as well. It coincides with the eight metros of `levels.METRO_CODES`, so clustering by **city** is admitted at exactly the boundary while clustering by **cycle** (k=3) is refused; no record says that was the reason and none is claimed here.

3. **What a floor buys, measured — a fact about the ESTIMATOR under a known null, not a fit to any model output.** Panel shape held at the real one (n≈528 columns split k ways, R=8 re-randomisations, independent uniform PIT, so the true design effect is 1; 200 replicates for the δ̄ rows, 400 for the cell row):

   | k | 3 | 4 | 6 | 8 | 12 | 24 |
   |---|---|---|---|---|---|---|
   | mean δ̄ | 1.005 | 0.993 | 1.003 | 1.002 | 0.997 | 0.998 |
   | rse(δ̄) | 12.1% | 10.2% | 7.5% | 6.0% | 4.8% | 3.1% |
   | p95 of the largest cell δ | 2.16 | 1.91 | 1.70 | 1.58 | 1.45 | 1.31 |

   δ̄ is unbiased at every k and its noise is **smooth in k**. There is no cliff at 8 or anywhere else, so any floor is a line drawn on a continuum and 6 and 12 are as defensible as 8. That is what keeps this 🔴.

4. ⚠️ **Whether the k=3 figures the docstring cites as its reason are estimator noise is NOT ESTABLISHED, and it turns on a quantity nobody has measured.** Same null hardened to the panel's own shape — k=3, unequal clusters, a non-uniform pooled PIT rising 8.0% → 12.4% across the deciles (which the δ formula scores against a flat `p0` and cannot subtract off), columns independent, 1500 replicates a row — the answer depends entirely on how much the R re-randomisations average away:

   | independent replicates | mean largest cell δ | p99 | max seen | P(≥ 5.08) |
   |---|---|---|---|---|
   | R = 1 | 2.91 | 7.24 | 11.10 | 6.4% |
   | R = 2 | 2.29 | 4.61 | 6.03 | 0.5% |
   | R = 8 | 1.59 | 2.45 | 2.99 | 0.0% |

   The observed 5.08 and 10.65 are ordinary noise under R=1 and impossible under R=8. The run uses R=64, but those replicates re-randomise **the same columns** inside their jump intervals, so they are positively correlated and the effective count is somewhere between 1 and 64 — **and it has never been computed.** Until it is, *"a number about the estimator, not about the panel"* is a conjecture, not a measurement; so is its negation.

5. **The justification that survives either way, and it does not pick 8.** With δ̄ estimated on k−1 degrees of freedom, reading χ²/δ̄ against a fixed χ²(9) critical value treats an estimated quantity as known, which is anti-conservative and worsens as k falls. That argues for an F-type reference (Rao–Scott / Thomas) rather than a bright-line refusal, and it has not been built.

**How to check.** Both nulls need `src/score.py` and numpy only — no data, no model run, no pools. Draw k clusters of independent PIT values, call `chi2_clustered(..., min_clusters=2)`, and read `deff` and `deff_cells`. The effective-R question needs the committed artefact's stored jump intervals.

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

**Since 2026-10-12 read only under `draw_law = "incumbent"`** (§A57); the shipped universal draw does not read it.

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

**Since 2026-10-12 read only under `draw_law = "incumbent"`** (§A57); the shipped universal draw does not read it.

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

### §F32 · ~~`ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI`~~ — ~~0.25, 0.95~~ — ⚫ deleted

**Now.** DELETED 2026-10-09 (model correction batch, item 9). The band these percentiles set was emitted into every spec as `seed_bands` and never drawn from: `make_drawer` skips every pool member before the lookup and every seeded arrival is a pool member, and `blended_centres` read only the band's middle, 1.0 by construction (MODEL-LOG §1.198; item9/FINDINGS.md finding 5 and Q5). The band, its emission, its notes and these two constants are gone; a seeded arrival's width is the within-pool split (§A50). The record below is kept as written.

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

**Note, 2026-10-09 (model correction batch, item 6).** The slate-change multiplier on the ratio (`montecarlo.slate_change_ratio`, `ratio × now / was`, now vote-weighted) is capped at `WARD_PR_RATIO_MAX`; it carried a second literal `[0, 2.0]` clip until then. It is not floored at `WARD_PR_RATIO_MIN`, which is a floor on the measured ratio: a party fielding no ward candidate keeps 0 (SPEC O3). `levels.projected_contestation` now projects vote-weighted slates (a partial declaration, or no target lists), and its `contestation_expand` was fitted on count fractions; the projection has not been re-fitted on vote-weighted values. Inert at Johannesburg 2026, whose declaration is complete (M2 review N2).

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
| `SD_FLOOR` | 0.15 | **[0.11, 0.30]** — *but see the caveat* | Forward-validated conditional sd(log θ) at ≥15% of the vote, cluster-bootstrapped on metro-year. §1.59 measured **0.138 [0.084, 0.171]** (n=37) on the old record. **[16-panel]** §1.77 re-measured **0.273 [0.136, 0.386]** (n=64) on sixteen city-years and the tree restored per §1.75. 0.15 is inside both. **§1.71's quoted 0.208 [0.114, 0.299] at n=370 DOES NOT REPRODUCE** — the residual count is 403 on the restored tree, with or without the Type A filter, while §1.71's own ≥15% binding count (26 of 64) matches today's exactly. It was measured against a tree state that cannot now be reconstructed, which is what §1.75 found had happened to `data/raw/elections/`. Quote §1.77's figures, not §1.71's** |
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
| `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` | ~~0.25, 0.95~~ | Deleted 2026-10-09 (§F32): the band they set was never drawn from |
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

**Plain — The excessive-seats clause.** The clause is applied as amended in
2021, with the arithmetic the Commission used in Laingsburg in 2021 (see *How
Johannesburg's council elections work*). No court has ruled on it. [Your forecast](your-forecast/) applies three versions of Germany's seat law instead; two of
them enlarge the council and move the majority line.

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

**Plain — Expected turnout leans on 2021.** Each voting district's turnout is
projected from how far turnout fell from the national election to the local
election two years later, in 2016 and in 2021, with 2021 counting for 70%. The
weight comes from the model's original plan and has never been tested. Turnout
fell less in 2016, so weighting the two equally would raise projected turnout.
On [your forecast](your-forecast/) you can move the turnout of any or all four
population groups at once. A group you leave alone stays at the forecast's
turnout.

**Where.** `turnout.py --w-recency`

**Now.** 0.70, verbatim from the original plan. It reaches the model through 20 committed `turnout.csv` files that carry no artefact key, so changing it does nothing until someone re-runs the script.

**Record.** Weight on the 2021 vs 2016 turnout drop-off. **Verbatim from the original plan §3.5**, whose own text asks for a fold-2 sensitivity test that `MODEL-LOG` never records. Reaches the model through 20 committed `turnout.csv` files that carry **no artefact key**, so changing it does nothing until someone re-runs the script and nothing announces the mismatch

**Direction of the alternative (read 2026-10-02, no model run).** In Johannesburg's
turnout.csv the median drop-off ratio over voting districts is 0.773 for 2016
(774 districts) and 0.625 for 2021 (817): turnout fell less from 2014 to 2016
than from 2019 to 2021, in 712 of the 766 districts that have both. A weight
below 0.70 therefore raises projected turnout. The sensitivity test the plan
asks for is still unrun; this gives the sign only.

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

**Now.** **AMENDED 2026-09-24 (register audit).** Only Johannesburg carries `[judgements.plan_bounds]` (Tshwane's were deleted 2026-08-31), and the clamp needs a by-election file, which exists only for Johannesburg 2026 — so it reads on none of the 24 panel rows and the panel is not a mixture of configurations. Whether it binds at 2026 is unmeasured.

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

**Now.** **AMENDED 2026-09-24 (register audit).** 0.6. Two other copies in `pools.py`, neither a live fallback: the `Config` dataclass default (marked unreachable — `load_config` refuses a TOML without the key) and `projected_pool_shares`' default argument.

**Record.** Damping on ward composition extrapolated past Census 2022 — four years for the 2026 forecast. Typed three more times as a fallback in `pools.py`

### §H9 · `extrapolation_max_years` / `max_extrapolation` — 8 / 8.0 — 🔴

**Where.** `dimensions.toml`, `pools.Config`

**Now.** 8 / 8.0 — two copies of one number, one in TOML and one as a dataclass field.

**Record.** How far past the census the projection may reach. **Two copies of one number**, one in TOML and one as a dataclass field

### §H10 · `total_seats` — 270 — 🔴

**Where.** `seats.allocate`

**Now.** **AMENDED 2026-09-24 (register audit).** Johannesburg's 270 as a DEFAULT ARGUMENT in the shared allocator. This row said every remaining call passes it explicitly; it was wrong. Both `allocate` calls in `fold.py` omit it, so `fold.py`'s printed seat diagnostic allocates 270 seats whatever the city. They feed that printout only, not the γ parameters the forecast reads, so no forecast number is affected.

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

**Now.** LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 1.5pp, declared and sourced from outside this repository; never divided by the number of houses, which is the defect it exists to fix.

**Record.** Finland 1.25pp; The Economist's production code 1.30pp; Selb et al., *POQ* 87(4) 2023, 5,240 German polls, 1.5pp mean absolute bias; South Africa 2024, 1.66pp

### §H18 · `SIGMA_IDIO` — 1.5pp — 🔴 declared, sourced

**Where.** The house-specific part. The **only** term `h_eff` may divide.

**Now.** LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 1.5pp, declared and sourced; the ONLY term `h_eff` may divide.

**Record.** Stoetzer prior N(0,1); Bon et al. ≈1.0; Jackman phone-only 1–3; SA 2024 1.71pp

### §H19 · `SIGMA_DRIFT_PER_ROOT_DAY` — 0.30 pp/√day — 🔴 declared, sourced

**Where.** Opinion movement between fieldwork and polling day.

**Now.** LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 0.30 pp/√day, declared and sourced; the shipped `POLL_DRIFT_PP_PER_ROOT_DAY` of 0.10 is 2–4× too small.

**Record.** Band 0.20 (Ellis, NZ — *estimated* in a state-space model) to 0.41 (derived from Jennings & Wlezien's 4 / 3 / <2pp horizon profile). The shipped `POLL_DRIFT_PP_PER_ROOT_DAY = 0.10` is 2–4× too small

### §H20 · `SIGMA_VOLATILITY` — 0.8pp — 🔴 declared, sourced

**Where.** A South Africa adjustment: +0.1pp per 1pp of average party swing.

**Now.** LIVE since 2026-08-24 in the poll path, which is OFF at 2026 (§A8), so the published forecast does not reach it (AMENDED 2026-09-24 (register audit)). 0.8pp, declared and sourced — a South Africa adjustment for average party swing.

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

### §L2 · The declaration sets the LEVEL; the record sets the WIDTH — ⚪

**Since 2026-10-12 the emit reads no strength key** (POOLS-REEMIT-QUEUE entry 34): a judged size and its width are applied at run time under §SJ, on a forecast only, and a party carrying `support` is sized at emit like any arrival and stays in the group budget.

⚪ **RETIRED 2026-10-09 (model correction batch, item 9).** The width half was
false: the arrival band this entry describes was never drawn from, so the pool
Dirichlet set the width whatever the band said. The SACP, declared at a level,
drew a 90% log width of 7.15 against its band's 3.46 (item9/FINDINGS.md finding
5). The band is deleted (§F32). The level half stands in the code: a declared
`support` or `overperform` sets the seed, and a judged size sits outside the
group budget (§1.178). A seeded arrival's width is the within-pool split
(§A50). The entry below is kept as written.

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

### §L9 · `REGISTRATION_MAX` — 2.0 — ⚫ deleted 2026-10-12, SUPERSEDED by §L15

**Deleted 2026-10-12** (model round step 5; design `audits/2026-10-11-model-round/step1/1g-census-composition-design.md`). Registration is now fitted with no upper bound; a pool the ward table cannot identify is held at the city's rate (§L15). The bound was the one place a group's census LEVEL reached the registered split (1g §0). The text below describes it as it stood.

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

### §L12 · Two party names in the pasted roster are SUBSTITUTED on judgement, not on evidence — 🔴 typed, and it decides whether a party keeps its baseline

**Where.** `judgements/joburg-2026.toml`, the `[roster] parties` list. No symbol
in `src/` — the substitution is a hand edit to a hand-written list, which is why
it is registered here rather than discoverable by grep.

**Now.** Four names in the IEC's certified 2026 list canonicalise to a different
code from the file the party's baseline comes from. **Two are certain and are not
judgement calls at all** — `UMKHONTO WESIZWE PARTY` is MK and `VRYHEIDSFRONT
PLUS | FREEDOM FRONT PLUS` is the VF Plus: same registered party, a suffix and a
bilingual form. **Two are judgement and are the subject of this entry:**

| written in the roster | instead of the IEC's string | the difference |
|---|---|---|
| `THE ORGANIC HUMANITY MOVEMENT` | `ORGANIC HUMANITY MOVEMENT` | a definite article |
| `CHANGE` | `CHANGE PARTY` | a trailing "PARTY" |

**Why it is a judgement.** Nothing in the record proves either identity. The IEC
publishes no party ID (`DATA-QUALITY.md` item 17), so the only evidence available
is the name itself, and a name is exactly what a renaming changes. Both readings
are plausible and neither is derivable: `CHANGE PARTY` may be the `CHANGE` that
contested in 2021, or a different registration reusing a common word — and the
archive scan in §1.242 independently found `CHANGE ← AFRICAN DEMOCRATIC CHANGE`
at 2019→2021 in two metros, which makes this party's naming history *actively*
unstable rather than merely ambiguous.

**What it costs if wrong, and the asymmetry.** Substituting wrongly hands a new
party an incumbent's baseline. NOT substituting when it was the same party sends
an incumbent through the arrival path instead, and additionally — under
`complete = true` — deletes the real one from the pools. The second error is the
larger of the two and is the one the code warns about at
`pools.resolve_roster`'s refusal. Both are small here: the two parties together
hold well under a tenth of a percent of the 2021 PR vote.

**How to check it.** Against the IEC's **party register** (registration numbers,
not the candidate list), which is the only source that can settle identity. Until
that is done these two stay in this register as typed. ⛔ **Do not resolve them
with a `[party.X]` table**: that declares the name a NEW party, sizing it from
the arrival record while `complete = true` deletes the incumbent — the ActionSA
failure with the sign reversed.

**Record.** Raised 2026-09-16 when the certified list was parsed; the owner's
instruction was that uncertain names be registered as judgement calls unless they
can be certified automatically, and nothing available certifies these. §1.242.

### §L13 · The SACP's first general ballot is sized by hand from its by-elections — ⚪ RETIRED 2026-10-09

⚪ **RETIRED 2026-10-09 (model correction batch, BRIEF items 13 and 18).** The
owner: "it's a strange case. it's usually in the alliance so strange it is
running alone, but only in some wards I think. Narrow it and treat like
everyone else until we have a mechanism to change that has some basis", and on
the specification, "SACP normal. Is it treated as a split or new entrant? ...
But leave it as a normal new party". The
`weights` and `support` lines are deleted from
`[party.SOUTH_AFRICAN_COMMUNIST_PARTY]`, so `arrival_rules` sizes it as a
generic entrant (reach-matched comparators, the even pool spread, zero level
shock, the pool split), the route this entry measured at about 0.06% (item (b)
below). Its alliance status is a comment in the judgement file, not a
mechanism; the owner's note that it stands "only in some wards" disagrees with
the declared slate, which lists it in every ward (SPEC §0 O8), and is noted,
not changed. The effect on the forecast is pre-registered (SPEC §6 P13) and
measured in the batch's window; the MODEL-LOG entry is the batch's (step 13).
The entry below is kept as written.

(Its reader-facing Plain field was removed on retirement: a retired call is not
shown to a reader as a live choice, `judgement_sheet.plain_calls`.)

**Where.** `judgements/joburg-2026.toml`, `[party.SOUTH_AFRICAN_COMMUNIST_PARTY]`:
`weights` and `support`. No symbol in `src/`.

**Now.** `support = 0.0131` of the city, drawn from the voter profile
`weights = [0.8804, 0.0106, 0.0084, 0.1006]` (categories order).

**Why it is a judgement.** The SACP is in the ANC-led alliance and has stood
through ANC lists; 2026 is its first general ballot under its own name. The
archive holds it only in `data/raw/byelections/byelections_SA_vd_party.csv` —
eight wards, 2025-07 to 2026-06, none in Johannesburg, all chosen by the party.
The owner took the MEAN of two measures over those eight, both defensible:

| measure | value |
|---|---|
| median SACP share of the ward vote | 1.815% |
| median SACP / (SACP + ANC), 2.93%, × the ANC's Johannesburg spine level 28.0% | 0.821% |
| **mean — the declared `support`** | **1.318%** |

The 28.0% is the model's own ANC spine level from the 2026-09-16 build log, not
an election result — a model input to a hand value, stated so it is visible.

**The alternatives, measured.** (a) `parent = "ANC"` — the owner's first call —
seeded it at 5.98% of the city: the split path takes the median of the splinter
record, whose named cases are COPE, EFF and MK, breakaways led by a national
figure, not an alliance partner standing a list. (b) An empty table sizes it as a
generic entrant, ≈0.06% — below the lowest of its eight by-elections (0.80%).
Both refuted by its own record; a blind review reached the same table and the
same conclusion independently, and the table was re-derived from the raw file.

**Why not `parent` plus `support`.** ⛔ The split branch of `arrival_rules`
(`pools.py`, `elif as_split`) never reads `support` or `overperform` — a stated
size beside a `parent` is discarded in silence, the defect class `PARTY_KEYS`
exists to close. The `weights` copy is the split path's own emitted voter profile,
so only the size changes. The defect is a `pools.py` code change and is queued,
not fixed tonight (it invalidates every spec).

**How to check it.** Against the 2026 result, and against the band the arrival
record puts around the declared level. **Record.** 2026-09-16, owner's decision.

### §L14 · A pool silenced at the 0.0 corner is held at the city's own rate — 🔴 a declared fallback, not an estimate

**Extended 2026-10-12 (§L15):** at the registration level a pool is also held at the city's own rate BEFORE the fit when the ward table cannot identify it (under `IDENTIFICATION_REACH` of every ward). Same fallback value, same `imputed` record, its own message in `unidentified`.

**Where.** `pools._nest_holding_silent`, with `pools._silent_pools` and
`pools._uninformed_rate`, called from `pool_counts` at each of its three nested
solves. Added 2026-09-28 for prereg C1 / queue entry 30, MODEL-LOG §1.269.

**What.** `pool_counts` fits one rate per pool at each of three levels
(`adult_share`, `registration`, `turnout`), each bounded below at 0.0. Where a
solve lands a pool on **0.0** while the level above still holds people in it,
that pool is HELD at the city's own rate for the level
(`sum(observed) / sum(parent)`; for turnout, votes cast over registered voters)
and the other pools are re-fitted around it. The value is the one `_nnls`
already starts every pool at, and so the one a pool with no parent mass in any
ward keeps. Only the lower corner: a rate on its upper bound keeps the pool in
the electorate and belongs to C2.

**Why it is a judgement.** Nothing measured says how a silenced pool registers
or turns out. Before this, the de facto value was **zero**: no votes, no party
weight, and the pool dropped from the spec while `pool_shares_at_target` still
sized it. Zero is also a judgement, and it is the one that contradicts the
artefact. **Amended 2026-09-29 (blind review, `audits/2026-09-29-pollster-blind/`).**
The city's own rate is a prior for the held pool that is consistent with the
panel: every held TURNOUT (0.436 to 0.560) lies inside the range the
Indian/Asian pool's turnout takes across the 24 fitting years (0.048 to 0.815);
the held registration rate at mangaung 2006 was not compared. It is not
uninformative. It is a specific value, and it
costs fit and moves other pools:

* **Ward-level fit.** Sum of squared ward residuals of the level's solve, free
  fit against held fit, on the fitting years of the declared targets
  (measured 2026-09-29 by instrumenting `_nest_holding_silent` over the
  population `test_no_fitting_year_leaves_a_pool_of_voters_casting_nothing`
  scans): turnout at buffalocity 2011 +26.8% (RMS per ward 371 → 417 votes),
  mangaung 2016 +6.2%, mangaung 2011 +1.6%, mangaung 2006 +1.0%; registration
  at mangaung 2006 +0.2%.
* **Displacement.** The re-fit lowers the other pools' rates in every case.
  At buffalocity 2011 the White turnout goes 0.719 → 0.646 and the Coloured
  0.600 → 0.529, each moving from above to below the median of that pool's
  turnout across the 24 fitting years (White median 0.660, Coloured 0.544);
  at mangaung the White turnout falls by 0.6 to 1.3 points. The held value
  therefore pushes the White and Coloured pools toward the low end of their
  panel range, and at Buffalo City the White pool is where the DA's capacity
  is tightest (§1.259).

A re-fit that silences a second pool holds it by the same rule
(`HoldCascadeRefused` if every populated pool would be held); on the
population above this happens nowhere.

**The cells it acts on.** Whatever
`test_no_fitting_year_leaves_a_pool_of_voters_casting_nothing` prints is the
current list. On 2026-09-28 it was the Indian/Asian pool every time: turnout at
mangaung 2006, 2011, 2016, 2021 and buffalocity 2011, 2021; registration at
mangaung 2006.

⚠️ **The re-fit moves the OTHER pools too.** Holding the silenced pool above
zero takes votes or registrations from the pools it shares wards with, and
through `panel_turnout_spread` it reaches turnout bands in cities where nothing
was held. The sizes are measured in MODEL-LOG §1.269. At Buffalo City one of
the moved pools is the White pool, where the DA's capacity is tightest (§1.259).

**Not the prereg's repair for C2.** D2 fixes partial pooling toward the panel's
estimate for the population group as the repair for unidentified pool levels.
That is F4, deferred past the freeze (TODO §0). This fallback covers only the
0.0 corners, because they are what drop a pool. The `adult_share` corners at
1.0 and the `registration` corners at `REGISTRATION_MAX` are untouched. When C2
lands, the pooled estimate replaces the city's rate in the same place.

**Excluded from the panel spread.** A held rate is not an observed movement, so
`panel_turnout_spread` skips any transition that starts or ends on a pool held
at any level (`PoolCounts.imputed`), as it already skipped a corner. A held
turnout is still in the city's own `turnout_record`, and it becomes the band
centre where it is the most recent election. That centre is the point of the
repair.

**How to check it.** `test_a_silenced_pool_is_held_and_the_rest_refitted`
(mechanism, constructed, with its revert) and
`test_no_fitting_year_leaves_a_pool_of_voters_casting_nothing` (every fitting
year a declared target uses). Each held cell stays listed in the spec's
`rates_on_a_bound` with the corner it came from and the value it was held at.

### §L15 · `IDENTIFICATION_REACH` — 0.25 — ⚖️ the owner's identification test for a registration rate

**Where.** `pools.pool_counts` (the registration solve), `pools._nest_holding_silent` (`hold`), `pools.IDENTIFICATION_REACH`.

**Now.** Registration is fitted with no upper bound. A population group whose largest share of any ward's people is under 25% is not fitted: its registration rate is HELD at the city's own rate (`_uninformed_rate`, the §L14 value), the other pools are fitted around it, and it is recorded in `imputed["registration"]` and in `unidentified` with the reach that selected it.

**Why.** Owner, 2026-10-12: a group the wards cannot identify is capped at the city's registration rate, by one rule for every group (PLAN.md; design 1g §c, "P_hold"). With no bound a group-uniform census error is absorbed by the group's fitted rate (1g §0: ≤ 0.10pp at Johannesburg 2021, 0.06pp at Cape Town 2016, measured); where the ward table says nothing the census level is the only information there is, and holding the city's rate is the composition rule applied pool by pool.

**Not settled by the record.** 1g §c sets the reach test against a coefficient-of-variation test (CV > 1); they disagree on Cape Town's Indian/Asian pool, and neither wins on 1g's ward-fit diagnostic. The owner chose the reach test. Both have a cliff (1g run6); a continuous partial pooling is queue entry 31's.

**How to check it.** `tests/test_pool_bounds.py::test_an_identified_pools_split_does_not_carry_its_census_level` (prereg K1 on a constructed table; the bounded solve moves, the unbounded does not), `::test_the_identification_hold_holds_an_unidentifiable_pool_and_no_other`, `::test_the_held_registration_set_is_the_unidentifiable_indian_asian_pools` (K7, the live held set), `::test_the_registration_bound_is_per_level` (Mangaung Indian/Asian held by name). Prereg 2026-10-12 §8 K1-K7 score it on the re-emitted trees.

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

## M. Added 2026-09-28 — the reader's own forecast (DESIGN-decided §9)

### §M1 · a reader's PR shares stand for both ballots — ⚖️ argued, owner's decision

**Where.** `reader_seats.reader_seats`, which the interactive calls in the
browser to seat a reader's edited forecast.

**Now.** A reader edits the citywide PR vote shares and the winner of any ward.
Schedule 1 sizes each party's entitlement from the COMBINED ward + PR vote
(`seats.py`), and a reader supplies one vote, not two ballots. So each party's
combined vote is taken as `share × total_votes`: the PR shares stand for both
ballots. Wards are taken as picked, and list seats fill each entitlement under
item 16 by `montecarlo.allocate_with_overhang` at the statutory rule.

**Two inputs this makes explicit.**

* `total_votes` is required, not defaulted: the quota is `total // available +
  1`, so the scale moves a party sitting on a remainder boundary. The page
  supplies it from the model state the reader started from.
* An exact tie (equal remainder and equal votes) falls by the order of the
  reader's shares, where Schedule 1 says "by lot".

**What it costs, measured, not assumed.** A model draw does not satisfy the
assumption: its ward ballot differs from its PR ballot party by party (the
ward/PR ratios, §6 of `MACHINERY.md`). `tests/test_reader_seats.py` feeds each
draw's PR-ballot share at the draw's combined total and prints how many draws
that reproduces and how many seats move where it does not. Fed the draw's
COMBINED share instead, every draw is reproduced exactly, which is the
evidence that the arithmetic itself adds nothing. The printed count is the
size of this assumption; read it there rather than here, because it moves with
the model.

**Alternatives, not taken.** Converting the reader's PR shares to a ward ballot
with the model's ward/PR ratios would close most of that gap, and would put a
model level back under a forecast the owner specified as "ignoring all our
levels and logic". Asking the reader for two ballots doubles the edit.

**How to check it.** `tests/test_reader_seats.py`: reproduction from the
combined tally, statute invariants, two hand-worked item 16 councils, and one
refusal per validation.

**Amended 2026-09-28 — the assumption is retired; the reader edits the
combined vote.** Owner, DESIGN-decided §10, after the blind pollster review
(`audits/2026-09-29-pollster-blind/`): the reader's slider shows each party's
share of all votes on both ballots together, exactly what Schedule 1 counts,
with no conversion. The input is `combined_shares`, so no PR share stands for
anything and nothing above about a PR-ballot input applies to the live code.
The reason is the measurement in MODEL-LOG §1.270: fed a draw's PR-ballot
share, the arithmetic moved seats in every draw at Johannesburg 2021 and 2026,
while the draw's combined share reproduces every draw exactly.
`test_the_pr_ballot_assumption_is_measured_not_asserted` still prints that
cost, as the evidence for this decision. What remains a choice: `total_votes`
is the start state's combined total (the start is our prediction since
2026-10-08, see §Q), supplied by the page and the saved-forecast
service from the model artefact, and an exact tie (in the quota's remainder or
in the vote rounding, `reader_seats.combined_votes`) falls by roster order
where Schedule 1 says "by lot". The register row above keeps its original name
for this entry.

**Amended 2026-10-08 — superseded: the reader sets both ballots.** BRIEF
change 13 (owner, 2026-10-08): a reader's entry holds whole votes on the ward
ballot and on the list ballot, and `reader_seats` takes them as they are
(`reader_seats(ward_votes, list_votes, ward_winners, context)`); no share is
converted, no total is fixed, and the statute's pool is formed from the two
ballots as given. The combined input, its `total_votes` and its rounding are
retired (MODEL-LOG §1.292); the editor's bounds that now shape what a reader
can set are §R.

**Amended 2026-10-09 — the tie, against the statute.** The entry says, in its
first form and in the 2026-09-28 amendment, that an exact tie falls by input
order (the reader's shares, then the roster) "where Schedule 1 says by lot".
Schedule 1 has no lot for seats: item 13(2)(b) (16(4)(c) in the excessive-seats
re-allocation) gives an equal surplus to the party with more valid votes, and it
says nothing about parties equal on both (law summary D9,
`audits/2026-10-09-site-batch/law/SUMMARY.md`). Since 2026-10-09
`seats.allocate` ranks the whole-vote surplus and then the votes, so an equal
surplus goes to the higher vote as the statute says, and only parties equal on
both reach a tie, which the statute does not address. That tie is drawn by the
seeded lot under the context's `lot` (the published run's identity; §Q6), so
neither roster order nor input order decides it. The original text is kept
above as the record of what was claimed.

## N. Added 2026-09-28 — re-weighting the published draws (PLAN.md S4)

### §N1 · `MIN_EFFECTIVE_DRAWS` = 200 — 🟡

**Where.** `reweight.py`, read by `require_effective`; the interactive calls it
on the weights of every control before it shows a figure.

**Now.** Typed at 200, the value `audits/2026-09-28-interactive-architecture/PLAN.md`
build step S4 names. Below it the page shows a refusal instead of a number.

**Record.** A control re-weights the published draws instead of re-running the
model, so a figure after a move rests on Kish's effective sample,
(Σw)²/Σw², not on the draw count. The floor is where that sample is judged too
thin to show. ARGUED, NOT TESTED: nothing derives 200. Two things bound it. The
standard error of a re-weighted mean grows as one over the square root of the
effective sample, so at 200 it is five times the standard error of the same
figure on all the published draws; and a quantile at the 5th or 95th percentile
rests on about ten effective draws in its tail at that size. Moves no forecast;
it decides only where the page stops answering.

**How to check it.** `tests/test_reweight.py` shows the floor refusing on a
constructed case and not refusing a modest move; the effective draws at the
headline turnout setting print when that module runs. A reader's view of where
the control greys out is the effective-draw count the page prints beside every
figure.

**Measured 2026-09-28 (MODEL-LOG §1.273).** At Kish = 200 on the published
run's draws, the worst party's 5th percentile is read from about ten effective
draws on its side and a 95th from two to seven (`reweight.tail_effective_draws`).
The floor holds for a mean and does not hold for a tail band. Tails are now
governed separately, by a precision ceiling in seats (§N2, owner 2026-09-30).

### §N2 · The poll-trust dial, `sd(t) = poll_sd / t`, and `MAX_FIGURE_SE_SEATS` = 2.5 — ⚖️ argued, owner's decisions (2026-09-30)

**Where.** `reweight.poll_trust_sd`, called by `reweight.poll_weights` when
it is given `trust`; `reweight.MAX_FIGURE_SE_SEATS`, read at call time by
`reweight.figure`, `reweight.imprecise_figures` and `reweight.within_precision`.
Spec: `audits/2026-09-30-interactive-s6/SPEC-v2.md`, decision 2 and lane R.

**The trust mapping.** The page's poll dial runs 0-100; `reweight` takes it as
`t` in [0, 1] and prices each polled party's reading with a normal likelihood
of sd `polling.poll_sd(poll, share, asof) / t`. At `t = 1` the width is the
model's own error for that poll; at `t = 0` it is infinite, which is uniform
weights exactly (the published forecast, and the site's stated position). The
width is always a multiple of a number the model derived, never one the page
chose. The alternative in the review (B4), "100 = the poll comes true",
collapses the effective draws, and there is no value past 1: trust above the
model's own reading of the poll is refused.

Four details are part of the mapping and are choices:

* `poll_sd` is the TOTAL error the model carries (sampling from the effective
  sample, `POLL_HOUSE_SD`, the undisclosed-screen term and drift), not
  sampling error alone, though decision 2 calls it "the poll's own sampling
  error". A poll with no published `n` is priced on the house term, which is
  `poll_sd`'s own fallback.
* Drift is measured to the target's polling day, as `montecarlo.run_model`
  measures it. `page_polls` stamps that date on each record as `asof`; a
  record without one is refused at non-zero trust rather than priced at zero
  drift.
* The comparison is on the polled parties' renormalised shares, so each sd is
  divided by the poll's reported total over those parties. That is the
  first-order change of units; it ignores the error in the denominator.
* Several polls on multiply their likelihoods, which treats them as
  independent. Two waves of one house share its house error, and the product
  does not know it (`polling.effective_houses` counts houses; nothing here
  uses it).

**The precision ceiling.** A figure the page shows (a party's median, 5th or
95th percentile of seats) is withheld when its Monte Carlo standard error,
`reweight.sampling_se`, exceeds 2.5 seats, and a control stops where any shown
figure would be withheld. This replaced SPEC-v2's rule of a 200-draw floor on
the tail's effective draws (F17), which the owner rejected: under uniform
weights a 5th or 95th percentile already rests on about 255 draws, so that
rule withheld every range at any move. `MIN_EFFECTIVE_DRAWS` stays as the
separate, whole-page refusal on the weights.

**Evidence for 2.0** (the lead's bootstrap, 400 resamples over the published
cell's draws, ANC seats): uniform weights, 5th/95th percentile SE ≈ 0.6/0.8
seats; Black African turnout +5 points with the other pools held, ≈ 1.5/1.4;
+8 points, ≈ 4.1/3.5. So the ceiling admits the pre-registered headline move
(+5, `prereg/2026-09-28-reweight-against-paired-rerun.md`) and stops short of
+8. ARGUED, NOT TESTED against any election: the owner's line for how much
re-run noise a shown seat figure may carry. It moves no forecast.

**Raised from 2.0 to 2.5 the same day (owner).** At 2.0 the Black African
slider stopped short of +5: every major party was within ±2 seats there, but
ActionSA's 95th percentile carried ±2.1 (the page's native fixture). The rule
applies to every party alike, so the ceiling moved rather than an exemption.
At 2.5 the pre-registered +5 is reachable; +8 still withholds figures.

**How to check it.** `tests/test_reweight.py`: the mapping's two ends and its
1/t form on a constructed record; `sampling_se` against a bootstrap and
against repeated samples on integer seats; on the published draws, uniform
weights withhold no published figure and Black African +8 withholds some.
`sampling_se` on the published draws can be compared with the bootstrap
figures above at any time.

### §N3 · "Analyse my forecast": the bands (`ANALYSIS_SEAT_BAND` = 2 seats, `ANALYSIS_SHARE_BAND_POINTS` = 2.0 points) and the whole-forecast figure — 🟡 argued, not tested (2026-10-03)

**Where.** `reweight.within_band`, `reweight.ward_calls_likelihood` and
`reweight.council_outcome`, called by `interactive/pyboot/page.py`'s `analyse` when a reader presses "Analyse my
forecast" in section 2 of /your-forecast/ (the owner's sweep of 2026-10-03,
item 6).

**Now.** Every chance is the PUBLISHED forecast's: the published cell's draws,
each counted once, seated by the statute. Five figures:

* **A ward.** The chance the model gives the reader's winner there,
  `reweight.ward_win_probability` (the published map's Jeffreys-corrected
  estimate). Printed on hover: "We give this outcome a N% chance."
* **A party's seats.** The share of simulations in which the party's seats
  land within `ANALYSIS_SEAT_BAND` of the reader's figure, either side, edges
  included. Two seats, typed: wide enough that a reader's round number near
  the model's middle scores as near it (the middle's own Monte Carlo error is
  under one seat, §N2). For a party whose 90% range is several times wider
  than the band, a figure outside that range scores low. For a party whose
  90% range is about as wide as the band or narrower (a party with a few
  seats), any figure near its middle scores high, so the figure separates
  little there. Not derived from anything.
* **A party's vote.** The share of simulations in which the party's
  LIST-BALLOT share lands within `ANALYSIS_SHARE_BAND_POINTS` of the reader's
  combined share. The draws carry no combined share (`export_draws` refuses
  one: the statutory pool is built inside the draw loop), so the list ballot
  is the nearest quantity the model has; the page says so beside the figure.
  A party whose ward ballot runs ahead of its list ballot is scored against
  the lower of the two. Two points, typed, on the same reasoning as the seat
  band.
* **The whole forecast: "this outcome".** The headline is the owner's form
  (2026-10-03): "We give this outcome a N% chance. But historical trends can
  always be broken." An exact match of the whole forecast (every ward, every
  seat, every share) has a chance of about zero for any forecast, the
  model's own included, so "this outcome" is DEFINED as the reader's
  council-level result, three parts read off the reader's council:
  1. the largest party: the party with the most seats on its own, or, when
     the reader's council has a tie for the most, a tie;
  2. whether any one party has a majority on its own (the reader's council
     against the majority the seat law reports for it);
  3. only if the reader picked a governing coalition: that coalition holding
     a majority.

  N is the share of the published draws, each counted once
  (`reweight.uniform`, the same weights as every other figure in the
  analysis), in which all three parts hold in the same draw, each draw read
  against its own majority threshold (`council/deduct`). The largest party
  is read as `reweight.largest_party` reads it (a tie is its own outcome).
  A coalition party outside the draws' party columns (summed into `OTHER`)
  counts no seats. Function: `reweight.council_outcome`. The page states
  the definition in the analysis's footnote and prints the outcome it scored
  in words under the headline. Typed choices with no record behind them:
  which three parts make "the outcome", and that the coalition part applies
  only when one is picked.
* **The ward calls, second (superseded 2026-10-03 by §N4's Wards line,
  the plain mean of correct calls over the draws; the rank below is no
  longer printed).** "We expect N of your M ward calls to come
  true": the sum of the ward chances. Beneath it, a rank: "Ranked by the
  chance we give each ward's winner, your ward calls as a set come level with
  or above the ward results of R of our simulations." Method of the rank:
  each set of ward results is scored by the sum over wards of the log of the
  chance the model gives its winner there. The reader's calls are scored so,
  and so is every simulation's own set of ward winners; R is the share of
  simulations scoring at or below the reader's. R is a PERCENTILE, not a
  chance: the chance of the reader's exact set is vanishingly small for any
  set, the model's own modal calls included, and the modal calls rank above
  every simulation.
* **Wording.** Every chance the analysis gives, the outcome's, a ward's
  (on hover), a party's seats and its vote (on hover over the cell), is
  worded "We give this outcome a N% chance"; a chance printed as "under
  0.1%" or "over 99%" reads "a chance of under 0.1%".

**What the method assumes.** The score treats wards as independent. They are
not: the simulations share citywide swings, so a reader who moves many wards
the same way is penalised as if each move were separate. Scoring every
simulation by the same rule puts the reader's set and the model's on one
footing, so the percentile ranks fairly; it is not a joint probability. The
council-level outcome is read draw by draw, so it carries the citywide swings
the ward score ignores. Seats and votes enter it only through its three
parts; they are shown party by party.

**Rejected wordings.**

| Wording | Why it was not used |
|---|---|
| "We give this outcome N% chance" with "this outcome" the whole forecast, every ward, seat and share | Its chance is about zero for any forecast, the model's own included. The owner's form is kept with "this outcome" defined as the council-level result above. |
| "We expect N of your M ward calls to come true" as the headline (lane Y, 2026-10-03) | The owner asked for a chance in the headline (2026-10-03, item 7). It is the second sentence. |
| "We give ward results as unlikely as yours, or less likely, a chance of R" (lane Y, first build) | R reads as the chance the forecast comes true. The untouched start printed "over 99%" (review of lane Y, 2026-10-03, must-fix 2; STYLE rule 10). |

**Waiting on the owner.**

* The bands for small parties: a fixed band of two seats and two points
  scores near-certain for a party with a few seats (ACDP 91%, Al Jama-ah
  over 99% at any plausible figure; review of lane Y, item 11). Options: a
  band scaled to each party's 90% range, or no seat and vote chance for
  parties below a seat threshold. Kept as typed until decided.

**Alternatives, not taken.** A joint figure across wards, seats and votes
(a distance in all three at once) would need a weighting of the three, which
is another judgement with no record to fit it to. Scoring the reader's calls
against the reader's own adjusted weights would answer "how likely under my
changes", which section 1 already shows.

**How to check it.** `tests/test_reweight.py` holds `within_band`,
`ward_calls_likelihood` and `council_outcome` to hand enumerations on constructed draws and
weights; `tests/test_your_forecast_page.py` holds `page.py`'s `analyse` to
those functions on the published draws for a constructed forecast. A
different band changes only which chance is printed; nothing in the model
reads it.

**Amended 2026-10-10 (§N10).** The badge on a reader's forecast no longer
reads `council_outcome`: it is judged by the forecast's boldest single call
(`reweight.boldest_call`). The "this outcome" chance line in "Analyse my
forecast", on the share cards and in the arrival view still prints
`council_outcome`'s figure, unchanged.

### §N4 · The competition rule: seats, then ward calls, then vote (list ballot); and the seat line — ⚖️ owner's order, the line derived (2026-10-03)

**Where.** `src/score_forecasts.py` (`seat_error`, `wards_called`,
`list_vote_error`, `rank_key`, `MEASURES`); on /your-forecast/,
`interactive/pyboot/page.py`'s `analyse` and `reweight.scored_as_results`,
with the line `reweight.seat_error_line`.

**The rule (owner, 2026-10-03).** Every forecast of the council is ranked on
three measures, compared in this order, each only breaking ties in the one
before. No weight combines them.

1. **Seats.** For every party holding a seat in the forecast or the result,
   `|forecast seats − actual seats|`, summed. A party the forecast never
   names is a forecast of zero. Lower is better.
2. **Ward calls.** The wards whose forecast winner is the actual winner.
   Higher is better.
3. **Vote, list ballot.** For every party with a share in the forecast or on
   the result's list (PR) ballot, `|forecast share − actual list-ballot
   share|` in percentage points, summed. Lower is better. The forecast's
   share is the one a reader sets, its share of both ballots together, which
   the seat law reads as its PR share (§M1). It is compared with the list
   ballot alone because the published simulations carry no other per-party
   share, and the page scores readers against them with these same
   functions. A forecast exact on the combined vote therefore still scores
   the gap between the two ballots.

Equal on all three, forecasts share a rank; the earlier save before the lock
names a single winner. This supersedes `DESIGN-decided.md` §13, which ranked
the ward-count error second and correct calls third. The ward-count error
and the ward/list split are still computed and reported, not ranked.

**On /your-forecast/ ("How likely is your forecast?").** The reader's
forecast is scored by these functions against EACH published simulation (the
published cell, each draw counted once, statutory seats) as if that
simulation were the result. The page prints, in the rule's order: the
expected seat error and the chance it is within the seat line or fewer
seats; the expected number of correct ward calls out of the wards; the
expected list-ballot vote error in points. Two adaptations to the draws:

* The draws' `OTHER` columns sum every party that never wins a seat in any
  draw. Its seats are zero by construction, so a reader's seats for such a
  party are compared with zero, as the rule does. Its list share is a sum,
  so the reader's shares for those parties are summed and compared with it
  as one group: a lower bound on the party-by-party error, for parties with
  no seat in any draw.
* The expected correct calls is the plain mean over the draws. The chance
  printed for a single ward (on hover) is `reweight.ward_win_probability`,
  Jeffreys-corrected as the published map's is. The two differ by that
  correction, which is under one ward in total; neither is wrong.

**The seat line (derived since 2026-10-03, after the review of the share
build).** `reweight.seat_error_line`: the model's own middle forecast
(`reweight.middle_seats`: each party's median seats over the draws, rounded
half up) is scored against every draw by `seat_error`; the line is the median
of those errors, rounded down. Half the simulations, or more, are that close
to the model's middle forecast. It replaced a typed 10 seats, the owner's
suggestion, under which every forecast, the model's own start included,
printed "a chance of under 0.1%": the reviewer measured the start forecast's
expected seat error at 108.5 seats, and 94.5 for each party's median
(figures from that review, not re-measured here; the native fixture
`interactive/tests/native-play.json` holds the current line for its cases).
The page says how the line is set where it explains the method. **Owner:**
the 10-seat line was yours; a different derivation, or printing where a
forecast ranks among the simulations instead, is yours to choose.

**How to check it.** `tests/test_score_forecasts.py` holds the three
measures to hand-worked arrays and the ranking to constructed forecasts on
the 2021 result, including one that only the new order ranks correctly;
`tests/test_your_forecast_page.py` holds `analyse`'s score to the three
measures written out as a loop over the published draws.

### §N5 · /your-forecast/ reserves room for two extra seat rows (`--yf-spare-rows` = 2) — 🔴 typed, presentation only (2026-10-03)

**Where.** `interactive/css/your-forecast.css`, "Reserved message regions";
`interactive/js/model.js`'s `renderSeats` marks the live seat table with
the rows it adds (`data-extra`).

**Now.** Section 1's seat table shows a row for every party with a middle of
at least the row threshold of `interactive/pyboot/page.py` in the published forecast or under the reader's
settings (`page.py`, owner decision D1). A lever that lifts a party to the
threshold adds a row. So that the row moves nothing below the table (owner,
2026-10-03: the page must not jump when a lever moves), the table keeps room
for two rows more than the published forecast's, empty until a lever fills
them. A third added row grows the table, and
`interactive/tools/yf_jump_check.mjs` fails on it.

**Section 2's council (added 2026-10-03, after the review of the share
build).** The same two, in their own `--yf-spare-rows` on section 2's council
table (`your-forecast.css`, "section 2's council"; `make.js` `councilRows`).
Every party seated at the start section 2 is open at, or in a friend's
forecast, keeps its row when the reader takes it to zero seats, so no edit
removes a row. A party seated in neither is new: up to two new rows fill the
reserved room, each a fixed `--yf-new-row` high (a long name is cut with an
ellipsis rather than wrapping); a third grows the table. The council sits
above the vote list on a phone, so a row added or removed there moved the
lever (measured by the reviewer at 375 wide: a party's vote set to 0 moved
the vote box 30px). The coalition chips below the vote list list the same
parties; a new party adds a chip, below the lever.

**Why two.** Typed. In the check's moves, every lever moved at once
included, the added rows fit. No record says how many parties a reader's
settings can lift, or how many a reader's vote edits can seat.

**How to check it.** `yf_jump_check.mjs` measures the document height and
the landmarks below the table around every lever move, at 375 and 1440
wide; its section 2 moves include a party's vote set to 0, a typed vote over
100, and a party from "Other parties" given its first seats. Nothing in the
model reads this value.

### §N6 · The boldness badge: Safe call at 20% or more, Bold call from 5% to under 20%, Wild call under 5% — ⚪ superseded 2026-10-10 by §N10

**Where.** `reweight.BOLDNESS`, read only by `reweight.boldness`, which
`reweight.outcome_chance` calls for `interactive/pyboot/page.py`'s `analyse`
and for the seat Worker's card answer (`worker-api/seats-py/src/entry.py`,
`/v1/card`). The share cards, the link preview and the arrival view on
/your-forecast/ print the badge they are handed; no JavaScript computes it.

**Now.** A reader's forecast carries a badge naming how bold its
council-level outcome is (§N3: the largest party, a majority alone or not,
the chosen coalition reaching a majority), from the chance the published
forecast gives that outcome:

| badge | chance of the reader's outcome |
|---|---|
| Safe call | 20% or more |
| Bold call | 5% to under 20% |
| Wild call | under 5% |

A chance exactly at an edge takes the higher band.

**Why these.** The owner's choice of the designer's proposal
of the bands proposed in the share design (`audits/2026-10-03-share-design/DESIGN.md` §5). The edges were set by
looking at the chances `council_outcome` gives the common outcomes on the
published draws: an outcome with no coalition can be no likelier than the
likeliest largest-party outcome, and a two-party government led by one of the
two largest parties lands in Safe or Bold; an outcome led by any other party
lands in Wild. Nothing is fitted; the edges are round numbers.

**How to check it.** `tests/test_reweight.py` holds the edges (exactly 5% and
20%). To see where today's outcomes fall, run `council_outcome` over the
published cell for each largest party with and without a majority, as
`interactive/pyboot/page.py`'s `analyse` does. Nothing in the model reads the
badge.

### §N7 · Entries equal on all three keys: the earlier seal places higher, then the seal id — ⚖️ judgement (2026-10-03)

**Where.** `src/rank_entries.py` (`rank_entries`), through
`score_forecasts.rank`'s `saved_at`; the leaderboard (`/leaderboard/`) prints
the place.

**Now.** Every sealed forecast is one entry, and every entry is ranked and
listed (owner, 2026-10-03). The vote error is rounded to one decimal
(`rank_entries.VOTE_DP`) before ranking, the precision the leaderboard prints,
so two entries that look equal on all three keys are equal. Entries equal
on seats, ward calls and vote (§N4) are placed by the earlier seal, the
Worker's own clock at sealing, to the second. Entries sealed in the same
second are placed by seal id, in character order. Every entry has its own
place; `score_forecasts.rank`'s shared competition rank is not printed.

**Why.** The owner asked for ties broken by the earlier seal. A seal time is
the one ordering of entries that existed before the result, so it cannot be
chosen after it. The seal id is a signature, so its order is arbitrary but
fixed when the seal is made.

**How to check it.** `tests/test_rank_entries.py` ranks three entries equal on
all keys, two of them sealed in the same second, and shows the order check
fires when the seal times are dropped. It also shows an entry off on the
vote by less than the printed decimal tying with the perfect entries, and
placing apart from them when ranked unrounded.

### §N8 · Entries are deleted ninety days after the leaderboard is published — ⚖️ judgement (2026-10-03)

**Where.** `docs-public/privacy.md`, "Forecasts entered"; the owner's delete
command is in `wrangler.toml`'s ENTRIES note.

**Now.** The D1 table `entries` (`migrations/0001_entries.sql`) is emptied
ninety days after `/leaderboard/` is published, and within six months of
polling day if no leaderboard is published. The same day the owner deletes
the results-night export (`~/joburg-entries.json`) and replaces every name on
the leaderboard with "Anonymous #" and the seal id's start
(`rank_entries.py --anonymise`); the leaderboard stays on the site. An entry
is deleted sooner on request, by its seal id: from D1, and once published
from the leaderboard (`rank_entries.py --drop`). The leaderboard's data is
gitignored, at `content/<city>/` and in `site/`, so a removed name is not kept
in the repository's history; `deploy_check` ships the built copy uncommitted.
D1 Time Travel keeps a restorable copy of deleted rows for up to thirty days
(seven on the Free plan); the privacy page says so.

**Why ninety.** Typed. Long enough for a reader to find their entry, query
it, or ask for a correction after the results; nothing in the ranking needs
the rows once the leaderboard is written. Nothing measured sets it. **Why six
months.** Typed: a limit that holds if results night never produces a
leaderboard, set past the ninety days that follow a normal count.

**How to check it.** The deletion is a command the owner runs; nothing runs
it on a schedule. `tests/test_entries.py` holds the privacy page to the
sentences; `tests/test_rank_entries.py` shows `--drop` and `--anonymise` on a
board and both paths gitignored.

### §N9 · Thirty seals per connection per minute (the SEAL_LIMIT binding) — 🔴 typed (2026-10-03)

**Where.** `wrangler.toml` `[[ratelimits]]`, binding SEAL_LIMIT; `src/share-edge.js`
`sealLimited`.

**Now.** `POST /seal/1` is counted per connection by the Workers Rate Limiting
binding. Past thirty in a minute it answers 429 and the share sheet says
"Too many links sealed from this connection. Try again in a minute." The
counter's key is an HMAC of the connection's address under the seal key
(`seal.js` `rateKey`), so no address is stored; the counter is Cloudflare's,
per location, and forgets after the minute.

**Why this mechanism.** The binding needs nothing created and stores nothing
for this site. A counter kept in the Workers cache would be per data centre,
not atomic, and would hold the key as a cache entry. **Why thirty.** The share
sheet seals when it opens and when a name or the forecast changes, so one
reader can seal several times in a minute. Mobile networks in South Africa put
many readers behind one address (carrier-grade NAT), so the limit is set well
above one reader's use. Typed, not measured: Cloudflare allows a period of ten
or sixty seconds only.

**How to check it.** `tests/test_entries.py` runs the limit at three and shows
the fourth seal refused, another address and a new period passed, and a
preview refused before it is counted.

### §N10 · The reader's badge: the boldest single call, in five bands (45, 30, 15, 5%) — ⚖️ owner's measure and bands (2026-10-10)

**Where.** `reweight.boldest_call` and `reweight.BOLDNESS`, read only by
`reweight.boldness`; both called by `reweight.outcome_chance` for
`interactive/pyboot/page.py`'s `analyse` and the seat Worker's card answer
(`worker-api/seats-py/src/entry.py`, `/v1/card`). The share cards, the link
preview and the arrival view on /your-forecast/ draw the owner's badge for
the words they are handed (`src/stamps/reader-<words>.svg`, served at
`/stamps/`) and name the call; no JavaScript computes either.

**Now.** For each party whose seats in the reader's forecast differ from the
model's middle forecast (`reweight.middle_seats`, each party's median seats
over the published draws), the share of simulations at least that far out on
the reader's side: `P(seats ≥ x)` when the reader's `x` is above the middle,
`P(seats ≤ x)` when below. The smallest of these is the boldest call; the
badge comes from it and the card names the party and its seats ("Boldest
call: the PA at 38 seats."). A tie goes to the party first in the draws'
column order. A party with no column in the draws holds no seats in any
simulation, as in §N3.

| badge | chance of the boldest call |
|---|---|
| Safe bet | 45% or more |
| Steady as she goes | 30% to under 45% |
| Long shot | 15% to under 30% |
| Wild call | 5% to under 15% |
| Hail Mary | under 5% |

A chance exactly at an edge takes the higher band. A forecast equal to the
middle forecast has no call and is a Safe bet. The badge reads the exact
chance, not a printed one; the card prints no chance for the call, so no
printed figure can disagree with it.

**Why.** The owner's decision, `audits/2026-10-09-site-batch/BADGE-DECISION.md`,
which records the measurements behind it: what §N6's badge gave the common
forecasts and the model's own middle forecast on the published draws, and
the chances of eight constructed forecasts under this measure. The owner's
words: "Our score is a little informational but mainly just fun. All
forecasts get judged against the real result." The edges are the ones
printed on his badges; nothing is fitted.

**Known limit, accepted by the owner.** A forecast that moves every party a
little takes its badge from some small party's tail (BADGE-DECISION.md
measures how often). The share fixture's two readers both take theirs from a
one-seat party.

**How to check it.** `tests/test_reweight.py` holds the four edges, the
measure on constructed draws, and the eight constructed forecasts of
BADGE-DECISION.md's table re-measured on the published draws (it fails, and
says to re-measure, when the published model is no longer 7ea27c28); and that
every badge word has the owner's file and every file a word. Nothing in the
model reads the badge.

## O. Added 2026-09-29 — mergers (F5, audits/2026-09-29-mergers/SPEC.md)

### §O1 · `MERGER_RETENTION` — 0.75, range [0.5, 0.9] — 🔴 declared, not measured

**Plain — What a merger keeps.** When parties merge, or one stands down for
another, and only one of them is on the ballot, it inherits 75% of the other's
previous vote. The rest goes to the parties that compete for the same voters, as
any absent party's vote does. In 2026 ActionSA inherits from Forum 4 Service
Delivery, and Rise Mzansi from GOOD. No merger in the record shows how much
carries over, so the share is a judgement; a review in September that was not
shown our reasoning recommended 50%. A lower share moves the inheriting party
down. It cannot be changed on [your forecast](your-forecast/).

**Where.** `pools.MERGER_RETENTION`, read at call time by `pools.apply_mergers`,
which every function in `pools.MERGER_CONSUMERS` calls: `montecarlo.run_model`
(the national baseline and every VD, then the preceding local PR shares),
`pools.emit_pools` (the spec's baseline and the successor's pool vector), and
`theta_residual._residuals_cached`. The declarations are data, `pools.MERGERS`,
with sources in SOURCES.md "Mergers".

**What.** A merger partner NOT on the target's ballot hands `MERGER_RETENTION`
of its share to the partner that IS, in each election's shares the consumer
passes. The remainder, (1 − r) of it, is then removed by the off-ballot drop as
the whole of it was before. Which partner inherits is read from the roster per
city and target; nothing in code names a successor. Two partners on the ballot
with a third off it is refused. The successor's pool vector becomes the
mass-weighted blend of its own and the predecessor's (`pools.merged_vector`).

**The rule that goes with it (owner, DESIGN-decided §10).** A merger adds to a
record the successor already holds and never creates one. RISE has a 2024
national record and no 2021 local one, so it takes GOOD's transfer on the
national route only; ActionSA takes Forum 4 Service Delivery's on both.

**Why it is a judgement.** No merger in the archive identifies a retention.
The two with elections on both sides (ID into the DA; NNP into the ANC) give
naive citywide retentions from −17 to +56, because the successor's own swing is
5 to 20 times the predecessor's mass (SPEC §1). The value is the owner's: a
merger is "not a perfect combination". The blind review (2026-09-29)
recommended 0.5 in [0.3, 0.8], on the reading that GOOD–RISE is a stand-down
pact whose voters follow incompletely; recorded, not adopted.

**How big it is.** The share moved is r × the predecessor's baseline share,
which MODEL-LOG §1.275 tabulates for each r with the resulting
medians. It acts at the 2026 targets only: no declared merger predates a held
election, so no backtest row moves and the backtest cannot score it.

**How to check it.** Against the 2026 result: RISE's and ActionSA's shares
relative to their 2024 baselines. Tests: `test_roster_aware_baseline.py`'s
merger block (r × P on constructed shares, the no-new-record rule with its
revert, the roster's direction, the real-baseline transfer, the consumer scan
in both directions, and that the mechanism names no party).

## P. Added 2026-10-07 — claim verdicts, the Soweto wards, the Mashaba claim

### §P1 · `CHANCE_SCALE` — the verdict a chance earns — ⚖️ owner's scale (2026-10-07)

**Where.** `render_sheet.CHANCE_SCALE`, read by `render_sheet.scale_verdict`
and `render_sheet.verdict_fault`; `render_sheet.VERDICT_STEP` is built from it
and `render_sheet.SETTLED_VERDICTS`, so the badge colours and the scale are one
table. `render_home` prints the same verdict through `render_sheet.verdict_class`.

**Now.** A claim rated by chance gets its verdict from the chance that the
claim holds:

| chance the claim holds | verdict | colour step |
|---|---|---|
| under 1% | NEAR IMPOSSIBLE | false |
| 1% to 15% | EXTREMELY UNLIKELY | unlikely |
| 15% to 45% | QUITE UNLIKELY | unlikely |
| 45% to 55% | COIN FLIP | open |
| 55% to 75% | QUITE LIKELY | likely |
| 75% to 90% | VERY LIKELY | likely |
| over 90% | NEAR CERTAIN | true |

FALSE (step false) and TRUE (step true) are for claims settled by fact or
arithmetic, not chance, and carry no `chance` field.

**Amended 2026-10-10.** The words are the owner's badges' words ("We
standardised badges, so adjust pages to match the badge"): 15% to 45% is
QUITE UNLIKELY (was UNLIKELY) and 45% to 55% COIN FLIP (was A COIN FLIP). The
edges and colour steps are unchanged, and no claim carried either word.
Each verdict's badge file is named by its words
(`render_sheet.verdict_badge_file`).

**The edge rule.** A chance exactly on an edge takes the band nearer a coin
flip: 1% is EXTREMELY UNLIKELY, 15% QUITE UNLIKELY, 45% and 55% COIN FLIP, 75%
QUITE LIKELY, 90% VERY LIKELY. This agrees with the owner's "under 1%" and
"over 90%". The chance is judged as the page prints it
(`reweight.chance_text`), so the verdict never disagrees with the figure beside
it.

**The guard.** Each chance-rated claim in `content/<city>/claims.toml` names
its figure: `chance = "<name>"`, or `chance = "1 - <name>"` when the claim
holds where that figure's event does not. The build reads the value out of
that figure's own token and refuses a verdict the scale does not give it. The
words it replaced (OUT OF REACH, VERY UNLIKELY, MORE LIKELY THAN NOT, LIKELY,
and on 2026-10-10 UNLIKELY and A COIN FLIP) are off the table, so a stale
label stops the build. A chance written as a
number instead of a name stops the build.

FALSE and TRUE need a `settled` field saying what fact or arithmetic settles
the claim, and may not name a chance, so a chance-rated claim cannot be
relabelled FALSE or TRUE to leave the scale. `render_sheet.claims_faults` is
the one check: the sheet runs it with the computed figures, and the home
page's claims list runs it on the form alone, since it computes no figure.

**The sentence that follows the verdict.** A claim may write `[[holds]]` and
name its subject in `holds_subject`; `render_sheet.HOLDS` gives the
predicate (owner, 2026-10-07): NEAR CERTAIN "is almost certainly correct",
VERY LIKELY "is very likely correct", QUITE LIKELY "is probably correct",
COIN FLIP "is as likely right as wrong", QUITE UNLIKELY "is probably wrong",
EXTREMELY UNLIKELY "is very likely wrong", NEAR IMPOSSIBLE "is almost
certainly wrong", TRUE "is correct", FALSE "is wrong". So "Mashaba is very
likely correct" cannot outlive its verdict.

**Text written for one end of the scale.** A claim whose own words are true
only at the likely end names the lowest verdict they may print under:
`requires_at_least` (the Mashaba card: QUITE LIKELY, for "The DA needs
Sowetan support, or partners who have it"). The build refuses the claim if its
verdict falls below it (`render_sheet.VERDICT_ORDER`), so the text must be
rewritten before a contrary verdict prints.

**Why it is a judgement.** The words and the edges are the owner's. Nothing
derives them. It moves no draw, seat or probability.

**How to check it.** `tests/test_site_structure.py`: every edge on, under and
over; a constructed mismatched verdict refused; every live claim accepted by a
regenerated sheet.

### §P2 · `SOWETO_GAZETTEER`, `SOWETO_EXCLUDE`, `SOWETO_CUT` — which wards are Soweto's — ⚖️ owner-accepted (2026-10-07)

**Where.** `areas.SOWETO_GAZETTEER`, `areas.SOWETO_EXCLUDE`, `areas.SOWETO_CUT`,
applied by `areas.derive`, which writes `content/joburg/areas.toml` `[areas.soweto]`.
Read by `render_sheet` for the Mashaba claim only. No model code reads it.

**Now.** No IEC or MDB file names Soweto. A 2026 ward is a Soweto ward if at
least half (`SOWETO_CUT` = 0.5, inclusive) of its registered voters are in
voting districts whose IEC voting-station address names Soweto or a Soweto
township, and names neither exclusion.

* **Registration**: `part_registered` in `vd_ward_2026.csv`, read through
  `montecarlo.read_ward_crosswalk`, so a split voting district counts in each
  ward for its own part. That roll is the MDB layer's REGPOP, a 2024
  snapshot (SOURCES.md, Boundaries).
* **Addresses**: the `ADDRESS` field of `votingstations2026_JHB.geojson`,
  joined on `VOTINGDIST`, one station per voting district.
* **Gazetteer**: SOWETO, CHIAWELO, TSHIAWELO, DHLAMINI, DLAMINI, DIEPKLOOF,
  DOBSONVILLE, DOORNKOP, DUBE, EMDENI, MNDENI, EMNDENI, JABAVU, JABULANI,
  JABULANE, KLIPTOWN, KLIPSPRUIT, MAPETLA, MEADOWLANDS, MMESI, MOFOLO, MOLAPO,
  MOLETSANE, MOROKA, NALEDI, ORLANDO, PHIRI, PIMVILLE, PROTEA GLEN, PROTEA
  NORTH, PROTEA SOUTH, PROTEA CITY, SENAOANE, TLADI, WHITE CITY, WHITECITY,
  ZOLA, ZONDI, LUFHERENG, SLOVOVILLE, GLEN RIDGE, GLENRIDGE, BRAAMFISCHER,
  BRAAM FISCHER.
* **Exclusions**: KLIPSPRUIT WEST, ELDORADO.
* **Matching**: upper-cased, spaces collapsed, a term matched at the START of
  a word. So BRAAMFISCHER matches BRAAMFISCHERVILLE, and a term inside a word
  does not match. Braamfischerville's stations give ROODEPOORT as their town:
  it is in the set by the gazetteer, not by an address naming Soweto. Under
  whole-word matching wards 44 and 49 (Braamfischerville) drop out; under
  plain substring matching the ward list is the same as this rule's.
* **Streets** (`STREET_TYPES`, added 2026-10-07): a gazetteer word followed by
  a street type (DRIVE, STREET, ROAD, BYPASS and the rest) names a street, not
  the place. Two stations matched that way before the rule: "N12 MOROKA
  BYPASS JHB LENASIA" (ward 10) and "6694 DLAMINI DRIVE IVORY PARK MIDRAND"
  (ward 133). Neither changed a ward; the list is the same 40 with and
  without the rule.

**The result** is the list in `content/joburg/areas.toml` `[areas.soweto]`, which
`tests/test_areas.py` regenerates from the raw files and compares.

**Sensitivity to the cut** (measured 2026-10-07 on the published 5,000
simulations; MODEL-LOG §1.288). The wards nearest it are 29 (37.9% of its
voters at Soweto stations), 10 (43.1%, Protea South with Lenasia; 47% before
the street rule removed the Moroka Bypass station) and 11 (58.2%). Any cut
from 0.44 to 0.58 gives the same 40 wards. At 0.40 ward 10 joins: the DA wins
no Soweto ward in 78.9% of simulations instead of 97.3%, and the Mashaba
claim holds with chance 85.2% instead of 76.5%, VERY LIKELY either way. At
0.60 ward 11 leaves: 98.1% and 76.1%, VERY LIKELY.

**Why it is a judgement.** "Soweto" has no official boundary in these files.
The gazetteer, the exclusions and the cut are choices.

**How to check it.** `.venv/bin/python src/areas.py --check`.
`tests/test_areas.py`: matching and exclusion on constructed addresses, the
cut inclusive and split VDs by part on a constructed crosswalk, the committed
list equal to a regeneration, and a one-ward change caught.

### §P3 · `REALISTIC_PARTNERS`, `ZILLE_RED_LINES` — what "the DA wins Joburg" means in the Mashaba claim: a coalition of at most 3 parties — ⚖️ owner's definition (2026-10-07)

**Where.** `render_sheet.da_coalitions`, called by `render_sheet._soweto`, over
`scenarios.all_party_seats`.

**Now.** Herman Mashaba said Helen Zille cannot "win Joburg without the support
of Soweto". The owner's reading, per simulation:

* **Win Joburg, the rated definition: a REALISTIC coalition the DA leads.**
  `REALISTIC_PARTNERS` names two: ActionSA with the PA, or the ANC. A
  coalition counts where the DA and its partners reach the simulation's
  majority threshold and the DA has strictly more seats than each partner.
  Zille ruled out the EFF and MK (`ZILLE_RED_LINES`), not the ANC.
* **More than three parties are not counted as a win** (owner, 2026-10-07).
  The card prints, as context, how often the DA would lead a majority by
  adding small parties to ActionSA and the PA (`DA_CORE_PARTNERS` plus every
  party outside the ANC and `ZILLE_RED_LINES` with fewer seats than the DA,
  the DA larger than each), and does not rate it. The build still computes
  how many small parties, largest first, the median such simulation needs
  (`small_needed_median`); since 2026-10-07 no card prints it. The evidence
  is one case:
  the last DA-led council (December 2021) was nine parties, the DA, ActionSA,
  the IFP, the FF Plus, the PA, the ACDP, Cope, the UIM and the ATM, holding
  exactly 136 of 270 seats (News24, 13 December 2021; Daily Maverick,
  3 October 2022), and it lost its majority when the PA left in September
  2022 (BizNews). The research does not establish a size threshold: Pholoma
  et al. (2024, JOLGRI) attribute South African metro coalition collapses to
  ideology and personality, and compare no coalition sizes. The cut at three
  is a judgement, not a finding. The card's intro prints the coalition's
  party count as the fixed token jhb_2021_coalition_parties
  (content/joburg/stats.toml); the seat count stays in SOURCES.md.
* **Without Soweto's support**: the DA wins none of the `[areas.soweto]` wards
  (`ward_draws.csv`).
* **The rated chance**: the claim holds with chance 1 − P(a realistic DA-led
  coalition | the DA wins no Soweto ward), declared in claims.toml as
  `chance = "1 - realistic_given_none"`. A conditional figure whose condition
  no simulation meets is not computed, so the card stops the build rather than
  print a share of nothing.

All seats are every party's, from `seat_detail_draws.csv` through
`scenarios.all_party_seats`, which refuses a simulation whose parties do not
add up to its council.

**Why it is a judgement.** Which partners are realistic is the owner's call;
the seats cannot say which parties would work together. Adding a partner (the
IFP, the VF+) raises the chance of a DA win and lowers the chance the claim
holds; the small-party figure is near the upper bound. Vote shares by area are not
in the published simulations, so "support" is read as ward wins.

**How to check it.** Re-derive from the three published files.
`tests/test_site_structure.py` checks the coalition rules on constructed
seats, including a DA no larger than its partner and the count of small
parties needed. MODEL-LOG §1.286 to §1.288 record the figures.

### §P4 · the plausibility instrument's constants — `TINY_LINE` 1% · `SIZE_CLASSES` · `OUTER_K` 1 IQR · `J7_FEATURES` · `J8_FEATURES` · `RATIO_LOG_FLOOR` 1e-4 · `MIN_JUDGING` 8 · `FAIL_P` 0.05 · `PIT90_MIN_FRACTION` 0.75 · `COLLAPSE_JUMP_MULT` 3 — ⚖️ typed (2026-10-12)

**Where.** `src/plausibility.py` (design `audits/2026-10-11-model-round/step1/1h-plausibility-check-design.md` §5.1).

**Now.** The tiny-party line for the tiny features (1%, the owner's); the five size classes at the previous election (under 1%, 1-3%, 3-10%, 10-30%, 30% and over); the outer envelope at the record's range ± 1 IQR; the two joint counts: seven whole-vote features (`J7_FEATURES`: `vol`, `max_gain`, `max_loss`, `d_enp`, `top2`, `n_ge5`, `tiny_max`), which the pre-registration's U1 and U2 read, and those plus the ward feature `w_top` (`J8_FEATURES`), which its U3 reads (amended 2026-10-12, step 6: one eight-feature tuple reported U1 on the wrong set; the prereg's own amendment 2 states the seven); the floor under a retained ratio's log; the fewest real transitions a target may be judged by (8); the failure rule of design §3.2: an event-test tail below 0.05, or fewer than three quarters of scored targets inside the central 90% of their draws (18 of 24), cycle-driven features (`enp`, `d_enp`, `top2`, `d_turnout`) reported and not failed; a party class fails when its collapse or jump rate exceeds three times the exchangeable 1/(n+1), or its threshold-event rate exceeds the record's rule-of-three bound.

**Why.** None is forced by the record (design §5.1). They define a JUDGE, not the model: the instrument sets no parameter, and a parameter estimated from a feature removes that feature from the check (design §3.1).

**How to check it.** `tests/test_plausibility.py` (the four-part rule on constructed records; the live population 8/16/24/32; the import closure).

## Q. Added 2026-10-08 — reducing the forecast to our prediction

The forecast is the simulations; our prediction is one complete result reduced
from them, sealed and scored like a reader's (STYLE.md rule 11,
`audits/2026-10-07-prediction-restructure/BRIEF.md`). The reduction is a choice
the data does not force, so it is registered here in full. One definition,
`src/prediction.py`; its callers and guards are in MACHINERY.md ("Our
prediction") and `tests/test_prediction_rule.py`.

### §Q1 · rule A, the reduction itself — ⚖️ owner's choice (2026-10-08)

**Now.** Three steps, each over every simulation of the published run (or the
reader's weighted simulations on the page):

1. each ward is called for the party that wins it in the most simulations;
2. each party gets its mean ward-ballot vote and its mean list-ballot vote, in
   whole votes;
3. seats follow from those calls and votes by the seat law
   (`prediction.seats_of`: the statutory pool, the C and D wards out, the
   quota, item 16 under the "deduct" reading), never stored as an input.

**What it replaced.** The seat-first start of `src/start_rule.py` (retired the
same day): each named party's middle seat count over the simulations, raised
to its called wards, Others filling the council; then vote shares chosen to
give those seats. That start chose seats first and votes to fit, so its votes
were not the model's votes and its seats were not a council the law produced
from any one vote vector.

**Evidence.** MODEL-LOG §1.290: rule A and the alternative (the single
simulation nearest all the others in seats) run on every past city-year that
section lists, with data only from before each election, scored against the
real results. The
owner chose rule A on that table. The reproduction of the table by the shipped
function (`audits/2026-10-07-prediction-restructure/backtest/rule_a.py`,
compared by `compare_rule_a.py`): 23 of 24 city-years identical; Joburg 2016
differs only by an exact seat tie that §1.290 broke by hash-seed-dependent set
order (MODEL-LOG §1.291).

**What it cannot test.** Excessive seats: no past city-year in §1.290 gave
rule A a party whose called wards met its entitlement, so the item-16 path of
the reduction is unexercised by the backtest. At Johannesburg 2026 it fires
for the ANC (SPEC-A M6 is the probe's preview; the figure from the run that
publishes is in MODEL-LOG §1.291). That case is argued from the statute and
`tests/test_overhang.py`, not tested against a result.

**How to check it.** `tests/test_prediction_rule.py` (one definition, the tie,
the rounding, the missing ballot, nothing summed);
`tests/test_your_forecast_page.py` recomputes the published start from the
served draws.

### §Q2 · the ward tie rule: a seeded lot — ⚖️ statute-shaped (owner, 2026-10-09)

**Now.** A ward whose top count of simulations is shared by two or more parties
is called for the party the seeded lot draws: `seats.lot_order(tied, key)`, with
`key = seats.ward_key(lot, ward)` and `lot` the run's identity,
`seats.lot_identity(city, target, seed)`. No party name enters the key. The
codes are numbered in string order only to enumerate them; which number draws
first is the key's (a SHA-256 ticket per number). So a repeat of the run gives
the same call, a different seed can give a different one, and over many keys
each tied party is called equally often whatever its code. Schedule 1 item 8(2)
settles a real ward tie by lot; this applies the same rule to a tie in the
count of simulations. A tie with no key raises (`prediction.RuleAError`).

Owner, 2026-10-09: "item 8 is a coin flip, so flip a coin. alphabetically
favours one name above others if it happens twice."

**What it replaced.** From 2026-10-08 to 2026-10-09 a tie went to the code
first in string order (`min` over the tied codes). It was independent of array
order, so the build, the page, the scorer and the map agreed, and it favoured
codes early in the alphabet at every tie. This entry then said Schedule 1 has
no rule for a ward tie; item 8(2) is that rule (law summary D9,
`audits/2026-10-09-site-batch/law/SUMMARY.md`).

**One lot everywhere.** The run's identity reaches each caller one way:
`ModelRun.lot` inside a run; `x-seat-context["lot"]` in the schema, written
only by `worker-api/tools/make_schema.mjs` from the model artefact, which
`build_make.run_lot` fills from the served draws' `artefact_key`; the same manifest on
the page (`page._lot`); and the published seed in `forecast_summary.json` with
the configured city and target for `scenarios.summary_lot`. A baseline's lot is
`benchmarks.benchmark_lot`, the truth's carries `"actual"` in place of a seed.

| site | tie went to, before 2026-10-08 | 2026-10-08 to 2026-10-09 | now |
|---|---|---|---|
| `score_forecasts.model_forecast` (the scorer; the build's start calls it) | the earlier party in the schema roster | rule A, string order | the lot, schema's `lot` |
| `page._ward_calls` (the page's map and hand-off) | the first party in a stable sort over the draws' ward-party order | rule A, string order | the lot, manifest's identity |
| `scenarios.modal_winners` (the published claims' boxes) | the party first seen, by `Counter.most_common` | `prediction.top_party`, string order | the lot, `scenarios.summary_lot` |
| the ward call in `diagnose.main` | the first in dict order, by `max` | `prediction.top_party`, string order | the lot, `ModelRun.lot` |
| `score.score_wards` (the backtest's ward hit rate) | the first in dict order, by `max` | `prediction.top_party`, string order | the lot, the forecaster's identity |
| the published winner column written by `montecarlo.main` | an unstable sort (SPEC-A M11) | unchanged, exempt | the lot, `ModelRun.lot` (`montecarlo.published_ward_winner`) |
| the baselines' ward calls, `benchmarks.council_from_shares` | the first column of an argmax, so universe order | unchanged | the lot, `benchmarks.benchmark_lot` |

**Outside the population, stated.** Two ward calls do not go through the lot.
Inside one draw, `run_model` takes each ward's winner as the argmax of that
draw's tally, which breaks an exact float tie by universe order; the tally
carries multiplicative ward noise, so an exact tie needs two equal floats
(argued, not measured). `fold.py`'s per-ward diagnostic calls (`max` with a
key) are a printed fold diagnostic, not a forecast. Neither is changed. The JS
`allocate` in `src/interactive_template.html` is not a second seat law: its
build raises at import (`build_interactive.py`, "not ported").

**How to check it.** `tests/test_prediction_rule.py`: one constructed tied ward
through every caller above gives one party for one lot, the other party for a
different seed, and refuses with no lot; the build's lot and the page's agree
and move together with the seed. `tests/test_seats.py`: over 1,000 keys each
of two tied codes wins between 45% and 55% of the time, renamed or not. Count
the tied wards at each published run: before this change none at Johannesburg
2026's published seed and draws, and none at any panel city-year (MODEL-LOG
§1.291); the count under the lot is TO-MEASURE on the batch's re-run. A non-zero
count means the lot decided a call.

### §Q3 · whole votes by round-half-to-even of the mean — 🔴 typed

**Now.** Each party's mean votes on each ballot are rounded to a whole vote,
half to even. With unit weights the mean is computed in exact integer
arithmetic; with other weights, the weighted mean in floating point, then
rounded half to even. It moves a party by at most half a vote, which can move
a seat only at a quota remainder boundary. Half-to-even is chosen because it is
Python's own rounding and so the arithmetic `one.py` used for §1.290 (SPEC-A
M7 found the two agree for every party at the published draw count).

**How to check it.** `tests/test_prediction_rule.py::test_rule_a_whole_votes_are_the_exact_mean`
separates half-to-even from half-up on constructed halves.

### §Q4 · nothing summed, nothing dropped — ⚖️ coordinator's resolution (2026-10-08), under the owner's decision to keep every party's votes in the pool

**Now.** Every party the simulations carry enters the prediction and the seat
law's pool under its own code, zero votes included; "Others" is a display
grouping only. A party off the reader roster with a rule-A vote above zero is
refused, and the vote off the roster is recorded per ballot
(the outside_roster field of `score_forecasts.model_forecast`'s result,
zero whenever it returns). There is no OTHER party in the model: the export's `OTHER` seat
column is a sum of parties that never win a seat, zero by construction (S1
SYNTHESIS, correcting S0 finding 3).

**Why it matters.** Summing small parties before the law seats differently: on
a constructed council of ten, six minor parties each under a quota win nothing
under their own codes, and summed into one column they hold a quota and win a
seat (`tests/test_prediction_rule.py::test_no_party_is_summed_and_summing_would_seat_differently`).

### §Q5 · a party with ward candidates and no list: the counting authority's formula, not the statute's text — ⚖️ judgement (2026-10-09)

**Now.** Two terms in the seat law follow the IEC's published formula where
Schedule 1's text has no such term (law summary D1, D2,
`audits/2026-10-09-site-batch/law/SUMMARY.md`):

* **D1, the quota.** A party that contested wards and registered no list is
  left out of the pool: its votes leave A (`seats.eligible_parties`), and the
  wards it wins leave the seats the quota is struck over, as the D term beside
  independents' C (`seats.outside_pool_wards`). The IEC's Seat Calculation
  Detail prints Q = A / (B − C − D) + 1 with D "ward councillor seats from
  parties with no PR list" (quoted in `seats.py`'s module docstring). Item
  12(1) reads Q = A / (B − C) + 1, with A the valid votes for all parties and C
  the independent ward councillors, and names no D.
* **D2, the excessive-seats re-quota.** `montecarlo.allocate_with_overhang`
  re-strikes the quota over the council less the excessive party's seats, less
  C and less D, which is the IEC's Q = (A − B) / (C − (D + E + F)) + 1 as
  printed in the Laingsburg 2021 report (F, its no-list ward seats). Item 16 as
  amended reads (A − B) / (C − (D + E)) + 1 and names no F.

**Why the formula and not the text.** The counting authority applies it and
publishes it, and the published councils are what the backtest scores against.
The statute's text gives a party with no list nowhere to go: its ward seats are
seats on the council, and its votes count toward A on the text, while it can
earn no list seat.

**Evidence.** For D1's A: the IEC's published A at Johannesburg 2021 is the
combined valid votes less the independents and the two no-list parties' votes;
the arithmetic is in `seats.py`'s module docstring, where it was checked. For
D1's seat term and for D2, none: C is not zero everywhere (eThekwini 2011 and
2016 record independents; `seats.outside_pool_wards`' docstring cites the
IEC's figures), but D, a no-list party winning a ward, is zero in every
published council on disk, and F = 0 at Laingsburg. So the text and the
formula give the same council at every case on record. Argued, not tested.

**How to check it.** A Seat Calculation Detail with D > 0 (a no-list party
winning a ward) checks D1's seat term against `validate_seats.py`; one with
F > 0 in the excessive-seats block checks D2.

### §Q6 · an exact tie at the last seat: a seeded lot — ⚖️ judgement where the statute is silent (owner, 2026-10-09)

**Now.** `seats.allocate` fills the undistributed seats by the whole-vote
surplus, `votes − floor(votes / quota) × quota` (Schedule 1 item 13(2)(a)),
and an equal surplus goes to the higher vote (13(2)(b); 16(4)(c) in the
excessive-seats re-allocation). Parties equal on both that straddle the last
seat are put in the order `seats.lot_order` draws for the call's key; the seats
falling to the group go to the first of them. The statute says nothing beyond
the higher vote. The key names the run and the allocation round, never a party.
Keys are built only by `seats.seat_key`, `seats.draw_key` and `seats.ward_key`
from `seats.lot_identity`, which refuses a missing city, target or seed:

| event | key |
|---|---|
| a seat inside draw `d` of a run | `seat_key(draw_key(lot, d), round)` |
| a seat of our prediction, a reader's entry, the scorer's truth | `seat_key(lot, round)`, `lot` from the schema's `x-seat-context` (the truth: `lot_identity(city, target, "actual")`) |
| a baseline | `benchmarks.benchmark_lot` (`"benchmark:<name>"` in place of the seed), made per draw by `draw_key` for `prior-lge-noise` |
| `backtest.actual_result`, `fold.py`, `validate_seats.py` | `"actual"` in place of the seed; the fold's label with `actual` or `predicted`; `"validate"` |

`round` is 0 for the first allocation in `montecarlo.allocate_with_overhang`
and counts each real re-allocation after it. The first `deduct` or `level`
iteration allocates the same council as round 0, so it reuses round 0's
allocation rather than re-drawing it under round 1's key; otherwise an exact
tie could fall one way where the excess is measured and the other way in the
council returned (M1 diff review, S5). A call that meets such a tie with no key
raises `seats.TieWithoutLot`, a `ValueError` naming the codes.

**Two populations, two changes.** Item 2 (the whole-vote surplus) moves a
council by itself where two parties at the cut have an equal whole-vote surplus
and unequal votes: the float remainder could put the smaller party first, and
the statute gives the seat to the higher vote. The M1 diff review found
published councils in that class. Item 1 (the lot) moves only a council whose
cut falls inside a group equal on surplus AND votes. Every other council is
identical. Both counts are TO-MEASURE at the batch's run (SPEC Revision 3,
R3.1).

**What it replaced.** The ranking key was the float remainder, then the votes;
two parties equal on both kept the order they arrived in, and the model's
arrival order is a set's, so `PYTHONHASHSEED`'s. The baselines fixed it from
2026-09-13 by a name rule (`canonical_order`: most votes, then the code), which
gave every such tie to the earlier code; a reader's entry fixed it by roster
order. Owner, 2026-10-09: "alphabetically favours one name above others if it
happens twice."

**What it decides.** Johannesburg 2016's rule-A row, where two parties hold
identical rule-A votes and straddle the last seat (MODEL-LOG §1.291 has the
parties, the votes and both seat errors). Which one the lot gives, the number
of draws at Johannesburg 2026 in which an allocation meets
such a tie, and the baselines' re-measured panel totals are TO-MEASURE on this
batch's re-run (pre-registration P1, P2, P2b).

**How to check it.** `tests/test_seats.py`: the lot's answer is fixed for a key
and moves with it, over 1,000 keys each of two tied codes wins 45% to 55% of
the time whatever their names, a tie with no key refuses, an untied council
never reads the key, and an equal surplus goes to the higher vote where a float
remainder misorders it. `tests/test_stage_realisation.py`: one council over 24
orderings of a tied tally, more than one with the lot replaced by arrival order.
`tests/test_overhang.py`: Laingsburg 2021's published round-two ranking.

### §Q7 · an unopposed ward: statute in the seat law, a refusal in the draws — ⚖️ statute-shaped, with a judgement on scope (2026-10-09)

**Now.** Schedule 1 item 12(2) counts each PR vote cast in an unopposed ward for the winner's party twice for factor A, item 13(1)(b) twice for that party's entitlement, and item 16(5) (as substituted by Act 3 of 2021) twice in the excessive-seats re-quota. `seats.eligible_parties` takes those votes as `unopposed_pr` and adds them once more to the party's combined votes; the re-quota reads the same tally. `backtest.actual_result` computes them from the result file (`levels.unopposed_wards`' rule through `levels.unopposed_pr_votes`).

The draws do not model an unopposed ward: they simulate a ward ballot in every ward. `montecarlo.run_model` refuses a target with one, naming the wards. Where the population is read: from the target's result file where it exists, else from the declared slates under `[roster.wards]` in the judgement file. At Johannesburg 2026 it is the declared slates, which are the press-typed list (§L12 and the `[roster]` provenance note), not an IEC-certified one.

**The judgement.** Not modelling it in the draws. No ward in any metro LGE result file 2000-2021 has fewer than two ward-ballot parties, and no declared 2026 slate has a ward with one party (`tests/test_unopposed.py` scans both), so a draw-loop branch would have no case to score (SPEC O4, owner: "OK").

**Deviation from the specification (SPEC §1.3).** The specification counted a ward as unopposed when its result file shows exactly one ward-ballot party. An unopposed ward holds no ward ballot, so a result file would show it with PR rows and no ward rows. `levels.unopposed_in` therefore also reports such a ward, as `{ward: None}` (the file does not name the candidate); `run_model` refuses it like any other, and `unopposed_pr_votes` refuses to reconstruct a council around it until the party is named. A ward the declared slates do not mention is not reported, because a partial paste cannot say nobody stood there. The `None` case is reported on the evidence of no ward ballot, which is what an unopposed ward would leave in the file; the file itself does not say the ward was unopposed.

**Limit: independents.** `IND` counts as one party. Result files merge every independent in a voting district into one `IND` row (DATA-QUALITY item 12), and a declared slate lists them under one key, so a ward contested only by two or more independents would read as unopposed and refuse falsely. Argued, not observed: no such ward is on disk or declared.

**How to check it.** `tests/test_unopposed.py`: the scan over every metro LGE file and every declared 2026 slate (population asserted against each city's ward count), a constructed unopposed ward caught and the detector quiet on revert, the refusal, and a hand-computed council where the doubled votes move a seat.


## R. Added 2026-10-08 — a reader's prediction on both ballots, and the editor's bounds

A reader's entry is a prediction (STYLE.md rule 11; BRIEF change 13,
`audits/2026-10-07-prediction-restructure/`, slice B): a winner for every ward
and each party's whole votes on the ward ballot and on the list ballot, entry
version 2. What is VALID is the seat law's refusals only (R1: a ward winner
with no ward vote; R2: a ward winner with a PR list and no list vote;
`reader_seats`, MACHINERY.md). What the page's EDITOR lets a reader set is
narrower, and the calls below are what narrows it. The mechanism is
`build_make.editor_bounds` and `interactive/js/builder-state.js`; the values
each build produces are in the schema's `x-editor-bounds` and MODEL-LOG §1.292 and §1.294,
not here.

### §R1 · the editor's bounds are read from every metro's past local elections — ⚖️ argued

**Now.** `build_make.panel_extremes` reads every cleaned metro LGE result file
before the target (`build_make._panel`: all eight metros, every local election
on file), and takes four extremes over it: the lowest share of a ward's valid
ward-ballot votes with which a ward was won; the highest share a ward's
runner-up held; and the lowest and highest list share minus ward share, in
points of each ballot's citywide total, over every party that stood on both
ballots in a city-year (the merged `INDEPENDENT` row, which stands on no list,
falls out by that test).

**Alternatives.** The city's own elections only: five city-years for
Johannesburg, too few to say what a ward result can look like; the shapes are a
property of the electoral system and its parties, which every metro shares. A
percentile instead of the extreme: the 1st percentile of winning shares would
put 1% of real winners outside the editor (SPEC-B's probe; MODEL-LOG §1.292).

**Limit.** The result files merge every independent in a voting district into
one `INDEPENDENT` row (DATA-QUALITY.md item 12), so a ward where several
independents stood records one share larger than any one candidate's. Where
that row is the runner-up it can raise `q_run` (widening the editor); where it
wins it raises the recorded winning share, so it can raise `q_win` and narrow
the editor. How often the row is present, wins, and whether it sets a bound today:
MODEL-LOG §1.293.

**How to check it.** `tests/test_your_forecast_page.py::test_the_editor_bounds_are_regenerated_from_the_panel`:
the panel is the glob, both ways, each file's sha256 recorded; a constructed
file with a lower winning share moves `q_win` to it, one with a wider gap moves
`gap_max`.

### §R2 · `EDITOR_WIDEN_PP` = 5.0 points beyond the extremes, the runner-up's bound capped at `RUNNER_UP_MAX` = 0.5 — ⚖️ owner's call (2026-10-08)

**Now.** Each of the four extremes of §R1 is widened by 5.0 percentage points
of its ballot: the lowest winning share less 5 points (`q_win`), the highest
runner-up share plus 5 points (`q_run`), the lowest list-minus-ward gap less 5
points (`gap_min`), the highest plus 5 points (`gap_max`). `q_run` is then
capped at 0.5 of the ward's vote: a runner-up holding more than half would be
the winner. The owner's words: "the historical extremes, widened by 5 points
either side"; "highest runner-up 50%: 52.8% capped, because a runner-up cannot
exceed half" (s1/SYNTHESIS.md, owner's answers, 4).

**Since 2026-10-09 (slice B2a, §R9 and §R14)** the widening of each bound is
the mean of its quantity's record events where it has at least
`MIN_RECORD_EVENTS` of them, and `EDITOR_WIDEN_PP` only where it has fewer.
Which rule each of the four takes at a build is written beside it in the
schema's `x-editor-bounds` (`shape.allowance`, each with its `rule` and
`events`); the cap at `RUNNER_UP_MAX` is unchanged.

**What it decides.** How far a reader may take a party past anything a metro
has produced. Unwidened, the editor would say no ward was ever won lower than
the lowest win on record, which is a record, not a law. The widening is
uniform in points: a gap of 5 points binds a large party long before a small
one (SPEC-B open question 5), which is accepted.

**Alternatives, not taken.** The extremes unwidened (the coordinator's
recommendation, s1/SYNTHESIS.md item 4); a percentile (§R1).

**How to check it.** The same test: the effective bounds equal the extremes
widened by `EDITOR_WIDEN_PP`, `q_run` capped at `RUNNER_UP_MAX`.

### §R3 · a ward's expected ward vote: the 2026 roll times the preceding local election's turnout in its voting districts — 🟡 argued

**Now.** `build_make.expected_ward_shares`: each ward's roll on the newest
registration snapshot (`inputs_preflight.roll_snapshot`, the file
`--strict` checks) times its expected turnout, the registration-weighted mean,
over the ward's voting-district parts (`montecarlo.ward_parts`, split VDs
apportioned), of each part's VD's ward-ballot turnout at the preceding local
election (valid ward votes over registered). A part whose VD has no record
there is left out of its ward's mean, and the count is recorded beside the
bounds (`expected_ward_vote.parts_left_out`). Its only use is the editor's
bounds: `e[w]`, a ward's share of the city's expected ward vote, weights the
wards a party is called for.

**Alternatives.** Every ward equal: wrong by a factor the probe measured
(MODEL-LOG §1.292, the range of `e`). The model's own turnout per draw: it is
a forecast quantity, and the bounds should not move with a model run.

**Limit.** Turnout differences between wards are taken as they were at the
preceding local election.

### §R4 · the bounds limit the editor, never validity — ⚖️ argued (SPEC-B D4)

**Now.** No validator, decoder or seat call reads `x-editor-bounds`. A state
from a link, a hand-off, a friend's prediction or our own may lie outside
them: it opens as it is, the page names the party (`builder-state.js`
`outOfBounds`), and each out-of-bounds value is clamped when it is next edited: a ward vote outside its range by the next change to any ward vote or ward call (the others are rescaled inside their ranges), a list vote outside its gap range only when that party's list vote is next set.
`start.out_of_bounds` in `forecast.json` records whether our own prediction is
outside them.

**Why.** The bounds are regenerated with the data; enforcing them on decode
would invalidate sealed links and our own encoded prediction whenever a result
file or the roll changed.

### §R5 · the bound on a party's ward vote treats each ward alone — ⚪ superseded 2026-10-09

**Was (slice B, 2026-10-08 to 2026-10-09).** For the wards on the map, with
the expected-vote share of the wards called for party P summed: its ward vote
at least `q_win` times that sum (and one vote if it wins a ward), and at most
that sum plus `q_run` times the rest. Each ward treated as won on at least
`q_win` of its expected vote and as giving any other party at most `q_run`,
whatever that ward's own history (`builder-state.js` `wonE`, `wardBounds`,
deleted).

**Is.** §R6-§R10 and §R12-§R14: ward-by-ward ranges from each ward's own
history, the per-party box they allow on the painted map, and a citywide limit.

**Decision.** The owner's, 2026-10-09 (PACKET.md of
`audits/2026-10-07-prediction-restructure/s1b/`): "1 ward by ward is certainly
preferred". The screenshot that prompted it (PACKET.md, "Why") held a party
painted to win most wards at a small share of the ward vote, inside this
bound. MODEL-LOG §1.294.

### §R6 · a party's range in a ward: its share there at the preceding local election, moved by the swings of consecutive local elections in every metro, of parties standing both times — ⚖️ argued

**Now.** `build_make.ward_priors` joins the preceding local election's VD votes
onto the target's wards through `montecarlo.ward_parts` (a split VD's votes
apportioned by `part_registered`). `build_make.swing_panel` reads every metro's
consecutive local pairs (a, b), a the calendar's local election before b, b
before the target, each b's wards taking a's VD votes through b's own VDs
(`build_make._held_parts`, `ward_parts`' held-election rule). Over the (ward,
party) swings where the party stood both times (a share at a and at b), the
merged `IND` row left out (DATA-QUALITY item 12), `build_make.swing_extremes`
takes the least and greatest swing per `SWING_BINS` bin of the starting share.
A party's range in a ward is its prior plus its bin's least and greatest swing,
widened by the ward allowance (§R9) and kept in [0, 1]
(`build_make.ward_ranges`, served as `ward_ranges`). Every real swing is kept in
the extremes; the exclusions of §R13 act on the allowance only.

**Alternatives.** Swings not conditioned on standing both times: candidacy
lapses then set the extremes (a party that stood in a ward and then did not
reads as a fall to zero), SPEC-B2 §2. The city's own transitions only: four
pairs, too few per bin. Percentiles instead of extremes: they make real 2026
(ward, party) pairs unpaintable and exclude real past results (SPEC-B2 §11 O1;
the owner chose extremes).

**Limit.** The join is by VD number; a number reused for another place cannot
be seen (SPEC-B2 §10). A party's candidacy in a ward is not known before the
IEC lists are read, so a party that will not stand still gets a range there.

**How to check it.** `tests/test_your_forecast_page.py::test_the_ward_ranges_are_regenerated_from_the_panel`:
the pairs and the cells recomputed from the files, both ways; a VD's votes
raised moves exactly its wards; a swing pushed past its bin moves that bin
alone.

### §R7 · `SWING_BINS` = (0.01, 0.05, 0.15, 0.35, 0.60) — 🔴 typed

**Now.** The interior edges of the starting-share bins a swing is grouped by,
as shares of a ward's (or a city's) ward-ballot votes: bin i holds starting
shares in (edge i-1, edge i], the first from zero. Seven edges, six bins, used
for ward swings, citywide swings and the national-to-local changes alike.

**Why it matters.** The spread of swings grows with the share a party starts
from (SPEC-B2 §2's table), so one pair of extremes for every party would give
a party at 1% the swings of a party at 60%.

**Alternatives.** Other edges; a continuous rule (swing extremes as a
function of the starting share). Neither was measured.

**How to check it.** The same test: a swing pushed past its bin's greatest
moves that bin's extreme and no other.

### §R8 · a party with no ward record: its citywide share; new to local elections: its national share; neither: the newcomer caps — ⚖️ argued (O2: owner's call)

**Now.**
- A party with no vote in a ward at the preceding local election, but a vote
  elsewhere in the city, takes its citywide share there as the prior, by the
  rule of §R6 (`party_ranges`, kind `local`).
- A party with no ward vote anywhere in the city at the preceding local
  election but a vote at the preceding national election
  (`Target.previous_npe`; `build_make.npe_priors`) takes its national share in
  the ward, joined the same way, or its citywide national share where it has
  none in the ward (kind `national`). Its range is moved by the least and
  greatest change from a national election to the next local election, per
  bin, over every metro's pairs (n, l) before the target, the party on both;
  a party's collapse at the local election (from at least `COLLAPSE_FROM` of
  the national vote to under `COLLAPSE_KEEP` of that) is left out of those
  extremes. The same rule on citywide shares gives its citywide limit (§R12).
- A party with neither (kind `newcomer`) ranges from zero to the greatest
  ward share taken by any party new to its city with no vote at the national
  election before, plus the ward allowance; its citywide limit, from zero to
  the greatest such citywide share plus the city allowance. Both caps, and
  where each was set, are served under `swing.newcomer`.
- A national file whose calendar template names an approximation
  (`APPROXIMATE`; the 1999 footprint) is never a prior and never a pair.

**Evidence.** The owner's O2 (2026-10-09): "new parties... 2024 result plus
usual party vote deterioration if one exists". The designer measured the
deterioration for parties new to local elections (SPEC-B2r2 §3): none beyond
COPE's collapse, so no centring adjustment moves a bound; it is recorded, not
applied.

**Limit.** A COPE-type collapse at a party's first local election falls
outside its national-prior range: that is the measured cost of O2 (SPEC-B2r2
§7, §8.4).

**How to check it.** The same test: each `party_ranges` entry is of the kind
its party's history says, recomputed from the files; a party deleted from the
preceding local file takes its national prior, and deleted from the national
file too becomes a newcomer.

### §R9 · the allowance is the mean of the pooled record exceedances — ⚖️ owner's call (O1), measured

**Now.** `build_make.record_events` takes rounds in order (the later election
of each local pair; every metro of one election in one round). The first
round in which a key appears sets its record in each direction; a later
round whose greatest (least) swing beats it is an event of size new record
minus old. `build_make.allowances` keys the records by bin, pooled over every
party and metro (the quantity the bins' extremes are made of), for ward swings
and for citywide swings, after §R13's exclusions; each allowance is the mean of
its events (`allowance.ward`, `allowance.city`, each served with its events).
With fewer than `MIN_RECORD_EVENTS` events, `EDITOR_WIDEN_PP` (§R14).

**Evidence.** The owner's O1 (2026-10-09): "when a party moved up or down more
than it ever had previously, what was the delta of that new swing? Leave out
mergers splits and collapse (cope) then average it out". The designer's
leave-one-election-out check (SPEC-B2r2 §1) against the flat 5 points and the
alternatives (median, party-own records, the max).

**Limit.** Few events, and they do not shrink from round to round; one event
moves the ward mean appreciably (SPEC-B2r2 §8.1). The values and their
events at each build are in `x-editor-bounds`, not here.

**How to check it.** `tests/test_your_forecast_page.py::test_the_allowance_is_the_mean_of_record_events`.

### §R10 · the per-ward shape inside each ward's ranges, and the shape alone where they cannot hold the painted winner — ⚖️ argued

**Now.** In a ward painted for W, W's share is at least `q_win` and every other
party's at most `q_run`, on top of each party's range. The least and greatest
share each party can hold there, with the shares summing to one and W at
least each other party, are taken in closed form (`builder-state.js`
`wardRange`, SPEC-B2 §3). A ward where no share vector satisfies them uses the
shape alone (W in [`q_win`, 1], the others in [0, `q_run`]), and the page names
the ward and party. The per-party BOX is those least and greatest shares
summed over the wards, each weighted by its share of the expected ward vote
(§R3).

**Alternatives.** Refusing the paint (readers hand-pick every ward); the bare
ranges with no shape, which lower the largest party's floor on rule A's map
far below what the shape gives it (SPEC-B2 §2).

**How to check it.** `interactive/tests/builder.test.mjs`: "the ward range is
the set's projection" (against vertex enumeration on random wards, and a
closed form without the winner condition caught); "a painted ward no past
result fits uses the shape alone, and is named".

§R11 is reserved for slice B2b (the witness editor, which needs scipy).

### §R12 · each party's citywide limit on its ward vote — ⚖️ owner's call (O4)

**Now.** `build_make.city_limits`, by the party's kind
(`build_make.party_kind`, the same rule as its ward ranges, §R8): a party's share of the preceding local
election's ward vote on the target's wards, weighted by each ward's expected
ward vote, moved by the least and greatest citywide swing of its bin
(citywide stood-both swings over the same pairs), widened by the city
allowance (§R9); a party new to local elections by its national share and the
national-to-local citywide changes (§R8); a party with neither, the newcomer
cap. The editor keeps each party's ward vote inside the box (§R10) intersected
with this limit (`builder-state.js` `limits`). Where they do not meet, the map
wins: the party is held to its box, and the page says its wards need more (or
leave it less) of the vote than past elections give it. Where the floors sum
past the whole ballot, or the ceilings fall short of it, the citywide parts are
eased in proportion until they fit.

**The weights of the citywide swings.** Each ward of a past local election
is weighted by its roll times the earlier election's turnout in its VDs
(`build_make._turnout_parts`, the definition `expected_ward_shares` uses). A
ward none of whose VDs was recorded at the earlier election takes the mean
turnout of the election's other wards, where the target's own build refuses:
a past record cannot be repaired, and leaving the ward out would drop its
votes from the citywide share. Each such ward is listed at each build in
`x-editor-bounds` (`mean_turnout_wards`, with `panel_wards` as the
denominator); the count is in MODEL-LOG §1.294. ⚖️ argued.

**Evidence.** The designer's walks on rule A's map (SPEC-B2 §0 and §3,
SPEC-B2r2 §5): the per-party box alone left most far-move states with no
ward-vote matrix behind them, and with the citywide limit none were. With
repainting, B2a leaves a joint gap that B2b closes (SPEC-B2r2 §5).

**How to check it.** `interactive/tests/builder.test.mjs`: "the limits are the
box inside the citywide limit, and the map wins where they do not meet";
"floors that sum past the ballot, or ceilings short of it, are eased until the
votes fit"; the random walk, every state inside the limits.

### §R13 · the exclusions of the record events — 🔴 typed

**Now.** `build_make.exclusions`, per metro and local pair (a → b), on the
city's ward-vote shares:
- **merger**: a party holding at least `VANISH_MIN` = 0.01 at a and standing
  nowhere at b (no ward or list vote); its absorber, the party standing at both
  whose ward swings correlate best with the vanished party's ward shares at a,
  if the correlation is at least `CORRELATION_MIN` = 0.5. The absorber's swings
  at b are left out. Below it, a dissolution, recorded, excluding nothing.
- **split**: a party new to the city with at least `SPLIT_MIN` = 0.05 at b; its
  source, the party whose ward swings correlate most negatively with the
  newcomer's ward shares, if at or below minus `CORRELATION_MIN`. The source's
  swings are left out. Otherwise a new party, recorded.
- **collapse**: a party falling from at least `COLLAPSE_FROM` = 0.02 to under
  `COLLAPSE_KEEP` = 0.25 of that share; its own swings are left out.

Exclusions act on the record events only; the bounds keep every real swing.
Each detected case, with its partner and correlation, is served under
`exclusions`.

**Known misfires.** The detector names two splits that did not happen: the EFF
"from the VF+" in Mangaung 2016 and COPE "from the DA" in Nelson Mandela Bay
2011 (COPE came from the ANC). It calls the NFP's failure to register in
eThekwini 2016 a merger into the IFP. The choice of exclusion rule moved the
allowance little in the designer's measurement (SPEC-B2r2 §1).

**How to check it.** `tests/test_your_forecast_page.py::test_the_allowance_is_the_mean_of_record_events`:
a constructed vanished party correlated with one party's swings is a merger,
and that party's event is gone.

### §R14 · `MIN_RECORD_EVENTS` = 2: below it a widening stays `EDITOR_WIDEN_PP` — 🔴 typed (coordinator's D1)

**Now.** A widening (the ward and city allowances of §R9, and each shape
quantity's of §R2) is the mean of its record events where there are at least
two, and `EDITOR_WIDEN_PP` where there are fewer
(`build_make._allowance`, `build_make.shape_allowances`).

**Why.** One event is not a mean. Measuring everywhere would set `gap_min`
from one event and put our own prediction outside on the PA's gap (rule A has
the PA's list share far below its ward share, MODEL-LOG §1.293), which the
model investigation is treating as a likely defect of the model's draws. The
coordinator's D1 (PACKET.md, 2026-10-09), to be revisited once that is
settled; the owner can overrule.

**How to check it.** The allowance test: a shape quantity with one event
keeps `EDITOR_WIDEN_PP`, and a second event makes it their mean.

## S. Added 2026-10-10 — the share images (OG-IMPLEMENTATION-SPEC.md, audits/2026-10-09-site-batch/)

### §S1 · The forecast image's four coalitions — ⚖️ owner's choice (2026-10-10)

**Where.** `og_pages.FORECAST_COALITIONS`, the one definition of each set's
parties; its label and its figure (`coal.<key>.majority`, the share of
simulations in which the set holds a majority) are both written from it.

**Now.** Four sets, as the image labels them:

| set | parties |
|---|---|
| ANC + DA | ANC; DA |
| DA, ActionSA, PA + IFP, VF+, ACDP | DA, ASA, PA; IFP, VFPLUS, ACDP |
| ANC, EFF, PA + Al Jama-ah | ANC, EFF, PA; ALJAMAAH |
| ANC + EFF + MK Party | ANC; EFF; MK |

A set /forecast's coalition table prints takes the page's figure; a set the
table does not list is computed over every party's seats
(`stats.coalition_majority`) and recorded in the publication ledger under
/forecast as a generated token.

**Why.** The owner's choice on the mock-up (`og-design/make_og.mjs`,
6cc87fb): "looks good". These are the coalitions in the news, not a ranking:
nothing in the model chose them, and the image shows nothing about sets left
out. Whether /forecast's coalition table uses the same list is the owner's to
confirm.

**How to check it.** `tests/test_og_pages.py` holds the image's figure fields
to this list and each figure to the string a page printed. Nothing in the
model reads it.

### §S2 · `SMALL_PARTY_SHARE` = 0.01 and `SMALL_PARTY_SURGE` = 0.05: the small-party note's test — ⚖️ the record's own thresholds (2026-10-10)

**Where.** `stats.small_party_surge`, read by the token `small_party_surge`
(source `published:small_party_surge`) and printed, with both thresholds as
tokens, in the small-party note on /methodology ("What this does not cover").

**Now.** The share of the published simulations in which at least one
established party (one that stood at the preceding local election) whose mean
list share over the simulations is under 1% takes more than 5% of the list
vote.

**Why these.** They are the thresholds of the record test the note sets the
simulations against: MODEL-LOG §1.296 counted the cases of a party under 1%
of the list vote at one local election in the eight metros, 2006 to 2021, and
found none that reached 5% at the next. The same two lines on both sides
compare like with like. They describe the model; nothing in it reads them.

**How to check it.** `tests/test_stat_sources.py` holds the measure on
constructed draws and the registered source to a direct computation on the
published draws.

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
