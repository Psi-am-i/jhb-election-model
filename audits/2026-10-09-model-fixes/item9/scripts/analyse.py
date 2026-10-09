"""Item 9 analysis. TEST, declared before the draw-side statistics were computed:
  population: the 45 group-budget entrants (SACP, declared, reported apart).
  benchmark:  each party's reach-matched comparator set from the spec's own
              entrant_record, built as arrival_rules builds it (|r - reach|<0.25,
              all rows if fewer than 8).
  quantity:   90% log width W = ln(q95/q5) of the citywide list share, and its
              halves U = ln(q95/q50), L = ln(q50/q5).
  verdict:    draws' W inside the bootstrap 90% CI of the comparators' W
              (2000 resamples) = matches; below = too narrow; above = too wide.
  secondary:  coverage = share of comparator results inside the party's drawn
              5-95% interval (90% expected if location and width both match);
              group total of the 45 against the record's entrant totals."""
import os, sys, json, pickle, re
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model')
import numpy as np
D = '/Users/simondavis/.claude/jobs/26965cd4/tmp/item9/'
spec = json.load(open('data/processed/pools_2026.json'))
er = np.array(spec['entrant_record'], float)
S = json.load(open(D + 'shares.json'))
rec = json.load(open(D + 'record.json'))
B = pickle.load(open(D + 'base.pkl', 'rb')); N = pickle.load(open(D + 'nosplit.pkl', 'rb'))
U = B['universe']; assert U == N['universe']
seeds = spec['seeds']; notes = spec['seed_notes']
def shares(R):
    v = np.asarray(R['pr_vote_draws'], float); return v / v.sum(1, keepdims=True)
Lb, Ln = shares(B), shares(N)
Tb, Tn = B['targets'], N['targets']
seatsB = np.array([[s.get(p, 0) for p in U] for s in B['seat_draws']])
cent = B['centres']; csum = sum(cent.values())
def reach_of(p):
    m = re.search(r'\((\d+)% of wards\)', notes[p]); return int(m.group(1)) / 100 if m else None
rng = np.random.default_rng(0)
def comps(r):
    near = er[np.abs(er[:, 1] - r) < 0.25, 0]; return near if len(near) >= 8 else er[:, 0]
def W(x):
    x = np.asarray(x, float); q5, q50, q95 = np.percentile(x, [5, 50, 95])
    f = lambda a, b: float(np.log(a / b)) if a > 0 and b > 0 else float('inf')
    return f(q95, q5), f(q95, q50), f(q50, q5)
def boot_W(x, n=2000):
    ws = [W(rng.choice(x, len(x)))[0] for _ in range(n)]; return np.percentile(ws, [5, 95])
rows = []
ent = [p for p in seeds if p != 'SOUTH_AFRICAN_COMMUNIST_PARTY']
for p in sorted(seeds, key=lambda p: -cent[p]):
    i = U.index(p); x = Lb[:, i]; s = seatsB[:, i]; r = reach_of(p)
    c = comps(r) if r is not None else None
    wb = W(x); wn = W(Ln[:, i]); wt = W(Tb[:, i])
    row = dict(party=p, reach=r, seed_pct=100*seeds[p], centre_pct=100*cent[p], centre_norm_pct=100*cent[p]/csum,
               drawn_mean_pct=100*x.mean(), drawn_q5_50_95_pct=[100*v for v in np.percentile(x, [5, 50, 95])],
               p_below_0_01pct=float((x < 1e-4).mean()), p_below_0_001pct=float((x < 1e-5).mean()),
               seats_median=float(np.median(s)), seats_q5_95=[float(v) for v in np.percentile(s, [5, 95])],
               p_seat_ge1=float((s >= 1).mean()), seats_mean=float(s.mean()),
               W_base=wb, W_nosplit=wn, W_target_base=wt,
               sdlog_base=float(np.std(np.log(np.maximum(x, 1e-12)))),
               why=notes[p].split('.')[0])
    if c is not None and p in ent:
        wc = W(c); ci = boot_W(c)
        q5, q95 = np.percentile(x, [5, 95])
        row.update(n_comp=int(len(c)), comp_q5_50_95_pct=[100*v for v in np.percentile(c, [5, 50, 95])],
                   comp_mean_pct=100*float(c.mean()), W_comp=wc, W_comp_ci90=[float(v) for v in ci],
                   comp_p_below_0_01pct=float((c < 1e-4).mean()),
                   coverage=float(((c >= q5) & (c <= q95)).mean()),
                   verdict=('matches' if ci[0] <= wb[0] <= ci[1] else ('too narrow' if wb[0] < ci[0] else 'too wide')))
    rows.append(row)
# group of 45
gi = [U.index(p) for p in ent]
G = Lb[:, gi].sum(1); Gn = Ln[:, gi].sum(1)
lt = np.array([t[2] for t in rec['panel_2011_2021']['entrant_totals_pct'] if t[2] > 0]) / 100
grp = dict(drawn_q5_50_95_pct=[100*v for v in np.percentile(G, [5, 50, 95])], drawn_mean_pct=100*G.mean(),
           W_drawn=W(G), W_nosplit=W(Gn), sdlog_drawn=float(np.std(np.log(G))),
           record_panel_totals_q5_50_95_pct=[100*v for v in np.percentile(lt, [5, 50, 95])], W_record_panel=W(lt),
           record_panel_n=int(len(lt)), record_sdlog_panel=float(np.std(np.log(lt))),
           spec_group_total_log_sd=spec['arrival_group']['total_log_sd'], spec_group_n=spec['arrival_group']['n_observations'],
           seats_q5_50_95=[float(v) for v in np.percentile(seatsB[:, gi].sum(1), [5, 50, 95])],
           seats_mean=float(seatsB[:, gi].sum(1).mean()))
for_icc = None
json.dump(dict(rows=rows, group=grp), open(D + 'analysis.json', 'w'), indent=1, default=float)
print('%-34s %5s %6s %6s %6s %6s | %-20s | %4s %-8s %5s | %5s %5s %5s | %5s %5s | %-11s %5s %4s' % ('party','reach','seed','centre','c/1.17','mean','drawn q5/50/95 %','smed','s5-95','P>=1','Wb','Wns','Wtgt','Wcomp','ci','verdict','cover','P<.01'))
for r in rows:
    q = r['drawn_q5_50_95_pct']
    print('%-34s %5s %6.3f %6.3f %6.3f %6.3f | %6.4f %6.4f %6.3f | %4.0f %3.0f-%-4.0f %5.2f | %5.2f %5.2f %5.2f | %5s %-11s %-11s %5s %4.2f' % (
        r['party'][:34], r['reach'], r['seed_pct'], r['centre_pct'], r['centre_norm_pct'], r['drawn_mean_pct'], *q,
        r['seats_median'], *r['seats_q5_95'], r['p_seat_ge1'], r['W_base'][0], r['W_nosplit'][0], r['W_target_base'][0],
        ('%.2f' % r['W_comp'][0]) if 'W_comp' in r else '-', ('%.2f-%.2f' % tuple(r['W_comp_ci90'])) if 'W_comp_ci90' in r else '-',
        r.get('verdict', '-'), ('%.2f' % r['coverage']) if 'coverage' in r else '-', r['p_below_0_01pct']))
print('\nGROUP of 45:', json.dumps(grp, default=float, indent=0))
