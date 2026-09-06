# State of the branch when the ultra review is run

**Written 2026-09-02. The brief itself is `ULTRA-REVIEW-1-pools-reemit.md` and is
FROZEN — read it, do not amend it.** This file records only what a reviewer needs
to know about the tree they are looking at, and it is not part of the hunt list.

## ⛔ HOW THIS REVIEW IS SCOPED, AND WHY THE COMMIT LOG IS ONE ENTRY

**The tool derives its diff from `merge-base(base, HEAD)`, not from the base's
tree.** So a base is only useful if it is an **ancestor** of what you are
reviewing. `ultra-review` is a child of `ultra-review-base`; their merge-base is
the anchor, and the diff is **37 files / 7,162 lines**. The reviewed tree is
**byte-identical** to the working branch `splinter-rule-and-historical-tail`.

Two earlier attempts failed, both loudly and before billing, and both are worth
knowing because they are easy to repeat:

| attempt | merge-base | result |
|---|---|---|
| no argument | `origin/main`, **228 commits back** | 276 files / 175,083 lines — too large |
| anchor built as a CHILD of HEAD | HEAD itself | **zero files** — an empty diff, which reads exactly like a clean review |

⚠️ **`.tidyignore` says `main` is pinned because "the no-argument review bundles
`main..HEAD`". That is wrong** — the no-argument form resolves `origin/main`
first and only falls back to the local ref. Pinning local `main` does not affect
it.

**Held constant by the anchor**, because they are artefacts and process records
rather than work to review, and together they put the diff ten times over the
limit. **All are present in this tree — read them here:**

`archive/pools-*` (~51,000 lines) · `data/processed/**` (~9,800) ·
`MODEL-LOG.md` (~2,100) · `BATCH-PLAN` · `SOURCES` · `DATA-QUALITY` ·
`ITERATING` · `HANDOVER` · `PLAN-TO-LIVE`

**`MODEL-LOG.md` §1.160 onward is the evidence base for most measured claims in
this diff.** It is not in the diff; it is in the tree.

⚠️ **`git log` shows one commit. The batch is 37** and their messages are
load-bearing — hunt 12 directs you at commit messages specifically:

```
49ee29e Freeze the ultra-review brief before the batch is written
56467db Phase 0: the C and D terms reach the forecast allocator
dc0259f Phase 0: the statute leaves the lever surface
9f9ac9e Phase 1a: bound the rate estimator, measure the turnout band
cacdbaa Phase 1b: fix the guard's population, and stop it overstating
e234cb8 Point the ultra review at the 20 files that are code
8d19f20 Record the batch plan and its checklist in the repository
b6834d4 R0a: the two ward-reach readers agree exactly, and one is ungated
0a0c994 R0b: the attribution anchor, and the band accuracy hypothesis is refuted
b55f388 R1: entries 1, 2 and 6, each caught by a constructed violation
309ca73 Add MemPalace wing + agent identity header to CLAUDE.md
a076e29 R1b: the turnout band was set by one broken row, and correcting it wins
aeb690a Tick R1b on the batch checklist
fb284b8 Correct the entry-6 population claim on the checklist
af054e3 R2: the artefact key was scanning the wrong population
310a274 Tick R2; record the sweep that nearly emptied the review scope
d5dff8f R2 follow-up: the key was still short by four inputs, one of them new
3628dae A 0.1% national-share floor on who is assumed onto an unheld ballot
aaf8f62 Correct §K1: it is the metro's national-election share, and it costs two seats
30148cc Exempt this repository from projects-tidy
6eba396 The blind review of the roster floor: value survives, three arguments do not
44d309c Record that a truncated suite read prints no banner
4e3b6eb R3: the roster seam -- three states, and only two may delete a party
bcd3090 The roster seam did not work, and the strength knob it advertised had no reader
7a74af0 The second blind review: six more, and the group budget is right by accident
5b84835 R-1 settled by measurement, and the plan's own answer is withdrawn
59a975f The coupling was recorded in one direction only
43cc86a Pollster concurs on the review timing; a phantom arrival, and a naming collision
4cf6499 Pre-register R4 properly, and correct two defects the blind review found in my own work
e56f8bc R4: the record widened, and every pre-registered prediction held
2892113 The blind review of R4: four predictions held, pointed at the wrong things
ceb3ddb The owner's reading beats mine: a trend, a transfer and an abstention, counted three times
cec0627 Omit the old elections from the pool split; book the owner's replacement mechanism
0343ac9 Sentiment is per-pool and signed; and the data question is retrospective availability
5b043d4 R5: the undeclared-split detector, emitted into the spec rather than printed
f30b1bc Full suite green on this tree; review state brought up to date
29348ed The howler check: four real ones, two of them mine
7eadb07 The review anchor was a DESCENDANT of HEAD: the diff would have been empty
48ceb2b Pre-register the per-level rate bound before touching it
f3eb2f5 The bound was clipping a quantity the model computes as >1; and P3 is falsified
2688b5f Surface the clip, fix its misattributed message, and four review findings
```

**If the diff comes back empty, stop and say so. Do not report it as clean.**

## ⛔ TWO HUNT ITEMS POINT AT WORK THAT WAS NEVER STARTED

The brief is frozen and correctly cannot be amended. This is the delta.

| hunt | status |
|---|---|
| **2** — reconcile `entrant_actual_for` / `arrival_group_score` baselines | ⛔ **DEAD.** `src/backtest.py` and `src/compare_history.py` are byte-identical to `main`. Entry 4's second step was not written. Its ⛔ *"do not recommend reverting it"* will read as live; there is nothing to revert. |
| **3** — verify the new config against the **deleted** `SPLITS` / `TYPE_A_EVENTS` | ⛔ **DEAD.** Neither is deleted. `SPLITS` is still a dict literal in `pools.py`; `TYPE_A_EVENTS` still lives in `levels.py`. Entry 5 was written in a narrow form that moves no table. |
| **1** — the new reader vs `levels._citywide` | ✅ live, and `src/levels.py` **is** in this diff. |
| **9** — what breaks at 2026 | ✅ live, and it is now the most important item: R3/R4/R5 all postdate the freeze and only hunt 9 reaches them. |

## ⚠️ AND ONE ADDITION TO WHAT WE ARE ASKING FOR

Hunt 10 asks whether the turnout band was tuned to a coverage statistic. The
evidence offered for it is *coverage 13/24 → 21/24, mean width 21.5pp → 38.6pp*.
**Those two numbers cannot settle that question**, because coverage is gameable
by widening and a 79% width increase buying eight city-years is exactly the
trade a coverage-maximiser makes.

**Please score citywide turnout properly — CRPS or log score, out of sample,
against persistence.** If the band is better rather than merely wider, CRPS
improves; if it is wider only, CRPS worsens while coverage improves. That is the
tell, and it does not require amending the brief because hunt 10 already asks
the question.

## Where the substance is — read this before opening the diff

`main` was fast-forwarded on 2026-09-02 so that **the diff is this batch and
nothing else**: five commits rather than the 194 the working branch had
accumulated. What remains is still 86 files, and only 20 of them are code:

| | files | insertions |
|---|---|---|
| **`src/` and `tests/` — THE REVIEWABLE SURFACE** | **20** | **2,355** |
| `data/processed/history.json` | 1 | 19,875 |
| `archive/pools-preemit-*/` | ~40 | ~25,000 |
| `MODEL-LOG.md` and other prose | rest | ~2,500 |

**The two large blocks are reference material, not changes to review.**
`history.json` is a generated scoreboard artefact and its size is an artefact of
the panel going 21 → 24 city-years. The archives are the pre-emit specs **this
brief explicitly asks to be supplied alongside the diff** — they are there to be
consulted, not audited.

The five commits, oldest first:

    49ee29e  freeze the brief; also carries the §1.160/§1.161 delimitation and
             crosswalk work that was uncommitted in the tree at the time
    56467db  Phase 0 — C and D reach the forecast allocator
    dc0259f  Phase 0 — the statute leaves the lever surface
    9f9ac9e  Phase 1a — bound `_nnls`, measure the turnout band
    cacdbaa  Phase 1b — fix the guard's population and its overstated message

⚠️ **`49ee29e` is a fat commit and that is a defect in how it was made**, not a
signal about its contents: `git add -A` swept the brief amendment together with
the delimitation fix. The brief's amendment section says the delimitation work is
part of the batch and should be seen in the diff, so nothing is hidden — but a
reviewer should not read the commit boundary as a scope boundary there.

## ⛔ "ENTRY 7" NAMES TWO DIFFERENT CHANGES. READ THIS FIRST.

The brief's entry numbering and `POOLS-REEMIT-QUEUE.md`'s row numbering are ONE
namespace: the brief uses **1-6** for the queue's rows and **7-10** for its own
amendments. Both of these are live in this batch:

* **Brief entry 7 = the turnout band** (§1.162 §9). Written, committed,
  un-emitted. Hunt items 10 and 11 are about this one.
* **Queue entry 11 = the arrival group budget** (§1.179). *Not yet written.*
  Filed on 2026-09-03 as "entry 7" by mistake and renumbered to 11 the same day;
  if any stale reference to "entry 7" meaning the arrival budget survives
  anywhere, it means this one.

The brief is frozen and is not amended for this. The disambiguation lives here
because this file is explicitly not part of the hunt list.

## Two things the brief predates, and cannot ask about

1. **R3, the declared-nomination-list roster seam**, landed after the freeze
   (§1.177, §1.178, §1.179). It is reviewable only under the generic hunt 9.
   It is also the only path in the batch that runs for the first time **in
   production**, on the live forecast, on 16 September. A reviewer who wants a
   target should start at `pools.resolve_roster` and `pools.arrival_rules`.
2. **Queue entry 11 and the R-1 decision** (§1.180, JUDGEMENT-CALLS §L6). Entry
   4 in the brief's hunt list is now one third of a single change; the other two
   thirds are not in the brief because they did not exist when it was frozen.

## The bidirectional obligation applies to the artefact key too

`CLAUDE.md` §4 point 0 asks a scan-shaped claim to assert BOTH directions. The
`artefact_key` was wrong twice in this batch — `af054e3` *"scanning the wrong
population"*, then `d5dff8f` *"still short by four inputs, one of them new"* —
and both were failures of the **code → key** direction. Hunt 6 asks the
dangerous direction (does it still change when it should). The complement worth
checking is whether anything a spec is built from is still outside the key;
`MACHINERY.md` names the ones known to be, including one flagged there as **a
real gap, not a decision**.

## The tree is deliberately un-emitted

`pools_*.json` on disk carry **`pools_sha 86995c914b530216`**, which is the key
from BEFORE this batch. The `pools.py` changes in the diff have not been emitted.

That is the brief's own sequence — *"write the changes → archive the specs → THIS
REVIEW → fix what it finds → one-writer window, emit → re-take compare_history"*
— and it is why a diff exists to review at all. **All 26 pre-emit specs are
archived at `archive/pools-preemit-2026-09-02/`** so the reviewer has the
artefacts alongside the code, which the brief asks for.

## The suite, run in full on this tree — 451 passed, 5 failed, 17 skipped

**2026-09-06, all 31 modules, 813s wall clock, no `PARTIAL RUN` banner, run at `54a8f97` — HEAD.** The
five failures are the ones tabled below and nothing else. The code's
`pools_sha` is now **`5184140a15336387`**; the specs on disk carry
**`86995c914b530216`**, from before the batch. That gap is the point — see
below.

## ⛔ TWO OF THE FIVE FAILURES ARE LIVE DEFECTS, NOT EXPECTED ONES

This table said all four were "resolved by the emit". **Two of them are not**,
and both were found by review rather than by the suite. A red test everyone is
told to expect is a red test nobody reads — that is why this is now first.

| test | verdict |
|---|---|
| `test_the_three_known_things_hold_at_once` | ⛔ **LIVE.** It never opens a spec — it calls `pools.fit_city` directly, so the emit cannot resolve it. Mangaung 2016's Indian/Asian pool has **3,531 registered voters and a fitted turnout of exactly 0.0000**, so its rates sum to zero. That pool is degenerate at all three targets. §1.188 |
| `test_no_emitted_composition_weight_is_arithmetically_impossible` | ⛔ **LIVE, and structural.** At Buffalo City 2011 the DA is fitted taking **100% of the Coloured, Indian/Asian and White pools at once** — those cast 7.6% of the vote combined against the DA's actual **20.26%**, so at least 12.7 points must come from the Black African pool, i.e. ≥62% of its vote against a fit saying 39.5%. The fit systematically under-attributes the DA to the dominant pool. **Pre-existing, not introduced here, and NOT fixed here.** §1.189 |
| `test_every_emitted_pool_spec_carries_a_current_artefact_key` | ✅ expected — every spec correctly reports stale until the single post-review emit |
| `test_the_documented_figures_match_the_committed_artefact` | ✅ expected — it reports `ITERATING.md rule 8 says ranks 1-3 n = 63; history.json says 72`. The panel grew from 16 to 24 city-years and rule 8's tables were never re-measured onto it |
| `test_the_freeze_records_every_environment_switch` | ⚠️ **NEW AND EXPECTED, 2026-09-06.** The published freeze records neither `HELD_BACK_OFF` nor `JHB_SCORE_NO_RELABEL`, because both were added to `freeze.ENV_SWITCHES` after it was taken. **That gap IS the finding**, now reported instead of silent — the first empties the pre-2011 quarantine and moves every band width; the second changes what the scorer is, worth 40 coherent seats. Resolved by re-taking the freeze in the emit window |

⚠️ **The DA/White corner was pre-registered as possibly an artefact of the rate
bound (§1.189 P3) and the prediction was FALSIFIED**: fatal cells went 18 → 17,
Buffalo City and Nelson Mandela Bay unchanged, Cape Town marginally worse. It is
its own defect and it is the best-evidenced open problem in the tree.

## The remaining three, and why they are red

| test | why it fails now | resolved by |
|---|---|---|
| `test_no_emitted_composition_weight_is_arithmetically_impossible` | reads the specs on disk, which predate the bounded `_nnls` and the measured turnout band | the emit |
| `test_the_three_known_things_hold_at_once` | ⛔ **THE LABEL WAS WRONG.** This test never opens a spec — it calls `pools.fit_city(...)` live (`test_pool_bounds.py:57-72`), so **the emit cannot resolve it**. Mangaung 2016's Indian/Asian pool has 3,531 registered and a fitted turnout of exactly 0.0000, so its rates sum to 0 and the row reads `[1, 1, 0, 1]`. It is the only one of the ten `FITS` entries that fails, and Mangaung's Indian/Asian pool is degenerate at all three targets. **This is a live defect in the fit, previously carrying an 'expected, ignore' label.** | **NOT the emit. Unresolved.** |
| `test_the_documented_figures_match_the_committed_artefact` | `ITERATING.md` rule 8 quotes 21 city-years; the panel is now 24 | re-record on the post-emit baseline |
| **`test_every_emitted_pool_spec_carries_a_current_artefact_key`** | **expected from R1 onward.** Each queued entry moves `pools_sha`, so every emitted spec correctly reports STALE until the single post-review emit. This is the artefact key doing its job, not a defect | the emit |

⛔ **READ THIS BEFORE CHASING A MISMATCH: THE SPECS CONTRADICT THE CODE ON
PURPOSE.** `data/processed/**` holds the PRE-BATCH emission. Every change in
this diff is un-emitted, deliberately, because the brief requires this review to
happen **before** the emit — afterwards there is no clean baseline to compare
against. So the artefact key correctly reports every spec stale, and two
pool-bounds tests correctly fail against numbers the new code no longer
produces. **None of that is a defect and none of it is worth reviewer time.**

⚠️ **What IS worth reviewer time in that area:** whether the two pool-bounds
failures are red because the *stale specs* violate bounds the new code enforces
(in which case the emit resolves them, as claimed) or because the *new code*
would emit out-of-bounds values (in which case it does not, and the batch
carries a live defect). That has not been separated and it is the cheapest
high-value check on the list.

⚠️ **A red test everyone is told to expect is a red test nobody reads.** Any *other* failure in `test_chain` from here on is a real one.

⚠️ **Reading a suite result before it finishes gives a clean-looking lie.** A
`-k` subset prints a loud `*** PARTIAL RUN` banner; a **truncated full run prints
nothing at all**. On 2026-09-03 a read taken while the serial `test_chain` module
was still going reported *"395 passed, 3 failed"* — plausible, close to the real
figure, and missing 42 tests including one of the expected failures. The real
result was **437 passed, 4 failed**. **The tell is `WALL CLOCK` in the output:
if it is absent, the run did not finish and the counts are not the counts.**

⚠️ **A reviewer should be suspicious of exactly this arrangement** — "it will be
fixed by the emit" is unfalsifiable until the emit happens, and the emit is after
the review. Two of the three are checkable now without emitting, by computing the
band and the rates directly; §1.168 records those measurements (coverage 13/24 →
21/24, mean width 21.5pp → 38.6pp) and they are the evidence, not the promise.

## What landed BEFORE this window and is measured

**Phase 0 (§1.163, §1.166, §1.167)** is committed and has its own baseline. It
touches `montecarlo.py`, `seats.py` and `benchmarks.py`, not `pools.py`, so it
did not move `pools_sha`:

* the C and D terms reach the forecast allocator; measured **number-neutral on
  the 21 common city-years** (seat error 545 → 545, CRPS 439.199 → 439.200);
* **the panel went 21 → 24 city-years** — Johannesburg, Tshwane and Cape Town
  2011 had been failing the F42 guard on what §1.160 wrongly called a truncated
  party name, and are in fact the D case;
* `overhang_rule` is refused any non-statutory value at the `--set` boundary and
  is out of the lever sweep.

**The baseline every post-emit number must be compared against is the 24
city-year run recorded in §1.166**, not the 21 city-year run before it.

## ⚠️ An operational hazard, recorded because it nearly cost the review

**2026-09-02 23:06.** A `projects-tidy` job in another session committed this
session's in-flight work as *"Save work in progress (4 file(s))"* **and moved
`main` to that commit.** The content was exactly the round in progress and
nothing was lost — but `main` is what defines this review's diff, so for a
period the review scope was **zero commits**. A `/code-review ultra` launched in
that window would have reviewed nothing and reported nothing wrong.

`main` has been restored to `a138788`, the review cut, and the scope is 15
commits again. **Anyone launching the review should check
`git rev-list --count main..HEAD` is non-zero first** — a review of an empty diff
is indistinguishable from a clean review.

## What is NOT in this batch, deliberately

* **The fit-time capacity constraint.** Proposed, then refuted: one was built,
  measured and reverted (§1.41, coherent seat error 306 → 486), and IPF already
  imposes the pool margin on every draw. §1.165.
* **Transitional-party level error** — COPE +36.5pp across 2011, ActionSA
  −12.57pp at Johannesburg 2021. Larger than anything in this batch, and the
  owner's decision was to fix what is internally broken first.
* **Forecasting independents**, which is what would actually close the eThekwini
  C-term gap.

## What landed AFTER the freeze, which the brief cannot ask about

The brief was frozen before these existed. Each is reviewable only under the
generic hunt 9, and each touches the live forecast.

| | what | where |
|---|---|---|
| **R3** | the declared-nomination-list roster seam, three states, and the sizing knobs beside it | `resolve_roster`, `declared_roster`, `arrival_rules` |
| **R4** | the 2000/2006 reader wired into three sites — and **deliberately NOT into the fourth** | `measure_pool_ratios`, `entrant_record`, `arrival_group_record`; **not** the `emit_pools` split-sample loop |
| **R5** | the undeclared-split detector, emitted into every spec | `unclassified_with_national_record` |

⛔ **The single most reviewable decision in the batch is the site R4 does NOT
touch.** Wiring the fallback into the split-sample loop moved the per-pool
concentration — `JUDGEMENT-CALLS` §B's *"dominant width lever, 83-98% of drawn
variance"* — from `[15.61, 22.58, 21.51, 21.94]` to `[12.73, 14.54, 16.15,
22.42]`, an 18-36% widening of the published forecast on three of four pools. It
was reverted on the evidence in **MODEL-LOG §1.184**: fit the concentration per
era and the pooled value sits **below both eras' own**, which is the signature of
a level shift read as scatter, not of newly measured dispersion. The reasoning
is the thing to attack; the arithmetic reproduces.

⚠️ **And one finding is recorded but NOT acted on:** `arrival_group_spec`'s
concentration moved 4.357 → 9.758 at 2021 (+124%) and nothing pre-registered it.
It is inert only because `arrival_group_draw` defaults to `False` — **and the
CRPS 85.9 → 109.9 measurement that retired that lever was taken at 4.357, so it
no longer describes the spec the lever would read.** §1.183.

