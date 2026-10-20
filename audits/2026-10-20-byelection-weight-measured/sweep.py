"""The by-election weight measured on 2021 (prereg/2026-10-20-byelection-weight-measured.md).

Runs grid arms over `w_bye`, the swing-0 arm R and the per-class arm C on the
2021 elections of the eight metros, reusing the deltas that
`audits/2026-10-20-byelection-2021-backtest/run.py` built under its --work
directory (`processed/base/<slug>/`). Same scoring as that run:
compare_history.run_city_year at 1,000 draws, seed 20261104, with run_model
pointed at the scratch processed directory. One results file per arm,
`<work>/sweep/<arm>.json`, so arms can run in separate processes. Writes
nothing into data/.

    .venv/bin/python audits/2026-10-20-byelection-weight-measured/sweep.py \\
        --work DIR --arm g0.333 [--arm R] [--arm C --class-weights 0.4,0.2]

An arm is `g<w>` (grid, the shipped cap), `R` (w_bye 0.5, every
weighted_delta set to 0), or `C` (w_bye None, class weights
`under,at_or_over` from --class-weights).
"""
import argparse, csv, functools, json, os, shutil, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import compare_history as CH
import montecarlo as M

SLUGS = ['joburg', 'tshwane', 'ekurhuleni', 'capetown', 'ethekwini',
         'nelsonmandelabay', 'buffalocity', 'mangaung']
DATA = R / 'data/raw/elections'

ap = argparse.ArgumentParser()
ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--arm', action='append', required=True)
ap.add_argument('--class-weights', default=None)
a = ap.parse_args(); W = a.work.resolve()
assert not str(W).startswith(str(R / 'data')), 'work dir must lie outside data/'
BASE = W / 'processed' / 'base'
assert all((BASE / s / 'byelection_party_deltas.csv').exists() for s in SLUGS), \
    'run audits/2026-10-20-byelection-2021-backtest/run.py --work DIR first'


def swing0_dir(slug):
    """A copy of the base processed directory with every weighted_delta 0."""
    out = W / 'processed' / 'swing0' / slug
    if (out / 'byelection_party_deltas.csv').exists():
        return out
    out.mkdir(parents=True, exist_ok=True)
    for f in (BASE / slug).iterdir():
        if f.name != 'byelection_party_deltas.csv':
            shutil.copy(f, out / f.name)
    with open(BASE / slug / 'byelection_party_deltas.csv', encoding='utf-8', newline='') as fi, \
         open(out / 'byelection_party_deltas.csv', 'w', encoding='utf-8', newline='') as fo:
        rd = csv.DictReader(fi); wr = csv.DictWriter(fo, fieldnames=rd.fieldnames); wr.writeheader()
        for row in rd:
            row['weighted_delta'] = '+0.0000'
            wr.writerow(row)
    return out


orig_run, orig_read, orig_w = M.run_model, M.read_bye_value, M.DEFAULTS['w_bye']
(W / 'sweep').mkdir(parents=True, exist_ok=True)
for arm in a.arm:
    if arm.startswith('g'):
        overrides, pdir = [f'w_bye={float(arm[1:])}'], (lambda s: BASE / s)
    elif arm == 'R':
        overrides, pdir = ['w_bye=0.5'], swing0_dir
    elif arm == 'C':
        under, over = (float(x) for x in a.class_weights.split(','))
        weights = {'under': under, 'at_or_over': over}
        M.DEFAULTS['w_bye'] = None
        M.read_bye_value = lambda path=None: {'weights': dict(weights),
                                              'artefact_key': 'sweep-arm-C', 'path': 'none'}
        overrides, pdir = [], (lambda s: BASE / s)
    else:
        raise SystemExit(f'unknown arm {arm}')
    results = {}
    try:
        for slug in SLUGS:
            M.run_model = functools.partial(orig_run, processed=pdir(slug))
            try:
                row = CH.run_city_year(slug, '2021', 1000, DATA, overrides=overrides,
                                       run_dir=W / 'sweep-trace' / arm)
            finally:
                M.run_model = orig_run
            results[slug] = {'pr_mae': row['pr_mae'], 'ward_mae': row['ward_mae'],
                             'seat_abs_err': row['seat_abs_err'], 'wards': row['wards'],
                             'votes': row['votes'], 'seats': row['seats']}
            print(arm, slug, round(row['pr_mae'], 4), row['seat_abs_err'], flush=True)
    finally:
        M.read_bye_value, M.DEFAULTS['w_bye'] = orig_read, orig_w
    (W / 'sweep' / f'{arm}.json').write_text(json.dumps(results, indent=1, default=str))
