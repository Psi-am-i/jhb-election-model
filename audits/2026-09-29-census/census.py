"""F10 mechanism census: the harness. Claims are in CLAIMS.md, written first.

    .venv/bin/python audits/2026-09-29-census/census.py selftest
    .venv/bin/python audits/2026-09-29-census/census.py run --out <dir> [--only C1-off ...]

Each mutation is an EXACT source edit (asserted to match once) applied to a
scratch copy of `src/` and `tests/`, inside a scratch root that mirrors the
repository: every other top-level entry symlinked, `data/processed` an APFS
clone, other `data/` entries symlinked. In that root, in fresh processes
(`probe.py`), the fixture's spec is emitted, the model is run with a full
trace, and the named test modules are run. The base is the same with no
edit. Nothing under the real `data/` is written.

A `pools.py` edit moves `pools_sha`, which would make every spec in the clone
look stale to `test_chain`'s current-key test (R3 fix check N3). Each root's
clone has its specs' `pools_sha` set to that root's own code hash, and a
CONTROL mutant (an inert code edit) shows the test runs are not confounded.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PY = str(ROOT / ".venv/bin/python")

STAGES = ("00_target", "01_scenario_in", "02_pools_artefact", "03_roster",
          "10_theta_prior", "20_spine", "30_centres", "40_draws", "41_guards",
          "42_pr_share_draws", "43_ward_share_draws", "44_seat_draws",
          "45_delivered")
# `path` differs by construction; `artefact_key` and `stale_reason` carry the
# code hash, which a source edit moves by construction (R3 F1).
IGNORED_KEYS = ("path", "artefact_key", "stale_reason")
TEST_MODULES = ("pool_bounds", "pool_conservation", "roster_aware_baseline",
                "theta", "chain")

B = ("mangaung", "2016")
J = ("joburg", "2026")
P, M, T = "src/pools.py", "src/montecarlo.py", "src/theta_residual.py"

# Flags added to pools.py for the run-time-only mutations (C4).
FLAGS = (P, "class HoldCascadeRefused(ValueError):",
         "_CENSUS_HOLD_OFF = False\n_CENSUS_HOLD_SCALE = 1.0\n\n\n"
         "class HoldCascadeRefused(ValueError):")
HOLD_OFF = (P, "    silenced = _silent_pools(parent, rate)\n    if silenced:",
            "    silenced = ({} if _CENSUS_HOLD_OFF\n"
            "                else _silent_pools(parent, rate))\n    if silenced:")
HOLD_SCALE = (P, "        fallback = _uninformed_rate(parent, observed)",
              "        fallback = _CENSUS_HOLD_SCALE * _uninformed_rate(parent, observed)")
RUNTIME_OLD = '            _counts = _pools.pool_counts(target.city, spec["fitted_on"], _cfg)'


def _runtime(flag, value, reset):
    return (M, RUNTIME_OLD,
            f"            _pools.{flag} = {value}\n{RUNTIME_OLD}\n"
            f"            _pools.{flag} = {reset}")


C3_OLD = "        if not members:\n            # ⛔ REFUSED, NOT SKIPPED"
C3_NEW = "        if not members:\n            continue\n            # ⛔ REFUSED, NOT SKIPPED"
C1_OFF = (P, "    silenced = _silent_pools(parent, rate)\n    if silenced:",
          "    silenced = {}\n    if silenced:")

MUTANTS: dict[str, dict] = {
    "CONTROL": {"fix": [B, J], "edits": [
        (P, "_RATE_BOUND_EPS = 1e-6\n", "_RATE_BOUND_EPS = 1e-6\n_CENSUS_CONTROL = 0\n")]},
    "C1-off": {"fix": [B], "edits": [C1_OFF]},
    "C1-nudge": {"fix": [B], "edits": [
        (P, "        fallback = _uninformed_rate(parent, observed)",
         "        fallback = 1.10 * _uninformed_rate(parent, observed)")]},
    "C1-guard": {"fix": [B, J], "edits": [
        (P, "            if populated <= set(silenced):",
         "            if False and populated <= set(silenced):")]},
    "C2-off": {"fix": [B, J], "edits": [
        (P, "            if not cascade:\n                break", "            break")]},
    "C3-guard": {"fix": [B], "edits": [(P, C3_OLD, C3_NEW)]},
    "C3-guard+C1-off": {"fix": [B], "tests": False,
                        "edits": [(P, C3_OLD, C3_NEW), C1_OFF]},
    "C4-off": {"fix": [B], "tests": False, "edits": [
        FLAGS, HOLD_OFF, _runtime("_CENSUS_HOLD_OFF", "True", "False")]},
    "C4-nudge": {"fix": [B], "tests": False, "edits": [
        FLAGS, HOLD_SCALE, _runtime("_CENSUS_HOLD_SCALE", "1.10", "1.0")]},
    "C9-off": {"fix": [B, J], "spread": True, "edits": [
        (P, "                if i in ia or j in ib:\n                    continue\n", "")]},
    "C5-off": {"fix": [J], "edits": [
        (M, "    base_city_d, base_share_d, _mergers = _pools_merge.apply_mergers(\n"
            "        base_city_d, _roster, target.year, per_vd=base_share_d)",
         "    _mergers = []")]},
    "C5-nudge": {"fix": [J], "tests": False, "edits": [
        (P, "MERGER_RETENTION = 0.75", "MERGER_RETENTION = 0.85")]},
    "C5-guard": {"fix": [J], "edits": [
        (P, "            raise MergerRefused(", "            MergerRefused(")]},
    "C6-off": {"fix": [J], "edits": [
        (M, "    prior_pr_share, _, _ = _pools_merge.apply_mergers(pc, _roster, target.year)",
         "    prior_pr_share = pc")]},
    "C6-guard": {"fix": [J], "edits": [
        (P, "        if out.get(successor, 0.0) <= 0.0:\n"
            "            continue            # no record to add to; never create one\n", ""),
        (P, "            out[successor] = out[successor] + moved",
         "            out[successor] = out.get(successor, 0.0) + moved")]},
    "C7-off": {"fix": [J], "edits": [
        (P, "    blend_merger_vectors(composition, pre_merger_baseline, merger_vectors,\n"
            "                         mergers_applied)",
         "    for _m in mergers_applied:\n        _m[\"vector_blended\"] = False")]},
    "C7-nudge": {"fix": [J], "tests": False, "edits": [
        (P, "composition[succ], held, merger_vectors[pred], m[\"moved\"])",
         "composition[succ], held, merger_vectors[pred], 2 * m[\"moved\"])")]},
    "C7-guard": {"fix": [J], "edits": [
        (P, "        held = mass.get(succ, pre_merger_baseline.get(succ, 0.0))",
         "        held = pre_merger_baseline.get(succ, 0.0)")]},
    "C8-off": {"fix": [], "c8": True, "edits": [
        (T, "            before, _, _ = pools.apply_mergers(before, _roster, year)\n", "")]},
    "C10-off": {"fix": [J], "edits": [
        (P, "            if vds is not None:\n                for s in vds.values():",
         "            if False:\n                for s in vds.values():")]},
}


# --------------------------------------------------------------------------
# Scratch roots
# --------------------------------------------------------------------------

def apply_edits(text_by_file: dict[str, str], edits) -> dict[str, str]:
    """Each edit's old text must occur exactly once in its file."""
    out = dict(text_by_file)
    for f, old, new in edits:
        n = out[f].count(old)
        if n != 1:
            raise SystemExit(f"edit on {f} matches {n} times, not once:\n{old}")
        out[f] = out[f].replace(old, new)
    return out


ENV = {"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin", "HOME": str(Path.home())}


def make_root(where: Path, edits) -> Path:
    root = where / "root"
    if root.exists():
        shutil.rmtree(root)
    (root / "data").mkdir(parents=True)
    for e in ROOT.iterdir():
        if e.name not in ("data", ".git", "src", "tests"):
            (root / e.name).symlink_to(e)
    shutil.copytree(ROOT / "src", root / "src",
                    ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "tests", root / "tests",
                    ignore=shutil.ignore_patterns("__pycache__"))
    for e in (ROOT / "data").iterdir():
        if e.name != "processed":
            (root / "data" / e.name).symlink_to(e)
    subprocess.run(["cp", "-Rc", str(ROOT / "data/processed"),
                    str(root / "data/processed")], check=True)
    files = {f for f, _, _ in edits}
    texts = apply_edits({f: (root / f).read_text() for f in files}, edits)
    for f, t in texts.items():
        (root / f).write_text(t)
    sha = subprocess.run(
        [PY, "-c", "import sys; sys.path.insert(0,'src'); import pools; "
                   "from pathlib import Path; "
                   "print(pools._code_sha(Path('src/pools.py')))"],
        cwd=root, capture_output=True, text=True, check=True, env=ENV).stdout.strip()
    for sp in (root / "data/processed").rglob("pools_*.json"):
        d = json.loads(sp.read_text())
        if isinstance(d.get("artefact_key"), dict):
            d["artefact_key"]["pools_sha"] = sha
            sp.write_text(json.dumps(d, indent=2, sort_keys=True))
    return root


def probe(root: Path, *args) -> None:
    r = subprocess.run([PY, str(HERE / "probe.py"), *map(str, args)],
                       cwd=root, env=ENV, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"probe {args} failed in {root}:\n{r.stderr[-2000:]}")


def run_tests(root: Path, out: Path) -> dict:
    args = [PY, "tests/run_all.py"]
    for m in TEST_MODULES:
        args += ["-k", m]
    r = subprocess.run(args, cwd=root, capture_output=True, text=True, env=ENV)
    (out / "tests.txt").write_text(r.stdout + r.stderr)
    fails = sorted({ln.split()[1] for ln in r.stdout.splitlines()
                    if ln.startswith("FAIL ")})
    return {"failed": fails}


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------

def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in IGNORED_KEYS}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def stage(trace: Path, name: str):
    p = trace / f"{name}.json"
    return _strip(json.loads(p.read_text())) if p.exists() else None


def first_changed(base: Path, mut: Path) -> dict:
    changed = [s for s in STAGES if stage(base, s) != stage(mut, s)]
    present = [s for s in STAGES if (base / f"{s}.json").exists()]
    return {"first": changed[0] if changed else None, "changed": changed,
            "compared": present}


def spec_fields(base: dict, mut: dict) -> list[str]:
    b = {k: v for k, v in base.items() if k != "artefact_key"}
    m = {k: v for k, v in mut.items() if k != "artefact_key"}
    return sorted(k for k in set(b) | set(m) if b.get(k) != m.get(k))


# --------------------------------------------------------------------------
# One mutant, end to end
# --------------------------------------------------------------------------

def run_one(name: str, spec: dict, out: Path, scratch: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    root = make_root(scratch / name, spec["edits"])
    res: dict = {"name": name}
    for slug, year in spec["fix"]:
        d = out / f"{slug}-{year}"
        probe(root, "emit", slug, year, d)
        if not (d / "emit_refused.txt").exists():
            probe(root, "run", slug, year, d)
    if spec.get("c8"):
        probe(root, "c8", out / "c8")
    if spec.get("spread"):
        probe(root, "spread", out / "spread")
    if spec.get("tests", True):
        res["tests"] = run_tests(root, out)
    shutil.rmtree(scratch / name, ignore_errors=True)
    return res


def compare(base_out: Path, mut_out: Path, spec: dict) -> dict:
    r = {}
    for slug, year in spec["fix"]:
        b, m = base_out / f"{slug}-{year}", mut_out / f"{slug}-{year}"
        one: dict = {}
        if (m / "emit_refused.txt").exists():
            one["emit_refused"] = (m / "emit_refused.txt").read_text()[:400]
        else:
            one["spec_fields_changed"] = spec_fields(
                json.loads((b / "spec.json").read_text()),
                json.loads((m / "spec.json").read_text()))
            if (m / "run_failed.txt").exists():
                one["run_failed"] = (m / "run_failed.txt").read_text()[:400]
            else:
                one["trace"] = first_changed(b / "trace", m / "trace")
        r[f"{slug}-{year}"] = one
    if spec.get("c8"):
        bb = json.loads((base_out / "c8" / "c8.json").read_text())
        mm = json.loads((mut_out / "c8" / "c8.json").read_text())
        r["c8"] = {"predecessor": bb["predecessor"],
                   "base_K_differs_from_real": bb["rows"]["K"] != bb["rows"]["real"],
                   "mutant_K_equals_real": mm["rows"]["K"] == mm["rows"]["real"],
                   "real_rows_identical": bb["rows"]["real"] == mm["rows"]["real"]}
    if spec.get("spread"):
        bb = json.loads((base_out / "spread" / "spread.json").read_text())
        mm = json.loads((mut_out / "spread" / "spread.json").read_text())
        r["spread"] = {y: {"changed_pools": sorted(
            k for k in set(bb[y]["spread"]) | set(mm[y]["spread"])
            if bb[y]["spread"].get(k) != mm[y]["spread"].get(k)),
            "n": [bb[y]["n"], mm[y]["n"]]} for y in bb}
    return r


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------

def selftest() -> None:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for name in ("a", "b"):
            (d / name).mkdir()
            for s in STAGES:
                (d / name / f"{s}.json").write_text(
                    json.dumps({"v": 1, "path": f"/{name}",
                                "artefact_key": {"pools_sha": name}}))
        assert first_changed(d / "a", d / "b")["first"] is None, \
            "a path- or key-only difference was read as a change"
        (d / "b" / "20_spine.json").write_text(json.dumps({"v": 2}))
        assert first_changed(d / "a", d / "b")["first"] == "20_spine"
    try:
        apply_edits({"f": "x x"}, [("f", "x", "y")])
    except SystemExit:
        pass
    else:
        raise AssertionError("an edit matching twice was applied")
    texts = {f: (ROOT / f).read_text() for f in (P, M, T)}
    for name, spec in MUTANTS.items():
        apply_edits(texts, spec["edits"])
    print(f"selftest: comparison sees a change; all {len(MUTANTS)} mutants "
          f"apply exactly once to the current tree")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("selftest", "run"))
    ap.add_argument("--out", type=Path)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        selftest()
        return 0
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="census-"))
    names = a.only or list(MUTANTS)
    base = {"fix": sorted({f for n in names for f in MUTANTS[n]["fix"]}),
            "edits": [], "c8": any(MUTANTS[n].get("c8") for n in names),
            "spread": any(MUTANTS[n].get("spread") for n in names)}
    if not (out / "base" / "done.json").exists():
        rb = run_one("base", base, out / "base", scratch)
        (out / "base" / "done.json").write_text(json.dumps(rb))
    base_fail = set(json.loads((out / "base" / "done.json").read_text())
                    .get("tests", {}).get("failed", []))
    results = {}
    for n in names:
        mdir = out / n
        if (mdir / "result.json").exists():
            results[n] = json.loads((mdir / "result.json").read_text())
            continue
        r = run_one(n, MUTANTS[n], mdir, scratch)
        r["compare"] = compare(out / "base", mdir, MUTANTS[n])
        if "tests" in r:
            r["new_test_failures"] = sorted(set(r["tests"]["failed"]) - base_fail)
        (mdir / "result.json").write_text(json.dumps(r, indent=1))
        results[n] = r
        print(n, json.dumps(r["compare"])[:500], r.get("new_test_failures"),
              flush=True)
    (out / "results.json").write_text(json.dumps(results, indent=1))
    shutil.rmtree(scratch, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
