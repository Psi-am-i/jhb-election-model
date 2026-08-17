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

**The Duncan-Davis bounds are COMPUTED AND NOT ENFORCED. Corrected 2026-08-17.**
This paragraph said "every estimate is projected into its Duncan-Davis interval"
from the day it was written, and nothing projects: `pools.bounds` is read at
exactly one place, `PoolFit.identified` (`pools.py:884-887`), where a narrow
bound sets a display flag. No rate is clipped to it, at any stage.

The bounds themselves are real and are arithmetic: pooled over the metros the
ANC's rate among Coloured voters is provably ≥ 0.4% and among Indian voters
≥ 0.7%, and the unconstrained fit answers 0.2% for both — below its own proven
floor, and left there. Where the bound stays wide (ANC among white voters,
0–20.4%) the rate is flagged unidentified and is a judgement, not a finding.

**This is not a documentation defect; it is the cause of a live one.** The PA's
Johannesburg 2021 fit is a corner solution — 0.5149 on Coloured, exactly 0.0000
on the other three pools, which is FISTA's simplex projection sitting on the
non-negativity boundary — and 0.5149 is **10.5pp above the PA's own Duncan-Davis
ceiling of 0.410**. Implied, that corner gives the PA 34,170 Johannesburg votes
against an actual 27,346, and the ward geography refutes it directly: binning
all 135 wards by Coloured share, 28.1% of the PA's vote arises in wards under
30% Coloured (18.2% in 10–30%, 9.9% under 10%). The emitted "Coloured 1.0000"
vector is that corner, and it is what makes the PA's 2026 level unrepresentable
by the pool layer — see §2 and MODEL-LOG §1.33. Projecting the fit into its
bounds is open work with its own measurement to do; it has not been done.

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
| **First local election** | has a national baseline, never faced an LGE | `pools.first_local_election`: national base × parent θ × ward reach × coherence | **78% within a factor of two**, 45 cases, median ratio 0.85 |
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
| Rank bands, SIGNED and ABSOLUTE, plus phantom mass | `compare_history.rank_bands` | — |
| Pooled coverage + pooled randomised PIT, three populations | `compare_history.calibration_columns` / `.pooled_calibration` | — |
| Ground truth | `backtest.actual_result`, asserted against `official_seats` | ✅ |
| Benchmarks (last-LGE, uniform swing, prior-LGE-noise) | `benchmarks.py` | pre-target only ✅ |
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
