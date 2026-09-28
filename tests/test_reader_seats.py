"""`reader_seats`: a reader's combined vote shares and ward picks, seated by the
statute alone.

DESIGN-decided §9 and §10 (the reader edits the COMBINED vote, both ballots
together). What this module proves:

1. REPRODUCTION. For every draw of a native `run_model` at Johannesburg 2021
   and 2026, the draw's own combined-ballot tally (captured by a wrapper around
   `montecarlo.allocate_with_overhang`, which needs no edit to the model) and
   its own ward winners, fed through `reader_seats`, give that draw's seats,
   ward seats, excessive-seats parties and council exactly. The comparator is
   shown to see a constructed disagreement and to go quiet when it is reverted.
   The draw's PR-BALLOT share is also fed, and the draws it does not reproduce
   are COUNTED AND PRINTED, not asserted: that is the cost of the RETIRED input
   (JUDGEMENT-CALLS.md §M1, MODEL-LOG §1.270), kept as the evidence the owner's
   §10 decision rests on.
2. STATUTE INVARIANTS. Seats sum to the council; each party's ward seats equal
   the wards picked for it; list seats are never negative.
3. EXCESSIVE SEATS, BY HAND. Two councils worked on paper below: a strict
   excess, and item 16(1)'s "equal to", which moves a seat between two OTHER
   parties. Plus a no-PR-list ward winner leaving through D.
4. REFUSALS. Each validation is triggered by one constructed violation of an
   otherwise valid input, which is shown to pass.
5. ROUNDING. The combined votes sum to `total_votes` exactly, on a case where
   rounding each party alone does not.
6. PYODIDE SHAPE. In a fresh interpreter with pandas/openpyxl/scipy made
   unimportable and every file open raising, the module imports and allocates.
7. THE SEAT SERVICE. worker-api/seats-py/src/entry.py passes a request body
   through as reader_seats' own arguments and reshapes the answer; the files
   worker-api/tools/sync_seats_py.mjs copies are the module's import closure,
   both ways.

The model runs in a subprocess from `ROOT/src`, or from the directory named in
`READER_SEATS_MODEL_SRC` (a `git archive` copy, when another worker is editing
`src/` mid-run). The allocation under test always comes from this process's
`src/`.
"""

from __future__ import annotations

import json
import os
import pickle
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned  # noqa: E402

import montecarlo as M  # noqa: E402
import reader_seats as R  # noqa: E402

CITY = "joburg"
TARGETS = ("2021", "2026")
SEED = 20261104
DRAWS = 100

_WORKER = r'''
import pickle, sys
src, out, city, target, seed, draws = sys.argv[1:7]
sys.path.insert(0, src)
import cityconfig
cityconfig.use(city)
t = cityconfig.use_target(target)
import montecarlo as mc
calls = []
real = mc.allocate_with_overhang
def capturing(combined, ward_wins, rule="deduct", independent_wards=0,
              no_pr_list_wards=0):
    value = real(combined, ward_wins, rule, independent_wards=independent_wards,
                 no_pr_list_wards=no_pr_list_wards)
    calls.append({"combined": list(combined.items()), "pool_wins": dict(ward_wins),
                  "rule": rule, "c": independent_wards, "d": no_pr_list_wards,
                  "council": mc.COUNCIL})
    return value
mc.allocate_with_overhang = capturing
class Args:
    config = None; set = None
Args.draws = int(draws); Args.seed = int(seed)
run = mc.run_model(t, mc.load_scenario(Args()), verbose=False)
payload = {
    "file": mc.__file__, "calls": calls, "universe": list(run.universe),
    "wards": list(run.wards), "seat_draws": run.seat_draws,
    "ward_seat_draws": run.ward_seat_draws,
    "ward_winner_draws": run.ward_winner_draws,
    "over_draws": [sorted(o) for o in run.over_draws],
    "council_sizes": run.council_sizes, "pr_share_draws": run.pr_share_draws,
    "council": t.council, "wards_configured": t.wards,
}
with open(out, "wb") as handle:
    pickle.dump(payload, handle)
'''

_STATE: dict = {}


def _runs() -> dict:
    """One native run per target, draws and captured allocator inputs. Cached."""
    if _STATE:
        return _STATE
    src = Path(os.environ.get("READER_SEATS_MODEL_SRC", ROOT / "src"))
    tmp = tempfile.TemporaryDirectory(prefix="reader_seats_")
    base = Path(tmp.name)
    worker = base / "worker.py"
    worker.write_text(_WORKER, encoding="utf-8")
    env = dict(os.environ, PYTHONHASHSEED=M.HASH_SEED)
    procs = {}
    for target in TARGETS:
        out = base / f"{target}.pkl"
        procs[target] = (out, subprocess.Popen(
            [sys.executable, str(worker), str(src), str(out), CITY, target,
             str(SEED), str(DRAWS)],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True))
    for target, (out, proc) in procs.items():
        _, err = proc.communicate(timeout=3600)
        if proc.returncode != 0:
            raise AssertionError(f"{CITY} {target} run failed:\n{err[-3000:]}")
        with out.open("rb") as handle:
            _STATE[target] = pickle.load(handle)
    _STATE["_tmp"] = tmp
    return _STATE


def _winners(run: dict, d: int) -> dict[str, str]:
    universe = run["universe"]
    return {w: universe[int(j)]
            for w, j in zip(run["wards"], run["ward_winner_draws"][d])}


def _context(run: dict) -> dict:
    return R.context_for(CITY, run["target"], run["universe"], run["wards"])


def _draw_disagreements(run: dict, d: int, result: dict) -> list[str]:
    """How `result` differs from draw `d` of `run`, as sentences. Empty = same."""
    problems = []
    if not result["ok"]:
        return [f"refused: {result['errors']}"]
    call = run["calls"][d]
    # Pool parties only: the model's `seat_draws` omit C and D ward seats, and
    # the captured C and D are asserted zero by the caller.
    pool = {p for p, _ in call["combined"]}
    got = {p: v["total"] for p, v in result["seats"].items() if p in pool}
    want = {p: n for p, n in run["seat_draws"][d].items() if n}
    if got != want:
        diff = sorted(p for p in set(got) | set(want) if got.get(p) != want.get(p))
        problems.append(f"seats differ for {diff}")
    wards = {p: v["ward"] for p, v in result["seats"].items() if v["ward"]}
    if wards != {p: n for p, n in run["ward_seat_draws"][d].items() if n}:
        problems.append("ward seats differ")
    if sorted(result["excessive"]) != run["over_draws"][d]:
        problems.append(f"excessive {sorted(result['excessive'])} vs "
                        f"{run['over_draws'][d]}")
    if result["council"] != int(run["council_sizes"][d]):
        problems.append("council differs")
    return problems


def _combined_inputs(run: dict, d: int) -> tuple[dict[str, float], int]:
    combined = run["calls"][d]["combined"]
    total = sum(v for _, v in combined)
    return {p: v / total for p, v in combined}, total


def _prepared() -> dict:
    runs = _runs()
    for target in TARGETS:
        runs[target]["target"] = target
    return runs


# -- 1. reproduction ------------------------------------------------------------

def test_the_capture_is_one_call_per_draw_on_the_configured_council():
    runs = _prepared()
    for target in TARGETS:
        run = runs[target]
        scanned(run["calls"], of=DRAWS, low=1.0, high=1.0,
                what=f"allocator calls captured at {target}",
                denominator="draws requested")
        assert len(run["seat_draws"]) == DRAWS
        assert len(run["wards"]) == run["wards_configured"]
        for call in run["calls"]:
            assert call["council"] == run["council"]
            assert call["rule"] == M.STATUTORY_VALUES["overhang_rule"]
            # The model seats no independent and no list-less party (its
            # universe has neither); if that changes, the comparison below must
            # add C and D back rather than silently agree on the wrong set.
            assert call["c"] == 0 and call["d"] == 0, (target, call["c"], call["d"])


def test_every_draw_is_reproduced_from_its_combined_tally_and_ward_winners():
    runs = _prepared()
    fired = unfired = 0
    for target in TARGETS:
        run = runs[target]
        context = _context(run)
        for d in range(DRAWS):
            shares, total = _combined_inputs(run, d)
            result = R.reader_seats(shares, _winners(run, d), context, total)
            problems = _draw_disagreements(run, d, result)
            assert not problems, f"{target} draw {d}: {problems}"
            fired += result["excessive_fired"]
            unfired += not result["excessive_fired"]
    # Both branches of item 16 were exercised by real draws, not only by the
    # hand-built councils below.
    assert fired and unfired, (fired, unfired)
    print(f"  reproduced {len(TARGETS) * DRAWS} draws exactly; excessive-seats "
          f"clause fired in {fired}")


def test_the_reproduction_comparator_sees_a_constructed_disagreement():
    run = _prepared()["2026"]
    context = _context(run)
    shares, total = _combined_inputs(run, 0)
    good = R.reader_seats(shares, _winners(run, 0), context, total)
    assert not _draw_disagreements(run, 0, good)
    # Move a tenth of the largest party's share to the second largest.
    first, second = sorted(shares, key=lambda p: -shares[p])[:2]
    moved = dict(shares)
    delta = moved[first] / 10
    moved[first] -= delta
    moved[second] += delta
    bad = R.reader_seats(moved, _winners(run, 0), context, total)
    assert _draw_disagreements(run, 0, bad)
    # Reverted, it is quiet again.
    again = R.reader_seats(dict(shares), _winners(run, 0), context, total)
    assert not _draw_disagreements(run, 0, again)


def test_the_pr_ballot_assumption_is_measured_not_asserted():
    """The draw's PR-ballot share, at the draw's combined total, per draw.

    Printed rather than asserted. This is the RETIRED input: until
    DESIGN-decided §10 a reader's PR shares stood for both ballots, and the
    draws this fails to reproduce are what that cost (MODEL-LOG §1.270). The
    reader now edits the combined vote, which reproduces every draw (above);
    this stays as the measurement that decision rests on, and the number moves
    with the model's ward/PR ratios.
    """
    runs = _prepared()
    for target in TARGETS:
        run = runs[target]
        context = _context(run)
        missed, seat_moves = 0, []
        for d in range(DRAWS):
            share = run["pr_share_draws"][d]
            _, total = _combined_inputs(run, d)
            # Parties below one vote at this total are dropped, as the model's
            # own `eligible_parties` drops a zero-vote party.
            pr = {p: float(share[i]) for i, p in enumerate(run["universe"])
                  if round(share[i] * total) > 0}
            norm = sum(pr.values())
            pr = {p: v / norm for p, v in pr.items()}
            result = R.reader_seats(pr, _winners(run, d), context, total,
                                    tolerance=1e-6)
            assert result["ok"], (target, d, result["errors"])
            if _draw_disagreements(run, d, result):
                missed += 1
                seat_moves.append(sum(
                    abs(result["seats"].get(p, {}).get("total", 0)
                        - run["seat_draws"][d].get(p, 0))
                    for p in set(result["seats"]) | set(run["seat_draws"][d])) // 2)
        print(f"  {CITY} {target}: the PR-ballot share alone reproduces "
              f"{DRAWS - missed} of {DRAWS} draws; where it does not, seats "
              f"moved: max {max(seat_moves, default=0)}, mean "
              f"{(sum(seat_moves) / len(seat_moves)) if seat_moves else 0:.2f}")


# -- 2. statute invariants --------------------------------------------------------

def _invariants(result: dict, winners: dict, council: int) -> list[str]:
    problems = []
    seats = result["seats"]
    if sum(v["total"] for v in seats.values()) != council:
        problems.append("seats do not sum to the council")
    picked: dict[str, int] = {}
    for party in winners.values():
        picked[party] = picked.get(party, 0) + 1
    if {p: v["ward"] for p, v in seats.items() if v["ward"]} != picked:
        problems.append("ward seats are not the picks")
    if any(v["pr"] < 0 or v["total"] != v["ward"] + v["pr"] for v in seats.values()):
        problems.append("a list-seat count is negative or does not add up")
    if result["council"] != council:
        problems.append("the council size moved")
    return problems


def test_statute_invariants_hold_on_real_draws_and_on_reader_edits():
    import numpy as np
    runs = _prepared()
    checked = 0
    for target in TARGETS:
        run = runs[target]
        context = _context(run)
        rng = np.random.default_rng(0)
        parties = [p for p, _ in run["calls"][0]["combined"]]
        for d in range(DRAWS):
            shares, total = _combined_inputs(run, d)
            winners = _winners(run, d)
            for result, picks in (
                    (R.reader_seats(shares, winners, context, total), winners),
                    # A reader's edit: random shares over the same parties, and
                    # every ward handed to a random one of the top five.
                    _edit(rng, parties, run["wards"], context, total)):
                assert result["ok"], result["errors"]
                problems = _invariants(result, picks, run["council"])
                assert not problems, (target, d, problems)
                checked += 1
    assert checked == 2 * len(TARGETS) * DRAWS


def _edit(rng, parties, wards, context, total):
    raw = rng.dirichlet([1.0] * len(parties))
    shares = {p: float(v) for p, v in zip(parties, raw)}
    shares = {p: v for p, v in shares.items() if round(v * total) > 0}
    norm = sum(shares.values())
    shares = {p: v / norm for p, v in shares.items()}
    top = sorted(shares, key=lambda p: -shares[p])[:5]
    picks = {w: top[int(rng.integers(len(top)))] for w in wards}
    return R.reader_seats(shares, picks, context, total, tolerance=1e-6), picks


def test_the_invariant_checker_sees_a_constructed_violation():
    context = _toy_context()
    winners = {"W1": "A", "W2": "A", "W3": "A", "W4": "A", "W5": "A"}
    result = R.reader_seats({"A": 0.31, "B": 0.40, "C": 0.29}, winners,
                            context, 1000)
    assert not _invariants(result, winners, 10)
    broken = json.loads(json.dumps(result))
    broken["seats"]["B"]["total"] += 1
    broken["seats"]["B"]["pr"] += 1
    assert _invariants(broken, winners, 10)
    lied = dict(winners, W5="B")
    assert _invariants(result, lied, 10)


# -- 3. excessive seats, by hand -------------------------------------------------

def _toy_context(no_pr_list=()) -> dict:
    """Ten seats, five wards: small enough to allocate on paper.

    Built directly, not through `context_for`, because no city has this
    council; `context_errors` still vets it.
    """
    return {"city": "toy", "target": "toy", "council": 10,
            "wards": ["W1", "W2", "W3", "W4", "W5"],
            "parties": ["A", "B", "C", "X"], "no_pr_list": list(no_pr_list)}


def _split(result):
    return {p: (v["ward"], v["pr"], v["total"]) for p, v in result["seats"].items()}


def test_a_strict_excess_is_fixed_at_its_wards_and_the_rest_reallocated():
    """A .31, B .40, C .29 of 1,000 votes; A wins all five wards.

    Quota 1000 // 10 + 1 = 101. A 310/101 = 3 r .069, B 400/101 = 3 r .960,
    C 290/101 = 2 r .871: eight in round one, the two remainders go to B and C,
    so A 3, B 4, C 3. A's five wards exceed its three: item 16 fixes A at 5 (an
    excess of 2) and re-strikes the quota for the others over 10 - 5 = 5 seats.
    690 // 5 + 1 = 139. B 400/139 = 2 r .878, C 290/139 = 2 r .086: four, the
    last to B. B 3, C 2. The council stays at 10.
    """
    winners = {w: "A" for w in ("W1", "W2", "W3", "W4", "W5")}
    result = R.reader_seats({"A": 0.31, "B": 0.40, "C": 0.29}, winners,
                            _toy_context(), 1000)
    assert result["ok"], result["errors"]
    assert _split(result) == {"A": (5, 0, 5), "B": (0, 3, 3), "C": (0, 2, 2)}
    assert result["excessive"] == {"A": 2} and result["excessive_fired"]
    assert result["council"] == 10 and result["majority"] == 6


def test_wins_equal_to_the_entitlement_trigger_item_16_and_move_another_seat():
    """A .06, B .16, C .78 of 1,000 votes; A wins W1, C the other four.

    Quota 101. A 60/101 = 0 r .594, B 160/101 = 1 r .584, C 780/101 = 7 r .723:
    eight, the two remainders to C and A, so A 1, B 1, C 8. A's one ward EQUALS
    its entitlement, which item 16(1) ("equal to or greater") counts: A is fixed
    at 1 and the quota is re-struck for B and C over nine seats. 940 // 9 + 1 =
    105. B 160/105 = 1 r .524, C 780/105 = 7 r .429: eight, the last to B. So
    B 2, C 7 — the clause fired at an excess of zero and moved a seat from C to
    B, which is why it is not a no-op for the others.
    """
    winners = {"W1": "A", "W2": "C", "W3": "C", "W4": "C", "W5": "C"}
    result = R.reader_seats({"A": 0.06, "B": 0.16, "C": 0.78}, winners,
                            _toy_context(), 1000)
    assert result["ok"], result["errors"]
    assert _split(result) == {"A": (1, 0, 1), "B": (0, 2, 2), "C": (4, 3, 7)}
    assert result["excessive"] == {"A": 0} and result["excessive_fired"]


def test_a_ward_won_by_a_party_with_no_pr_list_leaves_the_pool_through_d():
    """A .6, B .4 of 1,000; X (no PR list) wins W1, A the other four.

    D = 1, so nine seats are allocated: quota 1000 // 9 + 1 = 112. A 600/112 =
    5 r .357, B 400/112 = 3 r .571: eight, the last to B. A 5, B 4, X 1.
    """
    winners = {"W1": "X", "W2": "A", "W3": "A", "W4": "A", "W5": "A"}
    result = R.reader_seats({"A": 0.6, "B": 0.4}, winners,
                            _toy_context(no_pr_list=["X"]), 1000)
    assert result["ok"], result["errors"]
    assert _split(result) == {"A": (4, 1, 5), "B": (0, 4, 4), "X": (1, 0, 1)}
    assert result["no_pr_list_wards"] == 1 and result["independent_wards"] == 0
    assert not result["excessive_fired"]


# -- 4. refusals -------------------------------------------------------------------

_GOOD_SHARES = {"A": 0.5, "B": 0.3, "C": 0.2}
_GOOD_WINNERS = {"W1": "A", "W2": "A", "W3": "B", "W4": "C", "W5": "A"}


def _refusal(shares=None, winners=None, context=None, total=1000, **kw):
    result = R.reader_seats(_GOOD_SHARES if shares is None else shares,
                            _GOOD_WINNERS if winners is None else winners,
                            _toy_context() if context is None else context,
                            total, **kw)
    assert not result["ok"] and result["errors"] and not result["seats"], result
    return " ".join(result["errors"])


def test_the_unviolated_input_is_accepted():
    result = R.reader_seats(_GOOD_SHARES, _GOOD_WINNERS, _toy_context(), 1000)
    assert result["ok"] and not result["errors"], result["errors"]
    assert result["assumption"] == R.ASSUMPTION


def test_each_violation_is_refused_and_named():
    cases = {
        "unknown parties": dict(shares={**_GOOD_SHARES, "Z": 0.0}),
        "not 1": dict(shares={"A": 0.5, "B": 0.3, "C": 0.1}),
        "not finite non-negative": dict(shares={"A": 1.2, "B": -0.2, "C": 0.0}),
        "no winner": dict(winners={k: v for k, v in _GOOD_WINNERS.items()
                                   if k != "W3"}),
        "unknown wards": dict(winners={**_GOOD_WINNERS, "W6": "A"}),
        "not on the roster": dict(winners={**_GOOD_WINNERS, "W4": "Z"}),
        "zero share": dict(shares={"A": 0.7, "B": 0.3},
                           winners={**_GOOD_WINNERS, "W4": "C"}),
        "have no PR list": dict(context=_toy_context(no_pr_list=["C"])),
        "too small to receive": dict(shares={"A": 0.5, "B": 0.3, "C": 0.1999,
                                        "X": 0.0001}),
        "total_votes": dict(total=0),
        "context has no": dict(context={k: v for k, v in _toy_context().items()
                                        if k != "council"}),
        "a party twice": dict(context={**_toy_context(),
                                       "parties": ["A", "B", "C", "A"]}),
        "cannot fit": dict(context={**_toy_context(), "council": 4}),
        "not a mapping": dict(shares=[("A", 1.0)]),
    }
    for needle, kwargs in cases.items():
        message = _refusal(**kwargs)
        assert needle in message, (needle, message)
    # A float total is refused, not rounded.
    assert "total_votes" in _refusal(total=1000.0)


def test_the_seat_law_failing_is_reported_not_raised():
    # Ten seats cannot be shared out of three votes by largest remainder:
    # `seats.allocate` raises, and the reader gets a sentence instead.
    message = _refusal(total=3, shares={"A": 1 / 3, "B": 1 / 3, "C": 1 / 3})
    assert "seat law could not complete" in message, message


# -- 5. rounding -------------------------------------------------------------------

def test_the_combined_votes_sum_to_the_total_where_rounding_each_alone_does_not():
    """Three shares of a third at 1,000 votes: 333 each is 999, not 1,000.

    The old conversion rounded each party on its own. The case is shown to
    discriminate first — the old expression loses a vote on it — and then
    `combined_votes` and the allocation's own record of its votes are held to
    the total. Largest remainder with equal fractions: the first party in the
    caller's order takes the vote.
    """
    shares = {"A": 1 / 3, "B": 1 / 3, "C": 1 / 3}
    old = {p: int(round(s * 1000)) for p, s in shares.items()}
    assert sum(old.values()) == 999, old          # the case can see the defect
    assert R.combined_votes(shares, 1000) == {"A": 334, "B": 333, "C": 333}
    result = R.reader_seats(shares, _GOOD_WINNERS, _toy_context(), 1000)
    assert result["ok"], result["errors"]
    assert sum(result["votes"].values()) == 1000, result["votes"]
    # Order owns the tie: reversed input, reversed winner.
    rev = dict(reversed(list(shares.items())))
    assert R.combined_votes(rev, 1000) == {"C": 334, "B": 333, "A": 333}


def test_the_combined_votes_sum_to_the_total_on_random_shares():
    import numpy as np
    rng = np.random.default_rng(1)
    old_missed = 0
    for n in range(2, 16):
        for _ in range(200):
            raw = rng.dirichlet([0.5] * n)
            shares = {f"P{i}": float(v) for i, v in enumerate(raw)}
            total = int(rng.integers(n * 10, 2_000_000))
            votes = R.combined_votes(shares, total)
            assert sum(votes.values()) == total, (shares, total, votes)
            # No party moves more than one vote from its exact share.
            scale = sum(shares.values())
            assert all(abs(votes[p] - shares[p] / scale * total) < 1
                       for p in shares), (shares, total, votes)
            old_missed += sum(int(round(s * total))
                              for s in shares.values()) != total
    # The population exercised the defect, not only the healthy case.
    assert old_missed, "no random case made per-party rounding miss the total"
    print(f"  per-party rounding missed the total in {old_missed} of "
          f"{14 * 200} random cases; largest remainder in none")


def test_a_share_sum_inside_tolerance_moves_no_vote_between_parties():
    """0.5 + 0.3 + 0.2 + 1e-7: scaled to one before counting."""
    shares = {"A": 0.5, "B": 0.3, "C": 0.2 + 1e-7}
    result = R.reader_seats(shares, _GOOD_WINNERS, _toy_context(), 1000,
                            tolerance=1e-6)
    assert result["ok"], result["errors"]
    assert result["votes"] == {"A": 500, "B": 300, "C": 200}


# -- 6. context and the Pyodide shape ---------------------------------------------

def test_the_context_comes_from_the_city_config_and_round_trips_as_json():
    run = _prepared()["2026"]
    context = R.context_from_run(_RunStub(run))
    assert context == _context(run)
    assert context["council"] == run["council"]
    assert len(context["wards"]) == run["wards_configured"]
    assert json.loads(json.dumps(context)) == context
    try:
        R.context_for(CITY, "2026", run["universe"], run["wards"][:-1])
    except ValueError as exc:
        assert "city config says" in str(exc)
    else:
        raise AssertionError("a short ward list was accepted")


class _RunStub:
    """What `context_from_run` reads off a `ModelRun`, from the pickled run."""

    def __init__(self, run):
        import cityconfig
        self.target = cityconfig.Target(cityconfig.load(CITY), run["target"])
        self.universe, self.wards = run["universe"], run["wards"]


_PYODIDE_PROBE = r'''
import builtins, io, json, sys
sys.path.insert(0, sys.argv[1])
for name in ("pandas", "openpyxl", "scipy"):
    sys.modules[name] = None          # importing it now raises ImportError
import reader_seats
def refuse(*a, **k):
    raise AssertionError(f"file opened at call time: {a[:1]}")
builtins.open = io.open = refuse
context = json.loads(sys.argv[2])
result = reader_seats.reader_seats({"A": 0.31, "B": 0.40, "C": 0.29},
                                   {w: "A" for w in context["wards"]},
                                   context, 1000)
assert result["ok"], result["errors"]
print(json.dumps(result["seats"], sort_keys=True))
'''


def test_it_imports_and_allocates_without_pandas_or_a_file_read():
    done = subprocess.run(
        [sys.executable, "-c", _PYODIDE_PROBE, str(ROOT / "src"),
         json.dumps(_toy_context())],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-3000:]
    assert json.loads(done.stdout) == {"A": {"ward": 5, "pr": 0, "total": 5},
                                       "B": {"ward": 0, "pr": 3, "total": 3},
                                       "C": {"ward": 0, "pr": 2, "total": 2}}
    # The probe can see: a module that opens a file at import is caught.
    leaky = _PYODIDE_PROBE.replace(
        "result = reader_seats", "open(reader_seats.__file__)\nresult = reader_seats")
    caught = subprocess.run(
        [sys.executable, "-c", leaky, str(ROOT / "src"), json.dumps(_toy_context())],
        cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert caught.returncode != 0 and "file opened at call time" in caught.stderr



# -- 7. the seat service (worker-api/seats-py) -------------------------------------

_SEATS_PY = ROOT / "worker-api" / "seats-py" / "src" / "entry.py"
_SYNC = ROOT / "worker-api" / "tools" / "sync_seats_py.mjs"


def _load_entry(with_code: bool = True):
    """entry.py, with the Workers runtime stubbed and src/ as its seat code."""
    import importlib.util
    import types
    workers = types.ModuleType("workers")
    workers.Response = object
    workers.WorkerEntrypoint = object
    saved = {k: sys.modules.get(k) for k in ("workers", "code_ref")}
    sys.modules["workers"] = workers
    if with_code:
        code_ref = types.ModuleType("code_ref")
        code_ref.CODE_REF = "ab" * 32
        sys.modules["code_ref"] = code_ref
    else:
        sys.modules["code_ref"] = None      # importing it raises ImportError
    try:
        spec = importlib.util.spec_from_file_location("seats_entry", _SEATS_PY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return module


def test_the_seat_service_passes_the_body_through_as_reader_seats_arguments():
    import inspect
    entry = _load_entry()
    positional = [n for n, prm in inspect.signature(R.reader_seats).parameters.items()
                  if prm.kind is prm.POSITIONAL_OR_KEYWORD]
    assert list(entry.ARGUMENTS) == positional, (entry.ARGUMENTS, positional)
    body = {"combined_shares": {"A": 0.31, "B": 0.40, "C": 0.29},
            "ward_winners": {w: "A" for w in _toy_context()["wards"]},
            "context": _toy_context(), "total_votes": 1000}
    # Through JSON, as the Worker receives it.
    status, payload = entry.answer(json.loads(json.dumps(body)))
    assert status == 200, payload
    assert payload == {"seats": {"A": 5, "B": 3, "C": 2}, "ward": {"A": 5},
                       "pr": {"B": 3, "C": 2}, "council_total": 10,
                       "majority": 6, "excessive": {"A": 2},
                       "code_ref": "ab" * 32}


def test_the_seat_service_answers_a_refusal_as_422_and_a_bad_body_as_400():
    entry = _load_entry()
    body = {"combined_shares": {"A": 0.7, "B": 0.3},
            "ward_winners": {**_GOOD_WINNERS, "W4": "C"},
            "context": _toy_context(), "total_votes": 1000}
    status, payload = entry.answer(body)
    assert status == 422 and "zero share" in " ".join(payload["errors"]), payload
    assert entry.answer({**body, "seats": {}})[0] == 400
    assert entry.answer([1, 2])[0] == 400
    # Not copied yet: the stub answer, which build.test.js relies on.
    assert _load_entry(with_code=False).answer(body)[0] == 501


_CLOSURE_PROBE = r'''
import json, os, sys
src = os.path.abspath(sys.argv[1])
sys.path.insert(0, src)
import reader_seats
print(json.dumps(sorted(os.path.basename(m.__file__) for m in list(sys.modules.values())
      if getattr(m, "__file__", None)
      and os.path.dirname(os.path.abspath(m.__file__)) == src)))
'''


def _files_mismatch(files, closure) -> list[str]:
    missing, extra = sorted(set(closure) - set(files)), sorted(set(files) - set(closure))
    return ([f"imported but not copied: {missing}"] if missing else []) + \
           ([f"copied but not imported: {extra}"] if extra else [])


def test_the_seat_service_copies_exactly_the_import_closure_of_reader_seats():
    import re
    text = _SYNC.read_text(encoding="utf-8")
    block = re.search(r"export const FILES = \[([^\]]*)\]", text)
    assert block, "FILES not found in sync_seats_py.mjs: the scan examines nothing"
    files = re.findall(r'"([^"]+\.py)"', block.group(1))
    done = subprocess.run([sys.executable, "-c", _CLOSURE_PROBE, str(ROOT / "src")],
                          cwd=ROOT, capture_output=True, text=True, timeout=300)
    assert done.returncode == 0, done.stderr[-3000:]
    closure = json.loads(done.stdout)
    # It looked: the closure holds the module and the seat law at least, and no
    # more modules than src/ has.
    assert {"reader_seats.py", "seats.py", "montecarlo.py"} <= set(closure)
    assert len(closure) < len(list((ROOT / "src").glob("*.py")))
    assert len(files) == len(set(files)), files
    assert not _files_mismatch(files, closure), _files_mismatch(files, closure)
    # It can see, both ways, and goes quiet again.
    assert _files_mismatch(files[1:], closure)
    assert _files_mismatch(files + ["pools.py"], closure)
    assert not _files_mismatch(list(reversed(files)), closure)

if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
