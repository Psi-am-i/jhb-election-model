# Step 10 writer brief: the re-emit window (2026-10-10)

One writer, and **the only process touching the model** for the duration. You
own `data/processed` until you report. Branch `remediation`, starting at the
commit carrying this brief. Steps 1-9 are committed and reviewed, including
the pre-registration (`prereg/2026-10-10-model-correction-batch.md`, 3170ede,
amended 467ac2b before any run).

## Read first
- `CLAUDE.md` (§3, §4, §5), `QC.md`.
- `POOLS-REEMIT-QUEUE.md`, "The window, when it is taken".
- `audits/2026-10-09-model-fixes/spec/SPEC.md` §5 (the spec diff check, and
  which fields may move), R2.6, and every R3.x section and addendum (the
  window's obligations and the expected-red list).
- The pre-registration's §2-§3 and its amendments (what the window must
  leave for step 11).

## Scope: step 10 only. Stop and report after it.
1. **Before anything writes:** `src/backup_ignored.py`, and confirm arm A's
   saved specs `data/arms/A-specs-pre-batch/` pass `shasum -a 256 -c
   SHA256SUMS` (27 files). Do not touch that directory.
2. **Gate entries first (test files only, no `src/` change):**
   `EXPECTED_INERT` entries for `bye_weight_mode` and `BYE_MIN_WEIGHT` in
   `tests/test_levers_are_live.py`, each with its gate check (inert because
   both by-election class weights are 0; the check fails if a weight becomes
   positive). One commit.
3. **The re-emit:** the loop in `POOLS-REEMIT-QUEUE.md` exactly (2011, 2016,
   2021 for all eight metros; Johannesburg 2026 and its `--simulation`;
   Tshwane 2026). Tshwane gets no `--simulation` spec, as at the last window;
   say so. Count against the loop, and confirm one `pools_sha` across every
   spec. `test_chain::test_every_emitted_pool_spec_carries_a_current_artefact_key`
   and `test_artefact_key_discriminates::test_the_specs_on_disk_agree_with_the_constructed_one`
   must PASS (the second must not skip).
4. **The spec diff check (SPEC §5):** field by field, old spec (from arm A's
   saved copy) against new, for every spec. Report every field that moved,
   per spec, against §5's list of what may move. Anything outside that list is
   a finding: stop and report it before step 5.
5. **The derived records:** `src/bye_value.py --emit`, then
   `src/group_share_record.py --emit`. Confirm both by-election class weights
   match the M4 re-derivation (both 0; under 1%: 34 pairs; 1% or over: 35
   pairs) and that `test_intermediates_are_current` turns green for both.
6. **The rebuilds (M2 N7):** `src/citywide_table.py` and its served copy;
   `JUDGEMENT-SHEET.md`; `src/model_index.py`. M3 row 5: a real run at a
   covered city-year reports a group-share count, not "no record".
7. **The expected-red list re-read:** run every module named on any R3.x
   addendum (targeted, not the suite). Each test listed as "red until the
   window" must now pass. Report each one that does not, with its cause. The
   earlier causes masked by the stale-spec refusal (step 8 addendum) are read
   again here.
8. Commit the window's tracked changes (citywide table, judgement sheet, model
   index, any served copy) in one commit, with the counts and the diff-check
   summary in the body.

**Not in step 10:** the arms (step 11), `compare_history`, the freeze, the
whole suite, MODEL-LOG, the publishing run, the draws export, `site/`.

## Rules
- **Do not sub-delegate.** `.venv/bin/python` only.
- Nothing else runs while you write. Do not run `compare_history` (it writes
  `history.json`) or a bare `montecarlo.py` (it overwrites the forecast).
- Write nothing to `site/`, `content/` or `publications/`.
- If a step fails, stop: do not patch code to make the window pass. A code
  defect found here is reported, not fixed in the window.
- End each commit message with:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
- The backup path and the arm A checksum result.
- The emit count against the loop, and the `pools_sha`.
- The diff-check table: per spec, the fields that moved, and whether each is
  on §5's list.
- Both records' class weights and pair counts.
- The expected-red re-read: each listed test, pass or fail, with the cause.
- Commit hashes.
