# The architecture, and the problem it exists to solve

**This is the standing record. It replaces `ARCHITECTURE-PROPOSAL.md`, which is
in `archive/rejected/` — see the end of this file for why.**

## The problem, measured

The owner, 2026-08-25: *"Every round we find what sound like large errors — and
yet they do not affect the score at all more often than not. This seems very
unlikely time and time again."*

It is not unlikely. It is what the structure predicts.

| `montecarlo.run_model` | |
|---|---|
| lines | **1,315** |
| branches (`if`) | **74** |
| distinct local names bound | **231** |
| `scenario.get(...)` reads | 34 |
| `return` statements | **1** |

**Re-measured 2026-08-29 — the first three were stale, and the line count was
understating this document's own case by 216 lines** (1,099 → 1,315).
**Derive these, never re-type them**, by AST over `montecarlo.run_model`:
`ast.FunctionDef` named `run_model`, then `end_lineno - lineno + 1`, `ast.If`
nodes, `ast.Name` nodes with a `Store` context, and `scenario.get` calls. A
figure typed into prose here goes stale silently, which is the exact failure this
document exists to argue about.

**Six of the eight wiring mechanisms fail silently**, and they carry most of the
dataflow. The failure is uniform:

> a stage's input arrives through `dict.get`, and **absence is
> indistinguishable from the neutral value** — identity, `1.0`, `{}`, `0.0`,
> `set()`.

That is the whole answer to the question. A defect lands in a channel that was
already contributing its neutral value, so it cannot move the score. The
by-election decay is applied twice and is inert because `w_bye_local_*` ship at
`0.0`. An all-metro poll aggregate passed `polling.screen` and was saved only by
a second copy of the rule in another module. `poll_house_k` drives a cap that no
longer exists.

## What is actually wrong, in three parts

The stages are **not** missing. `run_model` calls **ten** of `montecarlo`'s own
top-level functions and **seventeen** module functions — about twenty-seven
seams that already exist, most with clean signatures where a mis-call is a
`TypeError`. `allocate_with_overhang(combined, wins, rule)` could have been
value-tested at any point. Nobody wrote the test.

| | remedy | cost |
|---|---|---|
| **~9 stages are already functions** and several have no value test — `spine`, `blended_centres`, `solve_and_predict`, `allocate_with_overhang`, `make_drawer`, `ward_parts`, `ward_pr_ratios`, `theta_prior`, `contestation` | **declare and TEST them** | no refactor |
| **~14 stages are inline blocks** in `run_model` — pool load, roster filter, seeding, universe, entrant geography, the by-election ward-local term, turnout, ward structure, the ward/PR split, the arrivals poll path, the metro-poll blend | extraction | the expensive part |
| **the orchestration between them is the silent layer** | **the bus** | moderate |

## The contract

Each unit declares what it needs and what it offers, so it cannot be wired up
wrongly:

```python
@dataclass(frozen=True)
class Unit:
    name:    str      # stable id
    kind:    str      # stage | lever | rule | constant | artefact | input
    where:   str      # (i)   module:function
    reads:   tuple    # (ii)  input names
    writes:  tuple    # (iii) output names
    does:    str      # (iv)  one sentence
    sources: tuple    # (v)   prior art, the § that adopted it, the data source
    status:  str      # live | gated | retired
    gate:    str | None
```

**`sources` is not decoration.** The project's external scholarship —
Shirani-Mehr on the two-term σ, Dominitz & Manski on non-identifiability, Powell
& Tucker's Type A/B volatility, Jackman's pooling theorem — currently lives only
in prose, in documents that have gone stale within a day. Attached to the unit
it travels with the code, and it is checkable: a `§N.M` that does not resolve
fails the build, and a data source not in `SOURCES.md` fails the build.

**The bus is what retires the defect class.** `bus.read(name)` **has no
`default=` parameter**, so the silent fallback becomes unwritable. A name no
unit declares as an output raises where it is used. A start-up set-comparison
refuses a `reads` with no producer, before the run begins.

**There is no scheduler and no graph engine.** This is a pipeline with one real
router (the route-precedence chain in `blended_centres`); a topological sort
over a linear sequence is ceremony. The declarations are **checked, not
scheduled** — and it is the declarations, not any ordering machinery, that fix
the problem.

## The four lists, all GENERATED

| | | from |
|---|---|---|
| **A** | every transformation, lever, rule, constant, artefact, with i–v | the manifest, dumped to `MODEL-MAP.json` |
| **B** | believed live / gated / retired | the `status` and `gate` fields |
| **C** | **verifiably** exercised | the bus read/write log + `sys.monitoring` line coverage, over the panel and the 2026 run |
| **D** | used **and measured** | the ablation table, `IMPACT.json` |

A and B are claims; **C and D are evidence**, and the tests assert the claims
against the evidence. Three prose registries have already gone stale
(`MACHINERY.md`, `JUDGEMENT-CALLS.md`, `POLLING.md`), so **none of these is
hand-maintained.**

**An ablation of code that did not execute is a coincidence, not a
measurement**, so every D entry carries its C evidence. §1.68 was burned by
exactly this: *"That null was measured WITH THE GATE SHUT."*

## Order of work

**A — declare and test the seams that already exist.** No refactor.
`allocate_with_overhang` first: a constructed council where `deduct`, `expand`
and `cap` give three different answers, all three pinned.

> **✅ A IS DONE — 2026-08-26, MODEL-LOG §1.97.** Seven seams had no value test
> (`make_drawer` and `contestation` already did). 111 tests; the suite goes 207
> → **349 passed, 0 failed**; `src/` byte-identical throughout. Verified by
> **mutation**, not by passing — 55 of 63 mutations of the source were caught,
> two survivors provably equivalent, six real gaps recorded.
>
> **It found about thirty-five defects without changing a line of the model**,
> and they are the class this document predicted. The sharpest:
> **`spine_k` cannot be set to zero** (`scenario.get("spine_k") or SPINE_K`, and
> `0.0 or 1.0` is `1.0`) — and fixing that alone crashes `run_model`, because
> `levels.py:882`'s `w = k / (worth + k)` is `0.0/0.0` for ActionSA at 2026.
> **`solve_and_predict` returns a half-solved answer when it fails to converge**,
> silently. **`theta_prior`'s groups block is read under a key it does not
> have**, so a `0.8` default always wins. **The by-election decay really is
> applied twice.** Three copies of one crosswalk, and a producer/consumer
> directory mismatch.
>
> **These are found, not fixed.** Each is owed a decision, and where one moves a
> number the backtest against real results adjudicates it — never the freeze.

> **⛔ STATUS, ADDED 2026-08-29 — B AND C ARE NOT STARTED, AND C'S TARGET IS
> GROWING.** Without these markers this file reads as a plan in progress. It is
> one third executed and two thirds dormant.
>
> * **B — NOT STARTED. Zero code.** There is no bus module and no `bus.read`
>   call anywhere in `src/`; the only occurrence in the repository is this
>   document being quoted inside a test docstring.
> * **C — NOT STARTED, and `run_model` has grown 19% since this file was
>   written.** Measured by AST at both commits: **1,107 lines on 2026-08-25**,
>   the day this document was written, against **1,315 today**. `montecarlo.py`
>   went 3,457 → 4,915, up 42%. The closing line of this file — *"`run_model`
>   grew from 863 lines to 1,315 while the work was deferred"* — is still being
>   written, in real time.
> * **Three of the four generated lists do not exist**, and never have:
>   `MODEL-MAP.json` and `IMPACT.json` have never been created in any commit in
>   this repository's history, and the `sys.monitoring` line-coverage half of
>   list C does not exist. List B exists for scenario levers only.
> * **The nine-field declaration is an ASPIRATION, not a practice.** No unit
>   declares itself. There is no `class Unit`, no `reads=`/`writes=` anywhere.
>   Of the nine fields, only `name` and `where` are machine-recoverable for any
>   unit, and both come free from Python rather than from anything adopted here.
>   The nearest real thing is the registered-null record in the lever test,
>   which covers five of the nine fields — **for levers, not for units.**
>
> **Recommendation recorded 2026-08-29, owner's call:** do not start B or C, and
> do not build `MODEL-MAP.json`, before 4 November. The silent-neutral defect
> class this file targets is currently being caught by cheaper machinery built
> *after* it — the delivery log, the registered nulls, the gates — which is
> finding real faults. Extraction would move forecast numbers with ~60 days to
> polling, and every move needs a sixteen-city-year paired backtest to
> adjudicate, with the freeze explicitly barred from arbitrating. A manifest
> also cannot reach the inline stages where this document says the defects live,
> so it would document the well-behaved third and be silent on the rest — which
> reads as coverage without being coverage.
>
> **The one cheap piece worth doing now:** this file promises that *"a `§N.M`
> that does not resolve fails the build"*. That test does not exist and is about
> an hour's work. It guards the exact rot this project keeps hitting — a
> citation to a renumbered or never-existent MODEL-LOG section, the same class
> that put 24 wrong line numbers into the constants register.

**B — replace the silent orchestration with the bus.**

**C — extract the ~14 inline stages**, each justified by a specific pain, each
landing with the value test its new seam makes possible.

### ⛔ The freeze is a tripwire, never a gate

**CORRECTED 2026-08-25 by the owner.** An earlier version of this section read
*"every commit must reproduce `forecast_frozen.json` to the seat or be
reverted"*. That is benchmarking against a broken implementation, it violates
`CLAUDE.md`'s standing rule, and it is actively harmful here:

> **"Reproduce the old numbers or revert" enshrines the current bugs as the
> definition of correct.** If an extraction changes a number it may have FIXED
> something — the poll channel was worth −6 and nobody knew (§1.94), the
> by-election decay is applied twice, `allocate_with_overhang` has no test. A
> rule that reverts any change on those paths protects the defects.

**So: when a change moves a number, the question is never "does it still
match?". It is "does the backtest against REAL ELECTION RESULTS improve?"** —
paired, cycle-replicated, against `ITERATING.md`'s four keys, on the sixteen
city-years.

The freeze still earns its place, for two things that are not evaluation:
recording what we published and the configuration that produced it, so the
forecast can be held to account after 4 November; and telling you *go and look*
when something moved that you did not expect to move. Investigating a surprise
is not the same as requiring agreement.

**The goldens are likewise not a standard.** They are not re-recorded silently —
a silent re-record destroys the only record of what changed — but a golden that
disagrees with a better model is the golden that is wrong.

## Why `ARCHITECTURE-PROPOSAL.md` was rejected

It was written 2026-08-18 and recommended deferring the restructure. Its
diagnosis was right and two of its five arguments still hold — **no scheduler**,
and **the draw loop stays whole** (a per-draw IPF over 1500 draws sharing arrays
is one unit). Three do not:

- *"Sequential locals read quite well; extraction can make data flow harder to
  trace."* Conflates **reading** with **verifying**, and attacks a strawman:
  extraction into a shared mutable dict does make dataflow harder to trace —
  that is what `run_model` already does with `scenario`. Extraction with
  *declared* interfaces is the opposite. Asserted of 223 locals; there are now
  228 across 74 branches.
- *"A manifest catches 3 of 5 defects."* That scores a **run manifest** —
  per-run paths and hashes — not declared interfaces. Different artefact,
  different failure mode.
- *"A refactor cannot improve prediction, so it can only be neutral or bad."* A
  category error. `ITERATING.md` governs changes to the **forecast**; the
  ability to verify is not one, and by that reasoning one would never write a
  test. Empirically false as well: instrumenting is what revealed the poll
  channel is worth **−6** and not **+48** (§1.94).

Its deferral condition — *"restructure against frozen numbers"* — is now met by
`src/freeze.py`. And `run_model` grew from 863 lines to 1,315 while the work was
deferred.
