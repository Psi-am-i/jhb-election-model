# Handover — 2026-08-28

**Read this, then `ITERATING.md`'s Key 4, then `POOLS-REEMIT-QUEUE.md`.**
Everything is committed; the tree is clean. Branch
`splinter-rule-and-historical-tail`, **suite 370 passed / 0 failed / 10
skipped**, freeze re-taken and verifying.

**19 days to nomination lists (16 September), 68 to polling (4 November).**

---

## ⛔ THE NEXT ORDER OF BUSINESS: the pollster's ranked list

Not the finding list. **The instrument.**

| # | do | why |
|---|---|---|
| **1** | **Fix Key 4's instrument** | ⛔ **before F22+F23** — see below |
| 2 | Restate Key 4 as a **quantity**, not a file path | nearly free |
| 3 | Record that the true committed held-out loss is **~2× the logged figure** | a correction to the record |
| 4 | Add a **bias floor `τ²`** before enabling `inverse_variance` | the lever stays off until then |
| 5 | `v_spine` should use `ln(high/low)/(2×1.2816)` | two minutes, uses both tails |
| 6 | Investigate: the by-election weighting is **worse than uniform** | number in hand, nobody acted |
| 7 | Per-party turnout sensitivity, **hierarchical**, behind a lever | real sign, unvalidatable magnitude |

---

## 1–3. Key 4 measures a stand-in, and it is untradeable

`ITERATING.md` says: *"Held-out NLL on `theta_residual`'s folds must not worsen
in either fold."* It is **untradeable**, and exists specifically because without
it the bar would have shipped the Type A filter.

**`theta_residual.form_a`'s own docstring says it is not the committed
estimator** — it uses *"the record's own weighted size instead"* of the party's
size at the target, and says *"This is for RANKING TWO FORMS, NOT FOR QUOTING A
WIDTH."*

| fold | true committed | `theta_residual` prints |
|---|---|---|
| 2016 | **1.3241** | 0.7531 |
| 2021 | **0.5791** | 0.2280 |

**And they rank candidates differently**: a variant improves on the printed
column and worsens on the true estimator at 2021 (0.5791 → 0.5955) — a pass on
one, a fail of an untradeable floor on the other. So the usual defence, *"a
relative comparison survives a biased instrument"*, is **false here** and the
counterexample is already in hand.

**F22+F23 is a change to the size-dispersion fit — exactly what the stand-in
mis-evaluates.** Running it against today's Key 4 gives a number uninterpretable
in either direction. **The hard part is done**: the true estimator has been
rebuilt per (target, metro) and verified to reproduce `theta_prior`'s widths
exactly. What remains is moving it into `theta_residual.py` as a labelled column
and re-baselining both folds.

**Restate Key 4 as:** *held-out NLL of the committed width estimator — `sd_for`
evaluated at the party's size at the target, as `theta_prior` computes it — on
forward-validated residuals, by fold; folds 2016 and 2021.* Then
`theta_residual.py` is one implementation of it rather than being it.

## 4–5. `bye_weight_mode` is shipped and must stay OFF

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
