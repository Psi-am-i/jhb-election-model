"""Every past election we can run, as votes and as seats, against every opponent.

``sweep.py`` answers "is anything obviously broken". This answers the question
that comes next: **how close was it, on what the ballots actually said.**

Three quantities per party, not one. Seats are a step function of votes through
a quota, so a forecast can be four seats out while being a tenth of a point out
on the ballot, or a tenth of a point out and four seats wrong. Reporting seats
alone hides which. So each table carries:

    list votes    the PR ballot, citywide share, predicted median vs actual
    ward votes    the ward ballot, citywide share, same
    seats         the combined-ballot council, same

and, since 2026-08-27, a fourth quantity that answers a question none of those
three can:

    ward winners  of the ~135 contests, how many the model called correctly

**It is here because the seat keys are structurally blind to geography.**
``solve_and_predict`` pins each party's realised citywide share to the share the
draw drew, and both ballots are ``weight @ pred`` against those pinned targets,
so ``dev``, ``gamma``, pool composition and the whole VD layer reach the seat
error ONLY through an overhang trigger. Any change to those, judged by seats
alone, is judged by an instrument that cannot see it — and returns a flat,
confident null that means nothing. See :func:`ward_winner_accuracy` and
``NULL-RESULTS.md``.

and each is scored against three opponents, all through ``score.py`` so nothing
is scored by different code:

    last-lge          "the last local election happens again"
    uniform-swing     that, shifted by the national movement bracketing it
    prior-lge-noise   that, with a spread from the previous transition
    published         the run recorded in data/processed/validation_<year>.json,
                      where one exists -- the model as it stood then, so a
                      change can be read as a change rather than asserted

It also reports **pooled calibration** -- coverage at 50/80/90 and the
randomised PIT histogram, summed over every city-year. Per city-year those are
noise (seven to fifteen scored columns), which is why they were never worth
printing and therefore never printed; pooled over nine they are ~130 columns and
they say something the rest of this report cannot: whether the intervals are the
right WIDTH and whether they are in the right PLACE. Those are different faults
with different remedies, and **this model's LEVEL differs by rank band while its
WIDTH does not** — over-forecast at ranks 1-3, under-forecast at ranks 4-12, and
intervals about 1.35x too wide in both — so the calibration is reported split by
actual PR rank as well as pooled. The pooled LEVEL is the average of two
opposite biases and describes neither.

**Width and level must be measured by different statistics, and this report was
twice wrong because they were not.** Coverage at one nominal level cannot tell a
narrow forecast from a shifted one; PIT variance against 1/12 cannot either, and
is not shift-invariant however often it is claimed to be. The width verdict here
comes from :func:`pit_dispersion` and :func:`dispersion_ratio`, which divide the
level out, corroborated by coverage read at all three levels at once. See
:func:`render_calibration`, :func:`pooled_by_band` and MODEL-LOG §1.34, §1.36,
§1.39.

Usage::

    python src/compare_history.py                    # everything runnable
    python src/compare_history.py --city joburg
    python src/compare_history.py --draws 2000 --md report.md
"""

from __future__ import annotations

import argparse
import ast
import datetime as _dt
import functools
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import sys
import zlib
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import backtest as B
import benchmarks as BM
import cityconfig
import levels
import montecarlo as M
# Imported here rather than only in ``__main__`` (where the artefact lock is
# taken) so that its module constants are inside the snapshot below: a module
# that arrives AFTER the snapshot has no recorded default and cannot be
# guarded. Costs ~50ms and pulls in nothing new — `montecarlo` imports it
# lazily on every run already.
import pools  # noqa: F401  (imported for the constant snapshot; see below)
import score as S
from fold import citywide, load

CITIES = ["joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "mangaung", "nelsonmandelabay", "buffalocity"]

# The three Gauteng metros. Here for ONE reason: the headline margin over
# uniform swing is not evenly spread and quoting the pooled figure alone is the
# strongest available criticism of it. See :func:`_headline_split`.
GAUTENG = frozenset({"joburg", "tshwane", "ekurhuleni"})


def runnable(city) -> tuple[list[str], list[tuple[str, str]]]:
    """Targets this city can actually run, AND why each other one cannot.

    **The reason half was added 2026-08-22 (MODEL-LOG §1.69), because the panel
    had been silently smaller than the archive for months.** `B.runnable_targets`
    reports what the ARCHIVE supports — 2011, 2016 and 2021 for all eight metros,
    24 city-years. This function reported nine, and the seven missing 2016
    targets were absent for TWO different reasons that looked identical from
    outside: no emitted pool spec, and no γ fold. Neither was stated anywhere.
    A city-year that quietly fails to appear is indistinguishable from one the
    archive cannot support, and `ITERATING.md`'s "when to stop" section
    concluded the model was finished partly on the strength of that number.

    Same shape as `polling.screen` (§1.68): a refusal is a returned reason, not
    a silent `continue`. The two reasons are very different in cost —

    * **no pool spec** — mechanical. `python src/pools.py --city X --target Y
      --emit`. This was the state of all seven 2016 targets until §1.69 emitted
      them, and it needed no new data at all.
    * **no γ fold** — blocked on the archive. A 2016 target needs a γ fold
      strictly preceding it, which is fold 3 (2009 NPE → 2011 LGE), which needs
      `npe2009` and `lge2006`. **Those exist for Johannesburg and for no other
      metro.** So this is the pre-2011 ingest `ITERATING.md` already names as
      the thing that would license restarting, and it cannot be worked around:
      fold 1 targets 2016 itself, so borrowing its γ is reading the answer.
    """
    out, refused = [], []
    for year in B.runnable_targets(city):
        if not (city.processed / f"pools_{year}.json").exists():
            hint = (" (NOTE: 2011 additionally needs the 2006 ward geography "
                    "to join the census, and it does not — `pools.py --city "
                    "joburg --target 2011 --emit` fails with 'no ward joined "
                    "the census'. Checked 2026-08-22, §1.69; do not spend a "
                    "second afternoon on it)" if year == "2011" else "")
            refused.append((year, f"no pool spec — run `src/pools.py --city "
                                  f"{city.slug} --target {year} --emit`{hint}"))
            continue
        fold = M.GAMMA_FOLD.get(year)
        if fold is not None and not (
                city.processed / f"fold{fold}_parameters.csv").exists():
            refused.append((year, f"no γ fold {fold} for this city; it needs "
                                  f"the pre-2011 archive, which exists only "
                                  f"for Johannesburg"))
            continue
        out.append(year)
    return out, refused


def actual_shares(target, data_dir: Path) -> tuple[dict, dict]:
    """The target's own citywide PR and ward shares. Scoring only."""
    path = data_dir / target.results(target.year)
    pr, _ = load(path, "PR")
    ward, _ = load(path, "Ward")
    return citywide(pr), citywide(ward)


def vote_table(run, actual_pr, actual_ward, top=12):
    """Per-party predicted vs actual on both ballots, MEAN AND MEDIAN.

    Both, because for this model they are not the same statement and the gap is
    the finding. A small party's share within a pool comes out of a Dirichlet
    whose concentration for that party is a fraction of one, which is a spike
    near zero with a long right tail: at Johannesburg 2021 the AIC's median
    predicted share is 0.11% and its mean 0.58%, a factor of five, and the
    actual was 0.69%. Reporting the median alone says the model missed the AIC
    by six-fold; reporting the mean alone says it was within 16%. Neither
    sentence is the whole truth and the distance between them is the story.
    """
    idx = run.index
    rows = []
    for party in sorted(actual_pr, key=lambda p: -actual_pr[p])[:top]:
        i = idx.get(party)
        if i is None:
            rows.append((party, float("nan"), float("nan"), actual_pr[party],
                         float("nan"), float("nan"),
                         actual_ward.get(party, 0.0)))
            continue
        pr, wd = run.pr_share_draws[:, i], run.ward_share_draws[:, i]
        rows.append((party,
                     float(np.median(pr)), float(pr.mean()), actual_pr[party],
                     float(np.median(wd)), float(wd.mean()),
                     actual_ward.get(party, 0.0)))
    return rows


# The rank bands, defined ONCE. Both the vote-error table and the calibration
# table split on these, and they must split identically or the two instruments
# can appear to disagree when they are only counting different parties.
BAND_LABELS = ("1-3", "4-12", "13+")


def rank_band_of(actual_pr) -> dict[str, str]:
    """``party -> rank band``, ranked by the party's ACTUAL citywide PR share.

    The single definition of the bands. :func:`rank_bands` splits the vote error
    on it and :func:`calibration_columns` splits the PIT and coverage on it, so
    "ranks 1-3 are over-forecast" means the same set of parties in both tables.
    That mattered: the two statistics were saying the same thing for months and
    it was impossible to see, because only one of them was disaggregated.
    """
    order = sorted(actual_pr, key=lambda p: -actual_pr[p])
    return {party: ("1-3" if i < 3 else "4-12" if i < 12 else "13+")
            for i, party in enumerate(order)}


def rank_bands(run, actual_pr, actual_seats):
    """Error by where a party sits on the ballot, which is where it fails.

    A single headline hides the shape of this model's error completely. Ranks
    1-3 are over-predicted and everything below is short, and the parties that
    matter for marginal seats are ranks 4-12: big enough to win one, small
    enough that a fraction of a point decides it.

    **SIGNED AND ABSOLUTE, and neither one alone.** The sign is a finding — it
    says one band is eating the other, which an unsigned figure cannot — but a
    signed sum is not a measure of error, because errors in opposite directions
    inside the same band cancel and the band then reports as accurate. This
    statistic shipped signed-only and hid the model's largest single failure:
    at **Johannesburg 2021 ranks 1-3 read +1.32pp signed against 26.50pp
    absolute**, because the ANC (+6.52) and the DA (+7.39) cancelled against
    ActionSA (−12.59). That city-year is the model's WORST on seats and read
    second-best on this table. Across the nine city-years the signed total for
    ranks 1-3 understates the absolute one by more than 2×.

    **NO NINE-CITY-YEAR FIGURE IS TYPED HERE, AND THAT IS DELIBERATE.** This is
    a Monte Carlo statistic that moves in the second decimal with the draw count
    and the seed, and it went stale in prose three times over. Three different
    values of the ranks 1-3 total once shipped inside a single commit —
    +32.67/72.06 in this docstring, +32.42/71.65 in MODEL-LOG §1.34's table,
    +32.50/71.12 in the artefact — all the same statistic at different draw
    counts, with no way for a reader to tell a re-run from a regression. The
    current values live in ONE place, the checked table in ``ITERATING.md``
    under rule 8, and
    ``tests/test_calibration_report.py::test_the_documented_figures_match_the_committed_artefact``
    fails the build when that table and ``data/processed/history.json`` disagree.
    Quote them from there. See MODEL-LOG §1.34, §1.36 and §1.39.

    **PHANTOM MASS.** The bands iterate the parties that actually stood, so any
    share the model gives to a party that did not stand at all is invisible to
    every band. It is reported separately rather than left out: the citywide
    share vector sums to one over the model's own universe, so the phantom total
    is exactly why the three signed bands sum to a negative number rather than
    to zero. It includes the generic ``ENTRANT`` column in a city-year where no
    party arrived, which is a real error and should be visible as one — and it
    is why the level gap between the bands is a **zero-sum transfer**: what
    ranks 1-3 and the phantom columns are given is what ranks 4-12 and 13+ lose.

    The band membership comes from :func:`rank_band_of`, which
    :func:`calibration_columns` also uses, so the vote table and the calibration
    table split the ballot the same way and can be read against each other.
    """
    membership = rank_band_of(actual_pr)
    bands = {label: [p for p, b in membership.items() if b == label]
             for label in BAND_LABELS}
    out = {}
    for label, parties in bands.items():
        signed = absolute = won = 0.0
        for party in parties:
            i = run.index.get(party)
            pred = float(run.pr_share_draws[:, i].mean()) if i is not None else 0.0
            signed += pred - actual_pr[party]
            absolute += abs(pred - actual_pr[party])
            won += actual_seats.get(party, 0)
        out[label] = {"n": len(parties), "signed_pp": 100 * signed,
                      "abs_pp": 100 * absolute, "seats_at_stake": won}
    ghosts = {}
    for party, i in (run.index.items() if run.pr_share_draws is not None else ()):
        if party in actual_pr:
            continue
        pred = float(run.pr_share_draws[:, i].mean())
        if pred > 0:
            ghosts[party] = 100 * pred
    out["phantom"] = {"n": len(ghosts), "pp": float(sum(ghosts.values())),
                      "top": sorted(ghosts.items(), key=lambda kv: -kv[1])[:5]}
    return out


# The nominal interval levels calibration is reported at. Three, not one:
# a model can be right at 90% and wrong at 50%, and one number cannot show it.
LEVELS = (0.5, 0.8, 0.9)

# The populations calibration is measured over, in the order they are printed.
# The difference between them IS the finding, so all four are reported and each
# is labelled with what selects it. See :func:`calibration_columns`.
POPULATIONS = ("reference", "claimed", "seat_holders", "all")

# WHAT PUTS A PARTY IN THE ``reference`` POPULATION. Both are ex-ante facts: a
# result already published when the forecast is made, and a nomination list that
# closes before polling day. Neither can move when a lever moves, which is the
# entire point — see :func:`reference_universe`.
#
# Both are DECLARED, not measured, and JUDGEMENT-CALLS.md carries them. The
# share cut sits below every metro's PR quota (Johannesburg's 270 seats put it
# near 0.37%), so no party that could take a PR seat on its previous showing is
# excluded. The slate cut is the weaker of the two and the one to argue with:
# a party can win a WARD seat with a single ward, so the honest threshold on
# that logic is "on the ballot at all" — which admits 24 to 57 parties a
# city-year, most of them zero on both sides, and reproduces exactly the
# dilution that makes ``all`` untestable. A quarter-slate is a judgement about
# plausibility, not a derivation. Sensitivity, summed over the nine city-years:
# 252 columns at 0.25, 232 at 0.50, 211 at 0.75.
REFERENCE_SHARE = 0.0025
REFERENCE_SLATE = 0.25

# Acklam's rational approximation to the inverse normal CDF, to about seven
# significant figures. Here to avoid a scipy dependency for the one transform
# that turns a PIT into a statistic a LEVEL SHIFT cannot fake -- see
# :func:`pit_dispersion`, which is the whole reason it exists.
_ACK_A = (-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
          1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00)
_ACK_B = (-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
          6.680131188771972e+01, -1.328068155288572e+01)
_ACK_C = (-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
          -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00)
_ACK_D = (7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
          3.754408661907416e+00)


def _probit(u):
    """``Phi^-1(u)``, vectorised, clipped away from 0 and 1.

    The clip matters: a randomised PIT can land exactly on 1.0 (five real
    columns do — parties given zero seats in every draw that nonetheless won
    one), and an infinity would make every statistic downstream ``nan``.

    ⛔ **THIS PARAGRAPH SAID THE CLIP IS NOT LOAD-BEARING AND THAT IT HAD BEEN
    CHECKED RATHER THAN ASSUMED. IT IS LOAD-BEARING, AND THE CHECK WENT STALE
    (2026-08-29, MODEL-LOG §1.132).** It claimed *"the `claimed` population
    carries no PIT at 0 or 1 (its range on the committed artefact is 0.052 to
    0.997)"*. **On the sixteen-city-year artefact the range is 0.0018 to exactly
    1.0** — ActionSA at Johannesburg 2021, a party given a seat in no draw that
    won 44 of them. One saturated column out of 48 is enough to move the
    TEST-GUARDED ranks 1-3 probit-SD by **17%**:

        clip      1e-4     1e-5     1e-6
        ranks 1-3   0.697    0.760    0.818     <- the figure `ITERATING.md`
                                                   rule 8's table pins
        reference 4-12, 7 saturated of 128:
                    1.140    1.224    1.305

    Ranks 4-12 on ``claimed`` has no saturated column and is genuinely clip-free
    at 0.820. So the statistic is stable exactly where it was checked and moves
    where it was not — which is the same shape of error as the check itself.

    **Quote the clip with the figure, or do not quote the figure.** And note the
    consequence for the disqualification below: sensitivity to the clip was the
    stated reason for calling the ``all`` population untrustworthy, and by that
    standard ranks 1-3 on ``claimed`` now fails the same test.

    It IS
    load-bearing for the ``all`` population, which has three columns at exactly
    1.0; that population is already labelled untrustworthy for other reasons
    (see :func:`calibration_columns`) and its width figure should not be quoted
    either.
    """
    p = np.clip(np.asarray(u, dtype=float), 1e-6, 1 - 1e-6)
    out = np.empty_like(p)
    lo, hi = p < 0.02425, p > 1 - 0.02425
    mid = ~(lo | hi)
    q = np.sqrt(-2 * np.log(p[lo]))
    out[lo] = ((((((_ACK_C[0] * q + _ACK_C[1]) * q + _ACK_C[2]) * q + _ACK_C[3])
                 * q + _ACK_C[4]) * q + _ACK_C[5])
               / ((((_ACK_D[0] * q + _ACK_D[1]) * q + _ACK_D[2]) * q
                   + _ACK_D[3]) * q + 1))
    q = np.sqrt(-2 * np.log(1 - p[hi]))
    out[hi] = -((((((_ACK_C[0] * q + _ACK_C[1]) * q + _ACK_C[2]) * q + _ACK_C[3])
                  * q + _ACK_C[4]) * q + _ACK_C[5])
                / ((((_ACK_D[0] * q + _ACK_D[1]) * q + _ACK_D[2]) * q
                    + _ACK_D[3]) * q + 1))
    q = p[mid] - 0.5
    r = q * q
    out[mid] = (((((_ACK_A[0] * r + _ACK_A[1]) * r + _ACK_A[2]) * r + _ACK_A[3])
                 * r + _ACK_A[4]) * r + _ACK_A[5]) * q / (
        ((((_ACK_B[0] * r + _ACK_B[1]) * r + _ACK_B[2]) * r + _ACK_B[3]) * r
         + _ACK_B[4]) * r + 1)
    return out


def pit_dispersion(pits) -> float:
    """Width, with the LEVEL divided out: ``sd(Phi^-1(u))``. **1.0 is right.**

    Below 1.0 the intervals are too WIDE; above 1.0 too narrow. The ratio is
    read directly: 0.73 means the intervals are about ``1/0.73 = 1.4x`` wider
    than the errors they are meant to cover.

    **This exists because the obvious dispersion statistic is not one.** PIT
    variance against a nominal ``1/12`` was proposed three times on this project
    as "shift-invariant, so a clean width statistic". It is not shift-invariant
    and it is not clean. A PIT lives on ``[0, 1]``; move the forecast off centre
    and its mass piles against a boundary, and the variance falls whatever the
    width is. On the suite's own fixture — ``_shift_scale_results(4242, 12,
    width_mult=1.0, shift=S)`` in ``tests/test_calibration_report.py``, whose
    forecast width is EXACTLY right — PIT variance reads **0.0829, 0.0450 and
    0.0240** at shifts of 0, +2 and +3 seats against the nominal 0.0833: a pure
    level error reading as a 3.5x under-dispersion.
    ``test_pit_variance_is_not_a_width_statistic`` holds that fixture.

    The probit transform is the fix, because under a location shift of a roughly
    normal forecast ``Phi^-1(u)`` TRANSLATES: the shift lands in the mean and
    leaves the spread alone. On the same three runs the probit sd reads 1.021,
    0.917 and 0.953 against a true 1.000 — attenuated by a few points at a large
    shift, against a factor of 3.5 for the variance.

    It is not exact, and the residual attenuation is conservative in the
    direction that matters here: a band that is both shifted and too wide will
    read slightly LESS wide than it is, so an over-width verdict from this
    statistic understates rather than manufactures the fault.

    :func:`dispersion_ratio` is the exact version and needs the draws.
    """
    u = np.asarray(pits, dtype=float)
    if u.size < 2:
        return float("nan")
    return float(_probit(u).std(ddof=1))


def dispersion_ratio(z) -> float:
    """The exact level-free width statistic: ``sd`` of the standardised error.

    ``z_i = (truth_i - mean_i) / sd_i`` per column, from the draws themselves.
    Its **standard deviation** is the ratio of the errors' spread to the spread
    the forecast claimed: 1.0 is right, above 1.0 too narrow, below 1.0 too
    wide. Subtracting the mean is what makes it exactly invariant to a level
    shift — the mean is the level statistic and is reported next to it, not
    inside it.

    Exact where :func:`pit_dispersion` is approximate: on the fixture above it
    reads **1.000 at shifts of 0, +2 and +3 seats** — unmoved to the third
    decimal — and 0.650 when the forecast is widened by 1.6x, which is 1/1.54.
    Requires ``z`` in the artefact, which :func:`calibration_columns`
    stores; an artefact written before that returns ``nan`` rather than a wrong
    number.
    """
    v = np.asarray([x for x in z if x is not None and x == x], dtype=float)
    if v.size < 2:
        return float("nan")
    return float(v.std(ddof=1))


def _pit_seed(city_slug: str, year: str, base: int = 20211101) -> int:
    """A per-city-year seed for the PIT randomisation, derived deterministically.

    ``score.pit_values`` draws one uniform per column from a fresh generator, so
    with the module default every city-year gives its k-th column the SAME
    uniform. Nine city-years pooled would then share nine draws rather than
    carry ~130 independent ones, and a single unlucky value would tilt the
    pooled histogram. Varying the seed per city-year removes that; deriving it
    from the name rather than a counter keeps the report reproducible and
    independent of which cities were run.
    """
    return base + zlib.crc32(f"{city_slug}:{year}".encode()) % 100_000


def reference_universe(target, city, data_dir: Path) -> list[str]:
    """The calibration population, selected on INPUTS ONLY.

    A party is in if it has a record — at least ``REFERENCE_SHARE`` of the
    combined ward+PR vote at the PREVIOUS local election — or a slate, standing
    in at least ``REFERENCE_SLATE`` of this election's wards. Both are known
    before polling day: the first is a published result, the second is a
    nomination fact (:func:`levels.contestation` reads row EXISTENCE, not
    ``Party_Votes``, for exactly this reason).

    **Why a fourth population exists at all.** The other three are each selected
    by something that moves when the model moves. ``claimed`` is the worst
    offender and it is the one the project quotes: its membership is
    ``(samples > 0).mean() >= CLAIM_FRACTION``, a function of the forecaster's
    own draws, so *narrowing the model admits columns* — a tighter draw puts a
    party whose mean clears the threshold into nearly every draw instead of
    into some of them. Measured at 1500 draws across a ``dirichlet_scale``
    sweep, the ``claimed`` set runs 58 / 67 / 81 columns at 0.5 / 1.0 / 2.0,
    and 30 / 37 / 45 of those are ranks 4-12. That is not a calibration
    statistic changing; it is the denominator changing underneath one.

    The consequence was a published conclusion. MODEL-LOG §1.55 read the two
    rank bands wanting different widths — 4-12 at scale 2.0, 1-3 at 1.0 — and
    the whole "a scalar cannot serve both bands" finding rests on it. Held
    fixed, ranks 1-3 are unchanged (the same 27 columns, always claimed) and
    **ranks 4-12 reverse**: `sd(z)` 1.553 / 1.940 / 2.267 against ``claimed``'s
    0.612 / 0.823 / 0.916, so the band is far too NARROW and raising the scale
    makes it worse. §1.56.

    Selection on the forecast is NEUTRAL — the docstring in
    :func:`score.score_seats` is right that PIT uniformity survives it, and that
    argument is about ONE forecaster. A lever sweep is a comparison ACROSS
    forecasters, and there the criterion is not neutral, because the population
    it admits is not the same population. Both facts are true; only the first
    was written down.

    **The price is dilution, and it is paid deliberately.** A fixed population
    must contain columns that are zero on both sides — nobody can know ex ante
    which parties will matter — and such a column is an interval [0, 0]
    containing 0: a free coverage hit and a near-uniform PIT. So ``reference``
    coverage and PIT read optimistically by construction and are NOT the
    figures to quote for calibration in absolute terms. What it is for is
    COMPARISON: the dilution is identical at every lever setting, so a
    difference between two settings is a real difference. Quote ``claimed`` for
    "is this model calibrated"; quote ``reference`` for "did that change help".

    ``sd(z)`` is the statistic this population was built to serve, and it is
    largely immune to the dilution above: a column whose draws are all zero has
    no scale and stores ``None`` rather than an infinity, so it drops out of the
    width figure without being selected out of the population.
    """
    universe: set[str] = set()
    previous = target.previous_lge
    if previous:
        path = data_dir / target.results(previous)
        if cityconfig.resolve_path(path).exists():
            for party, share in citywide(load(path, None)[0]).items():
                if share >= REFERENCE_SHARE:
                    universe.add(party)
    for party, fraction in levels.contestation(target, city).items():
        if fraction >= REFERENCE_SLATE:
            universe.add(party)
    return sorted(universe)


def _p_any(samples) -> list[float]:
    """Per column, the fraction of draws giving the party at least one seat.

    **The quantity a zero-probability failure must be measured on**, and the
    reason it is stored rather than derived later: "the truth exceeded every
    draw" is not a property of the forecast, it is a property of the forecast
    AND the draw count. At 600 draws six columns on this panel carry PIT 1.0
    and the parties in them won 19 seats; **at 1500 draws it is four columns
    and four seats**, because the PA at Johannesburg 2021 (8 seats) and the
    Cape Coloured Congress at Cape Town (7) fall inside the sample once there
    are enough draws to reach their tail. Nothing about the model changed.

    A gate written on the binary therefore tightens as you sample less, which
    is the wrong way round. ``p_any`` is stable: it estimates
    ``P(at least one seat)``, and the failure to gate on is a party that won
    seats while the model gave it a probability below some stated threshold —
    which is also exactly what the publication gate asks for
    (``PUBLISHING-BACKLOG.md`` §5b item 1, threshold 0.02).
    """
    if samples.ndim != 2 or samples.shape[0] == 0:
        return []
    return [float(v) for v in (samples > 0).mean(axis=0)]


def _population_block(parties, samples, truth, *, seed, membership) -> dict:
    """One population's calibration block, computed from its own matrix.

    Only ``reference`` uses this. The other three are masks over a single
    shared matrix and are computed inline in :func:`calibration_columns`,
    which duplicates the arithmetic below — deliberately. The randomised PIT
    consumes one uniform per column from a seeded generator, so computing a
    population from a SLICED matrix and from a MASK over the full matrix give
    different values for the same column. Routing the existing three through
    here would silently re-record every calibration number in the artefact to
    buy tidiness. Change either and the other is not affected. Both paths are
    tested: ``test_the_documented_figures_match_the_committed_artefact``
    covers the inline three against the artefact, and
    ``test_the_reference_population_is_fixed_and_keeps_the_worst_columns``
    covers this one.
    """
    n_cols = samples.shape[1] if samples.ndim == 2 else 0
    pits = (S.pit_values(samples, truth, parties, seed=seed)
            if samples.shape[0] else [])
    # THE JUMP EACH PIT LANDS INSIDE, stored beside the PIT itself. It carries
    # no randomness, and with it every PIT statistic is recoverable at any
    # number of randomisations without re-running the model. The seed band that
    # motivated this change was measurable at all only because the jumps
    # happened to be recoverable from a lattice (both are multiples of 1/draws)
    # — luck that does not survive a change of draw count. See
    # `score.pit_intervals`.
    pit_lo, pit_w = (S.pit_intervals(samples, truth) if samples.shape[0]
                     else ([], []))
    hits, z_cols = [], []
    for j in range(n_cols):
        hits.append([int(row["inside"])
                     for row in S.coverage(samples[:, [j]], truth[[j]], LEVELS)])
        col = samples[:, j].astype(float)
        sd = float(col.std(ddof=1)) if col.size > 1 else 0.0
        z_cols.append(float((truth[j] - col.mean()) / sd) if sd > 0 else None)
    return {
        "n": int(n_cols),
        "parties": list(parties),
        "pit": [float(v) for v in pits],
        "pit_lo": [float(v) for v in pit_lo],
        "pit_w": [float(v) for v in pit_w],
        "pit_seed": int(seed),
        "z": z_cols,
        "p_any": _p_any(samples),
        "band": [membership.get(p, "off-ballot") for p in parties],
        "hits": hits,
        "coverage": S.coverage(samples, truth, LEVELS),
    }


def calibration_columns(seat_draws, actual_seats, entrant_actual, seed,
                        actual_pr=None, reference=None):
    """Per-column PIT values and interval hits, UNPOOLED, for one city-year.

    Kept unpooled because per city-year these numbers are noise and pooling them
    is the whole point: Johannesburg 2021 reads 12/62/75 against nominal
    50/80/90 on n=8 columns and Cape Town 2021 reads 43/100/100 on n=7. Neither
    says anything. Summed over nine city-years (n≈132 seat-holding columns) they
    say something the rest of the report cannot — see :func:`pooled_calibration`
    and MODEL-LOG §1.34, §1.36.

    **The per-column band label is why ``actual_pr`` is here.** A pooled mean PIT
    over a population that contains two opposite biases is the same mistake as a
    signed error sum over a band that contains two opposite errors: it averages
    them and reports "fine". On the committed sixteen city-years this model's
    ``claimed`` population pools to **0.559** and is **+0.010 at ranks 1-3 and
    +0.113 at ranks 4-12** (updated 2026-08-31; the nine-city-year figures
    0.587 / −0.069 / +0.250 that stood here are superseded, and the ranks 1-3
    sign has flipped — see :func:`pooled_by_band`). Every block below
    therefore carries ``band`` alongside ``pit``, from :func:`rank_band_of` —
    the same partition :func:`rank_bands` splits the vote error on. Without
    ``actual_pr`` no column can be ranked and the pooled figure is all there is,
    which is the state that shipped.

    Three populations, because which columns you count changes the answer and
    the difference between them is itself informative:

    ``claimed``       columns this forecaster gives a seat in at least
                      ``score.CLAIM_FRACTION`` of its draws. Selection depends on
                      the FORECAST alone, so PIT uniformity survives it; this is
                      the neutral test and the one to quote.
    ``seat_holders``  columns that actually won a seat. Selection depends on the
                      OUTCOME, and zero is the bottom of the support, so under
                      perfect calibration the survivors are U(p₀, 1) rather than
                      uniform — this population reads high even for a flawless
                      forecaster and is INFLATED by construction. Reported
                      because it is the population a reader assumes, and because
                      it is what an outside reviewer computed.
    ``all``           every scored column, and **not the neutral set it was
                      documented as.** ``score.seat_matrix`` admits a column when
                      ``truth[i] > 0 or samples[:, i].max() > 0``: the first
                      clause lets a party in *because it won a seat*, which is
                      outcome selection, and the second lets one in on the
                      forecast, which is not. It is a MIXTURE of a neutral set
                      and an outcome-selected one. The outcome-selected part is
                      not hypothetical — five of its 331 columns across the nine
                      city-years carry PIT exactly 1.0 (Johannesburg 2016
                      ALJAMAAH, Johannesburg 2021 PA, eThekwini 2021
                      MINORITIES_OF_SOUTH_AFRICA, Cape Town 2021
                      CAPE_MUSLIM_CONGRESS and DEMOCRATIC_INDEPENDENT_PARTY),
                      parties the model gave zero seats in every single draw and
                      which are in the population only because they won. It is
                      also diluted by the ~200 parties correctly at zero on both
                      sides, each a free interval hit and a near-uniform PIT.
                      Both effects are real and they push opposite ways, so
                      ``all`` is not a test of anything: quote ``claimed``.
                      ``score.py`` is deliberately not changed — the admission
                      rule is right for CRPS, which is what it exists for.

    Nothing here is reimplemented: the matrix, the randomised PIT and the
    coverage all come from ``score.py``, so the pooled figures and a single
    run's report cannot drift apart. The per-column interval hits are
    ``score.coverage`` called on one column at a time, for the same reason.
    """
    parties, samples, truth = S.seat_matrix(seat_draws, actual_seats,
                                            entrant_actual)
    pits = S.pit_values(samples, truth, parties, seed=seed)
    all_lo, all_w = S.pit_intervals(samples, truth)
    n_cols = samples.shape[1] if samples.ndim == 2 else 0
    claimed = ((samples > 0).mean(axis=0) >= S.CLAIM_FRACTION
               if samples.shape[0] else np.zeros(n_cols, dtype=bool))
    masks = {"claimed": claimed,
             "seat_holders": truth > 0,
             "all": np.ones(n_cols, dtype=bool)}
    # ``reference`` is a DIFFERENT MATRIX, not another mask over this one, and
    # it has to be: the matrix above drops a column that is zero on both sides,
    # so a mask over it would still be missing every reference party the
    # forecaster happened to give nothing to — the forecast-dependence coming
    # straight back in through the universe after being shut out of the mask.
    # ``keep_all`` with an explicit ``parties`` is the only way to score a
    # genuinely fixed column set. See :func:`reference_universe`.
    ref = tuple(reference or ())
    membership = rank_band_of(actual_pr or {})
    # Per-column hits, so a pooled figure can be recomputed over ANY subset of
    # columns later. score.coverage returns aggregates, and an aggregate cannot
    # be disaggregated — which is exactly how the rank split came to be
    # impossible to make without re-running the whole nine city-years.
    hits = [[int(row["inside"])
             for row in S.coverage(samples[:, [j]], truth[[j]], LEVELS)]
            for j in range(n_cols)]
    # The standardised error per column, ``(truth - mean) / sd`` of the draws.
    # Stored because it is the ONLY statistic here that separates width from
    # level exactly (:func:`dispersion_ratio`), and it cannot be recovered from
    # the PIT afterwards -- which is how the width question came to be answered
    # three times from statistics that could not answer it. A column whose draws
    # are all identical has no scale and stores ``None`` rather than an
    # infinity.
    z_cols: list[float | None] = []
    for j in range(n_cols):
        col = samples[:, j].astype(float)
        sd = float(col.std(ddof=1)) if col.size > 1 else 0.0
        z_cols.append(float((truth[j] - col.mean()) / sd) if sd > 0 else None)
    out = {}
    for name in POPULATIONS:
        if name == "reference":
            out[name] = _population_block(
                *S.seat_matrix(seat_draws, actual_seats, entrant_actual,
                               keep_all=True, parties=ref),
                seed=seed, membership=membership)
            continue
        mask = masks[name]
        out[name] = {
            "n": int(mask.sum()),
            "parties": [p for p, keep in zip(parties, mask) if keep],
            "pit": [float(v) for v in np.asarray(pits)[mask]],
            # sliced alongside the PIT, so a masked population can be re-drawn
            # exactly as the reference one can. See `score.pit_intervals`.
            "pit_lo": [float(v) for v in np.asarray(all_lo)[mask]],
            "pit_w": [float(v) for v in np.asarray(all_w)[mask]],
            "pit_seed": int(seed),
            "z": [v for v, keep in zip(z_cols, mask) if keep],
            "p_any": _p_any(samples[:, mask]),
            # ``off-ballot`` is a column with no actual PR rank: a party the
            # model gave seats to that contested nothing. It is the calibration
            # counterpart of rank_bands' phantom mass and is kept out of the
            # three bands rather than swept into 13+.
            "band": [membership.get(p, "off-ballot")
                     for p, keep in zip(parties, mask) if keep],
            "hits": [h for h, keep in zip(hits, mask) if keep],
            "coverage": S.coverage(samples[:, mask], truth[mask], LEVELS),
        }
    return out


def redraw_pits(block: dict, replicates: int = 64):
    """PIT values redrawn ``replicates`` times from the stored jump intervals.

    Returns ``(array_of_shape_(R, n), exact)``. ``exact`` is False when the
    block predates ``pit_lo``/``pit_w``, in which case the stored single
    randomisation is returned unchanged as one replicate — **and the caller must
    say so**, because a silent fallback to R=1 is a guard that reads as working.

    ⛔ **AVERAGE THE STATISTIC, NEVER THE VALUES.** Averaging PIT values first
    shrinks each draw toward its jump midpoint: measured at R=64 on
    ``reference`` that reads probit-SD **1.01 ("correct")** where the honest
    figure is **1.20 ("too narrow")**, and 50% coverage 0.76 against 0.53. It
    would have inverted this project's width verdict.

    Why this exists: the randomisation alone moved the pooled mean PIT with
    sd 0.00955 on ``reference``, and moved the statistic Key 2 quotes as its
    width floor — ``reference``/2021 probit-SD, n=235, reading exactly 1.2000 —
    with sd **0.0327**. The 1.2000 → 1.3557 finding built on that floor is
    therefore **3.4 sd of a paired re-roll**. Key 2 is untradeable; a floor that
    moves 0.03 while the model stands still is not a floor. At R=64 the residual
    is 0.0040 and the same finding is 27 sd.
    """
    import numpy as _np
    pit = _np.asarray(block.get("pit") or [], dtype=float)
    lo = block.get("pit_lo")
    w = block.get("pit_w")
    if not lo or not w or len(lo) != len(pit):
        return pit.reshape(1, -1), False
    lo = _np.asarray(lo, dtype=float)
    w = _np.asarray(w, dtype=float)
    seed = int(block.get("pit_seed") or 0)
    R = max(1, int(replicates))
    out = _np.empty((R, len(lo)), dtype=float)
    for j, party in enumerate(block.get("parties") or []):
        rng = S.column_rng(seed, party)  # ONE definition; see score.column_rng
        out[:, j] = lo[j] + rng.random(R) * w[j]
    return out, True


def exact_mean_pit(block: dict) -> float:
    """The mean PIT over the randomisation, in closed form: ``mean(lo + w/2)``.

    Zero randomisation noise, no replicates needed. The randomised PIT is
    uniform on ``[lo, lo+w]``, so its expectation is the midpoint and the mean
    of the midpoints is the exact expected mean PIT. Returns ``nan`` on a block
    that predates the stored intervals rather than silently returning the
    single-draw figure, which is a different quantity.
    """
    lo, w = block.get("pit_lo"), block.get("pit_w")
    if not lo or not w:
        return float("nan")
    return float(np.mean(np.asarray(lo) + np.asarray(w) / 2.0))


def pooled_calibration(results, bins: int = 10,
                       replicates: int = 64) -> dict:
    """Coverage and PIT summed over every city-year, pooled AND split by rank.

    Coverage pools by adding hits and columns; PIT pools by concatenating the
    values, because each column is one draw from what should be U(0,1) whatever
    city-year it came from. A per-city-year figure on seven to fifteen columns
    cannot separate 50% from 80%; the pooled one on ~130 can.

    **The pooled figure must not be read alone, and the ``by_band`` block is
    why.** Pooling over city-years is what makes the statistic readable;
    pooling over rank bands is what makes it wrong. On the committed sixteen
    city-years this model's ``claimed`` population pools to a mean PIT of
    **0.559** and splits into **0.510 at ranks 1-3 and 0.613 at ranks 4-12**.
    The point stands — the pooled figure hides the split — but the SHAPE has
    changed since the nine-city-year reading quoted here (0.587 / 0.431 /
    0.750): ranks 1-3 is now centred, and the whole departure is the middle.
    See :func:`pooled_by_band` and MODEL-LOG §1.36, §1.146.
    """
    out = {}
    for pop in POPULATIONS:
        pits: list[float] = []
        cov: dict[float, dict] = {}
        # R-AVERAGED PIT, and a flag saying whether it really is. `redraw_pits`
        # needs the stored jump intervals; a block written before they existed
        # returns its single stored randomisation and `exact=False`, and that
        # must be REPORTED rather than quietly averaged over one replicate.
        reps: list[np.ndarray] = []
        exact_all = True
        for r in results:
            block = (r.get("calibration") or {}).get(pop)
            if not block:
                continue
            pits.extend(block["pit"])
            drawn, exact = redraw_pits(block, replicates=replicates)
            reps.append(drawn)
            exact_all = exact_all and exact
            for row in block["coverage"]:
                acc = cov.setdefault(float(row["level"]),
                                     {"inside": 0, "counted": 0})
                acc["inside"] += int(row["inside"])
                acc["counted"] += int(row["counted"])
        # The mean PIT over R randomisations, and — where the intervals are
        # stored — its exact closed form, which needs no replicates at all.
        wide = (np.hstack(reps) if reps and exact_all
                else np.array(pits, dtype=float).reshape(1, -1))
        # ⛔ POOLED OVER COLUMNS, matching `mean_pit_r`. This averaged
        # per-city-year means until 2026-08-31 — a DIFFERENT ESTIMAND, and on
        # the committed panel it differed from the pooled figure by 0.0168 on
        # `seat_holders`, which is 4.2x the 0.0040 residual this whole change
        # exists to remove. A weighting difference introduced while removing a
        # smaller noise term is the change defeating its own purpose.
        mids: list[float] = []
        for r in results:
            b = (r.get("calibration") or {}).get(pop)
            if not b or not b.get("pit_lo") or not b.get("pit_w"):
                continue
            mids.extend(np.asarray(b["pit_lo"], dtype=float)
                        + np.asarray(b["pit_w"], dtype=float) / 2.0)
        exact_mean = float(np.mean(mids)) if (exact_all and mids) else float("nan")
        out[pop] = {
            "n": len(pits),
            "pit": S.pit_histogram(np.array(pits, dtype=float), bins=bins),
            "pit_replicates": int(wide.shape[0]),
            "pit_randomisation_exact": bool(exact_all),
            "mean_pit_r": float(np.mean(wide)),
            "mean_pit_exact": exact_mean,
            "pit_dispersion_r": float(np.mean(
                [pit_dispersion(list(row)) for row in wide])),
            "coverage": [
                {"level": level, "inside": acc["inside"],
                 "counted": acc["counted"],
                 "empirical": (acc["inside"] / acc["counted"]
                               if acc["counted"] else float("nan"))}
                for level, acc in sorted(cov.items())],
            "by_band": pooled_by_band(results, pop),
        }
    return out


def _cluster_bootstrap_ci(groups, level=0.95, draws=20_000, seed=20260817):
    """A CI for a pooled mean, resampling CITY-YEARS rather than columns.

    Columns inside one city-year are not independent — they share a turnout
    draw, a pool structure and a national swing — so a naive column bootstrap
    would give an interval far too tight. The city-year is the cluster, and
    with nine of them the interval is wide and honest rather than narrow and
    wrong.

    ``draws`` and ``seed`` are literals in this signature rather than module
    constants on purpose. They are run control — how the CI is estimated, not
    what the model believes — and a numeric module constant is either a
    judgement that must be registered or a default-argument capture that freezes
    at import; this is neither. The seed is fixed because a CI that moves
    between two runs of the same data is a figure nobody can quote. The
    replicate count is returned with the result so the report can state it
    without a figure being typed into prose.

    Returns ``(lo, hi, draws)``, or ``(nan, nan, draws)`` when fewer than two
    clusters carry any value.

    The replicate mean is computed from per-cluster SUMS and SIZES rather than
    by concatenating the clusters, which is the same number — the mean of a
    concatenation is the total over the count — and turns 20,000 Python-level
    concatenations into two array reductions. That matters now: intervals are
    put on every coverage row as well as on the mean PIT, so this is called
    about sixty times per report rather than three.
    """
    groups = [np.asarray(g, dtype=float) for g in groups if len(g)]
    if len(groups) < 2:
        return float("nan"), float("nan"), draws
    rng = np.random.default_rng(seed)
    k = len(groups)
    sums = np.array([g.sum() for g in groups], dtype=float)
    sizes = np.array([g.size for g in groups], dtype=float)
    pick = rng.integers(0, k, size=(draws, k))
    means = sums[pick].sum(axis=1) / sizes[pick].sum(axis=1)
    lo, hi = np.percentile(means, [100 * (1 - level) / 2,
                                   100 * (1 + level) / 2])
    return float(lo), float(hi), draws


def _band_splits(detail) -> dict:
    """The four things that must travel with any width figure. §1.134.

    **1. PER CYCLE.** A width pooled over two cycles that disagree in SIGN is
    the error that produced §1.131's wrong answer and `ITERATING.md` rule 8's
    false claim to have replicated out of sample. On `reference` ranks 4-12 the
    pooled `sd(z)` is 1.796 and the halves are **0.485 at 2016 and 2.262 at
    2021**; the signed vote error is −0.04pp against −26.07pp. **Never quote the
    pooled figure without the pair.** Eight metros inside one cycle share a
    national swing, so a within-cycle figure is optimistic too — rule 11.

    **2. LEVERAGE.** The share of Σ(z−z̄)² carried by the largest two and three
    columns. At `reference` ranks 4-12 the top two carry **69.9%** — Cape Town's
    Cape Coloured Congress and Johannesburg's PA — and dropping them takes
    `sd(z)` from 1.796 to 0.981. One line here would have stopped a session's
    worth of wrong conclusions.

    **3. BY `p_any`.** Whether the model gives the column a seat in at least half
    its draws is a property of the FORECAST, not the outcome, so splitting on it
    is not selection on the answer — unlike the rank band itself, which
    `rank_band_of` assigns by ACTUAL share. `p_any ≥ 0.5` is exactly the
    `claimed` population; the two halves read 0.857 and 2.303.

    **4. PIT SATURATION AND THE CLIP.** `_probit`'s docstring asserted the clip
    was not load-bearing and that this had been "checked rather than assumed".
    The check went stale: one saturated column moves the TEST-GUARDED ranks 1-3
    figure **0.697 → 0.818** across clips 1e-4 to 1e-6. A band carrying a PIT at
    0 or 1 has an **unquotable** probit-SD, by the same rule `_probit` already
    applies to the `all` population — so it is marked, not silently printed.
    """
    def _stats(rows):
        z = np.array([v for _y, v, _u, _p in rows if v is not None], dtype=float)
        if z.size < 2:
            return {"n": int(z.size), "sd_z": float("nan"),
                    "z_bias": float("nan")}
        return {"n": int(z.size), "sd_z": float(z.std(ddof=1)),
                "z_bias": float(z.mean())}

    cycles = sorted({y for y, _z, _u, _p in detail})
    z = np.array([v for _y, v, _u, _p in detail if v is not None], dtype=float)
    lev = {}
    if z.size > 3:
        dev = np.sort((z - z.mean()) ** 2)[::-1]
        total = float(dev.sum()) or float("nan")
        lev = {"top2": float(dev[:2].sum() / total),
               "top3": float(dev[:3].sum() / total),
               "sd_z_drop2": float(np.sort(np.abs(z - z.mean()))[:-2].size > 1
                                   and np.delete(z, np.argsort(
                                       -np.abs(z - z.mean()))[:2]).std(ddof=1)
                                   or float("nan"))}
    pits = np.array([u for _y, _z, u, _p in detail if u is not None], dtype=float)
    saturated = int(((pits <= 0.0) | (pits >= 1.0)).sum()) if pits.size else 0
    clips = {}
    for c in (1e-4, 1e-5, 1e-6):
        if pits.size > 1:
            v = np.array([_probit(x) for x in np.clip(pits, c, 1 - c)])
            clips[f"{c:g}"] = float(v.std(ddof=1))
    return {
        "by_cycle": {y: _stats([d for d in detail if d[0] == y]) for y in cycles},
        "leverage": lev,
        "by_p_any": {
            "ge_half": _stats([d for d in detail
                               if d[3] is not None and d[3] >= 0.5]),
            "lt_half": _stats([d for d in detail
                               if d[3] is not None and d[3] < 0.5])},
        "pit_saturated": saturated,
        "probit_by_clip": clips,
        # ⛔ A band with a saturated PIT has an unquotable probit-SD. Not a
        # warning in prose — a field, so a consumer must look at it.
        "probit_quotable": saturated == 0,
    }


def pooled_by_band(results, pop) -> dict:
    """The pooled calibration of one population, SPLIT BY ACTUAL PR RANK.

    **This is the fix for the fault that shipped, and it is worth stating
    plainly why the split is not optional.** A pooled mean PIT is an average
    over columns. If the population contains two subsets biased in opposite
    directions, the average sits between them and reports something close to
    0.5 — "well centred" — while neither subset is. That is precisely the
    argument that condemned :func:`rank_bands`' signed sum one day earlier, and
    the pooled PIT shipped in the same commit with the same defect.

    ⛔ **RE-MEASURED 2026-08-31 ON THE COMMITTED SIXTEEN CITY-YEARS, AND HALF OF
    WHAT THIS DOCSTRING SAID IS NO LONGER TRUE.** The figures below stood here as
    "committed ``history.json``" while the artefact had grown from nine
    city-years to sixteen, and nothing checked them — the guard on rule 8's
    tables in ``ITERATING.md`` parses those tables only, not this docstring.

    ==================  ==========================  ==========================
    population/band     was (9 city-years)          is (16, cluster-bootstrap)
    ==================  ==========================  ==========================
    claimed, pooled     0.598                       0.559
    claimed, ranks 1-3  n=27, 0.434                 n=48, **0.510** [0.474, 0.542]
    claimed, ranks 4-12 n=28, 0.757                 n=57, **0.613** [0.537, 0.683]
    ==================  ==========================  ==========================

    **The ranks 1-3 finding is REFUTED.** Its CI now contains 0.50, and the two
    cycles have opposite signs (2016 0.554, 2021 0.465), so it does not
    replicate. The model does **not** over-forecast the top three on this panel,
    and the "two biases in opposite directions" reading must not be quoted.

    **The ranks 4-12 finding survives and strengthens.** On the ``reference``
    population — the one Key 2 makes an untradeable floor — it is **0.688,
    CI [0.634, 0.735], replicating across cycles at 0.623 (2016) and 0.745
    (2021)**. On ``claimed`` it is 0.613 with the CI excluding 0.50, but it does
    NOT replicate by cycle there (2016 0.512, 2021 0.687), so quote the
    ``reference`` reading and say which population it is.

    So the surviving claim is one bias, not two: **the mid-ballot is
    under-forecast.** The signed vote bands (+32.52pp at ranks 1-3, −37.18pp at
    4-12) are a separate instrument and are not corroborated at ranks 1-3 by
    this one — but the seat PIT has little power to see 0.26pp per party per
    city-year, so this is not evidence against the vote finding either. MODEL-LOG
    §1.146.

    **WIDTH DOES NOT SPLIT THE SAME WAY, AND THIS PROJECT GOT THAT BACKWARDS
    TWICE IN TWO DAYS.** First it read "roughly the right width, do not widen".
    Then it read the 50% column alone, saw 0.27 at ranks 4-12, and concluded
    "too narrow, widen the middle" — into ``ITERATING.md`` rule 8. Both are
    wrong, and in opposite directions. What the artefact actually says at ranks
    4-12, PIT-corrected:

        50% covers 0.32     80% covers 0.89     90% covers 0.96

    **A forecast that is too narrow under-covers at EVERY level.** This one
    over-covers at 80 and at 90, by 9 and 6 points. The low 50% is not a width
    reading at all: with a mean PIT of 0.757 the whole distribution has been
    pushed off centre, and a shifted forecast vacates the middle of its own
    interval however wide it is. On the suite's fixture with EXACTLY correct
    width and a pure +2-seat shift the same code returns 0.27 / **0.56** /
    **0.76** — the 50% falls, and the 80 and 90 fall WITH it. Widen that same
    forecast by 1.6x and it returns 0.44 / **0.86** / **0.94**, which is where
    the model sits. Only excess width lifts 80 and 90 above nominal. See
    ``tests/test_calibration_report.py`` and MODEL-LOG §1.39 for the table.

    The level-free statistics settle it and they are the ones to read.
    ``pit_dispersion`` (1.0 is right, below 1.0 too wide) is **0.74 at ranks 1-3
    and 0.73 at ranks 4-12** — the two bands are dispersed almost identically,
    both about 1.35x wider than the errors they cover. They differ in LEVEL
    (probit-mean −0.14 against +0.79), not in width. So the correct instruction
    is the same for both bands — narrow them — plus a level transfer, and since
    shares sum to one that transfer is zero-sum: ranks 1-3 are +32.52pp and the
    phantom columns +6.36pp against −37.18pp at 4-12 and −1.70pp at 13+.

    The two coverage measures still disagree by band and that is still real:
    ``score.coverage`` reads the empirical quantile interval, which on integer
    seats must include whole endpoints and therefore over-covers, and the
    randomised PIT carries no such inflation. At a nominal 50% ranks 1-3 read
    0.78 raw against 0.70 PIT-corrected and ranks 4-12 read 0.43 against 0.32.
    Read the PIT columns. But read all three LEVELS of them, not the 50% alone:
    reading one level is how the width verdict was wrong twice.
    """
    out = {}
    for band in (*BAND_LABELS, "off-ballot"):
        per_city: list[list[float]] = []
        per_city_hits: dict[float, list[list[int]]] = {lv: [] for lv in LEVELS}
        z_all: list[float] = []
        cov = {level: {"inside": 0, "counted": 0} for level in LEVELS}
        # (cycle, z, pit, p_any) per column, for the four splits below. MODEL-LOG
        # §1.134: a width pooled over two cycles that disagree in SIGN is what
        # produced §1.131's wrong answer and rule 8's false replication claim.
        detail: list[tuple] = []
        for r in results:
            block = (r.get("calibration") or {}).get(pop)
            if not block or "band" not in block:
                continue
            labels = block["band"]
            here = [float(u) for u, b in zip(block["pit"], labels) if b == band]
            per_city.append(here)
            z_all.extend(v for v, b in zip(block.get("z") or [], labels)
                         if b == band and v is not None)
            _pa = block.get("p_any") or [None] * len(labels)
            for b, zv, uv, pav in zip(labels, block.get("z") or [None] * len(labels),
                                      block["pit"], _pa):
                if b == band:
                    detail.append((str(r.get("year")), zv, uv, pav))
            city_hits = {level: [] for level in LEVELS}
            for hit, b in zip(block.get("hits") or [], labels):
                if b != band:
                    continue
                for level, inside in zip(LEVELS, hit):
                    cov[level]["inside"] += int(inside)
                    cov[level]["counted"] += 1
                    city_hits[level].append(int(inside))
            for level in LEVELS:
                per_city_hits[level].append(city_hits[level])
        pits = [u for g in per_city for u in g]
        if not pits:
            continue
        lo, hi, boot_draws = _cluster_bootstrap_ci(per_city)
        u = np.asarray(pits, dtype=float)
        splits = _band_splits(detail)

        def _cov_rows(hit_groups, inside, counted):
            """A coverage row WITH an interval on it.

            The interval is the point of this helper. Coverage was quoted bare
            for as long as it existed, and the numbers being argued over are
            three discordant columns out of 28 — a one-sided McNemar p of 0.125,
            which is not a finding. Same cluster bootstrap as the mean PIT: the
            city-year is the unit, because columns inside one share a turnout
            draw.
            """
            clo, chi, _ = _cluster_bootstrap_ci(hit_groups)
            return {"inside": inside, "counted": counted,
                    "empirical": (inside / counted if counted else float("nan")),
                    "ci": [clo, chi]}

        pit_hit_groups = {
            level: [[int((1 - level) / 2 <= v <= (1 + level) / 2) for v in g]
                    for g in per_city]
            for level in LEVELS}
        out[band] = {
            "n": len(pits),
            "mean_pit": float(np.mean(pits)),
            "ci": [lo, hi],
            "ci_replicates": int(boot_draws),
            # Width with the level divided out. ``pit_dispersion`` needs only
            # the PIT, so it can be read off any artefact ever written;
            # ``dispersion`` is exact and needs the ``z`` column, so it is
            # ``nan`` on an artefact written before that existed. Both are
            # reported: 1.0 is right, below 1.0 too WIDE, above 1.0 too narrow.
            # PIT VARIANCE IS DELIBERATELY NOT THE HEADLINE -- it is reported
            # only so the report can show it failing. See :func:`pit_dispersion`.
            "pit_dispersion": pit_dispersion(u),
            "dispersion": dispersion_ratio(z_all),
            # The count the DISPERSION was computed on, which is not ``n``.
            # ``n`` counts PIT values; a column whose draws are all identical
            # has no scale and stores z=None, so it has a PIT and no z. On the
            # ``reference`` population the gap is wide (ranks 13+: 139 PIT
            # values, 124 z), and labelling a width figure with the PIT count
            # says it was measured on columns it was not.
            "n_z": int(len(z_all)),
            # THE FOUR THINGS THAT MUST TRAVEL WITH EVERY WIDTH FIGURE. §1.134.
            **splits,
            "z_bias": (float(np.mean(z_all)) if len(z_all) else float("nan")),
            "pit_var": (float(u.var(ddof=1)) if u.size > 1 else float("nan")),
            "coverage": [
                {"level": level,
                 **_cov_rows(per_city_hits[level], acc["inside"],
                             acc["counted"])}
                for level, acc in cov.items()],
            # The same coverage question asked of the randomised PIT, which is
            # continuous by construction and so carries no discreteness
            # inflation. Where this and ``coverage`` disagree, the parties in
            # the band are small enough that a whole seat is a large part of the
            # interval — and THIS is the number to read.
            "pit_coverage": [
                {"level": level,
                 **_cov_rows(pit_hit_groups[level],
                             int(((u >= (1 - level) / 2)
                                  & (u <= (1 + level) / 2)).sum()),
                             int(u.size))}
                for level in LEVELS],
        }
    return out


def vote_mae(run, actual, ballot="pr", weighted=True, stat="mean") -> float:
    """Mean absolute error on citywide share, in percentage points.

    ``stat`` selects the point forecast. The default is the MEAN, because that
    is the central estimate of a right-skewed distribution; the median is
    reported next to it so the difference stays visible.
    """
    draws = run.pr_share_draws if ballot == "pr" else run.ward_share_draws
    if draws is None:
        return float("nan")
    err, wt = [], []
    for party, share in actual.items():
        i = run.index.get(party)
        if i is None:
            pred = 0.0
        else:
            col = draws[:, i]
            pred = float(col.mean() if stat == "mean" else np.median(col))
        err.append(abs(pred - share))
        wt.append(share)
    if not err:
        return float("nan")
    w = np.array(wt) if weighted else np.ones(len(err))
    return float(100 * np.average(err, weights=w if w.sum() > 0 else None))


def seats_from_draws(draws):
    """Median seats per party over a list of {party: seats} dicts.

    **These are MARGINAL medians and they do not sum to a council.** The median
    of a sum is not the sum of medians, and with many parties the shortfall is
    large: at Johannesburg 2021 this returns 243 seats against a 270-seat
    chamber, so 27 of the reported seat error is the aggregation rather than the
    model. The baselines in ``benchmarks.py`` allocate per draw and sum exactly,
    which makes any seat-error comparison against them unfair to this side.

    Kept, because the per-party median is what a reader wants to see next to a
    per-party actual. :func:`coherent_seats` is the summable counterpart, and
    :func:`render` prints both totals so the gap is never invisible.
    """
    parties = sorted({p for d in draws for p in d})
    return {p: int(np.median([d.get(p, 0) for d in draws])) for p in parties}


def coherent_seats(draws, council: int):
    """A point forecast that IS a council: largest remainder on the mean vector.

    The mean seat vector sums to the council up to rounding (every draw does),
    so apportioning it by largest remainder gives a chamber rather than a set of
    unrelated marginals. Use this for any seat-error comparison against the
    baselines; use the median for the per-party table a reader reads.
    """
    parties = sorted({p for d in draws for p in d})
    if not parties or council <= 0:
        return {}
    # THE UNTRIMMED MEAN, and it was tested against the alternative. A review
    # proposed trimming, on the reasoning that a micro-party's seat draws are
    # zero in almost every draw and occasionally large, so its mean is tail-
    # driven and largest remainder rewards exactly that. The reasoning is sound
    # and the result is the other way: a 5%/95% trim took the nine-city coherent
    # seat error from 338 to 384. Trimming strips the small parties' mass, which
    # is where it genuinely lives, and hands it to the top three, which this
    # model already over-forecasts. Kept untrimmed, with the measurement.
    mean = np.array([np.mean([d.get(p, 0) for d in draws]) for p in parties])
    total = mean.sum()
    if total <= 0:
        return {p: 0 for p in parties}
    exact = mean * (council / total)
    base = np.floor(exact).astype(int)
    short = council - int(base.sum())
    if short > 0:
        order = np.argsort(-(exact - base))
        for i in order[:short]:
            base[i] += 1
    return {p: int(n) for p, n in zip(parties, base)}


def ward_winner_accuracy(ward_probs, actual_winners) -> dict:
    """How many ward contests were called right. **THE GEOGRAPHY-SENSITIVE KEY.**

    **WHAT IT IS FOR, and it is not a nicer-looking seat score.** Every other
    key in this report is structurally blind to geography, and that is a
    property of the model rather than an oversight:

    * ``solve_and_predict`` exists to force each party's realised citywide share
      onto the share the draw drew, and it succeeds — reversing the geography,
      randomising it, or deleting ``gamma`` entirely moves the citywide totals
      by less than 1e-6 (measured on a constructed city of 200 VDs and six
      parties, ``NULL-RESULTS.md`` §2; **not** measured at panel scale, which
      is one of the things this key exists to make measurable);
    * ``pr_votes`` and ``ward_votes`` are both ``weight @ pred``, so both are
      pinned to those drawn targets, and ``combined`` is therefore a function of
      the drawn targets **alone**;
    * in ``allocate_with_overhang`` a party's ward wins change its seat count
      only when ``wins >= entitlement``.

    So ``seat_abs_err``, ``seat_abs_err_coherent`` and ``crps`` can see
    geography — ``dev``, ``gamma``, pool composition, anything at VD level —
    **only through an overhang trigger.** Judging a change to any of those by
    seat error is measuring with an instrument that cannot see it, and a flat
    result from it is `NULL-RESULTS.md`'s cause **B** (ABSORBED by the θ solve),
    not a finding. This key is the one that can see it: 135 separate contests
    per city-year, each decided by which party is largest *in that ward*.

    Read the hit rate against the baselines' hit rates in the same row, never
    on its own — "78% of wards called" means nothing until "last-lge calls 74%"
    is beside it, because ward calls are dominated by safe seats in every model.
    ``brier_multicategory`` is the proper score and is what a *confidence*
    change moves; the hit rate is the modal call and is what a *placement*
    change moves. They are different questions, as coverage and PIT dispersion
    are for the seat bands.

    Scored by :func:`score.score_wards`, which `backtest.py` and `benchmarks.py`
    already call, so the model and every baseline reach one definition.
    ``wards_matched`` is reported because a ward-key mismatch between the run
    and the result file would otherwise read as a model that calls nothing
    right — the same silent-zero this whole document class exists to stop.
    """
    if not actual_winners:
        return {"n_wards": 0, "wards_matched": 0, "called": 0,
                "hit_rate": float("nan"), "brier_multicategory": float("nan")}
    ward_probs = ward_probs or {}
    scored = S.score_wards(ward_probs, actual_winners)
    return {
        "n_wards": scored["n_wards"],
        "wards_matched": sum(1 for w in actual_winners if ward_probs.get(w)),
        "called": scored["modal_calls_correct"],
        "hit_rate": scored["modal_hit_rate"],
        "brier_multicategory": scored["brier_multicategory"],
    }


def _run_one(job):
    """One city-year, as a picklable unit of work for a worker process.

    Module level and taking a single tuple because `ProcessPoolExecutor` uses
    the *spawn* start method on macOS: the callable is pickled by qualified
    name and the child re-imports this module from scratch.

    PROCESSES, NOT THREADS, and the reason is specific. `montecarlo.apply_city`
    writes into the module-level `DEFAULTS`, and `levels.SD_FLOOR` is set by
    sweeps; threads would share both and city-years would corrupt each other's
    configuration mid-run. A process per city-year gets its own module state,
    which is also what makes the parallel result equal the serial one.
    """
    slug, year, draws, data_dir, overrides, run_dir = job
    return run_city_year(slug, year, draws, Path(data_dir), overrides,
                         run_dir=Path(run_dir) if run_dir else None)


def _reconcile_arrival(run, scored: dict) -> dict:
    """Does the arrival mass the SPEC declares equal the mass the RUN draws?

    ⛔ NOTHING COMPARED THESE TWO NUMBERS, AND THAT IS HOW THE DOUBLE-COUNT
    SURVIVED. The emitted spec declares `seeded_arrival_mass`; the run draws its
    own arrival total. On 2026-09-08 the first was 1.3977% and the second
    3.32% — a factor of 2.4 sitting in one artefact and one run, in plain sight,
    for a day. I saw both numbers, did not reconcile them, and reasoned my way
    to a different diagnosis entirely (§1.215).

    A quantity that crosses an artefact boundary and is not checked on the other
    side is not declared, whatever the artefact says. This is the check.

    ⚠️ IT REPORTS, IT DOES NOT REFUSE. A refusal here would abort every scored
    city-year in the panel on a defect the panel exists to measure — and the
    gap is currently REAL, so a refusal would make the instrument unusable at
    exactly the moment it is telling the truth. The number goes into the
    artefact, `_arrival_referee` prints it, and a test asserts on it.
    """
    seeds = (run.scenario.get("pool_seeds") or {}) if hasattr(run, "scenario") else {}
    declared = float(sum(v for v in seeds.values() if v > 0))
    drawn = float(scored.get("mass_mean") or 0.0)
    # The generic slot's contribution, if it is in the universe at all. It is
    # appended whenever `entrant_prob > 0`, unconditionally on whether named
    # seeds already exist — which is the mechanism being measured here.
    prob = float((run.scenario or {}).get("entrant_prob") or 0.0)
    share = (run.scenario or {}).get("entrant_share") or [0.0, 0.0, 0.0]
    slot = prob * (sum(float(x) for x in share) / 3.0) if prob > 0 else 0.0
    has_slot = "ENTRANT" in set(run.universe or ())
    return {
        "declared_seeded_mass": declared,
        "drawn_mass_mean": drawn,
        "generic_slot_expectation": slot if has_slot else 0.0,
        "generic_slot_present": bool(has_slot),
        "seeded_parties": len([v for v in seeds.values() if v > 0]),
        # The residual after accounting for the generic slot. If the slot is
        # the whole of the discrepancy this lands near zero, which is the
        # signature of double-counting rather than of a mis-sized budget.
        "unexplained": drawn - declared - (slot if has_slot else 0.0),
        "double_counted": bool(has_slot and declared > 0),
    }


def run_city_year(city_slug: str, year: str, draws: int, data_dir: Path,
                  overrides: list[str] | None = None,
                  run_dir: Path | None = None) -> dict:
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    # `set` AFTER apply_city, which is the whole point: apply_city writes the
    # city toml's scalars over DEFAULTS, so a --set is the only override that
    # survives it. See the --set help text.
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=list(overrides or []), draws=draws, seed=None,
        city=city_slug, target=year))
    # One trace per city-year, so a backtest leaves its own intermediates
    # behind. Chasing "why is ActionSA low at Tshwane 2021?" used to mean
    # re-running the whole comparison with a print added.
    run = M.run_model(target, scenario, data_dir, verbose=False,
                      run_dir=(run_dir / f"{city_slug}-{year}") if run_dir else None)

    actual_pr, actual_ward = actual_shares(target, data_dir)
    actual_seats, entrant_actual, actual_winners = _actual_seats(
        target, data_dir, run)
    # ⛔ MEASUREMENT-HARNESS ABLATION, OFF UNLESS EXPLICITLY ASKED FOR.
    #
    # `JHB_SCORE_NO_RELABEL=1` withholds the arrival label from the MODEL so the
    # relabel's worth can be priced. ITERATING.md has recorded that worth as
    # UNQUANTIFIED since the fault was found: `relabel_run` renames the model's
    # generic ENTRANT onto the largest realised arrival, **chosen with the
    # outcome in hand**, and the baselines have no ENTRANT column so there is
    # nothing to relabel and no equivalent benefit. The model is handed a free
    # correct label on the hardest column in the panel and uniform swing is not.
    #
    # It is an ENVIRONMENT variable because `compare_history` fans out to
    # sixteen spawned worker processes and `os.environ` is what they inherit —
    # the same route `fix_hash_seed` relies on. It is deliberately NOT a
    # scenario key: `--set` keys are MODEL levers, and putting a scoring switch
    # among them would make an instrument change look like a forecast change.
    #
    # ⛔ NEVER SET IT FOR A SHIPPED RUN OR A FREEZE. It changes what the scorer
    # is, not what the model predicts, and a number measured under it is not
    # comparable to one measured without it.
    if os.environ.get("JHB_SCORE_NO_RELABEL") == "1":
        # Suppressed EVERYWHERE, not just at the relabel. `entrant_actual` also
        # reaches `calibration_columns` and both `score_seats` calls, where
        # `seat_matrix` merges the ENTRANT column onto the named party. Dropping
        # only the relabel would leave the label still doing its work downstream
        # and would price the ablation at less than it is worth.
        entrant_actual = None

    # Before ANY of the tables below. entrant_actual used to reach score_seats
    # and nothing else, so votes, rank bands and both seat errors all scored the
    # arrival machinery as a total miss plus a phantom. See backtest.relabel_run.
    run = B.relabel_run(run, entrant_actual)

    model_seats = seats_from_draws(run.seat_draws)
    coherent = coherent_seats(run.seat_draws, target.council)
    out = {
        "city": city.name, "slug": city_slug, "year": year,
        "council": target.council,
        "votes": vote_table(run, actual_pr, actual_ward),
        "pr_mae": vote_mae(run, actual_pr, "pr", stat="mean"),
        "ward_mae": vote_mae(run, actual_ward, "ward", stat="mean"),
        "pr_mae_median": vote_mae(run, actual_pr, "pr", stat="median"),
        "ward_mae_median": vote_mae(run, actual_ward, "ward", stat="median"),
        "bands": rank_bands(run, actual_pr, actual_seats),
        "seats": {p: (actual_seats.get(p, 0), model_seats.get(p, 0))
                  for p in sorted(set(actual_seats) | set(model_seats))},
        "seat_abs_err": sum(abs(actual_seats.get(p, 0) - model_seats.get(p, 0))
                            for p in set(actual_seats) | set(model_seats)),
        "seat_abs_err_coherent": sum(
            abs(actual_seats.get(p, 0) - coherent.get(p, 0))
            for p in set(actual_seats) | set(coherent)),
        "median_sum": sum(model_seats.values()),
        # AFTER relabel_run, which renames ENTRANT on `ward_winner_counts`
        # itself — score the arrival machinery's ward calls under the name of
        # the party that actually arrived, or it is debited twice.
        "wards": ward_winner_accuracy(run.ward_probabilities()
                                      if run.ward_winner_counts is not None
                                      else {}, actual_winners),
        "calibration": calibration_columns(
            run.seat_draws, actual_seats, entrant_actual,
            _pit_seed(city_slug, year), actual_pr=actual_pr,
            reference=reference_universe(target, city, data_dir)),
        "opponents": {},
    }
    scored = S.score_seats(run.seat_draws, actual_seats,
                           entrant_actual=entrant_actual)
    out["crps"] = scored["crps"]["total"]
    # ⛔ THE ONLY JOINT SCORES IN THE BUILDING, AND THEY WERE COMPUTED AND
    # THROWN AWAY. `score_seats` has returned `energy` and `variogram` since it
    # was written (`score.py:710-711`); this function took `crps["total"]` and
    # dropped both on the floor, so no `energy` or `variogram` key has ever
    # existed in `history.json`.
    #
    # It matters because **CRPS is a MARGINAL score** — it is computed per
    # party and summed — so it is structurally blind to whether the parties move
    # together. The model's own draws say the ANC and DA trade against each
    # other (-0.271) where the realised errors say they do not (+0.09), and no
    # statistic in the panel could see that. These two can.
    #
    # ⚠️ THREE CAUTIONS, and they travel with every quotation of these numbers:
    #   * NOT A FIFTH KEY. Four keys is already more discipline than most
    #     published forecasts carry, and a fifth arriving nine weeks from
    #     polling is a tuning surface with no time to check it. Reported only.
    #   * ⛔ NOT COMPARABLE BETWEEN FORECASTERS AS COMPUTED, AND THE OBVIOUS
    #     FIX DOES NOT WORK. `seat_matrix` keeps a column when the truth OR this
    #     forecaster's own draws give it a seat, and its docstring is explicit:
    #     *"The scored column set depends only on this forecaster and the
    #     result."* So a summed joint score over a variable dimension is
    #     denominator drift by construction — measured here at Johannesburg
    #     2021: the model scores over **56** columns and uniform swing over
    #     **19**. Passing `parties=` does NOT fix it; that argument fixes column
    #     ORDER only, by its own docstring. The set is held only by
    #     `seat_matrix(keep_all=True)`, which `score_seats` does not expose.
    #     `n_scored` is recorded beside every joint score so the asymmetry is at
    #     least VISIBLE rather than silent — **do not quote a model-vs-baseline
    #     joint difference until the universe is held.** Making that possible is
    #     a change to a SCORER, which is the one class of change whose failure
    #     the suite cannot see (§1.136), so it is owed an adversarial review
    #     rather than a quick passthrough.
    #     Note the design being worked around is deliberate and right for
    #     per-forecaster scoring: `seat_matrix` refuses a materiality cliff
    #     because dropping a column drops PAIRS, which made the variogram
    #     improper and let a forecaster shade its claims below the threshold to
    #     improve its own score.
    #   * `energy_score` SUBSAMPLES at `max_draws=4000` with a fixed seed, so at
    #     5,000 production draws it is a stochastic statistic. Measure its
    #     seed-to-seed spread once and never quote a difference smaller than it.
    # MODEL-LOG §1.141.
    out["energy"] = scored["energy"]
    out["variogram"] = scored["variogram"]
    out["n_scored"] = len(scored.get("parties") or [])

    # THE ARRIVAL CHANNEL, SCORED WITHOUT A LABEL. `entrant_actual` above is
    # `max(newcomers, key=seats)` — the most favourable assignment available,
    # chosen with the outcome in hand — so every score that uses it flatters the
    # generic-slot incumbent on the hardest column in the panel, and that is
    # what rejected the group arrival mechanism at CRPS 85.9 → 109.9. This is
    # the referee that comparison never had: total arrival mass and total
    # arrival seats, assigned to nobody. **Reported BESIDE the relabelled score
    # as a sensitivity pair, never instead of it.** MODEL-LOG §1.133, §1.134.
    #
    # Computed BEFORE nothing and AFTER `relabel_run`, deliberately: the relabel
    # renames a column and moves no mass, so the group total is identical either
    # way — and asserting that is how a future reader knows the label cannot
    # reach this number.
    if run.pr_share_draws is not None:
        out["arrival_group"] = B.arrival_group_score(
            run.pr_share_draws, run.seat_draws,
            {p: i for i, p in enumerate(run.universe)},
            actual_pr, actual_seats, _npe_baseline(target, data_dir))
        out["arrival_reconciliation"] = _reconcile_arrival(
            run, out["arrival_group"])

    ctx = BM.build_context(int(year), data_dir)
    for name in ("last-lge", "uniform-swing", "prior-lge-noise"):
        try:
            # `run_with_wards` rather than `run_one`, which is a one-line
            # wrapper that calls it and DISCARDS the ward half. Identical seat
            # draws — so every existing number is unchanged — and it is the
            # only way the geography key gets an opponent. A ward hit rate
            # without a baseline beside it is unreadable: safe wards are called
            # right by anything, including "last time happens again".
            seat_draws, ward_draws = BM.run_with_wards(
                name, ctx, draws=min(draws, 2000))
        except SystemExit as exc:
            out["opponents"][name] = {"error": str(exc)}
            continue
        bench_seats = seats_from_draws(seat_draws)
        # Score the opponent ONCE and keep all three. A joint score with no
        # baseline beside it is unreadable — there is no scale on which an
        # energy score of 41 is good or bad, only better or worse than the
        # thing that needs no model. This also stops the opponent being scored
        # twice by two different calls.
        bench_scored = S.score_seats(seat_draws, actual_seats,
                                     entrant_actual=entrant_actual)
        out["opponents"][name] = {
            "crps": bench_scored["crps"]["total"],
            "energy": bench_scored["energy"],
            "variogram": bench_scored["variogram"],
            "n_scored": len(bench_scored.get("parties") or []),
            # ⛔ `seat_abs_err_coherent`, NOT `seat_abs_err`. THE SAME KEY NAME
            # MEANT TWO STATISTICS AT TWO DEPTHS OF THIS FILE.
            #
            # The model's own `seat_abs_err` is the MARGINAL statistic — a sum
            # over per-party medians, which need not fill a council. A baseline
            # is deterministic (or allocated per draw), so its error is the
            # COHERENT one. Under the old name a reader — or a future session —
            # could set the model's marginal total against a baseline's coherent
            # total and read the difference as skill. That is exactly what
            # happened on 2026-09-08: the pre-batch coherent 707 was quoted
            # against the post-batch marginal 706 and the batch was reported as
            # "essentially flat" when it was +38 coherent. §1.214.
            #
            # Renamed rather than detected afterwards: the collision was invited
            # by the schema, and a detector for it would be one more thing to
            # verify. `render` prints the full key name for the same reason.
            "seat_abs_err_coherent": sum(
                abs(actual_seats.get(p, 0) - bench_seats.get(p, 0))
                for p in set(actual_seats) | set(bench_seats)),
            "wards": ward_winner_accuracy(BM.ward_probabilities(ward_draws),
                                          actual_winners)}

    # ⛔ THE `published` OPPONENT IS DELETED. IT WAS THIS MODEL'S OWN OUTPUT.
    #
    # It read `data/processed/validation_2021.json` — a run of THIS model from
    # 2026-08-11 — and placed it in `opponents` beside `uniform-swing`,
    # `last-lge` and `prior-lge-noise`, where a reader takes it for an outside
    # forecaster. `CLAUDE.md` rule 1 bars comparing anything to an earlier
    # output of this model, and the key name invited exactly that: on 2026-09-09
    # I nearly reported "we lose to the published forecast by 9.7%" to the owner
    # as the external comparison he had asked for.
    #
    # It is not merely self-benchmarking, it is incomparable on FOUR axes at
    # once, all verified against the artefact:
    #
    #     axis            published        model (same 8 rows)   model (all 24)
    #     rows            8 of 24, 2021    8                     24, three cycles
    #     party universe  12, fixed        n_scored 20-56        n_scored 9-56
    #     draws           400              1000                  1000
    #     in_sample       True             out of sample         out of sample
    #
    # `in_sample` is `True` in every one of its eight cities and `run_city_year`
    # dropped that flag when it copied the number into `opponents` — so the one
    # field that disclosed the contamination did not survive into the table
    # where the comparison was made.
    #
    # ⚠️ AND STAMPING IT WITH AN `n` WOULD HAVE BEEN WORSE THAN LEAVING IT.
    # Printing `n=8` beside it certifies the row subset while silently blessing
    # the other three axes; the number then reads as checked, on the authority
    # of the instrument. A partial compatibility check that reads as a complete
    # one is the failure this whole change exists to remove. Deleted rather than
    # renamed for the same reason: `self_2026_08_11` still sits in a column of
    # opponents and still gets subtracted from. §1.216.
    #
    # `published_for` is deleted with it. If an external forecast ever exists,
    # it goes in its own section printing all four axes on its face — not into
    # `opponents`.

    # ⛔ THE SCORED ARTEFACT SAYS WHETHER IT WAS ABLATED. ALWAYS, NOT ONLY WHEN
    # IT WAS.
    #
    # `JHB_SCORE_NO_RELABEL` changes what the SCORER is, so two `history.json`
    # files can disagree by 11.52 CRPS with identical forecasts behind them
    # (§1.148). Recorded unconditionally because this repository has already
    # been bitten by the other convention: an ABSENT record and a NEGATIVE one
    # read the same, and "the key is missing" then means both "the ablation was
    # off" and "this artefact predates the ablation" — which are different
    # facts and only one of them is safe to compare against.
    #
    # It is NOT in `freeze.ENV_SWITCHES`, deliberately. `freeze` re-runs
    # `run_model` and never imports the scoring path, so this switch cannot
    # reach a frozen forecast; recording it there would assert an influence it
    # does not have and would demand a freeze re-record for nothing. That was
    # tried on 2026-08-31 and `test_the_freeze_records_every_environment_switch`
    # correctly refused it. The contamination risk is here, in the scored
    # artefact, and this is where the stamp belongs.
    out["scored_without_relabel"] = (
        os.environ.get("JHB_SCORE_NO_RELABEL") == "1")
    return out


def _npe_baseline(target, data_dir: Path) -> dict:
    """The preceding NPE's citywide shares — what "has no baseline" means.

    The same quantity `run_model` builds its universe from, and the same test
    `backtest.entrant_actual_for` applies: a party absent from it "arrived from
    nothing". Read here rather than carried on `ModelRun` because the run does
    not expose it.

    ⛔ **THIS DOCSTRING USED TO CLAIM IT WAS "defined ONCE so the arrival score
    and the relabel cannot drift apart on what counts as an arrival". THAT IS
    FALSE, MODEL-LOG SAYS SO, AND THE SENTENCE SURVIVED IN THE CODE ANYWAY** —
    corrected 2026-08-31 after a blind review found it still here.

    This function has exactly **one** call site, and it is the arrival score.
    The relabel does not use it: `_actual_seats` builds
    ``base = {p: 1.0 for p in run.index}`` — the model's whole universe, under
    which nothing has ever "arrived from nothing". **The two definitions
    therefore disagree, and they disagree loudest at the flagship city-year**:
    at joburg 2021 `entrant_actual` is `None` while `arrival_group_score`
    reports 32 arrived parties holding 46 seats. Reconciling them is the
    outstanding work (§1.144 §4, §1.146); until then, do not read either as
    speaking for the other.

    Off-ballot parties are NOT dropped (§1.124's `absent_from_ballot`): that
    changes which parties enter `sd_for`'s fit, and changes nothing about who
    has a baseline above zero, which is all this is asked.
    """
    npe = target.previous_npe
    if not npe:
        return {}
    path = data_dir / target.results(npe)
    if not cityconfig.resolve_path(path).exists():
        return {}
    return {p: v for p, v in citywide(load(path, None)[0]).items() if v > 0}


def _actual_seats(target, data_dir: Path, run):
    """Council, arriving party and WARD WINNERS, via the backtest's own reader.

    ``actual_result`` returns more than the seats and its arity has changed
    before, so each map is picked out by shape rather than by position: the
    seats are ``{party: int}``, the ward winners ``{ward: party}``.
    ``entrant_actual`` needs the model's own BASELINE — which party had no
    national share to grow from — not the target, which is what makes a
    correctly sized newcomer score as a newcomer rather than as a total miss.

    The winners were already being read here and thrown away, which is part of
    why no geography-sensitive score existed: the ground truth for one was a
    return value away. See :func:`ward_winner_accuracy`.
    """
    path = data_dir / target.results(target.year)
    actual = B.actual_result(path, target.council, int(target.year))
    seats, winners = None, None
    for item in (actual if isinstance(actual, tuple) else (actual,)):
        if seats is None and hasattr(item, "seats"):
            seats = item.seats
            continue
        if not isinstance(item, dict) or not item:
            continue
        if seats is None and all(isinstance(v, (int, float))
                                 and not isinstance(v, bool)
                                 for v in item.values()):
            seats = item
        elif winners is None and all(isinstance(v, str) for v in item.values()):
            winners = item
    if seats is None:
        raise ValueError(f"actual_result returned no seat map for {target.year}")
    base = {p: 1.0 for p in run.index}
    return seats, B.entrant_actual_for(seats, base), winners or {}


_POP_LABEL = {
    "reference": "reference (INPUT-selected — fixed; the only one to compare on)",
    "claimed": "claimed by the model (forecast-selected — neutral for ONE model)",
    "seat_holders": "won a seat (outcome-selected — INFLATED by construction)",
    "all": "every scored column (MIXED: outcome-selected + neutral, diluted)",
}

_BAND_LABEL = {
    "1-3": "ranks 1-3",
    "4-12": "ranks 4-12",
    "13+": "ranks 13+",
    "off-ballot": "off-ballot (no actual PR rank)",
}


def _width_on_reference(pooled: dict) -> list[str]:
    """The same width verdict on the FIXED population — and it disagrees.

    The table above is `claimed`, whose membership is a function of the
    forecaster's own draws (58 / 67 / 81 columns across a `dirichlet_scale`
    sweep) and which therefore **excludes the columns the model fails worst
    on** — a party given a seat in fewer than half the draws is exactly a party
    the model is failing on. `MODEL-LOG` §1.55 read "ranks 4-12 want
    `dirichlet_scale = 2.0`" off it, and on a fixed population that is
    backwards.

    So both are printed, side by side, and any BEFORE/AFTER comparison is read
    off the `reference` row. See :func:`reference_universe`.
    """
    ref = pooled.get("reference", {}).get("by_band")
    clm = pooled.get("claimed", {}).get("by_band")
    if not ref or not clm:
        return []
    out = ["#### The same question on the FIXED population — and it disagrees\n",
           "**The `n` here is the number of columns the width figure was "
           "actually computed on** — columns with a defined `z`. A column whose "
           "draws are all identical has no scale, so it carries a PIT and no "
           "`z`; the pooled tables above count PIT values and their `n` is "
           "larger.\n",
           "| band | `claimed` n(z) | `claimed` SD of z | `reference` n(z) | "
           "`reference` SD of z | `reference` mean z | `reference` probit-SD |",
           "|---|---|---|---|---|---|---|"]
    for band in BAND_LABELS:
        a, b = clm.get(band), ref.get(band)
        if not a or not b:
            continue

        def num(blk, key, fmt="{:.3f}"):
            v = blk.get(key)
            return "—" if v is None or v != v else fmt.format(v)

        out.append(f"| {_BAND_LABEL[band]} | {a.get('n_z', a['n'])} | "
                   f"{num(a, 'dispersion')} | {b.get('n_z', b['n'])} | "
                   f"{num(b, 'dispersion')} | "
                   f"{num(b, 'z_bias', '{:+.3f}')} | "
                   f"**{num(b, 'pit_dispersion')}** |")
    out.append(
        "\n**Read the last column, not the `SD of z` column, on ranks 13+.** "
        "`sd(z)` is exact under a level shift and **meaningless on a "
        "near-degenerate discrete column**: where the forecast is roughly "
        "Bernoulli(p) and the truth is zero, `z = −√(p/(1−p))` exactly, a "
        "function of the forecast probability with no room to spread. On the 96 "
        "ranks-13+ columns whose truth is zero, observed `z` correlates with "
        "that expression at **+0.93**. probit-SD comes from the randomised PIT, "
        "which is uniform under calibration whatever the support, and is the "
        "one to read there — at the cost of being attenuated by a level shift, "
        "so it is a LOWER BOUND wherever `mean z` is far from zero. Neither "
        "statistic is right everywhere; the pair is. MODEL-LOG §1.58.\n\n"
        "**Ranks 1-3 are the same columns in both populations** — the top three "
        "are always claimed — so that row is a consistency check and the two "
        "`SD of z` numbers should agree exactly. It is also the band that is "
        "genuinely too WIDE and the band that responds to `dirichlet_scale`.\n\n"
        "**Ranks 4-12 cannot be described by one width, and that is the "
        "finding.** On the same columns `sd(z)` says far too narrow, `IQR-sd` "
        "says too wide, and probit-SD disagrees with both — because the error "
        "distribution is a narrow shifted bulk with two enormous outliers, "
        "Cape Town's Cape Coloured Congress and Johannesburg's PA, both of "
        "which `claimed` excludes by construction. A distribution that reads "
        "differently depending which moment you take is mis-SHAPED, not "
        "mis-scaled, and no scalar fixes it.\n\n"
        "⛔ **AND THE SPREAD AT 4-12 IS TWO COLUMNS.** Those two carry ~70% of "
        "the band's total squared z; dropping them takes `sd(z)` to about 1.0. "
        "Quote the leave-the-largest-out figure beside the headline or the "
        "headline is two observations, not a width. §1.56, §1.58, §1.131.\n")
    return out


def render_calibration(results: list[dict], bins: int = 10) -> str:
    """The calibration block: pooled over city-years, SPLIT BY RANK BAND.

    The PIT mean says whether the intervals are in the right PLACE, and that
    answer **is** band-dependent: on the claimed columns of the committed
    ``history.json`` ranks 1-3 come out at 0.434 and ranks 4-12 at 0.757, which
    pool to 0.598 — a figure that is neither band's answer.

    **Coverage at one level does NOT say whether the intervals are the right
    width, and printing it as though it did is what made this report wrong
    twice.** Coverage responds to level and to width at once. A shifted forecast
    vacates the centre of its own interval, so its 50% coverage collapses
    whatever its width; only excess width lifts the 80% and 90% coverages ABOVE
    nominal, and only a genuinely narrow forecast pushes all three below. This
    model's ranks 4-12 read 32/89/96 against 50/80/90 — down at 50 and UP at 80
    and 90, which is the shifted-and-too-wide signature and not the narrow one.

    So the width verdict is taken from statistics with the level divided out —
    ``pit_dispersion`` and ``dispersion_ratio``, 1.0 being right — and coverage
    is printed at all three levels together, never one alone. Both bands come
    out near 0.73: **the same width fault, not opposite ones.**
    """
    pooled = pooled_calibration(results, bins=bins)
    lines: list[str] = []
    add = lines.append
    add("\n## Calibration — pooled across every city-year, and split by rank\n")
    add("**Pool over city-years; never over rank bands.** Seven to fifteen "
        "scored columns per city-year cannot distinguish a 50% interval from an "
        "80% one, so the city-years must be pooled to say anything at all. But "
        "the rank bands must NOT be: this model is biased in opposite "
        "directions at the top of the ballot and in the middle, and a mean over "
        "both lands between them and reports a model that does not exist. The "
        "pooled table comes first because it is the familiar one; **the split "
        "table below it is the one to read.**\n")
    add("A mean PIT above 0.50 means the truth keeps landing high in the "
        "forecast distribution — the model forecast too LOW for those columns. "
        "Below 0.50 means it forecast too HIGH. Read the sign per band; the "
        "pooled sign is an artefact of how the two bands happen to be sized.\n")
    add("| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (5% crit) |")
    add("|---|---|---|---|---|---|---|")
    for pop in POPULATIONS:
        block = pooled[pop]
        cov = {row["level"]: row["empirical"] for row in block["coverage"]}
        hist = block["pit"]
        crit = hist.get("chi2_crit_95")
        add(f"| {_POP_LABEL[pop]} | {block['n']} | "
            + " | ".join(f"{100 * cov.get(level, float('nan')):.0f}%"
                         for level in LEVELS)
            + f" | {hist['mean']:.3f} | {hist['chi2']:.1f} "
              f"({crit if crit is not None else '—'}) |")
    add("")
    for pop in POPULATIONS:
        block = pooled[pop]
        add(f"* **{pop}** (n={block['n']}) PIT histogram "
            f"{block['pit']['counts']} — {block['pit']['verdict']}")
    add("\nThe verdict at the end of each line is `score.pit_histogram`'s shape "
        "heuristic, which reads the end mass and the mean. **DO NOT ACT ON IT "
        "AS A WIDTH VERDICT — it is not reliable as one, and on this model it "
        "is demonstrably wrong.** The heuristic tests the mass in the two END "
        "bins against flat, so a histogram that is monotone increasing scores "
        "as U-shaped: a shifted forecast piles mass in the top bin and gets "
        "called under-dispersed. On the ranks 4-12 columns it reads the "
        "histogram `[1, 1, 1, 11, 14]` — 25 of 28 in the top two bins, "
        "monotone, nothing at the bottom — and prints *\"U-shaped … "
        "under-dispersed, widen it\"*, while calling the pooled population "
        "*\"hump-shaped — over-dispersed, hedging\"*. The two verdicts "
        "contradict each other and the band one contradicts the level-free "
        "width table below, which is the one that is right. `score.py` is not "
        "changed here — the heuristic is fine for its own purpose and what is "
        "wrong is quoting it about width. **The χ² column is the test of "
        "uniformity; the level-free dispersion table is the test of width.**")
    add("\nThe three populations differ by which columns they count, and the "
        "difference is itself the finding. `claimed` selects on the FORECAST, "
        "which leaves PIT uniform under calibration, so it is the honest test "
        "and the only one to quote. `seat_holders` selects on the OUTCOME: zero "
        "is the bottom of the support, so winning a seat selects over-performers "
        "and the population reads high even for a perfect forecaster — it is "
        "quoted because it is the population a reader assumes, not because it is "
        "neutral. `all` was documented as neutral and **is not**: "
        "`score.seat_matrix` admits a column when `truth[i] > 0 or "
        "samples[:, i].max() > 0`, and the first clause lets a party in because "
        "it WON, which is outcome selection. Five of its columns across the nine "
        "city-years carry PIT exactly 1.0 — parties the model gave zero seats in "
        "every draw, present only because they won a seat. It is a mixture of an "
        "outcome-selected set and a neutral one, and the neutral part is itself "
        "diluted by ~200 parties correctly at zero on both sides, each a free "
        "interval hit and a near-uniform PIT. Two errors pushing opposite ways: "
        "`all` tests nothing.\n")

    add("### Split by actual PR rank — `claimed` columns\n")
    add("**The pooled row above is the average of the rows below, and they have "
        "opposite signs.** This is the same fault as a signed error sum inside a "
        "rank band, one level up: an average over subsets biased in opposite "
        "directions reports the midpoint and calls it centred.\n")
    add("| band | n | mean PIT | 95% CI (cluster bootstrap) | 50% | 80% | 90% | "
        "50% (PIT) | 80% (PIT) | 90% (PIT) |")
    add("|---|---|---|---|---|---|---|---|---|---|")
    band_block = pooled["claimed"]["by_band"]

    def _cell(row):
        """A coverage cell WITH its interval. Bare coverage is not quotable.

        These are counts in the twenties and the differences argued over are
        two or three columns. The discreteness correction at ranks 4-12 — the
        step from "about right" to "far too narrow" that carried a whole width
        argument — is **three discordant columns out of 28**, a one-sided sign
        test at p = 0.125; at ranks 1-3 it is two, p = 0.25. The 80% and 90%
        over-coverages are not individually significant either. Printing a
        point estimate alone invites a conclusion the count cannot support, and
        did, twice. See MODEL-LOG §1.39.
        """
        if row is None:
            return "—"
        lo, hi = row.get("ci", [float("nan"), float("nan")])
        pct = f"{100 * row['empirical']:.0f}%"
        if lo != lo:
            return pct
        return f"{pct} [{100 * lo:.0f}–{100 * hi:.0f}]"

    for band in (*BAND_LABELS, "off-ballot"):
        blk = band_block.get(band)
        if not blk:
            continue
        cov = {row["level"]: row for row in blk["coverage"]}
        pit_cov = {row["level"]: row for row in blk["pit_coverage"]}
        lo, hi = blk["ci"]
        ci = ("—" if lo != lo else f"[{lo:.3f}, {hi:.3f}]")
        add(f"| {_BAND_LABEL[band]} | {blk['n']} | {blk['mean_pit']:.3f} | {ci} | "
            + " | ".join(_cell(cov.get(level)) for level in LEVELS) + " | "
            + " | ".join(_cell(pit_cov.get(level)) for level in LEVELS) + " |")
    add("")

    replicates = max((blk.get("ci_replicates", 0)
                      for blk in band_block.values()), default=0)
    add("The CI resamples CITY-YEARS, not columns: columns inside one city-year "
        f"share a turnout draw, a pool structure and a national swing, so a "
        f"column bootstrap would give an interval far too tight. "
        f"{replicates:,} replicates, fixed seed.\n")
    add("**The two coverage triples are the same question asked twice.** The "
        "first is `score.coverage` — the empirical quantile interval, which on "
        "integer seats must include whole endpoints and therefore over-covers. "
        "The second is the fraction of columns whose randomised PIT falls in the "
        "central interval, which carries no such inflation. They agree at ranks "
        "1-3, where parties hold tens of seats and one endpoint is worth "
        "nothing, and diverge at ranks 4-12, where parties hold one to ten and "
        "an endpoint is a large part of the interval. **Read the PIT columns "
        "whenever the two are compared** — but neither triple is the width "
        "verdict on its own; that is the table below.\n")
    add("**Read all three coverage levels together, never one of them.** A "
        "forecast whose intervals are too NARROW under-covers at EVERY level — "
        "that is what narrow means. A forecast that is merely SHIFTED loses "
        "coverage at the 50% level first and hardest, because it has vacated "
        "the middle of its own interval, and its 80% and 90% coverages fall "
        "too. Only intervals that are too WIDE push the 80% and 90% coverages "
        "above nominal. So a band that reads LOW at 50% and HIGH at 80 and 90 "
        "is shifted and too wide, and reading its 50% column alone gives "
        "exactly the opposite instruction. **That mistake has been made twice "
        "on this report, in opposite directions, and rule 8 of `ITERATING.md` "
        "carried each of them.** The width verdict belongs to the level-free "
        "table above; the coverage rows corroborate it or they do not.\n")
    add("The rank-band vote table further up and the mean-PIT column here are "
        "the same LEVEL finding measured twice — top three over, middle short. "
        "Because shares sum to one that gap is a zero-sum transfer, not two "
        "independent faults, so a level fix has to move mass rather than add "
        "it.\n")

    add("### Is it the right WIDTH? — the level divided out\n")
    add("**This table, not the coverage rows, is the width verdict.** Coverage "
        "moves with the level as well as the width: a forecast pushed off "
        "centre vacates the middle of its own interval, so its 50% coverage "
        "falls however wide it is. Read at one level, coverage says 'too "
        "narrow' for a forecast that is merely shifted. The columns below "
        "divide the level out. **1.00 is right; below 1.00 the intervals are "
        "too WIDE; above 1.00 too narrow.** `1/ratio` is roughly the factor "
        "they are out by.\n")
    add("| band | n | probit-SD (level-free) | exact SD of z | standardised "
        "bias (mean z) | PIT variance vs 1/12 |")
    add("|---|---|---|---|---|---|")
    for band in (*BAND_LABELS, "off-ballot"):
        blk = band_block.get(band)
        if not blk:
            continue

        def num(key, fmt="{:.3f}", blk=blk):
            v = blk.get(key)
            return "—" if v is None or v != v else fmt.format(v)

        add(f"| {_BAND_LABEL[band]} | {blk['n']} | {num('pit_dispersion')} | "
            f"{num('dispersion')} | {num('z_bias', '{:+.3f}')} | "
            f"{num('pit_var', '{:.4f}')} vs {1 / 12:.4f} |")
    add("")
    for line in _width_on_reference(pooled):
        add(line)
    add("**`probit-SD` is the one to quote when only a PIT is available.** It "
        "is `sd(Φ⁻¹(u))`, and under a location shift of a roughly normal "
        "forecast `Φ⁻¹(u)` translates — the shift lands in the mean, not the "
        "spread. `exact SD of z` is `(truth − forecast mean) / forecast sd` per "
        "column, centred, which is invariant to a shift by construction; it "
        "reads `—` on an artefact written before `calibration_columns` stored "
        "the `z` column, and it is the number to prefer when it is there. The "
        "standardised bias is the LEVEL, kept in its own column so that it can "
        "never be read as width again.\n")
    add("**The last column is printed to show it failing.** PIT variance "
        "against a nominal 1/12 has been proposed on this project as "
        "\"shift-invariant, therefore a clean width statistic\". **It is "
        "neither.** A PIT lives on [0, 1]; move the forecast off centre and its "
        "mass piles against a boundary and the variance falls whatever the "
        "width is. On the suite's fixture whose width is exactly right "
        "(`tests/test_calibration_report.py::_shift_scale_results`) it reads "
        "0.0829, 0.0450 and 0.0240 at truth shifts of 0, +2 and +3 seats "
        "against a nominal 0.0833 — a pure level error reading as a 3.5× "
        "under-dispersion, which is the wrong diagnosis with the wrong remedy. "
        "Do not quote it as a width statistic; it is here so that nobody "
        "rediscovers it as one.\n")

    add("Per city-year, for provenance only — **every n below is too small to "
        "read, and none of these rows is evidence of anything on its own.**\n")
    add("| city-year | n claimed | 50% | 80% | 90% | mean PIT (claimed) |")
    add("|---|---|---|---|---|---|")
    for r in results:
        block = (r.get("calibration") or {}).get("claimed")
        if not block:
            continue
        cov = {row["level"]: row["empirical"] for row in block["coverage"]}
        pit = np.array(block["pit"], dtype=float)
        cells = " | ".join(f"{100 * cov.get(level, float('nan')):.0f}%"
                           for level in LEVELS) if pit.size else "— | — | —"
        mean = f"{pit.mean():.3f}" if pit.size else "—"
        add(f"| {r['city']} {r['year']} | {block['n']} | {cells} | {mean} |")
    add("")
    return "\n".join(lines)


def _arrival_referee(results: list[dict]) -> list[str]:
    """The arrival channel scored WITHOUT the free label — reported beside the
    relabelled headline, never instead of it.

    ⛔ **THIS WAS COMPUTED, STORED AND NEVER SHOWN.** `arrival_group_score` has
    been written into `history.json` on every run since it was repaired, and
    appeared in no rendered report — so the one instrument that scores the
    arrival channel without handing the model the answer was invisible unless
    somebody opened the JSON. `ITERATING.md` already prescribes the remedy in
    these words: *"reported beside the relabelled score as a sensitivity pair,
    never instead of it."* This is that.

    **Why it is needed.** The headline CRPS is scored AFTER `relabel_run`
    renames the model's generic ENTRANT onto the largest realised arrival —
    chosen with the outcome in hand — and the baselines have no such column.
    Measured on this panel, that free label is worth **11.52 CRPS (3.5%) and
    2.17 points of the margin over uniform swing**; `JHB_SCORE_NO_RELABEL=1`
    reproduces it. This table is the label-free view of the same channel.

    `mass_pit` and `seats_pit` are the numbers to read. Both are PIT values, so
    **0.5 is centred and above 0.5 means the model forecast too LITTLE** arrival
    mass or too few arrival seats.
    """
    rows = [r for r in results if r.get("arrival_group")]
    if not rows:
        return []
    out = ["\n## The arrival channel, scored without the label\n",
           "The headline CRPS above is scored after the model's generic "
           "`ENTRANT` column is renamed onto the largest party that actually "
           "arrived — a label chosen with the result in hand, which no baseline "
           "gets. This table does not use it. **PIT above 0.5 means the model "
           "forecast too little.**\n",
           "| city-year | arrived | actual mass | forecast mass | actual seats "
           "| forecast seats | mass PIT | seats PIT |",
           "|---|---|---|---|---|---|---|---|"]
    mp, sp = [], []
    for r in rows:
        a = r["arrival_group"]
        mp.append(a["mass_pit"]); sp.append(a["seats_pit"])
        out.append(
            f"| {r['city']} {r['year']} | {a['n_arrived']} | "
            f"{a['actual_mass'] * 100:.2f}% | {a['mass_mean'] * 100:.2f}% | "
            f"{a['actual_seats']} | {a['seats_mean']:.1f} | "
            f"{a['mass_pit']:.3f} | {a['seats_pit']:.3f} |")
    out.append(f"| **panel mean** | | | | | | **{sum(mp) / len(mp):.3f}** | "
               f"**{sum(sp) / len(sp):.3f}** |")
    over = sum(1 for v in mp if v > 0.5)
    out.append(f"\nMass PIT is above 0.5 at **{over} of {len(mp)}** city-years. "
               f"A panel mean well above 0.5 on both columns is the model "
               f"systematically under-forecasting how much of the ballot goes "
               f"to parties arriving from nothing — read it next to the "
               f"mid-ballot calibration below, which is the same leak seen "
               f"through a different instrument.\n")
    return out


def _headline_split(results: list[dict]) -> list[str]:
    """The headline margin over uniform swing, split Gauteng against the rest.

    **Disclosure, not tuning — this table exists to be quoted against us.** The
    margin is concentrated: inside Gauteng the model takes far more off uniform
    swing's seat error than outside it, and it LOSES at Mangaung. For a
    Johannesburg product that is the reassuring reading — the margin is where
    the product is. For the multi-city portal it is not, and a reader who
    computes this for themselves after the fact and finds it undisclosed has a
    much better story than one who reads it here.

    **THE SIGN COUNT IS COMPUTED, NOT TYPED (2026-08-23).** Until then this
    function ended by printing the literal string *"8 of 9 city-years, 8 of
    which are one election"* into every generated `history.md` — a
    nine-city-year figure, still being emitted onto a SIXTEEN-city-year report
    after §1.70, into the canonical artefact every other document is audited
    against. §1.77's re-read did not reach it because the audit test parses
    `ITERATING.md`'s two marked tables and nothing parses generated prose. The
    percentages in this docstring went the same way and are gone for the same
    reason. `CLAUDE.md`: never type a model figure into prose.
    """
    groups = [("Gauteng (JHB, TSH, EKU)", lambda r: r["slug"] in GAUTENG),
              ("everywhere else", lambda r: r["slug"] not in GAUTENG)]
    out = ["### The margin is not evenly spread\n",
           "| | city-years | seat err (coherent) | uniform-swing | margin | "
           "CRPS | uniform-swing CRPS | margin |",
           "|---|---|---|---|---|---|---|---|"]
    for label, keep in groups:
        sel = [r for r in results if keep(r)]
        if not sel:
            continue
        opp = [r["opponents"].get("uniform-swing", {}) for r in sel]
        if any("error" in o or o.get("seat_abs_err_coherent") is None
               for o in opp):
            out.append(f"| {label} | {len(sel)} | — | — | — | — | — | — |")
            continue
        m = sum(r["seat_abs_err_coherent"] for r in sel)
        u = sum(o["seat_abs_err_coherent"] for o in opp)
        mc = sum(r["crps"] for r in sel)
        uc = sum(o["crps"] for o in opp)
        out.append(
            f"| {label} | {len(sel)} | {m:.0f} | {u:.0f} | "
            f"{100 * (1 - m / u):.0f}% | {mc:.1f} | {uc:.1f} | "
            f"{100 * (1 - mc / uc):.0f}% |" if u and uc else
            f"| {label} | {len(sel)} | {m:.0f} | {u:.0f} | — | {mc:.1f} | "
            f"{uc:.1f} | — |")
    # The sign count, per cycle, computed from these results.
    def _tally(rows):
        w = l = t = 0
        for r in rows:
            o = r["opponents"].get("uniform-swing", {})
            u = o.get("seat_abs_err_coherent")
            if u is None:
                continue
            m = r["seat_abs_err_coherent"]
            w, l, t = (w + (m < u), l + (m > u), t + (m == u))
        return w, l, t

    cycles = sorted({r["year"] for r in results})
    w, l, t = _tally(results)
    per = "; ".join(
        "{}: {}W {}L {}T".format(y, *_tally([r for r in results if r["year"] == y]))
        for y in cycles)
    replicates = all(
        _tally([r for r in results if r["year"] == y])[0]
        > _tally([r for r in results if r["year"] == y])[1] for y in cycles)
    out.append(
        f"\n**The headline margin is a Gauteng result.** Outside Gauteng the "
        f"model is closer to parity with uniform swing on seats and loses at "
        f"Mangaung. Quote the split, not the pool.\n\n"
        f"**Sign count against uniform swing: {w} wins, {l} losses, {t} ties "
        f"across {len(results)} city-years** — {per}. "
        + ("The sign REPLICATES across cycles, which is what the amended bar's "
           "Key 1 asks of any candidate and is the strongest claim this panel "
           "supports. "
           if replicates and len(cycles) > 1 else
           "The sign does NOT replicate across cycles; do not quote the pooled "
           "count without saying so. ")
        + f"Metros inside one cycle share a national swing, so {len(results)} "
        f"city-years is {len(cycles)} effective clusters, not {len(results)} — "
        f"never quote a p-value off the pooled count.")
    return out


def render_wards(results: list[dict]) -> str:
    """The ward-winner table — the only key in this report that sees geography.

    Separate section rather than two more headline columns, because it needs
    the paragraph: read against the seat columns without it, a flat ward score
    looks like corroboration when it is a different instrument answering a
    different question. See :func:`ward_winner_accuracy`.
    """
    rows = [r for r in results if (r.get("wards") or {}).get("n_wards")]
    if not rows:
        return ""
    lines = ["\n## Ward winners — the geography key\n",
             "**`seat_abs_err_coherent` cannot see geography and this can.** "
             "`solve_and_predict` forces every party's citywide share onto the "
             "share the draw drew, and both ballots are `weight @ pred` against "
             "those same targets, so `dev`, `gamma`, pool composition and the "
             "whole VD layer reach the seat score ONLY through an overhang "
             "trigger. Any change to those is judged here, or it is judged by "
             "an instrument that is blind to it. Hit rate is the modal call; "
             "Brier (multi-category, 0 to 2) is the proper score and is what a "
             "change in CONFIDENCE moves. **Read the model against the "
             "baselines in its own row** — safe wards are called correctly by "
             "anything at all.\n",
             "| city-year | wards | model called | hit rate | Brier MC | "
             "last-lge | uniform-swing | prior-lge-noise |",
             "|---|---|---|---|---|---|---|---|"]

    def opponent(r, key):
        w = ((r["opponents"].get(key) or {}).get("wards") or {})
        return f"{w['hit_rate']:.1%}" if w.get("n_wards") else "—"

    totals = {"n": 0, "called": 0}
    opp_totals: dict[str, dict[str, int]] = {}
    for r in rows:
        w = r["wards"]
        totals["n"] += w["n_wards"]
        totals["called"] += w["called"]
        for key in ("last-lge", "uniform-swing", "prior-lge-noise"):
            ow = ((r["opponents"].get(key) or {}).get("wards") or {})
            if ow.get("n_wards"):
                slot = opp_totals.setdefault(key, {"n": 0, "called": 0})
                slot["n"] += ow["n_wards"]
                slot["called"] += ow["called"]
        short = (f" (only {w['wards_matched']} matched)"
                 if w["wards_matched"] < w["n_wards"] else "")
        lines.append(
            f"| {r['city']} {r['year']} | {w['n_wards']}{short} | "
            f"{w['called']} | {w['hit_rate']:.1%} | "
            f"{w['brier_multicategory']:.3f} | "
            f"{opponent(r, 'last-lge')} | {opponent(r, 'uniform-swing')} | "
            f"{opponent(r, 'prior-lge-noise')} |")
    pooled = totals["called"] / totals["n"] if totals["n"] else float("nan")
    against = ", ".join(
        f"{key} {slot['called'] / slot['n']:.1%}"
        for key, slot in opp_totals.items() if slot["n"])
    lines.append(f"\n**Pooled over {len(rows)} city-year"
                 f"{'s' if len(rows) != 1 else ''}: "
                 f"{totals['called']}/{totals['n']} = {pooled:.1%} of ward "
                 f"contests called correctly"
                 + (f", against {against}." if against else ".") +
                 " A margin over the baselines that is smaller than the seat "
                 "margin is the model's geography adding less than its citywide "
                 "machinery, which is a statement the seat columns cannot make.")
    return "\n".join(lines)


def _opp_total(results: list[dict], key: str, field: str) -> float | None:
    """One opponent's total over the rows where it is present and scorable."""
    vals = [(r["opponents"].get(key) or {}).get(field) for r in results]
    good = [v for v in vals if v is not None]
    return sum(good) if len(good) == len(results) else None


def _totals_row(results: list[dict]) -> str:
    """The TOTAL line for the Headline table.

    ⛔ THIS ROW EXISTS BECAUSE THE POOLED NUMBER THIS PROJECT ARGUES OVER DID NOT
    EXIST IN ANY ARTEFACT. `render` printed 24 rows and no total, so every
    pooled claim ever made here was summed by hand — and on 2026-09-08 a
    hand-summed pre-batch COHERENT 707 was set against a post-batch MARGINAL 706
    and reported as "essentially flat" when it was +38 coherent (§1.214).

    An opponent's total is `None` unless it is present on EVERY row, so a
    benchmark scored on a subset cannot contribute a total that looks like the
    others.
    """
    n = len(results)
    def opp(key):
        v = _opp_total(results, key, "seat_abs_err_coherent")
        return "—" if v is None else f"{v:.0f}"
    return (f"| **TOTAL** [rows={n}] | "
            f"{sum(r['council'] for r in results)} | — | — | "
            f"**{sum(r['seat_abs_err'] for r in results)}** | — | "
            f"**{sum(r['seat_abs_err_coherent'] for r in results)}** | "
            f"**{sum(r['crps'] for r in results):.1f}** | "
            f"{opp('last-lge')} | {opp('uniform-swing')} | "
            f"{opp('prior-lge-noise')} |")


def _citable(results: list[dict], manifest: dict | None = None) -> str:
    """The block that is meant to be COPIED, not read.

    ⛔ EVERY NUMBER LEAVES THIS PROJECT WITH ITS OWN IDENTITY ATTACHED, OR IT
    DOES NOT LEAVE.

    The rule that decides what goes on a line: **a coordinate is printed when it
    VARIES within the report, and lives in the manifest when it does not.** So
    `rows` is here (it differs between the panel and any subset) and `draws` is
    not (one `--draws` for the whole run). If a subset-scored benchmark ever
    returns, its axes start varying and get promoted by the rule rather than by
    someone remembering.

    Printing run-level constants on every line would be furniture, and furniture
    teaches the eye to skip the label — which is the failure this is here to
    prevent.

    ⚠️ Compliance is a design property, not a discipline: citing has to be
    EASIER than retyping, or the number gets retyped. Hence a block that can be
    pasted whole.
    """
    n = len(results)
    us = _opp_total(results, "uniform-swing", "seat_abs_err_coherent")
    coh = sum(r["seat_abs_err_coherent"] for r in results)
    marg = sum(r["seat_abs_err"] for r in results)
    crps = sum(r["crps"] for r in results)
    scored = sum(r.get("n_scored") or 0 for r in results)
    # ⛔ THE ONE-LINE TOKEN, AND IT IS THE POINT OF THIS BLOCK.
    #
    # A blind reviewer put the load-bearing assumption plainly: to write "the
    # panel scores 745" in a sentence you would have to paste an eight-line
    # fenced block carrying four numbers you do not want — so you would retype
    # `745`, and the whole exercise fails. They were right.
    #
    # ⚠️ AND THE COORDINATE RULE WAS APPLIED BACKWARDS. §1.214 compared TWO
    # REPORTS (a pre-batch 707 against a post-batch 706), not two lines of one,
    # and both reports print `[rows=24]` — so the block did not disambiguate
    # the very confusion it cites as its reason for existing. A between-report
    # citation needs the between-report coordinates: the commit, the draw
    # count, and which specs were read.
    #
    # Hence one line, pasteable mid-sentence, carrying all of them.
    man_bits = []
    if manifest:
        c = str(manifest.get("git_commit") or "?")[:8]
        if manifest.get("git_dirty"):
            c += "+dirty"
        man_bits = [f"@{c}", f"{manifest.get('draws')}d"]
        keys = {k.get("pools_sha") for city in
                (manifest.get("pool_artefact_keys") or {}).values()
                for k in (city or {}).values() if isinstance(k, dict)}
        if len(keys) == 1:
            man_bits.append(f"pools:{str(keys.pop())[:8]}")
    tok = "/".join([f"seat_abs_err_coherent={coh}"] + man_bits + [f"rows={n}"])

    out = ["### Citable totals\n",
           f"**Quoting one number in a sentence? Paste this token, do not "
           f"retype the figure:**\n",
           "```",
           tok,
           "```",
           "",
           "The full set, for anything more than one number:\n",
           "```",
           f"seat_abs_err_coherent = {coh:<8} [rows={n}]",
           f"seat_abs_err          = {marg:<8} [rows={n}]   # MARGINAL, not "
           f"comparable to the line above",
           f"crps                  = {crps:<8.2f} [rows={n}]",
           f"n_scored              = {scored:<8} [rows={n}]   # summed scoring "
           f"columns, the CRPS denominator"]
    if us:
        out.append(f"margin_vs_uniform_swing = {100 * (1 - coh / us):.1f}%"
                   f"   [rows={n}, coherent]")
    else:
        # ⛔ SAY WHY, DO NOT DROP THE LINE. A margin that quietly disappears
        # reads as "not applicable"; a margin that is absent because the
        # opponent was not scored on every row is a different fact and the
        # reader must be told which. This is the same loud-degradation rule
        # `test_calibration_report.py` applies to an artefact missing its
        # intervals.
        have = sum(1 for r in results
                   if (r["opponents"].get("uniform-swing") or {})
                   .get("seat_abs_err_coherent") is not None)
        out.append(f"margin_vs_uniform_swing = UNAVAILABLE   "
                   f"[uniform-swing carries seat_abs_err_coherent on {have} of "
                   f"{n} rows; a total over a subset is not the panel's total]")
    out += ["```",
            "",
            "`seat_abs_err` and `seat_abs_err_coherent` are DIFFERENT "
            "STATISTICS. Quoting one against the other is §1.214."]
    return "\n".join(out)


def render(results: list[dict], manifest: dict | None = None) -> str:
    global _MANIFEST_FOR_RENDER
    _MANIFEST_FOR_RENDER = manifest
    lines: list[str] = []
    add = lines.append
    add("# Historical performance — votes and seats, predicted against actual\n")
    add(f"{len(results)} city-years. Shares are citywide percentages; the "
        f"model column is the median over draws.\n")

    add("## Headline\n")
    add("| city-year | council | list MAE | ward MAE | seat err (median) | "
        "medians sum to | seat err (coherent) | CRPS | last-lge | "
        "uniform-swing | prior-lge-noise |")
    add("|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        o = r["opponents"]
        def cell(key, field="seat_abs_err_coherent"):
            v = o.get(key, {})
            if "error" in v or v.get(field) is None:
                return "—"
            return (f"{v[field]:.0f}" if field == "seat_abs_err_coherent"
                    else f"{v[field]:.1f}")
        add(f"| {r['city']} {r['year']} | {r['council']} | "
            f"{r['pr_mae']:.2f}pp | {r['ward_mae']:.2f}pp | "
            f"{r['seat_abs_err']} | {r['median_sum']} | "
            f"{r['seat_abs_err_coherent']} | {r['crps']:.1f} | "
            f"{cell('last-lge')} | {cell('uniform-swing')} | "
            f"{cell('prior-lge-noise')} |")
    add(_totals_row(results))
    add("")
    add(_citable(results, _MANIFEST_FOR_RENDER))
    add("")
    for line in _headline_split(results):
        add(line)
    add("\n**Read the two seat-error columns together.** *seat err (median)* "
        "uses the per-party marginal median, which is what the per-party tables "
        "below show and which **does not sum to a council** — the *medians sum "
        "to* column says by how much. *seat err (coherent)* apportions the mean "
        "seat vector by largest remainder, so it IS a chamber and is the only "
        "one comparable to the baselines, which allocate per draw and sum "
        "exactly. Lower is better throughout.\n")

    for line in _arrival_referee(results):
        add(line)

    add("\n## Where the vote error sits on the ballot\n")
    add("**Two columns per band, and they answer different questions.** *signed* "
        "is the net error in points — positive means the model gave that band "
        "MORE than it won — and it is what shows one band eating another. *abs* "
        "sums the per-party error without cancelling, and it is the only one of "
        "the two that is a measure of error at all. Where they diverge, the band "
        "is wrong about individual parties in both directions at once: "
        "Johannesburg 2021's ranks 1-3 are the case that motivated the column "
        "(ANC and DA over, ActionSA far under). The bands are by actual rank.\n")
    add("| city-year | 1-3 signed | 1-3 abs | 4-12 signed | 4-12 abs | "
        "13+ signed | 13+ abs | phantom | seats at stake in 4-12 |")
    add("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        b = r["bands"]
        ph = b.get("phantom", {"pp": float("nan"), "n": 0})
        add(f"| {r['city']} {r['year']} | {b['1-3']['signed_pp']:+.2f}pp | "
            f"{b['1-3']['abs_pp']:.2f}pp | "
            f"**{b['4-12']['signed_pp']:+.2f}pp** | {b['4-12']['abs_pp']:.2f}pp | "
            f"{b['13+']['signed_pp']:+.2f}pp | {b['13+']['abs_pp']:.2f}pp | "
            f"{ph['pp']:.2f}pp ({ph['n']}) | "
            f"{b['4-12']['seats_at_stake']:.0f} |")
    tot = {k: sum(r["bands"][k]["signed_pp"] for r in results)
           for k in ("1-3", "4-12", "13+")}
    tot_abs = {k: sum(r["bands"][k]["abs_pp"] for r in results)
               for k in ("1-3", "4-12", "13+")}
    phantom = sum((r["bands"].get("phantom") or {}).get("pp", 0.0)
                  for r in results)
    add(f"\n**Totals across {len(results)} city-years:** ranks 1-3 "
        f"{tot['1-3']:+.2f}pp signed / {tot_abs['1-3']:.2f}pp absolute, ranks "
        f"4-12 {tot['4-12']:+.2f}pp / {tot_abs['4-12']:.2f}pp, ranks 13+ "
        f"{tot['13+']:+.2f}pp / {tot_abs['13+']:.2f}pp.")
    add(f"\n**Phantom mass: {phantom:.2f}pp** on parties that did not stand at "
        f"all — including the generic `ENTRANT` column where no party arrived. "
        f"The bands iterate the parties that DID stand, so none of them can see "
        f"it; it is exactly why the three signed bands sum to "
        f"{sum(tot.values()):+.2f}pp rather than to zero.\n")

    add(render_wards(results))

    add(render_calibration(results))

    for r in results:
        add(f"\n## {r['city']} {r['year']}\n")
        add("| party | list median | list mean | list actual | ward mean | "
            "ward actual | seats model | seats actual |")
        add("|---|---|---|---|---|---|---|---|")
        seats = r["seats"]
        for party, pr_md, pr_mn, pr_a, wd_md, wd_mn, wd_a in r["votes"]:
            a, m = seats.get(party, (0, 0))
            add(f"| {party} | {pr_md:.2%} | {pr_mn:.2%} | {pr_a:.2%} | "
                f"{wd_mn:.2%} | {wd_a:.2%} | {m} | {a} |")
        missed = [p for p, (a, m) in seats.items() if a >= 3 and m == 0]
        if missed:
            add(f"\n**Missed entirely:** {', '.join(missed)} — won seats, "
                f"median zero.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# THE SERIAL-FORCING GUARD, and the evidence it runs on
# ---------------------------------------------------------------------------
#
# A MODULE CONSTANT SET IN THIS PROCESS DOES NOT REACH A WORKER.
# `ProcessPoolExecutor` spawns children that re-import every module fresh, so a
# sweep that sets `levels.SD_FLOOR` here and then fans out measures the DEFAULT
# at every value and reports a flat, confident null — "this constant does
# nothing" — which is `ITERATING.md` rule 6's fault exactly, and cause **A**
# (UNDELIVERED) of `NULL-RESULTS.md`. Refuse rather than mislead.
#
# **UNTIL 2026-08-27 THIS GUARD NAMED THE DEFECT IT WAS BUILT FOR AND DID NOT
# COVER IT.** Its comment cited "the one `LEVEL_DF` was in for weeks" and it
# then checked five hand-typed names, all in `levels`: SD_FLOOR, SD_CEILING,
# SHRINK, RELIABILITY_HALF, SPINE_K. `LEVEL_DF` is `montecarlo.LEVEL_DF`. It
# was not on the list. Neither was anything in `polling` — the whole `SIGMA_*`
# family — nor `montecarlo.SHARE_FLOOR`, `DIRICHLET_FLOOR` or
# `TURNOUT_DRAW_FLOOR/CEILING`. Of the 48 constants pre-registered for the B2
# sweep, the largest blocked class was exactly this one.
#
# **So the list is DERIVED, not maintained.**
# `test_levers_are_live.test_every_defaults_key_is_swept_or_excused` already
# records what a hand-maintained allowlist does in this repository — it covered
# **13 of 27** `DEFAULTS` keys and nobody had noticed — and a sixth name here
# would have been forgotten the same way. The watched set is instead read out of
# the modules themselves at import: every UPPERCASE int/float/bool bound at
# module level in a file under `src/`, compared against the value a fresh import
# produced. Measured 2026-08-27: **60 constants across 14 modules**, against the
# five it checked before, and it grows by itself when a constant is added. The
# printed coverage line is that count, so the claim is checked on every run
# rather than in this comment.
#
# Two things it deliberately does NOT flag:
#
#   * a name the module reassigns **itself** from inside a function —
#     `montecarlo.COUNCIL` and `PLAN_BOUNDS`, which `apply_city` and
#     `use_target` write on every run. Those are runtime state, not sweep
#     settings, and flagging them would force serial execution permanently
#     after the first run in a process. Derived by AST, so it needs no list
#     either: an UPPERCASE name assigned (or declared `global`) inside a
#     function body is excluded.
#   * a non-scalar — `DEFAULTS`, `PLAN_BOUNDS`, `NATIONAL_VOTES`. A sweep of a
#     scenario key belongs in `--set`, which crosses the boundary because it
#     travels in the job tuple; that is what the `--set` help text is for.
#
# The one hole left, and it is stated rather than papered over: the defaults are
# snapshotted when THIS module is imported, so a script that mutates a constant
# *before* importing `compare_history` records the mutated value as the default.
# `_modules_imported_before_us()` names the modules that could be in that
# position and the guard prints them, so the coverage claim is checkable rather
# than assumed.


def _project_modules() -> dict[str, object]:
    """Every module of THIS repository that is currently imported, BY FILE.

    Keyed by the file's own stem rather than by its `sys.modules` name, because
    one module object routinely holds several names: the file that was run is
    `__main__`, and `multiprocessing` registers that same object a second time
    as `__mp_main__` so a spawned child can find it. Keying by name counted
    this file's constants twice and reported "62 across 15 modules" for a tree
    with fourteen — a coverage claim that is wrong in the flattering direction,
    which is the one kind this file may not make.
    """
    here = Path(__file__).resolve().parent
    out: dict[str, object] = {}
    for mod in list(sys.modules.values()):
        path = getattr(mod, "__file__", None)
        if not path:
            continue
        try:
            resolved = Path(path).resolve()
        except OSError:                       # a synthetic module with a fake path
            continue
        if resolved.parent == here:
            out.setdefault(resolved.stem, mod)
    return out


def _module_constants(mod) -> dict[str, int | float | bool]:
    """The module's UPPERCASE scalar constants — the sweepable ones.

    `type(v) in (...)` rather than `isinstance`, so a numpy scalar or an IntEnum
    is left out: those do not compare cleanly and none of them is a lever.
    """
    return {name: value for name, value in vars(mod).items()
            if name.isupper() and not name.startswith("_")
            and type(value) in (int, float, bool)}


@functools.lru_cache(maxsize=None)
def _reassigned_at_runtime(path: str) -> frozenset[str]:
    """UPPERCASE names the module assigns from inside one of its own functions.

    `montecarlo.COUNCIL` is the case that matters: `apply_city` and
    `use_target` set it per city-year, so after one run it differs from its
    import-time value for a reason that has nothing to do with a sweep. Read
    off the source with `ast` so no name has to be listed anywhere.
    """
    try:
        tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    except (OSError, SyntaxError, ValueError):
        return frozenset()

    def targets(node):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, (ast.Tuple, ast.List)):
            for element in node.elts:
                yield from targets(element)

    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if isinstance(inner, ast.Global):
                names.update(inner.names)
            elif isinstance(inner, ast.Assign):
                for target in inner.targets:
                    names.update(targets(target))
            elif isinstance(inner, (ast.AugAssign, ast.AnnAssign, ast.For)):
                names.update(targets(inner.target))
    return frozenset(name for name in names if name.isupper())


def moved_module_constants() -> tuple[list[str], list[str]]:
    """``(moved, unwatched)`` — what would not survive a fork, and what is blind.

    ``moved`` names every watched constant whose value differs from the one a
    fresh import produced, formatted for the operator. ``unwatched`` names the
    modules that were imported after the snapshot and therefore have no
    recorded default at all.
    """
    moved, unwatched = [], []
    for label, mod in _project_modules().items():
        defaults = _IMPORT_TIME_CONSTANTS.get(label)
        if defaults is None:
            unwatched.append(label)
            continue
        changed = {const: value for const, value in _module_constants(mod).items()
                   if const in defaults and defaults[const] != value}
        if not changed:
            continue
        own = _reassigned_at_runtime(mod.__file__)
        for const in sorted(changed):
            if const in own:
                continue
            moved.append(f"{label}.{const} = {changed[const]!r} "
                         f"(import-time default {defaults[const]!r})")
    return sorted(moved), sorted(set(unwatched))


def _modules_imported_before_us() -> list[str]:
    """Project modules already in `sys.modules` when this one started executing.

    `sys.modules` is insertion-ordered and a module is registered before its
    body runs, so anything listed ahead of us was imported by somebody else
    first — and its constants could already have been changed by the time the
    snapshot below was taken. That is the guard's one blind spot and this is
    how it is reported rather than assumed.
    """
    names = list(sys.modules)
    if __name__ not in names:
        return []
    ahead = set(names[:names.index(__name__)])
    here = Path(__file__).resolve()
    out = set()
    for name in ahead:
        mod = sys.modules.get(name)
        path = getattr(mod, "__file__", None)
        if not path:
            continue
        try:
            resolved = Path(path).resolve()
        except OSError:
            continue
        if resolved.parent == here.parent and resolved != here:
            out.add(resolved.stem)
    return sorted(out)


# TAKEN HERE, at the bottom of the module body, so it includes this file's own
# constants (`REFERENCE_SHARE`, `REFERENCE_SLATE`) — which are read inside the
# worker by `reference_universe` and so do not cross the boundary either.
_IMPORT_TIME_CONSTANTS = {label: _module_constants(mod)
                          for label, mod in _project_modules().items()}
_IMPORTED_BEFORE_US = _modules_imported_before_us()


# Operational, not a modelling choice: it versions the SHAPE of the scoreboard
# envelope so a reader can tell a manifested artefact from a bare one. Exempt
# from JUDGEMENT-CALLS for the same reason `publication.SCHEMA` is.
HISTORY_SCHEMA = 1
_MANIFEST_FOR_RENDER: dict | None = None


def _archive_targets() -> list[tuple[str, str]]:
    """Every city-year the archive supports, regardless of what this run chose.

    The denominator `population.excluded` is measured against. Derived, never
    typed — a typed panel list is how §1.69 stayed wrong for months.
    """
    out = []
    for slug in CITIES:
        try:
            years, refused = runnable(cityconfig.load(slug))
        except Exception:
            continue
        out += [(slug, y) for y in years] + [(slug, y) for y, _ in refused]
    return out


def build_manifest(args, excluded, results) -> dict:
    """What produced this scoreboard, assembled from `freeze`'s existing code.

    ⛔ `history.json` ARBITRATES EVERYTHING IN THIS PROJECT AND, UNTIL NOW,
    DECLARED NOTHING ABOUT ITSELF. Meanwhile `freeze.py` writes a full manifest
    — git sha, dirty flag, draws, seed, resolved env switches, every input
    spec's artefact key — onto `forecast_frozen.json`, **the one artefact
    `CLAUDE.md` bars from arbitrating anything.** The apparatus was pointed at
    the wrong artefact; this points it at the right one.

    ⚠️ EVERY FIELD IS A CALL INTO `freeze`, NOT A REIMPLEMENTATION. This
    repository already carries three dialects of "declare your identity"
    (`pools.artefact_key`, `freeze.bundle`, `publication.run_identity`), each
    grown around one artefact. A fourth would be the disease, not the cure — and
    the no-duplicated-logic rule is the same one that retired `leverage.py`.

    `excluded` is recorded, not just printed. It is the panel denominator, it
    was quietly smaller than the archive for months (§1.69), and stdout is not
    an artefact.
    """
    import freeze as F
    return {
        "schema": HISTORY_SCHEMA,
        "generated": _dt.datetime.now(_dt.timezone.utc)
                        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "draws": args.draws,
        # The seed every city-year actually ran at. `run_city_year` passes
        # seed=None, which is falsy, so each one takes DEFAULTS["seed"].
        "seed": M.DEFAULTS.get("seed"),
        "overrides": list(args.set or []),
        "git_commit": F._git("rev-parse", "HEAD"),
        "git_dirty": F._dirty_excluding(args.json, args.md),
        "env_switches": F.resolved_switches(),
        "pool_artefact_keys": {
            slug: F.pool_artefact_keys(cityconfig.load(slug))
            for slug in sorted({r["slug"] for r in results})},
        # THE POPULATION, BOTH WAYS. What was scored, and what the archive
        # supports but this run did not cover. A denominator that is only
        # implicit in the length of a list is the shape §1.69 got wrong.
        #
        # ⛔ AND THE FIRST VERSION RECORDED ONLY `runnable()` REFUSALS, SO THE
        # CLI FILTERS WERE INVISIBLE TO IT. `--city joburg` overwrites the
        # canonical scoreboard with three rows and a manifest reading
        # `excluded: []` — which ASSERTS that the archive supports three. That
        # is §1.69 reinstated inside the fix for §1.69, and stamped into an
        # artefact rather than merely printed. The filters are now recorded,
        # and `excluded` is derived from the full archive minus what was
        # scored, not from refusals alone.
        "filters": {"city": args.city, "target": args.target},
        "population": {
            "scored": [f"{r['slug']}:{r['year']}" for r in results],
            "n_scored_rows": len(results),
            "excluded": ([{"city": c, "year": y, "why": w}
                          for c, y, w in excluded]
                         + [{"city": c, "year": y, "why": "not selected by "
                             "--city/--target on this run"}
                            for c, y in _archive_targets()
                            if f"{c}:{y}" not in
                            {f"{r['slug']}:{r['year']}" for r in results}
                            and not any(c == e[0] and y == e[1]
                                        for e in excluded)]),
        },
    }


def load_history(path) -> tuple[dict, list[dict]]:
    """Read a scoreboard artefact, and REFUSE the pre-manifest shape.

    Returns ``(manifest, records)``.

    ⛔ IT DOES NOT ACCEPT BOTH SHAPES. A helper that silently copes with an old
    artefact is exactly the quiet fallback this repository forbids elsewhere
    (`test_calibration_report.py`'s "falls back LOUDLY"), and here it would be
    self-defeating: the whole point is that a number cannot be quoted without
    the manifest that says what produced it, so a path that yields records with
    no manifest reinstates the defect.
    """
    payload = json.loads(Path(path).read_text())
    if isinstance(payload, list):
        raise SystemExit(
            f"{path} is a bare list — the pre-manifest scoreboard shape. It "
            f"carries no git sha, no draw count, no seed, no env switches and "
            f"no declared population, so nothing measured against it can be "
            f"shown to be comparable with anything else. Re-run "
            f"`src/compare_history.py` to produce a scoreboard that declares "
            f"itself. (Refused rather than read: a number without its "
            f"provenance is how §1.214 happened.)")
    if not isinstance(payload, dict) or "records" not in payload:
        raise SystemExit(
            f"{path} is neither a bare list nor a manifest envelope; top level "
            f"is {type(payload).__name__} with keys "
            f"{sorted(payload)[:8] if isinstance(payload, dict) else '-'}.")
    return payload.get("manifest") or {}, payload["records"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--city", default=None)
    ap.add_argument("--target", default=None)
    ap.add_argument("--data-dir", type=Path, default=Path("data/raw/elections"))
    ap.add_argument("--md", type=Path, default=Path("data/processed/history.md"))
    ap.add_argument("--json", type=Path, default=Path("data/processed/history.json"))
    ap.add_argument("--jobs", type=int, default=0, metavar="N",
                    help="run the city-years in N parallel PROCESSES. 0 (the "
                         "default) picks one per city-year up to the machine's "
                         "cores less one; 1 forces the serial loop. The "
                         "city-years are independent -- each reads its own "
                         "pools spec and derives its own PIT seed from its "
                         "name -- so this changes no number, and a run that "
                         "disagrees with the serial one is a bug rather than a "
                         "speedup.")
    ap.add_argument("--run-dir", type=Path, default=None,
                    help="write a TRACE per city-year here: every stage's "
                         "output as JSON, so an intermediate can be read "
                         "instead of re-derived by re-running. Changes no "
                         "number in the comparison.")
    ap.add_argument("--set", action="append", metavar="KEY=VALUE",
                    help="override a scenario key for EVERY city-year, e.g. "
                         "--set entrant_prob=0.5. This is the only honest way to "
                         "sweep a constant here: editing montecarlo.DEFAULTS does "
                         "NOT reach a run, because apply_city writes cities/"
                         "<city>.toml's scalars over DEFAULTS afterwards — and "
                         "leaves them there for every city that follows. A sweep "
                         "of DEFAULTS returns byte-identical rows and reads as "
                         "'this constant does nothing'.")
    args = ap.parse_args(argv)

    jobs_list = []
    excluded: list[tuple[str, str, str]] = []
    for slug in ([args.city] if args.city else CITIES):
        city = cityconfig.load(slug)
        years, refused = runnable(city)
        excluded += [(slug, y, why) for y, why in refused]
        for year in years:
            if args.target and year != args.target:
                continue
            jobs_list.append((slug, year, args.draws, str(args.data_dir),
                              args.set, str(args.run_dir) if args.run_dir else None))

    # WHAT THE PANEL IS NOT SCORING, AND WHY. Printed unconditionally, because
    # the number of city-years is the denominator of every claim this report
    # makes and it had been quietly smaller than the archive for months. A
    # panel of nine, when the archive supports twenty-four, is a fact about
    # emission and ingest — not about the data — and nothing said so.
    # MODEL-LOG §1.69.
    if excluded:
        print(f"panel: {len(jobs_list)} city-year(s) scored, "
              f"{len(excluded)} the archive supports but this harness cannot:")
        for slug, year, why in excluded:
            print(f"    {slug} {year}: {why}")

    # THE SERIAL-FORCING GUARD. See the block above `_project_modules` for what
    # it watches, why the list is derived rather than typed, and what it cannot
    # see. Its coverage is printed unconditionally: a guard that reports nothing
    # is indistinguishable from a guard that is not running, and this one spent
    # weeks in exactly that state.
    _moved, _unwatched = moved_module_constants()
    _watched = sum(len(c) for c in _IMPORT_TIME_CONSTANTS.values())
    print(f"guard: {_watched} module constants across "
          f"{len(_IMPORT_TIME_CONSTANTS)} modules watched for values that "
          f"would not survive the fork")
    if _unwatched:
        print(f"  ! no import-time default recorded for {', '.join(_unwatched)}"
              f" — imported after compare_history, so a changed constant there "
              f"is INVISIBLE to this guard. Import compare_history first.")
    if _IMPORTED_BEFORE_US:
        print(f"  ! {', '.join(_IMPORTED_BEFORE_US)} were imported before "
              f"compare_history, so their recorded 'defaults' are whatever they "
              f"held at that moment. A constant changed before this import "
              f"reads as unchanged.")
    workers = args.jobs
    if _moved and workers != 1:
        print(f"  ! {'; '.join(_moved)} — and a module constant does not cross "
              f"a process boundary, so a worker would re-import the default and "
              f"the sweep would report a flat, confident null. Running SERIALLY "
              f"so it measures what it set. Pass --jobs 1 to silence this.")
        workers = 1
    if workers == 0:
        workers = max(1, min(len(jobs_list), (os.cpu_count() or 2) - 1))
    results = []
    if workers > 1 and len(jobs_list) > 1:
        # Order is preserved by index, not by completion, so the report and the
        # artefact read the same however the work finishes.
        print(f"  running {len(jobs_list)} city-years across {workers} processes",
              flush=True)
        done = [None] * len(jobs_list)
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_run_one, job): i
                       for i, job in enumerate(jobs_list)}
            for fut in as_completed(futures):
                i = futures[fut]
                slug, year = jobs_list[i][0], jobs_list[i][1]
                try:
                    done[i] = fut.result()
                    print(f"  {slug} {year} done", flush=True)
                except Exception as exc:
                    print(f"  {slug} {year} failed: {type(exc).__name__}: {exc}")
        results = [r for r in done if r is not None]
    else:
        for slug, year, draws, data_dir, overrides, run_dir in jobs_list:
            print(f"  {slug} {year} ...", flush=True)
            try:
                results.append(run_city_year(slug, year, draws, Path(data_dir),
                                             overrides,
                                             run_dir=Path(run_dir) if run_dir else None))
            except Exception as exc:
                print(f"    failed: {type(exc).__name__}: {exc}")
    if not results:
        print("nothing runnable")
        return 1
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(
        {"manifest": build_manifest(args, excluded, results),
         "records": results}, indent=2, default=float))
    text = render(results, build_manifest(args, excluded, results))
    args.md.write_text(text)
    print(text)
    print(f"\nwrote {args.md} and {args.json}")
    return 0


if __name__ == "__main__":
    # FIRST, because it may replace the process -- and re-execing while holding
    # the artefact lock would hand the child a lock the parent never released.
    # It also fixes the seed for the sixteen worker processes, which inherit
    # `os.environ` at spawn: until 2026-08-27 each of them had its own.
    M.fix_hash_seed()
    # A MEASUREMENT MAY NOT RUN WHILE THE POOL SPECS ARE BEING WRITTEN.
    # Held as a SHARED lock, so several readers may run at once (the sixteen
    # city-years already run in parallel processes) while an emit is excluded.
    # On 2026-08-27 two background emits raced and left eighteen specs carrying
    # two different `pools_sha` values; every number measured against that tree
    # was meaningless. See pools.artefact_lock.
    import pools as _pools
    with _pools.artefact_lock("read", "compare_history"):
        raise SystemExit(main())
