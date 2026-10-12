import sys, copy, io, contextlib, pickle
sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc, levels
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
orig = levels.contestation
levels.contestation = lambda t, c: orig(cityconfig.use_target(2021), c) if str(t.year) == '2026' else orig(t, c)
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = 400; sc['seed'] = 20261104
with contextlib.redirect_stdout(io.StringIO()):
    run = mc.run_model(target, sc, verbose=False)
keep = {k: getattr(run, k) for k in ['universe','wards','seat_draws','pr_share_draws','ward_share_draws','guards','ward_win_sum','overhang_count','ratio']}
pickle.dump(keep, open(sys.argv[1] + '/run.pkl', 'wb'))
u=run.universe; print({p: round(float(run.ratio[u.index(p)]),3) for p in ['PA','ANC','DA','ASA','EFF','ACDP','NFP']})
