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

Rewritten 2026-08-16. The hand-typed layer this section used to describe —
`theta_mode`, `individual_theta`, `f_other`, `PLAN_BOUNDS` — is gone from the
live path. Every one of them was formed by reading outcomes it would later be
asked to predict. They survive only as a fallback for a party the measurement
cannot reach, and `note_constant` records it in the run's provenance when one is
touched.

| Piece | Where | Source | Notes |
|---|---|---|---|
| **θ** national→local retention | `levels.theta_record` | MEASURED, 8 metros, strictly pre-target | 235 observations at 2026 |
| **ρ** local→local retention | `levels.local_record` | MEASURED, consecutive LGE pairs | the second route |
| **The spine** — blend of the two | `levels.spine` | MEASURED, `k = 1.0` fitted leave-one-metro-out | weight on the LOCAL route is `k/(worth+k)` |
| Size-dependent centre | `levels.size_centre` | MEASURED, `log θ = a + b·log(size)` | small parties gain locally (1.31 at <0.2%), large lose (0.94 at >10%) |
| Per-party spread | `levels.theta_prior` | MEASURED size-dispersion line | 0.19 at 40% of the vote rising to ~0.9 at 0.1% |
| by-election deltas | `byelections.py` | MEASURED, contests before the target | **inert in every backtest** — the scrape covers 2022-06 to 2026-02 only |
| `w_bye` = 0.40 | DEFAULTS | **JUDGED** | live in 2026, untestable historically |
| **Metro polls** | `polling.py` | MEASURED + inverse-variance blend | σ_poll = 3.03pp, a TRACK RECORD not a nominal margin |
| **National polls → metro** | `polling.metro_estimate` | MEASURED conversion | national share ÷ contested area's share of the national vote |

**The spine.** A party's level comes from BOTH its previous national result (× θ)
and its previous local result (× ρ), weighted toward the local route by
`k/(worth+k)` where `worth` is what that party's own θ record is worth. A party
with no θ history sits on its own last local result; one with a long record sits
on the national route. Held out one metro at a time: RMSE(log) 0.236 against the
national spine's 0.275.

**Polls are blended by PRECISION, not by how much history a party has.**
`w = (1/σ_poll²)/(1/σ_poll² + 1/σ_model²)`. At Johannesburg 2016 that gives the
ANC 0.92, the DA 0.86, the EFF 0.34 — and a 2% party 0.19, because a poll of
1,500 cannot resolve a 2% party better than the model can. A poll must declare
the election it was taken for, or fall inside a 550-day window; one that cannot
be dated is refused.

**The centres BIND.** `pool_spec` balances the pool × party matrix by IPF
(`pools.balance_margins`) so each party's *expected* citywide share IS its
centre. Before this the centre only set a party's share of its own pool, which
for a dominant party is almost no leverage — the ANC's centre could move 15% and
its realised share barely at all.

---

## 3. Arrivals and first local elections — parties with no local record

There are TWO classes here and they behave completely differently. The dividing
line is not novelty; it is whether a **national election has already measured the
party**.

| class | definition | how it is sized | how well it works |
|---|---|---|---|
| **First local election** | has a national baseline, never faced an LGE | `pools.first_local_election`: national base × parent θ × ward reach × coherence | **78% within a factor of two**, 45 cases, median ratio 0.85 |
| **Arrival** | no national vote at all | `pools.arrival_rules`: the arrival record, or a splinter fraction of its parent | **22% within a factor of two**, 7 of 32 |

**So the model is good at NEW parties and bad at UNKNOWN ones.** MK in 2026 is
in the first class (12.2% of Johannesburg's 2024 national vote, seeded at 8.18%),
as are RISE and BOSA. ActionSA in 2021 was in the second (no 2019 national vote
at all) and the model gave it 6.9% against 18.12%.

| Piece | Where | Source | Notes |
|---|---|---|---|
| `entrant_prob` = 0.25 | DEFAULTS | **JUDGED** | a party arrived and won seats in **3 of 3** Johannesburg elections; this is the most quotable undefended constant in the model |
| `entrant_share` = [0.01, 0.04, 0.12] | DEFAULTS | **JUDGED** | expected mass 1.42% of the ballot |
| Slots | **one** generic ENTRANT | — | reality delivers 11 to 32 arrivals per metro |
| `SPLINTER_PARENT_WEIGHT` = 0.35 | `pools.py` | MEASURED, 22 splinter-metro cases | a splinter's vector is 35% its parent's and 65% the city average |
| `MIN_HOME_SPLITS` = 2 | `pools.py` | **JUDGED** | binary home/away where ActionSA shows a gradient (0.611/0.315/0.289/0.103) |
| `coherence` | `judgements/` | **JUDGED**, default 1.0 | the largest single lever: COPE 0.12 against the EFF 1.26, and nothing measurable separated them beforehand |
| `SPLIT_SD_FLOOR` = 0.90 | `pools.py` | **JUDGED floor** on a measured spread | binds at target 2016 where the pooled record's log-sd is 0.286 |
| Ward reach | `levels.contestation` | MEASURED, nomination lists | corr(reach, log vote) = **+0.393** for arrivals; seat-winners have median reach 99% against 33% |
| Arrivals as a group | `pools.arrival_group_spec` | MEASURED | **BUILT AND NOT ADOPTED** — scored worse; see MODEL-LOG |

**What is measured about arrivals as a class.** They take between 1.53% and
19.99% of a metro's vote (median 7.21%) and **130 of 1,752 seats in the
nine-city sample — 7.4% of every chamber**. A single slot at 25% probability
cannot represent that, and the group mechanism that could was measured and
rejected because the group total may only be fitted on the previous cycle, which
2021 superseded.

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

`entrant_geography` · `w_bye_local_*` · `arrival_group_draw` · `polling_lean`

`poll_weight` has LEFT this list: metro polls now blend automatically for any
target that has one, and `polls.json` carries machine-readable fieldwork dates.
`arrival_group_draw` is off because it was built, measured and rejected — it
scored worse, for a reason recorded in MODEL-LOG rather than guessed at.

Two things are switched ON but cannot be exercised by any backtest, and must be
labelled as argued rather than tested wherever they are quoted: `w_bye` (the
by-election scrape covers 2022-06 to 2026-02, so no past target has any) and the
15% under-bias correction on the first-local-election path (44 of its 45 cases
fall at 2021, so a backtest there has one prior case to fit on) — the latter
identified but NOT applied.

`pools` runs by default — `run_model` loads
`data/processed/{city}/pools_{target}.json` when the scenario does not carry
pools, and prints the provenance and any pool whose members are unidentified.
When the file is absent the run stops: there is no second engine to fall back
on, so a missing spec cannot silently become a different model. It also refuses
a spec whose pools would hold no registered voters at all, which a ward-code
mismatch across a delimitation produced for Tshwane 2026.

## Summary of what is judged and saw the targets

`entrant_prob` · `entrant_share` · `coherence` · `MIN_HOME_SPLITS` ·
`SPLIT_SD_FLOOR` · `LEVEL_DF` · `level_sd_default` · `w_bye` ·
`ward_pr_ratio_overrides` · `pa_contestation_uplift`

`theta_mode`, `PLAN_BOUNDS`, `individual_theta` and `f_other` have LEFT this
list as live constants — the spine measures the level from transitions strictly
before the target, and they remain only as a fallback for a party the
measurement cannot reach, with `note_constant` recording any run that touches
one.

The hand-drawn party grouping is gone entirely. Parties are described by pool
vectors measured from ward demographics and bounded by what the arithmetic can
prove; lineage for a party with no measured vector is declared in
`judgements/{city}-{target}.toml`, and a splinter's vector is now 35% its
parent's and 65% the city average rather than pure inheritance.

Every one of these is listed with its evidence, its status and how to check it
in **`JUDGEMENT-CALLS.md`**, which is the register; this is the map. The
backtest prints an in-sample banner naming the ones a run actually consumed.

## Where the reasoning lives

| file | what it holds |
|---|---|
| **MACHINERY.md** | this map — every calculation, in order, and where its numbers come from |
| **JUDGEMENT-CALLS.md** | the register of choices the data did not force, each with status and evidence |
| **MODEL-LOG.md** | the append-only record: findings, obstacles, decisions, what was rejected and why |
| **ITERATING.md** | the terms of the exercise — what counts as better, and what the published forecast is not |
| **DATA-QUALITY.md** | every defect in the inputs |
| **SOURCES.md** | where each input came from |
| source docstrings | the reasoning for a specific mechanism, next to the code that runs it |

A change to a mechanism belongs in the docstring AND here. A change to a
*number* belongs in JUDGEMENT-CALLS.md. A finding — including a rejected one —
belongs in MODEL-LOG.md.
