# Data held, 2026-10-23

Read-only inventory by an agent on 2026-10-23, from its own reads of the files
(scripts in the session scratchpad). Anything marked *inferred* was not read
directly. Paths are under `data/raw/elections/` unless given in full.

## What every result file carries

- Per-metro files share one header: `Province, Municipality, Ward, VD_Number,
  VS_Name, [BallotType], Registered_Population, Spoilt_Votes,
  Total_Valid_Votes, sPartyName, Party_Votes`. Registered voters, spoilt
  ballots, valid votes and per-party votes per voting district (VD). No
  votes-cast or turnout column; both derive as valid + spoilt.
- The bulk zips also carry `TOTAL VOTES CAST` and `% VOTER TURNOUT` (2014:
  `SECTION 24A VOTES`, `SPECIAL VOTES`). The per-metro files dropped them; the
  special-vote split needs the zips.
- Party votes sum exactly to valid votes in every file and ballot.
- No historic result file splits a VD across wards; split VDs exist only in the
  2026 MDB layer.
- Metros have no district-council ballot; `ingest_historic.METRO_BALLOTS` drops
  the 2000/2006 "DC 40%" ballot.
- **National/provincial files are the PROVINCIAL ballot only**
  (`ingest_historic.SPECS` `prefer_event: "PROVINCIAL"`; `ingest_npe.py`
  `--event PROVINCIAL`).

| zip (`_source/`) | national-ballot rows | provincial-ballot rows |
|---|---|---|
| `1999_npe.zip` | 232,400 | 185,642 |
| `2004_npe.zip` | 356,412 | 255,723 |
| `npe2009_national_and_provincial.zip` | 513,084 | 341,827 |
| `npe2014_national_and_provincial.zip` | 645,627 | 418,836 |
| `npe2019_provincial_national.zip` (id 827) | not held | provincial only (*inferred* from name, SOURCES.md, URL) |
| `npe2024_provincial_national.zip` (id 1335) | not held | provincial only (*inferred*) |

`levels.HELD_BACK` withholds `lge2000` and `npe1999` for every metro except
Johannesburg pending a diagnosis (MODEL-LOG §1.154).

## Johannesburg

| election | file | level | VDs | wards | ballots | registered | PR valid/spoilt | Ward valid/spoilt | parties |
|---|---|---|---|---|---|---|---|---|---|
| LGE 2000 | `lge2000_JHB_vd_party_clean.csv` | VD + ward | 652 | 109 | PR, Ward | 1,552,791 | 599,937/10,686 | 600,372/10,458 | 14 |
| LGE 2006 | `lge2006_JHB_vd_party_clean.csv` | VD + ward | 727 | 109 | PR, Ward | 1,739,292 | 690,264/12,001 | 694,063/10,138 | 19 |
| LGE 2011 | `lge2011_JHB_vd_party_clean.csv` | VD + ward | 797 | 130 | PR, Ward | 2,010,121 | 1,090,124/11,724 | 1,082,663/15,803 | 22 |
| LGE 2016 | `lge2016_JHB_vd_party_clean.csv` | VD + ward | 842 | 135 | PR, Ward | 2,239,966 | 1,255,385/18,376 | 1,256,698/16,745 | 28 |
| LGE 2021 | `lge2021_JHB_vd_party_clean.csv` | VD + ward | 867 | 135 | PR, Ward | 2,220,710 | 923,724/11,975 | 922,465/11,432 | 57 |
| NPE 1999 | `npe1999_approx_JHB_vd_party.csv` | VD, no ward | 648 | – | provincial | 1,553,686 | 1,361,299/13,809 | – | 14 |
| NPE 2004 | `npe2004_JHB_vd_party.csv` | VD, no ward | 686 | – | provincial | 1,751,381 | 1,256,055/17,042 | – | 18 |
| NPE 2009 | `npe2009_JHB_vd_party.csv` | VD + ward | 759 | 109 | provincial | 2,003,007 | 1,483,848/15,590 | – | 20 |
| NPE 2014 | `npe2014_JHB_vd_party.csv` | VD + ward | 825 | 130 | provincial | 2,184,484 | 1,570,600/14,579 | – | 22 |
| NPE 2019 | `npe2019_JHB_vd_party.csv` | VD, no ward | 853 | – | provincial | 2,291,299 | 1,527,695/12,592 | – | 36 |
| NPE 2024 | `npe2024_JHB_vd_party.csv` | VD, no ward | 865 | – | provincial | 2,348,781 | 1,415,548/12,293 | – | 44 |

1999 is the sum of the councils that later merged into the metro.

The other seven metros hold the same set of files. Their VD counts, ward
counts, registration and valid/spoilt totals are in the agent's report, kept in
the session record. 1999 is approximate everywhere (Buffalo City: East London
only); Mangaung and Buffalo City cover different areas before 2011.

## By-elections (`data/raw/byelections/`)

| file | cycle | contests | dates | fetched |
|---|---|---|---|---|
| `byelections_SA_vd_party_2016.csv` | 2016–21, national | 319 | 2016-11-09 – 2021-05-19 | 2026-10-19 |
| `byelections_SA_vd_party.csv` | 2021–26, national | 311 | 2022-02-02 – 2026-06-24 | 2026-08-07 |
| `byelections_Gauteng_vd_party.csv` | 2021–26, Gauteng | 38 | duplicates the SA file | 2026-08-01 |

Columns: EEID, date, ward, VD, PartyID, short and full name, candidate, votes,
percentage, leading flag. **No file carries registered voters, spoilt ballots
or votes cast**; `src/byelections.py` divides valid votes by the previous LGE's
ward registration.

| metro | 2000–06 | 2006–11 | 2011–16 | 2016–21 | 2021–26 |
|---|---|---|---|---|---|
| JHB | not held | not held | not held | 12 (2017-04-05 – 2019-07-24) | 15 in 14 wards |
| TSH | not held | not held | not held | 3 | 12 |
| EKU | not held | not held | not held | 14 | 4 in 3 wards |
| ETH | not held | not held | not held | 15 | 13 in 12 wards |
| CPT | not held | not held | not held | 17 | 11 |
| MAN | not held | not held | not held | 4 | 9 |
| NMA | not held | not held | not held | 9 | 7 |
| BUF | not held | not held | not held | 3 | 4 |

No independent list of held by-elections is stored, so these counts cannot be
checked for completeness. Contests after 2026-08-07 are absent. Johannesburg has
no 2016–21 contest after 2019-07-24; no record says whether that is real.

## Boundary links

- VD→ward per past election: in each result file. NPE 1999, 2004, 2019 and 2024
  carry no ward; NPE 2009 sits on 2006 wards, NPE 2014 on 2011 wards.
- Historic VD→2026 VD: one concordance per metro (JHB
  `data/processed/vd_concordance.csv`, 8,521 rows, 79 unmatched VDs), keyed on
  VD number or station name; no geometry.
- Ward→ward crosswalks: none stored; `pools.reproject` builds one per run
  through VD numbers weighted by registration.
- Ward polygons held: 2011, 2016, 2020, 2026. **Not held: MDB Wards 2000 and
  2009 (= 2006)**, both published. VD polygons: 2026 only.

## Population group

- Census 2022 ward estimates (population group, age, sex), 2021 delimitation,
  all eight metros; modelled estimates of persons, not voters.
- Census 2022 home language: municipality level only.
- **Census 2011, 2001, 1996: not held at any level.**

## Voters' rolls

- Registration per VD inside every result file.
- 2024 per VD: `REGPOP` in `vds2026_*.geojson` (labelled current; is 2024).
- 2026 per ward: Johannesburg (2026-09-26) and Tshwane (2026-09-29) only.
- 2026 per VD and roll by age/sex below municipality: not published by the IEC.

## Gaps and the reasons recorded

| gap | reason recorded | where |
|---|---|---|
| National ballot 1999–2014 not extracted | ingesters hard-code the provincial ballot; the plan names it with no reason | `src/ingest_historic.py`, `src/ingest_npe.py`, original plan §1.1 |
| National ballot 2019, 2024 not on disk | only the provincial download was fetched; **no record of why** | SOURCES.md |
| Ward missing from NPE 1999, 2004, 2019, 2024 | source layouts carry none; recoverable through the preceding LGE, not done | `ingest_historic.py`; DATA-QUALITY 18 |
| By-elections before 2016 | **no record of an attempt** | MODEL-LOG §1.30; SOURCES.md |
| By-election registration, spoilt, turnout | fields not fetched; **no record** whether published | `src/fetch_byelections.py` |
| Census 2011 by ward | "highest-value outstanding data request"; **no record of a request** | `config/dimensions.toml`; SOURCES.md |
| Ward polygons 2000, 2006 | published; **no record of why not fetched** | SOURCES.md |
| Historic VD polygons | not published; needs an IEC request | SOURCES.md; DATA-QUALITY 14 |
| 2026 roll, six metros | owner: not before Johannesburg's interactive is done | TODO.md §3 |

## Inconsistencies

1. Ward codes change prefix at 2011 in seven metros; Cape Town keeps 191, so
   2000/2006 codes collide with later ones; codes are reused across
   delimitations.
2. At least six bulk-zip layouts (newlines in headers, double spaces, special
   votes, CP850 encoding); portal CSVs differ from clean files.
3. Parties are identified by name only in result files; independents share one
   name; `data/processed/party_crosswalk.csv` maps 130 names. Empty party names:
   260 rows (2016–21 by-elections), 72 (2021–26 SA), 17 (Gauteng).
4. `data/archive_manifest.csv` credits the wrong ingester for 2000/2006 and
   1999–2009 files, and the wrong report path for one PDF.
5. ActionSA's 6.22% is called a "2024 national ballot" figure in
   OWNER-DECISIONS-ANSWERED.md and MODEL-LOG; only the provincial ballot is held
   (*inferred*, not checked).
6. The IEC roll pages give 862 (JHB) and 796 (TSH) VDs against 865 and 774 in the
   crosswalks; not reconciled.

## Checked 2026-10-23 (plan step 1.5)

- The IEC by-election dashboard (`MapsJason/{year}/ByElections.js`) serves the
  2016 and 2021 cycles only. 2000, 2006, 2008, 2010–2015 and 2017–2020 return
  HTTP 404 (curl, 2026-10-23). The pre-2016 cycles are not available from this
  source; other IEC sources are still to be checked.
- Each contest's file (e.g. `MapsJason/1102/EEID1102BigMapsNational.js`) carries
  `RegisteredVoters`, `SpoiltVotes`, `TotalVotesCast`, `SpecialVotes` and
  `ValidVotesCast`. `src/fetch_byelections.py` `COLUMNS` keeps none of them, so
  by-election turnout can be fetched rather than derived from the previous
  LGE's roll.
