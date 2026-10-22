import csv, sys, math, json
from collections import defaultdict
from datetime import date
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R/'src'))
import parties as P
CODES = ['JHB','TSH','EKU','ETH','CPT','NMA','BUF','MAN']
npe = defaultdict(lambda: defaultdict(int)); vd_city = {}
for c in CODES:
    for r in csv.DictReader(open(R/f'data/raw/elections/npe2024_{c}_vd_party.csv', encoding='utf-8')):
        npe[r['VD_Number']][P.canonical(r['sPartyName'])] += int(r['Party_Votes']); vd_city[r['VD_Number']] = c
bye = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
for r in csv.DictReader(open(R/'data/raw/byelections/byelections_SA_vd_party.csv', encoding='utf-8')):
    if date.fromisoformat(r['ByElectionDate']) <= date(2024,5,29): continue
    if r['VD_Number'] not in vd_city: continue
    bye[(r['ByElectionDate'], r['WardID'])][r['VD_Number']][P.canonical(r['PartyFullName'])] += int(r['Party_Votes'])
rows = []; unmatched = 0
for (d, w), vds in sorted(bye.items()):
    city = {vd_city[v] for v in vds}; assert len(city) == 1
    b = defaultdict(int); n = defaultdict(int)
    for v, pv in vds.items():
        for p, x in pv.items(): b[p] += x
        for p, x in npe[v].items(): n[p] += x
    bt, nt = sum(b.values()), sum(n.values())
    stood = set(b)
    for p in set(n) | stood:
        ns = n[p]/nt if nt else 0
        if ns < 0.03: continue
        bs = b[p]/bt if bt else 0
        rows.append(dict(date=d, ward=w, city=city.pop() if False else list(city)[0], party=p, npe=ns, bye=bs, stood=p in stood, bt=bt, vds=len(vds)))
json.dump(rows, open(Path(__file__).with_name('rows.json'), 'w'), indent=0)  
print(len(bye), 'contests;', len(rows), 'party-contest rows')
def summ(sel):
    out = {}
    for p in sorted({r['party'] for r in sel}):
        for ver in 'AB':
            rs = [r for r in sel if r['party']==p and (r['stood'] or ver=='B')]
            if not rs: continue
            pos = [math.log(r['bye']/r['npe']) for r in rs if r['bye']>0]
            vw = sum(r['bye']*r['bt'] for r in rs)/sum(r['npe']*r['bt'] for r in rs)
            med = sorted([r['bye']/r['npe'] for r in rs])[len(rs)//2]
            out[(p,ver)] = (len(rs), sum(not r['stood'] for r in rs), med, vw)
    return out
for label, sel in [('JHB', [r for r in rows if r['city']=='JHB']), ('8 metros', rows)]:
    print('\n==', label, '  party ver  n  notstood  median_ratio  voteweighted_ratio')
    for (p,ver),(k,ns,med,vw) in summ(sel).items():
        if k >= 3: print(f'{p:10s} {ver} {k:3d} {ns:3d}  {med:6.3f}  {vw:6.3f}')
print('\nMK contests:')
for r in rows:
    if r['party']=='MK': print(r['date'], r['city'], r['ward'], f"npe {r['npe']:.3f} bye {r['bye']:.3f} stood {r['stood']} valid {r['bt']}")
