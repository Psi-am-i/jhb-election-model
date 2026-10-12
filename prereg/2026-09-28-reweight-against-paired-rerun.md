# Re-weighting the published draws against a paired re-run of the model

**Written 2026-09-28, before the run.** Not edited afterwards; scored as written.

**The consumer.** The interactive's turnout control (`src/reweight.py`,
build step S4 of `audits/2026-09-28-interactive-architecture/PLAN.md`) does not
re-run the model. It re-weights the published 5,000 draws of Johannesburg 2026
by each draw's four pool turnouts (`ModelRun.pool_turnout_draws`), and the page
then reports weighted seat means, quantiles and probabilities. The prediction is
about what the reader is shown: the weighted mean seats per party under the
statutory seat law (`deduct`), against what the model itself produces when the
turnout really is moved.

**The runs.** All from a `git archive HEAD src` copy, Johannesburg 2026, seed
20261104, 5,000 draws, `PYTHONHASHSEED` = `montecarlo.HASH_SEED`, `run_model`
called directly (never `main`):

* **base** — the default scenario.
* **shifted** — the same, with `montecarlo.correlated_triangular` wrapped so
  that the value returned for the Black African pool (identified by its band,
  not its position) is increased by 0.05. The wrapper consumes no random
  number, so the run is paired draw for draw with the base run. The IPF uses
  central turnout, so the shift acts after it: PLAN.md §2's "after the IPF"
  placement.
* **four seat laws** — `deduct`, `expand`, `level`, `cap` for the export.

**The re-weighting.** Exponential tilting: weights proportional to
exp(λ·t) over the four recorded pool turnouts t, with λ solved so that the
weighted mean of Black African turnout is its base mean + 0.05 and the weighted
means of the other three pools equal their base means. Effective draws are
Kish's (Σw)²/Σw².

**The standard error.** For party p, the re-weighted change is
m_w − m_base. Its SE is taken as the linearised SE of the weighted mean,
sqrt(Σ w̃ᵢ² (sᵢ − m_w)²) with w̃ normalised to sum to one, combined in
quadrature with the paired re-run's SE, sd(s_shift − s_base)/√n.

## Predictions

**P0 — the draws are shared across seat laws.** The four law runs record
identical `pool_turnout_draws`, `pr_share_draws` and `ward_winner_draws`, array
for array. Mechanism: the seat law acts only in `allocate_with_overhang`, after
every random draw of a simulation. If this fails, weights computed from one
law's draws cannot be carried to another by draw index (PLAN.md §7) and the
export has to carry the inputs per law.

**P1 — the five parties PLAN.md §3 reported.** For DA, ANC, EFF, PA and MK the
re-weighted change in mean seats is within 2 SE of the paired re-run's change.

**P2 — every seat-winning party.** For every party whose seats vary across the
base draws, the same comparison is within 3 SE. (Fifteen-odd correlated
comparisons: 2 SE each would be expected to fail somewhere by chance alone.)

**P3 — effective draws at the headline setting.** Black African +5pp with the
other three held at their means leaves between 1,000 and 1,500 effective draws
of 5,000. PLAN.md §3 reported 1,243; the lead did not re-derive it.

**P4 — the edge of the record.** Black African +8pp, the others held, leaves
fewer than 400 effective draws (PLAN.md §3 reported about 200).

**P5 — one pool alone is the wrong control.** Tilting the Black African pool
alone (the other three unconstrained) moves the DA's mean seats by less than
half the joint tilt does, because the pool turnouts are positively correlated
and selecting on one lifts all four.

**P6 — the export reproduces the published seat files.** Rebuilt from the
binary, all four of `seat_draws.csv` and `regime_{expand,level,cap}_seat_draws.csv`
are byte-equal to the files published on 2026-09-23. If one is not, the
published file is not what HEAD produces, and that is reported rather than
adjusted.

## What would falsify the approach

* **P1 failing** means the joint tilt does not stand in for moving turnout in
  the model at the size of move the page offers. The tilt matches a mean; the
  re-run moves the whole distribution. Those differ in shape, and a failure
  here says the difference matters at the level of seat means.
* **P0 failing** stops weights crossing seat laws by draw index.
* **P3 below 1,000** means the control's usable range is narrower than the
  page design assumes.
