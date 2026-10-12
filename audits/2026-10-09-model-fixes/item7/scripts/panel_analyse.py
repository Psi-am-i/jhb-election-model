import json, sys, collections
R = json.load(open(sys.argv[1]))
print('rows', len(R))
for g in ['Black African','Coloured','Indian/Asian','White']:
    rr = [r for r in R if r['pool']==g]
    print(f'\n== {g}: top fitted rates')
    for r in sorted(rr, key=lambda r: -r['rate'])[:6]:
        print(f"   {r['city'][:8]:8s}{r['year']} {r['party'][:10]:10s} rate {r['rate']:.3f} DD [{r['dd_lo']:.3f},{r['dd_hi']:.3f}] pool {r['pool_vote_share']:.3f}")
    print(f'   top DD lower bounds (proven minimum share):')
    for r in sorted(rr, key=lambda r: -r['dd_lo'])[:4]:
        print(f"   {r['city'][:8]:8s}{r['year']} {r['party'][:10]:10s} rate {r['rate']:.3f} DD [{r['dd_lo']:.3f},{r['dd_hi']:.3f}]")
    # non-dominant: excluding the top party per city-year, highest rate (relevant for minor parties)
print('\n== PA everywhere')
pa = collections.defaultdict(dict)
for r in R:
    if r['party']=='PA': pa[(r['city'],r['year'])][r['pool']] = r
for k, d in sorted(pa.items()):
    c = d['Coloured']; tot_share = c['city_share']
    # share of PA votes from outside Coloured: fitted, and DD range
    poolv = {g: d[g]['pool_vote_share'] for g in d}
    fitted_from_col = d['Coloured']['rate']*poolv['Coloured']/tot_share
    lo_out = 1 - c['dd_hi']*poolv['Coloured']/tot_share; hi_out = 1 - c['dd_lo']*poolv['Coloured']/tot_share
    print(f"  {k[0][:8]:8s}{k[1]} PA city {tot_share*100:5.2f}% Coloured pool {poolv['Coloured']*100:5.2f}% of votes; PA rate in Coloured {c['rate']:.3f} DD [{c['dd_lo']:.3f},{c['dd_hi']:.3f}]; outside-Coloured share of PA vote fitted {1-fitted_from_col:.3f} DD [{max(lo_out,0):.3f},{hi_out:.3f}]")
# largest rise of a fitted rate between consecutive elections, same city, per pool (party present both)
print('\n== largest rises in fitted rate between consecutive LGEs, per pool')
idx = {(r['city'],r['year'],r['party'],r['pool']): r for r in R}
for g in ['Black African','Coloured','Indian/Asian','White']:
    mv = []
    for (c,y,p,gg), r in idx.items():
        if gg!=g or y=='2011': continue
        prev = {'2016':'2011','2021':'2016'}[y]
        a = idx.get((c,prev,p,g)); a_rate = a['rate'] if a else 0.0
        mv.append((r['rate']-a_rate, c, prev, y, p, a_rate, r['rate'], r['dd_lo']-(a['dd_hi'] if a else 0)))
    mv.sort(reverse=True)
    for m in mv[:4]: print(f"   {g}: {m[4][:10]:10s} {m[1][:8]} {m[2]}->{m[3]} {m[5]:.3f}->{m[6]:.3f} (+{m[0]:.3f}); proven rise (DDlo_now - DDhi_before) {m[7]:+.3f}")
