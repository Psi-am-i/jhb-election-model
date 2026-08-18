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
| Party pool vectors | `pools.fit_city`, balanced by **`balance_within_bounds`** | MEASURED, 742 wards / 8 metros | the fitting election only ✅ |
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

**The Duncan-Davis bounds are now ENFORCED, since 2026-08-17.** For most of this
document's life this paragraph claimed "every estimate is projected into its
Duncan-Davis interval" and nothing projected: `pools.bounds` was read at exactly
one place, `PoolFit.identified`, where a narrow bound set a display flag. No rate
was clipped to it, at any stage.

`fit_city` now balances through **`balance_within_bounds`** rather than
`balance_margins` — but tries the unbounded answer first and **returns it unchanged where every rate is already inside its Duncan-Davis interval**. Five of the ten production fits take that pass-through, which matters because the projection is not free: at Ekurhuleni 2016, which had **zero** violations, the old unconditional path cost 0.61% of the ward fit it exists to minimise and moved the DA's Indian/Asian rate 1.00 → 0.90 for nothing. Each half-step scales a row or column by the factor that lands
its *clipped* sum on the known total — a Bregman projection onto a convex set,
the same object as the unbounded half-step — so the fit satisfies the arithmetic
bounds **and** both known margins at once. Across the ten (city, fitting-year)
pairs a production emit uses, the old code emitted **11 forbidden rates**; it now
emits none, with rows exact to 1e-9 and the worst citywide share off by 5.6e-17.

**Both halves are necessary and neither is sufficient**, which is the part worth
remembering. IPF is multiplicative, so a cell at exactly zero is a fixed point:
no iteration can move it, which is why `balance_margins` could never repair a
corner solution. Bounds alone therefore do not converge — a PA capped at 27,183
votes and zeroed elsewhere cannot account for its own 27,346. Seeding alone
leaves the corner untouched, because with no ceiling the Coloured cell absorbs
the whole total by scaling and no votes are ever unplaced. **The bound is what
creates unplaced votes; the seed is only what lets a multiplicative iteration
place them.**

**It was never only the PA.** The worst violation on record is the **DA at Nelson
Mandela Bay 2016: Black African 0.0059 against a proven floor of 0.0312** — 5.3×
below what the ward arithmetic shows it won, with the difference parked in the
White pool. The DA sits below its Black African floor in **four** cities. The PA
case was simply the one whose downstream consequence was loud enough to notice:
its Johannesburg 2021 corner (0.5149 Coloured, exactly 0.0000 on the other three)
implied 34,170 votes against an actual 27,346, and produced the "Coloured 1.0000"
vector that made its 2026 level unrepresentable by the pool layer.

**What it fixed downstream.** The per-draw capacity cap (§2) existed to guard
exactly this. It is now **inert on Johannesburg 2026**: the PA was held at
capacity in 39.2% of draws with a worst ask of 204%, and after the fix nothing is
held in any draw.

**The honest limit.** Projection removes only *refutable* corners. The PA's
non-Coloured share reaches 0.58%, not the ~5.7% its ward geography suggests,
because Duncan-Davis cannot exclude that all 1,173 of its votes in wards under
2% Coloured came from those wards' own 6,674 Coloured voters. Arithmetic forces
only about 159 votes out of the pool. Reaching 6% would require a model, and the model
that does it fits the ward table 20× worse (MODEL-LOG §1.38). The PA at **Cape
Town 2016 is still Coloured 1.0000**, and nothing in that ward table forbids it.

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

## 2a. How a party's level is actually arrived at — the full chain

Written 2026-08-17 after tracing it end to end (MODEL-LOG §1.43). Worked example
throughout: **VF Plus at Tshwane 2021**, which the model put at 4.28% against an
actual 7.79%.

### The two records

`levels.theta_record` and `levels.local_record` each return
`{party: [(ratio, size), ...]}`, pooled over the eight metros and every election
strictly before the target.

* **θ** — `LGE_share(year) / NPE_share(preceding NPE)`, `size` = the NPE share.
  National → local retention. 264 observations at target 2026.
* **ρ** — `LGE_share(later) / LGE_share(earlier)`, `size` = the earlier share.
  Local → local retention. 229 observations.

**The observation is a two-tuple: the metro and the year are discarded.** That is
a real loss — the year explains 8.7% of the residual variance after each party's
own mean is removed, against the metro's 2.5% — and §1.43 measured that
recovering it makes forward prediction **worse**. The loss is now a documented
choice rather than an accident.

### What one observation is worth

`_reliability(share) = share / (share + RELIABILITY_HALF)`, `RELIABILITY_HALF =
0.002` — the old hard 0.2% cut, now a continuous half-point. An observation off
2% of the vote is worth 0.91; off 0.2%, 0.50; off 0.02%, 0.09. A party's
**`worth`** is the sum over its observations. *Three ratios measured off 0.02% of
the vote are three weak statements, not three strong ones.*

### Shrinkage, and what it shrinks toward

`levels._shrunk` is a James–Stein estimator, unnamed in the code:

    weight = worth / (worth + SHRINK)                       SHRINK = 2.0
    mu     = weight * own_weighted_mean + (1 - weight) * target
    target = size_centre(size) = a + b * log(size)

**Both halves are load-bearing and both are measured.** Forward validation:
adding the party term takes RMSE(log θ) from 0.8045 to **0.7150**, so a party's
own record carries real signal; but **unpooled** party dummies score **1.0308**,
worse than having no party term at all. And `SHRINK = 2.0` — never fitted until
§1.43 — is **optimal**: 1.0 scores 314 seat error against 312, 5/9 against 6/9.

`size_centre` fits `log θ = a + b·log(size)` **unweighted** — deliberately, since
the reliability weight would remove the small-party observations that identify
the slope. At target 2021: `a = −0.2466, b = −0.0231`, giving a centre of θ 0.93
at 0.05% of the vote and 0.80 at 45%. **The slope is nearly flat and R² ≈ 0.04**:
it moves the centre by about a quarter across the whole ballot and explains
almost none of the variance around it.

For VF Plus (worth 6.46, weight 0.763): own 0.785, centre 0.868, **result 0.804**.

### The blend

`levels.spine` converts each record into a level and interpolates:

    nat_level = national_share * exp(mu_theta)     6.268% x 0.804 -> 5.040%
    loc_level = local_share    * exp(mu_rho)       1.970% x 1.091 -> 2.149%
    w         = k / (worth_theta + k)              k = SPINE_K = 1.0  ->  0.134
    level     = exp(w*log(loc_level) + (1-w)*log(nat_level))  ->  4.495%

**This is a geometric interpolation, so the result is mathematically confined
between its two legs.** VF Plus's actual 7.79% was above both, and no weight
reaches it. That is the structural limit of the spine and it is worth stating
plainly.

**The weight is keyed on θ evidence alone**, and `_worth_r` from the ρ record is
deliberately discarded. Making it symmetric was tried and is much worse — seat
error 338 against 312, CRPS 280.8 against 264.8 (§1.43).

### From centre to reported number

The level becomes `centres[party]` in `montecarlo.blended_centres`, whose
precedence is `poll_levels` → seeded arrival → `spine_level` → `theta_prior` →
(four dead branches). `pool_spec` then runs IPF so a party's **expected** citywide
share *is* its centre, and each draw applies a Student-t level shock, the
correlated turnout copula and a within-pool Dirichlet.

**The draw adds spread, not information.** Measured at Tshwane 2021, drawn mean
against spine centre: ANC 0.950, DA 0.942, VF Plus 0.956. The forecast is decided
at the blend.

### The level shrink — the last step before the draw

`compress_levels` runs on the finished centre vector, after every route and
after the by-election blend, so it reaches arrivals and poll-led parties as well
as spine ones. Each party keeps

    1 - level_shrink * s / (s + level_shrink_scale)

of its central level `s`, and the freed mass is returned by renormalising to the
original total. The pull is smooth and monotone in size — near zero for a
micro-party, near `level_shrink` for a dominant one.

It exists because the model's error is a **share vector too widely spread**, not
a level error in any one party: ranks 1-3 come out +32.30pp signed against ranks
4-12 at −36.20pp, almost exactly offsetting. Shrinking a vector of noisy
estimates toward its centre is the standard remedy, and the correction is
applied here rather than inside the spine precisely because the spine cannot see
arrivals, and a good part of ranks 4-12 are arrivals.

The parameter was **not** chosen on the nine city-years it is scored against —
see `MODEL-LOG` §1.44 for the forward test that picked it and for the cost,
which is a tail band that was unbiased and is now slightly over-forecast.

### Known divergence, unresolved

`theta_prior` and `_shrunk` are **two different estimators of the same quantity**.
`_shrunk` shrinks toward `size_centre`; `theta_prior` shrinks toward the flat
`mu_all` and ignores `size_centre`. They disagree by construction — ANC 0.869
against 0.862, PA 1.115 against 1.197 — and the drawer uses one while the spine
uses the other. At least one is wrong.

### The ceiling

Forward validation puts the best achievable RMSE(log θ) at **0.715** — a typical
error of about **2×** on retention. That is the ceiling given four cycles and
eight metros, and the estimator is at it. The mid-ballot deficit is therefore not
an estimation failure and cannot be closed by enriching this layer.

## 2. Level — how big each party will be

Rewritten 2026-08-16. The hand-typed layer this section used to describe —
`theta_mode`, `individual_theta`, `f_other`, `PLAN_BOUNDS` — is gone from the
live path. Every one of them was formed by reading outcomes it would later be
asked to predict. They survive only as a fallback for a party the measurement
cannot reach, and `note_constant` records it in the run's provenance when one is
touched.

| Piece | Where | Source | Notes |
|---|---|---|---|
| **θ** national→local retention | `levels.theta_record` | MEASURED, 8 metros, strictly pre-target | **257** observations at 2026 (ρ: 229). The 235 quoted here until 2026-08-17 was the *n* of a different table in `levels.py`; the run prints the real figure. |
| **ρ** local→local retention | `levels.local_record` | MEASURED, consecutive LGE pairs | the second route |
| **The spine** — blend of the two | `levels.spine` | MEASURED, `k = 1.0` fitted leave-one-metro-out | weight on the LOCAL route is `k/(worth+k)` |
| Size-dependent centre | `levels.size_centre` | MEASURED, `log θ = a + b·log(size)` | small parties gain locally (1.31 at <0.2%), large lose (0.94 at >10%) |
| Per-party spread | `levels.theta_prior` | MEASURED size-dispersion line | 0.19 at 40% of the vote rising to ~0.9 at 0.1% |
| by-election deltas | `byelections.py` | MEASURED, contests before the target | **inert in every backtest** — the scrape covers 2022-06 to 2026-02 only |
| `w_bye` = 0.40 | DEFAULTS | **JUDGED** | live in 2026, untestable historically |
| **Metro polls** | `polling.py` | MEASURED + inverse-variance blend | σ_poll = 3.03pp, a TRACK RECORD not a nominal margin |
| Several waves | `polling.aggregate` | recency-weighted, 120-day half-life | combined ONCE; applying them in sequence let the oldest win |
| Admission | `polling.usable_for` | rules, not judgement | must be dated, must declare its election (or fall inside 550 days), must NAME ITS CITY, and party-commissioned polls are excluded |
| **National polls → metro** | `polling.metro_estimate` | MEASURED conversion | national share ÷ contested area's share of the national vote |

**The spine.** A party's level comes from BOTH its previous national result (× θ)
and its previous local result (× ρ), weighted toward the local route by
`k/(worth+k)` where `worth` is what that party's own θ record is worth. A party
with no θ history sits on its own last local result; one with a long record sits
on the national route. Held out one metro at a time: RMSE(log) 0.236 against the
national spine's 0.275.

**A metro poll must name its city.** `ipsos-w2-2025-metros` is an eight-metro
average with no Johannesburg cut published and was being applied to Johannesburg
as a reading of it, importing Cape Town's DA and eThekwini's MK. Its scope is
`metro-aggregate` and it is admitted nowhere.

**House effects and herding are NOT corrected.** With two houses and four waves
they are not estimable, and both waves admitted for Johannesburg 2026 are the
same house (SRF). That is the single largest weakness in the 2026 poll input and
it is a data problem, not a code one.

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

### The balance runs TWICE: once per run, and once per draw

The per-draw one is the mechanism the layer is named for, and it had no row in
this document until 2026-08-17. Both are in `montecarlo.py`.

| step | where | what it does |
|---|---|---|
| pool capacity ceiling | `pool_spec`, `montecarlo.py:929-946` | a party can take at most every vote cast in the pools it belongs to. Its centre is water-filled under `POOL_CAPACITY_MARGIN × capacity` (`capped_targets`), and the excess goes to the parties that can hold it |
| run-level balance | `pool_spec` → `pools.balance_margins` | fixes each party's expected citywide share at its centre, once, on the unshocked centres |
| **per-draw balance** | `draw_pools`, `montecarlo.py:1290-1335` | the level shock is applied to the CENTRES and the matrix re-balanced against the shocked column margin, so the whole shock survives into the draw. Costs ~0.15 ms a draw |
| per-draw capacity clip | `draw_pools` → `capped_targets` | the shocked centres are water-filled under the same capacity before the balance, because a shock can ask for far more than the run-level centre did — at Johannesburg 2026 the PA has asked for up to **254%** of the Coloured pool |
| fallback | `partial_balance` (both sites) | when the two margins cannot both hold, alternating row/column scaling ENDING ON THE ROW pass: every pool exactly allocated, the party levels as close as the arithmetic permits. **Counted, not swallowed** — `ModelRun.ipf_failures` / `.ipf_balances`, printed by `main` |

**Why water-filling and not a clip.** Two places rescale the column margin and
would undo a plain clip: `pool_spec`'s own normalisation, and
`pools.balance_margins`, which opens with
`target_cols *= target_rows.sum() / target_cols.sum()` because IPF has no
solution unless the margins agree on the grand total. So `capped_targets`
preserves the total and moves mass sideways instead of removing it.

**Two ways for the margins to conflict, and only one of them is fixable here.**
A COLUMN can ask for more than its pools hold — the PA at Johannesburg 2026,
102% of every Coloured vote cast in the city — and the capacity clip removes
that case. A ROW can hold more votes than its members' targets add up to —
Nelson Mandela Bay 2021's Indian/Asian pool, 8,303 votes against 8,168 asked of
its sixteen members — and that cannot be removed by moving the party margin
without re-creating the first case. It goes to `partial_balance` and is counted.

**The capacity clip is a GUARD, not a cure.** What it reports is that the level
layer and the pool layer disagree and neither knows about the other. The cause
of the standing case is upstream, in the ecological fit: the PA's fitted vector
is a corner solution — 0.5149 on Coloured and exactly 0.0000 on the other three
pools — and 0.5149 is 10.5pp above the PA's own Duncan-Davis ceiling of 0.410,
which this code computes and then uses only as a display flag. §0 of this
document says "every estimate is projected into its Duncan-Davis interval".
**Nothing projects.** See MODEL-LOG §1.33; it is open work, not fixed work.

Before any draw is taken, `run_model` prints every party whose centre is at 90%
or more of its own pool capacity — Johannesburg 2026 reads `PA 98%`. That line
exists because until 2026-08-17 nobody found out until the balance raised, and
the raise was silent.

---

## 3. Arrivals and first local elections — parties with no local record

There are TWO classes here and they behave completely differently. The dividing
line is not novelty; it is whether a **national election has already measured the
party**.

| class | definition | how it is sized | how well it works |
|---|---|---|---|
| **First local election** | has a national baseline, never faced an LGE | **`levels.spine`**, like every other party with a national record — the national and local routes blended by how much θ evidence the party has. There is no separate first-local mechanism; `pools.first_local_election` was deleted 2026-08-17 (MODEL-LOG §1.35) having never been read by any forecast. | **76% within a factor of two**, 45 cases, median ratio 0.78 |
| **Arrival** | no national vote at all | `pools.arrival_rules`: the entrant GROUP is rescaled to the arrival-total record (`_arrival_total_prior`, median of prior city-years), and split between entrants by reach-matched mean. A splinter takes a fraction of its parent instead and is not rescaled. | **22% within a factor of two** individually, 7 of 32 — but the group TOTAL is now held to the record |

**Why the group and not the party (2026-08-17, MODEL-LOG §1.32).** Sizing each
entrant at its own reach-matched mean is right per party and wrong per city: a
city fields 20–40 arrivals, so 30 × 0.34% is a 10.2% arrival total against a
record whose median is 1.64%. Measured, that put +19.4pp into ranks 13+ and cost
6 seats. Sizing at the median gets the total right by accident (30 × 0.08% ≈
1.6%) and the split wrong. So the mean sets the *relative* weights, where ward
reach carries real signal — arrivals contesting 60–90% of wards clear 0.5% at
27.3% against 7–8% elsewhere — and the group total is held to the record.
**This fixes the aggregate and not the individual:** ranks 4-12 did not move
(−37.1 → −37.3pp) under any variant, because nothing on a nomination list says
which of twenty equally-wide-reaching parties will be the one that takes 2.83%.

**Correction, 2026-08-17 — this row credited the wrong mechanism for two weeks.**
It named `pools.first_local_election` and quoted "78% within a factor of two, 45
cases, median ratio 0.85". That function is computed, written to the emitted
spec, and **read by nothing**; `run_model` never loads its key. The 78% figure
reproduces for **the spine**, to within one case in 45 — because the instrument
that produced it, `src/arrivals.py`, scores `run.pr_share_draws`, i.e. whatever
actually ran. Confirmed by reproducing the entry's companion figure (`arrivals:
7/32`) exactly.

Measured properly across 46 parties on this path and nine city-years, the spine
beats the dead function on all three statistics — MAE 0.176 vs 0.224pp, median
ratio 0.78 vs 0.59, within-2× 76% vs 62% — winning **8 of 9 city-years**
(clustered sign test p ≈ 0.039; the unclustered 36/46 at p = 0.00016 is
optimistic because parties share city-years). No rescale or blend recovers it.
The function is being deleted; MODEL-LOG §1.35 carries the measurement.

**The finding of this section survives intact. Only the mechanism credited with
it was fictional** — which is worse than a wrong number, because a reader
checking the claim would have found the function, read its docstring, and been
satisfied. MK's forecast rests on the spine's 11.76%, not on the 8.18% that
function emits.

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
| `pa_contestation_uplift` = 1.25 | DEFAULTS | **JUDGED** | PA's 2021 ward count |
| Ward contestation | **MEASURED** since §1.29 | `levels.contestation`, from nomination lists; applied to the ward/PR ratio at `montecarlo.py:2080-2085` | 55 parties at 2021, median party contests 39% of wards. This row said "not modelled — all parties contest all wards" until 2026-08-17, contradicting §3 of this same document, which correctly listed it as MEASURED. |
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
| Pooled calibration **split by rank band** | `compare_history.pooled_by_band`, sharing `rank_band_of` with the band table so the two cannot mean different sets of parties | — |
| Brier + reliability on ward winners | `score.py` | — |
| Rank bands, SIGNED and ABSOLUTE, plus phantom mass | `compare_history.rank_bands` | — |
| Pooled coverage + pooled randomised PIT, three populations | `compare_history.calibration_columns` / `.pooled_calibration` | — |
| Ground truth | `backtest.actual_result`, asserted against `official_seats` | ✅ |
| Benchmarks (last-LGE, uniform swing, prior-LGE-noise) | `benchmarks.py` | pre-target only ✅ |
**Read the bands, not the pool (2026-08-17, MODEL-LOG §1.36).** The pooled mean
PIT over the claimed columns is 0.588 — and it is the average of **0.431 at ranks
1-3** (the model over-forecasts the top of the ballot) and **0.750 at ranks 4-12**
(it under-forecasts the middle), with both cluster-bootstrap CIs excluding 0.50 in
opposite directions. A signed average across bands with opposite errors is not a
measure of bias, for the same reason a signed sum is not a measure of error, and
this project shipped both faults two days apart. The width verdict is **not** band-dependent, and reading it off coverage is what
made this rule wrong twice (§1.39). Coverage moves with the LEVEL as well as the
width, so a purely shifted forecast of exactly the right width under-covers at
50% and over-covers at 80% and 90% — which is what this model does.

The level-free statistic is `compare_history.pit_dispersion`, the standard
deviation of the probit-transformed PIT, which **translates** under a shift where
the PIT's own variance **compresses**. It reads **0.740 at ranks 1-3 and 0.734 at
ranks 4-12** against 1.00 for a correctly-dispersed forecast. So both bands'
intervals are about **1.35× too wide**, they are near-identical in dispersion, and
they differ only in level (probit-mean −0.143 against +0.789). Since shares sum to
one, that level difference is a single zero-sum transfer.

**Two statistics that look like width evidence and are not**, both refuted on a
fixture with width held exactly right and only the level moved: the PIT's own
variance (0.0829 → 0.0450 → 0.0240 at shifts of 0/+2/+3 against a nominal 0.0833
— a pure level error reads as 3.5× under-dispersion), and empty PIT tails. Neither
says anything about width. `score.pit_histogram`'s shape verdict must not be
quoted about width either: it tests the end bins, so ranks 4-12's monotone
`[1,1,1,11,14]` scores as "U-shaped, widen it" while the same function calls the
pooled population "over-dispersed, the model is hedging".

**On significance:** the 80% and 90% over-coverage that the argument leans on is
not individually significant (p = 0.16 and 0.22). The weight sits in the
dispersion statistic — probit-SD against 1.0 gives p = 0.030 and 0.025 per band,
**p = 0.003 across both.**

The `all` population is **not** neutral: `score.py` admits a column if the party
won a seat, regardless of the forecast, so it is a mixture of a neutral set and an
outcome-selected one and is labelled that way.

| Generic `ENTRANT` renamed to the party that arrived | `backtest.relabel_run`, once on the run before any table | ✅ |

The model draws a *generic* entrant — it cannot know a new party's name — so
every comparison against a real election has to map that column onto whichever
seat-winning party had no baseline (`backtest.entrant_actual_for`). **This must
happen on the run, not per call site.** Until 2026-08-16 it happened inside
`score_seats` only, so votes, rank bands and both seat errors scored the arrival
machinery as a total miss *plus* a phantom — 8 seats of error on Johannesburg
2016, where the entrant slot had drawn 1.39% and 3.82 seats against the AIC's
actual 1.62% and 4. See MODEL-LOG §1.31. When no party arrived, the relabel is a
no-op and the entrant's seats are counted as error, which is correct.

### The rank bands report two numbers per band, not one

`compare_history.rank_bands` reports the SIGNED net error in each band and the
ABSOLUTE per-party error in the same band. The sign is a real finding — it is
what shows ranks 1-3 eating ranks 4-12 — but a signed sum is not a measure of
error, because two parties wrong in opposite directions cancel. Signed-only was
what shipped until 2026-08-17, and it hid the model's largest single failure:
Johannesburg 2021's ranks 1-3 read **+1.36pp signed against 26.69pp absolute**
(ANC +6.53, DA +7.39, ActionSA −12.59), so the worst city-year on seats was the
second-best row of the band table. Both columns are printed; neither is a
substitute for the other. MODEL-LOG §1.34.

The same function also reports **phantom mass** — share the model puts on
parties that did not stand at all, including the generic `ENTRANT` in a
city-year where nobody arrived. The bands iterate the parties that DID stand, so
no band can see it, and it is exactly why the three signed bands sum to
−6.48pp rather than to zero.

### Calibration is pooled across city-years, and reported over three populations

`score.py` has computed coverage and the randomised PIT per run since it was
written; `compare_history` took `crps.total` and discarded the rest, so the
nine-city-year scoreboard reported no calibration statistic at all. It now does,
through `calibration_columns` (per city-year, unpooled, reusing
`score.seat_matrix` / `pit_values` / `coverage`) and `pooled_calibration`
(coverage by summing hits and columns, PIT by concatenation).

**Pooled is the only readable version.** Per city-year there are four to fifteen
scored columns — Johannesburg 2021 reads 12/62/75 against nominal 50/80/90 on
n=8 — and nothing at that size distinguishes a 50% interval from an 80% one. The
report prints the per-city-year rows for provenance and labels them as noise.

Three populations, because which columns you count changes the answer:

| population | selected on | what it is for |
|---|---|---|
| `claimed` | the FORECAST (`score.CLAIM_FRACTION`) | the neutral test — selection depends on F alone, so PIT stays uniform under calibration |
| `seat_holders` | the OUTCOME (won a seat) | INFLATED by construction — zero is the bottom of the support, so a perfect forecaster reads high here too. Reported because it is the population a reader assumes |
| `all` | nothing | neutral but diluted: most columns are parties correctly at zero on both sides, each a free interval hit |

The PIT randomisation is per city-year seeded (`_pit_seed`, derived from the
city-year name) rather than left on `score.pit_values`'s module default, which
would give every city-year's k-th column the same uniform and leave nine draws
doing the work of a hundred and thirty.

**Coverage says whether the bands are the right WIDTH; the PIT mean says whether
they are in the right PLACE.** They are different faults with opposite remedies,
and this model has the second one — see MODEL-LOG §1.34.

---

## Summary of what is switched off

`entrant_geography` · `w_bye_local_*` · `arrival_group_draw` — and the legacy `poll_id`/`poll_weight`/`poll_k` path, superseded by the metro-poll inverse-variance blend and reachable only by setting `poll_id`. `polling_lean`/`polling_span` were listed here as *switched off*; they are **deleted** (2026-08-17), having been computed, passed to `pool_spec` as an argument it never read, and printed. "Switched off" and "deleted" are different claims and this line made the wrong one for one commit.

`poll_weight` has LEFT this list: metro polls now blend automatically for any
target that has one, and `polls.json` carries machine-readable fieldwork dates.
`arrival_group_draw` is off because it was built, measured and rejected — it
scored worse, for a reason recorded in MODEL-LOG rather than guessed at.

Two things are switched ON but cannot be exercised by any backtest, and must be
labelled as argued rather than tested wherever they are quoted: `w_bye` (the
by-election scrape covers 2022-06 to 2026-02, so no past target has any) and the
15% under-bias correction on the first-local-election path (**42** of its 45 cases
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

`entrant_prob` · `entrant_share` · `MIN_HOME_SPLITS` ·
`SPLIT_SD_FLOOR` · `LEVEL_DF` · `level_sd_default` · `w_bye` ·
`pa_contestation_uplift` — and note it is consumed at **2026 only** (`run.constants_read`), so it cannot contaminate any backtest. `ward_pr_ratio_overrides` was here until 2026-08-17 and is **deleted**: consumed at no target at all.

`level_shrink` belongs here with a distinction that matters. Its **value** did
not see the targets: 0.35 comes from a fit on Johannesburg 2016 alone, which
independently gives 0.375, and from a leave-one-city-year-out fit that gives
0.350 in all nine folds. Its **functional form** did — four families were
screened against the same nine city-years the change is scored on, and the ramp
won that screen. So the number is out-of-sample and the shape is not.

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

## Knowing whether the pool spec is stale

Every `pools_*.json` carries an `artefact_key`:

| field | what it pins |
|---|---|
| `city`, `target` | which city-year it was built for |
| `config_sha` | `config/dimensions.toml` |
| `pools_sha` | `pools.py`'s **code**, hashed over its syntax tree with docstrings stripped, so changing a comment does not fire it |

`run_model` compares it against what the current code would produce and prints a
named reason when it differs. The check is a **report, not a refusal** — an
unreadable spec should not take the forecast down — and it is held up by two
tests: every committed spec must be current, and a perturbed key must actually
be reported.

It does not replace `CLAUDE.md`'s one-writer rule. It stops a stale result being
believed afterwards; it does not stop the artefacts moving under a measurement
in progress.

## Reading a run without re-running it

`run_model(..., run_dir=...)` — or `--run-dir` on `montecarlo.py` and
`compare_history.py` — writes each stage's output to that directory as JSON:

| file | what it answers |
|---|---|
| `00_target`, `01_scenario_in` | which city-year, and every lever it ran with |
| `10_theta_prior` | the θ prior, the per-party `sd(log θ)`, the fitted spread by size, and **which parties are sitting on `SD_FLOOR`** |
| `20_spine` | per party: the route taken, what the national and local routes each said, the blend weight, and what its own θ record was worth |
| `30_centres` | every party's level **before and after** the shrink, with the ratio, plus the route note |
| `40_draws`, `41_guards` | drawn means and bands, ward wins, mean seats; and every guard counter — IPF failures, capacity moves, bounds violations, overhangs |

`--trace-detail` adds the per-draw arrays, which are tens of megabytes at 1500
draws and are off for that reason.

**It changes no number.** With no `run_dir` the `Trace` returns its argument
untouched and writes nothing, asserted by
`test_chain.py::test_the_trace_is_inert_without_a_run_directory`, and a traced
run is bit-identical to an untraced one.

**It is a record, not a gate.** It would have recorded the pool ceiling sitting
at 1.0 for 74 of 75 parties without anyone noticing, because nobody reads a
passive file. What catches that is an assertion; the trace is what makes such
assertions cheap, because the quantity is already exposed. See
`ARCHITECTURE-PROPOSAL.md`.

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
