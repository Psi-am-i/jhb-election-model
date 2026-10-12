"""Floor side: share of live 2026 draws in which the DA (and ANC) take less of
the Coloured vote than they PROVABLY took in Johannesburg (DD lower bound) in
2021 and 2024."""
import sys, json
sys.path.insert(0, '/Users/simondavis/projects/atlas-jhb-election-model/audits/2026-10-09-model-fixes/item7/scripts')
from capture import *
run, cap = run_capture(draws=400)
out = {}
for p, lo21, lo24 in [('DA', 0.030, 0.068), ('ANC', 0.002, 0.002)]:
    x = cap['shares']['Coloured'][p]
    out[p] = dict(below_2021_dd_lo=float((x < lo21).mean()), below_2024_dd_lo=float((x < lo24).mean()), median=float(np.median(x)))
print(json.dumps(out))
