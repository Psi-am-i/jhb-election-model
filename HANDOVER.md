# Handover — 2026-08-27

**Read this, then `AGENT-PLAN.md`, then `NULL-RESULTS.md`.** Everything below is
committed; the working tree is clean apart from `new data from statsSA/`, which
holds two `.inetloc` email shortcuts and no data.

**Branch `splinter-rule-and-historical-tail`. Suite 360 passed, 0 failed,
10 skipped.** 20 days to nomination lists (16 September), 69 to polling
(4 November).

---

## ⛔ THE ONE THING TO CHECK BEFORE MEASURING ANYTHING

**`data/processed/history.json` IS STALE RELATIVE TO THE TREE.** It is the
scoreboard committed at `2742785` on 24 August. Nine commits and a day of work
sit between it and HEAD, and the current tree has **never been measured**.

Today that exact staleness caused a wrong retraction: a +4 coherent-seat
difference was attributed to this session's changes when it predated them
entirely (§1.103). **A number carried in a file is not a measurement of the tree
in front of you.** Before any paired comparison, run the baseline on the current
tree.

---

## What was done today, in four commits

| commit | what |
|---|---|
| `7de0cd8` | Phase A: 111 value tests over 7 seams, mutation-verified. The 187% registration rate found, repaired, measured, and **reverted**. `pools.artefact_lock`. |
| `9348aa5` | F12 isolated: neutral. A retraction of a retraction. Goldens re-recorded on evidence. |
| `2636730` | `NULL-RESULTS.md` and the delivery-proof instrument. Ward-winner key. Absorption accounting. |
| `76ce46a` | The counters' first act: refuting the change that shipped them. |

## Where we are in the plan

`AGENT-PLAN.md` — its **SPINE** section is the frame: a declaration is a claim,
a read log is the evidence, and this is `ARCHITECTURE.md`'s C layer.

| workstream | state |
|---|---|
| Phase A — declare and test the seams | ✅ **done**, mutation-verified |
| Null-results instrument | 🟡 **built, ~1/3 covered** |
| B2 — sweep the constants | ⛔ **blocked, correctly** — see below |
| 34 neutral findings from the triage | ⬜ not started |
| Bottom-up model (owner's proposal) | ⬜ not started |
| Pool-vs-`dev` experiment | ⬜ not started — **now has a metric that can see it** |
| Phase B — the bus | ⬜ not started; **reversed to worth doing**, see SPINE |
| Phase C — extract 14 stages | ⬜ deliberately not started; deep surgery, high risk |
| Track A publishing (A2, A4) | ⛔ **untouched, and the calendar is real** |

**B2 is blocked on purpose.** Its pre-registration found **48 constants, 42 with
a blocker**, the largest class being undeliverable — a module constant set in the
parent does not cross the `ProcessPoolExecutor` boundary, so a sweep fans out to
eight workers reading the default and reports a **flat, confident null**. Running
B2 before the delivery proof covers those constants would produce a page of
authoritative nothing. That is the whole reason the last two commits exist.

---

## Open work, in the order I would take it

**1. Extend delivery-proof coverage.** 32 of ~90 module constants on the model
path are declared; 205 exist across `src/`. Entirely uncovered: `pools.py`'s 15
including **the whole `ALPHA_*` family** — the one `NULL-RESULTS.md` names as
feeding 83–98% of drawn variance — plus `fold.py`'s *second* `SHARE_FLOOR` and
its own `LEVEL_FLOOR`, `benchmarks`, `turnout`, `parties`, `cityconfig`.
Parallelises well: one agent per module, disjoint files.

**2. `PYTHONHASHSEED`.** One line in the runners. §1.104: two runs of unmodified
HEAD disagree without it, at ~5e-16. Not urgent for accuracy, but
`forecast_frozen.json` is published and the honest guarantee is *"identical to
the last bit under a fixed hash seed"*.

**3. F12 is genuinely unfixed, and I now know why my fix could not work.**
Measured on Johannesburg 2021: `solve_rounds / solve_calls == exactly 40.0` — the
early stop **never fires**. The reachable-only gap is **1.37e-5, thirteen times
`tol`**, because the mass the 27 sub-floor parties are stuck holding is *stolen
from every other party through the row renormalisation*. **The target is the
theft, not the convergence test.** This is a real, measured, per-draw deviation
from the drawn target that `montecarlo.py:1746` claims does not happen.

**4. The 34 neutral findings** (§1.98). Worktree-isolated, one agent per coupling
group. Note **F1+F2+F7 are one repair**: fixing the `spine_k or SPINE_K` idiom
alone makes `k=0` deliverable and `levels.py:882` then raises `ZeroDivisionError`
for ten parties at 2026.

**5. Pool-vs-`dev`** — the owner asked for this and it has never run. It must use
`PartyFit.rates` (the appeal rate, with Duncan-Davis bounds), **not** the stored
`members` transpose, and it must be scored on the **ward-winner key**, because
seat error structurally cannot see geography.

**6. Track A publishing.** `content/joburg/stats.toml` still carries sources
reading `run:turnout_tilt_da=1` — **a lever deleted from `run_model`**. First
thing a hostile reader sees.

---

## Rules this session paid for

**A constructed fixture proves a MECHANISM, never a MAGNITUDE.** Three claims
were asserted from toys and failed on the panel: F12 "bit-identical", the 1e-6
"float noise" (wrong by ten orders — the floor is **1e-16**, measured), and "3
rounds instead of 40" (never fires). Toys answer *does this path exist*; only the
panel answers *how much*.

**Never `git checkout` a whole file to revert part of it.** Reverting the
cap-and-blend took F14 — the ward-roll fix the owner had explicitly kept — with
it. A test caught it. Commit smaller and sooner.

**Queue, do not overlap.** Two background jobs raced on `pools_*.json` twice in
thirty minutes, leaving 18 specs with two different `pools_sha`. `artefact_lock`
now makes it fail loudly, but the discipline is still *one job at a time*. If a
run ever reports mixed `pools_sha`, stop and re-emit before believing anything.

**"No change" is four answers.** `UNDELIVERED` / `ABSORBED` / `CANCELLED` /
`INERT`, and only the last is a result.

**Geography reaches the seat score only through overhang**, which fires in
**8.1% of draws** through **ANC and IFP alone**. Do not judge a geography change
by `seat_abs_err_coherent`.

---

## Stats SA — live, and they are helping

Escalated by **Tracy Taylor** (Director, Stakeholder Relations) to three experts.

* **Vishanth Singh (Geography) — answered.** **No Census 2022 SAL exists.** Not
  withheld; never created. `SOURCES.md` corrected — it had said "supplied on
  request only", which was wrong. Ceiling now known: full variable set incl.
  **language only at local municipality**; pop group/age/sex at ward; nothing
  else below municipality. Offers geometry-only layers: 2011 SAL/EA/main/sub
  place, 2022 EA/main/sub place.
* **Thanyani Maremba (Electronic Product Development) — awaited.** The one who
  can say whether a **2022 electoral-ward geography exists in SuperWEB2**.
* **Angela Ngyende (Census Content and Outputs) — awaited.** For the
  sign-language coding change (9,309 in 2022 against ~235,000 in 2011) and the
  missing "Other" residual.

**The surviving route to ward-level language** is the rake: Census 2011 language
by ward (SuperWEB2, Community Profiles → 2011 → Descriptive → *South Africa by
Electoral Ward*) raked to the 2022 municipal totals in
`data/raw/covariates/Languages by Municipalities Census 2022.xls`. `pools.py`
already has the IPF machinery (`balance_margins`).

**Why it matters more than it looks:** `pools.py:372` carries a banner — *"THIS
IS A PROXY. IT IS MEANT TO BE REPLACED"* — because population group is the only
ward-level characteristic Stats SA publishes, and it cannot separate the ANC from
the IFP. `DATA-QUALITY.md` item 13 is the sharpest form of the same problem: **the
DA requires 103.3% of Johannesburg's entire white pool**, using only published
votes and published population.
