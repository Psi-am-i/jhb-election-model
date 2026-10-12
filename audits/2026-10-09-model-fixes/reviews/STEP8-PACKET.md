# Step 8 diff review packet (item 10's stale-spec refusal, and its fix round)

Issued to one fresh reviewer, 2026-10-10. Blind: you get the specification and
the diff `git diff 5cf36af..31663b4`, not the writers' accounts. Ignore files
under `audits/` in that range except `spec/SPEC.md`'s R3.6 addenda.

## Ground rules
- **Read-only.** Edit nothing. Do not sub-delegate. Credit is limited.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`, and nothing remote. No `--emit`. In-process imports and tests
  writing to temp directories are allowed. Do not run `-k temporal` (it
  rewrites two `data/processed` files by design).
- `.venv/bin/python`, `PYTHONHASHSEED=0`.
- **Read:** `CLAUDE.md` (§3, §4, the four-part absence rule), `QC.md`;
  `spec/SPEC.md` §1.9 (item 10, first row), §3's G10 row, §5, §7, and every R3.6
  addendum; `reviews/STEP8-WRITER-BRIEF.md` and `reviews/STEP8-FIX-BRIEF.md`.

## Questions
1. **The refusal.** Does every path by which `run_model` reads a pool spec from
   disk refuse when `pools.stale_reason` reports staleness or raises? Is there
   any path that reads a spec and skips the check (a supplied
   `scenario["pools"]`, another city root, another caller of the spec file such
   as `compare_history`, `export_draws`, `citywide_table`, the interactive
   build)? Which of those matter for a measurement?
2. **The escape.** Can `allow_stale_pools` reach a run from a city file, a
   scenario file, `--set`, `DEFAULTS`, or any default in a caller? When used,
   is it recorded where a reader of the run's outputs would see it
   (`forecast_summary.json`, the trace, the ledger)? Can an escaped run be
   mistaken for a measurement anywhere downstream?
3. **G10 and the stage pin.** Four-part rule for each new test. Does the
   constructed spec really exercise the code path a real stale spec takes? Is
   the `02_pools_artefact` pin change deliberate and complete?
4. **Fix row 1.** Are `bye_value.py` and `group_share_record.py` behaviour-
   preserving? Check one by before/after `--out` builds.
5. **Fix row 2.** Is `byelections.py` the whole of what the seat service's
   import closure lacked? Does importing it in the service open any file?
6. **Fix row 3.** Can `test_stage_estimation` still pass or skip while its real
   run did not happen on Atlas? Is the remaining skip condition one that cannot
   fire here?
7. **Expected red.** Is each test on the step 8 addendum red for the cause
   given? Is any test red on 31663b4 that no addendum lists?
8. **The measurement plan.** Arms B0-E are different code states and every
   one now refuses a spec not emitted for its own code. State what step 11
   must do so each arm reads specs emitted for its own tree, and anything in
   step 8 that would make that harder.

Return findings ranked blocking / should fix / note, each with file:line, and
mark each verified or argued.
