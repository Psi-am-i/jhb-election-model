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
  * `polling_lean` / `polling_span` — `lean` was computed and passed to
    `pool_spec`, whose body never referenced the parameter. Inert at any value,
    not merely defaulted to zero. DELETED 2026-08-17, which is why they are no
    longer in `PERTURB`; their removal is what
    `test_every_defaults_key_is_swept_or_excused` was written to catch, because
    the first deletion took their test coverage with it and nothing failed.
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
import json
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

# Perturbable through `--set` only because `load_scenario` copies them into the
# scenario; they are module constants, not DEFAULTS keys, and the sweep reaches
# them by scenario key of the same lowercase name where one exists.
_MODULE_LEVEL = {"turnout_correlation"}

# Reasons shared by several EXPECTED_INERT entries. Each is a claim about the
# model that a reader can check, not a suppression.
_LEGACY_POLL = (
    "RETRACTED 2026-08-17 and kept only as a warning. This entry used to say "
    "'verified directly: poll_k 1.0 vs 40.0 at 2026 moves the DA, ANC, ASA, MK "
    "and EFF by exactly 0.0000pp'. That null was measured WITH THE GATE SHUT — "
    "`poll_id` is None by default, so the branch never ran. It is ITERATING.md "
    "rule 6's exact fault, committed inside the commit that automated rule 6. "
    "Open the gate and poll_k 1.0 -> 1000 moves the DA 33.26 -> 36.67pp and "
    "89.8 -> 99.2 seats, live at 2016, 2021 AND 2026. The lever is not inert; "
    "it is CONDITIONAL, and a conditional lever has to be perturbed together "
    "with its condition — which `_PAIRED` below now does.")

# Levers that do nothing alone and something together. A conditional lever
# perturbed without its gate reads as dead, which is how the poll path was
# wrongly certified inert. Each entry names the keys that must move as a set.
PAIRED: dict[str, dict[str, object]] = {
    "the legacy poll path": {"poll_id": "ipsos-2021-lge-national",
                             "poll_weight": 0.9, "poll_k": 40.0},
}
_WARD_LOCAL_BYE = (
    "parameters of the §1.28 ward-local by-election term, which is gated on "
    "`w_bye_local_ward` / `w_bye_local_pr`, both 0.0 by design so the published "
    "forecast is untouched until it is deliberately switched on. Inert with "
    "their gate shut, and untestable in any backtest even open, because the "
    "by-election window is 2022-06 to 2026-02.")
_ENTRANT_GEOGRAPHY = (
    "empty by default and listed in MACHINERY.md's 'switched off' summary. "
    "`montecarlo.py:1871` reads it as `scenario.get(...) or {}` and the branch "
    "needs a declared `parent`; the perturbation used here supplies none, so "
    "this entry records that the EMPTY default is inert, not that the mechanism "
    "is dead.")

# A lever may be inert at a target for a REASON. Each entry is that reason, and
# each is a claim about the model that a reader can check — not a suppression.
# theta_mode, individual_theta and f_other were excused here from 2026-08-17
# until 2026-08-19, when they were DELETED. Three keys carrying twelve
# party-specific numbers between them, certified dead at every runnable target
# and then kept anyway for two days because their disposition was recorded as
# "an open decision". The decision had already been made -- twice -- by the
# project owner. MODEL-LOG §1.52.
EXPECTED_INERT: dict[tuple[str, str], str] = {
    ("w_bye", "2021"):
        "by-election data covers 2022-06 to 2026-02 only, so no past target has "
        "any. Inert in every backtest by construction; live in 2026. This is why "
        "JUDGEMENT-CALLS.md §A carries it at 🔴 as argued-not-tested.",
    ("w_bye_local_ward", "2021"): "built, disabled, and untestable for the same reason as w_bye",
    ("w_bye_local_pr", "2021"): "built, disabled, and untestable for the same reason as w_bye",
    ("poll_weight", "2026"): "same gate on poll_id",
    ("poll_weight", "2021"):
        "gated on `poll_id` as well, at montecarlo.py:2217. Perturbing the "
        "weight alone cannot do anything because no poll is selected; the pair "
        "has to move together. Not dead — conditional.",
    # --- added 2026-08-17, when the enumeration test raised PERTURB from 13 of
    # --- 27 DEFAULTS keys to 23 and seven more levers turned out not to move.
    # Each is inert for a DIFFERENT reason and every reason is checkable.
    ("poll_k", "2021"): _LEGACY_POLL,
    ("poll_k", "2026"): _LEGACY_POLL,
    ("bye_local_cap", "2021"): _WARD_LOCAL_BYE,
    ("bye_local_cap", "2026"): _WARD_LOCAL_BYE,
    ("bye_tau_months", "2021"): _WARD_LOCAL_BYE,
    ("bye_tau_months", "2026"): _WARD_LOCAL_BYE,
    ("entrant_geography", "2021"): _ENTRANT_GEOGRAPHY,
    ("entrant_geography", "2026"): _ENTRANT_GEOGRAPHY,
    # ("overhang_rule", "2021") was excused here from 2026-08-17 to 2026-08-18.
    # THE ENTRY RETIRED ITSELF, exactly as it said it would. It recorded that
    # its own excuse was weak -- the overhang clause fired in 1 draw of 200 at
    # that target, so the lever was inert only because a rare clause missed
    # under this seed and draw count -- and it predicted that any change to the
    # draws would make it live and fail the entry as a stale register claim.
    # The contestation correction (MODEL-LOG §1.47) changed the ward wins, the
    # clause now fires, and the `elif` in `_sweep_target` duly reported it.
    # Deleted rather than re-argued: the lever is live at both targets.
    # `pa_contestation_uplift` was excused here until 2026-08-18, on the
    # grounds that it fired only where no backtest could reach it. That was a
    # true statement and the wrong conclusion: a lever live ONLY in the live
    # forecast is not a lever to excuse, it is one to delete. It is gone, and
    # the branch it held now falls back to the previous local election's
    # measured contestation for EVERY party. MODEL-LOG §1.47.
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
    "width_budget.py:_no_pool_turnout(rng)":
        "an ABLATION STUB. `src/width_budget.py` measures what each variance source contributes by replacing it with a version that has none, and a replacement must present the signature of the thing it replaces or `montecarlo` cannot call it. Ignoring this argument IS the measurement. MODEL-LOG §1.48.",
    "width_budget.py:_no_pool_turnout(z_common)":
        "an ABLATION STUB. `src/width_budget.py` measures what each variance source contributes by replacing it with a version that has none, and a replacement must present the signature of the thing it replaces or `montecarlo` cannot call it. Ignoring this argument IS the measurement. MODEL-LOG §1.48.",
    "width_budget.py:_no_pool_turnout(rho)":
        "an ABLATION STUB. `src/width_budget.py` measures what each variance source contributes by replacing it with a version that has none, and a replacement must present the signature of the thing it replaces or `montecarlo` cannot call it. Ignoring this argument IS the measurement. MODEL-LOG §1.48.",
    "width_budget.py:_no_shock(rng)":
        "the same, for the theta level shock, which returns 1.0. NOTE that it therefore consumes no randomness -- which is exactly why the harness averages five seeds: an ablation that skips a draw shifts every later draw, and the first run of it reported negative variance contributions because of that.",
    "width_budget.py:_no_shock(df)":
        "the same, for the theta level shock, which returns 1.0. NOTE that it therefore consumes no randomness -- which is exactly why the harness averages five seeds: an ablation that skips a draw shifts every later draw, and the first run of it reported negative variance contributions because of that.",
    "levels.py:sd_for(size)":
        "the POOLED fallback branch, taken when fewer than 6 observations "
        "support a size fit. The fitted branch two lines above does use size. "
        "Both must present the same signature to their caller.",
}

# Keys that are NOT model judgements: how many draws, which seed, where the
# inputs came from. Perturbing them is meaningless, so they are excused by name
# rather than by omission — see `test_every_defaults_key_is_swept_or_excused`.
OPERATIONAL: dict[str, str] = {
    "draws": "how many samples to take; not a claim about the world",
    "seed": "reproducibility, not a model parameter",
    "pools": "the emitted pool spec itself, loaded from pools_<year>.json",
    "poll_id": "selects WHICH poll; `poll_weight` is the lever and is swept",
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
    "poll_weight": 1.0,
    "spine_k": 40.0,
    "level_floor": 0.02,
    "turnout_correlation": -0.9,
    # The level shrink, added 2026-08-17 and ADOPTED at 0.35 the next day.
    # PERTURBED TO 0.0, WHICH IS THE POINT: 0.0 is exactly the identity in
    # `compress_levels`, so this sweep asks whether the committed shrink is
    # doing anything at all, and a null here would mean the largest scored
    # improvement this model has had is not reaching the forecast. Perturbing
    # it to 0.35 -- as this entry did for a few minutes -- perturbs it to its
    # own default and is guaranteed to report a lever that cannot move.
    "level_shrink": 0.0,
    "level_shrink_scale": 0.40,
    # Added 2026-08-17 after the enumeration test below found that PERTURB
    # covered 13 of 27 DEFAULTS keys and nobody had noticed.
    "entrant_share": [0.20, 0.30, 0.45],
    "poll_k": 40.0,
    "bye_local_cap": 40.0,
    "bye_tau_months": 400.0,
    "entrant_geography": {"parent": "ANC", "k": 1.0},
    "overhang_rule": "expand",
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
    seats: dict[str, float] = {}
    for d in run.seat_draws:
        for party, n in d.items():
            seats[party] = seats.get(party, 0.0) + n
    return (run.pr_share_draws.copy(), run.ward_share_draws.copy(),
            dict(run.ward_win_sum), seats, dict(run.index))


def _moves(base, other) -> float:
    """Largest change any lever produced on any output, in percentage points."""
    (bp, bw, bwin, bs, bi), (op, ow, owin, os, oi) = base, other
    shared = set(bi) & set(oi)
    if not shared:
        return float("inf")
    share = max(
        max(abs(bp[:, bi[p]].mean() - op[:, oi[p]].mean()) for p in shared),
        max(abs(bw[:, bi[p]].mean() - ow[:, oi[p]].mean()) for p in shared))
    wins = max(abs(bwin.get(p, 0) - owin.get(p, 0))
               for p in set(bwin) | set(owin)) if (bwin or owin) else 0.0
    # SEATS TOO. `overhang_rule` touches nothing else -- it decides the
    # excessive-seats treatment at allocation, after every vote is drawn -- and
    # the first three versions of this test could not see it. Three
    # false-negative channels in one test written to catch false negatives:
    # list-only, then no ward wins, then no seats.
    seats = max(abs(bs.get(p, 0.0) - os.get(p, 0.0))
                for p in set(bs) | set(os)) if (bs or os) else 0.0
    return max(100 * share, float(wins), float(seats))


def _sweep_paired(year: str, base) -> list[str]:
    """Perturb a conditional lever TOGETHER WITH ITS GATE.

    A lever behind a gate reads as dead when the gate is shut, and that is not a
    fact about the lever. `poll_k` was certified inert on exactly that mistake —
    measured with `poll_id=None`, so the branch never ran — and the null was
    written into this file and into MODEL-LOG. Opened, the same lever moves the
    DA by 3.4pp and nine seats.
    """
    dead = []
    for label, keys in sorted(PAIRED.items()):
        if not all(k in M.DEFAULTS for k in keys):
            dead.append(f"{label}: {sorted(set(keys) - set(M.DEFAULTS))} not in DEFAULTS")
            continue
        overrides = [f"{k}={json.dumps(v)}" for k, v in keys.items()]
        if _moves(base, _run(year, overrides)) < 1e-9:
            dead.append(f"{label} at {year} (perturbed {sorted(keys)} together, "
                        f"nothing moved)")
    return dead


def _sweep_target(year: str) -> list[str]:
    base = _run(year, [])
    dead = _sweep_paired(year, base)
    for key, value in sorted(PERTURB.items()):
        if key not in M.DEFAULTS:
            continue
        # json.dumps, not an f-string: `--set` parses its value as JSON, and
        # Python's repr of a dict uses single quotes, which json.loads rejects.
        # It then falls back to storing the raw STRING, and the model gets a
        # str where it expects a mapping — which is an AttributeError deep in
        # run_model rather than a clear failure here.
        moved = _moves(base, _run(year, [f"{key}={json.dumps(value)}"]))
        why = EXPECTED_INERT.get((key, year))
        if moved < 1e-9 and why is None:
            # Name the year. Without it a key that is inert at one target and
            # live at the other reports identically to one that is dead
            # everywhere, and the reader cannot tell which -- that cost a
            # diagnosis when `overhang_rule` went inert at 2021 alone.
            dead.append(f"{key} at {year} (perturbed to {value}, nothing moved)")
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


def test_every_defaults_key_is_swept_or_excused():
    """A lever deleted from DEFAULTS must not silently delete its own coverage.

    `PERTURB` was a hand-maintained allowlist, and hand-maintained allowlists
    rot. An independent reviewer found it covered **13 of 27** DEFAULTS keys —
    omitting `ward_pr_ratio_overrides`, which this file's own docstring names as
    one of the four instances that motivated it. Worse, three PERTURB entries
    were being *silently skipped* by the `key not in M.DEFAULTS` guard:
    `polling_lean` and `polling_span`, which had just been deleted (so a
    deletion removed test coverage with no failure at all), and
    `turnout_correlation`, which is the module constant `TURNOUT_CORRELATION`
    and had therefore never been exercised despite appearing in the list.

    `test_every_tunable_constant_is_in_the_judgement_register` gets this right by
    ENUMERATING rather than listing. This does the same, in both directions.
    """
    keys = set(M.DEFAULTS)
    missing = sorted(keys - set(PERTURB) - set(OPERATIONAL))
    assert not missing, (
        "these DEFAULTS keys are never perturbed, so nothing would notice if "
        f"they stopped doing anything:\n  {missing}\n"
        "Give each a perturbation in PERTURB, or name it in OPERATIONAL with "
        "the reason it is not a model judgement.")

    stale = sorted(set(PERTURB) - keys - set(_MODULE_LEVEL))
    assert not stale, (
        "these PERTURB entries are not DEFAULTS keys, so the sweep SILENTLY "
        f"SKIPS them and reports success:\n  {stale}\n"
        "Either they were deleted — in which case remove them here and say so "
        "in MODEL-LOG — or they are module constants, which need naming in "
        "_MODULE_LEVEL and reaching a different way.")


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
