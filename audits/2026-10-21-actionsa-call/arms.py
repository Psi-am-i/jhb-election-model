"""Johannesburg 2026 with and without the strength judgements, saved as
arm directories (arrays.npz + meta.json, the layout of src/arms.py) for
reports/model-changes/build_report.py. Writes only into --out.

    .venv/bin/python audits/2026-10-21-actionsa-call/arms.py --out DIR
"""
import argparse, json, os, subprocess, sys
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig, montecarlo as M

ap = argparse.ArgumentParser()
ap.add_argument('--out', type=Path, required=True)
ap.add_argument('--draws', type=int, default=5000)
ap.add_argument('--seed', type=int, default=20261104)
a = ap.parse_args()
city = cityconfig.use('joburg'); target = cityconfig.use_target('2026')
head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
for arm, on in (('without', False), ('with', True)):
    dest = a.out / arm / 'joburg-2026'; dest.mkdir(parents=True, exist_ok=True)
    M.apply_city(city)
    sc = M.load_scenario(argparse.Namespace(config=None, set=None, draws=a.draws,
                                            seed=a.seed, city='joburg', target='2026'))
    sc['apply_judgements'] = on
    run = M.run_model(target, sc, R / 'data/raw/elections', verbose=False)
    universe = list(run.universe)
    seats = np.array([[s.get(p, 0) for p in universe] for s in run.seat_draws], dtype=np.int64)
    np.savez_compressed(dest / 'arrays.npz',
                        pr_share_draws=np.asarray(run.pr_share_draws, dtype=float),
                        pr_vote_draws=np.asarray(run.pr_vote_draws),
                        ward_winner_draws=np.asarray(run.ward_winner_draws, dtype=np.int64),
                        seat_draws=seats)
    (dest / 'meta.json').write_text(json.dumps(
        {'arm': arm, 'city': 'joburg', 'year': '2026', 'draws': a.draws, 'seed': a.seed,
         'apply_judgements': on, 'seat_cols': universe, 'git': head}, indent=1))
    print(arm, 'done', flush=True)
