import os, sys, json, collections
sys.path.insert(0, 'src')
ROOT = os.path.abspath('.'); SRC = ROOT + '/src/'
seen = collections.OrderedDict(); writes = set(); busy = [False]
def hook(ev, args):
    if ev != 'open' or busy[0]: return
    busy[0] = True
    try:
        f, mode = args[0], args[1]
        if not isinstance(f, (str, bytes, os.PathLike)): return
        p = os.path.abspath(os.fsdecode(f))
        if not p.startswith(ROOT + '/data'): return
        rel = os.path.relpath(p, ROOT)
        if mode and any(c in mode for c in 'wax+'): writes.add(rel); return
        if rel in seen: return
        fr = sys._getframe(1); chain = []
        while fr:
            if fr.f_code.co_filename.startswith(SRC):
                chain.append(f"{os.path.basename(fr.f_code.co_filename)}:{fr.f_code.co_name}")
            fr = fr.f_back
        seen[rel] = [os.path.getsize(p) if os.path.exists(p) else -1, chain[:4]]
    finally: busy[0] = False
sys.addaudithook(hook)
import cityconfig
cityconfig.use("joburg"); target = cityconfig.use_target("2026")
import montecarlo as mc
class _Args:
    def __init__(self, draws): self.config=None; self.set=None; self.draws=draws; self.seed=None
run = mc.run_model(target, mc.load_scenario(_Args(draws=20)), verbose=False)
tot = sum(v[0] for v in seen.values() if v[0] > 0)
print(f"files {len(seen)} total {tot/1e6:.1f} MB; writes {sorted(writes)}")
by = collections.defaultdict(lambda: [0,0])
for rel,(s,ch) in seen.items(): k = ch[0] if ch else '?'; by[k][0]+=1; by[k][1]+=max(s,0)
for k,(n,s) in sorted(by.items(), key=lambda x:-x[1][1]): print(f"{s/1e6:8.2f} MB {n:3d}  {k}")
json.dump(seen, open(os.environ['OUT'],'w'), indent=1)
