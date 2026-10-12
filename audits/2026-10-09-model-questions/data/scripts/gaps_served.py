import json,sys,numpy as np
sys.path.insert(0,'src')
import reweight
m=json.load(open('site/draws/manifest.json'))
blob=open('site/draws/base.bin','rb').read()
b=reweight.unpack(blob,m)
cols=[x for x in m['blocks'] if x['name']=='list_vote'][0]['columns']
L=b['list_vote'].astype(float); W=b['ward_vote'].astype(float)
Ls=L/L.sum(1,keepdims=True); Ws=W/W.sum(1,keepdims=True)
gap=(Ls-Ws)*100
order=np.argsort(-Ls.mean(0))
print("party list% ward% gap mean min max (list-ward, pts)")
for i in order[:25]:
    print(f"{cols[i]:<40s} {Ls[:,i].mean()*100:6.2f} {Ws[:,i].mean()*100:6.2f} {gap[:,i].mean():+6.2f} {gap[:,i].min():+6.2f} {gap[:,i].max():+6.2f}")
print("most negative mean gaps:")
for i in np.argsort(gap.mean(0))[:8]: print(cols[i], round(gap[:,i].mean(),2), round(gap[:,i].min(),2))
np.save('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/served_gap.npy',gap)
json.dump(cols,open('/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/served_cols.json','w'))
