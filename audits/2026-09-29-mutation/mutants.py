"""Mutant enumeration and application. Pure: reads source text, returns text.

Every mutant is ONE small edit, spliced into the original text at the node's
own position, so every line keeps its number. A mutant whose result does not
parse is discarded here and never reaches a worker.

Operators (the brief's list, one name each):

    cmp        flip a comparison: <→<=,>= · <=→<,> · >→>=,<= · >=→>,< · ==↔!= ·
               is↔is not · in↔not in
    const      change a numeric constant: int n→n+1; float x→2x (0.0→1.0);
               True↔False
    drop       drop a simple statement inside a function body (→ `pass`):
               assignment, augmented assignment, expression statement, return,
               raise, assert, del, break, continue. `print(...)` is skipped:
               dropping output is not a model mutation.
    negate     invert a branch condition: `if c` / `elif c` / `while c` /
               `a if c else b` → `not (c)`
    boolop     swap and/or (every operator of one BoolOp at once)
    offbyone   `range(...)` argument a → (a) + 1; slice bound a → (a) + 1

Not mutated: docstrings, strings, annotations, anything under
`if __name__ == "__main__":`, and module- or class-level statements for `drop`
(dropping one is a NameError at import, which every importer reports).

Each mutant carries the facts the scheduler needs to pick its tests and its
model mode without re-parsing:

    lines      the mutated node's own line span (what coverage is checked on)
    func       enclosing function qualname, or "<module>"
    kind       "body" (inside a function body), "default" (a def's default
               argument or decorator: evaluated at import, used by the body),
               "module" (module or class level: evaluated at import)
    names      for kind=module, the names the enclosing assignment binds
    func_span  for kind=body/default, the enclosing function's line span
"""

from __future__ import annotations

import ast
import hashlib
import re

CMP_SWAPS = {
    ast.Lt: ["<=", ">="], ast.LtE: ["<", ">"],
    ast.Gt: [">=", "<="], ast.GtE: [">", "<"],
    ast.Eq: ["!="], ast.NotEq: ["=="],
    ast.Is: ["is not"], ast.IsNot: ["is"],
    ast.In: ["not in"], ast.NotIn: ["in"],
}
CMP_TEXT = re.compile(r"is\s+not\b|not\s+in\b|\bis\b|\bin\b|<=|>=|==|!=|<|>")
BOOL_TEXT = re.compile(r"\b(and|or)\b")
DROP_TYPES = (ast.Assign, ast.AugAssign, ast.AnnAssign, ast.Expr, ast.Return,
              ast.Raise, ast.Assert, ast.Delete, ast.Break, ast.Continue)
OPERATORS = ("cmp", "const", "drop", "negate", "boolop", "offbyone")


class _Text:
    """Source text with (line, utf-8 column) -> character offset."""

    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines(keepends=True)
        self.starts = [0]
        for ln in self.lines:
            self.starts.append(self.starts[-1] + len(ln))

    def off(self, lineno: int, col: int) -> int:
        line = self.lines[lineno - 1]
        return self.starts[lineno - 1] + len(line.encode()[:col].decode())

    def span(self, node) -> tuple[int, int]:
        return (self.off(node.lineno, node.col_offset),
                self.off(node.end_lineno, node.end_col_offset))


def _strip_comments(text: str) -> str:
    """Blank out `#...` to end of line, keeping offsets. The text between two
    operands holds only brackets, whitespace, comments and the operator."""
    return re.sub(r"#[^\n]*", lambda m: " " * len(m.group()), text)


def _is_main_guard(node) -> bool:
    t = getattr(node, "test", None)
    return (isinstance(node, ast.If) and isinstance(t, ast.Compare)
            and isinstance(t.left, ast.Name) and t.left.id == "__name__")


def _docstring_nodes(tree) -> set[int]:
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)) and n.body:
            first = n.body[0]
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                out.add(id(first))
    return out


def _annotation_nodes(tree) -> set[int]:
    """ids of every node inside an annotation (never mutated)."""
    out = set()

    def mark(a):
        if a is not None:
            for sub in ast.walk(a):
                out.add(id(sub))

    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            mark(n.returns)
            a = n.args
            for arg in a.posonlyargs + a.args + a.kwonlyargs + [a.vararg, a.kwarg]:
                if arg is not None:
                    mark(arg.annotation)
        elif isinstance(n, ast.AnnAssign):
            mark(n.annotation)
    return out


def _bound_names(stmt) -> list[str]:
    targets = []
    if isinstance(stmt, ast.Assign):
        targets = stmt.targets
    elif isinstance(stmt, (ast.AugAssign, ast.AnnAssign)):
        targets = [stmt.target]
    names = []
    for t in targets:
        for sub in ast.walk(t):
            if isinstance(sub, ast.Name):
                names.append(sub.id)
            elif isinstance(sub, ast.Attribute):
                names.append(sub.attr)
    return names


def enumerate_mutants(source: str, relpath: str) -> list[dict]:
    """Every mutant of one module, in source order, each verified to parse."""
    tree = ast.parse(source)
    text = _Text(source)
    docstrings = _docstring_nodes(tree)
    annotations = _annotation_nodes(tree)
    out: list[dict] = []

    def emit(node, op, start, end, replacement, desc, ctx):
        mutated = source[:start] + replacement + source[end:]
        try:
            ast.parse(mutated)
        except SyntaxError:
            return
        lines = [node.lineno, node.end_lineno]
        raw = f"{relpath}|{start}|{end}|{op}|{replacement}"
        out.append({
            "id": hashlib.sha1(raw.encode()).hexdigest()[:12],
            "file": relpath, "line": node.lineno, "lines": lines,
            "op": op, "desc": desc, "start": start, "end": end,
            "replacement": replacement,
            "original": source[start:end],
            **ctx,
        })

    def visit(node, ctx, in_main):
        # ctx: func, kind, names, func_span, stmt
        if isinstance(node, ast.If) and _is_main_guard(node):
            return  # CLI entry; not on any path the model or tests import
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            qual = node.name if ctx["func"] == "<module>" else f"{ctx['func']}.{node.name}"
            span = [node.lineno, node.end_lineno]
            head = dict(ctx, kind="default", func=qual, func_span=span, names=[])
            for d in node.decorator_list:
                visit(d, head, in_main)
            for d in node.args.defaults + [x for x in node.args.kw_defaults if x]:
                visit(d, head, in_main)
            body = dict(ctx, kind="body", func=qual, func_span=span, names=[])
            for s in node.body:
                visit(s, body, in_main)
            return
        if isinstance(node, ast.ClassDef):
            qual = node.name if ctx["func"] == "<module>" else f"{ctx['func']}.{node.name}"
            # A class inside a function body stays in that body; a class at
            # module level is import-time code, named by its qualname.
            inner = ctx if ctx["kind"] == "body" else dict(ctx, func=qual)
            for d in node.decorator_list:
                visit(d, inner, in_main)
            for s in node.body:
                visit(s, inner, in_main)
            return
        if isinstance(node, ast.stmt):
            if id(node) in docstrings:
                return
            names = _bound_names(node) if ctx["kind"] == "module" else ctx.get("names", [])
            ctx = dict(ctx, names=names)
            # drop
            if (ctx["kind"] == "body" and isinstance(node, DROP_TYPES)
                    and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
                             and isinstance(node.value.func, ast.Name)
                             and node.value.func.id == "print")
                    and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))):
                s, e = text.span(node)
                emit(node, "drop", s, e,
                     "pass" + "\n" * (node.end_lineno - node.lineno),
                     f"drop `{_short(source[s:e])}`", ctx)
            if isinstance(node, (ast.If, ast.While)):
                ts, te = text.span(node.test)
                emit(node.test, "negate", ts, te, f"not ({source[ts:te]})",
                     f"negate `{_short(source[ts:te])}`", ctx)
        _node_ops(node, ctx)
        for child in ast.iter_child_nodes(node):
            if id(child) in annotations:
                continue
            visit(child, ctx, in_main)

    def _node_ops(node, ctx):
        if isinstance(node, ast.IfExp):
            s, e = text.span(node.test)
            emit(node.test, "negate", s, e, f"not ({source[s:e]})",
                 f"negate `{_short(source[s:e])}`", ctx)
        if isinstance(node, ast.Compare):
            left = node.left
            for op, right in zip(node.ops, node.comparators):
                gs = text.off(left.end_lineno, left.end_col_offset)
                ge = text.off(right.lineno, right.col_offset)
                gap = _strip_comments(source[gs:ge])
                m = CMP_TEXT.search(gap)
                if m:
                    for rep in CMP_SWAPS.get(type(op), []):
                        emit(node, "cmp", gs + m.start(), gs + m.end(), rep,
                             f"`{m.group()}` → `{rep}` in `{_short(source[slice(*text.span(node))])}`",
                             ctx)
                left = right
        if isinstance(node, ast.BoolOp):
            s0, e0 = text.span(node)
            pieces = []
            for a, b in zip(node.values, node.values[1:]):
                gs = text.off(a.end_lineno, a.end_col_offset)
                ge = text.off(b.lineno, b.col_offset)
                m = BOOL_TEXT.search(_strip_comments(source[gs:ge]))
                if m:
                    pieces.append((gs + m.start(), gs + m.end(), m.group()))
            if pieces and len(pieces) == len(node.values) - 1:
                seg = source[s0:e0]
                for ps, pe, word in reversed(pieces):
                    seg = seg[:ps - s0] + ("or" if word == "and" else "and") + seg[pe - s0:]
                word = pieces[0][2]
                emit(node, "boolop", s0, e0, seg,
                     f"`{word}` → `{'or' if word == 'and' else 'and'}` in `{_short(source[s0:e0])}`",
                     ctx)
        if isinstance(node, ast.Constant) and id(node) not in docstrings:
            v = node.value
            rep = None
            if isinstance(v, bool):
                rep = repr(not v)
            elif isinstance(v, int):
                rep = repr(v + 1)
            elif isinstance(v, float):
                rep = repr(v * 2 if v != 0 else 1.0)
            if rep is not None:
                s, e = text.span(node)
                ls = source.rfind("\n", 0, s) + 1
                le = source.find("\n", e)
                around = source[max(ls, s - 25):s] + "⟨" + source[s:e] + "⟩" + source[e:min(le if le >= 0 else len(source), e + 12)]
                emit(node, "const", s, e, rep,
                     f"`{source[s:e]}` → `{rep}` at `{_short(around)}`", ctx)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "range"):
            for a in node.args:
                s, e = text.span(a)
                emit(a, "offbyone", s, e, f"({source[s:e]}) + 1",
                     f"range arg `{_short(source[s:e])}` + 1", ctx)
        if isinstance(node, ast.Slice):
            for a in (node.lower, node.upper):
                if a is not None:
                    s, e = text.span(a)
                    emit(a, "offbyone", s, e, f"({source[s:e]}) + 1",
                         f"slice bound `{_short(source[s:e])}` + 1", ctx)

    root = {"func": "<module>", "kind": "module", "names": [], "func_span": None}
    for stmt in tree.body:
        visit(stmt, root, False)
    # de-duplicate (a Compare reached twice through nested visits never happens,
    # but ids are the contract, so enforce uniqueness)
    seen, uniq = set(), []
    for m in out:
        if m["id"] not in seen:
            seen.add(m["id"])
            uniq.append(m)
    return uniq


def _short(s: str, n: int = 70) -> str:
    s = " ".join(s.split())
    return s if len(s) <= n else s[: n - 1] + "…"


def apply(source: str, mutant: dict) -> str:
    """The mutated module text. Refuses if the source is not the one enumerated."""
    s, e = mutant["start"], mutant["end"]
    if source[s:e] != mutant["original"]:
        raise ValueError(f"mutant {mutant['id']}: source at {s}:{e} is "
                         f"{source[s:e]!r}, enumerated as {mutant['original']!r}")
    return source[:s] + mutant["replacement"] + source[e:]


def null_mutant(source: str, relpath: str) -> dict:
    """A mutant that changes the AST (so every code hash moves) and nothing the
    code does: `pass` appended at module level."""
    end = len(source)
    sep = "" if source.endswith("\n") else "\n"
    return {"id": f"null-{hashlib.sha1(relpath.encode()).hexdigest()[:7]}",
            "file": relpath, "line": source.count("\n") + 1, "lines": [0, 0],
            "op": "null", "desc": "append `pass` at module level (AST changes, behaviour does not)",
            "start": end, "end": end, "replacement": sep + "pass\n",
            "original": "", "func": "<module>", "kind": "null", "names": [],
            "func_span": None}


def reference_index(sources: dict[str, str]) -> dict[str, list[tuple[str, int, int]]]:
    """name -> [(file, first line, last line)] of every function in `sources`
    whose body mentions the name (as a bare name or as an attribute)."""
    index: dict[str, list[tuple[str, int, int]]] = {}
    for rel, src in sources.items():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            seen = set()
            for sub in ast.walk(fn):
                if isinstance(sub, ast.Name):
                    seen.add(sub.id)
                elif isinstance(sub, ast.Attribute):
                    seen.add(sub.attr)
            for name in seen:
                index.setdefault(name, []).append((rel, fn.lineno, fn.end_lineno))
    return index


def module_level_closure(sources: dict[str, str], names: set[str]) -> set[str]:
    """Names bound at module/class level from an expression mentioning any of
    `names`, transitively: `B = A * 2` carries a mutant of A to B's readers."""
    edges: list[tuple[set[str], set[str]]] = []
    for src in sources.values():
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        stack = list(tree.body)
        while stack:
            s = stack.pop()
            if isinstance(s, ast.ClassDef):
                stack.extend(s.body)
                continue
            if isinstance(s, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and s.value is not None:
                used = {n.id for n in ast.walk(s.value) if isinstance(n, ast.Name)}
                used |= {n.attr for n in ast.walk(s.value) if isinstance(n, ast.Attribute)}
                edges.append((used, set(_bound_names(s))))
    out = set(names)
    changed = True
    while changed:
        changed = False
        for used, bound in edges:
            if used & out and not bound <= out:
                out |= bound
                changed = True
    return out
