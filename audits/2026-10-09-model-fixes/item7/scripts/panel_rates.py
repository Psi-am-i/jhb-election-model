"""Every party x pool rate across the panel: fitted rate and city-level
Duncan-Davis bounds (aggregated from ward bounds: lo = sum max(0, p_w-(1-c_w)V_w),
hi = sum min(p_w, c_w V_w), each over the pool's votes). Read-only."""
import sys, os, json, io, contextlib, traceback
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, pools
cfg = pools.load_config()
rows = []
for slug in ['joburg','tshwane','ekurhuleni','ethekwini','capetown','nelsonmandelabay','buffalocity','mangaung']:
    for year in ['2011', '2016', '2021']:
        try:
            city = cityconfig.load(slug); cityconfig.use(slug)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                fits, ctx = pools.fit_city(city, year, cfg)
        except BaseException as e:
            print(slug, year, 'SKIP', type(e).__name__, str(e)[:120]); continue
        cats = list(ctx['categories']); comp, V, Y = ctx['comp'], ctx['votes'], ctx['Y']
        poolv = (comp * V[:, None]).sum(0)
        for j, p in enumerate(ctx['parties']):
            pv = Y[:, j] * V
            if pv.sum() <= 0: continue
            f = fits[p]
            for gi, g in enumerate(cats):
                c = comp[:, gi]
                lo = np.maximum(0, pv - (1 - c) * V).sum() / poolv[gi]
                hi = np.minimum(pv, c * V).sum() / poolv[gi]
                rows.append(dict(city=slug, year=year, party=p, pool=g, rate=float(f.rates[gi]),
                                 dd_lo=float(lo), dd_hi=float(hi), city_share=float(pv.sum() / V.sum()),
                                 pool_vote_share=float(poolv[gi] / V.sum())))
        print(slug, year, 'ok', len(ctx['parties']), flush=True)
json.dump(rows, open(sys.argv[1], 'w'))
