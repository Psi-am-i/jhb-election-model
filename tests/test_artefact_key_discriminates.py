"""THE ARTEFACT KEY MUST DISCRIMINATE — POOLS-REEMIT-QUEUE entries 24 and 25.

**The claim: every input the key hashes changes an emitted number, and every
input that changes an emitted number is hashed.** Both directions matter and
they fail differently — the forward direction failing is SILENT STALENESS
(entry 24), the reverse failing is CRY-WOLF (entry 25) — and cry-wolf is the
worse of the two here, because it trains the reader to ignore the field.

**Entry 24.** ``_config_sha``'s parameter selected a DIRECTORY and was then
thrown away. Verified on a constructed two-file directory:
``_config_sha(alpha.toml)``, ``_config_sha(beta.toml)`` **and
``_config_sha(does_not_exist.toml)`` all returned one hash** — the argument was
inert, and a path not on disk was not noticed. ⚠️ The directory scan is
DELIBERATE and replaced a single named path because THAT was a population bug;
the lie was the signature. And the zero-file case returned ``_sha``'s literal
string ``"missing"`` — a FIXED STRING in a hash field, so with ``config/``
emptied every spec agreed with every other and staleness became undetectable
rather than loud — against ``_cities_sha``'s ``sha256("")[:16]``. Two different
silent sentinels for one situation.

**Entry 25.** ``THETA_WINDOW`` sat in ``_gates_sha`` and ``pools.py`` read it
nowhere else, so setting it marked every spec STALE while changing nothing
emitted. ⛔ ``HELD_BACK_OFF`` and ``HELD_BACK_n`` MUST STAY: ``HELD_BACK_OFF=1``
genuinely changes what ``_npe_citywide_state`` and ``ward_totals`` may read, so
for those the staleness is TRUE and wanted. **Deleting the whole dict would
satisfy the ``THETA_WINDOW`` row and destroy the guard the other two provide**,
which is how this gets half-repaired — so both directions are asserted here and
each is reverted.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS.** The population is every component
   of ``artefact_key`` and every environment gate ``_gates_sha`` hashes, DERIVED
   — the first by calling ``artefact_key`` and reading its field names, the
   second by scanning ``_gates_sha``'s own syntax tree — never from a list typed
   here. ``stale_reason`` already carries the scar of a set typed in two places.
1. **IT LOOKED.** Every key field is asserted NON-CONSTANT: something in its
   declared population moves it. A field nothing moves is not being checked by
   anything. Bounded two-sidedly — under each perturbation the set of fields
   that move must be EXACTLY the expected one, not "at least one".
2. **IT CAN SEE — AND GOES QUIET WHEN REVERTED.** Constructed directories,
   constructed judgement files, and both environment gates, each reverted.
3. **CONSTRUCTED INPUT, NOT OBSERVED.** The config directories are temporary and
   the spec the staleness rows are scored against is BUILT, not read off disk.
   ⚠️ A second, on-disk pass is offered and **skips loudly** when the tree is not
   clean, rather than quietly becoming vacuous — which is what it would be today,
   with this batch un-emitted.

⚠️ **What this guard cannot prove.** It cannot prove ``THETA_WINDOW`` changes no
emitted number — only that ``pools.py`` never reads it and that ``pools``'s sole
use of ``levels`` is ``_held_back``. That is a STATIC argument and the strongest
one available without an emit, so it is asserted as a tripwire: the set of
``levels`` attributes ``pools`` touches, scanned from the source, must equal
``{_held_back}``. The day it does not, the argument must be re-derived.

Run:
    ./.venv/bin/python tests/test_artefact_key_discriminates.py
    ./.venv/bin/python -m pytest tests/test_artefact_key_discriminates.py -q
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module, skip  # noqa: E402

import cityconfig  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
TARGET = "2026"

# The gates `_gates_sha` is SUPPOSED to hash: those that change what THIS module
# reads. Asserted against the dict scanned out of the function, both ways.
EXPECTED_GATES = {"HELD_BACK_OFF", "HELD_BACK_n"}

# The only `levels` attribute `pools` may touch, which is what makes the static
# argument about THETA_WINDOW hold.
EXPECTED_LEVELS_ATTRS = {"_held_back"}


def _city_and_target():
    city = cityconfig.load(CITY)
    return city, cityconfig.Target(city=city, year=TARGET)


def _key(**kwargs) -> dict:
    city, target = _city_and_target()
    return pools.artefact_key(city, target, **kwargs)


def _moved(before: dict, after: dict) -> set[str]:
    assert set(before) == set(after), (
        f"the key's SHAPE moved: {sorted(set(before) ^ set(after))}")
    return {k for k in before if before[k] != after[k]}


@contextlib.contextmanager
def _env(name: str, value: str | None):
    """Set or clear one environment variable, and put it back."""
    original = os.environ.get(name)
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value
    try:
        yield
    finally:
        if original is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = original


def _two_file_dir() -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "alpha.toml").write_text("a = 1\n")
    (root / "beta.toml").write_text("b = 2\n")
    return root


# --------------------------------------------------------------------------
# 0. the population, derived from the code
# --------------------------------------------------------------------------

def _gates_hashed_in_source() -> set[str]:
    """The keys of the dict `_gates_sha` hashes, read out of its syntax tree.

    Not from a list here, and not by calling the function — the digest tells you
    nothing about what went into it. This is the register->code direction: a
    gate added to that dict with no case below fails.
    """
    tree = ast.parse(Path(pools.__file__).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_gates_sha":
            for inner in ast.walk(node):
                if isinstance(inner, ast.Dict) and inner.keys:
                    return {k.value for k in inner.keys
                            if isinstance(k, ast.Constant)}
    raise AssertionError(
        "no dict literal found inside `_gates_sha`. The function this guard "
        "scans has been restructured and the scan is now blind.")


def _code_mentions(name: str) -> bool:
    """Does `pools.py` mention this name in CODE, ignoring prose?

    ⛔ NOT A `grep`. This file's docstrings discuss ``THETA_WINDOW`` at length —
    that is where the reason it was removed is recorded — so a substring search
    over the source would report it as present for ever. The test is the same
    one ``_code_sha`` makes: strip the docstrings, and ask what the syntax tree
    still contains. Comments never reach the tree at all.
    """
    tree = ast.parse(Path(pools.__file__).read_text())
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = getattr(node, "body", None)
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            body.pop(0)
    return name in ast.dump(tree)


def _levels_attrs_in_source() -> set[str]:
    tree = ast.parse(Path(pools.__file__).read_text())
    return {n.attr for n in ast.walk(tree)
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)
            and n.value.id in ("levels", "_levels")}


def test_every_field_of_the_key_has_a_case_in_this_file():
    """BOTH DIRECTIONS OVER THE KEY'S OWN FIELD NAMES.

    The population is whatever ``artefact_key`` returns — derived by calling it,
    never typed. A field added to the key and not given a case here fails; a case
    here for a field the key no longer produces fails too.
    """
    produced = set(_key())
    covered = set(CASES) | pools._IDENTITY_FIELDS | {"schema"}
    assert produced == covered, (
        f"`artefact_key` produces {sorted(produced)} and this file covers "
        f"{sorted(covered)}.\n"
        f"UNCOVERED ({sorted(produced - covered)}): a field recorded into every "
        f"spec with nothing asserting that anything moves it — which is the "
        f"silent-staleness hole the key exists to close, sitting inside the "
        f"key.\n"
        f"STALE ({sorted(covered - produced)}): a case for a field that no "
        f"longer exists.")


def test_only_gates_this_module_reads_are_hashed():
    """⛔ THE CRY-WOLF DIRECTION — entry 25, and the half nobody checks.

    A gate in this dict that ``pools.py`` does not read marks every spec stale
    for nothing. ``THETA_WINDOW`` was exactly that: one line, in this dict, read
    nowhere else in the module, and ``pools``'s only use of ``levels`` is
    ``_held_back`` — so it could not reach an emitted number through the import
    either. Its real consumers are ``levels``, ``theta_residual``, ``freeze`` and
    ``montecarlo``.

    The static argument is asserted as a TRIPWIRE, not restated as prose: the
    set of ``levels`` attributes this module touches must stay ``{_held_back}``,
    or the argument has to be re-derived.
    """
    hashed = _gates_hashed_in_source()
    assert hashed == EXPECTED_GATES, (
        f"`_gates_sha` hashes {sorted(hashed)}; the gates that change what "
        f"`pools.py` reads are {sorted(EXPECTED_GATES)}.\n"
        f"EXTRA ({sorted(hashed - EXPECTED_GATES)}): cry-wolf — every spec goes "
        f"stale when that variable is set, on a tree where nothing is stale.\n"
        f"MISSING ({sorted(EXPECTED_GATES - hashed)}): silent staleness — a "
        f"diagnostic run can now emit a spec that reports itself current for "
        f"ever after.")

    assert not _code_mentions("THETA_WINDOW"), (
        "`THETA_WINDOW` is back in `pools.py`. It is read by `levels`, "
        "`theta_residual`, `freeze` and `montecarlo`, and by nothing here; "
        "hashing it stamps a false staleness into the trace of the "
        "HELD_BACK_OFF=1 THETA_WINDOW=2 arm.")
    attrs = _levels_attrs_in_source()
    assert attrs == EXPECTED_LEVELS_ATTRS, (
        f"`pools` now touches `levels.{sorted(attrs)}` rather than "
        f"{sorted(EXPECTED_LEVELS_ATTRS)}. The argument that an environment "
        f"gate on `levels` cannot reach an emitted number through this module "
        f"rested on that set, and it must be re-derived before this test's "
        f"expectation is edited.")


# --------------------------------------------------------------------------
# 1 + 2. every field moves, and only the expected one
# --------------------------------------------------------------------------

def _case_config_sha():
    """Two different files in ONE directory must hash differently."""
    root = _two_file_dir()
    before = _key(config_path=root / "alpha.toml")
    after = _key(config_path=root / "beta.toml")
    return before, after


def _case_cities_sha():
    """A ninth city is a PANEL input: it moves the band of every existing spec."""
    root = Path(tempfile.mkdtemp())
    (root / "one.toml").write_text("x = 1\n")
    # Resolved BEFORE the patch: `cityconfig.load` reads that directory, so a
    # city looked up while it is redirected does not exist.
    city, target = _city_and_target()
    real = cityconfig.CITIES_DIR
    cityconfig.CITIES_DIR = root
    try:
        before = pools.artefact_key(city, target)
        (root / "two.toml").write_text("y = 2\n")
        after = pools.artefact_key(city, target)
    finally:
        cityconfig.CITIES_DIR = real
    return before, after


def _case_deps_sha():
    """Every named dependency contributes, so dropping one moves the digest."""
    real = pools._EMIT_DEPENDENCIES
    before = _key()
    pools._EMIT_DEPENDENCIES = real[:-1]
    try:
        after = _key()
    finally:
        pools._EMIT_DEPENDENCIES = real
    return before, after


def _case_judgements_sha():
    """A hand edit to the judgement file — the input a human is likeliest to
    change, and the one that was in no hash at all."""
    tmp = Path(tempfile.mkdtemp()) / f"{CITY}-{TARGET}.toml"
    tmp.write_text('[party.NEWCO]\nsupport = 0.10\n')
    real = pools.lineage_path
    pools.lineage_path = lambda city, target: tmp
    try:
        before = _key()
        tmp.write_text('[party.NEWCO]\nsupport = 0.20\n')
        after = _key()
    finally:
        pools.lineage_path = real
    return before, after


def _case_gates_sha():
    """`HELD_BACK_OFF=1` genuinely changes what may be read — it MUST move."""
    with _env("HELD_BACK_OFF", None):
        before = _key()
    with _env("HELD_BACK_OFF", "1"):
        after = _key()
    return before, after


def _case_pools_sha():
    """Tied to `_code_sha`, whose non-constancy is proved on its own below.

    ⚠️ STATED RATHER THAN FAKED. Moving this field means editing `src/pools.py`
    mid-run, which `MEMORY.md`'s *never measure a moving tree* forbids and which
    would make every other assertion in this process meaningless. So the field
    is tied to its producer by equality, and the producer is perturbed directly.
    """
    return None, None


CASES = {
    "config_sha": _case_config_sha,
    "cities_sha": _case_cities_sha,
    "deps_sha": _case_deps_sha,
    "judgements_sha": _case_judgements_sha,
    "gates_sha": _case_gates_sha,
    "pools_sha": _case_pools_sha,
}


def test_each_key_field_moves_and_moves_alone():
    """IT LOOKED, TWO-SIDEDLY.

    For every field, a perturbation of ITS OWN declared population moves it —
    and moves nothing else. "At least one field moved" is the one-sided version
    and it passes for a key where two fields are accidentally the same input.
    """
    baseline = _key()
    for field, build in sorted(CASES.items()):
        before, after = build()
        if before is None:
            continue                  # see `_case_pools_sha`
        moved = _moved(before, after)
        assert moved == {field}, (
            f"perturbing {field}'s own population moved {sorted(moved)}.\n"
            f"If it moved NOTHING the field is not being checked by anything "
            f"and a spec can go stale under it in silence. If it moved MORE, "
            f"two fields are reading one input and the key cannot say which "
            f"changed.")
        # AND IT GOES QUIET. Every builder restores what it patched, so the
        # real key must be back where it started before the next case runs —
        # otherwise the case after this one is measuring the leak.
        assert _key() == baseline, (
            f"after the {field} case the real artefact key is "
            f"{sorted(_moved(baseline, _key()))} away from where it started. "
            f"A perturbation that does not revert makes every later assertion "
            f"in this file a measurement of the leak.")


def test_the_pools_hash_is_the_code_hash_of_this_file():
    """The tie `_case_pools_sha` rests on, and the property that makes the hash
    usable at all.

    Asserted on constructed files: a docstring edit must NOT move the digest —
    `CLAUDE.md` requires the documentation to change in the same commit as the
    model, so a hash that fired on prose would fire every time and be ignored —
    and a change to what the code COMPUTES must move it.
    """
    assert _key()["pools_sha"] == pools._code_sha(Path(pools.__file__)), (
        "`artefact_key`'s pools_sha is no longer `_code_sha` of this module, so "
        "perturbing `_code_sha` says nothing about the field.")
    root = Path(tempfile.mkdtemp())
    a, b, c = root / "a.py", root / "b.py", root / "c.py"
    a.write_text('"""One."""\n\n\ndef f():\n    return 1\n')
    b.write_text('"""Another docstring entirely."""\n\n\ndef f():\n    # and a comment\n    return 1\n')
    c.write_text('"""One."""\n\n\ndef f():\n    return 2\n')
    assert pools._code_sha(a) == pools._code_sha(b), (
        "a docstring-and-comment-only change moved `_code_sha`. A staleness "
        "warning that fires when someone improves a comment is one everybody "
        "learns to ignore — and then the one that matters is ignored too.")
    assert pools._code_sha(a) != pools._code_sha(c), (
        "a change to what the code COMPUTES did not move `_code_sha`, so the "
        "field cannot see the thing it exists to see.")


# --------------------------------------------------------------------------
# entry 24's own rows
# --------------------------------------------------------------------------

def test_two_configs_in_one_directory_do_not_share_a_hash():
    """ENTRY 24, and the row that was the defect.

    ⚠️ The directory scan stays: editing a SIBLING must still move the hash, or
    the repair has reverted to hashing one named file — the population bug the
    scan replaced.
    """
    root = _two_file_dir()
    alpha, beta = root / "alpha.toml", root / "beta.toml"
    a0, b0 = pools._config_sha(alpha), pools._config_sha(beta)
    assert a0 != b0, (
        f"two different files in one directory hash identically ({a0}), so "
        f"`artefact_key(..., config_path=X)` cannot tell two configs apart.")

    beta.write_text("b = 3\n")
    assert pools._config_sha(alpha) != a0, (
        "editing a sibling did not move the named file's hash, so the "
        "population has shrunk back to a single path — which is the bug the "
        "directory scan was introduced to fix.")
    beta.write_text("b = 2\n")
    assert pools._config_sha(alpha) == a0, (
        "reverting the sibling did not restore the hash.")


def test_a_config_path_that_is_not_on_disk_is_refused():
    """A hash of a file that is not there is a claim about nothing.

    It used to be ``_sha``'s literal ``"missing"``, which is a fixed string in a
    hash field, so it did not merely fail to notice — it made every such spec
    agree with every other.
    """
    root = _two_file_dir()
    try:
        got = pools._config_sha(root / "does_not_exist.toml")
    except SystemExit:
        pass
    else:
        raise AssertionError(
            f"a config path that is not on disk hashed to {got!r} instead of "
            f"refusing. If that value is shared with any other absent path, "
            f"staleness is undetectable rather than loud.")


def test_the_zero_file_case_is_one_stated_outcome_shared_by_both_scans():
    """``config_sha`` and ``cities_sha`` had TWO DIFFERENT SILENT SENTINELS for
    one situation — ``"missing"`` against ``sha256("")[:16]``. Neither said what
    had happened. Now both go through one definition and both refuse.
    """
    empty = Path(tempfile.mkdtemp())
    outcomes = {}
    for label, call in (
            ("config_sha", lambda: pools._config_sha(empty / "nothing.toml")),
            ("cities_sha", lambda: pools._toml_population(empty, "cities_sha")),
    ):
        try:
            outcomes[label] = ("returned", call())
        except SystemExit as refusal:
            outcomes[label] = ("refused", type(refusal).__name__)
    assert outcomes["config_sha"][0] == outcomes["cities_sha"][0] == "refused", (
        f"the zero-file case gave {outcomes}. A silent sentinel here is worse "
        f"than a refusal in the specific way this key cannot afford: "
        f"`sha256('')` reads like a hash of something, and a fixed string makes "
        f"every spec agree with every other.")
    assert hashlib.sha256(b"").hexdigest()[:16] not in {
        v for _kind, v in outcomes.values() if isinstance(v, str)}, (
        "the empty-population hash is still being returned somewhere")


# --------------------------------------------------------------------------
# entry 25's own rows — BOTH, or the repair is half made
# --------------------------------------------------------------------------

def _constructed_spec() -> dict:
    """A spec whose key is the key the code produces RIGHT NOW.

    ⛔ CONSTRUCTED, NOT READ OFF DISK. The on-disk specs are an OBSERVED premise
    — they are stale by construction while a `pools.py` batch sits un-emitted —
    so a test written against them expires the moment the tree is legitimately
    dirty, which is most of the time a change is being made. This spec is clean
    by construction and stays that way.
    """
    return {"artefact_key": dict(_key())}


def test_theta_window_no_longer_marks_a_clean_spec_stale():
    """ENTRY 25, the cry-wolf direction."""
    city, target = _city_and_target()
    spec = _constructed_spec()
    assert pools.stale_reason(spec, city, target) is None, (
        "the constructed spec is stale against the key that built it, so this "
        "test cannot see its own subject.")
    with _env("THETA_WINDOW", "2"):
        during = pools.stale_reason(spec, city, target)
    assert during is None, (
        f"setting THETA_WINDOW marked a clean spec STALE: {during!r}. "
        f"`pools.py` does not read it, so the staleness is false — and a "
        f"staleness field that fires on a variable that changes nothing is one "
        f"the reader learns to ignore.")
    assert pools.stale_reason(spec, city, target) is None, (
        "the environment was not restored")


def test_held_back_off_still_marks_a_clean_spec_stale():
    """⛔ THE OTHER HALF, AND THE REASON DELETING THE DICT IS NOT THE FIX.

    ``HELD_BACK_OFF=1`` genuinely changes what ``_npe_citywide_state`` and
    ``ward_totals`` may read, so a spec emitted during such a run MUST report
    itself stale. Taking only the test above and deleting ``_gates_sha`` would
    satisfy it and destroy this.
    """
    city, target = _city_and_target()
    spec = _constructed_spec()
    with _env("HELD_BACK_OFF", "1"):
        during = pools.stale_reason(spec, city, target)
    assert during is not None, (
        "a spec emitted with the HELD_BACK quarantine LIFTED reports itself "
        "current. That is the silent staleness `_gates_sha` exists to close, "
        "arriving through the one door the code hash cannot watch.")
    assert pools.stale_reason(spec, city, target) is None, (
        "the environment was not restored")


def test_the_specs_on_disk_agree_with_the_constructed_one():
    """The same two rows against the REAL specs — and it SKIPS LOUDLY.

    ⚠️ This premise is observed: it holds only while every spec on disk is
    clean, and a `pools.py` batch waiting for its emit makes them all stale for
    a reason that is CORRECT. Skipping says so rather than letting the test
    quietly become vacuous, which is what a `if clean:` would do.
    """
    paths = sorted(Path("data/processed").rglob("pools_*.json"))
    if not paths:
        skip("no emitted specs on disk")

    loaded = []
    for path in paths:
        spec = json.loads(path.read_text())
        key = spec.get("artefact_key") or {}
        slug, year = key.get("city"), key.get("target")
        if not slug or not year:
            skip(f"{path} carries no artefact key, so staleness cannot be read "
                 f"off it at all")
        city = cityconfig.load(slug)
        loaded.append((path, spec, city, cityconfig.Target(city=city, year=year)))

    dirty = [(str(p), pools.stale_reason(s, c, t).split(";")[0])
             for p, s, c, t in loaded if pools.stale_reason(s, c, t)]
    if dirty:
        skip(f"{len(dirty)} of {len(loaded)} specs on disk are already stale — "
             f"EXPECTED while a pools.py batch is un-emitted, and it makes the "
             f"THETA_WINDOW row unreadable here. First: {dirty[0]}")

    with _env("THETA_WINDOW", "2"):
        stale = [str(p) for p, s, c, t in loaded
                 if pools.stale_reason(s, c, t) is not None]
    assert not stale, (
        f"THETA_WINDOW=2 marked {len(stale)} of {len(loaded)} emitted specs "
        f"stale, on a tree where nothing is: {stale[:3]}")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
