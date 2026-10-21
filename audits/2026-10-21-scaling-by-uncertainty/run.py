"""Making the shares add to 100% by uncertainty (prereg/2026-10-21-scaling-by-uncertainty.md).

Scores every city-year of data/processed/history.json under one arm with
compare_history.run_city_year (1,000 draws, seed 20261104). Arm P is the
shipped model; V and H wrap montecarlo.blended_centres so that its centres sum
to 1 by taking the excess in proportion to u_i ((c σ)² for V, c σ² for H),
σ from montecarlo.poll_model_sd. Writes <work>/<arm>.json; nothing into data/.

    .venv/bin/python audits/2026-10-21-scaling-by-uncertainty/run.py --work DIR --arm V
"""
import argparse, json, os, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig as C
import compare_history as CH
import montecarlo as M

DATA = R / 'data/raw/elections'
FLOOR = 0.10  # a party keeps at least 10% of its centre

ap = argparse.ArgumentParser()
ap.add_argument('--work', type=Path, required=True)
ap.add_argument('--arm', required=True, choices=['P', 'V', 'H'])
ap.add_argument('--only', default=None, help='slug:year, for a smoke test')
a = ap.parse_args(); W = a.work.resolve()
assert not str(W).startswith(str(R / 'data')), 'work dir must lie outside data/'
W.mkdir(parents=True, exist_ok=True)


def take_excess(centres, u):
    """c_i − E·u_i/Σu over the positive centres, E the excess over 1; a party
    whose cut would pass 90% of its centre is held at FLOOR × centre and the
    remainder spread over the rest by the same rule."""
    pos = {p: v for p, v in centres.items() if v > 0}
    excess = sum(pos.values()) - 1.0
    if excess <= 0:
        return dict(centres), []
    out, free, held = dict(centres), set(pos), []
    while excess > 1e-15 and free:
        U = sum(u[p] for p in free)
        if U <= 0:
            break
        over = [p for p in free if out[p] - excess * u[p] / U < FLOOR * pos[p]]
        if not over:
            for p in free:
                out[p] -= excess * u[p] / U
            excess = 0.0
            break
        for p in over:
            excess -= out[p] - FLOOR * pos[p]
            out[p] = FLOOR * pos[p]
            free.discard(p); held.append(p)
    return out, held


orig = M.blended_centres
log = {}


def wrapped(scenario, base_city, prior_pr_share, bye, trace=None):
    centres, notes = orig(scenario, base_city, prior_pr_share, bye, trace)
    rec_cache = {}

    def rec():
        if 'r' not in rec_cache:
            rec_cache['r'] = M.read_width_record(YEAR, scenario)
        return rec_cache['r']
    sig = {p: M.poll_model_sd(p, scenario, base_city, centres, rec,
                              new=float(prior_pr_share.get(p, 0.0) or 0.0) <= 0.0)
           for p, v in centres.items() if v > 0 and p != 'ENTRANT'}
    u = {p: ((centres[p] * s) ** 2 if a.arm == 'V' else centres[p] * s ** 2)
         for p, s in sig.items()}
    for p, v in centres.items():
        if v > 0 and p not in u:
            u[p] = 0.0
    new, held = take_excess(centres, u)
    log[KEY] = {'sum_before': sum(v for v in centres.values() if v > 0),
                'held': held,
                'moved': {p: [centres[p], new[p], sig.get(p)] for p in centres
                          if centres[p] > 0.001}}
    return new, notes


rows = json.loads((R / 'data/processed/history.json').read_text())['records']
jobs = [(r['slug'], str(r['year'])) for r in rows]
if a.only:
    jobs = [tuple(a.only.split(':'))]
if a.arm != 'P':
    M.blended_centres = wrapped
results = {}
for slug, year in jobs:
    KEY, YEAR = f'{slug}-{year}', year
    row = CH.run_city_year(slug, year, 1000, DATA, overrides=[])
    results[KEY] = {k: row[k] for k in ('pr_mae', 'ward_mae', 'seat_abs_err', 'wards', 'votes', 'seats')}
    print(a.arm, KEY, round(row['pr_mae'], 4), row['seat_abs_err'], flush=True)
    (W / f'{a.arm}.json').write_text(json.dumps({'results': results, 'log': log}, indent=1, default=str))
