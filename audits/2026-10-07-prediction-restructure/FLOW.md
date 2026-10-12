# Flow: building the prediction brief (2026-10-08)

How `BRIEF.md` (revision 3) gets built. The owner's terms: fast without being
rash; the coordinator (Claude, this session) coordinates and reviews; the owner
reviews that review; more reviews are called if needed; then action; repeat.

## Roles

| role | who | writes |
|---|---|---|
| coordinator | this session | the brief, the specs it accepts, merges, the review of every step |
| designers | agents, parallel, read-only | specifications, never edits |
| reviewers | agents, parallel, read-only, blind | findings on a brief, a spec or a diff |
| writer | one agent at a time, in the main tree | code, tests and records for one step |
| owner | Simon | approves each review before action |

**Why one writer at a time:** `data/**` is gitignored, so a worktree has no data
and its tests prove little. Two writers in one tree collide (CLAUDE.md §3).
Analysis is parallel and application is serial.

## The loop, per step

    1. design / review     agents in parallel, read-only, same brief verbatim
    2. coordinator review  re-derive the decisive points; write a synthesis
    3. owner review        approve, amend, or call another review
    4. write               one writer; stops after editing
    5. diff review         a fresh agent reads the diff against the brief, blind
    6. checks              the tier the step's files demand (below), cheapest first
    7. record              MODEL-LOG / JUDGEMENT-CALLS / MACHINERY in the same commit

A check that fails after one fix stops the step and comes back to the
coordinator (QC.md §4b step 4).

## Steps

| step | content | runs in parallel with |
|---|---|---|
| **S0** | guard and provenance review of BRIEF.md: two agents (`review/S0-*`) | owner reading this flow |
| **S1** | specs, three designers: (a) rule A + both ballots in the draws; (b) the new entry version through validator, seat service, schema, scorer, cards; (c) sealing ours and the `/forecast` bar | each other |
| **S2** | write Phase 1 in three serial slices: (a), then (b), then (c), diff review after each | the Phase 2 design, read-only |
| **S3** | Phase 2 specs, then one writer | Phase 3 design |
| **S4** | Phase 3, one writer | — |
| **S5** | one UAT build of everything; the whole suite once; owner UAT | — |

## When the whole suite runs, and why not more often

The whole suite runs **once, at S5**, on the settled tree, before promote. It is
the only check that sees modules no step touched, and counts are quoted from it
alone.

It does not run per slice. **Each slice runs the modules its files reach:**
`run_all.py -k` for the modules importing what it changed, and the interactive
node tests by file. The coordinator names the list before the writer starts, and
the diff reviewer checks it against the diff. The question asked at each slice
is "which tests can see this change?", and only those run.

Exceptions that bring a whole-suite run forward:

- a slice changes `src/montecarlo.py` beyond adding a recorded field, or any
  file `run_model` imports in a way that could move a draw;
- a slice changes a shared helper whose importers cannot be listed with
  confidence (`stats.py`, `build_site.py`, `seats.py`);
- the targeted modules fail in a way that suggests reach beyond the list.

In those cases it runs **in the background, with the tree frozen**: nobody edits
while it runs (CLAUDE.md §3). Design work for the next step continues read-only
meanwhile.

## What the owner sees

At each step: one synthesis of the reviews with the disagreements unsplit, the
coordinator's own check of the decisive points (what was verified and what was
not), and the decision asked for.
