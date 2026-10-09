import sys, csv, glob, json, collections, numpy as np
sys.path.insert(0,'src'); import parties as P
out={}
files=sorted(glob.glob('data/raw/elections/lge*_*_vd_party_clean.csv'))
for f in files:
    yr=f.split('lge')[1][:4]; metro=f.split('_')[1]
    vdinfo={'PR':{}, 'Ward':{}}; votes={'PR':collections.defaultdict(lambda: collections.defaultdict(int)),'Ward':collections.defaultdict(lambda: collections.defaultdict(int))}
    vdward={}
    for r in csv.DictReader(open(f,encoding='utf-8')):
        b=r['BallotType'];
        if b not in vdinfo: continue
        vd=r['VD_Number']; vdinfo[b][vd]=(int(float(r['Registered_Population'] or 0)), int(float(r['Spoilt_Votes'] or 0)), int(float(r['Total_Valid_Votes'] or 0)))
        votes[b][vd][P.canonical(r['sPartyName'])]+=int(float(r['Party_Votes'] or 0))
        if r['Ward']: vdward[vd]=r['Ward']
    rec={}
    for b in ('PR','Ward'):
        reg=sum(v[0] for v in vdinfo[b].values()); sp=sum(v[1] for v in vdinfo[b].values()); va=sum(v[2] for v in vdinfo[b].values())
        rec[b]={'reg':reg,'spoilt':sp,'valid':va,'turnout':(sp+va)/reg if reg else None,'spoilt_share':sp/(sp+va) if sp+va else None}
        tot=collections.Counter()
        for vd,c in votes[b].items():
            for p,n in c.items(): tot[p]+=n
        s=sum(tot.values()); rec[b]['shares']={p:n/s for p,n in tot.items() if n>0}
    # ward winners
    wt=collections.defaultdict(collections.Counter); wp=collections.defaultdict(collections.Counter)
    for vd,c in votes['Ward'].items():
        for p,n in c.items(): wt[vdward.get(vd)][p]+=n
    for vd,c in votes['PR'].items():
        for p,n in c.items(): wp[vdward.get(vd)][p]+=n
    winners=collections.Counter(c.most_common(1)[0][0] for w,c in wt.items() if w and sum(c.values())>0)
    rec['ward_winners']=dict(winners); rec['n_wards']=len([w for w in wt if w])
    # ward-level split-ticket residual
    res=[]
    cw=rec['Ward']['shares']; cp=rec['PR']['shares']
    for w in wt:
        if not w or w not in wp: continue
        tw=sum(wt[w].values()); tp=sum(wp[w].values())
        if tw<500 or tp<500: continue
        for p in wp[w]:
            ps=wp[w][p]/tp; ws=wt[w][p]/tw
            if ps>=0.05 and ws>0 and p in cw and p in cp and p!='IND':
                res.append((p, np.log(ws/ps)-np.log(cw[p]/cp[p])))
    rec['split_resid_sd']=float(np.std([x for _,x in res])) if res else None
    rec['split_resid_n']=len(res)
    rec['split_resid_iqr']=[float(np.percentile([x for _,x in res],q)) for q in (5,25,75,95)] if res else None
    out[f'{metro}-{yr}']=rec
    print(metro, yr, 'PR turnout %.3f spoilt PR %.4f Ward %.4f IND ward %.4f IND wins %d/%d split_sd %.3f n%d'%(rec['PR']['turnout'], rec['PR']['spoilt_share'], rec['Ward']['spoilt_share'], rec['Ward']['shares'].get('IND',0), winners.get('IND',0), rec['n_wards'], rec['split_resid_sd'] or -1, len(res)), flush=True)
json.dump(out, open(sys.argv[1],'w'))
