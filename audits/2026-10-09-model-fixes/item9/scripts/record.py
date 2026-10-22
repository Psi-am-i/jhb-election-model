"""The record: citywide PR share moves between consecutive LGEs, 8 metros.
Continuing parties: log ratio and abs change (pp), binned by starting share.
Arrivals (absent from the earlier PR ballot): entry share, by reach (spec's
entrant_record), and per-city-year arrival totals. Departures: last share."""
import os, sys, json
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np
import pools
D = '/Users/simondavis/.claude/jobs/26965cd4/tmp/item9/'
S = json.load(open(D + 'shares.json'))
SPL = set(pools.SPLITS)
codes = ('JHB', 'TSH', 'EKU', 'ETH', 'CPT', 'MAN', 'NMA', 'BUF')
trans = [('2006', '2011'), ('2011', '2016'), ('2016', '2021')]   # panel targets 2011/16/21
trans0 = [('2000', '2006')]
BINS = [(0, 0.0005), (0.0005, 0.001), (0.001, 0.0025), (0.0025, 0.01), (0.01, 0.05), (0.05, 1.01)]
def lab(b): return f"{b[0]*100:g}-{b[1]*100:g}%"
def q(x, ps=(5, 25, 50, 75, 95)):
    x = np.asarray(x, float); return [float(np.percentile(x, p)) for p in ps] if len(x) else [None]*len(ps)
def collect(tr):
    cont, arr, dep, totals = [], [], [], []
    for c in codes:
        for a_y, b_y in tr:
            A = S[f'lge{a_y}_{c}']['shares']; B = S[f'lge{b_y}_{c}']['shares']
            tot_ent = 0.0
            for p in set(A) | set(B):
                a, b = A.get(p, 0.0), B.get(p, 0.0)
                if a > 0 and b > 0: cont.append(dict(p=p, c=c, y=b_y, a=a, b=b))
                elif b > 0: arr.append(dict(p=p, c=c, y=b_y, b=b, split=p in SPL)); tot_ent += 0 if p in SPL else b
                elif a > 0: dep.append(dict(p=p, c=c, y=b_y, a=a))
            totals.append(dict(c=c, y=b_y, entrants_total=tot_ent))
    return cont, arr, dep, totals
out = {}
for name, tr in (('panel_2011_2021', trans), ('pre_2000_2006', trans0)):
    cont, arr, dep, totals = collect(tr)
    rows = []
    for bn in BINS:
        sel = [r for r in cont if bn[0] <= r['a'] < bn[1]]
        lr = [np.log(r['b'] / r['a']) for r in sel]; ab = [100 * (r['b'] - r['a']) for r in sel]
        d = [r for r in dep if bn[0] <= r['a'] < bn[1]]
        rows.append(dict(bin=lab(bn), n=len(sel), n_departed=len(d),
                         depart_rate=len(d) / max(len(sel) + len(d), 1),
                         logratio_q5_25_50_75_95=q(lr), logratio_sd=float(np.std(lr)) if lr else None,
                         logratio_width_5_95=(q(lr)[4] - q(lr)[0]) if lr else None,
                         abschange_pp_q5_25_50_75_95=q(ab),
                         abs_abschange_pp_median=float(np.median(np.abs(ab))) if ab else None,
                         examples=sorted([(r['p'], r['c'], r['y'], round(100*r['a'], 3), round(100*r['b'], 3)) for r in sel], key=lambda t: t[4]/t[3])[:2] + sorted([(r['p'], r['c'], r['y'], round(100*r['a'], 3), round(100*r['b'], 3)) for r in sel], key=lambda t: t[4]/t[3])[-2:]))
    ent = [r['b'] for r in arr if not r['split']]
    lt = [np.log(t['entrants_total']) for t in totals if t['entrants_total'] > 0]
    out[name] = dict(continuing=rows, n_cont=len(cont), n_arr=len(arr), n_dep=len(dep),
                     arrivals_entrants_share_pct_q5_25_50_75_95=q(np.array(ent) * 100),
                     arrivals_entrants_logshare_sd=float(np.std(np.log(ent))) if ent else None,
                     n_entrants=len(ent), splits=[(r['p'], r['c'], r['y'], round(100*r['b'], 2)) for r in arr if r['split']],
                     entrant_totals_pct=[(t['c'], t['y'], round(100*t['entrants_total'], 3)) for t in totals],
                     entrant_total_log_sd=float(np.std(lt)) if lt else None,
                     entrant_total_pct_q5_50_95=q(np.exp(lt) * 100, (5, 50, 95)) if lt else None)
# the spec's own arrival record (share, reach), all transitions before 2026
spec = json.load(open('data/processed/pools_2026.json'))
er = np.array(spec['entrant_record'], float)
rb = []
for lo, hi in ((0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 0.95), (0.95, 1.01)):
    sel = er[(er[:, 1] >= lo) & (er[:, 1] < hi), 0]
    rb.append(dict(reach=f"{lo:g}-{hi:g}", n=int(len(sel)), share_pct_q5_25_50_75_95=q(sel * 100),
                   mean_pct=float(sel.mean() * 100) if len(sel) else None,
                   logshare_sd=float(np.std(np.log(sel))) if len(sel) else None,
                   log_width_5_95=float(np.log(np.percentile(sel, 95) / np.percentile(sel, 5))) if len(sel) else None))
# comparator set exactly as arrival_rules builds it, for reach ~1.0 (|r-1|<0.25)
near = er[np.abs(er[:, 1] - 1.0) < 0.25, 0]
out['spec_entrant_record'] = dict(n=int(len(er)), by_reach=rb,
    comparators_reach_1=dict(n=int(len(near)), mean_pct=float(near.mean()*100), share_pct_q5_25_50_75_95=q(near*100),
                             logshare_sd=float(np.std(np.log(near))), log_width_5_95=float(np.log(np.percentile(near,95)/np.percentile(near,5)))),
    arrival_group=dict((k, spec['arrival_group'][k]) for k in ('total_log_mean', 'total_log_sd', 'n_observations', 'alpha', 'derived_from')))
json.dump(out, open(D + 'record.json', 'w'), indent=1, default=float)
for name in ('panel_2011_2021', 'pre_2000_2006'):
    o = out[name]; print(f"\n== {name}: continuing {o['n_cont']}, arrivals {o['n_arr']} (entrants {o['n_entrants']}), departures {o['n_dep']}")
    for r in o['continuing']:
        print(f"  {r['bin']:>10s} n {r['n']:3d} dep {r['n_departed']:3d} ({r['depart_rate']:.2f})  logratio q5/25/50/75/95 " + ' '.join('%+.2f' % v if v is not None else '  -  ' for v in r['logratio_q5_25_50_75_95']) + f"  sd {r['logratio_sd'] if r['logratio_sd'] is None else round(r['logratio_sd'],2)}  w5-95 {r['logratio_width_5_95'] if r['logratio_width_5_95'] is None else round(r['logratio_width_5_95'],2)}   abs pp q5/50/95 " + ' '.join('%+.3f' % v if v is not None else '-' for v in [r['abschange_pp_q5_25_50_75_95'][i] for i in (0, 2, 4)]))
    print('  entrant share % q5/25/50/75/95', [round(v, 3) for v in o['arrivals_entrants_share_pct_q5_25_50_75_95']], 'log sd', round(o['arrivals_entrants_logshare_sd'], 2))
    print('  entrant totals log sd', o['entrant_total_log_sd'], 'q5/50/95 %', o['entrant_total_pct_q5_50_95'])
    print('  splits', o['splits'])
print('\n== spec entrant_record', out['spec_entrant_record']['n'])
for r in out['spec_entrant_record']['by_reach']: print('  ', r)
print('  comparators reach~1:', out['spec_entrant_record']['comparators_reach_1'])
print('  group:', out['spec_entrant_record']['arrival_group'])
