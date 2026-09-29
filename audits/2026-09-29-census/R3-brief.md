# R3 — review of the census claims, before the census runs

Committed before the review runs. Reissued verbatim or not at all.

## What you are reviewing

`audits/2026-09-29-census/CLAIMS.md`: eight claimed mechanisms (C1–C8)
added by freeze steps F3 and F5, each with a claim, the trace stage where it
first acts, and predictions for three mutations (switch off, nudge, disable
the guard). The method is `PUBLISHING-BACKLOG.md` §15. No mutation has run.

## Where to check

* F3: `src/pools.py` — `_nest_holding_silent`, `_nest`, `_silent_pools`,
  `_uninformed_rate`, `HoldCascadeRefused`, `pool_counts`, and the
  memberless-pool refusal in `emit_pools`. MODEL-LOG §1.269, §1.275 (its "F3
  follow-ups"), JUDGEMENT-CALLS §L14.
* F5: `src/pools.py` — `Merger`, `MERGERS`, `MERGER_RETENTION`,
  `apply_mergers`, `merged_vector`, `blend_merger_vectors`, `MergerRefused`;
  its callers in `src/montecarlo.py` (`run_model`) and `src/theta_residual.py`.
  MODEL-LOG §1.275, §1.278, JUDGEMENT-CALLS §O1.
* The trace: `montecarlo.run_model`'s `trace.put(...)` calls name the stages.
* Tests: `tests/test_pool_bounds.py`, `tests/test_roster_aware_baseline.py`.

## Rules

* **Read-only.** Do not run the model, `compare_history`, `pools.py --emit`,
  or anything that writes under `data/`. Reading code, tests and documents is
  the review.
* **Do not delegate** to sub-agents.

## Questions

1. **Is the list complete?** Is there a mechanism F3 or F5 added (a branch,
   a guard, a caller, a constant) that has no claim? Name it with file:line.
2. **Is each claim what the code does?** For each C1–C8, quote the code that
   makes the claim true or false.
3. **Is each first-changed stage right?** Trace the data from the mutated
   line to the first `trace.put` it reaches. If a claim names the wrong stage,
   say which is right.
4. **Is each prediction falsifiable, and stated tightly enough to fail?** A
   prediction any outcome satisfies is a defect. Name any.
5. **Are the fixtures able to show the claim?** Does mangaung 2016 exercise
   F3's hold on the path each claim needs? Does joburg 2026 exercise both
   mergers? Would another fixture be needed for any claim?
6. **Guards.** For each guard, is the named test really the one that would
   fail? Is any guard unguarded that the file does not say is?
7. Anything else that would make the census read a live mechanism as dead,
   a dead one as live, or a wrong-stage one as right.

## What to return

Findings, each with the claim, the defect, file:line evidence, and the fix.
Then one line per claim C1–C8: **correct**, **wrong claim**, **wrong
stage**, **unfalsifiable prediction**, or **missing mechanism**.
