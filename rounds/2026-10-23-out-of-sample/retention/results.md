# Second-election retention: scored (prereg 2026-10-23)

Produced by `score.py` in this directory from the raw local-election files (list ballot, eight metros). Natural logs. Score = mean absolute log error of predicted against realised ratio, party-metros averaged within party, then over parties.

## Checks the script refuses to score without

- Size line fitted at target 2026 (292 ratios, 59 parties), at share 0.1812: 0.7202.
- Johannesburg EFF list share 2016 → 2021: 10.93% → 10.11%.

## Rules fitted per target

| target | S: a | S: b | S fitted on (ratios / parties) | P | P fitted on (first→second pairs / parties) |
|---|---|---|---|---|---|
| 2016 | 0.0668 | 0.1747 | 83 / 24 | 0.449 | 10 / 9 |
| 2021 | -0.1912 | 0.0732 | 174 / 38 | 0.563 | 37 / 22 |

## Each party's median first→second ratio (P's inputs)

- **Target 2016:** UNITED_INDEPENDENT_FRONT 0.15, CHRISTIAN_FRONT 0.16, AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE 0.19, UNIVERSAL_PARTY 0.42, DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA 0.45, OKM 0.56, UDM 0.72, TRULY_ALLIANCE 0.88, INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA 0.92
- **Target 2021:** UNITED_INDEPENDENT_FRONT 0.15, CHRISTIAN_FRONT 0.16, AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE 0.19, COPE 0.23, MOVEMENT_DEMOCRATIC_PARTY 0.26, NATIONAL_PARTY_SOUTH_AFRICA 0.34, UNIVERSAL_PARTY 0.42, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION 0.44, APC 0.44, DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA 0.45, OKM 0.56, NATIONAL_PEOPLE_S_PARTY 0.57, UNITED_RESIDENTS_FRONT 0.65, UDM 0.72, PAN_AFRICANIST_MOVEMENT 0.85, TRULY_ALLIANCE 0.88, INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA 0.92, CAPE_PARTY_KAAPSE_PARTY 1.07, AIC 1.09, CAPE_MUSLIM_CONGRESS 1.11, ALJAMAAH 1.36, INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA 3.99

## Scores (mean absolute log error)

| target | party | party-metros | S | P |
|---|---|---|---|---|
| 2016 | COPE | 8 | 0.835 | 0.699 |
| 2016 | APC | 7 | 0.255 | 0.207 |
| 2016 | ALJAMAAH | 2 | 1.237 | 1.095 |
| 2016 | AIC | 1 | 0.598 | 0.884 |
| 2016 | **all (mean over parties)** | 18 | **0.731** | **0.721** |
| 2021 | EFF | 8 | 0.670 | 0.859 |
| 2021 | AIC | 6 | 0.382 | 0.357 |
| 2021 | **all (mean over parties)** | 14 | **0.526** | **0.608** |

## Scored pairs

| target | party | metro | first % | second % | realised ratio | S predicted | P predicted |
|---|---|---|---|---|---|---|---|
| 2016 | COPE | JHB | 1.11 | 0.21 | 0.19 | 0.487 | 0.449 |
| 2016 | COPE | TSH | 0.89 | 0.22 | 0.25 | 0.468 | 0.449 |
| 2016 | COPE | CPT | 1.13 | 0.24 | 0.21 | 0.488 | 0.449 |
| 2016 | COPE | ETH | 0.40 | 0.14 | 0.36 | 0.407 | 0.449 |
| 2016 | COPE | EKU | 1.09 | 0.28 | 0.26 | 0.485 | 0.449 |
| 2016 | COPE | MAN | 3.30 | 0.56 | 0.17 | 0.589 | 0.449 |
| 2016 | COPE | NMA | 4.88 | 0.70 | 0.14 | 0.631 | 0.449 |
| 2016 | COPE | BUF | 3.70 | 0.99 | 0.27 | 0.601 | 0.449 |
| 2016 | APC | JHB | 0.53 | 0.16 | 0.31 | 0.428 | 0.449 |
| 2016 | APC | TSH | 0.46 | 0.24 | 0.53 | 0.418 | 0.449 |
| 2016 | APC | CPT | 0.14 | 0.07 | 0.54 | 0.337 | 0.449 |
| 2016 | APC | ETH | 0.41 | 0.26 | 0.65 | 0.409 | 0.449 |
| 2016 | APC | EKU | 0.68 | 0.27 | 0.39 | 0.447 | 0.449 |
| 2016 | APC | MAN | 0.55 | 0.25 | 0.44 | 0.431 | 0.449 |
| 2016 | APC | NMA | 0.43 | 0.16 | 0.36 | 0.413 | 0.449 |
| 2016 | ALJAMAAH | JHB | 0.27 | 0.31 | 1.15 | 0.381 | 0.449 |
| 2016 | ALJAMAAH | CPT | 0.35 | 0.55 | 1.57 | 0.398 | 0.449 |
| 2016 | AIC | BUF | 3.58 | 3.89 | 1.09 | 0.598 | 0.449 |
| 2021 | EFF | JHB | 10.93 | 10.11 | 0.93 | 0.702 | 0.563 |
| 2021 | EFF | TSH | 11.64 | 10.43 | 0.90 | 0.706 | 0.563 |
| 2021 | EFF | CPT | 3.12 | 4.15 | 1.33 | 0.641 | 0.563 |
| 2021 | EFF | ETH | 3.63 | 10.80 | 2.98 | 0.648 | 0.563 |
| 2021 | EFF | EKU | 11.10 | 13.27 | 1.20 | 0.703 | 0.563 |
| 2021 | EFF | MAN | 8.84 | 11.37 | 1.29 | 0.692 | 0.563 |
| 2021 | EFF | NMA | 5.03 | 6.40 | 1.27 | 0.664 | 0.563 |
| 2021 | EFF | BUF | 8.21 | 12.37 | 1.51 | 0.688 | 0.563 |
| 2021 | AIC | JHB | 1.62 | 0.69 | 0.42 | 0.611 | 0.563 |
| 2021 | AIC | CPT | 0.76 | 0.28 | 0.37 | 0.578 | 0.563 |
| 2021 | AIC | ETH | 1.51 | 1.01 | 0.67 | 0.608 | 0.563 |
| 2021 | AIC | EKU | 1.65 | 1.36 | 0.83 | 0.612 | 0.563 |
| 2021 | AIC | MAN | 2.74 | 0.84 | 0.31 | 0.635 | 0.563 |
| 2021 | AIC | NMA | 1.61 | 0.68 | 0.42 | 0.611 | 0.563 |

## Predictions

| prediction | result | numbers |
|---|---|---|
| R1: \|S − P\| ≤ 0.2 at both targets | PASS | 2016: 0.010; 2021: 0.082 |
| R2: at 2021 both rules predict below 0.9 in ≥ 6 of EFF's 8 metros | PASS | S: 8 of 8; P: 8 of 8 |
| R3: P for use at 2026 (pairs through 2016→21) in [0.4, 1.2] | PASS | 0.854 (76 pairs, 43 parties) |

## Variants (not the pre-registered numbers)

| variant | value |
|---|---|
| 2016: scored on every first→second pair the rule finds (13 parties), S / P | 0.832 / 0.685 |
| 2016: P fitted on parties the SPEC names only | 0.723 |
| 2016: P with "first" read from live files only (adds 7 pairs) | 0.306 |
| 2021: scored on every first→second pair the rule finds (22 parties), S / P | 1.150 / 1.053 |
| 2021: P fitted on parties the SPEC names only | 0.723 |
| 2021: P with "first" read from live files only (adds 7 pairs) | 0.445 |
| 2021: scored on EFF alone (AIC dropped), S / P | 0.670 / 0.859 |
| R3 P without PA | 0.850 |
| R3 P without AIC's per-metro 2016→21 pairs | 0.884 |
| P fitted at target 2021 (pairs through 2011→16) | 0.563 |

## Parties the rule finds beyond the SPEC's list

- **Scorable at 2016, not scored:** CAPE_MUSLIM_CONGRESS, CAPE_PARTY_KAAPSE_PARTY, INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA, MOVEMENT_DEMOCRATIC_PARTY, NATIONAL_PARTY_SOUTH_AFRICA, NATIONAL_PEOPLE_S_PARTY, PAN_AFRICANIST_MOVEMENT, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION, UNITED_RESIDENTS_FRONT
- **Scorable at 2021, not scored:** ACADEMIC_CONGRESS_UNION, AFRICAN_MANDATE_CONGRESS, AFRICAN_MANTUNGWA_COMMUNITY, AGANG, AGENCY_FOR_NEW_AGENDA, ALLIED_MOVEMENT_FOR_CHANGE, BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA, BOTSHABELO_UNEMPLOYED_MOVEMENT, DEMOCRATIC_INDEPENDENT_PARTY, DEMOCRATIC_LIBERAL_CONGRESS, FORUM_4_SERVICE_DELIVERY, INDEPENDENT_PEOPLE_S_PARTY, INTERNATIONAL_REVELATION_CONGRESS, MINORITIES_OF_SOUTH_AFRICA, PEOPLE_S_DEMOCRATIC_MOVEMENT, PEOPLE_S_REVOLUTIONARY_MOVEMENT, SIZWE_UMMAH_NATION, THE_GREENS, UNITED_FRONT_OF_THE_EASTERN_CAPE
- **In P's fit at 2016:** AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE, CHRISTIAN_FRONT, DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA, INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA, OKM, TRULY_ALLIANCE, UNITED_INDEPENDENT_FRONT, UNIVERSAL_PARTY
- **In P's fit at 2021:** AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE, CAPE_MUSLIM_CONGRESS, CAPE_PARTY_KAAPSE_PARTY, CHRISTIAN_FRONT, DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA, INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA, INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA, MOVEMENT_DEMOCRATIC_PARTY, NATIONAL_PARTY_SOUTH_AFRICA, NATIONAL_PEOPLE_S_PARTY, OKM, PAN_AFRICANIST_MOVEMENT, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION, TRULY_ALLIANCE, UNITED_INDEPENDENT_FRONT, UNITED_RESIDENTS_FRONT, UNIVERSAL_PARTY
- **In P's fit for 2026 (R3):** ACADEMIC_CONGRESS_UNION, AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE, AFRICAN_MANDATE_CONGRESS, AFRICAN_MANTUNGWA_COMMUNITY, AGANG, AGENCY_FOR_NEW_AGENDA, ALLIED_MOVEMENT_FOR_CHANGE, BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA, BOTSHABELO_UNEMPLOYED_MOVEMENT, CAPE_MUSLIM_CONGRESS, CAPE_PARTY_KAAPSE_PARTY, CHRISTIAN_FRONT, DEMOCRATIC_INDEPENDENT_PARTY, DEMOCRATIC_LIBERAL_CONGRESS, DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA, FORUM_4_SERVICE_DELIVERY, INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA, INDEPENDENT_PEOPLE_S_PARTY, INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA, INTERNATIONAL_REVELATION_CONGRESS, MINORITIES_OF_SOUTH_AFRICA, MOVEMENT_DEMOCRATIC_PARTY, NATIONAL_PARTY_SOUTH_AFRICA, NATIONAL_PEOPLE_S_PARTY, OKM, PAN_AFRICANIST_MOVEMENT, PEOPLE_S_DEMOCRATIC_MOVEMENT, PEOPLE_S_REVOLUTIONARY_MOVEMENT, SIZWE_UMMAH_NATION, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION, THE_GREENS, TRULY_ALLIANCE, UNITED_FRONT_OF_THE_EASTERN_CAPE, UNITED_INDEPENDENT_FRONT, UNITED_RESIDENTS_FRONT, UNIVERSAL_PARTY

## Departures from the pre-registration's wording

| point | pre-registration | done here | why |
|---|---|---|---|
| first local election | not defined | earliest LGE with a non-zero list share in any metro, read from every file on disk including the held-back 2000 files | a party's having stood is a fact about the ballot; no held-back share enters a ratio |
| 2000 cohort | P at 2016 fitted on "UDM Johannesburg 2000 → 06" | the record starts in 2000, so every party then is left-censored; only UDM kept. DA (formed 2000) is the one excluded party that was new then | follows the table |
| fit sets | "the 2006 first-time parties that stood again in 2011", "the 2011 → 16 pairs" | every first→second pair the rule finds, named or not | plain reading; named-only variant reported |
| scored sets | parties named in the table | exactly those; every other rule-found pair is a variant | the table names them |
| AIC at 2021 | "AIC's 2016 → 21 metros" | metros where AIC's first appearance in that metro is 2016 (per-metro first, AIC only); also in P's 2026 fit | AIC's party-level first is 2011 (Buffalo City), so a party-level rule would not score it. Six metros qualify, not the SPEC's seven: AIC has no 2016 list share in Tshwane (first there in 2021), and Buffalo City's first is 2011 |
| R3 | "P fitted at 2021, for use at 2026" | P on first→second pairs whose later election precedes 2026 (through 2016→21) | "for use at 2026"; the target-2021 fit is reported beside it |
| S at a pair | not stated | the line evaluated at that party's first-election share in that metro | the size the model would see |
