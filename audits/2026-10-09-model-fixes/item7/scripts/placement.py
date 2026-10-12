"""Where the model puts the PA's 2026 list votes, by the Coloured share of
voters in each VD's 2021 ward, against where the real 2021 and 2024 PA votes
fell. In-process; nothing written outside scratch/audit dir."""
import sys, os, json, io, contextlib, csv, copy
from collections import defaultdict
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as mc, pools
city = cityconfig.use('joburg'); cfg = pools.load_config()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    fits, ctx = pools.fit_city(city, '2021', cfg)
ci = list(ctx['categories']).index('Coloured'); cw = dict(zip(ctx['wards'], ctx['comp'][:, ci]))
vd_ward = {}
for r in csv.DictReader(open('data/raw/elections/lge2021_JHB_vd_party_clean.csv', encoding='utf-8')):
    vd_ward[r['VD_Number']] = r['Ward']
def cls(vd):
    w = vd_ward.get(vd); c = cw.get(w)
    if c is None: return 'unmapped'
    return 'majority' if c >= .5 else ('10-50%' if c >= .1 else '<10%')
# real
real = {}
for yr, f, bt in [('2021', 'data/raw/elections/lge2021_JHB_vd_party_clean.csv', 'PR'), ('2024', 'data/raw/elections/npe2024_JHB_vd_party.csv', None)]:
    acc = defaultdict(float)
    for r in csv.DictReader(open(f, encoding='utf-8')):
        if bt and r['BallotType'] != bt: continue
        if r['sPartyName'].strip() == 'PATRIOTIC ALLIANCE': acc[cls(r['VD_Number'])] += float(r['Party_Votes'] or 0)
    T = sum(acc.values()); real[yr] = {k: round(v / T, 4) for k, v in acc.items()}
print('real PA vote by class', real)
# model
target = cityconfig.use_target('2026'); mc.apply_city(city)
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = int(sys.argv[1]); sc['seed'] = 20261104
got = []; fr = {}
orig = mc.solve_and_predict
def wrap(dev, base_city, tgt, gamma, weight, *a, **k):
    out = orig(dev, base_city, tgt, gamma, weight, *a, **k)
    f = sys._getframe(1).f_locals
    if not fr: fr['vds'] = list(f['vds'])
    if len(got) % 2 == 0 or True: got.append((out, weight.copy()))
    return out
mc.solve_and_predict = wrap
with contextlib.redirect_stdout(io.StringIO()):
    run = mc.run_model(target, sc, verbose=False)
mc.solve_and_predict = orig
i = run.universe.index('PA'); vds = fr['vds']; klass = np.array([cls(v) for v in vds])
pr_calls = got[0::2]
fr_by = defaultdict(list)
for out, w in pr_calls:
    v = w * out[:, i]; T = v.sum()
    for k in set(klass): fr_by[k].append(v[klass == k].sum() / T)
model = {k: [round(float(x), 4) for x in np.percentile(v, [5, 50, 95])] for k, v in fr_by.items()}
print('model PA list vote by class (p5/50/95):', model)
json.dump(dict(real=real, model=model), open(sys.argv[2], 'w'), indent=1)
