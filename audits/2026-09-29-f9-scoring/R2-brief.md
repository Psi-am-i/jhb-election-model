# R2 — review of the F9 scoring script, before any number is seen

Committed before the review runs. Reissued verbatim or not at all.

## What you are reviewing

`audits/2026-09-29-f9-scoring/score_f9.py`, and the helper it imports from
`tests/test_pool_bounds.py` (`_capacity_cases`, `_actual_shares`,
`_p1_violations`).

It scores one batch of model changes against two pre-registrations:

* `prereg/2026-09-25-pool-input-repairs.md` — P1 to P7, and the section
  "What would say the window failed".
* `prereg/2026-09-27-independents-and-mergers.md`, including its dated
  amendment.

## Facts you need, with where to check them

* **What shipped.** Of the four pool repairs C1–C4, only C1 was made (freeze
  step F3, `MODEL-LOG.md` §1.269). C2 is postponed until after the election.
  C3's composition side and C4 were deferred on a measurement (§1.268). Of the
  merger prereg, only Change 2 (mergers) shipped (§1.275, which also scores
  that prereg's amended predictions 1–5). Change 1 (independents) did not ship.
  `TODO.md` §0 has the plan.
* **The pair.** "Before" is commit `69cc6cc` run on the pool specs that were on
  disk before the re-emit. Those specs carry the `pools_sha` of `pools.py` at
  `69cc6cc`. "After" is the current tree on the re-emitted specs. Both are
  `compare_history` runs at one seed and one draw count. Between the two
  commits, the non-`pools.py` model changes are in `src/montecarlo.py`,
  `src/backtest.py` and `src/theta_residual.py`
  (`git diff 69cc6cc HEAD -- src/montecarlo.py src/backtest.py src/theta_residual.py`).
* **The artefacts.** A pool spec is `data/processed/**/pools_<year>.json`
  (fields: see any spec). A `history.json` row is built in
  `src/compare_history.py`, roughly lines 1905–2070. Calibration blocks come
  from `src/score.py`. `score.cluster_bootstrap` is the repository's one
  cluster bootstrap.

## Rules for this review

* **Read-only.** Do not run the model, `compare_history`, `pools.py --emit`, or
  anything that writes under `data/`. You may run
  `.venv/bin/python audits/2026-09-29-f9-scoring/score_f9.py --self-test`.
* **Do not read any value from any `history.json`.** The before and after runs
  have not been made. The file currently in `data/processed/` is from an older
  model, and its numbers are not evidence of anything here. Its keys and
  structure may be read.
* **Do not delegate** to sub-agents. Do it yourself.

## Questions

1. For **each** prediction P1–P7, each window criterion, and each item of the
   merger prereg: does the script compute the quantity the prereg names, on the
   population the prereg names? Quote the prereg sentence and the lines of code
   that answer it. "Wrong quantity" is the failure this gate exists for. It has
   happened twice in this project, e.g. a median-based statistic quoted as the
   coherent one (`compare_history.py`, the comment at the `seat_abs_err`
   fields).
2. Where the prereg text is ambiguous, the script states a `READING`. For each
   one, is it the natural reading of the prereg? What other reading is there,
   and would it change the verdict's direction? Say which reading you would
   defend, and why.
3. Which predictions are marked NOT TESTED? Is each marking forced by what
   shipped, or could the prediction be scored as written? The other direction
   too: is any prediction scored whose premise did not happen, so a pass or a
   fail would be meaningless?
4. **The placebo.** The script treats every spec that differs only in
   `artefact_key` as a placebo whose scored row must be identical, and voids
   P5–P7 and the window criteria otherwise. Is that the right tripwire? Is the
   list of fields it compares sufficient? Can the placebo pass while the pair
   still measures something other than the change?
5. **The statistics.** Is a city-clustered percentile bootstrap of the mean
   paired difference the right yardstick for P5, given prereg D5? Is P7's
   operationalisation a test of dose–response or something weaker? Are the
   calibration and "seats without votes" criteria computed in a way that can
   fail?
6. **The self-test.** Does each constructed case test what its comment says?
   Is there a verdict that no case can flip?
7. Anything else that would make a verdict wrong.

## What to return

A list of findings. Each gives: the prediction or criterion, the prereg text,
what the script does (file:line), the defect, and the fix you propose. Then one
line per prediction: **correct**, **wrong quantity**, **wrong population**, or
**reading disputed**. Findings go to the lead, who applies only those the lead's
own re-derivation agrees with and takes any disagreement to the owner.
