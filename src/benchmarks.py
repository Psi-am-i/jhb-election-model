"""Naive forecasters, so the model has something to beat.

The Monte Carlo is about three thousand lines of pool ranges, Dirichlet
concentrations, γ transfer, splinter branches and entrant geography. Until now
nothing in the repository has established that any of it beats the sentence
"assume the last local election happens again". A model that cannot beat that
sentence is not a model; it is an expensive way of restating history. So this
module implements the sentence, and two slightly less naive versions of it, in
the *same output shape* the model produces -- a list of ``{party: seats}``
dicts, one per draw, plus a matching list of ``{ward: winner}`` -- so
``score.py`` scores them with the identical code path and no special cases.

Three baselines, in increasing order of how much they are allowed to know:

``last-lge``
    The previous local election's VD-level result, re-laid on the target's ward
    boundaries and run through the same seat allocator. Deterministic. This is
    the baseline that matters: it is what a well-informed person with no model
    would say, and it is very hard to beat in a stable electorate.

``uniform-swing``
    The previous local election, shifted by the movement between the two
    national elections that bracket it -- see :func:`uniform_swing` for why that
    is the only aggregate a legitimate uniform swing can use here.

``prior-lge-noise``
    ``last-lge`` with a spread calibrated from how much the parties actually
    moved over the *preceding* local-election transition. Deterministic
    baselines score infinitely badly on nothing, but they also make CRPS
    collapse to absolute error and coverage collapse to 0% or 100%; this one is
    a genuine distribution, so it is the honest opponent for a distributional
    model. If the Monte Carlo cannot beat "last time, plus last transition's
    worth of uncertainty", its distributional layer is adding nothing.

**Every baseline sees only pre-election data.** Same rule as the backtest
harness, same reasoning: ward boundaries and the voters' roll come from the
target's own result file because they are published months before polling day;
the votes in that file are touched only by the scorer. Council size comes from
``cities/<slug>.toml`` (see :func:`council_size`), not from the IEC's
post-election seat calculation. What each baseline uses is listed in its
docstring, and there is nothing else in scope for it to use.

Usage::

    python src/benchmarks.py --target 2021
    python src/benchmarks.py --target 2016 --benchmark last-lge --draws 2000
    python src/benchmarks.py --city tshwane --target 2021
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

import backtest as B
import cityconfig
import montecarlo as M
import score as S
from fold import citywide, load, shares
from seats import eligible_parties  # allocate itself is reached via montecarlo

def sources_for(target: int) -> dict[str, str | None]:
    """Files each baseline needs that the backtest's TARGETS table does not name.

    ``prior_npe`` is the national election preceding ``prior_lge``; together
    with the target's own ``base`` NPE it brackets the local election being
    carried forward, which is what makes a uniform swing computable without
    seeing the target. ``earlier_lge`` is the local election before
    ``prior_lge``, used only to measure how much parties typically move over
    one local cycle.

    Walked off ``cityconfig.CALENDAR`` rather than typed as a per-target table:
    the table it replaces listed only 2011/2016/2021, so a target ``backtest``
    was willing to run and this module was not would have died on a ``KeyError``
    with nothing to say which of the two was wrong. ``None`` means the calendar
    has no such election, which the callers report as "this baseline is not
    computable for this target" rather than crashing.
    """
    prior_lge = cityconfig.preceding(target, "LGE")
    prior_npe = cityconfig.preceding(prior_lge, "NPE") if prior_lge else None
    earlier_lge = cityconfig.preceding(prior_lge, "LGE") if prior_lge else None
    return {"prior_npe": cityconfig.CALENDAR[prior_npe].results if prior_npe else None,
            "earlier_lge": (cityconfig.CALENDAR[earlier_lge].results
                            if earlier_lge else None)}

# THE OPPONENT'S FLOOR IS ITS OWN NUMBER, NOT THE MODEL'S (owner, 2026-08-28).
#
# This was `SHARE_FLOOR = M.SHARE_FLOOR`, evaluated at IMPORT — so setting
# `montecarlo.SHARE_FLOOR` moved the model and left the bar where it was
# (§1.97, verified: at `M.SHARE_FLOOR = 0.05` this stayed 0.002). That looked
# like a `LEVEL_DF` §1.33 freeze and it is asymmetric in the dangerous
# direction: a sweep silently changes the margin without changing the forecast.
#
# **The fix is NOT to make it track.** A baseline that moves when a model
# constant is swept is not a bar — nothing could be compared across the change.
# The defect was that a snapshot LOOKS like it tracks. So it is pinned as the
# opponent's own declared constant, at the value it already had.
#
# NUMBER-NEUTRAL: 0.002 is what `M.SHARE_FLOOR` resolved to at import, so no
# baseline moves. If the model's floor is ever re-derived, this is a separate
# decision and should be taken deliberately rather than inherited.
SHARE_FLOOR = 0.002     # the prior-lge-noise logit clip; see above
NEW_PARTY_SIGMA = 1.0   # logit spread for a party with no previous cycle to measure
MIN_SIGMA = 0.15        # nobody is nailed on: floor the measured movement
MAX_SIGMA = 2.0


# ---------------------------------------------------------------------------
# assembling what a baseline is allowed to see
# ---------------------------------------------------------------------------


@dataclass
class Context:
    """Pre-election inputs shared by the baselines. Contains no target votes."""

    target: int
    spec: dict
    council: int
    universe: list[str] = field(default_factory=list)
    vds: list[str] = field(default_factory=list)
    ward_list: list[str] = field(default_factory=list)
    vd_ward: np.ndarray | None = None
    weight: np.ndarray | None = None
    ward_share: np.ndarray | None = None   # (V, P) prior LGE, ward ballot
    pr_share: np.ndarray | None = None     # (V, P) prior LGE, PR ballot
    ward_city: np.ndarray | None = None    # (P,)  prior LGE citywide, ward ballot
    pr_city: np.ndarray | None = None
    base_npe_city: dict[str, float] = field(default_factory=dict)
    prior_npe_city: dict[str, float] = field(default_factory=dict)
    earlier_lge_city: dict[str, float] = field(default_factory=dict)
    prior_lge_city: dict[str, float] = field(default_factory=dict)
    overhang_rule: str = M.DEFAULTS["overhang_rule"]


def _city_shares(path: Path, ballot: str | None) -> dict[str, float]:
    votes, _ = load(path, ballot)
    return citywide(votes)


def _fill(vd_shares: dict[str, dict[str, float]], city: dict[str, float],
          vds: list[str], universe: list[str]) -> np.ndarray:
    """VD × party share matrix, falling back to the citywide share for a VD the
    previous election did not have (new or re-numbered voting districts)."""
    fallback = np.array([city.get(p, 0.0) for p in universe], dtype=float)
    rows = []
    for vd in vds:
        if vd in vd_shares:
            rows.append([vd_shares[vd].get(p, 0.0) for p in universe])
        else:
            rows.append(fallback)
    out = np.array(rows, dtype=float)
    total = out.sum(axis=1, keepdims=True)
    return np.divide(out, total, out=np.zeros_like(out), where=total > 0)


def council_size(target: int) -> int:
    """Seats in the target's council, from the city config's per-year structure.

    ``backtest.TARGETS`` carries a hard-coded ``council`` of 260/270/270. Those
    are *Johannesburg's* numbers: Tshwane's councils were 210/214/214, so a
    backtest of any other metro allocates the wrong chamber and mis-scores both
    the forecast and the ground truth. The right figure lives in
    ``cities/<slug>.toml`` under ``[structure.by_year.<year>]``.

    This used to open the IEC's ``seat_calculation_detail`` spreadsheet for the
    target year and take "Total Seats Available" from it. The number is the same
    -- council size is fixed by delimitation months before polling day, so there
    was no material leak -- but that spreadsheet is *published after the result*,
    and this module's promise is that every baseline sees only pre-election
    data. A promise that has to be argued for in a docstring is weaker than one
    you can check by looking at what the module opens, so it now opens a config
    file instead. (``derive_city.py`` read those config values from the same IEC
    source, once, outside the forecast path.)

    ``structure_for`` raises rather than falling back for a year it has no entry
    for: inheriting the wrong chamber silently is the failure this replaces.

    There is deliberately no override. A ``--council`` flag lived on the CLI
    until 2026-08-10, by which time it could not do anything: the size it set
    was passed on to ``backtest.actual_result``, which reconstructs the real
    council and asserts it against the IEC's published seat calculation, so any
    value other than the published one aborted the run before a single baseline
    was scored, and the value equal to it was a no-op. Council size is a fact
    about a city-year, not a dial; a counterfactual chamber belongs in
    ``overhang_regimes.py``, where the counterfactual is the point.
    """
    return int(cityconfig.active().structure_for(str(target))["council"])


def build_context(target: int, data_dir: Path = Path("data/raw/elections"),
                  overhang_rule: str | None = None) -> Context:
    """Gather every pre-election input the baselines need.

    Reads the target's result file for **boundaries and the roll only** -- the
    same exemption ``backtest.ward_structure`` documents -- and its votes never.
    """
    spec = B.TARGETS[target]
    src = sources_for(target)
    council = council_size(target)

    ward_of, registered = B.ward_structure(data_dir / spec["actual"])

    prior = data_dir / spec["prior_lge"]
    prior_ward_votes, _ = load(prior, "Ward")
    prior_pr_votes, _ = load(prior, "PR")
    prior_all_votes, _ = load(prior, None)

    ward_city_d = citywide(prior_ward_votes)
    pr_city_d = citywide(prior_pr_votes)

    base_npe_city = _city_shares(data_dir / spec["base"], None)
    # A missing file and a calendar with no such election are the same thing to
    # a baseline: it cannot be computed, and the ones that need it say so.
    try:
        prior_npe_city = (_city_shares(data_dir / src["prior_npe"], None)
                          if src["prior_npe"] else {})
    except FileNotFoundError:
        prior_npe_city = {}
    try:
        earlier_lge_city = (_city_shares(data_dir / src["earlier_lge"], None)
                            if src["earlier_lge"] else {})
    except FileNotFoundError:
        earlier_lge_city = {}

    # Party universe: everyone with a previous local result or a national one.
    # Independents are dropped, exactly as montecarlo does: they take seats out
    # of the pool through the Schedule 1 ``C`` term rather than earning an
    # entitlement, and no baseline here predicts an independent ward win.
    universe = sorted({p for p in set(ward_city_d) | set(pr_city_d) |
                       set(base_npe_city) | set(prior_npe_city)
                       if p not in ("IND", "INDEPENDENT")})

    vds = sorted(v for v in ward_of)
    ward_list = sorted({ward_of[v] for v in vds})
    ward_index = {w: i for i, w in enumerate(ward_list)}
    vd_ward = np.array([ward_index[ward_of[v]] for v in vds])

    # VD weight: the target's roll times the previous local election's turnout
    # there -- the same weighting montecarlo.run_model applies, so a baseline
    # and the model are weighting the same city.
    prior_cast = {v: sum(c.values()) for v, c in prior_pr_votes.items()}
    reg = np.array([registered.get(v, 0) for v in vds], dtype=float)
    turnout = np.array([prior_cast.get(v, np.nan) / registered[v]
                        if registered.get(v) else np.nan for v in vds])
    typical = np.nanmedian(turnout[np.isfinite(turnout)]) \
        if np.isfinite(turnout).any() else 0.4
    turnout = np.where(np.isfinite(turnout), turnout, typical)
    weight = np.clip(reg * turnout, 1.0, None)

    return Context(
        target=target, spec=spec, council=council, universe=universe, vds=vds,
        ward_list=ward_list, vd_ward=vd_ward, weight=weight,
        ward_share=_fill(shares(prior_ward_votes), ward_city_d, vds, universe),
        pr_share=_fill(shares(prior_pr_votes), pr_city_d, vds, universe),
        ward_city=np.array([ward_city_d.get(p, 0.0) for p in universe]),
        pr_city=np.array([pr_city_d.get(p, 0.0) for p in universe]),
        base_npe_city=base_npe_city, prior_npe_city=prior_npe_city,
        earlier_lge_city=earlier_lge_city,
        prior_lge_city=citywide(prior_all_votes),
        overhang_rule=overhang_rule or M.DEFAULTS["overhang_rule"],
    )


# ---------------------------------------------------------------------------
# shares -> a council
# ---------------------------------------------------------------------------


def council_from_shares(ctx: Context, ward_share: np.ndarray,
                        pr_share: np.ndarray) -> tuple[dict[str, int], dict[str, str]]:
    """Turn VD-level ballot shares into ``({party: seats}, {ward: winner})``.

    Uses the project's own allocator, including the excessive-seats rule, so a
    baseline's council is produced by exactly the machinery that produces the
    model's. ``montecarlo.COUNCIL`` is a module global the allocator reads, so
    it is set for the target and restored -- the same thing ``backtest.main``
    does, done locally and put back.
    """
    ward_votes = ctx.weight[:, None] * ward_share
    pr_votes = ctx.weight[:, None] * pr_share

    per_ward = np.zeros((len(ctx.ward_list), len(ctx.universe)))
    np.add.at(per_ward, ctx.vd_ward, ward_votes)
    winners = {ctx.ward_list[i]: ctx.universe[j]
               for i, j in enumerate(per_ward.argmax(axis=1))}
    wins: defaultdict[str, int] = defaultdict(int)
    for party in winners.values():
        wins[party] += 1

    ward_totals = {p: int(round(ward_votes[:, i].sum()))
                   for i, p in enumerate(ctx.universe)}
    pr_totals = {p: int(round(pr_votes[:, i].sum()))
                 for i, p in enumerate(ctx.universe)}
    combined = eligible_parties(ward_totals, pr_totals)

    previous = M.COUNCIL
    try:
        M.COUNCIL = ctx.council
        seats, _council, _thr, _over = M.allocate_with_overhang(
            combined, dict(wins), rule=ctx.overhang_rule)
    finally:
        M.COUNCIL = previous
    return {p: s for p, s in seats.items() if s > 0}, winners


def _repeat(seats: dict[str, int], winners: dict[str, str], draws: int):
    """A deterministic forecast as a degenerate distribution of ``draws`` draws.

    Not padding: it is the correct representation. A point forecast *is* a
    distribution with all its mass on one value, and scoring it that way makes
    CRPS reduce to absolute error and coverage to 0%/100% automatically, which
    is what a deterministic baseline deserves and what makes it comparable to
    the model under one code path.
    """
    return [dict(seats) for _ in range(draws)], [dict(winners) for _ in range(draws)]


# ---------------------------------------------------------------------------
# the three baselines
# ---------------------------------------------------------------------------


def last_lge(ctx: Context, draws: int = 1, seed: int | None = None):
    """"The last local election happens again." Deterministic.

    Uses: the previous LGE's VD-level ward and PR ballots; the target's ward
    boundaries and roll. Nothing else.

    The previous result is *re-laid on the target's boundaries* rather than
    copied as a seat count: VDs are mapped into the target's wards and the ward
    winner recomputed, so re-delimitation is handled honestly instead of being
    scored as a model error. Ward and PR ballots are kept separate, because
    seats follow the combined vote while ward wins follow the ward ballot alone.
    """
    seats, winners = council_from_shares(ctx, ctx.ward_share, ctx.pr_share)
    return _repeat(seats, winners, draws)


def uniform_swing(ctx: Context, draws: int = 1, seed: int | None = None):
    """The last local election, shifted by the national swing that bracketed it.

    Uses: the previous LGE's VD-level ballots; the two national elections
    *before* the target -- the one preceding the target (2019 for a 2021 run)
    and the one preceding the previous LGE (2014) -- plus boundaries and roll.

    **What a uniform swing may be pinned to here.** In the British usage the
    swing is applied so that the aggregate matches a *known* national result, or
    a poll. Neither exists for this problem: there is no national vote on local
    election day, and no metro-level polling series for these years. Pinning to
    the target's own aggregate would be reading the answer. So the only
    aggregate a legitimate uniform swing can use is the movement between the two
    national elections that bracket the local one being carried forward:

        predicted_share(party) = LGE_prev(party) + [NPE_recent - NPE_prior]

    That is a real assumption with a real failure mode -- it assumes national
    movement transfers one-for-one to local voting, which is exactly the
    assumption the model's γ and pool machinery exist to improve on. Which
    makes it the right thing to be measured against.

    The shift is additive in share space (the classic uniform swing), applied at
    VD level, clipped at zero and renormalised per VD. Additive means a party
    that gained 5 points nationally gains 5 points in every VD, including ones
    where it holds 2% -- deliberately naive. Parties in the LGE but not the NPEs
    get no shift; parties in the NPEs but not the LGE enter from zero, which is
    how a baseline gets to see a party like the EFF at all.
    """
    if not ctx.prior_npe_city:
        raise SystemExit(
            f"uniform-swing needs {sources_for(ctx.target)['prior_npe']}, which "
            f"is not on disk for this city — that file is the only legitimate "
            f"source of an aggregate shift for target {ctx.target}")
    swing = np.array([ctx.base_npe_city.get(p, 0.0) - ctx.prior_npe_city.get(p, 0.0)
                      for p in ctx.universe])
    ward = _renormalise(np.clip(ctx.ward_share + swing[None, :], 0.0, None))
    pr = _renormalise(np.clip(ctx.pr_share + swing[None, :], 0.0, None))
    seats, winners = council_from_shares(ctx, ward, pr)
    return _repeat(seats, winners, draws)


# How much of the national swing ``blended-swing`` carries. **MEASURED, and the
# answer is 1.0 — the boundary of the family, which is ``uniform-swing`` itself.**
# See :func:`blended_swing`; MODEL-LOG §1.57.
BLEND_W = 1.0


def blended_swing(ctx: Context, draws: int = 1, seed: int | None = None):
    """Uniform swing DAMPED toward persistence — the professional reference.

    ``last-lge`` (594 coherent seats over the panel) and ``prior-lge-noise``
    (561) are not references, they are strawmen, and quoting a 3.4x margin over
    them invites the obvious charge that the baselines were picked to be beaten.
    The standard answer in the forecasting literature is Murphy's convex
    combination of the two naive forecasts:

        w * (prev + swing) + (1 - w) * prev  ==  prev + w * swing

    which is worth writing out, because it collapses: **the convex combination
    of uniform swing and persistence is just a DAMPED swing**, and the whole
    family is one parameter. ``w = 1`` is ``uniform-swing``, ``w = 0`` is
    ``last-lge``, and anything between is the classic swing-damping correction
    for the fact that national movement does not transfer one-for-one to local
    voting.

    ``BLEND_W`` was fitted leave-one-city-year-out on this panel — the one place
    in this repository where fitting on the scoreboard is the right thing to do,
    because a reference forecast should be as strong as it honestly can be
    before the model is measured against it (rule 10 is about constants inside
    the MODEL).

    **The fit says 1.0, and 1.0 is ``uniform-swing``.** Coherent-comparable seat
    error over the nine city-years is monotone decreasing in ``w`` across the
    whole interval — 594 at 0.0, 456 at 0.5, 382 at 0.9, **376 at 1.0** — so the
    optimum inside the convex family sits exactly on the boundary. The
    unconstrained grid optimum is ``w = 1.05`` at 372, which is not a blend at
    all but an AMPLIFIED swing, it is worth 4 seats in 376, the grid is flat
    either side of it (376 / 376 / 372 / 374 / 372 / 374 / 376 from 0.95 to
    1.25), and **it does not survive leave-one-out: held out city-year by
    city-year the fitted blend totals 380 against uniform swing's 376.**

    So this function exists to have been checked, and it is kept runnable so the
    check is repeatable — but it is NOT reported as a fourth baseline, because a
    column identical to ``uniform-swing`` is noise. What it establishes is the
    thing worth establishing: **uniform swing is not a strawman.** It is the
    strongest member of the naive family on this panel, and the margin quoted
    over it is honest. MODEL-LOG §1.57.
    """
    if not ctx.prior_npe_city:
        raise SystemExit(
            f"blended-swing needs {sources_for(ctx.target)['prior_npe']}, which "
            f"is not on disk for this city — same requirement as uniform-swing")
    swing = BLEND_W * np.array(
        [ctx.base_npe_city.get(p, 0.0) - ctx.prior_npe_city.get(p, 0.0)
         for p in ctx.universe])
    ward = _renormalise(np.clip(ctx.ward_share + swing[None, :], 0.0, None))
    pr = _renormalise(np.clip(ctx.pr_share + swing[None, :], 0.0, None))
    seats, winners = council_from_shares(ctx, ward, pr)
    return _repeat(seats, winners, draws)


def prior_lge_noise(ctx: Context, draws: int = 2000, seed: int | None = 20211101,
                    scale: float = 1.0):
    """``last-lge`` with a spread calibrated on the previous local transition.

    Uses: the previous LGE's VD-level ballots; the LGE *before* that one, for
    the size of the spread only; boundaries and roll.

    **Why a spread at all.** A deterministic baseline is unbeatable on the
    scores that only look at a point and unscoreable on the ones that look at a
    distribution: its CRPS is just absolute error, its 90% interval is a single
    number, its PIT is degenerate. To ask whether the model's *uncertainty* is
    worth anything, the opponent must also be uncertain. This one is.

    **Where the spread comes from.** Not a guess: each party's citywide share is
    perturbed in logit space by ``N(0, σ_p)``, with ``σ_p`` set to how far that
    party actually moved over the preceding local-election transition
    (``|logit(prev) - logit(earlier)|``, floored at 0.15 and capped at 2.0 --
    nobody is nailed on, and nobody moves further than that in a way this can
    represent). A party with no earlier result gets σ = 1.0, since a party that
    did not exist last cycle is the least predictable thing on the ballot. So
    the claim is "parties will move about as much next time as they moved last
    time", calibrated only on data that predates the target.

    Draws are applied as a *proportional* swing: the citywide shift is turned
    into a per-party ratio and applied to every VD, then renormalised. The same
    draw drives both ballots, so ward and PR move together as they do in life,
    and the ward/PR split of the previous LGE is preserved.
    """
    if not ctx.earlier_lge_city:
        raise SystemExit(
            f"prior-lge-noise needs {sources_for(ctx.target)['earlier_lge']} to "
            f"calibrate its spread; it is not on disk for this city")
    sigma = np.array([_sigma_for(p, ctx) for p in ctx.universe]) * scale
    rng = np.random.default_rng(seed)

    seat_draws, ward_draws = [], []
    for _ in range(draws):
        z = rng.normal(0.0, sigma)
        ward = _shift(ctx.ward_share, ctx.ward_city, z)
        pr = _shift(ctx.pr_share, ctx.pr_city, z)
        seats, winners = council_from_shares(ctx, ward, pr)
        seat_draws.append(seats)
        ward_draws.append(winners)
    return seat_draws, ward_draws


def _sigma_for(party: str, ctx: Context) -> float:
    previous = ctx.prior_lge_city.get(party, 0.0)
    earlier = ctx.earlier_lge_city.get(party, 0.0)
    if previous <= 0 or earlier <= 0:
        return NEW_PARTY_SIGMA
    moved = abs(_logit(previous) - _logit(earlier))
    return float(np.clip(moved, MIN_SIGMA, MAX_SIGMA))


def _logit(p: float) -> float:
    p = min(max(p, SHARE_FLOOR), 1 - SHARE_FLOOR)
    return float(np.log(p / (1 - p)))


def _renormalise(matrix: np.ndarray) -> np.ndarray:
    total = matrix.sum(axis=1, keepdims=True)
    return np.divide(matrix, total, out=np.zeros_like(matrix), where=total > 0)


def _shift(vd_share: np.ndarray, city: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Apply a citywide logit shift to every VD as a proportional swing."""
    floored = np.clip(city, SHARE_FLOOR, 1 - SHARE_FLOOR)
    moved = 1.0 / (1.0 + np.exp(-(np.log(floored / (1 - floored)) + z)))
    moved = moved / moved.sum()
    ratio = np.divide(moved, floored, out=np.ones_like(moved), where=floored > 0)
    return _renormalise(vd_share * ratio[None, :])


BENCHMARKS = {
    "last-lge": last_lge,
    "uniform-swing": uniform_swing,
    "blended-swing": blended_swing,
    "prior-lge-noise": prior_lge_noise,
}


def run_one(name: str, ctx: Context, draws: int = 2000,
            seed: int | None = 20211101) -> list[dict[str, int]]:
    """Seat draws only -- the shape ``score.score_seats`` takes."""
    return run_with_wards(name, ctx, draws, seed)[0]


def run_with_wards(name: str, ctx: Context, draws: int = 2000,
                   seed: int | None = 20211101):
    """``(seat_draws, ward_winner_draws)``.

    The second half is what makes the Brier score computable: 135 contests per
    target rather than 10 party seat counts. The model reaches the same shape
    through ``montecarlo.ModelRun.ward_probabilities``, so a baseline and the
    model arrive at ``score.score_wards`` on identical terms.
    """
    if name not in BENCHMARKS:
        raise SystemExit(f"unknown benchmark {name!r}; have {sorted(BENCHMARKS)}")
    return BENCHMARKS[name](ctx, draws=draws, seed=seed)


def ward_probabilities(ward_draws) -> dict[str, dict[str, float]]:
    """``{ward: {party: P(win)}}`` from a list of per-draw winner maps."""
    counts: defaultdict[str, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int))
    for draw in ward_draws:
        for ward, party in draw.items():
            counts[ward][party] += 1
    n = len(ward_draws)
    return {w: {p: c / n for p, c in parties.items()} for w, parties in counts.items()}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    cityconfig.add_city_argument(ap)
    # Same set as backtest.py's --target, from the same derivation, and for the
    # same reason: --city is not parsed yet, so it is validated below rather
    # than frozen into `choices` against whichever city happened to be default.
    ap.add_argument("--target", type=int, default=2021, metavar="YEAR",
                    help="past local election to score against (default 2021); "
                         "runnable targets are derived per city")
    ap.add_argument("--benchmark", default="all",
                    choices=sorted(BENCHMARKS) + ["all"])
    ap.add_argument("--draws", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20211101)
    ap.add_argument("--overhang-rule", default=None)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    args = ap.parse_args(argv)

    city = cityconfig.use(args.city)
    runnable = B.runnable_targets(city)
    if str(args.target) not in runnable:
        raise SystemExit(
            f"--target {args.target} cannot be scored for {city.name}; "
            f"runnable targets are {', '.join(runnable)}.")
    M.apply_city(city)
    ctx = build_context(args.target, args.data_dir, args.overhang_rule)

    actual_seats, actual_winners = B.actual_result(
        args.data_dir / ctx.spec["actual"], ctx.council)

    print(f"benchmarks: {city.name} {args.target}  "
          f"(prior LGE {ctx.spec['prior_lge'].format(CODE=city.code)}, "
          f"council {ctx.council}, overhang rule {ctx.overhang_rule})")
    print(f"  actual: {sum(actual_seats.values())} seats to "
          f"{len(actual_seats)} parties; {len(actual_winners)} wards")

    names = sorted(BENCHMARKS) if args.benchmark == "all" else [args.benchmark]
    runs = {name: run_with_wards(name, ctx, args.draws, args.seed) for name in names}
    # A shared candidate universe, so every baseline's table lists parties in the
    # same order. It deliberately does *not* set the scored denominator: score.py
    # drops the columns where a baseline and the result are both zero, so each
    # baseline's numbers are identical whether it is run alone or in company.
    shared = S.relevant_parties([r[0] for r in runs.values()], actual_seats)

    summary = []
    for name in names:
        seat_draws, ward_draws = runs[name]
        seats = S.score_seats(seat_draws, actual_seats, seed=args.seed,
                              parties=shared)
        wards = S.score_wards(ward_probabilities(ward_draws), actual_winners)
        print()
        print(S.format_report(seats, wards, label=name))
        summary.append((name, seats, wards))

    if len(summary) > 1:
        # brier_multicategory, not brier_binary: the binary version's denominator
        # is the number of (ward, party) pairs each forecaster happened to
        # mention -- 138 for uniform-swing against 163 for prior-lge-noise at
        # 2016 -- so the two are not on the same base and the column would rank
        # by party universe as much as by skill. The multi-category form divides
        # by wards, which every forecaster has the same number of.
        print("\n  " + f"{'benchmark':18s}{'CRPS':>9s}{'energy':>9s}"
                       f"{'seatMAE':>9s}{'BrierMC':>9s}{'90% coverage':>15s}")
        for name, seats, wards in summary:
            cov90 = next(r for r in seats["coverage"] if r["level"] == 0.9)
            cov = f"{cov90['inside']}/{cov90['counted']} = {cov90['empirical']:.0%}"
            print(f"  {name:18s}{seats['crps']['total']:>9.2f}"
                  f"{seats['energy']:>9.2f}{seats['seat_mae_median']:>9.0f}"
                  f"{wards['brier_multicategory']:>9.4f}{cov:>15s}")
        print("  BrierMC = per-ward multi-category Brier (0 perfect, 2 confidently "
              "wrong); coverage denominators differ because each")
        print("  forecaster is scored only on parties it or the result put in the "
              "council — that is what makes the number roster-independent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
