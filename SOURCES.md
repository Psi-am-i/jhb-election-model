# Data sources — how each raw file was obtained

`data/` is gitignored, so this file is the reproducible record of where the raw
inputs come from. Downloaded archives are kept in
`data/raw/elections/_source/` so nothing depends on the browser's download
folder.

## Access constraints (learned the hard way)

`results.elections.org.za` and `www.elections.org.za` sit behind Cloudflare and
return **403 to plain curl**, including with a browser UA and referer. Some
individual report files are served without the challenge and *are* curl-able
(see LGE below); the bulk `.zip` exports are **not** and must be fetched through
a real browser session.

Two further notes:

* The report picker is an ASP.NET postback UI with native `<select>` elements.
  Setting `.value` alone does not fire the tracked setter — use the native
  property-descriptor setter plus `dispatchEvent(new Event('change'))`. Space
  the postbacks out; roughly ten rapid synthetic postbacks earned a WAF 403.
* Reading downloaded bytes requires the terminal to hold macOS **Full Disk
  Access** (System Settings → Privacy & Security), otherwise `~/Downloads` is
  `Operation not permitted` even though the file is there.

## Election IDs

The portal's election id is *not* the year and differs per ballot. Read them off
the `MainContent_ddlElections` dropdown after selecting the election type:

| Year | National | Provincial |
|---|---|---|
| 2024 | 1334 | **1335** |
| 2019 | 699 | **827** |
| 2014 | 291 | **292** |
| 2009 | 146 | **169** |
| 2004 | 45 | **50** |
| 1999 | 1 | **42** |
| 1994 | 61 | **62** |

LGE ids: **1091** = 2021, **402** = 2016, **197** = 2011.

The pre-2014 ids were read off the same dropdown on 2026-08-09. They are worth
having even though the report routes mostly 404 for them (below), because the
id is the only way to address an old election at all.

**The 2009 report route has one less path segment than the modern one.** For
2019 and later a municipality report is
`/{id}/{report}/{PROVINCE}/{MUNI}/{MUNI}.pdf`; for 2009 it is
`/{id}/{report}/{PROVINCE}/{MUNI}.pdf`, and the province-level report is
`/{id}/{report}/{PROVINCE}.pdf`. Guessing the modern shape returns 404 and
looks like "the data does not exist", which is how this was nearly missed:

```
results.elections.org.za/home/NPEPublicReports/169/Detailed%20Results/GP/JHB.pdf
```

is Johannesburg's full 2009 provincial result, and is the control the bulk
ingest is validated against (it reconciles to the vote).

## National & provincial elections (VD-level, provincial ballot)

| Year | Route | Result |
|---|---|---|
| 2024 | `results.elections.org.za/home/NPEPublicReports/1335/Downloadable%20Results/Provincial.zip` | ✔ browser download, 4.2 MB |
| 2019 | same pattern, id **827** | ✔ browser download, 4.0 MB |
| 2014 | same pattern **404s** — 2014 is published on the other host instead: `www.elections.org.za/content/Elections/Downloadable-results/2014-National-and-Provincial-Elections--Complete-voting-district-level-results-data-(zipped-CSV)/` | ✔ browser download, 7.1 MB |

Reachable from the UI at *NPE-Results → Provincial → \<year\> → Downloadable
report data*.

Ingest with `src/ingest_npe.py`, which normalises the two layouts and writes the
CoJ subset to `data/raw/elections/npe{year}_JHB_vd_party.csv`:

```
python src/ingest_npe.py "data/raw/.../2014 NPE.csv" 2014 --event PROVINCIAL
python src/ingest_npe.py "data/raw/.../827.csv"      2019
python src/ingest_npe.py "data/raw/.../Provincial.csv" 2024
```

Layout quirks the ingester handles: header punctuation drift, CP850 encoding in
2019, unquoted commas in voting-station names that shift columns, and the 2014
file's `VALID VOTES` column being the *party's* votes rather than the VD total.

## Local government elections (VD-level, ward + PR ballots)

These *are* curl-able without a browser:

```
https://results.elections.org.za/home/LGEPublicReports/{id}/Downloadable%20Party%20Results/GP/JHB.csv
```

with id **1091** (2021) and **402** (2016) → `lge{year}_JHB_vd_party.csv`.

Also confirmed working: turnout PDFs at
`.../LGEPublicReports/{id}/Voter%20Turnout/GP/JHB.pdf`.

Run `src/fetch_iec.py` to sweep every LGE report that is served directly
(party CSV, detailed results, seat calculation, turnout) for 2011, 2016 and 2021.

## The pre-2011 archive — a national bulk export nothing links to

Every election from 1999 is published as a single zipped national CSV under a
path that appears on no page of either site, is absent from the downloads
portal, and 404s on the portal's report routes:

```
https://www.elections.org.za/content/uploadedfiles/{YYYY}%20{NPE|LGE}.zip
```

Confirmed and archived to `data/raw/elections/_source/` on 2026-08-09/10:

| File | Bytes | SHA-256 (first 16) |
|---|---|---|
| `npe2009_national_and_provincial.zip` | 5,550,741 | `75c6cf58647e7e89` |
| `2004_npe.zip` | 4,012,589 | `c6a5cb39f3c4316a` |
| `1999_npe.zip` | 2,945,157 | `985ac3bfba844851` |
| `2006_lge.zip` | 2,866,931 | `42785a46247f1bad` |
| `2000_lge.zip` | 1,712,579 | `179d7258d66730d0` |
| `2011_lge.zip` | 3,544,022 | `19e54362f18b270d` |

`2016 LGE`, `2014/2019/2024 NPE` are **not** at this path — those years were
already held as national zips from their own routes.

Each archive holds one CSV covering the whole country, both electoral events
where applicable, keyed by a municipality string that changes every year
(`JHB -`, `JOHANNESBURG -`, `Johannesburg -`, and five separate metropolitan
local councils in 1999, before the metro existed). `src/ingest_historic.py`
converts them to the project's canonical VD files, describing each layout
explicitly rather than sniffing it, and refuses to write a file when more than
2% of its VD-ballots fail to reconcile -- party votes summing to that
district's valid total, within `--tolerance` (default 0.1%). All five
archives reconcile at 100%, worst drift 0.00%.

**Read DATA-QUALITY 10a and 10b before touching these files.** The vote column
mixes plain integers with thousands-separated ones in the same column, and a
naive reader silently discards 68.4% of Johannesburg's 2009 votes while
dropping only 4.0% of its rows. An unquoted comma inside a party's own name
shifts every later column in six 2006 districts.

**Caveat on 1999:** the City of Johannesburg did not exist until the December
2000 election. The 1999 file is aggregated from the five metropolitan local
councils that became it and is written as `npe1999_approx_*`; the footprint is
approximate and it must not be used for ward-level work.

## Boundaries — MDB Spatial Knowledge Hub

`spatialhub-mdb-sa.opendata.arcgis.com` is an ArcGIS Hub site. Its DCAT feed
(`/api/feed/dcat-us/1.1.json`) lists the datasets, but only advertises download
endpoints for some. Every layer sits behind a FeatureServer that takes a
municipality filter, which is better anyway — Johannesburg is selected
server-side rather than pulling the whole country. Layer URLs were resolved from
the MDB's "Wards2026" web map (ArcGIS item `6d7488a7f83645218e547d403871e1e0`).

| Layer | Service | Applies to |
|---|---|---|
| 2026 wards | `MDBWards2026` | 4 Nov 2026 election |
| 2026 voting districts | `VotingDistricts2026_Final` | carries `WardNo`, `Split_VD`, `REGPOP` |
| 2021 wards | `SA_Wards2020` | 2020 delimitation |
| 2026 voting stations | `VotingStations_March2026` | points; keyed on `MUNICIPALI`, not `CAT_B` |

The 2016 and 2011 ward layers are File Geodatabase item downloads, not services:
ArcGIS items `cfddb54aab5f4d62b2144d80d49b3fdb` and
`12d2deb98816451ab7c4dc09cdfeee6b`, fetched via
`arcgis.com/sharing/rest/content/items/{id}/data`.

`src/fetch_boundaries.py` pulls all of these; `src/build_geo.py` clips the
geodatabases and runs the checks.

**Caveat:** `REGPOP` on the 2026 VD layer sums to 2,348,781 — exactly the *2024*
registration total. It is a 2024 snapshot, not current 2026 registration.

## By-elections — use the dashboard, not the downloads page

The downloads page serves by-election reports only through per-session
`ReportViewer?_f=<token>` links. Those tokens are session-bound: fetched with
curl they reach the handler and return "Error occured while trying to generate
the by-election report".

The **dashboard** is backed by plain static JSON that needs no session:

```
.../dashboards/byelection/MapsJason/{year}/ByElections.js      # dates + EEIDs
.../dashboards/byelection/MapsJason/{year}/PartyList.js        # party id -> name
.../dashboards/byelection/MapsJason/{eeid}/EEID{eeid}BigMapsNational.js
.../dashboards/byelection/MapsJason/{eeid}/EEID{eeid}Munic{municipalityID}.js
```

The national/province files carry only the *leading* party per ward. The
per-municipality file is the one worth having: voting-district level, every
party, candidate names, historical comparators. `src/fetch_byelections.py`
walks all of it — 38 Gauteng ward contests since 2021, 15 in CoJ.

## Covariates

Stats SA's **Ward-level Small Area Population Estimates 2022** are directly
downloadable and cover all 135 CoJ wards on the 2020 delimitation, with
five-year age bands, sex and population group:

```
statssa.gov.za/wp-content/uploads/2025/11/Ward-Product_Locked-spreadsheets.zip
statssa.gov.za/wp-content/uploads/2025/11/Ward-statistical-product-technical-note.pdf
```

## Historic VD boundaries — searched for, not published

Needed to verify that a VD keeping its number kept its catchment (see
`src/build_concordance.py`). Everywhere checked, and not found:

| Where | Result |
|---|---|
| MDB ArcGIS org, full service list (43 services) | only 2026-era voting-district layers; ward layers back to 2000 |
| MDB DCAT catalogues, both hub sites | no VD datasets at all |
| ArcGIS Online public search | one 4-feature derived sample; nothing national |
| IEC GeoServer `vmdgeomaps.elections.org.za` | address points (NAD) plus GeoServer demo layers |
| Internet Archive CDX over both IEC and MDB hosts | ward and municipal shapefiles only, no VD |

The IEC delimits VDs with its own GIS and appears not to publish the boundaries,
so this needs a request to the IEC's Delimitation Directorate. Until then the
concordance keys on VD number, with the stability flags described in
`build_concordance.py` standing in for the geometric check.

The Internet Archive sweep did turn up one live URL worth having, since the MDB
has already retired the per-municipality shapefile downloads its old site
served: the **2016 LGE complete VD-level results**, on the same host pattern as
the 2014 NPE export —
`elections.org.za/content/Elections/Downloadable-results/2016-Municipal-Elections--Complete-VD-level-results-data-(zipped-CSV)/`.
Its JHB PR totals reconcile exactly, party for party, against the per-municipality
CSV we already had.

## Archive

`src/archive.py` records every raw and derived file with its size, SHA-256 and
provenance in `data/archive_manifest.csv`. The data itself is gitignored, so the
manifest is the tracked record — it is committed even though the bytes are not.
`python src/archive.py --verify` re-hashes and reports anything missing, changed
or new, which is how we will know if a file quietly diverges from the copy every
validation in this repo was run against.

## Still to acquire — needs a human

* **Defector counts per split, and ideally per metro** — added 2026-08-22
  (MODEL-LOG §1.73). **We do not have this data in any form.** The comparative
  literature's best predictor of how a split divides the vote is *membership
  strength and the share of legislators who defected*, and `pools.Split` records
  `parent`, `measured_from`, `home` and `why` — no counts. What would be needed,
  per split (COPE 2008, NFP 2011, EFF 2013, GOOD 2018, ActionSA 2019, MK 2023):
  how many of the parent's public representatives left with the founder, and —
  the part that would actually earn its keep — **how many in each metro**.

  Why the per-metro version matters more than the national one: the register
  already carries `MIN_HOME_SPLITS + binary home/away` at 🔴 because a splinter
  is modelled as either at home or away with nothing between, while ActionSA's
  fraction of the DA ran **0.611 / 0.315 / 0.289 / 0.103** across four metros —
  a gradient bucketed into two, and the reason Tshwane's seed was 0.17% against
  an actual 9.28%. A single national defector share is one number per split and
  cannot produce a gradient across metros. A *per-metro* defector share can, and
  it is the local analogue of the international finding rather than an import of
  it.

  **A possible route, and its limits.** Floor-crossing was abolished in 2009, so
  a councillor who defects vacates the seat and a by-election follows — which
  means defections are in principle observable as by-elections. The IEC's
  by-election notices state the reason for the vacancy (death, resignation,
  removal). **This repository's by-election data does not capture it**:
  `data/processed/byelection_contest_detail.csv` carries ward, date, party,
  shares, delta, weight and rho across 89 contests, and no cause field.
  `byelections.py`'s own docstring names the selection ("resign or defect,
  skewing toward unstable wards") without recording which. So the cause is a
  scrape that has not been done.

  **Its limit is severe and should be stated before anyone starts.** The scraped
  by-election window is 2022-06 to 2026-02, so this route can only characterise
  defections into MK (2023) and anything after. **COPE, the NFP, the EFF, GOOD
  and ActionSA are all outside it**, and those are the five splits the record is
  actually built from. For them the counts would have to come from council
  minutes and contemporaneous reporting, one at a time.

* **A NATIONAL poll declared for 2026** — added 2026-08-22, MODEL-LOG §1.69, and
  it is now the **highest-value acquisition on this list** measured in seats. The
  arrivals poll path converts a national poll share into a metro one through the
  contested-area arithmetic, and it is worth **48 coherent seats across nine
  city-years** (§1.65) — the largest single measured effect in the poll channel.
  §1.69 fixed the geographic half that blocked it at a live target
  (`polling.PROJECTED_METRO_SHARE`), so the code is ready and **the only
  remaining blocker is that no national poll declared for 2026 is in
  `polls.json`.** The three admitted 2026 records are two SRF metro waves and one
  metro-aggregate:

      admitted at 2026: srf-2026q2-coj (metro), srf-2026q1-coj (metro),
                        ipsos-w2-2025-metros (metro-aggregate)
      national among them: []

  Ipsos, SRF and the Social Research Foundation all publish national voting
  intention; what is needed is one with a **machine-readable `fieldwork_end`**
  and a party-share breakdown, entered as `scope = "national"`. Note that
  `metro-aggregate` does not substitute — eight metros averaged is not a reading
  of the country, and `polling.validate` says so as a warning on
  `ipsos-w2-2025-metros`.

* **The pre-2011 archive for the seven non-Johannesburg metros** (`npe2009_*`,
  `lge2006_*`) — promoted here 2026-08-22 because §1.69 established what it is
  worth. It is the ONLY remaining blocker on seven more backtest city-years:
  their 2016 pool specs are emitted and committed, and the sole thing stopping
  those targets running is γ fold 3 (2009 NPE → 2011 LGE), which needs these two
  files. That takes the panel from nine city-years to sixteen and from one
  effective electoral cycle to two — which `ITERATING.md` names as the one thing
  that would license reopening modelling work at all. See §101, "The pre-2011
  archive — a national bulk export nothing links to". **Not** worth attempting
  for 2011 targets: `pools.py --city joburg --target 2011 --emit` fails with
  *"no ward joined the census"* because the 2006 ward geography predates the
  delimitation the census is joined on.

* **Census 2022 home language, by ward** — the single most valuable missing
  input. The Ward Statistical Product carries only population group, age and
  sex, and population group is too coarse to describe how voters are grouped:
  the ANC and IFP are both overwhelmingly African-supported and stand on
  entirely separate ground (district correlation −0.14), while the DA and VF+
  differ in language and share ground (+0.61 in Johannesburg, +0.86 in
  Tshwane). Language would settle how many voter pools a city has and put a
  demographic bound on MK, which took 71% of its Johannesburg vote from the
  ANC while standing on IFP ground. Requested — draft at
  `drafts/statssa-request-language.md`.
* **Census 2022 Small Area Layer (SAL)** — plan §1.3 C1 asks for income,
  dwelling type and employment at small-area level. Stats SA does **not**
  publish the SAL for download; it is supplied on request only
  (`info@statssa.gov.za`, +27 12 310 8600). The ward-level product above is the
  usable substitute in the meantime, but it carries only age/sex/population
  group — no income or employment. Wazimap-NG (C2) was unreachable when tried.
* **Voters' roll by VD split by age and sex** — plan §1.3 C3. The IEC's
  registration statistics page publishes age/gender bands only down to
  *municipality* level, server-rendered with no API. VD-level registration
  *totals* we already have, from the election files and the VD layer's `REGPOP`.
* **2026 registration figures** — the IEC page shows the position as at
  1 Aug 2026 at municipality level; §3.2 wants the registration-weekend deltas,
  which are not published yet.

## All-metro sweep (2026-08-07, phase 2 groundwork)

One pass collected everything the other seven metros need, so the well never
has to be revisited for results:

* **IEC LGE reports, all 8 metros** — `data/raw/elections/_reports/` now holds
  the 2011/2016/2021 Downloadable Party Results (VD level), Detailed Results,
  Seat Calculation Detail (pdf+xls) and Voter Turnout for JHB, TSH, EKU, ETH,
  CPT, MAN, NMA and BUF. Portal code traps: Nelson Mandela Bay is **NMA** (not
  NMB), and the IEC's province path segments are **WP** for Western Cape and
  **KN** for KwaZulu-Natal. `python src/fetch_iec.py --muni TSH --province GP`
  et al.
* **By-elections, whole country** — `byelections_SA_vd_party.csv`: 9,163 VD×
  party rows across 311 ward contests in every province
  (`fetch_byelections.py --province ""`); the CoJ subset reconciles with the
  15 contests already used by the model.
* **Boundaries, all metros** — 2026 ward, VD and voting-station GeoJSON
  extracts per metro (`fetch_boundaries.py --muni TSH` …); the 2011 and 2016
  ward geodatabases were already national.
* **Census 2022 ward product** is national (all ~4,470 wards), so no further
  Stats SA request is needed per metro.

NPE 2014/2019/2024 and LGE 2016 were already held as national zips in
`_source/`. Remaining phase-2 work per metro is pipeline parameterisation,
not acquisition.

## Data quality issues

Defects found in the published record — encoding drift, silently mislabelled
columns, impossible turnout values, a seat report that reassigns its own
formula letters between years — are logged in
[`DATA-QUALITY.md`](DATA-QUALITY.md), written so they can be reported to the
IEC, MDB and Stats SA rather than only worked around here.

## Polls — searched for, and what does and does not exist (2026-08-22)

`polls.json` is the register and `POLLING.md` the human-readable version;
neither was referenced here at all until now, which is its own gap.

**Searched for, NOT published — do not look again without new information.**
Ipsos's pre-election work for the 2021 LGE was run for eNCA (fieldwork 9–14
October 2021, n = 1,346, CATI) and **publishes no metro-level party splits** —
only turnout scenarios per metro ("Tshwane and Johannesburg only at 50% in the
medium scenario"). We hold the national reading as `ipsos-2021-lge-national`.
This matters because a metro-level Ipsos 2021 Johannesburg poll would be the
single most valuable addition to the register: it would let the metro path fire
on the model's **worst** city-year, and give `H_eff > 1` for the first time.

**Houses that publish South African voting intention**, from the coverage of the
2026 cycle: Ipsos, MarkDATA, the Brenthurst Foundation, the Institute of Race
Relations, and the Social Research Foundation with Victory Research. Only the
last has published a Johannesburg metro cut for 2026, which is why `H_eff = 1.0`
and the weight cap binds at 0.42 (§1.67).

**On the 2026 register's single-house problem, independently.** The Daily
Maverick's *"Baselines and biases"* (17 August 2026) observes that SRF's leaders
and staff — and those of its service provider Victory Research — *"have had
close associations with the DA"*. That is an outside observation of the risk
`POLL_HOUSE_K` is priced for, and it is worth having on the record as something
other than our own suspicion. The same piece confirms the July 2026 Johannesburg
numbers we hold: DA 42, ANC 18, MK 13, ASA 10, EFF 8, n = 504, 8–31 July,
±4.4pp claimed.

## Cross-references — read against, never read from

**Nothing in `src/` opens anything in this section**, and that is the point of
separating it. A source listed beside the IEC exports would be taken for an
input; these are places to check our readings against somebody else's, which is
a different job and carries different risks. If one of them ever becomes an
input it moves up the file and acquires a provenance note like everything else.

### Inside Politics — 2026/7 election resources (added 2026-08-18)

<https://inside-politics.org/election-2026-7-resources/>

An independent analyst's index for the 2026 LGE, and it is **large — roughly 230
linked pages**, not a summary page. (A first survey of it recorded here called it
a handful of graphics with "notable gaps"; that was read off a compressed
summary and was wrong. Enumerated properly, the structure is below.)

| section | what | grain |
|---|---|---|
| Analysis | 18 numbered pieces | metro and ward |
| 1–2. Party performance | ANC, DA, EFF, FF+ vote share, plus ANC-vs-DA, ANC-vs-EFF, DA-vs-FF+ | national + 8 metros |
| 3–4. Turnout | overall, and ANC/DA turnout differentials | national + metros |
| 5–6. ANC and DA turnout | one page per metro plus an all-metros page | **by ward** |
| 7. ANC–DA trade-offs | one page per metro plus all-metros | **by ward** |
| 8.1 Heat maps, national | ANC, DA, IFP, FF+, EFF, GOOD, PA, ASA, MK, other, leading party, second party, turnout | municipality **and ward** |
| 8.2 Heat maps, provinces | the same set, all nine provinces | municipality **and ward** |
| 8.3 Heat maps, metros | the same set for each of the 8 metros | **by ward** |
| 9. Cumulative turnout tracks | 2000, 2006, 2011, 2016, 2021 | **by ward**, per metro |

**What is worth checking ours against, in order of value to this model:**

1. **Cumulative ANC–DA turnout tracks by ward, 2000–2021.** These are the same
   transitions the θ and ρ records are built from. Closest external check we
   have on the level layer's inputs.
2. **ANC and DA turnout by ward, per metro.** The turnout sub-model's own
   quantity, independently rendered.
3. **PA, ASA, MK, GOOD and IFP heat maps by ward.** Directly relevant to the
   pool vectors — the PA's Coloured concentration, and the ANC/IFP separation
   `MACHINERY.md` §0 records that population group *cannot* make.
4. **"Fragmentation: the most powerful force in Gauteng"** — the effect §1.43
   measured and then found does not forecast.
5. **"A brief history of the voters' roll"** — bears on `DATA-QUALITY.md` item
   11, registration against census.
6. **"How many votes the DA needs for 50% in JHB" (parts I and II)** and the
   **"Zille vs Mashaba methodology"** page — an independent quantitative
   treatment of our exact target, with its method stated.

**Provenance and limits.** Derived from the same IEC results this repository
ingests, so it is **not an independent measurement of the same quantity** — it
is an independent *reading* of it. Good for catching a mis-ingest, a wrong-city
file or a delimitation mismatch on our side; no use at all as corroboration that
a shared upstream figure is correct. Presented as graphics rather than
downloadable tables, so a check against it is by eye.

**What it does not carry**, checked because we want them: no raw voter roll, no
nomination lists, no by-election series, no quantitative metro seat forecast.
Our own gaps in those (see *Still to acquire*) are not closed by it.

#### CHECKED 2026-08-21, and the ingest passes exactly

The survey above says a check against it "is by eye" because the resources are
graphics. That is right about the heat maps and **wrong about the essays**, which
carry figures in prose. *"Action South Africa's prospects in JHB"* (17 Feb 2026)
gave enough to check numerically, and it was:

| Johannesburg 2021 | theirs | ours |
|---|---|---|
| ASA PR votes | 167,359 | **167,359** |
| ASA ward votes | 128,986 | **128,986** |
| ASA citywide PR share | 18.12% | **18.12%** |
| ASA PR share by ward, 135 wards, six bands | 1 / 19 / 16 / 50 / 33 / 16 | **1 / 19 / 16 / 50 / 33 / 16** |

Exact on all of it, including the ward distribution — which tests the VD→ward
mapping and the delimitation, not just a citywide sum. This is the first check of
this repository's ingest against a party outside it. It also resolves an
ambiguity in their write-up: those bands are the **PR** ballot (the ward ballot
gives 6 / 27 / 48 / 40 / 10 / 4).

The limit stated above still holds and is why this is not corroboration of the
IEC itself: same upstream source, independent reading. It catches a mis-ingest,
a wrong-city file or a delimitation mismatch, and it did not find one.
MODEL-LOG §1.64.

#### Two inputs they have and we do not

Neither is an ingest gap; both are quantities the model has no channel for.

* **Announced contestation, months before nomination lists.** They report ASA
  contesting about **42 municipalities** in 2026, from the party's own
  statements, in February. `levels.contestation` reads FILED lists and
  `contestation_expand` (§1.60) projects from 2021 — neither can see stated
  intent. Soft data, and it bears directly on the one input the live forecast
  lacks until 16 September.
* **The mayoral candidate.** Helen Zille is the DA's Johannesburg candidate and
  their argument is that she suppresses ASA specifically. **The model has no
  candidate term.** Not obviously fixable: one ASA local election is on record,
  so a candidate effect cannot be estimated here, and inventing one would be the
  party-specific constant deleted twice (§1.47). Recorded as a blind spot.

## Comparative political-science literature (added 2026-08-22)

The first evidence in this repository that is **not South African electoral
data**. Imported for one purpose — sizing party-lifecycle events, which the
record cannot do because each event happens once — and recorded here with its
provenance because an unsourced claim about another country's elections is worse
than no claim. The argument that uses them is MODEL-LOG §1.72 and §1.73.

**Read the third block before using any of it.** One of these findings has the
opposite sign in South Africa, for a reason that is itself the finding.

### The decomposition that motivates all of it

| source | what it gives us |
|---|---|
| Powell, E. N. & Tucker, J. A. (2014), "Revisiting Electoral Volatility in Post-Communist Countries", *BJPS* 44(1) — <http://www.eleanorneffpowell.com/uploads/8/3/9/3/8393347/powell_tucker_2014_bjps.pdf> | **Type A** volatility (party entry and exit) against **Type B** (vote switching among existing parties), and the argument that pooling them makes the aggregate meaningless. What we actually use is their **coding rules**: the classification is a documented fact about a party, not an inference from its votes, which is what makes §1.72's exclusion non-circular |
| "Rethinking Electoral Volatility", Good Authority — <https://goodauthority.org/news/rethinking-electoral-volatility/> | plain-language account of the Pedersen index and the A/B split |

### Splits — transfers well, and is better than the constant we ship

| source | what it gives us |
|---|---|
| "Electoral Competition after Party Splits", *PSRM* — <https://eprints.soton.ac.uk/407531/1/splits_el_conseq.pdf> | **200+ splits across 25 European countries** post-war. Rump and splinter first-election shares are predicted by **membership strength and the share of legislators who defected** — both observable before polling day. `pools.SPLINTER_PARENT_WEIGHT = 0.35` is a flat fraction identical for every split; this names the covariate that should replace it |

### Leader death — DOES NOT TRANSFER. The sign reverses.

| source | what it gives us |
|---|---|
| "Berlinguer, I Love You (Still)", *Political Behavior* (2025) — <https://link.springer.com/article/10.1007/s11109-025-10095-7> | the PCI **gained** after Berlinguer's death in 1984, in that election and in later ones |
| "The Effects of Political Martyrdom on Election Results: The Assassination of Abe" — <https://arxiv.org/pdf/2305.18004> | the LDP estimated at **~6% more seats** after Abe's assassination |
| So, F., "The Consequences of Party Leadership Change on Democratic Elections" — <http://www.scpi.politicaldata.org/SCPII/Florence%20So.pdf> | leadership change *short of death*: parties with new leaders lose about **3.5%** of their vote on average. This one does transfer |

**The warning.** Both death findings are sympathy-vote results and this model's
own observation runs the other way — the Minority Front at **θ = 0.193** after
Amichand Rajbansi died in 2011. Both are correct, and the moderator is
**institutionalisation**: a leader's death helps a party that outlives him and
destroys one that *is* him. Nearly every party this model must handle is a
personal vehicle — MK/Zuma, ActionSA/Mashaba, GOOD/De Lille, EFF/Malema,
Agang/Ramphele, Minority Front/Rajbansi, PA/McKenzie, COPE/Lekota. **Importing
the sympathy-vote prior without that moderator would be actively harmful**, and
it would have looked well-sourced.

### Context on the size question

| source | what it gives us |
|---|---|
| "Simulating Party Shares", *Political Analysis* — <https://www.cambridge.org/core/journals/political-analysis/article/simulating-party-shares/C391F0D44529EE6E73F904F2D1E1050F> | uniform against proportional swing. θ is a **ratio**, so this model sits at the proportional end; `benchmarks.uniform_swing` is the additive one. "Large parties move less than proportionally" is the contested middle, and §1.72 measures it on our own record |

**Not yet used by any code.** Every row above is argument, not measurement, and
nothing in `src/` reads any of it. Under CLAUDE.md's rule that anything the
harness cannot test is labelled argued-not-tested, these are argued.
