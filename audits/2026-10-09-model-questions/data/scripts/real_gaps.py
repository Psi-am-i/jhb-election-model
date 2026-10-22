"""Real ward-minus-list gaps in the 40 cleaned metro LGE files; contestation by count and by vote."""
import os, sys, glob, json, csv
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0,'src')
from collections import defaultdict
import numpy as np
import parties as P
rows=[]
files=sorted(glob.glob('data/raw/elections/lge*_*_vd_party_clean.csv'))
print(len(files),'files')
per={}
for f in files:
    yr=f.split('/')[-1][3:7]; code=f.split('_')[1]
    pr=defaultdict(int); wd=defaultdict(int)
    pr_vd=defaultdict(lambda: defaultdict(int))   # party -> ward -> PR votes
    wards_all=set(); contested=defaultdict(set)
    with open(f,encoding='utf-8',errors='replace') as fh:
        for row in csv.DictReader(fh):
            p=P.canonical(row['sPartyName']); v=int(row['Party_Votes']); w=(row.get('Ward') or '').strip()
            if row['BallotType']=='PR':
                pr[p]+=v; pr_vd[p][w]+=v
            elif row['BallotType']=='Ward':
                wd[p]+=v; wards_all.add(w); contested[p].add(w)
    tp=sum(pr.values()); tw=sum(wd.values()); n=len(wards_all)
    for p in set(pr)|set(wd):
        ps=pr.get(p,0)/tp; ws=wd.get(p,0)/tw
        totpr=sum(pr_vd[p].values())
        vcov=(sum(v for w,v in pr_vd[p].items() if w in contested[p])/totpr) if totpr else None
        rows.append(dict(file=f'{code}{yr}',code=code,year=yr,party=p,pr=ps*100,ward=ws*100,gap=(ps-ws)*100,
                         ccount=len(contested[p])/n if n else None,cvote=vcov))
json.dump(rows,open('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/real_rows.json','w'))
g=np.array([r['gap'] for r in rows])
print('rows',len(rows),'gap (list-ward) min',g.min().round(2),'max',g.max().round(2))
for r in sorted(rows,key=lambda r:r['gap'])[:8]: print('most neg',r['file'],r['party'],round(r['pr'],2),round(r['ward'],2),round(r['gap'],2),r['ccount'] and round(r['ccount'],3),r['cvote'] and round(r['cvote'],3))
for r in sorted(rows,key=lambda r:-r['gap'])[:8]: print('most pos',r['file'],r['party'],round(r['pr'],2),round(r['ward'],2),round(r['gap'],2),r['ccount'] and round(r['ccount'],3),r['cvote'] and round(r['cvote'],3))
for r in rows:
    if r['party'] in ('PA','ASA') and r['year'] in ('2016','2021'): print(r)
# relative gap, parties >=2% list
big=[r for r in rows if r['pr']>=2]
rel=np.array([r['ward']/r['pr'] for r in big])
print('parties >=2% list: n',len(big),'ward/list ratio min',rel.min().round(3),'max',rel.max().round(3),'p5,p95',np.percentile(rel,[5,95]).round(3))
for r in sorted(big,key=lambda r:r['ward']/r['pr'])[-6:]: print(' high ratio',r['file'],r['party'],round(r['pr'],2),round(r['ward'],2),round(r['ward']/r['pr'],3),round(r['ccount'],3),round(r['cvote'],3))
for r in sorted(big,key=lambda r:r['ward']/r['pr'])[:6]: print(' low ratio',r['file'],r['party'],round(r['pr'],2),round(r['ward'],2),round(r['ward']/r['pr'],3),round(r['ccount'],3),round(r['cvote'],3))
