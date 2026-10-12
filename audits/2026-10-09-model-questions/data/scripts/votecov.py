"""Candidate fix, as a monkeypatch of levels.contestation (repository untouched).

Coverage of a party's slate = the share of ITS OWN previous-LGE list (PR) vote that lies
in wards where it fields a ward candidate. Weights are always the forecast target's
previous LGE PR votes per VD; each VD is placed in the ward it belongs to in the year
whose slate is being measured (pools.vd_map: split VDs go to the part with most
registered voters). Falls back to the count fraction where a party has no PR vote at
the previous LGE (no weights) -- same value contestation would have returned.
"""
import csv
from collections import defaultdict
import cityconfig, levels, pools, parties as P
_orig = levels.contestation

def _ward_slates_from_result(path):
    w = defaultdict(set)
    with open(path, encoding='utf-8', errors='replace') as fh:
        for row in csv.DictReader(fh):
            if row.get('BallotType') != 'Ward': continue
            ward = (row.get('Ward') or '').strip()
            if ward: w[P.canonical(row['sPartyName'])].add(ward)
    return w

def _pr_by_vd(path):
    out = defaultdict(lambda: defaultdict(int))
    with open(path, encoding='utf-8', errors='replace') as fh:
        for row in csv.DictReader(fh):
            if row.get('BallotType') != 'PR': continue
            out[P.canonical(row['sPartyName'])][row['VD_Number']] += int(row['Party_Votes'])
    return out

def make(forecast_year):
    cache = {}
    def contestation(target, city):
        base = _orig(target, city)
        if not base: return base
        key = (city.slug, target.year)
        if key in cache: return dict(cache[key])
        ft = cityconfig.Target(city=city, year=forecast_year)
        prev = ft.previous_lge
        prev_path = levels.result_path(cityconfig.Target(city=city, year=prev), city)
        weights = _pr_by_vd(prev_path)
        if levels.has_result_file(target, city):
            slates = _ward_slates_from_result(levels.result_path(target, city))
        else:
            roster = pools.declared_roster(city, target) or {}
            slates = {p: set(map(str, ws)) for p, ws in (roster.get('wards') or {}).items()}
        ward_of, _ = pools.vd_map(city, target.year)
        out = {}
        for p, frac in base.items():
            w = weights.get(p) or {}
            pairs = [(ward_of[vd], v) for vd, v in w.items() if vd in ward_of]
            tot = sum(v for _, v in pairs)
            if tot <= 0:
                out[p] = frac; continue
            s = slates.get(p, set())
            out[p] = sum(v for ward, v in pairs if ward in s) / tot
        cache[key] = out
        return dict(out)
    return contestation
