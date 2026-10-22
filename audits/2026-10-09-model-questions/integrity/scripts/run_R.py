import sys, copy, io, contextlib, numpy as np
sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
cap=[]; orig=mc._balance
def wrap(R, el, pv):
    out=orig(R, el, pv); cap.append((out.copy(), np.asarray(el).copy())); return out
mc._balance=wrap
FR={}
om=mc.make_drawer
def md(sc,b,c,idx,rng):
    d=om(sc,b,c,idx,rng); return d
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = 200; sc['seed'] = 20261104
with contextlib.redirect_stdout(io.StringIO()):
    r = mc.run_model(target, sc, verbose=False)
# ipf parties/names: recover from pool_spec
ipf={}; mc.pool_spec(r.scenario, {p:1.0 for p in r.universe}, r.index, ipf)
names=ipf['names']; parties=ipf['parties']
for q in ['PA','ALJAMAAH','DA','ANC','IFP','VFPLUS']:
    j=parties.index(q)
    share_of_pool=np.array([[R[g,j]/R[g].sum() for g in range(len(names))] for R,_ in cap])
    from_pool=np.array([R[:,j]/R[:,j].sum() for R,_ in cap])
    print(q, 'share of each pool p50', dict(zip(names, np.median(share_of_pool,0).round(3))), '| p95', dict(zip(names, np.percentile(share_of_pool,95,0).round(3))), '| fraction of its votes from each pool p50', dict(zip(names, np.median(from_pool,0).round(3))))
print('vector weights PA', {n: round(r.scenario['pools'][n]['members']['PA'],4) for n in names})
