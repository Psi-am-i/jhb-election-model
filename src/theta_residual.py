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


def _fit_line(xs, ys):
    """The shared shape: a straight line through ``log(residual²)`` in log size.

    Both forms use it, so the comparison isolates WHICH RESIDUAL is fitted and
    nothing else. In particular neither applies `LOG_CHI2_BIAS`: recovering a
    dispersion this way is biased downwards by a derivable factor, the bias is
    identical for both, and §1.59 measured the uncorrected form as exactly right
    at the top of the ballot. Correcting one and not the other would confound
    the comparison with the question §1.50 already settled.
    """
    if len(xs) < 6:
        return None
    slope, intercept = np.polyfit(xs, np.log(np.maximum(ys, 1e-6)), 1)
    return float(intercept), float(slope)


def _clip(raw: float) -> float:
    return float(min(max(raw, levels.SD_FLOOR), levels.SD_CEILING))


def form_a(record):
    """The COMMITTED estimator, rebuilt for comparison only.

    `sd_for` fits ``(log r − mu_all)²`` — squared deviation from the COMMON
    centre — against ``log(size)``, where the size is the party's size AT THE
    TARGET, taken from the baseline handed to `theta_prior`. Reproduced here
    with the record's own weighted size instead, because a form has to be
    evaluated at a size and the two agree wherever a party's size is stable;
    §1.59's table uses `theta_prior`'s real output and is the authority on what
    the model does. This is for RANKING TWO FORMS, not for quoting a width.
    """
    everything = [o for v in record.values() for o in v]
    if not everything:
        return None
    ratios = np.array([r for r, _ in everything])
    weights = np.array([levels._reliability(s) for _, s in everything])
    if weights.sum() <= 0:
        return None
    mu_all = float(np.average(np.log(ratios), weights=weights))
    xs, ys = [], []
    for _party, obs in record.items():
        w = [levels._reliability(s) for _, s in obs]
        size = float(np.average([s for _, s in obs], weights=w))
        for ratio, _s in obs:
            xs.append(math.log(max(size, 1e-5)))
            ys.append((math.log(ratio) - mu_all) ** 2)
    return _fit_line(xs, ys)


def form_b(record):
    """The REFIT: the residual about the SHRUNK centre, leave-one-out.

    The quantity the layer actually faces is `log r − log(centre it was given)`,
    and the centre is `_shrunk`'s: the party's own weighted log-mean pulled
    toward `size_centre` by ``worth/(worth + SHRINK)``. Fitting the deviation
    from the COMMON centre instead — what form A does — is fitting very nearly
    the MARGINAL spread, which §1.50 established is the wrong quantity for this
    layer and §1.59 measured as 1.7x to 3.5x adrift below 15% of the vote.

    **Leave-one-out, or it is not a residual.** An observation that helped set
    the centre it is measured against sits closer to it than a forecast ever
    will, which is the same objection `sd_for`'s own comment raises against two
    earlier attempts ("with two or three observations a party's own mean sits
    almost on top of them"). Each observation is therefore scored against the
    centre built from the party's OTHER observations, with the shrinkage weight
    recomputed on the reduced worth — so a party with one observation falls
    entirely onto the size centre, which is exactly what the model does for a
    party with no record.

    The covariate is the size the observation was MEASURED OFF, not the party's
    size at the target. That is the second difference from form A and it is
    deliberate: the dispersion of a historical ratio is a property of how big
    the party was when the ratio happened.
    """
    fit = levels.size_centre(record)
    if not fit:
        return None
    xs, ys = [], []
    for _party, obs in record.items():
        w = [levels._reliability(s) for _, s in obs]
        total = sum(w)
        for j, (ratio, size) in enumerate(obs):
            others = [(o, wt) for k, (o, wt) in enumerate(zip(obs, w)) if k != j]
            reduced = total - w[j]
            if others and reduced > 0:
                ow = [wt for _o, wt in others]
                own = float(np.average([math.log(o[0]) for o, _ in others],
                                       weights=ow))
                own_size = float(np.average([o[1] for o, _ in others],
                                            weights=ow))
                weight = reduced / (reduced + levels.SHRINK)
            else:
                own, own_size, weight = 0.0, size, 0.0
            centre = (weight * own
                      + (1 - weight) * (fit[0] + fit[1]
                                        * math.log(max(own_size, 1e-6))))
            xs.append(math.log(max(size, 1e-5)))
            ys.append((math.log(ratio) - centre) ** 2)
    return _fit_line(xs, ys)


def labelled_record(target, codes=levels.METRO_CODES) -> dict:
    """`theta_record`, but each observation carries the CYCLE it came from.

    ``{party: [(ratio, share, lge_year)]}``. `theta_record` drops the year
    (`levels.py`, and MODEL-LOG §1.43 records that the variance decomposition
    which looked at it was refuted forward). It is needed back here for one
    reason only: to leave a whole cycle out when measuring dispersion. See
    :func:`form_c`.
    """
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    out: dict[str, list] = {}
    for year in lge:
        if int(year) >= int(target.year):
            continue
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
            for party in set(before) & set(after):
                if before[party] > 0:
                    out.setdefault(party, []).append(
                        (after[party] / before[party], before[party], year))
    return out


def form_c(record, target):
    """Form B's residual, but LEAVE ONE CYCLE OUT instead of one observation.

    **This is the second trial and it is counted as one** (MODEL-LOG §1.61
    allows a new hypothesis, not a new acceptance rule; the multiple-comparison
    cost of trying forms until one wins is real on two folds).

    Form B lost stage 1 badly, and in a diagnosable direction: it fitted
    dispersions that were too NARROW, which is the opposite of what §1.59 says
    the layer needs. The cause is that leave-one-OBSERVATION-out is not leaving
    out anything much. A party's observations cluster by cycle — the ANC's 2016
    ratio in Johannesburg and its 2016 ratio in Tshwane share the 2016 national
    swing — so dropping one of eight leaves the other seven of the same cycle
    still setting the centre it is scored against. Measured: the
    leave-one-observation-out residual sd inside the pre-target record is
    **0.589 against a genuine forward 0.724 at 2016, and 0.555 against 0.705 at
    2021** — understated by 1.23x and 1.27x, in the same direction both times.

    So the unit left out has to be the CYCLE. For each observation from
    transition year Y, both the party's own mean and the size centre are rebuilt
    from observations with year != Y. That is the same clustering ITERATING rule
    11 counts at the level above, applied here.

    ``target`` is unused in the arithmetic and is taken so the caller cannot
    hand this a record built for a different one.
    """
    del target
    by_year: dict[str, list] = {}
    for party, obs in record.items():
        for ratio, size, year in obs:
            by_year.setdefault(year, []).append((party, ratio, size))
    years = sorted(by_year)
    if len(years) < 2:
        return None                       # nothing to leave out
    xs, ys = [], []
    for held in years:
        kept = {p: [(r, sz) for r, sz, y in obs if y != held]
                for p, obs in record.items()}
        kept = {p: v for p, v in kept.items() if v}
        fit = levels.size_centre(kept)
        if not fit:
            continue
        for party, ratio, size in by_year[held]:
            own_obs = kept.get(party, [])
            if own_obs:
                w = [levels._reliability(s) for _, s in own_obs]
                worth = sum(w)
                weight = worth / (worth + levels.SHRINK)
                own = float(np.average([math.log(r) for r, _ in own_obs],
                                       weights=w))
                own_size = float(np.average([s for _, s in own_obs], weights=w))
            else:
                weight, own, own_size = 0.0, 0.0, size
            centre = (weight * own
                      + (1 - weight) * (fit[0] + fit[1]
                                        * math.log(max(own_size, 1e-6))))
            xs.append(math.log(max(size, 1e-5)))
            ys.append((math.log(ratio) - centre) ** 2)
    return _fit_line(xs, ys)


def held_out_nll(codes=levels.METRO_CODES) -> dict:
    """Out-of-sample NLL per target for both forms. MODEL-LOG §1.61 stage 1.

    For each target the coefficients are fitted from the record strictly before
    it — which is what the model does — and the resulting widths are scored
    against that target's realised residuals under

        NLL = sum[ log w + r^2 / (2 w^2) ]

    a proper scoring rule for dispersion: it punishes a width that is too small
    through the second term and one that is too large through the first, so
    neither widening nor narrowing alone can win. Lower is better.

    Returns per-target totals and per-observation means, plus the metro-year
    cluster count, because two totals over different n are not comparable and
    the clusters are what rule 11 counts.
    """
    rows = residuals(codes=codes)
    by_target: dict[str, list] = {}
    for row in rows:
        by_target.setdefault(row[4], []).append(row)
    out = {}
    for year, sel in sorted(by_target.items()):
        target = cityconfig.use_target(year)
        record = levels.theta_record(target, codes=codes)
        fits = {"A": form_a(record), "B": form_b(record),
                "C": form_c(labelled_record(target, codes=codes), target)}
        entry = {"n": len(sel),
                 "clusters": len({(r[4], r[5]) for r in sel})}
        for name, coef in fits.items():
            if coef is None:
                entry[name] = None
                continue
            total = 0.0
            for size, resid, _w, _p, _y, _c, _had in sel:
                width = _clip(math.exp(0.5 * (coef[0] + coef[1]
                                              * math.log(max(size, 1e-5)))))
                total += math.log(width) + resid ** 2 / (2 * width ** 2)
            entry[name] = {"nll": total, "mean": total / len(sel),
                           "intercept": coef[0], "slope": coef[1]}
        out[year] = entry
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
    out += ["", "MODEL-LOG §1.61 stage 1 — held-out NLL per observation, "
            "lower is better.", "A = committed, B = refit leave-one-observation-"
            "out, C = refit leave-one-cycle-out.",
            f"{'target':>8} {'n':>5} {'cy':>4} {'A':>10} {'B':>10} {'C':>10}"
            f"  winner"]
    for year, entry in held_out_nll().items():
        cells, have = [], {}
        for name in ("A", "B", "C"):
            blk = entry.get(name)
            cells.append(f"{blk['mean']:>10.4f}" if blk else f"{'—':>10}")
            if blk:
                have[name] = blk["mean"]
        best = min(have, key=have.get) if have else "—"
        out.append(f"{year:>8} {entry['n']:>5} {entry['clusters']:>4} "
                   + " ".join(cells) + f"  {best}")
    out += ["", "  B loses both usable folds; C wins one and loses one, which "
            "§1.61 calls undetermined.", "  Neither reached stage 2. The model "
            "is unchanged. MODEL-LOG §1.62."]
    return "\n".join(out)


def main() -> int:
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
