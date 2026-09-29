"""F9: score the freeze batch against its two pre-registrations.

    .venv/bin/python audits/2026-09-29-f9-scoring/score_f9.py \\
        --before-specs <dir> --after-specs <dir> \\
        --before-history <history.json> --after-history <history.json> \\
        [--json out.json]
    .venv/bin/python audits/2026-09-29-f9-scoring/score_f9.py --self-test

WHAT IS BEING SCORED. `prereg/2026-09-25-pool-input-repairs.md` (P1-P7 and
"What would say the window failed") and
`prereg/2026-09-27-independents-and-mergers.md`. Of the four pool repairs
only C1 shipped (F3, MODEL-LOG §1.269); C2 is F4, after the election; C3's
composition side and C4 were deferred by F2 (§1.268). Of the merger prereg
only Change 2 shipped (F5), and its amended predictions 1-5 were scored in
§1.275 on `run_model` directly. Independents (Change 1) did not ship. So:

  * a prediction whose repair was not made is reported NOT TESTED, never
    passed, and the instrument it names is still printed as context;
  * everything is scored as written; where the text needs an operational
    reading, the reading is stated in `READING` beside the verdict so the
    R2 review can dispute it.

THE PAIR. "before" is `69cc6cc` (the commit before F3, whose `pools.py`
hashes to the `pools_sha` the pre-F8 specs carry) run on the pre-F8 backup;
"after" is the freeze tree on the F8 specs. Same seed and draw count, checked
from both manifests. Code between the two that is not F3 is F5's merger
plumbing, a no-op at every backtest target, so:

  ⛔ THE PLACEBO IS THE TRIPWIRE. A spec that differs only in `artefact_key`
  must give an identical scored row. If any does not, the paired difference
  measures more than F3 and P5-P7 and the window criteria are VOID.

Every number here is read from the four inputs. Nothing runs the model.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import numpy as np                                    # noqa: E402

from score import cluster_bootstrap                   # noqa: E402
from test_pool_bounds import (_actual_shares,         # noqa: E402
                              _capacity_cases, _p1_violations)

NOT_TESTED = "NOT TESTED"
PASS, FAIL, VOID = "PASSED", "FAILED", "VOID"

# Row fields the placebo must reproduce exactly. Everything P5-P7 and the
# window criteria read is in this list, plus the vote errors and calibration.
PLACEBO_FIELDS = ("seats", "seat_abs_err", "seat_abs_err_coherent", "crps",
                  "pr_mae", "ward_mae", "wards", "calibration",
                  "arrival_group")

# P6's band and Cape Town allowance, typed from the prereg text.
P6_BAND = (2110, 2135)
P6_CAPETOWN_MAX = 1
COVERAGE_POPULATION = "reference"


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def spec_key(path: Path, root: Path) -> tuple[str, str] | None:
    """(slug, target) for a pool spec, or None for a variant (simulation).

    Johannesburg's specs sit directly under `processed/`; every other city has
    its own directory. Same rule as `test_pool_bounds`' scan.
    """
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


# --------------------------------------------------------------------------
# The spec diff: P1, the placebo set, and P7's dose. Arithmetic on artefacts.
# --------------------------------------------------------------------------

def _strip_key(spec: dict) -> dict:
    """The spec without its key, and without an EMPTY `mergers` list.

    F5 added `mergers` to every spec; at a backtest target it is `[]`, which
    declares that nothing moved. Absent (pre-F5) and `[]` are the same fact.
    A non-empty list is a change and stays.
    """
    return {k: v for k, v in spec.items()
            if k != "artefact_key" and not (k == "mergers" and v == [])}


def registered_dose(before: dict, after: dict) -> float:
    """L1 change of the pools' `registered` vector, as a fraction of the roll.

    A pool absent on one side counts as zero registered there, which is what
    C1's four specs look like before the fix. The roll is the before spec's
    registered total (the after total where the before one is zero).
    """
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
    """Sum over pools of |Δ| in the turnout triple (lo, centre, hi).

    Reported beside `registered_dose`, never instead of it: P7 names the
    `registered` vector. A spec whose turnout band moved with no registered
    change (Buffalo City 2021's Indian/Asian pool) is zero-dose by the
    prereg's measure and visibly not unchanged by this one.
    """
    total = 0.0
    for n in set(before.get("pools", {})) | set(after.get("pools", {})):
        tb = (before.get("pools", {}).get(n, {}).get("turnout") or [0, 0, 0])
        ta = (after.get("pools", {}).get(n, {}).get("turnout") or [0, 0, 0])
        total += sum(abs(float(x) - float(y)) for x, y in zip(tb, ta))
    return total


def spec_diff(before: dict, after: dict) -> dict:
    """Per city-year: P1 on each side, whether anything but the key moved,
    which top-level fields moved, and the registered dose."""
    out = {}
    for k in sorted(set(before) | set(after)):
        if k not in before or k not in after:
            out[k] = {"missing": "before" if k not in before else "after"}
            continue
        b, a = before[k], after[k]
        sb, sa = _strip_key(b), _strip_key(a)
        moved = sorted(f for f in set(sb) | set(sa) if sb.get(f) != sa.get(f))
        out[k] = {"p1_before": _p1_violations(b),
                  "p1_after": _p1_violations(a),
                  "key_only": not moved,
                  "fields_moved": moved,
                  "dose": registered_dose(b, a),
                  "band_dose": band_dose(b, a)}
    return out


# --------------------------------------------------------------------------
# Paired statistics
# --------------------------------------------------------------------------

def by_city(values: dict) -> list[list[float]]:
    """Group per-row values into one list per city: the bootstrap cluster."""
    groups: dict[str, list[float]] = {}
    for (slug, _y), v in sorted(values.items()):
        if v == v:
            groups.setdefault(slug, []).append(float(v))
    return list(groups.values())


def paired(values: dict, label: str) -> dict:
    """Mean and total of a per-row paired difference, with a percentile
    interval on the mean from resampling CITIES (`score.cluster_bootstrap`,
    the repository's one cluster bootstrap)."""
    finite = {k: v for k, v in values.items() if v == v}
    ci = cluster_bootstrap(by_city(finite))
    n = len(finite)
    return {"what": label, "n": n,
            "total": float(sum(finite.values())),
            "mean": ci["point"], "lo": ci["lo"], "hi": ci["hi"],
            "clusters": ci["clusters"],
            "contains_zero": bool(ci["lo"] <= 0.0 <= ci["hi"])
            if ci["lo"] == ci["lo"] else None}


def _abs_err(seats: dict, parties) -> float:
    """Sum of |actual - model median| over ``parties`` present in a row's
    `seats` table ((actual, model) pairs). The MEDIAN statistic: the row
    stores no per-party coherent apportionment."""
    return float(sum(abs(seats[p][0] - seats[p][1]) for p in parties
                     if p in seats))


# --------------------------------------------------------------------------
# The scoring
# --------------------------------------------------------------------------

def score(before_specs, after_specs, before_hist, after_hist) -> dict:
    (mb, rb), (ma, ra) = before_hist, after_hist
    res: dict = {"inputs": {}, "predictions": {}, "window": {}}

    # --- the pair is a pair -------------------------------------------------
    # `env_switches` carries PYTHONHASHSEED: under a different hash seed the
    # summation order changes the last float bit (test_drawer's header), and
    # the placebo compares with `!=`, so a mismatch there voids nothing
    # honestly -- it refuses the pair instead.
    same = {f: (mb.get(f), ma.get(f))
            for f in ("seed", "draws", "seed_by_row", "env_switches")}
    res["inputs"]["manifest_match"] = {f: v[0] == v[1] for f, v in same.items()}
    res["inputs"]["git"] = {"before": mb.get("git_commit"),
                            "after": ma.get("git_commit"),
                            "before_dirty": mb.get("git_dirty"),
                            "after_dirty": ma.get("git_dirty")}
    rows = sorted(set(rb) & set(ra))
    res["inputs"]["rows"] = {"both": len(rows),
                             "before_only": sorted(set(rb) - set(ra)),
                             "after_only": sorted(set(ra) - set(rb))}
    pair_ok = (all(res["inputs"]["manifest_match"].values())
               and not res["inputs"]["rows"]["before_only"]
               and not res["inputs"]["rows"]["after_only"])

    diff = spec_diff(before_specs, after_specs)
    res["spec_diff"] = {f"{s} {y}": d for (s, y), d in diff.items()}

    # --- placebo -------------------------------------------------------------
    placebo = [k for k in rows if diff.get(k, {}).get("key_only")]
    broken = {}
    for k in placebo:
        moved = [f for f in PLACEBO_FIELDS if rb[k].get(f) != ra[k].get(f)]
        if moved:
            broken[f"{k[0]} {k[1]}"] = moved
    res["placebo"] = {"rows": [f"{s} {y}" for s, y in placebo],
                      "broken": broken,
                      "holds": bool(placebo) and not broken}
    paired_valid = pair_ok and res["placebo"]["holds"]
    res["inputs"]["paired_valid"] = paired_valid

    # --- P1 -------------------------------------------------------------------
    backtest = [k for k in diff if k in ra]       # scored city-years
    p1_bad = {f"{s} {y}": diff[(s, y)].get("p1_after")
              for (s, y) in backtest if diff[(s, y)].get("p1_after")}
    missing = [f"{s} {y}" for (s, y) in backtest if "missing" in diff[(s, y)]]
    res["predictions"]["P1"] = {
        "verdict": PASS if backtest and not p1_bad and not missing else FAIL,
        "population": len(backtest),
        "violations_after": p1_bad, "missing": missing,
        "violations_before": sum(bool(diff[k].get("p1_before"))
                                 for k in backtest),
        "READING": "the prereg's two clauses, `test_pool_bounds._p1_violations`, "
                   "on every emitted spec with a scored row (the backtest "
                   "set). Future targets are checked by the same test, not "
                   "scored here."}

    # --- capacity scan (P3, P4, and D4's continuous instrument) -------------
    def scan(specs, hist):
        cases = []
        for k in rows:
            if k in specs:
                for c in _capacity_cases(specs[k], _actual_shares(hist[k])):
                    cases.append({"row": f"{k[0]} {k[1]}", **c})
        return cases
    # Actual shares are a property of the world: the same in both histories.
    scan_b, scan_a = scan(before_specs, ra), scan(after_specs, ra)
    res["scan"] = {"before": scan_b, "after": scan_a}

    def fatal(cases):
        return [c for c in cases if c["kind"] in ("fatal", "zero")]

    res["predictions"]["P2"] = {
        "verdict": NOT_TESTED,
        "why": "C2 (partial pooling of unidentified pool levels) is F4, "
               "deferred to after the election. No repair was made.",
        "context": _pool_roll_shares(after_specs,
                                     [("capetown", y) for y in
                                      ("2011", "2016", "2021")]
                                     + [("ethekwini", y) for y in
                                        ("2011", "2016", "2021")])}
    res["predictions"]["P3"] = {
        "verdict": NOT_TESTED,
        "why": "P3 is stated 'after C3'; C3 was not made (deferred by F2).",
        "context": {"fatal_before": len(fatal(scan_b)),
                    "fatal_after": len(fatal(scan_a)),
                    "total_before": len(scan_b), "total_after": len(scan_a)}}
    parties_after = sorted({c["party"] for c in scan_a})
    res["predictions"]["P4"] = {
        "verdict": NOT_TESTED,
        "why": "stated 'after all four repairs'; one was made.",
        "context": {"cases_after": len(scan_a),
                    "DA_cases_after": sum(c["party"] == "DA" for c in scan_a),
                    "parties_after": parties_after,
                    "at_2021_after": [c for c in scan_a
                                      if c["row"].endswith("2021")]}}

    # --- paired row differences --------------------------------------------
    def d(field_fn):
        return {k: field_fn(ra[k]) - field_fn(rb[k]) for k in rows}

    d_seat = d(lambda r: r["seat_abs_err_coherent"])
    d_crps = d(lambda r: r["crps"])

    # --- P5 -------------------------------------------------------------------
    seeded = {k: set((after_specs.get(k) or {}).get("seeds", {}))
              | set((before_specs.get(k) or {}).get("seeds", {}))
              for k in rows}
    d_seeded = {k: _abs_err(ra[k]["seats"], seeded[k])
                - _abs_err(rb[k]["seats"], seeded[k]) for k in rows}
    d_est = {k: _abs_err(ra[k]["seats"],
                         set(ra[k]["seats"]) - seeded[k])
             - _abs_err(rb[k]["seats"], set(rb[k]["seats"]) - seeded[k])
             for k in rows}

    def arrival_err(r):
        g = r.get("arrival_group") or {}
        v = g.get("seats_err")
        return abs(v) if isinstance(v, (int, float)) else float("nan")
    d_arr = {k: arrival_err(ra[k]) - arrival_err(rb[k]) for k in rows}

    headline = paired(d_seat, "Δ seat_abs_err_coherent per city-year")
    est = paired(d_est, "Δ Σ|actual−median| over non-seeded columns")
    res["predictions"]["P5"] = {
        "verdict": (VOID if not paired_valid else
                    PASS if headline["contains_zero"] and est["contains_zero"]
                    else FAIL),
        "headline": headline,
        "established_columns": est,
        "seeded_columns": paired(d_seeded, "Δ Σ|actual−median| over the "
                                           "spec's `seeds` columns"),
        "arrival_group": paired(d_arr, "Δ |arrival_group.seats_err|"),
        "directional_arrival_and_seeded_improve": {
            "seeded_total": float(sum(v for v in d_seeded.values() if v == v)),
            "arrival_total": float(sum(v for v in d_arr.values() if v == v)),
            "verdict": (VOID if not paired_valid else
                        PASS if (sum(v for v in d_seeded.values() if v == v)
                                 + sum(v for v in d_arr.values() if v == v)) < 0
                        else FAIL)},
        "READING": "'changes by less than its own paired bootstrap interval' "
                   "is read as: the 95% city-cluster percentile interval of the "
                   "mean paired change contains zero, for the headline AND for "
                   "the established columns. Per-column errors use the MEDIAN "
                   "seat (the only per-party model seat a row stores); the "
                   "headline is the coherent statistic. 'Established' = every "
                   "column not in either side's `seeds`, so an unseeded arrival "
                   "counts as established. The directional claim is the sum "
                   "of the seeded and arrival-group changes being negative."}

    # --- P6 -------------------------------------------------------------------
    called_b = sum(rb[k]["wards"]["called"] for k in rows)
    called_a = sum(ra[k]["wards"]["called"] for k in rows)
    matched_a = sum(ra[k]["wards"]["wards_matched"] for k in rows)
    ct = [k for k in rows if k[0] == "capetown"]
    ct_abs = sum(abs(ra[k]["wards"]["called"] - rb[k]["wards"]["called"])
                 for k in ct)
    ct_net = sum(ra[k]["wards"]["called"] - rb[k]["wards"]["called"]
                 for k in ct)

    def brier(rs):
        v = [rs[k]["wards"]["brier_multicategory"] for k in rows]
        return float(np.mean(v))
    in_band = P6_BAND[0] <= called_a <= P6_BAND[1]
    res["predictions"]["P6"] = {
        "verdict": (VOID if not paired_valid else
                    PASS if in_band and ct_abs <= P6_CAPETOWN_MAX else FAIL),
        "called_before": called_b, "called_after": called_a,
        "matched_after": matched_a, "band": P6_BAND,
        "capetown_abs_change": ct_abs, "capetown_net_change": ct_net,
        "brier_mean_before": brier(rb), "brier_mean_after": brier(ra),
        "READING": "the band is absolute, as typed in the prereg against an "
                   "older run; `called_before` is printed so a reader can see "
                   "whether the band is still centred on the before-run. Cape "
                   "Town 'at most one ward in total' is scored on the sum of "
                   "ABSOLUTE per-city-year changes (a gain and a loss are two "
                   "changes); the net is printed beside it."}

    # --- P7 -------------------------------------------------------------------
    dose = {k: diff[k]["dose"] for k in rows if k in diff and "dose" in diff[k]}
    dosed = {k: v for k, v in dose.items() if v > 0}
    undosed = [k for k, v in dose.items() if v == 0]
    top = max(dosed, key=dosed.get) if dosed else None
    top_move = abs(d_crps[top]) if top else float("nan")
    undosed_max = max((abs(d_crps[k]) for k in undosed), default=0.0)
    rho = _spearman([dosed[k] for k in dosed],
                    [abs(d_crps[k]) for k in dosed]) if len(dosed) > 2 else None
    res["predictions"]["P7"] = {
        "verdict": (VOID if not paired_valid else
                    NOT_TESTED if not dosed else
                    FAIL if undosed_max >= top_move else PASS),
        "dosed": {f"{s} {y}": {"dose": dosed[(s, y)],
                                "d_crps": d_crps[(s, y)]} for s, y in dosed},
        "undosed_with_band_dose": {
            f"{s} {y}": {"band_dose": diff[(s, y)]["band_dose"],
                         "d_crps": d_crps[(s, y)]}
            for s, y in undosed if diff[(s, y)].get("band_dose", 0) > 0},
        "undosed_nonzero": {f"{s} {y}": d_crps[(s, y)] for s, y in undosed
                            if d_crps[(s, y)] != 0},
        "top_dose_row": f"{top[0]} {top[1]}" if top else None,
        "top_dose_abs_d_crps": top_move, "undosed_max_abs_d_crps": undosed_max,
        "spearman_dosed": rho,
        "by_cycle_mean_abs_d_crps": {
            y: float(np.mean([abs(d_crps[k]) for k in rows if k[1] == y]))
            for y in sorted({k[1] for k in rows})},
        "READING": "P7's premise ('C3 moves all 27 specs') is false: only C1 "
                   "shipped. Scored on the dose that exists. Falsified if a "
                   "spec whose `registered` did not move (dose 0) shows a "
                   "|ΔCRPS| at least as large as the highest-dose spec's. "
                   "'Largest at 2011, smallest at 2021' was a C3 claim and is "
                   "reported by cycle, not scored. The verdict uses the "
                   "prereg's `registered` dose only; specs with zero "
                   "registered dose but a moved turnout band are listed in "
                   "`undosed_with_band_dose`, because a large |ΔCRPS| there "
                   "would read as P7 falsified for a reason the registered "
                   "dose cannot see."}

    # --- the window -----------------------------------------------------------
    cyc = {}
    for y in sorted({k[1] for k in rows}):
        cyc[y] = float(sum(d_crps[k] for k in rows if k[1] == y))
    signs = {int(np.sign(v)) for v in cyc.values() if v != 0}
    res["window"]["crps_by_cycle"] = {
        "change": cyc,
        "verdict": (VOID if not paired_valid else
                    FAIL if any(v > 0 for v in cyc.values()) or len(signs) > 1
                    else PASS),
        "READING": "the summed paired seat CRPS change per target cycle; lower "
                   "is better. Fails on a net loss in any cycle or a sign that "
                   "differs between cycles. A cycle with no change has no "
                   "sign."}
    cov_b, cov_a = _pooled_coverage(rb, rows), _pooled_coverage(ra, rows)
    pit_b, pit_a = _pooled_pit(rb, rows), _pooled_pit(ra, rows)
    away = {lvl: abs(cov_a[lvl] - lvl) > abs(cov_b[lvl] - lvl) + 1e-12
            for lvl in cov_b}
    pit_away = abs(pit_a - 0.5) > abs(pit_b - 0.5) + 1e-12
    res["window"]["calibration"] = {
        "population": COVERAGE_POPULATION,
        "coverage_before": cov_b, "coverage_after": cov_a,
        "pit_mean_before": pit_b, "pit_mean_after": pit_a,
        "moved_away": away, "pit_moved_away": pit_away,
        "verdict": (VOID if not paired_valid else
                    FAIL if any(away.values()) or pit_away else PASS),
        "READING": "pooled over every row: coverage = Σinside/Σcounted at each "
                   "level; PIT = mean of every column's PIT. 'Moves away from "
                   "nominal' = the after distance from nominal exceeds the "
                   "before distance, by any amount. No noise allowance: the "
                   "prereg set none."}
    d_pr = d(lambda r: r["pr_mae"])
    d_wd = d(lambda r: r["ward_mae"])
    seats_better = sum(d_seat.values()) < 0
    votes_better = (sum(d_pr.values()) < 0) or (sum(d_wd.values()) < 0)
    res["window"]["seats_without_votes"] = {
        "d_seat_total": float(sum(d_seat.values())),
        "d_pr_mae_total": float(sum(d_pr.values())),
        "d_ward_mae_total": float(sum(d_wd.values())),
        "verdict": (VOID if not paired_valid else
                    FAIL if seats_better and not votes_better else PASS),
        "READING": "fails when the summed coherent seat error falls while "
                   "neither the summed PR nor the summed ward vote MAE falls."}
    res["window"]["p1"] = res["predictions"]["P1"]["verdict"]
    res["window"]["p7"] = res["predictions"]["P7"]["verdict"]

    # --- the merger prereg --------------------------------------------------
    res["mergers_prereg"] = {
        "change_1_independents": NOT_TESTED + ": not in the freeze.",
        "change_2_mergers": "scored in MODEL-LOG §1.275 on run_model; no "
                            "declared merger predates a held election, so no "
                            "backtest row can test it. Its post-emit checks are "
                            "F8's, not F9's.",
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
        out[f"{k[0]} {k[1]}"] = {n: v / tot for n, v in reg.items()} if tot else {}
    return out


def _pooled_coverage(rows_, keys):
    inside, counted = {}, {}
    for k in keys:
        for c in rows_[k]["calibration"][COVERAGE_POPULATION]["coverage"]:
            lvl = float(c["level"])
            inside[lvl] = inside.get(lvl, 0) + c["inside"]
            counted[lvl] = counted.get(lvl, 0) + c["counted"]
    return {lvl: inside[lvl] / counted[lvl] for lvl in inside if counted[lvl]}


def _pooled_pit(rows_, keys):
    v = [p for k in keys
         for p in rows_[k]["calibration"][COVERAGE_POPULATION]["pit"]
         if p is not None and p == p]
    return float(np.mean(v)) if v else float("nan")


def _spearman(x, y):
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    if np.std(rx) == 0 or np.std(ry) == 0:
        return None
    return float(np.corrcoef(rx, ry)[0, 1])


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def report(res: dict) -> str:
    L = ["F9 scoring", "", "inputs:", json.dumps(res["inputs"], indent=1), ""]
    L.append(f"placebo: {len(res['placebo']['rows'])} key-only rows, "
             f"holds={res['placebo']['holds']}, broken={res['placebo']['broken']}")
    for name, p in res["predictions"].items():
        L.append(f"\n{name}: {p['verdict']}")
        for k, v in p.items():
            if k != "verdict":
                L.append(f"  {k}: {json.dumps(v, default=str)[:600]}")
    L.append("\nwindow:")
    for name, w in res["window"].items():
        L.append(f"  {name}: {json.dumps(w, default=str)[:600]}")
    L.append("\nmergers prereg: " + json.dumps(res["mergers_prereg"], indent=1))
    return "\n".join(L)


# --------------------------------------------------------------------------
# Self-test: constructed inputs, each verdict made to flip
# --------------------------------------------------------------------------

def _fixture():
    """Two cities x two cycles, one C1-shaped spec. Constructed, not lifted."""
    def spec(pools_, cats, shares, seeds=()):
        return {"categories": cats, "pool_shares_at_target": shares,
                "pools": pools_, "seeds": {s: {} for s in seeds},
                "artefact_key": {"pools_sha": "x"}}

    def pool(reg, members):
        return {"registered": reg, "turnout": [0.3, 0.5, 0.7],
                "members": members}
    full = {"A": pool(900.0, {"P": 0.9, "Q": 0.5}),
            "B": pool(100.0, {"P": 0.1, "Q": 0.5})}
    cats, sh = ["A", "B"], [0.9, 0.1]
    before = {("c1", "2016"): spec({"A": pool(1000.0, {"P": 1.0, "Q": 1.0})},
                                   cats, sh),
              ("c1", "2021"): spec(full, cats, sh),
              ("c2", "2016"): spec(full, cats, sh, seeds=("S",)),
              ("c2", "2021"): spec(full, cats, sh)}
    after = {k: json.loads(json.dumps(v)) for k, v in before.items()}
    after[("c1", "2016")] = spec(full, cats, sh)
    for v in after.values():
        v["artefact_key"] = {"pools_sha": "y"}
        v["mergers"] = []          # F5's field: empty is not a change

    def row(slug, year, seat_err, crps, called, cov_in=8):
        cov = [{"level": lvl, "inside": cov_in if lvl == 0.8 else 5,
                "counted": 10, "empirical": 0} for lvl in (0.5, 0.8, 0.9)]
        return {"slug": slug, "year": year, "seat_abs_err": seat_err,
                "seat_abs_err_coherent": seat_err, "crps": crps,
                "pr_mae": 1.0, "ward_mae": 1.0,
                "votes": [["P", 0, 0, 0.6, 0, 0, 0], ["Q", 0, 0, 0.4, 0, 0, 0]],
                "seats": {"P": [10, 9], "Q": [5, 6], "S": [1, 0]},
                "wards": {"n_wards": 10, "wards_matched": 10,
                          "called": called, "hit_rate": 1.0,
                          "brier_multicategory": 0.05},
                "calibration": {"reference": {"coverage": cov,
                                              "pit": [0.5, 0.5]}},
                "arrival_group": {"seats_err": 1}}
    man = {"seed": 1, "draws": 10, "seed_by_row": "x", "git_commit": "b"}
    rb = {("c1", "2016"): row("c1", "2016", 10, 5.0, 530),
          ("c1", "2021"): row("c1", "2021", 10, 5.0, 530),
          ("c2", "2016"): row("c2", "2016", 10, 5.0, 530),
          ("c2", "2021"): row("c2", "2021", 10, 5.0, 530)}
    ra = json.loads(json.dumps({"|".join(k): v for k, v in rb.items()}))
    ra = {tuple(k.split("|")): v for k, v in ra.items()}
    ra[("c1", "2016")]["crps"] = 4.0            # the dosed spec improves
    return before, after, (man, rb), (dict(man, git_commit="a"), ra)


def self_test() -> None:
    import copy
    b, a, hb, ha = _fixture()
    r = score(b, a, hb, ha)
    P = r["predictions"]
    assert r["placebo"]["holds"], r["placebo"]
    assert P["P1"]["verdict"] == PASS and P["P1"]["violations_before"] == 1
    assert P["P2"]["verdict"] == P["P3"]["verdict"] == NOT_TESTED
    assert P["P7"]["verdict"] == PASS, P["P7"]
    assert r["window"]["crps_by_cycle"]["verdict"] == PASS
    assert r["window"]["calibration"]["verdict"] == PASS

    # P1 sees a dropped pool in the after specs.
    a2 = copy.deepcopy(a); a2[("c2", "2021")]["pools"].pop("B")
    assert score(b, a2, hb, ha)["predictions"]["P1"]["verdict"] == FAIL

    # The placebo trips when a key-only row's score moves, and voids P5-P7.
    ha2 = copy.deepcopy(ha); ha2[1][("c2", "2021")]["crps"] = 4.5
    r2 = score(b, a, hb, ha2)
    assert not r2["placebo"]["holds"]
    assert {r2["predictions"][p]["verdict"] for p in ("P5", "P6", "P7")} == {VOID}
    assert r2["window"]["crps_by_cycle"]["verdict"] == VOID

    # The pair is refused when the seeds differ.
    ha3 = (dict(ha[0], seed=2), ha[1])
    assert not score(b, a, hb, ha3)["inputs"]["paired_valid"]

    # P7 falsified: an undosed spec moves as much as the dosed one. Its spec
    # must differ beyond the key, or it would be placebo and void everything.
    a4 = copy.deepcopy(a); a4[("c2", "2021")]["turnout_limits"] = {"x": 1}
    ha4 = copy.deepcopy(ha); ha4[1][("c2", "2021")]["crps"] = 4.0
    assert score(b, a4, hb, ha4)["predictions"]["P7"]["verdict"] == FAIL

    # A net CRPS loss in one cycle fails the window.
    ha5 = copy.deepcopy(ha); ha5[1][("c1", "2016")]["crps"] = 6.0
    assert score(b, a, hb, ha5)["window"]["crps_by_cycle"]["verdict"] == FAIL

    # Coverage moving away from nominal fails; toward it does not.
    ha6 = copy.deepcopy(ha)
    for k in ha6[1]:
        for c in ha6[1][k]["calibration"]["reference"]["coverage"]:
            if c["level"] == 0.8:
                c["inside"] = 6
    ha6[1][("c1", "2016")]["crps"] = 4.0
    ha6b = copy.deepcopy(hb)
    r6 = score(b, a4, ha6b, _with_placebo(ha6, ha6b, a4, b))
    assert r6["window"]["calibration"]["verdict"] == FAIL, r6["window"]

    # P6: Cape Town moving two wards fails.
    b7, a7 = _rename(b, "c1", "capetown"), _rename(a, "c1", "capetown")
    hb7, ha7 = _rename_h(hb, "c1", "capetown"), _rename_h(ha, "c1", "capetown")
    ha7[1][("capetown", "2016")]["wards"]["called"] = 532
    assert score(b7, a7, hb7, ha7)["predictions"]["P6"]["verdict"] == FAIL
    print("self-test: every verdict flipped as constructed")


def _with_placebo(h_after, h_before, a, b):
    """Keep key-only rows identical to before, so a calibration change on
    them does not trip the placebo instead of the calibration test."""
    import copy
    out = copy.deepcopy(h_after)
    diff = spec_diff(b, a)
    for k, d_ in diff.items():
        if d_.get("key_only"):
            out[1][k] = copy.deepcopy(h_before[1][k])
    return out


def _rename(specs, old, new):
    return {((new if s == old else s), y): v for (s, y), v in specs.items()}


def _rename_h(h, old, new):
    import copy
    m, rows_ = h
    return (m, {((new if s == old else s), y): copy.deepcopy(v)
                for (s, y), v in rows_.items()})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--before-specs", type=Path)
    ap.add_argument("--after-specs", type=Path)
    ap.add_argument("--before-history", type=Path)
    ap.add_argument("--after-history", type=Path)
    ap.add_argument("--json", type=Path)
    a = ap.parse_args(argv)
    if a.self_test:
        self_test()
        return 0
    res = score(load_specs(a.before_specs), load_specs(a.after_specs),
                load_rows(a.before_history), load_rows(a.after_history))
    print(report(res))
    if a.json:
        a.json.write_text(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
