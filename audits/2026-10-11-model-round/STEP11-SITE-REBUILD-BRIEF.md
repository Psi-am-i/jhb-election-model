# Step 11 brief: the site rebuilt on the round's forecast, to UAT

Owner approval needed before anything runs (QC.md §4b). Owner accepted the
before/after on 2026-10-14 (PLAN.md, step 10).

## Items

1. **Merge `remediation` into `site-release`** in the site worktree
   (`~/projects/atlas-jhb-site-release`). A trial merge (scratch worktree,
   aborted) conflicts in four files:
   - `MODEL-LOG.md`: both sides appended. Keep both, the site's three dated
     sections first, then §1.297-§1.303.
   - `MODEL-INDEX.md`, `JUDGEMENT-SHEET.md`: generated. Regenerate with
     `src/model_index.py` and `src/judgement_sheet.py` after the merge.
   - `site/your-forecast/forecast.json`: build output. Rebuilt in item 3.
2. **Bring the round's data into the site worktree.** `data/**` is per
   worktree and gitignored. Copy the main tree's `data/processed` after
   `src/backup_ignored.py` in the site worktree. Acceptance:
   `src/declares.py --verify` exits 0 in the site worktree, and
   `src/freeze.py` there reproduces `forecast_frozen.json`'s
   `seat_draws_sha256` (the main tree's, `346fb97`).
3. **Build `site/` the UAT way** (scratch copy of the ledger, as
   `docs/DEPLOY-UAT.md` §0 says) and pass the number review. Acceptance:
   review stamped `blocking=0`; `deploy_check` green.
4. **Party claims whose verdict changes.** `claims.toml` verdicts are judged
   against the forecast's chances; the step-9 suite shows they disagree with
   the new chances. At the first checkpoint I list each claim whose verdict
   moves, old and new chance, and a drafted "Since then" note in the
   publication convention's form. Owner approves the wording; no claim text
   ships without it.
5. **Pages that state the forecast** (home, /forecast, articles): the build
   fetches every figure from the forecast as a token, so these move without
   edits. Written pieces stay frozen and dated; any whose stated figure is
   now different gets a "Since then" note, listed at the same checkpoint,
   owner approves.
6. **Upload a UAT version** (`wrangler versions upload`) and run the
   DEPLOY-UAT §2 checks. Live promotion is the owner's.

## Out of scope

Live promotion; the `joburg-seats` card server; the Joburg-over-time brief;
`test_arms` retire-or-re-point and the calibration re-quotes (model-repo
findings, next round); any wording change not forced by a changed figure.

## Test tier

Published figures change, so the whole suite runs once, after the last edit,
before the UAT upload is offered for promotion (§4b.5). Before it: the page
modules (`site_assets`, `site_structure`, `number_scan`, `published_page`,
`served_draws`, `reader_seats`, `reweight`), cheapest first, time-boxed.

## Checkpoints

1. After items 1-2: merge resolved, `declares --verify` and the freeze
   hash. Report.
2. After item 3's build: the claim and article list for items 4-5. Stop
   for the owner's wording.
3. After item 6: the Version URL and the suite result.

## Estimate

Items 1-3: about an hour, most of it the build and the page modules. Item 6
and the suite: about an hour. Items 4-5 wait on the owner.
