import sys, json, pickle, numpy as np
sys.path.insert(0,'src')
S='/Users/simondavis/.claude/jobs/26965cd4/tmp/integrity/'+sys.argv[1]
r=pickle.load(open(S+'/run.pkl','rb')); T=S+'/trace/'
u=r['universe']; P=r['pr_share_draws']; W=r['ward_share_draws']
th=json.load(open(T+'10_theta_prior.json')); ce=json.load(open(T+'30_centres.json')); sp=json.load(open(T+'20_spine.json'))
spec=json.load(open('data/processed/joburg/pools_2026.json')) if False else None
import glob
cands=glob.glob('data/processed/**/pools_2026.json',recursive=True); print(cands)
spec=json.load(open('data/processed/pools_2026.json'))
print('spec keys', list(spec.keys()))
pools=spec['pools']; seeds=spec.get('seeds') or {}; bands=spec.get('seed_bands') or {}
members={p for c in pools.values() for p in c['members']}
print('npools',len(pools), {k:(len(v['members']), v.get('alpha'), v.get('tie')) for k,v in pools.items()})
print('universe',len(u),'ENTRANT' in u, 'seeded>0',sum(1 for s in seeds.values() if s>0), 'bands',len(bands))
sdm=th['sd']
seats=np.array([[s.get(p,0) for p in u] for s in r['seat_draws']])
rows=[]
for i,p in enumerate(u):
    seeded = seeds.get(p,0)>0
    lvl_sd = 0.0 if (seeded and p in members) else sdm.get(p, 0.45)
    x=P[:,i]; lx=np.log(np.maximum(x,1e-9))
    rows.append((p, p in members, seeded, p in bands, round(lvl_sd,3), ce['after_shrink'].get(p), x.mean(), np.median(x), np.std(lx), seats[:,i].mean(), np.percentile(seats[:,i],50), np.percentile(seats[:,i],99), (W[:,i].mean()-x.mean())*100))
rows.sort(key=lambda r:-(r[6]))
print(f"{'party':42} pool seed band lvl_sd centre mean median sdlog seat_mean p50 p99 ward-list_pp")
for r_ in rows: print(f"{r_[0][:42]:42} {int(r_[1])} {int(r_[2])} {int(r_[3])} {r_[4]:5} {r_[5] if r_[5] is None else round(r_[5]*100,3):>7} {r_[6]*100:7.3f} {r_[7]*100:7.3f} {r_[8]:5.2f} {r_[9]:6.2f} {r_[10]:4.0f} {r_[11]:4.0f} {r_[12]:6.2f}")
print('zero level sd parties:', sum(1 for r_ in rows if r_[4]==0), 'of', len(rows))
print('not in any pool:', [r_[0] for r_ in rows if not r_[1]])
