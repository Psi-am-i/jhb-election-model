"""F9: score the freeze batch against its two pre-registrations.

    .venv/bin/python audits/2026-09-29-f9-scoring/score_f9.py \\
        --before-specs <dir> --after-specs <dir> \\
        --before-history <history.json> --after-history <history.json> \\
        [--noise <history.json> ...] [--json out.json]
    .venv/bin/python audits/2026-09-29-f9-scoring/score_f9.py --self-test

WHAT IS BEING SCORED. `prereg/2026-09-25-pool-input-repairs.md` (P1-P7 and
"What would say the window failed") and
`prereg/2026-09-27-independents-and-mergers.md`. Of the four pool repairs
only C1 shipped (F3, MODEL-LOG §1.269); C2 is F4, after the election; C3's
composition side and C4 were deferred by F2 (§1.268). Of the merger prereg
only Change 2 shipped (F5), and its amended predictions 1-5 were scored in
§1.275 on `run_model` directly. Independents (Change 1) did not ship. So:

  * a prediction whose repair was not made, or whose stated premise did not
    happen, is NOT TESTED, never passed; the instrument it names is printed
    as context;
  * everything else is scored as written; where the text needs an
    operational reading, the reading is stated in `READING` beside it.

Revised 2026-09-29 on the R2 review (`R2-findings.md` beside this file),
before either `compare_history` run.

THE PAIR. "before" is `69cc6cc` (the commit before F3) with its specs
re-emitted TODAY in a worktree, so both sides share one environment (MODEL-LOG
§1.279: unchanged code no longer reproduces the 23/27 September floats).
"after" is the freeze tree on the F8 specs. Same seed, draws and hash seed,
enforced from both manifests, and each history is bound to its spec directory
through `pool_artefact_keys`.

  ⛔ THE PLACEBO IS THE TRIPWIRE. A spec that differs only in `artefact_key`
  (or by float round-off) must give an identical row, whole, less provenance.
  If any does not, the paired difference measures more than F3, and every
  paired verdict is VOID.

NOISE. `--noise` takes `compare_history` runs of the BEFORE tree at other
seeds. They never change a verdict. Each paired statistic is printed beside
the spread of the same statistic between the before run and each noise run,
because §1.275 found that a change to one pool vector decorrelates the draw
the way a new seed does.

Every number here is read from the inputs. Nothing runs the model.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import numpy as np                                    # noqa: E402

from score import cluster_bootstrap                   # noqa: E402
from test_pool_bounds import (_FIRST_UNHELD_TARGET,   # noqa: E402
                              _actual_shares, _capacity_cases,
                              _p1_violations)

NOT_TESTED = "NOT TESTED"
PASS, FAIL, VOID = "PASSED", "FAILED", "VOID"
UNINFORMATIVE = "PASSED (uninformative)"

# From the prereg's text: "24 emitted backtest specs", "over 24 city-years".
PREREG_POPULATION = 24
BEFORE_COMMIT = "69cc6cc"

# Provenance a placebo row may differ in. Everything else in the row must be
# identical. `constants_read` names the code's registers, not a drawn number.
PLACEBO_EXEMPT = ("constants_read",)

# Spec leaves differing by less than this, with the structure unchanged, are
# round-off, not a change (the largest seen in §1.279 is 1.6e-13).
ROUNDOFF = 1e-9

# P6, typed from the prereg: "currently 2,120 ... stays inside 2,110-2,135".
P6_PREREG_BASE = 2120
P6_BAND = (2110, 2135)
P6_CAPETOWN_MAX = 1
COVERAGE_POPULATION = "reference"


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def spec_key(path: Path, root: Path) -> tuple[str, str] | None:
    """(slug, target) for a pool spec, or None for a variant (simulation).
    Johannesburg's specs sit directly under `processed/`."""
    year = path.stem.replace("pools_", "")
    if not year.isdigit():
        return None
    rel = path.relative_to(root)
    slug = rel.parts[0] if len(rel.parts) > 1 else "joburg"
    return slug, year


def load_specs(root: Path) -> dict[tuple[str, str], dict]:
    out = {}
    for p in sorted(root.glob("**/pools_*.json")):
        k = spec_key(p, root)
        if k is not None:
            out[k] = json.loads(p.read_text())
    return out


def load_rows(path: Path) -> tuple[dict, dict[tuple[str, str], dict]]:
    payload = json.loads(Path(path).read_text())
    if not isinstance(payload, dict) or "manifest" not in payload:
        raise SystemExit(f"{path}: no manifest; refusing a pre-manifest file")
    rows = {(r["slug"], str(r["year"])): r for r in payload["records"]}
    return payload["manifest"], rows


def backtest_keys(specs: dict) -> list[tuple[str, str]]:
    """The emitted backtest population: digit-year specs before the first
    unheld target, the same boundary `test_pool_bounds` uses."""
    return sorted(k for k in specs if int(k[1]) < _FIRST_UNHELD_TARGET)


# --------------------------------------------------------------------------
# The spec diff. Arithmetic on artefacts.
# --------------------------------------------------------------------------

def _strip_key(spec: dict) -> dict:
    """The spec without its key, and without an EMPTY `mergers` list (F5's
    field; absent and `[]` are the same fact)."""
    return {k: v for k, v in spec.items()
            if k != "artefact_key" and not (k == "mergers" and v == [])}


def _flat(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _flat(v, f"{pre}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _flat(v, f"{pre}[{i}]")
    else:
        yield pre, x


def spec_class(before: dict, after: dict) -> tuple[str, float]:
    """``key_only``, ``roundoff`` or ``changed``, and the largest numeric
    difference. Round-off: same leaves, every difference numeric and below
    :data:`ROUNDOFF`."""
    fb, fa = dict(_flat(_strip_key(before))), dict(_flat(_strip_key(after)))
    if fb == fa:
        return "key_only", 0.0
    if set(fb) != set(fa):
        return "changed", float("inf")
    worst = 0.0
    for p in fb:
        a, b = fb[p], fa[p]
        if a == b:
            continue
        if not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
            return "changed", float("inf")
        worst = max(worst, abs(float(a) - float(b)))
    return ("roundoff" if worst < ROUNDOFF else "changed"), worst


def registered_dose(before: dict, after: dict) -> float:
    """L1 change of the pools' `registered` vector over the roll (P7's
    quantity). An absent pool counts as zero registered."""
    names = set(before.get("pools", {})) | set(after.get("pools", {}))
    rb = {n: float(before.get("pools", {}).get(n, {}).get("registered", 0.0))
          for n in names}
    ra = {n: float(after.get("pools", {}).get(n, {}).get("registered", 0.0))
          for n in names}
    roll = sum(rb.values()) or sum(ra.values())
    if roll <= 0:
        return float("nan")
    return sum(abs(ra[n] - rb[n]) for n in names) / roll


def band_dose(before: dict, after: dict) -> float:
    """Sum over pools of |Δ| in the turnout triple. Context beside
    `registered_dose`: F3 also reaches specs through the bands."""
    total = 0.0
    for n in set(before.get("pools", {})) | set(after.get("pools", {})):
        tb = before.get("pools", {}).get(n, {}).get("turnout") or [0, 0, 0]
        ta = after.get("pools", {}).get(n, {}).get("turnout") or [0, 0, 0]
        total += sum(abs(float(x) - float(y)) for x, y in zip(tb, ta))
    return total


def spec_diff(before: dict, after: dict) -> dict:
    out = {}
    for k in sorted(set(before) | set(after)):
        if k not in before or k not in after:
            out[k] = {"missing": "before" if k not in before else "after"}
            continue
        b, a = before[k], after[k]
        cls, worst = spec_class(b, a)
        sb, sa = _strip_key(b), _strip_key(a)
        out[k] = {"p1_before": _p1_violations(b),
                  "p1_after": _p1_violations(a),
                  "class": cls, "max_abs": worst,
                  "fields_moved": sorted(f for f in set(sb) | set(sa)
                                         if sb.get(f) != sa.get(f)),
                  "dose": registered_dose(b, a),
                  "band_dose": band_dose(b, a)}
    return out


# --------------------------------------------------------------------------
# The pair
# --------------------------------------------------------------------------

def _manifest_keys(manifest: dict) -> dict[tuple[str, str], str]:
    """(slug, year) -> the `pools_sha` the history says it ran on."""
    out = {}
    for slug, files in (manifest.get("pool_artefact_keys") or {}).items():
        for name, key in (files or {}).items():
            year = name.replace("pools_", "").replace(".json", "")
            if year.isdigit():
                out[(slug, year)] = (key or {}).get("pools_sha")
    return out


def pair_checks(mb, ma, rb, ra, specs_b, specs_a) -> dict:
    """Every condition under which a paired difference means anything.
    Each is a boolean; the pair is valid only if all hold."""
    pop = backtest_keys(specs_a)
    c = {}
    for f in ("seed", "draws", "seed_by_row", "env_switches", "overrides",
              "filters"):
        c[f"same_{f}"] = mb.get(f) == ma.get(f)
    c["no_filter"] = not any((ma.get("filters") or {}).values())
    c["same_excluded"] = ((mb.get("population") or {}).get("excluded")
                          == (ma.get("population") or {}).get("excluded"))
    c["before_commit"] = str(mb.get("git_commit", "")).startswith(BEFORE_COMMIT)
    c["both_clean"] = mb.get("git_dirty") is False and ma.get("git_dirty") is False
    c["population_is_prereg"] = len(pop) == PREREG_POPULATION
    c["rows_are_population"] = (sorted(rb) == pop and sorted(ra) == pop)
    for side, m, specs in (("before", mb, specs_b), ("after", ma, specs_a)):
        declared = _manifest_keys(m)
        c[f"{side}_bound_to_specs"] = bool(pop) and all(
            declared.get(k) == (specs.get(k) or {}).get("artefact_key", {})
            .get("pools_sha") for k in pop)
    return c


# --------------------------------------------------------------------------
# Paired statistics
# --------------------------------------------------------------------------

def paired(values: dict, label: str) -> dict:
    """Mean paired difference with a city-clustered percentile interval
    (`score.cluster_bootstrap`). When a percentile bound sits EXACTLY at
    zero, the interval cannot exclude zero whatever the size of the move: an
    integer statistic that moves in few cities leaves enough all-zero
    resamples to pin it (R2 F1). Containing zero is then no test, and
    `informative` is False. `zero_mass` (the share of replicates exactly zero)
    is reported beside it; on its own it is not the test, because symmetric
    moves also produce exact zeros with zero well inside the interval."""
    finite = {k: v for k, v in values.items() if v == v}
    groups: dict[str, list[float]] = {}
    for (slug, _year), v in sorted(finite.items()):
        groups.setdefault(slug, []).append(float(v))
    ci = cluster_bootstrap(list(groups.values()))
    reps = ci["replicates"]
    zero_mass = float((reps == 0).mean()) if reps.size else float("nan")
    informative = ci["lo"] == ci["lo"] and ci["lo"] != 0.0 and ci["hi"] != 0.0
    return {"what": label, "n": len(finite),
            "total": float(sum(finite.values())),
            "mean": ci["point"], "lo": ci["lo"], "hi": ci["hi"],
            "clusters": ci["clusters"], "zero_mass": zero_mass,
            "informative": bool(informative),
            "contains_zero": (bool(ci["lo"] <= 0.0 <= ci["hi"])
                              if ci["lo"] == ci["lo"] else None)}


def _abs_err(seats: dict, parties) -> float:
    """Σ |actual − model MEDIAN| over ``parties`` in a row's `seats` table.
    The row stores no per-party coherent seat, so this is context only."""
    return float(sum(abs(seats[p][0] - seats[p][1]) for p in parties
                     if p in seats))


def arrived(key) -> set | None:
    """Parties with seats or votes at the target and no preceding-NPE share,
    by `backtest.arrival_baseline`, the one definition. Reads inputs only.
    None when the baseline is unreadable."""
    import backtest
    import cityconfig
    target = cityconfig.Target(city=cityconfig.load(key[0]), year=key[1])
    base = backtest.arrival_baseline(target, ROOT / "data/raw/elections")
    return None if base is None else set(base)


def noise_spread(stat, base_rows, noise_runs) -> dict:
    """The statistic `stat(before_rows, other_rows)` between the before run and
    each noise run: the size a pure re-seed produces."""
    vals = [stat(base_rows, r) for r in noise_runs]
    return {"values": vals,
            "max_abs": max((abs(v) for v in vals), default=float("nan"))}


def _within(observed: float, spread: dict) -> bool | None:
    m = spread.get("max_abs")
    return None if m != m else bool(abs(observed) <= m)


# --------------------------------------------------------------------------
# Calibration helpers
# --------------------------------------------------------------------------

def _cal(row):
    return row["calibration"][COVERAGE_POPULATION]


def _pooled_coverage(rows_, keys):
    inside, counted = {}, {}
    for k in keys:
        for c in _cal(rows_[k])["coverage"]:
            lvl = float(c["level"])
            inside[lvl] = inside.get(lvl, 0) + c["inside"]
            counted[lvl] = counted.get(lvl, 0) + c["counted"]
    return {lvl: inside[lvl] / counted[lvl] for lvl in inside if counted[lvl]}


def _pits(rows_, keys, band=None):
    out = []
    for k in keys:
        cal = _cal(rows_[k])
        bands = cal.get("band") or [None] * len(cal["pit"])
        for p, b in zip(cal["pit"], bands):
            if p is not None and p == p and (band is None or b == band):
                out.append(float(p))
    return out


def _pit_summary(rows_, keys):
    pits = _pits(rows_, keys)
    bands = sorted({b for k in keys for b in (_cal(rows_[k]).get("band") or [])
                    if b is not None}, key=str)
    return {"mean": float(np.mean(pits)) if pits else float("nan"),
            "sd": float(np.std(pits)) if pits else float("nan"),
            "by_band": {str(b): float(np.mean(_pits(rows_, keys, b)))
                        for b in bands if _pits(rows_, keys, b)}}


# --------------------------------------------------------------------------
# The scoring
# --------------------------------------------------------------------------

def score(before_specs, after_specs, before_hist, after_hist,
          noise_hists=()) -> dict:
    (mb, rb), (ma, ra) = before_hist, after_hist
    # A noise run need only carry the rows that move; the rest are the before
    # run's, which is what a placebo row is by definition.
    noise = [{**rb, **{k: r for k, r in h[1].items() if k in rb}}
             for h in noise_hists]
    res: dict = {"inputs": {}, "predictions": {}, "window": {}}

    checks = pair_checks(mb, ma, rb, ra, before_specs, after_specs)
    res["inputs"]["checks"] = checks
    res["inputs"]["git"] = {"before": mb.get("git_commit"),
                            "after": ma.get("git_commit")}
    pair_ok = all(checks.values())

    diff = spec_diff(before_specs, after_specs)
    res["spec_diff"] = {f"{s} {y}": d for (s, y), d in diff.items()}
    pop = backtest_keys(after_specs)
    rows = [k for k in pop if k in rb and k in ra]

    # --- placebo: the whole row, less provenance --------------------------
    quiet = [k for k in rows if diff.get(k, {}).get("class")
             in ("key_only", "roundoff")]
    broken = {}
    for k in quiet:
        fields = sorted(f for f in set(rb[k]) | set(ra[k])
                        if f not in PLACEBO_EXEMPT and rb[k].get(f) != ra[k].get(f))
        if fields:
            broken[f"{k[0]} {k[1]}"] = fields
    res["placebo"] = {"rows": [f"{s} {y}" for s, y in quiet],
                      "roundoff_rows": [f"{s} {y}" for s, y in quiet
                                        if diff[(s, y)]["class"] == "roundoff"],
                      "broken": broken, "holds": bool(quiet) and not broken}
    moved = [k for k in rows if k not in quiet]
    res["moved_rows"] = [f"{s} {y}" for s, y in moved]
    valid = pair_ok and res["placebo"]["holds"]
    res["inputs"]["paired_valid"] = valid

    def v(verdict):
        return VOID if not valid else verdict

    # --- P1: on the spec files ---------------------------------------------
    p1_bad = {f"{s} {y}": _p1_violations(after_specs[(s, y)])
              for (s, y) in pop if _p1_violations(after_specs[(s, y)])}
    res["predictions"]["P1"] = {
        "verdict": (PASS if len(pop) == PREREG_POPULATION and not p1_bad
                    else FAIL),
        "population": len(pop), "violations_after": p1_bad,
        "violations_before": sum(bool(_p1_violations(before_specs[k]))
                                 for k in pop if k in before_specs),
        "READING": "the prereg's two clauses (`test_pool_bounds._p1_violations`)"
                   " on every emitted backtest spec FILE; the population must "
                   "be the prereg's 24."}

    # --- capacity scan: context for P2-P4 ----------------------------------
    def scan(specs, hist):
        return [{"row": f"{k[0]} {k[1]}", **c} for k in rows if k in specs
                for c in _capacity_cases(specs[k], _actual_shares(hist[k]))]
    scan_b, scan_a = scan(before_specs, ra), scan(after_specs, ra)
    res["scan"] = {"before": scan_b, "after": scan_a,
                   "LIMIT": "`_actual_shares` reads `votes`, the row's top-12 "
                            "parties, so a case outside a city-year's top 12 "
                            "is not seen (R2 F11)."}

    def fatal(cases):
        return [c for c in cases if c["kind"] in ("fatal", "zero")]
    res["predictions"]["P2"] = {
        "verdict": NOT_TESTED,
        "why": "C2 is F4, after the election. No repair was made.",
        "context": _pool_roll_shares(after_specs, [
            (c, y) for c in ("capetown", "ethekwini")
            for y in ("2011", "2016", "2021")])}
    res["predictions"]["P3"] = {
        "verdict": NOT_TESTED,
        "why": "stated 'after C3'; C3 was not made.",
        "context": {"fatal_before": len(fatal(scan_b)),
                    "fatal_after": len(fatal(scan_a)),
                    "total_before": len(scan_b), "total_after": len(scan_a)}}
    res["predictions"]["P4"] = {
        "verdict": NOT_TESTED,
        "why": "stated 'after all four repairs'; one was made.",
        "context": {"cases_after": len(scan_a),
                    "DA_cases_after": sum(c["party"] == "DA" for c in scan_a),
                    "parties_after": sorted({c["party"] for c in scan_a}),
                    "at_2021_after": [c for c in scan_a
                                      if c["row"].endswith("2021")]}}

    # --- paired row differences --------------------------------------------
    def dd(fn, a=ra, b=rb):
        return {k: fn(a[k]) - fn(b[k]) for k in rows}

    d_seat = dd(lambda r: r["seat_abs_err_coherent"])
    d_crps = dd(lambda r: r["crps"])

    # --- P5 -------------------------------------------------------------------
    headline = paired(d_seat, "Δ seat_abs_err_coherent per city-year")
    if not headline["informative"]:
        p5 = UNINFORMATIVE
    else:
        p5 = PASS if headline["contains_zero"] else FAIL

    def arrival_err(r):
        g = r.get("arrival_group") or {}
        x = g.get("seats_err")
        return abs(x) if isinstance(x, (int, float)) else float("nan")
    d_arr = dd(arrival_err)
    arr_total = float(sum(x for x in d_arr.values() if x == x))

    arrivals = {k: arrived(k) for k in rows} if valid else {}
    established = {}
    for k in rows:
        a_set = arrivals.get(k) or set()
        seeds = (set((after_specs.get(k) or {}).get("seeds", {}))
                 | set((before_specs.get(k) or {}).get("seeds", {})))
        cols = (set(ra[k]["seats"]) | set(rb[k]["seats"])) - seeds - a_set
        established[k] = (_abs_err(ra[k]["seats"], cols)
                          - _abs_err(rb[k]["seats"], cols))
    res["predictions"]["P5"] = {
        "verdict": v(p5),
        "headline": headline,
        "headline_noise": noise_spread(
            lambda b, o: sum(o[k]["seat_abs_err_coherent"]
                             - b[k]["seat_abs_err_coherent"] for k in moved),
            rb, noise),
        "directional_arrival": {
            "d_abs_arrival_group_seats_err_total": arr_total,
            "verdict": v(PASS if arr_total < 0 else FAIL),
            "noise": noise_spread(
                lambda b, o: sum(arrival_err(o[k]) - arrival_err(b[k])
                                 for k in moved
                                 if arrival_err(o[k]) == arrival_err(o[k])),
                rb, noise)},
        "context_established_median": paired(
            established, "Δ Σ|actual−median| over columns neither seeded nor "
                         "arrived (MEDIAN statistic; context only)"),
        "READING": "'changes by less than its own paired bootstrap interval' = "
                   "the 95% city-cluster interval of the mean paired change "
                   "contains zero; when a bound sits exactly at zero the interval "
                   "cannot exclude zero and the result is recorded PASSED "
                   "(uninformative). The established-columns "
                   "clause cannot be scored on the coherent statistic (no "
                   "per-party coherent seat is stored) and is context. The "
                   "directional claim is scored on the arrival group's "
                   "|seats_err| (seeded columns are arrivals, so they are "
                   "counted once)."}

    # --- P6 -------------------------------------------------------------------
    called_b = sum(rb[k]["wards"]["called"] for k in rows)
    called_a = sum(ra[k]["wards"]["called"] for k in rows)
    delta = called_a - called_b
    lo, hi = (P6_BAND[0] - P6_PREREG_BASE, P6_BAND[1] - P6_PREREG_BASE)
    matched_equal = all(ra[k]["wards"]["wards_matched"]
                        == rb[k]["wards"]["wards_matched"] for k in rows)
    ct = [k for k in rows if k[0] == "capetown"]
    ct_abs = sum(abs(ra[k]["wards"]["called"] - rb[k]["wards"]["called"])
                 for k in ct)

    def brier(rs):
        return float(np.mean([rs[k]["wards"]["brier_multicategory"]
                              for k in rows]))
    if not matched_equal:
        p6 = VOID
    elif delta > hi or ct_abs > P6_CAPETOWN_MAX:
        p6 = FAIL
    else:
        p6 = PASS
    res["predictions"]["P6"] = {
        "verdict": v(p6),
        "called_before": called_b, "called_after": called_a, "delta": delta,
        "band_as_change": (lo, hi), "band_absolute": P6_BAND,
        "absolute_in_band": P6_BAND[0] <= called_a <= P6_BAND[1],
        "loss_beyond_band": delta < lo,
        "wards_matched_equal": matched_equal,
        "capetown_abs_change": ct_abs,
        "capetown_uninformative": "Cape Town's rows carry no C1 change; the "
                                  "repair the clause was written for (C2) did "
                                  "not ship.",
        "brier_mean_before": brier(rb), "brier_mean_after": brier(ra),
        "noise": noise_spread(
            lambda b, o: sum(o[k]["wards"]["called"] - b[k]["wards"]["called"]
                             for k in moved), rb, noise),
        "READING": "the band read as a CHANGE from the before run (2,110-2,135 "
                   "around the stated 2,120, so -10..+15), since the prereg "
                   "fixed it around its baseline; the absolute band is printed. "
                   "Falsified by a gain above +15 (the prereg's falsifier is "
                   "one-sided) or by Cape Town moving more than one ward, "
                   "counting each gain and loss. A loss below -10 is reported, "
                   "not scored. VOID if any row's wards_matched differs."}

    # --- P7 -------------------------------------------------------------------
    res["predictions"]["P7"] = {
        "verdict": NOT_TESTED,
        "why": "its premise ('C3 moves all 27 specs') did not happen, and its "
               "dose (`registered`) was defined for C3's channel. C1 reaches "
               "rows by `registered`, the turnout bands, and the run-time "
               "`pool_counts` recompute, which no spec field records (R2 F4). "
               "Locality is the placebo's job.",
        "context": {f"{s} {y}": {"class": diff[(s, y)]["class"],
                                 "dose": diff[(s, y)]["dose"],
                                 "band_dose": diff[(s, y)]["band_dose"],
                                 "d_crps": d_crps[(s, y)]}
                    for s, y in moved}}

    # --- the window -----------------------------------------------------------
    years = sorted({k[1] for k in rows})

    def cyc(b, o):
        return {y: float(sum(o[k]["crps"] - b[k]["crps"]
                             for k in moved if k[1] == y)) for y in years}
    by_cycle = cyc(rb, ra)
    cyc_noise = {y: noise_spread(lambda b, o, y=y: cyc(b, o)[y], rb, noise)
                 for y in years}
    res["window"]["crps_by_cycle"] = {
        "change": by_cycle,
        "moved_rows_per_cycle": {y: sum(k[1] == y for k in moved) for y in years},
        "noise": cyc_noise,
        "within_noise": {y: _within(by_cycle[y], cyc_noise[y]) for y in years},
        "verdict": v(FAIL if any(x > 0 for x in by_cycle.values()) else PASS),
        "READING": "summed paired seat CRPS change per cycle (lower is better); "
                   "fails on a net loss in any cycle. Scored as written; the "
                   "seed spread is printed beside it and does not change the "
                   "verdict."}

    cov_b, cov_a = _pooled_coverage(rb, rows), _pooled_coverage(ra, rows)
    pit_b, pit_a = _pit_summary(rb, rows), _pit_summary(ra, rows)
    away = {lvl: abs(cov_a[lvl] - lvl) > abs(cov_b[lvl] - lvl) + 1e-12
            for lvl in cov_b}
    pit_away = abs(pit_a["mean"] - 0.5) > abs(pit_b["mean"] - 0.5) + 1e-12
    res["window"]["calibration"] = {
        "population": COVERAGE_POPULATION,
        "coverage_before": cov_b, "coverage_after": cov_a,
        "pit_before": pit_b, "pit_after": pit_a,
        "moved_away": away, "pit_mean_moved_away": pit_away,
        "coverage_noise": {
            lvl: noise_spread(lambda b, o, lvl=lvl: _pooled_coverage(o, rows)[lvl]
                              - _pooled_coverage(b, rows)[lvl], rb, noise)
            for lvl in cov_b},
        "verdict": v(FAIL if any(away.values()) or pit_away else PASS),
        "READING": "pooled coverage (Σinside/Σcounted) at each level and pooled "
                   "mean PIT, over the fixed `reference` columns; fails if any "
                   "moves further from nominal by any amount. PIT sd and mean "
                   "PIT per rank band are printed as the shape (R2 F7); the "
                   "seed spread is printed and does not change the verdict."}

    d_pr = dd(lambda r: r["pr_mae"])
    d_wd = dd(lambda r: r["ward_mae"])
    tot = {"seat": float(sum(d_seat.values())), "pr": float(sum(d_pr.values())),
           "ward": float(sum(d_wd.values()))}
    seats_better = tot["seat"] < 0
    votes_better = tot["pr"] < 0 or tot["ward"] < 0
    res["window"]["seats_without_votes"] = {
        "d_seat_total": tot["seat"], "d_pr_mae_total": tot["pr"],
        "d_ward_mae_total": tot["ward"],
        "verdict": v(FAIL if seats_better and not votes_better else PASS),
        "READING": "fails when summed coherent seat error falls while neither "
                   "summed PR nor summed ward MAE falls; both components "
                   "printed."}
    res["window"]["p1"] = res["predictions"]["P1"]["verdict"]
    res["window"]["no_dose_response"] = NOT_TESTED + " (P7)"

    res["mergers_prereg"] = {
        "change_1_independents": NOT_TESTED + ": not in the freeze.",
        "change_2_mergers": "scored in MODEL-LOG §1.275 on run_model; no "
                            "declared merger predates a held election, so no "
                            "backtest row can test it.",
        "change_3_roster": "no change; nothing to score."}
    return res


def _pool_roll_shares(specs, keys):
    out = {}
    for k in keys:
        s = specs.get(k)
        if not s:
            continue
        reg = {n: float(p.get("registered", 0.0)) for n, p in s["pools"].items()}
        tot = sum(reg.values())
        out[f"{k[0]} {k[1]}"] = {n: x / tot for n, x in reg.items()} if tot else {}
    return out


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def report(res: dict) -> str:
    L = ["F9 scoring", "", "inputs:", json.dumps(res["inputs"], indent=1), ""]
    L.append(f"placebo: {len(res['placebo']['rows'])} rows "
             f"(round-off {res['placebo']['roundoff_rows']}), "
             f"holds={res['placebo']['holds']}, broken={res['placebo']['broken']}")
    L.append(f"moved rows: {res['moved_rows']}")
    for name, p in res["predictions"].items():
        L.append(f"\n{name}: {p['verdict']}")
        for k, x in p.items():
            if k != "verdict":
                L.append(f"  {k}: {json.dumps(x, default=str)[:700]}")
    L.append("\nwindow:")
    for name, w in res["window"].items():
        L.append(f"  {name}: {json.dumps(w, default=str)[:900]}")
    L.append("\nmergers prereg: " + json.dumps(res["mergers_prereg"], indent=1))
    return "\n".join(L)


# --------------------------------------------------------------------------
# Self-test: constructed inputs, each branch made to flip and revert
# --------------------------------------------------------------------------

def _fixture(n_cities=8):
    """``n_cities`` cities x 3 cycles = the prereg's 24 when n_cities is 8.
    c0 2016 is C1-shaped (a pool dropped before, restored after). Constructed,
    not lifted from an artefact."""
    def spec(pools_, cats, shares, seeds=()):
        return {"categories": cats, "pool_shares_at_target": shares,
                "pools": pools_, "seeds": {s: {} for s in seeds},
                "artefact_key": {"pools_sha": "old"}}

    def pool(reg, members, turnout=(0.3, 0.5, 0.7)):
        return {"registered": reg, "turnout": list(turnout),
                "members": members}
    full = {"A": pool(900.0, {"P": 0.9, "Q": 0.5}),
            "B": pool(100.0, {"P": 0.1, "Q": 0.5})}
    cats, sh = ["A", "B"], [0.9, 0.1]
    cities = [f"c{i}" for i in range(n_cities)]
    before = {(c, y): spec(copy.deepcopy(full), cats, sh)
              for c in cities for y in ("2011", "2016", "2021")}
    before[("c0", "2016")] = spec({"A": pool(1000.0, {"P": 1.0, "Q": 1.0})},
                                  cats, sh)
    after = copy.deepcopy(before)
    after[("c0", "2016")] = spec(copy.deepcopy(full), cats, sh)
    for s in after.values():
        s["artefact_key"] = {"pools_sha": "new"}
        s["mergers"] = []

    def row(slug, year):
        cov = [{"level": lvl, "inside": int(round(lvl * 10)), "counted": 10,
                "empirical": 0} for lvl in (0.5, 0.8, 0.9)]
        return {"slug": slug, "year": year, "seat_abs_err": 10,
                "seat_abs_err_coherent": 10, "crps": 5.0,
                "pr_mae": 1.0, "ward_mae": 1.0,
                "votes": [["P", 0, 0, 0.6, 0, 0, 0], ["Q", 0, 0, 0.4, 0, 0, 0]],
                "seats": {"P": [10, 9], "Q": [5, 6]},
                "wards": {"n_wards": 100, "wards_matched": 100,
                          "called": 90, "hit_rate": 0.9,
                          "brier_multicategory": 0.05},
                "calibration": {"reference": {"coverage": cov,
                                              "pit": [0.4, 0.6],
                                              "band": ["1-3", "4-12"]}},
                "arrival_group": {"seats_err": 2},
                "constants_read": ["X"]}

    def manifest(commit, specs):
        keys = {}
        for (c, y), s in specs.items():
            keys.setdefault(c, {})[f"pools_{y}.json"] = s["artefact_key"]
        return {"seed": 1, "draws": 10, "seed_by_row": {}, "overrides": [],
                "filters": {"city": None, "target": None},
                "env_switches": {"raw": {"PYTHONHASHSEED": "0"}},
                "population": {"excluded": []},
                "git_commit": commit, "git_dirty": False,
                "pool_artefact_keys": keys}
    rb = {k: row(*k) for k in before}
    ra = copy.deepcopy(rb)
    ra[("c0", "2016")]["crps"] = 4.0            # the moved row improves
    return (before, after, (manifest(BEFORE_COMMIT + "abc", before), rb),
            (manifest("fff", after), ra))


def _score(b, a, hb, ha, noise=()):
    # `arrived` reads real inputs; the fixture's cities have none.
    global arrived
    real = arrived
    arrived = lambda key: set()                 # noqa: E731
    try:
        return score(b, a, hb, ha, noise)
    finally:
        arrived = real


def self_test() -> None:
    C = copy.deepcopy
    b, a, hb, ha = _fixture()
    r = _score(b, a, hb, ha)
    P, W = r["predictions"], r["window"]
    assert all(r["inputs"]["checks"].values()), r["inputs"]["checks"]
    assert r["placebo"]["holds"] and r["moved_rows"] == ["c0 2016"]
    assert P["P1"]["verdict"] == PASS and P["P1"]["violations_before"] == 1
    assert {P[p]["verdict"] for p in ("P2", "P3", "P4", "P7")} == {NOT_TESTED}
    assert W["no_dose_response"].startswith(NOT_TESTED)
    assert P["P6"]["verdict"] == PASS
    assert W["crps_by_cycle"]["verdict"] == PASS
    assert W["calibration"]["verdict"] == PASS
    assert W["seats_without_votes"]["verdict"] == PASS
    # No seat move, or a move in ONE city: the interval is pinned at zero,
    # so the pass is recorded as uninformative (R2 F1).
    assert P["P5"]["verdict"] == UNINFORMATIVE
    ha1 = C(ha); ha1[1][("c0", "2016")]["seat_abs_err_coherent"] = 0
    assert _score(b, a, hb, ha1)["predictions"]["P5"]["verdict"] == UNINFORMATIVE

    # P5 FAIL: seat error falls in one row of EVERY city; the other 16 rows
    # stay placebo, so the pair is valid and the interval leaves zero.
    a2, ha2 = C(a), C(ha)
    for c in [f"c{i}" for i in range(8)]:
        a2[(c, "2021")]["pools"]["A"]["turnout"] = [0.31, 0.5, 0.7]
        ha2[1][(c, "2021")]["seat_abs_err_coherent"] = 6
    ha2 = (_manifest_like(ha2[0], a2), ha2[1])
    r2 = _score(b, a2, hb, ha2)
    assert r2["placebo"]["holds"], r2["placebo"]
    assert r2["predictions"]["P5"]["verdict"] == FAIL, r2["predictions"]["P5"]
    # ... and it passes when the seat error is put back, the rows still moved
    # (a change that moves CRPS but not seats).
    for c in [f"c{i}" for i in range(8)]:
        ha2[1][(c, "2021")]["seat_abs_err_coherent"] = 10
        ha2[1][(c, "2021")]["crps"] = 4.9 if c < "c4" else 5.1
    ha2[1][("c0", "2021")]["seat_abs_err_coherent"] = 9
    ha2[1][("c1", "2021")]["seat_abs_err_coherent"] = 11
    ha2[1][("c2", "2021")]["seat_abs_err_coherent"] = 9
    ha2[1][("c3", "2021")]["seat_abs_err_coherent"] = 11
    ha2[1][("c4", "2021")]["seat_abs_err_coherent"] = 9
    ha2[1][("c5", "2021")]["seat_abs_err_coherent"] = 11
    ha2[1][("c6", "2021")]["seat_abs_err_coherent"] = 9
    ha2[1][("c7", "2021")]["seat_abs_err_coherent"] = 11
    assert _score(b, a2, hb, ha2)["predictions"]["P5"]["verdict"] == PASS

    # P5 directional: the arrival group worsening fails it.
    ha3 = C(ha); ha3[1][("c0", "2016")]["arrival_group"]["seats_err"] = 5
    assert (_score(b, a, hb, ha3)["predictions"]["P5"]["directional_arrival"]
            ["verdict"] == FAIL)
    ha3[1][("c0", "2016")]["arrival_group"]["seats_err"] = 1
    assert (_score(b, a, hb, ha3)["predictions"]["P5"]["directional_arrival"]
            ["verdict"] == PASS)

    # P1 sees a dropped pool in an after spec FILE.
    a4 = C(a); a4[("c1", "2021")]["pools"].pop("B")
    assert _score(b, a4, hb, (_manifest_like(ha[0], a4), ha[1]))[
        "predictions"]["P1"]["verdict"] == FAIL

    # The placebo trips on ANY row field, and voids every paired verdict.
    ha5 = C(ha); ha5[1][("c2", "2021")]["pr_mae_median"] = 9.9
    r5 = _score(b, a, hb, ha5)
    assert not r5["placebo"]["holds"]
    assert {r5["predictions"][p]["verdict"] for p in ("P5", "P6")} == {VOID}
    assert {r5["window"][w]["verdict"] for w in
            ("crps_by_cycle", "calibration", "seats_without_votes")} == {VOID}
    # ... but not on exempt provenance.
    ha5b = C(ha); ha5b[1][("c2", "2021")]["constants_read"] = ["Y"]
    assert _score(b, a, hb, ha5b)["placebo"]["holds"]
    # Round-off specs are placebo rows.
    a5 = C(a); a5[("c3", "2011")]["pools"]["A"]["members"]["P"] += 1e-13
    r5c = _score(b, a5, hb, ha)
    assert "c3 2011" in r5c["placebo"]["roundoff_rows"]

    # The pair is refused on each manifest field, the commit, dirt, the
    # population, and the binding to the spec directory.
    for f, val in (("seed", 2), ("draws", 11), ("seed_by_row", {"x": 1}),
                   ("env_switches", {"raw": {"PYTHONHASHSEED": "1"}}),
                   ("git_dirty", True), ("overrides", ["k=v"])):
        ha6 = (dict(ha[0], **{f: val}), ha[1])
        assert not _score(b, a, hb, ha6)["inputs"]["paired_valid"], f
    hb6 = (dict(hb[0], git_commit="deadbeef"), hb[1])
    assert not _score(b, a, hb6, ha)["inputs"]["paired_valid"]
    ha7 = (ha[0], {k: x for k, x in ha[1].items() if k != ("c7", "2021")})
    assert not _score(b, a, hb, ha7)["inputs"]["paired_valid"]
    ha8 = (_manifest_like(ha[0], b), ha[1])     # after history names OLD specs
    assert not _score(b, a, hb, ha8)["inputs"]["paired_valid"]
    b9, a9 = ({k: x for k, x in b.items() if k[0] != "c7"},
              {k: x for k, x in a.items() if k[0] != "c7"})
    hb9 = (_manifest_like(hb[0], b9), {k: x for k, x in hb[1].items() if k[0] != "c7"})
    ha9 = (_manifest_like(ha[0], a9), {k: x for k, x in ha[1].items() if k[0] != "c7"})
    r9 = _score(b9, a9, hb9, ha9)
    assert not r9["inputs"]["checks"]["population_is_prereg"]
    assert r9["predictions"]["P1"]["verdict"] == FAIL

    # P6: a gain above the band fails; a Cape Town swing of two fails; a
    # wards_matched change voids it; the band is read as a change.
    ha10 = C(ha); ha10[1][("c0", "2016")]["wards"]["called"] = 106
    assert _score(b, a, hb, ha10)["predictions"]["P6"]["verdict"] == FAIL
    ha10[1][("c0", "2016")]["wards"]["called"] = 104
    assert _score(b, a, hb, ha10)["predictions"]["P6"]["verdict"] == PASS
    ha10[1][("c0", "2016")]["wards"]["called"] = 70
    r10 = _score(b, a, hb, ha10)["predictions"]["P6"]
    assert r10["verdict"] == PASS and r10["loss_beyond_band"]
    ha11 = C(ha); ha11[1][("c0", "2016")]["wards"]["wards_matched"] = 99
    assert _score(b, a, hb, ha11)["predictions"]["P6"]["verdict"] == VOID
    b12, a12 = _rename(b, "c0", "capetown"), _rename(a, "c0", "capetown")
    hb12 = (_manifest_like(hb[0], b12), _rename(hb[1], "c0", "capetown"))
    ha12 = (_manifest_like(ha[0], a12), _rename(ha[1], "c0", "capetown"))
    ha12[1][("capetown", "2016")]["wards"]["called"] = 92
    assert _score(b12, a12, hb12, ha12)["predictions"]["P6"]["verdict"] == FAIL

    # CRPS by cycle: a net loss fails; the noise spread is carried.
    ha13 = C(ha); ha13[1][("c0", "2016")]["crps"] = 6.0
    hn = C(hb); hn[1][("c0", "2016")]["crps"] = 5.5
    r13 = _score(b, a, hb, ha13, [hn])["window"]["crps_by_cycle"]
    assert r13["verdict"] == FAIL and r13["within_noise"]["2016"] is False
    hn[1][("c0", "2016")]["crps"] = 7.0
    assert _score(b, a, hb, ha13, [hn])["window"]["crps_by_cycle"][
        "within_noise"]["2016"] is True

    # Calibration: coverage moving away fails, moving toward passes; the
    # PIT mean moving away fails.
    ha14 = C(ha)
    for c in ha14[1][("c0", "2016")]["calibration"]["reference"]["coverage"]:
        if c["level"] == 0.8:
            c["inside"] = 4
    assert _score(b, a, hb, ha14)["window"]["calibration"]["verdict"] == FAIL
    hb14, ha14b = C(hb), C(ha)
    for h, v_ in ((hb14, 4), (ha14b, 6)):
        for c in h[1][("c0", "2016")]["calibration"]["reference"]["coverage"]:
            if c["level"] == 0.8:
                c["inside"] = v_
    assert _score(b, a, hb14, ha14b)["window"]["calibration"]["verdict"] == PASS
    ha15 = C(ha); ha15[1][("c0", "2016")]["calibration"]["reference"]["pit"] = [0.9, 0.9]
    assert _score(b, a, hb, ha15)["window"]["calibration"]["verdict"] == FAIL

    # Seats without votes: seats improve, votes do not -> fail; votes also
    # improve -> pass.
    ha16 = C(ha); ha16[1][("c0", "2016")]["seat_abs_err_coherent"] = 8
    assert _score(b, a, hb, ha16)["window"]["seats_without_votes"]["verdict"] == FAIL
    ha16[1][("c0", "2016")]["pr_mae"] = 0.9
    assert _score(b, a, hb, ha16)["window"]["seats_without_votes"]["verdict"] == PASS
    print("self-test: every branch flipped as constructed, and reverted")


def _manifest_like(m, specs):
    keys = {}
    for (c, y), s in specs.items():
        keys.setdefault(c, {})[f"pools_{y}.json"] = s["artefact_key"]
    return dict(m, pool_artefact_keys=keys)


def _rename(d, old, new):
    return {((new if s == old else s), y): copy.deepcopy(x)
            for (s, y), x in d.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--before-specs", type=Path)
    ap.add_argument("--after-specs", type=Path)
    ap.add_argument("--before-history", type=Path)
    ap.add_argument("--after-history", type=Path)
    ap.add_argument("--noise", type=Path, nargs="*", default=[])
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    if a.self_test:
        self_test()
        return 0
    res = score(load_specs(a.before_specs), load_specs(a.after_specs),
                load_rows(a.before_history), load_rows(a.after_history),
                [load_rows(p) for p in a.noise])
    print(report(res))
    if a.json:
        a.json.write_text(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
