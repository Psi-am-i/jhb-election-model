# Review — the new guard tests, the census conclusions, and F9's conclusions

Committed before the review runs. Reissued verbatim or not at all.

## What you are reviewing

1. **Four new or extended tests, uncommitted in the working tree**
   (`git diff -- tests/`):
   * `tests/test_pool_bounds.py`: `test_emit_refuses_a_spec_that_would_drop_a_declared_pool`
     and `test_the_panel_spread_does_not_count_a_held_pool_as_a_movement`,
     with the helper `_free_nest`.
   * `tests/test_roster_aware_baseline.py`: the per-function call counts and
     the `blend_merger_vectors` check added to
     `test_every_consumer_the_spec_names_calls_apply_mergers`.

   They were written to close five gaps the census reported as "unguarded"
   (`audits/2026-09-29-census/RESULTS.md`, "The three lists").
2. **The census conclusions**, `audits/2026-09-29-census/RESULTS.md`, against
   the claims (`CLAIMS.md` at `c90e693`) and the saved run outputs under
   `audits/2026-09-29-census/runs/r1/` (each mutant's `result.json`, specs,
   traces; the per-draw stages 42–44 were deleted after comparison).
3. **F9's conclusions**, `MODEL-LOG.md` §1.280 and its addendum, against
   `audits/2026-09-29-f9-scoring/result.json` and the run files in
   `audits/2026-09-29-f9-scoring/runs/`.

## Rules

* **Read-only.** Do not run the model, `compare_history`, `pools.py --emit`,
  the census, or anything that writes under `data/`. You may run the two test
  modules in question: `.venv/bin/python tests/run_all.py -k pool_bounds -k
  roster_aware_baseline`. You may read any file.
* **Do not delegate** to sub-agents.

## Questions

**The tests.** For each of the four:

1. Does it test the mechanism it names, on the population it names? CLAUDE.md
   §4 lists four things a scan-shaped test must prove: it scanned the right
   thing, it looked, it can see, and its input is constructed. Which does each
   prove, and which not?
2. Would it go red if the mechanism it guards were removed? Reason it from the
   code. The lead's claim is yes for each, and it has NOT yet been shown by
   running the mutation. Name any mutation of the guarded code that would
   leave it green.
3. Could it go red for a reason unrelated to the mechanism (order dependence,
   a global it patches and fails to restore, a cache, a data file changing)?
4. Is any number typed into it that should be derived?

**The census conclusions.**

5. For each row of the results table, does the saved output support the
   verdict? In particular: every "as claimed", every first-changed stage, the
   C5-nudge "relative error 0" (check how P and B were obtained, and whether
   that check can fail), and the one post-run harness correction
   (`pools_sha` added to the ignored keys). Is that correction legitimate, or
   could it hide a real difference?
6. Are the three lists (dead, wrong-way or wrong-stage, unguarded) complete
   given the outputs? Is anything reported "as claimed" that the claim did not
   predict, or predicted differently?

**F9.**

7. Does each sentence of §1.280 and its addendum follow from `result.json` and
   the run files? Name any claim stronger than the numbers support.

## What to return

Findings, each with where (file:line), the defect, and the fix. Then one
line per test (sound / defect) and per conclusion (supported / overstated /
wrong).
