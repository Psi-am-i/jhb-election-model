import sys, copy, json, csv, io, contextlib, numpy as np
sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc, levels, pools
G='/Users/simondavis/.claude/jobs/26965cd4/tmp/integrity/guards/'
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
def run(draws=100, **kw):
    sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = draws; sc['seed'] = 20261104; sc.update(kw)
    buf=io.StringIO()
    with contextlib.redirect_stdout(buf):
        r = mc.run_model(target, sc, verbose=False)
    return r, buf.getvalue()
which = sys.argv[1]
if which == 'G1':   # capacity clip: ask PA for 12x its centre
    orig = mc.compress_levels
    def big(c, s):
        out = orig(c, s); out = dict(out); out['PA'] = out['PA'] * 12; return out
    mc.compress_levels = big
    r, log = run()
    i = r.universe.index('PA')
    print('G1 constructed: ipf_clipped', r.guards['ipf_clipped'].get('PA'), 'cap_moved', r.guards['cap_moved'], 'undershoots', r.guards['cap_undershoots'], 'ipf_failures', r.guards['ipf_failures'], 'PA mean list share', r.pr_share_draws[:, i].mean(), 'headroom', r.guards['ipf_headroom'].get('PA'))
    mc.compress_levels = orig
    r, log = run()
    print('G1 control: ipf_clipped', r.guards['ipf_clipped'], 'cap_moved', r.guards['cap_moved'])
if which == 'G2':   # PLAN_BOUNDS sanity counter
    keep = dict(mc.PLAN_BOUNDS); print('declared PLAN_BOUNDS', keep)
    mc.apply_city = lambda c: None
    mc.PLAN_BOUNDS = {'DA': (100.0, 200.0)}
    r, _ = run(50); print('G2 impossible DA bound: violations', r.guards['bounds_violations'], 'checked', r.guards['bounds_checked'])
    mc.PLAN_BOUNDS = {'DA': (0.0, 1e9)}
    r, _ = run(50); print('G2 vacuous bound: violations', r.guards['bounds_violations'], 'checked', r.guards['bounds_checked'])
    mc.PLAN_BOUNDS = {}
    r, _ = run(50); print('G2 no bounds at all: violations', r.guards['bounds_violations'], 'checked', r.guards['bounds_checked'], '<- control counts draws, not checks')
    mc.PLAN_BOUNDS = keep
if which == 'G3':   # levels._citywide on an unreadable (renamed-column) file
    src = 'data/raw/elections/lge2021_JHB_vd_party_clean.csv'
    good = levels._citywide(src); print('G3 control: parties read', len(good))
    out = G + 'lge2021_JHB_vd_party_clean.csv'
    with open(src, encoding='utf-8') as f, open(out, 'w', encoding='utf-8') as g:
        hdr = f.readline().replace('sPartyName', 'PartyName'); g.write(hdr)
        for k, line in enumerate(f):
            if k > 20000: break
            g.write(line)
    print('G3 renamed column -> _citywide returns', levels._citywide(out), '(no exception)')
    import os
    print('G3 missing file ->', end=' ')
    try: print(levels._citywide(G + 'lge2016_JHB_vd_party_clean.csv'))
    except BaseException as e: print('REFUSED:', type(e).__name__, str(e)[:160])
if which == 'G4':   # pool spec staleness
    spec = json.load(open('data/processed/pools_2026.json'))
    print('G4 control stale_reason:', pools.stale_reason(spec, city, target))
    s2 = copy.deepcopy(spec); s2['artefact_key']['judgements_sha'] = '0000000000000000'
    print('G4 altered judgements_sha:', (pools.stale_reason(s2, city, target) or '')[:200])
    orig = pools.stale_reason
    pools.stale_reason = lambda *a, **k: 'CONSTRUCTED: spec is stale'
    r, log = run(20)
    print('G4 run with a stale spec: completed', r.draws, 'draws; _pools_stale =', r.scenario.get('_pools_stale'), '| printed:', [l for l in log.splitlines() if 'STALE' in l][:1])
    def boom(*a, **k): raise RuntimeError('constructed failure inside stale_reason')
    pools.stale_reason = boom
    r, log = run(20)
    print('G4 run when the staleness check itself crashes: completed', r.draws, 'draws; _pools_stale =', str(r.scenario.get('_pools_stale'))[:120])
    pools.stale_reason = orig
if which == 'G5':   # a large party in no pool
    orig = mc.make_drawer
    def drop(sc, b, c, idx, rng):
        for cfg in sc['pools'].values(): cfg['members'].pop('MK', None)
        return orig(sc, b, c, idx, rng)
    mc.make_drawer = drop
    r, log = run(50)
    i = r.universe.index('MK')
    print('G5 MK removed from every pool: run completed', r.draws, 'draws; MK mean list share', round(r.pr_share_draws[:, i].mean(), 4), '| printed:', [l.strip() for l in log.splitlines() if 'in no pool' in l])
if which == 'G6':   # roster: a spec that claims a roster source but carries none
    for case in ({'_pools_roster_source': 'declared', '_pools_roster': []},
                 {'_pools_roster_source': 'declared', '_pools_roster': None},
                 {'_pools_roster_source': None, '_pools_roster': None}):
        try:
            ro, st = mc.roster_for_target(target, dict(case)); print('G6', case, '->', st, len(ro))
        except BaseException as e:
            print('G6', case, '-> REFUSED', type(e).__name__, str(e)[:100])
