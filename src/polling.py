"""Polls, filtered by date and converted from national numbers to metro ones.

A party with no electoral history cannot be forecast from a record it does not
have. Scored across nine city-years, this model gives a median seat to ONE of
the thirty-two parties that arrived from nothing and won one (``src/arrivals.py``),
14 seats against 130 — and no tuning of the arrival machinery reaches the gap,
because the machinery is extrapolating from splits that were an order of
magnitude smaller. Polls are the only pre-election evidence that exists for such
a party, which is the literature's unanimous position and this repository's own
measurement.

THE OBSTACLE, AND THE ARITHMETIC THAT REMOVES IT
------------------------------------------------

Published South African polls are NATIONAL and this model forecasts a metro. The
conversion is not a modelling assumption, it is arithmetic on two public facts.

If a party takes ``X`` of a territory's vote but stands only in municipalities
holding share ``s`` of that territory, then its average share **where it stands**
is ``X / s``. The poll supplies ``X``; nomination lists — which close weeks
before polling day — supply which municipalities, and the published roll supplies
their size. Nothing here is read from the result.

Measured against every arrival in the eight-metro archive, as the median
absolute log ratio between estimate and actual metro share::

                         raw national share    contested-area adjusted
    2016 (83 arrivals)            1.609                 0.000
    2021 (175 arrivals)           1.228                 0.144

**Reproduced 2026-08-22 by `src/contested_area.py`, which did not exist when
this table was written. Every figure is right and the table still oversells
what it shows** — read that module, or MODEL-LOG §1.66. Three corrections:

* A party standing in ONE metro has an estimate that is exact BY IDENTITY, and
  contributes a hard zero. That is 55% of the 2016 arrivals and 38% of the 2021
  ones, so the 0.000 is a tautology and the 0.144 is half built from the same
  material. **On multi-metro arrivals — the only cases where the conversion does
  any work — it is 0.234 and 0.431**, a factor of 1.54 at 2021.
* The two columns use DIFFERENT DENOMINATORS: "raw" is the party's share of the
  eight-metro aggregate, the adjusted column runs through the national one.
  Against a consistent national denominator raw is 2.504 and 1.995. So part of
  the improvement shown is a change of denominator.
* **It does not test the conversion it appears to.** Here ``X`` is rebuilt from
  the archive, so the national figure CANCELS and the estimate reduces to the
  party's share of its own contested area. The poll never appears and neither
  does ``NATIONAL_VOTES``. This validates the geographic half of the mechanism,
  not the conversion half.

What validates the production behaviour is MODEL-LOG §1.65: with the real Ipsos
2021 poll driving the real path, this channel is worth **48 coherent seats**
across nine city-years. Quote that. This table is the weaker companion.

WHAT IT DOES AND DOES NOT BUY
-----------------------------

Feeding the one independent pre-2021 poll — Ipsos, 16-20 August 2021, ActionSA at
1.5% national — the conversion gives about 6.3% wherever ActionSA stood::

    metro           poll + conversion    model (no poll)    actual
    Johannesburg           6.3%               6.4%          18.12%
    Tshwane                6.3%               1.5%           9.28%
    Ekurhuleni             6.3%               1.5%           7.36%
    eThekwini              6.3%               1.5%           2.35%

Better in two metros, far better in one, worse in one. **Nothing available would
have called Johannesburg**, and this does not pretend to: the conversion yields
the average where a party stands, and distributing it between metros still needs
the home-city effect. What it removes is the model's silence in the metros where
it currently says 1.5% and the answer was seven or nine.

TWO RULES ABOUT WHICH POLLS COUNT
---------------------------------

**Fieldwork dates are machine-readable and enforced.** A poll may only inform a
target if its fieldwork ENDED before that target's polling day. The register
previously stored dates as free text ("8-31 July 2026"), which no backtest can
filter on — a temporal leak waiting to happen in a repository that has spent
weeks removing them.

**Party-commissioned polls are excluded**, and the evidence is in the same
election. ActionSA commissioned a poll reporting it "on course to win Joburg";
it finished third on 16.05%. The one independent poll had the party low by a
factor of 1.6. Admitting the first and excluding the second would have been
worse than having no poll at all.
"""

from __future__ import annotations

import os as _os

import json
import math
from dataclasses import dataclass
from datetime import date

import numpy as np
from pathlib import Path

import cityconfig

REGISTER = Path("polls.json")

# A METRO POLL'S TOTAL ERROR, in points, measured rather than taken from the
# sampling formula. Nominal margin of error is the smaller half of the problem:
# it prices sampling and nothing else — not the likely-voter screen, not house
# effects, not late movement. Ipsos's three metro polls at 2016 (Johannesburg,
# Tshwane, Nelson Mandela Bay; ANC, DA and EFF in each) missed by
#
#     1.4  2.6  3.1   5.8  0.1  2.7   3.9  2.7  0.9
#
# giving an RMS of 3.03pp against a nominal margin nearer 1.5. So 3.0 is the
# number a forecaster should carry, and it is a TRACK RECORD rather than a
# formula — the standard the pollster brief asks for.
POLL_RMS_ERROR = 0.030

# ---------------------------------------------------------------------------
# σ_poll AS A DECOMPOSITION (2026-08-22). The flat 3.0pp above is retained as
# the CALIBRATION TARGET and is no longer the live weight.
# ---------------------------------------------------------------------------
#
# Why it had to change: `n` was recorded on every poll and read by nothing, so a
# 504-person subsample of one house counted exactly as much as a full-sample
# metro poll — and there was no cap, so ten waves of that one house would each
# blend at w≈0.9 and the forecast would simply become the poll. Both admitted
# 2026 polls are the same house.
#
#     σ_poll² = deff·p̂(1−p̂)/n  +  σ_house²  +  σ_screen²  +  (drift·√days)²
#
# THE POINT OF THE DECOMPOSITION IS THAT IT PRESERVES THE MEASUREMENT rather
# than discarding it. Removing the sampling component from the 3.03pp track
# record leaves the non-sampling residual, and that residual is what
# `POLL_HOUSE_SD` is. Computed on the nine readings' own shares:
#
#     n        mean sampling      residual
#     500        2.13pp            2.16pp
#     800        1.68pp            2.52pp
#     1500       1.23pp            2.77pp
#
# Ipsos never published the metro cut sizes, so n is declared — but the residual
# moves only from 2.2 to 2.8pp across a threefold range of it, which is why
# 0.025 can be carried as measured rather than chosen.
#
# **SCREEN AND DRIFT ARE EXCESS TERMS, NOT ADDITIONS.** This is the trap in the
# arithmetic. The 2.5pp residual is the TOTAL non-sampling error of those Ipsos
# readings, and they were taken two days before polling day by a house whose
# method is on the record — so their screen error and their drift are already
# inside it. Adding a screen term and a drift term to every poll on top would
# charge each poll twice. So both are measured as an EXCESS over that reference
# case: zero for a poll with a disclosed screen, zero at zero days out, and
# positive only for a poll that differs from the calibration poll.
#
# The self-consistency check, which `tests/test_polling_sd.py` asserts: run the
# calibration polls back through the decomposition and it must return 3.03pp.
POLL_RMS_ERROR_2016 = 0.0303      # MEASURED — RMS of the nine 2016 readings
POLL_CAL_N_2016 = 800             # DECLARED — Ipsos published no metro cut size
POLL_CAL_DEFF_2016 = 1.3          # DECLARED — RDD panel, registered voters
POLL_HOUSE_SD = 0.025             # MEASURED, conditional on the two above

# A SUBSAMPLE IS NOT A POLL. A ~500-person metro cut of a national sample
# carries the parent design effect — its weights were built for the national
# population and the metro is a slice of the clusters, not a fresh design. The
# recorded `n` therefore overstates the information: `effective_n = n / deff`.
# Both are DECLARED, and both become measurable the day a house publishes its
# effective base.
POLL_DEFF_SUBSAMPLE = 1.6         # DECLARED — a metro cut of a national sample
POLL_DEFF_STANDALONE = 1.2        # DECLARED — a purpose-designed metro sample

# EXCESS error from a likely-voter screen nobody can see. Zero when the screen
# is published, because the calibration poll's screen error is already inside
# POLL_HOUSE_SD. DECLARED; measurable from a within-house LV-vs-RV delta if a
# house ever publishes both.
POLL_SCREEN_SD_UNDISCLOSED = 0.020

# EXCESS error from opinion moving between fieldwork and polling day, as a
# random walk: σ = rate·√days. Zero at zero days, which is where the calibration
# poll sits. 0.0010 gives about 1.0pp over the 96 days from the July 2026 wave.
# DECLARED, and fittable from three waves of two houses over the campaign —
# pre-register that fit before running it.
POLL_DRIFT_PP_PER_ROOT_DAY = 0.0010

# HOW MANY INDEPENDENT HOUSES IT TAKES BEFORE A POLL IS TRUSTED IN FULL.
# Inverse variance is only correct if both estimates are UNBIASED, and a single
# DA-adjacent house with an undisclosed screen is exactly the case where the
# bias term is unbounded and no variance formula can express it. So the poll's
# weight is capped by house diversity:
#
#     w_cap(H) = H / (H + POLL_HOUSE_K)     1 → 0.50   2 → 0.67   3 → 0.75
#
# the same m/(k+m) shape the spine and POLL_K already use, and the asymptote is
# 1.0 by argument rather than by a constant — with enough independent houses,
# inverse variance is the right answer and no cap is wanted.
#
# **WHY 1.0 AND NOT SOMETHING ELSE.** At K = 1.0 the cap at one house is exactly
# one half, and that is a rule which can be stated in a sentence: *a single
# unreplicated house is never worth more than the model itself.* It is also the
# value `SPINE_K` and `POLL_K` already carry, so it is the repository's existing
# answer to "how much evidence before a competing estimate is trusted in full".
#
# It shipped at 1.4 for one day, which put the cap at 0.42 for no stated reason
# — a number chosen rather than argued, which is the thing this register exists
# to catch. The difference is not cosmetic: at 1.4 the cap overrode the variance
# arithmetic for the ANC as well as the DA, pulling both to 0.42 when precision
# alone said 0.498 and 0.560. At 1.0 it binds only where a poll would otherwise
# outweigh the model, which is the condition a cap should exist for.
#
# A tighter cap is available and is deliberately NOT taken. We have independent
# reason to think this particular house leans one way, but encoding a view about
# one house in a global constant is the party-specific fiddle this project has
# deleted twice. If a house needs discounting, discount that house explicitly.
#
# DECLARED. What would set it: with two or more houses in a wave the cross-house
# sd is directly estimable, and POLL_HOUSE_K follows from equating the cap to
# the inverse-variance weight computed with that measured sd. One backtest
# city-year cannot set it, and a sweep over n=1 is not a measurement.
# ---------------------------------------------------------------------------
# THE REPLACEMENT sigma, PRE-REGISTERED IN MODEL-LOG §1.87 AND OFF BY DEFAULT.
#
#     SIGMA_TWO_TERM=1 .venv/bin/python src/compare_history.py
#
# With the switch unset nothing below is read and no number moves.
#
# WHY. The four-component form cannot be identified — Dominitz & Manski, JASA
# 121(553) 2025, put a Total Margin of Error at 49.3pp with no assumption about
# non-respondents — and, worse, our version divides the COMMON component by the
# number of houses, so sigma runs 4.01pp -> 0.40pp from one house to a hundred.
# Jackman (2005), Shirani-Mehr et al. (2018) and The Economist's production code
# all say the shared component never shrinks. Shirani-Mehr's own model uses two
# terms, not four.
#
# Every constant here is taken from OUTSIDE this repository, which is the point:
# `POLL_HOUSE_SD` was a residual of the same nine 2016 readings that are also the
# only metro-poll test cases the backtest has.
SIGMA_COMMON = 0.015              # DECLARED, sourced — industry-common bias that
                                  # NEVER shrinks with more houses. Finland 1.25pp,
                                  # The Economist 1.30pp, Selb et al. (POQ 2023,
                                  # 5,240 German polls) 1.5pp mean absolute bias,
                                  # SA 2024 1.66pp.
SIGMA_IDIO = 0.015                # DECLARED, sourced — the house-specific part,
                                  # the ONLY term h_eff may divide. Stoetzer prior
                                  # N(0,1); Bon et al. ~1.0; Jackman phone-only
                                  # 1-3; SA 2024 1.71pp.
SIGMA_DRIFT_PER_ROOT_DAY = 0.0030 # DECLARED, sourced — band 0.20 (Ellis NZ,
                                  # ESTIMATED in a state-space model) to 0.41
                                  # (derived from Jennings & Wlezien's 4/3/<2pp
                                  # horizon profile). The shipped 0.0010 is 2-4x
                                  # too small.
SIGMA_VOLATILITY = 0.008          # DECLARED, sourced — +0.1pp per 1pp of average
                                  # party swing. South Africa's swings are large.

SIGMA_TWO_TERM = _os.environ.get(
    "SIGMA_TWO_TERM", "").lower() in ("1", "true", "yes")

POLL_HOUSE_K = 1.0                # DECLARED

# Below this an entry is recorded and never admitted. It exists because readers
# will supply polls to the competition, and it is the floor that stops a
# three-person "poll" being priced as evidence at all.
POLL_MIN_N = 300                  # DECLARED

# RECENCY HALF-LIFE for combining several waves. **It was registered in
# JUDGEMENT-CALLS.md at 120 and did not exist** — it was a default argument on
# `aggregate`, so nothing could reach it from `--set` or a config file and the
# register documented a constant that was not there. `DEFAULTS` mirrors it and
# the two are asserted equal at import, the TURNOUT_CORRELATION pattern.
POLL_HALF_LIFE_DAYS = 120.0       # DECLARED — no SA metro series can fit it

# Two copies of one number is this repository's most reliable defect, so the
# scenario key and the module constant are checked against each other rather
# than trusted. `montecarlo` imports `polling`, not the other way round, so
# the assertion lives there — see DEFAULTS["poll_half_life_days"].

# How long before polling day a poll may still be describing the same election,
# when it does not say which one it was taken for. Eighteen months covers a
# local-election campaign and the registration weekends either side of it, and
# excludes the previous cycle outright.
CAMPAIGN_WINDOW_DAYS = 550


def _end(poll: dict) -> date | None:
    """A poll's fieldwork end as a date, or None. One parser, used everywhere."""
    raw = poll.get("fieldwork_end")
    if not raw:
        return None
    try:
        return date.fromisoformat(str(raw))
    except (TypeError, ValueError):
        return None


def _recency_weights(polls: list[dict], *,
                     half_life_days: float | None = None,
                     asof: date | None = None) -> list[float]:
    """``exp(-age/tau)`` per poll, tau from the half-life. Undated polls get 0.

    Factored out of :func:`aggregate` so the aggregate and
    :func:`effective_houses` cannot weight the same polls differently — two
    copies of one calculation is this repository's most reliable defect.
    """
    half_life_days = (POLL_HALF_LIFE_DAYS if half_life_days is None
                      else half_life_days)
    ends = [_end(p) for p in polls]
    dated = [e for e in ends if e is not None]
    if not dated:
        return [0.0] * len(polls)
    when = asof or max(dated)
    tau = float(half_life_days) / math.log(2.0)
    return [0.0 if e is None else math.exp(-max((when - e).days, 0) / tau)
            for e in ends]


def design_effect(poll: dict, *,
                  deff_subsample: float | None = None,
                  deff_standalone: float | None = None) -> float:
    """How much of the recorded ``n`` is real information.

    An explicit ``deff`` published by the house wins. Otherwise it is decided by
    ``n_basis``: a metro cut of a national sample carries the parent design's
    weighting loss and clustering, a purpose-built metro sample much less. See
    the constants.
    """
    if poll.get("deff"):
        return max(float(poll["deff"]), 1.0)
    basis = str(poll.get("n_basis") or "").lower()
    if basis in ("standalone", "metro", "metro-standalone"):
        return float(deff_standalone if deff_standalone is not None
                     else POLL_DEFF_STANDALONE)
    return float(deff_subsample if deff_subsample is not None
                 else POLL_DEFF_SUBSAMPLE)          # the cautious default


def effective_n(poll: dict, **kw) -> float | None:
    """``n / deff`` — the sample size that is actually doing work.

    The July 2026 SRF wave records n = 504 and its own ``caveat`` claims a
    margin of ±4.4pp. At a subsample design effect of 1.6 the effective base is
    **315** and the margin is ±5.5pp. That is the difference between a caveat
    someone typed and a number in the pipeline.
    """
    n = poll.get("n")
    if not n:
        return None
    return float(n) / design_effect(poll, **kw)


def _days_out(poll: dict, asof: date | None) -> float:
    """Days between this poll's fieldwork ending and ``asof``. Never negative."""
    end = _end(poll)
    if end is None or asof is None:
        return 0.0
    return max((asof - end).days, 0)


def poll_sd(poll: dict, share: float, *, asof: date | None = None,
            screen_sd: float | None = None, drift_rate: float | None = None,
            **kw) -> float:
    """Total error on one poll's reading of one party, in share units.

    The four components of the module's decomposition. ``share`` is that party's
    polled share, because sampling error depends on where in [0,1] it sits.
    Screen and drift are EXCESS over the calibration case — see the constants,
    and do not add them unconditionally.
    """
    n_eff = effective_n(poll, **kw)
    p = min(max(float(share), 1e-4), 1 - 1e-4)
    sampling = math.sqrt(p * (1 - p) / n_eff) if n_eff else POLL_HOUSE_SD
    screen = (0.0 if poll.get("screen_disclosed")
              else float(screen_sd if screen_sd is not None
                         else POLL_SCREEN_SD_UNDISCLOSED))
    drift = (float(drift_rate if drift_rate is not None
                   else POLL_DRIFT_PP_PER_ROOT_DAY)
             * math.sqrt(_days_out(poll, asof)))
    return math.sqrt(sampling ** 2 + POLL_HOUSE_SD ** 2
                     + screen ** 2 + drift ** 2)


def sd_components(poll: dict, share: float, *, asof: date | None = None,
                  screen_sd: float | None = None,
                  drift_rate: float | None = None, **kw) -> dict[str, float]:
    """The same four numbers, unsummed, so they can be printed and traced.

    A weight nobody can decompose is a weight nobody can argue with, and this
    one is about to move a published forecast.
    """
    n_eff = effective_n(poll, **kw)
    p = min(max(float(share), 1e-4), 1 - 1e-4)
    return {
        "sampling": math.sqrt(p * (1 - p) / n_eff) if n_eff else float("nan"),
        "house": POLL_HOUSE_SD,
        "screen": (0.0 if poll.get("screen_disclosed")
                   else float(screen_sd if screen_sd is not None
                              else POLL_SCREEN_SD_UNDISCLOSED)),
        "drift": (float(drift_rate if drift_rate is not None
                        else POLL_DRIFT_PP_PER_ROOT_DAY)
                  * math.sqrt(_days_out(poll, asof))),
        "n_eff": n_eff if n_eff else float("nan"),
        "deff": design_effect(poll, **kw),
        "total": poll_sd(poll, share, asof=asof, screen_sd=screen_sd,
                         drift_rate=drift_rate, **kw),
    }


def effective_houses(polls: list[dict], *,
                     half_life_days: float | None = None,
                     asof: date | None = None) -> float:
    """Kish effective count of independent HOUSES, over recency weights.

    **This is what makes the single-house problem solve itself.** House error is
    a bias shared by every wave a house publishes, so averaging waves cuts the
    sampling term by √k and does not touch it. Weighting by house rather than by
    wave is what expresses that: ``H_eff = (Σ W_h)² / Σ W_h²`` where ``W_h`` is
    the recency weight a house's waves carry between them.

    Measured on the two admitted SRF waves: H_eff = 1.0. Ten waves of that one
    house would also give 1.0.
    """
    if not polls:
        return 0.0
    half_life_days = (POLL_HALF_LIFE_DAYS if half_life_days is None
                      else half_life_days)
    weights = _recency_weights(polls, half_life_days=half_life_days, asof=asof)
    by_house: dict[str, float] = {}
    for poll, w in zip(polls, weights):
        house = str(poll.get("house") or poll.get("id") or "?")
        by_house[house] = by_house.get(house, 0.0) + float(w)
    total = sum(by_house.values())
    sq = sum(w * w for w in by_house.values())
    return (total * total / sq) if sq > 0 else 0.0


def weight_cap(h_eff: float, *, house_k: float | None = None) -> float:
    """The most weight a poll may take, given how many houses stand behind it.

    ``H / (H + POLL_HOUSE_K)``. Belt and braces over inverse variance, which is
    only correct if both estimates are unbiased — see the constant.
    """
    k = float(house_k if house_k is not None else POLL_HOUSE_K)
    h = max(float(h_eff), 0.0)
    return h / (h + k) if h > 0 else 0.0


def blend_weight(poll_sd: float, model_sd: float) -> float:
    """Inverse-variance weight on the poll. The professional mechanism.

    Two estimates of the same quantity are combined in proportion to their
    precision: ``w = (1/s_p²) / (1/s_p² + 1/s_m²)``. This is what poll
    aggregation does and it is the right answer to "how much should a poll
    count", replacing a weight keyed on how much electoral history a party
    happens to have.

    It also REPRODUCES the rule it replaces, without being told to. A party with
    no record has an enormous model spread — ``levels.SD_CEILING`` is 1.20 in log
    units — so the poll takes nearly all the weight. A party with a long
    retention record has a tight prior and the poll is one reading among
    several. The difference is that the weight now follows from how uncertain
    the two estimates ARE, rather than from a count of observations, so an
    accurate metro poll of a well-known party is not thrown away: at Johannesburg
    2016 the model's own ANC interval was some 11 points wide against a poll
    error of 3, and the poll was right.
    """
    vp = max(float(poll_sd), 1e-6) ** 2
    vm = max(float(model_sd), 1e-6) ** 2
    return float((1.0 / vp) / ((1.0 / vp) + (1.0 / vm)))

# Registered voters nationally, per local election. Needed as the denominator of
# the contested-area conversion and NOT derivable from anything on disk: the
# archive holds eight metros, not the country. Sourced from the IEC's published
# figures as reported in Wikipedia's "<year> South African municipal elections",
# and recorded here rather than typed at a call site so a wrong one is findable.
# VOTES CAST, not registration: the conversion's numerator is a share of the
# vote, so its denominator must be too. Mixing the two understates the
# territory by the turnout ratio and inflates every estimate by about 2x.
NATIONAL_VOTES = {
    # roll x turnout, both as published by the IEC.
    "2016": int(26_333_353 * 0.5794),
    "2021": int(26_204_579 * 0.4579),
    # 2026 is not yet known; registration closes with the voters' roll for the
    # election. See PROJECTED_METRO_SHARE below for what the live forecast uses
    # instead, and why a national total is not what is missing.
}

# WHAT THE CONVERSION ACTUALLY NEEDS IS A RATIO, AND BOTH HALVES OF IT ARE
# VOTES CAST AT THE TARGET ELECTION.
# ---------------------------------------------------------------------------
# `contested_share` divides the votes cast in the municipalities a party
# contests by the votes cast nationally. At a past target both come from the
# archive. At a LIVE target neither is knowable — `votes_by_metro("2026")`
# returns `{}` because no 2026 result file exists, and `NATIONAL_VOTES` has no
# 2026 key. So the arrivals poll path — **the largest single measured effect in
# the poll channel, 48 coherent seats across nine city-years (§1.65)** — was
# switched off for the one election this repository is actually forecasting.
# §1.65 recorded that and asked for a 2026 `NATIONAL_VOTES` entry. That would
# not have fixed it: it supplies the denominator and the NUMERATOR is missing
# too.
#
# What IS projectable is the ratio itself. Each metro's share of the national
# vote is a demographic fact that moves slowly, and it is measured:
#
#     metro    2016      2021     change
#     JHB     0.0823    0.0770    -6.4%
#     CPT     0.0818    0.0761    -7.0%
#     ETH     0.0724    0.0646   -10.8%
#     TSH     0.0579    0.0561    -3.1%
#     EKU     0.0589    0.0559    -5.1%
#     NMA     0.0249    0.0220   -11.8%
#     BUF     0.0149    0.0150    +0.2%
#     MAN     0.0156    0.0147    -5.9%
#     all 8   0.4088    0.3813    -6.7%
#
# **TWO CYCLES IS n = 2, and a trend cannot be told from noise on it.** Every
# metro fell, which looks like a trend and is exactly what two points always
# look like. ITERATING rules 10 and 11 apply with full force, so nothing is
# extrapolated: the projection is the LAST OBSERVED value, and the 2016→2021
# movement is quoted as the uncertainty on it rather than fitted through.
# Declared in JUDGEMENT-CALLS.md §A.
#
# The backtest is untouched by construction: 2016 and 2021 have real result
# files, so `votes_by_metro` returns real numbers and this table is never
# consulted. It fires only where nothing can check it — which is the
# `contestation_expand` position (§1.60), stated here as it is there.
PROJECTED_METRO_SHARE = {
    "JHB": 0.0770, "CPT": 0.0761, "ETH": 0.0646, "TSH": 0.0561,
    "EKU": 0.0559, "NMA": 0.0220, "BUF": 0.0150, "MAN": 0.0147,
}


def load(path: Path = REGISTER) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("polls", [])


@dataclass(frozen=True)
class Problem:
    """Something wrong with a poll record.

    ``severity`` is the whole design. **"error" means malformed** — a typo, a
    wrong type, a value that cannot be meant — and it is fatal, because a poll
    we intended to count and silently did not is worse than a run that stops.
    **"warn" means incomplete but honest**: a real limitation of what the house
    published, which the arithmetic already handles.

    The distinction was found the hard way: the first version of this validator
    made a missing ``n`` fatal, and it would have refused the committed register
    — because Ipsos never published the metro cut sizes for the very nine
    readings `POLL_HOUSE_SD` is calibrated on. A rule strict enough to reject
    your own calibration set is measuring your wishes, not the data.
    """
    poll_id: str
    field: str
    message: str
    severity: str = "error"

    def __str__(self) -> str:
        return f"[{self.severity}] {self.poll_id}: {self.field} — {self.message}"


@dataclass(frozen=True)
class Exclusion:
    """A well-formed poll that this target may not use, and why."""
    poll_id: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"{self.poll_id}: {self.detail} [{self.rule}]"


SCOPES = frozenset({"national", "metro", "metro-aggregate", "province"})


class PollRegisterError(RuntimeError):
    """The register is malformed. Raised instead of quietly using less of it."""


def validate(polls: list[dict] | None = None) -> list[Problem]:
    """Every way a poll record is BROKEN, as opposed to inapplicable.

    **`min_n` IS GONE, and its removal was overdue.** The sample-size floor is a
    SCREEN, not a validation — see :func:`screen`'s ``under-min-n`` rule and
    MODEL-LOG §1.69. The kwarg was accepted and ignored from 2026-08-22, kept
    for callers written against the older signature, and its own
    ``DELIBERATELY_UNUSED`` entry said *"removing it would be the right cleanup
    once nothing passes it"*. On 2026-08-23 nothing passed it, and a widened
    lever guard flagged the asymmetry — `poll_min_n` reaching `screen` and not
    the validators. An argument accepted and ignored is a trap, not an API.
    MODEL-LOG §1.85.

    The distinction is the point. `usable_for` used to express both with the
    same silent ``continue``, so a poll that could not be used because it was
    taken after polling day — a fact about the election — was indistinguishable
    from one that could not be used because someone typed ``"Metro"`` instead of
    ``"metro"``. The first is correct behaviour; the second is a poll we meant
    to count and silently did not, and there was no way to tell them apart.

    That is not hypothetical: `ipsos-w2-2025-metros` is dropped by every caller
    and simultaneously offered as a one-click preset by the interactive.

    It matters more now for two reasons. **Readers will submit polls** to the
    competition, and a submission that vanishes without explanation is a bug
    report we never receive. And the 2026 forecast has **one house**: losing one
    of its two waves to a typo would move a published number and print nothing.
    """
    problems: list[Problem] = []
    for poll in (polls if polls is not None else load()):
        pid = str(poll.get("id") or "<no id>")
        if not poll.get("id"):
            problems.append(Problem(pid, "id", "every poll needs an id; "
                                    "`montecarlo` indexes on it"))
        scope = poll.get("scope")
        if scope not in SCOPES:
            problems.append(Problem(pid, "scope",
                                    f"{scope!r} is not one of {sorted(SCOPES)} "
                                    f"— case matters, 'Metro' is not 'metro'"))
        if scope == "metro" and poll.get("numbers") and not poll.get("city"):
            problems.append(Problem(pid, "city", "a metro poll must name its "
                                    "city, or it gets applied to whichever one "
                                    "is being forecast"))
        if scope == "metro-aggregate":
            problems.append(Problem(
                pid, "scope", "no caller admits `metro-aggregate` — the metro "
                "path takes `metro` and the arrivals path takes `national`, so "
                "this record is recorded and never used. That is correct (eight "
                "metros averaged is not a reading of one of them) but it should "
                "be a decision, not a silent drop", severity="warn"))
        raw = poll.get("fieldwork_end")
        if not raw:
            problems.append(Problem(pid, "fieldwork_end",
                                    "missing; a poll that cannot be dated "
                                    "cannot be shown to precede the election "
                                    "it informs"))
        elif _end(poll) is None:
            problems.append(Problem(pid, "fieldwork_end",
                                    f"{raw!r} is not ISO 8601 (YYYY-MM-DD)"))
        numbers = poll.get("numbers")
        if numbers:
            if not poll.get("house"):
                problems.append(Problem(pid, "house", "missing; the house is "
                                        "what `effective_houses` counts, and a "
                                        "KeyError on it once silently killed "
                                        "the whole 2026 poll path"))
            total = sum(float(v) for v in numbers.values())
            if total > 1.001:
                problems.append(Problem(pid, "numbers",
                                        f"shares sum to {total:.3f}; they are "
                                        f"fractions, not percentages"))
            if any(float(v) < 0 for v in numbers.values()):
                problems.append(Problem(pid, "numbers", "a negative share"))
            n = poll.get("n")
            if n is None:
                problems.append(Problem(
                    pid, "n", "no sample size published, so this poll cannot be "
                    "priced on sampling error and falls back to the house term "
                    "alone. Honest, not malformed — Ipsos never published the "
                    "metro cut sizes for the readings POLL_HOUSE_SD is "
                    "calibrated on", severity="warn"))
            elif float(n) <= 0:
                problems.append(Problem(
                    pid, "n", f"{n} is not a sample size"))
    return problems


def validate_or_die(polls: list[dict] | None = None) -> list[dict]:
    """Load and validate, or raise. The entry point everything else uses."""
    loaded = polls if polls is not None else load()
    errors = [p for p in validate(loaded)
              if p.severity == "error"]
    if errors:
        raise PollRegisterError(
            f"{len(errors)} malformed poll record(s) in {REGISTER}:\n  "
            + "\n  ".join(str(p) for p in errors)
            + "\n\nA malformed record used to be dropped in silence. It is "
              "fatal instead because a poll we meant to count and silently did "
              "not is worse than a run that stops. Warnings do not raise: see "
              "Problem.severity.")
    return loaded


def screen(target: cityconfig.Target, polls: list[dict] | None = None,
           allow_commissioned: bool = False, *,
           min_n: float | None = None
           ) -> tuple[list[dict], list[Exclusion]]:
    """Admitted polls, and every exclusion WITH ITS REASON.

    Same five rules `usable_for` always applied, plus the sample-size floor.
    The difference is that a refusal is now a returned object rather than a
    `continue`, so a run can print what it declined and why.

    **`min_n` lives here and not in `validate`, and that line was drawn in the
    wrong place once.** §1.68 defined the split as *validate = malformed,
    fatal; screen = well-formed polls this target may not use* — and then put
    the floor on the fatal side, so a 504-respondent SRF wave was reported as
    a *malformed record* rather than as a small one. Two consequences, both
    real: the shipped register raised `PollRegisterError` the moment the floor
    was swept above 504, so `test_every_tunable_lever_actually_moves_the_forecast`
    could not perturb `poll_min_n` at all and the whole run died; and a reader
    submitting a small poll to the competition would have been told their
    record was broken when it was merely small. A poll with a published,
    positive, too-small `n` is the *definition* of well-formed-but-inadmissible.
    MODEL-LOG §1.69.
    """
    floor = float(min_n if min_n is not None else POLL_MIN_N)
    kept: list[dict] = []
    out: list[Exclusion] = []
    for poll in (polls if polls is not None else load()):
        pid = str(poll.get("id") or "<no id>")
        n = poll.get("n")
        if poll.get("numbers") and n is not None and float(n) < floor:
            out.append(Exclusion(pid, "under-min-n",
                                 f"n = {n:g}, below the admission floor "
                                 f"{floor:g}"))
            continue
        when = _end(poll)
        if when is None:
            out.append(Exclusion(pid, "undated", "no usable fieldwork_end"))
            continue
        if when >= target.date:
            out.append(Exclusion(pid, "after-polling-day",
                                 f"fieldwork ended {when}, on or after "
                                 f"{target.date}"))
            continue
        if poll.get("commissioned_by") and not allow_commissioned:
            out.append(Exclusion(pid, "commissioned",
                                 f"commissioned by {poll['commissioned_by']}"))
            continue
        if poll.get("scope") == "metro" and not poll.get("city"):
            out.append(Exclusion(pid, "metro-without-city",
                                 "a metro poll that does not name its city"))
            continue
        declared = str(poll.get("target") or "")
        if declared and declared != str(target.year):
            out.append(Exclusion(pid, "other-election",
                                 f"declared for {declared}, not {target.year}"))
            continue
        if not declared and (target.date - when).days > CAMPAIGN_WINDOW_DAYS:
            out.append(Exclusion(pid, "outside-window",
                                 f"{(target.date - when).days} days before "
                                 f"polling day, over the "
                                 f"{CAMPAIGN_WINDOW_DAYS}-day window"))
            continue
        kept.append(poll)
    return kept, out


def usable_for(target: cityconfig.Target, polls: list[dict] | None = None,
               allow_commissioned: bool = False, *,
               min_n: float | None = None) -> list[dict]:
    """Polls whose fieldwork ended before this target's polling day.

    Anything without a machine-readable ``fieldwork_end`` is REFUSED rather than
    parsed leniently. A poll that cannot be dated cannot be shown to precede the
    election it is informing, and "probably before" is not a standard this
    repository applies anywhere else.

    Delegates to :func:`screen`, which returns the reasons as well. Callers that
    want to report what was declined should use that directly.
    """
    return screen(target, polls, allow_commissioned, min_n=min_n)[0]


def aggregate(polls: list[dict], half_life_days: float | None = None,
              asof: date | None = None) -> dict[str, float] | None:
    """One set of numbers from several polls, weighted by recency.

    Applying polls one after another, as this module first did, is not
    aggregation — it is the LAST one applied winning, and the order was the
    register's, so Johannesburg 2026 was having its oldest poll applied last and
    dominating. Three CoJ waves spanning six months were being read as though
    only the January one existed.

    Weight is ``exp(-age / tau)`` with tau set from a 120-day half-life: a poll
    six months stale counts about a quarter of a fresh one. That is a judgement
    about how fast a metro's opinion moves and it is declared as one — there is
    no South African metro polling series long enough to fit it.

    Herding and house effects are NOT corrected here. With two houses and four
    waves they are not estimable, and pretending otherwise would be worse than
    the gap. Note it wherever the blend is quoted.

    **`half_life_days` RESOLVES AT CALL TIME, and until 2026-08-23 it did not.**
    It was `half_life_days: float = 120.0` — a numeric default argument, the
    `LEVEL_DF` shape, and the THIRD instance of it here. This one was the worst,
    because this function produces the poll-blended **CENTRE**: `montecarlo`
    passed `scenario["poll_half_life_days"]` to `effective_houses` and
    `aggregate_sd` and passed **nothing** to this, so the lever moved the poll's
    WEIGHT and could not touch the poll's NUMBERS.

    Measured on the two admitted Johannesburg 2026 waves, the ANC's blended
    share runs **18.4% at a 30-day half-life to 24.0% with no decay** — 5.6
    points in the live forecast, unreachable by any sweep. And
    `test_levers_are_live` certified the lever live at 2026 throughout, because
    it does move — through the σ path. That is exactly how it hid.

    A `None` sentinel resolving to `POLL_HALF_LIFE_DAYS` cannot be frozen at
    import. `aggregate_sd` below already had this shape; this function did not.
    """
    if half_life_days is None:
        half_life_days = POLL_HALF_LIFE_DAYS
    dated = [(p, date.fromisoformat(str(p["fieldwork_end"])))
             for p in polls if p.get("fieldwork_end") and p.get("numbers")]
    if not dated:
        return None
    asof = asof or max(d for _, d in dated)
    tau = float(half_life_days) / np.log(2.0)
    out: dict[str, float] = {}
    total: dict[str, float] = {}
    for poll, when in dated:
        w = float(np.exp(-max((asof - when).days, 0) / tau))
        for party, share in (poll.get("numbers") or {}).items():
            out[party] = out.get(party, 0.0) + w * float(share)
            total[party] = total.get(party, 0.0) + w
    return {p: out[p] / total[p] for p in out if total[p] > 0}


def aggregate_sd(polls: list[dict], party: str, share: float, *,
                 half_life_days: float | None = None,
                 asof: date | None = None,
                 screen_sd: float | None = None,
                 drift_rate: float | None = None, **kw) -> float:
    """Total error on the AGGREGATE's reading of one party.

    The hierarchy is the whole point, and it is what makes the single-house
    problem solve itself rather than needing a dial:

    * **sampling shrinks with waves.** Each wave is an independent draw, so the
      recency-weighted combination has the usual ``Σw²σ² / (Σw)²``.
    * **the house term does NOT.** It is a bias every wave of a house shares, so
      it shrinks only with the number of independent HOUSES — ``σ_house² /
      H_eff`` — and publishing more often does nothing to it.
    * **screen and drift** are grouped the same way, being properties of a
      house's method and of when it went to field.

    **So one house has a FLOOR it cannot publish its way past.** Measured on the
    admitted 2026 SRF wave, replicated, at polling day:

        waves of one house    1      2      4      8     20    100
        σ_aggregate        4.35   3.88   3.63   3.49   3.41   3.36  pp

    against an irreducible **3.35pp** — the house, screen and drift block with
    H_eff = 1. More waves do buy something, because sampling error is real and
    does average down; they buy less and less, and they never cross the floor.

    That is the honest form of the single-house argument. An earlier draft of it
    claimed two waves "buy nothing" (4.24 → 4.30); measured, they buy 4.35 →
    3.88, which is a real reduction in the sampling term and nothing at all in
    the house term. The protection is the asymptote, not a flat line — and on
    top of it :func:`weight_cap` holds a one-house aggregate to 0.50 at the shipped `poll_house_k` of 1.0 of the
    blend however small σ gets.
    """
    half_life_days = (POLL_HALF_LIFE_DAYS if half_life_days is None
                      else half_life_days)
    usable = [p for p in polls if (p.get("numbers") or {}).get(party) is not None]
    if not usable:
        return POLL_HOUSE_SD
    weights = _recency_weights(usable, half_life_days=half_life_days, asof=asof)
    total = sum(weights)
    if total <= 0:
        return POLL_HOUSE_SD
    # sampling: shrinks with waves
    sampling_sq = 0.0
    for poll, w in zip(usable, weights):
        n_eff = effective_n(poll, **kw)
        p = min(max(float(share), 1e-4), 1 - 1e-4)
        s = math.sqrt(p * (1 - p) / n_eff) if n_eff else POLL_HOUSE_SD
        sampling_sq += (w * s) ** 2
    sampling_sq /= total ** 2
    # house, screen, drift: shrink with HOUSES, not waves
    h_eff = max(effective_houses(usable, half_life_days=half_life_days,
                                 asof=asof), 1e-9)
    _screen = float(screen_sd if screen_sd is not None
                    else POLL_SCREEN_SD_UNDISCLOSED)
    _drift = float(drift_rate if drift_rate is not None
                   else POLL_DRIFT_PP_PER_ROOT_DAY)
    screen = sum(w * (0.0 if p.get("screen_disclosed") else _screen)
                 for p, w in zip(usable, weights)) / total
    drift = sum(w * _drift * math.sqrt(_days_out(p, asof))
                for p, w in zip(usable, weights)) / total
    if SIGMA_TWO_TERM:
        # THE PRE-REGISTERED REPLACEMENT (§1.87). Two terms, and only ONE of
        # them may be divided by the number of houses. `screen` is folded into
        # the common term rather than argued separately, because a decomposition
        # cannot identify its own components (Dominitz & Manski 2025).
        return math.sqrt(sampling_sq
                         + SIGMA_COMMON ** 2                    # never shrinks
                         + SIGMA_IDIO ** 2 / h_eff              # only this one
                         + (drift * SIGMA_DRIFT_PER_ROOT_DAY
                            / max(POLL_DRIFT_PP_PER_ROOT_DAY, 1e-12)) ** 2
                         + SIGMA_VOLATILITY ** 2)
    return math.sqrt(sampling_sq
                     + (POLL_HOUSE_SD ** 2 + screen ** 2 + drift ** 2) / h_eff)


def contested_share(codes: list[str], year: str,
                    roll: dict[str, float] | None = None) -> float | None:
    """What fraction of the national roll sits in the municipalities listed.

    ``roll`` maps IEC code to registered voters; supplying it keeps this
    testable. Returns None when the national figure for that year is unknown,
    because a conversion with a guessed denominator is worse than none.
    """
    if not codes:
        return None
    if roll is None:
        roll = votes_by_metro(year)
    national = NATIONAL_VOTES.get(str(year))
    if not roll or not national:
        # A LIVE TARGET. Neither half of the ratio exists yet — see
        # PROJECTED_METRO_SHARE. Fall back to the last observed shares, which
        # is the whole ratio at once and needs no national total.
        held = sum(PROJECTED_METRO_SHARE.get(c, 0.0) for c in codes)
        return held if held > 0 else None
    held = sum(roll.get(c, 0.0) for c in codes)
    return (held / national) if held > 0 else None


def votes_by_metro(year: str) -> dict[str, float]:
    """Votes cast per metro on the PR ballot, from the published result files."""
    import pools as PL
    from ingest_lge import read_municipality

    out: dict[str, float] = {}
    for code in PL.METRO_CODES:
        path = PL.metro_file(code, year)
        if path is None:
            continue
        total = 0
        for row in read_municipality(path, code, "PR"):
            total += int(row["Party_Votes"] or 0)
        if total:
            out[code] = total
    return out


def metro_estimate(poll: dict, party: str, contests: list[str], year: str,
                   roll: dict[str, float] | None = None) -> dict | None:
    """A national poll number converted to a share of each contested metro.

    Returns ``{"share": s, "contested_share": t, "basis": ...}`` or None when
    the poll does not carry the party, or the denominator cannot be formed.

    The estimate is the party's AVERAGE across everywhere it stands. It is not a
    per-metro forecast and must not be presented as one: ActionSA's 9.78% by this
    route sat against actuals of 18.12%, 9.28%, 7.36% and 2.35%.
    """
    share = (poll.get("numbers") or {}).get(party)
    if share is None or poll.get("scope") != "national":
        return None
    t = contested_share(contests, year, roll)
    if not t:
        return None
    return {"share": float(share) / t, "contested_share": t,
            "national": float(share), "poll": poll.get("id"),
            "basis": (f"{poll.get('house')} {poll.get('fieldwork_end')}: "
                      f"{share:.1%} national, contesting municipalities holding "
                      f"{t:.1%} of the roll")}
