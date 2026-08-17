"""CLASS 12 — A LEVER THAT DOES NOTHING.

A tunable that is declared, documented, registered as a judgement call, and has
no effect on any output. It is worse than a missing lever: it is quoted in
`JUDGEMENT-CALLS.md` as a choice the project made, argued over in review, and
swept for calibration — and every one of those activities is wasted, because the
answer does not depend on it.

This is distinct from CLASS 11 (`test_regressions.py`), which catches a constant
whose value *cannot be changed* from the command line. A CLASS 11 lever moves the
model once you reach it. A CLASS 12 lever does not move it at all.

The instances that motivated this file, all confirmed by an independent review on
2026-08-17 and each found by a different accident rather than by a test:

  * `LEVEL_DF` — bound as a default argument, `def log_shock(..., df=LEVEL_DF)`,
    evaluated once at import. Swept at 2.5, 4, 7, 30, 200 and 1000: BYTE-IDENTICAL
    output every time. It is 🔴 in the register, it is the most-attacked constant
    in the project, and it did nothing at any value anyone contemplated.
  * `polling_lean` / `polling_span` — `lean` is computed at `montecarlo.py:883`
    and passed to `pool_spec`, whose body never references the parameter. Inert
    at any value, not merely defaulted to zero.
  * `pool_spec`'s `base_city_d` argument — same thing, never referenced, and
    missed by the review.
  * `ward_pr_ratio_overrides` (MK 0.80, ENTRANT 0.80) — gated on `not fallback`,
    and `levels.ward_pr_ratios` returns a fallback at every target the harness
    can run. The code's own comment says the fallback REPLACES these two numbers;
    they were left in `DEFAULTS` and in the register anyway.

The guard is behavioural and there is no static version of it: a textual
reference count passes for every one of the four above. So the test perturbs each
lever to a value that MUST change the answer and asserts that the answer changes
— which is `ITERATING.md` rule 6, applied automatically instead of remembered.

A lever that is legitimately inert at a given target belongs in `EXPECTED_INERT`
with the reason, so that "does nothing" is a claim someone made on purpose rather
than a thing nobody noticed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, skip  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402

DRAWS = 40
DATA = ROOT / "data/raw/elections"

# A lever may be inert at a target for a REASON. Each entry is that reason, and
# each is a claim about the model that a reader can check — not a suppression.
EXPECTED_INERT: dict[tuple[str, str], str] = {
    ("w_bye", "2021"):
        "by-election data covers 2022-06 to 2026-02 only, so no past target has "
        "any. Inert in every backtest by construction; live in 2026. This is why "
        "JUDGEMENT-CALLS.md §A carries it at 🔴 as argued-not-tested.",
    ("w_bye_local_ward", "2021"): "built, disabled, and untestable for the same reason as w_bye",
    ("w_bye_local_pr", "2021"): "built, disabled, and untestable for the same reason as w_bye",
    ("poll_weight", "2021"):
        "gated on `poll_id` as well, at montecarlo.py:2217. Perturbing the "
        "weight alone cannot do anything because no poll is selected; the pair "
        "has to move together. Not dead — conditional.",
    ("poll_weight", "2026"): "same gate on poll_id",
    ("pa_contestation_uplift", "2021"):
        "an `elif` on measured contestation being empty. Contestation is "
        "non-empty at 2011/2016/2021 and empty at 2026, so this fires ONLY in "
        "the live forecast and in no backtest — which is a stronger disclosure "
        "than the register's 'saw the targets', not a weaker one.",
}

# An argument may be accepted and ignored for a REASON. Each entry is that
# reason. `_`-prefixing is the usual way to say so, but it does not work where
# the argument is dispatched BY KEYWORD through a uniform interface — renaming
# it there breaks every caller.
DELIBERATELY_UNUSED: dict[str, str] = {
    "benchmarks.py:last_lge(seed)":
        "dispatched as BENCHMARKS[name](ctx, draws=draws, seed=seed), so the "
        "name is load-bearing and cannot be prefixed. The baseline is "
        "deterministic by design — and THIS IS WHY its CRPS is identically its "
        "absolute seat error, which matters when reading 'the model beats it "
        "8/9 on CRPS': a point forecast is maximally penalised by CRPS.",
    "benchmarks.py:uniform_swing(seed)": "same uniform dispatch, same reason",
    "levels.py:sd_for(size)":
        "the POOLED fallback branch, taken when fewer than 6 observations "
        "support a size fit. The fitted branch two lines above does use size. "
        "Both must present the same signature to their caller.",
}

# Perturbations chosen to be large enough that no honest lever could absorb them.
PERTURB: dict[str, object] = {
    "entrant_prob": 0.95,
    "dirichlet_floor": 0.05,
    "ward_noise_sd": 0.60,
    "turnout_pattern_blend": 1.0,
    "turnout_blend_jitter": 0.90,
    "turnout_noise_sd": 0.50,
    "w_bye": 0.95,
    "w_bye_local_ward": 0.90,
    "w_bye_local_pr": 0.90,
    "polling_lean": 1.0,
    "polling_span": 40.0,
    "poll_weight": 1.0,
    "pa_contestation_uplift": 3.0,
    "spine_k": 40.0,
    "level_floor": 0.02,
    "turnout_correlation": -0.9,
}


def _run(target_year: str, overrides: list[str]):
    city = cityconfig.use("joburg")
    target = cityconfig.use_target(target_year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=list(overrides), draws=DRAWS, seed=20261104,
        city="joburg", target=target_year))
    run = M.run_model(target, scenario, DATA, verbose=False)
    # ALL THREE OUTPUTS, because a lever may touch only one of them and the
    # first version of this test compared the list ballot alone. It therefore
    # reported `ward_noise_sd` and `pa_contestation_uplift` as dead when both
    # are live: the first perturbs the ward TALLY (so it moves winners, not
    # shares) and the second the ward/PR ratio (so it moves the ward ballot
    # only — measured at 2026, PA ward share 5.64% -> 6.95%, mean seats
    # 15.11 -> 16.83, with the list share unchanged to the digit).
    return (run.pr_share_draws.copy(), run.ward_share_draws.copy(),
            dict(run.ward_win_sum), dict(run.index))


def _moves(base, other) -> float:
    """Largest change any lever produced on any output, in percentage points."""
    (bp, bw, bwin, bi), (op, ow, owin, oi) = base, other
    shared = set(bi) & set(oi)
    if not shared:
        return float("inf")
    share = max(
        max(abs(bp[:, bi[p]].mean() - op[:, oi[p]].mean()) for p in shared),
        max(abs(bw[:, bi[p]].mean() - ow[:, oi[p]].mean()) for p in shared))
    wins = max(abs(bwin.get(p, 0) - owin.get(p, 0))
               for p in set(bwin) | set(owin)) if (bwin or owin) else 0.0
    return max(100 * share, float(wins))


def _sweep_target(year: str) -> list[str]:
    base = _run(year, [])
    dead = []
    for key, value in sorted(PERTURB.items()):
        if key not in M.DEFAULTS:
            continue
        moved = _moves(base, _run(year, [f"{key}={value}"]))
        why = EXPECTED_INERT.get((key, year))
        if moved < 1e-9 and why is None:
            dead.append(f"{key} (perturbed to {value}, nothing moved)")
        elif moved >= 1e-9 and why is not None:
            dead.append(f"{key} IS live at {year} but EXPECTED_INERT claims it is "
                        f"not: {why!r} — the register is now wrong, delete the entry")
    return dead


def test_every_tunable_lever_actually_moves_the_forecast():
    """A lever that cannot change the answer is not a judgement call.

    `LEVEL_DF` was swept at 2.5 through 1000 and returned byte-identical output,
    while sitting at 🔴 in the register as one of the model's most-argued
    constants. `polling_lean` is computed, passed to `pool_spec`, and never read
    by it. Both were found by accident. This finds them on purpose.
    """
    dead = _sweep_target("2021") + _sweep_target("2026")
    assert not dead, (
        "these levers did not move the forecast when perturbed to a value that "
        "must change it:\n  " + "\n  ".join(dead) +
        "\nEither wire the lever up, delete it from DEFAULTS and from "
        "JUDGEMENT-CALLS.md, or add it to EXPECTED_INERT with the reason it is "
        "legitimately inert at that target. A constant nobody can move is not a "
        "choice the project made — see ITERATING.md rule 6.")


def test_no_function_argument_is_accepted_and_never_used():
    """An unused parameter is a lever the caller believes in and the callee ignores.

    `pool_spec(scenario, base_city_d, centres, index, lean, ipf_out)` never
    references `lean` OR `base_city_d`. The caller computes `lean` from
    `polling_lean * polling_span` and passes it in good faith. The independent
    review caught `lean`; `base_city_d` it missed, which is the argument for a
    test rather than a reading.
    """
    import ast

    offenders = []
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = [a.arg for a in node.args.args + node.args.kwonlyargs]
            used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
            used |= {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
            for a in args:
                if a in ("self", "cls") or a.startswith("_"):
                    continue
                key = f"{path.name}:{node.name}({a})"
                if a not in used and key not in DELIBERATELY_UNUSED:
                    offenders.append(f"{path.name}:{node.lineno} {node.name}({a})")
    assert not offenders, (
        "these functions accept an argument they never read, so every caller "
        "passing it is passing it into nothing:\n  " + "\n  ".join(offenders) +
        "\nDelete the parameter and its call sites, or use it. If it exists only "
        "to satisfy a uniform dispatch interface, add it to DELIBERATELY_UNUSED "
        "with the reason — an ignored argument should be a claim someone made, "
        "not a thing nobody noticed.")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok   {name}")
