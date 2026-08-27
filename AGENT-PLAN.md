# Where an agent fleet pays, and where it does not — 2026-08-27

**Written after two workflows that worked** (Phase A: 14 agents, 111 tests, ~35
findings; triage: 7 agents, 44 findings verified by a second reader) **and one
stretch of serial surgery that went badly** (four coupled invariants broken in a
row inside `pools.py`). The difference between those two experiences is the
whole content of this document.

## The constraint that shapes everything: CPU, not agents

This machine has **8 cores**, and one `compare_history` at 1500 draws saturates
them — **169s parallel against 499s serial** (§1.46). Backtests therefore **do
not run concurrently**. Measurement throughput is roughly **20 runs/hour** no
matter how many agents exist.

| kind of work | scales with agents? | limit |
|---|---|---|
| reading, reasoning, test-writing, verification, design | **yes** | agents |
| anything requiring a backtest | **no** | one queue, ~20/hour |

**So the shape is: use agents to BUILD a measurement queue, then drain it
serially.** Preparing thirty pre-registered sweeps in parallel is cheap;
running them is four hours of wall clock whatever you do.

`pools.artefact_lock` (§1.102) now makes the failure mode loud rather than
silent — a second writer, or a reader during a write, fails immediately naming
the holder. That is what makes fleet work safe at all; before it, two racing
jobs left eighteen specs carrying two different `pools_sha` values.

---

## Workstream 1 — B2, the nineteen never-swept constants ★ start here

`PLAN-TO-LIVE.md` has said *"DO THIS FIRST in Track B"* since 23 August and it is
untouched.

**Cost:** 3–5 points each ≈ **60–95 backtests ≈ 4 hours of compute**. Feasible in
a day of background running.

**The agent half is the valuable half.** This repository requires
**pre-registration** — stating what would count as success *before* measuring —
and that discipline has already killed three ideas that looked good
(`sd_for` refit §1.x, the Type A filter, recency §1.82). So:

* **~10 agents**, one per constant or coupling cluster. Each produces: the values
  to sweep and why, the mechanism the constant is supposed to act through, and a
  **pass condition written against `ITERATING.md`'s four keys**.
* **One serial runner** drains the queue under the artefact lock.
* **A finding that a lever is INERT is a result**, not a failure — §1.84 found a
  live lever half-connected, and §1.94 found the poll channel worth −6 rather
  than +48. Several of the nineteen will be doing nothing.

**Why first:** highest confidence, best understood, no surgery, and it runs in the
background while other work proceeds.

## Workstream 2 — the 34 neutral findings ★ parallel with 1, no CPU contention

The triage (§1.98) classified 44 findings: 34 **neutral** — provably unable to
move a number on the shipped configuration — with 22 coupling groups already
identified.

* **~12 agents**, one per coupling group, `isolation: "worktree"` so concurrent
  edits to `montecarlo.py` and `levels.py` cannot collide, serial merge after.
* Each lands with a **mutation-verified test**. That discipline caught 55 of 63
  mutations in Phase A and is the reason those tests are worth having.
* **No backtest needed by definition** — neutral means neutral. But the claim is
  checked: anything that moves a number was mis-triaged and comes back.

**The known coupling that decides order:** F1+F2+F7 — fixing the
`spine_k or SPINE_K` idiom alone makes `k = 0` deliverable and `levels.py:882`
then evaluates `0.0/0.0` for ten parties at 2026. One repair, not two.

## Workstream 3 — the bottom-up model ★ highest upside, least specified

The owner's proposal: project ward/VD results forward **independently**, sum to a
citywide total, and compare against the top-down model. Where they disagree is
diagnostic, and the disagreement is measurable on all sixteen city-years.

**The trap, which the design must clear:** a naive bottom-up — summing historical
VD shares weighted by registration — reproduces last election's citywide result
**by construction**, because `base_city` is defined as that sum. It would be
comparing the model to its own input. The value appears only if each unit is
projected forward by its *own* evidence.

**Shape: a judge panel.** 4–5 agents produce independent designs, adversarial
scoring against the trap above, synthesise the winner, then build serially. The
design phase is where the value is; the code is straightforward once the design
is right.

## Workstream 4 — pool-vs-`dev`, using the right conditional

Established §1.98/§1.102: the model fits `PartyFit.rates` — *"appeal rate within
each pool"*, with Duncan-Davis bounds — then **stores the transpose** and never
persists the rates. The one place pools allocate geography (`montecarlo.py:2499`,
seeded parties only) uses the transpose, over-weighting every pool by its own
citywide size — a **13× relative discount** of the smallest pool against the
largest.

Test whether **corrected** pool allocation beats `dev` (fixed historical
geography) for parties that have both. 16 city-years, parallel prep, serial
measure. **Must use the rates, not the stored composition** — testing the
transpose would measure the wrong thing and a negative result would mean nothing.

---

## Where a fleet does NOT pay, and I would argue against it

**Phase C — extracting the ~14 inline stages.** Deep surgery on `montecarlo.py`.
On 2026-08-27 four coupled invariants were broken in a row doing exactly this
kind of work in `pools.py`, each fix exposing the next (§1.101). Agents would
multiply that, not contain it. Serial, careful, or not at all.

**Phase B — the bus.** Honest assessment: **Phase A already delivered most of
what the architecture argument promised.** The defects are found and written
down. The bus prevents *future* silent-neutral bugs — real, but insurance rather
than prediction, with 69 days to polling.

**Anything deciding what ships.** The owner's, and the four keys'.

---

## The calendar, which has not been mentioned in a while

**20 days to nomination lists (16 September). 69 days to polling (4 November).**
Both fixed by the IEC.

A1 (freeze and hash) is **done**. **A2 and A4 are not**: nothing in `content/` or
`site/` mentions poll credence, and `content/joburg/stats.toml` still carries
sources reading `run:turnout_tilt_da=1` — **a lever deleted from `run_model`**.
That is presentation work, which `CLAUDE.md` keeps out of the model backlog on
purpose, but the dates are real and it is the first thing a hostile reader sees.

## Recommended order

1. **B2 pre-registration** (agents) → queue → drain in background
2. **The 34 neutral fixes** (agents, worktrees) — runs alongside, no CPU contention
3. **Bottom-up design panel** (agents) once 1 and 2 are moving
4. **Pool-vs-`dev`** when the measurement queue has room

Everything above assumes the artefact lock holds. If a run ever reports mixed
`pools_sha`, stop and re-emit before believing any number.
