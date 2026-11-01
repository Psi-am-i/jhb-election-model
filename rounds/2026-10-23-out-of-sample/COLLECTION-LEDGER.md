# Collection ledger

Every attempt to collect an item in `DATA-PLAN.md` §4, successful or not, one
row per attempt, appended. Fetched files go to
`rounds/2026-10-23-out-of-sample/collection/<item>/`, never into `data/raw/`:
nothing replaces a file the model reads until an approved change does so with an
old-vs-new report (`DATA-PLAN.md` §4).

| Result | meaning |
|---|---|
| `got` | the data is held, path given, check run and its outcome stated |
| `partial` | some of it is held; what is missing is named |
| `refused` | the source answered and would not give it (status, message) |
| `absent` | the source does not hold it |
| `request` | it needs a human request; the draft is named |

| # | Item | Date | Who | Source | Result | Path / note |
|---|---|---|---|---|---|---|
| C6 | By-elections before 2016 | 2026-10-23 | scout-claude | IEC by-election dashboard | absent | dashboard serves 2016 and 2021 cycles only; other cycles answer 404 (`DATA-PLAN.md` §4) |
| C10 | JHB 2026 roll refresh (later than 2026-09-26?) | 2026-10-28 | scout-claude | IEC Voter-Registration-Statistics page, Chrome | got | `collection/iec-registration-2026-09-29/`; page dated 29 Sep 2026; all 135 wards identical to the 26 Sep snapshot; no refresh needed (`now/A2-roll-check.md`) |
| C8 | Census 2011 by ward × population group (and age) | 2026-10-28 | scout-claude | SuperWEB2 guest login → Census Profiles → Census 2011 → Electoral Ward Profiles → Descriptive | partial | table built (Geography "South Africa by Electoral Wards", 4,277 wards × Population group, person weighted; fields also hold Age in completed years (121) and Gender); download held for the owner's permission; nothing saved yet |
| C8 | Census 2001 by ward × population group (and age) | 2026-10-28 | scout-claude | SuperWEB2 → Census Profiles → Census 2001 → Electoral Ward Profiles → Descriptive | partial | fields: Geography to level "Municipality ward", Population group (4), Age (121), Gender, Language (12); not yet extracted; no Stats SA request needed for these variables |
| C5 | By-election registration, spoilt, cast | 2026-10-28 | scout-claude (agent) | IEC by-election dashboard JSON (`MapsJason/…`), 2016 and 2021 cycles | partial | `collection/byelections/`: 630 contests (319 + 311), VD and ward registration for all; cast/spoilt/special served only per municipality × date, so held per contest for 403 single-ward municipality-events (379 contests consistent, 24 inconsistent), not for 227 contests in multi-ward events; no VD-level cast/spoilt; 3 events (EEID 1186, 1919, 1926) have empty result files; independent (party 0) votes incomplete in VD rows; contest sets and VD × party votes match `data/raw` exactly (README) |
| C7a | By-elections after 2026-08-07 | 2026-10-28 | scout-claude (agent) | IEC by-election dashboard, `2021/ByElections.js` and `2026/ByElections.js` | absent | 2021 list ends 2026-06-24 (EEID 1935); 2026 list 404; dashboard cannot tell "none held" from "not published" — C22 |
| C7b | Johannesburg by-elections 2019-07 to 2021-11 | 2026-10-28 | scout-claude (agent) | IEC by-election dashboard, 2016 cycle | got | 4 contests, all 2019-07-24 (EEID 865), VD registration and party votes held; contest cast/spoilt not served (four wards that day, municipal total only); no JHB event on the dashboard 2019-07-25 to 2021-11 |
| C5 | By-election registration, spoilt, cast (correction to the C5 row above, same fetch) | 2026-10-28 | scout-claude (agent) | IEC by-election dashboard JSON, 2016 and 2021 cycles | partial | the C5 row above is superseded: from EEID 1598 (2024-12-04) the municipal file's party-0 row duplicates per-candidate negative-id independent rows; dropping it, 389 contests have consistent contest-level totals, 14 inconsistent, 227 not split. Independent votes are short in VD rows only to 2024-08 (16 municipality-events, multi-independent wards), and identically in `data/raw` (`collection/byelections/README.md`) |
| C8 | Census 2011 by ward × single year of age × population group | 2026-10-30 | scout-claude | SuperWEB2 guest, Census 2011 Electoral Ward Profiles, Descriptive, CSV | got | `collection/census/census2011_ward_age_popgroup.csv`; 4,277 wards; SA 51,770,560 and JHB 4,434,827 equal to published |
| C8 | Census 2001 by ward × single year of age × population group | 2026-10-30 | scout-claude | SuperWEB2 guest, Census 2001 Electoral Ward Profiles, Descriptive, CSV, codes on | got | `collection/census/census2001_ward_age_popgroup.csv`; 3,794 wards; SA 44,819,778 equal; JHB (79400) 3,225,832 vs 3,225,812 published |
