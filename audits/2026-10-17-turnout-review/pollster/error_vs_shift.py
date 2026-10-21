# Model mean list error (history.json at 4fb8002, N-P) vs realised-minus-projected
# turnout composition shift (partA4, previous-LGE VD shares held fixed).
import json, pandas as pd, numpy as np
R='/Users/simondavis/projects/atlas-jhb-election-model/'
h=json.load(open(R+'data/processed/history.json'))
rows=[]
for r in h['records']:
    v={p[0]:p for p in r['votes']}   # (party, pr_median, pr_mean, pr_actual, ...)
    rows.append(dict(city=r['slug'],target=int(r['year']),DA=100*(v['DA'][2]-v['DA'][3]),ANC=100*(v['ANC'][2]-v['ANC'][3])))
e=pd.DataFrame(rows)
a=pd.read_csv(R+'audits/2026-10-17-turnout-review/measure/partA4_partisan_error.csv')
m=e.merge(a[['city','target','oracle_composition_shift_DA','oracle_composition_shift_ANC']],on=['city','target'])
for p in ['DA','ANC']:
    s=m['oracle_composition_shift_'+p]
    print(p,'corr',round(np.corrcoef(m[p],s)[0,1],2),'MAE',round(m[p].abs().mean(),2),'+shift',round((m[p]+s).abs().mean(),2),'+demeaned',round((m[p]+s-s.mean()).abs().mean(),2))
    m[p+'2']=m[p]+s
print(m.groupby('target')[['DA','DA2','ANC','ANC2']].agg(lambda x:x.abs().mean()).round(2))
print(m.groupby('target')[['DA','ANC']].mean().round(2))
d=pd.read_csv(R+'audits/2026-10-17-turnout-review/measure/partA1_citywide.csv')
print('turnout MAE centre',d.err_centre.abs().mean(),'naive',d.err_naive_prev.abs().mean())
print('cycle-common sd',d.groupby('target').err_centre.mean().std(),'within-cycle rms',((d.err_centre-d.groupby('target').err_centre.transform('mean'))**2).mean()**.5)
b=pd.read_csv(R+'audits/2026-10-17-turnout-review/measure/partB6_within_vd_regression.csv')
q=b[(b.subset=='all_joined')&(b.model=='ds~dt+s0 [not_mixed]')&b.party.isin(['DA','ANC'])&b.pair.isin(['2011-2016','2016-2021'])]
print(q.pivot_table(index='city',columns=['pair','party'],values='slope_share_per_turnout_pt').round(3))
