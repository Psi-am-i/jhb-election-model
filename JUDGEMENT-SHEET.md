# The judgement calls, laid out

⛔ **GENERATED — do not edit.** `.venv/bin/python src/judgement_sheet.py`, and `tests/test_judgement_sheet.py` regenerates it and compares.

Every choice a person made that the data did not force, joined to what the registers say about it: what it is, whether it is doing anything at the live target, and whether a reader could move it. The sentence in *what it is* is `JUDGEMENT-CALLS.md`'s own, carried through verbatim — this document writes no new prose about any individual call, so there is one place to correct it.

## How to read the columns

Status: 🔴 wants a second opinion · 🟡 defensible, bounded by evidence ·
🟢 forced by arithmetic or by an identity · ⚪ superseded or resolved ·
⚫ deleted or refused

**doing anything?** is read from `tests/test_levers_are_live`:

* **CERTIFIED INERT** — a registered null with a cause and a gate check that proves it. It is not merely unobserved; something was measured.
* **CONDITIONAL** — dead in the shipped configuration, and measured with its gate held open, which is the only honest reading of such a lever.
* **not certified dead here** — ⚠️ exactly that, and *not* evidence that it fires. It means no null has been registered at this target. The absence of a certificate is not a measurement.

The live target below is **2026**, taken from the registers' own keys rather than typed here.

## 1 · What a reader can move

⛔ **NOTHING, TODAY. The interactive refuses to build**, and says why:

> the interactive page has not been ported to voter pools: its in-browser drawer is the old two-bloc engine and there is nothing left to feed it. See the note at the top of this file. The published page stays frozen in the meantime.

So every 'named by the interactive' below describes a control on a page that is **withheld**, not one a reader can touch. Two things follow, and the second is the one that bites:

* the published forecast exposes **no** judgement call to a reader;
* the frozen page's controls are not a subset of today's levers. The keys it reads that **no city declares** are listed below — each is either a deleted lever or one that never existed here, and the page would drive a control that moves nothing.

Controls the interactive reads off its `scalars` block that **no city declares** — each is a control with nothing behind it:

* `alpha_anc`
* `alpha_da`
* `anc_bloc_shift`
* `bloc_leak`
* `da_bloc_shift`
* `f_other`
* `turnout_tilt_anc`
* `turnout_tilt_da`

It also reads 1 key(s) off its `individual_theta` block; those are party codes, not levers, and are not checked against `[judgements.scalars]` here.
It also reads 6 key(s) off its `theta_mode` block; those are party codes, not levers, and are not checked against `[judgements.scalars]` here.

## 2 · The calls with a symbol

| call | value | kind | doing anything at the live target? | reader can move it? | what it is | status | entry |
|---|---|---|---|---|---|---|---|
| constant | value | unlinked | not linked to a scenario key or module constant | no | current state | status | entry |
| `_LOG_FLOOR` | 1e-6 | unlinked | not linked to a scenario key or module constant | no | Unexercised and kept deliberately: every dimension declares exactly one census, so the branch never runs. A flat sweep of it is not a null about the value. | 🟡 | §A31 |
| `_SIGN_EPS` | 1e-9 | unlinked | not linked to a scenario key or module constant | no | 1e-9, and it decides one of KEY 4's two failure triggers: six orders above the float dust a genuine no-op produced and six below the smallest real effect on record. | 🟡 | §F7 |
| `ALPHA_MIN_SHARE`, `ALPHA_FLOOR`, `ALPHA_CEILING`, `ALPHA_FALLBACK` | 0.01, 1.0, 200.0, 12.0 | unlinked | not linked to a scenario key or module constant | no | Promoted from inline literals 2026-08-22, number-neutral. They are the SELECTION RULE feeding the dominant width lever, and none has ever been swept. | 🔴 | §F31 |
| `alpha` per pool (and `dirichlet_scale`) | — | lever | not certified dead here | no | The model's DOMINANT width lever, sweepable since §1.63 via `dirichlet_scale` and NOT retuned — the method-of-moments fit names 1.0. The ranks 4-12 half of the old 'a scalar cannot serve both bands' finding is WITHDRAWN. | 🟡 | §B7 |
| `apply_city` never resets `DEFAULTS` | — | unlinked | not linked to a scenario key or module constant | no | Still true; harmless only while Johannesburg's sixteen scalars equal `DEFAULTS`, and guarded by a test that fails the moment they diverge. | 🔴 | §A43 |
| `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI` | 0.25, 0.95 | unlinked | not linked to a scenario key or module constant | no | 0.25 / 0.95, the triangular support of every seeded arrival. 25/95 rather than 10/90 or 5/95 is undefended and never swept. | 🔴 | §F32 |
| `arrival_group_draw` | False | lever | not certified dead here | no | Ships False. The rejection was re-run on the label-free referee 2026-08-29 and refuted again; the 254 → 348 figure is superseded and must not be quoted. | 🟢 | §A6 |
| `balance_margins` `iters` / `tol` | 2000 / 1e-12 | unlinked | not linked to a scenario key or module constant | no | 2000 / 1e-12. Nominally operational; registered because the cap is what turns an infeasible problem into an exception. 20,000 iterations move the failure rate 40.9% → 38.9%. | 🟡 | §F10 |
| `beta` | 1.0 | unlinked | not linked to a scenario key or module constant | no | 1.0. It is part of what "better" means, so `ITERATING.md` is arguably its proper home. | 🔴 | §H14 |
| `BINS` | 5 size bands | unlinked | not linked to a scenario key or module constant | no | The size bands behind §1.59/§1.77. The '≥15% of the vote' cut this register quotes as though it were natural is a CHOSEN threshold. | 🔴 | §H15 |
| `BLEND_W` | 1.0 | unlinked | not linked to a scenario key or module constant | no | 1.0, fitted leave-one-city-year-out to the boundary of the family: the optimal blend IS uniform swing. The one constant here legitimately fitted on the scoreboard, because it touches no forecast. | 🟢 | §D9 |
| `bye_local_cap`, `bye_tau_months` | 1.5, 18 | lever | CERTIFIED INERT (UNDELIVERED) — `if (w_ward or w_pr) and ...` — `w_bye_local_ward` and `w_bye_local_pr` both ship at 0.0, so the ward-local block never runs. The DATA is present at this target; only the switch is off; ALSO CONDITIONAL — measured with its gate held open: the cap on one contest's logit shift. At the shipped 1.5 it binds on 11 of the 65 party-contests; the question this asks is whether the model can tell the difference between that and no cap at all. | no | 1.5 / 18, inert in every backtest. | 🔴 | §F24 |
| `BYE_MIN_WEIGHT` | 30.0 | unlinked | not linked to a scenario key or module constant | no | 30.0, the admission gate on the WHOLE by-election channel, promoted from a bare literal. Same reach into the published forecast, same untestability, same status as `w_bye`. | 🔴 | §F33 |
| `bye_weight_mode` | `"fixed"` | lever | not certified dead here | no | Defaults to `fixed`. `inverse_variance` is built and derives the weight; switching it moves the published 2026 forecast and no backtest can score either — the owner's call. | 🟡 | §A33 |
| `CAMPAIGN_WINDOW_DAYS` | 550 | unlinked | not linked to a scenario key or module constant | no | 550, typed. | 🟡 | §F4 |
| `CELL_AREA_FACTOR` | — | unlinked | not linked to a scenario key or module constant | no | Typed at 1.0. ARGUED, NOT TESTED, and a trade between two goods rather than right against wrong. Touches no forecast. | 🟡 | §D17 |
| `independent_wards` (C) in the forecast | 0, structurally | unlinked | not linked to a scenario key or module constant | no | The forecast universe drops INDEPENDENT/IND, so no draw can seat an independent and C is always 0. The IEC records C=1 at eThekwini 2011 and C=4 at 2016, both SCORED — the model allocates those seats to parties and is charged for it. An ASSUMPTION, not a measurement; registered 2026-09-02 after being silent. | 🔴 | §1.166 |
| `CENSUS_COVERAGE_FLOOR` | 0.80 | unlinked | not linked to a scenario key or module constant | no | A WARNING in `pool_counts` and a REFUSAL in `registered_at_target`, on different denominators. Measured 2026-09-02: 0.9609-0.9979 at the refusal, so it binds nowhere and has never been exercised. The §J2 argument applies to it and has not been applied. | 🔴 | §J1 |
| `CENSUS_DRIFT_CEILING` | 0.05 | unlinked | not linked to a scenario key or module constant | no | The reprojection refusal: how far the CITYWIDE composition moves because of unmappable wards. Bounded by ablation (worst random loss 0.028, segregated loss ~0.28) on one city only. | 🟡 | §J2 |
| `contestation_expand` | 0.220 | lever | CERTIFIED INERT (UNDELIVERED) — `if (not _contest or _partial) and _contest_prev` — `levels.contestation` returns the DECLARED ward slates for a target with no result file, so `_contest` is non-empty, the roster declares itself complete, and `levels.projected_contestation` is never called | no | Ships 0.220, live only where no backtest can reach it; superseded automatically the day the IEC publishes 2026 lists. | 🔴 | §A5 |
| `DIRICHLET_FLOOR` | 1e-4 | unlinked | not linked to a scenario key or module constant | no | 1e-4 and inert as committed — but it has a SECOND consumer that floors a CONCENTRATION rather than a mean, and `PERTURB` sweeps it to 0.05 where that would bind. | 🟢 | §F1 |
| `dirichlet_floor`, `spine_k` (scenario keys) | — | lever | not certified dead here | no | Scenario keys mirroring the module constants so a sweep is reproducible. ⚠ This row also lists `poll_k`, which was DELETED on 2026-08-22 (§1.68) and is in no `DEFAULTS` — see the restructure note beneath. | 🟢 | §F21 |
| `entrant_prob` | 0.25 | lever | CERTIFIED INERT (UNDELIVERED) — `universe` does not contain ENTRANT — the 2026 spec, emitted from the declared certified roster, seeds 46 arrivals by name | named by the interactive, which is WITHHELD | Ships 0.25. Typed, but measurable since 2026-08-17 and the typed value survives the measurement; §G-R2 puts the defensible range at [0.25, 0.29]. | 🟡 | §A3 |
| `entrant_share` | `[0.01, 0.04, 0.12]` | lever | CERTIFIED INERT (UNDELIVERED) — `universe` does not contain ENTRANT — the 2026 spec, emitted from the declared certified roster, seeds 46 arrivals by name | named by the interactive, which is WITHHELD | Unchanged at [0.01, 0.04, 0.12]; with `entrant_prob` it puts an expected 1.42% of the vote on a generic newcomer in every run. | 🟡 | §A17 |
| `extrapolation_damping` | 0.6 | unlinked | not linked to a scenario key or module constant | no | 0.6, and typed three more times as a fallback in `pools.py`. | 🔴 | §H8 |
| `extrapolation_max_years` / `max_extrapolation` | 8 / 8.0 | unlinked | not linked to a scenario key or module constant | no | 8 / 8.0 — two copies of one number, one in TOML and one as a dataclass field. | 🔴 | §H9 |
| `FRESHNESS_GRACE_S` | — | unlinked | not linked to a scenario key or module constant | no | Typed at 300s. ARGUED, NOT TESTED — the harness cannot score a publishing guard; the strong half of the check catches the 16-day defect with no window at all. | 🟡 | §D16 |
| `GAMMA_FOLD` | `{2026:1, 2021:1, 2016:3, 2011:4}` | unlinked | not linked to a scenario key or module constant | no | The live 2026 forecast uses fold 1, and the code's own comment concedes the constraint does not pick one. A contestable choice on the published forecast. | 🔴 | §H6 |
| `GRID_MARGIN_CELLS` | — | unlinked | not linked to a scenario key or module constant | no | Typed at 2 and purely operational: the Johannesburg optimum uses no cell in the outermost ring. | 🟢 | §D18 |
| `kappa_bye` | 0.25 | unlinked | not linked to a scenario key or module constant | no | 0.25. Same provenance and the same artefact problem as `w_recency`. | 🔴 | §H3 |
| `LEVEL_DF` | 7.0 | unlinked | not linked to a scenario key or module constant | no | Ships 7.0, live since 2026-08-17 and swept. The sweep cannot distinguish 7 from 30; §F narrows it to ν ∈ [5, 15] on four constraints. | 🟡 | §A18 + §F8 |
| `LEVEL_DF` | 7.0 | unlinked | not linked to a scenario key or module constant | no | BOUNDED 2026-08-29 to ν ∈ [5, 15] on four constraints, with the committed 7.0 in the middle. The honest label is no longer 'unmeasured' but 'not resolvable further on this panel'; a joint (κ, ν) fit was designed and NOT built. | 🟡 | §F8 + §A18 |
| `level_floor` | 1e-6 | lever | not certified dead here | no | 1e-6; separates the level floor from the deviation floor. | 🟢 | §F19 |
| `LEVEL_FLOOR` vs `SHARE_FLOOR` | — | unlinked | not linked to a scenario key or module constant | no | Two separate floors, deliberately. On its own it fixed nothing — the 42 phantom seats were the scale drift above it. | 🟢 | §C4 |
| `level_sd_default` | 0.45 | lever | CERTIFIED INERT (UNDELIVERED) — both consumers are unreachable: `sd_for_party` sees only the `individual` path, which is empty (every index party is a pool member), and the poll blend's `_sd.get(party, default)` runs only when `poll_paths == 'all'` — it has been 'off' since 2026-09-12 | no | MEASURED inert at 2021 and 2026. Would bind for 44 unmeasured 2026 parties if polls were switched back on (`poll_paths` "off" since 2026-09-12). | 🟡 | §A29 |
| `level_shrink` (and `level_shrink_scale`) | 0.35 | lever | not certified dead here | no | Adopted 2026-08-17 and unchanged; the largest single improvement this model has had. Two things keep it off green: an L1 form-selection leak, and a tail the uniform renormalisation over-feeds. | 🟡 | §A23 + §F20 |
| `level_shrink`, `level_shrink_scale` | 0.35, 0.04 | lever | not certified dead here | no | See §A. The scale is a SCALE, not a tuned constant — swept twentyfold with no cliff. | 🟡 | §F20 + §A23 |
| `LOG_CHI2_BIAS` | — | unlinked | not linked to a scenario key or module constant | no | Correct, derived, and DELIBERATELY NOT APPLIED: applying it makes the model worse on every metric, because the record it reproduces is marginal and this layer is conditional. | 🟢 | §C5 |
| `MAX_DISPLACEMENT_RADII` | — | unlinked | not linked to a scenario key or module constant | no | Typed at 5.0 radii — a regression guard rather than a claim, and it separates the optimal assignment (3.8) from the greedy one (8.8). | 🟡 | §D21 |
| `max_parties` | 12 | unlinked | not linked to a scenario key or module constant | no | 12. Operational in flavour, but it silently truncates the coalition space if a council ever seats more than twelve parties — which the 2026 ballot could. | 🔴 | §H13 |
| `MAX_SIGMA`, `MIN_SIGMA`, `NEW_PARTY_SIGMA` | 2.0, 0.15, 1.0 | unlinked | not linked to a scenario key or module constant | no | Spread bounds for the `prior-lge-noise` BASELINE, not for the model. | 🟡 | §F28 |
| `METRO_CODES` widened 2 → 8 | — | unlinked | not linked to a scenario key or module constant | no | Eight metros. More evidence and no leakage, but it moves θ itself, so it is confounded with the spine in any before/after delta. | 🟡 | §B6 |
| `min_clusters` | 8 | unlinked | not linked to a scenario key or module constant | no | Typed. The floor below which the clustered uniformity test prints `not established` instead of a χ². Moves no forecast; decides whether a calibration verdict is a number or a refusal. Under a known null δ̄ is unbiased at every k from 3 to 24 and its noise is SMOOTH in k, so there is no cliff at 8 — any floor is a line on a continuum. | 🔴 | §D22 |
| `MIN_HOME_SPLITS` and the binary home/away | 2 | unlinked | not linked to a scenario key or module constant | no | Unchanged: a measured gradient (0.611 / 0.315 / 0.289 / 0.103) modelled as two buckets. | 🔴 | §A44 |
| `min_oos_gain` | 0.01 | unlinked | not linked to a scenario key or module constant | no | 0.01, and it is upstream of every pool in the model: age and sex are rejected by this number. | 🔴 | §H7 |
| `MIN_SHARE`, `CLAIM_FRACTION`, `F_OTHER` | 0.005, 0.50, 1.30 | unlinked | not linked to a scenario key or module constant | no | All three were filed under the wrong module once. `MIN_SHARE` is `gamma_recent.py`'s and is a CLAIM about the model, not reporting; `CLAIM_FRACTION` is `score.py`'s. ⚠ `F_OTHER` is no longer in `src/` at all — see the restructure note beneath. | 🟡 | §F29 |
| `OVERHANG_DEDUCT_MAX_ROUNDS_SLACK` | 2 | unlinked | not linked to a scenario key or module constant | no | Derived, not chosen: any value ≥ 1 is equivalent. | 🟢 | §A39 |
| `OVERHANG_LEVEL_MAX_ROUNDS` | 200 | unlinked | not linked to a scenario key or module constant | no | 200 rounds. Bounded on ROUNDS deliberately rather than on council size, because a magnitude off the real panel does not transfer to a toy. | 🟡 | §A40 |
| `NATIONAL_ONLY_FLOOR` | 0.001 | unlinked | not linked to a scenario key or module constant | no | The national share below which a party with no local record is NOT assumed onto an unheld ballot. **[16-panel]** Measured over 16 city-years: drops 158 of 226 such candidates for 0.10pp of vote. MK (12.2%) clears it. Owner's decision 2026-09-03; unreachable from any backtest. | 🟢 | §K1 |
| `PRIOR_LOCAL_FLOOR` | 0.001 | unlinked | not linked to a scenario key or module constant | no | The prior-LOCAL share below which a party with no national vote is not assumed onto an unheld ballot. Drops 112 of 189 such candidates for 0.038pp and ZERO seats. ⚠️ INERT until entry 3 lets a projected roster drive the off-ballot drop. | 🟢 | §K2 |
| `overhang_rule` | `"deduct"` | lever | not certified dead here | no | ⚖️ **STATUTE, reclassified 2026-09-02** — Act 3 of 2021 Schedule 1 item 16. NOT a lever and never swept: refused at the `--set` boundary, out of `PERTURB`. Never bound in 24 metro-years; tightest margin 2 seats. | ⚖️ | §H1 |
| `pa_contestation_uplift` | DELETED 2026-08-18 | unlinked | not linked to a scenario key or module constant | no | DELETED 2026-08-18. The branch now falls back to the previous local election's measured contestation for every party, which makes it backtestable. | ⚪ | §F27 |
| `PAGE_SIZE` | — | unlinked | not linked to a scenario key or module constant | no | Pagination. Reporting, not belief. | 🟢 | §F37 |
| `PARTIAL_BALANCE_PASSES` | 200 | unlinked | not linked to a scenario key or module constant | no | 200. A convergence budget that is not a converging sequence, so the number chooses how close to the boundary it gets. | 🟡 | §F12 |
| `PLAN_BOUNDS` | 7 party ranges | unlinked | not linked to a scenario key or module constant | no | **[16-panel]** Present for four of the sixteen panel city-years and absent for twelve, because six of eight metro configs have no `[judgements]` block — which makes the headline seat figure a mixture of two configurations. | 🔴 | §H5 |
| `poll_credence` | 1.0 | lever | CERTIFIED INERT (UNDELIVERED) — `if scenario['poll_paths'] == 'all'` guards the entire metro blend block; `poll_credence` multiplies `w` INSIDE it and is never read; ALSO CONDITIONAL — measured with its gate held open: the dial that chose the 2026 headline while the channel was on (§1.95). 0.0 against the shipped 1.0 is the identity against full belief, so this is the widest perturbation the dial admits. | no | Declared at 1.0, which is the identity, so it moves nothing. The value the backtest supports is UNMEASURED — the paired sweep is pre-registered and not run. | 🔴 | §A11 |
| `poll_deff_subsample` | 1.6 (standalone 1.2) | lever | CERTIFIED INERT (UNDELIVERED) — `polling.effective_n`, reached only from inside the metro blend block the shipped `poll_paths` does not enter; ALSO CONDITIONAL — measured with its gate held open: the design effect on a metro subsample — 4.0 prices the ~500-person cut as worth a quarter of its headline n. | no | Declared at 1.6 (standalone 1.2) and unmeasured; measurable the day a house publishes its effective base. | 🔴 | §A10 |
| `poll_half_life_days` | 120.0 | lever | CERTIFIED INERT (UNDELIVERED) — `polling._recency_weights`, same block; ALSO CONDITIONAL — measured with its gate held open: the recency half-life. At 5 days only the freshest wave counts, which collapses the two SRF waves to one and is the sharpest statement of what recency weighting is doing. | no | A real constant since §1.67 and mirrored in `DEFAULTS`, so a sweep can now reach it. Still declared: no SA metro series is long enough to fit it. | 🔴 | §A14 |
| `POLL_HALF_LIFE_DAYS` | 120 | unlinked | not linked to a scenario key or module constant | no | 120, declared. No SA metro series is long enough to fit it. | 🔴 | §F3 |
| `poll_house_k` | 1.0 | lever | CERTIFIED INERT (UNDELIVERED) — `_cap = 1.0 if polling.SIGMA_TWO_TERM else weight_cap(..., house_k=...)` — the shipped switch takes the branch that never reads the lever; ALSO CONDITIONAL — measured with its gate held open: the retired weight cap. The EXPECTED_INERT entry keeps the lever on the grounds that `SIGMA_TWO_TERM=0` still reads it — so that is the configuration it is measured in. If this ever goes dead the entry's own justification has gone with it and the lever should be deleted. | no | INERT. The cap it drove was deleted 2026-08-24 with the two-term σ; a lone house is now bounded by the derived `polling.house_ceiling` instead. | 🔴 | §A12 |
| `poll_id`, `poll_weight`, `poll_k` | — | unlinked | not linked to a scenario key or module constant | no | DELETED 2026-08-22. The legacy path bypassed every admission rule in `polling.usable_for` and had never executed. | ⚪ | §F30 |
| `POLL_K` | — | unlinked | not linked to a scenario key or module constant | no | DELETED 2026-08-22 with the legacy poll path. The shape survives as `poll_house_k`. | ⚪ | §F5 |
| `poll_min_n` | 300 | lever | CERTIFIED INERT (UNDELIVERED) — same — neither `national_polls` (arrivals) nor the metro block is entered, so nothing calls `polling.screen` on the forecast path at all; ALSO CONDITIONAL — measured with its gate held open: the same floor at the target where it gates the METRO path: both SRF waves are ~500-person subsamples, so a 5,000 floor admits neither. | no | Declared at 300 and settable. Note it runs ahead of every scope test, so it also gates the national polls that drive the arrivals path. | 🔴 | §A16 |
| `poll_paths` | **"off"** | lever | not certified dead here | no | **SHIPS "off" SINCE 2026-09-12 — the forecast uses no poll at all.** The owner's decision, on design grounds; see §A8 and MODEL-LOG §1.225. Measured on 24 city-years: removing the channel moves coherent seat error 725 → 723 and CRPS 545.8 → 541.4, i.e. **not distinguishable from zero**. Every other poll lever below is inert by configuration while this stands. | 🟢 | §A8 |
| `POLL_RMS_ERROR` | ~~0.030~~ | unlinked | not linked to a scenario key or module constant | no | DELETED 2026-08-28. Read by nothing; the constant the tests assert against is its neighbour `POLL_RMS_ERROR_2016`. | ⚫ deleted | §F2 |
| `poll_screen_sd`, `poll_drift_per_root_day`, `POLL_MIN_N` | 0.020 · 0.0010 · 300 | lever | CERTIFIED INERT (UNDELIVERED) — `polling._sigma_total`'s screen term, reached only from inside the metro blend block; ALSO CONDITIONAL — measured with its gate held open: the surcharge for an undisclosed likely-voter screen, priced as ruinous. SRF's screen is the caveat the register carries against both admitted waves, so this is the term that decides how much that caveat costs. | no | All three declared, none measured. The drift rate is fittable from the campaign's waves — pre-register that fit before running it. | 🔴 | §A13 |
| `polling_lean`, `polling_span` | — | unlinked | not linked to a scenario key or module constant | no | DELETED. This row said "still wired" for days after they were gone, which is why the register → code guard exists. | ⚪ | §F26 |
| `POOL_CAPACITY_MARGIN` | 0.98 | unlinked | not linked to a scenario key or module constant | no | Ships 0.98, one full step clear of a measured cliff. It is the guard, not the cure — the cause is an upstream corner solution in the ecological fit. | 🔴 | §A28 + §F9 |
| `POOL_CAPACITY_MARGIN` | 0.98 | unlinked | not linked to a scenario key or module constant | no | See §A — a judgement about what to do when two layers disagree, not a tolerance. | 🔴 | §F9 + §A28 |
| `PROJECTED_METRO_SHARE` | eight per-metro shares of the national vote, 2021 values | unlinked | not linked to a scenario key or module constant | no | The last observed value, so nothing is extrapolated; n = 2 and it fires only where no backtest can check it. | 🔴 | §F36 |
| `REFERENCE_SHARE`, `REFERENCE_SLATE` | `REFERENCE_SHARE` = 0.0025 · `REFERENCE_SLATE` = 0.25 | unlinked | not linked to a scenario key or module constant | no | Both typed. The share cut is safe (below every metro's PR quota); the slate cut is the one to attack, and it moves no forecast — only which columns a width comparison is read on. | 🔴 | §D8 |
| `REG_DRIFT_TOLERANCE` | 0.30 | unlinked | not linked to a scenario key or module constant | no | RECLASSIFIED 2026-08-24 from 🟢 reporting to 🔴: it reaches the forecast through `fold.suspect_vds` → `w_split` → γ. Declared, never measured, and not a `DEFAULTS` key, so no lever sweep can reach it. | 🔴 | §F38 |
| `RELIABILITY_HALF` | 0.002 | unlinked | not linked to a scenario key or module constant | no | 0.002, a value inherited from the hard cut it replaced; only the smooth form is new, and it has never been swept. | 🟡 | §F16 |
| `SAFE` / `STRONG` / `LEAN` | — | unlinked | not linked to a scenario key or module constant | no | Copies of `render_map.main`'s tiers, held in step by `test_the_two_maps_agree_on_the_confidence_tiers`. Not an independent judgement. | 🟢 | §D19 |
| `SD_FLOOR`, `SD_CEILING` | 0.15, 1.20 | unlinked | not linked to a scenario key or module constant | no | 🟡 at ≥15% of the vote. On the corrected harness the width in use is 0.151 against a measured 0.273 [0.136, 0.386] — inside the interval but near its bottom, at 1.81×, binding on 32 of 64. Below 15% every interval EXCLUDES it. | 🟡 (≥15%) | §F17 |
| `SHRINK` | 2.0 | unlinked | not linked to a scenario key or module constant | no | 2.0, measured optimal on forward-validated RMSE(log θ) and on the model's own three scores. Upgraded from 'pre-existing' — do not re-file it as untested. | 🟢 | §A24 + §F15 |
| `SHRINK` | 2.0 | unlinked | not linked to a scenario key or module constant | no | Measured optimal 2026-08-17. Do not re-file it here as 'pre-existing'. | 🟢 | §F15 + §A24 |
| `SIGMA_COMMON` | 1.5pp | unlinked | not linked to a scenario key or module constant | no | LIVE since 2026-08-24. 1.5pp, declared and sourced from outside this repository; never divided by the number of houses, which is the defect it exists to fix. | 🔴 declared, sourced | §H17 |
| `SIGMA_DRIFT_PER_ROOT_DAY` | 0.30 pp/√day | unlinked | not linked to a scenario key or module constant | no | LIVE since 2026-08-24. 0.30 pp/√day, declared and sourced; the shipped `POLL_DRIFT_PP_PER_ROOT_DAY` of 0.10 is 2–4× too small. | 🔴 declared, sourced | §H19 |
| `SIGMA_IDIO` | 1.5pp | unlinked | not linked to a scenario key or module constant | no | LIVE since 2026-08-24. 1.5pp, declared and sourced; the ONLY term `h_eff` may divide. | 🔴 declared, sourced | §H18 |
| `SIGMA_VOLATILITY` | 0.8pp | unlinked | not linked to a scenario key or module constant | no | LIVE since 2026-08-24. 0.8pp, declared and sourced — a South Africa adjustment for average party swing. | 🔴 declared, sourced | §H20 |
| `SIMULATION_BLOC` | container | unlinked | not linked to a scenario key or module constant | no | The reader-simulation bloc definition that `within_rate` sits in. | 🔴 | §H12 |
| `SOLVE_TOL` | 1e-9 | unlinked | not linked to a scenario key or module constant | no | Operational, and listed EXEMPT in the guard — named here so the exemption is visible in the register and not only in the test. | 🟢 | §F11 |
| `SPINE_K` | 1.0 | unlinked | not linked to a scenario key or module constant | no | See §B. | 🔴 | §F14 + §B1 |
| `spine_k = 0` on a party with no θ evidence | `w_local = 0.0` | unlinked | not linked to a scenario key or module constant | no | A CHOSEN limit (`w = 0`, pure national spine), inert at the shipped `spine_k = None` and reachable only by a sweep, which is what it exists for. | 🟡 | §F22 |
| `SPINE_K`, reciprocal form | — | unlinked | not linked to a scenario key or module constant | no | 1.0, fitted leave-one-metro-out on a curve that is flat 0.5–1.5. A step function scored better out of sample and was rejected on structural grounds — which is why this is 🔴 despite being fitted. | 🔴 | §B1 + §F14 |
| `SPLINTER_PARENT_WEIGHT` | 0.35 | unlinked | not linked to a scenario key or module constant | no | 0.35, measured over 22 splinter-metro cases, no bootstrap, and stale since the archive grew (§A). | 🔴 | §F6 |
| `SPLIT_SD_FLOOR` | — | unlinked | not linked to a scenario key or module constant | no | 0.90, and it overrides its own measurement at target 2016 while binding at neither 2021 nor 2026 — real work in the one fold where it is least justified. | 🔴 | §B3 |
| the `home` city and `measured_from` pair of each entry in `SPLITS` | ASA→JHB · GOOD→CPT · MK→ETH · NFP→ETH · COPE and EFF→**None** | unlinked | not linked to a scenario key or module constant | no | Six typed biographical claims that select WHICH record sizes a splinter. ActionSA's is the single assignment behind the panel's largest error, and the two unset ones announce nothing at all. Declared 2026-09-13, never swept. | 🔴 | §A47 |
| the size-dependence of `sd_for` below 15% | a straight line in log(size) | unlinked | not linked to a scenario key or module constant | no | The model is UNCHANGED and the fault is the FORM, not the residual. ⛔ No further functional form may be tried against these two folds, and this row's numbers are Form A's and must not be quoted. | 🔴 | §F18 |
| `THETA_CENTRAL` | 6 party values | unlinked | not linked to a scenario key or module constant | no | NOT LIVE. The plan's six typed party values, and the module holding them has since been retired out of `src/` — see the restructure note beneath. | 🟡 not live | §H16 |
| `theta_prior` and `_shrunk` | RESOLVED 2026-08-18 | unlinked | not linked to a scenario key or module constant | no | RESOLVED 2026-08-18. Both shrink toward `size_centre`, they agree to 1e-16, and no forecast moved. | ⚪ | §A26 |
| `TIP_FLOOR` / `OTHER_FLOOR` | — | unlinked | not linked to a scenario key or module constant | no | Same provenance and same drift guard as the tiers above. | 🟢 | §D20 |
| `top = 12` parties per table | — | unlinked | not linked to a scenario key or module constant | no | Cosmetic here — but it is what makes `validation_2021.json` not comparable. | — | §D13 |
| `total_seats` | 270 | unlinked | not linked to a scenario key or module constant | no | Johannesburg's 270 as a DEFAULT ARGUMENT in the shared allocator. The offending caller this row names was `leverage.py`, since retired — every `allocate` call left in `src/` passes it explicitly, so the trap is latent rather than live. | 🔴 | §H10 |
| `TURNOUT_CORRELATION` | — | unlinked | not linked to a scenario key or module constant | no | 0.63 applied as ONE constant to every city and pool pair. It supplies 4–12% of drawn variance in the shape a pool-turnout mechanism should have; why it matters so little is still not explained. | 🟡 | §B4 + §F13 |
| `TURNOUT_CORRELATION` | 0.63 | unlinked | not linked to a scenario key or module constant | no | 0.63, declared in `DEFAULTS` since §1.63 and asserted equal to the module constant at import. It MOVES the forecast, so it is a live lever. | 🟡 | §F13 + §B4 |
| TURNOUT_CORRELATION / SPLINTER_PARENT_WEIGHT / SPLIT_SD_FLOOR — the stale-`n` trio | `TURNOUT_CORRELATION` 0.63 · `SPLINTER_PARENT_WEIGHT` 0.35 · `SPLIT_SD_FLOOR` 0.90 | unlinked | not linked to a scenario key or module constant | no | Still NOT re-measured against the enlarged θ record, and deliberately so; quote none of their `n` values until the record question below is settled. | 🔴 | §A1 |
| `TURNOUT_DRAW_FLOOR`, `TURNOUT_DRAW_CEILING` | 0.02, 0.95 | unlinked | not linked to a scenario key or module constant | no | 0.02 / 0.95, applied per draw. They contradict §C's claim that the turnout band 'removes caps rather than adding one'; whether the ceiling ever binds is unmeasured. | 🔴 | §F34 |
| `turnout_noise_sd`, `turnout_blend_jitter` | 0.08, 0.25 | lever | not certified dead here | named by the interactive, which is WITHHELD | Typed; ~0.003 citywide, i.e. nothing. | 🟡 | §F23 + §A41 |
| `turnout_pattern_blend` / `turnout_blend_jitter` / `turnout_noise_sd` | 0.5 / 0.25 / 0.08 | lever | not certified dead here | named by the interactive, which is WITHHELD | Typed. The citywide effect of the 0.08 is ~0.003, i.e. nothing — but see §G-R5: the turnout knobs move 46 ward wins, so the citywide null is not the whole story. | 🟡 | §A41 + §F23 |
| `w_bye` | 0.40 | lever | not certified dead here | named by the interactive, which is WITHHELD | Typed at 0.40, live in the 2026 forecast and inert in every backtest. Only the 2026 result can bound it. | 🔴 | §A35 |
| `w_bye_local_ward` / `w_bye_local_pr` | 0.0 / 0.0 | lever | not certified dead here | no | Built and disabled at 0.0 / 0.0. Untestable for the same reason as `w_bye`. | 🟡 | §A37 + §F25 |
| `w_bye_local_ward`, `w_bye_local_pr` | 0.0, 0.0 | lever | not certified dead here | no | Built, disabled, untestable. | 🟡 | §F25 + §A37 |
| `w_recency` | 0.70 | unlinked | not linked to a scenario key or module constant | no | 0.70, verbatim from the original plan. It reaches the model through 20 committed `turnout.csv` files that carry no artefact key, so changing it does nothing until someone re-runs the script. | 🔴 | §H2 |
| `w_split` | 0.6 | unlinked | not linked to a scenario key or module constant | no | 0.6, plan §3.5 'Basis: Judgement', baked into the fold parameter artefacts. | 🔴 | §H4 |
| `ward_noise_sd` | 0.10 | lever | not certified dead here | no | Typed at 0.10 on an audit, never measured and never bounded. | 🟡 | §A38 |
| `WARD_PR_RATIO_MIN`, `WARD_PR_RATIO_MAX` | 0.5, 2.0 | unlinked | not linked to a scenario key or module constant | no | 0.5 / 2.0 — the clip that overrides the record §E says the ward/PR ratio comes from. How often it binds is unmeasured. | 🔴 | §F35 |
| `within_rate` | 0.90 | unlinked | not linked to a scenario key or module constant | no | 0.90, and three copies of one number. | 🔴 | §H11 |

## 3 · The calls with no symbol of their own

Structural choices the code makes without a constant to name them — the easiest kind to lose, because nothing can grep for them.

| the call | where | what it is | status | entry |
|---|---|---|---|---|
| the call | where | current state | status | entry |
| the θ record pools a collapse, a split and a merger | `levels.theta_record` | Not implemented. The 2009→2011 transition is still pooled into θ; a structural-event filter is the proposed instrument and the decision is the owner's. | 🔴 | §A2 |
| retiring the generic entrant at nomination close | `montecarlo`, `cities/joburg.toml` | OPEN GAP. A one-off decision to be taken when the lists close on 16 September — explicitly NOT to be automated. Task A4. | 🔴 | §A4 |
| the published 2026 forecast is not the backtested configuration | `montecarlo`, `polling`, and the whole `EXPECTED_I… | **AMENDED 2026-09-12.** No house decides the headline any more — the poll channel is OFF (§A8, MODEL-LOG §1.225). The criticism is REDUCED, not answered: the live forecast still runs `w_bye` and `contestation_expand`, which no backtest row can score, so it went from three unscoreable channels to two. Measured effect of the switch on the headline: DA 79 → 68, and the largest-party call becomes a **dead heat** (ANC 47.3% / DA 47.0%) rather than DA 71.4%. §1.226. | 🔴 | §A7 |
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

## 4 · Gaps this join can see

Scenario keys the judgement register does not name:

* `draws`
* `entrant_geography`
* `seed`

Scenario keys with **no register row under their own name**. Each is still a judgement call; the note says what stands in for its row, and a prose mention is not a row:

* `draws` — ⛔ not in the register at all
* `entrant_geography` — ⛔ not in the register at all
* `pools` — ⚠️ named only in the register's prose, with no row of its own — enough to count as registered, not enough to read
* `seed` — ⛔ not in the register at all
* `turnout_correlation` — its row is filed under the shadow constant `montecarlo.TURNOUT_CORRELATION`, tied to it by an assert, so the row does describe it

Register rows parsed: 110 with a symbol, 36 structural. A row whose cell count does not match its header is dropped rather than guessed at, so these counts are the parser's own view and a drop shows up as a missing row here rather than as a mangled one.

