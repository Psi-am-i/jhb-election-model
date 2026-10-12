"""THE THREE PROVENANCE GATES, AND WHETHER THEY CARRY ANY INFORMATION.

Each of these modules answers a question about where a number came from, and on
2026-09-14 each answered it in a way that could not be wrong:

* ``src/declares.py --verify`` — the command CLAUDE.md sends every session
  through *"before quoting or believing any number"* — **failed OPEN from the
  wrong working directory** (``PROCESSED`` was relative, and ``rglob`` on a
  missing directory yields nothing rather than raising, so it printed the
  all-clear over a population of zero) and **could never exit 0 from the right
  one** (``forecast_frozen.json`` is committed, ``freeze`` deliberately writes
  no timestamp, ``Row.worst`` is the worst cell, and ``--verify`` failed on
  ``worst``). Both outcomes were uninformative.

* ``src/overhang_regimes.py`` wrote three counterfactual councils through the
  **published** forecast's own files and restored them with a bare statement at
  the end of the function. ``level``, the second of the three, raises
  ``RuntimeError`` BY DESIGN (montecarlo.py:3234), and any raise skipped the
  restore.

* ``src/compare_history.py``'s manifest declared ``M.DEFAULTS["seed"]`` — a
  module global ``apply_city`` rewrites on every city-year — as "the seed every
  city-year actually ran at", and ``_archive_targets`` swallowed the exception
  that shrinks the panel denominator it is the sole source of.

⛔ EVERY TEST HERE FOLLOWS CLAUDE.md §4's FOUR PARTS, and the third and fourth
are the ones that get skipped: a constructed violation must be CAUGHT, and the
detector must GO QUIET when it is reverted. A guard that fires on the broken
tree and also on the fixed one has not been shown to measure anything.

⚠️ AND THE INPUTS ARE CONSTRUCTED, NOT OBSERVED. Nothing here asserts about the
repository's live ``data/processed``: it is gitignored, it moves under other
agents, and a test whose premise is a passing tree expires in silence. The
artefact trees are built in ``tempfile`` directories, the failures are injected,
and ``montecarlo`` is never run.
"""
from __future__ import annotations

import ast
import filecmp
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
sys.path.insert(0, str(SRC))

import compare_history as C                                    # noqa: E402
import declares as D                                           # noqa: E402
import freeze as F                                             # noqa: E402
import pools                                                   # noqa: E402


# ==========================================================================
# declares.py — the gate
# ==========================================================================

def _honest_tree(root: Path) -> dict:
    """A complete, truthful artefact tree. THE POSITIVE CONTROL.

    ⛔ A GATE THAT HAS NEVER BEEN SHOWN TO PASS HAS NOT BEEN SHOWN TO
    DISTINGUISH ANYTHING. `--verify` returned 1 on every tree that could exist,
    so "it exits 1" was evidence of nothing whatever about the tree. Building
    the passing case is what makes the failing cases mean something.
    """
    key = {"pools_sha": pools._code_sha(Path(pools.__file__)),
           "config_sha": "c", "cities_sha": "ci", "city": "joburg",
           "target": "2021", "deps_sha": "d", "judgements_sha": "j"}
    head = F._git("rev-parse", "HEAD")
    root.mkdir(parents=True, exist_ok=True)
    (root / "pools_2021.json").write_text(json.dumps({"artefact_key": key}))
    (root / "history.json").write_text(json.dumps({"manifest": {
        "git_commit": head, "git_dirty": False, "draws": 10, "seed": 1,
        "env_switches": {"A": "1"}, "generated": "2026-01-01T00:00:00Z",
        "population": {"scored": ["joburg:2021"]},
        "pool_artefact_keys": {"joburg": {"2021": key}}}, "records": []}))
    (root / "forecast_summary.json").write_text(json.dumps({
        "_generated": "2026-01-01T00:00:00Z", "_draws": 10,
        "scenario": {"_pools_artefact_key": key}}))
    (root / "forecast_frozen.json").write_text(json.dumps({
        "content": {"draws": 10, "seed": 1, "env_switches": {"A": "1"},
                    "pool_artefact_keys": {"joburg": {"2021": key}}},
        "provenance": {"git_commit": head, "git_dirty": False}}))
    return key


def _verify(root: Path, cwd: Path | None = None) -> tuple[int, str]:
    r = subprocess.run([str(REPO / ".venv/bin/python"), str(SRC / "declares.py"),
                        "--verify", "--processed", str(root)],
                       cwd=str(cwd or REPO), capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def test_the_declaration_gate_can_pass_and_each_violation_makes_it_fail():
    """1, 2 and 3: it looks, it can see, and it goes quiet when reverted."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "processed"
        key = _honest_tree(root)

        code, out = _verify(root)
        assert code == 0, (
            f"the gate cannot pass on a tree where nothing lies and every "
            f"field a writer in src/ emits is present. Until 2026-09-14 that "
            f"was true of EVERY tree, which is why the exit code carried no "
            f"information:\n{out}")

        # --- violation A: a stale pools_sha. The `~` state, the one the
        # module's docstring calls "the interesting one".
        summary = root / "forecast_summary.json"
        good = summary.read_text()
        d = json.loads(good)
        d["scenario"]["_pools_artefact_key"] = dict(key, pools_sha="0" * 16)
        summary.write_text(json.dumps(d))
        code, out = _verify(root)
        assert code == 1 and "embeds pools_sha" in out, (
            f"a summary embedding a pool key from code that is not on disk "
            f"scored clean:\n{out}")
        summary.write_text(good)
        assert _verify(root)[0] == 0, "the detector did not go quiet on revert"

        # --- violation B: an INTERROGATED cell goes absent. This one matters
        # because `--verify` now ignores UNDECLARED on the cells nothing
        # writes; if it ignored them all, it would be the old gate inverted.
        d = json.loads(good)
        del d["_generated"]
        summary.write_text(json.dumps(d))
        assert _verify(root)[0] == 1, (
            "a summary with no `_generated` passed. `time` IS interrogated on "
            "a summary -- montecarlo writes it -- so its absence is a real gap "
            "and not an exempt cell")
        summary.write_text(good)
        assert _verify(root)[0] == 0, "the detector did not go quiet on revert"

        # --- violation C: the freeze names a commit this repository does not
        # contain. A commit id that resolves to nothing is a false declaration
        # under any reading -- unlike naming an OLDER commit, which is what a
        # freeze is FOR and which used to be scored `~`.
        frozen = root / "forecast_frozen.json"
        good_frozen = frozen.read_text()
        d = json.loads(good_frozen)
        d["provenance"]["git_commit"] = "0" * 40
        frozen.write_text(json.dumps(d))
        code, out = _verify(root)
        assert code == 1 and "not a commit in this repository" in out, (
            f"a freeze naming a commit that does not exist scored clean:\n{out}")
        frozen.write_text(good_frozen)
        assert _verify(root)[0] == 0, "the detector did not go quiet on revert"


def test_a_freeze_that_is_merely_BEHIND_head_is_not_called_a_liar():
    """⛔ `~` IS THE STATE THAT MATTERS AND IT WAS BEING SPENT ON CORRECTNESS.

    A freeze records a PAST published forecast, so it names a past commit by
    construction. The old check compared it to HEAD and stamped `~` — "declared
    and WRONG" — on the next commit to the repository whatever that commit
    touched. CLAUDE.md §1: a freeze *"is a tripwire, not a gate"*. So being
    behind HEAD is a NOTE on a row that still counts as declared.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "processed"
        _honest_tree(root)
        parent = F._git("rev-parse", "HEAD~1")
        assert parent and not parent.startswith("<"), (
            "this test needs a repository with at least two commits; it has "
            f"{parent!r}")
        frozen = root / "forecast_frozen.json"
        d = json.loads(frozen.read_text())
        d["provenance"]["git_commit"] = parent
        frozen.write_text(json.dumps(d))

        code, out = _verify(root)
        assert code == 0, (
            f"a freeze one commit behind HEAD failed the gate. That is not a "
            f"false declaration, it is what a freeze is:\n{out}")
        assert "tripwire" in out, (
            "it passed silently. Being behind HEAD is worth SAYING -- the "
            "tripwire is the freeze's whole job -- it is just not a lie")

        # ...and a genuinely dirty freeze IS still a lie, so the row did not
        # simply stop being checked.
        d["provenance"]["git_dirty"] = True
        frozen.write_text(json.dumps(d))
        assert _verify(root)[0] == 1, (
            "`git_dirty` stopped being caught -- the commit check was "
            "loosened into no check at all")


def test_a_machine_without_git_does_not_produce_a_FALSE_lie():
    """⛔ `freeze._git` RETURNS A STRING WHEN IT FAILS, AND IT IS TRUTHY.

    It returns ``"<unavailable>"`` rather than raising (freeze.py:140-145). The
    old check was::

        head = F._git("rev-parse", "HEAD")
        if prov.get("git_commit") and head and prov["git_commit"] != head:
            r.states["git"] = LYING

    ``"<unavailable>"`` passes ``and``, and no real commit equals it, so on any
    machine where git is missing or the call fails, EVERY freeze was stamped
    `~` — declared and WRONG — for a reason that is about the machine and not
    about the artefact. That is precisely the class ``_SENTINELS`` was written
    for, unguarded, inside the module that defines it.

    And the old block ended ``except Exception: pass``, so a genuine failure
    left the row reading `DECLARED`: a silent downgrade to "fine" in a tool
    whose `_live_pools_sha` RAISES to prevent exactly that.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "processed"
        _honest_tree(root)
        real = F._git
        try:
            F._git = lambda *a: "<unavailable>"
            row = next(r for r in D.audit(root)
                       if r.path.endswith("forecast_frozen.json"))
        finally:
            F._git = real

        assert row.states["git"] != D.LYING, (
            f"a freeze scored `{D.LYING}` because GIT was unavailable, not "
            f"because the artefact was wrong: {row.notes}")
        assert any("git is unavailable" in n for n in row.notes), (
            f"it did not score a lie, but it also said nothing -- an unchecked "
            f"cell reading clean is the `except Exception: pass` defect with a "
            f"different spelling: {row.notes}")

        # 4 -- QUIET ON REVERT: with git working, the same tree is clean and
        # says so, which is what makes the assertion above a measurement.
        row = next(r for r in D.audit(root)
                   if r.path.endswith("forecast_frozen.json"))
        assert row.states["git"] == D.DECLARED
        assert not any("git is unavailable" in n for n in row.notes)


def test_the_gate_refuses_rather_than_scanning_a_tree_that_is_not_there():
    """⛔ THE ALL-CLEAR OVER ZERO ARTEFACTS.

    `PROCESSED` was `Path("data/processed")`, resolved against the SHELL's
    working directory, and `rglob` on a missing directory yields nothing rather
    than raising. Measured 2026-09-14::

        $ cd src && ../.venv/bin/python declares.py --verify
        **0 of 0 artefacts that CAN declare themselves do.**       EXIT=0

    `_live_pools_sha` still succeeded there, because its `sys.path` insert is
    absolute, so nothing in the output said the scan had found no tree.
    """
    with tempfile.TemporaryDirectory() as tmp:
        missing = Path(tmp) / "no-such-tree"
        code, out = _verify(missing)
        assert code != 0, (
            f"auditing a directory that does not exist exited {code}. An empty "
            f"scan is not an all-clear:\n{out}")
        assert "nothing to audit" in out, (
            f"it failed, but not with a reason a reader can act on:\n{out}")

        # THE POINT OF THE FIX, not merely that the refusal exists: the same
        # command from a DIFFERENT WORKING DIRECTORY must audit the same tree.
        root = Path(tmp) / "processed"
        _honest_tree(root)
        from_root = _verify(root, cwd=REPO)
        from_src = _verify(root, cwd=SRC)
        assert from_root[0] == from_src[0] == 0, (
            f"the verdict depends on the working directory: root "
            f"{from_root[0]}, src {from_src[0]}")


def test_the_cells_verify_ignores_are_the_cells_nothing_can_write():
    """0 — SCANNED THE RIGHT THING, BOTH DIRECTIONS, AND BOUNDED TWO-SIDEDLY.

    `--verify` ignores `UNDECLARED` on cells `declares` sets without reading the
    artefact (`Row.unchecked`). That exemption is what lets the gate pass at
    all, so it is the thing most worth watching: if it grew to cover the table,
    `--verify` would exit 0 on anything and this suite would not notice.

    The bound is two-sided against a COMPUTED denominator — every cell on every
    artefact that can declare — because a one-sided floor ratchets: when it
    trips, the cheapest fix is to move it.
    """
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "processed"
        _honest_tree(root)
        rows = D.audit(root)

        # POPULATION, asserted equal to what was scanned, BOTH WAYS.
        scanned = {r.path for r in rows}
        on_disk = {D._display(p) for p in root.rglob("*")
                   if p.is_file() and not p.name.startswith(".")}
        assert scanned == on_disk, (
            f"the audit did not cover the tree it was pointed at. "
            f"missed={sorted(on_disk - scanned)} "
            f"invented={sorted(scanned - on_disk)}")
        assert rows, "the population is empty, so nothing below is a measurement"

        capable = [r for r in rows if r.kind != "intermediate"]
        cells = sum(len(r.states) for r in capable)
        blind = sum(len(r.unchecked & set(r.states)) for r in capable)
        assert cells, "no cells: the denominator is zero and the bound is vacuous"
        assert 0 < blind < cells, (
            f"{blind} of {cells} cells are exempt from --verify. Zero would "
            f"mean the exemption has silently gone away and the gate is "
            f"unpassable again; all of them would mean the gate cannot fail.")
        assert blind / cells < 0.5, (
            f"the exemption covers {blind / cells:.0%} of the cells on the "
            f"artefacts that CAN declare. Past half, --verify is reporting on "
            f"a minority of the table and the number it prints is theatre. "
            f"Read `Row.unchecked` before moving this: the right response to "
            f"it tripping is to make a writer emit the field, never to widen "
            f"the exemption.")

        # A LIE IS COUNTED WHEREVER IT APPEARS, exempt cell or not -- otherwise
        # `unchecked` would be a way of switching the interesting state off.
        r = next(x for x in capable if x.unchecked)
        field = sorted(r.unchecked)[0]
        assert r.answerable == D.DECLARED
        r.states[field] = D.LYING
        assert r.answerable == D.LYING, (
            f"a `{D.LYING}` on the exempt cell `{field}` was ignored. "
            f"`unchecked` means 'no artefact carries this field', never 'do "
            f"not read what is written here'")


# ==========================================================================
# overhang_regimes.py — the published forecast
# ==========================================================================

_REFERENCE = json.dumps({"scenario": {"overhang_rule": "deduct"},
                         "council": 270, "_draws": 5000}, indent=1)
_REF_DRAWS = "draw,ANC,DA\n0,90,95\n"


def _fake_montecarlo(calls, fail=()):
    """Stands in for `montecarlo`. Writes the published files; fails on demand.

    The model is never run: this is a test about CONTROL FLOW around the writes,
    and running 5,000 draws three times to observe it would make the test too
    expensive to keep — which is how a guard like this one comes not to exist.
    """
    def main(argv=None):
        rule = "deduct"
        argv = argv or []
        for i, a in enumerate(argv):
            if a == "--set" and argv[i + 1].startswith("overhang_rule="):
                rule = argv[i + 1].split("=", 1)[1]
        calls.append(rule)
        if rule in fail:
            # montecarlo.py:3234 raises exactly this for `level`, BY DESIGN.
            raise RuntimeError(f"the `{rule}` rule grew the council from 270 "
                               f"to 331 seats and the allocation then failed")
        p = Path("data/processed")
        (p / "forecast_summary.json").write_text(json.dumps(
            {"scenario": {"overhang_rule": rule},
             "council": 270 if rule == "deduct" else 288, "_draws": 5000},
            indent=1))
        (p / "seat_draws.csv").write_text(f"draw,ANC,DA\n0,{rule}\n")
        return 0
    return type("M", (), {"main": staticmethod(main),
                          "fix_hash_seed": staticmethod(lambda: None)})


def _run_regimes(fail=()) -> dict:
    """Run `overhang_regimes.main` in a throwaway tree. Returns what survived."""
    spec = importlib.util.spec_from_file_location(
        "overhang_regimes_under_test", SRC / "overhang_regimes.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    calls: list[str] = []
    module.montecarlo = _fake_montecarlo(calls, fail)

    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "data" / "processed"
        p.mkdir(parents=True)
        (p / "forecast_summary.json").write_text(_REFERENCE)
        (p / "seat_draws.csv").write_text(_REF_DRAWS)
        for rule in module.RULES:
            (p / f"regime_{rule}_summary.json").write_text('{"stale": true}')
            (p / f"regime_{rule}_seat_draws.csv").write_text("stale\n")
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            try:
                module.main()
                raised = None
            except Exception as exc:                            # noqa: BLE001
                raised = f"{type(exc).__name__}"
            return {
                "raised": raised,
                "calls": list(calls),
                "summary": (p / "forecast_summary.json").read_text(),
                "draws": (p / "seat_draws.csv").read_text(),
                "regimes": {f.name: f.read_text()
                            for f in sorted(p.glob("regime_*"))},
            }
        finally:
            os.chdir(cwd)


def test_a_failed_counterfactual_leaves_the_published_forecast_alone():
    """⛔ `level` RAISES BY DESIGN AND IT IS THE SECOND OF THE THREE.

    The restore used to be a bare statement after the loop::

        for rule in ("expand", "level", "cap"):
            montecarlo.main(["--counterfactual", "--set", f"overhang_rule={rule}"])
            ...
        montecarlo.main([])          # <- skipped by any raise

    so a `level` failure — or a Ctrl-C — left `data/processed/forecast_summary
    .json`, which is the site's input, holding the **expand** council: grown
    past 270, with a moved majority threshold, under the name the published
    forecast reads. `stats.freshness_problems` compares mtimes and would not
    see it; nothing asserts the published `scenario.overhang_rule == "deduct"`;
    `data/**` is gitignored so nothing warns and nothing restores it.
    """
    out = _run_regimes(fail=("level",))

    assert out["raised"] == "RuntimeError", (
        f"the failure was swallowed ({out['raised']}) -- then the tree is "
        f"quietly whatever the last run left and nobody is told")
    assert out["calls"] == ["expand", "level"], (
        f"the injection did not land where the real one does: {out['calls']}")

    # THE CONSTRUCTED VIOLATION, CAUGHT: the published artefacts are the
    # reference, byte for byte, not a re-derivation of it.
    published = json.loads(out["summary"])
    assert published["scenario"]["overhang_rule"] == "deduct", (
        f"the published forecast is holding a COUNTERFACTUAL council: "
        f"overhang_rule={published['scenario']['overhang_rule']!r}, "
        f"council={published['council']}. This is the defect.")
    assert out["summary"] == _REFERENCE and out["draws"] == _REF_DRAWS, (
        "the reference was restored but not byte for byte. A file copy has no "
        "excuse for being approximate, and a re-run would not be a restore: "
        "`seats.allocate`'s largest-remainder key is not a total order, so a "
        "tied last seat is a coin flip under a random hash seed")

    # AND NO REGIME ARTEFACT WAS PUBLISHED from the half-finished sweep: a set
    # half from this run and half from the last one is worse than none.
    assert all(v.strip() in ('{"stale": true}', "stale")
               for v in out["regimes"].values()), (
        f"a partial sweep published regime artefacts: "
        f"{ {k: v[:30] for k, v in out['regimes'].items()} }")


def test_the_detector_goes_quiet_when_nothing_fails():
    """4 — AND IT GOES QUIET ON REVERT. Without this the test above passes on
    a script that simply never publishes anything."""
    out = _run_regimes(fail=())

    assert out["raised"] is None, f"a clean sweep raised {out['raised']}"
    assert out["calls"] == ["expand", "level", "cap", "deduct"], (
        f"the reference re-run did not happen: {out['calls']}. The table's "
        f"claim is that all four runs are the same simulated elections under "
        f"different law, which needs the reference from the same code")
    assert json.loads(out["summary"])["scenario"]["overhang_rule"] == "deduct"
    for rule in ("expand", "level", "cap"):
        got = json.loads(out["regimes"][f"regime_{rule}_summary.json"])
        assert got["scenario"]["overhang_rule"] == rule, (
            f"regime_{rule}_summary.json holds {got} -- the staged artefacts "
            f"were not published, or were published crossed over")


def test_the_regime_script_pins_the_hash_seed_like_every_other_caller():
    """⛔ FOUR RUNS OF THE PUBLISHED FORECAST UNDER A RANDOM PYTHONHASHSEED.

    `montecarlo.fix_hash_seed` runs only under `montecarlo`'s own `__main__`
    (montecarlo.py:5301). This script imports `montecarlo` and calls `main()`
    as a LIBRARY, and every other library-style entry point in `src/` pins the
    seed — `compare_history`, `backtest`, `sweep`, `diagnose`, `freeze`. This
    one did not, and the module docstring claimed the restore was
    *"deterministic seed — bit-identical"*.

    It compounds: `seats.allocate`'s largest-remainder key is not a total
    order, so under a random hash seed a tied last seat is a coin flip. The
    "restore" could write a forecast differing from the published one by a
    whole seat.

    Checked by AST rather than by running it, because `fix_hash_seed` RE-EXECS
    THE PROCESS — a test that let it happen would re-enter the test runner with
    the runner's argv. (That is not hypothetical: the first probe written for
    this on 2026-09-14 let the re-exec through and started the real model
    against the real `data/processed`.)
    """
    tree = ast.parse((SRC / "overhang_regimes.py").read_text())
    guards = [n for n in tree.body
              if isinstance(n, ast.If)
              and ast.unparse(n.test) == "__name__ == '__main__'"]
    assert len(guards) == 1, (
        f"expected exactly one `if __name__ == '__main__'` block, found "
        f"{len(guards)} -- this check reads the first and would miss the rest")
    calls = [ast.unparse(n.value) for n in ast.walk(guards[0])
             if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
    assert "montecarlo.fix_hash_seed()" in calls, (
        f"the guard does not pin PYTHONHASHSEED: {calls}")
    assert calls[0] == "montecarlo.fix_hash_seed()", (
        f"it is pinned, but not FIRST: {calls}. `fix_hash_seed` replaces the "
        f"process, so anything before it runs twice")

    # 2 — IT CAN SEE: the same reading of a guard that does not pin it must
    # fail, or this asserts nothing about the AST walk.
    without = ast.parse("if __name__ == '__main__':\n    sys.exit(main())\n")
    g = [n for n in without.body if isinstance(n, ast.If)][0]
    seen = [ast.unparse(n.value) for n in ast.walk(g)
            if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)]
    assert "montecarlo.fix_hash_seed()" not in seen, (
        "the detector reports a pinned seed on a guard that has none, so it "
        "cannot tell the two apart")


# ==========================================================================
# compare_history.py — the scoreboard's own manifest
# ==========================================================================

def _rows(*seeds):
    return [{"slug": f"c{i}", "year": "2021",
             "scenario_defaults": ({} if s is None else {"seed": s})}
            for i, s in enumerate(seeds)]


def test_the_manifest_records_the_seed_the_rows_resolved():
    """⛔ IT DECLARED A MODULE GLOBAL THAT `apply_city` REWRITES EVERY ROW.

    `"seed": M.DEFAULTS.get("seed")`, commented *"The seed every city-year
    actually ran at"*. `M.apply_city` clears `DEFAULTS` and re-overlays
    `_PRISTINE_DEFAULTS` plus the city toml on every city-year
    (montecarlo.py:1198), and two city tomls declare a `seed`. So it read the
    LAST city's value under `--jobs 1` and the pristine one under `--jobs N`,
    and never reflected `--set seed=N` at all, because `load_scenario` applies
    `--set` over a deepcopy (montecarlo.py:1961).

    ⚠️ It was RIGHT on the tree it was written against — every route and all
    24 committed rows read 20261104 — which is what `apply_city`'s own
    docstring calls *"luck, not design"*.
    """
    assert C._seed_block(_rows(7, 7, 7))["seed"] == 7

    mixed = C._seed_block(_rows(7, 7, 9))
    assert mixed["seed"] == [7, 7, 9], (
        f"a panel that ran at two seeds was described by one scalar: "
        f"{mixed['seed']!r}. One city's value standing in for all of them is "
        f"the declared-and-WRONG state, in the block whose job is provenance")
    assert mixed["seed_by_row"]["c2:2021"] == 9

    # THE SENTINEL. A row predating `scenario_defaults` cannot say what it ran
    # at, and "cannot say" is not "ran at the default".
    assert C._seed_block(_rows(None))["seed"] == "<unrecorded>"
    assert not D._declared(C._seed_block(_rows(None))["seed"]), (
        "`declares` would score `<unrecorded>` as a real declaration -- a "
        "truthy string passing a presence check is the whole reason "
        "`_SENTINELS` exists")

    # 4 — QUIET ON REVERT.
    assert C._seed_block(_rows(7, 7, 7))["seed"] == 7


def test_a_city_whose_archive_will_not_load_is_recorded_not_dropped():
    """⛔ §1.69 REINSTATED INSIDE THE FIX FOR §1.69.

    `_archive_targets` is the sole source of the denominator
    `population.excluded` is measured against, and it read::

        except Exception:
            continue

    so a city whose config would not load vanished from the archive entirely —
    neither scored, nor excluded, nor reached by the catch-all branch, which
    iterates that same archive. The manifest went on asserting the smaller
    number and `_exit_code` never looks here, so the run exited 0. Its own
    docstring says *"Derived, never typed — a typed panel list is how §1.69
    stayed wrong for months"*; deriving it does not help if the derivation may
    fail in silence.

    ⚠️ MEASURED 2026-09-14 on the live archive: 24 → 21 with one city's
    `cityconfig.load` made to raise, and nothing raised, printed or exited.
    """
    import cityconfig

    healthy, unreadable = C._archive_targets()
    assert healthy and not unreadable, (
        f"this test needs a readable archive to start from: "
        f"{len(healthy)} targets, {unreadable}")
    victim = healthy[0][0]
    lost = {y for c, y in healthy if c == victim}
    assert lost, "the chosen city contributes no city-years, so nothing is lost"

    real = cityconfig.load

    def broken(slug):
        if slug == victim:
            raise RuntimeError("injected: config unreadable")
        return real(slug)

    try:
        cityconfig.load = broken
        hurt, reported = C._archive_targets()
        assert len(hurt) == len(healthy) - len(lost), (
            f"the injection did not shrink the archive, so nothing below is a "
            f"measurement: {len(hurt)} vs {len(healthy)}")
        assert [c for c, _ in reported] == [victim], (
            f"the city that could not be enumerated was dropped in silence: "
            f"{reported}. That IS the defect -- the denominator got smaller "
            f"and the artefact went on asserting it")
        assert "injected: config unreadable" in reported[0][1], (
            f"it is recorded, but without the exception, which is the only "
            f"thing that says WHY: {reported[0][1]!r}")

        block = C._population_block_for([], [], hurt, reported)
        assert block["archive_unreadable"] == [
            {"city": victim, "why": reported[0][1]}]
        assert any(e["city"] == victim and e["year"] == "<all>"
                   for e in block["excluded"]), (
            f"it reached the manifest's own block in neither channel: "
            f"{block['archive_unreadable']}")
        assert not any(e["city"] == victim and "not selected" in e["why"]
                       for e in block["excluded"]), (
            "it picked up the catch-all reason as well -- 'not selected by "
            "--city/--target' is a statement about the CLI and is FALSE here")
    finally:
        cityconfig.load = real

    # 4 — QUIET ON REVERT, both the scan and the block.
    again, none = C._archive_targets()
    assert len(again) == len(healthy) and not none, (
        f"the detector did not go quiet: {len(again)} targets, {none}")
    assert C._population_block_for([], [], again, none)["archive_unreadable"] == []


def test_one_run_writes_one_manifest():
    """Two `build_manifest` calls made two independent records of one run.

    `history.json` got the first and `history.md` — which is what a human reads,
    and whose `_citable` token is stamped from it — got the second. Each call
    takes its own `generated` stamp at second resolution (~0.09 s apart,
    measured), its own `git status` reading and its own enumeration of every
    city's pool artefact keys. Two records of one run that can disagree is
    §1.214 in miniature, inside the layer built to stop it.
    """
    tree = ast.parse((SRC / "compare_history.py").read_text())
    main = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    calls = [n for n in ast.walk(main)
             if isinstance(n, ast.Call)
             and getattr(n.func, "id", None) == "build_manifest"]
    assert len(calls) == 1, (
        f"`main` calls build_manifest {len(calls)} times. The JSON and the "
        f"rendered report must carry the SAME manifest object, not two "
        f"readings of the same run.")

    # 2 — IT CAN SEE. The same walk over a two-call body must count two.
    doubled = ast.parse("def main():\n    a = build_manifest(1, 2, 3)\n"
                        "    b = build_manifest(1, 2, 3)\n")
    f = doubled.body[0]
    assert len([n for n in ast.walk(f)
                if isinstance(n, ast.Call)
                and getattr(n.func, "id", None) == "build_manifest"]) == 2, (
        "the detector counts one call in a body that has two, so it cannot "
        "tell the fixed shape from the broken one")
