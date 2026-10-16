exec(open('solve.py').read())
cw={v:list(d.WardID_2026) for v,d in c.groupby('VD_Number')}
split=[v for v in cw if len(cw[v])>1]
touched=set(w for v in split for w in cw[v])
untouched=[w for w in wards if w not in touched]
def ratios(asg):
    S=pd.Series({w:0.0 for w in wards})
    for v,w in asg.items():
        if w is not None: S[w]+=vdreg[v]
    return I.Registered/S
def desc(r): return dict(min=round(r.min(),3),q1=round(r.quantile(.25),3),med=round(r.median(),3),q3=round(r.quantile(.75),3),max=round(r.max(),3),sd=round(r.std(),4),n=len(r))
cur=I.Registered/c.groupby('WardID_2026').part_registered.sum()
print('current rule all', desc(cur)); print('current untouched', desc(cur[untouched])); print('current touched', desc(cur[list(touched)]))
# station rule
st=ratios({v:s.WARD[v] for v in cw}); print('station all',desc(st))
cnt_st=s.groupby('WARD').size().reindex(wards).fillna(0); print('station count abs dev', (cnt_st-I.Voting_Districts).abs().sum())
cnt_cw_whole=c[c.is_split!='Y'].groupby('WardID_2026').size().reindex(wards).fillna(0)
print('untouched wards:',len(untouched),'count match among untouched', (cnt_cw_whole[untouched]==I.Voting_Districts[untouched]).sum())
print((I.Voting_Districts[untouched]-cnt_cw_whole[untouched]).value_counts())
