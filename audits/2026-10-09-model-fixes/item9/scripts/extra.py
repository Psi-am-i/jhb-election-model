"""Extra record-vs-draw checks: top entrant's share of the entrant group;
city-year common component of entrant log share; seat-threshold test."""
import os, sys, json, pickle
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, pools
D = '/Users/simondavis/.claude/jobs/26965cd4/tmp/item9/'
S = json.load(open(D + 'shares.json')); spec = json.load(open('data/processed/pools_2026.json'))
SPL = set(pools.SPLITS)
top, cy, nent = [], [], []
for c in ('JHB', 'TSH', 'EKU', 'ETH', 'CPT', 'MAN', 'NMA', 'BUF'):
    for a, b in (('2006', '2011'), ('2011', '2016'), ('2016', '2021')):
        A = S[f'lge{a}_{c}']['shares']; Bs = S[f'lge{b}_{c}']['shares']
        e = np.array([v for p, v in Bs.items() if p not in A and p not in SPL and v > 0])
        if len(e) == 0: continue
        nent.append(len(e)); top.append(e.max() / e.sum()); cy.append(np.log(e))
top = np.array(top)
print('RECORD entrants per city-year: n city-years', len(top), 'count q5/50/95', np.percentile(nent, [5, 50, 95]), 'max', max(nent))
print('RECORD top entrant / entrant total: median %.3f q5 %.3f q95 %.3f' % tuple(np.percentile(top, [50, 5, 95])))
# one-way variance decomposition of log entrant share (no reach adjustment)
allv = np.concatenate(cy); gm = allv.mean()
between = sum(len(x) * (x.mean() - gm) ** 2 for x in cy); within = sum(((x - x.mean()) ** 2).sum() for x in cy)
k = len(cy); n = len(allv); msb = between / (k - 1); msw = within / (n - k); n0 = (n - sum(len(x) ** 2 for x in cy) / n) / (k - 1)
icc = (msb - msw) / (msb + (n0 - 1) * msw)
print('RECORD log entrant share: total sd %.2f, within-city-year sd %.2f, ICC %.2f (n %d in %d city-years)' % (allv.std(), np.sqrt(msw), icc, n, k))
# correlation of count with mean share
print('RECORD corr(n entrants, mean log share) %.2f; corr(n, log total) %.2f' % (
    np.corrcoef(nent, [x.mean() for x in cy])[0, 1], np.corrcoef(nent, [np.log(np.exp(x).sum()) for x in cy])[0, 1]))
B = pickle.load(open(D + 'base.pkl', 'rb')); U = B['universe']
v = np.asarray(B['pr_vote_draws'], float); L = v / v.sum(1, keepdims=True)
seats = np.array([[s.get(p, 0) for p in U] for s in B['seat_draws']])
ent = [p for p in spec['seeds'] if p != 'SOUTH_AFRICAN_COMMUNIST_PARTY']
gi = [U.index(p) for p in ent]
G = L[:, gi]; t = G.max(1) / G.sum(1)
print('DRAWS top of 45 / group: median %.3f q5 %.3f q95 %.3f' % tuple(np.percentile(t, [50, 5, 95])))
gi2 = [U.index(p) for p in ent if p != 'ALL_CITIZENS_PARTY']; G2 = L[:, gi2]; t2 = G2.max(1) / G2.sum(1)
print('DRAWS top of 44 (excl ACP) / group: median %.3f q5 %.3f q95 %.3f' % tuple(np.percentile(t2, [50, 5, 95])))
# seat threshold: smallest list share holding >=1 seat, any party, any draw; and largest with 0
has = seats >= 1
thr_lo = L[has].min(); thr_hi = L[~has & (L > 0)].max()
# per draw threshold estimate among small parties: the share at which P(seat) crosses 0.5
bins = np.linspace(0.001, 0.006, 26); x = L.ravel(); y = has.ravel()
cross = None
for lo, hi in zip(bins[:-1], bins[1:]):
    s = (x >= lo) & (x < hi)
    if s.sum() > 50 and y[s].mean() >= 0.5 and cross is None: cross = (lo + hi) / 2
print('DRAWS seat threshold: min share with a seat %.4f%%, max share with none %.4f%%, P(seat)>=0.5 from %.3f%%' % (100 * thr_lo, 100 * thr_hi, 100 * cross))
er = np.array(spec['entrant_record'], float)
for r in (1.0, 0.5, 0.15):
    c = er[np.abs(er[:, 1] - r) < 0.25, 0]; c = c if len(c) >= 8 else er[:, 0]
    print(f'RECORD comparators reach~{r}: n {len(c)}, P(share >= {100*cross:.3f}%) = {(c >= cross).mean():.3f}; same x0.22 group rescale: {(c*0.2203 >= cross).mean():.3f}')
for p in ent[:0]: pass
P1 = (seats[:, gi] >= 1).mean(0)
print('DRAWS P(>=1 seat) over 45: min %.3f median %.3f max %.3f; excluding ACP max %.3f' % (P1.min(), np.median(P1), P1.max(), np.sort(P1)[-2]))
print('DRAWS expected seats per 45-party: sum of mean seats %.2f' % seats[:, gi].mean(0).sum())
