# Step 12 brief: scoring the batch pre-registration (2026-10-10)

Two scorers receive this brief verbatim and work independently. Neither sees
the other's output. Branch `remediation`, at the commit carrying this brief.
Steps 1-11 are committed. Nothing runs the model while you score.

## Read
- `CLAUDE.md` §1 and §4, `ITERATING.md`.
- `prereg/2026-10-10-model-correction-batch.md` in full, with both amendment
  notes. **Its §4 states how each prediction is scored. That text is the
  rule.** Do not substitute a better rule; where §4 is ambiguous, say so and
  score under each reading.
- `audits/2026-10-09-model-fixes/results/STEP11-RUNS.md` and `STEP11-RESULTS.md`.
- Raw outputs, `data/arms/step11/` (per-run `arrays.npz`, `meta.json`,
  `trace/`; `measures.json`). The harness is in `results/harness/`.

## Task
For every prediction and check in prereg §4 (the spec neutrality check, item
10, P1, P2/P2b, P3-P5/P9, P6, P8, P11, P16, P17/A1, P13, P12, P19/A5, item
10's other rows), give:

1. the verdict: **held**, **falsified**, **partly held** (name which clause
   held and which did not) or **not scorable** (say why);
2. the number that decides it, with the file and key it came from;
3. for every number that decides a verdict, **re-derive it from the raw
   arrays or traces yourself.** Do not take it from STEP11-RESULTS.md. Say
   which you re-derived and which you took as given.

Then, separately:

4. **Departures from the pre-registration.** For each place where step 11 ran
   something other than what the prereg specified, say what the prereg said,
   what was done, and whether the verdict depends on it. These include at
   least: the C16 recipe failing `git apply --check` (A13 says that stops the
   arm), B6's tree hash needing a trailing blank line, P12's population (17
   covered runs per arm, not 24), the `seed_notes` count (18), and output
   paths. Do not decide whether a departure is acceptable; state what follows
   under each answer.
5. **What the pre-registration did not predict**, with numbers: at least the
   `PA|Coloured` group-share tripwire firing at Johannesburg 2026 in every
   W-based arm.

Write your scoring to the file named in the line under "Your file" below.
Results are scored against the world and the mechanism as the prereg states
them, never against a prior output.

## Rules
- **Read-only** except your own file. No `src/`, `tests/`, `prereg/`,
  `data/processed`, `site/` change. Do not run `compare_history`, a bare
  `montecarlo.py`, or anything that writes `data/`.
- Re-derivation scripts go in your scratch directory, not the repo.
- **Do not sub-delegate.**
- **Do not commit or stage anything.** Two scorers share one checkout; the
  coordinator commits both files.

## Return
The verdict table (prediction, verdict, deciding number), the departures, the
unpredicted findings, the commit hash.
