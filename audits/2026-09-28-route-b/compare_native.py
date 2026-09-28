# Compare a Pyodide table-mode run with a native parse run, same seed and draws.
# Usage (from repo root): .venv/bin/python compare_native.py <pyodide_out.json>
import json, sys
import numpy as np
sys.path.insert(0, "src")
r = json.load(open(sys.argv[1]))
import cityconfig
cityconfig.use("joburg"); target = cityconfig.use_target("2026")
import montecarlo as mc
class A:
    config=None; set=None; draws=r["draws"]; seed=r["seed"]
run = mc.run_model(target, mc.load_scenario(A()), verbose=False)
out = {}
def plain(x):
    """Native values as the Pyodide side serialised them: sets become sorted lists."""
    if isinstance(x, (set, frozenset)):
        return sorted(x)
    if isinstance(x, list):
        return [plain(y) for y in x]
    return x
for n, v in r["arrays"].items():
    a = np.asarray(getattr(run, n))
    if a.dtype.kind == "O":
        out[n] = {"exact": plain(a.tolist()) == v, "max_abs_diff": None, "shape_equal": True}
        continue
    b = np.asarray(v, dtype=a.dtype)
    exact = bool(np.array_equal(a, b))
    diff = float(np.max(np.abs(a.astype(float) - b.astype(float)))) if a.dtype.kind in "fiub" and a.shape == b.shape else None
    out[n] = {"exact": exact, "max_abs_diff": diff, "shape_equal": a.shape == b.shape}
print(json.dumps(out, indent=1))
