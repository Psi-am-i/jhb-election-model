# Judgement calls — what in these results is not from the record

Every number in this model is meant to be measured or declared. This is the list
of the **declared** ones: choices a person made that the data did not force. It
exists so that "the model measures its constants" can be audited rather than
believed.

Not to be confused with `judgements/<city>-<target>.toml`, which is the
*per-party* lineage and support file a forecaster fills in per city. This is the
register of **structural** calls in the code.

Status: 🔴 wants a second opinion · 🟡 defensible, bounded by evidence ·
🟢 forced by arithmetic or by an identity

Verified against the working tree on `splinter-rule-and-historical-tail`,
2026-08-16. Every line number and every claim below was re-checked by running
the code, not copied from a session narrative.

The 2026-08-14 pass said the same sentence and had already gone stale by the
16th: `LEVEL_DF` had moved 4.0 → 7.0, the Dirichlet floor 0.05 → 1e-4, and every
line number in §A was 10–190 lines out — and §A and §F contradicted each other on
two of them, because §F was written later and §A was never revisited. A register
that names the wrong line is worse than one that names none, because it is
checked and passes.

`test_every_tunable_constant_is_in_the_judgement_register` catches a constant
that is *missing*. It does not catch a row that is *wrong*, which is what
happened here — so re-read the cited line before quoting any row:

    grep -n 'LEVEL_DF\|DIRICHLET_FLOOR\|entrant_prob' src/*.py

---

## A. Not from the record at all

These have no measurement behind them. They are the ones to attack first.

| call | value | where | what it does | status |
|---|---|---|---|---|
| **`entrant_prob`** | **0.25** | `montecarlo.py:194` | The probability that a party arrives from nothing. **A party arrived and won seats in 3 of the last 3 Johannesburg elections** — NFP 2 seats (2011), AIC 4 (2016), ActionSA 44 (2021), and in **7 of the 9 backtested city-years**, median 3 arrivals apiece. At 0.25 the model is silent in 75% of draws, so its *median* seat forecast for an arriving party is **0 whatever its vote share** — but the *mean*, which is what `coherent_seats` uses, is 0.25 × E[triangular(1%, 4%, 12%)] = **1.42%**. Until 2026-08-17 this constant was **unmeasurable twice over** (§1.31): the scoring never relabelled the generic slot onto the party that arrived, and `apply_city` overwrote any edit to `DEFAULTS`. Now measurable, and **the typed value survives the measurement**: on Johannesburg 2016 it drew 1.39% and 3.82 seats against the AIC's actual 1.62% and 4, and at 0.99 it overshoots to 5.35% and 14 seats. The 78% base rate answers a different question — how often *an* arrival wins a seat, not how big *the largest* one is. Downgraded 🔴 → 🟡: still typed, but now tested. | 🟡 |
| `entrant_share` | `[0.01, 0.04, 0.12]` | `montecarlo.py:195` | The arriving party's size. With `entrant_prob` it puts an expected **1.42%** of the vote on a generic newcomer in every run — which matched the AIC's actual 1.62% in 2016 almost exactly (measured: 1.39% drawn, 3.82 seats, against 1.62% and 4), and was 30× short of ActionSA. | 🟡 |
| **`LEVEL_DF`** | **7.0** | `montecarlo.py:285` | Degrees of freedom of the Student-t level shock. Sets how heavy every party's level tail is. **Nothing was measured**; it was 4.0 until this branch, and 3 or 6 are equally arguable. Moved to 7 because `exp(t₄)` has no finite mean and the seat allocator takes a mean. | 🔴 |
| **`level_sd_default`** | **0.45** | `montecarlo.py:930, 1987` | The level spread for a party with no measured `sd(log θ)`. Typed, **and not a `DEFAULTS` key**, so it will not appear in a scenario dump or the in-sample provenance banner. Narrower than it looks: `levels.theta_prior` gives every party in the baseline an `sd`, so this binds only on parties outside it. Either measure it or promote it. | 🟡 |
| Dirichlet floor | `1e-4` | `montecarlo.py:92` (`DIRICHLET_FLOOR`), applied at `1055` | Was `0.05`, which was not a numerical guard but a claim: on Johannesburg 2021, 44 of the Black African pool's 52 members were floored and their collective share went from the 1.59% the model believed to **8.41%** — ~5pp of the citywide vote manufactured for parties the model itself puts near zero. Now floors only to keep the concentration positive, which is all numpy requires. **The register said `0.05` at `:863` for two days after the change.** | 🟢 |
| turnout spread with one observation | `0.30` logits | `pools.py:1269` | When a city has only one prior local election, the turnout band's width is typed. **This is every 2016 target.** | 🟡 |
| `w_bye` | 0.40 | `montecarlo.py:143` | By-election blend weight. **Inert in every backtest** — `byelection_*.csv` only covers 2022-06-01 → 2026-02-25 — but live in the 2026 forecast, so it is untested by anything here. | 🔴 |
| `w_bye_local_ward` / `_pr` | 0.0 / 0.0 | `montecarlo.py:158-159` | Built, disabled. Untestable for the same reason. | 🟡 |
| `ward_noise_sd` | 0.10 | `montecarlo.py:218` | Lognormal noise on each ward×party tally before calling winners. Adopted on an audit, not measured. | 🟡 |
| `turnout_pattern_blend` / `_jitter` / `_noise_sd` | 0.5 / 0.25 / 0.08 | `montecarlo.py:189-191` | The per-VD turnout pattern. The review found `0.08` i.i.d. over 855 VDs contributes ~0.003 citywide, i.e. nothing. | 🟡 |
| **the arrival boundary** | "no baseline at all" | `montecarlo`, by omission | Which parties reach `pools.arrival_rules` rather than θ × baseline. A party with a *trace* in the preceding national election — 0.05–0.17% in that metro — is treated as a retention case, and θ near 0.9 pins it there. **16 of the 79 parties in ranks 4-12 are in this position and are under-forecast by more than 5×, carrying +16.4pp of the −37.4pp band deficit** (§1.31). The code already knows those records are worthless: `RELIABILITY_HALF = 0.002` gives a 0.07% baseline a reliability of 0.26. The arrival record for the same city-years says a typical arrival takes 1.64% (IQR 1.43–2.29%), which is close to what they got. **A boundary nobody chose is still a judgement call.** | 🔴 |
| **`apply_city` never resets `DEFAULTS`** | — | `montecarlo.py:494` | Six of the eight metro configs set no scalars, `cities/joburg.toml` sets sixteen, and `DEFAULTS` is a module global. So every city after Johannesburg in a multi-city run inherits Johannesburg's judgement values. Harmless **only** because those sixteen currently equal `DEFAULTS`. Guarded by `test_apply_city_does_not_leak_one_citys_scalars_into_the_next`, which fails the moment they diverge. | 🔴 |
| `MIN_HOME_SPLITS` + binary home/away | 2 | `pools.py:1613` | A splinter is either "at home" or "away", nothing between. ActionSA's fraction of the DA ran **0.611 / 0.315 / 0.289 / 0.103** across four metros — a gradient modelled as two buckets. This is why Tshwane's seed was 0.17% against an actual 9.28%. | 🔴 |

## B. Measured, but the form or the selection was chosen

The number came from data. The *shape* it was fitted in, or the criterion that
picked it, did not.

| call | where | the choice | status |
|---|---|---|---|
| **`SPINE_K = 1.0`, reciprocal form** | `levels.py:154` | Fitted by leave-one-metro-out, and the curve is flat 0.5–1.5. But a **step function at `worth < 1.0` scored better out of sample (0.2300 against 0.2358)** and was rejected on structural grounds — a smooth weight was preferred to a cliff the data does not place anywhere. A better score overridden by an argument should not be self-certified. | 🔴 |
| **Vote-weighted RMSE as the criterion** | the #22 fit | The spine's 14% gain is on **vote-weighted** RMSE(log). Unweighted it is roughly a wash (0.7092 against 0.7083). The weighting chose the winner, and should be stated whenever the 14% is quoted. | 🔴 |
| **`SPLIT_SD_FLOOR = 0.90`** | `pools.py:1878` | Floors the splinter band's log-spread. **Verified to override the measurement at target 2016** (pooled log-sd 0.286); it does not bind at 2021 (1.599) or 2026 (1.492). So the floor does real work in the one fold where it is least justified. | 🔴 |
| `TURNOUT_CORRELATION = 0.63` | `montecarlo.py:324` | Measured over 14 metro-transitions — but applied as **one constant to every city and every pool pair**, when the measurement itself shows +0.86…+0.91 among three pools and +0.21…+0.47 for the fourth. | 🟡 |
| Gaussian copula for pool turnout | `montecarlo.py:_tri_ppf` | The measurement gives a correlation; it does not give a dependence structure. A Gaussian copula is the conventional choice and has no tail dependence, which is a substantive assumption about whether pools collapse together. | 🟡 |
| `METRO_CODES` widened 2 → 8 | `levels.py:164` | θ and ρ are now read off eight metros rather than Johannesburg and Tshwane. More evidence, no leakage — but it changes θ itself, so it is **confounded with the spine** in any before/after backtest delta. | 🟡 |
| `SHRINK = 2.0`, `RELIABILITY_HALF = 0.002`, `SD_FLOOR/CEILING = 0.15/1.20` | `levels.py:137-146` | Pre-existing shrinkage constants. `RELIABILITY_HALF` is explicitly set to the hard 0.2% cut it replaced. | 🟡 |
| `alpha` per pool | `pools.dirichlet_alpha` | Fitted from historical within-pool concentration, then floored per party at `DIRICHLET_FLOOR` = 1e-4 (§A). Was 0.05, which was a claim rather than a guard. | 🟡 |

## C. Forced by arithmetic or identity — not judgement

| call | where | why it is not a choice |
|---|---|---|
| `Σ base·θ = 1` in the IPF | `fold.calibrate_theta` | Predicted citywide shares are shares. The iteration was otherwise scale-degenerate and drifted four orders of magnitude. | 🟢 |
| Splinter fraction capped at 1.0 of parent | `pools._band_from` | A party cannot take 117% of the vote its parent had. | 🟢 |
| Turnout band in logit space | `pools.turnout_band` | A scale choice, but the standard one for a proportion, and it **removes** caps rather than adding one — no observed-maximum cap, no 1.0 cap. | 🟢 |
| `LEVEL_FLOOR = 1e-6` vs `SHARE_FLOOR = 0.002` | `fold.py:93,107` | Separating the level floor from the deviation floor. Note it fixed **nothing** on its own — the 42 phantom seats were the scale drift above. | 🟢 |

## D. In the reporting, not the model

These shape what a reader concludes and are easy to mistake for findings.

| call | where | effect |
|---|---|---|
| **ENTRANT relabelling** | `diagnose.py` | The model draws a *generic* entrant, so scoring maps it onto whichever party arrived from nothing. **The first version of `diagnose.py` did not do this** and reported Johannesburg 2016's AIC as 0.00% predicted against 1.62% actual (a total miss) *and* ENTRANT as 1.46% against 0.00% (pure phantom). They are the same forecast, and the model was within 0.17pp. Fixed; the corrected total PR vote error is 22.13pp, not 25.04pp. |
| Mean vs median as the point forecast | `compare_history.py` | They differ ~5× for small parties. Reporting the median alone makes the model look far worse at the bottom of the ballot. Both are now shown. |
| "ruled out" threshold | `diagnose.py`, `p < 0.02` | Separates a ward lost in a close contest from one the model excluded. The 2% is typed. |
| anomaly thresholds | `sweep.py` | `actual ≥ 3` seats for "missed entirely", `≥ 2` phantom seats, 10% of council for "does not add up", PIT ≤ 0.01 / ≥ 0.99. All typed. |
| `top = 12` parties per table | `compare_history.py:70` | Cosmetic — but it is also what makes `validation_2021.json` **not comparable**: that file stores only 12 parties while these targets have 15–24 seat-winners, so its seat error is truncated. |
| seat error summed over all parties | `compare_history.py` | The model's own figure spans all 69 parties; it contributes **0** from parties that won nothing, so the wider denominator does not inflate it. |
| modal ward winner = "the model's call" | `diagnose.py` | A defensible reading of a probabilistic forecast, but it is a reading. |

## F. The rest of the tunable constants

Added 2026-08-16 after an audit found **27 constants named in neither register**,
one hour after CLAUDE.md said the record changes in the same commit as the code.
`tests/test_regressions.py::test_every_tunable_constant_is_in_the_judgement_register`
now fails the build if any is missing, which is the only version of that rule
that survives contact with a long session.

| constant | value | what it is | status |
|---|---|---|---|
| `DIRICHLET_FLOOR` | 1e-4 | floor on the Dirichlet MEAN vector, so `E[X]` is exactly the vector asked for. Was 0.05, which manufactured ~5pp of citywide vote | 🟢 |
| `POLL_RMS_ERROR` | 0.030 | a metro poll's total error. A TRACK RECORD — Ipsos's nine 2016 metro readings — not a nominal margin, which was nearer 1.5pp | 🟡 |
| `POLL_HALF_LIFE_DAYS` | 120 | recency half-life for aggregating several waves. **No SA metro series is long enough to fit this**; declared, not measured | 🔴 |
| `CAMPAIGN_WINDOW_DAYS` | 550 | how long before polling day an undated poll may still describe the same election | 🟡 |
| `POLL_K` | 1.0 | legacy evidence-count poll weight, superseded by inverse variance on the metro path | 🟡 |
| `SPLINTER_PARENT_WEIGHT` | 0.35 | share of a splinter's starting vector taken from its parent; measured over 22 splinter-metro cases | 🔴 |
| `LEVEL_DF` | 7.0 | degrees of freedom of the level shock. Was 4.0, which has no finite mean | 🟡 |
| `TURNOUT_CORRELATION` | 0.63 | measured over 14 metro-transitions; applied as ONE constant to every city and pool pair | 🟡 |
| `SPINE_K` | 1.0 | see §B | 🔴 |
| `SHRINK`, `RELIABILITY_HALF` | 2.0, 0.002 | shrinkage constants; `RELIABILITY_HALF` is set to the hard cut it replaced | 🟡 |
| `level_floor` | 1e-6 | separates the level floor from the deviation floor | 🟢 |
| `dirichlet_floor`, `poll_k`, `spine_k` | — | scenario keys mirroring the constants above, so a sweep is reproducible | 🟢 |
| `turnout_noise_sd`, `turnout_blend_jitter` | 0.08, 0.25 | per-VD turnout pattern; the review measured `0.08` i.i.d. over 855 VDs as contributing ~0.003 citywide, i.e. nothing | 🟡 |
| `bye_local_cap`, `bye_tau_months` | 1.5, 18 | by-election ward-local term; **inert in every backtest** | 🔴 |
| `w_bye_local_ward`, `w_bye_local_pr` | 0.0, 0.0 | the ward-local by-election term: built, disabled, and untestable because no past target has by-election data at all | 🟡 |
| `polling_lean`, `polling_span` | 0.0, 8.0 | superseded by the poll paths; still wired | 🟡 |
| `pa_contestation_uplift` | 1.25 | one-party constant, only read when measured contestation is unavailable | 🟡 |
| `MAX_SIGMA`, `MIN_SIGMA`, `NEW_PARTY_SIGMA` | 2.0, 0.15, 1.0 | spread bounds for the `prior-lge-noise` BASELINE, not the model. A party with no earlier result gets 1.0 because a party that did not exist last cycle is the least predictable thing on the ballot | 🟡 |
| `MIN_SHARE`, `CLAIM_FRACTION`, `F_OTHER` | — | reporting and residual-bucket constants in `stats.py` / `benchmarks.py` | 🟡 |
| `poll_weight` | 0.0 | the MANUAL poll dial. Metro polls now blend automatically and do not read it; it remains for a one-off override by `poll_id` | 🟡 |
| `PAGE_SIZE`, `REG_DRIFT_TOLERANCE` | — | pagination and the tolerance on a pinned stat before the site build warns. Reporting, not belief | 🟢 |

## E. What is genuinely from the record

For contrast, and because the list above is not the whole model: θ and ρ and
their shrinkage; the spine's blend weight; pool composition (Census 2022); pool
size (the published roll); the turnout **centre** (the city's last local
election); the turnout **correlation** (14 metro-transitions); the splinter
fractions; the arrival record; contestation (nomination lists); γ (the folds);
ward/PR split ratios; and the seat allocator, which is statute.
