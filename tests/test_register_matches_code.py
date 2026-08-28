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
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _support import ROOT, run_module  # noqa: E402

SRC = ROOT / "src"
TESTS = ROOT / "tests"
REGISTER = ROOT / "JUDGEMENT-CALLS.md"


def _defined_names() -> set[str]:
    """Every name `src/` binds at any level: module, class, function, argument.

    Deliberately generous. This test exists to catch a register row naming
    something that does not exist AT ALL — a deleted lever, a renamed function,
    a constant filed under a module it was never in. It is not trying to
    police which scope a name lives in.
    """
    names: set[str] = set()
    for path in sorted(SRC.glob("*.py")) + sorted(TESTS.glob("*.py")):
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
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                # scenario keys are strings: scenario.get("poll_house_k")
                names.add(node.value)
    return names


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
    "individual_theta": "deleted 2026-08-19; §1.52",
    "f_other": "deleted 2026-08-19; §1.52",
    # Deleted 2026-08-28 (§1.119) on the owner's standing rule — "if something
    # is dead and no longer used, why would we want to keep it around". Each had
    # ZERO qualified readers in the tree, verified before deletion.
    "OTHER": "parties.OTHER, deleted 2026-08-28; §1.119. It was 'the residual "
             "bucket that f_other scales', and f_other went on 2026-08-19 "
             "(§1.52) — it outlived its only stated purpose by nine days. The "
             "OTHER bucket the site shows is built in the presentation layer",
    "POLL_RMS_ERROR": "deleted 2026-08-28; §1.119. Read by nothing in src/ "
                      "since §1.67 replaced it with the sigma decomposition. "
                      "The register described it as the surviving CALIBRATION "
                      "TARGET, and that was its neighbour: the tests assert "
                      "against POLL_RMS_ERROR_2016 (0.0303). Its derivation — "
                      "Ipsos's nine 2016 metro readings, RMS 3.03pp — is kept "
                      "as a comment in polling.py, because POLL_HOUSE_SD is "
                      "that number with the sampling term removed",
    "turnout_tilt_da": "deleted; it was still quoted on the published page "
                       "for weeks afterwards, which is why CLAUDE.md carries "
                       "the stat-token rule",
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
    # Python builtins and the standard vocabulary of the prose are not levers.
    import builtins
    vocabulary = set(dir(builtins)) | {
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
    missing = {t: line for t, line in named.items()
               if t not in defined and t not in vocabulary
               and t not in DELETED and len(t) > 2 and "_" in t}
    assert not missing, (
        "JUDGEMENT-CALLS.md names symbols that do not exist anywhere in src/:\n  "
        + "\n  ".join(f"`{t}`  — in: {line}" for t, line in sorted(missing.items()))
        + "\n\nEither the code was deleted and the register was not updated — "
          "the defect this test was written for — or the row names the wrong "
          "thing. If the name IS a deliberate record of a deletion, add it to "
          "`DELETED` above with the MODEL-LOG entry that removed it, so that "
          "the absence is a decision rather than a gap.")


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
