# Handover — 2026-08-29

**START AT "THE NEXT RUN" BELOW.** It is pre-registered and ready to execute;
everything after it is the reasoning that produced it.

Branch `splinter-rule-and-historical-tail`. **18 days to nomination lists
(16 September), 67 to polling (4 November).**

**⛔ The state to verify before trusting anything here:** run
`git status --short` (expect clean), `tests/run_all.py` (expect 0 failed) and
`freeze.py --verify` (expect VERIFIED). The last full suite was **377 passed / 0
failed / 10 skipped** with `freeze --verify` VERIFIED, on the tree this handover
describes. All 18 pool specs carry `pools_sha` `dbdf171344ffd5f0`, matching the
live code — **no re-emit is needed.** Re-run the preflight anyway; it is three
commands and it is what the plan's first step exists for.

---

## ▶ THE NEXT RUN — pre-registered, ready to execute

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

### 4. Predicted signs — recorded before the run

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

**This is a ONE-CYCLE validation on ~1 effective cluster, and it cannot be
widened.** Checked exhaustively:

| target | seeded arrivals | prior record to fit `M` | retry possible |
|---|---|---|---|
| 2011 | yes | **0 rows** | no — nothing to fit |
| 2016 | **0** | 6 rows | no — nothing to draw |
| **2021** | 32 | 14 rows | **yes, all 8 metros** |

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
| **1** | ⛔ **RE-RUN THE ARRIVAL RETRY AT 2021, FAIRLY** (§1.135) — `arrival_group_draw=True` + `compare_history` | the mechanism exists, its rejection was scored by an instrument that hands the incumbent the answer key, and the fair referee is now wired in. **No nomination list, no `pools.py` change, no re-emit needed** — the 2021 spec already carries a real `arrival_group` |
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

**The suite is 1455s → 557s.** Note the negative result: isolating the long pole
made it *slower* (586 → 679) because idleness cost more than oversubscription.
`LONGEST_FIRST` scheduling gets both.

**`POOLS-REEMIT-QUEUE.md` holds two entries**, and the second —
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
