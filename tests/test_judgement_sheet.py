"""`JUDGEMENT-SHEET.md` must be what today's tree produces, and say nothing new.

The sheet is a derived artefact, so the only check worth anything is to
REGENERATE IT AND COMPARE — MEMORY.md's rule, and the shape
`tests/test_model_index.py` and `tests/test_intermediates_are_current.py`
already use. Regeneration happens in a SUBPROCESS into a scratch path: a
comparison against a file that was never rewritten scores as current for the one
reason that proves nothing, and this module has to be safe to run beside
`test_levers_are_live`, which perturbs module constants inside its own process.

⛔ AND ONE GUARD THAT IS NOT ABOUT STALENESS. The sheet is a document ABOUT
levers, which makes it the single most likely file in `src/` to spell a deleted
lever's name — and `test_register_matches_code._names_bound_in(SRC, strings=True)`
counts every string literal in `src/` as a defined name. A generator that named
one would make the `DELETED` clause stop excusing anything while every test here
stayed green. The generator reads every name out of a register or a syntax tree
at run time; `test_the_generator_names_no_deleted_lever_as_a_literal` is what
holds that true.

⚠️ WHAT IS NOT CHECKED HERE. Nothing asserts the sheet is USEFUL, that its joins
are the right joins, or that any judgement call is well made. Equality with the
generator is a staleness guard, not a correctness one, and a wrong join would be
reproduced faithfully for ever.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))
import judgement_sheet  # noqa: E402
import model_index  # noqa: E402

PY = ROOT / ".venv" / "bin" / "python"
GENERATOR = ROOT / "src" / "judgement_sheet.py"


def _regenerated() -> str:
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

    A FUNCTION, so the constructed violation below goes through the same
    detector the real check uses; a hand-rolled `!=` in the test would prove the
    operator works and nothing about the guard.
    """
    a, b = have.splitlines(), fresh.splitlines()
    for n, (left, right) in enumerate(zip(a, b), 1):
        if left != right:
            return n
    return None if len(a) == len(b) else min(len(a), len(b)) + 1


def test_the_committed_sheet_is_what_the_generator_produces_today():
    """⛔ Regenerate and compare. An mtime fence does not substitute."""
    committed = judgement_sheet.OUTPUT
    assert committed.exists(), (
        f"{committed.name} is not committed. Run "
        f"`.venv/bin/python src/judgement_sheet.py` and commit the result — the "
        f"generator is the authority, the file is the copy anyone can read.")
    fresh = _regenerated()
    where = _first_difference(committed.read_text(encoding="utf-8"), fresh)
    assert where is None, (
        f"{committed.name} is not what the tree produces. First difference at "
        f"line {where}. Regenerate it in the SAME commit as whatever moved; do "
        f"not edit it by hand.")


def test_the_comparison_can_see_a_changed_sheet_and_goes_quiet_again():
    """(2) IT CAN SEE, on (3) A CONSTRUCTED input, and it stops seeing."""
    fresh = _regenerated()
    lines = fresh.splitlines()
    assert len(lines) > 20, "the sheet is too short to have been generated"
    victim = len(lines) // 2
    tampered = "\n".join(lines[:victim] + [lines[victim] + " edited"]
                         + lines[victim + 1:])
    assert _first_difference(tampered, fresh) == victim + 1, (
        "the comparison did not see a one-word edit in the middle of the "
        "sheet, so it would not see a stale committed copy either")
    assert _first_difference(fresh, fresh) is None, (
        "the comparison fires on an unchanged input, so its verdict carries "
        "no information")


def test_the_generator_is_deterministic():
    """Two runs on one tree must agree, or the guard above cannot be trusted."""
    assert _first_difference(_regenerated(), _regenerated()) is None, (
        "two regenerations of an unchanged tree disagree: look for an unsorted "
        "collection, a timestamp or an absolute path in the output.")


def test_the_sheet_names_every_registered_scenario_key():
    """(0) THE RIGHT SET, asserted rather than assumed, and both bounds.

    A sheet that silently dropped half the register would look exactly like a
    sheet with less to report. So the population is stated: every scenario key
    must appear in the rendered text by name.
    """
    text = judgement_sheet.OUTPUT.read_text(encoding="utf-8")
    keys = set(model_index._load_registers()["DEFAULTS"])
    missing = sorted(key for key in keys if key not in text)
    assert not missing, (
        f"the sheet joins scenario keys it never prints: {missing}")
    scanned(keys, of=text.count("\n") + 1, low=0.02, high=0.9,
            what="scenario keys the sheet must name",
            denominator="lines in the sheet")


def test_the_register_rows_survive_the_parse():
    """The parser drops a malformed row by design — so count what it kept.

    The register has already lost status markers to rows whose cell count did
    not match the header. Dropping such a row is right; dropping it SILENTLY
    would reproduce that defect one layer up, so the count is asserted against
    the number of table rows actually in the file.
    """
    sheet = judgement_sheet.build()
    text = judgement_sheet.REGISTER.read_text(encoding="utf-8")
    candidates = [line for line in text.splitlines()
                  if line.startswith("| ") and line.count("|") >= 5]
    kept = sheet["parsed"]["named"] + sheet["parsed"]["structural"]
    assert kept, "the parser kept no register rows at all"
    scanned(range(kept), of=len(candidates), low=0.5, high=1.0,
            what="register rows the parser kept",
            denominator="pipe-delimited rows in JUDGEMENT-CALLS.md")


def test_the_generator_names_no_deleted_lever_as_a_literal():
    """⛔ The guard that keeps this module from blinding another one."""
    tree = ast.parse(GENERATOR.read_text(encoding="utf-8"))
    literals = {node.value for node in ast.walk(tree)
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    deleted = set(model_index._load_registers()["DELETED"])
    assert deleted, "the DELETED register is empty; this proves nothing"
    offenders = sorted(deleted & literals)
    assert not offenders, (
        f"src/judgement_sheet.py names deleted levers as string literals: "
        f"{offenders}\n"
        f"  Those names are now 'defined' as far as "
        f"`test_register_matches_code` is concerned, so its DELETED clause "
        f"excuses nothing. Read the name out of a register instead.")


if __name__ == "__main__":
    raise SystemExit(run_module(vars(sys.modules[__name__])))
