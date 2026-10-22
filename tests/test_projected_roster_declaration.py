"""THE PROJECTED-ROSTER DECLARATION MUST SAY WHERE, HOW, AND WHAT ENDS IT.

``montecarlo.run_model`` prints a warning, unconditionally, whenever the ballot
it drops against is a PROJECTION rather than the target's own result file. The
warning existed before this module and said three of the four things it needed
to: that the roster is projected, how many parties are on it, and which
``roster_source`` the spec claimed. What it did not say was **where the file
is** (it named ``pools_<year>.json``, a filename carried by one spec per
city-year under two different roots), **how the projection was derived**, or
**what ends the condition** — so a reader told the roster is a guess could not
check the guess, could not say what it was a guess *from*, and had no way to
know whether the flag clears before polling day or after it.

⚠️ **AND IT CLEARS AFTER POLLING DAY, NOT BEFORE.** This is the fact the
declaration exists to correct, and the intuitive reading is wrong:
``roster_for_target`` branches on ``cityconfig.CALENDAR[year].results`` and
``pools.contesting_parties`` reads the *result* file, so ``published`` is
unreachable until the election has been held and ingested. A nomination list
pasted into the judgement file makes the roster far better — ``roster_source``
becomes ``declared`` — and still reports ``projected`` here. A reader who
believes the warning will disappear when the IEC publishes its lists will go on
believing the model is un-flagged when it is not.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS.** The claim is *"every roster
   source the emit can produce is explained"*. The population is therefore the
   set of string literals ``pools.resolve_roster`` assigns to ``roster_source``
   — read out of its AST, not typed here — and
   ``test_every_roster_source_the_emit_can_produce_is_explained`` asserts set
   EQUALITY against what the declaration branches on. Equality, not containment,
   because containment in one direction is exactly the blind spot §4 names as
   the worst record of the four: a register that lists a state the code cannot
   produce is as wrong as a state the register omits, and only one of the two
   directions is usually checked.
1. **IT LOOKED.** ``_support.scanned`` bounds that population two-sidedly
   against a computed denominator — the number of assignments to
   ``roster_source`` in the same function. An AST scan that matched nothing
   would otherwise report "all sources explained" over an empty set.
2. **IT CAN SEE.** Fault injection, three ways, each reverted and re-checked:
   a source the declaration does not name must fall to the catch-all and SAY
   the value; a missing spec path must produce the NO-FILE text and must not
   name a path; and a ``run_model`` whose declaration is stubbed out must be
   caught by the unconditional-print test rather than passing quietly.
3. **CONSTRUCTED INPUT, NOT AN OBSERVED ONE.** Every scenario here is built in
   the test. Nothing asserts a property of the tree that a future emit would
   silently satisfy — which matters especially because **no spec on disk today
   carries ``roster_source`` at all**, so the projected state is inert until the
   pending re-emit lands and an observed-input test would be vacuous now and
   would never say so.

**MUTATIONS RUN, 2026-09-14, and TWO OF THEM SURVIVED.** §4's honest name for
requirement 2 is mutation testing, so each assertion here was checked by
breaking the thing it guards and confirming the suite went red — and then green
again on revert, because a control that still passes after the repair it was
written to witness is worse than none. What survived is recorded because it is
the more useful half:

| mutation | caught by |
|---|---|
| the recorded path is never printed | path tests (2) |
| the path is RECOMPUTED instead of taken from the scenario | path tests (2) |
| `how` collapsed to one constant for every source | the derivation test |
| the projected branch names neither prior election by year | the derivation test |
| **every** `§K` citation removed from what the function prints | the derivation test |
| a branch on a `roster_source` the emit cannot produce | the population test |
| the `declared` branch removed | the population test |
| the declaration gated on `verbose` | the unconditional-print test |
| the declaration printed in every roster state | the negative-control test |
| the `NOT SCORED` admission removed | the scoring-admission test |
| the judgement file no longer named | 2 tests |
| ⚠️ *survived* — prose prepended to the projected `how` | nothing, correctly: the three explanations stayed distinct and the citations stayed present, so nothing this file claims was falsified. A weak mutation, not a blind test |
| ⚠️ *survived* — ONE of the two `§K1` mentions deleted | nothing. The string is redundant in the message, so deleting one occurrence changes nothing a reader loses. Deleting **all** of them is caught (row 5). Recorded because the first attempt at this mutation looked like a hole and was not |

⛔ **ASSERTS THE FACTS, NOT THE PROSE.** Every assertion here is that a value
the function was GIVEN is recoverable from what it returned, or that two
different inputs produce two different outputs. Nothing is pinned to a wording.

Run:
    ./.venv/bin/python tests/test_projected_roster_declaration.py
    ./.venv/bin/python -m pytest tests/test_projected_roster_declaration.py -q
"""

from __future__ import annotations

import ast
import contextlib
import inspect
import io
import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module, scanned, skip  # noqa: E402

import cityconfig  # noqa: E402
import montecarlo as M  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
UNHELD = "2026"
SPEC_PATH = "data/processed/somewhere/pools_9999.json"


class Sentinel(Exception):
    """Raised by a stub and by nothing else."""


def _target(year: str = UNHELD):
    cityconfig.use(CITY)
    return cityconfig.Target(city=cityconfig.load(CITY), year=year)


def _scenario(**over):
    base = {"_pools_roster_source": "projected",
            "_pools_spec_path": SPEC_PATH,
            "_pools_reach_source": "2021 ward ballot, carried forward unchanged"}
    base.update(over)
    return base


def _render(**over):
    return M._projected_roster_declaration(_target(), {"ANC", "DA", "MK"},
                                           _scenario(**over))


def _flat(text: str) -> str:
    """The message with its wrapping undone.

    The declaration is wrapped to a terminal width, so any fact longer than a
    line is split across two and a naive ``in`` test on it fails for a reason
    that has nothing to do with the fact being absent. Collapsing runs of
    whitespace is the whole of it.
    """
    return " ".join(text.split())


# --------------------------------------------------------------------------
# 0-1. the population, both directions, bounded
# --------------------------------------------------------------------------

def _sources_the_emit_can_produce() -> tuple[set[str], int]:
    """Every literal ``pools.resolve_roster`` assigns to ``roster_source``.

    Read from the AST of the live function, so a fourth state added there
    lands in this population without anyone editing this file — which is the
    only way a register→code check stays true.

    Returns the distinct literals and the number of assignments, so the caller
    has a denominator computed from the tree rather than a typed one.
    """
    tree = ast.parse(textwrap.dedent(inspect.getsource(pools.resolve_roster)))
    values, assignments = set(), 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if isinstance(tgt, ast.Name) and tgt.id == "roster_source":
                assignments += 1
                if isinstance(node.value, ast.Constant) and isinstance(
                        node.value.value, str):
                    values.add(node.value.value)
    return values, assignments


def _sources_the_declaration_names() -> set[str]:
    """Every literal ``_projected_roster_declaration`` compares ``source`` to."""
    tree = ast.parse(textwrap.dedent(
        inspect.getsource(M._projected_roster_declaration)))
    named = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) \
                and node.left.id == "source":
            for c in node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    named.add(c.value)
    return named


def test_every_roster_source_the_emit_can_produce_is_explained():
    """§4 PART 0 — BOTH DIRECTIONS, and part 1's two-sided bound.

    A declaration that explains two of three sources leaves the third printing
    a bare value with no derivation; a declaration that names a source the emit
    cannot produce is a register entry for a lever that was deleted, which is
    the failure §4 calls the worst record of the four. So: set equality.
    """
    produced, assignments = _sources_the_emit_can_produce()
    scanned(produced, of=assignments, low=0.2, high=1.0,
            what="distinct roster_source literals in pools.resolve_roster",
            denominator="assignments to roster_source in that function")
    named = _sources_the_declaration_names()
    assert produced == named, (
        f"the roster sources `pools.resolve_roster` can produce are "
        f"{sorted(produced)}, and `montecarlo._projected_roster_declaration` "
        f"branches on {sorted(named)}.\n"
        f"  only the emit can produce: {sorted(produced - named)} — these "
        f"print with no derivation, which is the state this declaration "
        f"exists to end.\n"
        f"  only the declaration names: {sorted(named - produced)} — these are "
        f"register entries for a state the code cannot reach; a reader takes "
        f"them for behaviour that exists.")


# --------------------------------------------------------------------------
# 2. the four facts, and the fault injections that prove the detector sees
# --------------------------------------------------------------------------

def test_the_declaration_carries_the_path_that_was_actually_read():
    """WHERE THE FILE IS — the owner's first question, and the one the old
    message answered with a bare filename.

    Asserts the value the scenario was GIVEN comes back, not that some path
    appears: a declaration that recomputed the path would pass an "is there a
    path" check and print a file the run never opened.
    """
    assert SPEC_PATH in _flat(_render()), (
        f"the spec path the run recorded ({SPEC_PATH!r}) is not in the "
        f"declaration, so a reader told the roster is a guess cannot open the "
        f"guess.\n\n{_render()}")


def test_no_spec_path_says_so_instead_of_naming_a_file():
    """FAULT INJECTION, and the direction that matters more.

    A caller supplying ``scenario['pools']`` directly opens no spec, so there
    is no path. Printing one anyway — recomputed from the city and the year —
    would name a file the run never read, which is the same class as an empty
    roster meaning "drop nobody": an answer that looks like evidence.

    Then reverted, and the healthy case re-checked, so a test that broke the
    mechanism cannot leave it broken.
    """
    without = _flat(_render(_pools_spec_path=None))
    assert ".json" not in without, (
        f"with no spec path recorded, the declaration still names a `.json` "
        f"file. It is claiming a file was read when none was.\n\n{without}")
    assert "NO FILE" in without, (
        f"with no spec path recorded, the declaration neither names a file nor "
        f"says it has none — so the `file` line is simply blank and a reader "
        f"cannot tell which happened.\n\n{without}")
    assert SPEC_PATH in _flat(_render()), (
        "after the no-path case, a well-formed scenario no longer carries its "
        "path into the declaration. Something in the injection above left "
        "state behind.")


def test_the_derivation_differs_by_source_and_cites_where_the_numbers_live():
    """HOW IT WAS DERIVED — the owner's "based on x, y, z".

    Two claims, and the first is the one a constant string would pass:

    * the three reachable sources must produce three DIFFERENT explanations. A
      declaration that printed one generic sentence would satisfy any "does it
      mention the derivation" check ever written.
    * the projected branch must name both floors by their JUDGEMENT-CALLS
      section AND both prior sources by the year the target resolves them to.
      ⛔ It must NOT restate the floors' measured costs: `CLAUDE.md` rule zero
      — a number copied where nobody re-measures it is a defect. So this
      asserts the POINTER is present, never a figure.
    """
    target = _target()
    hows = {}
    for source in ("projected", "declared", "published"):
        hows[source] = _flat(_render(_pools_roster_source=source))
    assert len({h for h in hows.values()}) == 3, (
        "two roster sources produced identical declarations, so the "
        "derivation is not actually a function of the source:\n"
        + "\n\n".join(f"{k}:\n{v}" for k, v in hows.items()))

    projected = hows["projected"]
    for token in ("§K1", "§K2", "JUDGEMENT-CALLS"):
        assert token in projected, (
            f"the projected derivation does not cite {token}, so the floors "
            f"that shape it are unattributed and a reader cannot find the "
            f"evidence for them.\n\n{projected}")
    for year in (target.previous_lge, target.previous_npe):
        assert year in projected, (
            f"the projected derivation does not name {year}, one of the two "
            f"elections it is built from. 'derived from the preceding "
            f"elections' is not a derivation a reader can check.\n\n{projected}")

    declared = hows["declared"]
    assert f"{CITY}-{UNHELD}.toml" in declared, (
        f"the declared derivation does not name the judgement file the list "
        f"was typed into, so the reader cannot go and check the list.\n\n"
        f"{declared}")


def test_an_unknown_source_is_reported_rather_than_explained_away():
    """FAULT INJECTION on the population itself.

    ``_sources_the_declaration_names`` above proves the branches match the
    emit TODAY. This proves what happens when they stop matching: a value the
    declaration does not name must reach the reader intact, so the mismatch is
    visible on the night rather than only in this test.
    """
    odd = _flat(_render(_pools_roster_source="ratified-by-committee"))
    assert "ratified-by-committee" in odd, (
        f"an unrecognised roster_source vanished from the declaration, so a "
        f"spec written by something other than `pools.resolve_roster` reads "
        f"exactly like one that was.\n\n{odd}")
    assert "projected" in _flat(_render()), (
        "after the unknown-source case, the known source no longer renders. "
        "Something in the injection above left state behind.")


def test_the_declaration_says_what_ends_the_condition_and_that_it_is_not_the_list():
    """WHAT ENDS IT — and the correction the owner's own framing needs.

    The condition ends with the target's own RESULT file, which arrives after
    polling day. The declaration must name the mechanism that decides it, so a
    reader can check the claim rather than take it: `CALENDAR[<year>].results`.
    It must also name the judgement file, because that is the one action
    available BEFORE the election.
    """
    for source in ("projected", "declared", "published"):
        text = _flat(_render(_pools_roster_source=source))
        assert "CALENDAR" in text and "results" in text, (
            f"the {source!r} declaration does not name the thing that decides "
            f"the state (`cityconfig.CALENDAR[year].results`), so its claim "
            f"about what ends the condition cannot be checked.\n\n{text}")
        assert f"{CITY}-{UNHELD}.toml" in text, (
            f"the {source!r} declaration does not name the judgement file, "
            f"which is the only action available before polling day.\n\n{text}")


def test_the_declaration_admits_that_nothing_scores_the_projection():
    """THE MISSING CAPABILITY, named rather than implied.

    Nothing compares a projected roster with the ballot that eventually
    arrives. Until something does, the honest thing the model can do is say
    so — an unscored projection that does not announce itself as unscored
    reads like one somebody is checking.

    ⚠️ **THIS TEST IS A TRIPWIRE FOR ITS OWN OBSOLESCENCE.** When the scorer
    described in MACHINERY.md is built, this assertion is the thing that
    should fail, and its failure is the reminder to change the sentence.
    """
    text = _flat(_render())
    assert "NOT SCORED" in text, (
        f"the declaration no longer says the projection is unscored. If a "
        f"scorer now exists, replace this assertion with one that names it; "
        f"if it does not, restore the admission.\n\n{text}")


# --------------------------------------------------------------------------
# the call site: printed UNCONDITIONALLY, and only in the projected state
# --------------------------------------------------------------------------

def _run_capturing(state: str, roster: set[str]) -> str:
    """Run ``run_model`` far enough to print, with everything after it stubbed.

    The declaration is emitted between ``roster_for_target`` returning and the
    off-ballot drop running, so stubbing ``levels.absent_from_ballot`` to raise
    stops the run immediately after the print. Nothing is written: ``run_model``
    writes only when given a ``run_dir``, and it is given none.
    """
    import levels
    spec = cityconfig.load(CITY).processed / f"pools_{UNHELD}.json"
    if not spec.exists():
        skip(f"no pool spec at {spec}")
    target = cityconfig.use_target(UNHELD)
    real_roster, real_absent = M.roster_for_target, levels.absent_from_ballot

    class _Args:
        config = None
        set = None
        draws = 10
        seed = None

    buf = io.StringIO()
    try:
        M.roster_for_target = lambda _t, _s=None: (set(roster), state)
        levels.absent_from_ballot = lambda *a, **k: (_ for _ in ()).throw(
            Sentinel("reached the off-ballot drop"))
        with contextlib.redirect_stdout(buf):
            try:
                M.run_model(target, M.load_scenario(_Args()), verbose=False)
            except Sentinel:
                pass
    finally:
        M.roster_for_target, levels.absent_from_ballot = real_roster, real_absent
        cityconfig.use(CITY)
    return _flat(buf.getvalue())


def test_run_model_prints_the_declaration_without_verbose():
    """THE PROPERTY THE WHOLE THING RESTS ON.

    A perfect declaration behind ``if verbose:`` is a declaration the live
    forecast does not make — the published run is not verbose. So this runs
    the model with ``verbose=False`` and requires the text in stdout.

    ⚠️ It asserts a fact the stub SUPPLIED (the party count) is in the output,
    not that some warning appeared: a leftover unconditional print elsewhere
    would satisfy the weaker check.
    """
    out = _run_capturing("projected", {"ANC", "DA", "MK", "EFF"})
    assert "PROJECTED" in out and "4" in out, (
        f"`run_model(verbose=False)` did not announce a projected roster. The "
        f"live forecast is not verbose, so a declaration gated on it is a "
        f"declaration nobody sees.\n\n{out}")


def test_a_published_or_not_yet_held_roster_prints_no_such_warning():
    """THE OTHER DIRECTION, without which the test above passes on a print
    that fires always.

    ``not_yet_held`` and ``published`` are not assumptions about the ballot —
    the first knowingly drops nobody, the second reads the real result file —
    and a warning that cried assumption in all three states would be ignored
    in the one that matters.
    """
    for state, roster in (("not_yet_held", set()), ("published", {"ANC", "DA"})):
        out = _run_capturing(state, roster)
        assert "is PROJECTED, not published" not in out, (
            f"state {state!r} printed the projected-roster warning. A warning "
            f"that fires in every state carries no information.\n\n{out}")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
