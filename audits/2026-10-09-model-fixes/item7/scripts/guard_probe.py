"""Prototype of the group-share guard, as a probe (no code edited).

Quantity: each party's REALISED share of each pool's vote in each draw (the
within-pool Dirichlet split, after the IPF balance) -- what reaches the votes.
Population: every (party, pool) with weight > 0 in the pool spec; asserted equal
to the scanned set.
Threshold per (party, pool): record(p,g) + margin(g), where
  record(p,g) = the party's largest Duncan-Davis UPPER bound in pool g in any real
                metro result before the target (0 if it has none: an arrival);
  margin(g)   = options: 0; the largest real one-cycle rise of any party's FITTED
                rate in pool g before the target; the largest PROVEN rise
                (DD lower now minus DD upper before).
Also reports the floor side for parties with a record: realised < the party's
smallest DD LOWER bound minus the pool's largest proven fall (option only).
usage: guard_probe.py DRAWS OUT.json"""
import sys, json, collections
sys.path.insert(0, '/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-09-model-fixes/item7/scripts')
from capture import *
import numpy as np
from unittest import mock

PANEL = json.load(open('/Users/simondavis/.claude/jobs/26965cd4/tmp/item7/panel_rates.json'))
NPE = json.load(open('/Users/simondavis/.claude/jobs/26965cd4/tmp/item7/panel_2024.json'))
YR = lambda y: 2024 if y == '2024n' else int(y)

def thresholds(target_year, city='joburg'):
    # RECORD: this city's own real results (LGE and the 2024 national), before the target.
    own = [r for r in PANEL + NPE if r['city'] == city and YR(r['year']) < int(target_year)]
    rec = collections.defaultdict(float)
    for r in own: rec[(r['party'], r['pool'])] = max(rec[(r['party'], r['pool'])], r['dd_hi'])
    # MARGIN: largest one-cycle rise of a fitted LGE rate, any metro, before the target.
    rows = [r for r in PANEL if int(r['year']) < int(target_year)]
    idx = {(r['city'], r['year'], r['party'], r['pool']): r for r in rows}
    rise = collections.defaultdict(float); proven = collections.defaultdict(float)
    for (c, y, p, g), r in idx.items():
        prev = {'2016': '2011', '2021': '2016'}.get(y)
        if not prev: continue
        a = idx.get((c, prev, p, g))
        rise[g] = max(rise[g], r['rate'] - (a['rate'] if a else 0.0))
        proven[g] = max(proven[g], r['dd_lo'] - (a['dd_hi'] if a else 0.0))
    return rec, rise, proven

def scan(cap, target_year, label):
    rec, rise, proven = thresholds(target_year)
    spec = cap['spec']
    population = {(p, g) for g in cap['names'] for p, w in spec[g][7].items() if w > 0}
    scanned = {(p, g) for g in cap['names'] for p in cap['shares'][g]}
    assert population <= scanned, 'scanned the wrong set'
    scanned = {k for k in scanned if k in population}
    assert scanned == population
    out = {'population': len(population), 'with_record': sum(1 for k in population if rec.get(k, 0) > 0),
           'margins': {'rise': dict(rise), 'proven': dict(proven)}, 'fires': {}}
    D = len(next(iter(cap['shares'][cap['names'][0]].values())))
    for mname, M in [('none', {}), ('rise', rise), ('proven', proven)]:
        hits = {}
        any_draw = np.zeros(D, bool)
        for (p, g) in population:
            thr = rec.get((p, g), 0.0) + M.get(g, 0.0)
            x = cap['shares'][g][p]
            f = x > thr
            if f.any():
                hits[f'{p}|{g}'] = dict(draw_frac=round(float(f.mean()), 4), thr=round(thr, 4), median=round(float(np.median(x)), 4))
                any_draw |= f
        out.setdefault('pa_da', {})[mname] = {k: hits.get(k) for k in ('PA|Coloured', 'PA|Black African', 'PA|White', 'PA|Indian/Asian', 'MK|Black African')}
        out['fires'][mname] = dict(pairs_firing=len(hits), draws_with_any=round(float(any_draw.mean()), 4),
                                   top=dict(sorted(hits.items(), key=lambda kv: -kv[1]['draw_frac'])[:8]))
    print(f'--- {label}: population {out["population"]} pairs ({out["with_record"]} with a record)')
    for m, v in out['fires'].items():
        print(f'   margin {m:6s}: {v["pairs_firing"]} pairs fire; draws with any firing {v["draws_with_any"]:.3f}; top {list(v["top"].items())[:5]}')
        print(f'        PA/MK: {out["pa_da"][m]}')
    return out

if __name__ == '__main__':
    draws = int(sys.argv[1]); res = {}
    run, cap = run_capture(draws=draws); res['live_2026'] = scan(cap, '2026', 'live 2026')
    o = mc.compress_levels
    def x12(c, s):
        out = dict(o(c, s)); out['PA'] = out['PA'] * 12; return out
    run, cap = run_capture(draws=draws, patches=[mock.patch.object(mc, 'compress_levels', x12)])
    i = run.universe.index('PA')
    print('x12 PA mean list share', run.pr_share_draws[:, i].mean(), 'existing counters', {k: run.guards.get(k) for k in ('ipf_clipped', 'cap_moved', 'cap_undershoots', 'ipf_failures')})
    res['x12_2026'] = scan(cap, '2026', 'constructed x12 PA centre')
    def inrange(c, s):
        out = dict(o(c, s)); S = sum(v for v in out.values() if v > 0); c0 = out['PA']; x = 0.0293
        out['PA'] = x * (S - c0) / (1 - x); return out
    run, cap = run_capture(draws=draws, patches=[mock.patch.object(mc, 'compress_levels', inrange)])
    res['reverted_PA_at_record'] = scan(cap, '2026', 'reverted: PA centre at its record (drawn ~2.8%)')
    json.dump(res, open(sys.argv[2], 'w'), indent=1)
