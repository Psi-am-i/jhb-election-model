# Review before the rebuild, 2026-10-21

Owner, 2026-10-21: "get a review of that and everything we have done so far
before we start rebuilding." Written before the reviewers start; not amended
after.

**The range.** Every commit on `remediation` after `3357a5ee` (the merge base
with `site-r11`, whose UAT version d22294e0 carries the 16 October model) up
to the commit named in each reviewer's prompt. `git log --oneline 3357a5ee..HEAD`
lists them; `git diff 3357a5ee..HEAD -- src tests cities judgements` is the
code.

**Rules for reviewers.** Read-only: edit no file, write nothing into `data/`.
Do not delegate. Use `.venv/bin/python`. Do not run `compare_history.py`,
`montecarlo.py` as a script, or anything with `--emit` (each writes shared
artefacts). Unit tests and in-process calls of `run_model` with a scratch
`run_dir` are allowed. Report each finding with file:line, what goes wrong,
a concrete failure, and whether it was confirmed by running or reading.
Say plainly when you find nothing.

## Reviewer A: the code that moves the forecast

The changes in the range that reach a forecast number: the newcomer width by
anchor class; turnout entering the vote and its revert; registered voters split
by census group shares; the by-election weight ½ for every party; no
by-election movement for a party with no earlier record; the 2016-cycle
by-election fetcher; and whatever `src/pools.py`, `src/width_record.py` and
`src/montecarlo.py` changed with them.

Questions:

1. Does each change do what its MODEL-LOG entry and its JUDGEMENT-CALLS entry
   say, for every party and every city-year it reaches, and nothing else?
2. Is anything left behind by the turnout revert (b325d65) that still reads
   or writes the reverted mechanism?
3. Are there inputs whose staleness nothing would detect at the rebuild
   (artefact keys that omit a file that feeds them)? The rebuild re-emits the
   pool specs, the width record, `bye_value.json` and the group-share record.
4. Do the tests added or changed in the range assert the numbers they claim,
   and would each fail if its mechanism were reverted?
5. Anything else that would make the rebuilt forecast wrong while it looks
   right.

## Reviewer B: the record and the experiments

MODEL-LOG §1.314 onward, the pre-registrations under `prereg/` dated
2026-10-16 onward and their scoring, the JUDGEMENT-CALLS entries those touch
(§A59, §A60, §SJ1, §F6, §A23), `OWNER-DECISIONS.md`, and the three audit
experiments: `audits/2026-10-20-byelection-2021-backtest/`,
`audits/2026-10-20-byelection-weight-measured/`,
`audits/2026-10-21-scaling-by-uncertainty/`.

Questions:

1. Is every number in those entries reproducible from the artefact or run the
   entry names? Re-derive the decisive ones from the saved results.
2. Was each pre-registration committed before its run (check commit order
   against the results' timestamps) and scored against its own wording?
3. Do the experiment scripts measure what their pre-registrations name?
4. Does `OWNER-DECISIONS.md` state each item's context and evidence correctly,
   and does any item claim more than its evidence?
5. Do the documents agree with each other and with the code (a mechanism
   described in MACHINERY.md or JUDGEMENT-CALLS that the code does not do, or
   the reverse)?
