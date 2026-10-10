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

## Addendum, 2026-10-10 (owner-approved text and two methodology changes)

3. **Home introduction: approved text** (owner, 2026-10-10), replacing the
   draft's corresponding paragraphs; the draft's first paragraph ("What this
   is") stays as drafted. Figures in braces are tokens, never typed:

   > The model simulates the election thousands of times. Each run uses
   > different values for turnout and for every party's support, but not just
   > any values: each is drawn from how far turnout and parties have moved in
   > past elections.
   >
   > Run on Johannesburg's last three elections, it called
   > {wards called 2011} of {wards 2011}, {… 2016} of {… 2016} and {… 2021} of
   > {… 2021} ward winners.
   >
   > It uses as few judgement calls as possible. Each one is listed, with its
   > evidence, on the [judgement calls] page, and several can be changed on
   > your forecast.

   - The ward figures come from `data/processed/history.json`, joburg rows,
     `wards.called` / `wards.n_wards` (its `pool_artefact_keys` carry
     pools_sha c70b8fc5, the live model's specs). Add a token source for it in
     `stats.py` (one resolver, tested), registered in `content/joburg/stats.toml`.
   - "[judgement calls]" links to the methodology page's "The judgement calls"
     section (anchor).
   - No 8-metro totals and no "34%" on the home page.
   - *Tier:* cosmetic plus the stats resolver's test.

4. **Methodology (docs-public/methodology.md), drafted for the owner, built
   only after he approves the wording:**
   a. **Correction.** The page says the model "beats simple baselines, in
      cities it was not built for". `validation_2021.json` marks all eight
      cities `in_sample: true`, and `history.json` marks all 24 city-years
      in-sample (settings chosen with those elections in view). Replace the
      claim with what is true, and add a corrections entry under the site's
      correction rules (heading = the error; published date; corrected date;
      what was wrong and what changed, nothing else). Find the date the claim
      first went live from the publication ledger / git history.
   b. **Per-metro table** in place of the combined totals (297 / 353, 7 of 8,
      34%): for each metro, the model's seat error and the best baseline's,
      from one artefact, as tokens. Say which artefact and why.
   c. **Small parties' range.** A short note: in the simulations, established
      small parties sometimes reach shares no established small party has
      reached in the record (parties under 1% at one local election: none
      reached 5% at the next); a fix is in progress. Figures as tokens where
      they are model outputs; the record figures cite their source.
   Return the drafted wording in your report before building it.
