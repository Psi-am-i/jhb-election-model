# Historical performance — votes and seats, predicted against actual

16 city-years. Shares are citywide percentages; the model column is the median over draws.

## Headline

| city-year | council | list MAE | ward MAE | seat err (median) | medians sum to | seat err (coherent) | CRPS | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | 270 | 0.84pp | 1.30pp | 23 | 259 | 22 | 19.7 | 92 | 26 | 91 |
| Johannesburg 2021 | 270 | 6.19pp | 4.97pp | 95 | 249 | 90 | 70.4 | 134 | 126 | 125 |
| Tshwane 2016 | 214 | 1.89pp | 1.25pp | 16 | 206 | 18 | 13.4 | 70 | 10 | 70 |
| Tshwane 2021 | 214 | 1.69pp | 1.68pp | 33 | 199 | 36 | 26.5 | 80 | 60 | 77 |
| Ekurhuleni 2016 | 224 | 1.63pp | 2.07pp | 20 | 214 | 18 | 16.7 | 80 | 22 | 76 |
| Ekurhuleni 2021 | 224 | 1.55pp | 1.27pp | 30 | 208 | 24 | 25.2 | 72 | 48 | 66 |
| eThekwini 2016 | 219 | 1.62pp | 2.73pp | 29 | 212 | 28 | 21.6 | 64 | 50 | 59 |
| eThekwini 2021 | 222 | 0.71pp | 1.01pp | 40 | 200 | 38 | 33.5 | 82 | 36 | 76 |
| Cape Town 2016 | 231 | 0.43pp | 0.89pp | 13 | 222 | 12 | 12.3 | 46 | 30 | 49 |
| Cape Town 2021 | 231 | 1.73pp | 1.96pp | 40 | 217 | 34 | 31.5 | 68 | 38 | 63 |
| Mangaung 2016 | 100 | 0.82pp | 1.44pp | 7 | 95 | 8 | 7.3 | 24 | 12 | 22 |
| Mangaung 2021 | 101 | 1.87pp | 0.92pp | 9 | 92 | 10 | 9.3 | 24 | 8 | 20 |
| Nelson Mandela Bay 2016 | 120 | 0.74pp | 0.63pp | 7 | 115 | 8 | 7.9 | 38 | 16 | 38 |
| Nelson Mandela Bay 2021 | 120 | 3.06pp | 3.22pp | 23 | 111 | 18 | 16.7 | 28 | 22 | 27 |
| Buffalo City 2016 | 100 | 1.20pp | 2.51pp | 11 | 93 | 10 | 9.5 | 28 | 14 | 25 |
| Buffalo City 2021 | 100 | 3.68pp | 2.42pp | 11 | 93 | 12 | 8.1 | 14 | 12 | 15 |

### The margin is not evenly spread

| | city-years | seat err (coherent) | uniform-swing | margin | CRPS | uniform-swing CRPS | margin |
|---|---|---|---|---|---|---|---|
| Gauteng (JHB, TSH, EKU) | 6 | 208 | 292 | 29% | 171.9 | 292.0 | 41% |
| everywhere else | 10 | 178 | 238 | 25% | 157.6 | 238.0 | 34% |

**The headline margin is a Gauteng result.** Outside Gauteng the model is closer to parity with uniform swing on seats and loses at Mangaung. Quote the split, not the pool.

**Sign count against uniform swing: 12 wins, 3 losses, 1 ties across 16 city-years** — 2016: 7W 1L 0T; 2021: 5W 2L 1T. The sign REPLICATES across cycles, which is what the amended bar's Key 1 asks of any candidate and is the strongest claim this panel supports. Metros inside one cycle share a national swing, so 16 city-years is 2 effective clusters, not 16 — never quote a p-value off the pooled count.

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber and is the only one comparable to the baselines, which allocate per draw and sum exactly. Lower is better throughout.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | -0.21pp | 3.40pp | **-0.48pp** | 1.63pp | +0.69pp | 1.39pp | 0.00pp (0) | 15 |
| Johannesburg 2021 | +0.08pp | 24.48pp | **-2.05pp** | 8.93pp | +0.29pp | 1.51pp | 1.68pp (3) | 58 |
| Tshwane 2016 | -2.74pp | 5.72pp | **+0.89pp** | 1.23pp | +0.41pp | 0.85pp | 1.43pp (2) | 7 |
| Tshwane 2021 | +5.66pp | 5.66pp | **-7.57pp** | 7.70pp | +0.27pp | 1.65pp | 1.63pp (5) | 44 |
| Ekurhuleni 2016 | -0.12pp | 5.06pp | **+0.11pp** | 1.47pp | +0.01pp | 0.83pp | 0.00pp (0) | 12 |
| Ekurhuleni 2021 | +3.69pp | 3.85pp | **-4.35pp** | 6.23pp | +0.60pp | 1.37pp | 0.06pp (1) | 38 |
| eThekwini 2016 | -0.80pp | 4.30pp | **+1.30pp** | 5.11pp | -0.50pp | 1.29pp | 0.00pp (0) | 18 |
| eThekwini 2021 | +0.52pp | 1.57pp | **-0.74pp** | 8.40pp | +0.07pp | 4.35pp | 0.16pp (3) | 31 |
| Cape Town 2016 | +0.22pp | 1.55pp | **+0.38pp** | 2.45pp | -0.60pp | 1.24pp | 0.00pp (0) | 12 |
| Cape Town 2021 | +5.80pp | 5.80pp | **-5.67pp** | 5.93pp | -0.28pp | 2.03pp | 0.15pp (3) | 38 |
| Mangaung 2016 | +1.65pp | 2.71pp | **-1.77pp** | 4.48pp | +0.11pp | 0.48pp | 0.00pp (0) | 6 |
| Mangaung 2021 | -1.76pp | 4.28pp | **-0.91pp** | 3.35pp | +1.28pp | 1.97pp | 1.39pp (1) | 12 |
| Nelson Mandela Bay 2016 | -0.57pp | 1.77pp | **+0.28pp** | 3.04pp | +0.29pp | 0.79pp | 0.00pp (0) | 7 |
| Nelson Mandela Bay 2021 | +4.32pp | 8.61pp | **-5.00pp** | 5.85pp | +0.68pp | 1.32pp | 0.00pp (0) | 15 |
| Buffalo City 2016 | -0.63pp | 5.42pp | **-0.76pp** | 5.24pp | +0.00pp | 0.00pp | 1.40pp (1) | 8 |
| Buffalo City 2021 | -2.83pp | 8.34pp | **+0.22pp** | 1.93pp | +1.03pp | 1.32pp | 1.58pp (2) | 6 |

**Totals across 16 city-years:** ranks 1-3 +12.29pp signed / 92.52pp absolute, ranks 4-12 -26.11pp / 73.00pp, ranks 13+ +4.35pp / 22.37pp.

**Phantom mass: 9.47pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -9.47pp rather than to zero.


## Ward winners — the geography key

**`seat_abs_err_coherent` cannot see geography and this can.** `solve_and_predict` forces every party's citywide share onto the share the draw drew, and both ballots are `weight @ pred` against those same targets, so `dev`, `gamma`, pool composition and the whole VD layer reach the seat score ONLY through an overhang trigger. Any change to those is judged here, or it is judged by an instrument that is blind to it. Hit rate is the modal call; Brier (multi-category, 0 to 2) is the proper score and is what a change in CONFIDENCE moves. **Read the model against the baselines in its own row** — safe wards are called correctly by anything at all.

| city-year | wards | model called | hit rate | Brier MC | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|
| Johannesburg 2016 | 135 | 134 | 99.3% | 0.018 | 94.8% | 97.8% | 94.8% |
| Johannesburg 2021 | 135 | 127 | 94.1% | 0.092 | 93.3% | 93.3% | 93.3% |
| Tshwane 2016 | 107 | 104 | 97.2% | 0.042 | 98.1% | 98.1% | 98.1% |
| Tshwane 2021 | 107 | 104 | 97.2% | 0.036 | 98.1% | 98.1% | 98.1% |
| Ekurhuleni 2016 | 112 | 111 | 99.1% | 0.028 | 97.3% | 99.1% | 97.3% |
| Ekurhuleni 2021 | 112 | 107 | 95.5% | 0.071 | 95.5% | 94.6% | 95.5% |
| eThekwini 2016 | 110 (only 109 matched) | 98 | 89.1% | 0.203 | 82.7% | 85.5% | 83.6% |
| eThekwini 2021 | 111 | 110 | 99.1% | 0.035 | 96.4% | 98.2% | 96.4% |
| Cape Town 2016 | 116 | 116 | 100.0% | 0.005 | 100.0% | 100.0% | 100.0% |
| Cape Town 2021 | 116 | 115 | 99.1% | 0.014 | 99.1% | 99.1% | 99.1% |
| Mangaung 2016 | 50 (only 49 matched) | 48 | 96.0% | 0.035 | 96.0% | 98.0% | 96.0% |
| Mangaung 2021 | 51 | 50 | 98.0% | 0.040 | 98.0% | 96.1% | 98.0% |
| Nelson Mandela Bay 2016 | 60 | 57 | 95.0% | 0.071 | 96.7% | 96.7% | 96.7% |
| Nelson Mandela Bay 2021 | 60 | 57 | 95.0% | 0.056 | 95.0% | 95.0% | 95.0% |
| Buffalo City 2016 | 50 | 48 | 96.0% | 0.091 | 100.0% | 96.0% | 100.0% |
| Buffalo City 2021 | 50 | 48 | 96.0% | 0.073 | 96.0% | 96.0% | 96.0% |

**Pooled over 16 city-years: 1434/1482 = 96.8% of ward contests called correctly, against last-lge 95.8%, uniform-swing 96.4%, prior-lge-noise 95.9%. A margin over the baselines that is smaller than the seat margin is the model's geography adding less than its citywide machinery, which is a statement the seat columns cannot make.

## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |
|---|---|---|---|---|---|---|
| reference (INPUT-selected — fixed; the only one to compare on) | 376 | 82% | 93% | 94% | 0.567 | 47.1 (16.92) |
| claimed by the model (forecast-selected — neutral for ONE model) | 109 | 83% | 94% | 96% | 0.559 | 43.6 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 199 | 63% | 85% | 87% | 0.699 | 107.9 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 430 | 83% | 93% | 94% | 0.539 | 13.9 (16.92) |

* **reference** (n=376) PIT histogram [29, 20, 23, 41, 32, 40, 41, 69, 33, 48] — approximately flat
* **claimed** (n=109) PIT histogram [5, 2, 6, 10, 16, 23, 18, 18, 7, 4] — hump-shaped: the truth lands mid-distribution too often — over-dispersed, the model is hedging
* **seat_holders** (n=199) PIT histogram [3, 2, 6, 9, 16, 24, 28, 44, 24, 43] — approximately flat; mean PIT 0.70 — the model under-predicts seats
* **all** (n=430) PIT histogram [35, 35, 35, 37, 43, 46, 53, 58, 40, 48] — approximately flat

The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ² column is the test of uniformity; the level-free dispersion table is the test of width.**

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. Five of its columns across the nine city-years carry PIT exactly 1.0 — parties the model gave zero seats in every draw, present only because they won a seat. It is a mixture of an outcome-selected set and a neutral one, and the neutral part is itself diluted by ~200 parties correctly at zero on both sides, each a free interval hit and a near-uniform PIT. Two errors pushing opposite ways: `all` tests nothing.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 48 | 0.510 | [0.473, 0.542] | 88% [75–98] | 96% [88–100] | 98% [94–100] | 85% [73–96] | 96% [88–100] | 98% [94–100] |
| ranks 4-12 | 57 | 0.613 | [0.536, 0.684] | 81% [68–93] | 91% [87–96] | 95% [90–100] | 61% [48–76] | 91% [87–96] | 93% [88–98] |
| ranks 13+ | 4 | 0.384 | [0.080, 0.687] | 50% [0–100] | 100% [100–100] | 100% [100–100] | 50% [0–100] | 50% [0–100] | 100% [100–100] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|
| ranks 1-3 | 48 | 0.818 | 0.725 | +0.032 | 0.0309 vs 0.0833 |
| ranks 4-12 | 57 | 0.820 | 0.857 | +0.168 | 0.0478 vs 0.0833 |
| ranks 13+ | 4 | 1.100 | 0.620 | -0.520 | 0.1234 vs 0.0833 |

#### The same question on the FIXED population — and it disagrees

**The `n` here is the number of columns the width figure was actually computed on** — columns with a defined `z`. A column whose draws are all identical has no scale, so it carries a PIT and no `z`; the pooled tables above count PIT values and their `n` is larger.

| band | `claimed` n(z) | `claimed` SD of z | `reference` n(z) | `reference` SD of z | `reference` mean z | `reference` probit-SD |
|---|---|---|---|---|---|---|
| ranks 1-3 | 48 | 0.725 | 48 | 0.725 | +0.032 | **0.818** |
| ranks 4-12 | 57 | 0.857 | 120 | 1.796 | +0.525 | **1.305** |
| ranks 13+ | 4 | 0.620 | 135 | 0.415 | -0.121 | **1.203** |

**Read the last column, not the `SD of z` column, on ranks 13+.** `sd(z)` is exact under a level shift and **meaningless on a near-degenerate discrete column**: where the forecast is roughly Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly, a function of the forecast probability with no room to spread. On the 96 ranks-13+ columns whose truth is zero, observed `z` correlates with that expression at **+0.93**. probit-SD comes from the randomised PIT, which is uniform under calibration whatever the support, and is the one to read there — at the cost of being attenuated by a level shift, so it is a LOWER BOUND wherever `mean z` is far from zero. Neither statistic is right everywhere; the pair is. MODEL-LOG §1.58.

**Ranks 1-3 are the same columns in both populations** — the top three are always claimed — so that row is a consistency check and the two `SD of z` numbers should agree exactly. It is also the band that is genuinely too WIDE (probit-SD 0.682, with `mean z` ≈ 0 so nothing is attenuating it) and the band that responds to `dirichlet_scale`.

**Ranks 4-12 cannot be described by one width, and that is the finding.** On the same columns `sd(z)` says far too narrow, `IQR-sd` (0.595) says too wide, and probit-SD says about right — because the error distribution is a narrow shifted bulk with two enormous outliers, Cape Town's Cape Coloured Congress at z = +12.1 and Johannesburg's PA at +9.3, both of which `claimed` excludes by construction. A distribution that reads too wide, about right and far too narrow depending which moment you take is mis-SHAPED, not mis-scaled, and no scalar fixes it. §1.56, §1.58.

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2016 | 7 | 86% | 100% | 100% | 0.525 |
| Johannesburg 2021 | 9 | 33% | 67% | 78% | 0.638 |
| Tshwane 2016 | 6 | 83% | 100% | 100% | 0.437 |
| Tshwane 2021 | 7 | 71% | 86% | 100% | 0.604 |
| Ekurhuleni 2016 | 6 | 100% | 100% | 100% | 0.519 |
| Ekurhuleni 2021 | 9 | 89% | 89% | 89% | 0.685 |
| eThekwini 2016 | 8 | 62% | 88% | 88% | 0.476 |
| eThekwini 2021 | 9 | 78% | 89% | 100% | 0.514 |
| Cape Town 2016 | 6 | 100% | 100% | 100% | 0.602 |
| Cape Town 2021 | 7 | 71% | 100% | 100% | 0.541 |
| Mangaung 2016 | 4 | 100% | 100% | 100% | 0.519 |
| Mangaung 2021 | 6 | 100% | 100% | 100% | 0.624 |
| Nelson Mandela Bay 2016 | 7 | 100% | 100% | 100% | 0.470 |
| Nelson Mandela Bay 2021 | 6 | 83% | 100% | 100% | 0.563 |
| Buffalo City 2016 | 6 | 100% | 100% | 100% | 0.591 |
| Buffalo City 2021 | 6 | 100% | 100% | 100% | 0.592 |


## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 44.84% | 44.89% | 44.92% | 44.18% | 44.09% | 120 | 121 |
| DA | 39.90% | 40.07% | 38.48% | 41.05% | 38.34% | 109 | 104 |
| EFF | 8.92% | 9.16% | 10.93% | 9.50% | 11.24% | 25 | 30 |
| IFP | 1.03% | 1.28% | 1.71% | 1.17% | 1.74% | 3 | 5 |
| AIC | 0.00% | 1.40% | 1.62% | 1.45% | 1.40% | 0 | 4 |
| ACDP | 0.28% | 0.48% | 0.31% | 0.51% | 0.28% | 1 | 1 |
| VFPLUS | 0.15% | 0.40% | 0.31% | 0.48% | 0.34% | 0 | 1 |
| ALJAMAAH | nan% | nan% | 0.31% | nan% | 0.22% | 0 | 1 |
| UDM | 0.14% | 0.33% | 0.25% | 0.37% | 0.28% | 0 | 1 |
| COPE | 0.06% | 0.23% | 0.21% | 0.15% | 0.15% | 0 | 1 |
| PA | 0.01% | 0.07% | 0.17% | 0.08% | 0.13% | 0 | 1 |
| PAC | 0.17% | 0.38% | 0.17% | 0.09% | 0.09% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 38.38% | 38.24% | 33.22% | 38.35% | 33.97% | 104 | 91 |
| DA | 32.45% | 32.72% | 25.45% | 33.32% | 26.83% | 88 | 71 |
| ASA | 5.35% | 5.92% | 18.12% | 4.90% | 13.98% | 13 | 44 |
| EFF | 12.89% | 13.48% | 10.11% | 14.17% | 11.14% | 36 | 29 |
| PA | 0.03% | 0.09% | 2.96% | 0.17% | 2.91% | 0 | 8 |
| IFP | 0.81% | 1.45% | 2.36% | 1.88% | 2.36% | 3 | 7 |
| VFPLUS | 0.63% | 0.86% | 1.33% | 0.95% | 1.35% | 2 | 4 |
| ACDP | 0.27% | 0.63% | 1.03% | 0.64% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.26% | 0.31% | 0.83% | 0.29% | 1.08% | 1 | 3 |
| AIC | 0.24% | 0.76% | 0.69% | 0.38% | 0.50% | 1 | 2 |
| AHC | 0.02% | 0.11% | 0.43% | 0.09% | 0.47% | 0 | 1 |
| GOOD | 0.09% | 0.31% | 0.33% | 0.25% | 0.40% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 40.32% | 40.67% | 43.10% | 41.24% | 43.20% | 87 | 93 |
| ANC | 43.19% | 42.97% | 41.48% | 41.66% | 41.02% | 91 | 89 |
| EFF | 9.57% | 9.84% | 11.64% | 10.55% | 11.62% | 21 | 25 |
| VFPLUS | 2.15% | 2.32% | 1.97% | 2.57% | 2.02% | 5 | 4 |
| ACDP | 0.50% | 0.73% | 0.47% | 0.85% | 0.52% | 1 | 1 |
| APC | 0.17% | 0.43% | 0.24% | 0.07% | 0.05% | 0 | 0 |
| COPE | 0.03% | 0.18% | 0.22% | 0.19% | 0.27% | 0 | 1 |
| PAC | 0.10% | 0.33% | 0.14% | 0.36% | 0.20% | 0 | 1 |
| UDM | 0.02% | 0.19% | 0.13% | 0.24% | 0.10% | 0 | 0 |
| IFP | 0.00% | 0.11% | 0.10% | 0.02% | 0.02% | 0 | 0 |
| AFRICAN_MANDATE_CONGRESS | nan% | nan% | 0.09% | nan% | 0.06% | 0 | 0 |
| PA | 0.01% | 0.05% | 0.09% | 0.05% | 0.05% | 0 | 0 |

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 35.99% | 35.75% | 34.84% | 35.89% | 34.42% | 77 | 75 |
| DA | 33.01% | 33.30% | 31.77% | 33.56% | 32.29% | 71 | 69 |
| EFF | 13.03% | 13.65% | 10.43% | 13.71% | 10.94% | 28 | 23 |
| ASA | 5.38% | 5.92% | 9.28% | 5.51% | 7.99% | 11 | 19 |
| VFPLUS | 4.56% | 4.83% | 7.79% | 4.97% | 7.96% | 10 | 17 |
| ACDP | 0.36% | 0.70% | 0.91% | 0.76% | 0.93% | 1 | 2 |
| AIC | 0.41% | 0.66% | 0.81% | 0.62% | 0.38% | 1 | 1 |
| DOP | 0.03% | 0.14% | 0.49% | 0.13% | 0.58% | 0 | 1 |
| PA | 0.01% | 0.06% | 0.48% | 0.11% | 0.52% | 0 | 1 |
| PAC | 0.00% | 0.27% | 0.21% | 0.27% | 0.18% | 0 | 1 |
| IFP | 0.00% | 0.11% | 0.21% | 0.17% | 0.09% | 0 | 1 |
| COPE | 0.00% | 0.10% | 0.19% | 0.13% | 0.20% | 0 | 1 |

## Ekurhuleni 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 47.89% | 47.54% | 48.84% | 46.20% | 48.44% | 106 | 109 |
| DA | 36.31% | 36.59% | 34.13% | 36.89% | 34.17% | 82 | 77 |
| EFF | 9.42% | 9.80% | 11.10% | 10.96% | 11.35% | 22 | 25 |
| AIC | 0.00% | 1.42% | 1.65% | 1.58% | 1.63% | 0 | 4 |
| IFP | 0.57% | 0.91% | 1.04% | 1.12% | 0.99% | 1 | 2 |
| VFPLUS | 0.71% | 0.95% | 0.90% | 1.11% | 0.89% | 2 | 2 |
| ACDP | 0.41% | 0.65% | 0.42% | 0.79% | 0.43% | 1 | 1 |
| PAC | 0.21% | 0.52% | 0.42% | 0.24% | 0.43% | 0 | 1 |
| COPE | 0.02% | 0.20% | 0.28% | 0.21% | 0.25% | 0 | 1 |
| PA | 0.00% | 0.03% | 0.28% | 0.04% | 0.25% | 0 | 1 |
| APC | 0.24% | 0.57% | 0.27% | 0.14% | 0.06% | 0 | 0 |
| UDM | 0.09% | 0.34% | 0.23% | 0.18% | 0.16% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 41.63% | 41.20% | 38.34% | 40.97% | 38.03% | 93 | 86 |
| DA | 28.63% | 29.28% | 28.37% | 29.12% | 29.07% | 64 | 65 |
| EFF | 12.73% | 13.19% | 13.27% | 13.40% | 13.87% | 29 | 31 |
| ASA | 5.31% | 5.88% | 7.36% | 5.78% | 5.84% | 12 | 15 |
| VFPLUS | 2.51% | 2.84% | 3.48% | 2.79% | 3.18% | 6 | 8 |
| PA | 0.15% | 0.20% | 1.87% | 0.40% | 1.89% | 1 | 4 |
| IFP | 0.39% | 1.07% | 1.47% | 0.94% | 1.24% | 1 | 3 |
| AIC | 0.27% | 0.90% | 1.36% | 1.01% | 1.22% | 1 | 3 |
| ACDP | 0.26% | 0.65% | 0.86% | 0.67% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.06% | 0.14% | 0.45% | 0.13% | 0.44% | 0 | 1 |
| PAC | 0.01% | 0.33% | 0.43% | 0.37% | 0.31% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.00% | 1.30% | 0.36% | 1.28% | 0.78% | 0 | 1 |

## eThekwini 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.59% | 57.34% | 59.11% | 52.84% | 52.95% | 121 | 126 |
| DA | 29.05% | 29.29% | 27.54% | 33.58% | 26.30% | 68 | 61 |
| IFP | 3.36% | 3.50% | 4.28% | 3.49% | 4.12% | 7 | 10 |
| EFF | 2.52% | 2.74% | 3.63% | 2.86% | 3.26% | 6 | 8 |
| AIC | 0.00% | 1.38% | 1.51% | 1.44% | 1.23% | 0 | 3 |
| ACDP | 0.52% | 0.67% | 0.54% | 0.75% | 0.55% | 1 | 1 |
| MINORITY_FRONT | 3.06% | 3.28% | 0.46% | 3.58% | 0.60% | 7 | 1 |
| DEMOCRATIC_LIBERAL_CONGRESS | nan% | nan% | 0.43% | nan% | 0.60% | 0 | 1 |
| TRULY_ALLIANCE | 0.34% | 0.51% | 0.42% | 0.65% | 0.40% | 1 | 1 |
| MINORITIES_OF_SOUTH_AFRICA | nan% | nan% | 0.27% | nan% | 0.35% | 0 | 1 |
| APC | 0.32% | 0.43% | 0.26% | 0.24% | 0.15% | 1 | 1 |
| ALJAMAAH | nan% | nan% | 0.18% | nan% | 0.20% | 0 | 1 |

**Missed entirely:** AIC — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 42.94% | 42.90% | 42.51% | 41.70% | 41.77% | 94 | 96 |
| DA | 26.64% | 26.98% | 26.33% | 27.92% | 25.57% | 60 | 59 |
| EFF | 9.60% | 10.28% | 10.80% | 10.19% | 10.15% | 21 | 24 |
| IFP | 3.81% | 4.68% | 7.45% | 5.15% | 6.67% | 9 | 16 |
| ASA | 5.37% | 6.00% | 2.35% | 5.83% | 1.50% | 12 | 4 |
| AIC | 0.23% | 0.89% | 1.01% | 0.38% | 0.33% | 0 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.02% | 0.10% | 0.81% | 0.10% | 1.03% | 0 | 2 |
| ACDP | 0.35% | 0.66% | 0.76% | 0.73% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.01% | 0.09% | 0.65% | 0.08% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.10% | 0.30% | 0.61% | 0.29% | 0.51% | 0 | 1 |
| ATM | 0.29% | 0.58% | 0.57% | 0.56% | 0.66% | 1 | 1 |
| MINORITY_FRONT | 0.48% | 0.67% | 0.50% | 0.95% | 0.47% | 1 | 1 |

## Cape Town 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 67.17% | 67.19% | 66.75% | 67.66% | 66.46% | 156 | 154 |
| ANC | 24.90% | 24.98% | 24.52% | 23.94% | 24.20% | 56 | 57 |
| EFF | 2.25% | 2.45% | 3.12% | 2.69% | 3.22% | 6 | 7 |
| ACDP | 0.70% | 0.95% | 1.13% | 1.18% | 1.29% | 2 | 3 |
| AIC | 0.27% | 0.44% | 0.76% | 0.48% | 0.42% | 1 | 1 |
| ALJAMAAH | 0.23% | 0.48% | 0.55% | 0.57% | 0.76% | 1 | 2 |
| VFPLUS | 0.17% | 0.30% | 0.39% | 0.35% | 0.43% | 0 | 1 |
| UDM | 0.24% | 0.39% | 0.33% | 0.20% | 0.20% | 0 | 1 |
| DEMOCRATIC_INDEPENDENT_PARTY | 0.00% | 1.56% | 0.28% | 1.70% | 0.32% | 0 | 1 |
| CAPE_MUSLIM_CONGRESS | nan% | nan% | 0.27% | nan% | 0.25% | 0 | 1 |
| COPE | 0.05% | 0.15% | 0.24% | 0.15% | 0.25% | 0 | 1 |
| PAC | 0.15% | 0.31% | 0.24% | 0.40% | 0.27% | 0 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 60.67% | 60.37% | 58.74% | 59.59% | 57.78% | 139 | 135 |
| ANC | 21.88% | 22.01% | 18.71% | 22.29% | 18.46% | 51 | 43 |
| EFF | 4.59% | 5.02% | 4.15% | 5.13% | 4.10% | 11 | 10 |
| GOOD | 2.86% | 3.18% | 3.68% | 3.06% | 3.94% | 7 | 9 |
| CAPE_COLOURED_CONGRESS | 0.00% | 0.07% | 2.83% | 0.07% | 2.78% | 0 | 7 |
| ACDP | 2.08% | 2.42% | 2.29% | 2.88% | 2.40% | 5 | 6 |
| VFPLUS | 0.62% | 0.94% | 1.54% | 1.01% | 1.63% | 2 | 4 |
| PA | 0.00% | 1.43% | 1.43% | 1.38% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.64% | 0.82% | 1.19% | 1.12% | 1.32% | 2 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.00% | 0.07% | 0.64% | 0.07% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.00% | 0.09% | 0.62% | 0.09% | 0.65% | 0 | 2 |
| UIM | 0.00% | 0.09% | 0.56% | 0.09% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.66% | 57.18% | 56.77% | 56.87% | 56.28% | 58 | 58 |
| DA | 27.49% | 27.97% | 26.20% | 28.68% | 25.73% | 28 | 27 |
| EFF | 7.80% | 8.31% | 8.84% | 7.47% | 8.48% | 7 | 9 |
| AIC | 0.00% | 1.44% | 2.74% | 1.30% | 0.64% | 0 | 2 |
| VFPLUS | 2.20% | 2.39% | 1.85% | 2.77% | 1.99% | 2 | 2 |
| AGENCY_FOR_NEW_AGENDA | nan% | nan% | 1.57% | nan% | 0.21% | 0 | 1 |
| COPE | 0.30% | 0.77% | 0.56% | 0.83% | 0.63% | 0 | 1 |
| ACDP | 0.31% | 0.61% | 0.39% | 0.95% | 0.39% | 0 | 0 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.09% | 0.30% | 0.28% | 0.27% | 0.11% | 0 | 0 |
| APC | 0.19% | 0.62% | 0.25% | 0.57% | 0.17% | 0 | 0 |
| AZANIAN_ALLIANCE_CONGRESS | nan% | nan% | 0.13% | nan% | 0.06% | 0 | 0 |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | nan% | nan% | 0.12% | nan% | 0.09% | 0 | 0 |

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 48.73% | 48.49% | 51.51% | 48.15% | 49.75% | 49 | 51 |
| DA | 25.43% | 26.29% | 25.48% | 25.85% | 25.98% | 25 | 26 |
| EFF | 11.06% | 11.82% | 11.37% | 11.36% | 11.24% | 11 | 12 |
| VFPLUS | 3.38% | 3.65% | 4.41% | 3.91% | 4.55% | 4 | 5 |
| PA | 1.52% | 2.04% | 1.78% | 1.96% | 1.83% | 2 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.15% | 0.37% | 1.26% | 0.36% | 1.61% | 0 | 2 |
| AIC | 0.61% | 1.64% | 0.84% | 3.00% | 1.70% | 1 | 1 |
| ACDP | 0.22% | 0.71% | 0.70% | 0.74% | 0.74% | 0 | 1 |
| ATM | 0.37% | 0.66% | 0.61% | 0.63% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.38% | nan% | 0.38% | 0 | 0 |
| COPE | 0.00% | 0.21% | 0.30% | 0.09% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.11% | 0.29% | 0.21% | 0.28% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 47.08% | 47.26% | 46.66% | 47.72% | 46.75% | 57 | 57 |
| ANC | 40.66% | 40.46% | 41.50% | 40.05% | 40.34% | 48 | 50 |
| EFF | 4.51% | 4.90% | 5.03% | 5.10% | 5.21% | 6 | 6 |
| UDM | 0.96% | 1.28% | 1.83% | 1.26% | 2.00% | 1 | 2 |
| AIC | 1.06% | 1.32% | 1.61% | 1.38% | 0.28% | 1 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.00% | 1.28% | 0.80% | 1.33% | 1.09% | 0 | 1 |
| COPE | 0.55% | 0.84% | 0.70% | 0.86% | 0.77% | 1 | 1 |
| ACDP | 0.34% | 0.51% | 0.35% | 0.58% | 0.37% | 0 | 1 |
| PA | nan% | nan% | 0.29% | nan% | 0.24% | 0 | 1 |
| ALTERNATIVE_DEMOCRATS | nan% | nan% | 0.25% | nan% | 0.08% | 0 | 0 |
| VFPLUS | 0.43% | 0.62% | 0.25% | 0.78% | 0.26% | 1 | 0 |
| PAC | 0.43% | 0.73% | 0.23% | 0.24% | 0.12% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 45.09% | 45.10% | 40.04% | 45.03% | 39.80% | 54 | 48 |
| ANC | 37.67% | 37.46% | 39.60% | 36.92% | 39.26% | 45 | 48 |
| EFF | 7.22% | 7.81% | 6.40% | 8.19% | 6.40% | 9 | 8 |
| NORTHERN_ALLIANCE | 0.05% | 0.17% | 2.09% | 0.17% | 2.18% | 0 | 3 |
| ACDP | 0.74% | 1.02% | 1.68% | 1.08% | 1.64% | 1 | 2 |
| VFPLUS | 1.07% | 1.31% | 1.64% | 1.35% | 1.51% | 1 | 2 |
| DOP | 0.04% | 0.16% | 1.38% | 0.17% | 1.47% | 0 | 2 |
| PA | 0.00% | 1.51% | 1.32% | 1.55% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.05% | 0.18% | 1.11% | 0.18% | 1.05% | 0 | 1 |
| UDM | 0.24% | 0.83% | 1.07% | 0.98% | 1.01% | 0 | 1 |
| AIC | 0.29% | 0.92% | 0.68% | 0.46% | 0.38% | 0 | 1 |
| PAC | 0.03% | 0.39% | 0.51% | 0.46% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.98% | 59.30% | 59.86% | 59.77% | 57.63% | 61 | 60 |
| DA | 24.55% | 25.85% | 23.45% | 26.48% | 23.35% | 25 | 24 |
| EFF | 4.64% | 5.74% | 8.21% | 4.94% | 7.74% | 4 | 8 |
| AIC | 0.93% | 2.09% | 3.89% | 3.96% | 2.95% | 1 | 4 |
| UDM | 1.59% | 2.67% | 1.29% | 0.81% | 0.45% | 1 | 1 |
| COPE | 0.01% | 0.47% | 0.99% | 0.48% | 0.72% | 0 | 1 |
| PAC | 0.60% | 1.66% | 0.98% | 1.46% | 0.82% | 1 | 1 |
| ACDP | 0.20% | 0.64% | 0.55% | 0.74% | 0.56% | 0 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | nan% | nan% | 0.32% | nan% | 0.27% | 0 | 0 |
| PAN_AFRICANIST_MOVEMENT | nan% | nan% | 0.20% | nan% | 0.04% | 0 | 0 |
| PEOPLES_ALLIANCE | nan% | nan% | 0.16% | nan% | 0.02% | 0 | 0 |
| UNITED_CONGRESS | 0.07% | 0.18% | 0.10% | 0.16% | 0.09% | 0 | 0 |

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 56.26% | 55.44% | 60.51% | 55.82% | 58.35% | 57 | 61 |
| DA | 21.16% | 22.25% | 19.49% | 23.17% | 19.55% | 22 | 20 |
| EFF | 10.89% | 11.85% | 12.37% | 11.69% | 11.76% | 11 | 13 |
| UDM | 0.27% | 0.83% | 1.10% | 1.69% | 0.82% | 1 | 1 |
| PAC | 0.23% | 1.08% | 1.05% | 1.11% | 0.83% | 0 | 1 |
| AIC | 0.60% | 1.66% | 0.97% | 0.41% | 0.45% | 0 | 1 |
| ATM | 0.77% | 1.08% | 0.89% | 0.95% | 0.93% | 1 | 1 |
| ACDP | 0.47% | 0.69% | 0.57% | 0.74% | 0.55% | 1 | 1 |
| VFPLUS | 0.32% | 0.56% | 0.52% | 0.49% | 0.51% | 0 | 1 |
| PA | 0.06% | 0.15% | 0.42% | 0.13% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.06% | 0.16% | 0.34% | 0.14% | 0.10% | 0 | 0 |
| COPE | 0.00% | 0.14% | 0.27% | 0.01% | 0.05% | 0 | 0 |