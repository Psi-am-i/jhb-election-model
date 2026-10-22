"""Citywide PR shares for every metro-year (LGE 2000-2021, NPE 2024), read with
levels._citywide_and_roster (the model's own reader, bypassing the HELD_BACK
gate on purpose: this measures the world, it feeds no model). Also roster."""
import os, sys, json
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0, 'src')
import levels
out = {}
for y in ('2000', '2006', '2011', '2016', '2021'):
    for c in ('JHB', 'TSH', 'EKU', 'ETH', 'CPT', 'MAN', 'NMA', 'BUF'):
        p = f'data/raw/elections/lge{y}_{c}_vd_party_clean.csv'
        s, roster = levels._citywide_and_roster(p)
        out[f'lge{y}_{c}'] = dict(shares=s, roster=sorted(roster))
        print(y, c, len(s), round(sum(s.values()), 4), flush=True)
for c in ('JHB', 'TSH', 'EKU', 'ETH', 'CPT', 'MAN', 'NMA', 'BUF'):
    p = f'data/raw/elections/npe2024_{c}_vd_party.csv'
    s, roster = levels._citywide_and_roster(p)
    out[f'npe2024_{c}'] = dict(shares=s, roster=sorted(roster))
    print('2024', c, len(s), round(sum(s.values()), 4), flush=True)
json.dump(out, open('/Users/simondavis/.claude/jobs/26965cd4/tmp/item9/shares.json', 'w'))
