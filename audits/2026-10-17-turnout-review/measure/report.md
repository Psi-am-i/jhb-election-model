# Turnout forecast accuracy and the turnout–share relation in real elections (measurement agent, 2026-10-17)

Read-only measurement on `remediation` at `3fe9f1f`. Scripts and CSVs beside this file. The model was not run; `turnout.main` was called per city-year with `--out` in a scratchpad (byte-identical to the on-disk `data/processed/<city>/<T>/turnout.csv`).

Definitions: turnout = votes cast on the higher ballot / registered (`turnout.read_turnout`). Error = realised − projected, turnout points. Centre = 0.5 × ratio pattern (T_NPE × λ̂) + 0.5 × level pattern (previous-LGE VD turnout rescaled to the ratio pattern's citywide mean), as in `montecarlo.run_model`.

## Part A — turnout forecast accuracy, 8 metros × 2011/2016/2021

A1. Citywide error (realised − projected), turnout points

| cycle | mean error | range | mean abs, centre | mean abs, naive "same as last LGE" |
|---|---|---|---|---|
| 2011 | +13.1 | +7.3 (BUF) to +16.5 (JHB) | 13.1 | 11.7 |
| 2016 | +6.9 | +3.8 (CPT) to +11.3 (TSH) | 6.9 | 1.6 |
| 2021 | −8.4 | −2.3 (BUF) to −11.5 (CPT) | 8.4 | 15.1 |

All 24: mean abs 9.45 (centre) vs 9.46 (naive). Johannesburg: 2011 38.6 projected / 55.1 realised; 2016 49.7 / 57.2; 2021 52.0 / 42.7.

A2. VD level, roll-weighted, 8-metro means (turnout points). Pattern-only = predictor rescaled to the realised citywide level first.

| cycle | RMSE centre | RMSE naive prev LGE | pattern-only RMSE ratio | centre | level/prev LGE |
|---|---|---|---|---|---|
| 2011 | 14.4 | 14.0 | 10.4 | 8.7 | 9.0 |
| 2016 | 9.0 | 6.7 | 9.2 | 7.0 | 6.6 |
| 2021 | 11.5 | 17.0 | 7.4 | 6.5 | 6.7 |

The ratio (λ̂) pattern is worst of the three on pattern-only RMSE at 22 of 24 city-years. Weighted correlation centre vs realised: 0.69 / 0.73 / 0.76.

A3. Pool bands vs realised pool turnout (realised = `pool_counts` at the target; an ecological estimate). Band mode = fitting-election `pool_counts` rate at 96 of 96 pools. Black African realised inside band: 8/8 (2011), 8/8 (2016), 2/8 (2021; below the low at 6, e.g. CPT 32.3 vs low 40.3). All pools 2016: 31/32 inside. Input defect: 2011-target Coloured modes fitted on 2006 are absurd (BUF 3.2%, TSH 15.4%, MAN 24.8% vs realised 53/43/55); 0 of 8 Coloured pools inside at 2011.

A4. Partisan structure of the error vs previous-LGE list shares

| target | DA slope, turnout pts per 10 DA share pts (positive at) | DA-majority minus ANC-majority VDs, mean (range) |
|---|---|---|
| 2011 | +0.76 (7/8) | +5.1 (+0.3 to +13.2) |
| 2016 | +0.58 (8/8; 7 beyond 2 SE) | +4.2 (−0.05 to +6.4) |
| 2021 | +0.16 (5/8) | +1.3 (−4.3 to +5.8) |

The projection under-predicts turnout where the DA is strong.

Item 11. Previous-LGE VD shares held fixed, reweighted by realised turnout instead of the projected centre: DA shift 2016 JHB +0.82, CPT +1.34, NMB +1.94 (positive 7/8, mean +0.91); 2011 mean +0.91 (6/8); 2021 mean +1.16 (6/8). MODEL-LOG §1.317's oracle move for JHB/CPT/NMB 2016: +1.1, +1.9, +2.5.

## Part B — what turnout did to list shares, no model

Join: VDs matched by number across consecutive elections; ≥89.6% of votes at both ends (Mangaung 2011→16: 79.6%). Dropping VDs whose registration moved >30% relative to the city changed the turnout term by ≤0.45 and the within term by ≤1.2.

B5. Decomposition of citywide list-share change, mean of 8 metros, points

| party, pair | actual (joined) | between-VD total | between-VD from turnout (sign count) | within-VD |
|---|---|---|---|---|
| DA 2006→11 | +10.2 | +2.3 | +1.3 (7/8 +) | +7.9 |
| DA 2011→16 | +4.6 | +2.6 | +1.45 (7/8 +) | +2.0 |
| DA 2016→21 | −6.3 | +2.0 | +1.5 (7/8 +) | −8.3 |
| ANC 2006→11 | −5.3 | −2.75 | −1.75 (8/8 −) | −2.6 |
| ANC 2011→16 | −10.9 | −2.5 | −1.5 (7/8 −) | −8.45 |
| ANC 2016→21 | −7.2 | −1.7 | −1.3 (7/8 −) | −5.6 |

JHB DA 2011→16: actual +4.35, turnout term +1.38, within +1.75. 2016→21: actual −12.9, turnout +0.77, within −14.3. Within-VD term vs between-VD turnout term across 24 pairs: correlation −0.10 (DA), +0.26 (ANC). 2006→11 DA alone is inflated by the ID merger.

B8. NPE → following LGE, DA between-VD from turnout: 2009→11 mean +1.8; 2014→16 +2.3; 2019→21 +2.7; range over metros and cycles +0.2 to +4.9 (positive everywhere). θ (`levels.theta_record`) is a national-to-local retention ratio of realised citywide shares and so contains this composition.

B6. Within-VD slope of share change on turnout change (weighted, previous share controlled, HC1): ANC 2016→21 −0.04 to +0.20 share pts per turnout pt at 8/8 (7 under 0.12); DA and ANC 2011→16 |slope| ≤ 0.19 at 8/8; 2006→11 DA positive everywhere (CPT 1.50 alone, 0.45 with ID). In mixed VDs signs flip across metros. Descriptive, not causal.

## Agent's reading (item 7)

Composition holds between VDs (≈ +1.3 to +1.5 DA points per LGE cycle from differential turnout, 7/8 metros each cycle); within-VD change neither offsets nor tracks it. The oracle's DA move has the right sign and size; it scored worse because the centre was already above the actual (JHB 2016 39.9 vs 38.5) before turnout entered, and the realised-minus-projected composition is systematic (positive at 19 of 24). θ contains the national-to-local composition (B8), consistent with turnout being counted twice — argued, not tested.

Not computed: JHB 2026 (no result); EFF covariate before 2021; 2000→06; within-VD pool composition (not identified from VD data); model draw mean not simulated; Mangaung/Tshwane 2011-target bands suspect (2006 census reprojection at 72–77% mapped).
