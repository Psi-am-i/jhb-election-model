"""Two-group (Coloured / everyone else) Goodman regression of the PA's ward
share on the ward's Coloured share of voters, 2021 LGE PR and 2024 NPE (2021
wards and 2021 voter composition). An ecological point estimate under a
constancy assumption: ARGUED, not measured."""
import sys, os, json, io, contextlib, csv
from collections import defaultdict
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, pools
city = cityconfig.use('joburg'); cfg = pools.load_config()
with contextlib.redirect_stdout(io.StringIO()):
    fits, ctx = pools.fit_city(city, '2021', cfg)
ci = list(ctx['categories']).index('Coloured'); cw = dict(zip(ctx['wards'], ctx['comp'][:, ci]))
vd_ward = {r['VD_Number']: r['Ward'] for r in csv.DictReader(open('data/raw/elections/lge2021_JHB_vd_party_clean.csv', encoding='utf-8'))}
out = {}
for yr, f, bt in [('2021', 'data/raw/elections/lge2021_JHB_vd_party_clean.csv', 'PR'), ('2024', 'data/raw/elections/npe2024_JHB_vd_party.csv', None)]:
    pa = defaultdict(float); tot = defaultdict(float)
    for r in csv.DictReader(open(f, encoding='utf-8')):
        if bt and r['BallotType'] != bt: continue
        w = vd_ward.get(r['VD_Number']);
        if w not in cw: continue
        v = float(r['Party_Votes'] or 0); tot[w] += v
        if r['sPartyName'].strip() == 'PATRIOTIC ALLIANCE': pa[w] += v
    W = sorted(tot); c = np.array([cw[w] for w in W]); V = np.array([tot[w] for w in W]); y = np.array([pa[w] / tot[w] for w in W])
    X = np.column_stack([c, 1 - c]); sw = np.sqrt(V)
    b, *_ = np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)
    b = np.clip(b, 0, 1)
    colv = (c * V).sum(); nonv = ((1 - c) * V).sum(); P = (y * V).sum()
    est_out = b[1] * nonv / (b[0] * colv + b[1] * nonv)
    # Restricted to wards under 10% Coloured, where the Coloured term is smallest
    m = c < .1
    b2, *_ = np.linalg.lstsq((X * sw[:, None])[m], (y * sw)[m], rcond=None)
    out[yr] = dict(rate_coloured=float(b[0]), rate_other=float(b[1]), outside_share=float(est_out),
                   low_wards_rate_coloured=float(b2[0]), low_wards_rate_other=float(b2[1]),
                   low_wards_outside_votes=float(max(b2[1], 0) * ((1 - c[m]) * V[m]).sum()), pa_votes=float(P))
    print(yr, json.dumps(out[yr]))
json.dump(out, open(sys.argv[1], 'w'), indent=1)
