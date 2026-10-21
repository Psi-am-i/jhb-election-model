"""Every tooltip on the site: one writer, one structure, one sentence per figure.

Owner, 2026-10-22 (audits/2026-10-22-tooltips/BRIEF.md): two lines everywhere,

    35% chance since 21 October. Was 45% on 6 October.
    SOURCE: This Model. The % of 5,000 simulations where the ANC was the largest party.

and "every time you use a technical part of the model, simply say 'This Model'".

What is checked, and how each check is shown to see:

* **The table covers the published set, both ways.** Every token a build
  publishes matches exactly one pattern of `tooltip_says.SAYS`, and every
  pattern matches a published token. The population is the build's own
  `changes.json`, and it is shown to be exactly the set of figures on the
  built pages (both directions), so the scan is of the right thing.
* **A token with no sentence stops the build**, end to end: a probe token
  injected into a copy of the forecast sheet is refused by name, and the same
  build without it passes.
* **Line 2 names no part of the model.** Every built tooltip's second line is
  scanned for file names and internal words; a constructed tooltip carrying
  one is caught, and the clean form is not.
* **Line 1's six states** (`build_site.tooltip_text`), on constructed changes.

Inputs are constructed except where a test says it builds the tree.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import tooltip_says as T  # noqa: E402
from _support import run_module, skip  # noqa: E402

FACTS = T.Facts(n=5000, n_hist=1000, n_val=400, val_year="2021",
                groups={"black_african": "Black African", "white": "White"})


# --- the table, on constructed names ------------------------------------------

def test_a_constructed_unmatched_token_is_reported_and_the_report_clears():
    good = ["seats.ANC.median", "coal.ANC+DA.majority", "home.seats.da_lo"]
    assert T.unsaid(good) == [], T.unsaid(good)
    assert T.unsaid(good + ["probe.nopattern"]) == [("probe.nopattern", 0)]
    assert T.unsaid(good) == []
    try:
        T.says("probe.nopattern", FACTS)
    except SystemExit as e:
        assert "probe.nopattern" in str(e)
    else:
        raise AssertionError("says() gave a sentence for a token with no pattern")


def test_a_party_code_must_be_a_party():
    """A pattern with a party slot matches only a known party: an unknown code
    is unsaid, not printed as a name."""
    assert len(T.matches("seats.ANC.median")) == 1
    assert T.matches("seats.NOTAPARTY.median") == []
    assert T.matches("home.seats.anc_hi") and T.matches("home.seats.zz_hi") == []
    # the Others row is its own sentence, never a party called Others
    assert [s.says for s, _ in T.matches("seats.OTHERS.median")] == [
        s.says for s in T.SAYS if s.pattern == r"seats\.OTHERS\.median"]


def test_the_sentence_names_the_party_and_the_count():
    unit, who, said = T.says("home.p_anc_largest", FACTS)
    assert (unit, who) == ("chance", "This Model")
    assert said == "The % of 5,000 simulations where the ANC was the largest party.", said
    # the count is the run's, not typed: another count, another sentence
    assert "1,234 simulations" in T.says("home.p_anc_largest", T.Facts(n=1234))[2]
    assert T.says("coal.ANC+ASA+EFF.majority", FACTS)[2].startswith(
        "The % of 5,000 simulations where the ANC, ActionSA and the EFF together")
    assert "Black African voters" in T.says("play.votes.DA.black_african", FACTS)[2]


# --- line 2 names no part of the model ----------------------------------------

#: What line 2 may not carry (the owner's rule, tooltip_says' header): a file,
#: a code name, or an internal word.
TECHNICAL = re.compile(r"\.csv|\.json|\.bin|src/|site/|[a-z]_[a-z]|\bdraws?\b|\bpools?\b|"
                       r"\bfolds?\b|\bregimes?\b|\blevers?\b|\bspecs?\b|\bthe run\b|"
                       r"computed at build|turnout_tilt|\bCRPS\b|MODEL-LOG|JUDGEMENT", re.I)


def technical_words(tip: str) -> list[str]:
    lines = tip.split("\n")
    if len(lines) != 2 or not lines[1].startswith("SOURCE: "):
        return [f"not two lines with SOURCE: ({tip!r})"]
    return TECHNICAL.findall(lines[1])


def test_the_technical_word_detector_sees_and_goes_quiet():
    clean = ("58% chance since 21 October.\nSOURCE: This Model. The % of 5,000 "
             "simulations where the ANC was the largest party.")
    assert technical_words(clean) == []
    assert technical_words(clean.replace("simulations", "seat_draws.csv draws"))
    assert technical_words(clean.replace("\nSOURCE:", " Source:"))
    assert technical_words(clean) == []


def test_no_sentence_in_the_table_carries_a_technical_word():
    """Every sentence and source the table holds, its placeholders taken out
    (they are filled with names and counts, which the built-page test below
    scans as the reader sees them)."""
    for say in T.SAYS:
        line = re.sub(r"\{[^}]*\}", "X", f"x.\nSOURCE: {say.who}. {say.says}")
        assert technical_words(line) == [], (say.pattern, technical_words(line))


# --- line 1: the six states ---------------------------------------------------

def _c(token="home.p_anc_largest", display="35%", movement="material", previous="45%",
       previous_since="2026-10-06T10:00:00Z", since=None):
    return {"token": token, "display": display, "movement": movement,
            "previous": previous, "previous_since": previous_since,
            "previous_published_at": previous_since, "since": since}


def _tip(c, *, publishing=True, registry=None, by_token=None):
    import build_site as B
    return B.tooltip_text(c, by_token=by_token or {c["token"]: c}, registry=registry or {},
                          edition="2026-10-21", publishing=publishing, facts=FACTS)


def test_line_one_moved_unchanged_new_and_unpublished():
    moved = _tip(_c())
    assert moved == ("35% chance since 21 October. Was 45% on 6 October.\nSOURCE: This "
                     "Model. The % of 5,000 simulations where the ANC was the largest "
                     "party."), moved
    assert _tip(_c(), publishing=False).startswith(
        "35% chance in this build. Was 45% on 6 October.\n")
    same = _c(display="45%", movement="none", since="2026-09-30T00:00:00Z")
    assert _tip(same).startswith("45% chance since 30 September.\n")
    assert _tip(same, publishing=False).startswith("45% chance since 30 September.\n")
    new = _c(movement="new", previous=None, previous_since=None)
    assert _tip(new).startswith("35% chance since 21 October.\n")
    assert _tip(new, publishing=False).startswith("35% chance in this build.\n")
    typed = _tip(new, registry={"home.p_anc_largest": {"on_site": "2026-08-08"}})
    assert typed.startswith("35% chance since 8 August.\n"), typed
    # ... and keeps that date once ledgered, while the value has not moved
    # since its first ledger row; once it has moved, the run's own date
    ledgered = _c(display="45%", movement="none", since="2026-10-06T10:00:00Z")
    reg = {"home.p_anc_largest": {"on_site": "2026-08-08"}}
    import build_site as B
    tip = B.tooltip_text(ledgered, by_token={ledgered["token"]: ledgered}, registry=reg,
                         edition="2026-10-21", publishing=True, facts=FACTS,
                         first_ledgered={"home.p_anc_largest": "2026-10-06T10:00:00Z"})
    assert tip.startswith("45% chance since 8 August.\n"), tip
    tip = B.tooltip_text(ledgered, by_token={ledgered["token"]: ledgered}, registry=reg,
                         edition="2026-10-21", publishing=True, facts=FACTS,
                         first_ledgered={"home.p_anc_largest": "2026-09-01T00:00:00Z"})
    assert tip.startswith("45% chance since 6 October.\n"), tip
    # a date in another year keeps its year
    assert _tip(_c(previous_since="2025-12-01T00:00:00Z")).split("\n")[0].endswith(
        "Was 45% on 1 December 2025.")
    # one seat is a seat
    assert _tip(_c("seats.ANC.median", "1", "none", "1", since="2026-09-30")).startswith(
        "1 seat since 30 September.")


def test_line_one_frozen_figures():
    live = _c("anc_entitlement", "59", "none", "59", since="2026-10-21T00:00:00Z")
    frozen = _c("pub0831_anc_entitlement", "65", "none", "65", since="2026-08-08")
    reg = {"pub0831_anc_entitlement": {"tracks": "anc_entitlement", "captured": "2026-08-08"}}
    by = {c["token"]: c for c in (live, frozen)}
    assert _tip(frozen, registry=reg, by_token=by).startswith(
        "65 seats on 8 August. 59 seats since 21 October.\n")
    assert _tip({**frozen, "display": "59"}, registry=reg, by_token=by).startswith(
        "59 seats on 8 August.\n")
    moved_live = {**live, "movement": "material", "previous": "61"}
    assert _tip(frozen, registry=reg, by_token={**by, "anc_entitlement": moved_live},
                publishing=False).startswith("65 seats on 8 August. 59 seats in this build.\n")
    hist = _c("claim_short_by", "39", "none", "39", since="2026-08-07")
    assert _tip(hist, registry={"claim_short_by": {"historical": "x", "captured": "2026-08-07"}}
                ).startswith("39 seats on 7 August.\n")


# --- end to end: the build ------------------------------------------------------

_BUILT: dict = {}


def _build(probe: bool) -> tuple[subprocess.CompletedProcess, dict]:
    """`build_site.main` into a temporary directory, on a copy of the forecast
    sheet that carries the probe token or not, against an empty ledger."""
    if probe in _BUILT:
        return _BUILT[probe]
    tmp = Path(tempfile.mkdtemp())
    src = (ROOT / "forecast-sheet.html").read_text(encoding="utf-8")
    extra = '<p>{{@probe.nopattern=1;int;probe}} probe.</p>' if probe else ""
    assert src.count("</body>") == 1
    (tmp / "sheet.html").write_text(src.replace("</body>", extra + "</body>"), encoding="utf-8")
    (tmp / "led" / "joburg").mkdir(parents=True)
    driver = (
        "import sys; sys.path.insert(0, 'src'); import build_site as B; "
        f"B.ARTEFACTS['forecast.html'] = ({json.dumps(str(tmp / 'sheet.html'))},"
        " *B.ARTEFACTS['forecast.html'][1:]); "
        f"raise SystemExit(B.main(['--out', {json.dumps(str(tmp / 'site'))}, "
        f"'--ledger-root', {json.dumps(str(tmp / 'led'))}, "
        "'--allow-orphans', '--allow-stale-sources']))")
    r = subprocess.run([str(ROOT / ".venv/bin/python"), "-c", driver],
                       capture_output=True, text=True, cwd=ROOT)
    pages = {}
    if r.returncode == 0:
        pages = {str(f.relative_to(tmp / "site")): f.read_text(encoding="utf-8")
                 for f in (tmp / "site").rglob("*.html")}
        pages["changes.json"] = (tmp / "site" / "changes.json").read_text(encoding="utf-8")
    _BUILT[probe] = (r, pages)
    return _BUILT[probe]


def _needs_run():
    if not (ROOT / "data" / "processed" / "forecast_summary.json").exists():
        skip("needs data/processed/forecast_summary.json; run montecarlo.py")


def test_the_build_refuses_a_token_with_no_sentence_and_builds_without_it():
    _needs_run()
    r, _ = _build(probe=True)
    assert r.returncode != 0, r.stdout[-1500:]
    assert "TOOLTIPS" in r.stdout + r.stderr and "probe.nopattern (0)" in r.stdout + r.stderr, (
        r.stdout[-1500:] + r.stderr[-1500:])
    r, _ = _build(probe=False)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]


def test_every_published_token_has_one_sentence_and_every_sentence_a_token():
    """Reads the tree, through a build. Population: the build's changes.json,
    shown equal to the figures on its pages in both directions."""
    _needs_run()
    r, pages = _build(probe=False)
    assert r.returncode == 0, r.stdout[-1500:] + r.stderr[-1500:]
    published = {c["token"] for c in json.loads(pages.pop("changes.json"))["changes"]}
    on_pages = {t for text in pages.values() for t in re.findall(r'class="mstat"[^>]*data-token="([^"]+)"', text)}
    assert published == on_pages, (sorted(published - on_pages)[:10], sorted(on_pages - published)[:10])
    # it looked: more tokens than patterns (each pattern names one or more),
    # and fewer than ten per pattern on average (a pattern that swallowed
    # whole families by accident would push this up)
    assert len(T.SAYS) <= len(published) <= 10 * len(T.SAYS), (len(published), len(T.SAYS))
    assert T.unsaid(published) == [], T.unsaid(published)
    assert T.unused(published) == [], T.unused(published)


def test_every_built_tooltip_is_two_lines_and_names_no_part_of_the_model():
    _needs_run()
    r, pages = _build(probe=False)
    assert r.returncode == 0, r.stdout[-1500:]
    pages = {k: v for k, v in pages.items() if k.endswith(".html")}
    tips = {(m.group(1), html.unescape(m.group(2)))
            for text in pages.values()
            for m in re.finditer(r'class="mstat"[^>]*data-token="([^"]+)"[^>]*data-prov="([^"]*)"', text)}
    assert len(tips) >= len(T.SAYS), len(tips)
    bad = [(t, tip, technical_words(tip)) for t, tip in sorted(tips) if technical_words(tip)]
    assert not bad, bad[:5]
    # the empty ledger: every figure is new, and this is not a publication,
    # unless the registry dates it from its first appearance on the site
    first = {tip.split("\n")[0] for _, tip in tips}
    assert all(" in this build." in line or " on " in line or " since " in line
               for line in first), sorted(first)[:5]


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
