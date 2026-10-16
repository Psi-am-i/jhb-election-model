import pandas as pd, json, numpy as np
R='/Users/simondavis/projects/atlas-jhb-election-model/'
c=pd.read_csv(R+'data/processed/vd_ward_2026.csv')
i=pd.read_csv(R+'archive/iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv')
print(c.shape, c.VD_Number.nunique(), c.groupby('VD_Number').vd_registered.first().sum(), c.part_registered.sum())
print(i.shape, i.Voting_Districts.sum(), i.Registered.sum())
print(c.groupby('VD_Number').size().value_counts())
vd=c.groupby('VD_Number').vd_registered.first().sort_values(); print(vd.head(8))
print(c[c.part_registered==0].shape, c[c.part_registered==0].head())
g=json.load(open(R+'data/raw/geo/votingstations2026_JHB.geojson'))
s=pd.DataFrame([f['properties'] for f in g['features']])
print(s.VOTINGDIST.nunique(), len(s), set(s.VOTINGDIST)^set(c.VD_Number))
# whole-VD forced counts per ward vs IEC
whole=c[c.is_split!='Y']; wc=whole.groupby('WardID_2026').size()
sp=c[c.is_split=='Y']; spc=sp.groupby('WardID_2026').VD_Number.nunique()
i=i.set_index('Ward'); d=pd.DataFrame({'iec':i.Voting_Districts,'whole':wc,'splitparts':spc}).fillna(0)
d['need']=d.iec-d.whole
print(d.need.describe()); print((d.need<0).sum(), (d.need>d.splitparts).sum())
print(d[(d.need<0)|(d.need>d.splitparts)])
