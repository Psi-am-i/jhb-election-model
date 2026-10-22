import sys, json; sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
from harness import *
from unittest import mock
cap = {}
orig = M.make_drawer
def wrap(scenario, base_city_d, centres, index, rng):
    f = orig(scenario, base_city_d, centres, index, rng)
    def cells(fn, seen):
        out = {}
        if fn in seen or not hasattr(fn, '__closure__') or not fn.__closure__: return out
        seen.add(fn)
        for name, c in zip(fn.__code__.co_freevars, fn.__closure__):
            try: v = c.cell_contents
            except ValueError: continue
            out[name] = v
            if callable(v) and hasattr(v, '__closure__'): out.update({k: x for k, x in cells(v, seen).items() if k not in out})
        return out
    cap.update(cells(f, set())); cap['centres'] = dict(centres); cap['base_city_d'] = dict(base_city_d); cap['scenario'] = scenario
    return f
year = sys.argv[1] if len(sys.argv) > 1 else '2026'; city = sys.argv[2] if len(sys.argv) > 2 else 'joburg'
t, r = run(city=city, year=year, draws=int(sys.argv[3]) if len(sys.argv)>3 else 200, patches=[mock.patch.object(M, 'make_drawer', wrap)])
sc = cap['scenario']
seeds = sc.get('pool_seeds') or {}
theta_sd = sc.get('_theta_sd') or {}
pss = cap.get('pool_sd_shock', {}); ipf = cap.get('ipf') or {}
ipf_parties = set(ipf.get('parties') or [])
handled = cap.get('handled', set())
indiv = {r.universe[i]: (tri, lvl) for i, tri, lvl in cap.get('individual', [])}
rows = []
for p in r.universe:
    pools_of = [n for n, cfg in sc['pools'].items() if p in cfg['members']]
    rows.append(dict(party=p, centre=cap['centres'].get(p), base=cap['base_city_d'].get(p), in_pool=p in handled,
                     pools=pools_of, seeded=seeds.get(p, 0) > 0, seed=seeds.get(p, 0), theta_sd=theta_sd.get(p),
                     pool_sd_shock=pss.get(p), in_ipf=p in ipf_parties, individual=p in indiv,
                     indiv_spec=str(indiv.get(p))))
json.dump(dict(rows=rows, keys=sorted(k for k in cap if k not in ('scenario',)), sd_default=sc.get('level_sd_default'),
               seed_bands={k: v for k, v in (sc.get('pool_seed_bands') or {}).items()}), open(f'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/canary_{city}_{year}.json', 'w'), default=str, indent=0)
z = [x for x in rows if not x['pool_sd_shock'] and x['in_pool']]
print('universe', len(rows), 'in pool', sum(x['in_pool'] for x in rows), 'individual', sum(x['individual'] for x in rows))
print('pooled with sd 0:', len(z), ' of which seeded:', sum(x['seeded'] for x in z), ' not in ipf:', sum(not x['in_ipf'] for x in z))
print('pooled not in ipf at all:', [x['party'] for x in rows if x['in_pool'] and not x['in_ipf']])
print('sd>0 parties:', sum(1 for x in rows if x['pool_sd_shock']))
for x in sorted(rows, key=lambda x: -(x['centre'] or 0))[:80]:
    print(f"{x['party'][:34]:<34s} centre {100*(x['centre'] or 0):6.3f} base {100*(x['base'] or 0):6.3f} seeded {x['seeded']!s:5s} seed {100*x['seed']:6.3f} theta_sd {x['theta_sd']} shock_sd {x['pool_sd_shock']} ipf {x['in_ipf']} pools {','.join(x['pools'])[:40]}")
