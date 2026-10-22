exec(open('solve.py').read())
cw={v:list(d.WardID_2026) for v,d in c.groupby('VD_Number')}
cs={v:sorted(set(cw[v])|{s.WARD[v]}) for v in cw}
for name,cand in [('crosswalk',cw),('crosswalk+station',cs)]:
    r=solve(cand); print(name,'hard', None if r is None else (r[0],r[2]))
    r=solve(cand,countpen=1e6); print(name,'soft', (r[0]%1e6, r[2]))
