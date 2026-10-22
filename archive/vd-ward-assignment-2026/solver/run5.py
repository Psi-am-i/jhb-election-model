exec(open('run2.py').read().split("cur=I.")[0])
truth=solve(cw,countpen=1e6,ndrop_exact=0)[1]
S=pd.Series(0.0,index=wards); C=pd.Series(0,index=wards)
for v,w in truth.items(): S[w]+=vdreg[v]; C[w]+=1
I0=I.copy()
rng=np.random.default_rng(1)
for sig in [0.04,0.05]:
  for rep in range(4):
    gw=rng.normal(1.03,sig,len(wards))
    I=I0.copy(); I['Registered']=(S.values*gw).round(); I['Voting_Districts']=C.values
    G2=I.Registered.sum()/vdreg.sum()
    a=solve(cw,countpen=1e6,ndrop_exact=0,gg=G2)[1]; b=solve(cw,countpen=0.0,ndrop_exact=0,gg=G2)[1]
    rec=lambda x: sum(x[v]==truth[v] for v in split)
    print(f'sig={sig} rep={rep} recovered with counts {rec(a)}/{len(split)}, reg-only {rec(b)}/{len(split)}, post-fit sd {ratios(a).std():.4f} vs true sd {np.std(gw):.4f}')
I=I0
