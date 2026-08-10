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

### 10a. 🔴 Vote counts carry thousands separators, so the biggest numbers are the ones that break
*Files: pre-2011 bulk exports (1999/2004/2009 NPE, 2000/2006 LGE), in
`VALID VOTES` / `Valid Votes  Cast`.*

Counts below a thousand are plain digits; counts of a thousand or more are
written `"1,656"`. Both forms appear in the same column of the same file.
CSV parsing succeeds — the field is quoted — and the failure lands on
`int()`, which is where a reader is most likely to skip the row rather than
stop.

The damage is severe *because* it is selective: only cells with four or more
digits are affected, which is precisely the large parties in the busy voting
districts. Measured on Johannesburg's 2009 provincial ballot, dropping the
unparseable cells loses **606 of 15,180 rows — 4.0% of rows but 68.4% of
votes** (1,014,620 of 1,483,848). The ANC reads 35.87% instead of 62.35%;
COPE reads 29.90% instead of 9.61%. Nothing errors, and the result is
plausible enough to publish.

We strip separators and count every rejected cell, reporting the count
(`src/ingest_historic.py`); the write is gated on a separate reconciliation
check that party votes sum to each district's valid total.

**Fix:** publish raw integers. Failing that, use one format per column.

### 10b. 🔴 A comma in a *party's own name* shifts every later column
*File: 2006 LGE bulk export.*

Entry 2 records this for voting-station names. It also happens in the party
field: `SUNRISE PARK, PROTEA CITY AND GREENSIDE RESIDENTS' ASSOCIATION`
is written unquoted, so the name splits across two fields and every
subsequent column moves one place right. The ballot-type cell then holds a
fragment of the party name, the registration cell holds the registered count
and the turnout percentage run together (`311100.00%`), and the party's votes
end up in the spoilt-votes position.

In Johannesburg this hits all six voting districts of ward 79400053 and
erases **469 ward-ballot votes** for that residents' association — a party
that simply vanishes from any straightforward read of the file. It is
detectable (the ballot-type cell is not a ballot type) and the recovered
votes close each district's shortfall exactly, which is how we verified the
repair (`src/ingest_historic.py`).

**Fix:** quote all fields.

### 10c. 🟠 Five elections are published only at an unlinked URL
*Files: 1999/2004/2009 NPE and 2000/2006 LGE bulk exports.*

Entry 9 notes 2014 missing from the portal. The pre-2011 elections are
further out of reach: they are absent from the downloads page, absent from
the portal's report routes (the shape that serves 2019 and 2024 returns 404
for election id 169, the 2009 provincial vote), and reachable only at

    www.elections.org.za/content/uploadedfiles/{YYYY}%20{NPE|LGE}.zip

which nothing links to. The data is complete and good once found — our 2009
Johannesburg extraction reconciles to the Commission's own published report
to the vote — but a researcher has no way to discover it exists.

**Fix:** link these from the downloads page alongside 2014 onward.

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

## 11. More registered voters than adults, in one population group

**Where:** Stats SA *Ward Statistical Product 2022* (population group and age
tables) read against the IEC's registered totals for LGE 2021, City of
Johannesburg, 135 wards.

Splitting each ward's published registration across population groups — one
rate per group, fitted across wards, then scaled so every ward matches its own
published total — gives:

| group | people | aged 20+ | registered | registered / adults |
|---|---|---|---|---|
| Black African | 4,053,803 | 2,867,723 | 1,438,596 | 50% |
| Coloured | 229,528 | 148,214 | 122,572 | 83% |
| Indian/Asian | 167,363 | 118,062 | 99,326 | 84% |
| **White** | 333,651 | 300,374 | **560,217** | **187%** |

560,217 registered white voters against 300,374 white adults. The city totals
reconcile (3.43M adults, 2.22M registered, 64.7%); only the split does not.

**Why it matters:** any model that sizes voter groups from the census inherits
this. Ours did, invisibly, until the levels were separated — a single
votes-per-person figure had the error folded into it and still reproduced the
correct total vote, because the aggregate was fitted rather than derived.

**It is not a simple undercount, and that is the point.** Census 2022's
Post-Enumeration Survey measured a **62% undercount for the white group and 72%
for the Indian group** against a 31% national figure — the highest the UN
Population Division has recorded, about 10 percentage points above the previous
worst. But the published figures are already adjusted for that, and the
demographers who reviewed them argue the adjustment **overshot**: the census
sits **14% above independent projections for the white group and 24% above for
the Indian group** (Dorrington et al., *S. Afr. J. Sci.* 2024). If the
published white population is if anything too high, the true adult count is
lower than 300,374 — roughly 263,000 — and the ratio above rises from 187% to
about **213%**. The census problem does not explain this gap; it widens it.

**Candidate causes**, not mutually exclusive and not separable from published
data alone:
1. **ward-level allocation.** The same review reports "several significant
   anomalies in the sub-provincial data". These are modelled small-area
   estimates, so the provincial total can be right while the ward split is not.
2. **voters registered where they do not live** — registration is by voting
   district, and registering at a property or family address is common.
3. the ecological assumption that one registration rate applies to a group
   across all wards.

**Fix:** publish registration by population group, or by voting district
alongside small-area census counts, so the split does not have to be inferred.
Failing that, publish the ward-level post-enumeration adjustment factors so
users can see where coverage was weakest.

**Reproduce:** `python src/pools.py --city joburg --target 2026`, which prints
the violation, or call `pools.pool_counts(city, "2021", cfg)` and read
`.violations`.

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

*Maintained as issues are found. Last updated 2026-08-10.*
