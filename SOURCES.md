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

## Still to acquire

* VD boundary / VD→ward lookups and MDB ward shapefiles for 2016, 2021, 2026
  (plan §1.2, G1–G4).
* CoJ by-election results 2021–2026 (plan §1.4). Note these are only reachable
  via per-session `ReportViewer?_f=<encrypted-token>` links, so they need the
  browser route; `thesouthafricabrief.substack.com` carries the same contests
  with 2021/2024 comparators already computed.
* Census 2022 small-area covariates for the turnout sub-model (plan §1.3).
