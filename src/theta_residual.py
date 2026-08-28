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

import functools
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

    **THE BASELINE IS THE ONE `run_model` PASSES, NOT THE RAW CITYWIDE TALLY.**
    `run_model` drops every party that is not on the target's ballot from
    `base_city_d` *before* calling `theta_prior`, and `sd_for`'s fit runs over
    `record` filtered by ``baseline.get(party) > 0`` — so a dropped party is out
    of the regression, the line moves, and **every** party's width moves with
    it. Until 2026-08-28 this function passed the raw tally, so the whole module
    measured a fit the model does not run. The drop removes 286 parties across
    the 32 metro-years, moves **no** row and **no** residual — a party not on
    the ballot has no result, so it was never in the outcome side of the join —
    and moves the largest single width by **0.605**. On the two Key-4 folds the
    committed held-out score moves 1.3241 → 1.0516 at 2016 and 0.5791 → 0.4319
    at 2021. MODEL-LOG §1.124.

    **Memoised**, because it is ~45 seconds of `theta_prior` refits and file
    reads and the suite calls it five times in one process. **The cache is keyed
    on the `levels` module state it depends on, not on `codes` alone** —
    `test_levers_are_live._patched` sets module constants process-globally and
    restores them in a `finally`, and a `finally` cannot invalidate an
    `lru_cache`. Without the state key a patch landing before a call here would
    poison every later call and survive its own restore, silently, in the file
    whose title is *"a measurement whose subject can move under it"*. A fresh
    list is handed back each call so no caller can corrupt another's. Measured
    2026-08-28: `test_levels_dispersion` 177s → 53s.
    """
    return list(_residuals_cached(tuple(codes), _levels_state()))


def _levels_state() -> tuple:
    """Everything in `levels` that can change what `residuals` returns.

    Read at CALL time, never bound as a default — the §1.33 lesson. If you add
    a module-level lever to `levels.py` that reaches `theta_record`, `sd_for` or
    `theta_prior`, it belongs here, or the memo will hand back an answer
    measured under the old value.
    """
    return (levels.SD_FLOOR, levels.SD_CEILING, levels.SHRINK,
            getattr(levels, "THETA_WINDOW", None),
            tuple(sorted(getattr(levels, "THETA_EXCLUDE_TARGETS", ()) or ())),
            getattr(levels, "FILTER_TYPE_A", None),
            getattr(levels, "EXCLUDE_DEMARCATION_CROSSING", None))


@functools.lru_cache(maxsize=None)
def _residuals_cached(codes: tuple, _state: tuple) -> tuple:
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
            # THE MODEL'S BASELINE, not the raw tally. See the docstring. NAMES
            # ONLY — `ballot_roster` reads the party column of the target's
            # result file and nothing else, which is the read
            # `pools.contesting_parties` already makes and `run_model` acts on.
            for _gone in levels.absent_from_ballot(
                    before,
                    levels.ballot_roster("data/raw/elections/"
                                         + lge_tpl.replace("{CODE}", code))):
                before.pop(_gone, None)
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
    return tuple(out)


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
    """The committed estimator's SHAPE, rebuilt at the record's own size.

    ⛔ **NOT the width the model uses, and NOT what Key 4 scores.** That is
    :func:`held_out_nll`'s ``COMMITTED`` column, which reads `theta_prior`'s own
    output. This function was labelled "A = committed" in the stage-1 table for
    three months and `ITERATING.md`'s untradeable Key 4 was written against that
    label; MODEL-LOG §1.124 records the correction and the two folds it moves.

    `sd_for` fits ``(log r − mu_all)²`` — squared deviation from the COMMON
    centre — against ``log(size)``, where the size is the party's size AT THE
    TARGET, taken from the baseline handed to `theta_prior`. Reproduced here
    with the record's own weighted size instead, because a form has to be
    evaluated at a size and the two agree wherever a party's size is stable;
    §1.59's table uses `theta_prior`'s real output and is the authority on what
    the model does. This is for RANKING TWO FORMS, not for quoting a width.

    The two differ by more than rounding — 0.7531 against 1.3241 at 2016, 0.2280
    against 0.5791 at 2021 — and, decisively, **they can rank the same candidate
    differently**, so "a relative comparison survives a biased instrument" is
    false here. A/B/C remain useful as a controlled three-way comparison of
    WHICH RESIDUAL is fitted, holding `_fit_line` constant. They are not the
    floor.
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


# Two-sided 95% Student-t critical values, df 1..30. A STANDARD TABLE, not a
# judgement: these are quantiles of a named distribution and `scipy` is not
# installed. `_t_crit` is used for the cluster band in `key4_delta`, where the
# number of clusters is eight and a normal quantile would be 13% too narrow.
_T95 = (12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042)


def _t_crit(df: int) -> float:
    if df < 1:
        return float("nan")
    return _T95[df - 1] if df <= len(_T95) else 1.960


def level_df() -> float:
    """`montecarlo.LEVEL_DF`, resolved AT CALL TIME.

    Imported lazily and never bound as a default, for the §1.33 reason: the
    same constant was once a default argument, and sweeping it changed nothing
    for five values in a row while reading as "the tail does nothing".
    """
    import montecarlo
    return float(montecarlo.LEVEL_DF)


def nll_gauss(resid: float, width: float) -> float:
    """Negative log density of ``resid`` under ``Normal(0, width)``.

    **The constant is carried.** Every held-out NLL in this repository before
    2026-08-28 was ``log w + r²/(2w²)`` — this quantity minus ½log2π =
    0.918939. Dropping it is harmless inside one comparison and makes the
    number meaningless on its own: it is what let "COMMITTED is about twice A"
    be written down, a ratio on a scale whose zero was arbitrary and which
    2006 already reports as negative. MODEL-LOG §1.124.
    """
    return (math.log(width) + resid ** 2 / (2 * width ** 2)
            + 0.5 * math.log(2 * math.pi))


def nll_t(resid: float, width: float, df: float | None = None) -> float:
    """Negative log density under the predictive `montecarlo.log_shock` DRAWS.

    **This is the score, and the Gaussian was the wrong member of the family.**
    `log_shock` returns ``exp(sd·√((df−2)/df)·t_df)`` with ``df = LEVEL_DF = 7``,
    so on the log scale the model's shock is Student-t with SCALE
    ``s = width·√((df−2)/df)``, not a Gaussian of sd ``width``. The declared
    80% band in `theta_prior` uses ±1.2816·sd and the drawn one is ±1.196·sd —
    the two agree in the body and differ entirely in the tail, which is where
    this fold's score lives.

    The size of the error: at ``w = SD_FLOOR`` and ``|r| = 2`` — a COPE-sized
    collapse — the Gaussian charges 88.9 nats and the t7 charges 14.4. A factor
    of six on ONE observation in a fold of 85. Every candidate this key has
    ever been used on (the Type A filter, state C, the `THETA_WINDOW` arms)
    works by removing or reweighting far-tail observations, so the Gaussian
    mis-ranked exactly the class of change it was pointed at.
    """
    df = level_df() if df is None else float(df)
    scale = width * math.sqrt((df - 2.0) / df)
    z = resid / scale
    const = (0.5 * math.log(df * math.pi)
             + math.lgamma(df / 2.0) - math.lgamma((df + 1.0) / 2.0))
    return (math.log(scale) + const
            + 0.5 * (df + 1.0) * math.log1p(z * z / df))


def _score(pairs, df=None) -> dict:
    """Score ``[(residual, width, cluster)]`` and decompose by cluster.

    Returns the per-observation mean (`mean`), the mean of the per-cluster
    means (`cluster_mean`) and the cluster means themselves. **The two means
    differ, and when they disagree one metro-year is driving the answer**: the
    per-observation mean weights a metro-year with 20 parties four times one
    with 5, which for a clustered design is the wrong weighting and for a
    per-observation loss is the right one. Report both; the disagreement is the
    diagnostic.

    `w_eff` is the width an honest Gaussian would have needed to score this
    badly, ``exp(NLL_gauss − ½)``. It is the reader-facing version of the
    number: a log score has no natural zero and 2006's is negative, so it
    cannot be quoted as a ratio, but an effective width has units and can.
    """
    if not pairs:
        return None
    clusters: dict[tuple, list[float]] = {}
    tot_t = tot_g = 0.0
    for resid, width, key in pairs:
        t, g = nll_t(resid, width, df), nll_gauss(resid, width)
        tot_t += t
        tot_g += g
        clusters.setdefault(key, []).append(t)
    n = len(pairs)
    cmeans = {k: sum(v) / len(v) for k, v in sorted(clusters.items())}
    vals = list(cmeans.values())
    return {"nll": tot_t, "mean": tot_t / n, "n": n,
            "mean_gauss": tot_g / n,
            "w_eff": math.exp(tot_g / n - 0.5),
            "clusters": len(cmeans), "cluster_means": cmeans,
            "cluster_mean": sum(vals) / len(vals)}


def held_out_nll(codes=levels.METRO_CODES) -> dict:
    """Out-of-sample NLL per target. ``COMMITTED`` is Key 4; A/B/C rank forms.

    **``COMMITTED`` is the width the model draws with.** It is
    ``groups["sd"][party]`` from the `theta_prior` call `residuals` makes with
    the baseline `run_model` passes — ``sd_for(size at the target)``, clamp and
    all, off-ballot parties already dropped — so it moves when `levels.py`
    moves. There is no intercept or slope to report because there is no single
    line: `sd_for` is refitted per metro-year.

    **A, B and C do NOT.** They are rebuilt from `_fit_line` to isolate WHICH
    RESIDUAL is fitted. A's fit regresses on the record's own reliability-
    weighted size where `sd_for` regresses on the party's size at the target,
    and A is fitted ONCE per fold where `sd_for` is refitted per metro-year.
    (All four are EVALUATED at the same point — the party's size at the target.
    An earlier version of this docstring said otherwise and was wrong.) Until
    2026-08-28 the stage-1 table labelled A "committed" and `ITERATING.md`'s
    untradeable Key 4 was written against it, so a change to `levels.sd_for`
    could move the model and leave the gate where it was — the seam
    `DUPLICATION-AUDIT.md` had already named from the other side.

    **⛔ KEY 4 IS A LAYER FLOOR, NOT THE MODEL'S PREDICTIVE SCORE.** It scores
    the θ WIDTH estimator about `theta_prior`'s OWN centre. The model does not
    draw about that centre: `make_drawer` is handed `centres[party]` from
    `blended_centres`, which for any party the spine reaches is the spine's
    level, then tilted by by-elections and polls. Saying otherwise would repeat
    the error this function was rewritten to fix, one level up.

    MODEL-LOG §1.124.
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
        # THE COMMITTED WIDTH, read off `theta_prior` rather than rebuilt. A
        # nan width cannot be scored; it is counted, and `unscored` must be
        # zero for the fold to be comparable with A/B/C, which are scored on
        # every row. `test_key_4_...` asserts it.
        good = [r for r in sel if r[2] == r[2]]
        entry["COMMITTED"] = _score([(r[1], r[2], (r[4], r[5])) for r in good])
        if entry["COMMITTED"]:
            entry["COMMITTED"]["unscored"] = len(sel) - len(good)
        for name, coef in fits.items():
            if coef is None:
                entry[name] = None
                continue
            entry[name] = _score(
                [(r[1], _clip(math.exp(0.5 * (coef[0] + coef[1]
                                              * math.log(max(r[0], 1e-5))))),
                  (r[4], r[5])) for r in sel])
            entry[name].update(intercept=coef[0], slope=coef[1])
        out[year] = entry
    return out


def key4_delta(incumbent: dict, candidate: dict, fold: str) -> dict:
    """The paired, CLUSTERED comparison Key 4's pass rule is stated against.

    ``incumbent`` and ``candidate`` are ``{(party, year, code): (resid, width)}``
    — one entry per held-out observation, each arm scored under its own
    `theta_prior` centre AND width, because a change moves both.

    **Why this exists.** Key 4 was written as a bare inequality between two
    per-observation means. That is indefensible in a document whose rule 11
    says metros within a cycle share one national swing, for four reasons at
    once: no band, so a truly neutral change fails about half the time per fold
    and about three quarters of the time across two; no clustering, so 97
    observations are treated as 97 facts when they are 8 metro-years; a loss
    quadratic in the residual, so the mean is a summary of its two worst rows;
    and folds that are not independent of each other, 2016's record being a
    subset of 2021's. §1.124's own decisive counterexample is a 0.0164
    nats/observation move — which is almost certainly inside this band, and is
    why that finding now rests on the MECHANISM and not on the number.

    **The population must be identical.** Denominator drift is the oldest way
    to make a scoring instrument lie, and a candidate that changes
    `theta_prior`'s coverage changes which parties are scored. This REFUSES
    rather than reconciling: score the intersection deliberately and report
    both counts, or do not claim a comparison.

    Returns the per-observation delta, the per-cluster deltas, a t(G−1)
    interval on the cluster means, and the sign count — which at eight clusters
    is the statistic to trust, and is free.
    """
    del fold                                  # the caller has already selected
    if incumbent.keys() != candidate.keys():
        only_i = sorted(set(incumbent) - set(candidate))[:5]
        only_c = sorted(set(candidate) - set(incumbent))[:5]
        raise ValueError(
            f"Key 4 population moved: incumbent has {len(incumbent)} "
            f"observations, candidate {len(candidate)}. Two means over "
            f"different populations are not a comparison. Only in incumbent: "
            f"{only_i}; only in candidate: {only_c}. Score the intersection "
            f"deliberately and report both counts.")
    per_obs, clusters = {}, {}
    for k, (r_i, w_i) in incumbent.items():
        r_c, w_c = candidate[k]
        d = nll_t(r_c, w_c) - nll_t(r_i, w_i)
        per_obs[k] = d
        clusters.setdefault((k[1], k[2]), []).append(d)
    cmeans = [sum(v) / len(v) for v in clusters.values()]
    g = len(cmeans)
    pooled = sum(per_obs.values()) / len(per_obs)
    cluster_mean = sum(cmeans) / g
    if g > 1:
        var = sum((x - cluster_mean) ** 2 for x in cmeans) / (g - 1)
        se = math.sqrt(var / g)
        lo, hi = (cluster_mean - _t_crit(g - 1) * se,
                  cluster_mean + _t_crit(g - 1) * se)
    else:
        se, lo, hi = float("nan"), float("-inf"), float("inf")
    return {"n": len(per_obs), "clusters": g,
            "pooled_delta": pooled, "cluster_delta": cluster_mean,
            "se": se, "ci95": (lo, hi),
            "worse_clusters": sum(1 for x in cmeans if x > 0),
            # THE FLOOR, and it is a floor: a worsening whose interval covers
            # zero is `undetermined` and does not block. ITERATING.md Key 4.
            "fails": lo > 0.0}


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
    table = held_out_nll()
    out += ["", "HELD-OUT NLL PER OBSERVATION under the predictive the model "
            "DRAWS: log θ = log(centre)", f"  + s·t_df, s = w·√((df−2)/df), "
            f"df = LEVEL_DF = {level_df():g}. Lower is better. Constants "
            f"carried, so these are", "  log scores and not log scores minus "
            "an unstated offset.",
            "",
            "  COMMITTED is ITERATING.md's KEY 4: the width `theta_prior` "
            "actually handed the party,",
            "  sd_for(size at the target) off the baseline `run_model` passes, "
            "clamp and all. It is",
            "  the only column a change to levels.py is guaranteed to move.",
            "  A / B / C are REBUILDS that differ only in which residual is "
            "fitted, at a common",
            "  `_fit_line`. A is NOT the committed width. MODEL-LOG §1.61 "
            "stage 1, corrected §1.124.",
            "",
            "  ⛔ THIS IS A LAYER FLOOR, NOT THE MODEL'S PREDICTIVE SCORE. It "
            "scores the θ WIDTH",
            "  about `theta_prior`'s OWN centre; the model draws about the "
            "SPINE's centre, tilted",
            "  by by-elections and polls. Do not quote it as the model's "
            "estimation loss.",
            "",
            f"{'target':>8} {'n':>5} {'cy':>4} {'COMMITTED':>10} {'A':>9} "
            f"{'B':>9} {'C':>9}  {'gauss':>8} {'w_eff':>8}  best A/B/C"]
    for year, entry in table.items():
        cells, have = [], {}
        for name in ("A", "B", "C"):
            blk = entry.get(name)
            cells.append(f"{blk['mean']:>9.4f}" if blk else f"{'—':>9}")
            if blk:
                have[name] = blk["mean"]
        com = entry.get("COMMITTED")
        best = min(have, key=have.get) if have else "—"
        out.append(
            f"{year:>8} {entry['n']:>5} {entry['clusters']:>4} "
            + (f"{com['mean']:>10.4f}" if com else f"{'—':>10}") + " "
            + " ".join(cells)
            + (f"  {com['mean_gauss']:>8.4f} {com['w_eff']:>8.2f}" if com
               else f"  {'—':>8} {'—':>8}")
            + f"  {best}"
            + (f"  ({com['unscored']} unscored)"
               if com and com.get("unscored") else ""))
    out += ["",
            "  `gauss` is the SAME widths scored as a Gaussian — the family "
            "every held-out NLL in",
            "  this repository used before 2026-08-28, but with the ½log2π = "
            "0.918939 those figures",
            "  dropped. Subtract it to reconcile with a number quoted in "
            "§1.61, §1.74 or §1.82.",
            "  `w_eff` = exp(gauss − ½): the width an honest Gaussian would "
            "have needed to score",
            "  this badly. It has units, which a log score does not — note "
            "2006's score is NEGATIVE,",
            "  so nothing here may be quoted as a RATIO.",
            ""]
    for year in ("2016", "2021"):
        com, a = table[year].get("COMMITTED"), table[year].get("A")
        if com and a:
            out.append(
                f"  KEY 4, fold {year}: COMMITTED {com['mean']:.4f} against "
                f"the rebuild A {a['mean']:.4f} — a difference of "
                f"{com['mean'] - a['mean']:+.4f} nats/obs "
                f"(effective width {com['w_eff']:.2f} against "
                f"{a['w_eff']:.2f}).")
    out += ["  The two columns are different estimators and CAN RANK A "
            "CANDIDATE DIFFERENTLY. That is",
            "  not hypothetical. But the finding rests on the MECHANISM — A is "
            "rebuilt from",
            "  `_fit_line` and reaches `levels` only through the clamp, so it "
            "cannot respond to a",
            "  change in `sd_for` at all — and NOT on the size of any one gap, "
            "which is inside the",
            "  clustering noise. Use `key4_delta` for a comparison; a bare "
            "difference of means is not one.",
            "",
            "  B loses both usable folds; C wins one and loses one, which "
            "§1.61 calls undetermined.",
            "  Neither reached stage 2. The model is unchanged. MODEL-LOG "
            "§1.62, §1.124."]
    return "\n".join(out)


def main() -> int:
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
