# Batch pre-registration review packet (step 9)

Issued to one fresh reviewer, 2026-10-10. Blind: you get the specification and
the document `prereg/2026-10-10-model-correction-batch.md` at commit 3170ede,
not the writer's account of it.

## Ground rules
- **Read-only.** Edit nothing. Do not sub-delegate. Credit is limited.
- A fix-round writer is editing `src/` and `tests/` on the working tree at the
  same time. **Work only from commits**: `git show 3170ede:<path>`,
  `git archive <commit>` into a scratch directory. Never import or run from
  the working tree.
- **Run nothing that writes** to `data/`, `site/`, `content/` or
  `publications/`; no `--emit` except into a scratch tree's own copy of data;
  no `compare_history` against the real tree. No arm measurement runs: a
  buildability probe of a few draws is allowed, and no number from it may be
  reported as a result.
- `.venv/bin/python`, `PYTHONHASHSEED=0`.
- **Read:** `CLAUDE.md` (§1, §4 "pre-register in writing", "level and shape"),
  `QC.md`, `ITERATING.md`; `audits/2026-10-09-model-fixes/BRIEF.md` (owner
  decisions); `spec/SPEC.md` §6, §6a, §7, R2.5, R2.6 and every R3.x section;
  `reviews/M2-SUMMARY.md` (B1, N4), `reviews/M3-SUMMARY.md`,
  `reviews/M4-SUMMARY.md`, `reviews/STEP9-WRITER-BRIEF.md`.

## Questions
1. **Self-benchmarking.** Is any prediction stated against a published or
   earlier model output rather than against the world or the mechanism? Where
   an earlier MODEL-LOG number sets a size, does the document tie it to the
   world?
2. **Already-known results.** Which predictions were known before they were
   written (the writer says the M3 windows were already measured as infinite)?
   Are they labelled as such and kept out of any count of confirmed
   predictions?
3. **Arm construction.** For two arms of your choice among B6, B8, C, B: build
   the tree from the recipe and check it is the code state the arm claims
   (items in, items out). Does each switch reproduce the earlier estimator it
   stands for? Is anything approximated without saying so?
4. **Arm D and D0.** Is adding D0 consistent with P19 and R2.5? Do D and E
   compare what item 19 changes?
5. **B1.** Re-derive item 8's entered-party list and the no-record residual for
   two city-years of your choice through the model's own functions. Do they
   match §1.1?
6. **Scoring rules.** Is every prediction scorable from the planned runs, with
   a stated hold/falsify rule? Name any that can only pass, or that no planned
   run measures.
7. **Owner decisions.** Is each decision in `BRIEF.md` and the M3 summary
   reflected, and nothing contradicted?

Return findings ranked blocking / should fix / note, each with a section or
line reference, marked verified or argued.
