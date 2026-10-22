"""The model's Johannesburg 2026 ratio to 2024 for each party: drawn mean
(5,000 draws, seed 20261104, run in process, nothing written) and the
pre-draw centre, each over the party's 2024 provincial-ballot citywide share.
Run: .venv/bin/python audits/2026-10-17-mk-byelections/model_ratio.py"""
import argparse, csv, os, sys
from collections import defaultdict
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig, parties as P
import montecarlo as M
city = cityconfig.use('joburg'); target = cityconfig.use_target('2026'); M.apply_city(city)
sc = M.load_scenario(argparse.Namespace(config=None, draws=5000, seed=20261104, set=None, counterfactual=False))
di = M.run_model(target, dict(sc), verbose=False, stop_after="drawer_inputs")
run = M.run_model(target, sc, verbose=False)
n = defaultdict(int)
for r in csv.DictReader(open('data/raw/elections/npe2024_JHB_vd_party.csv', encoding='utf-8')):
    n[P.canonical(r['sPartyName'])] += int(r['Party_Votes'])
t = sum(n.values())
print('by-election weights in the centres:', sc['_bye_value']['weights'])
for p in ['ANC', 'DA', 'EFF', 'MK', 'ASA', 'PA', 'VFPLUS', 'ALJAMAAH', 'IFP', 'RISE']:
    s24 = n[p] / t; m = run.pr_share_draws[:, run.index[p]].mean(); c = di.centres[p]
    print(f"{p:9s} 2024 {100*s24:5.2f}  drawn mean {100*m:5.2f} ratio {m/s24:.3f}  centre {100*c:5.2f} ratio {c/s24:.3f}")
