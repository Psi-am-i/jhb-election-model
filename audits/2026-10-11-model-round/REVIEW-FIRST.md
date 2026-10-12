# Ultra review 4: read this first

**The brief, with the hunt list, is
`audits/2026-10-11-model-round/ULTRA-REVIEW-BRIEF.md`. Read it before the
diff.** It was written at `3f2f1bb`, before any of this code, and has not been
changed since.

**Scope.** Base branch `ur4-base` is `8ee8269`, the last commit before the
code. The diff is the model round's steps 5 and 6: everything from `2e4ea79`
to the head of `remediation`.

Step 6 came after the brief was written. It fixed what an internal diff review
found, as listed in MODEL-LOG §1.299. Treat those changes as part of the code
under review.

**Read with it:**
- `prereg/2026-10-12-universal-draw.md`, amendments 1 and 2 included;
- the designs in `audits/2026-10-11-model-round/step1/`: 1c, 1g, 1h, 1j v4 and the v4 addendum;
- the writer's account of what landed and where it departs from the designs: MODEL-LOG §1.298 and §1.299. That account is a claim to check, not evidence.

**Expected test failures.** The pool specs under `data/processed/` predate two
`pools.py` changes in this diff and have not been re-emitted, and no width
record exists yet. Tests that refuse stale specs, or need the width record,
fail by design until the step-7 re-emit (POOLS-REEMIT-QUEUE.md, "model round's
step 7"). One judgement-declaration test fails by design until step 7 rewrites
the forecast summaries. `data/**` is gitignored, so those artefacts are not in
the bundle.
