import sys, json, argparse, glob
sys.path.insert(0,'src')
import cityconfig, montecarlo as M
city=cityconfig.use('joburg'); target=cityconfig.use_target('2026'); M.apply_city(city)
sc=M.load_scenario(argparse.Namespace(config=None,draws=20,seed=20261104,set=None,counterfactual=False))
out=sys.argv[1]
run=M.run_model(target, sc, verbose=False, run_dir=out)
