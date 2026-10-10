# Release brief: share images, reader badges, home introduction (2026-10-10)

Owner-approved 2026-10-10 ("ok go ahead"): option B, the 597ec38 tree
(slices A, B, B2a; no model batch), with share images, reader badges and the
home introduction. QC.md §4b applies throughout.

**Tree.** Worktree `/Users/simondavis/projects/atlas-jhb-site-release`,
branch `site-release` (597ec38 + 37ef09b, audits only). Its `data/` is a copy
with the 27 pre-batch specs and the pre-batch `citywide_2026.json` restored
(`pools_2026.json` sha256 96c73310…, the live `registration_sha256`). Work only
in this worktree. Never touch `/Users/simondavis/projects/atlas-jhb-election-model`
(the batch tree) or its `data/`. `.venv` is a symlink to the main tree's.

**Step 0 is done** (coordinator): a site build to `--out` reproduces the
committed `site/` apart from the "generated on" dates.

## Items

1. **A share image per page** (BRIEF.md item 9; `OG-IMPLEMENTATION-SPEC.md`
   §§2-6 with its addenda, built as its Option A).
   - New `src/og_pages.py` and `src/og-pages.mjs`; a node `toPNG` split out of
     `render_cards.mjs` without the fixture; primitives exported from
     `share-card.js`; `page_og` writes the image and alt tags.
   - Images at `/og-page/<slug>-<hash>.png`; the build refuses on a node failure.
   - Forecast card: ANC/DA most seats, one party alone, and the four approved
     coalitions (`e78f470`). New figures are tokens computed from the existing
     draws, registered where tokens are generated; none typed.
   - Claims index and article layouts.
   - **Owner defaults (2026-10-10):** no per-claim images in this release (the
     claims page gets one image); home, commentary and document pages keep
     `og.png`; articles without a designed visual get headline only (Laingsburg's
     bars dropped unless IEC tokens already exist); the interactive card shows our
     prediction's ward map; badges in the colours of the owner's files; the
     prediction seal is placed as the spec's default.
   - *Acceptance:* `tests/test_og_pages.py` covering spec §6 items 1-6, each
     with a constructed violation that is caught and goes quiet when reverted.
     **First checkpoint: one `toPNG` of an owner badge; report it and wait.**
2. **Reader badges** (`BADGE-DECISION.md`).
   - Boldest single call against `middle_seats`; bands 45/30/15/5%, an edge
     takes the higher band; the owner's `reader-*.svg`
     (`audits/2026-10-07-stamp-design/owner-stamps/2026-10-10/svg/`) on the
     share card and the arrival view, naming the party and seats.
   - JUDGEMENT-CALLS entry superseding §N6 and amending §N3.
   - Seat Worker copy resynced (`sync_seats_py.mjs`), not deployed.
   - *Acceptance:* `test_reweight` holds the four edges and the eight
     constructed forecasts in BADGE-DECISION's table; share-card node tests by
     file.
3. **Home introduction:** NOT in this writer's scope. The coordinator brings
   the text to the owner; it is built after approval.

## Process (QC.md §4b)
- **Write, then stop.** After editing, commit on `site-release` and report the
  diff summary. A reviewer reads the diff against this brief before ANY build
  or test beyond the first-checkpoint `toPNG` and module-import self-checks
  (`node -e 'import("./interactive/js/x.js")'`).
- After review: checks cheapest first, time-boxed; a check failing after one
  fix stops the run.
- No inline CSS/JS, no typed numbers, one definition of anything.

## Out of scope
The model batch (anything from `remediation` beyond the two audits
directories); any re-emit, `run_model`, `compare_history`, or draws re-export;
the batch's by-election wording (the existing 40% copy stays); BRIEF items
1-4, 6-8; the EFF claim; per-claim images; deploy.

## Rules
- Do not sub-delegate. `.venv/bin/python` only.
- End each commit message with:

      Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>

## Return
Commit hashes, the first-checkpoint PNG path, the diff summary by file, and
anything in the spec you could not follow.
