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
  ``DERIVED``).
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
#: served (``"play/js/live.js"``); the value is the set of ``data-live`` names.
#: A module not listed here may write no figure anywhere.
LIVE_WRITERS: dict[str, frozenset[str]] = {
    # "Play with the model" (src/build_play.py, from interactive/js/model.js):
    # the controls it builds and every figure a reader's settings produce. Each
    # results region is the LIVE twin of a build twin of tokens (DESIGN §4,
    # 2026-10-02): banner, result (the status strip and the one-line result),
    # map and its tooltip, flips, seats; then the controls, the line under the
    # by-elections, the seat law's summary and the note's effective count.
    "play/js/model.js": frozenset({
        "engine", "banner", "result", "map", "wardtip", "flips", "seats",
        "turnout", "polls", "trust", "cells", "byelection", "law", "lawnow", "ess",
    }),
    # Its share sheet (interactive/js/play-share.js): the link to the reader's
    # settings and the image of their figures, inside the one region "share".
    "play/js/play-share.js": frozenset({"share"}),
    # The share image's words (interactive/js/play-card.js): the figures the
    # seat table shows, from the same compute result, handed to the card
    # module. It builds figures and reaches NO region; play-share.js puts the
    # image in the sheet. Listed so the writer contract, not the non-writer
    # one, applies to it.
    "play/js/play-card.js": frozenset(),
    # The card module both pages share (interactive/js/forecast-card.js): an
    # SVG of the figures it is handed. It reaches NO region.
    "play/js/forecast-card.js": frozenset(),
    # "Make your own forecast" (src/build_make.py, from interactive/js/make.js):
    # the map, the vote, the coalition and the council the reader's edits give.
    "make/js/make.js": frozenset({"status", "map", "vote", "govern", "council"}),
    # Its share sheet (interactive/js/make-share.js), inside the region "share".
    "make/js/make-share.js": frozenset({"share"}),
    # The same card module as /play/'s (interactive/js/forecast-card.js),
    # served again under make/. It reaches NO region.
    "make/js/forecast-card.js": frozenset(),
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


def _derived(name: str, ctx: dict):
    """Named computations over the draw-level outputs."""
    draws = ctx.get("draws") or []
    summary = ctx.get("summary") or {}
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


def resolve(source: str, ctx: dict):
    """Live value for a source string, or None when not auto-resolvable."""
    if source.startswith("model:"):
        return _dig(ctx.get("summary") or {}, source[len("model:"):])
    if source.startswith("regime:"):
        _, rule, path = source.split(":", 2)
        return _dig((ctx.get("regimes") or {}).get(rule) or {}, path)
    if source.startswith("validation:"):
        return _dig((ctx.get("validation") or {}).get("headline") or {},
                    source[len("validation:"):])
    if source.startswith("derived:"):
        return _derived(source[len("derived:"):], ctx)
    return None                      # run: / external: — pinned only


def load_context(processed: Path) -> dict:
    """Model outputs the resolver reads, and the files they came out of.

    ``ctx["files"]`` maps a source prefix (``"regime:cap"``) to the path that
    backs it, and ``ctx["reference"]`` is ``forecast_summary.json``. Neither is
    used to resolve anything; they exist so :func:`freshness_problems` can ask
    how old the file under a *live* token actually is. See its docstring for
    why that question was not being asked.
    """
    ctx: dict = {"summary": {}, "draws": [], "regimes": {},
                 "files": {}, "reference": None}
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
    """Wrap a rendered stat so its provenance travels with it."""
    mode = entry.get("mode", "free")
    src = entry.get("source", "")
    when = entry.get("captured") or entry.get("inserted") or ""
    if mode == "fixed":
        tip = f"Source: {src}. Pinned {when}"
        if entry.get("run"):
            tip += f" ({entry['run']})"
        tip += "."
        if live_str is not None and live_str != text:
            tip += f" The current model gives {live_str}."
    elif mode == "generated":
        tip = f"Source: {src}, computed at build from the current model run."
    else:
        tip = f"Source: {src}, live from the current model run."
    # the tip goes into an attribute: escape before anything else can break out
    tip = (tip.replace("&", "&amp;").replace("<", "&lt;")
              .replace(">", "&gt;").replace('"', "&quot;"))
    # `data-current`, not `data-live` (renamed 2026-09-30): `data-live` now
    # marks a LIVE region, and one attribute may not mean two things.
    live_attr = f' data-current="{live_str}"' if live_str is not None else ""
    # `data-prov`, not `title`: a browser shows a title tooltip late or not at
    # all, and the owner saw none (2026-09-17). src/css/stat.css draws it as a hover box.
    return (f'<span class="mstat" data-mode="{mode}" data-token="{name}"'
            f' data-when="{when}"{live_attr} data-prov="{tip}" tabindex="0">{text}</span>')


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
#: page could exempt itself by typing a marker.
GENERATED_MARKERS = frozenset({"MAP", "HEXMAP", "BALLOTS", "REGIMES"})
REGION = re.compile(r"<!-- __([A-Z]+)_START__ -->(.*?)<!-- __\1_END__ -->", re.S)
#: Reader-visible attributes: tooltips, accessible labels, link previews.
ATTRS = re.compile(r'\b(?:title|data-tip|aria-label|alt|content)="([^"]*)"')
#: The legacy `[audit].allow` entries were written against the old audit, which
#: only ever saw "NN%" and "N seats". They excuse exactly that shape, in the old
#: 60/30 window — never a date, never a bare count they were not written for.
_LEGACY_SHAPE = re.compile(r"^\d{1,3}(?:[.,]\d+)?\s?%$|^\d+$")


#: Page furniture: a chart's scale ticks and the dated labels a piece carries.
#: Numbers here are not claims about the world — the axis of a chart and the
#: "31 August 2026: Published" line are structure, and their values come from
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


def scan_numbers(text: str, *, fixed=(), allow=(), generated_page: bool = False,
                 structural=(), ) -> list[dict]:
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
      this occurrence (not merely sits near it) and whose ``value`` matches,
      optionally scoped to one ``page``;
    * ``allowed``    — a legacy ``[audit].allow`` entry, for the shape it was
      written against only;
    * ``unreviewed`` — everything else.

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
              str(f.get("context", "")).strip().lower()) for f in fixed]
    allow_lower = [a.lower() for a in allow if a]
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
            if (status == "unreviewed" and m.lastgroup == "num"
                    and _LEGACY_SHAPE.match(value)):
                narrow = low_all[max(0, m.start() - 60):m.end() + 30]
                if any(a in narrow for a in allow_lower):
                    status = "allowed"
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


def audit(text: str, *, allow=(), fixed=(), structural=(),
          claim_patterns=CLAIM_PATTERNS) -> tuple[list[str], list[str]]:
    """Model figures and model claims that reach the reader unsourced.

    ``allow`` is a list of *context substrings*, not bare values. Whitelisting
    the number 23 would excuse every 23 on the site; whitelisting "Laingsburg"
    excuses the one figure that is a matter of record. Three things legitimately
    need it, and none of them can drift:

    * **historical fact** — "ActionSA went from nothing to 44 seats" is what
      happened in 2021, not what the model says will happen;
    * **the rules** — "a ward needs no majority, highest total wins" describes
      the electoral system;
    * **reviewed prose** a human has decided should stay static.

    Everything else should be a token, because a token carries its source to
    the reader and reports drift when the model moves under it.

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
    allow_lower = [a.lower() for a in allow if a]

    def excused(context: str) -> bool:
        low = context.lower()
        return any(a in low for a in allow_lower)

    numbers = [f"{h['value']!r}  …{h['context']}…"
               for h in scan_numbers(text, fixed=fixed, allow=allow,
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
    """The ``[audit]`` block of the stats registry, if it has one."""
    block = registry.get("audit") or {}
    return {"allow": tuple(block.get("allow", ())),
            "fixed": tuple(block.get("fixed", ())),
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
    out.append("  Register each as a {{token}}, or whitelist it in the "
               "[audit] block of the stats registry if it is structural.")
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


