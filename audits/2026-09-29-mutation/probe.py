"""What runs INSIDE the sandbox, inside one worker's copy of the tree.

    probe.py model --root COPY --mode table|parse --draws N --seed S --out F.pkl
                   [--rekey] [--cov F.json] [--cov-inside]
    probe.py tests --root COPY --ids F.txt --out F.jsonl [--stop-first]
                   [--cov-dir D]

It is started by `night.py` under `sandbox-exec` with writes to the live
repository denied, `PYTHONHASHSEED` fixed and bytecode writing off. It never
imports anything from the live tree: `sys.path[0]` is the copy's `src`.

`model` calls `run_model` directly (never `montecarlo.main`, which writes the
published artefacts) and pickles every `ModelRun` field whose name ends in
`draws`, normalised so `==` is exact comparison: numpy arrays stay arrays;
arrays of sets become nested sorted lists.

`tests` imports test modules from the copy's `tests/` and runs the named test
functions in the given order with the same per-test handling as
`tests/_support.run_module` (skip exceptions, `SystemExit` as a failure, the
active city restored after each test). One JSON line per test, flushed, so a
killed process still says how far it got.

Coverage uses `sys.monitoring` (3.12+): LINE events for files under the copy's
`src/`, each location DISABLEd after its first hit and re-armed with
`restart_events()` at every test boundary, so the cost is one callback per
line per test. Child processes are covered by `_cov/sitecustomize.py`, armed
through the environment.
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sys
import time
import traceback
from pathlib import Path

TOOL = 3  # sys.monitoring tool id (0-5 free for tools; 3 is unassigned)


class LineCov:
    def __init__(self, src_dir: str):
        self.src = str(Path(src_dir).resolve()) + os.sep
        self.hits: set[tuple[str, int]] = set()
        self.inside: set[tuple[str, int]] | None = None
        self.depth = 0
        mon = sys.monitoring
        mon.use_tool_id(TOOL, "mutnight")
        mon.register_callback(TOOL, mon.events.LINE, self._line)
        mon.set_events(TOOL, mon.events.LINE)
        self.keep_armed = False

    def _line(self, code, line):
        f = code.co_filename
        if f.startswith(self.src):
            key = (f[len(self.src):], line)
            self.hits.add(key)
            if self.depth and self.inside is not None:
                self.inside.add(key)
                return None  # stay armed while inside the watched call
            if self.keep_armed:
                return None
        return sys.monitoring.DISABLE

    def take(self) -> dict[str, list[int]]:
        out: dict[str, list[int]] = {}
        for f, ln in self.hits:
            out.setdefault(f, []).append(ln)
        self.hits = set()
        sys.monitoring.restart_events()
        return {f: sorted(v) for f, v in out.items()}

    def stop(self):
        sys.monitoring.set_events(TOOL, 0)
        sys.monitoring.free_tool_id(TOOL)


def _as_lines(pairs) -> dict[str, list[int]]:
    out: dict[str, list[int]] = {}
    for f, ln in pairs:
        out.setdefault(f, []).append(ln)
    return {f: sorted(v) for f, v in out.items()}


def normalise(value):
    import numpy as np
    if isinstance(value, np.ndarray) and value.dtype == object:
        return [normalise(v) for v in value.tolist()]
    if isinstance(value, (set, frozenset)):
        return sorted(normalise(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [normalise(v) for v in value]
    if isinstance(value, dict):
        return {k: normalise(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    return value


def cmd_model(a) -> int:
    root = Path(a.root).resolve()
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    cov = LineCov(root / "src") if a.cov else None
    if cov and a.cov_inside:
        # Every location stays armed: a line first hit OUTSIDE the watched call
        # and later inside it must still be seen inside. Slow; run once.
        cov.inside = set()
        cov.keep_armed = True
    t0 = time.monotonic()
    import cityconfig
    cityconfig.use(a.city)
    target = cityconfig.use_target(a.target)
    import montecarlo as mc
    import levels
    if a.mode == "table":
        import citywide_table as ct
        table = json.loads(ct.table_path(target).read_text())
        if a.rekey:
            # A levels.py / parties.py mutant moves the table's code key; the
            # entries are what the UNMUTATED reduction returns, which is exact
            # for every line the scheduler sends here (lines executed inside
            # `_citywide_and_roster` go to parse mode instead).
            import pools
            table["artefact_key"]["levels_sha"] = pools._code_sha(root / "src" / "levels.py")
            table["artefact_key"]["parties_sha"] = pools._code_sha(root / "src" / "parties.py")
        ct.install(table, target.year)
    elif cov is not None and cov.inside is not None:
        real = levels._citywide_and_roster

        def watched(path):
            cov.depth += 1
            try:
                return real(path)
            finally:
                cov.depth -= 1
        levels._citywide_and_roster = watched

    class Args:
        config = None
        set = None
        draws = a.draws
        seed = a.seed

    t1 = time.monotonic()
    run = mc.run_model(target, mc.load_scenario(Args()), verbose=False)
    t2 = time.monotonic()
    fields = {n: normalise(getattr(run, n)) for n in dir(run)
              if n.endswith("draws") and not n.startswith("_")}
    with open(a.out, "wb") as fh:
        pickle.dump({"fields": fields, "setup_s": t1 - t0, "run_s": t2 - t1,
                     "mc_file": mc.__file__}, fh)
    if cov:
        payload = {"lines": _as_lines(cov.hits)}
        if cov.inside is not None:
            payload["inside_citywide"] = _as_lines(cov.inside)
        cov.stop()
        Path(a.cov).write_text(json.dumps(payload))
    return 0


def cmd_tests(a) -> int:
    root = Path(a.root).resolve()
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    sys.path.insert(0, str(root / "tests"))
    ids = [ln.strip() for ln in Path(a.ids).read_text().splitlines() if ln.strip()]
    out = open(a.out, "a", buffering=1)
    cov = LineCov(root / "src") if a.cov_dir else None
    reads: dict[str, set[str]] = {}
    current = {"test": None}
    src_prefix = str((root / "src").resolve()) + os.sep
    if cov:
        os.environ["MUTCOV_DIR"] = str(Path(a.cov_dir).resolve())
        os.environ["MUTCOV_SRC"] = src_prefix
        cov_site = str(Path(__file__).resolve().parent / "_cov")
        os.environ["PYTHONPATH"] = cov_site + os.pathsep + os.environ.get("PYTHONPATH", "")

        def hook(event, args):
            # Which tests READ a src/*.py as text: they can see a mutant of
            # that file without executing the mutated line. Two kinds, told
            # apart by the stack:
            #   hash  — inside `pools._code_sha` (artefact keys, the citywide
            #           table's key). Sensitive to ANY edit; the null control
            #           decides whether the test cares.
            #   scan  — anything else (register guards, index generators,
            #           `inspect.getsource`). Selected for every mutant of the
            #           file.
            # Not reads: imports (frozen importlib on the stack), and source
            # lines fetched for a warning or a traceback (linecache without
            # inspect, or traceback).
            if event != "open" or not current["test"] or not args:
                return
            p = args[0]
            if not isinstance(p, (str, os.PathLike)):
                return
            p = os.fspath(p)
            if not p.endswith(".py"):
                return
            rp = os.path.realpath(p)
            if not rp.startswith(src_prefix):
                return
            kind = "scan"
            saw_linecache = saw_inspect = False
            f = sys._getframe(1)
            while f is not None:
                fn = f.f_code.co_filename
                if fn.startswith("<frozen importlib"):
                    return
                if fn.endswith(os.sep + "traceback.py"):
                    return
                if fn.endswith(os.sep + "linecache.py"):
                    saw_linecache = True
                elif fn.endswith(os.sep + "inspect.py"):
                    saw_inspect = True
                if f.f_code.co_name == "_code_sha":
                    kind = "hash"
                f = f.f_back
            if saw_linecache and not saw_inspect:
                return
            reads.setdefault(current["test"], set()).add(f"{kind}:{rp[len(src_prefix):]}")
        sys.addaudithook(hook)

    import _support
    skip_exc = _support.SKIP_EXCEPTIONS
    import importlib
    modules = {}
    for tid in ids:
        mod = tid.split("::")[0]
        if mod not in modules:
            t0 = time.monotonic()
            current["test"] = f"{mod}::<import>"
            try:
                modules[mod] = importlib.import_module(mod)
                err = None
            except BaseException:  # noqa: BLE001
                modules[mod] = None
                err = traceback.format_exc()[-2000:]
            current["test"] = None
            out.write(json.dumps({"import": mod, "s": round(time.monotonic() - t0, 3),
                                  "error": err,
                                  "reads": sorted(reads.pop(f"{mod}::<import>", set()))})
                      + "\n")
    # "mod::*" expands to every test_* callable in the module's namespace,
    # sorted: the population and the order `_support.run_module` uses.
    expanded = []
    for tid in ids:
        mod, name = tid.split("::")
        if name == "*":
            m = modules.get(mod)
            if m is None:
                expanded.append(f"{mod}::<import>")
                continue
            expanded += [f"{mod}::{n}" for n in sorted(
                k for k, v in vars(m).items() if k.startswith("test_") and callable(v))]
        else:
            expanded.append(tid)
    ids = expanded
    import_lines = cov.take() if cov else None
    if cov:
        Path(a.cov_dir, "_import.json").write_text(json.dumps(import_lines))
    try:
        import cityconfig as _cc
        city0 = _cc.active().slug
    except Exception:  # noqa: BLE001
        _cc = city0 = None
    rc = 0
    for tid in ids:
        mod, name = tid.split("::")
        m = modules.get(mod)
        current["test"] = tid
        os.environ["MUTCOV_TEST"] = tid
        t0 = time.monotonic()
        detail = None
        if m is None:
            status = "error-import"
        else:
            try:
                getattr(m, name)()
                status = "pass"
            except skip_exc as exc:
                status, detail = "skip", str(exc)[:300]
            except SystemExit:
                status, detail = "fail", traceback.format_exc()[-1500:]
            except BaseException:  # noqa: BLE001
                status, detail = "fail", traceback.format_exc()[-1500:]
            finally:
                if _cc is not None and city0 is not None:
                    try:
                        if _cc.active().slug != city0:
                            _cc.use(city0)
                    except Exception:  # noqa: BLE001
                        pass
        rec = {"test": tid, "status": status, "s": round(time.monotonic() - t0, 3)}
        if detail:
            rec["detail"] = detail
        if cov:
            rec["lines"] = cov.take()
            rec["reads"] = sorted(reads.pop(tid, set()))
        out.write(json.dumps(rec) + "\n")
        current["test"] = None
        if status in ("fail", "error-import"):
            rc = 1
            if a.stop_first:
                break
    out.close()
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("model")
    m.add_argument("--root", required=True)
    m.add_argument("--city", default="joburg")
    m.add_argument("--target", default="2026")
    m.add_argument("--mode", choices=("table", "parse"), default="table")
    m.add_argument("--draws", type=int, default=20)
    m.add_argument("--seed", type=int, default=20261104)
    m.add_argument("--out", required=True)
    m.add_argument("--rekey", action="store_true")
    m.add_argument("--cov")
    m.add_argument("--cov-inside", action="store_true")
    t = sub.add_parser("tests")
    t.add_argument("--root", required=True)
    t.add_argument("--ids", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--stop-first", action="store_true")
    t.add_argument("--cov-dir")
    a = ap.parse_args(argv)
    return cmd_model(a) if a.cmd == "model" else cmd_tests(a)


if __name__ == "__main__":
    raise SystemExit(main())
