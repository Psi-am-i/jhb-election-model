"""Proper scoring rules for a distributional forecast of a council.

``backtest.py`` currently reports two numbers: the total absolute error of the
median seat count, and the share of parties whose actual seat count fell inside
the 90% band. Both are weak. Median absolute error throws away the whole
distribution -- a forecast that says "ANC 90-100, flat" and one that says "ANC
95 with certainty" score identically when the answer is 95, though only one of
them was honest about what it knew. And a single hit rate over ~10 parties has
so little statistical power that 8/10 and 9/10 are indistinguishable noise.

This module replaces both with rules that are *proper*: a forecaster minimises
its expected score only by reporting what it actually believes. Nothing here
knows about this model; every function takes samples and an outcome, so the
Monte Carlo, a naive benchmark from ``benchmarks.py``, and any future variant
are all scored by the same code.

What is here, and what each thing is for:

============================  ===========  ==================================
rule                          orientation  what it rewards
============================  ===========  ==================================
``crps_sample``               lower        sharp *and* calibrated marginals
``pit_values`` + histogram    shape        shows *how* the spread is wrong
``coverage``                  match        interval honesty at 50/80/90
``brier`` + reliability       lower        ward-winner probabilities that
                                           mean what they say
``energy_score``              lower        the joint seat vector, so errors
                                           that move together are penalised
``variogram_score``           lower        the correlation structure itself
============================  ===========  ==================================

The highest-power test in the table is the ward one. A metro council backtest
offers about ten parties worth of seat outcomes per target -- thirty across
2011/2016/2021, and they are not independent. The same targets offer ~135 ward
contests each, ~405 in total, each a genuine event with a predicted
probability. Calibration is measurable there and essentially not measurable on
seats alone, so a model that is well calibrated on wards and mis-calibrated on
seats has a problem in the *seat allocator or the correlation structure*, not
in the vote model. The two together localise the fault; either alone does not.

Everything is pure: no I/O, no globals, no model imports.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence

import numpy as np

# Calibration is scored on the seats a forecaster actually CLAIMS: columns
# where it gives a seat in at least this fraction of its draws. Selecting on
# the forecast keeps PIT uniform under calibration; selecting on the outcome
# does not. See :func:`seat_matrix`.
CLAIM_FRACTION = 0.50

# There is deliberately NO materiality threshold on the scored column set. One
# was tried at 0.10 and it made the joint score improper: because
# :func:`variogram_score` sums over d(d-1)/2 pairs, dropping columns drops
# pairs, and a forecaster could shade 36 near-threshold claims below the cliff
# — conserving total seats, changing nothing it believed — and improve its
# variogram 4.2x. It bought 0.02 of CRPS and cost the property the whole module
# exists for. Spurious mass is penalised by being scored, not excused by being
# filtered.

# ---------------------------------------------------------------------------
# turning a list of {party: seats} draws into arrays
# ---------------------------------------------------------------------------


def _as_matrix(samples: np.ndarray) -> np.ndarray:
    """``samples`` as a 2-D ``(n_draws, n_parties)`` array.

    Every rule below indexes ``shape[1]``, and an empty forecast is a legitimate
    input -- zero draws, or a forecast whose every column was filtered away.
    NumPy gives those shape ``(0,)``, so without this they raise ``IndexError``
    rather than returning an empty score. Anything else 1-D is a caller bug and
    is rejected, because there is no way to tell one draw of ten parties from
    ten draws of one.
    """
    x = np.asarray(samples, dtype=float)
    if x.ndim == 2:
        return x
    if x.size == 0:
        return x.reshape(0, 0)
    raise ValueError(f"expected a 2-D (draws, parties) array, got shape {x.shape}")


def seat_matrix(
    draws: Sequence[Mapping[str, int]],
    actual: Mapping[str, int],
    entrant_actual: str | None = None,
    keep_all: bool = False,
    parties: Sequence[str] | None = None,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """``(parties, samples[n_draws, n_parties], actual[n_parties])``.

    Missing parties are zero seats, not missing data -- a draw that never
    mentions a party predicted it out of the council, and that is a prediction.

    ``entrant_actual`` renames the model's generic ``ENTRANT`` to whichever
    party actually arrived from nothing, matching ``backtest.score``: the model
    cannot know a newcomer's name, and scoring a correctly sized newcomer as a
    total miss would answer a question nobody asked.

    Parties are kept when they won a seat *or* this forecaster's own draws gave
    them one, so spurious predicted mass is penalised by being scored rather
    than excused by being filtered. There is deliberately no materiality cliff
    here: one was tried and it made the variogram improper, because dropping a
    column drops pairs and a forecaster could shade its claims below the
    threshold to improve its own score. ``keep_all=True`` keeps the full
    universe, including parties that are zero everywhere and contribute nothing
    but dilution.

    WHICH COLUMNS TEST CALIBRATION is a separate question, answered in
    :func:`score_seats`, and answered on the forecast side — see there for why
    selecting on the outcome is not neutral.

    **The scored column set depends only on this forecaster and the result.**
    That is the property the rules below need and it is easy to lose. An earlier
    version took a shared party list built from every forecaster in the run
    (:func:`relevant_parties`) and scored each model over all of it, on the
    theory that a common denominator is what makes a comparison fair. It is not:
    a column where *both* the truth and this forecaster are zero is an interval
    ``[0, 0]`` containing ``0``, a free coverage hit at every level, and a PIT
    value drawn from ``U(0, 1)``, which flattens the histogram towards the very
    shape it exists to test for. So a forecaster's coverage moved when an
    unrelated forecaster joined the run -- uniform-swing's 90% coverage at 2016
    read 25%, 50% or 37% depending on who else was being scored that day. The
    model-dependent denominator had not been removed, only relocated from the
    model to the roster.

    ``parties`` therefore declares a *candidate universe* and fixes the column
    order; the zero-everywhere filter still runs on top of it (use ``keep_all``
    to genuinely score a fixed universe). Because any sensible candidate list is
    a superset of "truth or own draws non-zero", passing one changes nothing
    about the numbers -- which is the point: the score is a property of the
    forecast and the outcome, not of the company it is scored in.
    """
    if entrant_actual:
        # SUM, do not overwrite. A dict comprehension keyed on a rename keeps
        # the LAST colliding value, and ``universe`` is sorted with "ENTRANT"
        # appended, so ENTRANT was always last and always won — silently
        # deleting the model's own forecast for the named party whenever it
        # forecast one. Measured: with ActionSA declared in judgements/, the
        # model produced a median of 43 seats against an actual 44, and this
        # line scored it as 0 with a CRPS of 37.30. The repository's founding
        # story, that the model gave ActionSA nothing, was in part an artefact
        # of this line. ``backtest.relabel_entrant`` has always merged the ward
        # probabilities correctly; the two paths disagreed about the same
        # operation.
        merged = []
        for draw in draws:
            row: dict[str, float] = defaultdict(float)
            for key, value in draw.items():
                row[entrant_actual if key == "ENTRANT" else key] += value
            merged.append(dict(row))
        draws = merged
    if parties is not None:
        universe = list(parties)
    else:
        universe = sorted(set().union(*(set(d) for d in draws)) | set(actual)) \
            if draws else sorted(actual)
    # reshape: an empty ``draws`` gives np.array([]) shape (0,), and every rule
    # below indexes shape[1]
    samples = np.array([[float(d.get(p, 0)) for p in universe] for d in draws],
                       dtype=float).reshape(len(draws), len(universe))
    truth = np.array([float(actual.get(p, 0)) for p in universe], dtype=float)
    if keep_all:
        return universe, samples, truth
    # MATERIALITY, not mere presence. Keeping a column because *one* draw in
    # five hundred gave a party a seat sounds conservative — spurious mass is
    # penalised rather than filtered — and it is, for CRPS, which that column
    # barely moves. It is ruinous for coverage and PIT: truth 0 against a
    # forecast that is 0 in 498 of 500 draws is an interval [0, 0] containing
    # 0, a free hit at 50, 80 and 90 alike, and a PIT value drawn from very
    # nearly U(0,1), which flattens the histogram towards the shape it exists
    # to test for.
    #
    # Measured on this model at 2021: 37 of 55 kept columns were parties that
    # won nothing and were forecast nothing. Printed coverage read 73/89/93
    # against a real 17/67/78, and at 2016 the printed verdict was
    # "over-dispersed, the model is hedging" when the truth was the opposite.
    # The diagnosis was not optimistic; it was inverted, and every tuning
    # decision taken against it was taken against a broken instrument.
    #
    # So a column earns its place by mattering to one side or the other: the
    # party won a seat, or this forecaster gives it one often enough that the
    # claim is a real claim.
    keep = [i for i, _ in enumerate(universe)
            if truth[i] > 0 or (samples.shape[0] and samples[:, i].max() > 0)]
    return [universe[i] for i in keep], samples[:, keep], truth[keep]


def relevant_parties(forecasts: Sequence[Sequence[Mapping[str, int]]],
                     actual: Mapping[str, int],
                     entrant_actual: str | None = None) -> list[str]:
    """A candidate party universe covering several forecasters.

    A party is in if it won a seat, or if *any* forecaster gave it one in any
    draw. Pass it to :func:`seat_matrix` / :func:`score_seats` as ``parties`` to
    fix the column order across a comparison.

    It does **not** equalise the scored denominators, and must not be used to
    try: :func:`seat_matrix` keeps only the columns this forecaster or the truth
    made non-zero, precisely so that no forecaster's score can move when a
    different forecaster joins the run. See that function for what went wrong
    when this list *was* the scored set.
    """
    keep = {p for p, s in actual.items() if s > 0}
    for draws in forecasts:
        for draw in draws:
            for party, seats in draw.items():
                if seats > 0:
                    keep.add(entrant_actual if (entrant_actual and party == "ENTRANT")
                             else party)
    return sorted(keep)


# ---------------------------------------------------------------------------
# CRPS
# ---------------------------------------------------------------------------


def crps_sample(samples: np.ndarray, actual: float, fair: bool = True) -> float:
    """Continuous Ranked Probability Score of one marginal. **Lower is better.**

    ``CRPS = E|X - y| - ½ E|X - X'|``, estimated from the sample itself. It is
    the integral of the squared difference between the predicted CDF and the
    step function at the truth, so it rewards a forecast for being *close* and
    for being *sharp*, and it is measured in seats: a CRPS of 3.0 means the
    distribution is, in this integrated sense, three seats away. A point
    forecast has ``E|X - X'| = 0``, so its CRPS is exactly its absolute error --
    which makes CRPS directly comparable between a deterministic benchmark and
    a Monte Carlo, unlike any interval score.

    ``fair=True`` uses the unbiased ``1/(n(n-1))`` estimator of the spread term.
    The textbook ``1/n²`` version is biased downwards for small ensembles, which
    quietly rewards under-dispersion -- exactly the failure this module exists
    to detect -- so the unbiased form is the default.
    """
    x = np.sort(np.asarray(samples, dtype=float))
    n = x.size
    if n == 0:
        return float("nan")
    absolute = float(np.abs(x - actual).mean())
    if n == 1:
        return absolute
    # sum over all ordered pairs of |xi - xj| = 2 * sum_i (2i - n - 1) x_(i)
    i = np.arange(1, n + 1, dtype=float)
    gini = float(((2.0 * i - n - 1.0) * x).sum())
    spread = gini / (n * (n - 1)) if fair else gini / (n * n)
    return absolute - spread


def crps_by_party(samples: np.ndarray, actual: np.ndarray, parties: Sequence[str],
                  fair: bool = True) -> dict:
    """Per-party CRPS plus the mean and total. **Lower is better.**

    The total is the quantity to compare between models; the per-party column
    is where you find out *which* party the model cannot forecast.
    """
    per = {p: crps_sample(samples[:, j], actual[j], fair=fair)
           for j, p in enumerate(parties)}
    values = list(per.values())
    return {"per_party": per,
            "total": float(sum(values)),
            "mean": float(np.mean(values)) if values else float("nan")}


# ---------------------------------------------------------------------------
# PIT
# ---------------------------------------------------------------------------


def pit_values(samples: np.ndarray, actual: np.ndarray,
               seed: int | None = 20211101) -> np.ndarray:
    """Randomised probability integral transform, one value per party.

    Under a perfectly calibrated forecast, PIT values are uniform on [0,1].
    Seat counts are integers, so the plain PIT ``F(y)`` is lumpy even when the
    forecast is perfect; the randomised version draws uniformly across the jump,
    ``u = F(y⁻) + v·(F(y) - F(y⁻))``, which restores exact uniformity under
    calibration. Without this correction a discrete forecast looks
    mis-calibrated when it is not.

    Not itself a score -- read it through :func:`pit_histogram`, whose *shape*
    says what kind of wrong the model is.
    """
    samples = _as_matrix(samples)
    if samples.shape[0] == 0:
        return np.zeros(0, dtype=float)   # no draws: no transform to take
    rng = np.random.default_rng(seed)
    out = []
    for j in range(samples.shape[1]):
        column = samples[:, j]
        below = float((column < actual[j]).mean())
        at_or_below = float((column <= actual[j]).mean())
        out.append(below + rng.random() * (at_or_below - below))
    return np.array(out, dtype=float)


# χ²(0.95) critical values, dof 1..20 -- avoids a scipy dependency for the one
# number needed to say whether a histogram is further from flat than noise.
_CHI2_95 = {1: 3.84, 2: 5.99, 3: 7.81, 4: 9.49, 5: 11.07, 6: 12.59, 7: 14.07,
            8: 15.51, 9: 16.92, 10: 18.31, 11: 19.68, 12: 21.03, 13: 22.36,
            14: 23.68, 15: 25.00, 16: 26.30, 17: 27.59, 18: 28.87, 19: 30.14,
            20: 31.41}


def pit_histogram(pits: np.ndarray, bins: int = 10) -> dict:
    """Bin the PIT values and say what the shape means. **Flat is the target.**

    A single calibration number hides the two failure modes, which need
    opposite fixes:

    * **U-shaped** -- too much mass at 0 and 1: the truth keeps landing outside
      the distribution. Under-dispersed; widen it.
    * **Hump-shaped** -- mass piled in the middle: the truth keeps landing
      comfortably inside. Over-dispersed; the model is hedging.
    * **Sloped / mean far from 0.5** -- biased. The spread may be fine.

    Returns counts, frequencies, the χ² statistic against flat with its 5%
    critical value (with a caveat: with ten parties the test has almost no
    power, and it is the three-target pooled histogram that is worth reading),
    and a plain-English verdict.
    """
    pits = np.asarray(pits, dtype=float)
    counts, edges = np.histogram(pits, bins=bins, range=(0.0, 1.0))
    n = int(counts.sum())
    expected = n / bins if n else float("nan")
    chi2 = float(((counts - expected) ** 2 / expected).sum()) if n else float("nan")

    verdict = "too few values to read"
    if n >= bins:
        ends = (counts[0] + counts[-1]) / n          # expected 2/bins if flat
        ratio = ends / (2.0 / bins)
        mean = float(pits.mean())
        if ratio > 1.25:
            verdict = ("U-shaped: the truth lands outside the distribution too "
                       "often — under-dispersed, widen it")
        elif ratio < 0.6:
            verdict = ("hump-shaped: the truth lands mid-distribution too often "
                       "— over-dispersed, the model is hedging")
        else:
            verdict = "approximately flat"
        if abs(mean - 0.5) > 0.12:
            side = "under" if mean > 0.5 else "over"
            verdict += f"; mean PIT {mean:.2f} — the model {side}-predicts seats"
    return {"counts": counts.tolist(),
            "edges": edges.tolist(),
            "frequencies": (counts / n).tolist() if n else [],
            "n": n,
            "mean": float(pits.mean()) if n else float("nan"),
            "chi2": chi2,
            "chi2_dof": bins - 1,
            "chi2_crit_95": _CHI2_95.get(bins - 1),
            "verdict": verdict}


# ---------------------------------------------------------------------------
# coverage
# ---------------------------------------------------------------------------


def coverage(samples: np.ndarray, actual: np.ndarray,
             levels: Sequence[float] = (0.5, 0.8, 0.9)) -> list[dict]:
    """Empirical coverage of central intervals. **Match the nominal level** —
    provided the columns were chosen without looking at the outcome, which is
    what :func:`score_seats` is careful about.

    Not a proper score -- an interval can be right for the wrong reason, and a
    forecaster can game coverage by widening everything -- but it is the number
    a reader understands, and read at three levels at once it is much harder to
    fool than the single 90% band the harness reports today. A model at 90/80/70
    against nominal 90/80/50 is over-dispersed in the middle and fine in the
    tails; one number cannot show that.

    Seats are integers, so a perfectly calibrated forecast still over-covers a
    little -- the interval has to include the whole endpoint. Empirically that
    is worth a few points at the 50% level and almost nothing at 90%; read
    :func:`pit_histogram`, which corrects for discreteness, when the two
    disagree.
    """
    samples = _as_matrix(samples)
    if samples.shape[0] == 0:
        return [{"level": float(level), "inside": 0, "counted": 0,
                 "empirical": float("nan")} for level in levels]
    rows = []
    for level in levels:
        lo_q, hi_q = (1 - level) / 2, (1 + level) / 2
        inside = 0
        for j in range(samples.shape[1]):
            lo, hi = np.quantile(samples[:, j], [lo_q, hi_q])
            if lo <= actual[j] <= hi:
                inside += 1
        counted = samples.shape[1]
        rows.append({"level": float(level), "inside": inside, "counted": counted,
                     "empirical": inside / counted if counted else float("nan")})
    return rows


# ---------------------------------------------------------------------------
# ward winners: Brier and reliability
# ---------------------------------------------------------------------------


def ward_events(ward_probs: Mapping[str, Mapping[str, float]],
                actual_winners: Mapping[str, str]) -> tuple[np.ndarray, np.ndarray]:
    """Flatten ward forecasts to binary events: "party P wins ward W".

    One event per (ward, party) pair the model gave probability to, *plus* the
    actual winner even when the model gave it nothing -- otherwise a model that
    never imagined the winner would escape the penalty entirely, which is the
    single most important thing a ward score has to catch.

    Only wards present in ``actual_winners`` are scored.
    """
    p, y = [], []
    for ward, winner in actual_winners.items():
        probs = dict(ward_probs.get(ward, {}))
        probs.setdefault(winner, 0.0)
        for party, prob in probs.items():
            p.append(float(prob))
            y.append(1.0 if party == winner else 0.0)
    return np.array(p, dtype=float), np.array(y, dtype=float)


def brier_score(probs: np.ndarray, outcomes: np.ndarray) -> float:
    """Mean squared error of binary probability forecasts. **Lower is better.**

    Proper: minimised only by reporting the true probability. Range 0 to 1.
    Because most (ward, party) events are near-certain non-wins, the absolute
    value is small and only comparisons between forecasters mean anything --
    which is exactly what a benchmark is for. See :func:`brier_decomposition`
    for the part that is interpretable on its own.
    """
    if probs.size == 0:
        return float("nan")
    return float(np.mean((probs - outcomes) ** 2))


def brier_multicategory(ward_probs: Mapping[str, Mapping[str, float]],
                        actual_winners: Mapping[str, str]) -> float:
    """Per-ward multi-category Brier, summed over parties. **Lower is better.**

    Range 0 to 2, and the natural per-contest reading: 0 is a certain correct
    call, 1 is total ignorance spread over two parties, 2 is certainty in the
    wrong party. Reported alongside the binary version because the binary
    version's denominator depends on how many parties the model happened to
    mention, which makes it awkward to compare across models with different
    party universes.
    """
    total, n = 0.0, 0
    for ward, winner in actual_winners.items():
        probs = dict(ward_probs.get(ward, {}))
        probs.setdefault(winner, 0.0)
        total += sum((prob - (1.0 if party == winner else 0.0)) ** 2
                     for party, prob in probs.items())
        n += 1
    return total / n if n else float("nan")


def reliability_table(probs: np.ndarray, outcomes: np.ndarray,
                      edges: Sequence[float] | None = None) -> list[dict]:
    """Predicted-probability bucket vs observed frequency. **Diagonal is right.**

    This is the calibration test with real power: ~135 ward contests per target,
    ~405 across 2011/2016/2021. If the model's 70% wards are won 70% of the
    time, the probabilities mean what they say. If its 90% wards are won 99% of
    the time, it is systematically under-confident and its seat bands are too
    wide for the same reason.

    Bins are finer at the ends by default, because that is where forecasts are
    made and where over-confidence shows first.
    """
    if edges is None:
        edges = [0.0, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5,
                 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
    edges = list(edges)
    rows = []
    for k in range(len(edges) - 1):
        lo, hi = edges[k], edges[k + 1]
        last = k == len(edges) - 2
        mask = (probs >= lo) & ((probs <= hi) if last else (probs < hi))
        n = int(mask.sum())
        rows.append({
            "lo": lo, "hi": hi, "n": n,
            "mean_predicted": float(probs[mask].mean()) if n else float("nan"),
            "observed": float(outcomes[mask].mean()) if n else float("nan"),
            "events": int(outcomes[mask].sum()) if n else 0,
        })
    return rows


def brier_decomposition(probs: np.ndarray, outcomes: np.ndarray,
                        table: Sequence[Mapping] | None = None) -> dict:
    """Murphy decomposition ``BS = reliability - resolution + uncertainty``.

    * **reliability** (lower is better) -- how far the bins sit off the diagonal.
      This is the calibration term, and the only one a model can fix by being
      more honest rather than more knowledgeable.
    * **resolution** (higher is better) -- how far the model dares to move away
      from the base rate. A forecaster that predicts the base rate everywhere is
      perfectly reliable and useless; resolution is what separates it from a
      real model.
    * **uncertainty** -- a property of the events, identical for every
      forecaster on the same target, so it cancels in any comparison.
    """
    if probs.size == 0:
        return {k: float("nan") for k in
                ("reliability", "resolution", "uncertainty", "brier", "residual")}
    rows = table if table is not None else reliability_table(probs, outcomes)
    n = probs.size
    base = float(outcomes.mean())
    reliability = resolution = 0.0
    for row in rows:
        if not row["n"]:
            continue
        w = row["n"] / n
        reliability += w * (row["mean_predicted"] - row["observed"]) ** 2
        resolution += w * (row["observed"] - base) ** 2
    uncertainty = base * (1 - base)
    brier = brier_score(probs, outcomes)
    return {"reliability": reliability, "resolution": resolution,
            "uncertainty": uncertainty, "brier": brier,
            # non-zero only because bins are coarse: within-bin spread of p
            "residual": brier - (reliability - resolution + uncertainty)}


def score_wards(ward_probs: Mapping[str, Mapping[str, float]],
                actual_winners: Mapping[str, str],
                edges: Sequence[float] | None = None) -> dict:
    """Everything ward-shaped in one call: Brier, reliability table, hit rate."""
    probs, outcomes = ward_events(ward_probs, actual_winners)
    table = reliability_table(probs, outcomes, edges)
    called = sum(1 for ward, winner in actual_winners.items()
                 if ward_probs.get(ward) and
                 max(ward_probs[ward], key=ward_probs[ward].get) == winner)
    return {"n_wards": len(actual_winners),
            "n_events": int(probs.size),
            "brier_binary": brier_score(probs, outcomes),
            "brier_multicategory": brier_multicategory(ward_probs, actual_winners),
            "decomposition": brier_decomposition(probs, outcomes, table),
            "reliability": table,
            "modal_calls_correct": called,
            "modal_hit_rate": called / len(actual_winners) if actual_winners else
            float("nan")}


# ---------------------------------------------------------------------------
# multivariate
# ---------------------------------------------------------------------------


def _mean_pairwise_norm(x: np.ndarray, beta: float, fair: bool,
                        chunk: int = 256) -> float:
    """E‖X - X'‖^β over the sample, computed in row chunks to bound memory."""
    n = x.shape[0]
    if n < 2:
        return 0.0
    total = 0.0
    for start in range(0, n, chunk):
        block = x[start:start + chunk]
        d = np.linalg.norm(block[:, None, :] - x[None, :, :], axis=2)
        total += float((d ** beta).sum())
    return total / (n * (n - 1)) if fair else total / (n * n)


def energy_score(samples: np.ndarray, actual: np.ndarray, beta: float = 1.0,
                 fair: bool = True, max_draws: int = 4000,
                 seed: int | None = 20211101) -> float:
    """Energy score of the *joint* seat vector. **Lower is better.**

    ``ES = E‖X - y‖^β - ½ E‖X - X'‖^β``, the multivariate generalisation of
    CRPS (β=1, Euclidean norm over parties), and strictly proper for the joint
    distribution. It exists here because per-party CRPS cannot see the thing
    that decides a council: seats are zero-sum, so errors are correlated by
    construction, and a model can have excellent marginals while never
    generating a coherent council. Two forecasts with identical marginals — one
    where ANC-up implies DA-down, one where they float independently — get the
    same CRPS and different energy scores.

    In seats, like CRPS. Sub-sampled above ``max_draws`` because the spread term
    is O(n²); with 2000 draws the estimate is far more precise than the three
    targets available to evaluate it on.
    """
    x = np.asarray(samples, dtype=float)
    y = np.asarray(actual, dtype=float)
    if x.shape[0] > max_draws:
        rng = np.random.default_rng(seed)
        x = x[rng.choice(x.shape[0], max_draws, replace=False)]
    if x.size == 0:
        return float("nan")
    first = float((np.linalg.norm(x - y[None, :], axis=1) ** beta).mean())
    return first - 0.5 * _mean_pairwise_norm(x, beta, fair)


def variogram_score(samples: np.ndarray, actual: np.ndarray, order: float = 0.5,
                    weights: np.ndarray | None = None) -> float:
    """Variogram score of order p on the joint seat vector. **Lower is better.**

    Compares ``E|X_i - X_j|^p`` against ``|y_i - y_j|^p`` for every pair of
    parties. Proper, and far more sensitive to the *dependence* structure than
    the energy score, which is dominated by the marginals in practice. Included
    because the specific question this model has never answered is whether its
    parties move together the way real parties do; this is the number that
    answers it. Insensitive to a shared bias, so read it next to CRPS, never
    instead of it.
    """
    x = _as_matrix(samples)
    y = np.asarray(actual, dtype=float)
    d = x.shape[1]
    if d < 2 or x.shape[0] == 0:
        return float("nan")
    expected = np.abs(x[:, :, None] - x[:, None, :]) ** order
    expected = expected.mean(axis=0)
    truth = np.abs(y[:, None] - y[None, :]) ** order
    w = np.ones((d, d)) if weights is None else np.asarray(weights, dtype=float)
    iu = np.triu_indices(d, 1)
    # MEAN over pairs, not a sum. A sum scales as d(d-1)/2, so a forecaster
    # scored over 55 columns and one scored over 19 are not comparable: 2226
    # against 690 was a dimension artefact, not a difference in skill. Scheuerer
    # and Hamill specify weights precisely because an unweighted sum is not
    # meaningful across different d.
    npairs = len(iu[0])
    if not npairs:
        return 0.0
    return float((w[iu] * (truth[iu] - expected[iu]) ** 2).sum() / npairs)


# ---------------------------------------------------------------------------
# one call for a whole forecast
# ---------------------------------------------------------------------------


def score_seats(draws: Sequence[Mapping[str, int]], actual: Mapping[str, int],
                entrant_actual: str | None = None,
                levels: Sequence[float] = (0.5, 0.8, 0.9),
                bins: int = 10, seed: int | None = 20211101,
                parties: Sequence[str] | None = None) -> dict:
    """Score a seat forecast end to end. Returns a dict; see :func:`format_report`.

    ``parties`` is an optional candidate universe (see :func:`seat_matrix`); it
    fixes the column order and cannot change any number, because the scored
    columns are always this forecaster's own non-zero ones plus the ones the
    result made non-zero. Nothing here depends on what else is in the run.

    Coverage and PIT are reported twice: the headline pair over the seats this
    forecaster CLAIMS (a seat in at least ``CLAIM_FRACTION`` of its draws), and
    ``coverage_all`` / ``pit_all`` over every scored column. The first is the
    calibration test; the second is kept so the difference is visible.
    """
    parties, samples, truth = seat_matrix(draws, actual, entrant_actual,
                                          parties=parties)
    # with no draws every per-party column is undefined rather than zero, and
    # saying so beats returning a short array the callers below would index off
    # the end of
    empty = np.full(samples.shape[1], float("nan"))
    pits = pit_values(samples, truth, seed=seed) if samples.shape[0] else empty
    median = np.median(samples, axis=0) if samples.shape[0] else empty

    # WHICH COLUMNS TEST CALIBRATION, and the answer must not depend on the
    # answer. Two wrong rules have shipped here; this is the third.
    #
    # Scoring every column is wrong because a party that won nothing, forecast
    # near nothing, is an interval [0, 0] containing 0 — a free hit at every
    # level and a near-uniform PIT. 36 of 54 columns at 2021 were exactly that.
    #
    # Selecting on the OUTCOME (truth > 0) is also wrong, and worse, because it
    # is not a neutral restriction: zero is the minimum of the support, so
    # PIT|y=0 lies in [0, F(0)] — the smallest values there are. Dropping those
    # events truncates the low tail, and under perfect calibration the survivors
    # are U(p0, 1), not uniform. Simulated at this model's own p0 vector, 93% of
    # PERFECTLY CALIBRATED replicates print "U-shaped, under-dispersed, widen
    # it", and the 2016 "mean PIT 0.73, under-predicts" reproduces its null of
    # 0.721 to three decimals. It is an instrument that manufactures its own
    # conclusion.
    #
    # Selecting on the FORECAST is neutral: the criterion depends on F alone, so
    # PIT uniformity survives it. A calibrated forecaster simulated under this
    # rule returns mean PIT 0.503. The question it asks is the right one — "of
    # the seats this forecaster claims, how well calibrated is it?" — and a
    # forecaster is answerable for its own claims whatever the outcome.
    claimed = ((samples > 0).mean(axis=0) >= CLAIM_FRACTION
               if samples.shape[0] else np.zeros(samples.shape[1], dtype=bool))
    s_won = samples[:, claimed] if samples.shape[0] else samples
    t_won = truth[claimed]
    pits_won = pits[claimed] if samples.shape[0] else empty[claimed]

    return {
        "parties": parties,
        "n_draws": int(samples.shape[0]),
        "actual": {p: int(truth[j]) for j, p in enumerate(parties)},
        "median": {p: float(median[j]) for j, p in enumerate(parties)},
        "crps": crps_by_party(samples, truth, parties),
        # headline: parties that won a seat
        "pit": pit_histogram(pits_won, bins=bins),
        "coverage": coverage(s_won, t_won, levels),
        "n_scored_calibration": int(claimed.sum()),
        # the full-column figures, kept and labelled so the difference is
        # visible rather than a matter of trust
        "pit_all": pit_histogram(pits, bins=bins),
        "coverage_all": coverage(samples, truth, levels),
        "n_scored_all": int(samples.shape[1]),
        "pit_values": {p: float(pits[j]) for j, p in enumerate(parties)},
        "energy": energy_score(samples, truth, seed=seed),
        "variogram": variogram_score(samples, truth),
        # kept so the new numbers can be read against the harness's old ones
        "seat_mae_median": float(np.abs(median - truth).sum()),
    }


def format_report(seats: Mapping | None = None, wards: Mapping | None = None,
                  label: str = "", top: int = 12) -> str:
    """Human-readable block for a :func:`score_seats` / :func:`score_wards` pair."""
    out: list[str] = []
    if label:
        out.append(f"=== {label} ===")
    if seats:
        parties = seats["parties"]
        crps = seats["crps"]["per_party"]
        order = sorted(parties, key=lambda p: -seats["actual"][p])[:top]
        out.append(f"  {'party':12s}{'actual':>8s}{'median':>8s}{'CRPS':>8s}{'PIT':>7s}")
        for p in order:
            out.append(f"  {p[:12]:12s}{seats['actual'][p]:>8d}"
                       f"{seats['median'][p]:>8.0f}{crps[p]:>8.2f}"
                       f"{seats['pit_values'][p]:>7.2f}")
        out.append(f"  CRPS total {seats['crps']['total']:.2f} seats "
                   f"(mean {seats['crps']['mean']:.2f} over "
                   f"{len(parties)} parties)   [lower better]")
        out.append(f"  energy score {seats['energy']:.2f}   "
                   f"variogram(0.5) {seats['variogram']:.2f}   [lower better]")
        cov = "  ".join(f"{r['level']:.0%}: {r['inside']}/{r['counted']}"
                        f" = {r['empirical']:.0%}" for r in seats["coverage"])
        out.append(f"  coverage   {cov}   [on the {seats.get('n_scored_calibration', '?')} "
                   f"seats this forecaster CLAIMS — should match the nominal level]")
        if "coverage_all" in seats:
            cov_all = "  ".join(f"{r['level']:.0%}: {r['inside']}/{r['counted']}"
                                f" = {r['empirical']:.0%}" for r in seats["coverage_all"])
            out.append(f"  (all {seats.get('n_scored_all','?')} scored columns: "
                       f"{cov_all} — inflated by parties nobody claimed)")
        out.append(f"  PIT {seats['pit']['counts']}  χ²={seats['pit']['chi2']:.1f} "
                   f"(5% crit {seats['pit']['chi2_crit_95']})")
        out.append(f"      {seats['pit']['verdict']}")
        out.append(f"  (old harness metric: median seat MAE "
                   f"{seats['seat_mae_median']:.0f})")
    if wards:
        d = wards["decomposition"]
        out.append(f"  wards {wards['n_wards']}  events {wards['n_events']}   "
                   f"Brier {wards['brier_binary']:.4f} "
                   f"(multi-cat {wards['brier_multicategory']:.3f})   [lower better]")
        out.append(f"    reliability {d['reliability']:.4f} [lower better]   "
                   f"resolution {d['resolution']:.4f} [higher better]   "
                   f"uncertainty {d['uncertainty']:.4f}")
        out.append(f"    modal call correct in {wards['modal_calls_correct']}/"
                   f"{wards['n_wards']} wards")
        out.append(f"    {'predicted':>14s}{'n':>7s}{'events':>8s}"
                   f"{'mean p':>9s}{'observed':>10s}")
        for row in wards["reliability"]:
            if not row["n"]:
                continue
            out.append(f"    {row['lo']:.2f}-{row['hi']:.2f}    {row['n']:>7d}"
                       f"{row['events']:>8d}{row['mean_predicted']:>9.3f}"
                       f"{row['observed']:>10.3f}")
    return "\n".join(out)
