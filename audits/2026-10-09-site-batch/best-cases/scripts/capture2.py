"""In-process run_model at the published seed, recording the drawn drivers.

Writes only to the scratch directory given as argv[1]. Wraps the rng in a
transparent proxy (same generator, same call order, so the same numbers) and
records: the citywide turnout factor and pool normals, the per-party level
shocks (log_shock), triangular draws, the turnout-pattern jitter, VD turnout
noise, ward noise, and the entrant coin.
"""
import pickle, sys
from pathlib import Path
out = Path(sys.argv[1])
sys.path.insert(0, "src")
import numpy as np
import cityconfig
cityconfig.use("joburg")
target = cityconfig.use_target("2026")
import montecarlo as mc

REC = {"std_normal": [], "t": [], "tri": [], "uniform": [], "random": [],
       "vd_noise": [], "ward_noise": [], "normal_other": [], "dirichlet_n": 0}
IPF = {}

class Proxy:
    def __init__(self, g): self._g = g
    def __getattr__(self, k): return getattr(self._g, k)
    def standard_normal(self, *a, **kw):
        v = self._g.standard_normal(*a, **kw)
        if not a and not kw: REC["std_normal"].append(float(v))
        return v
    def standard_t(self, *a, **kw):
        v = self._g.standard_t(*a, **kw)
        REC["t"].append(np.array(v, dtype=float).copy())
        return v
    def triangular(self, *a, **kw):
        v = self._g.triangular(*a, **kw)
        REC["tri"].append((tuple(float(x) for x in a[:3]), np.array(v, dtype=float)))
        return v
    def uniform(self, *a, **kw):
        v = self._g.uniform(*a, **kw); REC["uniform"].append(np.array(v, dtype=float)); return v
    def random(self, *a, **kw):
        v = self._g.random(*a, **kw); REC["random"].append(np.array(v, dtype=float)); return v
    def dirichlet(self, *a, **kw):
        REC["dirichlet_n"] += 1
        v = self._g.dirichlet(*a, **kw)
        al = np.asarray(a[0], dtype=float)
        REC.setdefault("dir", []).append((al / al.sum(), np.asarray(v, dtype=float), float(al.sum())))
        return v
    def normal(self, loc=0.0, scale=1.0, size=None):
        v = self._g.normal(loc, scale, size)
        if isinstance(size, tuple) and len(size) == 2:
            REC["ward_noise"].append(np.asarray(v, dtype=np.float32))
        elif isinstance(size, (int, np.integer)) and size > 1:
            REC["vd_noise"].append(np.asarray(v, dtype=np.float32))
        else:
            REC["normal_other"].append((float(loc), float(scale), np.array(v, dtype=float)))
        return v

_real_rng = np.random.default_rng
def proxy_rng(*a, **kw): return Proxy(_real_rng(*a, **kw))
mc.np.random.default_rng = proxy_rng

_real_pool_spec = mc.pool_spec
def pool_spec(scenario, centres, index, ipf_out=None, *a, **kw):
    r = _real_pool_spec(scenario, centres, index, ipf_out, *a, **kw)
    if ipf_out is not None and "parties" in ipf_out:
        IPF["parties"] = list(ipf_out["parties"])
        IPF["centres"] = {k: float(v) for k, v in centres.items()}
        IPF["pool_members"] = {nm: list(t[5]) for nm, t in r.items()}
    return r
mc.pool_spec = pool_spec
_real_log_shock = mc.log_shock
def log_shock(rng, sd, *a, **kw):
    v = _real_log_shock(rng, sd, *a, **kw)
    REC.setdefault("shock", []).append((np.array(sd, dtype=float), np.array(v, dtype=float)))
    return v
mc.log_shock = log_shock

class Args:
    config = None; set = None; draws = None; seed = 20261104
scen = mc.load_scenario(Args())
run = mc.run_model(target, scen, verbose=True)
mc.np.random.default_rng = _real_rng

payload = {
    "universe": list(run.universe), "wards": list(run.wards),
    "ward_winner_draws": run.ward_winner_draws,
    "pr_vote_draws": run.pr_vote_draws, "ward_vote_draws": run.ward_vote_draws,
    "pool_turnout_draws": run.pool_turnout_draws,
    "pool_turnout_names": list(getattr(run, "pool_turnout_names", []) or []),
    "seat_draws": run.seat_draws, "over_draws": [sorted(x) for x in run.over_draws],
    "thresholds": run.thresholds, "council_sizes": run.council_sizes,
    "ipf_parties": IPF.get("parties"), "pool_members": IPF.get("pool_members"), "centres": IPF.get("centres"),
    "scenario_pools": {k: list(v["members"]) for k, v in (run.scenario.get("pools") or {}).items()},
    "pool_seeds": run.scenario.get("pool_seeds"), "pool_seed_bands": run.scenario.get("pool_seed_bands"),
    "theta_sd": run.scenario.get("_theta_sd"),
    "rec": {k: v for k, v in REC.items() if k not in ("vd_noise", "ward_noise")},
}
with open(out / "capture2.pkl", "wb") as fh:
    pickle.dump(payload, fh)
np.save(out / "ward_noise.npy", np.stack(REC["ward_noise"]))
np.save(out / "vd_noise.npy", np.stack(REC["vd_noise"]))
print("done", len(REC["ward_noise"]), len(REC["vd_noise"]), len(REC["t"]), len(REC["uniform"]))
