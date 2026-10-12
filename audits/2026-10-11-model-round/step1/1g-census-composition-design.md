# 1g. Census as composition only: what the rule gets right, and the change it implies

Read-only design, 2026-10-11, branch `remediation`. Nothing under `data/` was written; no `montecarlo.py`, `compare_history.py` or `--emit` run. Every number below came from scratch scripts that call `pools.pool_counts` in process and capture the inputs of its three `_nest_holding_silent` solves, then re-solve them with `pools._nest` / `pools._nnls` / `pools.fit_joint` under variants. Scripts and raw output: `/private/tmp/claude-501/-Users-simondavis-projects-atlas-jhb-election-model/4d474bc9-5cd8-4783-ae76-e5d72dbc3c81/scratchpad/census/` (`variants.py` → `run1.txt`, `invariance.py` → `run2.txt`, `sweep.py` → `run3.txt`, `partyfit2.py` → `run4.txt`, `cvhold.py` → `run5.txt`, `inv2.py` → `run6.txt`).

**Measured** = computed in those runs or read in code. **Argued** = reasoned, not run.

**The ward-fit diagnostic** used in §0 and §c is not the backtest. It fits `fit_joint` party-by-pool rates on one election's `composition("voted")` under each variant, then reports the vote-weighted RMSE of ward party shares (pp) in that election (in-sample) and in the next one, using that election's own composition under the same variant (out-of-sample, "OOS"). The party set is the intersection of the two elections' parties, renormalised, so OOS RMSE is inflated by party turnover (Johannesburg 2016→2021 is above 21pp for every variant). It compares variants against each other on real ward results, and no more: no θ, no IPF, no seats, no draws.

Variants used throughout:

| name | registration step | census magnitude in the split |
|---|---|---|
| V0 | as shipped: `registered = _nest(voting_age, roll, upper=REGISTRATION_MAX)` | between-ward pattern of census adults, plus the level wherever the bound binds |
| strict / V1 | the owner's rule as stated: parent = voting-age composition × ward roll, so `registered_wg = s_wg × reg_w` | none |
| V1b | V1 with no age step (`s = comp`) | none |
| V2 | registration rate fitted on the ratio roll / census adults, weighted by the roll instead of by census adults | pattern only, different weights |
| V2a | adult share fitted on ward adult *proportions* (roll-weighted), registration as V0 | as V0 |
| unbounded | V0 with no upper bound on registration | pattern only |
| P_hold | unbounded, plus pools reaching < 25% of any ward held at the city's own rate | pattern for identified pools; level for held pools |
| P_cv | unbounded, plus pools whose free registration rate has coefficient of variation > 1 held at the city's own rate | same, with a different identification test |

---

## 0. Verdict: where the rule is right and where it is wrong

The rule bundles three different uses of census head counts. They need different answers.

**Why "parent = composition × roll" removes the registration rate entirely (algebra, exact).** With the roll as both parent and observation, the registration fit is `reg_w ≈ Σ_g (s_wg · reg_w) · r_g`. Because `Σ_g s_wg = 1`, `r = (1, …, 1)` fits every ward exactly. A per-group registration rate cannot be identified without a denominator that differs from the numerator, and census adults is the only one the project holds. Under the rule, the registered split *is* the census voting-age composition: V1. Re-weighting the fit cannot get around this.

**A census level error that is the same in every ward cancels from the split (measured).** If one group's census count (people and adults) is scaled by k in every ward, its fitted registration rate scales by 1/k and the registered split does not move. Runs 2 and 6 scaled each group by ×0.5 and ×1.5, re-solving the full chain without a bound:

| city-year | largest move in any pool's registered share, across 4 groups × 2 scalings, no bound |
|---|---|
| joburg 2021 | 0.10pp |
| capetown 2016 | 0.06pp |

So the PES over-adjustment (DATA-QUALITY §11) and a city-wide fall in a group's population between the fitting year and 2022 reach the split only where something stops that cancellation. `REGISTRATION_MAX` is one such thing. With the bound at 2.0, joburg 2021 White ×0.5 drives the White rate to the bound and moves White registered from 25.2% to 19.7%, and White voted from 31.8% to 26.2% (run2). Unbounded, the same perturbation moves it 0.06pp.

| use of census head counts | rule verdict | evidence |
|---|---|---|
| **Ward and pool size** (ward registered and voted totals, pool size at target) | **Right, and already obeyed.** No change. | `_nest` rescales every ward to the roll and to votes cast (pools.py:930-934). `registered_at_target` multiplies the target roll by a composition (pools.py:3238-3239). The invariance table above shows no census level reaches a split while nothing binds. Measured. |
| **Census level** (a group's total: PES adjustment, 2022 dating) | **Right.** The level must not reach the split, and it does so only through the bound. | Run2: joburg White ×0.5 moves 25.2% → 19.7% with the bound and 0.06pp without it. Measured. |
| **Between-ward pattern of census adults as the parent of the registration fit** | **Wrong if it means removing the census adults from the fit.** This pattern is information the roll lacks: the roll has no population group and no denominator. | Algebra above. Strict (V1) moves joburg 2021 White registered 25.2% → 15.1% and voted 31.8% → 21.4% (run1). Ward fit, strict against V0, by city (run4, in-sample / OOS pp): **worse** in joburg (13.04/15.98 vs 10.25/12.66 at 2011→16), tshwane (11.56/15.20 vs 7.63/11.68 at 2011→16), ekurhuleni (12.90/14.06 vs 10.12/9.68 at 2011→16), mangaung (all three transitions, OOS +1.3 to +1.5) and capetown (OOS +0.3 to +0.9 in all three); **better** in nelsonmandelabay 2011→16 and 2016→21 (OOS 13.28 vs 14.39, 12.18 vs 13.69); **flat** in ethekwini (OOS −0.5 to +0.06) and buffalocity (mixed, ±0.3). OOS worse in 19 of 24 transitions. Measured, on the diagnostic, not on `compare_history`. |
| **Weights of that fit** (census adults² vs roll²) | **No change warranted.** Changing the weights alone barely moves the result. | V2 vs V0 OOS: joburg 2016→21 21.31 vs 21.25, 2011→16 12.62 vs 12.66; capetown 2011→16 8.14 vs 8.73, 2016→21 10.82 vs 10.60 (run1). Mixed, small. Measured. |
| **`adult_share` from census people** (adults / people per pool) | **Already composition.** It is a ratio of two counts from one census, i.e. the ward's age mix, and no roll quantity is involved. It survives only as the shape of the registration denominator. | V1 vs V1b (age step on or off) differ by about 1pp of White registered at joburg 2021 (15.1% vs 13.9%, run1). Fitting it on proportions with roll weights (V2a) moves joburg 2021 White registered 25.2% → 24.7%. Measured. No consumer of `rates["adult_share"]` outside pools.py and tests (grep). |
| **Turnout fit** | **Already compliant.** The parent is the roll-anchored `registered`. | pools.py:1501-1502. Measured from code. |
| **`REGISTRATION_MAX`** | **Right to remove.** It is the one site where the census level reaches a split. **But what replaces it is a judgement:** see §c. | Run2 above, and run3: the bound binds on capetown Indian/Asian 2011 and 2016 and mangaung Indian/Asian 2016 and 2021, matching JUDGEMENT-CALLS §L9's four cells. Measured. |

**What the census adds, and where it is weak (argued).** The registration fit attributes ward-to-ward variation in roll ÷ census adults to the groups living there, one rate per group (DATA-QUALITY §11, cause 3). Part of what it attributes to "White" at Johannesburg may be an area effect: established suburbs where everyone registers at a higher rate. The ward-fit gain does not separate the two, because both make the voted composition track DA wards. That is a limit of the ecological fit. It is not a size use, and the strict rule would not fix it; it would replace it with an assumption of equal registration, which the ward results reject in the Gauteng metros and Mangaung.

**The rule is right for one more case: a pool the ward table cannot identify.** There the only information about the pool's registration is the census level, and holding it at the city's rate is the composition rule applied pool by pool. §c specifies it.

---

## a. The parent of each nested fit

| level | today (pools.py) | specified | why |
|---|---|---|---|
| people | `people = comp × census people_w` (1467) | **unchanged in what it computes**, documented as the age-step parent only | its magnitude enters only the `adult_share` regression weights, and every ward is rescaled to census adults (1483). Census against census, i.e. age composition. |
| voting age | `_nest_holding_silent(people, census adults_w)` (1480-1483), rate `adult_share` ≤ 1.0 | **unchanged.** Optional V2a (proportion form, roll weights) is listed in §g and not recommended alone. | `voting_age_wg = adults_w · comp_wg a_g / Σ_h comp_wh a_h`, so census people magnitude cancels out of `voting_age` entirely, leaving only the adult *proportion* fit. Measured effect of V2a: ≤ 0.5pp. |
| registered | `_nest_holding_silent(voting_age, roll_w, upper=REGISTRATION_MAX)` (1497-1500) | **parent unchanged (census adults by pool, roll-rescaled). Upper bound removed. A pool the fit cannot identify is held, or partially pooled (§c).** | the census adults are the only denominator that identifies differential registration (§0). The bound is the only level channel. |
| voted | `_nest_holding_silent(registered, votes_w)` (1501-1502) | **unchanged** | parent is already roll-sized. |

The adult step does not drop out. Under the rule, voting-age composition is a census proportion, and it is already applied as one: `voting_age` depends on census people only through the proportion fit.

---

## b. Identification and the per-pool shares, before and after

**Identification (measured, run3).** Unbounded, the registration rate is identified wherever a pool's census share varies across wards. Coefficient of variation of the free rate, from the unconstrained least-squares curvature (`sqrt(diag((AᵀA)⁻¹)·σ²)/r`, level-free because it scales with r):

* joburg, all four fitting years, every pool: CV ≤ 0.57; no bound binds.
* capetown Indian/Asian: CV 0.21-0.25 at reach 20.4-21.2%. The fit calls it identified, at rates of 1.90 / 2.13 / 2.26 / 1.93.
* mangaung Indian/Asian: CV 1.96 to 12.2 at reach 2.0-2.4%. Not identified.
* tshwane Indian/Asian 2006, 2011: CV 2.17, 1.69 at low rates (0.096, 0.161), not on a bound.

**Johannesburg 2021 (measured, run1).** Share of the city's registered roll / votes cast, per pool:

| variant | Black African | Coloured | Indian/Asian | White | rates (registration) |
|---|---|---|---|---|---|
| V0 (shipped) | 64.8 / 56.7 | 5.5 / 7.2 | 4.5 / 4.4 | 25.2 / 31.8 | 0.432 / 0.765 / 0.775 / 1.739 |
| recommended (bound removed; identification hold) | 64.8 / 56.7 | 5.5 / 7.2 | 4.5 / 4.4 | 25.2 / 31.8 | identical: nothing binds, nothing held |
| strict (V1) | 74.8 / 66.3 | 5.1 / 6.9 | 5.0 / 5.5 | 15.1 / 21.4 | none (equal registration) |
| V2 | 66.8 / 58.7 | 4.7 / 6.3 | 4.2 / 4.2 | 24.3 / 30.9 | 0.578 / 0.730 / 0.802 / 2.076 |

**Cape Town 2021 (measured, run1, run3).**

| variant | Black African | Coloured | Indian/Asian | White | Indian/Asian rate |
|---|---|---|---|---|---|
| V0 (shipped) | 33.6 / 23.6 | 35.7 / 36.0 | 7.8 / 8.9 | 23.0 / 31.5 | 1.932 (under the bound) |
| unbounded = P_cv | 33.6 / 23.6 | 35.7 / 36.0 | 7.8 / 8.9 | 23.0 / 31.5 | 1.932 |
| P_hold (reach < 25%) | 33.6 / 23.6 | 38.1 / 38.6 | 2.7 / 3.3 | 25.7 / 34.4 | 0.587 (city rate) |
| strict (V1) | 36.9 / 26.2 | 37.6 / 38.8 | 2.8 / 3.5 | 22.7 / 31.6 | n/a |

Cape Town at the two bound-binding fitting years (run3, run5), registered share of Indian/Asian: 2011 9.3% (V0) → 9.8% (unbounded / P_cv) or 2.8% (P_hold); 2016 8.3% → 9.2% or 2.7%. The held pool's share goes to Coloured (+2.7 to +3.3pp) and White (+2.9 to +3.4pp); Black African is unmoved.

**What the NNLS fits become.** The registration solve keeps its form, with `upper=np.inf`, so the bound never binds. `_nnls`'s projected gradient with an infinite upper bound is the non-negative least-squares fit. Unbounded runs converged at mangaung (rate 4.34, run1 V3) and in every other city-year swept. A pool held under §c enters `_nnls` through the existing `hold` argument, the same path L14 uses.

---

## c. `REGISTRATION_MAX`: what replaces it

**It is still needed for one job: stopping a runaway rate on a pool the ward table cannot see.** Removing it outright (the "unbounded" variant) is rejected on measurement: mangaung OOS worsens at every transition (12.35 → 12.47, 9.75 → 10.28, 11.29 → 11.37; run4), and the mangaung Indian/Asian rate runs to 4.34 (2016) and 3.27 (2021), giving that pool 3.3% of the roll against a census population share near 0.7%.

**Specified replacement (two parts):**

1. **No upper bound on registration** for a pool the fit identifies. Under §0's invariance this makes the registered split independent of every group's census level.
2. **A pool the fit cannot identify does not take its free rate.** It takes the composition rule: the city's own rate (`_uninformed_rate`, as L14), or entry 31's partial pooling once that lands (§h). It is recorded in `imputed["registration"]` and in `unidentified`, so `panel_turnout_spread` excludes its transitions (pools.py:3057-3064 already reads every `imputed` level).

**What counts as "cannot identify" is a judgement the data does not settle, and the two tests disagree on Cape Town.** This goes to the owner as it stands:

| test | capetown Indian/Asian (reach 20-21%, CV 0.21-0.25) | mangaung Indian/Asian | tshwane Indian/Asian 2006, 2011 | ward fit vs V0, OOS (run4, run5) |
|---|---|---|---|---|
| **reach < 25%** (the threshold already in the `_at_bound` message, pools.py:1554) | held: 7.8-9.9% → 2.7-2.9% of the roll | held | not held | capetown 20.15 vs 20.01, 8.88 vs 8.73, 10.51 vs 10.60; buffalocity 2006→11 14.04 vs 12.96; mangaung 12.34 / 9.59 / 11.27 vs 12.35 / 9.75 / 11.29. Also holds ekurhuleni 2006/2011, nelsonmandelabay 2006-2016 and buffalocity, all Indian/Asian. |
| **CV > 1** | not held: 8.3% → 9.2% (2016), 9.3% → 9.8% (2011) | held | held: 0.5% → 2.1%, 0.8% → 2.3% | capetown as unbounded (20.07, 8.71, 10.69); mangaung as P_hold; tshwane 11.65 vs 11.58, 11.84 vs 11.68 |

Neither test wins on the ward fit. The reach test treats a precise but implausible estimate as unidentified: Cape Town's Indian/Asian pool at 8-10% of the roll against 1.61% of the census population (prereg 2026-09-25 C2) would need a registration rate about five times the Black African one. The CV test trusts the fit's precision, which is precision under a misspecified ecological model. **Disagreement is the finding; it is not split here.**

**Both threshold tests have a cliff (measured, run6).** At mangaung 2016, scaling the Black African census by ×0.5 flips the Indian/Asian pool from held to free and moves a pool share by 5.97pp. A continuous rule, partial pooling weighted by identifying variation (entry 31, D2), has no cliff. That is the argument for making entry 31 the replacement rather than a threshold hold. Argued.

**A held pool carries the census level, by design.** Under P_cv, scaling the held pool's own census by ×0.5 / ×1.5 moves splits 0.34-0.40pp at mangaung 2016 and 0.88-0.99pp at tshwane 2011 (run6). Where the ward table is silent, the census level is the only information there is, and that is the rule's own premise.

**Measured on the panel (run3, P_hold column; run5 for P_cv).** No `registration` cell in joburg, tshwane, ekurhuleni or ethekwini is on the bound. Under either test, joburg's 16 pool-years are numerically unchanged.

---

## d. Downstream consumers and what changes

| consumer | file:function | change |
|---|---|---|
| registration solve | pools.py:1497-1500 `pool_counts` | `upper=REGISTRATION_MAX` → `upper=np.inf`, plus the identification hold (§c) |
| constant | pools.py:886-914 `REGISTRATION_MAX` | deleted; its comment block moves to the new identification helper and JUDGEMENT-CALLS |
| bound detector | pools.py:1536-1563 | registration tested against the lower corner only (`level_upper = np.inf`). New message for the identification hold (test, value, the rate it replaced). |
| `census_correction` | pools.py:1508-1510 | formula unchanged. Its values change only where a pool is held or was bound. Report only: no consumer outside pools.py (grep, measured). |
| `violations` | pools.py:1566-1580 | unchanged in code. With the bound gone, capetown Indian/Asian registered ÷ adults rises (2.13 / 2.26 under P_cv), or falls to the city rate under P_hold. |
| `imputed` / `unidentified` → spec `rates_on_a_bound` | pools.py:1488-1534, emit 6507 | held registration pools listed. Under P_cv the field gains tshwane Indian/Asian at 2006 and 2011 and loses the four capetown/mangaung `registration at 2.0000` lines (mangaung reappears as held). |
| `registered_at_target` | pools.py:3221-3335 | reads `composition("registered")`, so it moves wherever the split moves: capetown 2016/2021 targets (fitted 2011/2016) and the mangaung targets; joburg unchanged. Same whether or not entry 32 lands, because 32/D3 still takes the target composition from this solve. |
| `registration_series` → `projected_pool_shares` → spec `pool_shares_at_target` | pools.py:1670-1717, 5961-5963 | every prior election's registered split; same cells as above, plus 2006 fits (tshwane under P_cv) |
| `turnout_record` → `turnout_band` → spec `turnout` triple | pools.py:2832-2872, 6006 | turnout is re-fitted on the new registered split. Under P_cv the capetown Indian/Asian turnout moves 0.655 → 0.656 (2016) and 0.671 → 0.670 (2011). Under P_hold the capetown Coloured and White turnouts shift by up to 0.01. Measured, run1 V3 and run3. |
| `panel_turnout_spread` | pools.py:2986-3080 | transitions touching a held pool drop out. P_cv adds tshwane Indian/Asian 2006→2011 and 2011→2016. This moves the pooled Indian/Asian spread for every city that falls back to the panel (`_OWN_EVIDENCE_MIN_OBS`). Argued small; must be measured in the window. |
| party fits `fit_city` → spec `pools[*].members` | pools.py:2629-2660 | `composition("voted")` changes in the same cells, so the party-by-pool weights there are re-fitted |
| runtime pool geography | montecarlo.py:4485 `_pools.pool_counts(...)` | **re-computed at every model run, not read from the spec.** Between landing and re-emit, the stale-spec refusal stops runs, so no mixed state is reachable. Note it in the queue row anyway: this consumer moves even without an emit. |
| capacity test | tests/test_pool_bounds.py:333-407 (`votes = registered × turnout[1]`) | under P_hold, capetown Indian/Asian `registered` falls about threefold, which shrinks that pool's `pool_hi`. Whether a seed the DA or Al Jama-ah needs in that pool becomes infeasible is a falsifier (§f), not asserted here. |

**Tests that pin the changed quantities (measured by grep and by reading):**

* `tests/test_pool_bounds.py::test_the_registration_bound_is_per_level` (539-588). Assertion (2) `reg <= REGISTRATION_MAX` stops compiling. (3) `seen_above_one` stays green (joburg White 1.739). (4) mangaung 2016 `unidentified` non-empty stays green only if the hold writes to `unidentified`. Rewrite: (2) becomes "registration has no upper bound and an identified pool's split is invariant to its census level" (the run2 construction, on a constructed table per CLAUDE.md §4 part 3); (4) asserts mangaung Indian/Asian is *held*, by name, as data.
* `tests/test_pool_bounds.py` `_p1_violations` / the no-silent-pool scan (740-775) asserts the hold fires at the `registration` level somewhere. Today that is mangaung 2006 only (§L14). Under P_cv it is mangaung at all four years and tshwane 2006/2011, so the population behind the assertion changes. State the new population in the test. It must stay two-sided (CLAUDE.md §4 part 1).
* `tests/test_chain.py:360-386`: ordering and violation-reporting tests. Unaffected in direction; the joburg fixture does not move.
* **New, four-part:** (i) invariance: for each identified pool in a constructed table, ×0.5 and ×1.5 on its census column move the registered split < 1e-3; it must turn **red** when `upper=2.0` is restored (mutation). (ii) The identification test holds a constructed unidentifiable pool, and goes quiet when that pool is given identifying variation. (iii) Population: the set of held cells is printed and bounded two-sided over the declared fitting years.
* `tests/test_register_matches_code.py` (the register guard): `REGISTRATION_MAX` leaves the register in the same commit, and any new named constant (the CV or reach threshold) enters it.

**Documents, same commit (CLAUDE.md §2):** JUDGEMENT-CALLS §L9 superseded (status line, pointer to the new entry), §L14 extended (held at the lower corner *or* unidentified), DATA-QUALITY §11 "where it does not" open item closed with a pointer, `prereg/2026-09-05-registration-rate-bound.md` scored, the `PoolCounts` and `pool_counts` docstrings, and MACHINERY.md around 664-675 (checked by grep: it describes the 0.0 corner hold, so it needs the new case). MODEL-LOG gets the invariance finding and the strict-rule rejection.

---

## e. The census-date leak

Composition-only does not shrink the leak's reach. Composition is the leaked quantity: 2022 shares back-dated onto 2006-2016 wards (`1d-census-date.md` §2), and the rule keeps it. What the change removes is the bound's level channel. Because a group-uniform level error cancels in the split (§0, measured), a city-wide change in a group's size between the fitting year and 2022 is already absorbed by that group's fitted rate, except where `REGISTRATION_MAX` binds. Johannesburg White's registration rate rising across fitting years (1.272 / 1.382 / 1.711 / 1.739 at 2006 / 2011 / 2016 / 2021, run3) is consistent with that absorption, with the census adult count held at 2022 while the White population fell (MODEL-LOG "the owner's three observations", reported 12.3% → 7.0%). Consistent, not shown: the roll also changed. The two bound-binding Cape Town cells are the 2011 and 2016 fitting years, so removing the bound removes the dated level from exactly those cells. Measured that they bind; argued that the cause is dating.

What remains: the ward-differential part, meaning wards whose group mix changed between the fitting year and 2022 (out-migration from particular suburbs, informal settlement growth). That reaches the split, the turnout record and the party fits at every pre-2021 fitting year, and only a Census 2011 entry with a date filter fixes it (`1d-census-date.md` §6). This change does not touch it.

---

## f. Predicted effect, falsifiers

**Johannesburg 2026 (fitted on 2021).** Nothing binds and nothing is held, so `registered`, `pool_shares_at_target`, the turnout triple and `members` are unchanged within 0.1pp. Measured at the `pool_counts` level (run3: joburg 2021 rates and shares identical under P_hold; run5: no joburg cell held under P_cv). One indirect path: the panel turnout spread, if P_cv drops the tshwane Indian/Asian transitions and joburg's Indian/Asian band falls back to the panel. Argued small.

**Panel (argued from the pool-level runs; not a backtest).**

* capetown 2016 and 2021 targets: under P_cv, Indian/Asian registered +0.5 to +0.9pp; essentially unchanged. Under P_hold, or under entry 31 if it shrinks toward the census, Indian/Asian falls by 5 to 7pp of the roll, with Coloured and White up about 3pp each. The pooled DA/Al Jama-ah weight in the Indian/Asian pool must then relocate. Prereg 2026-09-25 P6 predicts Cape Town ward calls move by at most one ward.
* mangaung all targets: Indian/Asian registered about 1.5-1.8% → 0.6-0.7%, the other pools up 0.2-0.6pp.
* tshwane 2011 and 2016 targets (P_cv only): Indian/Asian 0.5-0.8% → 2.1-2.3%, taken from Black African (−0.7 to −0.8pp) and White (−0.6 to −0.7pp).
* Pools identified everywhere (joburg, ekurhuleni 2016/2021, ethekwini, most of the rest): unchanged within 0.1pp.

**Falsifiers.**

1. After the change, an identified pool's registered split moves more than 0.1pp when its census column is scaled ×0.5 or ×1.5 in any city-year. The level channel has then not been closed.
2. Joburg 2026 `registered` or `pool_shares_at_target` moves more than 0.5pp for any pool. That would be an unintended path.
3. The paired backtest (prereg 2026-09-25 D5) shows a net CRPS loss at the city-years this touches (capetown, mangaung, tshwane under P_cv) with no change elsewhere. In that case the bound was doing useful work that §0's argument missed.
4. The capacity scan (`test_pool_bounds` 333-407) gains a fatal cell in capetown's Indian/Asian pool under P_hold. A smaller pool then cannot hold the votes the party fit gives it, which would say the 8-10% was carrying a party's votes for a reason.
5. For the strict rule (rejected): a backtest showing V1 better than V0 on votes at joburg, tshwane and ekurhuleni would overturn §0. The ward-fit diagnostic predicts the opposite at OOS margins of 1.5-4.4pp at 2011→2016.

---

## g. Judgement calls introduced or removed

| call | status | entry |
|---|---|---|
| `REGISTRATION_MAX = 2.0` | **removed** | JUDGEMENT-CALLS §L9 superseded. It was "deferred, not defended". |
| the identification test for a registration rate (reach < 25%, or CV > 1, or entry 31's continuous weight) | **introduced**: the owner's decision, §c | new §L-entry, or folded into entry 31's D2 entry. The threshold must be named in code so the register guard sees it (MEMORY: naming a constant exposes it). |
| what an unidentified pool's registration takes (city rate vs panel-pooled rate) | **extended** from §L14 (lower corner only) to unidentified pools | §L14 amended. ⚠️ A *panel-pooled* registration rate is in units of registered per census adult, so it carries each city's census level into the others. The city rate keeps the level local. Entry 31's D2 must say which it pools: rates, or shares of the roll. |
| equal registration across groups (the strict rule) | **considered and rejected** | rejected-claims table below; MODEL-LOG entry |
| adult share fitted on proportions with roll weights (V2a) | **not introduced.** Optional. Moves joburg White registered 0.5pp with no measured gain. | if adopted, a one-line §L note on the weights |

### Rejected claims

| claim | evidence that rejects it |
|---|---|
| "Census head counts set the pool size" | Ward totals are forced to the roll and to results (pools.py:930-934). A group-uniform census scaling moves the unbounded split ≤ 0.10pp (run2, run6). |
| "Making the parent composition × roll keeps the registration fit, re-weighted" | `Σ_g s_wg = 1` gives the exact solution r = 1. The rule removes differential registration (algebra; V1 in run1). |
| "The census-weighted fit should be roll-weighted" | V2 vs V0 OOS differences are mixed and ≤ 0.6pp (run1). |
| "`REGISTRATION_MAX` lets the census override the roll" | The roll has no group, so no counted quantity is overridden. What the bound does is let a group's census *level* set a split (run2: 25.2% → 19.7%). That is the defect, under a different description. |
| "Remove the bound with nothing in its place" | Mangaung OOS worse at all three transitions; Indian/Asian rate 4.34 (run4, run1). |
| "Composition-only reduces the census-date leak" | The leak is in composition; the dated level already cancels except at the bound (§e). |

---

## h. Re-emit

A `pools.py` code change moves `pools_sha` and invalidates every spec (CLAUDE.md §3; POOLS-REEMIT-QUEUE header). It waits for the window and is emitted with the rest of the round.

**Queue entry: an amendment to entry 31, not a new row.** Entry 31 ("Pool levels the ward table cannot identify", prereg 2026-09-25 C2/D2/P2) already queues the treatment for every bound-sitting Indian/Asian rate, `registration` at 2.0000 included, with acceptance "Cape Town's Indian/Asian share of the roll falls below 5% at all three cycles". Its prereg cannot be edited (CLAUDE.md §4), so the amendment is a note on the row in POOLS-REEMIT-QUEUE.md stating:

* **Deletion of `REGISTRATION_MAX`** and `upper=np.inf` on the registration solve, as the prerequisite that makes D2's "cannot identify" a property of the ward table rather than of a bound.
* **The identification test is undecided (§c).** Under the CV test, P2 is falsified by construction (Cape Town Indian/Asian rises to 9.2-9.8%). Under the reach test or a census-shrunk partial pool, P2 can pass. The prereg's prediction therefore depends on a choice it did not fix, and the window must record which test was used before scoring P2.
* **The panel-pooling unit** (rates vs roll shares; §g warning).
* **Interaction with entry 32 (C3/D3):** `registered_at_target`'s composition comes from this solve whichever way 32 lands, so the two are measured together and attributed by the D5 paired run, not separately.
* The montecarlo.py:4485 runtime re-computation, as a consumer that moves without an emit.

Use a separate row (**34**, the next number above both this table's highest, 33, and the frozen brief's) only if the owner wants the bound removed in a window where entry 31 does not land. In that case the interim fallback is the city's own rate (§L14 extended), and the row carries falsifiers 1 and 2 of §f as acceptance. Following the queue's precedent for entries 4 and 11 and R-1 (same functions, one change), the amendment is the right form.

**Pre-register before the window:** falsifiers 1-4 of §f, and the per-city-year L1 dose of `registered` (prereg 2026-09-25 P7), computed from the two artefacts before any model run.
