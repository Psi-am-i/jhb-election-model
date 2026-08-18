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
Dirichlet -- and are removed by monkeypatch inside this harness. IT PATCHES
NOTHING PERMANENTLY: every patch is restored in a `finally`, and the model is
unchanged by importing or running this.

    .venv/bin/python src/width_budget.py --city joburg --year 2021 --draws 300

READ THE NOISE FLOOR IT PRINTS BEFORE READING ANYTHING ELSE. Switching a source
off also changes how many random numbers the draw consumes, so every later draw
shifts too, and a single-seed ablation mixes "this source contributed variance"
with "the stream moved". The first run of this harness duly reported NEGATIVE
contributions for ward noise -- removing a noise source appearing to make the
forecast wider, which is impossible and was the giveaway. It now averages over
five seeds and prints the full model's own seed-to-seed spread as the floor.
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
    import numpy.random as _npr
    saved, saved_dir = {}, None
    for name, fn in patches:
        if name == "__dirichlet__":
            saved_dir = np.random.default_rng
            np.random.default_rng = lambda *ar, **kw: _MeanDirichletRNG(
                saved_dir(*ar, **kw))
        else:
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
        if saved_dir is not None:
            np.random.default_rng = saved_dir


def spread(run_obj, parties):
    """sd(log share) per party across draws — the forecast's own dispersion."""
    out = {}
    for p in parties:
        i = run_obj.index.get(p)
        if i is None:
            continue
        col = np.clip(run_obj.pr_share_draws[:, i], 1e-9, None)
        out[p] = float(np.std(np.log(col), ddof=1))
    return out


def _no_pool_turnout(rng, spec, z_common, rho):
    """The pool turnout draw, removed: every pool takes its band's MODE.

    `spec` is the triangular (low, mode, high) that `pools.turnout_band`
    measured, so returning the mode keeps the level and removes the spread.
    """
    return float(spec[1])


class _MeanDirichletRNG:
    """A Generator proxy whose `dirichlet` returns the mean instead of a draw.

    numpy's Generator is an immutable extension type, so the method cannot be
    patched on the class. Wrapping the instance and delegating everything else
    keeps every other random stream identical -- which matters here, because
    the whole difficulty of this measurement is that changing one source
    perturbs the others through the stream.
    """

    def __init__(self, inner):
        object.__setattr__(self, "_inner", inner)

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_inner"), name)

    def dirichlet(self, alpha, size=None):
        a = np.asarray(alpha, dtype=float)
        total = a.sum()
        mean = a / total if total > 0 else np.full(a.shape, 1.0 / max(a.size, 1))
        return mean if size is None else np.tile(mean, (size, 1))


def _no_shock(rng, sd, size=None, df=None):
    """The level shock, removed: every draw takes the centre exactly."""
    n = 1 if size is None else size
    arr = np.ones(np.shape(sd) if np.ndim(sd) else (n,), dtype=float)
    return arr if np.ndim(sd) or size is not None else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--city", default="joburg")
    ap.add_argument("--year", default="2021")
    ap.add_argument("--draws", type=int, default=600)
    ap.add_argument("--parties", nargs="+",
                    default=["ANC", "DA", "EFF", "ASA", "IFP", "VFPLUS", "PA",
                             "ALJAMAAH", "ACDP", "COPE"])
    a = ap.parse_args()

    import numpy.random as _npr
    _real_dirichlet = _npr.Generator.dirichlet

    class _PatchDirichlet:
        """A context-manager-shaped pair, so `run`'s setattr loop can take it."""

    arms = [
        ("full model", [], ()),
        ("theta level shock off", [], (("log_shock", _no_shock),)),
        ("pool turnout copula off", [],
         (("correlated_triangular", _no_pool_turnout),)),
        ("within-pool Dirichlet off", [], (("__dirichlet__", None),)),
        ("ward noise off", ["ward_noise_sd=0"], ()),
        ("per-VD turnout noise off", ["turnout_noise_sd=0"], ()),
        ("turnout blend jitter off", ["turnout_blend_jitter=0"], ()),
        ("entrant slot off", ["entrant_prob=0"], ()),
        ("EVERYTHING BUT the theta shock off",
         ["ward_noise_sd=0", "turnout_noise_sd=0", "turnout_blend_jitter=0",
          "entrant_prob=0"],
         (("correlated_triangular", _no_pool_turnout),
          ("__dirichlet__", None))),
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
