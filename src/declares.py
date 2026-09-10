"""Does every artefact declare what produced it? One table, at a glance.

    .venv/bin/python src/declares.py            # the table
    .venv/bin/python src/declares.py --verify   # exit 1 if anything is UNDECLARED or LYING

⛔ WHY THIS EXISTS. Over 2026-09-08/09 seven errors reached the owner, every one
born in the layer that turns artefacts into English. The project's 453 tests
cover `src/` almost completely and the code was never the problem; nothing
covered that layer. The owner's instruction was exact: *"it should be possible to
see at a glance if everything declares itself."*

⛔ AND THE FIRST DESIGN OF THIS TOOL WAS WRONG, IN THIS PROJECT'S FAVOURITE WAY.
A binary declared / not-declared table paints an artefact green when it carries
the right field names — and three of the six artefacts that declare anything at
all are currently carrying declarations that are **false**:
`forecast_frozen.json` names a commit twenty behind HEAD; two artefacts embed
schema-1 pool keys while every spec on disk is schema 2. A binary table would
have shown all three as compliant. So the audit has **THREE states**:

    ✓  DECLARED    the field is present and agrees with what the code says now
    ~  LYING       the field is present and DISAGREES  <- the interesting one
    ✗  UNDECLARED  the field is absent

**The count that matters is `~`.** An artefact that declares nothing is a known
gap; an artefact that declares wrongly is a gap wearing a badge, and it is the
one nobody can see today. Reading a declaration and then CHECKING it is the verb
`pools.stale_reason` already applies to specs; this applies it everywhere.

⚠️ REQUIRED FIELDS ARE SET BY KIND, NOT BY A SINGLE LIST. A pool spec is not a
run: it genuinely should not carry `draws` or `seed`, and a column of N/A cells
trains the eye to skip red ones — which is the `orphaned_scenario_claims` failure
this repository already ran, where ten claims survived two reviews because a
print is not an audit. Each kind's required list is tied to the incident that
proves it necessary; see `KINDS`.

⚠️ THIS IS NOT A FIFTH DIALECT. `freeze.bundle`'s field set is the canonical
vocabulary and this module reports CONFORMANCE to it. It defines no new identity
mechanism, and it deliberately does not write an artefact of its own.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

PROCESSED = Path("data/processed")

DECLARED, LYING, UNDECLARED = "✓", "~", "✗"

# ⛔ THE STRINGS THIS REPOSITORY'S OWN CODE WRITES WHEN IT CANNOT ANSWER.
# `freeze._git` returns "<unavailable>" when git fails; `freeze.pool_artefact_keys`
# writes "<absent>" or "<unreadable: …>" when a spec will not read. Each is a
# TRUTHY STRING, so a presence-by-truthiness check calls it declared — which is
# the failure mode this whole tool exists to catch, committed inside the tool.
# A blind review constructed all three and every one scored ✓.
_SENTINELS = ("<unavailable>", "<absent>", "<unreadable", "<missing", "unknown")


def _declared(value) -> bool:
    """Is this a real declaration, or an absence wearing one?"""
    if value is None or value is False:
        return False
    if isinstance(value, str):
        v = value.strip().lower()
        return bool(v) and not any(v.startswith(x) for x in _SENTINELS)
    if isinstance(value, (dict, list, tuple, set)):
        return bool(value)
    return True


@dataclass(frozen=True)
class Kind:
    """One class of artefact, and the fields its class must carry.

    ``why`` cites the incident that put each field on the list, so a future
    reader can argue with the evidence rather than with taste — and so a field
    nobody can justify gets dropped rather than accumulating.
    """
    name: str
    required: tuple[str, ...]
    why: str


KINDS: dict[str, Kind] = {
    # A spec is not a run. It records what it was BUILT from, and asking it for
    # a draw count would be a category error that fills the table with N/A.
    "spec": Kind(
        "spec", ("code", "config", "scope", "inputs"),
        "§1.173 — a spec that cannot say which code emitted it cannot be shown "
        "current, and every measurement against it is unverifiable"),
    # A run output. §1.93 is the case: the settled tree scored 382 against a
    # committed 384 and `history.json` recorded neither its draws nor its seed,
    # so the artefact could not say which of the two explanations was true.
    "run": Kind(
        "run", ("git", "draws", "seed", "env", "inputs", "time"),
        "§1.93 — two artefacts are not comparable without draws, seed and the "
        "resolved switches; §1.104 — the reproducibility claim is false without "
        "the hash-seed state"),
    # A scoreboard is a run PLUS a population. §1.69: `runnable` reported 9
    # city-years where the archive supported 24, nothing said why, and
    # ITERATING's "when to stop" concluded the model was finished on that number.
    "scoreboard": Kind(
        "scoreboard", ("git", "draws", "seed", "env", "inputs", "time",
                       "population"),
        "§1.69 — the denominator of every claim, implicit in a list's length; "
        "§1.214 — two statistics of one name, quoted against each other"),
    # The artefacts that declare least and carry the most risk. §1.75: six raw
    # inputs left `data/raw` between a fit and its commit, and the fitted
    # intermediates are STILL on disk and still read, derived from inputs that
    # no longer exist.
    "intermediate": Kind(
        "intermediate", ("inputs",),
        "§1.75 — a fitted intermediate outliving the inputs it was fitted "
        "from, undetectable from the artefact itself"),
}


@dataclass
class Row:
    path: str
    kind: str
    states: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @property
    def worst(self) -> str:
        vals = set(self.states.values())
        return LYING if LYING in vals else (UNDECLARED if UNDECLARED in vals
                                            else DECLARED)


class CannotAudit(SystemExit):
    """The audit could not run its own check. NEVER downgraded to a warning."""


def _live_pools_sha() -> str:
    """The live `pools.py` AST hash — every `~` verdict is measured against it.

    ⛔ IT RAISES. It used to swallow the exception and return None, and every
    caller was guarded `if live_sha and …` — so with `pools` unimportable the
    tool printed a green table over twenty-seven specs it had not checked, and
    the LYING count silently fell from 5 to 1 with no diagnostic. `--verify`
    would then have passed a tree it never inspected.

    An audit that reports "all clear" when it could not run is worse than no
    audit, and this repository already has the rule: a guard that answers
    "fine" when it could not run is worse than no guard (`montecarlo.run_model`
    on staleness). Failing closed is the whole point of the tool.
    """
    try:
        import pools
        return pools._code_sha(Path(pools.__file__))
    except Exception as exc:
        raise CannotAudit(
            f"cannot import `pools` to read the live code hash "
            f"({type(exc).__name__}: {exc}). Every `{LYING}` verdict in this "
            f"audit is measured against it, so without it the table would be "
            f"green on artefacts nothing checked. Refusing to print one.")


def _spec_rows(live_sha: str | None) -> list[Row]:
    rows = []
    for p in sorted(PROCESSED.rglob("pools_*.json")):
        r = Row(str(p), "spec")
        try:
            key = json.loads(p.read_text()).get("artefact_key") or {}
        except Exception as exc:
            r.states = {f: UNDECLARED for f in KINDS["spec"].required}
            r.notes.append(f"unreadable: {type(exc).__name__}")
            rows.append(r)
            continue
        # `code`: present AND still agreeing with the live module. This is the
        # ~ state's whole point — a spec can name a `pools_sha` and be stale.
        if "pools_sha" not in key:
            r.states["code"] = UNDECLARED
        elif live_sha and key["pools_sha"] != live_sha:
            r.states["code"] = LYING
            r.notes.append(f"pools_sha {key['pools_sha']} but the live module "
                           f"is {live_sha} — re-emit before believing it")
        else:
            r.states["code"] = DECLARED
        r.states["config"] = (
            DECLARED if all(_declared(key.get(f))
                            for f in ("config_sha", "cities_sha")) else UNDECLARED)
        r.states["scope"] = (
            DECLARED if all(_declared(key.get(f)) for f in ("city", "target"))
            else UNDECLARED)
        # §1.75 is an INPUTS incident, and the spec already carries the data
        # coordinate — it was simply never read. A spec whose judgement files
        # moved since emission read ✓ on everything.
        r.states["inputs"] = (
            DECLARED if all(_declared(key.get(f))
                            for f in ("deps_sha", "judgements_sha")) else UNDECLARED)
        rows.append(r)
    return rows


def _json_rows(live_keys: dict) -> list[Row]:
    """Run outputs and scoreboards, each checked against what it embeds."""
    out = []

    def spec_keys_current(embedded) -> str | None:
        """Do the pool keys this artefact embedded still match the specs?

        Returns a sentence when they do not. This is where `~` is earned: the
        field is present, well-formed, and wrong.
        """
        found = []
        malformed = []
        def walk(o):
            if isinstance(o, dict):
                if "pools_sha" in o:
                    found.append(o["pools_sha"])
                elif o and not any(isinstance(v, (dict, list)) for v in o.values()):
                    # A leaf dict of keys with no `pools_sha` is a key-shaped
                    # object that names no code. Truthy, and declares nothing.
                    malformed.append(sorted(o)[:3])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
            elif isinstance(o, str) and not _declared(o):
                malformed.append(o)
        walk(embedded)
        if malformed:
            return (f"embeds a key-shaped object that names no code "
                    f"({malformed[0]}) — truthy, and declares nothing")
        stale = {s for s in found if live_keys and s not in live_keys}
        if stale:
            return (f"embeds pools_sha {sorted(stale)[0]} against a tree whose "
                    f"specs carry {sorted(live_keys)[0]}")
        return None

    # --- the scoreboard -----------------------------------------------------
    hp = PROCESSED / "history.json"
    if hp.exists():
        r = Row(str(hp), "scoreboard")
        payload = json.loads(hp.read_text())
        if isinstance(payload, list):
            r.states = {f: UNDECLARED for f in KINDS["scoreboard"].required}
            r.notes.append("bare list — the pre-manifest shape; declares nothing")
        else:
            m = payload.get("manifest") or {}
            r.states["git"] = (DECLARED if _declared(m.get("git_commit"))
                               else UNDECLARED)
            r.states["draws"] = (DECLARED if m.get("draws") is not None
                                 else UNDECLARED)
            r.states["seed"] = (DECLARED if m.get("seed") is not None
                                else UNDECLARED)
            r.states["env"] = (DECLARED if _declared(m.get("env_switches"))
                               else UNDECLARED)
            r.states["time"] = (DECLARED if _declared(m.get("generated"))
                                else UNDECLARED)
            r.states["population"] = (
                DECLARED if (m.get("population") or {}).get("scored")
                else UNDECLARED)
            lie = spec_keys_current(m.get("pool_artefact_keys"))
            r.states["inputs"] = (LYING if lie else
                                  DECLARED if m.get("pool_artefact_keys")
                                  else UNDECLARED)
            if lie:
                r.notes.append(lie)
            if m.get("git_dirty"):
                # ⛔ A COMMIT ID THAT DOES NOT IDENTIFY THE CONTENT IS A FALSE
                # DECLARATION, NOT A FOOTNOTE. This was a note beside a ✓, so
                # the one artefact that arbitrates everything counted as fully
                # declared while naming a commit its content is not at.
                r.states["git"] = LYING
                r.notes.append(f"git_dirty — names {str(m.get('git_commit'))[:8]} "
                               f"but the tree had moved off it, so the commit "
                               f"does not identify this content")
        out.append(r)

    # --- run outputs --------------------------------------------------------
    # ⛔ `glob`, NOT `rglob`, MISSED joburg/2021/forecast_summary.json — a run
    # embedding a THIRD stale pools_sha at `_draws: 2`, sitting in
    # data/processed unseen. A scan-shaped check must state the population it
    # covers and assert it equals what it scanned (CLAUDE.md §4 rule 0); this
    # one did not, and recurred in the tool written to stop that class.
    for p in sorted(PROCESSED.rglob("*summary.json")):
        r = Row(str(p), "run")
        d = json.loads(p.read_text())
        sc = d.get("scenario") or {}
        r.states["time"] = (DECLARED if _declared(d.get("_generated"))
                            else UNDECLARED)
        r.states["draws"] = (DECLARED if d.get("_draws") is not None
                             else UNDECLARED)
        r.states["git"] = UNDECLARED
        r.states["seed"] = UNDECLARED
        r.states["env"] = UNDECLARED
        lie = spec_keys_current(sc.get("_pools_artefact_key"))
        r.states["inputs"] = (LYING if lie else
                              DECLARED if sc.get("_pools_artefact_key")
                              else UNDECLARED)
        if lie:
            r.notes.append(lie)
        out.append(r)

    # --- the other run-shaped artefacts the first scan did not see ----------
    for name in ("validation_2021.json", "width_budget.json", "sweep.json",
                 "interactive_data.json"):
        q = PROCESSED / name
        if not q.exists():
            continue
        r = Row(str(q), "run")
        try:
            d = json.loads(q.read_text())
        except Exception:
            d = {}
        d = d if isinstance(d, dict) else {}
        r.states["time"] = (DECLARED if _declared(d.get("generated")
                                                  or d.get("_generated"))
                            else UNDECLARED)
        r.states["draws"] = (DECLARED if d.get("draws") is not None
                             else UNDECLARED)
        for f in ("git", "seed", "env", "inputs"):
            r.states[f] = UNDECLARED
        # `validation_2021.json` is the only artefact in the tree carrying an
        # explicit contamination flag, and it is the artefact behind the
        # `published` self-benchmark (§1.216). Say so where it is visible.
        if any((c.get("model") or {}).get("in_sample")
               for c in (d.get("cities") or {}).values()):
            r.notes.append("in_sample: True on every city — a contaminated "
                           "artefact, and the flag was dropped when its "
                           "numbers were copied into the scoreboard (§1.216)")
        out.append(r)

    # --- the freeze ---------------------------------------------------------
    fp = PROCESSED / "forecast_frozen.json"
    if fp.exists():
        r = Row(str(fp), "run")
        d = json.loads(fp.read_text())
        c, prov = d.get("content") or {}, d.get("provenance") or {}
        r.states["git"] = (DECLARED if _declared(prov.get("git_commit"))
                           else UNDECLARED)
        if prov.get("git_dirty"):
            r.states["git"] = LYING
            r.notes.append("git_dirty — the commit it names does not identify "
                           "this content")
        r.states["draws"] = (DECLARED if c.get("draws") is not None
                             else UNDECLARED)
        r.states["seed"] = DECLARED if c.get("seed") is not None else UNDECLARED
        r.states["env"] = (DECLARED if _declared(c.get("env_switches"))
                           else UNDECLARED)
        # Deliberate in freeze's own design, so it is UNDECLARED and not a lie.
        r.states["time"] = UNDECLARED
        lie = spec_keys_current(c.get("pool_artefact_keys"))
        r.states["inputs"] = (LYING if lie else
                              DECLARED if c.get("pool_artefact_keys")
                              else UNDECLARED)
        if lie:
            r.notes.append(lie)
        try:
            import freeze as F
            head = F._git("rev-parse", "HEAD")
            if prov.get("git_commit") and head and prov["git_commit"] != head:
                r.states["git"] = LYING
                r.notes.append(f"names {prov['git_commit'][:8]}, HEAD is "
                               f"{head[:8]}")
        except Exception:
            pass
        out.append(r)
    return out


def _intermediate_rows() -> list[Row]:
    """The CSVs. They declare nothing, and that is the §1.75 exposure."""
    rows = []
    for p in sorted(PROCESSED.rglob("*.csv")):
        if p.name.startswith("."):
            continue
        r = Row(str(p), "intermediate")
        r.states["inputs"] = UNDECLARED
        rows.append(r)
    return rows


def audit() -> list[Row]:
    live_sha = _live_pools_sha()
    spec = _spec_rows(live_sha)
    live_keys = {live_sha} if live_sha else set()
    return spec + _json_rows(live_keys) + _intermediate_rows()


def report(rows: list[Row]) -> str:
    """The table, and the two numbers worth reading first."""
    out: list[str] = []
    add = out.append
    add("# Does every artefact declare what produced it?\n")
    add(f"`{DECLARED}` declared and agrees · `{LYING}` **declared and WRONG** · "
        f"`{UNDECLARED}` undeclared\n")

    # ⛔ THE DENOMINATOR WAS 76% CONSTANT. `_intermediate_rows` sets every CSV
    # to UNDECLARED unconditionally — there is no input by which one can read
    # otherwise — so quoting "28 of 137" mixed a measurement with a structural
    # fact and produced the wrong owner decision in the first ten seconds.
    # A denominator that cannot vary is not a denominator.
    capable = [r for r in rows if r.kind != "intermediate"]
    hole = [r for r in rows if r.kind == "intermediate"]
    lying = [r for r in capable if r.worst == LYING]
    clean = [r for r in capable if r.worst == DECLARED]
    add(f"**{len(clean)} of {len(capable)} artefacts that CAN declare "
        f"themselves do. {len(lying)} declare themselves and are WRONG.**\n")
    if lying:
        add("⛔ The second number is the one that matters: an artefact that "
            "declares nothing is a known gap; an artefact that declares "
            "wrongly is a gap wearing a badge, and nothing else can see it.\n")
    add(f"Separately, and a design gap rather than an audit result: "
        f"**{len(hole)} CSV intermediates carry no identity at all** and have "
        f"no mechanism to. That is the §1.75 exposure — a fitted intermediate "
        f"outliving the inputs it was fitted from. They are not counted above, "
        f"because a denominator that cannot vary is not a measurement.\n")

    by_kind: dict[str, list[Row]] = {}
    for r in rows:
        by_kind.setdefault(r.kind, []).append(r)

    for kind in ("scoreboard", "run", "spec", "intermediate"):
        krows = by_kind.get(kind)
        if not krows:
            continue
        k = KINDS[kind]
        add(f"\n## {kind} — {len(krows)} artefact(s)")
        add(f"*Required: {', '.join(k.required)}. {k.why}*\n")
        # Collapse the specs: 27 identical rows is furniture, and furniture
        # teaches the eye to skip. Show the exceptions and count the rest.
        if kind in ("spec", "intermediate") and len(krows) > 6:
            worst = [r for r in krows if r.worst != DECLARED]
            ok = len(krows) - len(worst)
            if ok:
                add(f"- {ok} fully declared (not listed individually)")
            for r in worst[:8]:
                note = f" — {r.notes[0]}" if r.notes else ""
                add(f"- `{r.worst}` {r.path}{note}")
            if len(worst) > 8:
                add(f"- … and {len(worst) - 8} more in the same state")
            continue
        add("| artefact | " + " | ".join(k.required) + " |")
        add("|---" * (len(k.required) + 1) + "|")
        for r in krows:
            cells = " | ".join(r.states.get(f, UNDECLARED) for f in k.required)
            add(f"| `{r.path}` | {cells} |")
        for r in krows:
            for n in r.notes:
                add(f"  - ⚠️ `{r.path}`: {n}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true",
                    help="exit 1 if any artefact is undeclared or lying")
    args = ap.parse_args(argv)
    rows = audit()
    print(report(rows))
    if not args.verify:
        return 0
    # Report EVERYTHING, then exit once. Exiting on the first finding hands the
    # reader one per run, which `build_site.py` already learned the hard way.
    bad = [r for r in rows if r.worst != DECLARED]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
