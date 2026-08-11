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

The centre hardly moves. The spread collapses. So **size predicts how uncertain
a party is, not how it trends** — and it does so smoothly, with no threshold
anywhere (the correlation between log size and |log θ| is -0.37). A party's
prior is therefore one common centre, shrunk toward its own history where it
has any, with a width read off a fitted size-dispersion line. A small or
unfamiliar party gets a wide interval automatically rather than one typed for
it, and nothing has probability zero — which is what the old triangulars kept
doing to outcomes that had already happened.

Everything here is filtered to transitions strictly before the target, so a
backtest cannot read its own result.
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


def _citywide(path) -> dict[str, float]:
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
                 codes=("JHB", "TSH")) -> dict[str, list[tuple[float, float]]]:
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
                codes=("JHB", "TSH")) -> tuple[dict[str, tuple], dict]:
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
