# Working rules for this repository

## The documentation is part of the model, not a description of it

**Whenever the model changes, the record changes in the same commit.** Not
afterwards, not in a cleanup pass. A stale document here is worse than a missing
one: it looks current and cannot be, and every reader downstream — including the
next session, including a reviewer — takes it at its word.

This has already gone wrong more than once. `MACHINERY.md` spent weeks
describing a level layer that no longer ran. The published forecast page carried
ten claims pinned to `turnout_tilt_da`, a lever deleted from `run_model`, and the
stat audit kept reporting "no drift" because a fixed token cannot drift.
`site/plan.html` was served for weeks after no build produced it.

### Which file takes what

| change | goes in |
|---|---|
| a **mechanism** — how something is computed | the function's docstring **and** `MACHINERY.md` |
| a **number** the data did not force | `JUDGEMENT-CALLS.md`, with status, evidence and how to check it |
| a **finding** — including a rejected one, and especially a negative result | `MODEL-LOG.md` (append; never rewrite history) |
| a change in **what counts as better** | `ITERATING.md` |
| a defect in the **inputs** | `DATA-QUALITY.md` |
| a new or changed **source** | `SOURCES.md`, with provenance |
| a **claim on the public site** | `content/<city>/stats.toml` as a token — never typed into prose |

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
page, the stat tokens. **This repository's working list is the model's ability to
predict, and nothing else.** The owner's standing position is that the page gets
rebuilt when the model is ready, so presentation work is not a competing
priority and is never a reason to change a forecast.

## Iterating, not publishing

### ⛔ NOTHING THIS MODEL HAS EVER PRODUCED IS A STANDARD OF CORRECTNESS

**Never evaluate work by comparing it to the published forecast, to
`data/processed/forecast_frozen.json`, to a golden, or to any earlier output of
this model. The only standard is backtesting against REAL ELECTION RESULTS.**

This rule already existed in the sentence below and was broken anyway, on
2026-08-25, by the author of this note: `src/freeze.py` was built as a fixed
reference and "must reproduce the frozen panel to the seat or be reverted" was
written into the restructure plan as its verification gate. The owner stopped
it. **We are not benchmarking against a broken implementation we cannot
evaluate.**

**Why it is not a technicality.** "Reproduce the old numbers or revert"
**enshrines the current bugs as the definition of correct.** If an extraction
changes a number it may have *fixed* something — the poll channel was worth −6
and nobody knew for four days (§1.94), the by-election decay is applied twice,
`allocate_with_overhang` has no test. A rule that reverts any change to those
paths protects the defects. Agreement with a previous output is evidence of
*nothing*, because that output was never known to be right.

**So when a change moves a number, the question is never "does it still match?"
It is "does the backtest against real results improve?"** — paired,
cycle-replicated, against the four keys in `ITERATING.md`.

**What the freeze IS for**, and it is not this: recording what we published and
the exact configuration that produced it, so the forecast can be held to account
after 4 November; and acting as a **tripwire** that says *go and look* when
something moved unexpectedly. A tripwire is not a gate. It never decides whether
a change is right.

Read `ITERATING.md` first. The published forecast is a recent output of an
earlier version — not a benchmark, not a target, not evidence. The only question
is whether the current model predicts PAST elections better than the previous
iteration and better than the naive baselines. If it does not, it does not ship,
however well argued. Worse does not ship.

**The bar was AMENDED on 2026-08-23 and is now four keys, not one** — paired and
cycle-replicated on seats, calibration as an untradeable floor, derivedness
priced in coherent seats against a budget that never refills, and the estimation
record's held-out NLL as a second untradeable floor. Read the amendment at the
top of `ITERATING.md` before judging any change; the single-number version above
is what it replaced.

## Shared artefacts: one writer, and nobody measures while it writes

`data/processed/pools_*.json` is **precomputed**. Changing `src/pools.py` does
nothing until you re-emit it, and re-emitting it changes the baseline of every
measurement anyone else is taking at that moment.

This has cost twice. A lever sweep returned **different answers on two identical
runs** because another worker was re-emitting the artefacts underneath it; two
`EXPECTED_INERT` reasons were written from those unstable readings and had to be
retracted. Partitioning work by *file* is not enough — `pools.py` and
`compare_history.py` do not overlap as files and collide completely as work.

So, when more than one worker is active:

* **Exactly one** may re-emit `pools_*.json`, and it owns them for the duration.
* **Nobody else runs the model, `compare_history`, or any sweep** while that is
  true. Verify at unit level instead, and say so.
* The re-emit and the canonical measurement happen **once, at the end, on a
  settled tree** — and every number quoted anywhere must come from that run.

A number measured against a moving artefact is not a measurement. It reads
exactly like one.

**Since 2026-08-18 the artefacts say what built them.** Every `pools_*.json`
carries an `artefact_key` — city, target, a hash of `config/dimensions.toml`,
and a hash of `pools.py`'s code with comments and docstrings ignored — and a run
prints a named reason when it does not match. That does not replace the rule
above: it stops a stale result being *believed afterwards*, it does not stop the
artefacts moving under a measurement in progress. Re-emit with:

    .venv/bin/python src/pools.py --city <city> --target <year> --emit

Emission is deterministic — re-emitting every spec changes nothing but the key —
so the hazard is re-emitting *while someone measures*, not re-emitting. **There
are eighteen specs since 2026-08-22**, not eleven: the eight 2016 specs are now
all emitted (§1.69). Re-emit the lot with

    for c in joburg tshwane ekurhuleni ethekwini capetown mangaung \
             nelsonmandelabay buffalocity; do
      for y in 2016 2021; do
        .venv/bin/python src/pools.py --city $c --target $y --emit
      done
    done
    .venv/bin/python src/pools.py --city joburg --target 2026 --emit
    .venv/bin/python src/pools.py --city joburg --target 2026 --simulation --emit

**A CODE change to `pools.py` invalidates every one of them, and the guard will
say so.** This caught the §1.69 audit itself: constants were promoted to module
level, `pools_sha` moved, and a canonical measurement had already been taken
against the older specs. It was verified number-neutral separately and was in
fact correct — and "I checked it separately" is precisely the reasoning the key
exists to stop being sufficient, so everything was re-emitted and re-measured.
A comment-or-docstring-only change does NOT move the hash; that was confirmed
in the same session.

**A `pools.py` CODE change is BATCHED, not taken when convenient.** What is waiting for the next re-emit window, and the procedure for taking it, is in
`POOLS-REEMIT-QUEUE.md`. A comment-or-docstring-only change does not move the
hash and does not belong there.

**The specs are not tracked by git.** They have no version history, which is why
the key exists.

**`compare_history` runs its sixteen city-years in parallel processes** (since
2026-08-18), which is safe because they only READ the specs — the rule above is
about who WRITES them, and that is still one worker at a time. Measured at 1500
draws: 499s serial against 169s parallel, a 2.96x speedup, with
`seat_abs_err_coherent`, `crps`, `seat_abs_err` and `median_sum` bit-identical
and the MAE columns agreeing to 6.7e-15 (float summation order, MODEL-LOG
§1.46). Processes rather than threads because `apply_city` and `levels.SD_FLOOR`
are module state.

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

**Standing instruction from the owner, 2026-08-30:** *"use multiple agents,
check their work, and get pollster to review after each round. Then make
changes. Iterate this pattern. When a section is clear, move to the next."*

**This is the procedure, not a per-task choice. One section at a time, and a
section is not left until it is clear.**

    ROUND = design (parallel, read-only)
          → I check (re-derive the decisive number myself)
          → pollster reviews, BLIND where possible
          → apply only what the check and the review agree on
          → measure, and write the result up
          → next section

1. **DESIGN — split across agents, in parallel, READ-ONLY.** One agent per
   finding or coupling group. Give them the coupling warnings explicitly; an
   agent that does not know `compress_levels` renormalises over `centres` will
   cheerfully propose widening a loop. Agents return **specifications**, not
   edits — see the contention rule below.
2. **⛔ I CHECK WHAT THEY RETURN, BY RE-DERIVING IT.** Not by reading the
   summary. This has changed the answer repeatedly and in both directions: an
   agent cited `PARTY_OF_ACTION` as ActionSA (the conclusion held, the evidence
   did not); an agent's P(cap binds) of 0.7% was 9.4e-05 at 2021 and 5.7e-03 at
   2026; and one agent overturned another's cause for the 2016 null arm **and
   mine**. Quote what you verified and what you did not.
3. **THE POLLSTER REVIEWS EACH ROUND, AND BLIND WHERE IT CAN BE.** Not only at
   the end, and not only on substance. Give it the evidence base and the
   question; do **not** give it my conclusion. Two blind passes have now each
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
result into evidence. It has paid twice: a challenger's arrival mass was
predicted at +17.8pp and realised at +17.76pp; and a prediction that local
anchoring would *help* the mid-ballot was recorded, refuted, and the refutation
was the useful part.

### The three ultra reviews — spend them on code that moves numbers

**The owner holds three `/code-review ultra` runs. They are user-triggered and
billed; I cannot launch one, so ASK when the moment arrives rather than assuming.**

A deep multi-agent review is wasted on a documentation diff. Spend them where a
defect would be expensive and where this project's normal safety nets do not
reach — which is precisely where a change **moves forecast numbers**, because
`forecast_frozen.json` is explicitly barred from arbitrating and the backtest
cannot tell a fixed bug from a new one.

**Booked, in priority order:**

1. **The `pools.py` re-emit batch** — the 2000/2006 `metro_file` reader plus the
   roster/reach seam. Highest stakes on the calendar: it moves numbers, it
   invalidates **all eighteen** specs, it touches the shared artefact path, and
   it runs under a one-writer window. **Review it BEFORE the re-emit, not after**
   — afterwards the baseline has already moved and there is nothing clean to
   compare against.
2. **Any new SCORING instrument** — the bloc-total score, or anything else that
   arbitrates. This repository has just been bitten by a referee that raised on
   every city-year for its entire life while the suite stayed green, because its
   only test used a fixture of a type production never builds. A scorer is the
   one thing whose failure is invisible to the thing that would normally catch
   it.
3. **Hold the third in reserve** for whatever the width work becomes, or for the
   first change that alters a published figure.

**Do not spend one on:** a documentation pass, a doc consolidation, a lever
sweep that changes no code, or a change the 16-city-year backtest already
adjudicates in three minutes.

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

**Contention is managed by making agents READ-ONLY when they would collide.**
Three agents writing to `montecarlo.py` collide whatever regions they occupy,
because each writes the whole file. Parallel analysis plus serial application
has been the reliable shape; worktrees are the alternative when the files are
genuinely disjoint.

### Run the targeted modules per change; run the SUITE once per commit

Every run prints a per-module timing table, because a suite that does not say
which module owns its runtime cannot be made faster on evidence. Measured
2026-08-28: **`test_levers_are_live` was 999s of 1455s — 69% of the suite in one
module** — and the other 22 cheap modules together are 92s. It does ~108
`run_model` calls, one per lever per target; those are now run in parallel and
it is 361s, so the suite is ~14 minutes.

So the loop is:

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
