# Step 8: score the pre-registration as written (brief, 2026-10-13)

Issued verbatim to two independent scorers. Each works alone and does not see
the other's output.

## Goal
Score `prereg/2026-10-12-universal-draw.md` (amendments included) against the
step-7 canonical runs, every row as written: what it predicted, what was
measured, pass / fail / not measured. Then state what §9 ("Decisions that
follow") says follows from those results.

## Inputs
- The pre-registration: `prereg/2026-10-12-universal-draw.md`. Never edit it.
- Step-7 outputs: `.claude/step7-2026-10-13/` (arms/<arm>/<city>-<year>/,
  arms/compare_*.json, arms/describe_*.json, plausibility/plausibility_*.json,
  kappa_summary.txt, r1_*.json and r1 analysis logs under logs/, commands.log).
- C0 tree: worktree `wt/c0` (branch `step7-c0`, commit dcff8fe).
- The writer's account, a claim to check and not evidence: MODEL-LOG §1.298-§1.300.
- Process: `CLAUDE.md`, `QC.md`, `ITERATING.md`.

## Known gaps (do not fill by running the model)
The step-7 run did not produce: §8 K1, K2, K4-K7 (need `pools.pool_counts`
on both trees, which needs no model run; you may call it in process, read
only); §5.3 M6; R2's table beyond what `arms.py compare` prints; a
32-transition plausibility variant for Johannesburg 2026. Mark anything
unproduced "not measured" and say what would measure it.

## Constraints
- READ ONLY. Write nothing under `data/`, `site/`, `src/`, `tests/` or the
  worktrees. Do not run `montecarlo.py`, `compare_history`, any `--emit`, or
  `arms.py run`. `arms.py compare`/`describe` and `plausibility.py` into a
  directory under your own output folder are allowed if you need to recompute.
- Use `.venv/bin/python`.
- Re-derive every decisive number from the arrays or JSON yourself; quote the
  file and field. Do not take a printed summary on trust.
- Never judge against the published forecast, a golden or any earlier output.
- Do not sub-delegate.

## Output
Write `SCORE.md` in the output folder named in your prompt:
1. A table, one row per pre-registered test (id, prediction as written,
   measured value with source file/field, verdict).
2. Every falsified prediction listed separately, with the evidence.
3. What §9 says follows, rule by rule.
4. Anything in the runs that looks wrong (a probe or run defect, not a
   finding), with evidence.
Return a short summary of the verdicts and the §9 outcome.
