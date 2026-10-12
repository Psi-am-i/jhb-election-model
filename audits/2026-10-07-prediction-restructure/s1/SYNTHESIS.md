# S1 synthesis: Phase 1 specifications (2026-10-08)

Specs: `SPEC-A.md` (rule A, both ballots in the draws), `SPEC-B.md` (reader
entry v2, bounded editor), `SPEC-C.md` (sealing ours, `/forecast`). Each is
precise enough to write from. *Verified* marks a point the coordinator re-read or
re-ran.

## Where the specs conflict, and the resolution

| conflict | resolution |
|---|---|
| **OTHER.** B adds a 75th vote code. A finds that the simulations hold no OTHER party. | A is right. `OTHER` is `export_draws`' sum of parties that never win a seat, zero by construction (*verified*, `export_draws.py:11-22, 336-379`), and `run_model` has no such party. Every party enters the pool under its own code; "Others" is a display grouping only. S0 finding 3 was wrong; recorded as such. B drops D2. |
| **Ballot totals.** A keeps `x-total-votes`. B deletes it, and each prediction carries its own totals (the sums of its votes). | B, landing after A: A leaves `x-total-votes` as an interim, and B removes it. |
| **Who owns the seat law outside `run_model`.** | A creates `prediction.seats_of` as the one composition, and `reader_seats` delegates to it (no behaviour change). B then changes `reader_seats`' signature to two ballots. No second composition exists at any point. |
| **C needs the prediction for the `/forecast` pointer before `forecast.json` exists** (build order). | A exposes `build_make.our_prediction(draws)`, which `render_sheet` calls. |
| **C needs the entry format version from Python.** | B's D6: the schema carries `FORMAT` as a constant, and Python reads it there. |

## Order

A → B → C, one writer at a time, each diff-reviewed before its checks run.
- A: about 2 days, including a 24-minute backtest reproduction and three
  re-exports.
- B: about 2.5 days.
- C: about 1 day.

## Whole suite

**None of the three slices triggers an early run** (each argued in its spec):
- A adds two recorded fields to `run_model`, filled from values already
  computed. A one-off proof that no draw moved goes in MODEL-LOG.
- B touches neither `montecarlo` nor `seats`.
- C touches no `run_model` import.

The whole suite runs once, at S5. Each slice's targeted list is in its spec, §4/§5.

## Coordinator checks

- B's ward extremes re-derived: lowest winning share 23.6% (JHB 2021 ward 82),
  highest runner-up 47.8% (NMA 2006), over 40 files and 3,434 wards (*verified*).
  Caveat: merged independent rows could distort these extremes where several
  independents stood.
- C's seal facts: preview refusal and the `official` / `the model` name block
  (*verified*, `share-edge.js:382-384`, `blocklist.js:9-11`).
- Not re-derived: A's gzip sizes, M4's rounding misses, M9's interim re-seat, and
  B's turnout range. All four are reproduced by the writer's own tests or
  re-exports.

## Decisions for the owner

1. **Served file size.** Both vote blocks plus the existing list share come to
   1.70 MB gzipped, over the 1.5 MB budget. Dropping the list share, which is
   derivable from the list votes, gives 1.42 MB. **Recommended: drop it** (A).
2. **Record whole votes per draw rather than two totals per draw.** Shares ×
   totals miss the model's integers by up to 4 votes in about 2% of cells, so
   G2 could not be exact. These are values the loop already holds (A).
   **Recommended.**
3. **Exporting the old entries.** The repository is public and the rows carry
   names readers typed. Keep the export in gitignored `backups/` and commit only
   its metadata (time, count, sha, database id) (B). **Recommended.**
4. **Slider bounds:** the panel's extremes, so no real result is excluded
   (q_win 23.6%, q_run 47.8%, gap bounds −1.76 to +6.16pp), or a percentile
   (B). **Recommended: the extremes.**
5. **Our seal's name and the board.**
   - Our seal carries an empty name, because the blocklist refuses "official"
     and "the model". The board shows a fixed name for ours, from the ledger.
     The owner chooses the wording.
   - Only our last seal before polls open is ranked. Earlier ones are listed as
     superseded (C).
6. **The `/forecast` pointer:** our predicted seats for every seated party (rule
   11, no ranges), or a link with no figures (C). **Recommended: every seated
   party**, as tokens.
7. **Dormant prototype modules** (`f.js`, `api-stub.js`, `interactive/f/`) read
   the old format and are not served: retire them (B). **Recommended.**
8. **A fourth modal-winner site** in `montecarlo.main` (`ward_winner_probs.csv`)
   uses an unstable sort. Routing it through rule A touches the draw path's
   outputs, so it is exempted now and flagged for a later model-tier version
   (A).
9. **The tree is not clean.** The claims UAT build (`forecast-sheet.html`,
   `drafts/forecast-draft.html`, `site/claims.html`, `site/css/site.css`,
   `site/changes.json`, `NUMBERS-REVIEW.md`) is uncommitted. Slices A and C
   edit two of those files. Before the first writer starts, either release the
   claims update (upload to UAT, then publish) or commit the build as it
   stands.

## Facts corrected by S1

- S0 finding 3: there is no OTHER party in the model (above).
- The placeholder schema's account store is not deployed (B, from the Cloudflare
  listing), so it is retired.
- Seal storage is asynchronous: the D1 insert runs after the response (C), so
  the seal command retries its read-back.

## Owner's answers (2026-10-08)

1. **Drop the stored list share.** Nothing is lost: the list share is derived
   exactly from the list votes.
2. **Whole votes:** asked where and out of how many. Answer: citywide, for every
   party in every simulation, the ward-ballot and list-ballot votes, out of
   that simulation's votes cast on each ballot (about 985,000 each in our
   prediction).
3. **Old entries are tests.** No export is needed. They are cleared at the
   release step.
4. **Slider bounds:** the historical extremes, widened by 5 points either side.
   Lowest winning share 18.6%. Highest runner-up 50%: 52.8% capped, because a
   runner-up cannot exceed half. Gap bounds −6.76 to +11.16pp. Recorded in
   JUDGEMENT-CALLS as the owner's call.
5. **The board name for ours:** "WhySoSerious.City's Official JHB Prediction".
6. **The `/forecast` pointer** shows our predicted seats.
7. **The dormant prototypes** are retired.
8. Explained again; awaiting an answer.
9. Explained again; awaiting an answer. Slice A does not edit the dirty files,
   so it can start. The release must be settled before slice C.
