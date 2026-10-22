import pickle, json, numpy as np
B='/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/'
C=pickle.load(open(B+'split_capture.pkl','rb')); cana=json.load(open(B+'canary_joburg_2026.json'))
U=C['universe']; S=C['seats']; L=C['list_share']
info={x['party']:x for x in cana['rows']}
seeded=[i for i,p in enumerate(U) if info[p]['seeded']]; non=[i for i,p in enumerate(U) if not info[p]['seeded']]
print('seeded n',len(seeded),'non-seeded n',len(non))
def row(i):
    s=S[:,i]; return (U[i], info[U[i]]['centre']*100, np.median(s), s.mean(), (s>=1).mean(), (s>=5).mean(), np.percentile(s,99), s.max(), np.percentile(L[:,i],50)*100, np.percentile(L[:,i],99)*100)
print('party | centre% | median seats | mean | P>=1 | P>=5 | p99 | max | list share median / p99 %')
for i in sorted(seeded,key=lambda i:-info[U[i]]['centre'])[:12]: print('%-32s %6.3f %4.0f %6.2f %5.2f %5.3f %5.1f %4d %6.3f %6.2f'%row(i))
tot=S[:,seeded].sum(1); print('\n46 seeded combined seats: median %.0f mean %.1f p5 %.0f p95 %.0f p99 %.0f; combined centre %.2f%% of list vote; combined list share median %.2f p95 %.2f'%(np.median(tot),tot.mean(),*np.percentile(tot,[5,95,99]),sum(info[U[i]]['centre'] for i in seeded)*100,np.median(L[:,seeded].sum(1))*100,np.percentile(L[:,seeded].sum(1),95)*100))
small_non=[i for i in non if info[U[i]]['centre']<0.02]
print('non-seeded parties with centre<2%%: n %d'%len(small_non))
for i in sorted(small_non,key=lambda i:-info[U[i]]['centre'])[:8]: print('%-32s %6.3f %4.0f %6.2f %5.2f %5.3f %5.1f %4d %6.3f %6.2f'%row(i))
# matched comparison: parties of similar centre, seeded vs not: dispersion of log list share
def cv(i): x=L[:,i]; return x.std()/x.mean()
for lo,hi in [(0.0003,0.0007),(0.0007,0.0015),(0.009,0.02)]:
    a=[cv(i) for i in seeded if lo<=info[U[i]]['centre']<hi]; b=[cv(i) for i in non if lo<=info[U[i]]['centre']<hi]
    print(f'centre {lo*100:.2f}-{hi*100:.2f}%: CV of list share, seeded median {np.median(a) if a else float("nan"):.2f} (n{len(a)}), non-seeded median {np.median(b) if b else float("nan"):.2f} (n{len(b)})')
# width: how much of the big parties' seat variance co-moves with the seeded tail
for p in ['DA','ANC','ASA','EFF','MK','PA']:
    i=U.index(p); r=np.corrcoef(S[:,i],tot)[0,1]; print(f'{p}: sd seats {S[:,i].std():.2f}; corr with seeded-46 combined seats {r:+.3f}; R2 {r*r:.3f}')
