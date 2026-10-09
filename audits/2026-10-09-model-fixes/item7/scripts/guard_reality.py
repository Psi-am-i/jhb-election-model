"""Would REAL results have tripped the guard? For each LGE target (2016, 2021),
thresholds from results strictly before it (records: LGE + NPE-2024 rows where
dated before; margins: LGE one-cycle rises before it), applied to each real
(party, pool, metro) outcome at the target: its fitted rate (estimate) and its
DD lower bound (proven). Also prints the 2026 thresholds for the PA and MK."""
import json, collections, sys
P = json.load(open('/Users/simondavis/.claude/jobs/26965cd4/tmp/item7/panel_rates.json'))
N = json.load(open('/Users/simondavis/.claude/jobs/26965cd4/tmp/item7/panel_2024.json'))
yr = lambda y: 2024 if y == '2024n' else int(y)
def thr(target):
    # record is per city: (city, party, pool) -> largest DD upper bound in that city's own results before target
    rows = [r for r in P + N if yr(r['year']) < target]
    rec = collections.defaultdict(float)
    for r in rows: rec[(r['city'], r['party'], r['pool'])] = max(rec[(r['city'], r['party'], r['pool'])], r['dd_hi'])
    idx = {(r['city'], r['year'], r['party'], r['pool']): r for r in P if int(r['year']) < target}
    rise = collections.defaultdict(float)
    for (c, y, p, g), r in idx.items():
        prev = {'2016': '2011', '2021': '2016'}.get(y)
        if prev and (c, prev, p, g) in idx or prev:
            a = idx.get((c, prev, p, g)); rise[g] = max(rise[g], r['rate'] - (a['rate'] if a else 0.0))
    return rec, rise
out = {}
for target in (2016, 2021):
    rec, rise = thr(target)
    real = [r for r in P if int(r['year']) == target]
    fit_hits = [r for r in real if r['rate'] > rec.get((r['city'], r['party'], r['pool']), 0) + rise.get(r['pool'], 0)]
    pro_hits = [r for r in real if r['dd_lo'] > rec.get((r['city'], r['party'], r['pool']), 0) + rise.get(r['pool'], 0)]
    out[target] = dict(n=len(real), margins=dict(rise), fitted_exceed=[(r['city'], r['party'], r['pool'], round(r['rate'], 3), round(rec.get((r['city'], r['party'], r['pool']), 0) + rise.get(r['pool'], 0), 3)) for r in fit_hits],
                       proven_exceed=[(r['city'], r['party'], r['pool'], round(r['dd_lo'], 3)) for r in pro_hits])
    print(target, 'real (party,pool,metro) outcomes', len(real), 'margins', {k: round(v, 3) for k, v in rise.items()})
    print('   fitted rate above threshold:', len(fit_hits), out[target]['fitted_exceed'] if target == 2021 else '(list omitted)')
    print('   PROVEN (DD lower) above threshold:', len(pro_hits), out[target]['proven_exceed'])
rec, rise = thr(2026)
print('2026 margins', {k: round(v, 3) for k, v in rise.items()})
for p in ('PA', 'MK', 'DA', 'ANC', 'ASA', 'EFF'):
    print('2026 joburg', p, {g: (round(rec.get(('joburg', p, g), 0), 3), round(rec.get(('joburg', p, g), 0) + rise[g], 3)) for g in rise})
json.dump(out, open(sys.argv[1], 'w'), indent=1)
