"""One test per CLASS of error this project has actually made.

Every defect below was real, shipped, and found by measurement rather than by
reading. They are grouped by the *shape* of the mistake rather than by the file
it happened in, because each shape recurred: the temporal leak happened three
times, the wrong-anchor clamp three times, the un-namespaced path three times.
A test per instance would have caught none of the repeats; a test per class
catches the next one.

CLASS 1 — TEMPORAL LEAK. A record reads an election at or after the target it is
    forecasting. Instances: `splinter_record` hardcoded years (fixed earlier);
    `home_splinter_record` unfiltered, which let MK's 2024 eThekwini split size
    ActionSA in the 2021 backtest and was worth 37 seats of error; and a memo on
    `levels._citywide` that made the existing leak spy see nothing at all, so the
    guard would have passed by blindness.

CLASS 2 — DEGENERATE SUPPORT. A distribution that assigns probability zero to
    outcomes that happen, or one to an outcome that is merely likely. Instances:
    a splinter band built as (min, median, max) of ONE observation, giving
    low == high in seven of eight metros; a turnout band capped at the observed
    maximum, so mode == high in every 2016 backtest and turnout could not rise.

CLASS 3 — UNIDENTIFIED SCALE. An iteration with a free parameter nothing pins,
    which then drifts. Instance: `fold.calibrate_theta` — `predict` renormalises
    within each VD, so a common factor on θ cancels; the IPF wandered four orders
    of magnitude and handed 42 seats to 21 parties that won nothing.

CLASS 4 — WRONG ANCHOR. A bound or ratio computed against a quantity other than
    the one it is bounding. Instance: the by-election and polling clamps bounded
    evidence to [low × NATIONAL share, high × NATIONAL share] while the level
    they were correcting had been built from the LOCAL route, so two agreeing
    pieces of evidence were overruled by a bound derived from the route the
    model had deliberately abandoned.

CLASS 5 — LOST NAMESPACE. A path that ignores --city or --target and silently
    reads or writes another city's files. Instances: `turnout.py --out`,
    `export_interactive.py` and `leverage.py`, all defaulting to Johannesburg's
    `data/processed`.

CLASS 6 — DISPLAY LIMIT LEAKING INTO DATA. A human-readable cap becoming a
    stored dataset. Instance: `score.format_report(top=12)` is a terminal width,
    and `build_validation.py` regex-parses that block into JSON, so
    `validation_<year>.json` stored twelve parties for targets with fifteen to
    twenty-four seat-winners.

CLASS 7 — NEVER-EXECUTED PATH. A branch that looks unused and is actually
    broken. Instance: the polling channel raised NameError the instant
    `poll_weight` went above zero, because `prior` there was a local of another
    function. It had never run.

CLASS 8 — SUMMARY ARTEFACT. A reported statistic that is not what it claims.
    Instances: `diagnose.py` not relabelling the generic ENTRANT, so a party the
    model forecast within 0.17pp was reported as a total miss; and per-party
    marginal medians reported as a council when they do not sum to one.

CLASS 11 — A CONSTANT THAT CANNOT BE SWEPT. A tunable whose value, changed at
    the place it is declared, does not reach the run. Sweeping it returns
    identical rows, which reads as "this constant does nothing" when the truth
    is "you did not change it". `montecarlo.DEFAULTS["entrant_prob"]` is the
    instance: `apply_city` copies `cities/<city>.toml`'s scalars over DEFAULTS
    afterwards, so the edit is overwritten — and, because DEFAULTS is a module
    global that is never reset, Johannesburg's scalars then apply to every city
    that follows it in a multi-city run.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, skip, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import levels  # noqa: E402
import montecarlo as M  # noqa: E402
import pools as PL  # noqa: E402
import score as S  # noqa: E402

SRC = ROOT / "src"


# ---------------------------------------------------------------------------
# CLASS 1 — temporal leak
# ---------------------------------------------------------------------------

def test_no_record_reads_an_election_at_or_after_its_target():
    """Every measured record is strictly pre-target, for every runnable target.

    Covers θ, ρ, the away splinter record and — the one that was wrong — the
    HOME splinter record. `home_splinter_record` ignored the cutoff by design
    and the design was declared, but declared is not the same as priced: at
    target 2021 it was letting a 2024 result size the largest arrival on record.
    """
    for slug in ("joburg", "tshwane"):
        city = cityconfig.load(slug)
        cityconfig.use(slug)
        for year in ("2016", "2021"):
            target = cityconfig.Target(city=city, year=year)

            home = PL.home_splinter_record(before_year=target.year)
            for party, split in PL.SPLITS.items():
                if party in home and split.measured_from:
                    after = split.measured_from[1]
                    assert int(after) < int(year), (
                        f"{slug} {year}: home splinter record contains {party}, "
                        f"measured at {after}, which is not before the target")

            away = PL.splinter_record(city, target.year)
            assert isinstance(away, list)

            for name, rec in (("theta", levels.theta_record(target)),
                              ("rho", levels.local_record(target))):
                assert rec, f"{slug} {year}: {name} record is empty"

    # And the guard that proves it must still be able to SEE the reads: a memo
    # on the election reader makes a file-open spy observe nothing, so the leak
    # test passes by blindness rather than by cleanliness.
    src = (SRC / "levels.py").read_text()
    assert "_CITYWIDE_CACHE" not in src, (
        "levels._citywide is memoised again. A path-keyed memo makes the "
        "temporal-leak spy see no file opens, so the guard proving θ reads no "
        "post-target election passes by seeing nothing. Speed is not worth a "
        "silenced guard here.")


def test_the_home_record_still_grows_when_the_target_is_later():
    """The cutoff is a filter, not a ban: 2026 legitimately sees MK's 2024 split."""
    early = PL.home_splinter_record(before_year="2021")
    late = PL.home_splinter_record(before_year="2026")
    assert set(early) <= set(late), "the record shrank as the target moved later"
    assert len(late) > len(early), (
        "no split became available between 2021 and 2026, so the filter is "
        "either not applying or the SPLITS table has lost an entry")


# ---------------------------------------------------------------------------
# CLASS 2 — degenerate support
# ---------------------------------------------------------------------------

def _emitted_specs():
    out = []
    for path in sorted((ROOT / "data" / "processed").glob("*/pools_*.json")) + \
            sorted((ROOT / "data" / "processed").glob("pools_*.json")):
        if "simulation" in path.name:
            continue
        try:
            out.append((path, json.loads(path.read_text())))
        except Exception:
            continue
    return out


def test_no_emitted_turnout_band_is_one_sided():
    """mode == high is a triangular that cannot rise. It bound almost everywhere.

    4 of 4 pools in every metro at target 2016, 3-4 of 4 at 2021, 0 of 4 at 2026
    — so the bias was in exactly the runs used to judge the model and not in the
    run being judged.
    """
    checked = 0
    for path, spec in _emitted_specs():
        for name, cfg in spec["pools"].items():
            lo, mid, hi = cfg["turnout"]
            assert lo < mid, (f"{path.name} pool {name!r}: turnout low {lo} is "
                              f"not below the mode {mid} — it cannot fall")
            assert hi > mid * 1.002, (
                f"{path.name} pool {name!r}: turnout high {hi} equals the mode "
                f"{mid} — turnout cannot rise, which is the cap that biased "
                f"every historical backtest")
            assert 0.0 < lo and hi < 1.0, (
                f"{path.name} pool {name!r}: turnout band {lo}-{hi} leaves "
                f"(0, 1); a proportion's band must be built on the logit scale")
            checked += 1
    assert checked, "no emitted pool spec found"


def test_no_arrival_band_has_zero_width():
    """(min, median, max) of ONE observation is a band of zero width.

    Seven of eight metros were in that state at target 2021, so the model was
    asserting an arrival's size was known exactly. ActionSA then took 19 of
    Tshwane's 214 seats against a band of 0.4%-0.4%.
    """
    checked = 0
    for path, spec in _emitted_specs():
        for party, band in (spec.get("seed_bands") or {}).items():
            lo, mid, hi = band
            assert hi > lo, (
                f"{path.name}: {party}'s arrival band is [{lo}, {hi}] — zero "
                f"width, so every other outcome has probability exactly zero")
            checked += 1
    if not checked:
        skip("no seeded arrivals in any emitted spec")

    # The 1.0 ceiling belongs to the SPLINTER FRACTION -- a share of the
    # parent's vote -- and is asserted at that scale. The emitted `seed_bands`
    # above are a different quantity: a multiplier on the party's seed, which
    # can legitimately exceed 1 by a lot for a tiny seed. Conflating the two is
    # how the first version of this test failed on a band of 44.3.
    lo, mid, hi, _ = PL._band_from([0.14, 0.16, 0.24, 0.61], "away",
                                   [0.005, 0.017, 0.14, 0.16, 0.24, 0.61])
    assert hi <= 1.0, (
        f"a splinter fraction may not exceed 1.0 of its parent's vote; got "
        f"{hi:.3f}. Johannesburg's own record implied 1.17, which is a party "
        f"taking 117% of the vote its parent had.")
    assert lo < mid < hi, "the splinter band collapsed"


def test_the_level_shock_has_unbounded_support():
    """A bounded draw gives probability zero to things that have happened."""
    rng = np.random.default_rng(0)
    draws = M.log_shock(rng, 0.3, size=20000)
    assert draws.max() / draws.mean() > 3.0, (
        "the level shock has no tail: a party trebling should be unlikely, not "
        "impossible. Al Jama-ah won a 2016 seat with 0 of 500 draws non-zero.")
    realised = float(np.std(np.log(draws)))
    assert abs(realised - 0.3) < 0.03, (
        f"log_shock(sd=0.3) realised sd {realised:.3f} — the Student-t is not "
        f"standardised, so the measured sd(log θ) no longer means what "
        f"levels.py measured it to mean")


# ---------------------------------------------------------------------------
# CLASS 3 — unidentified scale
# ---------------------------------------------------------------------------

def test_the_theta_calibration_pins_its_scale():
    """`predict` renormalises, so a common factor on θ is free and will drift.

    It drifted four orders of magnitude: the ANC finished fold 2 at θ = 0.0001,
    and the parties pinned at the level floor sat 3.6 logits below it — 0.67% of
    the vote each, just over quota, two seats apiece, 42 seats to 21 parties that
    won nothing.
    """
    import fold

    base_city = {"A": 0.50, "B": 0.30, "C": 0.15, "D": 0.05}
    base = {f"vd{i}": dict(base_city) for i in range(20)}
    target_city = {"A": 0.40, "B": 0.35, "C": 0.20, "D": 0.05}
    gamma = {p: 1.0 for p in base_city}
    weights = {vd: 100 for vd in base}

    theta = fold.calibrate_theta(base, base_city, target_city, gamma, weights,
                                 list(base_city))
    total = sum(base_city[p] * theta[p] for p in base_city)
    assert abs(total - 1.0) < 1e-6, (
        f"Σ base·θ = {total:.6f}, not 1. The iteration's overall scale is "
        f"unpinned and will wander until the level floor binds.")

    got = fold.predicted_citywide(fold.predict(base, base_city, theta, gamma),
                                  weights, list(base_city))
    for p, want in target_city.items():
        assert abs(got[p] - want) < 5e-3, (
            f"{p}: calibrated to {got[p]:.4f} against a target {want:.4f}")


# ---------------------------------------------------------------------------
# CLASS 4 — wrong anchor
# ---------------------------------------------------------------------------

def test_no_clamp_is_anchored_on_the_national_baseline():
    """The clamp must bound evidence around the level the model BELIEVES.

    θ's band is a band on the NATIONAL route. Multiplying it by the national
    baseline bounds by-election and polling evidence to what a party's national
    share could become — which is the assumption task #22 exists to abandon, and
    it dragged ActionSA from the spine's 15.2% to 12.1% using evidence that
    independently said 18.7%.
    """
    src = (SRC / "montecarlo.py").read_text()
    for bad in ("low * base_city_d[party]", "high * base_city_d[party]",
                "low * base)", "high * base)"):
        assert bad not in src, (
            f"montecarlo.py still clamps with {bad!r} — a bound computed "
            f"against the national baseline rather than against the level the "
            f"spine settled on. This defect appeared at three separate sites.")
    assert "anchor = mode_level" in src, (
        "the by-election clamp must anchor on the model's own central level "
        "(`anchor = mode_level`); it no longer does")
    # The POLLING half of this test used to look for `anchor = centres.get(party)`.
    # There is no polling clamp any more: §1.68 replaced it with the variance-
    # weighted blend below, which needs no clamp because the weight itself is
    # bounded by `weight_cap`. What the test exists to guard is unchanged and
    # is still checked — that the poll is blended against the level the SPINE
    # settled on, not against the national baseline. The blend reads
    # `_mu = float(centres.get(_party, 0.0))`, so that is what is asserted.
    # Updated deliberately, 2026-08-22, MODEL-LOG §1.69: the old literal went
    # stale with the mechanism and failed while the property held.
    assert '_mu = float(centres.get(_party, 0.0))' in src, (
        "the poll blend must be taken against `centres` — the level the spine "
        "settled on — and not against the national baseline")
    # REPLACED 2026-08-25 (§1.96). This was a SOURCE-TEXT assertion on the
    # literal line `_w = min(_pg.blend_weight(_psd, _msd), _cap)`, and it
    # managed both failure modes of that technique inside one week: it PASSED
    # for weeks while the property it named ("bounded by weight_cap") was false,
    # because `_cap` is 1.0 under SIGMA_TWO_TERM; then it FAILED on a variable
    # rename that changed no behaviour. The arithmetic now has a seam,
    # `montecarlo.blend_poll_centre`, and the invariant is asserted on VALUES.
    for mu, share, w_raw in ((0.40, 0.25, 0.50), (0.18, 0.42, 0.90),
                             (0.05, 0.05, 0.30), (0.60, 0.10, 1.00)):
        centre, w = M.blend_poll_centre(mu, share, w_raw)
        assert 0.0 <= w <= 1.0, (
            f"the poll blend weight is {w}, outside [0, 1]. The blend would "
            f"not be a convex combination and the centre could overshoot the "
            f"poll or move away from it.")
        assert min(mu, share) - 1e-12 <= centre <= max(mu, share) + 1e-12, (
            f"blending model {mu} with poll {share} gave {centre}, outside the "
            f"interval between them.")
        assert M.blend_poll_centre(mu, share, w_raw, 0.0)[0] == mu, (
            "poll_credence=0 must return the model centre EXACTLY — a reader "
            "who says they do not believe the polls must get a forecast with "
            "no poll in it, not one with a little poll in it.")
        far = M.blend_poll_centre(mu, share, w_raw, 50.0)[0]
        assert abs(far - share) < 1e-12, (
            f"an unbounded credence gave {far}, not the poll's own {share}. "
            f"The weight must clamp at 1, so the most a reader can do is "
            f"believe the poll entirely.")
        near = M.blend_poll_centre(mu, share, w_raw, 0.5)[0]
        assert abs(near - share) >= abs(centre - share) - 1e-12, (
            "halving credence moved the centre CLOSER to the poll; the blend "
            "is not monotone in belief.")


# ---------------------------------------------------------------------------
# CLASS 5 — lost namespace
# ---------------------------------------------------------------------------

def test_no_module_defaults_a_processed_path_to_the_shared_root():
    """`data/processed` is JOHANNESBURG's directory, not a neutral one.

    A literal default there made `--city tshwane` read Johannesburg's turnout, γ
    and ward parts, and then write its interactive_data.json over the file the
    published page loads.
    """
    offenders = []
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            if not (isinstance(fn, ast.Attribute) and fn.attr == "add_argument"):
                continue
            names = [a.value for a in node.args if isinstance(a, ast.Constant)]
            if not any(str(n).lstrip("-").replace("-", "_") in
                       ("processed", "out") for n in names):
                continue
            for kw in node.keywords:
                if kw.arg != "default":
                    continue
                literal = ast.unparse(kw.value)
                if "data/processed'" in literal or 'data/processed"' in literal:
                    offenders.append(f"{path.name}: {names} default={literal}")
    assert not offenders, (
        "these default a per-city path to the shared root:\n  "
        + "\n  ".join(offenders)
        + "\nResolve it from the target AFTER --city is parsed.")


# ---------------------------------------------------------------------------
# CLASS 6 — display limit leaking into data
# ---------------------------------------------------------------------------

def test_a_data_producer_never_reads_a_truncated_report():
    """`top` is a terminal width. Anything storing this output must pass None."""
    # Build a REAL payload rather than a hand-made fixture: format_report reads
    # a dozen keys and a fixture drifts out of date the moment one is added.
    draws = [{f"P{i}": 20 - i for i in range(20)} for _ in range(40)]
    actual = {f"P{i}": 20 - i for i in range(20)}
    seats = S.score_seats(draws, actual)

    import re as _re
    # Party rows only. A loose startswith("P") also matches the PIT histogram
    # line, which is how this test first reported 13 rows for a top of 12.
    def rows(text):
        return sum(1 for l in text.splitlines()
                   if _re.match(r"^  P\d+\s+\d+", l))
    assert rows(S.format_report(seats, top=12)) == 12
    assert rows(S.format_report(seats, top=None)) == 20, (
        "format_report(top=None) must print every scored party")

    bv = (SRC / "build_validation.py").read_text()
    assert "--all-parties" in bv, (
        "build_validation.py builds validation_<year>.json by parsing the "
        "backtest's human-readable table. Without --all-parties it stores "
        "whatever fitted a terminal — twelve rows, for targets with 15 to 24 "
        "seat-winners — and every seat error computed from that file is "
        "truncated and not comparable to one summed over the whole ballot.")


# ---------------------------------------------------------------------------
# CLASS 7 — never-executed path
# ---------------------------------------------------------------------------

def test_the_polling_channel_actually_runs():
    """It raised NameError the instant the channel was switched on.

    It looked unused because the default weight was 0 and nothing exercised it.
    It was not unused, it was broken — and it is the only pre-election evidence
    that exists for a party with no history.

    **Rewritten 2026-08-22 (MODEL-LOG §1.69).** The test used to open the
    channel with `--set poll_id=... poll_weight=0.3`, and §1.68 deleted all
    three legacy keys, so it failed with `SystemExit: unknown scenario key:
    'poll_id'` — a stale test, not a broken model. It now drives the LIVE path
    the 2026 forecast actually uses (`poll_paths`, the register, `screen`),
    which makes it a stronger guard than the one it replaces: it checks both
    that the channel runs when switched on AND that switching it off silences
    it. A channel that cannot be switched off cannot be measured, which is the
    whole reason `poll_paths` exists (§1.65).
    """
    polls_path = ROOT / "polls.json"
    if not polls_path.exists():
        skip("no polls.json")

    city = cityconfig.use("joburg")
    target = cityconfig.use_target("2026")
    M.apply_city(city)
    spec = city.processed / f"pools_{target.year}.json"
    if not spec.exists():
        skip(f"no pool spec at {spec}")

    def notes_with_polls(setting):
        scenario = M.load_scenario(argparse.Namespace(
            config=None, set=[f"poll_paths={setting}"],
            draws=40, seed=None, city="joburg", target="2026"))
        run = M.run_model(target, scenario, Path("data/raw/elections"),
                          verbose=False)
        return [p for p, note in run.notes.items() if "polls " in note]

    on = notes_with_polls("all")
    assert on, (
        "poll_paths=all produced no poll note on any party — the branch did "
        "not execute. It previously raised NameError here.")
    off = notes_with_polls("off")
    assert not off, (
        f"poll_paths=off still blended polls into {off} — the switch does not "
        f"switch the channel off, so the 48 coherent seats of MODEL-LOG §1.65 "
        f"were measured against a baseline that still had polls in it.")


# ---------------------------------------------------------------------------
# CLASS 8 — summary artefact
# ---------------------------------------------------------------------------

def test_the_generic_entrant_is_relabelled_wherever_it_is_reported():
    """The model draws a GENERIC entrant; reporting it as its own party lies twice.

    At Johannesburg 2016 the unrelabelled report showed the AIC at 0.00%
    predicted against 1.62% actual (a total miss) AND ENTRANT at 1.46% against
    0.00% (pure phantom). They are the same forecast, and it was within 0.17pp.

    This test used to grep diagnose.py for a function name and stop there. It
    passed all the way through 2026-08-16 while `compare_history` — the module
    that produces the actual scoreboard — relabelled nothing outside `score_seats`,
    costing 8 seats of error per city-year with an arrival (MODEL-LOG §1.31). A
    source grep on one file is not a test of the behaviour. So: assert the
    behaviour, and assert it of EVERY module that computes an entrant.
    """
    import numpy as np
    import backtest as B

    # 1. The relabel itself moves everything, not just the seat draws.
    class _Run:
        pass
    run = _Run()
    run.universe = ["ANC", "DA", "ENTRANT"]
    run.index = {"ANC": 0, "DA": 1, "ENTRANT": 2}
    run.seat_draws = [{"ANC": 5, "ENTRANT": 3}, {"ANC": 6, "ENTRANT": 2}]
    run.ward_win_sum = {"ANC": 10, "ENTRANT": 4}
    run.overhang_count = {"ENTRANT": 1}
    run.notes = {"ENTRANT": "generic"}
    run.pr_share_draws = np.array([[0.5, 0.3, 0.2], [0.5, 0.3, 0.2]])
    run.ward_share_draws = None
    run.ward_winner_counts = None

    B.relabel_run(run, "ACTIONSA")
    assert "ENTRANT" not in run.index and "ACTIONSA" in run.index, (
        "relabel_run left ENTRANT in the index, so every table keyed on the "
        "index still reports a phantom party and a total miss")
    assert all("ENTRANT" not in d for d in run.seat_draws), \
        "seat draws still carry ENTRANT — it will score as a phantom"
    assert run.seat_draws[0]["ACTIONSA"] == 3
    assert "ENTRANT" not in run.ward_win_sum and run.ward_win_sum["ACTIONSA"] == 4
    assert "ENTRANT" not in run.overhang_count
    # The share column is keyed by index, so renaming the index is enough; the
    # column itself must NOT be zeroed or the arrival's vote disappears.
    assert run.pr_share_draws[0, run.index["ACTIONSA"]] == 0.2

    # 2. No party arrived: the entrant is NOT relabelled away, because the model
    #    should pay for predicting an arrival that did not happen.
    run2 = _Run()
    run2.universe = ["ANC", "ENTRANT"]
    run2.index = {"ANC": 0, "ENTRANT": 1}
    run2.seat_draws = [{"ENTRANT": 3}]
    B.relabel_run(run2, None)
    assert run2.seat_draws[0].get("ENTRANT") == 3, (
        "an entrant drawn where no party arrived must stay visible as error")

    # 3. Every module that works out WHICH party arrived must then apply it to
    #    the run, not to one call site. This is the fault that got through.
    for module in ("compare_history.py", "diagnose.py"):
        src = (SRC / module).read_text()
        if "entrant_actual_for" not in src:
            continue
        assert "relabel_run" in src or "relabel_entrant" in src, (
            f"{module} computes which party arrived but never applies it to the "
            f"run. Every table it builds — votes, rank bands, seat error — will "
            f"then count the arrival machinery as a total miss AND a phantom, "
            f"which is the same forecast scored twice in opposite directions.")


def test_a_seat_point_forecast_that_is_reported_as_a_council_sums_to_one():
    """Marginal medians do not sum to a chamber; the coherent one must.

    The median of a sum is not the sum of medians. At Johannesburg 2021 the
    per-party medians sum to 243 seats against a 270-seat council, so 27 of the
    reported seat error was the aggregation rather than the model — while the
    baselines allocate per draw and sum exactly, which made every seat-error
    comparison unfair to this side.

    Both are kept, because the per-party median is what a reader wants beside a
    per-party actual. What must not happen is one being presented as the other.
    """
    import compare_history as C

    council = 270
    draws = [{"A": 100 + (i % 7), "B": 90 - (i % 5), "C": 40, "D": 20, "E": 20}
             for i in range(60)]

    coherent = C.coherent_seats(draws, council)
    assert sum(coherent.values()) == council, (
        f"coherent_seats returned {sum(coherent.values())} seats for a council "
        f"of {council}. A point forecast presented as a chamber must be one.")
    assert all(v >= 0 for v in coherent.values())

    src = (SRC / "compare_history.py").read_text()
    assert "median_sum" in src and "seat_abs_err_coherent" in src, (
        "compare_history must report BOTH seat errors and what the medians "
        "actually sum to, or the incoherent one will be read as a council")
    assert "do not sum to a council" in src, (
        "seats_from_draws must say in its docstring that its output is not a "
        "chamber; this was reported as one for the whole of a review cycle")


# ---------------------------------------------------------------------------
# CLASS 9 — dead code that reads like live machinery
# ---------------------------------------------------------------------------

def test_no_top_level_function_is_defined_and_never_used():
    """A superseded function is worse than no function: it reads as the mechanism.

    `pools.apply_arrivals` documented, in detail, how an arrival takes votes out
    of its pools and leaves the rest to be shared in proportion. It had not been
    called in a long time — the debit happens at draw time, when the pool
    renormalises — so anyone reading pools.py to understand arrivals was reading
    a description of code that never ran. Also removed: `election_decimal_year`
    (superseded by `polling_decimal_year`), `metro_ward_shares`, and
    `build_site.build_documents` with its CARDS table, which built a landing
    page that the forecast replaced as index.html.

    ALLOWED is deliberately empty. Add a name to it only with a reason, and
    prefer deleting the function.
    """
    ALLOWED: set[str] = set()

    text = "\n".join(f.read_text() for f in
                     sorted(SRC.glob("*.py")) +
                     sorted((ROOT / "tests").glob("*.py")))
    dead = []
    for path in sorted(SRC.glob("*.py")):
        for node in ast.parse(path.read_text()).body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            name = node.name
            if name.startswith("_") or name == "main" or name in ALLOWED:
                continue
            if len(re.findall(rf"\b{re.escape(name)}\b", text)) <= 1:
                dead.append(f"{path.name}: {name}")
    assert not dead, (
        "defined and never referenced anywhere in src/ or tests/:\n  "
        + "\n  ".join(dead)
        + "\nDelete it, or call it, or add it to ALLOWED with a reason.")


# ---------------------------------------------------------------------------
# CLASS 10 — the registers drifting away from the code
# ---------------------------------------------------------------------------

def test_every_tunable_constant_is_in_the_judgement_register():
    """CLAUDE.md says the record changes in the same commit. This enforces it.

    A number that the data did not force must appear in JUDGEMENT-CALLS.md, or
    it will be mistaken for one that is measured -- and then none of them are
    trusted, which is that file's own stated reason for existing.

    **WIDENED 2026-08-23 (MODEL-LOG §1.86), because it inspected 53 names and
    was structurally blind to every shape the failures actually took.** It read
    only top-level `ast.Assign`, single target, UPPERCASE, literal int/float.
    It therefore could not see:

    * **numeric DEFAULT ARGUMENTS** — the `LEVEL_DF` shape, three instances,
      the latest costing 5.6pp of ANC in the live forecast (§1.84);
    * **argparse defaults** — where `w_recency = 0.70` and `kappa_bye = 0.25`
      have lived since the original plan, unregistered, reaching the model
      through 20 committed `turnout.csv` files that carry no artefact key;
    * **container constants** — `PLAN_BOUNDS` (the plan's theta table),
      `GAMMA_FOLD` (which fold the live forecast uses);
    * **non-numeric `DEFAULTS` values** — `overhang_rule`, a legal
      interpretation that sets council size and the majority threshold;
    * **dataclass fields** — `Config.max_extrapolation`;
    * **numbers in TOML** — `config/dimensions.toml`'s `min_oos_gain`, which
      decides which census dimensions exist at all.

    THREE PRINCIPLED FILTERS keep this from drowning in noise, and each is a
    rule rather than a list:

    1. **run control is not belief** — `draws`, `seed`, `jobs`, `tolerance`;
    2. **a counter initialised to zero is not a claim** — `ModelRun`'s
       accumulators start at 0 because that is what accumulators do;
    3. **a container is a judgement only if it CONTAINS NUMBERS** — a table of
       column names or file paths is structure; a table of bounds is belief.

    Those three take 144 raw hits down to 26, which is the number a person can
    actually triage. `EXEMPT` then names what is left and operational, and
    adding to it is itself a judgement someone has to write down.
    """
    EXEMPT = {
        "SOLVE_TOL", "draws", "seed", "COUNCIL",      # run control, not belief
        "SD_FLOOR", "SD_CEILING",                     # bounds on a MEASURED fit
        "MIN_HOME_SPLITS",                            # registered under its own name
        # `theta_residual.py` MEASURES the model; it is not part of it.
        # `SIM_DRAWS` and `NULL_REPS` bound how precisely a REFERENCE
        # distribution is simulated — the t sample behind `nll_t`'s calibrated
        # offset and the shape ratio's null. Neither can reach a forecast.
        # Added 2026-08-29 (§1.130) after this guard correctly caught a bare
        # `reps=2000` in a new signature.
        "BOOT", "BOOT_SEED", "SIM_DRAWS", "NULL_REPS",
        # --- operational residue surfaced by the 2026-08-23 widening ---
        "timeout",        # HTTP timeouts in the three fetch_* tools
        "steps",          # `_scale_into_box` solver iterations
        "pad",            # logo whitespace in prep_logos
        "simplify",       # polygon simplification for the map renderer
        "min_seats",      # a REPORTING threshold in arrivals.py, not a model input
        # The delivery-proof recorder (NULL-RESULTS.md §4.1). Both are
        # OPERATIONAL — they bound the SIZE of a log, not anything the model
        # computes. DELIVERY_MAX_VALUES caps how many distinct values are kept
        # per name, because the scenario is serialised into forecast_summary.json
        # on every run; `depth` bounds the recursion that summarises a value for
        # the log; DELIVERY_MAX_CHARS collapses a value that is small by COUNT
        # and enormous by CONTENT (levels.KNOWN_ABSENT is fourteen entries of
        # prose reason), replacing it with a count and a digest. None can reach
        # a forecast — `note_value` returns its argument unchanged, proven
        # bit-identical against HEAD.
        "DELIVERY_MAX_VALUES", "DELIVERY_MAX_CHARS", "depth",
        "LEVELS",         # the nominal coverage levels 50/80/90 a report prints
        "LGE_YEARS", "LGE_ELECTIONS", "FOLDS",        # calendar/route structure
        "independent_wards", "no_pr_list_wards",      # per-call council facts
    }
    RUN_CONTROL = {"draws", "seed", "jobs", "n_jobs", "verbose", "tolerance",
                   "report", "bins", "replicates", "boot", "max_draws",
                   "chunk", "limit", "width"}

    def _has_number(v):
        if isinstance(v, bool):
            return False
        if isinstance(v, (int, float)):
            return True
        if isinstance(v, dict):
            return any(_has_number(x) for x in v.values()) or any(
                _has_number(k) for k in v)
        if isinstance(v, (list, tuple, set, frozenset)):
            return any(_has_number(x) for x in v)
        return False

    reg = (ROOT / "JUDGEMENT-CALLS.md").read_text()
    found: dict[str, str] = {}          # name -> where it was seen

    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            # (a) numeric default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                a = node.args
                pairs = (list(zip(a.args[-len(a.defaults):], a.defaults))
                         if a.defaults else [])
                pairs += [(k, d) for k, d in zip(a.kwonlyargs, a.kw_defaults)
                          if d is not None]
                for arg, d in pairs:
                    if (isinstance(d, ast.Constant)
                            and isinstance(d.value, (int, float))
                            and not isinstance(d.value, bool)
                            and arg.arg not in RUN_CONTROL):
                        found.setdefault(
                            arg.arg,
                            f"{path.name}:{node.lineno} {node.name}({arg.arg}={d.value})")
            # (b) argparse defaults
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "add_argument"):
                flag = (node.args[0].value
                        if node.args and isinstance(node.args[0], ast.Constant)
                        else "")
                name = str(flag).lstrip("-").replace("-", "_")
                for kw in node.keywords:
                    if (kw.arg == "default"
                            and isinstance(kw.value, ast.Constant)
                            and isinstance(kw.value.value, (int, float))
                            and not isinstance(kw.value.value, bool)
                            and name and name not in RUN_CONTROL):
                        found.setdefault(
                            name, f"{path.name}:{node.lineno} {flag}={kw.value.value}")
        for node in tree.body:
            # (c) dataclass fields with a NON-ZERO numeric default
            if isinstance(node, ast.ClassDef):
                for sub in node.body:
                    if (isinstance(sub, ast.AnnAssign)
                            and isinstance(sub.value, ast.Constant)
                            and isinstance(sub.value.value, (int, float))
                            and not isinstance(sub.value.value, bool)
                            and sub.value.value != 0):
                        found.setdefault(
                            sub.target.id,
                            f"{path.name}:{sub.lineno} {node.name}.{sub.target.id}")
            # (d) module constants: scalars as before, PLUS containers holding numbers
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)):
                n = node.targets[0].id
                if n.startswith("_") or not n.isupper():
                    continue
                try:
                    v = ast.literal_eval(node.value)
                except Exception:
                    continue
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    found.setdefault(n, f"{path.name}:{node.lineno} {n}")
                elif (isinstance(v, (dict, tuple, list, set, frozenset))
                        and _has_number(v)):
                    found.setdefault(n, f"{path.name}:{node.lineno} {n}")

    # (e) EVERY DEFAULTS value, numeric or not. `overhang_rule` is a string and
    #     it sets the council size.
    import montecarlo as _mc
    for k, v in _mc.DEFAULTS.items():
        if isinstance(v, dict) and not v:
            continue                     # `pools`/`entrant_geography`: data, not a value
        found.setdefault(k, f"montecarlo.DEFAULTS[{k!r}]")

    # (f) numbers in the TOML the model reads
    import tomllib
    for toml in [ROOT / "config" / "dimensions.toml"]:
        if not toml.exists():
            continue
        def _walk(d, prefix=""):
            for k, v in d.items():
                if isinstance(v, dict):
                    _walk(v, f"{prefix}{k}.")
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    found.setdefault(k, f"{toml.name}:{prefix}{k} = {v}")
        _walk(tomllib.loads(toml.read_text()))

    missing = sorted(f"{n}   ({where})" for n, where in found.items()
                     if n not in EXEMPT and n not in reg)
    assert not missing, (
        f"{len(missing)} tunable constants are not named in JUDGEMENT-CALLS.md:\n  "
        + "\n  ".join(missing)
        + "\n\nRegister each with its value, its evidence and its status, or add "
          "it to EXEMPT with a reason if it is operational. This test was widened "
          "on 2026-08-23 and every category above was invisible to it before — "
          "which is why `poll_half_life_days` could move 5.6pp of the live "
          "forecast through a default argument nobody could sweep.")


# ---------------------------------------------------------------------------
# CLASS 11 — a constant that cannot be swept
# ---------------------------------------------------------------------------

def test_a_scenario_override_survives_apply_city():
    """A sweep must reach the run, or its flat result is a lie about the model.

    `entrant_prob` was swept over the nine city-years at 0.25 and 0.55 by editing
    `montecarlo.DEFAULTS`, and both rows came back identical to the decimal —
    CRPS 269.9, 314 seats, ranks 4-12 -37.4pp. The reading "this constant is
    inert" was wrong: `apply_city` writes `cities/joburg.toml`'s scalars over
    DEFAULTS *after* the edit, and `entrant_prob` is one of the sixteen it sets.
    Swept honestly through `--set`, the same constant moves Johannesburg 2016's
    ranks 4-12 from -0.92pp to +2.87pp. See MODEL-LOG §1.31.
    """
    city = cityconfig.use("joburg")
    M.apply_city(city)
    sc = M.load_scenario(argparse.Namespace(
        config=None, set=["entrant_prob=0.99"], draws=10, seed=None,
        city="joburg", target="2016"))
    assert sc["entrant_prob"] == 0.99, (
        "a --set override did not survive apply_city, so every sweep run "
        "through this path silently measures the committed value instead")

    # And the harness must expose that override, or there is no honest way to
    # sweep anything from the command line — which is how the flat rows happened.
    src = (SRC / "compare_history.py").read_text()
    assert '"--set"' in src, (
        "compare_history has no --set, so the only way to sweep a constant is "
        "to edit DEFAULTS, which apply_city overwrites. Every such sweep returns "
        "identical rows and reads as a dead constant.")
    assert "set=list(overrides" in src or "set=overrides" in src, (
        "compare_history parses --set but hardcodes set=None when it builds the "
        "scenario, so the flag is accepted and discarded")


def test_apply_city_does_not_leak_one_citys_scalars_into_the_next():
    """DEFAULTS is a module global and apply_city never resets it.

    joburg.toml sets sixteen scalars; six of the eight metro configs set none.
    So in a multi-city run every city after Johannesburg inherits Johannesburg's
    judgement values. Harmless *today* only because those sixteen currently equal
    DEFAULTS — the config was generated from them. That is a coincidence the
    code does not enforce, and it is exactly the coincidence that will be broken
    by the next per-city tuning. This test fails when it is.
    """
    import copy
    import tomllib
    pristine = copy.deepcopy(M.DEFAULTS)
    try:
        with open(ROOT / "cities" / "joburg.toml", "rb") as fh:
            raw = tomllib.load(fh)
        scalars = ((raw.get("judgements") or raw).get("scalars")
                   or raw.get("scalars") or {})
        differing = {k: (v, pristine.get(k)) for k, v in scalars.items()
                     if not k.endswith("_note")
                     and k in pristine and v != pristine[k]}
        assert not differing, (
            "cities/joburg.toml now disagrees with montecarlo.DEFAULTS on "
            f"{sorted(differing)}. apply_city writes these into the module "
            "global and never resets it, so every city that follows Johannesburg "
            "in a multi-city run will silently inherit Johannesburg's value. "
            "Either give apply_city a reset, or restate the key in every city's "
            "toml so no city is running on another's judgement.")
    finally:
        M.DEFAULTS.clear()
        M.DEFAULTS.update(pristine)




def test_no_ward_is_published_at_probability_one():
    """A Monte Carlo estimate of 1.000 is a claim the draw count cannot support.

    25 of Johannesburg's 135 wards were published at `p_win = 1.0000` on the
    2026 forecast, every one of them DA, and the map's tooltip rendered that as
    "DA — DA 100%". That asserts P(anyone else wins) is exactly zero.

    **Measured against Johannesburg 2021**, the wards this model called certain
    were right 31 times in 32 — ward 7 was PA at p = 1.000 and went ANC. An
    outcome at probability zero that then happens is an infinite log score.

    The estimator is now the Jeffreys posterior mean `(k + 1/2)/(N + 1)`, which
    cannot reach 0 or 1 from a finite sample. This test fails if anything
    reintroduces the raw fraction. MODEL-LOG §1.71.
    """
    path = ROOT / "data/processed/ward_winner_probs.csv"
    if not path.exists():
        skip("no ward_winner_probs.csv; run the model first")
    import csv as _csv
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    if not rows:
        skip("ward_winner_probs.csv is empty")
    certain = [r for r in rows if float(r["p_win"]) >= 1.0]
    assert not certain, (
        f"{len(certain)} ward(s) published at p_win = 1.000, e.g. ward "
        f"{certain[0]['ward']} ({certain[0]['winner']}). A probability of one "
        f"is not something 1,500 draws can establish; use the Jeffreys mean "
        f"(k + 1/2)/(N + 1). MODEL-LOG §1.71.")
    zero = [r for r in rows for kv in r["dist"].split("|")
            if kv and float(kv.split(":")[1]) <= 0.0]
    assert not zero, "a party is published at exactly p = 0 in a ward's dist"

def test_every_test_module_is_collected():
    """A test file the runner does not import reads as coverage and is not.

    `tests/run_all.py` keeps a hand-maintained `MODULES` list. On 2026-08-25
    `tests/test_freeze.py` was written and committed, the suite reported
    **201 passed, 0 failed**, and none of its five tests had run — the file was
    simply not in the list. The freeze it guards is the fixed reference the
    whole restructure is measured against, so the guard on the reference was
    itself unguarded.

    This is the same shape as every other defect found this week: a declaration
    made in one place, a consumer that does not read it, and nothing that can
    tell. The membership of `MODULES` is not a judgement call — the ORDER is,
    and that stays hand-written.
    """
    import run_all
    on_disk = {p.stem for p in sorted((ROOT / "tests").glob("test_*.py"))}
    listed = set(run_all.MODULES)
    missing = sorted(on_disk - listed)
    assert not missing, (
        f"test module(s) on disk but never collected by tests/run_all.py: "
        f"{missing}\nThe suite will report green without ever running them. "
        f"Add them to MODULES — position is your choice, membership is not.")
    stale = sorted(listed - on_disk)
    assert not stale, (
        f"tests/run_all.py lists module(s) that do not exist: {stale}\n"
        f"The suite would die on import; delete them from MODULES.")


if __name__ == "__main__":
    # `run_module`, NOT a hand-rolled loop. Until 2026-08-23 this file ended with
    # `for name, fn in sorted(globals().items()): ... fn()`, which catches
    # neither `SkipTest` nor `SystemExit` — so the FIRST skip aborted the run and
    # every later test in the file silently never executed, and no summary was
    # printed. Five files were in that state; `test_regressions` alone has five
    # `skip(` calls. Under `run_all.py` they were fine, because the suite calls
    # `run_module(vars(module))` itself — the suite hid it. MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
