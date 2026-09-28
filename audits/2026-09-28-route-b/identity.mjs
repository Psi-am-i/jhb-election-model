// Route B in Pyodide: the citywide table against parsing, same seed, same interpreter.
// Usage: node identity.mjs <repo> <draws> <seed> <out.json>
import { loadPyodide } from "pyodide";
const [repo, draws, seed, out] = process.argv.slice(2);
const now = () => Number(process.hrtime.bigint()) / 1e9;
const t0 = now();
const py = await loadPyodide();
await py.loadPackage(["numpy", "micropip"]);
try { await py.runPythonAsync(`import micropip\nawait micropip.install("openpyxl")`); }
catch (e) { console.log("OPENPYXL INSTALL FAILED:\n" + String(e.message).slice(-1500)); process.exit(1); }
const boot = now() - t0;
py.FS.mkdir("/repo");
py.FS.mount(py.FS.filesystems.NODEFS, { root: repo }, "/repo");
let res;
try { res = await py.runPythonAsync(`
import sys, os, time, json
sys.dont_write_bytecode = True
os.chdir("/repo"); sys.path.insert(0, "/repo/src")
import numpy as np
import cityconfig, levels, citywide_table as CT
cityconfig.use("joburg"); target = cityconfig.use_target("2026")
import montecarlo as mc
class A:
    config=None; set=None; draws=${draws}; seed=${seed}
def arrays(run):
    return {n: np.asarray(getattr(run, n)) for n in dir(run)
            if n.endswith("draws") and not n.startswith("_")}
real = levels._citywide_and_roster
t = time.perf_counter(); parse = arrays(mc.run_model(target, mc.load_scenario(A()), verbose=False)); t_parse = time.perf_counter()-t
table = json.loads(open(CT.table_path(target)).read())
CT.install(table, "2026")
opened = set()
def hook(ev, a):
    if ev == "open" and isinstance(a[0], str) and "data/raw/elections/" in a[0]: opened.add(os.path.basename(a[0]))
sys.addaudithook(hook)
t = time.perf_counter(); tab = arrays(mc.run_model(target, mc.load_scenario(A()), verbose=False)); t_tab = time.perf_counter()-t
levels._citywide_and_roster = real
same = {n: bool(np.array_equal(parse[n], tab[n])) for n in parse}
json.dumps({"same_interpreter_identical": same, "parse_s": t_parse, "table_s": t_tab,
            "election_files_opened_in_table_mode": sorted(opened),
            "arrays": {n: tab[n].tolist() for n in tab}},
           default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))
`); } catch (e) { console.log("PYERR:\n" + String(e.message).slice(-2500)); process.exit(1); }
const r = JSON.parse(res);
r.boot_s = boot; r.node = process.version; r.draws = +draws; r.seed = +seed;
(await import("fs")).writeFileSync(out, JSON.stringify(r));
console.log(JSON.stringify({boot_s: +boot.toFixed(1), parse_s: +r.parse_s.toFixed(1), table_s: +r.table_s.toFixed(1),
  identical: Object.values(r.same_interpreter_identical).every(x => x), per_array: r.same_interpreter_identical,
  opened: r.election_files_opened_in_table_mode}, null, 1));
