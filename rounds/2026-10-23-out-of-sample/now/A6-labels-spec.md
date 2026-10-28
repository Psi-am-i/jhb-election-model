# A6 labels: "national" where the files hold the provincial ballot — specification

Read-only specification, 2026-10-28, branch `site-sweep-1` at `99556398`, on
Scout. No file was edited except this one. Nothing was run that writes: the
measurements below are `git grep`, `unzip -p` to stdout and in-memory sums over
files in `data/raw/elections/`. Source: `DATA-USE-AUDIT.md` §2 item 6;
`DATA-PLAN-REVIEW.md` §3, row A6 ("Labels only… Fix labels (ActionSA's 6.22%)").
Which ballot the model should use is out of scope; this spec only makes the
words say which ballot it uses now.

## 1. The NPE files the model reads hold the provincial ballot

The model reads `data/raw/elections/npe<year>_<CODE>_vd_party.csv` (names in
`src/cityconfig.py:100-110`). Their canonical columns (`src/ingest_npe.py:47-58`)
are `Province, Municipality, Ward, VD_Number, VS_Name, Registered_Population,
Spoilt_Votes, Total_Valid_Votes, sPartyName, Party_Votes`. **No column records
the ballot**, so the file the model reads cannot say which ballot it is; only
the ingester and the source archive can.

| year | source archive (member) | how one ballot is chosen | evidence (**measured** 2026-10-28 unless marked) |
|---|---|---|---|
| 1999, 2004, 2009 | `1999_npe.zip`, `2004_npe.zip`, `npe2009_national_and_provincial.zip` (`<year> NPE.csv`) | `ingest_historic.SPECS` `prefer_event: "PROVINCIAL"` (`src/ingest_historic.py:74, 84, 93`), applied at `:396` as a strict filter: a row whose event lacks `PROVINCIAL` is skipped (`continue`). No fallback to national rows. | Each archive holds both events, so the filter has something to reject: 1999 232,400 rows `NATIONAL ELECTIONS 1999` / 185,642 `PROVINCIAL ELECTIONS 1999`; 2004 356,412 / 255,723; 2009 513,084 / 341,827. That the filter kept only the provincial rows is *inferred* from the code for these three years (no per-party comparison was made, as it was for 2014). |
| 2014 | `npe2014_national_and_provincial.zip` (`2014 NPE.csv`) | `ingest_npe.py --event` default `PROVINCIAL` (`:186-190`), filter at `:165` | Johannesburg sums over `npe2014_JHB_vd_party.csv` equal the archive's `2014 PROVINCIAL ELECTION` rows to three decimals (ANC 52.280%, DA 32.367%, EFF 10.130%, 22 parties). The `2014 NATIONAL ELECTION` rows give ANC 53.630%, DA 29.762%, EFF 10.149%, 29 parties. |
| 2019 | `npe2019_provincial_national.zip` (`827.csv`) | the archive holds one ballot (`ingest_npe.py:123-125`) | `SOURCES.md:31-36` lists portal id 827 as the 2019 **provincial** election (national is 699). The file has no ballot column; the number of parties differs by province (Gauteng 41, Western Cape 38, Northern Cape 22). A national ballot carries one list in every province. |
| 2024 | `npe2024_provincial_national.zip` (`Provincial.csv`) | as 2019 | Member name `Provincial.csv`; `SOURCES.md:63` gives the route `NPEPublicReports/1335/…/Provincial.zip` (1335 = provincial, `SOURCES.md:35`). Parties per province: Gauteng 47, Northern Cape 25. |

A row the model reads, `npe2024_JHB_vd_party.csv:4`:

    Gauteng,JHB - City of Johannesburg,,32840018,RIVERSANDS PRIMARY SCHOOL,1602,6,883,ACTIONSA,74

**ActionSA's 6.22% is this file.** Summing `Party_Votes` over
`npe2024_JHB_vd_party.csv`: ActionSA 88,013 of 1,415,548 valid votes = 6.218%,
44 parties. It is ActionSA's share of **Johannesburg's 2024 provincial
ballot**. Its share of Johannesburg's 2024 national ballot is not on disk (the
2024 archive holds only `Provincial.csv`), so no file here can say whether the
two differ.

**Turnout columns.** `Registered_Population` is the shared roll.
`Spoilt_Votes` and `Total_Valid_Votes` are provincial-ballot counts, so the VD
turnout level and λ (`turnout.py`, `fold.turnout_weights`) are
provincial-ballot votes cast over the roll. Rows describing them are sense T
below.

## 2. Vocabulary for the fix

"National" carries five senses in this repository. Every row below is tagged
with one.

| sense | meaning | action |
|---|---|---|
| **W** | a quantity read from the NPE files: share, vote, ballot, result, record, route, spine, baseline, fit, size, θ's denominator | relabel |
| **E** | the election event ("the national election", "the 2024 national election") | relabel in code and project documents; reader text by brief |
| **T** | turnout from the NPE files | relabel as provincial-ballot votes cast over the shared roll |
| **C** | correct, country-wide: "national swing", "nationally organised", "a national fact", "national CSV" (one file for the country), "national LGE turnout" | **keep** |
| **N** | correct, the national ballot or a national poll: `polling.py`, `contested_area.py`, `NATIONAL_VOTES`, `national_polls`, poll `scope = "national"`, the 2009/2014 national rows in the archives, the 2024 national compensatory ballot | **keep** (that polls report national-ballot intention is *inferred*, `DATA-USE-AUDIT.md` §2.6) |

One vocabulary, used in every proposal:

| rule | where the text names… | write |
|---|---|---|
| V1 | the election event | **NPE** in code and project documents ("the NPE before the target"); **national and provincial elections** in reader text |
| V2 | a number read from the files | **provincial-ballot share / vote / result** |
| V3 | a model construct built on those numbers (route, spine, baseline, record, fit, floor) | **NPE route / spine / baseline / record / fit / floor** |
| V4 | θ | **NPE-to-local retention ratio**; reader text: **provincial-to-local** |
| V5 | turnout from the files | **NPE turnout (provincial-ballot votes cast over the roll)** |
| V6 | senses C and N | unchanged |

V3 names the election tier, not the ballot, so it stays true if the ballot
decision (after 4 November) changes which ballot is read. V2 names the ballot
because the number is that ballot's.

## 3. The five most important items

1. **A live correction repeats the error it corrects.** `docs-public/corrections.md:241` (built to `site/corrections.html:180`):
   *"That is its share of Johannesburg's 2024 national ballot, not its national share."*
   The figure is the provincial ballot (§1). Proposed: *"That is its share of Johannesburg's 2024 provincial ballot, not its national share."* Reader-facing; needs the owner's brief, and under the corrections convention it is a new correction of a live page, with its own heading, published date and corrected date.
2. **Every rendering of 6.22% carries a tooltip naming the national ballot.** `src/tooltip_says.py:319-320`:
   *"ActionSA's share of Johannesburg's national ballot in the 2024 national election."* Rendered into `site/methodology.html:151` and `site/corrections.html:180-181`. Proposed: *"ActionSA's share of Johannesburg's provincial ballot in the 2024 national and provincial elections."* The token's `source` (`content/joburg/stats.toml:476`, published as `site/changes.json:3825`) says *"IEC NPE 2024, national ballot: ActionSA's share"*; proposed *"IEC NPE 2024, provincial ballot: ActionSA's share"*.
3. **The methodology describes θ as national-to-local.** `docs-public/methodology.md:105-112` and the claims register `content/joburg/model-claims.toml:71, 101, 206`. Exact sentences and proposals in §7.
4. **`src/levels.py`'s module docstring defines θ on "the national election" and quotes ActionSA "6.22% nationally".** `:22-23` and `:60-65`. Proposals in §5.
5. **`MACHINERY.md` records the mechanism in the same words.** θ row `:387` (*"θ national→local retention"*), `:214`, the spine `:400-405`, the own-record fit `:681-699`. Proposals in §6.

## 4. Class (a) — code identifiers

**Constraint.** `pools.py`'s code hash (`_code_sha`, `src/pools.py:210-245`)
is taken over the AST with comments and docstrings stripped, and covers
`pools.py` only. A comment or docstring in `pools.py` can change freely; a
**name or string literal** in `pools.py` moves `pools_sha`, invalidates every
`pools_*.json` and must go through `POOLS-REEMIT-QUEUE.md`. Identifiers in
other modules do not move the hash, but several are keys in artefacts or are
matched by tests.

Default for this round: **rename nothing that an artefact or test reads; fix
the docstring beside it.** Three renames are trivial and offered.

| identifier | defined | written to | read by | proposal |
|---|---|---|---|---|
| `fitted_from_national`, `national_fit_refused`, `unclassified_with_national_record` | `src/pools.py:6516, 6517, 6542` (spec keys) | every `pools_*.json` (each key in 27 spec files, **measured** by `grep -o`) | `MACHINERY.md:696-699`, `JUDGEMENT-CALLS.md`, `POOLS-REEMIT-QUEUE.md`, round documents | **Keep.** String literals in `pools.py`: renaming forces a full re-emit. Add one docstring line at `pools.py:6511` comment: "national" in these keys means the NPE (provincial ballot). Queue the rename (`npe_fitted`, `npe_fit_refused`, `unclassified_with_npe_record`) for the next batched `pools.py` change. |
| `national_fits` | `src/pools.py:5419` | — | `pools.py:6211`; `tests/test_national_record_fit.py:185`; `MACHINERY.md:686`; `JUDGEMENT-CALLS.md`; `POOLS-REEMIT-QUEUE.md`; `MODEL-INDEX.md` (generated) | **Keep** (a function name is in the AST). Fix its docstring (§5). |
| `national_fitted`, `national_refused` (locals) | `src/pools.py:6209-6241, 6408-6423` | — | — | Keep until the next batched `pools.py` re-emit (names are in the AST); then `npe_fitted`, `npe_refused`. |
| `NATIONAL_ONLY_FLOOR` | `src/pools.py:1042` | — | `tests/test_chain.py:1366, 1369, 2273`; `JUDGEMENT-CALLS.md:156` (§K1); `JUDGEMENT-SHEET.md`, `MODEL-INDEX.md` (generated) | **Keep.** Fix the comment at `:1043-1046` and the register row `JUDGEMENT-CALLS.md:156` ("The national share below which…" → "The provincial-ballot share below which…"). |
| `ARRIVED_VS_NATIONAL`, `ARRIVED_VS_NATIONAL_EXCLUDING_SPLITS`, `UNCLASSIFIED_WITH_NATIONAL_RECORD` | `src/pools.py:3620, 3626, 3648` (`ARRIVAL_DEFINITIONS` keys) | — | `# ARRIVAL DEFINITION: <NAME>` markers `pools.py:4149, 4208, 6228`, checked in both directions by `tests/test_chain.py:2538` `test_every_arrival_definition_is_named_where_it_is_computed`; `src/backtest.py:1127, 1232`; `src/compare_history.py:2234, 2267`; `src/seats.py:69`; `tests/test_chain.py:2642, 2684`; `tests/test_panel_wiring.py:19, 296, 302`; `tests/test_seats.py:533`; `MODEL-INDEX.md` | **Keep.** The predicates already say "preceding-NPE" (`:3621, 3649-3651`). Fix the text field at `:3635`: *"a party with a national record but no local one"* → *"a party with an NPE record but no local one"* (string literal in `pools.py`: batch it). |
| spine trace keys `detail[p]["national"]`, `routes["national_only"]`, `blend["moved_from_national"]`, `blend["at_full_national"]` | `src/levels.py:1837, 1734, 1741, 1743` | `--run-dir` `20_spine.json`; `data/processed/forecast_summary.json` ("national" ×109, the other three ×1, **measured**) | `tests/test_spine.py:183, 228-234, 645`; `tests/test_stage_estimation.py:56, 408, 440, 465, 515, 542-548, 594-624, 1306-1324, 1421, 1489, 1506`; `src/montecarlo.py:7208-7217`; `skills/forecast-stage-estimation/SKILL.md`; `MACHINERY.md:2117` | **Keep.** `tests/test_stage_estimation.py:56` already says the value is a level, not a vote share; add to `levels.spine`'s docstring (`:1654`) that `national` is the NPE route's level, from the provincial ballot. |
| route labels `"national only (first local election)"`, `"local only (no national record)"`, `"blend at full national (k=0)"` | `src/levels.py:1808, 1811, 1793` | `forecast_summary.json` (`route` values: 55 and 34 rows of the first two, **measured**); `20_spine.json` | `startswith("national only")` in `tests/test_spine.py:145, 469, 558`, `tests/test_stage_estimation.py:476, 547`; literal in `tests/test_stage_estimation.py:1299, 1495`, `tests/test_universal_draw.py:383`; quoted at `src/montecarlo.py:3718, 3724`, `MACHINERY.md:1397-1401` | **Keep** this round (seven test sites match the text). If renamed later: `"NPE only (first local election)"`, `"local only (no NPE record)"`, `"blend at full NPE (k=0)"`, all sites in one commit. |
| `national`, `nat_level` (locals in `levels.spine`) | `src/levels.py:1749-1811` | — | — | **Rename, trivial**: `national` → `npe_share`. No artefact, no test, not under the pools hash. `nat_level` may stay. |
| `party_kind` value `"national"`, output key `"national": {file, year}`, params `national`, `national_city` | `src/build_make.py:800-880, 987` | the page's bounds data (`city_limits[c].kind`, `party[p].kind`) | `interactive/js/builder-state.js:90, 119`; `interactive/js/make.js:805`; `tests/test_your_forecast_page.py:1102, 1108`; the shipped copy under `site/your-forecast/js/` | **Keep** the `"national"` value and key (page data contract). The params may be renamed `npe`, `npe_city` (local to `build_make.py`, trivial). |
| `inputs_preflight` label `"national baseline"` | `src/inputs_preflight.py:271`, matched at `:284` by `what.startswith("national")` | preflight output | `:284` (logic) | **Keep the logic**; if the label becomes `"NPE baseline"`, change `:284` to `startswith("NPE")` in the same edit. |
| test-internal names: `GONE_NATIONAL`, `spine_national`, `national_by_vd`, `stood_national`, `full_national`, `from_national`, `vs_national`, `national=` kwargs, `NATONLY`, test function names containing `national` | `tests/test_theta_prior.py:921-938`, `tests/test_universal_draw.py:382-388`, `tests/test_your_forecast_page.py:1096-1240`, `tests/test_stage_estimation.py`, `tests/test_national_record_fit.py:54-195`, `tests/test_spine.py:104-110` | — | the test itself; `run_all -k` filters | **Keep.** Renaming tests is not a label fix. |
| module `tests/test_national_record_fit.py` | — | — | `tests/run_all.py`; `JUDGEMENT-CALLS.md`; `MACHINERY.md`; `MODEL-INDEX.md`; `POOLS-REEMIT-QUEUE.md` | **Keep.** |
| claim ids `national-to-local-gap`, `split-placed-from-own-national-result`, `starting-level-blends-local-and-national`; probe `starting_level_is_local_national_blend` | `content/joburg/model-claims.toml:69, 99, 204-209` | the claims register | `tests/test_model_claims.py:229` | **Keep** the ids; the `text` fields are class (d). |
| `hist_asa_npe_2024` (token) | `content/joburg/stats.toml:472` | published ledger, `site/changes.json` | `src/tooltip_says.py:319`; `docs-public/*.md` | **Keep** — the name says NPE, which is right. |
| Correct, sense N/C: `NATIONAL_VOTES`, `national_polls`, `scope == "national"`, `SCOPES` (`src/polling.py:482, 783, 578`); `BigMapsNational` (IEC URL, `src/fetch_byelections.py:13, 101`); `lge2016_national`, `npe20xx_national_and_provincial` (archive file names, `src/archive.py`) | | | | **Do not change.** |

`ingest_npe.COLUMNS` has no ballot column, which is why the files cannot
declare their ballot (§1). Adding one is a data change, not a label fix; it is
noted for C1/C2.

## 5. Class (b) — comments and docstrings in `src/` and `tests/`

The full per-line list is Appendix B (592 lines, produced by the script
described in §9). The module-level texts that define the vocabulary come
first; fix these by hand, then sweep the appendix.

| file:line | current words | proposed words |
|---|---|---|
| `src/levels.py:22-23` | "θ, the national-to-local retention ratio: a party's share at a local election over its share at the national election before it." | "θ, the NPE-to-local retention ratio: a party's share at a local election over its provincial-ballot share at the NPE before it." |
| `src/levels.py:60-65` | "It converts a party's last NATIONAL share into a local one … 18.12% locally in 2021 against 6.22% nationally in 2024, and no θ of its own, so the forecast built it from the 6.22% and discounted it to about 6%." | "It converts a party's last NPE (provincial-ballot) share into a local one … 18.12% locally in 2021 against 6.22% on Johannesburg's 2024 provincial ballot, and no θ of its own, so the forecast built it from the 6.22% and discounted it to about 6%." Keep "nationally-organised" (`:61`, sense C). |
| `src/levels.py:682-687` | "Every observed national-to-local retention ratio before the target. … ``share`` is the national share the ratio was measured off. … Parties below 0.2% of the national vote" | "Every observed NPE-to-local retention ratio before the target. … ``share`` is the provincial-ballot share the ratio was measured off. … Parties below 0.2% of the provincial-ballot vote" |
| `src/levels.py:1654-1670` | "``baseline`` is the preceding national election's citywide shares; … sits on the national spine; … **National only.** … the national route … did not contest nationally, or was not yet national when it did." | "``baseline`` is the preceding NPE's citywide provincial-ballot shares; … sits on the NPE spine; … **NPE only.** … the NPE route … did not contest the NPE, or did not yet exist when it was held." Add: "The trace key ``national`` and the route label ``national only`` keep their names (§4 of the A6 spec)." |
| `src/pools.py:5422-5442` (`national_fits`) | "Every party fitted on the target's baseline NATIONAL election, by ward. … however large its national record … the national result file … The national file's voting districts … its own preceding national election … no national election before the target" | "Every party fitted on the target's baseline NPE (its provincial ballot), by ward. … however large its NPE record … the NPE result file … The NPE file's voting districts … its own preceding NPE … no NPE before the target". Docstring: does not move the hash. |
| `src/pools.py:5507` | "1. its own NATIONAL fit" | "1. its own NPE fit" |
| `src/fold.py:1` | "Backtest a national/provincial baseline against a local-government target" | "Backtest an NPE baseline (provincial ballot) against a local-government target" |
| `src/turnout.py:3-6` | "Local elections draw far fewer voters than the national/provincial elections that precede them. … N(x) for the national election preceding x" | first sentence sense C, keep; "N(x) for the NPE preceding x; its votes cast are the provincial ballot's" |
| `src/arrivals.py:10` | "**no share at all** of the national election the model builds its baseline from" | "**no share at all** of the NPE provincial ballot the model builds its baseline from" |
| `src/bye_value.py:14, 25-29` | ":14 "the outcome is a national-provincial list ballot"; :25 "converted to the national ballot by the model's own national-local relation"; :29 "at each party's 2019 national share" | ":14 "the outcome is the provincial list ballot"; :25 "converted to the provincial ballot by the model's own NPE-to-local relation"; :29 "at each party's 2019 provincial-ballot share". `:104` and `:375` ("the 2024 provincial ballot", "npe… provincial ballot") are already right. |
| `src/group_share_record.py:15-33, 123-183` | "every national election after one … the national election's own … for each national one … National elections after ``lge``" | "every NPE after one … the NPE's own … for each NPE … NPEs after ``lge``" |
| `src/theta_residual.py:25, 51, 110, 140` | "national election's citywide shares"; table header "national size"; "Size bins, in national vote share"; "``size`` is the national share" | "NPE's citywide provincial-ballot shares"; "NPE size"; "in provincial-ballot share"; "``size`` is the provincial-ballot share". `:448, 766, 1015` ("national swing") are sense C: keep. |
| `src/montecarlo.py:6160` | "# --- baseline: the last national election before the target" | "# --- baseline: the last NPE before the target (provincial ballot)" |
| `src/montecarlo.py:5725-5738` (f-string, reaches run output) | "party in the {target.previous_npe} national baseline … (a national-share floor … prior NATIONAL vote) … national baseline" | "party in the {target.previous_npe} NPE baseline … (a provincial-ballot share floor … prior NPE vote) … NPE baseline". Not under the pools hash; no test matches the text (`git grep`). |
| `src/pools.py:6407` (`derived_from` f-string) | "and on the {target.previous_npe} national election for N parties absent from it" | "and on the {target.previous_npe} NPE for N parties absent from it". **String literal in `pools.py`: batch with the next re-emit.** Reaches `pools_*.json` and `history.json` `derived_from` (64 occurrences, **measured**). |
| `src/pools.py:5943-5944` (print) | "parties held a {previous_npe} national vote below …" | "…{previous_npe} provincial-ballot vote below …" (batch). |
| `src/benchmarks.py:23, 94, 442-463` | "national elections that bracket it"; "the national election preceding"; "matches a *known* national result"; "gained 5 points nationally" | "NPEs that bracket it"; "the NPE preceding"; "a *known* provincial-ballot result"; "gained 5 points between the two NPEs" |
| `src/build_make.py:170, 359, 783, 823-828, 866` | "national result"; "A national result file by VD"; "no national result file for"; "national-to-local extremes"; "citywide national share" | "provincial-ballot result"; "An NPE result file (provincial ballot) by VD"; "no NPE result file for"; "NPE-to-local extremes"; "citywide provincial-ballot share" |
| `src/score_forecasts.py:138, 298, 310` | "the one-ballot national layout"; "from a national (NPE) VD-level file"; "not an IEC national VD result file" | "the one-ballot NPE layout"; "from an NPE (provincial ballot) VD-level file"; "not an IEC NPE VD result file" |
| `src/ingest_npe.py:1` | "Ingest IEC national/provincial election bulk result files" | keep (sense C); add after `:3`: "The output keeps one ballot, the provincial, and carries no ballot column." |
| `tests/test_stage_estimation.py:56` | "``detail[p]["national"]`` is not the party's national vote share" | "``detail[p]["national"]`` is not the party's provincial-ballot share" |

## 6. Class (c) — project documents

Excluded by instruction: `MODEL-LOG.md` (append-only), `audits/`, `rounds/`,
`prereg/`, `reports/`, `archive/`. Also excluded: `HANDOVER-ARCHIVE.md`
("NOTHING HERE IS CURRENT") and `OWNER-DECISIONS-ANSWERED.md` (the owner's
record; see below). Generated documents are fixed at their generator, never by
hand: `MODEL-INDEX.md` (`src/model_index.py`), `JUDGEMENT-SHEET.md`
(`src/judgement_sheet.py`), `SITE-TEXT.md` (`src/site_text.py --export`),
`content/joburg/NUMBERS-REVIEW.md` (`src/build_site.py`),
`data/processed/history.md` (`src/compare_history.py`). Their rows clear when
the source text in §4, §5 and §7 changes.

Per file, lines needing a change (Appendix C; script counts):
`JUDGEMENT-CALLS.md` 83, `MACHINERY.md` 46,
`skills/forecast-stage-estimation/SKILL.md` 14, `SOURCES.md` 13 (most of
`SOURCES.md` is sense C and stays), `DATA-QUALITY.md` 8,
`POOLS-REEMIT-QUEUE.md` 4, `judgements/joburg-2026.toml` 4,
`judgements/tshwane-2026.toml` 3, `PUBLISHING-BACKLOG.md` 2, one each in
`DUPLICATION-AUDIT.md`, `ITERATING.md`, `POLLING.md`, `README.md`, `TODO.md`,
`cities/joburg.toml`, `config/dimensions.toml`,
`judgements/ekurhuleni-2021.toml`, `judgements/joburg-2016.toml`.

Hand-checked rows that carry the mechanism:

| file:line | current words | proposed words |
|---|---|---|
| `MACHINERY.md:214` | "National → local retention." | "NPE → local retention (provincial ballot)." |
| `MACHINERY.md:255` | "its national share for θ" | "its provincial-ballot share for θ" |
| `MACHINERY.md:307` | "nat_level = national_share * exp(mu_theta)" | "nat_level = npe_share * exp(mu_theta)" (worked example; the code identifier changes only if §4's trivial rename is taken) |
| `MACHINERY.md:387` | "**θ** national→local retention" | "**θ** NPE→local retention (provincial ballot)" |
| `MACHINERY.md:400-405` | "A party's level comes from BOTH its previous national result (× θ) … on the national route … national spine's 0.275" | "…its previous NPE provincial-ballot result (× θ) … on the NPE route … NPE spine's 0.275" |
| `MACHINERY.md:511-512` | "has a national baseline … like every other party with a national record — the national and local routes"; "no national vote at all" | "has an NPE baseline … with an NPE record — the NPE and local routes"; "no NPE vote at all" |
| `MACHINERY.md:549-550` | "12.2% of Johannesburg's 2024 national vote"; "no 2019 national vote" | "12.2% of Johannesburg's 2024 provincial-ballot vote"; "no 2019 NPE vote" |
| `MACHINERY.md:681-699` | "A party with its own national record is fitted on it … the baseline national election … `fit_city` on the national result file … the national election's own … a party with a national record … a national fit" | "…its own NPE record … the baseline NPE … on the NPE result file (provincial ballot) … the NPE's own … an NPE record … an NPE fit". Keys `fitted_from_national`, `national_fit_refused` stay (§4). |
| `MACHINERY.md:1285` | "the outcome a national-provincial list ballot" | "the outcome the provincial list ballot" |
| `MACHINERY.md:1396-1401` | "took votes at the preceding national election … its own national result through θ … no national result" | "…the preceding NPE … its own NPE result through θ … no NPE result". The quoted route label stays. |
| `MACHINERY.md:1513, 1530` | table header "national size" | "NPE size (provincial-ballot share)" |
| `MACHINERY.md:111, 116` | "Why the fit is national" / "The national fit supplies the shape" | sense C (pooled over the eight metros). Keep, or write "pooled" to avoid a clash with `national_fits`; owner's choice. |
| `JUDGEMENT-CALLS.md:156` | "The national share below which a party with no local record…" | "The provincial-ballot share below which…" |
| `JUDGEMENT-CALLS.md:192` | "pure national spine" | "pure NPE spine" |
| `JUDGEMENT-CALLS.md:265` | "national share for θ" | "provincial-ballot share for θ" |
| `JUDGEMENT-CALLS.md:300` | "parties ≥5% of the national vote" | "parties ≥5% of the provincial-ballot vote" (check the source: θ dispersion is binned on NPE share) |
| `JUDGEMENT-CALLS.md:1110` (§SJ1) | "MK is fitted on its 2024 national ward results" | "MK is fitted on its 2024 provincial-ballot results by ward" |
| `DATA-QUALITY.md:1125-1149` | heading "four national elections have voting districts and no wards"; "publishes national results in two layouts" | "four NPEs…"; "publishes NPE results in two layouts" |
| `DATA-QUALITY.md:1231` | "no national baseline" | "no NPE baseline" |
| `POOLS-REEMIT-QUEUE.md:280` (item 41) | "A party with its own national record is fitted on it" | "…its own NPE record…". Items 11 and 17 (`:593-595`) quote the definition names; leave the names. |
| `POLLING.md:57` | "The conversion from a national number to a metro one" | sense N (polls): keep |
| `README.md:15` | "share a national swing" | sense C: keep |
| `ITERATING.md:180, 1225` | "national swing" | sense C: keep. `:605` "whose national file" → "whose NPE file". |

`OWNER-DECISIONS-ANSWERED.md:1094-1096` (*"Its share of Johannesburg's 2024
national ballot, 6.22%"*) and `:1110-1111` (*"share of Johannesburg's 2024
national ballot 6.22%"*) are the owner's record of questions put to him. Do not
edit; add a dated note under the entry: "2026-10-28: 6.22% is Johannesburg's
2024 **provincial** ballot (A6 labels spec §1)."

## 7. Class (d) — reader-facing text (needs the owner's approved brief)

Each row: the exact current sentence, and the proposal. Source files are
listed; built copies follow from them (`site/methodology.html`,
`site/corrections.html`, `site/review.html`, `site/sources.html`,
`site/forecast.html`, `site/changes.json`, `site/your-forecast/**`,
`SITE-TEXT.md`, `NUMBERS-REVIEW.md`) and must not be edited by hand.

**ActionSA's 6.22%** is the token `hist_asa_npe_2024`, value 0.0622
(`content/joburg/stats.toml:472-478`): ActionSA's share of Johannesburg's 2024
**provincial** ballot (§1). It appears on `/methodology` and `/corrections`.

**Every appearance of 6.22%** (`git grep -n '6\.22'`, whole tree, number-shaped matches inside unrelated floats removed). Each is Johannesburg's 2024 provincial-ballot share for ActionSA, from `npe2024_JHB_vd_party.csv`.

| file:line | exact words | class | action |
|---|---|---|---|
| `docs-public/corrections.md:241` → `site/corrections.html:180` | "said ActionSA polled {{hist_asa_npe_2024}} nationally in 2024. That is its share of Johannesburg's 2024 national ballot, not its national share." | (d) | §3 item 1; table below |
| `docs-public/corrections.md:243` → `site/corrections.html:181` | "ActionSA polled {{hist_asa_npe_2024}} in the city in the 2024 national election." | (d) | table below |
| `docs-public/methodology.md:111` → `site/methodology.html:151` | "{{hist_asa_npe_2024}} in the city in the 2024 national election" | (d) | table below |
| `src/tooltip_says.py:319-320` (tooltip on all three above) | "ActionSA's share of Johannesburg's national ballot in the 2024 national election." | (d) | table below |
| `content/joburg/stats.toml:476` → `site/changes.json:3825` | `source = "external:IEC NPE 2024, national ballot: ActionSA's share (MODEL-LOG, …)"` | (d) | table below |
| `publications/joburg/ledger.jsonl:1214, 1603, 2000, 2400, 2851, 3304, 3766, 4135, 4537, 4944, 5478, 5847, 6216, 6605, 6952` (15 rows, token `hist_asa_npe_2024`) | each row's `source` is the `stats.toml:476` string (read at `:1214`) | generated record | do not edit; past rows are history, new rows carry the corrected `source` once `stats.toml:476` changes |
| `SITE-TEXT.md:1246, 1688` | the methodology and corrections sentences above | generated (`src/site_text.py --export`) | follows its sources |
| `src/levels.py:64-65` | "18.12% locally in 2021 against 6.22% nationally in 2024 … built it from the 6.22%" | (b) | §5 |
| `JUDGEMENT-CALLS.md:1111` (§SJ2, withdrawn call) | "its share of Johannesburg's 2024 national ballot (6.22%; 5.4% after the model's national-to-local conversion…" | (c) | "its share of Johannesburg's 2024 provincial ballot (6.22%; 5.4% after the model's NPE-to-local conversion…" |
| `OWNER-DECISIONS-ANSWERED.md:1096, 1111` | "Its share of Johannesburg's 2024 national ballot, 6.22%"; "share of Johannesburg's 2024 national ballot 6.22%" | owner's record | dated note, §6 |
| `MODEL-LOG.md:1619-1620` | "against 6.22% nationally in 2024 … the forecast is built on the 6.22%" | append-only | a new dated entry stating the ballot, if the owner wants the log to carry it |
| `reports/model-changes/2026-10-21-actionsa/report.html:117`, `why.html:14` | "its share of Johannesburg's 2024 national ballot (6.22%, …" | dated report; no deploy reference found (`git grep model-changes -- src *.toml`: none) | historical; leave |
| `rounds/2026-10-23-out-of-sample/INVENTORY.md:141`, `PLAN.md:72`, `PLAN-REVIEW.md:140`, `DATA-PLAN-REVIEW.md:112` | already call it provincial or flag it | dated round files | leave |

| source file:line | current sentence | proposed | sense |
|---|---|---|---|
| `docs-public/corrections.md:239` | heading: *"Nationally in 2024" — published 26 September 2026, corrected 21 October 2026* | keep (a heading quotes the error) | — |
| `docs-public/corrections.md:241` | *"**What was wrong.** The methodology page said ActionSA polled {{hist_asa_npe_2024}} nationally in 2024. That is its share of Johannesburg's 2024 national ballot, not its national share."* | *"…That is its share of Johannesburg's 2024 provincial ballot, not its national share."* As a new correction (convention: heading = error, published date, corrected date). | W |
| `docs-public/corrections.md:243` | *"**What is right.** ActionSA polled {{hist_asa_npe_2024}} in the city in the 2024 national election."* | *"…in the city on the provincial ballot of the 2024 national and provincial elections."* | E |
| `src/tooltip_says.py:319-320` (tooltip on every 6.22%) | *"ActionSA's share of Johannesburg's national ballot in the 2024 national election."* | *"ActionSA's share of Johannesburg's provincial ballot in the 2024 national and provincial elections."* | W |
| `content/joburg/stats.toml:476` (`source`, published in `site/changes.json:3825`) | *"external:IEC NPE 2024, national ballot: ActionSA's share (MODEL-LOG, the local-premium entry quoting 18.12% against 6.22%)"* | *"external:IEC NPE 2024, provincial ballot: ActionSA's share of Johannesburg (`data/raw/elections/npe2024_JHB_vd_party.csv`)"*. The MODEL-LOG entry it cites (`MODEL-LOG.md:1619`) says "6.22% nationally" and is append-only; cite the file instead. | W |
| `docs-public/methodology.md:105-112` | *"Parties usually do worse locally than nationally. This Model measures the gap for each party from its own national-to-local transitions on record. A party's starting level blends its national result, converted down to local, with its last local result: the less record a party has of that gap, the more its local result counts. ActionSA polled {{hist_asa_pr_2021}} in this city's 2021 local election and {{hist_asa_npe_2024}} in the city in the 2024 national election. It has no national-to-local gap on record, so its starting level comes from its local result alone."* | *"Parties usually do worse in local elections than in national and provincial ones. This Model measures the gap for each party from its own provincial-to-local transitions on record, using the provincial ballot. A party's starting level blends its provincial-ballot result, converted down to local, with its last local result: … ActionSA polled {{hist_asa_pr_2021}} in this city's 2021 local election and {{hist_asa_npe_2024}} on the city's provincial ballot in 2024. It has no provincial-to-local gap on record, …"* | W, E |
| `docs-public/methodology.md:135-137` | *"A split that has stood in a national election since, as MK did in 2024, takes where its voters are from that result by ward, not from its parent."* | *"A split that has stood in a national and provincial election since, as MK did in 2024, takes where its voters are from its provincial-ballot result by ward, not from its parent."* | E, W |
| `docs-public/methodology.md:148` | *"Patricia de Lille was at least as well known nationally in 2019 as Julius Malema was in 2014"* | keep | C |
| `docs-public/methodology.md:215` | *"A party that had a vote in the 2024 national election cannot be moved by its by-elections further than This Model's usual range for it allows"* | *"A party that had a vote in the 2024 national and provincial elections cannot be moved…"* | E |
| `docs-public/methodology.md:217` | *"A party with no vote in the 2024 national election and none in the 2021 local election, on the list or in a ward, is not moved by its by-elections"* | *"A party with no vote in the 2024 national and provincial elections and none in the 2021 local election…"* | E |
| `docs-public/methodology.md:223` | *"…half by a projection from how far its turnout fell from the national to the local election in 2016 and 2021, with 2021 counting for 70%."* | *"…from the national and provincial to the local election in 2016 and 2021…"* | T |
| `docs-public/methodology.md:266, 286` | *"how a national poll and a metro poll combine"*; *"Before 2021 the only independent poll was national"* | keep | N |
| `docs-public/review.md:56` | *"The plan said MK — a party with no local-government machinery — should be expected to underperform its national result."* | reports what the plan said; keep, or *"…its 2024 result"*. Owner's choice. | W (quoted) |
| `docs-public/sources.md:21, 29` | *"This Model reads … the national and provincial elections from 1999 to 2024 at voting-district level"*; table row *"1999 to 2024 national/provincial elections \| The provincial ballot, This Model's between-elections baseline"* | keep: already right | C |
| `docs-public/corrections.md:143-145` | *"take the national swing since the last election…"*; *"It adds each party's change between the city's two national elections before the one forecast to the previous local result."* | heading quotes the error, keep; body: *"…between the city's two national and provincial elections…"* (the change is on the provincial ballot) | C, E |
| `docs-public/corrections.md:291` | *"The ANC bloc lost 587,000 votes between the 2019 national election and the 2021 local election, as the article says."* | *"…between the 2019 national and provincial elections and the 2021 local election…"*. The 587,000 is `bloc_leak_votes`, source *"MODEL-LOG 1.18 — ANC-bloc vote loss 2019 NPE to 2021 LGE"* (`stats.toml:324`); which ballot MODEL-LOG 1.18 summed was not checked. | E |
| `content/joburg/articles.toml:46-48` (standfirst of a dated article) | *"The opposition captured essentially none of the {{bloc_leak_votes}} votes the ANC bloc shed between the 2019 national election and the 2021 local election."* | Written pieces are frozen; a dated "Since then" note only if the owner wants one. Same text in `src/tooltip_says.py:313-316` (*"…from the 2019 national election to the 2021 local election."*), which is live and may change: *"…from the 2019 national and provincial elections to the 2021 local election."* | E |
| `content/joburg/model-claims.toml:71` | *"Each party's support moves by its own national-to-local gap, measured from its transitions on record."* | *"…its own provincial-to-local gap…"* (id stays) | W |
| `content/joburg/model-claims.toml:101` | *"A split that has stood in a national election since, as MK did in 2024, takes where its voters are from that result by ward, not from its parent."* | as `methodology.md:135` | E, W |
| `content/joburg/model-claims.toml:188` | *"Each voting district's turnout is projected from the fall between the national and the following local election in 2016 and 2021, weighted towards 2021."* | *"…between the national and provincial election and the following local election…"* | T |
| `content/joburg/model-claims.toml:206` | *"A party's starting level blends its national result, converted down to local, with its last local result: the less record a party has of that gap, the more its local result counts."* | *"…blends its provincial-ballot result…"* | W |
| `content/joburg/model-claims.toml:210` (`note`) | *"…it said every level comes from the national election…"* | internal note; *"…from the NPE…"* | E |
| `content/joburg/model-claims.toml:217` | *"…(2011, 2016, 2021 municipal; 2014, 2019, 2024 national/provincial)."* | keep | C |
| `interactive/your-forecast.html:392-393` | *"A party that has not stood in a local election starts from its last national result."* | *"…starts from its last provincial-ballot result."* | W |
| `interactive/js/make.js:805` | *"no party new to local elections moved that far from its last national result."* | *"…from its last provincial-ballot result."* (the `national:` key stays, §4) | W |
| `interactive/your-forecast.html:167` | *"smaller for a city subsample of a national survey"* | keep | N |
| `content/joburg/poll-caveats.toml:17, 19`; `content/joburg/stats.toml:1039-1176` (poll comments and `source`) | national omnibus / national survey / Ipsos national poll | keep | N |
| `src/interactive_template.html:211-212, 234-241, 273, 340` | *"MK's national surge…"*; *"MK's 2024 national vote carries fully into the local ballot"*; *"each party's result in the 2024 national election"*; *"twenty years of national-to-local swings"*; *"three-quarters of its 2024 national share"*; *"below national election"*; *"its national base"* | Not found in any tracked `site/` file (`git grep "MK collapses" -- site interactive`: none). If it is rebuilt: "2024 provincial-ballot vote/share/result", "provincial-to-local swings". | W, E |

## 8. Where "national" is correct — do not change

- **Polls (N):** `src/polling.py` throughout (`NATIONAL_VOTES` `:482`, `national_polls` `:783`, `SCOPES` `:578`, `metro_estimate` `:1043-1061`); `src/contested_area.py` (except `:21` and `:104`, which name the NPE that defines an arrival: "the preceding NPE"); `tests/test_polling*.py`; `POLLING.md`; poll text on the site.
- **Country-wide (C):** "national swing" (`README.md:15`, `ITERATING.md:180, 1225`, `src/theta_residual.py:448, 766, 1015`, `src/compare_history.py:2653`); "nationally-organised" (`src/levels.py:61`); "a national fact" (`src/cityconfig.py:70`); "national CSV/zip/bulk export" (one file for the country: `src/archive.py`, `SOURCES.md`, `src/ingest_npe.py:181`); `BigMapsNational`; "national LGE turnout" (`DATA-QUALITY.md:514`); "the national and provincial halves" (`DATA-QUALITY.md:89`, `docs-public/sources.md:14`); the census ward product being national (`SOURCES.md:567`).
- **Already right:** `src/bye_value.py:104, 375`; `docs-public/sources.md:29`; `SOURCES.md:61` ("National & provincial elections (VD-level, provincial ballot)"); `src/gamma_recent.py` (says NPE throughout, no "national").
- **Party names:** African National Congress, National Freedom Party, National Coloured Congress and the rest are filtered out of every count here.

## 9. Method and counts

Script (scratchpad, not committed): `git grep -n -I -i national` over `src`,
`tests`, top-level `*.md`, `skills`, `cities`, `config`, `judgements`,
`docs`, `notebooks`, `docs-public`, `content`, `interactive`, `site`,
excluding `audits rounds prereg archive reports data publications backups
drafts marketing interactive/tests site/stamps src/stamps`, `MODEL-LOG.md`,
`HANDOVER-ARCHIVE.md`, `OWNER-DECISIONS-ANSWERED.md`, and lines matching a
party name. 1,322 lines. Each line is tagged by regular expression (sense
W/E/T/C/N, or blank where no rule fired) and given a proposal by applying
V1-V6 as text substitutions. **The tags and proposals in the appendices are
machine-made**; a proposal marked ⟨check sense⟩ is a fallback ("national" →
"NPE") that a person must read before applying. §3-§7 were checked by hand.

| class | lines (excluding C and N) | where |
|---|---|---|
| (a) identifiers | 15 identifier groups (§4); 144 code statements in Appendix B that only reference them | §4 |
| (b) comments, docstrings, string literals in `src/`, `tests/` | 592 lines (src 335, tests 257), of which 144 are the code statements counted under (a) | §5, Appendix B |
| (c) project documents | 179 hand-edited lines in 18 files; 24 lines in generated documents | §6, Appendix C |
| (d) reader-facing sources | 28 lines in `docs-public/`, `content/`, `interactive/` (46 with C and N), plus `src/tooltip_says.py:313-320` and `src/interactive_template.html` (counted under (b) by the script) | §7 |
| do not change (C, N) outside reader text | 228 lines | Appendix D |

Built and shipped copies (`site/**`, `site/your-forecast/py/*.py`, which are
copies of `src/` modules made by `src/build_your_forecast.py`) account for the
rest of the 1,322 and change only when their sources do.

Not done: the 2009/2014 national–provincial gap bound (a separate read-only
item in `DATA-PLAN-REVIEW.md` §3); which ballot MODEL-LOG 1.18's 587,000 used.
The 2014 Johannesburg figures in §1 are one city-year of that gap and are
quoted only as evidence of which ballot the file holds.

## Appendices (machine-made; see §9)

### Appendix B. src/ and tests/ — comments, docstrings, string literals (592 lines)

| file:line | sense | current words | proposed words |
|---|---|---|---|
| src/arrivals.py:10 | E | share at all** of the national election the model builds its baseline from. That | share at all** of the NPE the model builds its baseline from. That |
| src/backtest.py:324 | W | # obligation to say so. 'levels.spine' weighs a party's national route | # obligation to say so. 'levels.spine' weighs a party's NPE route |
| src/backtest.py:333 |  | "the national-and-local level blend (task #22). Both records are " | "the NPE-and-local level blend (task #22). Both records are " ⟨check sense⟩ |
| src/backtest.py:341 | W | # their share of the national vote — are nomination and roll facts published | # their share of the provincial-ballot vote — are nomination and roll facts published |
| src/backtest.py:354 | W | "of the national vote in the municipalities it contests (task #23). " | "of the provincial-ballot vote in the municipalities it contests (task #23). " |
| src/backtest.py:355 | E | "Only for parties with NO record at the preceding national election; " | "Only for parties with NO record at the preceding NPE; " |
| src/backtest.py:1124 | E | The preceding national election's citywide shares, filtered to shares above | The preceding NPE's citywide shares, filtered to shares above |
| src/backtest.py:1127 | W | ["ARRIVED_VS_NATIONAL"]' — *"local share > 0 and preceding-NPE share <= 0, | statement: identifier kept (§4); no text change |
| src/backtest.py:1138 | W | handed a vector to was not an arrival even with no national record at | handed a vector to was not an arrival even with no NPE record at |
| src/backtest.py:1232 | W | # ('pools.ARRIVAL_DEFINITIONS["ARRIVED_VS_NATIONAL"]') says 'party != IND'. | # ('pools.ARRIVAL_DEFINITIONS["ARRIVED_VS_NATIONAL"]') says 'party != IND'. ⟨check sense⟩ |
| src/benchmarks.py:23 | E | national elections that bracket it -- see :func:'uniform_swing' for why that | NPEs that bracket it -- see :func:'uniform_swing' for why that |
| src/benchmarks.py:94 | E | ''prior_npe'' is the national election preceding ''prior_lge''; together | ''prior_npe'' is the NPE preceding ''prior_lge''; together |
| src/benchmarks.py:257 | W | # Party universe: everyone with a previous local result or a national one. | # Party universe: everyone with a previous local result or an NPE one. |
| src/benchmarks.py:442 | E | Uses: the previous LGE's VD-level ballots; the two national elections | Uses: the previous LGE's VD-level ballots; the two NPEs |
| src/benchmarks.py:447 | W | swing is applied so that the aggregate matches a *known* national result, or | swing is applied so that the aggregate matches a *known* provincial-ballot result, or |
| src/benchmarks.py:452 | E | national elections that bracket the local one being carried forward: | NPEs that bracket the local one being carried forward: |
| src/benchmarks.py:456 |  | That is a real assumption with a real failure mode -- it assumes national | That is a real assumption with a real failure mode -- it assumes NPE ⟨check sense⟩ |
| src/benchmarks.py:463 | W | that gained 5 points nationally gains 5 points in every VD, including ones | that gained 5 points on the provincial ballot gains 5 points in every VD, including ones ⟨check sense⟩ |
| src/benchmarks.py:503 |  | for the fact that national movement does not transfer one-for-one to local | for the fact that NPE movement does not transfer one-for-one to local ⟨check sense⟩ |
| src/benchmarks.py:555 | W | national result, so ''ctx.universe'' has no column for them at all. | provincial-ballot result, so ''ctx.universe'' has no column for them at all. |
| src/benchmarks.py:606 | E | union of the prior LGE's two ballots and two national elections, so a party | union of the prior LGE's two ballots and two NPEs, so a party |
| src/benchmarks.py:699 |  | f"result and a preceding national one, so 'arrival_group_record' " | f"result and a preceding NPE one, so 'arrival_group_record' " ⟨check sense⟩ |
| src/benchmarks.py:790 |  | swing could not represent it AT ALL: no prior local vote, no prior national | swing could not represent it AT ALL: no prior local vote, no prior NPE ⟨check sense⟩ |
| src/build_make.py:129 | E | #   there at the preceding local election (or national election, for a party | #   there at the preceding local election (or NPE, for a party |
| src/build_make.py:170 | W | #: national result in a metro's own VDs and is never a national prior. | #: provincial-ballot result in a metro's own VDs and is never a national prior. |
| src/build_make.py:359 | W | """A national result file by VD: ''{"vds": {vd: {"votes": Counter(code)}}, | """A provincial-ballot result file by VD: ''{"vds": {vd: {"votes": Counter(code)}}, |
| src/build_make.py:399 | W | file, the one ballot of a national file).""" | file, the one ballot of an NPE file).""" |
| src/build_make.py:479 | E | * ''npe_pairs'': every (metro, n, l), n the national election before the | * ''npe_pairs'': every (metro, n, l), n the NPE before the |
| src/build_make.py:496 | E | national election before b. | NPE before b. |
| src/build_make.py:563 | W | # parties new to the city with no national vote before b | # parties new to the city with no provincial-ballot vote before b |
| src/build_make.py:565 |  | national = _city_shares(_npe(npe[(code, n)])["vds"]) if (code, n) in npe else {} | statement: identifier kept (§4); no text change |
| src/build_make.py:566 |  | fresh = {p for p in Hb if p != "IND" and Ha.get(p, 0) == 0 and national.get(p, 0) == 0} | statement: identifier kept (§4); no text change |
| src/build_make.py:771 | E | """The same from the national election before the target | """The same from the NPE before the target |
| src/build_make.py:783 | W | raise MakeBuildError(f"build_make: no national result file for {city.code} {n}, the " | raise MakeBuildError(f"build_make: no provincial-ballot result file for {city.code} {n}, the " |
| src/build_make.py:800 |  | def party_kind(code: str, local_city: dict, national_city: dict) -> str: | statement: identifier kept (§4); no text change |
| src/build_make.py:804 |  | citywide shares there), else ''national'' if it had a vote at the | citywide shares there), else ''NPE'' if it had a vote at the ⟨check sense⟩ |
| src/build_make.py:805 | E | preceding national election, else ''newcomer''.""" | preceding NPE, else ''newcomer''.""" |
| src/build_make.py:808 |  | if national_city.get(code, 0) > 0: | statement: identifier kept (§4); no text change |
| src/build_make.py:809 |  | return "national" | statement: identifier kept (§4); no text change |
| src/build_make.py:813 |  | def ward_ranges(roster: list[str], wards: list[str], local: dict, national: dict, | statement: identifier kept (§4); no text change |
| src/build_make.py:822 |  | preceding local election), its share there at the preceding national | preceding local election), its share there at the preceding NPE ⟨check sense⟩ |
| src/build_make.py:823 | W | election, moved by the national-to-local extremes of its bin. | election, moved by the NPE-to-local extremes of its bin. |
| src/build_make.py:826 | W | local election as the prior), ''national'' (its citywide national share, | local election as the prior), ''national'' (its citywide provincial-ballot share, |
| src/build_make.py:828 | W | ward share any party new to its city with no national vote has taken]). | ward share any party new to its city with no provincial-ballot vote has taken]). |
| src/build_make.py:834 |  | kind = party_kind(p, local["city"], national["city"]) | statement: identifier kept (§4); no text change |
| src/build_make.py:839 |  | party[p] = {"kind": "national", "prior": national["city"][p], | statement: identifier kept (§4); no text change |
| src/build_make.py:840 |  | **dict(zip(("lo", "hi"), _moved(national["city"][p], bins["npe_ward"], A)))} | **dict(zip(("lo", "hi"), _moved(NPE["city"][p], bins["npe_ward"], A)))} ⟨check sense⟩ |
| src/build_make.py:851 |  | elif party[p]["kind"] == "national" and national["h"].get(w, {}).get(p, 0.0) > 0: | statement: identifier kept (§4); no text change |
| src/build_make.py:852 |  | row[p] = _moved(national["h"][w][p], bins["npe_ward"], A) | statement: identifier kept (§4); no text change |
| src/build_make.py:858 |  | def city_limits(roster: list[str], prior_e: dict, national: dict, local_city: dict, | statement: identifier kept (§4); no text change |
| src/build_make.py:865 |  | moved by the citywide swing extremes of its bin; a ''national'' party, | moved by the citywide swing extremes of its bin; a ''NPE'' party, ⟨check sense⟩ |
| src/build_make.py:866 | W | its citywide national share moved by the national-to-local citywide | its citywide provincial-ballot share moved by the NPE-to-local citywide |
| src/build_make.py:868 | W | its city with no national vote has taken]. Widened by the city allowance | its city with no provincial-ballot vote has taken]. Widened by the city allowance |
| src/build_make.py:873 |  | kind = party_kind(p, local_city, national["city"]) | statement: identifier kept (§4); no text change |
| src/build_make.py:879 |  | out[p] = {"kind": "national", "prior": national["city"][p], | statement: identifier kept (§4); no text change |
| src/build_make.py:880 |  | **dict(zip(("lo", "hi"), _moved(national["city"][p], bins["npe_city"], A)))} | **dict(zip(("lo", "hi"), _moved(NPE["city"][p], bins["npe_city"], A)))} ⟨check sense⟩ |
| src/build_make.py:890 | W | real swing, none excluded), ''npe_ward'' and ''npe_city'' from national to | real swing, none excluded), ''npe_ward'' and ''npe_city'' from NPE to ⟨check sense⟩ |
| src/build_make.py:892 | E | collapsed from the national election to the local one: a citywide | collapsed from the NPE to the local one: a citywide |
| src/build_make.py:893 | W | national share of at least :data:'COLLAPSE_FROM' and a local ward share | provincial-ballot share of at least :data:'COLLAPSE_FROM' and a local ward share |
| src/build_make.py:954 |  | national = npe_priors(city, target, elections=elections) | statement: identifier kept (§4); no text change |
| src/build_make.py:955 |  | cells, party = ward_ranges(roster, wards, local, national, bins, allow, panel["newcomer"]) | cells, party = ward_ranges(roster, wards, local, NPE, bins, allow, panel["newcomer"]) ⟨check sense⟩ |
| src/build_make.py:960 |  | limits = city_limits(roster, prior_e, national, local["city"], bins, allow, panel["newcomer"]) | limits = city_limits(roster, prior_e, NPE, local["city"], bins, allow, panel["newcomer"]) ⟨check sense⟩ |
| src/build_make.py:964 |  | sources[national["file"]] = national["sha256"] | statement: identifier kept (§4); no text change |
| src/build_validation.py:289 | E | "the national election before it for each party's starting level, and " | "the NPE before it for each party's starting level, and " |
| src/build_validation.py:308 | E | add("\| **uniform swing** \| take the previous local election and add each party's change between the city's two national elections before the one fo… | add("\| **uniform swing** \| take the previous local election and add each party's change between the city's two NPEs before the one forecast, equall… |
| src/bye_value.py:25 | W | by-elections: the 2021 LGE list share converted to the national ballot by | by-elections: the 2021 LGE list share converted to the provincial ballot by |
| src/bye_value.py:26 | W | the model's own national-local relation at the party's size, | the model's own NPE-local relation at the party's size, |
| src/bye_value.py:29 | W | items 11, 16 and 17 applied), at each party's 2019 national share in the | items 11, 16 and 17 applied), at each party's 2019 provincial-ballot share in the |
| src/bye_value.py:92 | E | #: the national election before the outcome (the size ''mu_θ'' is taken at). | #: the NPE before the outcome (the size ''mu_θ'' is taken at). |
| src/bye_value.py:124 | E | 2019 national files, and nothing dated 2024 or later. | 2019 NPE files, and nothing dated 2024 or later. |
| src/bye_value.py:133 |  | national = levels._citywide(_election(slug, BASE_NPE)) | statement: identifier kept (§4); no text change |
| src/bye_value.py:134 |  | mus, common, _worth = levels._shrunk(record, current=national, h=h) | mus, common, _worth = levels._shrunk(record, current=NPE, h=h) ⟨check sense⟩ |
| src/byelections.py:125 | E | against) and 2019 national file (the size ''mu_θ'' is taken at), and the | against) and 2019 NPE file (the size ''mu_θ'' is taken at), and the |
| src/cityconfig.py:5 | W | *judgements* (θ ranges, national-to-local shift ranges) | *judgements* (θ ranges, NPE-to-local shift ranges) |
| src/cityconfig.py:148 | E | """Ward-ID prefix used to pick this city out of national files.""" | """Ward-ID prefix used to pick this city out of NPE files.""" |
| src/cityconfig.py:204 | W | national share — and arrivals are routed to the arrival record | provincial-ballot share — and arrivals are routed to the arrival record |
| src/cityconfig.py:324 | E | """The last national election before this one — the freshest party | """The last NPE before this one — the freshest party |
| src/compare_history.py:35 |  | uniform-swing         that, shifted by the national movement bracketing it | uniform-swing         that, shifted by the NPE movement bracketing it ⟨check sense⟩ |
| src/compare_history.py:2234 | W | # ["ARRIVED_VS_NATIONAL"]' and is what 'diagnose', 'backtest.main', the relabel | # ["ARRIVED_VS_NATIONAL"]' and is what 'diagnose', 'backtest.main', the relabel ⟨check sense⟩ |
| src/compare_history.py:2257 | W | national share to grow from — not the target, which is what makes a | provincial-ballot share to grow from — not the target, which is what makes a |
| src/compare_history.py:2267 | W | registered ''ARRIVED_VS_NATIONAL'' predicate — as ''diagnose'' and | statement: identifier kept (§4); no text change |
| src/derive_city.py:11 | W | * **Judgements** — θ ranges, national-to-local shift | * **Judgements** — θ ranges, NPE-to-local shift |
| src/derive_city.py:128 | W | print("  θ ranges and the national-to-local shift ranges") | print("  θ ranges and the NPE-to-local shift ranges") |
| src/diagnose.py:332 | E | # national election -- not against its index. A party can be in the index | # NPE -- not against its index. A party can be in the index |
| src/group_share_record.py:15 | E | every national election after one, on that local election's wards and | every NPE after one, on that local election's wards and |
| src/group_share_record.py:16 | E | voter composition (carried forward: the national election's own | voter composition (carried forward: the NPE's own |
| src/group_share_record.py:24 |  | * ''sources'' — which elections entered the record, and for each national one | * ''sources'' — which elections entered the record, and for each NPE one ⟨check sense⟩ |
| src/group_share_record.py:33 | E | national election, and this reads every national election that follows a | NPE, and this reads every NPE that follows a |
| src/group_share_record.py:127 | E | the rows and the share of the national election's votes that reached a | the rows and the share of the NPE's votes that reached a |
| src/group_share_record.py:172 | E | """National elections after ''lge'' and before the next local election.""" | """NPEs after ''lge'' and before the next local election.""" |
| src/group_share_record.py:183 | W | """Every city's fitted local elections and the national ones after them. | """Every city's fitted local elections and the NPE ones after them. ⟨check sense⟩ |
| src/iec_csv.py:30 | E | national file. Was hard-coded to JHB; that made every ingest silently | NPE file. Was hard-coded to JHB; that made every ingest silently |
| src/ingest_npe.py:123 |  | ''event'' filters the 2014 bulk file to one ballot (''NATIONAL'' or | ''event'' filters the 2014 bulk file to one ballot (''NATIONAL'' or ⟨check sense⟩ |
| src/inputs_preflight.py:13 | E | the last national election recorded, and it keeps working perfectly while the | the last NPE recorded, and it keeps working perfectly while the |
| src/inputs_preflight.py:271 | W | for pattern, what in ((f"npe*_{code}_vd_party.csv", "national baseline"), | for pattern, what in ((f"npe*_{code}_vd_party.csv", "NPE baseline"), |
| src/inputs_preflight.py:284 |  | "used": baseline_used(city, target, "NPE" if what.startswith("national") else "LGE", with_roll), | statement: identifier kept (§4); no text change |
| src/interactive_template.html:211 |  | <button data-preset="mkfall" title="MK's national surge fails to translate locally — its slider to the historical floor.">MK collapses</button> | <button data-preset="mkfall" title="MK's NPE surge fails to translate locally — its slider to the historical floor.">MK collapses</button> ⟨check sense⟩ |
| src/interactive_template.html:212 | W | <button data-preset="mkhold" title="MK's 2024 national vote carries fully into the local ballot — its slider at the top of the observed range.">MK ho… | <button data-preset="mkhold" title="MK's 2024 provincial-ballot vote carries fully into the local ballot — its slider at the top of the observed rang… |
| src/interactive_template.html:234 |  | <div class="why">How close the vote is to each party's result in the <b>2024 national | <div class="why">How close the vote is to each party's result in the <b>2024 NPE ⟨check sense⟩ |
| src/interactive_template.html:236 | W | years of national-to-local swings.<br><b>●</b> = ANC bloc, <b>○</b> = DA bloc. | years of NPE-to-local swings.<br><b>●</b> = ANC bloc, <b>○</b> = DA bloc. |
| src/interactive_template.html:241 | W | three-quarters of its 2024 national share at the local election; ×1.30 means it runs 30% | three-quarters of its 2024 provincial-ballot share at the local election; ×1.30 means it runs 30% |
| src/interactive_template.html:273 | T | applied to that bloc. Local election turnout always runs far below national election | applied to that bloc. Local election turnout always runs far below NPE |
| src/interactive_template.html:340 | W | bloc's local share never falls below its national base. It has no losses to move, so | bloc's local share never falls below its NPE base. It has no losses to move, so |
| src/interactive_template.html:780 | W | // SOURCE bloc's losses (local share below its national base) to the | // SOURCE bloc's losses (local share below its NPE base) to the |
| src/levels.py:22 | W | What this module measures is θ, the national-to-local retention ratio: a | What this module measures is θ, the NPE-to-local retention ratio: a |
| src/levels.py:23 | E | party's share at a local election over its share at the national election | party's share at a local election over its share at the NPE |
| src/levels.py:36 | W | national size before    n    median θ   geometric mean | NPE size before    n    median θ   geometric mean |
| src/levels.py:60 | W | θ alone is only half a forecast. It converts a party's last NATIONAL share into | statement: identifier kept (§4); no text change |
| src/levels.py:64 | W | against 6.22% nationally in 2024, and no θ of its own, so the forecast built it | against 6.22% on the 2024 provincial ballot, and no θ of its own, so the forecast built it |
| src/levels.py:73 |  | θ evidence (Σ reliability)    n    RMSE(log) national    local    best weight on local | θ evidence (Σ reliability)    n    RMSE(log) NPE    local    best weight on local ⟨check sense⟩ |
| src/levels.py:80 | W | national route (best w 0.00) and those without want the local one (best w 1.00); | NPE route (best w 0.00) and those without want the local one (best w 1.00); |
| src/levels.py:85 |  | whose θ is nothing but the group centre, almost all national for a party with a | whose θ is nothing but the group centre, almost all NPE for a party with a ⟨check sense⟩ |
| src/levels.py:93 | W | vote-weighted RMSE(log) 0.236 against the national spine's 0.275, a 14% gain. | vote-weighted RMSE(log) 0.236 against the NPE spine's 0.275, a 14% gain. |
| src/levels.py:95 | W | wins land where the national route fails worst (Buffalo City 0.320 → 0.111, | wins land where the NPE route fails worst (Buffalo City 0.320 → 0.111, |
| src/levels.py:106 | W | partial fix — a local→national pair inverted is nominally the same ratio, and it | partial fix — a local→NPE pair inverted is nominally the same ratio, and it |
| src/levels.py:111 |  | national one, so a party's secular trend enters with the opposite sign: the PA, | NPE one, so a party's secular trend enters with the opposite sign: the PA, ⟨check sense⟩ |
| src/levels.py:164 | W | # against its national one — while this layer is CONDITIONAL: the within-pool | # against its NPE one — while this layer is CONDITIONAL: the within-pool |
| src/levels.py:182 | W | # The national share at which one observed ratio is worth half of a large | # The provincial-ballot share at which one observed ratio is worth half of a large |
| src/levels.py:187 | W | # How much θ evidence a party needs before the national spine is trusted over | # How much θ evidence a party needs before the NPE spine is trusted over |
| src/levels.py:558 | W | # Formed Dec 2008; the April 2009 NPE reading of 7.4% nationally was a | # Formed Dec 2008; the April 2009 NPE reading of 7.4% on the provincial ballot was a ⟨check sense⟩ |
| src/levels.py:682 | W | """Every observed national-to-local retention ratio before the target. | """Every observed NPE-to-local retention ratio before the target. |
| src/levels.py:685 | W | ''share'' is the national share the ratio was measured off. | ''share'' is the provincial-ballot share the ratio was measured off. |
| src/levels.py:687 | W | **There is no minimum share.** Parties below 0.2% of the national vote used | **There is no minimum share.** Parties below 0.2% of the provincial-ballot vote used |
| src/levels.py:725 | E | # national election is on disk as 'npe1999_approx_JHB_vd_party.csv' — | # NPE is on disk as 'npe1999_approx_JHB_vd_party.csv' — |
| src/levels.py:1080 | W | # apply θ to (MK in 2026 — a national vote, no local election yet) IS this | # apply θ to (MK in 2026 — a provincial-ballot vote, no local election yet) IS this |
| src/levels.py:1084 | W | # θ converts a national share into a local one and there is no national | # θ converts a provincial-ballot share into a local one and there is no national |
| src/levels.py:1144 | W | # No national share to be sized off: the width is the fit | # No provincial-ballot share to be sized off: the width is the fit |
| src/levels.py:1247 | W | national size before    n    median θ   geometric mean | NPE size before    n    median θ   geometric mean |
| src/levels.py:1328 | W | to (its national share for θ, its previous local share for ρ), since | to (its provincial-ballot share for θ, its previous local share for ρ), since |
| src/levels.py:1367 |  | ''current'' is each party's size now on this record's route: the national | ''current'' is each party's size now on this record's route: the NPE ⟨check sense⟩ |
| src/levels.py:1372 |  | such a party, because the spine consults ''mu_t'' only where the national | such a party, because the spine consults ''mu_t'' only where the NPE ⟨check sense⟩ |
| src/levels.py:1654 | E | ''baseline'' is the preceding national election's citywide shares; | ''baseline'' is the preceding NPE's citywide shares; |
| src/levels.py:1664 | W | with a long retention history sits on the national spine; a party whose θ | with a long retention history sits on the NPE spine; a party whose θ |
| src/levels.py:1666 |  | * **National only.** A party facing its first local election — MK in 2026. | * **NPE only.** A party facing its first local election — MK in 2026. ⟨check sense⟩ |
| src/levels.py:1668 | W | group would be worse than using the national route the party does have. | group would be worse than using the NPE route the party does have. |
| src/levels.py:1670 | W | nationally, or was not yet national when it did. Weight 1 by necessity. | on the provincial ballot, or was not yet NPE when it did. Weight 1 by necessity. ⟨check sense⟩ |
| src/levels.py:1681 | W | own θ (ρ) observations count only where measured off a national (local) | own θ (ρ) observations count only where measured off an NPE (local) ⟨check sense⟩ |
| src/levels.py:1691 | W | that "changing the national route did not move the forecast" can be told | that "changing the NPE route did not move the forecast" can be told |
| src/levels.py:1692 | W | apart from "the national route was never worth anything here": at | apart from "the NPE route was never worth anything here": at |
| src/levels.py:1710 | W | # that route (BRIEF item 11): its national share for θ, its previous | # that route (BRIEF item 11): its provincial-ballot share for θ, its previous |
| src/levels.py:1721 | W | # disagree by \|log(local) − log(national)\|, and 'w' decides how much of | # disagree by \|log(local) − log(NPE)\|, and 'w' decides how much of ⟨check sense⟩ |
| src/levels.py:1722 |  | # that disagreement survives. 'moved_from_national' is the mass the local | # that disagreement survives. 'moved_from_national' is the mass the local ⟨check sense⟩ |
| src/levels.py:1723 | W | # route actually won; a change to the national route with | # route actually won; a change to the NPE route with |
| src/levels.py:1734 |  | routes = {"blend": 0, "national_only": 0, "local_only": 0, "dropped": 0} | statement: identifier kept (§4); no text change |
| src/levels.py:1749 |  | national = float(baseline.get(party, 0.0)) | statement: identifier kept (§4); no text change |
| src/levels.py:1752 |  | if national > 0 and party not in mu_t: | statement: identifier kept (§4); no text change |
| src/levels.py:1756 |  | nat_level = national * float(np.exp(mu_t.get(party, c_t))) if national > 0 else 0.0 | statement: identifier kept (§4); no text change |
| src/levels.py:1758 |  | if national > 0 and local > 0: | statement: identifier kept (§4); no text change |
| src/levels.py:1768 | W | # national spine". Taking 'w = 0.0' when 'worth + k <= 0' keeps that | # NPE spine". Taking 'w = 0.0' when 'worth + k <= 0' keeps that |
| src/levels.py:1771 |  | # pure-national for everyone EXCEPT the parties with no θ evidence, | # pure-NPE for everyone EXCEPT the parties with no θ evidence, ⟨check sense⟩ |
| src/levels.py:1785 | W | # national route was contributing when it was not. | # NPE route was contributing when it was not. |
| src/levels.py:1793 | W | route = "blend at full national (k=0)" | route = "blend at full NPE (k=0)" |
| src/levels.py:1799 |  | blend["moved_from_national"] += w * gap | statement: identifier kept (§4); no text change |
| src/levels.py:1804 |  | blend["at_full_national"] += 1 | statement: identifier kept (§4); no text change |
| src/levels.py:1807 |  | elif national > 0: | statement: identifier kept (§4); no text change |
| src/levels.py:1808 |  | w, level, route = 0.0, nat_level, "national only (first local election)" | w, level, route = 0.0, nat_level, "NPE only (first local election)" ⟨check sense⟩ |
| src/levels.py:1809 |  | routes["national_only"] += 1 | statement: identifier kept (§4); no text change |
| src/levels.py:1811 | W | w, level, route = 1.0, loc_level, "local only (no national record)" | w, level, route = 1.0, loc_level, "local only (no NPE record)" |
| src/levels.py:1850 |  | blend["moved_from_national"] / blend["disagreement"] | statement: identifier kept (§4); no text change |
| src/levels.py:2260 | W | national baseline, no arrival seed, and a positive list vote at the | NPE baseline, no arrival seed, and a positive list vote at the |
| src/levels.py:2262 | W | national baseline did not carry it, 'pools' did not seed it (it has a | NPE baseline did not carry it, 'pools' did not seed it (it has a |
| src/montecarlo.py:399 | W | # How much θ evidence a party needs before the national spine is trusted | # How much θ evidence a party needs before the NPE spine is trusted |
| src/montecarlo.py:442 | W | # national result here, "unanchored" when it has none), each fitted by | # provincial-ballot result here, "unanchored" when it has none), each fitted by |
| src/montecarlo.py:489 |  | """Put each party with no national geography where its pools live. | """Put each party with no NPE geography where its pools live. ⟨check sense⟩ |
| src/montecarlo.py:521 | W | column at ''SHARE_FLOOR'' exactly as before, so a party with a national | column at ''SHARE_FLOOR'' exactly as before, so a party with an NPE ⟨check sense⟩ |
| src/montecarlo.py:2707 | E | (the national election before the target; a seeded arrival's seed).""" | (the NPE before the target; a seeded arrival's seed).""" |
| src/montecarlo.py:2757 |  | 2026-10-19, JUDGEMENT-CALLS §A60): one that is pool-seeded (no national | 2026-10-19, JUDGEMENT-CALLS §A60): one that is pool-seeded (no NPE ⟨check sense⟩ |
| src/montecarlo.py:2773 | W | # WITHOUT HISTORY. A party with no national share has no θ, because θ is | # WITHOUT HISTORY. A party with no provincial-ballot share has no θ, because θ is |
| src/montecarlo.py:2774 | W | # the ratio of a local share to a national one and there is nothing to | # the ratio of a local share to an NPE one and there is nothing to |
| src/montecarlo.py:2782 | W | # NATIONAL-to-local conversion factor, applied to something already local, | # NATIONAL-to-local conversion factor, applied to something already local, ⟨check sense⟩ |
| src/montecarlo.py:2788 | W | # common centre, or the centre itself for a party holding a national vote | # common centre, or the centre itself for a party holding a provincial-ballot vote |
| src/montecarlo.py:2792 | W | # is the answer: it already weighed the party's national route against its | # is the answer: it already weighed the party's NPE route against its |
| src/montecarlo.py:2842 | W | # A party that reaches here has a national baseline, no spine | # A party that reaches here has an NPE baseline, no spine |
| src/montecarlo.py:2848 | W | f"{party} has a national baseline but no spine level, no theta " | f"{party} has an NPE baseline but no spine level, no theta " |
| src/montecarlo.py:2860 | W | # seed, which only a party with no national share gets), no | # seed, which only a party with no provincial-ballot share gets), no |
| src/montecarlo.py:2864 | W | # national share, so never seeded); keyed on the seed rather than | # provincial-ballot share, so never seeded); keyed on the seed rather than |
| src/montecarlo.py:2966 | W | # the national baseline. θ's band is a band on the NATIONAL | # the NPE baseline. θ's band is a band on the NATIONAL |
| src/montecarlo.py:2968 | W | # evidence to what a party's national share could become, which | # evidence to what a party's provincial-ballot share could become, which |
| src/montecarlo.py:2973 |  | # 18.7%; and the clamp, computed as high × 5.99% national, cut | # 18.7%; and the clamp, computed as high × 5.99% NPE, cut ⟨check sense⟩ |
| src/montecarlo.py:2976 | W | # national share were overruled by a bound derived from the | # provincial-ballot share were overruled by a bound derived from the |
| src/montecarlo.py:2977 | W | # national share. The PA was clamped from 21.9% to 7.1% the same | # provincial-ballot share. The PA was clamped from 21.9% to 7.1% the same |
| src/montecarlo.py:3079 | W | # city-years. It becomes reachable the moment a national | # city-years. It becomes reachable the moment an NPE ⟨check sense⟩ |
| src/montecarlo.py:3579 | W | (''scenario["_theta_sd"]''), the size line at its national share; | (''scenario["_theta_sd"]''), the size line at its provincial-ballot share; |
| src/montecarlo.py:3717 | E | * ''"anchored"'': the party took votes at the preceding national election | * ''"anchored"'': the party took votes at the preceding NPE |
| src/montecarlo.py:3718 |  | in this city. ''levels.spine'' then sizes it on its "national only (first | in this city. ''levels.spine'' then sizes it on its "NPE only (first ⟨check sense⟩ |
| src/montecarlo.py:3720 | W | as its centre: the centre is the party's own national result through θ. | as its centre: the centre is the party's own provincial-ballot result through θ. |
| src/montecarlo.py:3722 | W | * ''"unanchored"'': no national result here. Its centre is an arrival | * ''"unanchored"'': no provincial-ballot result here. Its centre is an arrival |
| src/montecarlo.py:3724 |  | after the seeds are added, labels it "national only" too, so the route | after the seeds are added, labels it "NPE only" too, so the route ⟨check sense⟩ |
| src/montecarlo.py:3727 | W | The test is ''scenario["_baseline_before_seeds"]'' (the national baseline | The test is ''scenario["_baseline_before_seeds"]'' (the NPE baseline |
| src/montecarlo.py:3729 | W | added), the same input that makes the spine's national route real rather | added), the same input that makes the spine's NPE route real rather |
| src/montecarlo.py:3739 | W | f"set, so whether the party's centre is its own national result " | f"set, so whether the party's centre is its own provincial-ballot result " |
| src/montecarlo.py:4346 | W | # with no national baseline, so where 'theta_prior' emits an sd for it, it | # with no NPE baseline, so where 'theta_prior' emits an sd for it, it |
| src/montecarlo.py:4394 |  | # because the ratio it implies against a 6.2% national base sits above | # because the ratio it implies against a 6.2% NPE base sits above ⟨check sense⟩ |
| src/montecarlo.py:5695 | W | the preceding national baseline, minus two floors*. ⚠️ **The floors' | the preceding NPE baseline, minus two floors*. ⚠️ **The floors' |
| src/montecarlo.py:5725 | W | f"party in the {target.previous_npe} national baseline, minus " | f"party in the {target.previous_npe} NPE baseline, minus " |
| src/montecarlo.py:5727 | W | f"§K1 (a national-share floor on candidates with no prior LOCAL " | f"§K1 (an NPE-share floor on candidates with no prior LOCAL " ⟨check sense⟩ |
| src/montecarlo.py:5729 | W | f"prior NATIONAL vote) — and minus IND/ENTRANT, which are slots " | statement: identifier kept (§4); no text change |
| src/montecarlo.py:5738 | W | f"LGE result and national baseline, less the JUDGEMENT-CALLS.md " | f"LGE result and NPE baseline, less the JUDGEMENT-CALLS.md " |
| src/montecarlo.py:5821 | W | * **with a record** -- a previous-LGE list vote, a national baseline or an | * **with a record** -- a previous-LGE list vote, an NPE baseline or an |
| src/montecarlo.py:5860 | W | f"Each has a previous-LGE list vote, a national baseline or a seed, " | f"Each has a previous-LGE list vote, an NPE baseline or a seed, " |
| src/montecarlo.py:6160 | E | # --- baseline: the last national election before the target -------------- | # --- baseline: the last NPE before the target -------------- |
| src/montecarlo.py:6169 | W | # The universe used to be built from the national baseline alone, so every | # The universe used to be built from the NPE baseline alone, so every |
| src/montecarlo.py:6170 | E | # party that contested the last NATIONAL election kept a share at the local | # party that contested the last NPE election kept a share at the local |
| src/montecarlo.py:6210 | W | # holds a national record. The drop below then removes the remainder. One | # holds an NPE record. The drop below then removes the remainder. One |
| src/montecarlo.py:6285 | W | # national vote and won 44 of Johannesburg's 270 seats in 2021; the model | # provincial-ballot vote and won 44 of Johannesburg's 270 seats in 2021; the model |
| src/montecarlo.py:6507 | W | # PR base. Same function and rule as the national baseline above: a | # PR base. Same function and rule as the NPE baseline above: a |
| src/montecarlo.py:6514 |  | # record" has to mean the party took votes at the preceding national | # record" has to mean the party took votes at the preceding NPE ⟨check sense⟩ |
| src/montecarlo.py:6523 | W | # 2026-10-09). The run's party list is the national baseline plus the | # 2026-10-09). The run's party list is the NPE baseline plus the |
| src/montecarlo.py:6525 | W | # ballot with a previous-LGE list vote and no national vote was in neither | # ballot with a previous-LGE list vote and no provincial-ballot vote was in neither |
| src/montecarlo.py:6554 |  | # Every party with no national geography: the seeded arrivals and | # Every party with no NPE geography: the seeded arrivals and ⟨check sense⟩ |
| src/montecarlo.py:7143 |  | # Item 8's local-record-only parties are kept out of the national | # Item 8's local-record-only parties are kept out of the NPE ⟨check sense⟩ |
| src/montecarlo.py:7208 | T | key=lambda p: -abs(d[p]["local"] - d[p]["national"])) | statement: identifier kept (§4); no text change |
| src/montecarlo.py:7216 |  | f"(θ worth {d[p]['worth']:.1f})  national " | f"(θ worth {d[p]['worth']:.1f})  NPE " ⟨check sense⟩ |
| src/montecarlo.py:7217 |  | f"{d[p]['national']:.2%} / local {d[p]['local']:.2%} " | f"{d[p]['NPE']:.2%} / local {d[p]['local']:.2%} " ⟨check sense⟩ |
| src/montecarlo.py:7221 | W | f"national route alone") | f"NPE route alone") |
| src/parties.py:105 |  | "NATIONAL COLOURED CONGRESS": "NCC", | statement: identifier kept (§4); no text change |
| src/pools.py:1038 | W | # The preceding-NATIONAL share below which a party with no preceding LOCAL | # The preceding-NATIONAL share below which a party with no preceding LOCAL ⟨check sense⟩ |
| src/pools.py:1042 |  | NATIONAL_ONLY_FLOOR = 0.001 | statement: identifier kept (§4); no text change |
| src/pools.py:1044 | W | # The preceding-LOCAL share below which a party with no preceding NATIONAL vote | # The preceding-LOCAL share below which a party with no preceding NATIONAL vote ⟨check sense⟩ |
| src/pools.py:1046 |  | # NATIONAL_ONLY_FLOOR, and a better bargain: it drops 59% of that class for | # NATIONAL_ONLY_FLOOR, and a better bargain: it drops 59% of that class for ⟨check sense⟩ |
| src/pools.py:1144 | W | so those files land with it blank. A national election has no ward | so those files land with it blank. An NPE has no ward |
| src/pools.py:1147 | W | series loses two of its five cycles, and a national election cannot be | series loses two of its five cycles, and an NPE cannot be |
| src/pools.py:1148 | W | fitted at all (:func:'national_fits'). | statement: identifier kept (§4); no text change |
| src/pools.py:1219 | E | # National elections have one ballot and no BallotType column; local | # NPEs have one ballot and no BallotType column; local |
| src/pools.py:1677 | E | national election used the 2016 wards, the 2024 national the 2021 wards. | NPE used the 2016 wards, the 2024 national the 2021 wards. |
| src/pools.py:1878 | W | whose size you do not know — and wrong here. A national election does not | whose size you do not know — and wrong here. An NPE does not |
| src/pools.py:1911 | W | # A national election has one ballot and no BallotType column, and the | # An NPE has one ballot and no BallotType column, and the |
| src/pools.py:1914 | W | # dropped every NPE row, so a national election could not be fitted. | # dropped every NPE row, so an NPE could not be fitted. |
| src/pools.py:2557 |  | Local elections run fifteen to twenty points below national ones, which is | Local elections run fifteen to twenty points below NPE ones, which is ⟨check sense⟩ |
| src/pools.py:2558 | W | why ''kind'' filters: a local forecast learns nothing useful from national | why ''kind'' filters: a local forecast learns nothing useful from NPE ⟨check sense⟩ |
| src/pools.py:3290 | E | # off two national elections) and not every split has a pair to measure. | # off two NPEs) and not every split has a pair to measure. |
| src/pools.py:3298 | W | ActionSA never contested a national election before its | ActionSA never contested an NPE before its |
| src/pools.py:3316 | W | leader's fame: Patricia de Lille was at least as well known nationally in | leader's fame: Patricia de Lille was at least as well known on the provincial ballot in ⟨check sense⟩ |
| src/pools.py:3444 | W | "montecarlo.run_model",          # national baseline, and prev_local | "montecarlo.run_model",          # NPE baseline, and prev_local |
| src/pools.py:3462 | W | ''shares''      one election's citywide shares (a national baseline, or | ''shares''      one election's citywide shares (an NPE baseline, or |
| src/pools.py:3477 | W | holds a share in ''shares''. RISE has a 2024 national record and no 2021 | holds a share in ''shares''. RISE has a 2024 NPE record and no 2021 |
| src/pools.py:3479 |  | national-only route to the blend and pull it DOWN toward GOOD's size. So RISE | NPE only route to the blend and pull it DOWN toward GOOD's size. So RISE ⟨check sense⟩ |
| src/pools.py:3480 | W | takes GOOD's transfer on the national route only. | takes GOOD's transfer on the NPE route only. |
| src/pools.py:3604 | W | # group budget itself, which was measured over ARRIVED_VS_NATIONAL and spent | # group budget itself, which was measured over ARRIVED_VS_NATIONAL and spent ⟨check sense⟩ |
| src/pools.py:3627 | W | predicate="ARRIVED_VS_NATIONAL and party not in SPLITS", | statement: identifier kept (§4); no text change |
| src/pools.py:3636 | W | population="consecutive LGE pairs; a party with a national record but " | population="consecutive LGE pairs; a party with an NPE record but " |
| src/pools.py:3870 |  | continue          # a split with no national pair to measure across | continue          # a split with no NPE pair to measure across ⟨check sense⟩ |
| src/pools.py:4092 | W | party at its first local election has no preceding national vote whether it | party at its first local election has no preceding provincial-ballot vote whether it |
| src/pools.py:4096 | W | contender normally has a national result first — the correction §1.201 had | contender normally has a provincial-ballot result first — the correction §1.201 had |
| src/pools.py:4103 | W | EFF held a 2014 national vote before its first local election, COPE a 2004, | EFF held a 2014 provincial-ballot vote before its first local election, COPE a 2004, |
| src/pools.py:4149 | W | # ARRIVAL DEFINITION: ARRIVED_VS_NATIONAL | # ARRIVAL DEFINITION: ARRIVED_VS_NATIONAL ⟨check sense⟩ |
| src/pools.py:4180 |  | # A party at its FIRST local election has no preceding national | # A party at its FIRST local election has no preceding NPE ⟨check sense⟩ |
| src/pools.py:4352 | W | baseline parties. ActionSA held no 2019 national vote at all, so it never | baseline parties. ActionSA held no 2019 provincial-ballot vote at all, so it never |
| src/pools.py:5028 | W | # ⚖️ The preceding-NATIONAL share above which a party with no declared lineage | # ⚖️ The preceding-NATIONAL share above which a party with no declared lineage ⟨check sense⟩ |
| src/pools.py:5419 | W | def national_fits(city: cityconfig.City, target: cityconfig.Target, cfg: Config, | statement: identifier kept (§4); no text change |
| src/pools.py:5422 | E | """Every party fitted on the target's baseline NATIONAL election, by ward. | statement: identifier kept (§4); no text change |
| src/pools.py:5426 | W | no vector of its own there however large its national record. This fits | no vector of its own there however large its NPE record. This fits |
| src/pools.py:5428 | W | national result file, every party jointly, the same registration-nested | provincial-ballot result file, every party jointly, the same registration-nested |
| src/pools.py:5431 | E | the election differs. The national file's voting districts are placed in | the election differs. The NPE file's voting districts are placed in |
| src/pools.py:5436 | E | backtest reads its own preceding national election exactly as the live | backtest reads its own preceding NPE exactly as the live |
| src/pools.py:5440 |  | Returns ''({}, reason)'' when there is nothing to fit — no national | Returns ''({}, reason)'' when there is nothing to fit — no NPE ⟨check sense⟩ |
| src/pools.py:5447 | E | return {}, f"no national election precedes {target.year}" | return {}, f"no NPE precedes {target.year}" |
| src/pools.py:5449 | E | return {}, f"the {npe} national election has no result file" | return {}, f"the {npe} NPE has no result file" |
| src/pools.py:5453 | W | return {}, f"the {npe} national result is unavailable ({exc.cause})" | return {}, f"the {npe} provincial-ballot result is unavailable ({exc.cause})" |
| src/pools.py:5457 | W | return {}, f"the {npe} national fit could not be built: {exc}" | return {}, f"the {npe} NPE fit could not be built: {exc}" |
| src/pools.py:5459 | W | return {}, (f"the {npe} national fit has pools {list(ctx['categories'])}, " | return {}, (f"the {npe} NPE fit has pools {list(ctx['categories'])}, " |
| src/pools.py:5461 | W | return fits, f"{city.slug} {npe} national results by ward" | return fits, f"{city.slug} {npe} provincial-ballot result by ward" |
| src/pools.py:5496 |  | nat_available: bool, national: float | statement: identifier kept (§4); no text change |
| src/pools.py:5501 |  | ''no_measured_vector'' entry; ''fitted'' the ''fitted_from_national'' | ''no_measured_vector'' entry; ''fitted'' the ''fitted_from_national'' ⟨check sense⟩ |
| src/pools.py:5502 | W | record when the party's own national fit was used; ''refused'' why a party | record when the party's own NPE fit was used; ''refused'' why a party |
| src/pools.py:5503 | W | holding a national record was NOT fitted, else ''None''. | holding an NPE record was NOT fitted, else ''None''. |
| src/pools.py:5507 | W | 1. its own NATIONAL fit (:func:'national_fits'), when it identifies a | statement: identifier kept (§4); no text change |
| src/pools.py:5522 | W | refused = f"its {npe} national fit identifies no pool" | refused = f"its {npe} NPE fit identifies no pool" |
| src/pools.py:5523 |  | elif own_fit is None and national > 0: | statement: identifier kept (§4); no text change |
| src/pools.py:5525 | W | else f"not in the {npe} national fit") | else f"not in the {npe} NPE fit") |
| src/pools.py:5538 | E | note = (f"fitted on the {npe} national election's ward results " | note = (f"fitted on the {npe} NPE's ward results " |
| src/pools.py:5721 |  | if p not in composition and v < NATIONAL_ONLY_FLOOR} | statement: identifier kept (§4); no text change |
| src/pools.py:5771 |  | # record in this city (the fitted composition or the national | # record in this city (the fitted composition or the NPE ⟨check sense⟩ |
| src/pools.py:5817 | E | # one the preceding national file used — canonicalisation does not | # one the preceding NPE file used — canonicalisation does not |
| src/pools.py:5826 | E | # 2024 national file did not use has no baseline, so it is seeded | # 2024 NPE file did not use has no baseline, so it is seeded |
| src/pools.py:5899 | W | # ⛔ NOT EVERY PARTY WITH A NATIONAL VOTE. Measured over 16 city-years | # ⛔ NOT EVERY PARTY WITH A NATIONAL VOTE. Measured over 16 city-years ⟨check sense⟩ |
| src/pools.py:5900 | W | # (§1.175): candidates carrying a preceding NATIONAL vote but no | # (§1.175): candidates carrying a preceding NATIONAL vote but no ⟨check sense⟩ |
| src/pools.py:5903 | W | # kinds of evidence carry 89.73%. Admitting the whole national ballot | # kinds of evidence carry 89.73%. Admitting the whole provincial ballot |
| src/pools.py:5908 |  | # SIZE, not on class. At a 0.1% national floor, 158 of those 226 | # SIZE, not on class. At a 0.1% NPE floor, 158 of those 226 ⟨check sense⟩ |
| src/pools.py:5910 |  | # ones transfer nearly one-for-one (national 11.51% -> local 11.64%, | # ones transfer nearly one-for-one (NPE 11.51% -> local 11.64%, ⟨check sense⟩ |
| src/pools.py:5918 |  | # nothing at the preceding national one stands again only 28% of the | # nothing at the preceding NPE one stands again only 28% of the ⟨check sense⟩ |
| src/pools.py:5921 |  | # vote and ZERO seats** — against the national floor's 70% for two | # vote and ZERO seats** — against the NPE floor's 70% for two ⟨check sense⟩ |
| src/pools.py:5943 |  | print(f"  ! {len(thin)} parties held a {target.previous_npe} national " | print(f"  ! {len(thin)} parties held a {target.previous_npe} NPE " ⟨check sense⟩ |
| src/pools.py:5944 |  | f"vote below {NATIONAL_ONLY_FLOOR:.1%} and no local record, so " | statement: identifier kept (§4); no text change |
| src/pools.py:6064 | E | # meant for minor parties. It is fitted on the baseline national election | # meant for minor parties. It is fitted on the baseline NPE |
| src/pools.py:6112 | E | # party that contested the last national election and is NOT on this | # party that contested the last NPE and is NOT on this |
| src/pools.py:6134 | W | # the preceding NATIONAL baseline — which is EXACTLY 0.000% for every | # the preceding NATIONAL baseline — which is EXACTLY 0.000% for every ⟨check sense⟩ |
| src/pools.py:6145 | W | f"{held:.2%} of the {target.previous_npe} national baseline and " | f"{held:.2%} of the {target.previous_npe} NPE baseline and " |
| src/pools.py:6181 | W | # ⛔ A PARTY WITH A NATIONAL RECORD AND NO LINEAGE IS THE ActionSA SHAPE, | # ⛔ A PARTY WITH A NATIONAL RECORD AND NO LINEAGE IS THE ActionSA SHAPE, ⟨check sense⟩ |
| src/pools.py:6190 |  | # The detector triggers on the party's share at the preceding NATIONAL | # The detector triggers on the party's share at the preceding NATIONAL ⟨check sense⟩ |
| src/pools.py:6198 | W | # ⛔ A PARTY WITH ITS OWN NATIONAL RECORD IS FITTED, NOT INHERITED (owner, | # ⛔ A PARTY WITH ITS OWN NATIONAL RECORD IS FITTED, NOT INHERITED (owner, ⟨check sense⟩ |
| src/pools.py:6200 |  | # standing in the baseline national one is fitted on THAT election's ward | # standing in the baseline NPE one is fitted on THAT election's ward ⟨check sense⟩ |
| src/pools.py:6201 | W | # results, the way every locally fitted party is ('national_fits'), and the | # results, the way every locally fitted party is ('national_fits'), and the ⟨check sense⟩ |
| src/pools.py:6206 | W | # identifies nothing. PRECEDENCE: local fit > national fit > 'weights' > | # identifies nothing. PRECEDENCE: local fit > NPE fit > 'weights' > |
| src/pools.py:6209 | W | national_fitted: dict[str, dict] = {} | statement: identifier kept (§4); no text change |
| src/pools.py:6210 |  | national_refused: dict[str, str] = {} | statement: identifier kept (§4); no text change |
| src/pools.py:6211 | W | nat_fits, nat_source = ({}, "") if not no_vector else national_fits( | statement: identifier kept (§4); no text change |
| src/pools.py:6227 |  | national = float(baseline.get(party, 0.0)) | statement: identifier kept (§4); no text change |
| src/pools.py:6229 |  | if not parent and national >= UNCLASSIFIED_FLOOR: | statement: identifier kept (§4); no text change |
| src/pools.py:6230 |  | unclassified[party] = national | unclassified[party] = NPE ⟨check sense⟩ |
| src/pools.py:6236 | W | nat_available=bool(nat_fits), national=national) | statement: identifier kept (§4); no text change |
| src/pools.py:6239 | W | national_fitted[party] = fitted | statement: identifier kept (§4); no text change |
| src/pools.py:6241 |  | national_refused[party] = refused | statement: identifier kept (§4); no text change |
| src/pools.py:6407 |  | + (f", and on the {target.previous_npe} national " | + (f", and on the {target.previous_npe} NPE " ⟨check sense⟩ |
| src/pools.py:6408 | W | f"election for {len(national_fitted)} " | statement: identifier kept (§4); no text change |
| src/pools.py:6409 | W | f"part{'y' if len(national_fitted) == 1 else 'ies'} " | statement: identifier kept (§4); no text change |
| src/pools.py:6411 | W | if national_fitted else "") | statement: identifier kept (§4); no text change |
| src/pools.py:6419 | W | # its NATIONAL fit is ('national_fitted'); one placed by a lineage | # its NPE fit is ('national_fitted'); one placed by a lineage |
| src/pools.py:6423 | W | or name in national_fitted.get( | statement: identifier kept (§4); no text change |
| src/pools.py:6511 | W | # on the baseline NATIONAL election ('national_fits'): which | # on the baseline NPE election ('national_fits'): which |
| src/pools.py:6514 | W | # national record whose fit was not used, with why — they took the | # NPE record whose fit was not used, with why — they took the |
| src/pools.py:6516 | W | "fitted_from_national": national_fitted, | statement: identifier kept (§4); no text change |
| src/pools.py:6517 | W | "national_fit_refused": national_refused, | statement: identifier kept (§4); no text change |
| src/pools.py:6530 | W | # nevertheless hold a preceding NATIONAL vote — candidates for a | # nevertheless hold a preceding NATIONAL vote — candidates for a ⟨check sense⟩ |
| src/pools.py:6537 | W | # LEVEL; its vector is its own national fit where that identifies a | # LEVEL; its vector is its own NPE fit where that identifies a |
| src/pools.py:6538 |  | # pool ('fitted_from_national'), else the city's own composition. | # pool ('fitted_from_national'), else the city's own composition. ⟨check sense⟩ |
| src/score_forecasts.py:138 |  | reads the one-ballot national layout (no ''BallotType'', no ward) for the | reads the one-ballot NPE layout (no ''BallotType'', no ward) for the ⟨check sense⟩ |
| src/score_forecasts.py:139 | W | editor's national prior (''build_make.npe_priors''). | editor's NPE prior (''build_make.npe_priors''). ⟨check sense⟩ |
| src/score_forecasts.py:298 | W | """''{vd: {IEC name: votes}}'' from a national (NPE) VD-level file: one | """''{vd: {IEC name: votes}}'' from an NPE VD-level file: one ⟨check sense⟩ |
| src/score_forecasts.py:307 | E | f"one-ballot national file") | f"one-ballot NPE file") |
| src/score_forecasts.py:310 |  | raise ValueError(f"{path}: not an IEC national VD result file; " | raise ValueError(f"{path}: not an IEC NPE VD result file; " ⟨check sense⟩ |
| src/seats.py:69 | W | independent is never an arrival, ''ARRIVED_VS_NATIONAL'''s ''party != IND''). | statement: identifier kept (§4); no text change |
| src/theta_residual.py:25 | E | national election's citywide shares, which is exactly what 'montecarlo' passes | NPE's citywide shares, which is exactly what 'montecarlo' passes |
| src/theta_residual.py:51 | W | national size      n   cy   measured   95% CI (cluster)   sd_for   ratio | NPE size      n   cy   measured   95% CI (cluster)   sd_for   ratio |
| src/theta_residual.py:110 | W | # Size bins, in national vote share. Chosen to match the bands 'size_centre''s | # Size bins, in provincial-ballot share. Chosen to match the bands 'size_centre''s |
| src/theta_residual.py:140 | W | See the module docstring. ''size'' is the national share the ratio was | See the module docstring. ''size'' is the provincial-ballot share the ratio was |
| src/theta_residual.py:448 |  | ratio in Johannesburg and its 2016 ratio in Tshwane share the 2016 national | ratio in Johannesburg and its 2016 ratio in Tshwane share the 2016 NPE ⟨check sense⟩ |
| src/theta_residual.py:1134 | W | f"{'national size':>16} {'n':>4} {'cy':>4} {'measured':>9} " | f"{'NPE size':>16} {'n':>4} {'cy':>4} {'measured':>9} " |
| src/tooltip_says.py:314 | E | "The votes the ANC's bloc of parties lost in Johannesburg from the 2019 national election to the 2021 local election."), | "The votes the ANC's bloc of parties lost in Johannesburg from the 2019 NPE to the 2021 local election."), |
| src/tooltip_says.py:316 | E | "The votes the DA's bloc of parties lost in Johannesburg from the 2019 national election to the 2021 local election."), | "The votes the DA's bloc of parties lost in Johannesburg from the 2019 NPE to the 2021 local election."), |
| src/tooltip_says.py:320 | W | "ActionSA's share of Johannesburg's national ballot in the 2024 national election."), | "ActionSA's share of Johannesburg's provincial ballot in the 2024 NPE."), |
| src/turnout.py:6 | E | and N(x) for the national election preceding x: | and N(x) for the NPE preceding x: |
| src/turnout.py:74 | T | # The λ pairs: each LGE against the national election that preceded it, keyed | # The λ pairs: each LGE against the NPE that preceded it, keyed |
| src/turnout.py:255 | E | f"no national election on disk before {target.year} for " | f"no NPE on disk before {target.year} for " |
| src/width_record.py:37 |  | ''montecarlo.newness_class'' ("anchored": centre from the party's own national | ''montecarlo.newness_class'' ("anchored": centre from the party's own NPE ⟨check sense⟩ |
| tests/test_blended_centres.py:20 |  | 3. ''spine_level''      ''levels.spine'' — national and local, weighted | 3. ''spine_level''      ''levels.spine'' — NPE and local, weighted ⟨check sense⟩ |
| tests/test_blended_centres.py:100 | W | BASE = 0.10          # the party's national baseline share | BASE = 0.10          # the party's NPE baseline share |
| tests/test_blended_centres.py:165 |  | Both routes are live for exactly one class of party — one with no national | Both routes are live for exactly one class of party — one with no NPE ⟨check sense⟩ |
| tests/test_blended_centres.py:202 | W | θ is a NATIONAL-to-local conversion factor. Applying it in preference to a | statement: identifier kept (§4); no text change |
| tests/test_blended_centres.py:216 | W | The spine weighs a party's national route against its own last local | The spine weighs a party's NPE route against its own last local |
| tests/test_blended_centres.py:234 | W | estimate multiplied by a NATIONAL-to-local factor chosen with knowledge of | statement: identifier kept (§4); no text change |
| tests/test_blended_centres.py:248 | W | answer: it already weighed the party's national route against its own last | answer: it already weighed the party's NPE route against its own last |
| tests/test_blended_centres.py:303 | W | "a party with a national baseline, no spine level, no theta prior " | "a party with an NPE baseline, no spine level, no theta prior " |
| tests/test_blended_centres.py:348 | W | parties with NO national baseline (''montecarlo.py:2830'': skip if | parties with NO NPE baseline (''montecarlo.py:2830'': skip if |
| tests/test_blended_centres.py:583 |  | 18.7%, and a clamp computed as ''high × 5.99% national'' cut that to 7.5% | 18.7%, and a clamp computed as ''high × 5.99% NPE'' cut that to 7.5% ⟨check sense⟩ |
| tests/test_blended_centres.py:585 | W | agreeing the party is larger than its national share were overruled by a | agreeing the party is larger than its provincial-ballot share were overruled by a |
| tests/test_blended_centres.py:586 | W | bound derived from the national share. | bound derived from the provincial-ballot share. |
| tests/test_blended_centres.py:607 | W | "two pieces of evidence agreeing the party is larger than its national " | "two pieces of evidence agreeing the party is larger than its NPE " ⟨check sense⟩ |
| tests/test_blended_centres.py:608 | W | "share were overruled by a bound derived from the national share — the " | "share were overruled by a bound derived from the provincial-ballot share — the " |
| tests/test_blended_centres.py:611 | W | "the clamp is anchored on the national baseline again") | "the clamp is anchored on the NPE baseline again") |
| tests/test_blended_centres.py:642 | W | is a band on the NATIONAL route, so its absolute scale is a | statement: identifier kept (§4); no text change |
| tests/test_blended_centres.py:643 | W | national-to-local factor; only the RATIO to its own mode is dispersion. | NPE-to-local factor; only the RATIO to its own mode is dispersion. |
| tests/test_blended_centres.py:651 | W | which is the national-share reasoning the ActionSA 2026 rewrite removed. | which is the NPE-share reasoning the ActionSA 2026 rewrite removed. ⟨check sense⟩ |
| tests/test_blended_centres.py:704 | W | the national-share reasoning the ActionSA 2026 rewrite | the NPE-share reasoning the ActionSA 2026 rewrite ⟨check sense⟩ |
| tests/test_blended_centres.py:709 | W | over a national one — so the band ''(low, mid, high)'' carries two separable | over an NPE one — so the band ''(low, mid, high)'' carries two separable |
| tests/test_blended_centres.py:710 | W | things: a SCALE (roughly ''mid'', a national-to-local conversion factor) and | things: a SCALE (roughly ''mid'', an NPE-to-local conversion factor) and |
| tests/test_blended_centres.py:858 | W | contest. The fallback to the national baseline is what stops that, and it | contest. The fallback to the NPE baseline is what stops that, and it |
| tests/test_blended_centres.py:916 | W | sixteen backtest city-years. It becomes reachable the moment a national | sixteen backtest city-years. It becomes reachable the moment an NPE ⟨check sense⟩ |
| tests/test_blended_centres.py:1313 | W | # record"); and the MK case, a national share with no local vote at all | # record"); and the MK case, a provincial-ballot share with no local vote at all |
| tests/test_chain.py:29 | W | * A national fit was briefly used as a prior on city rates, on the theory that | * An NPE fit was briefly used as a prior on city rates, on the theory that |
| tests/test_chain.py:1366 |  | below = {q for q in lineage if baseline.get(q, 0.0) < pools.NATIONAL_ONLY_FLOOR} | statement: identifier kept (§4); no text change |
| tests/test_chain.py:1369 |  | f"§K1 floor of {pools.NATIONAL_ONLY_FLOOR:.1%}, so promoting party " | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2273 |  | "TINY is below NATIONAL_ONLY_FLOOR and must not be on a projected " | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2466 |  | resolve('[roster]\nparties = ["AFRICAN NATIONAL CONGRES"]\n') | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2471 |  | "a misspelt 'AFRICAN NATIONAL CONGRES' was accepted. Widening " | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2477 | W | """A party with a national vote and no lineage is the ActionSA shape. | """A party with a provincial-ballot vote and no lineage is the ActionSA shape. |
| tests/test_chain.py:2492 |  | f"national tail; above ~2% it misses the cases it exists for.") | f"NPE tail; above ~2% it misses the cases it exists for.") ⟨check sense⟩ |
| tests/test_chain.py:2494 | W | # (1) THE RULE: no declared parent AND a national share over the floor. | # (1) THE RULE: no declared parent AND a provincial-ballot share over the floor. |
| tests/test_chain.py:2495 |  | def flags(party, national, declared_parent=None): | def flags(party, NPE, declared_parent=None): ⟨check sense⟩ |
| tests/test_chain.py:2497 |  | return not parent and national >= floor | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2530 | E | f"no party in the {target.previous_npe} national file has a share over " | f"no party in the {target.previous_npe} NPE file has a share over " |
| tests/test_chain.py:2606 | W | PRECEDING NATIONAL vote" and each of those four had one. | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2651 | W | # The four that CANNOT appear, because each held a preceding national vote. | # The four that CANNOT appear, because each held a preceding provincial-ballot vote. |
| tests/test_chain.py:2666 | W | # a party with a national record and no local one: an arrival against the | # a party with an NPE record and no local one: an arrival against the |
| tests/test_chain.py:2673 | W | vs_national = arrivals_by_year.get("2016", set()) | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2674 | W | only_local = vs_local - vs_national | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2677 |  | "against the previous NATIONAL one, so the two definitions coincide at " | statement: identifier kept (§4); no text change |
| tests/test_chain.py:2679 | W | "national vote, no 2011 local one.") | "provincial-ballot vote, no 2011 local one.") |
| tests/test_chain.py:2690 | W | f"both sized from nothing and flagged as having a national record.") | f"both sized from nothing and flagged as having an NPE record.") |
| tests/test_covariate_fail_open.py:225 | W | # counts are a national and a local ballot four to five years apart and | # counts are an NPE and a local ballot four to five years apart and ⟨check sense⟩ |
| tests/test_draw_streams.py:474 | W | # Every fixture party holds a national result ('montecarlo.newness_class' | # Every fixture party holds a provincial-ballot result ('montecarlo.newness_class' |
| tests/test_drawer.py:343 | W | # anchored on the NATIONAL baseline, so it dragged ActionSA from the spine's | # anchored on the NATIONAL baseline, so it dragged ActionSA from the spine's ⟨check sense⟩ |
| tests/test_drawer.py:490 | W | # national-record fits, today's) 51.96. No mechanism is asserted per step; | # NPE-record fits, today's) 51.96. No mechanism is asserted per step; ⟨check sense⟩ |
| tests/test_drawer.py:500 | W | # whole movement appears. MK is anchored (a 2024 national vote here) and its δ | # whole movement appears. MK is anchored (a 2024 provincial-ballot vote here) and its δ |
| tests/test_drawer.py:565 | W | skip(f"no national baseline for {CITY} at {base_path} — the prior " | skip(f"no NPE baseline for {CITY} at {base_path} — the prior " |
| tests/test_drawer.py:630 | W | # fixture adds no seed, so it is the national baseline itself. | # fixture adds no seed, so it is the NPE baseline itself. |
| tests/test_ipf_feasibility.py:103 | W | skip(f"no national baseline for {CITY} at {base_path}") | skip(f"no NPE baseline for {CITY} at {base_path}") |
| tests/test_model_claims.py:229 |  | ("starting-level-blends-local-and-national", "live"), | ("starting-level-blends-local-and-NPE", "live"), ⟨check sense⟩ |
| tests/test_national_record_fit.py:1 | W | """A PARTY ABSENT FROM THE FITTING ELECTION BUT WITH ITS OWN NATIONAL RECORD IS | statement: identifier kept (§4); no text change |
| tests/test_national_record_fit.py:6 | W | from the fitting (local) election. Precedence: its own national fit when that | from the fitting (local) election. Precedence: its own NPE fit when that |
| tests/test_national_record_fit.py:13 | W | national path and the fitted-vector check goes red; restored, green. | NPE path and the fitted-vector check goes red; restored, green. ⟨check sense⟩ |
| tests/test_national_record_fit.py:15 | W | blank wards, the 2019/2024 layout that made a national fit impossible. | blank wards, the 2019/2024 layout that made an NPE fit impossible. |
| tests/test_national_record_fit.py:54 |  | def _place(rule, own_fit, *, national=0.12, nat_available=True): | statement: identifier kept (§4); no text change |
| tests/test_national_record_fit.py:59 | W | nat_available=nat_available, national=national) | statement: identifier kept (§4); no text change |
| tests/test_national_record_fit.py:74 | E | and note.startswith("fitted on the 2024 national election")) | and note.startswith("fitted on the 2024 NPE")) |
| tests/test_national_record_fit.py:87 |  | vec, note, fitted, _ = _place(rule, None, national=0.0) | statement: identifier kept (§4); no text change |
| tests/test_national_record_fit.py:98 | W | assert refused == "its 2024 national fit identifies no pool" | assert refused == "its 2024 NPE fit identifies no pool" |
| tests/test_national_record_fit.py:100 | W | assert note.endswith("(not fitted: its 2024 national fit identifies no pool)") | assert note.endswith("(not fitted: its 2024 NPE fit identifies no pool)") |
| tests/test_national_record_fit.py:110 | W | # a party with no national record at all is not "refused": nothing to fit | # a party with no NPE record at all is not "refused": nothing to fit |
| tests/test_national_record_fit.py:111 |  | vec, note, fitted, refused = _place({}, None, national=0.0) | statement: identifier kept (§4); no text change |
| tests/test_national_record_fit.py:116 | W | """Mutation: the national path returns nothing. Red; restored, green.""" | """Mutation: the NPE path returns nothing. Red; restored, green.""" ⟨check sense⟩ |
| tests/test_national_record_fit.py:177 | W | """LIVE (observed, not constructed): Johannesburg's 2024 national fit | """LIVE (observed, not constructed): Johannesburg's 2024 NPE fit |
| tests/test_national_record_fit.py:185 | W | fits, source = pools.national_fits(city, target, cfg, cats) | statement: identifier kept (§4); no text change |
| tests/test_national_record_fit.py:195 |  | nat_source=source, nat_available=True, national=0.12) | statement: identifier kept (§4); no text change |
| tests/test_number_scan.py:64 | W | other = S.scan_numbers("<p>ActionSA took 23% nationally.</p>", fixed=fixed) | other = S.scan_numbers("<p>ActionSA took 23% on the provincial ballot.</p>", fixed=fixed) ⟨check sense⟩ |
| tests/test_panel_wiring.py:19 | W | (''pools.ARRIVAL_DEFINITIONS["ARRIVED_VS_NATIONAL"]''). All four sites now go | statement: identifier kept (§4); no text change |
| tests/test_panel_wiring.py:296 | W | ''ARRIVED_VS_NATIONAL'' — *"local share > 0 and preceding-NPE share <= 0"* — | ''ARRIVED_VS_NATIONAL'' — *"local share > 0 and preceding-NPE share <= 0"* — ⟨check sense⟩ |
| tests/test_panel_wiring.py:302 | W | d = pools.ARRIVAL_DEFINITIONS["ARRIVED_VS_NATIONAL"] | statement: identifier kept (§4); no text change |
| tests/test_pool_placement.py:1 |  | """A party with no national geography is placed by its pool vector, and the | """A party with no NPE geography is placed by its pool vector, and the ⟨check sense⟩ |
| tests/test_pool_placement.py:76 | W | assert np.array_equal(old, new), "a national-record column moved" | assert np.array_equal(old, new), "an NPE-record column moved" ⟨check sense⟩ |
| tests/test_prior_local_fails_closed.py:450 | W | # exclude: '_local_thin' needs parties present locally and absent nationally. | # exclude: '_local_thin' needs parties present locally and absent on the provincial ballot. ⟨check sense⟩ |
| tests/test_register_matches_code.py:330 |  | "arrivals", "metro", "national", "province", "error", "warn", | statement: identifier kept (§4); no text change |
| tests/test_regressions.py:30 | W | evidence to [low × NATIONAL share, high × NATIONAL share] while the level | statement: identifier kept (§4); no text change |
| tests/test_regressions.py:264 | W | θ's band is a band on the NATIONAL route. Multiplying it by the national | statement: identifier kept (§4); no text change |
| tests/test_regressions.py:275 | W | f"against the national baseline rather than against the level the " | f"against the NPE baseline rather than against the level the " |
| tests/test_regressions.py:285 | W | # settled on, not against the national baseline. The blend reads | # settled on, not against the NPE baseline. The blend reads |
| tests/test_regressions.py:291 | W | "settled on — and not against the national baseline") | "settled on — and not against the NPE baseline") |
| tests/test_roster_aware_baseline.py:10 | W | vote, no prior national vote, nothing to swing — so it forecast zero against 44 | vote, no prior provincial-ballot vote, nothing to swing — so it forecast zero against 44 |
| tests/test_roster_aware_baseline.py:223 | W | f"local vote, no prior national vote, 44 seats — so either the roster " | f"local vote, no prior provincial-ballot vote, 44 seats — so either the roster " |
| tests/test_roster_aware_baseline.py:1116 | W | # two calls, the national baseline and the preceding local result, and a | # two calls, the NPE baseline and the preceding local result, and a |
| tests/test_roster_aware_baseline.py:1157 |  | # The baseline the national call hands the spine, captured at the call: since | # The baseline the NPE call hands the spine, captured at the call: since ⟨check sense⟩ |
| tests/test_roster_aware_baseline.py:1192 |  | the trace. RISE takes GOOD's transfer only through the NATIONAL call (it | statement: identifier kept (§4); no text change |
| tests/test_roster_aware_baseline.py:1211 | W | # RISE reaches the spine by the national route only, ASA at its local level. | # RISE reaches the spine by the NPE route only, ASA at its local level. |
| tests/test_roster_aware_baseline.py:1214 |  | # RISE (national call): the SIZE, not only the direction. What the call | # RISE (NPE call): the SIZE, not only the direction. What the call ⟨check sense⟩ |
| tests/test_roster_aware_baseline.py:1232 | W | f"the national-baseline call is not applying r x P") | f"the NPE-baseline call is not applying r x P") ⟨check sense⟩ |
| tests/test_seats.py:533 | W | 3-seat arrival, and 'ARRIVED_VS_NATIONAL' says 'party != IND'.""" | statement: identifier kept (§4); no text change |
| tests/test_spine.py:1 | W | """''levels.spine'' — the national-to-local level path, called by nothing that asserts. | """''levels.spine'' — the NPE-to-local level path, called by nothing that asserts. |
| tests/test_spine.py:5 | W | it decides ActionSA's 2026 level — 5.98% on the national route, 15.23% on its | it decides ActionSA's 2026 level — 5.98% on the NPE route, 15.23% on its |
| tests/test_spine.py:16 | W | with both records blends, one with only a national record takes the national | with both records blends, one with only an NPE record takes the national |
| tests/test_spine.py:22 |  | exactly ''sqrt(national x local)'' — which is precisely what ''SPINE_K'''s | exactly ''sqrt(NPE x local)'' — which is precisely what ''SPINE_K'''s ⟨check sense⟩ |
| tests/test_spine.py:104 |  | #   BOTH      national 9%, local 1%   -> blends between 0.09 and 0.01 | #   BOTH      NPE 9%, local 1%   -> blends between 0.09 and 0.01 ⟨check sense⟩ |
| tests/test_spine.py:105 |  | #   UP        national 1%, local 9%   -> blends the other way (monotonicity) | #   UP        NPE 1%, local 9%   -> blends the other way (monotonicity) ⟨check sense⟩ |
| tests/test_spine.py:106 |  | #   NOTHETA   national 5%, local 2%   -> in both records' PARTIES, but with no | #   NOTHETA   NPE 5%, local 2%   -> in both records' PARTIES, but with no ⟨check sense⟩ |
| tests/test_spine.py:108 |  | #   NATONLY   national 6%, no local   -> first local election (MK in 2026) | #   NATONLY   NPE 6%, no local   -> first local election (MK in 2026) ⟨check sense⟩ |
| tests/test_spine.py:109 | W | #   LOCONLY   no national, local 4%   -> stood locally, not nationally | #   LOCONLY   no NPE, local 4%   -> stood locally, not on the provincial ballot ⟨check sense⟩ |
| tests/test_spine.py:110 |  | #   NEITHER   national 0.0, no local  -> in neither; must not appear at all | #   NEITHER   NPE 0.0, no local  -> in neither; must not appear at all ⟨check sense⟩ |
| tests/test_spine.py:136 | W | necessity and the level is the national share times the party's retention | necessity and the level is the provincial-ballot share times the party's retention |
| tests/test_spine.py:144 | W | assert "NATONLY" in level, "a party with a national record must be levelled" | assert "NATONLY" in level, "a party with an NPE record must be levelled" |
| tests/test_spine.py:145 |  | assert info["detail"]["NATONLY"]["route"].startswith("national only") | assert info["detail"]["NATONLY"]["route"].startswith("NPE only") ⟨check sense⟩ |
| tests/test_spine.py:151 | W | """A party that stood locally but not nationally has no national route to blend. | """A party that stood locally but not nationally has no NPE route to blend. |
| tests/test_spine.py:172 | W | (national) and 1.00% (local), so its level must be strictly between them. | (NPE) and 1.00% (local), so its level must be strictly between them. ⟨check sense⟩ |
| tests/test_spine.py:183 |  | assert _close(d["national"], 0.09) and _close(d["local"], 0.01), d | statement: identifier kept (§4); no text change |
| tests/test_spine.py:194 |  | ''level = national^(1-w) * local^w'' the log of the level is affine in | ''level = NPE^(1-w) * local^w'' the log of the level is affine in ⟨check sense⟩ |
| tests/test_spine.py:228 |  | assert _close(d["national"], 0.09 * 1.3), d | statement: identifier kept (§4); no text change |
| tests/test_spine.py:230 |  | assert not _close(d["national"], 0.09) and not _close(d["local"], 0.01), ( | statement: identifier kept (§4); no text change |
| tests/test_spine.py:234 |  | assert _close(level["B"], d["national"] ** (1 - w) * d["local"] ** w, 1e-9), ( | statement: identifier kept (§4); no text change |
| tests/test_spine.py:290 | W | It is the pure national spine -- the configuration §1.30 measured at RMSE | It is the pure NPE spine -- the configuration §1.30 measured at RMSE |
| tests/test_spine.py:342 | W | "more theta evidence must move a party toward the national spine") | "more theta evidence must move a party toward the NPE spine") |
| tests/test_spine.py:349 | W | national route is discarded entirely however small k is. That is the | NPE route is discarded entirely however small k is. That is the |
| tests/test_spine.py:413 | W | ''NEITHER'' holds a national baseline of exactly 0.0 and no previous local | ''NEITHER'' holds an NPE baseline of exactly 0.0 and no previous local |
| tests/test_spine.py:469 |  | assert info["detail"]["NO_THETA_NAT"]["route"].startswith("national only") | assert info["detail"]["NO_THETA_NAT"]["route"].startswith("NPE only") ⟨check sense⟩ |
| tests/test_spine.py:484 |  | party with no theta record of its own at ''national x 1.0''. So "we have no | party with no theta record of its own at ''NPE x 1.0''. So "we have no ⟨check sense⟩ |
| tests/test_spine.py:485 | W | national-to-local retention record at all" and "the record says parties | NPE-to-local retention record at all" and "the record says parties |
| tests/test_spine.py:486 | W | retain their national share exactly" produce the same level AND the same | retain their provincial-ballot share exactly" produce the same level AND the same |
| tests/test_spine.py:537 | W | that a party at 0.20% of the national vote and one at 30%, both facing | that a party at 0.20% of the provincial-ballot vote and one at 30%, both facing |
| tests/test_spine.py:558 |  | assert info["detail"]["TINY"]["route"].startswith("national only") | assert info["detail"]["TINY"]["route"].startswith("NPE only") ⟨check sense⟩ |
| tests/test_spine.py:619 |  | point.** 'w' weights the LOCAL route, so 'k = 0' means "pure national | point.** 'w' weights the LOCAL route, so 'k = 0' means "pure NPE ⟨check sense⟩ |
| tests/test_spine.py:620 |  | spine". Taking 'w = 1' at 'worth = 0' would make 'k = 0' mean pure-national | spine". Taking 'w = 1' at 'worth = 0' would make 'k = 0' mean pure-NPE ⟨check sense⟩ |
| tests/test_spine.py:628 | W | no sense there either.* The national route for a party with no national | no sense there either.* The NPE route for a party with no national |
| tests/test_spine.py:640 | W | f"{party}: k=0 must put every blended party on its NATIONAL " | statement: identifier kept (§4); no text change |
| tests/test_spine.py:645 |  | assert abs(levels[party] - d["national"]) < 1e-12, ( | statement: identifier kept (§4); no text change |
| tests/test_spine.py:646 | W | f"{party}: w_local is 0 but the level is not the national one") | f"{party}: w_local is 0 but the level is not the NPE one") |
| tests/test_stage_estimation.py:8 |  | ''20_spine''        per-party central level, blending the national and local routes | ''20_spine''        per-party central level, blending the NPE and local routes ⟨check sense⟩ |
| tests/test_stage_estimation.py:56 | W | * ''20_spine'''s ''detail[p]["national"]'' is not the party's national vote | * ''20_spine'''s ''detail[p]["national"]'' is not the party's provincial-ballot vote |
| tests/test_stage_estimation.py:126 | W | #                the national share it is measured off. Dimensionless. The band | #                the provincial-ballot share it is measured off. Dimensionless. The band |
| tests/test_stage_estimation.py:143 | W | #                national baseline, and so none of them carrying a centre. | #                NPE baseline, and so none of them carrying a centre. |
| tests/test_stage_estimation.py:349 |  | #   detail       {party: {w_local, worth, route, national, local}}. | #   detail       {party: {w_local, worth, route, NPE, local}}. ⟨check sense⟩ |
| tests/test_stage_estimation.py:350 |  | #                ⚠ 'national' and 'local' are LEVELS, not the party's raw shares: | #                ⚠ 'NPE' and 'local' are LEVELS, not the party's raw shares: ⟨check sense⟩ |
| tests/test_stage_estimation.py:383 |  | missing = [k for k in ("w_local", "worth", "route", "national", "local") | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:391 |  | """''level == local**w * national**(1-w)'', exactly, on every row. | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:398 | W | The degenerate rows are checked too: a national-only party must sit exactly | The degenerate rows are checked too: an NPE only party must sit exactly |
| tests/test_stage_estimation.py:399 | W | on its national route, a local-only party exactly on its local one. | on its NPE route, a local-only party exactly on its local one. |
| tests/test_stage_estimation.py:408 |  | float(row["national"]), float(level[party])) | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:424 |  | f"reports (local {loc:.6g}, national {nat:.6g}, w_local {w:.4f}) " | f"reports (local {loc:.6g}, NPE {nat:.6g}, w_local {w:.4f}) " ⟨check sense⟩ |
| tests/test_stage_estimation.py:440 |  | loc, nat = row.get("local", 0.0), row.get("national", 0.0) | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:455 |  | labelled "blend" anyway. For ActionSA at 2026 the label said the national | labelled "blend" anyway. For ActionSA at 2026 the label said the NPE ⟨check sense⟩ |
| tests/test_stage_estimation.py:465 |  | w, loc, nat = row.get("w_local"), row.get("local"), row.get("national") | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:476 |  | if not route.startswith("national only"): | if not route.startswith("NPE only"): ⟨check sense⟩ |
| tests/test_stage_estimation.py:477 | W | faults.append(f"{party}: has a national record only and is labelled {route!r}") | faults.append(f"{party}: has an NPE record only and is labelled {route!r}") |
| tests/test_stage_estimation.py:479 |  | faults.append(f"{party}: national-only route carrying local weight {w}") | faults.append(f"{party}: NPE only route carrying local weight {w}") ⟨check sense⟩ |
| tests/test_stage_estimation.py:486 |  | full_local, full_national = w >= 1.0, w <= 0.0 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:490 | W | f"about whether the national route contributed anything") | f"about whether the NPE route contributed anything") |
| tests/test_stage_estimation.py:491 |  | if full_national != ("full national" in route): | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:507 | W | pure national spine" true for every party — so it is pinned here. | pure NPE spine" true for every party — so it is pinned here. |
| tests/test_stage_estimation.py:515 |  | if not (row.get("local", 0) > 0 and row.get("national", 0) > 0): | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:542 |  | faults, seen = [], {"blend": 0, "national_only": 0, "local_only": 0} | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:547 |  | elif route.startswith("national only"): | elif route.startswith("NPE only"): ⟨check sense⟩ |
| tests/test_stage_estimation.py:548 |  | seen["national_only"] += 1 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:577 |  | ''moved_from_national + moved_from_local == disagreement'' (the weight splits | ''moved_from_national + moved_from_local == disagreement'' (the weight splits ⟨check sense⟩ |
| tests/test_stage_estimation.py:582 |  | This block is the only thing that can distinguish "changing the national | This block is the only thing that can distinguish "changing the NPE ⟨check sense⟩ |
| tests/test_stage_estimation.py:583 | W | route did not move the forecast" from "the national route was never worth | route did not move the forecast" from "the NPE route was never worth |
| tests/test_stage_estimation.py:594 |  | blend.get("moved_from_national"), | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:596 |  | for name, value in (("disagreement", gap), ("moved_from_national", from_nat), | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:604 |  | f"the disagreement does not split: moved_from_national {from_nat:.6f} " | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:610 |  | f"moved_from_national/disagreement ({want_share:.6f})") | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:617 |  | if r.get("local", 0) > 0 and r.get("national", 0) > 0 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:619 |  | full_national = sum(1 for r in detail.values() | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:620 |  | if r.get("local", 0) > 0 and r.get("national", 0) > 0 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:624 |  | if blend.get("at_full_national") != full_national: | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:626 |  | f"at_full_national {blend.get('at_full_national')!r}; " | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:627 |  | f"{full_national} rows sit at w=0") | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1118 | W | national baseline, no spine level, no theta prior and no arrival seed used to | NPE baseline, no spine level, no theta prior and no arrival seed used to |
| tests/test_stage_estimation.py:1169 | W | NO national baseline, whose width is the fit extrapolated to ''log(1e-5)''. | NO NPE baseline, whose width is the fit extrapolated to ''log(1e-5)''. |
| tests/test_stage_estimation.py:1276 | W | # party        national level, local level, own theta worth | # party        NPE level, local level, own theta worth |
| tests/test_stage_estimation.py:1284 |  | blend_n = gap_total = from_national = from_local = 0 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1285 |  | at_full_local = at_full_national = 0 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1294 | W | route, at_full_national = "blend at full national (k=0)", at_full_national + 1 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1297 |  | from_national, from_local = from_national + w * gap, from_local + (1 - w) * gap | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1299 |  | w, value, route = 0.0, nat, "national only (first local election)" | w, value, route = 0.0, nat, "NPE only (first local election)" ⟨check sense⟩ |
| tests/test_stage_estimation.py:1301 | W | w, value, route = 1.0, loc, "local only (no national record)" | w, value, route = 1.0, loc, "local only (no NPE record)" |
| tests/test_stage_estimation.py:1306 |  | "national_only": sum(1 for n, l, _ in rows.values() if n > 0 >= l), | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1325 |  | "share_local": (from_national / gap_total) if gap_total else 0.0}, | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1421 |  | if r.get("local", 0) > 0 and r.get("national", 0) > 0)[0] | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1489 |  | s["level"][party] = max(row["national"], row["local"]) * 1.10 | statement: identifier kept (§4); no text change |
| tests/test_stage_estimation.py:1495 |  | s["detail"][_a_blend_party(s)]["route"] = "national only (first local election)" | s["detail"][_a_blend_party(s)]["route"] = "NPE only (first local election)" ⟨check sense⟩ |
| tests/test_stage_estimation.py:1506 |  | + (1 - w) * math.log(row["national"])) | statement: identifier kept (§4); no text change |
| tests/test_stage_inputs.py:1210 | W | # NATIONAL baseline that did not stand locally; 'size' counts parties on | # NATIONAL baseline that did not stand locally; 'size' counts parties on ⟨check sense⟩ |
| tests/test_standalone_modules.py:144 |  | "national-election ingest, run once per NPE file; its LGE twin " | "NPE-election ingest, run once per NPE file; its LGE twin " ⟨check sense⟩ |
| tests/test_standalone_modules.py:155 |  | "README.md step 3: 'python src/build_geo.py'. Clips the national ward " | "README.md step 3: 'python src/build_geo.py'. Clips the NPE ward " ⟨check sense⟩ |
| tests/test_temporal.py:415 | W | the national vote sitting in the municipalities the party contests. Deciding | the provincial-ballot vote sitting in the municipalities the party contests. Deciding |
| tests/test_temporal.py:489 | E | national election preceding each (''cityconfig.preceding''); for ρ, | NPE preceding each (''cityconfig.preceding''); for ρ, |
| tests/test_temporal.py:561 | E | the national election preceding each, from the calendar) plus each | the NPE preceding each, from the calendar) plus each |
| tests/test_temporal.py:562 | E | metro's 2021 LGE and 2019 national election. Both directions. | metro's 2021 LGE and 2019 NPE. Both directions. |
| tests/test_theta_prior.py:5 | W | national share before it, plus a diagnostic block. It has existed for the whole | provincial-ballot share before it, plus a diagnostic block. It has existed for the whole |
| tests/test_theta_prior.py:193 | E | """The preceding national election's citywide shares, off disk.""" | """The preceding NPE's citywide shares, off disk.""" |
| tests/test_theta_prior.py:197 | E | skip(f"no national election before {year} in the calendar") | skip(f"no NPE before {year} in the calendar") |
| tests/test_theta_prior.py:212 | W | If this fails, a party facing its first local election with a national vote | If this fails, a party facing its first local election with a provincial-ballot vote |
| tests/test_theta_prior.py:227 | W | "a party with a national baseline and no retention record got no θ " | "a party with an NPE baseline and no retention record got no θ " |
| tests/test_theta_prior.py:328 | W | 10% of the national vote, one off 0.02%. The second must end up on the | 10% of the provincial-ballot vote, one off 0.02%. The second must end up on the |
| tests/test_theta_prior.py:832 | W | party with a national baseline and no spine level, no seed and no θ prior | party with an NPE baseline and no spine level, no seed and no θ prior |
| tests/test_theta_prior.py:904 | W | not here and cannot be: θ converts a national share into a local one and | not here and cannot be: θ converts a provincial-ballot share into a local one and |
| tests/test_theta_prior.py:905 | W | there is no national share to convert."* The loop iterates | there is no provincial-ballot share to convert."* The loop iterates |
| tests/test_theta_prior.py:907 |  | priced at Johannesburg 2021 are in the record and not in the 2019 national | priced at Johannesburg 2021 are in the record and not in the 2019 NPE ⟨check sense⟩ |
| tests/test_theta_prior.py:921 |  | record["GONE_NATIONAL"] = [(_line(S0) * math.exp(D), S0)] * 2 | statement: identifier kept (§4); no text change |
| tests/test_theta_prior.py:924 |  | del baseline["GONE_NATIONAL"]          # in the record, not in the baseline | statement: identifier kept (§4); no text change |
| tests/test_theta_prior.py:929 |  | assert "GONE_NATIONAL" in priors, ( | statement: identifier kept (§4); no text change |
| tests/test_theta_prior.py:930 | W | "a party with a record and no national baseline is no longer priced. " | "a party with a record and no NPE baseline is no longer priced. " |
| tests/test_theta_prior.py:934 |  | assert groups["sd"]["GONE_NATIONAL"] == widest, ( | statement: identifier kept (§4); no text change |
| tests/test_theta_prior.py:935 |  | f"its width is {groups['sd']['GONE_NATIONAL']:.4f} against a widest " | statement: identifier kept (§4); no text change |
| tests/test_theta_prior.py:938 |  | assert groups["sd"]["GONE_NATIONAL"] > groups["sd"]["FILLER_00"], ( | statement: identifier kept (§4); no text change |
| tests/test_theta_prior.py:947 | W | "no party is priced without a national baseline at 2021 any more — " | "no party is priced without an NPE baseline at 2021 any more — " |
| tests/test_theta_prior.py:990 |  | driven by how many recorded parties happen to appear in the national | driven by how many recorded parties happen to appear in the NPE ⟨check sense⟩ |
| tests/test_theta_prior.py:1081 | W | # It looked: the parties with a 2021 national share and a θ record. | # It looked: the parties with a 2021 provincial-ballot share and a θ record. |
| tests/test_universal_draw.py:234 | W | ('montecarlo.newness_class'): an anchored newcomer holds a national result | ('montecarlo.newness_class'): an anchored newcomer holds a provincial-ballot result |
| tests/test_universal_draw.py:235 |  | in the city before any seed (its centre is the spine's national-only | in the city before any seed (its centre is the spine's NPE only ⟨check sense⟩ |
| tests/test_universal_draw.py:237 |  | also calls national-only, so the post-seed baseline must not decide it; | also calls NPE only, so the post-seed baseline must not decide it; ⟨check sense⟩ |
| tests/test_universal_draw.py:372 | W | the spine sized on its national-only route without an arrival seed, in | the spine sized on its NPE only route without an arrival seed, in |
| tests/test_universal_draw.py:373 | W | both directions; GOOD (a 2019 national vote) is anchored, ActionSA (no | both directions; GOOD (a 2019 provincial-ballot vote) is anchored, ActionSA (no |
| tests/test_universal_draw.py:374 | W | national vote, seeded) unanchored; the ANC is not new; and the record's | provincial-ballot vote, seeded) unanchored; the ANC is not new; and the record's |
| tests/test_universal_draw.py:382 |  | spine_national = {p for p in new | statement: identifier kept (§4); no text change |
| tests/test_universal_draw.py:383 |  | if route[p] == "national only (first local election)" | if route[p] == "NPE only (first local election)" ⟨check sense⟩ |
| tests/test_universal_draw.py:388 | W | assert anchored == spine_national, (anchored ^ spine_national) | statement: identifier kept (§4); no text change |
| tests/test_ward_contest_rule.py:9 | W | * every slated party, national record or not, has ward votes only in the wards | * every slated party, NPE record or not, has ward votes only in the wards |
| tests/test_ward_contest_rule.py:53 | W | """BIG everywhere; NAT (a national-record party) and WARDONLY in ward 1 | """BIG everywhere; NAT (an NPE-record party) and WARDONLY in ward 1 ⟨check sense⟩ |
| tests/test_ward_contest_rule.py:76 | W | # (a) a national-record party stands only where its slate says | # (a) an NPE-record party stands only where its slate says ⟨check sense⟩ |
| tests/test_ward_contest_rule.py:82 | W | assert "NAT" in m["masked"], "a national-record party was not masked" | assert "NAT" in m["masked"], "an NPE-record party was not masked" ⟨check sense⟩ |
| tests/test_ward_contest_rule.py:209 | W | assert "UDM" in b.ward_only(), "a national-record ward-only party" | assert "UDM" in b.ward_only(), "an NPE-record ward-only party" ⟨check sense⟩ |
| tests/test_your_forecast_page.py:867 | E | bounds read, the national files of the prior among them); ''e'' is over | bounds read, the NPE files of the prior among them); ''e'' is over |
| tests/test_your_forecast_page.py:1022 |  | national = build_make.npe_priors(city, target, **where) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1024 |  | cells, party = build_make.ward_ranges(roster, wards, local, national, bins, b["allowance"], | cells, party = build_make.ward_ranges(roster, wards, local, NPE, bins, b["allowance"], ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1039 | E | calendar's national election before l, the approximation left out; the | calendar's NPE before l, the approximation left out; the |
| tests/test_your_forecast_page.py:1042 | W | no ward vote anywhere in the city then, a national vote in them; each | no ward vote anywhere in the city then, a provincial-ballot vote in them; each |
| tests/test_your_forecast_page.py:1044 |  | national or newcomer); ''party_ranges'' and ''city_limits'' are keyed by | NPE or newcomer); ''party_ranges'' and ''city_limits'' are keyed by ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1057 | W | file: its national vote becomes its prior, and deleted from the national | file: its provincial-ballot vote becomes its prior, and deleted from the national |
| tests/test_your_forecast_page.py:1059 | E | elections deleted from the national file: it becomes a newcomer; (7) one | elections deleted from the NPE file: it becomes a newcomer; (7) one |
| tests/test_your_forecast_page.py:1060 | W | VD's national votes raised: exactly that VD's wards move.""" | VD's NPE votes raised: exactly that VD's wards move.""" ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1096 |  | national_by_vd = collections.defaultdict(set) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1099 |  | national_by_vd[r["VD_Number"].strip()].add(P.canonical(r["sPartyName"])) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1101 |  | stood_national = set().union(*national_by_vd.values()) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1102 |  | kind = {c: "local" if c in stood_local else "national" if c in stood_national else "newcomer" | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1108 |  | want \|= {(str(w), c) for c in national_by_vd.get(vd, ()) if kind.get(c) == "national"} | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1115 |  | assert {"local", "national", "newcomer"} == set(kind.values()) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1217 | W | # (5) a party deleted from the preceding file: its national vote becomes | # (5) a party deleted from the preceding file: its provincial-ballot vote becomes |
| tests/test_your_forecast_page.py:1218 | E | # its prior; deleted from the national file too, it is a newcomer | # its prior; deleted from the NPE file too, it is a newcomer |
| tests/test_your_forecast_page.py:1219 | W | c5 = min((c for c in roster if kind[c] == "local" and c in stood_national), | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1224 |  | assert party[c5]["kind"] == "national" | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1226 |  | {str(w) for vd, w, reg in parts if reg > 0 and c5 in national_by_vd.get(vd, ())} | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1231 | E | # (6) a party new to local elections deleted from the national file | # (6) a party new to local elections deleted from the NPE file |
| tests/test_your_forecast_page.py:1232 | T | c6 = max((c for c in roster if kind[c] == "national"), key=lambda c: b["party_ranges"][c]["prior"]) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1237 | W | # (7) one VD's national votes raised | # (7) one VD's NPE votes raised ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1240 |  | and c6 in national_by_vd.get(v, ())) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1304 |  | city at the preceding local election, else ''national'' with a vote at the | city at the preceding local election, else ''NPE'' with a vote at the ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1305 |  | preceding national one, else ''newcomer''), equal to its ''party_ranges'' | preceding NPE one, else ''newcomer''), equal to its ''party_ranges'' ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1310 | W | by the national-to-local citywide extremes; a newcomer's, zero to the | by the NPE-to-local citywide extremes; a newcomer's, zero to the |
| tests/test_your_forecast_page.py:1314 | W | a party's collapse from a national to a local election is left out of the | a party's collapse from an NPE to a local election is left out of the ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1315 | W | national-to-local citywide extremes, and the same swing short of a | NPE-to-local citywide extremes, and the same swing short of a |
| tests/test_your_forecast_page.py:1337 |  | national = collections.Counter() | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1339 |  | national[P.canonical(r["sPartyName"])] += int(r["Party_Votes"]) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1340 |  | nat_total = sum(national.values()) | nat_total = sum(NPE.values()) ⟨check sense⟩ |
| tests/test_your_forecast_page.py:1357 |  | kind = {c: "local" if local_city[c] > 0 else "national" if national[c] > 0 else "newcomer" for c in roster} | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1369 |  | want = moved(national[c] / nat_total, ext["npe_city"]) | statement: identifier kept (§4); no text change |
| tests/test_your_forecast_page.py:1393 | W | # constructed: a collapse from national to local, and the same swing short of one | # constructed: a collapse from NPE-to-local, and the same swing short of one |

### Appendix C. Project documents (hand-edited) (179 lines)

| file:line | sense | current words | proposed words |
|---|---|---|---|
| DATA-QUALITY.md:90 |  | election day have different IDs** (2019 provincial is 827, not the national | election day have different IDs** (2019 provincial is 827, not the NPE ⟨check sense⟩ |
| DATA-QUALITY.md:1065 |  | 'NATIONAL COLOURED CONGRESS' (3.482% at CPT 2024) does not appear before it; | 'NATIONAL COLOURED CONGRESS' (3.482% at CPT 2024) does not appear before it; ⟨check sense⟩ |
| DATA-QUALITY.md:1120 |  | national reads, not a repair to a live forecast number — and the reason it is | NPE reads, not a repair to a live forecast number — and the reason it is ⟨check sense⟩ |
| DATA-QUALITY.md:1125 | E | ## 18. 🔴 The results-portal NPE layout carries no ward, so four national elections have voting districts and no wards (found 2026-09-14) | ## 18. 🔴 The results-portal NPE layout carries no ward, so four NPEs have voting districts and no wards (found 2026-09-14) |
| DATA-QUALITY.md:1127 | W | **The class.** The Commission publishes national results in two layouts. The | **The class.** The Commission publishes provincial-ballot result in two layouts. The |
| DATA-QUALITY.md:1149 | E | **32 city-years carry voting districts and no wards** — four national elections | **32 city-years carry voting districts and no wards** — four NPEs |
| DATA-QUALITY.md:1231 | W | vote, no national baseline and no arrival seed has no pool vector, so the run | vote, no NPE baseline and no arrival seed has no pool vector, so the run |
| DUPLICATION-AUDIT.md:84 | W | is what produces the level. The named case is **MK in 2026** — a national vote | is what produces the level. The named case is **MK in 2026** — a provincial-ballot vote |
| ITERATING.md:605 | E | whose national file the calendar itself calls *"the approximate pre-metro | whose NPE file the calendar itself calls *"the approximate pre-metro |
| JUDGEMENT-CALLS.md:156 | W | \| 'NATIONAL_ONLY_FLOOR' \| 0.001 \| 'pools.py' \| The national share below which a party with no local record is NOT assumed onto an unheld ballot. … | \| 'NATIONAL_ONLY_FLOOR' \| 0.001 \| 'pools.py' \| The provincial-ballot share below which a party with no local record is NOT assumed onto an unheld… |
| JUDGEMENT-CALLS.md:157 | W | \| 'PRIOR_LOCAL_FLOOR' \| 0.001 \| 'pools.py' \| The prior-LOCAL share below which a party with no national vote is not assumed onto an unheld ballot… | \| 'PRIOR_LOCAL_FLOOR' \| 0.001 \| 'pools.py' \| The prior-LOCAL share below which a party with no provincial-ballot vote is not assumed onto an unhe… |
| JUDGEMENT-CALLS.md:177 | W | \| 'PROJECTED_METRO_SHARE' \| eight per-metro shares of the national vote, 2021 values \| — \| The last observed value, so nothing is extrapolated; n… | \| 'PROJECTED_METRO_SHARE' \| eight per-metro shares of the provincial-ballot vote, 2021 values \| — \| The last observed value, so nothing is extrap… |
| JUDGEMENT-CALLS.md:192 | W | \| 'spine_k = 0' on a party with no θ evidence \| 'w_local = 0.0' \| — \| A CHOSEN limit ('w = 0', pure national spine), inert at the shipped 'spine_… | \| 'spine_k = 0' on a party with no θ evidence \| 'w_local = 0.0' \| — \| A CHOSEN limit ('w = 0', pure NPE spine), inert at the shipped 'spine_k = N… |
| JUDGEMENT-CALLS.md:194 | W | \| 'SPLINTER_PARENT_WEIGHT' \| 0.35 \| — \| The DEFAULT 0.35, measured over 22 splinter-metro cases (EFF 0.89, GOOD 0.28, ActionSA about 0.02), no bo… | \| 'SPLINTER_PARENT_WEIGHT' \| 0.35 \| — \| The DEFAULT 0.35, measured over 22 splinter-metro cases (EFF 0.89, GOOD 0.28, ActionSA about 0.02), no bo… |
| JUDGEMENT-CALLS.md:265 | W | \| the size the shrink target is evaluated at \| 'levels._shrink_one' (via '_shrunk', 'theta_prior') \| The party's current size on the route (nation… | \| the size the shrink target is evaluated at \| 'levels._shrink_one' (via '_shrunk', 'theta_prior') \| The party's current size on the route (provin… |
| JUDGEMENT-CALLS.md:300 | W | **Record.** **MEASURED 2026-08-22 (§1.71) and it is the largest open modelling question.** θ dispersion for parties ≥5% of the national vote: 2004→20… | **Record.** **MEASURED 2026-08-22 (§1.71) and it is the largest open modelling question.** θ dispersion for parties ≥5% of the provincial-ballot vote… |
| JUDGEMENT-CALLS.md:596 | W | **Record.** '_worth_r' is computed and discarded with an underscore, so a party with a rich local record and thin θ is still pushed onto the national… | **Record.** '_worth_r' is computed and discarded with an underscore, so a party with a rich local record and thin θ is still pushed onto the NPE rout… |
| JUDGEMENT-CALLS.md:834 | E | **Record.** Which parties reach 'pools.arrival_rules' rather than θ × baseline. A party with a *trace* in the preceding national election — 0.05–0.17… | **Record.** Which parties reach 'pools.arrival_rules' rather than θ × baseline. A party with a *trace* in the preceding NPE — 0.05–0.17% in that metr… |
| JUDGEMENT-CALLS.md:836 | W | **Note, 2026-10-09 (model correction batch, item 8).** A roster party with a previous-LGE list vote and no national baseline is no longer outside the… | **Note, 2026-10-09 (model correction batch, item 8).** A roster party with a previous-LGE list vote and no NPE baseline is no longer outside the run:… |
| JUDGEMENT-CALLS.md:945 | W | **Now.** The size centre ('size_centre', fitted on the sizes the ratios were measured off) is evaluated at the party's size at the target: its share … | **Now.** The size centre ('size_centre', fitted on the sizes the ratios were measured off) is evaluated at the party's size at the target: its share … |
| JUDGEMENT-CALLS.md:958 | W | **Now.** A party's own θ (ρ) observations count only where measured off a national (previous local) share within 'h' natural-log units of its current… | **Now.** A party's own θ (ρ) observations count only where measured off an NPE (previous local) share within 'h' natural-log units of its current one… ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:990 |  | **Limits.** The size-group width is the size line of the θ record, fitted against the common centre; for a party far below the record's sizes it is a… | **Limits.** The size-group width is the size line of the θ record, fitted against the common centre; for a party far below the record's sizes it is a… ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:999 |  | **Now.** A pair is reported when the party's drawn share of the pool's vote exceeds 'record + margin' in more than 5% of draws. 'record': the party's… | **Now.** A pair is reported when the party's drawn share of the pool's vote exceeds 'record + margin' in more than 5% of draws. 'record': the party's… ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:1003 |  | **Limits.** It reports and changes nothing; a firing pair is a question for a person. The margin is taken from fitted rates, which are noisy in small… | **Limits.** It reports and changes nothing; a firing pair is a question for a person. The margin is taken from fitted rates, which are noisy in small… ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:1016 | W | **Now.** For every (party, metro) pair with a by-election in the metro between the 2021 LGE and 2024-05-29 and a list vote at the 2021 LGE or on the … | **Now.** For every (party, metro) pair with a by-election in the metro between the 2021 LGE and 2024-05-29 and a list vote at the 2021 LGE or on the … |
| JUDGEMENT-CALLS.md:1034 | W | - **'B' is a stand-in for the 2026 spine.** It is the 2021 list share through the θ record at the 2019 national share. Its residuals carry a party-si… | - **'B' is a stand-in for the 2026 spine.** It is the 2021 list share through the θ record at the 2019 provincial-ballot share. Its residuals carry a… |
| JUDGEMENT-CALLS.md:1038 | E | **In the model (2026-10-10).** 'montecarlo.blended_centres' gives each party with by-election evidence the weight of its class ('montecarlo.bye_weigh… | **In the model (2026-10-10).** 'montecarlo.blended_centres' gives each party with by-election evidence the weight of its class ('montecarlo.bye_weigh… |
| JUDGEMENT-CALLS.md:1110 |  | \| §SJ1 \| MK \| joburg 2026 \| 'parent_weight = 0.9' (a pool-vector judgement, not a strength: no 'support', 'overperform' or 'sigma_j') \| Owner, 2… | \| §SJ1 \| MK \| joburg 2026 \| 'parent_weight = 0.9' (a pool-vector judgement, not a strength: no 'support', 'overperform' or 'sigma_j') \| Owner, 2… ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:1111 | W | \| §SJ2 \| ASA (ActionSA) — **WITHDRAWN 2026-10-23** \| joburg 2026 \| ~~'support = 0.176', 'sigma_j = 0'~~ (entry removed from 'judgements/joburg-20… | \| §SJ2 \| ASA (ActionSA) — **WITHDRAWN 2026-10-23** \| joburg 2026 \| ~~'support = 0.176', 'sigma_j = 0'~~ (entry removed from 'judgements/joburg-20… |
| JUDGEMENT-CALLS.md:1139 | E | that had a vote in the 2024 national election cannot be moved by its | that had a vote in the 2024 NPE cannot be moved by its |
| JUDGEMENT-CALLS.md:1149 | W | **Where.** 'DEFAULTS["w_bye"]' in 'src/montecarlo.py', applied by 'montecarlo.bye_weight' (override branch) in 'montecarlo.blended_centres': 'centre … | **Where.** 'DEFAULTS["w_bye"]' in 'src/montecarlo.py', applied by 'montecarlo.bye_weight' (override branch) in 'montecarlo.blended_centres': 'centre … |
| JUDGEMENT-CALLS.md:1160 | E | national election and none in the 2021 local election, on the list or in a | NPE and none in the 2021 local election, on the list or in a |
| JUDGEMENT-CALLS.md:1166 | W | **Where.** 'montecarlo.blended_centres': a party in the by-election input that is sized by the arrival record (a pool seed, which only a party with n… | **Where.** 'montecarlo.blended_centres': a party in the by-election input that is sized by the arrival record (a pool seed, which only a party with n… |
| JUDGEMENT-CALLS.md:1581 | W | **Scope (owner, 2026-10-15, "option A").** The default applies only to a splinter with NO record of its own. A party absent from the fitting (local) … | **Scope (owner, 2026-10-15, "option A").** The default applies only to a splinter with NO record of its own. A party absent from the fitting (local) … |
| JUDGEMENT-CALLS.md:1713 | W | **Now.** A CHOSEN limit ('w = 0', pure national spine), inert at the shipped 'spine_k = None' and reachable only by a sweep, which is what it exists … | **Now.** A CHOSEN limit ('w = 0', pure NPE spine), inert at the shipped 'spine_k = None' and reachable only by a sweep, which is what it exists for. |
| JUDGEMENT-CALLS.md:1715 | W | **Record.** **A CHOSEN LIMIT, not a derived one** (owner, 2026-08-28). 'w = k / (worth + k)' is '0/0' when a party has both records and 'worth = 0', … | **Record.** **A CHOSEN LIMIT, not a derived one** (owner, 2026-08-28). 'w = k / (worth + k)' is '0/0' when a party has both records and 'worth = 0', … |
| JUDGEMENT-CALLS.md:1805 | W | ### §F36 · 'PROJECTED_METRO_SHARE' — eight per-metro shares of the national vote, 2021 values — 🔴 | ### §F36 · 'PROJECTED_METRO_SHARE' — eight per-metro shares of the provincial-ballot vote, 2021 values — 🔴 |
| JUDGEMENT-CALLS.md:1976 | W | 2021, 2 against 4), not the ANC. Nationally, Laingsburg WC051 2021 is the only | 2021, 2 against 4), not the ANC. Nationally, Laingsburg WC051 2021 is the only ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:1997 |  | the national to the local election in 2016 and 2021, with 2021 counting for | the NPE to the local election in 2016 and 2021, with 2021 counting for ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2318 |  | ### §K1 · 'NATIONAL_ONLY_FLOOR' — 0.001 — 🟢 measured, owner's decision | ### §K1 · 'NATIONAL_ONLY_FLOOR' — 0.001 — 🟢 measured, owner's decision ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2326 | W | election that has not happened yet. Below 0.1% of the national vote, it is not. | election that has not happened yet. Below 0.1% of the provincial-ballot vote, it is not. |
| JUDGEMENT-CALLS.md:2330 | W | 'set(baseline) \| set(composition)' — *everyone* with a national vote — and it had | 'set(baseline) \| set(composition)' — *everyone* with a provincial-ballot vote — and it had |
| JUDGEMENT-CALLS.md:2334 | W | corrected here.** "The lowest preceding national share of any party that went on | corrected here.** "The lowest preceding provincial-ballot share of any party that went on |
| JUDGEMENT-CALLS.md:2336 |  | had a prior local record and is admitted regardless of any national floor. It | had a prior local record and is admitted regardless of any NPE floor. It ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2346 |  | \| prior-local AND national \| 189 \| 125 \| **66.1%** \| **89.73%** \| | \| prior-local AND NPE \| 189 \| 125 \| **66.1%** \| **89.73%** \| ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2348 |  | \| **national ONLY** \| **226** \| 30 \| **13.3%** \| **5.12%** \| | \| **NPE ONLY** \| **226** \| 30 \| **13.3%** \| **5.12%** \| ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2356 |  | national-only class is 226 candidates for 5.12%. | NPE only class is 226 candidates for 5.12%. ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2360 | W | at 12.2% nationally in Johannesburg. So the limit is on SIZE. Ordering the 226: | at 12.2% on the provincial ballot in Johannesburg. So the limit is on SIZE. Ordering the 226: ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2370 |  | national-only parties (11.51% → 11.64%, 10.13% → 10.93%) and that reasoning is | NPE only parties (11.51% → 11.64%, 10.13% → 10.93%) and that reasoning is ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2375 | W | \| preceding national share \| n \| median local/national \| mean \| max \| | \| preceding provincial-ballot share \| n \| median local/national \| mean \| max \| |
| JUDGEMENT-CALLS.md:2414 |  | BASIC_INCOME_GRANT_SA (0.078%) and eleven more of that size. 24 of 44 national | BASIC_INCOME_GRANT_SA (0.078%) and eleven more of that size. 24 of 44 NPE ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2418 | W | no national vote, no local record — is still invisible. | no provincial-ballot vote, no local record — is still invisible. |
| JUDGEMENT-CALLS.md:2431 |  | national-only class this floor argues about (150).** Averaging a quiet cycle with | NPE only class this floor argues about (150).** Averaging a quiet cycle with ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2440 | W | **1. It is not the NATIONAL share. It is this metro's share of the national | **1. It is not the NATIONAL share. It is this metro's share of the NPE ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2443 | W | at the national election, not nationally. That is the better quantity — locally | at the NPE, not nationally. That is the better quantity — locally |
| JUDGEMENT-CALLS.md:2444 | W | relevant — but the first draft of this entry said "national share" throughout | relevant — but the first draft of this entry said "provincial-ballot share" throughout |
| JUDGEMENT-CALLS.md:2455 | W | worst at: **locally concentrated, nationally negligible.** Two seats out of the | worst at: **locally concentrated, on the provincial ballot negligible.** Two seats out of the ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2471 |  | record; if 'national ONLY' stops being ~5% of the vote, or if the transfer ratio | record; if 'NPE ONLY' stops being ~5% of the vote, or if the transfer ratio ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2485 |  | **Why it exists.** §K1's first draft filtered only the national-only class and | **Why it exists.** §K1's first draft filtered only the NPE only class and ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2498 |  | **59% of the class removed at zero measured seat cost** — against the national | **59% of the class removed at zero measured seat cost** — against the NPE ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2590 | W | than the arrival record (a former mayor with a national profile) or far worse | than the arrival record (a former mayor with an NPE profile) or far worse ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:2777 | E | at least **0.5%** at the preceding NATIONAL election. | at least **0.5%** at the preceding NPE election. |
| JUDGEMENT-CALLS.md:2779 | W | **Why the national share and not the local one.** The local baseline of such a | **Why the provincial-ballot share and not the local one.** The local baseline of such a |
| JUDGEMENT-CALLS.md:2802 |  | **Why 0.5%.** Below it the list fills with the national tail: at 0.1% it would | **Why 0.5%.** Below it the list fills with the NPE tail: at 0.1% it would ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:3004 | W | record, whose named cases are COPE, EFF and MK, breakaways led by a national | record, whose named cases are COPE, EFF and MK, breakaways led by an NPE ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:3122 | W | with a preceding NATIONAL result never reaches 'arrival_rules' at all: | with a preceding PROVINCIAL-ballot result never reaches 'arrival_rules' at all: |
| JUDGEMENT-CALLS.md:3124 |  | \| party \| prior national (JHB) \| sized by \| | \| party \| prior NPE (JHB) \| sized by \| ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:3127 |  | \| **Agang** 2016 \| **0.52%** (NPE 2014) \| 'levels.spine', route *national only* \| | \| **Agang** 2016 \| **0.52%** (NPE 2014) \| 'levels.spine', route *NPE only* \| ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:3161 | W | preceding national result where it has one. | preceding provincial-ballot result where it has one. |
| JUDGEMENT-CALLS.md:3172 | W | Both were new parties with nationally famous founders. A factor of six hundred | Both were new parties with on the provincial ballot famous founders. A factor of six hundred ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:3225 |  | * **The national anchor, and rupture as its exception.** EFF kept 1.01–1.50× of | * **The NPE anchor, and rupture as its exception.** EFF kept 1.01–1.50× of ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:3226 | W | its national share across eight metros, GOOD 1.07, PA 1.49, the ID 0.86 — | its provincial-ballot share across eight metros, GOOD 1.07, PA 1.49, the ID 0.86 — |
| JUDGEMENT-CALLS.md:4000 | W | (the national baseline and every VD, then the preceding local PR shares), | (the NPE baseline and every VD, then the preceding local PR shares), |
| JUDGEMENT-CALLS.md:4015 | W | national record and no 2021 local one, so it takes GOOD's transfer on the | NPE record and no 2021 local one, so it takes GOOD's transfer on the |
| JUDGEMENT-CALLS.md:4016 | W | national route only; ActionSA takes Forum 4 Service Delivery's on both. | NPE route only; ActionSA takes Forum 4 Service Delivery's on both. |
| JUDGEMENT-CALLS.md:4660 | W | for ward swings, citywide swings and the national-to-local changes alike. | for ward swings, citywide swings and the NPE-to-local changes alike. |
| JUDGEMENT-CALLS.md:4672 | W | ### §R8 · a party with no ward record: its citywide share; new to local elections: its national share; neither: the newcomer caps — ⚖️ argued (O2: ow… | ### §R8 · a party with no ward record: its citywide share; new to local elections: its provincial-ballot share; neither: the newcomer caps — ⚖️ argue… |
| JUDGEMENT-CALLS.md:4679 | E | election but a vote at the preceding national election | election but a vote at the preceding NPE |
| JUDGEMENT-CALLS.md:4680 | W | ('Target.previous_npe'; 'build_make.npe_priors') takes its national share in | ('Target.previous_npe'; 'build_make.npe_priors') takes its provincial-ballot share in |
| JUDGEMENT-CALLS.md:4681 | W | the ward, joined the same way, or its citywide national share where it has | the ward, joined the same way, or its citywide provincial-ballot share where it has |
| JUDGEMENT-CALLS.md:4682 |  | none in the ward (kind 'national'). Its range is moved by the least and | none in the ward (kind 'NPE'). Its range is moved by the least and ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:4683 | W | greatest change from a national election to the next local election, per | greatest change from an NPE to the next local election, per |
| JUDGEMENT-CALLS.md:4686 | W | the national vote to under 'COLLAPSE_KEEP' of that) is left out of those | the provincial-ballot vote to under 'COLLAPSE_KEEP' of that) is left out of those |
| JUDGEMENT-CALLS.md:4689 |  | ward share taken by any party new to its city with no vote at the national | ward share taken by any party new to its city with no vote at the NPE ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:4693 | W | - A national file whose calendar template names an approximation | - An NPE file whose calendar template names an approximation |
| JUDGEMENT-CALLS.md:4703 | W | outside its national-prior range: that is the measured cost of O2 (SPEC-B2r2 | outside its NPE-prior range: that is the measured cost of O2 (SPEC-B2r2 ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:4708 | W | preceding local file takes its national prior, and deleted from the national | preceding local file takes its NPE prior, and deleted from the NPE ⟨check sense⟩ |
| JUDGEMENT-CALLS.md:4765 | W | allowance (§R9); a party new to local elections by its national share and the | allowance (§R9); a party new to local elections by its provincial-ballot share and the |
| JUDGEMENT-CALLS.md:4766 | W | national-to-local citywide changes (§R8); a party with neither, the newcomer | NPE-to-local citywide changes (§R8); a party with neither, the newcomer |
| JUDGEMENT-CALLS.md:5020 | W | six ward-only parties, UDM the one with a national record) and 0.08% at | six ward-only parties, UDM the one with an NPE record) and 0.08% at |
| MACHINERY.md:111 |  | **Why the fit is national.** Ecological inference identifies a group's rate only | **Why the fit is NPE.** Ecological inference identifies a group's rate only ⟨check sense⟩ |
| MACHINERY.md:116 | W | or Coloured supporters", which is false. The national fit supplies the shape, | or Coloured supporters", which is false. The NPE fit supplies the shape, |
| MACHINERY.md:214 | W | National → local retention. **410 observations at target 2026.** | NPE→local retention. **410 observations at target 2026.** |
| MACHINERY.md:255 | W | **'size' is the party's size now** — its national share for θ, its previous | **'size' is the party's size now** — its provincial-ballot share for θ, its previous |
| MACHINERY.md:307 | W | nat_level = national_share * exp(mu_theta)     6.268% x 0.804 -> 5.040% | nat_level = national_share * exp(mu_theta)     6.268% x 0.804 -> 5.040% ⟨check sense⟩ |
| MACHINERY.md:387 | W | \| **θ** national→local retention \| 'levels.theta_record' \| MEASURED, 8 metros, strictly pre-target \| **410** observations at 2026 (ρ: 292), as at… | \| **θ** NPE→local retention \| 'levels.theta_record' \| MEASURED, 8 metros, strictly pre-target \| **410** observations at 2026 (ρ: 292), as at 2026… |
| MACHINERY.md:400 | W | **The spine.** A party's level comes from BOTH its previous national result (× θ) | **The spine.** A party's level comes from BOTH its previous provincial-ballot result (× θ) |
| MACHINERY.md:404 | W | on the national route. Held out one metro at a time: RMSE(log) 0.236 against the | on the NPE route. Held out one metro at a time: RMSE(log) 0.236 against the |
| MACHINERY.md:405 | W | national spine's 0.275. | NPE spine's 0.275. |
| MACHINERY.md:462 | E | election 'pools.fit_city' fits and every national election after one, on that | election 'pools.fit_city' fits and every NPE after one, on that |
| MACHINERY.md:506 | E | line is not novelty; it is whether a **national election has already measured the | line is not novelty; it is whether a **NPE has already measured the |
| MACHINERY.md:511 | W | \| **First local election** \| has a national baseline, never faced an LGE \| **'levels.spine'**, like every other party with a national record — the… | \| **First local election** \| has an NPE baseline, never faced an LGE \| **'levels.spine'**, like every other party with an NPE record — the nationa… |
| MACHINERY.md:512 | W | \| **Arrival** \| no national vote at all \| 'pools.arrival_rules': the entrant GROUP is rescaled to the arrival-total record ('_arrival_total_prior'… | \| **Arrival** \| no provincial-ballot vote at all \| 'pools.arrival_rules': the entrant GROUP is rescaled to the arrival-total record ('_arrival_tot… |
| MACHINERY.md:549 | W | in the first class (12.2% of Johannesburg's 2024 national vote, seeded at 8.18%), | in the first class (12.2% of Johannesburg's 2024 provincial-ballot vote, seeded at 8.18%), |
| MACHINERY.md:550 | W | as are RISE and BOSA. ActionSA in 2021 was in the second (no 2019 national vote | as are RISE and BOSA. ActionSA in 2021 was in the second (no 2019 provincial-ballot vote |
| MACHINERY.md:564 | W | \| 'SPLINTER_PARENT_WEIGHT' = 0.35 (the DEFAULT) \| 'pools.py', read through 'splinter_parent_weight(rule, party)' \| MEASURED, 22 splinter-metro cas… | \| 'SPLINTER_PARENT_WEIGHT' = 0.35 (the DEFAULT) \| 'pools.py', read through 'splinter_parent_weight(rule, party)' \| MEASURED, 22 splinter-metro cas… |
| MACHINERY.md:681 | W | **A party with its own national record is fitted on it (owner, 2026-10-15).** | **A party with its own NPE record is fitted on it (owner, 2026-10-15).** |
| MACHINERY.md:684 | E | its own fit on the baseline national election ('target.previous_npe') when | its own fit on the baseline NPE ('target.previous_npe') when |
| MACHINERY.md:686 | W | splinter blend, else the city mix. 'pools.national_fits' is 'fit_city' on the | splinter blend, else the city mix. 'pools.national_fits' is 'fit_city' on the ⟨check sense⟩ |
| MACHINERY.md:687 | W | national result file: every party jointly, the national election's own | provincial-ballot result file: every party jointly, the NPE's own |
| MACHINERY.md:694 | E | gate: the national election precedes the target, so a backtest reads its own | gate: the NPE precedes the target, so a backtest reads its own |
| MACHINERY.md:696 |  | 'fitted_from_national' (election, rates, bounds, pools identified, any | 'fitted_from_national' (election, rates, bounds, pools identified, any ⟨check sense⟩ |
| MACHINERY.md:697 | W | 'weights' or 'parent_weight' the fit superseded) and 'national_fit_refused' | 'weights' or 'parent_weight' the fit superseded) and 'national_fit_refused' ⟨check sense⟩ |
| MACHINERY.md:698 | W | (a party with a national record placed by the lineage rule, with why); the | (a party with an NPE record placed by the lineage rule, with why); the |
| MACHINERY.md:699 | W | per-pool 'identified' list counts a national fit where it identifies. | per-pool 'identified' list counts an NPE fit where it identifies. |
| MACHINERY.md:720 |  | tilt and input, the heavier-tails draw, the IFP pool, ActionSA on the national | tilt and input, the heavier-tails draw, the IFP pool, ActionSA on the NPE ⟨check sense⟩ |
| MACHINERY.md:1262 | W | model's level and its by-election level, its by-election level first capped by θ's band where the party has a national share, before the shrink; a pa… | model's level and its by-election level, its by-election level first capped by θ's band where the party has a provincial-ballot share, before the shr… |
| MACHINERY.md:1272 | W | record before 2024, at the party's 2019 national share); the residual | record before 2024, at the party's 2019 provincial-ballot share); the residual |
| MACHINERY.md:1320 | W | inheritance; one with a national record is fitted on it. | inheritance; one with an NPE record is fitted on it. |
| MACHINERY.md:1396 | E | **anchored** when it took votes at the preceding national election in the city | **anchored** when it took votes at the preceding NPE in the city |
| MACHINERY.md:1397 |  | ('_baseline_before_seeds'), so its centre is the spine's "national only (first | ('_baseline_before_seeds'), so its centre is the spine's "NPE only (first ⟨check sense⟩ |
| MACHINERY.md:1398 | W | local election)" level, its own national result through θ (COPE 2011, EFF | local election)" level, its own provincial-ballot result through θ (COPE 2011, EFF |
| MACHINERY.md:1399 | W | 2016, MK 2026); **unanchored** when it has no national result and its centre | 2016, MK 2026); **unanchored** when it has no provincial-ballot result and its centre |
| MACHINERY.md:1401 |  | seeds and labels a seeded arrival "national only" as well, which is why the | seeds and labels a seeded arrival "NPE only" as well, which is why the ⟨check sense⟩ |
| MACHINERY.md:1494 | W | local share against its national one — so making the θ layer reproduce it counts | local share against its NPE one — so making the θ layer reproduce it counts |
| MACHINERY.md:1513 | W | > \| national size \| measured conditional sd \| 95% CI \| what the model uses \| | > \| NPE size \| measured conditional sd \| 95% CI \| what the model uses \| |
| MACHINERY.md:1530 | W | \| national size \| measured conditional sd \| 95% CI \| what the model uses \| | \| NPE size \| measured conditional sd \| 95% CI \| what the model uses \| |
| MACHINERY.md:2117 |  | \| '20_spine' \| per party: the route taken, what the national and local routes each said, the blend weight, and what its own θ record was worth \| | \| '20_spine' \| per party: the route taken, what the NPE and local routes each said, the blend weight, and what its own θ record was worth \| ⟨check sense⟩ |
| MACHINERY.md:2762 | W | party new to local elections its national share ('npe_priors') and the | party new to local elections its provincial-ballot share ('npe_priors') and the |
| MACHINERY.md:2763 | W | national-to-local changes; a party with neither the newcomer cap | NPE-to-local changes; a party with neither the newcomer cap |
| MACHINERY.md:2834 | W | share dict: RISE, with a 2024 national share and no 2021 local one, receives | share dict: RISE, with a 2024 provincial-ballot share and no 2021 local one, receives |
| MACHINERY.md:2835 | W | GOOD's national share and not its local one, so its spine route stays | GOOD's provincial-ballot share and not its local one, so its spine route stays |
| MACHINERY.md:2836 |  | national-only. | NPE only. ⟨check sense⟩ |
| MACHINERY.md:2841 | W | * 'montecarlo.run_model', on the national baseline and every VD's shares, | * 'montecarlo.run_model', on the NPE baseline and every VD's shares, |
| MACHINERY.md:3115 |  | ## Placing a party with no national geography (2026-10-15) | ## Placing a party with no NPE geography (2026-10-15) ⟨check sense⟩ |
| POLLING.md:57 | W | **The conversion from a national number to a metro one is the whole problem, and | **The conversion from an NPE number to a metro one is the whole problem, and ⟨check sense⟩ |
| POOLS-REEMIT-QUEUE.md:280 | W | \| 41 \| **A party with its own national record is fitted on it (owner, 2026-10-15, "option A"; MODEL-LOG §1.307; JUDGEMENT-CALLS §F6, §SJ1).** 'pool… | \| 41 \| **A party with its own NPE record is fitted on it (owner, 2026-10-15, "option A"; MODEL-LOG §1.307; JUDGEMENT-CALLS §F6, §SJ1).** 'pools.pla… |
| POOLS-REEMIT-QUEUE.md:283 | T | \| 27 \| ⛔ **TWO CONFIRMED RENAMES, AND THEY ARE NOT NUMBER-NEUTRAL — MEASURED, NOT ASSUMED.** The owner confirmed 2026-09-16: 'CAPE COLOURED CONGRES… | \| 27 \| ⛔ **TWO CONFIRMED RENAMES, AND THEY ARE NOT NUMBER-NEUTRAL — MEASURED, NOT ASSUMED.** The owner confirmed 2026-09-16: 'CAPE COLOURED CONGRES… ⟨check sense⟩ |
| POOLS-REEMIT-QUEUE.md:593 | W | \| 11 \| ⛔ **LANDED 2026-09-03, WITH ENTRY 4, UNDER 'prereg/2026-09-03-arrival-record-widening.md' P2. THE ARRIVAL GROUP BUDGET IS MEASURED OVER A WI… | \| 11 \| ⛔ **LANDED 2026-09-03, WITH ENTRY 4, UNDER 'prereg/2026-09-03-arrival-record-widening.md' P2. THE ARRIVAL GROUP BUDGET IS MEASURED OVER A WI… |
| POOLS-REEMIT-QUEUE.md:595 | W | \| 17 \| **The five definitions of "an arrival" are named, and one of them was documented backwards.** 'pools.ARRIVAL_DEFINITIONS' registers all five… | \| 17 \| **The five definitions of "an arrival" are named, and one of them was documented backwards.** 'pools.ARRIVAL_DEFINITIONS' registers all five… |
| PUBLISHING-BACKLOG.md:145 | W | \| 'spine_k' \| 1.0 \| how much a party's own local record outweighs the national spine \| | \| 'spine_k' \| 1.0 \| how much a party's own local record outweighs the NPE spine \| |
| PUBLISHING-BACKLOG.md:533 | W | the election can be ('dirichlet_scale'), local record vs national mood | the election can be ('dirichlet_scale'), local record vs NPE mood ⟨check sense⟩ |
| SOURCES.md:31 |  | \| Year \| National \| Provincial \| | \| Year \| NPE \| Provincial \| ⟨check sense⟩ |
| SOURCES.md:67 |  | \| 2014 \| same pattern **404s** — 2014 is published on the other host instead: 'www.elections.org.za/content/Elections/Downloadable-results/2014-Nat… | \| 2014 \| same pattern **404s** — 2014 is published on the other host instead: 'www.elections.org.za/content/Elections/Downloadable-results/2014-NPE… ⟨check sense⟩ |
| SOURCES.md:405 | W | Why the per-metro version matters more than the national one: the register | Why the per-metro version matters more than the NPE one: the register |
| SOURCES.md:410 |  | an actual 9.28%. A single national defector share is one number per split and | an actual 9.28%. A single NPE defector share is one number per split and ⟨check sense⟩ |
| SOURCES.md:446 |  | national among them: [] | NPE among them: [] ⟨check sense⟩ |
| SOURCES.md:450 |  | and a party-share breakdown, entered as 'scope = "national"'. Note that | and a party-share breakdown, entered as 'scope = "NPE"'. Note that ⟨check sense⟩ |
| SOURCES.md:566 |  | ward geodatabases were already national. | ward geodatabases were already NPE. ⟨check sense⟩ |
| SOURCES.md:567 |  | * **Census 2022 ward product** is national (all ~4,470 wards), so no further | * **Census 2022 ward product** is NPE (all ~4,470 wards), so no further ⟨check sense⟩ |
| SOURCES.md:640 |  | \| 1–2. Party performance \| ANC, DA, EFF, FF+ vote share, plus ANC-vs-DA, ANC-vs-EFF, DA-vs-FF+ \| national + 8 metros \| | \| 1–2. Party performance \| ANC, DA, EFF, FF+ vote share, plus ANC-vs-DA, ANC-vs-EFF, DA-vs-FF+ \| NPE + 8 metros \| ⟨check sense⟩ |
| SOURCES.md:641 | T | \| 3–4. Turnout \| overall, and ANC/DA turnout differentials \| national + metros \| | \| 3–4. Turnout \| overall, and ANC/DA turnout differentials \| NPE + metros \| ⟨check sense⟩ |
| SOURCES.md:644 | T | \| 8.1 Heat maps, national \| ANC, DA, IFP, FF+, EFF, GOOD, PA, ASA, MK, other, leading party, second party, turnout \| municipality **and ward** \| | \| 8.1 Heat maps, NPE \| ANC, DA, IFP, FF+, EFF, GOOD, PA, ASA, MK, other, leading party, second party, turnout \| municipality **and ward** \| ⟨check sense⟩ |
| TODO.md:160 | W | Independent Congress — and 52 council seats nationally. In the backtest the | Independent Congress — and 52 council seats on the provincial ballot. In the backtest the ⟨check sense⟩ |
| cities/joburg.toml:88 | W | # Plan §3.5 sanity ranges on raw national-to-local retention ratios. | # Plan §3.5 sanity ranges on raw NPE-to-local retention ratios. |
| config/dimensions.toml:61 | W | # nationally against 6,673 in Johannesburg alone — which then made the vote | # on the provincial ballot against 6,673 in Johannesburg alone — which then made the vote ⟨check sense⟩ |
| judgements/ekurhuleni-2021.toml:119 |  | [party.THE_NATIONALS_OF_SOUTH_AFRICA] | [party.THE_NATIONALS_OF_SOUTH_AFRICA] ⟨check sense⟩ |
| judgements/joburg-2016.toml:49 |  | [party.FRONT_NASIONAAL_FRONT_NATIONAL] | [party.FRONT_NASIONAAL_FRONT_NATIONAL] ⟨check sense⟩ |
| judgements/joburg-2026.toml:247 |  | # councillor lists only, the site's own search returns just the national | # councillor lists only, the site's own search returns just the NPE ⟨check sense⟩ |
| judgements/joburg-2026.toml:315 |  | "NATIONAL COLOURED CONGRESS", | "NATIONAL COLOURED CONGRESS", ⟨check sense⟩ |
| judgements/joburg-2026.toml:407 |  | "NATIONAL COLOURED CONGRESS", | "NATIONAL COLOURED CONGRESS", ⟨check sense⟩ |
| judgements/joburg-2026.toml:488 |  | "NATIONAL COLOURED CONGRESS" = ["79800001", "79800002", "79800003", "79800004", "79800005", "79800006", "79800007", "79800008", "79800009", "79800010… | "NATIONAL COLOURED CONGRESS" = ["79800001", "79800002", "79800003", "79800004", "79800005", "79800006", "79800007", "79800008", "79800009", "79800010… ⟨check sense⟩ |
| judgements/tshwane-2026.toml:225 |  | "NATIONAL COLOURED CONGRESS", | "NATIONAL COLOURED CONGRESS", ⟨check sense⟩ |
| judgements/tshwane-2026.toml:303 |  | "NATIONAL COLOURED CONGRESS", | "NATIONAL COLOURED CONGRESS", ⟨check sense⟩ |
| judgements/tshwane-2026.toml:382 |  | "NATIONAL COLOURED CONGRESS" = ["79900001", "79900002", "79900003", "79900004", "79900005", "79900006", "79900007", "79900008", "79900009", "79900010… | "NATIONAL COLOURED CONGRESS" = ["79900001", "79900002", "79900003", "79900004", "79900005", "79900006", "79900007", "79900008", "79900009", "79900010… ⟨check sense⟩ |
| skills/forecast-stage-estimation/SKILL.md:39 | W | ## 1. '10_theta_prior' — how a national vote becomes a local one | ## 1. '10_theta_prior' — how a provincial-ballot vote becomes a local one |
| skills/forecast-stage-estimation/SKILL.md:42 | E | share at the national election before it. 'levels.theta_record' collects one | share at the NPE before it. 'levels.theta_record' collects one |
| skills/forecast-stage-estimation/SKILL.md:66 | W | no national baseline is here, and a party with a baseline and no record is here | no NPE baseline is here, and a party with a baseline and no record is here |
| skills/forecast-stage-estimation/SKILL.md:75 |  | 11 of 22 at 2011) and **every one of them is a party with no national | 11 of 22 at 2011) and **every one of them is a party with no NPE ⟨check sense⟩ |
| skills/forecast-stage-estimation/SKILL.md:99 | W | * the **national route** — its share at the last NPE, times 'exp(µ_θ)'; | * the **NPE route** — its share at the last NPE, times 'exp(µ_θ)'; |
| skills/forecast-stage-estimation/SKILL.md:106 |  | level = local**w · national**(1-w),   w = k / (worth + k),   SPINE_K = 1.0 | level = local**w · NPE**(1-w),   w = k / (worth + k),   SPINE_K = 1.0 ⟨check sense⟩ |
| skills/forecast-stage-estimation/SKILL.md:109 | W | a long retention history sits on the national spine, a party whose θ is nothing | a long retention history sits on the NPE spine, a party whose θ is nothing |
| skills/forecast-stage-estimation/SKILL.md:118 | W | \| 'detail[p].national' \| float \| ⚠ **not** the party's national vote share — it is that share **already through θ**. A level. \| | \| 'detail[p].national' \| float \| ⚠ **not** the party's provincial-ballot share — it is that share **already through θ**. A level. \| |
| skills/forecast-stage-estimation/SKILL.md:122 | W | \| 'detail[p].route' \| str \| 'blend' / 'blend at full local (no θ evidence)' / 'blend at full national (k=0)' / 'national only (first local electio… | \| 'detail[p].route' \| str \| 'blend' / 'blend at full local (no θ evidence)' / 'blend at full NPE (k=0)' / 'NPE only (first local election)' / 'loc… |
| skills/forecast-stage-estimation/SKILL.md:126 | W | \| 'absorption.blend' \| account \| 'disagreement' = Σ\\|log(local) − log(national)\\|; 'moved_from_national' = Σ w·gap (the mass the LOCAL route won… | \| 'absorption.blend' \| account \| 'disagreement' = Σ\\|log(local) − log(NPE)\\|; 'moved_from_national' = Σ w·gap (the mass the LOCAL route won); 's… ⟨check sense⟩ |
| skills/forecast-stage-estimation/SKILL.md:144 | W | an attractor and "changing the national route did not move the forecast" is | an attractor and "changing the NPE route did not move the forecast" is |
| skills/forecast-stage-estimation/SKILL.md:147 | W | national route wins 91% of the disagreement. | NPE route wins 91% of the disagreement. |
| skills/forecast-stage-estimation/SKILL.md:225 |  | \| 'level == local**w · national**(1-w)' \| the whole arithmetic of the spine, checked against the three numbers the row reports. \| | \| 'level == local**w · NPE**(1-w)' \| the whole arithmetic of the spine, checked against the three numbers the row reports. \| ⟨check sense⟩ |
| skills/forecast-stage-estimation/SKILL.md:235 |  | \| 'moved_from_national + moved_from_local == disagreement'; 'share_local' is that quotient \| the block is write-only in the model, so nothing else … | \| 'moved_from_national + moved_from_local == disagreement'; 'share_local' is that quotient \| the block is write-only in the model, so nothing else … ⟨check sense⟩ |

### Appendix C-gen. Generated documents — fix at the generator, never by hand (24 lines)

| file:line | sense | current words | proposed words |
|---|---|---|---|
| JUDGEMENT-SHEET.md:110 | W | \| 'NATIONAL_ONLY_FLOOR' \| 0.001 \| module constant \| module constant \| no \| The national share below which a party with no local record is NOT a… | \| 'NATIONAL_ONLY_FLOOR' \| 0.001 \| module constant \| module constant \| no \| The provincial-ballot share below which a party with no local record… |
| JUDGEMENT-SHEET.md:111 | W | \| 'PRIOR_LOCAL_FLOOR' \| 0.001 \| module constant \| module constant \| no \| The prior-LOCAL share below which a party with no national vote is not… | \| 'PRIOR_LOCAL_FLOOR' \| 0.001 \| module constant \| module constant \| no \| The prior-LOCAL share below which a party with no provincial-ballot vo… |
| JUDGEMENT-SHEET.md:131 | W | \| 'PROJECTED_METRO_SHARE' \| eight per-metro shares of the national vote, 2021 values \| module constant \| module constant \| no \| The last observ… | \| 'PROJECTED_METRO_SHARE' \| eight per-metro shares of the provincial-ballot vote, 2021 values \| module constant \| module constant \| no \| The la… |
| JUDGEMENT-SHEET.md:146 | W | \| 'spine_k = 0' on a party with no θ evidence \| 'w_local = 0.0' \| unlinked \| not linked to a scenario key or module constant \| no \| A CHOSEN li… | \| 'spine_k = 0' on a party with no θ evidence \| 'w_local = 0.0' \| unlinked \| not linked to a scenario key or module constant \| no \| A CHOSEN li… |
| JUDGEMENT-SHEET.md:148 | W | \| 'SPLINTER_PARENT_WEIGHT' \| 0.35 \| module constant \| module constant \| no \| The DEFAULT 0.35, measured over 22 splinter-metro cases (EFF 0.89,… | \| 'SPLINTER_PARENT_WEIGHT' \| 0.35 \| module constant \| module constant \| no \| The DEFAULT 0.35, measured over 22 splinter-metro cases (EFF 0.89,… |
| JUDGEMENT-SHEET.md:218 | W | \| the size the shrink target is evaluated at \| 'levels._shrink_one' (via '_shrunk', 'theta_prior') \| The party's current size on the route (nation… | \| the size the shrink target is evaluated at \| 'levels._shrink_one' (via '_shrunk', 'theta_prior') \| The party's current size on the route (provin… |
| MODEL-INDEX.md:790 |  | \| 'pools.NATIONAL_ONLY_FLOOR' \| float 0.001 \| NO \| NO \| yes \| -- \| | \| 'pools.NATIONAL_ONLY_FLOOR' \| float 0.001 \| NO \| NO \| yes \| -- \| ⟨check sense⟩ |
| MODEL-INDEX.md:805 | W | \| 'pools.ARRIVAL_DEFINITIONS' \| {'ARRIVED_VS_NATIONAL': ArrivalDefinition(predicate='local share > 0 and \| NO \| NO \| NO \| 'model_index' \| | \| 'pools.ARRIVAL_DEFINITIONS' \| {'ARRIVED_VS_NATIONAL': ArrivalDefinition(predicate='local share > 0 and \| NO \| NO \| NO \| 'model_index' \| ⟨check sense⟩ |
| MODEL-INDEX.md:1044 | W | \| 'ARRIVED_VS_LOCAL_EXCLUDING_SPLITS_WITH_REACH' \| 'pools.ARRIVAL_DEFINITIONS' \| -- \| predicate='preceding-LGE share <= 1e-4 < share, party not i… | \| 'ARRIVED_VS_LOCAL_EXCLUDING_SPLITS_WITH_REACH' \| 'pools.ARRIVAL_DEFINITIONS' \| -- \| predicate='preceding-LGE share <= 1e-4 < share, party not i… |
| MODEL-INDEX.md:1045 | W | \| 'ARRIVED_VS_NATIONAL' \| 'pools.ARRIVAL_DEFINITIONS' \| -- \| predicate='local share > 0 and preceding-NPE share <= 0, party != IND'; population='… | \| 'ARRIVED_VS_NATIONAL' \| 'pools.ARRIVAL_DEFINITIONS' \| -- \| predicate='local share > 0 and preceding-NPE share <= 0, party != IND'; population='… ⟨check sense⟩ |
| MODEL-INDEX.md:1181 | W | \| 'levels.theta_record' \| model+measurement \| Every observed national-to-local retention ratio before the target. \| 'bye_value', 'montecarlo', 't… | \| 'levels.theta_record' \| model+measurement \| Every observed NPE-to-local retention ratio before the target. \| 'bye_value', 'montecarlo', 'tests/… |
| MODEL-INDEX.md:1204 |  | \| 'montecarlo.place_by_pool' \| model+measurement \| Put each party with no national geography where its pools live. \| 'tests/test_pool_placement' … | \| 'montecarlo.place_by_pool' \| model+measurement \| Put each party with no NPE geography where its pools live. \| 'tests/test_pool_placement' \| ⟨check sense⟩ |
| MODEL-INDEX.md:1363 | W | \| 'pools.national_fits' \| model+measurement \| Every party fitted on the target's baseline NATIONAL election, by ward. \| 'tests/test_national_reco… | \| 'pools.national_fits' \| model+measurement \| Every party fitted on the target's baseline NPE election, by ward. \| 'tests/test_national_record_fi… |
| SITE-TEXT.md:1239 | W | ## <span data-asof="2026-10-21">"Nationally in 2024"</span> — published 26 September 2026, corrected 21 October 2026 | ## <span data-asof="2026-10-21">"Nationally in 2024"</span> — published 26 September 2026, corrected 21 October 2026 ⟨check sense⟩ |
| SITE-TEXT.md:1358 | E | **What is right.** The ANC bloc lost 587,000 votes between the 2019 national election and the 2021 local election, as the article says.</span> | **What is right.** The ANC bloc lost 587,000 votes between the 2019 NPE and the 2021 local election, as the article says.</span> |
| SITE-TEXT.md:1683 | W | nationally. This Model measures the gap for each party from its own | on the provincial ballot. This Model measures the gap for each party from its own ⟨check sense⟩ |
| SITE-TEXT.md:1684 | W | national-to-local transitions on record. A party's starting level blends its | NPE-to-local transitions on record. A party's starting level blends its |
| SITE-TEXT.md:1685 | W | national result, converted down to local, with its last local result: the | provincial-ballot result, converted down to local, with its last local result: the |
| SITE-TEXT.md:1688 | E | {{hist_asa_npe_2024}} in the city in the 2024 national election. It has no | {{hist_asa_npe_2024}} in the city in the 2024 NPE. It has no |
| SITE-TEXT.md:1689 | W | national-to-local gap on record, so its starting level comes from its local | NPE-to-local gap on record, so its starting level comes from its local |
| SITE-TEXT.md:1734 | W | splits took. A split that has stood in a national election since, as MK did | splits took. A split that has stood in an NPE since, as MK did |
| SITE-TEXT.md:1757 | W | least as well known nationally in 2019 as Julius Malema was in 2014; her party | least as well known on the 2019 provincial ballot as Julius Malema was in 2014; her party |
| SITE-TEXT.md:2555 | W | to underperform its national result. The simulation's internals quietly | to underperform its provincial-ballot result. The simulation's internals quietly |
| SITE-TEXT.md:3050 | E | the ANC bloc shed between the 2019 national election and the 2021 local | the ANC bloc shed between the 2019 NPE and the 2021 local |

### Appendix D. Do not change — country-wide or genuinely national-ballot senses (C, N) (228 lines)

| file:line | sense | current words | proposed words |
|---|---|---|---|
| src/archive.py:35 | C | "data/raw/elections/_source/lge2016_national": "elections.org.za Downloadable-results, 2016 LGE complete VD-level (zipped CSV)", | **keep** (correct) |
| src/archive.py:80 | C | # The pre-2011 national bulk export: one zipped national CSV per election, | **keep** (correct) |
| src/archive.py:83 | C | "data/raw/elections/_source/": "elections.org.za/content/uploadedfiles/{YYYY}%20{NPE\|LGE}.zip — unlinked national bulk export, archived 2026-08-09/1… | **keep** (correct) |
| src/backtest.py:353 | N | "an arrival's level taken from a national poll, converted by the share " | **keep** (correct) |
| src/benchmarks.py:440 | C | """The last local election, shifted by the national swing that bracketed it. | **keep** (correct) |
| src/benchmarks.py:448 | N | a poll. Neither exists for this problem: there is no national vote on local | **keep** (correct) |
| src/benchmarks.py:482 | C | # How much of the national swing ''blended-swing'' carries. **MEASURED, and the | **keep** (correct) |
| src/benchmarks.py:884 | C | the 2016 LGE, the national swing moves it to 0.1448%, and it finishes 17th | **keep** (correct) |
| src/build_make.py:838 | C | elif kind == "national": | **keep** (correct) |
| src/build_make.py:878 | C | elif kind == "national": | **keep** (correct) |
| src/build_make.py:987 | C | "national": {k: national[k] for k in ("file", "year")}}, | **keep** (correct) |
| src/bye_value.py:14 | C | By-elections are local ward contests; the outcome is a national-provincial | **keep** (correct) |
| src/bye_value.py:104 | C | "the 2024 provincial ballot, a national-provincial list ballot.") | **keep** (correct) |
| src/byelections.py:83 | C | #: The national by-election file the item-19 test reads (all eight metros). | **keep** (correct) |
| src/cityconfig.py:70 | C | # South Africa votes on one nationwide day, so the calendar is a national fact | **keep** (correct) |
| src/cityconfig.py:305 | C | This is the national calendar, not what is on disk: the pre-2011 | **keep** (correct) |
| src/compare_history.py:149 | C | the national swing that bracketed the target, then the only one that expresses a | **keep** (correct) |
| src/compare_history.py:1041 | C | national swing, so a within-cycle figure is optimistic too — rule 11. | **keep** (correct) |
| src/compare_history.py:2653 | C | "draw, a pool structure and a national swing, so the nominal test's " | **keep** (correct) |
| src/compare_history.py:2752 | C | f"share a turnout draw, a pool structure and a national swing, so a " | **keep** (correct) |
| src/compare_history.py:3348 | C | f"a single metro. Metros inside one cycle share a national swing, " | **keep** (correct) |
| src/compare_history.py:3355 | C | f"Metros inside one cycle share a national swing, and this panel is " | **keep** (correct) |
| src/compare_history.py:3361 | C | f"Metros inside one cycle share a national swing, so {len(results)} " | **keep** (correct) |
| src/compare_history.py:3969 | N | #   * a non-scalar — 'DEFAULTS', 'PLAN_BOUNDS', 'NATIONAL_VOTES'. A sweep of a | **keep** (correct) |
| src/contested_area.py:3 | N | 'polling.metro_estimate' converts a national poll share into a metro one by | **keep** (correct) |
| src/contested_area.py:4 | N | dividing by the share of the national vote sitting in the municipalities the | **keep** (correct) |
| src/contested_area.py:9 | N | raw national share    contested-area adjusted | **keep** (correct) |
| src/contested_area.py:21 | N | election while holding no share of that metro's vote at the preceding national | **keep** (correct) |
| src/contested_area.py:54 | N | **national** vote. Verified by computing both:: | **keep** (correct) |
| src/contested_area.py:56 | N | 2016   raw vs national total 2.504    raw vs eight-metro total 1.609 | **keep** (correct) |
| src/contested_area.py:57 | N | 2021   raw vs national total 1.995    raw vs eight-metro total 1.228 | **keep** (correct) |
| src/contested_area.py:66 | N | archive as (party's votes across the metros it stood in) / (national vote), and | **keep** (correct) |
| src/contested_area.py:67 | N | ''s'' is (votes cast in those metros) / (national vote). **The national figure | **keep** (correct) |
| src/contested_area.py:73 | N | metro archive. The poll never appears, and neither does 'NATIONAL_VOTES'. | **keep** (correct) |
| src/contested_area.py:77 | N | **not the CONVERSION half** (a poll's national share divided by a roll-derived | **keep** (correct) |
| src/contested_area.py:104 | N | # (local election, the national election whose result decides who is an arrival) | **keep** (correct) |
| src/contested_area.py:140 | N | lines.append(f"{'':>6} {'n':>5} {'raw(8-metro)':>13} {'raw(national)':>14} " | **keep** (correct) |
| src/contested_area.py:145 | N | national = polling.NATIONAL_VOTES[lge] | **keep** (correct) |
| src/contested_area.py:157 | N | raw_n.append(abs(math.log((total / national) / actual))) | **keep** (correct) |
| src/fetch_byelections.py:13 | C | MapsJason/{eeid}/EEID{eeid}BigMapsNational.js | **keep** (correct) |
| src/fetch_byelections.py:14 | C | that date's national summary -- used only to discover which provinces | **keep** (correct) |
| src/fetch_byelections.py:101 | C | payload = _get_json(f"{DASH}/{eeid}/EEID{eeid}BigMapsNational.js") | **keep** (correct) |
| src/fold.py:1 | C | """Backtest a national/provincial baseline against a local-government target (plan §4). | **keep** (correct) |
| src/fold.py:754 | C | # A fold exists nationally; its FILES exist per city. Only Johannesburg has | **keep** (correct) |
| src/group_share_record.py:123 | C | """One national election on a fitted local election's wards. | **keep** (correct) |
| src/ingest_lge.py:5 | C | (id 1091 = 2021, 402 = 2016), which unlike the national/provincial exports are | **keep** (correct) |
| src/ingest_npe.py:1 | C | """Ingest IEC national/provincial election bulk result files to a JHB VD-level subset. | **keep** (correct) |
| src/ingest_npe.py:18 | C | quoted, covers the national and provincial ballots in one file, and carries the | **keep** (correct) |
| src/ingest_npe.py:181 | C | parser.add_argument("source", type=Path, help="unzipped national CSV") | **keep** (correct) |
| src/levels.py:61 | C | a local one, which is the right spine for a nationally-organised party and the | **keep** (correct) |
| src/levels.py:100 | N | years stale at polling day where the national is two. Each route is corrected by | **keep** (correct) |
| src/levels.py:211 | C | # Every metro with a VD-level archive. The retention record is a national fact | **keep** (correct) |
| src/levels.py:1741 | C | blend = {"n": 0, "disagreement": 0.0, "moved_from_national": 0.0, | **keep** (correct) |
| src/levels.py:1743 | C | "at_full_national": 0, "nonfinite": 0} | **keep** (correct) |
| src/levels.py:1837 | C | "national": nat_level, "local": loc_level} | **keep** (correct) |
| src/montecarlo.py:220 | N | # ones and they answer different questions: "arrivals" is a national poll | **keep** (correct) |
| src/montecarlo.py:2236 | N | # declared. NATIONAL_VOTES (2016, 2021) and PROJECTED_METRO_SHARE (2026, | **keep** (correct) |
| src/montecarlo.py:2238 | N | # national-poll-to-metro denominator. | **keep** (correct) |
| src/montecarlo.py:2244 | N | "POLL_DEFF_STANDALONE", "NATIONAL_VOTES", | **keep** (correct) |
| src/montecarlo.py:3076 | N | # exclusive at every target that exists. 'national_polls' | **keep** (correct) |
| src/montecarlo.py:3128 | N | # 'national_polls' returns nothing at 2026 and the only 2021 candidate, | **keep** (correct) |
| src/montecarlo.py:7073 | N | # The number is a national poll share divided by the share of the national | **keep** (correct) |
| src/montecarlo.py:7087 | N | _usable = (_polling.national_polls(target, min_n=_min_n) | **keep** (correct) |
| src/plausibility.py:104 | C | # Driven by one national swing per cycle, so their event p-values are | **keep** (correct) |
| src/polling.py:1 | N | """Polls, filtered by date and converted from national numbers to metro ones. | **keep** (correct) |
| src/polling.py:15 | N | Published South African polls are NATIONAL and this model forecasts a metro. The | **keep** (correct) |
| src/polling.py:27 | N | raw national share    contested-area adjusted | **keep** (correct) |
| src/polling.py:41 | N | eight-metro aggregate, the adjusted column runs through the national one. | **keep** (correct) |
| src/polling.py:42 | N | Against a consistent national denominator raw is 2.504 and 1.995. So part of | **keep** (correct) |
| src/polling.py:47 | N | does ''NATIONAL_VOTES''. This validates the geographic half of the mechanism, | **keep** (correct) |
| src/polling.py:58 | N | 1.5% national — the conversion gives about 6.3% wherever ActionSA stood:: | **keep** (correct) |
| src/polling.py:167 | N | # A SUBSAMPLE IS NOT A POLL. A ~500-person metro cut of a national sample | **keep** (correct) |
| src/polling.py:168 | N | # carries the parent design effect — its weights were built for the national | **keep** (correct) |
| src/polling.py:173 | N | POLL_DEFF_SUBSAMPLE = 1.6         # DECLARED — a metro cut of a national sample | **keep** (correct) |
| src/polling.py:327 | N | ''n_basis'': a metro cut of a national sample carries the parent design's | **keep** (correct) |
| src/polling.py:474 | N | # Registered voters nationally, per local election. Needed as the denominator of | **keep** (correct) |
| src/polling.py:482 | N | NATIONAL_VOTES = { | **keep** (correct) |
| src/polling.py:488 | N | # instead, and why a national total is not what is missing. | **keep** (correct) |
| src/polling.py:495 | N | # contests by the votes cast nationally. At a past target both come from the | **keep** (correct) |
| src/polling.py:497 | N | # returns '{}' because no 2026 result file exists, and 'NATIONAL_VOTES' has no | **keep** (correct) |
| src/polling.py:501 | N | # §1.65 recorded that and asked for a 2026 'NATIONAL_VOTES' entry. That would | **keep** (correct) |
| src/polling.py:505 | N | # What IS projectable is the ratio itself. Each metro's share of the national | **keep** (correct) |
| src/polling.py:578 | N | SCOPES = frozenset({"national", "metro", "metro-aggregate", "province"}) | **keep** (correct) |
| src/polling.py:631 | N | "path takes 'metro' and the arrivals path takes 'national', so " | **keep** (correct) |
| src/polling.py:736 | N | # A POLL MUST NAME THE CITY IT IS A READING OF, and only a national | **keep** (correct) |
| src/polling.py:745 | N | if scope != "national" and not poll.get("city"): | **keep** (correct) |
| src/polling.py:748 | N | f"national poll may omit one")) | **keep** (correct) |
| src/polling.py:783 | N | def national_polls(target: cityconfig.Target, polls: list[dict] \| None = None, | **keep** (correct) |
| src/polling.py:787 | N | if q.get("scope") == "national"] | **keep** (correct) |
| src/polling.py:1002 | N | """What fraction of the national roll sits in the municipalities listed. | **keep** (correct) |
| src/polling.py:1012 | N | national = NATIONAL_VOTES.get(str(year)) | **keep** (correct) |
| src/polling.py:1013 | N | if not roll or not national: | **keep** (correct) |
| src/polling.py:1016 | N | # is the whole ratio at once and needs no national total. | **keep** (correct) |
| src/polling.py:1020 | N | return (held / national) if held > 0 else None | **keep** (correct) |
| src/polling.py:1043 | N | """A national poll number converted to a share of each contested metro. | **keep** (correct) |
| src/polling.py:1053 | N | if share is None or poll.get("scope") != "national": | **keep** (correct) |
| src/polling.py:1059 | N | "national": float(share), "poll": poll.get("id"), | **keep** (correct) |
| src/polling.py:1061 | N | f"{share:.1%} national, contesting municipalities holding " | **keep** (correct) |
| src/pools.py:2065 | C | # this at national scale (Free Democrats 111 votes, Eastern Cape Movement | **keep** (correct) |
| src/pools.py:3620 | C | "ARRIVED_VS_NATIONAL": ArrivalDefinition( | **keep** (correct) |
| src/pools.py:4322 | N | # a national poll speaks to. | **keep** (correct) |
| src/pools.py:5258 | N | # party polled at the preceding national election so a human sizing it has the | **keep** (correct) |
| src/pools.py:5286 | N | "baseline_share": "INFORMATIONAL: what it polled at the preceding national " | **keep** (correct) |
| src/pools.py:5939 | N | f"{PRIOR_LOCAL_FLOOR:.1%} and polled nothing nationally, so they " | **keep** (correct) |
| src/pools.py:6135 | N | # party 'local_thin' removes, because polling nothing nationally is what | **keep** (correct) |
| src/pools.py:6192 | C | # exists nationally and has no local lineage is exactly the case worth a | **keep** (correct) |
| src/score.py:700 | C | # turnout draw, a pool structure and a national swing, so this | **keep** (correct) |
| src/score.py:717 | C | city-year share a turnout draw, a pool structure and a national swing, and | **keep** (correct) |
| src/score.py:811 | C | a pool structure and a national swing. Rao & Scott's first-order correction | **keep** (correct) |
| src/score.py:856 | C | draw, one national swing, one city's small-party structure — so the count of | **keep** (correct) |
| src/theta_residual.py:766 | C | moves with that year's national swing. A nominal p-value here is | **keep** (correct) |
| src/theta_residual.py:1015 | C | says metros within a cycle share one national swing, for four reasons at | **keep** (correct) |
| src/tooltip_says.py:329 | N | "ActionSA's share in Ipsos's national poll of August 2021, the only independent poll before that election, scaled to the areas ActionSA contested."), | **keep** (correct) |
| src/turnout.py:3 | C | Local elections draw far fewer voters than the national/provincial elections | **keep** (correct) |
| tests/test_blended_centres.py:354 | N | every polled party at 2026 has a 2024 national baseline. A polled arrival | **keep** (correct) |
| tests/test_blended_centres.py:914 | N | exclusive at every target that exists. 'national_polls' returns nothing at | **keep** (correct) |
| tests/test_data_coverage.py:265 | C | string identifies each city in each pre-2011 national archive. **If it has | **keep** (correct) |
| tests/test_data_coverage.py:266 | C | an entry, the file is derivable today** — the national CSV is in | **keep** (correct) |
| tests/test_levers_are_live.py:324 | N | "2021 poll is 'ipsos-2021-lge-national', which drives the ARRIVALS path " | **keep** (correct) |
| tests/test_levers_are_live.py:330 | N | "the national poll the arrivals path reads too. Its entry is deleted.") | **keep** (correct) |
| tests/test_levers_are_live.py:339 | N | "'ipsos-2021-lge-national', whose scope is 'national'; the only " | **keep** (correct) |
| tests/test_levers_are_live.py:574 | N | where="'_usable = polling.national_polls(...) if scenario['poll_paths'] " | **keep** (correct) |
| tests/test_levers_are_live.py:581 | N | "so gated the national poll the arrivals path reads. With " | **keep** (correct) |
| tests/test_levers_are_live.py:585 | N | where="same — neither 'national_polls' (arrivals) nor the metro block " | **keep** (correct) |
| tests/test_levers_are_live.py:1590 | N | "path — 'ipsos-2021-lge-national' has n=1501, so a 5,000 floor " | **keep** (correct) |
| tests/test_polling_sd.py:7 | N | ~500-person subsamples of a national sample, by a different house, with an | **keep** (correct) |
| tests/test_polling_sd.py:159 | N | """'n' finally does work, and a metro cut of a national sample is discounted.""" | **keep** (correct) |
| tests/test_polling_sd.py:163 | N | "a metro cut of a national sample is priced the same as a " | **keep** (correct) |
| tests/test_polling_synthetic.py:260 | N | "a metro cut of a national sample is priced the same as a " | **keep** (correct) |
| tests/test_prior_local_fails_closed.py:440 | N | locally below ''PRIOR_LOCAL_FLOOR'' and polled nothing nationally are not | **keep** (correct) |
| tests/test_regressions.py:265 | N | baseline bounds by-election and polling evidence to what a party's national | **keep** (correct) |
| tests/test_reweight.py:818 | C | dict(ok, id="national", scope="national", city=None), | **keep** (correct) |
| tests/test_scored_universe.py:1373 | C | turnout draw and a national swing — and require the cluster interval to be | **keep** (correct) |
| tests/test_stage_estimation.py:1304 | C | "national": nat, "local": loc} | **keep** (correct) |
| tests/test_stage_estimation.py:1321 | C | "moved_from_national": from_national, | **keep** (correct) |
| tests/test_stage_estimation.py:1324 | C | "at_full_national": at_full_national, | **keep** (correct) |
| tests/test_temporal.py:414 | N | The contested-area conversion divides a national poll share by the share of | **keep** (correct) |
| tests/test_your_forecast_page.py:1368 | C | elif kind[c] == "national": | **keep** (correct) |
| DATA-QUALITY.md:89 | C | 2016 = 402, 2011 = 197), and **the national and provincial halves of the same | **keep** (correct) |
| DATA-QUALITY.md:98 | C | The 2014 national and provincial vote is absent from the current portal; its | **keep** (correct) |
| DATA-QUALITY.md:514 | C | collapse against a national LGE turnout of 45.9%, Cape Town highest of the | **keep** (correct) |
| DATA-QUALITY.md:527 | C | 'src/ingest_historic.py' converts the six pre-2011 national IEC archives into | **keep** (correct) |
| ITERATING.md:180 | C | national swing, so the binomial and the metro bootstrap are both | **keep** (correct) |
| ITERATING.md:1225 | C | 2021 national swing, ActionSA's arrival, one fragmentation shock. Under | **keep** (correct) |
| JUDGEMENT-CALLS.md:170 | N | \| 'poll_min_n' \| 300 \| 'polling.screen' \| Declared at 300 and settable. Note it runs ahead of every scope test, so it also gates the national pol… | **keep** (correct) |
| JUDGEMENT-CALLS.md:376 | N | the 2016 national poll names only ANC/DA/EFF, every one of which has a baseline, | **keep** (correct) |
| JUDGEMENT-CALLS.md:421 | N | 1. Which poll paths run: '"off"' · '"arrivals"' (a national poll converted to the contested area, for parties with NO record) · '"all"' (adds the met… | **keep** (correct) |
| JUDGEMENT-CALLS.md:423 | N | 3. **REVERSED ON SIXTEEN, 2026-08-25 (§1.94).** Sixteen city-years, 1500 draws, paired on identical seeds: **off 376 coherent / CRPS 324.6 · arrivals… | **keep** (correct) |
| JUDGEMENT-CALLS.md:455 | N | **Record.** A ~500-person metro cut of a national sample carries the parent design's weighting loss and clustering, so its recorded 'n' overstates th… | **keep** (correct) |
| JUDGEMENT-CALLS.md:501 | N | **Now.** Declared at 300 and settable. Note it runs ahead of every scope test, so it also gates the national polls that drive the arrivals path. | **keep** (correct) |
| JUDGEMENT-CALLS.md:638 | N | 4. **AMENDED 2026-10-09 (model correction batch, item 8): it now binds in the draws, outside the poll blend.** The roster parties whose only record i… | **keep** (correct) |
| JUDGEMENT-CALLS.md:1029 | C | - **Cross-ballot, on the whole record.** By-elections are local ward contests from 2022-02; the only real result after them is the 2024 provincial ba… | **keep** (correct) |
| JUDGEMENT-CALLS.md:1075 | N | \| — \| the newcomer δ by anchor class (arm S) \| 'newness_width = "by_anchor"': a new party is **anchored** when it took votes at the preceding nati… | **keep** (correct) |
| JUDGEMENT-CALLS.md:1365 | C | **Record.** How much of the national swing the 'blended-swing' reference carries: 'prev + w · swing', which is what Murphy's convex combination of pe… | **keep** (correct) |
| JUDGEMENT-CALLS.md:1906 | N | \| 'poll_min_n' / 'POLL_MIN_N' \| 300 \| An admission floor. The register's own smallest admitted poll is n=503, so any value in (0, 503] is observat… | **keep** (correct) |
| JUDGEMENT-CALLS.md:2324 | N | **What it decides.** Whether a party that polled in the preceding NATIONAL | **keep** (correct) |
| JUDGEMENT-CALLS.md:2482 | N | and polled nothing at the preceding NATIONAL one is assumed onto an unheld | **keep** (correct) |
| JUDGEMENT-CALLS.md:2781 | C | trigger can never fire. A party that plainly exists nationally and has no local | **keep** (correct) |
| JUDGEMENT-CALLS.md:3249 | N | national result to anchor on. If a rupture occurs before polling day the rule | **keep** (correct) |
| JUDGEMENT-SHEET.md:124 | N | \| 'poll_min_n' \| 300 \| lever \| CERTIFIED INERT (UNDELIVERED) — same — neither 'national_polls' (arrivals) nor the metro block is entered, so noth… | **keep** (correct) |
| JUDGEMENT-SHEET.md:253 | N | \| 'poll_credence' \| 2021 \| UNDELIVERED \| **DATA** \| '_metro' is empty, so '_agg' is None and run_model skips the entire poll-blend block — no le… | **keep** (correct) |
| JUDGEMENT-SHEET.md:255 | N | \| 'poll_deff_subsample' \| 2021 \| UNDELIVERED \| **DATA** \| '_metro' is empty, so '_agg' is None and run_model skips the entire poll-blend block —… | **keep** (correct) |
| JUDGEMENT-SHEET.md:257 | N | \| 'poll_drift_per_root_day' \| 2021 \| UNDELIVERED \| **DATA** \| '_metro' is empty, so '_agg' is None and run_model skips the entire poll-blend blo… | **keep** (correct) |
| JUDGEMENT-SHEET.md:259 | N | \| 'poll_half_life_days' \| 2021 \| UNDELIVERED \| **DATA** \| '_metro' is empty, so '_agg' is None and run_model skips the entire poll-blend block —… | **keep** (correct) |
| JUDGEMENT-SHEET.md:261 | N | \| 'poll_house_k' \| 2021 \| UNDELIVERED \| **DATA** \| '_metro' is empty, so '_agg' is None and run_model skips the entire poll-blend block — no lev… | **keep** (correct) |
| JUDGEMENT-SHEET.md:263 | N | \| 'poll_screen_sd' \| 2021 \| UNDELIVERED \| **DATA** \| '_metro' is empty, so '_agg' is None and run_model skips the entire poll-blend block — no l… | **keep** (correct) |
| JUDGEMENT-SHEET.md:281 | N | \| 'poll_min_n' \| 2021 \| UNDELIVERED \| **SWITCH** \| '_usable = polling.national_polls(...) if scenario['poll_paths'] in ('arrivals', 'all') else … | **keep** (correct) |
| JUDGEMENT-SHEET.md:282 | N | \| 'poll_min_n' \| 2026 \| UNDELIVERED \| **SWITCH** \| same — neither 'national_polls' (arrivals) nor the metro block is entered, so nothing calls '… | **keep** (correct) |
| MACHINERY.md:398 | N | \| **National polls → metro** \| 'polling.metro_estimate' \| MEASURED conversion \| national share ÷ contested area's share of the national vote \| | **keep** (correct) |
| MACHINERY.md:1213 | N | \| 'baseline_share' \| **nothing** \| informational: what it polled at the preceding national election \| | **keep** (correct) |
| MACHINERY.md:1285 | C | the by-elections are ward contests, the outcome a national-provincial list | **keep** (correct) |
| MODEL-INDEX.md:136 | N | \| 0.001 \| 'fold.FIT_MIN_BASE_SHARE', 'montecarlo.FALSIFIER_MIN_CENTRE', 'montecarlo.KAPPA_TOL', 'polling.POLL_DRIFT_PP_PER_ROOT_DAY', 'pools.NATION… | **keep** (correct) |
| MODEL-INDEX.md:782 | N | \| 'polling.NATIONAL_VOTES' \| {'2016': int(26333353 * 0.5794), '2021': int(26204579 * 0.4579)} \| yes \| NO \| NO \| 'contested_area', 'montecarlo' … | **keep** (correct) |
| MODEL-INDEX.md:784 | N | \| 'polling.SCOPES' \| frozenset({'national', 'metro', 'metro-aggregate', 'province'}) \| NO \| NO \| NO \| -- \| | **keep** (correct) |
| MODEL-INDEX.md:1078 | C | \| 'benchmarks.uniform_swing' \| model+measurement \| The last local election, shifted by the national swing that bracketed it. \| 'tests/test_roster… | **keep** (correct) |
| MODEL-INDEX.md:1298 | N | \| 'polling.national_polls' \| model+measurement \| The admitted polls that are a reading of the country. See metro_polls. \| 'montecarlo' \| | **keep** (correct) |
| MODEL-INDEX.md:1304 | N | \| 'polling.contested_share' \| model+measurement \| What fraction of the national roll sits in the municipalities listed. \| -- \| | **keep** (correct) |
| MODEL-INDEX.md:1306 | N | \| 'polling.metro_estimate' \| model+measurement \| A national poll number converted to a share of each contested metro. \| 'montecarlo' \| | **keep** (correct) |
| MODEL-INDEX.md:1493 | C | \| 'fold' \| model+measurement \| NO \| 'src/arrivals', 'src/backtest', 'src/benchmarks', 'src/compare_history', 'src/declares', 'src/diagnose', 'src… | **keep** (correct) |
| MODEL-INDEX.md:1501 | C | \| 'ingest_npe' \| neither \| yes \| -- \| Ingest IEC national/provincial election bulk result files to a JHB VD-level subset. \| | **keep** (correct) |
| MODEL-INDEX.md:1512 | N | \| 'polling' \| model+measurement \| NO \| 'src/build_play', 'src/contested_area', 'src/freeze', 'src/montecarlo', 'src/reweight', 'tests/test_delive… | **keep** (correct) |
| PLAN-TO-LIVE.md:48 | N | **SUPERSEDED 2026-08-25 (§1.94): re-measured on sixteen city-years the poll channel is worth −6 coherent seats, not +48 — turning it OFF is better. T… | **keep** (correct) |
| PLAN-TO-LIVE.md:107 | N | four 2026 polls, none national, 'montecarlo.py''s national-scope gate on the | **keep** (correct) |
| PLAN-TO-LIVE.md:134 | N | ### A3. Chase one national 2026 poll ★ start now, long lead time | **keep** (correct) |
| PLAN-TO-LIVE.md:137 | N | at 2026** — not for want of code, but because no national 2026 poll is in the | **keep** (correct) |
| PLAN-TO-LIVE.md:141 | N | **Adding SRF's national wave does NOT reduce one-house exposure — it extends the | **keep** (correct) |
| PLAN-TO-LIVE.md:143 | N | national reading and SRF also drives the arrivals path, for the same election, | **keep** (correct) |
| PLAN-TO-LIVE.md:146 | N | counts houses *within* a channel and cannot see across them. SRF national is | **keep** (correct) |
| PLAN-TO-LIVE.md:167 | N | **Reconcile 'ipsos-2021-lge-national' BEFORE the 8 September freeze.** The | **keep** (correct) |
| POLLING.md:12 | N | \| Ipsos Khayabus W2-2025 \| Dec 25–Jan 26 \| National LGE \| 3,600 CAPI ±1.9% \| ANC 38, DA 22, MK 13–14, EFF 12–13, ASA 4; 43–49% "politically home… | **keep** (correct) |
| POLLING.md:14 | N | \| SRF Q1-2026 national \| 16 Feb–6 Mar \| National LV (56% TO model) \| 2,222 CATI \| ANC 39, DA 28, MK 10, EFF 6, ASA 3 \| | **keep** (correct) |
| POLLING.md:23 | N | level. SRF Q2 national/Gauteng releases pending — re-check within days. | **keep** (correct) |
| POLLING.md:48 | N | \| Ipsos (national) \| 16–20 Aug 2021 \| 1,501 \| 49.3 \| 17.9 \| 14.5 \| **1.5** \| 1.4 \| 1.2 \| 1.5 \| | **keep** (correct) |
| POLLING.md:50 | N | ActionSA's actual national result was **2.34%**. The poll was low by a factor of | **keep** (correct) |
| POLLING.md:77 | N | Feeding the POLL rather than the outcome, 1.5% national scales to about **6.3% | **keep** (correct) |
| POLLING.md:92 | N | South African municipal elections*, which is where the single national poll is | **keep** (correct) |
| PUBLISHING-BACKLOG.md:521 | N | sample size, city vs national scope, and past accuracy (owner's first | **keep** (correct) |
| README.md:15 | C | inside one cycle share a national swing, so they are not eight independent | **keep** (correct) |
| SITE-TEXT.md:705 | N | Sources: Electoral Commission of South Africa — voting-district results for the 2011, 2016 and 2021 municipal elections, the 2014, 2019 and 2024 nati… | **keep** (correct) |
| SITE-TEXT.md:736 | N | Each forecast used what a forecaster had before polling day: the previous local election for its geography, the national election before it for each … | **keep** (correct) |
| SITE-TEXT.md:767 | C | \| **uniform swing** \| take the national swing since the last election and apply it equally everywhere \| | **keep** (correct) |
| SITE-TEXT.md:1246 | N | **What is right.** ActionSA polled {{hist_asa_npe_2024}} in the city in the 2024 national election.</span> | **keep** (correct) |
| SITE-TEXT.md:1996 | N | poll is discounted, how a national poll and a metro poll combine. The weighting | **keep** (correct) |
| SITE-TEXT.md:2701 | C | the national and provincial halves of the same election day have different | **keep** (correct) |
| SITE-TEXT.md:2703 | C | results. One election, the 2014 national and provincial vote, is missing from | **keep** (correct) |
| SITE-TEXT.md:2729 | C | \| 2014, 2019, 2024 national/provincial elections \| The provincial ballot, the model's between-elections baseline \| | **keep** (correct) |
| SOURCES.md:61 | C | ## National & provincial elections (VD-level, provincial ballot) | **keep** (correct) |
| SOURCES.md:111 | C | \| covers \| **LGE 2011, 2016, 2021 only** (ids 197 / 402 / 1091), per municipality \| **NPE 1999, 2004, 2009 and LGE 2000, 2006** (and 2011, as a cr… | **keep** (correct) |
| SOURCES.md:115 | C | \| layout \| 'Province,Municipality,Ward,VotingDistrict,…,PartyName,TotalValidVotes' (2011 is UTF-16LE) \| one national table per election; 'src/inge… | **keep** (correct) |
| SOURCES.md:118 | C | The NPE years 2014, 2019 and 2024 are a third case: national zips from their own | **keep** (correct) |
| SOURCES.md:119 | C | 'Downloadable-results' routes, and so is the 2016 LGE national export found via | **keep** (correct) |
| SOURCES.md:132 | C | ## The pre-2011 archive — a national bulk export nothing links to | **keep** (correct) |
| SOURCES.md:134 | C | Every election from 1999 is published as a single zipped national CSV under a | **keep** (correct) |
| SOURCES.md:154 | C | already held as national zips from their own routes. | **keep** (correct) |
| SOURCES.md:243 | C | .../dashboards/byelection/MapsJason/{eeid}/EEID{eeid}BigMapsNational.js | **keep** (correct) |
| SOURCES.md:247 | C | The national/province files carry only the *leading* party per ward. The | **keep** (correct) |
| SOURCES.md:261 | C | '.xls'/'.xlsx'/'.csv': nothing. One national file and one per province, e.g. | **keep** (correct) |
| SOURCES.md:314 | N | \| ArcGIS Online public search \| one 4-feature derived sample; nothing national \| | **keep** (correct) |
| SOURCES.md:433 | N | * **A NATIONAL poll declared for 2026** — added 2026-08-22, MODEL-LOG §1.69, and | **keep** (correct) |
| SOURCES.md:435 | N | arrivals poll path converts a national poll share into a metro one through the | **keep** (correct) |
| SOURCES.md:440 | N | remaining blocker is that no national poll declared for 2026 is in | **keep** (correct) |
| SOURCES.md:448 | N | Ipsos, SRF and the Social Research Foundation all publish national voting | **keep** (correct) |
| SOURCES.md:463 | C | archive — a national bulk export nothing links to". **Not** worth attempting | **keep** (correct) |
| SOURCES.md:570 | C | NPE 2014/2019/2024 and LGE 2016 were already held as national zips in | **keep** (correct) |
| SOURCES.md:591 | N | medium scenario"). We hold the national reading as 'ipsos-2021-lge-national'. | **keep** (correct) |
| SOURCES.md:844 | C | \| 'elections/_source/npe<YEAR>_provincial_national.zip' \| 2 \| 8,203,348 \| | **keep** (correct) |
| cities/joburg.toml:16 | C | ward_prefix = "798"          # picks CoJ out of national by-election files | **keep** (correct) |
| skills/forecast-stage-estimation/SKILL.md:163 | N | 1. 'poll_levels[p]' — a national poll, for a party with no record at all; | **keep** (correct) |
