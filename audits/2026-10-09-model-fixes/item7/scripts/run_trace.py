"""In-process run with trace to scratch. usage: run_trace.py DRAWS OUTDIR"""
import sys, os, pickle, copy, time, json
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc
draws = int(sys.argv[1]); out = sys.argv[2]
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = draws; sc['seed'] = 20261104
t = time.time()
run = mc.run_model(target, sc, run_dir=out + '/trace', verbose=True)
print('secs', time.time() - t)
keep = {k: getattr(run, k, None) for k in ['universe','seat_draws','pr_share_draws','ward_share_draws','guards','notes','ratio','pool_turnout_draws','pool_turnout_names']}
pickle.dump(keep, open(out + '/run.pkl', 'wb'))
