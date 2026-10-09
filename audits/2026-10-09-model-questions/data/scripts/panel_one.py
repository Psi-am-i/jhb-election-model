import os, sys, json
os.chdir('/Users/simondavis/projects/atlas-jhb-election-model'); sys.path.insert(0,'src'); sys.path.insert(0,'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq')
from pathlib import Path
from unittest import mock
import levels, votecov, compare_history as CH
slug, year, arm = sys.argv[1], sys.argv[2], sys.argv[3]
draws = 1000
patches = []
if arm == 'vote':
    patches = [mock.patch.object(levels, 'contestation', votecov.make(year))]
elif arm == 'none':
    _o = levels.contestation
    def same(target, city):
        # now/was = 1: return the PREVIOUS LGE's slates for the target as well
        import cityconfig
        if target.year == year:
            prev = cityconfig.Target(city=city, year=year).previous_lge
            return _o(cityconfig.Target(city=city, year=prev), city)
        return _o(target, city)
    patches = [mock.patch.object(levels, 'contestation', same)]
for p in patches: p.start()
r = CH.run_city_year(slug, year, draws, Path('data/raw/elections'))
keep = {k: r[k] for k in ('pr_mae', 'ward_mae', 'seat_abs_err_coherent') if k in r}
for k in r:
    if 'ward' in k and isinstance(r[k], (int, float)): keep[k] = r[k]
json.dump(keep, open(f'/Users/simondavis/.claude/jobs/26965cd4/tmp/modelq/panel/{slug}-{year}-{arm}.json', 'w'), default=str)
print(slug, year, arm, keep)
