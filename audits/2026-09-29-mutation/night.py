"""Mutation night: orchestrator. Runs OUTSIDE the sandbox; every probe runs inside.

    .venv/bin/python audits/2026-09-29-mutation/night.py selftest
    .venv/bin/python audits/2026-09-29-mutation/night.py prepare --run RUN --modules src/seats.py ...
    .venv/bin/python audits/2026-09-29-mutation/night.py run     --run RUN [--jobs 7] [--budget-hours H]
    .venv/bin/python audits/2026-09-29-mutation/night.py report  --run RUN

README.md in this directory is the manual. In one paragraph:

`prepare` extracts `git archive HEAD` into a temp directory (data/ excluded,
then symlinked to the live data/ read-only through the sandbox), enumerates the
mutants, and takes the baselines everything is compared with: two fixed-seed
`run_model`s in table mode and one in parse mode, with line coverage; every
suite test, with per-test line coverage, per-test source reads and per-test
time; and one NULL mutant per module, which changes the AST and nothing the
code does, to find the tests that fail on ANY edit of that file (code hashes).
`run` applies each mutant in a worker's own copy, runs the model if the model
executes the mutated line, then the tests that execute it (cheapest first,
stopping at the first failure), and appends one JSON line per mutant to
`results.jsonl`. It skips mutants already there, so it resumes. `report` writes
`report.md` and `report.json`.
"""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import io
import json
import os
import pickle
import random
import re
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE.parents[1]
sys.path.insert(0, str(HERE))
import mutants as MU  # noqa: E402

PY = str(LIVE / ".venv" / "bin" / "python")
PROBE = str(HERE / "probe.py")
GATES_ENV = ("HELD_BACK_OFF", "THETA_WINDOW", "THETA_EXCLUDE_TARGETS",
             "FILTER_TYPE_A", "EXCLUDE_DEMARCATION_CROSSING")

#: Never run per mutant, whatever coverage says. Each writes (or tries to
#: write) the live data/ or needs the live .git; the sandbox turns each write
#: into a failure, and `report` shows where this list and the sandbox disagree.
STATIC_EXCLUDE = {
    "test_temporal": "runs real pipeline commands against the real data/processed",
    "test_chain::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts":
        "runs montecarlo.main against the real processed directory",
    "test_chain::test_the_model_refuses_to_run_without_a_pool_spec":
        "renames the live data/processed/pools_2026.json (the sandbox refused it "
        "in the pilot's baseline; not in run_all's SERIAL_ONLY)",
    "test_draw_record": "git archive of a pinned commit + three full-draw runs",
    "test_freeze": "reads git state of the live tree",
}
#: Files whose code hash keys the citywide table: a mutant there re-keys it.
TABLE_KEYED = {"src/levels.py", "src/parties.py"}
#: Default population: the forecast path (see README, "Population").
DEFAULT_MODULES = ["src/montecarlo.py", "src/pools.py", "src/levels.py",
                   "src/seats.py", "src/overhang_regimes.py", "src/citywide_table.py"]
LATER_MODULES = ["src/reweight.py", "src/reader_seats.py", "src/export_draws.py"]


# --------------------------------------------------------------------------
# plumbing
# --------------------------------------------------------------------------

def jload(p: Path, default=None):
    try:
        return json.loads(Path(p).read_text())
    except FileNotFoundError:
        return default


def jlines(p: Path) -> list[dict]:
    if not Path(p).exists():
        return []
    out = []
    for ln in Path(p).read_text().splitlines():
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            pass  # a line cut by a kill; the mutant is re-run
    return out


def git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=LIVE, check=True,
                          capture_output=True, text=True).stdout.strip()


def sandbox_profile() -> str:
    live = os.path.realpath(LIVE)
    return ("(version 1)(allow default)"
            f'(deny file-write* (subpath "{live}"))')


def probe_env(tmp_base: Path) -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in GATES_ENV and k not in ("PYTHONPATH", "MUTCOV_DIR",
                                               "MUTCOV_SRC", "MUTCOV_TEST")}
    env.update(PYTHONHASHSEED=hash_seed(), PYTHONDONTWRITEBYTECODE="1",
               OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               VECLIB_MAXIMUM_THREADS="1", MKL_NUM_THREADS="1",
               MPLBACKEND="Agg", GIT_CEILING_DIRECTORIES=str(tmp_base),
               POOLS_LOCK_WAIT="0", PYTHON_COLORS="0", NO_COLOR="1")
    return env


_HASH_SEED = None


def hash_seed() -> str:
    """`montecarlo.HASH_SEED`, read from the source (never imported here)."""
    global _HASH_SEED
    if _HASH_SEED is None:
        m = re.search(r'^HASH_SEED\s*=\s*"(\d+)"', (LIVE / "src/montecarlo.py").read_text(), re.M)
        _HASH_SEED = m.group(1) if m else "0"
    return _HASH_SEED


def run_probe(copy: Path, args: list[str], timeout: float, tmp_base: Path,
              log: Path | None = None) -> tuple[str, float, str]:
    """Run probe.py sandboxed in `copy`. Returns (status, seconds, tail)."""
    t0 = time.monotonic()
    cmd = ["sandbox-exec", "-p", sandbox_profile(), PY, PROBE, *args]
    proc = subprocess.Popen(cmd, cwd=copy, env=probe_env(tmp_base),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=timeout)
        status = "ok" if proc.returncode == 0 else f"rc{proc.returncode}"
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, _ = proc.communicate()
        status = "timeout"
    text = (out or b"").decode(errors="replace")
    if log is not None:
        log.write_text(text[-20000:])
    return status, time.monotonic() - t0, text[-3000:]


def extract_copy(dest: Path, head: str) -> None:
    """`git archive <head>` of the whole tree, data/ excluded, then data/ and
    every other untracked top-level entry symlinked to the live one.

    The whole tree, not only src/ and tests/: `tests/_support.py` chdirs to its
    own parents[1], and the suite reads the registers, config/, cities/ and
    judgements/ through that root."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    blob = subprocess.run(["git", "archive", head], cwd=LIVE, check=True,
                          capture_output=True).stdout
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        members = [m for m in tar.getmembers()
                   if not (m.name == "data" or m.name.startswith("data/"))]
        tar.extractall(dest, members=members, filter="data")
    skip = {".git", ".claude", ".pytest_cache", ".DS_Store"}
    for entry in LIVE.iterdir():
        if entry.name in skip or (dest / entry.name).exists():
            continue
        (dest / entry.name).symlink_to(entry)
    for pc in dest.rglob("__pycache__"):
        shutil.rmtree(pc, ignore_errors=True)


def data_snapshot() -> dict[str, list]:
    """(size, mtime_ns) of every file under the live data/ — proof, at the end
    of a run, that nothing wrote there."""
    out = {}
    root = LIVE / "data"
    for dirpath, _, files in os.walk(root):
        for f in files:
            p = Path(dirpath) / f
            try:
                st = p.lstat()
            except FileNotFoundError:
                continue
            out[str(p.relative_to(LIVE))] = [st.st_size, st.st_mtime_ns]
    return out


def input_hashes() -> dict[str, str]:
    """The model's precomputed inputs a concurrent writer could move."""
    proc = LIVE / "data" / "processed"
    names = ["pools_2026.json", "citywide_2026.json", "turnout.csv"]
    names += sorted(p.name for p in proc.glob("fold*_parameters*.csv"))
    out = {}
    for n in names:
        p = proc / n
        if p.exists():
            out[n] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


class ReadLock:
    """`pools.artefact_lock("read")`, taken without writing: a shared flock on
    the existing lock file, opened read-only. An emit then fails loudly instead
    of moving the baseline under the night (CLAUDE.md §3)."""

    def __init__(self):
        self.fh = None

    def __enter__(self):
        path = LIVE / "data" / "processed" / ".pools.lock"
        if not path.exists():
            print("  ! no pools lock file; proceeding without the read lock")
            return self
        self.fh = open(path, "r")
        try:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit("pools artefacts are locked for EMIT by another "
                             "process; a mutation run would measure a moving tree")
        return self

    def __exit__(self, *exc):
        if self.fh:
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
            self.fh.close()


# --------------------------------------------------------------------------
# comparing draws
# --------------------------------------------------------------------------

def same(a, b) -> bool:
    import numpy as np
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        if not (isinstance(a, np.ndarray) and isinstance(b, np.ndarray)):
            return False
        return a.dtype == b.dtype and a.shape == b.shape and bool(np.array_equal(a, b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, float) and isinstance(b, float) and a != a and b != b:
        return True  # NaN in the same place
    return type(a) is type(b) and a == b


def moved_fields(base: dict, other: dict) -> list[str]:
    names = set(base) | set(other)
    return sorted(n for n in names
                  if n not in base or n not in other or not same(base[n], other[n]))


def cmd_selftest(_a) -> int:
    """The comparator's positive controls (QC.md §3): each constructed change is
    seen, and the comparator goes quiet when it is reverted."""
    import numpy as np
    base = {"seat_draws": np.arange(12).reshape(3, 4),
            "pr_share_draws": np.linspace(0.1, 0.9, 12).reshape(3, 4),
            "over_draws": [[["ANC"], []], [[], ["DA"]]]}
    fails = []

    def check(name, mutate, revert):
        import copy as _copy
        other = _copy.deepcopy(base)
        mutate(other)
        if not moved_fields(base, other):
            fails.append(f"{name}: not seen")
        revert(other)
        if moved_fields(base, other):
            fails.append(f"{name}: not quiet after revert")

    f0 = float(base["pr_share_draws"][1, 2])
    check("one ulp in a float cell",
          lambda o: o["pr_share_draws"].__setitem__((1, 2), np.nextafter(f0, 1.0)),
          lambda o: o["pr_share_draws"].__setitem__((1, 2), f0))
    check("one seat",
          lambda o: o["seat_draws"].__setitem__((0, 0), 1),
          lambda o: o["seat_draws"].__setitem__((0, 0), 0))
    check("a set member",
          lambda o: o["over_draws"][0][1].append("EFF"),
          lambda o: o["over_draws"][0][1].pop())
    check("a dtype change",
          lambda o: o.__setitem__("seat_draws", o["seat_draws"].astype(float)),
          lambda o: o.__setitem__("seat_draws", o["seat_draws"].astype(base["seat_draws"].dtype)))
    check("a field removed",
          lambda o: o.pop("over_draws"),
          lambda o: o.__setitem__("over_draws", json.loads(json.dumps(base["over_draws"]))))
    # enumerator: every mutant parses and keeps every line number
    src = (LIVE / "src" / "seats.py").read_text()
    ms = MU.enumerate_mutants(src, "src/seats.py")
    for m in ms:
        new = MU.apply(src, m)
        if new.count("\n") != src.count("\n"):
            fails.append(f"mutant {m['id']} moves line numbers")
    ops = Counter(m["op"] for m in ms)
    for op in MU.OPERATORS:
        if op != "offbyone" and not ops.get(op):
            fails.append(f"operator {op} produced nothing on seats.py")
    for f in fails:
        print("✗", f)
    print("selftest:", "FAILED" if fails else f"ok ({len(ms)} seats.py mutants, ops {dict(ops)})")
    return 1 if fails else 0


# --------------------------------------------------------------------------
# prepare
# --------------------------------------------------------------------------

class Run:
    def __init__(self, path: Path):
        self.dir = Path(path).resolve()
        self.meta = jload(self.dir / "meta.json", {})

    @property
    def tmp(self) -> Path:
        return Path(self.meta["tmp"])

    @property
    def pristine(self) -> Path:
        return self.tmp / "pristine"

    def save_meta(self):
        (self.dir / "meta.json").write_text(json.dumps(self.meta, indent=1))

    def mutants(self, module: str) -> list[dict]:
        return jlines(self.dir / "mutants" / (module.replace("/", "__") + ".jsonl"))


def _model_args(run: Run, out: Path, mode: str, rekey=False, cov=None, inside=False):
    a = ["model", "--root", ".", "--mode", mode, "--draws", str(run.meta["draws"]),
         "--seed", str(run.meta["seed"]), "--city", run.meta["city"],
         "--target", run.meta["target"], "--out", str(out)]
    if rekey:
        a.append("--rekey")
    if cov:
        a += ["--cov", str(cov)]
    if inside:
        a.append("--cov-inside")
    return a


def cmd_prepare(a) -> int:
    run = Run(a.run)
    run.dir.mkdir(parents=True, exist_ok=True)
    head = git_head()
    if run.meta and run.meta.get("head") != head:
        raise SystemExit(f"run {run.dir} was prepared at {run.meta['head']}, HEAD is "
                         f"{head}; start a new run directory")
    modules = a.modules or DEFAULT_MODULES
    missing = [m for m in modules if not (LIVE / m).exists()]
    if missing:
        print(f"  ! not in the tree yet, skipped: {missing}")
        modules = [m for m in modules if m not in missing]
    tmp = Path(tempfile.gettempdir()).resolve() / f"mutnight-{run.dir.name}"
    if run.meta.get("modules") and run.meta["modules"] != modules:
        raise SystemExit("a prepared run's module list cannot change; use a new run directory")
    run.meta.update(head=head, modules=modules, tmp=str(tmp), city=a.city,
                    target=a.target, draws=a.draws, seed=a.seed,
                    created=time.strftime("%Y-%m-%d %H:%M:%S"),
                    python=sys.version.split()[0], hash_seed=hash_seed(),
                    max_test_s=a.max_test_s)
    run.save_meta()
    with ReadLock():
        run.meta["inputs_at_prepare"] = input_hashes()
        (run.dir / "data_snapshot_prepare.json").write_text(json.dumps(data_snapshot()))
        if a.redo or not (run.pristine / "src").exists():
            print(f"extracting {head[:10]} into {run.pristine}")
            extract_copy(run.pristine, head)
        _sandbox_probe(run)
        _enumerate(run)
        base = run.dir / "baseline"
        base.mkdir(exist_ok=True)
        if a.redo or not (base / "model_table.pkl").exists():
            _baseline_model(run, base)
        if a.redo or a.redo_tests or not (base / "tests.jsonl").exists():
            _baseline_tests(run, base, a.jobs)
        _null_controls(run, base, a.jobs)
        run.meta["prepared"] = time.strftime("%Y-%m-%d %H:%M:%S")
        run.save_meta()
    print(f"prepared {run.dir}")
    return 0


def _sandbox_probe(run: Run) -> None:
    """A write through the copy's data/ symlink must be refused."""
    target = run.pristine / "data" / "processed" / ".mutnight_write_probe"
    r = subprocess.run(["sandbox-exec", "-p", sandbox_profile(), "/bin/sh", "-c",
                        f"echo x > '{target}'"], capture_output=True, text=True)
    live_target = LIVE / "data" / "processed" / ".mutnight_write_probe"
    if r.returncode == 0 or live_target.exists():
        raise SystemExit("sandbox did NOT refuse a write through the copy's data/ "
                         "symlink; refusing to run")
    print("  ✓ sandbox refuses writes through the copy's data/ symlink")


def _enumerate(run: Run) -> None:
    (run.dir / "mutants").mkdir(exist_ok=True)
    for mod in run.meta["modules"]:
        path = run.dir / "mutants" / (mod.replace("/", "__") + ".jsonl")
        src = (run.pristine / mod).read_text()
        ms = MU.enumerate_mutants(src, mod)
        path.write_text("".join(json.dumps(m) + "\n" for m in ms))
        print(f"  {mod}: {len(ms)} mutants {dict(Counter(m['op'] for m in ms))}")


def _baseline_model(run: Run, base: Path) -> None:
    rekey = False
    jobs = {"table": dict(mode="table", cov=base / "cov_model_table.json"),
            "table2": dict(mode="table"),
            "parse": dict(mode="parse", cov=base / "cov_model_parse.json", inside=True)}
    outs = {}
    with ThreadPoolExecutor(len(jobs)) as pool:
        futs = {}
        for k, spec in jobs.items():
            copy = run.tmp / f"base-{k}"
            shutil.copytree(run.pristine, copy, symlinks=True, dirs_exist_ok=True)
            out = copy.parent / f"base-{k}.pkl"
            covtmp = copy.parent / f"base-{k}.cov.json" if spec.get("cov") else None
            args = _model_args(run, out, spec["mode"], rekey, covtmp, spec.get("inside", False))
            futs[k] = (pool.submit(run_probe, copy, args, 3600, run.tmp,
                                   base / f"model_{k}.log"), out, covtmp, spec)
        for k, (fut, out, covtmp, spec) in futs.items():
            status, secs, tail = fut.result()
            if status != "ok":
                raise SystemExit(f"baseline model {k} failed ({status}):\n{tail}")
            shutil.copy(out, base / f"model_{k}.pkl")
            if covtmp:
                shutil.copy(covtmp, spec["cov"])
            outs[k] = pickle.loads(out.read_bytes())
            print(f"  baseline model {k}: {secs:.1f}s wall "
                  f"(setup {outs[k]['setup_s']:.1f}s, run_model {outs[k]['run_s']:.1f}s)")
    det = moved_fields(outs["table"]["fields"], outs["table2"]["fields"])
    tp = moved_fields(outs["table"]["fields"], outs["parse"]["fields"])
    run.meta["baseline_model"] = {
        "fields": sorted(outs["table"]["fields"]),
        "table_twice_differs": det, "table_vs_parse_differs": tp,
        "table_run_s": outs["table2"]["run_s"], "table_setup_s": outs["table2"]["setup_s"],
    }
    run.save_meta()
    if det:
        raise SystemExit(f"two identical table-mode runs differ in {det}: not deterministic")
    if tp:
        raise SystemExit(f"table mode and parse mode differ in {tp}; §1.265 no longer holds")
    print(f"  ✓ deterministic; table == parse on {len(outs['table']['fields'])} *draws fields")
    # the model's timing, per mode, for scheduling (from a second probe of each)
    run.meta["model_s"] = {"table": _probe_seconds(base / "model_table2.log", outs["table2"]),
                           "parse": None}
    run.save_meta()


def _probe_seconds(_log, out) -> float:
    return float(out["setup_s"] + out["run_s"])


def _baseline_tests(run: Run, base: Path, jobs: int) -> None:
    """Every suite module, sandboxed, with per-test coverage, reads and time."""
    modules = _suite_modules(run.pristine)
    covroot = run.tmp / "cov"
    shutil.rmtree(covroot, ignore_errors=True)
    copies = _worker_copies(run, jobs, prefix="bt")
    lock = threading.Lock()
    results: list[dict] = []
    imports: dict[str, dict] = {}

    def one(mod):
        copy = copies.get()
        try:
            d = covroot / mod
            d.mkdir(parents=True, exist_ok=True)
            ids = copy.parent / f"{copy.name}-{mod}.ids"
            ids.write_text(f"{mod}::*\n")
            out = copy.parent / f"{copy.name}-{mod}.jsonl"
            out.unlink(missing_ok=True)
            status, secs, tail = run_probe(copy, ["tests", "--root", ".", "--ids", str(ids),
                                                  "--out", str(out), "--cov-dir", str(d)],
                                           5400, run.tmp, base / "logs" / f"{mod}.log")
            recs = jlines(out)
            children = defaultdict(lambda: defaultdict(set))
            for cf in d.glob("child-*.json"):
                c = jload(cf, {})
                for f, lines in (c.get("lines") or {}).items():
                    children[c.get("test")][f].update(lines)
            with lock:
                for r in recs:
                    if "import" in r:
                        imports[r["import"]] = r
                        continue
                    ch = children.get(r["test"])
                    if ch:
                        r["child_lines"] = {f: sorted(v) for f, v in ch.items()}
                    results.append(r)
                if status == "timeout":
                    results.append({"test": f"{mod}::<timeout>", "status": "timeout", "s": secs})
            print(f"  {mod}: {len(recs)} records, {secs:.0f}s ({status})", flush=True)
        finally:
            copies.put(copy)

    (base / "logs").mkdir(exist_ok=True)
    t0 = time.monotonic()
    # longest first, by the suite's own named list
    order = sorted(modules, key=lambda m: 0 if m in ("test_levers_are_live",
                                                      "test_levels_dispersion",
                                                      "test_drawer") else 1)
    with ThreadPoolExecutor(jobs) as pool:
        list(pool.map(one, order))
    (base / "tests.jsonl").write_text("".join(json.dumps(r) + "\n" for r in results))
    (base / "test_imports.json").write_text(json.dumps(imports))
    st = Counter(r["status"] for r in results)
    run.meta["baseline_tests"] = {"counts": dict(st), "wall_s": time.monotonic() - t0,
                                  "module_s": sum(r["s"] for r in results)}
    run.save_meta()
    print(f"  baseline tests: {dict(st)} in {time.monotonic() - t0:.0f}s wall")


def _suite_modules(root: Path) -> list[str]:
    import ast
    tree = ast.parse((root / "tests" / "run_all.py").read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "MODULES" for t in node.targets):
            return [e.value for e in node.value.elts]
    raise SystemExit("tests/run_all.py has no MODULES list")


class _Copies:
    def __init__(self, paths):
        import queue
        self.q = queue.Queue()
        for p in paths:
            self.q.put(p)

    def get(self):
        return self.q.get()

    def put(self, p):
        self.q.put(p)


def _worker_copies(run: Run, n: int, prefix="w") -> _Copies:
    """n private copies of the pristine tree. An existing copy is reused only
    after every population file is checked against the pristine one and put
    back if it differs — a killed run can leave a mutant in place."""
    paths = []
    for i in range(n):
        p = run.tmp / f"{prefix}{i}"
        if not p.exists():
            shutil.copytree(run.pristine, p, symlinks=True)
        for f in run.meta["modules"]:
            want = (run.pristine / f).read_text()
            if (p / f).read_text() != want:
                (p / f).write_text(want)
                print(f"  restored {p.name}/{f} (left mutated by an interrupted run)")
        paths.append(p)
    return _Copies(paths)


# --------------------------------------------------------------------------
# the index the scheduler reads
# --------------------------------------------------------------------------

class Index:
    """Everything `prepare` measured, shaped for per-mutant decisions."""

    def __init__(self, run: Run):
        base = run.dir / "baseline"
        self.run = run
        tc = jload(base / "cov_model_table.json")
        pc = jload(base / "cov_model_parse.json")
        self.model_lines = defaultdict(set)
        for cov in (tc, pc):
            for f, lines in cov["lines"].items():
                self.model_lines["src/" + f].update(lines)
        self.inside = defaultdict(set)
        for f, lines in pc.get("inside_citywide", {}).items():
            self.inside["src/" + f].update(lines)
        self.tests: dict[str, dict] = {}
        for r in jlines(base / "tests.jsonl"):
            self.tests[r["test"]] = r
        imports = jload(base / "test_imports.json", {})
        # per test: file -> set(lines), children included
        self.cov: dict[str, dict[str, set]] = {}
        for tid, r in self.tests.items():
            d = defaultdict(set)
            for key in ("lines", "child_lines"):
                for f, lines in (r.get(key) or {}).items():
                    d["src/" + f].update(lines)
            self.cov[tid] = d
        # who reads which src file as text: "scan" readers are selected for
        # every mutant of the file; "hash" readers only for its null control
        self.readers: dict[str, set[str]] = defaultdict(set)
        self.hash_readers: dict[str, set[str]] = defaultdict(set)

        def note(tid, entry):
            kind, _, f = entry.partition(":")
            (self.readers if kind == "scan" else self.hash_readers)["src/" + f].add(tid)

        for tid, r in self.tests.items():
            for e in r.get("reads") or []:
                note(tid, e)
        for mod, rec in imports.items():
            for e in rec.get("reads") or []:
                for tid in self.tests:
                    if tid.startswith(mod + "::"):
                        note(tid, e)
        self.spawners = {tid for tid, r in self.tests.items() if r.get("child_lines")}
        # exclusions
        self.excluded: dict[str, str] = {}
        for tid, r in self.tests.items():
            mod = tid.split("::")[0]
            why = STATIC_EXCLUDE.get(tid) or STATIC_EXCLUDE.get(mod)
            if why:
                self.excluded[tid] = f"static: {why}"
            elif r["status"] != "pass":
                self.excluded[tid] = f"baseline {r['status']}"
            elif r["s"] > run.meta.get("max_test_s", 120):
                self.excluded[tid] = f"slow: {r['s']:.0f}s at baseline > cap"
        self.hash_sensitive: dict[str, set[str]] = defaultdict(set)
        for n in jlines(base / "nulls.jsonl"):
            self.hash_sensitive[n["file"]].update(n.get("failed", []))
        self.unreliable = set(jload(run.dir / "unreliable.json", []))
        # test module source text, for module-level name references
        self.test_src = {}
        for p in (run.pristine / "tests").glob("test_*.py"):
            self.test_src[p.stem] = p.read_text()
        srcs = {f"src/{p.name}": p.read_text() for p in (run.pristine / "src").glob("*.py")}
        self.refs = MU.reference_index(srcs)
        self.srcs = srcs
        self._closure_cache = {}

    def usable(self, tid: str, file: str) -> bool:
        return (tid not in self.excluded and tid not in self.unreliable
                and tid not in self.hash_sensitive.get(file, ()))

    def _covering(self, file: str, lo: int, hi: int) -> set[str]:
        return {tid for tid, d in self.cov.items()
                if any(lo <= ln <= hi for ln in d.get(file, ()))}

    def reaching(self, m: dict) -> set[str]:
        """Every test that can observe mutant m, before exclusions (README,
        'Which tests run for a mutant')."""
        f = m["file"]
        out = set(self.readers.get(f, ()))
        if m["kind"] == "body":
            out |= self._covering(f, m["lines"][0], m["lines"][1])
        elif m["kind"] == "default":
            out |= self._covering(f, m["func_span"][0], m["func_span"][1])
        else:  # module / class level: follow the names it binds
            names = tuple(sorted(m.get("names") or ()))
            if not names:
                out |= {tid for tid, d in self.cov.items() if d.get(f)}
            else:
                if names not in self._closure_cache:
                    self._closure_cache[names] = MU.module_level_closure(self.srcs, set(names))
                allnames = self._closure_cache[names]
                for n in allnames:
                    for (rf, lo, hi) in self.refs.get(n, ()):
                        out |= self._covering(rf, lo, hi)
                    pat = re.compile(rf"\b{re.escape(n)}\b")
                    for mod, text in self.test_src.items():
                        if pat.search(text):
                            out |= {tid for tid in self.tests if tid.startswith(mod + "::")}
        return out

    def executing(self, m: dict) -> set[str]:
        """Tests whose coverage EXECUTES the mutated code (not merely reads the
        file): body lines directly, a default through its function's body."""
        f = m["file"]
        if m["kind"] == "body":
            return self._covering(f, m["lines"][0], m["lines"][1])
        if m["kind"] == "default":
            return self._covering(f, m["func_span"][0], m["func_span"][1])
        return self.reaching(m) - self.readers.get(f, set())

    def in_model(self, m: dict) -> bool:
        lines = self.model_lines.get(m["file"], set())
        return any(m["lines"][0] <= ln <= m["lines"][1] for ln in lines)

    def mode(self, m: dict) -> str:
        lines = self.inside.get(m["file"], set())
        return "parse" if any(m["lines"][0] <= ln <= m["lines"][1] for ln in lines) else "table"


def _null_controls(run: Run, base: Path, jobs: int) -> None:
    """One null mutant per module: the model must not move, and every test that
    fails is hash-sensitive to that file (it fails on ANY edit of it).

    Two passes, because the candidates (every test that hashes, scans or
    spawns) are most of the suite: first every module's null at once, all
    candidates in parallel; then, per module, only the tests that failed the
    combined pass, with that module's null alone."""
    idx = Index(run)
    copies = _worker_copies(run, jobs)
    mods = run.meta["modules"]
    nulls = {m: MU.null_mutant((run.pristine / m).read_text(), m) for m in mods}
    edited = {m: (run.pristine / m).read_text() + nulls[m]["replacement"] for m in mods}

    def cands(m):
        return {t for t in (idx.readers.get(m, set()) | idx.hash_readers.get(m, set())
                            | idx.spawners) if t not in idx.excluded}

    union = set().union(*(cands(m) for m in mods))
    t0 = time.monotonic()
    failed_all = _run_tests_parallel(run, idx, copies, sorted(union), edited)
    print(f"  combined null: {len(union)} candidate tests, {len(failed_all)} failed, "
          f"{time.monotonic() - t0:.0f}s", flush=True)
    out = []
    for m in mods:
        res = _run_mutant(run, idx, copies, nulls[m], forced_tests=[], force_model=True)
        again = sorted(cands(m) & failed_all)
        failed = sorted(_run_tests_parallel(run, idx, copies, again, {m: edited[m]})) if again else []
        res["failed"] = failed
        res["candidates"] = len(cands(m))
        out.append(res)
        print(f"  null {m}: model {res['model']['status']}, {len(cands(m))} candidate "
              f"tests, hash-sensitive: {failed}", flush=True)
        if res["model"]["status"] != "identical":
            raise SystemExit(f"null mutant of {m} moved the model "
                             f"({res['model']}); the harness cannot tell a mutant from noise")
    (base / "nulls.jsonl").write_text("".join(json.dumps(r) + "\n" for r in out))


def _run_tests_parallel(run, idx, copies, tests, edited: dict[str, str]) -> set[str]:
    """Run `tests` (no stop-first) across the worker copies with `edited`
    files in place. Grouped by test module; returns the failed test ids."""
    groups = defaultdict(list)
    for t in tests:
        groups[t.split("::")[0]].append(t)
    failed: set[str] = set()
    lock = threading.Lock()

    def one(group):
        copy = copies.get()
        try:
            for f, text in edited.items():
                (copy / f).write_text(text)
            r = _run_tests(run, idx, copy, group, stop_first=False)
            with lock:
                failed.update(r.get("failed", []))
                if r["status"] in ("timeout", "crash"):
                    failed.update(t for t in group)  # cannot say which; all suspect
        finally:
            for f in edited:
                (copy / f).write_text((run.pristine / f).read_text())
            copies.put(copy)

    order = sorted(groups.values(), key=lambda g: -sum(idx.tests.get(t, {}).get("s", 0) for t in g))
    with ThreadPoolExecutor(len(copies.q.queue) or 1) as pool:
        list(pool.map(one, order))
    return failed


# --------------------------------------------------------------------------
# one mutant
# --------------------------------------------------------------------------

_BASE_CACHE = {}


def _baseline_fields(run: Run, mode: str) -> dict:
    key = (str(run.dir), mode)
    if key not in _BASE_CACHE:
        p = run.dir / "baseline" / ("model_table.pkl" if mode == "table" else "model_parse.pkl")
        _BASE_CACHE[key] = pickle.loads(p.read_bytes())["fields"]
    return _BASE_CACHE[key]


def _run_mutant(run: Run, idx: Index, copies: _Copies, m: dict,
                forced_tests=None, force_model=False, stop_first=True,
                test_budget: float = 0.0, prior: dict | None = None) -> dict:
    """One mutant: the model (unless `prior` already ran it), then the tests.

    `test_budget` > 0 is stage 1: the cheapest reaching tests, by baseline
    seconds, up to that many seconds (at least one). `prior` is a stage-1
    result: stage 2 runs only the tests stage 1 did not, and keeps its model."""
    copy = copies.get()
    t_start = time.monotonic()
    target = copy / m["file"]
    original = (run.pristine / m["file"]).read_text()
    res = {k: m[k] for k in ("id", "file", "line", "op", "desc", "func", "kind")}
    try:
        target.write_text(MU.apply(original, m) if m["op"] != "null"
                          else original + m["replacement"])
        # ---- the model
        mode = idx.mode(m)
        executed = force_model or idx.in_model(m)
        mres = {"mode": mode, "executed": executed}
        if prior is not None:
            mres = prior["model"]
        elif executed:
            out = copy.parent / f"{copy.name}.pkl"
            out.unlink(missing_ok=True)
            est = run.meta["model_s"]["table"] * (5 if mode == "parse" else 1)
            status, secs, tail = run_probe(
                copy, _model_args(run, out, mode, rekey=m["file"] in TABLE_KEYED),
                max(120, 6 * est), run.tmp)
            mres["s"] = round(secs, 2)
            if status == "timeout":
                mres["status"] = "timeout"
            elif status != "ok" or not out.exists():
                mres["status"] = "crash"
                mres["error"] = tail[-600:]
            else:
                got = pickle.loads(out.read_bytes())["fields"]
                mf = moved_fields(_baseline_fields(run, mode), got)
                mres["status"] = "moved" if mf else "identical"
                if mf:
                    mres["moved_fields"] = mf
        elif prior is None:
            mres["status"] = "not-executed"
        res["model"] = mres
        # ---- the tests
        reach = idx.reaching(m) if forced_tests is None else set(forced_tests)
        if forced_tests is None:
            chosen = [t for t in reach if idx.usable(t, m["file"])]
        else:
            chosen = list(reach)
        chosen.sort(key=lambda t: idx.tests.get(t, {}).get("s", 1e9))
        full = len(chosen)
        done_before = set(prior["tests"].get("ran_ids", [])) if prior else set()
        chosen = [t for t in chosen if t not in done_before]
        if test_budget > 0:
            take, acc = [], 0.0
            for t in chosen:
                acc += idx.tests.get(t, {}).get("s", 0)
                if take and acc > test_budget:
                    break
                take.append(t)
            chosen = take
        tres = {"reaching": len(reach), "selected": full,
                "this_stage": len(chosen), "ran_ids": sorted(done_before)}
        if chosen:
            tres.update(_run_tests(run, idx, copy, chosen, stop_first))
            tres["ran_ids"] = sorted(done_before | set(tres.pop("finished", [])))
            if tres.get("status") == "killed" and forced_tests is None:
                killer = tres["killer"]
                if not _passes_alone(run, idx, copy, m["file"], original, killer):
                    # a false kill hides a survivor; exclude and re-run
                    target.write_text(MU.apply(original, m))
                    rest = [t for t in chosen if t != killer]
                    tres = {"reaching": len(reach), "selected": full - 1,
                            "this_stage": len(rest), "dropped_unreliable": killer,
                            "ran_ids": sorted(done_before - {killer})}
                    if rest:
                        tres.update(_run_tests(run, idx, copy, rest, stop_first))
                        tres["ran_ids"] = sorted(set(tres["ran_ids"])
                                                 | set(tres.pop("finished", [])))
                    else:
                        tres["status"] = "none"
        else:
            tres["status"] = "none"
        tres["complete"] = (tres.get("status") in ("survived", "none")
                            and len(tres["ran_ids"]) >= tres["selected"])
        res["tests"] = tres
    finally:
        target.write_text(original)
        copies.put(copy)
    res["s"] = round(time.monotonic() - t_start, 2)
    res["stage"] = 2 if prior else (1 if test_budget > 0 else 0)
    if prior:
        res["s_stage1"] = prior.get("s")
    res["class"] = classify(res)
    return res


def _run_tests(run, idx, copy, chosen, stop_first) -> dict:
    ids = copy.parent / f"{copy.name}.ids"
    ids.write_text("\n".join(chosen) + "\n")
    out = copy.parent / f"{copy.name}.tests.jsonl"
    out.unlink(missing_ok=True)
    budget = 90 + 4 * sum(idx.tests.get(t, {}).get("s", 30) for t in chosen)
    args = ["tests", "--root", ".", "--ids", str(ids), "--out", str(out)]
    if stop_first:
        args.append("--stop-first")
    status, secs, tail = run_probe(copy, args, budget, run.tmp)
    recs = [r for r in jlines(out) if "test" in r]
    failed = [r["test"] for r in recs if r["status"] in ("fail", "error-import")]
    # The tests that FINISHED. A test cut off by a timeout or a crash has no
    # record and is not in this list, so stage 2 runs it again rather than
    # counting it as passed.
    res = {"ran": len(recs), "s": round(secs, 2), "failed": failed,
           "finished": [r["test"] for r in recs]}
    if failed:
        res["status"] = "killed"
        res["killer"] = failed[0]
        detail = next((r.get("detail") for r in recs if r["test"] == failed[0]), "")
        res["killer_detail"] = (detail or "")[-400:]
    elif status == "timeout":
        res["status"] = "timeout"
    elif status != "ok" and len(recs) < len(chosen):
        res["status"] = "crash"
        res["error"] = tail[-600:]
    else:
        res["status"] = "survived"
    return res


_ALONE_LOCK = threading.Lock()


def _passes_alone(run, idx, copy, file, original, tid) -> bool:
    """Does `tid` pass run ALONE on the pristine tree? Cached per test."""
    path = run.dir / "alone.json"
    with _ALONE_LOCK:
        cache = jload(path, {})
        if tid in cache:
            return cache[tid]
    (copy / file).write_text(original)
    r = _run_tests(run, idx, copy, [tid], True)
    ok = r["status"] == "survived"
    with _ALONE_LOCK:
        cache = jload(path, {})
        cache[tid] = ok
        path.write_text(json.dumps(cache, indent=1))
        if not ok:
            unr = set(jload(run.dir / "unreliable.json", []))
            unr.add(tid)
            (run.dir / "unreliable.json").write_text(json.dumps(sorted(unr), indent=1))
            idx.unreliable.add(tid)
    return ok


def classify(res: dict) -> str:
    t, mo = res["tests"], res["model"]
    if t.get("status") == "killed":
        return "KILLED"
    if t.get("status") == "timeout" or mo["status"] == "timeout":
        return "TIMEOUT"
    if mo["status"] == "crash" or t.get("status") == "crash":
        return "CRASH"
    if mo["status"] == "moved":
        return "MOVED-UNTESTED"
    return "INERT"


# --------------------------------------------------------------------------
# run
# --------------------------------------------------------------------------

def _estimate(idx: Index, m: dict, test_budget: float = 0.0) -> float:
    """Upper bound on one mutant's seconds: stop-first only makes it shorter."""
    s = 0.0
    if idx.in_model(m):
        s += idx.run.meta["model_s"]["table"] * (5 if idx.mode(m) == "parse" else 1) + 1.5
    ts = sorted(idx.tests.get(t, {}).get("s", 0) for t in idx.reaching(m)
                if idx.usable(t, m["file"]))
    acc = 0.0
    for x in ts:
        if test_budget > 0 and acc and acc + x > test_budget:
            break
        acc += x
    return s + acc + (4.0 if ts else 0.1)


def _sample(ms: list[dict], idx: Index, budget_s: float, jobs: int, seed: int,
            test_budget: float = 0.0):
    """Stratified by (function, operator): round-robin over strata in a seeded
    random order until the estimated cost fills the budget."""
    est = {m["id"]: _estimate(idx, m, test_budget) for m in ms}
    total = sum(est.values()) / jobs
    if total <= budget_s:
        return ms, total, False
    rng = random.Random(seed)
    strata = defaultdict(list)
    for m in ms:
        strata[(m["func"], m["op"])].append(m)
    for v in strata.values():
        rng.shuffle(v)
    keys = list(strata)
    rng.shuffle(keys)
    chosen, spent = [], 0.0
    while any(strata[k] for k in keys):
        for k in keys:
            if strata[k]:
                m = strata[k].pop()
                if spent + est[m["id"]] / jobs > budget_s:
                    continue
                chosen.append(m)
                spent += est[m["id"]] / jobs
        if spent >= budget_s * 0.98:
            break
        if all(spent + est[s[-1]["id"]] / jobs > budget_s for s in strata.values() if s):
            break
    return chosen, total, True


def cmd_run(a) -> int:
    run = Run(a.run)
    if not run.meta.get("prepared"):
        raise SystemExit("run `prepare` first")
    if git_head() != run.meta["head"]:
        print(f"  ! HEAD moved since prepare ({run.meta['head'][:10]}); the copies are "
              f"still {run.meta['head'][:10]}, which is what is mutated")
    idx = Index(run)
    results_path = run.dir / "results.jsonl"
    latest = {r["id"]: r for r in jlines(results_path)}
    done = set(latest)
    modules = a.modules or run.meta["modules"]
    plan = []
    if a.stage2:
        # survivors whose reaching tests were not all run: finish them,
        # the owner's concern (INERT) first, then MOVED-UNTESTED
        prio = {"INERT": 0, "MOVED-UNTESTED": 1, "CRASH": 2, "TIMEOUT": 3}
        todo = [r for r in latest.values() if r["file"] in modules
                and r["class"] != "KILLED" and not r["tests"].get("complete", True)]
        todo.sort(key=lambda r: (prio.get(r["class"], 9), r["file"], r["line"]))
        by_id = {m["id"]: m for mod in modules for m in run.mutants(mod)}
        plan = [(by_id[r["id"]], r) for r in todo]
        print(f"  stage 2: {len(plan)} survivors with unrun reaching tests")
    sampling = run.meta.setdefault("sampling", {})
    for mod in ([] if a.stage2 else modules):
        ms = run.mutants(mod)
        if a.budget_hours:
            chosen, est, sampled = _sample(ms, idx, a.budget_hours * 3600, a.jobs,
                                           a.sample_seed, a.test_budget)
        else:
            chosen, est, sampled = ms, sum(_estimate(idx, m, a.test_budget)
                                           for m in ms) / a.jobs, False
        sampling[mod] = {"population": len(ms), "chosen": len(chosen),
                         "sampled": sampled, "estimated_s_full": round(est),
                         "seed": a.sample_seed if sampled else None}
        print(f"  {mod}: {len(chosen)}/{len(ms)} mutants "
              f"({'SAMPLED' if sampled else 'all'}), est. full-module wall "
              f"{est / 3600:.2f} h at {a.jobs} jobs")
        plan += [(m, None) for m in chosen if m["id"] not in done]
    run.save_meta()
    if a.limit:
        plan = plan[: a.limit]
    print(f"  {len(plan)} mutants to run ({len(done)} already done)")
    copies = _worker_copies(run, a.jobs)
    wlock = threading.Lock()
    abort = threading.Event()
    counter = {"n": 0}
    t0 = time.monotonic()

    def control():
        copy = copies.get()
        try:
            out = copy.parent / f"{copy.name}.ctl.pkl"
            status, _, tail = run_probe(copy, _model_args(run, out, "table"), 600, run.tmp)
            if status != "ok":
                return f"control run failed: {tail[-300:]}"
            mf = moved_fields(_baseline_fields(run, "table"),
                              pickle.loads(out.read_bytes())["fields"])
            return f"control run moved {mf}" if mf else None
        finally:
            copies.put(copy)

    def one(item):
        m, prior = item
        if abort.is_set():
            return
        res = _run_mutant(run, idx, copies, m, test_budget=0 if prior else a.test_budget,
                          prior=prior)
        with wlock:
            with open(results_path, "a") as fh:
                fh.write(json.dumps(res) + "\n")
            counter["n"] += 1
            n = counter["n"]
            if n % 25 == 0 or n == len(plan):
                el = time.monotonic() - t0
                print(f"  {n}/{len(plan)}  {el / 60:.1f} min  "
                      f"({el / n:.1f} s/mutant wall)", flush=True)
        if a.control_every and n % a.control_every == 0:
            why = control()
            if why:
                (run.dir / "ABORTED").write_text(why + "\n")
                print(f"  ✗ ABORT: {why}")
                abort.set()

    with ReadLock():
        with ThreadPoolExecutor(a.jobs) as pool:
            futs = [pool.submit(one, m) for m in plan]
            for f in as_completed(futs):
                f.result()
        run.meta.setdefault("runs", []).append({
            "finished": time.strftime("%Y-%m-%d %H:%M:%S"), "mutants": counter["n"],
            "wall_s": round(time.monotonic() - t0), "jobs": a.jobs,
            "inputs_unchanged": input_hashes() == run.meta["inputs_at_prepare"],
            "aborted": abort.is_set()})
    snap = jload(run.dir / "data_snapshot_prepare.json", {})
    now = data_snapshot()
    changed = sorted(k for k in set(snap) | set(now) if snap.get(k) != now.get(k))
    run.meta["runs"][-1]["data_changed_since_prepare"] = changed[:50]
    run.save_meta()
    if changed:
        print(f"  ! {len(changed)} files under data/ changed since prepare "
              f"(another writer, or a leak): {changed[:5]}")
    return cmd_report(a)


# --------------------------------------------------------------------------
# report
# --------------------------------------------------------------------------

def cmd_report(a) -> int:
    run = Run(a.run)
    idx = Index(run)
    results = {}
    for r in jlines(run.dir / "results.jsonl"):
        results[r["id"]] = r  # last write wins
    rows = list(results.values())
    meta = run.meta
    by_id = {m["id"]: m for mod in meta["modules"] for m in run.mutants(mod)}
    for r in rows:
        m = by_id.get(r["id"])
        if m is None:
            continue
        ex = idx.executing(m)
        r["executing"] = len(ex)
        r["excluded_reaching"] = sorted(t for t in idx.reaching(m)
                                        if not idx.usable(t, m["file"]))
    by_mod = defaultdict(list)
    for r in rows:
        by_mod[r["file"]].append(r)
    L = []
    w = L.append
    meta = run.meta
    w(f"# Mutation survivor report — {run.dir.name}\n")
    w(f"HEAD `{meta['head'][:10]}` · prepared {meta.get('prepared')} · "
      f"{meta['city']} {meta['target']}, seed {meta['seed']}, {meta['draws']} draws · "
      f"python {meta['python']}, PYTHONHASHSEED={meta['hash_seed']}\n")
    for rr in meta.get("runs", []):
        w(f"- run finished {rr['finished']}: {rr['mutants']} mutants in "
          f"{rr['wall_s'] / 60:.1f} min at {rr['jobs']} jobs; inputs unchanged: "
          f"{rr['inputs_unchanged']}; data/ files changed since prepare: "
          f"{len(rr.get('data_changed_since_prepare', []))}; aborted: {rr['aborted']}")
    if (run.dir / "ABORTED").exists():
        w(f"\n**ABORTED:** {(run.dir / 'ABORTED').read_text().strip()}\n")
    w("\n## Outcome per module\n")
    w("Classes: KILLED — a selected test failed · MOVED-UNTESTED — a `*draws` array "
      "moved and no selected test failed · INERT — no selected test failed and no "
      "`*draws` array moved (`reached`: the model or a selected test executes the "
      "line; `unreached`: neither does) · TIMEOUT · CRASH — the model or the test "
      "process died and no test failed.\n")
    w("| module | population | run | KILLED | MOVED-UNTESTED | INERT reached | INERT unreached | TIMEOUT | CRASH | s per mutant, median / p90 (both stages, one worker) |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for mod in meta["modules"]:
        rs = by_mod.get(mod, [])
        c = Counter(r["class"] for r in rs)
        inert_r = sum(1 for r in rs if r["class"] == "INERT" and _reached(r))
        inert_u = c["INERT"] - inert_r
        secs = sorted(r["s"] + (r.get("s_stage1") or 0) for r in rs)
        med = secs[len(secs) // 2] if secs else 0
        p90 = secs[int(len(secs) * 0.9)] if secs else 0
        pop = meta.get("sampling", {}).get(mod, {}).get("population", len(run.mutants(mod)))
        w(f"| `{mod}` | {pop} | {len(rs)} | {c['KILLED']} | {c['MOVED-UNTESTED']} | "
          f"{inert_r} | {inert_u} | {c['TIMEOUT']} | {c['CRASH']} | {med:.1f} / {p90:.1f} |")
    samp = {k: v for k, v in meta.get("sampling", {}).items() if v.get("sampled")}
    if samp:
        w("\n**Sampled modules** (stratified by function × operator):")
        for k, v in samp.items():
            w(f"- `{k}`: {v['chosen']} of {v['population']}, seed {v['seed']}")
    # population
    w("\n## Population: what the fixed-seed run executes\n")
    w("Every `src/` module with at least one line executed by the baseline "
      "`run_model` (table and parse mode together), and whether it is mutated "
      "in this run. A module on this list and not in the population is forecast "
      "path this run did not mutate.\n")
    w("| module | lines executed by run_model | in this run's population |")
    w("|---|---|---|")
    for f in sorted(idx.model_lines, key=lambda f: -len(idx.model_lines[f])):
        w(f"| `{f}` | {len(idx.model_lines[f])} | {'yes' if f in meta['modules'] else 'no'} |")
    # controls
    w("\n## Controls\n")
    bm = meta.get("baseline_model", {})
    w(f"- Baseline model: {len(bm.get('fields', []))} `*draws` fields "
      f"({', '.join(bm.get('fields', []))}); two table-mode runs identical: "
      f"{not bm.get('table_twice_differs')}; table mode == parse mode: "
      f"{not bm.get('table_vs_parse_differs')}.")
    w("- Comparator positive controls: `night.py selftest`.")
    for n in jlines(run.dir / "baseline" / "nulls.jsonl"):
        w(f"- Null mutant of `{n['file']}`: model {n['model']['status']}; "
          f"tests failing on ANY edit of this file (excluded from its subsets): "
          f"{', '.join(n.get('failed') or []) or 'none'}")
    moved_any = defaultdict(int)
    for r in rows:
        if r["model"]["status"] == "moved":
            moved_any[r["file"]] += 1
    w("- Mutants whose `*draws` moved, per module, killed or not (the detector "
      "sees real moves): " + (", ".join(f"`{k}` {v}" for k, v in sorted(moved_any.items()))
                              or "none"))
    # exclusions
    w("\n## Tests not run per mutant\n")
    ex = defaultdict(list)
    for tid, why in idx.excluded.items():
        ex[why.split(":")[0]].append((tid, why))
    for kind, items in sorted(ex.items()):
        w(f"**{kind}** ({len(items)}):")
        for tid, why in sorted(items)[:80]:
            w(f"- `{tid}` — {why}")
        if len(items) > 80:
            w(f"- … {len(items) - 80} more (report.json)")
    if idx.unreliable:
        w(f"**fail alone on the pristine tree** (found during the run, excluded thereafter): "
          + ", ".join(f"`{t}`" for t in sorted(idx.unreliable)))
    static_names = set(STATIC_EXCLUDE)
    sandbox_failed = {t for t, r in idx.tests.items() if r["status"] != "pass"}
    stat_pass = sorted(t for t in idx.tests if (t in static_names or t.split("::")[0] in static_names)
                       and idx.tests[t]["status"] == "pass")
    if stat_pass:
        w(f"\nStatically excluded but PASSED in the sandbox at baseline "
          f"(they wrote nothing the sandbox refused, or skipped): {len(stat_pass)} — "
          + ", ".join(f"`{t}`" for t in stat_pass[:30]))
    # survivors
    w("\n## Survivors, by file and function\n")
    w("Every INERT and MOVED-UNTESTED mutant (and TIMEOUT/CRASH, which no test "
      "noticed either). `model`: what the fixed-seed run did (`not-executed` = the "
      "run never reaches the line). `tests`: run / selected / reaching before "
      "exclusions (scan readers of the file included); † = stage 1 ran only the "
      "cheapest of the selected tests, and the mutant still owes a stage-2 run of "
      "the rest. `executed by`: how many tests' baseline coverage executes the "
      "mutated code, as opposed to reading the file as text.\n")
    src_lines = {mod: (run.pristine / mod).read_text().splitlines()
                 for mod in meta["modules"] if (run.pristine / mod).exists()}
    for mod in meta["modules"]:
        surv = [r for r in by_mod.get(mod, []) if r["class"] != "KILLED"]
        if not surv:
            continue
        w(f"### `{mod}`\n")
        byf = defaultdict(list)
        for r in surv:
            byf[r["func"]].append(r)
        for func in sorted(byf, key=lambda f: min(r["line"] for r in byf[f])):
            w(f"**{func}**\n")
            w("| line | source | op | mutation | class | model | tests | executed by |")
            w("|---|---|---|---|---|---|---|---|")
            for r in sorted(byf[func], key=lambda r: (r["line"], r["op"])):
                mo = r["model"]
                ms = mo["status"] + (f" ({mo['mode']})" if mo.get("executed") and mo["mode"] == "parse" else "")
                if mo.get("moved_fields"):
                    ms += ": " + ", ".join(mo["moved_fields"])
                t = r["tests"]
                cls = r["class"] + ("" if r["class"] != "INERT" else
                                    (" reached" if _reached(r) else " unreached"))
                ran = len(t.get("ran_ids", []))
                mark = "" if t.get("complete", True) else " †"
                srcline = MU._short(src_lines.get(mod, [""] * (r["line"] + 1))[r["line"] - 1], 60)
                w(f"| {r['line']} | `{srcline.replace('|', '¦').replace('`', chr(39))}` | "
                  f"{r['op']} | {r['desc'].replace('|', '¦')} | {cls} | "
                  f"{ms} | {ran}/{t.get('selected', 0)}/{t.get('reaching', 0)}{mark} | "
                  f"{r.get('executing', 0)} |")
            exr = sorted({t for r in byf[func] for t in r.get("excluded_reaching", [])})
            if exr:
                w("Reaching tests NOT run for these mutants (excluded; see above): "
                  + ", ".join(f"`{t}`" for t in exr[:12])
                  + (f" … {len(exr) - 12} more" if len(exr) > 12 else ""))
            w("")
    (run.dir / "report.md").write_text("\n".join(L) + "\n")
    (run.dir / "report.json").write_text(json.dumps({
        "meta": meta, "results": rows,
        "excluded": idx.excluded, "unreliable": sorted(idx.unreliable)}, indent=1))
    print(f"wrote {run.dir / 'report.md'}")
    return 0


def cmd_estimate(a) -> int:
    """Cost of a night over `--modules`, from a finished pilot's measurements.

    Upper bounds come from the pilot's baseline (model time plus the baseline
    seconds of every usable reaching test, per mutant); the pilot's own
    measured/upper-bound ratio per stage turns them into expected core-hours,
    and its measured parallelism (summed seconds / wall) into wall hours. A
    module whose kill rate differs from the pilot's will differ from this."""
    run = Run(a.run)
    idx = Index(run)
    allr = jlines(run.dir / "results.jsonl")
    by = {m["id"]: m for mod in run.meta["modules"] for m in run.mutants(mod)}
    s1 = [r for r in allr if r.get("stage") == 1 and r["id"] in by]
    s2 = [r for r in allr if r.get("stage") == 2 and r["id"] in by]
    if not s1:
        raise SystemExit("the pilot has no stage-1 results")
    ub1 = sum(_estimate(idx, by[r["id"]], a.test_budget) for r in s1)
    ubf = sum(_estimate(idx, by[r["id"]], 0) for r in s1)
    got1 = sum(r["s"] for r in s1)
    gotf = got1 + sum(r["s"] for r in s2)
    k1, kf = got1 / ub1, gotf / ubf
    walls = [x["wall_s"] for x in run.meta.get("runs", [])]
    par = (gotf / sum(walls)) if walls else a.jobs
    print(f"pilot: stage 1 measured/upper bound {k1:.3f}; both stages {kf:.3f}; "
          f"parallelism measured {par:.1f} at the pilot's jobs")
    print(f"| module | mutants | stage 1 core-h | stage 1 wall h | full core-h | full wall h |")
    print("|---|---|---|---|---|---|")
    T1 = TF = 0.0
    for mod in a.modules or DEFAULT_MODULES:
        path = run.pristine / mod
        if not path.exists():
            print(f"| `{mod}` | not in the tree | | | | |")
            continue
        ms = MU.enumerate_mutants(path.read_text(), mod)
        e1 = sum(_estimate(idx, m, a.test_budget) for m in ms) * k1 / 3600
        ef = sum(_estimate(idx, m, 0) for m in ms) * kf / 3600
        T1 += e1
        TF += ef
        print(f"| `{mod}` | {len(ms)} | {e1:.1f} | {e1 / par:.1f} | {ef:.1f} | {ef / par:.1f} |",
              flush=True)
    print(f"| total | | {T1:.1f} | {T1 / par:.1f} | {TF:.1f} | {TF / par:.1f} |")
    return 0


def _reached(r: dict) -> bool:
    """The model run or at least one test EXECUTES the line (a test that only
    reads the file as text does not count)."""
    return bool(r["model"].get("executed")) or r.get("executing", 0) > 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("selftest")
    p = sub.add_parser("prepare")
    p.add_argument("--run", required=True)
    p.add_argument("--modules", nargs="*")
    p.add_argument("--city", default="joburg")
    p.add_argument("--target", default="2026")
    p.add_argument("--draws", type=int, default=20)
    p.add_argument("--seed", type=int, default=20261104)
    p.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--max-test-s", type=float, default=120.0)
    p.add_argument("--redo", action="store_true", help="retake every baseline")
    p.add_argument("--redo-tests", action="store_true", help="retake the test baseline")
    r = sub.add_parser("run")
    r.add_argument("--run", required=True)
    r.add_argument("--modules", nargs="*")
    r.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    r.add_argument("--budget-hours", type=float, default=0.0,
                   help="per-module wall budget; a module estimated over it is sampled")
    r.add_argument("--sample-seed", type=int, default=1)
    r.add_argument("--limit", type=int, default=0)
    r.add_argument("--control-every", type=int, default=150)
    r.add_argument("--test-budget", type=float, default=0.0,
                   help="stage 1: per mutant, run only the cheapest reaching tests "
                        "up to this many baseline seconds (0 = all of them)")
    r.add_argument("--stage2", action="store_true",
                   help="finish survivors whose reaching tests stage 1 did not all run")
    q = sub.add_parser("report")
    q.add_argument("--run", required=True)
    e = sub.add_parser("estimate")
    e.add_argument("--run", required=True, help="a finished pilot run")
    e.add_argument("--modules", nargs="*")
    e.add_argument("--test-budget", type=float, default=60.0)
    e.add_argument("--jobs", type=int, default=7)
    a = ap.parse_args(argv)
    return {"selftest": cmd_selftest, "prepare": cmd_prepare, "run": cmd_run,
            "report": cmd_report, "estimate": cmd_estimate}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
