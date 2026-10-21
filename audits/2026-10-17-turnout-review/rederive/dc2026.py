import pandas as pd, numpy as np
d=pd.read_csv('data/raw/elections/npe2024_JHB_vd_party.csv')
def code(n):
    n=n.upper()
    for k,c in [('AFRICAN NATIONAL CONGRESS','ANC'),('DEMOCRATIC ALLIANCE','DA'),('ECONOMIC FREEDOM','EFF'),('ACTIONSA','ASA'),('UMKHONTO','MK'),('PATRIOTIC ALLIANCE','PA')]:
        if k in n: return c
    return 'OTH'
d['p']=d.sPartyName.map(code)
v=d.groupby(['VD_Number','p']).Party_Votes.sum().unstack(fill_value=0)
val=v.sum(1); reg24=d.groupby('VD_Number').Registered_Population.first()
t=pd.read_csv('data/processed/turnout.csv').set_index('VD_Number')
m=pd.read_csv('data/processed/vd_ward_2026.csv'); reg26=m.groupby('VD_Number').part_registered_2026.sum()
x=pd.concat([v,val.rename('val'),reg24.rename('reg24'),reg26.rename('reg26'),t[['turnout_2026_projected','turnout_2026_level']]],axis=1,join='inner')
x=x[x.turnout_2026_projected.notna()&(x.reg26>0)]
s=x[['ANC','DA','EFF','MK','ASA','PA']].div(x.val,axis=0)
t24=x.val/x.reg24
def shares(w): return 100*(s.mul(w,axis=0).sum()/w.sum())
base=shares(x.reg26*t24)          # 2024 national turnout pattern on the 2026 roll
for name,tt in [('ratio',x.turnout_2026_projected),('level',x.turnout_2026_level),('centre 50/50',0.5*x.turnout_2026_projected+0.5*x.turnout_2026_level)]:
    print(name, (shares(x.reg26*tt)-base).round(2).to_dict())
print('VDs used', len(x), 'roll share', round(x.reg26.sum()/reg26.sum(),3))
