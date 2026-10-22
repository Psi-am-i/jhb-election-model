# Blind review of what a deploy would ship now

Committed before the review runs. Reissued verbatim or not at all. You have
the repository; you do not have the lead's reasoning.

## What you are reviewing

`env -u CLOUDFLARE_API_TOKEN npx wrangler deploy`, run from the repository
root at the current HEAD of branch `remediation`, would upload `site/` as
static assets and the Worker in `src/worker.js` (see `wrangler.toml`). The
live site is the 27 September edition. The question:

**Is everything under `site/` at HEAD correct, consistent, safe to make
public, and what the owner intends to publish?**

Where to look:

* `git log --oneline fbb829e..HEAD -- site/ src/worker.js wrangler.toml`: what
  changed in the shipped tree since the live edition.
* The freeze edition's pages (`site/*.html`), published to the ledger as run
  `r-c68c627d287e` (MODEL-LOG §1.282). A blind review (R4) and its fix check
  already covered them (`audits/2026-09-29-f11/R4-brief.md`); do not repeat
  that review. Check only that the pages are the ones that review approved
  and that nothing changed in them afterwards.
* Files added under `site/` since then: `site/draws/` (the interactive's
  exported draws, MODEL-LOG §1.283) — no page links to them yet.
* `site/_headers`, `site/robots.txt`, `site/changes.json`, `site/regimes.json`.

## Questions

1. Is every file under `site/` intended for the public, and does any expose
   something it should not (internal paths, machine names, tokens, personal
   data, unpublished figures)? Check `site/draws/*/manifest.json` and
   `site/draws/index.json` in particular.
2. Do the pages match the edition the ledger recorded (`publications/joburg/
   ledger.jsonl`, run `r-c68c627d287e`), with no change after the publish?
   `src/deploy_check.py` is the project's gate: run it and say what it
   checks and what it does not.
3. Is anything shipped that no page references, and is that a problem
   (size, cost, crawlability, confusion)? Should `site/draws/` ship before
   the page that uses it exists?
4. Does the Worker (`src/worker.js`) route and serve these files correctly,
   including content types (`site/_headers`)? Would anything 404 or be
   served wrongly?
5. Anything else that makes this deploy wrong, misleading or unsafe.

## Rules

Read-only. Do not run `wrangler`, `build_site.py` without `--out` to a
scratch directory, `--publish`, the model, or anything that writes under
`data/` or `site/`. `src/deploy_check.py` and `build_site.py --out <scratch>`
are safe. `.venv/bin/python` for Python. Do not delegate.

## Return

A verdict — ship as is / ship after named fixes / do not ship — and the
findings behind it, each with the file, the evidence, and the fix.
