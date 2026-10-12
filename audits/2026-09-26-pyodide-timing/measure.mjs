import { loadPyodide } from "pyodide";
const now = () => Number(process.hrtime.bigint()) / 1e9;

const t0 = now();
const py = await loadPyodide();
await py.loadPackage(["numpy", "micropip"]);
await py.runPythonAsync(`import micropip\nawait micropip.install("openpyxl")`);
const tBoot = now() - t0;

py.FS.mkdir("/repo");
py.FS.mount(py.FS.filesystems.NODEFS,
            { root: "/Users/simondavis/projects/jhb-election-model" }, "/repo");

let out;
try {
out = await py.runPythonAsync(`
import sys, os, time, json
sys.dont_write_bytecode = True          # never write .pyc into the real repo
os.chdir("/repo")
sys.path.insert(0, "/repo/src")

_opened = {}
def _hook(event, args):
    if event == "open":
        try: _opened[str(args[0])] = 1
        except Exception: pass
sys.addaudithook(_hook)

t = time.perf_counter()
import cityconfig
import montecarlo as mc
t_import = time.perf_counter() - t

class _Args:
    def __init__(self, draws):
        self.config = None; self.set = None; self.draws = draws; self.seed = None

cityconfig.use("joburg")
target = cityconfig.use_target("2026")

res = {"import_s": t_import, "numpy": __import__("numpy").__version__, "runs": {}}
for n in (20, 60):
    t = time.perf_counter()
    run = mc.run_model(target, mc.load_scenario(_Args(draws=n)), verbose=False)
    res["runs"][str(n)] = time.perf_counter() - t
    res["draws_seen_%d" % n] = len(run.seat_draws)
import os as _os
_files = sorted(f for f in _opened if f.startswith("/repo/data"))
_tot = 0
for f in _files:
    try: _tot += _os.path.getsize(f)
    except Exception: pass
res["data_files"] = len(_files)
res["data_bytes"] = _tot
res["biggest"] = sorted(((_os.path.getsize(f), f) for f in _files if _os.path.exists(f)), reverse=True)[:8]
json.dumps(res)
`);
} catch (e) { console.log("PYERR:\n" + String(e.message).slice(-2500)); process.exit(1); }
const r = JSON.parse(out);
const a = r.runs["20"], b = r.runs["60"];
const per = (b - a) / 40, fixed = a - 20 * per;
console.log(JSON.stringify({
  node: process.version, pyodide_boot_s: +tBoot.toFixed(2),
  numpy: r.numpy, import_s: +r.import_s.toFixed(2),
  run20_s: +a.toFixed(2), run60_s: +b.toFixed(2),
  fixed_cost_s: +fixed.toFixed(2), per_draw_ms: +(per * 1000).toFixed(1),
  extrapolated_300_s: +(fixed + 300 * per).toFixed(1),
  data_files: r.data_files, data_mb: +(r.data_bytes / 1048576).toFixed(1),
  biggest: r.biggest,
}, null, 2));
