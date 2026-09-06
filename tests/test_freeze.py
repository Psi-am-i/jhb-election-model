"""CLASS 19 — A REFERENCE THAT CANNOT BE CHECKED IS NOT A REFERENCE.

`data/processed/forecast_frozen.json` records what we published and the exact
configuration that produced it.

**It is NOT a benchmark and these tests do not make it one** — see `CLAUDE.md`,
"Nothing this model has ever produced is a standard of correctness". Nothing
here asserts that the model still agrees with the freeze; a change is judged by
backtesting against real election results. What these tests check is that the
RECORD is honest: that its hash covers its content, that it describes the
configuration the model actually has, and that it names a commit that exists.
A dishonest record is worthless for accountability and misleading as a
tripwire.

**These tests are deliberately CHEAP and do not run the model.** The expensive
check — re-run the forecast and compare — is `python src/freeze.py --verify`,
about two minutes, and belongs in the release path rather than in a suite that
already takes twenty-five. What is here instead is everything that can be
checked without a run, which turns out to be most of what goes wrong: a hash
that does not match its own content, a freeze taken on a dirty tree, a freeze
whose recorded commit no longer exists, a lever that has been added to
`DEFAULTS` since and is therefore unfrozen.

The last of those is the one that will actually fire, and it did within the
hour: `poll_credence` was added to `DEFAULTS` and the freeze stopped describing
the shipped configuration until it was retaken.

sources:
    MODEL-LOG §1.94 — the freeze, and why its first version could not reproduce
    PLAN: "Make the model declare itself", Phase 0
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import montecarlo as M  # noqa: E402

FROZEN = ROOT / "data" / "processed" / "forecast_frozen.json"


def _load() -> dict:
    assert FROZEN.exists(), (
        f"no freeze at {FROZEN}. Every 'this changed nothing' claim in the "
        f"restructure is measured against it. Run `python src/freeze.py`.")
    return json.loads(FROZEN.read_text())


def test_the_freeze_hash_matches_its_own_content():
    """The cheapest possible guard, and it catches a hand-edited freeze.

    A freeze is quotable only because its hash covers its content. If someone
    corrects a median by hand — which is exactly what happens to a file that
    looks like a summary — the hash stops matching and this says so.
    """
    frozen = _load()
    canonical = json.dumps(frozen["content"], sort_keys=True,
                           separators=(",", ":"))
    recomputed = hashlib.sha256(canonical.encode()).hexdigest()
    assert recomputed == frozen["content_sha256"], (
        f"the freeze's content_sha256 does not match its content:\n"
        f"  recorded   {frozen['content_sha256']}\n"
        f"  recomputed {recomputed}\n"
        f"Either the file was edited by hand or the hashing changed. Re-run "
        f"`python src/freeze.py` deliberately; do not patch the hash.")


def test_the_freeze_covers_every_declared_lever():
    """A lever added after the freeze is a lever the reference does not cover.

    This is the failure that will actually happen. `DEFAULTS` grows — it has
    grown repeatedly, `level_sd_default` and `arrival_group_draw` among them —
    and unless the freeze is retaken, the fixed reference silently stops
    describing the configuration it claims to.
    """
    frozen = _load()
    frozen_levers = set(frozen["content"]["scenario"])
    declared = set(M.DEFAULTS)
    missing = sorted(declared - frozen_levers)
    assert not missing, (
        f"{len(missing)} lever(s) in DEFAULTS are not in the freeze: "
        f"{missing}\nThe freeze was taken before they existed, so it is no "
        f"longer a description of the shipped configuration. Re-run "
        f"`python src/freeze.py` and commit it.")
    extra = sorted(frozen_levers - declared)
    assert not extra, (
        f"the freeze carries lever(s) that no longer exist in DEFAULTS: "
        f"{extra}\nThey were deleted after the freeze was taken; re-freeze so "
        f"the reference matches the model.")


def test_the_freeze_records_every_environment_switch():
    """The switches change the forecast and are invisible almost everywhere.

    They are absent from `DEFAULTS` and unreachable from `--set`, so two runs
    differing in them were indistinguishable from their recorded scenario —
    which is how a baseline was measured against the RETIRED sigma on
    2026-08-24 without anyone noticing until the numbers made no sense.

    **Corrected 2026-08-27: "and not written to the run trace" was true when
    written and is not true now.** `montecarlo.MODULE_CONSTANTS` declares five
    of the env-derived constants — `polling.SIGMA_TWO_TERM`,
    `levels.FILTER_TYPE_A`, `EXCLUDE_DEMARCATION_CROSSING`, `THETA_WINDOW`,
    `THETA_EXCLUDE_TARGETS` — so `note_module_constants` resolves them into
    `scenario["_delivered"]`, and from there into `45_delivered.json` and
    `forecast_summary.json`. What is still true, and is why this test stays:
    only the RESOLVED value travels that way, so an unset variable and one set
    to its own default are the same record everywhere EXCEPT the `raw` block
    below. That distinction is this freeze's alone.

    The seventh switch is `PYTHONHASHSEED`, added the same day. It decides
    whether this published artefact is reproducible to the last bit, and it
    was recorded in no artefact at all until then (§1.104).
    """
    import freeze as F
    frozen = _load()
    raw = frozen["content"]["env_switches"]["raw"]
    missing = sorted(set(F.ENV_SWITCHES) - set(raw))
    assert not missing, (
        f"environment switches missing from the freeze: {missing}")
    resolved = frozen["content"]["env_switches"]["resolved"]
    assert resolved, "the freeze records no RESOLVED switch values"
    assert "polling.SIGMA_TWO_TERM" in resolved, (
        "the freeze does not record the resolved value of SIGMA_TWO_TERM, "
        "which selects between two entirely different sigma decompositions "
        "and defaults to on from an UNSET variable")

    # ⛔ AND THE OTHER DIRECTION, WHICH IS THE ONE THAT FAILED.
    #
    # Everything above asserts ENV_SWITCHES ⊆ the freeze. Nothing asserted that
    # the variables `src/` actually READS are ⊆ ENV_SWITCHES — so a switch could
    # be added to the code and never to the register, which is exactly what
    # happened to `HELD_BACK_OFF`. It empties `levels.HELD_BACK` at import,
    # moving `theta_record` from 410 observations to 458 and setting every band
    # width in the published forecast, and it was in no register for weeks.
    #
    # This is CLAUDE.md §4 point 0: the claim is a set EQUALITY and the scan was
    # a subset check. MODEL-LOG §1.193 class A.
    import ast as _ast
    read: set[str] = set()
    for path in sorted(Path(ROOT / "src").glob("*.py")):
        tree = _ast.parse(path.read_text())
        for node in _ast.walk(tree):
            # os.environ.get("X") / os.environ["X"] / os.getenv("X")
            name = None
            if isinstance(node, _ast.Call):
                fn = node.func
                if (isinstance(fn, _ast.Attribute) and fn.attr in ("get", "getenv")
                        and node.args and isinstance(node.args[0], _ast.Constant)
                        and isinstance(node.args[0].value, str)):
                    src = _ast.unparse(fn.value)
                    if "environ" in src or src.endswith("os"):
                        name = node.args[0].value
            elif (isinstance(node, _ast.Subscript)
                  and isinstance(node.slice, _ast.Constant)
                  and isinstance(node.slice.value, str)
                  and "environ" in _ast.unparse(node.value)):
                name = node.slice.value
            if name and name.isupper():
                read.add(name)

    assert read, (
        "the AST scan found no environment reads in src/ at all — the detector "
        "is broken, not the code")
    unregistered = sorted(read - set(F.ENV_SWITCHES)
                          - set(getattr(F, "ENV_NOT_RECORDED", {})))
    assert not unregistered, (
        f"src/ reads these environment variables and the freeze records none "
        f"of them: {unregistered}.\n\n"
        f"A switch the code obeys and the artefact does not record makes two "
        f"freezes indistinguishable when they were produced differently — "
        f"§1.104's failure, and §1.193's. Add each to `freeze.ENV_SWITCHES`, "
        f"or stop reading it, or add it to `freeze.ENV_NOT_RECORDED` with the "
        f"reason it cannot change a number.")

    # An exemption must be for a variable that IS read, or the list is decoration
    # that hides the next real one.
    stale = sorted(set(getattr(F, "ENV_NOT_RECORDED", {})) - read)
    assert not stale, (
        f"`freeze.ENV_NOT_RECORDED` exempts {stale}, which `src/` does not "
        f"read. An exemption for a variable nobody reads is dead weight that "
        f"makes the list look considered when it is stale.")


def test_the_freeze_names_a_commit_that_exists_and_a_clean_tree():
    """A freeze taken on a dirty tree cannot be reproduced from the repository.

    It is still useful as a local reference, so this reports rather than
    forbids — but it must not be quoted as reproducible, and the only way to
    know is to record it.
    """
    frozen = _load()
    prov = frozen["provenance"]
    commit = prov.get("git_commit", "")
    assert commit and commit != "<unavailable>", (
        "the freeze records no git commit, so nothing can say which code "
        "produced it")
    found = subprocess.run(("git", "cat-file", "-e", f"{commit}^{{commit}}"),
                           cwd=ROOT, capture_output=True)
    assert found.returncode == 0, (
        f"the freeze names commit {commit[:9]}, which is not in this "
        f"repository. It was taken on a branch that has since been rewritten "
        f"or discarded, so the code that produced it cannot be recovered.")
    assert not prov.get("git_dirty"), (
        f"the freeze at {commit[:9]} was taken on a DIRTY tree, so it cannot "
        f"be reproduced from a commit alone. Re-take it on a clean tree "
        f"before quoting it as a reference.")


def test_the_frozen_forecast_is_a_council():
    """A sanity floor. Catches a freeze of a run that did not finish.

    Not a value test — the freeze IS the value — but a freeze whose medians sum
    to nothing like a council is a freeze of a broken run, and that should not
    become the reference everything is measured against.
    """
    frozen = _load()
    content = frozen["content"]
    parties = content["parties"]
    assert parties, "the freeze records no parties"
    total = sum(v["median"] for v in parties.values())
    council = content["council"]
    assert 0.5 * council <= total <= 1.5 * council, (
        f"the frozen per-party medians sum to {total:.0f} against a council of "
        f"{council}. Per-party medians do not sum to a council exactly — that "
        f"is what `seat_abs_err_coherent` exists for — but they should be "
        f"within half of it, and this is not.")
    for party, v in parties.items():
        assert v["p5"] <= v["median"] <= v["p95"], (
            f"{party}'s frozen interval is inverted: "
            f"p5 {v['p5']} median {v['median']} p95 {v['p95']}")


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
