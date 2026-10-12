"""PA's real vote by area, Johannesburg 2021 (ward PR ballot), against ward
composition of voters (pools.pool_counts 'voted'). Read-only."""
import sys, os, json, io, contextlib
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, pools
city = cityconfig.use('joburg'); cfg = pools.load_config()
out = {}
for year in ['2016', '2021']:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fits, ctx = pools.fit_city(city, year, cfg)
    cats = list(ctx['categories']); ci = cats.index('Coloured')
    comp, V, Y, parties = ctx['comp'], ctx['votes'], ctx['Y'], ctx['parties']
    counts = ctx['counts']
    keepw = [i for i, w in enumerate(counts.wards) if w in set(ctx['wards'])]
    reg = counts.registered[[counts.wards.index(w) for w in ctx['wards']]]
    j = parties.index('PA') if 'PA' in parties else None
    if j is None: print(year, 'PA absent'); continue
    pa = Y[:, j] * V
    col_v = comp[:, ci] * V                    # Coloured votes cast per ward (estimated split)
    c = comp[:, ci]
    tot = V.sum()
    # Duncan-Davis city-level bounds on PA votes coming from Coloured voters
    lo_from_col = np.maximum(0, pa - (1 - c) * V).sum()
    hi_from_col = np.minimum(pa, col_v).sum()
    f = fits['PA']
    res = dict(
        year=year, wards=len(V), votes_total=float(tot), pa_votes=float(pa.sum()),
        pa_share=float(pa.sum() / tot), coloured_votes=float(col_v.sum()),
        coloured_vote_share=float(col_v.sum() / tot),
        coloured_registered=float(reg[:, ci].sum()), coloured_turnout=float(col_v.sum() / reg[:, ci].sum()),
        city_turnout=float(tot / reg.sum()),
        pa_from_coloured_lo=float(lo_from_col), pa_from_coloured_hi=float(hi_from_col),
        pa_share_of_coloured_lo=float(lo_from_col / col_v.sum()), pa_share_of_coloured_hi=float(hi_from_col / col_v.sum()),
        pa_outside_coloured_min_share=float(1 - hi_from_col / pa.sum()),
        pa_outside_coloured_max_share=float(1 - lo_from_col / pa.sum()),
        fitted_rates=dict(zip(cats, map(float, f.rates))),
        dd_bounds={k: list(map(float, b)) for k, b in zip(cats, f.bounds)},
        fitted_vector=dict(zip(cats, map(float, f.composition(ctx['pool_votes'])))),
    )
    bins = [(0, .02), (.02, .1), (.1, .3), (.3, .5), (.5, 1.01)]
    res['by_coloured_share_of_voters'] = []
    for a, b in bins:
        m = (c >= a) & (c < b)
        res['by_coloured_share_of_voters'].append(dict(
            bin=f'{a:.0%}-{min(b,1):.0%}', wards=int(m.sum()), votes=float(V[m].sum()),
            coloured_votes=float(col_v[m].sum()), pa_votes=float(pa[m].sum()),
            pa_share_in_bin=float(pa[m].sum() / V[m].sum()) if m.any() else None,
            pa_votes_frac_of_pa_total=float(pa[m].sum() / pa.sum())))
    maj = c >= 0.5
    res['coloured_majority_wards'] = dict(n=int(maj.sum()), pa_share=float(pa[maj].sum() / V[maj].sum()) if maj.any() else None,
        coloured_frac_of_city_coloured_votes=float(col_v[maj].sum() / col_v.sum()),
        pa_votes_frac=float(pa[maj].sum() / pa.sum()),
        wards_detail=[(ctx['wards'][i], round(float(c[i]), 3), round(float(Y[i, j]), 4), int(V[i])) for i in np.where(maj)[0]])
    # top PA wards
    order = np.argsort(-pa)[:12]
    res['top_pa_wards'] = [(ctx['wards'][i], round(float(c[i]), 3), round(float(Y[i, j]), 4), int(pa[i])) for i in order]
    out[year] = res
    print(json.dumps({k: v for k, v in res.items() if k not in ('wards_detail',)}, indent=1, default=str))
json.dump(out, open(sys.argv[1], 'w'), indent=1, default=str)
