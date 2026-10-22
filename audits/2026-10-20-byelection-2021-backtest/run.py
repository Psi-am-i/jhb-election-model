"""The by-election weight tested on 2021 with the 2016-cycle by-elections
(prereg/2026-10-20-byelection-weight-2021-backtest.md).

Builds each metro's 2021 deltas from data/raw/byelections/
byelections_SA_vd_party_2016.csv into a scratch tree, then scores the 2021
elections of the eight metros with compare_history.run_city_year at 1,000
draws, seed 20261104, with run_model pointed at the scratch processed
directory. Arms A0 (w_bye 0), A5 (0.5), A10 (1.0), F (0.5, seat-changing
contests weighted x2 by multiplying their votes by 4). Writes nothing into
data/.

    .venv/bin/python audits/2026-10-20-byelection-2021-backtest/run.py --work DIR
"""
import argparse, csv, functools, json, os, shutil, sys
from pathlib import Path
R = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(R / 'src')); os.chdir(R)
import byelections as B
import cityconfig as C
import compare_history as CH
import montecarlo as M

SLUGS = ['joburg', 'tshwane', 'ekurhuleni', 'capetown', 'ethekwini',
         'nelsonmandelabay', 'buffalocity', 'mangaung']
SRC = R / 'data/raw/byelections/byelections_SA_vd_party_2016.csv'
DATA = R / 'data/raw/elections'
ARMS = {'A0': ('base', 0.0), 'A5': ('base', 0.5), 'A10': ('base', 1.0), 'F': ('flip', 0.5)}

ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True)
a = ap.parse_args(); W = a.work.resolve()
assert not str(W).startswith(str(R / 'data')), 'work dir must lie outside data/'


def flips():
    """(date, ward) of every contest whose ward winner differs from 2016's."""
    out = {}
    for slug in SLUGS:
        city = C.use(slug); t = C.use_target('2021')
        con = B.load_byelections(SRC, city.ward_prefix, C.CALENDAR['2016'].date, t.date)
        votes, _ = B.ward_ballot(DATA / t.results('2016'))
        for (when, ward), tally in con.items():
            base = votes.get(ward)
            if base and max(base, key=base.get) != max(tally, key=tally.get):
                out[(str(when)[:10], ward)] = (slug, max(base, key=base.get), max(tally, key=tally.get))
    return out


def raw_tree(name, flipset):
    root = W / 'raw' / name; (root / 'byelections').mkdir(parents=True, exist_ok=True)
    if not (root / 'elections').exists():
        (root / 'elections').symlink_to(DATA)
    dest = root / 'byelections' / 'byelections_Gauteng_vd_party.csv'
    if not flipset:
        if not dest.exists():
            dest.symlink_to(SRC)
        return root
    with open(SRC, encoding='utf-8', newline='') as fi, open(dest, 'w', encoding='utf-8', newline='') as fo:
        rd = csv.DictReader(fi); wr = csv.DictWriter(fo, fieldnames=rd.fieldnames); wr.writeheader()
        for row in rd:
            if (row['ByElectionDate'][:10], row['WardID']) in flipset:
                row['Party_Votes'] = str(int(float(row['Party_Votes'] or 0)) * 4)
            wr.writerow(row)
    return root


def processed_dir(variant, slug, raw):
    out = W / 'processed' / variant / slug
    if (out / 'byelection_party_deltas.csv').exists():
        return out
    out.mkdir(parents=True, exist_ok=True)
    real = C.use(slug); t = C.use_target('2021')
    for f in ('turnout.csv', 'gamma_recent.csv'):
        if (t.processed / f).exists():
            shutil.copy(t.processed / f, out / f)
    B.main(['--city', slug, '--target', '2021', '--data-dir', str(raw), '--processed', str(out)])
    return out


flipset = flips()
(W / 'flips.json').parent.mkdir(parents=True, exist_ok=True)
(W / 'flips.json').write_text(json.dumps({f'{k[0]} {k[1]}': v for k, v in flipset.items()}, indent=1))
raws = {'base': raw_tree('base', None), 'flip': raw_tree('flip', flipset)}
orig = M.run_model
results = {}
for arm, (variant, w) in ARMS.items():
    for slug in SLUGS:
        pdir = processed_dir(variant, slug, raws[variant])
        M.run_model = functools.partial(orig, processed=pdir)
        try:
            row = CH.run_city_year(slug, '2021', 1000, DATA, overrides=[f'w_bye={w}'],
                                   run_dir=W / 'trace' / arm)
        finally:
            M.run_model = orig
        results.setdefault(arm, {})[slug] = {
            'pr_mae': row['pr_mae'], 'ward_mae': row['ward_mae'],
            'seat_abs_err': row['seat_abs_err'], 'wards': row['wards'],
            'votes': row['votes'], 'seats': row['seats']}
        print(arm, slug, round(row['pr_mae'], 4), row['seat_abs_err'], flush=True)
(W / 'results.json').write_text(json.dumps(results, indent=1, default=str))
