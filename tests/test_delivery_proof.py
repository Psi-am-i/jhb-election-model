"""CLASS 14 — AN INSTRUMENT THAT CANNOT SEE WHAT IT CLAIMS TO PROVE.

`montecarlo.MODULE_CONSTANTS` and the functions around it are the *delivery
proof*: the machinery that separates "the change did nothing" from "the change
never arrived". `NULL-RESULTS.md` §1 is the whole argument — a null with the
gate shut is **VOID, NOT NULL** — and `test_levers_are_live.py` is the file that
paid for it, twice, in retracted `EXPECTED_INERT` reasons.

Until this file existed there was **no test of the table at all**. `grep -rn
MODULE_CONSTANTS src tests` returned hits inside `src/montecarlo.py` and
nowhere else: 48 declared names across five modules, a frozen-defaults
exception, a lossy-rendering path and a `sha` digest, and not one assertion on
any of it. An instrument nothing checks is exactly the thing it warns about —
it will record a blind guard faithfully as having run.

Every defect below is real and each one had the same shape: the log kept
reporting, so nothing looked wrong.

  * **A MODULE RUN AS A SCRIPT IS NOT IN `sys.modules` UNDER ITS OWN NAME.**
    Under `python src/montecarlo.py --city joburg --target 2021 --run-dir
    /tmp/t` — the command `CLAUDE.md` documents for tracing — `montecarlo` is
    `__main__`, nothing in its import closure imports it by name, and every one
    of its own declared constants recorded `not-imported`. Broken on the
    entry point a human uses by hand; correct where `compare_history` runs the
    panel, because that does `import montecarlo as M`. Fixed 2026-08-27 by
    `_module_namespace`; `test_a_module_running_as_main_is_still_found` is what
    stops it coming back, and what stops the fix over-reaching into capturing
    the WRONG module.

  * **A LENGTH IS NOT A VALUE.** `parties.ALIASES` — seventeen ballot-string to
    party-code mappings, read on every raw row inside `run_model`, which decide
    WHAT THE MODEL IS FORECASTING — rendered as `{"__dict__": 17}`. Two
    entirely different alias tables of the same size were indistinguishable in
    the log that exists to prove what a run consulted, and `assert_delivered`
    would have passed a sweep that changed every mapping in it.

  * **A LOG THAT IS NOT JSON BREAKS THE SITE.** `scenario` is dumped with a
    plain `json.dump` and no `default=` hook. A numpy array left on it produced
    malformed JSON and broke the build once already.

  * **A LOG THAT IS TOO BIG IS PAID FOR ON EVERY RUN.** `levels.KNOWN_ABSENT` is
    fourteen entries of prose reason — 5,327 characters of `repr` — and was
    rendered in full into `forecast_summary.json` on every run before the size
    collapse existed.

  * **A FROZEN DEFAULT MUST NEVER PASS AS DELIVERY.** `levels.METRO_CODES` is
    bound in four signatures at import, so rebinding the module attribute moves
    the RECORD and not the COMPUTATION. That is `LEVEL_DF` §1.33 exactly, and it
    cost weeks.

--------------------------------------------------------------------------
THIS FILE WAS WRITTEN RED, AND THE RED DROVE A REAL FIX
--------------------------------------------------------------------------
`test_no_declared_constant_is_silently_frozen_as_a_function_default` FAILED the
moment it was written, on two constants — and it was left failing rather than
excused, because a test weakened to make itself green is the one thing this
suite must never contain. **Both are now in `FROZEN_DEFAULTS` and the test is
green.** What it found:

    montecarlo.HASH_SEED   bound as  fix_hash_seed(seed=)
    polling.REGISTER       bound as  load(path=)

Both are declared in `MODULE_CONSTANTS`, both are captured as a function
default at import, and neither is in `FROZEN_DEFAULTS` — so both record as
`kind="resolved"`, a claim that the value this process holds is the value in
play. It is not. `polling.REGISTER` was checked by rebinding it to a
nonexistent path: `polling.load()` still returned the ten polls from the old
one, and `montecarlo` reaches that binding through `validate_or_die()` on the
model path. `fix_hash_seed()` is called with no argument at all seven of its
call sites.

`polling.REGISTER` is the one that matters. **Pointing the model at a different
poll register is silently ignored** while the read log would faithfully report
the new path — on a channel worth 48 coherent seats at 2026 (§1.65). It was
confirmed independently by rebinding it and watching `load()` return the same
ten polls.

Both are now declared, so this test guards the class rather than the two
instances. Do not excuse a future one in `FROZEN_BINDING_EXCUSED` without an
argument that the record cannot disagree with the computation.

--------------------------------------------------------------------------
WHAT THIS FILE MAY AND MAY NOT ASSERT
--------------------------------------------------------------------------
Everything here is a CONSTRUCTED FIXTURE, and a fixture proves a MECHANISM,
never a MAGNITUDE. Nothing below asserts that a model quantity has a particular
size, and nothing below compares anything to a previous output of this model.
The one number that IS asserted is the size of the log itself, which is a
property of the instrument and not of the forecast.
"""

from __future__ import annotations

import ast
import importlib
import json
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import montecarlo as M  # noqa: E402

# Imported for their side effect on `sys.modules`, which is the whole subject:
# `note_module_constants` reads the LIVE namespace and never imports anything,
# so a module absent from `sys.modules` records `not-imported` for every name it
# declares. A test of the table has to have the table's modules loaded, or it is
# testing the absence and not the record.
import levels  # noqa: E402,F401
import parties  # noqa: E402,F401
import polling  # noqa: E402,F401
import pools  # noqa: E402,F401

# The serialised `_delivered` log measured 8,500 bytes on 2026-08-27 with all
# five modules imported and all 48 names resolving. The ceiling is deliberately
# BELOW what a single un-collapsed constant would cost: `levels.KNOWN_ABSENT`
# alone reprs at 5,327 characters, so rendering it whole again lands near
# 13.8 KB and this budget fails. A ceiling that could not fail on the defect it
# names would be decoration.
DELIVERED_LOG_BUDGET_BYTES = 12_000
DELIVERED_LOG_MEASURED_BYTES = 8_500


def _recorded() -> dict:
    """One `note_module_constants` pass into a fresh scenario, as the log."""
    scenario: dict = {}
    M.note_module_constants(scenario, where="tests/test_delivery_proof.py")
    return scenario


def _names_imported_in_src() -> set[str]:
    """Every top-level module name anything in `src/` imports, from the AST.

    Read from the syntax tree and not by `grep`, because a name inside a
    docstring or a comment is not an import — and half this repository's
    comments discuss imports at length.
    """
    names: set[str] = set()
    for path in sorted((ROOT / "src").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names |= {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names.add(node.module.split(".")[0])
    return names


def _constants_bound_as_function_defaults() -> list[tuple[str, str, str]]:
    """Declared constants captured as a function default, from the AST.

    ``(module, constant, "function(argument=)")`` for every declared name that
    appears as a bare default expression in that module's own source.

    **Read from the syntax tree, NOT by object identity.** The identity version
    of this check was written first and reported two extra hits: `True is True`
    made `polling.aggregate_sd(include_sampling=True)` look like a binding of
    `polling.SIGMA_TWO_TERM`, which is `True`. Bools and small ints are
    singletons and short strings are interned, so identity cannot tell a
    coincidence from a capture — and a false positive in a table of frozen
    defaults is a claim that a live constant is dead, which is the worst
    direction to be wrong in here.
    """
    found: list[tuple[str, str, str]] = []
    for module_name, names in sorted(M.MODULE_CONSTANTS.items()):
        module = sys.modules.get(module_name)
        source = getattr(module, "__file__", None)
        if source is None:
            continue
        tree = ast.parse(Path(source).read_text(encoding="utf-8"), filename=source)
        declared = set(names)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = node.args
            positional = args.posonlyargs + args.args
            padding = [None] * (len(positional) - len(args.defaults))
            pairs = list(zip(positional, padding + list(args.defaults)))
            pairs += list(zip(args.kwonlyargs, args.kw_defaults))
            for arg, default in pairs:
                if isinstance(default, ast.Name) and default.id in declared:
                    found.append((module_name, default.id,
                                  f"{node.name}({arg.arg}=)"))
    return found


# A declared constant bound as a function default that is NOT in
# `FROZEN_DEFAULTS`, with the reason it does not need to be. The bar is the one
# `montecarlo` sets for itself: the record must not be able to disagree with
# the computation ON THE MODEL PATH.
FROZEN_BINDING_EXCUSED: dict[tuple[str, str], str] = {
    ("pools", "METRO_CODES"):
        "the binding is `entrant_record(codes=METRO_CODES)`, and "
        "`entrant_record` is called from ONE place — `pools.emit_pools`, which "
        "runs at `pools.py --emit` and not in a model process. That is the "
        "ARTEFACT-BORNE class montecarlo's own 'DELIBERATELY NOT DECLARED' "
        "note describes, and its delivery proof is the artefact key, not this "
        "table. The read that puts `pools.METRO_CODES` in the table is a LIVE "
        "attribute read at call time — `polling.py:1022` and "
        "`montecarlo.py:3568`, both `PL.METRO_CODES` — which a rebinding does "
        "reach. So the resolved record cannot disagree with the run.",
}


# --------------------------------------------------------------------------
# 1 + 2 — the table names things that exist, on modules that are reachable
# --------------------------------------------------------------------------
def test_every_declared_module_constant_exists_on_its_module():
    """A declared name that no longer exists is a ghost in the register.

    Would have caught: a constant renamed or deleted in `levels.py`,
    `polling.py` or `parties.py` while `MODULE_CONSTANTS` kept naming the old
    spelling. `note_module_constants` records that as `kind="missing"`, which is
    correct and deliberate behaviour — an absence is better than silence — but
    it is a RUNTIME report nobody reads unless they are already suspicious. The
    table itself should carry no ghosts, and the difference between "the log
    said missing" and "the suite went red" is about three weeks.

    Reports every one at once. A first-failure-only test turns a five-name
    rename into five commits.
    """
    ghosts: list[str] = []
    unreachable: list[str] = []
    for module_name, names in sorted(M.MODULE_CONSTANTS.items()):
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:  # covered properly by the next test
            unreachable.append(f"{module_name} ({exc})")
            continue
        ghosts += [f"{module_name}.{n}" for n in names if not hasattr(module, n)]
    assert not unreachable, (
        f"montecarlo.MODULE_CONSTANTS declares module(s) that will not import: "
        f"{unreachable}. Every name under them records `not-imported` on every "
        f"run forever. See test_every_declared_module_is_importable_by_its_"
        f"bare_name for what that costs.")
    assert not ghosts, (
        f"montecarlo.MODULE_CONSTANTS declares {len(ghosts)} name(s) that no "
        f"longer exist on their module: {ghosts}\n"
        f"\n"
        f"  Each writes a `kind=\"missing\"` record into `_delivered` on every "
        f"run — a row in the delivery proof that proves nothing, in a table a "
        f"reader takes as the list of what the model reads.\n"
        f"\n"
        f"  If the constant was RENAMED, rename it here too and say so in "
        f"MODEL-LOG. If it was DELETED, delete the entry. Do NOT leave it: a "
        f"table that carries names the code has dropped is how "
        f"`turnout_tilt_da` stayed on the published page after it left "
        f"`run_model`.")


def test_every_declared_module_is_importable_by_its_bare_name():
    """`note_module_constants` looks a module up by the BARE name it declares.

    Would have caught: a module declared as `src.levels`, or as a name nothing
    ever binds in `sys.modules`. `_module_namespace` returns `None` for it,
    every name under it records `not-imported`, and the log keeps printing — so
    the failure mode is not an error, it is a table of rows that say nothing,
    on every run, forever. That is silent uselessness, and it is worse than a
    crash because it reads as coverage.

    Asserts four things, because "it imported" is not the question. `import
    src.levels` succeeds under this layout — `src/` has no `__init__.py`, so it
    is a namespace package and the import works from the repository root — and
    registers under a name nothing on the model path ever binds. A test that
    only imported would pass on exactly the defect.

    The load-bearing one is the last: SOMETHING IN `src/` MUST IMPORT THE
    MODULE BY THIS NAME. That is what puts the key in `sys.modules`, and it is
    the difference between a name the instrument can resolve and a row that
    says `not-imported` forever.

    **What that check CANNOT establish, said plainly:** whether the module is
    imported during a MODEL RUN, as opposed to anywhere in `src/`. `turnout` is
    left out of the table on exactly that distinction — its only importer
    anywhere is a function-local `import turnout` inside `fold.turnout_weights`,
    reached only from `fold.main`, so it is never in `sys.modules` during a run
    — and a static walk sees that import and would pass it. That question is
    not statically decidable and this test does not pretend to answer it; what
    answers it is reading `45_delivered.json` from a real run and looking for
    `not-imported`.
    """
    imported_in_src = _names_imported_in_src()
    wrong: list[str] = []
    for module_name in sorted(M.MODULE_CONSTANTS):
        if "." in module_name:
            wrong.append(
                f"{module_name}: a DOTTED name. `note_module_constants` looks "
                f"up the bare name the model imports by, and nothing binds "
                f"this one")
            continue
        try:
            module = importlib.import_module(module_name)
        except ImportError as exc:
            wrong.append(f"{module_name}: will not import ({exc})")
            continue
        if sys.modules.get(module_name) is not module:
            wrong.append(f"{module_name}: not in sys.modules under that key")
        elif module.__name__ != module_name:
            wrong.append(
                f"{module_name}: imports as {module.__name__!r} instead")
        elif Path(getattr(module, "__file__", "")).parent != ROOT / "src":
            wrong.append(
                f"{module_name}: resolves to {getattr(module, '__file__', None)}, "
                f"which is not in {ROOT / 'src'} — the name has been shadowed")
        elif module_name not in imported_in_src:
            wrong.append(
                f"{module_name}: nothing in src/ does `import {module_name}`, "
                f"so no run puts it in sys.modules under that key")
    assert not wrong, (
        f"module(s) declared in montecarlo.MODULE_CONSTANTS under a name "
        f"`note_module_constants` cannot resolve: {wrong}\n"
        f"\n"
        f"  It does `sys.modules.get(module_name)` and NEVER imports — "
        f"deliberately, because an import performed for the sake of a log is a "
        f"side effect. So a name that never appears in `sys.modules` is not a "
        f"deferred lookup, it is a permanent `not-imported` record.\n"
        f"\n"
        f"  Declare the module under the name the model imports it by. If a "
        f"module genuinely is not on the run path, it does not belong in the "
        f"table at all — `turnout` is left out for exactly this reason, and the "
        f"reason is written beside it.")


# --------------------------------------------------------------------------
# 3 — the module that is `__main__`
# --------------------------------------------------------------------------
def test_a_module_running_as_main_is_still_found():
    """The defect fixed 2026-08-27, and the over-reach that fixing it invites.

    Would have caught: `sys.modules.get("montecarlo")` returning `None` under
    `python src/montecarlo.py`, so all of `montecarlo`'s own declared constants
    recorded `not-imported` — on the exact command `CLAUDE.md` documents for
    tracing a run. The instrument was blind precisely where a human looks by
    hand, and correct where the panel runs, which is the shape of defect that
    survives review.

    And the other half, which matters as much: the fallback must match on the
    FILE, never on the stem alone in the abstract. Two modules can share a
    basename. Capturing the wrong module's namespace under a declared name
    would write a FALSE delivery proof — a record saying the run read a value
    it never held — and a false proof is worse than a missing one, because the
    whole instrument exists to be believed.

    `sys.modules` is process-global and this suite runs every file in one
    process, so both entries are restored in a `finally`.
    """
    assert M._module_namespace("montecarlo") is sys.modules["montecarlo"], (
        "montecarlo is imported under its own name in this process and "
        "_module_namespace did not return it. The ordinary path is broken.")

    real_module = sys.modules.pop("montecarlo")
    real_main = sys.modules.get("__main__")
    try:
        # (b) the module IS __main__ — the `python src/montecarlo.py` case.
        stand_in = types.ModuleType("__main__")
        stand_in.__file__ = str(ROOT / "src" / "montecarlo.py")
        sys.modules["__main__"] = stand_in
        found = M._module_namespace("montecarlo")
        assert found is stand_in, (
            f"_module_namespace returned {found!r} for `montecarlo` when "
            f"`__main__` IS src/montecarlo.py.\n"
            f"\n"
            f"  This is the 2026-08-27 defect returning. Run "
            f"`.venv/bin/python src/montecarlo.py --city joburg --target 2021 "
            f"--run-dir /tmp/t` and read `45_delivered.json`: every "
            f"`montecarlo.*` row will say `not-imported`, and the trace whose "
            f"entire purpose is to say what the run read will say nothing "
            f"about the module that ran it.")

        # (c) __main__ is a DIFFERENT file — it must refuse, not guess.
        impostor = types.ModuleType("__main__")
        impostor.__file__ = str(Path(__file__).resolve())
        sys.modules["__main__"] = impostor
        assert M._module_namespace("montecarlo") is None, (
            "_module_namespace captured `__main__` as `montecarlo` while "
            "`__main__.__file__` is this test file.\n"
            "\n"
            "  It must match on the FILE. A stem-only or unconditional "
            "fallback records ANOTHER module's namespace under a declared "
            "name, which writes a delivery proof for a value the run never "
            "held. `missing` and `not-imported` are honest answers; a wrong "
            "answer is not, and every downstream reader of `_delivered` takes "
            "this table at its word.")

        # And a `__main__` with no `__file__` at all — an interactive session,
        # or `python -c` — must not crash the instrument or match by accident.
        bare = types.ModuleType("__main__")
        sys.modules["__main__"] = bare
        assert M._module_namespace("montecarlo") is None, (
            "_module_namespace matched a `__main__` that has no `__file__`. "
            "An interactive session or `python -c` must record "
            "`not-imported`, not capture the REPL's namespace as a model "
            "module.")
    finally:
        sys.modules["montecarlo"] = real_module
        if real_main is None:
            sys.modules.pop("__main__", None)
        else:
            sys.modules["__main__"] = real_main


# --------------------------------------------------------------------------
# 4 — a lossy rendering carries a digest
# --------------------------------------------------------------------------
def test_every_lossy_rendering_carries_a_content_digest():
    """A LENGTH IS NOT A VALUE, and the log exists to record values.

    Would have caught: `parties.ALIASES` recorded as `{"__dict__": 17}`.
    Seventeen ballot-string-to-party-code mappings, read on every raw row
    inside `run_model`, deciding what the model is even forecasting — and two
    completely different alias tables of the same size produced an IDENTICAL
    record. `assert_delivered` would have passed a sweep that rewrote every
    mapping in it, and reported a flat result as INERT.

    Checks all four lossy paths, because each was added separately and each can
    lose its digest separately: over sixteen entries, over
    `DELIVERY_MAX_CHARS`, nested past depth 2, and an unknown type.

    Then the part that is the actual guard — a SAME-LENGTH edit must move the
    digest. A digest taken over a count would satisfy the presence check above
    and fail this one.
    """
    wide = {f"k{i:02d}": f"v{i:02d}" for i in range(17)}
    rendered = M._delivery_value(wide)
    assert isinstance(rendered, dict) and rendered.get("__dict__") == 17, (
        f"a 17-entry dict rendered as {rendered!r}; the >16 collapse is the "
        f"path this test is about and it did not take it.")
    assert "sha" in rendered, (
        f"a dict of 17 entries collapsed to {rendered!r} with NO digest. That "
        f"is a length standing in for a value, which is the `parties.ALIASES` "
        f"defect exactly: the delivery proof cannot see a changed table, so "
        f"`assert_delivered` passes a sweep that never arrived.")

    edited = dict(wide)
    edited["k00"] = "w00"          # same key, same length, different content
    after = M._delivery_value(edited)
    assert after.get("sha") != rendered.get("sha"), (
        f"one value changed and the digest did not move: {rendered!r} -> "
        f"{after!r}.\n"
        f"\n"
        f"  A DELIVERY PROOF THAT CANNOT SEE A CHANGED VALUE IS NOT A "
        f"DELIVERY PROOF. If the digest is taken over the count, the shape, or "
        f"anything else that survives an edit, then every constant collapsed "
        f"by this path is unverifiable and a flat sweep over it is VOID, NOT "
        f"NULL. The digest must be taken over the CONTENT, sorted so it is "
        f"stable across processes whatever the hash seed did.")

    # The other three lossy paths. Nothing here asserts a digest VALUE — an
    # object's repr carries its address — only that the evidence is present.
    for label, value in (
            ("over DELIVERY_MAX_CHARS", {"prose": "x" * (M.DELIVERY_MAX_CHARS + 1)}),
            ("nested past depth 2", {"a": {"b": {"c": 1}}}),
            ("an unknown type", object()),
    ):
        shown = M._delivery_value(value)
        if label == "nested past depth 2":
            shown = shown["a"]["b"]
        assert isinstance(shown, dict) and "sha" in shown, (
            f"the {label} path rendered {shown!r} with no digest. Every lossy "
            f"rendering carries one or the collapse is a loss of evidence "
            f"rather than a compression of it.")


# --------------------------------------------------------------------------
# 5 + 6 — the log is JSON, and the log is small
# --------------------------------------------------------------------------
def test_the_delivery_log_is_json_serialisable():
    """`scenario` is dumped with a plain `json.dump` and no `default=` hook.

    Would have caught: a numpy array, a `Path`, a `frozenset` or a tuple-keyed
    dict left on the scenario by a new declared constant. That has already
    happened once — a numpy array on the scenario produced malformed JSON and
    broke the site build — and the failure lands in `build_site.py`, several
    steps downstream of the table that caused it.

    Serialises the WHOLE scenario, not just `_delivered`, because that is what
    `main` does. All five declared modules are imported by this file, so all 48
    names resolve and every rendering path in the table is exercised.
    """
    scenario = _recorded()
    log = scenario["_delivered"]
    assert len(log) == sum(len(v) for v in M.MODULE_CONSTANTS.values()), (
        f"note_module_constants wrote {len(log)} records for "
        f"{sum(len(v) for v in M.MODULE_CONSTANTS.values())} declared names. "
        f"One record per declared name is the contract; a collision means two "
        f"modules are writing under one key and one of them is invisible.")
    try:
        json.dumps(scenario)
    except (TypeError, ValueError) as exc:
        offenders = []
        for name, rec in sorted(log.items()):
            try:
                json.dumps(rec)
            except (TypeError, ValueError):
                offenders.append(name)
        blame = offenders or ["unclear — the failure is elsewhere on the "
                              "scenario, not in a constant record"]
        raise AssertionError(
            f"the delivery log is not JSON: {exc}\n"
            f"\n"
            f"  Record(s) that will not serialise: {blame}\n"
            f"\n"
            f"  `montecarlo.main` writes this with a plain `json.dump` and no "
            f"`default=` hook, so it does not fail here — it emits malformed "
            f"JSON into `forecast_summary.json` and breaks `build_site.py` "
            f"several steps later, where nothing points back at the constant "
            f"that caused it. Teach `_delivery_value` the type; do not add a "
            f"`default=` hook, which would hide the next one.") from exc


def test_the_delivery_log_stays_small():
    """The log rides into `forecast_summary.json` on EVERY run.

    Would have caught: `levels.KNOWN_ABSENT` — fourteen entries of prose reason,
    5,327 characters of `repr` — rendered in full, because it is under the
    sixteen-key limit and the size collapse did not yet exist. Kilobytes of
    diagnostics into a published artefact, on every run, for a constant whose
    value changes about once a month.

    The budget is stated rather than derived, and it is set BELOW the cost of
    re-inlining that one constant so that it can actually fail on the defect it
    names. Raising it is a decision to be made deliberately and written down —
    the same rule as re-recording a golden.
    """
    log = _recorded()["_delivered"]
    size = len(json.dumps(log))
    assert size <= DELIVERED_LOG_BUDGET_BYTES, (
        f"the module-constant delivery log serialises to {size:,} bytes, over "
        f"the {DELIVERED_LOG_BUDGET_BYTES:,}-byte budget. It measured "
        f"{DELIVERED_LOG_MEASURED_BYTES:,} bytes on 2026-08-27 across "
        f"{sum(len(v) for v in M.MODULE_CONSTANTS.values())} declared names.\n"
        f"\n"
        f"  This is paid on every run, into `forecast_summary.json`, which is "
        f"published. The usual cause is a large constant that stopped "
        f"collapsing: check `DELIVERY_MAX_CHARS` and the >16-entry rules in "
        f"`_delivery_value`, and check the digest still stands in for what was "
        f"dropped — a collapse WITHOUT a digest saves the bytes and destroys "
        f"the evidence, which is the wrong half to keep.\n"
        f"\n"
        f"  If the table has legitimately grown, raise the budget in one "
        f"commit that says so. Do not raise it to make a red suite green.")


# --------------------------------------------------------------------------
# 7 — a frozen default is not delivery
# --------------------------------------------------------------------------
def test_frozen_defaults_are_declared_and_recorded_as_frozen():
    """Rebinding a frozen default moves the RECORD and not the COMPUTATION.

    Would have caught: `levels.METRO_CODES` — bound as a function default in
    `theta_record`, `local_record`, `theta_prior` and `spine`, and `run_model`
    passes `codes` to none of them — being recorded as an ordinary `resolved`
    constant. A sweep would rebind the module attribute, watch the log dutifully
    report the new value, get a flat answer, and record a null. That is
    `LEVEL_DF` §1.33 precisely: swept 2.5 to 1000 for byte-identical output,
    over weeks, on the most-attacked constant in the project.

    Also catches a `FROZEN_DEFAULTS` pair naming a constant `MODULE_CONSTANTS`
    does not declare, which is inert — the exception would never be consulted,
    and the constant it was written to protect would be recorded as delivery.
    """
    declared = {(mod, const)
                for mod, names in M.MODULE_CONSTANTS.items() for const in names}
    inert = sorted(pair for pair in M.FROZEN_DEFAULTS if pair not in declared)
    assert not inert, (
        f"montecarlo.FROZEN_DEFAULTS names {inert}, which "
        f"montecarlo.MODULE_CONSTANTS does not declare.\n"
        f"\n"
        f"  The exception is consulted only inside `note_module_constants`, "
        f"and only for names that table walks — so an undeclared pair protects "
        f"nothing at all. Either declare the constant, or delete the pair and "
        f"say why in MODEL-LOG. A dead exception on a live defect reads as "
        f"protection.")

    scenario = _recorded()
    log = scenario["_delivered"]
    for module_name, const in sorted(M.FROZEN_DEFAULTS):
        name = f"{module_name}.{const}"
        rec = log.get(name)
        assert rec is not None, (
            f"{name} is in FROZEN_DEFAULTS and its module is imported, and "
            f"note_module_constants wrote no record for it at all.")
        assert rec["kinds"] == ["resolved-frozen"], (
            f"{name} was recorded as {rec['kinds']!r} and must be "
            f"['resolved-frozen'].\n"
            f"\n"
            f"  It is captured as a function default at import, so rebinding "
            f"the module attribute — which is exactly what a sweep does — "
            f"moves this record and NOT the computation. Recorded under any "
            f"other kind, the log agrees with the sweep while the model "
            f"disagrees with both, and the flat answer that follows gets "
            f"written down as INERT.")

        # And the kind must actually REFUSE the strong claim. A distinct label
        # that `assert_delivered` still accepts is a label and not a guard.
        try:
            M.assert_delivered(scenario, name, kind="consulted")
        except M.Undelivered as exc:
            assert "VOID, NOT NULL" in str(exc), (
                f"assert_delivered refused the frozen record for {name} "
                f"without saying the result is VOID rather than NULL. The "
                f"words are the deliverable: a reader who takes this for a "
                f"null writes an EXPECTED_INERT entry, and this project has "
                f"retracted two of those already.")
        else:
            raise AssertionError(
                f"assert_delivered(..., kind=\"consulted\") ACCEPTED the "
                f"`resolved-frozen` record for {name}.\n"
                f"\n"
                f"  A frozen default is the one thing that must never pass as "
                f"delivery. Nothing read it at that value — the value the code "
                f"used was captured in a signature at import time — so a "
                f"`consulted` claim over it is false, and every sweep that "
                f"leans on it is measuring a configuration it did not set.")


def test_no_declared_constant_is_silently_frozen_as_a_function_default():
    """`FROZEN_DEFAULTS` is a hand-written list, and the code moves under it.

    Would have caught — and DOES catch, see below — a declared constant that
    becomes a function default without anyone adding it to `FROZEN_DEFAULTS`.
    The test above iterates `FROZEN_DEFAULTS`, so it says nothing at all about
    a pair that was never added: empty the frozenset and it passes. That is the
    same hole as `EXPECTED_INERT` before the `Null` record — the register can
    only be wrong in the direction nobody enumerates.

    So enumerate it from the source instead. Every declared name bound as a
    bare function default is a candidate, and every candidate must either be in
    `FROZEN_DEFAULTS` or carry a reason in `FROZEN_BINDING_EXCUSED` saying why
    the record cannot disagree with the computation.

    This is `LEVEL_DF` §1.33 as a standing check rather than a memory: bound as
    a default argument, evaluated once at import, swept at 2.5, 4, 7, 30, 200
    and 1000 for BYTE-IDENTICAL output, over weeks, on the most-attacked
    constant in the project.
    """
    candidates = _constants_bound_as_function_defaults()
    assert candidates, (
        "no declared constant is bound as a function default anywhere, which "
        "cannot be right while FROZEN_DEFAULTS is non-empty — the AST walk has "
        "stopped finding what it is for. Check `_constants_bound_as_function_"
        "defaults` against the current source layout before trusting a green "
        "run of this test.")

    unguarded: dict[tuple[str, str], list[str]] = {}
    for module_name, const, site in candidates:
        pair = (module_name, const)
        if pair in M.FROZEN_DEFAULTS or pair in FROZEN_BINDING_EXCUSED:
            continue
        unguarded.setdefault(pair, []).append(site)

    stale = sorted(pair for pair in FROZEN_BINDING_EXCUSED
                   if pair not in {(m, c) for m, c, _ in candidates})
    assert not stale, (
        f"FROZEN_BINDING_EXCUSED excuses {stale}, which is no longer bound as "
        f"a function default anywhere. The excuse has outlived the binding: "
        f"delete it, so the table stays a list of live decisions rather than a "
        f"graveyard nobody rereads.")

    lines = "\n".join(
        f"    {mod}.{const}  bound as  {', '.join(sorted(set(sites)))}"
        for (mod, const), sites in sorted(unguarded.items()))
    assert not unguarded, (
        f"{len(unguarded)} declared module constant(s) are captured as a "
        f"FUNCTION DEFAULT at import and are NOT in "
        f"montecarlo.FROZEN_DEFAULTS:\n\n{lines}\n\n"
        f"  Each is recorded on every run as kind=\"resolved\", which asserts "
        f"that the value THIS PROCESS HOLDS is the value in play. For a frozen "
        f"default that is not true: the value the code uses was captured in a "
        f"signature at import time, so rebinding the module attribute — which "
        f"is exactly what a sweep does — MOVES THE RECORD AND NOT THE "
        f"COMPUTATION. The log then agrees with the sweep while the model "
        f"disagrees with both, and the flat answer that follows gets written "
        f"down as INERT. That is MODEL-LOG §1.33 and it cost weeks.\n"
        f"\n"
        f"  Two fixes, and only the second is free:\n"
        f"    * make the read live — resolve the constant in the body rather "
        f"than in the signature, which is what was done to `LEVEL_DF`; or\n"
        f"    * add the pair to `montecarlo.FROZEN_DEFAULTS`, so it records as "
        f"`resolved-frozen` and `assert_delivered(kind=\"consulted\")` refuses "
        f"it.\n"
        f"\n"
        f"  If the binding genuinely cannot mislead — because it is off the "
        f"model path, or because every caller passes the argument — say so in "
        f"`FROZEN_BINDING_EXCUSED` in this file, with the call sites. An "
        f"unexplained absence from a table of frozen defaults reads as a "
        f"statement that the constant is live, and this project has twice "
        f"retracted a null taken on that reading.")


# --------------------------------------------------------------------------
# 8 — assert_delivered refuses a value that was not the one set
# --------------------------------------------------------------------------
def test_assert_delivered_refuses_a_value_the_run_did_not_consult():
    """The assertion NULL-RESULTS.md §4.1 requires on every sweep.

    Would have caught: `assert_delivered` degenerating into a presence check —
    passing because the NAME is in the log, whatever value the run actually
    read. A sweep sets `LEVEL_DF = 1000`, something upstream overwrites it (a
    city TOML, `apply_city`, a scenario file, a default argument resolved at
    import), the run reads 4.0, the score does not move, and the null is
    recorded as a fact about the model. It is not a fact about the model. The
    measurement did not happen.

    This is a mechanism test on a fixture log: it asserts that the wrong value
    is REFUSED and the right one ACCEPTED, and asserts nothing whatever about
    any model quantity.
    """
    scenario: dict = {}
    M.note_value(scenario, "fixture.CONSTANT", 1.0,
                 where="tests/test_delivery_proof.py:fixture", kind="consulted")

    rec = M.assert_delivered(scenario, "fixture.CONSTANT", 1.0, kind="consulted")
    assert rec["reads"] == 1, (
        f"the fixture recorded {rec['reads']} read(s) of one note_value call; "
        f"`reads` is what tells a reader whether a site fired at all.")

    try:
        M.assert_delivered(scenario, "fixture.CONSTANT", 2.0)
    except M.Undelivered as exc:
        text = str(exc)
    else:
        raise AssertionError(
            "assert_delivered PASSED a value the run never consulted: the log "
            "records 1.0 and 2.0 was asserted.\n"
            "\n"
            "  It has degenerated into a presence check. Every sweep in this "
            "repository that calls it is then proving only that a name is in "
            "the log, and a flat result under that proof is VOID, NOT NULL — "
            "which is the confusion the whole instrument exists to end.")
    for phrase in ("UNDELIVERED", "VOID, NOT NULL", "fixture.CONSTANT",
                   "tests/test_delivery_proof.py:fixture"):
        assert phrase in text, (
            f"the Undelivered message does not contain {phrase!r}. The error "
            f"TEXT is the deliverable here, not the exception type: it has to "
            f"name the constant, name the site that read it, and say in words "
            f"that the result is VOID rather than NULL — because the reader is "
            f"someone holding a flat sweep who is about to write it up as "
            f"INERT.\n\nWhat it said instead:\n{text}")

    # An unknown name is the other half, and it must fail LOUDLY rather than
    # returning an empty record that a caller reads as success.
    try:
        M.assert_delivered(scenario, "fixture.NEVER_READ")
    except M.Undelivered as exc:
        assert "VOID, NOT NULL" in str(exc), (
            "assert_delivered refused an unrecorded name without saying the "
            "result is VOID rather than NULL.")
    else:
        raise AssertionError(
            "assert_delivered returned a record for a name the log has never "
            "heard of. An absent name is the single most common way a sweep "
            "fails to arrive — a module constant rebound in the parent process "
            "does not cross a ProcessPoolExecutor boundary — and it must raise, "
            "not return.")


if __name__ == "__main__":
    # `run_module`, NOT a hand-rolled loop: it is the only runner that catches
    # `SkipTest` and `SystemExit`, and five files in this suite once aborted on
    # their first skip with no summary printed. MODEL-LOG §1.84.
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
