# Slice M2 diff review packet (items 3, 6, 8, 9, 10)

Issued to one fresh reviewer, 2026-10-09. The review is blind: you get the
specification and the diff `git diff 954086b..2933c2e`, not the writer's
account of it.

## Ground rules
- **Read-only.** Edit nothing.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`, and nothing remote. In-process imports and pure tests are
  allowed, writing to temp directories only.
- Use `.venv/bin/python`. Do not sub-delegate. Credit is limited, so be
  economical.
- **Read:**
  - `CLAUDE.md` and `QC.md`;
  - `audits/2026-10-09-model-fixes/BRIEF.md`, including all of the owner's
    decisions;
  - `spec/SPEC.md`: §0, §1.3, §1.6–§1.9a, §2, §3 (G7–G9, G11, G12, G17, G18),
    §5, §7, and Revisions 2 and 3, including R3.6. M2 is writing-order steps
    3–5. Item 10's stale-spec refusal and its turnout-band review are not in
    M2.
  - `item9/FINDINGS.md` Q5.

## Expected red, not to be reported as regressions
Each of these follows from an un-emitted spec or table (R3.2, R3.5, R3.6):
- `test_export_draws` (2);
- `test_draw_record` (1);
- `test_chain::test_every_emitted_pool_spec_carries_a_current_artefact_key`;
- `test_stage_inputs::test_a_real_run_produces_a_trace_that_passes_every_predicate`;
- five `test_citywide_table` tests that refuse the table on `levels_sha`.

If a listed failure has some other cause, report it.

## Questions
1. **Statute.** Does the unopposed-ward handling match Schedule 1 items
   12(2), 13(1)(b) and 16(5)? Check it against `audits/2026-10-09-site-batch/law/sources/`.
   Is reporting a ward with list rows and no ward rows as `{ward: None}` right?
2. **Item 8.**
   - Does `roster_universe_check` refuse what it should in both directions, and
     nothing it should not?
   - Do the parties that enter take the local-only spine route and
     `level_sd_default`?
   - The writer changed the width-ceiling tripwire in `test_stage_estimation`
     so that it skips parties on the spine's local-only route. Can that
     exemption hide a real ceiling party? Is it delegated, as it should be, or
     a blanket exemption?
3. **Item 6.**
   - Is `slate_coverage` the one definition, with `now` and `was` on the same
     weights?
   - Is the clip `min(…, WARD_PR_RATIO_MAX)` with no floor (SPEC O3)?
   - Is any copy of the old `[0, 2.0]` clip or of the count fraction left?
4. **Item 9.** Is any reader of the band left anywhere, in `src/`, `tests/`,
   `worker-api/`, `interactive/` or the docs? Does any comment still claim a
   band runs?
5. **Item 10.**
   - Can the renamed-column check see both `sPartyName` and `Party_Votes`?
   - Is `bounds_checked` per party end to end: `run_model`, `main`,
     `compare_history` and the guard predicate?
   - Is dropping `bounds_checked` from `GUARD_DENOMINATOR_KEYS` sound?
6. **Numbers.** Can any M2 change move a drawn number at a target where the
   spec says it should not? Re-derive this in-process: a short `run_model` at
   one backtest city-year, before (`954086b`, in a temp worktree) and after.
   Report which arrays differ and whether the spec predicts it.
7. **Guards.** For each of G7, G8, G9, G11, G12, G17 and G18, check that:
   - the population is stated and checked, both ways where the claim is
     bidirectional;
   - a constructed violation is caught, and the guard goes quiet when it is
     reverted;
   - the input is constructed.
   Can any of them pass while blind?
8. **Records.** Check against the code, with no typed figures where a pointer
   belongs:
   - JUDGEMENT-CALLS §Q7, §A29, §A42, §A48, §A49, §A50, §L2 and §F32/§F35;
   - MACHINERY, DATA-QUALITY item 19, and the docstrings.
9. **The window.** The writer says the re-emit window must also rebuild the
   citywide table, which SPEC §5 does not name. Is that right? Does anything
   else need rebuilding?

Return findings ranked blocking / should fix / note, each with file:line, and
mark each verified or argued.
