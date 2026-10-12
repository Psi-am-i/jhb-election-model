# Pollster review of the state, 2026-09-26

Worked in the skill's order: instrument, out-of-sample score against a baseline,
where the error is, whether the uncertainty is honest, and only then structure.
Every number below is from `data/processed/history.json` or from
`pools.fit_city`/`fit_joint` re-run read-only in a scratch process.

## 1. The instrument

**Every one of the 24 panel rows carries `in_sample: True`.** The pool
composition comes from Census 2022 and each backtest target predates it, so
`backtest.FITTED_ON["pools"]` flags all of them. The consequence for how results
may be quoted: **"17.2% over uniform swing" is not an out-of-sample statement
about the pool machinery.** It is a statement about a model whose demographic
inputs were measured after the elections it predicts. Nothing in the pool-input
window changes that, and no repair can.

What would: Census 2011 ward tables on the 2011 delimitation, which
`config/dimensions.toml` already names as the highest-value outstanding data
request after home language. With one census there is no slope, so composition at
any other year is that census reprojected and damped.

The other instrument item is already fixed in the pre-registration: the ±148
figure is a bootstrap of the panel *level* and the comparison is paired.

## 2. Where the error is

| target cycle | mean PR vote MAE | coherent seat error, summed over 8 metros |
|---|---|---|
| 2011 | 5.55pp | 329 |
| 2016 | 0.98pp | 162 |
| 2021 | 2.91pp | 242 |

Panel: mean PR vote MAE **3.15pp**, mean ward vote MAE **2.98pp**, coherent seat
error **733**, CRPS **541.5**.

**The ward error and the citywide error are the same size** (2.98pp against
3.15pp), and the modal ward winner is called correctly in 2,120 of 2,191 wards
(96.76%). Read together: the model puts the right party first in nearly every
ward and gets everybody's share wrong by about the same amount everywhere. That
is a level error propagated into every ward, not a geography error.

Johannesburg 2021 is the worst single city-year — 6.29pp, 86 coherent seats,
CRPS 69.4 — and it is the city being published. It carries 12% of the panel's
seat error on its own.

**What follows for the pool-input window.** The window is structure work on a
model whose error is level. It buys honesty and removes claims that cannot be
defended in public; it should not be expected to move the score, and the
pre-registration is right to predict nulls on the seat headline and on ward
calls. Anything that does move the score lives in the level: the citywide vote
at 2011 and 2021 targets, and Johannesburg 2021 in particular.

## 3. Is the uncertainty honest

Two places where it is not, both measured.

**A point estimate is treated as known thereafter.** The Duncan–Davis interval is
computed per party-pool, used to clip the fit, and emitted as
`pools[<pool>].identified` — a list of party codes — which `montecarlo` reads at
`:3959` only to print a warning. Johannesburg 2021: the ANC's Indian/Asian rate is
fitted at 0.1348 inside a permitted 0.0000–0.8030; ActionSA's at 0.2988 inside
0.0000–0.7960. Those enter the draw as points. This is the standard published
criticism of ecological inference (Freedman et al. on King-style EI) and it is
answered by drawing from the interval rather than fixing a value in it.

**Bounded supports.** 245 of 3,417 emitted member cells are exactly zero and 37
party-city-years put over 99.9% of their weight in one pool, across 19 of 24
specs. IPF preserves zeros, so each is a claim that a party wins exactly nobody in
that pool in every draw. `pools_2021.json` puts the PA at 1.0 Coloured, which
asserts 45.6% of every Coloured vote in Johannesburg and nothing from anybody
else. An outcome given probability zero that has occurred is an indefensible
claim before it is a scoring problem.

## 4. The constant-rate assumption fails where it can be tested

Exploratory, not a judged measurement. Johannesburg 2021 wards split into terciles
by a pool's share of their voters, then re-fitted jointly within each tercile.
Only strata where the pool has real share are readable: at a mean share near 1%
the within-stratum fit is degenerate and returns zeros and corners.

Black African pool, the only one with usable share in all three terciles:

| tercile (mean Black African share) | ANC | ActionSA | EFF |
|---|---|---|---|
| low (14.0%) | 0.4604 | 0.3379 | 0.2017 |
| mid (80.5%) | 0.5408 | 0.1588 | 0.1754 |
| high (98.0%) | 0.5228 | 0.1964 | 0.1355 |
| pooled, all 135 wards | 0.5348 | 0.1824 | 0.1595 |

ActionSA's rate among Black African voters is twice as high in wards where that
group is a minority as in the mid tercile. The EFF's falls monotonically as the
group's share rises. The model assumes one rate per pool per city.

White pool: the DA fits at 0.4373 in the mid tercile (5.9% mean White share) and
0.6892 in the high tercile (70.8%), against 0.6785 pooled. **The pooled rate is
the high-share wards' rate, applied to every White voter in the city.** Where a
metro's White voters sit mostly in mixed wards, that overstates their DA support,
and the demand on the pool exceeds what it can supply — which is a second
mechanism for the DA/White capacity breach, alongside the level uncoupling of
§1.259. Both push the same way, so the 14-of-14 pattern does not discriminate
between them.

## 5. Ranked, by expected score improvement per unit of work

| # | item | measurement or judgement | what it buys | what it does not |
|---|---|---|---|---|
| 1 | The level error at 2011 and 2021 targets, Johannesburg 2021 first | measurement | the only place the score is: 86 of 733 coherent seats in one city-year, 5.55pp mean vote error at 2011 targets | nothing about pool structure |
| 2 | Draw a rate from its Duncan–Davis interval instead of fixing it at a point | judgement, then measurement | calibration, and it forecloses the standard EI criticism | sharpness; intervals will widen |
| 3 | Seed unidentified cells so no cell is exactly zero (queue 33) | measurement | removes 245 indefensible zero-probability claims | little on the seat headline |
| 4 | Conservation, queue 30 | arithmetic | four specs stop contradicting themselves about where their electorate is | no score |
| 5 | Cape Town's Indian/Asian pool against the census, queue 31 | measurement | ~145–175k voters move to the pool they belong in | ward calls: Cape Town already calls 342 of 343 |
| 6 | The constant-rate failure above | judgement, and a model change | the mechanism behind the DA/White strain | it must clear the out-of-city gate that age and sex both failed |

## 6. This is wrong, against this is undefended

**Wrong**, with the number: the hard zeros (245 cells); the four specs that emit
three pools while declaring four; the PA at 1.0 Coloured; Cape Town's
Indian/Asian pool at 8–10% of the roll against a census 1.61%.

**Undefended**, which is what draws criticism first: a city-wide rate applied to a
pool that is identified only in the wards where it is concentrated;
`REGISTRATION_MAX = 2.0`, a cap with no stated derivation that binds in five
specs; the 1e-4 cutoff at `pools.py:5991`, which turns a small weight into an
absence and therefore into a permanent zero; and quoting any margin over a
baseline as evidence about machinery whose inputs the project's own ledger marks
in-sample.

## 7. What cannot be fixed with the data held

The composition at any year other than 2022 is one census reprojected, so no
repair recovers a real 2006 or 2011 ward composition. ActionSA's and the IFP's
geography (ward-share R² 0.153 and 0.082) cannot be modelled from four census
race categories: ActionSA's fitted rates are nearly flat across all four, which is
the fit reporting that it has no information. Home language is the named
acquisition, and until it exists the honest statement is that the model cannot see
the cleavage those two parties sit on.
