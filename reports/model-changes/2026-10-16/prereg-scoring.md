# Scoring of two pre-registrations (2026-10-16)

Scored: `prereg/2026-10-15-roll-assignment-and-mk.md` and
`prereg/2026-10-16-ward-contest-and-national-fit.md`. Neither file is edited.
Verdicts: CONFIRMED, FALSIFIED, NOT TESTABLE. The format follows MODEL-LOG §1.304.

## Evidence used, and what each measures

| label | file | what it is |
|---|---|---|
| ROLL | `.claude/roll-2026-10-15/arm-roll/joburg-2026` | Johannesburg 2026, 5,000 draws, seed 20261104, on `911506d` (the §1.304 run) |
| WITH | `.claude/rebuild-2026-10-15b/with/joburg-2026` | same draws and seed, whole-VD assignment and judgements applied (the run `bb280c8` recorded) |
| WITHOUT | `.claude/rebuild-2026-10-15b/without/joburg-2026` | same, emitted with `--without-judgements` (drops `parent_weight`, `weights`, `support`, `overperform`, `sigma_j`, `register`; so MK's call and five other judgements, not MK's call alone) |
| HEAD | `/private/tmp/…/scratchpad/newarm2/joburg-2026` | Johannesburg 2026, 5,000 draws, same seed, in process at `aa95c51` (`.claude/rebuild-2026-10-16/arrays.py` with its output moved outside the repo); ANC 71.71, DA 69.84, MK 23.39 match `forecast_summary.json` and §1.310; every draw sums to 270 |
| H-OLD | `git show 74e7433:data/processed/history.json` | 24 backtest city-years, 1,000 draws; byte-identical to the file at `420e179^` and `bb280c8` |
| H-420 | `git show 420e179:data/processed/history.json` | the run for prereg 2 on the pre-§1.308 code |
| H-NEW | `data/processed/history.json` (`08136c5`) | the final panel, on the whole-council truth |
| H-D80 | `git show d806f99:data/processed/history.json` | the §1.304 roll round's panel |

Backtest quantities: `pr_mae` is the list-vote error in points; `ward_mae` the ward-ballot
share error in points; wards wrong is `wards.n_wards - wards.called`; seats to the wrong
party is half of `seat_abs_err` (the §1.310 definition; `build_report.py` uses half of
`seat_abs_err_coherent`, quoted where it differs).

## Prereg 1: whole-VD roll assignment and the owner's MK call (`40d932a`)

Baseline named by the prereg is §1.304 (ROLL). The re-emit that followed is WITH.

### Gates

| gate | verdict | number |
|---|---|---|
| G1 every backtest city-year identical to the tracked `history.json` | CONFIRMED | H-D80 against H-OLD: `pr_mae`, `ward_mae`, wards wrong, `seat_abs_err`, `seat_abs_err_coherent` and `seats` identical at 24 of 24 |
| G2 the 2026 roll sums to 2,417,915, each ward to its IEC row | CONFIRMED | `test_roll_2026::test_every_ward_sums_to_the_snapshot_and_the_city_to_its_ward_rows` ok in `.claude/rebuild-2026-10-15b/logs/tests.log` (20 of 20 in the module) and in `.claude/rebuild-2026-10-16/logs/tests.log` |

### Predictions

| prediction | verdict | deciding number |
|---|---|---|
| P1a with MK's call, every party's mean citywide list share within 0.05 points of the run without it | CONFIRMED | WITHOUT to WITH: largest move 0.001 points (MK 8.993 to 8.992). The comparison drops six judgements, not MK's alone |
| P1b the assignment change moves every party's mean list share under 0.05 points against §1.304 | CONFIRMED | ROLL to WITH: largest move 0.001 points (MK) |
| P2a the assignment change moves under 6 ward favourites against §1.304 | CONFIRMED | 5 wards change favourite, ROLL to WITH: 34 ANC to MK, 68 DA to PA, 82 PA to DA, 92 DA to ANC, 120 ANC to DA. One under the bound |
| P2b no party's mean seats move by more than 1 against §1.304 | CONFIRMED | largest 0.12 (ANC 71.71 to 71.83) |
| P3a MK's ward wins fall under the call | CONFIRMED in sign, effect nil | WITHOUT to WITH: MK mean wards 10.287 to 10.277 (-0.010). 1,525 of 675,000 ward-draw cells differ between the two runs |
| P3b the ANC's ward wins rise under the call | CONFIRMED in sign, effect nil | ANC mean wards 69.477 to 69.481 (+0.004) |
| P3c mean seats move under 2 for any party under the call | CONFIRMED | largest 0.01 (ANC) |

Reading of P3: the sign held and the size is zero for practical purposes. The mechanism the
prereg gave (the call makes MK's and the ANC's geography more alike, so MK stops
concentrating where the city mix put it) is not supported as a material effect: the call moved
MK's Black African pool weight from 0.686 to 0.872 (WITHOUT and WITH `pools_2026.json`), and
MK's wards moved by one hundredth of a ward. The Black African pool is the dominant pool in both
vectors. Larger ward-win moves in the same period came from the assignment change: MK 10.09 to 10.28 and
PA 4.44 to 4.62 (ROLL to WITH).

Not tested: whether MK's 2024 fit, which replaced the 0.9 call on 2026-10-16, fits better. That
is prereg 2.

## Prereg 2: ward-contest rule, small-party geography, national-record fits (`74e7433`)

Baselines named by the prereg: the published model (arm A, history at `7f0a921`) and the last
rebuild (WITH, history `bb280c8` = H-OLD). Scored against the last rebuild, the one the
predictions are worded against.

### Gates

| gate | verdict | number |
|---|---|---|
| G2 the 2026 roll sums to 2,417,915 (unchanged) | CONFIRMED | `test_roll_2026` ok in `.claude/rebuild-2026-10-16/logs/tests.log` |
| no party wins a ward outside its slate, Johannesburg 2026 | CONFIRMED | HEAD: 0 draws of 5,000 with a win outside a slate, 79 slated parties checked against `judgements/joburg-2026.toml` `[roster.wards]` (`.claude/rebuild-2026-10-16/checks.py` pointed at HEAD). WITH: MK 225 draws, RISE 1 |
| no party wins a ward outside its slate, every backtest city-year | CONFIRMED | in process at `aa95c51`, 100 draws per city-year, seed 20261104, 24 of 24 city-years run, 615 slated parties checked against `levels.ballots`: 0 draws with a ward win outside the party's slate. The mask was not run at 1,000 draws (the history's count) |
| ward-only parties have zero list share in every draw | CONFIRMED for Johannesburg 2026 | HEAD: AFRIKA UNITE CONGRESS, CIVIC MOVEMENT FOR PROGRESSIVE CITIZENS, MAWUSA, RESIDENT DEVELOPMENT, TAU DIA RORA, UDM: maximum list share over 5,000 draws 0.0. Backtests: same 24 runs, 16 ward-only parties across them, maximum list share over 100 draws 0.0 for every one |

### Predictions

| prediction | verdict | deciding number |
|---|---|---|
| P1a Johannesburg 2026, every party's mean list share moves under 0.5 points against the last rebuild | CONFIRMED | WITH to HEAD: largest move 0.156 (UDM, 0.156 to 0.000, its list vote removed); among list parties DA +0.095, ANC +0.087 |
| P1b ward-only parties' list mass is about 0.4% of the list vote | CONFIRMED | WITH: the six ward-only parties' mean list share sums to 0.37% |
| P1c mean seats move under 2 for every party | CONFIRMED | largest 0.46 (UDM 0.46 to 0); DA +0.34, ANC -0.12, MK +0.09 |
| P2a ward favourites change in under 8 wards | CONFIRMED | 1 (ward 82, DA 50.4% / PA 48.7% to PA 50.0% / DA 49.0%) |
| P2b MK wins no ward it does not contest (it did in about 5% of draws) | CONFIRMED | HEAD 0 of 5,000; WITH 225 of 5,000 (4.5%), the prereg's "about 5%" |
| P3a 2021 city-years move only through the ward mask and small-party geography; no 2021 national-record fit applies | CONFIRMED on the second clause; the first is NOT TESTABLE | §1.307 table: no 2021 party is fitted nationally (`pool_counts` refuses 2019). The history carries no run that holds one of the two changes fixed |
| P3b 2021 list error changes under 0.10 points per city-year | CONFIRMED | H-OLD to H-NEW: largest +0.075 (Cape Town), then Tshwane +0.069, eThekwini +0.051, Buffalo City -0.050; 8 of 8 under 0.10. H-420 gives the same `pr_mae` |
| P3c 2021 ward hit rate changes by at most 2 wards per city-year | CONFIRMED | wards wrong unchanged at all 8 (Johannesburg 8, Tshwane 2, Ekurhuleni 5, eThekwini 2, Cape Town 1, Mangaung 1, Nelson Mandela Bay 3, Buffalo City 2) |
| P4a 2011 and 2016 national-record fits do not move any VD's mean share (the parties have a map) | FALSIFIED as the premise; VD shares themselves NOT TESTABLE | the parties had no local map: §1.307 lists vectors that move by up to 0.526 (COPE, eThekwini 2011), 0.663 (PA, Johannesburg 2016), 0.362 (EFF, Cape Town 2016). `ward_mae` fell at all eight 2011 metros, by 0.35 to 0.64 points (Johannesburg 3.96 to 3.43, Tshwane 4.95 to 4.50, Ekurhuleni 3.48 to 2.90, eThekwini 1.43 to 1.07, Cape Town 3.30 to 2.66, Mangaung 6.02 to 5.46, Nelson Mandela Bay 6.82 to 6.34, Buffalo City 6.17 to 5.63). No run saves the VD shares before and after, and the ward mask moved in the same change |
| P4b 2011 and 2016 list error changes under 0.15 points per city-year | CONFIRMED | H-OLD to H-NEW: largest +0.057 (Johannesburg 2016), 2011 largest -0.016 (eThekwini); 16 of 16 under 0.15 |
| P5 ward-only parties' ward-ballot share stays far above their real share (2021: 0.00070 against 0.000027) | CONFIRMED | Johannesburg 2021, 300 draws, seed 20261104, in process at `aa95c51`: AFRICAN COVENANT 0.00030 and SAKHISIZWE CONVENTION 0.00039, sum 0.00069 against 0.000027 in the result file (25 times). The ward-only parties won a ward in 14 draw-wards |

### What the prereg did not predict

| observed | number | source |
|---|---|---|
| wards wrong rose at two 2011 city-years | Buffalo City 0 to 3, eThekwini 12 to 13; 2011 total 26 to 30 | H-OLD to H-NEW |
| 2016 seats to the wrong party rose | 62.0 to 65.0 (`seat_abs_err_coherent`/2); of the 3, eThekwini +2 is the independents' seats entering the truth (§1.309), Cape Town +1 | H-OLD to H-NEW |
| wards wrong total, 24 city-years | 75 to 79 | H-OLD to H-NEW; §1.310's "79 before and after" is H-420 to H-NEW |
| seats to the wrong party, panel | 381.0 to 382.5 on `seat_abs_err`/2 (380.0 at H-420); 356.5 to 356.0 on `seat_abs_err_coherent`/2 | H-OLD, H-420, H-NEW |

P3 and P4 name list error and, for 2021, wards; they name no bound for 2011 and 2016 wards, so
the Buffalo City and eThekwini 2011 moves are not a failed prediction. The mechanism behind them
is not isolated: the ward mask, small-party geography and the COPE national fit all reach 2011.

## Provenance problems

- The old-model forecast arrays are WITH, not ROLL. The 2026-10-15-roll report used ROLL as its
  new state; the commits since (`982cc97`, `185fa78` whole-VD assignment and MK 0.9) were never
  reported to the owner. The 2026-10-16 report uses WITH as old because the prereg 2 baseline and
  the backtest baseline (H-OLD = `bb280c8`) are both that state. ROLL to HEAD changes 4 favourites
  (wards 34, 68, 92, 120); WITH to HEAD changes 1 (ward 82). Mean seats ROLL to HEAD: ANC 71.71 to 71.71, DA 69.57 to 69.84.
- `src/arms.py` cannot run arm U or C0 on this tree (it demands the census hold or a C0 worktree),
  so HEAD was produced with the same in-process script the 2026-10-16 rebuild used.
- WITHOUT drops six judgement families, so P1a and P3 compare "MK's call plus five others" against
  none. The differences are small enough (0.001 points, 0.01 wards) that this does not change a verdict.
- The 2026-10-16 rebuild's own arm (`.claude/rebuild-2026-10-16/arm`) predates §1.308 and sums to 267 to 270
  seats (175 draws below 270); it is not used.
