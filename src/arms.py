"""Run the pre-registered arms of the 2026-10-11 model round, and compare them.

    .venv/bin/python src/arms.py run --arm U --out DIR            # every city-year
    .venv/bin/python src/arms.py run --arm I --out DIR --cities joburg --years 2021
    .venv/bin/python src/arms.py compare --out DIR --a I --b U    # after both ran

The pre-registration is ``prereg/2026-10-12-universal-draw.md`` (§3 the arms,
§3.2 the pairing, §4 the instruments, §6.3 R2) with its amendments. Step 7 of
``POOLS-REEMIT-QUEUE.md`` says when this runs: after the re-emit, the two
record emits and the post-emit checks, with no edit to the model in between.

THE ARMS (prereg §3). One seed per city-year, the same in every arm.

    I    the incumbent law (``draw_law = "incumbent"``)
    U    the universal draw, v4-L1 (the shipped defaults)
    UC   U with ``centre_correction`` on
    US   U with ``level_shrink = 0``, its own width-record variant
    C0   U run IN THE C0 WORKTREE (the final tree with the census commit
         ``c2edc60`` reverted, its own re-emit and records; amendment 2). This
         module refuses C0 in a tree that carries the census hold, and every
         other arm in a tree that does not.

WHAT A RUN WRITES, under ``DIR/<arm>/<city>-<year>/``, the format
``plausibility.load_run_dir`` reads: ``arrays.npz`` (``pr_share_draws``,
``pr_vote_draws``, ``ward_winner_draws`` as column indices, ``seat_draws``)
and ``meta.json`` (``seat_cols`` naming the columns, the arm, seed, draws,
overrides, the commit, the spec and width-record keys, the calibration
pass's convergence, the width-record variant, C0's ``final_commit``, the guard
board's universal-draw fields, the pool set and each party's ``pool_spec``
centre), plus ``trace/`` (``run_model``'s
``--run-dir`` stages). ``DIR`` must be outside ``data/``: nothing here writes
a forecast artefact, and ``run_model`` is called in process, never
``montecarlo.py`` as a script (CLAUDE.md §3).

WHAT IT REFUSES, per city-year, writing ``REFUSED.json`` with the reason and
no arrays: a universal arm whose width record is stale or missing
(``montecarlo.read_width_record``), and a universal arm whose calibration
pass did not converge (``41_guards.kappa_converged``). ``compare`` refuses to
read either, refuses a pair that is not the registered one
(``check_pairing``: seed, draws, tree, specs, width-record key and variant,
with C0's tree recognised explicitly), refuses an incomplete scored
population unless ``--allow-incomplete`` (recorded in the output), and
refuses when the classifying arm has not run.

THE SCORED POPULATION is ``plausibility.scored_population``: prereg §2's 16
city-years of 2016 and 2021, defined once for this module and the
plausibility scorer. 2011 and Johannesburg 2026 are run and reported,
labelled ``scored: false`` with the reason, and enter no interval.

EVERY ARM GETS A FRESH SCENARIO. ``run_model`` writes into the scenario it is
given (``_judgements_applied_sha``, ``_width``, the stage inputs), so a
scenario reused across arms would carry one arm's state into the next. Each
city-year of each arm loads its own from ``montecarlo.load_scenario``.

THE COMPARISONS (``compare``), two statistics named apart (prereg §3.2):

* ``cluster_interval``: the 90% cluster bootstrap over city-years
  (``score.cluster_bootstrap``) of the mean per party-city-year CRPS
  difference B − A (``score.crps_by_party``, points of list share), for
  large (centre ≥ 15%), middle (5-15%), small (< 5%) and all parties, the
  class taken from the ``classify_by`` arm's ``pool_spec`` centre (prereg §4:
  arm I's), over the scored population only; a party in the actuals that
  neither arm drew is excluded from every class and listed;
* ``mc_error``: per city-year, the Monte Carlo error of the list-MAE
  difference (``compare_history.vote_mae``) and of the mean CRPS difference,
  by ONE draw-index resample applied to both arms (``MC_RESAMPLES`` of them);
* ``r2``: per city-year, the median over parties of the per-draw correlation
  of the two arms' list shares (prereg §6.3), and whether the pool sets
  agree (U against C0 is read only where no pool is dropped).

It reports; the rules that score these numbers are the pre-registration's.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import cityconfig            # noqa: E402
import montecarlo as M       # noqa: E402

DATA = REPO / "data/raw/elections"

# THE ARMS: the scenario overrides each applies (prereg §3), as `--set` pairs.
ARMS: dict[str, dict] = {
    "I": {"draw_law": "incumbent"},
    "U": {},
    "UC": {"centre_correction": True},
    "US": {"level_shrink": 0.0},
    "C0": {},
}
UNIVERSAL_ARMS = frozenset({"U", "UC", "US", "C0"})
# The arm whose tree must NOT carry the census hold (amendment 2).
CENSUS_OFF_ARMS = frozenset({"C0"})

# The default population (prereg §2-§3): every metro at the 2011, 2016 and
# 2021 backtests, and Johannesburg's 2026 forecast; draws per prereg §3.
BACKTEST_YEARS = ("2011", "2016", "2021")
FORECASTS = (("joburg", "2026"),)
BACKTEST_DRAWS = 1000
FORECAST_DRAWS = 5000

# The size classes of the comparison, by `pool_spec` centre (prereg §4).
LARGE_MIN = 0.15
MIDDLE_MIN = 0.05
# The 90% interval of prereg §4.
CLUSTER_LEVEL = 0.90
# Draw-index resamples behind each Monte Carlo error. A numerical constant
# (JUDGEMENT-CALLS §A58): it sets the precision of the error, not its size.
MC_RESAMPLES = 200
MC_SEED = 20261012
# Prereg §6.3, R2's bar on the median per-draw correlation.
R2_MIN_MEDIAN = 0.98


class ArmRefused(Exception):
    """A city-year this arm may not produce, with the reason."""


# --------------------------------------------------------------------------
# the tree and the scenario
# --------------------------------------------------------------------------

def census_hold_in_tree() -> bool:
    """Does this tree carry the census hold (commit ``c2edc60``)? Read off
    ``pools``: the hold defines ``IDENTIFICATION_REACH`` and deletes
    ``REGISTRATION_MAX``."""
    import pools
    return hasattr(pools, "IDENTIFICATION_REACH") and not hasattr(
        pools, "REGISTRATION_MAX")


def check_tree(arm: str) -> None:
    """REFUSES an arm run in the wrong tree (amendment 2)."""
    if arm not in ARMS:
        raise SystemExit(f"unknown arm {arm!r}; the arms are {sorted(ARMS)}")
    held = census_hold_in_tree()
    if arm in CENSUS_OFF_ARMS and held:
        raise SystemExit(
            f"arm {arm} runs in the C0 worktree (the final tree with c2edc60 "
            f"reverted); this tree carries the census hold")
    if arm not in CENSUS_OFF_ARMS and not held:
        raise SystemExit(
            f"arm {arm} runs in the final tree; this one has no census hold "
            f"(is it the C0 worktree?)")


def check_out(out: Path) -> Path:
    """REFUSES an output root inside ``data/``: arms write no forecast
    artefact and nothing under the processed tree."""
    out = Path(out).resolve()
    data = (REPO / "data").resolve()
    if out == data or data in out.parents:
        raise SystemExit(f"--out {out} is inside {data}: an arm writes nothing "
                         f"under data/")
    return out


def overrides(arm: str) -> list[str]:
    """The arm's `--set` pairs, values as JSON (``parse_set`` reads JSON)."""
    return [f"{k}={json.dumps(v)}" for k, v in sorted(ARMS[arm].items())]


def fresh_scenario(arm: str, city: str, year: str, draws: int, seed: int):
    """``(target, scenario)``: the city and target made active, and a NEW
    scenario from ``montecarlo.load_scenario`` with the arm's overrides."""
    c = cityconfig.use(city)
    target = cityconfig.use_target(year)
    M.apply_city(c)
    sc = M.load_scenario(argparse.Namespace(
        config=None, set=overrides(arm), draws=int(draws), seed=int(seed),
        city=city, target=year))
    return target, sc


def population(cities=None, years=None) -> list[tuple[str, str]]:
    """The city-years an arm runs: every metro at every backtest year, and
    the forecasts, filtered by ``cities`` and ``years``."""
    import compare_history as CH
    out = [(c, y) for c in CH.CITIES for y in BACKTEST_YEARS] + list(FORECASTS)
    return [(c, y) for c, y in out
            if (not cities or c in cities) and (not years or y in years)]


def default_draws(year: str) -> int:
    return BACKTEST_DRAWS if M.target_is_held(year) else FORECAST_DRAWS


def _git(*args: str) -> str:
    try:
        return subprocess.run(("git", *args), capture_output=True, text=True,
                              check=True, cwd=REPO).stdout.strip()
    except Exception:                                    # noqa: BLE001
        return "<unavailable>"


# --------------------------------------------------------------------------
# one city-year of one arm
# --------------------------------------------------------------------------

def _width_check(year: str, scenario: dict) -> dict:
    """The width record this run will read, or ArmRefused: missing, stale or
    built for other centres (``montecarlo.read_width_record``)."""
    try:
        M.read_width_record(year, scenario)
    except SystemExit as exc:
        raise ArmRefused(f"width record: {exc}") from None
    return M.width_record_key()


def _pool_spec_centres(run_model, target, scenario) -> dict:
    """Each pooled party's ``pool_spec`` centre, from the model's own drawer
    inputs (no draw made), as ``width_record.case_for`` builds them."""
    with contextlib.redirect_stdout(io.StringIO()):
        inp = run_model(target, scenario, DATA, verbose=False,
                        stop_after="drawer_inputs")
        spec = M.pool_spec(inp.scenario, inp.centres, inp.index)
    return {p: float(v) for p, v in M.pool_spec_centres(spec).items()}


def run_city_year(arm: str, city: str, year: str, out: Path, *,
                  draws: int | None = None, seed: int | None = None,
                  run_model=None, width_check=None) -> dict:
    """Run one city-year of one arm into ``out/<arm>/<city>-<year>/``.

    ``run_model`` and ``width_check`` default to ``montecarlo.run_model`` and
    the width-record check; a test passes constructed ones. Returns the
    meta written, or raises :class:`ArmRefused` after writing
    ``REFUSED.json`` (and no arrays)."""
    run_model = run_model or M.run_model
    width_check = width_check or _width_check
    draws = int(draws or default_draws(year))
    seed = int(seed if seed is not None else M.DEFAULTS["seed"])
    dest = check_out(out) / arm / f"{city}-{year}"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    try:
        target, scenario = fresh_scenario(arm, city, year, draws, seed)
        width_key = (width_check(year, scenario) if arm in UNIVERSAL_ARMS
                     else None)
        _t, sc_inputs = fresh_scenario(arm, city, year, draws, seed)
        centres = _pool_spec_centres(run_model, target, sc_inputs)
        run = run_model(target, scenario, DATA, verbose=False,
                        run_dir=dest / "trace")
        guards = dict(getattr(run, "guards", {}) or {})
        if arm in UNIVERSAL_ARMS and guards.get("kappa_converged") is not True:
            raise ArmRefused(
                f"the calibration pass did not converge (kappa_converged "
                f"{guards.get('kappa_converged')!r} after "
                f"{guards.get('kappa_iters')!r} iterations): the run does not "
                f"conserve its centres")
    except ArmRefused as why:
        for p in dest.iterdir():
            shutil.rmtree(p) if p.is_dir() else p.unlink()
        (dest / "REFUSED.json").write_text(json.dumps(
            {"arm": arm, "city": city, "year": year, "reason": str(why)},
            indent=1))
        raise
    universe = list(run.universe)
    seats = np.array([[s.get(p, 0) for p in universe] for s in run.seat_draws],
                     dtype=np.int64)
    np.savez_compressed(
        dest / "arrays.npz",
        pr_share_draws=np.asarray(run.pr_share_draws, dtype=float),
        pr_vote_draws=np.asarray(run.pr_vote_draws),
        ward_winner_draws=np.asarray(run.ward_winner_draws, dtype=np.int64),
        seat_draws=seats)
    import freeze
    meta = {
        "arm": arm, "city": city, "year": year, "draws": draws, "seed": seed,
        "overrides": overrides(arm), "seat_cols": universe,
        "git": {"commit": _git("rev-parse", "HEAD"),
                "dirty": bool(_git("status", "--porcelain", "--", "src"))},
        "census_hold": census_hold_in_tree(),
        "spec_keys": freeze.pool_artefact_keys(target.city),
        "width_record_key": width_key,
        "width_record_current": (True if arm in UNIVERSAL_ARMS else None),
        "width_record_variant": (M.width_record_variant(scenario)
                                 if arm in UNIVERSAL_ARMS else None),
        "final_commit": (_git("rev-parse", "HEAD^") if arm in CENSUS_OFF_ARMS
                         else None),
        "draw_law": guards.get("draw_law"),
        "kappa_converged": guards.get("kappa_converged"),
        "kappa_iters": guards.get("kappa_iters"),
        "guards": {k: guards.get(k) for k in
                   ("kappa_error", "mean_error", "gamma_fallbacks",
                    "gamma_draws", "draws")},
        "pools": list(getattr(run, "pool_turnout_names", []) or []),
        "pool_spec_centres": centres,
        "judgements_applied_sha": scenario.get("_judgements_applied_sha"),
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True,
                                               default=str))
    return meta


def run_arm(arm: str, out: Path, cities=None, years=None, draws=None,
            seed=None, run_model=None, width_check=None) -> dict:
    """Every city-year of ``population`` for one arm. Returns
    ``{"ran": [...], "refused": {city-year: reason}}``."""
    check_tree(arm)
    check_out(out)
    ran, refused = [], {}
    for city, year in population(cities, years):
        try:
            run_city_year(arm, city, year, out, draws=draws, seed=seed,
                          run_model=run_model, width_check=width_check)
            ran.append(f"{city}-{year}")
        except ArmRefused as why:
            refused[f"{city}-{year}"] = str(why)
    return {"ran": ran, "refused": refused}


# --------------------------------------------------------------------------
# reading arms back, and comparing two
# --------------------------------------------------------------------------

def load_arm(out: Path, arm: str) -> dict:
    """``{(city, year): (meta, arrays)}`` for every city-year the arm wrote.
    REFUSES a universal-arm city-year whose meta says the calibration did not
    converge or the width record was not current; a refused city-year (no
    arrays) is not loaded."""
    root = Path(out) / arm
    got = {}
    for d in sorted(p for p in root.iterdir() if (p / "meta.json").exists()):
        meta = json.loads((d / "meta.json").read_text())
        if arm in UNIVERSAL_ARMS and (meta.get("kappa_converged") is not True
                                      or meta.get("width_record_current")
                                      is not True):
            raise SystemExit(f"{d}: kappa_converged "
                             f"{meta.get('kappa_converged')!r}, width record "
                             f"current {meta.get('width_record_current')!r}; "
                             f"refused")
        a = np.load(d / "arrays.npz")
        got[(meta["city"], meta["year"])] = (
            meta, {k: a[k] for k in a.files})
    return got


def _shares(arrays: dict, cols: list, parties: list) -> np.ndarray:
    """Draws × ``parties`` list shares; a party with no column is 0."""
    S = np.asarray(arrays["pr_share_draws"], dtype=float)
    idx = {p: j for j, p in enumerate(cols)}
    out = np.zeros((S.shape[0], len(parties)))
    for k, p in enumerate(parties):
        if p in idx:
            out[:, k] = S[:, idx[p]]
    return out


def size_class(centre: float) -> str:
    return ("large" if centre >= LARGE_MIN
            else "middle" if centre >= MIDDLE_MIN else "small")


def _crps(S: np.ndarray, actual: np.ndarray, parties: list) -> np.ndarray:
    import score
    per = score.crps_by_party(S, actual, parties)["per_party"]
    return 100.0 * np.array([per[p] for p in parties])


def _mae(S: np.ndarray, parties: list, actual: dict) -> float:
    import compare_history as CH
    run = SimpleNamespace(pr_share_draws=S,
                          index={p: k for k, p in enumerate(parties)})
    return CH.vote_mae(run, actual)


def _variant_level_shrink(meta: dict) -> float | None:
    v = meta.get("width_record_variant")
    return None if v is None else float(json.loads(v)["level_shrink"])


def check_pairing(a: str, ma: dict, b: str, mb: dict) -> None:
    """REFUSES (SystemExit) two city-year metas that are not the pair the
    prereg registers (§3, §3.2; amendment 2).

    * the same draws and seed (§3);
    * the same tree: one commit, neither dirty in ``src``, the same pool
      specs (``spec_keys``) and the same width-record key, EXCEPT when
      exactly one arm is C0, whose tree is the final tree with the census
      hold reverted (amendment 2): its meta's ``final_commit`` must be the
      other arm's commit, its ``census_hold`` false and the other's true; its
      specs and record are its own and are not compared;
    * the width-record variant each arm registers: US the ``level_shrink =
      0`` variant (amendment 2 item 2), every other universal arm a variant
      with the shrink on; two arms neither of which is US read one variant.
      Arm I reads no record and records none.
    """
    where = f"{ma.get('city')}-{ma.get('year')}"
    if ma["draws"] != mb["draws"] or ma["seed"] != mb["seed"]:
        raise SystemExit(f"{where}: arms {a} and {b} ran different draws or "
                         f"seeds ({ma['draws']}/{ma['seed']} against "
                         f"{mb['draws']}/{mb['seed']}): not paired")
    for arm, m in ((a, ma), (b, mb)):
        if (m.get("git") or {}).get("dirty") is not False:
            raise SystemExit(f"{where}: arm {arm} ran on a tree dirty in src/ "
                             f"(or recorded none): its commit does not "
                             f"identify the code")
        if arm in UNIVERSAL_ARMS:
            ls = _variant_level_shrink(m)
            if ls is None:
                raise SystemExit(f"{where}: arm {arm} recorded no width-record "
                                 f"variant")
            if (arm == "US") != (ls == 0.0):
                raise SystemExit(f"{where}: arm {arm} read the width-record "
                                 f"variant {m['width_record_variant']}; the "
                                 f"prereg registers level_shrink = 0 for US "
                                 f"only (amendment 2 item 2)")
    if "US" not in (a, b) and a in UNIVERSAL_ARMS and b in UNIVERSAL_ARMS \
            and ma["width_record_variant"] != mb["width_record_variant"]:
        raise SystemExit(f"{where}: arms {a} and {b} read different "
                         f"width-record variants")
    if (a in CENSUS_OFF_ARMS) != (b in CENSUS_OFF_ARMS):
        c0, other = ((a, ma), (b, mb)) if a in CENSUS_OFF_ARMS else ((b, mb),
                                                                    (a, ma))
        if c0[1].get("final_commit") != other[1]["git"]["commit"]:
            raise SystemExit(
                f"{where}: arm {c0[0]} names the final tree "
                f"{c0[1].get('final_commit')!r}, but arm {other[0]} ran at "
                f"{other[1]['git']['commit']!r}: C0 is the final tree with "
                f"c2edc60's pools.py hunks reverted (amendment 2, 3)")
        if c0[1].get("census_hold") is not False or \
                other[1].get("census_hold") is not True:
            raise SystemExit(f"{where}: C0 must run without the census hold "
                             f"and {other[0]} with it")
        return
    if ma["git"]["commit"] != mb["git"]["commit"]:
        raise SystemExit(f"{where}: arms {a} and {b} ran at different commits "
                         f"({ma['git']['commit']} against "
                         f"{mb['git']['commit']}): the prereg pairs them on "
                         f"one tree")
    if ma.get("census_hold") != mb.get("census_hold"):
        raise SystemExit(f"{where}: arms {a} and {b} differ in the census hold")
    if ma.get("spec_keys") != mb.get("spec_keys"):
        raise SystemExit(f"{where}: arms {a} and {b} read different pool specs "
                         f"(spec_keys differ): not one emit")
    if a in UNIVERSAL_ARMS and b in UNIVERSAL_ARMS and \
            ma.get("width_record_key") != mb.get("width_record_key"):
        raise SystemExit(f"{where}: arms {a} and {b} read width records under "
                         f"different keys")


def compare(out: Path, a: str, b: str, actuals: dict,
            classify_by: str = "I", resamples: int | None = None,
            population=None, allow_incomplete: bool = False) -> dict:
    """Arm ``b`` against arm ``a`` (differences are b − a), paired.

    THE SCORED POPULATION is ``plausibility.scored_population`` (prereg §2:
    the 16 city-years of 2016 and 2021), unless ``population`` is given (a
    constructed test). Every city-year both arms ran gets its R2 row; a
    city-year outside the population that has a result (2011) also gets its
    scores, labelled ``scored: false`` with the reason, and enters no
    interval. REFUSES:

    * a pair that is not the registered one (:func:`check_pairing`);
    * a population member missing from either arm, unless
      ``allow_incomplete`` (the output's ``population`` block records it,
      and lists every city-year present in one arm and not the other);
    * a scored city-year with no actual result;
    * a classifying arm (prereg §4: arm I) that has not run, or lacks a
      scored city-year. There is no fallback to another arm's centres.

    ``actuals`` maps ``(city, year)`` to the realised citywide list shares
    (``compare_history.actual_shares``). A party in the actuals that NEITHER
    arm drew enters no size class and not ``all``: both arms put no mass on
    it, so its difference is identically zero and would dilute every mean.
    It is listed per city-year (``undrawn_actual``) with its share. A drawn
    party with no ``pool_spec`` centre in the classifying arm enters ``all``
    and no size class, and is listed (``unclassed``). List MAE is
    ``compare_history.vote_mae``'s definition (every actual party, an
    undrawn one at 0)."""
    import plausibility as P
    import score
    resamples = int(resamples or MC_RESAMPLES)
    population = list(P.scored_population() if population is None
                      else population)
    pop_set = set(population)
    A, B = load_arm(out, a), load_arm(out, b)
    if classify_by == a:
        C = A
    elif classify_by == b:
        C = B
    else:
        if not (Path(out) / classify_by).is_dir():
            raise SystemExit(f"the size classes are arm {classify_by}'s "
                             f"pool_spec centres (prereg §4), and arm "
                             f"{classify_by} has not run under {out}")
        C = load_arm(out, classify_by)
    pop_a = P.check_population(A, population, allow_incomplete)
    pop_b = P.check_population(B, population, allow_incomplete)
    rng = np.random.default_rng(MC_SEED)
    per, groups = {}, {k: [] for k in ("large", "middle", "small", "all")}
    scored_keys = []
    for key in sorted(set(A) & set(B)):
        (ma, xa), (mb, xb) = A[key], B[key]
        check_pairing(a, ma, b, mb)
        parties = sorted(set(ma["seat_cols"]) | set(mb["seat_cols"]))
        Sa = _shares(xa, ma["seat_cols"], parties)
        Sb = _shares(xb, mb["seat_cols"], parties)
        both = [k for k, p in enumerate(parties)
                if p in ma["seat_cols"] and p in mb["seat_cols"]
                and Sa[:, k].std() > 0 and Sb[:, k].std() > 0]
        cors = [float(np.corrcoef(Sa[:, k], Sb[:, k])[0, 1]) for k in both]
        row = {"r2": {"median": float(np.median(cors)) if cors else None,
                      "parties": len(cors),
                      "passes": bool(cors) and float(np.median(cors))
                      >= R2_MIN_MEDIAN,
                      "pools_equal": ma.get("pools") == mb.get("pools")},
               "scored": key in pop_set}
        if key not in pop_set:
            row["not_scored_because"] = P.unscored_reason(key[1])
        actual = actuals.get(key)
        if actual is None and key in pop_set:
            raise SystemExit(f"{key[0]}-{key[1]} is in the scored population "
                             f"and has no actual result")
        if actual is not None:
            if key in pop_set and key not in C:
                raise SystemExit(f"arm {classify_by} has no run at "
                                 f"{key[0]}-{key[1]}: its size classes "
                                 f"cannot be read (prereg §4)")
            undrawn = {p: float(v) for p, v in actual.items()
                       if p not in parties}
            act = np.array([actual.get(p, 0.0) for p in parties])
            d = _crps(Sb, act, parties) - _crps(Sa, act, parties)
            cen = ((C.get(key) or ({}, None))[0].get("pool_spec_centres")
                   or {})
            unclassed = [p for p in parties if p not in cen]
            cls = [size_class(cen[p]) if p in cen else None for p in parties]
            if key in pop_set:
                scored_keys.append(key)
                for name in ("large", "middle", "small"):
                    sel = np.array([c == name for c in cls])
                    if sel.any():
                        groups[name].append(d[sel])
                groups["all"].append(d)
            D = Sa.shape[0]
            mae_d, crps_d = [], []
            for _ in range(resamples):
                idx = rng.integers(0, D, D)
                mae_d.append(_mae(Sb[idx], parties, actual)
                             - _mae(Sa[idx], parties, actual))
                crps_d.append(float((_crps(Sb[idx], act, parties)
                                     - _crps(Sa[idx], act, parties)).mean()))
            row["score"] = {
                "list_mae_difference": _mae(Sb, parties, actual)
                - _mae(Sa, parties, actual),
                "crps_mean_difference": float(d.mean()),
                "mc_error": {"list_mae": float(np.std(mae_d, ddof=1)),
                             "crps_mean": float(np.std(crps_d, ddof=1)),
                             "resamples": resamples},
                "undrawn_actual": undrawn,
                "unclassed": unclassed}
        per[f"{key[0]}-{key[1]}"] = row
    intervals = {}
    for name, g in groups.items():
        if not g:
            intervals[name] = None
            continue
        ci = score.cluster_bootstrap(g, level=CLUSTER_LEVEL)
        intervals[name] = {k: v for k, v in ci.items() if k != "replicates"}
    population_block = {
        "registered": "prereg §2: the 16 city-years of 2016 and 2021",
        "expected": len(population),
        "scored": sorted(f"{c}-{y}" for c, y in scored_keys),
        "missing_in_" + a: pop_a["missing"],
        "missing_in_" + b: pop_b["missing"],
        "only_in_" + a: sorted(f"{c}-{y}" for c, y in set(A) - set(B)),
        "only_in_" + b: sorted(f"{c}-{y}" for c, y in set(B) - set(A)),
        "complete": pop_a["complete"] and pop_b["complete"],
        "allow_incomplete": bool(allow_incomplete)}
    if len(scored_keys) != len(population) and not allow_incomplete:
        raise SystemExit(f"scored {len(scored_keys)} city-years against the "
                         f"{len(population)} registered")
    return {"a": a, "b": b, "difference": f"{b} - {a}",
            "classified_by": classify_by, "per_city_year": per,
            "population": population_block,
            "cluster_interval": intervals,
            "units": "CRPS and list MAE in points of list share"}


def actual_shares(keys) -> dict:
    """The realised list shares of every held city-year in ``keys``."""
    import compare_history as CH
    out = {}
    for city, year in keys:
        if not M.target_is_held(year):
            continue
        cityconfig.use(city)
        target = cityconfig.use_target(year)
        out[(city, year)] = CH.actual_shares(target, DATA)[0]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--arm", required=True, choices=sorted(ARMS))
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--cities", nargs="+")
    r.add_argument("--years", nargs="+")
    r.add_argument("--draws", type=int)
    r.add_argument("--seed", type=int)
    c = sub.add_parser("compare")
    c.add_argument("--out", type=Path, required=True)
    c.add_argument("--a", required=True, choices=sorted(ARMS))
    c.add_argument("--b", required=True, choices=sorted(ARMS))
    c.add_argument("--classify-by", default="I", choices=sorted(ARMS))
    c.add_argument("--allow-incomplete", action="store_true",
                   help="compare with some of prereg §2's city-years missing "
                        "(the output records the flag)")
    args = ap.parse_args(argv)
    M.fix_hash_seed()
    if args.cmd == "run":
        res = run_arm(args.arm, args.out, args.cities, args.years,
                      args.draws, args.seed)
        print(f"ran {len(res['ran'])}; refused {len(res['refused'])}")
        for k, v in res["refused"].items():
            print(f"  REFUSED {k}: {v}")
        return 1 if res["refused"] else 0
    keys = {k for arm in (args.a, args.b) for k in load_arm(args.out, arm)}
    res = compare(args.out, args.a, args.b, actual_shares(keys),
                  args.classify_by, allow_incomplete=args.allow_incomplete)
    path = check_out(args.out) / f"compare_{args.a}_{args.b}.json"
    path.write_text(json.dumps(res, indent=1, sort_keys=True, default=str))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
