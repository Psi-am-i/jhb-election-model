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
    at 2021 — **Gaussian without its constant, the convention this module used
    at the time**; the current column is the t predictive with constants
    carried. MODEL-LOG §1.124.

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
            # `_reliability` sets `mu_all`, the shrink weight, `obs_size` and
            # `worth`, so it moves the residual AND the width. 🟡 and never
            # swept, i.e. a live sweep candidate.
            getattr(levels, "RELIABILITY_HALF", None),
            getattr(levels, "THETA_WINDOW", None),
            tuple(sorted(getattr(levels, "THETA_EXCLUDE_TARGETS", ()) or ())),
            getattr(levels, "FILTER_TYPE_A", None),
            getattr(levels, "EXCLUDE_DEMARCATION_CROSSING", None),
            # THE PAYLOADS, NOT ONLY THE SWITCHES. The first version of this
            # key carried `FILTER_TYPE_A` and `EXCLUDE_DEMARCATION_CROSSING`
            # and not the tables they read — which is precisely the defect
            # `montecarlo.py`'s delivery inventory records for the same two
            # flags: "the log recorded THAT a filter ran and nothing about what
            # it removed". Edit a register, and without these the memo hands
            # back the answer measured under the old one.
            _freeze(getattr(levels, "TYPE_A_EVENTS", None)),
            _freeze(getattr(levels, "DEMARCATION_CROSSING", None)))


def _freeze(value):
    """A hashable, order-stable image of a nested dict/set/list, for the key."""
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    if isinstance(value, (set, frozenset)):
        return tuple(sorted(_freeze(v) for v in value))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


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

    **The argument against using this as the floor is the MECHANISM, not any
    gap.** A is rebuilt from `_fit_line` and reaches `levels` only through the
    `[SD_FLOOR, SD_CEILING]` clamp, so a change to `sd_for`'s covariate or
    weighting cannot move it at all. §1.124's first draft argued from a
    0.5791 → 0.5955 counterexample instead; that is 0.0164 nats/observation on
    eight clusters, inside the band, and it is **retracted as evidence**. The
    figures it quoted — 0.7531 and 0.2280 against 1.3241 and 0.5791 — are also
    superseded twice over (Gaussian without its constant, raw baseline).

    A/B/C remain useful as a controlled three-way comparison of WHICH RESIDUAL
    is fitted, holding `_fit_line` constant. They are not the floor.
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
# number of clusters is eight and a normal quantile would be 17.1% too narrow
# (1.960 against t(7) = 2.365).
_T95 = (12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042)


# Below this, a cluster mean is float noise rather than a direction. Set six
# orders of magnitude above the 1.6e-14 dust a genuine no-op produced and six
# below the smallest real effect on record (WINDOW=3 at 2021, 0.0062).
_SIGN_EPS = 1e-9

# One-sided 95% (= two-sided 90%) Student-t critical values, df 1..30.
_T90 = (6.314, 2.920, 2.353, 2.132, 2.015, 1.943, 1.895, 1.860, 1.833, 1.812,
        1.796, 1.782, 1.771, 1.761, 1.753, 1.746, 1.740, 1.734, 1.729, 1.725,
        1.721, 1.717, 1.714, 1.711, 1.708, 1.706, 1.703, 1.701, 1.699, 1.697)


def _t_crit(df: int) -> float:
    if df < 1:
        return float("nan")
    return _T95[df - 1] if df <= len(_T95) else 1.960


def _t_crit_one_sided(df: int) -> float:
    if df < 1:
        return float("nan")
    return _T90[df - 1] if df <= len(_T90) else 1.645


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
    collapse — the Gaussian charges **87.9107** nats and the t7 **13.2845**, a
    difference of **74.6 nats on ONE observation** in a fold of 85. (Stated as a
    difference, not a ratio: these are log densities on an interval scale, which
    is the same rule that withdrew "about twice" in §1.124. An earlier version
    of this docstring said 88.9 and 14.4 — the quadratic and the log1p term
    each taken alone, i.e. both figures missing exactly the constants this
    function exists to restore.)

    Every candidate this key has been used on works by removing or reweighting
    far-tail observations, so the Gaussian scored that class of change on a tail
    penalty the model never incurs. **It did not, in the event, change any
    VERDICT** — §1.126 sweeps df from 3 to 1000 and Type A's Key-4 verdict is
    stable throughout. What changed the verdict was giving the comparison a
    noise band.
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

    `w_eff` is the width a CALIBRATED predictive would have needed to score
    this badly — the reader-facing version, because a log score has no natural
    zero (2006's is negative) and cannot be quoted as a ratio, while a width
    has units and can.

    **Both offsets are derived, and the Gaussian one was wrong by √(2π) for a
    day.** For `r ~ N(0, w)`, ``E[nll_gauss] = log w + ½ + ½log2π``, so the
    offset is 1.418939 — not ½. The ½ came from the constant-FREE score this
    module used before `nll_gauss` started carrying its constant, and leaving
    it behind made every printed width **2.5066× too large**: fold 2011 read
    452 when it is 180. The t offset is derived the same way and is 1.398228
    at ν=7; the two agreeing to 0.02 nats is the sanity check, since a t₇ and
    a Gaussian of the same sd have nearly the same entropy.

    **`w_eff_t` is the primary reader-facing column**, because it is the
    model's own predictive. It says the θ prior at 2016 and 2021 performs like
    an honest t₇ of width ≈0.77 against §1.59's pooled forward residual sd of
    0.7053 and §1.43's independent forward RMSE of 0.7150 — a two-instrument
    agreement, and a far more useful reading than the Gaussian column's alarm.
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
    df = level_df() if df is None else float(df)
    return {"nll": tot_t, "mean": tot_t / n, "n": n,
            "mean_gauss": tot_g / n,
            "w_eff_t": math.exp(tot_t / n - _calibrated_offset_t(df)),
            "w_eff_gauss": math.exp(tot_g / n - _GAUSS_OFFSET),
            "clusters": len(cmeans), "cluster_means": cmeans,
            "cluster_mean": sum(vals) / len(vals),
            # THE BAND ON THE LEVEL, not only on a delta. Quoting two fold
            # means against each other with no band is what let "the two
            # folds are within 0.006 nats" be written as though it meant
            # something. It is deep inside this interval.
            "ci95": _t_band(vals)}


# ``E[log w + r²/(2w²) + ½log2π]`` for ``r ~ N(0, w)``. DERIVED, not typed.
_GAUSS_OFFSET = 0.5 + 0.5 * math.log(2 * math.pi)


def _t_band(values) -> tuple:
    """t(G−1) interval on the mean of G cluster means. nan below two."""
    g = len(values)
    if g < 2:
        return (float("nan"), float("nan"))
    m = sum(values) / g
    var = sum((x - m) ** 2 for x in values) / (g - 1)
    se = math.sqrt(var / g)
    return (m - _t_crit(g - 1) * se, m + _t_crit(g - 1) * se)


@functools.lru_cache(maxsize=None)
def _calibrated_offset_t(df: float, draws: int = 4_000_000) -> float:
    """``E[NLL_t] − log w`` for a CALIBRATED t predictive of scale ``w√((ν−2)/ν)``.

    The closed form needs ``E[log1p(z²/ν)]``, a digamma difference; simulating
    it is three lines, exact enough (1.39792 against the analytic 1.398228 at
    ν=7) and cannot be got wrong the way the Gaussian offset was. Seeded and
    memoised, so it is deterministic and paid once per df.
    """
    rng = np.random.default_rng(20260829)
    z = rng.standard_t(df, size=draws)
    const = (0.5 * math.log(df * math.pi)
             + math.lgamma(df / 2.0) - math.lgamma((df + 1.0) / 2.0))
    return float(0.5 * math.log((df - 2.0) / df) + const
                 + 0.5 * (df + 1.0) * np.log1p(z * z / df).mean())


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
            if entry[name] is not None:     # `sel` is never empty today
                entry[name].update(intercept=coef[0], slope=coef[1])
        out[year] = entry
    return out


@functools.lru_cache(maxsize=None)
def _t_reference(df: float, draws: int = 4_000_000) -> tuple:
    """A seeded, sorted t sample. The CDF and the quantiles, without scipy."""
    rng = np.random.default_rng(20260829)
    return tuple(np.sort(rng.standard_t(df, size=draws)))


def pit_table(codes=levels.METRO_CODES, df=None) -> dict:
    """PIT and coverage of the θ prior under the predictive the model DRAWS.

    **This is the instrument a log score cannot replace, and §1.126 is the entry
    that needed it.** `NLL` charges a level bias and a width error to the same
    number; PIT separates them — ``mean(u) − ½`` is the level, ``var(u)``
    against 1/12 is the width — and coverage at a fixed quantile is a
    BOUNDED-INFLUENCE statistic where ``mean z²`` under a t₇ is not (each
    observation's contribution to the second moment is unbounded, and the
    sample mean's own variance is finite only because ν > 4). When the two
    disagree, coverage is the estimate and **the disagreement is the finding**.

    ``u = F_t(z)``, ``z = residual / (w·√((ν−2)/ν))``, the same scale
    `montecarlo.log_shock` draws through. A calibrated forecast gives
    ``mean(u) = 0.5``, ``var(u) = 1/12 = 0.0833``, and coverage at nominal.

    ``kappa_star`` is the single multiplier on every committed width that
    minimises the held-out NLL — the width the layer SHOULD have carried,
    expressed as a factor on the width it did. It is reported per fold and per
    size bin, because §1.59 measured the conditional dispersion as NON-MONOTONE
    in size and a pooled multiplier would be set by the small parties.

    ⛔ **A κ above 1 does NOT authorise widening `sd_for` by it.** §1.50
    established, and §1.59 confirmed, that this layer must carry the CONDITIONAL
    dispersion because the within-pool Dirichlet independently supplies most of
    the drawn variance. A θ layer 1.8× under-wide does not make the SEAT
    forecast 1.8× under-wide, and widening θ could over-widen the published
    intervals while fixing the layer. **`ITERATING.md` Key 2 is the gate, and it
    is untradeable** — CRPS, and the LEVEL-FREE WIDTH STATISTICS on the
    `reference` population, which is the population rule 8 requires for a width
    comparison because `claimed` selects columns from the forecaster's own
    draws. (An earlier version of this docstring called Key 2 "cluster-corrected
    seat coverage". It is not; that is a different quantity, and §1.127 carried
    the same mis-paraphrase.) This function diagnoses; it does not license.
    """
    df = level_df() if df is None else float(df)
    ref = np.asarray(_t_reference(df))
    scale = math.sqrt((df - 2.0) / df)
    q80 = float(np.abs(ref)[np.argsort(np.abs(ref))][int(0.80 * len(ref))])
    q95 = float(np.abs(ref)[np.argsort(np.abs(ref))][int(0.95 * len(ref))])

    rows = residuals(codes=codes)
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r[4], []).append(r)

    out = {}
    for year, sel in sorted(by.items()):
        resid = np.array([r[1] for r in sel])
        width = np.array([r[2] for r in sel])
        z = resid / (width * scale)
        u = np.searchsorted(ref, z) / len(ref)
        out[year] = {
            "n": len(sel),
            "pit_mean": float(u.mean()), "pit_var": float(u.var()),
            "cov80": float((np.abs(z) <= q80).mean()),
            "cov95": float((np.abs(z) <= q95).mean()),
            "mean_z2": float((z * z).mean()),
            # TRIMMED, so "a few extreme rows" is measured rather than asserted.
            "mean_z2_trim3": float(np.sort(z * z)[:-3].mean()),
            "kappa_star": _kappa_star(resid, width, df),
            "kappa_by_bin": {
                name: _kappa_star(resid[m], width[m], df)
                for name, m in ((n, np.array([lo <= r[0] < hi for r in sel]))
                                for (lo, hi), n in zip(BINS, _BIN_NAMES))
                if m.sum() >= 8},
        }
    return {"folds": out, "df": df, "q80": q80, "q95": q95}


_BIN_NAMES = ("<0.2%", "0.2-1%", "1-5%", "5-15%", ">=15%")


def _kappa_star(resid, width, df, lo=0.2, hi=6.0, steps=60) -> float:
    """The width multiplier minimising held-out NLL. Golden-section, not a grid.

    Reported as a DIAGNOSIS of how far the layer is from calibrated, never as a
    coefficient to apply — see `pit_table`'s warning about §1.50.
    """
    if len(resid) < 2:
        return float("nan")

    def cost(k):
        return float(sum(nll_t(r, k * w, df) for r, w in zip(resid, width)))

    phi = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = lo, hi
    c, d = b - phi * (b - a), a + phi * (b - a)
    fc, fd = cost(c), cost(d)
    for _ in range(steps):
        if fc < fd:
            b, d, fd = d, c, fc
            c = b - phi * (b - a)
            fc = cost(c)
        else:
            a, c, fc = c, d, fd
            d = a + phi * (b - a)
            fd = cost(d)
    return float((a + b) / 2.0)


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
    stray = [k for k in incumbent if k[1] != fold]
    if stray:
        raise ValueError(f"{len(stray)} incumbent observations are not from "
                         f"fold {fold} (first {stray[0]}). The caller selects "
                         f"the fold; this asserts it rather than trusting it.")
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
    # A CLUSTER MEAN BELOW FLOAT DUST IS NOT A WORSENING. `THETA_WINDOW=3` at
    # 2016 is a no-op — the window cannot bind on a three-transition record —
    # and it scored "2 of 8 metro-years worse" off per-observation deltas of
    # 1.6e-14, which then went into §1.125's table as though it meant
    # something. Summation order in `_fit_line`'s polyfit is enough to produce
    # them. §1.126.
    pooled = sum(per_obs.values()) / len(per_obs)
    cluster_mean = sum(cmeans) / g
    if g > 1:
        var = sum((x - cluster_mean) ** 2 for x in cmeans) / (g - 1)
        se = math.sqrt(var / g)
        lo, hi = (cluster_mean - _t_crit(g - 1) * se,
                  cluster_mean + _t_crit(g - 1) * se)
        # ONE-SIDED AT alpha = 0.05, WHICH IS THE TEST THE FLOOR ACTUALLY WANTS.
        # `lo > 0` on the TWO-sided 95% interval above is a one-sided test at
        # 2.5% — conservative in the one direction this floor cannot afford,
        # because the t score it runs on is already low-powered in the tail
        # (§1.126). t(0.95, 7) = 1.895 against the two-sided 2.365.
        one_sided_lo = cluster_mean - _t_crit_one_sided(g - 1) * se
    else:
        se, lo, hi = float("nan"), float("-inf"), float("inf")
        one_sided_lo = float("-inf")
    worse = sum(1 for x in cmeans if x > _SIGN_EPS)
    # THE SIGN COUNT AS A SECOND TRIGGER, not a tiebreak. The t interval is
    # driven by the BETWEEN-cluster variance and can miss a small worsening that
    # is utterly consistent; a one-sided exact binomial cannot. At G=8,
    # P(X>=7 | p=0.5) = 9/256 = 0.035. Checked against the arms on record: state
    # C at 2016 is 6/8 (P = 0.145, correctly not a failure) and WINDOW=2 at 2016
    # is 6/8 with an interval excluding zero, so the two triggers agree there.
    # It adds a real trigger without firing on anything already measured.
    sign_fail = g >= 8 and worse >= g - 1
    # THE p-VALUE, IN THE TREE. §1.128's nine-bin Holm table was computed by a
    # scratch script — the THIRD off-tree table in four entries, after §1.125's
    # verdict table and §1.126's PIT table — and `ITERATING.md` then said "never
    # quote the uncorrected table without the Holm column" while nothing here
    # could produce that column. One-sided, against the t reference already
    # memoised for the scoring family. §1.129.
    if g > 1 and se > 0:
        _ref = np.asarray(_t_reference(float(g - 1)))
        one_sided_p = float((_ref > cluster_mean / se).mean())
    else:
        one_sided_p = 0.0 if cluster_mean > _SIGN_EPS else 1.0
    return {"n": len(per_obs), "clusters": g,
            "pooled_delta": pooled, "cluster_delta": cluster_mean,
            "se": se, "ci95": (lo, hi), "one_sided_lo": one_sided_lo,
            "one_sided_p": one_sided_p,
            "worse_clusters": worse, "sign_fail": sign_fail,
            # THE FLOOR, and it is a floor: a worsening that clears neither
            # trigger is `undetermined` and does not block. ITERATING.md Key 4.
            "fails": one_sided_lo > 0.0 or sign_fail}


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
            f"{'B':>9} {'C':>9}  {'gauss':>8} {'w_t7':>7} {'w_gau':>7}"
            f"  best A/B/C"]
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
            + (f"  {com['mean_gauss']:>8.4f} {com['w_eff_t']:>7.2f} "
               f"{com['w_eff_gauss']:>7.2f}" if com
               else f"  {'—':>8} {'—':>7} {'—':>7}")
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
            f"  `w_t7` = exp(COMMITTED − {_calibrated_offset_t(level_df()):.6f})"
            f" and `w_gau` = exp(gauss − {_GAUSS_OFFSET:.6f}): the width a",
            "  CALIBRATED predictive of each family would have needed to score "
            "this badly. Widths have",
            "  units; a log score does not, and 2006's is NEGATIVE, so nothing "
            "here may be a RATIO.",
            "  Read `w_t7` — it is the model's own predictive. Both offsets are "
            "derived; the Gaussian",
            "  one was ½ for a day, which printed every width 2.5066x too "
            "large (§1.126).",
            ""]
    # CALIBRATION, which the log score cannot decompose and this can.
    pit = pit_table()
    out += [f"PIT AND COVERAGE under the same predictive (df = {pit['df']:g}). "
            f"A log score charges a level",
            "  bias and a width error to one number; this separates them. "
            "Calibrated: PIT mean 0.500,",
            "  PIT var 0.0833, coverage at nominal. `k*` is the single width "
            "multiplier that minimises",
            "  held-out NLL — the width the layer SHOULD have carried, as a "
            "factor on the one it did.",
            "",
            f"{'fold':>8} {'n':>5} {'PIT mean':>9} {'PIT var':>8} {'cov80':>7} "
            f"{'cov95':>7} {'mean z2':>8} {'trim3':>7} {'k*':>6}"]
    for year, e in pit["folds"].items():
        out.append(f"{year:>8} {e['n']:>5} {e['pit_mean']:>9.4f} "
                   f"{e['pit_var']:>8.4f} {e['cov80']:>7.3f} {e['cov95']:>7.3f} "
                   f"{e['mean_z2']:>8.3f} {e['mean_z2_trim3']:>7.3f} "
                   f"{e['kappa_star']:>6.3f}")
    out += ["", "  k* by size bin — a POOLED multiplier would be set by the "
            "small parties, and §1.59",
            "  measured the conditional dispersion as NON-MONOTONE in size:"]
    for year, e in pit["folds"].items():
        cells = "  ".join(f"{k} {v:.2f}" for k, v in e["kappa_by_bin"].items())
        out.append(f"{year:>8}  {cells}")
    out += ["",
            "  ⛔ k* > 1 DOES NOT AUTHORISE WIDENING `sd_for` BY IT. §1.50 and "
            "§1.59: this layer must",
            "  carry the CONDITIONAL dispersion because the within-pool "
            "Dirichlet independently supplies",
            "  most of the drawn variance. A theta layer 1.8x under-wide does "
            "NOT make the SEAT forecast",
            "  1.8x under-wide. ITERATING.md KEY 2 is the gate and it is "
            "untradeable: CRPS, and the",
            "  LEVEL-FREE WIDTH STATISTICS on the `reference` population — "
            "which already reads sd(z)",
            "  1.940 at ranks 4-12, the SEAT side of this same fault. This "
            "diagnoses; it does not",
            "  license. MODEL-LOG §1.127, §1.128.",
            ""]
    for year in ("2016", "2021"):
        com, a = table[year].get("COMMITTED"), table[year].get("A")
        if com and a:
            out.append(
                f"  KEY 4, fold {year}: COMMITTED {com['mean']:.4f} against "
                f"the rebuild A {a['mean']:.4f} — a difference of "
                f"{com['mean'] - a['mean']:+.4f} nats/obs "
                f"(t7 effective width {com['w_eff_t']:.2f} against "
                f"{a['w_eff_t']:.2f}).")
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


def dump_arm(path, codes=levels.METRO_CODES) -> int:
    """Write one Key-4 ARM to JSON: ``{"party|fold|metro": [residual, width]}``.

    **The reason this exists is a process failure worth stating.** MODEL-LOG
    §1.125's ten-row verdict table and §1.126's PIT table were both produced by
    scratch scripts that were not in the repository — and §1.126 indicts §1.125
    for exactly that, in bold, before doing it again. An arm comparison needs
    two runs under different `levels` environments, so it cannot be one function
    call; it can be two documented commands, and then the tables in the log are
    reproducible by anyone:

        .venv/bin/python src/theta_residual.py --dump-arm /tmp/base.json
        FILTER_TYPE_A=1 .venv/bin/python src/theta_residual.py \
            --dump-arm /tmp/typea.json
        .venv/bin/python src/theta_residual.py --compare /tmp/base.json \
            /tmp/typea.json

    Every fold is written, not only the two Key 4 gates on, because 2011 is the
    structural-events fold and reading it is how a candidate is understood even
    though it cannot gate.
    """
    import json
    rows = residuals(codes=codes)
    # SIZE IS CARRIED so a channel split can be read per size bin without a
    # second run. It is the party's share at the target and is identical in
    # every arm — an exclusion changes the fitting record, never the baseline —
    # so it is safe to take from whichever arm is loaded.
    out = {f"{p}|{y}|{c}": [r, w, sz]
           for sz, r, w, p, y, c, _h in rows if w == w}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"n": len(out), "obs": out}, fh)
    print(f"wrote {len(out)} observations to {path}")
    return 0


def compare_arms(incumbent_path, candidate_path) -> int:
    """`key4_delta` on two dumped arms, per fold, with the channel split.

    **The channel split is not decoration.** §1.125 asserted the gain from an
    exclusion was in the width; §1.126 measured that the widths barely move and
    said the gain is in the CENTRE — and asserted THAT without isolating it,
    which is the same error one level down. A residual IS ``log θ − log(centre
    theta_prior gave)``, so an arm carrying the incumbent's residual and the
    candidate's width is the width channel alone, and the difference from the
    full delta is the centre channel. It costs one dictionary comprehension.
    """
    import json
    inc = json.load(open(incumbent_path, encoding="utf-8"))["obs"]
    can = json.load(open(candidate_path, encoding="utf-8"))["obs"]
    key = lambda k: tuple(k.split("|"))                        # noqa: E731
    inc = {key(k): tuple(v) for k, v in inc.items()}
    can = {key(k): tuple(v) for k, v in can.items()}
    # Size is carried in the dump but is NOT part of the scored pair; strip it
    # here rather than teaching `key4_delta` about a field it must not use.
    size = {k: v[2] for k, v in inc.items() if len(v) > 2}
    inc = {k: (v[0], v[1]) for k, v in inc.items()}
    can = {k: (v[0], v[1]) for k, v in can.items()}
    folds = sorted({k[1] for k in inc})
    bins = []
    print(f"{'fold':>6} {'channel':>10} {'n':>5} {'delta':>9} {'1-sided lo':>11} "
          f"{'worse':>7}  verdict")
    for fold in folds:
        i = {k: v for k, v in inc.items() if k[1] == fold}
        c = {k: v for k, v in can.items() if k[1] == fold}
        if i.keys() != c.keys():
            print(f"{fold:>6}  POPULATION MOVED — {len(i)} vs {len(c)}")
            continue
        # WIDTH CHANNEL: the candidate's width against the incumbent's centre.
        # A residual IS `log θ − log(centre)`, so holding the incumbent's
        # residual and taking the candidate's width isolates the width exactly,
        # and the remainder of the total is the centre channel.
        width_only = {k: (i[k][0], c[k][1]) for k in i}
        for label, arm in (("width", width_only), ("total", c)):
            r = key4_delta(i, arm, fold)
            lo = r["one_sided_lo"]
            print(f"{fold:>6} {label:>10} {r['n']:>5} {r['cluster_delta']:>+9.4f} "
                  f"{lo:>+11.4f} {r['worse_clusters']:>4}/{r['clusters']}  "
                  f"{'FAILS Key 4' if r['fails'] else 'does not block'}")
        # PER SIZE BIN, because a pooled median can hide a real narrowing in one
        # band: §1.74 measured `sd_for` at 5–15% falling 0.203 → 0.150 under the
        # Type A filter while §1.126 found no pooled narrowing at all (median
        # 0.3439 → 0.3291, mean RISING). Both were quoted as the same claim.
        # THE HOLM FAMILY IS THE FOLDS THAT CAN MOVE. A fold whose fitting
        # record the candidate does not touch is structurally null — 2006 and
        # 2011 under any `TYPE_A_EVENTS` arm, because `theta_record` keys the
        # filter on transitions strictly BEFORE the target and neither fold's
        # record contains one. Padding the family with hypotheses that cannot
        # be false is not conservatism, it is throwing away power: it took the
        # smallest Holm critical from 0.0056 to 0.0031. §1.129.
        if size and abs(key4_delta(i, c, fold)["cluster_delta"]) > _SIGN_EPS:
            for (lo_b, hi_b), name in zip(BINS, _BIN_NAMES):
                sel = [k for k in i if lo_b <= size.get(k, -1) < hi_b]
                if len(sel) < 8:
                    continue
                sub_i = {k: i[k] for k in sel}
                sub_w = {k: (i[k][0], c[k][1]) for k in sel}
                bins.append((fold, name, key4_delta(sub_i, sub_w, fold),
                             _median([i[k][1] for k in sel]),
                             _median([c[k][1] for k in sel])))
    # THE HOLM COLUMN, ranked, because a family of bin tests is not a family of
    # independent ones: they partition the same rows and the folds share a
    # nested record. Holm is valid under arbitrary dependence, which is what
    # that requires. FWER rather than FDR because this is a GATE — a false
    # rejection blocks a good change. **The uncorrected column must never be
    # quoted without this one.** §1.128, §1.129.
    if bins:
        bins.sort(key=lambda b: b[2]["one_sided_p"])
        m = len(bins)
        print(f"\nWIDTH CHANNEL BY SIZE BIN — {m} tests, Holm at alpha=0.05. "
              f"`sd_for` medians are the DIRECT")
        print("  width measurement, so a score delta is never read as a width "
              "movement (§1.129).")
        print(f"{'fold':>6} {'bin':>8} {'n':>4} {'G':>3} {'delta':>9} {'se':>7} "
              f"{'worse':>6} {'p':>8} {'Holm':>8} {'w_inc':>7} {'w_cand':>7}  "
              f"verdict")
        still = True
        for j, (fold, name, r, w_i, w_c) in enumerate(bins):
            crit = 0.05 / (m - j)
            if r["one_sided_p"] > crit:
                still = False
            print(f"{fold:>6} {name:>8} {r['n']:>4} {r['clusters']:>3} "
                  f"{r['cluster_delta']:>+9.4f} {r['se']:>7.4f} "
                  f"{r['worse_clusters']:>3}/{r['clusters']} "
                  f"{r['one_sided_p']:>8.4f} {crit:>8.4f} {w_i:>7.4f} "
                  f"{w_c:>7.4f}  "
                  + ("FAILS (Holm)" if still and r["one_sided_p"] <= crit
                     else "fails uncorrected" if r["one_sided_p"] <= 0.05
                     else ""))
    return 0


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return float("nan") if not n else (
        xs[n // 2] if n % 2 else 0.5 * (xs[n // 2 - 1] + xs[n // 2]))


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump-arm", metavar="PATH")
    ap.add_argument("--compare", nargs=2, metavar=("INCUMBENT", "CANDIDATE"))
    args = ap.parse_args()
    if args.dump_arm:
        return dump_arm(args.dump_arm)
    if args.compare:
        return compare_arms(*args.compare)
    print(report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
