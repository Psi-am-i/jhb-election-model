import sys, csv, glob, json, collections, numpy as np
sys.path.insert(0,'src'); import parties as P
res={}
for f in sorted(glob.glob('data/raw/elections/lge*_*_vd_party_clean.csv')):
    yr=f.split('lge')[1][:4]; metro=f.split('_')[1]
    wv=collections.defaultdict(collections.Counter); tot={'PR':collections.Counter(),'Ward':collections.Counter()}
    for r in csv.DictReader(open(f,encoding='utf-8')):
        b=r['BallotType']; 
        if b not in tot: continue
        p=P.canonical(r['sPartyName']); v=int(float(r['Party_Votes'] or 0)); tot[b][p]+=v
        if b=='Ward' and r['Ward']: wv[r['Ward']][p]+=v
    nw=len(wv); sp=sum(tot['PR'].values()); sw=sum(tot['Ward'].values())
    d={}
    for p in tot['PR']:
        if tot['PR'][p]/sp>0.001:
            c=sum(1 for w in wv if wv[w][p]>0)/nw
            d[p]=(tot['Ward'][p]/sw/(tot['PR'][p]/sp), c, tot['PR'][p]/sp)
    res[f'{metro}-{yr}']=d
json.dump(res,open(sys.argv[1],'w'))
yrs=['2000','2006','2011','2016','2021']
X=[];Y=[];rows=[]
for m in sorted({k.split('-')[0] for k in res}):
    for a,b in zip(yrs,yrs[1:]):
        A=res[f'{m}-{a}']; B=res[f'{m}-{b}']
        for p in set(A)&set(B):
            if p=='IND': continue
            ra,ca,sa=A[p]; rb,cb,sb=B[p]
            if ca>0 and cb>0 and ra>0 and rb>0:
                X.append(np.log(cb/ca)); Y.append(np.log(rb/ra)); rows.append((m,b,p,ca,cb,ra,rb,sb))
X=np.array(X);Y=np.array(Y)
sl=(X*Y).sum()/(X*X).sum(); b1=np.polyfit(X,Y,1)
print('n pairs',len(X),'slope through origin %.3f, OLS slope %.3f intercept %.3f, corr %.3f'%(sl,b1[0],b1[1],np.corrcoef(X,Y)[0,1]))
big=[(r,x,y) for r,x,y in zip(rows,X,Y) if r[4]/r[3]>=1.8]
print('cases where contestation rose >=1.8x:',len(big))
for r,x,y in sorted(big,key=lambda t:-t[1])[:25]:
    print(f"  {r[0]} {r[1]} {r[2][:22]:22} contest {r[3]:.2f}->{r[4]:.2f} (x{r[4]/r[3]:.2f}) ratio {r[5]:.2f}->{r[6]:.2f} (x{r[6]/r[5]:.2f}) model would predict x{min(r[4]/r[3], 2.0/r[5]):.2f}")
yb=np.array([y for _,_,y in big]); xb=np.array([x for _,x,_ in big])
print('in those: median realised ratio change x%.2f, median contest change x%.2f'%(np.exp(np.median(yb)),np.exp(np.median(xb))))
