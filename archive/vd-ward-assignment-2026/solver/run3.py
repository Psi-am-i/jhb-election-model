exec(open('run2.py').read().split("cur=I.")[0])
cur=I.Registered/c.groupby('WardID_2026').part_registered.sum()
print(c[c.VD_Number.map(s.WARD).isin([79800096,79800113]) & ~c.WardID_2026.isin([79800096,79800113])][['VD_Number','WardID_2026','vd_registered','is_split']].assign(st=lambda d:d.VD_Number.map(s.WARD)).to_string())
print('st count 96,113:', (s.WARD==79800096).sum(), (s.WARD==79800113).sum())
cs={v:sorted(set(cw[v])|{s.WARD[v]}) for v in cw}
for name,cand in [('cw',cw),('cw+st',cs)]:
    r=solve(cand,countpen=1e6)
    asg=r[1]; dropped=[v for v,w in asg.items() if w is None]
    cnt=pd.Series([w for w in asg.values() if w is not None]).value_counts().reindex(wards).fillna(0)
    dev=cnt-I.Voting_Districts
    print(name,'countdev',r[2],'wards off',(dev!=0).sum(),'dropped',[(v,vdreg[v]) for v in dropped])
    print(' count residuals', dev[dev!=0].to_dict())
    rr=ratios(asg); print(' ratio all',desc(rr)); print(' ratio count-ok wards',desc(rr[dev==0]))
    # reg-only fit
    r2=solve(cand,countpen=0.0); rr2=ratios(r2[1]); print(' reg-only fit',desc(rr2),'countdev',r2[2])
    nonmod=[v for v in split if asg[v]!=s.WARD[v]]
    print(' split VDs agree with station', sum(asg[v]==s.WARD[v] for v in split),'/',len(split))
    print(' whole VDs moved off crosswalk', sum(1 for v in cw if len(cw[v])==1 and asg[v] not in (cw[v][0],None)))
