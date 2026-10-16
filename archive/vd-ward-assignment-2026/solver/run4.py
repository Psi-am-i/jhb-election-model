import time
exec(open('run2.py').read().split("cur=I.")[0])
r0=solve(cw,countpen=1e6,ndrop_exact=0); print('no-drop countdev',r0[2],'resid',r0[0]-1e6*r0[2], desc(ratios(r0[1])))
t=time.time(); r=solve(cw,countpen=1e6); print('base',r[2],r[0]-1e6*r[2],time.time()-t)
asg=r[1]; base=r[0]
rows=[]
for v in split:
    for w in cw[v]:
        if w==asg[v]: continue
        rr=solve(cw,countpen=1e6,force=[(v,w)])
        rows.append((v,asg[v],w,(rr[0]-base) if rr else np.inf, (rr[2]-r[2]) if rr else np.inf))
d=pd.DataFrame(rows,columns=['vd','sol','alt','dobj','dcount'])
d.to_csv('alts.csv',index=False)
m=d.groupby('vd').agg(mindobj=('dobj','min'),mindc=('dcount','min'))
print(m.mindobj.describe()); print('alt ties (dobj<1):',(m.mindobj<1).sum(),' <500:',(m.mindobj<500).sum(),' <1000:',(m.mindobj<1000).sum(),' count-worsening(all alts):',(m.mindc>0).sum())
dropped=[v for v,w in asg.items() if w is None]
out=[]
for v in cw:
    if v in dropped: out.append((v,'','dropped'))
    elif len(cw[v])==1: out.append((v,asg[v],'forced'))
    else: out.append((v,asg[v],'forced' if m.mindobj[v]>=1000 else 'free'))
pd.DataFrame(out,columns=['VD_Number','ward_2026','status']).to_csv('assignment.csv',index=False)
print(pd.DataFrame(out)[2].value_counts())
rt=ratios(asg); print('top ratios', rt.sort_values().tail(5).round(3).to_dict(), rt.sort_values().head(3).round(3).to_dict())
