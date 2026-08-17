"""How big each party will be, measured instead of typed.

The model's level layer was a set of hand-written per-party constants —
``theta_mode`` for six parties, ``individual_theta`` for six more, ``f_other``
for everyone else, and ``PLAN_BOUNDS`` clamping the lot. Every one of them was
formed by reading the outcomes it would later be asked to predict, which is
what the backtest's in-sample banner has been reporting. They also disagreed
with the record:

===============  ============  ====================================
constant         hand-typed    measured
===============  ============  ====================================
ANC theta_mode   0.75          0.84 (0.95, 0.86, 0.84, 0.67, 0.76)
DA theta_mode    1.30          1.19
f_other mode     1.30          0.79 — applied to 31 parties
PLAN_BOUNDS ANC  (0.65, 0.90)  excludes the observed 0.95
===============  ============  ====================================

``f_other`` mattered most: it had every minor party *growing* 30% on its way
into a local election when the record says they retain about four fifths.

What this module measures is θ, the national-to-local retention ratio: a
party's share at a local election over its share at the national election
before it. Binned by party size, the record says something specific::

    baseline share    n   median θ   sd(log θ)
    0    – 0.5%      18     0.84       0.72
    0.5% – 2%        17     0.90       0.46
    5%   – 15%        4     0.85       0.25
    15%  – 100%      12     0.93       0.26

**That table was measured on TWO metros, n=51, and its conclusion is wrong.**
It said the centre hardly moves and only the spread does, so size predicts how
uncertain a party is and not how it trends. On eight metros, n=235::

    national size before    n    median θ   geometric mean
    < 0.2%                 75      1.31         1.53
    0.2 - 0.5%             57      1.03         0.98
    0.5 - 2%               44      1.04         0.90
    2 - 10%                18      1.05         0.90
    > 10%                  41      0.94         0.95

Small parties GAIN going into a local election and large ones lose — Reif and
Schmitt's second-order effect, in this archive's own numbers. A single common
centre erases it, and erases it against the parties the model already
under-forecasts: they were being handed the large-party number. ``size_centre``
now fits ``log θ = a + b·log(size)`` and each party shrinks toward the centre
for a party ITS SIZE. The spread still collapses with size as the table always
said, so both terms now depend on it. A small or
unfamiliar party gets a wide interval automatically rather than one typed for
it, and nothing has probability zero — which is what the old triangulars kept
doing to outcomes that had already happened.

Everything here is filtered to transitions strictly before the target, so a
backtest cannot read its own result.

THE SPINE (2026-08-13, MODEL-LOG task #22)
------------------------------------------

θ alone is only half a forecast. It converts a party's last NATIONAL share into
a local one, which is the right spine for a nationally-organised party and the
wrong one for a party whose evidence is local — and until now the model used it
unconditionally. ActionSA is the case that forced this: 18.12% locally in 2021
against 6.22% nationally in 2024, and no θ of its own, so the forecast built it
from the 6.22% and discounted it to about 6%.

There is a second route. A party's previous LOCAL result, moved by the measured
local-to-local retention ρ, estimates the same quantity from different evidence.
Measured over 180 party-city-years across eight metros and three transitions,
neither route dominates — but **which one wins is predictable, and the thing
that predicts it is how much θ evidence the party has**:

    θ evidence (Σ reliability)    n    RMSE(log) national    local    best weight on local
    0     – 2                    60          1.53            0.72            1.00
    2     – 5                    55          0.089           0.24            0.10
    5     – 20                   65          0.20            0.41            0.10

That is not party size wearing a disguise. Within *every* size band the flip
survives: among parties under 0.5% of the vote, those with θ evidence want the
national route (best w 0.00) and those without want the local one (best w 1.00);
the same holds in the 0.5–5% band. Keying the same rule on size instead of
evidence is measurably worse (0.2377 against 0.2358 held out by metro).

So the weight on the local route is ``k / (worth + k)``: all local for a party
whose θ is nothing but the group centre, almost all national for a party with a
long retention record. One parameter, and it is a statement about *evidence*
rather than about which parties are "local" — which matters, because the two
things that sound like they should identify a local party do not (geographic
concentration correlates with the local premium at r = −0.09, and the premium is
no larger at home than away; MODEL-LOG §6).

Held out one metro at a time, refitting both routes without it: pooled
vote-weighted RMSE(log) 0.236 against the national spine's 0.275, a 14% gain.
It wins on four metros of eight by count and on the pooled error because the
wins land where the national route fails worst (Buffalo City 0.320 → 0.111,
Johannesburg 0.559 → 0.480) and the losses where it was already accurate
(Mangaung 0.077 → 0.094).

**Recency is priced by construction, not by a term.** The local result is five
years stale at polling day where the national is two. Each route is corrected by
a ratio fitted over its own gap — ρ over five-year LGE-to-LGE pairs, θ over
roughly two-year NPE-to-LGE ones — and the blend weight was fitted on local
results that were themselves five years stale. Nothing further is owed.

**Rejected: measuring θ in both directions.** MODEL-LOG proposed this as the
partial fix — a local→national pair inverted is nominally the same ratio, and it
would give ActionSA a θ of its own. Measured, it makes the forecast worse:
pooled held-out RMSE(log) 0.292 against forward-only 0.275, and every adaptive
blend built on it is worse than the same blend on forward θ. The reason is
visible in the pairs. A reverse observation divides a local result by a *later*
national one, so a party's secular trend enters with the opposite sign: the PA,
growing, measures 1.90 forward and 0.60 reverse; the ANC, declining, 0.85
forward and 1.05 reverse. The two numbers are not the same quantity, and pooling
them averages a party's trend into its local premium. The blend above solves
ActionSA's case directly and better, so the inversion is not needed for it
either.
"""

from __future__ import annotations

import csv
from collections import defaultdict

import numpy as np

import cityconfig
import parties as P

# There is no "large party" threshold, because the record does not contain one.
# Binning the observations by baseline share gives sd(log theta) of 0.72, 0.46,
# 0.25 and 0.26 from the smallest band to the largest — a smooth decline, not a
# break, with the correlation between log size and |log theta| at -0.37. The
# *centre* barely moves at all (median 0.84 to 0.93 across every band). So size
# predicts how UNCERTAIN a party is, not how it trends, and it does so
# continuously. An earlier version split at 5%, which invented a discontinuity
# and put the difference in the median where it belongs in the spread.
SD_FLOOR, SD_CEILING = 0.15, 1.20

# How many of a party's own observations are worth one group observation. Low,
# because a party has at most three and the group has dozens.
SHRINK = 2.0

# The national share at which one observed ratio is worth half of a large
# party's. Set to the hard cut it replaces, so the same evidence is being
# discounted — continuously, and without denying any party a measured θ.
RELIABILITY_HALF = 0.002

# How much θ evidence a party needs before the national spine is trusted over
# its own last local result. The weight on the LOCAL route is k / (worth + k),
# so at worth = k the two routes are equal. Fitted by leave-one-metro-out over
# 180 party-city-years: the curve is flat between 0.5 and 1.5 (0.2377, 0.2358,
# 0.2387) and degrades either side, so 1.0 is the middle of a plateau rather
# than a point estimate. See the module docstring.
SPINE_K = 1.0


# Every metro with a VD-level archive. The retention record is a national fact
# about how parties behave between election types, not a Johannesburg one, and
# reading it off eight cities instead of two is what makes ρ measurable at all:
# two metros give four LGE-to-LGE pairs, eight give sixteen. Nothing here is
# ever read at or after the target, so a wider evidence base is more evidence,
# not more leakage. A city whose archive does not go back simply contributes
# nothing — _citywide returns empty on a missing file.
METRO_CODES = ("JHB", "TSH", "CPT", "ETH", "EKU", "MAN", "NMA", "BUF")

def _citywide(path) -> dict[str, float]:
    """One election's citywide PR shares. **Deliberately not cached.**

    Widening the record from two metros to eight multiplied the file reads, and
    a path-keyed memo is the obvious fix. It was written, and it broke
    ``test_the_level_prior_reads_no_election_at_or_after_its_target`` — the
    guard that spies on file opens to prove the θ record never touches an
    election at or after its target. A memo makes the second target's reads
    invisible to it, so the leak test passes by seeing nothing rather than by
    seeing only clean files.

    That trade is the wrong way round in this repository. The temporal guards
    are the reason any score here can be believed, and the cost being bought
    with them is a few seconds of CSV parsing per run.
    """
    counts: dict[str, int] = defaultdict(int)
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                if row.get("BallotType") in (None, "", "PR"):
                    counts[P.canonical(row["sPartyName"])] += int(
                        float(row.get("Party_Votes") or 0))
    except FileNotFoundError:
        return {}
    total = sum(counts.values())
    return {k: v / total for k, v in counts.items()} if total else {}


def theta_record(target: cityconfig.Target,
                 codes=METRO_CODES) -> dict[str, list[tuple[float, float]]]:
    """Every observed national-to-local retention ratio before the target.

    One entry per party per metro per transition, as ``(ratio, share)`` where
    ``share`` is the national share the ratio was measured off.

    **There is no minimum share.** Parties below 0.2% of the national vote used
    to be dropped here, on the grounds that a party going from 30 votes to 90
    is not evidence that parties triple. That reasoning is right about the
    NUMBER and wrong about the PARTY: dropping it did not stop the model
    forming a view of that party, it just meant the view came from a constant
    somebody typed instead of from the party's own record. A hard cut also has
    a cliff at 0.2% that nothing in the data puts there.

    So every party with any history at all keeps its ratios, and ``share``
    travels with them so :func:`theta_prior` can weight by how much the ratio
    is worth. A party measured off 0.02% of the vote lands on the group centre
    because its own observations carry almost no weight — which is what the
    cut was reaching for, without the cliff and without handing the party to a
    judgement.
    """
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    out: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for year in lge:
        if int(year) >= int(target.year):
            continue                      # strictly before the target
        npe = cityconfig.preceding(year, "NPE")
        if not npe:
            continue
        for code in codes:
            before = _citywide(f"data/raw/elections/npe{npe}_{code}_vd_party.csv")
            after = _citywide(
                f"data/raw/elections/lge{year}_{code}_vd_party_clean.csv")
            for party in set(before) & set(after):
                if before[party] > 0:
                    out[party].append((after[party] / before[party],
                                       before[party]))
    return dict(out)


def local_record(target: cityconfig.Target,
                 codes=METRO_CODES) -> dict[str, list[tuple[float, float]]]:
    """Every observed LOCAL-to-LOCAL retention ratio before the target.

    ρ is θ's opposite number: a party's share at one local election over its
    share at the local election before it, as ``(ratio, share)`` where ``share``
    is the earlier local share the ratio was measured off. It is what moves a
    party's *own* last local result forward five years, and it is the second of
    the two routes :func:`spine` weighs against each other.

    Consecutive LGE pairs only, both strictly before the target — pairing 2011
    with 2021 would measure ten years of drift and call it five.
    """
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    out: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for earlier, later in zip(lge, lge[1:]):
        if int(later) >= int(target.year):
            continue                      # strictly before the target
        for code in codes:
            before = _citywide(
                f"data/raw/elections/lge{earlier}_{code}_vd_party_clean.csv")
            after = _citywide(
                f"data/raw/elections/lge{later}_{code}_vd_party_clean.csv")
            for party in set(before) & set(after):
                if before[party] > 0:
                    out[party].append((after[party] / before[party],
                                       before[party]))
    return dict(out)


def _reliability(share: float) -> float:
    """How much one observed ratio is worth, on 0-1, from what it was measured off.

    ``share / (share + RELIABILITY_HALF)``: an observation taken off the old
    0.2% cut is worth half of one taken off a large party, 2% is worth 0.91,
    0.02% is worth 0.09. Continuous, so nothing changes character at a
    threshold, and monotone in the only thing that governs the noise — how
    many votes the ratio was computed from.
    """
    return float(share) / (float(share) + RELIABILITY_HALF)


def theta_prior(target: cityconfig.Target, baseline: dict[str, float],
                codes=METRO_CODES) -> tuple[dict[str, tuple], dict]:
    """Per-party (low, mode, high) on θ, and the groups they were drawn from.

    A party's own log-mean is shrunk toward its group's by ``n / (n + SHRINK)``,
    and the width comes from the group's log-spread. The band is the 10th to
    90th percentile of that lognormal, so it is wide where the record is wide
    and nothing sits at probability zero.
    """
    record = theta_record(target, codes)
    if not record:
        return {}, {}

    # One common centre: the record says the trend does not vary with size.
    # Weighted by what each observation is worth, which is what replaced the
    # 0.2% cut — an unweighted mean over every ratio would let a party that
    # went from 30 votes to 90 move the centre as far as the ANC does.
    everything = [obs for ratios in record.values() for obs in ratios]
    ratios_all = np.array([r for r, _ in everything])
    weights_all = np.array([_reliability(s) for _, s in everything])
    if weights_all.sum() <= 0:
        return {}, {}
    mu_all = float(np.average(np.log(ratios_all), weights=weights_all))

    # Dispersion IS a function of size, so fit it as one — against the COMMON
    # centre, not each party's own. Two earlier attempts used within-party
    # deviation and both came out too narrow (sd 0.15 for a large party where
    # the binned record shows 0.26), because with two or three observations a
    # party's own mean sits almost on top of them. What a forecast faces is the
    # total spread: we do not know a party's centre either, and the shrinkage
    # above leans on the common one. Erring wide is also the right way to be
    # wrong here — this model's measured failure has always been overconfidence.
    xs, ys = [], []
    for party, ratios in record.items():
        size = baseline.get(party, 0.0)
        if size <= 0:
            continue
        for r, _share in ratios:
            xs.append(np.log(size))
            ys.append((np.log(r) - mu_all) ** 2)
    if len(xs) >= 6:
        slope, intercept = np.polyfit(xs, np.log(np.maximum(ys, 1e-6)), 1)

        def sd_for(size: float) -> float:
            x = np.log(max(size, 1e-5))
            return float(np.clip(np.exp(0.5 * (intercept + slope * x)),
                                 SD_FLOOR, SD_CEILING))
    else:
        pooled = float(np.std(np.log(ratios_all), ddof=1))

        def sd_for(size: float) -> float:
            return float(np.clip(pooled, SD_FLOOR, SD_CEILING))

    # PATH ONE — a party WITH history. Its own log-mean, shrunk toward the
    # common centre by how much that history is worth rather than by how many
    # rows of it there are: three ratios measured off 0.02% of the vote are
    # three weak statements, not three strong ones, and the party ends up on
    # the group centre. A party with no ratios of its own but a baseline to
    # apply θ to (MK in 2026 — a national vote, no local election yet) IS this
    # path, sitting at the centre with the group's spread.
    #
    # PATH TWO — a party with NO baseline at all is not here and cannot be:
    # θ converts a national share into a local one and there is no national
    # share to convert. It is an arrival, and ``pools.arrival_rules`` sizes it
    # from the arrival record. ``montecarlo.blended_centres`` routes it there.
    priors: dict[str, tuple] = {}
    for party in set(record) | set(baseline):
        size = baseline.get(party, 0.0)
        sd = sd_for(size)
        own = record.get(party, [])
        if own:
            worth = sum(_reliability(s) for _, s in own)
            weight = worth / (worth + SHRINK)
            own_mu = float(np.average([np.log(r) for r, _ in own],
                                      weights=[_reliability(s) for _, s in own]))
            mu = weight * own_mu + (1 - weight) * mu_all
        else:
            mu = mu_all
        priors[party] = (float(np.exp(mu - 1.2816 * sd)), float(np.exp(mu)),
                         float(np.exp(mu + 1.2816 * sd)))
    return priors, {
        "centre": {"n": len(everything), "median": float(np.exp(mu_all)),
                   "effective_n": float(weights_all.sum())},
        "spread": {"at_0.1%": sd_for(0.001), "at_1%": sd_for(0.01),
                   "at_10%": sd_for(0.10), "at_40%": sd_for(0.40)},
        # What each party's own θ record is WORTH, on the same 0-1-per-
        # observation scale the shrinkage uses. This is the quantity the spine
        # blend is keyed on, and it is reported rather than recomputed so the
        # weight and the shrinkage can never be keyed on different numbers.
        "worth": {party: float(sum(_reliability(s) for _, s in obs))
                  for party, obs in record.items()},
        # Per-party log-spread, so the draw can use the width that was measured
        # instead of a triangular fitted to the same band's endpoints.
        "sd": {party: float(sd_for(baseline.get(party, 0.0)))
               for party in priors},
    }


def size_centre(record: dict[str, list[tuple[float, float]]]):
    """The centre θ shrinks TOWARD, as a function of how big the party is.

    ``levels.py`` has said since it was written that "size predicts how
    UNCERTAIN a party is, not how it trends — the centre hardly moves (0.84 to
    0.93 across every band)". That was measured on TWO metros, n=51. On eight
    metros, n=235, it is not true::

        national size before    n    median θ   geometric mean
        < 0.2%                 75      1.31         1.53
        0.2 - 0.5%             57      1.03         0.98
        0.5 - 2%               44      1.04         0.90
        2 - 10%                18      1.05         0.90
        > 10%                  41      0.94         0.95

    Small parties GAIN going into a local election and large ones lose, which is
    Reif and Schmitt's second-order effect stated in this archive's own numbers,
    and which a single common centre erases. The model was applying 0.83 to 0.96
    to every party at once, so the parties it under-forecasts most were being
    handed the large-party number.

    Fitted as ``log θ = a + b·log(size)`` on the same reliability weights the
    shrinkage uses — correlation −0.27, and a gradient from about 1.10 at a
    twentieth of a per cent to 0.89 at thirty. The R² is 0.04, which is the
    honest figure: this moves the CENTRE by a quarter across the ballot and
    explains almost none of the variance around it. Both facts matter, and the
    second is why the dispersion stays where it is.

    Returns ``(a, b)``; ``centre(size) = exp(a + b·log(size))``.
    """
    obs = [(np.log(max(sz, 1e-6)), np.log(r), _reliability(sz))
           for v in record.values() for r, sz in v if r > 0 and sz > 0]
    if len(obs) < 20:
        return None
    x = np.array([o[0] for o in obs])
    y = np.array([o[1] for o in obs])
    w = np.sqrt(np.array([o[2] for o in obs]))
    # UNWEIGHTED. The reliability weight exists to stop a party that went from
    # 30 votes to 90 moving a party's OWN mean, and it is right for that. Here
    # it is wrong: the quantity being fitted is how the centre varies WITH SIZE,
    # and down-weighting the small end removes the observations that identify
    # it. Weighted, the gradient runs 1.10 to 0.89; unweighted, 1.31 to 0.94,
    # which is what the size bands actually show.
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def _shrunk(record: dict[str, list[tuple[float, float]]],
            ) -> tuple[dict[str, float], float, dict[str, float]]:
    """Per-party log-mean shrunk to the weighted common centre, and the worth.

    The estimator :func:`theta_prior` uses on θ, extracted so ρ gets exactly the
    same treatment. If the two routes were shrunk differently, the comparison
    between them in :func:`spine` would be measuring the estimators rather than
    the evidence.
    """
    everything = [obs for obs in (o for v in record.values() for o in v)]
    if not everything:
        return {}, 0.0, {}
    ratios = np.array([r for r, _ in everything])
    weights = np.array([_reliability(s) for _, s in everything])
    if weights.sum() <= 0:
        return {}, 0.0, {}
    mu_all = float(np.average(np.log(ratios), weights=weights))
    fit = size_centre(record)
    mus: dict[str, float] = {}
    worth: dict[str, float] = {}
    for party, obs in record.items():
        w = [_reliability(s) for _, s in obs]
        worth[party] = float(sum(w))
        weight = worth[party] / (worth[party] + SHRINK)
        own = float(np.average([np.log(r) for r, _ in obs], weights=w))
        # Shrink toward the centre for a party THIS SIZE, not toward one number
        # for the whole ballot. See size_centre: the size of the party is the
        # single thing that moves the centre, and a party with little history of
        # its own is almost entirely this term.
        size = float(np.average([sz for _, sz in obs], weights=w))
        target = (fit[0] + fit[1] * np.log(max(size, 1e-6))) if fit else mu_all
        mus[party] = weight * own + (1 - weight) * target
    return mus, mu_all, worth


def spine(target: cityconfig.Target, baseline: dict[str, float],
          prev_local: dict[str, float], codes=METRO_CODES,
          k: float | None = None) -> tuple[dict[str, float], dict]:
    """Each party's central level at the target, from BOTH of its records.

    ``baseline`` is the preceding national election's citywide shares;
    ``prev_local`` the preceding local election's. Returns the blended central
    share per party and a diagnostic block naming, for every party, which route
    it came from and why — because the whole point of task #22 is that the model
    could not previously say.

    Three cases, and every party is in exactly one:

    * **Both records.** The blend, weighted ``k / (worth + k)`` toward the local
      route, where ``worth`` is what the party's own θ record is worth. A party
      with a long retention history sits on the national spine; a party whose θ
      is nothing but the group centre sits on its own last local result.
    * **National only.** A party facing its first local election — MK in 2026.
      Weight 0: there is no local result to blend, and inventing one from the
      group would be worse than using the national route the party does have.
    * **Local only.** A party that contested locally and then did not contest
      nationally, or was not yet national when it did. Weight 1 by necessity.

    A party with neither is an arrival and is not here at all;
    ``pools.arrival_rules`` sizes it from the arrival record.
    """
    # RESOLVED AT CALL TIME. `k: float = SPINE_K` would freeze the constant at
    # import, so setting `levels.SPINE_K` afterwards would change nothing and a
    # sweep of it would return identical rows — the trap ITERATING.md rule 6
    # exists for, and the one `montecarlo.LEVEL_DF` was actually in until
    # 2026-08-17. See MODEL-LOG §1.33.
    k = SPINE_K if k is None else float(k)
    theta_obs = theta_record(target, codes)
    rho_obs = local_record(target, codes)
    mu_t, c_t, worth_t = _shrunk(theta_obs)
    mu_r, c_r, _worth_r = _shrunk(rho_obs)
    if not mu_t and not mu_r:
        return {}, {}

    levels: dict[str, float] = {}
    detail: dict[str, dict] = {}
    for party in set(baseline) | set(prev_local):
        national = float(baseline.get(party, 0.0))
        local = float(prev_local.get(party, 0.0))
        worth = float(worth_t.get(party, 0.0))
        nat_level = national * float(np.exp(mu_t.get(party, c_t))) if national > 0 else 0.0
        loc_level = local * float(np.exp(mu_r.get(party, c_r))) if local > 0 else 0.0
        if national > 0 and local > 0:
            w = k / (worth + k)
            level = float(np.exp(w * np.log(loc_level) + (1 - w) * np.log(nat_level)))
            route = "blend"
        elif national > 0:
            w, level, route = 0.0, nat_level, "national only (first local election)"
        elif local > 0:
            w, level, route = 1.0, loc_level, "local only (no national record)"
        else:
            continue
        levels[party] = level
        detail[party] = {"w_local": w, "worth": worth, "route": route,
                         "national": nat_level, "local": loc_level}
    return levels, {
        "k": k,
        "n_theta": sum(len(v) for v in theta_obs.values()),
        "n_rho": sum(len(v) for v in rho_obs.values()),
        "theta_centre": float(np.exp(c_t)), "rho_centre": float(np.exp(c_r)),
        "detail": detail,
    }


def ward_pr_ratios(target: cityconfig.Target, city: cityconfig.City,
                   ) -> tuple[dict[str, float], float]:
    """Each party's ward-ballot share over its PR share, from the last LGE.

    Replaces the hand-set overrides (``MK 0.80`` "bounded by ActionSA's
    observed 0.77", ``ENTRANT 0.80``). A party with no ward history gets the
    median of those that have one, which is a rule rather than a per-party
    number and applies to whoever turns up next.
    """
    year = target.previous_lge
    template = cityconfig.CALENDAR[year].results if year else None
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        return {}, 0.8
    pr: dict[str, int] = defaultdict(int)
    ward: dict[str, int] = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            party = P.canonical(row["sPartyName"])
            votes = int(float(row.get("Party_Votes") or 0))
            (ward if row.get("BallotType") == "Ward" else pr)[party] += votes
    pr_total, ward_total = sum(pr.values()), sum(ward.values())
    if not pr_total or not ward_total:
        return {}, 0.8
    ratios = {p: (ward[p] / ward_total) / (pr[p] / pr_total)
              for p in set(pr) & set(ward) if pr[p] > 0}
    fallback = float(np.median(list(ratios.values()))) if ratios else 0.8
    return ratios, fallback


def contestation(target: cityconfig.Target, city: cityconfig.City,
                 ) -> dict[str, float]:
    """The fraction of wards each party fields a ward candidate in.

    Nomination lists close and are published before polling day, so this is
    available to a forecaster. It replaces ``pa_contestation_uplift`` — a
    one-party constant of 1.25 that existed because the PA contested 52 of 135
    wards in 2021 and the model assumed every party contested all of them. The
    same correction is owed to every party, and measured rather than chosen:
    the median party contests well under half the wards.

    **Presence on the ballot, never a vote.** The justification above is a
    statement about nomination lists, and the code used to count a ward only
    where the party had ``Party_Votes > 0`` — which is not who stood, it is
    who scored, and it is exactly the outcome a backtest is meant to be
    predicting. The IEC publishes a row per party per voting district *where
    that party is on the ballot* (20 to 34 parties per VD in Johannesburg
    2021, not a cross-product of every party), so the row's existence is the
    nomination fact and reading it does not touch the result. It matters most
    where the model is weakest: Royal Loyal Progress stood in all 135 wards
    and scored in 79, so the old rule called a full slate 59% of a slate, and
    contestation multiplies through to an arrival's size.
    """
    template = cityconfig.CALENDAR[target.year].results
    path = city.path("raw", "elections", template) if template else None
    if not path or not path.exists():
        return {}
    wards: dict[str, set] = defaultdict(set)
    seen: set = set()
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            if row.get("BallotType") != "Ward":
                continue
            ward = (row.get("Ward") or "").strip()
            if not ward:
                continue
            seen.add(ward)
            wards[P.canonical(row["sPartyName"])].add(ward)
    n = len(seen)
    return {p: len(w) / n for p, w in wards.items()} if n else {}
