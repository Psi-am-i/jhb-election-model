import sys, os, pickle, copy, time, json, csv, collections
sys.path.insert(0, 'src')
import cityconfig, montecarlo as mc
draws = int(sys.argv[1]); out = sys.argv[2]
city = cityconfig.use('joburg'); target = cityconfig.use_target(2026); mc.apply_city(city)
iec = {}
for r in csv.DictReader(open('archive/iec-registration-2026-09-26/joburg_ward_registration_2026-09-26.csv')):
    iec[r['Ward'][-3:].lstrip('0')] = int(r['Registered'])
orig = mc.ward_parts
def patched(*a, **k):
    parts, src = orig(*a, **k)
    tot = collections.Counter()
    for vd, w, r in parts: tot[str(w)[-3:].lstrip('0')] += r
    out_ = [(vd, w, int(round(r * iec[str(w)[-3:].lstrip('0')] / tot[str(w)[-3:].lstrip('0')]))) for vd, w, r in parts]
    print('patched roll', sum(r for *_, r in parts), '->', sum(r for *_, r in out_), 'example ward key', parts[0][1])
    return out_, src + ' [IEC 2026 ward totals]'
mc.ward_parts = patched
sc = copy.deepcopy(mc.DEFAULTS); sc['draws'] = draws; sc['seed'] = 20261104
run = mc.run_model(target, sc, verbose=False)
keep = {k: getattr(run, k) for k in ['universe','wards','seat_draws','pr_share_draws','ward_share_draws','guards','ward_win_sum','overhang_count']}
pickle.dump(keep, open(out + '/run.pkl', 'wb'))
