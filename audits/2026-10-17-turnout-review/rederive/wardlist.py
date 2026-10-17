import sys, argparse, numpy as np, json
sys.path.insert(0,'src')
import cityconfig, montecarlo as M
city=cityconfig.use('joburg'); target=cityconfig.use_target('2026'); M.apply_city(city)
sc=M.load_scenario(argparse.Namespace(config=None,draws=int(sys.argv[1]),seed=20261104,set=None,counterfactual=False))
run=M.run_model(target, sc, verbose=False)
u=list(run.universe)
out={}
for p in ['ANC','DA','EFF','ASA','MK','PA','IFP','ACDP','FFPLUS','RISE','BOSA','VF']:
    if p in u:
        i=u.index(p)
        seats=np.array([s.get(p,0) for s in run.seat_draws])
        wins=(run.ward_winner_draws==i).sum(1) if hasattr(run,'ward_winner_draws') else None
        out[p]=dict(list=100*run.pr_share_draws[:,i].mean(), ward=100*run.ward_share_draws[:,i].mean(), seats=seats.mean(), wards=None if wins is None else wins.mean())
for k,v in out.items(): print(k, {a:(round(b,2) if b is not None else None) for a,b in v.items()})
