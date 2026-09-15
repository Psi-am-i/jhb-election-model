**MemPalace wing:** `jhb_election_model` — file every diary entry, drawer and KG fact here.
**Global policy — agent identity, MemPalace, machines, secrets — is in `~/CLAUDE.md` (rules 1-5)** and `~/projects/SECRETS.md`. Do not restate it.

---

# Forecasting South African Local Government Elections

**This file holds only the rules a session would otherwise break by default.**
A rule written twice is a rule that drifts.

**`README.md` is the map.** Two files it omits: `ARCHITECTURE.md` (the structural
argument about `run_model`) and `HANDOVER.md` (where the branch stands — start there).

---

## 0. ⛔ MECHANISM ONLY. NO CLAIMS.

**The model evolves; every number describing it is a moving quantity.**

⛔ **No number, count, size, score, parameter, runtime or audit result may be
written into this file. Name the instrument that reports it instead.**

| don't write | write |
|---|---|
| the panel size | "whatever `compare_history` reports — its `rows=` token carries the population" |
| the spec count | "whatever `find data/processed -name 'pools_*.json'` counts, checked against the emit loop in `POOLS-REEMIT-QUEUE.md`" |
| test counts or runtimes | "whatever `tests/run_all.py` prints" |
| a score, margin, error or parameter | the run that produces it, or the `MODEL-LOG.md` §  that recorded it |

**Why this is rule zero.** This file loads into every session, so a stale number
here is a false premise injected into all downstream work — invisible, because it
arrives wearing the authority of the rules. It has already happened: this file
misstated the panel size, the spec count and its own module count simultaneously.

A historical incident may be cited **by pointer** as the reason for a rule.
Restating its numbers copies a measurement into a file nobody re-measures.

**A number in this file is a defect. Delete it and cite the instrument — do not
update it.** Updating is how these survived.

---

## 1. The only standard is real elections

Predictions are tested against real elections, using only data from before that
election. Variables are derived where possible; a hand-written value goes in
`JUDGEMENT-CALLS.md` so it is obvious.

### ⛔ NOTHING THIS MODEL HAS PRODUCED IS A STANDARD OF CORRECTNESS

**Never evaluate work against the published forecast, `forecast_frozen.json`, a
golden, or any earlier output.** Agreement with a previous output is evidence of
nothing — that output was never known to be right. "Reproduce the old numbers or
revert" enshrines current bugs as the definition of correct. The question is
always *"does the backtest against real results improve?"*, never *"does it still
match?"*.

⚠️ **The published site is not an oracle and not a reference point.** It is an
artefact of an earlier model, usually a different draw count, often built from
artefacts that no longer exist, and it may claim mechanisms the code has since
deleted. When it disagrees with the model that is a fact about its age. Correct
it because it is wrong — never cite it as evidence about the model.

**A freeze is a tripwire, not a gate.** It says *go and look*. It never decides
whether a change is right.

**Read `ITERATING.md` before judging any change.** The rule is **"MORE HONEST
USUALLY SHIPS"** — a change that makes the model more honest ships even when a
headline score worsens. What does not ship is a change that scores worse **and
explains nothing**. *("Worse does not ship" is retired: it meant something new
each time it was invoked.)*

**`PUBLISHING-BACKLOG.md` is presentation and is never a reason to change a
forecast.**

---

## 2. Documentation is part of the model

**When the model changes, the record changes in the same commit** — not
afterwards. A stale document is worse than a missing one: it looks current.

| change | goes in |
|---|---|
| a **mechanism** | the function's docstring **and** `MACHINERY.md` |
| a **number the data did not force** | `JUDGEMENT-CALLS.md` — status, evidence, how to check it |
| a **finding**, especially a negative one | `MODEL-LOG.md` (append; never rewrite) |
| what counts as **better** | `ITERATING.md` |
| a defect in the **inputs** | `DATA-QUALITY.md` |
| a **source** | `SOURCES.md`, with provenance |
| a **number on the public site** | `content/<city>/stats.toml` as a token — never prose |

**A NUMBER LIVES WHERE IT WAS GENERATED. EVERYWHERE ELSE POINTS AT IT.**

That is the whole rule, and it is about staleness, not about arithmetic. A
number copied into a second file cannot be updated — only updated in the copies
someone remembers — and the stale copy goes on looking like truth, because
nothing about a written figure says when it was measured.

So: **do not copy a number, fetch it.** Name the instrument, the artefact or the
dated entry that produced it, and let the reader (or the next session) go and
read the current value. If it changes, the pointer still resolves; a copy does
not.

Where numbers are *generated*, and therefore correctly written as digits:

| the number | is generated in | and is |
|---|---|---|
| a **measurement** of the model | `MODEL-LOG.md` | append-only and dated, so an old entry is read as describing the past |
| a **judgement call** | `JUDGEMENT-CALLS.md` | concrete, and written out in full |
| a **published** figure | `content/<city>/stats.toml`, as a token | fetched by the build, never retyped into prose |

⚠️ **`JUDGEMENT-CALLS.md` is not an exception to the rule — it is the rule.** A
judgement call is a weighting or an opinion inserted into the model to slant it.
Nothing derives it; if anything did, it would not be a judgement call. So there
is no upstream generator to point at, and the value must be stated concretely
and explicitly, or it is a hidden thumb on the scale. **Being explicit is the
point.**

- **A rejected idea is written up with the measurement that rejected it.**
- **An unmeasured constant is declared**, or it will be mistaken for a measured
  one — and then none of them are trusted.
- **What the harness cannot test is labelled argued, not tested.**
- **Re-record a golden deliberately and say why.** A silent re-record destroys
  the only guard on the prior.

---

## 3. Shared artefacts: one writer, and nobody measures while it writes

`data/processed/pools_*.json` is **precomputed**. Changing `src/pools.py` does
nothing until you re-emit — and re-emitting moves the baseline of every
measurement in flight. **Partitioning by *file* is not enough**: `pools.py` and
`compare_history.py` never overlap as files and collide completely as work.

When more than one worker is active:

* **Exactly one** may re-emit, and it owns the specs for the duration.
* **Nobody else runs the model, `compare_history`, or any sweep.** Verify at unit
  level instead, and say so.
* The re-emit and the canonical measurement happen **once, at the end, on a
  settled tree**, and every number quoted anywhere comes from that run.

**This applies to documents too.** Do not edit a file while an audit of it runs.

**A `pools.py` CODE change invalidates EVERY spec and is BATCHED.** Procedure in
`POOLS-REEMIT-QUEUE.md`. A comment-only change does not move the hash.

    .venv/bin/python src/pools.py --city <city> --target <year> --emit

⚠️ **Know your writers.** `pools_*.json` declares itself via `artefact_key`;
`turnout.csv`, `fold*_parameters.csv` and the rest carry no key, so a stale one
moves every draw in silence — `tests/test_intermediates_are_current.py` is the
only thing that catches those. **`compare_history` writes `history.json`/`.md`.
A bare `montecarlo.py` run overwrites that city-year's forecast artefacts** — to
inspect without writing, import `run_model` and call it directly. `data/**` is
gitignored: nothing warns you, nothing restores it.

**Make agents READ-ONLY when they would collide.** Three agents writing
`montecarlo.py` collide whatever regions they occupy, because each writes the
whole file. **Parallel analysis, serial application.**

---

## 4. ⛔ The working loop

**`QC.md` is the process document** — this loop, the gated stage observation the
`--run-dir` trace supports, and what a plan item must name to be finishable.
Read it before designing a round; nothing else brings it into a session.

    ROUND = design (parallel, read-only)
          → I re-derive the decisive number myself
          → pollster reviews, BLIND
          → apply only what the check and the review agree on
          → measure, write it up
          → iterate, then next section

1. **DESIGN — parallel, READ-ONLY.** Agents return **specifications**, not edits.
   Give them the coupling warnings explicitly.
2. **⛔ CHECK BY RE-DERIVING.** Not by reading the summary. This has changed the
   answer repeatedly, in both directions. Quote what you verified and what you
   did not.
3. **BLIND REVIEW EACH ROUND.** Give the evidence and the question, never your
   conclusion. Independent blind passes each catch what the other misses.
   **A brief is reissued verbatim or not at all** — a brief rewritten by the
   agent under review is no longer blind. **Tell agents not to sub-delegate**;
   a broad brief fans out and exhausts the budget.
4. **APPLY ONLY WHAT BOTH AGREE ON.** Disagreement is the finding; it goes to the
   owner unsplit.
5. **MEASURE, THEN WRITE IT UP.** Prefer questions `compare_history` can settle.

**PRE-REGISTER IN WRITING BEFORE THE RUN**, under `prereg/`. Predict against the
world and the mechanism — **never against a prior output**, which is
self-benchmarking in a lab coat. **Never edit a pre-registration after the
result**; score it honestly, including what it falsified.

### A test that asserts ABSENCE must prove four things, and usually proves one

Scan-shaped tests — those that search live state and assert emptiness — are this
suite's largest single source of defects. One must show:

0. **It scanned the RIGHT thing.** State the population and assert it equals what
   was scanned; where the claim is bidirectional, assert both directions. **Worst
   record of the four** — a guard checking code→register but not register→code
   left a deleted lever in the register for days. The scan was healthy, the
   detector worked, and it found nothing *in the wrong set*.
1. **It looked.** Population non-empty and within a **two-sided** bound, as a
   fraction of a computed denominator. A one-sided floor ratchets: when it trips,
   the cheapest fix is to lower it.
2. **It can see.** A constructed violation is caught — *and the detector goes
   quiet again when it is reverted*.
3. **Its input is constructed, not observed.** A test whose premise is a passing
   tree expires silently.

**The honest name is mutation testing**: change one line, watch whether the suite
stays green. The four-part rule is the cheap approximation, not the answer.

**This applies to throwaway probes too** — which is exactly where it gets
skipped. A broken probe fails toward "something changed", indistinguishable from
a real regression. **To test whether a derived artefact is current, regenerate
it** — purged, in an isolated tree, so nothing scores "current" by never being
rewritten. An mtime fence does not substitute: `cp -R` restamps.

### Level and shape are different repairs; only one is estimation

**Fitting to a property of the WORLD is estimation. Fitting to a ratio defined
against our own output is tuning.** Realised dispersion of `log θ` is a fact
about the world — permitted. `k*` is *realised over predicted* and cannot be
computed without the model, so tuning until `k*` hits 1 is barred.

⚠️ **The trap:** calibrating against realised **seat** width is tuning (seat
width is scored against our own seat output); against realised **vote**
dispersion it is estimation. Settle which before starting.

**A level is not necessarily a constant.** `k*` varies substantially by cycle
(figures in `MODEL-LOG.md`). If set at all it belongs at the **RMS, not the
mean** — a forecast of an unknown cycle carries `E[k²]`. Better read as a
variable with a missing covariate: nothing models how turbulent a cycle is.

### Ultra reviews

**The owner holds a limited number; how many remain is his to say. They are
user-triggered and billed — ASK, never assume.** Spend them where a defect is
expensive *and* the normal nets do not reach: changes that **move forecast
numbers**, since the freeze cannot arbitrate and the backtest cannot tell a fixed
bug from a new one. **Read a brief before writing the code it covers; never amend
it afterwards** — otherwise the code is written to pass the hunt list and the
review inherits a blind spot shaped like the brief. Briefs live in `audits/`.

---

## 5. Running things

`.venv/bin/python`, never bare `python` — numpy is not on the system interpreter.

    .venv/bin/python tests/run_all.py                   # whole suite
    .venv/bin/python tests/run_all.py -k spine -k theta # those modules
    .venv/bin/python tests/run_all.py -x levers         # all but the slow one
    .venv/bin/python tests/run_all.py --list            # module names
    .venv/bin/python src/compare_history.py             # votes/seats vs actual
                                                        #   ⚠️ WRITES history.json/.md

**These have no importer and are alive only because they are named here.**
`tests/test_standalone_modules.py` cites this section verbatim as the evidence
that each is not dead — do not remove a line without moving its entry there, and
let that test, not this file, be the authority on how many there are:

    .venv/bin/python src/arrivals.py                    # arrival machinery, scored alone
    .venv/bin/python src/contested_area.py              # poll path's contested-area conversion
    .venv/bin/python src/sweep.py                       # obvious-fault sweep

**`src/diagnose.py` was in that list until 2026-09-12 and is not any more** —
`tests/test_diagnose_baselines.py` imports it, so it satisfies the rule on its
own and its `ENTRY_POINTS` exemption was deleted (an exemption that exempts
nothing costs a reader the one thing the list is for). It is still a CLI a human
runs, and the command lives in its own docstring now, which is where the person
about to run it will read it:

    .venv/bin/python src/diagnose.py --city joburg --target 2021 --wards 0

⚠️ **The guard chain here runs one way only.** `test_standalone_modules` checks
ENTRY_POINTS → document (the cited file must still name the module); nothing
checks document → ENTRY_POINTS, so this block could name a module with no entry
and the suite would stay green. That is the same blind direction the register
guard had until 2026-09-12 (§4's scanned-the-wrong-set class). Until it is
closed, this block is maintained by hand.

**Before quoting or believing any number:**

    .venv/bin/python src/declares.py            # does every artefact declare
    .venv/bin/python src/declares.py --verify   #   what produced it? exit 1 if not

⛔ **Three states:** `✓` declared and agrees · `~` **declared and WRONG** · `✗`
undeclared. The middle is the point — an artefact declaring nothing is a known
gap; one declaring wrongly is a gap wearing a badge.

And one imported by `test_levels_dispersion.py` rather than orphaned:

    .venv/bin/python src/theta_residual.py      # conditional sd(log theta), §1.59

### Targeted modules per change; the SUITE once per commit

* **iterating** — `-k` the modules your change reaches. `-x levers` is a large
  speedup if you are not touching a lever.
* **before committing** — the whole suite, once, for the whole batch.

**A subset is not a suite run** — `run_all.py` prints `*** PARTIAL RUN`. **Quote
the counts from the run that finished *after* your last edit.**

### Ask for a trace before adding a print

    .venv/bin/python src/montecarlo.py --city joburg --target 2021 --run-dir /tmp/t
    .venv/bin/python src/compare_history.py --run-dir /tmp/t

`--run-dir` writes every stage as JSON — θ prior, spine, centres before and after
the shrink, drawn means and bands, every guard counter. **Opt-in and changes no
number** — `test_chain.py::test_passing_a_run_directory_changes_no_drawn_number`
runs the model twice on one seed and compares the drawn seats *and* the drawn
shares. It is a *record*, not a check: it will happily record a guard that has
gone blind. Assertions catch those; the trace makes them cheap to write.
