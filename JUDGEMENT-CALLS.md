# Judgement calls — the register

Every number in this model is meant to be measured or declared. This file is the
list of the ones that are **declared**: choices a person made that the data did
not force, each with what it is, where it lives, what evidence bounds it, and how
to check it. It exists so that "the model measures its constants" can be audited
rather than believed.

Not to be confused with `judgements/<city>-<target>.toml`, which is the
*per-party* lineage and support file a forecaster fills in per city. This is the
register of **structural** calls in the code.

Status key: 🔴 wants a second opinion · 🟡 defensible, bounded by evidence ·
🟢 forced by arithmetic or by an identity

Last updated 2026-08-13, covering the working tree on
`splinter-rule-and-historical-tail` (task #22, the calibration items, and the
bug sweep). Line numbers are that tree's.

---

## 1. Calls made in the task #22 / calibration / bug work

### 1.1 The spine — how a party's level is built

| | Call | Where | Evidence, and what is *not* evidenced |
|---|---|---|---|
| 🟡 | **`SPINE_K = 1.0`** — weight on the local route is `k / (worth + k)` | `src/levels.py:141` | Leave-one-metro-out over 180 party-city-years: k=0.5 → 0.2377, **k=1.0 → 0.2358**, k=1.5 → 0.2387, against a national-only spine at 0.2745. The curve is flat across 0.5–1.5, so this is the middle of a plateau, not a point estimate. Anything in that range is equally defensible. |
| 🔴 | **Reciprocal form rather than a step** | `src/levels.py`, `spine()` | A step function at `worth < 1.0` **scored better out of sample** (0.2300 against 0.2358). It was rejected as two implicit parameters fitted on 180 points, and brittle at the boundary. *This is a case where a better score was overridden by a structural argument* — the call most worth a second opinion in this file. |
| 🔴 | **Selection on vote-weighted RMSE(log)** | probe methodology | Unweighted, the blend is close to a wash with the national spine. Vote-weighted, it wins by 14%. Weighting is defensible (seats follow votes) but it is the choice that picked the winner, and it should be stated whenever the 14% is quoted. |
| 🟡 | **Accepting 4 wins / 4 losses by metro** | probe methodology | Blend beats national-only on JHB, TSH, EKU, BUF; loses on CPT, ETH, MAN, NMA. It wins *pooled* because the wins land where the national route fails worst (BUF 0.320 → 0.111) and the losses where it was already accurate (MAN 0.077 → 0.094). A real trade, not a clean victory. |
| 🟡 | **Rejecting bidirectional θ outright** | `src/levels.py` docstring | Measured worse (0.292 against 0.275 held out), because a reverse observation divides a local result by a *later* national one and so carries the party's trend with the opposite sign (PA 1.90 forward / 0.60 reverse; ANC 0.85 / 1.05). But it is the only θ evidence an ActionSA-type party has, and it was dropped for those parties too rather than kept as a fallback. |
| 🟡 | **Widening the evidence base from two metros to eight** | `src/levels.py:151` | More evidence, no leakage (everything is strictly before the target). But it changes θ on the *pre-existing* path as well, so it is confounded with the spine change in every before/after figure reported for this branch. Separating them would need a run with `METRO_CODES = ("JHB","TSH")`. |

### 1.2 Calibration — how wide the draw is

| | Call | Where | Evidence, and what is *not* evidenced |
|---|---|---|---|
| 🔴 | **`LEVEL_DF = 4.0`** — Student-t degrees of freedom for the level shock | `src/montecarlo.py:237` | **Not measured.** Chosen so the variance stays finite (the measured `sd(log θ)` keeps its meaning) while the tail is heavy enough that observed-but-unlikely results are not assigned probability zero. 3 or 6 would be equally arguable and nothing in the record distinguishes them. |
| 🔴 | **`level_sd_default = 0.45`** — spread for a party with no measured `sd(log θ)` | `src/montecarlo.py:745` | Typed, and **not surfaced as a key in `DEFAULTS`** — it is an inline fallback, so it will not appear in a scenario dump or the provenance banner. Either measure it or promote it. |
| 🟡 | **`TURNOUT_CORRELATION = 0.63`** — one scalar for how pools move together | `src/montecarlo.py:265` | The mean is measured over 14 metro-transitions. The matrix behind it is *not* homogeneous: Black African / Coloured / White sit at +0.86 to +0.91, Indian/Asian at +0.21 to +0.47. Collapsing that to one number is the call. Consequence is real — independent pools put citywide turnout sd at 0.50 of a single pool's where the record says 0.82. |
| 🟡 | **Gaussian copula as the coupling mechanism** | `src/montecarlo.py`, `correlated_triangular` | Chosen because it preserves each pool's measured marginal turnout band exactly, so only the dependence changes. The copula *family* has no evidence behind it; a t-copula would give more joint-tail dependence. |
| 🟡 | **Seeded arrivals excluded from the per-party level shock** | `src/montecarlo.py`, `pool_sd_shock` | Their arrival band *is* the estimate, so shocking it again would double-count. Arguable the other way. |
| 🟡 | **Removing the θ-band clamp on the spine centre** | `src/montecarlo.py`, `make_drawer` | Required, or the clamp silently undoes task #22 (it would pull ActionSA's blended level back toward the band measured on parties that *have* a θ). But it removes a guard that was catching something, and nothing replaced it. |

### 1.3 Bugs — the fixes, and what they assume

| | Call | Where | Evidence, and what is *not* evidenced |
|---|---|---|---|
| 🟢 | **`Σ base·θ = 1` pins θ's scale** | `src/fold.py:241` | The degeneracy is real: `predict` renormalises within each VD, so a common factor on θ cancels wherever `expit` is in its exponential tail, and the iteration had drifted four orders of magnitude (ANC at θ = 0.0001). The constraint is the identity the quantity already implies. Other pins exist; this one is the natural one. Effect: 42 phantom seats removed from fold 2; fold 1 total seat error 12 → 14. |
| 🟡 | **`LEVEL_FLOOR = 1e-6` in the fold** | `src/fold.py:107` | Separates the level floor from the deviation floor, matching what `montecarlo.py` did on 2026-08-06. On its own it changed **nothing** — which is how the real bug above was found. Kept because the 0.002 level floor is still a substantive claim (no party smaller than 0.2% anywhere) rather than a numerical guard. |
| 🔴 | **`SPLIT_SD_FLOOR = 0.90`** — narrowest a splinter band may be, in log units | `src/pools.py:1816` | Typed, and it **actively overrides the measurement at target 2016**, where the pooled record's own log-sd is 0.286. Verified: 2016 → floor binds; 2021 (1.599) and 2026 (1.492) → measured spread wins. So the floor is doing real work in exactly the fold where it is least justified. |
| 🟢 | **Splinter band capped at 1.0** | `src/pools.py:1859` | A splinter takes a share *of its parent*; above 1.0 there is nothing to take. Johannesburg's own record produced a lognormal top of 1.17 without it. |
| 🟡 | **Turnout band capped at 1.0 rather than at the observed maximum** | `src/pools.py:1267` | Fixes a genuine one-sidedness (previously mode == high in most pools at targets 2016 and 2021, so turnout could only fall — the same mistake the docstring rejects for the *bottom* of the band). Verified fixed: 0 of 4 pools pinned in every city-year checked. **New artefact:** the 1.0 cap now binds for Tshwane's Indian/Asian pool, giving a band whose top is 100% turnout (27%/64%/100% at 2021). A 100% upper bound is not credible and wants a real ceiling. |
| 🟡 | **Not regenerating `pools_2026.json`** | — | 2016/2021 specs were re-emitted; the live forecast's spec was deliberately left alone. Consequence: the live forecast and the backtests now run on specs generated by *different* code. Intentional, and a state that should not persist. |
| 🟡 | **Anomaly thresholds in the sweep** | `src/sweep.py:108,112,118,122,125` | All typed: seat-winner missed = `actual ≥ 3 and median == 0`; phantom = `≥ 2` seats; council mismatch = `> 10%`; interval excludes truth = PIT `≥ 0.99` / `≤ 0.01`. These decide what gets reported as an anomaly, so they shape the finding list. |

---

## 2. Pre-existing calls the anomaly sweep surfaced

Not made in this work, but now known to be load-bearing.

| | Call | Where | Why it matters |
|---|---|---|---|
| 🔴 | **`MIN_HOME_SPLITS = 2` and the binary home/away splinter split** | `src/pools.py:1585` | ActionSA took 0.611 of the DA's vote in Johannesburg, 0.315 in Tshwane, 0.289 in Ekurhuleni, 0.103 in eThekwini — a gradient, modelled as two buckets. Sized as "away", Tshwane's ActionSA got a seed of 0.17% against an actual 9.28%, and the model gave it a median of 0 seats where it won 19. Widening the band does not fix this; the *centre* is wrong. |
| 🟡 | **The `SPLITS` lineage table** | `src/pools.py` | Which party split from which is declared by a person, by design, with evidence in the docstring. Correctly a judgement; listed for completeness. |
| 🟡 | **`w_bye = 0.40`, `w_bye_local_ward = 0.0`, `w_bye_local_pr = 0.0`** | `src/montecarlo.py:129,144,145` | All three are **inert in every backtest**: by-election data covers 2022-06-01 → 2026-02-25 only, so no historical target has any. The by-election channel is untestable with the data held, not merely untested — which is the real answer to "why is the ward-local term still disabled". |
| 🟡 | **`entrant_prob = 0.25`, `entrant_share = [0.01, 0.04, 0.12]`** | `src/montecarlo.py:179,180` | Untouched typed constants governing the generic-entrant slot. |
| 🟡 | **`turnout_noise_sd = 0.08`, `ward_noise_sd = 0.10`, `level_floor = 1e-6`** | `src/montecarlo.py:176,203,209` | Typed; the last two carry adoption dates and rationale in-line, the first does not. |
| 🟡 | **`SD_FLOOR/SD_CEILING = 0.15/1.20`, `SHRINK = 2.0`, `RELIABILITY_HALF = 0.002`** | `src/levels.py:124,128,133` | The θ prior's shrinkage machinery. `RELIABILITY_HALF` is documented as deliberately set to the hard cut it replaced; the other three are typed. |
| 🟡 | **`theta_mode`, `individual_theta`, `f_other`, `PLAN_BOUNDS`** | `src/montecarlo.py:96,109,116,124` | Still present as fallbacks. They are the hand-typed constants the measured layer replaced, and reaching them still trips the in-sample banner — which is the intended behaviour, not a bug. |
| 🟢 | **`judgements/*-2021.toml` are untouched templates** | `judgements/` | Worth recording as a *negative*: no city declares ActionSA's support for 2021. Johannesburg's ActionSA result comes from the arrival rules, not from a human telling the model the answer. |

---

## 3. The one that is not a tuning choice

The largest and most systematic historical error is **new parties**, and no
setting in this file fixes it. At target 2021 ActionSA had no prior splinter
observation of its own, so it was sized from COPE and EFF, which took 0.45% to
1.7% of their parent's vote away from home. ActionSA took 10% to 61%. The record
is three splits and the new party is an order of magnitude larger than any of
them; widening the band to cover that would make the band meaningless for
everything else.

Ward reach does not rescue it either: reach predicts *whether* a splinter
appears (ActionSA contested four metros of eight and scored zero in the other
four), not how big it is — among the four it contested, reach was 99–100%
everywhere while its share ran from 2.35% to 18.12%.

Pre-election polls are the only evidence that could have caught it, which is the
substance of task #23 and the reason it outranks further calibration work.
