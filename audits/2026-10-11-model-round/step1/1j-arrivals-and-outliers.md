# 1j. New parties, splits and outliers: the owner's question tested

The owner's question, 2026-10-12, verbatim: "Remove actionSA and COPE and how many arrivals do you have (vs splits and mergers) and is there a more stable version if we take out outliers. COPE and ActionSA would both need outside input between elections in order to model correctly."

This is a design document. It reads code but edits none, and it writes nothing under `data/`. It runs no model, no `compare_history` and no emit, and it is not sub-delegated. Scripts are in the session scratchpad, `uni3/` (`c1`-`c7.py`, `variant.py`); none is committed. The widths and simulations use v3's machinery and the v3 addendum's two options:

- **A:** the middle width is a straight line between the 1-5% band and the large parties.
- **B:** the middle uses its own 5-20% record.

"Width" is the log-scale spread of a party's draw. "Residual" is how far a real result landed from the model's own centre (v1's frame). **Measured** means computed by those scripts; **sourced** means from a cited document; **argued** means reasoning.

## Summary for the owner

**Counts.** The record behind the widths holds 169 elections in which a party stood in a city's local election for the first time, or for the first time since an absence: 322 metro results across the 2011, 2016 and 2021 backtests.

- Most are small parties with no earlier record anywhere: 123 of the 169.
- Origins are sourced for 18. These are 8 splits from a named party (COPE, EFF, GOOD, ActionSA, the APC twice, Abantu Batho Congress, the UIM), 3 vehicles of known figures with no parent (Agang, the PA twice), and 6 new organisations (the AIC three times, the ATM, the Cape Coloured Congress, the Northern Alliance). The NFP's 2021 re-entry is the 18th.
- The other 151 are small parties whose origin I could not source.
- No merger falls inside the record. The two declared mergers are dated 2025 and 2026.

**Removing COPE and ActionSA does not touch the middle-width choice.** Neither party is an established party between 5% and 20%, which is the population that sets that width. What it changes is the width given to national debutants: from 0.48 to 0.32 for 2026, and from 0.78 to 0.46 for the 2016 backtest. Removing them makes the backtests look better for both options. The middle-party score improves enough under A to go negative, though it still misses the pass mark; under B it still fails.

**It is not a fix, for three reasons:**

1. **The removal reads hindsight.** Both parties are known to be special only after their elections.
2. **Other parties share the property.** About ten party-elections in the record follow a dated founding or split event: Agang, the Cape Coloured Congress, the APC, the PA in 2016, the EFF and GOOD among them. They are spread just as widely (sd 1.77 in log after removing COPE and ActionSA, against 0.8-1.0 for ordinary parties). Agang alone moves the debutant width more than COPE does.
3. **A forecast without a judgement would become too confident.** The parties the owner would set aside are exactly the ones a 2026 forecast must still draw: MK, RISE and BOSA.

**What I recommend instead.** Do not delete such parties; give them their own class. A party whose first election follows a dated, sourced founding event of a declared kind is an "event party". Event parties are measured as a class and get that class's wider width unless a judgement is entered for them. The judgement entry of v3 §11 then replaces the class width with the judged centre and width.

The record says national debutants without such an event behave like established parties (no extra width), while event parties need about 1.5 in log beyond their size width. That is consistent with the owner's reasoning, and it applies to every party the same way.

**Outliers.** Leaving each party out in turn shows which widths are fragile:

- **the debutant width:** removing Agang alone takes it from 0.50 to 0.14;
- **option B's middle width:** removing VF+ takes it from 0.62 to 0.41.

The small-party bands and option A's middle width barely move. A robust version that caps every standardised residual at 2.5 standard deviations, applied to all parties, narrows only the smallest bands. It leaves the middle choice where it was.

---

## 1. Every new-to-city party-election in the width record

**Population.** Every party-election in the three backtest cycles whose party had no result at the previous local election in that city:

- national debutants (`debut_npe`): the party has a result at the preceding national election in that city;
- seeded arrivals (`seed`): no such result.

2006 enters only as the "previous" election for 2011; no 2006 forecast exists to give a residual. The NFP's 2011 arrival is not in the record, because the 2011 runs carried it as the generic `ENTRANT` slot (1h §1.3). Each row's **record category** comes from the raw local results 2000-2021 (`rec.json`, built through `levels._citywide_and_roster`); a row can fall in more than one category across metros. **Origin** comes from the cited source; "not sourced" means I found no source in the repository and did not search for one.

### 1.1 Counts

| count by | category | party-elections | metro results |
|---|---|---|---|
| record category (the category of most of the party's metro results) | no earlier record in any metro or national election | 123 | 208 |
| | first local election in any metro, with a national record | 22 | 66 |
| | new to this city, stood in another metro before | 19 | 38 |
| | returning to this city after an absence | 5 | 10 |
| | **total** | **169** | **322** |
| origin (sourced) | split: founded by people who left a named party | 8 (COPE 2011, APC 2011 and 2021, EFF 2016, ASA 2021, GOOD 2021, Abantu Batho Congress 2021, UIM 2021) | |
| | split party re-entering cities it skipped (NFP 2021) | 1 | |
| | vehicle of known figures, no parent party | 3 (Agang 2016, PA 2016 and 2021) | |
| | new organisation, no parent | 6 (AIC 2011, 2016, 2021; ATM 2021; Cape Coloured Congress 2021; Northern Alliance 2021) | |
| | merger | 0. The declared mergers are FORUM_4_SERVICE_DELIVERY into ActionSA (2025) and GOOD with RISE (2026), both after the record (SOURCES.md, `pools.MERGERS`) | |
| | not sourced | 151 (all with largest realised share and centre under 3%; 136 under 0.5%) | |

The origin column describes the party. Only a party's **first** election after its founding event carries that event: APC 2021 and AIC 2016 and 2021 are later elections of older parties.

### 1.2 The table (sorted by year, then by size)

Columns: party code, year, metros it is new in, record category with metro counts, the largest realised share and largest centre across those metros, origin, source.

| party | year | metros | record category (cases) | largest realised / centre | origin | source |
|---|---|---|---|---|---|---|
| COPE | 2011 | 8 | national record only (8) | 4.88% / 17.09% | split: left ANC (Lekota, Shilowa, 2008) | pools.SPLITS; SOURCES.md |
| AIC | 2011 | 1 | national record only (1) | 3.58% / 0.72% | new organisation: Matatiele boundary protest by former ANC members (2005) | [Wikipedia](https://en.wikipedia.org/wiki/African_Independent_Congress); [SABC](https://www.sabcnews.com/sabcnews/political-party-african-independent-congress/) |
| ALJAMAAH | 2011 | 1 | national record only (1) | 0.35% / 0.86% | not sourced |  |
| APC | 2011 | 7 | national record only (7) | 0.68% / 0.30% | split: left PAC (Godi, PAC deputy leader, 2007 floor-crossing) | [Mail & Guardian 2007](https://mg.co.za/article/2007-09-04-godi-leaves-pac-for-african-peoples-convention); [Wikipedia](https://en.wikipedia.org/wiki/African_People%27s_Convention) |
| NATIONAL_PARTY_SOUTH_AFRICA | 2011 | 1 | national record only (1) | 0.54% / 0.23% | not sourced |  |
| PAN_AFRICANIST_MOVEMENT | 2011 | 1 | national record only (1) | 0.23% / 0.28% | not sourced |  |
| MOVEMENT_DEMOCRATIC_PARTY | 2011 | 1 | national record only (1) | 0.03% / 0.22% | not sourced |  |
| CAPE_PARTY_KAAPSE_PARTY | 2011 | 1 | national record only (1) | 0.13% / 0.16% | not sourced |  |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 2011 | 1 | stood in another metro (1) | 0.08% / 0.10% | not sourced |  |
| AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE | 2011 | 2 | stood in another metro (2) | 0.08% / 0.09% | not sourced |  |
| EFF | 2016 | 8 | national record only (8) | 11.64% / 9.47% | split: expelled from ANC (Malema, ANCYL leadership, 2012-13) | pools.SPLITS |
| AIC | 2016 | 6 | stood in another metro (6) | 2.74% / 1.11% | new organisation: Matatiele boundary protest by former ANC members (2005) | [Wikipedia](https://en.wikipedia.org/wiki/African_Independent_Congress); [SABC](https://www.sabcnews.com/sabcnews/political-party-african-independent-congress/) |
| AGENCY_FOR_NEW_AGENDA | 2016 | 1 | no record (1) | 1.57% / 0.49% | not sourced |  |
| PEOPLES_ALLIANCE | 2016 | 1 | no record (1) | 0.16% / 0.96% | not sourced |  |
| UNITED_FRONT_OF_THE_EASTERN_CAPE | 2016 | 2 | no record (2) | 0.80% / 0.94% | not sourced |  |
| AGANG | 2016 | 3 | national record only (3) | 0.04% / 0.67% | vehicle of a known figure, no parent (Ramphele, 2013) | [Wikipedia](https://en.wikipedia.org/wiki/Agang_South_Africa); [Britannica](https://www.britannica.com/topic/Agang-SA) |
| FORUM_4_SERVICE_DELIVERY | 2016 | 1 | no record (1) | 0.04% / 0.55% | not sourced for 2016; merged into ActionSA in 2025 | SOURCES.md (mergers) |
| AZANIAN_ALLIANCE_CONGRESS | 2016 | 1 | no record (1) | 0.13% / 0.49% | not sourced |  |
| BOTSHABELO_UNEMPLOYED_MOVEMENT | 2016 | 1 | no record (1) | 0.12% / 0.49% | not sourced |  |
| UNITED_FRONT_OF_CIVICS | 2016 | 3 | no record (3) | 0.02% / 0.44% | not sourced |  |
| DEMOCRATIC_LIBERAL_CONGRESS | 2016 | 1 | no record (1) | 0.43% / 0.14% | not sourced |  |
| AFRICAN_PEOPLE_S_SOCIALIST_PARTY | 2016 | 3 | no record (3) | 0.02% / 0.43% | not sourced |  |
| AFRICAN_MANDATE_CONGRESS | 2016 | 1 | no record (1) | 0.09% / 0.41% | not sourced |  |
| PA | 2016 | 5 | national record only (4); no record (1) | 0.29% / 0.19% | new organisation around known figures, no parent (McKenzie, Kunene, 2013) | [News24 2013](https://www.news24.com/southafrica/news/cape-gangsters-form-political-party-20131201); [Wikipedia](https://en.wikipedia.org/wiki/Patriotic_Alliance) |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 2016 | 1 | returning (1) | 0.28% / 0.25% | not sourced |  |
| ALTERNATIVE_DEMOCRATS | 2016 | 1 | no record (1) | 0.25% / 0.28% | not sourced |  |
| DEMOCRATIC_INDEPENDENT_PARTY | 2016 | 1 | no record (1) | 0.28% / 0.10% | not sourced |  |
| BUILDING_A_COHESIVE_SOCIETY | 2016 | 3 | no record (3) | 0.03% / 0.27% | not sourced |  |
| MINORITIES_OF_SOUTH_AFRICA | 2016 | 1 | no record (1) | 0.27% / 0.15% | not sourced |  |
| AFRICAN_POWER_MOVEMENT | 2016 | 1 | no record (1) | 0.03% / 0.27% | not sourced |  |
| UBUNTU_PARTY | 2016 | 3 | no record (3) | 0.04% / 0.27% | not sourced |  |
| ALLIED_MOVEMENT_FOR_CHANGE | 2016 | 1 | no record (1) | 0.08% / 0.21% | not sourced |  |
| UNITED_CONGRESS | 2016 | 1 | national record only (1) | 0.10% / 0.19% | not sourced |  |
| ALJAMAAH | 2016 | 2 | stood in another metro (2) | 0.18% / 0.19% | not sourced |  |
| INTERNATIONAL_REVELATION_CONGRESS | 2016 | 2 | no record (2) | 0.03% / 0.19% | not sourced |  |
| PALMRIDGE_COMMUNITY_FORUM | 2016 | 1 | no record (1) | 0.03% / 0.19% | not sourced |  |
| PAN_AFRICAN_SOCIALIST_MOVEMENT_OF_AZANIA | 2016 | 1 | no record (1) | 0.03% / 0.19% | not sourced |  |
| UNITED_RESIDENTS_FRONT | 2016 | 2 | stood in another metro (2) | 0.03% / 0.18% | not sourced |  |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 2016 | 1 | no record (1) | 0.00% / 0.18% | not sourced |  |
| PREM_PEOPLES_AGENDA | 2016 | 1 | no record (1) | 0.01% / 0.18% | not sourced |  |
| EKURHULENI_COMMUNITY_MOVEMENT | 2016 | 1 | no record (1) | 0.04% / 0.18% | not sourced |  |
| AFRICAN_MANTUNGWA_COMMUNITY | 2016 | 1 | no record (1) | 0.18% / 0.08% | not sourced |  |
| PEOPLE_S_CIVIC_ORGANISATION | 2016 | 1 | stood in another metro (1) | 0.01% / 0.17% | not sourced |  |
| PATRIOTIC_ASSOCIATION_OF_SOUTH_AFRICA | 2016 | 2 | no record (2) | 0.05% / 0.17% | not sourced |  |
| PEOPLE_S_REVOLUTIONARY_MOVEMENT | 2016 | 1 | no record (1) | 0.17% / 0.14% | not sourced |  |
| TRULY_ALLIANCE | 2016 | 1 | stood in another metro (1) | 0.08% / 0.16% | not sourced |  |
| INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA | 2016 | 1 | stood in another metro (1) | 0.12% / 0.16% | not sourced |  |
| THE_PROMISE_OF_FREEDOM | 2016 | 1 | no record (1) | 0.02% / 0.15% | not sourced |  |
| PAC | 2016 | 1 | returning (1) | 0.09% / 0.15% | not sourced |  |
| SOUTH_AFRICAN_POLITICAL_PARTY | 2016 | 1 | no record (1) | 0.03% / 0.15% | not sourced |  |
| ACADEMIC_CONGRESS_UNION | 2016 | 2 | no record (2) | 0.04% / 0.14% | not sourced |  |
| INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA | 2016 | 1 | stood in another metro (1) | 0.04% / 0.14% | not sourced |  |
| UNITED_PEOPLES_PARTY | 2016 | 1 | no record (1) | 0.13% / 0.14% | not sourced |  |
| INDEPENDENT_PEOPLE_S_PARTY | 2016 | 1 | no record (1) | 0.14% / 0.14% | not sourced |  |
| AZAPO | 2016 | 1 | returning (1) | 0.03% / 0.12% | not sourced |  |
| CHRISTIAN_DEMOCRATIC_PARTY | 2016 | 1 | stood in another metro (1) | 0.09% / 0.11% | not sourced |  |
| INDEPENDENT_SPORT_PARTY | 2016 | 1 | no record (1) | 0.01% / 0.11% | not sourced |  |
| KHOISAN_KINGDOM_AND_ALL_PEOPLE | 2016 | 1 | no record (1) | 0.04% / 0.11% | not sourced |  |
| KHOISAN_REVOLUTION | 2016 | 1 | no record (1) | 0.04% / 0.11% | not sourced |  |
| LOCAL_PEOPLE_S_PARTY | 2016 | 1 | no record (1) | 0.08% / 0.11% | not sourced |  |
| PEOPLE_S_DEMOCRATIC_MOVEMENT | 2016 | 1 | no record (1) | 0.02% / 0.11% | not sourced |  |
| SIZWE_UMMAH_NATION | 2016 | 1 | no record (1) | 0.02% / 0.11% | not sourced |  |
| SOUTH_AFRICAN_PEOPLE_FOR_EQUALITY | 2016 | 1 | no record (1) | 0.01% / 0.11% | not sourced |  |
| SOUTH_AFRICA_PEOPLE_S_PARTY | 2016 | 1 | no record (1) | 0.04% / 0.11% | not sourced |  |
| THE_GREENS | 2016 | 1 | no record (1) | 0.03% / 0.11% | not sourced |  |
| NATIONALIST_COLOURED_PARTY_OF_SOUTH_AFRICA | 2016 | 1 | no record (1) | 0.05% / 0.10% | not sourced |  |
| COLOURED_VOICE | 2016 | 1 | no record (1) | 0.04% / 0.10% | not sourced |  |
| AL_SHURA_PARTY | 2016 | 1 | no record (1) | 0.05% / 0.10% | not sourced |  |
| ASA | 2021 | 4 | no record (4) | 18.12% / 6.71% | split: left DA (Mashaba, former Johannesburg mayor, 2019); vehicle of a known figure | pools.SPLITS; SOURCES.md |
| GOOD | 2021 | 6 | national record only (6) | 3.68% / 3.19% | split: left DA (De Lille, former Cape Town mayor, 2018) | pools.SPLITS |
| CAPE_COLOURED_CONGRESS | 2021 | 4 | no record (4) | 2.83% / 0.17% | new organisation (Fadiel Adams, 2020) | [Wikipedia](https://en.wikipedia.org/wiki/National_Coloured_Congress) |
| NORTHERN_ALLIANCE | 2021 | 1 | no record (1) | 2.09% / 0.18% | new community organisation, Nelson Mandela Bay northern areas (2020) | [HeraldLIVE 2021](https://www.heraldlive.co.za/news/politics/2021-11-08-northern-alliance-at-centre-of-coalition-talks/); [Polity 2024](https://polity.org.za/article/gbeberha-based-national-alliance-formerly-northern-alliance-throws-its-weight-behind-good-for-2024-election-2024-05-20) |
| PA | 2021 | 3 | stood in another metro (3) | 1.78% / 1.76% | new organisation around known figures, no parent (McKenzie, Kunene, 2013) | [News24 2013](https://www.news24.com/southafrica/news/cape-gangsters-form-political-party-20131201); [Wikipedia](https://en.wikipedia.org/wiki/Patriotic_Alliance) |
| DOP | 2021 | 3 | no record (3) | 1.38% / 0.18% | not sourced |  |
| AFRIKAN_ALLIANCE_OF_SOCIAL_DEMOCRATS | 2021 | 1 | national record only (1) | 1.26% / 0.37% | not sourced |  |
| ABANTU_INTEGRITY_MOVEMENT | 2021 | 1 | no record (1) | 1.11% / 0.18% | not sourced |  |
| ATM | 2021 | 8 | national record only (8) | 0.89% / 1.00% | new organisation: political arm of a church council (2018) | [Wikipedia](https://en.wikipedia.org/wiki/African_Transformation_Movement); [Daily Maverick 2019](https://www.dailymaverick.co.za/article/2019-05-06-prophecy-or-political-party-the-atm-a-church-jacob-zuma-a-50-year-history/) |
| AIC | 2021 | 1 | stood in another metro (1) | 0.81% / 0.62% | new organisation: Matatiele boundary protest by former ANC members (2005) | [Wikipedia](https://en.wikipedia.org/wiki/African_Independent_Congress); [SABC](https://www.sabcnews.com/sabcnews/political-party-african-independent-congress/) |
| ACTIVE_CITIZENS_COALITION | 2021 | 1 | no record (1) | 0.81% / 0.13% | not sourced |  |
| ABANTU_BATHO_CONGRESS | 2021 | 7 | no record (7) | 0.65% / 0.22% | split: left NFP (Mavundla, NFP councillor, 2020) | [City Press 2021](https://www.news24.com/citypress/politics/abantu-batho-congress-gets-tough-20210109); [Wikipedia](https://en.wikipedia.org/wiki/Abantu_Batho_Congress) |
| AFRICA_RESTORATION_ALLIANCE | 2021 | 7 | no record (7) | 0.64% / 0.20% | not sourced |  |
| CAPE_INDEPENDENCE_PARTY_KAAPSE_ONAFHANKLIKHEIDS_PARTY | 2021 | 1 | no record (1) | 0.62% / 0.08% | not sourced |  |
| JUSTICE_AND_EMPLOYMENT_PARTY | 2021 | 2 | no record (1); national record only (1) | 0.61% / 0.31% | not sourced |  |
| UIM | 2021 | 8 | no record (8) | 0.56% / 0.37% | vehicle of a known figure who left ANC (de Beer, 2020) | [Cape Argus 2020](https://capeargus.co.za/capetimes/news/2020-10-02-maimane-former-mk-agent-de-beer-join-forces-in-united-independent-movement); [Wikipedia](https://en.wikipedia.org/wiki/United_Independent_Movement) |
| VFPLUS | 2021 | 1 | stood in another metro (1) | 0.52% / 0.43% | not sourced |  |
| NFP | 2021 | 7 | returning (5); stood in another metro (2) | 0.36% / 0.51% | split from IFP (2011); here re-entering cities it skipped in 2016 | pools.SPLITS |
| AFRICAN_DEMOCRATIC_CHANGE | 2021 | 1 | no record (1) | 0.45% / 0.09% | not sourced |  |
| INDEPENDENT_CITIZENS_MOVEMENT | 2021 | 1 | no record (1) | 0.45% / 0.14% | not sourced |  |
| AHC | 2021 | 1 | no record (1) | 0.43% / 0.08% | not sourced |  |
| THE_ORGANIC_HUMANITY_MOVEMENT | 2021 | 8 | no record (8) | 0.10% / 0.37% | not sourced |  |
| AFRICA_S_NEW_DAWN | 2021 | 1 | no record (1) | 0.13% / 0.35% | not sourced |  |
| INDEPENDENT_SOUTH_AFRICAN_NATIONAL_CIVIC_ORGANISATION | 2021 | 4 | no record (4) | 0.34% / 0.16% | not sourced |  |
| BLACK_FIRST_LAND_FIRST | 2021 | 5 | national record only (4); no record (1) | 0.12% / 0.30% | not sourced |  |
| INTERNATIONAL_PARTY | 2021 | 4 | no record (4) | 0.08% / 0.29% | not sourced |  |
| MANGAUNG_COMMUNITY_FORUM | 2021 | 1 | no record (1) | 0.21% / 0.29% | not sourced |  |
| SOUTH_AFRICAN_ROYAL_KINGDOMS_ORGANIZATION | 2021 | 3 | no record (3) | 0.03% / 0.29% | not sourced |  |
| AFRICAN_PEOPLE_FIRST | 2021 | 1 | no record (1) | 0.28% / 0.09% | not sourced |  |
| KZN_INDEPENDENCE | 2021 | 1 | no record (1) | 0.27% / 0.10% | not sourced |  |
| AFRICAN_MULTICULTURAL_ECONOMIC_CONGRESS | 2021 | 1 | no record (1) | 0.26% / 0.21% | not sourced |  |
| FORUM_4_SERVICE_DELIVERY | 2021 | 3 | stood in another metro (3) | 0.16% / 0.24% | not sourced for 2016; merged into ActionSA in 2025 | SOURCES.md (mergers) |
| ALJAMAAH | 2021 | 3 | stood in another metro (3) | 0.22% / 0.20% | not sourced |  |
| APC | 2021 | 1 | stood in another metro (1) | 0.12% / 0.21% | split: left PAC (Godi, PAC deputy leader, 2007 floor-crossing) | [Mail & Guardian 2007](https://mg.co.za/article/2007-09-04-godi-leaves-pac-for-african-peoples-convention); [Wikipedia](https://en.wikipedia.org/wiki/African_People%27s_Convention) |
| PEOPLE_S_FREEDOM_PARTY | 2021 | 2 | no record (2) | 0.20% / 0.10% | not sourced |  |
| BATHO_PELE_MOVEMENT | 2021 | 1 | no record (1) | 0.10% / 0.19% | not sourced |  |
| AFRICAN_COVENANT | 2021 | 2 | national record only (2) | 0.07% / 0.17% | not sourced |  |
| SPECTRUM_NATIONAL_PARTY | 2021 | 5 | no record (5) | 0.05% / 0.17% | not sourced |  |
| GOD_SAVE_AFRICA | 2021 | 6 | no record (6) | 0.08% / 0.17% | not sourced |  |
| ARUSHA_ECONOMIC_COALITION | 2021 | 3 | no record (3) | 0.08% / 0.16% | not sourced |  |
| CIVIC_INDEPENDENT | 2021 | 1 | no record (1) | 0.04% / 0.16% | not sourced |  |
| PROGRESSIVE_COMMUNITY_MOVEMENT | 2021 | 1 | no record (1) | 0.13% / 0.16% | not sourced |  |
| MANDELA_BAY_COMMUNITY_MOVEMENT | 2021 | 1 | no record (1) | 0.15% / 0.14% | not sourced |  |
| COMPATRIOTS_OF_SOUTH_AFRICA | 2021 | 2 | no record (2) | 0.10% / 0.14% | not sourced |  |
| INDEPENDENT_CIVIC_MOVEMENT | 2021 | 1 | no record (1) | 0.06% / 0.14% | not sourced |  |
| CREDIBLE_ALTERNATIVE_1ST_MOVEMENT | 2021 | 1 | no record (1) | 0.14% / 0.10% | not sourced |  |
| CHANGE | 2021 | 2 | no record (2) | 0.05% / 0.14% | not sourced |  |
| THE_NATIONALS_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.08% / 0.14% | not sourced |  |
| AFRICAN_PEOPLE_S_MOVEMENT | 2021 | 3 | no record (3) | 0.06% / 0.13% | not sourced |  |
| ONE_MOVEMENT_FOR_CAPE_TOWN | 2021 | 1 | no record (1) | 0.13% / 0.06% | not sourced |  |
| RCT | 2021 | 1 | no record (1) | 0.13% / 0.10% | not sourced |  |
| UNITED_CHRISTIAN_DEMOCRATIC_PARTY | 2021 | 3 | returning (2); stood in another metro (1) | 0.10% / 0.13% | not sourced |  |
| PARTY_OF_ACTION | 2021 | 2 | no record (2) | 0.13% / 0.10% | not sourced |  |
| AFRICAN_FREEDOM_REVOLUTION | 2021 | 4 | no record (4) | 0.11% / 0.11% | not sourced |  |
| AFRICAN_SECURITY_CONGRESS | 2021 | 2 | no record (2) | 0.09% / 0.11% | not sourced |  |
| BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA | 2021 | 2 | stood in another metro (2) | 0.01% / 0.11% | not sourced |  |
| NATIONAL_PEOPLE_S_FRONT | 2021 | 2 | national record only (2) | 0.11% / 0.06% | not sourced |  |
| ABLE_LEADERSHIP | 2021 | 1 | no record (1) | 0.05% / 0.10% | not sourced |  |
| LAND_PARTY | 2021 | 2 | national record only (1); no record (1) | 0.04% / 0.10% | not sourced |  |
| FEDERAL_PARTY_SA | 2021 | 2 | no record (2) | 0.05% / 0.10% | not sourced |  |
| DEMOCRATIC_PEOPLE_S_CONGRESS | 2021 | 1 | no record (1) | 0.04% / 0.10% | not sourced |  |
| ACTIVISTS_MOVEMENT_OF_SOUTH_AFRICA | 2021 | 3 | no record (3) | 0.08% / 0.10% | not sourced |  |
| ADVANCED_DYNAMIC_ALLIANCE | 2021 | 1 | no record (1) | 0.06% / 0.09% | not sourced |  |
| DEMOCRATIC_UNION_PLUS | 2021 | 1 | no record (1) | 0.05% / 0.09% | not sourced |  |
| IQELA_LENTSANGO_DAGGA_PARTY | 2021 | 1 | no record (1) | 0.09% / 0.06% | not sourced |  |
| DEMOCRATIC_LABOUR_PARTY | 2021 | 1 | no record (1) | 0.09% / 0.08% | not sourced |  |
| AFRICAN_PROGRESSIVE_MOVEMENT | 2021 | 1 | national record only (1) | 0.09% / 0.03% | not sourced |  |
| AGENCY_FOR_NEW_AGENDA | 2021 | 2 | stood in another metro (2) | 0.03% / 0.08% | not sourced |  |
| CONCERN | 2021 | 1 | no record (1) | 0.08% / 0.08% | not sourced |  |
| AFRICAN_ISLAMIC_MOVEMENT | 2021 | 1 | no record (1) | 0.06% / 0.08% | not sourced |  |
| AFRICAN_BASIC_REPUBLICANS | 2021 | 1 | no record (1) | 0.03% / 0.08% | not sourced |  |
| OUR_NATION | 2021 | 1 | no record (1) | 0.03% / 0.08% | not sourced |  |
| UNITED_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.06% / 0.08% | not sourced |  |
| DEMOCRATIC_PEOPLE_S_ALTERNATIVE | 2021 | 1 | no record (1) | 0.08% / 0.08% | not sourced |  |
| ACTIVE_MOVEMENT_FOR_CHANGE | 2021 | 1 | no record (1) | 0.00% / 0.08% | not sourced |  |
| DEMOCRATIC_ARTISTS_PARTY | 2021 | 2 | no record (2) | 0.06% / 0.08% | not sourced |  |
| DISABILITY_AND_OLDER_PERSON_POLITICAL_PARTY | 2021 | 1 | no record (1) | 0.00% / 0.08% | not sourced |  |
| POELANO_REVELATION_PARTY | 2021 | 1 | no record (1) | 0.02% / 0.08% | not sourced |  |
| UNITED_CULTURAL_MOVEMENT | 2021 | 3 | no record (3) | 0.04% / 0.08% | not sourced |  |
| ECONOMIC_EMANCIPATION_FORUM | 2021 | 3 | national record only (2); no record (1) | 0.06% / 0.08% | not sourced |  |
| UNITED_PROGRESSIVE_PARTY_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.06% / 0.08% | not sourced |  |
| THE_PEOPLE_S_VOICE | 2021 | 1 | no record (1) | 0.05% / 0.08% | not sourced |  |
| ROYAL_LOYAL_PROGRESS | 2021 | 1 | no record (1) | 0.02% / 0.08% | not sourced |  |
| SHOSHOLOZA_PROGRESSIVE_PARTY | 2021 | 1 | no record (1) | 0.02% / 0.08% | not sourced |  |
| AFRICAN_FEDERAL_CONVENTION | 2021 | 1 | no record (1) | 0.04% / 0.08% | not sourced |  |
| AFRICAN_AMBASSADORS_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.08% / 0.07% | not sourced |  |
| DEMOCRATIC_EQUALITY_EMPOWERMENT_PARTY | 2021 | 1 | no record (1) | 0.00% / 0.07% | not sourced |  |
| EASTERN_CAPE_MOVEMENT | 2021 | 1 | no record (1) | 0.01% / 0.07% | not sourced |  |
| KHOI_SAN_KINGDOM_OF_RSA | 2021 | 1 | no record (1) | 0.00% / 0.07% | not sourced |  |
| CHRISTIANS_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.00% / 0.06% | not sourced |  |
| DEMOCRATIC_PEOPLE_S_MOVEMENT | 2021 | 1 | no record (1) | 0.06% / 0.06% | not sourced |  |
| ABAHLALY_BAAHI | 2021 | 1 | no record (1) | 0.05% / 0.06% | not sourced |  |
| COMMUNITY_SOLIDARITY_ASSOCIATION | 2021 | 1 | no record (1) | 0.03% / 0.06% | not sourced |  |
| DISRUPT_PARTY | 2021 | 1 | no record (1) | 0.02% / 0.06% | not sourced |  |
| US_THE_PEOPLE | 2021 | 1 | no record (1) | 0.06% / 0.06% | not sourced |  |
| AMALGAMATED_RAINBOW_MOVEMENT | 2021 | 1 | no record (1) | 0.03% / 0.06% | not sourced |  |
| KHOISAN_KINGDOM_AND_ALL_PEOPLE | 2021 | 1 | stood in another metro (1) | 0.00% / 0.06% | not sourced |  |
| CIVIC_MOVEMENT_OF_SOUTH_AFRICA | 2021 | 1 | no record (1) | 0.02% / 0.06% | not sourced |  |
| BLACK_AND_WHITE_PARTY | 2021 | 1 | no record (1) | 0.01% / 0.05% | not sourced |  |
| SAKHISIZWE_CONVENTION | 2021 | 1 | no record (1) | 0.00% / 0.05% | not sourced |  |
| FREE_DEMOCRATS | 2021 | 1 | national record only (1) | 0.01% / 0.03% | not sourced |  |

---

## 2. Widths with COPE and ActionSA removed, and a robust version

### 2.1 What the two parties touch

| party | rows in the width record | class |
|---|---|---|
| COPE | 2011: 8 national-debutant rows. 2016 and 2021: established rows below 1% | debutant increment; small bands |
| ActionSA | 2021: 4 seeded-arrival rows | seed increment, arrival factor |

Neither party has an **established** row between 5% and 20%. So neither enters the 5-20% root (option B) or the 1-5% band and large anchors that build option A's bridge.

### 2.2 Widths (2026 record unless stated; after v2's location fixed point)

The four variants are applied to every party:

- **full:** the record as is;
- **without COPE and ActionSA:** every row of both parties deleted;
- **robust:** each standardised residual capped at ±2.5 inside the offset-aware root. The rule was set before looking and applied to every party and band, not to chosen ones;
- **both:** the deletion and the cap together.

| width | full | without COPE and ActionSA | robust | both | leave-one-party-out range (full record, before the fixed point) | most influential party |
|---|---|---|---|---|---|---|
| 1-5% band | 0.840 | 0.839 | 0.839 | 0.839 | 0.730-0.903 | Agency for New Agenda / PAC |
| 0.3-1% band | 0.822 | 0.824 | 0.821 | 0.823 | 0.767-0.846 | — (none moves it by 0.05) |
| 0.1-0.3% band | 0.901 | 0.908 | 0.846 | 0.852 | 0.775-0.946 | PA |
| under 0.1% band | 0.998 | 1.027 | 0.789 | 0.820 | 0.902-1.024 | PA / COPE |
| 5-20% root (option B's middle anchor) | 0.623 | 0.623 | 0.623 | 0.623 | 0.409-0.671 | **VF+** (Tshwane 2011) / Minority Front |
| A: width at 11.7% | 0.307 | 0.307 | 0.307 | 0.307 | 0.275-0.332 | — |
| B: width at 11.7% | 0.488 | 0.488 | 0.489 | 0.488 | 0.360-0.562 | VF+ / Minority Front |
| national-debutant increment | **0.477** | **0.321** | 0.513 | 0.378 | **0.140-0.610** | **Agang** (to 0.14) / PA |
| same, 2021 record | 0.833 | 0.737 | 0.837 | 0.743 | — | — |
| same, 2016 record (2011 only) | 0.776 | 0.461 | — | — | — | COPE |
| seeded-arrival increment | 0.848 | 0.834 | 0.870 | 0.856 | 0.753-0.951 | Cape Coloured Congress / PA |
| arrival factor | 0.726 | 0.719 | 0.727 | 0.719 | 0.680-0.787 | — |

Leave-one-party-out deletes every row of one party and refits; 177 parties were tried, and the jackknife standard error is in `c3.py`'s output. The most fragile widths are the debutant increment (jackknife se 0.49; twelve parties each move it by more than 0.05) and option B's middle anchor (se 0.22). Option A's middle width is the most stable (se 0.05), because it borrows from the 1-5% band and the large parties.

The robust cap narrows the two smallest bands, where a few tiny parties had extreme residuals. It does not move the middle, which no single residual dominates at that cap. It raises the debutant increment slightly, because the standardisation changes. The cap does not make the debutant width stable.

### 2.3 What changes in the forecast and the backtests

Citywide simulation as in v3 §8: 5,000 draws for Johannesburg 2026, counts the mean of four seeds; backtests 2016 and 2021, intervals by a city-year cluster bootstrap. The must-not-worsen rule for each group is that the 90% upper bound of the score difference against the current model stays at or below +0.05 points.

| | A, full | A, without COPE and ActionSA | A, robust | B, full | B, without COPE and ActionSA | B, robust |
|---|---|---|---|---|---|---|
| JHB 2026 log-sd ANC / ASA / EFF / MK / PA | 0.13 / 0.28 / 0.31 / 0.56 / 0.50 | 0.12 / 0.28 / 0.31 / **0.46** / 0.50 | 0.13 / 0.28 / 0.31 / 0.58 / 0.50 | 0.17 / 0.44 / 0.48 / 0.70 / 0.67 | 0.16 / 0.44 / 0.48 / **0.64** / 0.67 | 0.17 / 0.44 / 0.48 / 0.74 / 0.67 |
| MK p5-p95 (today 2.6-18.1%) | 3.1-19.3% | 3.9-17.2% | 2.9-19.8% | 2.2-22.4% | 2.6-20.9% | 2.1-23.1% |
| draws: established, previous share under 1%, above 5% (today 403) | 22.8 | 23.3 | 22.3 | 24.0 | 23.5 | 23.5 |
| draws: largest new party above 18.12% (today 255) | 325 | **196** | 356 | 471 | 400 | 502 |
| backtests, large parties: score difference [90%]; inside 90% band | −0.171 [−0.316, −0.008]; 30/32 | −0.213 [−0.366, −0.042]; 30/32 | −0.170 [−0.316, −0.007]; 30/32 | −0.158 [−0.286, −0.019]; 31/32 | −0.190 [−0.324, −0.045]; 31/32 | −0.157 [−0.286, −0.017]; 31/32 |
| backtests, middle parties: score difference [90%]; inside 90% band | +0.143 [−0.119, +0.429]; fails | **−0.043 [−0.234, +0.136]; still fails (upper bound above +0.05)** | +0.144 [−0.118, +0.428]; fails | +0.364 [+0.120, +0.667]; fails | +0.236 [+0.055, +0.450]; fails | +0.366 [+0.123, +0.668]; fails |
| wrong-party seats (list proxy), 2016 / 2021 (today 71.8 / 154.9) | 72.6 / 153.1 | 72.4 / 153.1 | 72.6 / 153.1 | 72.7 / 153.2 | 72.6 / 153.3 | 72.7 / 153.2 |

Removing COPE helps the backtest scores through one route. It lowers the 2016 debutant width (0.78 → 0.46), which is the width applied to the EFF in 2016. That row was the cause of the middle-party failure in v3. **This is the backtest scoring itself on knowledge it did not have.** In 2016 the model could not have known to discount COPE's 2011 collapse, unless a rule stated before 2016 classified COPE (§3.3).

---

## 3. The owner's reasoning, tested for consistency

### 3.1 Which parties share the property "needed outside input between elections"

The property, made testable: **the party's first local election in the city follows a dated founding or split event since the previous local election, and the event is in a public source.** That is what made COPE (2008 split) and ActionSA (2019 departure of a mayor) unforecastable from the record.

Parties in the record with that property (first election after the event), and how they landed against their centre:

| party-election | event (sourced, §1.2) | metros | residual range (log) | mean standardised residual (in sd units) |
|---|---|---|---|---|
| COPE 2011 | split from the ANC, 2008 | 8 | −2.33 to −1.38 | −3.64 |
| APC 2011 | split from the PAC, 2007 | 7 | +0.28 to +1.10 | +1.28 |
| EFF 2016 | split from the ANC, 2013 | 8 | +0.15 to +0.44 | +0.61 |
| Agang 2016 | vehicle of a known figure, 2013 | 3 | −3.07 to −2.67 | −3.14 |
| PA 2016 | new organisation around known figures, 2013 | 5 | −0.16 to +1.91 | +1.16 |
| GOOD 2021 | split from the DA, 2018 | 6 | −0.48 to +0.22 | +0.23 |
| ActionSA 2021 | departure of a DA mayor, 2019 | 4 | +0.52 to +1.19 | +1.31 |
| Abantu Batho Congress 2021 | split from the NFP, 2020 | 7 | −1.47 to +2.01 | +0.20 |
| UIM 2021 | vehicle of a former ANC member, 2020 | 8 | −0.82 to +2.03 | +0.98 |
| Cape Coloured Congress 2021 | new organisation, 2020 | 1 | +3.65 | +4.27 |

These ten party-elections (57 metro results), measured as a class:

- weighted mean residual +0.11, sd about the mean 1.73 in log, against a size-based width of 0.83 on average for the same parties;
- without COPE and ActionSA: mean +0.29, sd 1.77;
- the offset-aware estimator finds **no root**: no single mean-preserving log-normal width fits the class. It is a mixture of collapses (COPE, Agang) and surges (Cape Coloured Congress, ActionSA, APC, PA).

**Removing COPE and ActionSA leaves the class just as unpredictable.**

Parties with the same property that the owner did not name:

- **EFF 2016 and GOOD 2021**, which landed close to their centres;
- **Agang 2016**, a collapse that moves the debutant width more than COPE does;
- **in the 2026 forecast: MK** (2023 split from the ANC), **RISE** (founded 2023) and **BOSA** (founded 2022), all national debutants at Johannesburg 2026. These are recalled, not checked in this session; the writer sources them.

National debutants **without** such an event (29 party-elections, 51 results) show no excess width over established parties of the same size: the increment is 0.00. Seeded arrivals without such an event (128 party-elections, 200 results) still need 0.74.

So the record supports the owner's reasoning in its general form. The extra uncertainty of new parties sits in parties formed by a recent dated event, plus the general noise of the many tiny seeded arrivals. It does not support singling out two parties.

**One outlier the property does not catch:** the PA in Johannesburg 2021. It was an established party, centre 0.075%, realised 2.96%, standardised +4.53, the largest positive residual among parties under 20%. Its surge followed a campaign, not a founding event. Any rule of this kind leaves such cases in the record width, which is right: they are the record's evidence that established small parties sometimes jump.

### 3.2 What the record width describes if such parties are removed, and the risk

If event parties are deleted from the record, the debutant and seed widths describe "a new party with no recent founding event". For a forecast where an event party is on the ballot and **no judgement is entered**, that width is too narrow by about 1.5 in log (the class's extra sd beyond its size width). At Johannesburg 2026:

| | MK draw p5-p95 | today (arm E) |
|---|---|---|
| option A, full record | 3.1-19.3% | 2.6-18.1% |
| option A, COPE and ActionSA removed | 3.9-17.2% | 2.6-18.1% |

The removed record says MK is better known than any earlier split was. Nothing in the record supports that. **Deleting understates uncertainty unless a judgement is always entered for every event party**, and nothing enforces that.

### 3.3 Proposed rule: partition, not deletion

One rule, applied to every party, naming none in code:

1. **The event class.** A party-election belongs to it when its first local election in the city follows a founding event since the previous local election, in a closed declared list, with a dated public source in SOURCES.md:
   - (a) founded by sitting or former public representatives who left another party;
   - (b) founded around a person who has held national, provincial or metro office;
   - (c) merger with or absorption of a party that held seats;
   - (d) re-registration under a new name.

   The list lives in a lineage table beside `pools.SPLITS` / `pools.MERGERS` and extends them. It is filled from sources dated before the election, so it is available ex ante. COPE in 2011 and ActionSA in 2021 both qualify on sources that existed before those elections.
2. **Width record.** The writer partitions new parties into three classes, each estimated forward on earlier cycles only:
   - event parties;
   - national debutants without an event;
   - seeded arrivals without an event.

   Each class keeps its increment over the size width, measured from its own rows. No row is deleted.
3. **Draw without a judgement.** An event party with no judgement entry takes the event class's width, in place of its record class's.
4. **Draw with a judgement.** When a judgement is entered (v3 §11), its judged centre and `sigma_j` replace the class increment, as for any party. `sigma_j` is then stated against the size width.
5. **Backtests.** The classification uses only sources dated before the target election. Backtests apply the class widths and never a judgement (v3 §11.2).

**What the record gives each class for 2026** (all three cycles; to be refitted by the writer forward per target):

| class | party-elections / results | extra width over the size width |
|---|---|---|
| event parties | 10 / 57 | no single width fits (no root); sd about the mean 1.73 against a size width of 0.83, i.e. about 1.5 extra |
| national debutants without an event | 29 / 51 | 0.00 |
| seeded arrivals without an event | 128 / 200 | 0.74 |

Ten party-elections is above the design's minimum of 8, but this class is **not described by one mean-preserving log-normal**. Its draw needs either the class sd about the mean, with the class mean bias filed as a level report as the no-root rule says, or a judgement. That is the owner's point, stated as a rule: these parties need outside input. The record width for them is a fallback when none is given, not a claim of knowledge.

**Effect on the middle-width choice.** None. The middle is set by established parties at 5-20%, and no event party is among them.

**For the checkpoint, added to the v3 addendum's list:**

| # | call | value | evidence | how it is checked |
|---|---|---|---|---|
| 29 | event class | founding events (a)-(d), sourced and dated before the election; event parties estimated as their own class | §3.1-3.3 | the writer prints each class's increment with its party-elections; the lineage table is checked two ways against SOURCES.md |
| 30 | an event party without a judgement | takes the event class width (about 1.5 extra in log; no single width fits) | §3.2: deletion understates by that amount | the trace lists event parties and whether a judgement was entered |
| 31 | robust cap | none adopted; reported as a sensitivity | the cap moves only the two smallest bands and does not stabilise the debutant width | the writer prints capped and uncapped widths |

---

## What I re-derived and what I did not

**Re-derived:**

- the 169 party-elections and their record categories;
- widths under the four variants;
- leave-one-party-out for every width (177 parties);
- the event-class statistics;
- the Johannesburg 2026 simulations and backtest scores for A and B under each variant.

**Sourced by web search this session:**

- PA, AIC, Cape Coloured Congress, ATM, APC, Northern Alliance, Abantu Batho Congress, UIM, Agang (sources in §1.2);
- three further searches (Agency for New Agenda, Active Citizens Coalition, the party coded DOP) did not settle an origin, so those rows stay "not sourced".

**Not done:**

- the origins of 151 small party-elections;
- whether the 2026 founding events (MK, RISE, BOSA) meet the rule. Those dates are recalled, not sourced here;
- the leave-one-party-out ranges are before the location fixed point, which moves widths by at most 0.025;
- no model run.
