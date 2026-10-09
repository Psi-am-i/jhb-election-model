"""Reconstruct the yearly within-pool splits that pools.dirichlet_alpha is fitted on (pools.py ~6334-6360), from the emitted
2026 spec's member weights, and re-derive each pool's alpha as a check."""
import os, sys, json
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0,'src')
import numpy as np
import cityconfig, pools
cityconfig.use('joburg'); cityconfig.use_target('2026')
spec = json.load(open('data/processed/pools_2026.json'))
cats = list(spec['pools'])
parties = sorted({p for g in cats for p in spec['pools'][g]['members']})
comp = {p: [spec['pools'][g]['members'].get(p, 0.0) for g in cats] for p in parties}
tr = pools.lge_transitions(before='2026')
years = sorted({y for pair in tr for y in pair}, key=int)
print('transitions', tr, 'years', years)
splits = {g: [] for g in cats}; labels = {g: [] for g in cats}
for code in pools.METRO_CODES:
    for y in years:
        sh = pools.metro_citywide(code, y)
        if not sh: continue
        for gi, g in enumerate(cats):
            c = np.array([comp[p][gi] * sh.get(p, 0.0) for p in parties])
            if c.sum() > 0:
                splits[g].append(c / c.sum()); labels[g].append(f'{code}{y}')
out = {}
for g in cats:
    a = pools.dirichlet_alpha(splits[g])
    print(g, 'n splits', len(splits[g]), 'alpha re-derived', round(a, 4), 'spec', round(spec['pools'][g]['alpha'], 4))
    arr = np.array(splits[g])
    out[g] = {'labels': labels[g], 'parties': parties, 'splits': arr.tolist(), 'alpha': a}
    # members that enter the estimate
    m = arr.mean(0); v = arr.var(0, ddof=1)
    use = (v > 1e-12) & (m > pools.ALPHA_MIN_SHARE) & (m < 1 - 1e-4)
    est = m[use] * (1 - m[use]) / v[use] - 1
    for p, mm, e in sorted(zip(np.array(parties)[use], m[use], est), key=lambda x: -x[1]):
        print(f'   uses {p:<10s} mean share {mm*100:6.2f}%  own alpha {e:8.2f}')
json.dump(out, open('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/hist_splits.json', 'w'))
