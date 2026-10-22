"""Candidate corrections for item 7, as monkeypatches, alone and on item 6.
usage: variants.py DRAWS OUT.json [ids...]"""
import sys, json, math
sys.path.insert(0, '/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-09-model-fixes/item7/scripts')
sys.path.insert(0, '/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-09-model-questions/data/scripts')
from capture import *
from unittest import mock
import levels, votecov

PA_NAT, PA_LOC, W_LOCAL = None, None, None
_o_spine = levels.spine
def spine_with(mt, mr):
    def f(target, baseline, prev_local, *a, **k):
        lv, info = _o_spine(target, baseline, prev_local, *a, **k)
        d = info['detail']['PA']; w = d['w_local']
        nat = baseline['PA'] * mt; loc = prev_local['PA'] * mr
        lv = dict(lv); lv['PA'] = math.exp(w * math.log(loc) + (1 - w) * math.log(nat))
        return lv, info
    return f

_o_cl = mc.compress_levels
def centre_for_mean(x):
    def f(c, s):
        out = dict(_o_cl(c, s)); S = sum(v for v in out.values() if v > 0); c0 = out['PA']
        out['PA'] = x * (S - c0) / (1 - x); return out
    return f

_o_ps = mc.pool_spec
def vector_outside(x):
    def f(scenario, centres, index, ipf_out=None):
        P = scenario['pools']
        if not scenario.get('_item7_vec'):
            vol = {g: float(P[g]['registered']) * float(P[g]['turnout'][1]) for g in P}
            others = [g for g in P if g != 'Coloured']; tv = sum(vol[g] for g in others)
            P['Coloured']['members']['PA'] = 1 - x
            for g in others: P[g]['members']['PA'] = x * vol[g] / tv
            scenario['_item7_vec'] = True
        return _o_ps(scenario, centres, index, ipf_out)
    return f

CANDS = {
    'base': ([], {}),
    'a1': ([('pool_spec', vector_outside(0.037))], {}),
    'a2': ([('pool_spec', vector_outside(0.16))], {}),
    'b1': ([('spine', spine_with(1.074, 0.826))], {}),
    'b2': ([('spine', spine_with(0.921, 0.762))], {}),
    'c': ([], {'w_bye': 0.0}),
    'd1': ([('compress_levels', centre_for_mean(0.0293))], {}),
    'd2': ([('compress_levels', centre_for_mean(0.0565))], {}),
    'a2+b1': ([('pool_spec', vector_outside(0.16)), ('spine', spine_with(1.074, 0.826))], {}),
}
def patches_for(spec, item6):
    ps = []
    for kind, fn in spec:
        if kind == 'spine': ps.append(mock.patch.object(levels, 'spine', fn))
        elif kind == 'compress_levels': ps.append(mock.patch.object(mc, 'compress_levels', fn))
    if item6: ps.append(mock.patch.object(levels, 'contestation', votecov.make('2026')))
    return ps

draws = int(sys.argv[1]); outp = sys.argv[2]; ids = sys.argv[3:] or list(CANDS)
res = {}
for cid in ids:
    for item6 in (False, True):
        spec, scen = CANDS[cid]
        # pool_spec wrapper must sit UNDER capture's own wrapper: install on mc before run_capture reads it
        vec = [fn for kind, fn in spec if kind == 'pool_spec']
        if vec: mc.pool_spec = vec[0]
        try:
            run, cap = run_capture(draws=draws, scen=scen, patches=patches_for(spec, item6))
        finally:
            mc.pool_spec = _o_ps
        key = cid + ('+item6' if item6 else '')
        r = {p: pa_summary(run, cap, p, 'Coloured') for p in ['PA', 'DA', 'ANC']}
        i = run.universe.index('PA')
        r['PA']['ward_share_mean'] = float(run.ward_share_draws[:, i].mean())
        r['PA']['wins_mean'] = float((run.ward_winner_draws == i).sum(1).mean())
        r['guards'] = {k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items() if kk in ('PA', 'DA')}) for k, v in run.guards.items() if k in ('ipf_clipped', 'cap_moved', 'ipf_failures')}
        res[key] = r
        print(f"{key:14s} PA seats {r['PA']['seats_mean']:6.2f} list {r['PA']['list_share_mean']*100:5.2f}% Col-rate med {r['PA']['rate_in_group_p5_50_95'][1]:.3f} [{r['PA']['rate_in_group_p5_50_95'][0]:.3f},{r['PA']['rate_in_group_p5_50_95'][2]:.3f}] | DA seats {r['DA']['seats_mean']:6.2f} list {r['DA']['list_share_mean']*100:5.2f}% DA Col-rate med {r['DA']['rate_in_group_p5_50_95'][1]:.3f} | ANC seats {r['ANC']['seats_mean']:6.2f}", flush=True)
        json.dump(res, open(outp, 'w'), indent=1)
