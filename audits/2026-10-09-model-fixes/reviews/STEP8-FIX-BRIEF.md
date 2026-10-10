# M4 / step 8 fix round brief (2026-10-10)

One writer. Branch `remediation`, starting at the commit after `89a3a2e` that
carries this brief. Same rules as `STEP8-WRITER-BRIEF.md` (read it): no
sub-delegation, nothing written to `data/`, `site/`, `content/` or
`publications/`, no `--emit`, docs in the same commit, targeted modules after
the last edit quoted in each commit body, every failure assigned.

The step 8 writer found these; the coordinator reproduced rows 1-3 on 89a3a2e.

| row | defect | fix |
|---|---|---|
| 1 | `test_ipf_feasibility::test_no_numeric_module_constant_is_a_default_argument` red since M4: `bye_value.py` captures `CITIES`, `BYE_VALUE_RESAMPLES`, `BYE_VALUE_SEED`, `BYE_VALUE_PERCENTILE` in default arguments (lines ~118, 145, 193, 265), so they are frozen at import | Default `None`, resolved from the module constant inside the function. `bye_value.py`'s output must not change: build `--out` into a scratch directory before and after and compare the JSON (excluding the key's timestamp, if any). `-k bye_value -k ipf_feasibility` green on that test. |
| 2 | `test_reader_seats::test_the_seat_service_copies_exactly_the_import_closure_of_reader_seats` red since M4: `montecarlo` now imports `byelections`, and `sync_seats_py.mjs`'s `FILES` omits `byelections.py`. The seat Worker build would ship without a module it imports | First establish what the seat service needs: does `reader_seats`'s path import `byelections` at module level, and does importing it read a file the Worker does not have? If the import only needs the module, add it to `FILES`. If it reads data at import, make that read lazy so the service imports cleanly, and say so. Do not run the sync script against the real Worker directory if it writes outside the repo; check what it writes first. |
| 3 | `test_stage_estimation` turns a `SystemExit` from its real run into SKIP (~1751), so a refusing model leaves five tests unexercised while the suite looks green (CLAUDE.md §4: "it looked") | A `SystemExit` from the real run FAILS with its message. A missing input that is legitimately absent on a machine (say which, if any) may still skip, by an explicit, named condition. Constructed check: a forced `SystemExit` makes the tests fail, not skip; reverted, they behave as before. These five then fail until the window: add them to the R3.6 step 8 addendum as moved from skip to fail. |
| 4 | `test_provenance_dates::test_every_registered_entry_clears_something_on_every_page_it_names` red: the two `fixed '40%'` entries in `content/joburg/stats.toml` no longer match the methodology page | Do not touch `content/`. Find out why the page lost the text (which commit, which source) and record the test on the R3.6 step 8 addendum as owned by the site step (the w_bye reader copy, with "Partly, as the forecast does" and "The forecast counts them partly"). |

One commit per row (rows 3 and 4 may share the addendum commit).

End each commit message with:

    Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
Commit hashes; per row what changed and the test table; for row 2 what the
seat service needed and why; for row 4 the cause; any deviation.
