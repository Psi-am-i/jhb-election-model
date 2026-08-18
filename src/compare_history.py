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
import montecarlo as M
import score as S
from fold import citywide, load

CITIES = ["joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
          "mangaung", "nelsonmandelabay", "buffalocity"]


def runnable(city) -> list[str]:
    out = []
    for year in B.runnable_targets(city):
        if (city.processed / f"pools_{year}.json").exists():
            out.append(year)
    return out


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
# The difference between them IS the finding, so all three are reported and each
# is labelled with what selects it. See :func:`calibration_columns`.
POPULATIONS = ("claimed", "seat_holders", "all")

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

    **It is not load-bearing for the figure this report quotes, and that was
    checked rather than assumed.** The ``claimed`` population carries no PIT at
    0 or 1 (its range on the committed artefact is 0.052 to 0.997), and the
    per-band probit-SD is 0.7399 / 0.7338 at ``1e-4``, ``1e-6`` and ``1e-8``
    alike — unchanged to four decimals across four orders of magnitude. It IS
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


def calibration_columns(seat_draws, actual_seats, entrant_actual, seed,
                        actual_pr=None):
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
    them and reports "fine". This model's ``claimed`` population pools to 0.587
    and is −0.069 at ranks 1-3 and +0.250 at ranks 4-12. Every block below
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
    pits = S.pit_values(samples, truth, seed=seed)
    n_cols = samples.shape[1] if samples.ndim == 2 else 0
    claimed = ((samples > 0).mean(axis=0) >= S.CLAIM_FRACTION
               if samples.shape[0] else np.zeros(n_cols, dtype=bool))
    masks = {"claimed": claimed,
             "seat_holders": truth > 0,
             "all": np.ones(n_cols, dtype=bool)}
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
        mask = masks[name]
        out[name] = {
            "n": int(mask.sum()),
            "parties": [p for p, keep in zip(parties, mask) if keep],
            "pit": [float(v) for v in np.asarray(pits)[mask]],
            "z": [v for v, keep in zip(z_cols, mask) if keep],
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


def pooled_calibration(results, bins: int = 10) -> dict:
    """Coverage and PIT summed over every city-year, pooled AND split by rank.

    Coverage pools by adding hits and columns; PIT pools by concatenating the
    values, because each column is one draw from what should be U(0,1) whatever
    city-year it came from. A per-city-year figure on seven to fifteen columns
    cannot separate 50% from 80%; the pooled one on ~130 can.

    **The pooled figure must not be read alone, and the ``by_band`` block is
    why.** Pooling over city-years is what makes the statistic readable;
    pooling over rank bands is what makes it wrong. This model's ``claimed``
    population pools to a mean PIT of 0.587 and splits into 0.431 at ranks 1-3
    and 0.750 at ranks 4-12 — an over-forecast averaged with an under-forecast.
    See :func:`pooled_by_band` and MODEL-LOG §1.36.
    """
    out = {}
    for pop in POPULATIONS:
        pits: list[float] = []
        cov: dict[float, dict] = {}
        for r in results:
            block = (r.get("calibration") or {}).get(pop)
            if not block:
                continue
            pits.extend(block["pit"])
            for row in block["coverage"]:
                acc = cov.setdefault(float(row["level"]),
                                     {"inside": 0, "counted": 0})
                acc["inside"] += int(row["inside"])
                acc["counted"] += int(row["counted"])
        out[pop] = {
            "n": len(pits),
            "pit": S.pit_histogram(np.array(pits, dtype=float), bins=bins),
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


def pooled_by_band(results, pop) -> dict:
    """The pooled calibration of one population, SPLIT BY ACTUAL PR RANK.

    **This is the fix for the fault that shipped, and it is worth stating
    plainly why the split is not optional.** A pooled mean PIT is an average
    over columns. If the population contains two subsets biased in opposite
    directions, the average sits between them and reports something close to
    0.5 — "well centred" — while neither subset is. That is precisely the
    argument that condemned :func:`rank_bands`' signed sum one day earlier, and
    the pooled PIT shipped in the same commit with the same defect.

    On this model's ``claimed`` population (committed ``history.json``) the
    pooled mean is 0.598 and the split is:

        ranks 1-3    n=27  mean PIT 0.434
        ranks 4-12   n=28  mean PIT 0.757

    Two biases in opposite directions, both cluster-bootstrap CIs excluding
    0.50, and the pooled figure is their average. The model **over**-forecasts
    the top three and **under**-forecasts the middle — which is exactly what the
    signed vote bands (+32.52pp at ranks 1-3, −37.18pp at 4-12) had been saying
    all along. The two instruments never disagreed; only one of them was
    disaggregated.

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
        for r in results:
            block = (r.get("calibration") or {}).get(pop)
            if not block or "band" not in block:
                continue
            labels = block["band"]
            here = [float(u) for u, b in zip(block["pit"], labels) if b == band]
            per_city.append(here)
            z_all.extend(v for v, b in zip(block.get("z") or [], labels)
                         if b == band and v is not None)
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


def published_for(city_slug: str, year: str) -> dict | None:
    path = Path("data/processed") / f"validation_{year}.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text())
    except Exception:
        return None
    entry = (payload.get("cities") or {}).get(city_slug)
    return entry


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
    actual_seats, entrant_actual = _actual_seats(target, data_dir, run)
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
        "calibration": calibration_columns(
            run.seat_draws, actual_seats, entrant_actual,
            _pit_seed(city_slug, year), actual_pr=actual_pr),
        "opponents": {},
    }
    scored = S.score_seats(run.seat_draws, actual_seats,
                           entrant_actual=entrant_actual)
    out["crps"] = scored["crps"]["total"]

    ctx = BM.build_context(int(year), data_dir)
    for name in ("last-lge", "uniform-swing", "prior-lge-noise"):
        try:
            seat_draws = BM.run_one(name, ctx, draws=min(draws, 2000))
        except SystemExit as exc:
            out["opponents"][name] = {"error": str(exc)}
            continue
        bench_seats = seats_from_draws(seat_draws)
        out["opponents"][name] = {
            "crps": S.score_seats(seat_draws, actual_seats,
                                  entrant_actual=entrant_actual)["crps"]["total"],
            "seat_abs_err": sum(
                abs(actual_seats.get(p, 0) - bench_seats.get(p, 0))
                for p in set(actual_seats) | set(bench_seats))}

    pub = published_for(city_slug, year)
    if pub and pub.get("model"):
        m = pub["model"]
        out["opponents"]["published"] = {
            "crps": m.get("crps"),
            "seat_abs_err": sum(
                abs(r["actual"] - r["forecast"]) for r in m.get("parties", [])),
            "generated": pub.get("generated")}
    return out


def _actual_seats(target, data_dir: Path, run):
    """The published council for this target, via the backtest's own reader.

    ``actual_result`` returns more than the seats and its arity has changed
    before, so the seat map is picked out by shape rather than by position.
    ``entrant_actual`` needs the model's own BASELINE — which party had no
    national share to grow from — not the target, which is what makes a
    correctly sized newcomer score as a newcomer rather than as a total miss.
    """
    path = data_dir / target.results(target.year)
    actual = B.actual_result(path, target.council, int(target.year))
    seats = None
    for item in (actual if isinstance(actual, tuple) else (actual,)):
        if hasattr(item, "seats"):
            seats = item.seats
            break
        if isinstance(item, dict) and item and all(
                isinstance(v, (int, float)) for v in item.values()):
            seats = item
            break
    if seats is None:
        raise ValueError(f"actual_result returned no seat map for {target.year}")
    base = {p: 1.0 for p in run.index}
    return seats, B.entrant_actual_for(seats, base)


_POP_LABEL = {
    "claimed": "claimed by the model (forecast-selected — the neutral test)",
    "seat_holders": "won a seat (outcome-selected — INFLATED by construction)",
    "all": "every scored column (MIXED: outcome-selected + neutral, diluted)",
}

_BAND_LABEL = {
    "1-3": "ranks 1-3",
    "4-12": "ranks 4-12",
    "13+": "ranks 13+",
    "off-ballot": "off-ballot (no actual PR rank)",
}


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


def render(results: list[dict]) -> str:
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
        def cell(key, field="seat_abs_err"):
            v = o.get(key, {})
            if "error" in v or v.get(field) is None:
                return "—"
            return f"{v[field]:.0f}" if field == "seat_abs_err" else f"{v[field]:.1f}"
        add(f"| {r['city']} {r['year']} | {r['council']} | "
            f"{r['pr_mae']:.2f}pp | {r['ward_mae']:.2f}pp | "
            f"{r['seat_abs_err']} | {r['median_sum']} | "
            f"{r['seat_abs_err_coherent']} | {r['crps']:.1f} | "
            f"{cell('last-lge')} | {cell('uniform-swing')} | "
            f"{cell('prior-lge-noise')} |")
    add("\n**Read the two seat-error columns together.** *seat err (median)* "
        "uses the per-party marginal median, which is what the per-party tables "
        "below show and which **does not sum to a council** — the *medians sum "
        "to* column says by how much. *seat err (coherent)* apportions the mean "
        "seat vector by largest remainder, so it IS a chamber and is the only "
        "one comparable to the baselines, which allocate per draw and sum "
        "exactly. Lower is better throughout.\n")

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
    for slug in ([args.city] if args.city else CITIES):
        city = cityconfig.load(slug)
        for year in runnable(city):
            if args.target and year != args.target:
                continue
            jobs_list.append((slug, year, args.draws, str(args.data_dir),
                              args.set, str(args.run_dir) if args.run_dir else None))

    workers = args.jobs
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
    args.json.write_text(json.dumps(results, indent=2, default=float))
    text = render(results)
    args.md.write_text(text)
    print(text)
    print(f"\nwrote {args.md} and {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
