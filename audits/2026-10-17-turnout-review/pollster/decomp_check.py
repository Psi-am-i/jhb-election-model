import sys
sys.path.insert(0,'/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-17-turnout-review/measure')
import common as C, cityconfig, numpy as np
res=[]
for city in C.CITIES:
    cityconfig.use(city)
    for y0,y1 in [("2011","2016"),("2016","2021")]:
        cityconfig.use_target(y1)
        try:
            t0=C.realised_turnout(y0); t1=C.realised_turnout(y1); v0=C.pr_votes(y0); v1=C.pr_votes(y1)
        except Exception as e:
            print(city,y0,e); continue
        vds=[v for v in v0 if v in v1 and v in t0 and v in t1 and t0[v][0]>0 and t1[v][0]>0]
        for party in ["DA","ANC"]:
            s0=np.array([v0[v].get(party,0)/max(sum(v0[v].values()),1) for v in vds])
            s1=np.array([v1[v].get(party,0)/max(sum(v1[v].values()),1) for v in vds])
            r0=np.array([t0[v][0] for v in vds],float); r1=np.array([t1[v][0] for v in vds],float)
            T0=np.array([t0[v][1] for v in vds])/r0; T1=np.array([t1[v][1] for v in vds])/r1
            def sh(r,T,s): w=r*T; return (w*s).sum()/w.sum()
            # turnout composition at old registration and at new registration
            a=sh(r0,T1,s0)-sh(r0,T0,s0); b=sh(r1,T1,s0)-sh(r1,T0,s0)
            act=sh(r1,T1,s1)-sh(r0,T0,s0)
            res.append((city,y0,y1,party,len(vds),100*act,100*a,100*b))
for r in res: print("%-17s %s->%s %-3s n=%4d actual %+6.2f turnout-comp(reg0) %+5.2f (reg1) %+5.2f"%r)
