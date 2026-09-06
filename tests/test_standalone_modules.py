"""Every module in `src/` is either IMPORTED or a DECLARED entry point.

⛔ THE DEFECT THIS EXISTS FOR. `src/leverage.py` sat in `src/` for weeks,
imported by nothing, run by nobody, and rotted where it stood. `f_other` — the
mechanism it was built on — was deleted from `run_model` on 2026-08-19
(MODEL-LOG §1.52), and for eleven days after that the script kept printing
numbers from a path the forecast had abandoned, while reading as a sensitivity
analysis *of* the forecast. It was retired to `archive/retired-scripts/` on
2026-08-30 (§1.140). **Nothing in this suite could see any of it**: a file
nobody imports is a file no test reaches, and the suite reported green the whole
time.

THE RULE. A module in `src/` must be one of two things, and it must be
obvious which:

  (a) **IMPORTED** by another module in `src/` or by a test in `tests/`; or
  (b) an **ENTRY POINT** — a script a human or the build runs — declared in
      `ENTRY_POINTS` below **with a reason naming who runs it**.

Anything in neither is dead code, and this file names it.

⚠️ **`if __name__ == "__main__":` IS NOT THE TEST, AND CANNOT BE.**
`archive/retired-scripts/leverage.py` has one, and an `argparse.ArgumentParser`
beside it — so does every single un-imported module in `src/` today, all
twenty-two of them. An automatic "it has a main block, therefore it is alive"
rule would have exonerated exactly the file that prompted this. A `__main__`
block says the module *can* be run; it says nothing about whether anyone still
does.

⚠️ **"IT IS NAMED IN A DOCUMENT" IS NOT THE TEST EITHER.** At the time of
writing, `README.md`'s reproduction recipe still reads

    python src/leverage.py                   # per-ward turnout elasticity

for a script that has been retired and must not be run. The documentation goes
stale in the same direction and for the same reason as the code, so a scan of
the prose would inherit the rot rather than catch it.

What is left, and what this file therefore uses, is a **hand-declared list with
a reason attached to every entry** — the same shape as `run_all.MODULES`, and
for the same reason: membership is not a judgement call, so it is asserted; the
justification is a judgement call, so it is written down where the next reader
can disagree with it.

HOW THE IMPORTS ARE READ, and why it matters here. From the **syntax tree**, and
from **every node in it** — not the top of the file, and not `grep`.

* Half of this repository's real imports are function-local:
  `publication.py:368` does `import freeze as _freeze` inside a method,
  `iec_csv.py:32` does `import cityconfig` inside `active_muni_code`,
  `fold.py:326` does `from turnout import ELECTIONS ...` inside a function. A
  top-of-file scan reports `freeze`, `turnout` and (transitively) others as
  dead. All three are alive.
* And half of this repository's *comments* discuss imports at length, so `grep`
  reports the opposite error. `src/cityconfig.py`'s docstring contains the line
  `import cityconfig`; the AST does not see it, because it is prose.

WHAT THIS TEST CANNOT ESTABLISH, said plainly:

* **That an importer is itself alive.** Liveness here is one hop. If an
  allowlisted entry point is retired tomorrow, any helper only it imported
  becomes dead the same day — and this test will say so *then*, on the next
  run, which is the point.
* **That a module imported only by its own test does any work in production.**
  `publication.py` is in exactly that position today: nothing in `src/` imports
  it, `tests/test_publication_ledger.py` does, and it passes rule (a) on that
  alone. That is a weaker signal than a production import and it is recorded
  here rather than asserted away.
* **Anything about `archive/`.** Retired scripts are deliberately excluded from
  the importer scan: a retired file must not be able to keep a `src/` module
  alive, or retirement would preserve exactly what it is meant to release.
"""

from __future__ import annotations

import ast
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

SRC = ROOT / "src"
TESTS = ROOT / "tests"


# ---------------------------------------------------------------------------
# THE ALLOWLIST — module -> who runs it, and why it is not imported.
#
# A REASON IS NOT OPTIONAL AND IT IS NOT DECORATION. It is the only thing in
# this file that a future reader can use to decide whether an entry has gone
# the way of `leverage.py`. "who runs it" means a command in a document, a step
# in `build_all.plan`, or a named human workflow — not "it is useful".
#
# Adding a name here is a claim. Make it a checkable one.
# ---------------------------------------------------------------------------
ENTRY_POINTS: dict[str, str] = {
    # --- named in CLAUDE.md's "Running things" -----------------------------
    "arrivals":
        "CLAUDE.md 'Running things': `.venv/bin/python src/arrivals.py` — the "
        "arrival machinery scored on its own, because its failures are "
        "otherwise indistinguishable from a level error inside a seat total. "
        "Run by hand when the arrival path changes.",
    "contested_area":
        "CLAUDE.md 'Running things': `.venv/bin/python src/contested_area.py` "
        "— validates the poll path's contested-area conversion, the table "
        "`polling.metro_estimate` asserted for months with no script behind it "
        "(MODEL-LOG §1.66). Run by hand when the poll channel changes.",
    "diagnose":
        "CLAUDE.md 'Running things': `.venv/bin/python src/diagnose.py --city "
        "joburg --target 2021 --wards 0` — the per-city-year investigation CLI. "
        "Run by hand when compare_history flags a city-year.",
    "sweep":
        "CLAUDE.md 'Running things': `.venv/bin/python src/sweep.py` — the "
        "obvious-fault sweep. Run by hand before a commit that moves numbers.",

    # --- named in README.md's reproduction recipe --------------------------
    "fetch_iec":
        "README.md step 1 (acquire): `python src/fetch_iec.py`. Human-run "
        "download of the IEC result files; needs a real browser session for "
        "some endpoints (SOURCES.md). Cited as provenance by `archive.py`.",
    "fetch_boundaries":
        "README.md step 1 (acquire): `python src/fetch_boundaries.py`. "
        "Human-run download of MDB ward/VD boundaries; cited as the provenance "
        "of every `data/raw/geo/*` entry in `archive.py`.",
    "fetch_byelections":
        "README.md step 1 (acquire): `python src/fetch_byelections.py`. "
        "Human-run download of the by-election dashboard; cited as the "
        "provenance of `data/raw/byelections/` in `archive.py`.",
    "ingest_npe":
        "README.md step 1 (acquire): `python src/ingest_npe.py ...`. The "
        "national-election ingest, run once per NPE file; its LGE twin "
        "`ingest_lge` is imported by `pools`/`polling`, this one is not.",
    "validate_seats":
        "README.md step 2: `python src/validate_seats.py --year 2021|2016|2011` "
        "— proves the seat allocator against three published councils, exact "
        "or exit 1. Run by hand when `seats.py` changes.",
    "build_crosswalk":
        "README.md step 3: `python src/build_crosswalk.py`. Builds the party "
        "crosswalk; `montecarlo.PARTIES` exists to be read by it "
        "(montecarlo.py:1543).",
    "build_geo":
        "README.md step 3: `python src/build_geo.py`. Clips the national ward "
        "shapefiles to the city; cited as the provenance of the "
        "`data/raw/geo/wards*_` entries in `archive.py`.",
    "byelections":
        "README.md step 3: `python src/byelections.py`. Turns the by-elections "
        "in the window into the two signals `fold`/`levels` consume from the "
        "processed directory, not by import.",
    "gamma_recent":
        "README.md step 3: `python src/gamma_recent.py`. Fits γ for parties "
        "fold 1 never saw and writes `gamma_recent.csv`, which `montecarlo.py` "
        "reads as an ARTEFACT (montecarlo.py:3901), never as an import.",
    "render_sheet":
        "README.md step 5: `python src/render_sheet.py`, and a step in "
        "`build_all.plan` ('sheet figures, claims, regimes'), invoked as a "
        "subprocess rather than imported.",
    "build_portal":
        "README.md step 5: `python src/build_portal.py`, and the 'portal' step "
        "in `build_all.plan`, invoked as a subprocess. It imports `build_site` "
        "for the palette; nothing imports it.",
    "build_validation":
        "README.md 'Scoring it against a past election': `python "
        "src/build_validation.py --target 2021` — runs the model and the "
        "baselines across eight metros and regenerates "
        "`docs-public/about-the-model.md` whole. Every figure on the About "
        "page comes from this and none is typed.",

    # --- steps in build_all.plan, invoked as subprocesses ------------------
    "overhang_regimes":
        "The `--regimes` step in `build_all.plan` ('overhang "
        "counterfactuals'), run as a subprocess; also `python "
        "src/overhang_regimes.py` in its own docstring. Produces the "
        "regime-comparison table `render_sheet.py` publishes.",
    "export_interactive":
        "The `--interactive` step in `build_all.plan` ('interactive data "
        "pack'), run as a subprocess. OPTIONAL and currently off by design — "
        "it feeds `build_interactive.py`, which refuses. ⚠️ ON NOTICE: it is "
        "the closest thing here to `leverage.py`'s position, because the only "
        "thing that runs it is a flag nobody sets. PUBLISHING-BACKLOG.md §308 "
        "carries the decision to port it; if that decision is reversed, this "
        "module is retired, not left here.",
    "build_interactive":
        "The `--interactive` step in `build_all.plan` ('interactive page'), "
        "run as a subprocess. ⚠️ IT REFUSES AT IMPORT ON PURPOSE — its "
        "in-browser drawer is the old two-bloc engine and is not ported to "
        "voter pools, so it exits 1 rather than publish arithmetic that "
        "disagrees with the model (README.md; `tests/test_build_all.py` "
        "asserts the refusal does not stop the site being built). The refusal "
        "is why it can never be imported by anything.",

    # --- instruments and one-off human workflows ---------------------------
    "width_budget":
        "The ablation harness behind the width attribution quoted in "
        "MACHINERY.md ('Measured by ablation, Johannesburg 2021, five seeds "
        "(`src/width_budget.py`)') and named in PUBLISHING-BACKLOG.md as one of "
        "the two instruments for the width work. Run by hand; it monkeypatches "
        "`montecarlo` and restores every patch in a `finally`, so it must not "
        "be imported into a run.",
    "derive_city":
        "City onboarding, one run per new city: `python src/derive_city.py "
        "--code TSH --slug tshwane --province GP` (its own docstring). Proposes "
        "`cities/<slug>.toml` from the city's own IEC files — structure derived, "
        "judgements only *informed*, for a human to accept or reject.",
    "prep_logos":
        "One-off asset preparation: `python src/prep_logos.py` -> "
        "`site/logos/<CODE>.png` (its own docstring). Re-run only when party "
        "artwork changes.",
}

# The minimum a reason has to be before it counts as one. Short enough to be no
# obstacle to a real sentence, long enough that "TODO", "CLI" or "entry point"
# cannot be typed in to silence the guard — which is the only way this list
# rots into the thing it replaced.
MIN_REASON_CHARS = 60


def _module_names() -> set[str]:
    """Every module `src/` offers under its bare importable name.

    Bare, because that is how this repository imports: `src/` goes on
    `sys.path` (see `tests/_support`), so it is `import pools`, never
    `import src.pools`. `__init__.py` does not exist and must not.
    """
    names = {path.stem for path in SRC.glob("*.py")}
    # (1) IT LOOKED, once, for every test below — all four consume this and all
    # four pass on an empty set, because `orphans`, `ghosts` and `redundant`
    # are set differences that go empty when `SRC` does. The denominator is the
    # whole Python tree, which moves with the repository, so the band cannot be
    # repaired by lowering a number: 50 of 84 files, 0.60, on 2026-08-31.
    scanned(names, of=sorted(SRC.glob("*.py")) + sorted(TESTS.glob("*.py")),
            low=0.25, high=0.85,
            what="modules found in src/",
            denominator=".py files across src/ and tests/")
    return names


def _importers() -> dict[str, set[str]]:
    """Map each `src/` module name to the files that import it.

    From the AST, walking EVERY node — `ast.walk` reaches an `import` inside a
    function body, a method, a `try:`, or an `if`, which is where a large share
    of this repository's real imports live (see the module docstring).

    Scans `src/` and `tests/` and nothing else. `archive/retired-scripts/` is
    excluded on purpose: a retired script must not be able to hold a module
    alive.

    Related to `test_delivery_proof._names_imported_in_src`, which answers a
    different question — *which names does src/ import at all*, as one flat set,
    to check `montecarlo.MODULE_CONSTANTS` resolves. This one needs the inverse
    mapping and needs `tests/` in scope, so it cannot be that function.
    """
    names = _module_names()
    found: dict[str, set[str]] = {name: set() for name in names}
    for directory in (SRC, TESTS):
        for path in sorted(directory.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"),
                             filename=str(path))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported |= {a.name.split(".")[0] for a in node.names}
                elif (isinstance(node, ast.ImportFrom)
                      and node.module and not node.level):
                    imported.add(node.module.split(".")[0])
            for name in imported & names:
                if name == path.stem:
                    continue      # a docstring's self-referential example
                found[name].add(f"{directory.name}/{path.name}")
    return found


def test_no_module_in_src_is_dead_code():
    """The whole rule, in one assertion: imported, declared, or named here.

    THE FAILURE MODE THIS CATCHES IS SILENCE. Dead code does not raise, does not
    slow anything down and does not fail a test — it simply keeps agreeing with
    a version of the model that no longer exists, and it reads as part of the
    system to everyone downstream. `leverage.py` did that for eleven days after
    the mechanism under it was deleted, and the only reason it was ever found
    was that a human went looking.
    """
    importers = _importers()
    orphans = sorted(name for name, seen in importers.items()
                     if not seen and name not in ENTRY_POINTS)
    assert not orphans, (
        f"{len(orphans)} module(s) in src/ are imported by nothing in src/ or "
        f"tests/ and are not declared entry points: {orphans}\n"
        f"\n"
        f"  Each is dead code until proven otherwise. This is the shape "
        f"`src/leverage.py` was in for weeks while the suite stayed green.\n"
        f"\n"
        f"  Do ONE of three things — not a fourth:\n"
        f"    · WIRE IT UP. If it should be part of a run, import it from the "
        f"module that should be calling it, and give it a test.\n"
        f"    · DECLARE IT. If a human or the build genuinely runs it, add it "
        f"to ENTRY_POINTS in this file with a reason NAMING WHO RUNS IT and "
        f"where that is written down — a command in README.md or CLAUDE.md, or "
        f"a step in `build_all.plan`.\n"
        f"    · RETIRE IT. Move it to archive/retired-scripts/ with a header "
        f"saying what it did, why it is retired and what to build instead, and "
        f"append the finding to MODEL-LOG.md. That is what §1.140 did.\n"
        f"\n"
        f"  Do NOT add it to ENTRY_POINTS because it has an `if __name__ == "
        f"\"__main__\"` block. So did leverage.py.")


def test_the_allowlist_names_no_module_that_has_been_deleted():
    """A stale exemption is how this rots back into what it replaced.

    An entry naming a file that no longer exists is worse than no entry: it
    reads as a live declaration of a live script, it can never fail, and it
    quietly widens the exemption list for as long as nobody re-reads it. Every
    hand-maintained list in this repository has failed this way at least once —
    `run_all.MODULES` lost `test_freeze.py` for a day (§1.84 neighbourhood),
    `montecarlo.MODULE_CONSTANTS` carried ghosts, and the published page carried
    ten claims pinned to a lever `run_model` no longer had.
    """
    names = _module_names()
    ghosts = sorted(set(ENTRY_POINTS) - names)
    assert not ghosts, (
        f"ENTRY_POINTS names {len(ghosts)} module(s) that do not exist in "
        f"src/: {ghosts}\n"
        f"  If the file was RENAMED, rename it here too. If it was RETIRED, "
        f"delete the entry — the reason it carried belongs in the retired "
        f"file's own header and in MODEL-LOG.md, not in a live allowlist.")


def test_the_allowlist_exempts_nothing_that_is_already_imported():
    """An exemption that exempts nothing is a claim nobody is checking.

    A module something imports satisfies rule (a) on its own and needs no
    declaration. Leaving the declaration behind costs a reader the one thing
    this list is for: the ability to read it top to bottom and see the complete
    set of things in `src/` that run only because a human runs them.
    """
    importers = _importers()
    redundant = sorted(f"{name} (imported by {sorted(importers[name])})"
                       for name in ENTRY_POINTS if importers.get(name))
    assert not redundant, (
        f"ENTRY_POINTS exempts {len(redundant)} module(s) that something "
        f"already imports, so the exemption does nothing:\n    "
        + "\n    ".join(redundant)
        + f"\n  Delete the entry. If the module is still ALSO a script a human "
          f"runs, that belongs in its own docstring's usage line, where the "
          f"person about to run it will read it.")


def test_every_declared_entry_point_carries_a_real_reason():
    """The reason is the whole guard, so an empty one must fail loudly.

    `if __name__ == "__main__":` cannot arbitrate this — every un-imported
    module in `src/` has one, and so does `archive/retired-scripts/leverage.py`,
    which is the file that proved the rule needed writing. What separates a live
    script from a rotting one is a statement of who runs it that a reader can go
    and check. A one-word entry is an exemption with no such statement.
    """
    thin = sorted(f"{name}: {len(reason.strip())} chars"
                  for name, reason in ENTRY_POINTS.items()
                  if len(reason.strip()) < MIN_REASON_CHARS)
    assert not thin, (
        f"ENTRY_POINTS entries whose reason is under {MIN_REASON_CHARS} "
        f"characters: {thin}\n"
        f"  A reason must name WHO RUNS IT and WHERE THAT IS WRITTEN DOWN — a "
        f"command in README.md or CLAUDE.md, a step in `build_all.plan`, or a "
        f"named human workflow. 'CLI' and 'entry point' are not reasons; they "
        f"are restatements of the exemption.")

    # (0) THE RIGHT SET. The rule above says the reason must name WHERE IT IS
    # WRITTEN DOWN, and the scan measured only its LENGTH — sixty characters of
    # anything passed. The shortest live reason is 134 characters and the floor
    # is 60, so the length test has never been within 2x of binding and, when
    # it finally did trip, the cheap repair would have been to lower it. So
    # check the citation instead: the document the reason names must exist and
    # must still name the module. Measured 2026-08-31: 22 of 22 do.
    #
    # `README.md` carried `python src/leverage.py` for a script retired to
    # `archive/retired-scripts/` — a citation rotting exactly this way, one
    # layer out — which is why this direction is worth a test.
    documents = {p.name: p for p in ROOT.glob("*.md")}
    documents["build_all.plan"] = SRC / "build_all.py"

    uncited, stale = [], []
    for name, reason in sorted(ENTRY_POINTS.items()):
        cited = [d for d in documents if d in reason]
        if not cited and "docstring" not in reason:
            uncited.append(name)
        for doc in cited:
            # The FILENAME, not the bare name: `SOURCES.md` contains the word
            # "sweep" in prose and does not run `src/sweep.py`, and a citation
            # that matches on an English word is the length test again.
            if f"{name}.py" not in documents[doc].read_text(encoding="utf-8"):
                stale.append(f"{name} cites {doc}, which does not name "
                             f"{name}.py")
    assert not uncited, (
        f"ENTRY_POINTS entries citing no checkable document: {uncited}\n"
        f"  Name a file this test can open — one of {sorted(documents)} — or "
        f"say 'its own docstring'. A reason nobody can follow is the length "
        f"test passing and the rule failing.")
    assert not stale, (
        "ENTRY_POINTS reasons whose citation has gone stale:\n  "
        + "\n  ".join(stale)
        + "\n  The declaration is now the only place this script is claimed "
          "to be run from, which is the state `leverage.py` was in.")


def test_the_dead_code_detector_catches_a_constructed_orphan():
    """(2) IT CAN SEE, and (3) ON A CONSTRUCTED TREE.

    Every other test in this file reports on the tree as it happens to be, and
    the tree currently has no orphan — so nothing here has ever demonstrated
    that the import graph can find one. This builds a two-module `src/` where
    one module imports the other and a third imports nothing, and pushes it
    through the same `ast.walk`-based edge collection.

    It also covers the shape `_importers` was written for and the shape it is
    still blind to, and asserts the difference rather than assuming it: an
    import inside a FUNCTION BODY counts (that is what `ast.walk` buys over
    `tree.body`), while two modules that import only each other look alive to a
    one-hop rule and are therefore NOT reported — recorded here so the
    limitation is a measured fact rather than an unexamined belief.
    """
    def importers_over(directory):
        names = {p.stem for p in directory.glob("*.py")}
        found = {name: set() for name in names}
        for path in sorted(directory.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imported: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported |= {a.name.split(".")[0] for a in node.names}
                elif (isinstance(node, ast.ImportFrom)
                      and node.module and not node.level):
                    imported.add(node.module.split(".")[0])
            for name in imported & names:
                if name != path.stem:
                    found[name].add(path.name)
        return found

    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp)
        (fake / "consumer.py").write_text(
            "def go():\n"
            "    import used_deep\n"          # inside a body: ast.walk finds it
            "    return used_deep\n")
        (fake / "used_deep.py").write_text("VALUE = 1\n")
        (fake / "orphan.py").write_text(
            'def f():\n    return 1\n\n'
            'if __name__ == "__main__":\n    f()\n')
        (fake / "cycle_a.py").write_text("import cycle_b\n")
        (fake / "cycle_b.py").write_text("import cycle_a\n")
        seen = importers_over(fake)

    assert seen["used_deep"] == {"consumer.py"}, (
        f"an import inside a function body was not seen: {seen['used_deep']}. "
        f"`ast.walk` rather than `tree.body` is the whole reason this graph is "
        f"trusted, because a large share of this repository's imports are "
        f"deferred into function bodies.")
    orphans = sorted(n for n, s in seen.items() if not s)
    assert orphans == ["consumer", "orphan"], (
        f"the orphan detector reported {orphans}. It must report `orphan` — "
        f"which nothing imports and which has the `__main__` block that makes "
        f"dead code look alive — and `consumer`, the root. It must NOT report "
        f"`cycle_a` or `cycle_b`: THEY IMPORT ONLY EACH OTHER AND A ONE-HOP "
        f"RULE CANNOT SEE THAT. `leverage.py` with a friend would be invisible "
        f"to the live test, and this records that limit rather than assuming "
        f"it away.")


def test_every_declared_entry_point_can_actually_be_run():
    """Corroboration, not proof: a declared script must at least be runnable.

    ⚠️ READ THIS BEFORE TRUSTING IT. A `__main__` block is NECESSARY and
    nowhere near SUFFICIENT — `archive/retired-scripts/leverage.py` has one, and
    so does every un-imported module in `src/`. This test therefore establishes
    only that nothing has been allowlisted which could not be executed at all:
    an importable library declared as a script, or a script whose `__main__`
    block was deleted in a refactor while the declaration stayed.

    The declaration's reason is what does the real work. This checks the one
    part of it a machine can check.
    """
    unrunnable: list[str] = []
    for name in sorted(ENTRY_POINTS):
        path = SRC / f"{name}.py"
        if not path.exists():
            continue          # the previous test owns this failure
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        runnable = any(
            isinstance(node, ast.If)
            and any(isinstance(sub, ast.Name) and sub.id == "__name__"
                    for sub in ast.walk(node.test))
            for node in tree.body)
        if not runnable:
            unrunnable.append(name)
    assert not unrunnable, (
        f"ENTRY_POINTS declares {len(unrunnable)} module(s) as scripts a human "
        f"runs, but they have no `if __name__ == \"__main__\":` block, so "
        f"running them does nothing: {unrunnable}\n"
        f"  Either the entry is wrong and the module is a library — in which "
        f"case something must import it — or the block was lost. A declaration "
        f"that names a command nobody can execute is the same defect as a "
        f"README naming a retired script.")


if __name__ == "__main__":
    # `run_module`, not a hand-rolled loop: it is the only runner that catches
    # `SkipTest` and `SystemExit`, which every module in `src/` raises for a
    # missing input. See `tests/_support.run_module` and MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
