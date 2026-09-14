"""Does every artefact declare what produced it? One table, at a glance.

    .venv/bin/python src/declares.py            # the table
    .venv/bin/python src/declares.py --verify   # exit 1 if anything is UNDECLARED or LYING
    .venv/bin/python src/declares.py --processed DIR   # audit a tree elsewhere

⛔ BOTH OUTCOMES OF `--verify` WERE UNINFORMATIVE UNTIL 2026-09-14, AND
CLAUDE.md SENDS EVERY SESSION THROUGH IT *"before quoting or believing any
number"*. It failed OPEN from any working directory but the repository root —
`PROCESSED` was relative and `rglob` on a missing directory yields nothing
rather than raising, so `cd src && declares.py --verify` printed the all-clear
over a population of ZERO and exited 0. And from the root it could never exit 0
on any tree that could exist: `forecast_frozen.json` is committed,
`freeze` deliberately writes no timestamp (freeze.py:46), `Row.worst` is the
worst cell, and `--verify` failed on `worst`. See `_processed_root`,
`Row.unchecked` and the freeze block in `_json_rows` for the three repairs.

⛔ WHY THIS EXISTS. Over 2026-09-08/09 seven errors reached the owner, every one
born in the layer that turns artefacts into English. The suite — whatever
`tests/run_all.py` prints — covers `src/` almost completely and the code was
never the problem; nothing covered that layer. The owner's instruction was
exact: *"it should be possible to see at a glance if everything declares
itself."*

⛔ AND THE FIRST DESIGN OF THIS TOOL WAS WRONG, IN THIS PROJECT'S FAVOURITE WAY.
A binary declared / not-declared table paints an artefact green when it carries
the right field names, while the declaration it carries is **false** — an
artefact embedding a `pools_sha` from code that is no longer on disk is the
standing example, and run `--verify` to see how many there are now rather than
trusting a count written here. A binary table shows every one of them as
compliant. So the audit has **THREE states**:

⚠️ ONE OF THE ORIGINAL THREE EXAMPLES WAS NOT A LIE AND IS NO LONGER SCORED AS
ONE. This paragraph used to cite *"`forecast_frozen.json` names a commit twenty
behind HEAD"*. A freeze is a snapshot of a PAST published forecast, so it names
a past commit BY CONSTRUCTION, and the check went red on the next commit to the
repository whatever that commit touched — spending the state this module calls
"the interesting one" on correct behaviour, and on the one artefact CLAUDE.md §1
calls a tripwire. What is checked instead is whether the named commit EXISTS in
this repository; see the freeze block in `_json_rows`.

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

# ==========================================================================
# WHERE THE TREE IS. Anchored to the module, not to the shell's cwd.
# ==========================================================================
# It was `Path("data/processed")`, and `rglob` on a directory that does not
# exist yields nothing rather than raising -- so from any working directory
# but the repository root this tool audited NOTHING and printed the all-clear
# its own docstring exists to make impossible:
#
#     $ cd src && ../.venv/bin/python declares.py --verify
#     **0 of 0 artefacts that CAN declare themselves do.**        EXIT=0
#
# That is `_live_pools_sha`'s failure exactly -- a green table over a
# population nothing inspected -- committed again, in the tool written to
# catch it, thirty lines below the paragraph describing it. `_live_pools_sha`
# still succeeded there, because its `sys.path` insert is absolute, so not one
# thing in the output said the scan had found no tree.
#
# The anchor takes the cwd out of the question. `_processed_root` then REFUSES
# on an absent tree rather than scanning it, which is what `archive.py
# --verify` does by accident (its manifest is missing, so it exits 1) and what
# an audit must do on purpose.
REPO = Path(__file__).resolve().parents[1]
PROCESSED = REPO / "data" / "processed"

DECLARED, LYING, UNDECLARED = "✓", "~", "✗"

# ⛔ THE STRINGS THIS REPOSITORY'S OWN CODE WRITES WHEN IT CANNOT ANSWER.
# `freeze._git` returns "<unavailable>" when git fails; `freeze.pool_artefact_keys`
# writes "<absent>" or "<unreadable: …>" when a spec will not read. Each is a
# TRUTHY STRING, so a presence-by-truthiness check calls it declared — which is
# the failure mode this whole tool exists to catch, committed inside the tool.
# A blind review constructed all three and every one scored ✓.
# `<unrecorded>` joined them 2026-09-14 with `compare_history._seed_block`,
# which emits it for a row predating `scenario_defaults` -- "this row cannot
# say what seed it ran at" is exactly the fact the other five record, and it
# arrived in the one manifest that arbitrates the panel.
_SENTINELS = ("<unavailable>", "<absent>", "<unreadable", "<missing", "unknown",
              "<unrecorded", "<varies")


def _processed_root(override: Path | None = None) -> Path:
    """The tree to audit, or a typed refusal. NEVER an empty scan.

    ⛔ THE ALL-CLEAR THIS TOOL PRINTED FROM `src/` WAS NOT A FINDING, IT WAS AN
    ABSENCE. `rglob` on a missing directory yields nothing and raises nothing,
    so every population came back empty, every count came back 0, and `--verify`
    exited clean having inspected no artefact at all. CLAUDE.md 4 requires a
    scan-shaped check to state its population and assert it equals what it
    scanned; this is that assertion, made before the scan rather than after it.

    Raising `CannotAudit` rather than warning is the same decision
    `_live_pools_sha` documents: an audit that reports "all clear" when it could
    not run is worse than no audit.
    """
    root = Path(override) if override is not None else PROCESSED
    if not root.is_dir():
        raise CannotAudit(
            f"no artefact tree at {root} -- there is nothing to audit, and an "
            f"empty scan is not an all-clear. (`data/**` is gitignored, so a "
            f"fresh clone has no tree until the model is run; and this module "
            f"used to resolve the path against the WORKING DIRECTORY, which "
            f"made `cd src && python declares.py --verify` exit 0 over zero "
            f"artefacts. Pass --processed to audit a tree elsewhere.)")
    return root


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
    """One artefact, its per-field verdicts, and WHICH OF THEM WERE ASKED.

    ⛔ `unchecked` IS THE DIFFERENCE BETWEEN A GATE AND A RITUAL. Several cells
    in this table are set to `UNDECLARED` by this module WITHOUT LOOKING AT THE
    ARTEFACT, because no writer in the repository puts that field there at all:
    `montecarlo` writes no `git`, `seed` or `env` onto a summary, `freeze`
    *deliberately does not cover timestamps* (freeze.py:46), and a CSV has
    nowhere to carry an identity. Those cells cannot vary, and `report` already
    says so of the CSVs -- *"a denominator that cannot vary is not a
    measurement"*.

    `--verify` counted them anyway, so it returned 1 on EVERY POSSIBLE TREE,
    including one where nothing lies. A gate that cannot pass is read once and
    then ignored, and on the day a real `~` appears it says exactly what it
    said the day before. CLAUDE.md sends every session through this command
    *"before quoting or believing any number"*; it has to be able to answer.

    So the exemption is recorded HERE, at the site that sets the cell, rather
    than in a central list of names that would drift from the code -- and
    `report` prints its size, two-sided, so it cannot quietly grow to cover the
    whole table.
    """
    path: str
    kind: str
    states: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    unchecked: set[str] = field(default_factory=set)

    @property
    def worst(self) -> str:
        vals = set(self.states.values())
        return LYING if LYING in vals else (UNDECLARED if UNDECLARED in vals
                                            else DECLARED)

    @property
    def answerable(self) -> str:
        """`worst` over the cells this module actually interrogated.

        A LIE anywhere still counts: `unchecked` says "no artefact carries this
        field", never "do not read what is written here".
        """
        vals = {st for f, st in self.states.items() if f not in self.unchecked}
        if LYING in set(self.states.values()):
            return LYING
        return UNDECLARED if UNDECLARED in vals else DECLARED


class CannotAudit(SystemExit):
    """The audit could not run its own check. NEVER downgraded to a warning."""


def _display(path: Path) -> str:
    """Repository-relative where possible: the table is read by a human.

    `PROCESSED` is absolute since it was anchored to `__file__`, and an
    absolute path per row is forty characters of noise repeated 139 times.
    """
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


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


def _spec_rows(live_sha: str | None, processed: Path) -> list[Row]:
    rows = []
    for p in sorted(processed.rglob("pools_*.json")):
        r = Row(_display(p), "spec")
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


def _json_rows(live_keys: dict, processed: Path) -> list[Row]:
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
    hp = processed / "history.json"
    if hp.exists():
        r = Row(_display(hp), "scoreboard")
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
            # `_declared`, NOT `is not None`. `seed` is the one manifest
            # field that can now arrive as a SENTINEL -- `_seed_block` writes
            # `<unrecorded>` for a row that predates `scenario_defaults` -- and
            # a truthy string passing a presence check is the exact failure
            # `_SENTINELS` exists for. `_declared` is safe for the numeric
            # cases: it returns True for 0, and True for a non-empty list of
            # seeds (which is what a panel that did not agree emits).
            r.states["seed"] = (DECLARED if _declared(m.get("seed"))
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
    for p in sorted(processed.rglob("*summary.json")):
        r = Row(_display(p), "run")
        d = json.loads(p.read_text())
        sc = d.get("scenario") or {}
        r.states["time"] = (DECLARED if _declared(d.get("_generated"))
                            else UNDECLARED)
        r.states["draws"] = (DECLARED if d.get("_draws") is not None
                             else UNDECLARED)
        # NOT INTERROGATED: `montecarlo.main` writes no git sha, no seed and no
        # resolved switches onto a summary, so these three cells read the same
        # on every summary that has ever existed. They are the 1.93 gap, worth
        # keeping visible in the table -- and worth keeping out of the exit
        # code, which otherwise says "something is wrong here" about a design
        # decision, on every tree, for ever.
        r.states["git"] = UNDECLARED
        r.states["seed"] = UNDECLARED
        r.states["env"] = UNDECLARED
        r.unchecked |= {"git", "seed", "env"}
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
        q = processed / name
        if not q.exists():
            continue
        r = Row(_display(q), "run")
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
        r.unchecked |= {"git", "seed", "env", "inputs"}
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
    fp = processed / "forecast_frozen.json"
    if fp.exists():
        r = Row(_display(fp), "run")
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
        # NOT INTERROGATED, and deliberate in `freeze`'s own design: its
        # docstring says the bundle *"deliberately does NOT cover timestamps or
        # file paths, which move without meaning"* (freeze.py:46). The cell is
        # shown, because a reader should know the freeze carries no date; it is
        # not counted, because a `run`'s required list demanding a field the
        # only writer refuses to emit is what made `--verify` return 1 on every
        # tree that could ever exist. THIS CELL ALONE WAS THE WHOLE OF IT:
        # `forecast_frozen.json` is committed, `Row.worst` is the worst cell,
        # and `--verify` failed on `worst`.
        r.states["time"] = UNDECLARED
        r.unchecked.add("time")
        lie = spec_keys_current(c.get("pool_artefact_keys"))
        r.states["inputs"] = (LYING if lie else
                              DECLARED if c.get("pool_artefact_keys")
                              else UNDECLARED)
        if lie:
            r.notes.append(lie)
        # ==================================================================
        # ⛔ A FREEZE NAMING AN OLDER COMMIT IS NOT LYING. THAT IS WHAT IT IS
        # FOR.
        # ==================================================================
        # This block read `prov["git_commit"] != head` and spent a `~` on it.
        # `~` is the state this module's docstring calls *the one that
        # matters* -- "a gap wearing a badge" -- and it was being burned on
        # correct behaviour: a freeze is a snapshot of a PAST published
        # forecast, so it names a past commit by construction, and the cell
        # went red on the next commit to the repository whatever that commit
        # touched. A documentation-only commit turned the one artefact
        # CLAUDE.md calls a tripwire into a declared liar.
        #
        # Two further faults were in the same six lines:
        #
        #   * `freeze._git` RETURNS THE STRING "<unavailable>" when git fails
        #     (freeze.py:140-145) rather than raising. It is truthy, so `head`
        #     passed the `and`, and `commit != "<unavailable>"` is true of
        #     every commit -- a FALSE `~` on any machine without git. That is
        #     the sentinel class `_SENTINELS` exists for, unguarded, inside the
        #     module that defines it.
        #
        #   * `except Exception: pass` left the row at whatever it already
        #     said -- `DECLARED` -- when the check could not run. A silent
        #     downgrade to "fine" is precisely what `_live_pools_sha` raises to
        #     prevent, in the file that documents why.
        #
        # What replaces it is a check that can actually fail: does this
        # repository CONTAIN the commit the freeze names? A commit id naming
        # nothing is a false declaration under any reading. Being behind HEAD
        # is reported as the tripwire it is -- a note on a row that still
        # counts as declared -- because CLAUDE.md 1 is explicit that a freeze
        # *"says go and look"* and *"never decides whether a change is right"*.
        named = prov.get("git_commit")
        try:
            import freeze as F
            head = F._git("rev-parse", "HEAD")
            known = F._git("rev-parse", "--verify", "--quiet",
                           f"{named}^{{commit}}") if _declared(named) else None
        except Exception as exc:
            r.notes.append(
                f"the commit it names could NOT be checked "
                f"({type(exc).__name__}: {exc}) -- this cell is unverified, "
                f"not clean")
        else:
            if not _declared(head):
                # git is unusable here. Say so; do not score it either way.
                r.notes.append(
                    "git is unavailable in this environment, so the commit "
                    "this freeze names was NOT checked against the repository")
            elif _declared(named) and not _declared(known):
                r.states["git"] = LYING
                r.notes.append(
                    f"names {str(named)[:8]}, which is not a commit in this "
                    f"repository -- the declaration resolves to nothing")
            elif _declared(named) and named != head:
                r.notes.append(
                    f"names {str(named)[:8]}, HEAD is {head[:8]} -- expected: "
                    f"a freeze records a PAST forecast. It is a tripwire, not "
                    f"a gate: re-read it before comparing anything to it")
        out.append(r)
    return out


def _intermediate_rows(processed: Path) -> list[Row]:
    """The CSVs. They declare nothing, and that is the §1.75 exposure."""
    rows = []
    for p in sorted(processed.rglob("*.csv")):
        if p.name.startswith("."):
            continue
        r = Row(_display(p), "intermediate")
        # NOT INTERROGATED: there is no field on a CSV for this to read. The
        # cell is structural, which `report` has always said in prose -- "a
        # denominator that cannot vary is not a measurement" -- while
        # `--verify` counted all of them anyway.
        r.states["inputs"] = UNDECLARED
        r.unchecked.add("inputs")
        rows.append(r)
    return rows


def audit(processed: Path | None = None) -> list[Row]:
    root = _processed_root(processed)
    live_sha = _live_pools_sha()
    spec = _spec_rows(live_sha, root)
    live_keys = {live_sha} if live_sha else set()
    return spec + _json_rows(live_keys, root) + _intermediate_rows(root)


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

    # ⛔ THE EXEMPTION IS PRINTED, WITH ITS DENOMINATOR, OR IT GROWS UNWATCHED.
    # `--verify` ignores UNDECLARED on cells this module sets without reading
    # the artefact (see `Row.unchecked`). An exemption nobody can see is how a
    # gate stops meaning anything the second time — so it is reported with the
    # fraction it covers and the field/kind pairs it is made of, both DERIVED
    # from the rows rather than typed beside them. If that fraction ever
    # approaches 1 the gate has become a ritual and this line is the tell.
    #
    # Counted over the artefacts that CAN declare — the CSVs' one blind cell is
    # the §1.75 hole described in the paragraph above, and counting it twice
    # would put the fraction near half and make a known design gap read as a
    # hole in the gate.
    #
    # ⚠️ "`x` on 4 of 11 runs", NOT "`x` on every run. The first draft
    # collapsed to (field, kind) and printed *"`inputs` on every run"* when
    # four of eleven run rows are exempt on `inputs` and the rest are fully
    # interrogated on it — an exemption that reads wider than it is, in the
    # line whose whole job is to stop the exemption growing unnoticed.
    cells = sum(len(r.states) for r in capable)
    blind: dict[tuple[str, str], int] = {}
    for r in capable:
        for f in r.unchecked & set(r.states):
            blind[(f, r.kind)] = blind.get((f, r.kind), 0) + 1
    per_kind: dict[str, int] = {}
    for r in capable:
        per_kind[r.kind] = per_kind.get(r.kind, 0) + 1
    n_blind = sum(blind.values())
    if cells:
        pairs = ", ".join(f"`{f}` on {n} of {per_kind[k]} {k}(s)"
                          for (f, k), n in sorted(blind.items()))
        add(f"**{n_blind} of {cells} cells on those {len(capable)} artefacts "
            f"({n_blind / cells:.0%}) were never interrogated** — no writer in "
            f"`src/` puts that field on that artefact, so the cell cannot vary "
            f"and `--verify` does not count it: {pairs}. A `{LYING}` is still "
            f"counted wherever it appears, and so is a `{UNDECLARED}` on any "
            f"cell not named here.\n")

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
    ap.add_argument("--processed", type=Path, default=None,
                    help="audit a tree other than the repository's own "
                         "data/processed (used by the positive control: a "
                         "gate that has never been shown to PASS has not been "
                         "shown to distinguish anything)")
    args = ap.parse_args(argv)
    rows = audit(args.processed)
    print(report(rows))
    if not args.verify:
        return 0
    # Report EVERYTHING, then exit once. Exiting on the first finding hands the
    # reader one per run, which `build_site.py` already learned the hard way.
    #
    # ⛔ `r.answerable`, NOT `r.worst`. `worst` counts the cells nothing writes
    # and nothing can write, so this returned 1 on every tree that has ever
    # existed and every tree that could -- `forecast_frozen.json` is committed
    # and `freeze` deliberately emits no timestamp, which was enough on its own.
    # A gate with one possible answer transmits no information, and a session
    # told to run it "before quoting or believing any number" learns in one
    # reading to ignore the result. See `Row.unchecked` for what is exempt and
    # why it is recorded at the site that sets it.
    bad = [r for r in rows if r.answerable != DECLARED]
    if bad:
        lying = [r for r in bad if LYING in set(r.states.values())]
        print(f"\n⛔ --verify FAILS: {len(bad)} of {len(rows)} artefact(s), "
              f"{len(lying)} of them declaring something WRONG rather than "
              f"declaring nothing. Every one is listed above with the cell "
              f"that failed.")
    else:
        print(f"\n✓ --verify passes: no artefact in {_processed_root(args.processed)} "
              f"declares anything false, and every field a writer in `src/` "
              f"actually emits is present on the artefacts that carry it.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
