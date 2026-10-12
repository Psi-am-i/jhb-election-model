"""F2 / pool prereg D1: how much of the emitted pool seed survives the per-draw IPF.

Measurement only. Runs `montecarlo.run_model` directly on an ARCHIVED copy of
`src/` (never the live tree, never `montecarlo.py`'s main, which overwrites
published artefacts). Writes nothing under data/.

    git archive <commit> src | tar -x -C /tmp/seedsurv_src
    .venv/bin/python audits/2026-09-28-seed-survival/seed_survival.py \
        --src /tmp/seedsurv_src/src --city joburg --year 2021 --draws 1000 \
        --out /tmp/seedsurv_out

One process per city-year; run_all.sh fans them out.

DEFINITIONS (fixed before the first run)
----------------------------------------
seed S         `members` per party, normalised over pools: the share of a
               party's vote the spec says comes from each pool.
post-IPF C     the same object as the draw actually uses it: the per-draw
               balanced matrix Rd (`montecarlo._balance`), times each pool's
               central votes, normalised over pools per party; averaged over
               draws.
survival       (a) structural: IPF output is a diagonal rescaling of its input,
               so every cross-product ratio of S among positive cells, and every
               zero, is carried into every draw exactly. Checked numerically.
               (b) transmission: TV(C', C) / TV(S', S) when the seed is
               perturbed S -> S'. 1 = the perturbation reaches the draw's
               composition in full.
               (c) outcome sensitivity, the one that decides: paired change in
               mean seats, PR share and ward calls when the seed is perturbed.

VARIANTS
  base       the spec as emitted, seed 20261104
  seed2      the spec as emitted, seed 20261105 (unpaired Monte Carlo floor)
  placebo    each party's members column multiplied by a constant in [0.3, 3];
             IPF is invariant to it, so any change is harness or tolerance
  c4_eps     every zero cell (party in the spec's pool universe, absent from a
             pool) set to 1e-9: the zero becomes a member, nothing else moves.
             Separates the structural channel (ceiling indicator, Dirichlet
             mean floor, Dirichlet dimension) from the value channel.
  c4_mild    every zero cell set to 0.05 x that pool's share of central votes,
             column renormalised (queue 33's max-entropy fill, one reading)
  c4_strong  every column mixed halfway to the pool vote shares,
             S' = 0.5 S + 0.5 u: an upper bound on composition sensitivity,
             not a candidate repair
  c3_target  each pool's `registered` replaced by the TARGET year's fitted
             registration split (pools.pool_counts(city, target)), same total
             roll. Backtest targets only: an unheld target has no fit.
  c3_proj    `registered` split replaced by the spec's own
             `pool_shares_at_target`, same total (all specs; the incumbent
             projection, used here only as a second dose)

PAIRING: common random numbers. The drawer's generator is replaced by a proxy
reseeded per draw from (seed, draw), and every Dirichlet call gets its own
stream from (seed, draw, call). So a perturbation that changes a Dirichlet's
parameters or dimension cannot desynchronise anything else, and the VD/ward
stage (main generator, no longer consumed by the drawer) is identical across
variants. This changes WHICH random numbers the model sees, not its
distribution; `base` here is therefore not byte-equal to a normal run.

MATERIALITY (fixed before the first run). A variant MATTERS at a city-year if
  expected seats moved  M = sum_p |mean seats_p(variant) - mean seats_p(base)| / 2
is >= 1.0 seat AND at least one party's paired difference exceeds 3 paired
standard errors; or if expected ward calls moved (sum over wards and parties of
|Δ win probability| / 2) is >= 1.0 ward. C3/C4 are "in" the window if their
realistic variant (c3_target, c4_mild) matters at any city-year.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

VARIANTS = ["base", "seed2", "placebo", "c4_eps", "c4_mild", "c4_strong",
            "c3_target", "c3_proj"]
SEED = 20261104


class CRN:
    """Generator proxy: per-draw stream, and a fresh stream per Dirichlet call."""

    def __init__(self, seed):
        self.seed = seed
        self.reset(0)

    def reset(self, k):
        self.k = k
        self.j = 0
        self.gen = np.random.default_rng([self.seed, k])

    def dirichlet(self, alpha, size=None):
        self.j += 1
        return np.random.default_rng([self.seed, self.k, 7919, self.j]).dirichlet(alpha, size)

    def __getattr__(self, name):
        return getattr(self.gen, name)


def seed_matrix(pools, names, parties):
    S = np.array([[float(pools[g]["members"].get(p, 0.0)) for p in parties]
                  for g in names])
    cs = S.sum(axis=0, keepdims=True)
    return np.divide(S, cs, out=np.zeros_like(S), where=cs > 0)


def tv_cols(A, B):
    """Total-variation distance per column (both column-normalised)."""
    return 0.5 * np.abs(A - B).sum(axis=0)


def perturb(spec, variant, city, target, rs):
    import pools as PL
    spec = json.loads(json.dumps(spec))
    P = spec["pools"]
    names = list(P)
    parties = sorted({p for c in P.values() for p in c["members"]})
    votes = np.array([float(P[g]["registered"]) * float(P[g]["turnout"][1]) for g in names])
    u = votes / votes.sum()
    info = {}
    if variant == "placebo":
        k = {p: float(rs.uniform(0.3, 3.0)) for p in parties}
        for g in names:
            P[g]["members"] = {p: w * k[p] for p, w in P[g]["members"].items()}
    elif variant in ("c4_eps", "c4_mild", "c4_strong"):
        S = seed_matrix(P, names, parties)
        zeros = int((S == 0).sum())
        if variant == "c4_strong":
            S2 = 0.5 * S + 0.5 * u[:, None]
        else:
            fill = 1e-9 if variant == "c4_eps" else 0.05
            S2 = S.copy()
            for j in range(len(parties)):
                z = S[:, j] == 0
                if z.any():
                    S2[z, j] = fill * u[z]
            S2 = S2 / S2.sum(axis=0, keepdims=True)
        for gi, g in enumerate(names):
            P[g]["members"] = {p: float(S2[gi, j]) for j, p in enumerate(parties)
                               if S2[gi, j] > 0}
        info = {"zero_cells": zeros, "cells": int(S.size),
                "seed_tv_mean": float(tv_cols(S, S2).mean())}
    elif variant in ("c3_target", "c3_proj"):
        reg = np.array([float(P[g]["registered"]) for g in names])
        if variant == "c3_proj":
            cats = spec["categories"]
            new = np.array([float(spec["pool_shares_at_target"][cats.index(g)])
                            if g in cats else 0.0 for g in names])
        else:
            counts = PL.pool_counts(city, target.year, PL.load_config())
            tot = counts.totals("registered")
            new = np.array([float(tot[list(counts.categories).index(g)])
                            if g in counts.categories else 0.0 for g in names])
        new = new / new.sum() * reg.sum()
        for gi, g in enumerate(names):
            P[g]["registered"] = float(new[gi])
        info = {"split_before": dict(zip(names, (reg / reg.sum()).round(4).tolist())),
                "split_after": dict(zip(names, (new / new.sum()).round(4).tolist())),
                "dose_L1_of_roll": float(np.abs(new - reg).sum() / reg.sum())}
    return spec, info


def run_one(M, cityconfig, slug, year, draws, seed, spec_text, spec_path):
    """run_model with the spec read replaced and the drawer on common random numbers."""
    city = cityconfig.use(slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=[], draws=draws, seed=None, city=slug, target=year))
    scenario["seed"] = seed

    real_rt = Path.read_text
    want = str(spec_path.resolve())

    def rt(self, *a, **k):
        if str(Path(self).resolve()) == want:
            return spec_text
        return real_rt(self, *a, **k)

    cap = {"rd": [], "in_draw": False}
    real_ps, real_bal, real_pb, real_md = M.pool_spec, M._balance, M.partial_balance, M.make_drawer

    def ps(scenario, centres, index, ipf_out=None):
        out = real_ps(scenario, centres, index, ipf_out)
        if ipf_out is not None:
            cap["R0"] = np.array(ipf_out["R0"])
            cap["pool_votes"] = np.array(ipf_out["pool_votes"])
            cap["parties"] = list(ipf_out["parties"])
            cap["names"] = list(ipf_out["names"])
            cap["centres"] = {p: float(centres.get(p, 0.0)) for p in ipf_out["parties"]}
        return out

    def bal(R, e, t):
        r = real_bal(R, e, t)
        if cap["in_draw"]:
            cap["rd"].append(np.array(r, dtype=np.float64))
        return r

    def pb(R, e, t, *a, **k):
        r = real_pb(R, e, t, *a, **k)
        if cap["in_draw"]:
            cap["rd"].append(np.array(r, dtype=np.float64))
        return r

    def md(scenario, base_city_d, centres, index, rng):
        proxy = CRN(seed)
        f = real_md(scenario, base_city_d, centres, index, proxy)
        n = [0]

        def g(*a, **k):
            proxy.reset(n[0])
            n[0] += 1
            return f(*a, **k)
        g.ipf_stats = getattr(f, "ipf_stats", {})
        cap["in_draw"] = True
        return g

    Path.read_text = rt
    M.pool_spec, M._balance, M.partial_balance, M.make_drawer = ps, bal, pb, md
    try:
        run = M.run_model(target, scenario, verbose=False)
    finally:
        Path.read_text = real_rt
        M.pool_spec, M._balance, M.partial_balance, M.make_drawer = real_ps, real_bal, real_pb, real_md
    return run, cap, city, target


def summarise(run, cap):
    parties = sorted({p for d in run.seat_draws for p in d})
    seats = np.array([[d.get(p, 0) for p in parties] for d in run.seat_draws], float)
    wwc = np.asarray(run.ward_winner_counts, float)
    comp = None
    if cap.get("rd"):
        pv = cap["pool_votes"][:, None]
        C = np.stack([r * pv for r in cap["rd"]])
        cs = C.sum(axis=1, keepdims=True)
        comp = np.divide(C, cs, out=np.zeros_like(C), where=cs > 0)
    return {
        "parties": parties, "seats": seats, "universe": list(run.universe),
        "pr": np.asarray(run.pr_share_draws, float), "wwc": wwc,
        "ward_draws": np.asarray(run.ward_winner_draws) if run.ward_winner_draws is not None else None,
        "comp": comp, "ipf_parties": cap.get("parties"), "names": cap.get("names"),
        "R0": cap.get("R0"), "pool_votes": cap.get("pool_votes"),
        "guards": {"ipf_balances": run.ipf_balances, "ipf_failures": run.ipf_failures,
                   "cap_moved": float(run.cap_moved), "cap_undershoots": run.cap_undershoots,
                   "ipf_clipped": dict(run.ipf_clipped),
                   "ipf_worst": {k: float(v) for k, v in run.ipf_worst.items()},
                   "stale": run.scenario.get("_pools_stale")},
    }


def compare(b, v, draws):
    allp = sorted(set(b["parties"]) | set(v["parties"]))
    def col(x, p):
        return x["seats"][:, x["parties"].index(p)] if p in x["parties"] else np.zeros(len(x["seats"]))
    d_mean, se, per = {}, {}, {}
    for p in allp:
        diff = col(v, p) - col(b, p)
        d_mean[p] = float(diff.mean())
        se[p] = float(diff.std(ddof=1) / np.sqrt(len(diff))) if len(diff) > 1 else 0.0
    seats_moved = 0.5 * sum(abs(x) for x in d_mean.values())
    z = {p: (abs(d_mean[p]) / se[p] if se[p] > 0 else (np.inf if d_mean[p] else 0.0)) for p in allp}
    same_draw = float(np.mean([np.array_equal(b["seats"][i], v["seats"][i])
                               for i in range(min(len(b["seats"]), len(v["seats"])))])) \
        if b["parties"] == v["parties"] else float("nan")
    ward_moved = float(0.5 * np.abs(v["wwc"] - b["wwc"]).sum() / draws) \
        if b["wwc"].shape == v["wwc"].shape else float("nan")
    pr_pp = {}
    if b["pr"].shape == v["pr"].shape:
        dpr = (v["pr"] - b["pr"]).mean(axis=0) * 100
        pr_pp = {b["universe"][i]: float(dpr[i]) for i in range(len(dpr))}
    comp_tv = None
    if b["comp"] is not None and v["comp"] is not None and b["comp"].shape == v["comp"].shape:
        tv = 0.5 * np.abs(v["comp"] - b["comp"]).sum(axis=1)  # draws x parties
        comp_tv = dict(zip(b["ipf_parties"], tv.mean(axis=0).round(5).tolist()))
    return {"seats_moved": seats_moved, "d_mean_seats": d_mean, "se_paired": se,
            "max_z": float(max(z.values())) if z else 0.0,
            "max_abs_d": float(max(abs(x) for x in d_mean.values())) if d_mean else 0.0,
            "same_draw_frac": same_draw, "ward_calls_moved": ward_moved,
            "d_pr_pp": pr_pp,
            "max_abs_d_pr_pp": float(max((abs(x) for x in pr_pp.values()), default=float("nan"))),
            "post_ipf_comp_tv": comp_tv}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--city", required=True)
    ap.add_argument("--year", required=True)
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", default=",".join(VARIANTS))
    a = ap.parse_args()
    sys.path.insert(0, a.src)
    import cityconfig
    import montecarlo as M

    city = cityconfig.use(a.city)
    target = cityconfig.use_target(a.year)
    spec_path = city.processed / f"pools_{a.year}.json"
    spec = json.loads(spec_path.read_text())
    rs = np.random.default_rng(12345)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    res = {"city": a.city, "year": a.year, "draws": a.draws, "spec": str(spec_path),
           "seeds_in_spec": sorted(spec.get("seeds") or {}), "variants": {}}

    runs = {}
    for var in a.variants.split(","):
        t0 = time.time()
        if var in ("base", "seed2"):
            s2, info = spec, {}
        else:
            if var == "c3_target" and a.year == "2026":
                res["variants"][var] = {"skipped": "unheld target: no target-year fit"}
                continue
            try:
                s2, info = perturb(spec, var, city, target, rs)
            except SystemExit as e:
                res["variants"][var] = {"skipped": f"perturbation refused: {e}"}
                continue
        seed = SEED + 1 if var == "seed2" else SEED
        run, cap, city, target = run_one(M, cityconfig, a.city, a.year, a.draws, seed,
                                         json.dumps(s2), spec_path)
        runs[var] = summarise(run, cap)
        res["variants"][var] = {"info": info, "guards": runs[var]["guards"],
                                "seconds": round(time.time() - t0, 1)}
        if var == "base":
            b = runs["base"]
            names, parties = b["names"], b["ipf_parties"]
            S = seed_matrix(spec["pools"], names, parties)
            R0 = b["R0"]
            C0 = R0 * b["pool_votes"][:, None]
            C0 = C0 / np.where(C0.sum(axis=0, keepdims=True) > 0, C0.sum(axis=0, keepdims=True), 1)
            # structural check: R0 = diag(a) S diag(b) on positive cells <=> log R0 - log S additive
            pos = (S > 0) & (R0 > 0)
            L = np.where(pos, np.log(np.where(pos, R0, 1)) - np.log(np.where(pos, S, 1)), np.nan)
            # fit additive row + col effects by alternating means, report max residual
            rr = np.zeros(L.shape[0]); cc = np.zeros(L.shape[1])
            for _ in range(200):
                rr = np.nanmean(L - cc[None, :], axis=1)
                cc = np.nanmean(L - rr[:, None], axis=0)
            resid = np.nanmax(np.abs(L - rr[:, None] - cc[None, :]))
            zero_kept = bool(np.all((S == 0) == (R0 == 0)))
            comp_mean = b["comp"].mean(axis=0) if b["comp"] is not None else C0
            res["structure"] = {
                "ipf_parties": parties, "pools": names,
                "logratio_additive_max_resid": float(resid),
                "zero_pattern_identical_R0": zero_kept,
                "zero_pattern_identical_draws": bool(np.all((b["comp"] > 0) == (S > 0)[None]))
                if b["comp"] is not None else None,
                "zero_cells": int((S == 0).sum()), "cells": int(S.size),
                "single_pool_parties": [p for j, p in enumerate(parties) if S[:, j].max() > 0.999],
                "seed_vs_post_ipf_tv": dict(zip(parties, tv_cols(S, comp_mean).round(4).tolist())),
                "seed_vs_R0_tv": dict(zip(parties, tv_cols(S, C0).round(4).tolist())),
                "pool_vote_share": dict(zip(names, (b["pool_votes"] / b["pool_votes"].sum()).round(4).tolist())),
                "mean_seats": dict(zip(b["parties"], b["seats"].mean(axis=0).round(3).tolist())),
            }
        print(f"{a.city} {a.year} {var} {time.time()-t0:.0f}s", flush=True)

    if "base" in runs:
        for var, v in runs.items():
            if var == "base":
                continue
            c = compare(runs["base"], v, a.draws)
            res["variants"][var]["vs_base"] = c
        # seed TV per party for c4 variants (same parties/pools as base)
        for var in ("c4_mild", "c4_strong", "c4_eps"):
            if var in runs and runs[var]["comp"] is not None:
                b = runs["base"]
                names, parties = b["names"], b["ipf_parties"]
                S = seed_matrix(spec["pools"], names, parties)
                s2, _ = perturb(spec, var, city, target, np.random.default_rng(0))
                S2 = seed_matrix(s2["pools"], names, parties)
                res["variants"][var]["seed_tv"] = dict(zip(parties, tv_cols(S, S2).round(5).tolist()))
    (out / f"{a.city}-{a.year}.json").write_text(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
