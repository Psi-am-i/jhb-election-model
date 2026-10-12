"""Attribute the forecast's realised width to the layers that produce it.

WHY. `SD_FLOOR` cannot be settled without this. Two sound measurements point
opposite ways: the theta record for parties at or above 15% baseline (n=39,
eight metros) gives sd(log theta) = 0.227, so the size fit (0.111-0.148) and the
typed floor (0.150) are both too NARROW; but with the floor OFF the realised
ranks 1-3 width is already nearly right (sd(z) 0.948 against a nominal 1.0), and
the floor pushes it to 0.842 -- too wide. The likely reconciliation is that
theta is not the only source of level spread, so no layer should be asked to
reproduce its own marginal record on its own. Nobody has written the sum down.

METHOD. Disable one source at a time and measure how much of the DRAWN spread
disappears. The quantity is sd(log citywide PR share) per party across draws --
the forecast's own dispersion, which needs no outcome and so can be measured on
the live target as well as a backtest.

Sources reachable as scenario keys are switched off through the scenario. Three
are not -- the per-party level shock, the pool turnout copula and the within-pool
Dirichlet -- and are removed by monkeypatch inside this harness: `log_shock`,
`correlated_triangular` and `pool_split`, the named patch points of the keyed
draw (design 1c §2.5). IT PATCHES NOTHING PERMANENTLY: every patch is restored
in a `finally`, and the model is unchanged by importing or running this.

    .venv/bin/python src/width_budget.py --city joburg --year 2021 --draws 300

READ THE NOISE FLOOR IT PRINTS BEFORE READING ANYTHING ELSE. Before the keyed
streams (design 1c), switching a source off changed how many random numbers the
draw consumed, so every later draw shifted too, and a single-seed ablation mixed
"this source contributed variance" with "the stream moved" (the first run here
reported NEGATIVE contributions for ward noise). Every source now reads its own
keyed stream, so an ablation leaves the others' primitives bit-identical and
the arms are paired. That is argued from the stream design, not re-measured
here: the five-seed average and the printed floor are kept until a paired
re-measurement shows the floor has fallen.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

import cityconfig            # noqa: E402
import montecarlo as M       # noqa: E402

DATA = REPO / "data/raw/elections"


def run(city, year, draws, overrides, patches=(), seed=20261104):
    saved = {}
    for name, fn in patches:
        saved[name] = getattr(M, name)
        setattr(M, name, fn)
    try:
        c = cityconfig.use(city)
        t = cityconfig.use_target(year)
        M.apply_city(c)
        sc = M.load_scenario(argparse.Namespace(
            config=None, set=list(overrides), draws=draws, seed=seed,
            city=city, target=year))
        return M.run_model(t, sc, DATA, verbose=False)
    finally:
        for name, fn in saved.items():
            setattr(M, name, fn)


def spread(run_obj, parties):
    """sd(log share) per party across draws — the forecast's own dispersion.

    ``parties=None`` means THE RUN'S OWN UNIVERSE. This function took a fixed
    list until 2026-08-30 and its only caller passed a ten-party cast typed in
    an earlier cycle, so a party outside that list was never budgeted and its
    width was never checked. The universe is what the model actually built;
    asking it is always right and never goes stale. MODEL-LOG §1.140.
    """
    out = {}
    for p in (run_obj.index if parties is None else parties):
        i = run_obj.index.get(p)
        if i is None:
            continue
        col = np.clip(run_obj.pr_share_draws[:, i], 1e-9, None)
        out[p] = float(np.std(np.log(col), ddof=1))
    return out


def _no_pool_turnout(z_own, spec, z_common, rho):
    """The pool turnout draw, removed: every pool takes its band's MODE.

    `spec` is the triangular (low, mode, high) that `pools.turnout_band`
    measured, so returning the mode keeps the level and removes the spread.
    Same signature as `montecarlo.correlated_triangular`.
    """
    return float(spec[1])


def _mean_split(log_g, alpha):
    """The within-pool Dirichlet, removed: every draw takes its MEAN.

    Patched over `montecarlo.pool_split`, whose second argument is the
    concentration vector the drawer would have drawn from. The keyed gammas
    are still read, so every other stream is untouched.
    """
    a = np.asarray(alpha, dtype=float)
    total = a.sum()
    return a / total if total > 0 else np.full(a.shape, 1.0 / max(a.size, 1))


def _no_shock(sd, z, log_chi, df):
    """The level shock, removed: every draw takes the centre exactly.

    Same signature as `montecarlo.log_shock`; ones in the shape of `z`.
    """
    return np.ones(np.shape(z), dtype=float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--year", default="2021")
    ap.add_argument("--draws", type=int, default=600)
    # A TEN-PARTY TYPED DEFAULT MEASURED THE WIDTH OF A FIXED CAST. Any party
    # outside the list was never budgeted and its width never checked — and the
    # list is from an earlier cycle. `None` means "the run's own universe",
    # resolved after the model is loaded, so a new party is measured the first
    # time it appears. MODEL-LOG §1.140.
    ap.add_argument("--parties", nargs="+", default=None,
                    help="parties to budget (default: the run's own universe)")
    a = ap.parse_args()

    arms = [
        ("full model", [], ()),
        ("theta level shock off", [], (("log_shock", _no_shock),)),
        ("pool turnout copula off", [],
         (("correlated_triangular", _no_pool_turnout),)),
        ("within-pool Dirichlet off", [], (("pool_split", _mean_split),)),
        ("ward noise off", ["ward_noise_sd=0"], ()),
        ("per-VD turnout noise off", ["turnout_noise_sd=0"], ()),
        ("turnout blend jitter off", ["turnout_blend_jitter=0"], ()),
        ("entrant slot off", ["entrant_prob=0"], ()),
        ("EVERYTHING BUT the theta shock off",
         ["ward_noise_sd=0", "turnout_noise_sd=0", "turnout_blend_jitter=0",
          "entrant_prob=0"],
         (("correlated_triangular", _no_pool_turnout),
          ("pool_split", _mean_split))),
    ]

    # SEVERAL SEEDS PER ARM, and the reason is a defect in the obvious method.
    # Switching a source off also changes how many random numbers the draw
    # consumes, so every later draw shifts too. A single-seed ablation therefore
    # mixes "this source contributed variance" with "the stream moved", and the
    # first run of this harness duly reported NEGATIVE contributions for ward
    # noise -- removing a noise source appearing to make the forecast wider,
    # which is impossible and was the giveaway. Averaging over seeds washes the
    # stream shift out; the spread of the full-model arm across seeds is
    # reported below as the floor under which nothing here is a finding.
    seeds = [20261104, 20261105, 20261106, 20261107, 20261108]
    # RESOLVE THE PARTY LIST FROM THE RUN, not from a typed cast. One cheap
    # baseline run supplies the universe the model actually built, so every
    # party in this forecast is budgeted — including one that did not exist when
    # this script was written. `--parties` still overrides, for a targeted look.
    if not a.parties:
        probe = run(a.city, a.year, min(a.draws, 60), [], {}, seeds[0])
        by_mean = {p: float(np.mean(probe.pr_share_draws[:, i]))
                   for p, i in probe.index.items()}
        a.parties = sorted(spread(probe, None), key=lambda q: -by_mean.get(q, 0.0))
        print(f"  parties: {len(a.parties)} from the run's own universe, "
              f"largest first (pass --parties to narrow)")
    rows = {}
    for label, overrides, patches in arms:
        per_seed = [spread(run(a.city, a.year, a.draws, overrides, patches, sd),
                           a.parties) for sd in seeds]
        rows[label] = {p: float(np.mean([d[p] for d in per_seed if p in d]))
                       for p in a.parties
                       if any(p in d for d in per_seed)}
        rows[label + " __sd_across_seeds"] = {
            p: float(np.std([d[p] for d in per_seed if p in d], ddof=1))
            for p in a.parties if any(p in d for d in per_seed)}
        print(f"  measured: {label}", flush=True)
    base = rows["full model"]

    print(f"\nSHARE OF DRAWN VARIANCE REMOVED, {a.city} {a.year}, "
          f"{a.draws} draws, mean of {len(seeds)} seeds")
    print("  (1 - var_without / var_full)\n")
    print("  " + f"{'source removed':<36}" + "".join(f"{p[:8]:>10}" for p in a.parties))
    for label, _o, _p in arms:
        if label == "full model":
            continue
        cells = []
        for p in a.parties:
            f, w = base.get(p), rows[label].get(p)
            cells.append("        —" if not f or w is None
                         else f"{1 - (w * w) / (f * f):>9.2f}")
        print(f"  {label:<36}" + "".join(cells))

    noise = rows["full model __sd_across_seeds"]
    print("\n  NOISE FLOOR — sd of the full model's own sd(log share) across "
          "the five seeds,\n  as a share of the mean. Nothing above is a "
          "finding unless it clears roughly twice this.")
    print("  " + "".join(
        f"{(noise.get(p, 0) / base[p] if base.get(p) else 0):>9.2f} " for p in a.parties))

    out = REPO / "data/processed/width_budget.json"
    out.write_text(json.dumps({"city": a.city, "year": a.year,
                               "draws": a.draws, "spread": rows}, indent=1))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
