"""One index of every lever, constant, fold, window and method, JOINED.

    .venv/bin/python src/model_index.py           # write MODEL-INDEX.md
    .venv/bin/python src/model_index.py --stdout  # print it instead

⛔ THE INDEX IS GENERATED. DO NOT EDIT `MODEL-INDEX.md` BY HAND.
`tests/test_model_index.py` regenerates it into a scratch path and compares, so
a hand edit is a red suite, not a silent divergence. CLAUDE.md §2: a number
lives where it was generated.

WHY A JOIN AND NOT A DOCUMENT
-----------------------------
This repository already keeps a dozen registers — the scenario defaults, the
module-constant delivery table, the inert-lever nulls, the deleted-lever
exemptions, the entry-point allowlist, the backtest provenance classes, the
judgement register, the intermediates' producer table. **Nothing joins them.**
Every register is internally consistent and the gaps live BETWEEN them: a name
in one and not another, an exemption that no longer exempts anything, a claim
about a producer that the code contradicts, two names for one statistic.

That is not a hypothesis. `tests/test_register_matches_code` records the case:
the judgement register carried a row marked *"still wired"* for a pair of levers
that had been deleted, and every guard passed, because each guard checked one
direction of one register. The reverse direction was written and the row fell
over the same day. This module generalises that move — it walks every register
this repository has, and reports the names each one does NOT share with the
others.

WHAT IT READS, AND WHAT IT DELIBERATELY DOES NOT
------------------------------------------------
Reads: the syntax trees of `src/*.py` and `tests/*.py`, the register objects
themselves (imported, so a register is never re-typed here), and
`JUDGEMENT-CALLS.md`. It reads **nothing under `data/`** — those artefacts are
gitignored, so an index derived from them could not be regenerated on a clean
checkout and the drift test would go red for the wrong reason.

⛔ IT WRITES NO LINE NUMBERS, ON EVIDENCE. `test_register_matches_code` bans
them from the judgement register because 24 citations had all gone stale by 34
to 375 lines. That ban covers one file; the allowlist in
`tests/test_standalone_modules.py` cites line numbers and two of them have
already rotted (see the entry-point section below). A name does not drift.

⚠️ WHAT AN ENTRY HERE IS AND IS NOT. A row saying a name is read in one module
is an AST fact about references, not a claim that a run reaches it — that is
`montecarlo.MODULE_CONSTANTS` and the delivery proof's job, and where the two
disagree the delivery proof is right. A row saying nothing references a name IS
strong: an unreferenced name cannot be read by anything.

⛔ AND THIS FILE IS NOT INERT MERELY BECAUSE IT IS READ-ONLY.
`test_register_matches_code._defined_names` harvests every **string literal** in
`src/` into the population it checks the judgement register against, so a module
here that merely NAMED a deleted lever in a docstring would make that name
"defined" and quietly retire the `DELETED` clause — the identical self-pollution
that file measured and repaired on 2026-08-31. Nothing in this module names a
lever as a literal: every name it prints is read out of a register at run time.
`tests/test_model_index.py` holds the measurement that the clause is still
load-bearing with this file in the tree.
"""

from __future__ import annotations

import argparse
import ast
import importlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
TESTS = ROOT / "tests"
JUDGEMENT_REGISTER = ROOT / "JUDGEMENT-CALLS.md"
OUTPUT = ROOT / "MODEL-INDEX.md"

# The entry points of the two graphs the index reports membership of. Module
# names, not values -- `montecarlo` is what a forecast runs through and
# `compare_history` is what scores it, and every module either is reachable
# from one of them or is not part of either job.
MODEL_ROOT = "montecarlo"
MEASUREMENT_ROOT = "compare_history"

# Substrings that make a name a FOLD or a WINDOW rather than a level: a span of
# time or of history that some estimate is fitted over. Matched against the
# upper-cased name, so `theta_window` and `THETA_WINDOW` are the same question.
# How much source a function may hold and still be read as an apportionment
# rather than a pipeline. A largest-remainder allocation is a handful of lines;
# `run_model` is not one, whatever it contains.
MAX_APPORTIONMENT_CHARS = 3000
# How much of an expression to print where a constant is not a literal.
MAX_EXPRESSION_CHARS = 72
# The shortest literal piece of a filename glob worth matching on. Anything
# shorter matches half the tree.
MIN_GLOB_FRAGMENT = 6

SPAN_MARKERS = ("FOLD", "WINDOW", "HALF_LIFE", "_DAYS", "_MONTHS", "_YEARS",
                "TAU", "RECENT", "CAMPAIGN", "LAG", "SPAN", "HORIZON")


# ---------------------------------------------------------------------------
# Syntax: the trees, the import graph, and who references what
# ---------------------------------------------------------------------------

def _trees(directory: Path) -> dict[str, ast.Module]:
    return {p.stem: ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
            for p in sorted(directory.glob("*.py"))}


def _imports(tree: ast.Module, universe: set[str]) -> set[str]:
    """Module names from `universe` that this tree imports, at any depth.

    `ast.walk`, not `tree.body`: a large share of this repository's imports sit
    inside a function, a `try:` or an `if`, and `test_standalone_modules` makes
    the same point about the same graph.
    """
    got: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            got |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            got.add(node.module.split(".")[0])
    return got & universe


def _closure(start: str, edges: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        here = stack.pop()
        if here in seen:
            continue
        seen.add(here)
        stack.extend(edges.get(here, ()))
    return seen


def _references(trees: dict[str, ast.Module]) -> dict[str, set[str]]:
    """name -> the modules that mention it as an identifier OR a string.

    Both, because a scenario key exists in `src/` only as a string literal --
    `scenario.get(...)` binds nothing -- while a module constant exists only as
    an identifier. A table that harvested one kind would report every lever as
    unread or every constant as unread.
    """
    out: dict[str, set[str]] = {}
    for name, tree in trees.items():
        for node in ast.walk(tree):
            token = None
            if isinstance(node, ast.Name):
                token = node.id
            elif isinstance(node, ast.Attribute):
                token = node.attr
            elif isinstance(node, ast.arg):
                token = node.arg
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                token = node.value
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                   ast.ClassDef)):
                token = node.name
            if token:
                out.setdefault(token, set()).add(name)
    return out


def _top_level(tree: ast.Module):
    """(name, node) for every top-level def, class and assignment."""
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            yield node.name, node
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield target.id, node
                elif isinstance(target, ast.Tuple):
                    for element in target.elts:
                        if isinstance(element, ast.Name):
                            yield element.id, node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            yield node.target.id, node


def _summary(node) -> str:
    """The first line of a docstring, flattened, or an empty string."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Module)):
        return ""
    text = ast.get_docstring(node) or ""
    first = text.strip().split("\n")[0].strip()
    return re.sub(r"\s+", " ", first)


def _kind(node) -> str:
    """What a top-level assignment binds, without printing a moving value."""
    value = getattr(node, "value", None)
    if value is None:
        return "?"
    try:
        literal = ast.literal_eval(value)
    except (ValueError, SyntaxError, TypeError):
        # The EXPRESSION, not the node class. `Call` says nothing; the source
        # says `_env_int("THETA_WINDOW", ...)`, which is the whole answer to
        # where a window comes from.
        return ast.unparse(value)[:MAX_EXPRESSION_CHARS]
    if isinstance(literal, bool):
        return f"bool {literal}"
    if isinstance(literal, (int, float)):
        return f"{type(literal).__name__} {literal!r}"
    if isinstance(literal, str):
        return f"str {literal!r}" if len(literal) <= 24 else "str"
    if isinstance(literal, (list, tuple, set, dict, frozenset)):
        return f"{type(literal).__name__}[{len(literal)}]"
    return type(literal).__name__


# ---------------------------------------------------------------------------
# The registers. Imported, never retyped.
# ---------------------------------------------------------------------------

def _load_registers() -> dict[str, object]:
    """Every register this repository keeps, as live objects.

    Imported through `importlib` rather than a static `import`, so that the
    AST-based import graphs in `tests/` -- which read `ast.Import` nodes -- do
    not gain an edge from `src/` into `tests/` merely because the index reads a
    register that happens to live in a test file. The edge would be real and it
    would be misleading: nothing here executes a test.
    """
    for extra in (str(SRC), str(TESTS)):
        if extra not in sys.path:
            sys.path.insert(0, extra)
    got: dict[str, object] = {}
    for module_name, names in (
            ("montecarlo", ("DEFAULTS", "MODULE_CONSTANTS")),
            ("pools", ("ARRIVAL_DEFINITIONS",)),
            ("fold", ("FOLDS",)),
            ("backtest", ("FITTED_ON", "FITTED_ON_UNINSTRUMENTED",
                          "PROVENANCE_UNSETTLED", "NOT_FITTED")),
            ("freeze", ("ENV_SWITCHES",)),
            ("test_levers_are_live", ("EXPECTED_INERT", "CONDITIONAL",
                                      "MODULE_PERTURB", "GATES",
                                      "GATE_OPEN_AT")),
            ("test_register_matches_code", ("DELETED", "STILL_IN_THE_TREE",
                                            "UNRESOLVED_LIVE_CLAIMS")),
            ("test_standalone_modules", ("ENTRY_POINTS",)),
            ("test_intermediates_are_current", ("NOT_GENERATED_HERE",
                                                "NOT_REGENERATED_HERE",
                                                "TRANSIENT")),
    ):
        module = importlib.import_module(module_name)
        for name in names:
            got[name] = getattr(module, name)
            got.setdefault("_home", {})
            got["_home"][name] = module_name          # type: ignore[index]
    return got


def _register_symbols() -> set[str]:
    """Bare backticked identifiers in the judgement register, strikes removed.

    The same reading `test_register_matches_code` takes, for the same reason: a
    struck-through row is an obituary and its symbol is supposed to be gone.
    """
    text = re.sub(r"~~.*?~~", "", JUDGEMENT_REGISTER.read_text(encoding="utf-8"), flags=re.S)
    return {token for token in re.findall(r"`([^`]+)`", text)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token.strip())}


# ---------------------------------------------------------------------------
# The join
# ---------------------------------------------------------------------------

def build() -> dict:
    """Every register, every syntax fact, joined into one plain structure.

    Returns a dictionary of tables. `render` turns it into the document; a test
    can assert on it without parsing markdown.
    """
    src, tests = _trees(SRC), _trees(TESTS)
    universe = set(src)
    edges = {name: _imports(tree, universe) - {name} for name, tree in src.items()}

    importers: dict[str, set[str]] = {name: set() for name in src}
    for where, trees in (("src", src), ("tests", tests)):
        for name, tree in trees.items():
            for target in _imports(tree, universe):
                if target != name:
                    importers[target].add(f"{where}/{name}")

    model = _closure(MODEL_ROOT, edges)
    measurement = _closure(MEASUREMENT_ROOT, edges)
    refs_src = _references(src)
    refs_tests = _references(tests)
    reg = _load_registers()
    registered = _register_symbols()

    index: dict = {
        "modules": _modules(src, importers, model, measurement, reg),
        "levers": _levers(src, refs_src, reg, registered),
        "constants": _constants(src, refs_src, reg, registered),
        "spans": _spans(src, reg),
        "methods": _methods(src, model, measurement, refs_src, refs_tests),
        "collisions": _collisions(src),
        "inert": _inert(src, importers, refs_src, refs_tests, reg, registered),
        "guards": _guards(tests, reg),
        "producers": _producers(src, reg),
    }
    return index


def _modules(src, importers, model, measurement, reg) -> list[dict]:
    entry_points = reg["ENTRY_POINTS"]
    rows = []
    for name, tree in sorted(src.items()):
        role = []
        if name in model:
            role.append("model")
        if name in measurement:
            role.append("measurement")
        rows.append({
            "module": name,
            "role": "+".join(role) or "neither",
            "importers": sorted(importers[name]),
            "entry_point": name in entry_points,
            "public_defs": sorted(
                n.name for n in tree.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not n.name.startswith("_")),
            "summary": _summary(tree),
        })
    return rows


def _levers(src, refs, reg, registered) -> list[dict]:
    defaults = reg["DEFAULTS"]
    inert_at = {}
    for (lever, target) in reg["EXPECTED_INERT"]:
        inert_at.setdefault(lever, []).append(target)
    conditional = {}
    for key in reg["CONDITIONAL"]:
        lever, _, target = key.partition("@")
        conditional.setdefault(lever, []).append(target)
    provenance = {}
    for register_name in ("FITTED_ON", "FITTED_ON_UNINSTRUMENTED",
                          "PROVENANCE_UNSETTLED", "NOT_FITTED"):
        for lever in reg[register_name]:
            provenance.setdefault(lever, []).append(register_name)

    text = {name: (SRC / f"{name}.py").read_text(encoding="utf-8")
            for name in src}
    rows = []
    for lever in sorted(defaults):
        shadow = _shadow_for(lever, src)
        rows.append({
            "lever": lever,
            "default": _value(defaults[lever]),
            "provenance": sorted(provenance.get(lever, [])) or ["--"],
            "inert_at": sorted(inert_at.get(lever, [])),
            "conditional_at": sorted(conditional.get(lever, [])),
            "registered": lever in registered,
            "read_in": sorted(refs.get(lever, set())),
            "shadow": shadow,
            "shadow_tied": _shadow_tied(lever, shadow, text),
        })
    return rows


def _value(value) -> str:
    if isinstance(value, (dict, list, tuple, set)):
        return f"{type(value).__name__}[{len(value)}]"
    return repr(value)


def _shadow_for(lever: str, src) -> str:
    """The module constant whose name is this lever's, upper-cased, if any.

    A shadow is not a defect by itself -- the model reads the scenario key and
    the constant is the value the key defaults to -- but an UNTIED shadow is:
    two places hold the same number and nothing makes them agree.
    """
    wanted = lever.upper()
    found = []
    for module, tree in sorted(src.items()):
        for name, _node in _top_level(tree):
            if name == wanted:
                found.append(f"{module}.{name}")
    return ", ".join(found)


def _shadow_tied(lever: str, shadow: str, text: dict[str, str]) -> bool:
    """Is there a statement anywhere in `src/` that asserts the two are equal?

    Looks for an `assert` whose source mentions both the constant and the key.
    `montecarlo` does exactly this for the poll half-life, on evidence -- the
    register documented a constant that was not there -- so the shape is the
    repository's own, not an invention here.
    """
    if not shadow:
        return False
    constant = lever.upper()
    for module, body in text.items():
        try:
            tree = ast.parse(body)
        except SyntaxError:                                  # pragma: no cover
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assert):
                continue
            rendered = ast.unparse(node)
            if constant in rendered and lever in rendered:
                return True
    return False


def _constants(src, refs, reg, registered) -> list[dict]:
    declared = {f"{module}.{name}"
                for module, names in reg["MODULE_CONSTANTS"].items()
                for name in names}
    swept = {f"{entry[0]}.{entry[1]}" for entry in reg["MODULE_PERTURB"]}
    rows = []
    for module, tree in sorted(src.items()):
        for name, node in _top_level(tree):
            if not name.isupper() or name.startswith("_"):
                continue
            qualified = f"{module}.{name}"
            readers = sorted(refs.get(name, set()) - {module})
            rows.append({
                "constant": qualified,
                "kind": _kind(node),
                "delivered": qualified in declared,
                "swept": qualified in swept,
                "registered": name in registered,
                "read_elsewhere": readers,
            })
    return rows


def _spans(src, reg) -> list[dict]:
    """Folds and windows: the spans of history an estimate is fitted over."""
    rows = []
    for lever in sorted(reg["DEFAULTS"]):
        if any(marker in lever.upper() for marker in SPAN_MARKERS):
            rows.append({"name": lever, "where": "montecarlo.DEFAULTS",
                         "value": _value(reg["DEFAULTS"][lever]), "spans": ""})
    for module, tree in sorted(src.items()):
        for name, node in _top_level(tree):
            if not name.isupper() or name.startswith("_"):
                continue
            if any(marker in name for marker in SPAN_MARKERS):
                rows.append({"name": name, "where": module,
                             "value": _kind(node), "spans": ""})
    for key, fold in sorted(reg["FOLDS"].items()):
        rows.append({"name": f"FOLDS[{key!r}]", "where": "fold",
                     "value": "", "spans": _fields(fold)})
    for name, definition in sorted(reg["ARRIVAL_DEFINITIONS"].items()):
        rows.append({"name": name, "where": "pools.ARRIVAL_DEFINITIONS",
                     "value": "", "spans": _fields(definition)})
    return rows


def _fields(obj) -> str:
    """Whatever an object declares about itself, without knowing its type.

    A fold is a dict here and an arrival definition is a dataclass, and both
    are read the same way on purpose: naming the fields would put a copy of
    their shape in this module, where it would go stale the first time either
    gained one.
    """
    import dataclasses
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        pairs = [(f.name, getattr(obj, f.name))
                 for f in dataclasses.fields(obj)]
    elif isinstance(obj, dict):
        pairs = sorted(obj.items())
    else:
        return repr(obj)
    return "; ".join(f"{k}={v!r}" for k, v in pairs)


def _methods(src, model, measurement, refs_src, refs_tests) -> list[dict]:
    """Every public function on the measurement or model path, with callers.

    The population is a DERIVED one -- the import closures of the two entry
    points -- rather than a list of statistical methods somebody remembered.
    A method that is not in either closure is not invoked by a forecast or by
    the scoring of one, whatever its name suggests.
    """
    rows = []
    for module in sorted(model | measurement):
        tree = src[module]
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_") or node.name == "main":
                continue
            callers = sorted((refs_src.get(node.name, set()) - {module})
                             | {f"tests/{t}" for t
                                in refs_tests.get(node.name, set())})
            rows.append({
                "function": f"{module}.{node.name}",
                "path": ("model+measurement" if module in model and module in measurement
                         else "model" if module in model else "measurement"),
                "summary": _summary(node),
                "callers": callers,
            })
    return rows


# ---------------------------------------------------------------------------
# Collisions -- two names for one thing, or one name for two
# ---------------------------------------------------------------------------

def _collisions(src) -> dict:
    return {
        "alias_families": _alias_families(src),
        "shared_names": _shared_names(src),
        "repeated_values": _repeated_values(src),
        "apportionment": _apportionment_sites(src),
    }


def _defined_functions(src) -> set[str]:
    """Functions this repository defines. Classes are excluded on purpose.

    A dict of constructor calls is a table of records, not one computation
    reported under several names, and including classes buried the statistics
    under the roster tables.
    """
    names: set[str] = set()
    for tree in src.values():
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


def _alias_families(src) -> list[dict]:
    """One computation, reported under several names, in one dict literal.

    ⛔ THIS IS THE `seat_abs_err` SHAPE, and it is why the detector exists: a
    reported key whose value is a call to a function of the SAME NAME, sitting
    beside a second key calling the same function on a DIFFERENT argument. The
    two keys are then two statistics wearing one name plus a suffix, and a
    summary that adds them, or quotes one as the other, is wrong in a way no
    arithmetic test can see.

    Restricted to functions this repository defines. A family built out of
    `len`, `int` or `dict.get` is a shape, not a statistic.
    """
    ours = _defined_functions(src)
    rows = []
    for module, tree in sorted(src.items()):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            family: dict[str, list[str]] = {}
            for key, value in zip(node.keys, node.values):
                if not (isinstance(key, ast.Constant)
                        and isinstance(key.value, str)):
                    continue
                if not isinstance(value, ast.Call):
                    continue
                func = value.func
                called = (func.id if isinstance(func, ast.Name)
                          else func.attr if isinstance(func, ast.Attribute)
                          else None)
                if called in ours:
                    family.setdefault(called, []).append(key.value)
            for called, keys in sorted(family.items()):
                if len(keys) >= 2:
                    rows.append({"module": module, "function": called,
                                 "keys": sorted(set(keys))})
    unique = {(r["module"], r["function"], tuple(r["keys"])): r for r in rows}
    return [unique[k] for k in sorted(unique)]


def _shared_names(src) -> list[dict]:
    """One name, defined at the top level of more than one module.

    Both halves matter. Two constants of one name holding DIFFERENT values are
    a trap -- `METRO_CODES` is the repository's own example, two modules, same
    eight codes, different order, and `montecarlo.MODULE_CONSTANTS` says so in
    a comment. Two functions of one name are a reader hazard even when both are
    correct.
    """
    where: dict[str, list[str]] = {}
    values: dict[str, set[str]] = {}
    for module, tree in sorted(src.items()):
        for name, node in _top_level(tree):
            if name.startswith("_") or name == "main":
                continue
            where.setdefault(name, []).append(module)
            values.setdefault(name, set()).add(_kind(node))
    rows = []
    for name, modules in sorted(where.items()):
        if len(modules) < 2:
            continue
        rows.append({"name": name, "modules": sorted(modules),
                     "kinds": sorted(values[name]),
                     "same_kind": len(values[name]) == 1})
    return rows


def _repeated_values(src) -> list[dict]:
    """One number, typed under two names -- a constant that cannot be updated.

    CLAUDE.md §2: a number copied into a second place cannot be updated, only
    updated in the copies someone remembers. `stats.DECLARATION_MIN_CHARS`
    exists because the same bare value was written twice for two different
    fields; this finds the survivors of that shape mechanically.

    Small integers and the obvious identities are excluded: 0 and 1 and the
    like are structure, not belief, and a table of them would bury the rest.
    """
    seen: dict[object, list[str]] = {}
    for module, tree in sorted(src.items()):
        for name, node in _top_level(tree):
            if not name.isupper() or name.startswith("_"):
                continue
            value = getattr(node, "value", None)
            if value is None:
                continue
            try:
                literal = ast.literal_eval(value)
            except (ValueError, SyntaxError, TypeError):
                continue
            if isinstance(literal, bool) or not isinstance(literal, (int, float)):
                continue
            if abs(literal) <= 1 and float(literal).is_integer():
                continue
            seen.setdefault(literal, []).append(f"{module}.{name}")
    return [{"value": repr(value), "names": sorted(names)}
            for value, names in sorted(seen.items(), key=lambda kv: repr(kv[0]))
            if len(set(names)) >= 2]


def _apportionment_sites(src) -> list[dict]:
    """Every function that turns a real vector into integers summing to a total.

    ⛔ THE SECOND CALIBRATION CASE, AND IT IS A STRUCTURAL FINGERPRINT RATHER
    THAN A WORD SEARCH. Largest-remainder apportionment has one shape whatever
    it is called: take the whole part, rank what is left over, and hand the
    shortfall out down that ranking. So the detector asks for the shape -- a
    floor or an integer division, an ordering, and either an increment or a
    top-k slice -- and not for the phrase "largest remainder", which appears in
    the docstrings of modules that only DISCUSS it.

    Two sites is the expected reading, and they are not the same algorithm:
    one strikes a quota and breaks ties on the larger vote total, the other
    rescales to a fixed council and breaks ties on the sort's own order. Which
    is to say the tie rule differs, and only one of them has ever been proved
    against a published council.
    """
    rows = []
    for module, tree in sorted(src.items()):
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            rendered = _source_without_strings(node)
            if len(rendered) > MAX_APPORTIONMENT_CHARS:
                continue
            whole = ("floor" in rendered or "//" in rendered
                     or "astype(int)" in rendered or "int(" in rendered)
            ordered = ("argsort" in rendered or "sorted(" in rendered
                       or ".sort(" in rendered)
            handed_out = ("+= 1" in rendered
                          or re.search(r"\[:[A-Za-z_]", rendered))
            if whole and ordered and handed_out:
                rows.append({"function": f"{module}.{node.name}",
                             "summary": _summary(node),
                             "ties": _tie_rule(rendered)})
    return rows


class _Unstring(ast.NodeTransformer):
    """Replace every string constant with an empty one.

    ⛔ WITHOUT THIS THE FINGERPRINT MATCHES PROSE. `ast.unparse` reproduces
    docstrings, error messages and f-strings, and this repository writes long
    ones: a function whose only `sorted(` is inside an assertion message scored
    as an apportionment site until the strings were stripped.
    """

    def visit_Constant(self, node):                       # noqa: N802
        if isinstance(node.value, str):
            return ast.Constant(value="")
        return node


def _source_without_strings(node) -> str:
    import copy
    return ast.unparse(_Unstring().visit(copy.deepcopy(node)))


def _tie_rule(rendered: str) -> str:
    """How the shortfall is ordered, read off the source of the ordering call.

    The ordering that DECIDES the shortfall is the one carrying a key or an
    `argsort`; a bare `sorted(...)` earlier in the same function is usually
    just putting the party list in a stable order. Preferring the keyed call
    is what makes the tie rule comparable between two implementations, which
    is the only reason this column exists.
    """
    found = re.findall(r"(?:sorted|argsort)\([^\n]*", rendered)
    if not found:
        return ""
    keyed = [f for f in found if "key=" in f or "argsort" in f]
    chosen = (keyed or found)[0]
    return re.sub(r"\s+", " ", chosen).rstrip("):, ")[:120]


# ---------------------------------------------------------------------------
# The dead: exemptions that no longer exempt anything
# ---------------------------------------------------------------------------

def _inert(src, importers, refs_src, refs_tests, reg, registered) -> dict:
    """For every exemption this repository keeps, does it still exempt anything?

    ⛔ THE ONE SWEEP NOTHING IN THE TREE DOES, and the generalisation of the
    incident that produced `tests/test_register_matches_code`. An exemption
    list is a claim that something needs excusing; when the thing it excused is
    gone, the entry sits there ready to excuse the next name that happens to
    collide with it, and every guard stays green. That file measured exactly
    this about its own `DELETED` table -- all 18 names were in the harvested
    population, so removing the clause changed the verdict from 0 offenders to
    0 offenders -- and repaired it. Every other exemption table in the
    repository is asserted in only one direction or in none.
    """
    everywhere = set(refs_src) | set(refs_tests)
    return {
        "deleted": [
            {"name": name,
             "named_by_register": name in registered,
             "still_referenced": sorted(refs_src.get(name, set()))}
            for name in sorted(reg["DELETED"])],
        "still_in_the_tree": [
            {"name": name, "present": name in everywhere,
             "where": sorted(refs_src.get(name, set()))}
            for name in sorted(reg["STILL_IN_THE_TREE"])],
        "unresolved_live_claims": sorted(reg["UNRESOLVED_LIVE_CLAIMS"]),
        "entry_points": [
            {"module": name,
             "importers": sorted(importers.get(name, ())),
             "still_needed": not importers.get(name)}
            for name in sorted(reg["ENTRY_POINTS"])],
        "gates_open_at": sorted(f"{gate}@{target}"
                                for gate, target in reg["GATE_OPEN_AT"]),
        "gates_unused": sorted(
            gate for gate in reg["GATES"]
            if not any(null.gate_check == gate
                       for null in reg["EXPECTED_INERT"].values())),
        "orphans": sorted(
            name for name in src
            if not importers.get(name) and name not in reg["ENTRY_POINTS"]),
        "unreferenced_constants": sorted(
            f"{module}.{name}"
            for module, tree in src.items()
            for name, _node in _top_level(tree)
            if name.isupper() and not name.startswith("_")
            and not (refs_src.get(name, set()) - {module})
            and not refs_tests.get(name)),
    }


def _guards(tests, reg) -> list[dict]:
    """Which test modules so much as mention each register.

    Not a claim that a test CHECKS the register -- a mention is a mention. It
    is the cheap half of the question, and the cheap half is enough to see a
    register no test names at all.
    """
    refs = _references(tests)
    rows = []
    home = reg["_home"]                                   # type: ignore[index]
    for name in sorted(home):
        rows.append({"register": name, "defined_in": home[name],
                     "named_by_tests": sorted(refs.get(name, set()))})
    return rows


def _producers(src, reg) -> list[dict]:
    """Every declared producer of an intermediate, against the code.

    The register says which script writes each artefact under `data/processed`.
    A claim like that is exactly what `src/declares.py` calls the interesting
    state -- present, and wrong -- so it is checked here the only way it can be
    without reading the gitignored tree: the module the register names must be
    a module that actually mentions the artefact.
    """
    text = {module: (SRC / f"{module}.py").read_text(encoding="utf-8")
            for module in src}
    rows = []
    for register_name in ("NOT_REGENERATED_HERE",):
        for pattern, why in sorted(reg[register_name].items()):
            claimed = sorted(set(re.findall(r"src/(\w+)\.py", why)))
            fragments = [piece for piece in pattern.split("*")
                         if len(piece) >= MIN_GLOB_FRAGMENT]
            mentions = sorted(module for module, body in text.items()
                              if fragments
                              and any(piece in body for piece in fragments))
            rows.append({"artefact": pattern, "claimed": claimed,
                         "mentions": mentions,
                         "agrees": bool(claimed) and set(claimed) <= set(mentions)})
    return rows


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(cell or "--" for cell in row) + " |"
            for row in rows]
    return out


def _cell(value) -> str:
    if isinstance(value, bool):
        return "yes" if value else "NO"
    if isinstance(value, (list, tuple, set)):
        return ", ".join(f"`{item}`" for item in value) if value else ""
    return str(value)


def to_markdown(index: dict) -> str:
    """The index as markdown. Sorted throughout; no dates, no line numbers."""
    out: list[str] = []
    add = out.append

    add("# The model index")
    add("")
    add("⛔ **GENERATED. Do not edit.** `src/model_index.py` writes this file "
        "and `tests/test_model_index.py` regenerates it into a scratch path "
        "and compares, so a hand edit fails the suite.")
    add("")
    add("Every register this repository keeps, joined on the names they share. "
        "A name in one register and not another is the finding; the sections "
        "below are ordered so the joins come before the inventories.")
    add("")
    add("Read `model` and `measurement` as membership of the import closure of "
        "`montecarlo` and of `compare_history` — what a forecast runs through, "
        "and what scores one. `neither` is not an accusation: a build script "
        "is correctly in neither.")

    add("")
    add("## 1 · Collisions")
    add("")
    add("### 1.1 One computation, several reported names")
    add("")
    add(_alias_families.__doc__.strip().split("\n\n")[1].strip())
    add("")
    out += _table(["module", "function", "reported as"],
                  [[f"`{r['module']}`", f"`{r['function']}`", _cell(r["keys"])]
                   for r in index["collisions"]["alias_families"]])

    add("")
    add("### 1.2 One name, defined in more than one module")
    add("")
    out += _table(["name", "modules", "kinds", "same kind"],
                  [[f"`{r['name']}`", _cell(r["modules"]), _cell(r["kinds"]),
                    _cell(r["same_kind"])]
                   for r in index["collisions"]["shared_names"]])

    add("")
    add("### 1.3 One value, typed under two names")
    add("")
    out += _table(["value", "names"],
                  [[r["value"], _cell(r["names"])]
                   for r in index["collisions"]["repeated_values"]])

    add("")
    add("### 1.4 Apportionment sites — the same job, written more than once")
    add("")
    add("Matched on the SHAPE of largest-remainder apportionment (a whole "
        "part, an ordering, a shortfall handed out), not on the phrase, which "
        "appears in the docstrings of modules that only discuss it.")
    add("")
    out += _table(["function", "orders the shortfall by", "summary"],
                  [[f"`{r['function']}`", f"`{r['ties']}`", r["summary"]]
                   for r in index["collisions"]["apportionment"]])

    add("")
    add("### 1.5 Shadow pairs — a scenario key and a module constant of one name")
    add("")
    add("`tied` means some `assert` in `src/` names both, so they cannot "
        "silently disagree. An untied shadow is one number in two places.")
    add("")
    out += _table(["lever", "shadow constant", "tied"],
                  [[f"`{r['lever']}`", f"`{r['shadow']}`", _cell(r["shadow_tied"])]
                   for r in index["levers"] if r["shadow"]])

    add("")
    add("## 2 · Exemptions, and whether they still exempt anything")
    add("")
    add("### 2.1 Deleted levers the judgement register is allowed to discuss")
    add("")
    add("`named by register` is what the exemption is FOR. An entry the "
        "register never names excuses nothing today and is waiting to excuse "
        "the next name that collides with it.")
    add("")
    out += _table(["name", "named by register", "still referenced in src"],
                  [[f"`{r['name']}`", _cell(r["named_by_register"]),
                    _cell(r["still_referenced"])]
                   for r in index["inert"]["deleted"]])

    add("")
    add("### 2.2 Deleted from the model, still read somewhere in `src/`")
    add("")
    out += _table(["name", "present", "read in"],
                  [[f"`{r['name']}`", _cell(r["present"]), _cell(r["where"])]
                   for r in index["inert"]["still_in_the_tree"]])

    add("")
    add("### 2.3 Entry points — modules exempted from the dead-code rule")
    add("")
    add("An entry point that has acquired an importer no longer needs the "
        "exemption: the importer proves it alive on its own.")
    add("")
    out += _table(["module", "exemption still load-bearing", "importers"],
                  [[f"`{r['module']}`", _cell(r["still_needed"]),
                    _cell(r["importers"])]
                   for r in index["inert"]["entry_points"]])

    add("")
    add("### 2.4 The rest of the dead")
    add("")
    out += _table(["what", "which"], [
        ["register sections still making a live claim on a deleted lever",
         _cell(index["inert"]["unresolved_live_claims"])],
        ["gates declared and named by no inert entry",
         _cell(index["inert"]["gates_unused"])],
        ["gates recorded OPEN at a target",
         _cell(index["inert"]["gates_open_at"])],
        ["modules imported by nothing and not declared entry points",
         _cell(index["inert"]["orphans"])],
    ])

    add("")
    add("### 2.5 Module constants nothing outside their own module reads")
    add("")
    add("Not dead by itself — a constant read only where it is defined is "
        "ordinary. Dead is this list crossed with a module in `neither` "
        "closure, and with §4's delivery table.")
    add("")
    add(_cell(index["inert"]["unreferenced_constants"]) or "--")

    add("")
    add("## 3 · Declared producers against the code")
    add("")
    add("The intermediates register names the script that writes each "
        "artefact. `agrees` is false when the module it names does not so much "
        "as mention the artefact.")
    add("")
    out += _table(["artefact", "register claims", "modules naming it", "agrees"],
                  [[f"`{r['artefact']}`", _cell(r["claimed"]),
                    _cell(r["mentions"]), _cell(r["agrees"])]
                   for r in index["producers"]])

    add("")
    add("## 4 · Levers")
    add("")
    add("Every key of `montecarlo.DEFAULTS`, against every register that "
        "classifies it. `provenance` is the backtest's leak class; "
        "`inert at` and `conditional at` are the targets where the lever has "
        "been certified dead or measured live; `registered` is whether "
        "`JUDGEMENT-CALLS.md` names it.")
    add("")
    out += _table(["lever", "default", "provenance", "inert at",
                   "conditional at", "registered", "read in"],
                  [[f"`{r['lever']}`", f"`{r['default']}`",
                    _cell(r["provenance"]), _cell(r["inert_at"]),
                    _cell(r["conditional_at"]), _cell(r["registered"]),
                    _cell(r["read_in"])]
                   for r in index["levers"]])

    add("")
    add("## 5 · Module constants")
    add("")
    add("`delivered` is membership of `montecarlo.MODULE_CONSTANTS` — the "
        "table of names resolved into the run record. `swept` is "
        "`MODULE_PERTURB`. `registered` is `JUDGEMENT-CALLS.md`.")
    add("")
    out += _table(["constant", "kind", "delivered", "swept", "registered",
                   "read elsewhere"],
                  [[f"`{r['constant']}`", r["kind"], _cell(r["delivered"]),
                    _cell(r["swept"]), _cell(r["registered"]),
                    _cell(r["read_elsewhere"])]
                   for r in index["constants"]])

    add("")
    add("## 6 · Folds and windows")
    add("")
    add("Every name that declares a SPAN — of folds, of history, of recency — "
        "matched on the name and then read off the object.")
    add("")
    out += _table(["name", "where", "value", "spans"],
                  [[f"`{r['name']}`", f"`{r['where']}`", r["value"], r["spans"]]
                   for r in index["spans"]])

    add("")
    add("## 7 · Methods on the model and measurement paths")
    add("")
    add("Every public function in the import closure of `montecarlo` or of "
        "`compare_history`. A statistic that is not here is not invoked by a "
        "forecast or by the scoring of one, whatever its name suggests.")
    add("")
    out += _table(["function", "path", "summary", "callers"],
                  [[f"`{r['function']}`", r["path"], r["summary"],
                    _cell(r["callers"])]
                   for r in index["methods"]])

    add("")
    add("## 8 · Modules")
    add("")
    out += _table(["module", "path", "entry point", "importers", "summary"],
                  [[f"`{r['module']}`", r["role"], _cell(r["entry_point"]),
                    _cell(r["importers"]), r["summary"]]
                   for r in index["modules"]])

    add("")
    add("## 9 · Registers, and which test modules name them")
    add("")
    add("A mention is not a check. It is the cheap half of the question, and "
        "it is enough to see a register no test names at all.")
    add("")
    out += _table(["register", "defined in", "named by tests"],
                  [[f"`{r['register']}`", f"`{r['defined_in']}`",
                    _cell(r["named_by_tests"])]
                   for r in index["guards"]])
    add("")
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--stdout", action="store_true",
                        help="print the index instead of writing it")
    parser.add_argument("--out", type=Path, default=None,
                        help="write somewhere other than MODEL-INDEX.md")
    args = parser.parse_args(argv)
    text = to_markdown(build())
    if args.stdout:
        sys.stdout.write(text)
        return 0
    destination = args.out or OUTPUT
    destination.write_text(text, encoding="utf-8")
    print(f"wrote {destination.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
