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
import tomllib
from datetime import datetime
from pathlib import Path

TOKEN = re.compile(r"\{\{([a-z0-9_]+)\}\}")

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
    if spec == "one_dp":
        return f"{float(value):.1f}"
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
        tip = f"Pinned {when}"
        if entry.get("run"):
            tip += f" · {entry['run']}"
        if live_str is not None and live_str != text:
            tip += f" · the model now says {live_str}"
        tip += f" · source: {src}"
    else:
        tip = f"Live from the current model run · source: {src}"
    # the tip goes into an attribute: escape before anything else can break out
    tip = (tip.replace("&", "&amp;").replace("<", "&lt;")
              .replace(">", "&gt;").replace('"', "&quot;"))
    live_attr = f' data-live="{live_str}"' if live_str is not None else ""
    return (f'<span class="mstat" data-mode="{mode}" data-token="{name}"'
            f' data-when="{when}"{live_attr} title="{tip}">{text}</span>')


def render(text: str, registry: dict, ctx: dict, *, wrap: bool = True):
    """Substitute every ``{{token}}``.

    Returns ``(text, drift_rows, unresolved)``. ``unresolved`` being
    non-empty is a build error for the caller; ``drift_rows`` are advisory.
    """
    drift: list[dict] = []
    unresolved: list[str] = []

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

        return _span(shown, entry, name, live_str) if wrap else shown

    return TOKEN.sub(_one, text), drift, unresolved


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

# Figures that are structural rather than modelled: statute, geography, dates.
# A number here is not a forecast and never goes stale.
STRUCTURAL = {
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
    "50", "100", "135", "136", "270",
    "1994", "1999", "2000", "2004", "2006", "2009", "2011", "2014", "2016",
    "2019", "2021", "2024", "2026",
}

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


def audit(text: str, *, allow=(), claim_patterns=CLAIM_PATTERNS,
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

    numbers: list[str] = []
    for match in re.finditer(r"(?<![\w.])(\d{1,3}(?:[.,]\d+)?\s?%|\d+\s+seats?)",
                             prose):
        token = match.group(1)
        bare = token.replace("%", "").replace("seats", "").replace("seat", "").strip()
        if bare in STRUCTURAL:
            continue
        context = prose[max(0, match.start() - 60):match.end() + 30].strip()
        if excused(context):
            continue
        numbers.append(f"{token.strip()!r}  …{context}…")

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


def drift_report(rows: list[dict]) -> str:
    if not rows:
        return "  no drift — every pinned stat is within tolerance"
    out = []
    for r in rows:
        out.append(f"  ⚠ {r['token']}: pinned {r['pinned']} → model now says "
                   f"{r['live']} (tolerance {r['tolerance']})")
        if r["used_in"]:
            out.append(f"      used in: {r['used_in']} — the argument may need rewriting")
    return "\n".join(out)


# The CSS/markup a page needs so pinned figures reveal their provenance.
# Injected into every page that renders tokens. `mstat` (model stat), NOT
# `stat` — that class is already the headline tiles, whose flex-column
# display turned every inline figure into its own block.
STAT_CSS = """  .mstat{display:inline;}
  .mstat[data-mode="fixed"]{border-bottom:1px dotted var(--ink-3);cursor:help;}
"""
