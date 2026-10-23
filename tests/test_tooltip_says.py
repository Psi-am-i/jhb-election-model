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
* **A figure that moved keeps its "Was"** in the edition that moved it and in
  every later one, through `_ledger_candidates` over a constructed ledger
  (owner, 2026-10-23; audits/2026-10-23-site-sweep/BRIEF-tooltip-was.md).
  A corrected FROZEN figure does too, its "Was" dated to the replaced value's
  first publication (BRIEF-tooltip-was-frozen.md).

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


def test_a_pattern_matching_nothing_is_reported_and_the_report_clears():
    every = ["seats.ANC.median"]
    assert r"seats\.OTHERS\.median" in T.unused(every)
    assert r"seats\.OTHERS\.median" not in T.unused(every + ["seats.OTHERS.median"])
    # and a constructed table: one pattern that matches nothing is named alone
    saved = T.SAYS, T._COMPILED
    try:
        T.SAYS = (T.Say(r"probe\.a", "", "x", "A."), T.Say(r"probe\.never", "", "x", "B."))
        T._COMPILED = [(x, __import__("re").compile(x.pattern)) for x in T.SAYS]
        assert T.unused(["probe.a"]) == [r"probe\.never"]
        assert T.unused(["probe.a", "probe.never"]) == []
    finally:
        T.SAYS, T._COMPILED = saved


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
    """A change whose prior value is its previous one when the two differ:
    the ledger holds one earlier run."""
    moved = previous is not None and previous != display
    return {"token": token, "display": display, "movement": movement,
            "previous": previous, "previous_since": previous_since,
            "previous_published_at": previous_since, "since": since,
            "prior": previous if moved else None,
            "prior_since": previous_since if moved else None}


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
    import build_site as B

    def tip(x, by_token, publishing=True):
        return B.tooltip_text(x, by_token=by_token, registry=reg, edition="2026-10-21",
                              publishing=publishing, facts=FACTS,
                              dated_on={"pub0831_anc_entitlement": "2026-08-08"})
    assert tip(frozen, by).startswith("65 seats on 8 August. 59 seats since 21 October.\n")
    assert tip({**frozen, "display": "59"}, by).startswith("59 seats on 8 August.\n")
    moved_live = {**live, "movement": "material", "previous": "61"}
    assert tip(frozen, {**by, "anc_entitlement": moved_live}, publishing=False).startswith(
        "65 seats on 8 August. 59 seats in this build.\n")
    # a pinned figure is not current: "on" its published date, never "since";
    # the dated passage's own date first, then on_site, then its first ledger row
    pinned = {**_c("claim_poll_base", "985,000", "none", "985,000", since="2026-08-08"),
              "mode": "fixed"}
    reg = {"claim_poll_base": {"mode": "fixed", "captured": "2026-08-07"}}
    import build_site as B
    tip = B.tooltip_text(pinned, by_token={}, registry=reg, edition="2026-10-21",
                         publishing=True, facts=FACTS, dated_on={"claim_poll_base": "2026-08-07"},
                         first_ledgered={"claim_poll_base": "2026-08-08T00:00:00Z"})
    assert tip.startswith("985,000 on 7 August.\n"), tip
    tip = B.tooltip_text(pinned, by_token={}, registry=reg, edition="2026-10-21",
                         publishing=True, facts=FACTS,
                         first_ledgered={"claim_poll_base": "2026-08-08T00:00:00Z"})
    assert tip.startswith("985,000 on 8 August.\n"), tip
    # a share whose "%" the prose carries gets it in line 1
    pct = {**_c("claim_490k_of_2021", "53", "none", "53"), "mode": "fixed"}
    assert _tip(pct, registry={"claim_490k_of_2021": {"mode": "fixed", "on_site": "2026-08-08"}}
                ).startswith("53% on 8 August.\n")
    # a date is the date alone
    day = {**_c("generated_date", "21 October 2026", "material", "29 September 2026"),
           "fmt": "date_long"}
    assert _tip(day).startswith("21 October 2026.\n"), _tip(day)
    hist = _c("claim_short_by", "39", "none", "39", since="2026-08-07")
    assert B.tooltip_text(hist, by_token={}, registry={"claim_short_by": {"historical": "x"}},
                          edition="2026-10-21", publishing=True, facts=FACTS,
                          dated_on={"claim_short_by": "2026-08-07"}
                          ).startswith("39 seats on 7 August.\n")


# --- "Was" outlives the edition that moved the figure ---------------------------

def _row(token, display, published_at, movement="none", value=None, superseded_at=None):
    import publication as P
    return P.Row(token=token, value=display if value is None else value, display=display,
                 fmt="pct0", source="s", model_run_id="r1", run_at=None, as_of=None,
                 published_at=published_at, change_class=None, reason=None,
                 movement=movement, superseded_at=superseded_at)


def _editions():
    """Line 1 of three tooltips in each of three editions built over one
    constructed ledger, each edition appended before the next is built:
    ``home.p_anc_largest`` moves 47 -> 58 in edition N (with a rounding row
    inside the 47 run) and is reprinted unchanged in N+1 and N+2;
    ``home.p_alone`` never moves; ``tile.p_da_largest`` moves 30 -> 40 in N,
    and its only 35 is a superseded row, which is not a value the reader was
    shown as current."""
    import build_site as B
    import publication as P
    ledger = [_row("home.p_anc_largest", "47%", "2026-09-26T00:00:00Z", "new", 0.471),
              _row("home.p_anc_largest", "47%", "2026-10-06T00:00:00Z", "rounding", 0.468),
              _row("home.p_alone", "12%", "2026-09-26T00:00:00Z", "new"),
              _row("home.p_alone", "12%", "2026-10-06T00:00:00Z"),
              _row("tile.p_da_largest", "30%", "2026-09-26T00:00:00Z", "new"),
              _row("tile.p_da_largest", "35%", "2026-10-06T00:00:00Z", "material",
                   superseded_at="2026-10-06T00:00:00Z")]
    shown = {"home.p_anc_largest": ("58%", 0.58), "home.p_alone": ("12%", 0.12),
             "tile.p_da_largest": ("40%", 0.40)}
    ident = {"model_run_id": "r-abc-1234", "run_at": None, "as_of": None}
    out = []
    for now in ("2026-10-21T16:46:09Z", "2026-10-22T11:38:25Z", "2026-10-23T03:02:10Z"):
        occ = [{"token": t, "value": v, "display": d, "fmt": "pct0", "source": "s",
                "mode": "free", "tolerance": None, "page": "x.html"}
               for t, (d, v) in shown.items()]
        rows, changes = B._ledger_candidates(occ, P.latest_of(ledger), ident, now,
                                             reason="r", change_class="mechanism",
                                             since=P.run_starts(ledger), history=ledger)
        by = {c["token"]: c for c in changes}
        out.append({t: B.tooltip_text(c, by_token=by, registry={}, edition=now[:10],
                                      publishing=True, facts=FACTS).split("\n")[0]
                    for t, c in by.items()})
        ledger = ledger + rows
    return out


def test_a_moved_figure_says_what_it_was_in_its_edition_and_every_later_one():
    n, n1, n2 = _editions()
    assert n["home.p_anc_largest"] == "58% chance since 21 October. Was 47% on 26 September.", n
    for later in (n1, n2):
        assert later["home.p_anc_largest"] == (
            "58% chance since 21 October. Was 47% on 26 September."), later


def test_a_figure_that_never_moved_has_no_was_clause():
    for edition in _editions():
        assert edition["home.p_alone"] == "12% chance since 26 September.", edition
        assert "Was" not in edition["home.p_alone"]


def test_a_superseded_row_is_not_a_prior_value():
    for edition in _editions():
        line = edition["tile.p_da_largest"]
        assert line.endswith(" Was 30% on 26 September."), edition
        assert "35" not in line, line


def test_prior_values_dates_the_run_as_run_starts_did_while_it_was_current():
    """The date "Was" names is the date `run_starts` returned while that value
    was current, including across a retirement, which starts a new run."""
    import publication as P
    rows = [_row("r", "9", "2026-08-08T00:00:00Z", "new"),
            _row("r", "9", "2026-09-01T00:00:00Z", superseded_at="2026-09-01T00:00:00Z"),
            _row("r", "9", "2026-09-26T00:00:00Z", "new")]
    while_current = P.run_starts(rows)["r"]
    rows.append(_row("r", "11", "2026-10-21T00:00:00Z", "material"))
    assert P.prior_values(rows) == {"r": ("9", while_current)}, P.prior_values(rows)
    assert while_current == "2026-09-26T00:00:00Z"
    # a value the build is about to show is the current one, not the ledger's
    assert P.prior_values(rows, {"r": "9"}) == {"r": ("11", "2026-10-21T00:00:00Z")}
    # a value that returns names the other one, not itself
    rows.append(_row("r", "9", "2026-10-22T00:00:00Z", "material"))
    assert P.prior_values(rows) == {"r": ("11", "2026-10-21T00:00:00Z")}


def _frozen_editions():
    """Line 1 of two FIXED tooltips in two editions built over one constructed
    ledger, the build's ``first_ledgered`` and ``dated_on`` passed as `main`
    computes them: ``rev0806_da_largest_fixed`` is first ledgered at 63% on 8
    August in a passage dated 6 August, corrected to 61% in edition N and
    republished unchanged in N+1; ``rev0806_da_minority_viable`` stays 63%."""
    import build_site as B
    import publication as P
    fixed, still = "rev0806_da_largest_fixed", "rev0806_da_minority_viable"
    ledger = [_row(fixed, "63%", "2026-08-08T00:00:00Z", "new"),
              _row(fixed, "63%", "2026-10-06T00:00:00Z"),
              _row(still, "63%", "2026-08-08T00:00:00Z", "new")]
    shown = {fixed: "61%", still: "63%"}
    dated_on = {fixed: "2026-08-06", still: "2026-08-06"}
    ident = {"model_run_id": "r-abc-1234", "run_at": None, "as_of": None}
    out = []
    for now in ("2026-10-23T03:02:10Z", "2026-10-24T09:00:00Z"):
        occ = [{"token": t, "value": d, "display": d, "fmt": "pct0", "source": "s",
                "mode": "fixed", "tolerance": "exact", "page": "review.html"}
               for t, d in shown.items()]
        rows, changes = B._ledger_candidates(occ, P.latest_of(ledger), ident, now,
                                             reason="r", change_class="correction",
                                             since=P.run_starts(ledger), history=ledger)
        first = {}
        for r in ledger:
            if r.token not in first or str(r.published_at) < first[r.token]:
                first[r.token] = str(r.published_at)
        by = {c["token"]: c for c in changes}
        out.append({t: B.tooltip_text(c, by_token=by, registry={}, edition=now[:10],
                                      publishing=True, facts=FACTS, first_ledgered=first,
                                      dated_on=dated_on).split("\n")[0]
                    for t, c in by.items()})
        ledger = ledger + rows
    return out


def test_a_corrected_frozen_figure_says_what_it_was_on_its_first_date():
    """Owner, 2026-10-23 (audits/2026-10-23-site-sweep/BRIEF-tooltip-was-frozen.md):
    on 6 August the review said 63%, so a tooltip reading "61% chance on 6
    August." puts the corrected value on the wrong date."""
    for edition in _frozen_editions():
        assert edition["rev0806_da_largest_fixed"] == (
            "61% chance since 23 October. Was 63% on 6 August."), edition


def test_a_frozen_figure_never_corrected_says_only_when_it_was_published():
    for edition in _frozen_editions():
        assert edition["rev0806_da_minority_viable"] == "63% chance on 6 August.", edition


def test_a_frozen_figure_corrected_twice_dates_the_middle_value_by_its_run():
    """When the replaced value is not the token's first run, its date is the
    run's own (``prior_since``), not the passage's: 6 August was the first
    value's date, not the second's."""
    import build_site as B
    c = {"token": "rev0806_da_largest_fixed", "display": "59%", "movement": "material",
         "previous": "61%", "previous_since": "2026-10-23T03:02:10Z",
         "previous_published_at": "2026-10-23T03:02:10Z", "since": None,
         "prior": "61%", "prior_since": "2026-10-23T03:02:10Z", "mode": "fixed"}
    line = B.tooltip_text(c, by_token={c["token"]: c}, registry={}, edition="2026-10-25",
                          publishing=True, facts=FACTS,
                          first_ledgered={c["token"]: "2026-08-08T00:00:00Z"},
                          dated_on={c["token"]: "2026-08-06"}).split("\n")[0]
    assert line == "59% chance since 25 October. Was 61% on 23 October.", line


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
    import tomllib
    reg = tomllib.loads((ROOT / "content/joburg/stats.toml").read_text(encoding="utf-8"))
    wrong = dry_line_one_faults(tips, reg)
    assert not wrong, wrong[:5]


def dry_line_one_faults(tips, reg) -> list:
    """Line 1s wrong for a dry build on an empty ledger: every live figure is
    "in this build" unless the registry dates it from the site (`on_site`);
    a pinned, tracking or historical figure is "on" a date; a date figure is
    the date alone. A build that dated itself as a publication ("since
    <today>") is caught."""
    import calendar
    wrong = []
    for t, tip in sorted(tips):
        line = tip.split("\n")[0]
        e = reg.get(t) if isinstance(reg.get(t), dict) else {}
        if re.fullmatch(r"\d{1,2} [A-Z][a-z]+ \d{4}\.", line):
            continue
        if e.get("mode") == "fixed" or e.get("tracks") or e.get("historical"):
            # dated by its passage or on_site, else undated on an empty ledger
            ok = (bool(re.search(r" on \d{1,2} [A-Z][a-z]+( \d{4})?\.", line))
                  and " since " not in line.split(" on ")[0]) or line.endswith(" in this build.")
        elif e.get("on_site"):
            d = e["on_site"]
            ok = line.endswith(f" since {int(d[8:10])} {calendar.month_name[int(d[5:7])]}.")
        else:
            ok = line.endswith(" in this build.")
        if not ok:
            wrong.append((t, line))
    return wrong


def test_the_dry_run_check_fires_on_a_build_dated_as_a_publication():
    reg = {"pinned": {"mode": "fixed"}, "typed": {"on_site": "2026-08-08"}}
    good = {("live", "58% chance in this build.\nSOURCE: This Model. X."),
            ("pinned", "44 seats on 8 August.\nSOURCE: IEC. X."),
            ("typed", "52,000 since 8 August.\nSOURCE: IEC. X.")}
    assert dry_line_one_faults(good, reg) == []
    for t, line in (("live", "58% chance since 21 October."),
                    ("pinned", "44 seats since 8 August."),
                    ("pinned", "44 seats since 21 October."),
                    ("typed", "52,000 in this build.")):
        bad = {x for x in good if x[0] != t} | {(t, line + "\nSOURCE: X. Y.")}
        assert [w[0] for w in dry_line_one_faults(bad, reg)] == [t], (t, line)
    assert dry_line_one_faults(good, reg) == []


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
