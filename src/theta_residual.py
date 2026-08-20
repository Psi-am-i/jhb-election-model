"""The CONDITIONAL dispersion of log θ — the quantity `SD_FLOOR` claims to be.

`levels.sd_for` fits a dispersion from `(log r − mu_all)²`: how far each observed
retention ratio sits from the COMMON centre. That is very nearly the MARGINAL
spread of θ, and MODEL-LOG §1.50 argued at length that the layer needs the
CONDITIONAL one — the residual about the centre the model would actually have
used, after shrinkage — because the within-pool Dirichlet independently supplies
most of the drawn variance, so asking θ to reproduce the marginal record counts
the same uncertainty twice.

**The argument was right and nothing in this repository computed the quantity.**
`SD_FLOOR = 0.15` sat at 🟡 on the strength of a sentence. This computes it,
forward validated.

    .venv/bin/python src/theta_residual.py

WHAT IS MEASURED. For every target LGE, and every metro, predicted from strictly
earlier cycles only — which is `levels.theta_record`'s own contract, so there is
no leakage to argue about:

    residual = log(observed θ) − log(the centre `theta_prior` gave that party)

**Both the centre and the fitted dispersion come from `levels.theta_prior`
itself**, called with the real baseline for that metro-year: the preceding
national election's citywide shares, which is exactly what `montecarlo` passes
it. So `sd_for` is compared per party per metro-year, at the value the draw
actually used, rather than at a bin midpoint.

That was not the first design and the difference matters. The first version
REBUILT the fit outside its closure — `sd_for` is a closure inside `theta_prior`
with no way to ask it a question from outside — and was wrong within minutes:
`sd_for` regresses squared deviation on ``baseline.get(party)``, the party's size
at the TARGET, not on the size its historical ratios were measured off. A rebuild
fed the record's own sizes fits a different line and reported 0.530 where the
model returns 0.150. ``tests/test_levels_dispersion.py`` caught it on its first
run; the guard is kept because the same trap is available to the next person.

A party with no θ history before the target is still measured. `theta_prior`
gives it the size centre and the group's spread, which is a real forecast the
model makes, and dropping those columns would report the dispersion of the
easy half.

WHY THE INTERVALS ARE CLUSTER BOOTSTRAPPED. Observations are one per party per
metro per transition, and every party in one metro-year moves with that
metro-year: an ANC collapse is not eight independent facts. Resampling metro-year
CLUSTERS is the same correction §1.34 applies to coverage; without it the
intervals are about half as wide as they should be.

THE RESULT, and it is two findings pointing opposite ways:

    national size      n   cy   measured   95% CI (cluster)   sd_for   ratio
    < 0.2%            78   17     0.915    [0.683, 1.065]      0.460   1.99x
    0.2 - 1%          96   18     0.737    [0.565, 0.869]      0.340   2.17x
    1 - 5%            32   16     0.448    [0.274, 0.613]      0.263   1.70x
    5 - 15%           14   13     0.663    [0.243, 1.008]      0.188   3.53x
    >= 15%            37   18     0.138    [0.084, 0.171]      0.150   0.92x

1. **`SD_FLOOR` is vindicated, by measurement rather than by argument.** At the
   top of the ballot the conditional dispersion is 0.138 with an interval of
   [0.084, 0.171], and the width the model uses there is 0.150 — inside it. The
   marginal record for the same parties is 0.222 and the chi-square-corrected
   fit would be 0.260, both far outside. §1.50 reasoned that the layer needs the
   conditional quantity and that applying `LOG_CHI2_BIAS` would count the same
   uncertainty twice; that reasoning is now measured and it holds.

   And `SD_FLOOR` is what puts it there: the fit is refitted per metro-year
   against that year's baseline, and the floor binds on **20 of the 37
   observations at or above 15%** (the rest run up to 0.246). Below 5% of the
   vote it never binds at all. So the floor is a top-of-ballot constant that
   happens to land on the measurement — which is a better defence than it had,
   and still not a derivation.

2. **Everywhere below 15% the prior is 1.7x to 3.5x too NARROW, and every one
   of those four intervals excludes the width the model uses.** The largest gap
   is 5-15%, the band with the fewest observations and the widest interval, but
   the two best-supported bins (n=96 and n=78) exclude it comfortably too.

   MODEL-LOG §1.58 independently measures the mid-ballot SEAT forecast as too
   narrow on a fixed calibration population. Two instruments, one on the θ prior
   and one on the seat draws, agreeing on the same band and the same direction.

   The cause is visible in the estimator: `sd_for` is a straight line in
   log(size), and the measured conditional dispersion is **not monotone** in
   size (0.915, 0.737, 0.448, 0.663, 0.138). A line cannot be right in the
   middle and at both ends, and this one is anchored at the ends.

CROSS-CHECK. The pooled forward residual sd is **0.7335** against MODEL-LOG
§1.43's independently computed forward-validation RMSE of **0.7150** for the
same estimator family — two different computations of the same thing, agreeing
to about 2.5%.

MODEL-LOG §1.59.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cityconfig
import levels

# Size bins, in national vote share. Chosen to match the bands `size_centre`'s
# own docstring reports, so these numbers can be read against ones already in
# the record rather than against nothing.
BINS = ((0.0, 0.002), (0.002, 0.01), (0.01, 0.05), (0.05, 0.15), (0.15, 1.0))

BOOT = 4000
BOOT_SEED = 20211101


def _last_lge() -> str:
    return sorted((y for y, e in cityconfig.CALENDAR.items()
                   if e.kind == "LGE" and e.results), key=int)[-1]


def residuals(codes=levels.METRO_CODES) -> list[tuple]:
    """``(size, residual, fitted_sd, party, year, code, had_record)``.

    See the module docstring. ``size`` is the national share the ratio was
    measured off — the same quantity `sd_for` takes as its argument — and
    ``fitted_sd`` is ``groups["sd"][party]``, the width the draw used.
    """
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    out: list[tuple] = []
    for year in lge:
        target = cityconfig.use_target(year)
        if not levels.theta_record(target, codes=codes):
            continue                       # the first LGE has nothing before it
        npe = cityconfig.preceding(year, "NPE")
        npe_tpl = cityconfig.CALENDAR[npe].results if npe else None
        lge_tpl = cityconfig.CALENDAR[year].results
        if not (npe_tpl and lge_tpl):
            continue
        for code in codes:
            before = levels._citywide(
                "data/raw/elections/" + npe_tpl.replace("{CODE}", code))
            after = levels._citywide(
                "data/raw/elections/" + lge_tpl.replace("{CODE}", code))
            if not before or not after:
                continue
            priors, groups = levels.theta_prior(target, before, codes=codes)
            sds = groups.get("sd", {})
            history = groups.get("worth", {})
            for party in set(before) & set(after):
                size = before[party]
                if size <= 0 or after[party] <= 0 or party not in priors:
                    continue
                centre = priors[party][1]              # the mode, exp(mu)
                if centre <= 0:
                    continue
                out.append((size,
                            math.log(after[party] / size) - math.log(centre),
                            float(sds.get(party, float("nan"))),
                            party, year, code, party in history))
    return out


def cluster_bootstrap(rows, rng) -> tuple[float, float]:
    """95% interval on sd(residual), resampling METRO-YEARS not observations."""
    clusters: dict[tuple, list[float]] = {}
    for row in rows:
        clusters.setdefault((row[4], row[5]), []).append(row[1])
    keys = list(clusters)
    reps = []
    for _ in range(BOOT):
        drawn = rng.integers(0, len(keys), len(keys))
        values = [v for i in drawn for v in clusters[keys[i]]]
        if len(values) > 1:
            reps.append(float(np.std(values, ddof=1)))
    if not reps:
        return float("nan"), float("nan")
    lo, hi = np.percentile(reps, [2.5, 97.5])
    return float(lo), float(hi)


def report() -> str:
    rows = residuals()
    rng = np.random.default_rng(BOOT_SEED)
    years = sorted({r[4] for r in rows})
    out = [f"forward-validated θ residuals: n={len(rows)} over "
           f"{len(years)} target LGEs ({', '.join(years)})",
           "",
           f"{'national size':>16} {'n':>4} {'cy':>4} {'measured':>9} "
           f"{'95% CI (cluster)':>20} {'sd_for':>8} {'ratio':>7} {'mean':>8}"]
    for lo, hi in BINS:
        sel = [r for r in rows if lo <= r[0] < hi]
        if len(sel) < 3:
            continue
        values = np.array([r[1] for r in sel])
        observed = float(values.std(ddof=1))
        ci_lo, ci_hi = cluster_bootstrap(sel, rng)
        # The MEDIAN width the model actually handed the parties in this bin.
        # Not the fit evaluated at a midpoint: `sd_for` is refitted per
        # metro-year against that year's baseline, so there is no single line.
        widths = [r[2] for r in sel if r[2] == r[2]]
        fitted = float(np.median(widths)) if widths else float("nan")
        flag = (" <-- CI excludes it"
                if fitted == fitted and not ci_lo <= fitted <= ci_hi else "")
        out.append(
            f"{lo:>6.3%}-{hi:<8.1%} {len(sel):>4} "
            f"{len({(r[4], r[5]) for r in sel}):>4} {observed:>9.3f} "
            f"{'[' + format(ci_lo, '.3f') + ', ' + format(ci_hi, '.3f') + ']':>20} "
            f"{fitted:>8.3f} {observed / fitted:>6.2f}x {values.mean():>+8.3f}"
            + flag)
    pooled = np.array([r[1] for r in rows])
    with_record = np.array([r[1] for r in rows if r[6]])
    without = np.array([r[1] for r in rows if not r[6]])
    out += ["",
            f"  pooled          n={len(pooled):>4}  sd={pooled.std(ddof=1):.4f}"
            f"  mean={pooled.mean():+.4f}"
            f"   (§1.43's independent forward RMSE: 0.7150)",
            f"  with a record   n={len(with_record):>4}  "
            f"sd={with_record.std(ddof=1):.4f}",
            f"  without one     n={len(without):>4}  "
            f"sd={without.std(ddof=1):.4f}",
            "",
            f"  SD_FLOOR={levels.SD_FLOOR}  SD_CEILING={levels.SD_CEILING}  "
            f"LOG_CHI2_BIAS={levels.LOG_CHI2_BIAS:.6f} (unused)"]
    return "\n".join(out)


def main() -> int:
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
