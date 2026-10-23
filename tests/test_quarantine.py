"""The withdrawn in-sample scores stay withdrawn.

Owner, 2026-10-23 (OWNER-DECISIONS-ANSWERED.md item 29): "I WANT EXACTLY ZERO
chance they are being read and accepted blindly." Every backtest score made
before that day was scored with settings chosen on the election scored or a
later one (rounds/2026-10-23-out-of-sample/POLLSTER-ON-RECORD.md). The scores
were retired from the pages and the ledger, and their files were moved out of
the repository to the quarantine folder its README describes
(audits/2026-10-23-site-sweep/BRIEF-step0-withdraw-scores.md, items 1-5).

Two claims, each scanned over a stated, bounded population and each shown to
fire on a planted violation and to go quiet when it is reverted (CLAUDE.md §4,
"A test that asserts ABSENCE"):

(a) **Nothing under** ``src/ tests/ content/ docs-public/ site/`` **names the
    quarantine folder.** The needle is the folder's own name, built from parts
    here so this module does not carry it. It is the LOCATION, not the moved
    files' names: ``compare_history`` writing a new ``history.json`` to
    ``data/processed`` is the re-scoring the plan needs, and a check on the
    file name would forbid it (PLAN-REVIEW.md change 9). That case is asserted
    quiet below. "Reads one" is checked statically, as a path in the bytes of
    a file: a path assembled at run time from pieces would pass, so that half
    is argued, not tested.

(b) **No backtest score is held or printed without its label.** A registry
    token whose source is a backtest (:data:`SCORE_PREFIXES`) must carry
    ``label = "in-sample"`` or ``label = "forward-chained"``, and every built
    page that prints it must print that label beside it
    (:data:`BESIDE` characters either side, tags stripped). On 2026-10-23 no
    such token exists, so the live half asserts an empty set over the whole
    registry and the planted token is what shows the detector can see.
"""
from __future__ import annotations

import html as _html
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

#: The quarantine folder's name, from parts, so this file does not hold it.
NEEDLE = ("jhb-election-model" + "-" + "2026-10-23" + "-in-sample").encode()
#: The trees claim (a) covers (the brief's list).
ROOTS = ("src", "tests", "content", "docs-public", "site")
#: Sources that state a backtest result: the scoreboard, the past-elections
#: panel, and a pinned panel comparison.
SCORE_PREFIXES = ("validation:", "history:", "compare_history:")
LABELS = ("in-sample", "forward-chained")
#: How far either side of a printed figure its label may sit, in characters of
#: page text.
BESIDE = 200
REGISTRY = ROOT / "content" / "joburg" / "stats.toml"


# ---------------------------------------------------------------- detectors

def files_under(roots, base: Path = ROOT) -> list[Path]:
    """Every file under ``roots``, bytecode caches aside."""
    out = []
    for r in roots:
        out += [p for p in (base / r).rglob("*")
                if p.is_file() and "__pycache__" not in p.parts]
    return out


def naming_the_quarantine(paths) -> list[Path]:
    """The files among ``paths`` whose bytes contain :data:`NEEDLE`."""
    return [p for p in paths if NEEDLE in p.read_bytes()]


def unlabelled_tokens(registry: dict) -> list[str]:
    """Registry tokens with a backtest source and no permitted label."""
    return sorted(k for k, v in registry.items()
                  if isinstance(v, dict)
                  and str(v.get("source", "")).startswith(SCORE_PREFIXES)
                  and v.get("label") not in LABELS)


def score_tokens(registry: dict) -> dict[str, str]:
    """Labelled backtest tokens and the label each must be printed with."""
    return {k: v["label"] for k, v in registry.items()
            if isinstance(v, dict)
            and str(v.get("source", "")).startswith(SCORE_PREFIXES)
            and v.get("label") in LABELS}


def _text(fragment: str) -> str:
    return _html.unescape(re.sub(r"<[^>]+>", " ", fragment))


def printed_without_label(pages: dict[str, str], tokens: dict[str, str]) -> list[str]:
    """``page:token`` for each printing of a labelled token whose label is
    not within :data:`BESIDE` characters of page text either side."""
    out = []
    for name, page in pages.items():
        for tok, label in tokens.items():
            for m in re.finditer(rf'<span\b[^>]*\bdata-token="{re.escape(tok)}"[^>]*>.*?</span>',
                                 page, re.S):
                before = _text(page[:m.start()])[-BESIDE:]
                after = _text(page[m.end():])[:BESIDE]
                if label.lower() not in (before + " " + after).lower():
                    out.append(f"{name}:{tok}")
    return out


def registry_population(text: str) -> tuple[dict, int]:
    """The registry's token tables, and the count of ``[name]`` headers that
    declare them (``[audit]`` aside), read independently of TOML."""
    reg = {k: v for k, v in tomllib.loads(text).items()
           if k != "audit" and isinstance(v, dict)}
    headers = [h for h in re.findall(r"^\[([^\[\]]+)\]\s*(?:#.*)?$", text, re.M)
               if h != "audit"]
    return reg, len(headers)


def built_pages() -> dict[str, str]:
    return {p.relative_to(ROOT).as_posix(): p.read_text(encoding="utf-8")
            for p in (ROOT / "site").rglob("*.html")}


# ---------------------------------------------------------------- (a)

def test_nothing_in_the_tree_names_the_quarantine():
    population = files_under(ROOTS)
    tracked = subprocess.run(["git", "ls-files", "--", *ROOTS], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
    # every root contributes, and the walk sees the tracked tree and not
    # three times it (an untracked build output or a broken filter)
    for r in ROOTS:
        assert any(p.is_relative_to(ROOT / r) for p in population), f"nothing scanned under {r}/"
    scanned(population, of=len(tracked), low=0.9, high=1.5,
            what="files scanned under " + ", ".join(ROOTS),
            denominator="files git tracks under those roots")
    assert naming_the_quarantine(population) == []


def test_a_planted_read_of_the_quarantine_is_caught_and_its_revert_clears():
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        (base / "src").mkdir()
        f = base / "src" / "reader.py"
        quiet = 'json.loads(Path("data/processed/history.json").read_text())\n'
        f.write_text(quiet, encoding="utf-8")
        paths = files_under(("src",), base)
        assert naming_the_quarantine(paths) == [], "a read of data/processed/history.json was flagged"
        f.write_text('json.loads(Path("/Users/x/projects/quarantine/' + NEEDLE.decode()
                     + '/data/processed/history.json").read_text())\n', encoding="utf-8")
        assert naming_the_quarantine(paths) == [f]
        f.write_text(quiet, encoding="utf-8")
        assert naming_the_quarantine(paths) == []


# ---------------------------------------------------------------- (b)

def test_no_backtest_score_is_held_without_its_label():
    text = REGISTRY.read_text(encoding="utf-8")
    reg, n_headers = registry_population(text)
    # the scan covers every token the registry declares, counted two ways
    scanned(reg, of=n_headers, low=1.0, high=1.0,
            what="registry tokens read by TOML", denominator="[name] headers in stats.toml")
    assert unlabelled_tokens(reg) == []


def test_every_printed_score_carries_its_label_beside_it():
    reg, _ = registry_population(REGISTRY.read_text(encoding="utf-8"))
    pages = built_pages()
    html_files = list((ROOT / "site").rglob("*.html"))
    scanned(pages, of=len(html_files), low=1.0, high=1.0,
            what="built pages read", denominator="html files under site/")
    with_tokens = [n for n, p in pages.items() if 'data-token="' in p]
    scanned(with_tokens, of=len(pages), low=0.5, high=1.0,
            what="built pages that print a registry token", denominator="built pages")
    assert printed_without_label(pages, score_tokens(reg)) == []


def test_a_planted_unlabelled_score_is_caught_and_its_revert_clears():
    planted = {"bt_wins": {"mode": "free", "source": "validation:total.wins", "format": "int"},
               "bt_panel": {"mode": "fixed", "value": 1, "source": "compare_history:crps"},
               "n_vds": {"mode": "free", "source": "model:n_vds"}}
    assert unlabelled_tokens(planted) == ["bt_panel", "bt_wins"]
    planted["bt_wins"]["label"] = "in-sample"
    planted["bt_panel"]["label"] = "forward-chained"
    assert unlabelled_tokens(planted) == []
    planted["bt_wins"]["label"] = "out-of-sample"          # not a permitted label
    assert unlabelled_tokens(planted) == ["bt_wins"]

    span = '<span class="mstat" data-token="bt_wins" data-prov="x">7</span>'
    bare = {"p.html": f"<p>It wins in {span} of 8 metros.</p>"}
    labelled = {"p.html": f"<p>In-sample: it wins in {span} of 8 metros.</p>"}
    far = {"p.html": "<p>In-sample.</p>" + "<p>" + "x " * BESIDE + f"It wins in {span}.</p>"}
    tokens = {"bt_wins": "in-sample"}
    assert printed_without_label(bare, tokens) == ["p.html:bt_wins"]
    assert printed_without_label(labelled, tokens) == []
    assert printed_without_label(far, tokens) == ["p.html:bt_wins"]
    assert printed_without_label(bare, {}) == []


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
