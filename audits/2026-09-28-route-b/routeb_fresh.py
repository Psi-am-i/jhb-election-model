import os, sys, json, time
sys.path.insert(0, 'src')
MODE = os.environ['MODE']
t0 = time.perf_counter()
import cityconfig, levels
cityconfig.use("joburg"); target = cityconfig.use_target("2026")
import montecarlo as mc
if MODE == 'table':
    table = json.load(open(os.environ['S']+'/reduced_table.json'))
    def lookup(path):
        e = table[os.path.relpath(os.path.abspath(str(path)))]
        return dict(e["shares"]), set(e["roster"])
    levels._citywide_and_roster = lookup
class _Args:
    def __init__(self, draws): self.config=None; self.set=None; self.draws=draws; self.seed=None
t = time.perf_counter(); mc.run_model(target, mc.load_scenario(_Args(20)), verbose=False); t20 = time.perf_counter()-t
t = time.perf_counter(); mc.run_model(target, mc.load_scenario(_Args(20)), verbose=False); t20b = time.perf_counter()-t
print(f"{MODE}: import {t-t0-t20:.1f}s  first 20-draw run {t20:.1f}s  second {t20b:.1f}s")
