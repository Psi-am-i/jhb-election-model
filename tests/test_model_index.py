"""`MODEL-INDEX.md` must be what today's tree produces, and the generator inert.

Two jobs, and the second is the one that is easy to skip.

**The index cannot drift.** It is a derived artefact, so the only check worth
anything is to REGENERATE IT AND COMPARE — MEMORY.md's rule, and
`tests/test_intermediates_are_current` is the pattern this follows rather than
inventing a second one. Regeneration happens in a SUBPROCESS, into a scratch
path, never in place: a comparison against a file that was never rewritten
scores as current for the one reason that proves nothing, and this module has
to be safe to run beside `test_levers_are_live`, which perturbs module
constants inside the process it runs in.

**The generator must not blind an existing guard.**
`test_register_matches_code._defined_names` harvests every string literal in
`src/` into the population the judgement register is checked against. A new
`src/` module that merely NAMED a deleted lever — in a docstring, in a comment
turned into a string, in an example — would make that name "defined", and the
`DELETED` clause would stop excusing anything while every test stayed green.
That file measured exactly this about itself on 2026-08-31 and repaired it.
So two tests here: one says `src/model_index.py` contains no deleted lever as a
literal, and one re-runs that measurement WITH this file in the tree and
asserts the clause is still load-bearing.

⚠️ WHAT IS NOT CHECKED HERE. Nothing asserts that the index is USEFUL, or that
its joins are the right joins. Equality with the generator's output is a
staleness guard, not a correctness one, and a wrong join would be reproduced
faithfully for ever. The content is argued in the generator's docstrings and in
MODEL-LOG; this module only refuses to let the file and the tree disagree.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import model_index  # noqa: E402

import test_register_matches_code as REG  # noqa: E402

PY = ROOT / ".venv" / "bin" / "python"
GENERATOR = ROOT / "src" / "model_index.py"


def _regenerated() -> str:
    """The index as the tree produces it NOW, from a subprocess, into scratch.

    A subprocess for two reasons that are both about not measuring a moving
    tree: the suite runs modules that mutate `src/` module constants in their
    own process, and an in-process regeneration would inherit whatever the last
    one left behind. A scratch path because writing `MODEL-INDEX.md` from a
    test would make the comparison a comparison with itself.
    """
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "regenerated.md"
        done = subprocess.run([str(PY), str(GENERATOR), "--out", str(out)],
                              cwd=str(ROOT), capture_output=True, text=True)
        assert done.returncode == 0, (
            f"the generator failed, so nothing here has been checked:\n"
            f"{done.stdout}\n{done.stderr}")
        return out.read_text(encoding="utf-8")


def _first_difference(have: str, fresh: str):
    """The 1-based line where two renderings first differ, or None.

    A FUNCTION, so that the constructed violation below goes through the same
    detector the real check uses. A test that asserts a hand-rolled `!=` proves
    the `!=` operator works and nothing about the guard.
    """
    a, b = have.splitlines(), fresh.splitlines()
    for n, (left, right) in enumerate(zip(a, b), 1):
        if left != right:
            return n
    return None if len(a) == len(b) else min(len(a), len(b)) + 1


def test_the_committed_index_is_what_the_generator_produces_today():
    """⛔ Regenerate and compare. An mtime fence does not substitute.

    MEMORY.md, "Regenerate, don't grep": to know whether a derived artefact is
    current, purge and rebuild it — two cheaper checks each gave a confident
    wrong answer. The committed file exists so the index can be READ without
    running anything; this is the only thing keeping that reading honest.
    """
    committed = model_index.OUTPUT
    assert committed.exists(), (
        f"{committed.name} is not committed. Run "
        f"`.venv/bin/python src/model_index.py` and commit the result — the "
        f"generator is the authority, the file is the copy anyone can read.")
    fresh = _regenerated()
    have = committed.read_text(encoding="utf-8")
    where = _first_difference(have, fresh)
    assert where is None, (
        f"{committed.name} is not what the tree produces. First difference at "
        f"line {where}.\n"
        f"  committed: {have.splitlines()[where - 1:where]}\n"
        f"  generated: {fresh.splitlines()[where - 1:where]}\n"
        f"  Regenerate it — `.venv/bin/python src/model_index.py` — in the "
        f"SAME commit as whatever moved. Do not edit the file by hand; it is "
        f"generated, and a hand edit is how the registers it joins got into "
        f"the state it exists to report.")


def test_the_comparison_can_see_a_changed_index_and_goes_quiet_again():
    """(2) IT CAN SEE, on (3) A CONSTRUCTED input, and it stops seeing.

    The test above reports on the tree as it happens to be, and the tree is
    currently correct — so on its own it has never demonstrated it can catch
    the thing it was written for. The revert half matters as much: a detector
    that fires on everything would pass the first half and be worthless.
    """
    fresh = _regenerated()
    lines = fresh.splitlines()
    assert len(lines) > 20, "the index is too short to have been generated"
    victim = len(lines) // 2
    tampered = "\n".join(lines[:victim] + [lines[victim] + " edited"]
                         + lines[victim + 1:])
    assert _first_difference(tampered, fresh) == victim + 1, (
        "the comparison did not see a one-word edit in the middle of the "
        "index, so it would not see a stale committed copy either")
    assert _first_difference(fresh, fresh) is None, (
        "the comparison fires on an unchanged input, so its verdict carries "
        "no information")


def test_the_generator_is_deterministic():
    """Two runs on one tree must agree, or the guard above can never be trusted.

    An unsorted set, a timestamp or an absolute path in the output would make
    `test_the_committed_index_...` fail at random, and the cheap repair for a
    flaky guard is to delete it.
    """
    assert _first_difference(_regenerated(), _regenerated()) is None, (
        "two regenerations of an unchanged tree disagree: the generator is "
        "not deterministic. Look for an unsorted collection, a timestamp or "
        "an absolute path in the output.")


def test_the_index_names_every_row_of_every_register_it_joins():
    """(0) THE RIGHT SET, asserted rather than assumed, and both bounds.

    An index that silently dropped a register would look exactly like an index
    with nothing to report about it. So the population is stated: every
    scenario key, every deleted lever, every declared entry point must appear
    in the rendered text by name.
    """
    text = model_index.OUTPUT.read_text(encoding="utf-8")
    registers = model_index._load_registers()
    expected = (set(registers["DEFAULTS"])
                | set(registers["DELETED"])
                | set(registers["ENTRY_POINTS"])
                | set(registers["NOT_REGENERATED_HERE"]))
    missing = sorted(name for name in expected if name not in text)
    assert not missing, (
        f"the index joins registers it does not print: {missing}\n"
        f"  A register row that reaches no table is a row the index claims to "
        f"cover and does not.")
    scanned(expected, of=text.count("\n") + 1, low=0.02, high=0.9,
            what="register rows the index must name",
            denominator="lines in the index")


def test_the_generator_names_no_deleted_lever_as_a_literal():
    """⛔ The guard that keeps this module read-only IN EFFECT, not just in kind.

    `test_register_matches_code._names_bound_in(SRC, strings=True)` counts every
    string constant in `src/` as a defined name. A generator that wrote a
    deleted lever's name into a docstring would therefore DEFINE it, and the
    `DELETED` exemption would go inert — the same self-pollution that file found
    in its own table. Every name this generator prints is read out of a register
    at run time, and this is what holds that true.
    """
    import ast
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    literals = {node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    deleted = set(model_index._load_registers()["DELETED"])
    assert deleted, "the DELETED register is empty; this proves nothing"
    offenders = sorted(deleted & literals)
    assert not offenders, (
        f"src/model_index.py names deleted levers as string literals: "
        f"{offenders}\n"
        f"  Those names are now 'defined' as far as "
        f"`test_register_matches_code._defined_names` is concerned, and its "
        f"`DELETED` clause has stopped excusing them. Read the name out of the "
        f"register instead of typing it.")


def test_the_deleted_clause_is_still_load_bearing_with_this_module_in_the_tree():
    """The measurement itself, re-run — not the argument that it should hold.

    `test_register_matches_code` measured on 2026-08-31 that dropping its
    `t not in DELETED` clause changes the offender count, and that the clause
    had previously been inert because the table's own keys were harvested as
    strings. A new `src/` module is exactly the thing that could make it inert
    again, so the measurement is repeated here rather than reasoned about.
    """
    defined = REG._defined_names()
    named = REG._register_symbols()
    with_exemptions = REG._register_symbols_that_do_not_exist(named, defined)
    without = REG._register_symbols_that_do_not_exist(named, defined, exempt=set())
    assert not with_exemptions, (
        f"the register names symbols that do not exist: "
        f"{sorted(with_exemptions)} — that is "
        f"`test_register_matches_code`'s own failure and it should be fixed "
        f"there; this module only measures the clause.")
    assert len(without) > len(with_exemptions), (
        f"dropping the `t not in DELETED` clause changes nothing: "
        f"{len(without)} offenders either way. The exemption is INERT, which "
        f"means a deleted lever can sit in the register unseen. The usual "
        f"cause is a file in `src/` naming those levers as string literals — "
        f"see the test above.")


if __name__ == "__main__":
    # `run_module`, not a hand-rolled loop: it is the only runner that catches
    # `SkipTest` and `SystemExit`. Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
