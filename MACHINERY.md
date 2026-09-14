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

> ⚠️ **EVERY SCOREBOARD FIGURE IN THIS FILE IS PINNED TO THE PANEL IT WAS TAKEN
> ON, AND THE PANEL HAS MOVED TWICE** (banner added 2026-09-13). The panel went
> nine → sixteen at §1.70 and sixteen → twenty-four on 2026-09-02, and the
> specs were re-emitted on 2026-09-08 (§1.212). A seat error, a CRPS, a mean
> PIT, a coverage or a dispersion figure written in this file's prose is
> therefore a **dated reading**, not a current one, unless the line itself says
> which panel it is on. **The live values are read from the run** —
> `compare_history`'s `rows=` token carries the population — and the source of
> record for each mechanism's own figures is the function's docstring. Do not
> re-derive a ratio from a figure typed here; `JUDGEMENT-CALLS.md` §A38 records
> what that already cost once.

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
| ~~Pool ratio ranges~~ | ⛔ `pools.measure_pool_ratios` **HAS NO CALLER** — NOT part of the live construction | — | §1.210, 2026-09-08 |
| Pool α | `pools.dirichlet_alpha` | MEASURED, method of moments, size-weighted | ditto |
| **Arrival SPLIT** (how a fixed arrival budget divides between unnamed parties) | **the pool Dirichlet — NOT the emitted `seeds`** | see below | — |
| Emitted spec | `data/processed/{city}/pools_{target}.json` | DERIVED | — |

⛔ **HOW THE ARRIVAL SPLIT ACTUALLY WORKS, BECAUSE NOTHING SAID SO AND EVERY
READER — INCLUDING THIS ONE — CONCLUDED THE WRONG THING.**

The emitted `seeds` for undeclared entrants are near-uniform: at Cape Town 2016,
sixteen parties within a **1.12×** max/min spread. **That is the MEAN VECTOR, not
the forecast.** Seeded arrivals are pool members, so their realised split is drawn
by the pool Dirichlet at a per-component concentration of
`α_i = p_i × A_pool ≈ 0.005` — a spike at zero with a rare large chunk.

Measured from a live 400-draw run:

| | Cape Town 2016 | Johannesburg 2021 |
|---|---|---|
| mean-vector spread | 1.12× | 184.8× (ActionSA is a *split*, not an entrant) |
| **E[top arrival's share of the group]** | **0.412** | 0.723 |
| if the draw were flat | 0.062 | 0.031 |
| median party's draw ÷ its own mean | 0.137 | 0.079 |

Against a realised top-of-group share of **median 62.6%** across 24 metro-years.
**So the model already concentrates, and roughly correctly on the head** — and it
does so through a pool concentration fitted for an entirely different purpose.

⚠️ **The consequence for anyone editing this path:** the flat-looking `seeds` are
not a bug to be "fixed" by concentrating them, and a *deterministic* point split
is the genuinely pathological alternative — it makes the forecast's arrival seat
count a step function of the nomination roster length (6, 6, 6, 5, 8, 9, 6, 3, 3,
2, 2, 1, 1, 0, 0 for n = 1…120 at a fixed group total), which is not a vote.
Randomising is what buys the model its accuracy here; concentration barely
matters — every stochastic split lands within ~1 seat of every other across a 13×
range of concentration, over 16 metro-years. §1.220.

⚠️ **What IS wrong, measured and deliberately unfixed:** the mean vector is
ordered *backwards* against ward reach (`corr(reach, log seed) = −0.945` at Cape
Town 2016, against `corr(reach, log actual) = +0.558`), because `base` is an
arithmetic mean of a right-skewed comparator window. A geometric mean of the same
window flips it to +0.983. It is worth ≲1 seat, the arrival referee cannot see it,
two floors absorb it, and it costs a re-emit window — so it waits for one. §1.220.

⛔ **THE STRUCK ROW ABOVE IS THIS FILE'S OWN OPENING FAILURE, REPEATED.**
`CLAUDE.md` §2 leads with *"MACHINERY.md spent weeks describing a level layer
that no longer ran"*, and the pool-ratio row was doing exactly that:
`measure_pool_ratios` has **zero call sites in `src/`** (every other row in the
table has callers — `fit_city` 4, `bounds` 4, `dirichlet_alpha` 1,
`balance_within_bounds` 1). It was found by the transition ledger, which counts
*executions*: the function never appeared in a tally. **Two tests name it and
both pass**, because they assert on `inspect.getsource` and `inspect.signature`
— properties of the text, not of whether anything runs it. The function is kept
pending an owner decision; the claim that it is live is not. §1.210.


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
  National → local retention. **410 observations at target 2026.**
* **ρ** — `LGE_share(later) / LGE_share(earlier)`, `size` = the earlier share.
  Local → local retention. **292 observations.**

Both counts are as at 2026-08-23, on the tree §1.75 restored. They were 264 and
229 before §1.70's pre-2011 ingest doubled the panel, and this file was not
updated at the time — see §1.77, which is the re-read of everything that entry
invalidated.

**A missing election file is a REFUSAL, not an empty record.** `levels._citywide`
used to catch `FileNotFoundError` and return `{}`, which the two records cannot
distinguish from a metro that contested nothing. That is how Mangaung's and
Buffalo City's entire pre-2011 history left the record without a single guard
firing (MODEL-LOG §1.75). Absences are now declared in `levels.KNOWN_ABSENT`
with a reason — currently the 1999→2000 transition for the seven metros other
than Johannesburg, mirroring a refusal `ingest_historic.MUNI_HEAD` already makes
— and anything absent and undeclared stops the run by name.

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
4-12 at −36.20pp, almost exactly offsetting. ⚠️ **TWO ESTIMATORS, TWO NUMBERS,
AND BOTH ARE IN THE TREE** (noted 2026-09-13): that pair is measured on the
cached mean vectors at 400 draws (§1.44), while `compare_history`'s own band
table reads **+32.52 / −37.18pp** on the same populations at 1500 draws, and
both are quoted as live facts in different files. §1.44 records the gap and
attributes it to draw count. **Neither is a current reading** — both are nine
city-years, and the panel is twenty-four. Shrinking a vector of noisy
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
| **θ** national→local retention | `levels.theta_record` | MEASURED, 8 metros, strictly pre-target | **410** observations at 2026 (ρ: 292), as at 2026-08-23. It was 257/229 before §1.70's pre-2011 ingest and this row was not updated then (§1.77). The 235 quoted here until 2026-08-17 was the *n* of a different table in `levels.py`; the run prints the real figure. |
| **ρ** local→local retention | `levels.local_record` | MEASURED, consecutive LGE pairs | the second route |
| **The spine** — blend of the two | `levels.spine` | MEASURED, `k = 1.0` fitted leave-one-metro-out | weight on the LOCAL route is `k/(worth+k)` |
| Size-dependent centre | `levels.size_centre` | MEASURED, `log θ = a + b·log(size)` | small parties gain locally (1.31 at <0.2%), large lose (0.94 at >10%) |
| Per-party spread | `levels.theta_prior` | MEASURED size-dispersion line | 0.19 at 40% of the vote rising to ~0.9 at 0.1% |
| by-election deltas | `byelections.py` | MEASURED, contests before the target | **inert in every backtest** — the scrape covers 2022-06 to 2026-02 only |
| ward→PR conversion of the delta | `montecarlo.blended_centres` | MEASURED out-of-sample | the delta is a within-ward change on the **ward** ballot and the level it joins is on **PR**, so it is divided by the party's measured ward/PR ratio — on the population and clip `ward_pr_ratios` already uses (`pc > 0.001`, `[0.5, 2.0]`). Additive below that: the ratio is then a quotient of two noisy numbers. §1.113, §1.114 |
| `w_bye` = 0.40 | DEFAULTS | **JUDGED** | live in 2026, untestable historically |
| **Metro polls** | `polling.py` | DECLARED decomposition + inverse-variance blend | σ is `_sigma_total` — sampling + σ_common² + σ_idio²/H_eff + screen² + drift² + σ_volatility², and **only σ_idio shrinks with houses**. Adopted 2026-08-24 (§1.91), replacing the measured 3.03pp Ipsos-2016 track record, which could not say which part of the error more houses would remove |
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
| pool capacity ceiling | `pool_spec` (`montecarlo.py`) | a party can take at most every vote cast in the pools it belongs to. Its centre is water-filled under `POOL_CAPACITY_MARGIN × capacity` (`capped_targets`), and the excess goes to the parties that can hold it |
| run-level balance | `pool_spec` → `pools.balance_margins` | fixes each party's expected citywide share at its centre, once, on the unshocked centres |
| **per-draw balance** | `draw_pools` (`montecarlo.py`) | the level shock is applied to the CENTRES and the matrix re-balanced against the shocked column margin, so the whole shock survives into the draw. Costs ~0.15 ms a draw |
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
at all) and the model gave it a small fraction of the 18.12% it took.
⚠️ **The forecast share is NOT typed here** (2026-09-13): this line said 6.9%,
`POLLING.md`'s comparison table says 6.4% for the same quantity, and
`PUBLISHING-BACKLOG.md` proposed publishing 6.3%, which is the *poll's* number
and not the model's. Three copies, three values, one of them attributed to the
wrong forecaster. Read it from the run's vote table for joburg 2021; 18.12% is
the published result (`SOURCES.md`) and is the half of the pair that may stand.

| Piece | Where | Source | Notes |
|---|---|---|---|
| `entrant_prob` = 0.25 | DEFAULTS | **JUDGED** | a party arrived and won seats in **3 of 3** Johannesburg elections; this is the most quotable undefended constant in the model |
| `entrant_share` = [0.01, 0.04, 0.12] | DEFAULTS | **JUDGED** | expected mass 1.42% of the ballot |
| Slots | **one** generic ENTRANT | — | reality delivers 11 to 32 arrivals per metro |
| `SPLINTER_PARENT_WEIGHT` = 0.35 | `pools.py` | MEASURED, 22 splinter-metro cases | a splinter's vector is 35% its parent's and 65% the city average |
| `MIN_HOME_SPLITS` = 2 | `pools.py` | **JUDGED** | binary home/away where ActionSA shows a gradient (0.611/0.315/0.289/0.103) |
| `SPLIT_SD_FLOOR` = 0.90 | `pools.py` | **JUDGED floor** on a measured spread | binds at target 2016 where the pooled record's log-sd is 0.286 |
| Ward reach | `levels.contestation` | MEASURED, nomination lists | corr(reach, log vote) = **+0.393** for arrivals; seat-winners have median reach 99% against 33% |
| Arrivals as a group | `pools.arrival_group_spec`, drawn in `montecarlo.make_drawer` (**not** `blended_centres`) | MEASURED for the group TOTAL; **not a measurement of the split** | **BUILT, MIS-SCOPED, NOT ADOPTED.** Its weights cover every key of `arrival_rules` — splinters as well as entrants, 32 of them at Johannesburg 2021 — and the draw **zeroes all of them**, so it deletes the splinter seed channel rather than replacing the generic slot. Re-run fairly 2026-08-29 and refuted again: label-free `mass_err` worse at 6 of 8 metros, pooled Σ\|err\| 0.2714 → 0.5084. §1.136 |

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

**The θ calibration does not reach its target, and the reason is the floor.**
`solve_and_predict` exists to force each party's realised citywide share onto
the share that draw drew. It gets within ~1e-5 and no closer, on every draw of
every target, and this is **not** under-iteration: twenty-five times the rounds
moves the gap 2% (§1.108).

`logit` pins a sub-floor party's level at `logit(level_floor)`, so after the row
renormalisation it **holds about `level_floor` of every row whatever its target
says** — and that excess is taken from every party above the floor in proportion
to size. Johannesburg 2021: 14.5 sub-floor parties hold 1.4866e-05 against
targets asking 1.6011e-06, injecting **1.3265e-05**; the largest party ends
5.2612e-06 short against 5.4284e-06 predicted by `share × injected`.

It is reported per run as `solve_floor_injected_mean` / `_worst` in `41_guards`,
because an absorbing stage must say how much it absorbed. The only lever that
shrinks it is `level_floor` itself, which has a range and therefore faces the
full bar. **At 1.3e-05 against a seat ~300× larger, it is a mechanism to know
about, not a defect costing seats.**

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
| `turnout_tilt_anc` / `_da` | **DELETED** | — | ⛔ **NOT IN `DEFAULTS` AND NOT READ BY `run_model`.** Verified 2026-08-29: both keys are absent from `montecarlo.DEFAULTS`. They applied a tilt *after* calibration, breaking it. This row said "**OFF** in DEFAULTS" until 2026-08-29 — **claiming a switch that does not exist**, which is precisely the failure `CLAUDE.md` records as having already cost this project once, when ten front-page claims were pinned to a deleted `turnout_tilt_da` (`build_site.py`, `stats.py` — search `turnout_tilt_da`) |
| κ_bye tilt | `turnout.py` | MEASURED | contests before target ✅ |

---

## 6. Ballots and seats

| Piece | Where | Source | Saw |
|---|---|---|---|
| Ward/PR split ratio | previous LGE, per party | MEASURED | ✅ |
| Ward contestation | **MEASURED**, for every party | `levels.contestation`, from nomination lists; where the target's lists are not published yet, the PREVIOUS local election's measured shares | 55 parties at 2021, median party contests 39% of wards. Until 2026-08-18 the not-yet-published branch instead applied `pa_contestation_uplift`, a 1.25 for one named party — deleted, §1.47. This row said "not modelled — all parties contest all wards" until 2026-08-17, contradicting §3 of this same document, which correctly listed it as MEASURED. |
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
| Pooled coverage + pooled randomised PIT, **four** populations | `compare_history.calibration_columns` / `.pooled_calibration` | — |
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
outcome-selected one and is labelled that way. ⚠️ **And it does NOT reject
uniformity** (2026-09-13): under the clustered, replicate-averaged test it
rejects in only a minority-short fraction of randomisations, so its honest
status is **"not established"**, not the clean rejection a single-randomisation
χ² made it look like. `reference` and `claimed` are the two populations that may
be quoted, and only they reject in every replicate. The figures are in
`score.chi2_clustered`'s docstring and the live ones come off the run's
calibration table, which prints `not established` in words rather than a number.

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

### The arrival channel, scored without a label

`backtest.arrival_group_score`, called once per city-year in
`compare_history.run_city_year` and stored as `arrival_group`. It reports **total
mass and total seats taken by parties with no NPE baseline** — forecast against
realised — and **assigns nothing to anybody.**

It exists because every other arrival number in the report is scored through
`backtest.entrant_actual_for`, which maps the nameless `ENTRANT` column onto
`max(newcomers, key=seats)`: **the seat-winning newcomer with the most seats,
chosen with the outcome in hand.** That is the most favourable assignment
available, and the same class of fault as the `claimed` population selecting away
from a forecaster's own failures. **The baselines have no `ENTRANT` column at
all** (`benchmarks.py` never builds one), so the relabel benefits the model on a
column uniform swing structurally lacks. Report the label-free score **beside**
the relabelled one as a sensitivity pair, never instead of it — the pair is the
finding.

⚠️ **SCOPE, ADDED 2026-09-13 — THE MECHANISM IS REAL AND ITS REACH IS SMALL, AND
THIS PARAGRAPH READ AS THOUGH IT WERE UNIVERSAL.** A generic `ENTRANT` exists
only where a spec carries no seeds, so on the current panel the relabel can fire
at the 2011 rows alone, and it needs a seat-winning party with no baseline as
well — **four rows of twenty-four**, at all of which the relabelled party's seat
median is 0, so it is worth nothing on seats. ⛔ **ActionSA is a named seeded
column and is NEVER relabelled**, which is the opposite of the impression the
sentence above leaves: the hardest column in the panel gets no help from the
label. Its worth in CRPS on the 24-row panel is **still unmeasured** — the
"11.52 CRPS / 2.17 points" that used to be quoted for it is a sixteen-panel
figure and is struck. MODEL-LOG §1.229 #14; `ITERATING.md`, Key 1 carries the
row-by-row derivation. **The asymmetry that is actually material is a different
one — the roster — and `benchmarks.uniform_swing_roster` now prices it.**

| field | what it is |
|---|---|
| `actual_mass`, `actual_seats` | realised arrival totals, selected from `actual_shares` = `citywide(pr)` — **the whole PR ballot**, not the seat winners |
| `mass_mean/median`, `seats_mean/median` | the drawn totals, summed over every arrival column the model holds |
| `mass_err`, `seats_err` | realised **minus** drawn mean — **SIGNED**; read them as \|error\| |
| `mass_pit`, `seats_pit` | mid-rank PIT of the realised total in the drawn distribution. `nan` means nobody arrived, which is an outcome and not a gap |
| `seats_outside_support` | the realised total lies outside every draw — the ActionSA case the score exists to see |

⛔ **IT HAD NEVER PRODUCED A NUMBER UNTIL 2026-08-29.** It indexed `seat_draws` —
a `list[dict[str, int]]` on `ModelRun` — as if it were the `(draws, parties)`
array `pr_share_draws` is, so `np.asarray(...)[:, cols]` raised `IndexError` on
**all sixteen** city-years then scored and `compare_history` printed `nothing runnable`. The
suite was green throughout: its one unit test handed it a dense 2-D fixture
production never builds. **Seats are now summed by party NAME.** §1.136.

⛔ **AND ITS REALISED SIDE WAS OUTCOME-SELECTED.** `arrived` came from
`actual_seats`, which is filtered to `s > 0`, so realised arrival mass counted
only arrivals that **won a seat** while the forecast side summed every arrival
column. Understated in all sixteen city-years then scored and **exactly zero in four**. It
pointed the same way as the rig the function exists to remove. Both sides are now
input-selected.

**Two cautions on reading it.** `seats_pit` saturates at exactly 1.0 when the
realised total exceeds every draw — that is reported, not hidden, and
`seats_outside_support` flags it. And a **mid-P PIT is under-dispersed** against
uniform, so it must not be pooled through `_probit` without randomisation.

**It is emitted but NOT rendered.** `render()` has no arrival section; the
numbers live only in the JSON artefact. A score nobody sees in the report is a
score nobody reads.

**It does not share the relabel's definition of "arrival", and its docstring said
it did.** The relabel tests against `run.index`; this score tests against
`_npe_baseline`. A pool-seeded party such as ActionSA holds a column, so it can
never be the entrant, and yet it **is** an arrival column here. §1.136.

### Calibration is pooled across city-years, and reported over four populations

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

Four populations, because which columns you count changes the answer:

| population | selected on | what it is for |
|---|---|---|
| `reference` | the INPUTS (`reference_universe`) | **the only one a BEFORE/AFTER comparison may be quoted on.** Membership is a previous result and a nomination list, so it cannot move when a lever moves — 252 columns at every `dirichlet_scale` setting. Coverage and PIT on it read optimistically by construction and are not calibration figures; the dilution is identical at every setting, which is what makes a DIFFERENCE readable |
| `claimed` | the FORECAST (`score.CLAIM_FRACTION`) | the answer to "is this model calibrated". Neutral for ONE forecaster — selection depends on F alone, so PIT stays uniform under calibration — and **not neutral across forecasters**: 58 / 67 / 81 columns across a `dirichlet_scale` sweep, and it excludes a party the model gives a seat in fewer than half its draws, which is exactly a party the model is failing on |
| `seat_holders` | the OUTCOME (won a seat) | INFLATED by construction — zero is the bottom of the support, so a perfect forecaster reads high here too. Reported because it is the population a reader assumes |
| `all` | nothing | mixed and diluted: most columns are parties correctly at zero on both sides, each a free interval hit |

`reference` was added on 2026-08-20 after `claimed` was found to have carried a
backwards result into `MODEL-LOG` §1.55 — the two largest standardised errors in
ranks 4-12, Cape Town's Cape Coloured Congress at z = +12.1 and Johannesburg's PA
at +9.3, are outside `claimed` and inside `reference`, and they are the
difference between a band that reads 0.823 (too wide) and one that reads 1.940
(far too narrow). §1.56.

The PIT randomisation is per city-year seeded (`_pit_seed`, derived from the
city-year name) rather than left on `score.pit_values`'s module default, which
would give every city-year's k-th column the same uniform and leave nine draws
doing the work of a hundred and thirty.

**Coverage says whether the bands are the right WIDTH; the PIT mean says whether
they are in the right PLACE.** They are different faults with opposite remedies,
and this model has the second one — see MODEL-LOG §1.34.

---

## Summary of what is switched off

`entrant_geography` · `w_bye_local_*` · `arrival_group_draw`. The legacy `poll_id`/`poll_weight`/`poll_k` path was on this list until 2026-08-29, described as "reachable only by setting `poll_id`"; it is **deleted** (2026-08-22, §1.68) — verified: none of the three keys is in `DEFAULTS`, and the code is gone (the tombstone is the `poll_id` comment in `montecarlo.py`). There is nothing to reach. `polling_lean`/`polling_span` were listed here as *switched off*; they are **deleted** (2026-08-17), having been computed, passed to `pool_spec` as an argument it never read, and printed. **"Switched off" and "deleted" are different claims, and this line has now made the wrong one twice, about two different levers** — see also the `turnout_tilt_*` row above, which claimed a `DEFAULTS` switch that does not exist.

`poll_weight` has LEFT this list: metro polls now blend automatically for any
target that has one, and `polls.json` carries machine-readable fieldwork dates.
**`arrival_group_draw` was not off. Until 2026-08-20 it was UNREACHABLE** — the key was in no `DEFAULTS`, and both `parse_set` and `read_scenario_file` reject a key that is not already in the scenario, so neither `--set` nor a config file could create it. The branch was also broken (`NameError: dirichlet_floor`) and would have crashed the first time anything reached it. It is now declared at `False` and repaired.

⛔ **The 254 → 348 / CRPS 232.9 → 296.0 figures once quoted here must NOT be
cited as its rejection.** Three defects, all verified 2026-08-29 (§1.136):
**(a)** they were scored through `backtest.entrant_actual_for`, which assigns the
nameless `ENTRANT` to `max(newcomers, key=seats)` — the largest arriving
seat-winner, chosen with the outcome in hand — so they flatter the incumbent on
the one column that decides the comparison; **(b)** half that panel is a **null
arm**: all eight 2016 specs carry `arrival_group: null` and zero seeds,
`make_drawer` leaves `group_idx` at `None`, and the same RNG draws are
consumed either way; **(c)** the lever is **mis-scoped** — `arrival_group_spec`
receives `sorted(arrivals)`, the whole key set of `arrival_rules`, so splinters
are in its weights and `draw_pools` zeroes those columns before
overwriting them. ActionSA's pool seed becomes **0.18%** against an actual
**18.12%**. That is not a test of the group estimator. ⚠️ **The seed itself is
NOT typed here** (2026-09-13): it is `seeds["ASA"]` in the emitted spec and it
moves with every emit — this sentence used to say 6.85%, the 2026-09-02 archive
holds 6.756% and the live spec holds 6.840%, and the same figure was typed into
three documents that then disagreed. `ITERATING.md`, Key 1 carries the note.

**It was re-run fairly on 2026-08-29** with the label-free referee
(`backtest.arrival_group_score`) and **the rejection stands**: label-free
`mass_err` better at only 2 of 8 metros at 2021, pooled Σ|mass_err| 0.2714 →
0.5084 and Σ|seats_err| 54.15 → 104.21; Key 2's level-free width worsens 1.2000
→ 1.3557; the direction survives dropping Johannesburg and Cape Town; and all
eight 2016 city-years came back byte-identical. **But it refutes THIS LEVER, not
the idea of scoring arrivals as a group** — Ekurhuleni's incumbent arrival mass
error is +0.0002, essentially exact, and the lever turns it into +0.0702, because
the seeds it destroys were doing the work.

At 2026 it is inert for a further reason no code change can fix —
`pools.arrival_group_spec` needs a real roster, and the IEC publishes the 2026
candidate list on 16 September. `level_sd_default` and `turnout_correlation` had
the identical declaration defect and are now declared too. MODEL-LOG §1.63,
§1.133, §1.136.

### Who is on the ballot — `pools.resolve_roster`

ONE function decides who stands at a target and who may be **deleted** from the
pools, and it returns `(roster, roster_source, deliberate, prior_local)`. Three
states, and they license different things — the distinction is the whole
mechanism, because the second question deletes 2.4-2.9% of a city's vote across
16-20 parties when it fires wrongly (§1.175):

| state | source | absence means | may delete |
|---|---|---|---|
| `published` | the target's own result file | the party did not stand | everything absent |
| `declared` | `[roster]` in `judgements/<slug>-<year>.toml` | **ambiguous** — possibly a half-typed list | only if `complete = true` |
| `projected` | our own guess, from the baseline and the fitted composition | **ignorance** | only what the §K1/§K2 floors deliberately excluded |

`published` outranks a declared list: a held election is what happened. A
declared list ADDS parties always — that is what lets a genuine entrant be
named — and `complete` defaults to **false**, so a partial paste on a deadline
fails safe. See JUDGEMENT-CALLS §L1.

⚠️ **`[roster]` says WHO stands; `[party.X]` says HOW they are placed.** They
are different tables and promoting the second to the first is a defect, not a
convenience: `write_lineage_template` auto-generates a `[party.X]` entry per
party with no measured vector, so a stale template lists parties the measured
floors have since excluded — 13 of them at Johannesburg 2026 — and would
silently override §K1 and §K2.

**It is a function and not eighty inline lines for a reason.** Reached only
through a 97-second city fit, the truth table did not get tested, and the first
version shipped with the projected branch one indent level out: it ran in the
declared case too and rebuilt the roster from the baseline **two lines after**
reading the declared list. The parser was flawless; nothing crossed from it to
`seeds`. Four rows now run against the function in milliseconds and one
end-to-end test crosses to the emitted spec. §1.178.

### The SECOND consumer of the same roster — `montecarlo.roster_for_target`

`resolve_roster` decides what to drop from the **pools**; a separate function,
`montecarlo.roster_for_target`, decides what to drop from the **theta
baseline** (`run_model`'s off-ballot drop, which pops absent parties out of
`base_city_d`/`base_share_d` before `theta_prior` ever sees them). Until
2026-09-14 the two did not agree, because the pool spec never wrote its own
roster decision anywhere a caller could read: `emit_pools` folded
`roster_source`/`reach_source` into the free-text `provenance` sentence only,
and `roster_for_target` could see nothing but the calendar's own
`results` template — so a not-yet-held target (2026, today) always resolved
`not_yet_held` and left the theta-baseline drop disabled, **even when
`resolve_roster` had already built and used a projected ballot for the pools
themselves.** Two mechanisms, one target, disagreeing about what the ballot
is, and nothing said so. §1.237.

`emit_pools` now writes `roster` / `roster_source` / `reach_source` as spec
fields, `run_model` reads them into `scenario` before calling
`roster_for_target`, and that function gains a **fourth** state:

| state | source | the off-ballot drop |
|---|---|---|
| `published` | the target's own result file | runs, correct |
| `projected` | the pool spec's own `roster`/`roster_source` (whichever of published/declared/projected `resolve_roster` reached) | runs, against an ASSUMPTION |
| `not_yet_held` | neither a result file nor a spec roster | disabled, knowingly |
| *(raise)* | a spec claiming a `roster_source` with no readable `roster` behind it | the run stops |

`projected` is deliberately never called `published` here, whatever
`resolve_roster` itself decided internally — from `roster_for_target`'s
standpoint every non-result-file source is a guess, and the state name is the
one place a downstream reader (`compare_history`, `forecast_summary.json`,
a person) can tell "ran against a fact" from "ran against an assumption"
without opening the spec. The fourth branch — a named `roster_source` with an
unreadable `roster` — fails the SAME way `contesting_parties` returning empty
on a file that exists was fixed to fail: it raises, rather than quietly
falling back to `not_yet_held` and disabling the drop in silence. See
`roster_for_target`'s own docstring for the full history, including why the
earlier decision NOT to wire a declared/projected roster into this drop was
reversed rather than merely widened.

⚠️ **`arrival_group` is a THIRD mechanism and is not part of this reconciliation.**
`emit_pools` builds it only when `roster_source in ("published", "declared")` —
never for `projected` — because it splits arrivals across specific wards by a
measured `reach`, a property of an actual nomination list that a guessed
roster does not have. Investigated 2026-09-14 and found to be a different,
still-deliberate choice, not the same disagreement.

### How a declared party is SIZED — `[party.X]`

| key | read by | what it does |
|---|---|---|
| `parent` | `classify_arrival` | names a parent, making it a SPLIT rather than an entrant |
| `weights` | `arrival_rules` | its pool vector, in `categories` order, normalised |
| `support` | `arrival_rules` | **the strength knob** — its expected share of the city |
| `overperform` | `arrival_rules` | a multiplier on the default, to scale the record rather than replace it — **in both branches**, with or without `weights` |
| `baseline_share` | **nothing** | informational: what it polled at the preceding national election |

The set is closed by `pools.PARTY_KEYS` and an unknown key **refuses**, naming
the file. **`weights` declares WHERE the votes come from, not HOW MANY** — a
party with `weights` and no `support` **and no `overperform`** is sized and
budgeted exactly like an undeclared one, and the note says `size NOT declared`.

⚠️ **`overperform` was read in one branch of two until 2026-09-06**, while
`PARTY_KEYS` promised it unconditionally and the closed-key refusal accepted it
beside `weights`. So the declaration form the code's own note instructs a reader
to use — *"declare which pools it pulls from and what support you expect"* —
was the one form that dropped the multiplier on the floor, seeded the party at
the comparator mean, and said nothing. Number-neutral when fixed (no judgement
file declares any of the three keys) and reachable on 16 September. §1.195.

⚠️ **`MAX_POOL_CAPTURE = 0.9` clips a concentrated declaration and used to do it
silently** — 6% aimed entirely at Johannesburg's Indian/Asian pool delivers
2.85%. `capture_shortfall` measures the loss and the note reports it.
JUDGEMENT-CALLS §L5.

**`[roster]` refuses what it cannot read**, in three closed sets:
`LINEAGE_TABLES` (a misspelt `[rostr]` used to drop the run silently through to
a PROJECTED ballot), `ROSTER_KEYS`, and `KNOWN_PARTY_CODES` — a declared name
must resolve to a known party **or** carry its own `[party.X]` table, because
`parties.canonical` slugs what it does not recognise and `'VF PLUS'` becomes a
phantom `VF_PLUS` while the real `VFPLUS` is deleted. And a `complete = true`
deletion above `ROSTER_DROP_CEILING` (1.5% of the fitting year's vote) refuses,
names the parties, and requires `confirm_drop = true`. §L4. Until 2026-09-03 `support` was read only alongside `weights`, so a
party announced without a ward list had its declared size silently discarded;
and all three docstrings plus the template named `baseline_share` — the one key
nothing reads — as the strength knob. JUDGEMENT-CALLS §L3.

⛔ **A JUDGED SIZE SITS OUTSIDE THE GROUP BUDGET.** `arrival_rules` rescales
the entrant group to the arrival-total record (`_arrival_total_prior`). That
record is a prior over arrivals nobody has sized, so a party declared with
`support` or `overperform` is held out of it — inside, a declared 12% came out
at 0.3687%. The undeclared entrants still carry the record. §1.178.

⛔ **THE DECLARATION SETS THE LEVEL; THE RECORD SETS THE WIDTH.** The band is
the arrival record's quantiles divided by the **comparator mean**, never by the
adjusted centre. Dividing by the centre made a stated level narrow its own band
in proportion to it — ActionSA's ×36 would have produced a 95th percentile at
7.7% of its own mean. JUDGEMENT-CALLS §L2, §1.178.

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
`ward_pr_ratio_overrides` was here until 2026-08-17 and is **deleted**: consumed at no target at all. `pa_contestation_uplift` was here until 2026-08-18 and is **deleted** too — it was consumed at 2026 only, which was offered as a reason it could not contaminate a backtest, and is better read as the reason nothing could test it.

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

## Where the forecast's width comes from

Measured by ablation, Johannesburg 2021, five seeds (`src/width_budget.py`).
Share of drawn variance in each party's citywide PR share that disappears when
the source is switched off:

| source | ANC | DA | mid-ballot and below |
|---|---|---|---|
| within-pool Dirichlet | 0.67 | 0.39 | **0.83 – 0.98** |
| θ level shock | 0.37 | 0.54 | 0.07 – 0.44 |
| pool turnout copula | ~0 | 0.03 | ≤ 0.11, mostly noise |
| ward noise | ~0 | 0.07 | ≤ 0.06 |
| per-VD turnout noise, blend jitter | **0.00** | **0.00** | **0.00** |

**"0.00" means "not a source of CITYWIDE width", not "does nothing".** Both
turnout knobs are live and act on the **ward** layer: at Johannesburg 2021 the
committed `turnout_noise_sd = 0.08` moves 46 ward wins and `turnout_blend_jitter
= 0.25` moves 14, while citywide dispersion is identical to six decimals across
a tenfold change in either. That is what i.i.d. noise over 865 voting districts (the review said **855**, which matches no year of this city — 797 in 2011, 842 in 2016, 867 in 2021, 865 in 2026; the count is derived in `cities/joburg.toml` and never typed, §1.93)
should do. The copula's row is the least certain in this table — 0 to 5%, inside
the noise floor, and not explained (§1.48).
| entrant slot | ~0 | 0.04 | ≤ 0.07 |

**The Dirichlet is the width layer**, and was not thought to be — it is
registered as a concentration guard. θ matters at the top of the ballot and
little below it. Three registered constants (`turnout_noise_sd`,
`turnout_blend_jitter`, `TURNOUT_CORRELATION`) move citywide party width
essentially not at all.

Read the harness's printed noise floor before reading its table: switching a
source off shifts the random stream as well, so a single-seed ablation cannot
tell contribution from stream movement. See MODEL-LOG §1.48.

**Each layer carries a CONDITIONAL share, not its own marginal record.** This is
the practical consequence and it has been measured (§1.50). The binned
`sd(log θ)` record is a marginal dispersion — everything that moved a party's
local share against its national one — so making the θ layer reproduce it counts
the Dirichlet's contribution twice. Done deliberately, with a derived and
correct bias correction, it takes coherent seat error 258 → 268 and ranks 4-12
`sd(z)` from 0.856 to 0.522. `SD_FLOOR = 0.15` is approximately the conditional
share, between the raw fit's 0.120 and the marginal record's 0.227.

Anything that reads a layer's own historical spread and sets that layer's
parameter from it is making this mistake.

**Since 2026-08-20 the conditional share is COMPUTED rather than argued** —
`src/theta_residual.py`, MODEL-LOG §1.59. It forward-validates the residual of
log θ about the centre `theta_prior` actually used, cluster bootstrapped on
metro-year, and it says two things:

> ⛔ **THIS TABLE IS §1.59's NINE CITY-YEARS AND HAS BEEN SUPERSEDED TWICE.**
> §1.77 re-measured it on §1.70's doubled panel and §1.124 corrected the
> harness to use the baseline `run_model` actually passes. **Current, n=403
> over 32 metro-year clusters:**
>
> | national size | measured conditional sd | 95% CI | what the model uses |
> |---|---|---|---|
> | ≥ 15% | **0.273** | [0.136, 0.386] | **0.151** (1.81×) |
> | 5 – 15% | 0.841 | [0.529, 1.026] | 0.187 |
> | 1 – 5% | 0.503 | [0.380, 0.615] | 0.300 |
> | 0.2 – 1% | 0.701 | [0.580, 0.811] | 0.369 |
> | < 0.2% | 0.864 | [0.678, 1.006] | 0.460 |
>
> **The four intervals BELOW 15% all exclude the width in use. The ≥15% one
> does not** — 0.136 ≤ 0.151 ≤ 0.386, near the bottom of a much wider interval
> than §1.59 measured. That is §1.77's withdrawal of §1.59's 🟢, not a
> refutation: the constant is still inside its interval and is no longer
> comfortably in the middle of it. (This block claimed the opposite for a day,
> contradicting both `JUDGEMENT-CALLS.md` and MODEL-LOG §1.124 written in the
> same commit. §1.126.) Run `src/theta_residual.py` rather than quoting either
> table.

| national size | measured conditional sd | 95% CI | what the model uses |
|---|---|---|---|
| ≥ 15% | **0.138** | [0.084, 0.171] | **0.150** ✓ |
| 5 – 15% | 0.663 | [0.243, 1.008] | 0.188 |
| 1 – 5% | 0.448 | [0.274, 0.613] | 0.263 |
| 0.2 – 1% | 0.737 | [0.565, 0.869] | 0.340 |
| < 0.2% | 0.915 | [0.683, 1.065] | 0.460 |

The paragraph above is **confirmed at the top of the ballot** — 0.150 is inside
the interval, while the marginal 0.222 and the chi-square-corrected 0.260 are
far outside it. It is **refuted everywhere else**: below 15% the interval
excludes the model's width in every bin, always too narrow, 1.7× to 3.5×.
`sd_for` is a straight line in log(size) and the measured quantity is not
monotone (0.915, 0.737, 0.448, 0.663, 0.138), so the line is anchored at the
ends and wrong in the middle. That middle is the mid-ballot — the band §1.58
independently measures as too narrow on the seat forecast.

## Running the panel

`compare_history` runs them in parallel processes by default — one per
city-year, capped at the machine's cores less one. `--jobs 1` forces the serial
loop, `--jobs N` fixes the count.

They are independent by construction: each reads its own pool spec, derives its
PIT seed from its own name (`_pit_seed`, deliberately not from a counter), and
since 2026-08-18 `apply_city` restores `DEFAULTS` before applying a city's
scalars, so no city inherits another's judgements. Processes rather than threads
because that module state is shared and would corrupt across city-years.

**Measured at 1500 draws: 499s serial, 169s parallel — 2.96x.** Not the order of
magnitude the core count suggests, because numpy already threads inside a single
run. Coherent seat error, CRPS, raw seat error and the medians-sum are
bit-identical between the two; the MAE columns agree to 6.7e-15, which is
floating-point summation order and not a behavioural difference (§1.46).

## Knowing whether the pool spec is stale

Every `pools_*.json` carries an `artefact_key`:

| field | what it pins |
|---|---|
| `schema` | the key's own shape. **2 since 2026-09-02** |
| `city`, `target` | which city-year it was built for |
| `config_sha` | **every `config/*.toml`**, by name and content, sorted — not the one named file it used to be |
| `cities_sha` | **every `cities/*.toml`**. Not a per-city input: `panel_turnout_spread` globs the directory, so adding a ninth city moves the turnout band of every spec |
| `pools_sha` | `pools.py`'s **code**, hashed over its syntax tree with docstrings stripped, so changing a comment does not fire it |
| `deps_sha` | the code of `parties`, `cityconfig`, `ingest_lge`, `levels` — the first-party modules the emit leans on. ⚠️ `montecarlo` is deliberately excluded: it changes on most working days and would mark every spec stale continuously, so a change to `read_ward_crosswalk` alone will NOT fire |
| `judgements_sha` | `judgements/<slug>-<year>.toml`, hashed as **parsed payload** — so a prose edit does not fire it and a declared parent or weight does |

⛔ **Two of those changed on 2026-09-02 because the key's POPULATION was wrong,
not because a file was missing (§1.173).** `config_sha` named a single path,
which coincided with the whole of `config/` only by accident; a second config
file would have been consumed and invisible. And `judgements/<slug>-<year>.toml`
— which sets each party's `parent`, `baseline_share` and pool `weights`, and is
the one input a human is most likely to hand-edit — **was in no hash at all.** A
nomination-list edit on 16 September would have changed what the model computes
while every spec reported itself current.

**Still outside the key, and named here so the gap is stated rather than
implied:**

* **`data/raw/**`** — deliberate, but *not* for the reason this used to give.
  Hashing all 387 MB takes about a third of a second, so "it would cost more
  than it catches" is wrong by an order of magnitude. The real reason is that
  **`data/archive_manifest.csv` already covers it**, git-tracked, with
  bidirectional tests written after six inputs went missing (§1.75). A second
  mechanism over the same population is the duplication this project is named
  for. ⚠️ Refreshing the manifest is therefore the moment to re-emit.
* **`data/processed/<…>/vd_ward_<target>.csv`** — covered by nothing: not in
  the key, gitignored, and excluded from the manifest assertions as an
  "output", which it is not. It is a hand-curated input that sets the pool
  sizes of the live forecast, and the IEC will republish the roll before
  4 November. **This is a real gap, not a decision.**
* **`montecarlo.py`** — see `deps_sha` above; excluded to avoid crying wolf,
  with the residual risk named.
* Emit parameters (`from_year`, `split_bloc`, `retrospective_home`), so
  `pools_2026.json` and `pools_2026_simulation.json` carry byte-identical keys.
  The `simulation_only` marker is the compensating control.

`run_model` compares it against what the current code would produce and prints a
named reason when it differs. The check is a **report, not a refusal** — an
unreadable spec should not take the forecast down — and it is held up by two
tests: every committed spec must be current, and a perturbed key must actually
be reported.

It does not replace `CLAUDE.md`'s one-writer rule. It stops a stale result being
believed afterwards; it does not stop the artefacts moving under a measurement
in progress.

## Knowing whether a published number is stale

The stat registry has two modes, and only one of them was ever checked.

A **fixed** token is pinned to the run that produced it and is checked by the
drift report and by `orphaned_scenario_claims`. A **free** token is recomputed
every build — and `mode = "free"` says nothing whatever about *when*. A free
token resolves out of a FILE, and the file has a date:

| source | file it reads |
|---|---|
| `model:` | `forecast_summary.json` — the reference run, by definition current |
| `derived:` | `seat_draws.csv`, written by the same run |
| `regime:<rule>:` | `regime_<rule>_summary.json`, written by `overhang_regimes.py`, which is **opt-in** (`build_all.py --regimes`) and therefore lags |

So a `regime:` token republishes its file's number on every build while reading
as the model speaking now, and the drift report says nothing — correctly, since
a frozen file cannot drift. `stats.freshness_problems` closes that. It refuses
the build when a token's backing file fails either test:

| signal | what it is | strength |
|---|---|---|
| the file's `scenario` block names scalar keys absent from **both** `montecarlo.DEFAULTS` and the reference run's own scenario | the file says which model wrote it | **strong** — survives any filesystem accident |
| the file's mtime is more than `FRESHNESS_GRACE_S` behind `forecast_summary.json`'s | the disk says which file is older | **weak** — `cp -p`, a restore, a checkout or a `touch` all move it, and it says nothing about which code ran |

mtime is a fallback, not a design: `forecast_summary.json` carries
`_pools_artefact_key` and `_constants_read` but **no run time, no target year
and no code hash**, so there is nothing better on disk. A `_generated` stamp
written by `montecarlo` alongside the artefact key would replace it outright.

`overhang_regimes.py` re-stamps its six outputs after the reference run is
restored, because it writes them *before* that run and every correct build would
otherwise trip the mtime test. A check that fires on a clean pipeline is a check
somebody switches off.

**Refusal, not a warning.** `orphaned_scenario_claims` printed its finding and
ten front-page claims pinned to a deleted lever survived two independent reviews
that both named them. `--allow-stale-sources` stages the fix, as
`--allow-orphans` does, and should not outlive it.

All three provenance guards — `stats.audit`, `orphaned_scenario_claims`,
`freshness_problems` — live in `build_site.py` and **nowhere else**, so the
build has to reach it. Until 2026-08-24 it could not: `build_all.py` ran
`build_interactive.py` as a mandatory step ahead of `build_site`, and that
module refuses at import by design, so the one-command build died before every
audit on every city. The interactive steps are now opt-in
(`build_all.py --interactive`), non-fatal and last. MODEL-LOG §1.89.

## Saying what we published, and when: the publication ledger

Staleness (above) asks whether a number on the page is still current. This asks
a different question the site could not answer at all: **what did we publish,
when, and out of which run.**

The owner's standard is **attribution, not re-derivability**. A forecast value
is live at one point and is bound to be superseded; the old value goes into that
token's history. We do not have to be able to recompute it — ten front-page
claims are pinned to `run:turnout_tilt_da=1`, a lever `run_model` no longer has,
and nothing will ever recompute those. We do have to be able to say what the
value was, when that was, and which model produced it.

`src/publication.py` is an **append-only** ledger — one row per token per
publication — and it is **bitemporal**, keeping two clocks that are routinely
conflated:

| field | clock | what it answers |
|---|---|---|
| `as_of` | VALID time | what the run KNEW — its input cut-off |
| `published_at` | TRANSACTION time | when a reader could first see it |
| `run_at` | — | when the model was executed |

Keeping them apart is what lets "we republished an unchanged figure" and "the
model re-estimated" be different events. `as_of` is currently the run time and **says so in the row** — `as_of_is` is
carried in the row's `provenance`, alongside the git commit and dirty flag, the
pool artefact keys, the draw count and the forecast content hash. A genuine
cut-off would be the newest fieldwork end date the run consumed, and until that
is wired the field is a labelled stand-in rather than a measurement. **The label
has to be in the ROW**: `site/changes.json` is overwritten every build, so a
future reader looking at a two-year-old row has only the row.

Every row carries **both** the raw `value` and the `display` string the reader
saw, because the interesting case is invisible from either alone: a raw move
that does not change the printed glyph is classified `rounding` — recorded, and
disclosed in aggregate, but not marked inline, since a mark that fires when
nothing visible changed teaches readers to ignore marks.

### What the build does with it

`build_site.py` classifies every token that reaches a reader against the last
published row, prints what moved, and writes `site/changes.json` for the page
layer to render from — the same classification the ledger stores, not a second
copy of the logic.

**Publishing is opt-in and a move must be declared.** `--publish` appends to the
ledger; without it the build still writes `site/changes.json` but **appends no
ledger row**, because the ledger cannot take a row back and this script runs many
times a day. With it, a batch in which anything **moved** is refused unless
`--reason` and `--change-class` (one of `recompute`, `data_revision`,
`mechanism`, `bugfix`) are given. **A first publication is not a move**: a `new`
token has nothing to have changed from, and stamping the founding rows with one
of those four classes would write a false lineage into a record that cannot be
rewritten. **This is not a
gate on the forecast moving — that is expected. It is a gate on the move being
silent.**

Four refusals stand between a build and a published row — the first on the
WRITE path proper, the other three on the BUILD path ahead of it — and they
refuse rather than warn for the
reason recorded throughout this file: a print is a comment, and ten orphaned
claims survived two reviews that both named them.

* **Unattributable rows.** A row whose `model_run_id` says *unknown*, or with no
  run time or no transaction time, is refused — and the **whole batch is
  validated before the file is opened**, because a refusal raised mid-write left
  the earlier rows permanently written.
* **Undeclared moves**, above.
* **A superseded figure in live present tense.** A retired figure may appear as
  history — *"as of 7 August the model said …"* — and not as the present. The
  prose **declares** its own dating by enclosing the sentence in an element
  carrying `data-asof`, recorded per occurrence, because the same token is live
  on one page and historical in another. It is declared rather than sniffed for
  a nearby date: such a guess fails **open** on prose it cannot parse, which is
  the exact defect, and closed on prose that is fine.
* **A published token that has left the registry unretired** — `set(latest(city))
  − set(registry)`, minus anything already carrying `superseded_at`. This one
  has **no escape hatch**, unlike `--allow-orphans` and `--allow-stale-sources`,
  because the obligation it enforces is one call to `retire()` with a reason
  rather than model work. See below.

### The seam: a ledger that starts empty, and a figure that can simply vanish

`retire()` is the only thing that sets `superseded_at`, and the superseded-in-
present-tense refusal is built entirely on that stamp. So a token that is
**deleted** rather than retired takes the guard with it — there is no row left
for the check to fire on. That is not hypothetical: it is exactly what the ten
`turnout_tilt_da` claims are, and the lever was deleted for a good reason by
someone with no idea a front-page claim was pinned to it.

Two halves, and the second is the one that matters:

* **`publication.backfill(city, rows)`** enters figures the site published
  **before this ledger existed**. They have no run identity and never will, so
  the row is keyed to the **archived page's bytes** instead:
  `r-preledger-<first 12 hex of sha256(page)>`, with the page path, the full sha
  and an `as_of_is` saying *"reconstructed from the published page; no run
  identity exists"* in `provenance`. `preledger_identity(page)` cuts that
  identity, in the same shape `run_identity` returns, so a backfilled row is
  built exactly like a live one. **`build_site` never calls it.** It is a
  one-off, and its purpose is to make a figure *retirable*, not to make it
  current — backfilling a claim and leaving it in live prose publishes precisely
  the stale number this machinery exists to stop.

  **The one exemption from the attribution refusal is keyed on EVIDENCE, not on
  the caller.** The prefix alone buys nothing: the id must follow from the sha
  the row itself records, the page path and the label must be there, and the row
  must not also claim a run time. A caller-keyed version — *only `backfill` may
  write such a row* — was written first and is **wrong**: `retire()` closes a
  token out by re-appending the row it is retiring, so the retirement of a
  backfilled figure is itself a pre-ledger row arriving through `append`.
  Locking the caller made the ten claims backfillable and then **unretirable**,
  moving the seam one step down rather than closing it. `backfill` adds the one
  check that needs the world and cannot be made later: the page at the recorded
  path must still be there and must still hash to what the row claims.

* **The build refusal above is the durable half.** The backfill fixes ten rows;
  the refusal stops the eleventh, the next time a lever is deleted.

**Backfilling and retiring the ten does not clear the build.** Measured
2026-08-31 against a throwaway ledger: the `ORPHANED PINNED CLAIMS` refusal is a
property of `content/joburg/stats.toml`, not of the ledger, so it still fires on
all ten; and the superseded-in-present-tense refusal then fires for the first
time in its life on **13 occurrences of 9 of the ten tokens**, because no page in
the tree carries a single `data-asof`. Both are correct. What is left is
editorial — date the prose, re-capture the claims under a mechanism that exists,
or cut them — and not machinery.

The run identity is built from what actually determines a forecast — the git
commit and dirty flag, the pool artefact keys, and a hash of the forecast
content with the volatile `_`-prefixed stamps stripped — so two identical
forecasts produced a minute apart get the **same** id, and the id can answer
whether anything moved. `freeze.py` already computes the commit, the dirty flag
and the pool artefact keys, and is called rather than reimplemented; the content
hash is the one piece computed here, because nothing else needed it.

Nothing has been published yet: `--publish` refuses today because
`data/processed/forecast_summary.json` predates the `_generated` stamp and
carries no run time. **`publications/` does not exist**, and no backfill has been
run — the machinery is built and proven against a throwaway ledger, and the real
one is append-only, so the first row written to it is a decision, not a step. See
MODEL-LOG §1.142 for the seam and how it was closed.

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
`ARCHITECTURE.md` (the rejected earlier proposal is in
`archive/rejected/`).

## Proving a value arrived: the delivery log

`45_delivered.json` (and `scenario["_delivered"]`, which travels into
`forecast_summary.json`) records **which constants a run consulted and at what
value**. It exists because "this change did nothing" and "this change never
arrived" were the same observation: of 48 constants pre-registered for a sweep,
42 carried a blocker, and the largest class was a module constant rebound in the
parent that never crossed the `ProcessPoolExecutor` boundary.

**The rule (`NULL-RESULTS.md` §4.1): the swept constant must appear in the log,
at the value that was set. Until it does, a flat result is VOID, not NULL.**

| function | what it does |
|---|---|
| `note_value(scenario, name, value, where, kind)` | records one read; returns its argument, so a read is instrumented by wrapping it |
| `note_module_constants(scenario, where)` | records what THIS PROCESS holds for every name in `MODULE_CONSTANTS`, at the end of a run |
| `delivery_log(source)` | the log, from a `ModelRun`, a scenario, or a `--run-dir` |
| `assert_delivered(run, name, expected, kind)` | raises `Undelivered` if it did not arrive, or arrived changed |

### The `kind` is the strength of the claim, and it is the whole point

| kind | what it proves |
|---|---|
| `consulted` | recorded **at the site that reads it** — the value demonstrably reached the computation. A delivery proof. |
| `resolved` | the value this process holds, recorded once per run without reference to any reader. Proves it crossed the process boundary; proves **nothing** about any code reading it. |
| `resolved-frozen` | as `resolved`, and the name is ALSO captured as a function default at import — so rebinding the module attribute moves the record and **not** the computation (`LEVEL_DF`, §1.33). Never delivery. |
| `missing` / `not-imported` | the declared name was not there to read. A renamed constant shows as an absence rather than as silence. |

**A `resolved` record must never be reported as evidence that a lever is
`INERT`.** §1.68 was burned by exactly this — *"that null was measured with the
gate shut."*

### What `MODULE_CONSTANTS` declares, and what it deliberately does not

**47** names across `montecarlo`, `levels`, `polling`, `pools` and `parties` (re-counted 2026-08-29; it said 48). The
rule for membership is **read in this process, on the model path** — which is
not the same question `JUDGEMENT-CALLS.md` asks, and gives a different answer.

**Deliberately absent**, because a constant read only while an artefact is
*precomputed* reaches the model through that artefact and not through the run:
the whole `pools.ALPHA_*` family and ten of its siblings, both `fold.py` floors,
and all of `turnout.py`. **Their delivery proof is `artefact_key` / `pools_sha`:
a sweep of any of them that does not move `pools_sha` never arrived.** Also
absent: `turnout` (never imported during a run) and `benchmarks` (it shapes the
**opponent**, not the model — see §1.106).

### Every lossy rendering carries a digest

`_delivery_value` collapses anything large to a count — and a count is not a
value. `parties.ALIASES`, seventeen mappings that decide what the model is even
forecasting, recorded as `{"__dict__": 17}`, so two entirely different alias
tables were the same record. Each collapse now carries `_delivery_digest`, an
order-stable content hash, and a same-length edit changes it.

## Reproducibility: the hash seed

Python randomises `hash()` for `str` per process, which reorders `set` and
`dict` iteration, which reorders a float summation on the model path. The effect
on any **share** is machine epsilon — **3.1e-16 to 5.0e-16** against party shares
whose median is 9.4e-5. What moves is whether a re-run is bit-comparable to the
one before it, and `compare_history` fans out to sixteen worker processes that
each had their own seed.

⛔ **THIS SECTION USED TO SAY "SO NO FORECAST MOVES", AND THAT IS FALSE.**
Measured on `prior-lge-noise` at mangaung 2021, 1000 draws, seed `0` against seed
`1`: **one draw in a thousand differs, and it differs by a SEAT** — ACDP 1 → 0,
UNITED_CHRISTIAN_DEMOCRATIC_PARTY 0 → 1, council size preserved. The epsilon
cannot move a share, but the allocator has a discrete step, and a
largest-remainder **tie** between two micro-parties is broken by iteration order.
A 1e-16 perturbation crosses the tie. The old claim was true of the continuous
quantity and false of the published one. MODEL-LOG §1.145.

**MEASURED on a BASELINE, ARGUED for `run_model`** — and this file's own rule is
that the distinction is stated wherever the claim is quoted. The seat that moved
was `benchmarks.prior_lge_noise`'s. `run_model` shares the allocator, so the
mechanism transfers by argument; **it has not been measured there**, and the
honest reading is that no model forecast is *known* to have moved and the
guarantee can no longer promise that none could.

`montecarlo.fix_hash_seed()` re-execs the process once under
`PYTHONHASHSEED=0`, called from the `__main__` guard of every runner. The seed
must be set **before the interpreter starts**, so a re-exec is the only way to
honour it from inside; the child sees it set and does not re-exec again. Workers
are fixed for free — a spawned child inherits `os.environ`.

`freeze.ENV_SWITCHES` records it, along with `sys.flags.hash_randomization`,
because a freeze produced by an *importing* caller holds the constant while the
interpreter never got it. The guarantee is *identical to the last bit under a
fixed hash seed; identical to ~1e-16 in the shares, and up to a tie-broken seat,
otherwise.*

**The guard is attached to `__main__`, so it protects how the code is RUN and not
how it is IMPORTED — and every ad-hoc measurement harness imports.** A script
that imports these modules gets no re-exec and no fixed seed, and its numbers are
then not bit-comparable to a canonical run. This is not hypothetical: it accounts
exactly for a two-cell, ≤0.0016 CRPS disagreement between an analysis harness and
`compare_history` (MODEL-LOG §1.145). **An analysis script must call
`montecarlo.fix_hash_seed()` itself**, or set `PYTHONHASHSEED` before the
interpreter starts, before comparing anything it produces to a shipped number.

## The ward cartogram — drawing seats instead of land

`src/render_map.py` draws real ward boundaries. That map is honest about
*where* and dishonest about *how many*: wards are drawn to hold roughly equal
population and each returns exactly one councillor, so **ward area carries no
information**, and Johannesburg's ward areas are unequal in a way that
correlates with party. Measured on the committed inputs the DA takes 1.64x its
seat share of the map's ink and MK 0.16x (MODEL-LOG §1.90). `src/hex_cartogram.py`
draws the same forecast with one equal hexagon per ward, where ink share equals
seat share by construction.

It is a *second* map, not a replacement. Geography answers where the support
sits — a real and interesting fact about this city — and the cartogram answers
how many seats it buys. The intended presentation is both, on a toggle.

**It needs no model run.** Everything it reads is already on disk:
`data/processed/ward_paths.json` (written by `render_map.py`, holding every ward
as an SVG path in final screen coordinates) and
`data/processed/ward_winner_probs.csv` (written by every Monte Carlo).

    .venv/bin/python src/hex_cartogram.py            # preview, layout, distortion table
    .venv/bin/python src/hex_cartogram.py --into <page.html>

Four stages:

1. **Centroids.** The paths in `ward_paths.json` use only `M`/`L`/`Z` with
   absolute coordinates, so `parse_path` reads them without a geometry library.
   `polygon_area_centroid` takes the shoelace area and first moments of every
   ring, treating the largest ring as the exterior so interior rings subtract.
2. **The grid.** Pointy-top hexagons on offset rows. The circumradius is set so
   that `N` hexagons have the **same total area as the city** —
   `R = sqrt(A_city / N / (3 sqrt3 / 2))` — which puts the cartogram on the
   geographic map's own footprint, so the two overlay and a toggle between them
   reads as one object moving rather than two pictures. Candidates cover the
   wards' bounding box plus a two-cell margin; there are ~3x more cells than
   wards and unused ones are simply not drawn.
3. **The assignment.** Minimise total squared displacement between ward
   centroids and cell centres — a rectangular linear assignment problem.
   `assign_optimal` is a numpy Jonker–Volgenant (the e-maxx Hungarian
   formulation, inner loops vectorised over columns, O(n²m)); scipy is not a
   dependency of this repository and a presentation feature is not the reason to
   make it one. `assign_greedy` is the cheap alternative — outermost ward first,
   nearest free cell — kept as the baseline the optimal one has to beat, which
   it does by 1.6x on mean displacement and 2.3x on the worst ward. Ties break
   on lowest cell index, so both are deterministic functions of their input.
4. **The rendering.** One `<polygon id="hexcell">` in `<defs>`, `<use>`d once per
   ward. Not a size optimisation: 135 separately-emitted polygons with rounded
   coordinates differ in area, and "every ward is the same size" is the whole
   claim of the figure, so it must hold by construction rather than to a
   tolerance. The snippet sits between `__HEXMAP_START__`/`__HEXMAP_END__`,
   distinct from the geographic map's markers so both can live on one page.

**The two maps share one visual language, and one of the two links is enforced.**
Party colours, `NAMES` and the toss-up grey are *imported* from `render_map`, so
they cannot drift. The four confidence tiers (Safe ≥90% solid, Strongly leaning
75–90% finely hatched, Leaning 60–75% heavily hatched, Toss-up <60% grey) are
inline in `render_map.main` and cannot be imported; they are re-declared as
`hex_cartogram.SAFE/STRONG/LEAN` and
`tests/test_hex_cartogram.py::test_the_two_maps_agree_on_the_confidence_tiers`
reads `render_map.py`'s source and fails if the two ever disagree.

**The headline test is the distortion measurement itself.** `ink_table` groups
drawn area by predicted winner and divides by seat share; the same function
measures both maps, because the point is that one returns 1.00x and the other
does not. `test_the_cartogram_ink_is_proportional_to_seats` recomputes it from
the **emitted SVG** rather than the layout object, demands every party inside
1e-9 of its seat share, and then runs the same instrument over the real ward
polygons where the DA must exceed 1.4x — so the check cannot pass by measuring
nothing.


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
