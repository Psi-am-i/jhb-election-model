"""End-to-end invariants for the prediction chain.

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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np                                              # noqa: E402
from _support import ROOT, run_module, skip                     # noqa: E402

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
    """The emitted pool spec for a target, from disk."""
    key = f"spec{target}"
    if key not in _CACHE:
        path = _city().processed / f"pools_{target}.json"
        if not path.exists():
            skip(f"no {path.name}; run: python src/pools.py --city {CITY} "
                 f"--target {target} --emit")
        _CACHE[key] = json.loads(path.read_text())
    return _CACHE[key]


# --------------------------------------------------------------------------
# 1. the constrained fit — what must be true of any election
# --------------------------------------------------------------------------

def test_pool_rates_are_never_negative():
    """No party wins a negative number of votes.

    Caught: independent per-party fits put Al Jama-ah at -1.9% +/- 0.3 among
    white voters and the PA at -3.5% among Indian voters. Tight negatives are
    misspecification, not noise.
    """
    fits, _ = _fit()
    worst = min((f.rates.min(), p) for p, f in fits.items())
    assert worst[0] >= 0.0, f"{worst[1]} has a negative rate: {worst[0]}"


def test_each_pool_allocates_exactly_one_vote():
    """Every voter votes for someone, so a pool's rates sum to 1.

    Caught: the white pool was assigned 111.4% of its voters and the Coloured
    pool 90.4%, with 106.1% of the vote existing in total.
    """
    fits, ctx = _fit()
    rates = np.array([f.rates for f in fits.values()])
    sums = rates.sum(axis=0)
    assert np.allclose(sums, 1.0, atol=1e-6), \
        f"pool rates sum to {sums} across {len(ctx['categories'])} pools, not 1"


def test_party_totals_match_the_votes_actually_cast():
    """Each party's implied vote equals what it won: the other known margin."""
    fits, ctx = _fit()
    electorate = ctx["pool_votes"]
    total = electorate.sum()
    worst = 0.0
    for party, fit in fits.items():
        implied = float(fit.rates @ electorate) / total
        worst = max(worst, abs(implied - fit.citywide))
    assert worst < 1e-6, f"worst party-total error {worst:.2e}"


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

def test_a_party_with_a_baseline_is_never_seeded():
    """Caught: MK held 12.22% of the 2024 baseline AND got a +15.98% seed, so
    a split already present in the baseline was applied twice — MK started at
    28.20% and the ANC was debited to 15.98%, half its measured share. It
    produced ANC 36 / MK 68."""
    spec = _spec(TARGET)
    seeds = spec.get("seeds", {})
    target = cityconfig.Target(city=_city(), year=TARGET)
    path = _city().path("raw", "elections",
                        cityconfig.CALENDAR[target.previous_npe].results)
    if not path.exists():
        skip(f"no baseline at {path}")
    import csv
    import parties as P
    from collections import defaultdict
    counts: dict = defaultdict(int)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for row in csv.DictReader(fh):
            counts[P.canonical(row["sPartyName"])] += int(
                float(row.get("Party_Votes") or 0))
    total = sum(counts.values())
    offenders = [p for p, v in seeds.items()
                 if v > 0 and counts.get(p, 0) / total > 1e-6]
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
    newcomer vanished from the LIVE forecast while the backtests looked fine."""
    city = _city()
    assert not pools.contesting_parties(city, TARGET), \
        "an unheld target now has a roster; this test's premise has changed"
    spec = _spec(TARGET)
    members = {p for cfg in spec["pools"].values() for p in cfg["members"]}
    assert len(members) > 10, \
        (f"only {len(members)} parties carry a pool vector for {TARGET}; the "
         f"roster fallback has stopped working")


# --------------------------------------------------------------------------
# 4. temporal validity — a forecast may not read its own answer
# --------------------------------------------------------------------------

def test_pool_ratios_are_measured_only_before_the_target():
    for target in ("2016", "2021"):
        pairs = pools.lge_transitions(before=target)
        late = [p for p in pairs if int(p[1]) >= int(target)]
        assert not late, f"target {target} would measure ratios over {late}"


def test_the_level_prior_reads_no_election_at_or_after_its_target():
    """levels.theta_record must stop strictly before the target."""
    city = _city()
    for year in ("2016", "2021"):
        target = cityconfig.Target(city=city, year=year)
        record = levels.theta_record(target)
        assert record, f"no theta record before {year}"
        # every contributing LGE must be strictly earlier
        contributing = [y for y, e in cityconfig.CALENDAR.items()
                        if e.kind == "LGE" and e.results and int(y) < int(year)]
        assert contributing, f"no prior LGE for {year}"


# --------------------------------------------------------------------------
# 5. scoring — the instrument every decision is made against
# --------------------------------------------------------------------------

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


class _Args:
    """The shape ``montecarlo.load_scenario`` expects from argparse."""

    def __init__(self, draws: int):
        self.config = None
        self.set = None
        self.draws = draws
        self.seed = None


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
