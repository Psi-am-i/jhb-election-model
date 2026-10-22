"""In-process 2026 run recording each Dirichlet draw (mean, draw, total concentration) per pool. Scratch only."""
import os, sys, pickle
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0,'src'); sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
import numpy as np
import harness, montecarlo as M
REC = {'dir': []}; POOLS = {}
class Proxy:
    def __init__(self, g): self._g = g
    def __getattr__(self, k): return getattr(self._g, k)
    def dirichlet(self, *a, **kw):
        v = self._g.dirichlet(*a, **kw); al = np.asarray(a[0], dtype=float)
        REC['dir'].append((al / al.sum(), np.asarray(v, dtype=float), float(al.sum()))); return v
_real = np.random.default_rng
M.np.random.default_rng = lambda *a, **kw: Proxy(_real(*a, **kw))
_ps = M.pool_spec
def pool_spec(scenario, centres, index, ipf_out=None, *a, **kw):
    r = _ps(scenario, centres, index, ipf_out, *a, **kw)
    POOLS['order'] = list(r); POOLS['members'] = {nm: list(t[5]) for nm, t in r.items()}
    return r
M.pool_spec = pool_spec
N = int(sys.argv[1])
t, r = harness.run(draws=N)
M.np.random.default_rng = _real
seats = np.array([[s.get(p, 0) for p in r.universe] for s in r.seat_draws])
L = r.pr_vote_draws.astype(float)
pickle.dump(dict(dir=REC['dir'], pools=POOLS, universe=r.universe, seats=seats, list_share=L / L.sum(1, keepdims=True),
                 wards=(r.ward_winner_draws)), open('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/split_capture.pkl', 'wb'))
print('dirichlet calls', len(REC['dir']), 'pools', POOLS['order'], 'draws', N)
