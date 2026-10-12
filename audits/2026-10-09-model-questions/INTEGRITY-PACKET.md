# Model integrity review packet

One reviewer, read-only, running alongside the model investigation (`PACKET.md`
in this directory). Issued 2026-10-09.

The owner, verbatim: "get a reviewer to look at whether the model is accurately
running or missing anything at the same time."

## Ground rules
- Edit nothing in the repository. Write only to
  `audits/2026-10-09-model-questions/integrity/` and scratch.
- No `montecarlo.py` run as a script, no `compare_history`, no `build_site`, no
  emit. In-process runs are allowed, with output to scratch only.
- Use `.venv/bin/python`. Do not sub-delegate.
- Mark every claim **verified** or **argued**.

## Questions
1. **Does the model run what it says it runs?** For every mechanism `MACHINERY.md`
   and `JUDGEMENT-CALLS.md` describe as live, show from an in-process run (the
   published seed, a few hundred draws) that it fires, for the parties and pools
   it should, and how much it moves. Use the `--run-dir` trace stages and the
   guard counters (`ModelRun.guards`). List every documented mechanism that does
   not fire, or fires for fewer members than claimed.
2. **What is missing?** Compare what a real Johannesburg election varies with
   what the model draws:
   - turnout by group and place;
   - each party's support by group;
   - new parties;
   - candidates;
   - ward-level local effects;
   - split tickets between the ward and list ballots;
   - spoilt ballots;
   - registration changes.

   For each, say whether the model draws it, fixes it, or ignores it, and what
   the published draws imply about it against real results (40 metro files).
3. **Silent fallbacks and defaults** on the run path: defaults that apply when an
   input is absent, constants that read as measured but are typed, and guards
   that count but never fire. CLAUDE.md §4b's `levels._citywide` returning `{}`
   is the precedent.
4. **The guards.** Spot-check five guards on the run path by a constructed
   violation in scratch: are they blind?

## Return
Findings ranked by severity, each verified or argued, with what it does to the
published forecast where measurable.
