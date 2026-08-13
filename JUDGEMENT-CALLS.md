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
2026-08-14. Every line number and every claim below was re-checked by running
the code, not copied from a session narrative.

---

## A. Not from the record at all

These have no measurement behind them. They are the ones to attack first.

| call | value | where | what it does | status |
|---|---|---|---|---|
| **`entrant_prob`** | **0.25** | `montecarlo.py:179` | The probability that a party arrives from nothing. **A party arrived and won seats in 3 of the last 3 Johannesburg elections** — NFP 2 seats (2011), AIC 4 (2016), ActionSA 44 (2021). At 0.25 the model is silent in 75% of draws, so its *median* seat forecast for an arriving party is **0 whatever its vote share**. This single constant produces most of the "seat-winner missed entirely" anomalies. | 🔴 |
| `entrant_share` | `[0.01, 0.04, 0.12]` | `montecarlo.py:180` | The arriving party's size. With `entrant_prob` it puts an expected **1.42%** of the vote on a generic newcomer in every run — which matched the AIC's actual 1.62% in 2016 almost exactly, and was 30× short of ActionSA. | 🟡 |
| **`LEVEL_DF`** | **4.0** | `montecarlo.py:237` | Degrees of freedom of the Student-t level shock. Sets how heavy every party's level tail is. **Nothing was measured**; 3 or 6 are equally arguable. | 🔴 |
| **`level_sd_default`** | **0.45** | `montecarlo.py:745` | The level spread for a party with no measured `sd(log θ)`. Typed, **and not a `DEFAULTS` key**, so it will not appear in a scenario dump or the in-sample provenance banner. Either measure it or promote it. | 🔴 |
| Dirichlet floor | `0.05` | `montecarlo.py:863` | `np.maximum(moved * alpha, 0.05)`. Invented. It is why a small party's within-pool share is a spike near zero with a long tail, and therefore why **median and mean diverge ~5×** for small parties (AIC 2021: median 0.11%, mean 0.58%, actual 0.69%). 22 of 214 member slots are floored at even props; far more in practice. | 🔴 |
| turnout spread with one observation | `0.30` logits | `pools.py:1296` | When a city has only one prior local election, the turnout band's width is typed. **This is every 2016 target.** | 🟡 |
| `w_bye` | 0.40 | `montecarlo.py:129` | By-election blend weight. **Inert in every backtest** — `byelection_*.csv` only covers 2022-06-01 → 2026-02-25 — but live in the 2026 forecast, so it is untested by anything here. | 🔴 |
| `w_bye_local_ward` / `_pr` | 0.0 / 0.0 | `montecarlo.py:143-144` | Built, disabled. Untestable for the same reason. | 🟡 |
| `ward_noise_sd` | 0.10 | `montecarlo.py:203` | Lognormal noise on each ward×party tally before calling winners. Adopted on an audit, not measured. | 🟡 |
| `turnout_pattern_blend` / `_jitter` / `_noise_sd` | 0.5 / 0.25 / 0.08 | `montecarlo.py:174-176` | The per-VD turnout pattern. The review found `0.08` i.i.d. over 855 VDs contributes ~0.003 citywide, i.e. nothing. | 🟡 |
| `MIN_HOME_SPLITS` + binary home/away | 2 | `pools.py:1616` | A splinter is either "at home" or "away", nothing between. ActionSA's fraction of the DA ran **0.611 / 0.315 / 0.289 / 0.103** across four metros — a gradient modelled as two buckets. This is why Tshwane's seed was 0.17% against an actual 9.28%. | 🔴 |

## B. Measured, but the form or the selection was chosen

The number came from data. The *shape* it was fitted in, or the criterion that
picked it, did not.

| call | where | the choice | status |
|---|---|---|---|
| **`SPINE_K = 1.0`, reciprocal form** | `levels.py:141` | Fitted by leave-one-metro-out, and the curve is flat 0.5–1.5. But a **step function at `worth < 1.0` scored better out of sample (0.2300 against 0.2358)** and was rejected on structural grounds — a smooth weight was preferred to a cliff the data does not place anywhere. A better score overridden by an argument should not be self-certified. | 🔴 |
| **Vote-weighted RMSE as the criterion** | the #22 fit | The spine's 14% gain is on **vote-weighted** RMSE(log). Unweighted it is roughly a wash (0.7092 against 0.7083). The weighting chose the winner, and should be stated whenever the 14% is quoted. | 🔴 |
| **`SPLIT_SD_FLOOR = 0.90`** | `pools.py:1847` | Floors the splinter band's log-spread. **Verified to override the measurement at target 2016** (pooled log-sd 0.286); it does not bind at 2021 (1.599) or 2026 (1.492). So the floor does real work in the one fold where it is least justified. | 🔴 |
| `TURNOUT_CORRELATION = 0.63` | `montecarlo.py:265` | Measured over 14 metro-transitions — but applied as **one constant to every city and every pool pair**, when the measurement itself shows +0.86…+0.91 among three pools and +0.21…+0.47 for the fourth. | 🟡 |
| Gaussian copula for pool turnout | `montecarlo.py:_tri_ppf` | The measurement gives a correlation; it does not give a dependence structure. A Gaussian copula is the conventional choice and has no tail dependence, which is a substantive assumption about whether pools collapse together. | 🟡 |
| `METRO_CODES` widened 2 → 8 | `levels.py:151` | θ and ρ are now read off eight metros rather than Johannesburg and Tshwane. More evidence, no leakage — but it changes θ itself, so it is **confounded with the spine** in any before/after backtest delta. | 🟡 |
| `SHRINK = 2.0`, `RELIABILITY_HALF = 0.002`, `SD_FLOOR/CEILING = 0.15/1.20` | `levels.py:124-133` | Pre-existing shrinkage constants. `RELIABILITY_HALF` is explicitly set to the hard 0.2% cut it replaced. | 🟡 |
| `alpha` per pool | `pools.dirichlet_alpha` | Fitted from historical within-pool concentration, then floored per party at 0.05 (§A). | 🟡 |

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

## E. What is genuinely from the record

For contrast, and because the list above is not the whole model: θ and ρ and
their shrinkage; the spine's blend weight; pool composition (Census 2022); pool
size (the published roll); the turnout **centre** (the city's last local
election); the turnout **correlation** (14 metro-transitions); the splinter
fractions; the arrival record; contestation (nomination lists); γ (the folds);
ward/PR split ratios; and the seat allocator, which is statute.
