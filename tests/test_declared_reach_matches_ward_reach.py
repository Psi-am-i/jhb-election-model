"""THERE IS ONE DEFINITION OF REACH — POOLS-REEMIT-QUEUE entry 23.

**The claim: there is one definition of reach, and the declared path computes
it.** Not an absence claim but an AGREEMENT claim, which is easier to test — and
which the comment above ``declared_roster``'s derivation already asserted in
prose. The reason this file exists is that **the comment was false while it read
as verified**: it said the two are *"derived the same way … so the two
definitions of 'reach' cannot drift"*, and they already had.

``declared_roster`` built its denominator from ``{w for ws in wards.values() for
w in ws}`` — the union over **only the parties typed in so far** — while
``_ward_reach`` builds it from every row of the whole ward ballot. One entrant
declared on **20 of Johannesburg's 135 wards scored 1.0 against a true
0.1481**, 6.75x.

Three things follow and the second is what makes it a defect rather than a wrong
number:

* it flips ``comparators``' ``abs(r - reach) < 0.25`` bucket and takes
  ``arrival_group_spec``'s maximum split weight;
* **reach was not a property of the party at all.** Declare a second party on the
  other 115 wards and the first party's reach falls 1.0 -> 0.1481 with nothing
  about its own declaration changed. The value was a function of how far through
  the paste the typist had got — maximal at the FIRST party entered, shrinking
  as the list grows, which is the opposite of the direction anyone would check;
* **it is indistinguishable from a correct value.** ``_ward_reach('JHB','2021')``
  returns exactly 1.0 for 15 of its 55 parties, so a 20-ward party at 1.0 looks
  like every genuinely city-wide party in the record.

WHAT THIS FILE HAS TO PROVE, per ``CLAUDE.md`` §4:

0. **THE RIGHT POPULATION, BOTH DIRECTIONS — AND ⛔ THIS ONE WAS OVERCLAIMED
   UNTIL 2026-09-14, WHICH IS THE CLASS OF DEFECT THE PARAGRAPH IS ABOUT.** It
   said the population was *"every PRODUCER of a reach value … a third producer
   added later must fail this"*. It was not, and one did not: the scan matched a
   ``Div`` whose **both operands are literal ``len()`` calls**, and a genuine
   second definition of reach that bound its two counts to names first was added
   to ``pools.py`` and **this module stayed green, 6 passed 0 failed**. It also
   failed the other way, turning red for any unrelated ``len(a)/len(b)``
   anywhere in the module. The scan now catches the bound spelling as well, and
   the claim is cut to what a syntax scan can carry: **every ratio of counts in
   ``pools.py`` is classified** — a reach, which needs a case here, or a line in
   ``NOT_A_REACH`` saying what it is instead. A reach computed some other way
   (``sum(1 for …)/n``, a counting helper, another module) is invisible to it,
   and the registers are maintained by hand. Stated, not claimed away; see
   :func:`_count_ratios_in_source`.
1. **IT LOOKED.** The denominators are asserted to be the SAME QUANTITY, not
   merely to match on one example: for a declaration covering the whole ballot,
   ``declared_roster``'s reach equals ``_ward_reach``'s for EVERY party, and the
   shared denominator equals the city's ward count from ``vd_map``. The number of
   parties compared is bounded two-sidedly against
   ``len(contesting_parties(city, year))``.
2. **IT CAN SEE — AND GOES QUIET WHEN REVERTED.** The three constructed cases
   that found the defect. ⛔ The second is load-bearing and is the one a naive
   fix passes by accident: dividing by a ``len(seen)`` computed over a FULLER
   paste still makes reach depend on who else was typed. Only a denominator
   taken from the CITY makes it a property of the party, so the assertion is
   INVARIANCE under adding and removing other parties — the single-case equality
   is just one instance of it.
3. **CONSTRUCTED INPUT, NOT OBSERVED.** Only the lineage read is patched, so the
   real ``declared_roster`` body executes; nothing is written into
   ``judgements/``, which is tracked and shared. The derivation is guarded by
   ``if wards:``, so this file asserts it was REACHED — a ``parties``-only
   fixture would otherwise pass every test here by never running the code.

⚠️ **What this guard cannot prove.** It tests the value, not every consumer.
That a wrong reach changes what the consumers do is asserted separately, by
feeding both values through ``arrival_group_spec`` — otherwise the reach could be
repaired and a consumer still read a stale copy.

Run:
    ./.venv/bin/python tests/test_declared_reach_matches_ward_reach.py
    ./.venv/bin/python -m pytest tests/test_declared_reach_matches_ward_reach.py -q
"""

from __future__ import annotations

import ast
import contextlib
import io
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module, scanned, skip  # noqa: E402

import cityconfig  # noqa: E402
import parties as P  # noqa: E402
import pools  # noqa: E402

CITY = "joburg"
YEAR = "2021"          # a held election: a real ward ballot, so both producers run

# Every function in `pools.py` that COMPUTES a reach value. Not a list of call
# sites — the half of the scan below that must have a case in this file.
REACH_PRODUCERS = {"_ward_reach", "declared_roster"}

# ⛔ AND THE OTHER HALF, WHICH THE SCAN CANNOT TELL APART FROM A REACH. The scan
# finds a SPELLING — one count divided by another — and a mean, a coverage
# fraction or a hit rate has that spelling too. Such a function is not a defect
# and must not turn this file red on its own; it is a prompt to look, and the
# looking is recorded here with a reason. EMPTY TODAY, and that is a fact about
# `pools.py` (verified 2026-09-14: the two producers above are the only
# count-ratios in the module), not a permission to leave a new one unclassified.
NOT_A_REACH: dict[str, str] = {}

# How much of the ballot a whole-ballot declaration should reproduce. Two-sided
# against a computed denominator, per `_support.scanned`: a whole-ballot paste
# cannot name more parties than the ballot holds, and well below the floor the
# reader has stopped seeing rows. Measured 55 of 57 when this was written —
# the two missing are parties with no WARD candidate anywhere.
COMPARED_LO, COMPARED_HI = 0.70, 1.00


# --------------------------------------------------------------------------
# 0. the population of PRODUCERS, scanned from the code
# --------------------------------------------------------------------------

def _count_ratios_in_source() -> dict[str, list[str]]:
    """Every function in ``pools.py`` that divides one COUNT by another.

    ⛔ **WHAT THIS IS AND IS NOT, because the docstring here used to claim the
    semantic version and deliver the syntactic one.** It claimed *"a third reach
    producer added to `pools.py` fails here until it is given a case"*. It did
    not. The predicate was a ``Div`` whose **both operands are literal ``len()``
    calls**, and a genuine second definition of reach — same computation,
    disagreeing answer, differing only in binding ``n = len(seen)`` and
    ``k = len(w)`` before dividing — was added to `pools.py` on 2026-09-14 and
    **this module stayed fully green, 6 passed 0 failed**. It scanned a
    SPELLING and called it a population.

    Two changes followed, and only one of them is a widening:

    * **the spelling is widened by one hop**, to a name the same function binds
      to a ``len()`` call. That closes the demonstrated evasion, which is also
      the shape an ordinary refactor takes — hoist the two counts, then divide.
      Verified not to fire on anything new: run against the real `pools.py` it
      returns exactly the two producers, the same answer the old predicate gave.
    * **the claim is cut down to what a scan can actually support.** This is a
      TRIPWIRE over a family of spellings, not an enumeration of reach. A reach
      computed as ``sum(1 for …) / n``, through a counting helper, from a
      precomputed total, or in another module, is INVISIBLE to it. Nothing here
      can see those, and the register above is maintained by hand — which is the
      same one-directional weakness ``CLAUDE.md`` §5 records for
      ``test_standalone_modules``, stated rather than papered over.

    It also failed the other way: the old predicate turned this module red for
    any unrelated ``len(a) / len(b)`` anywhere in a six-thousand-line file, with
    a message accusing it of being an unguarded reach. Constructed and confirmed
    the same day — a ``len(composition) / len(pools_d)`` mean made the module
    fail. That is now a classification rather than a verdict: see
    ``NOT_A_REACH``.

    Returns ``{function name: [the ratio expressions found in it]}`` — the
    expressions so the failure message can show a reader what it caught rather
    than only where.
    """
    tree = ast.parse((Path(pools.__file__)).read_text())

    def is_len(node):
        return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "len")

    found: dict[str, list[str]] = {}
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # Names this function binds to a `len()` call, anywhere in its body.
        # Deliberately flow-INSENSITIVE: a name that is ever a count is treated
        # as a count, because the alternative is a dataflow analysis in a test.
        counts: set[str] = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Assign) and is_len(node.value):
                counts.update(tgt.id for tgt in node.targets
                              if isinstance(tgt, ast.Name))
            elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
                value, target = node.value, node.target
                if (value is not None and is_len(value)
                        and isinstance(target, ast.Name)):
                    counts.add(target.id)

        def is_count(node):
            return is_len(node) or (isinstance(node, ast.Name)
                                    and node.id in counts)

        for node in ast.walk(fn):
            if (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
                    and is_count(node.left) and is_count(node.right)):
                found.setdefault(fn.name, []).append(ast.unparse(node))
    return found


def test_every_count_ratio_in_pools_is_classified():
    """BOTH DIRECTIONS, AND THIS IS THE ONE THIS REPOSITORY KEEPS MISSING.

    code -> register: a ratio of counts added to ``pools.py`` fails here until
    somebody says which it is — a reach, which needs a case in this file, or
    something else, which needs a line in ``NOT_A_REACH`` saying why. register
    -> code: a name in either register that the module no longer contains fails
    too, so the guard cannot go on claiming to cover something that has moved.

    ⚠️ **THE CLAIM IS NARROWER THAN THE NAME OF THIS FILE, DELIBERATELY.** The
    old version of this test claimed to catch *any* third producer of reach and
    a constructed one walked past it (see ``_count_ratios_in_source``). What is
    asserted now is what a syntax scan can carry: every ratio-of-counts in
    ``pools.py`` is accounted for. A reach computed some other way is not
    covered by this test and is not claimed to be.
    """
    found = _count_ratios_in_source()
    classified = REACH_PRODUCERS | set(NOT_A_REACH)
    assert set(found) == classified, (
        f"`pools.py` divides one count by another in {sorted(found)}; this "
        f"file has cases for {sorted(REACH_PRODUCERS)} and records "
        f"{sorted(NOT_A_REACH)} as deliberately not reach.\n\n"
        f"UNCLASSIFIED in the code ({sorted(set(found) - classified)}): "
        + "; ".join(f"{name} -> {found[name]}"
                    for name in sorted(set(found) - classified))
        + f"\nDecide which it is. If it computes reach it needs a case here "
        f"asserting it agrees with `_ward_reach` — that is exactly how the "
        f"declared path came to disagree while a comment said it could not. If "
        f"it is a mean, a coverage fraction or a hit rate, add it to "
        f"`NOT_A_REACH` with the reason; this scan matches a SPELLING and "
        f"cannot tell them apart.\n"
        f"MISSING from the code ({sorted(classified - set(found))}): a register "
        f"entry watching a function that has been renamed, deleted, or "
        f"rewritten so its ratio is no longer a ratio of counts — in every case "
        f"this guard now covers less than its registers say.")
    assert found, (
        "the scan found no count-ratio anywhere in `pools.py`. `_ward_reach` "
        "computes one on its last line, so the scan has lost its input rather "
        "than passed.")
    for name in REACH_PRODUCERS | set(NOT_A_REACH):
        assert callable(getattr(pools, name, None)), (
            f"`pools.{name}` is not callable, so a register names something "
            f"this file cannot exercise.")


def test_the_scan_sees_a_count_ratio_however_it_is_spelled():
    """⛔ CAN IT SEE — on constructed source, and both spellings.

    The detector is run over a module written for the purpose rather than over
    ``pools.py``, because adding a second reach to ``src/`` to find out is not
    available to a test. Three cases, and the second is the one the previous
    predicate failed:

    1. the literal spelling ``len(a) / len(b)`` — what it always caught;
    2. ⛔ **the bound spelling**, ``n = len(a)`` … ``k = len(b)`` … ``k / n``.
       A real second definition of reach in exactly this shape was added to
       ``pools.py`` and the whole module stayed green;
    3. a ratio that is NOT of counts — ``len(a) / total`` — which must not be
       caught, or every average in the file becomes a reach.

    And it goes quiet again: the module with the violations removed returns
    nothing, so a pass above is not the scan having stopped working.
    """
    import tempfile as _tf

    def scan(src: str) -> dict[str, list[str]]:
        with _tf.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fake_pools.py"
            path.write_text(src)
            real = pools.__file__
            try:
                pools.__file__ = str(path)
                return _count_ratios_in_source()
            finally:
                pools.__file__ = real

    literal = "def a(x, y):\n    return len(x) / len(y)\n"
    assert sorted(scan(literal)) == ["a"], scan(literal)

    bound = ("def b(x, y):\n"
             "    n = len(y)\n"
             "    k = len(x)\n"
             "    return k / n\n")
    assert sorted(scan(bound)) == ["b"], (
        f"the bound spelling was not caught: {scan(bound)}. This is the "
        f"constructed second definition of reach that walked past the previous "
        f"predicate while this module reported 6 passed, 0 failed.")

    not_counts = "def c(x, total):\n    return len(x) / total\n"
    assert scan(not_counts) == {}, (
        f"a count over a non-count was caught: {scan(not_counts)}. Widening "
        f"until everything matches is not a guard; it is a permanent red.")

    # ...AND QUIET WHEN THE VIOLATIONS ARE REVERTED.
    assert scan("def d(x, y):\n    return sum(x) / sum(y)\n") == {}, (
        "the scan reports a count-ratio in a module that has none, so the "
        "cases above prove nothing about what it can tell apart.")


# --------------------------------------------------------------------------
# the constructed declaration
# --------------------------------------------------------------------------

@contextlib.contextmanager
def _declaration(body: str):
    """Run the real `declared_roster` against a constructed judgement file.

    Only `lineage_path` is redirected. ``judgements/`` is tracked and shared and
    is never written to from a test.
    """
    tmp = Path(tempfile.mkdtemp()) / f"{CITY}-{YEAR}.toml"
    tmp.write_text(body)
    real = pools.lineage_path
    pools.lineage_path = lambda city, target: tmp
    try:
        yield
    finally:
        pools.lineage_path = real


def _declare(body: str) -> tuple[dict, str]:
    city = cityconfig.load(CITY)
    target = cityconfig.Target(city=city, year=YEAR)
    buf = io.StringIO()
    with _declaration(body):
        with contextlib.redirect_stdout(buf):
            out = pools.declared_roster(city, target)
    return out, buf.getvalue()


def _ward_lists() -> dict[str, set[str]]:
    """Each party's wards at the real ballot, keyed as `_ward_reach` keys them.

    The ward LISTS only. The ratio is never recomputed here — that would make
    this file a second definition of the quantity it exists to keep singular.
    """
    from ingest_lge import read_municipality
    city = cityconfig.load(CITY)
    path = pools.metro_file(city.code, YEAR)
    if path is None:
        skip(f"no ward ballot on disk for {CITY} {YEAR}")
    out: dict[str, set[str]] = defaultdict(set)
    for row in read_municipality(path, city.code, "Ward"):
        ward = (row.get("Ward") or "").strip()
        if ward:
            out[P.canonical(row["sPartyName"])].add(ward)
    return dict(out)


def _toml_wards(wards: dict[str, set[str]]) -> str:
    lines = ["[roster.wards]"]
    for party, ws in sorted(wards.items()):
        body = ", ".join(f'"{w}"' for w in sorted(ws))
        lines.append(f'"{party}" = [{body}]')
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# 1. it looked — the denominators are the same quantity
# --------------------------------------------------------------------------

def test_a_whole_ballot_declaration_reproduces_ward_reach_exactly():
    """IT LOOKED, and the two definitions are asserted to AGREE, not to be close.

    A declaration listing every party's real wards must give every party the
    same reach ``_ward_reach`` gives it — which is only true if the denominators
    are the same quantity. Under the defect they coincide in this case alone
    (the paste IS the whole ballot), which is why the second and third tests
    below carry the weight; this one proves the repaired path has not broken the
    case that used to work.
    """
    city = cityconfig.load(CITY)
    truth = pools._ward_reach(city.code, YEAR)
    assert truth, f"`_ward_reach` returned nothing for {CITY} {YEAR}"
    wards = _ward_lists()
    assert set(wards) == set(truth), (
        f"the ward lists this test built cover {len(wards)} parties and "
        f"`_ward_reach` reports {len(truth)}. The two readers of the same file "
        f"disagree about who is on it, so any equality below would be an "
        f"accident.")
    # `_ward_reach` keys on `P.canonical`, and so does `declared_roster`. If
    # canonicalisation is not idempotent the keys cannot match and the
    # comparison would silently compare nothing.
    assert all(P.canonical(p) == p for p in truth), (
        "`P.canonical` is not idempotent on its own output, so the declared "
        "keys and `_ward_reach`'s keys are different spaces.")

    got, printed = _declare(_toml_wards(wards))
    reach = got["reach"]
    assert reach, (
        "the derivation did not run. It is guarded by `if wards:`, so a "
        "fixture with no [roster.wards] block passes every test in this file "
        "by never reaching the code.")

    assert set(reach) == set(truth), (
        f"the declared path produced reach for {len(reach)} parties and "
        f"`_ward_reach` for {len(truth)}.")
    worst = max(truth, key=lambda p: abs(reach[p] - truth[p]))
    assert all(abs(reach[p] - truth[p]) < 1e-12 for p in truth), (
        f"the two definitions of reach disagree; worst at {worst}: declared "
        f"{reach[worst]:.6f} against `_ward_reach`'s {truth[worst]:.6f}. There "
        f"is supposed to be ONE definition.")

    # The shared denominator IS the city's ward count.
    ward_of, _reg = pools.vd_map(city, YEAR)
    n_city = len(set(ward_of.values()))
    a_party = max(wards, key=lambda p: len(wards[p]))
    assert abs(reach[a_party] - len(wards[a_party]) / n_city) < 1e-12, (
        f"{a_party} holds {len(wards[a_party])} wards and the city has "
        f"{n_city}, but its declared reach is {reach[a_party]:.6f}. The "
        f"denominator is not the city's ward count.")
    assert not any("not wards of" in line for line in printed.splitlines()), (
        f"the whole-ballot declaration reported wards that are not the city's, "
        f"so the two id spaces have diverged:\n{printed}")

    scanned(len(reach), of=len(pools.contesting_parties(city, YEAR)),
            low=COMPARED_LO, high=COMPARED_HI,
            what="parties whose reach the two definitions were compared on",
            denominator=f"parties on the whole {YEAR} ballot")


# --------------------------------------------------------------------------
# 2. it can see — the three constructed cases
# --------------------------------------------------------------------------

def _city_wards() -> list[str]:
    city = cityconfig.load(CITY)
    return sorted(set(pools.vd_map(city, YEAR)[0].values()))


def test_a_partial_declaration_is_sized_against_the_city_not_the_paste():
    """CASE 1: one party on *k* of the city's *N* wards must give k/N."""
    wards = _city_wards()
    n, k = len(wards), 20
    assert n > k, f"{CITY} {YEAR} has only {n} wards"
    got, _ = _declare(_toml_wards({"NEWCO": set(wards[:k])}))
    assert abs(got["reach"]["NEWCO"] - k / n) < 1e-12, (
        f"a party declared on {k} of {CITY}'s {n} wards was given reach "
        f"{got['reach']['NEWCO']:.6f}, not {k / n:.6f}. Under the defect this "
        f"was 1.0 — indistinguishable from the 15 of 55 parties that "
        f"legitimately hold 1.0 in `_ward_reach`.")


def test_a_partys_reach_does_not_move_when_somebody_else_is_typed_in():
    """⛔ CASE 2, THE LOAD-BEARING ONE, AND THE ONE A NAIVE FIX PASSES.

    A repair that divides by a ``len(seen)`` computed over a FULLER paste still
    makes reach depend on who else was typed; it would satisfy case 1 on a
    one-party fixture and fail here. The property is INVARIANCE — reach is a
    fact about the party, not about the state of the typist's clipboard — and
    the single-case equality above is one instance of it.

    Asserted in both directions: adding a party does not move the first one's
    reach, and removing it again returns the same value exactly.
    """
    wards = _city_wards()
    n, k = len(wards), 20
    alone, _ = _declare(_toml_wards({"NEWCO": set(wards[:k])}))
    crowded, _ = _declare(_toml_wards({"NEWCO": set(wards[:k]),
                                       "OTHERCO": set(wards[k:])}))
    back, _ = _declare(_toml_wards({"NEWCO": set(wards[:k])}))

    assert alone["reach"]["NEWCO"] == crowded["reach"]["NEWCO"] == back["reach"]["NEWCO"], (
        f"NEWCO's reach moved when a SECOND party was declared: "
        f"{alone['reach']['NEWCO']:.6f} alone, "
        f"{crowded['reach']['NEWCO']:.6f} with OTHERCO, "
        f"{back['reach']['NEWCO']:.6f} after removing it. Nothing about "
        f"NEWCO's own declaration changed. Under the defect it fell 1.0 -> "
        f"0.1481, so the error was MAXIMAL at the first party entered and "
        f"shrank as the list grew — the opposite of the direction anyone "
        f"would check on the night.")
    assert abs(crowded["reach"]["OTHERCO"] - (n - k) / n) < 1e-12, (
        f"the second party's own reach is {crowded['reach']['OTHERCO']:.6f}, "
        f"not {(n - k) / n:.6f}. Case 1 and case 2 must hold together, or the "
        f"denominator is being chosen per party.")


def test_an_explicit_roster_reach_still_wins():
    """CASE 3: the derivation is a fallback, not an override.

    ``reach.setdefault`` is what makes the declared value win. Deleting the
    derivation would also pass this test, which is why cases 1 and 2 are here —
    and ⛔ deleting it is barred anyway: it restores the ``reach = None`` defect
    the derivation was written to close.
    """
    wards = _city_wards()
    body = ('[roster.reach]\nNEWCO = 0.9\n'
            + _toml_wards({"NEWCO": set(wards[:20])}))
    got, _ = _declare(body)
    assert got["reach"]["NEWCO"] == 0.9, (
        f"an explicit [roster.reach] of 0.9 was overwritten by the derivation "
        f"({got['reach']['NEWCO']:.6f}). A hand-declared value is the one thing "
        f"that must survive.")


# --------------------------------------------------------------------------
# the consumers, asserted separately
# --------------------------------------------------------------------------

def test_the_two_reach_values_do_not_produce_the_same_split_weights():
    """THE CONSUMER READS THE REPAIRED QUANTITY, not a stale copy.

    ``arrival_group_spec`` turns reach straight into split weights. If the
    wrong value and the right one gave the same spec, repairing reach would have
    bought nothing — and the reach could be repaired while a consumer still read
    something else. Asserted on the WEIGHT, which is the number, not on a note.
    """
    wards = _city_wards()
    n, k = len(wards), 20
    wrong, right = 1.0, k / n
    a = pools.arrival_group_spec(YEAR, {"NEWCO": wrong}, ["NEWCO"])
    b = pools.arrival_group_spec(YEAR, {"NEWCO": right}, ["NEWCO"])
    if a is None or b is None:
        skip(f"no arrival record before {YEAR} to split")
    assert a["weights"]["NEWCO"] != b["weights"]["NEWCO"], (
        f"a reach of {wrong} and one of {right:.4f} produce the SAME split "
        f"weight ({a['weights']['NEWCO']}), so `arrival_group_spec` is not "
        f"reading the quantity entry 23 repaired.")
    assert a["weights"]["NEWCO"] > b["weights"]["NEWCO"], (
        f"the inflated reach gave the SMALLER weight "
        f"({a['weights']['NEWCO']} vs {b['weights']['NEWCO']}), which inverts "
        f"the direction of the harm this entry describes.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
