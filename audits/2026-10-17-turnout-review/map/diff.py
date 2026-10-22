import sys, json, io, contextlib, math
sys.path.insert(0,'src')
import numpy as np, cityconfig, pools, montecarlo as M
rng=np.random.default_rng(2); N=20000; rho=0.63
cfg=pools.load_config()
cities=['joburg','tshwane','capetown','ekurhuleni','ethekwini','nelsonmandelabay','buffalocity','mangaung']
print("city year | realised log(k_BA/k_W) | model p5 p50 p95 | realised k per pool (BA,Col,Ind,W) | pctile")
pct=[]
for y in ['2011','2016','2021']:
  for c in cities:
    city=cityconfig.use(c); t=cityconfig.use_target(y)
    sp=t.processed/f'pools_{y}.json'
    if not sp.exists(): sp=cityconfig.active().processed/f'pools_{y}.json'
    s=json.load(open(sp)); names=list(s['pools']); bands={n:tuple(s['pools'][n]['turnout']) for n in names}
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pc=pools.pool_counts(city, y, cfg)
    except BaseException as ex:
        print(c,y,'pool_counts refused',type(ex).__name__); continue
    real={g:float(r) for g,r in zip(pc.categories, pc.rates['turnout'])}
    kr={n: real[n]/bands[n][1] for n in names if n in real}
    if 'Black African' not in kr or 'White' not in kr: continue
    zc=rng.standard_normal(N)
    K={}
    for n in ('Black African','White'):
        z=math.sqrt(rho)*zc+math.sqrt(1-rho)*rng.standard_normal(N)
        K[n]=np.array([M.tri_from_z(zz,bands[n]) for zz in z])/bands[n][1]
    dm=np.log(K['Black African']/K['White']); dr=math.log(kr['Black African']/kr['White'])
    q=np.quantile(dm,[.05,.5,.95]); p=float((dm<dr).mean()); pct.append(p)
    ks=' '.join('%.3f'%kr.get(n,float('nan')) for n in names)
    print(f"{c:16s} {y} | {dr:+.3f} | {q[0]:+.3f} {q[1]:+.3f} {q[2]:+.3f} | {ks} | {p:.2f}")
pct=np.array(pct); print('n',len(pct),'inside 90%:',int(((pct>.05)&(pct<.95)).sum()),'below p5',int((pct<=.05).sum()),'above p95',int((pct>=.95).sum()))
