import pandas as pd, json, numpy as np, sys
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
R='/Users/simondavis/projects/atlas-jhb-election-model/'
c=pd.read_csv(R+'data/processed/vd_ward_2026.csv')
I=pd.read_csv(R+'archive/iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv').set_index('Ward')
g=json.load(open(R+'data/raw/geo/votingstations2026_JHB.geojson'))
s=pd.DataFrame([f['properties'] for f in g['features']]).set_index('VOTINGDIST')
vdreg=c.groupby('VD_Number').vd_registered.first()
wards=list(I.index); W={w:k for k,w in enumerate(wards)}
G=I.Registered.sum()/vdreg.sum()

def solve(cands, maxdrop=3, countpen=None, force=None, ndrop_exact=None, gg=G, extra=None):
    """cands: dict vd->list of wards. countpen None => hard count equality."""
    vds=list(cands); pairs=[(v,w) for v in vds for w in cands[v]]
    nx=len(pairs); nd=len(vds); nw=len(wards)
    # vars: x(pairs), drop(nd), e+ e- (nw each) for registration resid, c+ c- (nw) for counts
    n=nx+nd+4*nw
    cost=np.zeros(n); cost[nx+nd:nx+nd+2*nw]=1.0
    if countpen is not None: cost[nx+nd+2*nw:]=countpen
    integ=np.zeros(n); integ[:nx+nd]=1
    lb=np.zeros(n); ub=np.full(n,np.inf); ub[:nx+nd]=1
    if countpen is None: ub[nx+nd+2*nw:]=0
    rows=[];lo=[];hi=[]
    A=lil_matrix((nd+1+2*nw+ (len(extra) if extra else 0),n))
    vi={v:k for k,v in enumerate(vds)}
    r=0
    for k,(v,w) in enumerate(pairs): A[vi[v],k]=1
    for v in vds: A[vi[v],nx+vi[v]]=1
    lo+= [1]*nd; hi+=[1]*nd; r=nd
    for v in vds: A[r,nx+vi[v]]=1
    lo.append(ndrop_exact if ndrop_exact is not None else 0); hi.append(ndrop_exact if ndrop_exact is not None else maxdrop); r+=1
    # count: sum x - c+ + c- = iec
    for k,(v,w) in enumerate(pairs): A[r+W[w],k]=1
    for j in range(nw): A[r+j,nx+nd+2*nw+j]=-1; A[r+j,nx+nd+3*nw+j]=1
    lo+=list(I.Voting_Districts.values); hi+=list(I.Voting_Districts.values); r+=nw
    # reg: sum vdreg x - e+ + e- = iec/g
    for k,(v,w) in enumerate(pairs): A[r+W[w],k]=vdreg[v]
    for j in range(nw): A[r+j,nx+nd+j]=-1; A[r+j,nx+nd+nw+j]=1
    tgt=I.Registered.values/gg; lo+=list(tgt); hi+=list(tgt); r+=nw
    if extra:
        for (pr,l,h) in extra:
            for (v,w) in pr: A[r,pairs.index((v,w))]=1
            lo.append(l);hi.append(h); r+=1
    if force:
        for (v,w) in force:
            for k,(vv,ww) in enumerate(pairs):
                if vv==v: ub[k]= 1 if ww==w else 0
            ub[nx+vi[v]]=0
    res=milp(cost,constraints=LinearConstraint(A.tocsr(),lo,hi),integrality=integ,bounds=Bounds(lb,ub),options={'time_limit':120,'mip_rel_gap':1e-6})
    if res.x is None: return None
    x=res.x
    asg={v:None for v in vds}
    for k,(v,w) in enumerate(pairs):
        if x[k]>0.5: asg[v]=w
    cdev=x[nx+nd+2*nw:nx+nd+3*nw]+x[nx+nd+3*nw:]
    return res.fun, asg, cdev.sum(), res
