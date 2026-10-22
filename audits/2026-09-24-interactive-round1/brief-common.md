# Common brief — interactive design round (read-only)

You are one of several parallel DESIGN agents for the Johannesburg 2026 council
election forecasting model. You return a SPECIFICATION. You make NO edits.

## Where things are
- Code (a clean read-only clone of the current branch):
  /private/tmp/claude-501/-Users-simondavis-projects-jhb-election-model/2661b1d6-dd08-4a2f-a244-f9fff8f94798/scratchpad/repo
  Read CLAUDE.md, README.md, ARCHITECTURE.md, MACHINERY.md, JUDGEMENT-CALLS.md,
  ITERATING.md and PUBLISHING-BACKLOG.md §9 and §10 first. §9 and §10 hold the
  owner's decisions on the interactive; they are binding.
- `data/**` is gitignored and NOT in the clone. The real data and the project
  venv are on the host `atlas`, reachable by `ssh atlas`, repo at
  `~/projects/jhb-election-model`, interpreter `.venv/bin/python`.

## Hard rules
- READ-ONLY on atlas. Never write inside `~/projects/jhb-election-model` on
  atlas: no `pools.py --emit`, no `montecarlo.py` CLI, no `compare_history`,
  no `build_*` scripts, no sweeps, no test runs (a full suite is running there
  now). You may read files there, and you may run SHORT read-only Python that
  imports modules and reads data (e.g. `run_model` called in-process with a
  small draw count, writing nothing), sending any scratch output to /tmp on
  atlas or to stdout.
- Do NOT sub-delegate. Do not spawn agents.
- Never judge anything against the published forecast, a freeze, a golden or
  any earlier output. The only standard is real election results, using only
  data from before that election.
- Fitting to a property of the WORLD (e.g. realised historical turnout range)
  is estimation and permitted. Fitting to a ratio defined against the model's
  own output is tuning and barred.
- Do not write numbers you did not measure. Every number in your answer must
  say where it came from (file:line, or the exact command you ran and its
  output). Mark anything argued rather than measured as ARGUED.

## What to return
A specification, under ~1,200 words, with:
1. The mechanism: exactly which function/input it enters, with file:line.
2. The decisive number(s) and how you measured them (command + output), so
   the lead can re-derive them independently.
3. What goes in JUDGEMENT-CALLS.md (any value the data does not force).
4. A falsifiable prediction, written as it would go into a pre-registration
   under `prereg/`: what the change will and will not move, against the world
   and the mechanism, never against a prior output.
5. The test(s) it needs — including, for any test that asserts absence, how it
   proves it scanned the right population, looked, and can see.
6. Coupling warnings: what else this touches (pools re-emit? other levers?).
7. Open questions that are the OWNER's to decide, stated neutrally.
