import sys, io, contextlib, argparse, json
sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as M
arm = sys.argv[1]; D = int(sys.argv[2])
c = cityconfig.use('joburg'); target = cityconfig.use_target('2026'); M.apply_city(c)
sets = []
if arm in ('nonoise','mode','meanfix_nonoise'):
    sets = ['turnout_noise_sd=0', 'turnout_blend_jitter=0']
orig = M.correlated_triangular
if arm == 'mode':
    M.correlated_triangular = lambda z_own, spec, z_common, rho: float(spec[1])
if arm in ('meanfix','meanfix_nonoise'):
    def f(z_own, spec, z_common, rho):
        a, m, b = spec
        return orig(z_own, spec, z_common, rho) * m / ((a + m + b) / 3.0)
    M.correlated_triangular = f
sc = M.load_scenario(argparse.Namespace(config=None, set=sets, draws=D, seed=20261104, city='joburg', target='2026'))
with contextlib.redirect_stdout(io.StringIO()):
    run = M.run_model(target, sc, verbose=False)
u = list(run.universe); P = ['ANC','DA','ASA','EFF','MK','PA']
sh = run.pr_share_draws.mean(axis=0); sd = run.pr_share_draws.std(axis=0)
seats = {p: float(np.mean([s.get(p,0) for s in run.seat_draws])) for p in P}
tm = run.guards['turnout_moved']
res = {'arm': arm, 'share': {p: round(100*float(sh[u.index(p)]),3) for p in P},
       'sd': {p: round(100*float(sd[u.index(p)]),3) for p in P},
       'turnout_moved_pts': {p: round(100*tm[p],3) for p in P},
       'seats': {p: round(v,2) for p, v in seats.items()},
       'ipf': run.guards['district_ipf'],
       'ward_wins': {p: int(run.ward_win_sum.get(p,0)) for p in P}}
print(json.dumps(res))
