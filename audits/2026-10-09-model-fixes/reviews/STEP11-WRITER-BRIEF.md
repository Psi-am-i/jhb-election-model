# Step 11 writer brief: the arm measurements (2026-10-10)

One writer. Branch `remediation`, starting at the commit carrying this brief.
The window (step 10) is done: 27 specs, one `pools_sha` (a58f884b337a7735),
`bye_value.json` and `group_share_record.json` emitted (2d73de7). No other
process runs the model while you measure.

## Read first
- `CLAUDE.md` (§3, §4, §5), `QC.md`, `ITERATING.md`.
- `prereg/2026-10-10-model-correction-batch.md` in full, including every
  "Amendments before any run" note. **It is the specification of this step.**
  Where it and this brief disagree, stop and report; do not choose.
- `audits/2026-10-09-model-fixes/spec/SPEC.md` §6 (runs), §1.9 (the turnout
  table), R2.5, R3.x.
- `reviews/WINDOW-WRITER-BRIEF.md` and commit 2d73de7's body (the window).

## Scope: step 11 only
1. **Record before any run**, in a new file
   `audits/2026-10-09-model-fixes/results/STEP11-RUNS.md` (commit it before
   the first arm run): HEAD; each arm's recomputed diff sha256 and tree hash at
   that HEAD (the W-based ones moved with the step 8 review fix round; the
   recipes still apply); the seeds and draws; the exact commands.
2. **Build every arm** as the pre-registration's §3 says: its own scratch tree
   (`git archive`, or the recipe), its own copy of `data/processed` (never a
   symlink shared with another arm), raw data linked read-only. Arm A reads
   `data/arms/A-specs-pre-batch/` after `shasum -c SHA256SUMS`. Every other arm
   emits its own specs (and `bye_value.py --emit` / `group_share_record.py
   --emit` where its code reads them) into its own tree, then proves them
   current before any run. Arms are separated by tree and working directory,
   never by `--processed`.
3. **Run** each arm on the 24 city-years `compare_history.runnable` returns
   and on Johannesburg 2026, at the draws and seeds the pre-registration
   fixes, in-process (`run_model` + `compare_history.run_city_year`; no
   `history.json` written anywhere in the real tree). Assert
   `02_pools_artefact.stale_reason` is null for every run of every arm.
   Arms B-E share draws and seeds.
4. **Results, not verdicts.** Put each prediction's measured quantity, by its
   pre-registered instrument, in
   `audits/2026-10-09-model-fixes/results/STEP11-RESULTS.md`: one section per
   prediction, the numbers and the command or file that produced them. Do not
   write held / falsified: scoring is a separate step with its own review.
   Include SPEC §1.9's turnout-band table from arm B's runs.
5. Raw outputs (traces, per-run JSON) go under `data/arms/<arm>/`
   (gitignored); the two results files are committed.

**Not in step 11:** scoring, MODEL-LOG, `compare_history` on the real tree,
the freeze, the whole suite, any `src/` or `tests/` change, the publishing
run, the draws export, `site/`.

## Rules
- **Do not sub-delegate.** Parallel processes inside your own work are fine;
  say how many ran at once.
- **Write nothing** to `data/processed` in the real tree, `site/`, `content/`,
  `publications/`, `prereg/`, `src/` or `tests/`. Do not touch
  `data/arms/A-specs-pre-batch/`.
- If an arm cannot be built as recipe'd (a hash that does not reproduce, a
  refusal, B8's `extra` refusal), stop that arm and report it; never patch it
  to proceed. Other arms continue.
- If credit runs short, commit what is complete in the results file, say
  exactly which arms and targets are done, and stop.
- End each commit message with:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
- Commit hashes.
- The arm table: tree hash recomputed, specs emitted and proven current,
  runs completed, any arm stopped and why.
- Where each prediction's numbers are in the results file.
- Anything the pre-registration did not anticipate.
