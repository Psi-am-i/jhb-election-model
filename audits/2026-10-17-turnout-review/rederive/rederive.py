import pandas as pd, numpy as np
R='data/raw/elections/'
def lge(y):
    d=pd.read_csv(R+f'lge{y}_JHB_vd_party_clean.csv')
    vd=d.groupby(['VD_Number','BallotType']).agg(reg=('Registered_Population','first'),sp=('Spoilt_Votes','first'),val=('Total_Valid_Votes','first')).reset_index()
    vd['cast']=vd.sp+vd.val
    w=vd.pivot(index='VD_Number',columns='BallotType',values='cast').max(axis=1)
    reg=vd.groupby('VD_Number').reg.first()
    pr=d[d.BallotType=='PR']
    da=pr[pr.sPartyName.str.upper().str.contains('DEMOCRATIC ALLIANCE')].groupby('VD_Number').Party_Votes.sum()
    val=vd[vd.BallotType=='PR'].set_index('VD_Number').val
    return pd.DataFrame({'reg':reg,'cast':w,'val':val,'da':da}).fillna({'da':0})
def npe(y):
    d=pd.read_csv(R+f'npe{y}_JHB_vd_party.csv')
    vd=d.groupby('VD_Number').agg(reg=('Registered_Population','first'),sp=('Spoilt_Votes','first'),val=('Total_Valid_Votes','first'))
    vd['cast']=vd.sp+vd.val
    vd['da']=d[d.sPartyName.str.upper().str.contains('DEMOCRATIC ALLIANCE')].groupby('VD_Number').Party_Votes.sum()
    return vd.fillna({'da':0})
# (a) 2021 projection vs realised
t=pd.read_csv('data/processed/joburg/2021/turnout.csv').set_index('VD_Number')
a=lge(2021)
j=a.join(t[['turnout_2021_projected']],how='left')
own=j.turnout_2021_projected.notna()
print('2021 realised citywide turnout (cast/reg): %.2f'%(100*a.cast.sum()/a.reg.sum()))
print('2021 projected, roll(2021)-weighted over VDs with own projection: %.2f  (roll share %.3f)'%(100*(j.reg[own]*j.turnout_2021_projected[own]).sum()/j.reg[own].sum(), j.reg[own].sum()/j.reg.sum()))
print('2016 realised: %.2f'%(100*lge(2016).cast.sum()/lge(2016).reg.sum()))
# (b) NPE2019 -> LGE2021 composition, DA
n=npe(2019); m=n.join(a,lsuffix='_n',rsuffix='_l',how='inner')
s_n=m.da_n/m.val_n
base=(m.da_n.sum()/m.val_n.sum())
tot=(s_n*m.val_l).sum()/m.val_l.sum()
# turnout part: weights reg_l*turnout_n vs reg_l*turnout_l (valid/reg)
tn=m.val_n/m.reg_n; tl=m.val_l/m.reg_l
w0=m.reg_l*tn; w1=m.reg_l*tl
print('joined share of 2021 PR valid votes %.3f'%(m.val_l.sum()/a.val.sum()))
print('DA NPE2019 share (joined) %.2f; reweighted by 2021 valid votes %.2f; between-VD total %+.2f'%(100*base,100*tot,100*(tot-base)))
print('between-VD from turnout only %+.2f'%(100*((s_n*w1).sum()/w1.sum()-(s_n*w0).sum()/w0.sum())))
print('actual DA LGE2021 share (joined) %.2f'%(100*m.da_l.sum()/m.val_l.sum()))
