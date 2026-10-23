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
| Base dimension = population group | Census 2022 ward tables: each ward's group SHARES only, applied to its registered roll (`pools.pool_counts`) | MEASURED shares; the split of the roll is ASSUMED (equal registration across groups within a ward) | census pre-dates the 2026 target ✅; every backtest uses Census 2022, taken after its target ⚠️ |
| Tilt dimensions | none configured: age and sex were rejected by the gate and removed 2026-10-17 (MODEL-LOG §1.321) | — | — |
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

⚠️ **The capacity cap cannot see a party taking too much of one group**
(integrity review F2, `audits/2026-10-09-model-questions/integrity/FINDINGS.md`):
every party has weight in every pool, so a party's capacity is the whole
electorate. A ×12 PA centre gave a 45% PA with every counter at zero. The
**group-share tripwire** below is what reports it.

**The honest limit.** Projection removes only *refutable* corners. The PA's
non-Coloured share reaches 0.58%, not the ~5.7% its ward geography suggests,
because Duncan-Davis cannot exclude that all 1,173 of its votes in wards under
2% Coloured came from those wards' own 6,674 Coloured voters. Arithmetic forces
only about 159 votes out of the pool. Reaching 6% would require a model, and the model
that does it fits the ward table 20× worse (MODEL-LOG §1.38). The PA at **Cape
Town 2016 is still Coloured 1.0000**, and nothing in that ward table forbids it.

**Time and geography.** One census is held (2022), so its composition is held
flat for every election; `composition_at`'s interpolation and extrapolation
branches run only when a second census is configured, and none is. Ward codes are contiguous and *reused* across delimitations, so
Census 2022's 135 Johannesburg codes join the 2011 election's 130 wards at a
perfect 130/130 — every one the wrong polygon. `pools.reproject` goes through
voting districts, which every election file maps to its own wards, and reports
the fraction of the electorate it accounted for.

**Still open.** Population group cannot separate the ANC from the IFP (both fit
as almost entirely Black African) though their measured ground correlates −0.14
— which is precisely the distinction MK turns on. Census 2011 ward tables are
not held, so the 2011 and 2016 backtests are fitted on Census 2022 shares moved
onto their wards (`pools.reproject`), which uses a census taken after the
target.

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
    size   = the party's CURRENT size on the route           (since 2026-10-09)

**`size` is the party's size now** — its national share for θ, its previous
local share for ρ — for every party (BRIEF item 11, JUDGEMENT-CALLS §A51). The
line is fitted on the sizes the ratios were measured off and evaluated at the
current one. Until 2026-10-09 it was evaluated at the reliability-weighted size
of the party's own observations, which gave a party that had grown the
multiplier of its former size. The per-party body is `levels._shrink_one`,
called by both `_shrunk` and `theta_prior` (§A26). A party in a record with no
current size keeps its observed one and is counted (`size_fallback`).

**Only observations from a similar size count** (BRIEF item 16,
JUDGEMENT-CALLS §A52). A party's own ratios enter `own_weighted_mean` and
`worth` only where measured off a size within `h` (natural-log units) of its
current size; where none survive, its worth is 0 and it sits on the size centre
at its current size, and the spine's blend weight on its θ route falls with the
lost worth. `h` is derived per run, one per route, by `levels.size_window`: the
calendar is walked up to the target, every party's earlier record predicts each
new observation, each candidate is scored by reliability-weighted mean
absolute error in `ln r`, and `h` is the widest grid value whose paired error
difference from the best, clustered by cycle, is not measurably worse (one-sided
5%, Student's t on cycles − 1 degrees of freedom); too few scored observations
or fewer than two cycles leave the filter off. `run_model` passes the θ
window to `theta_prior` and `spine` alike. The windows and the error table are
in the `20_spine` trace.

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

For VF Plus (worth 6.46, weight 0.763), at target 2021 with the centre taken at its observed size (the rule before 2026-10-09): own 0.785, centre 0.868, **result 0.804**.

**A party with no record of its own** on a route, but a current size there,
takes its size group's average: `_shrunk` returns it at the size centre for its
current size (BRIEF item 17, JUDGEMENT-CALLS §A53). The flat common mean
(`centre_fallback`) is left only where the record is too thin for a size fit.
Its level-shock width is the size group's range at its size, `levels.size_sd`
on `theta_prior`'s fit (`montecarlo.level_shock_sd`, the one rule the drawer
and the poll blend read). A drawn party with no measured width, no size and
no θ fit stops the run: there is no typed fallback width (JUDGEMENT-CALLS §A29).

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
share *is* its centre, and each draw applies a Student-t level shock (sd 0 for
seeded arrivals, whose width is the within-pool split; JUDGEMENT-CALLS §A50),
the correlated turnout copula and a within-pool Dirichlet.

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

### One estimator

`theta_prior` and `_shrunk` share one per-party body, `levels._shrink_one`,
and agree party for party (JUDGEMENT-CALLS §A26, resolved 2026-08-18;
`tests/test_theta_prior.py` asserts it on the constructed and the real record).

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
| by-election deltas | `byelections.py` | MEASURED, contests before the target | **inert in every backtest** — `byelections.py` reads the 2021-cycle file only (contests 2022-02-02 to 2026-06-24); the 2016-cycle file is on disk and read only by the off-panel audits of §1.325–§1.327 |
| ward→PR conversion of the delta | `montecarlo.blended_centres` | MEASURED out-of-sample | the delta is a within-ward change on the **ward** ballot and the level it joins is on **PR**, so it is divided by the party's measured ward/PR ratio — on the population and clip `ward_pr_ratios` already uses (`pc > 0.001`, `[0.5, 2.0]`). Additive below that: the ratio is then a quotient of two noisy numbers. §1.113, §1.114 |
| by-election weight | `DEFAULTS["w_bye"]` → `montecarlo.bye_weight` | **DECLARED** 0.5 for every party (owner, 2026-10-17, JUDGEMENT-CALLS §A59) | no backtested target on the panel has a by-election; off the panel, the 2021 elections fed the 2016–2021 by-elections put the lowest list-vote error at ½ (MODEL-LOG §1.325–§1.327). Set to `None`, each party takes its size class's weight measured against the 2024 provincial ballot by `bye_value.py` (§A55; 0.0 for both classes when 0.5 was set). A city file may not set it (`montecarlo.DERIVED_NOT_CITY`, refused by `apply_city`). Was a typed 0.40 (§A35) |
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

⚠️ The two capacity rows above bind only where a party's pools hold less
than it asks for, and every party has weight in every pool, so its capacity is
the whole electorate (integrity review F2). They cannot report a party taking
more of one group than history allows; the group-share tripwire does.

### The group-share tripwire (reports, changes no number)

BRIEF item 12, JUDGEMENT-CALLS §A54. `make_drawer` keeps each pool's
within-pool Dirichlet split per draw (values already drawn; no extra call on
the random stream). `run_model` counts, for every (party, pool) with member
weight > 0, the draws in which the party's share of that pool's vote exceeds
its record plus the pool's margin, and reports each pair that does so in more
than `GROUP_SHARE_TRIPWIRE_DRAWS` of draws in `41_guards.group_share_tripwire`,
with the population of member pairs and the count scanned. `main` writes it into
`forecast_summary.json` and `build_site.py` prints one line per pair. Nothing
reads it back into a draw.

* **record** — the party's largest Duncan-Davis upper bound on its share of the
  pool's vote in this city's real results before the target: every local
  election `pools.fit_city` fits and every national election after one, on that
  local election's wards and composition (carried forward, argued).
* **margin** — the largest one-cycle rise of a fitted pool rate by any party in
  any metro, between consecutive fitted local elections before the target.

Both come from `data/processed/group_share_record.json`, written by
`src/group_share_record.py --emit` in a re-emit window and keyed to its own
code, `pools.py` and the emit dependencies (`declares.py`, `record` kind). No
file, or no entry for the city-year: the guard says `"no record"`.

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
| `SPLINTER_PARENT_WEIGHT` = 0.35 (the DEFAULT) | `pools.py`, read through `splinter_parent_weight(rule, party)` | MEASURED, 22 splinter-metro cases | a splinter with no record of its own: its vector is 35% its parent's and 65% the city average, unless the party's `[party.X]` entry on the judgements sheet carries `parent_weight` in [0, 1] (one mechanism for every party; the first is MK at 0.9, JUDGEMENT-CALLS §SJ1). A party whose baseline national fit identifies a pool takes that vector instead (`pools.place_vectorless`) |
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
| γ default 1.0 | `montecarlo.py` | JUDGED (JUDGEMENT-CALLS §A48) | who took it is recorded per run as the delivery note `gamma.default_1.0` |
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

**Not every fold row is a fit.** `fold.py` writes a γ for every party in a
fold's universe, and two kinds of row are placeholders: γ = 1.0 where the base
citywide share is ≤ 0.001 (`FIT_MIN_BASE_SHARE`), and γ = 0.0 where the target
has no votes for the party (every y is zero). `fold.fit_status` names which
rows those are (`fitted`, `base share <= 0.001`, `no target votes`, `unseen`).
`run_model` reads any row present as fitted (`if p in params[ballot]["gamma"]`),
so a placeholder row blocks `gamma_recent.csv` for that party.

**Pooled γ (`fold.py --pool 1,2 --out DIR`).** `fit_gamma` is `gamma_sums`
(Σwxy, Σwx², n) divided by `gamma_from_sums`. The pooled fit adds each fold's
sums, per ballot and party, over the folds whose row is a real fit, and divides
once: the through-origin fit over every fold's VD rows together, not the mean
of the folds' γs. Each fold is prepared as its own default fit (`fold_inputs`,
`fold_target`, the same functions `main` fits through). It writes
`gamma_pooled_fold1-2.csv` with the folds that contributed and each fold's
`fit_status`; nothing in the forecast reads it. `--fold N --out DIR` writes
the ordinary fit into DIR so it can be compared with the canonical file;
`--out` under `data/` is refused.

**Known:** `fit_gamma` is a no-intercept OLS of noisy y on noisy x — regression
dilution, monotone in party size (COPE 0.17 PR / 0.074 Ward against ANC 1.03).
γ carries no uncertainty into the draws. `calibrate_theta` returns 0.0000 for
PA and PAC — a degenerate solution reported as converged.

### The 2026 roll: the IEC snapshot, apportioned over the crosswalk's parts (2026-10-15)

`build_concordance.apportion_roll` places each voting district wholly in one 2026
ward (the solved assignment, `archive/vd-ward-assignment-2026/assignment.csv`),
scales the VDs of ward w by w's snapshot figure over their summed `vd_registered`
(`inputs_preflight.roll_snapshot` names the snapshot; whole numbers by largest
remainder, so the ward's rows sum to the snapshot exactly) and writes
`part_registered_2026` (the whole VD's figure on its assigned ward's row, 0 on
its other parts) and `roll_snapshot` beside `part_registered`.
`montecarlo.read_ward_crosswalk` is the one reader and returns the 2026 column
when the file has it; `ward_parts`, `pools._target_roll`, `pools.vd_map`,
`areas`, `export_interactive` and `build_make.expected_ward_shares` reach it
through that reader. It is reached only for a target with no result file, so a
backtest reads its own result file's registration and never opens the crosswalk.
`pools.artefact_key` carries `roll_sha` (the crosswalk's hash), and
`inputs_preflight` reports the roll `used` only when the crosswalk declares the
newest snapshot. Judgement: JUDGEMENT-CALLS §T1 and §T2; the input's limits:
DATA-QUALITY item 20. The assignment is a solver's recovery of the IEC's placement, not the IEC's
list, so ward-level outputs carry that limit (§T1, Limit).

**One roll in a spec.** `pools.emit_pools` sizes the pools from
`registered_at_target` and derives `pool_shares_at_target` and the provenance
phrase from that same vector (`pools.pool_shares_of_roll`); `registration_series`
is recorded history and sizes nothing. `tests/test_pool_shares_one_roll.py`.

**Preflight guard A.** Every REQUIRED row of `inputs_preflight` carries a
`used` bool computed from the artefact the model reads (`_require_used` refuses
a row without one), and `--strict` exits 1 for a required input that is present
and not used, as it does for one missing or stale. `tests/test_inputs_preflight.py`.

**A party with its own national record is fitted on it (owner, 2026-10-15).**
A party in the target's roster with no vector from the fitting (local)
election is placed by `pools.place_vectorless`, one rule for every such party:
its own fit on the baseline national election (`target.previous_npe`) when
that fit identifies at least one pool, else judged `weights`, else the
splinter blend, else the city mix. `pools.national_fits` is `fit_city` on the
national result file: every party jointly, the national election's own
registration-nested composition (`pool_counts`), the method-of-bounds box and
`PartyFit.identified`. Its voting districts are placed in wards by the
preceding LGE's map through `_ward_resolver`, the one resolver `ward_totals`
and `ward_party_shares` share (the 2019/2024 files carry no Ward column and no
BallotType, and the party table dropped every such row before). The vector is
`PartyFit.composition` on the target's pool votes, as for a local fit. No year
gate: the national election precedes the target, so a backtest reads its own
(the EFF at 2016 from 2014, COPE at 2011 from 2009). The spec records
`fitted_from_national` (election, rates, bounds, pools identified, any
`weights` or `parent_weight` the fit superseded) and `national_fit_refused`
(a party with a national record placed by the lineage rule, with why); the
per-pool `identified` list counts a national fit where it identifies.
`tests/test_national_record_fit.py`; JUDGEMENT-CALLS §F6, §SJ1; MODEL-LOG §1.307.

**Splinter weight and the emit without owner calls.** `parent_weight` under
`[party.X]` replaces the default weight for that party at both places a
splinter's vector is blended (a party with no record of its own; see above);
it is read at emit, so it is in `judgements_sha`.
`pools.py --emit --without-judgements --out DIR` drops the owner's per-party
calls (`pools.OWNER_JUDGEMENT_KEYS`) and keeps `parent`, `[roster]` and every
default; it requires `--out`, so it cannot overwrite the forecast's spec, and
the spec records `without_judgements`.

### The claims register (2026-10-15)

`content/joburg/model-claims.toml` lists each public claim that the model uses
something: page, short text, the code symbol that implements it on the 2026
forecast path, `state` (`live`, `off` or `absent`) and, for every non-live claim,
a `probe` (a function in `tests/test_model_claims.py` returning True when the
declared state holds). The test imports every symbol, runs every probe (no model
run), and asserts the pages the register lists and the pages its claims cite are
the same set. The non-live entries found when it was written (the by-election
tilt and input, the heavier-tails draw, the IFP pool, ActionSA on the national
number alone, the roll per voting district) were corrected on the pages on
2026-10-16 and are now `live`, each keeping its probe; each entry's `note` says
what the page said before.
To add a claim, add a `[[claim]]` and, if it is not live, its probe. The register
records the pages; correcting a page is a separate edit.

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
| a VD with no turnout of its own → the city's roll-weighted mean | `montecarlo.run_model` | JUDGED (JUDGEMENT-CALLS §A49) | the VD count and their share of the roll are recorded per run as `turnout.mean_fallback_vds` |

### Which elections the turnout record is allowed to lose, and how it says so

`turnout_record`, `registration_series` and `panel_turnout_spread` all read
`pool_counts`, which refuses a city-year whose census join is unsafe. Until
2026-09-14 each caller carried its own `except SystemExit: continue` and the
city-year simply **vanished** — `registration_series`'s clause even said *"that
election is not on disk for this city"* for years whose files are all on disk.

The claim is not that nothing is ever dropped — dropping a genuinely absent
election is correct — it is that **silence is forbidden**, because the size of
the harm depends on WHICH year falls and neither magnitude is visible without
the loss list:

* lose the **most recent** LGE and `turnout_band` is RE-CENTRED (`arr[-1]` is the
  centre) — a forced Tshwane 2016 refusal moved the centre by −0.4919, 63.3% →
  14.1%, with zero output;
* lose any **earlier** one and the band NARROWS — a forced joburg 2000 refusal
  took pool 2's width 0.7511 → 0.5777, −23.1%, centre unmoved. A silently
  sharpened band is an overconfident forecast with no trace.

So `pool_counts` now raises `PoolCountsUnsafe` — deliberately **not** a
`SystemExit`, which is the whole repair — for the three census refusals, and
`ElectionUnavailable(SystemExit)` carrying `not_on_disk` / `held_back` for the
two absence cases. One helper serves all three callers, files the loss under a
cause from `POOL_LOSS_CAUSES`, prints one summary line per record per city, and
**does not catch `Exception`**, so a real `TypeError` inside `pool_counts`
propagates instead of reading as a missing file. `pools.pool_losses()` exposes
the ledger as state rather than as log text.

Which years are lost today is a property of the inputs, not of this mechanism —
`DATA-QUALITY.md` item 18 carries it, and
`tests/test_census_refusal_is_not_swallowed.py` asserts the served and lost sets
PARTITION the on-disk population with no residue.

### Each ward's roll is split by its census group shares; registered voters are the only population (owner, 2026-10-17)

`pools.pool_counts` builds two levels per ward and pool, both anchored to the
IEC's ward totals:

    registered_wg = roll_w × census share_wg
    voted_wg      = registered_wg × turnout_g, each ward then scaled to its counted votes

The census enters as each ward's group shares and nothing else: no census head
count, adult (20+) count, age band or registration rate is read. The split
assumes every group in a ward registers at the same rate. Turnout by group is
the one fitted level, because votes by group are not published (`_nest`: one
rate per pool across the city's wards, bounded to [0, 1], then each ward scaled
to its counted votes). Two declared limits (JUDGEMENT-CALLS §L9): census
population includes children and the Black African population is younger, so
its share of the roll is probably overstated; and the census's "Other" (about
0.5%) is dropped before the four shares are taken. The nest this replaced
(people → adults → registered, with citywide fitted rates and a registration
bound of 2.0) gave Johannesburg 2021 a White share of the roll of 25.2% and a
White registration rate of 1.74 per adult; the split above gives 13.9%
(MODEL-LOG §1.321). `_reprojection_drift`, the gate on a census moved onto
another delimitation, weights each ward's mix by its registered voters.

### A pool silenced at the 0.0 corner is kept at the city's own rate

`pool_counts` splits each ward's votes across pools with one turnout per pool,
bounded below at 0.0 (until 2026-10-17 it also fitted adult and registration
rates the same way). A small pool whose wards run below what the other pools
explain is driven to the **0.0** corner: registered voters who cast nothing. Until 2026-09-28 that zero travelled all the
way to the spec. The pool's column in `composition("voted")` was empty,
`fit_city` left its party-rate row at zero, no party had weight in it, and
`emit_pools` skipped it. Four specs declared four pools and emitted three
(prereg C1, queue entry 30): the turnout solve silenced Mangaung's and Buffalo
City's Indian/Asian pools, and at Mangaung 2006 the registration solve did.

`_nest_holding_silent` runs each level's solve, finds any pool on the 0.0 bound
that holds registered voters (`_silent_pools`), holds it at the city's
own rate for that level (`_uninformed_rate`), and re-fits the others around it
(`_nest(..., hold=)`). The held pools are recorded in `PoolCounts.imputed` and
in `unidentified`, which the spec emits as `rates_on_a_bound`.
`panel_turnout_spread` skips any transition touching a held pool. The fallback
is declared in JUDGEMENT-CALLS §L14.

`emit_pools` now **refuses** a pool with no members instead of skipping it,
so prereg P1 (`set(pools) == set(categories)`) is an invariant of the emit.
The partial-pooling repair prereg D2 fixes for unidentified levels (C2) is not
this; it replaces the held value in the same place when it lands (F4).

---

## 6. Ballots and seats

| Piece | Where | Source | Saw |
|---|---|---|---|
| Ward/PR split ratio | previous LGE, per party | MEASURED | ✅ |
| Ward contestation, as applied to the ward/PR ratio | `levels.slate_coverage`, `montecarlo.slate_change_ratio` | MEASURED | since 2026-10-09 (item 6, owner: "vote weighted"): each slate is the share of the party's own previous-LGE list vote lying in the wards it contests, then and now, on one set of weights; the change `now / was` is capped at `WARD_PR_RATIO_MAX`, not floored. `levels.contestation` (the count of wards, below) stays the who-stands fact |
| Ward contestation | **MEASURED**, for every party | `levels.contestation`, from nomination lists — the target's result file where it exists, else the slates DECLARED under `[roster.wards]` in the judgement file (2026-09-23, §1.252); only where neither exists does it fall back to the PREVIOUS local election's shares projected by `contestation_expand` | 55 parties at 2021, median party contests 39% of wards; 82 parties at 2026 from the certified list, median 99%. **The declared branch was missing for a week after the lists landed** — they were pasted on 16 September and read only by `pools`, so the correction went on projecting slates it could have read (§1.251), and the PA was carried at a 0.520 slate against a real 1.000. Until 2026-08-18 the not-yet-published branch instead applied `pa_contestation_uplift`, a 1.25 for one named party — deleted, §1.47. This row said "not modelled — all parties contest all wards" until 2026-08-17, contradicting §3 of this same document, which correctly listed it as MEASURED. |
| a roster party whose only record is the previous LGE | `levels.local_record_only`, `montecarlo.run_model`; guard `montecarlo.roster_universe_check` | MEASURED (its previous-LGE list share) | since 2026-10-09 (item 8): entered at that share, placed by its fitted pool vector (`montecarlo.place_by_pool`, floored at `level_floor`, deviation clipped at `level_floor`: `placement_deviation`; before 2026-10-15 both clips were `SHARE_FLOOR` and erased the vector, MODEL-LOG 1.305), its ward ballot confined to the wards its slate names (as every slated party's since 2026-10-15: `levels.ballots`, `montecarlo.ballot_masks`, `solve_and_predict(mask=)`; section "Who stands where"), sized on the spine's local route, shock sd the size-group width at its local share (§A53; was `level_sd_default`, §A29). Before, it was not in the run at all. The roster is checked against the run's parties both ways; roster parties with no record are named in `41_guards.roster_unrepresented` |
| `ward_noise_sd` = 0.10 | DEFAULTS | JUDGED | applied to ward tallies, not to shares |
| Schedule 1 quota + highest surplus | `seats.allocate` | STATUTE | ✅ verified against the IEC, 6 city-years; the round-two ranking against Laingsburg 2021's published column (`tests/test_overhang.py`) |
| equal surplus → the higher vote | `seats.allocate` (integer surplus, then votes) | STATUTE, item 13(2)(b), 16(4)(c) | since 2026-10-09; the float remainder it replaced could decide before the vote count was read (law summary D3). This alone moves a council whose cut has an equal whole-vote surplus and unequal votes (the M1 diff review found published ones); the count is TO-MEASURE at the batch's run |
| equal surplus and equal votes → the seeded lot | `seats.lot_order`, keys from `seats.seat_key` / `draw_key` / `ward_key` on `seats.lot_identity` | JUDGED: the statute is silent (JUDGEMENT-CALLS §Q6) | since 2026-10-09; it was input order, so set order and `PYTHONHASHSEED`. A call with a tie and no key raises. The first `deduct` / `level` iteration reuses round 0's allocation, so one invocation never draws one council twice |
| `eligible_parties` (C/D exclusions) | `seats.py` | STATUTE | ✅ |
| Seats outside the pool: C (independents) and D (ward winners with no PR list) | `seats.outside_pool_seats` (who), `seats.outside_pool_wards` (the counts), `seats.council_seats` (the chamber) | STATUTE, Schedule 1 item 13 (`B - C - D`) | since 2026-10-16 (MODEL-LOG §1.308). The quota is struck over `council - C - D`; each C or D seat stays with its winner as a ward seat and no list seat is ever added to it. `council_seats` returns the pool plus those seats as their own party entries and refuses unless they sum to the council. Every per-draw seat vector goes through it: `montecarlo.run_model` (`seat_draws`), `prediction.seats_of` (the reader's council), `benchmarks.council_from_shares` (the baselines); `reader_seats.context_from_run` marks the run's ward-only parties `no_pr_list` so a reader's council seats them the same way, and so does the site's entry schema: `build_make.model_artefact` writes `no_pr_list` from `build_make.no_pr_list` (`levels.ballots`' ward-only set on the roster) and its roster is every party the draws' vote blocks carry (`build_play.roster_codes`), not only the seat winners, since 2026-10-16. The ground truth goes through it too (since 2026-10-16, MODEL-LOG §1.309): `backtest.actual_result` returns the pool plus each C and D ward seat, C at the IEC's published figure where a Seat Calculation Detail exists (independents under `IND`, so eThekwini 2011 carries 1 and 2016 carries 4; Buffalo City 2021's counted IND ward is 0 by the IEC), so the truth sums to the council at every city-year and a forecast C or D ward seat is scored against a real one. D is zero at every city-year on record. `seats.is_independent` is the one test for an independent, read by `outside_pool_seats` and by `backtest.entrant_actual_for`, which never names an independent as the arrival |
| The overhang rules and C/D | `montecarlo.allocate_with_overhang` | STATUTE (`deduct`); counterfactuals (`expand`, `cap`, `level`) | C and D are fixed seats under every rule: subtracted before each quota, never in `ward_wins`, never excessive, never topped up. A ward winner absent from `combined`, or present with no votes, is refused under every rule. `level` returns the smallest council at or above `COUNCIL` covering every pool ward winner, by a one-seat scan between a lower bound `(w-1)·A/v` and an upper bound `w·A/(v-w)` on the seats the quota is struck over (since 2026-10-16; it crept by the deficit under a 200-round cap, which a JHB 2026 draw exceeded, §1.308) |
| an unopposed ward's PR votes counted twice | `seats.eligible_parties(..., unopposed_pr=)`, fed by `levels.unopposed_wards` / `unopposed_pr_votes` in `backtest.actual_result` | STATUTE, items 12(2), 13(1)(b), 16(5) | since 2026-10-09. No metro LGE file on disk and no declared 2026 slate has an unopposed ward (`tests/test_unopposed.py`), so it moves no number. The draws do not model such a ward: `run_model` refuses a target that has one (JUDGEMENT-CALLS §Q7) |
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
candidate list on 16 September. `level_sd_default` (deleted 2026-10-09, §A29)
and `turnout_correlation` had the identical declaration defect and were declared
too. MODEL-LOG §1.63,
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

⛔ **AND IT REFUSES WHEN THE RECORD IT WEIGHS CANNOT BE READ.** `prior_local`
— the fitting year's citywide shares — is not a by-product: the `complete = true`
deletion is scored as a MASS against it, and the §K2 floor is derived from it.
Until 2026-09-14 it came from `_npe_citywide_for`, which returned `{}` for four
causes a caller could not tell apart (no calendar template, file absent, held
back, and read-with-a-zero-total), and the two consumers read that one value in
**opposite directions**: the deletion scored 0.00% and its ceiling never fired,
while the floor excluded nobody and the incomplete-roster union re-admitted
everything it had just removed. It is now `_npe_citywide_state`, which returns
`(shares, state)`, and `resolve_roster` refuses on any state but `read`.
⚠️ **`read` includes a genuine zero**: a file that was opened and holds no PR
vote is a fact about the world and still admits. Refusing on emptiness is the
naive repair, and it deletes the distinction. §1.238, guarded by
`tests/test_prior_local_fails_closed.py`.

`published` outranks a declared list: a held election is what happened. A
declared list ADDS parties always — that is what lets a genuine entrant be
named — and `complete` defaults to **false**, so a partial paste on a deadline
fails safe. See JUDGEMENT-CALLS §L1.

⚠️ **A declared `[roster.wards]` block sizes reach against THE CITY, not against
the paste.** A party's reach is its ward count over the city's own ward count
from `vd_map(city, target.year)` — which is what `_ward_reach` means by its
denominator, and there is one definition of reach. It was the union of wards
named in the declaration until 2026-09-14, which made reach a function of how far
through the list the typist had got: one entrant on 20 of Johannesburg's 135
wards scored 1.0 against a true 0.1481, and declaring a second party on the other
115 dropped the first party's value to 0.1481 with nothing about its own
declaration changed. Wards named outside the city's set are **reported, not
refused** — the identifiers may legitimately be typed in another space, and a
guard that fires on the correct input on the one night it runs is worse than no
guard. An explicit `[roster.reach]` still wins over the derivation, and deleting
the derivation is barred: it restores the `reach = None` defect the derivation
closed. §1.238, `tests/test_declared_reach_matches_ward_reach.py`.

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

**Since 2026-10-12 `support` and `overperform` are read at RUN time, not here**
(design 1j v3 §11.2; POOLS-REEMIT-QUEUE entry 34): `arrival_rules` sizes a
party carrying them exactly like one that does not, from the record. Since
2026-10-13 the emit reads WHICH parties carry them on a forecast
(`pools.judged_parties`; entry 37), and those sit outside the group budget
(JUDGEMENT-CALLS §L2), so the other arrivals keep the record's total; the
membership is in the spec's hash and the values are not. The judged centre and its width (`sigma_j`)
reach the forecast through `montecarlo.strength_judgements`, on a forecast
only; see "The universal draw". The text below describes the emit-time path
before that change.

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
labelled as argued rather than tested wherever they are quoted: the by-election
weights (the scrape covers 2022-06 to 2026-02, so no past target has any; since
2026-10-17 every party's weight is 0.5, the owner's declared value (JUDGEMENT-CALLS
§A59): each party with by-election evidence is centred halfway between the
model's level and its by-election level, its by-election level first capped by θ's band where the party has a national share, before the shrink; a party with no earlier vote of any kind gets no weight, §A60; only Johannesburg has a by-election input, MODEL-LOG §1.323) and the
15% under-bias correction on the first-local-election path (**42** of its 45 cases
fall at 2021, so a backtest there has one prior case to fit on) — the latter
identified but NOT applied.

**The by-election value test (BRIEF item 19, JUDGEMENT-CALLS §A55).**
`src/bye_value.py` asks whether by-election evidence predicted the next real
result beyond the model's own baseline. Per (party, metro) pair with a
by-election between the 2021 LGE and 2024-05-29: the baseline `B` is the 2021
list share through the θ relation the model uses (`levels._shrunk` on the θ
record before 2024, at the party's 2019 national share); the residual
`e = actual_2024 − B` is regressed through the origin on the party's
list-scale weighted delta, `δ_pr` (`byelections.weighted_deltas`, converted by
`byelections.delta_pr` with `levels.trusted_ward_pr`, the model's own
definitions), leave one metro out, separately for parties under and over 1%
of the 2021 list (`byelections.size_class`). A class keeps its slope only if
the 5th percentile of its out-of-sample gain over 2,000 metro-cluster
bootstrap resamples is above 0, and under 10 pairs it takes 0. The output is
`data/processed/bye_value.json`, with an `artefact_key`
(`byelections.bye_value_key`: the test's and the delta code, the emit's
dependencies, the by-election file, every raw election file up to 2024 in
every metro (`byelections.bye_value_files`), every `cities/*.toml`, and the
ward/PR clip). **A cross-ballot test on the whole record:**
the by-elections are ward contests, the outcome a national-provincial list
ballot, and nothing later exists to test against.

`pools` runs by default — `run_model` loads
`data/processed/{city}/pools_{target}.json` when the scenario does not carry
pools, and prints the provenance and any pool whose members are unidentified.
When the file is absent the run stops: there is no second engine to fall back
on, so a missing spec cannot silently become a different model. It also refuses
a spec whose pools would hold no registered voters at all, which a ward-code
mismatch across a delimitation produced for Tshwane 2026.

## Summary of what is judged and saw the targets

`entrant_prob` · `entrant_share` · `MIN_HOME_SPLITS` ·
`SPLIT_SD_FLOOR` · `LEVEL_DF` · `w_bye` ·
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
`judgements/{city}-{target}.toml`, and a splinter with no record of its own
takes 35% its parent's vector and 65% the city average rather than pure
inheritance; one with a national record is fitted on it.

Every one of these is listed with its evidence, its status and how to check it
in **`JUDGEMENT-CALLS.md`**, which is the register; this is the map. The
backtest prints an in-sample banner naming the ones a run actually consumed.

## The universal draw: one log-scale draw for every party (2026-10-12)

**The shipped draw law** (`draw_law = "universal"`; design
`audits/2026-10-11-model-round/step1/1j-universal-draw-design-v4.md` with its
addendum, option L1; owner 2026-10-12). It replaces the incumbent law's two
sources of a party's spread, a level shock at `level_shock_sd` and the
within-pool Dirichlet split, with ONE draw per party. The incumbent law stays
selectable (`draw_law = "incumbent"`) so the round's arm I exists; the section
below this one describes it.

**The draw** (`montecarlo.make_drawer`). Every drawn party gets a latent log
level `x = √ρ(s)·σ(s)·z + ω·ε`, `z` the run's one shared normal (stream
`level.shared`) and `ε` the party's own (`level.z`), with
`ω² = σ(s)²(1 − ρ(s)) + δ²·new − v_comp` floored at zero. The shares are
`c·exp(κ + x)` normalised, where `c` is the party's `pool_spec` centre
(`montecarlo.pool_spec_centres`: the post-IPF proportions weighted by pool
votes at modal turnout). **The width is read where the record measured it.**
`width_record` fits σ(s), ρ(s) and m(s) at `s = pool_spec_centres(spec)[p]`,
the pool-spec centre over the pooled parties (summing to one over them), not
at a whole-city vote share. The drawer reads each pooled party's width at that
same number. The conserved share `c` is it times (1 − the individual-path
parties' mass); that mass is 0 on every emitted spec, so the two coincide
there, and it is recorded as `35_widths.individual_mass`. An individual-path
party has no record row and is read at its share of the whole city. The pooled block then goes through the capacity
water-fill and the per-draw balance exactly as the incumbent's shocked centres
did; each pool's split is the balanced proportion itself: no Dirichlet, no mean
floor. `v_comp` is what pool turnout alone puts into a party's share through
the group mix, measured on the run's own turnout draws and SUBTRACTED, because
the record's residuals already contain differential turnout (the excess is
`41_guards.width_floored`). κ is set by a CALIBRATION PASS before the run's
draws: `N_CAL` draws through the same code on the `calib.*` streams, κ moved
until every party's mean drawn share equals `c` within `KAPPA_TOL`, at most
`KAPPA_MAX_ITER` times; it records nothing and counts nothing. An update is
applied only when another measurement follows it, so `41_guards.kappa_error`
is always the error of the κ the run draws with. `kappa_iters` and
`kappa_converged` are in `35_widths` and `41_guards`; an unconverged run is a
fault on the guard board and `src/arms.py` refuses it. The run's own mean is then tested against
`c` per party (`41_guards.mean_error`, design v2 §1.2): it reports, it does not
refuse.

**The width** (`src/width_record.py`, `data/processed/width_record.json`).
Per target, from strictly earlier backtest cycles, one smooth curve
`σ(s) = a + (b − a)/(1 + exp(k(log s − log s_mid)))` over every party-election,
one newness term δ for every party new to the city (split by anchor class
below), and a location curve
`m(s)` fitted jointly by weighted ML (one unit per party-cycle), on residuals
measured about the `pool_spec` centres the model itself builds
(`run_model(stop_after="drawer_inputs")`), relative to the large block. The
location is the centres' size-related error: fitting it keeps it out of the
width, and under option L1 it is NOT carried in the draw; it is recorded for
the centre-correction arm. ρ(s) is the shared share of variance by size group
(one-way city-year decomposition). A location fixed point subtracts the draw's
own model-internal location and re-fits. 2011 has no earlier cycle and takes a
labelled, untestable fallback, split by θ history (`montecarlo.theta_history`),
which refuses when the history was never set rather than giving every party
the `without` width. `make_drawer` refuses a missing record, a stale
one (`montecarlo.width_record_key`: the code, and the inputs it read — every
spec of `width_record.record_specs` by content, the live judgements of those
city-years, the group-share record's key, the realised result file behind
each residual city-year, the raw files up to 2006 the 2011 fallback can read,
the code of `compare_history` and `theta_residual`, and `bye_value.json`'s key —
so a re-emit or a corrected input with no code change marks it stale) or one
built for other centres (the
variant: `level_shrink` and its scale). Every value is in the record, not here;
the judgement calls are JUDGEMENT-CALLS §A57.

**The newcomer δ by anchor class** (`newness_width`, default `"by_anchor"`;
`prereg/2026-10-16-newness-width-by-anchor.md`, arm S). A party new to the
city is in one of two classes, by where its centre comes from
(`montecarlo.newness_class`, one definition for the fit and the draw):
**anchored** when it took votes at the preceding national election in the city
(`_baseline_before_seeds`), so its centre is the spine's "national only (first
local election)" level, its own national result through θ (COPE 2011, EFF
2016, MK 2026); **unanchored** when it has no national result and its centre
is an arrival seed (ActionSA 2021). The spine reads the baseline after the
seeds and labels a seeded arrival "national only" as well, which is why the
class reads the pre-seed baseline and not the route label. Each class has its
own δ (`width_record.fit_class_deltas`): the same likelihood as the joint
fit, profiled over δ alone on that class's new rows, at the converged curve,
location and fixed-point shifts of the single-δ fit, which is fitted and
iterated exactly as before (the fixed point draws `newness_width = "single"`).
So σ(s), ρ(s), m(s) and the single δ are unchanged by the split, and an
established party's width is identical under either setting. A class with no
rows in a target's record takes the single δ (`source: "single: no rows"`):
target 2016's record (2011's newcomers) holds no unanchored row, and every
2011 newcomer is anchored, so at 2016 both classes' δ equal the single δ and
the two settings draw identically; 2011 is the fallback and has no δ at all.
`"single"` runs the one δ for every newcomer (the comparison arm). The record
carries both (`delta`, `delta_by_class` with each class's rows,
party-elections and in-sample likelihood at its own and at the single δ); the
drawer writes each party's class to `35_widths.parties[p].newness_class`, the
record's split to `35_widths.record.delta_by_class` and the setting to
`35_widths.newness_width`. A record with no `delta_by_class` REFUSES under
`"by_anchor"` for a run with a newcomer (`montecarlo.newness_delta`). Read
only under the universal law. JUDGEMENT-CALLS §A57.

**The centre-correction switch** (`centre_correction`, off; prereg arm UC).
On, every party whose `pool_spec` centre is below 20% has it multiplied by
exp(m(s)), m the target's record location (fitted on earlier cycles only, s
clamped at 0.016%), and the vector is renormalised before the calibration pass,
so the run conserves the corrected centres. Widths are still read at the
uncorrected centre. The factors are in `35_widths.centre_correction`.
Under `draw_law = "incumbent"` the switch REFUSES (`SystemExit`): that law
reads no `pool_spec` centre and no width record, so the correction would be
ignored. `arrival_group_draw` likewise refuses under the universal law: the
group's Dirichlet would widen arrivals on top of the newness term δ; it runs
only under the incumbent law.

**Strength judgements** (JUDGEMENT-CALLS §SJ, design v3 §11). A party the
record cannot size takes a judged centre (`support`, `overperform`) that
replaces its centre before `pool_spec`, and a judged width `sigma_j` that
replaces its newness term, read at run time from `judgements/`. A backtest
ignores them and records that it did (`35_widths.judgements_ignored`); a
forecast declares the hash of the entries it applied
(`scenario._judgements_applied_sha` in the run summary;
`artefact_key.judgements_applied_sha` in an `export_draws` manifest), which
`declares.py --verify` checks against the live file: a declared hash the
file contradicts is `~`. On a forecast (`montecarlo.target_is_held` false) an
absent declaration is `✗` and fails, and so does a summary naming no `_target`;
a backtest may declare nothing. The audit reads `export_draws` manifests under
`site/draws/` (or under an overriding `--processed` root) as run rows, and
computes each record's live key under the root it audits. The file is
`pools.lineage_path`, under the repository's `judgements/`
(`pools.JUDGEMENTS_DIR`) whatever the working directory, and on a forecast a
missing file refuses rather than reading as the empty set.

**The trace.** `35_widths`: the law, the record used, and per party the centre,
σ, δ, ρ, the shared and own sds, `v_comp`, the floored excess, κ, and whether
it was new or judged; the judgements applied and ignored, and their hash.

## Where the forecast's width comes from (the incumbent law)

**Since 2026-10-12 this describes `draw_law = "incumbent"` only** (above).

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

## The projected roster: declaring it, and scoring it

A forecast for an election that has not been held has no nomination list, so
**who is on the ballot is itself a forecast.** `pools.resolve_roster` resolves
it into one of three sources and `montecarlo.roster_for_target` reports two
states to the run; `montecarlo._projected_roster_declaration` is what the run
says about it out loud.

| source (`pools.resolve_roster`) | what it is | state at `roster_for_target` |
|---|---|---|
| `published` | the target's own **result file** | `published` |
| `declared` | a nomination list hand-typed into `judgements/<slug>-<year>.toml` under `[roster]` | `projected` |
| `projected` | the preceding LGE result ∪ the preceding NPE baseline, less two measured floors (`JUDGEMENT-CALLS.md` §K1, §K2) and less the `IND`/`ENTRANT` slots | `projected` |

⚠️ **THE FLAG CLEARS AFTER POLLING DAY, NOT BEFORE IT, AND THE INTUITIVE
READING IS THE WRONG ONE.** `roster_for_target` branches on
`cityconfig.CALENDAR[year].results`, and `pools.contesting_parties` reads the
**result** file — so `published` is unreachable until the election has been held
and ingested. Pasting the IEC's nomination lists into the judgement file makes
the roster very much better (`roster_source` becomes `declared`, and with
`complete = true` it replaces the projection outright and licenses deleting the
parties it omits) and the run still reports `projected`, because it is still not
a result file. Anyone who expects the warning to disappear in the weeks before
the election will read an un-flagged model as flagged.

### What the run declares

`run_model` prints the declaration **unconditionally** — not behind `verbose`,
because the published run is not verbose — whenever the state is `projected`. It
carries five fields, and each exists because its absence was a question a reader
could not answer:

| field | what it answers |
|---|---|
| `parties` | how many are on the assumed ballot |
| `file` | **the spec path that was actually read**, from `scenario["_pools_spec_path"]`, never recomputed. A caller supplying `scenario["pools"]` directly opened no file, and the field says `NO FILE` rather than naming one — printing a path that was not opened is the same class of answer-shaped-non-answer as an empty roster meaning "drop nobody" |
| `source` | `roster_source` and `reach_source` as the spec recorded them |
| `how` | the derivation, **per source**. The projected branch names both prior elections by the year the target resolves them to and cites `JUDGEMENT-CALLS.md` §K1/§K2 for the floors. ⛔ It does **not** restate the floors' measured costs — `CLAUDE.md` rule zero; the figures live in §K1/§K2 and are fetched, not copied |
| `ends` | that `published` arrives with the result file, and that the available action before then is a declared list |
| `scored` | that **nothing scores the projection** — see below |

`tests/test_projected_roster_declaration.py` holds it up. Its population check
reads the `roster_source` literals out of `pools.resolve_roster`'s own AST and
asserts **set equality** with the values the declaration branches on — both
directions, because a register naming a state the code cannot reach is the same
defect as a state the register omits, and only one of those two is usually
checked.

⚠️ **Inert on the tree as it stands.** No `pools_*.json` on disk carries
`roster_source` at all: the field was added on 2026-09-14 and the batch re-emit
has not run, so every target still resolves to `not_yet_held` and this
declaration has never fired against a real spec. It goes live with the re-emit.

### Scoring the projected roster — ⛔ NOT BUILT. This is a specification.

**Nothing compares a projected roster with the ballot that eventually arrives.**
A projection that is never scored is a guess nobody learns from, and the model
has made this class of guess in every forecast it has published.

*The question.* Of the parties the projection said would contest, how many did —
and which real contestants did it miss?

*Why it is not a weekend's work, and what blocks it.* The projection is
`pools.resolve_roster`'s `_projected` set, which is built from `composition` —
the fitted pool vectors, i.e. the output of the city fit. At a **published**
target `_projected` is still computed (it is hoisted above the branch so the
declared-incomplete case can union with it) and then **thrown away**: nothing
emits it, so no spec on disk carries the counterfactual projection for a
city-year whose ballot is known. There are exactly two ways to get one, and the
choice is the whole design:

1. **Emit it.** Have `resolve_roster` return `_projected` and `emit_pools` write
   it as a spec field beside `roster` — three lines, one definition, no second
   copy of the derivation. The scorer then reads two fields off one artefact and
   never recomputes anything. **Cost: it is a `pools.py` change, so it
   invalidates every spec and belongs in the pending batch
   (`POOLS-REEMIT-QUEUE.md`), and it produces no number until that emit runs.**
2. **Recompute it in the scorer.** Cheaper to start and it is a **second
   definition of the projection**, whose failure mode is party-shaped and
   seat-costing. This project's standing rule is one definition only, and the
   quantity in question is the one that decides whether a party exists at all.

**(1) is the design.** (2) is rejected and this line is the record of it.

*What it must report, and why counts alone are the wrong headline.* Unweighted
precision and recall treat a party that polls 0.02% as the equal of one that
polls 16%, and §K1/§K2 exist precisely because those are not equal. The scorer
must report, per city-year:

* `predicted`, `actual`, `hit`, `missed`, `spurious` — counts, and the **missed
  set by name**, ordered by the missed party's **actual share at the target**,
  which is the number that says whether the miss mattered;
* **missed mass** — the missed parties' combined actual share. This is the
  headline. A recall of 0.6 costing 0.1pp and a recall of 0.9 costing 16pp are
  opposite results and the counts cannot tell them apart;
* **missed mass net of the arrival allowance.** ⚠️ This is the correction
  without which the scorer libels the model. The ENTRANT slot and
  `pools.default_seeds` exist *because* a projection cannot name a party that
  does not yet exist; the arrival total is the model's designed absorber for
  exactly this miss. A scorer that reports raw recall reports the arrival
  machinery's job as the roster's failure. What is diagnostic is the missed mass
  **beyond** what the arrival total was sized to carry.

*What it can and cannot claim.* Every backtested city-year has both halves once
(1) lands, so the panel is whatever `backtest.runnable_targets` offers across
`cities/*.toml`. But the §K1/§K2 floors were **chosen by measuring over that same
panel**, so the score is not out-of-sample with respect to the floors and must
be reported as in-sample for them. The honest out-of-sample statement is about
the *sources*, not the floors: how much of the real ballot no projection from
the preceding LGE and the preceding NPE could ever have named. That quantity
needs no fit, no floors and no second definition, and is the recall ceiling the
scorer's recall should be read against.

*Where the numbers go.* `MODEL-LOG.md`, dated, as with every other measurement.

## Knowing whether the pool spec is stale

Every `pools_*.json` carries an `artefact_key`:

| field | what it pins |
|---|---|
| `schema` | the key's own shape. **2 since 2026-09-02** |
| `city`, `target` | which city-year it was built for |
| `config_sha` | **the named config file AND every `config/*.toml` beside it**, by name and content, sorted. Both halves are load-bearing and each was a defect on its own: hashing only the named file was a population bug (a second config would have been consumed and invisible), and hashing only the directory made the ARGUMENT INERT — `_config_sha(alpha.toml)`, `_config_sha(beta.toml)` and `_config_sha(does_not_exist.toml)` returned one hash, verified. A named file not on disk, or a directory with no `*.toml` in it, is a **refusal** — the second shared with `cities_sha` through one definition, replacing two different silent sentinels (`"missing"` against `sha256("")[:16]`) |
| `cities_sha` | **every `cities/*.toml`**. Not a per-city input: `panel_turnout_spread` globs the directory, so adding a ninth city moves the turnout band of every spec |
| `pools_sha` | `pools.py`'s **code**, hashed over its syntax tree with docstrings stripped, so changing a comment does not fire it |
| `deps_sha` | the code of `parties`, `cityconfig`, `ingest_lge`, `levels` — the first-party modules the emit leans on. ⚠️ `montecarlo` is deliberately excluded: it changes on most working days and would mark every spec stale continuously, so a change to `read_ward_crosswalk` alone will NOT fire |
| `judgements_sha` | `judgements/<slug>-<year>.toml`, hashed as **parsed payload** — so a prose edit does not fire it and a declared parent or weight does |
| `gates_sha` | the RESOLVED state of the environment gates that change what THIS module may read: `HELD_BACK_OFF` and the size of `levels.HELD_BACK`. A hole the code hash cannot see — `HELD_BACK_OFF=1` empties the quarantine without changing a byte of any `.py`. ⛔ **Only gates `pools.py` actually reads belong here.** `THETA_WINDOW` sat in it until 2026-09-14 and is read by `levels`, `theta_residual`, `freeze` and `montecarlo` and by nothing here, so setting it marked every spec STALE while changing nothing emitted — cry-wolf in the one field that must not cry wolf. Removing the dict instead would have destroyed the `HELD_BACK_OFF` guard, which is real; `tests/test_artefact_key_discriminates.py` asserts both directions |

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

`run_model` compares it against what the current code would produce and, when
it differs, **refuses** (since 2026-10-10, batch item 10): `SystemExit` naming
the spec's path, `stale_reason`'s sentence and "Re-emit
(POOLS-REEMIT-QUEUE.md)". A `stale_reason` that itself raises refuses the same
way, with the exception's repr, and so does a file that is not readable JSON
(`02_pools_artefact` then records `artefact_key` and `fitted_on` as null). The
refusal comes after `02_pools_artefact` is written (so a refused run's trace
says why) and before anything reads the spec: a refused run leaves
`scenario["pools"]` empty, builds no `_vd_pool_composition`, and writes no later
stage.

**One check, three readers.** `montecarlo.read_pool_spec` reads the file and
returns the spec with `stale_reason`'s sentence (or the parse or check error);
`montecarlo.stale_pool_spec_refusal` builds the refusal text. `run_model`,
`export_interactive.read_pool_spec_or_refuse` (the interactive's
`pools_2026.json`) and `build_play._spec` (the /play/ composition block) all call
them, so the published interactive refuses exactly what the forecast refuses.
The two page readers have no escape.
Until then it printed a warning and carried on, so a run between a `pools.py`
change and its re-emit measured a model nobody had built.

**The escape**, for diagnosis only: `scenario["allow_stale_pools"] = True`, set
in-process. It is not in `DEFAULTS`, so `--set`, a scenario file and a city file
refuse it as an unknown key; it is listed in `test_levers_are_live`'s
`RUNTIME_INJECTED` so the declared-key scan accepts the read, and it is not a
lever (it moves no draw on a run that is allowed to happen), so it has no
`JUDGEMENT-CALLS.md` entry. Only `True` opens it. A run through it prints the
reason, records `02_pools_artefact.stale_allowed: true` and
`_pools_stale_allowed: true` (which travels into `forecast_summary.json` with the
scenario), and its trace fails `pools.stale` and `pools.stale_allowed`.

Held up by: every committed spec must be current
(`test_chain::test_every_emitted_pool_spec_carries_a_current_artefact_key`), a
perturbed key must be reported (`test_chain`), and G10
(`tests/test_stage_inputs.py`, section 6) on a constructed spec: a moved
`pools_sha` refuses, a raising `stale_reason` refuses, a spec that is not JSON
refuses even through the escape, a current spec runs, the escape runs and
records itself, a refused run has consumed nothing, and both page readers
refuse the same three cases through the shared check.

⚠️ **Consequence: between a `pools.py`/emit-dependency change and the re-emit,
no run on an emitted spec is possible**, the suite's model runs included. That
is the point; the window's first step is the re-emit.

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
| `validation:` | `validation_<year>.json`, written by `build_validation.py`: its `headline` as written, or (`stats.validation_value`) `cities.<slug>.<model|best>.<field>`, one metro and its best baseline by CRPS, and `total.*`, the sums of those same per-metro figures, so a printed total is the sum of its printed rows. "Seats given to the wrong party" is `stats.wrong_party_seats`, half the summed absolute seat error, the one definition |
| `published:small_party_surge` | the published draws (`site/draws/`): the share of simulations in which an established party under `stats.SMALL_PARTY_SHARE` mean list share exceeds `stats.SMALL_PARTY_SURGE` (the record's test, MODEL-LOG §1.296) |
| `published:run_date` | the published draws' manifest: `export_draws.run_time`, when the run that exported them was made. `generated_date` reads it, so the pages' date and our forecast's card (`forecast.json` `forecast_date`) come from one instant (owner, 2026-10-15) |
| `history:<city>:<year>:` | `history.json`, written by `compare_history.py`: the backtest of past elections, a different run from the forecast's. Not dated against the forecast run; `stats.history_key_fault` instead refuses a record whose manifest's artefact key for `pools_<year>.json` is not the current spec's, and its tooltip's sentence counts the backtest's simulations, not the forecast's (`tooltip_says`, `build_site.run_facts`) |

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

**The settings those guards run with are `build_site.audit_configs(registry,
ctx)` and nowhere else** (extracted 2026-09-25). It returns the `[audit]` block
of the stats registry plus `structural` — the council size, the threshold and
the ward count as *this run* reports them, never typed — in the two different
shapes `stats.audit` and `stats.scan_numbers` take. It was assembled inline in
`main`, so anything else asking "would the build refuse this page?" had to
retype the structural set, and a retyped copy answers a different question the
moment the council changes size. `tests/test_home_page.py` is the first caller
outside the build.

**A registered fact clears only on the pages it names** (owner's sweep,
2026-10-03). Every `[[audit.fixed]]` and `[[audit.allow]]` entry carries
`page` — output paths, comma-separated, or `"*"` — and `stats.load_audit_config`
refuses one without it. `stats.for_page` is the one place an entry is matched to
a page; `scan_numbers` and `audit` take `page=` and every build call passes the
output path. The field had been written on most entries and read by nothing, so
when the 8 August article moved to `nobody-will-win.html` the entries naming
`index.html` went on clearing it. **An allow phrase clears no number**: it
excuses a claim in words. It used to clear any `NN%` within sixty characters of
the phrase on any page, which is how ActionSA's 18% and Laingsburg's 23% went
without a registered source; each such figure is now an `[[audit.fixed]]` entry.

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

Five refusals stand between a build and a published row — the first on the
WRITE path proper, the other four on the BUILD path ahead of it — and they
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

* **A figure in a dated passage that is not of its date.** The other direction
  of the clause above: a passage carrying `data-asof` says when its figures
  were true, so `publication.misdated_figures` accepts in one only a `fixed`
  token captured on or before that date, or a token whose source is a
  constant of the council (`stats.council_constant_tokens`: the council size
  and the majority). The exemption is by token, not by the value shown, so a
  forecast that prints 136 is still refused. The 8 August standfirst carried the
  live `{{n_draws}}` inside such a passage; it is now `{{pub0808_n_draws}}`,
  frozen as published with `tracks = "n_draws"`.

**The dates on a figure's tooltip come from `publication.run_starts`.** For
every token it is the first `published_at` of the unbroken run of rows showing
the reader the current `display` (a `rounding` row continues a run; a value
that returns after another, or a row after a retirement, starts one). The build
passes it to `_ledger_candidates`, which records `since` (when the value on the
page first appeared; empty when it moved) and `previous_since` (when the last
published value first appeared) on every change, so `changes.json` and the
tooltips read one date. "Unchanged since" used to name the latest edition.

**Every figure's tooltip has one writer, `build_site.tooltip_text`** (owner,
2026-10-22; audits/2026-10-22-tooltips/BRIEF.md). `stats.render` leaves
`data-prov` empty; the build fills it with two lines. Line 1 is the figure, its
unit word and its history from those dates: `<v> since <this edition>.` when
it moved, `<v> since <run start>.` when it did not, `<v> since <this
edition>.` when it is new (`on_site` dates a figure typed before it became a
token); a figure that has ever shown another value then adds `Was <prior> on
<date that value first appeared>.` in every edition (`publication.prior_values`).
A pinned figure (`mode = "fixed"`, `tracks` or `historical`) is `<v> on
<date>.`, the date being the earliest of its dated passage's `data-asof`,
`on_site` and its first ledger row; a corrected one is `<v> since <run
start>. Was <prior> on <date>.`, that date being the earliest-of rule when the
replaced value is the token's first run and the figure has `on_site`, and the
replaced run's start otherwise. A "Was" value carries its unit word ("Was 54
seats"), except "chance". Either is followed by the live counterpart when one it `tracks` has
moved. A date figure is the date
alone. Outside a publication "since <this edition>" reads "in this build".
Line 2 is `SOURCE: <who>. <sentence>.` from `src/tooltip_says.py`: one table
of token-name patterns, each with the unit word, the source ("This Model" for
any figure the model computes, never a component of it) and the sentence,
filled with party names (`render_sheet.NAMES`) and the run's own counts
(`build_site.run_facts`). A published token matching no pattern, or two,
stops the build; `tests/test_tooltip_says.py` checks the table against a
build's published set in both directions.

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

## Judging whole simulated elections — `src/plausibility.py` (2026-10-12)

Each draw is turned into twenty whole-election features (volatility, the new
parties' share and the largest, the largest gain and loss, fragmentation and
its change, the top one and two, parties clearing 1%, 5% and 10%, the
small-party bucket, the tiny-party jump and mass, turnout's change, and three
ward features), by ONE definition that a real election also passes through as a
one-row call. A target is judged by the real transitions before it (strict:
ending five years before; `strict06` and `loco` as sensitivities): envelope
exceedance below and above against 1/(n+1), the Poisson-binomial event test
across targets, the randomised PIT (ties split for count features), two joint
counts (`J7_no_w_top` over the seven whole-vote features, which the
pre-registration's U1 and U2 read; `J8_with_w_top` adding the ward feature
`w_top`, its U3), each marked incomplete and left out of the panel at a target
where one of its features was not judged, and the party classes (collapse, jump,
threshold events). The record reads the 2000 files `levels.HELD_BACK` withholds
from the model, and says so. The ward winners it reads are the backtest's own
(`backtest.ward_winners`); the roll is `backtest.registered_roll`. Nothing that
draws imports it. Constants: JUDGEMENT-CALLS §P4.

The panel is the pre-registration's scored population and nothing else
(`scored_population`: every metro of `compare_history.CITIES` at 2016 and 2021,
its size asserted against prereg §2). Every run read gets per-target rows; a
target outside the population (2011, untestable; a forecast) is labelled
`scored: false` with its reason and enters no panel number, the mean exceedance
rates and the party classes included. A missing member refuses unless
`--allow-incomplete`, which the output's `population` block records. `--out` is
required and refused under `data/`.

## Running the round's arms — `src/arms.py` (2026-10-12)

The pre-registered arms of `prereg/2026-10-12-universal-draw.md` (I, U, UC,
US, C0) are scenario overrides of one tree (C0 is the same code run in a
worktree whose HEAD is one commit on the final tree reverting the census
commit's `src/pools.py` hunks and nothing else; the runner refuses C0 in a
tree that carries the hold or differs from its parent in anything else
(`check_tree`, `c0_faults`), and the others in one without the hold). Each city-year
of each arm loads a fresh scenario, calls `run_model` in process with its
trace, and writes `arrays.npz` and `meta.json` in the format
`plausibility.load_run_dir` reads, under a directory outside `data/`. A
universal-law city-year whose width record is stale or whose calibration pass
did not converge is refused (`REFUSED.json`, no arrays). `compare` reports, for
B − A: the 90% cluster bootstrap over city-years of the per party-city-year
CRPS difference by size class (`cluster_interval`), the Monte Carlo error of
the list-MAE and CRPS differences from one draw-index resample applied to both
arms (`mc_error`), and R2's median per-draw correlation with whether the pool
sets agree (`r2`). Constants: JUDGEMENT-CALLS §A58.

The intervals run over `plausibility.scored_population` only (one definition
for both scorers); 2011 is scored and reported, labelled `scored: false`, and
enters no interval. `compare` refuses: a pair that is not the registered one
(`check_pairing`: draws and seed; one clean commit, one set of pool specs and
one width-record key, except that C0's meta must name the other arm's commit as
its `final_commit` and run without the hold; US on the `level_shrink = 0`
width-record variant and every other universal arm on a variant with the shrink
on); a scored city-year missing from either arm unless `--allow-incomplete`
(recorded, with every city-year present in one arm only); and a classifying
arm (arm I) that has not run. A party only in the actuals, drawn by neither
arm, is excluded from every size class and from `all` and listed with its
share; a drawn party with no `pool_spec` centre in the classifying arm enters
`all` and no class, and is listed.

`compare`'s `instruments` block carries the registered quantities that had no
instrument, each defined as prereg amendment 3 reads its row: per cycle, the
mean CRPS difference by size class and the mean list-MAE difference over the
cycle's city-years (C1, C5, S3, U16); per arm, band coverage by class (the
realised share inside the drawn 5th-95th percentile, U11 and U14) and the
median drawn log-sd of the large parties per cycle (U12); coherent wrong-party
seats per city-year, cycle and in total (`compare_history.coherent_seats` of the
saved seat draws against `_actual_seats`, half the summed absolute error; U15,
S4); and at a forecast the §5.6 draw counts (C8). `describe` gives one arm's
drawn log-sd per party (M4), its excess over the run's own `35_widths` total
(M5) and the §5.6 counts.

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
draws and are off for that reason: `42_pr_share_draws`, `43_ward_share_draws`
(each draw's citywide share of each ballot), `42a_pr_vote_draws`,
`43a_ward_vote_draws` (the whole votes the seat law read, since 2026-10-08) and
`44_seat_draws`.

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

**Amended 2026-10-09.** An exact tie at the last seat (equal whole-vote surplus
and equal votes) is no longer broken by iteration order: the seeded lot draws it
under the run's identity and the allocation round (`seats.lot_order`,
JUDGEMENT-CALLS §Q6), so the order a set hands the allocator decides nothing. A
perturbation that changes a party's whole-vote count can still move a seat.
Whether the Mangaung case above was an exact tie or a rounding crossing is
TO-MEASURE on the next run of that baseline.

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

## Keyed draw streams: two arms on one seed see the same luck (2026-10-12)

**What.** A run has no shared random generator. `run_model` builds one
`montecarlo.DrawStreams` from the run identity `seats.lot_identity(city,
target, seed)`, and every random quantity reads its own stream, named by what it
is (the *stage*) and by whom (the *name*), at the draw's index:

| stage | name | per draw | what it drives |
|---|---|---|---|
| `turnout.common` | `""` | 1 normal | the citywide turnout factor of the copula |
| `turnout.pool` | the pool's declared tie label, or its own name | 1 normal | that pool's (or tied group's) turnout through `correlated_triangular` |
| `level.z`, `level.chi` | party | 1 normal; a gamma at shape df/2 | the Student-t level shock `log_shock(sd, z, log_chi, df)`, pooled and individual parties alike |
| `split` | `pool|party` | a gamma at the member's Dirichlet shape | the within-pool split, `pool_split` |
| `arrival.total`, `arrival.split` | `""`; party | 1 normal; a gamma | the arrival-group draw (off by default) |
| `entrant.gate`, `entrant.share` | `ENTRANT` | 1 uniform; 1 normal, both every draw | the generic entrant slot |
| `vd_turnout.blend`, `vd_turnout.noise` | `""` | 1 uniform; one normal per VD | the per-draw turnout pattern |
| `ward_noise` | party | one normal per ward | the ward-tally noise, `ward_noise_multiplier` |

A stream holds only parameter-free primitives (standard normals, uniforms on
(0, 1]) in a fixed count per draw; every parameter enters afterwards through a
deterministic transform. Gammas are Marsaglia-Tsang on shape + 1 with the boost
at every shape (`log_gamma_slots`, `GAMMA_SLOTS` fixed trials, JUDGEMENT-CALLS
§A56), computed in log space; an exhausted draw takes an exact fallback and is
counted (`41_guards.gamma_fallbacks` out of `gamma_draws`). Every key read is
recorded (`41_guards.stream_keys`).

**What follows.** Adding or removing a party adds or removes its streams and
moves no other stream's values; changing a centre, a width or a df moves only
the transform over the same primitives; draw `d` is row `d` whatever the run's
length, so a short run is the prefix of a long one. Pairing is bit-identity of
the PRIMITIVES. Drawn shares of unchanged parties still move through the
normalisations and the per-draw balance, so between arms they are correlated,
not identical; a paired difference is quoted with its measured correlation
(design 1c §2.6). A renamed party, a party moving between pools, a changed tie
label, and a changed VD or ward set are unpaired by construction.

**City and target are in the root key on purpose**, so one party's shocks are
independent across the panel's city-years: pairing is wanted between arms at
one city-year, never between city-years.

**Checked by** `tests/test_draw_streams.py` (samplers exact against numpy at
N = 200,000 with power rows; chunk and prefix identity at stream and run level;
key stability across interpreters; pairing of a constructed two-pool spec under
seven arms against `prereg/2026-10-12-universal-draw.md` §6.3's thresholds).
Design: `audits/2026-10-11-model-round/step1/1c-paired-draws-design.md` and
`step2/2-review-1c.md`.

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


## The browser engine's citywide table — `src/citywide_table.py`

The interactive runs the real `run_model` under Pyodide. Natively, one
Johannesburg 2026 run opens 65 election files through
`levels._citywide_and_roster`, which reduces each to its citywide PR shares and
its ballot roster. The browser cannot ship those files, so it ships
`data/processed/citywide_<target>.json` and calls `citywide_table.install`,
which replaces the function with a lookup. The native model never installs it
and keeps parsing, so the temporal spies in `tests/_support.py` keep watching
every read.

* **Built, never computed.** `build` runs the real model and records what the
  real function returned, keyed by the repository-relative path it was asked
  for. `--check` rebuilds and compares bytes.
* **Declares itself.** The key names `levels.py` and `parties.py` by AST hash
  (`pools._code_sha`), the city and target, and the sha256 of every file
  reduced. `declares.py` audits it as the `reduction` kind, re-hashing each input.
* **Refuses rather than falls back.** `install` refuses:
  * another target;
  * a table holding an election dated at or after its target;
  * a table naming other code;
  * any environment gate in `GATES` being set.
  A path missing from the table raises `TableRefusal`, a `SystemExit`. It is
  not a `FileNotFoundError`, which `run_model` catches at two sites and answers
  with fallback constants.
* **Enforced by** `tests/test_citywide_table.py`:
  * the table regenerates byte-identically;
  * the key sets match under every control the page ships;
  * the temporal lock, a missing entry and a stale code hash are each refused;
  * a same-seed native run gives identical draws;
  * `GATES` names every gate `levels.py` reads.
  Add a control to `LEVER_SETTINGS` there when the page gains one.

Measurement: MODEL-LOG §1.265 and §1.266. Review: `audits/2026-09-28-route-b/`.

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

## Per-simulation outputs, the scenario tool, and build-time page figures (2026-09-17)

**What the Monte Carlo writes now.** Besides `seat_draws.csv`,
`ward_winner_probs.csv` and `forecast_summary.json`, `montecarlo.main` writes:

| file | one row per | columns |
|---|---|---|
| `ward_draws.csv` | simulation | `draw`, then the winning party code for every ward |
| `seat_detail_draws.csv` | simulation × party with seats | `ward_seats`, `list_seats` (= seats − wards), `seats`, `excessive` (1 if the excessive-seats clause fired for it) |

They only record what `run_model` already computed and threw away, so they
change no draw. This was verified on seed 20261104: the published
`seat_draws.csv` and `ward_winner_probs.csv` were byte-identical, and the
summary matched except for `_generated`.

**`src/scenarios.py`** reads them back: `scenarios.py "DA>=136"` lists the
matching simulations with each party's ward/list split and the wards won by
someone other than their modal winner. Every narrative claim about a scenario
should cite simulations found this way. The model is over-confident at ward
level, so a simulation's ward map looks more settled than an election would.

**Page figures are rendered at build time, never by script.** `render_sheet.py`
writes each figure as a generated token `{{@name=value;fmt;source}}`.
`stats.render` turns it into the same provenance span as a registry token and
records it for the publication ledger. The format `chance` never prints 100% or
0%. `stats.script_writes` makes the build refuse a page whose script holds a
data block, injects HTML or interpolates template text. The live 31 August page
had 12 such violations.

**Arrows.** After ledger classification, `build_site` marks each figure that
moved visibly since the last publication (▲/▼, ◆ for a changed string), with a
"Was X." hover note (the figure's own tooltip is `tooltip_text`'s). It then re-stamps the page hashes in
`NUMBERS-REVIEW.md`, so `deploy_check` still matches the pages.

## Per-draw pool turnouts (2026-09-28)

**What is recorded.** In each draw, `draw_pools` (inside `make_drawer`) draws
one turnout per voter pool with `correlated_triangular`; a tied group draws one
shock and every member receives it. The value each pool received is appended to
`draw_pools.turnout_record`, one row per draw, columns in
`draw_pools.turnout_pools` order (the pools `pool_spec` kept). `run_model`
carries them out as `ModelRun.pool_turnout_draws`, shape (draws, pools), with
`ModelRun.pool_turnout_names`. The interactive re-weights the published draws
by these (`audits/2026-09-28-interactive-architecture/PLAN.md` §3).

**It changes no draw.** The record reads values already drawn and makes no call
on any stream. `tests/test_draw_record.py` verifies this at Johannesburg 2026, seed
20261104, the shipped draw count, under `HASH_SEED`: every `*draws` field of
`ModelRun` is identical to the code before the recording (commit `4711a15`,
run from a `git archive` copy), both reproduce the published `seat_draws.csv`
byte for byte, and the record equals what an independent wrapper around
`correlated_triangular` captures, pool by pool and draw by draw. The
comparison with `4711a15` expires at the first legitimate change to a drawn
number and is then retired, not re-pinned (the test module's docstring).

`montecarlo.main` does not write the record. `src/export_draws.py` does (next
section).

**The whole votes per ballot (2026-10-08).** In the same way, each draw's
whole votes on each ballot, exactly the two dicts the loop hands
`seats.eligible_parties` (`ward_totals_d`, `pr_totals_d`: each party's ballot
total rounded to a whole vote), are copied into `ModelRun.ward_vote_draws` and
`ModelRun.pr_vote_draws`, shape (draws, parties), int64, columns in `universe`
order, and traced as `42a_pr_vote_draws` / `43a_ward_vote_draws`. No random
call and no reordering. That they moved no draw is shown once, against the tree
before them, by `audits/2026-10-07-prediction-restructure/backtest/no_draw_moved.py`
(result in MODEL-LOG §1.291); `test_draw_record.py` compares every `*draws`
field of the live run with an independently wrapped one; and
`test_chain.py::test_the_seat_law_on_recorded_votes_is_every_draw_s_council`
shows the seat law on one draw's recorded votes and winners gives that draw's
council. They are kept whole because shares times a total do not reproduce
the integers (`audits/2026-10-07-prediction-restructure/s1/SPEC-A.md` M4).
Rule A reads them (below).

## The interactive's draw file and its re-weighting — `src/export_draws.py`, `src/reweight.py` (2026-09-28)

**Why the page re-weights instead of re-running.** The published draws already
vary in what the turnout and poll controls move: each draw carries its four
pool turnouts (above) and its PR shares. So a control is a weight on each of
the published draws, and every figure on the page is a weighted statistic of
them (`audits/2026-09-28-interactive-architecture/PLAN.md` §§2-5, build steps
S2 and S4). Controls that change how the model draws (within-pool movement,
the by-election weight) are not re-weightings; they are PLAN.md §6's grid of
full runs, not built here.

**The file.** `export_draws.py` calls `run_model` directly, once per seat law
(`deduct`, `expand`, `level`, `cap`), each in its own process under
`montecarlo.HASH_SEED`, and writes `base.bin` and `manifest.json` to `--out`
(never into `data/`). Per draw: seats for every party that wins a seat in any
draw under any law, plus `OTHER`, under each law, with each law's majority
threshold and council size; each ward's winner as a one-byte code; each
party's whole votes on the ward ballot and on the list ballot (blocks
`ward_vote` and `list_vote`, the run's whole universe as columns, nothing
summed into `OTHER`, since 2026-10-08); and the four pool turnouts. Blocks are
column-major, little-endian; seats, wards and votes are exact unsigned
integers of the narrowest width, turnouts are float64. A list share is
`reweight.list_shares(list_vote)`, the one definition; the stepped PR-share
block it replaced is gone (owner, 2026-10-08), and with it the manifest's
`combined_share` refusal: the combined tally is
`seats.eligible_parties(ward_vote, list_vote)` per draw, computed by its
reader, never stored. `export_draws.ballot_faults` refuses a manifest missing
either block, storing one as anything but whole votes, putting them on
different columns, or carrying the refusal beside them. The layout has one
definition, `reweight.pack` / `reweight.unpack`, because the reader is the
browser.

Before writing, the export refuses if the four laws did not draw identical
turnouts, votes and ward winners (a weight could then not cross laws by
draw index, PLAN.md §7), if a draw's seats do not sum to its council, or if a
pool spec's `artefact_key` changed while it ran. The manifest's `artefact_key`
carries the fields `declares.py` requires of a run, plus `code_sha256` over
the source directory the model was imported from and each law's scenario
levers. `declares.py` does not scan the file yet: it is written outside
`data/processed`, and nothing publishes it.

**The engine.** `reweight.py`, pure Python and numpy, the file the page runs
under Pyodide. Every party is treated identically (DESIGN-decided §8).

* **Turnout:** `turnout_tilt` takes a shift for EVERY pool (0 holds a pool at
  its published mean) and returns exponential-tilting weights, w ∝ exp(λ·t),
  with λ solved by Newton's method so the weighted mean turnouts hit all four
  targets. Of the weightings that hit them, it is the closest to uniform in
  Kullback-Leibler divergence. There is no single-pool form: the pools' turnouts
  are correlated, so selecting on one lifts all four (PLAN.md finding 3). A
  target outside what the draws span is refused, not extrapolated. The
  Newton step is halved until the dual falls (Armijo), with an allowance of
  `DUAL_ROUNDING` for the dual's own rounding: near the optimum the true
  decrease is below what a float resolves at the dual's size, and without
  the allowance a target well inside the draws was refused "did not
  converge" (owner's test, 2026-10-05: a poll at one trust step).
  Convergence is judged on the gradient alone.
* **Polls** *(superseded 2026-09-28: the `trust` exponent and `combine` are
  gone; see the dated paragraph "Changed 2026-09-28, after the blind pollster
  review" below)*: `poll_weights` is an independent-normal likelihood on each draw's
  PR shares, with the draw and the poll both renormalised to the polled
  parties, raised to the power `trust` in [0, 1]. Trust 0 is uniform weights
  exactly; trust 1 is "the draws closest to this poll", not "the poll happens".
  `sigma` has no default: it is the reader's. `combine_polls` averages the
  switched-on polls on a common base and returns the spread between them.
* **Floor:** `effective_draws` is Kish's (Σw)²/Σw²; `require_effective` refuses
  below `MIN_EFFECTIVE_DRAWS` (JUDGEMENT-CALLS §N1).
* **Statistics:** `weighted_quantile`, `weighted_probability`,
  `ward_win_probability` (Jeffreys, with the effective sample in place of N) and
  `weighted_mean_se`. Each reduces to the published formula bit for bit under
  uniform weights, so the untouched page is the published forecast.

**What stands behind "moving turnout".** The tilt matches a mean; moving turnout
in the model moves the whole distribution. `tests/test_reweight.py` compares
the two for Black African turnout +5 points, the other pools held, against a
paired re-run of the model with that pool's drawn turnout shifted after the IPF
on the same seed (pre-registered in
`prereg/2026-09-28-reweight-against-paired-rerun.md`; the result and the
effective draws are in MODEL-LOG). The agreement is a measurement at that size
of move, not an identity.

**Tested** in `tests/test_export_draws.py` (the four published seat files and
`ward_draws.csv` rebuilt byte for byte from the file; conservation; the
manifest's declaration; the size budget; each refusal on constructed runs) and
`tests/test_reweight.py` (uniform weights against `forecast_summary.json` and
`ward_winner_probs.csv`; the paired re-run; the refusal floor; the statistics on
constructed inputs). Not yet tested: the same fixture under Pyodide
(INTEGRATION.md §3b's third check).

**Changed 2026-09-28, after the blind pollster review (MODEL-LOG §1.273).
Where this conflicts with the bullets above, this paragraph is current.**
`poll_weights(shares, columns, poll, *, sd)` has ONE control, the reader's poll
error `sd`; the `trust` exponent is gone, because a likelihood at σ raised to t
is the likelihood at σ/√t (finding A8). `sd = inf` returns uniform weights
exactly, the published forecast. `combine` is deleted: a turnout tilt is solved
ON the poll's weights, `turnout_tilt(turnouts, shift, base=poll_weights)`,
w ∝ base·exp(λ·t), so the turnout targets (published means plus `shift`) hold
under the weights returned; multiplying a tilt solved on uniform weights by the
poll's missed them (finding A7). With a base, a zero shift holds turnout at the
published means rather than doing nothing. Beside Kish's count, each quantile
reports `quantile_effective_draws` (the draws that would place its level as
precisely; n under uniform weights) and `tail_effective_draws` (Kish over the
draws on its own side, which its value is read from); `figure` returns both
with the value and, for poll weights, `POLL_LABEL`, "the model's draws nearest
this poll". `require_effective` and `export_draws.export` resolve their
defaults (`MIN_EFFECTIVE_DRAWS`, `LAWS`) at call time.


**Added 2026-10-03, with /your-forecast/ (the owner's sweep, lane Y).** Two
more uses of the same draws, neither of which moves a forecast:

* **Our prediction — `src/prediction.py` (rule A, 2026-10-08; replaced
  `src/start_rule.py`'s seat-first start).** The forecast reduced to one
  complete result: each ward to the party that wins it in the most
  simulations (`ward_calls`; a tie drawn by the seeded lot under
  `seats.ward_key(lot, ward)`, `lot` being the run's identity, whatever the column
  order; the code first in string order until 2026-10-09), each party's mean
  ward-ballot and list-ballot
  whole votes (`mean_votes`; exact integer arithmetic, half to even, when the
  weights are unit or all equal; the weighted mean rounded half to even
  otherwise), every column kept under its own code; `rule_a` returns
  `{ward_calls, ward_votes, list_votes}` and refuses, naming it, a missing
  ballot, a ballot that is a copy of the other, or a call for a party the
  votes do not carry. Seats are never stored: `seats_of` is the one
  composition of the seat law for a prediction or a reader's forecast
  (the two others are `run_model`'s draw loop and
  `benchmarks.council_from_shares`, which seats the naive baselines)
  (`eligible_parties` → `outside_pool_wards` → `allocate_with_overhang` under
  the statutory rule, `montecarlo.COUNCIL` set for the call), and
  `reader_seats` delegates to it. Callers: `score_forecasts.model_forecast`
  (the scorer), `build_make.start_state` (section 2's start, unit weights;
  `build_make.our_prediction` for a caller that needs it before
  `forecast.json` exists), and the page (`page.handoff` on the reader's
  weights, and `page._ward_calls`, the map's call). The tie rule alone is
  `prediction.top_party`, which the ward calls made from counts or
  probabilities also use (`scenarios.modal_winners` for the published claims,
  `diagnose.main`, `score.score_wards`, and since 2026-10-09 the winner
  column `montecarlo.main` writes). The run's identity reaches each caller
  one way: `ModelRun.lot` in a run, `x-seat-context["lot"]` in the schema
  (written only by `worker-api/tools/make_schema.mjs`, from the model
  artefact `build_make.run_lot` fills from the served manifest's
  `artefact_key`), and the
  same manifest on the page (`page._lot`). JUDGEMENT-CALLS §Q;
  `tests/test_prediction_rule.py` holds it to one definition, following
  renamed copies of the draws' arrays, with its exemptions listed there.
* **"Analyse my forecast"** — `within_band` (the weighted share of draws within
  a band of a reader's figure) and `ward_calls_likelihood` (each ward call's
  chance, their sum, and the reader's set of ward results ranked among the
  draws' own by the sum of log ward chances), on the published draws, unit
  weights. The bands and the method are JUDGEMENT-CALLS §N3. The seat line
  (`seat_error_line`) is derived: the median, over the draws, of the seat
  error of the model's own middle forecast (`middle_seats`, each party's
  median seats), rounded down (JUDGEMENT-CALLS §N4).

## A reader's prediction, seated by the statute alone — `src/reader_seats.py` (2026-09-28; two ballots 2026-10-08)

**What it does.** DESIGN-decided §9, with BRIEF change 13
(`audits/2026-10-07-prediction-restructure/`): a reader's prediction holds a
winner for every ward and each party's whole votes on the ward ballot and on
the list ballot, and seats follow from Schedule 1 with no model level, band or
pool involved. `reader_seats.reader_seats(ward_votes, list_votes,
ward_winners, context)` validates, then calls `prediction.seats_of`, the one
composition of the seat law for a prediction or a reader's entry (`run_model`'s
draw loop and `benchmarks.council_from_shares` are the two others):
`seats.eligible_parties` on the two ballots as given (a party with a list vote
is pooled on its ward plus list votes), `seats.outside_pool_wards` for C and D,
and `montecarlo.allocate_with_overhang` at `montecarlo.STATUTORY_VALUES`'
`overhang_rule`, the pool in the context's roster order (which decides nothing:
an exact tie at the last seat is drawn by the seeded lot under the context's
`lot`). It returns ward, list
and total seats per party (C and D ward winners included, so totals sum to the
council), the council and majority, the item 16 parties and their excess, the
pool (`{party: ward + list votes}`), and the stated assumption. Each ballot's
total is the sum of its votes; nothing scales them.

**It refuses rather than guesses**: a malformed context; vote maps that are not
roster parties to whole non-negative votes (`bool` included); a ballot with no
vote; a list vote for a party the roster lists with no PR list; missing or
unknown wards; a ward won off the roster; **R1** a ward winner with no ward
vote; **R2** a ward winner with a PR list and no list vote (guard G14: the
statute would otherwise move its wards to D in silence); and an allocation the
seat law cannot complete. Each is a sentence in `errors`; no seats are
returned alongside one. A ward winner and its citywide ward vote are set
separately, so an entry can be impossible as a whole (many wards on a small
ward vote); that is allowed.

**The context** (`city`, `target`, `council`, `wards`, `parties`,
`no_pr_list`, `lot`) is built at build time by `context_for` / `context_from_run`,
with council and ward count from `cities/<city>.toml`, and shipped as JSON.
Nothing is read from disk at call time.

**Under Pyodide** the module needs `prediction`, `montecarlo` and its
module-level imports (`cityconfig`, `coalitions`, `fold`, `parties`,
`polling`, `seats`): numpy and the standard library only. That dependency
exists because item 16 lives in `montecarlo.allocate_with_overhang`, not in
`seats.py`.

**Tested** in `tests/test_reader_seats.py`: every draw of a native run at
Johannesburg 2021 and 2026 is reproduced exactly from its own recorded whole
votes per ballot (`ModelRun.ward_vote_draws`, `pr_vote_draws`) and ward
winners, the pool equal to the allocator's own input; statute invariants on
real draws and random reader edits; two item 16 councils worked by hand; one
refusal per validation, R2 with its no-PR-list counterpart seated through D;
and an import-and-allocate run with pandas unimportable and every file open
refused. The seat Worker (`worker-api/seats-py`) passes the same four
arguments through and copies this module's import closure, which the test
holds equal to its `FILES` list both ways.

**What was.** Until 2026-10-08 the input was each party's share of the
COMBINED vote and a fixed `total_votes` (the schema's `x-total-votes`), turned
into whole votes by largest remainder (`combined_votes`) and handed to the law
as list votes alone (JUDGEMENT-CALLS §M1 and its amendment; before 2026-09-28,
PR shares standing for both ballots). A reader could not say which ballot a
vote was on, and the list ballot an entry is scored on was not something the
reader set.

## A reader's entry, version 2: encoding, validity and the editor's bounds (2026-10-08)

Slice B of `audits/2026-10-07-prediction-restructure/` (`s1/SPEC-B.md`, as
amended by `s1/SYNTHESIS.md`). An entry is a reader's prediction (STYLE.md
rule 11), and our own prediction is held in the same shape.

* **The version.** `interactive/js/make-state.js` `FORMAT` is the one
  definition; `worker-api/tools/make_schema.mjs` writes it into the schema as
  `properties.v.const`, and Python reads it there
  (`score_forecasts.entry_version`). An entry of another version is refused by
  name: by `validate.js` (field `v`), by `score_forecasts.seat_forecast` and
  `score`, and by `rank_entries.rank_entries`, which names the seal ids (guard
  G12). The D1 table carries the version (`migrations/0002_entry_version.sql`;
  rows stored before it read 1).
* **The encoding** (`make-state.js`): the palette of ward winners, the calls
  packed in `ceil(log2 k)` bits, one LEB128 varint per roster party for the
  ward ballot, one per party for the list ballot, then the coalition. Each
  ballot's total is the sum of its votes, carried in `f`; no total is fixed by
  the schema (`x-total-votes` and `x-share-sum` are gone). `context_ref` is a
  hash of the roster and the wards only, so new bounds or a new roll do not
  break a link.
* **Validity**: each ballot holding a vote, R1, R2, no list vote for a party
  with no PR list, whole non-negative votes, and nothing else, in four
  readers that differ in one place, a roster party missing from a ballot:
  `builder-state.js` `invariantErrors` and `worker-api/src/validate.js` refuse
  it (keys must be exactly the roster); the decoder cannot produce it (the
  encoding carries one varint per roster party); `reader_seats` takes it as
  zero votes, because `score_forecasts.ingest_result` passes the real result's
  counts, in which a party that did not stand on a ballot has no entry. An
  unknown party is refused by all four.
* **Our prediction on the page** (`build_make.start_state`): the prediction
  object plus `start.f`, written by one node call to the page's own encoder,
  which the build refuses unless `decode(f)` is the object (guard G7); the
  page opens on `decode(start.f)` and throws if it is not
  `stateFromPrediction(start)`. `start.out_of_bounds` is the parties outside
  the editor's bounds, a reported fact. The hand-off from section 1
  (`page.py` `handoff`) is the same object under the reader's weights;
  `builder-state.js` `stateFromPrediction` is the one entry from an object,
  and refuses a missing ballot, party or ward by name. `make.js` `follow()`
  shows that sentence when a hand-off is refused or fails (guard G8).
* **The editor's bounds** (`build_make.editor_bounds`, the schema's
  `x-editor-bounds`; JUDGEMENT-CALLS §R; slice B2a since 2026-10-09,
  MODEL-LOG §1.294). Regenerated from the result files at every build, each
  with its provenance; the page reads every figure from there.
  * **Shape**: `q_win` and `q_run` (the lowest winning and highest runner-up
    share of a ward's vote) and `gap_min`, `gap_max` (list share minus ward
    share, in points): the past extremes (`panel_extremes` per election, every
    metro) widened by the mean of each quantity's record events, or by
    `EDITOR_WIDEN_PP` where it has fewer than `MIN_RECORD_EVENTS`
    (`shape_allowances`); `q_run` capped at `RUNNER_UP_MAX`.
  * **Ward ranges** (`ward_ranges`): a party's share in a ward at the
    preceding local election (`ward_priors`, through `montecarlo.ward_parts`),
    moved by the least and greatest swing of its starting-share bin
    (`SWING_BINS`) over every metro's consecutive local pairs, parties standing
    both times (`swing_panel`, `swing_extremes`), widened by the ward
    allowance. A party with no vote in the ward takes its citywide share; a
    party new to local elections its national share (`npe_priors`) and the
    national-to-local changes; a party with neither the newcomer cap
    (`party_ranges`).
  * **Citywide limits** (`city_limits`): the same rule on citywide shares, the
    kind of history (`party_kind`) shared with the ward ranges,
    the prior weighted by `e[w]`, each ward's share of the expected ward vote
    (2026 roll times the preceding local election's VD ward-ballot turnout,
    `expected_ward_shares`).
  * **Allowances** (`allowances`): the mean of the pooled record events
    (`record_events`; a record per bin and direction, rounds by election)
    of ward swings and of citywide swings, mergers, splits and collapses left
    out (`exclusions`, thresholds in JUDGEMENT-CALLS §R13).
  The bounds limit the editor only: a state from a link, a hand-off or our
  own prediction may lie outside them and opens with a note naming the party
  (`outOfBounds`); each out-of-bounds value is clamped when it is next edited:
  a ward vote outside its limits by the next change to any ward vote or ward
  call (the others are rescaled inside theirs), a list vote outside its gap
  range only when that party's list vote is next set. The note goes once the
  state is inside the bounds.
* **The editor** (`builder-state.js`). For the calls on the map: each ward's
  ranges with the shape applied (`wardCell`; the winner at least `q_win`, the
  others at most `q_run`), the least and greatest share each party can hold
  there in closed form (`wardRange`; a ward with no share vector falls back to
  the shape alone and is named), summed by `e[w]` into the per-party box
  (`boxOf`, each (ward, winner) computed once), intersected with the citywide
  limit (`limits`; where they do not meet the map wins and the conflict is
  named; floors past the ballot or ceilings short of it are eased in
  proportion), in whole votes (`wardLimits`, a ward winner keeping one vote).
  `setWardPercent` clamps the party to its limits, says what set the clamp
  (its wards, its citywide limit, or the other parties' limits), and rescales
  the others' ward votes inside theirs by bounded largest remainder
  (water-filling); every list vote then follows its party's new ward share
  with its gap kept, inside the gap bounds (`listFollow`). `setListGap` sets
  one party's gap, rescales the others' list votes, and reduces the change to
  the largest that keeps every gap inside. A change of calls brings every
  ward vote into its new limits (`clampToBounds`) and names the parties it
  moved, the conflicts and the fallback wards. `make.js` shows one row per
  party: the ward-vote slider (its ends at the party's limits), and a
  collapsed "Adjust list vote" in points; a live line states each ballot's
  total.
* **One entry schema** (guard G13): the schema `build_make` writes into
  `your-forecast/forecast.json`. The site Worker validates a sealed entry
  against it before storing (`share-edge.js` `entryRow`); the dormant account
  store (`worker-api/src/forecasts.js`) imports it from there; the placeholder
  `worker-api/generated/forecast.schema.json` and the prototype modules that
  read it (`f.js`, `api-stub.js`, `interactive/f/`, the save path of `api.js`)
  are retired. `tests/test_site_structure.py::test_one_entry_schema` holds the
  set of files naming or importing a schema both ways.
* **The old entries** were test entries (owner, 2026-10-08): no export.
  `rank_entries --clear-version 1` prints the count and deletes only with
  `--confirm <that count>`, at release, when the owner approves it.

Tests: `tests/test_score_forecasts.py` (version, key 3 on the list ballot),
`tests/test_rank_entries.py` (version, clearing), `tests/test_entries.py`
(columns composed from every migration, the stored body),
`tests/test_your_forecast_page.py` (the start is `decode(f)`, the bounds
regenerated from the panel), `interactive/tests/builder.test.mjs` (random
walks valid, inside the bounds, seated by CPython; R1 and R2 on each ballot),
`interactive/tests/make.test.mjs` (G7, the consumers of `start.f`, G8),
`worker-api/test/validate.test.js`, `worker-api/test/node/build.test.js`.

## Mergers — `pools.apply_mergers` (F5, 2026-09-29)

The inverse of a split. `pools.MERGERS` holds each declaration as data: the
partners, a date, and the source. For a target whose polling day is after that
date, `apply_mergers` reads the target's roster: a partner on the ballot
inherits, a partner off it hands over `MERGER_RETENTION` of its share
(JUDGEMENT-CALLS §O1). It moves nothing when every partner is on the ballot,
when none is, or when the roster is unknown, and it refuses when two partners
are on the ballot and another is off it.

**It only adds to a record the successor already holds.** The test is per
share dict: RISE, with a 2024 national share and no 2021 local one, receives
GOOD's national share and not its local one, so its spine route stays
national-only.

**Where it runs** (`pools.MERGER_CONSUMERS`, scanned in both directions by
`test_roster_aware_baseline.py`):

* `montecarlo.run_model`, on the national baseline and every VD's shares,
  before `levels.absent_from_ballot`, which then removes the predecessor's
  unretained remainder; and on the preceding local PR shares (`prior_pr_share`)
  before the spine and `blended_centres`. The ward/PR ratios keep the unmerged
  2021 ballots. The transfers made are in `scenario["_mergers"]`.
* `pools.emit_pools`, on the spec's baseline before the off-ballot drop; the
  successor's pool vector becomes the mass-weighted blend of its own and the
  predecessor's (`pools.merged_vector`). The spec lists the transfers under
  `mergers`.
* `theta_residual._residuals_cached`, so Key 4 measures the baseline
  `run_model` uses. No declared merger predates a held election, so this moves
  no row today.

## `_nest_holding_silent` re-holds a pool its own re-fit silences (2026-09-29)

Holding a silenced pool at the city's rate re-fits the others, and that re-fit
can drive a second pool to the 0.0 corner. The function now checks the re-fit,
holds any newly silenced pool by the same rule, and re-fits again until no
populated pool is silent; it raises `HoldCascadeRefused` if that would hold
every populated pool. Every held pool is returned, so `PoolCounts.imputed` and
`rates_on_a_bound` list them all. On the fitting years of the declared targets
the cascade does not occur (MODEL-LOG §1.275), so the guard moves no
spec today.

## Scoring forecasts against the result — `src/score_forecasts.py` (2026-09-29)

One scorer for the model and every reader (DESIGN-decided §5 and §13,
INTEGRATION.md §3e); it must be frozen before polls open on 4 November.

* `ingest_result(path, city, target, roster, aliases, official)` reads a
  cleaned IEC VD file (the `ingest_lge.py` output, not the raw download). Names
  go alias → `parties.canonical`, and a code outside the certified roster
  (`certified_roster`, from `[roster]` via `pools.declared_roster`) is refused
  with the list. Ward MDB ids lose the city's `ward_prefix`; a tied ward is
  refused. The council is seated by `reader_seats` on the actual ward and list
  votes — the path readers take — with ward-only parties as `no_pr_list`, and an official table is compared
  party by party, chamber, C and D, every disagreement recorded.
* `seat_error`, `wards_called`, `list_vote_error`: the three ranking
  measures (JUDGEMENT-CALLS §N4), as array functions over a last axis of
  parties or wards, so the same definitions score one result here and every
  published simulation on /your-forecast/ (`page.py`'s `analyse`, summarised
  by `reweight.scored_as_results`). `aligned` puts a forecast and an actual
  array on the union of their parties, zero where one side lacks a party.
  `reader_seats` is imported inside the functions that seat a council, so the
  page can import the measures without the seat code.
* `score(forecast, schema, result, seat_source)` takes the stored entry
  (version 2; another version is refused by name) and the entry schema,
  re-seats it with `reader_seats` on its two ballots, and returns the seat
  total error, the correct ward calls and the list-ballot vote error (the
  entry's list votes as a share of its own list total, against
  `ingest_result`'s `list_share`: list against list, guard G15), each with per-party or
  per-ward detail, plus, for information, the ward-count error (wards won per
  party, from the ward winners on both sides) and the ward/list split per
  party. It refuses a result whose councils disagree until `seat_source` is
  named.
* `model_forecast(...)` is our prediction as the scorer holds it: rule A
  (`src/prediction.py`) on the draws' ward winners and both vote blocks, in
  the schema's ward order, with `outside_roster` recording the rule-A vote off
  the roster per ballot (a positive one is refused), in the entry's own shape
  (`v`, `ward_calls`, `ward_votes`, `list_votes`) so `score` reads it as it
  reads a reader's.
* `rank_key` / `rank`: the owner's lexicographic ranking (2026-10-03,
  JUDGEMENT-CALLS §N4, superseding DESIGN-decided §13) — seat total error
  ascending, then correct ward calls descending, then the list-ballot vote
  error ascending; the ward-count error and the split are not keys. Full ties share a competition rank;
  `saved_at` orders a tie so the earlier save names a single winner. `rank`
  raises, naming each one, if any forecast is unscorable (the seat service
  refuses those at save with 422), rather than exclude it.

Tests: `tests/test_score_forecasts.py`. Findings: MODEL-LOG §1.276, §1.277.

## A reader's forecast, shared — `src/share-edge.js`, `src/seal.js`, `interactive/js/share-card.js` (2026-10-03)

The design and the owner's decisions: `audits/2026-10-03-share-design/`.

* **The cards.** `share-card.js` is the one builder of every share card, as
  SVG (owner, 2026-10-06: one design): a reader's link card (1200×630),
  story card (1080×1920) and return card (two forecasts), and the model's own
  card at the two sizes (`modelCardSVG`, black and white, for section 1
  untouched). Each but the return card carries the council graphic, the
  table and the ward map. The story layouts size their blocks first, draw the
  widest map that fits, and spread what is left evenly over the gaps down to
  `STORY_TEXT_BOTTOM`. A winner whose colour has no hue is marked in the
  card's ink (`markColour`), and every party name is clipped to its column.
  The page draws them in the browser for the one share sheet
  (`share-sheet.js`, used by `play-share.js` and `make-share.js`); the site's
  Worker draws the link card as the forecast's preview image. A reader who
  moves section 1's settings shares section 1's hand-off as a reader's
  forecast, sealed through the same `/seal/1` (`make.js` `setHandoff`: the
  hand-off seated in the seat Worker's `handoff` lane, its badge from
  `analyse`).
  `forecastSpec` takes the seat law's answer, the badge (words only: no card
  prints a chance or the closeness figure; each card prints `verdictLine`,
  what the badge says: "We think this prediction is <phrase>, but time will
  tell."), the reader's vote, and forecast.json's
  `baseline` (the previous council election per roster party, from
  `build_make.baseline`); it adds no figure of its own. The council graphic's
  geometry (`councilLayout`, `stepPath`) is shared with the arrival view.
  Text is measured with the IBM Plex faces that draw it (`card-fonts.js`,
  generated from `src/card-fonts/` by `interactive/tools/card_fonts.mjs`).
* **The badge** comes only from Python: `reweight.outcome_badge` (the
  council in words, `reader_outcome`; and the badge, `closeness_badge` of
  `closeness`, JUDGEMENT-CALLS §N10). The closeness is measured from the
  published prediction (`forecast.json` `start`: seats and list votes) and
  banded in the owner's fixed ten-point bands (`reweight.CLOSENESS_BANDS`):
  the page sends the prediction with `analyse` (`make.js` `ours`) and the
  seat Worker reads it from the site's `forecast.json`
  (`entry.load_prediction`). The closeness itself is
  never returned; the answer carries the badge's `phrase`
  (`reweight.CLOSENESS_PHRASES`). The analysis prints the badge at twice the
  arrival view's size, with `verdictLine(phrase, "your")` and `SEALED_LINE`;
  the arrival view prints `verdictLine(phrase)` and `RANKING_SENTENCE`
  (share-card.js, one definition each; `SEALED_LINE` ends with
  `RANKING_SENTENCE`). The cards draw the owner's badge for the words
  (`src/stamps/reader-*.svg`, served at `/stamps/`) through share-card.js
  `stampSVG`, the one function that places a stamp, which prefixes the
  stamp's internal ids per embed. The page reaches it through `page.py`'s `analyse`;
  the Worker through the seat Worker's `/v1/card`
  (`worker-api/seats-py/src/entry.py`), which seats the link's picks with
  `reader_seats` and reads the published draws from the site. A link's own
  figures are never read for an image.
* **Our forecast's card and sheet** (owner, 2026-10-13; `play-card.js`,
  `play-share.js`, `share-card.js` `modelCardSVG`): the card is drawn in the
  browser, never by the edge. It carries `whysoseriouscity.svg` (the umbrella
  logo without its tagline, traced from the owner's file), "forecast" and the
  forecast's date, read from `forecast.json` `forecast_date` (`build_make.py`:
  the day of `export_draws.run_time`, the draws manifest's own
  `artefact_key.time`, never typed and never the ledger's newest row, which a
  new forecast enters only after the build that prints its date; the pages'
  `generated_date` reads the same instant through `published:run_date`, and
  `og_pages.forecast_spec` refuses a build where the two differ). A reader's
  card prints the reader's own date (`madeText`: "Sealed" or "Made", from the
  seal or the day the reader made it), never the forecast's; the same words head the alt text
  and the native share (`forecastWords`). It carries no name, and the sheet
  does not offer the name field for it (`nameShown`), so sharing it seals
  nothing: `section1Share.fields()` is `null` until a setting is moved.
* **The edge** (`share-edge.js`, routed by `src/worker.js`): `/s/` counts a
  share arrival (channel `share`, the button) and redirects to the arrival
  view; `/your-forecast/?f=…` gets its og: tags pointed at
  `/og/6/link.png?…`, which is drawn from `/v1/card` over the `SEATS` binding,
  rasterised by resvg (`src/og-render.js`), cached at the edge by the link and
  the draws' hash (a year when the link's seal checks, an hour otherwise), and
  is `/og.png` on any failure.
* **Sealed links** (`seal.js`): HMAC-SHA256 under the Worker secret
  `SEAL_KEY` over `v`, `c`, `f`, `n` and the Worker's clock; refused from
  `election.polls_open` (`content/joburg/election.toml`) and on preview
  versions. `/seal/1/check` checks the signature before reading the
  forecast, so a link sealed under an earlier `context_ref` still checks
  (`readable: false`). The arrival view checks a link's seal; a card prints a
  time only for a verified seal. A seal shows when a forecast was made, not
  that it was its maker's only one.
* **The name** on every card and image is `play-state.cardName`: the page's
  cleaning, then the owner's blocklist (`worker-api/src/blocklist.js`, copied
  beside the page's modules by the build). The page, both share sheets and
  the Worker use it.
* **The arrival view** (`arrival.js`): `from=1` opens the friend's forecast
  read-only; section 2 stays locked until the reader starts from it or from
  the published start. The share sheet's buttons stay off until the seal
  returns or is refused. The friend's forecast stays in the address (`vs`,
  `vn`) for the return card; its seats come from the page's seat Worker in a
  lane of their own (`make-worker.js`).

Tests: `tests/test_worker_routing.py` (routes, counting, fallback, seal),
`tests/test_share.py` (baseline, polls open), `tests/test_reweight.py`
(badge edges), `tests/test_reader_seats.py` (`/v1/card`),
`interactive/tests/share.test.mjs` (cards, fonts, the edge's card, seals).

## A share image for each page — `src/og_pages.py`, `src/og-pages.mjs` (2026-10-10)

`/forecast`, `/claims`, each article, each claim's own page
(`/claims/<slug>`) and `/your-forecast/` carry an image of their own in
`og:image`, `twitter:image` and `og:image:alt` (`og_pages.designed`); the home
page, `/commentary` and the documents keep `og.png`. OG-IMPLEMENTATION-SPEC.md (audits/2026-10-09-site-batch/) is the
design; this is what runs.

* **Python resolves, node draws.** `og_pages` builds one card spec per page
  from the build's own render: every figure is the `display` string a page
  printed for its token (`stats.render`'s record), and every word is the
  page's or a declared constant. `src/og-pages.mjs` draws each spec with
  share-card.js's primitives, the owner's stamps (`src/stamps/`, placed only
  by share-card.js `stampSVG`, which prefixes each stamp's internal ids per
  embed) and the party logos, and rasterises it through
  `src/og-raster-node.mjs`. It holds layout constants only; the page-kind
  colours come from `tokens.css` (`og_pages.kind_colour`).
* **The build order.** `build_site.main` renders each designed page with
  placeholders in its head (`og_pages.pending`) and holds it. Once every page
  is rendered, `build_site.share_images` builds the specs from the figures
  the pages printed (`og_pages.figure_pool`; a figure printed two ways is
  refused where an image draws it), draws them all in one node process into
  `<out>/og-page/` (`og_pages.render_all`, which deletes every other file
  there and refuses a directory), fills each held page (`og_pages.fill`),
  and only then audits, scans and writes it. Every figure an image prints is
  appended to the publication record under that page
  (`og_pages.ledger_records`). A node failure stops the build; there is no
  fallback image.
* **Names.** `<slug>-<12 letters>.png`: sha256 of the SVG, the card faces and
  resvg's version, written a-p, so the address changes with any figure, word,
  layout, badge or face, and the number scan finds no digit in it.
* **The forecast image's coalitions** are `og_pages.FORECAST_COALITIONS`
  (JUDGEMENT-CALLS §S1): each set's figure is `coal.<key>.majority`, /forecast's
  own token where its coalition table prints one, else computed over every
  party's seats by `stats.coalition_majority`, which refuses a party the
  run's seat file does not name.
* **The forecast map** is the page's own map cut to its `<pattern>`s and
  `<path>`s (`og_pages.map_paths`), and refused unless it holds one outline
  per ward of the geometry.

Tests: `tests/test_og_pages.py` (spec §6: every page its image and every
image a page, every figure a page's, names, badges both ways, tags, glyphs,
the stamps' ids), `tests/test_stat_sources.py` (`history:`,
`coalition_majority`).

### Each claim's page, and the share button on every page (2026-10-11)

SHARE-BRIEF.md (audits/2026-10-09-site-batch/).

* **A claim's page** is cut from the claims page, not rendered a second time:
  `build_site.claim_pages` takes the claims page's template, keeps one
  `<article class="claim">` (render_sheet's card), puts the claim's `label`
  as the title (in a dated span, the claim's `captured` date) under a kicker
  that links back, and a link back to all claims under the card. Each card is
  matched to its claims.toml entry by position and refused unless party,
  verdict and quote agree (`claim_articles`). The address is the claim's
  `slug` in claims.toml (`load_claims`: lowercase words and hyphens, no digit,
  unique), written to `<out>/claims/<slug>.html`, which the static-assets
  Worker serves at `/claims/<slug>` (`html_handling` is the default,
  `auto-trailing-slash`), so no Worker route. The directory is rewritten whole
  each build. The rendered page is re-pointed one level down
  (`build_play.one_level_down`). The claims page links each card to its page
  (`link_claims`), and so does the home page's list of claims
  (`render_home._claims`). Its image is the `claim` layout: the quote, the verdict
  badge, the party logo, the party and the speaker; no figure
  (`og_pages.claim_spec`, image slug `claim-<slug>`). A claim is read one way
  everywhere: `og_pages.printed_verdicts`/`verdict_word`, `claim_logo`,
  `speaker_name`, and `claim_party` (claims.toml's `party_name`, the name the
  card prints, for the page's title, its image and the image's alt text).
* **The share button** (`build_site.share_button`) is one component after
  each page's one `</h1>`, on every page the build writes except
  `/your-forecast/` (its own two sheets) and the portal. Its preview and
  download are the page's own og:image, written in as a relative address so a
  scratch build or a UAT version shows the image beside it; the link it sends
  is the page's canonical address, which `src/js/page-share.js` reads from the
  head. Every document page therefore has its own share card and canonical
  address (DOCS' description, or the standfirst).
* **One sheet.** `src/share_sheet.py` writes every sheet's markup: the one
  `share_button` adds and Your forecast's two, at its `<!-- __YFSHEET:play__ -->`
  and `<!-- __YFSHEET:break__ -->` markers (`build_your_forecast.sheets`, which
  adds the name, seal, entry note and image picker). `src/js/share-dialog.js` holds the sheet's controls (the
  dialog, Copy link, WhatsApp, X, Share…, Download image, the status line);
  `src/js/page-share.js` (site pages) and `interactive/js/share-sheet.js`
  (Your forecast, which adds the name, the seal, the image picker and the
  drawn card) both call it. Your forecast imports it as
  `../../src/js/share-dialog.js`, rewritten to `../../js/share-dialog.js` when
  served (`build_your_forecast.SHARE_DIALOG_LINE`). Its look is
  `src/css/share-sheet.css` (every rule under the dialog's class `sharesheet`;
  `sheet` is the forecast pages' column); `.btn` and the form controls
  (select and text fields) are `components.css`'s.

Tests: `tests/test_page_share.py` (the page set both ways, one button per
page wired to its own image and address, a constructed missing, miswired or
extra button caught, a wrong canonical, og:url, placement or script caught,
each claim's page, image and links, a mismatched card refused, and in a
browser at 375 wide: Share… shown exactly where the Web Share API exists,
the sheet inside the screen on a content-box page).


## Placing a party with no national geography (2026-10-15)

Applies to seeded arrivals and `levels.local_record_only` parties. Order: which wards, then who lives there.

1. **List ballot.** `place_by_pool` sets each voting district's share to `pool-weighted composition x citywide base`, floored at `level_floor` (not `SHARE_FLOOR`, which exceeds these parties' bases). `placement_deviation` clips these columns at `level_floor`, every other column at `SHARE_FLOOR` as before; `dev` is their geography. The list ballot is not masked.
2. **Ward ballot.** As for every party: section "Who stands where" below. Before 2026-10-15 this step compared WardIDs with the crosswalk's ward numbers at 2026 and zeroed these parties' ward ballots (MODEL-LOG §1.306).


## Who stands where: the ward ballot and the list ballot (2026-10-15)

Owner rule, 2026-10-15: a party running for ward seats only is omitted from every citywide calculation and wins only in the wards it contests. MODEL-LOG §1.306.

1. **One source.** `levels.ballots(target, city)` returns each party's ward slate (WardIDs), the set of parties with a PR list, whether absence is a fact (`complete`), and the source: the target's result file (ward-ballot rows; PR-ballot rows) where it exists, else `[roster]` in the judgement file (`[roster.wards]`, `[roster] pr`). `contestation`, `declared_contestation`, `slate_coverage`, `unopposed_wards` and `montecarlo.run_model` read it. `pools.declared_roster` refuses a `pr` name that is not in `parties` and a party in `parties` on neither ballot.
2. **Ward ballot, every party.** `montecarlo.ballot_masks` gives each party a column: 1 in the ward parts its slate covers; all zero for a party the source names with no slate or any party under a complete source (a list-only party); all ones when the slate is unknown (a partial declaration, `ENTRANT`; JUDGEMENT-CALLS §U2). The run's ward keys are mapped to WardIDs by `montecarlo.ward_ids` (identity at a held target; the crosswalk's `Ward_<year>` → `WardID_<year>` at an unheld one). `solve_and_predict(mask=)` zeroes the share outside the slate, renormalises each row over who stands there, and solves the party's citywide ward target on the districts it stands in. The ward tally masks by part and renormalises each part's row. A run whose slated parties match none of its wards refuses.
3. **List ballot.** A party with a slate and no PR list (`Ballots.ward_only`) is ward-only. Per draw, `montecarlo.ballot_targets` takes the ward target from the full drawn vector, then zeroes the ward-only parties' PR targets and renormalises the rest pro rata (JUDGEMENT-CALLS §U1); the PR solve masks their columns to zero. With no PR list they are outside `seats.eligible_parties`, and a ward they win leaves the pool through the D term (`seats.outside_pool_wards`), as in the ground truth (`backtest.actual_result`). The ward seat is the party's council seat: `seats.council_seats` adds it to the draw as that party's own column, so every draw's seats sum to its council (section 6, "Seats outside the pool"; MODEL-LOG §1.308). Until 2026-10-16 the seat draws carried the pool only and summed to `council - D`.
4. **Reported, not dropped.** `scenario["_ballot_report"]` (on `ModelRun.scenario`, and printed when non-empty): slates for parties outside the run, PR lists for parties with no PR baseline in it, parties slated only in wards the run drops, and independents' slates (no run carries an independent; JUDGEMENT-CALLS, the `independent_wards` (C) row). `inputs_preflight` has a REQUIRED row for the PR lists of an unheld target.
