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


# ---------------------------------------------------------------------------
# /methodology's "The judgement calls", generated from the register's Plain
# fields (owner, 2026-10-02). The same rule as the sheet: regenerate, compare.
# ---------------------------------------------------------------------------

import re  # noqa: E402
import tomllib  # noqa: E402

STATS = ROOT / "content" / "joburg" / "stats.toml"


def _regenerated_section() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "section.md"
        done = subprocess.run([str(PY), str(GENERATOR), "--section-out", str(out)],
                              cwd=str(ROOT), capture_output=True, text=True)
        assert done.returncode == 0, (
            f"the section generator failed, so nothing here has been checked:\n"
            f"{done.stdout}\n{done.stderr}")
        return out.read_text(encoding="utf-8").rstrip("\n")


def _committed_section() -> str:
    return judgement_sheet.section_in(
        judgement_sheet.METHODOLOGY.read_text(encoding="utf-8"))


def _titles(section: str) -> list[str]:
    """The bold lead of every call paragraph in a rendered section."""
    return re.findall(r"(?m)^\*\*(.+?)\.\*\* ", section)


def _population_mismatch(register_text: str, section: str) -> tuple[list, list]:
    """(fields missing from the section, calls in it with no field), in order.

    A FUNCTION, so the constructed register edits below go through the same
    detector the real check uses.
    """
    want = [c["title"] for c in judgement_sheet.plain_calls(register_text)]
    have = _titles(section)
    return ([t for t in want if t not in have], [t for t in have if t not in want])


def _entry_count(register_text: str) -> int:
    return sum(1 for line in register_text.splitlines()
               if judgement_sheet._ENTRY.match(line))


def test_the_methodology_section_is_what_the_generator_produces_today():
    """⛔ Regenerate in a subprocess and compare with the committed region."""
    where = _first_difference(_committed_section(), _regenerated_section())
    assert where is None, (
        f"docs-public/methodology.md's 'The judgement calls' is not what the "
        f"register produces. First difference at line {where} of the region. "
        f"Run `.venv/bin/python src/judgement_sheet.py --methodology` (the site "
        f"build does it too) and commit the page with the register edit.")


def test_the_section_comparison_can_see_an_edit_and_goes_quiet_again():
    """(2) IT CAN SEE, on (3) A CONSTRUCTED input, and it stops seeing."""
    fresh = _regenerated_section()
    lines = fresh.splitlines()
    assert len(lines) > 5, "the section is too short to have been generated"
    victim = len(lines) // 2
    tampered = "\n".join(lines[:victim] + [lines[victim] + " edited"]
                         + lines[victim + 1:])
    assert _first_difference(tampered, fresh) == victim + 1
    assert _first_difference(fresh, fresh) is None


def test_every_call_with_a_plain_field_is_on_the_page_and_no_other():
    """(0) THE RIGHT SET, in BOTH directions, and (1) it looked.

    Register -> page: a field the page lacks. Page -> register: a call on the
    page that no field supports (a hand-typed paragraph inside the region).
    """
    text = judgement_sheet.REGISTER.read_text(encoding="utf-8")
    calls = judgement_sheet.plain_calls(text)
    section = _committed_section()
    missing, extra = _population_mismatch(text, section)
    assert not missing, f"fields the page does not carry: {missing}"
    assert not extra, f"calls on the page with no Plain field: {extra}"
    assert len(_titles(section)) == len(calls), (
        "the page carries a title twice, or the register does")
    assert len({c["title"] for c in calls}) == len(calls), (
        "two Plain fields share a title, so the page cannot tell them apart")
    scanned(calls, of=_entry_count(text), low=0.02, high=0.2,
            what="register entries carrying a Plain field",
            denominator="§ entries in JUDGEMENT-CALLS.md")


def test_the_population_check_sees_a_field_added_or_removed_and_goes_quiet():
    """(2)+(3): constructed register edits, each caught, each reverted."""
    text = judgement_sheet.REGISTER.read_text(encoding="utf-8")
    section = _committed_section()
    assert _population_mismatch(text, section) == ([], [])

    # ADD a field to the first live entry that has none.
    have = {(c["entry"], c["heading"]) for c in judgement_sheet.plain_calls(text)}
    lines = text.splitlines()
    for n, line in enumerate(lines):
        m = judgement_sheet._ENTRY.match(line)
        if (m and (m.group(1), m.group(2)) not in have
                and not any(r in line for r in judgement_sheet._RETIRED)):
            break
    else:
        raise AssertionError("no entry without a Plain field to add one to")
    added = "\n".join(lines[:n + 1] + ["", "**Plain — A constructed call.** "
                                        "Text."] + lines[n + 1:])
    assert _population_mismatch(added, section) == (["A constructed call"], [])

    # REMOVE the first field.
    first = judgement_sheet.plain_calls(text)[0]
    m = re.search(r"(?m)^\*\*Plain — " + re.escape(first["title"])
                  + r"\.\*\*.*?(?:\n\n|\Z)", text, re.S)
    removed = text[:m.start()] + text[m.end():]
    assert _population_mismatch(removed, section) == ([], [first["title"]])

    assert _population_mismatch(text, section) == ([], []), (
        "the detector does not go quiet on the unedited register")


def test_the_parser_refuses_a_field_it_cannot_place():
    """Each refusal on a constructed register, beside one it accepts."""
    good = "### §Z1 · a call — 1.0 — 🔴\n\n**Plain — A title.** Some text.\n"
    assert [c["title"] for c in judgement_sheet.plain_calls(good)] == ["A title"]
    bad = {
        "malformed": "### §Z1 · a call — 🔴\n\n**Plain.** Some text.\n",
        "outside an entry": "## Z. A part\n\n**Plain — T.** Some text.\n",
        "twice in one entry": good + "\n**Plain — Another.** More text.\n",
        "a backtick": "### §Z1 · a call — 🔴\n\n**Plain — T.** Uses `w`.\n",
        "a retired entry": "### §Z1 · a call — ⚫ deleted\n\n**Plain — T.** x.\n",
    }
    for why, text in bad.items():
        try:
            judgement_sheet.plain_calls(text)
        except ValueError:
            continue
        raise AssertionError(f"a Plain field with {why} was accepted")


def test_every_field_says_whether_play_can_move_it():
    """The owner's brief: each call says whether /play/ can change it."""
    calls = judgement_sheet.plain_calls(
        judgement_sheet.REGISTER.read_text(encoding="utf-8"))
    silent = [c["title"] for c in calls if "](play/)" not in c["body"]]
    assert not silent, f"Plain fields that never mention /play/: {silent}"


def _heading_numbers(heading: str) -> set[float]:
    return {float(x) for x in re.findall(r"(?<![\w.])\d+(?:\.\d+)?", heading)}


def _fixed_as_number(value: str) -> float | None:
    value = value.strip()
    try:
        return float(value[:-1]) / 100 if value.endswith("%") else float(value)
    except ValueError:
        return None


def _stale_fixed(rows: list[dict], register_text: str) -> tuple[list[str], int]:
    """Fixed facts that cite a register entry whose heading no longer states
    their value, and how many rows cite an entry at all."""
    headings: dict[str, list[str]] = {}
    for line in register_text.splitlines():
        m = judgement_sheet._ENTRY.match(line)
        if m:
            headings.setdefault(m.group(1), []).append(m.group(2))
    stale, cited = [], 0
    for row in rows:
        m = re.search(r"JUDGEMENT-CALLS\.md (§[A-Z]\d+)", str(row.get("source", "")))
        if not m:
            continue
        cited += 1
        value = _fixed_as_number(str(row.get("value", "")))
        if m.group(1) not in headings:
            stale.append(f"{row.get('value')!r} cites {m.group(1)}, which is not an entry")
        elif value is None or not any(
                abs(value - n) < 1e-9 or abs(value * 100 - n) < 1e-9
                for h in headings[m.group(1)] for n in _heading_numbers(h)):
            stale.append(f"{row.get('value')!r} is not the value {m.group(1)}'s "
                         f"heading states")
    return stale, cited


def test_every_fixed_figure_citing_a_judgement_call_is_that_calls_value():
    """A figure cleared for /methodology on a register entry's authority must
    be the value the entry states, or a changed call leaves a stale sentence
    cleared. (0)-(3) on the live rows and on a constructed one."""
    rows = list(tomllib.loads(STATS.read_text(encoding="utf-8"))
                .get("audit", {}).get("fixed", []))
    text = judgement_sheet.REGISTER.read_text(encoding="utf-8")
    stale, cited = _stale_fixed(rows, text)
    assert not stale, stale
    scanned(range(cited), of=len(rows), low=0.01, high=0.5,
            what="fixed facts citing a JUDGEMENT-CALLS entry",
            denominator="[[audit.fixed]] rows in stats.toml")
    i = next(n for n, r in enumerate(rows) if "JUDGEMENT-CALLS.md §" in r["source"])
    moved = rows[:i] + [{**rows[i], "value": "41%"}] + rows[i + 1:]
    assert len(_stale_fixed(moved, text)[0]) == 1, "a changed value was not seen"
    assert _stale_fixed(rows, text)[0] == [], "the detector does not go quiet"


def test_the_section_passes_the_number_gate_as_prose():
    """The region is scanned as PROSE (its words are a person's), and every
    figure in it is cleared by a fixed fact. A typed figure is caught."""
    import markdown
    import stats
    html = markdown.markdown(_committed_section(),
                             extensions=["tables", "fenced_code", "smarty"])
    cfg = stats.load_audit_config(stats.load_registry(STATS))

    def blocking(page):
        hits = stats.scan_numbers(page, page="methodology.html", fixed=cfg["fixed"])
        return hits, [h for h in hits if stats.is_blocking(h)]

    hits, blocked = blocking(html)
    assert not blocked, [f"{h['value']} …{h['context']}…" for h in blocked]
    cleared = [h for h in hits if h["status"] == "fixed" and h["region"] == "prose"]
    assert cleared, ("no figure in the section was cleared as prose: either it "
                     "carries none, or the region is being exempted")
    typed = html.replace("</p>", " It moves 17 seats.</p>", 1)
    assert len(blocking(typed)[1]) == 1, "a typed figure in the section passed"
    assert not blocking(html)[1]


if __name__ == "__main__":
    raise SystemExit(run_module(vars(sys.modules[__name__])))
