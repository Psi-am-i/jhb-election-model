import sys, json; sys.path.insert(0, '/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-09-model-fixes/item7/scripts')
from capture import *
run, cap = run_capture(draws=int(sys.argv[1]))
out = {p: pa_summary(run, cap, p, 'Coloured') for p in ['PA', 'DA', 'ANC']}
# every party x pool: share of draws whose realised rate exceeds the panel record (filled later)
print(json.dumps(out, indent=1))
print('guards', {k: v for k, v in run.guards.items() if k in ('ipf_clipped', 'cap_moved', 'cap_undershoots', 'ipf_failures')})
