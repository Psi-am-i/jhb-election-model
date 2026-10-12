# Archive — superseded, kept for the record

Nothing in here is current. It is kept because deleting a superseded document
destroys the record of why a decision was made, and this project's rule is that
`MODEL-LOG.md` is the record of record.

**Moved here 2026-08-23**, after an exhaustive audit found each of these was
still in the working tree, still linked or still served, and describing a model
that no longer runs.

| path | what it was | superseded by |
|---|---|---|
| `original-plan/joburg-prediction-model-plan-v2.md` | the original design document, 2026-08-04 | **`MODEL-LOG.md` Appendix A**, which contains it verbatim — every line over 40 characters was confirmed present there before this was moved |
| `original-plan/joburg-prediction-model-plan-v2.pdf` | the same, as PDF — 13.6 MB, about 90% of the repository's tracked bytes | as above |
| `superseded-docs/METHODOLOGY.md` | "the review brief", 2026-08-03, last touched 2026-08-06 | `MACHINERY.md` for mechanism, `docs-public/methodology.md` for the reader edition. It was never in `CLAUDE.md`'s routing table, which is why it stopped being maintained, and it typed a dozen figures from before the level shrink, the contestation correction and the 2016 ingest |
| `superseded-docs/EXPANSION.md` | the phase-2 multi-city plan, 2026-08-07 | steps 0–4 shipped. Its "what is wrong on the live site" table had itself gone stale in **both** columns, so a reader could take its right-hand side for the current model |
| `superseded-docs/Graph Engineering.txt` | a generic essay on LLM agent workflow design | reading material, not a project document; its conclusions were in `ARCHITECTURE-PROPOSAL.md`, now in `rejected/` |
| `superseded-docs/review-original-excerpts.md` | excerpts staged for a compare page | third copy of the same 2026-08-04 text |
| `superseded-pages/model-review.html` | the 2026-08-04 technical audit, linked from the live review page as *"the full technical audit"* | **describes the EXPAND rule** — council growing to ~281, threshold ~141. The model uses the deduct rule and the live page says so. It was contradicting the site it was linked from |
| `superseded-pages/forecast-interactive.html` | the interactive, frozen 2026-08-04 | byte-identical to the former `site/dev/interactive.html`; both carry deleted levers (`paUplift`, `turnout_tilt_da`). See `PUBLISHING-BACKLOG.md` §1 |
| `superseded-pages/site-dev/` | the same file, **served** under `/dev/` | as above |
| `superseded-pages/site-drafts/` | four pages **served** under `/drafts/`, produced by no build | `build_site.py` only sweeps `site/*.html`, so subdirectories were never cleaned. They carried the dead expand-rule copy — "281" 34 times in one file. This is the `site/plan.html` failure repeating |

Also removed from tracking on the same day: `.wrangler/cache/wrangler-account.json`,
a build cache carrying a Cloudflare account id and an email-derived account name,
and the empty `notebooks/` placeholder.

## `rejected/`

Documents whose recommendation was examined and **not** taken. They are kept
because the reasoning is the record, and because a rejected argument that is
deleted gets re-made.

| file | why it was rejected |
|---|---|
| `ARCHITECTURE-PROPOSAL.md` | 2026-08-18. Recommended deferring the restructure and argued against declared interfaces. Two of its five arguments survive and are carried into `ARCHITECTURE.md` — no scheduler, and the draw loop stays whole. Three fail: it conflates reading with verifying, its 3-of-5 manifest table scores a different artefact, and "a refactor cannot improve prediction" is a category error. Its own deferral condition is now met by `src/freeze.py`, and `run_model` grew 863 → 1,099 lines while the work was deferred. |
