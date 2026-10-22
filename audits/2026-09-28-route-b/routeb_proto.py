import os, sys, json, time
import numpy as np
sys.path.insert(0, 'src')
import cityconfig, levels
cityconfig.use("joburg"); target = cityconfig.use_target("2026")
import montecarlo as mc
class _Args:
    def __init__(self, draws): self.config=None; self.set=None; self.draws=draws; self.seed=None
N = int(os.environ.get('N', 60))
real = levels._citywide_and_roster
calls = {}
def recording(path):
    r = real(path); calls[os.path.relpath(os.path.abspath(str(path)))] = r; return r
levels._citywide_and_roster = recording
t = time.perf_counter(); A = mc.run_model(target, mc.load_scenario(_Args(N)), verbose=False); tA = time.perf_counter()-t
table = {k: {"shares": v[0], "roster": sorted(v[1])} for k, v in calls.items()}
blob = json.dumps(table, sort_keys=True, separators=(',',':'))
open(os.environ['S']+'/reduced_table.json','w').write(blob)
missing = []
def lookup(path):
    k = os.path.relpath(os.path.abspath(str(path)))
    if k not in table: missing.append(k); return real(path)
    e = table[k]; return dict(e["shares"]), set(e["roster"])
levels._citywide_and_roster = lookup
t = time.perf_counter(); B = mc.run_model(target, mc.load_scenario(_Args(N)), verbose=False); tB = time.perf_counter()-t
def arr(run, name): return np.asarray(getattr(run, name))
same = {n: np.array_equal(arr(A,n), arr(B,n)) for n in ('seat_draws',) }
for n in dir(A):
    if n.endswith('draws') and n not in same:
        try: same[n] = np.array_equal(arr(A,n), arr(B,n))
        except Exception as e: same[n] = f'err {e}'
print(f"calls {len(calls)}; table {len(blob)/1e3:.1f} KB; missing lookups {len(missing)}")
print(f"run with parsing {tA:.1f}s, with table {tB:.1f}s  (N={N})")
print("identical:", same)
