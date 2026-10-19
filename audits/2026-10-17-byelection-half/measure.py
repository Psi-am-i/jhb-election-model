"""w_bye None (size-class weights, 0.0) against 0.5 (owner, §A59) at
Johannesburg and Tshwane 2026: drawn PR means, mean seats and P(largest party
alone) on 5,000 draws, seed 20261104, in process, written to out.json beside
this file. The centres, by-election levels and caps are in each run's trace
(`--trace DIR`, `<city>_<arm>/30_centres.json`); the four used for MODEL-LOG
§1.323 are kept beside this file as `<city>_<arm>_30_centres.json`. No data/
artefact is written.
Run: .venv/bin/python audits/2026-10-17-byelection-half/measure.py --trace DIR"""
import argparse, json, os, sys
from collections import Counter
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig
import montecarlo as M

ap = argparse.ArgumentParser(); ap.add_argument('--trace', required=True); a = ap.parse_args()
out = {}
for city_name in ('joburg', 'tshwane'):
    city = cityconfig.use(city_name); target = cityconfig.use_target('2026'); M.apply_city(city)
    for label, w in (('none', None), ('half', 0.5)):
        sc = M.load_scenario(argparse.Namespace(config=None, draws=5000, seed=20261104,
                                                set=None, counterfactual=False))
        sc['w_bye'] = w
        rd = Path(a.trace) / f'{city_name}_{label}'
        run = M.run_model(target, sc, verbose=False, run_dir=rd)
        means = {p: float(run.pr_share_draws[:, i].mean()) for p, i in run.index.items()}
        alone = Counter()
        for d in run.seat_draws:
            top = max(d.values()); lead = [p for p, s in d.items() if s == top]
            alone[lead[0] if len(lead) == 1 else 'tie'] += 1
        n = len(run.seat_draws)
        mean_seats = {p: sum(d.get(p, 0) for d in run.seat_draws) / n for p in run.index}
        out[f'{city_name}_{label}'] = {
            'drawn_mean': means, 'mean_seats': mean_seats,
            'p_largest_alone': {k: v / n for k, v in alone.items()},
            'bye_weight': sc.get('_bye_weight')}
        print(city_name, label, 'done', flush=True)
(Path(__file__).parent / 'out.json').write_text(json.dumps(out, indent=1, default=str))
