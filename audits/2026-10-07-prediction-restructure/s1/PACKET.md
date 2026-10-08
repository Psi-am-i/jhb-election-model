# S1 design packet: Phase 1 specifications

Issued verbatim to three designers, 2026-10-08. Each takes one slice.

## Ground rules

- **Read-only.** Edit nothing in the repository. Do not run `src/montecarlo.py`
  as a script, `src/compare_history.py`, `src/build_site.py`, `src/pools.py --emit`,
  or anything that writes into `data/`, `site/`, `content/`, `publications/`.
  Importing modules and calling functions in-process with outputs to your
  scratch directory is allowed. Use `.venv/bin/python`.
- **Do not sub-delegate.**
- Read first: `CLAUDE.md`, `QC.md` (§4b), `STYLE.md` rule 11,
  `audits/2026-10-07-prediction-restructure/BRIEF.md` (revision 4),
  `review/S0-SYNTHESIS.md` (the guards G1-G20, as amended by the owner's
  decisions at its end), and `FLOW.md`.
- Mark every claim **verified** (file:line or a command you ran) or **argued**.

## What you return: a specification, not edits

1. **Changes, file by file:** functions added, changed, deleted, with
   signatures and the behaviour in prose or pseudocode precise enough that a
   writer cannot choose differently. Name every caller you change.
2. **Records:** what goes in `MACHINERY.md`, `JUDGEMENT-CALLS.md`,
   `MODEL-LOG.md`, docstrings (CLAUDE.md §2).
3. **Guards:** each S0 guard your slice owns (listed below), as a test name,
   its population, its constructed violation, and its file.
4. **The test list:** the exact `tests/run_all.py -k` modules and node test
   files that can see your slice's change, and why each. Say whether anything in
   your slice falls under FLOW.md's whole-suite exceptions, and why or why not.
5. **Order and dependencies:** what must land before your slice, and what your
   slice hands the next. Files you touch that another slice also touches.
6. **Risks and open questions** for the coordinator, and an estimate.

## The shared interface (BRIEF.md, "The prediction object")

    ward_calls   one party code per ward, in the schema's x-ward-ids order
    ward_votes   {party: whole votes} on the ward ballot, OTHER included
    list_votes   {party: whole votes} on the list ballot, OTHER included
    seats        derived by the seat law; never stored as an input

Encoded once as the make-state `f`. Do not invent a second shape; if the
interface cannot work for your slice, say so as an open question rather than
working around it.

## Coupling warnings

- `src/montecarlo.py` is touched by slice A only.
- `src/share-edge.js` is likely touched by slices B and C; say which functions.
- `interactive/js/make-state.js`, `builder-state.js` and `make.js`: B owns the
  encoding; A's hand-off and C's card read it.
- Served copies must stay in step: `interactive/tools/sync_py.mjs` PAGE_FILES
  (the page's Python), `worker-api/tools/sync_seats_py.mjs` (the seat Worker's
  copy of `reader_seats`/`reweight`), and anything `deploy_check` ships.
- The seat law has one definition (`seats.py`, `montecarlo.allocate_with_overhang`,
  `reader_seats`); your slice must not create a second.

## Slices

**A: rule A and both ballots in the draws.**
- `run_model` records each draw's two ballot totals.
- `export_draws` writes whole-vote ward and list blocks for every cell, and
  lifts the combined-share refusal.
- One rule-A function (proposed `src/prediction.py`) taking draws and optional
  weights and returning the prediction object.
- Its callers: `build_make` (the start), `score_forecasts.model_forecast`, and
  the page's hand-off in `interactive/pyboot/page.py`.
- `start_rule.py` retired.
- One tie rule.
- OTHER kept in the pool.
- Reproduce §1.290's backtest table through the new function (the backtest
  script is in `backtest/`).
- Guards owned: G1, G2, G3, G4, G5, G6.

**B: the reader entry, new version.**
- The make-state encoding of the prediction object.
- The editor's two vote rows: readers enter percentages, converted to whole
  votes with stated ballot totals (which totals, and from where: specify).
- The seat Worker (`worker-api/seats-py`) and `reader_seats` reading two
  ballots.
- The refusals (ward winner with zero ward vote or zero list vote) and the
  allowed-with-a-note case.
- The stored entry and its version column (D1 migration).
- The validator, and the placeholder schema in `worker-api/generated/`: check
  whether the account store that imports it is in use, then retire or
  regenerate it.
- `score_forecasts` reading the new fields, with key 3 on the list ballot.
- The export-then-clear of existing D1 entries, as a script whose run is an
  owner-approved step.
- Guards owned: G7 (the encoding side), G8, G12, G13, G14, G15, G20.

**C: our sealed prediction and `/forecast`.**
- The manual seal command and `publications/joburg/seals.jsonl`.
- `rank_entries` marking ours by the ledger and refusing on disagreement.
- Removing the single simulation from `/forecast` (bar, strip, map inset), with
  the `ballots.typical.*` tokens retired with a reason, and the replacement
  pointer reading the prediction object.
- Durable counting of reader seal storage failures.
- The card-image check after promote.
- Guards owned: G7 (the card and seal side), G11, G16, G17, G18, G19.

## Amendment 1 (owner, 2026-10-08), slice B

The owner, verbatim: "can we not have our vote prediction interface enforce
this? each ward has a known register. So if they paint various wards there
shoudl be a cheap check on hwo many votes that is per ward based on past resulst
and current register. That will at least keep the sliders bounded to a
reasonable degree. Id also posit that its rare for people to split their vote
so 1 almost always is 2'"

Coordinator's measurement (Johannesburg, cleaned IEC files, citywide ward share
minus list share): 2016, every party within 0.9pp; 2021, main parties within
1.4pp except ActionSA −4.1pp (18.1% list, 14.0% ward); independents about 1.3%
of the ward vote, no list vote.

Slice B's specification must therefore cover:

1. **One vote row by default.** The list vote follows the ward vote. An
   optional per-party list adjustment, bounded by the ward-list gaps real
   elections have produced (derived from the panel's cleaned files, not typed).
   Independents: ward ballot only.
2. **Sliders bounded by the painted map.** Each ward's expected votes come from
   its current roll (`archive/iec-registration-*`, joined through
   `montecarlo.ward_parts`) times an expected turnout from past results. A party
   painted to win a ward needs at least a winning share there; the minimum is
   derived from the lowest winning shares in real wards across the panel. Its
   votes in wards it does not win stay below that ward's winner. Together these
   give each party a citywide floor and ceiling that move as the reader paints,
   computed in the browser, cheaply.
3. **Where the derived bounds and their cut-offs are recorded** (JUDGEMENT-CALLS
   for any quantile chosen), and the guard that proves the bounds come from the
   data and change when the data does.
4. Whether the "allowed with a note" case still exists once the sliders are
   bounded, and what the refusals become.
