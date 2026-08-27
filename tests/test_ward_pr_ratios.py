"""``levels.ward_pr_ratios`` — the split-ticket ratio, and the half of it nobody reads.

The function is named in ``ARCHITECTURE.md``'s phase-A list ("~9 stages are
already functions and several have no value test") and, until this file, in
exactly one other place: the module docstring of ``tests/test_levers_are_live.py``,
which says

    ``ward_pr_ratio_overrides`` (MK 0.80, ENTRANT 0.80) — gated on
    ``not fallback``, and ``levels.ward_pr_ratios`` returns a fallback at every
    target the harness can run.

**That sentence is true and it does not mean what it looks like it means**, so
establishing which reading is right is most of what this file does.

It does NOT mean the measured path never runs. The measured path runs at every
one of the twenty-four (city, target) pairs the harness can reach — 8 cities ×
{2016, 2021, 2026} — returning between 8 and 52 measured per-party ratios
(``test_the_measured_path_runs_at_every_target_the_harness_can_reach``). What it
means is narrower and structurally worse: **the second return value is never
falsy.** It is either the median of the measured ratios (always > 0 on real
data) or the bare literal ``0.8``. So ``not fallback`` was not "dead at these
targets", it was dead by construction, and no target could ever have revived it.

Four things the seam does that nothing was checking:

CLASS — THE OUTPUT THAT IS COMPUTED, STORED, AND NEVER READ. ``run_model``
    writes the measured map to ``scenario["_ward_pr_measured"]``
    (``montecarlo.py:2352``) and no line in ``src/`` ever reads it back. The
    per-party ratios are then recomputed from the same file, inline, a few
    hundred lines later (``montecarlo.py:2715-2725``) via
    ``fold.load``/``fold.citywide``. Only the *fallback* — the second element —
    survives the round trip. Two definitions of one quantity, which CLAUDE.md's
    no-duplicated-logic rule exists to prevent, and the seam reads as wired.

CLASS — ABSENCE EQUALS THE NEUTRAL VALUE. When there is no previous LGE, no
    result file, or no votes on one of the two ballots, the function returns
    ``({}, 0.8)``. ``run_model`` gates BOTH scenario keys on ``if _ratios:``, so
    on that path ``_ward_pr_fallback`` is never set, ``scenario.get`` returns
    ``None``, the ``if fallback:`` loop does not run, and every party with no
    previous-LGE ward history keeps ``ratio = 1.0`` from ``np.ones(npar)``.
    The documented ``0.8`` is unreachable *as a value*; what actually happens is
    the identity, silently. This is ARCHITECTURE.md's headline defect class.

CLASS — THE FALLBACK IS MEASURED OVER A POPULATION THE CONSUMER REFUSES TO
    TRUST, AND RETURNED UNCLIPPED. ``run_model`` will not believe a measured
    ratio for a party under 0.1% of the previous LGE's PR vote
    (``if pc.get(p, 0) > 0.001``) and clips every one it does believe to
    ``[WARD_PR_RATIO_MIN, WARD_PR_RATIO_MAX]`` = [0.5, 2.0]. The median it hands
    those same distrusted parties instead is taken over ALL of them, unclipped,
    including exact zeros. At Johannesburg 2026 that is 29 of 52 parties; the
    fallback moves by up to 0.215 (Mangaung 2021) and 0.103 (Tshwane 2026).

CLASS — TWO COPIES, TWO WAYS TO ADDRESS THE SAME FILE. ``ward_pr_ratios`` takes
    no ``data_dir`` and substitutes ``{CODE}`` from its ``city`` ARGUMENT;
    ``run_model``'s inline copy reads through its ``data_dir`` parameter (a
    ``--data-dir`` flag exists) and substitutes ``{CODE}`` from the
    PROCESS-GLOBAL active city inside ``fold.load``. Nothing checks that the two
    halves of one quantity read the same file.

Nothing here asserts that a number equals what the code returns because the code
returns it. Every value test is either arithmetic done by hand on a constructed
ballot file, or an invariant (the fallback is the median of what was returned;
the two copies of the formula agree; no file at or after the target is opened).

Run:
    ./.venv/bin/python tests/test_ward_pr_ratios.py
    ./.venv/bin/python -m pytest tests/test_ward_pr_ratios.py -q
"""

from __future__ import annotations

import ast
import csv
import inspect
import math
import statistics
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, election_files_read, run_module, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import levels  # noqa: E402
import montecarlo as M  # noqa: E402
from fold import citywide, load  # noqa: E402

ELECTIONS = ROOT / "data" / "raw" / "elections"

# The targets the harness can actually run, from CLAUDE.md's re-emit loop: eight
# cities at 2016 and 2021, plus Johannesburg's live 2026.
HARNESS_CITIES = ("joburg", "tshwane", "ekurhuleni", "ethekwini", "capetown",
                  "mangaung", "nelsonmandelabay", "buffalocity")


# --------------------------------------------------------------------------
# constructed ballots
#
# `ward_pr_ratios` touches exactly three things on its two arguments —
# `target.previous_lge`, `cityconfig.CALENDAR[year].results` and
# `city.path("raw", "elections", template)` — and three columns of the CSV. So a
# stub is enough to drive the real function over a ballot file whose arithmetic
# is doable on paper, WITHOUT writing anything under data/ (which is shared, and
# which other workers are measuring against).
# --------------------------------------------------------------------------


class _StubCity:
    """A ``City`` as far as ``ward_pr_ratios`` is concerned: one ``path()``."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def path(self, *parts: str, root: str = "data") -> Path:
        return self._path


class _StubTarget:
    """A ``Target`` as far as ``ward_pr_ratios`` is concerned."""

    def __init__(self, previous_lge: str | None) -> None:
        self.previous_lge = previous_lge


def _ballot_file(directory: Path, rows) -> Path:
    """Write ``(BallotType, party, votes)`` rows as an IEC-shaped VD export."""
    path = directory / "constructed_lge.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Province", "Municipality", "Ward", "VD_Number",
                         "BallotType", "sPartyName", "Party_Votes"])
        for i, (ballot, party, votes) in enumerate(rows):
            writer.writerow(["GT", "JHB", "1", f"3200{i:04d}",
                             ballot, party, votes])
    return path


def _on(rows):
    """Run the real ``ward_pr_ratios`` over a constructed ballot file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _ballot_file(Path(tmp), rows)
        # 2016 is any calendar year with a non-None `results` template; the stub
        # city returns our file whatever the template says.
        return levels.ward_pr_ratios(_StubTarget("2016"), _StubCity(path))


# --------------------------------------------------------------------------
# what the sentence in test_levers_are_live.py actually means
# --------------------------------------------------------------------------


def test_the_measured_path_runs_at_every_target_the_harness_can_reach():
    """The measured path is not dead; the SECOND RETURN VALUE is never falsy.

    ``tests/test_levers_are_live.py:29`` and MODEL-LOG §1.37 justify deleting
    ``ward_pr_ratio_overrides`` on the grounds that "``levels.ward_pr_ratios``
    returns a fallback at every target the harness can run". Read as "the
    computed path never runs" that would mean a defect in the ratio measurement
    could not be detected at any target — and it would be false. This test
    establishes the true reading: the computed path runs everywhere, returning a
    non-empty map at all twenty-four (city, target) pairs, and the reason
    ``not fallback`` was dead is that the second element is the median of a
    non-empty positive set, hence always truthy.

    If this failed, either the measurement has stopped running at some target —
    in which case that target is silently forecasting entrants at the identity
    ratio, see ``test_when_the_measurement_is_unavailable_run_model_falls_back_to_1_0``
    — or the archive has lost a previous-LGE result file (MEMORY: silent input
    loss).
    """
    if not ELECTIONS.exists():
        skip("data/raw/elections is not present")
    checked = 0
    empty: list[str] = []
    for slug in HARNESS_CITIES:
        try:
            city = cityconfig.load(slug)
        except SystemExit:
            continue
        for year in ("2016", "2021", "2026"):
            target = cityconfig.Target(city, year)
            template = cityconfig.CALENDAR[target.previous_lge].results
            if not city.path("raw", "elections", template).exists():
                continue
            ratios, fallback = levels.ward_pr_ratios(target, city)
            checked += 1
            if not ratios:
                empty.append(f"{slug} {year}")
            assert fallback, (
                f"{slug} {year}: the fallback is falsy ({fallback!r}). The "
                f"whole reason `ward_pr_ratio_overrides` was unreachable is "
                f"that this value cannot be falsy; if that has changed, the "
                f"`not fallback` reasoning in MODEL-LOG §1.37 needs revisiting.")
    if checked < 8:
        skip(f"only {checked} city-years on disk; not enough to make the claim")
    assert not empty, (
        "`ward_pr_ratios` returned NO measured ratios at these targets, so the "
        "computed path did not run there and nothing tests it:\n  "
        + "\n  ".join(empty))


def test_the_fallback_alone_cannot_tell_a_measurement_from_the_hard_coded_default():
    """Only the emptiness of the dict distinguishes computed from fallback.

    ``ward_pr_ratios`` signals "I could not measure anything" by returning
    ``({}, 0.8)`` — a literal, not a sentinel. A ballot file whose measured
    median happens to be exactly 0.8 returns a second element that is
    byte-identical to the failure value, so a caller that looks only at the
    fallback cannot tell a measurement from a miss. That is the
    absence-equals-neutral shape ARCHITECTURE.md is about, one level up.

    Constructed by hand: PR 250/500/250 of 1000 -> shares .25/.50/.25; ward
    100/400/500 of 1000 -> shares .10/.40/.50; ratios .10/.25 = 0.4,
    .40/.50 = 0.8, .50/.25 = 2.0; median 0.8.

    If this failed, ``ward_pr_ratios`` had grown a distinguishable failure
    signal — which would be an improvement, and this test should be rewritten
    to pin the new one rather than deleted.
    """
    measured, fallback = _on([
        ("PR", "ALPHA PARTY", 250), ("PR", "BETA PARTY", 500),
        ("PR", "GAMMA PARTY", 250),
        ("Ward", "ALPHA PARTY", 100), ("Ward", "BETA PARTY", 400),
        ("Ward", "GAMMA PARTY", 500),
    ])
    assert measured == {"ALPHA_PARTY": 0.4, "BETA_PARTY": 0.8,
                        "GAMMA_PARTY": 2.0}, measured
    assert fallback == 0.8, fallback

    missing, missing_fallback = levels.ward_pr_ratios(
        _StubTarget(None), _StubCity(Path("nowhere.csv")))
    assert missing == {} and missing_fallback == 0.8, (missing, missing_fallback)
    assert fallback == missing_fallback, (
        "expected the coincidence this test is about")
    assert measured != missing, (
        "the ONLY discriminator between a real measurement and the hard-coded "
        "0.8 is whether the first element is empty; the fallback value is not "
        "a sentinel and must never be treated as one.")


def test_no_previous_local_election_returns_the_bare_default_without_saying_so():
    """A target with nothing behind it is silent, not loud.

    2000 is the earliest LGE in ``cityconfig.CALENDAR``, so ``previous_lge`` is
    ``None`` and there is no ward/PR history to measure at all. The function
    returns ``({}, 0.8)`` and prints nothing, raises nothing, and records
    nothing. The value 0.8 is not derived from any election: it is the
    hand-typed ``ENTRANT 0.80`` this function's own docstring says it replaced,
    left behind as the miss value.

    If this failed the miss path had changed shape, and every caller's
    ``if ratios:`` guard needs re-reading with it.
    """
    city = cityconfig.load("joburg")
    target = cityconfig.Target(city, "2000")
    assert target.previous_lge is None, target.previous_lge
    assert levels.ward_pr_ratios(target, city) == ({}, 0.8)


# --------------------------------------------------------------------------
# the arithmetic
# --------------------------------------------------------------------------


def test_the_ratio_is_the_ward_vote_share_over_the_pr_vote_share():
    """The quantity itself, against arithmetic done on paper.

    This is the number that decides how much better or worse a party does on the
    ward ballot than on the PR ballot, and it multiplies straight into ward
    win probabilities and therefore into seats. Constructed:

        PR    A 600  B 300  C 100   total 1000 -> .600 .300 .100
        ward  A 300  B 300  C 200   total  800 -> .375 .375 .250
        ratio A .375/.600 = 0.625
              B .375/.300 = 1.25
              C .250/.100 = 2.5

    If this failed, the split-ticket adjustment is computing something other
    than what its docstring and MODEL-LOG §1.37 say it computes — the most
    likely error being a raw vote ratio (300/600 = 0.5) instead of a share
    ratio, which is only the same number when the two ballots have identical
    turnout.
    """
    ratios, _fallback = _on([
        ("PR", "ALPHA PARTY", 600), ("PR", "BETA PARTY", 300),
        ("PR", "GAMMA PARTY", 100),
        ("Ward", "ALPHA PARTY", 300), ("Ward", "BETA PARTY", 300),
        ("Ward", "GAMMA PARTY", 200),
    ])
    assert ratios == {"ALPHA_PARTY": 0.625, "BETA_PARTY": 1.25,
                      "GAMMA_PARTY": 2.5}, ratios


def test_a_party_with_no_pr_votes_is_excluded_instead_of_dividing_by_zero():
    """The ratio's denominator is a PR share, so a zero PR share has no ratio.

    ``ratios`` divides each party's ward share by its PR share, and the
    comprehension is guarded by ``if pr[p] > 0``. A party can reach that line
    with ``pr[p] == 0``: the IEC publishes a row per party per voting district
    *where the party is on the ballot* (see ``contestation``'s docstring), so a
    party listed on both ballots and scoring nothing on the PR one has a PR key
    worth zero, and is in ``set(pr) & set(ward)``.

    Two things must hold and neither is a statement about the implementation.
    A ratio to a zero denominator is undefined, so the party carries no
    information and must be ABSENT — not present as ``inf``, not present as
    ``nan``, both of which would propagate into the median every entrant
    inherits and from there into ward win probabilities. And the function must
    not raise: it is called once per run inside ``run_model`` with no handler
    (montecarlo.py:2350), so a ``ZeroDivisionError`` here is a dead forecast.

    Relaxing the guard to ``pr[p] >= 0`` — MODEL-LOG §1.19's "equal to or
    greater" class, the boundary this repository has already got wrong once —
    raises ``ZeroDivisionError`` on the file below while leaving every other
    test in this file green, which is why this one exists.

    Constructed: PR A 500 / B 500 / GHOST 0 (total 1000); ward A 250 / B 750 /
    GHOST 0 (total 1000). Ratios A = .25/.50 = 0.5, B = .75/.50 = 1.5, and
    GHOST has no ratio at all.
    """
    ratios, fallback = _on([
        ("PR", "ALPHA PARTY", 500), ("PR", "BETA PARTY", 500),
        ("PR", "GHOST PARTY", 0),
        ("Ward", "ALPHA PARTY", 250), ("Ward", "BETA PARTY", 750),
        ("Ward", "GHOST PARTY", 0),
    ])
    assert set(ratios) == {"ALPHA_PARTY", "BETA_PARTY"}, (
        f"GHOST PARTY took no PR vote, so its ward/PR ratio is undefined and it "
        f"must be excluded from the map and from the median: {ratios}")
    assert all(math.isfinite(v) for v in ratios.values()), (
        f"a non-finite ratio reaches the median and then every entrant: {ratios}")
    assert ratios == {"ALPHA_PARTY": 0.5, "BETA_PARTY": 1.5}, ratios
    assert fallback == 1.0, fallback


def test_a_file_with_ward_rows_but_no_ward_votes_misses_instead_of_raising():
    """Every ward share is undefined when the ward ballot is empty; miss, don't crash.

    ``ward_total`` is the denominator of every ward share, so a result file
    carrying ward rows whose votes are all zero makes the whole measurement
    undefined, not merely one party's. ``if not pr_total or not ward_total``
    turns that into the documented miss ``({}, 0.8)``; drop the ``ward_total``
    half and the comprehension divides by zero and takes the run with it, since
    ``run_model`` calls this with no handler (montecarlo.py:2350).

    The mis-cased-ballot test above does NOT cover this: a wholly mis-cased file
    leaves ``ward`` EMPTY, so ``set(pr) & set(ward)`` is empty and no division
    is ever attempted. The guard is only load-bearing when ward keys exist and
    their votes sum to zero — a blank or zero ``Party_Votes`` column on the ward
    rows, which is the shape of the four IEC quirks in ``DATA-QUALITY.md`` that
    corrupt silently instead of erroring.

    This asserts that the degenerate file takes the miss path, NOT that the miss
    path is right: what ``run_model`` then does with ``({}, 0.8)`` is the defect
    ``test_when_the_measurement_is_unavailable_run_model_falls_back_to_1_0_not_0_8``
    documents.
    """
    try:
        result = _on([("PR", "ALPHA PARTY", 600), ("PR", "BETA PARTY", 400),
                      ("Ward", "ALPHA PARTY", 0), ("Ward", "BETA PARTY", 0)])
    except ZeroDivisionError as exc:                      # pragma: no cover
        raise AssertionError(
            "a ballot file with ward rows and no ward votes divided by a zero "
            f"ward total instead of returning the miss pair: {exc!r}") from exc
    assert result == ({}, 0.8), (
        f"expected the empty ward ballot to be a miss; got {result}")


def test_the_fallback_is_the_median_of_the_ratios_it_returned():
    """The rule the docstring promises: "the median of those that have one".

    Asserted as an invariant over the real panel rather than against any stored
    number, because the median is a property of the archive and not a judgement:
    whatever ratios came back, the fallback must be their median. A fallback
    that drifts off the set it claims to summarise would hand every entrant —
    MK and ActionSA at 2026 — a ward/PR ratio derived from nothing.

    The constructed half pins the median with an even count too, where the
    convention (mean of the middle two) is a choice: ratios 0.625, 1.25, 2.5 and
    a fourth at 1.75 give (1.25 + 1.75) / 2 = 1.5.
    """
    ratios, fallback = _on([
        ("PR", "ALPHA PARTY", 600), ("PR", "BETA PARTY", 300),
        ("PR", "GAMMA PARTY", 100),
        ("Ward", "ALPHA PARTY", 300), ("Ward", "BETA PARTY", 300),
        ("Ward", "GAMMA PARTY", 200),
    ])
    assert fallback == statistics.median(ratios.values()) == 1.25, fallback

    if not ELECTIONS.exists():
        return
    for slug in HARNESS_CITIES:
        try:
            city = cityconfig.load(slug)
        except SystemExit:
            continue
        for year in ("2016", "2021", "2026"):
            target = cityconfig.Target(city, year)
            template = cityconfig.CALENDAR[target.previous_lge].results
            if not city.path("raw", "elections", template).exists():
                continue
            ratios, fallback = levels.ward_pr_ratios(target, city)
            if not ratios:
                continue
            assert abs(fallback - statistics.median(ratios.values())) < 1e-12, (
                f"{slug} {year}: fallback {fallback} is not the median of the "
                f"{len(ratios)} ratios returned with it")


def test_a_party_that_stood_on_the_ward_ballot_and_scored_nothing_enters_as_zero():
    """A zero-vote ward slate is counted as a ratio of 0.0 and drags the median.

    ``ward`` is a ``defaultdict(int)``, so a party with ward rows and no ward
    votes IS in ``set(ward)`` and gets ``(0 / ward_total) / (pr_share) = 0.0``.
    It is then included in the median that every party with no ward history
    inherits. This is not hypothetical: INTERNATIONAL PARTY has 9 ward rows and
    0 ward votes in ``lge2021_JHB_vd_party_clean.csv``, so a 0.0 sits in the
    median that the LIVE 2026 Johannesburg forecast hands to MK and to every
    other entrant.

    Contrast a party that did not stand on the ward ballot at all: it is not in
    ``set(pr) & set(ward)`` and is excluded, which is the right treatment for
    "no information". Standing and scoring nothing is treated as the strongest
    possible evidence of ward weakness instead — and ``run_model`` would have
    clipped a measured 0.0 up to ``WARD_PR_RATIO_MIN`` = 0.5, but the fallback
    it derives from that 0.0 is not clipped at all (see the next test).

    Constructed: PR A 500 / B 500 / C 500; ward A 1000, B 0, C absent.
    Shares: PR .3333 each; ward A 1.0, B 0.0. Ratios A = 3.0, B = 0.0, and C is
    not in the map. Median = 1.5.
    """
    ratios, fallback = _on([
        ("PR", "ALPHA PARTY", 500), ("PR", "BETA PARTY", 500),
        ("PR", "GAMMA PARTY", 500),
        ("Ward", "ALPHA PARTY", 1000), ("Ward", "BETA PARTY", 0),
    ])
    assert set(ratios) == {"ALPHA_PARTY", "BETA_PARTY"}, (
        f"GAMMA stood on no ward ballot and must be absent, not zero: {ratios}")
    assert abs(ratios["ALPHA_PARTY"] - 3.0) < 1e-12, ratios
    assert ratios["BETA_PARTY"] == 0.0, ratios
    assert abs(fallback - 1.5) < 1e-12, fallback

    path = ELECTIONS / "lge2021_JHB_vd_party_clean.csv"
    if not path.exists():
        return
    city = cityconfig.load("joburg")
    live, _ = levels.ward_pr_ratios(cityconfig.Target(city, "2026"), city)
    assert live.get("INTERNATIONAL_PARTY") == 0.0, (
        "the live instance this test documents has changed; re-read the ward "
        "rows of lge2021_JHB before believing the rest of this docstring")


def test_the_fallback_is_returned_unclipped_and_can_exceed_the_consumers_bound():
    """The median handed to entrants is not held to the bound measured parties are.

    ``run_model`` clips every MEASURED ratio to ``[WARD_PR_RATIO_MIN,
    WARD_PR_RATIO_MAX]`` (montecarlo.py:2723) and then assigns the fallback to
    the unmeasured parties with no clip at all (montecarlo.py:2730-2733). So the
    bound that exists to stop a wild split-ticket ratio reaching the draw does
    not apply to the one party that is guaranteed to be a guess — an entrant.

    Constructed so the median lands outside the bound: PR A/B/C 100 each and
    D 700 of 1000; ward 250 each of 1000. Ratios A = B = C = .25/.10 = 2.5,
    D = .25/.70 = 0.357…; median 2.5, which is above WARD_PR_RATIO_MAX = 2.0.

    On today's archive every city-year's fallback happens to land inside the
    bound (0.845 to 1.123 over the 24 pairs), so this is a latent defect, not a
    live wrong number — which is exactly the kind that is cheapest to catch now
    and most expensive to discover in a forecast. If it failed because the
    function had started clipping, that is a fix and the test should be
    rewritten to pin the clip.
    """
    _ratios, fallback = _on([
        ("PR", "ALPHA PARTY", 100), ("PR", "BETA PARTY", 100),
        ("PR", "GAMMA PARTY", 100), ("PR", "DELTA PARTY", 700),
        ("Ward", "ALPHA PARTY", 250), ("Ward", "BETA PARTY", 250),
        ("Ward", "GAMMA PARTY", 250), ("Ward", "DELTA PARTY", 250),
    ])
    assert abs(fallback - 2.5) < 1e-12, fallback
    assert fallback > M.WARD_PR_RATIO_MAX, (
        f"expected the constructed median {fallback} to exceed the consumer's "
        f"clip {M.WARD_PR_RATIO_MAX}; the point of the test is that "
        f"ward_pr_ratios applies no bound of its own")


def test_the_fallback_is_measured_over_parties_run_model_refuses_to_trust():
    """The median includes the micro-parties whose own ratios are discarded.

    ``run_model`` believes a measured ratio only where the party took more than
    0.1% of the previous LGE's PR vote (``if pc.get(p, 0) > 0.001``); everyone
    below that gets the fallback instead. The fallback is the median over ALL
    parties with ward history — including that discarded tail, whose ratios are
    the wildest in the file (0.031, 0.052, 2.323 at Johannesburg 2026).

    So the number handed to an entrant is dominated by exactly the measurements
    the consumer has declared untrustworthy. At Johannesburg 2026 that is 29 of
    52 parties and moves the fallback from 1.023 to 0.951; over the panel it
    moves 17 of 24 city-years, by up to 0.215 (Mangaung 2021) and 0.103
    (Tshwane 2026), always in the direction of a lower ward ratio for entrants.

    Asserted structurally — that the returned map contains parties below the
    consumer's own credibility floor — rather than against either median, since
    neither number is independently justifiable. If it failed, the two halves
    had been brought into agreement, which is the fix.
    """
    path = ELECTIONS / "lge2021_JHB_vd_party_clean.csv"
    if not path.exists():
        skip("lge2021_JHB_vd_party_clean.csv is not present")
    cityconfig.use("joburg")
    city = cityconfig.load("joburg")
    ratios, _fallback = levels.ward_pr_ratios(cityconfig.Target(city, "2026"), city)
    pr_share = citywide(load(path, "PR")[0])
    below = {p for p in ratios if pr_share.get(p, 0.0) <= 0.001}
    assert below, (
        "no party in the fallback's population is below run_model's 0.1% "
        "credibility floor — either the floor moved or the file did")
    assert len(below) > len(ratios) / 3, (
        f"only {len(below)} of {len(ratios)} — the imbalance this test "
        f"documents has changed materially; re-measure before trusting the "
        f"numbers in this docstring")


# --------------------------------------------------------------------------
# the two copies of one formula
# --------------------------------------------------------------------------


def test_the_measured_ratios_agree_with_run_models_second_copy_of_the_formula():
    """Two implementations of one quantity must not disagree.

    ``ward_pr_ratios`` reads the previous LGE's CSV itself with ``csv.DictReader``
    and its own ``BallotType`` split; ``run_model`` re-reads the same file with
    ``fold.load(path, "Ward")`` / ``fold.load(path, "PR")`` and ``fold.citywide``
    and computes the same share ratio. CLAUDE.md forbids duplicated logic
    precisely because two copies drift; this pins them together for every party
    the consumer will actually believe (PR share > 0.1%).

    A failure means one of the two readers has changed — the likely candidates
    being the ballot-type filter (``== "Ward"`` here, case-insensitive there) or
    the vote parser (``int(float(x or 0))`` here, ``int(x)`` there) — and the
    fallback would then be summarising a different set of parties from the one
    the ratios are measured over.
    """
    if not ELECTIONS.exists():
        skip("data/raw/elections is not present")
    checked = 0
    try:
        checked = _cross_check_every_city()
    finally:
        # `fold.load` resolves {CODE} from the process-global active city, so a
        # test that walks the cities MUST put it back or it leaks into whatever
        # runs next. That is the defect
        # `test_the_city_code_comes_from_the_argument_not_the_process_global`
        # documents, met here as a hazard in the test suite itself.
        cityconfig.use("joburg")
    if not checked:
        skip("no previous-LGE result files on disk")


def _cross_check_every_city() -> int:
    checked = 0
    for slug in HARNESS_CITIES:
        try:
            city = cityconfig.load(slug)
        except SystemExit:
            continue
        cityconfig.use(slug)
        for year in ("2021", "2026"):
            target = cityconfig.Target(city, year)
            template = cityconfig.CALENDAR[target.previous_lge].results
            path = city.path("raw", "elections", template)
            if not path.exists():
                continue
            ratios, _fallback = levels.ward_pr_ratios(target, city)
            ward_share = citywide(load(path, "Ward")[0])
            pr_share = citywide(load(path, "PR")[0])
            for party, mine in ratios.items():
                if pr_share.get(party, 0.0) <= 0.001:
                    continue          # run_model does not use these
                theirs = ward_share.get(party, 0.0) / pr_share[party]
                assert abs(mine - theirs) < 1e-9, (
                    f"{slug} {year} {party}: ward_pr_ratios says {mine}, "
                    f"run_model's inline copy says {theirs}")
                checked += 1
    return checked


def test_the_measured_map_is_written_to_the_scenario_and_never_read_back():
    """DOCUMENTS A DEFECT. ``_ward_pr_measured`` is a dead write.

    ``montecarlo.py:2352`` stores the whole per-party map on the scenario and
    nothing in ``src/`` ever reads it — the ratios are recomputed inline instead
    (montecarlo.py:2715-2725). So ``ward_pr_ratios``'s first return value, which
    is the entire point of the function, is discarded by its only caller, and
    the seam reads as wired when only the median crosses it. This is the
    duplicated-logic rule in CLAUDE.md, and it is why a defect in this function's
    per-party arithmetic could not change a forecast.

    **The assertion below pins the WRONG behaviour on purpose**, so that the day
    someone wires the map through — or deletes the dead write — this test fails
    and is rewritten rather than the change going unnoticed. It is not an
    endorsement. Contrast ``_ward_pr_fallback``, which is written and read, and
    is asserted here to show the check can tell the difference.
    """
    unread, read_back = [], []
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for key, stores, loads in _scenario_key_uses(tree):
            if key == "_ward_pr_measured":
                unread.append((path.name, stores, loads))
            elif key == "_ward_pr_fallback":
                read_back.append((path.name, stores, loads))
    assert unread, "_ward_pr_measured is no longer written anywhere in src/"
    assert sum(l for _n, _s, l in unread) == 0, (
        f"_ward_pr_measured is now READ somewhere ({unread}) — good news, and "
        f"this test must be rewritten to assert what reads it.")
    assert sum(l for _n, _s, l in read_back) >= 1, (
        f"_ward_pr_fallback is no longer read ({read_back}); the fallback was "
        f"the ONLY part of ward_pr_ratios that reached the model, so nothing "
        f"the function computes is used at all now.")


def _scenario_key_uses(tree):
    """``(key, stores, loads)`` for every ``scenario[...]``-shaped key used.

    Both subscripts (``scenario["k"] = v``, ``scenario["k"]``) and the ``.get`` /
    ``.setdefault`` / ``.pop`` forms count, because ``run_model`` uses all of
    them. Docstrings and comments cannot match, which is the point: a textual
    reference count passes for a dead write (test_levers_are_live.py says the
    same of its four levers).
    """
    counts: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        key = None
        is_store = False
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
            key = node.slice.value
            is_store = isinstance(node.ctx, ast.Store)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr in ("get", "setdefault", "pop") \
                and node.args and isinstance(node.args[0], ast.Constant):
            key = node.args[0].value
        if not isinstance(key, str) or not key.startswith("_ward_pr"):
            continue
        slot = counts.setdefault(key, [0, 0])
        slot[0 if is_store else 1] += 1
    return [(k, s, l) for k, (s, l) in counts.items()]


def test_ward_pr_ratios_cannot_be_told_which_data_dir_the_rest_of_the_run_reads():
    """DOCUMENTS A DEFECT. The two copies address the file by different routes.

    ``run_model`` takes ``data_dir`` (there is a ``--data-dir`` flag on
    ``montecarlo``, ``backtest``, ``compare_history`` and six other scripts) and
    reads the previous LGE through it. ``ward_pr_ratios`` takes no such
    parameter: it hard-codes ``city.path("raw", "elections", …)``. Point a run at
    a different archive and the per-party ratios come from the new one while the
    fallback comes from the default — or, if the default directory is absent,
    ``ward_pr_ratios`` silently returns ``({}, 0.8)``, the scenario key is never
    set, and every unmeasured party falls to 1.0.

    Nothing here asserts the divergence is harmful today (both routes resolve to
    ``data/raw/elections`` under the default). It asserts that the divergence
    EXISTS, so that "the fallback and the ratios came from the same file" is a
    checked property rather than a coincidence of default arguments.
    """
    assert "data_dir" in inspect.signature(M.run_model).parameters, (
        "run_model no longer takes data_dir; re-read this test")
    assert "data_dir" not in inspect.signature(levels.ward_pr_ratios).parameters, (
        "ward_pr_ratios now takes data_dir — the defect this documents is "
        "fixed; assert instead that run_model passes its own through.")

    city = cityconfig.load("joburg")
    cityconfig.use("joburg")          # resolve_path reads the process global
    target = cityconfig.Target(city, "2026")
    default_dir = inspect.signature(M.run_model).parameters["data_dir"].default
    theirs = Path(default_dir) / target.results(target.previous_lge)
    mine = city.path("raw", "elections",
                     cityconfig.CALENDAR[target.previous_lge].results)
    assert cityconfig.resolve_path(theirs) == mine, (
        f"the two routes to the previous LGE's file no longer agree even at "
        f"the default: {cityconfig.resolve_path(theirs)} vs {mine}")


def test_the_city_code_comes_from_the_argument_not_the_process_global():
    """DOCUMENTS A DEFECT. ``{CODE}`` is resolved two different ways.

    ``ward_pr_ratios`` substitutes ``{CODE}`` from the ``city`` it is HANDED;
    ``fold.load``, which run_model's inline copy goes through, calls
    ``cityconfig.resolve_path`` and substitutes from the PROCESS-GLOBAL active
    city. ``run_model`` calls ``ward_pr_ratios(target, target.city)``, so if the
    active city and ``target.city`` ever diverge — and the active city is
    mutable module state that ``compare_history`` sets per process and
    ``run_model`` itself flips to read the previous LGE's contestation and back
    (montecarlo.py:2360-2363) — the fallback would be measured from one metro's
    ballots and the ratios from another's, with no error.

    This test makes the divergence visible by driving it deliberately. It is not
    a claim that any current caller does so.
    """
    if not (ELECTIONS / "lge2021_JHB_vd_party_clean.csv").exists() or not \
            (ELECTIONS / "lge2021_TSH_vd_party_clean.csv").exists():
        skip("need both the Johannesburg and Tshwane 2021 result files")
    joburg, tshwane = cityconfig.load("joburg"), cityconfig.load("tshwane")
    cityconfig.use("joburg")
    try:
        # The ARGUMENT wins inside ward_pr_ratios ...
        theirs, _ = levels.ward_pr_ratios(cityconfig.Target(tshwane, "2026"),
                                          tshwane)
        # ... while the process global wins inside fold.load, for the same
        # template string, in the same breath.
        template = cityconfig.CALENDAR["2021"].results
        active_share = citywide(load(Path("data/raw/elections") / template, "PR")[0])
        tshwane_share = citywide(load(tshwane.path("raw", "elections", template),
                                      "PR")[0])
    finally:
        cityconfig.use("joburg")
    assert theirs, "Tshwane 2026 measured nothing; the file may have moved"
    assert active_share != tshwane_share, (
        "resolve_path no longer follows the process-global active city, so the "
        "divergence this test documents is gone — delete it and say so.")


# --------------------------------------------------------------------------
# temporal validity
# --------------------------------------------------------------------------


def test_ward_pr_ratios_reads_no_election_at_or_after_its_target():
    """A ratio measured from the target's own ballots would score beautifully.

    The whole quantity is "how a party splits its ticket", and the target
    election is where the answer is written down. Reading it would leak the
    result straight into the ward win probabilities — the ``MK 0.80`` and
    ``ENTRANT 0.80`` constants this function replaced were, by MODEL-LOG §1.37's
    own account, "read off the target".

    Watched at the file level rather than restated as a calendar fact, per
    ``_support.election_files_read``: a guard rewritten as an assertion about
    the calendar passes with the guard deleted. This asserts both that no file
    at or after the target was opened AND that a file WAS opened, because "no
    late file" is not evidence if nothing was read.
    """
    if not (ELECTIONS / "lge2016_JHB_vd_party_clean.csv").exists():
        skip("lge2016_JHB_vd_party_clean.csv is not present")
    city = cityconfig.load("joburg")
    cityconfig.use("joburg")
    for year in ("2021", "2026"):
        target = cityconfig.Target(city, year)
        with election_files_read() as seen:
            ratios, _fallback = levels.ward_pr_ratios(target, city)
        assert ratios, f"{year}: nothing measured, so nothing was read"
        assert seen, f"{year}: no election file was opened at all"
        late = [s for s in seen if s[0] >= year]
        assert not late, (
            f"target {year} opened an election at or after its own polling "
            f"day: {late}")
        assert all(s[0] == target.previous_lge and s[1] == "LGE" for s in seen), (
            f"target {year} should read {target.previous_lge} and nothing "
            f"else; it read {sorted({(s[0], s[1]) for s in seen})}")


# --------------------------------------------------------------------------
# the reader
# --------------------------------------------------------------------------


def test_a_ballot_type_that_is_not_exactly_Ward_is_counted_as_a_pr_vote():
    """DOCUMENTS A DEFECT. The ballot split is case-sensitive and not exhaustive.

    ``(ward if row.get("BallotType") == "Ward" else pr)`` sends everything that
    is not the exact string ``"Ward"`` into the PR denominator — a different
    spelling, a blank, or a third ballot type such as a district council's
    ``DC 40%``. ``fold.load``, reading the same column for the same purpose,
    upper-cases both sides and filters explicitly, so the two copies disagree on
    what a ward vote is.

    All thirty-three LGE files in ``data/raw/elections`` today carry exactly
    ``"PR"`` and ``"Ward"``, so this is latent. Its failure mode is the worst
    available: a wholly mis-cased file leaves ``ward_total == 0``, returns
    ``({}, 0.8)``, and — because ``run_model`` gates the scenario key on the
    map being non-empty — leaves every party at the identity 1.0 with no
    message. DATA-QUALITY.md records four IEC CSV quirks that corrupt silently
    rather than erroring; this is the fifth waiting to happen.

    Constructed: the same ballots as the arithmetic test with ``Ward`` spelled
    ``WARD``.
    """
    good, _ = _on([("PR", "ALPHA PARTY", 600), ("PR", "BETA PARTY", 400),
                   ("Ward", "ALPHA PARTY", 500), ("Ward", "BETA PARTY", 500)])
    assert good, "the control case must measure something"

    miscased = _on([("PR", "ALPHA PARTY", 600), ("PR", "BETA PARTY", 400),
                    ("WARD", "ALPHA PARTY", 500), ("WARD", "BETA PARTY", 500)])
    assert miscased == ({}, 0.8), (
        f"expected the mis-cased ballot type to collapse to the silent default; "
        f"got {miscased}. If the reader has become case-insensitive that is a "
        f"fix — rewrite this test to assert the two spellings agree.")

    third = _on([("PR", "ALPHA PARTY", 600), ("PR", "BETA PARTY", 400),
                 ("DC 40%", "ALPHA PARTY", 900), ("DC 40%", "BETA PARTY", 100),
                 ("Ward", "ALPHA PARTY", 500), ("Ward", "BETA PARTY", 500)])
    assert third[0] != good, (
        "a third ballot type was absorbed into the PR denominator and changed "
        "every ratio; that is the defect. If it is now excluded, say so here.")


def test_when_the_measurement_is_unavailable_run_model_falls_back_to_1_0_not_0_8():
    """DOCUMENTS A DEFECT, and it is the absence-equals-neutral class exactly.

    ``ward_pr_ratios`` documents ``0.8`` as its fallback and returns
    ``({}, 0.8)`` when it cannot measure. ``run_model`` then does::

        _ratios, _fallback = _levels.ward_pr_ratios(target, target.city)
        if _ratios:                                  # montecarlo.py:2351
            scenario["_ward_pr_measured"] = _ratios
            scenario["_ward_pr_fallback"] = _fallback
        ...
        fallback = scenario.get("_ward_pr_fallback")  # montecarlo.py:2730
        if fallback:
            for p, i in index.items():
                if pc.get(p, 0) <= 0.001:
                    ratio[i] = fallback

    Both keys are gated on the MAP being non-empty, so on the miss path the
    fallback never reaches the scenario, ``scenario.get`` returns ``None``, the
    loop does not run, and every party with no previous-LGE ward history keeps
    ``ratio = 1.0`` from ``np.ones(npar)`` — the identity. The documented 0.8 is
    unreachable as a value, and "we could not measure this" is indistinguishable
    from "the ward and PR ballots behave identically", which for an entrant is
    the single most consequential assumption in the ward model.

    Asserted at the source, because the alternative is a full model run, which
    this phase does not do. Both the guard and the neutral initialisation are
    pinned, so removing either fails here.
    """
    source = (ROOT / "src" / "montecarlo.py").read_text(encoding="utf-8")
    assert 'if _ratios:\n            scenario["_ward_pr_measured"] = _ratios' in source \
        and 'scenario["_ward_pr_fallback"] = _fallback' in source, (
            "the guard around the two ward/PR scenario keys has changed shape; "
            "re-derive whether the miss path still lands on 1.0")
    assert 'fallback = scenario.get("_ward_pr_fallback")' in source, (
        "the consumer no longer reads the fallback off the scenario")
    assert "ratio = np.ones(npar)" in source, (
        "the ward/PR ratio vector is no longer initialised to the identity; if "
        "it is now initialised to the declared fallback, this defect is fixed "
        "and the test should say so")
    # And the function really does hand back the pair that triggers it.
    assert levels.ward_pr_ratios(_StubTarget("2016"),
                                 _StubCity(Path("no-such-file.csv"))) == ({}, 0.8)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
