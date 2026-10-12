"""The width record of the universal draw: one curve over every party-election.

    .venv/bin/python src/width_record.py --out DIR          # build into DIR
    .venv/bin/python src/width_record.py --emit             # re-emit window only
    .venv/bin/python src/width_record.py --emit --set level_shrink=0   # US arm

Design: ``audits/2026-10-11-model-round/step1/1j-universal-draw-design-v4.md``
with its addendum, option L1 (owner, 2026-10-12), on the machinery of v3, v2
and v1 that v4 inherits; reviews ``step2/2-review-1j*.md`` and
``2-recheck-1j-v*.md``. It writes ``data/processed/width_record.json``, which
``montecarlo.read_width_record`` reads and ``make_drawer`` refuses when it is
missing, stale, or built for different centres.

WHAT IT ESTIMATES, per target year, from strictly EARLIER backtest cycles only
(2016 from 2011; 2021 from 2011-2016; 2026 from 2011-2021):

    r_i ~ Normal( m(s_i) − σ_i²/2 , σ_i² ),  σ_i² = σ(s_i)² + δ²·new_i
    σ(s) = a + (b − a) / (1 + exp(k·(log s − log s_mid)))
    m(s) = c1·L + c2·L²,  L = min(log(s / 20%), 0)

by weighted maximum likelihood, one unit of weight per party-cycle. ``r_i`` is
the realised list share against the party's ``pool_spec`` centre (the centre the
draw conserves, ``montecarlo.pool_spec_centres``), RELATIVE TO THE LARGE BLOCK
(parties with centre ≥ 20%) for a party below 20%, and within the block for a
member of a block of two or more. ``new_i`` is 1 for a party with no result at
the previous local election in the city. Under L1 the location ``m(s)`` is
fitted so that the level error is not read as spread, and NOT carried in the
draw; it is recorded for the centre-correction arm (prereg §3.3).

Then: the shared share of variance by size group (one-way city-year
decomposition of standardised residuals about zero, established parties, under
1% and 1-20%), and the location fixed point of design v2 §2.3, which subtracts
the draw's own model-internal location from the residuals and re-fits.

ESTIMATION, NOT TUNING (CLAUDE.md §4). The target is the realised dispersion of
the vote about a centre that does not depend on any width. No coverage, PIT,
seat width or realised-over-predicted ratio enters. The fixed point reads no
outcome: it is the draw's own location.

2011 HAS NO EARLIER CYCLE. Its width is design 1b v3's fallback: the forward θ
residual of target 2006 by population (with and without θ history), labelled
untestable wherever it is used (v3 addendum, call 21).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import cityconfig            # noqa: E402
import montecarlo as M       # noqa: E402

DATA = REPO / "data/raw/elections"

# Which backtest cycles each target's record is fitted on: strictly earlier
# ones (design v4 §1). 2011 has none and takes the fallback.
FORWARD = {"2016": ("2011",), "2021": ("2011", "2016"),
           "2026": ("2011", "2016", "2021")}
FALLBACK_TARGETS = ("2011",)
# The θ forward residual the 2011 fallback is read from (design 1b v3).
FALLBACK_RESIDUAL_YEAR = "2006"

# A target whose record holds fewer established party-elections than this
# refuses (design v1 §2.6; v3 addendum call 20). JUDGEMENT-CALLS §A57.
MIN_ESTABLISHED = 20
# The location fixed point (design v2 §2.3; v3 addendum call 15): at most two
# iterations, stopping when no width at the checked sizes moves by more than
# the tolerance; each iteration draws `FIXED_POINT_DRAWS` at every earlier
# city-year. JUDGEMENT-CALLS §A57.
FIXED_POINT_ITERS = 2
FIXED_POINT_TOL = 0.01
FIXED_POINT_DRAWS = 2000
FIXED_POINT_SIZES = (0.0005, 0.002, 0.005, 0.02, 0.1, 0.25)
# Diagnostics only (design v4 §1.3): the band roots printed beside the curve,
# each band needing this many party-elections. No band sets a width.
DIAGNOSTIC_BANDS = ((0.01, 0.05, "1-5%"), (0.003, 0.01, "0.3-1%"),
                    (0.001, 0.003, "0.1-0.3%"), (0.0, 0.001, "<0.1%"))
DIAGNOSTIC_MIN_EFF = 8


def record_cities() -> list[str]:
    """The metros the record is fitted on: ``compare_history.CITIES``."""
    import compare_history as CH
    return list(CH.CITIES)


def record_specs() -> list[tuple[str, str, str]]:
    """``(city, year, path under data/processed)`` of every pool spec the
    record reads: each city at each cycle some target's record is fitted on.
    ``montecarlo.width_record_key`` hashes these, so a re-emit that changes
    one marks the record stale with no code change (step-6 review, item 7)."""
    years = sorted({y for ys in FORWARD.values() for y in ys}, key=int)
    out = []
    for slug in record_cities():
        city = cityconfig.load(slug)
        rel = Path(city.processed).relative_to("data/processed")
        for y in years:
            out.append((slug, y, str(rel / f"pools_{y}.json")))
    return out


# --------------------------------------------------------------------------
# the residual rows
# --------------------------------------------------------------------------

def residual_rows(cases: list[dict]) -> list[dict]:
    """Every party-election's residual in the record's frame (design v1 §1.1).

    ``cases`` holds one dict per city-year: ``city``, ``year``, ``centres``
    (each pooled party's ``pool_spec`` centre, ``montecarlo.pool_spec_centres``),
    ``actual`` (realised list shares) and ``new`` (parties with no result at
    the previous local election there).

    A party below ``WIDTH_BLOCK`` gets ``r = log(act/s) − log(A/P)``, where A
    and P are the realised and centre shares of the block (parties at or above
    the line); a block member gets ``log((act/A)/(s/P))`` when the block has
    two or more members (a single-member block's within-block residual is
    identically 0 and is skipped; v2 N5). A zero result has no log residual and
    is counted, not used (v2 rejected-claims table, N4).
    """
    rows = []
    for case in cases:
        s_all, act, new = case["centres"], case["actual"], set(case["new"])
        block = [p for p, s in s_all.items() if s >= M.WIDTH_BLOCK]
        A = sum(act.get(p, 0.0) for p in block)
        P = sum(s_all[p] for p in block)
        if not block or A <= 0 or P <= 0:
            continue
        lb = math.log(A / P)
        for p, s in s_all.items():
            if p == "ENTRANT" or s <= 0:
                continue
            a = float(act.get(p, 0.0))
            row = {"city": case["city"], "year": case["year"], "party": p,
                   "s": float(s), "act": a, "new": p in new,
                   "block": s >= M.WIDTH_BLOCK, "r": None}
            if a > 0:
                if s < M.WIDTH_BLOCK or p in new:
                    row["r"] = math.log(a / s) - lb
                elif len(block) >= 2:
                    row["r"] = math.log((a / A) / (s / P))
            rows.append(row)
    return rows


def fit_records(rows: list[dict]) -> list[dict]:
    """The rows the joint fit uses: every row with a residual, except an
    established block member of a single-member block."""
    return [r for r in rows if r["r"] is not None]


def _weights(recs: list[dict]) -> np.ndarray:
    """One unit of weight per party-cycle (design v4 §1; v3 §0.1)."""
    k = Counter(f"{r['party']}|{r['year']}" for r in recs)
    return np.array([1.0 / k[f"{r['party']}|{r['year']}"] for r in recs])


# --------------------------------------------------------------------------
# the joint fit
# --------------------------------------------------------------------------

def _curve(p) -> dict:
    return {"a": float(p[0]), "b": float(p[1]), "log_mid": float(p[2]),
            "k": float(p[3])}


def joint_nll(p, s, r, new, w) -> float:
    """The weighted negative log likelihood of design v4 §1 at parameters
    ``p = [a, b, log s_mid, k, δ, c1, c2]``; 1e12 outside the admissible box
    (a > 0.005, a < b ≤ 3, 0.2 < k ≤ 20, δ ≥ 0)."""
    a, b, lm, kk, d = p[:5]
    if a <= 0.005 or b <= a or kk <= 0.2 or kk > 20 or d < 0 or b > 3:
        return 1e12
    curve = _curve(p)
    sig = M.width_sigma(curve, s)
    m = M.width_location({"c1": p[5], "c2": p[6]}, s, clamp=False)
    sg2 = sig * sig + d * d * new
    mu = m - sg2 / 2.0
    return float(np.sum(w * (0.5 * np.log(sg2) + (r - mu) ** 2 / (2.0 * sg2))))


def fit_joint(rows: list[dict], delta: dict | None = None) -> dict:
    """The weighted ML fit of width curve, newness δ and location m(s).

    ``delta`` maps ``(city, year, party)`` to the model-internal location shift
    of the fixed point (0 when absent). Deterministic: a coarse grid start and
    a coordinate search with step halving, the estimator the design measured
    (v4, ``uni4/v4.py``). Refuses fewer than ``MIN_ESTABLISHED`` established
    party-elections.
    """
    delta = delta or {}
    recs = fit_records(rows)
    est = {f"{r['party']}|{r['year']}" for r in recs if not r["new"]}
    if len(est) < MIN_ESTABLISHED:
        raise SystemExit(f"the width record holds {len(est)} established "
                         f"party-elections, under MIN_ESTABLISHED = "
                         f"{MIN_ESTABLISHED}: no curve is fitted on so little")
    s = np.array([r["s"] for r in recs])
    new = np.array([1.0 if r["new"] else 0.0 for r in recs])
    r_ = np.array([r["r"] - delta.get((r["city"], r["year"], r["party"]), 0.0)
                   for r in recs])
    w = _weights(recs)
    best = None
    for a in (0.03, 0.06):
        for b in (0.8, 1.0):
            for lm in np.log([0.03, 0.08, 0.15]):
                for kk in (1.5, 3.0):
                    for d in (0.0, 0.6):
                        for c1 in (-0.2, 0.0, 0.2):
                            p = [a, b, float(lm), kk, d, c1, 0.0]
                            v = joint_nll(p, s, r_, new, w)
                            if best is None or v < best[0]:
                                best = (v, p)
    p = list(best[1])
    step = [0.01, 0.05, 0.2, 0.3, 0.1, 0.05, 0.02]
    for _ in range(800):
        improved = False
        for j in range(7):
            for dd in (step[j], -step[j]):
                q = list(p)
                q[j] += dd
                v = joint_nll(q, s, r_, new, w)
                if v < best[0] - 1e-10:
                    best, p, improved = (v, q), q, True
        if not improved:
            step = [x / 2 for x in step]
            if max(step) < 1e-5:
                break
    return {"curve": _curve(p), "delta": float(p[4]),
            "location": {"c1": float(p[5]), "c2": float(p[6])},
            "nll": float(best[0]), "n": len(recs),
            "party_elections": len({f"{r['party']}|{r['year']}" for r in recs}),
            "established_party_elections": len(est)}


def shared_shares(rows: list[dict], fit: dict, delta: dict | None = None
                  ) -> dict:
    """ρ by size group (design v2 §3.1): the one-way city-year share of the
    variance of standardised residuals ``u = (r − Δ − m(s) + σ²/2)/σ`` of
    ESTABLISHED parties below the block line, about zero, for parties under
    ``RHO_GROUP_EDGE`` and for the rest. A group with fewer than two
    city-years or no within-group degrees of freedom takes 0."""
    delta = delta or {}
    est = [r for r in fit_records(rows)
           if not r["new"] and r["s"] < M.WIDTH_BLOCK]

    def u(r):
        sg = M.width_sigma(fit["curve"], r["s"])
        return (r["r"] - delta.get((r["city"], r["year"], r["party"]), 0.0)
                - M.width_location(fit["location"], r["s"], clamp=False)
                + sg * sg / 2.0) / sg

    def oneway(sel):
        g = defaultdict(list)
        for r in est:
            if sel(r):
                g[(r["city"], r["year"])].append(u(r))
        within = [x - np.mean(xs) for xs in g.values() for x in xs]
        dfw = len(within) - len(g)
        if len(g) < 2 or dfw <= 0:
            return 0.0
        msw = float(np.sum(np.square(within)) / dfw)
        means = np.array([np.mean(x) for x in g.values()])
        ns = np.array([len(x) for x in g.values()])
        sb2 = max(float(np.mean(means ** 2 - msw / ns)), 0.0)
        return sb2 / (sb2 + msw) if sb2 + msw > 0 else 0.0

    return {"lo": oneway(lambda r: r["s"] < M.RHO_GROUP_EDGE),
            "hi": oneway(lambda r: r["s"] >= M.RHO_GROUP_EDGE)}


def band_diagnostics(rows: list[dict], delta: dict | None = None) -> list:
    """The offset-aware band roots of design v2 §2.1, PRINTED beside the curve
    and never used to set a width (design v4 §1.3)."""
    delta = delta or {}
    out = []
    est = [r for r in fit_records(rows) if not r["new"]
           and r["s"] < M.WIDTH_BLOCK]
    for lo, hi, label in DIAGNOSTIC_BANDS:
        b = [r for r in est if lo <= r["s"] < hi]
        ne = len({f"{r['party']}|{r['year']}" for r in b})
        if ne < DIAGNOSTIC_MIN_EFF:
            out.append({"band": label, "n": len(b), "party_elections": ne,
                        "width": None, "rule": "thin"})
            continue
        x = np.array([r["r"] - delta.get((r["city"], r["year"], r["party"]),
                                         0.0) for r in b])
        w = _weights(b)
        mu = float(np.sum(w * x) / w.sum())
        m2 = float(np.sum(w * x * x) / w.sum())
        disc = (1 - mu) ** 2 - m2
        if disc >= 0:
            width, rule = math.sqrt(2 * ((1 - mu) - math.sqrt(disc))), "root"
        else:
            width, rule = math.sqrt(max(m2 - mu * mu, 0.0)), "no root"
        out.append({"band": label, "n": len(b), "party_elections": ne,
                    "width": width, "rule": rule, "mean": mu})
    return out


# --------------------------------------------------------------------------
# the location fixed point (design v2 §2.3): the draw's own location
# --------------------------------------------------------------------------

def location_shift(inputs_by_cy: dict, record: dict,
                   draws: int | None = None) -> dict:
    """``Δ`` per (city, year, party): the universal draw's own mean of
    ``log(s_i/c_i) − log(S_B/C_B)`` at each earlier city-year under the trial
    ``record``, plus ``σ_total²/2`` (so 0 when the draw's location is the
    estimator's assumed −σ²/2). Model-internal: it reads no outcome."""
    draws = FIXED_POINT_DRAWS if draws is None else int(draws)
    out = {}
    for (city, year), inp in inputs_by_cy.items():
        sc = dict(inp.scenario)
        sc["_width"] = dict(record, kind="fit")
        sc["_strength_applied"] = []
        sc["draw_law"] = "universal"
        lot = M.lot_identity(city, year, f"width-record-{sc.get('seed')}")
        with contextlib.redirect_stdout(io.StringIO()):
            drawer = M.make_drawer(sc, inp.base_city_d, inp.centres, inp.index,
                                   M.DrawStreams(lot, draws))
            for d in range(draws):
                drawer(d)
        names = list(drawer.u_names)
        c = np.asarray(drawer.u_centres)
        S = np.asarray(drawer.conserve_record)
        S = S / S.sum(axis=1, keepdims=True)
        B = c >= M.WIDTH_BLOCK
        if not B.any():
            continue
        lb = np.log(S[:, B].sum(axis=1) / c[B].sum())
        for k, p in enumerate(names):
            loc = float(np.mean(np.log(np.maximum(S[:, k], 1e-300) / c[k]) - lb))
            tot = drawer.widths[p]["total"]
            out[(city, year, p)] = loc + tot * tot / 2.0
    return out


def fit_target(rows: list[dict], inputs_by_cy: dict | None,
               iters: int | None = None) -> dict:
    """The record of one target: the joint fit, iterated with the location
    fixed point at most ``iters`` times (stop below ``FIXED_POINT_TOL``), then
    the shared shares and the band diagnostics. ``inputs_by_cy`` None skips
    the fixed point (unit tests on constructed rows)."""
    iters = FIXED_POINT_ITERS if iters is None else int(iters)
    fit = fit_joint(rows)
    fit["rho"] = shared_shares(rows, fit)
    delta: dict = {}
    history = []
    for it in range(iters if inputs_by_cy else 0):
        delta = location_shift(inputs_by_cy, dict(fit, kind="fit"))
        fit2 = fit_joint(rows, delta)
        fit2["rho"] = shared_shares(rows, fit2, delta)
        change = max(abs(M.width_sigma(fit2["curve"], x)
                         - M.width_sigma(fit["curve"], x))
                     for x in FIXED_POINT_SIZES)
        history.append({"iteration": it + 1, "max_width_change": change})
        fit = fit2
        if change < FIXED_POINT_TOL:
            break
    fit.update(kind="fit", fixed_point=history,
               bands=band_diagnostics(rows, delta),
               delta_shift={f"{c}|{y}|{p}": v for (c, y, p), v in delta.items()},
               zero_results=sum(1 for r in rows if r["act"] <= 0))
    return fit


# --------------------------------------------------------------------------
# 2011: the fallback
# --------------------------------------------------------------------------

def fallback_record() -> dict:
    """The 2011 width (design 1b v3 §3.3; v3 addendum call 21): the RMS of
    the forward θ residual at target ``FALLBACK_RESIDUAL_YEAR`` (2006), by
    population, from ``theta_residual.residuals`` (one definition of the
    residual). Untestable; every report labels it so."""
    import theta_residual as T
    res = [r for r in T.residuals() if r[4] == FALLBACK_RESIDUAL_YEAR]
    out = {}
    for label, flag in (("with_history", True), ("without", False)):
        x = np.array([r[1] for r in res if bool(r[6]) == flag])
        if x.size == 0:
            raise SystemExit(f"no θ residual at {FALLBACK_RESIDUAL_YEAR} for "
                             f"the {label} population: the 2011 fallback "
                             f"cannot be read")
        out[label] = float(np.sqrt(np.mean(x * x)))
        out[f"n_{label}"] = int(x.size)
    return {"kind": "fallback", "fallback": out, "untestable": True}


# --------------------------------------------------------------------------
# the record, through the model's own estimation
# --------------------------------------------------------------------------

def _scenario(city: str, year: str, sets: list[str]):
    c = cityconfig.use(city)
    target = cityconfig.use_target(year)
    M.apply_city(c)
    sc = M.load_scenario(argparse.Namespace(
        config=None, set=list(sets), draws=FIXED_POINT_DRAWS,
        seed=M.DEFAULTS["seed"], city=city, target=year))
    return target, sc


def drawer_inputs(city: str, year: str, sets: list[str]):
    """``run_model(stop_after="drawer_inputs")`` at one backtest city-year:
    the centres the model itself builds, with no draw."""
    target, sc = _scenario(city, year, sets)
    with contextlib.redirect_stdout(io.StringIO()):
        return M.run_model(target, sc, DATA, verbose=False,
                           stop_after="drawer_inputs")


def case_for(inp, city: str, year: str) -> dict:
    """One city-year's rows input: ``pool_spec`` centres, realised list
    shares (``compare_history.actual_shares``), and the new parties."""
    import compare_history as CH
    with contextlib.redirect_stdout(io.StringIO()):
        spec = M.pool_spec(inp.scenario, inp.centres, inp.index)
    centres = M.pool_spec_centres(spec)
    actual, _ = CH.actual_shares(inp.target, DATA)
    return {"city": city, "year": year, "centres": centres, "actual": actual,
            "new": list(inp.scenario.get("_new_parties") or [])}


def build(sets: list[str], cities: list[str] | None = None,
          targets=("2011", "2016", "2021", "2026"),
          fixed_point: bool = True) -> dict:
    """The record for every target, in the variant ``sets`` names."""
    cities = list(cities or record_cities())
    need = sorted({y for t in targets if t in FORWARD for y in FORWARD[t]})
    inputs = {}
    cases = []
    for city in cities:
        for year in need:
            inp = drawer_inputs(city, year, sets)
            inputs[(city, year)] = inp
            cases.append(case_for(inp, city, year))
            print(f"  {city} {year}: {len(cases[-1]['centres'])} pooled parties",
                  flush=True)
    rows = residual_rows(cases)
    out = {}
    for t in targets:
        if t in FALLBACK_TARGETS:
            out[t] = fallback_record()
            continue
        sub = [r for r in rows if r["year"] in FORWARD[t]]
        sub_in = {k: v for k, v in inputs.items() if k[1] in FORWARD[t]}
        out[t] = dict(fit_target(sub, sub_in if fixed_point else None),
                      from_cycles=list(FORWARD[t]))
        f = out[t]
        print(f"  target {t}: b {f['curve']['b']:.3f} mid "
              f"{math.exp(f['curve']['log_mid']):.2%} δ {f['delta']:.3f} "
              f"c1 {f['location']['c1']:+.3f} c2 {f['location']['c2']:+.3f} "
              f"ρ {f['rho']['lo']:.2f}/{f['rho']['hi']:.2f}", flush=True)
    variant_sc = _scenario(cities[0], "2021", sets)[1]
    return {"variant": M.width_record_variant(variant_sc), "targets": out}


def write(record: dict, path: Path) -> None:
    """Merge one variant into the file at ``path`` under the live key; a file
    under another key is replaced, never merged into. The key's inputs are
    the specs the build READ, which are always the repository's
    ``data/processed`` (``run_model``'s default), whatever ``path`` is."""
    key = M.width_record_key()
    blob = {}
    if path.exists():
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            blob = {}
    if blob.get("artefact_key") != key:
        blob = {"artefact_key": key, "variants": {}}
    blob["generated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    blob["variants"][record["variant"]] = {"targets": record["targets"]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(blob, indent=1, sort_keys=True), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--emit", action="store_true",
                    help="write data/processed/width_record.json (re-emit "
                         "window only)")
    ap.add_argument("--out", type=Path, default=None,
                    help="write DIR/width_record.json instead")
    ap.add_argument("--set", action="append", default=[],
                    help="scenario override for the centres (e.g. level_shrink=0)")
    ap.add_argument("--cities", nargs="+", default=None)
    a = ap.parse_args(argv)
    if not a.emit and a.out is None:
        ap.error("pass --emit (re-emit window) or --out DIR")
    M.fix_hash_seed()
    rec = build(a.set, a.cities)
    path = (M.width_record_path() if a.emit else a.out / M.WIDTH_RECORD)
    write(rec, path)
    print(f"wrote {path} (variant {rec['variant']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
