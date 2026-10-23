# Before the freeze: by-elections off, and γ from the other fold

Written before any run, on 2026-10-23. Owner, answering OWNER-DECISIONS item 31
("Before the freeze: test two inputs the backtest never checks?"): "test the two
inputs." The owner then chooses what is frozen by 31 October.

**Already known before this was written:**
- MODEL-LOG §1.323: when `w_bye` went from 0 to ½ (17 October tree), Johannesburg
  2026 P(ANC largest alone) went 57.0% → 47.4% and DA 35.4% → 44.3%; mean seats
  ANC 72.1 → 69.7, DA 69.7 → 70.0.
- MODEL-LOG §1.325–§1.326: the 2016–2021 by-elections against 2021 supported ½
  (left-out range 0.4–0.6), on scores now withdrawn as in-sample (2026-10-23).
- The live forecast's turnout file carries a by-election tilt in 79 of 825 VDs,
  ×0.907 to ×1.137.
- γ for 2026 reads fold 1; fold 2 (2019 → 2021) is on disk; no pooled fit exists.

No published figure, freeze or golden is the standard here (CLAUDE.md §1). The
comparison is between arms on the same tree, seed and draws, to show the owner
how much each input moves the forecast. No arm is scored against a result,
because 2026 has none.

## Arms (Johannesburg 2026, seed 20261104, 5,000 draws)

| arm | change from baseline |
|---|---|
| **B** baseline | the current tree as it is |
| **A7** by-elections off | `w_bye = 0` (each party's centre stays at the spine level), and `turnout.csv` rebuilt by `turnout.py --kappa-bye 0` (no turnout tilt). The ward-level by-election term is already 0 in the baseline. The `processed` directory is a full copy of `data/processed/` with that turnout file and with the `byelection_*` files removed |
| **G2** γ fold 2 | γ from the 2019 → 2021 fit (`fold2_parameters.csv`) |
| **GP** γ pooled | γ from folds 1 and 2 fitted together: per party and ballot, γ = (Σwxy over both folds' VD rows) ÷ (Σwx² over both), the same through-origin weighted fit as `fold.fit_gamma`, not the mean of the two γs |

**Fallback rule, all γ arms.** A party with no real fit in the arm's fold(s)
keeps the γ the baseline gives it. "No real fit" is the `fold.py` branch that
writes γ = 1.0 because the party's base citywide share is ≤ 0.001, or because
the fold never saw it (`fold.py:592-604`); the writer recomputes the base share
to confirm each case. In the pooled arm, a party fitted in only one fold takes
that fold's sums. The runs record the list of parties the rule touches, and the
γ each party was drawn with.

Nothing is re-emitted: the pool specs, `bye_value.json` and the width record do
not read by-elections or the 2026 γ.

## Blocking conditions (each checked before any result is read)

- **C1 pairing:** `arms.check_pairing` passes for each arm against B (seed,
  draws, tree, specs, width key).
- **C2 the switch took:**
  - A7: every party's by-election weight is 0 and its level is the spine level;
    the 79 tilted VDs read ×1.000 in the turnout the run used.
  - G2, GP: the per-party γ actually drawn equals the arm's fit, for every party
    outside the fallback list.
- **C3 vintage:**
  - `turnout.py --kappa-bye 0.25` rebuilt into scratch equals the live
    `turnout.csv`.
  - The writer's fold code, refitting fold 1 alone, equals `fold1_parameters.csv`.
  - If either differs, the arm affected reads scratch-built files in both its
    baseline and its own run, and the report says the baseline differs from the
    site.
- **C4 the baseline is the site:** B's headline figures equal those on the live
  site (largest-party chances, seat medians per party). This is not a standard
  of correctness; it shows that "old" in the report is what readers see. If they
  differ, stop and report that first.

## Predictions

**A7, by-elections off.**
- **P1.** P(ANC largest alone) rises and P(DA largest alone) falls, each by at
  least 4 points. §1.323 measured the reverse move at 9.6 and 8.9 points on an
  earlier tree.
- **P2.** ActionSA's mean list share falls. Its by-election level sits above its
  spine level, and the cap held it inside the band.
- **P3.** With `w_bye` held at ½, turning the turnout tilt off alone moves no
  party's mean citywide share by more than 0.05 points. §1.315 found that no
  turnout input moves a mean share by more than 0.011. This is measured as a
  fourth run, A7t (κ = 0 only).

**G2 and GP, γ.**
- **P4.** No party's mean list share moves by more than 0.3 points; calibration
  pins the citywide level and γ shapes the geography.
- **P5.** Ward favourites change in at least one ward and in no more than 10% of
  the 135 wards.
- **P6.** No party's median seats move by more than 3; the movement comes
  through wards won and overhang.
- **P7.** GP lies between B and G2 on P(ANC largest alone), P(DA largest
  alone) and each of the five largest parties' median seats.

## What the owner receives

One old-vs-new report per arm (B against A7, G2, GP), built under
`reports/model-changes/`. Each report gives, per party:
- mean and median seats and the 5–95% range;
- list share;
- wards won, the largest-party chance and the majority chance;
- the ward favourites that change;
- the coalition figures.

The backtest panel reads "No backtest: neither input is tested by any backtest."
No `history.json` is read. The choice of what is frozen goes to the owner as a
new item in `OWNER-DECISIONS.md`.

## Limits stated here

- **No arm is scored**, because 2026 has no result. The reports show sensitivity, not which arm is
  right.
- **G2's fit is fold 2's default fit,** and fold 2 targets 2021, so it saw 2021. That is
  legitimate for 2026 ("Settings fitted through 2021 are legitimate for 2026",
  `rounds/2026-10-23-out-of-sample/SCORES-FOR-2026-EVALUATION.md`).
- **The site's interactive hard-codes fold 1** (`export_interactive.py:158`). Freezing G2 or GP
  needs that changed too.
- **Negative ward γ in fold 2** (AIC −0.09, COPE −0.02) inverts those two parties' geography in G2
  and, if they survive pooling, in GP.

---

## Amendment, 2026-10-23, before any run (after blind pollster review)

The review found a defect in the baseline itself, checked against the code:
`run_model` takes any party listed in the fold file as fitted
(`montecarlo.py:6670`, `if p in params[ballot]["gamma"]`), so fold 1's
placeholder rows (γ written as 1.0 by the unfitted branch, `fold.py:592-605`)
block the real fits in `gamma_recent.csv`. PA (recent 0.5443), ALJAMAAH (0.8874)
and AIC are drawn at 1.0 in the live forecast. Fold 1 also writes γ = 0.0 for
parties with no target votes (MINORITY_FRONT, NFP; SRWP in fold 2), which the
base-share test does not catch.

**Definition replacing the fallback rule above.** A fold row is a *real fit*
unless the party's base citywide share is ≤ 0.001, the fold never saw it, or
its target share is 0 (γ written as 0.0). A party without a real fit takes
`gamma_recent`, then 1.0: the order `run_model` intends.

**New arm BF.** B with that definition applied to fold 1: placeholder rows no
longer block `gamma_recent`. BF against B measures the defect. G2 and GP use the
same definition and are compared with BF, so each γ comparison moves only γ
values. They are also reported against B.

**Added to the report:**
- A table per party and arm (B, BF, G2, GP) of the γ drawn and its source,
  separating "γ changed" (fitted in both) from "γ appeared" (fitted in only one).
- The negative fitted γ values (fold 2 ward AIC −0.09, COPE −0.02) flagged,
  not bounded. Bounding or shrinking them would be a new judgement call and is
  not made here.
- Each arm's movement in median seats and in ward favourites set beside the
  baseline's own 5–95% seat range.
- Arms in fixed order (B, BF, A7t, A7, G2, GP), each opening with its input's
  evidence status, with the headline chances after.

**P8 (BF).** PA's and ALJAMAAH's ward patterns flatten (γ 1.0 → 0.544 and
0.887). No party's median seats move by more than 1, and P(largest alone) moves
by less than 1 point for every party.

**P7 caveat, written before the result.** P7 holds by construction for each
party's γ. P(largest alone) depends on many γs together, so GP can fall outside
B–G2 on it without a fault; P7 is scored on the five parties' median seats and
the chances separately.

**How the frozen arm is chosen** is asked of the owner before any result is read
(OWNER-DECISIONS, "How will the frozen forecast be chosen from the pre-freeze
arms?").
