# Handover — 2026-08-28

**Read this, then `ITERATING.md`'s Key 4, then `POOLS-REEMIT-QUEUE.md`.**
Everything is committed; the tree is clean. Branch
`splinter-rule-and-historical-tail`, **suite 370 passed / 0 failed / 10
skipped**, freeze re-taken and verifying.

**19 days to nomination lists (16 September), 68 to polling (4 November).**

---

## ⛔ THE NEXT ORDER OF BUSINESS

**Items 1, 2, 3 and 5 of the pollster's list are DONE (MODEL-LOG §1.124).** What
is left, re-ranked after the review of that work:

| # | do | why |
|---|---|---|
| **1** | **Re-measure Type A, state C and the four `THETA_WINDOW` arms on the corrected instrument** | ⛔ **before F22+F23.** ~30 min of compute. See below |
| 2 | **PIT as a second instrument** — `u = F_t7(z)` per fold and size bin | a log score charges level bias to the width and cannot say which moved |
| 3 | Add a **bias floor `τ²`** before enabling `bye_weight_mode="inverse_variance"` | the lever stays off until then |
| 4 | Investigate: the by-election weighting is **worse than uniform** | 24.83 vs 24.66, number in hand, nobody acted |
| 5 | Per-party turnout sensitivity, **hierarchical**, behind a lever | real sign, unvalidatable magnitude |
| 6 | Write the **fold policy** argument into `JUDGEMENT-CALLS.md` | 2006/2011 are computed and not gated; the reason is in `ITERATING.md` but unregistered |

---

## 1. Key 4's instrument was wrong three ways, and is now fixed

`ITERATING.md`'s Key 4 is **untradeable**. It said *"Held-out NLL on
`theta_residual`'s folds must not worsen in either fold."* Wrong on all three
counts of what that pointed at:

1. **`form_a` is not the committed estimator.** It is rebuilt from `_fit_line`
   and reaches `levels` only through the clamp — **so a change to `sd_for` moves
   the model and leaves the gate where it was.** That mechanism is dispositive
   on its own; an earlier draft led on a 0.0164 nats counterexample that is
   inside the clustering noise, and that over-read is itself recorded.
2. **The harness passed a baseline `run_model` does not pass** — the raw
   citywide tally, where the model drops off-ballot parties first. 286 parties
   across 32 metro-years; largest single width moved 0.605.
3. **The score was a Gaussian; the model draws Student-t₇.** At `w = SD_FLOOR`
   and `|r| = 2` the Gaussian charges 87.9 nats against the t₇'s 13.3.

**Baselines are now 2016 = 1.1363 and 2021 = 1.1425** — within 0.006 nats of each
other, where the Gaussian made them look 2.3× apart. The spread was the
instrument. Fold 2011's notorious 5.59 was the Gaussian tail penalty on three
known party-structural events (COPE, the NFP split, the DA/ID merger, all
already measured in §1.71); as an effective width it was **452**, which is not a
forecast.

Key 4 also had **no noise band** on an untradeable floor. `theta_residual.
key4_delta` is now the pass rule as code: paired on identity, **refusing** if the
population moved, t(G−1) on the eight metro-year cluster means, sign count
reported. **Fails only if the 95% interval lies entirely above zero.**

**⛔ It is a LAYER floor, not the model's predictive score** — it scores the θ
width about `theta_prior`'s own centre, and the model draws about the spine's.
Do not quote it as the model's estimation loss; the first draft of §1.124 did.

### Why item 1 is the head of the list

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
