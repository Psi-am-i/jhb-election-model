# Pre-registration: what reaches the simulated vote in the Johannesburg 2026 forecast

Written 2026-10-16, before any run below, on `remediation` at `8a71a9d`. Census and
code-path arguments: the scratchpad census (`census.md`, rows cited by number). This
file is not edited after a result is read; results and scoring go in MODEL-LOG.

## Question

For each input whose effect the census could not settle by argument: does it move
(a) a party's citywide mean list share, (b) which party is the favourite in a ward,
(c) a party's mean seats? And does the page's turnout control agree with a re-run?

## What the predictions rest on (argued, montecarlo.py at 8a71a9d)

- κ calibration (:4842, :4847) pins every party's mean drawn share to its pool-spec
  centre `c` within 1e-3 relative, through the same `_turnouts` (:4501) the run uses.
- `c` is the IPF party margin, fixed to the centres (:3298); pool size, pool turnout
  and pool vectors change the matrix, not the margin, unless the capacity cap
  (:3280) binds.
- `solve_and_predict` pins `weights @ pred` to the drawn citywide target (:1573,
  :1583); VD turnout and the roll only redistribute it (:7402, :7422).
- `v_comp` (:4572-4583) subtracts the run's own turnout composition variance from each
  party's own term, so the total width is held unless `own2 < 0` is floored.

## Runs

All in process through `run_arm.py` (scratchpad), `montecarlo.run_model` with
`run_dir` outside `data/`, `PYTHONHASHSEED=0`, Johannesburg 2026, shipped DEFAULTS
except the one change named. No `montecarlo.py` script run, no `compare_history`.

| arm | change | how applied |
|---|---|---|
| A0 | none | baseline, seed 20261104 |
| A1 | none | seed 20261105 (sampling scale only) |
| Z | none | A0 again at 200 draws, twice (harness determinism check) |
| T1 | Black African pool turnout band +0.05 on all three points (lo, mode, hi), capped 0.95 | `read_pool_spec` wrapped; the spec is read and staleness-checked as usual, then edited in memory |
| T2 | all four pools' bands +0.05 | same |
| T3 | `turnout_correlation` 0.63 → 0.0 | `--set` |
| T4 | VD turnout: VDs whose `turnout_2026_projected` is above the roll-weighted median get ×1.15 on `turnout_2026_projected` and `turnout_2021` (cap 0.95) | `processed=` a scratch directory of symlinks to `data/processed`, `turnout.csv` rewritten |
| T5 | Black African pool `registered` ×1.2 | `read_pool_spec` wrapped |
| C1 | `POOL_CAPACITY_MARGIN` 0.98 → 0.5 | module attribute (read at call time, :3280) |
| C2 | `POOL_CAPACITY_MARGIN` → 0.2 (guard: the cap can be seen) | module attribute |
| W1 | `ward_noise_sd` 0.10 → 0 | `--set` |
| L1 | `level_shrink` 0.35 → 0 (positive control on the mean layer; width-record variant exists) | `--set` |
| TILT | `reweight.turnout_tilt` at Black African +0.05, others held, on A0's own draws | no run |

**Draws.** 2,000 per arm, seed 20261104 (paired by draw index), A1 on 20261105. Rule
fixed now: if A0 takes more than 12 minutes wall time, every other arm drops to
1,000 draws, decided on A0's runtime before any arm's result is read. Arms run up to
four at a time. Estimated total under 90 minutes.

## Quantities read

1. Mean list share per party (`pr_share_draws` mean), points.
2. Ward favourite: the modal winner over draws in each of the 135 wards; count of
   wards whose favourite differs from A0.
3. Mean seats per party (deduct law); seat p5-p95.
4. Mechanism readings from each trace: per-party κ (`35_widths.parties[p].kappa`),
   `kappa_converged`, `v_comp`, `floored`; capacity headroom (`ipf_stats`/`41_guards`).

## Noise

Same-seed arms are paired by draw index. For each quantity, the paired difference's
standard error is `sd_d(x_arm,d − x_A0,d) / √N`. A "moves" verdict needs
|Δ| > 3 × paired SE **and** above the stated size; a "does not move" verdict needs
|Δ| below the stated bound. A1 − A0 is reported as the unpaired sampling scale. Z
must give byte-identical draws; if not, every paired SE is void and the plan stops.

Parties scored: the six with mean list share above 5% (ANC, DA, ActionSA, EFF, MK,
PA), and the maximum |Δ| over all parties above 1%.

## Predictions

| id | arm | prediction |
|---|---|---|
| P0 | Z | byte-identical `pr_share_draws` and seats across the two runs |
| P1 | T1 | mean list share: every party above 1% moves less than 0.05 points; κ moves in the compensating direction (DA's κ up, ANC/MK/EFF κ down) |
| P2 | T1 | mean seats: every party within ±0.5 seats of A0; ward favourites changed ≤ 3 |
| P3 | TILT vs T1 | TILT gives DA −3.0 to −5.5 seats on A0's draws; T1 gives DA within ±0.5. The two disagree by more than 3 combined SE |
| P4 | T2 | as P1 and P2 |
| P5 | T3 | means as P1; each scored party's sd of list share within ±10% (relative) of A0; seat p5-p95 width within ±2 seats of A0; mean seats within ±0.5 |
| P6 | T4 | mean list share: every party moves less than 0.01 points; ward favourites change in 2 to 20 wards, net towards the DA; mean seats within ±1.5 for every party, ANC's change ≤ 0 |
| P7 | T5 | as P1 and P2 |
| P8 | C1 | no party's mean list share moves more than 0.05 points (no party asks for more than half its pool ceiling) |
| P9 | C2 | DA and ANC mean list shares each fall by more than 2 points |
| P10 | W1 | `pr_share_draws` identical to A0 (ward noise touches only the ward tally); ward favourites changed ≤ 5; mean seats within ±1 |
| P11 | L1 | ANC and DA mean list shares each rise by more than 1 point; mean seats move more than 2 for at least one of them |

## What would falsify the census

- P1, P4, P5 or P7 failing (a mean moving) means κ does not absorb pool-layer
  changes, and every "W only" verdict for pool turnout, pool size and census rows
  (census I10-I12, I19, I33, register group R-pool) is wrong.
- P3 failing in the direction "T1 also moves the DA" means the site note is true of
  the shipped law and census §3 is wrong.
- P6 failing on the mean means VD turnout reaches citywide shares and the
  `solve_and_predict` argument is wrong.
- P9 or P11 failing means the harness cannot see a mean move, and every null above
  is void.
