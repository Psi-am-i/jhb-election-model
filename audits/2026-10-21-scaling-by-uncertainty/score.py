"""Scores arms P, V, H of prereg/2026-10-21-scaling-by-uncertainty.md from
<work>/<arm>.json. Reads only; prints the report.

    .venv/bin/python audits/2026-10-21-scaling-by-uncertainty/score.py --work DIR
"""
import argparse, json, math, os, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig as C
import levels

ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True)
W = ap.parse_args().work.resolve()
arms = {a: json.loads((W / f'{a}.json').read_text()) for a in 'PVH' if (W / f'{a}.json').exists()}
res = {a: d['results'] for a, d in arms.items()}
keys = list(res['P'])
hist = {f"{r['slug']}-{r['year']}": r for r in
        json.loads((R / 'data/processed/history.json').read_text())['records']}

# S1 control
d = max(abs(res['P'][k]['pr_mae'] - hist[k]['pr_mae']) for k in keys)
same = all(res['P'][k]['seat_abs_err'] == hist[k]['seat_abs_err'] for k in keys)
print(f'S1 control: max |pr_mae - history| {d:.2e}; seat errors identical {same}')


def wrong(row):
    return row['wards']['n_wards'] - row['wards']['called']


def prev(key):
    slug, year = key.rsplit('-', 1)
    city = C.use(slug); t = C.use_target(year)
    return levels._citywide(R / 'data/raw/elections' /
                            t.results(t.previous_lge).replace('{CODE}', city.code))


prevs = {k: prev(k) for k in keys}
print('\narm | summed pr_mae (24) | 2011 | 2016 | 2021 | wards wrong | seats to wrong party | new parties signed (pts) | top-3 signed (pts)')
for a, r in res.items():
    by = {y: sum(r[k]['pr_mae'] for k in keys if k.endswith(y)) for y in ('2011', '2016', '2021')}
    new_s = top_s = 0.0
    for k in keys:
        rows = [v for v in r[k]['votes'] if not math.isnan(v[2]) and not math.isnan(v[3])]
        for v in rows:
            if prevs[k].get(v[0], 0) <= 0:
                new_s += (v[2] - v[3]) * 100
        for v in sorted(rows, key=lambda v: -v[3])[:3]:
            top_s += (v[2] - v[3]) * 100
    print(f'{a} | {sum(r[k]["pr_mae"] for k in keys):.3f} | {by["2011"]:.3f} | {by["2016"]:.3f} | '
          f'{by["2021"]:.3f} | {sum(wrong(r[k]) for k in keys)} | '
          f'{sum(r[k]["seat_abs_err"] for k in keys) / 2:.1f} | {new_s:+.2f} | {top_s:+.2f}')

print('\nper city-year pr_mae: P / V / H')
for k in keys:
    print(f'  {k:24} ' + ' / '.join(f'{res[a][k]["pr_mae"]:.2f}' for a in res))
for a in ('V', 'H'):
    if a in arms:
        held = {k: v['held'] for k, v in arms[a]['log'].items() if v['held']}
        print(f'\n{a}: parties held at the floor: {held}')
