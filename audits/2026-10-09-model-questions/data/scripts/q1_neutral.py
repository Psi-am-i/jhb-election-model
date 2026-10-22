import sys, json; sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
from harness import *
from unittest import mock
import numpy as np
N=int(sys.argv[1]); arm=sys.argv[2]
patches=[]; sets=[]
if arm=='no_contest_change':   # N1: target slates = previous slates -> now/was = 1 for all
    patches=[mock.patch.object(levels,'declared_contestation',lambda t,c:({},False))]; sets=['contestation_expand=0']
elif arm=='projection_0.22':   # pre-2026-09-23 behaviour: projected slates
    patches=[mock.patch.object(levels,'declared_contestation',lambda t,c:({},False))]
elif arm=='w_bye0':
    sets=['w_bye=0']
elif arm=='w_bye1':
    sets=['w_bye=1']
t,r=run(draws=N,sets=sets,patches=patches)
out=summary(r); show(out,arm)
# N5: does the solve reproduce ward_target = pr*ratio/sum? predicted from realised list shares
L=r.pr_vote_draws.astype(float); W=r.ward_vote_draws.astype(float)
Ls=L/L.sum(1,keepdims=True); Ws=W/W.sum(1,keepdims=True)
pred=Ls*r.ratio; pred/=pred.sum(1,keepdims=True)
i=r.index['PA']
print('PA ward share realised mean %.3f; implied by list*ratio/sum %.3f; normaliser mean %.4f'%(Ws[:,i].mean()*100,pred[:,i].mean()*100,(Ls*r.ratio).sum(1).mean()))
# all-party gap table for Q3
allp={p:dict(list=float(Ls[:,j].mean()*100),gap_mean=float(((Ls-Ws)[:,j]).mean()*100),gap_p01=float(np.percentile((Ls-Ws)[:,j],1)*100),gap_p99=float(np.percentile((Ls-Ws)[:,j],99)*100),ratio=float(r.ratio[j])) for p,j in r.index.items()}
json.dump(dict(summary=out,allp=allp),open(f'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/q1_{arm}.json','w'),default=float)
