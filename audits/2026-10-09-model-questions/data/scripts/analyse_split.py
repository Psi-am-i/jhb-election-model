import pickle, json, numpy as np
B='/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/'
C=pickle.load(open(B+'split_capture.pkl','rb')); H=json.load(open(B+'hist_splits.json'))
cana=json.load(open(B+'canary_joburg_2026.json'))
seeded={x['party'] for x in cana['rows'] if x['seeded']}
order=C['pools']['order']; mem=C['pools']['members']; npool=len(order)
D=C['dir']; N=len(D)//npool
res=[]
for gi,g in enumerate(order):
    means=np.array([D[d*npool+gi][0] for d in range(N)]); draws=np.array([D[d*npool+gi][1] for d in range(N)]); A=D[gi][2]
    hp=H[g]['parties']; hs=np.array(H[g]['splits']); lab=H[g]['labels']; jhb=[i for i,l in enumerate(lab) if l.startswith('JHB')]
    for j,p in enumerate(mem[g]):
        m=means[:,j].mean(); x=draws[:,j]
        if p in hp:
            k=hp.index(p); h=hs[:,k]; hmax=h.max(); hmin=h.min(); jmax=h[jhb].max() if jhb else np.nan; jmin=h[jhb].min()
            argmax=lab[int(h.argmax())]
        else: hmax=hmin=jmax=jmin=0.0; argmax='-'
        res.append(dict(pool=g,party=p,seeded=p in seeded,A=A,mean=m,alpha_i=m*A,p01=np.percentile(x,1),p50=np.median(x),p99=np.percentile(x,99),mx=x.max(),
            hmin=hmin,hmax=hmax,hmax_at=argmax,jmin=jmin,jmax=jmax,above_hmax=float((x>hmax).mean()) if hmax>0 else float((x>0.005).mean()),
            above_jmax=float((x>jmax).mean()) if jmax>0 else float((x>0.005).mean())))
json.dump(res,open(B+'split_vs_history.json','w'),default=float)
print('total concentration per pool:',{g:round(D[i][2],3) for i,g in enumerate(order)})
print('\nparty | pool | drawn mean | alpha_i | drawn p1/p50/p99 | history range 24 metro-yrs (max at) | JHB range | P(draw > hist max) | P(> JHB max)')
for r in sorted(res,key=lambda r:-r['mean']):
    if r['mean']<0.004 and r['p99']<0.03: continue
    print(f"{r['party'][:22]:<22s} {r['pool'][:13]:<13s} {r['mean']*100:6.2f} a_i {r['alpha_i']:6.3f}  {r['p01']*100:5.2f}/{r['p50']*100:5.2f}/{r['p99']*100:5.2f}  hist {r['hmin']*100:5.2f}-{r['hmax']*100:5.2f} ({r['hmax_at']})  JHB {r['jmin']*100:5.2f}-{r['jmax']*100:5.2f}  {r['above_hmax']*100:5.1f}% {r['above_jmax']*100:5.1f}%  {'SEEDED' if r['seeded'] else ''}")
# seeded parties summary: share of each pool
for g in order:
    S=[r for r in res if r['pool']==g and r['seeded']]
    print(g,'seeded members',len(S),'median of their p99 within-pool %.2f%%'%(np.median([r['p99'] for r in S])*100),'max p99 %.2f%%'%(max(r['p99'] for r in S)*100), 'their drawn mean %.4f%%'%(np.median([r['mean'] for r in S])*100))
