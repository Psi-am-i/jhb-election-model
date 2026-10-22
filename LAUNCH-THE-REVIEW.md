# Launching the paid review — read this first, it is three lines

**Run, from this repository:**

    /code-review ultra ultra-review-base

⛔ **NOT bare `/ultrareview` or `/code-review ultra`.** With no argument the tool
resolves **`origin/main`**, which is 228 commits behind, and refuses with
*"275 files, 174,850 lines changed"*. It has already done this once.

**You should already be on the `ultra-review` branch.** If not:

    git checkout ultra-review

---

## Why the base branch is needed at all

**The tool derives its diff from `merge-base(base, HEAD)`, not from the base's
tree.** So the base is useful only if it is an **ancestor** of what you review.
`ultra-review-base` holds the artefacts and running records constant — three
archived spec sets, `data/processed/**`, `MODEL-LOG.md` and the process
documents, together about 63,000 lines — so the diff is the **46 files / 7,758
lines** of code, tests and governing documents that the batch actually changed.

⚠️ **Two failures have already happened here and both were silent until launch:**

| attempt | merge-base | result |
|---|---|---|
| no argument | `origin/main`, 228 commits back | 275 files — refused as too large |
| anchor built as a **child** of HEAD | HEAD itself | **zero files** — an empty diff, which reads exactly like a clean review |

**If the tool reports an empty diff or zero files, stop. Do not read it as
clean.**

## What to expect back

**The suite is 451 passed / 5 failed / 17 skipped** at `b6cf585`, and **two of
the five are live defects, not expected ones** — that distinction is in
`audits/ULTRA-REVIEW-1-STATE.md`, which the reviewers should read first.

**Two of the fifteen hunt items in the frozen brief point at work that was never
started** (`backtest.py` and `compare_history.py` are untouched; `SPLITS` was
never deleted). Roughly 13% of a five-agent, 22-minute budget will land on
nothing. That is flagged in the state document; the brief itself is frozen and
must not be amended.

## After the findings land

Triage first — fix-before / fix-after / rejected-with-reason. **The emit does not
happen until the fix-before list is empty.** Then one window, per
`POOLS-REEMIT-QUEUE.md`: archive the post-emit set **before** restoring, restore
only the 26 `pools_*.json` **by name** (`compare_history` writes `history.json`
into the same directory), then `compare_history`, then the freeze.

**Current state of the model** is `audits/ENGINE-SUMMARY-2026-09-05.md`.
**What is in flight** is `audits/BATCH-PLAN-2026-09-02.md`.
