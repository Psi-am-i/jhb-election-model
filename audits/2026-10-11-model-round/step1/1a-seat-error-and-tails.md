# 1a. Where the seat error comes from, and the tails of the simulated draws

Read-only analysis of arm E (step 11 runs, `data/arms/step11/E/<city>-<year>/`) on the 24 backtest city-years, plus Johannesburg 2026 for Part B. Nothing in `src/` or `data/` was written. Scripts were run from the session scratchpad and are not committed.

## Method

**Files read.** Per city-year: `arrays.npz` (`seat_draws`, `pr_share_draws`, `ward_share_draws`; one column per party, column names in `meta.json` `seat_cols`), `result.json` (`seat_abs_err_coherent`, used only as a check). Johannesburg 2026 has `arrays.npz` and `meta.json` only (no `result.json`; no actual result exists).

**Actual results.** The read functions `compare_history.actual_shares(target, Path("data/raw/elections"))` (citywide list share, `PR` ballot) and `compare_history._actual_seats(target, ...)` (actual seats and the arrival label), with `cityconfig.use(slug)` / `cityconfig.use_target(year)`. The previous election's list shares come from the same `actual_shares` at target year minus 5 (2006 for 2011, 2021 for 2026).

**Relabel.** In the eight 2011 runs the draws carry a generic `ENTRANT` column. As `compare_history` does (`backtest.relabel_run`), it is renamed onto the arrival label from `_actual_seats` where one exists (Cape Town 2011, Ekurhuleni 2011, eThekwini 2011, Johannesburg 2011); where none exists it stays as `ENTRANT` and counts as a party that won nothing. The harness chooses that label with the outcome in hand (see `relabel_run`'s docstring), so the 2011 rows with a label flatter the model slightly.

**Predicted seats, two ways.**
- *coherent* = `compare_history.coherent_seats(draws, council)`, the largest-remainder apportionment of the mean seats, which sums to the council. This is the statistic scored as `seat_abs_err_coherent`. Re-derived here per party and checked: the sum of absolute errors matches `result.json` `seat_abs_err_coherent` exactly at all 24 city-years.
- *mean seats* = mean of `seat_draws` over the 1,000 draws (non-integer; does not sum to the council exactly).

**Seats given to the wrong party** = half the summed absolute seat error over the union of modelled and actual parties, as the owner specified. Per-party contributions in the tables are the party's own absolute error; because the headline is half the sum, a party's contribution to it is half its absolute error. Both are labelled where they appear. The summed (un-halved) figure is not reported except for the single-party errors in A3.

**Party classes** (each (city-year, party) row is in exactly one, tested in this order; numbers match the table headings):
1. ANC/DA.
2. EFF (stood in 2016 and 2021 only).
6. not stood: in the model's columns, actual list share 0 (phantoms, including an unlabelled `ENTRANT`).
3. new: stood at this election (actual list share above 0) and had no list vote at the previous local election in that city. Includes COPE in 2011 (no 2006 local record), ASA 2021, AIC and others in 2016.
4. mid: actual list share 1% or more, not new, not above.
5. small: actual list share under 1% and above 0, not new.

**List-share error** = mean predicted list share over draws minus the actual citywide list share, in percentage points. **Seat error** = mean predicted seats minus actual seats (signed), unless a column says coherent.

**Limits stated here.** The panel is 24 city-years, one seed (20261104), 1,000 draws each, so a class total for a rare class is a handful of parties. "New" depends on the previous election's file, so COPE 2011 is "new" although it was a national party. The record comparison in Part B uses the previous-LGE list share as in MODEL-LOG §1.296 "The real record", taken from `actual_shares`; I quote the 337-case record from §1.296 and did not re-derive it.

## Part A. Seat error source

### A1. Seats given to the wrong party, per city-year (arm E, 1,000 draws each)

Columns 3-4: half the summed absolute seat error. "coherent" = scored statistic (sums to `seat_abs_err_coherent`/2); "mean seats" = from non-integer mean seats. Columns 6-11: the coherent figure split by party class (rows sum to column 3).

| city-year | council seats | actual seats-wrong-party (coherent) | wrong-party (mean seats) | coherent as % of council | 1 ANC/DA | 2 EFF | 3 new | 4 mid | 5 small | 6 not stood |
|---|---|---|---|---|---|---|---|---|---|---|
| buffalocity-2011 | 100.0 | 15.0 | 15.3 | 15.0 | 7.0 | 0.0 | 6.5 | 0.0 | 1.0 | 0.5 |
| buffalocity-2016 | 100.0 | 5.0 | 4.4 | 5.0 | 0.5 | 1.5 | 1.0 | 1.0 | 1.0 | 0.0 |
| buffalocity-2021 | 100.0 | 4.0 | 5.6 | 4.0 | 3.5 | 0.0 | 0.5 | 0.0 | 0.0 | 0.0 |
| capetown-2011 | 221.0 | 21.0 | 21.2 | 9.5 | 10.5 | 0.0 | 8.5 | 0.5 | 1.5 | 0.0 |
| capetown-2016 | 231.0 | 5.0 | 6.8 | 2.2 | 1.5 | 0.5 | 1.0 | 0.0 | 2.0 | 0.0 |
| capetown-2021 | 231.0 | 18.0 | 20.9 | 7.8 | 7.0 | 1.0 | 7.5 | 2.5 | 0.0 | 0.0 |
| ekurhuleni-2011 | 202.0 | 21.0 | 21.7 | 10.4 | 10.0 | 0.0 | 6.0 | 1.0 | 4.0 | 0.0 |
| ekurhuleni-2016 | 224.0 | 12.0 | 12.5 | 5.4 | 4.0 | 1.5 | 4.5 | 0.0 | 2.0 | 0.0 |
| ekurhuleni-2021 | 224.0 | 17.0 | 17.3 | 7.6 | 6.0 | 0.5 | 5.5 | 3.0 | 2.0 | 0.0 |
| ethekwini-2011 | 205.0 | 17.5 | 17.4 | 8.5 | 4.5 | 0.0 | 6.5 | 5.0 | 1.5 | 0.0 |
| ethekwini-2016 | 219.0 | 12.0 | 11.8 | 5.5 | 1.5 | 0.5 | 4.5 | 1.0 | 4.5 | 0.0 |
| ethekwini-2021 | 222.0 | 15.0 | 16.8 | 6.8 | 5.0 | 0.0 | 6.5 | 2.0 | 1.5 | 0.0 |
| joburg-2011 | 260.0 | 32.0 | 32.4 | 12.3 | 15.0 | 0.0 | 13.5 | 1.5 | 2.0 | 0.0 |
| joburg-2016 | 270.0 | 13.0 | 12.8 | 4.8 | 1.5 | 3.0 | 5.0 | 0.5 | 2.5 | 0.5 |
| joburg-2021 | 270.0 | 45.0 | 46.9 | 16.7 | 17.0 | 4.5 | 15.5 | 6.5 | 1.5 | 0.0 |
| mangaung-2011 | 97.0 | 15.0 | 14.8 | 15.5 | 7.0 | 0.0 | 5.0 | 1.0 | 1.5 | 0.5 |
| mangaung-2016 | 100.0 | 4.0 | 4.6 | 4.0 | 1.0 | 0.5 | 1.0 | 0.5 | 1.0 | 0.0 |
| mangaung-2021 | 101.0 | 4.0 | 6.1 | 4.0 | 1.0 | 0.0 | 1.0 | 0.5 | 1.5 | 0.0 |
| nelsonmandelabay-2011 | 120.0 | 18.0 | 17.9 | 15.0 | 9.0 | 0.0 | 6.5 | 0.0 | 1.5 | 1.0 |
| nelsonmandelabay-2016 | 120.0 | 3.0 | 4.1 | 2.5 | 0.0 | 0.5 | 1.0 | 0.5 | 1.0 | 0.0 |
| nelsonmandelabay-2021 | 120.0 | 10.0 | 11.4 | 8.3 | 4.0 | 1.0 | 3.5 | 1.0 | 0.5 | 0.0 |
| tshwane-2011 | 210.0 | 31.0 | 30.9 | 14.8 | 15.0 | 0.0 | 7.5 | 3.5 | 3.5 | 1.5 |
| tshwane-2016 | 214.0 | 9.0 | 9.4 | 4.2 | 2.0 | 2.0 | 3.0 | 0.5 | 1.5 | 0.0 |
| tshwane-2021 | 214.0 | 17.0 | 19.8 | 7.9 | 3.0 | 4.0 | 5.5 | 3.0 | 1.5 | 0.0 |
| TOTAL (24 city-years) | 4375.0 | 363.5 | 382.8 | 8.3 | 136.5 | 21.0 | 126.5 | 35.0 | 40.5 | 4.0 |

### A2. By party class, summed over the 24 city-years

All seat columns are seats given to the wrong party (half the summed absolute error), summed over the rows in the class. Over-/under-forecast columns are the positive and negative seat errors of the mean-seat variant, un-halved, so over + under = 2 x the mean-seats column. The last column is the signed sum of coherent errors (predicted minus actual).

| class | (city-year,party) rows | n_parties_distinct | wrong-party seats, coherent | wrong-party seats, mean seats | seats over-forecast (mean seats) | seats under-forecast (mean seats) | share of coherent total % | signed (pred-actual) seats, coherent |
|---|---|---|---|---|---|---|---|---|
| 1 ANC/DA | 48 | 2 | 136.5 | 136.6 | 94.6 | 178.7 | 37.6 | -75 |
| 2 EFF | 16 | 1 | 21.0 | 21.1 | 21.2 | 20.9 | 5.8 | 2 |
| 3 new | 344 | 173 | 126.5 | 137.7 | 166.5 | 108.9 | 34.8 | 33 |
| 4 mid | 39 | 9 | 35.0 | 37.5 | 28.4 | 46.7 | 9.6 | -14 |
| 5 small | 188 | 56 | 40.5 | 44.9 | 64.7 | 25.1 | 11.1 | 51 |
| 6 not stood | 20 | 15 | 4.0 | 4.9 | 9.8 | -0.0 | 1.1 | 8 |

Same split by election year (coherent, wrong-party seats):

| k | 2011 | 2016 | 2021 |
|---|---|---|---|
| 1 ANC/DA | 78.0 | 12.0 | 46.5 |
| 2 EFF | 0.0 | 10.0 | 11.0 |
| 3 new | 60.0 | 21.0 | 45.5 |
| 4 mid | 12.5 | 4.0 | 18.5 |
| 5 small | 16.5 | 15.5 | 8.5 |
| 6 not stood | 3.5 | 0.5 | 0.0 |

Parties with the largest totals (coherent wrong-party seats summed over the city-years in which the party appears; for COPE the 2011 rows are the new-entrant cases):

| party | wrong-party seats (coherent, summed over its rows) | signed seats (pred - actual) | city-years it appears in |
|---|---|---|---|
| DA | 69.0 | -28 | 24 |
| ANC | 67.5 | -47 | 24 |
| COPE | 53.0 | 94 | 24 |
| EFF | 21.0 | 2 | 16 |
| ASA | 20.5 | -41 | 4 |
| VFPLUS | 13.5 | 5 | 22 |
| IFP | 11.5 | 3 | 15 |
| PA | 10.5 | -21 | 13 |
| AIC | 9.5 | -13 | 16 |
| ACDP | 7.0 | 12 | 24 |
| NFP | 6.0 | -4 | 12 |
| APC | 5.5 | 1 | 21 |

### A3. The 10 largest single (city-year, party) seat errors (coherent)

Seat error = predicted minus actual. The 10 together are 175 seats of absolute error, i.e. 87.5 wrong-party seats, out of 363.5 across the panel.

| rank | city-year | party | class | actual seats | predicted seats (coherent) | predicted mean seats | actual list % | mean predicted list % | list % at previous LGE | seat error (pred-actual) |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | joburg-2021 | ASA | 3 new | 44 | 17 | 16.8 | 18.12 | 6.78 | 0.0 | -27 |
| 2 | joburg-2011 | COPE | 3 new | 3 | 26 | 25.6 | 1.11 | 10.01 | 0.0 | 23 |
| 3 | joburg-2011 | DA | 1 ANC/DA | 90 | 70 | 69.7 | 34.35 | 26.52 | 27.11 | -20 |
| 4 | joburg-2021 | DA | 1 ANC/DA | 71 | 90 | 89.3 | 25.45 | 32.68 | 38.48 | 19 |
| 5 | tshwane-2011 | DA | 1 ANC/DA | 82 | 64 | 64.0 | 38.74 | 30.02 | 30.7 | -18 |
| 6 | joburg-2021 | ANC | 1 ANC/DA | 91 | 106 | 105.4 | 33.22 | 38.78 | 44.92 | 15 |
| 7 | tshwane-2011 | COPE | 3 new | 2 | 16 | 16.2 | 0.89 | 7.93 | 0.0 | 14 |
| 8 | capetown-2011 | COPE | 3 new | 3 | 16 | 15.8 | 1.13 | 7.16 | 0.0 | 13 |
| 9 | capetown-2011 | ANC | 1 ANC/DA | 73 | 60 | 59.9 | 33.17 | 27.34 | 38.67 | -13 |
| 10 | nelsonmandelabay-2011 | COPE | 3 new | 6 | 19 | 19.4 | 4.88 | 16.43 | 0.0 | 13 |

### A4. Does seat error track list-vote error?

Rows are (city-year, party) pairs with a positive actual or predicted list share. Seat error is mean seats minus actual seats; list error in points. The last column multiplies each list-share error by the council size, the seat count a purely proportional reading of that share error would imply.

| group | rows | mean abs list-share error (pp) | corr(list-share error pp, seat error) | slope (seats per pp) | sum abs seat error (mean seats) | sum abs (list error x council) |
|---|---|---|---|---|---|---|
| all | 655 | 0.637 | 0.927 | 1.66 | 765.4 | 764.0 |
| 1 ANC/DA | 48 | 3.398 | 0.932 | 1.71 | 273.2 | 292.7 |
| 2 EFF | 16 | 1.522 | 0.955 | 1.89 | 42.1 | 47.7 |
| 3 new | 344 | 0.418 | 0.918 | 1.6 | 275.4 | 263.2 |
| 4 mid | 39 | 1.037 | 0.948 | 1.84 | 75.1 | 78.2 |
| 5 small | 188 | 0.204 | 0.88 | 2.05 | 89.9 | 71.7 |
| 6 not stood | 20 | 0.357 | 0.91 | 1.16 | 9.8 | 10.4 |

## Part B. Extreme draws

Shares are list (PR) shares in percent. "Prev LGE" is the party's list share at the previous local election in that city (2021 for Johannesburg 2026), 0.00 if it did not stand. Draw counts are out of 5,000 (Johannesburg 2026) or 1,000 (backtests). For backtests, "actual percentile" is the share of draws at or below the actual list share (100 = actual above every draw).

### joburg-2026 (5000 draws): parties with mean list share under 1% (72 parties, sorted by max)

| party | list % prev LGE | mean % | median % | p99 % | max % | draws >2% | draws >5% | draws >10% |
|---|---|---|---|---|---|---|---|---|
| AIC | 0.69 | 0.42 | 0.01 | 6.38 | 25.39 | 297 | 75 | 12 |
| AFRICA_RESTORATION_ALLIANCE | 0.04 | 0.05 | 0.00 | 1.20 | 18.98 | 25 | 6 | 1 |
| PAC | 0.27 | 0.37 | 0.01 | 5.24 | 18.49 | 259 | 56 | 8 |
| UIM | 0.13 | 0.14 | 0.01 | 2.15 | 18.08 | 57 | 8 | 3 |
| INTERNATIONAL_REVELATION_CONGRESS | 0.09 | 0.11 | 0.00 | 2.70 | 16.61 | 73 | 17 | 3 |
| ACDP | 1.03 | 0.76 | 0.36 | 5.88 | 16.41 | 468 | 75 | 6 |
| ALL_NATIVES_OF_SOUTH_AFRICA | 0.00 | 0.09 | 0.00 | 2.04 | 15.82 | 53 | 9 | 1 |
| AHC | 0.43 | 0.43 | 0.01 | 5.56 | 15.61 | 316 | 68 | 10 |
| ATM | 0.32 | 0.47 | 0.01 | 6.41 | 14.57 | 332 | 94 | 12 |
| RESIDENT_DEVELOPMENT | 0.00 | 0.03 | 0.00 | 0.76 | 14.19 | 14 | 1 | 1 |
| NATIONAL_DEMOCRATIC_CONVENTION | 0.00 | 0.09 | 0.00 | 2.11 | 14.15 | 53 | 14 | 4 |
| CIVIC_MOVEMENT_FOR_PROGRESSIVE_CITIZENS | 0.00 | 0.08 | 0.00 | 2.17 | 14.01 | 58 | 12 | 2 |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 0.03 | 0.04 | 0.00 | 1.19 | 13.44 | 29 | 4 | 1 |
| VFPLUS | 1.33 | 0.90 | 0.47 | 5.38 | 13.26 | 665 | 63 | 4 |
| MINORITY_FRONT | 0.00 | 0.08 | 0.00 | 1.75 | 13.15 | 43 | 12 | 3 |
| CHRIST_KINGDOM_PARTY | 0.00 | 0.04 | 0.00 | 0.89 | 12.52 | 24 | 5 | 2 |
| PEOPLE_S_CONSENT_PARTY | 0.00 | 0.03 | 0.00 | 0.58 | 12.50 | 15 | 3 | 1 |
| UDM | 0.24 | 0.17 | 0.00 | 3.80 | 12.36 | 121 | 31 | 2 |
| KINGDOM_COVENANT_DEMOCRATIC_PARTY | 0.00 | 0.03 | 0.00 | 0.79 | 12.21 | 14 | 3 | 1 |
| NCC | 0.00 | 0.08 | 0.00 | 1.86 | 12.19 | 47 | 6 | 1 |
| AZANIA_PEACEFUL_REVOLUTION | 0.00 | 0.04 | 0.00 | 1.19 | 12.06 | 24 | 7 | 1 |
| EKHETHU_PEOPLES_PARTY | 0.00 | 0.08 | 0.00 | 2.10 | 12.01 | 54 | 6 | 1 |
| AZAPO | 0.08 | 0.10 | 0.00 | 2.28 | 11.98 | 58 | 9 | 1 |
| UNITED_AFRICANS_TRANSFORMATION | 0.00 | 0.24 | 0.00 | 3.66 | 11.98 | 147 | 26 | 5 |
| SOUTH_AFRICAN_PEOPLE_S_CIVIC_ORGANIZATION | 0.00 | 0.07 | 0.00 | 1.63 | 11.91 | 38 | 7 | 1 |
| SOUTH_AFRICAN_COMMUNIST_PARTY | 0.00 | 0.07 | 0.00 | 1.46 | 11.72 | 35 | 9 | 1 |
| ECONOMIC_LIBERATORS_FORUM_SOUTH_AFRICA | 0.00 | 0.09 | 0.00 | 2.42 | 11.60 | 62 | 11 | 2 |
| DUDULA | 0.00 | 0.18 | 0.00 | 3.47 | 11.55 | 107 | 27 | 5 |
| ACTIVE_AFRICAN_CHRISTIANS_UNITED_MOVEMENT | 0.00 | 0.08 | 0.00 | 1.86 | 11.46 | 44 | 7 | 1 |
| IMSTAYING | 0.00 | 0.04 | 0.00 | 1.18 | 11.45 | 32 | 5 | 1 |
| AFRICAN_UNEMPLOYED_CONGRESS | 0.00 | 0.08 | 0.00 | 1.72 | 11.44 | 43 | 11 | 1 |
| AZANIAN_GROUND_FORCES | 0.00 | 0.08 | 0.00 | 1.86 | 11.33 | 43 | 7 | 1 |
| TRUTH_AND_SOLIDARITY_MOVEMENT | 0.00 | 0.08 | 0.00 | 1.96 | 11.11 | 47 | 9 | 1 |
| KNOW_YOUR_POWER | 0.00 | 0.08 | 0.00 | 1.98 | 10.67 | 50 | 6 | 1 |
| LAND_PARTY | 0.00 | 0.04 | 0.00 | 1.13 | 10.58 | 24 | 4 | 1 |
| PEOPLE_OF_JOBURG | 0.00 | 0.07 | 0.00 | 1.92 | 10.57 | 49 | 9 | 1 |
| AFRICAN_RENAISSANCE_UNITY | 0.00 | 0.08 | 0.00 | 1.78 | 10.49 | 43 | 11 | 1 |
| AFRICAN_ECONOMIC_FREEDOM | 0.00 | 0.08 | 0.00 | 1.46 | 10.13 | 42 | 11 | 1 |
| ECONOMIC_EMANCIPATION_FORUM | 0.04 | 0.05 | 0.00 | 1.13 | 9.82 | 27 | 7 | 0 |
| MAWUSA_MOVEMENT_PARTY | 0.00 | 0.03 | 0.00 | 0.72 | 9.79 | 17 | 3 | 0 |
| ILIZWE_NATHI | 0.00 | 0.04 | 0.00 | 1.02 | 9.77 | 23 | 8 | 0 |
| PEOPLE_S_MOVEMENT_FOR_CHANGE | 0.00 | 0.07 | 0.00 | 1.75 | 9.45 | 44 | 9 | 0 |
| VUKA_SA | 0.00 | 0.08 | 0.00 | 1.94 | 9.43 | 48 | 8 | 0 |
| GAZA_DEMOCRATIC_FRONT | 0.00 | 0.04 | 0.00 | 0.93 | 9.25 | 21 | 5 | 0 |
| AFRICAN_CONGRESS_FOR_TRANSFORMATION | 0.00 | 0.06 | 0.00 | 1.49 | 9.24 | 40 | 2 | 0 |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.00 | 0.08 | 0.00 | 1.90 | 9.17 | 47 | 6 | 0 |
| NFP | 0.11 | 0.08 | 0.00 | 1.90 | 9.16 | 47 | 12 | 0 |
| UMPHAKATHI_WARONA | 0.00 | 0.07 | 0.00 | 1.65 | 8.98 | 39 | 8 | 0 |
| SERVICE_DELIVERY_PARTY | 0.00 | 0.07 | 0.00 | 1.67 | 8.94 | 39 | 8 | 0 |
| APC | 0.12 | 0.13 | 0.00 | 2.94 | 8.91 | 83 | 17 | 0 |
| ECONOMIC_REDRESS_MOVEMENT | 0.00 | 0.04 | 0.00 | 1.13 | 8.75 | 25 | 9 | 0 |
| ALJAMAAH | 0.83 | 0.95 | 0.84 | 2.67 | 8.55 | 255 | 4 | 0 |
| COPE | 0.19 | 0.06 | 0.00 | 1.54 | 8.48 | 38 | 3 | 0 |
| GAP_FIXERS_OF_SOUTH_AFRICA | 0.00 | 0.04 | 0.00 | 0.86 | 8.43 | 15 | 2 | 0 |
| COMMUNITY_FIRST_MOVEMENT | 0.00 | 0.04 | 0.00 | 1.07 | 8.43 | 22 | 5 | 0 |
| MOVE_SA | 0.00 | 0.07 | 0.00 | 1.42 | 8.37 | 33 | 5 | 0 |
| CHANGE | 0.04 | 0.04 | 0.00 | 1.01 | 8.18 | 26 | 5 | 0 |
| ALLIED_INDEPENDENTS_UMBRELLA | 0.00 | 0.08 | 0.00 | 1.89 | 7.84 | 48 | 6 | 0 |
| LEKWE_BEPE_KINGDOM_PARTY | 0.00 | 0.04 | 0.00 | 1.01 | 7.75 | 23 | 2 | 0 |
| AFRIKA_MAYIBUYE_MOVEMENT | 0.00 | 0.08 | 0.00 | 1.90 | 7.70 | 48 | 11 | 0 |
| AFRICAN_LABOUR_CONVENTION | 0.00 | 0.05 | 0.00 | 1.32 | 7.51 | 29 | 7 | 0 |
| PRO_SOUTH_AFRICA | 0.00 | 0.05 | 0.00 | 1.25 | 7.48 | 29 | 7 | 0 |
| MOVEMENT_OF_RESIDENTS_PARTY | 0.00 | 0.04 | 0.00 | 0.97 | 7.31 | 22 | 4 | 0 |
| ALL_CITIZENS_PARTY | 0.00 | 0.04 | 0.00 | 1.12 | 7.04 | 25 | 2 | 0 |
| AMALGAMATED_RAINBOW_MOVEMENT | 0.03 | 0.03 | 0.00 | 0.61 | 6.87 | 9 | 1 | 0 |
| LABOUR_PARTY_OF_SOUTH_AFRICA | 0.00 | 0.07 | 0.00 | 1.62 | 6.87 | 41 | 4 | 0 |
| AFRICAN_ROYAL_RAINBOW_CONGRESS | 0.00 | 0.03 | 0.00 | 1.10 | 5.64 | 19 | 2 | 0 |
| SHOSHOLOZA_PROGRESSIVE_PARTY | 0.02 | 0.02 | 0.00 | 0.61 | 5.46 | 10 | 1 | 0 |
| COMBAT | 0.00 | 0.03 | 0.00 | 0.90 | 5.33 | 23 | 1 | 0 |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.04 | 0.05 | 0.00 | 1.17 | 4.97 | 14 | 0 | 0 |
| TAU_DIA_RORA_CULTURAL_AND_TRADITIONAL_LEKGOTLA | 0.00 | 0.02 | 0.00 | 0.73 | 4.77 | 10 | 0 | 0 |
| AFRIKA_UNITE_CONGRESS | 0.00 | 0.03 | 0.00 | 0.81 | 4.53 | 13 | 0 | 0 |

Summary for joburg-2026: 69 of 72 sub-1% parties reach 5% or more in at least one draw; 38 reach 10%; 72 reach 2%; 19 have a 99th percentile of 2% or more.

#### joburg-2026: parties with mean list share of 1% or more

| party | list % prev LGE | mean % | p1 % | median % | p99 % | max % |
|---|---|---|---|---|---|---|
| DA | 25.45 | 25.59 | 14.12 | 25.33 | 38.97 | 50.23 |
| ANC | 33.22 | 23.84 | 8.59 | 23.49 | 41.91 | 53.56 |
| ASA | 18.12 | 11.73 | 2.61 | 10.96 | 28.12 | 40.63 |
| EFF | 10.11 | 10.98 | 1.94 | 10.21 | 26.72 | 37.97 |
| MK | 0.00 | 9.03 | 1.47 | 8.24 | 22.74 | 31.36 |
| PA | 2.96 | 5.67 | 2.50 | 5.53 | 12.10 | 31.14 |
| RISE | 0.00 | 1.83 | 0.01 | 1.08 | 9.95 | 18.36 |
| IFP | 2.36 | 1.49 | 0.00 | 0.60 | 9.71 | 21.47 |
| BOSA | 0.00 | 1.19 | 0.00 | 0.53 | 8.35 | 23.49 |

### joburg-2021 (1000 draws): parties with mean list share under 1% (51 parties, sorted by max)

| party | list % prev LGE | mean % | median % | p99 % | max % | draws >2% | draws >5% | draws >10% | actual % | actual percentile in draws | in [min,max] | in [p1,p99] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UDM | 0.25 | 0.19 | 0.01 | 2.52 | 11.08 | 16 | 1 | 1 | 0.24 | 83.5 | yes | yes |
| AFRICAN_PEOPLE_S_MOVEMENT | 0.00 | 0.07 | 0.00 | 1.12 | 10.61 | 5 | 1 | 1 | 0.05 | 83.8 | yes | yes |
| AIC | 1.62 | 0.77 | 0.27 | 6.07 | 10.58 | 116 | 17 | 1 | 0.69 | 68.4 | yes | yes |
| PAC | 0.17 | 0.32 | 0.00 | 4.87 | 9.78 | 39 | 8 | 0 | 0.27 | 78.9 | yes | yes |
| GOOD | 0.00 | 0.40 | 0.12 | 3.73 | 9.74 | 43 | 6 | 0 | 0.33 | 71.5 | yes | yes |
| ACDP | 0.31 | 0.65 | 0.30 | 5.87 | 9.57 | 69 | 13 | 0 | 1.03 | 81.9 | yes | yes |
| DOP | 0.00 | 0.09 | 0.00 | 1.60 | 9.49 | 8 | 2 | 0 | 0.12 | 88.9 | yes | yes |
| ATM | 0.00 | 0.28 | 0.06 | 2.74 | 9.21 | 32 | 2 | 0 | 0.32 | 78.1 | yes | yes |
| AZAPO | 0.06 | 0.10 | 0.00 | 2.03 | 8.21 | 11 | 3 | 0 | 0.08 | 87.9 | yes | yes |
| NFP | 0.00 | 0.14 | 0.00 | 2.84 | 7.74 | 14 | 3 | 0 | 0.11 | 83.5 | yes | yes |
| AFRICAN_COVENANT | 0.00 | 0.07 | 0.00 | 1.53 | 7.62 | 6 | 1 | 0 | 0.00 | 0.0 | NO | NO |
| AFRICAN_AMBASSADORS_OF_SOUTH_AFRICA | 0.00 | 0.09 | 0.00 | 1.51 | 7.58 | 9 | 2 | 0 | 0.08 | 85.9 | yes | yes |
| COMMUNITY_SOLIDARITY_ASSOCIATION | 0.00 | 0.07 | 0.00 | 1.64 | 7.35 | 7 | 1 | 0 | 0.03 | 82.3 | yes | yes |
| PARTY_OF_ACTION | 0.00 | 0.08 | 0.00 | 1.33 | 7.32 | 6 | 1 | 0 | 0.13 | 88.4 | yes | yes |
| AHC | 0.00 | 0.08 | 0.00 | 1.47 | 6.56 | 6 | 1 | 0 | 0.43 | 95.0 | yes | yes |
| BLACK_FIRST_LAND_FIRST | 0.00 | 0.23 | 0.03 | 2.72 | 6.39 | 24 | 6 | 0 | 0.12 | 69.8 | yes | yes |
| ABAHLALY_BAAHI | 0.00 | 0.05 | 0.00 | 0.97 | 6.18 | 4 | 2 | 0 | 0.05 | 85.4 | yes | yes |
| APC | 0.16 | 0.19 | 0.00 | 3.05 | 5.89 | 27 | 3 | 0 | 0.12 | 80.1 | yes | yes |
| DEMOCRATIC_ARTISTS_PARTY | 0.00 | 0.06 | 0.00 | 1.17 | 5.77 | 4 | 1 | 0 | 0.06 | 87.8 | yes | yes |
| PEOPLE_S_FREEDOM_PARTY | 0.00 | 0.05 | 0.00 | 0.87 | 5.63 | 4 | 1 | 0 | 0.06 | 87.1 | yes | yes |
| CIVIC_MOVEMENT_OF_SOUTH_AFRICA | 0.00 | 0.06 | 0.00 | 1.29 | 5.36 | 4 | 1 | 0 | 0.02 | 79.6 | yes | yes |
| ECONOMIC_EMANCIPATION_FORUM | 0.00 | 0.05 | 0.00 | 1.15 | 5.32 | 6 | 1 | 0 | 0.04 | 88.6 | yes | yes |
| AFRICAN_FREEDOM_REVOLUTION | 0.00 | 0.06 | 0.00 | 1.17 | 5.28 | 6 | 1 | 0 | 0.02 | 82.4 | yes | yes |
| SAKHISIZWE_CONVENTION | 0.00 | 0.06 | 0.00 | 1.15 | 5.26 | 6 | 1 | 0 | 0.00 | 0.0 | NO | NO |
| VFPLUS | 0.31 | 0.91 | 0.62 | 3.98 | 5.19 | 124 | 2 | 0 | 1.33 | 76.8 | yes | yes |
| ROYAL_LOYAL_PROGRESS | 0.00 | 0.08 | 0.00 | 1.63 | 5.06 | 7 | 1 | 0 | 0.02 | 72.7 | yes | yes |
| UIM | 0.00 | 0.07 | 0.00 | 1.43 | 4.97 | 5 | 0 | 0 | 0.13 | 90.4 | yes | yes |
| AFRICA_RESTORATION_ALLIANCE | 0.00 | 0.08 | 0.00 | 1.50 | 4.89 | 8 | 0 | 0 | 0.04 | 83.0 | yes | yes |
| DISRUPT_PARTY | 0.00 | 0.06 | 0.00 | 1.08 | 4.83 | 3 | 0 | 0 | 0.02 | 79.5 | yes | yes |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.00 | 0.08 | 0.00 | 1.31 | 4.73 | 5 | 0 | 0 | 0.04 | 81.5 | yes | yes |
| AGENCY_FOR_NEW_AGENDA | 0.00 | 0.07 | 0.00 | 1.53 | 4.67 | 4 | 0 | 0 | 0.02 | 81.5 | yes | yes |
| UNITED_CULTURAL_MOVEMENT | 0.00 | 0.06 | 0.00 | 1.28 | 4.64 | 5 | 0 | 0 | 0.02 | 79.2 | yes | yes |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 0.00 | 0.09 | 0.00 | 2.09 | 4.35 | 11 | 0 | 0 | 0.03 | 82.5 | yes | yes |
| AGANG | 0.03 | 0.02 | 0.00 | 0.26 | 4.10 | 2 | 0 | 0 | 0.08 | 97.8 | yes | yes |
| NATIONAL_PEOPLE_S_FRONT | 0.00 | 0.04 | 0.00 | 0.96 | 4.06 | 5 | 0 | 0 | 0.05 | 90.4 | yes | yes |
| CHANGE | 0.00 | 0.07 | 0.00 | 1.47 | 4.06 | 4 | 0 | 0 | 0.04 | 80.3 | yes | yes |
| COPE | 0.21 | 0.07 | 0.00 | 1.59 | 4.03 | 8 | 0 | 0 | 0.19 | 92.2 | yes | yes |
| AFRICAN_SECURITY_CONGRESS | 0.00 | 0.06 | 0.00 | 1.82 | 3.74 | 8 | 0 | 0 | 0.06 | 88.5 | yes | yes |
| US_THE_PEOPLE | 0.00 | 0.07 | 0.00 | 1.16 | 3.65 | 3 | 0 | 0 | 0.06 | 85.1 | yes | yes |
| ABANTU_BATHO_CONGRESS | 0.00 | 0.05 | 0.00 | 1.31 | 3.47 | 3 | 0 | 0 | 0.13 | 92.8 | yes | yes |
| ACTIVISTS_MOVEMENT_OF_SOUTH_AFRICA | 0.00 | 0.04 | 0.00 | 1.02 | 3.22 | 2 | 0 | 0 | 0.05 | 88.1 | yes | yes |
| INTERNATIONAL_PARTY | 0.00 | 0.06 | 0.00 | 1.26 | 3.02 | 6 | 0 | 0 | 0.02 | 83.3 | yes | yes |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.00 | 0.07 | 0.00 | 1.10 | 3.01 | 3 | 0 | 0 | 0.05 | 83.2 | yes | yes |
| AMALGAMATED_RAINBOW_MOVEMENT | 0.00 | 0.05 | 0.00 | 0.99 | 2.87 | 3 | 0 | 0 | 0.03 | 84.2 | yes | yes |
| BLACK_AND_WHITE_PARTY | 0.00 | 0.05 | 0.00 | 0.91 | 2.53 | 4 | 0 | 0 | 0.01 | 82.0 | yes | yes |
| INTERNATIONAL_REVELATION_CONGRESS | 0.03 | 0.02 | 0.00 | 0.67 | 2.47 | 1 | 0 | 0 | 0.09 | 97.7 | yes | yes |
| FORUM_4_SERVICE_DELIVERY | 0.00 | 0.04 | 0.00 | 0.89 | 2.43 | 1 | 0 | 0 | 0.03 | 85.5 | yes | yes |
| ALJAMAAH | 0.31 | 0.30 | 0.23 | 1.16 | 2.24 | 2 | 0 | 0 | 0.83 | 95.2 | yes | yes |
| SHOSHOLOZA_PROGRESSIVE_PARTY | 0.00 | 0.06 | 0.00 | 0.96 | 2.02 | 1 | 0 | 0 | 0.02 | 76.7 | yes | yes |
| PA | 0.17 | 0.09 | 0.03 | 0.68 | 1.46 | 0 | 0 | 0 | 2.96 | 100.0 | NO | NO |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 0.00 | 0.00 | 0.00 | 0.06 | 1.13 | 0 | 0 | 0 | 0.03 | 98.6 | yes | yes |

Summary for joburg-2021: 26 of 51 sub-1% parties reach 5% or more in at least one draw; 3 reach 10%; 49 reach 2%; 12 have a 99th percentile of 2% or more. The actual list share lies inside [min,max] of the draws for 48 of 51 and inside [p1,p99] for 48 of 51.

#### joburg-2021: parties with mean list share of 1% or more

| party | list % prev LGE | mean % | p1 % | median % | p99 % | max % | actual % | actual percentile in draws | in [p1,p99] |
|---|---|---|---|---|---|---|---|---|---|
| ANC | 44.92 | 38.78 | 21.99 | 38.69 | 55.02 | 61.51 | 33.22 | 21.7 | yes |
| DA | 38.48 | 32.68 | 20.70 | 32.37 | 46.69 | 54.26 | 25.45 | 7.0 | yes |
| EFF | 10.93 | 13.42 | 4.28 | 12.91 | 27.55 | 31.90 | 10.11 | 28.1 | yes |
| ASA | 0.00 | 6.78 | 1.73 | 6.20 | 16.14 | 22.00 | 18.12 | 99.7 | NO |
| IFP | 1.71 | 1.47 | 0.00 | 0.90 | 7.58 | 18.62 | 2.36 | 79.0 | yes |

### ekurhuleni-2011 (1000 draws): parties with mean list share under 1% (8 parties, sorted by max)

| party | list % prev LGE | mean % | median % | p99 % | max % | draws >2% | draws >5% | draws >10% | actual % | actual percentile in draws | in [min,max] | in [p1,p99] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| UDM | 0.74 | 0.43 | 0.00 | 7.45 | 24.90 | 64 | 22 | 6 | 0.42 | 84.2 | yes | yes |
| THEMBISA_CONCERNED_RESIDENTS_ASSOCIATION | 0.21 | 0.26 | 0.00 | 4.48 | 21.72 | 43 | 7 | 3 | 0.05 | 81.5 | yes | yes |
| SIMUNYE_IN_CHRIST_ORGANISATION | 0.36 | 0.45 | 0.04 | 6.71 | 19.72 | 56 | 22 | 4 | 0.08 | 59.2 | yes | yes |
| PAC | 1.40 | 0.79 | 0.04 | 9.55 | 18.11 | 117 | 48 | 8 | 0.61 | 78.5 | yes | yes |
| AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE | 0.00 | 0.10 | 0.00 | 2.28 | 11.59 | 12 | 5 | 1 | 0.08 | 89.0 | yes | yes |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.35 | 0.41 | 0.16 | 3.54 | 10.17 | 36 | 5 | 1 | 0.32 | 67.6 | yes | yes |
| APC | 0.00 | 0.19 | 0.00 | 3.19 | 9.23 | 26 | 8 | 0 | 0.68 | 93.7 | yes | yes |
| CHRISTIAN_DEMOCRATIC_PARTY | 0.17 | 0.16 | 0.00 | 2.70 | 9.00 | 16 | 1 | 0 | 0.08 | 76.1 | yes | yes |

Summary for ekurhuleni-2011: 8 of 8 sub-1% parties reach 5% or more in at least one draw; 6 reach 10%; 8 reach 2%; 8 have a 99th percentile of 2% or more. The actual list share lies inside [min,max] of the draws for 8 of 8 and inside [p1,p99] for 8 of 8. Parties that stood and won list votes but have no model column: BLACK_CONSCIOUSNESS_PARTY 0.11%, FIRST_NATION_LIBERATION_ALLIANCE 0.08%, NATIONAL_REPUBLICAN_PARTY 0.05%, PAN_AFRICANIST_MOVEMENT 0.03%, PEOPLE_S_CIVIC_ORGANISATION 0.08%, THE_REAL_CONGRESS 0.12%.

#### ekurhuleni-2011: parties with mean list share of 1% or more

| party | list % prev LGE | mean % | p1 % | median % | p99 % | max % | actual % | actual percentile in draws | in [p1,p99] |
|---|---|---|---|---|---|---|---|---|---|
| ANC | 61.29 | 56.44 | 30.80 | 57.64 | 72.48 | 76.13 | 62.17 | 68.9 | yes |
| DA | 25.89 | 25.71 | 14.65 | 24.76 | 45.49 | 65.01 | 30.13 | 82.7 | yes |
| COPE | 0.00 | 6.50 | 0.31 | 5.08 | 24.43 | 31.83 | 1.09 | 7.2 | yes |
| IFP | 2.86 | 2.27 | 0.02 | 0.85 | 16.10 | 33.72 | 1.16 | 57.4 | yes |
| DISPLACEES_RATE_PAYERS_ASSOCIATION | 1.43 | 1.99 | 0.00 | 0.46 | 16.89 | 33.95 | 0.41 | 48.7 | yes |
| VFPLUS | 1.05 | 1.70 | 0.05 | 0.97 | 11.93 | 24.40 | 0.51 | 26.1 | yes |
| NFP | 0.00 | 1.42 | 0.00 | 0.00 | 9.96 | 11.92 | 1.13 | 75.4 | yes |
| ACDP | 1.21 | 1.17 | 0.00 | 0.44 | 11.56 | 32.09 | 0.59 | 58.0 | yes |

### mangaung-2021 (1000 draws): parties with mean list share under 1% (16 parties, sorted by max)

| party | list % prev LGE | mean % | median % | p99 % | max % | draws >2% | draws >5% | draws >10% | actual % | actual percentile in draws | in [min,max] | in [p1,p99] |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NFP | 0.00 | 0.06 | 0.00 | 1.32 | 18.53 | 7 | 1 | 1 | 0.08 | 93.1 | yes | yes |
| UIM | 0.00 | 0.34 | 0.05 | 4.43 | 17.46 | 38 | 8 | 3 | 0.17 | 67.0 | yes | yes |
| ATM | 0.00 | 0.68 | 0.16 | 7.02 | 16.66 | 95 | 22 | 4 | 0.61 | 74.1 | yes | yes |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 0.00 | 0.30 | 0.03 | 4.42 | 15.63 | 39 | 7 | 1 | 0.03 | 48.8 | yes | yes |
| INTERNATIONAL_PARTY | 0.00 | 0.29 | 0.03 | 3.33 | 15.46 | 31 | 8 | 2 | 0.08 | 61.9 | yes | yes |
| APC | 0.25 | 0.29 | 0.00 | 6.26 | 12.85 | 39 | 12 | 1 | 0.12 | 78.6 | yes | yes |
| MANGAUNG_COMMUNITY_FORUM | 0.00 | 0.29 | 0.03 | 4.51 | 12.48 | 29 | 8 | 2 | 0.21 | 76.6 | yes | yes |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.28 | 0.21 | 0.00 | 3.98 | 11.51 | 33 | 5 | 1 | 0.38 | 90.4 | yes | yes |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 0.00 | 0.42 | 0.08 | 5.12 | 11.44 | 54 | 12 | 3 | 1.26 | 91.5 | yes | yes |
| ACDP | 0.39 | 0.64 | 0.24 | 5.87 | 11.29 | 74 | 13 | 3 | 0.70 | 75.7 | yes | yes |
| UNITED_RESIDENTS_FRONT | 0.09 | 0.12 | 0.00 | 3.66 | 10.11 | 19 | 7 | 1 | 0.05 | 90.9 | yes | yes |
| FORUM_4_SERVICE_DELIVERY | 0.00 | 0.26 | 0.02 | 4.59 | 9.26 | 31 | 7 | 0 | 0.16 | 77.4 | yes | yes |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 0.12 | 0.12 | 0.00 | 2.95 | 8.62 | 20 | 5 | 0 | 0.14 | 91.3 | yes | yes |
| AFRICA_S_NEW_DAWN | 0.00 | 0.32 | 0.05 | 4.95 | 8.11 | 40 | 10 | 0 | 0.13 | 67.8 | yes | yes |
| COPE | 0.56 | 0.18 | 0.01 | 3.21 | 7.76 | 26 | 5 | 0 | 0.30 | 89.9 | yes | yes |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.00 | 0.40 | 0.07 | 5.00 | 7.40 | 52 | 10 | 0 | 0.04 | 41.4 | yes | yes |

Summary for mangaung-2021: 16 of 16 sub-1% parties reach 5% or more in at least one draw; 11 reach 10%; 16 reach 2%; 15 have a 99th percentile of 2% or more. The actual list share lies inside [min,max] of the draws for 16 of 16 and inside [p1,p99] for 16 of 16.

#### mangaung-2021: parties with mean list share of 1% or more

| party | list % prev LGE | mean % | p1 % | median % | p99 % | max % | actual % | actual percentile in draws | in [p1,p99] |
|---|---|---|---|---|---|---|---|---|---|
| ANC | 56.77 | 48.04 | 27.97 | 48.26 | 65.18 | 70.68 | 51.51 | 64.4 | yes |
| DA | 26.20 | 26.13 | 16.59 | 25.21 | 42.25 | 56.79 | 25.48 | 52.2 | yes |
| EFF | 8.84 | 12.45 | 2.02 | 11.66 | 28.83 | 40.05 | 11.37 | 47.8 | yes |
| VFPLUS | 1.85 | 3.53 | 0.85 | 3.35 | 7.80 | 12.58 | 4.41 | 75.6 | yes |
| PA | 0.00 | 1.92 | 0.02 | 1.12 | 11.36 | 22.33 | 1.78 | 67.2 | yes |
| AIC | 2.74 | 1.67 | 0.00 | 0.62 | 11.14 | 24.75 | 0.84 | 57.5 | yes |
| AGENCY_FOR_NEW_AGENDA | 1.57 | 1.32 | 0.00 | 0.45 | 10.39 | 16.88 | 0.14 | 34.2 | yes |


### B-record. The draw range against the real record

MODEL-LOG §1.296 "The real record": of 337 cases of a party under 1% at one election and a consecutive one, none reached 5% at the next; two reached 2% (VFPLUS Ekurhuleni 0.90% to 3.48%; PA Johannesburg 0.17% to 2.96%); every rise past 5% from under 1% was a party absent at the earlier election (EFF 2016, ActionSA 2021).

Here "eligible" = a party in the draws that stood at the previous election with a list share above 0 and under 1%. "First-time" = absent at the previous election (record permits these to rise). Rates are over (eligible party, draw) pairs.

| run | parties that stood at prev LGE with <1% (eligible) | per party-draw: share >=2 % | per party-draw: share >=5 % | draws with at least one eligible party >=2% | draws with at least one eligible party >=5% | eligible parties that reach 5% in some draw | largest eligible share in any draw (%) | parties absent at prev LGE (first-time) | first-time: draws with one >=5% | largest first-time share (%) |
|---|---|---|---|---|---|---|---|---|---|---|
| joburg-2026 | 19 | 2.19% | 0.44% | 34.7% | 8.1% | 18 | 25.39 | 54 | 83.6% | 31.36 |
| joburg-2021 | 12 | 2.49% | 0.25% | 26.8% | 3.0% | 6 | 11.08 | 39 | 68.0% | 22.0 |
| ekurhuleni-2011 | 5 | 4.3% | 1.14% | 19.8% | 5.4% | 5 | 24.9 | 4 | 58.6% | 31.83 |
| mangaung-2021 | 6 | 3.52% | 0.78% | 19.4% | 4.7% | 6 | 12.85 | 11 | 17.4% | 22.33 |

## 5-line summary

1. Seats given to the wrong party total 363.5 over the 24 city-years (coherent; 8.3% of 4,375 council seats): 170.5 at the 2011 elections, 63.0 at 2016, 130.0 at 2021; Johannesburg 2021 (45.0) and 2011 (32.0) and Tshwane 2011 (31.0) are the largest.
2. ANC and DA carry 136.5 of them (37.6%), parties new at that election carry 126.5 (34.8%; COPE 2011 alone 50.0 and ActionSA 2021 20.5), mid parties 35.0, small old parties 40.5, EFF 21.0, phantom columns 4.0; the 10 largest single errors are 87.5 wrong-party seats (24%).
3. Seat error follows list-vote error: correlation 0.93 across 655 (city-year, party) rows, 1.66 seats per point of list share; the biggest misses are list misses (COPE 2011 forecast 7-16% against 1% actual, ASA Johannesburg 2021 6.8% against 18.1%, DA/ANC 5-9 points off).
4. Johannesburg 2026 (5,000 draws): 69 of 72 parties under 1% mean share reach 5% in at least one draw and 38 reach 10%; AIC (0.69% in 2021) reaches 25.4%; the three backtests show the same, so the draw tails sit far outside the real record (no sub-1% party reached 5%; largest rise 3.48%), though per party-draw the 5% rate (0.25 to 1.14%) is not by itself excluded by 0 of 337.
5. In the backtests the actual share of every small party lies inside the drawn range except the PA at Johannesburg 2021 (2.96% actual against a maximum draw of 1.46%); ASA 2021 (18.12% actual) sits at the 99.7th percentile of its draws, above the 99th (16.14%) and below the maximum (22.00%).
