# Final review before the deploy: read it as someone looking for fault

Committed before the review runs. Reissued verbatim or not at all. You have
the repository; you do not have the lead's reasoning.

## Your stance

You are a hostile but fair critic: a rival analyst, a party spokesperson whose
side looks bad, or a journalist looking for a story about a flawed election
model. You want the one thing you could quote to discredit this work. Find
it, and anything else a critic would fixate on. Glaring errors first.

## What is under review

1. **What the deploy ships now** (`env -u CLOUDFLARE_API_TOKEN npx wrangler
   deploy` from the repository root at HEAD, branch `remediation`): the
   public pages in `site/` (the published freeze edition, MODEL-LOG §1.282),
   `site/_headers`, `site/.assetsignore` (which should keep `site/draws/`
   from being uploaded — check that this is how wrangler behaves for this
   project's `wrangler.toml` and wrangler version in `package.json` /
   `node_modules`, if present), and the Worker `src/worker.js`.
2. **The fixes made since the last reviews**, especially:
   * `3f4aafe` (the deploy review's fixes: `_headers`, the guards);
   * `f5347a7` (precision ceiling 2.5 seats; slider stop; `.assetsignore`);
   * the freeze edition's claims and correction as published: the ANC
     "Not close." claim and its dated note, the red-lines "two-party"
     sentence and its correction on `/corrections`, the home page's
     "dead heat" line, the coalition table, the re-scored track record on
     `/about` and `/methodology`.
3. **The interactive that will follow** (`/play/`, built by
   `src/build_play.py`, not yet deployed; `interactive/`, `src/reweight.py`,
   `JUDGEMENT-CALLS.md` §N1–§N2, `audits/2026-09-27-interactive-levers/
   DESIGN-decided.md` §11–§15). Read it as a critic would read it on launch
   day.

## Questions

1. What is the single most damaging thing a critic could say about the
   published site as it would be after this deploy? Quote the page text or
   figure.
2. Any figure that contradicts another figure anywhere on the site, any
   claim the numbers do not support, any wording that overclaims, any date
   or provenance that cannot be backed.
3. Any way the deploy could go wrong: a file served wrongly, a file shipped
   that should not be, a page that breaks, something private exposed.
4. For the interactive: anything a critic would call misleading, arbitrary,
   partisan, or broken — e.g. the precision ceiling, the poll dial, the
   by-election column, the unpaired cells, the default state.
5. Anything else you would fixate on.

## Rules

Read-only. Never run `wrangler`, `--publish`, the model, `compare_history`,
or anything that writes under `data/` or `site/`. `src/deploy_check.py`,
`build_site.py --out <scratch dir outside the repo>` and reading the live
site with `curl` are allowed. `.venv/bin/python` for Python. Ignore
`.claude/worktrees/`. Do not delegate.

## Return

A ranked list: glaring (fix before deploy), serious (fix soon), and what a
critic would fixate on even if defensible. Each with the page or file, the
quoted text or evidence, why a critic would seize on it, and the fix.
