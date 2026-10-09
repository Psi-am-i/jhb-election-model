import sys, json; sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
from harness import *
from unittest import mock
import numpy as np, votecov
t,b=run(draws=1000)
t,f=run(draws=1000,patches=[mock.patch.object(levels,'contestation',votecov.make('2026'))])
show(summary(b),'baseline'); show(summary(f),'vote-weighted fix')
print('F6 list votes bit-identical:', np.array_equal(b.pr_vote_draws,f.pr_vote_draws))
L=f.pr_vote_draws.astype(float);W=f.ward_vote_draws.astype(float);g=(L/L.sum(1,keepdims=True)-W/W.sum(1,keepdims=True))*100
i=f.index['PA']; print('PA draws gap < -1.76: %.2f%%'%((g[:,i]<-1.76).mean()*100), 'p1 %.2f'%np.percentile(g[:,i],1))
d=f.index['DA']; print('DA draws gap < -1.76: %.2f%% p1 %.2f min %.2f'%((g[:,d]<-1.76).mean()*100,np.percentile(g[:,d],1),g[:,d].min()))
Lb=b.pr_vote_draws.astype(float);Wb=b.ward_vote_draws.astype(float);gb=(Lb/Lb.sum(1,keepdims=True)-Wb/Wb.sum(1,keepdims=True))*100
print('DA baseline draws gap < -1.76: %.2f%%'%((gb[:,d]<-1.76).mean()*100))
rows=[]
for p,j in f.index.items():
    sb=np.array([s.get(p,0) for s in b.seat_draws]).mean(); sf=np.array([s.get(p,0) for s in f.seat_draws]).mean()
    rows.append((abs(sf-sb),p,sb,sf,gb[:,j].mean(),g[:,j].mean(),np.percentile(g[:,j],1),np.percentile(g[:,j],99),float(f.ratio[j]),float(b.ratio[j])))
for x in sorted(rows,reverse=True)[:15]: print('%-30s seats %.2f -> %.2f  gap %+.2f -> %+.2f  fix p1/p99 %+.2f/%+.2f ratio %.3f (was %.3f)'%x[1:])
json.dump([dict(party=x[1],seats_base=x[2],seats_fix=x[3],gap_base=x[4],gap_fix=x[5],gap_fix_p01=x[6],gap_fix_p99=x[7],ratio_fix=x[8],ratio_base=x[9]) for x in rows],open('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/fix2026.json','w'))
