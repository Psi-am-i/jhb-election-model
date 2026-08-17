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
with different remedies, and **this model's answer to both differs by rank
band** — over-forecast and too wide at ranks 1-3, under-forecast and far too
narrow at ranks 4-12 — so the calibration is reported split by actual PR rank as
well as pooled. The pooled figure alone is the average of two opposite biases
and describes neither. See :func:`render_calibration`, :func:`pooled_by_band`
and MODEL-LOG §1.34, §1.36.

Usage::

    python src/compare_history.py                    # everything runnable
    python src/compare_history.py --city joburg
    python src/compare_history.py --draws 2000 --md report.md
"""

from __future__ import annotations

import argparse
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
    ActionSA (−12.59). That city-year is the model's WORST on seats (104 of
    error) and read second-best on this table. Across the nine city-years the
    signed total for ranks 1-3 is +32.50pp against 71.12pp absolute — an
    understatement of 2.2×.

    **EVERY FIGURE ABOVE IS THE COMMITTED ``data/processed/history.json`` AT
    1500 DRAWS, and none of them may be quoted without that.** This is a Monte
    Carlo statistic and it moves in the second decimal with the draw count and
    the seed. Three different values of the ranks 1-3 nine-city-year total
    shipped inside one commit — +32.67/72.06 in this docstring, +32.42/71.65 in
    MODEL-LOG §1.34's table, +32.50/71.12 in the committed ``history.json`` —
    all the same statistic at different draw counts, and a reader had no way to
    tell a re-run from a regression. **Quote the draw count with the number, or
    quote neither.** See MODEL-LOG §1.34 and §1.36.

    **PHANTOM MASS.** The bands iterate the parties that actually stood, so any
    share the model gives to a party that did not stand at all is invisible to
    every band. It is reported separately rather than left out: the citywide
    share vector sums to one over the model's own universe, so the phantom total
    is exactly why the three bands sum to −6.53pp rather than to zero across the
    nine city-years (committed ``history.json``, 1500 draws). It includes the
    generic ``ENTRANT`` column in a city-year where no party arrived, which is a
    real error and should be visible as one.

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
    out = {}
    for name in POPULATIONS:
        mask = masks[name]
        out[name] = {
            "n": int(mask.sum()),
            "parties": [p for p, keep in zip(parties, mask) if keep],
            "pit": [float(v) for v in np.asarray(pits)[mask]],
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
    """
    groups = [np.asarray(g, dtype=float) for g in groups if len(g)]
    if len(groups) < 2:
        return float("nan"), float("nan"), draws
    rng = np.random.default_rng(seed)
    k = len(groups)
    means = np.empty(draws, dtype=float)
    kept = 0
    for pick in rng.integers(0, k, size=(draws, k)):
        sample = np.concatenate([groups[i] for i in pick])
        means[kept] = sample.mean()
        kept += 1
    lo, hi = np.percentile(means[:kept], [100 * (1 - level) / 2,
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

    On this model's ``claimed`` population (committed ``history.json``, 1500
    draws) the pooled mean is 0.587 and the split is:

        ranks 1-3    n=27  mean PIT 0.431   50% coverage 0.70
        ranks 4-12   n=26  mean PIT 0.750   50% coverage 0.27

    Two biases in opposite directions, both cluster-bootstrap CIs excluding
    0.50, and the pooled figure is their average. The model **over**-forecasts
    the top three and **under**-forecasts the middle — which is exactly what the
    signed vote bands (+32.50pp at ranks 1-3, −37.34pp at 4-12) had been saying
    all along. The two instruments never disagreed; only one of them was
    disaggregated.

    Width splits the same way, and **the two coverage measures disagree in one
    band and not the other, which is itself the finding.** ``score.coverage``
    reads the empirical quantile interval, which on integer seats has to include
    whole endpoints and therefore over-covers; the randomised PIT corrects for
    exactly that, so the fraction of columns whose PIT falls in the central
    ``level`` is the discreteness-corrected version of the same number. At a
    nominal 50%:

        ranks 1-3    interval 0.70   PIT-corrected 0.70   -> too WIDE
        ranks 4-12   interval 0.46   PIT-corrected 0.27   -> too NARROW

    Ranks 1-3 are big parties whose forecast distributions are tens of seats
    wide, so one endpoint is a negligible share of the interval and the two
    measures come out equal. Ranks 4-12 are parties on one to ten seats, where a
    single endpoint is a large fraction of the interval and the raw coverage is
    inflated by 19 points.
    So "the bands are roughly the right width" is true at the top of the ballot,
    approximately true in the middle if you read the uncorrected number, and
    false in the middle once you correct for discreteness. Both columns are
    printed; the PIT-corrected one is the one that answers the question.
    """
    out = {}
    for band in (*BAND_LABELS, "off-ballot"):
        per_city: list[list[float]] = []
        cov = {level: {"inside": 0, "counted": 0} for level in LEVELS}
        for r in results:
            block = (r.get("calibration") or {}).get(pop)
            if not block or "band" not in block:
                continue
            labels = block["band"]
            here = [float(u) for u, b in zip(block["pit"], labels) if b == band]
            per_city.append(here)
            for hit, b in zip(block.get("hits") or [], labels):
                if b != band:
                    continue
                for level, inside in zip(LEVELS, hit):
                    cov[level]["inside"] += int(inside)
                    cov[level]["counted"] += 1
        pits = [u for g in per_city for u in g]
        if not pits:
            continue
        lo, hi, boot_draws = _cluster_bootstrap_ci(per_city)
        u = np.asarray(pits, dtype=float)
        out[band] = {
            "n": len(pits),
            "mean_pit": float(np.mean(pits)),
            "ci": [lo, hi],
            "ci_replicates": int(boot_draws),
            "coverage": [
                {"level": level, "inside": acc["inside"],
                 "counted": acc["counted"],
                 "empirical": (acc["inside"] / acc["counted"]
                               if acc["counted"] else float("nan"))}
                for level, acc in cov.items()],
            # The same coverage question asked of the randomised PIT, which is
            # continuous by construction and so carries no discreteness
            # inflation. Where this and ``coverage`` disagree, the parties in
            # the band are small enough that a whole seat is a large part of the
            # interval — and THIS is the number to read.
            "pit_coverage": [
                {"level": level,
                 "inside": int(((u >= (1 - level) / 2)
                                & (u <= (1 + level) / 2)).sum()),
                 "counted": int(u.size),
                 "empirical": float(((u >= (1 - level) / 2)
                                     & (u <= (1 + level) / 2)).mean())}
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


def run_city_year(city_slug: str, year: str, draws: int, data_dir: Path,
                  overrides: list[str] | None = None) -> dict:
    city = cityconfig.use(city_slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    # `set` AFTER apply_city, which is the whole point: apply_city writes the
    # city toml's scalars over DEFAULTS, so a --set is the only override that
    # survives it. See the --set help text.
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=list(overrides or []), draws=draws, seed=None,
        city=city_slug, target=year))
    run = M.run_model(target, scenario, data_dir, verbose=False)

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

    Coverage says whether the intervals are the right WIDTH; the PIT mean says
    whether they are in the right PLACE. **Both answers are band-dependent here,
    and a single pooled number gives the wrong one for both.** On the claimed
    columns (committed ``history.json``, 1500 draws) ranks 1-3 come out at mean
    PIT 0.431 with a nominal 50% interval covering 70%, and ranks 4-12 at 0.750
    covering 27% once discreteness is corrected for: over-forecast and too wide
    at the top, under-forecast and too narrow in the middle. Pooled they average
    to 0.588 and "58% at a nominal 50%", which is neither band's answer and is
    not a description of any part of this model.
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
        "heuristic, which reads the end mass and the mean; **the χ² column is "
        "the test.** They can disagree — a histogram can be sloped rather than "
        "U-shaped, print 'approximately flat' and still be far past the "
        "critical value, which is what a level bias looks like when it is "
        "spread over the upper half rather than piled in the last bin.")
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
    for band in (*BAND_LABELS, "off-ballot"):
        blk = band_block.get(band)
        if not blk:
            continue
        cov = {row["level"]: row["empirical"] for row in blk["coverage"]}
        pit_cov = {row["level"]: row["empirical"] for row in blk["pit_coverage"]}
        lo, hi = blk["ci"]
        ci = ("—" if lo != lo else f"[{lo:.3f}, {hi:.3f}]")
        add(f"| {_BAND_LABEL[band]} | {blk['n']} | {blk['mean_pit']:.3f} | {ci} | "
            + " | ".join(f"{100 * cov.get(level, float('nan')):.0f}%"
                         for level in LEVELS) + " | "
            + " | ".join(f"{100 * pit_cov.get(level, float('nan')):.0f}%"
                         for level in LEVELS) + " |")
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
        "an endpoint is a large part of the interval. **Read the PIT columns for "
        "the width verdict.**\n")
    add("**Read the sign and the width together, per band.** A mean PIT below "
        "0.50 with coverage ABOVE the nominal level is a band the model forecasts "
        "too high with intervals too wide. A mean above 0.50 with coverage BELOW "
        "the nominal level is a band forecast too low with intervals too narrow. "
        "This model has one of each, which is why no single sentence about its "
        "width or its level is true of the whole ballot — and why the rank-band "
        "vote table above (top three over, middle short) and this table are the "
        "same finding measured twice.\n")

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

    results = []
    for slug in ([args.city] if args.city else CITIES):
        city = cityconfig.load(slug)
        for year in runnable(city):
            if args.target and year != args.target:
                continue
            print(f"  {slug} {year} ...", flush=True)
            try:
                results.append(run_city_year(slug, year, args.draws, args.data_dir,
                                         args.set))
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
