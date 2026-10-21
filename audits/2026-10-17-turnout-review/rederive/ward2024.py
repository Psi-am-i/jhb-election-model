import pandas as pd
d=pd.read_csv('data/raw/elections/npe2024_JHB_vd_party.csv')
m=pd.read_csv('data/processed/vd_ward_2026.csv')
def code(n):
    n=n.upper()
    for k,c in [('AFRICAN NATIONAL CONGRESS','ANC'),('DEMOCRATIC ALLIANCE','DA'),('ECONOMIC FREEDOM','EFF'),('ACTIONSA','ASA'),('UMKHONTO','MK'),('PATRIOTIC ALLIANCE','PA'),('INKATHA','IFP')]:
        if k in n: return c
    return 'OTH:'+n
d['p']=d.sPartyName.map(code)
v=d.groupby(['VD_Number','p']).Party_Votes.sum().unstack(fill_value=0)
x=m.merge(v,left_on='VD_Number',right_index=True,how='left').fillna(0)
cols=[c for c in v.columns]
w=x[cols].multiply(x.weight,axis=0).groupby(x.Ward_2026).sum()
print('VDs in map not in 2024 file:', (~m.VD_Number.isin(v.index)).sum(), 'of', m.VD_Number.nunique())
win=w.idxmax(axis=1)
print('wards:',len(w)); print(win.value_counts().head(8).to_string())
tot=w.sum(); print('citywide 2024 national shares, joined:'); print((100*tot/tot.sum()).sort_values(ascending=False).head(7).round(2).to_string())
s=w.div(w.sum(1),axis=0)
anc=win=='ANC'
print('ANC-won wards: median ANC share %.1f, median margin over 2nd %.1f'%(100*s.ANC[anc].median(), 100*(s[anc].apply(lambda r: r.sort_values().iloc[-1]-r.sort_values().iloc[-2],axis=1)).median()))
