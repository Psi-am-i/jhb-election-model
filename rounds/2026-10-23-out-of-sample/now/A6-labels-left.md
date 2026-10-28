# A6 labels — items left for a human

2026-10-28, branch `site-sweep-1`, working tree on top of `99556398`. Classes (b)
and (c) of `A6-labels-spec.md` were applied as word changes. Nothing below was
edited. Line numbers are the working tree's.

Phrasings used: the election → **NPE**; a number read from the files →
**provincial-ballot share / vote / result**; a model construct (route, spine,
baseline, record, fit, floor, file) → **NPE route / spine / …**; θ →
**NPE-to-local retention ratio**.

## 1. Generated documents now stale (re-run the generator; do not hand-edit)

| file | generator | test that is red |
|---|---|---|
| `MODEL-INDEX.md` (first difference line 1181) | `.venv/bin/python src/model_index.py` | `test_model_index::test_the_committed_index_is_what_the_generator_produces_today` |
| `JUDGEMENT-SHEET.md` (first difference line 110) | `.venv/bin/python src/judgement_sheet.py` | `test_judgement_sheet::test_the_committed_sheet_is_what_the_generator_produces_today` |

`test_the_methodology_section_is_what_the_generator_produces_today` stays green,
so no Plain field (reader text) changed.

Shipped copies: `site/your-forecast/py/{byelections,cityconfig,fold,montecarlo}.py`
are copies of edited `src/` modules (docstring/comment differences only). Not
touched; they follow when `src/build_your_forecast.py` rebuilds the page.

## 2. String literals that reach an artefact, a test or a page: left as they are

| file:line | text | why left |
|---|---|---|
| `src/pools.py:3636` | `"a party with a national record but "` | string in `pools.py`: moves `pools_sha`; batch with the next re-emit |
| `src/pools.py:5447-5461` | `"no national election precedes …"`, `"the {npe} national fit …"`, `"… national results by ward"` | `pools.py` strings (reason/source text in the spec) |
| `src/pools.py:5522, 5525, 5538` | `"its {npe} national fit identifies no pool"`, `"fitted on the {npe} national election's ward results"` | `pools.py`; asserted by `tests/test_national_record_fit.py:74, 98, 100` |
| `src/pools.py:5943-5944, 6145` | prints `"… national vote below …"`, `"… national baseline and …"` | `pools.py` strings |
| `src/pools.py:6407` | `derived_from` `", and on the {previous_npe} national election …"` | `pools.py`; reaches `pools_*.json` and `history.json` |
| `src/pools.py:6517-6518` and `ARRIVAL_DEFINITIONS` keys | `fitted_from_national`, `national_fit_refused`, `ARRIVED_VS_NATIONAL…` | identifiers / spec keys (spec §4) |
| `src/levels.py:1736-1813` | route labels `"national only (first local election)"`, `"local only (no national record)"`, `"blend at full national (k=0)"`; trace keys `national`, `national_only`, `moved_from_national`, `at_full_national` | matched by tests and in `20_spine.json` / `forecast_summary.json` (spec §4) |
| `src/montecarlo.py:2848, 3739, 5725-5738, 5860, 7216, 7221` | raise/print text: `"… has a national baseline but no spine level …"`, `"… its own national result …"`, the projected-roster `how` text (`"… national baseline …"`, `"a national-share floor"`, `"prior NATIONAL vote"`), `"… a national baseline or a seed …"`, verbose `"national "` label, `"national route alone"` | non-docstring strings are in the AST that `pools._code_sha` hashes; `montecarlo_sha` is a field of `width_record.json`'s key, so editing them marks the width record stale and every run refuses (seen, then reverted). Batch with the next width-record emit |
| `src/theta_residual.py:1134` | printed table header `'national size'` | same: `theta_residual_sha` is in the width-record key |
| `cities/joburg.toml:88` | comment "raw national-to-local retention ratios" | `cities/*.toml` is hashed as bytes into every spec's `cities_sha`; a comment edit marks every `pools_*.json` stale (seen, then reverted). Batch with the next re-emit |
| `src/backtest.py:333, 353-355` | registry text `"the national-and-local level blend …"`, `"… national poll … share of the national vote … preceding national election"` | printed into `data/processed/history.md` |
| `src/build_validation.py:289, 308` | `"the national election before it …"`, `"… two national elections …"` | written to the validation page / `SITE-TEXT.md` (reader text) |
| `src/inputs_preflight.py:271, 284` | label `"national baseline"` and `what.startswith("national")` | label and logic are coupled (spec §4) |
| `src/build_make.py:809, 839, 851, 879` | kind value `"national"` | page data contract (spec §4) |
| `src/tooltip_says.py:314, 316, 320` | `Say(...)` texts | class (d) |
| `src/interactive_template.html:211-340, 780` | template text | class (d) |
| `tests/test_standalone_modules.py:144` | `"national-election ingest, run once per NPE file"` | `ENTRY_POINTS` evidence text; not a label the spec required |
| `tests/test_model_claims.py:229`, `tests/test_number_scan.py:64`, `tests/test_register_matches_code.py:330` | claim id, scan input, word list | compared or used as input |
| `tests/test_your_forecast_page.py:1102-1357` | kind `"national"` | page data contract |

## 3. Sense not settled: left, for a reader to decide

| file:line | words | question |
|---|---|---|
| `src/backtest.py:341` | "their share of the national vote" (poll conversion) | which ballot the contested-area denominator reads |
| `tests/test_temporal.py:414-415` | "the share of the national vote sitting in the municipalities the party contests" | same |
| `JUDGEMENT-CALLS.md:177`, `:1805` (§F36 heading) | `PROJECTED_METRO_SHARE` — "eight per-metro shares of the national vote" | country-wide or provincial ballot; poll path (N?) |
| `tests/test_chain.py:29` | "A national fit was briefly used as a prior on city rates" | pooled across metros (C) or the NPE |
| `MACHINERY.md:111, 116` | "Why the fit is national" / "The national fit supplies the shape" | pooled over metros; spec: keep or write "pooled" (owner's choice) |
| `MACHINERY.md:307` | `nat_level = national_share * exp(mu_theta)` | worked example; changes only if the `levels.spine` local `national` is renamed |
| `MACHINERY.md:720` | "ActionSA on the national number alone" | names a corrected page entry |
| `JUDGEMENT-CALLS.md:2455` | "locally concentrated, nationally negligible" | rhetorical; PA was 0.03-0.06% at the NPE in the metro |
| `PUBLISHING-BACKLOG.md:533` | "local record vs national mood (`spine_k` …)" | proposed reader label for a lever (class d) |
| `src/levels.py:558`, `JUDGEMENT-CALLS.md:300` | COPE "7.4% nationally" in 2009 | kept as the country-wide national-ballot figure; confirm |

## 4. Reader-facing or owner's record: not touched (class d)

- `JUDGEMENT-CALLS.md:1139, 1160, 1997` — inside **Plain** fields, which build
  `docs-public/methodology.md`.
- `OWNER-DECISIONS-ANSWERED.md:1094-1096, 1110-1111` — the spec's dated note
  ("6.22% is Johannesburg's 2024 provincial ballot") is new text in the owner's
  record; not added.
- Everything in spec §7.

## 5. Kept on purpose (quotation or code name inside prose)

`JUDGEMENT-CALLS.md:2334, 2444` (quoted first-draft wording); `src/pools.py:4091-4093`
(quoted former paragraph); route labels quoted at `src/montecarlo.py:3718, 3724`,
`MACHINERY.md:1397, 1401`, `JUDGEMENT-CALLS.md:3127`; key names in formulas at
`tests/test_spine.py:194, 484`, `tests/test_stage_estimation.py:349-350, 391, 577`,
`skills/forecast-stage-estimation/SKILL.md:106, 122, 126, 225, 235`.

## 6. Non-docstring strings that were changed

Message text only (raise, print, skip, assertion message); no test matches it
and no artefact stores it (`git grep` of each fragment). `python -m tokenize`
over HEAD and the tree, comments and docstrings removed: no other token differs.
None is in a module whose `_code_sha` enters an artefact key.

- `src/benchmarks.py:699`: 'result and a preceding national one, so `arrival_group_record`' -> 'result and a preceding NPE one, so `arrival_group_record`'
- `src/build_make.py:783`: 'build_make: no national result file for' -> 'build_make: no NPE result file for'
- `src/derive_city.py:128`: '"  θ ranges and the national-to-local shift ranges"' -> '"  θ ranges and the NPE-to-local shift ranges"'
- `src/score_forecasts.py:307`: 'one-ballot national file' -> 'one-ballot NPE file'
- `src/score_forecasts.py:310`: ': not an IEC national VD result file;' -> ': not an IEC NPE VD result file;'
- `src/turnout.py:255`: 'no national election on disk before' -> 'no NPE on disk before'
- `tests/test_blended_centres.py:303`: '"a party with a national baseline, no spine level, no theta prior "' -> '"a party with an NPE baseline, no spine level, no theta prior "'
- `tests/test_blended_centres.py:607`: '"two pieces of evidence agreeing the party is larger than its national "' -> '"two pieces of evidence agreeing the party is larger than its provincial-ballot "'
- `tests/test_blended_centres.py:608`: '"share were overruled by a bound derived from the national share — the "' -> '"share were overruled by a bound derived from the provincial-ballot share — the "'
- `tests/test_blended_centres.py:611`: '"the clamp is anchored on the national baseline again"' -> '"the clamp is anchored on the NPE baseline again"'
- `tests/test_chain.py:2492`: 'national tail; above ~2% it misses the cases it exists for.' -> 'NPE tail; above ~2% it misses the cases it exists for.'
- `tests/test_chain.py:2530`: 'national file has a share over' -> 'NPE file has a share over'
- `tests/test_chain.py:2677`: '"against the previous NATIONAL one, so the two definitions coincide at "' -> '"against the previous NPE, so the two definitions coincide at "'
- `tests/test_chain.py:2679`: '"national vote, no 2011 local one."' -> '"NPE vote, no 2011 local one."'
- `tests/test_chain.py:2690`: 'both sized from nothing and flagged as having a national record.' -> 'both sized from nothing and flagged as having an NPE record.'
- `tests/test_drawer.py:565`: 'no national baseline for' -> 'no NPE baseline for'
- `tests/test_ipf_feasibility.py:103`: 'no national baseline for' -> 'no NPE baseline for'
- `tests/test_pool_placement.py:76`: '"a national-record column moved"' -> '"an NPE-record column moved"'
- `tests/test_regressions.py:275`: 'against the national baseline rather than against the level the' -> 'against the NPE baseline rather than against the level the'
- `tests/test_regressions.py:291`: '"settled on — and not against the national baseline"' -> '"settled on — and not against the NPE baseline"'
- `tests/test_roster_aware_baseline.py:223`: 'local vote, no prior national vote, 44 seats — so either the roster' -> 'local vote, no prior NPE vote, 44 seats — so either the roster'
- `tests/test_roster_aware_baseline.py:1232`: 'the national-baseline call is not applying r x P' -> 'the NPE-baseline call is not applying r x P'
- `tests/test_spine.py:144`: '"a party with a national record must be levelled"' -> '"a party with an NPE record must be levelled"'
- `tests/test_spine.py:342`: '"more theta evidence must move a party toward the national spine"' -> '"more theta evidence must move a party toward the NPE spine"'
- `tests/test_spine.py:640`: ': k=0 must put every blended party on its NATIONAL' -> ': k=0 must put every blended party on its NPE'
- `tests/test_spine.py:646`: ': w_local is 0 but the level is not the national one' -> ': w_local is 0 but the level is not the NPE one'
- `tests/test_stage_estimation.py:424`: ', national' -> ', NPE'
- `tests/test_stage_estimation.py:477`: ': has a national record only and is labelled' -> ': has an NPE record only and is labelled'
- `tests/test_stage_estimation.py:479`: ': national-only route carrying local weight' -> ': NPE-only route carrying local weight'
- `tests/test_stage_estimation.py:490`: 'about whether the national route contributed anything' -> 'about whether the NPE route contributed anything'
- `tests/test_theta_prior.py:197`: 'no national election before' -> 'no NPE before'
- `tests/test_theta_prior.py:227`: '"a party with a national baseline and no retention record got no θ "' -> '"a party with an NPE baseline and no retention record got no θ "'
- `tests/test_theta_prior.py:930`: '"a party with a record and no national baseline is no longer priced. "' -> '"a party with a record and no NPE baseline is no longer priced. "'
- `tests/test_theta_prior.py:947`: '"no party is priced without a national baseline at 2021 any more — "' -> '"no party is priced without an NPE baseline at 2021 any more — "'
- `tests/test_ward_contest_rule.py:82`: '"a national-record party was not masked"' -> '"an NPE-record party was not masked"'
- `tests/test_ward_contest_rule.py:209`: '"a national-record ward-only party"' -> '"an NPE-record ward-only party"'
- `tests/test_roster_aware_baseline.py:1157`: a comment inside the subprocess script string at :1152 ("the national call" -> "the NPE call")
