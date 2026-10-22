# Pre-registered predictions, written BEFORE the analysis run

Written 2026-08-31, after reading `score.seat_matrix` / `score.crps_by_party`
and before `measure_crps.py` produced a single number. The canonical
`compare_history.py` run was already in flight but had not been read.

## The mechanism, as read off the code

`score.seat_matrix` (src/score.py:191) keeps column *i* iff

    truth[i] > 0  or  samples[:, i].max() > 0

so a column a forecaster does NOT score is one where **that forecaster is
identically zero in every draw AND the party won nothing**.

## P1 — the arithmetic prediction (deterministic, not statistical)

For any such dropped column, seats are non-negative, so `x ≡ 0`, `y = 0`:

    CRPS = E|X − y| − ½E|X − X'| = 0 − 0 = 0   exactly.

Therefore `crps["total"]`, being a **SUM**, must be **numerically identical**
whether it is taken over the forecaster's own set or over any superset of it —
the union across forecasters, or the full universe.

**Prediction: `union_total == own_total` to the last bit, for every forecaster
at every one of the 16 city-years.** If that fails, my reading of the code is
wrong and the rest of this is void.

## P2 — the mean is the drifting statistic, not the sum

`crps["mean"]` divides the same sum by `n_scored`. The model draws 1000 times
and picks up columns for every party it seats in ≥1 draw; `last-lge` and
`uniform-swing` are deterministic (`benchmarks._repeat`) and pick up almost
none. So the model's denominator is the larger one.

**Prediction: switching sum → mean moves the comparison strongly IN THE
MODEL'S FAVOUR** (it divides the model's total by a bigger number), i.e. the
mean flatters the model and must never be used as the cross-forecaster key.

## P3 — the intersection is the WRONG common support

Restricting to the intersection deletes columns on which a forecaster is
non-zero — real, earned penalty — and deletes columns where truth > 0 if any
one forecaster missed the party entirely. **Prediction: intersection lowers
every forecaster's total, and lowers the model's by more than the deterministic
baselines'** (the model has more non-zero columns to lose). Intersection is
therefore a biased common support, not a fix.

## P4 — the headline ranking

**Prediction: the model-vs-uniform-swing CRPS ranking does NOT move** under the
union (P1 says it cannot), and the panel-level conclusion drawn from
`crps["total"]` therefore stands. The dilution result already established for
the VARIOGRAM (0.5498 → 0.0801 on padding 19 columns to 56) does **not**
transfer to CRPS, because a variogram is a MEAN OVER PAIRS and CRPS total is a
SUM over columns whose extra terms are exactly zero.

If P1 holds and P4 holds, the honest verdict is: `crps["total"]` is *not*
denominator-drift-affected; `crps["mean"]`, `n_scored`, `coverage_all`,
`energy` and `variogram` are.
