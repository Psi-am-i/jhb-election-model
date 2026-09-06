"""The register must not describe a model that does not exist.

`test_every_tunable_constant_is_in_the_judgement_register` checks **code →
register**: every tunable constant in `src/` is named in `JUDGEMENT-CALLS.md`.
That is one direction of two, and the missing direction is the one that failed.

On 2026-08-22 an audit found `JUDGEMENT-CALLS.md` §F carrying

    | `polling_lean`, `polling_span` | 0.0, 8.0 | superseded by the poll paths;
      still wired | 🟡 |

for a pair of levers that had been **deleted**, and whose only remaining trace
in `src/` was the comments recording their deletion. The register was making a
false claim about the model's current behaviour, in the file whose entire
purpose is to be the thing a reader trusts about the model's current behaviour,
and every guard passed. `POLL_RMS_ERROR` was in the same position — declared
live, read by nothing — and `MIN_SHARE` and `F_OTHER` were filed under modules
they have never been in.

Two guards here, both cheap:

* **register → code.** A symbol the register names in backticks must exist.
* **no line numbers.** They go stale silently and they had all gone stale: 24
  citations, 24 wrong, by 34 to 375 lines. A name does not drift.

MODEL-LOG §1.69.
"""

from __future__ import annotations

import ast
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module, scanned  # noqa: E402

SRC = ROOT / "src"
TESTS = ROOT / "tests"
REGISTER = ROOT / "JUDGEMENT-CALLS.md"


def _names_bound_in(paths, *, strings: bool) -> set[str]:
    """Every name these files bind: module, class, function, argument, attribute.

    Deliberately generous about SCOPE. This test exists to catch a register row
    naming something that does not exist AT ALL — a deleted lever, a renamed
    function, a constant filed under a module it was never in. It is not trying
    to police which scope a name lives in.

    It is NOT generous about string literals, and that distinction is the whole
    point of the ``strings`` flag. **A scenario key is a string in `src/`** —
    `scenario.get("poll_house_k")` binds nothing and the name exists only as a
    literal — so string constants in `src/` must count. **An exemption table is
    a string in `tests/`**, and counting those made this guard exempt its own
    exemptions:

        DELETED = {"polling_lean": "superseded by the poll paths; §1.68", ...}

    Every key of that dict is an `ast.Constant` string in a `tests/` file, so
    the moment a name was written into `DELETED` it became "defined" and
    `test_every_symbol_the_register_names_exists` could no longer see it as
    missing whatever the register claimed about it. **Measured 2026-08-31: all
    18 `DELETED` names were in the harvested population, and deleting the
    `t not in DELETED` clause outright changed the guard's verdict from 0
    offenders to 0 offenders** — the exemption list was inert, and inert in the
    direction that hides deletions. With string literals dropped from `tests/`
    the same clause is load-bearing on 11 names.
    """
    names: set[str] = set()
    for path in paths:
        names.add(path.stem)
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                names.add(node.name)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    a = node.args
                    for arg in (a.posonlyargs + a.args + a.kwonlyargs
                                + ([a.vararg] if a.vararg else [])
                                + ([a.kwarg] if a.kwarg else [])):
                        names.add(arg.arg)
            elif isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
            elif strings and isinstance(node, ast.Constant) \
                    and isinstance(node.value, str):
                # scenario keys are strings: scenario.get("poll_house_k")
                names.add(node.value)
    return names


def _defined_names() -> set[str]:
    """The population the register's symbols are checked against.

    `src/` with its string literals, because a scenario key is a literal;
    `tests/` WITHOUT them, because the register legitimately cites test
    functions (`test_the_two_maps_agree_on_the_confidence_tiers`) and test
    constants (`EXPECTED_INERT`, `MAX_DISPLACEMENT_RADII`) as the evidence for
    a row — measured 2026-08-31: eight such names, all real — while the string
    literals in `tests/` are exemption tables and fixtures.
    """
    return (_names_bound_in(sorted(SRC.glob("*.py")), strings=True)
            | _names_bound_in(sorted(TESTS.glob("*.py")), strings=False))


# LEVERS THIS REPOSITORY HAS DELETED. The register must be able to discuss them
# — a deletion that leaves no record is how a rejected idea gets rediscovered —
# but the list has to be EXPLICIT, so that "this name is not in the code" is a
# decision someone made rather than a gap the guard shrugged at. Adding a name
# here is itself a judgement, and each carries the entry that removed it.
DELETED = {
    "polling_lean": "superseded by the poll paths; §1.68",
    "polling_span": "superseded by the poll paths; §1.68",
    "poll_id": "legacy poll path, bypassed every admission rule; §1.68",
    "poll_weight": "legacy poll path; §1.68 — and it survived in two city "
                   "tomls until §1.69, which is why apply_city now rejects an "
                   "unknown [judgements.scalars] key",
    "poll_k": "legacy poll path; §1.68. The shape survives as poll_house_k",
    "POLL_K": "the module constant behind poll_k; §1.68",
    "pa_contestation_uplift": "a one-party constant, live only where no "
                              "backtest could reach it; §1.47",
    "theta_mode": "deleted 2026-08-19; §1.52",
    # Retired with `src/leverage.py` on 2026-08-31 (§1.140), to
    # `archive/retired-scripts/`. The script was standalone — never imported by
    # `run_model`, `compare_history` or the build, and nothing read its
    # `ward_leverage.csv` — and it typed six parties' growth rates with
    # `F_OTHER = 1.30` for anything unlisted. The disqualifying part is that
    # `f_other` itself was deleted from the model on 2026-08-19 (§1.52), so
    # every number the script printed after that date came from a path the
    # forecast had abandoned, while reading as a sensitivity analysis OF the
    # forecast. Recorded here rather than struck from the register because the
    # register is where a deleted constant is DISCUSSED, and the argument for
    # its removal is worth keeping.
    "THETA_CENTRAL": "six typed per-party theta centres in the retired "
                     "leverage.py; §1.140",
    "F_OTHER": "the 1.30 fallback growth for any party not named in "
               "THETA_CENTRAL, in the retired leverage.py. It ran `f_other`, "
               "deleted from the model 2026-08-19; §1.52, §1.140",
    "DA_LED_COALITION": "a two-party tuple in the retired leverage.py; §1.140",
    # Deleted 2026-08-28 (§1.119) on the owner's standing rule — "if something
    # is dead and no longer used, why would we want to keep it around". Each had
    # ZERO qualified readers in the tree, verified before deletion.
    "POLL_RMS_ERROR": "deleted 2026-08-28; §1.119. Read by nothing in src/ "
                      "since §1.67 replaced it with the sigma decomposition. "
                      "The register described it as the surviving CALIBRATION "
                      "TARGET, and that was its neighbour: the tests assert "
                      "against POLL_RMS_ERROR_2016 (0.0303). Its derivation — "
                      "Ipsos's nine 2016 metro readings, RMS 3.03pp — is kept "
                      "as a comment in polling.py, because POLL_HOUSE_SD is "
                      "that number with the sampling term removed",
    # Added 2026-08-26 by §1.100 and removed 2026-08-27 by §1.102, both inside a
    # day. They were the diagnostics on a repair to Johannesburg's 187%
    # registration rate; the repair was reverted once it was established that
    # the census adult count is not an input this model consumes — elections are
    # decided by registered voters and the roll is a counted list, so a rate
    # above 100% is a fact about the census, not a quantity to clamp.
    # JUDGEMENT-CALLS.md section I keeps the withdrawn set rather than silently
    # losing the rows, which is why these names still appear there.
    "census_blend": "diagnostic on the withdrawn registration repair; "
                    "§1.100 added, §1.102 removed",
    "census_blend_wanted": "as census_blend — the lift the roll asked for "
                           "before MAX_CENSUS_LIFT bound it; §1.100/§1.102",
}


# NAMES DELETED FROM THE MODEL THAT ARE STILL READ SOMEWHERE IN `src/`.
#
# These four were in `DELETED` until 2026-08-31, where they were doing nothing:
# the register names none of them, so they exempted no row, and they are all
# still in the tree, so the guard would not have flagged them anyway. Kept as a
# record, and CHECKED IN THE OPPOSITE DIRECTION — each must still be present.
# The day one of them finally leaves `src/`, the guard says so and the entry
# moves back to `DELETED`. An exemption that can only rot in one direction is
# how a deleted lever sat in the register for days.
#
# The finding this table records, measured 2026-08-31: `src/build_interactive.py`
# still reads `individual_theta`, `theta_mode`, `f_other` and `turnout_tilt_da`
# out of the scenario and the city judgements, with a typed fallback
# `[0.7, 1.3, 2.0]` for `f_other` — every one of them a lever deleted from the
# model, `turnout_tilt_da` being the exact lever CLAUDE.md cites as having been
# quoted on the published page for weeks after `run_model` stopped having it.
STILL_IN_THE_TREE = {
    "f_other": "deleted from the model 2026-08-19 (§1.52) — still read by "
               "build_interactive.py, which types [0.7, 1.3, 2.0] as its "
               "fallback",
    "individual_theta": "deleted 2026-08-19 (§1.52) — still read by "
                        "build_interactive.py from both the scenario and the "
                        "city judgements",
    "turnout_tilt_da": "deleted from run_model, and quoted on the published "
                       "page for weeks afterwards, which is why CLAUDE.md "
                       "carries the stat-token rule — still read by "
                       "build_interactive.py as `turnoutDA`",
    "OTHER": "parties.OTHER, deleted 2026-08-28 (§1.119) — the name survives "
             "as a display bucket string in export_interactive.py, "
             "render_map.py and render_sheet.py, which is a different thing "
             "wearing the same name",
}


# SECTIONS OF THE REGISTER THAT MAKE A LIVE CLAIM ON A DELETED LEVER, and that
# the register ITSELF records as flagged-and-not-resolved. Each entry must be
# matched by that admission in `JUDGEMENT-CALLS.md`, so the exemption cannot
# outlive the defect: fix the row, the note goes, and this test then demands
# the entry be removed. That is the difference between an exemption and a
# licence — CLAUDE.md's example of `poll_k` is precisely a licence, one row's
# obituary excusing another row's false live claim.
UNRESOLVED_LIVE_CLAIMS = {
    "§F21": "poll_k",     # heading still lists it as a live scenario key, 🟢
    "§F29": "F_OTHER",    # heading still lists it at 1.30, 🟡, after §1.140
}


def _register_symbols() -> dict[str, str]:
    """Backticked identifiers in the register, minus struck-through rows.

    A struck-through row (`~~name~~`) is a record that something was deleted, so
    its symbol is supposed to be gone. Those are the rows that keep this file
    honest and they must not be asserted on.
    """
    text = REGISTER.read_text()
    # Drop struck-through spans first, so a deleted lever's own obituary does
    # not fail the test that exists because obituaries were not being written.
    text = re.sub(r"~~.*?~~", "", text, flags=re.S)
    out: dict[str, str] = {}
    for line in text.splitlines():
        for tok in re.findall(r"`([^`]+)`", line):
            tok = tok.strip()
            # Only bare identifiers. Expressions, paths, prose, dotted calls
            # and anything with whitespace are out of scope.
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tok):
                out.setdefault(tok, line.strip()[:120])
    return out


def _vocabulary() -> set[str]:
    """Python builtins and the standard vocabulary of the prose. Not levers."""
    import builtins
    return set(dir(builtins)) | {
        "n", "z", "w", "k", "p", "s", "x", "y", "N", "K", "W", "S",
        "true", "false", "None", "nan", "int", "float", "str", "bool",
        "md", "json", "toml", "csv", "html", "py", "grep", "sed", "awk",
        "pytest", "numpy", "np", "scipy", "git", "main", "off", "all",
        "arrivals", "metro", "national", "province", "error", "warn",
        "claimed", "reference", "seat_holders", "blend", "deduct", "expand",
        "level", "cap", "low", "high", "mode", "median", "mean", "sd",
        # mathematical notation in the prose, not code identifiers
        "H_eff", "sd_log", "log", "exp",
    }


def _considered(named: dict[str, str]) -> dict[str, str]:
    """The register symbols this guard is willing to adjudicate.

    An identifier of one or two characters, or one with no underscore, is
    ambiguous between a lever and a word — `cap`, `HI`, `elif`, `cp` are all
    backticked somewhere in the prose. Measured 2026-08-31: of 214 backticked
    bare identifiers the filter keeps 169 and drops 45, and of the 45 dropped
    exactly five are absent from the tree, every one of them a word in a
    sentence rather than a lever. The filter is a real narrowing of the claim
    and `test_the_scan_covers_most_of_the_register` bounds it on both sides.
    """
    return {t: line for t, line in named.items() if len(t) > 2 and "_" in t}


def _register_symbols_that_do_not_exist(named, defined, exempt=DELETED):
    """The offenders. A FUNCTION so a constructed violation can use it too."""
    vocabulary = _vocabulary()
    return {t: line for t, line in _considered(named).items()
            if t not in defined and t not in vocabulary and t not in exempt}


def test_every_symbol_the_register_names_exists():
    """A register row may not name a lever the code does not have.

    This is the direction nothing checked, and it is the direction that failed:
    `polling_lean` and `polling_span` sat in §F marked "still wired" after they
    were deleted. A reader auditing the model would have gone looking for a
    lever that was not there — and, worse, a reader NOT auditing it would have
    believed the model had a behaviour it does not.
    """
    defined = _defined_names()
    named = _register_symbols()
    missing = _register_symbols_that_do_not_exist(named, defined)
    assert not missing, (
        "JUDGEMENT-CALLS.md names symbols that do not exist anywhere in src/:\n  "
        + "\n  ".join(f"`{t}`  — in: {line}" for t, line in sorted(missing.items()))
        + "\n\nEither the code was deleted and the register was not updated — "
          "the defect this test was written for — or the row names the wrong "
          "thing. If the name IS a deliberate record of a deletion, add it to "
          "`DELETED` above with the MODEL-LOG entry that removed it, so that "
          "the absence is a decision rather than a gap.")


# ---------------------------------------------------------------------------
# THE GUARD ON THE GUARD — CLAUDE.md, "A test that asserts ABSENCE must prove
# four things, and usually proves one".
# ---------------------------------------------------------------------------

def test_the_scan_covers_most_of_the_register():
    """(1) IT LOOKED. `assert not missing` passes on an empty scan.

    Both bounds are fractions of a denominator computed from the register
    itself — its `### §Xn ·` section headings — so neither goes stale as the
    register grows, and neither can be repaired by lowering a number. Measured
    2026-08-31: 117 headings, 214 backticked bare identifiers, 169 of them
    considered.

    The UPPER bound is the half that gets left out, and here it is the one that
    matters: if `_considered`'s filter breaks open, the guard starts
    adjudicating `elif`, `cp` and `HI` as levers and the failure looks like a
    rotten register rather than a broken scan.
    """
    headings = re.findall(r"^###\s+§\S+\s+·", REGISTER.read_text(), re.M)
    named = _register_symbols()
    scanned(named, of=headings, low=0.8, high=6.0,
            what="backticked bare identifiers in JUDGEMENT-CALLS.md",
            denominator="its numbered section headings")
    scanned(_considered(named), of=named, low=0.4, high=1.0,
            what="register symbols this guard adjudicates",
            denominator="all backticked bare identifiers")


def test_a_register_row_naming_a_symbol_that_does_not_exist_is_caught():
    """(2) IT CAN SEE, and (3) ON A CONSTRUCTED INPUT.

    The premise is not "the tree currently passes". A synthetic register naming
    a synthetic lever, and a synthetic `src/` that does not define it, are
    pushed through the SAME `_register_symbols_that_do_not_exist` the live test
    uses. If the detector is ever narrowed until it sees nothing, this fails
    while the live assertion stays green.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fake = Path(tmp) / "fake_module.py"
        fake.write_text('live_lever = 1.0\n\n'
                        'def use(cfg):\n'
                        '    return cfg.get("scenario_key_alive")\n')
        defined = _names_bound_in([fake], strings=True)

    named = {"live_lever": "| `live_lever` | 1.0 | 🟢 |",
             "scenario_key_alive": "| `scenario_key_alive` | — | 🟢 |",
             "ghost_lever": "| `ghost_lever` | 0.5 | still wired | 🟢 |"}
    caught = _register_symbols_that_do_not_exist(named, defined, exempt={})
    assert set(caught) == {"ghost_lever"}, (
        f"the detector was handed one register row naming a symbol no module "
        f"defines and two naming symbols that exist, and reported {sorted(caught)}. "
        f"It must report exactly ['ghost_lever'].")

    # And the exemption must be able to silence it — otherwise `DELETED` is
    # doing nothing, which is the state this file was in until 2026-08-31.
    assert not _register_symbols_that_do_not_exist(
        named, defined, exempt={"ghost_lever": "a reason"}), (
        "an exempted symbol was still reported; `DELETED` is not consulted.")


def test_the_deleted_exemption_is_load_bearing():
    """(0) THE RIGHT SET — the exemption must exempt something real.

    Until 2026-08-31 it exempted nothing. `_defined_names` harvested string
    literals out of `tests/`, and every key of `DELETED` is a string literal in
    THIS file, so each name made itself "defined" the moment it was written
    down. **Deleting the whole `t not in DELETED` clause changed the verdict
    from 0 offenders to 0 offenders.** A guard whose exemption list can be
    removed with no effect is not exempting; it is decorating.

    Measured after the fix: the clause is load-bearing on 11 of the 14 names.
    """
    defined = _defined_names()
    named = _register_symbols()
    without = _register_symbols_that_do_not_exist(named, defined, exempt={})
    assert without, (
        "removing `DELETED` from the guard changes nothing, so the guard "
        "cannot see a deleted lever the register still names. That is the "
        "exact defect §1.69 was written for, one layer down.")
    scanned(without, of=DELETED, low=0.3, high=1.0,
            what="register symbols kept green only by the DELETED exemption",
            denominator="entries in DELETED")


def test_no_deleted_entry_is_dead_weight_and_none_has_quietly_returned():
    """(0) BOTH DIRECTIONS, on the exemption tables themselves.

    An entry in `DELETED` earns its place by doing one of two jobs: the
    register names the symbol (so the entry is excusing a real row), or the
    symbol is genuinely absent from the tree (so the entry is the record of a
    real deletion). An entry that is NEITHER — the name still in the tree and
    no register row mentioning it — is dead weight, and dead weight in an
    exemption list is how a later, real offender gets waved through under a
    name someone already excused.

    Four entries were in that state on 2026-08-31 — `f_other`,
    `individual_theta`, `turnout_tilt_da`, `OTHER` — and are now in
    `STILL_IN_THE_TREE`, which is checked the other way round.
    """
    defined = _defined_names()
    register = REGISTER.read_text()

    dead = sorted(n for n in DELETED
                  if n in defined and f"`{n}`" not in register)
    assert not dead, (
        f"`DELETED` entries that exempt nothing and record nothing: {dead}.\n"
        f"Each name is still bound somewhere in src/ or tests/ AND is named "
        f"nowhere in JUDGEMENT-CALLS.md, so the entry cannot be excusing a "
        f"register row and cannot be recording an absence. Move it to "
        f"`STILL_IN_THE_TREE` with the evidence, or delete it.")

    returned = sorted(n for n in STILL_IN_THE_TREE if n not in defined)
    assert not returned, (
        f"`STILL_IN_THE_TREE` claims these names are still read somewhere, "
        f"and they are not: {returned}.\nThe deletion finally completed — "
        f"move the entry to `DELETED`, which is the table that records a "
        f"symbol being gone. An exemption that can only rot in one direction "
        f"is how `polling_lean` sat in the register for days.")

    overlap = sorted(set(DELETED) & set(STILL_IN_THE_TREE))
    assert not overlap, f"named in both tables, which cannot both be true: {overlap}"


def _live_rows_naming_a_deleted_lever(text: str, deleted) -> dict[str, str]:
    """Register sections whose SUBJECT names a deleted lever at a live status.

    The subject is what the row is ABOUT — everything between `·` and the
    status mark in a `### §Xn · … — 🟢` heading. A deleted lever named in the
    PROSE of a live row is a discussion of a deletion, which is what the
    register is for; named in the SUBJECT it is a claim that the model has
    that lever. `⚪` is the retired mark and `~~…~~` is a struck subject, so
    both are records rather than claims.
    """
    out: dict[str, str] = {}
    for section, subject, status in re.findall(
            r"^###\s+(§\S+)\s+·\s+(.*?)\s+—\s+(\S+)\s*$", text, re.M):
        if "~~" in subject or status == "⚪":
            continue
        for token in re.findall(r"`([^`]+)`", subject):
            if token in deleted:
                out[section] = token
    return out


def test_no_live_register_row_is_about_a_lever_that_was_deleted():
    """(0) THE FAILURE CLAUDE.md NAMES: one row's obituary licensing another's lie.

    `poll_k` is in `DELETED` so that §F30's obituary could name it — and that
    exemption is exactly what stops the register→code guard seeing §F21, whose
    heading still lists `poll_k` as a live scenario key at 🟢. The exemption
    was added for one row and spent on another.

    This detector reads the row's SUBJECT rather than its symbols, so an
    obituary stays legal and a live claim does not. Run against the register on
    2026-08-31 it found two, not the one that had been flagged by hand: §F21's
    `poll_k`, and §F29's `F_OTHER`, still listed at 1.30 and 🟡 after
    `src/leverage.py` was retired by §1.140.

    Both are recorded in `UNRESOLVED_LIVE_CLAIMS`, and **each entry must be
    matched by the register's own "flagged, not resolved" admission for that
    section**. When the row is fixed the admission goes with it, and this test
    then requires the entry to be removed. That is what makes it an exemption
    rather than a second licence.
    """
    text = REGISTER.read_text()
    found = _live_rows_naming_a_deleted_lever(text, DELETED)

    unexpected = {s: t for s, t in found.items()
                  if UNRESOLVED_LIVE_CLAIMS.get(s) != t}
    assert not unexpected, (
        "live register rows whose SUBJECT is a lever this repository deleted:\n  "
        + "\n  ".join(f"{s} · `{t}`" for s, t in sorted(unexpected.items()))
        + "\n\nThe row claims the model has a lever it does not. Strike the "
          "subject, or move the symbol into the row's prose where a deletion "
          "belongs. This is the §1.68 `polling_lean` failure repeated.")

    gone = sorted(set(UNRESOLVED_LIVE_CLAIMS) - set(found))
    assert not gone, (
        f"`UNRESOLVED_LIVE_CLAIMS` still excuses {gone}, and the register no "
        f"longer makes that claim. Delete the entry — an exemption that "
        f"outlives its defect is the next false live claim's licence.")

    for section in UNRESOLVED_LIVE_CLAIMS:
        assert re.search(
            rf"###\s+{re.escape(section)}\s+·(?:.|\n)*?"
            rf"Restructure note, [\d-]+ — flagged, not resolved", text), (
            f"{section} is excused here as a known-unresolved live claim, but "
            f"{REGISTER.name} carries no 'flagged, not resolved' note for it. "
            f"Either the register was fixed — remove the entry — or the "
            f"exemption was never the owner's decision to begin with.")


def test_the_register_cites_no_line_numbers():
    """`file.py:NNN` decays on a timescale of hours and decays invisibly.

    All 24 citations in §A were wrong on 2026-08-22 — by 34 to 375 lines,
    several pointing at blank lines — in a register whose own preamble warns
    that "a register that names the wrong line is worse than one that names
    none, because it is checked and passes". It had been re-verified six days
    earlier and the note saying so was itself stale.

    Cite the module and the symbol. A name does not drift.
    """
    text = REGISTER.read_text()
    cites = sorted(set(re.findall(r"[a-z_]+\.py:\d+(?:-\d+)?", text)))
    assert not cites, (
        "JUDGEMENT-CALLS.md cites line numbers:\n  " + "\n  ".join(cites)
        + "\n\nUse the module and the symbol instead — `levels.py`, `SHRINK` — "
          "which `test_every_symbol_the_register_names_exists` can then check. "
          "Every line number this register has ever carried has gone stale, "
          "twice, within a week. MODEL-LOG §1.69.")


def test_no_test_file_defines_a_test_after_its_main_block():
    """CLASS 17 — THE SUITE HIDES WHAT THE DOCUMENTED INVOCATION BREAKS.

    `run_all.py` imports each module and reads `vars()` afterwards, so it
    collects every `test_*` in the file whatever order they are defined in.
    A file's own `if __name__ == "__main__":` block does NOT: it runs at the
    point it appears, so any test defined below it is never collected when the
    file is run directly — the invocation `CLAUDE.md` documents.

    On 2026-08-23 five files were in that state, hiding nine tests between them:
    `test_temporal` collected 4 of 8, and `test_calibration_report`,
    `test_levers_are_live`, `test_pool_bounds` and `test_regressions` each hid
    one or two. Every one of them PASSED under the suite and printed a
    complete-looking pass count standalone. Found while chasing MODEL-LOG §1.75,
    which is the same failure one layer down: an absence that looks exactly like
    a deliberate choice.
    """
    offenders = {}
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        match = re.search(r'^if __name__ == "__main__":', text, re.M)
        if not match:
            continue
        below = re.findall(r"^def (test_\w+)", text[match.end():], re.M)
        if below:
            offenders[path.name] = below
    assert not offenders, (
        "tests defined below their file's `__main__` block, so running that "
        "file directly silently skips them:\n  "
        + "\n  ".join(f"{f}: {', '.join(t)}" for f, t in offenders.items())
        + "\n\nMove the `__main__` block to the END of the file. It is the "
          "last thing in every other file here for exactly this reason.")


if __name__ == "__main__":
    # AT THE END — this file holds the test that requires it. Append above.
    raise SystemExit(run_module(globals()))
