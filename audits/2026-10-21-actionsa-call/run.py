"""Johannesburg 2026 with and without the strength judgements, in process.
Writes only into --out (a trace per arm and a summary json)."""
import argparse, json, os, sys
from pathlib import Path
import numpy as np
R = Path('/Users/simondavis/projects/atlas-jhb-election-model')
sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig, montecarlo as M

ap = argparse.ArgumentParser()
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--draws', type=int, default=5000)
ap.add_argument('--seed', type=int, default=20261104)
a = ap.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
city = cityconfig.use('joburg'); target = cityconfig.use_target('2026')
res = {}
for arm, on in (('with', True), ('without', False)):
    M.apply_city(city)
    sc = M.load_scenario(argparse.Namespace(config=None, set=None, draws=a.draws,
                                            seed=a.seed, city='joburg', target='2026'))
    sc['apply_judgements'] = on
    run = M.run_model(target, sc, R / 'data/raw/elections', verbose=False,
                      run_dir=a.out / arm)
    names = list(run.index)
    pr = np.asarray(run.pr_share_draws, dtype=float)
    seats = np.array([[d.get(p, 0) for p in names] for d in run.seat_draws], float)
    thr = np.asarray(run.thresholds, dtype=float)
    out = {}
    for j, p in enumerate(names):
        s = pr[:, j]
        out[p] = {'mean': float(s.mean()), 'p05': float(np.quantile(s, .05)),
                  'p95': float(np.quantile(s, .95)), 'seats': float(seats[:, j].mean()),
                  'seats_p05': float(np.quantile(seats[:, j], .05)),
                  'seats_p95': float(np.quantile(seats[:, j], .95))}
    res[arm] = {'parties': out, 'council_mean': float(seats.sum(1).mean()),
                'threshold_mean': float(thr.mean()) if thr.size else None}
    print(arm, 'done', flush=True)
(a.out / 'summary.json').write_text(json.dumps(res, indent=1))
top = sorted(res['without']['parties'], key=lambda p: -res['without']['parties'][p]['mean'])[:9]
print('party | list vote without | with | seats without | with')
for p in top:
    w, j = res['without']['parties'][p], res['with']['parties'][p]
    print(f"{p} | {w['mean']*100:.1f} ({w['p05']*100:.1f}-{w['p95']*100:.1f}) | "
          f"{j['mean']*100:.1f} ({j['p05']*100:.1f}-{j['p95']*100:.1f}) | "
          f"{w['seats']:.1f} ({w['seats_p05']:.0f}-{w['seats_p95']:.0f}) | "
          f"{j['seats']:.1f} ({j['seats_p05']:.0f}-{j['seats_p95']:.0f})")
