"""F10 mechanism census: the harness. Claims are in CLAIMS.md, written first.

    .venv/bin/python audits/2026-09-29-census/census.py selftest
    .venv/bin/python audits/2026-09-29-census/census.py run --out <dir>

Writes nothing under `data/`. Each run works on an APFS clone of
`data/processed` in a scratch directory, builds any mutated spec in process
(`pools.emit_pools`, lineage template stubbed), writes it into the clone, and
calls `montecarlo.run_model` with `processed=<clone>` and a `run_dir` trace.
A mutation is compared with the unmutated run at the same seed, stage by
stage; `path` fields are ignored because the clone's path differs by
construction.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

SEED = 20261104
DRAWS = 300
STAGES = ("00_target", "01_scenario_in", "02_pools_artefact", "03_roster",
          "10_theta_prior", "20_spine", "30_centres", "40_draws", "41_guards",
          "42_pr_share_draws", "43_ward_share_draws", "44_seat_draws",
          "45_delivered")
IGNORED_KEYS = ("path",)


# --------------------------------------------------------------------------
# Patching
# --------------------------------------------------------------------------

@contextlib.contextmanager
def patched(*triples):
    """Set ``(obj, attr, value)`` for the duration, and restore it."""
    saved = [(o, a, getattr(o, a)) for o, a, _ in triples]
    try:
        for o, a, v in triples:
            setattr(o, a, v)
        yield
    finally:
        for o, a, v in reversed(saved):
            setattr(o, a, v)


# --------------------------------------------------------------------------
# Specs and runs
# --------------------------------------------------------------------------

def make_root(scratch: Path) -> Path:
    """A scratch repository root: every top-level entry of ROOT symlinked,
    except `data/`, whose `processed/` is an APFS clone (copy-on-write) and
    whose other entries are symlinked. The model resolves `data/processed`
    against the working directory (`cityconfig.City.processed`), so a run
    made from this root reads the clone and writes nothing in ROOT's `data/`.
    Returns the clone's `data/processed`."""
    root = scratch / "root"
    if root.exists():
        shutil.rmtree(root)
    (root / "data").mkdir(parents=True)
    for entry in ROOT.iterdir():
        if entry.name not in ("data", ".git"):
            (root / entry.name).symlink_to(entry)
    for entry in (ROOT / "data").iterdir():
        if entry.name != "processed":
            (root / "data" / entry.name).symlink_to(entry)
    subprocess.run(["cp", "-Rc", str(ROOT / "data/processed"),
                    str(root / "data/processed")], check=True)
    return root / "data/processed"


@contextlib.contextmanager
def inside(processed: Path):
    """Run with the scratch root (the clone's grandparent) as cwd."""
    import os
    here = os.getcwd()
    os.chdir(processed.parent.parent)
    try:
        yield
    finally:
        os.chdir(here)


def spec_path(processed: Path, slug: str, year: str) -> Path:
    return (processed if slug == "joburg" else processed / slug) / f"pools_{year}.json"


def write_spec(processed: Path, slug: str, year: str, spec: dict) -> None:
    """Exactly as `emit_pools` writes it (`indent=2, sort_keys=True`). The
    draw follows the members' key order, so a spec written unsorted draws
    differently from the same spec on disk (found building this harness)."""
    spec_path(processed, slug, year).write_text(
        json.dumps(spec, indent=2, sort_keys=True))


def emit_spec(slug: str, year: str) -> dict:
    """`pools.emit_pools` in process, with the lineage template stubbed so
    nothing under `judgements/` or `data/` is written. Keeps `artefact_key`,
    so the run does not refuse the spec as stale."""
    import cityconfig
    import pools
    city = cityconfig.use(slug)
    target = cityconfig.use_target(year)
    with patched((pools, "write_lineage_template",
                  lambda c, t, *a, **k: pools.lineage_path(c, t))):
        with contextlib.redirect_stdout(io.StringIO()):
            return pools.emit_pools(city, target, pools.load_config())


def run(slug: str, year: str, processed: Path, run_dir: Path,
        draws: int = DRAWS, seed: int = SEED):
    """One traced model run, set up as `compare_history.run_city_year` does."""
    import cityconfig
    import montecarlo as M
    city = cityconfig.use(slug)
    target = cityconfig.use_target(year)
    M.apply_city(city)
    scenario = M.load_scenario(argparse.Namespace(
        config=None, set=[f"seed={seed}"], draws=draws, seed=None,
        city=slug, target=year))
    with inside(processed), contextlib.redirect_stdout(io.StringIO()):
        out = M.run_model(target, scenario, Path("data/raw/elections"),
                          verbose=False, run_dir=run_dir)
    return out, scenario


# --------------------------------------------------------------------------
# Stage comparison
# --------------------------------------------------------------------------

def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in IGNORED_KEYS}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def stage(run_dir: Path, name: str):
    p = run_dir / f"{name}.json"
    return _strip(json.loads(p.read_text())) if p.exists() else None


def first_changed(base: Path, mut: Path) -> dict:
    """The first stage whose JSON differs, and every stage that differs."""
    changed = [s for s in STAGES if stage(base, s) != stage(mut, s)]
    return {"first": changed[0] if changed else None, "changed": changed}


# --------------------------------------------------------------------------
# Self-test: the comparison sees a change, and only where it is
# --------------------------------------------------------------------------

def selftest() -> None:
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        for name in ("a", "b"):
            (d / name).mkdir()
            for s in STAGES:
                (d / name / f"{s}.json").write_text(
                    json.dumps({"v": 1, "path": f"/{name}"}))
        assert first_changed(d / "a", d / "b")["first"] is None, \
            "a path-only difference was read as a change"
        (d / "b" / "20_spine.json").write_text(json.dumps({"v": 2, "path": "/b"}))
        r = first_changed(d / "a", d / "b")
        assert r == {"first": "20_spine", "changed": ["20_spine"]}, r
        (d / "b" / "20_spine.json").write_text(json.dumps({"v": 1, "path": "/b"}))
        assert first_changed(d / "a", d / "b")["first"] is None
    print("selftest: the stage comparison sees a change and goes quiet")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("selftest", "run"))
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        selftest()
        return 0
    raise SystemExit("the mutations are defined after R3 (CLAIMS.md)")


if __name__ == "__main__":
    sys.exit(main())
