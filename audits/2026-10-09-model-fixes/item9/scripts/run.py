"""In-process run_model for joburg 2026, writes only to scratch.
variant: base | nosplit (every within-pool Dirichlet replaced by its mean) |
         shock (seeded parties' zero level-shock sd replaced by a supplied map)
Captures draw_pools' citywide target vector per draw (the pool stage's output,
before the ward layer), the pools' concentrations, and the final draws."""
import os, sys, copy, json, pickle, time
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np
import cityconfig, montecarlo as M
variant = sys.argv[1]; draws = int(sys.argv[2]); out = sys.argv[3]
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); M.apply_city(city)
sc = copy.deepcopy(M.DEFAULTS); sc['draws'] = draws; sc['seed'] = 20261104

class NoSplitRng:
    def __init__(self, rng): self._r = rng
    def __getattr__(self, k): return getattr(self._r, k)
    def dirichlet(self, alpha, size=None):
        a = np.asarray(alpha, float); return a / a.sum()

cap = {'targets': [], 'pools': None}
orig = M.make_drawer
def cells(f):
    out = {}
    for n, c in zip(f.__code__.co_freevars, f.__closure__):
        try: out[n] = c.cell_contents
        except ValueError: pass
    return out
SDMAP = json.load(open(sys.argv[4])) if variant == 'shock' else {}
def wrap(scenario, base_city_d, centres, index, rng):
    if variant == 'nosplit':
        rng = NoSplitRng(rng)
    f = orig(scenario, base_city_d, centres, index, rng)
    cl = cells(f)
    pools = cl.get('pools')
    if variant == 'shock':
        d = cl['pool_sd_shock']; n = 0
        for p, v in SDMAP.items():
            if p in d and d[p] == 0.0: d[p] = float(v); n += 1
        print('shock set for', n, 'parties')
    cap['pools'] = {n: dict(alpha=float(p[4]), members=list(p[5])) for n, p in pools.items()}
    cap['pool_sd_shock'] = dict(cl.get('pool_sd_shock') or {})
    cap['centres'] = dict(centres); cap['index'] = dict(index)
    def g():
        t = f(); cap['targets'].append(np.array(t, float)); return t
    for a in ('ipf_stats', 'turnout_record', 'turnout_pools'):
        setattr(g, a, getattr(f, a))
    return g
M.make_drawer = wrap
t = time.time()
r = M.run_model(target, sc, verbose=False)
print('secs', round(time.time() - t, 1))
keep = dict(universe=list(r.universe), seat_draws=r.seat_draws,
            pr_vote_draws=np.asarray(r.pr_vote_draws), targets=np.array(cap['targets']),
            pools=cap['pools'], pool_sd_shock=cap['pool_sd_shock'], centres=cap['centres'], index=cap['index'])
pickle.dump(keep, open(out, 'wb'))
