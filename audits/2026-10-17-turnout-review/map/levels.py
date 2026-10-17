import sys, csv, json, io, contextlib
sys.path.insert(0,'src')
import numpy as np, cityconfig, turnout as T
from pathlib import Path
cities=['joburg','tshwane','capetown','ekurhuleni','ethekwini','nelsonmandelabay','buffalocity','mangaung']
print("city year | proj(λ̂·NPE) | ref pool(prev LGE, spec reg) | band-mean pool | realised | prevLGE actual")
for c in cities:
    for y in ['2011','2016','2021','2026']:
        try:
            cityconfig.use(c); t=cityconfig.use_target(y)
        except SystemExit: continue
        tp=t.processed/'turnout.csv'
        sp=t.processed/f'pools_{y}.json'
        if not sp.exists(): sp=cityconfig.active().processed/f'pools_{y}.json'
        if not tp.exists() or not sp.exists(): continue
        rows=list(csv.DictReader(tp.open()))
        rc=[k for k in rows[0] if k.startswith('registered_')][0]
        pc=f'turnout_{y}_projected'
        num=sum(float(r[pc])*int(r[rc]) for r in rows if r[pc]); den=sum(int(r[rc]) for r in rows if r[pc])
        proj=num/den
        s=json.load(open(sp))
        reg=np.array([p['registered'] for p in s['pools'].values()])
        tb=np.array([p['turnout'] for p in s['pools'].values()])
        ref=(reg*tb[:,1]).sum()/reg.sum(); bm=(reg*tb.mean(axis=1)).sum()/reg.sum()
        real=prev=float('nan')
        with contextlib.redirect_stdout(io.StringIO()):
            try:
                e=cityconfig.CALENDAR[y]
                if e.results:
                    real=T.citywide(T.read_turnout(Path('data/raw/elections')/e.results, e.two_ballot))
            except Exception as ex: pass
            try:
                pl=t.previous_lge; e=cityconfig.CALENDAR[pl]
                prev=T.citywide(T.read_turnout(Path('data/raw/elections')/e.results, e.two_ballot))
            except Exception: pass
        print(f"{c:17s} {y} | {proj:.3f} | {ref:.3f} | {bm:.3f} | {real:.3f} | {prev:.3f}")
