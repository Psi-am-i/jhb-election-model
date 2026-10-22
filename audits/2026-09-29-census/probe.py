"""One census step, run INSIDE a scratch root (cwd) against its own `src/`.

    python probe.py emit <slug> <year> <out_dir>   # in-process emit -> clone + out_dir/spec.json
    python probe.py run  <slug> <year> <out_dir>   # traced run_model -> out_dir/trace/
    python probe.py c8   <out_dir>                 # constructed merger, theta_residual rows
    python probe.py spread <out_dir>               # panel_turnout_spread at 2016 and 2026

Each step is its own process, so no module cache carries one step's result
into another (R3 F9). Writes only under the scratch root and `out_dir`.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import sys
from pathlib import Path

SRC = Path.cwd() / "src"
sys.path.insert(0, str(SRC))

SEED = 20261104
DRAWS = 300


def spec_path(slug, year):
    base = Path("data/processed")
    return (base if slug == "joburg" else base / slug) / f"pools_{year}.json"


def emit(slug, year, out: Path):
    import cityconfig
    import pools
    assert Path(pools.__file__).resolve().parent == SRC.resolve(), pools.__file__
    city = cityconfig.use(slug)
    target = cityconfig.use_target(year)
    pools.write_lineage_template = lambda c, t, *a, **k: pools.lineage_path(c, t)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            spec = pools.emit_pools(city, target, pools.load_config())
    except BaseException as exc:                  # a refusal is a result
        (out / "emit_refused.txt").write_text(f"{type(exc).__name__}: {exc}")
        return
    text = json.dumps(spec, indent=2, sort_keys=True)   # as emit_pools writes
    spec_path(slug, year).write_text(text)
    (out / "spec.json").write_text(text)


def run(slug, year, out: Path):
    import argparse as _ap
    import cityconfig
    import montecarlo as M
    assert Path(M.__file__).resolve().parent == SRC.resolve(), M.__file__
    city = cityconfig.use(slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(_ap.Namespace(
        config=None, set=[f"seed={SEED}"], draws=DRAWS, seed=None,
        city=slug, target=year))
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            M.run_model(target, scenario, Path("data/raw/elections"),
                        verbose=False, run_dir=out / "trace",
                        trace_detail=True)
    except BaseException as exc:
        (out / "run_failed.txt").write_text(f"{type(exc).__name__}: {exc}")
        return
    (out / "mergers.json").write_text(json.dumps(scenario.get("_mergers"),
                                                 default=str))


def c8(out: Path):
    """Fixture K: one constructed merger dated before Johannesburg 2021, the
    predecessor the largest 2019-national party off the 2021 ballot, the
    successor the DA. theta_residual's rows are dumped with the real MERGERS
    and with K."""
    import cityconfig
    import levels
    import pools
    import theta_residual as T
    npe = cityconfig.CALENDAR["2019"].results.replace("{CODE}", "JHB")
    lge = cityconfig.CALENDAR["2021"].results.replace("{CODE}", "JHB")
    before = levels._citywide("data/raw/elections/" + npe)
    _after, roster = levels._citywide_and_roster("data/raw/elections/" + lge)
    off = sorted((p for p in before if p not in roster and before[p] > 0),
                 key=lambda p: -before[p])
    assert off and "DA" in roster, (off[:3], "DA" in roster)
    pred = off[0]
    rows = {}
    for label, mergers in (("real", pools.MERGERS),
                           ("K", (pools.Merger(frozenset({pred, "DA"}),
                                               dt.date(2020, 6, 1),
                                               "census fixture K"),))):
        pools.MERGERS = mergers
        T._residuals_cached.cache_clear()
        rows[label] = [list(map(str, r)) for r in T.residuals(codes=("JHB",))]
    (out / "c8.json").write_text(json.dumps({"predecessor": pred,
                                             "share": before[pred],
                                             "rows": rows}))


def spread(out: Path):
    import pools
    cfg = pools.load_config()
    res = {}
    for before in ("2016", "2026"):
        by_pool, n = pools.panel_turnout_spread(cfg, before=before)
        res[before] = {"spread": {k: float(v) for k, v in by_pool.items()},
                       "n": int(n)}
    (out / "spread.json").write_text(json.dumps(res, indent=1, sort_keys=True))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("emit", "run", "c8", "spread"))
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()
    if a.cmd in ("c8", "spread"):
        out = Path(a.args[0]); out.mkdir(parents=True, exist_ok=True)
        (c8 if a.cmd == "c8" else spread)(out)
        return
    slug, year, out = a.args
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    (emit if a.cmd == "emit" else run)(slug, year, out)


if __name__ == "__main__":
    main()
