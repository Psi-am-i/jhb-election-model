import sys, io, contextlib, argparse, json, pickle
sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as M
OUT = sys.argv[1]
c = cityconfig.use('joburg'); target = cityconfig.use_target('2026'); M.apply_city(c)
sc = M.load_scenario(argparse.Namespace(config=None, set=[], draws=400, seed=20261104, city='joburg', target='2026'))
with contextlib.redirect_stdout(io.StringIO()):
    run = M.run_model(target, sc, verbose=False)
g = run.guards
out = {k: g.get(k) for k in ('turnout_reference','turnout_moved','district_ipf')}
out['pool_turnout_names'] = run.pool_turnout_names
ptd = np.asarray(run.pool_turnout_draws)
out['pool_turnout_mean'] = ptd.mean(axis=0).tolist()
out['pool_turnout_sd'] = ptd.std(axis=0).tolist()
dl = [k for k in sc.get('_delivery', {})] if isinstance(sc.get('_delivery'), dict) else None
print(json.dumps(out, indent=1, default=str))
print([f for f in dir(run) if not f.startswith('_')])
