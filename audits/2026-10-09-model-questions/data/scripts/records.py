"""Amendment 2: each party's within-group record and the group ceiling, from the fit's own yearly splits;
then the drawn 2026 splits against them. Units: percentage points of the group's vote."""
import json, pickle, sys, numpy as np
from collections import defaultdict
B='/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/'
H=json.load(open(B+'hist_splits.json')); cap=sys.argv[1] if len(sys.argv)>1 else 'split_capture.pkl'
C=pickle.load(open(B+cap,'rb'))
SPLITS={'COPE','EFF','NFP','GOOD','MK','ASA'}   # pools.SPLITS registry (pools.py:3629)
years=['2011','2016','2021']; out={'groups':{}}
for g,h in H.items():
    lab=h['labels']; P=h['parties']; S=np.array(h['splits'])*100
    metros=sorted({l[:3] for l in lab}); idx={l:i for i,l in enumerate(lab)}
    rec={}; moves=[]
    for k,p in enumerate(P):
        x=S[:,k]
        if x.max()<=0: continue
        per={}
        for m in metros:
            v=[x[idx[m+y]] if (m+y) in idx else np.nan for y in years]
            per[m]=v
            for a,b,ya,yb in [(v[0],v[1],'2011','2016'),(v[1],v[2],'2016','2021')]:
                if np.isnan(a) or np.isnan(b): continue
                kind='ordinary'
                if a<=0.005 and b>0: kind='arrival' + (' (declared split)' if p in SPLITS else '')
                elif b<=0.005 and a>0: kind='exit'
                elif a>=1.0 and b<0.25*a: kind='collapse (<25% of previous)'
                moves.append(dict(party=p,metro=m,frm=ya,to=yb,a=a,b=b,d=b-a,kind=kind))
        own=[mv for mv in moves if mv['party']==p and mv['kind']=='ordinary']
        rec[p]=dict(min=float(x.min()),max=float(x.max()),
                    jhb=[float(t) for t in per.get('JHB',[np.nan]*3)],
                    per_metro={m:[None if np.isnan(t) else round(float(t),2) for t in v] for m,v in per.items()},
                    largest_move=(max(own,key=lambda mv:abs(mv['d'])) if own else None))
    ordinary=[mv for mv in moves if mv['kind']=='ordinary']
    ceil=max(ordinary,key=lambda mv:abs(mv['d']))
    rise=max(ordinary,key=lambda mv:mv['d']); fall=min(ordinary,key=lambda mv:mv['d'])
    top_all=sorted(moves,key=lambda mv:-abs(mv['d']))[:8]
    out['groups'][g]=dict(ceiling=ceil,largest_rise=rise,largest_fall=fall,records=rec,top_moves_all_kinds=top_all,
                          n_moves=len(moves),n_ordinary=len(ordinary),
                          kinds={k:sum(1 for mv in moves if mv['kind']==k) for k in {mv['kind'] for mv in moves}},
                          size_vs_move=[(mv['a'],abs(mv['d'])) for mv in ordinary])
    print(f"\n=== {g}: {len(moves)} moves, {len(ordinary)} ordinary; kinds {out['groups'][g]['kinds']}")
    print(f"  CEILING |move| {abs(ceil['d']):.2f}pp: {ceil['party']} {ceil['metro']} {ceil['frm']}->{ceil['to']} {ceil['a']:.2f}->{ceil['b']:.2f}")
    print(f"  largest rise {rise['d']:+.2f} {rise['party']} {rise['metro']}{rise['to']}; largest fall {fall['d']:+.2f} {fall['party']} {fall['metro']}{fall['to']}")
    print('  largest moves of any kind:', '; '.join(f"{mv['party']} {mv['metro']}{mv['frm'][2:]}-{mv['to'][2:]} {mv['d']:+.1f} [{mv['kind']}]" for mv in top_all[:6]))
    # size dependence
    a=np.array([s for s,_ in out['groups'][g]['size_vs_move']]); d=np.array([m for _,m in out['groups'][g]['size_vs_move']])
    for lo,hi in [(0.005,1),(1,5),(5,20),(20,101)]:
        sel=(a>=lo)&(a<hi)
        if sel.any(): print(f"  starting share {lo}-{hi}%: n {sel.sum():3d} median |move| {np.median(d[sel]):5.2f} max {d[sel].max():5.2f} median |move|/start {np.median(d[sel]/a[sel]):.2f}")
# correlated moves: within a metro transition, ANC change vs sum of others in Black African
g='Black African'; h=H[g]; P=h['parties']; S=np.array(h['splits'])*100; lab=h['labels']; idx={l:i for i,l in enumerate(lab)}
print('\nBlack African, ANC move vs EFF+ASA+MK move per metro transition:')
for m in sorted({l[:3] for l in lab}):
    for ya,yb in [('2011','2016'),('2016','2021')]:
        if m+ya in idx and m+yb in idx:
            dA=S[idx[m+yb],P.index('ANC')]-S[idx[m+ya],P.index('ANC')]
            dO=sum(S[idx[m+yb],P.index(q)]-S[idx[m+ya],P.index(q)] for q in ('EFF','ASA') if q in P)
            print(f"  {m} {ya}->{yb}: ANC {dA:+6.2f}  EFF+ASA {dO:+6.2f}")
# draws vs records
order=C['pools']['order']; mem=C['pools']['members']; D=C['dir']; npool=len(order); N=len(D)//npool
rows=[]
for gi,g in enumerate(order):
    G=out['groups'][g]; ceil=abs(G['ceiling']['d']); draws=np.array([D[d*npool+gi][1] for d in range(N)])*100
    for j,p in enumerate(mem[g]):
        x=draws[:,j]; r=G['records'].get(p)
        last=r['jhb'][2] if r and not np.isnan(r['jhb'][2]) else 0.0
        mv=np.abs(x-last)
        if r:
            own_out=float(((x>r['max'])|(x<r['min'])).mean()); lm=abs(r['largest_move']['d']) if (r['largest_move'] and abs(r['largest_move']['d'])>0.05) else None
            own_move=float((mv>lm).mean()) if lm is not None else None
        else: own_out=None; own_move=None; lm=None
        mu=np.array([D[d*npool+gi][0][j] for d in range(N)])*100
        resid=np.abs(x-mu)
        rows.append(dict(mean_mu=float(mu.mean()),frac_resid_beyond_ceiling=float((resid>ceil).mean()),frac_resid_beyond_own=(float((resid>lm).mean()) if lm is not None else None),group=g,party=p,has_record=r is not None,last_jhb2021=last,own_min=r['min'] if r else None,own_max=r['max'] if r else None,
                         own_largest_move=lm,ceiling=ceil,p01=float(np.percentile(x,1)),p50=float(np.median(x)),p99=float(np.percentile(x,99)),
                         frac_outside_own_range=own_out,frac_move_beyond_own_largest=own_move,frac_move_beyond_ceiling=float((mv>ceil).mean()),
                         n_beyond_ceiling=int((mv>ceil).sum())))
out['draws']=dict(N=N,capture=cap,rows=rows)
json.dump(out,open(B+'records.json','w'),default=lambda o: o if not isinstance(o,np.floating) else float(o))
print(f'\nDRAWS (N={N}) against records. move = draw minus JHB 2021 share in that group.')
for g in order:
    print(f'\n-- {g} (ceiling {out["groups"][g]["ceiling"]["d"]:+.2f}pp)')
    R=[r for r in rows if r['group']==g and (r['p99']>=1 or (r['has_record'] and r['own_max']>=1))]
    for r in sorted(R,key=lambda r:-r['p50']):
        oo='  n/a ' if r['frac_outside_own_range'] is None else f"{100*r['frac_outside_own_range']:5.1f}%"
        om='  n/a ' if r['frac_move_beyond_own_largest'] is None else f"{100*r['frac_move_beyond_own_largest']:5.1f}%"
        rng='no record' if not r['has_record'] else f"{r['own_min']:5.1f}-{r['own_max']:5.1f}"
        lm='' if r['own_largest_move'] is None else f"{r['own_largest_move']:5.1f}"
        print(f"  {r['party'][:24]:<24s} JHB21 {r['last_jhb2021']:5.1f} own {rng:<12s} own-max-move {lm:>5s} | draw p1/p50/p99 {r['p01']:5.1f}/{r['p50']:5.1f}/{r['p99']:5.1f} | outside own range {oo} beyond own move {om} beyond ceiling {100*r['frac_move_beyond_ceiling']:5.1f}% | mean {r['mean_mu']:5.1f} split-residual beyond ceiling {100*r['frac_resid_beyond_ceiling']:5.1f}%")
    nr=[r for r in rows if r['group']==g and not r['has_record']]
    print(f"  no-record members: {len(nr)}; draws with any no-record member above 5pp: see summary")
# any no-record member > x in a draw
for gi,g in enumerate(order):
    draws=np.array([D[d*npool+gi][1] for d in range(N)])*100
    nr=[j for j,p in enumerate(mem[g]) if p not in out['groups'][g]['records']]
    mx=draws[:,nr].max(1)
    print(f'{g}: draws in which some no-record party takes >=5pp of the group {100*(mx>=5).mean():.1f}%, >=10pp {100*(mx>=10).mean():.1f}%')
