# Step 8 review summary (2026-10-10)

Writers: 89a3a2e (step 8), bc86ea0, aed9f69, 31663b4 (fix round). Blind
review: packet `STEP8-PACKET.md` (acbd9f8). Coordinator reproduction on
acbd9f8: `test_model_index`, `test_freeze`, `test_pool_bounds` each 1 red as
the reviewer reports; G10's module 15/1/1 with the one red on the stale spec.

**No blocking finding.** The refusal, the escape and G10 do what SPEC §1.9
says; seven mutations, six caught.

## Fix round (one writer, after the step 9 writer finishes)

| row | finding | fix |
|---|---|---|
| 1 | `MODEL-INDEX.md` stale since 31663b4 (`cityconfig.load` row) | Regenerate with `src/model_index.py`. |
| 2 | G10 cannot see a refusal moved after the spec is consumed (`scenario["pools"]`, `pool_counts`, `vd_map` set before the raise; both refusal tests still pass) | The refused run leaves `scenario` without `pools` and `_vd_pool_composition`, and no stage after `02_pools_artefact` exists. The reviewer's mutation (refusal moved to before `rng = ...`) is caught; reverted, quiet. |
| 3 | Fix row 3's behaviour (refusal fails, raw file absent skips) has no test | A constructed test asserting both, in `test_stage_estimation` or a sibling; mutation of each branch caught. |
| 4 | `export_interactive.py:229` and `build_play.py:364` read `pools_2026.json` with no `stale_reason` check, and feed the published interactive | Both refuse a stale or unverifiable spec through the same `pools.stale_reason`, with the same message form as `run_model`. One definition: share a helper rather than copying the check. |
| 5 | A spec that is not valid JSON raises `JSONDecodeError` outside the `try` (montecarlo.py ~4328) | Inside the refusal path: an unreadable spec refuses with the same message form. |
| 6 | Unlisted reds, all red before step 8 | A dated R3.6 addendum: `test_freeze::test_the_freeze_covers_every_declared_lever` (freeze carries `level_sd_default`, deleted in 6074382; re-freeze at the end of the batch, after the window); `test_published_page::test_the_published_pages_are_what_this_tree_builds_today` (the 40% prose, site step, with fix row 4 of the previous round); `test_pool_bounds::test_no_emitted_composition_weight_is_arithmetically_impossible` (find the commit it turned red at, and whether the window's emit clears it; if it is red on the pre-batch tree, it is a pre-existing defect: say so and leave it for the owner); `test_artefact_key_discriminates::test_the_specs_on_disk_agree_with_the_constructed_one` skips while specs are stale and must pass after the window (add to the window's checklist). |

**Noted, no change now:**
- `compare_history` catches `Exception`, not `SystemExit`: one stale city-year
  aborts the panel and `history.json` is not written. Fails safe.
- A caller supplying `scenario["pools"]` skips the check; only tests do
  (`test_drawer`, `test_ipf_feasibility`, `test_pool_conservation`).
- `history.json`, `backtest` and `export_draws` do not record
  `_pools_stale_allowed`. The escape is reachable only in-process, and step 11
  asserts `stale_reason` is null for every arm run.
- `STAGE_TRACE_DIR` can feed `test_stage_estimation` an old or escaped trace;
  nothing checks its `stale_allowed`. An opt-in for a human; noted.
- The reviewer's Q8 (arm construction) went to the step 9 writer.
- The near-full suite run rewrote the gitignored `interactive/py/*` copy;
  the site build re-syncs it.

## Rules for the fix round
As `STEP8-WRITER-BRIEF.md`. Do not run `-k temporal`.
