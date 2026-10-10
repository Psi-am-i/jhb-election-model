# Step 12: the two scorings compared (2026-10-10)

Scorers 1 and 2 worked from `reviews/STEP12-SCORING-BRIEF.md` independently.
Each re-derived the panel scores of all 240 runs from the raw arrays, and each
found every run matching its own `result.json`.

## Agreed verdicts

| Prediction | Verdict | Deciding number |
|---|---|---|
| E1, E2, E4, P10, P1, P2, P2b, P3, P16, P13, P19 (with A5) | held | as in both files |
| P6 F1-F6, B1, B3, CHANGE | held | PA ratio 2.000 → 1.029; PA seats 16.92; coherent seat error 735 → 721 |
| P8, four no-entry city-years, guard lists, 2026 clauses | held | seven parties 0.415%, 0-1 seat in 84.3% of draws |
| P8, panel-mean list MAE ≤ +0.005 | falsified | +0.0754 |
| P8, list MAE falls at the three named city-years | falsified, 0 of 3 | ekurhuleni 2011 +0.940, mangaung 2021 +0.611, NMB 2021 +0.029 |
| P8, coherent seat error | inconclusive (A2 middle region) | +2 |
| P11, PA, DA, coherent | held | PA −0.78, DA +0.51, −2 |
| P11, no other party > 0.6 seats | falsified | EFF +0.98 |
| P11, ANC gains | falsified | ANC −0.33 |
| P11, list MAE moves < 0.05 everywhere | falsified | 18 of 24 at ≥ 0.05, largest 0.603 |
| P17, MK falls 1.5-4 | falsified | −1.40 |
| P17, EFF gains | falsified | −0.84 |
| P17, GOOD | not scorable | GOOD is off the 2026 ballot (merged into RISE) |
| P17, panel-mean list MAE | ambiguous | +0.0336: outside the predicted range, below the stated falsifier |
| P17, all other clauses and A1 | held | |
| P12 clause 1 | held | |
| P12 clause 3, `PA\|Coloured` silent at 2026 | falsified | fires in 47.9-67.9% of draws in every W-based arm; `fire_at` 0.05 (read from traces; per-pool draws not saved) |

## Where the scorers differ (unsplit, for the owner)

| Item | Scorer 1 | Scorer 2 | Same numbers? |
|---|---|---|---|
| P6 B2 (named city-years improve or hold; none worse by > 0.15) | partly held: fails only if "hold" allows no rise, and only if "I expect" is a prediction | falsified on both clauses | yes: joburg 2021 +0.154, ekurhuleni 2021 +0.015, four city-years > 0.15, worst ethekwini 2016 +0.425 |
| E3 without A11 | falsified at the 16 backtest specs | holds either way | yes. A11 was committed before any arm run (ec2d602), so both score E3 held under the operative text |
| E3, 2026 member weights differing by ≤ 2.2e-16 | held if read as derived from the SACP change | same | yes |

## Raised by one scorer only

**Draws are not paired between every pair of arms** (scorer 2). §3 says the
arms share draws and seeds. The seed is shared; per-draw pairing is not.
Coordinator check, median per-party correlation of drawn list shares:

| Pair | ekurhuleni 2011 | mangaung 2021 | joburg 2021 |
|---|---|---|---|
| A / B0 | 1.000 | 1.000 | 1.000 |
| A / B6 | 1.000 | 1.000 | 1.000 |
| A / B8 | 0.005 | 0.005 | −0.002 |
| C16 / C | 1.000 | 1.000 | 1.000 |
| C / B | 0.965 | 0.041 | 0.664 |
| C16 / D | 0.159 | 0.202 | 0.055 |

So P8 (A/B8), P11 (C/B) and P17 (C16/D) compare unpaired runs. Scorer 2's
bootstrap puts the Monte Carlo error of an unpaired list-MAE difference at
about 0.19-0.20 points per city-year and 0.041 on the panel mean. On that
scale, P8's ekurhuleni 2011 rise is 4.1 errors, mangaung 2021 2.4, and the
panel mean 1.8. P11's 0.05 per-city-year bound is a quarter of one error, so
its 18-of-24 falsification cannot separate item 11a from draw noise.

## Departures (both scorers, same reading)

1. **C16 recipe fails `git apply --check`**, at W and at acbd9f8 where the
   prereg built it. If A13 stops it, B and C stop with it: P16, P17, P11, P13
   and the B/C/C16 parts of P12 and CHANGE become not scorable, and the P11
   and P17 falsifications go with them. P8, P6 and P12 on D and E stand. If
   A13's check means the three-way application §3.3 describes (the only form
   the recipe could pass), every verdict stands.
2. **B6's stated hash needs one trailing blank line.** If the stated hash is
   the authority (as A6 rules for B8), P6 is scored; otherwise P6 is not
   scorable from that tree. No code differs.
3. **P12 clause 2 covers 17 runs per arm**, not 25: the record has no 2011.
   Read as conditional on coverage, it holds; read as every run, it fails at
   the eight 2011 runs per arm.

## Unpredicted, both scorers

- `PA|Coloured` firing at 2026 (above). D at `w_bye` 0.4 fires about 13
  points more often than D0 and E.
- Item 11a and item 17 move the EFF at 2026 by +0.98 and −0.84 seats while
  neither changes its spine level.
- D → E moves EFF +2.58, ACP −2.22, ASA −1.41 seats.
- Item 6 worsens ward MAE by more than 0.15 at four city-years while the panel
  mean falls 0.089; mangaung 2011 supplies 0.078 of that fall (scorer 1).
