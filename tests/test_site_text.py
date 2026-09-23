"""THE SITE'S WORDS GO OUT FOR EDITING AND COME BACK WITHOUT THE FIGURES MOVING.

`src/site_text.py` exports every editable prose block to one markdown file and
applies the edits back to the SOURCE the block came from. Two properties make
that safe rather than convenient, and both are asserted here:

* **a round trip changes nothing.** Export, apply without editing, and no file
  moves. A tool whose no-op is not a no-op cannot be trusted with the rest.
* **a figure cannot be edited.** `{{token}}` and `[[token]]` are filled in from
  the run that produced them; an editor who types `62%` over one publishes a
  number nothing can trace, which is CLAUDE.md §2's whole subject. `--apply`
  refuses the block.

⛔ **EVERY TEST POINTS THE MODULE AT A TEMPORARY FILE.** `SITE-TEXT.md` at the
repo root may hold edits somebody is part-way through, and a test that writes
over them would destroy work while reporting success.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module                            # noqa: E402

import site_text                                                 # noqa: E402


def _export_to(tmp: Path):
    """Export into a throwaway file and return its text."""
    saved, site_text.OUT = site_text.OUT, tmp
    try:
        site_text.export()
        return tmp.read_text(encoding="utf-8")
    finally:
        site_text.OUT = saved


def _apply_from(tmp: Path, dry_run=True):
    saved, site_text.OUT = site_text.OUT, tmp
    try:
        return site_text.apply(dry_run=dry_run)
    finally:
        site_text.OUT = saved


def test_the_export_finds_prose_in_every_source_it_claims():
    """The export is only useful if it reaches all three kinds of source."""
    with tempfile.TemporaryDirectory() as d:
        text = _export_to(Path(d) / "x.md")
    for source in ("forecast-sheet.html", "docs-public/", "claims.toml"):
        assert source in text, (
            f"no block came from {source}; the export claims to cover it, and "
            f"an editor would never see those words.")
    assert len(re.findall(r"<!-- block ", text)) > 50, (
        "suspiciously few blocks — a selector probably stopped matching.")


def test_nothing_inside_a_generated_region_is_offered_for_editing():
    """The build rewrites those, so an edit there is lost at the next run."""
    sheet = (ROOT / "forecast-sheet.html").read_text(encoding="utf-8")
    regions = site_text.GENERATED.findall(sheet)
    assert regions, (
        "forecast-sheet.html has no generated regions, so this test is "
        "guarding nothing — check GENERATED still matches the markers.")
    inside = site_text.GENERATED.search(sheet).group(0)
    sample = [t for t in re.findall(r">([^<>{}]{40,})<", inside) if t.strip()]
    assert sample, "no sample text inside a generated region to test with."
    with tempfile.TemporaryDirectory() as d:
        text = _export_to(Path(d) / "x.md")
    for chunk in sample[:5]:
        flat = re.sub(r"\s+", " ", chunk.strip())
        assert flat not in text, (
            f"text from inside a generated region was offered for editing: "
            f"{flat[:60]!r}. The build overwrites it on the next run.")


def test_an_unedited_round_trip_changes_nothing():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "x.md"
        _export_to(tmp)
        before = {p: p.read_bytes() for p in
                  [ROOT / "forecast-sheet.html",
                   ROOT / "content" / "joburg" / "claims.toml",
                   *(ROOT / "docs-public").glob("*.md")]}
        _apply_from(tmp, dry_run=False)
        after = {p: p.read_bytes() for p in before}
    moved = [p.name for p in before if before[p] != after[p]]
    assert not moved, f"an unedited apply rewrote {moved}."


def test_typing_a_number_over_a_figure_is_refused():
    """The property the whole tool exists to have.

    Mutation-checked 2026-09-23: drop the placeholder comparison in `apply` and
    this test fails — the edit sails through and a hand-typed number reaches the
    page.
    """
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "x.md"
        text = _export_to(tmp)
        m = re.search(r"<!-- block ([\w-]+)[^>]*-->\n\*[^*]+\*\n\n"
                      r"([^\n]*\{\{\w+\}\}[^\n]*)\n", text)
        assert m, "no exported block carries a {{token}} to test with."
        edited = (text[:m.start(2)]
                  + re.sub(r"\{\{\w+\}\}", "62%", m.group(2), count=1)
                  + text[m.end(2):])
        tmp.write_text(edited, encoding="utf-8")
        try:
            _apply_from(tmp, dry_run=True)
        except SystemExit as refusal:
            assert "figures" in str(refusal), str(refusal)
        else:
            raise AssertionError(
                "a block whose {{token}} was replaced by a typed number was "
                "accepted. That is how a figure nothing can trace reaches a "
                "reader.")


def test_a_wording_edit_reaches_its_own_source_file():
    """And only that file, and only that block."""
    target = ROOT / "docs-public" / "about-the-model.md"
    original = target.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "x.md"
        text = _export_to(tmp)
        block = next(
            m for m in re.finditer(
                r"<!-- block ([\w-]+) -->\n\*md\*\n\n(.*?)\n\n<!-- /block \1 -->",
                text, re.S)
            if "{{" not in m.group(2) and m.group(2) in original)
        marker = "ROUND-TRIP MARKER."
        edited = text[:block.end(2)] + " " + marker + text[block.end(2):]
        tmp.write_text(edited, encoding="utf-8")
        try:
            _apply_from(tmp, dry_run=False)
            now = target.read_text(encoding="utf-8")
            assert marker in now, "the edit never reached the source file."
            assert now.count(marker) == 1, "the edit was written more than once."
        finally:
            target.write_text(original, encoding="utf-8")
    assert target.read_text(encoding="utf-8") == original


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
