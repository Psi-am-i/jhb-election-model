# 1b v3 addendum: the line at a flat 1% of the list vote

Owner decision, 2026-10-11: the line is a flat 1% of the list vote in every
city, not seat quotas. Everything in `1b-small-party-design-v3.md` stands except
what this addendum replaces. Read-only: nothing in `src/` or `data/` written, no
writing runs, no sub-delegation. Same sources and the same scripts as v3, re-run
at the new line. Every centre is the unshocked `pool_spec` centre the draw
conserves.

## 1. The rule

A party is a unit party, drawn outside the pool split and counted in the
small-party class, when all three hold:
- it is not a seeded arrival;
- it stood at the previous election in this city (the previous local election;
  for a party new to local elections, the preceding national election);
- both that result and its current centre are below `UNIT_LINE_SHARE`.

`UNIT_LINE_SHARE` = 0.01 is a named module constant, replacing
`UNIT_LINE_QUOTAS`. In v3 §3.1 the test becomes
max(`s_prev`, `centre_i`) < `UNIT_LINE_SHARE`. Nothing else in the specification
changes.

## 2. The record at 1%

Consecutive metro LGE pairs 2006→2011, 2011→2016, 2016→2021. Same denominator
rule as v3: parties on the ballot at the later election.

| population | below 1%, all | on the ballot again | reached 5% | largest later share |
|---|---|---|---|---|
| previous local result < 1% | 337 | 175 | 0 | 3.48% (VF+ Ekurhuleni 2021, from 0.90%) |
| new to local elections, preceding national share < 1% (stood) | — | 69 | 0 | 3.58% (AIC Buffalo City 2011, from 0.49% nationally) |
| **together** | | **244** | **0** | **3.58%** |

With 0 of 244, the rate of a rise to 5% is below 1.2% at 95% confidence
(one-sided). Two parties standing again reached 2% from below 1%: VF+
Ekurhuleni (0.90 → 3.48%) and the PA in Johannesburg (0.17 → 2.96%). At three
quotas the figures were 0 of 273 and a bound of 1.1%. The record supports both
lines equally; the choice between them is the owner's.

## 3. Membership: 1% against three quotas

Established / debutant unit parties per city-year. No party is in the class at
1% that was not in it at three quotas; the 1% line only removes parties.

| city-year | 1% | 3 quotas | in at 3 quotas only |
|---|---|---|---|
| buffalocity-2011 | 0 / 2 | 3 / 2 | ACDP, PAC, UDM |
| buffalocity-2016 | 2 / 1 | 4 / 1 | PAC, UDM |
| buffalocity-2021 | 2 / 6 | 4 / 6 | PAC, UDM |
| capetown-2011 | 8 / 5 | 9 / 5 | AFRICA_MUSLIM_PARTY |
| capetown-2016 | 13 / 2 | 15 / 2 | ACDP, COPE |
| capetown-2021 | 15 / 5 | 15 / 5 | — |
| ekurhuleni-2011 | 5 / 2 | 7 / 2 | ACDP, PAC |
| ekurhuleni-2016 | 6 / 3 | 8 / 3 | COPE, IFP |
| ekurhuleni-2021 | 8 / 4 | 9 / 4 | IFP |
| ethekwini-2011 | 4 / 1 | 4 / 1 | — |
| ethekwini-2016 | 7 / 1 | 7 / 1 | — |
| ethekwini-2021 | 16 / 5 | 16 / 5 | — |
| joburg-2011 | 8 / 2 | 8 / 2 | — |
| joburg-2016 | 9 / 2 | 10 / 2 | COPE |
| joburg-2021 | 12 / 7 | 12 / 7 | — |
| **joburg-2026** | **19 / 5** | **20 / 5** | **ACDP** |
| mangaung-2011 | 1 / 1 | 3 / 1 | ACDP, PAC |
| mangaung-2016 | 5 / 1 | 6 / 1 | VFPLUS |
| mangaung-2021 | 6 / 3 | 8 / 4 | AGENCY_FOR_NEW_AGENDA, AIC, PA |
| nelsonmandelabay-2011 | 4 / 1 | 6 / 1 | UDM, VFPLUS |
| nelsonmandelabay-2016 | 6 / 0 | 7 / 1 | AIC, UDM |
| nelsonmandelabay-2021 | 5 / 3 | 9 / 3 | ACDP, AIC, UDM, VFPLUS |
| tshwane-2011 | 6 / 2 | 7 / 2 | PAC |
| tshwane-2016 | 11 / 2 | 11 / 2 | — |
| tshwane-2021 | 12 / 8 | 12 / 8 | — |

The two lines coincide in the large councils and differ in the small ones,
where three quotas is 2.5-3% and takes in parties of 1-3% (PAC, UDM, AIC, ACDP,
VF+) that 1% leaves in the pool split.

**Johannesburg 2026 at 1%.**
- **19 established**, by `pool_spec` centre: ALJAMAAH 0.879%, ATM 0.428%,
  AHC 0.409%, AIC 0.379%, PAC 0.338%, UDM 0.157%, UIM 0.128%, APC 0.119%,
  INTERNATIONAL_REVELATION_CONGRESS 0.099%, AZAPO 0.097%, NFP 0.068%,
  COPE 0.061%, THE_ORGANIC_HUMANITY_MOVEMENT 0.045%,
  AFRICA_RESTORATION_ALLIANCE 0.043%, CHANGE 0.040%,
  ECONOMIC_EMANCIPATION_FORUM 0.040%, BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA 0.034%,
  AMALGAMATED_RAINBOW_MOVEMENT 0.029%, SHOSHOLOZA_PROGRESSIVE_PARTY 0.018%.
- **5 debutants:** UNITED_AFRICANS_TRANSFORMATION 0.215%, DUDULA 0.158%,
  ECONOMIC_LIBERATORS_FORUM_SOUTH_AFRICA 0.074%,
  AFRICAN_CONGRESS_FOR_TRANSFORMATION 0.062%, AZANIA_PEACEFUL_REVOLUTION 0.030%.
- **Unit centre total:** 3.95%.
- **Left out compared with three quotas:** ACDP (previous LGE 1.03%, centre
  0.73%).

## 4. Parties within ±10% of the line (for the trace and the pre-registration)

Johannesburg 2026, previous result or centre between 0.9% and 1.1%:

| party | treatment | previous result | centre |
|---|---|---|---|
| ACDP | pool split (previous result above the line) | 1.03% (LGE) | 0.731% |
| BOSA | pool split (centre above the line) | 1.02% (NPE) | 1.163% |

ALJAMAAH (previous 0.83%, centre 0.879%) sits 12% below the line and is a unit
party. The trace lists every party within ±10% at every city-year.

**Parties above the line that keep the spike**, Johannesburg 2026, arm E draws.
ACDP is the one addition to v3's list.

| party | arm E mean | median | p99 | max | draws above 5% |
|---|---|---|---|---|---|
| ACDP | 0.76% | 0.36% | 5.88% | 16.41% | 75 |
| VF+ | 0.90% | 0.47% | 5.38% | 13.26% | 63 |
| IFP | 1.49% | 0.60% | 9.71% | 21.47% | 378 |
| RISE | 1.83% | 1.08% | 9.95% | 18.36% | 400 |
| BOSA | 1.19% | 0.53% | 8.35% | 23.49% | 210 |

## 5. Widths re-derived (membership changes them)

Forward, about the `pool_spec` centre, by the same estimator as v3 §3.3.

Established unit parties at 1%:

| target | n | cycle mean | between-metro sd | within sd |
|---|---|---|---|---|
| 2011 | 36 | −0.971 | 0.00 | 0.64 |
| 2016 | 58 | −0.191 | 0.27 | 0.63 |
| 2021 | 75 | +0.495 | 0.14 | 0.84 |

| width for | σ_cyc | σ_btw | σ_wit | total (1%) | total (3 quotas, v3) |
|---|---|---|---|---|---|
| 2016 | 0.97 | 0.00 | 0.64 | 1.16 | 1.06 |
| 2021 | 0.70 | 0.19 | 0.63 | 0.96 | 0.89 |
| 2026 | 0.64 | 0.18 | 0.73 | 0.99 | 0.94 |

Debutants (n 16 / 12 / 40): `σ_deb` 0.94 / 1.29 / 0.95 for 2016 / 2021 / 2026
(v3: 0.94 / 1.27 / 0.94). 2011 keeps v3's fallback (0.27 / 0.48), labelled
untestable.

The widths rise slightly. The smaller membership drops the 1-3% parties, whose
results stayed closer to their centres, so the cycle means (−0.97 / −0.19 /
+0.50) are larger than at three quotas.

## 6. Predictions and falsifiers at 1%

Same method as v3 §6:
- citywide simulation;
- unit parties drawn about their `pool_spec` centres on the logit scale;
- other parties from arm E's draws, scaled by (1 − unit total);
- list seats by largest remainder on 270;
- four simulation seeds.

Arm E figures are recomputed on the 1% membership where the population changed.

### 6.1 Johannesburg 2026 (5,000 draws)

| quantity | arm E (1% members) | v3 (3 quotas) | **1%** |
|---|---|---|---|
| unit parties' mean list share, total | 4.33% | 4.68% (arm E 5.09%) | **3.95%** (0.38 points move to other parties) |
| AIC / ALJAMAAH / ATM mean | 0.422 / 0.950 / 0.468% | 0.379 / 0.879 / 0.428% | **0.379 / 0.879 / 0.428%** |
| ACDP | pool split | unit party: mean 0.731%, p99 4.44% | **pool split, as arm E: mean 0.76%, p99 5.88%, max 16.41%** |
| draws with an established unit party above 5% | 403 | 31 (arm E 473) | **11** (seed sd 2) |
| rate above 2% per party-draw, established unit parties | 0.0219 | 0.0086 | **0.0067** (record 0.011, 95% interval 0.14%-4.1%) |
| draws with any party of arm E mean share < 1% above 5% | 853 | 386 | **438** (ACDP's 75 return) |
| unit-class total p5 / p50 / p95 | 1.02 / 3.47 / 10.88% | 1.69 / 4.02 / 9.72% | **1.36 / 3.34 / 8.41%** |
| list seats, 20 unit parties below one quota | 5.41 | 3.80 | **3.85** |
| list seats, unit parties above one quota | 6.15 (4 parties) | 8.04 (5) | **5.93** (4) |
| ALJAMAAH / ATM / AIC p99 | 2.67 / 6.41 / 6.38% | 2.80 / 2.57 / — | **2.92 / 2.49 / 2.13%** |

### 6.2 Panel (24 city-years), out of sample

| | n | 1% | v3 (3 quotas) |
|---|---|---|---|
| 2016 | 71 | 0.915 | 0.926 |
| 2021 | 117 | 0.855 | 0.850 |
| **2016 + 2021 (falsifier population)** | 188 | **0.878** | 0.880 |
| 2011 (width untestable, not a falsifier) | 52 | 0.288 | 0.302 |
| all 24 | 240 | 0.750 | 0.745 |

**List MAE.** Moving unit parties to their `pool_spec` centres, with the freed
mass spread over the other parties in proportion, changes share-weighted list
MAE by −0.015 points on the panel mean. Range: −0.169 to +0.105; mass moved 0.19
points per city-year on average. v3 predicted −0.027. Unit parties' mean shares
fall against arm E by +0.032 / +0.092 / +0.114 / +0.114 in log
(2011 / 2016 / 2021 / 2026).

### 6.3 Falsifiers

| # | falsifier | v3 (3 quotas) | **1%** |
|---|---|---|---|
| 1 | panel-mean list MAE change | outside −0.027 ± 0.05 | **outside −0.015 ± 0.05** |
| 2 | unit party mean drawn share vs its `pool_spec` centre | > 5% relative | **> 5% relative** |
| 3 | JHB 2026 draws with an established unit party above 5% | > 47 (prediction 31) | **> 40** (a tenth of arm E's 403; prediction 11) |
| 4 | per-year coverage vs the simulation, 2016 and 2021 only | outside 0.926 ± 0.06, 0.850 ± 0.06 | **outside 0.915 ± 0.07, 0.855 ± 0.06** (two binomial standard errors at n 71 and 117) |
| 5 | guard firing rate | > 5e-3 | **> 5e-3** |
| 6 | JHB 2026 unit parties' mean total | outside 4.68% ± 0.15 points | **outside 3.95% ± 0.15 points** |

Response to a coverage miss, as v3: re-estimate widths only from the record,
never to coverage.

## 7. Judgement-call changes

| call | value | evidence | how to check |
|---|---|---|---|
| `UNIT_LINE_SHARE` (named; owner's decision) | 0.01 | 0 of 244 on the ballot below 1% reached 5% (95% bound 1.2%); largest 3.58% | the writer reprints the table each cycle; a rise past 5% from below the line is a defect report |
| widths for 2026 | σ_cyc 0.64, σ_btw 0.18, σ_wit 0.73 (total 0.99); σ_deb 0.95 | §5, forward ANOVA about the `pool_spec` centre; v3's N6 caveat applies | regenerated by the writer |
| widths for 2016 / 2021 | total 1.16 / 0.96; σ_deb 0.94 / 1.29 | §5 | cluster interval printed |

All other judgement calls are as in v3 §5.
