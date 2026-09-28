# Mutation survivor report — pilot

HEAD `69cc6cc8f6` · prepared 2026-09-28 17:38:18 · joburg 2026, seed 20261104, 20 draws · python 3.13.4, PYTHONHASHSEED=0

- run finished 2026-09-28 17:47:51: 163 mutants in 8.3 min at 7 jobs; inputs unchanged: True; data/ files changed since prepare: 0; aborted: False
- run finished 2026-09-28 18:08:34: 83 mutants in 19.8 min at 7 jobs; inputs unchanged: True; data/ files changed since prepare: 0; aborted: False

## Outcome per module

Classes: KILLED — a selected test failed · MOVED-UNTESTED — a `*draws` array moved and no selected test failed · INERT — no selected test failed and no `*draws` array moved (`reached`: the model or a selected test executes the line; `unreached`: neither does) · TIMEOUT · CRASH — the model or the test process died and no test failed.

| module | population | run | KILLED | MOVED-UNTESTED | INERT reached | INERT unreached | TIMEOUT | CRASH | s per mutant, median / p90 (both stages, one worker) |
|---|---|---|---|---|---|---|---|---|---|
| `src/citywide_table.py` | 107 | 107 | 66 | 0 | 10 | 31 | 0 | 0 | 51.4 / 90.2 |
| `src/seats.py` | 56 | 56 | 37 | 1 | 7 | 11 | 0 | 0 | 6.9 / 681.2 |

## Population: what the fixed-seed run executes

Every `src/` module with at least one line executed by the baseline `run_model` (table and parse mode together), and whether it is mutated in this run. A module on this list and not in the population is forecast path this run did not mutate.

| module | lines executed by run_model | in this run's population |
|---|---|---|
| `src/montecarlo.py` | 1207 | no |
| `src/pools.py` | 718 | no |
| `src/levels.py` | 388 | no |
| `src/polling.py` | 175 | no |
| `src/cityconfig.py` | 170 | no |
| `src/fold.py` | 115 | no |
| `src/parties.py` | 70 | no |
| `src/citywide_table.py` | 62 | yes |
| `src/seats.py` | 58 | yes |
| `src/coalitions.py` | 28 | no |

## Controls

- Baseline model: 9 `*draws` fields (draws, excessive_draws, over_draws, pool_turnout_draws, pr_share_draws, seat_draws, ward_seat_draws, ward_share_draws, ward_winner_draws); two table-mode runs identical: True; table mode == parse mode: True.
- Comparator positive controls: `night.py selftest`.
- Null mutant of `src/citywide_table.py`: model identical; tests failing on ANY edit of this file (excluded from its subsets): none
- Null mutant of `src/seats.py`: model identical; tests failing on ANY edit of this file (excluded from its subsets): none
- Mutants whose `*draws` moved, per module, killed or not (the detector sees real moves): `src/seats.py` 7

## Tests not run per mutant

**baseline fail** (8):
- `test_pool_bounds::test_no_emitted_composition_weight_is_arithmetically_impossible` — baseline fail
- `test_pool_bounds::test_the_three_known_things_hold_at_once` — baseline fail
- `test_provenance_gates::test_a_freeze_that_is_merely_BEHIND_head_is_not_called_a_liar` — baseline fail
- `test_provenance_gates::test_a_machine_without_git_does_not_produce_a_FALSE_lie` — baseline fail
- `test_provenance_gates::test_the_declaration_gate_can_pass_and_each_violation_makes_it_fail` — baseline fail
- `test_provenance_gates::test_the_gate_refuses_rather_than_scanning_a_tree_that_is_not_there` — baseline fail
- `test_published_page::test_the_page_diff_is_readable_and_names_the_token_first` — baseline fail
- `test_published_page::test_the_published_pages_are_what_this_tree_builds_today` — baseline fail
**baseline skip** (18):
- `test_data_coverage::test_raw_input_hashes_match_when_asked` — baseline skip
- `test_seats::test_official_council_BUF_2000` — baseline skip
- `test_seats::test_official_council_BUF_2006` — baseline skip
- `test_seats::test_official_council_CPT_2000` — baseline skip
- `test_seats::test_official_council_CPT_2006` — baseline skip
- `test_seats::test_official_council_EKU_2000` — baseline skip
- `test_seats::test_official_council_EKU_2006` — baseline skip
- `test_seats::test_official_council_ETH_2000` — baseline skip
- `test_seats::test_official_council_ETH_2006` — baseline skip
- `test_seats::test_official_council_JHB_2000` — baseline skip
- `test_seats::test_official_council_JHB_2006` — baseline skip
- `test_seats::test_official_council_MAN_2000` — baseline skip
- `test_seats::test_official_council_MAN_2006` — baseline skip
- `test_seats::test_official_council_NMA_2000` — baseline skip
- `test_seats::test_official_council_NMA_2006` — baseline skip
- `test_seats::test_official_council_TSH_2000` — baseline skip
- `test_seats::test_official_council_TSH_2006` — baseline skip
- `test_stage_inputs::test_an_existing_trace_passes_every_predicate` — baseline skip
**slow** (9):
- `test_census_refusal_is_not_swallowed::test_a_swallowed_refusal_narrows_the_turnout_band` — slow: 164s at baseline > cap
- `test_census_refusal_is_not_swallowed::test_the_panel_sweep_names_its_losses_in_every_city` — slow: 139s at baseline > cap
- `test_chain::test_a_declared_roster_reaches_the_emitted_spec` — slow: 307s at baseline > cap
- `test_chain::test_the_reader_simulation_spec_is_not_what_the_forecast_reads` — slow: 145s at baseline > cap
- `test_citywide_table::test_every_control_asks_for_exactly_the_tables_files` — slow: 208s at baseline > cap
- `test_intermediates_are_current::test_every_generator_ran` — slow: 233s at baseline > cap
- `test_levels_dispersion::test_key_4_is_scored_on_the_width_the_model_actually_used` — slow: 159s at baseline > cap
- `test_levers_are_live::test_a_lever_whose_gate_the_harness_can_open_is_measured_with_it_open` — slow: 549s at baseline > cap
- `test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast` — slow: 384s at baseline > cap
**static** (22):
- `test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts` — static: runs montecarlo.main against the real processed directory
- `test_chain::test_the_model_refuses_to_run_without_a_pool_spec` — static: renames the live data/processed/pools_2026.json (the sandbox refused it in the pilot's baseline; not in run_all's SERIAL_ONLY)
- `test_draw_record::test_a_tied_group_records_its_one_shared_shock` — static: git archive of a pinned commit + three full-draw runs
- `test_draw_record::test_each_check_catches_a_constructed_violation_and_then_goes_quiet` — static: git archive of a pinned commit + three full-draw runs
- `test_draw_record::test_every_drawn_array_is_identical_with_recording_on_and_off` — static: git archive of a pinned commit + three full-draw runs
- `test_draw_record::test_every_recorded_turnout_lies_inside_its_pools_band` — static: git archive of a pinned commit + three full-draw runs
- `test_draw_record::test_the_off_run_is_the_code_before_the_recording` — static: git archive of a pinned commit + three full-draw runs
- `test_draw_record::test_the_published_seats_are_byte_equal_with_recording_on_and_off` — static: git archive of a pinned commit + three full-draw runs
- `test_draw_record::test_the_record_equals_an_independent_capture_of_every_pool_turnout` — static: git archive of a pinned commit + three full-draw runs
- `test_freeze::test_an_output_outside_the_repository_does_not_discard_the_run` — static: reads git state of the live tree
- `test_freeze::test_the_dirt_detector_can_be_made_to_say_BOTH_and_exclusion_does_work` — static: reads git state of the live tree
- `test_freeze::test_the_freeze_covers_every_declared_lever` — static: reads git state of the live tree
- `test_freeze::test_the_freeze_hash_matches_its_own_content` — static: reads git state of the live tree
- `test_freeze::test_the_freeze_names_a_commit_that_exists_and_a_clean_tree` — static: reads git state of the live tree
- `test_freeze::test_the_freeze_records_every_environment_switch` — static: reads git state of the live tree
- `test_freeze::test_the_frozen_forecast_is_a_council` — static: reads git state of the live tree
- `test_temporal::test_fold_variant_run_leaves_canonical_parameters_untouched` — static: runs real pipeline commands against the real data/processed
- `test_temporal::test_fold_variant_run_writes_only_its_own_variant_file` — static: runs real pipeline commands against the real data/processed
- `test_temporal::test_metro_roster_and_vote_presence_still_agree_where_the_poll_path_looks` — static: runs real pipeline commands against the real data/processed
- `test_temporal::test_the_poll_path_asks_who_stood_not_who_scored` — static: runs real pipeline commands against the real data/processed
- `test_temporal::test_turnout_for_another_city_leaves_joburg_turnout_untouched` — static: runs real pipeline commands against the real data/processed
- `test_temporal::test_turnout_for_another_city_writes_only_its_own_directory` — static: runs real pipeline commands against the real data/processed

Statically excluded but PASSED in the sandbox at baseline (they wrote nothing the sandbox refused, or skipped): 9 — `test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`, `test_draw_record::test_a_tied_group_records_its_one_shared_shock`, `test_freeze::test_an_output_outside_the_repository_does_not_discard_the_run`, `test_freeze::test_the_freeze_covers_every_declared_lever`, `test_freeze::test_the_freeze_hash_matches_its_own_content`, `test_freeze::test_the_freeze_records_every_environment_switch`, `test_freeze::test_the_frozen_forecast_is_a_council`, `test_temporal::test_metro_roster_and_vote_presence_still_agree_where_the_poll_path_looks`, `test_temporal::test_the_poll_path_asks_who_stood_not_who_scored`

## Survivors, by file and function

Every INERT and MOVED-UNTESTED mutant (and TIMEOUT/CRASH, which no test noticed either). `model`: what the fixed-seed run did (`not-executed` = the run never reaches the line). `tests`: run / selected / reaching before exclusions (scan readers of the file included); † = stage 1 ran only the cheapest of the selected tests, and the mutant still owes a stage-2 run of the rest. `executed by`: how many tests' baseline coverage executes the mutated code, as opposed to reading the file as text.

### `src/citywide_table.py`

**<module>**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 60 | `if str(HERE) not in sys.path:` | cmp | `not in` → `in` in `str(HERE) not in sys.path` | INERT reached | identical | 33/33/38 | 11 |
| 60 | `if str(HERE) not in sys.path:` | negate | negate `str(HERE) not in sys.path` | INERT reached | identical | 33/33/38 | 11 |
| 61 | `sys.path.insert(0, str(HERE))` | const | `0` → `1` | INERT reached | not-executed | 33/33/38 | 11 |
Reaching tests NOT run for these mutants (excluded; see above): `test_citywide_table::test_every_control_asks_for_exactly_the_tables_files`, `test_freeze::test_the_freeze_records_every_environment_switch`, `test_provenance_gates::test_a_machine_without_git_does_not_produce_a_FALSE_lie`, `test_provenance_gates::test_the_declaration_gate_can_pass_and_each_violation_makes_it_fail`, `test_provenance_gates::test_the_gate_refuses_rather_than_scanning_a_tree_that_is_not_there`

**_key**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 94 | `p = p.relative_to(REPO)` | drop | drop `p = p.relative_to(REPO)` | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**election_year**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 101 | `raise TableRefusal(f"citywide table: cannot date {key!r}; a…` | drop | drop `raise TableRefusal(f"citywide table: cannot date {key!r}; an undatabl…` | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**_gates_set**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 112 | `return [g for g in GATES if os.environ.get(g) not in (None,…` | drop | drop `return [g for g in GATES if os.environ.get(g) not in (None, "")]` | INERT reached | identical | 32/32/33 | 6 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**build**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 118 | `raise TableRefusal(f"citywide table: refusing to build with…` | drop | drop `raise TableRefusal(f"citywide table: refusing to build with " f"{_gat…` | INERT unreached | not-executed | 26/26/27 | 0 |
| 121 | `cityconfig.use(city)` | drop | drop `cityconfig.use(city)` | INERT reached | not-executed | 27/27/28 | 1 |
| 132 | `config = None; set = None; draws = 2; seed = None # noqa: E…` | const | `2` → `3` | INERT reached | not-executed | 27/27/28 | 1 |
| 136 | `mc.run_model(target, mc.load_scenario(_Args()), verbose=Fal…` | const | `False` → `True` | INERT reached | not-executed | 27/27/28 | 1 |
| 138 | `levels._citywide_and_roster = real` | drop | drop `levels._citywide_and_roster = real` | INERT reached | not-executed | 27/27/28 | 1 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**stale_reason**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 160 | `return f"schema {key.get('schema')!r}, expected {SCHEMA}"` | drop | drop `return f"schema {key.get('schema')!r}, expected {SCHEMA}"` | INERT unreached | not-executed | 26/26/27 | 0 |
| 161 | `if int(key.get("target", -1)) != int(target_year):` | const | `1` → `2` | INERT reached | identical | 31/31/32 | 5 |
| 174 | `return "entries and declared inputs name different files"` | drop | drop `return "entries and declared inputs name different files"` | INERT unreached | not-executed | 26/26/27 | 0 |
| 175 | `return None` | drop | drop `return None` | INERT reached | identical | 29/29/30 | 3 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**install**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 181 | `raise TableRefusal(f"citywide table: {_gates_set()} set; th…` | drop | drop `raise TableRefusal(f"citywide table: {_gates_set()} set; the table wa…` | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**main**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 201 | `ap = argparse.ArgumentParser(description=(__doc__ or "").sp…` | boolop | `or` → `and` in `__doc__ or ""` | INERT unreached | not-executed | 26/26/27 | 0 |
| 201 | `ap = argparse.ArgumentParser(description=(__doc__ or "").sp…` | const | `0` → `1` | INERT unreached | not-executed | 26/26/27 | 0 |
| 201 | `ap = argparse.ArgumentParser(description=(__doc__ or "").sp…` | drop | drop `ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[…` | INERT unreached | not-executed | 26/26/27 | 0 |
| 202 | `ap.add_argument("--city", required=True)` | const | `True` → `False` | INERT unreached | not-executed | 26/26/27 | 0 |
| 202 | `ap.add_argument("--city", required=True)` | drop | drop `ap.add_argument("--city", required=True)` | INERT unreached | not-executed | 26/26/27 | 0 |
| 203 | `ap.add_argument("--target", required=True)` | const | `True` → `False` | INERT unreached | not-executed | 26/26/27 | 0 |
| 203 | `ap.add_argument("--target", required=True)` | drop | drop `ap.add_argument("--target", required=True)` | INERT unreached | not-executed | 26/26/27 | 0 |
| 204 | `ap.add_argument("--check", action="store_true",` | drop | drop `ap.add_argument("--check", action="store_true", help="regenerate and …` | INERT unreached | not-executed | 26/26/27 | 0 |
| 207 | `os.chdir(REPO)` | drop | drop `os.chdir(REPO)` | INERT unreached | not-executed | 26/26/27 | 0 |
| 208 | `fresh = dumps(build(a.city, a.target))` | drop | drop `fresh = dumps(build(a.city, a.target))` | INERT unreached | not-executed | 26/26/27 | 0 |
| 209 | `path = table_path(cityconfig.use_target(a.target))` | drop | drop `path = table_path(cityconfig.use_target(a.target))` | INERT unreached | not-executed | 26/26/27 | 0 |
| 210 | `if a.check:` | negate | negate `a.check` | INERT unreached | not-executed | 26/26/27 | 0 |
| 211 | `if not path.exists():` | negate | negate `not path.exists()` | INERT unreached | not-executed | 26/26/27 | 0 |
| 212 | `print(f"✗ {path.relative_to(REPO)} does not exist"); return…` | const | `1` → `2` | INERT unreached | not-executed | 26/26/27 | 0 |
| 212 | `print(f"✗ {path.relative_to(REPO)} does not exist"); return…` | drop | drop `return 1` | INERT unreached | not-executed | 26/26/27 | 0 |
| 213 | `if path.read_text() != fresh:` | cmp | `!=` → `==` in `path.read_text() != fresh` | INERT unreached | not-executed | 26/26/27 | 0 |
| 213 | `if path.read_text() != fresh:` | negate | negate `path.read_text() != fresh` | INERT unreached | not-executed | 26/26/27 | 0 |
| 214 | `print(f"✗ {path.relative_to(REPO)} differs from a fresh bui…` | const | `1` → `2` | INERT unreached | not-executed | 26/26/27 | 0 |
| 214 | `print(f"✗ {path.relative_to(REPO)} differs from a fresh bui…` | drop | drop `return 1` | INERT unreached | not-executed | 26/26/27 | 0 |
| 215 | `print(f"✓ {path.relative_to(REPO)} matches a fresh build");…` | const | `0` → `1` | INERT unreached | not-executed | 26/26/27 | 0 |
| 215 | `print(f"✓ {path.relative_to(REPO)} matches a fresh build");…` | drop | drop `return 0` | INERT unreached | not-executed | 26/26/27 | 0 |
| 216 | `path.write_text(fresh)` | drop | drop `path.write_text(fresh)` | INERT unreached | not-executed | 26/26/27 | 0 |
| 217 | `print(f"wrote {path.relative_to(REPO)} ({len(fresh) / 1e3:.…` | const | `1e3` → `2000.0` | INERT unreached | not-executed | 26/26/27 | 0 |
| 219 | `return 0` | const | `0` → `1` | INERT unreached | not-executed | 26/26/27 | 0 |
| 219 | `return 0` | drop | drop `return 0` | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

### `src/seats.py`

**Allocation.top**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 51 | `def top(self, n: int = 12) -> list[tuple[str, int]]:` | const | `12` → `13` | INERT reached | identical | 47/47/53 | 26 |
| 52 | `ranked = sorted(self.seats.items(), key=lambda kv: -kv[1])` | const | `1` → `2` | INERT unreached | not-executed | 26/26/27 | 0 |
| 52 | `ranked = sorted(self.seats.items(), key=lambda kv: -kv[1])` | drop | drop `ranked = sorted(self.seats.items(), key=lambda kv: -kv[1])` | INERT unreached | not-executed | 26/26/27 | 0 |
| 53 | `return [(party, count) for party, count in ranked[:n] if co…` | offbyone | slice bound `n` + 1 | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`, `test_intermediates_are_current::test_every_generator_ran`, `test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast`, `test_provenance_gates::test_the_declaration_gate_can_pass_and_each_violation_makes_it_fail`, `test_provenance_gates::test_the_gate_refuses_rather_than_scanning_a_tree_that_is_not_there`, `test_temporal::test_fold_variant_run_leaves_canonical_parameters_untouched`

**eligible_parties**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 65 | `party: ward_votes.get(party, 0) + pr_votes.get(party, 0)` | const | `0` → `1` | INERT reached | identical | 79/79/86 | 59 |
Reaching tests NOT run for these mutants (excluded; see above): `test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`, `test_citywide_table::test_every_control_asks_for_exactly_the_tables_files`, `test_freeze::test_the_freeze_records_every_environment_switch`, `test_intermediates_are_current::test_every_generator_ran`, `test_levers_are_live::test_a_lever_whose_gate_the_harness_can_open_is_measured_with_it_open`, `test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast`, `test_temporal::test_fold_variant_run_leaves_canonical_parameters_untouched`

**outside_pool_wards**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 97 | `if p in (INDEPENDENT, "IND") or p not in combined}` | boolop | `or` → `and` in `p in (INDEPENDENT, "IND") or p not in combined` | INERT reached | identical | 50/50/55 | 28 |
| 99 | `if p in (INDEPENDENT, "IND"))` | cmp | `in` → `not in` in `p in (INDEPENDENT, "IND")` | INERT unreached | not-executed | 26/26/27 | 0 |
| 101 | `if p not in (INDEPENDENT, "IND"))` | cmp | `not in` → `in` in `p not in (INDEPENDENT, "IND")` | INERT unreached | not-executed | 26/26/27 | 0 |
| 102 | `pool_wins = {p: n for p, n in ward_wins.items() if p not in…` | cmp | `not in` → `in` in `p not in outside` | MOVED-UNTESTED | moved: excessive_draws, over_draws, seat_draws | 50/50/55 | 28 |
Reaching tests NOT run for these mutants (excluded; see above): `test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`, `test_citywide_table::test_every_control_asks_for_exactly_the_tables_files`, `test_freeze::test_the_freeze_records_every_environment_switch`, `test_levers_are_live::test_a_lever_whose_gate_the_harness_can_open_is_measured_with_it_open`, `test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast`

**allocate**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 108 | `total_seats: int = 270,` | const | `270` → `271` | INERT reached | identical | 137/137/146 | 119 |
| 114 | `if available <= 0:` | cmp | `<=` → `<` in `available <= 0` | INERT reached | identical | 116/116/123 | 96 |
| 114 | `if available <= 0:` | const | `0` → `1` | INERT reached | identical | 116/116/123 | 96 |
| 115 | `raise ValueError(f"no seats left to allocate ({available})")` | drop | drop `raise ValueError(f"no seats left to allocate ({available})")` | INERT unreached | not-executed | 26/26/27 | 0 |
| 128 | `if shortfall > len(ranked := sorted(` | cmp | `>` → `>=` in `shortfall > len(ranked := sorted( remainders, key=lambda p: (-remaind…` | INERT reached | identical | 116/116/123 | 96 |
Reaching tests NOT run for these mutants (excluded; see above): `test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`, `test_citywide_table::test_every_control_asks_for_exactly_the_tables_files`, `test_freeze::test_the_freeze_records_every_environment_switch`, `test_intermediates_are_current::test_every_generator_ran`, `test_levers_are_live::test_a_lever_whose_gate_the_harness_can_open_is_measured_with_it_open`, `test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast`, `test_provenance_gates::test_the_declaration_gate_can_pass_and_each_violation_makes_it_fail`, `test_provenance_gates::test_the_gate_refuses_rather_than_scanning_a_tree_that_is_not_there`, `test_temporal::test_fold_variant_run_leaves_canonical_parameters_untouched`

**pr_seats**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 157 | `party: allocation.seats.get(party, 0) - ward_wins.get(party…` | const | `0` → `1` | INERT unreached | not-executed | 26/26/27 | 0 |
| 157 | `party: allocation.seats.get(party, 0) - ward_wins.get(party…` | const | `0` → `1` | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

**overhang**

| line | source | op | mutation | class | model | tests | executed by |
|---|---|---|---|---|---|---|---|
| 167 | `if deficit < 0` | cmp | `<` → `<=` in `deficit < 0` | INERT unreached | not-executed | 26/26/27 | 0 |
| 167 | `if deficit < 0` | cmp | `<` → `>=` in `deficit < 0` | INERT unreached | not-executed | 26/26/27 | 0 |
| 167 | `if deficit < 0` | const | `0` → `1` | INERT unreached | not-executed | 26/26/27 | 0 |
Reaching tests NOT run for these mutants (excluded; see above): `test_freeze::test_the_freeze_records_every_environment_switch`

