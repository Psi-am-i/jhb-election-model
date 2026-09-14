"""THE INPUTS SEGMENT OF THE TRACE — is what entered the model what we think
it is, and was all of it available before the target election?

``run_model`` emits thirteen stages when given ``--run-dir``. The first four are
the INPUTS::

    00_target          which election is being forecast, and how big
    01_scenario_in     the settled lever set, before the model touches it
    02_pools_artefact  which precomputed pool spec was read, and its identity
    03_roster          who is on the target's ballot, and which of two states
                       that answer is in

Everything downstream is a transformation of those four. A defect here is
therefore invisible at the point it is introduced and expensive at the point it
is found, which is the shape of most of this repository's history.

**WHY A TRACE NEEDS ITS OWN TESTS.** The trace is a RECORD, not a check --
``Trace``'s own docstring says so: *"The pool ceiling that went blind would
appear here as 74 of 75 parties at exactly 1.0 and nobody would have looked."*
This module is the looking. It is written as **pure predicates over a stage
payload**, so every invariant runs on a constructed dict with no data on disk,
and the same predicates are then applied to a real trace.

⛔ **EVERY PREDICATE CARRIES A CONSTRUCTED VIOLATION** (CLAUDE.md §4). This
project already shipped a stage observer that could not see -- the arrival
reconciliation was blind at 20 of 24 rows while reporting nothing -- so an
observer that cannot demonstrate detection is worse than none.
:data:`CORRUPTIONS` is a table of one broken payload per invariant, and
``test_the_corruption_table_covers_every_declared_invariant`` fails if the two
sets differ **in either direction**: an invariant with no constructed violation
is undemonstrated, and a corruption whose id is not declared is a test asserting
something nobody wrote down.

**WHAT THIS MODULE DOES NOT DO.** It does not re-check the roster mechanism
(``test_roster_fails_closed.py``), the provenance registers against the code
(``test_register_matches_code.py``, ``test_levers_are_live.py``) or the trace's
inertness (``test_chain.py``). It checks the four PAYLOADS, and the AGREEMENTS
between them -- which nothing checked, because a trace directory is a bag of
JSON files and nothing has ever asserted that they came from one run.

⚠️ **THIS MODULE MUST BE LISTED IN ``tests/run_all.py``'s ``MODULES``** or it is
not collected, and a test that is not collected reads as coverage and is not.
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned, skip     # noqa: E402

import backtest as B                                     # noqa: E402
import cityconfig                                         # noqa: E402
import montecarlo as mc                                   # noqa: E402

STAGES = ("00_target", "01_scenario_in", "02_pools_artefact", "03_roster")

# The nine members of `pools.artefact_key`. Typed here so a field added to the
# code and not to this module is a FAILURE rather than an unchecked field --
# `test_the_artefact_key_field_set_matches_the_code` asserts the two agree, in
# both directions. `pools.stale_reason` learned this lesson the expensive way:
# it compared a literal tuple against a dict built elsewhere, so a field added
# to one and not the other was recorded and never checked.
ARTEFACT_KEY_FIELDS = frozenset({
    "schema", "city", "target",
    "pools_sha", "config_sha", "cities_sha", "deps_sha", "judgements_sha",
    "gates_sha"})
ARTEFACT_KEY_IDENTITY = frozenset({"schema", "city", "target"})
ARTEFACT_KEY_SCHEMA = 2

# Every hash in the key is `hashlib.sha256(...).hexdigest()[:16]`. A blank or
# short one is a hash that cannot differ from the next one, so staleness would
# pass for ever and silently -- the exact failure `artefact_key` exists to close.
_SHA16 = re.compile(r"\A[0-9a-f]{16}\Z")

ROSTER_STATES = ("published", "projected", "not_yet_held")

# Where an existing trace may be found for the integration test. An env var
# rather than a fixed path, because a trace is a diagnostic artefact and lives
# wherever the person running the diagnosis put it.
TRACE_ENV = "JHB_STAGE_TRACE"


# --------------------------------------------------------------------------
# the invariants, declared once
# --------------------------------------------------------------------------
#
# id -> why it exists. The id is what a predicate returns and what the
# corruption table keys on, so the three cannot drift apart silently.

INVARIANTS: dict[str, str] = {
    # --- 00_target ------------------------------------------------------
    "target.fields":
        "the stage must carry exactly city, year, council, draws and seed. A "
        "field that quietly disappears takes its invariant with it.",
    "target.year_not_a_string":
        "every cutoff comparison in this repository is a STRING comparison on "
        "a zero-padded year -- `contaminated` does `y >= str(target_year)`, "
        "`preceding` relies on lexicographic order being chronological. An int "
        "year does not raise; it compares wrong.",
    "target.year_not_in_calendar":
        "an election the calendar does not know has no date, no kind and no "
        "result template, so nothing downstream can place it in time.",
    "target.not_a_local_election":
        "this model forecasts a metro council. A target whose CALENDAR kind is "
        "NPE would run and produce seats for a body that has none.",
    "target.city_unknown":
        "the slug must load, or nothing can re-derive the council, the wards "
        "or the judgement file this run was supposed to read.",
    "target.council_disagrees_with_config":
        "`COUNCIL` is a module global set from `target.council`, and the active "
        "city is process-global. A trace whose recorded council is not the one "
        "`cities/<slug>.toml` gives for that year is a run whose city and "
        "target got out of step -- the city-namespacing class.",
    "target.draws_not_positive":
        "a run with no draws has no distribution; every band downstream would "
        "be an artefact of the sample size rather than of the model.",
    "target.seed_not_an_int":
        "the seed is the whole of reproducibility. A null seed makes the run "
        "unrepeatable while the trace still looks complete.",

    # --- 01_scenario_in --------------------------------------------------
    "scenario.keys_differ_from_defaults":
        "the settled lever set must be exactly `montecarlo.DEFAULTS`. A key "
        "missing means a lever was consumed from somewhere the artefact does "
        "not record; an extra key means a city toml or a scenario file invented "
        "a lever, which `apply_city` used to accept.",
    "scenario.private_key_leaked":
        "the stage filters `_`-prefixed keys, which are the run's own "
        "bookkeeping (`_delivered`, `_pools_stale`, `_roster_state`). One "
        "appearing means the filter broke and the payload is no longer the "
        "lever set.",
    "scenario.unregistered_lever":
        "every DEFAULTS key sits in exactly one of backtest's four provenance "
        "registers. An unregistered lever cannot be audited for leakage at all "
        "-- 27 of 35 reached neither list as recently as this summer.",
    "scenario.statutory_value_changed":
        "`overhang_rule` is statute (Municipal Structures Act Schedule 1 item "
        "16). A trace carrying any other value is a --counterfactual run and "
        "must never be read as the forecast.",
    "scenario.seed_disagrees_with_target":
        "00_target and 01_scenario_in read the seed from one dict at one "
        "moment. If they disagree, the trace was assembled from two runs.",
    "scenario.draws_disagree_with_target":
        "as above, for the draw count.",

    # --- 02_pools_artefact -----------------------------------------------
    "pools.fields":
        "the stage must carry path, artefact_key, stale_reason and fitted_on.",
    "pools.no_artefact_key":
        "a spec emitted before artefact keys existed cannot be shown to match "
        "the code that is running, so no measurement taken against it means "
        "anything.",
    "pools.artefact_key_fields":
        "the key's member set must be exactly the nine `pools.artefact_key` "
        "produces. A field present in the stored key and no longer produced is "
        "the register->code blindness this project calls its worst class.",
    "pools.schema_unexpected":
        "the key's own shape is versioned; a different schema means the fields "
        "mean something else.",
    "pools.sha_not_a_hash":
        "every *_sha is sha256()[:16]. A blank, null or short hash cannot "
        "differ from the next one, so staleness would pass for ever -- "
        "silently, which is the whole failure mode the key was built against.",
    "pools.stale":
        "`stale_reason` is non-null when the spec no longer matches live code, "
        "config, cities, judgements or gates. run_model PRINTS this and "
        "continues, so nothing refuses; a trace is the only place it survives.",
    "pools.key_identity_mismatch":
        "the key records the city and target it was built for. A spec copied "
        "between city-years matches on filename and not on this.",
    "pools.path_not_for_target":
        "the spec is read from `pools_<target>.json`. A payload naming any "
        "other file is a trace whose stages came from different runs.",
    "pools.fitted_on_not_before_target":
        "⛔ THE CUTOFF. `fitted_on` is the election whose results the pool "
        "ratios were fitted on, and `emit_pools` resolves it as `from_year or "
        "target.previous_lge or target.year` -- so a target with no previous "
        "LGE, or any `--from-year`, can fit the pools on the target's own "
        "result. Nothing in src/ checks it.",
    "pools.fitted_on_not_a_year":
        "a fitted_on that is not a four-digit string compares wrong against the "
        "target year instead of raising.",

    # --- 03_roster -------------------------------------------------------
    "roster.fields":
        "the stage must carry state, size and dropped.",
    "roster.state_unknown":
        "`roster_for_target` returns exactly three states; a fourth value "
        "means somebody widened the contract without telling the consumers.",
    "roster.published_but_empty":
        "⛔ THE POSITIVE CONTROL. An empty roster is the value meaning DROP "
        "NOBODY, and it used to be indistinguishable from an election not yet "
        "held -- so any defect inside `contesting_parties` silently disabled "
        "the off-ballot drop, worth of the order of one invented seat. `size` "
        "is what tells a roster that was READ from one that was merely absent.",
    "roster.projected_but_empty":
        "the same trap one layer up: a spec that NAMES a `roster_source` is "
        "claiming `pools.resolve_roster` produced a roster, and "
        "`roster_for_target` raises rather than returning an empty or "
        "malformed one under that claim (2026-09-14) -- so a `projected` "
        "state with size<=0 cannot have come from that function either.",
    "roster.not_yet_held_but_populated":
        "the not-yet-held state has no result file and no usable spec roster, "
        "so it can have no roster and can have dropped nobody. A size or a "
        "drop in that state means the state label is lying about which branch "
        "ran.",
    "roster.dropped_not_sorted_unique":
        "`dropped` is written `sorted(...)` of a list built by appending each "
        "absent party once. A duplicate means the drop ran twice on one party; "
        "an unsorted list means the payload was not produced by this code.",
    "roster.state_disagrees_with_calendar":
        "the discriminator is the RESULTS TEMPLATE, not the clock: "
        "`CALENDAR[year].results is None` is the calendar's own statement that "
        "an election has no result file, and it is the same condition "
        "`contesting_parties` keys its legitimate empty return on. A held "
        "target (a result file exists) must be `published`; an unheld one may "
        "be `not_yet_held` OR `projected` (2026-09-14: the spec's own roster, "
        "when it has one), but `published` is never legitimate without a "
        "result file. A trace where these disagree is a run that took the "
        "wrong branch.",

    # --- agreements across the four --------------------------------------
    "across.stage_missing":
        "all four input stages are unconditional in `run_model`. A missing one "
        "is a run that raised, a trace that was truncated, or -- for "
        "02_pools_artefact -- a run that supplied `scenario['pools']` itself "
        "and therefore SKIPPED the staleness check entirely.",
    "across.pools_value_not_recorded":
        "⚠️ `01_scenario_in` is written BEFORE the pool spec is loaded, so it "
        "records `pools: {}` on every run. The value actually consumed -- a "
        "70-party dict -- is recorded nowhere except as the artefact key in "
        "02. A lever consumed at a value the artefact does not record is the "
        "defect class this project is remediating, and the only thing standing "
        "between here and it is that 02 is present and carries a key.",
    "across.delivery_proof_disagrees":
        "`45_delivered['pools']` is built from the same dict 02 is built from, "
        "three lines apart. They are two copies of one number and one of them "
        "will go stale.",
    "across.pools_not_in_constants_read":
        "`note_constant(scenario, 'pools', ...)` fires in the same branch that "
        "writes 02. A trace with 02 and without `pools` in `constants_read` has "
        "lost its delivery proof, and `in_sample_banner` would then report the "
        "run clean on the largest input it has.",
}


def _off(out: list, ident: str, detail: str) -> None:
    assert ident in INVARIANTS, f"undeclared invariant id {ident!r}"
    out.append((ident, detail))


def ids(offences) -> set[str]:
    """The invariant ids in a predicate's return value."""
    return {i for i, _ in offences}


# --------------------------------------------------------------------------
# the predicates — pure functions over one stage payload
# --------------------------------------------------------------------------

def offences_target(payload, *, calendar=None, council_for=None) -> list:
    """Offences in ``00_target``.

    ``calendar`` maps year -> CALENDAR kind ("LGE"/"NPE"); ``council_for`` is
    ``(city, year) -> int | None``, None meaning the city is not loadable. Both
    default to the live repository, and both are arguments so the predicate can
    be exercised on a constructed world with no data on disk.
    """
    out: list = []
    if calendar is None:
        calendar = {y: e.kind for y, e in cityconfig.CALENDAR.items()}
    if council_for is None:
        council_for = _real_council_for

    expected = {"city", "year", "council", "draws", "seed"}
    if not isinstance(payload, dict) or set(payload) != expected:
        _off(out, "target.fields",
             f"expected exactly {sorted(expected)}, got "
             f"{sorted(payload) if isinstance(payload, dict) else type(payload)}")
        if not isinstance(payload, dict):
            return out

    year = payload.get("year")
    if not isinstance(year, str):
        _off(out, "target.year_not_a_string", f"year is {year!r}")
    else:
        if year not in calendar:
            _off(out, "target.year_not_in_calendar",
                 f"{year} is not in the calendar ({sorted(calendar)})")
        elif calendar[year] != "LGE":
            _off(out, "target.not_a_local_election",
                 f"{year} is a {calendar[year]}, not a local election")

    city = payload.get("city")
    council = payload.get("council")
    want = council_for(city, year) if isinstance(year, str) else None
    if want is None:
        _off(out, "target.city_unknown", f"city {city!r} at {year!r}")
    elif council != want:
        _off(out, "target.council_disagrees_with_config",
             f"the trace says {council}, cities/{city}.toml says {want} "
             f"for {year}")

    draws = payload.get("draws")
    if not isinstance(draws, int) or isinstance(draws, bool) or draws <= 0:
        _off(out, "target.draws_not_positive", f"draws={draws!r}")
    seed = payload.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        _off(out, "target.seed_not_an_int", f"seed={seed!r}")
    return out


def _real_council_for(city, year):
    try:
        return int(cityconfig.load(str(city)).structure_for(str(year))["council"])
    except Exception:                       # unknown slug, or no by_year entry
        return None


def offences_scenario_in(payload, *, defaults=None, registers=None,
                         statutory=None, target=None) -> list:
    """Offences in ``01_scenario_in``.

    ``registers`` is a mapping register-name -> set of keys; ``statutory`` maps
    a key to the one value the law allows. ``target`` is the ``00_target``
    payload, for the two agreements that are cheapest to check here.
    """
    out: list = []
    if defaults is None:
        defaults = set(mc.DEFAULTS)
    if registers is None:
        registers = {"FITTED_ON": set(B.FITTED_ON),
                     "FITTED_ON_UNINSTRUMENTED": set(B.FITTED_ON_UNINSTRUMENTED),
                     "PROVENANCE_UNSETTLED": set(B.PROVENANCE_UNSETTLED),
                     "NOT_FITTED": set(B.NOT_FITTED)}
    if statutory is None:
        statutory = dict(mc.STATUTORY_VALUES)

    if not isinstance(payload, dict):
        _off(out, "scenario.keys_differ_from_defaults", f"not a dict: {payload!r}")
        return out

    private = sorted(k for k in payload if str(k).startswith("_"))
    if private:
        _off(out, "scenario.private_key_leaked", f"{private}")

    keys = {k for k in payload if not str(k).startswith("_")}
    if keys != set(defaults):
        _off(out, "scenario.keys_differ_from_defaults",
             f"missing {sorted(set(defaults) - keys)}, "
             f"extra {sorted(keys - set(defaults))}")

    # ⛔ BOTH DIRECTIONS IS THE POINT, and one of them is somebody else's test:
    # `test_levers_are_live` enumerates DEFAULTS against the registers. This
    # enumerates THE RUN'S OWN LEVER SET, which is what a scenario file or a
    # city toml can widen without DEFAULTS moving.
    for key in sorted(keys):
        holding = [name for name, members in registers.items() if key in members]
        if len(holding) != 1:
            _off(out, "scenario.unregistered_lever",
                 f"{key} is in {holding or 'no register'}")

    for key, value in sorted(statutory.items()):
        if key in payload and payload[key] != value:
            _off(out, "scenario.statutory_value_changed",
                 f"{key}={payload[key]!r}, statute says {value!r}")

    if isinstance(target, dict):
        if "seed" in target and payload.get("seed") != target.get("seed"):
            _off(out, "scenario.seed_disagrees_with_target",
                 f"{payload.get('seed')!r} vs {target.get('seed')!r}")
        if "draws" in target and payload.get("draws") != target.get("draws"):
            _off(out, "scenario.draws_disagree_with_target",
                 f"{payload.get('draws')!r} vs {target.get('draws')!r}")
    return out


def offences_pools_artefact(payload, *, target=None,
                            key_fields=ARTEFACT_KEY_FIELDS,
                            schema=ARTEFACT_KEY_SCHEMA) -> list:
    """Offences in ``02_pools_artefact``.

    ``target`` is the ``00_target`` payload. Without it the identity and cutoff
    checks cannot run, and their absence is reported rather than skipped.
    """
    out: list = []
    expected = {"path", "artefact_key", "stale_reason", "fitted_on"}
    if not isinstance(payload, dict) or set(payload) != expected:
        _off(out, "pools.fields",
             f"expected exactly {sorted(expected)}, got "
             f"{sorted(payload) if isinstance(payload, dict) else type(payload)}")
        if not isinstance(payload, dict):
            return out

    if payload.get("stale_reason") is not None:
        _off(out, "pools.stale", str(payload.get("stale_reason")))

    key = payload.get("artefact_key")
    if not isinstance(key, dict) or not key:
        _off(out, "pools.no_artefact_key", f"artefact_key={key!r}")
    else:
        if set(key) != set(key_fields):
            _off(out, "pools.artefact_key_fields",
                 f"records {sorted(set(key) - set(key_fields)) or 'nothing'} the "
                 f"code does not produce and is missing "
                 f"{sorted(set(key_fields) - set(key)) or 'nothing'}")
        if key.get("schema") != schema:
            _off(out, "pools.schema_unexpected",
                 f"schema={key.get('schema')!r}, expected {schema}")
        for field in sorted(set(key) - set(ARTEFACT_KEY_IDENTITY)):
            value = key[field]
            if not isinstance(value, str) or not _SHA16.match(value):
                _off(out, "pools.sha_not_a_hash", f"{field}={value!r}")

    fitted = payload.get("fitted_on")
    if not (isinstance(fitted, str) and re.fullmatch(r"\d{4}", fitted)):
        _off(out, "pools.fitted_on_not_a_year", f"fitted_on={fitted!r}")

    if isinstance(target, dict):
        year, city = target.get("year"), target.get("city")
        if isinstance(fitted, str) and isinstance(year, str) \
                and re.fullmatch(r"\d{4}", fitted) and fitted >= year:
            _off(out, "pools.fitted_on_not_before_target",
                 f"the pool ratios were fitted on {fitted}, and the target is "
                 f"{year}: the spec has read the answer")
        if isinstance(key, dict) and key:
            if key.get("target") != year or key.get("city") != city:
                _off(out, "pools.key_identity_mismatch",
                     f"key is for {key.get('city')} {key.get('target')}, the "
                     f"run is {city} {year}")
        want = f"pools_{year}.json"
        got = Path(str(payload.get("path", ""))).name
        if got != want:
            _off(out, "pools.path_not_for_target", f"read {got}, expected {want}")
    return out


def offences_roster(payload, *, target=None, has_results=None) -> list:
    """Offences in ``03_roster``.

    ``has_results`` maps a year to whether ``CALENDAR[year].results`` is set --
    the discriminator ``roster_for_target`` actually uses. Defaults to the live
    calendar.
    """
    out: list = []
    if has_results is None:
        has_results = {y: e.results is not None
                       for y, e in cityconfig.CALENDAR.items()}

    expected = {"state", "size", "dropped"}
    if not isinstance(payload, dict) or set(payload) != expected:
        _off(out, "roster.fields",
             f"expected exactly {sorted(expected)}, got "
             f"{sorted(payload) if isinstance(payload, dict) else type(payload)}")
        if not isinstance(payload, dict):
            return out

    state = payload.get("state")
    size = payload.get("size")
    dropped = payload.get("dropped")

    if state not in ROSTER_STATES:
        _off(out, "roster.state_unknown", f"state={state!r}")

    if not isinstance(dropped, list) or \
            any(not isinstance(p, str) for p in dropped):
        _off(out, "roster.dropped_not_sorted_unique",
             f"dropped is {dropped!r}")
    elif dropped != sorted(set(dropped)):
        _off(out, "roster.dropped_not_sorted_unique",
             f"{len(dropped)} entries, {len(set(dropped))} distinct, "
             f"sorted={dropped == sorted(dropped)}")

    n_dropped = len(dropped) if isinstance(dropped, list) else 0
    if state == "published":
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            _off(out, "roster.published_but_empty",
                 f"state=published with size={size!r}. An empty roster is the "
                 f"value meaning DROP NOBODY, and `roster_for_target` refuses "
                 f"rather than returning it -- so this payload cannot have come "
                 f"from that function.")
    elif state == "projected":
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            _off(out, "roster.projected_but_empty",
                 f"state=projected with size={size!r}. A spec naming a "
                 f"roster_source is claiming a roster was resolved, and "
                 f"`roster_for_target` refuses rather than returning an empty "
                 f"or malformed one under that claim -- so this payload cannot "
                 f"have come from that function.")
    elif state == "not_yet_held":
        if size != 0 or n_dropped:
            _off(out, "roster.not_yet_held_but_populated",
                 f"size={size!r}, {n_dropped} dropped")

    if isinstance(target, dict) and isinstance(target.get("year"), str) \
            and state in ROSTER_STATES:
        year = target["year"]
        if year in has_results:
            # A held target (a result file exists) must be `published`; an
            # unheld one may be `not_yet_held` OR `projected` -- both are
            # legitimate depending on whether the pool spec resolved a roster
            # -- but `published` is never legitimate without a result file.
            allowed = {"published"} if has_results[year] \
                else {"not_yet_held", "projected"}
            if state not in allowed:
                _off(out, "roster.state_disagrees_with_calendar",
                     f"state={state} at target {year}, whose calendar entry "
                     f"{'has' if has_results[year] else 'has no'} a result "
                     f"template, so the state must be one of {sorted(allowed)}")
    return out


def offences_across(stages) -> list:
    """Offences in the AGREEMENTS between the four stages.

    A trace directory is a bag of JSON files. Nothing has ever asserted that
    they came from one run, and several of the numbers below exist in two
    places three lines apart in ``run_model``.
    """
    out: list = []
    if not isinstance(stages, dict):
        _off(out, "across.stage_missing", f"not a mapping: {stages!r}")
        return out

    for name in STAGES:
        if not isinstance(stages.get(name), dict):
            _off(out, "across.stage_missing", name)

    scenario = stages.get("01_scenario_in")
    artefact = stages.get("02_pools_artefact")
    if isinstance(scenario, dict) and "pools" in scenario:
        recorded = scenario["pools"]
        has_key = isinstance(artefact, dict) and isinstance(
            artefact.get("artefact_key"), dict) and bool(artefact["artefact_key"])
        if recorded:
            _off(out, "across.pools_value_not_recorded",
                 "01_scenario_in carries a non-empty `pools`, which means the "
                 "caller supplied the spec itself: run_model's `if not "
                 "scenario.get('pools')` branch did not run, so NO staleness "
                 "check was performed and no 02_pools_artefact was written.")
        elif not has_key:
            _off(out, "across.pools_value_not_recorded",
                 "01_scenario_in records `pools: {}` (it is written before the "
                 "spec is loaded) and 02_pools_artefact carries no key, so "
                 "nothing in this trace says WHICH pools the run consumed.")

    index = stages.get("_index")
    if isinstance(artefact, dict) and isinstance(index, dict):
        read = set(index.get("constants_read") or ())
        if "pools" not in read:
            _off(out, "across.pools_not_in_constants_read",
                 f"constants_read={sorted(read)}")

    delivered = stages.get("45_delivered")
    if isinstance(artefact, dict) and isinstance(delivered, dict) \
            and isinstance(delivered.get("pools"), dict):
        rec = delivered["pools"]
        values = rec.get("values") or []
        if not values or values[-1] != artefact.get("artefact_key"):
            _off(out, "across.delivery_proof_disagrees",
                 f"45_delivered records {values[-1] if values else None!r}, "
                 f"02 records {artefact.get('artefact_key')!r}")
        who = (rec.get("who") or [None])[-1]
        if who != f"fitted on {artefact.get('fitted_on')}":
            _off(out, "across.delivery_proof_disagrees",
                 f"45_delivered says {who!r}, 02 says fitted_on="
                 f"{artefact.get('fitted_on')!r}")
    return out


def all_offences(stages) -> list:
    """Every predicate, over a whole trace."""
    target = stages.get("00_target")
    return (offences_target(stages.get("00_target"))
            + offences_scenario_in(stages.get("01_scenario_in"), target=target)
            + offences_pools_artefact(stages.get("02_pools_artefact"),
                                      target=target)
            + offences_roster(stages.get("03_roster"), target=target)
            + offences_across(stages))


# --------------------------------------------------------------------------
# the cutoff report — reported, never asserted empty
# --------------------------------------------------------------------------

def implicated_levers(stages, *, fitted_on=None, uninstrumented=None,
                      unsettled=None) -> tuple[list[str], list[str]]:
    """``(contaminated, unsettled)`` read FROM THE TRACE ALONE.

    This reproduces :func:`backtest.contaminated` and :func:`backtest.unsettled`
    from four JSON files, which matters because the banner is printed once, to
    stdout, by a process that has already exited by the time anyone asks.

    ⚠️ **`pools` MUST BE TAKEN FROM 02, NOT FROM 01.** `01_scenario_in` records
    `pools: {}` on every run -- it is written before the spec is loaded -- and
    `pools` is a `FITTED_ON` key implicated at 2011, 2016 and 2021. A cutoff
    audit reading the lever set alone therefore clears the single largest input
    the model has. The delivery proof (`constants_read`) is what makes it
    visible, and is why this function needs `_index`.

    The two registers are read differently and deliberately so: a `FITTED_ON`
    key is implicated only when the run's read log names it, because
    consumption is instrumented there; an uninstrumented or unsettled key is
    implicated on PRESENCE, because nothing records its read. That asymmetry is
    :func:`backtest._grade`'s and is reproduced rather than improved on.
    """
    if fitted_on is None:
        fitted_on = {k: v[0] for k, v in B.FITTED_ON.items()}
    if uninstrumented is None:
        uninstrumented = {k: v[0] for k, v in B.FITTED_ON_UNINSTRUMENTED.items()}
    if unsettled is None:
        unsettled = {k: v[0] for k, v in B.PROVENANCE_UNSETTLED.items()}

    target = stages.get("00_target") or {}
    year = str(target.get("year"))
    scenario = dict(stages.get("01_scenario_in") or {})
    read = set((stages.get("_index") or {}).get("constants_read") or ())

    def peeks(years) -> bool:
        return any(str(y) >= year for y in years)

    bad = {k for k, years in fitted_on.items() if k in read and peeks(years)}
    bad |= {k for k, years in uninstrumented.items()
            if k in scenario and peeks(years)}
    open_q = {k for k, years in unsettled.items()
              if k in scenario and peeks(years)}
    return sorted(bad), sorted(open_q)


# --------------------------------------------------------------------------
# constructed payloads — a healthy trace, built by hand
# --------------------------------------------------------------------------
#
# ⛔ CONSTRUCTED, NOT OBSERVED (CLAUDE.md §4, requirement 3). A fixture copied
# out of a passing run expires the day the tree changes and takes its test with
# it. This world is invented: `metropolis` is not a city, and `2019`/`2021`/
# `2026` here are a CALENDAR this module supplies.

WORLD = dict(
    calendar={"2019": "NPE", "2021": "LGE", "2024": "NPE", "2026": "LGE"},
    has_results={"2019": True, "2021": True, "2024": True, "2026": False},
    councils={("metropolis", "2021"): 200, ("metropolis", "2026"): 200},
    defaults={"draws", "seed", "w_bye", "level_shrink", "overhang_rule",
              "pools", "turnout_correlation"},
    registers={"FITTED_ON": {"pools"},
               "FITTED_ON_UNINSTRUMENTED": {"level_shrink",
                                            "turnout_correlation"},
               "PROVENANCE_UNSETTLED": set(),
               "NOT_FITTED": {"draws", "seed", "w_bye", "overhang_rule"}},
    statutory={"overhang_rule": "deduct"},
)


def healthy() -> dict:
    """A trace that every predicate must pass."""
    key = {"schema": ARTEFACT_KEY_SCHEMA, "city": "metropolis",
           "target": "2021",
           "pools_sha": "0123456789abcdef", "config_sha": "fedcba9876543210",
           "cities_sha": "00112233445566aa", "deps_sha": "aabbccddeeff0011",
           "judgements_sha": "1234abcd5678ef90", "gates_sha": "abcdef0123456789"}
    return {
        "00_target": {"city": "metropolis", "year": "2021", "council": 200,
                      "draws": 5000, "seed": 20261104},
        "01_scenario_in": {"draws": 5000, "seed": 20261104, "w_bye": 0.4,
                           "level_shrink": 0.35, "overhang_rule": "deduct",
                           "pools": {}, "turnout_correlation": 0.63},
        "02_pools_artefact": {"path": "data/processed/pools_2021.json",
                              "artefact_key": key, "stale_reason": None,
                              "fitted_on": "2016"},
        "03_roster": {"state": "published", "size": 57,
                      "dropped": ["ALPHA", "BETA"]},
        "_index": {"constants_read": ["pools", "spine"],
                   "written": list(STAGES)},
        "45_delivered": {"pools": {"values": [key], "who": ["fitted on 2016"],
                                   "where": ["montecarlo:run_model <- "
                                             "pools_2021.json"],
                                   "kinds": ["consulted"], "reads": 1,
                                   "dropped": 0}},
    }


def healthy_not_yet_held() -> dict:
    """The live-forecast shape: no result file, so no roster and no drop."""
    trace = healthy()
    trace["00_target"]["year"] = "2026"
    trace["02_pools_artefact"] = {
        "path": "data/processed/pools_2026.json",
        "artefact_key": {**trace["02_pools_artefact"]["artefact_key"],
                         "target": "2026"},
        "stale_reason": None, "fitted_on": "2021"}
    trace["45_delivered"]["pools"]["values"] = [
        trace["02_pools_artefact"]["artefact_key"]]
    trace["45_delivered"]["pools"]["who"] = ["fitted on 2021"]
    trace["45_delivered"]["pools"]["where"] = [
        "montecarlo:run_model <- pools_2026.json"]
    trace["03_roster"] = {"state": "not_yet_held", "size": 0, "dropped": []}
    return trace


def healthy_projected() -> dict:
    """2026-with-a-spec-roster: no result file, but the pool spec has one.

    Added 2026-09-14 alongside the `projected` state: `roster_for_target` now
    reads `pools.emit_pools`'s own `roster`/`roster_source` off the spec for a
    target with no result file, instead of always disabling the drop. Built
    from `healthy_not_yet_held` -- same target, same calendar shape -- with
    only `03_roster` changed, so a test comparing the two isolates exactly
    that difference.
    """
    trace = healthy_not_yet_held()
    trace["03_roster"] = {"state": "projected", "size": 40,
                          "dropped": ["GAMMA"]}
    return trace


def _check(trace, world=None) -> list:
    """Every predicate over a constructed trace, in the constructed world.

    ``world`` is a patch over :data:`WORLD`, because two invariants are about
    the WORLD being wrong rather than the payload -- a lever that is in
    ``DEFAULTS`` and in no register is not visible in a payload at all.
    """
    w = {**WORLD, **(world or {})}
    target = trace.get("00_target")
    return (offences_target(target, calendar=w["calendar"],
                            council_for=lambda c, y: w["councils"].get((c, y)))
            + offences_scenario_in(trace.get("01_scenario_in"),
                                   defaults=w["defaults"],
                                   registers=w["registers"],
                                   statutory=w["statutory"], target=target)
            + offences_pools_artefact(trace.get("02_pools_artefact"),
                                      target=target)
            + offences_roster(trace.get("03_roster"), target=target,
                              has_results=w["has_results"])
            + offences_across(trace))


# --------------------------------------------------------------------------
# the constructed violations — one per invariant
# --------------------------------------------------------------------------

def _mut(path, value, *, delete=False):
    """A corruption that sets (or deletes) one field of a healthy trace."""
    def apply(trace):
        node = trace
        for part in path[:-1]:
            node = node[part]
        if delete:
            node.pop(path[-1], None)
        else:
            node[path[-1]] = value
        return trace
    return apply


def _drop_stage(name):
    def apply(trace):
        trace.pop(name, None)
        return trace
    return apply


# id -> (break a healthy trace, which base to break[, a patch over WORLD])
CORRUPTIONS: dict[str, tuple] = {
    "target.fields": (_mut(("00_target", "council"), None, delete=True), healthy),
    "target.year_not_a_string": (_mut(("00_target", "year"), 2021), healthy),
    "target.year_not_in_calendar": (_mut(("00_target", "year"), "2013"), healthy),
    "target.not_a_local_election": (_mut(("00_target", "year"), "2024"), healthy),
    "target.city_unknown": (_mut(("00_target", "city"), "atlantis"), healthy),
    "target.council_disagrees_with_config":
        (_mut(("00_target", "council"), 270), healthy),
    "target.draws_not_positive": (_mut(("00_target", "draws"), 0), healthy),
    "target.seed_not_an_int": (_mut(("00_target", "seed"), None), healthy),

    "scenario.keys_differ_from_defaults":
        (_mut(("01_scenario_in", "poll_weight"), 0.5), healthy),
    "scenario.private_key_leaked":
        (_mut(("01_scenario_in", "_delivered"), {}), healthy),
    # A lever that IS in DEFAULTS and in no register: invisible in the payload
    # alone, which is why this one patches the world instead of only the trace.
    # It is the state 27 of 35 DEFAULTS keys were in until this summer.
    "scenario.unregistered_lever":
        (_mut(("01_scenario_in", "orphan_lever"), 1.0), healthy,
         {"defaults": WORLD["defaults"] | {"orphan_lever"}}),
    "scenario.statutory_value_changed":
        (_mut(("01_scenario_in", "overhang_rule"), "expand"), healthy),
    "scenario.seed_disagrees_with_target":
        (_mut(("01_scenario_in", "seed"), 1), healthy),
    "scenario.draws_disagree_with_target":
        (_mut(("01_scenario_in", "draws"), 40), healthy),

    "pools.fields":
        (_mut(("02_pools_artefact", "fitted_on"), None, delete=True), healthy),
    "pools.no_artefact_key":
        (_mut(("02_pools_artefact", "artefact_key"), {}), healthy),
    "pools.artefact_key_fields":
        (_mut(("02_pools_artefact", "artefact_key", "gates_sha"), None,
              delete=True), healthy),
    "pools.schema_unexpected":
        (_mut(("02_pools_artefact", "artefact_key", "schema"), 1), healthy),
    "pools.sha_not_a_hash":
        (_mut(("02_pools_artefact", "artefact_key", "pools_sha"), ""), healthy),
    "pools.stale":
        (_mut(("02_pools_artefact", "stale_reason"), "src/pools.py changed"),
         healthy),
    "pools.key_identity_mismatch":
        (_mut(("02_pools_artefact", "artefact_key", "target"), "2016"), healthy),
    "pools.path_not_for_target":
        (_mut(("02_pools_artefact", "path"),
              "data/processed/pools_2026_simulation.json"), healthy),
    "pools.fitted_on_not_before_target":
        (_mut(("02_pools_artefact", "fitted_on"), "2021"), healthy),
    "pools.fitted_on_not_a_year":
        (_mut(("02_pools_artefact", "fitted_on"), "the 2016 election"), healthy),

    "roster.fields":
        (_mut(("03_roster", "size"), None, delete=True), healthy),
    "roster.state_unknown":
        (_mut(("03_roster", "state"), "unknown"), healthy),
    # ⛔ THE DEFECT, EXACTLY AS IT WAS: an unreadable roster returning an empty
    # set while the state still claims the drop ran.
    "roster.published_but_empty":
        (_mut(("03_roster", "size"), 0), healthy),
    # Same defect, one layer up: a spec claiming a roster_source with no
    # readable roster behind it. `roster_for_target` raises on this rather
    # than falling back to `not_yet_held` -- see its docstring, 2026-09-14.
    "roster.projected_but_empty":
        (_mut(("03_roster", "size"), 0), healthy_projected),
    "roster.not_yet_held_but_populated":
        (_mut(("03_roster", "size"), 57), healthy_not_yet_held),
    "roster.dropped_not_sorted_unique":
        (_mut(("03_roster", "dropped"), ["BETA", "ALPHA"]), healthy),
    "roster.state_disagrees_with_calendar":
        (_mut(("03_roster", "state"), "not_yet_held"), healthy),

    "across.stage_missing": (_drop_stage("03_roster"), healthy),
    "across.pools_value_not_recorded":
        (_mut(("01_scenario_in", "pools"), {"POOL": {}}), healthy),
    "across.delivery_proof_disagrees":
        (_mut(("45_delivered", "pools", "who"), ["fitted on 2021"]), healthy),
    "across.pools_not_in_constants_read":
        (_mut(("_index", "constants_read"), ["spine"]), healthy),
}


# --------------------------------------------------------------------------
# 1. the predicates pass what they must pass
# --------------------------------------------------------------------------

def test_a_healthy_payload_raises_no_offence():
    """The floor. A predicate that fires on a correct payload is noise.

    All three roster states, because they are different branches and two of
    them -- ``not_yet_held`` and, since 2026-09-14, ``projected`` -- are states
    the live 2026 forecast can legitimately run in.
    """
    for name, trace in (("published", healthy()),
                        ("not_yet_held", healthy_not_yet_held()),
                        ("projected", healthy_projected())):
        found = _check(trace)
        assert not found, f"the {name} trace was flagged: {found}"


def test_the_live_forecasts_roster_state_is_not_treated_as_a_fault():
    """`not_yet_held` with an empty roster is CORRECT and must stay so.

    The whole point of (now four) states is that an election with no result
    file legitimately has no roster, UNLESS the pool spec resolved one --
    ``test_a_projected_roster_state_is_not_treated_as_a_fault`` is that other
    half. A guard that could not tell either from a broken read would have to
    be switched off for the live forecast, and a guard that is off is not a
    guard.
    """
    trace = healthy_not_yet_held()
    assert trace["03_roster"] == {"state": "not_yet_held", "size": 0,
                                  "dropped": []}
    assert not offences_roster(trace["03_roster"], target=trace["00_target"],
                               has_results=WORLD["has_results"])
    # …and the same payload at a HELD target is a fault, so the pass above is
    # about the state and not about the predicate being asleep.
    held = dict(trace["00_target"], year="2021")
    assert "roster.state_disagrees_with_calendar" in ids(offences_roster(
        trace["03_roster"], target=held, has_results=WORLD["has_results"]))


def test_a_projected_roster_state_is_not_treated_as_a_fault():
    """`projected` at an unheld target is CORRECT; at a held one it is a fault.

    Added 2026-09-14 with the state itself. Mirrors the `not_yet_held` test
    above exactly, because the two are siblings under the same calendar
    discriminator (`has_results[year]` false) -- this is the other value that
    branch may legitimately take, and it must be told apart from
    `not_yet_held` by a consumer, not merged into "some unheld state".
    """
    trace = healthy_projected()
    assert trace["03_roster"]["state"] == "projected" and trace["03_roster"][
        "size"] > 0, "the fixture itself must carry a real, non-empty roster"
    assert not offences_roster(trace["03_roster"], target=trace["00_target"],
                               has_results=WORLD["has_results"])
    # …and the same payload at a HELD target is a fault: `projected` is an
    # assumption, and an assumption is never legitimate once the real result
    # file exists to read instead.
    held = dict(trace["00_target"], year="2021")
    assert "roster.state_disagrees_with_calendar" in ids(offences_roster(
        trace["03_roster"], target=held, has_results=WORLD["has_results"]))
    # `projected` and `not_yet_held` must not be conflated: a consumer reading
    # only "did the drop run on real data" needs the states kept SEPARATE.
    assert trace["03_roster"]["state"] != \
        healthy_not_yet_held()["03_roster"]["state"]


# --------------------------------------------------------------------------
# 2. the predicates CAN SEE — one constructed violation per invariant
# --------------------------------------------------------------------------

def test_every_constructed_violation_is_caught():
    """Push a broken payload through the same predicate and require the hit.

    Not "some offence was raised" -- **the declared one**. A test satisfied by
    any failure passes on a predicate that reports the wrong thing, which is
    the shape of the arrival reconciliation's blindness: it ran, it reported,
    and what it reported was about the wrong index.
    """
    for ident, entry in sorted(CORRUPTIONS.items()):
        corrupt, base, patch = (list(entry) + [None])[:3]
        found = _check(corrupt(base()), patch)
        assert ident in ids(found), (
            f"{ident}: the constructed violation was NOT caught. The predicate "
            f"reported {sorted(ids(found)) or 'nothing at all'}.\n"
            f"  why this invariant exists: {INVARIANTS[ident]}")


def test_the_corruption_table_covers_every_declared_invariant():
    """Requirement 0: the scan must have scanned the RIGHT population.

    Both directions. An invariant with no constructed violation is a claim
    nobody has shown the code can detect; a corruption whose id is not declared
    is a test asserting something that is written down nowhere. The register
    guard checked code->register and never register->code, and a deleted lever
    sat in the register for days.
    """
    declared, exercised = set(INVARIANTS), set(CORRUPTIONS)
    assert declared == exercised, (
        f"invariants with no constructed violation: "
        f"{sorted(declared - exercised) or 'none'}\n"
        f"corruptions for undeclared invariants: "
        f"{sorted(exercised - declared) or 'none'}")
    scanned(exercised, of=declared, low=1.0, high=1.0,
            what="invariants with a constructed violation",
            denominator="invariants declared in INVARIANTS")


def test_every_predicate_contributes_at_least_one_invariant():
    """No predicate is dead weight, and none is unreachable.

    A predicate whose ids are all raised by some OTHER predicate is not being
    exercised, and would keep passing if it were deleted.
    """
    predicates = {
        "offences_target": lambda t, w: offences_target(
            t.get("00_target"), calendar=w["calendar"],
            council_for=lambda c, y: w["councils"].get((c, y))),
        "offences_scenario_in": lambda t, w: offences_scenario_in(
            t.get("01_scenario_in"), defaults=w["defaults"],
            registers=w["registers"], statutory=w["statutory"],
            target=t.get("00_target")),
        "offences_pools_artefact": lambda t, w: offences_pools_artefact(
            t.get("02_pools_artefact"), target=t.get("00_target")),
        "offences_roster": lambda t, w: offences_roster(
            t.get("03_roster"), target=t.get("00_target"),
            has_results=w["has_results"]),
        "offences_across": lambda t, w: offences_across(t),
    }
    seen = {name: set() for name in predicates}
    for entry in CORRUPTIONS.values():
        corrupt, base, patch = (list(entry) + [None])[:3]
        broken = corrupt(base())
        world = {**WORLD, **(patch or {})}
        for name, fn in predicates.items():
            seen[name] |= ids(fn(broken, world))
    empty = sorted(n for n, got in seen.items() if not got)
    assert not empty, f"these predicates never fired on any corruption: {empty}"
    scanned(len(predicates) - len(empty), of=len(predicates), low=1.0, high=1.0,
            what="predicates demonstrated to fire",
            denominator="predicates defined in this module")


# --------------------------------------------------------------------------
# 3. the constants in this file must track the code
# --------------------------------------------------------------------------

def test_the_artefact_key_field_set_matches_the_code():
    """:data:`ARTEFACT_KEY_FIELDS` is a second copy of a set, so check it.

    ``pools.stale_reason`` carries the scar: it compared a literal tuple and
    then indexed a literal dict, so a field added to ``artefact_key`` and not to
    both was recorded and never checked. This module holds a third copy. It is
    justified only because this test exists.
    """
    import pools
    city = cityconfig.load("joburg")
    target = cityconfig.Target(city, "2021")
    key = pools.artefact_key(city, target)
    assert set(key) == set(ARTEFACT_KEY_FIELDS), (
        f"pools.artefact_key produces {sorted(set(key) - ARTEFACT_KEY_FIELDS)} "
        f"that this module does not check, and this module expects "
        f"{sorted(ARTEFACT_KEY_FIELDS - set(key))} that the code no longer "
        f"produces.")
    assert key["schema"] == ARTEFACT_KEY_SCHEMA, (
        f"the artefact key's schema moved to {key['schema']}; the field set "
        f"and the meanings recorded in skills/forecast-stage-inputs/SKILL.md "
        f"must be revisited before this constant is bumped.")
    for field in sorted(set(key) - ARTEFACT_KEY_IDENTITY):
        assert _SHA16.match(str(key[field])), (
            f"{field} is {key[field]!r}, which is not a 16-character hex "
            f"digest -- `pools.sha_not_a_hash` would fire on every real trace.")


def test_the_registers_this_module_reads_still_partition_the_levers():
    """Every ``DEFAULTS`` key in exactly one register, read the way I read it.

    ``test_levers_are_live`` owns this claim. It is repeated here for one
    reason: ``offences_scenario_in`` builds its default ``registers`` argument
    from these four names, and if one were renamed the predicate would silently
    classify every lever as unregistered -- or, worse, a register split in two
    would leave keys in none and the predicate would report a fault that is not
    there. The predicate's INPUT is what is checked, not the model's.
    """
    registers = {"FITTED_ON": set(B.FITTED_ON),
                 "FITTED_ON_UNINSTRUMENTED": set(B.FITTED_ON_UNINSTRUMENTED),
                 "PROVENANCE_UNSETTLED": set(B.PROVENANCE_UNSETTLED),
                 "NOT_FITTED": set(B.NOT_FITTED)}
    homeless = [k for k in mc.DEFAULTS
                if sum(k in m for m in registers.values()) != 1]
    assert not homeless, (
        f"these DEFAULTS keys are in none of the four registers, or in more "
        f"than one: {sorted(homeless)}. `offences_scenario_in` would report "
        f"every trace as carrying an unregistered lever.")
    scanned(mc.DEFAULTS, of=sum(len(m) for m in registers.values()),
            low=0.5, high=1.0,
            what="DEFAULTS keys the register partition covers",
            denominator="entries across the four provenance registers")


# --------------------------------------------------------------------------
# 4. the cutoff report
# --------------------------------------------------------------------------

def test_the_cutoff_report_sees_a_lever_fitted_on_the_target():
    """The leak detector's positive control, on a constructed world.

    A backtest at 2021 consuming a lever fitted on 2021 is circular, and the
    only thing that makes it visible is a register read against the recorded
    target year. If this reported nothing the banner would read as an
    all-clear.
    """
    trace = healthy()
    bad, open_q = implicated_levers(
        trace,
        fitted_on={"pools": ("2011", "2016", "2021")},
        uninstrumented={"level_shrink": ("2016", "2021"),
                        "turnout_correlation": ("2016", "2021")},
        unsettled={"spine_k": ("2011", "2016", "2021")})
    assert bad == ["level_shrink", "pools", "turnout_correlation"], bad
    assert open_q == [], open_q

    # ⚠️ AND THE TRAP: `pools` is in the report only because `constants_read`
    # names it. `01_scenario_in` records `pools: {}` on every run, so a cutoff
    # audit reading the lever set alone clears the largest input the model has.
    blind = dict(trace, _index={"constants_read": ["spine"]})
    assert "pools" not in implicated_levers(
        blind, fitted_on={"pools": ("2011", "2016", "2021")},
        uninstrumented={}, unsettled={})[0], (
        "this assertion RECORDS a hole rather than guarding one: without the "
        "delivery proof the pool spec is invisible to a cutoff audit. If it "
        "ever starts failing, 01_scenario_in has begun recording the pools it "
        "was actually handed, and `implicated_levers` should stop needing "
        "_index.")


def test_the_cutoff_report_clears_a_target_nothing_was_fitted_on():
    """And the other side of the two-sided bound: it can say nothing.

    A detector that fires on everything is as useless as one that fires on
    nothing, and is much easier to ship.
    """
    trace = healthy_not_yet_held()
    bad, open_q = implicated_levers(
        trace,
        fitted_on={"pools": ("2011", "2016", "2021")},
        uninstrumented={"level_shrink": ("2016", "2021")},
        unsettled={})
    assert bad == [] and open_q == [], (bad, open_q)


# --------------------------------------------------------------------------
# 5. integration — the same predicates, on a real trace
# --------------------------------------------------------------------------

def _read_trace(run_dir: Path) -> dict:
    out = {}
    for path in sorted(Path(run_dir).glob("*.json")):
        try:
            out[path.stem] = json.loads(path.read_text())
        except ValueError as exc:                       # a truncated write
            out[path.stem] = {"__unreadable__": repr(exc)}
    return out


def test_an_existing_trace_passes_every_predicate():
    """Point ``JHB_STAGE_TRACE`` at a run directory and this checks it.

    Skips LOUDLY when there is none, and never asserts less because of it. A
    trace is a diagnostic artefact and lives wherever the diagnosis put it::

        .venv/bin/python src/montecarlo.py --city joburg --target 2021 \\
            --run-dir /tmp/t
        JHB_STAGE_TRACE=/tmp/t .venv/bin/python tests/test_stage_inputs.py
    """
    where = os.environ.get(TRACE_ENV)
    if not where:
        skip(f"no {TRACE_ENV} set. This test checks a trace that already "
             f"exists; the one below BUILDS one, so the predicates are not "
             f"left unexercised against real data.")
    run_dir = Path(where)
    if not (run_dir / "00_target.json").exists():
        skip(f"{TRACE_ENV}={where} has no 00_target.json in it")
    stages = _read_trace(run_dir)
    found = all_offences(stages)
    assert not found, "\n".join(
        f"  {i}: {d}\n      {INVARIANTS[i]}" for i, d in found)


def test_a_real_run_produces_a_trace_that_passes_every_predicate():
    """Build a trace and check it. The only place the predicates meet reality.

    ⚠️ A skip-always integration test is worse than none -- it is the
    "premise is a passing state of the tree" failure inverted, and it expires
    on the day the data moves without anybody noticing. So this one makes its
    own input, at a draw count chosen to be cheap: the input stages do not
    depend on the number of draws at all.

    ⛔ Reads nothing but the trace it wrote. `--run-dir` is asserted inert by
    ``test_chain.py``, and ``run_model`` publishes nothing.
    """
    spec = ROOT / "data" / "processed" / "pools_2021.json"
    if not spec.exists():
        skip(f"no pool spec at {spec}: run "
             f"`python src/pools.py --city joburg --target 2021 --emit`")

    class _Args:
        config = None
        set = None
        draws = 24
        seed = None
        counterfactual = False

    with tempfile.TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "trace"
        city = cityconfig.use("joburg")
        target = cityconfig.use_target("2021")
        mc.apply_city(city)
        scenario = mc.load_scenario(_Args())
        mc.run_model(target, scenario, verbose=False, run_dir=run_dir)
        stages = _read_trace(run_dir)

    for name in STAGES:
        assert name in stages, f"{name} was not written"

    found = all_offences(stages)
    assert not found, "a real run's input stages were flagged:\n" + "\n".join(
        f"  {i}: {d}\n      {INVARIANTS[i]}" for i, d in found)

    # The positive control for the integration test itself: the predicates ran
    # against a payload with real content, not against four empty dicts.
    roster = stages["03_roster"]
    assert roster["state"] == "published" and roster["size"] > 0, roster
    # ⚠️ THE RATIO IS NOT BOUNDED BY 1. `dropped` counts parties in the 2019
    # NATIONAL baseline that did not stand locally; `size` counts parties on
    # the 2021 LOCAL ballot. They are different populations, and across the
    # panel the ratio runs from 0.15 (Cape Town 2011) to 1.00 (Buffalo City
    # 2011). Johannesburg 2021 is 13/57. The band is wide because the quantity
    # is; what it excludes is a drop that stopped firing and a drop that has
    # eaten the baseline.
    scanned(roster["dropped"], of=roster["size"], low=0.05, high=1.25,
            what="2019-baseline parties dropped as not on the 2021 ballot",
            denominator="parties on the 2021 Johannesburg ballot")

    # And the trace-only cutoff report must agree with backtest's own, which is
    # the strongest check available: two independent readings of one run.
    bad, open_q = implicated_levers(stages)
    read = {k: [] for k in (stages["_index"].get("constants_read") or [])}
    assert bad == B.contaminated("2021", set(), read=read,
                                 scenario=stages["01_scenario_in"]), (
        f"the trace-only cutoff report says {bad}, backtest.contaminated says "
        f"{B.contaminated('2021', set(), read=read, scenario=stages['01_scenario_in'])}")
    assert open_q == B.unsettled(stages["01_scenario_in"], target_year="2021")
    assert bad, (
        "a 2021 backtest consumes levers fitted on 2021 and the banner says "
        "so; an empty report here means the reader has gone blind, not that "
        "the run became clean.")


if __name__ == "__main__":
    raise SystemExit(run_module(globals()))
