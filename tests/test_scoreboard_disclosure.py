"""The scoreboard's DISCLOSURE layer: what it declares about its own numbers.

Four blind pollsters reviewed a Johannesburg backtest and found the model more
honest than most published forecasts — and the discipline stopping at the
harness door. `compare_history` computed, or was handed, the right things and
then discarded them, never asked for them, or described them wrongly:

    F1   `backtest.contaminated` and `backtest.in_sample_banner` existed, were
         correct, and were called by nothing in this file — so the panel that
         arbitrates every decision in this project declared no provenance.
    F6   the arrival referee tested the POST-relabel index for the generic
         `ENTRANT` slot, by which point the slot had been renamed onto a real
         party. It was blind exactly where the thing it hunts happens.
    F8   a crashed city-year landed in neither `results` nor `excluded`, so it
         was stamped into the manifest as "not selected by --city/--target" —
         a declared reason that was false — and the process exited 0.
    F9   five narrative claims were printed as literal prose from a different,
         larger panel: a Gauteng group label, "loses at Mangaung", two named
         parties and a leverage share, a PIT-saturation count "across the nine
         city-years", and a dilution figure attributed to the wrong population.
    F10  `last-lge` and `uniform-swing` are deterministic — their CRPS equals
         their coherent seat error exactly — and a CRPS margin over them was
         printed as though it said something about uncertainty.

**Every test here is a guard of the open-spy shape** (`tests/_support.py`,
`election_files_read`): it asserts the bad thing is ABSENT *and* that the
mechanism ran at all, so a silently-inert detector cannot pass. Where the
detector is a pure predicate the positive control is mechanical — a constructed
violation pushed through the same code — and that is how most of these are
written. The inputs are CONSTRUCTED, never a passing state of the real tree, so
no test here expires the day the panel happens to be clean.

⚠️ The artefact-reading tests skip LOUDLY on an artefact written before this
change rather than passing vacuously. Re-run `src/compare_history.py`.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import backtest as B  # noqa: E402
import cityconfig  # noqa: E402
import compare_history as C  # noqa: E402


# ---------------------------------------------------------------------------
# fixtures — constructed, never observed
# ---------------------------------------------------------------------------

def _run(universe, seeds=None, prob=0.25, share=(0.01, 0.04, 0.12)):
    """The three attributes :func:`compare_history._reconcile_arrival` reads."""
    return type("_Run", (), {
        "scenario": {"entrant_prob": prob, "entrant_share": list(share),
                     "pool_seeds": dict(seeds or {})},
        "universe": list(universe)})()


def _board(**over):
    """A `41_guards`-shaped board, with distinctive non-zero values.

    Deliberately NOT a copy of montecarlo's literal: the values are chosen to be
    individually recognisable in rendered output, so a test can prove a specific
    counter reached a specific cell rather than that *some* number did.
    """
    board = {
        "ipf_balances": 1000, "ipf_failures": 427,
        "cap_undershoots": 3, "cap_moved": 0.001234,
        "ipf_clipped": {"ANC": 12}, "ipf_headroom": {"ANC": 0.97},
        "bounds_violations": {"EFF": 7}, "bounds_checked": 500,
        "excessive_draws": 11, "overhang_count": {"ANC": 5},
        "solve_calls": 800, "solve_rounds": 32000,
        "solve_nonconvergent": 800, "solve_nonconvergent_reachable": 19,
        "solve_worst_gap": 0.51, "solve_worst_gap_reachable": 0.07,
        "solve_unreachable_parties": 4,
        "solve_floor_injected_mean": 0.004321,
        "solve_floor_injected_worst": 0.09,
        "solve_identity_hits": 0,
    }
    board.update(over)
    return board


def _guard_run(board=None, roster=("published", 41, ())):
    """A `ModelRun`-shaped stub carrying only what `_guard_block` reads."""
    state, size, dropped = roster
    return type("_GuardRun", (), {
        "guards": dict(board) if board is not None else {},
        "roster_state": state, "roster_size": size,
        "roster_dropped": list(dropped)})()


def _slot_expectation(prob=0.25, share=(0.01, 0.04, 0.12)) -> float:
    """The generic slot's mean, computed here rather than typed.

    A test that hard-codes 0.014167 passes when the production formula changes
    to something else that also yields 0.014167, and fails for the wrong reason
    when the scenario defaults move. Recomputing from the same inputs the
    fixture supplies asserts the ARITHMETIC, not a remembered constant.
    """
    return prob * (sum(share) / 3.0)


def _record(year="2011", slug="joburg", city="Johannesburg", *, seats=8,
            saturate=False, seed=7, read=None, contaminated=None,
            opponents=None, reconciliation=None):
    """One city-year record in the shape `render` consumes.

    The seat draws are Poisson with a known mean; `saturate=True` pushes one
    column's truth above every draw, which is the zero-probability failure that
    produces a PIT of exactly 1.0 and makes a band's probit-SD a function of
    `_probit`'s clip.
    """
    rng = np.random.default_rng(seed)
    parties = [f"P{j}" for j in range(seats)]
    draws = [{} for _ in range(400)]
    actual = {}
    for j, party in enumerate(parties):
        column = rng.poisson(6, size=400)
        for d, value in zip(draws, column):
            d[party] = int(value)
        actual[party] = int(rng.poisson(14 if j == 0 else 6))
    if saturate:
        actual[parties[-1]] = int(max(d[parties[-1]] for d in draws) + 3)
    actual_pr = {p: 0.40 - 0.03 * j for j, p in enumerate(parties)}
    bands = {b: {"n": 2, "signed_pp": 1.0, "abs_pp": 2.0, "seats_at_stake": 3}
             for b in C.BAND_LABELS}
    bands["phantom"] = {"n": 1, "pp": 0.5, "top": [("X", 0.5)]}
    return {
        "city": city, "slug": slug, "year": year, "council": 270,
        "votes": [], "pr_mae": 1.0, "ward_mae": 1.0, "pr_mae_median": 1.0,
        "ward_mae_median": 1.0, "bands": bands, "seats": {},
        "seat_abs_err": 50, "seat_abs_err_coherent": 60, "median_sum": 250,
        "crps": 40.0,
        "calibration": C.calibration_columns(draws, actual, None, seed,
                                             actual_pr=actual_pr,
                                             reference=parties),
        "constants_read": (read if read is not None
                           else {"pools": ["montecarlo:run_model"]}),
        "contaminated": (contaminated if contaminated is not None
                         else ["pools"]),
        "in_sample": bool(contaminated if contaminated is not None else True),
        "arrival_reconciliation": reconciliation,
        "opponents": opponents if opponents is not None else {
            "last-lge": {"crps": 52.0, "seat_abs_err_coherent": 52, "wards": {}},
            "uniform-swing": {"crps": 70.0, "seat_abs_err_coherent": 70,
                              "wards": {}},
            "prior-lge-noise": {"crps": 48.5, "seat_abs_err_coherent": 66,
                                "wards": {}}},
    }


def _artefact():
    """The committed scoreboard, or a loud skip."""
    path = ROOT / "data" / "processed" / "history.json"
    if not path.exists():
        skip(f"{path} is not on disk; run src/compare_history.py")
    return C.load_history(path)


# ---------------------------------------------------------------------------
# F1 — the scoreboard declares its own contamination
# ---------------------------------------------------------------------------

def test_the_in_sample_verdict_is_derived_from_FITTED_ON_and_not_typed():
    """The implicated keys come from the run's own read log, dynamically.

    ⚠️ **This is not an all-clear mechanism and must not be read as one.**
    `montecarlo.note_constant(scenario, "pools")` fires unconditionally and
    `FITTED_ON["pools"]` lists 2011/2016/2021, so every target this harness can
    run is in-sample already and said so inside `backtest.py`'s CLI. What was
    missing from `compare_history` is the DISCLOSURE — which constants, read by
    what, on which rows.

    The key is chosen from `FITTED_ON` **at run time** rather than named here:
    that table is being extended, and a test that pins `"pools"` would go stale
    the moment somebody adds or removes an entry.
    """
    year = "2011"
    dirty_keys = sorted(k for k, (years, _why) in B.FITTED_ON.items()
                        if any(y >= year for y in years))
    clean_keys = sorted(k for k, (years, _why) in B.FITTED_ON.items()
                        if not years)
    assert dirty_keys and clean_keys, (
        f"backtest.FITTED_ON no longer contains both a key implicated at "
        f"{year} and a key that reads no result ({dirty_keys=}, {clean_keys=}). "
        f"This test needs one of each to tell the two verdicts apart.")

    key, clean = dirty_keys[0], clean_keys[0]
    dirty_row = _record(year=year, read={key: ["montecarlo:run_model"]},
                        contaminated=[key])
    clean_row = _record(year=year, slug="tshwane", city="Tshwane",
                        read={clean: ["levels:contestation"]}, contaminated=[])

    assert C._in_sample_verdict([dirty_row])["verdict"] == "IN-SAMPLE"
    assert C._in_sample_verdict([clean_row])["verdict"] == "OUT-OF-SAMPLE (MEASURED)"

    both = C._in_sample_verdict([dirty_row, clean_row])
    assert both["verdict"] == "IN-SAMPLE", (
        "one contaminated row among clean ones must make the PANEL in-sample; "
        "a verdict that reports the majority hides the row that matters")
    assert both["rows_in_sample"] == [f"joburg:{year}"], both["rows_in_sample"]
    assert both["rows_out_of_sample"] == [f"tshwane:{year}"]
    assert both["keys"] == {key: [f"joburg:{year}"]}, both["keys"]

    # 0 — SCANNED THE RIGHT THING, BOTH DIRECTIONS. The keys reported must be
    # exactly the implicated subset of what the run read: no key invented, and
    # no implicated key dropped. The register guard's one-directional check is
    # the cautionary case (CLAUDE.md 4).
    assert set(both["keys"]) <= set(B.FITTED_ON), (
        "the verdict named a key that is not in backtest.FITTED_ON")
    assert set(both["keys"]) == set(dirty_row["contaminated"]), (
        "the verdict's key map and the row's own `contaminated` list disagree")


def test_an_artefact_without_provenance_is_unknown_and_not_clean():
    """A missing record and a negative record are different facts.

    An older `history.json` has no `contaminated` key on any row. Reporting that
    as OUT-OF-SAMPLE would be the "empty record vs unreachable record" defect
    this repository has already got wrong twice about one bug.
    """
    old = _record()
    del old["contaminated"]
    del old["constants_read"]
    verdict = C._in_sample_verdict([old])
    assert verdict["verdict"].startswith("UNKNOWN"), verdict["verdict"]
    assert verdict["rows_unknown"] == ["joburg:2011"]
    assert not verdict["rows_out_of_sample"], (
        "a row with no provenance record was counted as out-of-sample. That is "
        "an all-clear issued on the strength of a missing field.")


def test_the_banner_is_printed_above_the_tables_and_cannot_go_missing():
    """CONSTRUCTED CONTAMINATED RUN — the positive control for F1.

    `backtest.in_sample_banner` renders a rule of exclamation marks and the
    words "IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES". If that text is
    absent from a report built from a contaminated row, the banner has gone
    missing however healthy the verdict field looks.

    It must also appear ABOVE the headline table, for the reason the banner's
    own docstring gives: nobody reads a seat MAE and then checks the provenance.
    """
    year = "2011"
    key = sorted(k for k, (years, _w) in B.FITTED_ON.items()
                 if any(y >= year for y in years))[0]
    text = C.render([_record(year=year, read={key: ["montecarlo:run_model"]},
                             contaminated=[key])])

    assert "IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES" in text, (
        "the in-sample banner is not in the rendered report. It is the one "
        "thing standing between a reader and taking a fit statistic for a "
        "forecast score.")
    assert text.index("IN-SAMPLE — THESE ARE NOT") < text.index("## Headline"), (
        "the banner is printed BELOW the headline table. A caveat after the "
        "number is a caveat nobody reads.")
    assert key in text, f"the banner does not name the implicated constant {key}"

    # NEGATIVE CONTROL: a clean row must not raise the banner. Without this the
    # assertion above passes for a report that prints the warning always, which
    # is furniture and teaches the eye to skip it.
    clean = sorted(k for k, (years, _w) in B.FITTED_ON.items() if not years)[0]
    clean_text = C.render([_record(year=year, read={clean: ["levels:x"]},
                                   contaminated=[])])
    assert "THESE ARE NOT OUT-OF-SAMPLE SCORES" not in clean_text, (
        "the in-sample banner printed for a run that read no contaminated "
        "constant, so it is unconditional and says nothing")
    assert "OUT-OF-SAMPLE (MEASURED)" in clean_text


def test_the_manifest_carries_the_in_sample_verdict():
    """A reader of `history.json` must not have to infer it from the rows."""
    manifest, records = _artefact()
    if "in_sample" not in manifest:
        skip("this history.json predates the in-sample manifest block; re-run "
             "src/compare_history.py to produce a scoreboard that declares it")
    block = manifest["in_sample"]
    assert block["verdict"] in ("IN-SAMPLE", "OUT-OF-SAMPLE (MEASURED)") or \
        block["verdict"].startswith("UNKNOWN"), block["verdict"]
    # The manifest must agree with the rows it was derived from.
    assert block == C._in_sample_verdict(records), (
        "the manifest's in-sample verdict and the one recomputed from the "
        "records disagree, so one of them is stale")


# ---------------------------------------------------------------------------
# F6 — the arrival referee sees the slot before the relabel hides it
# ---------------------------------------------------------------------------

def test_the_generic_slot_is_detected_before_the_relabel_renames_it():
    """⛔ THE 2011-SHAPED CASE: a slot present pre-relabel, renamed after.

    This is the defect in miniature. The model holds a generic `ENTRANT`
    column; a party arrives; `backtest.relabel_run` renames ENTRANT onto it;
    and the referee then asks the POST-relabel universe whether an `ENTRANT`
    column exists. It never can.

    Measured on the committed twenty-four-row artefact before the repair: the
    flag read true at 4 of 24 rows — exactly the 2011 city-years where NO party
    arrived, so the relabel never fired. At the four 2011 rows where it did
    fire, `unexplained` read 0.01507 / 0.01410 / 0.01411 / 0.01493 against a
    slot expectation of 0.014167. **The mass filed as unexplained was the slot
    the detector could not see.**
    """
    slot = _slot_expectation()
    drawn = 0.0148
    post = ["ANC", "DA", "AIC"]              # ENTRANT renamed onto AIC
    pre = ("ANC", "DA", "ENTRANT")           # what the model actually built

    fixed = C._reconcile_arrival(_run(post), {"mass_mean": drawn}, pre)
    assert fixed["generic_slot_present"] is True, (
        "the generic slot was not detected from the pre-relabel universe, so "
        "the repair is not in place")
    assert abs(fixed["generic_slot_expectation"] - slot) < 1e-12
    assert abs(fixed["unexplained"] - (drawn - slot)) < 1e-12
    assert abs(fixed["unexplained"]) < 0.001, (
        f"unexplained is {fixed['unexplained']:.5f}. In this case the slot IS "
        f"the whole arrival forecast, so the residual must collapse to about "
        f"zero; a residual near {drawn:.4f} means the slot was not counted.")

    # ⛔ THE MUTATION. Reproduce the defect on demand by handing it the
    # POST-relabel universe — the exact input the code used to read. If this
    # does not come back blind, the test is passing for a reason other than the
    # fix and would pass with the fix reverted.
    blind = C._reconcile_arrival(_run(post), {"mass_mean": drawn}, post)
    assert blind["generic_slot_present"] is False
    assert abs(blind["unexplained"] - drawn) < 1e-12, (
        "the constructed defect did not reproduce, so this test cannot "
        "distinguish the repaired detector from the blind one")
    assert blind["unexplained"] != fixed["unexplained"], (
        "the pre- and post-relabel universes give the same answer, so the "
        "presence test is not reading the argument at all")


def test_the_pre_relabel_universe_cannot_be_forgotten():
    """A REQUIRED parameter is the guard against the fix being undone.

    The defect was a read of the wrong variable at the wrong moment. A default
    value here would let a future edit drop the capture and go silently blind
    again, which is precisely the failure being repaired; without one it raises
    `TypeError` at the call site.
    """
    parameter = inspect.signature(C._reconcile_arrival).parameters
    assert "pre_relabel_universe" in parameter, sorted(parameter)
    assert parameter["pre_relabel_universe"].default is inspect.Parameter.empty, (
        "`pre_relabel_universe` has a default, so a caller that forgets to "
        "capture the universe before `relabel_run` gets a silent wrong answer "
        "instead of a TypeError. That is the defect, reinstated.")

    # And the caller must capture it BEFORE the relabel. Asserted on ORDER in
    # the source because there is no way to observe a local's lifetime from
    # outside, and the whole defect was an ordering mistake.
    src = (ROOT / "src" / "compare_history.py").read_text(encoding="utf-8")
    capture = src.index("pre_relabel_universe = ")
    relabel = src.index("run = B.relabel_run(run, entrant_actual)")
    assert capture < relabel, (
        "the pre-relabel universe is captured AFTER `relabel_run` has already "
        "rewritten it, which is the original defect with an extra variable")


def test_an_unexplained_arrival_mass_raises_a_visible_flag():
    """Recorded silently for its whole life. The threshold is DERIVED.

    A row is flagged when the residual exceeds the budget it is a residual of —
    `declared + slot`. No number is typed, so nothing is owed to
    `JUDGEMENT-CALLS.md`, and the rule scales with whatever the budget is.
    """
    slot = _slot_expectation()
    pre = ("ANC", "ENTRANT")

    quiet = C._reconcile_arrival(_run(["ANC"]), {"mass_mean": slot * 1.5}, pre)
    assert quiet["unexplained_flag"] is False, (
        "a residual well inside its own budget was flagged, so the flag is "
        "unconditional and carries no information")

    loud = C._reconcile_arrival(_run(["ANC"]), {"mass_mean": slot * 4}, pre)
    assert loud["unexplained_flag"] is True, (
        f"a drawn arrival mass of {slot * 4:.4f} against an accounted budget "
        f"of {slot:.4f} was NOT flagged. The residual is more than twice the "
        f"whole budget.")
    assert abs(loud["unexplained_budget"] - slot) < 1e-12

    # TWO-SIDED. A declared budget that exceeds what was drawn is the same
    # disagreement pointing the other way, and a one-sided test would call it
    # success.
    over = C._reconcile_arrival(_run(["ANC"], seeds={"MK": 0.10}),
                                {"mass_mean": 0.0}, ("ANC",))
    assert over["unexplained_flag"] is True, (
        "a budget of 10% against a drawn mass of zero was not flagged; the "
        "flag only looks in one direction")

    # AND IT MUST REACH A HUMAN. A field nobody renders is the defect this
    # whole fix is about — `arrival_reconciliation` was written to the artefact
    # on every run and printed nowhere.
    row = _record(reconciliation=loud)
    text = "\n".join(C._arrival_reconciliation_table([row]))
    assert "FLAG" in text and "Johannesburg 2011" in text, text
    calm = "\n".join(C._arrival_reconciliation_table([_record(
        reconciliation=quiet)]))
    assert "FLAG" not in calm, (
        "the flag is rendered for an unflagged row, so it is decoration")


def test_the_arrival_reconciliation_is_rendered_at_all():
    """It was computed into the artefact on every run and shown to nobody.

    `_reconcile_arrival`'s own docstring asserted that "`_arrival_referee`
    prints it, and a test asserts on it". Neither was true: the referee
    rendered `arrival_group` only, and no test in `tests/` referenced
    `arrival_reconciliation`, `generic_slot_present` or `unexplained`. Both are
    true now, and this is the second half.
    """
    row = _record(reconciliation=C._reconcile_arrival(
        _run(["ANC"]), {"mass_mean": 0.0148}, ("ANC", "ENTRANT")))
    text = "\n".join(C._arrival_referee([dict(row, arrival_group={
        "n_arrived": 3, "n_columns": 4, "actual_mass": 0.02, "actual_seats": 4,
        "mass_mean": 0.0148, "mass_median": 0.01, "seats_mean": 3.0,
        "seats_median": 3.0, "mass_pit": 0.8, "seats_pit": 0.7,
        "seats_outside_support": False, "mass_err": 0.005, "seats_err": 1.0})]))
    assert "arrival budget" in text.lower(), (
        "the arrival reconciliation section is not rendered by the referee")
    # An artefact predating the reconciliation must render nothing, not crash
    # and not an empty table.
    assert C._arrival_reconciliation_table([{"city": "X", "year": "2016"}]) == []


# ---------------------------------------------------------------------------
# F8 — a crashed city-year is recorded, and the run exits non-zero
# ---------------------------------------------------------------------------

def test_a_failed_city_year_makes_the_process_exit_non_zero():
    """A shrunken panel must not be mistaken for a complete one.

    The totals are re-summed over the survivors, and the only surviving trace
    was `rows=N` inside the citable token — which a reader sees after they have
    already read and believed the number.
    """
    row = _record()
    assert C._exit_code([row], []) == 0
    assert C._exit_code([row], [("joburg", "2016", "FAILED: boom")]) != 0, (
        "a city-year failed and the process still reported success")
    assert C._exit_code([], []) == 1, (
        "the existing 'nothing runnable' exit code changed")
    assert C._exit_code([row], [("a", "b", "c")]) != C._exit_code([], []), (
        "'everything failed' and 'something failed' return the same code, so a "
        "caller cannot tell a total outage from a short panel")


def test_a_failed_city_year_is_excluded_with_its_REAL_reason():
    """⛔ IT USED TO BE STAMPED WITH A REASON THAT WAS FALSE.

    A crashed row reached the manifest in neither `results` nor `excluded`, so
    the catch-all branch labelled it *"not selected by --city/--target on this
    run"* — a statement about the CLI, about a row that WAS selected, WAS run
    and died. A reader who sees a declared reason stops looking.
    """
    results = [_record(year="2011")]
    archive = [("joburg", "2011"), ("joburg", "2016"), ("tshwane", "2011")]
    failure = ("joburg", "2016", "FAILED while scoring: ValueError: boom")

    block = C._population_block_for([failure], results, archive)
    by_row = {(e["city"], e["year"]): e["why"] for e in block["excluded"]}

    assert by_row[("joburg", "2016")] == failure[2], (
        f"the failed city-year carries {by_row[('joburg', '2016')]!r} instead "
        f"of its exception")
    assert "not selected" not in by_row[("joburg", "2016")]
    assert "not selected" in by_row[("tshwane", "2011")], (
        "a genuinely unselected row lost its reason")
    assert len(block["excluded"]) == 2, (
        f"the failed row appears twice — once with its reason and once with "
        f"the catch-all — which is worse than either: {block['excluded']}")

    # ⛔ THE CONSTRUCTED VIOLATION: omit the failure from `excluded`, which is
    # exactly what `main` used to do, and watch the false reason appear. If
    # this does not reproduce, the assertions above are not testing the bug.
    bug = C._population_block_for([], results, archive)
    bug_by_row = {(e["city"], e["year"]): e["why"] for e in bug["excluded"]}
    assert "not selected" in bug_by_row[("joburg", "2016")], (
        "the old defect did not reproduce, so this test cannot distinguish "
        "the fix from the bug")

    # 0 — SCANNED THE RIGHT THING, BOTH DIRECTIONS: every archive row is either
    # scored or excluded, and nothing is both.
    scored = set(block["scored"])
    excluded = {f"{e['city']}:{e['year']}" for e in block["excluded"]}
    assert scored | excluded == {f"{c}:{y}" for c, y in archive}, (
        "the panel's declared population does not cover the archive")
    assert not (scored & excluded), "a city-year is both scored and excluded"


# ---------------------------------------------------------------------------
# F9 — the report prints only what the scored rows support
# ---------------------------------------------------------------------------

# Words after which a count is GENERIC — a statement about what a city-year is,
# not about how many this panel holds. See the note in `_render_spy`.
_GENERIC_BEFORE = frozenset({
    "inside", "within", "per", "each", "in", "of", "a", "than", "to"})

_NUMERALS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
             "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11,
             "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
             "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
             "twenty": 20, "twenty-four": 24}


def _render_spy(text: str, results: list[dict]) -> list[str]:
    """Offences: printed claims the scored rows cannot support.

    Three detectors, all pure predicates over the rendered text, so each has a
    mechanical positive control:

    1. **A city that is not in the run.** The vocabulary is derived from
       `cityconfig`, so it does not go stale when a city is added. "Gauteng" is
       a province and is deliberately not in it.
    2. **A city-year count that is not this panel's.** Every ``<n> city-year``
       occurrence, digits or English numeral.
    3. **A party named in prose that is in no scored row.** Party names in this
       repository are SHOUTY_SNAKE_CASE, which is what makes them findable.
    """
    offences: list[str] = []
    here = {r.get("city") for r in results} | {r.get("slug") for r in results}

    for slug in C.CITIES:
        try:
            city = cityconfig.load(slug)
        except Exception:                        # pragma: no cover
            continue
        if city.name in here or slug in here:
            continue
        for token in (city.name, slug):
            if re.search(rf"\b{re.escape(token)}\b", text):
                offences.append(f"names {token!r}, which is not a scored row")

    n = len(results)
    sizes = {n} | {len([r for r in results if r.get("slug") == s])
                   for s in {r.get("slug") for r in results}}
    for match in re.finditer(r"(\w+)\s+([\w-]+)\s+city-years?\b", text):
        before, word = match.group(1).lower(), match.group(2).lower()
        value = (int(word) if word.isdigit() else _NUMERALS.get(word))
        if value is None:
            continue
        # ⛔ A COUNT IS NOT ALWAYS A CLAIM ABOUT THIS PANEL. "columns inside one
        # city-year share a turnout draw" is a statement about what a city-year
        # IS, and reads identically to "across the nine city-years", which is a
        # claim about the panel's size. The preceding word separates them; a
        # detector without this distinction fires on the report's own correct
        # generic prose and would be switched off, which is worse than a
        # narrower one that runs.
        if before in _GENERIC_BEFORE:
            continue
        if value not in sizes:
            offences.append(f"claims {value} city-years; this panel has {n}")

    known = set()
    for r in results:
        for block in (r.get("calibration") or {}).values():
            known.update(block.get("parties") or [])
        known.update(p[0] for p in (r.get("votes") or []))
    # ⛔ UNDERSCORED ALL-CAPS ONLY, and the narrowness is deliberate. A bare
    # `[A-Z]{4,}` scan cannot tell a party key from prose the report SHOUTS for
    # emphasis (LOWER BOUND, MIS-SHAPED, THE SPREAD…), and the first draft of
    # this spy returned six false positives from its own report. The fix is NOT
    # an exemption list — a list of allowed words is a second thing to maintain,
    # it silently absorbs a real party the day one is added to it, and it makes
    # the detector's coverage a function of who last remembered to update it.
    # `parties.canonical` produces SHOUTY_SNAKE_CASE, so an underscore is an
    # unambiguous signature no English prose in this report carries.
    #
    # ⚠️ WHAT THIS GIVES UP, stated rather than hidden: a short un-underscored
    # party key (`PA`, `ANC`, `AIC`) is invisible to this detector. The
    # historical sentence it exists to catch — "Cape Town's Cape Coloured
    # Congress and Johannesburg's PA" — is caught by the CITY detector above,
    # which is the load-bearing one; the party rule is a second net, not the
    # first.
    for match in re.finditer(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", text):
        name = match.group(0)
        if name not in known:
            offences.append(f"names party {name!r}, which is in no scored row")
    return offences


def test_the_report_names_no_city_count_or_party_it_did_not_score():
    """⛔ THE TEXT SPY. Five printed claims came from a different panel.

    On the three-row Johannesburg run the review read, the report printed a
    group row labelled `Gauteng (JHB, TSH, EKU)` over three Johannesburg rows
    under the sentence "the headline margin is a Gauteng result … loses at
    Mangaung"; named "Cape Town's Cape Coloured Congress and Johannesburg's PA"
    as the two high-leverage columns; said "across the nine city-years"; and
    printed "3 city-years is 3 effective clusters, not 3".

    The input is CONSTRUCTED — a single-city panel — so this does not expire the
    day the real panel happens to contain every city it mentions.
    """
    results = [_record(year=y, seed=s, saturate=(y == "2021"))
               for y, s in (("2011", 1), ("2016", 2), ("2021", 3))]
    text = C.render(results)

    # 1 — IT LOOKED. Two-sided, against a denominator computed from the report
    # itself, so it cannot go stale as the report grows.
    prose = [ln for ln in text.splitlines()
             if ln.strip() and not ln.lstrip().startswith("|")]
    scanned(prose, of=text.splitlines(), low=0.05, high=0.80,
            what="prose lines scanned in the rendered report",
            denominator="lines in the rendered report")

    # 0 — SCANNED THE RIGHT THING. There must BE other cities for the spy to
    # have caught, or its silence means nothing.
    absent = [s for s in C.CITIES if s not in {r["slug"] for r in results}]
    assert len(absent) >= 5, f"only {len(absent)} cities are absent from the run"

    offences = _render_spy(text, results)
    assert not offences, (
        "the rendered report makes claims the scored rows cannot support:\n  "
        + "\n  ".join(offences))


def test_the_text_spy_catches_a_constructed_false_sentence():
    """2 — IT CAN SEE. Three real sentences from the old report, each caught.

    A pure predicate, so the positive control is mechanical: push the exact
    prose that used to ship through the same detector.
    """
    results = [_record(year="2011")]
    for sentence, why in (
            ("Outside Gauteng the model loses at Mangaung.", "a city"),
            ("Five of its columns across the nine city-years carry PIT 1.0.",
             "a panel size"),
            ("Cape Town's CAPE_COLOURED_CONGRESS and Johannesburg's PA.",
             "a party")):
        offences = _render_spy(sentence, results)
        assert offences, (
            f"the spy did not catch {why} in {sentence!r}. A detector that "
            f"cannot see the sentences that actually shipped is inert, and its "
            f"silence on the real report means nothing.")
    # And it must not fire on prose the panel DOES support.
    assert not _render_spy("Johannesburg 2011 is one city-year.", results)


def test_the_leverage_columns_are_named_from_the_rows_scored():
    """"Cape Town's CCC and Johannesburg's PA … ~70% … about 1.0" was typed.

    On a Johannesburg panel neither party is in the run; on the twenty-four-row
    panel the share is 48.5%, not ~70%. Three typed figures, each true of a
    panel that no longer exists.
    """
    results = [_record(year=y, seed=s, saturate=True)
               for y, s in (("2016", 5), ("2021", 6))]
    band = C.pooled_by_band(results, "reference")["4-12"]
    leverage = band.get("leverage") or {}
    assert leverage.get("top_columns"), (
        "`_band_splits` reports no `top_columns`, so the report has no names to "
        "print and must fall back to typed prose")
    for column in leverage["top_columns"]:
        assert {"label", "z", "share"} <= set(column), column
        assert any(r["city"] in column["label"] for r in results), (
            f"the leverage column {column['label']!r} names no scored city")

    # The ORDER must match the share the report prints beside the name: the
    # first named column is the largest contributor, or the sentence is wrong
    # about its own numbers.
    shares = [c["share"] for c in leverage["top_columns"]]
    assert shares == sorted(shares, reverse=True), shares
    assert abs(sum(shares[:2]) - leverage["top2"]) < 1e-9, (
        "the named columns' shares do not sum to the reported `top2`, so the "
        "names and the percentage come from different orderings")


def test_the_saturation_count_is_computed_and_attributed_to_the_right_population():
    """⛔ THE FIFTH FALSE CLAIM, AND IT WAS WRONG IN KIND.

    The report printed "diluted by ~200 parties correctly at zero on both
    sides" **about the `all` population**. `score.seat_matrix` admits a column
    only when `truth > 0 or samples.max() > 0`, so a column zero on BOTH sides
    cannot be in `all` at all. Measured on the committed artefact: 0 of 580 in
    `all`, and 87 of 514 in `reference`, which is built with `keep_all=True`.
    A property of one population was attached to another.
    """
    results = [_record(year=y, seed=s, saturate=True)
               for y, s in (("2011", 11), ("2016", 12))]

    labels, total = C._saturated_columns(results, "all")
    assert total > 0, "the `all` population is empty, so the count means nothing"
    assert labels, (
        "no saturated column was found in a panel constructed to contain one "
        "per city-year; the detector is not seeing PIT values of exactly 1.0")
    assert len(labels) >= len(results)
    for label in labels:
        assert any(r["city"] in label and r["year"] in label for r in results)

    assert C._both_sides_zero(results, "all") == 0, (
        "a both-sides-zero column was found in `all`, which "
        "`score.seat_matrix`'s admission rule makes impossible. Either the "
        "rule changed or this counter is measuring something else.")

    text = C.render_calibration(results)
    assert f"{len(labels)} of its {total} columns" in text, (
        f"the saturation count in the prose is not the computed one "
        f"({len(labels)} of {total})")
    assert f"across {len(results)} city-years" in text, (
        "the prose does not state the panel size it counted over")
    # AND THE DILUTION FIGURE IS ATTRIBUTED TO THE POPULATION THAT CARRIES IT.
    assert "dilution is in `reference`" in text
    assert f"{C._both_sides_zero(results, 'reference')} of " in text


def test_a_single_city_panel_refuses_to_claim_independent_clusters():
    """"3 city-years is 3 effective clusters, not 3" — a template, twice filled.

    It also asserts full independence for three elections of one metro, which
    share its pools, its geography and its party system.
    """
    one_city = [_record(year=y, seed=s) for y, s in (("2011", 1), ("2016", 2),
                                                     ("2021", 3))]
    text = "\n".join(C._headline_split(one_city))
    assert "NO POOLED CLUSTER COUNT" in text, (
        "a one-city panel still printed an effective-cluster count")
    assert not re.search(r"is (\d+) effective clusters, not \1\b", text), (
        "the cluster sentence substitutes the same number twice")

    many = one_city + [_record(year=y, slug="tshwane", city="Tshwane", seed=s)
                       for y, s in (("2011", 4), ("2016", 5), ("2021", 6))]
    multi = "\n".join(C._headline_split(many))
    assert "effective clusters" in multi, (
        "a genuinely multi-city panel lost the cluster caveat entirely, which "
        "is the opposite failure")
    assert "NO POOLED CLUSTER COUNT" not in multi


def test_the_group_label_names_the_cities_in_the_group():
    """`Gauteng (JHB, TSH, EKU)` over three Johannesburg rows."""
    text = "\n".join(C._headline_split([_record(year=y, seed=s)
                                        for y, s in (("2011", 1), ("2016", 2))]))
    assert "Gauteng (Johannesburg)" in text, text[:600]
    assert "TSH" not in text and "EKU" not in text, (
        "the group label still names metros that are not in the run")
    assert "only one of the two groups" in text, (
        "a panel with no non-Gauteng row must say the split is unavailable "
        "rather than assert where the margin is concentrated")


# ---------------------------------------------------------------------------
# F10 — labels that do not mislead
# ---------------------------------------------------------------------------

def test_a_deterministic_baseline_is_identified_as_a_point_forecast():
    """Measured from the rows, never declared.

    On the committed artefact `last-lge` and `uniform-swing` carry
    `crps == seat_abs_err_coherent` on 24 of 24 rows to exactly zero
    difference, and `prior-lge-noise` on 0 of 24. CRPS collapses to absolute
    error for a point mass, so a CRPS margin over the first two is a claim
    about the central estimate and not about uncertainty.
    """
    def row(**opp):
        return {"slug": "joburg", "year": "2011", "opponents": opp}

    point = [row(x={"crps": 52.0, "seat_abs_err_coherent": 52}),
             row(x={"crps": 92.0, "seat_abs_err_coherent": 92})]
    assert C._reference_kind(point, "x") == "point"

    spread = point[:1] + [row(x={"crps": 48.5, "seat_abs_err_coherent": 66})]
    assert C._reference_kind(spread, "x") == "probabilistic", (
        "one row whose CRPS differs from its seat error is enough to make a "
        "reference probabilistic; a rule that needs a majority would label a "
        "mostly-degenerate forecast as a point mass")

    # ⛔ MISSING EVIDENCE IS NOT EVIDENCE OF DETERMINISM. Defaulting to "point"
    # would attach the caveat on the strength of an absent field.
    assert C._reference_kind([row(x={})], "x") == "unknown"
    assert C._reference_kind([row(x={"crps": 1.0})], "x") == "unknown"
    assert C._reference_kind([], "x") == "unknown"


def test_the_report_marks_point_forecasts_and_promotes_the_probabilistic_one():
    """(a) and (b): the caveat where a CRPS margin is printed, and
    `prior-lge-noise` in the headline it was missing from."""
    results = [_record(year=y, seed=s) for y, s in (("2011", 1), ("2016", 2))]
    text = C.render(results)

    assert "POINT forecast" in text, (
        "no CRPS margin in the report is marked as being against a point "
        "forecast, so the margin reads as a claim about uncertainty")
    assert "margin_vs_prior_lge_noise" in text, (
        "`prior-lge-noise` is the only probabilistic reference here and is "
        "absent from the citable totals")
    assert "`prior-lge-noise` is **probabilistic**" in text, text[-2500:]

    # NEGATIVE CONTROL: make every reference probabilistic and the point-forecast
    # caveat must disappear, or it is unconditional furniture.
    probabilistic = [dict(r, opponents={
        k: {"crps": 40.0, "seat_abs_err_coherent": 70, "wards": {}}
        for k in ("last-lge", "uniform-swing", "prior-lge-noise")})
        for r in results]
    assert "POINT forecast" not in C.render(probabilistic), (
        "the point-forecast caveat printed for a panel whose references all "
        "express uncertainty, so it says nothing")


def test_a_total_is_not_described_as_having_a_denominator():
    """(c) `crps` is a SUM over columns; dividing by `n_scored` normalises
    nothing. The count matters for the opposite reason — the scored column set
    differs between forecasters (§1.141) — and the line now says that."""
    text = C.render([_record()])
    assert "CRPS denominator" not in text, (
        "`n_scored` is still described as the CRPS denominator")
    assert "NOT a denominator" in text and "§1.141" in text


def test_every_probit_sd_is_printed_with_its_clip_sensitivity():
    """(d) The bolded width figure is a function of a 1e-6 clip on two PITs.

    `_band_splits` has computed `probit_by_clip`, `pit_saturated` and
    `probit_quotable` since §1.134 and **none of them was printed**, so the
    figure the report's central width argument rests on carried no sign that it
    was not a property of the forecast. Measured on `reference` ranks 4-12 over
    Johannesburg alone: 1.5497 at the 1e-6 clip the code uses, 1.0655 at 1e-2,
    and 1.0991 with the saturated columns dropped instead of pinned.
    """
    results = [_record(year=y, seed=s, saturate=True)
               for y, s in (("2016", 21), ("2021", 22))]
    band = C.pooled_by_band(results, "reference")["4-12"]
    assert band["pit_saturated"] > 0, (
        "the constructed panel produced no saturated PIT, so this test cannot "
        "exercise the clip at all")
    assert "0.01" in band["probit_by_clip"], sorted(band["probit_by_clip"])
    assert band["probit_drop_saturated"] == band["probit_drop_saturated"], (
        "probit_drop_saturated is nan on a band with columns to drop")

    text = C.render_calibration(results)
    assert "drop saturated" in text and "same @1e-2" in text, (
        "the clip-sensitivity columns are not in the width table")
    assert "UNQUOTABLE" in text, (
        "a band carrying a saturated PIT is not marked unquotable in the "
        "table cell; `probit_quotable` has been computed and unprinted since "
        "§1.134 and a footnote is not enough — the number is what gets read")
    assert f"{band['probit_by_clip']['0.01']:.3f}" in text
    assert f"{band['probit_drop_saturated']:.3f}" in text

    # NEGATIVE CONTROL: no saturated column ANYWHERE, no unquotable mark.
    # Otherwise the mark is unconditional and carries no information. The
    # emptiness has to hold across every band of every population the report
    # renders, not just the band under test — the first draft checked ranks
    # 4-12 alone and failed on a saturated column in ranks 13+, which is the
    # scan-the-wrong-population defect this suite exists to catch.
    clean = [_record(year=y, seed=s, saturate=False)
             for y, s in (("2016", 31), ("2021", 32))]
    saturated_anywhere = any(
        blk.get("pit_saturated", 0)
        for pop in C.POPULATIONS
        for blk in C.pooled_by_band(clean, pop).values())
    if not saturated_anywhere:
        assert "UNQUOTABLE" not in C.render_calibration(clean), (
            "no band of any population carries a saturated PIT, yet the report "
            "still marks a width figure unquotable — the mark is unconditional")



# ---------------------------------------------------------------------------
# F5 — every guard counter the model computes reaches the artefact
# ---------------------------------------------------------------------------

def test_every_guard_counter_the_run_produced_reaches_the_record():
    """⛔ THEY WERE COMPUTED AND THROWN AWAY, AND `verbose=False` HID THE REST.

    The panel is scored with the printed warnings suppressed, and until
    `ModelRun.guards` existed the ten solve counters were LOCALS of `run_model`
    reachable only by re-running with a `--run-dir`. So the guard state of every
    city-year in the scoreboard was *unknown*, and "that guard is not binding"
    was an assumption about the panel that decides what ships.

    The board is read WHOLE rather than field by field, because it is the same
    dict `montecarlo` hands to the trace — one definition, and a scoreboard
    cannot then disagree with a trace from the same run.
    """
    board = _board()
    block = C._guard_block(_guard_run(board))

    assert block["recorded"] is True
    assert block["unavailable_why"] is None
    assert block["counters"] == board, (
        "the guard block is not the whole board; a subset here is a second "
        "definition of what the run did")

    # THE TEN THAT HAD NO ROUTE OUT AT ALL must be among them.
    for key in ("solve_calls", "solve_rounds", "solve_nonconvergent",
                "solve_nonconvergent_reachable", "solve_worst_gap",
                "solve_worst_gap_reachable", "solve_unreachable_parties",
                "solve_floor_injected_mean", "solve_floor_injected_worst",
                "solve_identity_hits"):
        assert key in block["counters"], (
            f"{key} is not on the record. It was a local of `run_model` and "
            f"reachable only through a --run-dir trace; that is the gap this "
            f"fix closes.")

    # It must be a COPY, or a later mutation of the run rewrites the artefact.
    board["ipf_failures"] = 999
    assert block["counters"]["ipf_failures"] == 427


def test_an_unrecorded_guard_board_is_not_reported_as_a_measured_zero():
    """⛔ THE POSITIVE CONTROL THAT MATTERS MOST HERE.

    `ModelRun.guards` defaults to `{}`, so a run from before the field existed
    is byte-identical to a run in which nothing fired — unless the difference is
    written down. Reporting the first as "every counter zero" would be the
    "empty record vs unreachable record" defect, which this repository has
    already published two write-ups getting wrong about a single bug.
    """
    absent = C._guard_block(_guard_run(None))
    assert absent["recorded"] is False
    assert absent["counters"] == {}
    assert absent["unavailable_why"] and "not" in absent["unavailable_why"].lower()
    assert "zero" in absent["unavailable_why"].lower(), (
        "the absence marker does not say that this is NOT a report of zeroes, "
        "which is the only thing it exists to say")

    # AND A MEASURED ALL-ZERO BOARD IS A DIFFERENT FACT, recorded as such.
    zeroed = C._guard_block(_guard_run(
        {k: (0 if isinstance(v, (int, float)) else {})
         for k, v in _board().items()}))
    assert zeroed["recorded"] is True and zeroed["unavailable_why"] is None
    assert zeroed["counters"] != absent["counters"], (
        "a measured all-zero board and an unrecorded one are indistinguishable "
        "on the record, which is exactly the confusion being prevented")


def test_the_guard_table_prints_the_counters_and_a_zero_is_not_a_dash():
    """A counter recorded and never rendered is a counter nobody reads.

    That is not hypothetical here: `arrival_reconciliation` was written to
    `history.json` on every run and rendered nowhere until this same round.
    """
    rows = [_record(year=y, seed=s) for y, s in (("2011", 1), ("2016", 2))]
    for r in rows:
        r["guards"] = C._guard_block(_guard_run(_board()))
        r["roster"] = C._roster_block(_guard_run(_board()))
    text = "\n".join(C._guard_table(rows))

    assert "Guards — what fired" in text
    assert "427/1,000 (42.7%)" in text, (
        "the IPF fallback rate is not rendered; it was 42.7% of the 2026 "
        "forecast and invisible until §1.33")
    assert "0.1234%" in text, "cap_moved is not rendered"
    assert "19/800" in text, (
        "the REACHABLE solve non-convergence is not rendered; the raw count is "
        "expected to equal solve_calls and is not the one to read (§1.98)")
    assert "0.4321%" in text, "the level floor's injected mass is not rendered"
    assert "published (41)" in text, "the roster state is not rendered"

    # A MEASURED ZERO RENDERS AS A ZERO, NOT AS A DASH. The distinction is the
    # whole point of the table and is asserted on the rendered cell, not on a
    # note beside it.
    assert "| 0 |" in text, (
        "`solve_identity_hits` is 0 in this board and no cell renders as a "
        "plain zero, so a measured null is being shown as something else")
    assert "**A zero here is a MEASURED zero.**" in text


def test_the_guard_table_names_a_counter_it_asked_for_and_did_not_get():
    """⛔ CONSTRUCTED VIOLATION: a renamed counter must not blank silently.

    `_GUARD_COLUMNS` is a hard-coded key list against a dict built in another
    module. That arrangement goes stale the moment somebody renames a key — the
    column would read `—` in every row for ever, and "the guard did not fire"
    and "this table lost the guard" would look identical. So the renderer names
    what it asked for and did not get.
    """
    board = _board()
    del board["solve_floor_injected_worst"]        # the rename, simulated
    row = _record()
    row["guards"] = C._guard_block(_guard_run(board))
    row["roster"] = C._roster_block(_guard_run(board))
    text = "\n".join(C._guard_table([row]))

    assert "solve_floor_injected_worst" in text, (
        "a counter the table asked for is missing from the board and the "
        "report does not say so; the column is silently blind")
    assert "did not produce" in text

    # NEGATIVE CONTROL: a complete board must NOT raise the warning, or it is
    # unconditional and says nothing.
    whole = _record()
    whole["guards"] = C._guard_block(_guard_run(_board()))
    whole["roster"] = C._roster_block(_guard_run(_board()))
    assert "did not produce" not in "\n".join(C._guard_table([whole]))


def test_a_city_year_with_no_guard_board_is_called_out_in_the_report():
    """An older record must degrade LOUDLY, the way `load_history` does."""
    row = _record()
    row["guards"] = C._guard_block(_guard_run(None))
    row["roster"] = C._roster_block(_guard_run(None, roster=("", 0, ())))
    whole = _record(year="2016", seed=9)
    whole["guards"] = C._guard_block(_guard_run(_board()))
    whole["roster"] = C._roster_block(_guard_run(_board()))

    text = "\n".join(C._guard_table([row, whole]))
    assert "carry no guard board" in text and "Johannesburg 2011" in text
    assert "NOT measured" in text

    # A results set with no board anywhere renders no section at all, rather
    # than an empty table with a misleading summary over zero rows.
    assert C._guard_table([row]) == [] or "carry no guard board" in "\n".join(
        C._guard_table([row]))
    assert C._guard_table([_record()]) == [], (
        "a record predating the guard board produced a table; older "
        "history.json files have no such key and must render no section")


def test_the_roster_size_separates_a_read_roster_from_an_absent_one():
    """`roster_dropped == []` alone cannot tell those apart. `roster_size` can."""
    read = C._roster_block(_guard_run(_board(), roster=("published", 41, ())))
    assert read == {"recorded": True, "state": "published", "size": 41,
                    "dropped": []}

    none = C._roster_block(_guard_run(_board(), roster=("", 0, ())))
    assert none["recorded"] is False and none["state"] is None
    assert read["dropped"] == none["dropped"], (
        "this test is only meaningful while both have an empty `dropped`; that "
        "is the ambiguity `roster_size` and `recorded` exist to resolve")

    dropped = C._roster_block(_guard_run(
        _board(), roster=("published", 41, ("MK", "ACTIONSA"))))
    assert dropped["dropped"] == ["ACTIONSA", "MK"], "dropped is not sorted"


def test_the_committed_artefact_carries_the_guard_counters():
    """THE POSITIVE CONTROL ON PRODUCTION — proves the counters really arrive.

    Every assertion above runs against a stub. Only the real artefact can show
    that `run_city_year` reads a board `run_model` actually filled, so this is
    the one that would catch a `guards` field that exists and is always empty.
    """
    _manifest, records = _artefact()
    if not any((r.get("guards") or {}).get("counters") for r in records):
        skip("this history.json predates the guard board; re-run "
             "src/compare_history.py to record what the guards did")
    for r in records:
        block = r.get("guards") or {}
        assert block.get("recorded") is True, (
            f"{r['slug']} {r['year']} carries no guard board")
        counters = block["counters"]
        # IT RAN AT ALL: a board of zeroes with no solve calls would mean the
        # model never reached the solve, not that it converged.
        assert counters.get("solve_calls", 0) > 0, (
            f"{r['slug']} {r['year']} reports {counters.get('solve_calls')} "
            f"solve calls. The board arrived but the mechanism did not run, "
            f"which is a silently-inert guard, not a clean one.")
        assert counters.get("ipf_balances", 0) > 0, (
            f"{r['slug']} {r['year']} reports no IPF balance attempts")


def test_the_guard_columns_name_keys_montecarlo_actually_produces():
    """A STATIC RECONCILIATION, so a rename is caught without running the model.

    `_GUARD_COLUMNS` is a hard-coded key list in one module against a dict
    literal in another. `_guard_table` reports a key it asked for and did not
    get, but only on a run — and the counters it would lose are exactly the ones
    that had no route out before. Reading montecarlo's `41_guards` literal with
    `ast` closes that at suite time, on a machine with no data.

    This is the "scanned the RIGHT thing, both directions" requirement: the
    board must be non-empty and within a two-sided bound (below it the AST walk
    has stopped finding the literal and the subset check is vacuous; above it
    the walk has matched something else), and every column key must be in it.
    """
    import ast

    tree = ast.parse((ROOT / "src" / "montecarlo.py").read_text(encoding="utf-8"))
    board = None
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "put"
                and node.args and isinstance(node.args[0], ast.Constant)
                and node.args[0].value == "41_guards"
                and len(node.args) > 1 and isinstance(node.args[1], ast.Dict)):
            board = {k.value for k in node.args[1].keys
                     if isinstance(k, ast.Constant)}
    assert board, (
        "no `trace.put(\"41_guards\", {...})` dict literal was found in "
        "montecarlo.py. Either it was renamed — in which case the guard table "
        "is about to go blind — or this walk has broken and is asserting "
        "nothing.")

    # IT LOOKED, two-sided. The denominator is the column count this file asks
    # for, so the band moves with the table rather than going stale.
    wanted = {k for _h, keys, _f in C._GUARD_COLUMNS for k in keys}
    scanned(board, of=wanted, low=1.0, high=4.0,
            what="keys in montecarlo's 41_guards board",
            denominator="distinct keys _GUARD_COLUMNS asks for")

    missing = sorted(wanted - board)
    assert not missing, (
        f"_GUARD_COLUMNS asks for {missing}, which montecarlo's `41_guards` "
        f"payload does not produce. Those columns will read `-` in every row "
        f"for ever, which is indistinguishable from a guard that did not fire.")

def test_the_disclosure_names_the_uninstrumented_constants_too():
    """The two halves of the register must BOTH reach the artefact.

    `contaminated` implicates an INSTRUMENTED constant from `read` (a proof it
    was consumed) and an UNINSTRUMENTED one from scenario membership (a proof
    only that it was resolved). Called with `read` alone it returns `FITTED_ON`
    and silently omits the rest.

    ⛔ **That is exactly what `run_city_year` did until 2026-09-12**, so the
    scoreboard disclosed `['pools']` and nothing else while `level_shrink` —
    worth coherent seat error 312 -> 264 on a panel this harness scores — went
    unnamed. The fix is three lines; this is the guard that would have caught
    it, and the ABSENCE of this guard is why it shipped at all.
    """
    import montecarlo as M
    read = {"pools": ["2021"]}
    defaults = dict(M.DEFAULTS)

    without = set(B.contaminated("2021", set(), read))
    with_scn = set(B.contaminated("2021", set(), read, defaults))

    # (1) IT LOOKED: the uninstrumented register is non-empty, so the claim
    # below is about a real population rather than a vacuously satisfied one.
    uninstrumented = set(getattr(B, "FITTED_ON_UNINSTRUMENTED", {}))
    assert uninstrumented, (
        "`FITTED_ON_UNINSTRUMENTED` is empty. If every constant has been "
        "instrumented with `note_constant` that is GOOD and this guard should "
        "be deleted with a note saying so — but check, do not assume.")
    scanned(uninstrumented, of=set(M.DEFAULTS), low=0.05, high=0.9,
            what="constants in the uninstrumented register",
            denominator="keys in montecarlo.DEFAULTS")

    # (2) THE CLAIM: passing the scenario discloses strictly more, and what it
    # adds is the uninstrumented register.
    assert with_scn > without, (
        f"passing the scenario disclosed nothing extra: {sorted(without)} "
        f"either way. The uninstrumented half of the register is not reaching "
        f"the artefact, which is the defect this guard exists for.")
    assert with_scn & uninstrumented, (
        f"the disclosure names {sorted(with_scn)}, none of which is in "
        f"`FITTED_ON_UNINSTRUMENTED` ({sorted(uninstrumented)}).")

    # (3) AND THE SCOREBOARD ACTUALLY PASSES IT. The call above proves the
    # BACKTEST function can do it; this proves `compare_history` does, which is
    # the half that was broken. Asserted on the source, because running a
    # city-year here would cost minutes and need the archive.
    # Parsed, not grepped: a regex over the call text is brittle (`[^)]*`
    # stops at the `)` inside `set()`, which is how the first version of this
    # assertion failed on correct code). Count the ARGUMENTS.
    import ast, textwrap
    tree = ast.parse(textwrap.dedent(inspect.getsource(C.run_city_year)))
    calls = [n for n in ast.walk(tree)
             if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute)
             and n.func.attr == "contaminated"]
    assert calls, "`run_city_year` no longer calls `B.contaminated` at all"
    assert any(len(c.args) + len(c.keywords) >= 4 for c in calls), (
        "`run_city_year` calls `B.contaminated` with "
        f"{[len(c.args) + len(c.keywords) for c in calls]} argument(s) and the "
        "scenario is the fourth. Without it the call returns the instrumented "
        "register only, and the uninstrumented constants — `level_shrink` "
        "among them — go unnamed in `history.json`.")


def test_the_disclosure_guard_can_see_the_scenario_being_dropped():
    """(2) IT CAN SEE, on (3) A CONSTRUCTED input — the mutation is the bug.

    Re-runs the guard's own predicate against the pre-fix call, which passed no
    scenario. If that shape does not trip the assertion, the guard above is
    furniture.
    """
    import montecarlo as M
    read = {"pools": ["2021"]}
    pre_fix = set(B.contaminated("2021", set(), read))          # the old call
    uninstrumented = set(getattr(B, "FITTED_ON_UNINSTRUMENTED", {}))
    assert not (pre_fix & uninstrumented), (
        "the pre-fix call already disclosed an uninstrumented constant, so the "
        "guard above cannot distinguish the fixed code from the broken code "
        "and proves nothing.")


if __name__ == "__main__":
    # AT THE END. `test_register_matches_code` fails any test module that
    # defines a test below its `__main__` block, because running the file
    # directly would silently skip it.
    raise SystemExit(run_module(globals()))
