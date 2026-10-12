import sys, pickle, numpy as np
S='/Users/simondavis/.claude/jobs/26965cd4/tmp/integrity/'
a=pickle.load(open(S+sys.argv[1]+'/run.pkl','rb')); b=pickle.load(open(S+sys.argv[2]+'/run.pkl','rb'))
u=a['universe']; assert u==b['universe'], (len(u), len(b['universe']))
n=len(a['seat_draws'])
def sm(r,p): return np.array([s.get(p,0) for s in r['seat_draws']])
print(f"{'party':32} seats_mean A   B   d | p5-p95 A | p5-p95 B | wardwins/draw A  B | list% A  B | ward% A B")
for p in sorted(u, key=lambda p:-sm(a,p).mean())[:14]:
    i=u.index(p); x,y=sm(a,p),sm(b,p)
    print(f"{p[:32]:32} {x.mean():6.2f} {y.mean():6.2f} {y.mean()-x.mean():+5.2f} | {np.percentile(x,5):.0f}-{np.percentile(x,95):.0f} | {np.percentile(y,5):.0f}-{np.percentile(y,95):.0f} | {a['ward_win_sum'].get(p,0)/n:6.2f} {b['ward_win_sum'].get(p,0)/len(b['seat_draws']):6.2f} | {100*a['pr_share_draws'][:,i].mean():5.2f} {100*b['pr_share_draws'][:,i].mean():5.2f} | {100*a['ward_share_draws'][:,i].mean():5.2f} {100*b['ward_share_draws'][:,i].mean():5.2f}")
print('overhang draws A', a['guards'].get('excessive_draws'), 'B', b['guards'].get('excessive_draws'))
