# Which judgement calls reach /methodology, and why

Owner, 2026-10-02: "where are judgement calls in plain English? Those should be
methodology." and "omit all judgement calls that aren't an opinion on
machinery. There are many that literally nobody would get at all."

**The test applied.** A call is kept when it is a substantive opinion about how
the model works, live in the published 2026 Johannesburg forecast, that a lay
reader can follow without the code and might disagree with. Dropped: thresholds,
guards, numerical floors and solver budgets; data cleaning; reporting and page
design; anything superseded, deleted, refused or certified inert at 2026; and
anything that needs the code to explain. Where a call has two entries (§A and
§F), the field sits on one and the other is listed as its duplicate.

**What a kept call carries.** A *Plain* field in its register entry, directly
under the heading: what was chosen, why, what the alternative changes, and
whether /play/ can move it. `src/judgement_sheet.py` writes the /methodology
section "The judgement calls" from those fields, in register order; the site
build refreshes it and `tests/test_judgement_sheet.py` checks it both ways.

**Counts.** 163 § entries in `JUDGEMENT-CALLS.md`: 10 kept (in nine Plain fields; §A33 shares §A35's),
153 dropped. One table row has no § entry of its own (the
independent-ward count, citing MODEL-LOG §1.166): dropped, a structural
limitation of the seat count rather than an opinion a reader can weigh.

Liveness at 2026 was read from `JUDGEMENT-SHEET.md` and, for breakaway sizing,
from the emitted 2026 spec's seed notes (no 2026 seed is sized as a breakaway).

| entry | call (register heading) | verdict | reason |
|---|---|---|---|
| §A1 | three constants carry an n the new archive has changed, and none is re-measured — TURNO... | dropped | a note that three constants are not re-measured; internal bookkeeping |
| §A2 | the θ record pools a collapse, a split and a merger as if they were retention — the 200... | dropped | an open defect in the record awaiting a decision, not a choice the forecast makes on purpose |
| §A3 | entrant_prob — 0.25 — 🟡 | dropped | the generic newcomer is certified inert at 2026 (named arrivals replace it) |
| §A4 | nothing retires the generic entrant when the ballot becomes known — entrant_prob stays ... | dropped | closed by the certified roster; nothing left to choose |
| §A5 | contestation_expand — 0.220 — 🔴 | dropped | certified inert at 2026 |
| §A6 | arrival_group_draw — False — 🟢 | dropped | a switched-off alternative mechanism; needs the arrival machinery to explain |
| §A7 | the published 2026 forecast is not the configuration the backtest scores — 🔴 | dropped | a disclosure about the backtest configuration, not a choice about how the model works |
| §A8 | poll_paths — **"off"** — 🟢 | KEPT | kept as "No poll is used" |
| §A9 | σ_poll, decomposed — POLL_HOUSE_SD 0.025 · POLL_CAL_N_2016 800 · POLL_CAL_DEFF_2016 1.3... | dropped | poll error parts; inert while polls are off, and covered by the polls paragraph |
| §A10 | poll_deff_subsample (module defaults POLL_DEFF_SUBSAMPLE, POLL_DEFF_STANDALONE) — 1.6 (... | dropped | poll sub-setting; inert while polls are off |
| §A11 | poll_credence — 1.0 — 🔴 | dropped | poll sub-setting; inert while polls are off |
| §A12 | poll_house_k (module default POLL_HOUSE_K) — 1.0 — 🔴 | dropped | poll sub-setting; inert while polls are off |
| §A13 | poll_screen_sd, poll_drift_per_root_day, POLL_MIN_N (module defaults POLL_SCREEN_SD_UND... | dropped | poll sub-settings; inert while polls are off |
| §A14 | poll_half_life_days — 120.0 — 🔴 | dropped | poll ageing; inert while polls are off |
| §A15 | the derivedness budget (governance, not a code lever — it deliberately has no symbol in... | dropped | governance budget, no symbol in the model |
| §A16 | poll_min_n — 300 — 🔴 | dropped | poll sample-size threshold; inert while polls are off |
| §A17 | entrant_share — [0.01, 0.04, 0.12] — 🟡 | dropped | generic newcomer size; inert at 2026 |
| §A18 | LEVEL_DF — 7.0 — 🟡 | KEPT | kept as "Large surprises are allowed" |
| §A19 | how unplaced votes are spread over a party's zeroed pool cells — pool-size proportional... | dropped | a fitting detail that needs the pool solve to explain |
| §A20 | the §3.5 θ sanity ranges are violated by most of the forecast, and nothing acts on it — 🔴 | dropped | an unacted diagnostic, not a choice |
| §A21 | the width statistic the report quotes — probit-SD, sd(Φ⁻¹(u)) — 🟡 | dropped | a reporting statistic |
| §A22 | doc-vs-artefact tolerances — n exact · mean PIT ±0.012 · coverage ±2pp · vote bands ±0.... | dropped | document tolerance, plumbing |
| §A23 | level_shrink = 0.35 (with level_shrink_scale = 0.04) — 0.35 — 🟡 | KEPT | kept as "The largest parties are pulled down" |
| §A24 | SHRINK = 2.0 — 2.0 — 🟢 | dropped | measured optimal, not an opinion; needs the record-weighting to explain |
| §A25 | the blend weight ignores the ρ record's evidence — w = k/(worth_θ + k) — 🟢 | dropped | a form choice inside the level blend; needs the code to explain |
| §A26 | theta_prior and _shrunk are different estimators of the same quantity — RESOLVED 2026-0... | dropped | resolved |
| §A27 | the capacity redistribution rule — proportional to mass held — 🔴 | dropped | a capacity redistribution rule inside the pool solve; needs the code |
| §A28 | POOL_CAPACITY_MARGIN — 0.98 — 🔴 | dropped | a guard margin |
| §A29 | level_sd_default — 0.45 — 🟡 | dropped | measured inert at 2026 |
| §A30 | Dirichlet floor — 1e-4 — 🟢 | dropped | numerical floor |
| §A31 | _LOG_FLOOR — 1e-6 — 🟡 | dropped | numerical floor, unexercised |
| §A32 | turnout spread with one observation — 0.30 logits — 🟡 | dropped | fallback for a missing measurement |
| §A33 | bye_weight_mode — "fixed" — 🟡 | KEPT | carried inside §A35's field "How much recent by-elections count" (merged 2026-10-02: the weight and the per-party alternative read as one call, and the page describes the by-election blend only there) |
| §A34 | turnout-adjusted by-election weighting — ⚫ refused | dropped | refused, never shipped |
| §A35 | w_bye — 0.40 — 🔴 | KEPT | kept as "How much recent by-elections count" |
| §A36 | ward→PR conversion of the by-election delta — ratio, clipped [0.5, 2.0], above pc > 0.0... | dropped | conversion detail inside the by-election channel |
| §A37 | w_bye_local_ward / w_bye_local_pr — 0.0 / 0.0 — 🟡 | dropped | built and disabled at zero |
| §A38 | ward_noise_sd — 0.10 — 🟡 | dropped | ward-level noise and a standing refusal; needs scoring rules to explain |
| §A39 | OVERHANG_DEDUCT_MAX_ROUNDS_SLACK — 2 — 🟢 | dropped | loop bound in the seat allocator |
| §A40 | OVERHANG_LEVEL_MAX_ROUNDS — 200 — 🟡 | dropped | loop bound in the seat allocator |
| §A41 | turnout_pattern_blend / turnout_blend_jitter / turnout_noise_sd — 0.5 / 0.25 / 0.08 — 🟡 | dropped | per-district turnout jitter; tiny citywide effect, needs the code |
| §A42 | the arrival boundary — "no baseline at all" — 🔴 | dropped | an unmade decision about where arrivals start; nobody has chosen |
| §A43 | apply_city never resets DEFAULTS — 🔴 | dropped | a fixed code defect |
| §A44 | MIN_HOME_SPLITS + binary home/away — 2 — 🔴 | dropped | breakaway home/away buckets; no party on the 2026 Johannesburg ballot is sized by them |
| §A45 | the arrival-group mechanism's five typed constants — reach floor 0.02 · total_log_sd fa... | dropped | thresholds and fallbacks inside the arrival mechanism |
| §A46 | the peer window that sizes every seeded arrival — ±0.25 of ward reach, minimum 8 compar... | dropped | a comparator window inside arrival sizing; needs the code |
| §A47 | which city is a splinter's home, and which pair of elections it is measured across — SP... | dropped | breakaway home-city assignments; no party on the 2026 Johannesburg ballot is sized by them |
| §B1 | SPINE_K = 1.0, reciprocal form — 🔴 | dropped | blend-weight form; needs the record-weighting to explain |
| §B2 | Vote-weighted RMSE as the criterion — 🔴 | dropped | an evaluation criterion, not how the model works |
| §B3 | SPLIT_SD_FLOOR = 0.90 — 🔴 | dropped | spread floor; binds at neither 2021 nor 2026 |
| §B4 | TURNOUT_CORRELATION = 0.63 — 🟡 | KEPT | kept as "Turnout moves together across population groups" |
| §B5 | Gaussian copula for pool turnout — 🟡 | dropped | copula form; statistical plumbing behind the turnout link |
| §B6 | METRO_CODES widened 2 → 8 — 🟡 | dropped | which metros the record is read from; confounded and needs the code to explain |
| §B7 | alpha per pool — 🟡 | dropped | fitted from history, not chosen; needs the pool distribution to explain |
| §C1 | Σ base·θ = 1 in the IPF — 🟢 | dropped | forced by arithmetic |
| §C2 | Splinter fraction capped at 1.0 of parent — 🟢 | dropped | forced by arithmetic |
| §C3 | Turnout band in logit space — 🟢 | dropped | forced scale choice |
| §C4 | LEVEL_FLOOR = 1e-6 vs SHARE_FLOOR = 0.002 — 🟢 | dropped | numerical floors |
| §C5 | LOG_CHI2_BIAS = 1.887365 — 🟢 | dropped | a derived constant deliberately not applied; technical |
| §D1 | ENTRANT relabelling | dropped | reporting |
| §D2 | Mean vs median as the point forecast | dropped | reporting (both are shown) |
| §D3 | "ruled out" threshold | dropped | reporting threshold |
| §D4 | anomaly thresholds | dropped | reporting thresholds |
| §D5 | signed-only rank bands | dropped | reporting, retired |
| §D6 | phantom mass reported nowhere | dropped | reporting |
| §D7 | which columns test calibration | dropped | reporting |
| §D8 | what puts a party in the reference population — REFERENCE_SHARE = 0.0025 · REFERENCE_SL... | dropped | reporting population threshold |
| §D9 | BLEND_W — 1.0 — 🟢 | dropped | a scoring baseline setting |
| §D10 | pooled AND per rank band, not pooled alone | dropped | reporting |
| §D11 | the pooled figure must NOT be read alone — 🟡 | dropped | reporting rule |
| §D12 | PIT seed derived per city-year | dropped | reproducibility seed |
| §D13 | top = 12 parties per table | dropped | table length |
| §D14 | seat error summed over all parties | dropped | reporting |
| §D15 | modal ward winner = "the model's call" | dropped | reporting reading of a forecast, not machinery |
| §D16 | FRESHNESS_GRACE_S = 300s — 🟡 | dropped | publishing guard |
| §D17 | CELL_AREA_FACTOR = 1.0 — 🟡 | dropped | map drawing |
| §D18 | GRID_MARGIN_CELLS = 2 — 🟢 | dropped | map drawing |
| §D19 | SAFE / STRONG / LEAN = 0.90 / 0.75 / 0.60 — 🟢 | dropped | map colour tiers |
| §D20 | TIP_FLOOR = 0.05 · OTHER_FLOOR = 0.005 — 🟢 | dropped | map label floors |
| §D21 | MAX_DISPLACEMENT_RADII = 5.0 — 🟡 | dropped | map regression guard |
| §D23 | WALL_FLIPS = 30 — ⚖️ argued, and it names a scenario rather than measuring one | dropped | a named scenario on a page, not a model setting |
| §D22 | min_clusters — 8 — 🔴 | dropped | test threshold; moves no forecast |
| §F1 | DIRICHLET_FLOOR — 1e-4 — 🟢 | dropped | numerical floor |
| §F2 | POLL_RMS_ERROR — 0.030 — ⚫ deleted | dropped | deleted |
| §F3 | POLL_HALF_LIFE_DAYS — 120 — 🔴 | dropped | duplicate of §A14; inert while polls are off |
| §F4 | CAMPAIGN_WINDOW_DAYS — 550 — 🟡 | dropped | poll window; inert while polls are off |
| §F5 | POLL_K — ⚪ | dropped | deleted |
| §F6 | SPLINTER_PARENT_WEIGHT — 0.35 — 🔴 | dropped | breakaway sizing share; no party on the 2026 Johannesburg ballot is sized by it |
| §F7 | _SIGN_EPS — 1e-9 — 🟡 | dropped | numerical tolerance |
| §F8 | LEVEL_DF — 7.0 — 🟡 | dropped | duplicate of §A18, which carries the field |
| §F9 | POOL_CAPACITY_MARGIN — 0.98 — 🔴 | dropped | duplicate of §A28; guard margin |
| §F10 | balance_margins iters / tol — 2000 / 1e-12 — 🟡 | dropped | solver budget |
| §F11 | SOLVE_TOL — 1e-9 — 🟢 | dropped | solver tolerance |
| §F12 | PARTIAL_BALANCE_PASSES — 200 — 🟡 | dropped | solver budget |
| §F13 | TURNOUT_CORRELATION — 0.63 — 🟡 | dropped | duplicate of §B4, which carries the field |
| §F14 | SPINE_K — 1.0 — 🔴 | dropped | duplicate of §B1 |
| §F15 | SHRINK — 2.0 — 🟢 | dropped | duplicate of §A24 |
| §F16 | RELIABILITY_HALF — 0.002 — 🟡 | dropped | smoothing constant |
| §F17 | SD_FLOOR, SD_CEILING — 0.15, 1.20 — 🟡 (≥15%) | dropped | spread bounds; needs the code |
| §F18 | the size-dependence of sd_for is wrong below 15% of the vote — a straight line in log(s... | dropped | a known defect in a functional form, not a choice |
| §F19 | level_floor — 1e-6 — 🟢 | dropped | numerical floor |
| §F20 | level_shrink, level_shrink_scale — 0.35, 0.04 — 🟡 | dropped | duplicate of §A23, which carries the field |
| §F21 | dirichlet_floor, poll_k, spine_k — 🟢 | dropped | sweep keys |
| §F22 | spine_k = 0 on a party with no θ evidence — w_local = 0.0 — 🟡 | dropped | limiting case reachable only by a sweep |
| §F23 | turnout_noise_sd, turnout_blend_jitter — 0.08, 0.25 — 🟡 | dropped | duplicate of §A41 |
| §F24 | bye_local_cap, bye_tau_months — 1.5, 18 — 🔴 | dropped | inert in every run |
| §F25 | w_bye_local_ward, w_bye_local_pr — 0.0, 0.0 — 🟡 | dropped | built and disabled |
| §F26 | polling_lean, polling_span — ⚪ | dropped | deleted |
| §F27 | pa_contestation_uplift — DELETED 2026-08-18 — ⚪ | dropped | deleted |
| §F28 | MAX_SIGMA, MIN_SIGMA, NEW_PARTY_SIGMA — 2.0, 0.15, 1.0 — 🟡 | dropped | a baseline's settings, not the model's |
| §F29 | MIN_SHARE, CLAIM_FRACTION, F_OTHER — 0.005, 0.50, 1.30 — 🟡 | dropped | mixed small thresholds |
| §F30 | poll_id, poll_weight, poll_k — ⚪ | dropped | deleted |
| §F31 | ALPHA_MIN_SHARE, ALPHA_FLOOR, ALPHA_CEILING, ALPHA_FALLBACK — 0.01, 1.0, 200.0, 12.0 — 🔴 | dropped | selection thresholds inside the pool distribution |
| §F32 | ARRIVAL_BAND_LO, ARRIVAL_BAND_HI — 0.25, 0.95 — 🔴 | dropped | arrival band shape; needs the code |
| §F33 | BYE_MIN_WEIGHT — 30.0 — 🔴 | dropped | admission threshold |
| §F34 | TURNOUT_DRAW_FLOOR, TURNOUT_DRAW_CEILING — 0.02, 0.95 — 🔴 | dropped | per-draw turnout clamps |
| §F35 | WARD_PR_RATIO_MIN, WARD_PR_RATIO_MAX — 0.5, 2.0 — 🔴 | dropped | a clip on a ratio |
| §F36 | PROJECTED_METRO_SHARE — eight per-metro shares of the national vote, 2021 values — 🔴 | dropped | fallback input fired only where no backtest checks it; plumbing |
| §F37 | PAGE_SIZE — 🟢 | dropped | pagination |
| §F38 | REG_DRIFT_TOLERANCE — 0.30 — 🔴 | dropped | a data-cleaning tolerance |
| §H1 | overhang_rule — "deduct" — ⚖️ STATUTE, NOT A JUDGEMENT CALL | KEPT | kept as "The excessive-seats clause" |
| §H2 | w_recency — 0.70 — 🔴 | KEPT | kept as "Expected turnout leans on 2021" |
| §H3 | kappa_bye — 0.25 — 🔴 | dropped | turnout-model sub-setting; needs the turnout model to explain |
| §H4 | w_split — 0.6 — 🔴 | dropped | down-weight for unstable districts; data cleaning |
| §H5 | PLAN_BOUNDS — 7 party ranges — 🔴 | dropped | clamp ranges that read on no panel row |
| §H6 | GAMMA_FOLD — {2026:1, 2021:1, 2016:3, 2011:4} — 🔴 | dropped | which past transition sets geographic swing; needs the geography model to explain |
| §H7 | min_oos_gain — 0.01 — 🔴 | dropped | a threshold on which census characteristics form pools |
| §H8 | extrapolation_damping — 0.6 — 🔴 | dropped | damping on a composition projection; needs the projection to explain |
| §H9 | extrapolation_max_years / max_extrapolation — 8 / 8.0 — 🔴 | dropped | projection limit |
| §H10 | total_seats — 270 — 🔴 | dropped | a default argument; the council size is the law |
| §H11 | within_rate — 0.90 — 🔴 | dropped | setting of the reader-simulation bloc |
| §H12 | SIMULATION_BLOC — container — 🔴 | dropped | a container |
| §H13 | max_parties — 12 — 🔴 | dropped | coalition table limit |
| §H14 | beta — 1.0 — 🔴 | dropped | part of the scoring definition |
| §H15 | BINS — 5 size bands — 🔴 | dropped | size bands for diagnostics |
| §H16 | THETA_CENTRAL — 6 party values — 🟡 not live | dropped | not live |
| §H17 | SIGMA_COMMON — 1.5pp — 🔴 declared, sourced | dropped | poll error part; inert while polls are off |
| §H18 | SIGMA_IDIO — 1.5pp — 🔴 declared, sourced | dropped | poll error part; inert while polls are off |
| §H19 | SIGMA_DRIFT_PER_ROOT_DAY — 0.30 pp/√day — 🔴 declared, sourced | dropped | poll error part; inert while polls are off |
| §H20 | SIGMA_VOLATILITY — 0.8pp — 🔴 declared, sourced | dropped | poll error part; inert while polls are off |
| §J1 | CENSUS_COVERAGE_FLOOR — 0.80 — 🔴 typed, and it means two things | dropped | census coverage guard |
| §J2 | CENSUS_DRIFT_CEILING — 0.05 — 🟡 measured against an alternative | dropped | census reprojection guard |
| §K1 | NATIONAL_ONLY_FLOOR — 0.001 — 🟢 measured, owner's decision | dropped | threshold for assuming a party onto the ballot |
| §K2 | PRIOR_LOCAL_FLOOR — 0.001 — 🟢 measured, and INERT TODAY | dropped | threshold, inert today |
| §L1 | A declared roster ADDS always and DELETES only on complete = true — ⚖️ argued | dropped | roster handling rule |
| §L2 | The declaration sets the LEVEL; the record sets the WIDTH — ⚖️ argued | dropped | band arithmetic for declared parties; needs the code |
| §L3 | PARTY_KEYS is closed and an unknown key refuses — ⚖️ argued, and cheap | dropped | input validation |
| §L4 | ROSTER_DROP_CEILING — 0.015 — ⚖️ argued, from a measured cost | dropped | roster guard |
| §L5 | MAX_POOL_CAPTURE — 0.9 — 🔴 typed, and it binds SILENTLY | dropped | capture cap |
| §L6 | _arrival_total_prior — pooled MEAN over entrants only — 🟢 measured, and a hypothesis wi... | dropped | estimator for the newcomer total; technical |
| §L7 | len(arr) < 3 in arrival_group_record — 🔴 selects on the dependent variable | dropped | record row filter |
| §L8 | UNCLASSIFIED_FLOOR — 0.005 — ⚖️ a REPORT, and it changes no number | dropped | a report; changes no number |
| §L9 | REGISTRATION_MAX — 2.0 — ⚖️ a runaway guard, not an estimate | dropped | runaway guard |
| §L12 | Two party names in the pasted roster are SUBSTITUTED on judgement, not on evidence — 🔴 ... | dropped | name matching for two small parties; data cleaning |
| §L13 | The SACP's first general ballot is sized by hand from its by-elections — 🔴 typed, and i... | KEPT | kept as "The SACP's first ballot under its own name" |
| §L14 | A pool silenced at the 0.0 corner is held at the city's own rate — 🔴 a declared fallbac... | dropped | a fallback for a fitting failure; needs the pool solve to explain |
| §L11 | The CONTENDER rule — ⛔ SUPERSEDED 2026-09-07, ITS HEADLINE COMPARISON IS ACROSS TWO MOD... | dropped | superseded |
| §L11 | The CONTENDER rule — who is not chaff — ⚖️ argued, and not yet wired | dropped | superseded |
| §L10 | gates_sha — the artefact key records the resolved ENV gates | dropped | artefact key plumbing |
| §M1 | a reader's PR shares stand for both ballots — ⚖️ argued, owner's decision | dropped | the design of the reader's own forecast page, not of the model |
| §N1 | MIN_EFFECTIVE_DRAWS = 200 — 🟡 | dropped | a page threshold on /play/ |
| §N2 | The poll-trust dial, sd(t) = poll_sd / t, and MAX_FIGURE_SE_SEATS = 2.5 — ⚖️ argued, ow... | dropped | the /play/ trust mapping, explained beside the control on that page |
| §O1 | MERGER_RETENTION — 0.75, range [0.5, 0.9] — 🔴 declared, not measured | KEPT | kept as "What a merger keeps" |
