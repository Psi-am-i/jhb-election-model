# Step 9: ship arm U without the census hold (brief, 2026-10-14)

Owner decisions: PLAN.md "Owner decisions after step 8" (f83ad5a). Findings:
MODEL-LOG §1.301. Step-7 report: `.claude/step7-2026-10-13/commands.log`.

## Goal
The remediation tree carries arm U (universal draw, no centre correction,
splinter default 0.35) WITHOUT the census hold; its artefacts are regenerated
and current; the suite is green or every red is explained; and the owner gets a
before/after table against real results.

## Items, in order (one writer; nobody else touches data/)
1. **Withdraw the census hold.** Apply to `remediation` exactly the
   `src/pools.py` revert committed in the C0 worktree (`dcff8fe`, branch
   `step7-c0`). Update in the same commit: MACHINERY.md, JUDGEMENT-CALLS.md
   (the hold's rows marked withdrawn this round, with the K1 finding and the
   `_uninformed_rate` mechanism as the reason), the tests that assert the hold
   (retire or mark them for the next round with the reason; never weaken a
   test to pass), MODEL-INDEX via its generator. MODEL-LOG new §.
2. **Confirm the shipping configuration equals arm U.** Read `src/arms.py`'s
   arm definitions and the live config; state, with file:line, that the
   default run is U (universal draw on, centre correction off, level_shrink as
   U, splinter 0.35, poll_paths off). If it is not, stop and report.
3. **Regenerate.** `src/backup_ignored.py` first. Then the step-7 order items
   3-5 and 7 of POOLS-REEMIT-QUEUE ("The model round's step 7"): re-emit every
   spec, group_share_record, width_record (the shipping variant; the
   level_shrink=0 variant only if anything still reads it), the post-emit
   checks, `declares.py --verify`. Then the canonical forecast run for
   Johannesburg 2026 (5,000 draws) and every backtest summary the suite's
   declaration test needs, as POOLS-REEMIT-QUEUE / HANDOVER.md prescribe.
4. **Before/after against real results.** Run `compare_history` (it writes
   history.json/.md, which is intended now). Produce a table, per scored
   city-year (16, 2016 and 2021) plus 2011 reported: list-vote error and
   seats given to the wrong party (half the summed absolute seat error),
   for the model before this round (the tracked history.json at `7f0a921`,
   or the old summaries, state which) and after. Totals per cycle. Label every
   column with what it is and over which population. Write it into the
   MODEL-LOG §.
5. **Whole suite once**, after the last edit, full log kept. Every failure
   named, with whether it predates this step.
6. **Goldens and freeze.** Re-record goldens deliberately, saying why in the
   commit and MODEL-LOG (the round changed the draw); freeze; draws export as
   the procedure names it. Do NOT write into the site repo
   (`~/projects/atlas-jhb-site-release`); another writer is working there.
   List exactly which files the site rebuild will need to take.
7. **Splinter judgement, design only.** The owner wants
   `SPLINTER_PARENT_WEIGHT` adjustable per party as a judgement call, entered
   the same way for any party (§SJ row, judgements/joburg-2026.toml). First
   case: MK, "more like 90% ANC resemblance". Report, read-only: does the
   judgements file already support a per-party parent weight? If not, the
   smallest one-mechanism design (field name, where it is read, what the
   emit/hash covers, tests). Do not implement.

## Constraints
- Atlas only; `.venv/bin/python`. CLAUDE.md §3 (one writer, data/ is
  unrestorable: backup first) and §4b if anything treats 2026 as a forecast:
  run `src/inputs_preflight.py --strict --city joburg --target 2026` and
  report it.
- Never judge against the published forecast, a golden or earlier output: the
  before/after table is against REAL results only.
- Commit on `remediation` with messages ending
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do not push.
- Do not sub-delegate.

## Report
Commits; the item-2 confirmation; the before/after table; suite counts and
every failure; the files the site rebuild needs; the item-7 design; anything
that departed from this brief and why.
