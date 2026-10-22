import os, sys, json, pickle
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model')
import numpy as np
D='/Users/simondavis/.claude/jobs/26965cd4/tmp/item9/'
m=json.load(open('site/draws/manifest.json')); raw=open('site/draws/base.bin','rb').read()
B={b['name']:b for b in m['blocks']}
def blk(n):
    b=B[n]; a=np.frombuffer(raw[b['offset']:b['offset']+b['nbytes']],dtype=np.dtype(b['dtype'])); return a.reshape(-1,m['draws']).T, b['columns']
seats, sc = blk('seats/deduct'); lv, lc = blk('list_vote')
R=pickle.load(open(D+'base.pkl','rb')); U=R['universe']
mine_seats=np.array([[s.get(p,0) for p in sc if p in U] for s in R['seat_draws']])
pub_seats=seats[:, [i for i,p in enumerate(sc) if p in U]]
print('seat cols', [p for p in sc if p not in U])
print('seats identical:', np.array_equal(mine_seats, pub_seats), mine_seats.shape)
pv=np.asarray(R['pr_vote_draws']); idx=[U.index(p) for p in lc]
print('list votes identical:', np.array_equal(pv[:, idx].astype(np.int64), lv.astype(np.int64)), 'max abs diff', np.abs(pv[:, idx]-lv).max())
