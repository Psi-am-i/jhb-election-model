"""Instruments 1-5 of prereg/2026-10-20-byelection-weight-measured.md, over the
arm files sweep.py wrote. Reads only; prints the report and writes
`<work>/sweep/analysis.json`.

    .venv/bin/python audits/2026-10-20-byelection-weight-measured/analyze.py --work DIR
"""
import argparse, json, math, os, re, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import cityconfig as C
import levels

SLUGS = ['joburg', 'tshwane', 'ekurhuleni', 'capetown', 'ethekwini',
         'nelsonmandelabay', 'buffalocity', 'mangaung']
REACHED = ['joburg', 'ekurhuleni', 'capetown', 'ethekwini', 'nelsonmandelabay', 'mangaung']
DATA = R / 'data/raw/elections'

ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True)
W = ap.parse_args().work.resolve(); S = W / 'sweep'
arms = {p.stem: json.loads(p.read_text()) for p in S.glob('*.json') if p.stem != 'analysis'}
grid = sorted((float(k[1:]), k) for k in arms if k.startswith('g'))
out = {}


def pr(arm, slug):
    return arms[arm][slug]['pr_mae']


def seats_wrong(arm):
    return sum(arms[arm][s]['seat_abs_err'] for s in SLUGS) / 2


def wards_wrong(arm):
    w = [arms[arm][s]['wards'] for s in SLUGS]
    return sum(x['n_wards'] - x['called'] for x in w)


# 1. the curve
print('1. summed pr_mae over 8 metros (points) | wards wrong | seats to wrong party')
curve = {}
for w, k in grid:
    curve[w] = sum(pr(k, s) for s in SLUGS)
    print(f'   w={w:<6g} {curve[w]:7.3f} | {wards_wrong(k):3d} | {seats_wrong(k):6.1f}')
for k in (x for x in arms if not x.startswith('g')):
    print(f'   {k:<8} {sum(pr(k, s) for s in SLUGS):7.3f} | {wards_wrong(k):3d} | {seats_wrong(k):6.1f}')
wmin = min(curve, key=curve.get)
flat = [w for w in curve if curve[w] <= curve[wmin] + 0.3]
print(f'   minimum at w={wmin:g}; within 0.3 of it: {min(flat):g}-{max(flat):g}')
out['curve'] = curve; out['w_min'] = wmin; out['flat_0.3'] = [min(flat), max(flat)]

# 2. leave one metro out
print('2. leave one metro out (grid choice on the other seven; held-out pr_mae)')
lomo = {}
for m in REACHED:
    rest = {w: sum(pr(k, s) for s in SLUGS if s != m) for w, k in grid}
    wm = min(rest, key=rest.get); k = dict(grid)[wm]
    lomo[m] = {'w': wm, 'held_out': pr(k, m), 'at_half': pr('g0.5', m), 'at_zero': pr('g0.0', m)}
    print(f'   {m:<17} w={wm:<6g} held-out {lomo[m]["held_out"]:.3f} | at 0.5 {lomo[m]["at_half"]:.3f} | at 0 {lomo[m]["at_zero"]:.3f}')
ws = [v['w'] for v in lomo.values()]
tot = {key: sum(v[key] for v in lomo.values()) for key in ('held_out', 'at_half', 'at_zero')}
print(f'   chosen range {min(ws):g}-{max(ws):g}; summed held-out {tot["held_out"]:.3f} vs fixed 0.5 {tot["at_half"]:.3f} vs fixed 0 {tot["at_zero"]:.3f}')
out['lomo'] = lomo; out['lomo_totals'] = tot


# 3. least-squares slope on forecast shares
def prev_share(slug):
    city = C.use(slug); t = C.use_target('2021')
    return levels._citywide(DATA / t.results('2016').replace('{CODE}', city.code))


def rows(slug):
    a0 = {r[0]: r for r in arms['g0.0'][slug]['votes']}
    a1 = {r[0]: r for r in arms['g1.0'][slug]['votes']}
    for p in a0:
        if p in a1 and all(isinstance(x, (int, float)) and not math.isnan(x)
                           for x in (a0[p][2], a1[p][2], a0[p][3])):
            yield p, a0[p][3] - a0[p][2], a1[p][2] - a0[p][2]


def slope(pairs):
    sdd = sum(d * d for _, e, d in pairs)
    return sum(e * d for _, e, d in pairs) / sdd if sdd > 1e-12 else None


print('3. least-squares slope w* = sum(e d)/sum(d^2) on forecast list shares (w=0 vs w=1)')
prev = {s: prev_share(s) for s in REACHED}
allpairs = {s: [(p, e, d) for p, e, d in rows(s)] for s in REACHED}
groups = {'pooled': lambda s, p: True,
          'under 1%': lambda s, p: prev[s].get(p, 0) < 0.01,
          'at or over 1%': lambda s, p: prev[s].get(p, 0) >= 0.01,
          'under 10%': lambda s, p: prev[s].get(p, 0) < 0.10,
          'at or over 10%': lambda s, p: prev[s].get(p, 0) >= 0.10}
out['slope'] = {}
for g, f in groups.items():
    sel = {s: [x for x in allpairs[s] if f(s, x[0]) and abs(x[2]) > 1e-9] for s in REACHED}
    full = slope([x for s in REACHED for x in sel[s]])
    lo = {m: slope([x for s in REACHED if s != m for x in sel[s]]) for m in REACHED}
    n = sum(len(v) for v in sel.values())
    vals = [v for v in lo.values() if v is not None]
    rng = (min(vals), max(vals)) if vals else (None, None)
    out['slope'][g] = {'w': full, 'n_parties': n, 'lomo': lo, 'range': rng}
    fmt = lambda v: 'n/a' if v is None else f'{v:.3f}'
    print(f'   {g:<15} w*={fmt(full)} over {n} party-metros; leave-one-out {fmt(rng[0])}-{fmt(rng[1])}')

# 4. the cap: uncapped vs capped by-election level, from a w>0 trace's notes
print('4. cap: slope on (by-election level - model level), capped vs uncapped, from 30_centres notes')
NOTE = re.compile(r'level ([\d.]+)% → [\d.]+% \(by-elections imply ([\d.]+)%(?:.*?clamped to ([\d.]+)%)?')
cap = {}
for s in REACHED:
    tr = json.loads((W / 'sweep-trace' / 'g0.5' / f'{s}-2021' / '30_centres.json').read_text())
    a0 = {r[0]: r for r in arms['g0.0'][s]['votes']}
    for p, note in tr['route_notes'].items():
        m = NOTE.search(note)
        if not m or p not in a0 or math.isnan(a0[p][3]):
            continue
        lvl, imp = float(m[1]) / 100, float(m[2]) / 100
        clp = float(m[3]) / 100 if m[3] else imp
        cap.setdefault(s, []).append((p, a0[p][3] - lvl, clp - lvl, imp - lvl))
out['cap'] = {}
for which, i in (('capped', 2), ('uncapped', 3)):
    pairs = [(p, e, x[i]) for s in cap for x in cap[s] for p, e in [(x[0], x[1])]]
    w = slope(pairs)
    per = {}
    for s in cap:
        ps = [(x[0], x[1], x[i]) for x in cap[s]]
        per[s] = sum((e - w * d) ** 2 for _, e, d in ps)
    out['cap'][which] = {'w': w, 'sse_by_metro': per, 'sse': sum(per.values())}
    print(f'   {which:<9} w*={w:.3f}  pooled squared error {sum(per.values()) * 1e4:.2f} (points^2)')
better = [s for s in cap if out['cap']['uncapped']['sse_by_metro'][s] < out['cap']['capped']['sse_by_metro'][s]]
print(f'   uncapped has lower squared error in {len(better)} of {len(cap)} metros: {better}')
out['cap']['uncapped_better_in'] = better

# per-metro table
print('per metro pr_mae by grid weight')
for s in SLUGS:
    print(f'   {s:<17}' + ' '.join(f'{pr(k, s):5.2f}' for _, k in grid))
print('   weights          ' + ' '.join(f'{w:5g}' for w, _ in grid))
(S / 'analysis.json').write_text(json.dumps(out, indent=1, default=str))
