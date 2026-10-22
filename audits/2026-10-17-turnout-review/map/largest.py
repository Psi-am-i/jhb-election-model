import sys, io, contextlib, argparse, json
sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as M
arm=sys.argv[1]; city=sys.argv[2]; year=sys.argv[3]; D=int(sys.argv[4])
c = cityconfig.use(city); target = cityconfig.use_target(year); M.apply_city(c)
orig = M.correlated_triangular
if arm == 'meanfix':
    def f(z_own, spec, z_common, rho):
        a, m, b = spec
        return orig(z_own, spec, z_common, rho) * m / ((a + m + b) / 3.0)
    M.correlated_triangular = f
sc = M.load_scenario(argparse.Namespace(config=None, set=[], draws=D, seed=20261104, city=city, target=year))
with contextlib.redirect_stdout(io.StringIO()):
    run = M.run_model(target, sc, verbose=False)
out={'arm':arm,'city':city,'year':year}
if year=='2026':
    al=0; da=0; tie=0
    for s in run.seat_draws:
        a,d=s.get('ANC',0),s.get('DA',0); mx=max(s.values()); top=[p for p,v in s.items() if v==mx]
        if len(top)>1: tie+=1
        elif top[0]=='ANC': al+=1
        elif top[0]=='DA': da+=1
    out.update({'P_ANC_largest_alone':al/len(run.seat_draws),'P_DA_largest_alone':da/len(run.seat_draws),'P_tie':tie/len(run.seat_draws)})
tr=run.guards['turnout_reference']; out['turnout_reference']={k:tr[k] for k in ('pool','districts_carry','turnout_scale','districts_without_projection')}
print(json.dumps(out))
