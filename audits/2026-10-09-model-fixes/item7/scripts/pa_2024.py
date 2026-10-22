"""PA 2024 NPE by 2021 ward (VD->ward from the 2021 LGE file), against 2021
ward Coloured share of voters; and turnout in Coloured-majority wards. Read-only."""
import sys, os, json, io, contextlib, csv
from collections import defaultdict
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, pools
city = cityconfig.use('joburg'); cfg = pools.load_config()
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    fits, ctx = pools.fit_city(city, '2021', cfg)
cats = list(ctx['categories']); ci = cats.index('Coloured')
cw = dict(zip(ctx['wards'], ctx['comp'][:, ci]))
counts = ctx['counts']
regc = {w: counts.registered[counts.wards.index(w)] for w in ctx['wards']}
# VD -> ward from the 2021 file; registered and votes by ward 2021
vd_ward = {}; reg21 = {}; val21 = defaultdict(float)
for r in csv.DictReader(open('data/raw/elections/lge2021_JHB_vd_party_clean.csv', encoding='utf-8')):
    if r['BallotType'] != 'PR': continue
    vd_ward[r['VD_Number']] = r['Ward']; reg21[r['VD_Number']] = float(r['Registered_Population'])
    val21[r['VD_Number']] = float(r['Total_Valid_Votes'])
pa24 = defaultdict(float); tot24 = defaultdict(float); reg24 = {}; unm = [0, 0]
for r in csv.DictReader(open('data/raw/elections/npe2024_JHB_vd_party.csv', encoding='utf-8')):
    vd = r['VD_Number']; w = vd_ward.get(vd)
    v = float(r['Party_Votes'] or 0)
    if w is None:
        unm[0] += v; unm[1] += v if 'PATRIOTIC ALLIANCE' in r['sPartyName'] else 0; continue
    tot24[w] += v; reg24[vd] = float(r['Registered_Population'])
    if r['sPartyName'].strip() == 'PATRIOTIC ALLIANCE': pa24[w] += v
print('2024 votes in VDs not on the 2021 map:', unm[0], 'PA among them:', unm[1])
W = [w for w in ctx['wards'] if w in tot24]
c = np.array([cw[w] for w in W]); V = np.array([tot24[w] for w in W]); P = np.array([pa24[w] for w in W])
print('2024 mapped: total', V.sum(), 'PA', P.sum(), 'share', P.sum()/V.sum())
# DD bounds at city level, using the 2021 voter composition (argued: composition of 2024 voters unknown)
lo = np.maximum(0, P - (1-c)*V).sum(); hi = np.minimum(P, c*V).sum(); colv = (c*V).sum()
print(f'2024 Coloured votes (2021 comp) {colv:.0f}; PA from Coloured DD [{lo:.0f},{hi:.0f}] = share of Coloured [{lo/colv:.3f},{hi/colv:.3f}]; outside share [{1-hi/P.sum():.3f},{1-lo/P.sum():.3f}]')
res = []
for a, b in [(0,.02),(.02,.1),(.1,.3),(.3,.5),(.5,1.01)]:
    m = (c>=a)&(c<b)
    res.append(dict(bin=f'{a:.0%}-{min(b,1):.0%}', wards=int(m.sum()), votes=V[m].sum(), pa=P[m].sum(), pa_share=P[m].sum()/V[m].sum(), frac_pa=P[m].sum()/P.sum()))
    print('  ', res[-1])
# turnout by ward class, 2021 and 2024 (valid votes / registered, VD sums)
def turnout(regd, vald, wards):
    R = sum(v for vd, v in regd.items() if vd_ward.get(vd) in wards); Vv = sum(v for vd, v in vald.items() if vd_ward.get(vd) in wards)
    return Vv / R, R, Vv
val24 = defaultdict(float)
seen=set()
for r in csv.DictReader(open('data/raw/elections/npe2024_JHB_vd_party.csv', encoding='utf-8')):
    if r['VD_Number'] not in seen:
        seen.add(r['VD_Number']); val24[r['VD_Number']] = float(r['Total_Valid_Votes'])
for name, sel in [('coloured>=50%', {w for w in W if cw[w] >= .5}), ('coloured<2%', {w for w in W if cw[w] < .02}), ('all', set(W))]:
    print(name, 'turnout 2021 valid/registered', turnout(reg21, val21, sel), '2024', turnout(reg24, val24, sel))
print('pool-model Coloured turnout 2021 (voted/registered pool counts):', counts.voted[:, ci].sum()/counts.registered[:, ci].sum(),
      'Black African', counts.voted[:, 0].sum()/counts.registered[:, 0].sum(), 'White', counts.voted[:, 3].sum()/counts.registered[:, 3].sum())
# turnout among Coloured in majority wards implied, vs pool model
for w in sorted(W, key=lambda w: -cw[w])[:6]:
    i = counts.wards.index(w)
    print(w, 'col share voters', round(cw[w],3), 'pool turnouts', np.round(counts.voted[i]/np.maximum(counts.registered[i],1),3), 'ward turnout 2021', round(turnout(reg21, val21, {w})[0],3))
json.dump(dict(bins=res, dd=[lo, hi, colv]), open(sys.argv[1], 'w'), default=float, indent=1)
