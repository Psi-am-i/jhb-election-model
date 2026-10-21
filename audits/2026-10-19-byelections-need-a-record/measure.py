"""Johannesburg and Tshwane 2026 at the shipped defaults (w_bye 0.5, no
by-election weight for a party with no record), 5,000 draws, seed 20261104, in
process: drawn PR means, mean seats, P(largest party alone) to out.json; each
run's 30_centres trace kept beside this file. Compared against
audits/2026-10-17-byelection-half/ (the same at w_bye 0.5 before this change).
Run: .venv/bin/python audits/2026-10-19-byelections-need-a-record/measure.py --trace DIR --width WIDTH_RECORD_JSON"""
import argparse, json, os, shutil, sys
from collections import Counter
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig
import montecarlo as M

ap = argparse.ArgumentParser(); ap.add_argument('--trace', required=True)
# A width record rebuilt for this tree (`src/width_record.py --out DIR`), passed
# in rather than written to data/ outside a re-emit window.
ap.add_argument('--width', required=True); a = ap.parse_args()
width_blob = json.loads(Path(a.width).read_text())
out = {}
for city_name in ('joburg', 'tshwane'):
    city = cityconfig.use(city_name); target = cityconfig.use_target('2026'); M.apply_city(city)
    sc = M.load_scenario(argparse.Namespace(config=None, draws=5000, seed=20261104,
                                            set=None, counterfactual=False))
    rd = Path(a.trace) / city_name
    rec = width_blob['variants'][M.width_record_variant(sc)]['targets']['2026']
    run = M.run_model(target, sc, verbose=False, run_dir=rd, width_override=rec)
    shutil.copy(rd / '30_centres.json', Path(__file__).parent / f'{city_name}_30_centres.json')
    alone = Counter()
    for d in run.seat_draws:
        top = max(d.values()); lead = [p for p, s in d.items() if s == top]
        alone[lead[0] if len(lead) == 1 else 'tie'] += 1
    n = len(run.seat_draws)
    out[city_name] = {
        'drawn_mean': {p: float(run.pr_share_draws[:, i].mean()) for p, i in run.index.items()},
        'mean_seats': {p: sum(d.get(p, 0) for d in run.seat_draws) / n for p in run.index},
        'p_largest_alone': {k: v / n for k, v in alone.items()},
        'bye_weight': sc.get('_bye_weight')}
    print(city_name, 'done', flush=True)
(Path(__file__).parent / 'out.json').write_text(json.dumps(out, indent=1, default=str))
