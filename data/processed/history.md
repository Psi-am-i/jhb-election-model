# Historical performance — votes and seats, predicted against actual

9 city-years. Shares are citywide percentages; the model column is the median over draws.

## Headline

| city-year | council | list MAE | ward MAE | seat err (median) | medians sum to | seat err (coherent) | CRPS | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | 270 | 1.50pp | 2.25pp | 27 | 261 | 22 | 22.8 | 92 | 26 | 91 |
| Johannesburg 2021 | 270 | 6.83pp | 6.09pp | 108 | 254 | 106 | 78.8 | 134 | 126 | 126 |
| Tshwane 2021 | 214 | 2.37pp | 2.64pp | 42 | 202 | 42 | 30.9 | 80 | 60 | 76 |
| Ekurhuleni 2021 | 224 | 2.24pp | 2.34pp | 38 | 210 | 28 | 29.0 | 72 | 48 | 67 |
| eThekwini 2021 | 222 | 1.91pp | 2.44pp | 44 | 204 | 36 | 34.1 | 82 | 36 | 77 |
| Cape Town 2021 | 231 | 2.95pp | 3.85pp | 51 | 218 | 42 | 36.2 | 68 | 38 | 64 |
| Mangaung 2021 | 101 | 0.81pp | 1.27pp | 10 | 93 | 8 | 9.6 | 24 | 8 | 20 |
| Nelson Mandela Bay 2021 | 120 | 2.56pp | 3.06pp | 23 | 113 | 18 | 17.7 | 28 | 22 | 27 |
| Buffalo City 2021 | 100 | 1.90pp | 1.62pp | 8 | 94 | 8 | 7.5 | 14 | 12 | 15 |

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber and is the only one comparable to the baselines, which allocate per draw and sum exactly. Lower is better throughout.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | +0.53pp | 5.45pp | **-0.85pp** | 1.64pp | +0.31pp | 1.01pp | 0.00pp (0) | 15 |
| Johannesburg 2021 | +1.04pp | 26.29pp | **-2.05pp** | 10.69pp | -0.50pp | 1.41pp | 1.51pp (3) | 58 |
| Tshwane 2021 | +7.97pp | 7.97pp | **-9.14pp** | 9.14pp | -0.49pp | 1.38pp | 1.67pp (5) | 44 |
| Ekurhuleni 2021 | +5.67pp | 5.67pp | **-5.68pp** | 7.69pp | -0.04pp | 1.17pp | 0.05pp (1) | 38 |
| eThekwini 2021 | +2.66pp | 4.32pp | **-1.81pp** | 8.58pp | -0.96pp | 4.23pp | 0.11pp (3) | 31 |
| Cape Town 2021 | +7.98pp | 7.98pp | **-7.01pp** | 7.01pp | -1.08pp | 1.74pp | 0.12pp (3) | 38 |
| Mangaung 2021 | +0.59pp | 2.58pp | **-2.76pp** | 3.56pp | +0.73pp | 1.46pp | 1.44pp (1) | 12 |
| Nelson Mandela Bay 2021 | +6.34pp | 7.33pp | **-6.28pp** | 6.37pp | -0.06pp | 1.11pp | 0.00pp (0) | 15 |
| Buffalo City 2021 | -0.83pp | 4.48pp | **-1.30pp** | 1.95pp | +0.54pp | 1.04pp | 1.59pp (2) | 6 |

**Totals across 9 city-years:** ranks 1-3 +31.95pp signed / 72.07pp absolute, ranks 4-12 -36.88pp / 56.63pp, ranks 13+ -1.55pp / 14.57pp.

**Phantom mass: 6.48pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -6.48pp rather than to zero.


## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |
|---|---|---|---|---|---|---|
| claimed by the model (forecast-selected — the neutral test) | 56 | 57% | 91% | 96% | 0.596 | 14.0 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 132 | 42% | 76% | 87% | 0.758 | 132.8 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 331 | 77% | 90% | 95% | 0.559 | 20.3 (16.92) |

* **claimed** (n=56) PIT histogram [2, 3, 4, 4, 7, 8, 5, 7, 12, 4] — hump-shaped: the truth lands mid-distribution too often — over-dispersed, the model is hedging
* **seat_holders** (n=132) PIT histogram [2, 3, 4, 4, 7, 9, 7, 22, 32, 42] — U-shaped: the truth lands outside the distribution too often — under-dispersed, widen it; mean PIT 0.76 — the model under-predicts seats
* **all** (n=331) PIT histogram [23, 32, 28, 26, 32, 28, 30, 36, 47, 49] — approximately flat

The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ² column is the test of uniformity; the level-free dispersion table is the test of width.**

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. Five of its columns across the nine city-years carry PIT exactly 1.0 — parties the model gave zero seats in every draw, present only because they won a seat. It is a mixture of an outcome-selected set and a neutral one, and the neutral part is itself diluted by ~200 parties correctly at zero on both sides, each a free interval hit and a near-uniform PIT. Two errors pushing opposite ways: `all` tests nothing.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 27 | 0.432 | [0.378, 0.483] | 74% [48–93] | 93% [78–100] | 96% [89–100] | 70% [48–89] | 93% [78–100] | 96% [89–100] |
| ranks 4-12 | 29 | 0.749 | [0.682, 0.804] | 41% [23–63] | 90% [81–100] | 97% [90–100] | 31% [16–50] | 86% [72–100] | 93% [85–100] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|
| ranks 1-3 | 27 | 0.829 | 0.994 | -0.132 | 0.0410 vs 0.0833 |
| ranks 4-12 | 29 | 0.724 | 0.828 | +0.606 | 0.0400 vs 0.0833 |

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2016 | 6 | 67% | 100% | 100% | 0.627 |
| Johannesburg 2021 | 8 | 0% | 62% | 75% | 0.635 |
| Tshwane 2021 | 6 | 67% | 83% | 100% | 0.605 |
| Ekurhuleni 2021 | 7 | 57% | 100% | 100% | 0.642 |
| eThekwini 2021 | 7 | 86% | 86% | 100% | 0.520 |
| Cape Town 2021 | 7 | 29% | 100% | 100% | 0.564 |
| Mangaung 2021 | 5 | 80% | 100% | 100% | 0.634 |
| Nelson Mandela Bay 2021 | 5 | 60% | 100% | 100% | 0.551 |
| Buffalo City 2021 | 5 | 100% | 100% | 100% | 0.583 |


## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.91% | 45.97% | 44.92% | 45.58% | 44.09% | 123 | 121 |
| DA | 40.26% | 40.42% | 38.48% | 41.70% | 38.34% | 111 | 104 |
| EFF | 8.18% | 8.47% | 10.93% | 8.85% | 11.24% | 23 | 30 |
| IFP | 0.88% | 1.12% | 1.71% | 0.76% | 1.74% | 2 | 5 |
| AIC | 0.00% | 1.44% | 1.62% | 1.50% | 1.40% | 0 | 4 |
| ACDP | 0.19% | 0.38% | 0.31% | 0.38% | 0.28% | 1 | 1 |
| VFPLUS | 0.06% | 0.28% | 0.31% | 0.34% | 0.34% | 0 | 1 |
| ALJAMAAH | nan% | nan% | 0.31% | nan% | 0.22% | 0 | 1 |
| UDM | 0.07% | 0.24% | 0.25% | 0.28% | 0.28% | 0 | 1 |
| COPE | 0.23% | 0.45% | 0.21% | 0.28% | 0.15% | 1 | 1 |
| PA | 0.00% | 0.05% | 0.17% | 0.01% | 0.13% | 0 | 1 |
| PAC | 0.06% | 0.26% | 0.17% | 0.06% | 0.09% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 39.44% | 39.54% | 33.22% | 40.44% | 33.97% | 108 | 91 |
| DA | 32.56% | 32.81% | 25.45% | 34.07% | 26.83% | 90 | 71 |
| ASA | 4.98% | 5.50% | 18.12% | 4.61% | 13.98% | 12 | 44 |
| EFF | 13.86% | 14.43% | 10.11% | 15.45% | 11.14% | 39 | 29 |
| PA | 0.02% | 0.08% | 2.96% | 0.02% | 2.91% | 0 | 8 |
| IFP | 0.70% | 1.26% | 2.36% | 1.08% | 2.36% | 2 | 7 |
| VFPLUS | 0.42% | 0.69% | 1.33% | 0.77% | 1.35% | 1 | 4 |
| ACDP | 0.18% | 0.44% | 1.03% | 0.41% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.21% | 0.26% | 0.83% | 0.19% | 1.08% | 1 | 3 |
| AIC | 0.11% | 0.51% | 0.69% | 0.20% | 0.50% | 0 | 2 |
| AHC | 0.01% | 0.08% | 0.43% | 0.06% | 0.47% | 0 | 1 |
| GOOD | 0.05% | 0.26% | 0.33% | 0.17% | 0.40% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 37.35% | 37.30% | 34.84% | 37.72% | 34.42% | 80 | 75 |
| DA | 32.54% | 33.11% | 31.77% | 33.94% | 32.29% | 71 | 69 |
| EFF | 14.17% | 14.60% | 10.43% | 14.90% | 10.94% | 31 | 23 |
| ASA | 4.86% | 5.42% | 9.28% | 5.13% | 7.99% | 10 | 19 |
| VFPLUS | 4.01% | 4.24% | 7.79% | 4.43% | 7.96% | 9 | 17 |
| ACDP | 0.30% | 0.60% | 0.91% | 0.68% | 0.93% | 1 | 2 |
| AIC | 0.23% | 0.42% | 0.81% | 0.12% | 0.38% | 0 | 1 |
| DOP | 0.02% | 0.09% | 0.49% | 0.08% | 0.58% | 0 | 1 |
| PA | 0.00% | 0.05% | 0.48% | 0.04% | 0.52% | 0 | 1 |
| PAC | 0.00% | 0.13% | 0.21% | 0.12% | 0.18% | 0 | 1 |
| IFP | 0.00% | 0.12% | 0.21% | 0.03% | 0.09% | 0 | 1 |
| COPE | 0.00% | 0.13% | 0.19% | 0.16% | 0.20% | 0 | 1 |

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 43.42% | 43.12% | 38.34% | 43.52% | 38.03% | 98 | 86 |
| DA | 28.23% | 28.78% | 28.37% | 29.33% | 29.07% | 64 | 65 |
| EFF | 13.09% | 13.75% | 13.27% | 14.30% | 13.87% | 30 | 31 |
| ASA | 4.92% | 5.66% | 7.36% | 5.65% | 5.84% | 11 | 15 |
| VFPLUS | 1.99% | 2.28% | 3.48% | 2.29% | 3.18% | 5 | 8 |
| PA | 0.11% | 0.16% | 1.87% | 0.15% | 1.89% | 0 | 4 |
| IFP | 0.34% | 0.98% | 1.47% | 0.58% | 1.24% | 1 | 3 |
| AIC | 0.11% | 0.59% | 1.36% | 0.58% | 1.22% | 0 | 3 |
| ACDP | 0.18% | 0.54% | 0.86% | 0.57% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.04% | 0.11% | 0.45% | 0.11% | 0.44% | 0 | 1 |
| PAC | 0.00% | 0.28% | 0.43% | 0.12% | 0.31% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.00% | 1.36% | 0.36% | 1.37% | 0.78% | 0 | 1 |

**Missed entirely:** AIC, PA — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 46.17% | 46.00% | 42.51% | 45.48% | 41.77% | 102 | 96 |
| DA | 25.86% | 26.14% | 26.33% | 27.54% | 25.57% | 59 | 59 |
| EFF | 9.43% | 10.16% | 10.80% | 10.07% | 10.15% | 21 | 24 |
| IFP | 4.07% | 4.83% | 7.45% | 5.12% | 6.67% | 9 | 16 |
| ASA | 5.03% | 5.73% | 2.35% | 5.62% | 1.50% | 11 | 4 |
| AIC | 0.08% | 0.64% | 1.01% | 0.26% | 0.33% | 0 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.01% | 0.09% | 0.81% | 0.06% | 1.03% | 0 | 2 |
| ACDP | 0.30% | 0.55% | 0.76% | 0.62% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.01% | 0.06% | 0.65% | 0.05% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.07% | 0.19% | 0.61% | 0.19% | 0.51% | 0 | 1 |
| ATM | 0.22% | 0.46% | 0.57% | 0.46% | 0.66% | 1 | 1 |
| MINORITY_FRONT | 0.15% | 0.33% | 0.50% | 0.48% | 0.47% | 0 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 62.33% | 62.20% | 58.74% | 62.74% | 57.78% | 144 | 135 |
| ANC | 22.56% | 22.67% | 18.71% | 22.67% | 18.46% | 52 | 43 |
| EFF | 4.45% | 4.71% | 4.15% | 4.92% | 4.10% | 11 | 10 |
| GOOD | 2.32% | 2.71% | 3.68% | 2.66% | 3.94% | 5 | 9 |
| CAPE_COLOURED_CONGRESS | 0.00% | 0.06% | 2.83% | 0.06% | 2.78% | 0 | 7 |
| ACDP | 1.69% | 2.10% | 2.29% | 2.43% | 2.40% | 4 | 6 |
| VFPLUS | 0.46% | 0.74% | 1.54% | 0.81% | 1.63% | 1 | 4 |
| PA | 0.00% | 1.32% | 1.43% | 1.29% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.42% | 0.63% | 1.19% | 0.88% | 1.32% | 1 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.00% | 0.08% | 0.64% | 0.07% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.00% | 0.06% | 0.62% | 0.06% | 0.65% | 0 | 2 |
| UIM | 0.00% | 0.07% | 0.56% | 0.07% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 50.88% | 50.52% | 51.51% | 51.72% | 49.75% | 52 | 51 |
| DA | 24.62% | 25.72% | 25.48% | 26.10% | 25.98% | 25 | 26 |
| EFF | 11.98% | 12.72% | 11.37% | 12.61% | 11.24% | 12 | 12 |
| VFPLUS | 2.96% | 3.13% | 4.41% | 3.47% | 4.55% | 3 | 5 |
| PA | 1.19% | 1.63% | 1.78% | 1.62% | 1.83% | 1 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.13% | 0.27% | 1.26% | 0.26% | 1.61% | 0 | 2 |
| AIC | 0.33% | 1.24% | 0.84% | 0.64% | 1.70% | 0 | 1 |
| ACDP | 0.17% | 0.54% | 0.70% | 0.56% | 0.74% | 0 | 1 |
| ATM | 0.25% | 0.46% | 0.61% | 0.39% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.38% | nan% | 0.38% | 0 | 0 |
| COPE | 0.00% | 0.25% | 0.30% | 0.10% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.09% | 0.22% | 0.21% | 0.02% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 45.52% | 45.46% | 40.04% | 46.36% | 39.80% | 55 | 48 |
| ANC | 39.24% | 39.11% | 39.60% | 38.69% | 39.26% | 47 | 48 |
| EFF | 7.20% | 7.81% | 6.40% | 8.22% | 6.40% | 9 | 8 |
| NORTHERN_ALLIANCE | 0.04% | 0.16% | 2.09% | 0.17% | 2.18% | 0 | 3 |
| ACDP | 0.54% | 0.79% | 1.68% | 0.86% | 1.64% | 1 | 2 |
| VFPLUS | 0.75% | 0.99% | 1.64% | 1.05% | 1.51% | 1 | 2 |
| DOP | 0.03% | 0.13% | 1.38% | 0.12% | 1.47% | 0 | 2 |
| PA | 0.00% | 1.36% | 1.32% | 1.43% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.04% | 0.16% | 1.11% | 0.17% | 1.05% | 0 | 1 |
| UDM | 0.18% | 0.72% | 1.07% | 0.80% | 1.01% | 0 | 1 |
| AIC | 0.12% | 0.65% | 0.68% | 0.09% | 0.38% | 0 | 1 |
| PAC | 0.00% | 0.23% | 0.51% | 0.07% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.10% | 58.02% | 60.51% | 59.57% | 58.35% | 60 | 61 |
| DA | 20.26% | 21.32% | 19.49% | 22.67% | 19.55% | 21 | 20 |
| EFF | 10.90% | 12.21% | 12.37% | 12.31% | 11.76% | 11 | 13 |
| UDM | 0.30% | 0.73% | 1.10% | 0.36% | 0.82% | 0 | 1 |
| PAC | 0.04% | 0.73% | 1.05% | 0.55% | 0.83% | 0 | 1 |
| AIC | 0.33% | 1.30% | 0.97% | 0.33% | 0.45% | 0 | 1 |
| ATM | 0.59% | 0.81% | 0.89% | 0.56% | 0.93% | 1 | 1 |
| ACDP | 0.39% | 0.53% | 0.57% | 0.58% | 0.55% | 1 | 1 |
| VFPLUS | 0.23% | 0.38% | 0.52% | 0.34% | 0.51% | 0 | 1 |
| PA | 0.05% | 0.11% | 0.42% | 0.01% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.05% | 0.10% | 0.34% | 0.02% | 0.10% | 0 | 0 |
| COPE | 0.00% | 0.14% | 0.27% | 0.01% | 0.05% | 0 | 0 |