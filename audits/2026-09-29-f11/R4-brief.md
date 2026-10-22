# R4 — blind review before the freeze publish

Committed before the review runs. Reissued verbatim or not at all. You have
the repository; you do not have the lead's reasoning, deliberately.

## What you are reviewing

The site as it would be published at the model freeze. It is built and
committed at `02fe902` on branch `remediation` and is **not deployed**. The
live site is the 27 September edition (`fbb829e`).

    git diff fbb829e..02fe902 -- site/ home.html forecast-sheet.html publications/ content/ src/render_sheet.py src/render_home.py
    audits/2026-09-29-f11/build_all_site.log   # the build, and the ledger's dry-run summary
    site/changes.json                           # the reader-facing "what changed"

**The question is not "is the model good".** It is: **does anything on these
pages make the published site wrong, misleading, internally contradictory, or
broken — and does every figure that moved since the last edition move in a way
the pages handle honestly?**

## What changed underneath (facts, with where to check)

* The model changed between 27 September and now: a silenced voter pool is
  held at the city rate (F3, MODEL-LOG §1.269) and two party mergers transfer
  part of a predecessor's vote (F5, §1.275). Every pool spec was re-emitted
  (§1.279) and the 2026 forecast re-run. F9 (§1.280) and F10 (§1.281) record
  how the changes were measured.
* Coalition tokens are now keyed in a fixed member order
  (`render_sheet.COALITION_KEY_ORDER`).
* One figure published on 27 September, `claim.da_alone.wall_anc_high`, had
  been retired then; its quantity is now published as
  `claim.da_alone.wall_anc_top`.
* `home.p_da_largest` was retired with a reason (see the last rows of
  `publications/joburg/ledger.jsonl`).

## Where to look hardest

1. **Written claims whose verdict or wording no longer fits the numbers.** The
   site's convention (`PUBLISHING-BACKLOG.md`, and the memory of it in
   `HANDOVER.md`): live data stays current; written pieces are frozen as
   published, dated, and get a dated "Since then" note when numbers move
   materially; a statement that was wrong when published is a correction.
   Read every claim, headline and sentence whose figures moved (the dry-run
   list in the build log names them) and say whether the prose around each
   figure is still true. Quote any sentence that is now false.
2. **Figures that contradict each other** across pages or within one page.
3. **The ledger rows `--publish` would append** (the dry run in the log) and
   the retirement row: is each reason accurate, and is anything moving that
   should have been retired or dated instead?
4. **The pages against their generators.** Does the tree rebuild them
   identically? `build_site.py --out <a scratch path>` is safe.
5. **Anything that reads as an overclaim** to a reader.

## Ground rules

Read-only. ⛔ **DO NOT RUN** `src/montecarlo.py`, `src/build_all.py`,
`src/compare_history.py`, `src/build_validation.py` without `--from-json`,
`build_site.py --publish`, anything with `--emit`, or `wrangler`. They write
into `data/processed/` (gitignored, no restore), the ledger, or the live site.
`src/build_site.py --out <scratch path>` is safe. `.venv/bin/python` for
anything you run. **Do not delegate** to sub-agents.

## What to return

A verdict per area above, and a list of what must be fixed before this is
published, each with the page, the quoted text or figure, and why. Say
plainly where something is correct. Not a list of everything that could be
improved.
