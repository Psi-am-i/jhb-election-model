# Data quality issues found in the public record

Every defect this project hit while building a voting-district model of South
African metro elections, with enough detail to reproduce it. Kept because
these are worth reporting to the bodies that publish the data: each one is
fixable at source, and several corrupt an analysis **silently** rather than
raising an error — which is the dangerous kind.

Nothing here is a complaint about the data being hard. It is a list of
specific, small changes that would stop the next person losing the same days.

Status key: **🔴 corrupts silently** · **🟠 blocks or delays access** ·
**🟡 friction, no correctness risk**

---

## Electoral Commission of South Africa (IEC)

### 1. 🔴 `TotalValidVotes` is the *party's* votes, not the voting district's
*Files: LGE Downloadable Party Results (all years); NPE 2014 bulk export
(`VALID VOTES`).*

The column name reads as a district total. It is the party's own votes on
that row. Anyone computing turnout or shares by taking the first value per
district gets a number that is wrong by the number of parties, with no error
and a plausible-looking result. We recompute the district total by summing
party rows (`src/ingest_lge.py`, `src/ingest_npe.py`).

**Fix:** rename to `PartyVotes`, or add a separate `VDTotalValidVotes`.

### 2. 🔴 A comma in a voting-station name shifts every later column
*Files: NPE bulk exports.*

Some rows are not quoted, so a station named e.g. `"SMITH, JOHN PRIMARY"`
breaks naive CSV parsing and silently moves votes into the wrong fields.

**Fix:** quote all fields, which is standard CSV and costs nothing.

### 3. 🔴 Mixed character encodings across years, including CP850
*Files: LGE/NPE exports.* We have encountered UTF-8 with BOM, **CP850** (a
DOS-era code page) and **UTF-16** in the same series — Tshwane's 2011 file is
UTF-16 while its 2021 file is UTF-8. Party and place names carrying
diacritics decode to mojibake, and mojibake breaks party-name matching, which
silently drops or duplicates a party's votes. We sniff the encoding per file
(`src/iec_csv.py: sniff_encoding`).

**Fix:** publish everything as UTF-8.

### 4. 🔴 Header punctuation and spacing drift between years
*Files: LGE/NPE exports.* Column names change shape between elections, so a
fixed header map breaks or, worse, matches the wrong column.

**Fix:** freeze the header row across years, or publish a schema version.

### 5. 🔴 Seat Calculation Detail changes layout **and reassigns its letters**
*Files: `Seat Calculation Detail` (xls), 2011 vs 2021.*

The formula is published as `Q = (A / (B − C − D)) + 1`. But in the 2021
report **A** is the total valid votes, while in the 2011 report **(A) labels
the seat count** and the valid-vote total is not published at all. The same
letter means different quantities in different years. A parser keyed on the
letters silently compares the wrong things; we match on wording instead and
derive the missing total from the party rows (`src/official_seats.py`).

**Fix:** keep the letters consistent with the formula, and always publish the
valid-vote total.

### 6. 🔴 Impossible turnout values
*Files: derived from the VD result and registration figures.* **87
voting-district-years in Johannesburg alone show turnout above 105%** — more
votes cast than registered voters. These are dropped rather than modelled
(`src/turnout.py`, MODEL-LOG §1.13).

**Fix:** publish registration as at the voting day for each election, or flag
districts whose roll changed mid-cycle; a >100% turnout should never survive
publication.

### 7. 🟠 Programmatic access is refused
*`results.elections.org.za`, `www.elections.org.za`.* Automated requests are
blocked regardless of user agent, so bulk collection has to be done by
clicking each file in a browser session. Generated report files are
curl-able; the SPA shell and bulk archives are not.

**Fix:** allow ordinary HTTP access to published results, or provide an API.
Election results are a public record.

### 8. 🟠 Elections are identified by opaque internal IDs, not years
The portal identifies an election by an arbitrary number (2021 LGE = 1091,
2016 = 402, 2011 = 197), and **the national and provincial halves of the same
election day have different IDs** (2019 provincial is 827, not the national
number). Guess wrong and the site does not error — **it returns a different
election's results**.

**Fix:** accept a year and ballot type in the URL, or at minimum error on an
unknown combination rather than serving other data.

### 9. 🟠 One election is missing from the results portal
The 2014 national and provincial vote is absent from the current portal; its
files live on a second, older host.

**Fix:** complete the archive on one host.

### 10. 🟠 By-election reports are locked behind session-bound tokens
Per-contest reports are reachable only via `ReportViewer?_f=<token>` links
that fail outside the browser session that generated them. The by-election
*dashboard*, by contrast, is backed by static JSON needing no session — and
is richer than the PDF (voting-district level, all parties, candidate names).

**Fix:** expose the same static JSON from the downloads page.

### 11. 🟡 Municipality and province codes are not the obvious ones
Nelson Mandela Bay is `NMA`, not NMB. Western Cape is `WP`, not WC.
KwaZulu-Natal is `KN`, not KZN. Undocumented, and a wrong guess returns an
error page with HTTP 200.

**Fix:** publish the code list; return a real status code for an unknown one.

### 12. 🟡 An HTML error page is served with HTTP 200
A missing report returns a small HTML page and a success status, so an
automated fetch saves an error page as if it were data. We check the payload
prefix (`src/fetch_iec.py`).

**Fix:** return 404.

---

## Municipal Demarcation Board

### 13. 🔴 The 2026 voting-district layer carries a stale registration field
The field reads as current voter registration. It is **a snapshot from 2024**.
Anyone weighting by it believes they are using 2026 figures.

**Fix:** name the field with its vintage (`REG_2024`), or publish the date in
the layer metadata.

### 14. 🟠 Historic voting-district boundaries are not published anywhere
Needed to verify a district concordance geometrically across delimitations.
We checked the MDB's full service list, both DCAT catalogues, ArcGIS Online,
the IEC's GeoServer and an Internet Archive sweep of both hosts. Not
available. (Recorded as an open item, MODEL-LOG obstacle O6.)

**Fix:** publish past VD layers as an archive.

---

## Statistics South Africa

### 15. 🟠 Census 2022 Small Area Layer is request-only
Income, dwelling and employment data at small-area level is supplied on
request rather than published. The ward-level product (age, sex, population
group) is downloadable and is what this model uses instead.

**Fix:** publish the SAL product like the ward product.

---

## Before submitting: re-verify

**Re-run every check against a freshly downloaded file first.** Two reasons.
Layouts and encodings may have been fixed since we hit them, and reporting a
defect that no longer exists costs credibility. And at least one figure here
cannot be re-derived from the working data: the 87 impossible-turnout
district-years were counted *before* the pipeline drops them, so
`data/processed/turnout.csv` now shows none — that number must be
re-measured from the raw result and registration files, not quoted from here.

A short verification pass before sending: re-download one file per issue,
confirm the defect still reproduces, note the download date beside each item,
and drop anything that has been fixed.

## How to reproduce any of these

Each item names the file and the code that works around it. The whole
pipeline is public: <https://github.com/Psi-am-i/jhb-election-model>. The
acquisition recipes, including the exact URLs and election IDs, are in
`SOURCES.md`.

*Maintained as issues are found. Last updated 2026-08-08.*
