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

import json
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np                                              # noqa: E402
from _support import (ROOT, election_files_read, run_module,    # noqa: E402
                      skip)

import cityconfig                                               # noqa: E402
import levels                                                   # noqa: E402
import montecarlo as mc                                         # noqa: E402
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
    read = {"theta_mode": ["ASA"]}
    assert B.contaminated("2021", set(), read) == ["theta_mode"], \
        "a constant the run did read was not reported"
    assert B.contaminated("2026", set(), read) == [], \
        "theta_mode was reported against a target it predates"


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
    for path in sorted(ROOT.glob("data/processed/**/pools_*.json")):
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


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
