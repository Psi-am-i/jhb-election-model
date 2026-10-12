"""In-process run_model (writes nothing outside scratch) that records, per draw,
each party's realised share of each pool's vote (the Dirichlet split) and each
pool's votes, plus the post-IPF rate matrix. Import and call run_capture()."""
import sys, os, copy, io, contextlib
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, montecarlo as mc

class RngProxy:
    def __init__(self, rng, log): self._r = rng; self._log = log
    def dirichlet(self, a, *k, **kw):
        out = self._r.dirichlet(a, *k, **kw); self._log.append(out); return out
    def __getattr__(self, n): return getattr(self._r, n)

def run_capture(draws=400, seed=20261104, scen=None, patches=(), target_year='2026', city='joburg'):
    city_o = cityconfig.use(city); target = cityconfig.use_target(target_year); mc.apply_city(city_o)
    sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = draws; sc['seed'] = seed
    sc.update(scen or {})
    box = {}; dlog = []; rdlog = []
    o_ps, o_md, o_bal, o_pb = mc.pool_spec, mc.make_drawer, mc._balance, mc.partial_balance
    def ps(scenario, centres, index, ipf_out=None):
        s = o_ps(scenario, centres, index, ipf_out); box['spec'] = s; box['ipf'] = ipf_out; return s
    def md(scenario, b, c, idx, rng):
        f = o_md(scenario, b, c, idx, RngProxy(rng, dlog)); box['drawer'] = f; return f
    def bal(R, e, pv):
        out = o_bal(R, e, pv); rdlog.append(out.copy()); return out
    mc.pool_spec, mc.make_drawer, mc._balance = ps, md, bal
    try:
        with contextlib.ExitStack() as st:
            for p in patches: st.enter_context(p)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                run = mc.run_model(target, sc, verbose=False)
    finally:
        mc.pool_spec, mc.make_drawer, mc._balance = o_ps, o_md, o_bal
    spec = box['spec']; names = list(spec)
    sizes = [len(spec[n][5]) for n in names]
    # dirichlet calls per draw: one per pool, in spec order, then possibly the arrival group
    per = len(dlog) // draws
    assert per * draws == len(dlog), (len(dlog), draws)
    assert [len(dlog[k]) for k in range(len(names))] == sizes, ([len(x) for x in dlog[:6]], sizes)
    tr = np.array(box['drawer'].turnout_record)  # draws x pools in turnout_pools order
    tpools = list(box['drawer'].turnout_pools)
    reg = np.array([spec[n][1] for n in tpools])
    votes = tr * reg[None, :]
    shares = {}
    for gi, n in enumerate(names):
        mem = spec[n][5]
        S = np.array([dlog[d * per + gi] for d in range(draws)])
        shares[n] = {p: S[:, k] for k, p in enumerate(mem)}
    pool_votes = {n: votes[:, tpools.index(n)] for n in names}
    return run, dict(names=names, shares=shares, pool_votes=pool_votes, rd=rdlog, ipf=box['ipf'], spec=spec, log=buf.getvalue())

def pa_summary(run, cap, party='PA', group='Coloured'):
    sh = cap['shares'][group].get(party)
    pv = cap['pool_votes']
    from_pools = {g: cap['shares'][g].get(party, 0) * pv[g] for g in cap['names']}
    tot = sum(from_pools.values())
    outside = 1 - from_pools[group] / tot
    seats = np.array([s.get(party, 0) for s in run.seat_draws])
    i = run.universe.index(party)
    q = lambda x: [round(float(v), 4) for v in np.percentile(x, [5, 50, 95])]
    return dict(rate_in_group_p5_50_95=q(sh), rate_mean=float(sh.mean()), outside_share_p5_50_95=q(outside),
                list_share_p5_50_95=q(run.pr_share_draws[:, i]), list_share_mean=float(run.pr_share_draws[:, i].mean()),
                group_vote_share_of_city_mean=float((pv[group] / sum(pv.values())).mean()),
                seats_mean=float(seats.mean()), seats_p5_50_95=q(seats))
