exec(open('run2.py').read().split("cur=I.")[0])
I0=I.copy(); rng=np.random.default_rng(2)
# null: fitter's power to absorb spread. Targets = current-rule ward sums x random growth sd 0.17 (same spread as current-rule ratios)
P=c.groupby('WardID_2026').part_registered.sum().reindex(wards).values
for rep in range(4):
    I=I0.copy(); I['Registered']=(P*rng.normal(1.03,0.168,len(wards))).round()
    r=solve(cw,countpen=1e6); print('null rep',rep,'post-fit sd',round(ratios(r[1]).std(),4),'countdev',r[2])
I=I0
