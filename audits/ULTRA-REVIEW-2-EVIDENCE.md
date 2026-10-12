# Pre-emit evidence — ultra review 2

Derived 2026-09-21 from the emitted specs, before the batch is emitted.
`data/**` is gitignored, so this table travels with the pull request in
their place. Regenerate with the script in the PR description.

## Parties whose emitted composition is EXACTLY FLAT across pools

A flat vector is the signature of the arrival path's `np.full(n, 1/n)`:
`_capture_from_share` divides by pool size and `emit_pools` multiplies
back by it, so a flat spread in is a flat composition out. Beside each is
the city's own composition at that spec, which is what the artefact's
`no_measured_vector` note already claims was written.

### `data/processed/buffalocity/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| PEOPLES_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00707 | no measured vector |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00691 | no measured vector |
| **the city itself** | 0.8032 | 0.0535 | 0.0019 | 0.1414 | | votes cast at the top of each pool's turnout band |

### `data/processed/buffalocity/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00115 | no measured vector |
| AFRICAN_MULTICULTURAL_ECONOMIC_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00148 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00144 | no measured vector |
| ARUSHA_ECONOMIC_COALITION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00115 | no measured vector |
| BATHO_PELE_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00138 | no measured vector |
| CAPE_COLOURED_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00118 | no measured vector |
| CIVIC_INDEPENDENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00115 | no measured vector |
| GOD_SAVE_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00123 | no measured vector |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00113 | no measured vector |
| PA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00113 | no measured vector |
| PROGRESSIVE_COMMUNITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00113 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00144 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00144 | no measured vector |
| **the city itself** | 0.7528 | 0.0582 | 0.0344 | 0.1546 | | votes cast at the top of each pool's turnout band |

### `data/processed/capetown/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| AL_SHURA_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00081 | no measured vector |
| CHRISTIAN_DEMOCRATIC_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| COLOURED_VOICE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00082 | no measured vector |
| DEMOCRATIC_INDEPENDENT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00084 | no measured vector |
| INDEPENDENT_SPORT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| KHOISAN_KINGDOM_AND_ALL_PEOPLE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| KHOISAN_REVOLUTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| LOCAL_PEOPLE_S_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| NATIONALIST_COLOURED_PARTY_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00084 | no measured vector |
| PATRIOTIC_ASSOCIATION_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00091 | no measured vector |
| PEOPLE_S_DEMOCRATIC_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| SIZWE_UMMAH_NATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| SOUTH_AFRICAN_PEOPLE_FOR_EQUALITY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| SOUTH_AFRICA_PEOPLE_S_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| THE_GREENS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| UBUNTU_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00087 | no measured vector |
| **the city itself** | 0.2852 | 0.4036 | 0.0978 | 0.2134 | | votes cast at the top of each pool's turnout band |

### `data/processed/capetown/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| AFRICAN_FREEDOM_REVOLUTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00065 | no measured vector |
| AFRICAN_ISLAMIC_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00066 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| BLACK_FIRST_LAND_FIRST | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00054 | no measured vector |
| CAPE_COLOURED_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| CHRISTIANS_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00051 | no measured vector |
| COMPATRIOTS_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00052 | no measured vector |
| CREDIBLE_ALTERNATIVE_1ST_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00077 | no measured vector |
| DEMOCRATIC_EQUALITY_EMPOWERMENT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00052 | no measured vector |
| DEMOCRATIC_LABOUR_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| DEMOCRATIC_PEOPLE_S_ALTERNATIVE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| DEMOCRATIC_PEOPLE_S_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00051 | no measured vector |
| EASTERN_CAPE_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00052 | no measured vector |
| ECONOMIC_EMANCIPATION_FORUM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| GOD_SAVE_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00051 | no measured vector |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00051 | no measured vector |
| INTERNATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00051 | no measured vector |
| IQELA_LENTSANGO_DAGGA_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| KHOI_SAN_KINGDOM_OF_RSA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00052 | no measured vector |
| ONE_MOVEMENT_FOR_CAPE_TOWN | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| OUR_NATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00065 | no measured vector |
| SPECTRUM_NATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| UNITED_PROGRESSIVE_PARTY_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| UNITED_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00065 | no measured vector |
| **the city itself** | 0.2705 | 0.3958 | 0.0883 | 0.2454 | | votes cast at the top of each pool's turnout band |

### `data/processed/ekurhuleni/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ACADEMIC_CONGRESS_UNION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00055 | no measured vector |
| AFRICAN_PEOPLE_S_SOCIALIST_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00134 | no measured vector |
| AIC | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00125 | no measured vector |
| ALJAMAAH | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00137 | no measured vector |
| BUILDING_A_COHESIVE_SOCIETY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00137 | no measured vector |
| EKURHULENI_COMMUNITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00129 | no measured vector |
| INTERNATIONAL_REVELATION_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00137 | no measured vector |
| PALMRIDGE_COMMUNITY_FORUM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00137 | no measured vector |
| PAN_AFRICAN_SOCIALIST_MOVEMENT_OF_AZANIA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00137 | no measured vector |
| UNITED_FRONT_OF_CIVICS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00137 | no measured vector |
| UNITED_RESIDENTS_FRONT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00134 | no measured vector |
| **the city itself** | 0.7079 | 0.0290 | 0.0288 | 0.2342 | | votes cast at the top of each pool's turnout band |

### `data/processed/ekurhuleni/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00082 | no measured vector |
| ABLE_LEADERSHIP | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00079 | no measured vector |
| AFRICAN_FREEDOM_REVOLUTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00083 | no measured vector |
| AFRICAN_PEOPLE_S_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00100 | no measured vector |
| AFRICAN_SECURITY_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00083 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00104 | no measured vector |
| ARUSHA_ECONOMIC_COALITION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00083 | no measured vector |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00082 | no measured vector |
| CHANGE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00104 | no measured vector |
| DEMOCRATIC_UNION_PLUS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00069 | no measured vector |
| GOD_SAVE_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00089 | no measured vector |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00104 | no measured vector |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00085 | no measured vector |
| SPECTRUM_NATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00084 | no measured vector |
| THE_NATIONALS_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00104 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00104 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00105 | no measured vector |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00098 | no measured vector |
| **the city itself** | 0.6638 | 0.0421 | 0.0292 | 0.2649 | | votes cast at the top of each pool's turnout band |

### `data/processed/ethekwini/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ACADEMIC_CONGRESS_UNION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00097 | no measured vector |
| AFRICAN_MANTUNGWA_COMMUNITY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00059 | no measured vector |
| AIC | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00097 | no measured vector |
| ALJAMAAH | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00097 | no measured vector |
| ALLIED_MOVEMENT_FOR_CHANGE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00150 | no measured vector |
| DEMOCRATIC_LIBERAL_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00097 | no measured vector |
| INDEPENDENT_PEOPLE_S_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00095 | no measured vector |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00097 | no measured vector |
| MINORITIES_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00103 | no measured vector |
| PEOPLE_S_REVOLUTIONARY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00100 | no measured vector |
| SOUTH_AFRICAN_POLITICAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00103 | no measured vector |
| THE_PROMISE_OF_FREEDOM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00108 | no measured vector |
| UNITED_PEOPLES_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00097 | no measured vector |
| UNITED_RESIDENTS_FRONT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00100 | no measured vector |
| **the city itself** | 0.6789 | 0.0319 | 0.1836 | 0.1057 | | votes cast at the top of each pool's turnout band |

### `data/processed/ethekwini/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00068 | no measured vector |
| ACTIVE_CITIZENS_COALITION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00095 | no measured vector |
| ACTIVISTS_MOVEMENT_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00070 | no measured vector |
| ADVANCED_DYNAMIC_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00067 | no measured vector |
| AFRICAN_BASIC_REPUBLICANS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00060 | no measured vector |
| AFRICAN_DEMOCRATIC_CHANGE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00069 | no measured vector |
| AFRICAN_FEDERAL_CONVENTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00056 | no measured vector |
| AFRICAN_FREEDOM_REVOLUTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| AFRICAN_PEOPLE_FIRST | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00069 | no measured vector |
| AFRICAN_PEOPLE_S_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00069 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00070 | no measured vector |
| CAPE_COLOURED_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00056 | no measured vector |
| DEMOCRATIC_PEOPLE_S_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00071 | no measured vector |
| FEDERAL_PARTY_SA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00041 | no measured vector |
| FORUM_4_SERVICE_DELIVERY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00056 | no measured vector |
| GOD_SAVE_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00055 | no measured vector |
| INTERNATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00056 | no measured vector |
| KZN_INDEPENDENCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00070 | no measured vector |
| LAND_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00056 | no measured vector |
| PA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00055 | no measured vector |
| PEOPLE_S_FREEDOM_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00070 | no measured vector |
| SPECTRUM_NATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00055 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00070 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00070 | no measured vector |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00071 | no measured vector |
| UNITED_CULTURAL_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00054 | no measured vector |
| **the city itself** | 0.6616 | 0.0280 | 0.1991 | 0.1113 | | votes cast at the top of each pool's turnout band |

### `data/processed/mangaung/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| AGENCY_FOR_NEW_AGENDA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00352 | no measured vector |
| AIC | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00343 | no measured vector |
| AZANIAN_ALLIANCE_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00352 | no measured vector |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00352 | no measured vector |
| **the city itself** | 0.7112 | 0.0527 | 0.0041 | 0.2320 | | votes cast at the top of each pool's turnout band |

### `data/processed/mangaung/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| AFRICA_S_NEW_DAWN | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00257 | no measured vector |
| FORUM_4_SERVICE_DELIVERY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00181 | no measured vector |
| INTERNATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00219 | no measured vector |
| MANGAUNG_COMMUNITY_FORUM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00219 | no measured vector |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00219 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00274 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00274 | no measured vector |
| **the city itself** | 0.6924 | 0.0613 | 0.0095 | 0.2368 | | votes cast at the top of each pool's turnout band |

### `data/processed/nelsonmandelabay/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| AFRICAN_POWER_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00204 | no measured vector |
| ALTERNATIVE_DEMOCRATS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00217 | no measured vector |
| BUILDING_A_COHESIVE_SOCIETY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00211 | no measured vector |
| INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00122 | no measured vector |
| PA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00121 | no measured vector |
| UBUNTU_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00204 | no measured vector |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00317 | no measured vector |
| **the city itself** | 0.5038 | 0.2436 | 0.0300 | 0.2227 | | votes cast at the top of each pool's turnout band |

### `data/processed/nelsonmandelabay/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00166 | no measured vector |
| ABANTU_INTEGRITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00136 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00136 | no measured vector |
| COMPATRIOTS_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00109 | no measured vector |
| DOP | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00134 | no measured vector |
| GOD_SAVE_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00107 | no measured vector |
| INDEPENDENT_CIVIC_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00108 | no measured vector |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00100 | no measured vector |
| MANDELA_BAY_COMMUNITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00107 | no measured vector |
| NORTHERN_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00136 | no measured vector |
| SPECTRUM_NATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00133 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00136 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00136 | no measured vector |
| **the city itself** | 0.4548 | 0.2399 | 0.0347 | 0.2707 | | votes cast at the top of each pool's turnout band |

### `data/processed/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| AFRICAN_PEOPLE_S_SOCIALIST_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00124 | no measured vector |
| AIC | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00124 | no measured vector |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00134 | no measured vector |
| BUILDING_A_COHESIVE_SOCIETY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00127 | no measured vector |
| INTERNATIONAL_REVELATION_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00127 | no measured vector |
| PATRIOTIC_ASSOCIATION_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00127 | no measured vector |
| PEOPLE_S_CIVIC_ORGANISATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00129 | no measured vector |
| PREM_PEOPLES_AGENDA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00134 | no measured vector |
| TRULY_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00119 | no measured vector |
| UBUNTU_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00127 | no measured vector |
| UNITED_FRONT_OF_CIVICS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00127 | no measured vector |
| **the city itself** | 0.6149 | 0.0686 | 0.0489 | 0.2676 | | votes cast at the top of each pool's turnout band |

### `data/processed/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABAHLALY_BAAHI | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| ACTIVISTS_MOVEMENT_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00049 | no measured vector |
| AFRICAN_AMBASSADORS_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00056 | no measured vector |
| AFRICAN_FREEDOM_REVOLUTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| AFRICAN_PEOPLE_S_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00058 | no measured vector |
| AFRICAN_SECURITY_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| AGENCY_FOR_NEW_AGENDA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00053 | no measured vector |
| AHC | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| AMALGAMATED_RAINBOW_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00049 | no measured vector |
| BLACK_AND_WHITE_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00037 | no measured vector |
| CHANGE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00061 | no measured vector |
| CIVIC_MOVEMENT_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| COMMUNITY_SOLIDARITY_ASSOCIATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| DEMOCRATIC_ARTISTS_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| DISRUPT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| DOP | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| FORUM_4_SERVICE_DELIVERY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| INTERNATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| JUSTICE_AND_EMPLOYMENT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| PARTY_OF_ACTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00076 | no measured vector |
| PEOPLE_S_FREEDOM_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00050 | no measured vector |
| ROYAL_LOYAL_PROGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| SAKHISIZWE_CONVENTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00037 | no measured vector |
| SHOSHOLOZA_PROGRESSIVE_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00049 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00061 | no measured vector |
| UNITED_CULTURAL_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00049 | no measured vector |
| US_THE_PEOPLE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00049 | no measured vector |
| **the city itself** | 0.5863 | 0.0677 | 0.0520 | 0.2941 | | votes cast at the top of each pool's turnout band |

### `data/processed/pools_2026.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ACTIVE_AFRICAN_CHRISTIANS_UNITED_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| AFRICAN_ECONOMIC_FREEDOM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| AFRICAN_LABOUR_CONVENTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00038 | no measured vector |
| AFRICAN_RENAISSANCE_UNITY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00067 | no measured vector |
| AFRICAN_ROYAL_RAINBOW_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| AFRICAN_UNEMPLOYED_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| AFRIKA_MAYIBUYE_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| AFRIKA_UNITE_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00029 | no measured vector |
| ALLIED_INDEPENDENTS_UMBRELLA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| ALL_CITIZENS_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00036 | no measured vector |
| ALL_NATIVES_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| AZANIAN_GROUND_FORCES | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| CHRIST_KINGDOM_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00029 | no measured vector |
| CIVIC_MOVEMENT_FOR_PROGRESSIVE_CITIZENS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| COMBAT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| COMMUNITY_FIRST_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| ECONOMIC_REDRESS_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00032 | no measured vector |
| EKHETHU_PEOPLES_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| GAP_FIXERS_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00032 | no measured vector |
| GAZA_DEMOCRATIC_FRONT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| ILIZWE_NATHI | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| IMSTAYING | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| KINGDOM_COVENANT_DEMOCRATIC_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00032 | no measured vector |
| KNOW_YOUR_POWER | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| LABOUR_PARTY_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| LAND_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00032 | no measured vector |
| LEKWE_BEPE_KINGDOM_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00029 | no measured vector |
| MAWUSA_MOVEMENT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| MINORITY_FRONT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| MOVEMENT_OF_RESIDENTS_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00031 | no measured vector |
| MOVE_SA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| NATIONAL_DEMOCRATIC_CONVENTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00060 | no measured vector |
| NCC | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| PEOPLE_OF_JOBURG | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| PEOPLE_S_CONSENT_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00025 | no measured vector |
| PEOPLE_S_MOVEMENT_FOR_CHANGE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| PRO_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00045 | no measured vector |
| RESIDENT_DEVELOPMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00025 | no measured vector |
| SERVICE_DELIVERY_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| SOUTH_AFRICAN_PEOPLE_S_CIVIC_ORGANIZATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| TAU_DIA_RORA_CULTURAL_AND_TRADITIONAL_LEKGOTLA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00025 | no measured vector |
| TRUTH_AND_SOLIDARITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| UMPHAKATHI_WARONA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| VUKA_SA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00065 | no measured vector |
| **the city itself** | 0.5537 | 0.0738 | 0.0619 | 0.3106 | | votes cast at the top of each pool's turnout band |

### `data/processed/pools_2026_simulation.json`

| party | Black African | Coloured | Indian/Asian | White | IFP-located | seeded share | note says |
|---|---|---|---|---|---|---|---|
| ACTIVE_AFRICAN_CHRISTIANS_UNITED_MOVEMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00063 | no measured vector |
| AFRICAN_ECONOMIC_FREEDOM | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| AFRICAN_LABOUR_CONVENTION | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00038 | no measured vector |
| AFRICAN_RENAISSANCE_UNITY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00067 | no measured vector |
| AFRICAN_ROYAL_RAINBOW_CONGRESS | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| AFRICAN_UNEMPLOYED_CONGRESS | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| AFRIKA_MAYIBUYE_MOVEMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| AFRIKA_UNITE_CONGRESS | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00029 | no measured vector |
| ALLIED_INDEPENDENTS_UMBRELLA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| ALL_CITIZENS_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00036 | no measured vector |
| ALL_NATIVES_OF_SOUTH_AFRICA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| AZANIAN_GROUND_FORCES | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| CHRIST_KINGDOM_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00029 | no measured vector |
| CIVIC_MOVEMENT_FOR_PROGRESSIVE_CITIZENS | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| COMBAT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| COMMUNITY_FIRST_MOVEMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| ECONOMIC_REDRESS_MOVEMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00032 | no measured vector |
| EKHETHU_PEOPLES_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| GAP_FIXERS_OF_SOUTH_AFRICA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00032 | no measured vector |
| GAZA_DEMOCRATIC_FRONT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| ILIZWE_NATHI | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| IMSTAYING | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| INDEPENDENT_CITIZENS_MOVEMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| KINGDOM_COVENANT_DEMOCRATIC_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00032 | no measured vector |
| KNOW_YOUR_POWER | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| LABOUR_PARTY_OF_SOUTH_AFRICA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| LAND_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00032 | no measured vector |
| LEKWE_BEPE_KINGDOM_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00029 | no measured vector |
| MAWUSA_MOVEMENT_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| MINORITY_FRONT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| MOVEMENT_OF_RESIDENTS_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00031 | no measured vector |
| MOVE_SA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| NATIONAL_DEMOCRATIC_CONVENTION | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00060 | no measured vector |
| NCC | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| PEOPLE_OF_JOBURG | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| PEOPLE_S_CONSENT_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00025 | no measured vector |
| PEOPLE_S_MOVEMENT_FOR_CHANGE | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| PRO_SOUTH_AFRICA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00045 | no measured vector |
| RESIDENT_DEVELOPMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00025 | no measured vector |
| SERVICE_DELIVERY_PARTY | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| SOUTH_AFRICAN_PEOPLE_S_CIVIC_ORGANIZATION | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00063 | no measured vector |
| TAU_DIA_RORA_CULTURAL_AND_TRADITIONAL_LEKGOTLA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00025 | no measured vector |
| TRUTH_AND_SOLIDARITY_MOVEMENT | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00064 | no measured vector |
| UMPHAKATHI_WARONA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00063 | no measured vector |
| VUKA_SA | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.2000 | 0.00065 | no measured vector |
| **the city itself** | 0.4868 | 0.0703 | 0.0597 | 0.3012 | 0.0820 | | votes cast at the top of each pool's turnout band |

### `data/processed/tshwane/pools_2016.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| AFRICAN_MANDATE_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00312 | no measured vector |
| AFRICAN_PEOPLE_S_SOCIALIST_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00325 | no measured vector |
| FORUM_4_SERVICE_DELIVERY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00423 | no measured vector |
| UNITED_FRONT_OF_CIVICS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00338 | no measured vector |
| **the city itself** | 0.6165 | 0.0253 | 0.0037 | 0.3545 | | votes cast at the top of each pool's turnout band |

### `data/processed/tshwane/pools_2021.json`

| party | Black African | Coloured | Indian/Asian | White | seeded share | note says |
|---|---|---|---|---|---|---|
| ABANTU_BATHO_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| ACTIVE_MOVEMENT_FOR_CHANGE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| ACTIVISTS_MOVEMENT_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00066 | no measured vector |
| AFRICA_RESTORATION_ALLIANCE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00078 | no measured vector |
| AGENCY_FOR_NEW_AGENDA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00067 | no measured vector |
| ARUSHA_ECONOMIC_COALITION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| CAPE_COLOURED_CONGRESS | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| CONCERN | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| DEMOCRATIC_ARTISTS_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| DISABILITY_AND_OLDER_PERSON_POLITICAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| DOP | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00079 | no measured vector |
| FEDERAL_PARTY_SA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00078 | no measured vector |
| GOD_SAVE_AFRICA | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00064 | no measured vector |
| KHOISAN_KINGDOM_AND_ALL_PEOPLE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| PARTY_OF_ACTION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00079 | no measured vector |
| POELANO_REVELATION_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| RCT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00078 | no measured vector |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00046 | no measured vector |
| SPECTRUM_NATIONAL_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00088 | no measured vector |
| THE_ORGANIC_HUMANITY_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00078 | no measured vector |
| THE_PEOPLE_S_VOICE | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| UIM | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00062 | no measured vector |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| UNITED_CULTURAL_MOVEMENT | 0.2500 | 0.2500 | 0.2500 | 0.2500 | 0.00063 | no measured vector |
| **the city itself** | 0.5896 | 0.0262 | 0.0172 | 0.3671 | | votes cast at the top of each pool's turnout band |

## Every spec's city composition, for comparison

| spec | Black African | Coloured | Indian/Asian | White |
|---|---|---|---|---|
| `data/processed/buffalocity/pools_2011.json` | 0.9164 | 0.0028 | 0.0046 | 0.0762 |
| `data/processed/buffalocity/pools_2016.json` | 0.8032 | 0.0535 | 0.0019 | 0.1414 |
| `data/processed/buffalocity/pools_2021.json` | 0.7528 | 0.0582 | 0.0344 | 0.1546 |
| `data/processed/capetown/pools_2011.json` | 0.3345 | 0.3386 | 0.1087 | 0.2182 |
| `data/processed/capetown/pools_2016.json` | 0.2852 | 0.4036 | 0.0978 | 0.2134 |
| `data/processed/capetown/pools_2021.json` | 0.2705 | 0.3958 | 0.0883 | 0.2454 |
| `data/processed/ekurhuleni/pools_2011.json` | 0.7274 | 0.0390 | 0.0229 | 0.2107 |
| `data/processed/ekurhuleni/pools_2016.json` | 0.7079 | 0.0290 | 0.0288 | 0.2342 |
| `data/processed/ekurhuleni/pools_2021.json` | 0.6638 | 0.0421 | 0.0292 | 0.2649 |
| `data/processed/ethekwini/pools_2011.json` | 0.6903 | 0.0274 | 0.1725 | 0.1098 |
| `data/processed/ethekwini/pools_2016.json` | 0.6789 | 0.0319 | 0.1836 | 0.1057 |
| `data/processed/ethekwini/pools_2021.json` | 0.6616 | 0.0280 | 0.1991 | 0.1113 |
| `data/processed/mangaung/pools_2011.json` | 0.7805 | 0.0242 | 0.0000 | 0.1953 |
| `data/processed/mangaung/pools_2016.json` | 0.7112 | 0.0527 | 0.0041 | 0.2320 |
| `data/processed/mangaung/pools_2021.json` | 0.6924 | 0.0613 | 0.0095 | 0.2368 |
| `data/processed/nelsonmandelabay/pools_2011.json` | 0.6267 | 0.1604 | 0.0271 | 0.1858 |
| `data/processed/nelsonmandelabay/pools_2016.json` | 0.5038 | 0.2436 | 0.0300 | 0.2227 |
| `data/processed/nelsonmandelabay/pools_2021.json` | 0.4548 | 0.2399 | 0.0347 | 0.2707 |
| `data/processed/pools_2011.json` | 0.6400 | 0.0499 | 0.0288 | 0.2813 |
| `data/processed/pools_2016.json` | 0.6149 | 0.0686 | 0.0489 | 0.2676 |
| `data/processed/pools_2021.json` | 0.5863 | 0.0677 | 0.0520 | 0.2941 |
| `data/processed/pools_2026.json` | 0.5537 | 0.0738 | 0.0619 | 0.3106 |
| `data/processed/pools_2026_simulation.json` | 0.4868 | 0.0703 | 0.0597 | 0.3012 | 0.0820 |
| `data/processed/tshwane/pools_2011.json` | 0.6457 | 0.0115 | 0.0031 | 0.3397 |
| `data/processed/tshwane/pools_2016.json` | 0.6165 | 0.0253 | 0.0037 | 0.3545 |
| `data/processed/tshwane/pools_2021.json` | 0.5896 | 0.0262 | 0.0172 | 0.3671 |
| `data/processed/tshwane/pools_2026.json` | 0.5554 | 0.0276 | 0.0217 | 0.3953 |
