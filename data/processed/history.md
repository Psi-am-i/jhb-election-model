# Historical performance — votes and seats, predicted against actual

9 city-years. Shares are citywide percentages; the model column is the median over draws.

## Headline

| city-year | council | list MAE | ward MAE | seat err (median) | medians sum to | seat err (coherent) | CRPS | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | 270 | 0.67pp | 1.58pp | 22 | 260 | 18 | 18.8 | 92 | 26 | 91 |
| Johannesburg 2021 | 270 | 5.79pp | 5.29pp | 96 | 252 | 94 | 69.2 | 134 | 126 | 126 |
| Tshwane 2021 | 214 | 1.34pp | 1.78pp | 32 | 200 | 32 | 26.3 | 80 | 60 | 76 |
| Ekurhuleni 2021 | 224 | 1.16pp | 1.45pp | 29 | 209 | 20 | 25.2 | 72 | 48 | 67 |
| eThekwini 2021 | 222 | 0.53pp | 1.24pp | 36 | 202 | 32 | 32.5 | 82 | 36 | 77 |
| Cape Town 2021 | 231 | 1.19pp | 2.27pp | 40 | 217 | 32 | 30.9 | 68 | 38 | 64 |
| Mangaung 2021 | 101 | 1.99pp | 0.38pp | 7 | 94 | 8 | 9.0 | 24 | 8 | 20 |
| Nelson Mandela Bay 2021 | 120 | 2.91pp | 3.41pp | 24 | 112 | 18 | 16.7 | 28 | 22 | 27 |
| Buffalo City 2021 | 100 | 3.74pp | 1.77pp | 11 | 93 | 10 | 7.8 | 14 | 12 | 15 |

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber and is the only one comparable to the baselines, which allocate per draw and sum exactly. Lower is better throughout.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | -0.87pp | 3.03pp | **+0.15pp** | 1.74pp | +0.72pp | 1.42pp | 0.00pp (0) | 15 |
| Johannesburg 2021 | -0.87pp | 22.75pp | **-1.14pp** | 9.35pp | +0.49pp | 1.41pp | 1.52pp (3) | 58 |
| Tshwane 2021 | +5.18pp | 5.18pp | **-7.18pp** | 7.21pp | +0.43pp | 1.59pp | 1.57pp (5) | 44 |
| Ekurhuleni 2021 | +2.94pp | 2.94pp | **-3.79pp** | 6.06pp | +0.77pp | 1.37pp | 0.09pp (1) | 38 |
| eThekwini 2021 | +0.02pp | 0.76pp | **-0.22pp** | 8.09pp | +0.03pp | 4.23pp | 0.17pp (3) | 31 |
| Cape Town 2021 | +5.09pp | 5.09pp | **-5.23pp** | 5.66pp | -0.02pp | 2.09pp | 0.17pp (3) | 38 |
| Mangaung 2021 | -2.01pp | 4.88pp | **-0.72pp** | 3.13pp | +1.21pp | 1.94pp | 1.51pp (1) | 12 |
| Nelson Mandela Bay 2021 | +4.15pp | 8.66pp | **-4.94pp** | 5.50pp | +0.79pp | 1.38pp | 0.00pp (0) | 15 |
| Buffalo City 2021 | -3.00pp | 7.81pp | **+0.30pp** | 1.69pp | +1.19pp | 1.45pp | 1.51pp (2) | 6 |

**Totals across 9 city-years:** ranks 1-3 +10.62pp signed / 61.09pp absolute, ranks 4-12 -22.76pp / 48.42pp, ranks 13+ +5.60pp / 16.89pp.

**Phantom mass: 6.54pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -6.54pp rather than to zero.


## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |
|---|---|---|---|---|---|---|
| claimed by the model (forecast-selected — the neutral test) | 65 | 82% | 94% | 95% | 0.581 | 26.8 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 132 | 59% | 85% | 87% | 0.727 | 89.2 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 331 | 84% | 94% | 95% | 0.540 | 11.5 (16.92) |

* **claimed** (n=65) PIT histogram [1, 3, 4, 4, 10, 9, 12, 14, 5, 3] — hump-shaped: the truth lands mid-distribution too often — over-dispersed, the model is hedging
* **seat_holders** (n=132) PIT histogram [1, 2, 4, 4, 10, 10, 17, 29, 23, 32] — approximately flat; mean PIT 0.73 — the model under-predicts seats
* **all** (n=331) PIT histogram [23, 33, 27, 25, 37, 32, 36, 44, 36, 38] — approximately flat

The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ² column is the test of uniformity; the level-free dispersion table is the test of width.**

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. Five of its columns across the nine city-years carry PIT exactly 1.0 — parties the model gave zero seats in every draw, present only because they won a seat. It is a mixture of an outcome-selected set and a neutral one, and the neutral part is itself diluted by ~200 parties correctly at zero on both sides, each a free interval hit and a near-uniform PIT. Two errors pushing opposite ways: `all` tests nothing.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 27 | 0.464 | [0.413, 0.510] | 85% [70–96] | 96% [89–100] | 96% [89–100] | 81% [67–96] | 96% [89–100] | 96% [89–100] |
| ranks 4-12 | 35 | 0.680 | [0.610, 0.733] | 77% [65–91] | 91% [85–100] | 94% [88–100] | 51% [36–70] | 91% [85–100] | 94% [88–100] |
| ranks 13+ | 3 | 0.474 | [0.123, 0.668] | 100% [100–100] | 100% [100–100] | 100% [100–100] | 67% [0–100] | 100% [100–100] | 100% [100–100] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|
| ranks 1-3 | 27 | 0.692 | 0.853 | -0.062 | 0.0358 vs 0.0833 |
| ranks 4-12 | 35 | 0.626 | 0.647 | +0.263 | 0.0327 vs 0.0833 |
| ranks 13+ | 3 | 0.895 | 0.491 | -0.331 | 0.0930 vs 0.0833 |

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2016 | 7 | 100% | 100% | 100% | 0.521 |
| Johannesburg 2021 | 9 | 44% | 78% | 78% | 0.636 |
| Tshwane 2021 | 7 | 71% | 86% | 100% | 0.617 |
| Ekurhuleni 2021 | 8 | 88% | 100% | 100% | 0.645 |
| eThekwini 2021 | 9 | 89% | 89% | 89% | 0.517 |
| Cape Town 2021 | 7 | 71% | 100% | 100% | 0.519 |
| Mangaung 2021 | 6 | 100% | 100% | 100% | 0.631 |
| Nelson Mandela Bay 2021 | 7 | 86% | 100% | 100% | 0.574 |
| Buffalo City 2021 | 5 | 100% | 100% | 100% | 0.560 |


## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.30% | 45.37% | 44.92% | 45.20% | 44.09% | 122 | 121 |
| DA | 39.08% | 39.10% | 38.48% | 40.56% | 38.34% | 108 | 104 |
| EFF | 8.67% | 8.98% | 10.93% | 9.43% | 11.24% | 24 | 30 |
| IFP | 1.16% | 1.42% | 1.71% | 0.97% | 1.74% | 3 | 5 |
| AIC | 0.00% | 1.52% | 1.62% | 1.59% | 1.40% | 0 | 4 |
| ACDP | 0.30% | 0.51% | 0.31% | 0.52% | 0.28% | 1 | 1 |
| VFPLUS | 0.13% | 0.37% | 0.31% | 0.45% | 0.34% | 0 | 1 |
| ALJAMAAH | nan% | nan% | 0.31% | nan% | 0.22% | 0 | 1 |
| UDM | 0.15% | 0.37% | 0.25% | 0.42% | 0.28% | 0 | 1 |
| COPE | 0.33% | 0.58% | 0.21% | 0.36% | 0.15% | 1 | 1 |
| PA | 0.01% | 0.08% | 0.17% | 0.01% | 0.13% | 0 | 1 |
| PAC | 0.15% | 0.36% | 0.17% | 0.08% | 0.09% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 37.53% | 37.62% | 33.22% | 38.88% | 33.97% | 103 | 91 |
| DA | 31.76% | 31.99% | 25.45% | 33.58% | 26.83% | 88 | 71 |
| ASA | 5.70% | 6.31% | 18.12% | 5.34% | 13.98% | 14 | 44 |
| EFF | 13.74% | 14.12% | 10.11% | 15.29% | 11.14% | 39 | 29 |
| PA | 0.04% | 0.11% | 2.96% | 0.04% | 2.91% | 0 | 8 |
| IFP | 1.01% | 1.58% | 2.36% | 1.37% | 2.36% | 3 | 7 |
| VFPLUS | 0.63% | 0.89% | 1.33% | 1.00% | 1.35% | 2 | 4 |
| ACDP | 0.28% | 0.63% | 1.03% | 0.60% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.30% | 0.36% | 0.83% | 0.27% | 1.08% | 1 | 3 |
| AIC | 0.22% | 0.76% | 0.69% | 0.31% | 0.50% | 1 | 2 |
| AHC | 0.02% | 0.12% | 0.43% | 0.09% | 0.47% | 0 | 1 |
| GOOD | 0.10% | 0.36% | 0.33% | 0.24% | 0.40% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 35.74% | 35.60% | 34.84% | 36.26% | 34.42% | 77 | 75 |
| DA | 31.70% | 32.21% | 31.77% | 33.24% | 32.29% | 69 | 69 |
| EFF | 14.04% | 14.41% | 10.43% | 14.80% | 10.94% | 30 | 23 |
| ASA | 5.58% | 6.25% | 9.28% | 5.95% | 7.99% | 12 | 19 |
| VFPLUS | 4.60% | 4.86% | 7.79% | 5.12% | 7.96% | 10 | 17 |
| ACDP | 0.45% | 0.79% | 0.91% | 0.89% | 0.93% | 1 | 2 |
| AIC | 0.32% | 0.59% | 0.81% | 0.16% | 0.38% | 1 | 1 |
| DOP | 0.03% | 0.12% | 0.49% | 0.11% | 0.58% | 0 | 1 |
| PA | 0.01% | 0.05% | 0.48% | 0.05% | 0.52% | 0 | 1 |
| PAC | 0.00% | 0.22% | 0.21% | 0.21% | 0.18% | 0 | 1 |
| IFP | 0.00% | 0.16% | 0.21% | 0.04% | 0.09% | 0 | 1 |
| COPE | 0.00% | 0.13% | 0.19% | 0.16% | 0.20% | 0 | 1 |

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 40.97% | 40.66% | 38.34% | 41.26% | 38.03% | 93 | 86 |
| DA | 27.78% | 28.53% | 28.37% | 29.24% | 29.07% | 63 | 65 |
| EFF | 13.27% | 13.73% | 13.27% | 14.36% | 13.87% | 31 | 31 |
| ASA | 5.60% | 6.16% | 7.36% | 6.19% | 5.84% | 13 | 15 |
| VFPLUS | 2.48% | 2.71% | 3.48% | 2.75% | 3.18% | 6 | 8 |
| PA | 0.17% | 0.22% | 1.87% | 0.21% | 1.89% | 0 | 4 |
| IFP | 0.46% | 1.20% | 1.47% | 0.71% | 1.24% | 1 | 3 |
| AIC | 0.24% | 0.82% | 1.36% | 0.81% | 1.22% | 1 | 3 |
| ACDP | 0.26% | 0.71% | 0.86% | 0.75% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.06% | 0.15% | 0.45% | 0.16% | 0.44% | 0 | 1 |
| PAC | 0.01% | 0.39% | 0.43% | 0.17% | 0.31% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.00% | 1.49% | 0.36% | 1.51% | 0.78% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 43.03% | 42.90% | 42.51% | 42.55% | 41.77% | 95 | 96 |
| DA | 25.88% | 26.06% | 26.33% | 27.55% | 25.57% | 59 | 59 |
| EFF | 10.03% | 10.70% | 10.80% | 10.64% | 10.15% | 22 | 24 |
| IFP | 4.37% | 5.16% | 7.45% | 5.48% | 6.67% | 10 | 16 |
| ASA | 5.54% | 6.28% | 2.35% | 6.18% | 1.50% | 12 | 4 |
| AIC | 0.23% | 0.88% | 1.01% | 0.35% | 0.33% | 0 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.02% | 0.13% | 0.81% | 0.10% | 1.03% | 0 | 2 |
| ACDP | 0.44% | 0.73% | 0.76% | 0.82% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.02% | 0.12% | 0.65% | 0.10% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.09% | 0.24% | 0.61% | 0.24% | 0.51% | 0 | 1 |
| ATM | 0.31% | 0.53% | 0.57% | 0.53% | 0.66% | 1 | 1 |
| MINORITY_FRONT | 0.22% | 0.42% | 0.50% | 0.61% | 0.47% | 1 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 59.72% | 59.47% | 58.74% | 60.23% | 57.78% | 139 | 135 |
| ANC | 21.76% | 21.86% | 18.71% | 21.95% | 18.46% | 50 | 43 |
| EFF | 5.11% | 5.35% | 4.15% | 5.61% | 4.10% | 12 | 10 |
| GOOD | 3.07% | 3.35% | 3.68% | 3.30% | 3.94% | 7 | 9 |
| CAPE_COLOURED_CONGRESS | 0.00% | 0.08% | 2.83% | 0.08% | 2.78% | 0 | 7 |
| ACDP | 2.14% | 2.48% | 2.29% | 2.88% | 2.40% | 5 | 6 |
| VFPLUS | 0.69% | 1.03% | 1.54% | 1.14% | 1.63% | 2 | 4 |
| PA | 0.00% | 1.45% | 1.43% | 1.43% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.66% | 0.87% | 1.19% | 1.21% | 1.32% | 2 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.00% | 0.09% | 0.64% | 0.09% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.00% | 0.09% | 0.62% | 0.09% | 0.65% | 0 | 2 |
| UIM | 0.00% | 0.10% | 0.56% | 0.10% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 48.43% | 48.07% | 51.51% | 49.45% | 49.75% | 50 | 51 |
| DA | 24.70% | 25.48% | 25.48% | 25.99% | 25.98% | 25 | 26 |
| EFF | 11.86% | 12.81% | 11.37% | 12.76% | 11.24% | 12 | 12 |
| VFPLUS | 3.53% | 3.74% | 4.41% | 4.17% | 4.55% | 4 | 5 |
| PA | 1.53% | 2.12% | 1.78% | 2.11% | 1.83% | 2 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.18% | 0.39% | 1.26% | 0.37% | 1.61% | 0 | 2 |
| AIC | 0.58% | 1.54% | 0.84% | 0.80% | 1.70% | 1 | 1 |
| ACDP | 0.25% | 0.73% | 0.70% | 0.77% | 0.74% | 0 | 1 |
| ATM | 0.36% | 0.61% | 0.61% | 0.53% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.38% | nan% | 0.38% | 0 | 0 |
| COPE | 0.01% | 0.33% | 0.30% | 0.14% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.12% | 0.31% | 0.21% | 0.02% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 44.36% | 44.54% | 40.04% | 45.59% | 39.80% | 54 | 48 |
| ANC | 37.37% | 37.35% | 39.60% | 37.09% | 39.26% | 45 | 48 |
| EFF | 7.77% | 8.31% | 6.40% | 8.78% | 6.40% | 10 | 8 |
| NORTHERN_ALLIANCE | 0.06% | 0.19% | 2.09% | 0.20% | 2.18% | 0 | 3 |
| ACDP | 0.81% | 1.10% | 1.68% | 1.20% | 1.64% | 1 | 2 |
| VFPLUS | 0.98% | 1.20% | 1.64% | 1.28% | 1.51% | 1 | 2 |
| DOP | 0.05% | 0.19% | 1.38% | 0.17% | 1.47% | 0 | 2 |
| PA | 0.00% | 1.35% | 1.32% | 1.43% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.06% | 0.21% | 1.11% | 0.22% | 1.05% | 0 | 1 |
| UDM | 0.32% | 0.97% | 1.07% | 1.08% | 1.01% | 0 | 1 |
| AIC | 0.30% | 0.92% | 0.68% | 0.13% | 0.38% | 0 | 1 |
| PAC | 0.02% | 0.40% | 0.51% | 0.13% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 55.88% | 55.11% | 60.51% | 57.17% | 58.35% | 57 | 61 |
| DA | 20.77% | 21.78% | 19.49% | 23.39% | 19.55% | 22 | 20 |
| EFF | 11.47% | 12.49% | 12.37% | 12.70% | 11.76% | 12 | 13 |
| UDM | 0.39% | 0.98% | 1.10% | 0.49% | 0.82% | 0 | 1 |
| PAC | 0.17% | 0.95% | 1.05% | 0.71% | 0.83% | 0 | 1 |
| AIC | 0.54% | 1.59% | 0.97% | 0.40% | 0.45% | 0 | 1 |
| ATM | 0.80% | 1.10% | 0.89% | 0.77% | 0.93% | 1 | 1 |
| ACDP | 0.52% | 0.71% | 0.57% | 0.79% | 0.55% | 1 | 1 |
| VFPLUS | 0.33% | 0.54% | 0.52% | 0.49% | 0.51% | 0 | 1 |
| PA | 0.07% | 0.16% | 0.42% | 0.02% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.07% | 0.16% | 0.34% | 0.03% | 0.10% | 0 | 0 |
| COPE | 0.01% | 0.23% | 0.27% | 0.02% | 0.05% | 0 | 0 |