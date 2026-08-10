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

A **pool** is a body of voters with a measured characteristic, and a party's
membership of it is the share of its vote that demonstrably comes from there.
That is a claim about the electorate, and it can be checked. It replaces a
hand-drawn grouping of parties, which was a claim about parties and could not
be.

| Piece | Where | Source | Saw |
|---|---|---|---|
| Dimension registry (n-dimensional) | `config/dimensions.toml` | — | — |
| Base dimension = population group | Census 2022 ward tables | MEASURED | census pre-dates the 2026 target ✅ |
| Tilt dimensions (age, sex) | same | MEASURED and **REJECTED** by the gate | — |
| Party pool vectors | `pools.fit_city`, shrunk toward `pools.fit_national` | MEASURED, 742 wards / 8 metros | the fitting election only ✅ |
| Lower/upper bounds per rate | `pools.bounds` (Duncan-Davis) | MEASURED, arithmetic only | ✅ |
| Pool ratio ranges | `pools.measure_pool_ratios` | MEASURED, 16 metro transitions | 2011→2016, 2016→2021 |
| Pool α | `pools.dirichlet_alpha` | MEASURED, method of moments, size-weighted | ditto |
| Emitted spec | `data/processed/{city}/pools_{target}.json` | DERIVED | — |

**What the dimensions are for.** A pool is not restricted to race; the registry
takes n vectors (income, education, home language, age, sex). Race is the only
one that has *earned* admission: the base dimension carries the pools and every
further dimension enters as a deviation from the city mean, admitted only if it
improves fit out-of-sample when vectors fitted on one metro are tested on
another. Age gains +0.03–0.06 R² in sample and ~0.00 out of it, because ward
%Black African correlates +0.75 with %aged 20–29 — it is re-describing the base.
Sex has almost no cross-ward variance to identify anything from. Both are fitted
and rejected in the config, with the reason recorded, rather than omitted.

**Why the fit is national.** Ecological inference identifies a group's rate only
where wards vary in that group's share. Johannesburg holds **1** majority-Indian
ward and **3** majority-Coloured; across the eight metros there are **17** and
**63**. Fitted on the city alone, every minority rate was decided by the
regularisation and collapsed to the floor — which read as "the ANC has no Indian
or Coloured supporters", which is false. The national fit supplies the shape,
rescaled to the city's own level, because direction transfers between cities and
magnitude does not (Al Jama-ah is Indian-shaped in both metros, at 0.8% and
0.1%).

**Why nothing is zero.** Every estimate is projected into its Duncan-Davis
interval. Pooled over the metros the ANC's rate among Coloured voters is
provably ≥ 0.4% and among Indian voters ≥ 0.7%; the unconstrained fit answered
0.2% for both — below its own proven floor. Where the bound stays wide (ANC
among white voters, 0–20.4%) the rate is flagged unidentified and is a judgement,
not a finding.

**Time and geography.** Censuses are a decade apart, so composition is
interpolated to polling day in log-share space and damped-extrapolated beyond
the last one. Ward codes are contiguous and *reused* across delimitations, so
Census 2022's 135 Johannesburg codes join the 2011 election's 130 wards at a
perfect 130/130 — every one the wrong polygon. `pools.reproject` goes through
voting districts, which every election file maps to its own wards, and reports
the fraction of the electorate it accounted for.

**Still open.** Population group cannot separate the ANC from the IFP (both fit
as almost entirely Black African) though their measured ground correlates −0.14
— which is precisely the distinction MK turns on. Census 2011 ward tables are
not held, so pools cannot be fitted for the 2011 or 2016 backtests.

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

**Splinter ≠ entrant, and both are now handled.** COPE at 2011 is a splinter
(9.61% of the 2009 NPE); ActionSA at 2021 is an entrant (0.0000% of 2019). The
old branch could reach neither — it looked the party up in the *base* election,
so a party with no base fell through. `pools.emit_pools` instead gives every
baseline party a vector: a splinter inherits its parent's, an entrant takes an
even share of every pool, and `judgements/{city}-{target}.toml` is generated
with the defaults filled in for a human to override. MK, 12.2% of the 2024
baseline, was previously drawn from the residual range at mode 1.30 against a
`theta_mode` of 0.60; `make_drawer` now names any baseline party that reached
no pool instead of absorbing it silently.

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

`entrant_geography` · `poll_weight` · `w_bye_local_*`

Every one is measured work that does not run. The four backtests reported so
far exercised none of it.

`pools` **now runs by default** — `run_model` loads
`data/processed/{city}/pools_{target}.json` when the scenario does not carry
pools, and prints the provenance and any pool whose members are unidentified.
When the file is absent the run stops: there is no second engine to fall back
on, so a missing spec cannot silently become a different model. Correcting the α estimator (it was taking
the median across ~40 members, most of them negligible parties whose shares are
stable because they are tiny, and pinning every pool at the 200 ceiling) widened
the Johannesburg 2026 ANC interval from 68 [60–78] to 67 [36–95]. Measured
coverage had been running at 44–71% against a nominal 90%.

## Summary of what is judged and saw the targets

`theta_mode` · `PLAN_BOUNDS` · `individual_theta` · `f_other` ·
`entrant_prob` · `entrant_share` · `ward_pr_ratio_overrides` ·
`pa_contestation_uplift`

The hand-drawn party grouping has left this list entirely, along with the
shift ranges, leak dial and concentration parameters that hung off it. Parties
are described by pool vectors measured from ward demographics and bounded by
what the arithmetic can prove; lineage for a party with no measured vector (a
splinter inherits its parent's, an entrant takes an even share) is declared in
`judgements/{city}-{target}.toml`.

That is most of the distributional layer. The backtest now prints an in-sample
banner naming these for the target being scored.
