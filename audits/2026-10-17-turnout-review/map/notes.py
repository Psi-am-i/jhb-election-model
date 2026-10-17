import sys, io, contextlib, argparse, json
sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as M
c = cityconfig.use('joburg'); target = cityconfig.use_target('2026'); M.apply_city(c)
sc = M.load_scenario(argparse.Namespace(config=None, set=[], draws=20, seed=20261104, city='joburg', target='2026'))
with contextlib.redirect_stdout(io.StringIO()):
    run = M.run_model(target, sc, verbose=False)
for src in (run.delivered, run.notes):
    items = src.items() if isinstance(src, dict) else enumerate(src)
    for k, v in items:
        s = json.dumps(v, default=str)
        if 'turnout' in str(k) or 'turnout' in s[:200]:
            print(k, s[:400])
print(run.n_vds, run.n_vd)
