"""SPEC §1.9 turnout band review, from arm B's runs. Run with arm B's tree as cwd:

    PYTHONHASHSEED=0 .venv/bin/python turnout_table.py <data/arms/step11/B> > turnout.json

Drawn: `ModelRun.pool_turnout_draws` (saved by arm_run.py), q5 and q95 per
pool; citywide per draw = the registration-weighted mean of the pool draws,
weights = each pool's `registered` in the run's own spec (the definition
`pools.turnout_limits` uses for the citywide slider). Observed: per pool,
`pools.turnout_record(city, cfg, before="2022", kind="LGE")` (every LGE of the
city in the calendar with a results file, 2000-2021), min and max; citywide,
the same registration-weighted mean over each year's pool turnouts, with the
target spec's registration as weights. Reads only.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "src")
import cityconfig  # noqa: E402
import pools  # noqa: E402

runs = Path(sys.argv[1])
_stdout = sys.stdout
sys.stdout = sys.stderr      # the readers print warnings; keep stdout for the JSON
cfg = pools.load_config()
out = {}
for d in sorted(p for p in runs.iterdir() if (p / "arrays.npz").exists()):
    label = d.name
    if label.startswith("rule_a"):
        continue
    slug, year = label.rsplit("-", 1)
    city = cityconfig.use(slug)
    meta = json.loads((d / "meta.json").read_text())
    draws = np.load(d / "arrays.npz")["pool_turnout_draws"]
    names = meta["pool_turnout_names"]
    spec = json.loads((city.processed / f"pools_{year}.json").read_text())
    reg = np.array([float(spec["pools"][n]["registered"]) for n in names])
    record = pools.turnout_record(city, cfg, before="2022", kind="LGE")
    years = sorted(record)
    cats = list(spec["pools"])
    arr = np.array([record[y] for y in years])          # (years, pools in spec order)
    idx = [cats.index(n) for n in names]
    arr = arr[:, idx]
    city_draw = (draws * reg[None, :]).sum(axis=1) / reg.sum()
    city_obs = (arr * reg[None, :]).sum(axis=1) / reg.sum()
    rows = {}
    for j, n in enumerate(names):
        rows[n] = {"q5": float(np.percentile(draws[:, j], 5)),
                   "q95": float(np.percentile(draws[:, j], 95)),
                   "obs_min": float(arr[:, j].min()), "obs_max": float(arr[:, j].max())}
    rows["citywide"] = {"q5": float(np.percentile(city_draw, 5)),
                        "q95": float(np.percentile(city_draw, 95)),
                        "obs_min": float(city_obs.min()), "obs_max": float(city_obs.max())}
    out[label] = {"years": years, "rows": rows}
json.dump(out, _stdout, indent=1)
