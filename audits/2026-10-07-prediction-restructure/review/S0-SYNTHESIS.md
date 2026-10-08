# S0 synthesis: guards, verification, provenance (2026-10-08)

Two reviewers, packet `S0-PACKET.md` issued verbatim: R1 (generated, consumed,
provenance) and R2 (knowing when something happens and when it does not).
**Coordinator checks:** marked *verified* where re-read or re-run in this
session; the rest is the reviewers' word.

## What the reviews found that changes the design

1. **Rule A has no producer in `src/`.** Only the audit script computes it. The
   brief's three callers do not exist yet. A further consumer the brief did not
   name: `rank_entries`, the card, the `/forecast` pointer and the served page
   copy (R1).
2. **Rule A needs whole vote totals per ballot per draw, and the served draws
   hold neither.** The §1.290 backtest averaged integer totals captured inside
   `run_model`. `site/draws/` holds a rounded list share only, and
   `eligible_parties` admits a party on `pr_votes > 0` (*verified*,
   `src/seats.py:56-68`), a test on totals that rounding can flip. So
   `run_model` must record per-draw ward and list totals, which is a
   `montecarlo.py` change: FLOW.md's whole-suite exception (R1 G2, R2 G3/G5/G6).
3. **The draws carry an OTHER column the roster does not.** `pr_share` and
   `seats/*` have 75 columns including OTHER; the roster has 74 (*verified*,
   manifest). `run_model` keeps OTHER in the quota pool; `model_forecast` drops
   it and renormalises. These seat differently (R2 G2).
4. **Three tie rules for a ward call exist today.** `model_forecast`: earlier
   in the schema roster (*verified*). `page._ward_calls`: earlier in
   `ward_parties` order by stable sort (*verified*, `page.py:206`). The audit
   script: earlier universe index. They agree only because both lists are
   alphabetical and no served ward is tied (R1).
5. **Our seal has no producer and no identity.** Only the live Worker holds the
   seal key, and previews refuse to seal, so the build cannot seal. D1 has no
   column marking ours, and the label is reader-typed. `rank_entries` would rank
   every version of ours (R1 G4, R2 G11-G13).
6. **Silent fallbacks on the path rule A will use:**
   - `make.js` `follow()` swallows an engine error and a refusal with a bare
     `return` (*verified*, `make.js:233-236`);
   - `startState` fills missing ward calls from the published ones;
   - `votesFromPercent` turns missing shares into zero or an even spread;
   - `storeEntry` failures are a `console.error` only;
   - `cardImage` falls back to the generic image without logging;
   - `aligned` scores an absent party as zero (R1, R2).
7. **There are two forecast schemas.** `worker-api/generated/forecast.schema.json`
   is a placeholder (14 parties, a different total vote; *verified*) and
   `worker-api/src/forecasts.js` imports it (*verified*). The page's schema has
   74 parties. Whether the account store that reads it is deployed: not verified.
8. **The single-simulation view has a third place:** the map's council inset,
   besides the bar and the strip (R2 G10). Its `ballots.typical.*` tokens are
   in the publication ledger, and `build_site` will refuse until they are
   retired with a reason: a guard working as designed.
9. **Retargeting `your-forecast` touches 50+ files** (R1, `git grep`), not the
   five the brief names. Committed stale files under `site/your-forecast/` would
   keep shipping, because `deploy_check` refuses only untracked files (R2 G9).
10. **Existing guards this blinds or that will fire.**
    - Blinded: the hand-off test (premise ends), `page.test.mjs`'s recorded
      hand-off fixture, `test_export_draws` and `test_served_draws` (no vote
      blocks), `test_chain`'s no-perturb test (two arrays only), and
      `yf_jump_check` (old page).
    - Will fire, correctly: the routing baseline differential and the
      `PAGE_FILES` both-ways test.
    - `declares.py` scans `data/processed` only, so nothing served or in D1 is in
      its population.

## Guard list (merged, deduplicated)

Each needs a stated population checked both ways, a constructed violation that
is caught and goes quiet when reverted, and a home. The reviewers' full text is
the specification; this is the index.

| # | guard | from | home |
|---|---|---|---|
| G1 | rule A is one function; importers equal the declared callers; an AST scan finds no inline modal/mean reduction outside a declared exemption list; a constructed tied ward resolves the same through build, hand-off and scorer | R1 G1, R2 G1 | new `tests/test_prediction_rule.py` |
| G2 | rule A on the served blocks equals rule A on `run_model`'s in-process totals: calls, whole votes per ballot, pool membership, seats; every cell carries both blocks | R1 G2, R2 G3 | `test_export_draws`, `test_served_draws` |
| G3 | a missing ballot block is refused by name, never zeros or a copy of the other ballot | R2 G4 | `page.test.mjs`, page test |
| G4 | OTHER: the rule applied and the mass per ballot are recorded; a toy where the opposite rule seats differently proves the test can see it | R2 G2 | `test_score_forecasts` + JUDGEMENT-CALLS |
| G5 | the combined-share refusal is lifted with `run_model` recording the tally, or kept with no served arithmetic over both blocks; never both | R2 G5 | `test_export_draws` |
| G6 | the trace and the no-perturb test see any new per-draw quantity; the realisation coverage assertion (QC.md §3) lands first | R2 G6 | `test_chain`, `test_stage_realisation` |
| G7 | our prediction is one encoded `f` with whole votes, and the build block, the page's opening state, the card and the sealed entry all equal `decode(f)` (votes and calls, not seats); a fifth consumer must join the set | R1 G3 | `make.test.mjs`, page test, `test_rank_entries` |
| G8 | the hand-off arrives or says why: complete payload or a visible refusal; never opens on our prediction silently | R1 G9, R2 G7 | `make.test.mjs` |
| G9 | redirect: every combination of link keys routes to exactly one named page with its query; key lists imported from `yf-url.js`, not retyped; routing baseline re-recorded deliberately | R1 G8, R2 G8 | `test_worker_routing` |
| G10 | no file outside a declared list names `your-forecast`; nothing served from the old directory; paths derived from one constant | R1 G7, R2 G9 | `test_site_structure`, routing test |
| G11 | no single simulation on `/forecast` (bar, strip, map inset); its tokens retired with a reason; the replacement pointer reads G7's prediction | R1 G10, R2 G10 | page test |
| G12 | entry version stored; the scorer refuses any version it does not read, naming the rows; a v1 body is refused with a version error | R1 G5, R2 G15 | `test_entries`, `test_rank_entries` |
| G13 | one schema: the placeholder is retired or regenerated and compared | R1 G6 | page test or worker test |
| G14 | a party winning wards must have a list share above zero, or its wards move silently to the D term | R2 G16 | seat service tests |
| G15 | scoring key 3 reads the list-ballot field: changing only the ward share leaves it unchanged | R2 G17 | `test_score_forecasts` |
| G16 | our seal: a committed ledger row per version (`seal_id`, time, `model_ref`, `draws_sha256`, `context_ref`, `v`, `f`), written by a post-promote step that reads the D1 row back; `rank_entries` marks ours by ledger `seal_id` only, ranks one, and refuses a published version with no seal or a seal whose `f` differs | R1 G4, R2 G11-G13 | `rank_entries`, `test_rank_entries` |
| G17 | reader seal storage failures are counted durably, and seals issued are compared with D1 rows on results night | R2 G13 | `share-edge.js` + a runbook check |
| G18 | card images: after promote our card answers 200 with an image; the generic fallback writes a reason | R2 G14 | routing test + deploy runbook |
| G19 | nothing served on `/forecast` posts to `/seal/1` | R2 G18 | page test |
| G20 | the D1 export before the clear carries export time, row count, sha and database id | R1 Q2 | export script |

## Decisions for the owner

1. **Votes, not shares.** Rule A and every entry carry whole votes per ballot.
   `run_model` records per-draw ward and list totals, and the combined-share
   refusal is lifted. This is a model change, so the whole suite runs in the
   background on a frozen tree before Phase 1's later slices build on it.
   **Recommended.**
2. **OTHER.** The draws carry a mass for parties outside the roster. Either keep
   it in the quota pool as the simulations do, shown as "Others", or drop it and
   renormalise as `model_forecast` does today. **Recommended: keep it**, as the
   simulations and a real count do. A reader's entry then has an "Others" row on
   each ballot.
3. **Ward winners against ward votes (R2's answer; R1 not asked).** Warn, don't
   refuse. Refuse only impossibilities: a ward winner with zero ward vote, or a
   ward-winning party with zero list vote. The warning test is derived from past
   results: the pairs of ward vote and wards won seen in real city-years, and a
   swing from the previous election's ward results. The cut-off goes in
   JUDGEMENT-CALLS. Our own prediction is run through it too.
4. **Sealing ours.** A post-promote step seals, reads the row back and commits a
   ledger row. "A version" is a distinct prediction, not every deploy. Edge
   cases need rules:
   - a publish too close to the lock to seal;
   - a rollback after the last seal.

   **Recommended:** our last publish before the lock is no later than a set time
   the evening before, and a rollback reseals.
5. **The placeholder schema** in `worker-api`: retire it if the account store is
   not in use, or regenerate it. To be checked.
6. **Old sealed links, after the clear,** open on our prediction with a "made by
   another version" note, and their previews show the generic image. Accepted?
   Nothing was advertised.

## Effect on the plan

- Phase 1 grows: the `run_model` tally, the seal step and ledger, G1-G8 and
  G12-G16. Estimate three days, not two.
- The path move (Phase 2) touches 50+ files; G10 makes it checkable.
- One whole-suite run moves forward, to after the `run_model` slice, because
  that slice touches `montecarlo.py`.
- The final whole suite at S5 stays.
