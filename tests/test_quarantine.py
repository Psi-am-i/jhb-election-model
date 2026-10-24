"""The withdrawn in-sample scores stay withdrawn.

Owner, 2026-10-23 (OWNER-DECISIONS-ANSWERED.md item 29): "I WANT EXACTLY ZERO
chance they are being read and accepted blindly." Every backtest score made
before that day was scored with settings chosen on the election scored or a
later one (rounds/2026-10-23-out-of-sample/POLLSTER-ON-RECORD.md). The scores
are retired from the pages and the registry
(audits/2026-10-23-site-sweep/BRIEF-step0-withdraw-scores.md, items 1-3, 6;
MODEL-LOG §1.337). The in-sample files themselves stay in the project: the
copies made outside it were deleted on 2026-10-23 by the owner's instruction,
so this module asserts nothing about any folder outside the repository.

Three claims, each scanned over a stated, bounded population and each shown
to fire on a planted violation and to go quiet when it is reverted
(CLAUDE.md §4, "A test that asserts ABSENCE"):

(a) **The scoring section is the withdrawal notice.** The file the methodology
    splices in (``build_site.VALIDATION_SOURCE``) is byte for byte what
    ``build_validation`` writes while ``WITHDRAWN`` is set, and the notice
    carries no figure but its date. This is the population check too: the
    file scanned is the one the build reads, not a copy.

(b) **No backtest score is held or printed without its label.** A registry
    token whose source is a backtest (:data:`SCORE_PREFIXES`) must carry
    ``label = "in-sample"`` or ``label = "forward-chained"``, and every built
    page that prints it must print that label beside it
    (:data:`BESIDE` characters either side, tags stripped). On 2026-10-24 no
    such token exists, so the live half asserts an empty set over the whole
    registry and the planted token is what shows the detector can see. It
    does not forbid ``compare_history`` writing a new ``history.json``: the
    re-scoring the plan needs (PLAN-REVIEW.md change 9).

(c) **Every model-change report that holds a score says it is in-sample.**
    Each ``reports/model-changes/<round>/report.html`` whose ``backtest.json``
    holds scores (not ``null``) carries :data:`BANNER`. The population is
    every tracked ``backtest.json``, so a round added later is scanned.
"""
from __future__ import annotations

import html as _html
import re
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

#: The first words of the banner each scored model-change report carries.
BANNER = "These scores are in-sample"
REPORTS = ROOT / "reports" / "model-changes"
#: Sources that state a backtest result: the scoreboard, the past-elections
#: panel, and a pinned panel comparison.
SCORE_PREFIXES = ("validation:", "history:", "compare_history:")
LABELS = ("in-sample", "forward-chained")
#: How far either side of a printed figure its label may sit, in characters of
#: page text.
BESIDE = 200
REGISTRY = ROOT / "content" / "joburg" / "stats.toml"


# ---------------------------------------------------------------- detectors

def notice_problems(text: str, notice: str) -> list[str]:
    """Why ``text`` is not the withdrawal notice ``notice``: it differs from
    it, or it carries a digit outside the notice's own date."""
    out = []
    if text != notice:
        out.append("differs from build_validation.notice()")
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    body = re.sub(r"\b\d{1,2} [A-Z][a-z]+ \d{4}\b", "", body)
    if re.search(r"\d", body):
        out.append("carries a figure")
    return out


def scored_reports(base: Path = REPORTS) -> list[Path]:
    """The rounds under ``base`` whose ``backtest.json`` holds scores."""
    return sorted(p.parent for p in base.glob("*/backtest.json")
                  if json.loads(p.read_text(encoding="utf-8")) is not None)


def unbannered(rounds) -> list[Path]:
    """The rounds among ``rounds`` whose ``report.html`` lacks :data:`BANNER`."""
    return [r for r in rounds
            if BANNER not in (r / "report.html").read_text(encoding="utf-8")]


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

def test_the_scoring_section_is_the_withdrawal_notice():
    import build_site
    import build_validation
    assert build_validation.WITHDRAWN, "the scores are withdrawn; WITHDRAWN must stay set"
    source = build_site.VALIDATION_SOURCE
    assert source == ROOT / "docs-public" / "about-the-model.md", source
    notice = build_validation.notice()
    assert notice_problems(source.read_text(encoding="utf-8"), notice) == []
    # main() writes the notice and nothing else
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / "about.md"
        assert build_validation.main(["--out", str(out)]) in (0, None)
        assert out.read_text(encoding="utf-8") == notice
        assert sorted(p.name for p in Path(t).iterdir()) == ["about.md"]


def test_a_planted_score_in_the_section_is_caught_and_its_revert_clears():
    import build_validation
    notice = build_validation.notice()
    assert notice_problems(notice, notice) == []
    planted = notice + "\n| Johannesburg | 66.8 | 114.1 |\n"
    assert notice_problems(planted, notice) == ["differs from build_validation.notice()",
                                                "carries a figure"]
    assert notice_problems(notice, notice) == []


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


# ---------------------------------------------------------------- (c)

def test_every_scored_report_says_it_is_in_sample():
    tracked = subprocess.run(["git", "ls-files", "--", "reports/model-changes/*/backtest.json"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    on_disk = sorted(REPORTS.glob("*/backtest.json"))
    scanned(on_disk, of=len(tracked), low=1.0, high=1.0,
            what="backtest.json files read", denominator="backtest.json files git tracks")
    rounds = scored_reports()
    scanned(rounds, of=len(on_disk), low=0.1, high=1.0,
            what="rounds whose backtest.json holds scores", denominator="backtest.json files")
    assert unbannered(rounds) == []
    assert BANNER in (REPORTS / "template.html").read_text(encoding="utf-8")


def test_a_planted_unbannered_report_is_caught_and_its_revert_clears():
    with tempfile.TemporaryDirectory() as t:
        base = Path(t)
        scored, empty = base / "r1", base / "r2"
        for r, bt in ((scored, {"panel": 1}), (empty, None)):
            r.mkdir()
            (r / "backtest.json").write_text(json.dumps(bt), encoding="utf-8")
            (r / "report.html").write_text("<p>scores</p>", encoding="utf-8")
        assert scored_reports(base) == [scored], "a null backtest.json was counted"
        assert unbannered(scored_reports(base)) == [scored]
        (scored / "report.html").write_text(f"<p>{BANNER}.</p><p>scores</p>", encoding="utf-8")
        assert unbannered(scored_reports(base)) == []


def test_the_template_prints_the_banner_only_for_a_report_with_scores():
    """build_report keeps the template's banner when its backtest holds scores
    and cuts it when the backtest is null (brief 3 item 10). Both directions,
    on the real template."""
    sys.path.insert(0, str(REPORTS))
    import build_report
    page = (REPORTS / "template.html").read_text(encoding="utf-8")
    scored = build_report.in_sample_banner(page, [{"panel": 1}])
    empty = build_report.in_sample_banner(page, None)
    assert BANNER in scored and BANNER not in empty
    assert "__IN_SAMPLE_" not in scored and "__IN_SAMPLE_" not in empty
    # the rest of the page is the same either way: only the banner's line differs
    banner_line = next(ln for ln in scored.splitlines(keepends=True) if BANNER in ln)
    assert scored.replace(banner_line, "", 1) == empty


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
