# Defect note: `compress_levels` lifts every small party's centre by about a third

A defect report, not a design. Read-only; nothing written in `src/` or `data/`.
Found in the 1b small-party work (`1b-small-party-design-v3.md`) and measured
independently by its reviewer (`step2/2-recheck-1b-v2.md`, Part 4).

## What it is

`compress_levels` (`src/montecarlo.py:2541-2599`, called at `:2502`; live at
`level_shrink` = 0.35, `level_shrink_scale` = 0.04 in `DEFAULTS`, `:409-410`)
keeps `1 − c·s/(s + h)` of each party's level and returns the freed mass by
uniform renormalisation to the original total (`:2596-2598`). For a party far
below `h` the kept fraction is about 1, so its centre is multiplied by the whole
renormalisation factor `total / freed`. Every small party therefore receives the
same proportional boost. The boost is set by how much the large parties gave up,
not by anything about the small party.

## Evidence

Unit parties of the 1b v3 line (previous result and centre below three quotas;
established and national debutants), mean over parties:

| target | parties | log(after shrink / before shrink), `30_centres` | factor | reviewer: result against each stage, established only |
|---|---|---|---|---|
| 2011 | 63 | +0.330 | 1.39 | lift +0.310 (1.36x) |
| 2016 | 81 | +0.339 | 1.40 | +0.272 (1.31x) |
| 2021 | 127 | +0.325 | 1.38 | +0.254 (1.29x) |
| JHB 2026 | 25 | +0.291 | 1.34 | +0.185 (1.20x), net of dividing the after-shrink centres by their total of 1.112 |

The two columns measure the lift against different references: my column
compares `after_shrink` with `before_shrink`; the reviewer's compares mean log
residuals of the result at the spine stage and at the normalised after-shrink
stage. They agree in sign and size: **1.29-1.40x in every backtest cycle and
1.20-1.34x at 2026, never below 1.2.**

Results against the after-shrink centre for the same established parties
(reviewer, Part 4): mean log residual −0.886 / −0.156 / +0.427 at
2011 / 2016 / 2021, against −0.577 / +0.117 / +0.681 at the spine stage. The
lift moves the residual by about −0.3 in every cycle. The remaining swing
(−0.58 → +0.12 → +0.68 at the spine) is the cycle common to small parties, which
no level fix removes.

The function's docstring records the cost: ranks 13+ go from +0.78pp to +8.68pp
(`:2575-2583`). The same docstring says "Off by default (`level_shrink = 0.0`)"
(`:2585`), but `DEFAULTS` ships 0.35 (`:409`). The docstring is stale.

## Why it matters

- Small parties' centres are high by about 0.3 in log in every cycle, a constant
  bias in sign and size.
- In arm E this bias was hidden by the within-pool Dirichlet's spike at zero.
  Under the 1b v3 draw it is carried inside the cycle width: σ_cyc is an RMS
  about zero, so it includes the mean bias, −0.20 across three cycles about the
  `pool_spec` centre.
- Removing the lift would change the 1b widths: the writer's artefact key over
  the centres' inputs forces a re-estimate. The reviewer estimates σ_cyc for 2026
  falling from 0.57 to about 0.48.

## Not in this note

A repair. The docstring lists three targeted redistributions already measured
and rejected on summed error. Any repair is a level-layer change to be designed,
pre-registered and compared paired, as its own item.
