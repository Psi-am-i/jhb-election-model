"""The judgement calls, laid out for a person rather than for a grep.

    .venv/bin/python src/judgement_sheet.py        # write JUDGEMENT-SHEET.md

⛔ THE SHEET IS GENERATED. DO NOT EDIT `JUDGEMENT-SHEET.md` BY HAND.
`tests/test_judgement_sheet.py` regenerates it and compares, so a hand edit is
reverted by the next run and reported as a failure in the meantime.

WHY A SECOND DOCUMENT, WHEN `JUDGEMENT-CALLS.md` ALREADY EXISTS. That file is
the register: authoritative, and organised so a symbol can be found. It answers
*"what did we choose for X, and why"*. It cannot answer the three questions a
reader actually arrives with, because no single register holds them:

    1. what IS this thing, in a sentence?          -> the register
    2. is it doing anything AT 2026?               -> `test_levers_are_live`
    3. can I, the reader, move it?                 -> the interactive's own code

Each register is internally consistent; the gaps live between them. This module
joins them and narrates the join. It invents no prose about any individual call:
the sentence beside each row is the register's own `current state` cell, carried
through verbatim, so there is exactly one place where that sentence is written.

⛔ IT TYPES NO LEVER NAME, EVER, AND THAT IS A HARD CONSTRAINT RATHER THAN A
STYLE. `test_register_matches_code` harvests every string literal in `src/` into
the population it checks the judgement register against. A module here that
merely SPELLED a deleted lever — in a docstring, in an example, in a heading —
would make that name "defined", and the `DELETED` clause would stop excusing
anything while the suite stayed green. `src/model_index.py` carries the same
constraint for the same reason, and both are held to it by a test. So every name
below is read out of a register or out of a syntax tree at run time.

WHAT THIS DOES NOT DO. It does not judge a call, re-measure one, or decide
whether a value is right — `MODEL-LOG.md` holds measurements and
`JUDGEMENT-CALLS.md` holds the arguments. It reports what the registers say
about each other, including where they disagree, and its own test checks only
that it is current: equality with the generator is a staleness guard, never a
correctness one.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
CITIES = ROOT / "cities"
REGISTER = ROOT / "JUDGEMENT-CALLS.md"
OUTPUT = ROOT / "JUDGEMENT-SHEET.md"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import model_index  # noqa: E402  (same package, and it owns the register loader)

# The target the live forecast is for. Read from the register loader's own
# scenario defaults would be wrong -- the year is not a scenario key -- so it is
# derived from the city configurations, which name their targets.
LIVE_TARGET_KEY = "by_year"


# ---------------------------------------------------------------------------
# the register, parsed
# ---------------------------------------------------------------------------

def _tables(text: str) -> tuple[list[list[str]], list[list[str]]]:
    """The two register tables as raw cell lists: (named constants, structural).

    Rows are split naively on `|`, and a row whose cell count is not what its
    header declares is DROPPED AND COUNTED rather than guessed at. The register
    has been through exactly that failure -- rows carrying an unescaped pipe
    spilled across phantom columns and a renderer silently dropped the last
    cell, which is how status markers went invisible on eleven rows. A parser
    that silently accepts a malformed row reproduces that defect one layer up.
    """
    named: list[list[str]] = []
    structural: list[list[str]] = []
    current: list[list[str]] | None = None
    width = 0
    for line in text.splitlines():
        if line.startswith("### "):
            heading = line[4:].strip().lower()
            if heading.startswith("named"):
                current, width = named, 6
            elif heading.startswith("judgements with no symbol"):
                current, width = structural, 5
            else:
                current = None
            continue
        if line.startswith("## "):
            current = None
            continue
        if current is None or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != width or set("".join(cells)) <= set("-: "):
            continue
        if cells[0].startswith("---"):
            continue
        current.append(cells)
    return named, structural


def _symbols(cell: str) -> list[str]:
    """Backticked identifiers in a register cell, strikes removed.

    The same reading `test_register_matches_code` takes: a struck row is an
    obituary and its symbol is meant to be gone.
    """
    cell = re.sub(r"~~.*?~~", "", cell)
    return [token for token in re.findall(r"`([^`]+)`", cell)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", token.strip())]


def _legend(text: str) -> list[str]:
    """The status legend, lifted from the register so it cannot drift from it."""
    out, taking = [], False
    for line in text.splitlines():
        if line.startswith("Status:"):
            taking = True
        elif taking and not line.strip():
            break
        if taking:
            out.append(line.strip())
    return out


# ---------------------------------------------------------------------------
# what a reader can move: the interactive's own slider map, read from its AST
# ---------------------------------------------------------------------------

def _interactive() -> dict:
    """What the published interactive exposes, and whether it can be built.

    Read from the syntax tree rather than by importing, because the module
    REFUSES at import: it raises at module level on purpose, since its
    in-browser drawer is the old two-bloc engine. Importing it here would take
    this generator down with it -- and the refusal is itself the answer to
    "which of these can a reader move today", so it is reported, not defeated.
    """
    path = SRC / "build_interactive.py"
    if not path.exists():
        return {"present": False, "refuses": False, "keys": [], "reason": ""}
    tree = ast.parse(path.read_text(encoding="utf-8"))

    refuses, reason = False, ""
    for node in tree.body:                       # MODULE LEVEL ONLY: a raise
        if isinstance(node, ast.Raise):          # inside a function is control
            refuses = True                       # flow, not a refusal to load.
            for sub in ast.walk(node):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    reason = " ".join(sub.value.split())
                    break
        elif isinstance(node, ast.If):
            for inner in node.body:
                if isinstance(inner, ast.Raise):
                    refuses = True

    # ⛔ GROUPED BY THE BLOCK EACH LOOKUP READS, NOT SWEPT UP FLAT.
    #
    # The first version of this walked EVERY `.get("x")` in the file and called
    # the result "keys the interactive reads". It collected party codes and the
    # names of the judgement tables themselves alongside the actual controls,
    # and the rendered sheet then asserted that each one was a deleted lever —
    # a scan over the wrong set, reported confidently, which is the defect class
    # this repository keeps finding in its own guards. The receiver is what
    # gives a lookup its meaning: a key read off the scalars block is a lever, a
    # key read off a per-party block is a party.
    #
    # So: resolve each local name to the judgement block it was bound from, and
    # attribute a lookup only to a receiver that resolves. A lookup on anything
    # else is ignored rather than guessed at.
    groups: dict[str, set[str]] = {}
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef):
            continue
        bound: dict[str, str] = {}
        for node in ast.walk(function):
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Attribute)
                    and node.value.func.attr == "get" and node.value.args
                    and isinstance(node.value.args[0], ast.Constant)
                    and isinstance(node.value.args[0].value, str)):
                bound[node.targets[0].id] = node.value.args[0].value
        for node in ast.walk(function):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "get" and node.args
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in bound
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                groups.setdefault(bound[node.func.value.id], set()).add(
                    node.args[0].value)

    # The scalar block is the one holding levers; the others hold party codes.
    # Named by the longest-matching block rather than typed, so a renamed block
    # shows up as an empty group here instead of as a silently wrong list.
    scalar_block = max(groups, key=lambda name: len(groups[name]), default="")
    declared = set().union(*_city_scalars().values()) if _city_scalars() else set()
    scalar_block = next((name for name, keys in sorted(groups.items())
                         if keys & declared), scalar_block)
    return {"present": True, "refuses": refuses, "reason": reason,
            "keys": sorted(groups.get(scalar_block, set())),
            "block": scalar_block,
            "other": {name: sorted(keys) for name, keys in sorted(groups.items())
                      if name != scalar_block}}


def _city_scalars() -> dict[str, set[str]]:
    """Each city's declared `[judgements.scalars]` keys.

    Parsed straight from the TOML: this reads a configuration file's KEY SET,
    which is not model logic, and importing `cityconfig` here would set the
    process-global active city as a side effect of writing a document.
    """
    out: dict[str, set[str]] = {}
    for path in sorted(CITIES.glob("*.toml")):
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError:
            continue
        block = (raw.get("judgements") or {}).get("scalars") or {}
        out[path.stem] = set(block)
    return out


# ---------------------------------------------------------------------------
# the join
# ---------------------------------------------------------------------------

def build() -> dict:
    """Every judgement call, joined to what each register says about it."""
    text = REGISTER.read_text(encoding="utf-8")
    named, structural = _tables(text)
    index = model_index.build()
    reg = model_index._load_registers()

    levers = {row["lever"]: row for row in index["levers"]}
    constants = {row["constant"]: row for row in index["constants"]}

    # firing, at the live target -- keyed off the registers, not off a year
    # typed here. EXPECTED_INERT is keyed (lever, target); CONDITIONAL is
    # keyed "lever@target".
    targets = sorted({target for _, target in reg["EXPECTED_INERT"]}
                     | {key.partition("@")[2] for key in reg["CONDITIONAL"]})
    live_target = targets[-1] if targets else ""

    inert = {lever: null for (lever, target), null in reg["EXPECTED_INERT"].items()
             if target == live_target}
    conditional = {key.partition("@")[0]: value
                   for key, value in reg["CONDITIONAL"].items()
                   if key.partition("@")[2] == live_target}

    interactive = _interactive()
    scalars = _city_scalars()
    exposed = {key for key in interactive["keys"]
               for keys in scalars.values() if key in keys}
    wanted_missing = sorted(
        key for key in interactive["keys"]
        if scalars and not any(key in keys for keys in scalars.values()))

    rows = []
    for cells in named:
        constant, value, where, state, status, entry = cells
        names = _symbols(constant)
        primary = next((name for name in names if name in levers), None)
        kind = "lever"
        if primary is None:
            primary = next((name for name in names if name in constants), None)
            kind = "module constant" if primary else "unlinked"
        null = inert.get(primary) if primary else None
        rows.append({
            "shown": constant,
            "symbols": names,
            "symbol": primary or "",
            "kind": kind,
            "value": value,
            "where": where,
            "state": state,
            "status": status,
            "entry": entry,
            "firing": _firing(primary, null, conditional, levers),
            "reader": _reader(names, interactive, exposed),
        })

    # ⛔ A SCENARIO KEY WHOSE ROW IS FILED UNDER ANOTHER SPELLING IS NOT COVERED,
    # AND "REGISTERED" IS A WEAKER CLAIM THAN IT READS AS.
    #
    # Found by this module's own population test, which is the only reason it is
    # here: one lever has register rows filed under its UPPERCASE module
    # constant and none under the key itself, so a join on row symbols drops it
    # silently. The index calls such a lever `registered: yes` because its check
    # harvests every backticked identifier ANYWHERE in the register — a prose
    # mention counts. That is the right reading for the index's question and the
    # wrong one for this document's, so the difference is printed rather than
    # smoothed over: a shadow row that is TIED really does describe the lever; a
    # prose mention does not.
    covered = {name for row in rows for name in row["symbols"]}
    mentioned = model_index._register_symbols()
    uncovered = []
    for lever in sorted(reg["DEFAULTS"]):
        if lever in covered:
            continue
        lever_row = levers.get(lever, {})
        shadow = lever_row.get("shadow") or ""
        if shadow.rpartition(".")[2] in covered and shadow:
            tied = lever_row.get("shadow_tied")
            how = (f"its row is filed under the shadow constant `{shadow}`, "
                   + ("tied to it by an assert, so the row does describe it"
                      if tied else
                      "⚠️ and the two are UNTIED — one number in two places"))
        elif lever in mentioned:
            how = ("⚠️ named only in the register's prose, with no row of its "
                   "own — enough to count as registered, not enough to read")
        else:
            how = "⛔ not in the register at all"
        uncovered.append({"lever": lever, "how": how})

    return {
        "live_target": live_target,
        "legend": _legend(text),
        "uncovered": uncovered,
        "rows": rows,
        "structural": [dict(zip(("call", "where", "state", "status", "entry"),
                                cells)) for cells in structural],
        "interactive": interactive,
        "interactive_missing": wanted_missing,
        "unregistered_levers": sorted(
            row["lever"] for row in index["levers"] if not row["registered"]),
        "parsed": {"named": len(named), "structural": len(structural)},
    }


def _firing(symbol, null, conditional, levers) -> str:
    """One phrase for 'is this doing anything at the live target'."""
    if not symbol:
        return "not linked to a scenario key or module constant"
    if null is not None:
        cause = getattr(null, "cause", "")
        where = " ".join(str(getattr(null, "where", "")).split())
        return f"CERTIFIED INERT ({cause})" + (f" — {where}" if where else "")
    if symbol in conditional:
        why = " ".join(str(getattr(conditional[symbol], "why", "")).split())
        return "CONDITIONAL — dead as shipped, measured with its gate held open" \
               + (f": {why}" if why else "")
    if symbol in levers:
        return "not certified dead here"
    return "module constant"


def _reader(names, interactive, exposed) -> str:
    """Whether a reader could move this from the published page."""
    hit = [name for name in names if name in interactive["keys"]]
    if not hit:
        return "no"
    if interactive["refuses"]:
        return "named by the interactive, which is WITHHELD"
    return "yes" if any(name in exposed for name in hit) else \
        "named by the interactive, but no city declares it"


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def render(sheet: dict) -> str:
    out: list[str] = []
    add = out.append
    add("# The judgement calls, laid out\n")
    add("⛔ **GENERATED — do not edit.** `.venv/bin/python src/judgement_sheet.py`, "
        "and `tests/test_judgement_sheet.py` regenerates it and compares.\n")
    add("Every choice a person made that the data did not force, joined to what "
        "the registers say about it: what it is, whether it is doing anything at "
        "the live target, and whether a reader could move it. The sentence in "
        "*what it is* is `JUDGEMENT-CALLS.md`'s own, carried through verbatim — "
        "this document writes no new prose about any individual call, so there "
        "is one place to correct it.\n")

    add("## How to read the columns\n")
    for line in sheet["legend"]:
        add(line)
    add("")
    add("**doing anything?** is read from `tests/test_levers_are_live`:\n")
    add("* **CERTIFIED INERT** — a registered null with a cause and a gate check "
        "that proves it. It is not merely unobserved; something was measured.")
    add("* **CONDITIONAL** — dead in the shipped configuration, and measured with "
        "its gate held open, which is the only honest reading of such a lever.")
    add("* **not certified dead here** — ⚠️ exactly that, and *not* evidence that "
        "it fires. It means no null has been registered at this target. The "
        "absence of a certificate is not a measurement.\n")
    add(f"The live target below is **{sheet['live_target']}**, taken from the "
        f"registers' own keys rather than typed here.\n")

    add("## 1 · What a reader can move\n")
    inter = sheet["interactive"]
    if inter["refuses"]:
        add("⛔ **NOTHING, TODAY. The interactive refuses to build**, and says "
            "why:\n")
        add(f"> {inter['reason']}\n")
        add("So every 'named by the interactive' below describes a control on a "
            "page that is **withheld**, not one a reader can touch. Two things "
            "follow, and the second is the one that bites:\n")
        add("* the published forecast exposes **no** judgement call to a reader;")
        add("* the frozen page's controls are not a subset of today's levers. "
            "The keys it reads that **no city declares** are listed below — each "
            "is either a deleted lever or one that never existed here, and the "
            "page would drive a control that moves nothing.\n")
    if sheet["interactive_missing"]:
        add(f"Controls the interactive reads off its `{inter['block']}` block "
            f"that **no city declares** — each is a control with nothing behind "
            f"it:\n")
        for key in sheet["interactive_missing"]:
            add(f"* `{key}`")
        add("")
    for name, keys in (inter.get("other") or {}).items():
        add(f"It also reads {len(keys)} key(s) off its `{name}` block; those are "
            f"party codes, not levers, and are not checked against "
            f"`[judgements.scalars]` here.")
    if inter.get("other"):
        add("")

    add("## 2 · The calls with a symbol\n")
    add("| call | value | kind | doing anything at the live target? | reader can move it? | what it is | status | entry |")
    add("|---|---|---|---|---|---|---|---|")
    for row in sheet["rows"]:
        add(f"| {row['shown']} | {row['value']} | {row['kind']} | "
            f"{row['firing']} | {row['reader']} | {row['state']} | "
            f"{row['status']} | {row['entry']} |")
    add("")

    add("## 3 · The calls with no symbol of their own\n")
    add("Structural choices the code makes without a constant to name them — "
        "the easiest kind to lose, because nothing can grep for them.\n")
    add("| the call | where | what it is | status | entry |")
    add("|---|---|---|---|---|")
    for row in sheet["structural"]:
        add(f"| {row['call']} | {row['where']} | {row['state']} | "
            f"{row['status']} | {row['entry']} |")
    add("")

    add("## 4 · Gaps this join can see\n")
    if sheet["unregistered_levers"]:
        add("Scenario keys the judgement register does not name:\n")
        for lever in sheet["unregistered_levers"]:
            add(f"* `{lever}`")
        add("")
    else:
        add("Every scenario key is named by the register.\n")
    if sheet["uncovered"]:
        add("Scenario keys with **no register row under their own name**. Each "
            "is still a judgement call; the note says what stands in for its "
            "row, and a prose mention is not a row:\n")
        for row in sheet["uncovered"]:
            add(f"* `{row['lever']}` — {row['how']}")
        add("")
    add(f"Register rows parsed: {sheet['parsed']['named']} with a symbol, "
        f"{sheet['parsed']['structural']} structural. A row whose cell count "
        f"does not match its header is dropped rather than guessed at, so these "
        f"counts are the parser's own view and a drop shows up as a missing "
        f"row here rather than as a mangled one.\n")
    return "\n".join(out) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUTPUT,
                        help="write somewhere other than JUDGEMENT-SHEET.md")
    args = parser.parse_args(argv)
    text = render(build())
    args.out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out} ({text.count(chr(10))} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
