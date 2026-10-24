"""The corrected date of a release's corrections entries comes from one place.

`build_site.RELEASE_DATE_MARK` is typed in an entry's heading and its
`data-asof` values; `build_site.fill_release_date` writes the build's date
there, and `build_site.release_date` says which date
(audits/2026-10-23-site-sweep/BRIEF-3-item35.md, item 9). Inputs are
constructed: a planted entry, and a throwaway ledger.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import build_site as B  # noqa: E402
import publication as P  # noqa: E402
from _support import run_module  # noqa: E402

MARK = B.RELEASE_DATE_MARK
ENTRY = (f'## <span data-asof="{MARK}">"A wrong sentence"</span> — published '
         f'2 October 2026, corrected {MARK}\n\n'
         f'<span data-asof="{MARK}">**What was wrong.** It was wrong.</span>\n')


def test_the_mark_is_iso_inside_data_asof_and_long_elsewhere():
    out = B.fill_release_date(ENTRY, "2026-10-24")
    assert out.count('data-asof="2026-10-24"') == 2, out
    assert "corrected 24 October 2026" in out, out
    assert MARK not in out, out
    # the long form never reaches an attribute, the ISO form never the prose
    assert 'data-asof="24 October 2026"' not in out
    assert "corrected 2026-10-24" not in out
    # a single-digit day is not zero-padded in prose
    assert "corrected 3 November 2026" in B.fill_release_date(ENTRY, "2026-11-03")


def test_text_without_the_mark_is_unchanged_and_a_planted_mark_is_replaced():
    plain = '## <span data-asof="2026-10-23">"x"</span> — corrected 23 October 2026\n'
    assert B.fill_release_date(plain, "2026-10-24") == plain
    planted = plain + ENTRY
    out = B.fill_release_date(planted, "2026-10-24")
    assert MARK not in out
    assert out.startswith(plain), "text outside the mark moved"


def test_render_doc_writes_every_mark_on_a_planted_corrections_page():
    """The real corrections page with a planted entry, rendered with a
    constructed date: no mark survives the renderer. Planted, so the test
    still sees once the release's own marks are replaced after publication."""
    real = (ROOT / "docs-public" / "corrections.md").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "corrections.md"
        src.write_text(real + "\n" + ENTRY, encoding="utf-8")
        html = B.render_doc(src, "Corrections", "", "corrections.html", False, "x",
                            release="2026-10-24")
    assert MARK not in html
    assert "corrected 24 October 2026" in html
    assert 'data-asof="2026-10-24"' in html


def _publish(root: Path, when: str) -> None:
    P.append("joburg", [P.Row(token="t", value=1, display="1", fmt="int", source="s",
                              model_run_id="r1", run_at=when, as_of=None,
                              published_at=when, change_class=None, reason=None,
                              movement="new")], root=root)


def test_as_published_takes_the_newest_publication_and_otherwise_the_build_instant():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _publish(root, "2026-10-21T08:00:00Z")
        _publish(root, "2026-10-24T23:59:59Z")
        assert B.release_date(True, "joburg", root) == "2026-10-24"
        # not as-published: the build's own instant, never the ledger's
        assert B.release_date(False, "joburg", root, "2026-10-26T00:00:01Z") == "2026-10-26"
        # as-published with nothing published falls back to the instant
        empty = root / "empty"
        empty.mkdir()
        assert B.release_date(True, "joburg", empty, "2026-10-26T00:00:01Z") == "2026-10-26"
    # with no stamp given, today's UTC day
    assert B.release_date() == P.utc_now()[:10]


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
