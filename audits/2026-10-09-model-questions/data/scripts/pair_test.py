"""Across consecutive LGE pairs: predict each party's ward share at t from its actual list share at t
times ratio_{t-1} x change, change = 1 (none) / count-based now/was / vote-weighted now/was.
Vote weights = the party's t-1 PR votes per VD, placed in t's wards via VD number. World-only test."""
import os, sys, glob, json, csv
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0,'src')
from collections import defaultdict
import numpy as np
import parties as P
def read(f):
    pr=defaultdict(int); wd=defaultdict(int); prvd=defaultdict(lambda: defaultdict(int)); vdward={}
    wards=set(); cont=defaultdict(set)
    with open(f,encoding='utf-8',errors='replace') as fh:
        for row in csv.DictReader(fh):
            p=P.canonical(row['sPartyName']); v=int(row['Party_Votes']); w=(row.get('Ward') or '').strip(); vd=row['VD_Number']
            if w: vdward[vd]=w
            if row['BallotType']=='PR': pr[p]+=v; prvd[p][vd]+=v
            elif row['BallotType']=='Ward': wd[p]+=v; wards.add(w); cont[p].add(w)
    tp=sum(pr.values()); tw=sum(wd.values())
    return dict(pr={p:v/tp for p,v in pr.items()}, wd={p:v/tw for p,v in wd.items()}, prvd=prvd, vdward=vdward, n=len(wards), cont=cont)
codes=['BUF','CPT','EKU','ETH','JHB','MAN','NMA','TSH']; years=['2000','2006','2011','2016','2021']
D={(c,y):read(f'data/raw/elections/lge{y}_{c}_vd_party_clean.csv') for c in codes for y in years}
rows=[]
for c in codes:
    for a,b in zip(years,years[1:]):
        A,B=D[(c,a)],D[(c,b)]
        for p in A['pr']:
            if p not in B['pr'] or A['pr'][p]<=0.001: continue
            if p not in A['cont']: continue      # no ward record at t-1
            r0=A['wd'].get(p,0)/A['pr'][p]
            was_c=len(A['cont'][p])/A['n']; now_c=len(B['cont'].get(p,()))/B['n']
            tot=sum(A['prvd'][p].values())
            was_v=sum(v for vd,v in A['prvd'][p].items() if A['vdward'].get(vd) in A['cont'][p])/tot
            # t-1 PR votes in VDs that exist at t, placed in t's wards
            inB=[(vd,v) for vd,v in A['prvd'][p].items() if vd in B['vdward']]
            totB=sum(v for _,v in inB)
            now_v=(sum(v for vd,v in inB if B['vdward'][vd] in B['cont'].get(p,set()))/totB) if totB else now_c
            rows.append(dict(c=c,a=a,b=b,p=p,pr_t=B['pr'][p],wd_t=B['wd'].get(p,0),r0=r0,was_c=was_c,now_c=now_c,was_v=was_v,now_v=now_v,matched=totB/tot))
json.dump(rows,open('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/pair_rows.json','w'))
print('pairs',len(rows))
def pred(r,form,clip=(0.5,2.0)):
    if form=='none': ch=1
    elif form=='count': ch=(r['now_c']/r['was_c']) if r['was_c'] else 1
    elif form=='vote': ch=(r['now_v']/r['was_v']) if r['was_v'] else 1
    rr=np.clip(r['r0'],*clip)*ch
    rr=np.clip(rr,0,2.0)
    return r['pr_t']*rr
for sub,flt in [('all',lambda r:True),('slate changed by >0.2 (count)',lambda r:abs(r['now_c']-r['was_c'])>0.2),('expanded >=2x by count',lambda r:r['was_c']>0 and r['now_c']/r['was_c']>=2),('list share>=1%',lambda r:r['pr_t']>=0.01)]:
    S=[r for r in rows if flt(r)]
    print(f'\n{sub}: n={len(S)}')
    for form in ('none','count','vote'):
        e=np.array([(pred(r,form)-r['wd_t'])*100 for r in S]); w=np.array([r['wd_t'] for r in S])
        print(f"  {form:6s} MAE {np.abs(e).mean():.3f}pt  vote-wtd MAE {np.average(np.abs(e),weights=w+1e-9):.3f}pt  mean err {e.mean():+.3f}  worst {e[np.argmax(np.abs(e))]:+.2f}")
S=[r for r in rows if r['was_c']>0 and r['now_c']/r['was_c']>=2]
print('\nparties whose slate at least doubled (count):')
for r in sorted(S,key=lambda r:-r['pr_t'])[:25]:
    print(f"{r['c']}{r['a']}->{r['b']} {r['p'][:22]:<22s} list_t {r['pr_t']*100:5.2f} ward_t {r['wd_t']*100:5.2f} r0 {r['r0']:.2f} cnt {r['was_c']:.2f}->{r['now_c']:.2f} vote {r['was_v']:.2f}->{r['now_v']:.2f}  pred none {pred(r,'none')*100:5.2f} count {pred(r,'count')*100:5.2f} vote {pred(r,'vote')*100:5.2f}  matched {r['matched']:.2f}")
