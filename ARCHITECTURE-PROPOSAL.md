# Making the model cheaper to audit

**Status: a proposal for discussion. Nothing here has been built.** It exists
because reviews of this model now cost more than the changes they review.

**It began as a proposal to restructure the model as an explicit graph. After
working the argument through, most of that is not recommended.** The diagnosis
below stands; the remedy changed. The short version:

> The expensive part of a review is not that the code is one function. It is
> that you cannot see an intermediate without re-running the whole simulation,
> and that the artefacts underneath a measurement can move while you take it.
> Both are fixable with instruments. Neither needs a refactor.

---

## 1. Why auditing costs what it does — measured, not asserted

From the current tree:

| | |
|---|---|
| `run_model` | **863 lines**, one function, `montecarlo.py:1760–2623` |
| distinct local names bound inside it | **223** |
| writes into the shared `scenario` dict inside it | **16** |
| **function-local imports** inside it | **7**, at lines 1812, 1875, 1911, 2310, 2311, 2345, 2394 |
| `run_model` call sites in the suite | 11, across 5 of 10 test files |
| intermediate-inspection facilities | 15 `if verbose:` prints, one end-of-run JSON summary |
| full-suite wall clock | ~35 minutes |
| one `compare_history` at 1500 draws | 499s serial, 169s parallel (measured 2026-08-18; an earlier draft of this table said ~50 minutes, which was guessed from polling intervals while other jobs competed, and was wrong) |

Four consequences, each of which has already cost real time:

**You cannot see an intermediate without re-running everything.** Every quantity
in the level chain — the θ record, the shrunk estimator, the spine blend, the
by-election clamp, the capacity guard — exists only as a local inside those 863
lines. To look at one you add a print and re-run. **This is the single largest
tax on troubleshooting and it is nearly free to remove.**

**The dependency graph is invisible.** `levels.spine` is called at line 2345,
`levels.theta_prior` at 1911, `pools.contesting_parties` at 1875 — through
imports written *inside the function body*. Nothing at the top of the file says
`montecarlo` depends on `levels` or `pools` at all.

**The input is also the scratchpad.** `scenario` is passed in and then written
to sixteen times. That is why `apply_city` silently overwriting `DEFAULTS` was so
hard to see, and why `--set` must be applied *after* `apply_city`.

**The biggest edge in the system is an untyped file.** `montecarlo` and `pools`
are joined by `data/processed/pools_*.json`, which is precomputed. Changing
`pools.py` does nothing until it is re-emitted, and re-emitting it changes the
baseline of every measurement in flight. `CLAUDE.md` carries a whole section —
*"one writer, and nobody measures while it writes"* — whose only job is to
compensate by human discipline for an edge nothing checks. **It has already
failed twice**: a lever sweep returned different answers on two identical runs,
and two `EXPECTED_INERT` reasons were written from those unstable readings and
had to be retracted.

### The pattern in the defects

Of the defects found this month — the pool ceiling going blind, a wrong-city ward
roll loaded by fallback, an arrival total read from the wrong aggregate,
`theta_mode` reading live because artefacts moved underneath the measurement, a
`{CODE}` template never substituted — **not one is a modelling error.** They are
boundary and instrument errors. That is what the remedy has to target, and it is
not the same thing as more end-to-end testing.

---

## 2. What I recommend, smallest first

None of items 1–4 requires freezing the model, and together they are most of the
available benefit.

### 1. Dump every intermediate by default

Write each stage's output to a run directory instead of discarding it. Then
"what did the spine give ActionSA before the by-election blend?" is a file read,
not a whole-comparison re-run with an added print.

Highest troubleshooting gain per unit of risk on this list, and it requires **no
restructuring whatsoever** — `run_model` keeps its shape and gains write calls.

### 2. Content-address the artefacts

Key `pools_*.json` by city, target, code version and config hash. A stale
artefact becomes *detectable* rather than prevented by a rule people must
remember, and a measurement taken across a change of hash can be refused instead
of silently believed.

This is the item that retires a discipline tax paid every session, on a failure
mode that has already cost twice. It is also the precondition for item 3.

### 3. Parallelise the nine city-years — **DONE 2026-08-18**

They are genuinely independent, and `compare_history` now runs them in parallel
processes by default. **499s serial against 169s parallel at 1500 draws, a 2.96×
speedup** — worth having, and a good deal less than the core count suggests,
because numpy already threads inside a single run.

Coherent seat error, CRPS, raw seat error and the medians-sum come out
bit-identical; the MAE columns agree to 6.7e-15, which is float summation order
(§1.46) and not a behavioural difference.

It depended on item 2 less than expected and on something else more: `apply_city`
wrote each city's scalars over `DEFAULTS` and never restored them, so a city
inherited whatever ran before it and the serial loop and a parallel one were
different programs. That had to be fixed first (§1.47).

### 4. Build more fast, validated screens

**The largest efficiency gain of the last week was not structural.** Caching the
nine city-years' mean vectors turned "one full scored run per candidate" into
seconds per candidate, and made it possible to compare four functional forms
and sweep two parameters in an afternoon. It was validated before it was trusted
— reconstructed coherent seats reproduced the runs' own at **306 against 308**.

That is roughly a hundredfold on iteration speed from a seventy-line script, with
no refactor and nothing to undo. **If the goal is cheaper review, better
instruments beat better architecture**, and they are cheap to try and reversible
if they fail. The discipline that makes them safe is the one used here: validate
the screen against the real thing, and say so, before believing any of it.

### 5. Node extraction — defer

Give stages declared inputs and outputs only when a specific pain demands it, and
**do not build a graph engine**.

---

## 3. Why the graph framing is not recommended

The original proposal was to restructure the model as NODE / EDGE / STATE /
ROUTER / GATE. Working it through, most of it does not fit:

**This is a pipeline with one router, not a graph.** Real branching is almost
absent — the only genuine router is the route-precedence chain in
`blended_centres` (poll → seeded arrival → spine → prior → dead branches).
Adopting graph vocabulary invites building routers, gates and a scheduler for a
problem that is about ninety per cent linear, and then we own a framework's bugs
on top of the model's.

**Node extraction improves auditability more than clarity, and I first conflated
the two.** The model is not hard to follow because it is one function. It is
hard because the domain is intricate: θ, ρ, ecological inference, IPF,
Duncan–Davis bounds, largest-remainder allocation. Splitting 863 lines into
fourteen 60-line functions does not reduce the number of concepts, and it can
make data flow *harder* to trace — sequential locals read quite well, and
cross-node plumbing adds indirection and "where was this set?". That is trading
one kind of opacity for another, and it was presented as pure gain.

**Most of that document is written for agent systems.** Routers over
probabilistic judgement, verifiers that check a model's claims, and
cycles-until-convergence solve problems we do not have; our nodes are
deterministic functions. What transfers is narrower and duller: declared inputs,
durable intermediates, checked edges, parallel fan-out. Those are items 1–3.

**Some things must not be split.** The draw loop is a per-draw IPF over 1500
draws sharing arrays for performance. That is one unit, not 1500.

### Two things a manifest will not do

An earlier draft claimed a run manifest would have caught every boundary defect
above. That is wrong, and the check is worth keeping:

| defect | caught by a manifest? |
|---|---|
| wrong-city ward roll loaded by fallback | **yes** — a Tshwane run recording Johannesburg input paths is visible at a glance |
| `theta_mode` reading live off moving artefacts | **yes** — differencing runs with different artefact hashes is detectably invalid |
| `{CODE}` never substituted | **probably** — an output path containing a literal `{CODE}` stands out |
| the pool ceiling going blind (74 of 75 at exactly 1.0) | **no** — it records the fact; nobody reads a passive record. This needed a GATE asserting an invariant |
| the arrival total read as a per-party figure | **no** — the quantity was recorded correctly and misunderstood. That is naming, not plumbing |

Three of five. **A manifest makes defects findable; it does not find them.** What
finds them is a gate asserting an invariant — and the manifest's real value is
that it makes such gates cheap to write, because the quantity is already exposed.

**And it does not replace the lever sweep.** `individual_theta` was a *dead
store*: written, read, and then the reader short-circuited before using it. Only
an end-to-end perturbation catches that, so CLASS 12's fifty model runs stay.

---

## 4. The constraint that governs any refactor

**A refactor cannot improve prediction, so by `ITERATING.md` it can only be
neutral or bad.** Every number must be unchanged, and the golden prior is the
instrument that proves it — which means the goldens must **not** be re-recorded
at any point during it. A re-record during a refactor destroys the only evidence
that the refactor was safe.

That argues for sequencing, and against starting now. The model went from 336 to
264 coherent seat error in a week; the open work on the width budget and
`SD_FLOOR` will move the numbers again. **Land the modelling work, let the
goldens settle, then restructure against frozen numbers** — if by then anything
still argues for it.

Items 1–4 are exempt from this, which is most of why they are the recommendation:
none of them changes a forecast.

---

# AMENDED 2026-08-25 — the deferral condition is met, and §3's argument is adopted

**Status change: this is no longer a proposal for discussion. Items 1, 2 and 3
are built; item 5 is now scheduled, on terms this document set.**

The owner asked, on 2026-08-25: *"Every round we find what sound like large
errors — and yet they do not affect the score at all more often than not."* Three
audits were run to answer it. **This document's diagnosis was right, its remedy
list was right, and its argument against the graph framing survives contact with
the new evidence.** What has changed is the size of the problem and the fact that
its own precondition for restructuring has now been satisfied.

## What this document got right, and is hereby adopted

**§3 stands and governs the work.** Specifically:

* **No graph engine.** A topological runner over a ninety-per-cent-linear
  pipeline is ceremony, and the first draft of the 2026-08-25 plan proposed
  exactly that. Declarations are **checked, not scheduled**; the call sequence
  stays a sequence.
* **"A manifest makes defects findable; it does not find them."** Scored 3 of 5
  on the boundary defects, honestly. The manifest's value is that it makes
  invariant-gates cheap to write, so **the gates are the point and the manifest
  is the enabler** — not the reverse.
* **"Give stages declared inputs and outputs only when a specific pain demands
  it."** Adopted as the extraction test. "Clarity" does not qualify. A stage
  that cannot be value-tested without a seam does.
* **§4's sequencing.** *"Land the modelling work, let the goldens settle, then
  restructure against frozen numbers."*

## What has changed since it was written

**The deferral condition is met.** §4 asked for frozen numbers first.
`src/freeze.py` and `data/processed/forecast_frozen.json` landed on 2026-08-25:
content hash `67e9641856b9ad04…`, a hash of the full seat-draw matrix, the
resolved levers, the six import-time environment switches *as resolved*, the pool
artefact keys and the commit. `--verify` re-runs and exits 1 on drift. There is
now a fixed reference to restructure against.

**The function grew 27% while the work was deferred.**

| | this document, 2026-08-18 | now, 2026-08-25 |
|---|---|---|
| `run_model` | 863 lines | **1,099** |
| distinct local names | 223 | **228** |
| branches (`if`) | not measured | **74** |
| `return` statements | not measured | **1** |

**And three findings this document could not have had:**

1. **Six of the eight wiring mechanisms fail silently**, and they carry most of
   the dataflow. The failure is uniform: a stage's input arrives through
   `dict.get`, and *absence is indistinguishable from the neutral value* —
   identity, `1.0`, `{}`, `0.0`, `set()`. **That is the answer to the owner's
   question.** A defect lands in a channel already contributing its neutral
   value, so it cannot move the score. Three bare `except` blocks sit around
   wiring steps; one silently empties the roster, which skips *every* party in
   the arrivals poll path with no message.
2. **`montecarlo.allocate_with_overhang` has no test.** It is the seat allocator
   the forecast calls on every draw, implementing Schedule 1 item 16 with four
   rules. `tests/test_seats.py`'s 24 passing city-year checks exercise
   `seats.allocate` — a *different function* — and `test_chain` compares
   `seat_draws` against `council_sizes`, both returned by the same call, so it
   asserts the function agrees with itself. The suite is not fake (163 of 211
   tests assert computed values); it is **mis-aimed**, dense at the
   ecological-inference fit and the scoreboard and thin in the middle, which is
   where seats are decided.
3. **The poll channel is worth −6 coherent seats, not +48** (§1.94). One of the
   two effects that carried ~79% of the model's measured margin reversed when
   re-read on sixteen city-years — and it was still being quoted from nine three
   days ago.

## The revised recommendation

Items 1–2 of §2 are done in outline and are extended rather than replaced: the
trace records **6 of 26 stages** and strips exactly the `_`-prefixed keys that
carry the inter-stage wiring, and `30_centres` is written *before* the
metro-poll blend mutates `centres` in place — so the centre vector the drawer
actually receives is recorded nowhere. That is item 1 half-built, not built.

**Item 5, node extraction, is no longer deferred — but it is scoped by §3, not
by the original graph proposal.** It proceeds stage by stage, each justified by
a specific pain, each landing with the value test its seam makes possible, and
each required to reproduce the frozen panel to the seat or be reverted. The
extraction order follows the **test-coverage gap**, not execution order:
`allocate_with_overhang` first.

**§4's warning is honoured literally: the goldens are not re-recorded at any
point during the extraction.** They are the evidence that it was safe.

*The working plan is `~/.claude/plans/linear-hatching-tarjan.md`; this file is
the standing architecture record and takes precedence where they differ.*
