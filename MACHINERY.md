# The machinery: every calculation, and where its numbers come from

A map of what the model computes, in the order it computes it, with the
provenance of every input. Written because the model had reached a size where
nobody could say from memory which parts were measured, which were judged, and
which were switched off — and three separate sessions of work turned out to be
inert by default.

**Source column:**
`MEASURED` fitted from data · `JUDGED` someone chose it · `STATUTE` fixed by law ·
`DERIVED` computed from other inputs · `OFF` present but inactive by default

**Saw column:** which elections the number's value depends on. This is the
temporal-validity question: a number that saw election *T* cannot be used to
predict *T*.

---

## 0. Structure — which parties compete with which

| Piece | Where | Source | Saw |
|---|---|---|---|
| `BLOCS` = ANC_BLOC / DA_BLOC | `cities/*.toml [judgements.blocs]` → `montecarlo.BLOCS` | JUDGED | 2021, 2024 (needs ActionSA, MK, BOSA to exist) |
| Pool membership + weights (12 pools) | `scenarios/joburg-pools.json` **only** | MEASURED (flow, k, racial gradient) | 2019→2024 |
| Pool ratio ranges | same file | MEASURED, 32 metro-transitions | **includes every backtest target** |
| Pool α | same file | MEASURED, method of moments | includes 2021, 2024 |

**The gap that matters.** The city TOMLs define two blocs; the twelve pools live
only in a scenario file and `DEFAULTS["pools"] = {}`. So every default run uses
blocs. There is no Tshwane pool file. Pool membership also changes as parties
appear and die, so it belongs on the target axis, not the city axis.

---

## 1. Baseline — the starting position

| Piece | Where | Source | Saw |
|---|---|---|---|
| Citywide + VD shares | `target.results(target.previous_npe)` | MEASURED | prior NPE only ✅ |
| Party canonicalisation | `parties.py` ALIASES | JUDGED (naming) | nothing — verified carries no outcome knowledge ✅ |
| Ward boundaries, roll | `vd_ward_<year>.csv`, else the target's own result file | MEASURED | published pre-election ✅ |
| Council size, ward count | `cities/*.toml [structure.by_year]` | STATUTE | delimitation, pre-election ✅ |

---

## 2. Level — how big each party will be

| Piece | Where | Source | Saw |
|---|---|---|---|
| `theta_mode` | DEFAULTS + city TOML | **JUDGED** | 2016, 2021, and 2025/26 polling |
| `PLAN_BOUNDS` | `montecarlo.py`, city TOML | **JUDGED** | 2016, 2021 — and *excludes* observed ANC 0.91/0.94 and DA 0.88 |
| `individual_theta` (6 parties) | DEFAULTS | **JUDGED** | fold 1 and 2 = the 2016 and 2021 targets |
| `f_other` (the ~31 residual parties) | DEFAULTS | **JUDGED** | 2024 residual share |
| `anc_bloc_shift` / `da_bloc_shift` | DEFAULTS | **JUDGED** | four transitions incl. 2009→11, 2014→16, 2019→21 |
| `alpha_anc` / `alpha_da` | DEFAULTS | **JUDGED** | α_da justified by "the ActionSA outcome" |
| `bloc_leak` | DEFAULTS | JUDGED, default 0 | 2021 |
| `splinter` branch | DEFAULTS | MEASURED, 24 metro-obs | **OFF**; ranges saw 2011 and 2016 |
| `w_bye` blend | DEFAULTS | JUDGED | plan default |
| by-election deltas | `byelections.py` | MEASURED | contests before the target ✅ |
| `poll_id` / `poll_weight` | DEFAULTS | — | **OFF** (weight 0); `polls.json` has no machine-readable date |
| `polling_lean` / `polling_span` | DEFAULTS | JUDGED | superseded by poll_weight, still wired |

---

## 3. Entrants — parties with no baseline

| Piece | Where | Source | Saw |
|---|---|---|---|
| `entrant_prob` = 0.25 | DEFAULTS | **JUDGED** — an entrant appeared in **5 of 5** transitions | the record incl. targets |
| `entrant_share` = [0.01, 0.04, 0.12] | DEFAULTS | **JUDGED** — observed 0.35%, 0.31%, 0.78%, 1.51%, **16.05%**; the support **excludes** the largest | ditto |
| Slots | hard-coded **one** | — | 2021 had two (ActionSA 16.05% + PA from 0.03%) |
| Funding | `target *= (1-share)`, proportional from everyone | **JUDGED** | contradicts measured flow (ANC −0.381, EFF −0.262, DA **+0.199** per point of ActionSA) |
| Geography (`entrant_geography`, k) | DEFAULTS | MEASURED (k = 0.03 MK, 0.05 EFF, 1.00 ActionSA) | **OFF**; k saw 2021, 2024 |

**Splinter ≠ entrant.** The splinter branch does `if party not in index: continue`
and `index` comes from the *base* election, so a party with no base can never
reach it. COPE at 2011 is a splinter (9.61% of the 2009 NPE). ActionSA at 2021
is an entrant (0.0000% of 2019). They are different machinery and only one of
them can create a party from nothing.

---

## 4. Geography — where the votes sit

| Piece | Where | Source | Saw |
|---|---|---|---|
| γ per party per ballot | `fold{N}_parameters.csv`, fold precedes the target (asserted) | MEASURED | prior transition ✅ |
| γ fallback | `gamma_recent.csv` | MEASURED | last LGE→NPE before the target ✅ |
| γ default 1.0 | `montecarlo.py` | JUDGED | — |
| `dev` (logit deviation) | computed from the base | DERIVED | prior NPE ✅ |
| Share model `expit(level + γ·dev)` | `solve_and_predict` | DERIVED | — |
| θ calibration (IPF) | `solve_and_predict` | DERIVED | — |
| `SHARE_FLOOR` = 0.002 | `montecarlo.py` | JUDGED | — |
| `level_floor` = 1e-6 | DEFAULTS | JUDGED | 2026 audit |

**Known:** `fit_gamma` is a no-intercept OLS of noisy y on noisy x — regression
dilution, monotone in party size (COPE 0.17 PR / 0.074 Ward against ANC 1.03).
γ carries no uncertainty into the draws. `calibrate_theta` returns 0.0000 for
PA and PAC — a degenerate solution reported as converged.

---

## 5. Turnout — who votes

| Piece | Where | Source | Saw |
|---|---|---|---|
| λ per VD | `turnout.py`, pairs before the target | MEASURED | ✅ |
| `w_recency` = 0.70 | `turnout.py` | JUDGED | 2016 vs 2021 |
| `turnout_pattern_blend` / `_jitter` | DEFAULTS | JUDGED | — |
| `turnout_noise_sd` = 0.08 | DEFAULTS | JUDGED | i.i.d. per VD, so it vanishes citywide |
| `turnout_tilt_anc` / `_da` | DEFAULTS | JUDGED | **OFF**; applied *after* calibration, breaking it |
| κ_bye tilt | `turnout.py` | MEASURED | contests before target ✅ |

---

## 6. Ballots and seats

| Piece | Where | Source | Saw |
|---|---|---|---|
| Ward/PR split ratio | previous LGE, per party | MEASURED | ✅ |
| `ward_pr_ratio_overrides` | DEFAULTS | **JUDGED** | MK 0.80 "bounded by ActionSA's observed 0.77" — 2021 |
| `pa_contestation_uplift` = 1.25 | DEFAULTS | **JUDGED** | PA's 2021 ward count |
| Ward contestation | **not modelled** | — | all parties contest all wards; reality is a median of 26 of 54 |
| `ward_noise_sd` = 0.10 | DEFAULTS | JUDGED | applied to ward tallies, not to shares |
| Schedule 1 quota + largest remainder | `seats.py` | STATUTE | ✅ verified against the IEC, 6 city-years |
| `eligible_parties` (C/D exclusions) | `seats.py` | STATUTE | ✅ |
| `overhang_rule` = deduct | DEFAULTS | STATUTE (Act 3 of 2021) | **anachronistic for 2011/2016** |
| Coalition enumeration | `coalitions.py` | DERIVED | capped at 12 parties while 21 hold seats |

---

## 7. Scoring

| Piece | Where | Source |
|---|---|---|
| CRPS, PIT, coverage, energy, variogram | `score.py` | — |
| Brier + reliability on ward winners | `score.py` | — |
| Ground truth | `backtest.actual_result`, asserted against `official_seats` | ✅ |
| Benchmarks (last-LGE, uniform swing, prior-LGE-noise) | `benchmarks.py` | pre-target only ✅ |

---

## Summary of what is switched off

`splinter` · `pools` · `entrant_geography` · `poll_weight` · `bloc_leak` ·
`turnout_tilt_*` · `w_bye_local_*`

Every one is measured work that does not run. The four backtests reported so
far exercised none of it.

## Summary of what is judged and saw the targets

`theta_mode` · `PLAN_BOUNDS` · `individual_theta` · `f_other` ·
`anc_bloc_shift` · `da_bloc_shift` · `alpha_anc` · `alpha_da` ·
`entrant_prob` · `entrant_share` · `ward_pr_ratio_overrides` ·
`pa_contestation_uplift` · `BLOCS` membership

That is most of the distributional layer. The backtest now prints an in-sample
banner naming these for the target being scored.
