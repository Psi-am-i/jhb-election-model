# Pollster review of DATA-PLAN.md

2026-10-23. Reviewer: pollster standpoint (`~/.claude/skills/pollster`), read-only.
Reviewed: `DATA-PLAN.md` as of 17:19 on 2026-10-23, against `DATA-USE-AUDIT.md`,
`INVENTORY.md`, `PLAN.md`, `PLAN-REVIEW.md` and the code on `site-sweep-1` at
`90037fd`. No model, test or sweep was run. One read was made under `nice -n 15`
and is marked **measured** where used; code claims marked **read** were checked
at the cited line; the rest relies on the audit and is marked as the audit's.

## Summary

The structure is right: one store, one gate, one definition per quantity, and
tests that fail on a second reader. That is the real-time-dataset design
(Croushore & Stark 2001, high confidence) applied to elections, and it answers
the owner's "haphazard and inconsistent" directly.

Six defects need fixing before anything is built:

1. **The gate as specified refuses the backtest's own roll.** The plan defines
   the roll at an election as the registration in that election's result file,
   and defines "clean" as `public_on` < polling day. A result file is public
   after polling day, so every backtest row loses its roll, its ward map and its
   ballot presence, or the code grows a special case that lets the whole row in.
   `PLAN-REVIEW.md` Q5 named this ("file-level granularity"); the store design
   reproduces it at row level.
2. **The pre-freeze list in §7 contradicts `PLAN.md` 5.1** ("freeze … on the
   current settings") and, item by item, either cannot be done in the window or
   does not reach the 2026 forecast (Q3 below).
3. **"Read-only collection; no model change" for C5/C7 is false as the fetcher
   is written.** `src/fetch_byelections.py` writes by default to
   `data/raw/byelections/byelections_{province or SA}_vd_party.csv` (**read**,
   `:158`, `:189`; only the 2016 cycle takes a `_2016` suffix, `:29`), which are
   the current-cycle files `byelections.py` (`:346-348`) and `bye_value.py` read.
   A refresh overwrites live model inputs.
4. **A14 is mis-resolved.** It is a leak of the target's own votes cast into
   backtest poll conversion, filed under "turnout defined three ways". `NATIONAL_VOTES`
   and `PROJECTED_METRO_SHARE` are dicts in `src/polling.py` (`:482`, `:530`,
   **read**); the gate cannot see a dict in source.
5. **A5's resolution overrides a stated reason without engaging it.** The code
   comment at `montecarlo.py:1176-1182` (**read**) says 2026 uses fold 1 so that
   fold 2 stays a validation fold.
6. **Derived artefacts are outside the gate.** Test 1 polices reads of
   `data/raw/` and spine files; the leaks this project has had came through
   `data/processed/` artefacts (`fold*_parameters.csv`, `turnout.csv`,
   `width_record.json`, pool specs). `PLAN.md`'s definition (a derived table's
   `period_end` is computed as the maximum over its inputs, and a loader refuses
   a later one) is not carried into the data plan.

**What may start now:** C8's SuperWEB2 attempt; the A6 label fix; the
read-only A3 trace and the 2009/2014 national–provincial gap bound; C5/C7
fetches only with `--out-dir` outside `data/raw/byelections/`. **What waits on
the changes below:** the store, anything that replaces a live input, and every
§6 resolution.

## Answers to the plan's four questions

### 1. Are the section 2 definitions right, and is anything missing?

| Term | Verdict | Change |
|---|---|---|
| Ballot | Incomplete for 2024. The 2024 NPE had three ballots (national compensatory, regional, provincial) under the Electoral Amendment Act 2023 (high confidence). "NPE national" is ambiguous for 2024. | Name `NPE national (compensatory)` and `NPE regional` separately for 2024; C2 fetches both. |
| Votes cast | Right as a derived figure; silent on conflict with the zips' `TOTAL VOTES CAST` (C3 will list differences). | State which is canonical when they differ (recommend the IEC's own field, with valid + spoilt kept as a check column). |
| Turnout | Per ballot is right as a table fact. The model consumes one turnout per VD, and A3's definitions differ on exactly the open choices: which ballot, whether spoilt counts. | Define one *turnout of record* per election kind: LGE = PR ballot (every voter in the municipality receives it, including out-of-ward voters; medium confidence on the IEC rule), NPE = the ballot whose shares the route reads. Retire "higher of the two" (`turnout.read_turnout`, `:83-108`, **read**) or justify it in `JUDGEMENT-CALLS.md`. |
| Turnout, VD level | Missing: section 24A votes. At an NPE a voter may vote outside the registered VD and the vote is counted where cast, so VD cast ÷ VD registered is not the turnout of that VD's voters; commuter VDs exceed it. The 2014 zips carry `SECTION 24A VOTES` (`INVENTORY.md`). | Carry `s24a` beside `special` in `vd_totals`; VD-level turnout is reported net of s24a where the source has it, and ward or city level otherwise. |
| Share | Right per ballot. Missing two things: (a) a party's ward share where it stood in only some wards (*contested share*, used by A10's readers); (b) the combined ward + PR vote that seats follow (seat-entitlement memory note). | Add `contested share` and `combined vote` as defined terms. |
| Roll | Ambiguous and, with the gate, self-refusing (Summary 1). "One roll per run" reads as one roll for history and target alike, which would be wrong: each past election's quantities sit on its own roll. | "Each election's quantities on its own roll; one **target** roll per run, dated." The target roll enters `rolls` with `public_on` = the certification or snapshot date, extracted from the result file by a reviewed script, so the gate admits it without opening vote rows. |
| Geography | VD level is right (`PLAN-REVIEW.md` Q4). Two inputs exist only at ward level: Census 2022 and the 2026 roll (`INVENTORY.md`). | Make the downscaling rule part of the definition (ward → VD by registration weight, one function), and the split-VD rule (one method for every city; the audit shows three: whole VD in backtests, solver at JHB 2026, `WardPop` at TSH 2026). State that no backtest exercises split VDs, since no historic result file splits one (`INVENTORY.md`). |
| Party identity | Right in form. The source test should be "public before the target that uses it", not "before the event's next election". Missing: independents. Result files carry one name for all independents (`INVENTORY.md` inconsistency 3); each independent candidate is its own contestant. | Change the test; add an `independent` rule (candidate-level identity). |
| Period / Clean for T | `period_end` and `public_on` at row level cannot represent a result file row whose roll is pre-election and whose votes are post-election. Gating on polling day also lets a backtest see more than the frozen forecast saw: the forecast is frozen 31 October and admits nothing published between then and 4 November. | Gate on an `as_of` date recorded per run (default: polling day; the forecast's own: freeze date); permit backtests at the forecast's lead time (Tashman 2000, high). Column-level `public_on`, or separate tables for pre-election facts (roll, delimitation, nominations, statute). |
| Census exception | Right, and matches the owner. Census 2011 and 2001 should be used where *released* before T, not where enumerated before it: Census 2011 (enumerated October 2011, released 2012; medium confidence on the release month) is ex-post at T = 2011. | "Latest census released before T"; the owner's 2022 exception applies only where none is held. |
| Held back | Conflates a data defect (1999 approximate, MAN and BUF different areas before 2011, `INVENTORY.md`) with a diagnostic switch (`levels.HELD_BACK` exists "pending a diagnosis", `INVENTORY.md`). | Two lists: `defective` (excluded for every reader, permanently) and `withheld for diagnosis` (an arm, recorded per run). |
| Missing | Statute per election (council size, ward count, overhang rule: A15); boundary changes of the municipality itself (Tshwane absorbed Metsweding's municipalities in 2011, high confidence; Mangaung absorbed Naledi in 2016, medium); polls (absent from the store; say whether deliberately). | Add `statute` and `municipal_extent` tables; add `polls` with `fieldwork_end` and `published_on`, or state that polls stay outside the store and why. |

Naming: `src/spine.py` collides with `levels.spine`, the model's θ/ρ spine. Call the store something else (`src/store.py`).

### 2. Is a single gated store right, and what would still let a later fact in?

**Right structure.** What it does not see:

| Path | Why the gate misses it | Fix |
|---|---|---|
| Derived artefacts | Built from a view, then cached in `data/processed/` with no target; `turnout.csv` carries no artefact key (`CLAUDE.md` §3). | Every artefact records the view(s) it was built from (city, target, `as_of`, store checksum); a loader refuses an artefact whose view does not match the run. Check that `pools.emit_pools`' `artefact_key` would carry the view record. |
| Hand-typed `public_on` | Self-declared metadata; a mislabelled row passes. | `public_on` comes from a per-source table with its citation; a derived table's `period_end`/`public_on` is the maximum over its inputs, computed by the writer. |
| Constants, curated dicts and code | `NATIONAL_VOTES`, `PROJECTED_METRO_SHARE`, `pools.SPLITS`, `parties.ALIASES`, `DEFAULTS` chosen on the panel. The four tests cannot see them. | Pointer to `PLAN.md` 3.1 in the plan; the alias and lineage tables move into `parties` with dated sources. |
| Geometry built later | `vd_concordance.csv` and `vd_links` by geometry use the 2026 VD layer, the only VD polygons held (`INVENTORY.md`). | `vd_links` rows carry the vintage of the geometry; a backtest that uses a 2026-geometry link is labelled. |
| Truth | Scoring must read the target's results; test 1 would fail `compare_history` or exempt it. | A separate `store.truth(city, T)`, callable only from the scoring process, which runs after the forecast artefacts are written and hashed (`PLAN-REVIEW.md` Q5). |
| Revisions | "Rebuilt, never edited" keeps one vintage. Rolls, MDB layers and census estimates are revised or overwritten (the IEC roll page holds one snapshot, `CLAUDE.md` §4b; `REGPOP` is labelled current and is 2024, `INVENTORY.md`). | Key facts by vintage; a view returns the latest vintage with `public_on` < `as_of`. |
| The store build itself | Rebuilding the store moves every measurement in flight. | The rebuild is a re-emit window under `CLAUDE.md` §3: one writer, nobody measures. |

**The four tests are absence tests** and must meet the project's four-part rule
(`CLAUDE.md` §4): state the population scanned and assert it equals the set of
model modules; two-sided bounds; a planted violation that fails and clears when
reverted; constructed input. Test 2 ("each defined quantity has one
implementation") has no stated way to detect a second implementation; say how
(a registry of quantity → function, and a grep for the computations it names),
or label it argued, not tested.

### 3. Which of A1–A17 matter most for the 2026 forecast, and should any be fixed before the freeze?

The frozen forecast is the only out-of-sample number the model will have this
cycle, and every backtest score is withdrawn, so a change made before 31 October
cannot be scored before it is published. Pre-freeze work should be clean input
refreshes, label fixes and read-only traces. Item by item for Johannesburg 2026:

| Item | Reaches JHB 2026? | Before the freeze |
|---|---|---|
| A7 by-elections act only at JHB 2026 (`w_bye`, κ, local ward term); no backtest row scores them (audit) | Yes, three mechanisms | Most consequential. No fix possible in the window. Run the forecast with the by-election terms off as an old-vs-new sensitivity arm and state on the page that these terms are unscored. |
| A5 γ from fold 1 (2014→2016) | Yes | Not a swap. The code's reason (fold 2 is the validation fold) is a real reason; the counter-reason is that every backtest row uses the most recent qualifying fold, so 2026 is the only row built differently. Run fold 2, and a pooled fold 1 + 2, as sensitivity arms; the choice is the owner's, in `OWNER-DECISIONS.md`. 2019→2021 was a low-turnout cycle (national LGE turnout about 46%, high confidence), which argues against fold 2 alone. |
| A3 two turnout models in one run | Yes | Untraced: pool turnout sets pool votes (`montecarlo.py:3202`, **read**) and `turnout.csv` sets the VD pattern rescaled to λ̂ (`:6745-6752`, **read**); which decides a seat is not known (audit §3). Trace it, read-only, and record the answer. No change. |
| A2 rolls | Partly: `turnout.py` weights λ̂ by the NPE 2024 roll while `run_model` sizes by the 2026-09-26 snapshot | Record it. Refresh the snapshot only if the IEC's certified roll is now published and the snapshot predates roll closure; the README does not say which (`archive/iec-registration-2026-09-26/README`, "live registration statistics page"). |
| A11 VD universe | **No, at JHB 2026.** **Measured** 2026-10-23 from `data/processed/vd_ward_2026.csv` and `data/raw/elections/npe2024_JHB_vd_party.csv`: 865 crosswalk VDs, 1,059 VD-ward rows, 375 rows flagged split; 0 crosswalk VDs and 0 of 2,417,915 `part_registered_2026` voters absent from NPE 2024's 865 VDs. | Nothing. Other city-years not counted. |
| A6 provincial called national | Labels only. Deciding the ballot needs C1/C2 and 5.2, which §7 puts after 4 November. | Fix labels (ActionSA's 6.22%). A cheap bound is available read-only: the 2009 and 2014 national-ballot rows are in the zips on disk (`INVENTORY.md`); the per-party national–provincial gap for Johannesburg in those years bounds what A6 could move. |
| A1 quarantine ignored by four readers | No. Johannesburg is exempt from `HELD_BACK`, and at 2026 the ignoring readers reach no 2000 or 1999 file (`turnout.py` λ from the last two pairs; fold 1; benchmarks are not in the forecast). | Nothing. |
| A10 contestation sources | Only for undeclared parties; the JHB 2026 roster is the certified list (`judgements/joburg-2026.toml:219-261`, pasted 2026-09-16, `complete = true`, **read**) | Nothing. |
| A12, A13 Tshwane | Only if a Tshwane 2026 page goes live; the site says "No 2026 forecast yet" (`content/joburg/NUMBERS-REVIEW.md:3199`, **read**) | Nothing unless Tshwane is published before polling day; then A12 blocks it. |
| A8 windows | Yes: turnout anchors ≥ 2011, α from 2011–2021, level shrink chosen on 2016/2021 all act at 2026, built the same way as every backtest row | Nothing changes; list them in the published input list. |
| A4, A9, A14–A17 | No (backtest-only, off, or maintenance) | Nothing. |

**Add before the freeze:** publish `inputs_preflight --strict`'s output, plus a
one-page list of which data each part of the frozen forecast reads (the audit's
matrix, 2026 column), beside the hash. That is the honest pre-freeze answer to
the owner's question.

### 4. Is the collection list complete for the analysis the owner asked for?

Missing:

| # | Item | Why |
|---|---|---|
| C13 | NPE 2024 regional ballot, beside the compensatory national ballot | Three-ballot election (Q1) |
| C14 | Section 24A votes per VD, every NPE where the zips carry them | VD turnout (Q1) |
| C15 | Certification date of the voters' roll per election, from IEC media releases or the Government Gazette; municipal certified totals for 2011, 2016, 2021 | `public_on` for the roll (Summary 1); a check on the result file's registration; the pre-election roll arm in A2 |
| C16 | Community Survey 2016 at municipality level | `PLAN-REVIEW.md` change 15, dropped here |
| C17 | Statute per election: council size, ward count, seat formula and overhang rule, with the gazette or IEC worked example | A15 |
| C18 | Municipal extent changes 2000–2026 (MDB) | Citywide series break at Tshwane 2011 and Mangaung 2016; a common-area series is needed for 5.1's citywide pairs |
| C19 | Reconcile the IEC roll page's 862 (JHB) and 796 (TSH) VDs against the crosswalks' 865 and 774 (`INVENTORY.md` item 6) | The forecast roll |
| C20 | Census age by ward (voting-age population), for each census held | Splits registration change into population growth and registration rate in 5.1's decomposition |
| C21 | Polls, if they stay in the model: house, mode, frame, fieldwork dates, publication date, ballot asked | Machine-readable fieldwork dates before any poll enters a backtest |
| C22 | A stored list of held by-elections per cycle, independent of the dashboard | `INVENTORY.md`: no completeness check is possible without it; C7 only compares the dashboard with itself |

C10 should also cover a Johannesburg refresh if the certified roll is published
after 2026-09-26. C11 rightly excludes Johannesburg and Tshwane (both certified
lists are entered).

## Does the plan answer the owner's request as written?

The owner asked where the plan is for diligent collection and consistent
analysis, given that the data used across the model is "entirely haphazard and
inconsistent". The plan answers with a structure that would remove the
inconsistency and a collection list that closes most gaps. Missing:

1. **What the frozen 2026 forecast uses.** Almost all of the plan lands after
   4 November, so the forecast published on 31 October will carry A2, A3, A5
   and A7 as they are. The plan does not say this. The owner should read it in
   the plan, and readers should see the input list beside the hash.
2. **The model's records are not tied to the analysis.** §5 computes retention,
   turnout and change tables; `levels.theta_record`, `local_record` and
   `pools.turnout_record` compute the same quantities separately. Unless §6
   says the model's records *are* §5's tables, the store produces a fourth
   reader of retention and the analysis and the model can disagree again.
3. **The audit's open questions are not carried.** Eleven questions in
   `DATA-USE-AUDIT.md` §3 have no plan item, including which turnout model
   decides seats and whether `_metros/`/`_reports/` agree with the clean files
   in EKU, ETH, MAN and NMA. Each needs an item or a stated reason to leave it.
4. **Diligence has no ledger.** "Each item ends with the data … or the exact
   reason" is right; add one table (`SOURCES.md` or the store manifest) with,
   per item: attempted on, by whom, source URL, result. `INVENTORY.md` found
   four gaps with "no record of an attempt"; a ledger is what prevents a fifth.

## Audit inconsistencies mis-resolved or missing in §6

| Audit | Plan's resolution | Problem | Correct resolution |
|---|---|---|---|
| A1 | One held-back list | Keeps the JHB/other-metros asymmetry, which conflicts with A8's "same window for every city" | Split defective from diagnostic (Q1); the regime effect figure the audit says measured only part of the gate is in-sample and withdrawn, so re-measure it on the store with the gate applied to every reader |
| A2 | One roll per run | Wrong as worded (Q1 Roll); silent on the split-VD rule | One target roll per run; one split-VD method; state that backtests cannot exercise split VDs |
| A3, A9, A14 grouped | One turnout definition | A9 is the benchmark using different turnout inputs from the model (an opponent on different data); A14 is a leak | A9: benchmarks read the same turnout table as the model, and the margin over uniform swing is re-measured. A14: the contested share at a backtest comes from the view at `as_of`; `NATIONAL_VOTES` and `PROJECTED_METRO_SHARE` move into the store with dates |
| A4 | Census 2011/2001 replace 2022 "for the targets they precede" | "Precede" should be "released before"; ignores the cause the audit names (a second VD→ward resolver, `pools.vd_map` skipping blank wards while `_ward_resolver` fills them) | Cite C4 as the fix for `national_fit_refused` at 2021; one resolver |
| A5 | Most recent fold, every city | Ignores the validation reason in the code; drops the audit's other two findings: the fallback (`gamma_recent.csv`) exists for JHB and TSH only, and is fitted LGE→NPE but applied NPE→LGE; and fold files of different dates | Owner decision with arms (Q3); one fallback rule for all cities, fitted in the direction it is applied; every fold file regenerated from one commit |
| A6 | 5.2 decides | Fine after 4 November; §7 wrongly lists it pre-freeze | Labels before the freeze; the decision after |
| A7 | Every city from the national file | Omits the 2016–21 file as the 2021 target's input, `bye_value.py` target-awareness (`PLAN.md` 3.5), fetched registration (C5), and the literal `share_2021` column at `montecarlo.py:6628` | Name all four |
| A8 | One window per quantity, same for every city | Different quantities may legitimately have different windows; the defect is that none is declared | Each window declared with its reason in `JUDGEMENT-CALLS.md`; any window chosen by score is chosen inside the rolling origin |
| A15 | Statute in force at each election | No source named | C17 |
| Audit §3 | — | Not carried | Plan item per question (above) |

## Changes to the plan

1. **§2 Roll:** replace with "Each election's quantities on its own roll. One target roll per run, dated, recorded. A past target's roll and VD→ward map enter `rolls` and `vd_ward` from a reviewed extract, with `public_on` = the roll's certification date; the vote rows are not opened to build them."
2. **§2 Period / Clean:** add `as_of` per run (default polling day; the forecast's is its freeze date); gate on `public_on` < `as_of`. Pre-election facts held in a result file (roll, ward map, ballot presence) are stored in their own tables with their own `public_on`.
3. **§2 Ballot:** name the 2024 compensatory and regional ballots separately.
4. **§2 Votes cast and Turnout:** name the canonical votes-cast field; define one turnout of record per election kind; carry `s24a` beside `special`; state VD-level turnout net of s24a where held.
5. **§2 Share:** add `contested share` and `combined vote`.
6. **§2 Geography:** add the ward → VD downscaling rule and one split-VD method; state that backtests cannot exercise split VDs.
7. **§2 Party identity:** source public before the target that uses it; add candidate-level identity for independents.
8. **§2 Census:** "the latest census released before T; Census 2022 (the owner's exception) only where none is held"; labelled at every output.
9. **§2 Held back:** split into `defective` (every reader, permanent) and `withheld for diagnosis` (an arm).
10. **§3:** rename `src/spine.py` (collides with `levels.spine`); add tables `statute`, `municipal_extent`, and `polls` or a statement that polls stay outside the store; key every fact by vintage.
11. **§3:** every derived artefact records the views it was built from; its `period_end`/`public_on` is the maximum over its inputs, computed by the writer; a loader refuses an artefact whose view does not match the run (carry `PLAN.md`'s definition).
12. **§3:** add `store.truth(city, T)` for scoring only, in a separate process after the forecast artefacts are hashed.
13. **§3:** the store rebuild is a re-emit window under `CLAUDE.md` §3.
14. **§4 C5/C7:** fetch with `--out-dir` outside `data/raw/byelections/`, and do not replace the live files until an approved change does so with an old-vs-new report. Strike "no model change" until then.
15. **§4:** add C13–C22 from Q4; extend C10 to a Johannesburg refresh if the certified roll is published after 2026-09-26.
16. **§4:** add a collection ledger (attempted on, by whom, source, result) for every item.
17. **§5:** state that §5's tables are the model's records (θ, ρ, turnout and arrival records are read from them), so analysis and model share one implementation.
18. **§5.1:** Duncan–Davis bounds per cell for the R×C case, with gross flows labelled ecological estimates (King 1997; Freedman et al. 1998); ward-level comparisons across delimitations report the linked share and are labelled as subject to the modifiable areal unit problem (Openshaw 1984).
19. **§5.1:** citywide pairs across a municipal extent change are computed on a common area, or marked.
20. **§6:** apply the corrections in the table above (A1, A2, A3/A9/A14 split into three, A4, A5, A7, A8, A15).
21. **§6:** add one item per open question in `DATA-USE-AUDIT.md` §3, or a stated reason to leave it.
22. **§6 tests:** each test states its population, a two-sided bound, and a planted violation that fails and clears; test 2 states its detection method or is labelled argued.
23. **§7 "before the freeze":** replace the candidate list with: (a) old-vs-new sensitivity arms for A7 (by-election terms off) and A5 (fold 2; pooled folds 1 + 2), each reported to the owner, the choice in `OWNER-DECISIONS.md`; (b) the A3 trace, read-only; (c) the A6 labels and the 2009/2014 national–provincial gap bound, read-only; (d) the roll check in A2; (e) the input list published beside the hash. Default if the owner does not choose: freeze on current settings, as `PLAN.md` 5.1 says.
24. **§7:** state in the plan that the frozen 2026 forecast carries A2, A3, A5 and A7 as they are, and that A1 and A11 do not reach it (A11 measured above).

## Rejected claims

| Claim | Why rejected | Evidence |
|---|---|---|
| C5/C7 fetches are read-only collection with no model change | The fetcher's default output path is the file the model reads | `src/fetch_byelections.py:158`, `:189`; `src/byelections.py:346-348` |
| A1 should be fixed before the freeze where it reaches 2026 | It does not reach JHB 2026: JHB is exempt, and the ignoring readers reach no 2000/1999 file at 2026 | `INVENTORY.md`; audit §2 item 1 |
| A6 is a pre-freeze candidate | The decision needs C1/C2 and §5.2, scheduled after 4 November | `DATA-PLAN.md` §7 |
| "Most recent fold" is the obvious single rule for A5 | The 2026 exception has a stated validation reason; 2019→2021 is a single low-turnout transition | `montecarlo.py:1176-1182` |
| A11 could move the JHB 2026 forecast | 0 of 865 crosswalk VDs and 0 of 2,417,915 voters are absent from NPE 2024 | measured 2026-10-23, Q3 |
| A14 is a turnout-definition problem | It is the target's own votes cast entering a backtest's poll conversion | audit §2 item 14; `polling.py:1000-1037` |

## Sources and confidence

| Source | Used for | Confidence |
|---|---|---|
| Croushore, D. & Stark, T. (2001). A real-time data set for macroeconomists. *Journal of Econometrics* 105(1). | Vintage-keyed store; gate on what was public at the origin | High |
| Tashman, L.J. (2000). Out-of-sample tests of forecasting accuracy. *International Journal of Forecasting* 16(4). | Evaluation at the forecast's own origin and lead time (`as_of`) | High |
| Duncan, O.D. & Davis, B. (1953). *American Sociological Review* 18(6). | Bounds in §5.1 | High |
| King, G. (1997). *A Solution to the Ecological Inference Problem*. | Bounds plus model; EI as estimate | High |
| Freedman, D.A. et al. (1998). Review of King (1997), *JASA* 93(444). | Point estimates treated as known understate uncertainty | High on the critique, medium on citation detail |
| Openshaw, S. (1984). *The Modifiable Areal Unit Problem*. CATMOG 38. | Ward comparisons across delimitations | Medium |
| Reif, K. & Schmitt, H. (1980). Nine second-order national elections. *European Journal of Political Research* 8(1). | National→local pairs as the predictor; why the national-vs-provincial choice is empirical | High |
| Electoral Amendment Act 1 of 2023 (South Africa) | Three ballots in the 2024 NPE | High |
| Electoral Act 73 of 1998, s 24A | Voting outside the registered VD at an NPE | High on the provision; medium on how the IEC files record it per VD |
| Municipal boundary changes (MDB): Tshwane + Metsweding 2011; Mangaung + Naledi 2016 | C18 | High (Tshwane), medium (Mangaung) |
| 2021 LGE national turnout about 46% | A5's low-turnout caveat | High |
