# A Model for forecasting Local Government Elections in South Africa

## Documentation is part of the model, not a description of it.

**The model's ability to predict is above everything else.** 
It is tested by comparing it's predictions to real elections - and using only data from before that election. Variables are ideally derived and not hard coded. When this is not possible, all hand written variables are recorded in Judgement-Calls.md to make them obvious.

**The model is evolving and it's forecast evolves with it**
The published forecast is not 'correct'. The only measure of teh model is how well it predicts real elections.

**Whenever the model changes, the documented record must change in the same commit.** 
Not afterwards, not in a cleanup pass. A stale document here is worse than a missing
one. This has already gone wrong more than once. `MACHINERY.md` spent weeks
describing a level layer that no longer ran. The published forecast page carried
ten claims pinned to `turnout_tilt_da`, a lever deleted from `run_model`just as an example.

### Which file records what

| change | goes in |
|---|---|
| a **mechanism** — how something is computed | the function's docstring | `MACHINERY.md` |
| a **number** the data did not force | `JUDGEMENT-CALLS.md`, with status, evidence and how to check it |
| a **finding** — including a rejected one, and especially a negative result | `MODEL-LOG.md` (append; never rewrite history) |
| a change in **what counts as better** | `ITERATING.md` |
| a defect in the **inputs** | `DATA-QUALITY.md` |
| a new or changed **source** | `SOURCES.md`, with provenance |
| a **number or claim on the public site** | `content/<city>/stats.toml` as a token — never typed into prose |

`MODEL-LOG.md` is the record of record. If a thing was measured and rejected, it
belongs there with its number, so nobody spends a day rediscovering it.

### Non-negotiable

- **A rejected idea is written up with the measurement that rejected it.** Three
  of this project's most useful entries are negative results.
- **A constant that is not measured is declared** in `JUDGEMENT-CALLS.md`, or it
  will be mistaken for one that is — and then none of them are trusted.
- **Anything that cannot be tested by the harness is labelled as argued, not
  tested**, wherever it is quoted. `w_bye` and the first-local-election bias
  correction are both in this position.
- **Never type a model figure into prose.** It goes stale silently. Register it
  as a stat token; `build_site.py` audits for typed figures and will name them.
- **Re-record a golden test deliberately and say why in the file.** A silent
  re-record destroys the only guard on the prior.

## Two backlogs, and they do not mix

`PUBLISHING-BACKLOG.md` holds the presentation layer — the interactive, the live
page, the stat tokens. 

## Iterating, not publishing

### ⛔ NOTHING THIS MODEL HAS EVER PRODUCED IS A STANDARD OF CORRECTNESS

**Never evaluate work by comparing it to the published forecast, to
`data/processed/forecast_frozen.json`, to a golden, or to any earlier output of
this model. The only standard is backtesting against REAL ELECTION RESULTS.**

**Agreement with a previous output is evidence of nothing**
When a change moves a number, the question is always "does the backtest against real results improve?" and never "does it still match?". It is cycle-replicated, against the keys in `ITERATING.md`.

**A freeze of results** is only a **tripwire** that says *go and look* when
something moved unexpectedly. A tripwire is not a gate. It never decides whether
a change is right.

Read `ITERATING.md` first. Does the current predicts PAST elections better than the previous
iteration one and better than the naive baselines? This is the main criteria of shipping changes. Read the amendment at the top of `ITERATING.md` before judging any change.

## BEWARE CONTENTIION - SHARED ARTIFACTS - nobody measures while it writes

`data/processed/pools_*.json` is **precomputed**. Changing `src/pools.py` does
nothing until you re-emit it, and re-emitting it changes the baseline of every
measurement anyone else is taking at that moment.

A lever sweep will return **different answers on two identical
runs** if another worker is re-emitting the artefacts underneath it.
Partitioning work by *file* is not enough — `pools.py` and `compare_history.py` do not overlap as files and collide completely as work.

When more than one worker is active:

* **Exactly one** may re-emit `pools_*.json`, and it owns them for the duration.
* **Nobody else runs the model, `compare_history`, or any sweep** while that is
  true. Verify at unit level instead, and say so.
* The re-emit and the canonical measurement happen **once, at the end, on a
  settled tree** — and every number quoted anywhere must come from that run.

**Contention is managed by making agents READ-ONLY when they would collide.**
Three agents writing to `montecarlo.py` collide whatever regions they occupy,
because each writes the whole file. **Parallel analysis plus serial application
is the reliable shape**

A number measured against a moving artefact is not a measurement but reads exactly like one.

**Since 2026-08-18 the artefacts say what built them.** Every `pools_*.json`
carries an `artefact_key` — city, target, a hash of `config/dimensions.toml`,
and a hash of `pools.py`'s code with comments and docstrings ignored — and a run
prints a named reason when it does not match. That does not replace the rule
above: it stops a stale result being *believed afterwards*, it does not stop the
artefacts moving under a measurement in progress. Re-emit with:

    .venv/bin/python src/pools.py --city <city> --target <year> --emit

Emission is deterministic — re-emitting every spec changes nothing but the key —
so the hazard is re-emitting *while someone measures*, not re-emitting. 

**A CODE change to `pools.py` invalidates every one of them, and the guard will
say so.** 

**A `pools.py` CODE change is BATCHED, not taken when convenient.** What is waiting for the next re-emit window, and the procedure for taking it, is in `POOLS-REEMIT-QUEUE.md`. A comment-or-docstring-only change does not move the hash and does not belong there.

**The specs are not tracked by git.** They have no version history, which is why
the key exists.

**`compare_history` runs its sixteen city-years in parallel processes** (since
2026-08-18), which is safe because they only READ the specs — the rule above is
about who WRITES them, and that is still one worker at a time. 

## Running things

Use `.venv/bin/python`, never bare `python` — numpy is not on the system
interpreter.

    .venv/bin/python tests/run_all.py                  # the suite (~14 min)
    .venv/bin/python tests/run_all.py -k spine -k theta # just those modules
    .venv/bin/python tests/run_all.py -x levers         # everything but the slow one
    .venv/bin/python tests/run_all.py --list            # the module names
    .venv/bin/python src/compare_history.py            # votes and seats vs actual, 16 city-years
                                                       #   runs in parallel by default; --jobs 1 forces serial
    .venv/bin/python src/diagnose.py --city joburg --target 2021 --wards 0
    .venv/bin/python src/arrivals.py                   # the arrival machinery, scored alone
    .venv/bin/python src/contested_area.py             # validates the poll path's
                                                       #   contested-area conversion (§1.66)
    .venv/bin/python src/theta_residual.py             # the CONDITIONAL sd(log theta),
                                                       #   forward validated, against what
                                                       #   the model actually uses (§1.59)
    .venv/bin/python src/sweep.py                      # obvious-fault sweep

### ⛔ THE WORKING LOOP — the standard procedure for this project

**This is the procedure, not a per-task choice. One section at a time, and a section is not left until it is clear.**

    ROUND = design (parallel, read-only)
          → I check (re-derive the decisive number myself)
          → pollster reviews, BLIND where possible
          → apply only what the check and the review agree on
          → measure, and write the result up
          → iterate what is left then move to next section

1. **DESIGN — split across agents, in parallel, READ-ONLY.** One agent per
   finding or coupling group. Give them the coupling warnings explicitly; an
   agent that does not know `compress_levels` renormalises over `centres` will
   cheerfully propose widening a loop. Agents return **specifications**, not
   edits — see the contention rule below.
2. **⛔ I CHECK WHAT THEY RETURN, BY RE-DERIVING IT.** Not by reading the
   summary. This has changed the answer repeatedly and in both directions.
3. **THE POLLSTER REVIEWS EACH ROUND, AND BLIND WHERE IT CAN BE.** Not only at
   the end, and not only on substance. Give it the evidence base and the
   question; do **not** give it your conclusion. Two blind passes have now each
   found a publication-blocking defect the other reviewer missed entirely, and
   one of them **downgraded its own earlier verdict on better arithmetic**,
   which is the behaviour blindness buys.
4. **APPLY ONLY WHAT BOTH AGREE ON.** Where they disagree, the disagreement is
   the finding and it goes to the owner — do not split the difference.
5. **MEASURE, THEN WRITE IT UP.** `compare_history` adjudicates 16 city-years in
   about three minutes. **Prefer questions that instrument can settle, and be
   sparing with those it cannot.** A rejected idea is written up with the
   measurement that rejected it.

**PRE-REGISTER THE PREDICTION BEFORE THE RUN, IN WRITING.** It is what turns a
result into evidence. 

### The three ultra reviews — spend them on code that moves numbers

**The owner holds three `/code-review ultra` runs. They are user-triggered and
billed; I cannot launch one, so ASK when the moment arrives rather than assuming.**

A deep multi-agent review to be used where a defect would be expensive and where this project's normal safety nets do not reach — which is precisely where a change **moves forecast numbers**, because
`forecast_frozen.json` is explicitly barred from arbitrating and the backtest cannot tell a fixed bug from a new one.

**BOOKED FIRST: the `pools.py` re-emit batch** — the 2000/2006 `metro_file`
reader plus the roster/reach seam. **Its brief is written and frozen at
`audits/ULTRA-REVIEW-1-pools-reemit.md`.**

* **Read the brief before writing a line of the batch, and do not amend it
  afterwards.** If the hunt list is visible while the code is written, the code
  gets written to pass it and the review inherits a blind spot shaped exactly
  like the brief.
* **Run it from a branch carrying ONLY the batch**, not from here:

      git checkout -b pools-reemit          # off this branch
      # write the batch, archive the 18 current specs, then:
      /ultrareview splinter-rule-and-historical-tail

  `/ultrareview` takes a PR number, a branch, or nothing — **there is no way to
  pass it instructions**, which is why the brief lives in the repo and is
  pointed at from here. With no argument it diffs against `main`, which on this
  branch is 158 files and 88k lines and is **refused outright** (limits: 500
  files, 8,000 lines).
* **Before the emit, never after.** Afterwards the baseline has moved and there
  is nothing clean to compare against.

**Contention is managed by making agents READ-ONLY when they would collide.**
Three agents writing to `montecarlo.py` collide whatever regions they occupy,
because each writes the whole file. **Parallel analysis plus serial application
is the reliable shape**; worktrees are the alternative when the files are
genuinely disjoint. Only one worker may re-emit `pools_*.json`, and **nobody
measures while that happens.**

### The review rule: agents check me, and the pollster checks the substance

**Standing instruction from the owner, 2026-08-28: *"same as before: split
between agent, you check them and pollster checks you (should just make that the
rule)"*.** So it is the rule, not a per-task choice:

1. **Split the work across agents**, one per finding or coupling group, and read
   their specifications rather than their summaries. Give them the coupling
   warnings explicitly — an agent that does not know `compress_levels`
   renormalises over `centres` will cheerfully propose widening a loop.
2. **CHECK WHAT THEY RETURN.** Re-derive the decisive number yourself before
   acting on it. This has repeatedly mattered in both directions: an agent
   caught §1.109 claiming to be an index when it was a summary, and an agent's
   own premise about F19's classification turned out to be unverifiable.
3. **The pollster reviews anything touching the FORECAST'S SUBSTANCE** — an
   estimator, a weight, a prior, a selection rule. Not plumbing. It found that
   F34's clamp is three times tighter than its estimate's own noise, and that
   the ρ weighting moves the answer by 0.065pp while correlating +0.46 with the
   thing it exists to neutralise. Neither was visible from the code.

### Run the targeted modules per change; run the SUITE once per commit

Every run prints a per-module timing table, because a suite that does not say
which module owns its runtime cannot be made faster on evidence. 

* **while iterating** — `-k` the modules your change can reach. Seconds, not
  minutes. `-x levers` alone is a 3x speedup if you are not touching a lever.
* **before committing** — the whole suite, once, for the whole batch. Several
  independent fixes can share one run; that is what `-k` buys, because the
  targeted run is what tells you which change broke something.

**A subset is not a suite run**, and `run_all.py` prints a banner saying so on
any partial run. Do not report one as the other.

**Before adding a print to find out what something is, ask for a trace.**

    .venv/bin/python src/montecarlo.py --city joburg --target 2021 \
        --run-dir /tmp/t                  # every stage's output, as JSON
    .venv/bin/python src/compare_history.py --run-dir /tmp/t   # one per city-year

`--run-dir` writes each stage of the run — the θ prior and its per-party
`sd(log θ)`, the spine's level and route per party, the centres before and after
the level shrink, the drawn means and bands, and every guard counter — to files
you can read without running anything again. It is **opt-in and changes no
number**: with no `--run-dir` the run is byte-identical, and `test_chain.py`
asserts it.

This exists because the alternative was re-running the whole comparison with a
print added — 499s serial, 169s parallel at 1500 draws — and that cost was being
paid on every investigation. It is a *record*, not a
check: it will happily record a guard that has gone blind. What catches those is
an assertion — and the trace is what makes assertions cheap to write, because
the quantity is already on disk.
