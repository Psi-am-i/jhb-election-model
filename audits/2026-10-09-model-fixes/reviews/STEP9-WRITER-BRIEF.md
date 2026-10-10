# Step 9 writer brief: the batch pre-registration (2026-10-10)

One writer. Branch `remediation`. Steps 1-8 are committed and reviewed (M1-M4,
step 8 and their fix rounds). A blind review of step 8 runs in parallel and
is read-only; do not edit anything it reads except the files below.

## Read first
- `CLAUDE.md` (§1, §4: "pre-register in writing", "predict against the world
  and the mechanism, never against a prior output"), `QC.md`, `ITERATING.md`.
- `audits/2026-10-09-model-fixes/BRIEF.md`, every owner decision.
- `spec/SPEC.md`: §6 (the draft), §6a, §7, R2.5 (arms revised), R2.6, and every
  R3.x section and addendum.
- `reviews/M2-SUMMARY.md` (B1, N4), `reviews/M3-SUMMARY.md` (owner decisions:
  the window rule; the tripwire cannot fire for PA/Coloured, which replaces
  O1's prediction), `reviews/M4-SUMMARY.md` (arm E; `EXPECTED_INERT`),
  `prereg/2026-10-10-byelection-value-test.md` (scored), MODEL-LOG §1.295.

## Scope: one document, plus the measurements it needs
Write `prereg/2026-10-10-model-correction-batch.md` and its `prereg/README.md`
row. Commit it before any arm runs. It is §6 as amended by R2.5 and every
later decision, filled in:

1. **Arms and how each is built.** A, B0, B6, B8, B, C, C16, D, E. For each:
   the exact code state (commits, or a constructed tree with the recipe), the
   specs it reads, and the seeds and draws. Item 10 now refuses a spec not
   emitted for the running code, so every arm except A runs in its own scratch
   tree (`git archive` plus a copy of `data/`) with its own `pools.py --emit`
   (and `bye_value.py --emit` / `group_share_record.py --emit` where that arm's
   code reads them) into that tree. A runs from a `git archive` of 597ec38 with
   the pre-batch specs. B through E share draws and seeds. If an arm cannot be
   built as a code state from the commits (items interleaved across commits),
   say so and give the construction (a revert of named hunks, or a switch),
   never an approximation silently. Arm runs and emits are step 11; do not
   run them.
2. **Predictions P1-P19** as R2.5 leaves them, with these amendments, each in a
   dated note naming its source (never by editing R2.5):
   - P14 withdrawn.
   - N4: CHANGE's ward share is about 1e-6 (`level_floor`), not 0.
   - M3: the window rule (the widest window whose cycle-clustered paired error
     difference from the best is not measurably worse) replaces the typed tie;
     P16's predictions are restated against the windows that rule gives, as a
     prediction of the windows themselves (state your expected windows and
     why, from the mechanism).
   - M3: the PA/Coloured tripwire pair cannot fire under the owner's rule;
     O1's and P16's tripwire predictions are replaced by that statement.
   - M4: both by-election weights derive to 0, so arm E equals arm D on every
     centre and every draw. Predict exactly that, and that
     `bye_weight_mode` and `BYE_MIN_WEIGHT` are inert at 2026 (they need
     `EXPECTED_INERT` entries with a gate check in the window).
   - Step 8: item 10's prediction is "bit-identical draws; a stale spec
     refuses; none is stale after the window".
3. **B1 re-measurement (blocks this document).** P8's panel list and its null,
   and O5's no-record counts, were measured on the wrong population (item 8
   enters parties at 20 of 24 city-years; the spec's probe read
   Johannesburg's previous LGE for every city). Re-measure them on each
   city-year's own previous LGE, through the model's own functions (imported,
   not re-implemented), and put the measured lists in the document with the
   command that produced them. If a re-measurement needs `run_model`, the only
   route is `scenario["allow_stale_pools"] = True` on the current stale specs;
   that is a probe, not a measurement: say so wherever its output is used, and
   prefer a route that does not need the pools at all.
4. **Scoring rules**: what holds, what falsifies, for every prediction, stated
   before the run.

## Rules
- **Do not sub-delegate.** `.venv/bin/python` only.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`: no `--emit`, no `compare_history`, no bare `montecarlo.py`,
  no `-k temporal`. Scratch work in a temp directory.
- **No prediction against a published or earlier model output.** A number from
  an earlier MODEL-LOG measurement may set the size of an expected change only
  where the mechanism ties it to the world; say so where used.
- **No party singled out** in any rule; predictions may name parties.
- Commit the document (one commit; a second only to fix a factual error found
  before any arm runs, and say so). End each message with:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
- The commit hash.
- The arm construction table.
- The B1 re-measured lists and the commands.
- Every place you had to choose something R2.5 left open, and what you chose.
- Anything that makes an arm unbuildable as specified.
