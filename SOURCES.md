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

LGE ids: **1091** = 2021, **402** = 2016.

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

## Still to acquire — needs a human

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
