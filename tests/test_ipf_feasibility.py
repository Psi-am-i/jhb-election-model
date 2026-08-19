"""Two CLASSES of error, both of which made a mechanism inoperative in silence.

Neither of these is a wrong number. Both are a piece of machinery that does not
run, reports nothing when it does not run, and therefore reads as working. The
model log's most expensive hours have gone on exactly this shape.

CLASS 12 — A GUARD THAT SWALLOWS THE MECHANISM IT GUARDS. A ``try`` whose
    ``except`` discards the whole computation and says nothing. Instance:
    ``montecarlo.draw_pools`` shocks the pool x party centres, re-balances them
    by IPF, and wrapped the balance in ``except Exception: pass``. When
    ``pools.balance_margins`` raised, ``pool_props`` kept the UNSHOCKED values —
    so the level shock was discarded **for every party in that draw**, not just
    for the party that made the problem infeasible.

    It fired in **42.7% of the draws of the live 2026 Johannesburg forecast**
    and 12.7% of Nelson Mandela Bay 2021's, and in none of the other eight
    backtested city-years. So no backtest could see it: over the nine city-years
    the rate was 1.4%, and forcing it to zero left eight of them bit-identical.
    It also fired PREFERENTIALLY on the draws where the shock was largest, which
    is the worst possible selection — the mechanism was absent exactly where it
    mattered most. The cause was a party asked for more votes than the pools it
    belongs to contain (the PA, 102% of every Coloured vote cast in
    Johannesburg); the cure here is a guard, not a fix. See MODEL-LOG §1.33.

CLASS 13 — A CONSTANT FROZEN AT IMPORT. A module constant written as a default
    argument, ``def f(..., df: float = LEVEL_DF)``, which Python evaluates once
    when the module loads. Setting ``montecarlo.LEVEL_DF`` afterwards changes
    nothing, so a sweep of it returns identical rows and reads as "this constant
    does nothing" when the truth is "you did not change it". ``LEVEL_DF`` was
    swept at 2.5, 4, 7, 30, 200 and 1000 for byte-identical output every time,
    while sitting at 🔴 in ``JUDGEMENT-CALLS.md`` as one of the most-attacked
    numbers in the register.

    This is the same shape as CLASS 11 in ``test_regressions.py``
    (``entrant_prob``, overwritten by ``apply_city`` after the edit) reached by
    a different route, and it is what ``ITERATING.md`` rule 6 is for: before
    tuning a constant, sweep it to a value that MUST change the answer and
    confirm the answer changes.

Run:
    ./.venv/bin/python tests/test_ipf_feasibility.py
    ./.venv/bin/python -m pytest tests/test_ipf_feasibility.py -q
"""

from __future__ import annotations

import ast
import copy
import csv
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, skip  # noqa: E402

SRC = ROOT / "src"

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402

CITY = "joburg"
TARGET = "2026"
SEED = 20261104
ELECTIONS = ROOT / "data" / "raw" / "elections"
PROCESSED = ROOT / "data" / "processed"


# --------------------------------------------------------------------------
# fixture — the 2026 configuration, which is the only one that shows the defect
# --------------------------------------------------------------------------

_INPUTS: dict[str, tuple] = {}


def build_inputs():
    """(scenario, base_city_d, centres, index) for the live 2026 forecast.

    Deliberately the SAME assembly ``tests/test_drawer.build_inputs`` uses, so
    the two files exercise one configuration rather than two. It is the 2026 one
    because the defect this file guards does not appear anywhere else: the nine
    backtested city-years fire it in 1.4% of draws, all of them at Nelson
    Mandela Bay, and a test built on them would pass with the bug in place.
    """
    if "v" in _INPUTS:
        return _INPUTS["v"]
    city = cityconfig.load(CITY)
    cityconfig.use(CITY)
    M.apply_city(city)
    scenario = copy.deepcopy(M.DEFAULTS)

    base_path = ELECTIONS / "npe2024_{CODE}_vd_party.csv"
    if not cityconfig.resolve_path(base_path).exists():
        skip(f"no national baseline for {CITY} at {base_path}")
    base_votes, _ = M.load(base_path, None)
    base_city_d = M.citywide(base_votes)

    universe = sorted(p for p in base_city_d if p not in (M.INDEPENDENT, "IND"))
    if scenario["entrant_prob"] > 0:
        universe.append("ENTRANT")
    index = {party: i for i, party in enumerate(universe)}

    lge_path = ELECTIONS / "lge2021_{CODE}_vd_party_clean.csv"
    if not cityconfig.resolve_path(lge_path).exists():
        skip(f"no 2021 result file for {CITY} at {lge_path}")
    pr21, _ = M.load(lge_path, "PR")
    share_2021 = M.citywide(pr21)

    bye: dict[str, tuple[float, float]] = {}
    bye_path = PROCESSED / "byelection_party_deltas.csv"
    if bye_path.exists():
        with bye_path.open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                bye[row["party"]] = (float(row["weight_sum"]),
                                     float(row["weighted_delta"]))

    spec_path = city.processed / f"pools_{TARGET}.json"
    if not spec_path.exists():
        skip(f"no pool spec at {spec_path} — run: python src/pools.py "
             f"--city {CITY} --target {TARGET} --emit")
    scenario["pools"] = json.loads(spec_path.read_text())["pools"]

    # THE LEVEL LAYER, as `run_model` builds it. This fixture had the same
    # defect `test_drawer.py` did: it loaded the pool spec and stopped, so every
    # party fell through the precedence chain to constants the forecast never
    # reaches. Deleting those constants (§1.52) surfaced both. Two fixtures
    # were characterising a configuration the model does not run.
    import levels as _levels
    _target = cityconfig.use_target("2026")
    _prior, _groups = _levels.theta_prior(_target, base_city_d)
    if _prior:
        scenario["theta_prior"] = _prior
        scenario["_theta_sd"] = _groups.get("sd", {})
    _spine, _ = _levels.spine(_target, base_city_d, share_2021)
    if _spine:
        scenario["spine_level"] = _spine

    centres, _ = M.blended_centres(scenario, base_city_d, share_2021, bye)
    if "ENTRANT" in index:
        centres["ENTRANT"] = 0.0
    _INPUTS["v"] = (scenario, base_city_d, centres, index)
    return _INPUTS["v"]


def draw_with_spy(draws: int = 200):
    """Run ``draws`` draws, recording every ``(R, pool_votes, col_target)``.

    Spies on ``montecarlo._balance``, which is the ONLY route the per-draw path
    takes into ``pools.balance_margins``. ``pool_spec`` calls ``balance_margins``
    directly, so the spy sees the per-draw calls and nothing else — which is
    what both tests below want.
    """
    scenario, base_city_d, centres, index = build_inputs()
    seen: list[tuple[np.ndarray, np.ndarray, np.ndarray]] = []
    real = M._balance

    def spy(R, electorate, party_votes):
        seen.append((R.copy(), np.asarray(electorate).copy(),
                     np.asarray(party_votes).copy()))
        return real(R, electorate, party_votes)

    M._balance = spy
    try:
        rng = np.random.default_rng(SEED)
        draw = M.make_drawer(scenario, base_city_d, centres, index, rng)
        for _ in range(draws):
            draw()
    finally:
        M._balance = real
    return draw, seen


# --------------------------------------------------------------------------
# CLASS 12 — the guard that swallowed the mechanism
# --------------------------------------------------------------------------

def test_the_balance_is_never_asked_for_more_than_the_pools_can_hold():
    """IPF cannot satisfy two margins that cannot both hold. Do not ask it to.

    A party can take at most every vote cast in the pools it belongs to. Ask for
    more and ``pools.balance_margins`` is not slow, it is impossible: it runs to
    its 2000-iteration cap and raises. (Measured: 20,000 iterations at tol 1e-9
    took the failure rate from 40.9% to 38.9%, which is what genuine
    infeasibility looks like rather than slow convergence.)

    The instance was the PA at Johannesburg 2026 — one pool, Coloured, casting
    about 66,700 votes, against a shocked centre asking for up to 136,000. The
    review's isolated draw read column 34: capacity 66,684.8, asked 68,020.3.

    This asserts on the NUMBERS the balance was handed, not on the source: a
    clip written into the code and then undone by a later rescale would pass a
    source-text check and fail this one. Both rescales that would undo it are
    real — ``pool_spec``'s ``want / want.sum()`` and ``balance_margins``' own
    ``target_cols *= target_rows.sum() / target_cols.sum()`` — which is why
    ``montecarlo.capped_targets`` preserves the total instead of removing mass.
    """
    _draw, seen = draw_with_spy(200)
    assert seen, ("no per-draw balance was attempted at all, so this test "
                  "asserts nothing — has the centres-bind mechanism been "
                  "removed, or has _balance stopped being the route to it?")
    worst = 0.0
    worst_where = ""
    for k, (R, pool_votes, col_target) in enumerate(seen):
        # A party's capacity is the votes in the pools its column can reach.
        # IPF preserves structural zeros, so R's support IS its reach.
        reach = R > 0
        capacity = np.array([pool_votes[reach[:, j]].sum()
                             for j in range(R.shape[1])])
        over = col_target > capacity * (1.0 + 1e-9)
        if over.any():
            j = int(np.argmax(col_target - capacity))
            ratio = float(col_target[j] / max(capacity[j], 1e-12))
            if ratio > worst:
                worst, worst_where = ratio, (
                    f"draw {k}, column {j}: capacity {capacity[j]:,.1f} votes, "
                    f"asked {col_target[j]:,.1f}")
    assert worst == 0.0, (
        "the per-draw IPF was handed a column target above that party's own "
        f"pool capacity ({worst:.0%} of it) — {worst_where}.\n"
        "balance_margins cannot converge on this and raises, and every party's "
        "level shock in that draw is lost with it. Cap the shocked column "
        "targets with montecarlo.capped_targets before balancing, and note that "
        "a plain clip does not survive: balance_margins rescales the column "
        "margin back to the row total on entry.")


def test_a_failed_balance_is_counted_and_reported_rather_than_passed():
    """A silent failure of the model's central mechanism is not permitted.

    The branch was ``except Exception: pass``. It fired in 42.7% of the live
    2026 forecast's draws and nothing anywhere said so — not the run report, not
    the ModelRun, not the published summary. `JUDGEMENT-CALLS.md` did not carry
    it either, because nobody knew there was a judgement being made.

    So: force the balance to fail, and require that (a) the failure is counted,
    (b) the draw still returns a probability vector, and (c) the fallback is a
    partial balance rather than the unshocked proportions — because discarding
    the shock for every party is what made this defect expensive.
    """
    scenario, base_city_d, centres, index = build_inputs()
    real = M._balance

    def always_raise(R, electorate, party_votes):
        raise RuntimeError("margin balancing did not converge")

    M._balance = always_raise
    try:
        rng = np.random.default_rng(SEED)
        draw = M.make_drawer(scenario, base_city_d, centres, index, rng)
        vectors = [draw() for _ in range(5)]
    finally:
        M._balance = real

    stats = getattr(draw, "ipf_stats", None)
    assert stats is not None, (
        "make_drawer's closure carries no ipf_stats, so run_model has no way to "
        "learn that the per-draw balance failed and no test can assert on it. "
        "That is the state the bug lived in.")
    assert stats["balances"] == 5, (
        f"5 draws attempted {stats['balances']} balances — the counter is not "
        f"counting the attempts, so any rate computed from it is wrong")
    assert stats["failures"] == 5, (
        f"every balance was forced to raise and only {stats['failures']} of 5 "
        f"were counted. A failure that is not counted cannot be reported, and "
        f"an unreported failure of the centres-bind mechanism is exactly the "
        f"defect this file exists for.")
    for v in vectors:
        assert abs(float(np.sum(v)) - 1.0) < 1e-9 and (v >= 0).all(), (
            "a draw stopped being a probability vector when the balance failed")

    # (c) the fallback must still BE a balance. Three draws off the same seed:
    # the healthy one, the fallback, and the old `pass` behaviour reconstructed
    # by making the fallback hand back the un-rebalanced R0. The fallback has to
    # sit far closer to the healthy draw than the old behaviour does, or the
    # level shock is still being thrown away and only the counter has changed.
    def draw_once(balance_raises: bool, partial=None) -> np.ndarray:
        real_partial = M.partial_balance
        M._balance = always_raise if balance_raises else real
        if partial is not None:
            M.partial_balance = partial
        try:
            rng = np.random.default_rng(SEED)
            return M.make_drawer(scenario, base_city_d, centres, index, rng)()
        finally:
            M._balance = real
            M.partial_balance = real_partial

    healthy = draw_once(False)
    fallback = draw_once(True)
    discarded = draw_once(True, partial=lambda R, pv, ct, passes=None: R)
    near = float(np.abs(fallback - healthy).sum())
    far = float(np.abs(discarded - healthy).sum())
    assert near < far / 10, (
        f"the failure path lands {near:.4f} from the healthy draw and simply "
        f"discarding the shock lands {far:.4f} from it — the fallback is not "
        f"materially better than `except Exception: pass`, which discarded the "
        f"level shock for EVERY party in the draw, not just the offender")

    # And the field must exist on ModelRun, or nothing surfaces it to a report.
    for name in ("ipf_balances", "ipf_failures", "ipf_clipped", "ipf_worst",
                 "ipf_headroom"):
        assert hasattr(M.ModelRun, "__dataclass_fields__") and \
            name in M.ModelRun.__dataclass_fields__, (
            f"ModelRun has no `{name}` field, so run_model cannot carry the "
            f"per-draw balance's health out of the loop and `main` cannot print "
            f"it — the same way bounds_violations is carried")


def test_capped_targets_preserves_the_total_it_is_given():
    """The invariant both rescale sites depend on. A plain clip breaks it.

    ``pools.balance_margins`` opens with
    ``target_cols *= target_rows.sum() / target_cols.sum()`` — IPF has no
    solution unless the two margins agree on the grand total — so a clip that
    merely removes mass is restored in full on the next line, to the offending
    column included. ``pool_spec``'s ``want / want.sum()`` does the same thing
    one stage earlier. Water-filling is what survives both.
    """
    rng = np.random.default_rng(7)
    for _ in range(200):
        n = int(rng.integers(3, 40))
        target = rng.random(n) * rng.integers(1, 1000)
        cap = rng.random(n) * rng.integers(1, 1000)
        cap[rng.integers(0, n)] = 0.0          # a party in no pool at all
        out = M.capped_targets(target, cap)
        if cap.sum() <= target.sum():
            continue                            # documented degenerate branch
        assert abs(out.sum() - target.sum()) < 1e-6 * max(target.sum(), 1.0), (
            f"capped_targets changed the total from {target.sum():.6f} to "
            f"{out.sum():.6f}. balance_margins will restore the difference by "
            f"rescaling the whole column margin, which puts the clipped party "
            f"straight back over its cap and the clip does nothing.")
        assert (out <= cap + 1e-9).all(), (
            "capped_targets left a column above its cap, which is the one "
            "thing it exists to prevent")


# --------------------------------------------------------------------------
# CLASS 13 — a constant frozen at import
# --------------------------------------------------------------------------

def test_level_df_reaches_the_draw():
    """Sweeping LEVEL_DF must change the answer. For months it could not.

    ``def log_shock(rng, sd, size=None, df: float = LEVEL_DF)`` binds the
    constant once, at import. Swept at 2.5, 4, 7, 30, 200 and 1000 the model
    returned byte-identical output at every value — while ``JUDGEMENT-CALLS.md``
    carried ``LEVEL_DF`` at 🔴 as one of the numbers most in need of attack.

    Now that it is read at call time the effect is real and it is in the tail,
    which is what the constant is for: at Johannesburg 2026 over 3,000 draws,
    MK's maximum drawn share runs 46.2% at df=3, 37.5% at df=7 and 33.8% at
    df=1000, and the DA's realised sd(log) runs 0.2395 / 0.1886 / 0.1835. It is
    NOT what makes MK's seat band wide — that band is 8-53 at df=2.5 and 8-57 at
    df=1000 (MODEL-LOG §1.33).

    Two assertions, because they fail for different reasons: the first pins the
    function, the second pins the path from the constant to a drawn vector.
    """
    original = M.LEVEL_DF
    try:
        sd = np.full(6, 0.30)
        M.LEVEL_DF = 2.5
        heavy = M.log_shock(np.random.default_rng(11), sd)
        M.LEVEL_DF = 1000.0
        light = M.log_shock(np.random.default_rng(11), sd)
        assert not np.allclose(heavy, light), (
            "log_shock returned the same draws at LEVEL_DF 2.5 and 1000, which "
            "differ by two orders of magnitude in tail weight. The constant is "
            "captured in the signature default and frozen at import: resolve it "
            "inside the function body instead. Every sweep of it until then "
            "measured 7.0.")

        scenario, base_city_d, centres, index = build_inputs()

        def draw_at(df: float) -> np.ndarray:
            M.LEVEL_DF = df
            rng = np.random.default_rng(SEED)
            drawer = M.make_drawer(scenario, base_city_d, centres, index, rng)
            return np.array([drawer() for _ in range(60)])

        assert not np.allclose(draw_at(2.5), draw_at(1000.0)), (
            "the drawer produced identical citywide vectors at LEVEL_DF 2.5 and "
            "1000, so the constant does not reach the draw however it is bound. "
            "ITERATING.md rule 6: a sweep that cannot change the answer is not "
            "evidence about the answer.")
    finally:
        M.LEVEL_DF = original


def test_no_numeric_module_constant_is_a_default_argument():
    """The generalising version of the test above. This is what stops the class.

    ``def f(x=SOME_CONSTANT)`` evaluates ``SOME_CONSTANT`` once, at import. Any
    later assignment to the module attribute — which is how every sweep in this
    repository is written, and how ``src/sweep.py`` and the ``--set`` harness
    both reach the model — is then invisible. The constant reads as inert at
    every value.

    Four sites were in this state when the rule was written: ``LEVEL_DF``
    (`montecarlo.log_shock`), ``SHARE_FLOOR`` (`fold.logit`, `montecarlo.logit`,
    `montecarlo.solve_and_predict`) and ``SPINE_K`` (`levels.spine`). All four
    now resolve in the body from a ``None`` sentinel.

    EXEMPT holds the module-level names that are CONTAINERS or PATHS rather than
    tunables — a dict of metro codes, a directory, a register file. They have the
    same late-binding hazard in principle (rebinding the module attribute does
    not reach the default) but nothing sweeps them, and mutating them in place
    does reach it. Adding a name to EXEMPT is itself a judgement someone has to
    write down; adding a NUMBER to it is not permitted.
    """
    EXEMPT = {
        "METRO_CODES",     # dict of city codes; mutated in place, never swept
        "REPORTS",         # a directory path
        "REGISTER",        # the polls register path
        "CONFIG",          # the pools config path
        "CLAIM_PATTERNS",  # regex table for the stat audit
    }
    offenders: list[str] = []
    for path in sorted(SRC.glob("*.py")):
        tree = ast.parse(path.read_text())
        numeric: dict[str, object] = {}
        top: set[str] = set()
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target]
            for t in targets:
                top.add(t.id)
                try:
                    value = ast.literal_eval(node.value)
                except Exception:
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    numeric[t.id] = value
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            defaults = list(node.args.defaults) + [
                d for d in node.args.kw_defaults if d is not None]
            for d in defaults:
                if not isinstance(d, ast.Name) or d.id not in top:
                    continue
                if d.id in EXEMPT and d.id not in numeric:
                    continue
                kind = "NUMBER" if d.id in numeric else "module-level name"
                offenders.append(
                    f"{path.name}:{node.lineno} {node.name}(... = {d.id})"
                    f"  [{kind}]")
    assert not offenders, (
        "these module-level constants are captured in a default argument and "
        "therefore frozen at import:\n  " + "\n  ".join(offenders)
        + "\nSet the parameter to None and resolve the constant in the "
          "function body, so that setting the module attribute reaches the "
          "call. Until you do, every sweep of these returns the committed "
          "value's rows and reads as a dead constant (ITERATING.md rule 6).")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
