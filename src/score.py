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

import hashlib

import numpy as np

# Calibration is scored on the seats a forecaster actually CLAIMS: columns
# where it gives a seat in at least this fraction of its draws.
#
# ⛔ **THE THEOREM IS TRUE AND IT DOES NOT LICENCE LEADING WITH THIS
# POPULATION.** Selecting on the forecast leaves PIT uniform *under
# calibration* — that is a statement about the NULL, and it is the only thing
# the argument buys. It says nothing about what the statistic estimates when
# the null is false, and here the selection rule is very nearly the complement
# of this model's dominant failure mode: the failure is giving a real party
# essentially zero, and the rule admits a column only when the model gives it a
# seat in half its draws.
#
# Measured on the committed 24-city-year artefact, against the fixed
# ``reference`` population (input-selected — see
# ``compare_history.reference_universe``):
#
#     columns carrying a z          413 fixed / 153 kept by `claimed`
#     the ten worst |z| columns     `claimed` keeps 2 of 10
#     sd(z)                         1.062 fixed, 0.784 kept, 1.194 dropped
#     mean z                        +0.105 fixed, +0.014 kept, +0.158 dropped
#
# So on this model `claimed` reports a width fault ~26% smaller and a level
# bias near zero where the fixed population reads +0.105, and the columns it
# drops are the ones the model got most wrong — Cape Town 2021
# CAPE_COLOURED_CONGRESS (z=+11.19, p_any 0.11), Johannesburg 2021 PA (z=+8.24,
# p_any 0.28), Nelson Mandela Bay 2021 NORTHERN_ALLIANCE (z=+5.06, p_any 0.10).
#
# `claimed` is therefore a CONDITIONAL diagnostic — "of the seats this
# forecaster claims, is it calibrated?" — and it is a fair question a forecaster
# is answerable for. It is not the headline, and there is no neutral undiluted
# third population to go looking for: the fixed one is diluted by columns that
# are zero on both sides, and that is the price of being fixed. **Report both,
# permanently, each labelled with what selects it.**
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
# holding the universe, so a model-vs-baseline difference is one comparison
# ---------------------------------------------------------------------------


def hold_universe(forecasts: Sequence[Sequence[Mapping[str, int]]],
                  actual: Mapping[str, int],
                  entrant_actual: str | None = None,
                  fixed: Sequence[str] = ()) -> list[str]:
    """The column set several forecasters are to be COMPARED on.

    ``fixed`` is an input-selected population — in this repository,
    ``compare_history.reference_universe``, a party's previous-election share
    plus its nomination slate, neither of which can move when a lever moves.
    The union with :func:`relevant_parties` adds every party that actually won
    a seat and every column any forecaster in the comparison claims.

    **Why the union, and not ``fixed`` alone.** ``fixed`` was the obvious
    candidate and it is not sufficient, for two measured reasons.

    *It does not contain every seat-winner.* Across the committed 24 city-years
    **seven parties won seats while sitting outside ``reference``** — ALJAMAAH
    at Johannesburg 2011, PA at Johannesburg 2016 and Ekurhuleni 2016, IFP at
    Tshwane 2021, MINORITIES_OF_SOUTH_AFRICA at eThekwini 2016,
    AGENCY_FOR_NEW_AGENDA at Mangaung 2016, AIC at Buffalo City 2011. Scoring on
    ``fixed`` alone deletes a column where a party really won, for BOTH sides at
    once, so whichever forecaster was worse on it is forgiven. These are exactly
    the small-party misses this model's failure mode produces.

    *It excuses spurious mass.* ``fixed`` holds no column for a party that was
    never plausibly on the ballot, and this model puts seats on 25 such columns
    at Johannesburg 2021 alone. Dropping them stops the score seeing phantom
    mass, which is the property :func:`seat_matrix` exists to protect.

    **The union is a superset of every forecaster's own scored set, and that is
    what makes it free.** A column outside a forecaster's own set is, by the
    admission rule in :func:`seat_matrix`, zero in the truth and zero in every
    one of its draws — and a both-zero column contributes **exactly nothing** to
    CRPS (``E|X-y| = 0`` and the spread term is 0) and nothing to the energy
    score (an extra zero coordinate leaves every Euclidean norm unchanged).
    Measured, padding a real 8-column forecast out to 58 columns: CRPS total
    12.773299 and energy 6.158879 at m=0, 5, 20 and 50 padding columns alike.

    So holding the universe this way moves **no CRPS and no energy number**,
    for the model or for a baseline, and the difference between them becomes a
    difference over one column set rather than two. It is what makes the number
    quotable; it is not a correction of an inflation, and must not be sold as
    one.

    ⚠️ **The variogram is the exception and it really does move.**
    :func:`variogram_score` is a MEAN over ``d(d-1)/2`` pairs, so a both-zero
    column adds ``d`` non-zero cross terms and ``m(m-1)/2`` zero ones, and

        V(m) = (S + m·C) / [(d+m)(d+m-1)/2],  C = Σ_j (|y_j|^p - E|X_j|^p)²

    with ``S`` the original ``d(d-1)/2`` pairs' contribution. Verified to six
    figures against the real thing: on the fixture in ``test_scored_universe``
    the closed form and ``variogram_score`` agree to 3e-17 over m = 0..19.
    **V(m+1) > V(m) exactly while**

        m < d - 1 - 2S/C

    and falls after it. Both signs are reachable and which one applies depends
    on ``S`` and ``C``, neither of which survives into ``history.json``. **Do
    not predict the direction of a variogram change from the column counts.**

    ⛔ **THIS LINE USED TO READ ``m < 2C/V - 2d + 1``, WHICH IS OUT BY A FACTOR
    OF TWO.** Differentiating ``V`` in ``u = d + m`` gives ``C·u(u-1) >
    V·u(u-1)(2u-1)/2``, hence ``u < C/V + ½`` and ``m < C/V - d + ½`` — the old
    line doubled that. (The continuous form names ``V`` on both sides and can
    only be read as a fixed point, which is why the discrete condition above is
    the one stated; they agree.) Measured on the same fixture, d=8, S=4.3507,
    C=1.9415: the variogram peaks at **m = 3**, the corrected condition returns
    2.52 so the last rising step is 2→3, and the old one returns 5.99. The
    conclusion this was quoted for is unaffected — both signs really are
    reachable, and the test below pins both limbs — but the stated reason for it
    was wrong.

    What holding the universe buys on the variogram, then, is not invariance but
    that the two forecasters are at least at the same ``d``: today the
    model is scored over 580 columns across the panel and uniform-swing over
    332, and a mean over pairs is not comparable across that.

    ⚠️ The returned set depends on WHICH forecasters are in the comparison —
    that is the price of keeping spurious mass scored. It is harmless for CRPS
    and energy (invariant, as above) and not harmless for the variogram, so a
    variogram computed on a held universe is quotable as a difference WITHIN one
    run and never as an absolute. Pass ``forecasts=[]`` to get ``fixed`` plus
    the seat-winners and nothing else, if a roster-independent set is wanted
    instead and the phantom-mass cost is accepted deliberately.
    """
    held = set(relevant_parties(forecasts, actual, entrant_actual))
    held.update(fixed)
    return sorted(held)


def universe_key(columns: Sequence[str] | Mapping) -> str:
    """A stable fingerprint of a scored column SET, order-insensitive.

    Takes a list of party names or a :func:`score_seats` result. Order is
    deliberately not part of the key: no score here depends on column order
    (each PIT column is keyed by its own party name, and CRPS, energy and the
    variogram are all symmetric), so two runs that differ only in order ARE
    comparable and a key that said otherwise would cry wolf.

    ``hashlib`` rather than ``hash()`` for the reason :func:`_column_entropy`
    gives: Python randomises string hashing per process, so a ``hash()``-derived
    key would differ between the run that produced a score and the run that
    checked it.
    """
    if isinstance(columns, Mapping):
        columns = columns.get("parties") or []
    digest = hashlib.blake2b(
        "\n".join(sorted(str(c) for c in columns)).encode("utf-8"),
        digest_size=8)
    return digest.hexdigest()


def comparable(scored: Mapping[str, Mapping]) -> dict:
    """Were these forecasters scored on the same columns? **The #13 predicate.**

    ``scored`` maps a forecaster name to its :func:`score_seats` result. Returns
    ``{"comparable", "key", "n", "columns", "by_forecaster", "mismatch"}``;
    ``mismatch`` is empty exactly when every forecaster carries the same column
    set, and otherwise names, per forecaster, the columns only it has
    (``only_here``) and the columns it lacks (``missing``).

    **This is a predicate on the SETS, not on the scores**, and it is strict on
    purpose even though :func:`hold_universe` records that CRPS and energy are
    invariant to the columns that differ under the default admission rule. That
    invariance is a property of *that* rule; a held universe that dropped a
    forecaster's claims, or two runs scored against different reference
    universes, break it, and a predicate that tried to be clever about which
    differences are harmless would be a second place where the admission rule is
    encoded.

    Read it as: *may I quote a difference between these summed scores?* A
    ``False`` here is what the warning in ``compare_history`` describes —
    ``n_scored`` 55 for the model against 18-19 for the baselines at 2021 — and
    the fix is to score both with ``universe=hold_universe(...)``.
    """
    by_forecaster = {name: sorted(result.get("parties") or [])
                     for name, result in scored.items()}
    sets = {name: set(cols) for name, cols in by_forecaster.items()}
    union: set[str] = set().union(*sets.values()) if sets else set()
    mismatch = {}
    for name, cols in sets.items():
        only = sorted(cols - set().union(*(s for n, s in sets.items()
                                           if n != name)) ) if len(sets) > 1 else []
        missing = sorted(union - cols)
        if only or missing:
            mismatch[name] = {"only_here": only, "missing": missing}
    keys = {name: universe_key(cols) for name, cols in by_forecaster.items()}
    same = len(set(keys.values())) <= 1
    return {"comparable": bool(same and not mismatch),
            "key": next(iter(keys.values())) if same and keys else None,
            "n": len(union),
            "columns": sorted(union),
            "by_forecaster": {name: len(cols)
                              for name, cols in by_forecaster.items()},
            "mismatch": mismatch}


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


def _column_entropy(party: str) -> int:
    """A stable 64-bit integer from a party name.

    ⛔ **NOT** ``hash()``. Python randomises string hashing per process. This
    repository pins it with ``montecarlo.fix_hash_seed()``, but that runs only
    from an ``if __name__ == "__main__"`` guard — so any IMPORTING caller (a
    test module, an analysis harness, ``build_site``) is unpinned, and the same
    forecast would get a different PIT depending on how the code was entered.
    That is the §1.145 failure exactly, and it is the one this function must not
    reproduce.

    blake2b rather than ``zlib.crc32`` (the precedent ``_pit_seed`` sets):
    CRC32 is a 32-bit linear checksum, so a 200-name panel carries a ~5e-6
    birthday-collision chance against blake2b-64's ~1e-15. Measured on the real
    panel there are 151 distinct party names and **zero** collisions under
    either, so this is cheap insurance rather than a fix — but two parties
    sharing a uniform would be invisible and permanent.
    """
    return int.from_bytes(
        hashlib.blake2b(party.encode("utf-8"), digest_size=8).digest(), "big")


def column_rng(seed: int | None, party: str) -> np.random.Generator:
    """THE PIT column key. One definition, because two would drift.

    ⛔ It was written twice — here and in ``compare_history.redraw_pits`` — and
    the golden test asserted ``_column_entropy`` rather than either call site,
    so **reverting both to ``hash()`` left every test green**: a duplicated
    number and an un-fireable guard in the same three lines, inside the key
    built to stop exactly that (§1.145). Found in review 2026-08-31.
    """
    return np.random.default_rng([int(seed or 0), _column_entropy(party)])


def pit_intervals(samples: np.ndarray,
                  actual: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The jump each randomised PIT lands inside: ``(F(y⁻), F(y) − F(y⁻))``.

    **This is the entire information content of a randomised PIT, and it carries
    no randomness.** ``below + u·width`` is the PIT; ``below + width/2`` is its
    exact expectation over the randomisation; the exact probability of landing
    in any bin is that bin's overlap with ``[below, below + width]`` divided by
    ``width``. Store these two numbers and every PIT statistic is recoverable at
    any number of randomisations, for ever, without re-running the model.

    Which is why they are now written into the artefact: the seed band below was
    only measurable at all because the jumps happened to be recoverable from a
    lattice (both are multiples of 1/draws). That was luck, and it will not
    survive a change of draw count.
    """
    samples = _as_matrix(samples)
    if samples.shape[0] == 0:
        return np.zeros(0, dtype=float), np.zeros(0, dtype=float)
    below = np.array([float((samples[:, j] < actual[j]).mean())
                      for j in range(samples.shape[1])], dtype=float)
    at_or = np.array([float((samples[:, j] <= actual[j]).mean())
                      for j in range(samples.shape[1])], dtype=float)
    return below, at_or - below


def pit_values(samples: np.ndarray, actual: np.ndarray,
               parties: Sequence[str], seed: int | None = 20211101,
               replicates: int = 1) -> np.ndarray:
    """Randomised probability integral transform, one value per party.

    Under a perfectly calibrated forecast, PIT values are uniform on [0,1].
    Seat counts are integers, so the plain PIT ``F(y)`` is lumpy even when the
    forecast is perfect; the randomised version draws uniformly across the jump,
    ``u = F(y⁻) + v·(F(y) - F(y⁻))``, which restores exact uniformity under
    calibration. Without this correction a discrete forecast looks
    mis-calibrated when it is not.

    ⛔ **EACH COLUMN'S GENERATOR IS DERIVED FROM ``(seed, party name)``, AND THE
    REASON IS THAT THE OLD ONE MADE THE FLOOR MOVE ON ITS OWN.**

    Until 2026-08-31 this drew from a SINGLE stream, one value per column, in
    column order — so the j-th column got the j-th draw and nothing else
    determined it. Adding, removing or reordering a column re-rolled the
    randomisation of every column after it, and a change to the model was then
    indistinguishable from a re-roll. Measured on the committed panel: the seed
    alone moved the pooled mean PIT with sd **0.00955** on ``reference`` and
    **0.00528** on ``claimed`` (not 0.0013 — on ``claimed`` the randomisation
    lives in the small-party JUMP MASSES, not the truth-zero columns, which is
    the opposite of where it was looked for). On the statistic ``ITERATING.md``
    quotes as Key 2's width floor — ``reference``/2021 probit-SD, n=235, reading
    exactly 1.2000 — the re-roll sd is **0.0327**, which makes the 1.2000 →
    1.3557 finding built on it just **3.4 sd of a paired re-roll**.

    **Key 2 is an untradeable floor. A floor that moves 0.03 while the model
    stands still is not a floor.**

    So a column's PIT now depends on exactly: the seed, its own party name, its
    own draws and its own outcome — and on NOTHING about which other columns are
    scored or in what order. Adding, removing or reordering a column leaves
    every other column bit-identical (measured: max |Δ| = 0.0, exactly).

    ``replicates`` returns shape ``(replicates, n_cols)`` above 1, for callers
    that average a STATISTIC over randomisations; the first row is always
    bit-identical to the ``replicates=1`` value. ⛔ **Average the statistic,
    never the PIT values** — averaging the values first shrinks each draw toward
    the jump midpoint and would have read this model's width as 1.01 ("correct")
    where it is 1.20 ("too narrow"). See :func:`pit_intervals`.

    Not itself a score -- read it through :func:`pit_histogram`, whose *shape*
    says what kind of wrong the model is.
    """
    samples = _as_matrix(samples)
    if samples.shape[0] == 0:
        return np.zeros(0, dtype=float)
    if len(parties) != samples.shape[1]:
        raise ValueError(
            f"pit_values got {len(parties)} party names for "
            f"{samples.shape[1]} columns. The name IS the key now, so a "
            f"mismatch silently mis-keys every column after the first gap.")
    if len(set(parties)) != len(parties):
        dupes = sorted({p for p in parties if list(parties).count(p) > 1})
        raise ValueError(
            f"pit_values got duplicate party names {dupes}. Two columns would "
            f"share one uniform, which is invisible and permanent.")

    below, width = pit_intervals(samples, actual)
    reps = max(1, int(replicates))
    out = np.empty((reps, len(below)), dtype=float)
    for j, party in enumerate(parties):
        rng = column_rng(seed, party)
        out[:, j] = below[j] + rng.random(reps) * width[j]
    # ⛔ A PIT OUTSIDE [0,1] IS NOT A PIT, AND NOTHING ELSE WOULD HAVE SAID SO.
    # `pit_intervals` had no test: returning `at_or` instead of `at_or - below`
    # emits values up to 1.37 and every calibration statistic downstream keeps
    # computing. Measured in review 2026-08-31. This is the cheapest possible
    # guard on the quantity Key 2 is quoted against.
    if out.size and (out.min() < -1e-9 or out.max() > 1 + 1e-9):
        bad = int(np.argmax((out < -1e-9) | (out > 1 + 1e-9)) % out.shape[1])
        raise ValueError(
            f"PIT outside [0,1]: {out.min():.4f}..{out.max():.4f}, first at "
            f"column {parties[bad]!r}. `pit_intervals` must return the JUMP "
            f"F(y)-F(y-), not F(y).")
    return out[0] if replicates <= 1 else out


# χ²(0.95) critical values, dof 1..20 -- avoids a scipy dependency for the one
# number needed to say whether a histogram is further from flat than noise.
_CHI2_95 = {1: 3.84, 2: 5.99, 3: 7.81, 4: 9.49, 5: 11.07, 6: 12.59, 7: 14.07,
            8: 15.51, 9: 16.92, 10: 18.31, 11: 19.68, 12: 21.03, 13: 22.36,
            14: 23.68, 15: 25.00, 16: 26.30, 17: 27.59, 18: 28.87, 19: 30.14,
            20: 31.41}


def chi2_crit_95(dof: float) -> float | None:
    """χ²(0.95) at a possibly FRACTIONAL ``dof``. One table, extended.

    The Satterthwaite form in :func:`chi2_clustered` divides the degrees of
    freedom by ``1 + cv²``, so its reference distribution stops having a whole
    number of them and the integer table above stops being enough. This
    interpolates that table rather than introducing a closed-form approximation
    beside it, because a second way of producing one critical value is how two
    definitions of one number start (:func:`column_rng` is this repository's
    worked example of what that costs).

    Linear in ``dof`` between the tabulated points. χ²(0.95) is very nearly
    linear there — the table's second differences run about −0.04 — so the error
    is bounded and small. Measured against an exact inverse of the regularised
    incomplete gamma over dof 1.00 to 20.00 in steps of 0.01: worst absolute
    error **0.066, at dof 1.45**, and under **0.01 for every dof ≥ 5**, which is
    the whole range this module reaches (``dof = 9/(1+cv²)``, and ``cv²`` would
    have to exceed 0.8 to leave it). ``None`` outside the table: an extrapolated
    critical value is a fabrication, and returning one would be worse than
    returning nothing.
    """
    if dof is None or not (1.0 <= float(dof) <= 20.0):
        return None
    dof = float(dof)
    lo = int(dof)
    if lo == dof:
        return _CHI2_95[lo]
    return _CHI2_95[lo] + (dof - lo) * (_CHI2_95[lo + 1] - _CHI2_95[lo])


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
            # ⛔ `chi2` ABOVE IS THE NOMINAL TEST AND IT ASSUMES INDEPENDENT
            # COLUMNS, WHICH THEY ARE NOT. Columns inside one city-year share a
            # turnout draw, a pool structure and a national swing, so this
            # critical value is not the design's. :func:`chi2_clustered` is the
            # test to quote; this pair is the familiar number kept beside it.
            # It is also ONE randomisation — on the committed panel a re-roll
            # moves it from 19.3 to 66.2 on `reference`.
            "chi2_crit_95": _CHI2_95.get(bins - 1),
            "verdict": verdict}


def cluster_bootstrap(groups: Sequence[Sequence[float]],
                      statistic=None, level: float = 0.95,
                      draws: int = 20_000, seed: int = 20260817) -> dict:
    """Percentile interval for a pooled statistic, resampling CLUSTERS.

    ``groups`` is one array per cluster — here, per city-year. Clusters are
    drawn ``k`` at a time with replacement from the ``k`` observed ones, which
    is the only resampling that respects the dependence: columns inside a
    city-year share a turnout draw, a pool structure and a national swing, and
    a column bootstrap would return an interval far too tight.

    ``statistic`` takes the resampled list of cluster arrays and returns a
    float. ``None`` means the pooled mean, and that path is computed from
    per-cluster sums and sizes rather than by concatenating — the same number,
    two array reductions instead of ``draws`` Python-level concatenations.

    ⛔ **THIS IS THE ONLY CLUSTER BOOTSTRAP ``compare_history`` HAS**, since
    2026-09-13. It held a private copy, ``_cluster_bootstrap_ci`` — this
    function pinned to the pooled mean — which drew the same cluster indices
    from the same ``seed`` and ``draws`` and returned the same interval to the
    last bit. The two were checked bit-for-bit (same float, same hex, same
    degenerate ``nan``) and the whole ``pooled_calibration`` output diffed
    across ~60 intervals before the copy was deleted; no number moved. Both of
    its call sites now come here. ``compare_history`` cannot be imported back
    from this module (the arrow runs one way, it imports ``score``), which is
    why the general version lives here and not there.

    ⚠️ **One duplicate is left and it is NOT this one.**
    ``theta_residual.cluster_bootstrap`` is the same scheme specialised to
    ``sd(residual)`` and should become a call to this function when that file
    is next opened. ``test_scored_universe`` asserts the set of modules
    defining a resampler by NAME, so a fourth turns red and so does a rename.

    ⚠️ Nothing independent now recomputes this interval, which is the price of
    the consolidation. ``test_scored_universe`` pins the value in hex on a fixed
    fixture in its place.

    ⚠️ **A percentile interval on an observed statistic is not a test.** It is
    centred on what was seen, not on the null, so "the interval excludes the
    critical value" is evidence and not a p-value. The test is
    :func:`chi2_clustered`'s Rao-Scott correction.

    Returns ``{"lo", "hi", "point", "level", "draws", "clusters", "n",
    "replicates"}``; ``lo``/``hi``/``point`` are ``nan`` with fewer than two
    non-empty clusters, because one cluster carries no between-cluster
    information and an interval drawn from it would be a fabrication.
    """
    kept = [np.asarray(g, dtype=float) for g in groups if len(g)]
    k = len(kept)
    n = int(sum(g.size for g in kept))
    empty = {"lo": float("nan"), "hi": float("nan"), "point": float("nan"),
             "level": float(level), "draws": int(draws), "clusters": k,
             "n": n, "replicates": np.zeros(0, dtype=float)}
    if k < 2:
        return empty
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, k, size=(draws, k))
    if statistic is None:
        sums = np.array([g.sum() for g in kept], dtype=float)
        sizes = np.array([g.size for g in kept], dtype=float)
        values = sums[pick].sum(axis=1) / sizes[pick].sum(axis=1)
        point = float(sums.sum() / sizes.sum())
    else:
        values = np.array([statistic([kept[i] for i in row]) for row in pick],
                          dtype=float)
        point = float(statistic(kept))
    lo, hi = np.percentile(values, [100 * (1 - level) / 2,
                                    100 * (1 + level) / 2])
    return {"lo": float(lo), "hi": float(hi), "point": point,
            "level": float(level), "draws": int(draws), "clusters": k,
            "n": n, "replicates": values}


def _chi2_flat(values: np.ndarray, bins: int) -> float:
    """Pearson χ² of ``values`` against a flat histogram on [0, 1]."""
    counts, _ = np.histogram(np.asarray(values, dtype=float), bins=bins,
                             range=(0.0, 1.0))
    n = int(counts.sum())
    if not n:
        return float("nan")
    expected = n / bins
    return float(((counts - expected) ** 2 / expected).sum())


def chi2_clustered(groups, bins: int = 10, level: float = 0.95,
                   draws: int = 20_000, seed: int = 20260817,
                   min_clusters: int = 8) -> dict:
    """Is the pooled PIT histogram flatter than CLUSTERED noise? **The test.**

    ``groups`` is one entry per cluster — per city-year. An entry is either the
    cluster's PIT values, or a ``(replicates, n_columns)`` array of the same
    columns re-randomised, which is what :func:`pit_intervals` makes possible
    and what should be passed: the χ² of a single randomisation is not a stable
    number. Measured on the committed 24-city-year artefact at R=64, the
    ``reference`` population's nominal χ² runs **19.31 to 66.19** across
    re-rolls with the model standing still, and the stored single randomisation
    reads 55.61 against an R-averaged 34.44. **Never quote a χ² from one
    randomisation.** Statistics are averaged over replicates, never the PIT
    values (:func:`pit_values`).

    **What the correction is.** The nominal test treats the columns as
    independent, and they are not: a city-year's columns share a turnout draw,
    a pool structure and a national swing. Rao & Scott's first-order correction
    divides Pearson's χ² by a mean cell design effect,

        d_k = Var_cluster(p̂_k) / [p_k(1 - p_k) / N],   δ̄ = Σ_k (1-p_k) d_k/(B-1)

    with ``p_k = 1/bins`` the null and ``Var_cluster`` the with-replacement
    between-cluster variance of the pooled cell share. ``χ²/δ̄`` is then read
    against the same ``χ²(B-1)`` critical value. ``δ̄ > 1`` means clustering has
    inflated the nominal statistic and the nominal test is anti-conservative;
    ``δ̄ < 1`` means the opposite.

    **What it says here, and it is not what was feared.** On the committed
    artefact, 24 city-years:

        population    N    χ²(R=64)   δ̄      χ²_RS   crit   rejects
        reference    514     34.44   1.07    32.33   16.92   64/64
        claimed      157     41.31   1.01    41.05   16.92   64/64
        seat_holders 269    124.52   1.13   110.44   16.92   64/64
        all          580     24.67   1.06    23.62   16.92   52/64

    The design effect is ≈1, so **the rejection of uniformity survives the
    clustering correction** on both populations that may be quoted. The cluster
    bootstrap agrees: on ``claimed`` the 95% interval on χ² is [25.5, 85.0] and
    on ``reference`` [18.4, 80.0], both entirely above 16.92.

    ⛔ **δ̄ ≈ 1 IS AN AVERAGE OVER CELLS THAT RUN 0.11 TO 2.84, AND THE OLD
    EXPLANATION OF IT PREDICTED THE WRONG SIGN.** This docstring used to say
    that seats inside a council are zero-sum, so a city-year's per-column errors
    are negatively correlated, pushing the between-cluster variance below its
    independent value. That predicts δ̄ < 1, and **every measured δ̄ is ≥ 1**
    (1.07, 1.01, 1.13, 1.06). What the cells actually say, replicate-averaged
    over R=64 — this is ``deff_cells``, and the bar marks the median PIT:

        reference     0.73 0.66 0.69 0.82 0.97 | 1.27 1.25 1.28 1.34 1.70
        seat_holders  0.38 0.11 0.34 0.45 0.82 | 1.47 1.44 1.58 1.91 2.84
        all           0.70 0.78 0.78 0.86 0.92 | 1.34 1.12 1.30 1.52 1.24
        claimed       0.80 0.44 0.65 0.82 1.34 | 1.99 1.34 1.41 0.98 0.35

    The zero-sum intuition is right where the PIT is low or middling — those
    cells do run below 1 — and it is wrong at the top, where they run 1.2 to
    2.8. **A high PIT is the truth landing above the forecast: a party the model
    UNDER-forecast, which is this model's dominant failure.** The pooled
    ``reference`` histogram rises monotonically from 8.0% of its mass in the
    bottom decile to 12.4% in the top, and ``seat_holders`` from 4.1% to 21.2%.
    And under-forecasting arrives a whole city-year at a time — one turnout
    draw, one national swing, one city's small-party structure — so the count of
    top-decile columns varies between city-years far more than binomially.
    **The clustering is concentrated in the failure mode — on ``reference``,
    ``seat_holders`` and ``all``, and NOT on ``claimed``**, which is the
    opposite of harmless even though the mean is ≈1. ⛔ That qualification is
    load-bearing and must travel with the sentence: ``claimed`` is one of the
    two populations this repository may quote, so an unqualified "the
    clustering is concentrated in the failure mode" is false of half the
    headline. Measured: the correlation
    between bin index and cell design effect is **+0.71** on ``reference`` and
    **+0.90** on ``seat_holders``, and positive in 64/64 randomisations of each.

    ``claimed`` is the exception, and it is the same finding seen from the other
    side: its top cell is **0.35**, because the selection rule admits a column
    only when the model gives it a seat in half its draws, and so drops the
    under-forecast columns before they can cluster. Its top decile holds 2.3% of
    its mass against ``reference``'s 12.4%. See the ``CLAIM_FRACTION`` note at
    the top of this module.

    **Heterogeneous cells are precisely what the first-order correction assumes
    away, so it is CHECKED and not assumed.** Rao & Scott's second-order
    (Satterthwaite) form divides again by ``1 + cv²`` of the cell design effects
    and reads the result against χ² on ``(B-1)/(1+cv²)`` dof. Same artefact,
    R=64, averaging the adjusted STATISTIC over randomisations:

        population    cv²    χ²_S    dof_S   crit_S   rejects
        reference    0.177   27.46   7.67    15.04    64/64
        claimed      0.279   32.17   7.07    14.16    64/64
        seat_holders 0.572   70.42   5.74    12.19    64/64
        all          0.156   20.50   7.80    15.23    51/64

    **First order is adequate and the rejection survives on both quotable
    populations.** ``all`` reads 51/64 here against 52/64 first order: it was
    never a rejecting population by this function's own rule, and the
    second-order form does not change that. The ``cv²`` used is an UPPER bound
    on the design heterogeneity, because the PIT randomisation adds noise to
    each cell that a per-replicate ``cv²`` counts as spread — so the correction
    is conservative in the direction that matters.

    ⚠️ **THE CLUSTER LEVEL MAY BE THE WRONG ONE, AND THIS PANEL CANNOT TEST THE
    RIGHT ONE.** The clusters are whatever the caller grouped by, and
    ``compare_history`` groups by city-year — the level this panel can estimate,
    24 clusters against a floor of 8. But the panel is 8 cities × 3 CYCLES, and
    the cycle effect is the large one. sd(z) on ``reference`` across
    2011 / 2016 / 2021, **by rank band and pooled — they are different
    populations and both are quoted in this repository**:

        ranks 1-3     0.881   0.367   0.954    2.6x
        ranks 4-12    0.452   1.155   1.960    4.3x   <- §1.228 quotes THIS
        ranks 13+     0.094   0.233   0.415    4.4x
        pooled        0.601   0.889   1.265    2.1x

    with pooled mean z −0.096 / +0.013 / +0.238. §1.228's figures are the
    ranks 4-12 band, not the whole population; re-derived here on the committed
    artefact and they reproduce to three decimals. **Quote the band with the
    number** — the two were briefly recorded as a discrepancy and they are not
    one. Either way the cycle effect is large, and ranks 4-12 is the band that
    decides marginal seats. Re-clustered on YEAR (k=3, R=64, reached only by
    lowering ``min_clusters``):

        population    δ̄     χ²_RS   crit    rejects
        reference    1.61   22.27   16.92   51/64
        claimed      1.46   29.06   16.92   64/64
        seat_holders 2.20   57.67   16.92   64/64
        all          1.47   17.49   16.92   35/64

    δ̄ is 1.5 to 2.2 there, not 1.07, and on ``reference`` and ``all`` the
    rejection stops being established by this function's own rule. **So the
    honest statement is "clustering at the CITY-YEAR level buys almost nothing",
    never "the clustering correction buys almost nothing".**

    ⛔ **And those k=3 figures are a WARNING, not a result.** Three clusters give
    each cell two degrees of freedom; the cell design effects come back at 5.08
    and 10.65. **The level where the dependence lives is the level this panel
    cannot test, and a fourth cycle is the only thing that fixes it** — the
    city-year result is what is quotable, with that limitation attached to it
    wherever it is quoted.

    ⚠️ **THIS DOCSTRING USED TO CALL 5.08 AND 10.65 "a number about the
    estimator and not about the panel". THAT IS WITHDRAWN — it is not
    established, in either direction** (2026-09-13, JUDGEMENT-CALLS §D22).
    Simulated against a known null with this panel's own shape — k=3, unequal
    clusters, a pooled PIT rising 8.0% → 12.4% across the deciles, columns
    INDEPENDENT so the true design effect is 1 — the largest of the ten cell
    design effects reaches 11.10 with ``P(≥ 5.08) = 6.4%`` when the replicates
    do not average (R=1), and never exceeds 2.99 in 1500 tries once eight
    independent replicates do (R=8). The run uses R=64, but those replicates
    re-randomise **the same columns** inside their jump intervals, so they are
    positively correlated and the effective count is somewhere in between and
    **has never been computed**. Compute it before quoting either reading.

    ⚠️ The correction needs the design effect ESTIMATED, and with ``k`` clusters
    there are ``k`` of them. The three-city-year panel this question was first
    asked on could not estimate δ̄ at all; 24 city-years can. Below
    ``min_clusters`` (default 8) ``estimable`` is False and the result says so
    rather than printing a number. Lowering it is for the diagnostic question
    *where is the dependence?* and its output is not a test.

    ⛔ **``min_clusters`` IS TYPED AND 8 IS A ROUND NUMBER — JUDGEMENT-CALLS
    §D22, 🔴.** Nothing derives it. Under the null above δ̄ is unbiased at every
    k and its noise is SMOOTH in k — rse 12.1% at k=3, 6.0% at k=8, 3.1% at
    k=24 — so there is no cliff here and any floor is a line drawn on a
    continuum. What survives as an argument for having one is that χ²/δ̄ is read
    against a fixed ``χ²(B-1)`` critical value as though δ̄ were known, which is
    anti-conservative and worsens as k falls; that argues for an F-type
    reference (Rao & Scott, Thomas), not for a bright-line refusal, and the
    F-type reference has not been built.

    Returns the nominal and corrected statistics with their replicate spread,
    the per-cell design effects and their ``cv²``, the Satterthwaite pair, the
    bootstrap interval, and ``verdict``.
    """
    blocks = []
    for g in groups:
        arr = np.asarray(g, dtype=float)
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.size:
            blocks.append(arr)
    k = len(blocks)
    reps = max((b.shape[0] for b in blocks), default=0)
    dof = bins - 1
    crit = _CHI2_95.get(dof)
    out = {"n": int(sum(b.shape[1] for b in blocks)), "clusters": k,
           "bins": int(bins), "dof": dof, "chi2_crit_95": crit,
           "replicates": int(reps), "estimable": False,
           "min_clusters": int(min_clusters),
           "chi2": float("nan"), "chi2_sd": float("nan"),
           "deff": float("nan"), "deff_cells": [], "deff_cells_sd": [],
           "deff_cv2": float("nan"),
           "chi2_rs": float("nan"), "chi2_rs_sd": float("nan"),
           "chi2_satt": float("nan"), "dof_satt": float("nan"),
           "chi2_satt_crit_95": float("nan"), "rejects_satt": 0,
           "rejects_in": 0, "ci_lo": float("nan"), "ci_hi": float("nan"),
           "ci_level": float(level), "ci_draws": int(draws),
           # ⛔ THE RESULT IS ONLY AS GOOD AS THE LEVEL IT WAS CLUSTERED AT, AND
           # THIS FUNCTION CANNOT SEE WHICH LEVEL THAT WAS — the caller chose
           # it. Carried in the result so it travels with the number rather
           # than living only in a docstring nobody opens at quoting time.
           "level_caveat":
               "the clusters are whatever the caller grouped by. On this panel "
               "city-year clustering (k=24) gives delta-bar 1.07 and buys "
               "almost nothing; the CYCLE level, where the dependence actually "
               "is (sd(z) across 2011/2016/2021 is 0.601/0.889/1.265 pooled "
               "and 0.452/1.155/1.960 on ranks 4-12), has k=3 and cannot be "
               "estimated. Quote the city-year result WITH that limitation — "
               "see score.chi2_clustered.__doc__.",
           "verdict": f"not established: fewer than {int(min_clusters)} "
                      f"clusters, so the design effect cannot be estimated"}
    if k < min_clusters or crit is None or not out["n"]:
        return out
    if any(b.shape[0] != reps for b in blocks):
        raise ValueError(
            f"chi2_clustered got clusters with different replicate counts "
            f"{sorted({b.shape[0] for b in blocks})}. Every cluster must be "
            f"re-randomised the same number of times or the average is over a "
            f"different population per cluster.")

    p0 = 1.0 / bins
    chi2s, deffs, rs, cv2s, satts = [], [], [], [], []
    cells = np.empty((reps, k, bins), dtype=float)
    cell_deffs = np.empty((reps, bins), dtype=float)
    for r in range(reps):
        for c, block in enumerate(blocks):
            cells[r, c] = np.histogram(block[r], bins=bins, range=(0.0, 1.0))[0]
        a = cells[r]
        n_c = a.sum(axis=1)
        total = a.sum(axis=0)
        n = float(total.sum())
        chi2 = float(((total - n * p0) ** 2 / (n * p0)).sum())
        phat = total / n
        # with-replacement between-cluster variance of the pooled cell share
        resid = a - np.outer(n_c, phat)
        var = (k / (k - 1.0)) * (resid ** 2).sum(axis=0) / n ** 2
        d_cells = var / (p0 * (1.0 - p0) / n)
        deff = float(((1.0 - p0) * d_cells).sum() / dof)
        chi2s.append(chi2)
        deffs.append(deff)
        rs.append(chi2 / deff if deff > 0 else float("nan"))
        # Rao & Scott's SECOND-ORDER (Satterthwaite) correction. `cv2` is the
        # squared coefficient of variation of the cell design effects, standing
        # in for the one over the generalised design effects (the eigenvalues),
        # which a cell-level estimate is all this has. Per replicate, because
        # the adjusted value is a STATISTIC and this module averages statistics
        # and never the PIT values.
        mean_cell = float(d_cells.mean())
        cv2 = float(d_cells.var() / mean_cell ** 2) if mean_cell else float("nan")
        cv2s.append(cv2)
        satts.append(rs[-1] / (1.0 + cv2))
        # ⛔ THE REPLICATE MEAN, NOT ``r == 0``. It used to store the first
        # randomisation's cells beside a `deff` averaged over all R of them, so
        # the two did not even describe the same quantity — on `reference` the
        # stored cells averaged 1.115 while `deff` read 1.072, and the cells
        # moved by up to 0.5 between randomisations. `deff` is a LINEAR
        # functional of the cells, so the mean of the cells reproduces it
        # exactly; `test_scored_universe` asserts that identity, which is what
        # makes this a checkable claim rather than a convention.
        cell_deffs[r] = d_cells

    # The interval integrates BOTH sources of noise — which city-years were
    # observed, and which randomisation the PIT drew — by giving each
    # randomisation an equal share of the bootstrap draws. At reps == 1 this is
    # one `cluster_bootstrap` call with the caller's seed and draw count, so it
    # reduces exactly to the plain scheme.
    per = max(1, draws // reps)
    boot: list[np.ndarray] = []
    for r in range(reps):
        res = cluster_bootstrap([b[r] for b in blocks],
                                statistic=lambda gs: _chi2_flat(
                                    np.concatenate(gs), bins),
                                level=level, draws=per, seed=seed + r)
        boot.append(res["replicates"])
    values = np.concatenate(boot) if boot else np.zeros(0)
    lo, hi = (np.percentile(values, [100 * (1 - level) / 2,
                                     100 * (1 + level) / 2])
              if values.size else (float("nan"), float("nan")))

    mean_rs = float(np.mean(rs))
    rejects = int(sum(1 for v in rs if v > crit))
    cells_mean = cell_deffs.mean(axis=0)
    # The Satterthwaite reference distribution, on its own (fractional) dof.
    # Both the statistic and the dof are averaged over randomisations; the
    # critical value is then taken once, at the mean dof.
    dof_satt = float(np.mean([dof / (1.0 + v) for v in cv2s]))
    crit_satt = chi2_crit_95(dof_satt)
    rejects_satt = 0
    for value, c in zip(satts, cv2s):
        per_crit = chi2_crit_95(dof / (1.0 + c))
        # A dof outside the table is NOT a rejection. `chi2_crit_95` returns
        # None rather than extrapolating, and counting an unknown critical
        # value as passed would turn a gap in the table into evidence.
        if per_crit is not None and value > per_crit:
            rejects_satt += 1
    out.update({
        "estimable": True,
        "chi2": float(np.mean(chi2s)), "chi2_sd": float(np.std(chi2s)),
        "deff": float(np.mean(deffs)),
        "deff_cells": [float(v) for v in cells_mean],
        "deff_cells_sd": [float(v) for v in cell_deffs.std(axis=0)],
        "deff_cv2": float(np.mean(cv2s)),
        "chi2_rs": mean_rs, "chi2_rs_sd": float(np.std(rs)),
        "chi2_satt": float(np.mean(satts)), "dof_satt": dof_satt,
        "chi2_satt_crit_95": (float(crit_satt) if crit_satt is not None
                              else float("nan")),
        "rejects_satt": rejects_satt,
        "rejects_in": rejects,
        "ci_lo": float(lo), "ci_hi": float(hi),
    })
    # The cell SPREAD is printed beside δ̄ wherever δ̄ is: a mean over cells that
    # run 0.11 to 2.84 is not a description of any of them, and the cells are
    # where the finding is (see the docstring).
    spread = (f"cells {cells_mean.min():.2f}–{cells_mean.max():.2f}, "
              f"cv² {out['deff_cv2']:.2f}; Satterthwaite χ² {out['chi2_satt']:.2f} "
              f"against {out['chi2_satt_crit_95']:.2f} on {dof_satt:.1f} dof, "
              f"{rejects_satt}/{reps}")
    if mean_rs > crit and rejects == reps:
        out["verdict"] = (
            f"uniformity REJECTED after the clustering correction: "
            f"χ²_RS {mean_rs:.2f} against {crit} on {dof} dof, design effect "
            f"{out['deff']:.2f}, in {rejects}/{reps} randomisations "
            f"[{spread}]")
    elif mean_rs > crit:
        out["verdict"] = (
            f"not established: χ²_RS averages {mean_rs:.2f} against {crit} but "
            f"only {rejects}/{reps} randomisations reject — the answer depends "
            f"on the PIT re-roll, not on the model [{spread}]")
    else:
        out["verdict"] = (
            f"uniformity NOT rejected once the columns are clustered: χ²_RS "
            f"{mean_rs:.2f} against {crit} on {dof} dof, design effect "
            f"{out['deff']:.2f} (nominal χ² {out['chi2']:.2f}) [{spread}]")
    return out


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
                parties: Sequence[str] | None = None,
                universe: Sequence[str] | None = None) -> dict:
    """Score a seat forecast end to end. Returns a dict; see :func:`format_report`.

    ``parties`` is an optional candidate universe (see :func:`seat_matrix`); it
    fixes the column order and cannot change any number, because the scored
    columns are always this forecaster's own non-zero ones plus the ones the
    result made non-zero. Nothing here depends on what else is in the run.

    ``universe`` is the different thing, and the one a CROSS-FORECASTER
    comparison needs: the exact column set to score, filter and all. Without it
    the scored set is ``truth > 0 or this forecaster's draws > 0``, so the
    denominator moves with the forecaster — measured on the committed panel,
    the model is scored over 580 columns across the 24 city-years and
    uniform-swing over 332 — and a summed or joint score over two different
    column sets is not one comparison. Build it with :func:`hold_universe`,
    check the result with :func:`comparable`, and see ``hold_universe`` for
    what does and does not move when you do (CRPS and energy: nothing; the
    variogram: really, and in a direction the column counts do not determine).

    A ``universe`` that omits a party which actually won a seat is REFUSED. It
    would delete a real error from the sum for every forecaster at once, which
    forgives whichever of them was worse on that column — and the seven parties
    in this panel that won seats outside the input-selected ``reference`` set
    are exactly the small-party misses this model produces. A universe that
    omits a column this forecaster CLAIMS is allowed, because forgiving
    spurious mass is a defensible deliberate choice, and the count of them is
    returned as ``dropped_claims`` so it is never silent.

    Coverage and PIT are reported twice: the pair over the seats this
    forecaster CLAIMS (a seat in at least ``CLAIM_FRACTION`` of its draws), and
    ``coverage_all`` over every scored column. ⛔ **The first is a CONDITIONAL
    diagnostic, not the headline** — its selection rule is nearly the
    complement of this model's dominant failure mode and it drops eight of the
    ten worst columns in the fixed population; see the ``CLAIM_FRACTION`` note
    at the top of this module for the measured cost. The fixed population
    cannot be computed here — it is built from a previous result and a
    nomination list, which are inputs this module never reads — so it is
    ``compare_history.reference_universe`` that supplies it, and both must be
    reported.

    ⚠️ Holding the universe does not change the ``claimed`` pair at all, and
    that is provable rather than lucky: ``claimed`` is a subset of this
    forecaster's own non-zero columns, so a held SUPERSET adds only columns it
    cannot contain, and each PIT is keyed by its own party name
    (:func:`column_rng`) so no column's value moves when another is added.
    ``coverage_all`` and ``n_scored_all`` do move, and are labelled as diluted
    where they are printed.
    """
    held = None
    dropped_claims: list[str] = []
    if universe is not None:
        if parties is not None:
            raise ValueError(
                "score_seats got both `parties` and `universe`. They are "
                "different things — `parties` fixes column ORDER over a set "
                "still chosen by the forecaster, `universe` fixes the SET — "
                "and silently letting one win would make the scored columns a "
                "matter of argument order. Pass `universe` alone.")
        held = list(universe)
        duplicates = sorted({p for p in held if held.count(p) > 1})
        if duplicates:
            raise ValueError(
                f"score_seats got a universe with duplicate names "
                f"{duplicates}. Two columns would share one PIT uniform and "
                f"the column set would not be the set it reports.")
        own = set(relevant_parties([draws], actual, entrant_actual))
        lost_truth = sorted(p for p in set(actual) - set(held)
                            if actual.get(p, 0) > 0)
        if lost_truth:
            raise ValueError(
                f"score_seats was given a universe that omits {len(lost_truth)} "
                f"parties that actually won seats: {lost_truth}. Scoring on it "
                f"would delete a real error from the sum for every forecaster "
                f"at once. Union the universe with the seat-winners — "
                f"`hold_universe` already does.")
        dropped_claims = sorted(own - set(held))
    parties, samples, truth = seat_matrix(draws, actual, entrant_actual,
                                          keep_all=held is not None,
                                          parties=held if held is not None
                                          else parties)
    # with no draws every per-party column is undefined rather than zero, and
    # saying so beats returning a short array the callers below would index off
    # the end of
    empty = np.full(samples.shape[1], float("nan"))
    pits = (pit_values(samples, truth, parties, seed=seed)
            if samples.shape[0] else empty)
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
    # Selecting on the FORECAST is neutral UNDER THE NULL: the criterion depends
    # on F alone, so PIT uniformity survives it, and a calibrated forecaster
    # simulated under this rule returns mean PIT 0.503. ⛔ **THAT IS THE WHOLE
    # OF WHAT THE ARGUMENT BUYS, AND THIS COMMENT USED TO CLAIM MORE.** It said
    # the question was "the right one". It is *a* right question — a forecaster
    # is answerable for its own claims whatever the outcome — but it is a
    # CONDITIONAL one, and when the null is false the selection is not
    # informationless: on this model it drops eight of the ten worst columns in
    # the fixed population and reads sd(z) 0.784 against 1.062. The measurement
    # is at the top of this module. It is reported BESIDE a fixed population,
    # never instead of one.
    claimed = ((samples > 0).mean(axis=0) >= CLAIM_FRACTION
               if samples.shape[0] else np.zeros(samples.shape[1], dtype=bool))
    s_won = samples[:, claimed] if samples.shape[0] else samples
    t_won = truth[claimed]
    pits_won = pits[claimed] if samples.shape[0] else empty[claimed]

    return {
        "parties": parties,
        # THE SCORED COLUMN SET, DECLARED. `universe_held` False says the set is
        # this forecaster's own — fine for its own score, not comparable with
        # another forecaster's summed or joint score. `universe_key` is what
        # `comparable` matches on, and it is in the result so a stored
        # scoreboard can be checked long after the run.
        "universe_held": held is not None,
        "universe_key": universe_key(parties),
        "dropped_claims": dropped_claims if held is not None else [],
        "n_draws": int(samples.shape[0]),
        "actual": {p: int(truth[j]) for j, p in enumerate(parties)},
        "median": {p: float(median[j]) for j, p in enumerate(parties)},
        "crps": crps_by_party(samples, truth, parties),
        # the CLAIMED columns — a seat in at least CLAIM_FRACTION of the draws.
        # Not "parties that won a seat", which is what this comment said and is
        # the outcome-selected population the block above rejects; and not the
        # headline either. See the CLAIM_FRACTION note.
        "pit": pit_histogram(pits_won, bins=bins),
        "coverage": coverage(s_won, t_won, levels),
        "n_scored_calibration": int(claimed.sum()),
        # the full-column figures, kept and labelled so the difference is
        # visible rather than a matter of trust
        # `pit_all` was here: a second PIT histogram over every scored
        # column, computed on every scoring call and READ BY NOWHERE.
        # `coverage_all` below is read, which is what made this look
        # deliberate. Deleted 2026-08-22, MODEL-LOG §1.69.
        "coverage_all": coverage(samples, truth, levels),
        "n_scored_all": int(samples.shape[1]),
        "pit_values": {p: float(pits[j]) for j, p in enumerate(parties)},
        "energy": energy_score(samples, truth, seed=seed),
        "variogram": variogram_score(samples, truth),
        # kept so the new numbers can be read against the harness's old ones
        "seat_mae_median": float(np.abs(median - truth).sum()),
    }


def format_report(seats: Mapping | None = None, wards: Mapping | None = None,
                  label: str = "", top: int | None = 12) -> str:
    """Human-readable block for a :func:`score_seats` / :func:`score_wards` pair.

    ``top`` truncates the party table to fit a terminal. **None prints every
    scored party**, and anything that turns this output back into data must pass
    None.

    That is not a style note. ``build_validation.py`` builds
    ``validation_<year>.json`` by regex-parsing this block, so the display cap
    silently became the *stored* party set: twelve rows, for targets with
    fifteen to twenty-four actual seat-winners. Every seat error computed off
    that file is therefore truncated, and it was compared against errors summed
    over the whole ballot — which is not a like-for-like comparison and made a
    later iteration look worse than an earlier one. A display limit leaking into
    a data artefact is exactly the denominator drift this module's own
    ``seat_matrix`` docstring warns about, arriving through the back door.
    """
    out: list[str] = []
    if label:
        out.append(f"=== {label} ===")
    if seats:
        parties = seats["parties"]
        crps = seats["crps"]["per_party"]
        order = sorted(parties, key=lambda p: -seats["actual"][p])
        if top is not None:
            order = order[:top]
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
        # WHETHER THESE THREE MAY BE SET AGAINST ANOTHER FORECASTER'S. Printed
        # on the same line as the joint scores because that is where a reader
        # decides to quote a difference, and the summed CRPS above is subject
        # to it too — the warning that scoped this caution to `energy` and
        # `variogram` alone left the CRPS margin looking exempt.
        if seats.get("universe_held"):
            note = (f"universe HELD at {len(parties)} columns "
                    f"[{seats.get('universe_key', '?')}] — a difference against "
                    f"another forecaster scored on the same key is one "
                    f"comparison")
            if seats.get("dropped_claims"):
                note += (f"; {len(seats['dropped_claims'])} of this "
                         f"forecaster's own claimed columns are OUTSIDE it and "
                         f"go unpenalised")
        else:
            note = (f"universe NOT held: these {len(parties)} columns are this "
                    f"forecaster's own ∪ the result's, so the denominator moves "
                    f"with the forecaster — do not quote a model-vs-baseline "
                    f"difference off them")
        out.append(f"  ({note})")
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
