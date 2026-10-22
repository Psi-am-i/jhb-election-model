# Tshwane judgement review and the city coupling

Read-only review, 2026-10-21, on branch `remediation` at `d62af5f`, run on Atlas. Nothing was edited, emitted or run beyond read-only Python probes (`nice -n 15`, one process at a time). Every claim below cites the code or record it was read from. Where a claim rests on file modification times or on argument rather than measurement, it says so.

## Summary

- **The cities are linked through one hash, and it covers more than the model reads.** `pools._cities_sha` (src/pools.py:421-437) hashes the raw bytes of every `cities/*.toml`, so any edit to `cities/tshwane.toml` (a comment, a map colour, a newsdesk outlet) marks every pool spec stale in every city, Johannesburg's live 2026 spec included.
- **What Johannesburg's numbers do read from `cities/tshwane.toml`:** the city code and slug (to find Tshwane's result files), the directory-layout flag, and the polling date for each past year in `[structure.by_year]` (a year without a `by_year` entry falls back to the national calendar date: src/pools.py:1883-1890). That is all. No `[judgements]`, `[map]`, `[site]` or `[newsdesk]` value reaches a Johannesburg pool spec. A second, narrower path exists through the cross-city width record (details in Part A).
- **Every value in Tshwane's `[judgements.scalars]` equals the model's own default** (`montecarlo._PRISTINE_DEFAULTS`). They are not Johannesburg's numbers. `cities/joburg.toml:3-5` says it was itself "GENERATED from the live constants". Six of the eight metros declare no scalars and run on those same defaults. The backtest panel (`compare_history.CITIES`, src/compare_history.py:117) scores those values on Tshwane 2011, 2016 and 2021 as well as on Johannesburg.
- **The earlier claim does not hold.** OWNER-DECISIONS-ANSWERED.md item 16 said "a published forecast built on another city's judgement values would claim calibration it does not have". Tshwane's config holds no other city's judgement values. The one Johannesburg-derived judgement block, `plan_bounds`, was deleted from Tshwane on 2026-08-31 (cities/tshwane.toml:116-134).
- **What does need work for Tshwane is inputs, not judgements:** the certified roster (16.1), the per-city VD-to-ward roll assignment, the 2026 `registered` figure, the map rotation, and the Johannesburg-only literals in the page builders. None of these requires changing a judgement value.
- **Smallest change to run cities separately:** narrow `_cities_sha` to a parsed hash of the fields the panel reads. This edits `pools.py` once, so every spec has to be re-emitted once. The last full window took about 15 minutes of wall-clock time (inferred from file mtimes). After that, a Tshwane config edit re-keys only Tshwane. There is no way to re-key the specs without recomputing them.

---

## Part A — how an edit to `cities/tshwane.toml` reaches Johannesburg

### A1. Every artefact key that covers the city configs

| key | file:line | covers | how it hashes |
|---|---|---|---|
| pool spec `artefact_key["cities_sha"]` | src/pools.py:281, 421-437 | **all** `cities/*.toml` | raw bytes of each file (`_sha`, src/pools.py:201-206), names and bytes joined |
| pool spec `artefact_key["judgements_sha"]` | src/pools.py:499-528 | **this city-year only**: `judgements/<slug>-<year>.toml` | parsed payload, deliberately not bytes: "A byte hash would mark all 26 specs stale on every comment edit" (src/pools.py:523-527) |
| `bye_value.json` `artefact_key["cities_sha"]` | src/byelections.py:141-177 (hash at 168-176) | **all** `cities/*.toml` | raw bytes, a copy of `_cities_sha`'s format |
| `width_record.json` `width_record_key` | src/montecarlo.py:3758-3836 | no direct city-toml hash. It hashes every backtest spec by content (`specs_sha`, which carries each spec's `cities_sha`), the per-city-year `judgements_sha`, and the **stored** keys of `bye_value.json` and `group_share_record.json` | indirect |
| `group_share_record.json` `artefact_key` | src/group_share_record.py:71-77 | no city-toml hash (code and deps only) | — |

`judgements/<city>-<year>.toml` is per city-year, as it should be. `_judgements_sha(city, target)` reads `lineage_path(city, target)` (src/pools.py:5020) and nothing else. The width record hashes only the backtest city-years it reads (2011, 2016, 2021: `width_record.FORWARD`, src/width_record.py:80-81). So an edit to `judgements/tshwane-2026.toml` marks only `data/processed/tshwane/pools_2026.json` stale.

### A2. Why `cities_sha` covers every city

Its docstring gives the reason (src/pools.py:422-433): `panel_turnout_spread` globs `cityconfig.CITIES_DIR` to measure how far each pool's turnout moves across the whole panel, so "adding a ninth city changes the turnout band of all twenty-six existing specs". The hash was added in the 2026-09-06 re-emit batch (`git log -S"_cities_sha"` → `efa06f7`). The bug it closed was a real one, a population the key did not cover. But the fix hashes whole files, while the panel reads only a few fields of each.

`bye_value_key` copies the same form. Its docstring says it hashes all city files for "the ward prefixes and codes that select each metro's contests and files" (src/byelections.py:150-151). The only city field it reads is `city.ward_prefix` (src/byelections.py:348).

### A3. Which `cities/tshwane.toml` fields can move a Johannesburg number

**Path 1: Johannesburg's pool spec (turnout band width).** `pool_spec` calls `panel_turnout_spread` (src/pools.py:6044). That function loads every city (src/pools.py:2747) and counts pools in each of its past local elections. The City attributes `pools.py` reads (all occurrences, by grep):

| attribute | count | what it reads from the toml |
|---|---|---|
| `city.code`, `city.path`, `city.processed` | 5, 6, 1 | `[identity].code`, `legacy_processed_root`: which files to open |
| `city.slug`, `city.name` | 28, 5 | filename, messages |
| `city.structure_for(year)` | 1 (src/pools.py:1885) | `election_date` only, inside `polling_decimal_year`; a missing `by_year` entry is caught and falls back to the calendar date (:1889-1890). `pool_counts` builds a `Target` only for its `crosswalk` path (src/pools.py:1552), which reads no structure |

`levels.py` reads only `city.path` and `city.slug` from a City (grep: 2 and 1 occurrences). Its metro list is the hard-coded `METRO_CODES` (src/levels.py:218). No `[judgements]`, `[map]`, `[site]` or `[newsdesk]` field, and no `council`, `wards` or `registered` value, is read on this path. `group_share_record._fit` (src/group_share_record.py:95-99) reaches other cities through `pools.fit_city` and the same file-locating fields, so the same analysis covers it.

**So Johannesburg's turnout band depends on Tshwane's election data, which is intended: it is a panel measurement of the world. It does not depend on Tshwane's config beyond the file-locating fields.**

**Path 2: the width record, which Johannesburg's 2026 forecast reads.** The universal draw is the default (`draw_law = "universal"`, src/montecarlo.py:428). It takes every party's width from `width_record.json` and refuses a stale one (src/montecarlo.py:3839-3860). The record is fitted across `compare_history.CITIES`, Tshwane included (src/width_record.py:104-107). For each city-year it calls `_scenario(city, ...)` → `M.apply_city(c)` (src/width_record.py:527-534), so each city's own `[judgements.scalars]` are applied. It then runs `run_model(..., stop_after="drawer_inputs")` (src/width_record.py:537-543; the stop is at src/montecarlo.py:7297). Before that stop the model reads `level_floor` (src/montecarlo.py:6461, 6527) and `entrant_prob` (src/montecarlo.py:6509: whether an ENTRANT column exists). **So a change to Tshwane's `level_floor` or `entrant_prob` could move Johannesburg's widths.** Today both equal the defaults (Part B), so nothing moves. The width record key does not hash these scalars directly; it catches them only because every spec's `cities_sha` changes. Argued from the code, not measured.

**Path 3: `bye_value.json`.** It is read only when `w_bye` is `None` (src/montecarlo.py:6964-6974). The default is 0.5 (src/montecarlo.py:162, JUDGEMENT-CALLS §A59), so it is not read on the published path. Its key still covers all cities, and the width record key covers its stored key. A re-emit after a city-toml edit therefore cascades into the width record (the order is given in POOLS-REEMIT-QUEUE.md step 3a).

### A4. The state today

All 27 specs on disk carry `cities_sha = 9328df1260c85faf`, which equals the live value. `pools.stale_reason` returns `None` (current) for Johannesburg and Tshwane at 2011, 2016, 2021 and 2026 (read-only probe, this session).

### A5. What an edit to `cities/tshwane.toml` costs today

1. Every spec goes stale: 8 metros × 3 backtest years, plus Johannesburg 2026, Johannesburg 2026 simulation and Tshwane 2026 (the loop in POOLS-REEMIT-QUEUE.md:44-53).
2. `bye_value.json` goes stale (its own `cities_sha`). The width record goes stale through `specs_sha` and the bye_value key. `group_share_record` must be rebuilt after the specs.
3. Then `compare_history` and the freeze are re-run (POOLS-REEMIT-QUEUE.md step 4).

**How long the last full window took.** This comes from file mtimes, not from a log (no duration is recorded in MODEL-LOG.md, POOLS-REEMIT-QUEUE.md or HANDOVER.md). On 17 Oct the first spec landed at 12:17:10 (`pools_2011.json`), the last backtest spec at 12:27:39 (`buffalocity/pools_2021.json`), Tshwane 2026 at 12:30:37, `group_share_record.json` at 12:31:28 and `bye_value.json` at 12:31:54. That is about 30-45 seconds per backtest spec (12:17:10 → 12:17:40 → 12:18:24 → Tshwane 2011 at 12:18:39) and about 15 minutes for specs plus two records. On 21 Oct the Johannesburg 2026 spec landed at 11:12:15, the simulation spec at 11:13:26 (about 70 seconds apart) and `width_record.json` at 11:31:22. So the width record took no more than about 18 minutes; its start time is not recorded. These mtimes record when the files were written, not when each job started.

### A6. The change that lets cities run separately

**Smallest correct change.** Replace the byte hash in `_cities_sha` with a parsed-payload hash of what the emit reads:

- **own city:** the parsed `[identity]`, `legacy_processed_root` and `[structure]` of the spec's own city. The emit never reads `[judgements]`, so it does not belong in a spec key at all: `pools.py` has no `city.judgements` read, and the scalars are applied at run time by `montecarlo.apply_city`, src/montecarlo.py:1725-1795.
- **panel:** for every `cities/*.toml`, the slug, `[identity].code` and `legacy_processed_root`, and `[structure.by_year]`'s years and `election_date`. These are the fields `panel_turnout_spread` reaches.

To go with it:

- `bye_value_key` (src/byelections.py:168-176): hash each city's `code` and `ward_prefix` only, parsed.
- `width_record_key` (src/montecarlo.py:3758): add a hash of each record city's resolved `[judgements.scalars]`. It runs each city under its own scalars (Path 2), and this keeps that dependency explicit rather than leaving it to ride on the spec hash.

**Files:** src/pools.py (`_cities_sha`, the `stale_reason` label at :611), src/byelections.py, src/montecarlo.py (`width_record_key`), src/declares.py:337 (field list), MACHINERY.md and the docstrings. Tests that name the field: tests/test_artefact_key_discriminates.py (`_case_cities_sha` :253, :346, :458-472), tests/test_stage_inputs.py:72 and :685, tests/test_bye_value.py:345, tests/test_areas.py:118.

**What it costs once.** A code change to `pools.py` moves `pools_sha` and marks every spec stale (CLAUDE.md §3). The change to `byelections.py` stales `bye_value.json`, and the change to `montecarlo.py` stales the width record (`montecarlo_sha`). That means one full window: the queue loop, the three records, then `compare_history`. By the 17 Oct mtimes, specs and two records took about 15 minutes, plus the width record and the baseline. Batch it with whatever else is queued in POOLS-REEMIT-QUEUE.md.

**After it lands:**
- An edit to Tshwane's `[map]`, `[site]`, `[newsdesk]`, comments or `[judgements]` stales no spec anywhere. A `[judgements.scalars]` edit stales only the width record, and that only if a scalar the record's runs read has changed.
- An edit to Tshwane's own `[identity]` or `[structure]` stales Tshwane's own specs. It stales other cities only if it changes a panel field. Those change only when a city is added or a delimitation is re-derived, and both are genuine panel changes.
- Re-emitting only Johannesburg's 2026 specs is short: on 21 Oct the main spec and the simulation spec landed 70 seconds apart (mtimes, A5); the main spec's own duration is not recorded. It does not stale the width record, which reads backtest specs only (src/width_record.py:110-121).

**Re-keying without recomputing is not possible under the project's rules.** The stored `artefact_key` claims what produced the spec. Rewriting it by hand would make the spec claim it was produced by code that never ran on it. That is the hand edit "Regenerate, don't grep" and CLAUDE.md §4 ("to test whether a derived artefact is current, regenerate it") forbid. Showing that the numbers did not move also needs a regeneration, so there is no zero-emit path.

**An alternative that needs no code change, and why it is worse:** move `[site]`, `[map]` and `[newsdesk]` out of `cities/*.toml`. Moving them is itself a city-toml edit, so it costs the same full window once. It also leaves comments and `[judgements.scalars]` in the byte hash. The parsed hash fixes both.

---

## Part B — the judgement review

### B1. What the Tshwane header says, and where it is right

cities/tshwane.toml:3-7, verbatim:

> `# STATUS: SKELETON. Structure is derived from Tshwane's own IEC files`
> `# (src/derive_city.py --code TSH --slug tshwane). The judgements below are`
> `# COPIED FROM JOHANNESBURG AS PLACEHOLDERS and are NOT yet defensible for`
> `# this city — see the TODO block. Nothing may be published from this config`
> `# until each one has been reviewed against Tshwane's own history.`

- **Wrong about the judgements as they stand.** The theta ranges it refers to were deleted on 2026-08-31 (cities/tshwane.toml:116-134). The remaining scalars are the model defaults, which every metro runs on (B3).
- **Right that some values are not yet Tshwane's own** (B2): `registered` and `vds` hold 2021 figures, `rotate_deg` is unchecked, and the 2026 roll has not been apportioned to wards.
- **The TODO block (cities/tshwane.toml:72-93) is mostly out of date.**
  - #2 cites the PA contestation uplift, which was deleted on 2026-08-18 (JUDGEMENT-CALLS §F27).
  - #3 is done: per-city pools are emitted, and `tshwane/pools_*.json` are current.
  - #1 asks for a VF+-specific "dial, chip and theta range". A party-specific theta range conflicts with the owner's no-party-singled-out rule (memory: no-party-singled-out). A display chip is presentation.
  - #5 (local formations such as Defenders of the People) is answered by the certified roster, once declared.

### B2. Every value in `cities/tshwane.toml`, with `cities/joburg.toml` for comparison

| key (tshwane line) | Tshwane | Johannesburg | what it is and where it came from | Joburg-specific? | Tshwane verdict |
|---|---|---|---|---|---|
| `legacy_processed_root` (:9) | false | true | output directory layout | Joburg's legacy path | keep |
| `[identity]` code, slug, names, province, `ward_prefix` (:11-19) | TSH, 799 | JHB, 798 | IEC codes. The 2026 crosswalk's ward IDs start 799 (`data/processed/tshwane/vd_ward_2026.csv`) | per city, factual | keep |
| `subdomain` (:19) | tshwane.whysoserious.city | joburg… | site address | per city | keep (owner chose the address in 16.3, not yet answered) |
| `[structure].council` (:27) | 214 | 270 | IEC Seat Calculation Detail for 2016 and 2021 (comment :23-26) | per city, derived | keep. 2026 assumes the 2021 council on 107 wards. The 2026 roll snapshot has 107 wards (`archive/iec-registration-2026-09-29/`, 107 rows), consistent with 2×107. Johannesburg's 270 makes the same assumption |
| `wards`, `list_seats` (:28-29) | 107, 107 | 135, 135 | counted from result files | per city, derived | keep (107 matches the 2026 snapshot and crosswalk) |
| `vds` (:30) | 778 | 865 | VD count | per city, derived | **stale for 2026.** 778 is the 2021 count. The 2026 crosswalk holds 774 distinct VDs. Johannesburg's top block holds its 2026 count. No model reader of `vds` found by grep |
| `registered` (:31) | 1,526,585 | 2,417,915 | target-election roll; `derive_city.target_registered` takes the snapshot's ward-row sum (src/derive_city.py:59-70, §T2) | per city, derived | **stale for 2026.** It is the 2021 roll. The 29 Sep snapshot sums to 1,684,463 (OWNER-DECISIONS-ANSWERED 16). `derive_city.py` prints a paste block and writes no file (src/derive_city.py:142-158), so the value is taken from its output and pasted by hand into `[structure]`. No model reader found: the model takes the roll from the crosswalk (§T1), and `export_interactive` reads the spec's pool `registered` |
| `election_date` (:32) | 2026-11-04 | 2026-11-04 | national polling day | national | keep |
| `[structure.by_year]` 2011/2016/2021 (:44-63) | 210/214/214 councils | 260/270/270 | IEC Seat Calculation Detail | per city, derived | keep |
| `[site]` accents (:65-69) | purple | amber | presentation | per city | keep |
| `[map]` width, cos_lat, `rotate_deg`, labels (:95-114) | 840, 0.901, 0, Tshwane places | 840, 0.898, 40, Joburg places | presentation. `cos_lat` is cos(25.75°) | per city | `rotate_deg = 0` needs a look at the first render (the file says so at :96). Labels are Tshwane's own |
| `[judgements.plan_bounds]` | absent (deleted 2026-08-31) | 7 party ranges (joburg.toml:87-95) | "Plan §3.5 sanity ranges", transcribed from the plan's theta table (§H5). Clamps only the by-election tilt, which needs `byelection_party_deltas.csv`, on disk only for Johannesburg 2026. "reads on none of the 24 panel rows" (§H5) | **yes, Joburg-specific** (from Johannesburg's history) | keep absent. Absent is the preferred state (src/cityconfig.py:196-214) |
| `turnout_pattern_blend` / `turnout_blend_jitter` / `turnout_noise_sd` (:140-142) | 0.5 / 0.25 / 0.08 | same | typed (§A41, §F23). Citywide effect of 0.08 about 0.003 | general: model default, same on all 8 metros | keep |
| `entrant_prob` (:143) | 0.25 | same | typed, then checked on the panel. §G-R2 range [0.25, 0.29] (§A3). The evidence cites Johannesburg arrivals and "7 of the 9 backtested city-years" | general: model default, scored on the panel | keep. **Live at Tshwane 2026 today**, because its spec has `roster_source = projected` and 0 seeds, while Johannesburg's has `declared` and 46. It goes inert once the certified roster is declared (§A4) |
| `entrant_share` (:144) | [0.01, 0.04, 0.12] | same | typed (§A17). Acts only where no arrival is named | general | keep (same note as `entrant_prob`) |
| `ward_noise_sd` (:145) | 0.10 | same | typed on an audit, never measured (§A38). Owner's standing refusal to widen it | general | keep |
| `level_floor` (:146) | 1e-6 | same | numerical floor (§F19, 🟢) | not a judgement | keep |
| `overhang_rule` (:147) | "deduct" | same | the statute as amended in 2021 (§H1, "STATUTE, NOT A JUDGEMENT CALL") | national law | keep |
| `draws`, `seed` (:148-149) | 5000, 20261104 | same | run settings | not judgements | keep |
| `[newsdesk]` (:151-155) | Tshwane parties, outlets | Joburg's | newsroom routine terms | per city | keep |

**Equality check (read-only probe, this session):** for both cities each of the 10 scalar keys equals `montecarlo._PRISTINE_DEFAULTS[key]`. `apply_city` resets `DEFAULTS` from the pristine copy before applying a city's scalars (src/montecarlo.py:1760-1763). **Deleting Tshwane's `[judgements.scalars]` block would change no number**, and leaving it in place changes none either.

### B3. Are these "Joburg judgements" Joburg-specific?

The backtest panel is `compare_history.CITIES` = joburg, tshwane, ekurhuleni, ethekwini, capetown, mangaung, nelsonmandelabay, buffalocity (src/compare_history.py:117-118). The six validation cities carry no `[judgements]` block. Their configs say why: "Copying Johannesburg's theta ranges here would make an out-of-sample test into a test of Johannesburg's opinions" (cities/capetown.toml:9-13). They therefore run on `DEFAULTS`. Since `apply_city` gained its reset on 2026-08-18 (§A43, src/montecarlo.py:1732-1749), every panel city-year, Tshwane's three included, runs the same scalars as Johannesburg. A value scored on that panel is a model-wide setting, not a Johannesburg one.

Of everything in the two configs, one judgement block is Johannesburg-specific: `plan_bounds`. Tshwane already lacks it.

### B4. Per-city judgements in `JUDGEMENT-CALLS.md` and the code

These are the register rows that name a city or apply per city. Every other register row is a model-wide constant applied identically to every metro (src/montecarlo.py `DEFAULTS`, src/pools.py and src/levels.py module constants).

| entry | value | Joburg-specific? | evidence | Tshwane verdict |
|---|---|---|---|---|
| §H5 `PLAN_BOUNDS` | 7 Joburg ranges | yes | above | keep absent |
| §H10 `seats.allocate(total_seats=270)` default (src/seats.py:302) | 270 | yes, Joburg's council as a default argument | `fold.py`'s two calls omit it, "printed seat diagnostic only… no forecast number is affected" (§H10). `montecarlo.COUNCIL = 270` (src/montecarlo.py:95) is overwritten by `apply_city` (:1764) | no forecast effect. The fix the register recommends (make the argument required) is a code change. It does not need a Tshwane decision |
| §A47 `SPLITS` homes (src/pools.py:3368-3390): ASA→JHB, GOOD→CPT, MK→ETH, NFP→ETH | per party | a biographical claim per party, national in scope: it sets which city counts as home for every city | §A47 | keep. For Tshwane, ActionSA counts as "away". Tshwane's 2026 ActionSA has a 2021 baseline, so it is not sized as an arrival. Argued from the code path, not tested |
| §A44 `MIN_HOME_SPLITS` and home/away | 2 | general. Its evidence names Tshwane: ActionSA's seed was "0.17% against an actual 9.28%" in Tshwane 2021 | §A44 | keep (a model-wide open item) |
| §O1 `MERGER_RETENTION` and `MERGERS` (src/pools.py:3427-3438) | 0.75. Forum 4→ASA, GOOD/RISE | general: party events, applied in every city where the parties appear | §O1 | keep |
| §F36 `PROJECTED_METRO_SHARE` (src/polling.py:531) | 8 per-metro shares, TSH 0.0561 | per metro, measured for every metro | used only by the poll paths, which ship "off" (§A8) | keep (inert) |
| §A59 `w_bye` 0.5, §A60 | all parties | general (owner) | needs a by-election delta file, which exists only for Johannesburg 2026 (§H5). OWNER-DECISIONS-ANSWERED 16 says by-election adjustments were "never built for Tshwane" | keep the value. Tshwane has no by-election input yet; that is an input gap, not a judgement |
| §T1 roll assignment, `ASSIGNMENT_2026` (src/build_concordance.py:188) | `archive/vd-ward-assignment-2026/assignment.csv`, 865 Johannesburg VDs, 798 prefixes | **the rule is general; the file is Johannesburg's** | Tshwane's `vd_ward_2026.csv` has no `part_registered_2026` column, so the 29 Sep snapshot has not been applied to its wards | needs the per-city assignment (brief 16.3) |
| §T2 city total = sum of ward rows | rule | general rule. The entry text names "the 135 ward rows" | §T2 | keep the rule. Apply it to Tshwane's 107 rows by re-running `derive_city` |
| §L12 two roster name substitutions | in `judgements/joburg-2026.toml` | per city-year | §L12 | Tshwane's certified list (16.1) needs its own canonicalisation check. Same rule, own file |
| §L1 roster `complete = true` deletes omitted parties | rule | general rule, per city-year licence | §L1, CLAUDE.md §4b | owner said yes for Tshwane if the list is the certified one (16.1) |
| §P2 Soweto gazetteer (src/areas.py:70) | Joburg wards | yes, a Johannesburg claim | §P2 | not used for Tshwane |
| §P3 `REALISTIC_PARTNERS`, `ZILLE_RED_LINES` | Joburg DA claim | yes, a Johannesburg claim | §P3 | not used for Tshwane |
| §S1 the forecast image's four coalitions | ANC+DA and others | presentation. The Joburg sets are the owner's choice | §S1 | Tshwane page: owner's call |
| §R1, §R6 editor bounds | read from all 8 metros' past LGEs | general, measured on the panel | §R1 | keep |
| §D18 `GRID_MARGIN_CELLS` | 2 | operational. "at the Johannesburg layout the optimum uses no cell in the outermost ring" | §D18 | re-check at Tshwane's first hex layout |
| §H6 `GAMMA_FOLD` | {2026:1, …} | general (per target year) | §H6 | keep (an open model-wide item) |
| per-city-year `judgements/tshwane-2026.toml` | 22 `[party.*]` entries, **no `[roster]` block** | per city-year by construction | file read | add the certified roster here (16.1). This re-keys only Tshwane 2026 (A1) |

**Joburg-only literals in page builders, not judgements:** `render_sheet.py:894-976` ("135 wards + 135 list seats = 270"), `site_text.py:63` (`content/joburg/stats.toml`), `build_site.py:1552`, `arms.py:119` (`FORECASTS = (("joburg", "2026"),)`), `fetch_iec.py:48` (`MUNI = "JHB"`), `fetch_byelections.py:196`. These belong to the Tshwane page brief (16.3).

### B5. What the item-16 recommendation got wrong

| claim | evidence that refutes it |
|---|---|
| "`cities/tshwane.toml` carries values copied from Johannesburg" (OWNER-DECISIONS-ANSWERED 16.2) | the 10 scalars equal `montecarlo._PRISTINE_DEFAULTS` (probe, B2). Johannesburg's file was generated from those defaults (cities/joburg.toml:3-5). The Johannesburg-derived ranges were deleted from Tshwane on 2026-08-31 |
| "a published forecast built on another city's judgement values would claim calibration it does not have" | the panel scores those same values on Tshwane 2011/2016/2021 (B3) |
| "Editing that file re-keys every city's pool specs… so it needs a full re-emit window" | true of the key, but no judgement edit is needed (B2). The re-keying is an over-broad hash (A3), not a real dependency |

---

## Recommendation

1. **Change no judgement value for Tshwane.** None is Johannesburg-specific except `plan_bounds`, and Tshwane already has none.
2. **Do the Tshwane work in the per-city-year file and the inputs:** the certified roster in `judgements/tshwane-2026.toml` (re-keys Tshwane 2026 only), the per-city VD-to-ward assignment and apportionment (brief 16.3), and by-election deltas if wanted. Then run `src/inputs_preflight.py --strict --city tshwane --target 2026` (CLAUDE.md §4b).
3. **Narrow `_cities_sha` (A6) in the next scheduled `pools.py` window.** In the same window, make the three edits to `cities/tshwane.toml` that are worth making:
   - re-derive `registered` and `vds` from the 2026 snapshot and crosswalk (`derive_city.py` prints them; it writes no file);
   - correct the header and the TODO block;
   - set `rotate_deg` once the map has been viewed;
   - optionally, delete the redundant `[judgements.scalars]` from both files. This is number-neutral by B2, but tests/test_register_matches_code.py, tests/test_stage_inputs.py and tests/test_blended_centres.py read the scalars, so check them first. Leaving the block in place costs nothing.

   Johannesburg then re-emits once, and Tshwane config edits never re-key it again.
4. **Until that window, any `cities/tshwane.toml` edit forces a full re-emit.** So hold all such edits for the window. None of them blocks a Tshwane forecast: the model reads none of `registered`, `vds`, `rotate_deg` or the comments.
