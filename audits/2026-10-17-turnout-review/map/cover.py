import sys, csv, json, io, contextlib, math
sys.path.insert(0,'src')
import numpy as np, cityconfig, turnout as T, montecarlo as M
from pathlib import Path
rng=np.random.default_rng(1); N=20000; rho=0.63
cities=['joburg','tshwane','capetown','ekurhuleni','ethekwini','nelsonmandelabay','buffalocity','mangaung']
print("city year | proj | drawn p5 p50 p95 (proj x citywide k) | realised | inside? | mean k")
ins=0; tot=0; below=above=0
for y in ['2011','2016','2021','2026']:
  for c in cities:
    try: cityconfig.use(c); t=cityconfig.use_target(y)
    except SystemExit: continue
    tp=t.processed/'turnout.csv'; sp=t.processed/f'pools_{y}.json'
    if not sp.exists(): sp=cityconfig.active().processed/f'pools_{y}.json'
    if not tp.exists() or not sp.exists(): continue
    rows=list(csv.DictReader(tp.open())); rc=[k for k in rows[0] if k.startswith('registered_')][0]; pc=f'turnout_{y}_projected'
    proj=sum(float(r[pc])*int(r[rc]) for r in rows if r[pc])/sum(int(r[rc]) for r in rows if r[pc])
    s=json.load(open(sp)); P=list(s['pools'].values())
    reg=np.array([p['registered'] for p in P]); bands=[tuple(p['turnout']) for p in P]
    w=reg*np.array([b[1] for b in bands]); w=w/w.sum()
    zc=rng.standard_normal(N); K=np.zeros((N,len(P)))
    for g,b in enumerate(bands):
        z=math.sqrt(rho)*zc+math.sqrt(1-rho)*rng.standard_normal(N)
        K[:,g]=[M.tri_from_z(zz,b) for zz in z[:4000]]+[0]*(N-4000) if False else np.array([M.tri_from_z(zz,b) for zz in z])/b[1]
    ck=K@w; d=proj*ck
    real=float('nan')
    with contextlib.redirect_stdout(io.StringIO()):
        e=cityconfig.CALENDAR[y]
        if e.results: real=T.citywide(T.read_turnout(Path('data/raw/elections')/e.results,e.two_ballot))
    q=np.quantile(d,[.05,.5,.95]); inside = q[0]<=real<=q[2] if real==real else None
    if inside is not None:
        tot+=1; ins+=inside; below+= real<q[0]; above+= real>q[2]
    print(f"{c:16s} {y} | {proj:.3f} | {q[0]:.3f} {q[1]:.3f} {q[2]:.3f} | {real:.3f} | {inside} | {ck.mean():.4f}")
print(f"inside 90% interval: {ins}/{tot}; realised below p5: {below}; above p95: {above}")
