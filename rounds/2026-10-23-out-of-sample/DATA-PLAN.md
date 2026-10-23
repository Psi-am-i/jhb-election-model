# Data plan: one consistent dataset, read one way (v2)

Owner, 2026-10-23: "Where is the plan for more dilligent data collection and
consisten analysis? … the mismatch in what data we are using for various parts
of the model is entirely haphazard and inconsistent."

Evidence: `INVENTORY.md` (what is held) and `DATA-USE-AUDIT.md` (what each part of
the model reads; its 17 inconsistencies are A1–A17, its open questions Q-a…Q-k).
v1 was reviewed in `DATA-PLAN-REVIEW.md`; v2 applies all 24 of its changes.
`PLAN.md` (the backtest round) carries out its steps 1–3 through this plan.
Nothing here is built until the owner has read it.

## 1. The rule

Every part of the model reads the same facts, defined once, from one store,
through one gate that knows the date the forecast is made as of. A second reader
of a fact, or a second definition of it, is a defect, and a test finds it.

## 2. Definitions

| Term | Definition |
|---|---|
| Ballot | LGE ward, LGE PR, NPE national, NPE provincial, and for 2024 the compensatory national and the regional ballot, each named. Nothing is called "national" that is the provincial ballot (A6). |
| Votes cast | the source's `TOTAL VOTES CAST` where it has one, else valid + spoilt; `special` and `s24a` carried beside it where the source has them. |
| Turnout | votes cast ÷ registered, per ballot. One turnout of record per election kind: the PR ballot for an LGE, the national ballot for an NPE. At VD level, net of s24a votes where held (s24a voters cast outside their VD). |
| Share, contested share, combined vote | share = party valid votes ÷ valid votes on one ballot; contested share = share among the wards a party stood in; combined vote = ward + PR valid votes, the statute's basis for seats. |
| Roll | each election's quantities on that election's own roll. One target roll per run, dated and recorded. A past target's roll and VD→ward map enter the store from a reviewed extract dated by the roll's certification (C15); the vote rows are not opened to build them. |
| Geography | quantities carried at VD level, placed in wards by one join, in the delimitation of the election they describe; moved to another delimitation by one crosswalk with weights and a linked-share figure; one rule for ward→VD downscaling and one for VDs split across wards. Backtests cannot exercise split VDs (no past file has one); stated wherever a backtest is quoted. |
| Party identity | one table of codes, names by date and events (rename, merger, split), each with a source public before the target that uses it; independents identified per candidate. |
| Census | the latest census released before the target; Census 2022 (the owner's exception) only where none is held; labelled at every output it reaches. |
| Period | every fact carries `period_end`, `public_on` and a vintage. Every run carries `as_of`: polling day for a backtest, the freeze date for the forecast. **Clean** = `public_on` < `as_of`. A pre-election fact held in a result file (roll, ward map, ballot presence) is stored in its own table with its own `public_on`. |
| Excluded data | `defective` (excluded for every reader, permanently, with the defect) is separate from `withheld for diagnosis` (an arm, applied to every reader or none) (A1). |
| Window | each quantity's window of years declared with its reason in `JUDGEMENT-CALLS.md`; a window chosen by score is chosen inside the rolling origin (A8). |

## 3. The store

One generator, `src/store.py`, builds `data/store/` from `data/raw/` only. Its
rebuild is a re-emit window under `CLAUDE.md` §3 (one writer; nobody measures
while it runs).

| Table | One row per |
|---|---|
| `results` | election × ballot × VD × party: votes |
| `vd_totals` | election × ballot × VD: registered, valid, spoilt, cast, special, s24a |
| `rolls` | roll vintage × VD or ward: registered, certified on |
| `vd_ward` | delimitation × VD × ward part: weight, source |
| `vd_links` | VD in election A × VD in election B: method, confidence |
| `nominations` | election × ward × party: stood |
| `byelections` | contest × VD (× party): votes; registered, spoilt, cast as fetched |
| `census` | census × delimitation × ward × group (and age): persons, released on |
| `parties` | party × event: code, name, event, date, source |
| `statute` | election × municipality: council size, wards, formula, overhang rule, source |
| `municipal_extent` | municipality × period: area changes, source |
| `polls` | poll: house, mode, frame, fieldwork dates, published on, ballot asked (or a statement that polls stay out of the model) |

Every fact is keyed by vintage. Each table has a checksum and a manifest entry
(generator commit, inputs, checksums).

**The gate.** `store.view(city, as_of)` returns only clean facts, plus the
labelled census exception. Every model part gets its data from a view; the view
records what it returned, and that record is part of every run.

**Derived artefacts** (pool specs, `turnout.csv`, fold parameters, width record,
by-election weights) record the views they were built from; their `period_end`
and `public_on` are the maximum over their inputs, computed by the writer; a
loader refuses an artefact whose views do not match the run.

**Truth** for scoring is `store.truth(city, T)`, read only in a separate process
after the forecast's artefacts are hashed.

**What the gate cannot see**, and how each is covered: constants and lists in
code (`PLAN.md` 3.1's classification); a hand-typed `public_on` (each comes from
a cited source, reviewed); 2026 geometry (dated as a 2026 fact); revised vintages
(kept, not overwritten).

## 4. Collection

Johannesburg first, then the other seven. Each item ends with data in
`data/raw/` with provenance in `SOURCES.md`, or the exact reason it cannot be
had. **A collection ledger** (`rounds/2026-10-23-out-of-sample/COLLECTION-LEDGER.md`)
records every attempt: item, date, who, source URL, result. Nothing replaces a
file the model reads until an approved change does so with an old-vs-new report;
fetches go to a separate directory.

| # | Item | Source | Check |
|---|---|---|---|
| C1 | NPE national ballot 1999–2014 | zips on disk | party votes sum to valid votes |
| C2 | NPE national ballot 2019; 2024 compensatory national | IEC downloads | as C1 |
| C3 | Votes cast, special votes, every election | zips | cast against valid + spoilt, differences listed |
| C4 | Ward for NPE 1999 (via LGE 2000), 2004, 2019, 2024 (via the preceding LGE); one VD→ward resolver for every reader (fixes `national_fit_refused` at 2021, A4) | derived | share of registration assigned |
| C5 | By-election registration, spoilt, cast | dashboard contest files | every contest, both cycles |
| C6 | By-elections before 2016 | dashboard serves 2016 and 2021 only (404 otherwise, 2026-10-23); IEC media releases, municipal notices | or a reason per cycle |
| C7 | By-elections after 2026-08-07; JHB 2019-07 to 2021-11 | dashboard | against C22 |
| C8 | Census 2011 and 2001 by ward, population group and age | SuperWEB2 first; owner sends a request for what it lacks | ward counts per delimitation |
| C9 | Ward polygons 2000, 2006 | MDB | ward counts |
| C10 | 2026 rolls for the six metros without one; Tshwane's into its crosswalk; a Johannesburg refresh if the certified roll is published after 2026-09-26 | IEC ward page | against the IEC municipal figure |
| C11 | Certified 2026 rosters, six metros | IEC | `complete = true` only from the certified list |
| C12 | Party events with dated sources | IEC register, press | source before the next election |
| C13 | NPE 2024 regional ballot | IEC | as C1 |
| C14 | s24a votes per VD, every NPE where held | zips | per VD |
| C15 | Roll certification date per election; certified municipal totals 2011, 2016, 2021 | IEC releases, Government Gazette | against the result files' registration |
| C16 | Community Survey 2016, municipality level | Stats SA | citywide check for 2016 |
| C17 | Statute per election | gazette, IEC worked examples | reproduces the IEC seat calculation |
| C18 | Municipal extent changes 2000–2026 (Tshwane 2011, Mangaung 2016 at least) | MDB | common-area citywide series |
| C19 | Reconcile IEC 862/796 VDs against crosswalk 865/774 (JHB/TSH) | IEC, MDB | each difference explained |
| C20 | Voting-age population by ward, each census held | Stats SA | splits registration change |
| C21 | Poll metadata, if polls stay in the model | publishers | fieldwork and publication dates machine-readable |
| C22 | A stored list of held by-elections per cycle, independent of the dashboard | IEC, municipal notices | C6/C7 completeness |

## 5. Consistent analysis

**The analysis tables are the model's records.** θ, ρ, turnout and arrival
records are read from them, so the analysis and the model share one
implementation (no fourth reader of retention).

5.1 Every pair (LGE→LGE; NPE→LGE and LGE→NPE on the national and the provincial
    ballot), citywide and per ward, the same code for all eight metros: votes,
    vote change, share, retention, turnout, registration change (split into
    voting-age population growth and registration rate where C20 is held); the
    exact split of vote change into registration, turnout and share; where the
    votes went, net, with Duncan–Davis bounds per cell, gross flows labelled
    ecological estimates; population-group estimates labelled as ecological on
    the composition of the census used; how the changes change across
    consecutive pairs; by-elections against the elections either side and the
    correlation with the next. Ward comparisons across delimitations report the
    linked share and are labelled as subject to the areal-unit problem. Citywide
    pairs across a municipal extent change are computed on a common area or
    marked. A cell that cannot be computed says why.
5.2 Which national ballot predicts the local result better, on pre-target pairs
    only.

## 6. Moving the model onto the store

One change per row, written and reviewed by different agents, pre-registered
where it moves a number.

| Audit | Resolution |
|---|---|
| A1 | `defective` and `withheld` split; the withheld-files effect (in-sample, withdrawn) re-measured on the store with the gate on every reader |
| A2 | one target roll per run; one split-VD method; backtests stated not to exercise split VDs; a pre-election-roll arm where C15 holds a roll |
| A3 | one turnout of record per election kind; pool and VD turnout derived from one table; trace first (Q-a: which turnout model decides seats) |
| A4 | latest census released before T; one VD→ward resolver (C4) |
| A5 | owner decision with arms (fold 1; fold 2; folds 1+2 pooled), keeping the code's validation reason in view; one γ fallback rule for every city, fitted in the direction it is applied; every fold file regenerated from one commit |
| A6 | labels now; the choice of ballot after 5.2 |
| A7 | 2016–21 file as the 2021 target's input; `bye_value.py` target-aware; fetched registration (C5); the literal `share_2021` column at `montecarlo.py:6628` made target-aware |
| A8 | each window declared with its reason; score-chosen windows inside the rolling origin |
| A9 | benchmarks read the model's turnout table; margins re-measured |
| A10 | `nominations` only |
| A11 | universe from the target delimitation; measured not to reach JHB 2026 (0 of 865 VDs, 0 of 2,417,915 voters absent from NPE 2024; review, 2026-10-23) |
| A12 | Tshwane built from the same inputs as Johannesburg before publication |
| A13 | hard-coded paths removed; each reader run for a second city in a test |
| A14 | a leak, not a definition: the backtest's contested share from the view at `as_of`; `NATIONAL_VOTES` and `PROJECTED_METRO_SHARE` move into the store with dates |
| A15 | statute per election from C17 |
| A16 | one citywide-share reader |
| A17 | `parties` replaces both mappings |
| Q-a … Q-k | each of the audit's open questions gets an item or a stated reason to leave it (listed when the store work starts) |

**Tests** (each with its population, a two-sided bound, and a planted violation
that fails and clears): (1) no model module opens `data/raw/` or the store except
through `store.view` / `store.truth`; (2) each defined quantity has one
implementation — detection by a call-graph scan of the readers, or labelled
argued if no scan can see it; (3) a view at `as_of` holds no fact with
`public_on` at or after it except labelled census rows; (4) every run's record
lists its views.

## 7. Order, and what the frozen forecast carries

**The 2026 forecast frozen by 31 October carries A2, A3, A5 and A7 as they are;
A1 and A11 do not reach it** (A11 measured). Readers see the list of inputs the
forecast reads, and `inputs_preflight --strict`'s output, beside the hash.

| When | Work |
|---|---|
| now (no model change) | C8's SuperWEB2 attempt; C5/C7 fetches into a separate directory; the A6 labels; the A3 trace; the national–provincial gap per party for 2009 and 2014 from the zips; the A2 roll check; the collection ledger |
| before 31 Oct, owner's choice | old-vs-new sensitivity arms: A7 (by-election terms off) and A5 (fold 2; folds 1+2 pooled), each reported to the owner, the choice in `OWNER-DECISIONS.md`. Default if he does not choose: freeze on current settings (`PLAN.md` 5.1) |
| by 31 Oct | freeze; publish the hash, the input list and the preflight output |
| after 4 Nov | the store; C1–C4, C6, C9–C22; section 5; section 6 row by row; `PLAN.md` step 3 on the store, Johannesburg first |
