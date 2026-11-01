# By-election registration, spoilt and cast — DATA-PLAN.md §4 items C5, C7

Fetched 2026-10-28, 21:09:56 to 21:25:12 UTC, on Scout, by `scout-claude (agent)`.
Nothing here is read by the model; nothing under `data/` was written.

## Source

IEC by-election dashboard, static JSON (no session, no Cloudflare challenge):

```
https://results.elections.org.za/dashboards/byelection/MapsJason/{2016,2021}/ByElections.js
https://results.elections.org.za/dashboards/byelection/MapsJason/{2016,2021}/PartyList.js
https://results.elections.org.za/dashboards/byelection/MapsJason/{eeid}/EEID{eeid}BigMapsNational.js
https://results.elections.org.za/dashboards/byelection/MapsJason/{eeid}/EEID{eeid}Munic{municipalityID}.js
```

`2011/ByElections.js` and `2026/ByElections.js` answer 404 (probed 2026-10-28).
`EEID{eeid}Ward{wardID}.js` and `EEID{eeid}VD{vd}.js` answer 404: there is no
ward- or VD-level file. The dashboard's own script (`Content/Includes/js/main_functions.js`)
reads only the four patterns above for results.

## Method

`fetch_byelections_c5.py` is a patched copy of `src/fetch_byelections.py`:
`fetch` requests every file sequentially, 1 s apart, all provinces, both cycles,
and archives each body verbatim under `raw/` (659 files, 10 MB); `build`
derives the tables from `raw/` only. `fetch.log` has one line per request
(659 × 200, 7 × 522 Cloudflare origin timeouts, each retried successfully).
`compare_existing.py` compares with `data/raw/byelections/` (read-only).

## What the dashboard serves, by level

| level | registered | cast | spoilt | special | valid | party votes |
|---|---|---|---|---|---|---|
| municipality × date | `RegisteredVoters` (= `RegPop`) | `TotalVotesCast` | `SpoiltVotes` | `SpecialVotes` | `ValidVotesCast` | yes |
| ward (contest) | `RegPop` | — | — | — | sum of parties only | yes |
| voting district | `RegPop` | — | — | — | sum of parties only | yes |

`RegPop` is registered voters: Σ VD `RegPop` = ward `RegPop` in all 630 contests,
and ward `RegPop` = municipal `RegisteredVoters` in every single-ward municipality
where the municipal totals are not in conflict.

**Cast and spoilt exist per contest only where the municipality held one ward
that day.** They are copied onto the contest row in that case and left empty
otherwise; no apportioning. VD-level cast and spoilt are not served.

## Files

| file | rows | grain |
|---|---|---|
| `byelections_vd_party.csv` | 17,616 | VD × party; the original columns + `cycle`, `VD_RegPop`, `Ward_RegPop` |
| `byelections_vd.csv` | 3,159 | VD: `VD_RegPop`, party valid sum |
| `byelections_contest.csv` | 630 | ward contest: `Ward_RegPop`, valid sum, `contest_*` totals, `contest_totals_status` |
| `byelections_muni_event.csv` | 461 | municipality × date: the five municipal totals |
| `checks.json` | | every check failure, listed |
| `compare.json` | | contest sets and VD × party values against `data/raw` |
| `failures.csv` | 3 | events with no result file |

Contests: 2016 cycle 319 (2016-11-09 to 2021-05-19), 2021 cycle 311
(2022-02-02 to 2026-06-24).

## Contest-level totals (`contest_totals_status`)

| | consistent | not split (several wards that day) | inconsistent |
|---|---|---|---|
| 2016 cycle | 181 | 134 | 4 |
| 2021 cycle | 208 | 93 | 10 |

Metros, consistent / not split / inconsistent:

| metro | 2016 cycle | 2021 cycle |
|---|---|---|
| JHB | 3 / 9 / 0 (12) | 9 / 6 / 0 (15) |
| TSH | 3 / 0 / 0 (3) | 8 / 4 / 0 (12) |
| EKU | 4 / 10 / 0 (14) | 4 / 0 / 0 (4) |
| CPT | 10 / 7 / 0 (17) | 8 / 3 / 0 (11) |
| ETH | 4 / 11 / 0 (15) | 10 / 3 / 0 (13) |
| NMA | 5 / 4 / 0 (9) | 5 / 2 / 0 (7) |
| BUF | 1 / 2 / 0 (3) | 0 / 4 / 0 (4) |
| MAN | 4 / 0 / 0 (4) | 1 / 8 / 0 (9) |

"Consistent" = single ward; ward party sum = `ValidVotesCast`; valid + spoilt =
cast; registered ≥ cast; ward `RegPop` = `RegisteredVoters`; municipal party
rows = Σ VD rows for every party.

## Checks and outcomes

| check | level | failures | what they are |
|---|---|---|---|
| Σ VD party votes = ward party votes | ward × party | 10 | all party id 0 (independents); see below |
| Σ VD `RegPop` = ward `RegPop` | ward | 0 | |
| VD `RegPop` ≥ Σ VD party votes | VD | 0 | the only registered-against-votes test the VD files allow |
| VDs complete = expected | ward | 2 | EEID 1163 uMdoni 52102013 (0/1), EEID 1770 Emalahleni EC 21306004 (0/5) |
| Σ party = `ValidVotesCast` | municipality | 1 | EEID 518 Naledi NW 2017-08-02: parties 1,980, valid 1,631, cast 1,708 (unexplained) |
| valid + spoilt = cast | municipality | 0 | |
| registered ≥ cast | municipality | 3 | EEID 498 Nqutu (whole-council, two ballots); EEID 1303 Dihlabeng and uMhlabuyalingana (totals doubled, below) |
| municipal party rows = Σ VD rows | municipality × party | 16 (party 0) + 90 (other parties, 9 events) | below |
| totals identical on every party row | municipality | 0 | after dropping the duplicate party-0 row below |

Party valid votes against a stated valid total can be tested only at municipal
level: ward and VD files state no valid total.

**Independents.** Two encodings, by date:

* To 2024-08 (EEID ≤ 1544) every independent candidate is party id 0, and a VD
  row carries one party-0 candidate. Where a ward had two or more
  independents, the VD and ward rows hold fewer independent votes than the
  municipal row, which agrees with `ValidVotesCast`. 16 municipality-events
  (48 contests in them: 33 in the 2016 cycle, 15 in the 2021 cycle); e.g.
  EEID 1209 Mkhondo ward 83003015, municipal 557, Σ VD 438. The VD × party
  rows in `data/raw/byelections/` are identical, so they carry the same loss.
* From 2024-12-04 (EEID 1598) each independent has a negative per-candidate
  id in VD, ward and municipal rows, and the municipal file adds an aggregate
  party-0 row whose totals are zeroed. That row duplicates the negative-id
  rows (e.g. EEID 1791 JHB 2025-10-15: `-590047` 49 and `0` 49; valid 5,765
  without the duplicate). `build` drops the party-0 row in these 13 files;
  with it dropped, these files pass every check except EEID 1598 Thabazimbi,
  a whole-council event (below). No votes are missing in this encoding.

Party names: 2016 cycle, 260 rows across 7 ids neither party list names
(996, 1138, 1146, 1262, 1272, 1290, 1378; 581 votes); 2021 cycle, 72 rows
with negative (independent) ids, which no party list names (candidate names
are present). The fallback to the other cycle's list named none of them.

**Two ballots / doubled totals.** Whole-council by-elections (EEID 498 Nqutu, 566
Metsimaholo, 1032 Phokwane, 1230 Ditsobotla, 1598 Thabazimbi): municipal rows
count ward and PR ballots, about twice Σ VD, so their cast counts ballots, not
voters. Four single-ward events have municipal valid exactly 2 × ward valid
(EEID 1303 Dihlabeng, uMhlabuyalingana, Overstrand, 2023-04-26; EEID 1467 Govan
Mbeki 2024-02-28); in two of them registered < cast. Their contest totals are
marked inconsistent.

## Comparison with `data/raw/byelections/`

| cycle | existing file | contests existing / collected / shared | only in collection | only in existing | VD × party values differing |
|---|---|---|---|---|---|
| 2021 | `byelections_SA_vd_party.csv` | 311 / 311 / 311 | 0 | 0 | 0 of 9,163 |
| 2016 | `byelections_SA_vd_party_2016.csv` | 319 / 319 / 319 | 0 | 0 | 0 of 8,453 |

The existing files carry no registration, cast or spoilt column; their VD × party
votes are reproduced exactly.

## C7

**After 2026-08-07.** The existing 2021-cycle file's mtime is 2026-08-07 11:49;
SOURCES.md gives its range as 2022-02-02 to 2026-06-24. The dashboard's 2021
list (110 events) still ends at 2026-06-24 (EEID 1935), and no 2026-cycle list
exists (404). The dashboard serves no by-election after 2026-08-07. It cannot
distinguish "none held" from "not published"; C22 settles that.

**Johannesburg, 2019-07 to 2021-11.** The 2016-cycle list ends 2021-05-19 and
the 2021-cycle list begins 2022-02-02. Johannesburg contests in the window: 4,
all on 2019-07-24 (EEID 865; wards 79800054, 79800083, 79800109, 79800112).
All fetched; VD registration and party votes held. The municipality held all
four that day, so contest-level cast and spoilt are not served; the four-ward
total is in `byelections_muni_event.csv`.

## Failed

| EEID | date | reason |
|---|---|---|
| 1186 | 2022-10-05 | `BigMapsNational` and `LiteMapsNational` answer 200 with an empty body (retried 2026-10-28) |
| 1919 | 2026-05-27 | same |
| 1926 | 2026-06-10 | same |

These three events are listed in `2021/ByElections.js` and absent from the
existing file too. No `Munic` file can be addressed without the national file,
which names the municipalities.
