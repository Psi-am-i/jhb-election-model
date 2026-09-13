# Historical performance — votes and seats, predicted against actual

24 city-years. Shares are citywide percentages; the model column is the median over draws.

## Headline

| city-year | council | list MAE | ward MAE | seat err (median) | medians sum to | seat err (coherent) | CRPS | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 260 | 5.06pp | 4.24pp | 56 | 244 | 60 | 41.4 | 52 | 60 | 50 |
| Johannesburg 2016 | 270 | 0.83pp | 1.21pp | 21 | 259 | 28 | 20.6 | 92 | 26 | 91 |
| Johannesburg 2021 | 270 | 6.30pp | 5.12pp | 94 | 254 | 86 | 68.3 | 134 | 126 | 125 |
| Tshwane 2011 | 210 | 6.51pp | 4.86pp | 46 | 196 | 60 | 32.5 | 40 | 56 | 39 |
| Tshwane 2016 | 214 | 1.18pp | 1.02pp | 17 | 209 | 16 | 13.5 | 70 | 10 | 70 |
| Tshwane 2021 | 214 | 1.96pp | 1.92pp | 36 | 202 | 34 | 27.5 | 80 | 60 | 77 |
| Ekurhuleni 2011 | 202 | 3.55pp | 2.48pp | 32 | 188 | 36 | 24.8 | 32 | 44 | 35 |
| Ekurhuleni 2016 | 224 | 1.66pp | 2.11pp | 19 | 213 | 24 | 17.8 | 80 | 22 | 76 |
| Ekurhuleni 2021 | 224 | 2.51pp | 2.12pp | 38 | 208 | 26 | 29.3 | 72 | 48 | 66 |
| eThekwini 2011 | 205 | 2.68pp | 1.89pp | 28 | 196 | 31 | 23.3 | 49 | 35 | 55 |
| eThekwini 2016 | 219 | 1.57pp | 2.68pp | 29 | 212 | 34 | 21.0 | 64 | 50 | 59 |
| eThekwini 2021 | 222 | 2.27pp | 2.51pp | 39 | 205 | 34 | 30.4 | 82 | 36 | 76 |
| Cape Town 2011 | 221 | 4.27pp | 3.69pp | 38 | 207 | 42 | 26.6 | 94 | 58 | 93 |
| Cape Town 2016 | 231 | 0.49pp | 0.43pp | 11 | 224 | 8 | 12.2 | 46 | 30 | 49 |
| Cape Town 2021 | 231 | 2.18pp | 2.36pp | 43 | 220 | 40 | 34.1 | 68 | 38 | 63 |
| Mangaung 2011 | 97 | 8.00pp | 8.13pp | 29 | 92 | 34 | 18.7 | 28 | 30 | 28 |
| Mangaung 2016 | 100 | 0.55pp | 1.14pp | 6 | 94 | 10 | 7.1 | 24 | 12 | 22 |
| Mangaung 2021 | 101 | 1.79pp | 0.87pp | 7 | 94 | 8 | 9.5 | 24 | 8 | 20 |
| Nelson Mandela Bay 2011 | 120 | 7.20pp | 6.76pp | 33 | 111 | 34 | 21.0 | 48 | 42 | 48 |
| Nelson Mandela Bay 2016 | 120 | 0.48pp | 0.80pp | 6 | 116 | 8 | 7.6 | 38 | 16 | 38 |
| Nelson Mandela Bay 2021 | 120 | 2.60pp | 2.78pp | 22 | 112 | 20 | 17.0 | 28 | 22 | 27 |
| Buffalo City 2011 | 100 | 7.16pp | 6.90pp | 32 | 90 | 32 | 19.9 | 28 | 30 | 27 |
| Buffalo City 2016 | 100 | 1.17pp | 2.39pp | 11 | 95 | 10 | 9.5 | 28 | 14 | 25 |
| Buffalo City 2021 | 100 | 2.99pp | 1.91pp | 9 | 93 | 8 | 7.8 | 14 | 12 | 15 |
| **TOTAL** [rows=24] | 4375 | — | — | **702** | — | **723** | **541.4** | 1315 | 885 | 1274 |

### Citable totals

**Quoting one number in a sentence? Paste this token, do not retype the figure:**

```
seat_abs_err_coherent=723/@1d9a0e1d+dirty/1000d/pools:843229db/rows=24
```

The full set, for anything more than one number:

```
seat_abs_err_coherent = 723      [rows=24]
seat_abs_err          = 702      [rows=24]   # MARGINAL, not comparable to the line above
crps                  = 541.39   [rows=24]
n_scored              = 580      [rows=24]   # summed scoring columns, the CRPS denominator
margin_vs_uniform_swing = 18.3%   [rows=24, coherent]
```

`seat_abs_err` and `seat_abs_err_coherent` are DIFFERENT STATISTICS. Quoting one against the other is §1.214.

### The margin is not evenly spread

| | city-years | seat err (coherent) | uniform-swing | margin | CRPS | uniform-swing CRPS | margin |
|---|---|---|---|---|---|---|---|
| Gauteng (JHB, TSH, EKU) | 9 | 370 | 452 | 18% | 275.9 | 452.0 | 39% |
| everywhere else | 15 | 353 | 433 | 18% | 265.5 | 433.0 | 39% |

**The headline margin is a Gauteng result.** Outside Gauteng the model is closer to parity with uniform swing on seats and loses at Mangaung. Quote the split, not the pool.

**Sign count against uniform swing: 15 wins, 7 losses, 2 ties across 24 city-years** — 2011: 4W 3L 1T; 2016: 5W 3L 0T; 2021: 6W 1L 1T. The sign REPLICATES across cycles, which is what the amended bar's Key 1 asks of any candidate and is the strongest claim this panel supports. Metros inside one cycle share a national swing, so 24 city-years is 3 effective clusters, not 24 — never quote a p-value off the pooled count.

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber and is the only one comparable to the baselines, which allocate per draw and sum exactly. Lower is better throughout.


## The arrival channel, scored without the label

The headline CRPS above is scored after the model's generic `ENTRANT` column is renamed onto the largest party that actually arrived — a label chosen with the result in hand, which no baseline gets. This table does not use it. **PIT above 0.5 means the model forecast too little.**

| city-year | arrived | actual mass | forecast mass | actual seats | forecast seats | mass PIT | seats PIT |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 10 | 1.64% | 1.51% | 4 | 3.8 | 0.728 | 0.728 |
| Johannesburg 2016 | 13 | 2.29% | 1.84% | 5 | 4.8 | 0.742 | 0.605 |
| Johannesburg 2021 | 32 | 19.99% | 8.74% | 46 | 21.1 | 0.993 | 0.987 |
| Tshwane 2011 | 5 | 0.36% | 1.46% | 0 | 3.0 | 0.741 | 0.370 |
| Tshwane 2016 | 7 | 0.31% | 1.88% | 0 | 4.2 | 0.001 | 0.006 |
| Tshwane 2021 | 25 | 11.38% | 7.99% | 21 | 15.9 | 0.848 | 0.798 |
| Ekurhuleni 2011 | 12 | 2.56% | 1.41% | 5 | 2.8 | 0.766 | 0.766 |
| Ekurhuleni 2016 | 12 | 2.06% | 1.89% | 5 | 4.1 | 0.668 | 0.688 |
| Ekurhuleni 2021 | 20 | 9.14% | 5.98% | 17 | 12.8 | 0.869 | 0.789 |
| eThekwini 2011 | 8 | 5.61% | 1.41% | 11 | 2.9 | 0.875 | 0.868 |
| eThekwini 2016 | 14 | 3.25% | 1.98% | 6 | 4.2 | 0.917 | 0.821 |
| eThekwini 2021 | 29 | 7.21% | 3.69% | 15 | 7.4 | 0.907 | 0.903 |
| Cape Town 2011 | 16 | 1.02% | 1.49% | 1 | 3.3 | 0.747 | 0.747 |
| Cape Town 2016 | 20 | 1.43% | 1.70% | 2 | 3.8 | 0.469 | 0.248 |
| Cape Town 2021 | 31 | 8.00% | 2.01% | 18 | 4.2 | 0.998 | 0.998 |
| Mangaung 2011 | 2 | 0.28% | 1.26% | 0 | 1.1 | 0.782 | 0.391 |
| Mangaung 2016 | 6 | 4.74% | 2.09% | 3 | 1.8 | 0.947 | 0.835 |
| Mangaung 2021 | 11 | 1.53% | 2.50% | 0 | 2.1 | 0.310 | 0.080 |
| Nelson Mandela Bay 2011 | 4 | 0.41% | 1.32% | 0 | 1.6 | 0.766 | 0.383 |
| Nelson Mandela Bay 2016 | 8 | 1.59% | 1.82% | 2 | 1.9 | 0.502 | 0.563 |
| Nelson Mandela Bay 2021 | 15 | 7.02% | 2.11% | 8 | 2.1 | 0.980 | 0.976 |
| Buffalo City 2011 | 0 | 0.00% | 1.45% | 0 | 1.3 | 0.000 | 0.376 |
| Buffalo City 2016 | 3 | 0.68% | 1.95% | 0 | 1.8 | 0.100 | 0.073 |
| Buffalo City 2021 | 12 | 1.75% | 2.55% | 0 | 1.6 | 0.307 | 0.121 |
| **panel mean** | | | | | | **0.665** | **0.588** |

Mass PIT is above 0.5 at **18 of 24** city-years. A panel mean well above 0.5 on both columns is the model systematically under-forecasting how much of the ballot goes to parties arriving from nothing — read it next to the mid-ballot calibration below, which is the same leak seen through a different instrument.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | -10.31pp | 12.42pp | **+10.36pp** | 12.04pp | -0.05pp | 0.54pp | 0.00pp (0) | 12 |
| Johannesburg 2016 | -0.71pp | 3.11pp | **-1.66pp** | 3.05pp | +2.20pp | 2.42pp | 0.17pp (1) | 15 |
| Johannesburg 2021 | +1.73pp | 24.51pp | **-2.20pp** | 8.98pp | +0.38pp | 1.47pp | 0.09pp (2) | 58 |
| Tshwane 2011 | -10.61pp | 17.46pp | **+8.51pp** | 9.46pp | +0.64pp | 0.96pp | 1.46pp (1) | 6 |
| Tshwane 2016 | -3.27pp | 3.84pp | **+1.28pp** | 1.45pp | +1.87pp | 2.15pp | 0.12pp (1) | 7 |
| Tshwane 2021 | +6.89pp | 6.89pp | **-7.57pp** | 7.65pp | +0.42pp | 1.69pp | 0.26pp (4) | 44 |
| Ekurhuleni 2011 | -6.32pp | 8.55pp | **+6.94pp** | 9.27pp | -0.63pp | 0.76pp | 0.00pp (0) | 13 |
| Ekurhuleni 2016 | -0.66pp | 5.07pp | **-1.08pp** | 2.71pp | +1.74pp | 2.01pp | 0.00pp (0) | 12 |
| Ekurhuleni 2021 | +6.19pp | 6.19pp | **-7.03pp** | 7.13pp | +0.77pp | 1.48pp | 0.07pp (1) | 38 |
| eThekwini 2011 | -3.25pp | 5.58pp | **+3.38pp** | 11.58pp | -0.13pp | 0.38pp | 0.00pp (0) | 24 |
| eThekwini 2016 | -1.14pp | 4.03pp | **+0.25pp** | 5.84pp | +0.88pp | 1.21pp | 0.00pp (0) | 18 |
| eThekwini 2021 | +5.64pp | 5.64pp | **-4.83pp** | 5.47pp | -1.06pp | 3.79pp | 0.26pp (3) | 31 |
| Cape Town 2011 | -3.34pp | 16.09pp | **+3.50pp** | 4.52pp | -0.16pp | 1.24pp | 0.00pp (0) | 10 |
| Cape Town 2016 | +0.14pp | 2.09pp | **-1.07pp** | 1.34pp | +0.92pp | 1.61pp | 0.00pp (0) | 12 |
| Cape Town 2021 | +7.05pp | 7.05pp | **-6.97pp** | 7.12pp | -0.27pp | 2.02pp | 0.19pp (3) | 38 |
| Mangaung 2011 | -4.90pp | 26.38pp | **+3.64pp** | 4.71pp | +0.00pp | 0.00pp | 1.26pp (1) | 3 |
| Mangaung 2016 | +1.00pp | 1.97pp | **-1.12pp** | 5.43pp | +0.12pp | 0.48pp | 0.00pp (0) | 6 |
| Mangaung 2021 | -0.68pp | 4.70pp | **-0.62pp** | 3.45pp | +1.30pp | 2.04pp | 0.00pp (0) | 12 |
| Nelson Mandela Bay 2011 | -2.23pp | 26.22pp | **+0.96pp** | 2.25pp | -0.05pp | 0.05pp | 1.32pp (1) | 3 |
| Nelson Mandela Bay 2016 | -0.42pp | 1.78pp | **-0.76pp** | 2.63pp | +1.18pp | 1.25pp | 0.00pp (0) | 7 |
| Nelson Mandela Bay 2021 | +5.57pp | 7.37pp | **-6.36pp** | 6.83pp | +0.79pp | 1.48pp | 0.00pp (0) | 15 |
| Buffalo City 2011 | +0.14pp | 26.78pp | **-1.59pp** | 3.93pp | +0.00pp | 0.00pp | 1.45pp (1) | 5 |
| Buffalo City 2016 | -1.32pp | 5.30pp | **+1.32pp** | 6.18pp | +0.00pp | 0.00pp | 0.00pp (0) | 8 |
| Buffalo City 2021 | -1.57pp | 6.67pp | **+0.21pp** | 1.97pp | +1.18pp | 1.58pp | 0.18pp (1) | 6 |

**Totals across 24 city-years:** ranks 1-3 -16.36pp signed / 235.69pp absolute, ranks 4-12 -2.52pp / 135.00pp, ranks 13+ +12.07pp / 30.61pp.

**Phantom mass: 6.82pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -6.82pp rather than to zero.


## Ward winners — the geography key

**`seat_abs_err_coherent` cannot see geography and this can.** `solve_and_predict` forces every party's citywide share onto the share the draw drew, and both ballots are `weight @ pred` against those same targets, so `dev`, `gamma`, pool composition and the whole VD layer reach the seat score ONLY through an overhang trigger. Any change to those is judged here, or it is judged by an instrument that is blind to it. Hit rate is the modal call; Brier (multi-category, 0 to 2) is the proper score and is what a change in CONFIDENCE moves. **Read the model against the baselines in its own row** — safe wards are called correctly by anything at all.

| city-year | wards | model called | hit rate | Brier MC | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 130 | 126 | 96.9% | 0.048 | 92.3% | 93.8% | 92.3% |
| Johannesburg 2016 | 135 | 134 | 99.3% | 0.017 | 94.8% | 97.8% | 94.8% |
| Johannesburg 2021 | 135 | 127 | 94.1% | 0.092 | 93.3% | 93.3% | 93.3% |
| Tshwane 2011 | 105 (only 99 matched) | 98 | 93.3% | 0.081 | 98.1% | 98.1% | 98.1% |
| Tshwane 2016 | 107 | 104 | 97.2% | 0.044 | 98.1% | 98.1% | 98.1% |
| Tshwane 2021 | 107 | 104 | 97.2% | 0.038 | 98.1% | 98.1% | 98.1% |
| Ekurhuleni 2011 | 101 | 97 | 96.0% | 0.045 | 94.1% | 96.0% | 95.0% |
| Ekurhuleni 2016 | 112 | 111 | 99.1% | 0.027 | 97.3% | 99.1% | 97.3% |
| Ekurhuleni 2021 | 112 | 108 | 96.4% | 0.068 | 95.5% | 94.6% | 95.5% |
| eThekwini 2011 | 103 | 97 | 94.2% | 0.101 | 93.2% | 92.2% | 93.2% |
| eThekwini 2016 | 110 (only 109 matched) | 97 | 88.2% | 0.201 | 82.7% | 85.5% | 83.6% |
| eThekwini 2021 | 111 | 109 | 98.2% | 0.036 | 96.4% | 98.2% | 96.4% |
| Cape Town 2011 | 111 | 111 | 100.0% | 0.014 | 85.6% | 97.3% | 85.6% |
| Cape Town 2016 | 116 | 116 | 100.0% | 0.004 | 100.0% | 100.0% | 100.0% |
| Cape Town 2021 | 116 | 115 | 99.1% | 0.014 | 99.1% | 99.1% | 99.1% |
| Mangaung 2011 | 49 | 49 | 100.0% | 0.026 | 98.0% | 95.9% | 98.0% |
| Mangaung 2016 | 50 (only 49 matched) | 48 | 96.0% | 0.034 | 96.0% | 98.0% | 96.0% |
| Mangaung 2021 | 51 | 50 | 98.0% | 0.038 | 98.0% | 96.1% | 98.0% |
| Nelson Mandela Bay 2011 | 60 | 59 | 98.3% | 0.024 | 83.3% | 96.7% | 83.3% |
| Nelson Mandela Bay 2016 | 60 | 57 | 95.0% | 0.069 | 96.7% | 96.7% | 96.7% |
| Nelson Mandela Bay 2021 | 60 | 57 | 95.0% | 0.047 | 95.0% | 95.0% | 95.0% |
| Buffalo City 2011 | 50 | 49 | 98.0% | 0.045 | 94.0% | 98.0% | 94.0% |
| Buffalo City 2016 | 50 | 48 | 96.0% | 0.089 | 100.0% | 96.0% | 100.0% |
| Buffalo City 2021 | 50 | 48 | 96.0% | 0.071 | 96.0% | 96.0% | 96.0% |

**Pooled over 24 city-years: 2119/2191 = 96.7% of ward contests called correctly, against last-lge 94.7%, uniform-swing 96.2%, prior-lge-noise 94.8%. A margin over the baselines that is smaller than the seat margin is the model's geography adding less than its citywide machinery, which is a statement the seat columns cannot make.

## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |
|---|---|---|---|---|---|---|
| reference (INPUT-selected — fixed; the only one to compare on) | 514 | 79% | 91% | 94% | 0.581 | 57.0 (16.92) |
| claimed by the model (forecast-selected — neutral for ONE model) | 157 | 77% | 92% | 95% | 0.536 | 40.9 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 269 | 59% | 81% | 87% | 0.692 | 127.7 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 580 | 81% | 91% | 94% | 0.550 | 30.7 (16.92) |

* **reference** (n=514) PIT histogram [35, 27, 28, 45, 42, 70, 66, 72, 70, 59] — approximately flat
* **claimed** (n=157) PIT histogram [12, 8, 6, 15, 19, 31, 18, 24, 20, 4] — hump-shaped: the truth lands mid-distribution too often — over-dispersed, the model is hedging
* **seat_holders** (n=269) PIT histogram [10, 4, 6, 12, 19, 33, 32, 44, 51, 58] — U-shaped: the truth lands outside the distribution too often — under-dispersed, widen it; mean PIT 0.69 — the model under-predicts seats
* **all** (n=580) PIT histogram [47, 42, 37, 57, 48, 75, 65, 75, 73, 61] — approximately flat

The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ² column is the test of uniformity; the level-free dispersion table is the test of width.**

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. Five of its columns across the nine city-years carry PIT exactly 1.0 — parties the model gave zero seats in every draw, present only because they won a seat. It is a mixture of an outcome-selected set and a neutral one, and the neutral part is itself diluted by ~200 parties correctly at zero on both sides, each a free interval hit and a near-uniform PIT. Two errors pushing opposite ways: `all` tests nothing.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.528 | [0.491, 0.562] | 72% [58–85] | 92% [85–97] | 96% [92–100] | 69% [54–83] | 92% [85–97] | 94% [89–99] |
| ranks 4-12 | 78 | 0.572 | [0.493, 0.641] | 82% [73–91] | 91% [86–96] | 94% [89–98] | 65% [54–77] | 90% [84–95] | 94% [89–98] |
| ranks 13+ | 7 | 0.220 | [0.114, 0.483] | 71% [25–100] | 100% [100–100] | 100% [100–100] | 29% [0–100] | 71% [25–100] | 100% [100–100] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.748 | 0.755 | +0.062 | 0.0525 vs 0.0833 |
| ranks 4-12 | 78 | 0.850 | 0.794 | +0.004 | 0.0558 vs 0.0833 |
| ranks 13+ | 7 | 0.593 | 0.416 | -0.646 | 0.0333 vs 0.0833 |

#### The same question on the FIXED population — and it disagrees

**The `n` here is the number of columns the width figure was actually computed on** — columns with a defined `z`. A column whose draws are all identical has no scale, so it carries a PIT and no `z`; the pooled tables above count PIT values and their `n` is larger.

| band | `claimed` n(z) | `claimed` SD of z | `reference` n(z) | `reference` SD of z | `reference` mean z | `reference` probit-SD |
|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.755 | 72 | 0.755 | +0.062 | **0.748** |
| ranks 4-12 | 78 | 0.794 | 170 | 1.557 | +0.420 | **1.308** |
| ranks 13+ | 7 | 0.416 | 171 | 0.381 | -0.177 | **1.119** |

**Read the last column, not the `SD of z` column, on ranks 13+.** `sd(z)` is exact under a level shift and **meaningless on a near-degenerate discrete column**: where the forecast is roughly Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly, a function of the forecast probability with no room to spread. On the 96 ranks-13+ columns whose truth is zero, observed `z` correlates with that expression at **+0.93**. probit-SD comes from the randomised PIT, which is uniform under calibration whatever the support, and is the one to read there — at the cost of being attenuated by a level shift, so it is a LOWER BOUND wherever `mean z` is far from zero. Neither statistic is right everywhere; the pair is. MODEL-LOG §1.58.

**Ranks 1-3 are the same columns in both populations** — the top three are always claimed — so that row is a consistency check and the two `SD of z` numbers should agree exactly. It is also the band that is genuinely too WIDE and the band that responds to `dirichlet_scale`.

**Ranks 4-12 cannot be described by one width, and that is the finding.** On the same columns `sd(z)` says far too narrow, `IQR-sd` says too wide, and probit-SD disagrees with both — because the error distribution is a narrow shifted bulk with two enormous outliers, Cape Town's Cape Coloured Congress and Johannesburg's PA, both of which `claimed` excludes by construction. A distribution that reads differently depending which moment you take is mis-SHAPED, not mis-scaled, and no scalar fixes it.

⛔ **AND THE SPREAD AT 4-12 IS TWO COLUMNS.** Those two carry ~70% of the band's total squared z; dropping them takes `sd(z)` to about 1.0. Quote the leave-the-largest-out figure beside the headline or the headline is two observations, not a width. §1.56, §1.58, §1.131.

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2011 | 6 | 67% | 83% | 83% | 0.501 |
| Johannesburg 2016 | 8 | 88% | 100% | 100% | 0.527 |
| Johannesburg 2021 | 9 | 33% | 67% | 78% | 0.639 |
| Tshwane 2011 | 5 | 40% | 80% | 80% | 0.472 |
| Tshwane 2016 | 10 | 90% | 100% | 100% | 0.363 |
| Tshwane 2021 | 7 | 71% | 86% | 100% | 0.613 |
| Ekurhuleni 2011 | 6 | 67% | 83% | 100% | 0.439 |
| Ekurhuleni 2016 | 6 | 100% | 100% | 100% | 0.554 |
| Ekurhuleni 2021 | 9 | 78% | 89% | 89% | 0.691 |
| eThekwini 2011 | 6 | 100% | 100% | 100% | 0.449 |
| eThekwini 2016 | 8 | 75% | 88% | 88% | 0.501 |
| eThekwini 2021 | 10 | 100% | 100% | 100% | 0.587 |
| Cape Town 2011 | 6 | 67% | 83% | 83% | 0.535 |
| Cape Town 2016 | 7 | 86% | 100% | 100% | 0.633 |
| Cape Town 2021 | 7 | 71% | 100% | 100% | 0.522 |
| Mangaung 2011 | 4 | 0% | 75% | 100% | 0.452 |
| Mangaung 2016 | 4 | 100% | 100% | 100% | 0.475 |
| Mangaung 2021 | 6 | 100% | 100% | 100% | 0.579 |
| Nelson Mandela Bay 2011 | 3 | 33% | 67% | 100% | 0.555 |
| Nelson Mandela Bay 2016 | 7 | 100% | 100% | 100% | 0.572 |
| Nelson Mandela Bay 2021 | 6 | 83% | 100% | 100% | 0.480 |
| Buffalo City 2011 | 3 | 33% | 67% | 67% | 0.541 |
| Buffalo City 2016 | 8 | 88% | 100% | 100% | 0.529 |
| Buffalo City 2021 | 6 | 100% | 100% | 100% | 0.549 |


## Johannesburg 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 55.85% | 55.18% | 59.29% | 55.25% | 57.82% | 145 | 153 |
| DA | 27.04% | 27.10% | 34.35% | 27.41% | 34.90% | 71 | 90 |
| IFP | 1.31% | 2.67% | 1.61% | 2.22% | 1.66% | 3 | 4 |
| COPE | 9.01% | 10.13% | 1.11% | 9.69% | 1.19% | 23 | 3 |
| NFP | 0.00% | 1.51% | 0.82% | 1.44% | 0.74% | 0 | 2 |
| APC | 0.00% | 0.21% | 0.53% | 0.20% | 0.39% | 0 | 1 |
| ACDP | 0.31% | 0.79% | 0.40% | 0.77% | 0.44% | 1 | 1 |
| PAC | 0.00% | 0.63% | 0.35% | 0.87% | 0.43% | 0 | 1 |
| ALJAMAAH | nan% | nan% | 0.27% | nan% | 0.19% | 0 | 1 |
| OKM | nan% | nan% | 0.25% | nan% | 0.15% | 0 | 1 |
| VFPLUS | 0.27% | 0.91% | 0.23% | 0.92% | 0.27% | 1 | 1 |
| UDM | 0.01% | 0.36% | 0.22% | 0.71% | 0.25% | 0 | 1 |

## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 44.52% | 44.56% | 44.92% | 43.82% | 44.09% | 119 | 121 |
| DA | 39.59% | 39.68% | 38.48% | 40.62% | 38.34% | 108 | 104 |
| EFF | 9.13% | 9.38% | 10.93% | 9.72% | 11.24% | 25 | 30 |
| IFP | 1.02% | 1.24% | 1.71% | 1.13% | 1.74% | 3 | 5 |
| AIC | 0.06% | 0.16% | 1.62% | 0.17% | 1.40% | 0 | 4 |
| ACDP | 0.34% | 0.52% | 0.31% | 0.55% | 0.28% | 1 | 1 |
| VFPLUS | 0.19% | 0.44% | 0.31% | 0.54% | 0.34% | 1 | 1 |
| ALJAMAAH | nan% | nan% | 0.31% | nan% | 0.22% | 0 | 1 |
| UDM | 0.17% | 0.36% | 0.25% | 0.41% | 0.28% | 1 | 1 |
| COPE | 0.07% | 0.23% | 0.21% | 0.15% | 0.15% | 0 | 1 |
| PA | 0.00% | 0.06% | 0.17% | 0.06% | 0.13% | 0 | 1 |
| PAC | 0.20% | 0.39% | 0.17% | 0.09% | 0.09% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 38.92% | 38.90% | 33.22% | 38.99% | 33.97% | 105 | 91 |
| DA | 32.79% | 32.89% | 25.45% | 33.46% | 26.83% | 89 | 71 |
| ASA | 6.30% | 6.73% | 18.12% | 5.56% | 13.98% | 16 | 44 |
| EFF | 13.02% | 13.43% | 10.11% | 14.10% | 11.14% | 36 | 29 |
| PA | 0.03% | 0.09% | 2.96% | 0.17% | 2.91% | 0 | 8 |
| IFP | 0.81% | 1.39% | 2.36% | 1.79% | 2.36% | 3 | 7 |
| VFPLUS | 0.64% | 0.89% | 1.33% | 0.98% | 1.35% | 2 | 4 |
| ACDP | 0.28% | 0.59% | 1.03% | 0.61% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.23% | 0.30% | 0.83% | 0.28% | 1.08% | 1 | 3 |
| AIC | 0.21% | 0.74% | 0.69% | 0.37% | 0.50% | 1 | 2 |
| AHC | 0.01% | 0.07% | 0.43% | 0.06% | 0.47% | 0 | 1 |
| GOOD | 0.12% | 0.35% | 0.33% | 0.29% | 0.40% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 52.29% | 51.10% | 56.46% | 50.91% | 54.18% | 110 | 118 |
| DA | 29.79% | 30.07% | 38.74% | 31.03% | 38.56% | 63 | 82 |
| VFPLUS | 4.13% | 5.01% | 1.59% | 5.26% | 1.73% | 9 | 4 |
| COPE | 6.54% | 7.82% | 0.89% | 7.35% | 0.92% | 13 | 2 |
| ACDP | 0.49% | 1.37% | 0.59% | 1.49% | 0.67% | 1 | 1 |
| APC | 0.00% | 0.19% | 0.46% | 0.18% | 0.35% | 0 | 1 |
| PAC | 0.01% | 0.46% | 0.25% | 0.58% | 0.28% | 0 | 1 |
| AZAPO | 0.00% | 0.43% | 0.18% | 0.48% | 0.21% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.06% | 0.83% | 0.15% | 0.32% | 0.12% | 0 | 0 |
| IFP | 0.01% | 0.25% | 0.12% | 0.21% | 0.13% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.11% | nan% | 0.13% | 0 | 0 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.09% | nan% | 0.05% | 0 | 0 |

## Tshwane 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 40.68% | 41.06% | 43.10% | 41.62% | 43.20% | 88 | 93 |
| ANC | 41.73% | 41.77% | 41.48% | 40.46% | 41.02% | 88 | 89 |
| EFF | 9.85% | 10.12% | 11.64% | 10.84% | 11.62% | 22 | 25 |
| VFPLUS | 2.03% | 2.29% | 1.97% | 2.52% | 2.02% | 5 | 4 |
| ACDP | 0.46% | 0.72% | 0.47% | 0.83% | 0.52% | 1 | 1 |
| APC | 0.17% | 0.43% | 0.24% | 0.07% | 0.05% | 0 | 0 |
| COPE | 0.02% | 0.18% | 0.22% | 0.19% | 0.27% | 0 | 1 |
| PAC | 0.10% | 0.33% | 0.14% | 0.36% | 0.20% | 0 | 1 |
| UDM | 0.02% | 0.19% | 0.13% | 0.23% | 0.10% | 0 | 0 |
| IFP | 0.00% | 0.14% | 0.10% | 0.03% | 0.02% | 0 | 0 |
| AFRICAN_MANDATE_CONGRESS | 0.26% | 0.42% | 0.09% | 0.45% | 0.06% | 1 | 0 |
| PA | 0.00% | 0.04% | 0.09% | 0.04% | 0.05% | 0 | 0 |

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 36.34% | 36.26% | 34.84% | 36.36% | 34.42% | 78 | 75 |
| DA | 33.04% | 33.36% | 31.77% | 33.59% | 32.29% | 71 | 69 |
| EFF | 13.91% | 14.31% | 10.43% | 14.35% | 10.94% | 30 | 23 |
| ASA | 5.20% | 5.90% | 9.28% | 5.49% | 7.99% | 11 | 19 |
| VFPLUS | 4.54% | 4.84% | 7.79% | 4.97% | 7.96% | 10 | 17 |
| ACDP | 0.35% | 0.73% | 0.91% | 0.80% | 0.93% | 1 | 2 |
| AIC | 0.27% | 0.67% | 0.81% | 0.63% | 0.38% | 1 | 1 |
| DOP | 0.03% | 0.11% | 0.49% | 0.11% | 0.58% | 0 | 1 |
| PA | 0.02% | 0.05% | 0.48% | 0.11% | 0.52% | 0 | 1 |
| PAC | 0.00% | 0.25% | 0.21% | 0.24% | 0.18% | 0 | 1 |
| IFP | 0.00% | 0.13% | 0.21% | 0.19% | 0.09% | 0 | 1 |
| COPE | 0.00% | 0.10% | 0.19% | 0.12% | 0.20% | 0 | 1 |

## Ekurhuleni 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.74% | 58.38% | 62.17% | 59.06% | 61.08% | 122 | 125 |
| DA | 25.72% | 26.49% | 30.13% | 26.64% | 30.46% | 52 | 62 |
| IFP | 0.87% | 2.28% | 1.16% | 1.45% | 1.04% | 1 | 2 |
| NFP | 0.00% | 1.41% | 1.13% | 1.33% | 1.19% | 0 | 3 |
| COPE | 5.20% | 6.95% | 1.09% | 6.55% | 0.79% | 10 | 2 |
| APC | 0.00% | 0.25% | 0.68% | 0.24% | 0.54% | 0 | 1 |
| PAC | 0.04% | 0.72% | 0.61% | 0.73% | 0.75% | 0 | 2 |
| ACDP | 0.47% | 1.05% | 0.59% | 1.25% | 0.67% | 1 | 1 |
| VFPLUS | 1.05% | 1.85% | 0.51% | 1.75% | 0.59% | 2 | 1 |
| UDM | 0.00% | 0.48% | 0.42% | 0.88% | 0.51% | 0 | 1 |
| DISPLACEES_RATE_PAYERS_ASSOCIATION | nan% | nan% | 0.41% | nan% | 0.48% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.32% | nan% | 0.78% | 0 | 1 |

**Missed entirely:** NFP — won seats, median zero.

## Ekurhuleni 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 47.35% | 47.34% | 48.84% | 45.99% | 48.44% | 105 | 109 |
| DA | 35.97% | 36.33% | 34.13% | 36.61% | 34.17% | 81 | 77 |
| EFF | 9.25% | 9.73% | 11.10% | 10.87% | 11.35% | 22 | 25 |
| AIC | 0.06% | 0.17% | 1.65% | 0.19% | 1.63% | 0 | 4 |
| IFP | 0.57% | 0.92% | 1.04% | 1.13% | 0.99% | 2 | 2 |
| VFPLUS | 0.72% | 0.92% | 0.90% | 1.08% | 0.89% | 2 | 2 |
| ACDP | 0.34% | 0.66% | 0.42% | 0.80% | 0.43% | 1 | 1 |
| PAC | 0.22% | 0.54% | 0.42% | 0.25% | 0.43% | 0 | 1 |
| COPE | 0.02% | 0.22% | 0.28% | 0.23% | 0.25% | 0 | 1 |
| PA | 0.00% | 0.04% | 0.28% | 0.04% | 0.25% | 0 | 1 |
| APC | 0.22% | 0.54% | 0.27% | 0.14% | 0.06% | 0 | 0 |
| UDM | 0.10% | 0.37% | 0.23% | 0.20% | 0.16% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 43.40% | 43.07% | 38.34% | 42.80% | 38.03% | 97 | 86 |
| DA | 28.93% | 29.60% | 28.37% | 29.42% | 29.07% | 65 | 65 |
| EFF | 13.02% | 13.50% | 13.27% | 13.71% | 13.87% | 29 | 31 |
| ASA | 3.27% | 3.89% | 7.36% | 3.82% | 5.84% | 7 | 15 |
| VFPLUS | 2.59% | 2.97% | 3.48% | 2.92% | 3.18% | 6 | 8 |
| PA | 0.15% | 0.21% | 1.87% | 0.42% | 1.89% | 1 | 4 |
| IFP | 0.50% | 1.22% | 1.47% | 1.08% | 1.24% | 1 | 3 |
| AIC | 0.28% | 0.99% | 1.36% | 1.12% | 1.22% | 1 | 3 |
| ACDP | 0.24% | 0.72% | 0.86% | 0.75% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.04% | 0.14% | 0.45% | 0.13% | 0.44% | 0 | 1 |
| PAC | 0.03% | 0.49% | 0.43% | 0.55% | 0.31% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.36% | nan% | 0.78% | 0 | 1 |

## eThekwini 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.72% | 58.72% | 62.02% | 61.35% | 60.11% | 125 | 126 |
| DA | 20.23% | 20.70% | 21.81% | 16.88% | 20.21% | 38 | 43 |
| MINORITY_FRONT | 5.93% | 6.10% | 4.94% | 6.61% | 5.68% | 13 | 11 |
| NFP | 0.00% | 1.41% | 4.48% | 1.43% | 4.92% | 0 | 10 |
| IFP | 6.93% | 8.44% | 3.96% | 8.91% | 4.30% | 15 | 9 |
| ACDP | 0.75% | 1.31% | 0.67% | 1.52% | 0.80% | 2 | 2 |
| TRULY_ALLIANCE | nan% | nan% | 0.62% | nan% | 0.83% | 0 | 1 |
| APC | 0.00% | 0.25% | 0.41% | 0.26% | 0.20% | 0 | 1 |
| COPE | 1.36% | 2.64% | 0.40% | 2.69% | 0.35% | 3 | 1 |
| UNITED_ACTION_FRONT | nan% | nan% | 0.13% | nan% | 0.21% | 0 | 0 |
| AZAPO | nan% | nan% | 0.13% | nan% | 0.14% | 0 | 0 |
| UDM | 0.00% | 0.23% | 0.11% | 0.18% | 0.15% | 0 | 0 |

**Missed entirely:** NFP — won seats, median zero.

## eThekwini 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.38% | 57.30% | 59.11% | 52.76% | 52.95% | 121 | 126 |
| DA | 28.82% | 28.99% | 27.54% | 33.18% | 26.30% | 68 | 61 |
| IFP | 3.35% | 3.50% | 4.28% | 3.48% | 4.12% | 7 | 10 |
| EFF | 2.56% | 2.69% | 3.63% | 2.80% | 3.26% | 6 | 8 |
| AIC | 0.04% | 0.13% | 1.51% | 0.14% | 1.23% | 0 | 3 |
| ACDP | 0.49% | 0.62% | 0.54% | 0.70% | 0.55% | 1 | 1 |
| MINORITY_FRONT | 2.91% | 3.19% | 0.46% | 3.47% | 0.60% | 7 | 1 |
| DEMOCRATIC_LIBERAL_CONGRESS | 0.04% | 0.13% | 0.43% | 0.13% | 0.60% | 0 | 1 |
| TRULY_ALLIANCE | 0.36% | 0.50% | 0.42% | 0.64% | 0.40% | 1 | 1 |
| MINORITIES_OF_SOUTH_AFRICA | 0.05% | 0.15% | 0.27% | 0.15% | 0.35% | 0 | 1 |
| APC | 0.30% | 0.42% | 0.26% | 0.23% | 0.15% | 1 | 1 |
| ALJAMAAH | 0.05% | 0.14% | 0.18% | 0.15% | 0.20% | 0 | 1 |

**Missed entirely:** AIC — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 46.38% | 46.03% | 42.51% | 44.64% | 41.77% | 102 | 96 |
| DA | 27.92% | 28.36% | 26.33% | 29.30% | 25.57% | 63 | 59 |
| EFF | 9.82% | 10.89% | 10.80% | 10.78% | 10.15% | 22 | 24 |
| IFP | 4.17% | 5.01% | 7.45% | 5.50% | 6.67% | 10 | 16 |
| ASA | 0.72% | 1.33% | 2.35% | 1.29% | 1.50% | 2 | 4 |
| AIC | 0.28% | 0.92% | 1.01% | 0.39% | 0.33% | 1 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.03% | 0.14% | 0.81% | 0.13% | 1.03% | 0 | 2 |
| ACDP | 0.39% | 0.67% | 0.76% | 0.73% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.02% | 0.10% | 0.65% | 0.09% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.03% | 0.32% | 0.61% | 0.31% | 0.51% | 0 | 1 |
| ATM | 0.20% | 0.66% | 0.57% | 0.64% | 0.66% | 1 | 1 |
| MINORITY_FRONT | 0.53% | 0.74% | 0.50% | 1.04% | 0.47% | 2 | 1 |

## Cape Town 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 57.97% | 57.72% | 61.15% | 58.07% | 60.69% | 128 | 135 |
| ANC | 26.87% | 26.88% | 33.17% | 26.25% | 32.44% | 59 | 73 |
| COPE | 6.89% | 7.51% | 1.13% | 7.44% | 1.08% | 15 | 3 |
| ACDP | 1.17% | 1.80% | 1.06% | 1.92% | 1.37% | 3 | 3 |
| NATIONAL_PARTY_SOUTH_AFRICA | 0.00% | 0.17% | 0.54% | 0.17% | 0.51% | 0 | 1 |
| UDM | 0.10% | 0.62% | 0.38% | 0.54% | 0.40% | 0 | 1 |
| ALJAMAAH | 0.23% | 0.86% | 0.35% | 0.85% | 0.39% | 1 | 1 |
| AFRICA_MUSLIM_PARTY | 0.38% | 0.89% | 0.28% | 1.12% | 0.40% | 1 | 1 |
| CAPE_MUSLIM_CONGRESS | 0.00% | 1.49% | 0.25% | 1.48% | 0.33% | 0 | 1 |
| PAC | 0.08% | 0.55% | 0.18% | 0.57% | 0.23% | 0 | 1 |
| VFPLUS | 0.08% | 0.48% | 0.17% | 0.48% | 0.19% | 0 | 1 |
| DEMOCRATS_FOR_CHANGE | nan% | nan% | 0.15% | nan% | 0.08% | 0 | 0 |

## Cape Town 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 66.79% | 66.47% | 66.75% | 66.93% | 66.46% | 155 | 154 |
| ANC | 25.47% | 25.64% | 24.52% | 24.59% | 24.20% | 58 | 57 |
| EFF | 2.23% | 2.43% | 3.12% | 2.67% | 3.22% | 6 | 7 |
| ACDP | 0.70% | 0.96% | 1.13% | 1.18% | 1.29% | 2 | 3 |
| AIC | 0.28% | 0.48% | 0.76% | 0.53% | 0.42% | 1 | 1 |
| ALJAMAAH | 0.22% | 0.41% | 0.55% | 0.49% | 0.76% | 1 | 2 |
| VFPLUS | 0.18% | 0.31% | 0.39% | 0.37% | 0.43% | 1 | 1 |
| UDM | 0.23% | 0.39% | 0.33% | 0.20% | 0.20% | 0 | 1 |
| DEMOCRATIC_INDEPENDENT_PARTY | 0.01% | 0.11% | 0.28% | 0.12% | 0.32% | 0 | 1 |
| CAPE_MUSLIM_CONGRESS | nan% | nan% | 0.27% | nan% | 0.25% | 0 | 1 |
| COPE | 0.04% | 0.16% | 0.24% | 0.16% | 0.25% | 0 | 1 |
| PAC | 0.16% | 0.31% | 0.24% | 0.40% | 0.27% | 0 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 61.05% | 60.87% | 58.74% | 60.04% | 57.78% | 140 | 135 |
| ANC | 22.69% | 22.70% | 18.71% | 22.97% | 18.46% | 53 | 43 |
| EFF | 4.77% | 5.09% | 4.15% | 5.20% | 4.10% | 11 | 10 |
| GOOD | 2.91% | 3.25% | 3.68% | 3.12% | 3.94% | 7 | 9 |
| CAPE_COLOURED_CONGRESS | 0.00% | 0.08% | 2.83% | 0.07% | 2.78% | 0 | 7 |
| ACDP | 2.00% | 2.36% | 2.29% | 2.81% | 2.40% | 5 | 6 |
| VFPLUS | 0.69% | 0.99% | 1.54% | 1.07% | 1.63% | 2 | 4 |
| PA | nan% | nan% | 1.43% | nan% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.65% | 0.88% | 1.19% | 1.20% | 1.32% | 2 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.00% | 0.08% | 0.64% | 0.07% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.00% | 0.09% | 0.62% | 0.09% | 0.65% | 0 | 2 |
| UIM | 0.00% | 0.08% | 0.56% | 0.08% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 58.92% | 58.03% | 66.57% | 57.24% | 65.96% | 57 | 65 |
| DA | 18.62% | 19.73% | 26.82% | 20.10% | 27.40% | 18 | 26 |
| COPE | 12.45% | 14.04% | 3.30% | 11.41% | 3.02% | 11 | 3 |
| VFPLUS | 3.78% | 4.33% | 1.40% | 8.65% | 1.62% | 6 | 2 |
| ACDP | 0.23% | 1.03% | 0.56% | 0.45% | 0.29% | 0 | 0 |
| APC | 0.00% | 0.30% | 0.55% | 0.25% | 0.39% | 0 | 1 |
| PAC | 0.01% | 0.66% | 0.26% | 0.32% | 0.21% | 0 | 0 |
| DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA | 0.00% | 0.62% | 0.25% | 0.57% | 0.22% | 0 | 0 |
| BLACK_CONSCIOUSNESS_PARTY | nan% | nan% | 0.15% | nan% | 0.09% | 0 | 0 |
| UNITED_RESIDENTS_FRONT | nan% | nan% | 0.14% | nan% | 0.20% | 0 | 0 |

## Mangaung 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.34% | 56.71% | 56.77% | 56.47% | 56.28% | 57 | 58 |
| DA | 26.99% | 27.69% | 26.20% | 28.42% | 25.73% | 27 | 27 |
| EFF | 7.88% | 8.41% | 8.84% | 7.57% | 8.48% | 8 | 9 |
| AIC | 0.27% | 0.50% | 2.74% | 0.45% | 0.64% | 0 | 2 |
| VFPLUS | 2.12% | 2.36% | 1.85% | 2.74% | 1.99% | 2 | 2 |
| AGENCY_FOR_NEW_AGENDA | 0.29% | 0.54% | 1.57% | 0.48% | 0.21% | 0 | 1 |
| COPE | 0.29% | 0.78% | 0.56% | 0.84% | 0.63% | 0 | 1 |
| ACDP | 0.31% | 0.56% | 0.39% | 0.87% | 0.39% | 0 | 0 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.03% | 0.29% | 0.28% | 0.26% | 0.11% | 0 | 0 |
| APC | 0.18% | 0.69% | 0.25% | 0.64% | 0.17% | 0 | 0 |
| AZANIAN_ALLIANCE_CONGRESS | 0.29% | 0.55% | 0.13% | 0.49% | 0.06% | 0 | 0 |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 0.31% | 0.51% | 0.12% | 0.46% | 0.09% | 0 | 0 |

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 49.13% | 48.82% | 51.51% | 48.44% | 49.75% | 50 | 51 |
| DA | 25.42% | 26.27% | 25.48% | 25.81% | 25.98% | 26 | 26 |
| EFF | 11.89% | 12.59% | 11.37% | 12.08% | 11.24% | 12 | 12 |
| VFPLUS | 3.41% | 3.68% | 4.41% | 3.94% | 4.55% | 4 | 5 |
| PA | 1.13% | 2.01% | 1.78% | 1.93% | 1.83% | 1 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.04% | 0.43% | 1.26% | 0.41% | 1.61% | 0 | 2 |
| AIC | 0.76% | 1.75% | 0.84% | 3.19% | 1.70% | 1 | 1 |
| ACDP | 0.25% | 0.72% | 0.70% | 0.75% | 0.74% | 0 | 1 |
| ATM | 0.17% | 0.71% | 0.61% | 0.68% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.38% | nan% | 0.38% | 0 | 0 |
| COPE | 0.00% | 0.22% | 0.30% | 0.09% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.16% | 0.36% | 0.21% | 0.34% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.27% | 44.72% | 52.13% | 45.06% | 51.69% | 54 | 63 |
| DA | 32.49% | 33.43% | 40.24% | 33.10% | 40.02% | 39 | 48 |
| COPE | 15.22% | 16.88% | 4.88% | 15.95% | 5.01% | 18 | 6 |
| UDM | 0.04% | 0.66% | 0.54% | 1.04% | 0.55% | 0 | 1 |
| PAC | 0.03% | 0.83% | 0.52% | 1.44% | 0.57% | 0 | 1 |
| APC | 0.00% | 0.15% | 0.43% | 0.14% | 0.01% | 0 | 0 |
| ACDP | 0.35% | 0.69% | 0.36% | 0.75% | 0.40% | 0 | 1 |
| AZAPO | 0.01% | 0.58% | 0.28% | 0.44% | 0.22% | 0 | 0 |
| VFPLUS | 0.31% | 0.74% | 0.20% | 0.84% | 0.25% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.16% | nan% | 0.18% | 0 | 0 |
| AFRICAN_COMMUNITY_MOVEMENT | nan% | nan% | 0.14% | nan% | 0.18% | 0 | 0 |
| UNITED_INDEPENDENT_FRONT | nan% | nan% | 0.06% | nan% | 0.08% | 0 | 0 |

## Nelson Mandela Bay 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 47.10% | 47.34% | 46.66% | 47.78% | 46.75% | 57 | 57 |
| ANC | 41.48% | 41.28% | 41.50% | 40.85% | 40.34% | 50 | 50 |
| EFF | 3.81% | 4.15% | 5.03% | 4.32% | 5.21% | 5 | 6 |
| UDM | 0.75% | 1.07% | 1.83% | 1.06% | 2.00% | 1 | 2 |
| AIC | 0.90% | 1.19% | 1.61% | 1.24% | 0.28% | 1 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.22% | 0.43% | 0.80% | 0.44% | 1.09% | 0 | 1 |
| COPE | 0.41% | 0.73% | 0.70% | 0.75% | 0.77% | 1 | 1 |
| ACDP | 0.26% | 0.49% | 0.35% | 0.57% | 0.37% | 0 | 1 |
| PA | 0.04% | 0.15% | 0.29% | 0.16% | 0.24% | 0 | 1 |
| ALTERNATIVE_DEMOCRATS | 0.11% | 0.28% | 0.25% | 0.29% | 0.08% | 0 | 0 |
| VFPLUS | 0.33% | 0.55% | 0.25% | 0.69% | 0.26% | 1 | 0 |
| PAC | 0.35% | 0.65% | 0.23% | 0.21% | 0.12% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 44.89% | 45.15% | 40.04% | 45.13% | 39.80% | 54 | 48 |
| ANC | 38.73% | 38.70% | 39.60% | 38.17% | 39.26% | 46 | 48 |
| EFF | 7.16% | 7.76% | 6.40% | 8.15% | 6.40% | 9 | 8 |
| NORTHERN_ALLIANCE | 0.04% | 0.15% | 2.09% | 0.16% | 2.18% | 0 | 3 |
| ACDP | 0.76% | 1.06% | 1.68% | 1.13% | 1.64% | 1 | 2 |
| VFPLUS | 1.11% | 1.36% | 1.64% | 1.40% | 1.51% | 1 | 2 |
| DOP | 0.04% | 0.19% | 1.38% | 0.19% | 1.47% | 0 | 2 |
| PA | nan% | nan% | 1.32% | nan% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.04% | 0.16% | 1.11% | 0.17% | 1.05% | 0 | 1 |
| UDM | 0.28% | 0.86% | 1.07% | 1.01% | 1.01% | 0 | 1 |
| AIC | 0.30% | 0.92% | 0.68% | 0.46% | 0.38% | 0 | 1 |
| PAC | 0.02% | 0.42% | 0.51% | 0.50% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 62.12% | 61.23% | 69.13% | 63.06% | 70.88% | 63 | 71 |
| DA | 12.77% | 14.83% | 20.26% | 15.69% | 20.71% | 13 | 21 |
| COPE | 15.68% | 17.16% | 3.70% | 13.58% | 2.02% | 14 | 3 |
| AIC | 0.02% | 0.83% | 3.58% | 0.65% | 0.17% | 0 | 2 |
| PAC | 0.26% | 1.72% | 1.66% | 1.99% | 2.11% | 0 | 2 |
| UDM | 0.02% | 1.06% | 0.74% | 2.04% | 0.53% | 0 | 0 |
| ACDP | 0.35% | 1.40% | 0.70% | 1.57% | 0.79% | 0 | 1 |
| PAN_AFRICANIST_MOVEMENT | 0.00% | 0.32% | 0.23% | 0.25% | 0.13% | 0 | 0 |

## Buffalo City 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.53% | 59.22% | 59.86% | 59.70% | 57.63% | 60 | 60 |
| DA | 24.68% | 25.44% | 23.45% | 26.09% | 23.35% | 25 | 24 |
| EFF | 4.54% | 5.55% | 8.21% | 4.78% | 7.74% | 4 | 8 |
| AIC | 1.14% | 2.18% | 3.89% | 4.16% | 2.95% | 2 | 4 |
| UDM | 1.73% | 2.79% | 1.29% | 0.85% | 0.45% | 1 | 1 |
| COPE | 0.05% | 0.47% | 0.99% | 0.47% | 0.72% | 0 | 1 |
| PAC | 0.67% | 1.54% | 0.98% | 1.35% | 0.82% | 1 | 1 |
| ACDP | 0.20% | 0.66% | 0.55% | 0.77% | 0.56% | 0 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.60% | 0.96% | 0.32% | 0.82% | 0.27% | 1 | 0 |
| PAN_AFRICANIST_MOVEMENT | nan% | nan% | 0.20% | nan% | 0.04% | 0 | 0 |
| PEOPLES_ALLIANCE | 0.61% | 0.99% | 0.16% | 0.85% | 0.02% | 1 | 0 |
| UNITED_CONGRESS | 0.00% | 0.20% | 0.10% | 0.17% | 0.09% | 0 | 0 |

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 56.70% | 56.39% | 60.51% | 56.66% | 58.35% | 57 | 61 |
| DA | 20.80% | 21.83% | 19.49% | 22.70% | 19.55% | 21 | 20 |
| EFF | 11.62% | 12.59% | 12.37% | 12.41% | 11.76% | 12 | 13 |
| UDM | 0.32% | 0.86% | 1.10% | 1.75% | 0.82% | 1 | 1 |
| PAC | 0.33% | 1.19% | 1.05% | 1.22% | 0.83% | 0 | 1 |
| AIC | 0.67% | 1.72% | 0.97% | 0.42% | 0.45% | 1 | 1 |
| ATM | 0.36% | 0.97% | 0.89% | 0.86% | 0.93% | 0 | 1 |
| ACDP | 0.47% | 0.69% | 0.57% | 0.74% | 0.55% | 1 | 1 |
| VFPLUS | 0.10% | 0.44% | 0.52% | 0.39% | 0.51% | 0 | 1 |
| PA | 0.09% | 0.18% | 0.42% | 0.16% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.09% | 0.18% | 0.34% | 0.16% | 0.10% | 0 | 0 |
| COPE | 0.00% | 0.11% | 0.27% | 0.01% | 0.05% | 0 | 0 |