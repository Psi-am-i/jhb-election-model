"""Duncan-Davis bounds for the 2024 national result in each metro, on 2021 wards
(VD -> ward from the 2021 LGE file) with the 2021 voter composition carried
forward (ARGUED: 2024 voter composition is not observed). Appends rows with
year '2024n' to the panel file."""
import sys, os, json, io, contextlib, csv
from collections import defaultdict
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import numpy as np, cityconfig, pools, parties as P
cfg = pools.load_config(); rows = []
for slug in ['joburg','tshwane','ekurhuleni','ethekwini','capetown','nelsonmandelabay','buffalocity','mangaung']:
    city = cityconfig.load(slug); cityconfig.use(slug)
    with contextlib.redirect_stdout(io.StringIO()):
        fits, ctx = pools.fit_city(city, '2021', cfg)
    cats = list(ctx['categories']); comp = dict(zip(ctx['wards'], ctx['comp']))
    vdw = {}
    for r in csv.DictReader(open(f'data/raw/elections/lge2021_{city.code}_vd_party_clean.csv', encoding='utf-8', errors='replace')):
        vdw[r['VD_Number']] = r['Ward']
    tally = defaultdict(lambda: defaultdict(float))
    for r in csv.DictReader(open(f'data/raw/elections/npe2024_{city.code}_vd_party.csv', encoding='utf-8', errors='replace')):
        w = vdw.get(r['VD_Number'])
        if w in comp: tally[w][P.canonical(r['sPartyName'])] += float(r['Party_Votes'] or 0)
    W = sorted(tally); C = np.array([comp[w] for w in W]); V = np.array([sum(tally[w].values()) for w in W])
    poolv = (C * V[:, None]).sum(0)
    for p in {q for w in W for q in tally[w]}:
        pv = np.array([tally[w].get(p, 0.0) for w in W])
        if pv.sum() <= 0: continue
        for gi, g in enumerate(cats):
            c = C[:, gi]
            rows.append(dict(city=slug, year='2024n', party=p, pool=g, rate=None,
                             dd_lo=float(np.maximum(0, pv - (1 - c) * V).sum() / poolv[gi]),
                             dd_hi=float(np.minimum(pv, c * V).sum() / poolv[gi]),
                             city_share=float(pv.sum() / V.sum()), pool_vote_share=float(poolv[gi] / V.sum())))
    print(slug, 'ok', flush=True)
json.dump(rows, open(sys.argv[1], 'w'))
for r in rows:
    if r['party'] in ('PA', 'MK') and r['city'] == 'joburg': print(r)
