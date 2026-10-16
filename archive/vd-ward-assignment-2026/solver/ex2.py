import pandas as pd, json
R='/Users/simondavis/projects/atlas-jhb-election-model/'
c=pd.read_csv(R+'data/processed/vd_ward_2026.csv')
i=pd.read_csv(R+'archive/iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv').set_index('Ward')
g=json.load(open(R+'data/raw/geo/votingstations2026_JHB.geojson'))
s=pd.DataFrame([f['properties'] for f in g['features']]).set_index('VOTINGDIST')
c['stward']=c.VD_Number.map(s.WARD)
pd.set_option('display.width',200)
for w in [79800027,79800059,79800063,79800064,79800065,79800096,79800113]:
    print('WARD',w,'iec',i.loc[w].tolist())
    print(c[c.WardID_2026==w][['VD_Number','vd_registered','part_registered','is_split','stward']].to_string())
# whole VDs whose station ward differs
wh=c[c.is_split!='Y']; print('whole VDs stward!=ward', (wh.stward!=wh.WardID_2026).sum())
sp=c[c.is_split=='Y']; ok=sp.groupby('VD_Number').apply(lambda d:(d.stward==d.WardID_2026).any()); print('split VDs whose stward in parts', ok.sum(), len(ok))
# station counts per ward match
sc=s.groupby('WARD').size(); print('station-count match', (sc.reindex(i.index).fillna(0)==i.Voting_Districts).sum())
