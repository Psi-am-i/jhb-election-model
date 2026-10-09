import pickle, json, numpy as np
D='/Users/simondavis/.claude/jobs/26965cd4/tmp/item9/'
spec=json.load(open('data/processed/pools_2026.json')); seeds=list(spec['seeds'])
R={k:pickle.load(open(D+k+'.pkl','rb')) for k in ('base','shock','nosplit')}
U=R['base']['universe']
def sh(r): v=np.asarray(r['pr_vote_draws'],float); return v/v.sum(1,keepdims=True)
def seats(r): return np.array([[s.get(p,0) for p in U] for s in r['seat_draws']])
L={k:sh(v) for k,v in R.items()}; Sx={k:seats(v) for k,v in R.items()}
ent=[p for p in seeds if p!='SOUTH_AFRICAN_COMMUNIST_PARTY']; gi=[U.index(p) for p in ent]
print('variant | 44-generic median q95% | median P>=1 | 45 group total q5/50/95 % | 45 group seats mean (q5-q95) | SACP q5/50/95 % | SACP seats mean, P>=1')
for k in ('base','shock','nosplit'):
    l=L[k]; s=Sx[k]; gen=[U.index(p) for p in ent if p not in ('ALL_CITIZENS_PARTY',)]
    q95=np.median(np.percentile(l[:,gen],95,axis=0)); p1=np.median((s[:,gen]>=1).mean(0))
    G=l[:,gi].sum(1); gs=s[:,gi].sum(1); i=U.index('SOUTH_AFRICAN_COMMUNIST_PARTY')
    print(k, '| %.3f | %.3f | %s | %.2f (%d-%d) | %s | %.2f %.2f'%(100*q95,p1,' / '.join('%.2f'%v for v in 100*np.percentile(G,[5,50,95])),gs.mean(),*np.percentile(gs,[5,95]),' / '.join('%.4f'%v for v in 100*np.percentile(l[:,i],[5,50,95])),s[:,i].mean(),(s[:,i]>=1).mean()))
# big-party seat effect
for p in ('ANC','DA','EFF','MK','ASA','PA'):
    i=U.index(p); print(p, ' '.join('%s %.2f±%.2f'%(k,Sx[k][:,i].mean(),Sx[k][:,i].std()) for k in ('base','shock','nosplit')))
