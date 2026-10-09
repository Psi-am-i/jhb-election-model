"""In-process run_model harness. Writes only to the scratch dir."""
import os, sys, argparse, json, time, contextlib
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model')
sys.path.insert(0, 'src')
import numpy as np
import cityconfig, montecarlo as M, levels

def run(city='joburg', year='2026', draws=1000, seed=20261104, sets=(), patches=None):
    city_o = cityconfig.use(city)
    target = cityconfig.use_target(year)
    M.apply_city(city_o)
    args = argparse.Namespace(config=None, draws=draws, seed=seed,
                              set=list(sets) or None, counterfactual=bool(sets),
                              city=city, target=year)
    scenario = M.load_scenario(args)
    with contextlib.ExitStack() as st:
        for p in (patches or []):
            st.enter_context(p)
        t = time.time()
        r = M.run_model(target, scenario, verbose=False)
    r._secs = time.time() - t
    return target, r

def summary(r, parties=('PA','DA','ANC','ASA','EFF','MK','IFP','ALJAMAAH','AIC','PAC','ATM','BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA','VFPLUS','ACDP','RISE')):
    L = r.pr_vote_draws.astype(float); W = r.ward_vote_draws.astype(float)
    Ls = L/L.sum(1, keepdims=True); Ws = W/W.sum(1, keepdims=True)
    out = {}
    for p in parties:
        i = r.index.get(p)
        if i is None: continue
        seats = np.array([s.get(p, 0) for s in r.seat_draws])
        wins = (r.ward_winner_draws == i).sum(1)
        g = (Ls[:, i]-Ws[:, i])*100
        out[p] = dict(list=Ls[:, i].mean()*100, ward=Ws[:, i].mean()*100,
                      gap=g.mean(), gap_min=g.min(), gap_max=g.max(),
                      seats=seats.mean(), seats_med=float(np.median(seats)),
                      wins=wins.mean(), ratio=float(r.ratio[i]))
    return out

def show(out, label=''):
    print(f'--- {label}')
    for p, d in out.items():
        print(f"{p[:14]:<14s} list {d['list']:6.2f} ward {d['ward']:6.2f} gap {d['gap']:+6.2f} [{d['gap_min']:+6.2f},{d['gap_max']:+6.2f}] seats {d['seats']:6.2f} wins {d['wins']:5.2f} ratio {d['ratio']:.3f}")
