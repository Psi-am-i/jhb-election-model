# Historical performance — votes and seats, predicted against actual

24 city-years. Shares are citywide percentages; the model column is the median over draws.

## Headline

| city-year | council | list MAE | ward MAE | seat err (median) | medians sum to | seat err (coherent) | CRPS | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 260 | 5.09pp | 4.26pp | 55 | 245 | 62 | 41.2 | 52 | 60 | 50 |
| Johannesburg 2016 | 270 | 0.78pp | 1.27pp | 21 | 261 | 20 | 19.6 | 92 | 26 | 91 |
| Johannesburg 2021 | 270 | 6.25pp | 5.01pp | 96 | 250 | 88 | 70.2 | 134 | 126 | 125 |
| Tshwane 2011 | 210 | 6.55pp | 4.90pp | 45 | 197 | 58 | 32.5 | 40 | 56 | 39 |
| Tshwane 2016 | 214 | 2.37pp | 1.72pp | 18 | 206 | 22 | 13.7 | 70 | 10 | 70 |
| Tshwane 2021 | 214 | 1.62pp | 1.60pp | 33 | 199 | 34 | 27.5 | 80 | 60 | 77 |
| Ekurhuleni 2011 | 202 | 3.57pp | 2.49pp | 33 | 187 | 36 | 24.8 | 32 | 44 | 35 |
| Ekurhuleni 2016 | 224 | 1.32pp | 1.76pp | 18 | 214 | 18 | 16.5 | 80 | 22 | 76 |
| Ekurhuleni 2021 | 224 | 1.32pp | 1.26pp | 29 | 207 | 20 | 25.8 | 72 | 48 | 66 |
| eThekwini 2011 | 205 | 2.65pp | 1.98pp | 28 | 196 | 33 | 23.2 | 49 | 35 | 55 |
| eThekwini 2016 | 219 | 1.32pp | 2.81pp | 28 | 213 | 28 | 21.5 | 64 | 50 | 59 |
| eThekwini 2021 | 222 | 0.76pp | 1.00pp | 37 | 201 | 36 | 33.9 | 82 | 36 | 76 |
| Cape Town 2011 | 221 | 4.27pp | 3.70pp | 37 | 208 | 42 | 26.5 | 94 | 58 | 93 |
| Cape Town 2016 | 231 | 0.45pp | 0.94pp | 14 | 223 | 12 | 12.8 | 46 | 30 | 49 |
| Cape Town 2021 | 231 | 1.84pp | 2.06pp | 40 | 217 | 36 | 31.8 | 68 | 38 | 63 |
| Mangaung 2011 | 97 | 7.98pp | 8.10pp | 29 | 92 | 34 | 18.7 | 28 | 30 | 28 |
| Mangaung 2016 | 100 | 0.83pp | 1.48pp | 5 | 95 | 8 | 7.1 | 24 | 12 | 22 |
| Mangaung 2021 | 101 | 1.75pp | 1.10pp | 10 | 91 | 10 | 9.9 | 24 | 8 | 20 |
| Nelson Mandela Bay 2011 | 120 | 7.25pp | 6.80pp | 33 | 111 | 34 | 21.5 | 48 | 42 | 48 |
| Nelson Mandela Bay 2016 | 120 | 0.39pp | 0.28pp | 8 | 114 | 8 | 8.2 | 38 | 16 | 38 |
| Nelson Mandela Bay 2021 | 120 | 2.80pp | 2.96pp | 22 | 110 | 18 | 16.1 | 28 | 22 | 27 |
| Buffalo City 2011 | 100 | 7.13pp | 6.88pp | 31 | 89 | 30 | 19.4 | 28 | 30 | 27 |
| Buffalo City 2016 | 100 | 0.84pp | 2.56pp | 8 | 94 | 8 | 8.8 | 28 | 14 | 25 |
| Buffalo City 2021 | 100 | 3.48pp | 2.28pp | 11 | 93 | 12 | 8.3 | 14 | 12 | 15 |

### The margin is not evenly spread

| | city-years | seat err (coherent) | uniform-swing | margin | CRPS | uniform-swing CRPS | margin |
|---|---|---|---|---|---|---|---|
| Gauteng (JHB, TSH, EKU) | 9 | 358 | 452 | 21% | 271.8 | 452.0 | 40% |
| everywhere else | 15 | 349 | 433 | 19% | 267.6 | 433.0 | 38% |

**The headline margin is a Gauteng result.** Outside Gauteng the model is closer to parity with uniform swing on seats and loses at Mangaung. Quote the split, not the pool.

**Sign count against uniform swing: 16 wins, 5 losses, 3 ties across 24 city-years** — 2011: 4W 3L 1T; 2016: 7W 1L 0T; 2021: 5W 1L 2T. The sign REPLICATES across cycles, which is what the amended bar's Key 1 asks of any candidate and is the strongest claim this panel supports. Metros inside one cycle share a national swing, so 24 city-years is 3 effective clusters, not 24 — never quote a p-value off the pooled count.

**Read the two seat-error columns together.** *seat err (median)* uses the per-party marginal median, which is what the per-party tables below show and which **does not sum to a council** — the *medians sum to* column says by how much. *seat err (coherent)* apportions the mean seat vector by largest remainder, so it IS a chamber and is the only one comparable to the baselines, which allocate per draw and sum exactly. Lower is better throughout.


## The arrival channel, scored without the label

The headline CRPS above is scored after the model's generic `ENTRANT` column is renamed onto the largest party that actually arrived — a label chosen with the result in hand, which no baseline gets. This table does not use it. **PIT above 0.5 means the model forecast too little.**

| city-year | arrived | actual mass | forecast mass | actual seats | forecast seats | mass PIT | seats PIT |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 10 | 1.64% | 1.51% | 4 | 3.8 | 0.728 | 0.728 |
| Johannesburg 2016 | 13 | 2.29% | 1.48% | 5 | 4.1 | 0.748 | 0.737 |
| Johannesburg 2021 | 32 | 19.99% | 9.12% | 46 | 22.0 | 0.980 | 0.976 |
| Tshwane 2011 | 5 | 0.36% | 1.46% | 0 | 3.0 | 0.741 | 0.370 |
| Tshwane 2016 | 7 | 0.31% | 1.65% | 0 | 3.7 | 0.726 | 0.363 |
| Tshwane 2021 | 25 | 11.38% | 9.27% | 21 | 18.5 | 0.720 | 0.667 |
| Ekurhuleni 2011 | 12 | 2.56% | 1.41% | 5 | 2.8 | 0.766 | 0.766 |
| Ekurhuleni 2016 | 12 | 2.06% | 1.41% | 5 | 3.3 | 0.758 | 0.758 |
| Ekurhuleni 2021 | 20 | 9.14% | 9.44% | 17 | 20.5 | 0.553 | 0.417 |
| eThekwini 2011 | 8 | 5.61% | 1.41% | 11 | 2.9 | 0.875 | 0.868 |
| eThekwini 2016 | 14 | 3.25% | 1.21% | 6 | 2.7 | 0.814 | 0.801 |
| eThekwini 2021 | 29 | 7.21% | 9.66% | 15 | 20.6 | 0.348 | 0.339 |
| Cape Town 2011 | 16 | 1.02% | 1.50% | 1 | 3.3 | 0.747 | 0.747 |
| Cape Town 2016 | 20 | 1.43% | 1.59% | 2 | 3.8 | 0.738 | 0.738 |
| Cape Town 2021 | 31 | 8.00% | 3.18% | 18 | 6.9 | 0.922 | 0.922 |
| Mangaung 2011 | 2 | 0.28% | 1.25% | 0 | 1.1 | 0.782 | 0.391 |
| Mangaung 2016 | 6 | 4.74% | 1.40% | 3 | 1.3 | 0.855 | 0.794 |
| Mangaung 2021 | 11 | 1.53% | 4.25% | 0 | 3.9 | 0.135 | 0.040 |
| Nelson Mandela Bay 2011 | 4 | 0.41% | 1.31% | 0 | 1.5 | 0.775 | 0.388 |
| Nelson Mandela Bay 2016 | 8 | 1.59% | 1.40% | 2 | 1.7 | 0.755 | 0.756 |
| Nelson Mandela Bay 2021 | 15 | 7.02% | 3.65% | 8 | 4.0 | 0.824 | 0.820 |
| Buffalo City 2011 | 0 | 0.00% | 1.32% | 0 | 1.2 | 0.000 | 0.384 |
| Buffalo City 2016 | 3 | 0.68% | 1.45% | 0 | 1.4 | 0.748 | 0.374 |
| Buffalo City 2021 | 12 | 1.75% | 3.90% | 0 | 2.9 | 0.262 | 0.099 |
| **panel mean** | | | | | | **0.679** | **0.594** |

Mass PIT is above 0.5 at **20 of 24** city-years. A panel mean well above 0.5 on both columns is the model systematically under-forecasting how much of the ballot goes to parties arriving from nothing — read it next to the mid-ballot calibration below, which is the same leak seen through a different instrument.


## Where the vote error sits on the ballot

**Two columns per band, and they answer different questions.** *signed* is the net error in points — positive means the model gave that band MORE than it won — and it is what shows one band eating another. *abs* sums the per-party error without cancelling, and it is the only one of the two that is a measure of error at all. Where they diverge, the band is wrong about individual parties in both directions at once: Johannesburg 2021's ranks 1-3 are the case that motivated the column (ANC and DA over, ActionSA far under). The bands are by actual rank.

| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | 13+ signed | 13+ abs | phantom | seats at stake in 4-12 |
|---|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | -10.32pp | 12.43pp | **+10.37pp** | 12.05pp | -0.05pp | 0.54pp | 0.00pp (0) | 12 |
| Johannesburg 2016 | -0.37pp | 3.29pp | **-0.31pp** | 1.57pp | +0.67pp | 1.37pp | 0.00pp (0) | 15 |
| Johannesburg 2021 | +0.10pp | 24.53pp | **-1.79pp** | 9.28pp | +0.36pp | 1.61pp | 1.33pp (3) | 58 |
| Tshwane 2011 | -10.59pp | 17.50pp | **+8.50pp** | 9.44pp | +0.64pp | 0.95pp | 1.46pp (1) | 6 |
| Tshwane 2016 | -2.92pp | 6.93pp | **+0.75pp** | 1.09pp | +0.41pp | 0.85pp | 1.76pp (2) | 7 |
| Tshwane 2021 | +5.73pp | 5.73pp | **-7.66pp** | 7.74pp | +0.24pp | 1.57pp | 1.68pp (5) | 44 |
| Ekurhuleni 2011 | -6.29pp | 8.49pp | **+6.92pp** | 9.25pp | -0.63pp | 0.76pp | 0.00pp (0) | 13 |
| Ekurhuleni 2016 | -0.10pp | 4.28pp | **+0.11pp** | 1.45pp | -0.01pp | 0.81pp | 0.00pp (0) | 12 |
| Ekurhuleni 2021 | +3.29pp | 3.29pp | **-3.98pp** | 6.11pp | +0.62pp | 1.48pp | 0.07pp (1) | 38 |
| eThekwini 2011 | -3.24pp | 5.48pp | **+3.37pp** | 11.57pp | -0.13pp | 0.38pp | 0.00pp (0) | 24 |
| eThekwini 2016 | -0.59pp | 3.78pp | **+1.12pp** | 5.41pp | -0.53pp | 1.28pp | 0.00pp (0) | 18 |
| eThekwini 2021 | +0.42pp | 1.55pp | **-0.51pp** | 8.61pp | -0.07pp | 4.26pp | 0.16pp (3) | 31 |
| Cape Town 2011 | -3.34pp | 16.00pp | **+3.53pp** | 4.52pp | -0.19pp | 1.19pp | 0.00pp (0) | 10 |
| Cape Town 2016 | +0.22pp | 1.54pp | **+0.41pp** | 2.48pp | -0.62pp | 1.23pp | 0.00pp (0) | 12 |
| Cape Town 2021 | +6.06pp | 6.06pp | **-5.89pp** | 6.05pp | -0.31pp | 2.01pp | 0.14pp (3) | 38 |
| Mangaung 2011 | -4.88pp | 26.35pp | **+3.63pp** | 4.69pp | +0.00pp | 0.00pp | 1.25pp (1) | 3 |
| Mangaung 2016 | +1.89pp | 2.48pp | **-1.99pp** | 4.38pp | +0.10pp | 0.47pp | 0.00pp (0) | 6 |
| Mangaung 2021 | -1.98pp | 4.00pp | **-1.11pp** | 3.40pp | +1.76pp | 2.42pp | 1.33pp (1) | 12 |
| Nelson Mandela Bay 2011 | -2.22pp | 26.40pp | **+0.96pp** | 2.34pp | -0.05pp | 0.05pp | 1.31pp (1) | 3 |
| Nelson Mandela Bay 2016 | -0.81pp | 1.01pp | **+0.50pp** | 3.15pp | +0.31pp | 0.81pp | 0.00pp (0) | 7 |
| Nelson Mandela Bay 2021 | +4.09pp | 7.97pp | **-4.84pp** | 5.78pp | +0.75pp | 1.52pp | 0.00pp (0) | 15 |
| Buffalo City 2011 | +0.08pp | 26.45pp | **-1.41pp** | 4.37pp | +0.00pp | 0.00pp | 1.32pp (1) | 5 |
| Buffalo City 2016 | -0.58pp | 4.33pp | **-0.86pp** | 5.07pp | +0.00pp | 0.00pp | 1.45pp (1) | 8 |
| Buffalo City 2021 | -2.72pp | 7.55pp | **+0.03pp** | 1.97pp | +1.03pp | 1.28pp | 1.66pp (2) | 6 |

**Totals across 24 city-years:** ranks 1-3 -29.09pp signed / 227.43pp absolute, ranks 4-12 +9.85pp / 131.78pp, ranks 13+ +4.31pp / 26.83pp.

**Phantom mass: 14.93pp** on parties that did not stand at all — including the generic `ENTRANT` column where no party arrived. The bands iterate the parties that DID stand, so none of them can see it; it is exactly why the three signed bands sum to -14.93pp rather than to zero.


## Ward winners — the geography key

**`seat_abs_err_coherent` cannot see geography and this can.** `solve_and_predict` forces every party's citywide share onto the share the draw drew, and both ballots are `weight @ pred` against those same targets, so `dev`, `gamma`, pool composition and the whole VD layer reach the seat score ONLY through an overhang trigger. Any change to those is judged here, or it is judged by an instrument that is blind to it. Hit rate is the modal call; Brier (multi-category, 0 to 2) is the proper score and is what a change in CONFIDENCE moves. **Read the model against the baselines in its own row** — safe wards are called correctly by anything at all.

| city-year | wards | model called | hit rate | Brier MC | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|---|---|---|
| Johannesburg 2011 | 130 | 126 | 96.9% | 0.047 | 92.3% | 93.8% | 92.3% |
| Johannesburg 2016 | 135 | 134 | 99.3% | 0.018 | 94.8% | 97.8% | 94.8% |
| Johannesburg 2021 | 135 | 127 | 94.1% | 0.092 | 93.3% | 93.3% | 93.3% |
| Tshwane 2011 | 105 (only 99 matched) | 98 | 93.3% | 0.080 | 98.1% | 98.1% | 98.1% |
| Tshwane 2016 | 107 | 105 | 98.1% | 0.041 | 98.1% | 98.1% | 98.1% |
| Tshwane 2021 | 107 | 104 | 97.2% | 0.038 | 98.1% | 98.1% | 98.1% |
| Ekurhuleni 2011 | 101 | 97 | 96.0% | 0.043 | 94.1% | 96.0% | 95.0% |
| Ekurhuleni 2016 | 112 | 111 | 99.1% | 0.027 | 97.3% | 99.1% | 97.3% |
| Ekurhuleni 2021 | 112 | 107 | 95.5% | 0.071 | 95.5% | 94.6% | 95.5% |
| eThekwini 2011 | 103 | 97 | 94.2% | 0.100 | 93.2% | 92.2% | 93.2% |
| eThekwini 2016 | 110 (only 109 matched) | 97 | 88.2% | 0.199 | 82.7% | 85.5% | 83.6% |
| eThekwini 2021 | 111 | 110 | 99.1% | 0.036 | 96.4% | 98.2% | 96.4% |
| Cape Town 2011 | 111 | 111 | 100.0% | 0.012 | 85.6% | 97.3% | 85.6% |
| Cape Town 2016 | 116 | 116 | 100.0% | 0.006 | 100.0% | 100.0% | 100.0% |
| Cape Town 2021 | 116 | 115 | 99.1% | 0.014 | 99.1% | 99.1% | 99.1% |
| Mangaung 2011 | 49 | 49 | 100.0% | 0.025 | 98.0% | 95.9% | 98.0% |
| Mangaung 2016 | 50 (only 49 matched) | 48 | 96.0% | 0.035 | 96.0% | 98.0% | 96.0% |
| Mangaung 2021 | 51 | 50 | 98.0% | 0.037 | 98.0% | 96.1% | 98.0% |
| Nelson Mandela Bay 2011 | 60 | 59 | 98.3% | 0.022 | 83.3% | 96.7% | 83.3% |
| Nelson Mandela Bay 2016 | 60 | 57 | 95.0% | 0.067 | 96.7% | 96.7% | 96.7% |
| Nelson Mandela Bay 2021 | 60 | 57 | 95.0% | 0.051 | 95.0% | 95.0% | 95.0% |
| Buffalo City 2011 | 50 | 49 | 98.0% | 0.047 | 94.0% | 98.0% | 94.0% |
| Buffalo City 2016 | 50 | 48 | 96.0% | 0.085 | 100.0% | 96.0% | 100.0% |
| Buffalo City 2021 | 50 | 48 | 96.0% | 0.073 | 96.0% | 96.0% | 96.0% |

**Pooled over 24 city-years: 2120/2191 = 96.8% of ward contests called correctly, against last-lge 94.7%, uniform-swing 96.2%, prior-lge-noise 94.8%. A margin over the baselines that is smaller than the seat margin is the model's geography adding less than its citywide machinery, which is a statement the seat columns cannot make.

## Calibration — pooled across every city-year, and split by rank

**Pool over city-years; never over rank bands.** Seven to fifteen scored columns per city-year cannot distinguish a 50% interval from an 80% one, so the city-years must be pooled to say anything at all. But the rank bands must NOT be: this model is biased in opposite directions at the top of the ballot and in the middle, and a mean over both lands between them and reports a model that does not exist. The pooled table comes first because it is the familiar one; **the split table below it is the one to read.**

A mean PIT above 0.50 means the truth keeps landing high in the forecast distribution — the model forecast too LOW for those columns. Below 0.50 means it forecast too HIGH. Read the sign per band; the pooled sign is an artefact of how the two bands happen to be sized.

| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |
|---|---|---|---|---|---|---|
| reference (INPUT-selected — fixed; the only one to compare on) | 514 | 79% | 92% | 94% | 0.585 | 69.8 (16.92) |
| claimed by the model (forecast-selected — neutral for ONE model) | 149 | 76% | 90% | 95% | 0.546 | 46.1 (16.92) |
| won a seat (outcome-selected — INFLATED by construction) | 269 | 58% | 83% | 88% | 0.687 | 129.1 (16.92) |
| every scored column (MIXED: outcome-selected + neutral, diluted) | 528 | 79% | 91% | 94% | 0.569 | 48.4 (16.92) |

* **reference** (n=514) PIT histogram [33, 26, 30, 42, 40, 70, 62, 85, 69, 57] — approximately flat
* **claimed** (n=149) PIT histogram [11, 6, 7, 11, 17, 33, 18, 23, 18, 5] — hump-shaped: the truth lands mid-distribution too often — over-dispersed, the model is hedging
* **seat_holders** (n=269) PIT histogram [10, 4, 7, 11, 17, 35, 31, 54, 46, 54] — approximately flat; mean PIT 0.69 — the model under-predicts seats
* **all** (n=528) PIT histogram [38, 30, 32, 50, 44, 68, 59, 80, 69, 58] — approximately flat

The verdict at the end of each line is `score.pit_histogram`'s shape heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT AS A WIDTH VERDICT — it is not reliable as one, and on this model it is demonstrably wrong.** The heuristic tests the mass in the two END bins against flat, so a histogram that is monotone increasing scores as U-shaped: a shifted forecast piles mass in the top bin and gets called under-dispersed. On the ranks 4-12 columns it reads the histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, monotone, nothing at the bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling the pooled population *"hump-shaped — over-dispersed, hedging"*. The two verdicts contradict each other and the band one contradicts the level-free width table below, which is the one that is right. `score.py` is not changed here — the heuristic is fine for its own purpose and what is wrong is quoting it about width. **The χ² column is the test of uniformity; the level-free dispersion table is the test of width.**

The three populations differ by which columns they count, and the difference is itself the finding. `claimed` selects on the FORECAST, which leaves PIT uniform under calibration, so it is the honest test and the only one to quote. `seat_holders` selects on the OUTCOME: zero is the bottom of the support, so winning a seat selects over-performers and the population reads high even for a perfect forecaster — it is quoted because it is the population a reader assumes, not because it is neutral. `all` was documented as neutral and **is not**: `score.seat_matrix` admits a column when `truth[i] > 0 or samples[:, i].max() > 0`, and the first clause lets a party in because it WON, which is outcome selection. Five of its columns across the nine city-years carry PIT exactly 1.0 — parties the model gave zero seats in every draw, present only because they won a seat. It is a mixture of an outcome-selected set and a neutral one, and the neutral part is itself diluted by ~200 parties correctly at zero on both sides, each a free interval hit and a near-uniform PIT. Two errors pushing opposite ways: `all` tests nothing.

### Split by actual PR rank — `claimed` columns

**The pooled row above is the average of the rows below, and they have opposite signs.** This is the same fault as a signed error sum inside a rank band, one level up: an average over subsets biased in opposite directions reports the midpoint and calls it centred.

| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | 50% (PIT) | 80% (PIT) | 90% (PIT) |
|---|---|---|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.538 | [0.505, 0.568] | 72% [57–86] | 90% [85–96] | 96% [92–100] | 69% [56–83] | 90% [85–96] | 93% [88–99] |
| ranks 4-12 | 73 | 0.566 | [0.490, 0.633] | 78% [69–88] | 89% [83–95] | 93% [88–98] | 63% [53–74] | 89% [83–95] | 92% [87–97] |
| ranks 13+ | 4 | 0.308 | [0.118, 0.499] | 100% [100–100] | 100% [100–100] | 100% [100–100] | 50% [0–100] | 75% [25–100] | 100% [100–100] |

The CI resamples CITY-YEARS, not columns: columns inside one city-year share a turnout draw, a pool structure and a national swing, so a column bootstrap would give an interval far too tight. 20,000 replicates, fixed seed.

**The two coverage triples are the same question asked twice.** The first is `score.coverage` — the empirical quantile interval, which on integer seats must include whole endpoints and therefore over-covers. The second is the fraction of columns whose randomised PIT falls in the central interval, which carries no such inflation. They agree at ranks 1-3, where parties hold tens of seats and one endpoint is worth nothing, and diverge at ranks 4-12, where parties hold one to ten and an endpoint is a large part of the interval. **Read the PIT columns whenever the two are compared** — but neither triple is the width verdict on its own; that is the table below.

**Read all three coverage levels together, never one of them.** A forecast whose intervals are too NARROW under-covers at EVERY level — that is what narrow means. A forecast that is merely SHIFTED loses coverage at the 50% level first and hardest, because it has vacated the middle of its own interval, and its 80% and 90% coverages fall too. Only intervals that are too WIDE push the 80% and 90% coverages above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 is shifted and too wide, and reading its 50% column alone gives exactly the opposite instruction. **That mistake has been made twice on this report, in opposite directions, and rule 8 of `ITERATING.md` carried each of them.** The width verdict belongs to the level-free table above; the coverage rows corroborate it or they do not.

The rank-band vote table further up and the mean-PIT column here are the same LEVEL finding measured twice — top three over, middle short. Because shares sum to one that gap is a zero-sum transfer, not two independent faults, so a level fix has to move mass rather than add it.

### Is it the right WIDTH? — the level divided out

**This table, not the coverage rows, is the width verdict.** Coverage moves with the level as well as the width: a forecast pushed off centre vacates the middle of its own interval, so its 50% coverage falls however wide it is. Read at one level, coverage says 'too narrow' for a forecast that is merely shifted. The columns below divide the level out. **1.00 is right; below 1.00 the intervals are too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor they are out by.

| band | n | probit-SD (level-free) | exact SD of z | standardised bias (mean z) | PIT variance vs 1/12 |
|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.802 | 0.786 | +0.097 | 0.0514 vs 0.0833 |
| ranks 4-12 | 73 | 0.909 | 0.837 | +0.009 | 0.0596 vs 0.0833 |
| ranks 13+ | 4 | 0.710 | 0.520 | -0.443 | 0.0508 vs 0.0833 |

#### The same question on the FIXED population — and it disagrees

**The `n` here is the number of columns the width figure was actually computed on** — columns with a defined `z`. A column whose draws are all identical has no scale, so it carries a PIT and no `z`; the pooled tables above count PIT values and their `n` is larger.

| band | `claimed` n(z) | `claimed` SD of z | `reference` n(z) | `reference` SD of z | `reference` mean z | `reference` probit-SD |
|---|---|---|---|---|---|---|
| ranks 1-3 | 72 | 0.786 | 72 | 0.786 | +0.097 | **0.802** |
| ranks 4-12 | 73 | 0.837 | 168 | 1.504 | +0.297 | **1.335** |
| ranks 13+ | 4 | 0.520 | 148 | 0.361 | -0.144 | **1.082** |

**Read the last column, not the `SD of z` column, on ranks 13+.** `sd(z)` is exact under a level shift and **meaningless on a near-degenerate discrete column**: where the forecast is roughly Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly, a function of the forecast probability with no room to spread. On the 96 ranks-13+ columns whose truth is zero, observed `z` correlates with that expression at **+0.93**. probit-SD comes from the randomised PIT, which is uniform under calibration whatever the support, and is the one to read there — at the cost of being attenuated by a level shift, so it is a LOWER BOUND wherever `mean z` is far from zero. Neither statistic is right everywhere; the pair is. MODEL-LOG §1.58.

**Ranks 1-3 are the same columns in both populations** — the top three are always claimed — so that row is a consistency check and the two `SD of z` numbers should agree exactly. It is also the band that is genuinely too WIDE and the band that responds to `dirichlet_scale`.

**Ranks 4-12 cannot be described by one width, and that is the finding.** On the same columns `sd(z)` says far too narrow, `IQR-sd` says too wide, and probit-SD disagrees with both — because the error distribution is a narrow shifted bulk with two enormous outliers, Cape Town's Cape Coloured Congress and Johannesburg's PA, both of which `claimed` excludes by construction. A distribution that reads differently depending which moment you take is mis-SHAPED, not mis-scaled, and no scalar fixes it.

⛔ **AND THE SPREAD AT 4-12 IS TWO COLUMNS.** Those two carry ~70% of the band's total squared z; dropping them takes `sd(z)` to about 1.0. Quote the leave-the-largest-out figure beside the headline or the headline is two observations, not a width. §1.56, §1.58, §1.131.

**`probit-SD` is the one to quote when only a PIT is available.** It is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per column, centred, which is invariant to a shift by construction; it reads `—` on an artefact written before `calibration_columns` stored the `z` column, and it is the number to prefer when it is there. The standardised bias is the LEVEL, kept in its own column so that it can never be read as width again.

**The last column is printed to show it failing.** PIT variance against a nominal 1/12 has been proposed on this project as "shift-invariant, therefore a clean width statistic". **It is neither.** A PIT lives on [0, 1]; move the forecast off centre and its mass piles against a boundary and the variance falls whatever the width is. On the suite's fixture whose width is exactly right (`tests/test_calibration_report.py::_shift_scale_results`) it reads 0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a 3.5× under-dispersion, which is the wrong diagnosis with the wrong remedy. Do not quote it as a width statistic; it is here so that nobody rediscovers it as one.

Per city-year, for provenance only — **every n below is too small to read, and none of these rows is evidence of anything on its own.**

| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |
|---|---|---|---|---|---|
| Johannesburg 2011 | 6 | 67% | 67% | 83% | 0.508 |
| Johannesburg 2016 | 8 | 100% | 100% | 100% | 0.527 |
| Johannesburg 2021 | 9 | 33% | 78% | 78% | 0.636 |
| Tshwane 2011 | 5 | 40% | 60% | 80% | 0.479 |
| Tshwane 2016 | 6 | 100% | 100% | 100% | 0.487 |
| Tshwane 2021 | 7 | 71% | 100% | 100% | 0.623 |
| Ekurhuleni 2011 | 6 | 67% | 83% | 100% | 0.441 |
| Ekurhuleni 2016 | 6 | 100% | 100% | 100% | 0.549 |
| Ekurhuleni 2021 | 9 | 89% | 89% | 89% | 0.689 |
| eThekwini 2011 | 6 | 100% | 100% | 100% | 0.451 |
| eThekwini 2016 | 8 | 62% | 88% | 88% | 0.503 |
| eThekwini 2021 | 9 | 78% | 89% | 100% | 0.549 |
| Cape Town 2011 | 6 | 67% | 83% | 83% | 0.538 |
| Cape Town 2016 | 6 | 83% | 100% | 100% | 0.615 |
| Cape Town 2021 | 7 | 71% | 100% | 100% | 0.531 |
| Mangaung 2011 | 4 | 0% | 50% | 100% | 0.451 |
| Mangaung 2016 | 4 | 100% | 100% | 100% | 0.454 |
| Mangaung 2021 | 6 | 100% | 100% | 100% | 0.603 |
| Nelson Mandela Bay 2011 | 3 | 0% | 67% | 100% | 0.564 |
| Nelson Mandela Bay 2016 | 7 | 100% | 100% | 100% | 0.547 |
| Nelson Mandela Bay 2021 | 6 | 83% | 100% | 100% | 0.501 |
| Buffalo City 2011 | 3 | 33% | 67% | 67% | 0.536 |
| Buffalo City 2016 | 6 | 100% | 100% | 100% | 0.588 |
| Buffalo City 2021 | 6 | 100% | 100% | 100% | 0.550 |


## Johannesburg 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 55.83% | 55.09% | 59.29% | 55.16% | 57.82% | 145 | 153 |
| DA | 27.47% | 27.18% | 34.35% | 27.49% | 34.90% | 72 | 90 |
| IFP | 1.31% | 2.66% | 1.61% | 2.22% | 1.66% | 3 | 4 |
| COPE | 9.03% | 10.14% | 1.11% | 9.69% | 1.19% | 23 | 3 |
| NFP | 0.00% | 1.51% | 0.82% | 1.44% | 0.74% | 0 | 2 |
| APC | 0.00% | 0.21% | 0.53% | 0.20% | 0.39% | 0 | 1 |
| ACDP | 0.31% | 0.79% | 0.40% | 0.77% | 0.44% | 1 | 1 |
| PAC | 0.00% | 0.63% | 0.35% | 0.87% | 0.43% | 0 | 1 |
| ALJAMAAH | nan% | nan% | 0.27% | nan% | 0.19% | 0 | 1 |
| OKM | nan% | nan% | 0.25% | nan% | 0.15% | 0 | 1 |
| VFPLUS | 0.27% | 0.91% | 0.23% | 0.92% | 0.27% | 1 | 1 |
| UDM | 0.01% | 0.36% | 0.22% | 0.72% | 0.25% | 0 | 1 |

## Johannesburg 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.13% | 45.07% | 44.92% | 44.35% | 44.09% | 121 | 121 |
| DA | 39.63% | 39.78% | 38.48% | 40.75% | 38.34% | 109 | 104 |
| EFF | 8.73% | 9.10% | 10.93% | 9.44% | 11.24% | 24 | 30 |
| IFP | 1.11% | 1.33% | 1.71% | 1.22% | 1.74% | 3 | 5 |
| AIC | 0.00% | 1.48% | 1.62% | 1.54% | 1.40% | 0 | 4 |
| ACDP | 0.33% | 0.51% | 0.31% | 0.54% | 0.28% | 1 | 1 |
| VFPLUS | 0.21% | 0.41% | 0.31% | 0.50% | 0.34% | 1 | 1 |
| ALJAMAAH | nan% | nan% | 0.31% | nan% | 0.22% | 0 | 1 |
| UDM | 0.18% | 0.36% | 0.25% | 0.41% | 0.28% | 1 | 1 |
| COPE | 0.06% | 0.20% | 0.21% | 0.12% | 0.15% | 0 | 1 |
| PA | 0.00% | 0.08% | 0.17% | 0.08% | 0.13% | 0 | 1 |
| PAC | 0.20% | 0.39% | 0.17% | 0.09% | 0.09% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Johannesburg 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 38.53% | 38.43% | 33.22% | 38.52% | 33.97% | 104 | 91 |
| DA | 32.27% | 32.57% | 25.45% | 33.13% | 26.83% | 88 | 71 |
| ASA | 5.55% | 5.90% | 18.12% | 4.88% | 13.98% | 14 | 44 |
| EFF | 13.43% | 13.79% | 10.11% | 14.48% | 11.14% | 37 | 29 |
| PA | 0.03% | 0.09% | 2.96% | 0.16% | 2.91% | 0 | 8 |
| IFP | 0.74% | 1.39% | 2.36% | 1.80% | 2.36% | 2 | 7 |
| VFPLUS | 0.71% | 0.94% | 1.33% | 1.03% | 1.35% | 2 | 4 |
| ACDP | 0.30% | 0.59% | 1.03% | 0.60% | 1.08% | 1 | 3 |
| ALJAMAAH | 0.21% | 0.29% | 0.83% | 0.27% | 1.08% | 1 | 3 |
| AIC | 0.24% | 0.73% | 0.69% | 0.37% | 0.50% | 1 | 2 |
| AHC | 0.01% | 0.09% | 0.43% | 0.07% | 0.47% | 0 | 1 |
| GOOD | 0.09% | 0.35% | 0.33% | 0.29% | 0.40% | 0 | 1 |

**Missed entirely:** PA — won seats, median zero.

## Tshwane 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 52.26% | 50.92% | 56.46% | 50.71% | 54.18% | 110 | 118 |
| DA | 29.94% | 30.24% | 38.74% | 31.21% | 38.56% | 64 | 82 |
| VFPLUS | 4.17% | 5.04% | 1.59% | 5.29% | 1.73% | 9 | 4 |
| COPE | 6.52% | 7.81% | 0.89% | 7.34% | 0.92% | 13 | 2 |
| ACDP | 0.49% | 1.37% | 0.59% | 1.49% | 0.67% | 1 | 1 |
| APC | 0.00% | 0.19% | 0.46% | 0.18% | 0.35% | 0 | 1 |
| PAC | 0.01% | 0.46% | 0.25% | 0.57% | 0.28% | 0 | 1 |
| AZAPO | 0.00% | 0.42% | 0.18% | 0.47% | 0.21% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.06% | 0.83% | 0.15% | 0.32% | 0.12% | 0 | 0 |
| IFP | 0.01% | 0.25% | 0.12% | 0.21% | 0.13% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.11% | nan% | 0.13% | 0 | 0 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.09% | nan% | 0.05% | 0 | 0 |

## Tshwane 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 39.75% | 40.07% | 43.10% | 40.64% | 43.20% | 86 | 93 |
| ANC | 43.51% | 43.48% | 41.48% | 42.15% | 41.02% | 92 | 89 |
| EFF | 9.46% | 9.74% | 11.64% | 10.44% | 11.62% | 21 | 25 |
| VFPLUS | 2.10% | 2.27% | 1.97% | 2.51% | 2.02% | 5 | 4 |
| ACDP | 0.43% | 0.66% | 0.47% | 0.77% | 0.52% | 1 | 1 |
| APC | 0.18% | 0.42% | 0.24% | 0.07% | 0.05% | 0 | 0 |
| COPE | 0.03% | 0.19% | 0.22% | 0.20% | 0.27% | 0 | 1 |
| PAC | 0.10% | 0.34% | 0.14% | 0.37% | 0.20% | 0 | 1 |
| UDM | 0.02% | 0.18% | 0.13% | 0.22% | 0.10% | 0 | 0 |
| IFP | 0.00% | 0.10% | 0.10% | 0.02% | 0.02% | 0 | 0 |
| AFRICAN_MANDATE_CONGRESS | nan% | nan% | 0.09% | nan% | 0.06% | 0 | 0 |
| PA | 0.00% | 0.04% | 0.09% | 0.05% | 0.05% | 0 | 0 |

## Tshwane 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 36.31% | 36.13% | 34.84% | 36.27% | 34.42% | 78 | 75 |
| DA | 32.18% | 32.47% | 31.77% | 32.71% | 32.29% | 69 | 69 |
| EFF | 13.46% | 14.17% | 10.43% | 14.23% | 10.94% | 29 | 23 |
| ASA | 5.25% | 5.87% | 9.28% | 5.46% | 7.99% | 11 | 19 |
| VFPLUS | 4.47% | 4.78% | 7.79% | 4.92% | 7.96% | 10 | 17 |
| ACDP | 0.36% | 0.76% | 0.91% | 0.83% | 0.93% | 1 | 2 |
| AIC | 0.28% | 0.62% | 0.81% | 0.58% | 0.38% | 1 | 1 |
| DOP | 0.03% | 0.11% | 0.49% | 0.10% | 0.58% | 0 | 1 |
| PA | 0.01% | 0.06% | 0.48% | 0.12% | 0.52% | 0 | 1 |
| PAC | 0.00% | 0.25% | 0.21% | 0.24% | 0.18% | 0 | 1 |
| IFP | 0.00% | 0.14% | 0.21% | 0.21% | 0.09% | 0 | 1 |
| COPE | 0.00% | 0.12% | 0.19% | 0.14% | 0.20% | 0 | 1 |

## Ekurhuleni 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.74% | 58.29% | 62.17% | 58.99% | 61.08% | 121 | 125 |
| DA | 25.68% | 26.62% | 30.13% | 26.74% | 30.46% | 52 | 62 |
| IFP | 0.85% | 2.26% | 1.16% | 1.44% | 1.04% | 1 | 2 |
| NFP | 0.00% | 1.41% | 1.13% | 1.33% | 1.19% | 0 | 3 |
| COPE | 5.24% | 6.94% | 1.09% | 6.55% | 0.79% | 10 | 2 |
| APC | 0.00% | 0.25% | 0.68% | 0.24% | 0.54% | 0 | 1 |
| PAC | 0.04% | 0.72% | 0.61% | 0.73% | 0.75% | 0 | 2 |
| ACDP | 0.46% | 1.04% | 0.59% | 1.25% | 0.67% | 1 | 1 |
| VFPLUS | 1.04% | 1.84% | 0.51% | 1.74% | 0.59% | 2 | 1 |
| UDM | 0.00% | 0.48% | 0.42% | 0.88% | 0.51% | 0 | 1 |
| DISPLACEES_RATE_PAYERS_ASSOCIATION | nan% | nan% | 0.41% | nan% | 0.48% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | nan% | nan% | 0.32% | nan% | 0.78% | 0 | 1 |

**Missed entirely:** NFP — won seats, median zero.

## Ekurhuleni 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 47.80% | 47.91% | 48.84% | 46.56% | 48.44% | 106 | 109 |
| DA | 35.79% | 36.22% | 34.13% | 36.52% | 34.17% | 81 | 77 |
| EFF | 9.57% | 9.84% | 11.10% | 11.00% | 11.35% | 23 | 25 |
| AIC | 0.00% | 1.41% | 1.65% | 1.57% | 1.63% | 0 | 4 |
| IFP | 0.57% | 0.93% | 1.04% | 1.14% | 0.99% | 1 | 2 |
| VFPLUS | 0.70% | 0.93% | 0.90% | 1.09% | 0.89% | 2 | 2 |
| ACDP | 0.36% | 0.66% | 0.42% | 0.80% | 0.43% | 1 | 1 |
| PAC | 0.22% | 0.54% | 0.42% | 0.25% | 0.43% | 0 | 1 |
| COPE | 0.02% | 0.20% | 0.28% | 0.21% | 0.25% | 0 | 1 |
| PA | 0.00% | 0.04% | 0.28% | 0.04% | 0.25% | 0 | 1 |
| APC | 0.26% | 0.58% | 0.27% | 0.15% | 0.06% | 0 | 0 |
| UDM | 0.09% | 0.30% | 0.23% | 0.16% | 0.16% | 0 | 0 |

**Missed entirely:** AIC — won seats, median zero.

## Ekurhuleni 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 41.29% | 40.95% | 38.34% | 40.71% | 38.03% | 92 | 86 |
| DA | 28.20% | 28.70% | 28.37% | 28.53% | 29.07% | 63 | 65 |
| EFF | 13.13% | 13.62% | 13.27% | 13.83% | 13.87% | 30 | 31 |
| ASA | 5.41% | 6.05% | 7.36% | 5.95% | 5.84% | 12 | 15 |
| VFPLUS | 2.46% | 2.75% | 3.48% | 2.70% | 3.18% | 6 | 8 |
| PA | 0.14% | 0.20% | 1.87% | 0.39% | 1.89% | 1 | 4 |
| IFP | 0.46% | 1.10% | 1.47% | 0.97% | 1.24% | 1 | 3 |
| AIC | 0.24% | 0.90% | 1.36% | 1.02% | 1.22% | 1 | 3 |
| ACDP | 0.23% | 0.66% | 0.86% | 0.69% | 0.82% | 1 | 2 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.05% | 0.15% | 0.45% | 0.15% | 0.44% | 0 | 1 |
| PAC | 0.02% | 0.47% | 0.43% | 0.54% | 0.31% | 0 | 1 |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.00% | 1.38% | 0.36% | 1.36% | 0.78% | 0 | 1 |

## eThekwini 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.81% | 58.75% | 62.02% | 61.47% | 60.11% | 125 | 126 |
| DA | 20.34% | 20.72% | 21.81% | 16.79% | 20.21% | 38 | 43 |
| MINORITY_FRONT | 5.90% | 6.06% | 4.94% | 6.57% | 5.68% | 13 | 11 |
| NFP | 0.00% | 1.41% | 4.48% | 1.44% | 4.92% | 0 | 10 |
| IFP | 6.99% | 8.44% | 3.96% | 8.91% | 4.30% | 15 | 9 |
| ACDP | 0.76% | 1.31% | 0.67% | 1.52% | 0.80% | 2 | 2 |
| TRULY_ALLIANCE | nan% | nan% | 0.62% | nan% | 0.83% | 0 | 1 |
| APC | 0.00% | 0.25% | 0.41% | 0.26% | 0.20% | 0 | 1 |
| COPE | 1.36% | 2.64% | 0.40% | 2.70% | 0.35% | 3 | 1 |
| UNITED_ACTION_FRONT | nan% | nan% | 0.13% | nan% | 0.21% | 0 | 0 |
| AZAPO | nan% | nan% | 0.13% | nan% | 0.14% | 0 | 0 |
| UDM | 0.00% | 0.23% | 0.11% | 0.18% | 0.15% | 0 | 0 |

**Missed entirely:** NFP — won seats, median zero.

## eThekwini 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.99% | 57.78% | 59.11% | 53.29% | 52.95% | 122 | 126 |
| DA | 28.78% | 29.14% | 27.54% | 33.41% | 26.30% | 68 | 61 |
| IFP | 3.20% | 3.42% | 4.28% | 3.41% | 4.12% | 7 | 10 |
| EFF | 2.45% | 2.67% | 3.63% | 2.79% | 3.26% | 6 | 8 |
| AIC | 0.00% | 1.21% | 1.51% | 1.26% | 1.23% | 0 | 3 |
| ACDP | 0.50% | 0.65% | 0.54% | 0.74% | 0.55% | 1 | 1 |
| MINORITY_FRONT | 3.15% | 3.34% | 0.46% | 3.65% | 0.60% | 7 | 1 |
| DEMOCRATIC_LIBERAL_CONGRESS | nan% | nan% | 0.43% | nan% | 0.60% | 0 | 1 |
| TRULY_ALLIANCE | 0.34% | 0.51% | 0.42% | 0.64% | 0.40% | 1 | 1 |
| MINORITIES_OF_SOUTH_AFRICA | nan% | nan% | 0.27% | nan% | 0.35% | 0 | 1 |
| APC | 0.29% | 0.46% | 0.26% | 0.25% | 0.15% | 1 | 1 |
| ALJAMAAH | nan% | nan% | 0.18% | nan% | 0.20% | 0 | 1 |

**Missed entirely:** AIC — won seats, median zero.

## eThekwini 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 43.54% | 43.27% | 42.51% | 42.07% | 41.77% | 96 | 96 |
| DA | 25.94% | 26.55% | 26.33% | 27.50% | 25.57% | 59 | 59 |
| EFF | 9.57% | 10.24% | 10.80% | 10.16% | 10.15% | 21 | 24 |
| IFP | 3.77% | 4.69% | 7.45% | 5.16% | 6.67% | 9 | 16 |
| ASA | 5.47% | 6.19% | 2.35% | 6.02% | 1.50% | 12 | 4 |
| AIC | 0.25% | 0.93% | 1.01% | 0.40% | 0.33% | 1 | 2 |
| ACTIVE_CITIZENS_COALITION | 0.02% | 0.11% | 0.81% | 0.11% | 1.03% | 0 | 2 |
| ACDP | 0.36% | 0.71% | 0.76% | 0.78% | 0.78% | 1 | 2 |
| ABANTU_BATHO_CONGRESS | 0.02% | 0.10% | 0.65% | 0.09% | 0.76% | 0 | 2 |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.03% | 0.25% | 0.61% | 0.24% | 0.51% | 0 | 1 |
| ATM | 0.16% | 0.51% | 0.57% | 0.50% | 0.66% | 0 | 1 |
| MINORITY_FRONT | 0.52% | 0.71% | 0.50% | 1.00% | 0.47% | 1 | 1 |

## Cape Town 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 58.08% | 57.67% | 61.15% | 58.01% | 60.69% | 129 | 135 |
| ANC | 26.89% | 26.98% | 33.17% | 26.35% | 32.44% | 59 | 73 |
| COPE | 6.85% | 7.45% | 1.13% | 7.40% | 1.08% | 15 | 3 |
| ACDP | 1.20% | 1.83% | 1.06% | 1.95% | 1.37% | 3 | 3 |
| NATIONAL_PARTY_SOUTH_AFRICA | 0.00% | 0.19% | 0.54% | 0.19% | 0.51% | 0 | 1 |
| UDM | 0.10% | 0.63% | 0.38% | 0.54% | 0.40% | 0 | 1 |
| ALJAMAAH | 0.25% | 0.85% | 0.35% | 0.84% | 0.39% | 1 | 1 |
| AFRICA_MUSLIM_PARTY | 0.40% | 0.89% | 0.28% | 1.12% | 0.40% | 1 | 1 |
| CAPE_MUSLIM_CONGRESS | 0.00% | 1.50% | 0.25% | 1.49% | 0.33% | 0 | 1 |
| PAC | 0.06% | 0.51% | 0.18% | 0.53% | 0.23% | 0 | 1 |
| VFPLUS | 0.06% | 0.49% | 0.17% | 0.49% | 0.19% | 0 | 1 |
| DEMOCRATS_FOR_CHANGE | nan% | nan% | 0.15% | nan% | 0.08% | 0 | 0 |

## Cape Town 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 67.58% | 67.24% | 66.75% | 67.72% | 66.46% | 157 | 154 |
| ANC | 24.71% | 24.92% | 24.52% | 23.89% | 24.20% | 56 | 57 |
| EFF | 2.25% | 2.46% | 3.12% | 2.70% | 3.22% | 6 | 7 |
| ACDP | 0.70% | 0.94% | 1.13% | 1.16% | 1.29% | 2 | 3 |
| AIC | 0.30% | 0.47% | 0.76% | 0.51% | 0.42% | 1 | 1 |
| ALJAMAAH | 0.21% | 0.42% | 0.55% | 0.51% | 0.76% | 1 | 2 |
| VFPLUS | 0.17% | 0.32% | 0.39% | 0.37% | 0.43% | 0 | 1 |
| UDM | 0.23% | 0.37% | 0.33% | 0.19% | 0.20% | 0 | 1 |
| DEMOCRATIC_INDEPENDENT_PARTY | 0.00% | 1.59% | 0.28% | 1.74% | 0.32% | 0 | 1 |
| CAPE_MUSLIM_CONGRESS | nan% | nan% | 0.27% | nan% | 0.25% | 0 | 1 |
| COPE | 0.04% | 0.17% | 0.24% | 0.17% | 0.25% | 0 | 1 |
| PAC | 0.16% | 0.33% | 0.24% | 0.42% | 0.27% | 0 | 1 |

## Cape Town 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 60.72% | 60.49% | 58.74% | 59.71% | 57.78% | 139 | 135 |
| ANC | 22.14% | 22.21% | 18.71% | 22.50% | 18.46% | 51 | 43 |
| EFF | 4.68% | 4.96% | 4.15% | 5.07% | 4.10% | 11 | 10 |
| GOOD | 2.88% | 3.19% | 3.68% | 3.07% | 3.94% | 7 | 9 |
| CAPE_COLOURED_CONGRESS | 0.00% | 0.09% | 2.83% | 0.09% | 2.78% | 0 | 7 |
| ACDP | 2.05% | 2.37% | 2.29% | 2.82% | 2.40% | 5 | 6 |
| VFPLUS | 0.61% | 0.92% | 1.54% | 0.99% | 1.63% | 2 | 4 |
| PA | 0.00% | 1.24% | 1.43% | 1.19% | 1.54% | 0 | 4 |
| ALJAMAAH | 0.65% | 0.84% | 1.19% | 1.15% | 1.32% | 2 | 3 |
| AFRICA_RESTORATION_ALLIANCE | 0.00% | 0.08% | 0.64% | 0.08% | 0.81% | 0 | 2 |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.00% | 0.08% | 0.62% | 0.08% | 0.65% | 0 | 2 |
| UIM | 0.00% | 0.08% | 0.56% | 0.07% | 0.58% | 0 | 1 |

**Missed entirely:** CAPE_COLOURED_CONGRESS, PA — won seats, median zero.

## Mangaung 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 59.20% | 58.05% | 66.57% | 57.28% | 65.96% | 57 | 65 |
| DA | 18.62% | 19.73% | 26.82% | 20.08% | 27.40% | 18 | 26 |
| COPE | 12.41% | 14.03% | 3.30% | 11.41% | 3.02% | 11 | 3 |
| VFPLUS | 3.77% | 4.33% | 1.40% | 8.63% | 1.62% | 6 | 2 |
| ACDP | 0.23% | 1.02% | 0.56% | 0.45% | 0.29% | 0 | 0 |
| APC | 0.00% | 0.30% | 0.55% | 0.25% | 0.39% | 0 | 1 |
| PAC | 0.01% | 0.66% | 0.26% | 0.32% | 0.21% | 0 | 0 |
| DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA | 0.00% | 0.62% | 0.25% | 0.57% | 0.22% | 0 | 0 |
| BLACK_CONSCIOUSNESS_PARTY | nan% | nan% | 0.15% | nan% | 0.09% | 0 | 0 |
| UNITED_RESIDENTS_FRONT | nan% | nan% | 0.14% | nan% | 0.20% | 0 | 0 |

## Mangaung 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 57.92% | 57.30% | 56.77% | 57.02% | 56.28% | 58 | 58 |
| DA | 27.04% | 27.85% | 26.20% | 28.57% | 25.73% | 27 | 27 |
| EFF | 8.13% | 8.55% | 8.84% | 7.69% | 8.48% | 8 | 9 |
| AIC | 0.00% | 1.40% | 2.74% | 1.27% | 0.64% | 0 | 2 |
| VFPLUS | 2.13% | 2.30% | 1.85% | 2.67% | 1.99% | 2 | 2 |
| AGENCY_FOR_NEW_AGENDA | nan% | nan% | 1.57% | nan% | 0.21% | 0 | 1 |
| COPE | 0.33% | 0.73% | 0.56% | 0.79% | 0.63% | 0 | 1 |
| ACDP | 0.29% | 0.58% | 0.39% | 0.90% | 0.39% | 0 | 0 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.03% | 0.25% | 0.28% | 0.23% | 0.11% | 0 | 0 |
| APC | 0.17% | 0.64% | 0.25% | 0.59% | 0.17% | 0 | 0 |
| AZANIAN_ALLIANCE_CONGRESS | nan% | nan% | 0.13% | nan% | 0.06% | 0 | 0 |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | nan% | nan% | 0.12% | nan% | 0.09% | 0 | 0 |

## Mangaung 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 49.07% | 48.52% | 51.51% | 48.19% | 49.75% | 49 | 51 |
| DA | 24.87% | 25.68% | 25.48% | 25.26% | 25.98% | 25 | 26 |
| EFF | 11.23% | 12.19% | 11.37% | 11.72% | 11.24% | 11 | 12 |
| VFPLUS | 3.46% | 3.62% | 4.41% | 3.89% | 4.55% | 4 | 5 |
| PA | 1.11% | 1.93% | 1.78% | 1.86% | 1.83% | 1 | 2 |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.03% | 0.37% | 1.26% | 0.36% | 1.61% | 0 | 2 |
| AIC | 0.65% | 1.68% | 0.84% | 3.07% | 1.70% | 1 | 1 |
| ACDP | 0.24% | 0.60% | 0.70% | 0.61% | 0.74% | 0 | 1 |
| ATM | 0.15% | 0.57% | 0.61% | 0.55% | 0.58% | 0 | 1 |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.38% | nan% | 0.38% | 0 | 0 |
| COPE | 0.00% | 0.26% | 0.30% | 0.11% | 0.16% | 0 | 0 |
| MANGAUNG_COMMUNITY_FORUM | 0.19% | 0.36% | 0.21% | 0.34% | 0.02% | 0 | 0 |

## Nelson Mandela Bay 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 45.03% | 44.59% | 52.13% | 44.93% | 51.69% | 54 | 63 |
| DA | 32.80% | 33.47% | 40.24% | 33.19% | 40.02% | 39 | 48 |
| COPE | 15.85% | 16.97% | 4.88% | 16.01% | 5.01% | 18 | 6 |
| UDM | 0.02% | 0.75% | 0.54% | 1.17% | 0.55% | 0 | 1 |
| PAC | 0.03% | 0.73% | 0.52% | 1.27% | 0.57% | 0 | 1 |
| APC | 0.00% | 0.11% | 0.43% | 0.10% | 0.01% | 0 | 0 |
| ACDP | 0.31% | 0.73% | 0.36% | 0.79% | 0.40% | 0 | 1 |
| AZAPO | 0.01% | 0.58% | 0.28% | 0.44% | 0.22% | 0 | 0 |
| VFPLUS | 0.29% | 0.76% | 0.20% | 0.86% | 0.25% | 0 | 0 |
| CHRISTIAN_DEMOCRATIC_PARTY | nan% | nan% | 0.16% | nan% | 0.18% | 0 | 0 |
| AFRICAN_COMMUNITY_MOVEMENT | nan% | nan% | 0.14% | nan% | 0.18% | 0 | 0 |
| UNITED_INDEPENDENT_FRONT | nan% | nan% | 0.06% | nan% | 0.08% | 0 | 0 |

## Nelson Mandela Bay 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 46.53% | 46.76% | 46.66% | 47.20% | 46.75% | 56 | 57 |
| ANC | 40.93% | 40.76% | 41.50% | 40.34% | 40.34% | 49 | 50 |
| EFF | 4.43% | 4.86% | 5.03% | 5.06% | 5.21% | 5 | 6 |
| UDM | 1.02% | 1.26% | 1.83% | 1.24% | 2.00% | 1 | 2 |
| AIC | 1.07% | 1.40% | 1.61% | 1.46% | 0.28% | 1 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.00% | 1.40% | 0.80% | 1.45% | 1.09% | 0 | 1 |
| COPE | 0.57% | 0.84% | 0.70% | 0.86% | 0.77% | 1 | 1 |
| ACDP | 0.30% | 0.54% | 0.35% | 0.63% | 0.37% | 0 | 1 |
| PA | nan% | nan% | 0.29% | nan% | 0.24% | 0 | 1 |
| ALTERNATIVE_DEMOCRATS | nan% | nan% | 0.25% | nan% | 0.08% | 0 | 0 |
| VFPLUS | 0.42% | 0.65% | 0.25% | 0.83% | 0.26% | 1 | 0 |
| PAC | 0.42% | 0.71% | 0.23% | 0.23% | 0.12% | 0 | 0 |

## Nelson Mandela Bay 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| DA | 44.53% | 44.66% | 40.04% | 44.59% | 39.80% | 53 | 48 |
| ANC | 37.91% | 37.66% | 39.60% | 37.11% | 39.26% | 45 | 48 |
| EFF | 7.08% | 7.81% | 6.40% | 8.19% | 6.40% | 9 | 8 |
| NORTHERN_ALLIANCE | 0.05% | 0.21% | 2.09% | 0.22% | 2.18% | 0 | 3 |
| ACDP | 0.78% | 1.06% | 1.68% | 1.13% | 1.64% | 1 | 2 |
| VFPLUS | 1.05% | 1.27% | 1.64% | 1.31% | 1.51% | 1 | 2 |
| DOP | 0.04% | 0.18% | 1.38% | 0.19% | 1.47% | 0 | 2 |
| PA | 0.00% | 1.54% | 1.32% | 1.58% | 1.42% | 0 | 2 |
| ABANTU_INTEGRITY_MOVEMENT | 0.05% | 0.21% | 1.11% | 0.21% | 1.05% | 0 | 1 |
| UDM | 0.27% | 0.80% | 1.07% | 0.94% | 1.01% | 0 | 1 |
| AIC | 0.28% | 0.93% | 0.68% | 0.47% | 0.38% | 0 | 1 |
| PAC | 0.03% | 0.44% | 0.51% | 0.53% | 0.48% | 0 | 1 |

**Missed entirely:** NORTHERN_ALLIANCE — won seats, median zero.

## Buffalo City 2011

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 62.32% | 61.25% | 69.13% | 63.04% | 70.88% | 63 | 71 |
| DA | 12.80% | 14.96% | 20.26% | 15.86% | 20.71% | 13 | 21 |
| COPE | 15.00% | 16.97% | 3.70% | 13.43% | 2.02% | 13 | 3 |
| AIC | 0.02% | 0.70% | 3.58% | 0.55% | 0.17% | 0 | 2 |
| PAC | 0.33% | 2.08% | 1.66% | 2.39% | 2.11% | 0 | 2 |
| UDM | 0.01% | 0.95% | 0.74% | 1.82% | 0.53% | 0 | 0 |
| ACDP | 0.30% | 1.39% | 0.70% | 1.57% | 0.79% | 0 | 1 |
| PAN_AFRICANIST_MOVEMENT | 0.00% | 0.38% | 0.23% | 0.30% | 0.13% | 0 | 0 |

## Buffalo City 2016

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 60.38% | 59.67% | 59.86% | 60.09% | 57.63% | 61 | 60 |
| DA | 24.10% | 25.32% | 23.45% | 25.94% | 23.35% | 24 | 24 |
| EFF | 4.90% | 5.95% | 8.21% | 5.12% | 7.74% | 5 | 8 |
| AIC | 1.11% | 2.15% | 3.89% | 4.08% | 2.95% | 2 | 4 |
| UDM | 1.72% | 2.60% | 1.29% | 0.78% | 0.45% | 1 | 1 |
| COPE | 0.05% | 0.45% | 0.99% | 0.46% | 0.72% | 0 | 1 |
| PAC | 0.70% | 1.65% | 0.98% | 1.44% | 0.82% | 1 | 1 |
| ACDP | 0.22% | 0.60% | 0.55% | 0.70% | 0.56% | 0 | 1 |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | nan% | nan% | 0.32% | nan% | 0.27% | 0 | 0 |
| PAN_AFRICANIST_MOVEMENT | nan% | nan% | 0.20% | nan% | 0.04% | 0 | 0 |
| PEOPLES_ALLIANCE | nan% | nan% | 0.16% | nan% | 0.02% | 0 | 0 |
| UNITED_CONGRESS | 0.00% | 0.17% | 0.10% | 0.15% | 0.09% | 0 | 0 |

## Buffalo City 2021

| party | list median | list mean | list actual | ward mean | ward actual | seats model | seats actual |
|---|---|---|---|---|---|---|---|
| ANC | 56.36% | 55.62% | 60.51% | 55.98% | 58.35% | 57 | 61 |
| DA | 21.03% | 21.91% | 19.49% | 22.82% | 19.55% | 22 | 20 |
| EFF | 11.14% | 12.13% | 12.37% | 11.98% | 11.76% | 11 | 13 |
| UDM | 0.34% | 0.84% | 1.10% | 1.72% | 0.82% | 1 | 1 |
| PAC | 0.26% | 1.12% | 1.05% | 1.16% | 0.83% | 0 | 1 |
| AIC | 0.69% | 1.73% | 0.97% | 0.42% | 0.45% | 1 | 1 |
| ATM | 0.38% | 0.95% | 0.89% | 0.84% | 0.93% | 0 | 1 |
| ACDP | 0.49% | 0.68% | 0.57% | 0.72% | 0.55% | 1 | 1 |
| VFPLUS | 0.10% | 0.40% | 0.52% | 0.36% | 0.51% | 0 | 1 |
| PA | 0.08% | 0.16% | 0.42% | 0.14% | 0.19% | 0 | 0 |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.08% | 0.15% | 0.34% | 0.13% | 0.10% | 0 | 0 |
| COPE | 0.00% | 0.13% | 0.27% | 0.01% | 0.05% | 0 | 0 |