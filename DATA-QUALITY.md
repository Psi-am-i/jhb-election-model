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

⛔ **THE ORDERING, STATED ONCE AND AT THE TOP** (owner, 2026-09-06; it was
previously recorded only inside the struck-through repair below, which is the
wrong place for a standing rule). **Registration and votes outrank the census,
always.** Both require an in-person appearance with an ID book: they are
administrative events, as close to a count as this data gets. The census is a
survey estimate with sampling error, a disputed post-enumeration adjustment and
a different reference date. So when the two disagree, **the census yields** —
and a ratio above 100% is a statement about the estimate, never a licence to
revise the roll.

**What the census is still needed for, and it is not nothing.** The roll and the
results carry **no population group**, so the census is the only available
apportionment key for the pool split, and it is the soft ceiling on the eligible
pool — *room for growth*, which does not decide an election. Those are its two
jobs. It is never a validator: a census-derived denominator that comes in under
a hard count is evidence the estimate is stale, over-adjusted or wrongly
allocated at ward level, not evidence the count is too high.

**Where the model obeys this**: `_nest` forces every ward to its published
registration and vote totals, so the counted quantity is exact and only the
*split* is estimated; the violation message says so in those words; the
`census_correction` ratio is filed as *"a property of the census, not of the
model"*; and the 2026-08-26 repair that lifted the census to fix the ratio was
reverted after measuring worse.

⚠️ **Where it does not, and this is the open item**: `REGISTRATION_MAX = 2.0` is
a census-derived ceiling on a counted quantity, and it **binds on four cells in
two cities** — Cape Town Indian/Asian 2011 and 2016, Mangaung Indian/Asian 2016
and 2021, re-measured on the shipped instrument 2026-09-06 and reproducing
JUDGEMENT-CALLS §L9's table. Where it binds, the census overrules the roll and
`_nest`'s row scaling pushes the surplus into the other pools of that ward. The
value is recorded as **deferred, not defended**; see §L9 and
`prereg/2026-09-05-registration-rate-bound.md`.

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

### NOT resolved in the model — attempted 2026-08-26, REVERTED 2026-08-27

> ⛔ **THE REPAIR DESCRIBED BELOW WAS REVERTED** (MODEL-LOG §1.102). The
> before/after table and the blend are no longer what the code does; the model
> reports this violation and carries on, as it did before. **The reason is not
> resignation.** Elections are decided by registered voters, the roll is a hard
> count, and the census adult figure is not an input the model consumes — so a
> rate above 100% is a fact about the census rather than a quantity to clamp.
> Correcting it in the pool sizes measured WORSE (+8 seats, +3.09 CRPS) because
> pool size and fitted rate are jointly identified by the votes: their product
> was already right. Kept below as the record of what was tried.

**The data problem above is still real and Stats SA has not answered it.** What
changed is that the model no longer carries it forward.

Until 2026-08-26 the policy was *"nesting violations are reported, not
clamped"*, on the argument that clamping would bury a public-record defect
inside our own numbers. That argument protected the record and did nothing for
the model: **reporting the 187% never stopped it propagating**, and every
party's fitted appeal rate in that pool was computed against a denominator
1.87× too large. The DA's fitted appeal among white voters read 66.8% — a figure
the model itself declines to call identified.

The owner's ruling: *"the roll and census do not agree, so I would blend them
since they are both direct measures. But we should not allow anything more than
100%. And nothing will ever be 100% let alone 156%."*

So both measures now move, the ceiling is hard, and Johannesburg 2021 becomes:

| group | adults (blended) | registered | registered / adults |
|---|---|---|---|
| Black African | 2,901,719 | 1,529,453 | 52.7% |
| Coloured | 150,147 | 121,459 | 80.9% |
| Indian/Asian | 124,414 | 109,832 | 88.3% |
| **White** | **504,547** | **459,967** | **91.2%** |

The white pool's adult count is lifted 1.48× and its registrations fall from an
impossible 560,217 to 459,967. **The published ward totals are untouched** —
2,220,710 to the voter, per ward — because that number is counted, not
modelled, and this machinery exists to split it, not revise it.

**The lift is reported, not hidden.** `pools.rates["census_blend"]` carries what
was applied and `census_blend_wanted` what the roll asked for; where they differ,
`MAX_CENSUS_LIFT` bound and the residue is still a live data problem. Johannesburg
asks ≈1.48× in both 2016 and 2021 — a stable, group-and-city-specific
discrepancy — while Cape Town's white pool asks for nothing. Mangaung 2016's
Indian/Asian pool asks **3.69×** and is clamped at 2.0, because 13,309
registered against a census population of 14,929 is not two measures disagreeing.

Constants in `JUDGEMENT-CALLS.md` section I. Mechanism in MODEL-LOG §1.100.
**The request to Stats SA stands**: publish registration by population group, or
the ward-level post-enumeration adjustment factors.

---

---

## 12. Every independent candidate is published under one name

**Where:** every IEC municipal product we hold — the VD-level party results
CSV, the Detailed Results PDF and the Seat Calculation Detail — for every
metro and every year from 2011 to 2021.

Independent candidates are not identified. All of them in a voting district
appear as a single row named `INDEPENDENT`, and no candidate column exists at
that level in any published file: Buffalo City 2021 has exactly one such row
per (ward, voting district, ballot), 89 of 89 cases. The Detailed Results PDF
carries the same single merged line for the whole municipality (`INDEPENDENT
8,383 ward votes, no PR votes`), and `fetch_iec.py`'s five report types are
all the IEC publishes for a municipal election.

**Why it matters:** a ward contested by several independents shows their
*sum*, so the bloc can top the poll when no individual did. Buffalo City ward
29200044:

| | ward votes |
|---|---|
| INDEPENDENT (merged) | 1,899 |
| African National Congress | 1,714 |
| Democratic Alliance | 735 |

The IEC records **C = 0** independent ward councillors for Buffalo City 2021.
Both facts are true: several independents stood, their votes are merged into
that 1,899, the largest polled under 1,714, and the ANC won the ward.

**The effect is not confined to that ward.** C leaves the seat pool *before*
the quota is struck — Schedule 1 gives `Q = (A / (B − C − D)) + 1` — so one
phantom ward win removes a seat from the divisor and moves the quota, and with
it every party's entitlement:

| | inferred C | published C | seats available | our quota | IEC quota |
|---|---|---|---|---|---|
| Buffalo City 2021 | 1 | 0 | 99 vs 100 | 3,555 | 3,519 |
| eThekwini 2016 | 5 | 4 | 214 vs 215 | 9,964 | 9,918 |

About 1% high in both, enough that the reconstructed council did not match the
IEC's and `backtest.py` refused to score either city. `A` itself is exactly
right in both (351,899 and 2,132,173, to the vote), so the votes and the
eligibility rule are sound — only the attribution of ward wins is not.

**What we do about it:** C is now *read from the IEC's Seat Calculation
Detail* rather than counted from the votes, in both `backtest.py` and the seat
tests, because it cannot be counted from data that has already been merged. A
run says so out loud when the two differ. The counted figure is kept as what
it is — an upper bound, since merging can only ever add apparent wins — and a
test asserts it never falls *below* the published C, which would mean the
ward-winner rule was wrong rather than merely imprecise.

**What it costs:** the model can no longer claim to derive the whole council
from votes alone for a city with contested independent wards; it takes one
structural input from the IEC. That is a real reduction in what the backtest
proves, and it is the honest one — the alternative was scoring two cities
against a council we had reconstructed wrongly. It does not affect a forecast,
which must predict independent performance rather than reconstruct it.

**Fixable by:** candidate-level results, which the IEC does not appear to
publish for municipal elections. Worth an enquiry to the Electoral Commission
alongside the outstanding Stats SA requests.

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

## `build_concordance.py` cannot regenerate the roll it produced (2026-08-17)

Found while establishing that the multi-city expansion is **not** blocked by a
delimitation change. Two defects, both live:

1. **`{CODE}` is never substituted.** The script reads
   `args.geo_dir / "vds2026_{CODE}.geojson"` literally, so it is broken for
   **every** city including Johannesburg — the committed
   `data/processed/vd_ward_2026.csv` **cannot be regenerated by the code that
   claims to produce it.** An input nobody can rebuild is an input nobody can
   check.
2. **`--out-dir` defaults to a hard-coded `data/processed`.** Fix (1) and run
   `--city tshwane`, and it would **overwrite Johannesburg's roll** — the same
   un-namespaced hazard that made every non-Johannesburg city silently load
   Johannesburg's wards, one script upstream, still live.

**The good news, and it changes the Phase 2 plan.** `data/raw/geo/vds2026_{CODE}.geojson`
**already exists for all eight metros** with every field the concordance needs.
Joined against each city's 2021-fitted composition:

    tshwane · ekurhuleni · mangaung · nelsonmandelabay · buffalocity   0.0% unmatched
    ethekwini  0.8%  (one new ward, 59500112)
    capetown   1.8%  (two new wards, 19100117/8)

Same ward-code prefixes, genuine 2026 ward-count growth, both far under the 50%
refusal threshold. **There is no delimitation blocker anywhere.** The expansion
was blocked by two lines in a build script, not by data acquisition — and the
"almost certainly a delimitation boundary" message that said otherwise was itself
the artefact of a wrong-city file fallback (MODEL-LOG §1.40).

*Maintained as issues are found. Last updated 2026-08-17.*


## Metro turnout, checked against the published record (2026-08-20)

Done as the substance of the Inside Politics cross-check (task #9), whose stated
purpose was catching a **mis-ingest on our side**. Their article pages return
**403 to automated fetching** — only the index is retrievable — and their
material is graphics rather than tables, so a comparison against it is by eye and
by a human. The check that actually serves the purpose does not need them.

Ward ballot, computed from the raw files, `Total_Valid_Votes` over
`Registered_Population`:

| city | 2011 | 2016 | 2021 |
|---|---|---|---|
| Johannesburg | 53.9% | 56.1% | **41.5%** |
| Tshwane | 54.5% | 58.3% | 44.1% |
| Cape Town | 63.7% | 63.3% | **46.1%** |
| eThekwini | 58.1% | 58.4% | 40.6% |

All four agree with the published record: the 2016 rise, the historic 2021
collapse against a national LGE turnout of 45.9%, Cape Town highest of the
metros and eThekwini lowest. **No mis-ingest at metro level.**

This does not check the ward-level series, which is where a delimitation
mismatch would show and where their ward heat maps would be genuinely useful to
a human reading them side by side. That remains an eyeball job for a person, not
a fetch.

## 13. The historic ingest was Johannesburg's in everything but its `--city` flag (2026-08-22)

**The worst defect found in this repository's inputs to date, because it wrote
silently-wrong files that passed every gate.** MODEL-LOG §1.70.

`src/ingest_historic.py` converts the six pre-2011 national IEC archives into
per-metro VD files. It advertises `--city` and had only ever been run for
Johannesburg. Run for anything else it failed in two ways at once.

### It wrote Johannesburg's 1999 election into seven other metros' files

`matches_city` returned on `spec["muni_match"]` **without ever looking at
`city`**, and `npe1999`'s `muni_match` is the two Johannesburg metropolitan
local councils. So `--city tshwane --year npe1999` collected Johannesburg's rows
and wrote them to `npe1999_approx_TSH_vd_party.csv`.

Seven such files were produced. Every one was **byte-identical to Johannesburg's
at 789,426 bytes**: 9,072 party-VD rows, 648 voting districts, 1,361,299 votes,
for metros ranging from Buffalo City (~370k votes) to Cape Town (~1.5M).

**And they passed the reconciliation gate — 648/648 VD-ballots, worst drift
0.00%.** They had to: the rows were Johannesburg's real rows, individually
valid. The gate checks that party votes sum to each VD's valid total. It cannot
check that the VDs are the right city's, and nothing else did either. This is
the identical failure the `matches_city` docstring already describes for Buffalo
City one archive earlier — where matching on the last word put 2,087 VDs and 5.1
million votes into a 350-VD metro — recurring in a code path that comment did
not cover. Caught only because the totals were compared across metros and were
the same number.

All seven were deleted the same hour. No measurement was ever taken against
them.

### And 2004 matched nothing at all

`npe2004` has no `muni_match`, so it fell to the code/name matcher and found
nothing for any metro but Johannesburg — then halted the run, which is why
`lge2006` and `npe2009` were never reached and the pre-2011 gap looked like a
data-acquisition problem for a fortnight. **It was not.** All eight metros are
in all four archives. The strings are simply not derivable:

| archive | Tshwane | Ekurhuleni | Mangaung | Buffalo City |
|---|---|---|---|---|
| `npe2004` | `PRETORIA - TSHWANE METRO` | `EAST RAND - EKURHULENI` | `FS172 - MANGAUNG` | `EC125 - BUFFALO CITY` |
| `lge2006` | `TSH - Tshwane Metro` | `EKU - Ekurhuleni` | `FS172 - Mangaung` | `EC125 - Buffalo City` |
| `npe2009` | `TSH - TSHWANE METRO` | `EKU - EKURHULENI` | `FS172 - MANGAUNG` | `EC125 - BUFFALO CITY` |
| `lge2000` | `Pretoria - Tshwane Metro` | *absent* | `FS172 - Mangaung` | `EC125 - Buffalo City` |

2004 and 2000 key the Gauteng and Eastern Cape metros on the **place**, and
every archive keys Mangaung and Buffalo City on their **pre-2011 municipality
codes** `FS172` and `EC125` rather than `MAN` and `BUF`. No rule recovers that.

### The fix

An explicit `MUNI_HEAD` table — archive → city → municipality head — enumerated
from the archives themselves, matching this module's stated philosophy of
describing each layout rather than sniffing it. Matching is on the token **before
`" - "`**, so a match cannot spread into a neighbouring municipality the way the
last-word fallback did.

**A missing entry is a REFUSAL, not a fallback.** That is the whole lesson: the
fallback is what wrote Johannesburg's election into seven other cities.

> ### ⛔ BOTH "DELIBERATE ABSENCES" RECORDED HERE WERE WRONG (2026-08-31/09-01)
>
> This paragraph used to end: *"Two absences are recorded deliberately —
> Ekurhuleni and eThekwini in `lge2000` (both constituted at that election), and
> every metro but Johannesburg in `npe1999` (which predates them all)."*
> **Neither survived being looked at again**, and the way each failed is the
> useful part, because a refusal that is wrong looks exactly like one that is
> right.
>
> * **`lge2000` for Ekurhuleni and eThekwini.** The table above marks Ekurhuleni
>   *absent* from `lge2000` and the note said "checked 2026-08-22 — do not add a
>   guess here". They are in that archive, as `East Rand - Greater East Rand
>   Metro` (9,813 rows) and `Durban - Durban Metro` (13,328) — and the heads
>   that find them, `EAST RAND` and `DURBAN`, were **already declared one row
>   down in `npe2004`**. This was not a guess that failed. It was a search that
>   stopped at the modern name, plus a note instructing the next reader not to
>   repeat it. **A refusal is only as good as the search behind it, and this one
>   documented the stopping point as a finding.**
> * **`npe1999` for every metro but Johannesburg.** 1999 predates every metro
>   *including* Johannesburg — 2000 was the first election under wall-to-wall
>   demarcation — so "Johannesburg is reconstructible and the others are not"
>   was never a real distinction. All eight are the sum of the councils that
>   amalgamated into them, enumerated in `MUNI_HEAD` and all tagged `_approx`.
>
> Johannesburg's own `npe1999` head list was **also** wrong while this was
> believed: it declared `("JOHANNESBURG MLC", "MIDRAND/ RABIE RIDGE/ IVORY PARK
> MLC")` and `matches_city` compares whole heads, so of five councils only
> Midrand could match. The file on disk was nonetheless correct — 9,072 rows,
> 648 VDs, 1,361,299 votes, all five councils present — because it predated the
> whole-head matcher. Re-ingesting with the corrected heads reproduces it
> **byte-identically** (sha256 `818d351ce629d8…`, unchanged in
> `data/archive_manifest.csv`), so no Johannesburg number moved.
>
> **Result: all sixteen pre-2011 metro files now exist**, `lge2000` and
> `npe1999` for all eight, every one at 100% reconciliation.
> `levels.KNOWN_ABSENT` is consequently **empty** — there is nothing left to
> declare. Fourteen of the sixteen are withheld from the model in
> `levels.HELD_BACK`, which is a different fact: *present and correct, not yet
> fed in, pending a stated diagnosis.* Do not read that as an absence.

### Verified

* Johannesburg re-ingests **byte-identically** (md5 unchanged), so no existing
  number moved.
* 21 new files across seven metros, **every one at 100% reconciliation, worst
  drift 0.00%**, with distinct and size-plausible totals: Cape Town 1,456,350
  votes at `lge2006`, Mangaung 301,043, Buffalo City 369,123.

  > **Six of those 21 are no longer on disk (2026-08-23, MODEL-LOG §1.75).**
  > `npe2004`, `lge2006` and `npe2009` for Mangaung and Buffalo City were
  > ingested, γ fold 3 was fitted from them, the pool specs and the panel were
  > measured with them present — and they were then removed with nothing
  > recording it. `levels._citywide` swallows the absence and returns `{}`, so
  > the θ record simply lost twelve transitions in silence. Re-ingesting
  > reproduces the two totals above to the vote, so the loss is repairable;
  > what is not repairable by re-ingesting is that no guard noticed.
  >
  > **Restored, dated and guarded (§1.78–§1.79).** The files left between
  > 09:43 and 13:32 on 22 August — `history.json` at 09:43 reproduces the
  > restored tree exactly, and `forecast_summary.json` at 13:32 matches the
  > damaged one on all 22 parties. Everything derived after 09:43 has been
  > re-run. `tests/test_data_coverage.py` now fails if any recorded raw input
  > goes missing, changes size, or sits on disk without being recorded.
* γ fold 3 now fits for all eight metros, which is what the 2016 targets need.

### Caveat on the pre-2011 footprint, especially Mangaung and Buffalo City

The eight metros' share of the eight-metro vote is smooth across four cycles,
which is the check that the new files are the right cities:

| metro | 2006 | 2011 | 2016 | 2021 |
|---|---|---|---|---|
| JHB | 19.3% | 19.9% | 20.1% | 20.2% |
| CPT | 20.3% | 20.4% | 20.0% | 19.9% |
| ETH | 16.7% | 17.8% | 17.8% | 17.0% |
| EKU | 14.6% | 14.4% | 14.4% | 14.7% |
| TSH | 12.0% | 13.3% | 14.1% | 14.7% |
| NMA | 7.8% | 6.7% | 6.1% | 5.8% |
| MAN | 4.2% | 3.7% | 3.8% | 3.8% |
| BUF | 5.1% | 3.9% | 3.7% | 3.9% |

Tshwane's rise and Nelson Mandela Bay's fall are real and continue through
cycles built from data that was never in question, so they are not artefacts of
this ingest.

**But `MAN` and `BUF` are keyed on `FS172` and `EC125` before 2011**, which are
their *pre-demarcation municipality codes*, and the 2011 demarcation moved
municipal boundaries as well as wards. Buffalo City's 5.1% → 3.9% step is larger
than any other metro's and is the shape a footprint change makes. So for those
two, the pre-2011 files describe a **different area** from the post-2011 ones,
not merely different wards inside the same area.

`ingest_historic.py` already warns that pre-2011 VD and ward identifiers predate
two delimitations and are usable for citywide party shares but not for spatial
work until a concordance exists. This is the stronger version of that warning
for two cities: **their citywide shares are not strictly comparable either.**
Not chased further, and recorded so a θ ratio computed across the 2006→2011
transition for Mangaung or Buffalo City is read with it in view.

---

## 13. The census cannot supply the votes the DA actually received

**Where:** Stats SA *Ward Statistical Product 2022* (population group and age
tables) read against IEC results for City of Johannesburg, LGE 2016 and 2021.

Item 11 records that splitting the roll across population groups puts **187% of
white adults on the voters' roll**. This is the same defect seen from the other
end, and it is the more decisive view, because it does not depend on the roll at
all — only on votes actually cast.

Johannesburg 2016, with the white pool sized from the census and blended half-way
toward the roll (`CENSUS_ROLL_BLEND` 0.5, MODEL-LOG §1.100):

| | |
|---|---|
| DA total votes | 451,225 (38.5% of the city — the DA took ~38%) |
| votes the white pool can cast | 289,055 |
| DA votes the fit needs from the white pool | 298,565 |
| **DA share of the entire white pool required** | **103.3%** |

**Every white voter in Johannesburg would have to vote DA, and there would still
not be enough of them.** And that is *after* the pool has been enlarged by 48%
from the census's own figure.

**Why this matters more than item 11.** Item 11 can be waved away as a
registration artefact — people registering where they do not live, students,
family addresses. This cannot. It says the census's white population is too
small to have produced the observed result, using only published votes and
published population. Either the census undercounts the white group in
Johannesburg, or the DA draws far more support outside it than any ward-level
ecological fit can identify — and the fit says the DA's rate in that pool is
**not identified** (4 of 74 parties in the white pool are).

**Two independent reasons to think the census is the problem, not the fit.**
The correction the roll demands is **stable and specific**: Johannesburg's white
pool asks for ≈1.48× in *both* 2016 and 2021, while **Cape Town's white pool
asks for no correction at all**. A fitting artefact would not replicate across
cycles in one city and vanish in another. And Census 2022's Post-Enumeration
Survey measured a **62% undercount for the white group** — the highest the UN
Population Division has recorded — with the published figures adjusted for it and
the adjustment itself disputed in both directions (item 11).

**What must be fixed, and the order.** This is a **census-level** problem and it
cannot be resolved by tuning `CENSUS_ROLL_BLEND`. Raising the blend hides the
contradiction by believing the roll; lowering it makes the arithmetic worse. The
pool sizes are downstream of a population estimate that is wrong, and the
sequence has to be:

1. **Establish a defensible white/Indian adult population for each metro ward**,
   independent of both the census's small-area estimate and the roll — Dorrington
   et al.'s independent projections (*S. Afr. J. Sci.* 2024) are the obvious
   starting point, and Stats SA's ward-level post-enumeration adjustment factors
   are the ask that would settle it.
2. **Then** re-derive the pool sizes.
3. **Only then** is the blend a meaningful dial rather than a way of choosing
   which impossibility to display.

**Reproduce:**

    .venv/bin/python tests/test_pool_bounds.py
      # test_no_emitted_composition_weight_is_arithmetically_impossible
      # joburg 2016 DA in White: weight 0.6617 against a maximum of 0.6406

**Open in the model.** MODEL-LOG §1.100 ships the registration-ceiling repair
with a measured cost and records it as a debt. This item is the reason the debt
exists and the thing that has to be fixed before it can be discharged.

## 14. 🔴 Two LGE cycles are on disk, reconciled, and invisible to `pools.py` (2026-08-29)

**This is a defect in this repository's own plumbing, not in the public record** —
which is why item 13 above, correctly, says the opposite about the same files.

`pools.metro_file` resolves only two candidates:

    data/raw/elections/_metros/lge{year}_{CODE}_vd_party.csv
    data/raw/elections/_reports/lge{year}_{CODE}_downloadable_party_results.csv

Those exist for **2011, 2016 and 2021 only**. The 2000 and 2006 metro results are
in the archive as `data/raw/elections/lge{year}_{CODE}_vd_party_clean.csv` —
**eight metros at 2006**, verified by item 13 at *100% reconciliation, worst
drift 0.00%* — and read every run by `levels._citywide`. `metro_file` returns
`None` for both years, for every metro.

> **Updated 2026-09-01, and the defect got BIGGER, not smaller.** When this item
> was written, `lge2000` existed for Johannesburg alone. It now exists for **all
> eight metros**, so `metro_file` is blind to sixteen reconciled files rather
> than nine. Re-checked on the settled tree after the 2026-08-31 re-emit:
> `metro_file('JHB','2006')` and `metro_file('JHB','2000')` both still return
> `None`, `entrant_record(lge_transitions(before='2016'))` is still **0 rows**,
> and all eight 2016 specs still carry `arrival_group: null`. **The fix did not
> land in that window** — it remains `POOLS-REEMIT-QUEUE.md` entry 4, and
> `archive/pools-preemit-2026-08-31/README.md` predicted the 2016 specs would go
> from `seeds = 0` / `arrival_group: null` to populated in that emit. They did
> not, because entry 4 was not taken. Verified by diffing all eighteen archived
> pre-emit specs against the emitted ones: **not one measured party's pool
> vector moved by more than 1e-12**; the only fields that changed were the
> unmeasured-entrant vectors and, for Cape Town alone, `registration_series` and
> `turnout_limits`.

**It is a path-and-format mismatch, not missing data.** The two candidate paths
are bulk-export format (`PARTYNAME`); the archive files are clean format
(`sPartyName`/`Party_Votes`). `pools._npe_citywide_for` **already reads the clean
format from that directory, inside the same module**, so the reader exists and is
not wired to LGE years. `pools.metro_roster`'s comment claims the header drift between the two
formats is handled in one place — that path cannot be taken.

**Measured cost.**

    metro_file('JHB','2006')                       -> None
    lge_transitions(before='2016')                 -> (('2000','2006'), ('2006','2011'))
    entrant_record(that)                           -> 0 rows
    arrival_group_record('2016')                   -> 6 rows (NOT empty)

`entrant_record` is empty, so `arrival_rules` takes its `if not record: return
{}, {}` exit and **all eight 2016 specs carry zero seeds and `arrival_group:
null`** — which is the entire reason the arrival-mechanism validation is one
cycle wide (§1.136). Note the record itself is *not* the constraint: six rows are
available. At 2021 `entrant_record` rests on **1 usable transition of 3**, at 2026
on **2 of 4**; `arrival_group_record` is 22 rows over three cycles at 2026 where
**five** cycles exist on disk. Every pools-side record is affected —
`measure_pool_ratios`, `entrant_record`, `_ward_reach`, `home_splinter_record`,
`splinter_record`, `arrival_group_record`, `metro_roster`.

**⚠️ The trap this creates for a reader**, and it caught two write-ups already:
item 13 says the 2006 archive is complete and guarded, which is TRUE — so an
empty arrival record reads as *"history is thin"* rather than *"the file is
unreachable"*. §1.135 concluded "not enough record to fit" and §1.136 §5
concluded a definitional gap; both were wrong, and §1.136 §9 corrects them. **An
absent record and an unreadable one return the same empty list and are opposite
findings.**

**How to check it.**

    .venv/bin/python -c "import sys;sys.path.insert(0,'src');import pools;\
      print(pools.metro_file('JHB','2006'), \
            len(pools.entrant_record(pools.lge_transitions(before='2016'))))"
    # prints "None 0" today

**Fix** is queued as `POOLS-REEMIT-QUEUE.md` entry 4. It is a `pools.py` change
and it **moves numbers**, not only `pools_sha`.

## 15. 🔴 `HELD_BACK` has a third reader it does not gate, and Cape Town's specs are already carrying the withheld data (2026-09-01)

**A defect in this repository's own plumbing, like item 14 — not in the public
record.** The pre-2011 files are correct; the question is which code is allowed
to see them.

`levels.HELD_BACK` withholds `lge2000` and `npe1999` for the seven metros
ingested on 2026-08-31 pending a diagnosis of their effect on the panel. Two
readers honour it: `levels._citywide` (the θ and ρ records) and
`pools._npe_citywide_for` (the splinter records), the second of which had to be
told to — its own docstring records that when it was not, `npe1999` "kept
flowing in through here … and the panel moved by 2.63 CRPS for no stated
reason".

**There is a third, and it is still open.** `pools.registration_series` walks
every CALENDAR year with a result template and calls `pools.pool_counts`, which
opens the election file for its per-VD registered population. Nothing on that
path consults the gate:

Run from the repository root, as `leak.py`:

    import sys; sys.path.insert(0, 'src')
    import levels as L, cityconfig, pools
    print(('lge2000', 'CPT') in L.HELD_BACK)
    print(L._citywide('data/raw/elections/lge2000_CPT_vd_party_clean.csv'))
    city = cityconfig.load('capetown'); cityconfig.use('capetown')
    print(pools.pool_counts(city, '2000', pools.load_config())
               .totals('registered').sum())

prints today:

    True
    {}                 # levels refuses the file
    1269582.0          # pools reads 1.27m registered voters out of the same file

**It has already reached the emitted specs.** Diffing all eighteen archived
pre-emit specs (`archive/pools-preemit-2026-08-31/`) against the ones emitted on
2026-08-31, Cape Town is the only city whose non-entrant fields moved:

| spec | field | before | after |
|---|---|---|---|
| `capetown/pools_2016.json` | `registration_series` | 2006, 2009, 2011, 2014 | **2000**, 2006, 2009, 2011, 2014 |
| `capetown/pools_2016.json` | `turnout_limits.pool[3].observed_high` (White) | 0.7484 | **0.8578** |
| `capetown/pools_2016.json` | `turnout_limits.pool[3].high` (White) | 0.8232 | **0.9435** |

`capetown/pools_2021.json` gains the same `2000` series row. No other city
gained one, because their 2000 wards do not join the census — which is a second
reason this is worth fixing rather than shrugging at: **the leak is city-shaped
and arbitrary**, present where the join happens to succeed and absent where it
does not, so it is not even a consistent bias.

`projected_pool_shares` reads only the last two years of the series, so the
extra `2000` row does not move the projection. The turnout limits are used, and
they moved.

**Why this matters beyond the numbers.** `HELD_BACK`'s own comment states that
withholding data on a *score* would be selection of training data on the test
set, and that it is therefore withheld only because its effect is **not
understood**. A quarantine that leaks through one of three readers cannot
support that argument: the effect being diagnosed is not the effect being
measured. The gate is imported rather than copied in `_npe_citywide_for`
precisely so it "cannot be true in one module and false in the other" — and it
currently is.

**How to check it.** The one-liner above, or:

    .venv/bin/python -c "import sys,json;sys.path.insert(0,'src');\
      print(sorted(json.load(open('data/processed/capetown/pools_2016.json'))\
                   ['registration_series']))"
    # ['2000', '2006', '2009', '2011', '2014'] today

**Fix** belongs with `POOLS-REEMIT-QUEUE.md`: it is a `pools.py` change, it
**moves numbers** for at least Cape Town, and it needs the window. Not applied
here — this item records it rather than fixing it, because taking the re-emit
window would destroy the measurement the current specs were taken with.

---

## Seven cities scored 2021 on a turnout projection built without the pre-2011 archive (found and fixed 2026-09-10, §1.222)

**Status: FIXED. Effect on scored numbers: none, measured.**

`<city>/2021/turnout.csv` for buffalocity, capetown, ekurhuleni, ethekwini,
mangaung, nelsonmandelabay and tshwane predated the 2026-08-09 pre-2011 archive
ingest. They were missing `turnout_{1999,2000,2004,2006,2009}` and
`lambda_2011`, so λ̂ had no 2011 anchor, and `turnout_2021_projected` — the
column `montecarlo.py` reads as `ratio_pattern` — differed from what the code
produces on 207 to 709 VDs per city, mean |Δ| 0.020, max 0.30. Johannesburg's
files were current at all three years; the other seven were a month stale.

The same sweep found the 2016 files stale in a way that is inert (the added
columns are all pre-2011 and `prior_years` is `>= "2011"` at that target), and
eleven `fold*_parameters.csv` stale only in `theta_calibrated`, which the
forecast never reads.

**How it went unnoticed.** `turnout.csv` carries no `artefact_key`, unlike
`pools_*.json`. `montecarlo.run_model` says so in a comment — *"a stale or rebuilt
copy moves every draw in silence"* — and records the citywide levels it was
given as a delivery proof, but nothing compares that record against what the
generator would produce. **A recorded value is not a check.**

**How to check it.** There is no key to compare, so the check is a
regeneration. Delete every CSV under a copy of `data/processed` in a scratch
root, re-run the generators from empty, and diff:

    src/build_concordance.py --city <c>   # per city
    src/build_crosswalk.py
    src/byelections.py
    src/turnout.py --city <c> --target <y>
    src/gamma_recent.py --city <c> --target <y>
    src/fold.py --fold <n> --city <c>

Purging first is what makes the population honest: a file nothing rewrote
reports "identical" trivially, and an mtime fence does not catch it because
`cp -R` restamps.

**What is still open.** `turnout.csv` still has no artefact key, so this can
recur silently the next time an ingest lands. The durable fix is a key on it,
or the regeneration diff above run as a test.

## 16. 🔴 `history.json` and `history.md` are two DIFFERENT runs, and prose cites them as one artefact (found 2026-09-13)

**Every document in this repository that says "the committed 24-row artefact"
means one of two files that disagree.** Measured on Atlas, read-only, at
`7fcfd30`:

| file | commit it records | panel `seat_abs_err_coherent` |
|---|---|---|
| `data/processed/history.json` | `efa06f78…`, `git_dirty: true`, `manifest.schema` **1** | **725** (summed over its 24 `records`) |
| `data/processed/history.md` | `1d9a0e1d…`, `+dirty`, per its own token line | **723** |

`history.md` is the later, polls-off run (§1.225); `history.json` is the
2026-09-10 run that preceded the switch. They sit side by side in the same
directory under names that read as a pair, and **nothing in either file says the
other is from a different tree.** That is how "725" and "723" both came to be
quoted as the current panel total in the same week — `HANDOVER.md` has them as a
before/after pair, which is correct, and other prose has them as alternatives,
which is not.

⛔ **AND BOTH ARE NOW BEHIND THE CODE.** `manifest.schema` is **1**; the
instrument repairs of 2026-09-13 (§1.228, §1.229) raised `HISTORY_SCHEMA` and
changed what several columns mean — the held column set, the baselines' scoring
statistic, and the χ² the calibration table prints. **So any figure sourced to
either file is awaiting the canonical run, not merely a cycle out of date**, and
that includes the CRPS margin, the per-band z-scores and every `n_scored`.

**What a citation must therefore carry:** which of the two files, the commit in
its manifest, and the schema. A bare "the committed artefact" no longer
identifies anything. The run's own token line
(`seat_abs_err_coherent=<n>/@<commit>+dirty/<draws>d/pools:<sha>/rows=<n>`) is
the right thing to quote, because it carries all three.

**Not fixed here.** The repair is the canonical run on a settled tree, after
which both files come from one invocation; until then the pair is a tripwire,
not a source.
