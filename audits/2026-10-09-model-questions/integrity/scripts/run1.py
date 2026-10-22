import sys, os, pickle, copy, time, json
sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc
draws = int(sys.argv[1]); out = sys.argv[2]
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = draws; sc['seed'] = 20261104
for kv in sys.argv[3:]:
    k, v = kv.split('=', 1); sc[k] = json.loads(v)
t = time.time()
run = mc.run_model(target, sc, run_dir=out + '/trace', verbose=False)
print('secs', time.time() - t)
keep = {k: getattr(run, k) for k in ['universe','wards','seat_draws','pr_share_draws','ward_share_draws','guards','notes','roster_state','roster_size','roster_dropped','ward_win_sum','overhang_count','pool_turnout_draws','pool_turnout_names','ratio','gamma_source','ward_winner_draws']}
keep['constants_read'] = run.constants_read
pickle.dump(keep, open(out + '/run.pkl', 'wb'))
print(json.dumps({k: v for k, v in run.guards.items() if not isinstance(v, dict)}, indent=1))
