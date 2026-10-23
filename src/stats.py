"""The stat registry: no model result is ever typed into prose by hand.

Phase 1 typed them, and four went stale on the live site — the standfirst
claimed the DA finished first 54% of the time when the model said 62%.
This module makes every reused figure a ``{{token}}`` resolved at build
time, and every token carries its provenance.

Two modes, and the distinction is the whole point:

* **free** — recomputed from the current model outputs every build. Use for
  statements of what the model says *now* ("the DA is largest in X% of
  simulations"). **Free is not a freshness guarantee.** A free token is only
  as current as the FILE its source names: a ``regime:`` source resolves out
  of ``regime_<rule>_summary.json``, and if that file is weeks old the token
  republishes a dead model's number every build while reading as live, with
  the drift report correctly saying nothing because a frozen file cannot
  drift. :func:`freshness_problems` is what closes that, and it is fatal.
* **fixed** — pinned to the run that produced it, because it sits inside a
  dated argument. "Short by 39 seats" is only true while the DA's median is
  97; silently refreshing that number would turn a correct article into
  nonsense. The build instead reports **drift** — pinned value, live value,
  and which article depends on it — so a human re-pins or rewrites.

Drift warns; it never blocks. An *unresolved* token, by contrast, is a hard
build error: a silent blank in published prose is unacceptable.

Registry format (``content/<city>/stats.toml``)::

    [p_da_largest]
    mode = "free"
    source = "model:structural.P(DA is the largest single party)"
    format = "pct0"
    inserted = "2026-08-07"

    [claim_da_median]
    mode = "fixed"
    value = 97
    source = "run:turnout_tilt_da=1 parties.DA.median"
    captured = "2026-08-07"
    run = "seed=20261104 draws=1500"
    tolerance = 2
    used_in = "claims/zille-490k — the 'short by 39 seats' argument"

Source grammar:

* ``model:<dotted path>`` — into ``forecast_summary.json``; the final
  segment may contain spaces and brackets (``structural.P(ANC+DA is
  winning)``).
* ``regime:<rule>:<dotted path>`` — into ``regime_<rule>_summary.json``,
  the counterfactual runs (``cap`` is the pure-proportional entitlement).
* ``derived:<name>`` — a named computation over ``seat_draws.csv`` (see
  ``_derived``).
* ``history:<city>:<year>:<dotted path>`` — into the record of that city-year
  in ``history.json`` (``compare_history``'s backtest of past elections):
  ``history:joburg:2011:wards.called``. See :func:`history_value`.
* ``published:small_party_surge`` — :func:`small_party_surge` over the
  published draws (``site/draws/``, the files the site's pages read).
* ``published:list_share_median:<PARTY>`` — that party's middle share of the
  list ballot over the published draws (:func:`published_list_share_median`).
* ``published:run_date`` — when the run that exported the published draws was
  made (``export_draws.run_time``); the date the pages and our forecast's card
  both print.
* ``judgement:<city>-<target>:<dotted path>`` — into that city-year's
  judgements file (``judgements/<city>-<target>.toml``), the values the owner
  set by hand and the run applied (``judgement:joburg-2026:party.MK.parent_weight``).
  A judgement call is written once, there; a page quoting it reads it from
  there (:func:`judgement_value`).
* ``run:<description>`` / ``external:<description>`` — never auto-resolved;
  legal only for ``fixed`` entries (a scenario run, or a fact from outside
  the model such as an IEC record).
"""

from __future__ import annotations

import csv
import json
import re
from html.parser import HTMLParser
import tomllib
from datetime import datetime
from pathlib import Path

UNVERIFIABLE = "unverifiable"  # see `drift_report`
DECLARATION_MIN_CHARS = 12   # a declaration shorter than this is not a reason
HISTORICAL = "historical"   # see `orphaned_scenario_claims`

TOKEN = re.compile(r"\{\{([a-z0-9_]+)\}\}")
#: A GENERATED token: a figure a render script computed at build time, written
#: inline as `{{@name=value;fmt;source}}`. It carries its own value, so it needs
#: no registry entry — but it renders as the same provenance span, is recorded
#: for the publication ledger (so it gets arrows), and is invisible to the
#: number scanner exactly as a registry token is. It replaces figures that page
#: script used to write into the DOM at view time, which had no provenance, no
#: history and could not be scanned (owner, 2026-09-17).
GEN_TOKEN = re.compile(r"\{\{@([A-Za-z0-9_.+\-]+)=([^;{}]*);([a-z0-9_]*);([^{}]*)\}\}")

# ⛔ A DATED CONTEXT IS DECLARED BY THE PROSE, NEVER INFERRED FROM IT.
#
# `publication.dated_context_violations` refuses to publish a SUPERSEDED figure
# in live present tense — "the model says the DA is short by 39 seats" — while
# permitting the same figure in a dated one — "as of 7 August the model said …".
# Only the sentence knows which it is. A regex hunting for a nearby date would
# be a guess, and a guess in a refusal path is worse than no refusal: it fails
# open on the prose it cannot parse and fails closed on prose that is fine.
#
# So the author declares it, per occurrence, by enclosing the sentence:
#
#     <span data-asof="2026-08-07">As of 7 August the model gave {{token}}.</span>
#
# Per OCCURRENCE and not per token, because dating is a property of the
# sentence: the same token can be live on the forecast page and historical in a
# retrospective, and a registry-level flag could not tell those apart.
_ASOF_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _RegionScanner(HTMLParser):
    """Character ranges of elements carrying a well-formed ``attr``.

    One parser for every attribute that marks out a region of a page:
    ``data-asof`` (a dated passage) and ``data-live`` (a LIVE region, below).
    An element's extent means the same thing for both.

    ⛔ **THIS WAS A REGEX AND THE REGEX FAILED OPEN.** It matched
    ``<tag …data-asof…>.*?</tag>`` non-greedily, which is not what an element
    is. Verified in review 2026-08-31:

    * an **unclosed** ``<section data-asof=…>`` whose ``</section>`` is supplied
      by a *different, undated* element later in the page dated **every token in
      between**, including tokens inside their own separate undated sections —
      one malformed tag silently discharged the dating obligation for the rest
      of the page;
    * the same tag with **no** closer anywhere dated nothing (fails closed);
    * a **nested** same-tag element truncated the region at the inner closer.

    `stats`' own argument for declared-over-sniffed dating is that a guess
    *"fails open on exactly the prose it cannot parse"*. A regex over HTML is
    that guess. This is a real parser with a depth counter, so an element's
    extent is its extent.

    **The value is validated, not merely present.** ``data-asof="banana"`` used
    to buy the exemption; the obligation is to say WHEN a figure was true, and a
    string that is not a date says nothing. ``valid`` is the pattern and
    ``wants`` what it is called in the refusal. ``skip`` names elements that
    carry the attribute with another meaning (a token span's ``data-live``).
    """

    def __init__(self, attr: str = "data-asof", valid: re.Pattern | None = None,
                 wants: str = "a YYYY-MM-DD date", skip=None) -> None:
        super().__init__(convert_charrefs=False)
        self.attr, self.valid, self.wants = attr, valid or _ASOF_DATE, wants
        self.skip = skip or (lambda attrs: False)
        self.spans: list[tuple[int, int, str]] = []
        self._dates: dict[int, str] = {}
        self._open: list[tuple[str, int, int | None]] = []   # tag, depth, start
        self._depth = 0
        self.malformed: list[str] = []

    def _offset(self) -> int:
        line, col = self.getpos()
        return self._line_start[line - 1] + col

    def feed_text(self, text: str) -> None:
        self._line_start = [0]
        for ln in text.split("\n"):
            self._line_start.append(self._line_start[-1] + len(ln) + 1)
        self._text = text
        self.feed(text)
        self.close()
        # An element opened and never closed cannot define a region. Recorded
        # so the caller can REFUSE rather than silently date nothing.
        for tag, _, start in self._open:
            if start is not None:
                self.malformed.append(
                    f"<{tag} {self.attr}=…> at offset {start} is never closed")

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        start = None
        if self.attr in d and not self.skip(d):
            value = (d.get(self.attr) or "").strip()
            if self.valid.match(value):
                start = self._offset()
                self._dates[start] = value
            else:
                self.malformed.append(
                    f'<{tag} {self.attr}="{value}"> is not {self.wants}')
        self._open.append((tag, self._depth, start))
        self._depth += 1

    def handle_startendtag(self, tag, attrs):
        d = dict(attrs)
        if self.attr in d and not self.skip(d):
            self.malformed.append(
                f"<{tag} {self.attr}=… /> is self-closing and encloses nothing")

    def handle_endtag(self, tag):
        for i in range(len(self._open) - 1, -1, -1):
            if self._open[i][0] == tag:
                _, depth, start = self._open.pop(i)
                self._depth = depth
                if start is not None:
                    self.spans.append((start, self._offset() + len(tag) + 3,
                                       self._dates.pop(start, "")))
                return
        # a closer with no opener: ignore, but it is why the regex failed open


def dated_spans(text: str) -> list[tuple[int, int, str]]:
    """``(start, end, date)`` per region of prose that dates a figure."""
    return _dated_scan(text)[0]


def _region_scan(text: str, parser: _RegionScanner
                 ) -> tuple[list[tuple[int, int, str]], list[str]]:
    try:
        parser.feed_text(text)
    except Exception:                                        # noqa: BLE001
        return [], [f"the page could not be parsed for {parser.attr} regions"]
    return parser.spans, parser.malformed


def _dated_scan(text: str) -> tuple[list[tuple[int, int, str]], list[str]]:
    """``(spans, malformed)`` — the second is why a build may refuse."""
    return _region_scan(text, _RegionScanner())


# --------------------------------------------------------------------------
# LIVE regions (owner's decision 1, 2026-09-30, audits/2026-09-30-interactive-s6)
# --------------------------------------------------------------------------
#
# A figure computed in the reader's browser from the reader's own settings has
# no build-time value, so it cannot be a token. It may appear ONLY inside an
# element marked
#
#     <output data-live="seats-da"></output>
#
# and such an element holds NO build-time digits: whatever the build writes
# there is blocking, whatever its status — a token, a registered fixed fact or
# a structural constant inside a LIVE region is still a number the build put
# where the page says the reader's browser computes. Only a module listed in
# `LIVE_WRITERS` may write into one (`script_writes`).
#
# A pinned token span used to carry `data-live="<current value>"` as well;
# it is `data-current` since 2026-09-30, so the overload is gone. Pages built
# before then still carry the old attribute, so an element with `data-token`
# is still never treated as a LIVE region.
#
# Deliberately NOT a `GENERATED_MARKERS` entry: a generated region is scanned
# and its figures listed as script-made; a LIVE region must be EMPTY of figures.
LIVE_ATTR = "data-live"
LIVE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

#: The only modules allowed to write figures into a page, and the LIVE regions
#: each may write into. Keyed by the module's path under the site root, as
#: served (``"your-forecast/js/model.js"``); the value is the set of
#: ``data-live`` names. A module not listed here may write no figure anywhere.
#: Regions on one page are disjoint between writers: each has one writer.
LIVE_WRITERS: dict[str, frozenset[str]] = {
    # "Your forecast" (src/build_your_forecast.py), section 1, "Adjust the
    # model" (interactive/js/model.js): the controls it builds and every figure
    # a reader's settings produce. Each results region is the LIVE twin of a
    # build twin of tokens (DESIGN §4, 2026-10-02): banner, result (the status
    # strip and the one-line result), map and its tooltip, flips, seats; then
    # the controls, the line under the by-elections, the seat law's summary,
    # the note's effective count, the floating "computing" overlay and the
    # phone's change toast.
    "your-forecast/js/model.js": frozenset({
        "engine", "busy", "banner", "result", "map", "wardtip", "flips", "seats",
        "turnout", "polls", "trust", "trustwhy", "cells", "byelection", "law", "lawnow", "ess",
        "toast",
    }),
    # Section 1's share sheet (interactive/js/play-share.js): its content (the
    # model's card, or the reader's hand-off sealed) for the one share sheet,
    # in the region "share".
    "your-forecast/js/play-share.js": frozenset({"share"}),
    # The one share sheet both sections use (interactive/js/share-sheet.js):
    # it holds no selector, and writes only to the elements play-share.js
    # and make-share.js took from their own regions and handed it.
    "your-forecast/js/share-sheet.js": frozenset({"share", "b-share"}),
    # Section 1's share image words (interactive/js/play-card.js): the figures
    # the seat table shows, from the same compute result, handed to the card
    # module (share-card.js). It builds figures and reaches NO region;
    # play-share.js puts the image in the sheet. Listed so the writer
    # contract, not the non-writer one, applies to it.
    "your-forecast/js/play-card.js": frozenset(),
    # Section 2, "Break the model" (interactive/js/make.js): the map, the vote,
    # the coalition and the council the reader's edits give, the walkthrough's
    # buttons, and the analysis of the reader's forecast with its ward tooltip.
    "your-forecast/js/make.js": frozenset({
        "b-status", "b-map", "b-vote", "b-govern", "b-council", "b-actions",
        "b-analysis", "b-wardtip",
    }),
    # Section 2's share sheet (interactive/js/make-share.js), in "b-share".
    "your-forecast/js/make-share.js": frozenset({"b-share"}),
    # The view a shared link opens (interactive/js/arrival.js): the friend's
    # forecast, its outcome and chance, and the ways on, in "arrival".
    "your-forecast/js/arrival.js": frozenset({"arrival"}),
    # How many forecasts have been sealed so far (interactive/js/entries.js,
    # the site Worker's /entries/1/count), in "entries"; arrival.js prints the
    # same line, from the same module, in its own region.
    "your-forecast/js/entries.js": frozenset({"entries"}),
    # /leaderboard/ (src/build_leaderboard.py, interactive/js/leaderboard.js),
    # once published: the first places in "lb-top", and the reader's own
    # entry, found by their link, in "lb-mine". Every figure is read from
    # leaderboard.json (src/rank_entries.py); none is computed in the page.
    "leaderboard/js/leaderboard.js": frozenset({"lb-top", "lb-mine"}),
    # The share cards of both sections (interactive/js/share-card.js): an SVG
    # of the figures it is handed, for the share sheet and the site's Worker.
    # It reaches NO region.
    "your-forecast/js/share-card.js": frozenset(),
}


def _live_scan(text: str) -> tuple[list[tuple[int, int, str]], list[str]]:
    """``(spans, malformed)`` for LIVE regions: ``(start, end, name)``."""
    return _region_scan(text, _RegionScanner(
        LIVE_ATTR, LIVE_NAME, f"a region name matching {LIVE_NAME.pattern}",
        skip=lambda attrs: "data-token" in attrs))


# The run every other artefact in data/processed is dated against. A file-backed
# source older than this one describes an earlier model.
REFERENCE_ARTEFACT = "forecast_summary.json"

# How far a backing file may lag the reference before it counts as stale.
# ARGUED, NOT MEASURED (JUDGEMENT-CALLS). It exists because of pipeline order,
# not tolerance for staleness: `overhang_regimes.py` writes each
# regime_<rule>_summary.json and only THEN re-runs the default rule to restore
# forecast_summary.json, so on a correct run the regime copies are legitimately
# older than the reference by one Monte Carlo. `overhang_regimes.py` now
# re-stamps them afterwards, which is what makes a window this small safe; the
# window absorbs filesystem timestamp granularity and a hand-run `cp`, and
# nothing longer. The defect this check was written for was 16 DAYS.
FRESHNESS_GRACE_S = 300.0

# What to re-run when a file-backed source has gone stale, by source prefix.
FRESHNESS_REMEDY = {
    "regime": "python src/overhang_regimes.py    # ~4 Monte Carlo runs",
}


# --------------------------------------------------------------------------
# formatting
# --------------------------------------------------------------------------

def _fmt(value, spec: str | None):
    if spec is None or spec == "raw":
        return str(value)
    if spec == "int":
        return f"{round(float(value)):d}"
    if spec == "comma":
        return f"{round(float(value)):,d}"
    if spec == "pct0":
        return f"{float(value) * 100:.0f}%"
    if spec == "pct1":
        return f"{float(value) * 100:.1f}%"
    if spec == "pct2":                # an official result to the hundredth: 18.12%
        return f"{float(value) * 100:.2f}%"
    if spec == "pct0_plain":          # 62 (no % sign, for "X of every")
        return f"{float(value) * 100:.0f}"
    if spec == "chance":              # a share of simulations, never "100%" or "0%"
        import reweight as _rw        # one definition, which /play/ prints too
        return _rw.chance_text(value)
    if spec == "pct0_capped":         # a share that rounds to 100% but is not all of it
        v = float(value)
        return "over 99%" if v > 0.99 and v < 1.0 else f"{v * 100:.0f}%"
    if spec == "one_dp":
        return f"{float(value):.1f}"
    if spec == "date_long":           # 2026-09-16T21:46:15Z -> 16 September 2026
        from datetime import datetime
        d = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return f"{d.day} {d:%B %Y}"
    raise ValueError(f"unknown format {spec!r}")


# --------------------------------------------------------------------------
# resolution
# --------------------------------------------------------------------------

def _dig(obj, path: str):
    """Walk a dotted path, tolerating final keys that contain dots/spaces."""
    cur = obj
    parts = path.split(".")
    for i, part in enumerate(parts):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
            continue
        # the remainder may be a single key containing dots
        rest = ".".join(parts[i:])
        if isinstance(cur, dict) and rest in cur:
            return cur[rest]
        return None
    return cur


#: The ``source`` of every token whose value IS the council, not a forecast:
#: its size and its majority (`_derived`). No edition moves them, so they may
#: stand in a dated passage (`publication.misdated_figures`). Matched by the
#: token's source, never by the number it shows: a forecast that happens to
#: print 136 is still a forecast.
COUNCIL_CONSTANT_SOURCES = ("derived:council_size", "derived:majority")


def council_constant_tokens(registry: dict) -> set[str]:
    """The registry's tokens whose source is a council constant."""
    return {name for name, e in registry.items()
            if isinstance(e, dict)
            and str(e.get("source", "")).strip() in COUNCIL_CONSTANT_SOURCES}


def _derived(name: str, ctx: dict):
    """Named computations over the draw-level outputs."""
    draws = ctx.get("draws") or []
    summary = ctx.get("summary") or {}
    if name == "small_party_share":          # the record test's two thresholds
        return SMALL_PARTY_SHARE             # (MODEL-LOG §1.296), printed from
    if name == "small_party_surge_share":    # the constants the measure uses
        return SMALL_PARTY_SURGE
    if name == "n_draws":
        return len(draws) or summary.get("scenario", {}).get("draws")
    if name == "council_size":
        return int(draws[0]["council_size"]) if draws else None
    if name == "majority":
        return int(draws[0]["threshold"]) if draws else None
    if name == "p_alone":
        if not draws:
            return None
        parties = [k for k in draws[0] if k not in ("draw", "threshold", "council_size")]
        hit = sum(1 for r in draws
                  if max(int(r[p]) for p in parties) >= int(r["threshold"]))
        return hit / len(draws)
    if name.startswith("largest_outright.") or name == "largest_tied":
        # ONE DEFINITION, reweight.largest_party (side finding S1, 2026-10-02):
        # `structural.P(X is the largest single party)` in forecast_summary.json
        # is an argmax over the model's party order, which credits every tied
        # simulation to the first party in it. Ties are their own outcome.
        if not draws:
            return None
        import numpy as _np
        import reweight as _rw
        parties = [k for k in draws[0] if k not in ("draw", "threshold", "council_size")]
        seats = _np.array([[int(float(r[p] or 0)) for p in parties] for r in draws])
        got = _rw.largest_party(seats, parties)
        if name == "largest_tied":
            return got["tied"]
        return got["outright"].get(name[len("largest_outright."):])
    return None


def judgement_value(source: str):
    """A ``judgement:<city>-<target>:<dotted path>`` source: the value in that
    city-year's judgements file (under ``pools.JUDGEMENTS_DIR``, the directory
    the run reads them from), or None where the file or the path is absent.
    Added 2026-10-23 so the forecast page can state ActionSA's judged level
    from the one place it is set, not as a typed copy."""
    import pools
    _, name, path = source.split(":", 2)
    f = pools.JUDGEMENTS_DIR / f"{name}.toml"
    if not f.is_file():
        return None
    return _dig(tomllib.loads(f.read_text(encoding="utf-8")), path)


def coalition_majority(members: list[str], ctx: dict):
    """The share of simulations in which ``members`` together reach that
    simulation's threshold, over EVERY party's seats
    (``scenarios.all_party_seats``, the one definition of the whole council:
    ``seat_draws.csv`` keeps only the largest parties, so a coalition with a
    small partner summed over its columns would drop that partner's seats).
    Its caller, until 2026-10-13, was the forecast share image's coalitions.
    None without draws or a processed directory. Refuses an empty or repeated
    member list, and a party the run's seat file does not name. That file
    holds rows only for parties with seats, so a party that wins no seat in
    any simulation is refused with a misspelt code: it cannot be told apart,
    and a coalition naming it is worth a look either way."""
    draws = ctx.get("draws") or []
    processed = ctx.get("processed")
    if not draws or processed is None:
        return None
    if not members or len(set(members)) != len(members) or not all(members):
        raise SystemExit(f"coalition {'+'.join(members)!r}: name each party once")
    cache = ctx.setdefault("_all_party_seats", {})
    if "seats" not in cache:
        import scenarios as _sc
        cache["seats"], cache["thr"], _council = _sc.all_party_seats(processed, rows=draws)
    seats, thr = cache["seats"], cache["thr"]
    unknown = [m for m in members if m not in seats]
    if unknown:
        raise SystemExit(f"coalition {'+'.join(members)!r}: {unknown} not in the run's "
                         "seat_detail_draws.csv")
    total = sum(seats[m] for m in members)
    return float((total >= thr).mean())


def resolve(source: str, ctx: dict):
    """Live value for a source string, or None when not auto-resolvable."""
    if source.startswith("model:"):
        return _dig(ctx.get("summary") or {}, source[len("model:"):])
    if source.startswith("regime:"):
        _, rule, path = source.split(":", 2)
        return _dig((ctx.get("regimes") or {}).get(rule) or {}, path)
    if source.startswith("validation:"):
        return validation_value(source[len("validation:"):], ctx)
    if source.startswith("derived:"):
        return _derived(source[len("derived:"):], ctx)
    if source.startswith("history:"):
        return history_value(source, ctx)
    if source.startswith("judgement:"):
        return judgement_value(source)
    if source == "published:run_date":
        import build_make as _bm
        from export_draws import run_time
        return run_time(_bm._draws(ctx.get("draws_dir"))[0])
    if source == "published:small_party_surge":
        return published_small_party_surge(ctx)
    if source.startswith("published:list_share_median:"):
        return published_list_share_median(source.rsplit(":", 1)[1], ctx)
    return None                      # run: / external: — pinned only


#: The record's own test of a small party's range (MODEL-LOG §1.296): a party
#: under 1% of the list vote at one local election, and whether it reached 5%
#: at the next. In the eight metros' consecutive local elections from 2006 to
#: 2021 none did. :func:`small_party_surge` asks the same of the simulations.
SMALL_PARTY_SHARE = 0.01
SMALL_PARTY_SURGE = 0.05


def small_party_surge(shares, columns, established) -> float:
    """The share of draws in which at least one ESTABLISHED small party (in
    ``established``: it stood at the preceding local election) whose mean list
    share over the draws is under :data:`SMALL_PARTY_SHARE` takes more than
    :data:`SMALL_PARTY_SURGE` of the list vote. ``shares`` is
    ``reweight.list_shares``' ``(draws, len(columns))``. Refuses when no
    column is an established small party: a share of nothing measured."""
    import numpy as _np
    s = _np.asarray(shares, dtype=float)
    est = set(established)
    small = [j for j, c in enumerate(columns) if c in est and s[:, j].mean() < SMALL_PARTY_SHARE]
    if not small:
        raise SystemExit("small_party_surge: no established party is under the small-party share")
    return float((s[:, small] > SMALL_PARTY_SURGE).any(axis=1).mean())


def published_small_party_surge(ctx: dict):
    """:func:`small_party_surge` over the published draws' list vote
    (``build_make``'s reader of ``site/draws/``), the established parties
    being those with a list vote at the preceding local election
    (``build_make.baseline``). Cached in ``ctx``; ``ctx["draws_dir"]`` points
    a test at constructed draws, and ``ctx["established"]`` at its parties."""
    if "_small_party_surge" not in ctx:
        import build_make as _bm
        import cityconfig as _cc
        import reweight as _rw
        manifest, arrays, _raw = _bm._draws(ctx.get("draws_dir"))
        cols = _bm._columns(manifest, "list_vote")
        est = ctx.get("established")
        if est is None:
            est = _bm.baseline(_cc.active(), cols)["list_vote"]
        ctx["_small_party_surge"] = small_party_surge(_rw.list_shares(arrays["list_vote"]), cols, est)
    return ctx["_small_party_surge"]


def published_list_share_median(party: str, ctx: dict):
    """``party``'s median share of the list ballot over the published draws
    (``site/draws``' ``list_vote`` block, as shares by ``reweight.list_shares``),
    or None when the party has no column. Added 2026-10-23 for the
    methodology's ANC list share, which was typed ("the mid-twenties")."""
    if "_list_shares" not in ctx:
        import build_make as _bm
        import reweight as _rw
        manifest, arrays, _raw = _bm._draws(ctx.get("draws_dir"))
        ctx["_list_shares"] = (_rw.list_shares(arrays["list_vote"]),
                               _bm._columns(manifest, "list_vote"))
    shares, cols = ctx["_list_shares"]
    if party not in cols:
        return None
    import numpy as _np
    return float(_np.median(shares[:, cols.index(party)]))


def wrong_party_seats(summed_abs_error) -> int:
    """Seats given to the wrong party: half the summed absolute seat error,
    which counts every misplaced seat twice, once where it went and once where
    it should have gone (owner, 2026-10-10: "if 43 seats are the wrong party
    then the error is 43. Why double it."), in WHOLE seats (owner, 2026-10-10:
    half seats are not shown). Where a forecast's middles do not sum to the
    council the half ends in .5, and it is rounded up: a misplaced half seat
    counts as a seat. THE ONE DEFINITION, and the rounding is applied per
    metro, so a total (``validation:total.*``, a sum) equals the sum of the
    metro figures printed beside it."""
    import math
    return int(math.floor(float(summed_abs_error) / 2 + 0.5))


def validation_value(path: str, ctx: dict):
    """A ``validation:`` source over ``validation_<year>.json``:

    * ``<headline field>``: the artefact's ``headline`` block, as written;
    * ``cities.<slug>.model.<field>`` / ``cities.<slug>.best.<field>``: that
      city's model, or its best baseline by CRPS (the artefact's
      ``_best_baseline_per_city``), field ``crps``, ``seat_mae``,
      ``wrong_party_seats`` (:func:`wrong_party_seats`) or, for ``best``,
      ``name`` (``build_validation.BASELINES``' words);
    * ``total.model.<field>`` / ``total.best.<field>``: the sum over the
      cities of the same field, so a total is the sum of the table's own
      figures; ``total.wins`` (cities where the model's CRPS is below its best
      baseline's) and ``total.crps_better`` (one minus the ratio of the CRPS
      totals).

    None where the artefact, the city or the field is absent."""
    v = ctx.get("validation") or {}
    head = v.get("headline") or {}
    if not path.startswith(("cities.", "total.")):
        return _dig(head, path)
    cities = v.get("cities") or {}
    best = head.get("_best_baseline_per_city") or {}

    def one(slug, side, field):
        c = cities.get(slug)
        if c is None:
            return None
        if side == "model":
            block = c.get("model") or {}
        elif side == "best":
            name = best.get(slug)
            if name is None:
                return None
            if field == "name":
                import build_validation as _bv
                return _bv.BASELINES[name]
            block = (c.get("baselines") or {}).get(name) or {}
        else:
            raise SystemExit(f"validation:{path}: the side is model or best, not {side!r}")
        if field == "wrong_party_seats":
            return None if block.get("seat_mae") is None else wrong_party_seats(block["seat_mae"])
        return block.get(field)

    parts = path.split(".")
    if parts[0] == "cities":
        if len(parts) != 4:
            raise SystemExit(f"validation:{path}: write cities.<slug>.<model|best>.<field>")
        return one(*parts[1:])
    if path == "total.wins":
        return sum(1 for slug in cities
                   if one(slug, "model", "crps") is not None
                   and one(slug, "model", "crps") < one(slug, "best", "crps"))
    if path == "total.crps_better":
        m, b = validation_value("total.model.crps", ctx), validation_value("total.best.crps", ctx)
        return None if not b else 1 - m / b
    if len(parts) != 3 or parts[2] == "name":
        raise SystemExit(f"validation:{path}: write total.<model|best>.<field>, total.wins "
                         "or total.crps_better")
    vals = [one(slug, parts[1], parts[2]) for slug in cities]
    if not vals or any(x is None for x in vals):
        return None
    return sum(vals)


def history_value(source: str, ctx: dict):
    """``history:<city>:<year>:<dotted path>``: the value at that path in the
    one ``history.json`` record for that city slug and election year, or None
    when the file, the record or the path is absent. Two records for one
    city-year is refused: which one a page quoted would be an accident. So is
    a record scored on specs other than the current ones
    (:func:`history_key_fault`): history.json is a separate run, and nothing
    else notices when it falls behind a re-emit."""
    parts = source.split(":", 3)
    if len(parts) != 4 or not all(parts[1:]):
        raise SystemExit(f"{source!r}: a history source is history:<city>:<year>:<path>")
    _, slug, year, path = parts
    hist = ctx.get("history") or {}
    rows = [r for r in hist.get("records", [])
            if r.get("slug") == slug and str(r.get("year")) == year]
    if len(rows) > 1:
        raise SystemExit(f"history.json holds {len(rows)} records for {slug} {year}")
    if not rows:
        return None
    fault = history_key_fault(hist, slug, year, ctx.get("spec_root"))
    if fault:
        raise SystemExit(f"{source}: {fault}. Re-run src/compare_history.py on the current "
                         "specs before quoting it.")
    return _dig(rows[0], path)


def history_key_fault(hist: dict, slug: str, year: str, root: Path | None = None) -> str | None:
    """Why history.json's record for ``slug`` ``year`` was not scored on the
    current spec, or None: the artefact key its manifest records for
    ``pools_<year>.json`` must equal the one the spec on disk declares
    (``pools.artefact_key``). ``root`` is the repository (a test passes a
    constructed one)."""
    import cityconfig as _cc
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    name = f"pools_{year}.json"
    scored = ((hist.get("manifest") or {}).get("pool_artefact_keys") or {}).get(slug, {}).get(name)
    if scored is None:
        return f"history.json records no artefact key for {slug} {name}"
    spec = root / _cc.load(slug).processed / name
    if not spec.is_file():
        return f"no current spec {spec.relative_to(root)} to compare history.json with"
    current = json.loads(spec.read_text(encoding="utf-8")).get("artefact_key")
    if current != scored:
        return f"history.json scored {slug} {year} on a different spec than {spec.relative_to(root)}"
    return None


def load_context(processed: Path) -> dict:
    """Model outputs the resolver reads, and the files they came out of.

    ``ctx["files"]`` maps a source prefix (``"regime:cap"``) to the path that
    backs it, and ``ctx["reference"]`` is ``forecast_summary.json``. Neither is
    used to resolve anything; they exist so :func:`freshness_problems` can ask
    how old the file under a *live* token actually is. See its docstring for
    why that question was not being asked.
    """
    ctx: dict = {"summary": {}, "draws": [], "regimes": {},
                 "files": {}, "reference": None, "processed": processed}
    summary = processed / REFERENCE_ARTEFACT
    if summary.exists():
        ctx["summary"] = json.loads(summary.read_text(encoding="utf-8"))
        ctx["reference"] = summary
    seat_draws = processed / "seat_draws.csv"
    if seat_draws.exists():
        with seat_draws.open(encoding="utf-8", newline="") as fh:
            ctx["draws"] = list(csv.DictReader(fh))
    # The backtest scoreboard, for `validation:` tokens. `build_validation`
    # writes its own comparison figures into the artefact, so the methodology
    # quotes them rather than keeping a second copy.
    for path in sorted(processed.glob("validation_*.json")):
        ctx["validation"] = json.loads(path.read_text(encoding="utf-8"))
        ctx["files"]["validation"] = path
    # The backtest of past elections, for `history:` tokens. Not entered in
    # ctx["files"]: `freshness_problems` dates a file against the forecast
    # run, and history.json is a different run (compare_history over the
    # past elections), so "older than the forecast" says nothing about it.
    hist = processed / "history.json"
    if hist.exists():
        ctx["history"] = json.loads(hist.read_text(encoding="utf-8"))
    for path in processed.glob("regime_*_summary.json"):
        rule = path.stem[len("regime_"):-len("_summary")]
        ctx["regimes"][rule] = json.loads(path.read_text(encoding="utf-8"))
        ctx["files"][f"regime:{rule}"] = path
    return ctx


def load_registry(path: Path) -> dict:
    with path.open("rb") as fh:
        registry = tomllib.load(fh)
    orphaned_scenario_claims(registry)
    return registry


def orphaned_scenario_claims(registry: dict) -> list[tuple[str, str]]:
    """Claims pinned to a scenario key the model no longer has. Warns loudly.

    A ``fixed`` token records a number captured from a named run, e.g.
    ``source = "run:turnout_tilt_da=1 parties.DA.median"``. The drift report
    cannot check one: re-deriving it means re-running that scenario, so a fixed
    token is trusted by construction. That is fine while the scenario exists and
    a silent lie the moment it does not — the number stays on the page, the
    audit keeps reporting no drift, and nothing anywhere says the mechanism it
    describes has been deleted.

    It had happened. TEN claims on the published forecast page were pinned to
    ``turnout_tilt_da``, a differential-turnout lever removed from
    ``montecarlo.run_model`` because it was applied after the citywide
    calibration and was never measured. The page still carried its numbers —
    "the DA reaches 97 seats if its turnout surges" and nine others — describing
    a lever the model had not had for weeks.

    This cannot detect a scenario key whose MEANING changed, only one that is
    gone. That is the cheap half; the expensive half is still a person's job.
    """
    try:
        import montecarlo as _mc
        known = set(_mc.DEFAULTS)
    except Exception:
        return []
    orphans: list[tuple[str, str]] = []
    for name, entry in (registry.get("stat") or registry).items():
        if not isinstance(entry, dict):
            continue
        # ⛔ A DECLARED HISTORICAL CLAIM IS NOT AN ORPHAN — BUT THE DECLARATION
        # COSTS SOMETHING, WHICH IS THE ONLY REASON IT IS NOT AN ESCAPE HATCH.
        #
        # The owner's ruling (2026-08-30): a published figure need not be
        # re-derivable, it must be ATTRIBUTABLE — and a figure whose mechanism
        # the model no longer has may be published as HISTORY and not as the
        # present tense. Ten claims fact-checking a party's turnout arithmetic
        # were run on 7 August under `turnout_tilt_da`, a lever `run_model` no
        # longer has. They cannot be re-derived by anything. Deleting them
        # destroys sound analysis; leaving them undeclared publishes a live
        # number nothing can check.
        #
        # So `historical` declares them — and `build_site` REFUSES any token
        # carrying it that renders outside a `data-asof` context. Declaring one
        # therefore obliges the prose to say when it was true. That coupling is
        # what makes this a discipline rather than `--allow-orphans` by another
        # name; see `stats.DATED_REGION`.
        if len(str(entry.get(HISTORICAL, "")).strip()) >= DECLARATION_MIN_CHARS:
            continue
        source = str(entry.get("source", ""))
        if not source.startswith("run:"):
            continue
        spec = source[4:].split()[0]
        if "=" not in spec:
            continue
        key = spec.split("=")[0]
        if key and key not in known:
            orphans.append((name, key))
    if orphans:
        keys = sorted({k for _, k in orphans})
        print(f"  !! {len(orphans)} pinned claim(s) describe a scenario this "
              f"model no longer has: {', '.join(keys)}")
        for name, key in orphans:
            print(f"     {name}  (source key {key!r})")
        print("     These cannot drift because they cannot be re-derived. "
              "Re-capture them under a mechanism that exists, or cut the claim.")
    return orphans


# --------------------------------------------------------------------------
# freshness: a token is only as live as the file underneath it
# --------------------------------------------------------------------------

def _stamp(epoch: float) -> str:
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


def _scenario_of(blob) -> dict:
    block = (blob or {}).get("scenario")
    return block if isinstance(block, dict) else {}


def _extinct_keys(scenario: dict, reference: dict) -> list[str]:
    """Scalar scenario keys this artefact records that nothing current knows.

    "Current" is deliberately two things: ``montecarlo.DEFAULTS`` (the lever
    set the model has) and the reference run's own scenario block (facts a run
    records that were never levers — ``arrival_group`` is one, and comparing
    against ``DEFAULTS`` alone flags the reference itself).

    Nested blocks are ignored. A regime summary carries ``theta_mode`` and
    ``individual_theta``; the reference carries ``pools``. Their *presence*
    says nothing, and a key-by-key comparison inside them would be a schema
    diff, which is a different job.

    This is the STRONG half of the freshness check, and the half that would
    still work if every mtime on the disk were destroyed: an artefact whose
    scenario names ``turnout_tilt_da`` was produced by a model that had
    ``turnout_tilt_da``, and this one has not had it for weeks.
    """
    try:
        import montecarlo as _mc
        known = set(_mc.DEFAULTS)
    except Exception:
        return []
    known |= set(reference)
    return sorted(k for k, v in scenario.items()
                  if not k.startswith("_") and not isinstance(v, dict)
                  and k not in known)


def freshness_problems(registry: dict, ctx: dict) -> list[dict]:
    """File-backed sources that are older than the run the site is built from.

    **``mode = "free"`` is not a freshness guarantee, and that is the whole
    point of this function.** A free token is recomputed every build, so it
    reads — to a reader, to a reviewer, and to the drift report — as the
    current model speaking. It is only ever as current as the FILE its source
    names. ``regime:cap:parties.ANC.median`` resolves out of
    ``regime_cap_summary.json``; if that file was written weeks ago by a
    version of the model that still had ``turnout_tilt_da``, the token
    faithfully republishes a dead model's number every single build, and the
    drift audit correctly reports no drift, because a frozen file cannot
    drift. That is exactly the state ``anc_entitlement`` was found in: the
    regime summaries were dated 2026-08-07 and appeared twice on the live
    front page.

    Two signals, and they are not equal:

    * **the artefact's scenario block** (:func:`_extinct_keys`) — strong. It
      identifies the model that produced the file from what the file says
      about itself.
    * **modification time** — weak, and only a fallback. mtime is a property
      of the filesystem, not of the model: `cp -p`, a restore from backup, a
      checkout or a `touch` all move it or fail to, and it says nothing about
      *which* code ran. It is used because there is nothing better on disk —
      ``forecast_summary.json`` carries ``_pools_artefact_key`` and
      ``_constants_read`` but no run time, no target year and no code hash.
      **What would be better:** a ``_generated`` stamp written by
      ``montecarlo`` alongside the artefact key, so every derived file could
      be dated against the run rather than against the disk.

    Returns one dict per stale FILE (not per token), naming every token that
    reads it, both dates, and what to re-run.
    """
    reference = ctx.get("reference")
    ref_scenario = _scenario_of(ctx.get("summary"))
    ref_mtime = reference.stat().st_mtime if reference else None

    users: dict[str, list[str]] = {}
    for name, entry in (registry.get("stat") or registry).items():
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source", ""))
        prefix = ":".join(source.split(":")[:2])
        if prefix in (ctx.get("files") or {}):
            users.setdefault(prefix, []).append(name)

    problems: list[dict] = []
    for prefix in sorted(users):
        path = ctx["files"][prefix]
        mtime = path.stat().st_mtime
        try:
            blob = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            blob = {}          # unreadable is `resolve`'s problem, not this one
        extinct = _extinct_keys(_scenario_of(blob), ref_scenario)
        behind = (ref_mtime is not None
                  and ref_mtime - mtime > FRESHNESS_GRACE_S)
        if not extinct and not behind:
            continue
        problems.append({
            "source": prefix,
            "path": str(path),
            "file_date": _stamp(mtime),
            "reference": str(reference) if reference else "(absent)",
            "reference_date": _stamp(ref_mtime) if ref_mtime else "(absent)",
            "tokens": sorted(users[prefix]),
            "extinct": extinct,
            "behind": behind,
            "remedy": FRESHNESS_REMEDY.get(prefix.split(":", 1)[0],
                                           "re-run whatever writes this file"),
        })
    return problems


def freshness_report(problems: list[dict]) -> str:
    if not problems:
        return "  every file-backed source is at least as new as the reference run"
    out = []
    for item in problems:
        out.append(f"  ✗ {item['path']}  ({item['file_date']})")
        out.append(f"      reference {item['reference']}  "
                   f"({item['reference_date']})")
        if item["extinct"]:
            out.append(f"      records levers this model no longer has: "
                       f"{', '.join(item['extinct'])}")
        if item["behind"]:
            out.append("      and it is older than the reference run")
        out.append(f"      read by: {', '.join(item['tokens'])}")
        out.append(f"      re-run:  {item['remedy']}")
    return "\n".join(out)


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

def _span(text: str, entry: dict, name: str, live_str: str | None) -> str:
    """Wrap a rendered stat so the build can attach its tooltip.

    ⛔ THE TOOLTIP IS NOT WRITTEN HERE. `data-prov` is left empty and
    ``build_site.tooltip_text`` writes the whole of it, two lines from the
    ledger and ``tooltip_says`` (owner, 2026-10-22: "use the identical
    structure everywhere"; audits/2026-10-22-tooltips/BRIEF.md). This wrote a
    technical source line ("Source: seat_draws.csv, … computed at build") that
    the build then prefixed with the history: two writers, and file names in
    front of readers. The build refuses a page that still carries an empty
    one."""
    mode = entry.get("mode", "free")
    when = entry.get("captured") or entry.get("inserted") or ""
    # `data-current`, not `data-live` (renamed 2026-09-30): `data-live` now
    # marks a LIVE region, and one attribute may not mean two things.
    live_attr = f' data-current="{live_str}"' if live_str is not None else ""
    # `data-prov`, not `title`: a browser shows a title tooltip late or not at
    # all, and the owner saw none (2026-09-17). src/css/stat.css draws it as a hover box.
    return (f'<span class="mstat" data-mode="{mode}" data-token="{name}"'
            f' data-when="{when}"{live_attr} data-prov="" tabindex="0">{text}</span>')


def render(text: str, registry: dict, ctx: dict, *, wrap: bool = True,
           record: list | None = None):
    """Substitute every ``{{token}}``.

    Returns ``(text, drift_rows, unresolved)``. ``unresolved`` being
    non-empty is a build error for the caller; ``drift_rows`` are advisory.

    ``record``, if given, is appended one mapping per token OCCURRENCE:
    ``token``, the raw ``value``, the ``display`` string the reader actually
    sees, ``fmt``, ``source``, ``mode`` and ``dated``. The publication ledger
    needs all of these and could not reconstruct any of them from the rendered
    HTML — ``value`` and ``display`` in particular must both be kept, because a
    raw move that leaves the glyph unchanged is exactly the case the ledger
    classifies as ``rounding`` and is undetectable from the string alone.

    Recording is opt-in and changes no output: with ``record=None`` this
    function is byte-identical to what it was.
    """
    drift: list[dict] = []
    unresolved: list[str] = []
    regions, malformed = (_dated_scan(text) if record is not None
                          else ([], []))

    def _one(match: re.Match) -> str:
        name = match.group(1)
        entry = registry.get(name)
        if entry is None:
            unresolved.append(name)
            return match.group(0)
        spec = entry.get("format")
        live = resolve(entry.get("source", ""), ctx)
        live_str = None if live is None else _fmt(live, spec)

        if entry.get("mode") == "fixed":
            if "value" not in entry:
                unresolved.append(f"{name} (fixed with no value)")
                return match.group(0)
            shown = (entry["value"] if isinstance(entry["value"], str)
                     else _fmt(entry["value"], spec))
            if live is not None:
                tol = entry.get("tolerance", 0)
                moved = (str(live) != str(entry["value"]) if tol == "exact"
                         else abs(float(live) - float(entry["value"])) > float(tol))
                if moved:
                    drift.append({"token": name, "pinned": shown,
                                  "live": live_str, "tolerance": tol,
                                  "used_in": entry.get("used_in", "")})
        else:
            if live is None:
                unresolved.append(f"{name} (free, source did not resolve: "
                                  f"{entry.get('source', '')})")
                return match.group(0)
            shown = _fmt(live, spec)

        if record is not None:
            at = match.start()
            record.append({
                "token": name,
                # the RAW value as published: the pinned value for a fixed
                # token (that is what the reader got), the live one otherwise.
                "value": (entry["value"] if entry.get("mode") == "fixed"
                          else live),
                "display": shown,
                "fmt": spec,
                "source": entry.get("source", ""),
                "mode": entry.get("mode", "free"),
                "tolerance": entry.get("tolerance"),
                "dated": any(lo <= at < hi for lo, hi, _ in regions),
                "asof": next((d for lo, hi, d in regions
                              if lo <= at < hi), ""),
                "captured": str(entry.get("captured", "")),
                "historical": str(entry.get(HISTORICAL, "")).strip(),
            })
        return _span(shown, entry, name, live_str) if wrap else shown

    def _gen(match: re.Match) -> str:
        name, raw, spec, src = (match.group(1), match.group(2),
                                match.group(3) or None, match.group(4))
        try:
            value = float(raw)
        except ValueError:
            value = raw
        shown = _fmt(value, spec)
        entry = {"mode": "generated", "source": src}
        if record is not None:
            at = match.start()
            record.append({
                "token": name, "value": value, "display": shown, "fmt": spec,
                "source": src, "mode": "generated", "tolerance": None,
                "dated": any(lo <= at < hi for lo, hi, _ in regions),
                "asof": next((d for lo, hi, d in regions if lo <= at < hi), ""),
                "captured": "", "historical": "",
            })
        return _span(shown, entry, name, None) if wrap else shown

    # Generated tokens first, then registry tokens — and the dated regions are
    # re-scanned in between. `_one` locates each occurrence by its offset in the
    # text it is substituting, and expanding a generated token into a span moves
    # every offset after it: scanning once, on the original text, put the dated
    # Zille figures outside their own `data-asof` spans (caught by the build,
    # 2026-09-17).
    text = GEN_TOKEN.sub(_gen, text)
    if record is not None:
        regions, malformed = _dated_scan(text)
    out_text = TOKEN.sub(_one, text)
    if record is not None and malformed:
        # Surfaced through the record so the caller can REFUSE. A
        # malformed dated region silently dates nothing (or, before
        # the parser, everything), and either way the reader is not
        # told when the figure was true.
        record.append({"token": "", "malformed_asof": malformed})
    return out_text, drift, unresolved


# --------------------------------------------------------------------------
# the audit: what got past the registry
# --------------------------------------------------------------------------
# A token carries its provenance to the reader. Anything typed straight into
# prose carries none, and cannot drift-check — which is exactly how four
# figures went stale on the live site and the standfirst came to claim the DA
# finished first 54% of the time when the model said 62%.
#
# Numbers are the obvious case. Sentences are the dangerous one: "the DA is the
# largest party" is a model result stated in words, it goes stale the same way,
# and nothing in the build has ever looked at it. If the model moves and the ANC
# leads, that sentence is simply false and no drift report fires.

SOURCED = re.compile(r'<span[^>]*data-token="[^"]*".*?</span>', re.S)
TAGS = re.compile(r"<[^>]+>")
SCRIPTS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S)

# ⛔ THERE IS NO LIST OF BARE NUMBERS THAT ARE "ALWAYS FINE". There was —
# 0-12, 50, 100, 135, 136, 270 and the election years — and it is how "Note the
# ANC's list bar: just 7 seats" reached the live page wrong: `7` was structural,
# so the audit never looked. A number is cleared by a TOKEN, or by a registered
# fixed fact that names its value AND its context (`[[audit.fixed]]` in the
# stats registry), never by being small. Owner, 2026-09-17.
_WORDS = ("zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
          "thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
          "thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
          "million|billion|half|third|quarter|twice|double")
_MONTHS = ("January|February|March|April|May|June|July|August|September|October|"
           "November|December")
_COUNTED = r"(?:seats?|wards?|votes?|voters?|councillors?|parties|per\s?cent|percent|%)"
NUMBERISH = re.compile(
    rf"(?P<date>\b\d{{1,2}}\s(?:{_MONTHS})\s\d{{4}}\b|\b\d{{4}}-\d{{2}}-\d{{2}}\b)"
    # a year is a year only when it is not counting something: "1998 votes" is a number
    rf"|(?P<year>\b(?:19|20)\d{{2}}\b(?!\s*{_COUNTED}))"
    # a number glued to letters is still a number: R1.2bn, x2, ward7
    rf"|(?P<num>(?<![\d.,#])[−-]?\d(?:[\d,]*\d)?(?:\.\d+)?(?:\s?%|pt)?)"
    # a number WORD that counts something is a number: "just seven seats"
    rf"|(?P<wnum>\b(?:{_WORDS})\b(?=\s+{_COUNTED}\b))"
    rf"|(?P<word>\b(?:{_WORDS})\b)", re.I)
#: Kinds that BLOCK a publish when unreviewed. Years and bare number words are
#: listed for review but do not block: a gate that fires on "one ballot" is a
#: gate someone learns to switch off.
GATING = ("num", "date", "wnum")
#: The only marker regions a SCRIPT writes. `CLAIMS` is not one: its prose is
#: typed into claims.toml by hand, so it is scanned as prose. A region name not
#: in this set is prose, whatever the comment says — otherwise any hand-written
#: page could exempt itself by typing a marker. `VALIDATION` is /methodology's
#: scoring section, written by src/build_validation.py and spliced in by
#: `build_site.validation_html`, which refuses a source without the generator's
#: own marker.
GENERATED_MARKERS = frozenset({"MAP", "HEXMAP", "BALLOTS", "REGIMES", "VALIDATION"})
REGION = re.compile(r"<!-- __([A-Z]+)_START__ -->(.*?)<!-- __\1_END__ -->", re.S)
#: Reader-visible attributes: tooltips, accessible labels, link previews.
ATTRS = re.compile(r'\b(?:title|data-tip|aria-label|alt|content)="([^"]*)"')
#: ``page = "*"`` on a registry entry: every page, said explicitly (the footer).
ALL_PAGES = "*"


def for_page(entries, page: str | None) -> list:
    """The `[[audit.fixed]]` / `[[audit.allow]]` entries that apply on ``page``.

    ⛔ THE `page` FIELD WAS IGNORED (owner's sweep, 2026-10-03). Every entry
    cleared its value in any page whose text happened to hold the context, so
    a fact registered for one page cleared the same words on every other, and
    a page that moved (the 8 August article left index.html on 2026-09-24)
    kept being cleared by entries that still named the old one.

    ``page`` is a comma-separated list of output paths, or ``"*"``. An entry
    with a page applies only when the caller names a page it lists: a caller
    that names no page gets no page-scoped entry (fails closed). An entry with
    NO page field applies everywhere; only constructed inputs have one, because
    `load_audit_config` refuses a registry entry without a page.
    """
    out = []
    for e in entries:
        where = e.get("page") if isinstance(e, dict) else None
        if where is None:
            out.append(e)
            continue
        listed = {w.strip() for w in str(where).split(",") if w.strip()}
        if ALL_PAGES in listed or (page is not None and page in listed):
            out.append(e)
    return out


#: Page furniture: a chart's scale ticks and the dated labels a piece carries.
#: Numbers here are not claims about the world — the axis of a chart and the
#: "8 August 2026: Published" line are structure, and their values come from
#: the chart's own scale or from the piece's publication date.
# A claim's attribution line — speaker, outlet, date of the article — is a
# citation, the same kind of thing as a piece's own dated label: it dates the
# quote, it does not assert anything about the city.
CHROME_CLASSES = ("ticks", "scale", "pubdate", "since-h", "colophon",
                   # and the quotation itself: the page tests that claim, it does
                   # not assert it. Our own figures about it are tokens below it.
                   "claim-who", "claim-quote")
#: A number in a heading is a step marker or a section number — "1. Start by
#: counting who can vote" — not a claim about the world.
_HEADING = re.compile(r"<h[1-4][^>]*>.*?</h[1-4]>", re.S)
_CHROME = re.compile(
    r"<(\w+)[^>]*class=\"[^\"]*\b(?:" + "|".join(CHROME_CLASSES) + r")\b[^\"]*\"[^>]*>.*?</\1>", re.S)
#: A footnote marker points at a note; it counts nothing (/play/'s notes,
#: 2026-10-02). Only this exact shape is chrome: a class named "fn" anywhere in
#: an attribute ("pl-fn", "fn-wrap", a <p class="fn">) would otherwise exempt
#: every figure inside it on every page (code review, 2026-10-02).
_FN_MARKER = re.compile(r'<sup class="fn"><a href="#note-[a-z-]+">\d{1,2}</a></sup>')


def scan_numbers(text: str, *, page: str | None = None, fixed=(),
                 generated_page: bool = False, structural=()) -> list[dict]:
    """Every number-shaped string a reader can see, classified.

    One dict per occurrence: ``kind`` (num/wnum/date/year/word), ``value``,
    ``context``, ``region`` (``prose``, ``generated:<MARKER>`` or
    ``generated-page``, with ``:attr`` appended for attribute text) and
    ``status``:

    Cleared automatically, each for a stated reason (owner, 2026-09-17, asked
    for a rule rather than a row-by-row review of the obvious):

    * ``dated``      — inside a ``data-asof`` passage: the prose already says
      when it was true, which is the whole obligation;
    * ``structural`` — a constant of this council (its size, its majority, its
      ward count), passed in from the model's own configuration, never typed
      here;
    * ``chrome``     — a chart's scale ticks or a piece's dated label.

    And by declaration:

    * ``fixed``      — a registered fixed fact whose ``context`` phrase CONTAINS
      this occurrence (not merely sits near it), whose ``value`` matches, and
      whose ``page`` lists ``page`` (`for_page`);
    * ``unreviewed`` — everything else.

    An `[[audit.allow]]` phrase clears no number (owner's sweep, 2026-10-03:
    "Laingsburg" cleared every "NN%" within sixty characters of the word on
    any page, which is how ActionSA's 18% and Laingsburg's 23% escaped being
    registered). It excuses a CLAIM in words (`audit`), nothing else.

    Token spans are removed first, so a token — including its provenance
    tooltip — never appears here. Script text is not scanned: a number a script
    writes at view time is invisible to this function, and says so here rather
    than being assumed covered (`script_writes` is the guard on scripts).

    **LIVE regions are cut out before anything else**, tokens included, and
    listed under ``live:<name>``: every digit in one is blocking whatever its
    status would otherwise be (`is_blocking`). A malformed LIVE marker is a hit
    of kind ``malformed`` and blocks too — an unparseable region cannot be
    shown to be empty.
    """
    body = SCRIPTS.sub(" ", text)
    structural = {str(s).strip() for s in structural}
    fixed = [(str(f.get("value", "")).strip().lower(),
              str(f.get("context", "")).strip().lower())
             for f in for_page(fixed, page)]
    out: list[dict] = []

    def classify(prose: str, region: str) -> None:
        low_all = prose.lower()
        for m in NUMBERISH.finditer(prose):
            value = m.group(0).strip()
            context = prose[max(0, m.start() - 70):m.end() + 40].strip()
            status = "unreviewed"
            if value.replace(",", "") in structural:
                status = "structural"
            for v, c in fixed:
                if not c or v != value.lower():
                    continue
                i = low_all.find(c)
                while i != -1:
                    if i <= m.start() and i + len(c) >= m.end():
                        status = "fixed"
                        break
                    i = low_all.find(c, i + 1)
                if status == "fixed":
                    break
            if region.startswith("live:"):
                # nothing clears a build-time figure inside a LIVE region
                status = "unreviewed"
            out.append({"kind": m.lastgroup, "value": value, "context": context,
                        "region": region, "status": status})

    def visit(fragment: str, region: str) -> None:
        # chrome first, and out of the fragment: its numbers are listed under
        # their own region and never block.
        for m in _HEADING.finditer(fragment):
            classify(re.sub(r"\s+", " ", html_unescape(TAGS.sub(" ", m.group(0)))),
                     region + ":heading")
        fragment = _HEADING.sub(" ", fragment)
        for m in _CHROME.finditer(fragment):
            classify(re.sub(r"\s+", " ", html_unescape(TAGS.sub(" ", m.group(0)))),
                     region + ":chrome")
        fragment = _CHROME.sub(" ", fragment)
        for m in _FN_MARKER.finditer(fragment):
            classify(re.sub(r"\s+", " ", html_unescape(TAGS.sub(" ", m.group(0)))),
                     region + ":chrome")
        fragment = _FN_MARKER.sub(" ", fragment)
        for attr in ATTRS.findall(fragment):
            classify(re.sub(r"\s+", " ", html_unescape(attr)), region + ":attr")
        classify(re.sub(r"\s+", " ", html_unescape(TAGS.sub(" ", fragment))), region)

    # LIVE regions first, with their token spans still in them: a token inside
    # a LIVE region is a build-time digit and must be seen.
    live, bad_live = _live_scan(body)
    for why in bad_live:
        out.append({"kind": "malformed", "value": LIVE_ATTR, "context": why,
                    "region": "live:malformed", "status": "unreviewed"})
    if live:
        keep, last = [], 0
        for lo, hi, name in sorted(live):
            if lo < last:
                continue
            keep.append(body[last:lo])
            visit(body[lo:hi], f"live:{name}")
            last = hi
        keep.append(body[last:])
        body = " ".join(keep)
    body = SOURCED.sub(" ", body)

    if generated_page:
        visit(body, "generated-page")
        return out

    def cut(m):
        if m.group(1) in GENERATED_MARKERS:
            visit(m.group(2), f"generated:{m.group(1)}")
            return " "
        return m.group(0)
    body = REGION.sub(cut, body)
    # Dated passages are pulled out whole, by the same parser the publication
    # gate uses, so a figure the prose has already dated is not asked to be a
    # live token as well.
    dated, _bad = _dated_scan(body)
    if dated:
        keep, last = [], 0
        for lo, hi, when in sorted(dated):
            if lo < last:
                continue
            keep.append(body[last:lo])
            visit(body[lo:hi], f"dated:{when}")
            last = hi
        keep.append(body[last:])
        body = " ".join(keep)
    visit(body, "prose")
    return out


def is_blocking(hit: dict) -> bool:
    """Does this `scan_numbers` hit stop a publish? The one definition, used by
    `audit` and by `build_site`'s number review.

    * outside LIVE regions: an unreviewed digit, date or counting word in prose
      (`GATING`) — headings, chrome and generated regions are listed, not gated;
    * inside a LIVE region (``live:*``, sub-regions included): ANY digit, and a
      malformed marker. The region must hold no build-time figure at all.
    """
    if hit["status"] != "unreviewed":
        return False
    if hit["region"].startswith("live:"):
        return hit["kind"] == "malformed" or any(c.isdigit() for c in hit["value"])
    return hit["region"] == "prose" and hit["kind"] in GATING


#: What a script needs in order to write a figure the build never saw: a data
#: block or a data source to hold it, and a way to put markup or interpolated
#: text into the page. A script not in `LIVE_WRITERS` may use none of them.
#: `textContent` stays legal — it cannot create markup, and with no data there
#: is nothing numeric for it to write (the map tooltip copies a `data-tip`
#: attribute, which is scanned).
#:
#: "a data source" was added with external modules (2026-09-30): a module that
#: `fetch`es JSON and writes it with `textContent` evades the other three.
SCRIPT_FORBIDDEN = (
    ("a data block", re.compile(r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=\s*[\[{]\s*[\"'\d\[{]")),
    ("HTML injection", re.compile(r"\.(?:innerHTML|outerHTML)\s*\+?=|insertAdjacentHTML|document\.write")),
    ("template interpolation", re.compile(r"`[^`]*\$\{")),
    ("a data source", re.compile(
        r"\bfetch\s*\(|\bXMLHttpRequest\b|\bnew\s+(?:Shared)?Worker\s*\(|\bonmessage\b"
        r"|addEventListener\(\s*[\"']message|\bWebSocket\b|\bEventSource\b"
        r"|\bimport\s*\(|\bimport\b[^;]*\.json[\"']")),
)

#: What a LIVE writer may NOT do, because each reaches outside the LIVE region
#: it selected or past this check: HTML injection (and `document.write`),
#: sibling insertion, traversal upwards or sideways, document-level handles,
#: lookups by id or class, writing through an event's target, and a dynamic
#: import this check cannot follow.
WRITER_FORBIDDEN = (
    ("HTML injection", re.compile(r"\.(?:innerHTML|outerHTML)\b|insertAdjacent\w*|document\.write")),
    ("insertion beside the region", re.compile(r"\.(?:before|after|replaceWith)\s*\(")),
    ("traversal out of the region", re.compile(
        r"\.(?:parentNode|parentElement|closest|previousSibling|nextSibling"
        r"|previousElementSibling|nextElementSibling|ownerDocument|getRootNode"
        r"|form|labels|offsetParent)\b")),
    ("a document-level handle", re.compile(
        r"\bdocument\.(?:body|documentElement|head|all|forms|links|images|children"
        r"|firstChild|lastChild|firstElementChild|lastElementChild|title)\b"
        r"|\bdocument\s*\[")),
    ("a lookup that is not a LIVE selector", re.compile(
        r"\b(?:getElementById|getElementsBy\w+|elementFromPoint|elementsFromPoint)\s*\(")),
    ("a write through an event target", re.compile(
        r"\b(?:target|currentTarget|srcElement)\b[\w$.\[\]'\"]*\.(?:textContent|innerText"
        r"|nodeValue|data|value)\s*\+?=(?!=)")),
    ("an import this check cannot follow", re.compile(r"\bimport\s*\(")),
)
_SELECTOR_CALL = re.compile(r"\bquerySelector(?:All)?\s*\(\s*")
#: The whole argument must be the literal: `'[data-live="x"]' + ', p'` would
#: select outside the region, so the call must close right after the quote.
#: The part after the region is a descendant selector with no combinator:
#: `'[data-live="x"] ~ main p'` selects a sibling of the region, so `~`, `+`
#: and `>` are refused there (code review of /play/ share, 2026-10-01).
_LIVE_SELECTOR = re.compile(
    r"""^(["'`])\[data-live=(["']?)([a-z][a-z0-9-]*)\2\](?:\s+[^,"'`$~+>]*)?\1\s*\)""")
_SCRIPT_TAG = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.S | re.I)
_SRC = re.compile(r"""\bsrc\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)
_STATIC_IMPORT = re.compile(
    r"""\bimport\s*["']([^"']+)["']"""
    r"""|\b(?:import|export)\b[^;'"`]*?\bfrom\s*["']([^"']+)["']""")


#: What a writer listed for NO region may not do either: it reaches no element,
#: so its figures can only come from the result it is handed. A data block or a
#: data source would let it draw figures the page never computed (code review
#: of /play/ share, 2026-10-01: listing play-card.js had lifted these two).
_NO_REGION_FORBIDDEN = tuple((w, p) for w, p in SCRIPT_FORBIDDEN
                             if w in ("a data block", "a data source"))


def _writer_problems(body: str, regions: frozenset[str]) -> list[str]:
    out = []
    for what, pat in (WRITER_FORBIDDEN if regions
                      else WRITER_FORBIDDEN + _NO_REGION_FORBIDDEN):
        for hit in pat.finditer(body):
            out.append(f"{what}: …{body[max(0, hit.start() - 40):hit.end() + 40].strip()}…")
    for call in _SELECTOR_CALL.finditer(body):
        sel = _LIVE_SELECTOR.match(body[call.end():])
        here = body[max(0, call.start() - 20):call.end() + 60].strip()
        if not sel:
            out.append(f"a lookup that is not a LIVE selector: …{here}…")
        elif sel.group(3) not in regions:
            out.append(f"a LIVE region it is not listed for ({sel.group(3)!r}; "
                       f"listed: {', '.join(sorted(regions)) or 'none'}): …{here}…")
    return out


def _module_imports(body: str) -> list[str]:
    return [m.group(1) or m.group(2) for m in _STATIC_IMPORT.finditer(body)]


def _resolve(spec: str, base: Path, root: Path) -> tuple[Path | None, str]:
    """A script reference as a file under ``root``, or ``(None, why)``."""
    if re.match(r"^(?:[a-z][a-z0-9+.-]*:|//)", spec, re.I):
        return None, f"a remote or inline script cannot be read: {spec}"
    clean = re.split(r"[?#]", spec, maxsplit=1)[0]
    if base.suffix in (".js", ".mjs") and not clean.startswith(("/", "./", "../")):
        return None, f"a bare module specifier cannot be resolved: {spec}"
    f = (root / clean.lstrip("/")) if clean.startswith("/") else (base.parent / clean)
    f = f.resolve()
    try:
        f.relative_to(root.resolve())
    except ValueError:
        return None, f"a script outside the site cannot ship with it: {spec}"
    if not f.is_file():
        return None, f"a script the page loads does not exist: {spec}"
    return f, ""


#: The ONE remote script a page may load: Cloudflare Web Analytics' beacon,
#: emitted by `build_site.analytics_head()` only when the owner has set a site
#: token. It reads the browser's performance timings and posts them to
#: Cloudflare; it writes nothing into the page, so it cannot put a figure in
#: front of a reader. Matched as the exact URL, no query string: any other
#: remote script, including this host with another path, is still refused.
ANALYTICS_BEACON = "https://static.cloudflareinsights.com/beacon.min.js"


def _forbidden(body: str, where: str = "") -> list[str]:
    return [f"{where}{what}: …{body[max(0, hit.start() - 40):hit.end() + 40].strip()}…"
            for what, pat in SCRIPT_FORBIDDEN for hit in pat.finditer(body)]


def script_writes(text: str, *, page: Path | None = None, root: Path | None = None,
                  writers: dict[str, frozenset[str]] | None = None) -> list[str]:
    """Ways a page's scripts could put a figure on the page at view time.

    Owner, 2026-09-17: script-written figures had no provenance, no ledger row
    and no arrow, and the number scanner could not see them. Every figure is
    rendered at build time; this is the guard that keeps it that way, with ONE
    exception (decision 1, 2026-09-30): a module in ``writers`` (default
    `LIVE_WRITERS`) may compute figures, and may put them only into the LIVE
    regions it is listed for, reached by a literal ``[data-live="<name>"]``
    selector.

    Scanned: every inline ``<script>``, every ``<script src>`` the page loads
    (resolved against ``page``, and against ``root`` when ``/``-rooted), and
    every module those import statically, transitively. A reference that cannot
    be read — remote, bare, outside ``root``, missing, or on a page given
    without ``page``/``root`` — is itself a problem: a script nobody read is one
    nobody can vouch for.

    **Limits.** This is a lexical check over JavaScript, not an analysis of it.
    It catches the ways a figure reaches a page by accident — a data block, a
    fetch, an ``innerHTML``, a lookup outside the region — and each breach of
    the writer contract has a visible spelling. A module written to evade a
    regex can. Workers are not followed: a Worker cannot touch the page, and
    the module that creates one is flagged unless it is a listed writer.
    """
    writers = LIVE_WRITERS if writers is None else writers
    out: list[str] = []
    queue: list[Path] = []
    for m in _SCRIPT_TAG.finditer(text):
        src = _SRC.search(m.group(1))
        if not src:
            out += _forbidden(m.group(2))
            continue
        spec = next(g for g in src.groups() if g is not None)
        if spec == ANALYTICS_BEACON and not m.group(2).strip():
            continue
        if page is None or root is None:
            out.append(f"a script the check was given no path to read: {spec}")
            continue
        f, why = _resolve(spec, page, root)
        if f is None:
            out.append(why)
        else:
            queue.append(f)
    seen: set[Path] = set()
    while queue:
        f = queue.pop(0)
        if f in seen:
            continue
        seen.add(f)
        rel = f.relative_to(root.resolve()).as_posix()
        body = f.read_text(encoding="utf-8")
        if rel in writers:
            out += [f"{rel} (LIVE writer): {w}"
                    for w in _writer_problems(body, frozenset(writers[rel]))]
        else:
            out += _forbidden(body, f"{rel}: ")
        for imp in _module_imports(body):
            g, why = _resolve(imp, f, root)
            if g is None:
                out.append(f"{rel}: {why}")
            else:
                queue.append(g)
    return out


def html_unescape(s: str) -> str:
    import html as _html
    return _html.unescape(s)


# Phrases that assert a model outcome. Each must be tokenised or whitelisted.
CLAIM_PATTERNS = (
    r"largest (?:single )?party",
    r"finish(?:es|ed)? first",
    r"wins? (?:the )?most",
    r"(?:no|without an?) (?:overall |outright )?majority",
    r"short of (?:an? )?majority",
    r"on course (?:to|for)",
    r"is (?:now )?(?:ahead|behind) of",
    r"(?:more|less) likely than not",
    r"(?:will|would) (?:win|lose|govern|hold)",
    r"nobody will win",
)


def _visible(text: str) -> str:
    """Reader-visible prose, with already-sourced spans removed."""
    body = SCRIPTS.sub(" ", text)
    body = SOURCED.sub(" ", body)
    return TAGS.sub(" ", body)


def audit(text: str, *, page: str | None = None, allow=(), fixed=(),
          structural=(), claim_patterns=CLAIM_PATTERNS
          ) -> tuple[list[str], list[str]]:
    """Model figures and model claims that reach the reader unsourced.

    ``allow`` excuses CLAIMS IN WORDS, never a number: each entry is a context
    phrase (a string, or an ``{"phrase", "page"}`` mapping scoped by
    `for_page`). Three kinds of sentence legitimately need it, and none can
    drift:

    * **historical fact** stated in words — "ActionSA went from nothing";
    * **the rules** — "a ward needs no majority, highest total wins";
    * **reviewed prose** a human has decided should stay static.

    A number is cleared only by a token or by a registered fixed fact
    (`scan_numbers`), which names its value, its context, its page and its
    source.

    Returns ``(numbers, claims)``.
    """
    # A claim inside a dated passage is history, and a claim whose own sentence
    # carries a token is sourced — the same two rules the number scan applies.
    # Without them the checker flagged "the DA is the largest party in 47% of
    # simulations" while pointing at the token that says so.
    dated_ranges, _ = _dated_scan(text)
    if dated_ranges:
        keep, last = [], 0
        for lo, hi, _when in sorted(dated_ranges):
            if lo < last:
                continue
            keep.append(text[last:lo])
            last = hi
        keep.append(text[last:])
        text = " ".join(keep)
    # The same prose, but with each token span marked rather than removed, so a
    # claim can be checked for a figure standing beside it.
    marked = re.sub(r"\s+", " ", TAGS.sub(" ", SOURCED.sub(" ⟦TOK⟧ ", SCRIPTS.sub(" ", text))))
    prose = re.sub(r"\s+", " ", _visible(text))
    allow_lower = [(a.get("phrase", "") if isinstance(a, dict) else a).lower()
                   for a in for_page(allow, page)]
    allow_lower = [a for a in allow_lower if a]

    def excused(context: str) -> bool:
        low = context.lower()
        return any(a in low for a in allow_lower)

    numbers = [f"{h['value']!r}  …{h['context']}…"
               for h in scan_numbers(text, page=page, fixed=fixed,
                                     structural=structural)
               if is_blocking(h)]
    lowered = prose.lower()
    claims: list[str] = []
    for pattern in claim_patterns:
        for match in re.finditer(pattern, lowered):
            context = prose[max(0, match.start() - 60):match.end() + 40].strip()
            if excused(context):
                continue
            # a token within the claim's own sentence is its source
            here = marked.lower().find(match.group(0))
            if here != -1 and "⟦tok⟧" in marked.lower()[max(0, here - 160):here + 200]:
                continue
            claims.append(f"{match.group(0)!r}  …{context}…")
    return numbers, claims


def load_audit_config(registry: dict) -> dict:
    """The ``[audit]`` block of the stats registry, if it has one.

    Refuses an `[[audit.fixed]]` or `[[audit.allow]]` entry that names no
    ``page``, or an allow entry that is a bare string: the page is what scopes
    the entry (`for_page`), and an entry without one would clear its words on
    every page, which is the defect the field exists to close.
    """
    block = registry.get("audit") or {}
    fixed = tuple(block.get("fixed", ()))
    allow = tuple(block.get("allow", ()))
    bad = [f"[[audit.fixed]] value={f.get('value')!r} context={f.get('context')!r}"
           for f in fixed if not str(f.get("page", "")).strip()]
    bad += [f"[[audit.allow]] {a!r}" for a in allow
            if not isinstance(a, dict) or not str(a.get("page", "")).strip()
            or not str(a.get("phrase", "")).strip()]
    if bad:
        raise ValueError(
            "audit entries with no page (name the output page(s) it clears, "
            "comma-separated, or \"*\" for every page):\n  " + "\n  ".join(bad))
    return {"allow": allow, "fixed": fixed,
            "claim_patterns": tuple(block.get("claim_patterns", CLAIM_PATTERNS))}


def audit_report(numbers: list[str], claims: list[str], *, limit: int = 8) -> str:
    if not numbers and not claims:
        return "  every model figure and claim on the page is sourced"
    out = []
    if numbers:
        out.append(f"  {len(numbers)} model figure(s) typed into prose, unsourced:")
        out += [f"      {n}" for n in numbers[:limit]]
        if len(numbers) > limit:
            out.append(f"      … and {len(numbers) - limit} more")
    if claims:
        out.append(f"  {len(claims)} model claim(s) stated in words, unsourced:")
        out += [f"      {c}" for c in claims[:limit]]
        if len(claims) > limit:
            out.append(f"      … and {len(claims) - limit} more")
    out.append("  Register each figure as a {{token}} or an [[audit.fixed]] "
               "fact with its page and source; a claim in words that cannot "
               "drift goes in [[audit.allow]] with its page.")
    return "\n".join(out)


def drift_report(rows: list[dict], registry: dict | None = None) -> str:
    """The drift lines, and — when the registry is given — what was NOT checked.

    ⛔ "no drift — every pinned stat is within tolerance" WAS A LIE BY
    OMISSION, and `tests/test_published_page.py` names it: *"the build's
    cheerful 'no drift' is not a finding but the absence of one."* A pinned
    token drifts only inside `if live is not None`, and a `run:` or `external:`
    source never resolves — so **all 24 pinned tokens on this site are
    undriftable**, and the build was reporting their silence as their health.

    Now that every one of them carries an `unverifiable` declaration, the count
    can be stated instead of implied. A reader of the build log should not have
    to know the internals to discover that "no drift" was computed over nothing.
    """
    unchecked = 0
    if registry:
        unchecked = sum(1 for e in (registry.get("stat") or registry).values()
                        if isinstance(e, dict) and e.get("mode") == "fixed"
                        and str(e.get(UNVERIFIABLE, "")).strip())
    # ⛔ STATE THE DECLARATION, NOT A CAUSE THIS FUNCTION NEVER CHECKS. The
    # first version said "their sources never resolve" while counting only the
    # DECLARATIONS — so pointing one token at a resolvable source would print a
    # drift row and "never resolve" in the same report. The previous defect was
    # a lie by omission; that would have been the same lie by assertion.
    tail = (f"\n  ({unchecked} pinned token(s) carry an `unverifiable` "
            f"declaration and are therefore unchecked rather than "
            f"checked-and-fine)" if unchecked else "")
    if not rows:
        return ("  no drift among the pinned stats that CAN be drift-checked"
                + tail)
    out = []
    for r in rows:
        out.append(f"  ⚠ {r['token']}: pinned {r['pinned']} → model now says "
                   f"{r['live']} (tolerance {r['tolerance']})")
        if r["used_in"]:
            out.append(f"      used in: {r['used_in']} — the argument may need rewriting")
    return "\n".join(out) + tail


