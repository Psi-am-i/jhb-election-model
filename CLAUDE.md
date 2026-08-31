# A model for forecasting Local Government Elections in South Africa

**This file holds only the rules a session would otherwise break by default.**
Everything else is in the record and is pointed at, not repeated — a rule
written twice is a rule that drifts.

**`README.md` is the map** — what this repository is, the reproduction recipe and
the table of every document. Two it does not list: `ARCHITECTURE.md` (the
structural argument about `run_model`) and `HANDOVER.md` (where the branch stands
today, and what to do next — start there).

---

## 1. The only standard is real elections

**The model's ability to predict is above everything else.** It is tested by
comparing its predictions to real elections, using only data from before that
election. Variables are ideally derived, not hard coded; where that is not
possible the hand-written value is recorded in `JUDGEMENT-CALLS.md` so it is
obvious.

**The model evolves and its forecast evolves with it.** The published forecast is
not "correct".

### ⛔ NOTHING THIS MODEL HAS EVER PRODUCED IS A STANDARD OF CORRECTNESS

**Never evaluate work by comparing it to the published forecast, to
`data/processed/forecast_frozen.json`, to a golden, or to any earlier output of
this model. The only standard is backtesting against REAL ELECTION RESULTS.**

**Agreement with a previous output is evidence of nothing**, because that output
was never known to be right. "Reproduce the old numbers or revert" enshrines the
current bugs as the definition of correct. When a change moves a number the
question is always *"does the backtest against real results improve?"* and never
*"does it still match?"*.

*(`ITERATING.md` deliberately does not restate this and points here. Do not
reduce it to a pointer in the other direction — nothing would then state it.)*

**A freeze of results is a tripwire, not a gate.** It says *go and look* when
something moved unexpectedly. It never decides whether a change is right.

**Read `ITERATING.md` before judging any change** — the bar is four keys, not a
single seat total, and the 2026-08-23 and 2026-08-27 amendments at the top change
what "better" means. Worse does not ship, and the reason it does not is that
worse almost always means something nonsensical or inert has been modelled.

**Two backlogs, and they do not mix.** `PUBLISHING-BACKLOG.md` is the
presentation layer and is never a reason to change a forecast; it carries the
owner's standing position and the rule in full.

---

## 2. Documentation is part of the model, not a description of it

**Whenever the model changes, the documented record changes in the same commit.**
Not afterwards, not in a cleanup pass. A stale document is worse than a missing
one: it looks current and cannot be. `MACHINERY.md` spent weeks describing a
level layer that no longer ran, and the published page carried ten claims pinned
to `turnout_tilt_da`, a lever already deleted from `run_model`.

### Which file records what

| change | goes in |
|---|---|
| a **mechanism** — how something is computed | the function's docstring **and** `MACHINERY.md` |
| a **number** the data did not force | `JUDGEMENT-CALLS.md`, with status, evidence and how to check it |
| a **finding** — including a rejected one, and especially a negative result | `MODEL-LOG.md` (append; never rewrite history) |
| a change in **what counts as better** | `ITERATING.md` |
| a defect in the **inputs** | `DATA-QUALITY.md` |
| a new or changed **source** | `SOURCES.md`, with provenance |
| a **number or claim on the public site** | `content/<city>/stats.toml` as a token — never typed into prose |

`MODEL-LOG.md` is the record of record. If a thing was measured and rejected it
belongs there with its number, so nobody spends a day rediscovering it.

### Non-negotiable

- **A rejected idea is written up with the measurement that rejected it.** Some
  of this project's most useful entries are negative results.
- **A constant that is not measured is declared** in `JUDGEMENT-CALLS.md`, or it
  will be mistaken for one that is — and then none of them are trusted.
- **Anything the harness cannot test is labelled argued, not tested**, wherever
  it is quoted. `w_bye` and the first-local-election bias correction are both in
  this position.
- **Never type a model figure into prose.** It goes stale silently. Register it
  as a stat token; `build_site.py` audits for typed figures and will name them.
- **Re-record a golden deliberately and say why in the file.** A silent
  re-record destroys the only guard on the prior.

---

## 3. Shared artefacts: one writer, and nobody measures while it writes

`data/processed/pools_*.json` is **precomputed**. Changing `src/pools.py` does
nothing until you re-emit, and re-emitting moves the baseline of every
measurement anyone else is taking at that moment. A lever sweep will return
different answers on two identical runs if that happens underneath it.
**Partitioning work by *file* is not enough** — `pools.py` and
`compare_history.py` do not overlap as files and collide completely as work.

When more than one worker is active:

* **Exactly one** may re-emit `pools_*.json`, and it owns them for the duration.
* **Nobody else runs the model, `compare_history`, or any sweep** while that is
  true. Verify at unit level instead, and say so.
* The re-emit and the canonical measurement happen **once, at the end, on a
  settled tree** — and every number quoted anywhere comes from that run.

A number measured against a moving artefact is not a measurement, and reads
exactly like one.

**The specs are not tracked by git**, so each one's `artefact_key` is its only
version history, and a run prints a named reason when it does not match. That
stops a stale result being *believed afterwards*; it does not stop the artefacts
moving under a measurement in progress, which is what the rule above is for.

**A CODE change to `pools.py` invalidates all eighteen specs and is BATCHED, not
taken when convenient.** What is queued, the emit loop and the window procedure
are in `POOLS-REEMIT-QUEUE.md`; a comment-or-docstring-only change does not move
the hash and does not belong there. One spec re-emits with

    .venv/bin/python src/pools.py --city <city> --target <year> --emit

`compare_history` runs its sixteen city-years in parallel processes, which is
safe because they only READ the specs.

### Contention between agents

**Manage it by making agents READ-ONLY when they would collide.** Three agents
writing to `montecarlo.py` collide whatever regions they occupy, because each
writes the whole file. **Parallel analysis plus serial application is the
reliable shape**; worktrees are the alternative when the files are genuinely
disjoint.

---

## 4. ⛔ The working loop — the standard procedure for this project

**This is the procedure, not a per-task choice. One section at a time, and a
section is not left until it is clear.**

    ROUND = design (parallel, read-only)
          → I check (re-derive the decisive number myself)
          → pollster reviews, BLIND where possible
          → apply only what the check and the review agree on
          → measure, and write the result up
          → iterate what is left, then move to the next section

1. **DESIGN — split across agents, in parallel, READ-ONLY.** One agent per
   finding or coupling group. Agents return **specifications**, not edits. Give
   them the coupling warnings explicitly: an agent that does not know
   `compress_levels` renormalises over `centres` will cheerfully propose widening
   a loop.
2. **⛔ CHECK WHAT THEY RETURN, BY RE-DERIVING IT.** Not by reading the summary.
   This has changed the answer repeatedly and in both directions. Quote what you
   verified and what you did not.
3. **THE POLLSTER REVIEWS EACH ROUND, AND BLIND WHERE IT CAN BE.** Not only at
   the end. Give it the evidence base and the question; do **not** give it your
   conclusion. It reviews anything touching the forecast's **substance** — an
   estimator, a weight, a prior, a selection rule — not plumbing. Blindness is
   what buys the finding: two blind passes each caught a publication-blocking
   defect the other reviewer missed entirely.
4. **APPLY ONLY WHAT BOTH AGREE ON.** Where they disagree, the disagreement is
   the finding and it goes to the owner — do not split the difference.
5. **MEASURE, THEN WRITE IT UP.** `compare_history` adjudicates 16 city-years in
   about three minutes. **Prefer questions that instrument can settle, and be
   sparing with those it cannot.**

**PRE-REGISTER THE PREDICTION BEFORE THE RUN, IN WRITING.** It is what turns a
result into evidence.

### A test that asserts ABSENCE must prove four things, and usually proves one

**Audited 2026-08-31: 38 tests scan live repository state and assert emptiness;
13 carried a positive guard and 22 did not.** That class produced roughly half of
everything found in a week of review. A scan-shaped test must show:

0. **It scanned the RIGHT thing.** State the population the claim covers and
   assert it equals what was scanned; where the claim is bidirectional, assert
   both directions. **This is the class with the worst record** — the register
   guard checked code→register and never register→code, so a deleted lever sat
   in the register for days; the calibration audit parsed one marked table and
   not the docstrings beside it, leaving six stale figures and a flipped sign.
   In each case the scan was healthy, the detector worked, and it found nothing
   **in the wrong set**.
1. **It looked.** The population is non-empty and within a **two-sided** bound.
   Prefer a fraction of a computed denominator (`.py` files in `src/`, registry
   entries, test modules) so nothing goes stale; a bare one-sided floor
   ratchets — when it trips, the cheapest fix is to lower it.
2. **It can see.** A constructed violation, pushed through the same detector, is
   caught. Where the detector is a pure predicate this is mechanical; where it
   is an AST walk or a subprocess build it is per-test, so the rule is *supply
   one or the other*.
3. **Its input is constructed, not observed.** A test whose premise is a passing
   state of the tree expires silently — one here asserted the build refuses an
   unattributable run and broke the day that defect was fixed.

**The honest name for all of this is mutation testing**, which subsumes 1 and 2:
every guard defect in that review was found by changing one line and watching the
suite stay green. The four-part rule is the cheap approximation. Do not mistake
it for the complete answer.

### Level and shape are different repairs, and only one of them is estimation

*"The shape is right and only the level is wrong"* recurs in this project's
analysis. The mechanism, and the line that decides whether a fix is permitted:

**Fitting to a property of the WORLD is estimation. Fitting to a ratio defined
against our own output is tuning.** The realised conditional dispersion of
`log θ` is a fact about how parties' local-vs-national ratios actually vary —
fitting to it is permitted (rule 10). `k*` is *realised over predicted*: it
cannot be computed without the model, so moving a parameter until `k*` hits 1 is
tuning against our own output, and the register bars it. **The two are not the
same operation even when they produce a similar number.**

⚠️ **The corollary is the trap.** A joint calibration of the layers against
realised **seat** width is on the wrong side of that line, because seat width is
scored against the model's own seat output. Against realised **vote** dispersion,
with seats following as a consequence, it is on the right side. Settle which one
before starting, not after.

**And a level is not necessarily a constant.** `k*` reads 0.62 / 2.48 / 1.70 /
1.76 across 2006 / 2011 / 2016 / 2021 — a 4× spread that no single number
resolves to better than about ±40%. If a level is set at all it belongs at the
**RMS (1.77), not the mean (1.64)**, because a forecast of an unknown future
cycle carries `E[k²]`. The productive reading is that **`k*` is not a constant to
estimate but a variable with a missing covariate** — the model has no term for
how turbulent a cycle is, and the three post-realignment cycles all sit between
1.70 and 2.48 while the quiet one is the 0.62 outlier.

### The three ultra reviews — spend them on code that moves numbers

**The owner holds three `/code-review ultra` runs. They are user-triggered and
billed; I cannot launch one, so ASK when the moment arrives rather than
assuming.** Spend them where a defect would be expensive *and* this project's
normal safety nets do not reach — which is where a change **moves forecast
numbers**, because `forecast_frozen.json` is barred from arbitrating and the
backtest cannot tell a fixed bug from a new one.

**Booked first: the `pools.py` re-emit batch.** Its brief is frozen at
`audits/ULTRA-REVIEW-1-pools-reemit.md` and carries when to run it (**before the
emit, never after** — afterwards the baseline has moved and there is nothing
clean to compare against), how to invoke it, and the severability decision.
**Read the brief before writing a line of the batch, and do not amend it
afterwards** — if the hunt list is visible while the code is written, the code
gets written to pass it and the review inherits a blind spot shaped exactly like
the brief.

---

## 5. Running things

Use `.venv/bin/python`, never bare `python` — numpy is not on the system
interpreter.

    .venv/bin/python tests/run_all.py                   # the suite (~14 min)
    .venv/bin/python tests/run_all.py -k spine -k theta # just those modules
    .venv/bin/python tests/run_all.py -x levers         # everything but the slow one
    .venv/bin/python tests/run_all.py --list            # the module names
    .venv/bin/python src/compare_history.py             # votes and seats vs actual,
                                                        #   16 city-years; parallel by
                                                        #   default, --jobs 1 forces serial

Four modules have no importer and are alive only because they are named here.
**`tests/test_standalone_modules.py` cites this section verbatim as the evidence
that each is not dead** — do not remove a line without moving its entry there:

    .venv/bin/python src/diagnose.py --city joburg --target 2021 --wards 0
                                                        # per-city-year investigation
    .venv/bin/python src/arrivals.py                    # the arrival machinery, scored alone
    .venv/bin/python src/contested_area.py              # the poll path's contested-area
                                                        #   conversion (§1.66)
    .venv/bin/python src/sweep.py                       # obvious-fault sweep

And one more, imported by `test_levels_dispersion.py` rather than orphaned:

    .venv/bin/python src/theta_residual.py              # the CONDITIONAL sd(log theta),
                                                        #   forward validated (§1.59)

### Run the targeted modules per change; run the SUITE once per commit

Every run prints a per-module timing table, so the suite can be made faster on
evidence rather than on a guess.

* **while iterating** — `-k` the modules your change can reach. Seconds, not
  minutes. `-x levers` alone is a 3x speedup if you are not touching a lever.
* **before committing** — the whole suite, once, for the whole batch. Several
  independent fixes can share one run; that is what `-k` buys, because the
  targeted run is what tells you which change broke something.

**A subset is not a suite run.** `run_all.py` prints a `*** PARTIAL RUN` banner
saying so. Do not report one as the other.

### Before adding a print to find out what something is, ask for a trace

    .venv/bin/python src/montecarlo.py --city joburg --target 2021 \
        --run-dir /tmp/t                  # every stage's output, as JSON
    .venv/bin/python src/compare_history.py --run-dir /tmp/t   # one per city-year

`--run-dir` writes every stage of the run as JSON — the θ prior, the spine, the
centres before and after the level shrink, the drawn means and bands, every guard
counter. It is **opt-in and changes no number**: with no `--run-dir` the run is
byte-identical and `test_chain.py` asserts it. It is a *record*, not a check — it
will happily record a guard that has gone blind. What catches those is an
assertion, and the trace is what makes assertions cheap to write.
