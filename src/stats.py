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


class _AsOfScanner(HTMLParser):
    """Character ranges of elements carrying a well-formed ``data-asof``.

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

    **The date is validated, not merely present.** ``data-asof="banana"`` used
    to buy the exemption; the obligation is to say WHEN a figure was true, and a
    string that is not a date says nothing.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
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
                    f"<{tag} data-asof=…> at offset {start} is never closed")

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        start = None
        if "data-asof" in d:
            value = (d.get("data-asof") or "").strip()
            if _ASOF_DATE.match(value):
                start = self._offset()
                self._dates[start] = value
            else:
                self.malformed.append(
                    f'<{tag} data-asof="{value}"> is not a YYYY-MM-DD date')
        self._open.append((tag, self._depth, start))
        self._depth += 1

    def handle_startendtag(self, tag, attrs):
        if "data-asof" in dict(attrs):
            self.malformed.append(
                f"<{tag} data-asof=… /> is self-closing and encloses nothing")

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


def _dated_scan(text: str) -> tuple[list[tuple[int, int, str]], list[str]]:
    """``(spans, malformed)`` — the second is why a build may refuse."""
    p = _AsOfScanner()
    try:
        p.feed_text(text)
    except Exception:                                        # noqa: BLE001
        return [], ["the page could not be parsed for data-asof regions"]
    return p.spans, p.malformed


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
        v = float(value)
        if v > 0.99:
            return "over 99%"
        if v < 0.0005:
            return "under 0.1%"
        return f"{v * 100:.0f}%" if v >= 0.095 else f"{v * 100:.1f}%"
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
    return None


def resolve(source: str, ctx: dict):
    """Live value for a source string, or None when not auto-resolvable."""
    if source.startswith("model:"):
        return _dig(ctx.get("summary") or {}, source[len("model:"):])
    if source.startswith("regime:"):
        _, rule, path = source.split(":", 2)
        return _dig((ctx.get("regimes") or {}).get(rule) or {}, path)
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
    live_attr = f' data-live="{live_str}"' if live_str is not None else ""
    # `data-prov`, not `title`: a browser shows a title tooltip late or not at
    # all, and the owner saw none (2026-09-17). STAT_CSS draws it as a hover box.
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
    rf"(?P<date>\b\d{{1,2}}\s(?:{_MONTHS})\s\d{{4}}\b)"
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


def scan_numbers(text: str, *, fixed=(), allow=(), generated_page: bool = False,
                 ) -> list[dict]:
    """Every number-shaped string a reader can see, classified.

    One dict per occurrence: ``kind`` (num/wnum/date/year/word), ``value``,
    ``context``, ``region`` (``prose``, ``generated:<MARKER>`` or
    ``generated-page``, with ``:attr`` appended for attribute text) and
    ``status``:

    * ``fixed``      — a registered fixed fact whose ``context`` phrase CONTAINS
      this occurrence (not merely sits near it) and whose ``value`` matches,
      optionally scoped to one ``page``;
    * ``allowed``    — a legacy ``[audit].allow`` entry, for the shape it was
      written against only;
    * ``unreviewed`` — everything else.

    Token spans are removed first, so a token — including its provenance
    tooltip — never appears here. Script text is not scanned: a number a script
    writes at view time is invisible to this function, and says so here rather
    than being assumed covered.
    """
    body = SCRIPTS.sub(" ", text)
    body = SOURCED.sub(" ", body)
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
            out.append({"kind": m.lastgroup, "value": value, "context": context,
                        "region": region, "status": status})

    def visit(fragment: str, region: str) -> None:
        for attr in ATTRS.findall(fragment):
            classify(re.sub(r"\s+", " ", html_unescape(attr)), region + ":attr")
        classify(re.sub(r"\s+", " ", html_unescape(TAGS.sub(" ", fragment))), region)

    if generated_page:
        visit(body, "generated-page")
        return out

    def cut(m):
        if m.group(1) in GENERATED_MARKERS:
            visit(m.group(2), f"generated:{m.group(1)}")
            return " "
        return m.group(0)
    visit(REGION.sub(cut, body), "prose")
    return out


#: What a script needs in order to write a figure the build never saw: a data
#: block to hold it, and a way to put markup or interpolated text into the page.
#: A published page's scripts may use none of them. `textContent` stays legal —
#: it cannot create markup, and with no data block there is nothing numeric for
#: it to write (the map tooltip copies a `data-tip` attribute, which is scanned).
SCRIPT_FORBIDDEN = (
    ("a data block", re.compile(r"\b(?:const|let|var)\s+[A-Za-z_$][\w$]*\s*=\s*[\[{]\s*[\"'\d\[{]")),
    ("HTML injection", re.compile(r"\.(?:innerHTML|outerHTML)\s*\+?=|insertAdjacentHTML|document\.write")),
    ("template interpolation", re.compile(r"`[^`]*\$\{")),
)


def script_writes(text: str) -> list[str]:
    """Ways a page's scripts could put a figure on the page at view time.

    Owner, 2026-09-17: script-written figures had no provenance, no ledger row
    and no arrow, and the number scanner could not see them. Every figure is now
    rendered at build time; this is the guard that keeps it that way.
    """
    out = []
    for m in re.finditer(r"<script[^>]*>(.*?)</script>", text, re.S):
        body = m.group(1)
        for what, pat in SCRIPT_FORBIDDEN:
            for hit in pat.finditer(body):
                out.append(f"{what}: …{body[max(0, hit.start() - 40):hit.end() + 40].strip()}…")
    return out


def inject_stat_css(page: str) -> str:
    """Put STAT_CSS into a page, once. The only place the token styling comes
    from: a template that kept its own copy is how a hover box written here
    never reached the page (2026-09-17)."""
    if "/*stat-css*/" in page or "</head>" not in page:
        return page
    # A pop-over near the right or bottom edge of the window flips so it stays
    # visible. The script only toggles a class; it writes no text or figure.
    flip = ("<script>/*stat-tip*/document.addEventListener('mouseover',function(e){"
            "var s=e.target.closest&&e.target.closest('.mstat');if(!s)return;"
            "var r=s.getBoundingClientRect();"
            "var w=document.documentElement.clientWidth,h=document.documentElement.clientHeight;"
            "s.classList.toggle('tip-left',r.left+316>w);"
            "s.classList.toggle('tip-up',r.bottom+96>h);});</script>")
    return page.replace("</head>", f"<style>/*stat-css*/\n{STAT_CSS}</style>\n{flip}\n</head>", 1)


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


def audit(text: str, *, allow=(), fixed=(), claim_patterns=CLAIM_PATTERNS,
          ) -> tuple[list[str], list[str]]:
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
    prose = re.sub(r"\s+", " ", _visible(text))
    allow_lower = [a.lower() for a in allow if a]

    def excused(context: str) -> bool:
        low = context.lower()
        return any(a in low for a in allow_lower)

    numbers = [f"{h['value']!r}  …{h['context']}…"
               for h in scan_numbers(text, fixed=fixed, allow=allow)
               if h["region"] == "prose" and h["kind"] in GATING
               and h["status"] == "unreviewed"]
    lowered = prose.lower()
    claims: list[str] = []
    for pattern in claim_patterns:
        for match in re.finditer(pattern, lowered):
            context = prose[max(0, match.start() - 60):match.end() + 40].strip()
            if excused(context):
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


# The CSS/markup a page needs so pinned figures reveal their provenance.
# Injected into every page that renders tokens. `mstat` (model stat), NOT
# `stat` — that class is already the headline tiles, whose flex-column
# display turned every inline figure into its own block.
STAT_CSS = """  .mstat{display:inline;position:relative;border-bottom:1px dotted var(--ink-3);cursor:help;}
  .mstat[data-mode="fixed"]{border-bottom-style:dashed;}
  @media (min-width:760px){.tablewrap{overflow:visible;}}  /* phones keep sideways scroll */
  .mstat:hover::after,.mstat:focus::after,.mstat-move:hover::after{content:attr(data-prov);position:absolute;
    left:0;top:1.5em;z-index:50;width:max-content;max-width:300px;white-space:normal;
    background:var(--ink,#1a1d1b);color:var(--paper,#fbfbfa);font:500 11.5px/1.35 ui-sans-serif,system-ui;
    padding:6px 8px;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,.25);pointer-events:none;}
  .mstat.tip-left:hover::after,.mstat.tip-left:focus::after{left:auto;right:0;}
  .mstat.tip-up:hover::after,.mstat.tip-up:focus::after{top:auto;bottom:1.5em;}
  .mstat-move{font-size:.7em;margin-left:2px;cursor:help;vertical-align:.15em;position:relative;}
  .mstat-move.up{color:#2f6d4a;} .mstat-move.down{color:#a33a2a;} .mstat-move.changed{color:var(--ink-3);}
"""
