"""No model run: the coverage values and implied ward/PR ratio change at Johannesburg 2026, both forms."""
import os, sys
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0,'src'); sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
import cityconfig, levels, votecov
from fold import load, citywide
city=cityconfig.use('joburg'); t=cityconfig.use_target('2026')
cnt_now=levels.contestation(t,city); cnt_was=levels.contestation(cityconfig.use_target('2021'),city); cityconfig.use_target('2026')
vc=votecov.make('2026')
v_now=vc(t,city); v_was=vc(cityconfig.use_target('2021'),city); cityconfig.use_target('2026')
f='data/raw/elections/'+t.results('2021')
wc=citywide(load(f,'Ward')[0]); pc=citywide(load(f,'PR')[0])
rows=[]
for p in cnt_was:
    if p not in cnt_now or pc.get(p,0)<=0.001: continue
    import numpy as np
    r0=float(np.clip(wc.get(p,0)/pc[p],0.5,2.0))
    rc=float(np.clip(r0*cnt_now[p]/cnt_was[p],0,2)) if cnt_was[p] else r0
    rv=float(np.clip(r0*v_now[p]/v_was[p],0,2)) if v_was.get(p) else r0
    rows.append((pc[p],p,r0,cnt_was[p],cnt_now[p],v_was.get(p),v_now.get(p),rc,rv))
for x in sorted(rows,reverse=True):
    print(f"{x[1][:30]:<30s} pr21 {x[0]*100:6.2f} r0 {x[2]:.3f} count {x[3]:.3f}->{x[4]:.3f} vote {x[5]:.3f}->{x[6]:.3f} ratio count {x[7]:.3f} vote {x[8]:.3f}")
