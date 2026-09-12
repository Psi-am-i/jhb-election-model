# Handover — 2026-08-29, with a 2026-09-12 banner

> ## ⛔ STATE AT 2026-09-12 — READ THIS FIRST
>
> **THE POLL CHANNEL IS SWITCHED OFF. THE FORECAST USES NO POLL AT ALL.**
> `montecarlo.DEFAULTS["poll_paths"]` is `"off"` (was `"all"`), on the owner's
> decision, taken on design grounds: the interaction between several polls was
> never designed, and he wants a per-poll reader control ("i trust / dont trust
> this poll") before it goes back in. **Nothing is deleted** — `--set
> poll_paths=all` restores the previous forecast exactly. Pre-registration
> `prereg/2026-09-12-polls-out-of-the-forecast.md`, result MODEL-LOG §1.225.
>
> **Measured, both arms, 1000 draws, 24 rows, run serially on one tree:**
>
>     seat_abs_err_coherent  725 -> 723   (-2)
>     CRPS                 545.84 -> 541.39
>     margin over uniform swing  18.1% -> 18.3%
>
> ⛔ **DO NOT QUOTE −2 AS THE VALUE OF THE POLL CHANNEL.** Seven of 24 rows
> moved; ekurhuleni 2021 moved **+6 against** the change, joburg 2021 −4,
> tshwane 2016 −4, and seventeen rows were identical. The contribution is not
> distinguishable from zero. Every 2011 row moved by exactly zero, which is the
> clause that proves the switch does what it says.
>
> **Three consequences already handled:** the seven poll levers are inert by
> configuration and each now carries BOTH an `EXPECTED_INERT` entry and a
> `CONDITIONAL` one that opens the gate and proves it still moves;
> `polling.SIGMA_TWO_TERM` went red for the same reason and `MODULE_PERTURB`
> now takes a gate-override field rather than losing the entry — deleting it
> would have removed the sole justification for keeping `poll_house_k`.
>
> **SUITE: 460 passed, 9 failed, 17 skipped, no PARTIAL banner.** Run twice —
> once after the code was settled and again after the documentation was, because
> the register→code guard reads these files; both runs identical, and the second
> is the one these counts come from. **Eight of the nine failures pre-date this
> work and none is poll-related** — the two drifted `test_drawer` goldens were
> proved independent of the switch by rebuilding the fixture under BOTH settings
> and getting byte-identical marginals (DA mean 25.9253% either way, against a
> recorded 26.4646%), so that drift has some other cause and is not mine. The
> ninth is below and is deliberate.
>
> ### ⚠️ ONE TEST IS RED ON PURPOSE AND IT IS A DECISION FOR THE OWNER
>
> `test_the_published_pages_are_what_this_tree_builds_today` fails on
> `site/methodology.html` (and will on `index.html`). Those pages' sources were
> rewritten to say polls are no longer used; the published site is still the
> 31 August build. **Rebuilding it publishes the polls-off forecast and moves
> the headline.** That is an outward-facing act and was deliberately not taken
> here.
>
> ### ⛔ MEASURED 2026-09-12 — WHAT THE SWITCH DOES TO THE 2026 HEADLINE
>
> Joburg 2026, `poll_paths` off vs all, 1000 draws, seed 20261104, `run_model`
> called directly so nothing was published:
>
>     party   OFF median  (5-95)   ALL median  (5-95)   shift
>     DA           68    [47- 93]       79    [55-105]   -11
>     ANC          68    [31- 96]       64    [27- 89]    +4
>     ASA          27    [11- 52]       25    [10- 51]    +2
>     EFF          26    [ 8- 58]       23    [ 8- 55]    +3
>     MK           23    [ 7- 53]       23    [ 7- 52]     0
>
>     largest party   OFF: ANC 47.3% / DA 47.0%      ALL: DA 71.4% / ANC 25.3%
>
> ⛔ **THE HONEST HEADLINE IS "TOO CLOSE TO CALL", NOT "THE ANC WINS".** With
> polls off the largest-party call is a **dead heat** — 47.3% against 47.0%, a
> 0.3pp gap on 1000 draws, which is inside its own sampling error. Removing
> polls did not buy a confident wrong call; it replaced a confident call with an
> honest tie. Say it that way or not at all.
>
> ✅ **THE CALIBRATION GATE PASSES.** The polls-off DA 90% interval is [47, 93]
> and contains the polls-on median of 79. So the forecast is NOT asserting that
> the only independent reading of this election lies outside its own interval —
> which it would have been indefensible to publish.
>
> ⛔ **AND THIS RETIRES THE "83 → 77" CLAIM FOR GOOD.** `methodology.md` said
> turning polls ON moved the DA **83 → 77**. Measured, it moves the DA **68 →
> 79** — the opposite direction and a different pair. `JUDGEMENT-CALLS.md` §A7's
> "65 → 78" was right in direction and within ~3 seats in magnitude. The
> sentence was deleted rather than corrected, which was the right call: it also
> described a cap retired at §1.91.
>
> **Also landed:** the `CLAUDE.md` numbers rule rewritten to the owner's
> statement of it (*a number lives where it was generated; everywhere else
> points*); `BATCH-PLAN-2026-09-02.md` archived with a stub;
> `test_passing_a_run_directory_changes_no_drawn_number` added, because
> `CLAUDE.md` cited a test for that claim which asserted something else, and so
> did `test_levers_are_live` and `run_model`'s own docstring.
>
> **Still open:** the freeze question (see below) and a clean-tree panel (item
> 13). `site/index.html`'s poll wording (item 16) is FIXED in its source
> (`forecast-sheet.html`) and awaits the same rebuild decision as methodology.
>
> ⛔ **THE LABEL-FREE PANEL WAS NEVER WAITING ON A SETTLED TREE — IT IS WAITING
> ON A REPAIR.** `test_the_relabel_ablation_actually_withholds_the_label` is red
> and says the switch is inert: *"6.9450 with the label, 6.9450 without"*. So
> `JHB_SCORE_NO_RELABEL=1` withholds nothing, and this banner and its two
> predecessors were wrong to list it as merely unrun. It needs to reach
> `calibration_columns` and both `score_seats` calls, not only `relabel_run`.
> This matters beyond bookkeeping: `relabel_run` gives the model a correct label
> on the hardest column in the panel, chosen with the result in hand, which no
> baseline gets — so the ABSOLUTE totals (725/723) and the margin over uniform
> swing flatter the model, and nothing can say by how much until the ablation
> works. **Quote paired differences, not the margin.**
>
> **On the freeze, since the owner asked what it is for.** `forecast_frozen.json`
> is NOT an orphan: it records commit `82c61e1` with `git_dirty: false`, and
> `pools.py` at that commit re-hashes to the `dbdf171344ffd5f0` the freeze
> records — verified 2026-09-12. So the published 28 August model IS recoverable
> from git; what is not preserved is the emitted spec FILES (`data/**` is
> gitignored) and the raw inputs, which have since been refreshed (§1.222). It
> also agrees with the site's `forecast_summary.json` on **every headline seat
> median** (DA 78, ANC 63, ASA 25, EFF 24, MK 22, PA 19, IFP 2) despite the
> 1500-vs-5000 draw difference — they differ in the tails, not the headline.


> ## ⛔ STATE AT 2026-09-11 — READ THIS FIRST
>
> **The document-integrity pass is half landed; the three owner decisions and
> the two measurements are not.** Full ledger: `audits/DOC-INTEGRITY-2026-09-10.md`
> §H. It holds the pollster's 17-item work list, persisted because its only other copy was lost.
>
> **Landed, all uncommitted** — mechanical items 4, 5, 7–12: no line-number
> citations left in `MACHINERY.md` or `POOLS-REEMIT-QUEUE.md`; "sixteen
> city-years" removed as a live claim from README, MACHINERY, ARCHITECTURE and
> AGENT-PLAN, with a dated banner on `PLAN-TO-LIVE.md`; JUDGEMENT-CALLS rows whose evidence is the retired panel
> tagged **[16-panel]** (not re-measured). **One code fix:**
> `freeze._dirty_excluding` no longer raises on an out-of-repo `--json`, which
> used to throw away a completed `compare_history` run (MODEL-LOG §1.223).
>
> **Waiting on the owner:** the `methodology.md` wording (it describes a deleted
> poll cap as live); which artefact is *the* freeze; the `CLAUDE.md` "only
> MODEL-LOG holds numbers" rule; and his review of the `CLAUDE.md` §0 rewrite.
>
> **Waiting on a settled tree:** the label-free panel
> (`JHB_SCORE_NO_RELABEL=1`) and a clean with-label panel, run once, serially,
> after a commit. Nothing has been measured this session.

> ## ⛔ STATE AT 2026-09-10 — READ THIS FIRST, IT SUPERSEDES THE BANNER BELOW
>
> **The processed intermediates were audited by regeneration and 26 of the 104
> CSVs did not match what the code produces (§1.222).** Seven cities' 2021
> turnout files predated the 2026-08-09 pre-2011 archive ingest, in the column
> `montecarlo.py` reads as `ratio_pattern`. All 26 refreshed; two orphans
> (`ward_leverage.csv`, `tshwane/turnout.csv`) deleted; `fold5_parameters.csv`
> kept and flagged as **not reproducible by any invocation available today**.
>
> **Measured, pre-registered at `prereg/2026-09-10-stale-intermediates-refresh.md`:
> the 24-row seat table is BYTE-IDENTICAL before and after.**
> `seat_abs_err_coherent=725/@efa06f78+dirty/1000d/pools:843229db/rows=24` on
> both sides; `margin_vs_uniform_swing` 18.1% on both. The pre-registration's
> secondary clause ("exactly seven city-years change") is **FALSIFIED** — none
> did. The input is live (an A/B moves coalition probabilities by 0.1pp) but
> sits below seat resolution, swamped by `turnout_noise_sd = 0.08`.
>
> **`tests/test_intermediates_are_current.py` is new and now in the suite.** It
> purges every CSV from a scratch copy, re-runs every generator from empty, and
> compares. Verified by mutation: restoring the month-stale capetown file turns
> it red and names the file. Suite: **453 passed, 8 failed, 17 skipped, no
> PARTIAL banner** — the same eight as before this work.
>
> **Still open:** `turnout.csv` has no artefact key, so this can only be caught
> by that test, not by a run. The freeze has not been taken and the tree is
> dirty. The published site is still the 31 August build.

> ## ⛔ STATE AT 2026-09-08 (SECOND PASS) — READ THIS BEFORE EVERYTHING BELOW
>
> **Branch `ultra-review`, last commit `efa06f7`. FOURTEEN FILES MODIFIED AND
> TWO NEW PRE-REGISTRATIONS, ALL UNCOMMITTED.** The emit window is **shut** and
> nothing has been emitted.
>
> ### ⛔ THE QUEUE IS EMPTY. THE ONLY THING LEFT IS THE WINDOW.
>
> `POOLS-REEMIT-QUEUE.md`'s *Queued* table listed all six original entries as
> outstanding for days while **every one of them was in the tree**. Verified
> entry by entry in code on 2026-09-08 and moved to *Landed*, each with the grep
> that proves it. **This is the third tracking document in this batch to
> understate the tree** — R4's own heading (§1.197), queue entry 11, and now the
> table itself. ⛔ **AN UNTICKED BOX IS NOT EVIDENCE OF UNSTARTED WORK. VERIFY
> IN CODE BEFORE BELIEVING ONE.**
>
> **On disk:** 26 specs at `pools_sha 86995c914b530216`, schema **1**, and
> byte-identical to `archive/pools-preemit-2026-09-02/` on all 26 — the restore
> was exact and nothing has drifted. **Live code:** `pools_sha
> 1bdc972788b5082d`, schema **2**. That gap is the pending emit, and it is why
> `test_every_emitted_pool_spec_carries_a_current_artefact_key` is red.
>
> ### What landed in the working tree
>
> * The three ultra-review repairs (queue 12–14) and the violation-message
>   reword (16), all number-neutral, all awaiting the same emit.
> * **Queue entry 15 (§1.207)** — the adults reprojection was gated on the BASE
>   dimension's delimitation while reprojecting on the AGE dimension's. Fixed,
>   proved number-neutral on nine city-years, and guarded by a CONSTRUCTED
>   divergence (the branch is unreachable on today's config).
> * **The five definitions of "an arrival" are now named (§1.206)** —
>   `pools.ARRIVAL_DEFINITIONS`, a marker at each of the five computing sites,
>   and a BIDIRECTIONAL register guard. This was the recurring defect the last
>   banner flagged. ⛔ **Measuring it found a false claim in the code**:
>   `arrival_group_record` said EFF, ActionSA, COPE, GOOD, MK and the NFP were
>   all in its totals — **four of the six are in no row**, because each held a
>   preceding national vote. Only NFP (2011) and ASA (2021) ever appear, so the
>   all-arrivals/entrants-only split bites in 9 rows of 29. No number moves.
> * The two false comments claiming `read_municipality` handles the header drift
>   between `_metros/` and the `_clean` files (§1.208). It raises
>   `KeyError: 'VOTINGDISTRICT'` on a clean file.
> * `total_log_median` → `total_log_mean`. **The reader's old-key fallback in
>   `montecarlo.py` must be deleted at the window.**
> * MODEL-LOG §1.195–§1.208. §1.205 is a RESERVED placeholder — the T1 rupture
>   mixture, claimed by a forward reference in §1.201 and not yet written.
> * **Still in the tree from the first 2026-09-08 pass** (this banner replaces
>   that one; nothing it listed has been reverted):
>   `tests/test_pool_conservation.py::test_every_seeded_party_belongs_to_a_pool`
>   — green, 165 seeded parties across 8 of 25 specs; §L6 rewritten (two
>   effective observations, the constant 2.8% is an ex-post fit);
>   `DATA-QUALITY.md` item 11 given the count-outranks-census rule at the top;
>   **§L11 marked SUPERSEDED** — its evidence table spans two modules.
>
> ### ⛔ THE EMIT WINDOW IS TAKEN. 27 SPECS, ONE KEY, BASELINE RE-TAKEN.
>
>     specs        26 -> 27  (tshwane/pools_2026.json, first ever emit)
>     pools_sha    86995c914b530216 schema 1 -> 843229dbe414b6b9 schema 2
>     archived     archive/pools-postbatch-2026-09-08/   (saved FIRST, per R0b)
>
>     ⛔ BASELINE — THE FIRST WRITE-UP OF THIS WAS WRONG. See §1.214/§1.215.
>     "707 -> 706, essentially flat" compared the pre-batch COHERENT figure
>     against the post-batch MARGINAL one. Like for like, 24 city-years:
>       seat_abs_err            689 -> 706     (+17)
>       seat_abs_err_coherent   707 -> 745     (+38)   <- the headline Key 1 uses
>       CRPS                 539.41 -> 548.05  (+8.64)
>       margin over uniform swing (coherent)  20.1% -> 15.8%
>     WORSE ON ALL THREE. Found by all three blind reviewers independently.
>       by cycle    2011 seat 294 / CRPS 208.23
>                   2016 seat 129 / CRPS 115.04
>                   2021 seat 283 / CRPS 224.78
>       coherent 745 | energy 233.93 | variogram 15.04
>       arrival referee LIVE on 23 of 24: mass_pit mean 0.583, 0 outside support
>
> ⛔ **AND ATTRIBUTION WAS NOT GONE — 2011 IS A NATURAL CONTROL.** 0 of its 8
> specs carry any arrival-path change (§1.211), so its delta prices everything
> EXCEPT arrivals. It is **exactly zero** on coherent seats and +0.41 CRPS:
>
>     cycle              coherent            CRPS              columns
>     2011 (control)   329 -> 329  (+0)   207.82 -> 208.23   98  -> 98
>     2016 (ON)        124 -> 156 (+32)   108.14 -> 115.04   114 -> 175
>     2021             254 -> 260  (+6)   223.45 -> 224.78   316 -> 316
>
> **The entire regression is the arrival channel.** The turnout band, the
> winsorisation and the `_nnls` bound cost ZERO seats where only they applied.
>
> ⚠️ **The CRPS rise is denominator drift, not worse forecasting**: scored
> columns 528 -> 589 (+11.6%, all at 2016) while CRPS **per column** improved
> 1.0216 -> 0.9305 (−8.9%). Do not quote the CRPS pair until it is re-scored on
> a fixed universe. **`seat_abs_err_coherent` is immune to this** — it
> apportions a fixed council — so **+38 is the real damage and the number to act
> on.** §1.215.
>
> ### Suite on the settled post-emit tree: 452 passed / 8 failed / 17 skipped
>
> Was 451/5/17. ⚠️ **The register failure was fixed after that run and its module
> re-runs 8/8, so the tree stands at 453/7/17 by module arithmetic — NOT a suite
> run, and not to be reported as one.** **The artefact-key failure is FIXED by the emit.** Three of the
> old five stand (Mangaung's degenerate pool and the DA composition
> infeasibility — both live, both pre-existing; plus the freeze's env switches),
> and the ITERATING rule-8 one is now precise: *rule 8 says n = 63, history.json
> says 72*. **Four are new, and none is a regression:**
>
> * **`test_drawer`'s two recorded marginals** — the tripwire firing on the
>   emit. DA mean −0.5393pp at Johannesburg 2026, ANC +0.0454, EFF +0.1417.
>   ⛔ **NOT re-recorded.** `.venv/bin/python tests/test_drawer.py --record` is
>   the command and it is deliberately unrun — a silent re-record destroys the
>   only guard on the prior, so it goes with the owner's read of the baseline.
> * **`test_every_symbol_the_register_names_exists`** — the guard caught my own
>   deletion of `total_log_median` the same day. **Fixed**: it is in the test's
>   `DELETED` table now, so the absence is a decision. Module green 8/8.
> * **`test_the_relabel_ablation_actually_withholds_the_label`** — Mangaung 2016
>   scores **7.5149 with the label and 7.5149 without**. The switch is not inert;
>   the label is worth *zero* there, because that spec went from `seeds = {}` to
>   four NAMED seeds and the generic-entrant relabel has nothing to move.
>   `ITERATING.md`'s "11.52 CRPS / 2.17 points" is struck as stale in the same
>   commit. **The test is NOT patched to pass** — re-measure which city-years
>   still carry a live label, and the label's worth on 24, first. §1.213.
>
> ### What is still open
>
> 1. ⛔ **THE FREEZE IS NOT TAKEN.** `freeze.py` records `git_dirty` and the tree
>    carries the whole batch uncommitted. It waits on a commit — the owner's
>    call. Do not take it on a moving tree.
> 2. The **placebo emit** is still unrun, and now costs its own window. What
>    partly replaces it is done: the batch is localised by cycle and channel
>    (§1.211).
> 3. The **pollster SIGHTED check** against the R-1 decision.
> 4. `measure_pool_ratios` has **no caller** (§1.210) — kept, flagged, not
>    deleted. An owner decision.
>
> **What is decided and NOT built:** the T1 rupture mixture (§1.205) — intact
> θ = 1.0, rupture θ ≈ 0.16 at p = 0.25, on `spine`'s *national only* route.
> Buildable entirely in `montecarlo.py`, which is not in `_EMIT_DEPENDENCIES`,
> so it invalidates no specs and is not part of this batch. Pre-register the
> seat effect before writing it.
>
> **What is refused, with numbers:** the turnout normalisation of the arrival
> record (§1.203, confirmed §1.204 on 8,822 VDs); the per-party turnout lever
> (the DA is reliable when turnout falls and marginal when it rises — no stable
> propensity can be both); the entrant-count budget covariate (§1.200 — it lost
> on the population the budget is actually spent over).

> ## ⛔ READ THIS FIRST — the state below is from 2026-08-29 and the tree has moved a long way since
>
> **Current state is `audits/ENGINE-SUMMARY-2026-09-05.md` (where the engine
> stands) and `audits/BATCH-PLAN-2026-09-02.md` (what is in flight).** This file
> is kept for its pre-registration record, which is its whole value and must not
> be edited to fit later answers.
>
> What has changed since it was written:
>
> * **The panel is 24 city-years, not 16.** Every score quoted below is a
>   sixteen-city-year figure.
> * **There are 26 pool specs, not 18**, and they are **deliberately stale** —
>   a single re-emit is pending behind a paid code review.
> * **The suite is 451 passed / 5 failed / 17 skipped**, not 377/0/10. Two of
>   those five failures are **live defects**, not expected ones.
> * A batch of ~40 commits has landed: the turnout band, a bounded rate
>   estimator, the artefact key's population, a declared-nomination-list roster
>   seam, the 2000/2006 election results made readable, and an
>   undeclared-split detector.

# Handover — 2026-08-29 (REVISED, post-result)

**⛔ THE PRE-REGISTERED RUN HAS BEEN EXECUTED AND ITS RESULT IS READ. DO NOT
RE-RUN IT.** MODEL-LOG **§1.136 §7** carries both arms; **§8** carries what they
do and do not refute; **§9** corrects §5 of the same entry. The section
"THE NEXT RUN" below is kept **verbatim, as the pre-registration record** — it is
what was written before any number was seen, and its whole value is that it
cannot now be edited to fit the answer. Its deviations are annotated in place.

**START AT "▶ WHAT TO DO NEXT", immediately below.**

Branch `splinter-rule-and-historical-tail`. Nomination lists **16 September
2026**, polling **4 November 2026** (18 and 67 days as of 2026-08-29 — quote the
dates, not the countdown).

**⛔ THE PREFLIGHT BELOW PASSED WHILE THE REFEREE WAS BROKEN, AND CANNOT SEE
THAT.** On 2026-08-29 `git status --short` was clean, the suite was **377 passed
/ 0 failed / 10 skipped**, and `freeze --verify` said VERIFIED — while
`backtest.arrival_group_score` raised `IndexError` on **all sixteen**
city-years and had never produced a number in its life. `freeze --verify`
re-runs the MODEL and hashes its output (`freeze.py:290`); it never imports the
scoring path. **The preflight tests the model and has no instrument that can see
a broken referee.** So it now has a fourth step:

    git status --short                      # must be clean
    .venv/bin/python tests/run_all.py       # must be 0 failed
    .venv/bin/python src/freeze.py --verify # must say VERIFIED
    # AND, before trusting ANY comparison:
    .venv/bin/python src/compare_history.py --jobs 1 --draws 50 \
        --json /tmp/smoke.json --md /tmp/smoke.md
    .venv/bin/python -c "import json;r=json.load(open('/tmp/smoke.json'));\
      assert len(r)==16, len(r);\
      assert all('arrival_group' in x for x in r), 'referee did not run';\
      print('16 city-years, referee live')"

**⛔ `compare_history` CATCHES PER CITY-YEAR** (`:2224`, `:2234`) and prints
`failed: <Error>` rather than stopping. It returns 1 and prints `nothing
runnable` only when EVERY city-year fails — **if three fail it exits 0 and
writes a JSON with thirteen records**, and two arms compared on different subsets
are not a comparison. **Assert the count of 16 on both arms, every time.**

⛔ **SUPERSEDED 2026-09-05, AND IT WAS THE FIRST THING A NEW SESSION READ.**
This said *"All 18 pool specs carry `pools_sha` `dbdf171344ffd5f0`, matching the
live code — no re-emit is needed and none should be taken."* **Every clause of
that is now false**: there are **26** specs, not 18; they carry
`86995c914b530216`, not `dbdf171344ffd5f0`; the live code has moved many times
since; and **a re-emit is the whole point of the current batch** and is pending
behind a paid review. `CLAUDE.md` sends every new session to this file first,
so a stale line here is the most expensive kind in the repository.

---


---

## ▶ WHAT TO DO NEXT — the run is done and the lever is REFUTED

### 0. Close the tree first
The referee fix may still be uncommitted (`src/backtest.py`,
`tests/test_calibration_report.py`, `MODEL-LOG.md`, and the documentation
corrected in the same batch). Commit them **together**, then run the FULL suite
once on that commit. The recorded 377/0/10 predates the **three** tests
added/repaired on 2026-08-29 — do not report the old count as a pass.

### 1. Do NOT re-run the arms. Read §1.136 §7.
The lever fails pass conditions **1, 2 and 3**; condition **4 passes** (all eight
2016 city-years byte-identical). **It refutes THIS LEVER, not the idea of
scoring arrivals as a group** — §1.136 §8 is explicit and the distinction must
survive every later citation.

### 2. ★ THE ONLY DATED ITEM: the roster seam, BEFORE 16 September
`POOLS-REEMIT-QUEUE` entry 3. `pools_2026.json` carries `arrival_group: null`
because `contesting_parties` and `_ward_reach` both read the target's **result
file**, which does not exist at 2026. Feeding a published nomination list needs a
declared-roster path — a `pools.py` change, so it moves `pools_sha`, so it forces
the full **eighteen-spec re-emit → baseline → freeze** under the one-writer rule.
**Land it before the model freeze, so 16 September is a data drop and not a code
change under deadline.** It is needed whatever any lever does.
`PLAN-TO-LIVE.md` A5 called this "dated and mechanical"; it is neither.

### 3. The model question this channel now poses
Build a lever that replaces **only** the generic `ENTRANT` slot and **leaves
`arrival_rules`' splinter seeds standing** (§1.136 §8). That is the untested
version of the group estimator; the tested one deleted the seeds, and the seeds
do real work — Ekurhuleni's incumbent arrival-mass error is **+0.0002** and the
lever turns it into +0.0702. Pre-register it first, and **name a pass condition
the code can actually compute** (see the two deviations annotated in §3 below).

### 4. Widening to a second cycle is now a filed, verified defect
`POOLS-REEMIT-QUEUE` entry **4**, and `DATA-QUALITY.md` item **14**.
`pools.metro_file` cannot resolve the 2000 and 2006 metro results **which are on
disk and reconciled**, so `entrant_record` before 2016 is empty and all eight
2016 specs carry zero seeds. It is wiring, not missing history. ⚠️ **This entry
moves NUMBERS, not only `pools_sha`.**

### 5. Get an owner ruling on the 27 August Track B gate
`PLAN-TO-LIVE.md`'s own rule drops Track B if A1, A2 and the A4 content decision
are not done by 27 August. A1 is done; **A2 and A4 are not** —
`content/joburg/stats.toml` still carries eleven `mode="fixed"` tokens sourced to
`turnout_tilt_da`, **a lever `run_model` no longer has**. That date has passed.
Until the owner rules, this file and `PLAN-TO-LIVE.md` give opposite
instructions.

---

## ▶ THE NEXT RUN — the PRE-REGISTRATION RECORD (executed; do not re-run)

**Written 2026-08-29 BEFORE any of it was run, so no pass condition and no
predicted sign can be chosen after seeing a number.** Read this section top to
bottom and do exactly what it says. MODEL-LOG §1.133, §1.134, §1.135.

### What is being tested and why

The **group arrival mechanism** (`pools.arrival_group_spec`,
`montecarlo.arrival_group_draw`) was built, measured and rejected at CRPS
85.9 → 109.9. **That rejection is not admissible**: it was scored through
`backtest.entrant_actual_for`, which relabels the model's nameless `ENTRANT`
onto `max(newcomers, key=seats)` — the seat-winning newcomer with the most
seats, **chosen with the outcome in hand**. `montecarlo.py` concedes it: *"the
slot it replaces was scoring well for a reason that is not skill."* This is a
re-run of that comparison with a referee that cannot be handed the answer.

### 0. Preflight — do not skip, and abort on any failure

    git status --short                      # must be clean
    .venv/bin/python tests/run_all.py       # must be 0 failed
    .venv/bin/python src/freeze.py --verify # must say VERIFIED

> ⛔ **ANNOTATED 2026-09-05, NOT EDITED.** Every line of the preflight below is
> now false, and a session following it would draw the wrong conclusion four
> ways: the suite is **451 passed / 5 failed** (two of the five are live
> defects), `freeze --verify` speaks for a pre-batch artefact, the code hash is
> **not** `dbdf171344ffd5f0`, and there are **26** specs rather than 18. **A
> re-emit is not merely permitted — it is the pending step of the current
> batch.** Kept verbatim because this section is the pre-registration record and
> its value is that it cannot be edited to fit later answers.

Confirm the artefacts are live (they were at the time of writing — **no re-emit
is needed and none should be taken**):

    .venv/bin/python -c "import sys;sys.path.insert(0,'src');import pools;\
      from pathlib import Path;print(pools._code_sha(Path('src/pools.py')))"
    # must print dbdf171344ffd5f0, matching all 18 specs

**⛔ Do NOT run `pools.py --emit`.** The keys match; re-emitting while measuring
is the hazard `CLAUDE.md` names twice.

### 1. The two arms — neither writes the committed artefact

    .venv/bin/python src/compare_history.py \
        --json /tmp/arm_incumbent.json --md /tmp/arm_incumbent.md

    .venv/bin/python src/compare_history.py --set arrival_group_draw=true \
        --json /tmp/arm_group.json --md /tmp/arm_group.md

`--set` is the only honest way to move this lever: editing `DEFAULTS` does not
reach a run, because `apply_city` writes the city TOML over it afterwards.
Verified: `arrival_group_draw=true` parses to a real boolean.

### 2. What decides it

**PRIMARY — the label-free arrival score.** Each city-year record now carries
`arrival_group`: total mass and total seats taken by parties with **no NPE
baseline**, forecast against realised, assigned to nobody. Compare `mass_err`,
`seats_err`, `mass_pit`, `seats_pit` across the arms.

**SENSITIVITY PAIR — the relabelled score** (`crps`, `seat_abs_err_coherent`).
Report it **beside** the label-free one, never instead of it. **If the two
disagree, that disagreement is the finding**, and it is the whole reason this
re-run exists.

**KEY 1** — paired, per city-year, **reported by cycle separately**.
**KEY 2** — CRPS and the level-free width statistics on `reference`, which is
untradeable. Use the new `by_cycle`, `leverage`, `by_p_any` and
`probit_quotable` fields; a band marked unquotable may not be cited.
**KEY 3** — the mechanism replaces a typed generic slot with a fitted group, so
price the derivedness honestly in both directions.

### 3. Pass conditions, fixed now

1. The **label-free** `mass_err` and `seats_err` must improve at 2021, on the
   pooled 8 metros **and** in at least 5 of the 8 individually.
2. **Key 2 must not worsen.** Untradeable.
3. The improvement must **survive removing the two largest arrival columns**
   (Cape Town's Cape Coloured Congress, and ActionSA at Johannesburg). If the
   whole gain is those two, it is a two-observation fit and **it does not ship**.
4. The **2016 arm must come back byte-identical**. See the tripwire below.

> **⛔ TWO DEVIATIONS, RECORDED 2026-08-29. The conditions above are NOT edited.**
>
> **(a) Condition 1's "improve" was never pinned to a direction.** `mass_err` and
> `seats_err` are **signed** (`actual − forecast_mean`, `backtest.py`), and no
> document pinned "improve" to `|error|`. It was pinned to **|error|** in the
> review *before* the arms were read, consistent with `seat_abs_err_coherent`
> elsewhere — but it was choosable, and it flips the reading at buffalocity and
> mangaung, the only two metros the challenger wins. The verdict is 2/8 under
> either reading, so nothing turned on it. **No future condition may name a
> signed quantity without saying which direction is better.**
>
> **(b) Condition 3 was NOT EXECUTABLE AS WRITTEN.** `arrival_group_score`
> returns group **totals** only — there is no per-column breakdown and nothing in
> the codebase can drop a named arrival column from it. It also names ActionSA
> where the leverage instrument it echoes (`compare_history._band_splits`) names
> **Johannesburg's PA**, which §1.135 established is *not* an arrival at all.
> What was actually run is a **metro-level** leave-two-out (drop Johannesburg and
> Cape Town): Σ|mass_err| 0.1212 vs 0.2709, Σ|seats_err| 20.53 vs 49.46, pointing
> the same way. **That is a stronger test than the one written, and it is still a
> deviation.** A pre-registration the code cannot execute is one that gets
> reinterpreted after the fact.

### 4. Predicted signs — recorded before the run

* ⛔ **SUPERSEDED 2026-08-29 by MODEL-LOG §1.136 §4, recorded BEFORE arm B was
  read. Kept unedited below, because a pre-registration revised after the fact is
  not one.** The **"2016"** half is right, but it silently REPLACED §1.133's and
  §1.135's recorded *"2016 worsens"* with no dated note — and both MODEL-LOG
  halves were themselves wrong. The **"2021 should improve"** half is **REFUTED**:
  measured incumbent arrival mass at Johannesburg was 9.52% against a realised
  19.99%, the challenger's expected arrival mass is 2.17%, so it was predicted to
  score ~7pp WORSE — realised **+17.76pp** against a prediction of +17.8pp.
* **2021 should improve; 2016 should not move at all.** §1.48's trace has the
  entrant rescale pulling the top of the ballot 7–9% below its centre; at 2021
  ranks 1-3 are over-forecast by **+15.48pp** so taking mass off the top is
  directionally right.
* **⛔ 2016 IS A NULL ARM AND IS THE STRONGEST TRIPWIRE IN THE SET.** Every 2016
  spec has **zero seeded arrivals** and `arrival_group: None`, so the lever has
  nothing to act on. **If any 2016 city-year moves by one seat, the lever is
  reaching something it must not, and the run is void** — stop and find out why
  before reading 2021.
* Spreading mass across many named arrivals instead of one lump should **raise**
  the ranks 13+ over-forecast and phantom mass. Watch it; §1.54 measured the
  remedy on the receiving side at 14–22 coherent seats.

### 5. What must NOT count as a pass

* **The relabelled score improving on its own.** That is the rigged instrument.
* **A gain that vanishes when the top two arrival columns are removed.**
* **Key 4 saying anything.** It cannot fire — the arrival path touches neither
  `sd_for` nor `theta_prior`, and four of the five biggest misses have no θ row
  at all. **A key that cannot fire is not a key that passed**, and both halves
  must be stated when this is written up.

### 6. The constraint to state in the write-up, whatever the result

**This is a ONE-CYCLE validation on ~1 effective cluster** — ⛔ **but "it cannot
be widened / checked exhaustively" is WITHDRAWN (§1.136 §9).** 2016's zero seeds
are not a fact about 2016: `pools.metro_file` **cannot resolve the 2000 and 2006
metro results, which are on disk and reconciled at 100%** (`DATA-QUALITY.md` item
14). So `entrant_record(lge_transitions(before='2016'))` is `[]`, `arrival_rules`
takes its `if not record` exit, and no seeds exist. The record is **not** the
constraint — `arrival_group_record('2016')` returns **6 rows**. It is wiring, and
it is `POOLS-REEMIT-QUEUE` entry 4. The table below is kept as written:

| target | seeded arrivals | prior record to fit `M` | retry possible |
|---|---|---|---|
| 2011 | yes | **0 rows** | no — nothing to fit |
| 2016 | **0** | 6 rows | no — nothing to draw |
| **2021** | **32 at Johannesburg, 165 across the panel** | 14 rows | **yes, all 8 metros** |

Eight metros inside one cycle share a national swing, so rule 11 applies at its
strongest. **Do not report 8 city-years as 8 independent facts.**

### 7. If it passes

It still does not ship on this evidence alone. Write it up with the one-cycle
caveat, the label-free/relabelled pair, and the leverage check, and put it to the
owner. The live 2026 forecast additionally needs the roster seam
(`POOLS-REEMIT-QUEUE` entry 3) before the mechanism can be constructed at all.

---

## ⛔ THE NEXT ORDER OF BUSINESS

The pollster's original list is done. This is the list after **two rounds of
review of that work** (§1.126), which found real errors in it — including one I
made while fixing the identical class of error one file over.

| # | do | why |
|---|---|---|
| ~~1~~ ✅ | ⛔ **DONE 2026-08-29 — RAN, AND THE LEVER FAILED** (§1.136 §7). Its justification below is also stale: it said "the fair referee is now wired in", and the referee had never produced a number. **Replaced by: build a lever scoped to the generic slot alone** (§1.136 §8). ~~RE-RUN THE ARRIVAL RETRY AT 2021, FAIRLY (§1.135)~~ — `arrival_group_draw=True` + `compare_history` | the mechanism exists, its rejection was scored by an instrument that hands the incumbent the answer key, and the fair referee is now wired in. **No nomination list, no `pools.py` change, no re-emit needed** — the 2021 spec already carries a real `arrival_group` |
| **1b** | The **PA-type failure is NOT the arrival channel** (§1.135) | a 0.03% national base growing ~40× locally is the θ/seeding path. Two of the biggest misses, two different mechanisms — the retry touches one of them |
| **2** | **Build the instrument for THE VACANCY** — see `ITERATING.md`, "THE VACANCY" | ⛔ **decided 2026-08-29: Key 4 is KEPT as a θ-width floor, its old justification is dead, and nothing in the bar now guards against a change that improves the many by degrading the few** |
| 3 | **State C's PIT and A²** — one `--dump-arm` away | turns reading 2's refutation from one member of the exclusion class into two |
| 4 | The **pooled 403-row ν bound with δ free** | the only version of the `LEVEL_DF` measurement that returns anything: simulated interval ≈ [4.7, 15], rules out ν=4 with ~81% probability |
| 4 | Add a **bias floor `τ²`** before enabling `bye_weight_mode="inverse_variance"` | the lever stays off until then |
| 5 | Measure the **`v_spine` change under that lever** before enabling it | it is a no-op on the θ branch and an unmeasured change on the `PLAN_BOUNDS` fallback (§1.126) |
| 6 | Investigate: the by-election weighting is **worse than uniform** | 24.83 vs 24.66 LOO RMSE, number in hand, nobody acted |
| 7 | Per-party turnout sensitivity, **hierarchical**, behind a lever | real sign, unvalidatable magnitude |
| 8 | Fold policy → a `JUDGEMENT-CALLS.md` row | 2006/2011 computed, not gated; the reasons are in `ITERATING.md` but unregistered |

---

### ⛔ Item 1 changed on 2026-08-29, and the old item 1 was wrong

I told the owner the θ prior's overconfidence was the top priority. **Two rounds
of review took it off the top, and took my replacement off too.**

Split the committed artefact by cycle and the bands do not survive it. Ranks
4-12 `sd(z)` is **0.485 at 2016** and **2.262 at 2021**; the signed vote error is
**−0.04pp** against **−26.07pp**. Split again on whether the party has a record
in that metro: 2021 established parties read **0.583**, new parties **3.193**,
and 2021 ranks 1-3 established read **0.446**.

> **On every column where the model has a local record — either cycle, either
> band — the forecast is too WIDE by 1.7× to 2.7×. The whole "too narrow"
> reading is parties the model had not seen.**

⚠️ **But "had not seen" has two meanings and they are different failure modes**
(§1.135). `entrant_actual_for` calls a party an arrival when it is absent from
the preceding NPE baseline. ActionSA and the CCC are — the group arrival
mechanism addresses them. **The PA is not: it held 0.0295% nationally at
Johannesburg in 2019 and grew roughly fortyfold locally**, which is the
θ/seeding path. The two biggest seat-side misses need two different repairs.

Eleven of the twelve worst 2021 misses are parties with no 2016 column in that
metro. And **four of the five biggest have no θ row at all** — no NPE2019 vote
in their metro — so they are structurally invisible to the instrument §1.127
used. ActionSA at Johannesburg, PIT exactly 1.0, *cannot* be a θ defect.

The pooled `sd(z)` of 1.796 also has a cluster CI of **[0.810, 2.501]**, which
contains 1.0: it is not distinguishable from correct dispersion on this panel.

**So item 1 is arrival SIZE** — §1.58 said it in one line and it was never made
the priority: *"That is an error of SIZE, and it is a different repair from an
error of possibility."* It is the one channel with dated new evidence arriving:
**nomination lists, 16 September.** Carry both caveats: it can only be validated
on 2021 (2016 has almost no new parties of consequence), so it is a one-cycle
validation and rule 11 applies; and "three successive fragmenting cycles" is an
argument, not a measurement.

### ⛔ Key 4: kept, repurposed, and the hole it leaves is now named

**Owner decision, 2026-08-29:** *"4 was still useful, but has a new role. Keep it
but change its raison d'être. We will have to find something novel to take its
place which we do not yet have."*

So `ITERATING.md` now says three things where it said one. **Key 4 IS** a floor
on the θ width estimator — 235 observations, 16 metro-year clusters, against
Keys 1 and 2's ~2 — and untradeable because a layer that has stopped estimating
its own dispersion honestly cannot be repaired by a better score elsewhere.
**Key 4 IS NOT** a guard against an exclusion moving volatility out of the prior
and into the error; §1.125 measured that it passes Type A at every `LEVEL_DF`
from 3 to 1000. **And THE VACANCY** is written into the bar as a known hole:
nothing now blocks a change that improves the many by degrading the few, and
until something does, **no exclusion or record restriction may be adopted on an
aggregate score alone.**

The live evidence that this is not hypothetical: under Type A the θ prior's PIT
variance falls and coverage rises at both folds while `mean z²` at 2016 worsens
6.230 → 7.400 and the *trimmed* figure improves to 3.642. Ninety-odd ordinary
parties forecast better by forecasting three collapses worse — and every
aggregate score in the bar reads that as an improvement, because on average it
is one.

### The re-measurement that got us here

§1.125. On the corrected instrument **Type A's 2016 fold no longer worsens** —
4/8 metro-years better, 4/8 worse, 95% interval [−0.305, +0.269] — and 2021
improves beyond the noise. `ITERATING.md` says Key 4 exists *because* the bar
would otherwise have shipped Type A. **It would ship it now.**

Type A is still refuted on §1.74's seat condition, and §1.82's refutation of
recency weighting survives and is now banded (`THETA_WINDOW=2` is the first arm
ever to fail the floor on a banded test). But the key's justification is
undercut, **and nothing in `ITERATING.md` has been changed on the strength of
it — the bar is the owner's.** §1.125 recommends keeping Key 4 as the layer
floor it honestly is and adding PIT, which can see a too-narrow width where a t₇
log score structurally cannot.

Note also: the pollster predicted the opposite direction and was wrong. The
distribution change dominates the baseline change.

### Why that re-measurement was the head of the list

**Every held-out NLL figure quoted in this repository before 2026-08-28 is form
A's, Gaussian, without its constant, on the raw baseline.** They are marked in
place. The one that matters most is §1.82's `THETA_WINDOW` table, which closed
off recency weighting on the **shape** of a four-point curve whose two closest
points are 0.03 nats apart — and shape is far more fragile to an instrument
change than a sign is. No wrong change shipped (Type A and state C were both
*rejected*), but `PLAN-TO-LIVE.md`'s B1 gate and F22+F23 are live decisions that
would otherwise be judged against a baseline nobody has measured.

## 3–4. `bye_weight_mode` is shipped and must stay OFF

`"fixed"` (default) or `"inverse_variance"`. Derived weights at joburg 2026:
EFF 0.722, ANC 0.704, DA 0.528, ASA 0.413, **MK 0.216**, PA 0.204, IFP 0.132,
AIC 0.089, ATM 0.031. Total 2.005pp of centre.

**The construction is correct and one term is missing.** ANC and EFF get
`w > 0.70` — the by-elections outweigh the spine for the two largest parties —
and their dominant error is **bias, not variance**: measured turnout
correlations of **+0.720** and **+0.842**. Inverse-variance cannot see a bias it
was not given, and fifteen contests sharing one selection mechanism are not
fifteen independent draws.

**Fix:** `v_bye = sd²/n + τ²`, with `τ²` estimated from the residual spread
*after* removing the turnout relationship, per party. A measurement, not a typed
constant. It pulls ANC/EFF back and leaves MK's 0.216 alone.

**`v_spine` now uses both tails** — `ln(high/low)/(2×1.2816)` — which was item 5
and is done.

---

## Tier 2 is pre-registered and NOT run

All three are read-only specifications with pass conditions written before any
measurement, per `ITERATING.md`.

* **F28+F29** — ready, ~20 min. Predicts Key 1 `undetermined` **structurally**:
  four of eight 2016 city-years have a fallback delta of *exactly* zero, so that
  cycle can never supply the ≥5/8 the pass condition needs. **The clip never
  binds anywhere** — only the restriction does work. ENTRANT is the only channel
  that can move a seat. Its failure condition 4 is the strongest tripwire in the
  set: the four zero-delta 2016 city-years must come back byte-identical.
* **F22+F23** — blocked on item 1. Separately established: **`SD_CEILING`'s
  entire caseload is phantom parties** — 40 at the ceiling, every one a phantom,
  never binding on a party that reaches the draw.
* **F3+F8 + `level_floor`** — recommends **not spending** the `level_floor` runs:
  the lever moves 0.0002–0.0034pp across the whole ballot and **zero seat-mean**;
  one seat is 150× larger. What *is* real is convergence — at 1e-7 the solver
  converges and rounds/call falls **40.0 → 16.7**. That is a
  correctness-and-cost change and must not be dressed as accuracy. F3+F8 carries
  a **pre-registered expectation of failure** (EFF's level error worsens at 6 of
  8 metros in both cycles), and recommends splitting the coupling the other way:
  **F3 alone is free** and F8 then becomes a clean scored change.

---

## The rules this session established

**The review rule, now in `CLAUDE.md`:** split across agents → **check them** →
**the pollster reviews anything touching the forecast's substance**. I broke it
in the session that wrote it — reported a change as done and only ran the
pollster when asked. Run it *before* reporting, not after.

**Measurement discipline:** `freeze --verify` as the neutrality check instead of
a second suite run; targeted `-k` per change and the **full suite once per
commit**; a partial run prints a banner that it is not a suite run.

**The suite is 1455s → 557s.** ⚠️ **Both figures are stale: measured 2026-08-29 at 1194.5s wall clock** (2045.9s of module time, 1.71x from parallelism), with `test_levers_are_live` still the long pole at 809.6s / 39.6%. `CLAUDE.md` says "~14 minutes" and this line says 557s; neither matches. Quote the measurement, and re-measure rather than re-typing. Note the negative result: isolating the long pole
made it *slower* (586 → 679) because idleness cost more than oversubscription.
`LONGEST_FIRST` scheduling gets both.

**`POOLS-REEMIT-QUEUE.md` holds FOUR entries** (it said two; it held three even then, and §1.136 added a fourth), and the second —
`_target_roll`'s crosswalk path — **blocks all multi-city 2026 work**: no second
city can emit a 2026 spec until it lands.

---

## Corrections made to this log's own earlier claims

* **§1.109's F10 boundary was a decade out.** `solve_identity_hits` is 0 at
  1e-8 and 2990 at 1e-9; 1e-8 is the lowest safe point.
* **§1.117's "second truthiness site" did not exist** — deleted 2026-08-17,
  surviving only as a tombstone comment.
* **§1.109 claimed to be an index and was a summary.** The 48-row table is there
  now, with provenance: five rows spot-checked, F15/F19 verified in full, **the
  rest recovered and not re-verified** — treat those as pointers to look, not as
  findings.
