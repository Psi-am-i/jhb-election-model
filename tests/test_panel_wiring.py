"""The cross-file wiring no single-file change could make, and its two defects.

Four agents landed Phase 1 on disjoint files. Two of the repairs are only real
once something downstream CALLS them, and nothing in either agent's grant could
do the calling. This module guards the calls.

**#13 — the held universe.** `score.hold_universe` and `score_seats(universe=)`
exist and are tested (``tests/test_scored_universe.py``). They change no number
in the panel until ``compare_history.run_city_year`` passes one, and passing one
requires the references to be RUN before the model is SCORED, because the held
set is built out of every forecaster's claims. That re-order is the risk and the
order is therefore what is asserted.

**#12 — one definition of "arrived from nothing".** There were three, and they
reached different call sites: ``compare_history._actual_seats`` tested against
the MODEL'S OWN INDEX, ``diagnose`` and ``backtest.main`` against the preceding
NPE unfiltered, ``compare_history._npe_baseline`` against the same filtered to
shares above zero. Only the last is a registered definition
(``pools.ARRIVAL_DEFINITIONS["ARRIVED_VS_NATIONAL"]``). All four sites now go
through ``backtest.arrival_baseline``.

⛔ **WHAT THIS FILE DOES NOT CLAIM.** Nothing here says the arrival LABEL is a
good one. It is ``max(newcomers, key=seats)``, chosen with the outcome in hand,
and ``backtest.arrival_group_score`` exists precisely because of that (§1.133).
Routing three call sites through one definition makes the answer consistent; it
does not make it fair.

Every guard below is either a CONSTRUCTED fixture put through the real function,
or a scan of live state carrying a constructed violation and a two-sided
population bound (``_support.scanned``). Nothing here asserts a docstring, and
nothing asserts a number this model produced.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, SRC, run_module, scanned  # noqa: E402

import backtest as B  # noqa: E402
import compare_history as C  # noqa: E402
import pools  # noqa: E402
import score as S  # noqa: E402

COMPARE_SRC = (SRC / "compare_history.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# #13 — the held universe, and the re-order that makes it possible
# ---------------------------------------------------------------------------


def _score_seats_calls(source: str, inside: str) -> list[ast.Call]:
    """Every `score_seats(...)` call inside the named function."""
    fn = next(n for n in ast.walk(ast.parse(source))
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              and n.name == inside)
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call)
            and ast.unparse(n.func).split(".")[-1] == "score_seats"]


def _hold_universe_calls(source: str, inside: str) -> list[ast.Call]:
    fn = next(n for n in ast.walk(ast.parse(source))
              if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
              and n.name == inside)
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call)
            and ast.unparse(n.func).split(".")[-1] == "hold_universe"]


# A working `run_city_year` in miniature, in the shape the real one had BEFORE
# the fix: the model is scored first on its own columns, the references are run
# and scored afterwards, and no universe is held. Every detector below is run
# over this as well as over the real file — a detector that has not caught
# something has proved nothing about the file it is silent on.
VIOLATION_UNHELD = '''
def run_city_year(city, year):
    scored = S.score_seats(run.seat_draws, actual, entrant_actual=e)
    for name in scored_opponents():
        seat_draws, ward_draws = BM.run_with_wards(name, ctx)
        bench = S.score_seats(seat_draws, actual, entrant_actual=e)
'''

# The subtler one: a universe IS held, and it is built AFTER the model has
# already been scored — so the model's own score is still taken on its own
# columns and only the references are held. This is what a careless re-order
# produces, it reads correct in a diff, and it is the whole reason the ORDER is
# asserted rather than the presence of the keyword.
VIOLATION_LATE_HOLD = '''
def run_city_year(city, year):
    scored = S.score_seats(run.seat_draws, actual, entrant_actual=e)
    held = S.hold_universe([run.seat_draws], actual, e, fixed=reference)
    for name in scored_opponents():
        bench = S.score_seats(sd, actual, entrant_actual=e, universe=held)
'''


def test_every_score_seats_in_the_panel_holds_the_universe():
    """Both call sites pass `universe=`, and the detector is shown to work.

    ⛔ `universe=` AND NOT `parties=`. They are different arguments —
    `score_seats` refuses both at once for exactly this reason — and `parties`
    fixes column ORDER over a set the forecaster still chooses. Passing the
    wrong one leaves the denominator drifting while reading, in a diff, like the
    fix.
    """
    calls = _score_seats_calls(COMPARE_SRC, "run_city_year")

    # (1) IT LOOKED. Two forecaster scores in this function — the model and each
    # reference — and the bound is two-sided against the number of `score_seats`
    # calls in the whole module, so a call added outside this function or a call
    # lost from inside it both move the ratio.
    module_calls = [n for n in ast.walk(ast.parse(COMPARE_SRC))
                    if isinstance(n, ast.Call)
                    and ast.unparse(n.func).split(".")[-1] == "score_seats"]
    scanned(calls, of=module_calls, low=1.0, high=1.0,
            what="`score_seats` calls inside `run_city_year`",
            denominator="`score_seats` calls anywhere in compare_history.py")
    assert len(calls) == 2, (
        f"{len(calls)} `score_seats` calls in `run_city_year`, expected two: "
        f"the model's and the references'. If a third forecaster is scored "
        f"here it must be held too, and this count is how that gets noticed.")

    for call in calls:
        kwargs = {k.arg for k in call.keywords}
        assert "universe" in kwargs, (
            f"`score_seats` at compare_history.py:{call.lineno} does not pass "
            f"`universe=`, so `seat_matrix` chooses that forecaster's columns "
            f"from its own draws and the summed scores in this row are over "
            f"different denominators. `score.comparable` is the predicate; "
            f"`score.hold_universe` builds the set.")
        assert "parties" not in kwargs, (
            f"`score_seats` at compare_history.py:{call.lineno} passes "
            f"`parties=`, which fixes column ORDER and not the SET.")

    # (2) IT CAN SEE. The same detector over a constructed pre-fix function must
    # find both calls and report neither as held.
    bad = _score_seats_calls(VIOLATION_UNHELD, "run_city_year")
    assert len(bad) == 2 and not any("universe" in {k.arg for k in c.keywords}
                                     for c in bad), (
        "the detector does not see an unheld `score_seats` call, so its silence "
        "about compare_history.py above means nothing")


def test_the_references_are_run_before_the_model_is_scored():
    """THE RE-ORDER, ASSERTED AS AN ORDER AND NOT AS A COMMENT.

    `hold_universe` takes every forecaster's claims, so the references have to
    have been RUN before it is called, and it has to be called before ANY
    `score_seats` — including the model's. A held set built after the model's
    score holds only the references, which is a comparison over two column sets
    wearing the fix's diff.

    The invariant is positional, so it is asserted positionally: every
    `run_with_wards` line, then the `hold_universe` line, then every
    `score_seats` line.
    """
    fn = next(n for n in ast.walk(ast.parse(COMPARE_SRC))
              if isinstance(n, ast.FunctionDef) and n.name == "run_city_year")
    runs = [n.lineno for n in ast.walk(fn) if isinstance(n, ast.Call)
            and ast.unparse(n.func).split(".")[-1] == "run_with_wards"]
    holds = [n.lineno for n in _hold_universe_calls(COMPARE_SRC, "run_city_year")]
    scores = [n.lineno for n in _score_seats_calls(COMPARE_SRC, "run_city_year")]

    # (1) IT LOOKED: all three populations are non-empty, and there is exactly
    # ONE held set per city-year. Two would mean two answers to "which columns
    # is this row scored on", which is the state being removed.
    assert runs, "no `run_with_wards` call in `run_city_year`"
    assert len(holds) == 1, (
        f"{len(holds)} `hold_universe` calls in `run_city_year`. One row is "
        f"scored on one column set or it is not one comparison.")
    assert scores, "no `score_seats` call in `run_city_year`"

    assert max(runs) < holds[0], (
        f"`run_with_wards` last appears at line {max(runs)} and `hold_universe` "
        f"is called at {holds[0]}. The held set is built from every "
        f"forecaster's claims, so a reference run afterwards contributes none "
        f"of its columns to it and is then scored on a set that forgives its "
        f"phantom mass.")
    assert holds[0] < min(scores), (
        f"`hold_universe` is called at line {holds[0]} and a `score_seats` "
        f"call precedes it at {min(scores)}. A forecaster scored before the "
        f"universe is held is scored on its own columns, whatever the other "
        f"call sites do.")

    # (2) IT CAN SEE. The constructed late-hold function passes the keyword
    # check in the test above and must fail this one.
    late_holds = [n.lineno for n in _hold_universe_calls(VIOLATION_LATE_HOLD,
                                                         "run_city_year")]
    late_scores = [n.lineno for n in _score_seats_calls(VIOLATION_LATE_HOLD,
                                                        "run_city_year")]
    assert late_holds and late_scores
    assert not late_holds[0] < min(late_scores), (
        "the order detector does not catch a universe held after the model was "
        "already scored, which is the failure this test exists for")


def test_holding_the_universe_is_what_makes_two_forecasters_comparable():
    """The positive control, on the real scorer, with constructed forecasters.

    Two forecasters whose claims barely overlap. Scored the way the panel scored
    them before this change they carry different column sets and
    `score.comparable` says so; scored on `hold_universe` they carry one set.

    ⛔ AND THE NUMBERS THAT MUST NOT MOVE ARE ASSERTED TOO. `hold_universe`'s
    docstring claims CRPS and energy are invariant to the padding columns,
    because a both-zero column contributes exactly nothing to either. That is
    the claim that makes the held score quotable, so it is checked here rather
    than taken from the docstring.
    """
    actual = {"ANC": 100, "DA": 80, "SMALL": 4}
    model = [{"ANC": 98, "DA": 82, "SMALL": 3, "PHANTOM": 1} for _ in range(20)]
    bench = [{"ANC": 104, "DA": 78} for _ in range(20)]

    own_model = S.score_seats(model, actual)
    own_bench = S.score_seats(bench, actual)
    loose = S.comparable({"model": own_model, "bench": own_bench})
    assert loose["comparable"] is False, (
        "the fixture no longer separates the two forecasters' column sets, so "
        "the held comparison below is not evidence of anything")
    assert loose["mismatch"], loose

    held = S.hold_universe([model, bench], actual, fixed=["FIXED_ONLY"])
    assert "PHANTOM" in held and "SMALL" in held and "FIXED_ONLY" in held, held
    held_model = S.score_seats(model, actual, universe=held)
    held_bench = S.score_seats(bench, actual, universe=held)
    tight = S.comparable({"model": held_model, "bench": held_bench})
    assert tight["comparable"] is True, tight
    assert tight["key"] == S.universe_key(held)

    # The invariance, as numbers. CRPS is a sum over columns and energy a mean
    # over draw-pairs of a Euclidean norm; neither can move when a coordinate
    # that is zero in the truth and zero in every draw is appended.
    assert abs(held_model["crps"]["total"] - own_model["crps"]["total"]) < 1e-9
    assert abs(held_bench["crps"]["total"] - own_bench["crps"]["total"]) < 1e-9
    assert abs(held_model["energy"] - own_model["energy"]) < 1e-9
    assert abs(held_bench["energy"] - own_bench["energy"]) < 1e-9
    # Nobody's own claims were dropped, which is what makes the difference a
    # difference rather than a mutual amnesty.
    assert not held_model["dropped_claims"] and not held_bench["dropped_claims"]


def test_the_reference_alone_is_not_a_legal_held_set():
    """`fixed` on its own deletes a real seat-winner, and `score_seats` refuses.

    The scorer agent's finding, pinned at the wiring: seven parties across the
    committed panel won seats while outside `reference_universe`, and scoring on
    `reference` alone would delete those columns for BOTH forecasters at once —
    forgiving whichever was worse on them, which is this model's own failure
    mode. `hold_universe` unions the seat-winners back in; this asserts that the
    union is load-bearing and not decorative.
    """
    actual = {"ANC": 100, "OUTSIDER": 6}
    draws = [{"ANC": 100} for _ in range(10)]
    reference = ["ANC", "DA"]          # OUTSIDER has neither record nor slate

    try:
        S.score_seats(draws, actual, universe=reference)
    except ValueError as exc:
        assert "OUTSIDER" in str(exc), exc
    else:
        raise AssertionError(
            "score_seats accepted a universe that omits a party which actually "
            "won seats, so scoring on `reference` alone would silently delete a "
            "real error from every forecaster's sum at once")

    held = S.hold_universe([draws], actual, fixed=reference)
    assert "OUTSIDER" in held and "DA" in held, held
    scored = S.score_seats(draws, actual, universe=held)
    assert set(scored["parties"]) == set(held)


# ---------------------------------------------------------------------------
# #12 — one definition of "arrived from nothing"
# ---------------------------------------------------------------------------


class _FakeTarget:
    """A target whose preceding NPE file may or may not exist. Constructed."""

    def __init__(self, previous_npe, filename):
        self.previous_npe = previous_npe
        self.year = "2021"
        self._filename = filename

    def results(self, year):
        return self._filename


def test_the_arrival_baseline_is_the_registered_definition():
    """ONE definition, and it is the one the register already names.

    ``ARRIVED_VS_NATIONAL`` — *"local share > 0 and preceding-NPE share <= 0"* —
    is what `arrival_baseline` implements, and the answer to "which population
    is this?" is a lookup rather than a sixth entry. The register is asserted to
    still carry the name, because a definition that is named where it does not
    exist is the stale-register fault CLAUDE.md §4 puts worst.
    """
    d = pools.ARRIVAL_DEFINITIONS["ARRIVED_VS_NATIONAL"]
    assert "preceding-NPE" in d.predicate and "IND" in d.predicate, d.predicate

    # The predicate, on a constructed baseline: presence decides, and presence
    # is decided at a share strictly above zero.
    base = {"ANC": 0.55, "DA": 0.27, "GHOST": 0.0}
    seats = {"ANC": 140, "DA": 90, "NEW": 7, "SMALLER_NEW": 3}
    assert B.entrant_actual_for(seats, {p: v for p, v in base.items() if v > 0}) \
        == "NEW"
    # A zero-share row is NOT a baseline, and the two readings of the same file
    # genuinely differ — which is why the filter is kept even though it removes
    # nothing on today's files.
    seats_with_ghost = {**seats, "GHOST": 9}
    assert B.entrant_actual_for(
        seats_with_ghost, {p: v for p, v in base.items() if v > 0}) == "GHOST"
    assert B.entrant_actual_for(seats_with_ghost, base) == "NEW", (
        "the filtered and unfiltered readings of a preceding NPE must be able "
        "to disagree, or the choice between them is not a choice")

    # The tie-break is a stated rule, not an iteration order.
    tie = {"AAA": 5, "ZZZ": 5}
    assert B.entrant_actual_for(tie, {}) == "ZZZ"


def test_an_unreadable_baseline_relabels_nothing_rather_than_everything():
    """⛔ EMPTY AND UNREACHABLE ARE DIFFERENT FACTS, AND ONE OF THEM IS RUINOUS.

    An empty baseline does not mean "no party had a record". It means EVERY
    party arrived — so `entrant_actual_for` would relabel the model's generic
    ENTRANT onto the largest party in the council, handing the model a free
    correct label on the ANC. `arrival_baseline` therefore returns ``None`` and
    `entrant_actual_for_target` returns ``None``: with no label the ENTRANT
    column stays in the scored universe as phantom mass and is penalised, which
    is the direction a scorer must err in.

    Both halves are asserted. A one-sided test would pass against a function
    wired to return ``None`` always.
    """
    seats = {"ANC": 140, "DA": 90, "NEW": 7}
    data_dir = ROOT / "data" / "raw" / "elections"

    # No preceding NPE in the calendar at all.
    none_target = _FakeTarget(None, "does-not-matter.csv")
    assert B.arrival_baseline(none_target, data_dir) is None
    assert B.entrant_actual_for_target(none_target, seats, data_dir) is None

    # A preceding NPE that is named and whose file is not on disk.
    missing = _FakeTarget("2019", "no-such-file-for-this-test.csv")
    assert B.arrival_baseline(missing, data_dir) is None
    assert B.entrant_actual_for_target(missing, seats, data_dir) is None

    # THE POSITIVE CONTROL, and it is what stops the two assertions above from
    # being satisfied by a function that always returns None: an EMPTY baseline
    # — the value the failure mode would have produced — makes the largest party
    # in the council the arrival. That is the outcome being refused, shown to be
    # reachable by the same arithmetic.
    assert B.entrant_actual_for(seats, {}) == "ANC", (
        "an empty baseline must make every party an arrival; if it does not, "
        "the refusal above is guarding against nothing")


def test_nothing_outside_backtest_chooses_its_own_arrival_baseline():
    """THE POPULATION: every module that decides who arrived. Both directions.

    Three sites built three baselines. The claim is that exactly one module now
    defines the operation and every other site calls the wrapper, so the scan is
    over `src/*.py` and the assertion is bidirectional: nobody outside
    `backtest.py` may call `entrant_actual_for` directly, AND the consumers must
    actually call `entrant_actual_for_target` — an absence check alone passes on
    a file that has stopped computing arrivals at all.
    """
    files = sorted(SRC.glob("*.py"))
    scanned(files, of=files, low=1.0, high=1.0,
            what="source modules scanned for a hand-built arrival baseline",
            denominator="`.py` files in src/")

    offenders = []
    consumers = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = {ast.unparse(n.func).split(".")[-1] for n in ast.walk(tree)
                 if isinstance(n, ast.Call)}
        if "entrant_actual_for_target" in names:
            consumers.append(path.name)
        if path.name != "backtest.py" and "entrant_actual_for" in names:
            offenders.append(path.name)

    assert not offenders, (
        f"{offenders} call `entrant_actual_for` directly, which means each of "
        f"them decides for itself what 'has a baseline' means — the state fix "
        f"#12 removes. Call `backtest.entrant_actual_for_target`.")
    # The other direction: the consumers are there, and they are the ones
    # expected. A silent loss of the call is a module that has stopped
    # relabelling, which scores the arrival machinery as a miss and a phantom
    # at once (`tests/test_regressions.py`).
    assert set(consumers) >= {"compare_history.py", "diagnose.py"}, consumers

    # IT CAN SEE: the same detector over a constructed module that builds its
    # own baseline must name it.
    violation = ast.parse(
        "base = {p: 1.0 for p in run.index}\n"
        "e = B.entrant_actual_for(actual_seats, base)\n")
    seen = {ast.unparse(n.func).split(".")[-1] for n in ast.walk(violation)
            if isinstance(n, ast.Call)}
    assert "entrant_actual_for" in seen, (
        "the call detector does not see a direct `entrant_actual_for` call, so "
        "its silence about src/ above means nothing")


def test_the_panel_does_not_pass_an_empty_baseline_to_the_arrival_score():
    """The same fail-closed rule at the arrival channel, one layer up.

    `arrival_group_score` selects its realised side as
    ``[p for p in actual_shares if p not in base_city]``, so an empty baseline
    reports the WHOLE BALLOT as an arrival and the realised arrival mass as 100%
    of the city. `run_city_year` must therefore branch on ``None`` rather than
    pass whatever it got.
    """
    fn = next(n for n in ast.walk(ast.parse(COMPARE_SRC))
              if isinstance(n, ast.FunctionDef) and n.name == "run_city_year")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call)
             and ast.unparse(n.func).split(".")[-1] == "arrival_group_score"]
    assert len(calls) == 1, f"{len(calls)} `arrival_group_score` calls"
    base_arg = ast.unparse(calls[0].args[-1])
    assert base_arg.isidentifier(), (
        f"the arrival baseline is passed as the expression `{base_arg}`, which "
        f"cannot have been tested for None before it was passed")
    tested = {ast.unparse(n.left) for n in ast.walk(fn)
              if isinstance(n, ast.Compare)
              and any(isinstance(o, (ast.Is, ast.IsNot)) for o in n.ops)}
    assert base_arg in tested, (
        f"`{base_arg}` reaches `arrival_group_score` without being compared to "
        f"None. An unreadable preceding NPE would then be spent as an empty "
        f"one, and every party on the ballot would be scored as an arrival.")

    # IT CAN SEE: the realised-side selection really is membership-based, so an
    # empty baseline really would sweep the whole ballot in.
    shares = {"ANC": 0.55, "DA": 0.27, "NEW": 0.02}
    assert [p for p in shares if p not in {}] == list(shares)
    assert [p for p in shares if p not in {"ANC": 0.5, "DA": 0.3}] == ["NEW"]


def test_the_ground_truth_no_longer_depends_on_the_forecast():
    """`_actual_seats` must not take the run. It is what happened, not a score.

    The old signature took a `ModelRun` for one purpose: to read `run.index` as
    the arrival baseline. A function that needs the forecast in order to say
    what the result was couples the two in the one place the panel relies on
    them being independent — change a pool seed and the panel changes its mind
    about which party arrived.
    """
    fn = next(n for n in ast.walk(ast.parse(COMPARE_SRC))
              if isinstance(n, ast.FunctionDef) and n.name == "_actual_seats")
    args = [a.arg for a in fn.args.args]
    assert "run" not in args, (
        f"`_actual_seats{tuple(args)}` still takes the model run. The only "
        f"thing it was ever read for is the arrival baseline, which is now "
        f"`backtest.arrival_baseline`.")
    assert args == ["target", "data_dir"], args
    # And no caller is still handing it one — a stale third argument would be a
    # TypeError at panel time, sixteen worker processes deep.
    for call in [n for n in ast.walk(ast.parse(COMPARE_SRC))
                 if isinstance(n, ast.Call)
                 and ast.unparse(n.func).split(".")[-1] == "_actual_seats"]:
        assert len(call.args) == 2, ast.unparse(call)


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
