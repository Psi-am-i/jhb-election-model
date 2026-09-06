"""End-to-end invariants for the prediction chain.

================================================================================
**HOW A POOL IS BUILT. THIS IS THE RULE. IT IS NOT NEGOTIABLE.**

**A POOL IS CALCULATED PER CITY, AND THEN PER WARD.**

**IT IS GENERATED FROM LOCAL DATA. VOTER REGISTRATION TRUMPS CENSUS DATA.**

**THE CENSUS IS A SENSE CHECK, NOT A SOURCE OF TRUTH.**
================================================================================

Registration and votes are COUNTED, published per voting district, every
cycle. Census ward figures are MODELLED small-area estimates, and for the
groups that matter most they are disputed by 14-24% in the published
literature — Johannesburg's white pool comes out at 187% of its own
voting-age population, which cannot be true. So the census may inform the
*split* of a ward between pools, and it may never override a counted total,
and it may never be transported from one city to another.

Two violations of this rule have already shipped, both caught by the project
owner and not by any automated review:

* ``measure_pool_ratios`` took Johannesburg's fitted party-to-pool weights and
  applied them to Cape Town's, eThekwini's and Mangaung's party shares, then
  called the result those cities' pool ratios. It measured a quantity that
  describes no city. In Johannesburg the PA is ~94% Coloured; in Cape Town the
  DA, GOOD and PA occupy that pool completely differently.
* A national fit was briefly used as a prior on city rates, on the theory that
  "direction transfers between cities". It does not: the Coloured pool in Cape
  Town and in Johannesburg are different populations with different politics.

Neither was caught by three separate adversarial reviews, because the
docstrings asserted the design as deliberate and the reviews checked the code
against the docstrings. Hence this banner: the rule lives in the test file, in
the place a reviewer cannot mistake for an implementation detail, and the tests
below enforce it.

**AND THE MODEL MUST BE VALIDATED ACROSS METROS.** That is the point of having
eight of them. Each city's pools are fitted on its own wards from its own
registration; what a multi-metro run tests is whether the METHOD works, not
whether one city's pools describe another. Fitting on seven and scoring the
eighth is the only out-of-sample estimate available, and n=2 in one city is not
a skill estimate.


Every defect this file guards against reached the working tree unopposed,
because nothing tested ``pools``, ``levels``, ``montecarlo``, ``score``,
``backtest`` or ``benchmarks`` — the entire forecast path and the entire
scoring path were uncovered. Two adversarial audits then found, among others:

* the entrant relabel in ``score.seat_matrix`` deleting the model's own
  forecast for a named new party (a dict comprehension keeping the last
  colliding key);
* coverage and PIT computed over parties that won nothing and were forecast
  nothing, which inverted the calibration verdict;
* ``default_seeds`` seeding MK on top of its own 12.22% baseline while
  debiting the ANC to half its measured share;
* ``contesting_parties`` returning an empty set for a not-yet-held election,
  silently deleting every seed from the live spec;
* ``levels.py`` fitting a dispersion, printing it, and applying it to
  thirteen micro-parties and none that matter.

None of those is exotic. Each is an *invariant* that was quietly false: a
constraint that must hold, a number that must be used, a set that must not be
empty. So the tests here are written as invariants over the real pipeline
rather than as unit tests over helpers — a helper that is individually correct
and never called is exactly the failure mode this repository keeps producing.

Two rules for anything added here:

**Assert the property, not the value.** A golden number belongs in
``test_drawer.py``, which exists to catch silent drift and is deliberately
re-recorded on purpose. Here, prefer "the pool's rates sum to one" over "the
ANC's rate is 0.53", because the former survives a legitimate re-fit and the
latter fails on every one, trains people to re-record without reading, and
then catches nothing.

**Name the defect.** Each test says which real failure it would have caught.
A test whose purpose nobody remembers is deleted the first time it is
inconvenient.

Runs standalone or under pytest::

    ./.venv/bin/python tests/test_chain.py
    ./.venv/bin/python -m pytest tests/test_chain.py -q
"""

from __future__ import annotations

import collections
import csv
import os
import json
import tomllib
import sys
import ast
import inspect
import tempfile
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np                                              # noqa: E402
from _support import (ROOT, election_files_read, run_module,    # noqa: E402
                      skip)

import cityconfig                                               # noqa: E402
import levels                                                   # noqa: E402
import montecarlo as mc                                         # noqa: E402
import parties                                                  # noqa: E402
import pools                                                    # noqa: E402
import score as S                                               # noqa: E402

CITY = "joburg"
FIT_YEAR = "2021"          # a held election, so every input exists
TARGET = "2026"            # the live forecast: not held, no result file


# --------------------------------------------------------------------------
# fixtures — built once, because a pool fit takes tens of seconds
# --------------------------------------------------------------------------
_CACHE: dict = {}


def _cfg():
    if "cfg" not in _CACHE:
        _CACHE["cfg"] = pools.load_config()
    return _CACHE["cfg"]


def _city():
    cityconfig.use(CITY)
    return cityconfig.load(CITY)


def _fit():
    """The joint pool fit on a held election."""
    if "fit" not in _CACHE:
        _CACHE["fit"] = pools.fit_city(_city(), FIT_YEAR, _cfg())
    return _CACHE["fit"]


def _counts():
    if "counts" not in _CACHE:
        _CACHE["counts"] = pools.pool_counts(_city(), FIT_YEAR, _cfg())
    return _CACHE["counts"]


def _spec(target: str):
    """The pool spec for a target, BUILT HERE by the code under test.

    It used to be read from ``data/processed/pools_{target}.json``, and that
    made every test below a statement about a file rather than about the code
    that writes it: a mutation making ``contesting_parties`` return an empty
    roster for an unheld target — the exact defect that once deleted every
    newcomer from the live forecast — left the three spec tests green, because
    the stale JSON on disk still had the parties in it. They would only have
    noticed after someone re-emitted, which is precisely when nobody is
    looking.

    ``emit_pools`` returns the structure and writes nothing, so calling it
    cannot overwrite the spec the live forecast reads (a real hazard here: an
    un-namespaced write from one city has reached another city's forecast
    before).
    """
    key = f"spec{target}"
    if key not in _CACHE:
        city = _city()
        _CACHE[key] = pools.emit_pools(
            city, cityconfig.Target(city=city, year=target), _cfg())
    return _CACHE[key]


# --------------------------------------------------------------------------
# 1. the constrained fit — what must be true of any election
# --------------------------------------------------------------------------

def _raw_joint_fit():
    """``fit_joint``'s OWN output, before ``balance_margins`` touches it.

    This distinction is the whole point of the next four tests. ``fit_city``
    runs ``raw = fit_joint(...)`` and then ``R = balance_margins(raw, ...)``,
    and IPF forces both margins exactly whatever it was handed — so asserting
    on the finished product certifies one line of ``balance_margins`` and says
    NOTHING about the fit. Proven by a review: replacing ``fit_joint`` with
    uniform random noise left all three assertions green.

    ``raw`` comes back from ``fit_city`` rather than being refitted here, so
    what is asserted about is the matrix the production run actually computed.
    Refitting in the test would quietly diverge — ``fit_city`` drops parties
    that polled zero in every ward from its universe, and a test that missed
    that would be fitting a different problem and certifying the answer.
    """
    if "raw" not in _CACHE:
        _, ctx = _fit()
        _CACHE["raw"] = (ctx["raw_rates"], ctx["parties"])
    return _CACHE["raw"]


def test_the_fit_itself_never_returns_a_negative_rate():
    """No party wins a negative number of votes — asserted on FIT_JOINT.

    Caught: independent per-party fits put Al Jama-ah at -1.9% +/- 0.3 among
    white voters and the PA at -3.5% among Indian voters. Tight negatives are
    misspecification, not noise.
    """
    R, universe = _raw_joint_fit()
    worst = float(R.min())
    where = universe[int(np.argmin(R.min(axis=0)))]
    assert worst >= -1e-12, f"fit_joint returned {worst} (worst party {where})"


def test_the_fit_itself_allocates_exactly_one_vote_per_pool():
    """Every voter votes for someone — asserted on FIT_JOINT, not on IPF.

    Caught: the white pool was assigned 111.4% of its voters and the Coloured
    pool 90.4%, with 106.1% of the vote existing in total.
    """
    R, _ = _raw_joint_fit()
    sums = R.sum(axis=1)
    assert np.allclose(sums, 1.0, atol=1e-6), \
        f"fit_joint's pool rates sum to {sums}, not 1"


def test_the_fit_beats_the_only_answer_it_is_allowed_to_fall_back_to():
    """The fit must explain the wards better than "every ward votes alike".

    The two constraint tests above are necessary and jointly worthless as a
    check on the FIT: ``_project_simplex`` enforces both by construction, so a
    ``fit_joint`` that ignored the data entirely and returned any feasible
    matrix — the uniform 1/n it starts from, or noise projected onto the
    simplex — passes them. What no such matrix passes is this.

    Giving every pool the city's own shares is a feasible point of exactly the
    problem ``fit_joint`` minimises (it is non-negative and sums to one), and
    it is the answer that says pools do not differ. A minimiser must therefore
    come back with a strictly lower objective than it. That is not a magnitude
    to re-record; it is arithmetic that only fails if the solver stopped
    early, ran backwards, or never looked at ``Y``.
    """
    R, _ = _raw_joint_fit()
    _, ctx = _fit()
    E, Y, votes = ctx["comp"], ctx["Y"], ctx["votes"]

    def objective(rates):
        sw = np.sqrt(votes / votes.sum())[:, None]
        return float((((E @ rates - Y) * sw) ** 2).sum())

    citywide = np.average(Y, axis=0, weights=votes)
    null = np.tile(citywide, (E.shape[1], 1))
    assert abs(null.sum(axis=1) - 1.0).max() < 1e-9, \
        "the null is not a feasible point; this test's premise has changed"
    fitted, flat = objective(R), objective(null)
    assert fitted < flat, (
        f"the joint fit ({fitted:.6e}) explains the wards no better than "
        f"giving every pool the citywide shares ({flat:.6e}) — it is not "
        f"minimising anything")


def test_balancing_hits_both_known_margins():
    """IPF's own postcondition, asserted separately from the fit's."""
    fits, ctx = _fit()
    electorate = ctx["pool_votes"]
    total = electorate.sum()
    worst = max(abs(float(f.rates @ electorate) / total - f.citywide)
                for f in fits.values())
    assert worst < 1e-6, f"worst party-total error after balancing {worst:.2e}"
    rates = np.array([f.rates for f in fits.values()])
    assert np.allclose(rates.sum(axis=0), 1.0, atol=1e-6), \
        "pool rates do not sum to 1 after balancing"


def test_the_fit_refuses_rather_than_returning_an_unconverged_iterate():
    """A number that is a function of the iteration cap is not an estimate.

    Caught: 4000 fixed gradient steps left ~37% of the error, and the DA's rate
    in the smallest pool read 20.9% at 4000 iterations and 0.2% at 400,000.
    """
    _, ctx = _fit()
    comp, vote, wards, shares = (ctx["comp"], ctx["votes"], ctx["wards"],
                                 ctx["shares"])
    # The REAL matrix. A single-column Y is fully determined by the simplex
    # constraint and converges in two steps, so slicing one out tests nothing.
    universe = sorted({p for w in wards for p in shares[w]})
    Y = np.array([[shares[w].get(p, 0.0) for p in universe] for w in wards])
    try:
        pools.fit_joint(comp, Y, vote, iters=2)
    except RuntimeError:
        return                     # refused, which is the point
    raise AssertionError("fit_joint returned after 2 iterations without "
                         "checking convergence")


# --------------------------------------------------------------------------
# 1b. THE POOL RULE — local data, registration over census, never transposed
# --------------------------------------------------------------------------

def test_a_pool_is_never_built_from_another_citys_composition():
    """THE RULE: pools are per city. A composition fitted on one city may not
    be applied to another's votes.

    Caught by the project owner, missed by three adversarial reviews:
    measure_pool_ratios applied Johannesburg's party-to-pool weights to Cape
    Town's, eThekwini's and Mangaung's party shares. In Johannesburg the PA is
    ~94% Coloured; in Cape Town the DA, GOOD and PA occupy that pool
    completely differently, so the result described no city.
    """
    import inspect
    src = inspect.getsource(pools.measure_pool_ratios)
    if "codes" in inspect.signature(pools.measure_pool_ratios).parameters:
        default = inspect.signature(
            pools.measure_pool_ratios).parameters["codes"].default
        assert default is None or len(list(default)) <= 1, (
            "measure_pool_ratios defaults to several metros while taking ONE "
            f"composition ({list(default)}). One city's party-to-pool weights "
            f"applied to another city's votes measures nothing real. Fit each "
            f"city's pools on its own wards.")


def test_counted_totals_are_never_overridden_by_the_census():
    """THE RULE: registration trumps census. The census may inform the split
    of a ward between pools; it may never move a counted total.

    Registration and votes are published per voting district. Census ward
    figures are modelled, and for the groups that matter are disputed by
    14-24% — Johannesburg's white pool is 187% of its own voting-age
    population.
    """
    city = _city()
    reg, votes = pools.ward_totals(city, FIT_YEAR)
    c = _counts()
    for ward_i, ward in enumerate(c.wards[:40]):        # a sample is enough
        assert abs(c.registered[ward_i].sum() - reg[ward]) < 0.5, (
            f"ward {ward}: pools hold {c.registered[ward_i].sum():,.0f} "
            f"registered against a published {reg[ward]:,.0f}")
        assert abs(c.voted[ward_i].sum() - votes.get(ward, 0.0)) < 0.5, (
            f"ward {ward}: pools hold {c.voted[ward_i].sum():,.0f} votes "
            f"against a published {votes.get(ward, 0.0):,.0f}")


def test_the_pool_split_is_computed_per_ward_not_citywide():
    """THE RULE: per city, and THEN per ward. A single citywide composition
    applied to every ward would erase the geography the whole model rests on."""
    c = _counts()
    comp = c.composition("voted")
    spread = comp.max(axis=0) - comp.min(axis=0)
    assert (spread > 0.2).any(), (
        "every ward has nearly the same pool composition; the split is not "
        f"being computed per ward (max spread per pool: {spread.round(3)})")


# --------------------------------------------------------------------------
# 2. the nested voter sets
# --------------------------------------------------------------------------

def test_the_nested_levels_are_ordered_where_the_data_allows():
    """people >= voting_age, and voted <= registered.

    The registered-vs-voting-age step is NOT asserted: Johannesburg's white
    pool genuinely comes out at 187% of it, which is a defect in the published
    census rather than in this code (DATA-QUALITY item 11). That one must be
    *reported*, which the next test checks.
    """
    c = _counts()
    assert (c.voting_age.sum(axis=0) <= c.people.sum(axis=0) + 1e-6).all(), \
        "a pool has more voting-age people than people"
    assert (c.voted.sum(axis=0) <= c.registered.sum(axis=0) + 1e-6).all(), \
        "a pool cast more votes than it has registered voters"


def test_an_impossible_nesting_is_reported_not_swallowed():
    """The 187% is known. Silence about it would be the bug."""
    c = _counts()
    over = c.registered.sum(axis=0) / np.maximum(c.voting_age.sum(axis=0), 1e-9)
    if (over > 1.0).any():
        assert c.violations, ("a pool has more registered voters than adults "
                              "and nothing was reported")


def test_every_level_is_anchored_to_its_published_ward_total():
    """Only the split across pools is estimated; the totals are counted."""
    city = _city()
    reg, votes = pools.ward_totals(city, FIT_YEAR)
    c = _counts()
    published_reg = sum(reg[w] for w in c.wards)
    published_votes = sum(votes.get(w, 0.0) for w in c.wards)
    assert abs(c.registered.sum() - published_reg) < 1.0, \
        f"registered {c.registered.sum():,.0f} vs published {published_reg:,.0f}"
    assert abs(c.voted.sum() - published_votes) < 1.0, \
        f"votes {c.voted.sum():,.0f} vs published {published_votes:,.0f}"


# --------------------------------------------------------------------------
# 3. seeds — a vector and a level are different questions
# --------------------------------------------------------------------------

def _baseline_shares(target: str = TARGET) -> dict[str, float]:
    """Each party's share of the target's baseline election, from the file."""
    key = f"baseline{target}"
    if key not in _CACHE:
        import csv
        from collections import defaultdict

        import parties as P
        city = _city()
        year = cityconfig.Target(city=city, year=target).previous_npe
        path = city.path("raw", "elections", cityconfig.CALENDAR[year].results)
        if not path.exists():
            skip(f"no baseline at {path}")
        counts: dict = defaultdict(int)
        with open(path, encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                counts[P.canonical(row["sPartyName"])] += int(
                    float(row.get("Party_Votes") or 0))
        total = sum(counts.values())
        _CACHE[key] = {p: v / total for p, v in counts.items()} if total else {}
    return _CACHE[key]


def test_a_party_with_a_baseline_is_never_seeded():
    """Caught: MK held 12.22% of the 2024 baseline AND got a +15.98% seed, so
    a split already present in the baseline was applied twice — MK started at
    28.20% and the ANC was debited to 15.98%, half its measured share. It
    produced ANC 36 / MK 68."""
    spec = _spec(TARGET)
    seeds = spec.get("seeds", {})
    baseline = _baseline_shares()
    offenders = [p for p, v in seeds.items()
                 if v > 0 and baseline.get(p, 0.0) > 1e-6]
    assert not offenders, \
        f"seeded despite already holding a baseline share: {offenders}"


def test_every_baseline_party_reaches_a_pool():
    """A party in no pool falls to the residual bucket and is drawn against a
    range meant for minor parties. MK, 12.2% of the baseline, was drawn at mode
    1.30 against a theta_mode of 0.60."""
    spec = _spec(TARGET)
    members = {p for cfg in spec["pools"].values() for p in cfg["members"]}
    seeds = set(spec.get("seeds", {}))
    missing = [p for p in ("ANC", "DA", "EFF", "MK", "PA", "IFP")
               if p not in members and p not in seeds]
    assert not missing, f"baseline parties in no pool: {missing}"


def test_emitting_for_an_unheld_target_does_not_silently_empty_the_spec():
    """Caught: contesting_parties() reads the target's result file, which does
    not exist before the election, so the roster came back empty and every
    newcomer vanished from the LIVE forecast while the backtests looked fine.

    What the defect deletes is the parties with NO vector from the fitting
    election — everyone who contested it keeps theirs either way. So counting
    pool members could not see it: with the fallback removed the spec still
    carried 40-odd fitted parties and this test stayed green. It now asks the
    question the defect answers wrongly, which is whether the parties that
    arrived AFTER the fitting election are still in the spec at all.
    """
    city = _city()
    assert not pools.contesting_parties(city, TARGET), \
        "an unheld target now has a roster; this test's premise has changed"
    spec = _spec(TARGET)
    members = {p for cfg in spec["pools"].values() for p in cfg["members"]}
    carried = members | set(spec.get("seeds") or {}) \
        | set(spec.get("no_measured_vector") or {})
    # Anything material in the baseline must reach the spec by one of those
    # three routes, whether or not it existed at the fitting election. MK is
    # the live case: 12.22% of 2024, absent from 2021.
    dropped = sorted(p for p, share in _baseline_shares().items()
                     if share > 0.005 and p not in carried)
    assert not dropped, (
        f"parties holding over 0.5% of the baseline are in the {TARGET} spec "
        f"nowhere — not as pool members, seeds or declared vectorless: "
        f"{dropped}. The roster fallback has stopped working, and the live "
        f"forecast is the run that loses them.")
    assert len(members) > 10, \
        (f"only {len(members)} parties carry a pool vector for {TARGET}; the "
         f"fit itself has emptied")


# --------------------------------------------------------------------------
# 4. temporal validity — a forecast may not read its own answer
# --------------------------------------------------------------------------

def test_pool_ratios_are_measured_only_before_the_target():
    for target in ("2016", "2021"):
        pairs = pools.lge_transitions(before=target)
        late = [p for p in pairs if int(p[1]) >= int(target)]
        assert not late, f"target {target} would measure ratios over {late}"


def test_the_level_prior_reads_no_election_at_or_after_its_target():
    """``levels.theta_record`` must stop strictly before the target.

    Caught nothing for as long as it existed. The first version asserted that
    the CALENDAR contains an LGE before 2016 and that the record is non-empty
    — both true with ``theta_record``'s ``continue`` deleted, because neither
    statement is about what the function read. It now watches the file opens:
    a θ record for 2016 that touches ``lge2021_...`` or ``npe2019_...`` has
    read its own answer, and says so with the filename.
    """
    city = _city()
    for year in ("2016", "2021"):
        target = cityconfig.Target(city=city, year=year)
        with election_files_read() as reads:
            record = levels.theta_record(target)
        assert record, f"no theta record before {year}"
        assert reads, (f"the θ record for {year} opened no election file at "
                       f"all; the spy is watching the wrong thing")
        late = sorted({(y, kind) for y, kind, _ in reads if int(y) >= int(year)})
        assert not late, (
            f"the θ prior for target {year} read {late} — a retention ratio "
            f"measured across the election being forecast")


# --------------------------------------------------------------------------
# 5. scoring — the instrument every decision is made against
# --------------------------------------------------------------------------

BLOC = {"parent": "Black African", "name": "IFP-located", "indicator": "IFP",
        "within_rate": 0.90}


def test_split_or_entrant_is_decided_in_exactly_one_place():
    """The classification lived in three places and they disagreed.

    ``SPLITS``, the ``pairs`` argument of ``splinter_record`` and a ``parent``
    field in every city's judgement file each answered "is this a split, and
    of what". ActionSA was named in the first, missing from the second and
    blank in the third, so it was dropped from the entrant record for being a
    split and then sized as an entrant for having no parent — 0.1% against an
    actual 18.12%. This fails if the pieces drift apart again.
    """
    splits = pools.SPLITS
    assert splits, "no splits declared at all"

    # Every declaration carries its evidence: a person, a party, a date.
    for party, split in splits.items():
        assert split.parent, f"{party} is a split of nothing"
        assert len(split.why) > 20, \
            f"{party} has no evidence for being called a split: {split.why!r}"
        if split.measured_from is not None:
            for year in split.measured_from:
                assert year in cityconfig.CALENDAR, \
                    f"{party} is measured across {year}, not in the calendar"

    # The classifier is the only route, and it agrees with the declaration.
    for party, split in splits.items():
        parent, why = pools.classify_arrival(party)
        assert parent == split.parent, \
            f"classify_arrival says {party} splits from {parent}, not {split.parent}"
        assert why == split.why
    assert pools.classify_arrival("A_PARTY_NOBODY_HAS_HEARD_OF") == (
        None, "no lineage on record: arrived from nothing")
    assert pools.classify_arrival("EFF", "SOMEONE_ELSE")[0] == "SOMEONE_ELSE", \
        "a city's judgement file must be able to override the default lineage"

    # The two records derive from it rather than restating it.
    city = _city()
    measured = {p for p, s in splits.items() if s.measured_from}
    assert measured, "no split has a pair to measure its fraction across"
    assert len(pools.splinter_record(city)) <= len(measured), \
        "splinter_record measured more splits than are declared"
    transitions = pools.lge_transitions(before=TARGET)
    kept = pools.entrant_record(transitions)
    everything = pools.entrant_record(transitions, exclude=frozenset())
    assert kept, "no entrant record at all"
    assert len(kept) < len(everything), \
        "excluding the declared splits removed nothing from the entrant record"
    # The point of excluding them: the top of the record was the EFF, and
    # every shell party contesting widely was being sized by it.
    assert max(s for s, _ in kept) < max(s for s, _ in everything), \
        ("the biggest 'arrival' on record is the same with the splits removed, "
         "so the record is still describing a split")


def test_a_vote_located_bloc_is_carved_out_of_its_parent_not_added_on_top():
    """Its members are already counted in the parent pool, so a ward's
    composition must still sum to 1 and the parent must shrink by exactly what
    the bloc took. Adding a fifth column on top would invent voters, inflate
    the electorate and quietly break the vote margins the fit is constrained
    by — the same failure the retired "Other" pool caused."""
    city = _city()
    plain = pools.pool_counts(city, FIT_YEAR, _cfg())
    split = pools.pool_counts(city, FIT_YEAR, _cfg(), split_bloc=BLOC)
    assert len(split.categories) == len(plain.categories) + 1
    assert split.categories[-1] == "IFP-located"

    for level in ("people", "voting_age", "registered", "voted"):
        before = getattr(plain, level)
        after = getattr(split, level)
        assert abs(after.sum() - before.sum()) < 1.0, \
            f"{level}: the split changed the electorate by " \
            f"{after.sum() - before.sum():,.0f}"
        rows = split.composition(level).sum(axis=1)
        assert np.allclose(rows[rows > 0], 1.0, atol=1e-9), \
            f"{level}: a ward's composition no longer sums to 1"

    # The carve itself is exact, but every level is then re-fitted across the
    # new set of pools, so the other pools move a little as the least-squares
    # answer shifts. What must hold is that the bloc's voters come out of its
    # PARENT: adding a column on top instead would leave the parent untouched.
    cats = list(plain.categories)
    g = cats.index("Black African")
    lost = plain.voted[:, g].sum() - split.voted[:, g].sum()
    gained = split.voted[:, -1].sum()
    assert lost > 0.9 * gained, \
        f"the bloc holds {gained:,.0f} voters but its parent only gave up " \
        f"{lost:,.0f}; it is not being carved out of the parent"
    for i, name in enumerate(cats):
        if i == g:
            continue
        moved = abs(split.voted[:, i].sum() - plain.voted[:, i].sum())
        assert moved < 0.05 * plain.voted[:, i].sum(), \
            f"{name} moved {moved:,.0f} voters ({moved / plain.voted[:, i].sum():.1%}) " \
            f"when a bloc was carved out of {cats[g]}"


def test_the_bloc_is_located_only_by_elections_before_the_target():
    """The bloc is defined by a party's own past geography, so a run that read
    the target's result would be locating it with the answer. Watched at the
    file, not asserted from the loop's own condition."""
    city = _city()
    for year in ("2016", "2021"):
        with election_files_read() as reads:
            located, prov = pools.vote_located_bloc(city, year)
        assert located, f"no bloc located before {year}"
        late = sorted({(y, k) for y, k, _ in reads if int(y) >= int(year)})
        assert not late, f"the bloc for {year} was located using {late}"
        assert all(int(y) < int(year) for y in prov["elections"]), \
            f"provenance claims {prov['elections']} for target {year}"


def test_the_bloc_identifies_the_party_that_located_it():
    """The justification, as a property rather than a number: if the indicator
    party's rate in its own bloc is not higher than in every census pool, the
    column is not finding a constituency and should not be carried.

    Caught nothing yet — it exists because the alternative to this test is
    keeping a fifth pool on the strength of a story. With the census pools
    alone the IFP fits at r2 0.082, which is no fit at all."""
    fits, ctx = pools.fit_city(_city(), FIT_YEAR, _cfg(), split_bloc=BLOC)
    cats = list(ctx["categories"])
    assert cats[-1] == "IFP-located"
    ifp = fits.get("IFP")
    if ifp is None:
        skip("the IFP did not contest the fitting election")
    inside = ifp.rates[-1]
    outside = ifp.rates[:-1].max()
    assert inside > outside, (
        f"the IFP wins {inside:.3f} of its own bloc and {outside:.3f} of the "
        f"best census pool; the bloc is not locating it")


def test_the_reader_simulation_spec_is_not_what_the_forecast_reads():
    """The vote-located bloc is for the reader simulation and not for the
    published forecast: its location is measured, its size is a judgement.

    Separation by FILENAME rather than by a flag inside one spec, because an
    un-namespaced write has reached a live forecast in this repository before
    (a Tshwane run overwriting Johannesburg's fold parameters). A flag can be
    read wrongly; a path the forecast never opens cannot.
    """
    source = (ROOT / "src" / "montecarlo.py").read_text()
    assert 'f"pools_{target.year}.json"' in source, \
        "the model no longer loads the spec by that name; this test is stale"
    assert "_simulation" not in source, \
        ("montecarlo mentions the simulation spec. The forecast must not be "
         "able to load it by any path.")

    plain = _spec(TARGET)
    assert "simulation_only" not in plain, \
        "the published spec is carrying the simulation marker"
    sim = pools.emit_pools(_city(), cityconfig.Target(city=_city(), year=TARGET),
                           _cfg(), split_bloc=pools.SIMULATION_BLOC)
    assert sim.get("simulation_only"), \
        "a spec with a vote-located bloc does not declare itself"
    assert len(sim["pools"]) == len(plain["pools"]) + 1, \
        (f"the simulation spec has {len(sim['pools'])} pools and the published "
         f"one {len(plain['pools'])}; the bloc is not being added")
    assert set(plain["pools"]) < set(sim["pools"]), \
        "the simulation spec is not a superset of the published pools"


def test_a_splinter_is_never_sized_on_a_split_that_had_not_happened_yet():
    """``splinter_record``'s three pairs had their years hardcoded, and the
    caller passed no target, so every run measured the MK split of 2024 —
    including a backtest at 2016, sizing its splinters on an event eight years
    in its own future. ``backtest.FITTED_ON`` carried a "splinter" key
    announcing this rather than a cutoff preventing it."""
    city = _city()
    full = pools.splinter_record(city)
    assert len(full) >= 2, \
        f"only {len(full)} splits on record; this test's premise has changed"
    for year in ("2011", "2016", "2021"):
        with election_files_read() as reads:
            record = pools.splinter_record(city, year)
        late = sorted({(y, kind) for y, kind, _ in reads if int(y) >= int(year)})
        assert not late, \
            f"the splinter record for {year} read {late}"
        assert len(record) < len(full) or year == "2021", \
            (f"target {year} kept all {len(full)} splits; the cutoff is not "
             f"being applied")


@contextmanager
def _votes_erased():
    """Every ``Party_Votes`` reads 0 inside the block; the rows stay.

    The one honest way to ask "does this read the result?". Anything that
    counts votes collapses to nothing; anything that counts ballot lines is
    untouched. No reimplementation of the rule in the test, so nothing can
    drift apart from what production runs.
    """
    import csv

    import ingest_lge
    real_reader, real_muni = csv.DictReader, ingest_lge.read_municipality

    def blind_reader(*args, **kwargs):
        for row in real_reader(*args, **kwargs):
            if "Party_Votes" in row:
                row["Party_Votes"] = "0"
            yield row

    def blind_muni(*args, **kwargs):
        rows = real_muni(*args, **kwargs)
        for row in rows:
            if "Party_Votes" in row:
                row["Party_Votes"] = "0"
        return rows

    csv.DictReader = blind_reader
    ingest_lge.read_municipality = blind_muni
    try:
        yield
    finally:
        csv.DictReader = real_reader
        ingest_lge.read_municipality = real_muni


def test_contestation_counts_the_ballot_and_not_the_votes():
    """How much of the city a party contests is a NOMINATION fact, published
    when lists close and available to a forecaster weeks before polling day.
    Both readers took it from the target's result file and counted only the
    wards where the party WON votes, which is the outcome the forecast is
    being scored against. It reaches the drawer as a multiplier on the
    ward/PR ratio and the record as an arrival's size, so it is not a footnote.

    Royal Loyal Progress stood in all 135 Johannesburg wards in 2021 and
    scored in 79: the old rule called a full slate 59% of a slate.
    """
    city = _city()
    target = cityconfig.Target(city=city, year=FIT_YEAR)

    measured = levels.contestation(target, city)
    reach = pools._ward_reach(city.code, FIT_YEAR)
    assert measured and reach, \
        "nothing measured; this test cannot say anything"

    with _votes_erased():
        blind = levels.contestation(target, city)
        blind_reach = pools._ward_reach(city.code, FIT_YEAR)

    assert blind == measured, (
        "contestation changed when every vote was erased, so it is reading "
        "the result: "
        + str(sorted(p for p in set(blind) | set(measured)
                     if blind.get(p) != measured.get(p))[:6]))
    assert blind_reach == reach, (
        "ward reach changed when every vote was erased, so it is reading the "
        "result: "
        + str(sorted(p for p in set(blind_reach) | set(reach)
                     if blind_reach.get(p) != reach.get(p))[:6]))


def test_every_constant_the_model_falls_back_to_says_when_it_was_fitted():
    """Each hand-typed constant a run can fall back to must declare which
    elections it read, and each declaration must name a constant a run can
    actually reach.

    Both halves failed at once. ``theta_mode`` was dropped from ``FITTED_ON``
    on the grounds that levels.py measures θ instead — true for the parties
    the record covers, and target 2021 still took ActionSA's 1.50 from it,
    unnamed. In the other direction ``FITTED_ON`` carried "splinter", which is
    not a constant at all and which no scenario could ever declare clean, so
    2011 and 2016 were reported in-sample forever on account of it.
    """
    import re

    import backtest as B
    source = (ROOT / "src" / "montecarlo.py").read_text()
    noted = set(re.findall(r'note_constant\(\s*scenario,\s*"([^"]+)"', source))
    assert noted, "no note_constant calls found; the accounting has moved"
    undeclared = sorted(noted - set(B.FITTED_ON))
    assert not undeclared, (
        f"the model falls back to {undeclared} and FITTED_ON does not say "
        f"which elections they read, so a backtest reports itself clean while "
        f"using them")
    phantom = sorted(set(B.FITTED_ON) - noted)
    assert not phantom, (
        f"FITTED_ON declares {phantom}, which no run records reading. A key "
        f"nothing can read is a permanent in-sample verdict no scenario can "
        f"clear — either wire it into note_constant or enforce its cutoff in "
        f"code and drop it")


def test_the_in_sample_verdict_is_about_the_run_not_about_the_defaults():
    """A constant nothing read cannot contaminate anything."""
    import backtest as B
    assert B.contaminated("2016", set(), {}) == [], \
        "a run that read no tracked constant was still called in-sample"
    # `plan_bounds`, not `theta_mode`: the latter was this test's example key
    # until 2026-08-19 and no longer exists (§1.52). The mechanism under test is
    # unchanged — a tracked key is reported only for the targets it saw, and
    # only when a run actually read it.
    read = {"plan_bounds": ["ASA"]}
    assert B.contaminated("2021", set(), read) == ["plan_bounds"], \
        "a constant the run did read was not reported"
    assert B.contaminated("2026", set(), read) == [], \
        "plan_bounds was reported against a target it predates"


def test_the_entrant_relabel_sums_and_does_not_overwrite():
    """Caught: a dict comprehension keyed on the rename kept the LAST colliding
    value, and ENTRANT sorts last, so it deleted the model's own forecast for
    the named party. With ActionSA declared the model produced a median of 43
    against an actual 44 and the harness scored it 0."""
    draws = [{"ASA": 40, "ENTRANT": 3}, {"ASA": 44, "ENTRANT": 0}]
    parties, samples, truth = S.seat_matrix(draws, {"ASA": 44},
                                            entrant_actual="ASA")
    column = samples[:, parties.index("ASA")]
    assert list(column) == [43.0, 44.0], \
        f"ASA column is {list(column)}; expected the sum, not the last key"


def test_calibration_is_not_measured_on_parties_that_won_nothing():
    """A party with truth 0 and a forecast near 0 is an interval [0,0]
    containing 0 — a free hit at every level, and a near-uniform PIT value.
    36 of 54 columns at 2021 were exactly that, and the verdict inverted."""
    rng = np.random.default_rng(0)
    draws = []
    for _ in range(200):
        row = {"REAL": int(rng.integers(0, 20))}
        for i in range(30):                      # noise parties, truth 0
            row[f"NOISE{i}"] = int(rng.random() < 0.15)
        draws.append(row)
    result = S.score_seats(draws, {"REAL": 40})   # badly missed
    assert result["n_scored_calibration"] == 1, \
        f"calibration scored over {result['n_scored_calibration']} columns"
    headline = {r["level"]: r["empirical"] for r in result["coverage"]}
    inflated = {r["level"]: r["empirical"] for r in result["coverage_all"]}
    assert headline[0.9] < inflated[0.9], \
        ("scoring the noise columns did not inflate coverage; this test's "
         "premise has changed")


def test_a_forecast_that_is_right_is_not_scored_as_a_miss():
    """The end-to-end property the entrant bug violated."""
    draws = [{"ENTRANT": 44}] * 100
    result = S.score_seats(draws, {"ASA": 44}, entrant_actual="ASA")
    assert result["crps"]["total"] < 1.0, \
        f"a correct forecast scored CRPS {result['crps']['total']:.2f}"


# --------------------------------------------------------------------------
# 6. the whole chain
# --------------------------------------------------------------------------

def test_the_forecast_runs_and_fills_the_council():
    """Every draw allocates exactly the council's seats, no more, no fewer."""
    city = _city()
    target = cityconfig.use_target(TARGET)
    scenario = mc.load_scenario(_Args(draws=60))
    run = mc.run_model(target, scenario, verbose=False)
    assert run.seat_draws, "no draws"
    sizes = {sum(d.values()) for d in run.seat_draws}
    council = {int(c) for c in run.council_sizes}
    assert sizes <= council | {target.council}, \
        f"draws allocate {sorted(sizes)} seats; council is {target.council}"


def test_the_model_is_reproducible_from_its_seed():
    """Without this, no golden test and no published number means anything."""
    city = _city()
    target = cityconfig.use_target(TARGET)
    first = mc.run_model(target, mc.load_scenario(_Args(draws=30)), verbose=False)
    second = mc.run_model(target, mc.load_scenario(_Args(draws=30)), verbose=False)
    assert first.seat_draws == second.seat_draws, \
        "two runs with the same seed disagree"


def test_the_model_refuses_to_run_without_a_pool_spec():
    """There is no second engine. A missing spec must be an error, not a quiet
    substitution — this repo has twice shipped a different model by accident."""
    city = _city()
    target = cityconfig.use_target(TARGET)
    scenario = mc.load_scenario(_Args(draws=10))
    scenario["pools"] = {}
    moved = city.processed / f"pools_{TARGET}.json"
    if not moved.exists():
        skip("no spec on disk to hide")
    backup = moved.with_suffix(".json.testbak")
    moved.rename(backup)
    try:
        mc.run_model(target, scenario, verbose=False)
    except SystemExit:
        return
    finally:
        backup.rename(moved)       # always restore, even on assertion failure
    raise AssertionError("run_model produced a forecast with no pool spec")


def test_applying_a_city_does_not_inherit_the_previous_city_s_judgements():
    """`apply_city` must start from the module's defaults, not from whatever ran.

    It used to write each city's scalars over `DEFAULTS` and never restore them,
    so in a nine-city-year loop a city inherited whatever the cities before it
    happened to declare. Only two of the eight metros declare scalars at all, so
    the other six were running on Johannesburg's or Tshwane's values — and WHICH
    ONE depended on the order the loop happened to visit them in.

    Exactly one key differed at the time (`pa_contestation_uplift`, since
    deleted) and it was consumed at no backtested target, so no score moved.
    That was luck. This test is what makes it not luck, and it is also what
    makes a parallel `compare_history` run equal a serial one: with the reset,
    a fresh process and a re-used one see the same configuration.
    """
    pristine = dict(mc.DEFAULTS)

    tsh = cityconfig.load("tshwane")
    mc.apply_city(tsh)
    after_tshwane = dict(mc.DEFAULTS)

    # A city that declares no scalars of its own must land back on the defaults.
    plain = cityconfig.load("capetown")
    mc.apply_city(plain)
    leaked = {k: (after_tshwane.get(k), mc.DEFAULTS.get(k))
              for k in mc.DEFAULTS
              if mc.DEFAULTS.get(k) != pristine.get(k)}
    assert not leaked, (
        "apply_city left another city's judgements in DEFAULTS: " + repr(leaked))

    # And applying the same city twice is idempotent.
    mc.apply_city(tsh)
    once = dict(mc.DEFAULTS)
    mc.apply_city(tsh)
    assert dict(mc.DEFAULTS) == once, "apply_city is not idempotent"

    mc.apply_city(cityconfig.load(CITY))     # leave the module where we found it


def test_every_emitted_pool_spec_carries_a_current_artefact_key():
    """The committed artefacts must match the code that is committed with them.

    `pools_*.json` is precomputed, so `pools.py` can change without it changing,
    and a measurement taken across that gap is not a measurement. That has
    already cost twice: a lever sweep returned different answers on two
    identical runs, and two `EXPECTED_INERT` reasons written from those unstable
    readings had to be retracted. `CLAUDE.md`'s "one writer" rule is the human
    compensation; this is the check.

    **If this fails, the fix is to re-emit, not to loosen the test** — and to
    check what re-emitting moves, because that is exactly the question the
    failure is asking.
    """
    stale = []
    specs = sorted(ROOT.glob("data/processed/**/pools_*.json"))
    # ⛔ (1) IT LOOKED. `data/**` is gitignored, so on a fresh clone this glob
    # is EMPTY and the test passed while checking nothing — the headline
    # staleness guard, vacuous. Two-sided against a computed denominator so it
    # cannot go stale as cities are added.
    cities = len(list((ROOT / "cities").glob("*.toml")))
    assert cities <= len(specs) <= 4 * cities + 4, (
        f"found {len(specs)} emitted specs against {cities} cities. Zero means "
        f"this scan is examining nothing and its emptiness is worth nothing; a "
        f"wild count means the glob is picking up something it should not.")
    for path in specs:
        spec = json.loads(path.read_text())
        slug = path.parent.name if path.parent.name != "processed" else "joburg"
        city = cityconfig.load(slug)
        year = spec.get("target")
        why = pools.stale_reason(spec, city, _Target(year))
        if why:
            stale.append(f"{path.relative_to(ROOT)}: {why}")
    assert not stale, (
        "these emitted pool specs no longer match the code that reads them:\n  "
        + "\n  ".join(stale) +
        "\nRe-emit with `python src/pools.py --city <city> --target <year> "
        "--emit`, and say in the commit what re-emitting changed besides the "
        "artefact key.")


def test_every_field_of_the_artefact_key_is_actually_checked():
    """A field recorded and never compared is a guard that cannot fire.

    `stale_reason` used to compare a **typed tuple** `("pools_sha",
    "config_sha")` and then index a **typed dict** for the human label. Adding a
    field to `artefact_key` and not to both left it recorded and unchecked;
    adding it to only one raised `KeyError` on a real spec. A number typed in
    two places, and this is the test that makes the third place impossible.

    ⛔ ENUMERATES rather than lists (§1.173). It asks `artefact_key` what fields
    exist and requires each non-identity one to be NAMED in the refusal, so a
    field added tomorrow is covered without editing this test.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    now = pools.artefact_key(city, target)

    # The SAME set the code uses, imported rather than retyped — a set typed
    # in two places is exactly what `stale_reason` was fixed for.
    checkable = sorted(set(now) - pools._IDENTITY_FIELDS)
    # (1) IT LOOKED, two-sided against a computed denominator.
    assert 2 <= len(checkable) <= 8, (
        f"artefact_key has {len(checkable)} comparable fields ({checkable}); "
        f"one or none means this scan is examining almost nothing.")

    for field in checkable:
        doctored = dict(now)
        doctored[field] = "0000000000000000"
        why = pools.stale_reason({"artefact_key": doctored}, city, target)
        # (2) IT CAN SEE, on a CONSTRUCTED key rather than the tree's state.
        assert why is not None, (
            f"perturbing {field} produced no staleness reason: it is recorded "
            f"in the key and never compared, so nothing would notice it moving")
        assert field in why, (
            f"{field} moved and the reason does not name it: {why!r}. The "
            f"useful half of a staleness report is WHICH thing moved.")


def test_the_judgement_file_is_keyed_by_payload_and_not_by_prose():
    """A staleness warning that fires on a comment is one nobody reads.

    `judgements/<slug>-<year>.toml` declares each party's `parent`,
    `baseline_share` and pool `weights` — it sets seeds — and until 2026-09-02
    it was **in no hash anywhere**, so hand-editing it changed what the model
    computes while every spec reported itself current. That is the hole entry 3
    would have shipped a nomination list through on 16 September.

    Hashing its BYTES would have been the other failure: 26 specs marked stale
    on every prose edit, and a guard that cries wolf is switched off. So the
    hash is over the PARSED payload, following `theta_residual`'s memo key,
    which freezes the table and not the switch.

    Both directions are asserted, on a constructed file — the tree's own
    judgement files are never touched.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    body = '[party.EXAMPLE]\nbaseline_share = 0.05\nparent = "ANC"\n'

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "joburg-2026.toml"
        original = pools.lineage_path
        try:
            pools.lineage_path = lambda c, t: path

            path.write_text(body)
            base = pools.artefact_key(city, target)["judgements_sha"]

            path.write_text(body + "\n# prose, and nothing else\n")
            after_comment = pools.artefact_key(city, target)["judgements_sha"]
            assert after_comment == base, (
                "a comment-only edit moved `judgements_sha`. Every spec would "
                "report stale on a prose change, and a warning that fires on "
                "prose is one everybody learns to ignore — which is the "
                "failure `_code_sha`'s docstring exists to prevent.")

            path.write_text(body.replace('parent = "ANC"', 'parent = "DA"'))
            after_payload = pools.artefact_key(city, target)["judgements_sha"]
            assert after_payload != base, (
                "changing a declared PARENT did not move `judgements_sha`. "
                "That field selects between two different sizing machineries "
                "(`classify_arrival`), and getting it wrong once produced 0.1% "
                "against an actual 18.12%.")
        finally:
            pools.lineage_path = original


def test_the_config_hash_covers_the_whole_config_directory():
    """The population is `config/*.toml`, not one named file.

    `config_sha` hashed a single path. `config/` held exactly one file, so the
    claim ("what this spec was built from") and the scan coincided **by
    accident** — and a second config file would have been consumed by the model
    and invisible to staleness. §1.173.

    ⚠️ RUNS IN A TEMPORARY DIRECTORY, and the first version of this test did
    not. It wrote `config/_constructed_by_a_test.toml` into the live tree —
    mutating a **hashed shared input** while CLAUDE.md §3 forbids moving the
    artefacts' baseline during a measurement, so a concurrent `compare_history`
    worker would have seen `config_sha` move under it. It also leaked the file
    if the test was killed. `_config_sha` takes a path, so there is no reason
    to touch the real directory.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        named = root / "dimensions.toml"
        named.write_text("# constructed\nx = 1\n")
        before = pools._config_sha(named)

        (root / "second.toml").write_text("# a second config file\ny = 2\n")
        after = pools._config_sha(named)
        assert after != before, (
            "a new config/*.toml did not move `config_sha`. Its content would "
            "be read by the model and reported as current by every spec.")

        (root / "second.toml").unlink()
        assert pools._config_sha(named) == before, (
            "removing the second file did not restore the hash, so the scan is "
            "not a function of the directory's contents")


# A genuine entrant legitimately slugs, so `[roster]` requires it to carry a
# `[party.X]` table as well — which is what makes a misspelt EXISTING party
# detectable. Declaring one is therefore a two-line edit, and the tests do it
# the way the refusal instructs.
_PLACE_NEWPARTY = '[party.NEWPARTY]\nsupport = 0.05\n'


def test_a_roster_has_three_states_and_only_two_may_delete_a_party():
    """Drop what was deliberately excluded, never what was merely absent.

    `roster_is_real` was a boolean and it conflated "we know the ballot" with
    "we may delete parties from the pools". The second deletes 2.4-2.9% of a
    city's vote across 16-20 parties when it fires wrongly (§1.175), and on
    16 September 2026 it would fire on a half-typed nomination list.

      published  absence is deliberate      -> may drop
      declared   absence is ambiguous       -> may drop ONLY if complete = true
      projected  absence is ignorance       -> may drop only what a measured
                                              floor deliberately excluded

    ⛔ THIS ASSERTS `resolve_roster`, NOT `declared_roster`. The first version
    of this test checked only the PARSER, and the seam shipped broken: the
    projected branch sat one indent level out, so it ran in the declared case
    too and rebuilt `roster` from the baseline **two lines after** reading the
    declared list. The parser was perfect and the hand-declared nomination list
    reached nothing. The population a roster test must cover is the resolution,
    which is why it is a function and not eighty inline lines.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    original = pools.lineage_path

    # Constructed, not observed. NEWPARTY is in neither, which is the whole
    # case the seam exists for: a genuine entrant is invisible to a projection.
    composition = {"ANC": [0.9, 0.1], "DA": [0.2, 0.8], "SMALLFRY": [0.5, 0.5]}
    baseline = {"ANC": 0.40, "DA": 0.25, "SMALLFRY": 0.0004}

    def _resolve(body, tgt=target, year="2021"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / f"joburg-{tgt.year}.toml"
            path.write_text(body)
            try:
                pools.lineage_path = lambda c, t: path
                return pools.resolve_roster(
                    city, tgt, year, dict(composition), dict(baseline))
            finally:
                pools.lineage_path = original

    # (1) PROJECTED — no [roster] at all.
    roster, source, deliberate, _ = _resolve(
        '[party.MK]\nbaseline_share = 0.12\nparent = "ANC"\n')
    assert source == "projected", source
    assert "NEWPARTY" not in roster, (
        "a projection invented a party it has no evidence for")
    assert "ANC" in roster and "DA" in roster
    assert deliberate <= {"SMALLFRY"}, (
        f"a projected roster deleted {deliberate - {'SMALLFRY'}} from the "
        f"pools. Only what a MEASURED floor excluded may go; everything else "
        f"absent from a guess is ignorance, and that is how ActionSA was lost.")
    # A [party.X] entry does not put MK on the ballot — [roster] does.
    assert "MK" not in roster, (
        "a [party.X] entry became a ballot claim. `write_lineage_template` "
        "auto-generates one per no_vector party, so a stale template would "
        "silently override the measured floors §K1/§K2.")

    # (2) DECLARED, incomplete — ADDS and removes nothing.
    roster, source, deliberate, _ = _resolve(
        '[roster]\nparties = ["ANC", "NEWPARTY"]\n' + _PLACE_NEWPARTY)
    assert source == "declared", source
    assert "NEWPARTY" in roster, (
        "THE BLOCKING BUG. A declared nomination list was read and then "
        "discarded — the projected branch rebuilt `roster` from the baseline "
        "and the entrant vanished. This is the assertion that catches it.")
    assert deliberate == set(), (
        f"an INCOMPLETE declared roster deleted {deliberate}. A partial paste "
        f"on a deadline must add parties and delete none: `complete` defaults "
        f"to false and that is the whole safety property.")

    # (3) DECLARED, complete = true — the deletion is licensed, and only now.
    roster, source, deliberate, _ = _resolve(
        '[roster]\ncomplete = true\nconfirm_drop = true\n'
        'parties = ["ANC", "NEWPARTY"]\n' + _PLACE_NEWPARTY)
    assert source == "declared", source
    assert "NEWPARTY" in roster
    assert deliberate == {"DA", "SMALLFRY"}, (
        f"a COMPLETE declared roster dropped {deliberate}, expected "
        f"{{'DA', 'SMALLFRY'}} — the composition members it does not name")

    # (4) PUBLISHED beats a declared list. The target has been held, so the
    #     result file is the ballot and a hand-written guess cannot override it.
    held = cityconfig.Target(city=city, year="2021")
    published = pools.contesting_parties(city, "2021")
    assert len(published) > 20, (
        f"IT LOOKED: contesting_parties(joburg, 2021) returned {len(published)} "
        f"parties. With an empty result the published arm is untested and rows "
        f"1-3 are all this proves.")
    roster, source, deliberate, _ = _resolve(
        '[roster]\ncomplete = true\nparties = ["ANC"]\n', held, "2016")
    assert source == "published", (
        f"a declared [roster] overrode a HELD election ({source}). The result "
        f"file is what happened; a judgement call cannot outrank it.")
    assert roster == published
    assert deliberate == {"SMALLFRY"}, (
        f"the published arm dropped {deliberate}. The DA contested 2021 and "
        f"the result file says so, so it survives a declared list that omits "
        f"it — which is the point: a held election outranks a judgement call. "
        f"Only SMALLFRY, absent from the real ballot, is deliberate.")


def test_a_declared_roster_reaches_the_emitted_spec():
    """The end-to-end anchor: one emit, and the declared party must arrive.

    ⛔ THIS IS THE EXPENSIVE TEST AND IT IS DELIBERATE. It costs a full city
    fit (~100s) and everything above it is milliseconds, because everything
    above it exercises `resolve_roster` in isolation. Isolation is exactly what
    let the seam ship broken once: the resolution was correct in the branch
    that never ran, and no test crossed from the resolution to `seeds`.

    So this asserts the one thing a unit test cannot — that the wire is
    connected — on the STRUCTURE and not the values. The seed's size is
    `arrival_rules`' business and R4 will move it; that this party has a seed
    at all, and a place in every pool, is this seam's business.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.use_target("2026")
    original = pools.lineage_path
    body = pools.lineage_path(city, target).read_text()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "joburg-2026.toml"
        path.write_text('[roster]\nparties = ["ANC", "DA", "EFF", "NEWPARTY"]\n'
                        + _PLACE_NEWPARTY + '\n' + body)
        try:
            pools.lineage_path = lambda c, t: path
            spec = pools.emit_pools(city, target, pools.load_config())
        finally:
            pools.lineage_path = original

    assert "roster declared" in spec["provenance"], spec["provenance"]
    assert "NEWPARTY" in spec["seeds"], (
        "a party declared under [roster] emitted no seed. It is in no pool "
        "vector and in no baseline, so with no seed it is not forecast at all "
        "— which is the ActionSA failure the seam exists to prevent.")
    placed = [n for n, pl in spec["pools"].items() if "NEWPARTY" in pl["members"]]
    assert len(placed) == len(spec["pools"]), (
        f"NEWPARTY reached {len(placed)} of {len(spec['pools'])} pools. With "
        f"no measured vector it takes an even share of every pool — a "
        f"placeholder, and meant to look like one — so absence from a pool "
        f"means the declaration did not reach the composition.")
    # AND the incomplete list deleted nobody: ANC/DA/EFF are named, everyone
    # else in the composition must still be there.
    members = {p for pl in spec["pools"].values() for p in pl["members"]}
    assert len(members) > 20, (
        f"the composition fell to {len(members)} parties. An INCOMPLETE "
        f"declared roster must add and never delete.")


def test_a_party_table_entry_does_not_put_a_party_on_the_ballot():
    """`[roster]` decides who stands; `[party.X]` decides how they are placed.

    A first version of the seam added every `[party.X]` entry to the roster.
    `write_lineage_template` auto-generates one entry per `no_vector` party, so
    the file already lists parties the measured floors (§K1, §K2) exclude, and
    a stale template would have silently overridden measured evidence.

    The BEHAVIOUR is asserted next door, on a constructed file, by
    `test_a_roster_has_three_states_...` row (1). What this asserts is that the
    hazard is LIVE in the tree rather than hypothetical: the real judgement
    file really does carry entries the §K1 floor really does exclude. Without
    that, the constructed test guards an interaction nobody would ever meet.

    A previous version of this test asserted a string was absent from
    `inspect.getsource(pools.emit_pools)`. That proved nothing about what the
    code does, and it broke the moment the block moved to `resolve_roster` —
    which is the correct fate of a test that scans source instead of running it.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    lineage = pools.load_lineage(city, target)
    assert len(lineage) >= 5, (
        f"judgements/joburg-2026.toml carries {len(lineage)} [party.*] entries; "
        f"with too few, this proves nothing about the interaction it pins")

    # The §K1 baseline, read the way `emit_pools` reads it — no fit needed.
    path = city.path("raw", "elections",
                     cityconfig.CALENDAR[target.previous_npe].results)
    counts = collections.defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            counts[parties.canonical(row["sPartyName"])] += int(
                float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    assert total > 0, f"{path} parsed to zero votes"
    baseline = {q: c / total for q, c in counts.items()}

    below = {q for q in lineage if baseline.get(q, 0.0) < pools.NATIONAL_ONLY_FLOOR}
    assert below, (
        f"no [party.*] entry in judgements/joburg-2026.toml sits below the "
        f"§K1 floor of {pools.NATIONAL_ONLY_FLOOR:.1%}, so promoting party "
        f"entries to the roster would currently override nothing and the "
        f"constructed guard next door defends an interaction that cannot "
        f"arise. Re-check that the floor and the template still disagree.")
    assert len(below) < len(lineage), (
        f"ALL {len(lineage)} party entries sit below the floor. A one-sided "
        f"count that can only grow is not a measurement; if the template has "
        f"stopped emitting anything the floor keeps, this test is scanning the "
        f"wrong population.")


def test_the_emit_dependency_set_matches_what_pools_actually_imports():
    """`deps_sha` names four modules. That claim must hold in BOTH directions.

    `pools_sha` hashes one file while `_code_sha`'s docstring claims any change
    to what the code computes moves it — false of the first-party modules the
    emit leans on. `deps_sha` covers them, and this asserts the named set is
    neither short (a dependency nobody hashes) nor long (a module hashed that
    the emit does not read, which would cry wolf).

    `montecarlo` is deliberately absent and that absence is asserted, with the
    reason: it carries every forecast lever and changes on most working days,
    so hashing it would mark all 26 specs stale continuously.
    """
    source = (ROOT / "src" / "pools.py").read_text()
    tree = ast.parse(source)
    first_party = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            first_party.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            first_party.add(node.module.split(".")[0])
    local = {m for m in first_party if (ROOT / "src" / f"{m}.py").exists()}

    named = set(pools._EMIT_DEPENDENCIES)
    # (1) IT LOOKED, two-sided against a computed denominator.
    assert 3 <= len(named) <= len(local), (
        f"`_EMIT_DEPENDENCIES` names {len(named)} of {len(local)} first-party "
        f"modules pools.py imports ({sorted(local)}); one or none means this "
        f"is examining almost nothing.")
    unknown = named - local
    assert not unknown, (
        f"`_EMIT_DEPENDENCIES` names {sorted(unknown)}, which `pools.py` does "
        f"not import — hashing a module the emit never reads cries wolf.")
    assert "montecarlo" not in named, (
        "montecarlo is excluded deliberately: it carries every forecast lever "
        "and changes on most working days, so hashing it would mark all 26 "
        "specs stale continuously. If that judgement is revisited, the residual "
        "risk recorded beside `_EMIT_DEPENDENCIES` must be revisited with it.")
    missing = local - named - {"montecarlo"}
    assert not missing, (
        f"pools.py imports {sorted(missing)} and `deps_sha` does not hash "
        f"them, so a change to what they compute leaves every spec reporting "
        f"itself current. Either hash them or record why not.")


def test_a_pool_spec_from_different_code_is_reported_as_stale():
    """The guard has to FIRE, not merely exist.

    A staleness check that cannot detect staleness is the pool ceiling all over
    again: a guard whose silence gets read as evidence. This perturbs the key
    the way a real code change would and requires a reason to come back.
    """
    city = cityconfig.load(CITY)
    good = pools.artefact_key(city, _Target("2021"))
    assert pools.stale_reason({"artefact_key": good}, city, _Target("2021")) is None

    moved = dict(good, pools_sha="0" * 16)
    why = pools.stale_reason({"artefact_key": moved}, city, _Target("2021"))
    assert why and "pools.py" in why, f"a changed code hash was not reported: {why!r}"

    wrong_city = dict(good, city="tshwane")
    why = pools.stale_reason({"artefact_key": wrong_city}, city, _Target("2021"))
    assert why and "tshwane" in why, f"a wrong-city spec was not reported: {why!r}"

    assert pools.stale_reason({}, city, _Target("2021")), \
        "a spec with no key at all must not pass silently"


class _Target:
    """The two attributes `pools.artefact_key` reads off a target."""

    def __init__(self, year):
        self.year = year


def test_a_diagnostic_run_does_not_overwrite_the_published_artefacts():
    """A diagnostic that REPLACES the forecast is not a diagnostic either.

    `montecarlo.main` writes three files into the processed directory —
    `ward_winner_probs.csv`, `seat_draws.csv`, `forecast_summary.json` — and
    they are the site's inputs and the published forecast.

    **This happened on 2026-08-28.** `CLAUDE.md` documents
    `python src/montecarlo.py ... --run-dir /tmp/t` as the way to trace a run,
    and two such runs — the second a `--set spine_k=0` sweep at 60 draws —
    replaced the 5,000-draw shipped forecast on disk. `data/**` is gitignored,
    so `git status` was clean and no artefact key noticed;
    `test_the_cartogram_ink_is_proportional_to_seats` went red an hour later,
    reading like a cartogram problem. §1.118.

    `run_model`'s docstring — *"writes nothing unless `run_dir` is given, and
    then it writes only a trace"* — is true OF THE FUNCTION and was read as
    covering the command. This test is about the command.

    **It runs against the REAL processed directory on purpose**, because that
    is the path that broke and a temporary one cannot supply the pool spec and
    turnout the run reads. The three files are snapshotted and restored in a
    `finally`, so a regression fails the test rather than damaging the tree.
    """
    import montecarlo as M
    import cityconfig

    cityconfig.use("joburg")
    processed = cityconfig.use_target("2026").processed
    # ⛔ THE WHOLE DIRECTORY, NEVER A LIST OF NAMES. This test enumerated
    # exactly three filenames until 2026-08-30, and `coalitions.write_outputs`
    # published FOUR more from 64 lines above the guard. Both the guard and this
    # test named the same three, so four files walked past both — every suite
    # run wrote 20-draw coalition CSVs into the real processed directory, and
    # they carried a timestamp newer than the 5,000-draw artefacts they claimed
    # to summarise. A list of names cannot protect a file added later, and
    # `write_outputs` predates the guard it evaded. So the property is stated
    # over the directory: same filenames, same bytes.
    before = {f.name: f.read_bytes() for f in processed.iterdir() if f.is_file()}
    if not before:
        skip(f"no published artefacts in {processed} to protect")
    _created_by_this_run: set[str] = set()

    try:
        with tempfile.TemporaryDirectory() as tmp:
            trace_dir = Path(tmp) / "trace"
            rc = M.main(["--city", "joburg", "--target", "2026",
                         "--draws", "20", "--run-dir", str(trace_dir)])
            assert rc == 0, rc
            assert (trace_dir / "41_guards.json").exists(), (
                "the trace must still be written — the guard is about "
                "PUBLISHING, not about tracing")
        created = {f.name for f in processed.iterdir()
                   if f.is_file()} - set(before)
        _created_by_this_run.update(created)
        assert not created, (
            f"a --run-dir run CREATED {sorted(created)} in {processed}. A "
            f"diagnostic must not publish, and a guard that enumerates "
            f"filenames cannot see a new one — which is exactly how four "
            f"coalition CSVs were published at 20 draws. MODEL-LOG §1.118.")
        for name, blob in before.items():
            assert (processed / name).read_bytes() == blob, (
                f"a --run-dir run rewrote {name}. A diagnostic must not "
                f"publish: `data/**` is gitignored, so this is invisible until "
                f"something downstream breaks. MODEL-LOG §1.118.")
    finally:
        # Restore whatever the run may have written, so a REGRESSION in the
        # guard costs a red test and not a contaminated forecast. Deleting what
        # the run CREATED matters as much as restoring what it overwrote.
        #
        # ⛔ DELETE ONLY WHAT THIS RUN CREATED, NEVER "anything not in the
        # snapshot". `data/processed` is SHARED and gitignored, and an
        # unconditioned sweep here would delete a file some other process wrote
        # between the snapshot and this teardown. That is the failure mode of
        # the entry titled "Gitignored is not unimportant" — a diagnostic
        # destroying a published artefact because nothing warns on an ignored
        # path. The created set is captured inside the `try`, above.
        for name in _created_by_this_run:
            target = processed / name
            if target.is_file():
                target.unlink()
        for name, blob in before.items():
            if (processed / name).read_bytes() != blob:
                (processed / name).write_bytes(blob)


def test_the_trace_is_inert_without_a_run_directory():
    """A diagnostic that changes the forecast is not a diagnostic.

    ``Trace`` is threaded through ``run_model`` and ``blended_centres``, and it
    is only safe to leave there because with no ``run_dir`` it writes nothing
    and returns its argument untouched. If that ever stops being true, every
    number in the repository moves for a reason that has nothing to do with the
    model, and the golden prior would have to be re-recorded to accommodate a
    logging change.
    """
    empty = mc.Trace(None)
    assert not empty, "a trace with no run_dir must be falsey"

    obj = {"ANC": 0.4, "DA": 0.25}
    assert empty.put("anything", obj) is obj, \
        "put() must return its argument, not a copy"
    empty.close()          # must not raise, must not create anything

    # And the wrapping must be transparent where it is actually used.
    scenario = {"level_shrink": 0.35, "level_shrink_scale": 0.04}
    centres = {"ANC": 0.40, "DA": 0.25, "SMALL": 0.01}
    assert mc.compress_levels(centres, scenario) == \
        mc.compress_levels(dict(centres), scenario)


def test_a_trace_records_the_level_chain_without_touching_it(tmp_path=None):
    """The trace must contain the stages, and the run must not notice it.

    The point of the trace is that "why is this party at this number?" is
    answerable by reading a file rather than by adding a print and paying a
    fifty-minute re-run. That is only worth anything if the recorded numbers
    are the ones the model actually used, so this checks the recorded centres
    against the drawn means rather than merely checking the files exist.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "trace"
        target = cityconfig.use_target("2021")
        mc.apply_city(cityconfig.use(CITY))
        scenario = mc.load_scenario(_Args(40))
        run = mc.run_model(target, scenario, verbose=False, run_dir=run_dir)

        for name in ("00_target", "10_theta_prior", "20_spine", "30_centres",
                     "41_guards", "_index"):
            assert (run_dir / f"{name}.json").exists(), f"{name} was not traced"

        centres = json.loads((run_dir / "30_centres.json").read_text())
        before, after = centres["before_shrink"], centres["after_shrink"]
        assert before and after and set(before) == set(after)

        # The shrink's claim, checked on what the RUN recorded rather than on a
        # fixture: the largest party is pulled down, the smallest lifted.
        order = sorted(before, key=lambda p: -before[p])
        big, small = order[0], order[-1]
        if before[big] > 0 and before[small] > 0:
            assert after[big] / before[big] < after[small] / before[small], \
                "the recorded shrink is not monotone in size"

        # And the trace is a record of THIS run, not of a re-derivation.
        assert run.scenario is scenario


def test_the_level_shrink_is_exactly_the_identity_when_it_is_off():
    """Off must mean untouched, not nearly untouched.

    ``level_shrink`` ships at 0.0, so every committed forecast and every golden
    test runs through ``compress_levels``. If the off path returned a
    renormalised copy rather than its input, the whole model would move by a
    rounding error the moment this landed, and the golden prior would have to be
    re-recorded for a change that is supposed to do nothing.
    """
    centres = {"ANC": 0.40, "DA": 0.25, "EFF": 0.10, "TINY": 0.0004, "ZERO": 0.0}
    for scenario in ({"level_shrink": 0.0, "level_shrink_scale": 0.04},
                     {"level_shrink": 0.0, "level_shrink_scale": 0.0},
                     {}):
        out = mc.compress_levels(centres, scenario)
        assert out == centres, f"the off path moved the centres: {scenario}"


def test_the_level_shrink_takes_from_the_big_and_gives_to_the_small():
    """The mechanism's whole claim, as an ordering rather than a number.

    The fault is ranks 1-3 over-forecast and ranks 4-12 under-forecast, so the
    correction must be monotone in size: strictly shrinking the largest party,
    strictly lifting the smallest, preserving the total, and never reordering
    anybody. A form that merely lowered the total would score better on a
    signed statistic while being wrong.
    """
    centres = {"ANC": 0.40, "DA": 0.25, "EFF": 0.10, "SMALL": 0.01,
               "TINY": 0.0004}
    out = mc.compress_levels(centres, {"level_shrink": 0.35,
                                       "level_shrink_scale": 0.04})

    assert abs(sum(out.values()) - sum(centres.values())) < 1e-12, \
        "the shrink must return the mass it takes, not delete it"

    ratio = {p: out[p] / centres[p] for p in centres}
    order = sorted(centres, key=lambda p: -centres[p])
    for big, small in zip(order, order[1:]):
        assert ratio[big] < ratio[small], (
            f"{big} ({centres[big]:.2%}) must be pulled down harder than "
            f"{small} ({centres[small]:.2%}); got {ratio[big]:.4f} vs "
            f"{ratio[small]:.4f}")
    assert ratio[order[0]] < 1.0, "the largest party must lose share"
    assert ratio[order[-1]] > 1.0, "the smallest party must gain share"
    assert [p for p in sorted(out, key=lambda p: -out[p])] == order, \
        "the shrink must not reorder the ballot"


class _Args:
    """The shape ``montecarlo.load_scenario`` expects from argparse."""

    def __init__(self, draws: int):
        self.config = None
        self.set = None
        self.draws = draws
        self.seed = None


def _close(a, b, rel=1e-9):
    """Elementwise near-equality. This harness has no pytest."""
    a, b = list(a), list(b)
    return len(a) == len(b) and all(
        abs(x - y) <= rel * max(1.0, abs(x), abs(y)) for x, y in zip(a, b))


def _arrival_kw():
    """A synthetic arrival record. Constructed, so it cannot expire silently."""
    return dict(
        rates=np.array([[0.30, 0.10], [0.05, 0.40]]),
        universe=["ANC", "DA"],
        categories=["A", "B"],
        record=[(0.010, 0.5), (0.004, 0.4), (0.02, 0.6), (0.001, 0.3),
                (0.05, 0.7), (0.002, 0.45), (0.03, 0.55), (0.007, 0.5)],
        splinter_fractions=[0.10, 0.20, 0.15],
        pool_size=np.array([1000.0, 2000.0]))


def test_a_declared_strength_is_read_and_does_not_narrow_its_own_band():
    """The 16-September path: an owner states how big a new party will be.

    Three defects, all measured 2026-09-03 and all on this one path:

    1. `support` was read ONLY inside `if weights:`. A party announced without
       a ward list — the ordinary case — had its declared size discarded and
       was seeded at the comparator mean instead.
    2. `lo_e`/`hi_e` were bound only in the entrant branch and read by every
       non-split branch. Declaring `weights` raised `UnboundLocalError` when
       the party was the sole newcomer, and inherited the PREVIOUS party's
       quantiles when it was not — so the band depended on alphabetical order.
    3. The band divided the record's quantiles by the ADJUSTED centre, so
       stating a level narrowed the band in proportion to it. ActionSA's x36
       would have produced a 95th percentile at 7.7% of its own mean: the act
       of admitting a guess made the forecast 36x sharper.

    The rule: **the declaration sets the level, the record sets the width.**
    """
    kw = _arrival_kw()
    peers = [s for s, _ in kw["record"]]
    expect_lo = float(np.quantile(peers, pools.ARRIVAL_BAND_LO)) / float(np.mean(peers))
    expect_hi = float(np.quantile(peers, pools.ARRIVAL_BAND_HI)) / float(np.mean(peers))
    assert expect_hi / expect_lo > 3.0, (
        f"IT LOOKED: the constructed record's band spans only "
        f"{expect_hi / expect_lo:.1f}x. Too narrow to show a band collapsing, "
        f"so widen the record before trusting what follows.")

    def rules_for(lineage, others=()):
        r, notes = pools.arrival_rules({"NEWPARTY", *others}, lineage, **kw)
        return r["NEWPARTY"], notes["NEWPARTY"]

    def implied_share(rule):
        """The citywide share a capture vector actually buys.

        ⛔ ASSERT THE NUMBER, NOT THE NOTE. The first version of this test
        checked that the note said "DECLARED 12.00%", and a mutation that
        deleted the line honouring `support` left the note untouched and the
        test green: the prose claimed a declaration the arithmetic ignored.
        `_capture_from_share` puts `share * w_g * electorate / pool_size[g]`
        in each pool, so weighting back by pool size recovers the share.
        """
        size = kw["pool_size"]
        return sum(r * size[g] for g, r in rule["capture"].items()) / size.sum()

    # (1) weights + support, sole newcomer. This raised UnboundLocalError.
    got, why = rules_for({"NEWPARTY": {"weights": [1.0, 0.0], "support": 0.12}})
    assert _close(got["band"], [expect_lo, 1.0, expect_hi]), got["band"]
    assert "DECLARED" in why, why
    assert _close([implied_share(got)], [0.12], rel=1e-6), (
        f"declared 12% with weights, bought {implied_share(got):.4%}")

    # (2) ORDER INDEPENDENCE. `AAAOTHER` sorts first and takes the entrant
    #     branch, which is what used to leave lo_e/hi_e lying around.
    other, _ = rules_for({"NEWPARTY": {"weights": [1.0, 0.0], "support": 0.12}},
                         others=("AAAOTHER",))
    assert _close(other["band"], got["band"]), (
        f"a party's band changed because another party was emitted first: "
        f"{other['band']} vs {got['band']}. The band is a property of the "
        f"arrival record, not of the loop's iteration order.")

    # (3) `support` WITHOUT weights — the case that was silently discarded.
    got3, why3 = rules_for({"NEWPARTY": {"support": 0.12}})
    assert "DECLARED 12.00%" in why3, why3
    assert _close(got3["band"], [expect_lo, 1.0, expect_hi])
    assert _close([implied_share(got3)], [0.12], rel=1e-6), (
        f"a `support` declared WITHOUT `weights` bought "
        f"{implied_share(got3):.4%} of the city, not the 12% stated. It was "
        f"read only inside `if weights:`, so an owner who knew the size but "
        f"not the ward list had their number silently discarded — and the "
        f"note still said DECLARED, which is why this asserts the arithmetic.")
    default_share = implied_share(rules_for({})[0])
    assert abs(implied_share(got3) - default_share) > 0.05, (
        f"the declared share {implied_share(got3):.4%} is indistinguishable "
        f"from the undeclared default {default_share:.4%}, so this test would "
        f"pass whether or not the declaration was honoured")

    # (4) A LEVEL DOES NOT BUY SHARPNESS. x36 is the ActionSA judgement.
    plain, _ = rules_for({})
    loud, _ = rules_for({"NEWPARTY": {"overperform": 36.0}})
    assert _close(loud["band"], plain["band"]), (
        f"a x36 judgement moved the band from {plain['band']} to "
        f"{loud['band']}. Stating that a party is bigger than its comparators "
        f"says nothing about how well we know it, and dividing the record's "
        f"quantiles by the raised centre made the forecast 36x sharper.")
    assert _close([sum(loud["capture"].values())],
                  [36.0 * sum(plain["capture"].values())]), (
        "the multiplier must still move the LEVEL — this test must not pass "
        "by making `overperform` inert.")

    # (5) ⛔ THE GROUP BUDGET MUST NOT RENORMALISE A DECLARATION AWAY.
    #     `arrival_rules` holds the entrant GROUP to the arrival-total record.
    #     That record is a prior over arrivals nobody has sized; a declared
    #     party is not one. Leaving it in the budget put a declared 12.00% out
    #     at 0.3687% -- a factor of 33 -- while the note said "group rescaled
    #     x0.03". `support` was readable by then and still did nothing.
    crowd = tuple(f"P{i:02d}" for i in range(29))
    pool = kw["pool_size"]

    def with_budget(lineage):
        r, _ = pools.arrival_rules({"NEWPARTY", *crowd}, lineage,
                                   group_total=0.0175, **kw)
        return r

    r5 = with_budget({"NEWPARTY": {"support": 0.12}})
    got5 = sum(v * pool[g] for g, v in r5["NEWPARTY"]["capture"].items()) / pool.sum()
    assert _close([got5], [0.12], rel=1e-6), (
        f"a declared 12% emerged from the group rescale at {got5:.4%}. The "
        f"arrival-total record is a prior over arrivals we know nothing "
        f"about, and a party somebody has named and sized is not one of them.")

    rest = sum(sum(v * pool[g] for g, v in r5[q]["capture"].items()) / pool.sum()
               for q in crowd)
    assert _close([rest], [0.0175], rel=1e-6), (
        f"the 29 UNDECLARED entrants total {rest:.4%} against a record of "
        f"1.75%. Holding a declared party out of the budget must not release "
        f"the rest of the group from it — that would trade one bug for the "
        f"over-allocation the rescale was built to fix (ranks 13+ went "
        f"-4.6pp to +19.4pp when it was absent).")

    # IT LOOKED: without the exemption the budget really does bite here.
    unfixed = with_budget({})
    solo = sum(v * pool[g] for g, v in unfixed["NEWPARTY"]["capture"].items()) / pool.sum()
    assert solo < 0.01, (
        f"an UNDECLARED entrant in this 30-party crowd comes out at {solo:.4%}, "
        f"so the group rescale is barely binding and the assertions above "
        f"would pass whether or not the exemption existed")


def test_an_unreadable_key_in_a_party_table_refuses_instead_of_being_ignored():
    """A misspelt `support` is a forecast, not a run, and it fails silently.

    `[party.X]` is hand-edited under time pressure on the day a nomination
    list lands. `suport = 0.12` costs nothing to type, nothing reads it, and
    the emit prints the party at the comparator mean without complaint.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    original = pools.lineage_path

    # (0) THE RIGHT POPULATION: every key the tree actually uses must be
    #     accepted, or this refusal breaks the twenty-six live files.
    used = set()
    for path in sorted(Path("judgements").glob("*.toml")):
        raw = tomllib.loads(path.read_text())
        for body in (raw.get("party") or {}).values():
            used |= set(body)
    assert used, "no [party.*] keys found in judgements/ — scanning the wrong place"
    assert used <= set(pools.PARTY_KEYS), (
        f"the live judgement files use {sorted(used - set(pools.PARTY_KEYS))}, "
        f"which PARTY_KEYS does not admit. This refusal would break the emit.")

    def _load(body):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "joburg-2026.toml"
            p.write_text(body)
            try:
                pools.lineage_path = lambda c, t: p
                return pools.load_lineage(city, target)
            finally:
                pools.lineage_path = original

    # (1) every accepted key passes
    ok = "[party.X]\n" + "\n".join(
        f'{k} = {"[0.5, 0.5]" if k == "weights" else chr(34) + "ANC" + chr(34) if k == "parent" else "0.1"}'
        for k in pools.PARTY_KEYS)
    assert set(_load(ok)["X"]) == set(pools.PARTY_KEYS)

    # (2) A CONSTRUCTED VIOLATION, through the same detector.
    try:
        _load('[party.X]\nsuport = 0.12\n')
    except SystemExit as exc:
        assert "suport" in str(exc) and "support" in str(exc), str(exc)
    else:
        raise AssertionError(
            "a misspelt `suport` was accepted and ignored. The party is then "
            "seeded at the comparator mean and nothing says the declaration "
            "did not land.")


def test_the_arrival_record_figures_are_the_record():
    """A quoted figure must fail when the thing it quotes moves.

    `arrival_group_record`'s docstring said *"sixteen metro-years… median
    3.11%"* for weeks after the panel became 22 city-years and 2.17%, and three
    further sites quoted "0.31%-4.74% over sixteen metro-years" — which is
    2016's range over eight, not the record's. None of the four stated the
    number the live forecast actually uses.

    This is the decay class the register's appendix documents for line numbers,
    and the same remedy: if a number is written down, something fails when it
    moves. Derived here, never typed.
    """
    rec = pools.arrival_group_record()
    shares = [x for x, _, _ in rec]
    doc = pools.arrival_group_record.__doc__

    assert len(rec) >= 20, (
        f"IT LOOKED: the arrival record is {len(rec)} rows. Below about 20 the "
        f"panel has shrunk and the docstring's claims need re-reading, not "
        f"re-asserting.")
    for label, text in (("row count", f"**{len(rec)}**"),
                        ("median", f"**median {np.median(shares):.2%}**"),
                        ("maximum", f"{max(shares):.2%}")):
        assert text in doc, (
            f"`arrival_group_record`'s docstring does not state the record's "
            f"{label}: expected {text!r}. Re-derived now — {len(rec)} rows, "
            f"median {np.median(shares):.4%}, range {min(shares):.2%}-"
            f"{max(shares):.2%}.")

    # ⛔ AND THE CONCENTRATION, WHICH THIS TEST DID NOT LOOK AT.
    #
    # It asserted the row count, the median of TOTALS and the max of TOTALS —
    # and the docstring's alpha range went stale underneath it twice without a
    # word. Its own docstring says the fault it exists for is that "none of the
    # four stated the number the live forecast actually uses"; it then did not
    # pin that number either. Healthy scan, working detector, wrong population.
    alphas = [a for _, a, _ in rec]
    for label, text in (("alpha range", f"{min(alphas):.2f} to {max(alphas):.2f}"),
                        ("alpha median", f"median of {np.median(alphas):.2f}")):
        assert text in doc, (
            f"`arrival_group_record`'s docstring does not state the record's "
            f"{label}: expected {text!r}. Re-derived — range {min(alphas):.2f}"
            f"-{max(alphas):.2f}, median {np.median(alphas):.2f}. This is the "
            f"CONCENTRATION, which `arrival_group_spec` emits into every spec "
            f"with a roster, and it moved +124% at 2021 when the record was "
            f"widened.")

    # And the split/entrant decomposition the docstring warns about.
    prior = pools._arrival_total_prior.__doc__
    ent = [e for _, _, e in rec]
    for text in (f"median {np.median(shares):.4%}", f"mean {np.mean(shares):.4%}",
                 f"median {np.median(ent):.4%}", f"mean {np.mean(ent):.4%}"):
        assert text in prior, (
            f"`_arrival_total_prior` does not state {text!r}. Its two numbers "
            f"are an error of population and an error of statistic that nearly "
            f"cancel, so BOTH must be visible or the next reader repairs one.")

    # ⛔ AND THE VALUE THE FUNCTION ACTUALLY RETURNS. Everything above pins the
    # record; this pins the OUTPUT, which is what the forecast consumes and
    # what no version of this test had ever checked.
    for year in ("2011", "2016", "2021", "2026"):
        got = pools._arrival_total_prior(year)
        assert got is not None, f"_arrival_total_prior({year}) is None"
        assert f"{year}  n=" in prior or f"{got:.4%}" in prior, (
            f"_arrival_total_prior({year}) returns {got:.4%} and the docstring "
            f"does not state it. The number the live forecast uses is the one "
            f"that must be pinned.")
    live = pools._arrival_total_prior("2026")
    assert f"{live:.4%}" in prior, (
        f"the 2026 budget is {live:.4%} and the docstring does not say so — "
        f"this is the value the published forecast consumes.")


def test_a_declared_pool_vector_is_not_a_declared_size():
    """`weights` says WHERE the votes come from, not HOW MANY there are.

    For one commit the `weights` branch defaulted its size to the median over
    the whole un-reach-matched arrival record, and exempted the party from the
    group budget on `not weights`. Two consequences: the two branches held
    different beliefs about "no information" (4.8x apart on the live
    Johannesburg record), and a party nobody had sized escaped the budget
    carrying a number nobody had stated — under a note reading "pools and
    support DECLARED".
    """
    kw = _arrival_kw()
    pool = kw["pool_size"]
    crowd = tuple(f"P{i:02d}" for i in range(29))

    def outcome(lineage):
        r, notes = pools.arrival_rules({"NEWPARTY", *crowd}, lineage,
                                       group_total=0.0175, **kw)
        mine = sum(v * pool[g] for g, v in r["NEWPARTY"]["capture"].items()) / pool.sum()
        rest = sum(sum(v * pool[g] for g, v in r[q]["capture"].items()) / pool.sum()
                   for q in crowd)
        return mine, rest, notes["NEWPARTY"]

    bare, bare_rest, _ = outcome({})
    wonly, wonly_rest, why = outcome({"NEWPARTY": {"weights": [1.0, 0.0]}})
    sized, _, _ = outcome({"NEWPARTY": {"weights": [1.0, 0.0], "support": 0.12}})

    assert _close([wonly], [bare], rel=1e-6), (
        f"a `weights`-only party was sized at {wonly:.4%} against an "
        f"undeclared party's {bare:.4%}. Declaring a pool vector states no "
        f"level, so both must fall back to the same reach-matched estimate.")
    assert _close([wonly_rest], [bare_rest], rel=1e-6), (
        f"a `weights`-only party changed the other entrants' total "
        f"({bare_rest:.4%} -> {wonly_rest:.4%}), so it escaped the group "
        f"budget. The exemption is for a party somebody has named AND SIZED.")
    assert "size NOT declared" in why, (
        f"the note claims a size was declared when none was: {why[:120]!r}")
    assert _close([sized], [0.12], rel=1e-6), (
        "adding `support` must still declare the level — this test must not "
        "pass by making the weights branch inert.")


def test_a_declared_roster_refuses_what_it_cannot_read():
    """On 16 September this file is pasted from the IEC list, under pressure.

    Four silent failures, all measured 2026-09-03 and all fixed here:
      * `[rostr]` parses cleanly, reads as nothing, and the run falls through
        to a PROJECTED ballot printing only its routine message;
      * `partys = [...]` does the same;
      * `parties.canonical` SLUGS an unrecognised name, so 'VF PLUS' becomes
        VF_PLUS — a phantom party — while under `complete = true` the real
        VFPLUS is deleted from the pools by the same edit;
      * a `complete` deletion reported a COUNT, never the MASS, and §1.175
        prices a wrongly-fired drop at 2.4-2.9% of a city's vote.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    original = pools.lineage_path

    def read(body):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "joburg-2026.toml"
            path.write_text(body)
            try:
                pools.lineage_path = lambda c, t: path
                return pools.declared_roster(city, target)
            finally:
                pools.lineage_path = original

    def refuses(body, needle):
        try:
            read(body)
        except SystemExit as exc:
            assert needle in str(exc), f"wrong refusal for {body!r}: {exc}"
            return
        raise AssertionError(f"accepted in silence: {body!r}")

    # (0) THE RIGHT POPULATION: the live files must still parse.
    for path in sorted(Path("judgements").glob("*.toml")):
        raw = tomllib.loads(path.read_text())
        assert set(raw) <= pools.LINEAGE_TABLES, (
            f"{path} carries top-level {sorted(set(raw) - pools.LINEAGE_TABLES)}, "
            f"which this refusal would reject. It would break the emit.")

    # (1) it accepts what it should
    ok = read('[roster]\nparties = ["FREEDOM FRONT PLUS", "ANC"]\n')
    assert ok["parties"] == ["VFPLUS", "ANC"], ok
    assert ok["complete"] is False and ok["confirm_drop"] is False

    # (2) CONSTRUCTED VIOLATIONS, each through the same detector
    refuses('[rostr]\nparties = ["ANC"]\n', "rostr")
    refuses('[roster]\npartys = ["ANC"]\n', "partys")
    refuses('[roster]\nparties = ["ANC"]\ncomplte = true\n', "complte")
    # ⚠️ THE NAME CHECK MOVED, AND SO DOES ITS TEST. It used to live in
    # `declared_roster`, which has no evidence about the city and so had to
    # define "known" as the alias tables alone — and that refused the REAL 2021
    # ballot (see `test_a_realistic_nomination_list_is_accepted`). It now lives
    # in `resolve_roster`, which has the composition and the baseline. Asserting
    # it here would test a function that no longer makes the claim.
    original_lp = pools.lineage_path
    composition = {"ANC": [1.0], "DA": [1.0]}
    baseline = {"ANC": 0.40, "DA": 0.25}

    def resolve_refuses(body, needle):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "joburg-2026.toml"
            path.write_text(body)
            try:
                pools.lineage_path = lambda c, t: path
                pools.resolve_roster(city, target, "2021",
                                     dict(composition), dict(baseline))
            except SystemExit as exc:
                assert needle in str(exc), f"wrong refusal: {exc}"
                return
            finally:
                pools.lineage_path = original_lp
        raise AssertionError(f"a slugged name was accepted: {body!r}")

    for name, slug in (("VF PLUS", "VF_PLUS"),
                       ("UMKHONTO WE SIZWE", "UMKHONTO_WE_SIZWE"),
                       ("ACTIONSA (ASA)", "ACTIONSA_ASA")):
        resolve_refuses(f'[roster]\nparties = ["{name}"]\n', slug)

    # (3) a GENUINE entrant slugs legitimately, and is admitted once placed
    placed = read('[roster]\nparties = ["BRAND NEW PARTY"]\n'
                  '[party.BRAND_NEW_PARTY]\nsupport = 0.05\n')
    assert placed["parties"] == ["BRAND_NEW_PARTY"], placed
    # and it survives resolution, because its [party.X] table places it
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "joburg-2026.toml"
        path.write_text('[roster]\nparties = ["BRAND NEW PARTY"]\n'
                        '[party.BRAND_NEW_PARTY]\nsupport = 0.05\n')
        try:
            pools.lineage_path = lambda c, t: path
            roster, _, _, _ = pools.resolve_roster(
                city, target, "2021", {"ANC": [1.0]}, {"ANC": 0.4})
            assert "BRAND_NEW_PARTY" in roster, roster
        finally:
            pools.lineage_path = original

    # (4) THE DELETION RECONCILES OR IT DOES NOT HAPPEN.
    composition = {"ANC": [1.0], "DA": [1.0], "EFF": [1.0]}
    baseline = {"ANC": 0.40, "DA": 0.25, "EFF": 0.10}

    def resolve(body):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "joburg-2026.toml"
            path.write_text(body)
            try:
                pools.lineage_path = lambda c, t: path
                return pools.resolve_roster(city, target, "2021",
                                            dict(composition), dict(baseline))
            finally:
                pools.lineage_path = original

    big = '[roster]\ncomplete = true\nparties = ["ANC"]\n'
    try:
        resolve(big)
    except SystemExit as exc:
        assert "ceiling" in str(exc) and "confirm_drop" in str(exc), str(exc)
        assert "DA" in str(exc), (
            f"the refusal must NAME what it would delete: {exc}")
    else:
        raise AssertionError(
            "a `complete = true` roster deleted the DA and the EFF from the "
            "pools without reconciling the mass. §1.175 prices a wrongly-fired "
            "drop at 2.4-2.9% of a city's vote, and it is funded out of the "
            "parties ranked 4th to 12th.")

    # and the acknowledgement lets a real one through
    roster, source, deliberate, _ = resolve(big.rstrip() + "\nconfirm_drop = true\n")
    assert source == "declared" and deliberate == {"DA", "EFF"}, (source, deliberate)

    # IT LOOKED: a SMALL drop must still pass without acknowledgement, or the
    # ceiling is really a ban and `complete = true` is unusable.
    small = ('[roster]\ncomplete = true\n'
             'parties = ["ANC", "DA", "EFF"]\n')
    _, src2, del2, _ = resolve(small)
    assert src2 == "declared" and del2 == set(), (src2, del2)


def test_the_pool_capture_cap_says_when_it_binds():
    """`min(..., 0.9)` was a bare literal in no register entry, and it is silent.

    On Johannesburg-like pool sizes a declaration concentrated in one small
    pool loses more than half of itself, under a note that still reads
    "DECLARED". `capture_shortfall` is what lets the note tell the truth.
    """
    pool = np.array([2_180_000.0, 155_000.0, 92_000.0, 480_000.0])
    flat = np.ones(4)
    narrow = np.array([0.0, 0.0, 1.0, 0.0])

    assert pools.capture_shortfall(flat, 0.02, pool) == 0.0, (
        "the cap binds on a 2% flat declaration, so it binds almost "
        "everywhere and is not a cap but a ceiling on the model")
    big = pools.capture_shortfall(narrow, 0.06, pool)
    assert big > 0.4, (
        f"a 6% declaration concentrated in a pool holding "
        f"{pool[2] / pool.sum():.1%} of the electorate lost only {big:.1%}. "
        f"Re-check the arithmetic: this is the case the warning exists for.")

    # the note must SAY so — the whole defect was a silent clip under a
    # message reading DECLARED.
    kw = _arrival_kw()
    kw["pool_size"] = pool
    kw["rates"] = np.zeros((4, 2))
    kw["categories"] = ["A", "B", "C", "D"]
    _, notes = pools.arrival_rules(
        {"NEWPARTY"}, {"NEWPARTY": {"weights": [0, 0, 1, 0], "support": 0.06}}, **kw)
    assert "DID NOT FIT" in notes["NEWPARTY"], notes["NEWPARTY"]


def test_an_incomplete_declared_roster_unions_and_never_strips_a_vector():
    """"ADDS always, removes none" has to mean UNION. It meant REPLACE.

    `roster = set(declared["parties"])` looked right and inverted the only
    safety property the incomplete state has. `no_vector` derives from
    `roster`, so a baseline party left out of a half-typed paste was not in
    `roster`, therefore not in `no_vector`, and got **no pool vector at all** —
    falling to the residual bucket and drawn against a range meant for minor
    parties.

    Measured on the real 2026 inputs before the fix: pasting the top six cost
    **8 parties 15.4826% of the 2024 baseline their pool vector, MK alone at
    12.22%**, while the run printed "ADDS 6 parties and removes none".

    ⚠️ And the union must still honour §K1/§K2 — the first fix re-admitted the
    13 parties those floors had just excluded on measured evidence.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    original = pools.lineage_path

    # Constructed. MK stands for any party with a baseline and no fitted vector.
    composition = {"ANC": [1.0], "DA": [1.0], "EFF": [1.0], "SMALLFRY": [1.0]}
    baseline = {"ANC": 0.40, "DA": 0.25, "EFF": 0.10,
                "MK": 0.1222, "TINY": 0.0001}

    def resolve(body=None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "joburg-2026.toml"
            path.write_text(body if body is not None else "")
            try:
                pools.lineage_path = lambda c, t: path
                return pools.resolve_roster(city, target, "2021",
                                            dict(composition), dict(baseline))
            finally:
                pools.lineage_path = original

    projected, psrc, _, _ = resolve()
    assert psrc == "projected"
    assert "MK" in projected, "the projected ballot must carry a baseline party"
    assert "TINY" not in projected, (
        "TINY is below NATIONAL_ONLY_FLOOR and must not be on a projected "
        "ballot — otherwise this test cannot show the union honours the floor")

    partial, src, deliberate, _ = resolve(
        '[roster]\nparties = ["ANC", "DA"]\n')
    assert src == "declared"
    assert deliberate == set(), f"an INCOMPLETE roster deleted {deliberate}"

    # (1) THE DEFECT: nothing the projection carried may be lost.
    lost = projected - partial
    assert not lost, (
        f"a partial declared roster dropped {sorted(lost)} from the ballot. "
        f"They then get no pool vector at all. 'Adds always, removes none' "
        f"means UNION with the projected ballot, not replace it.")
    assert "MK" in partial, (
        "MK has a baseline and no fitted vector, so it must stay on the ballot "
        "to be given one. This is the 12.22% case.")

    # (2) AND THE UNION HONOURS THE MEASURED FLOORS.
    assert "TINY" not in partial, (
        "the union re-admitted a party §K1's floor excluded on measured "
        "evidence. The floor applies whoever is asking.")

    # (3) COMPLETE still replaces — that is what declaring a whole ballot means.
    whole, wsrc, wdel, _ = resolve(
        '[roster]\ncomplete = true\nconfirm_drop = true\nparties = ["ANC"]\n')
    assert whole == {"ANC"}, whole
    assert wdel == {"DA", "EFF", "SMALLFRY"}, wdel


def test_the_two_safety_booleans_refuse_a_quoted_value():
    """`bool("false")` is True, and these two flags decide deletions.

    Every other key in `[roster]` refuses a wrong type loudly. The two whose
    entire job is safety accepted any truthy string — so one pair of quotes
    turned the deletion on and a second disabled the ceiling that would have
    caught it, at 22:00 on the one night this file is ever edited.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    original = pools.lineage_path

    def read(body):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "joburg-2026.toml"
            path.write_text(body)
            try:
                pools.lineage_path = lambda c, t: path
                return pools.declared_roster(city, target)
            finally:
                pools.lineage_path = original

    # real booleans still work, both ways
    assert read('[roster]\nparties = ["ANC"]\ncomplete = true\n')["complete"] is True
    assert read('[roster]\nparties = ["ANC"]\ncomplete = false\n')["complete"] is False
    assert read('[roster]\nparties = ["ANC"]\n')["complete"] is False, "default"

    # CONSTRUCTED VIOLATIONS: every truthy non-boolean must refuse.
    for key in ("complete", "confirm_drop"):
        for literal in ('"false"', '"no"', '"true"', '1', '0'):
            try:
                read(f'[roster]\nparties = ["ANC"]\n{key} = {literal}\n')
            except SystemExit as exc:
                assert key in str(exc), str(exc)
            else:
                raise AssertionError(
                    f"[roster] {key} = {literal} was accepted. "
                    f"`bool({literal})` decides whether parties are deleted "
                    f"from the pools, and {literal} is not a boolean.")


def test_an_environment_gate_moves_the_artefact_key():
    """`_code_sha` hashes a syntax tree. An env var does not change the tree.

    `_deps_sha` names `levels` as a dependency BECAUSE it carries `HELD_BACK`,
    "which decides whether a fitting election may be read at all". But
    `HELD_BACK_OFF=1` empties `HELD_BACK` at import time, and `levels.py`'s own
    comment invites exactly that run. Measured 2026-09-05 before the fix:
    `HELD_BACK` 14 entries -> 0, `deps_sha` byte-identical. A spec emitted that
    way reported itself current for ever after — the silent staleness this key
    exists to close, through the one door it did not watch.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")

    base = pools.artefact_key(city, target)
    assert "gates_sha" in base, (
        "the artefact key records no gate state, so an emit run under "
        "HELD_BACK_OFF=1 is indistinguishable from a normal one")

    # CONSTRUCTED VIOLATION: flip the resolved gate and the key must move.
    import levels
    real_env = os.environ.get("HELD_BACK_OFF")
    real_gate = levels.HELD_BACK
    try:
        os.environ["HELD_BACK_OFF"] = "1"
        levels.HELD_BACK = type(real_gate)()
        moved = pools.artefact_key(city, target)
    finally:
        levels.HELD_BACK = real_gate
        if real_env is None:
            os.environ.pop("HELD_BACK_OFF", None)
        else:
            os.environ["HELD_BACK_OFF"] = real_env

    assert moved["gates_sha"] != base["gates_sha"], (
        "lifting HELD_BACK did not move the artefact key. A spec emitted "
        "during a diagnostic run would report itself current for ever.")
    assert pools.artefact_key(city, target)["gates_sha"] == base["gates_sha"], (
        "the gate state did not restore — this test has contaminated the tree")

    # IT LOOKED: the gate must actually be non-empty by default, or the
    # constructed violation is a change from nothing to nothing.
    assert len(real_gate) > 0, (
        f"levels.HELD_BACK is empty by default ({len(real_gate)}), so this "
        f"test flips nothing. It held 14 entries when written.")


def test_a_realistic_nomination_list_is_accepted():
    """⛔ THE 16 SEPTEMBER REHEARSAL. It has to accept the real thing.

    Every other roster test drives a constructed three-party file. This one
    pastes an actual metro ballot — the real 2021 Johannesburg list, 57 parties,
    which is the shape and size of what a human will paste on nomination night.

    **It failed when written, and that is why it exists.** `KNOWN_PARTY_CODES`
    was the hand-maintained alias tables alone, so the long tail of small
    parties that genuinely contested resolved to "unknown" and the run refused
    the correct input. A guard that fires on the right answer on the one night
    it runs is worse than no guard at all.

    "Known" is now: the alias tables, OR a prior record in this city, OR a party
    that stood at the last local election even if it scored nothing
    (AFRICAN_COVENANT and SAKHISIZWE_CONVENTION are both on the real 2021
    ballot with zero votes), OR placed by its own `[party.X]` table.
    """
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    original = pools.lineage_path

    ballot = sorted(pools.contesting_parties(city, "2021"))
    assert len(ballot) > 40, (
        f"IT LOOKED: the 2021 Johannesburg ballot parsed to {len(ballot)} "
        f"parties. A realistic list is 50+; with fewer this rehearses nothing.")

    local = pools.metro_citywide("JHB", "2021")
    spec = json.loads((ROOT / "data/processed/pools_2026.json").read_text())
    cats = list(spec["pools"])
    composition = {q: [spec["pools"][c]["members"].get(q, 0.0) for c in cats]
                   for q in {r for pl in spec["pools"].values() for r in pl["members"]}
                   if q in local}
    path = city.path("raw", "elections",
                     cityconfig.CALENDAR[target.previous_npe].results)
    counts = collections.defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            counts[parties.canonical(row["sPartyName"])] += int(
                float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    baseline = {q: c / total for q, c in counts.items()}

    def resolve(body):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "joburg-2026.toml"
            f.write_text(body)
            try:
                pools.lineage_path = lambda c, t: f
                return pools.resolve_roster(city, target, "2021",
                                            dict(composition), dict(baseline))
            finally:
                pools.lineage_path = original

    listing = json.dumps(ballot)

    # (1) THE HAPPY PATH, INCOMPLETE — adds, deletes nothing.
    roster, src, deliberate, _ = resolve(f"[roster]\nparties = {listing}\n")
    assert src == "declared", src
    assert deliberate == set(), (
        f"an INCOMPLETE roster deleted {len(deliberate)} parties")
    assert len(roster) >= len(ballot), (
        f"the union lost parties: {len(roster)} on the ballot against "
        f"{len(ballot)} declared")

    # (2) THE HAPPY PATH, COMPLETE — the whole ballot, and it is accepted.
    roster2, src2, _, _ = resolve(
        f"[roster]\ncomplete = true\nparties = {listing}\n")
    assert src2 == "declared" and roster2 == set(ballot), (
        f"a complete real ballot did not resolve to itself: "
        f"{len(roster2)} against {len(ballot)}")

    # (3) AND A TYPO IN A REAL PARTY'S NAME STILL REFUSES. If this passes,
    #     the fix for (1) and (2) has made the guard useless.
    try:
        resolve('[roster]\nparties = ["AFRICAN NATIONAL CONGRES"]\n')
    except SystemExit as exc:
        assert "AFRICAN_NATIONAL_CONGR" in str(exc), str(exc)
    else:
        raise AssertionError(
            "a misspelt 'AFRICAN NATIONAL CONGRES' was accepted. Widening "
            "`known` to admit the real ballot must not admit typos — that is "
            "the whole trade this guard exists to make.")


def test_an_undeclared_split_is_flagged_in_the_spec_not_printed():
    """A party with a national vote and no lineage is the ActionSA shape.

    `classify_arrival` says "arrived from nothing" for anything absent from
    `SPLITS` and undeclared. That is right for a genuine entrant and wrong for a
    party that plainly exists and has simply not been typed in — which cost
    0.1% against an actual 18.12% once already.

    The flag is written INTO the spec rather than printed, because a print
    during an emit is scrollback and the emit is the one operation nobody
    re-runs. This asserts the detector's rule on constructed input; the
    end-to-end test asserts it reaches the file.
    """
    floor = pools.UNCLASSIFIED_FLOOR
    assert 0.001 < floor < 0.02, (
        f"UNCLASSIFIED_FLOOR is {floor}. Below ~0.1% it flags the whole "
        f"national tail; above ~2% it misses the cases it exists for.")

    # (1) THE RULE: no declared parent AND a national share over the floor.
    def flags(party, national, declared_parent=None):
        parent, _ = pools.classify_arrival(party, declared_parent)
        return not parent and national >= floor

    assert flags("BRANDNEW", floor + 1e-6), "a party over the floor must flag"
    assert not flags("BRANDNEW", floor - 1e-6), "under the floor must not flag"
    assert not flags("BRANDNEW", 0.5, declared_parent="ANC"), (
        "a DECLARED parent means the lineage is known — nothing to flag")

    # (2) A PARTY ALREADY IN `SPLITS` IS CLASSIFIED AND MUST NOT FLAG. MK is
    #     the live case: it carries 12.22% of the 2024 vote, so a rule keying
    #     only on size would flag the one party whose parent IS declared.
    parent, _ = pools.classify_arrival("MK", None)
    assert parent == "ANC", f"MK's declared parent is {parent!r}, expected ANC"
    assert not flags("MK", 0.1222), (
        "MK flagged despite being in SPLITS with parent ANC. The detector must "
        "key on MISSING LINEAGE, not on size — otherwise the biggest arrival "
        "in the file is the first false positive.")

    # (3) IT LOOKED: the live 2026 roster must actually contain a case, or this
    #     guards a situation that does not arise.
    city = cityconfig.use("joburg")
    target = cityconfig.Target(city=city, year="2026")
    path = city.path("raw", "elections",
                     cityconfig.CALENDAR[target.previous_npe].results)
    counts = collections.defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            counts[parties.canonical(row["sPartyName"])] += int(
                float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    baseline = {q: c / total for q, c in counts.items()}
    live = [q for q, v in baseline.items()
            if flags(q, v) and q not in ("IND", "ENTRANT")]
    assert live, (
        f"no party in the {target.previous_npe} national file has a share over "
        f"{floor:.1%} and no declared lineage, so this detector currently "
        f"guards nothing. Re-check the floor against the file.")
    assert len(live) < 10, (
        f"{len(live)} parties flagged. The list is meant to be short enough to "
        f"read on nomination day; this one would be ignored.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))

