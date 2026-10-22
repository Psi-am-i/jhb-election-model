"""THE CLAIMS REGISTER: EVERY PUBLIC CLAIM THAT THE MODEL USES SOMETHING NAMES
THE CODE THAT DOES IT, AND SAYS WHETHER THAT CODE RUNS ON THE 2026 FORECAST PATH.

`content/joburg/model-claims.toml` lists the claims (page, short text, symbol,
state, probe). Public text has described mechanisms the shipped forecast does
not run (by-election weights of zero, a retired heavy-tailed draw, a pool that
exists only in the simulation spec); nothing connected a sentence on a page to
the code it speaks of. This does, cheaply, with no model run.

What this file proves, per CLAUDE.md section 4:

0. THE RIGHT POPULATION, BOTH WAYS. The register's `pages` list and the pages
   its claims cite are the same set (`test_the_pages_listed_are_the_pages_cited`),
   every listed page exists, and the four pages named in `EXPECTED_PAGES` here
   (the ones the register was started from) are all listed.
1. IT LOOKED. The claim count is within a two-sided bound of the number of
   `[[claim]]` tables parsed from the file text, and every state used is one
   of the three.
2. IT CAN SEE. A constructed register with a missing symbol, a non-live claim
   with no probe, a probe that returns False, and an uncited page is caught in
   each case (`test_the_detector_sees_each_fault`), and the live register is
   clean.
3. CONSTRUCTED INPUT. The detector tests run on constructed registers, not the
   live file.

A probe returns True when the claim's DECLARED state holds. A probe for an `off`
or `absent` claim is what keeps that status honest; a probe on a `live` claim
does the same the other way: if `w_bye` went to 0, `bye_weight_is_positive`
returns False and every by-election claim must change state.
"""
from __future__ import annotations

import importlib
import json
import re
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module, scanned, skip  # noqa: E402

REGISTER = ROOT / "content" / "joburg" / "model-claims.toml"
STATES = ("live", "off", "absent")
EXPECTED_PAGES = {
    "docs-public/methodology.md", "docs-public/sources.md",
    "forecast-sheet.html", "interactive/your-forecast.html",
}


# ---------------------------------------------------------------------------
# probes: cheap reads of live state. True means the declared state holds.
# ---------------------------------------------------------------------------

def bye_weight_is_positive() -> bool:
    """By-elections reach the 2026 centres: a positive `w_bye` and a
    by-election input for Johannesburg 2026 to apply it to."""
    import montecarlo as M
    path = ROOT / "data" / "processed" / "byelection_party_deltas.csv"
    if not path.exists():
        skip("data/processed/byelection_party_deltas.csv is not on this machine")
    with path.open(encoding="utf-8") as handle:
        if sum(1 for _ in handle) < 2:
            return False
    w = M.DEFAULTS["w_bye"]
    return w is not None and float(w) > 0.0


def bye_weight_is_half() -> bool:
    """Halfway for every party: 0.5, applied as given ("fixed")."""
    import montecarlo as M
    return M.DEFAULTS["w_bye"] == 0.5 and M.DEFAULTS["bye_weight_mode"] == "fixed"


def draw_law_is_universal() -> bool:
    import montecarlo as M
    return (M.DEFAULTS["draw_law"] == "universal"
            and "incumbent" in M.DRAW_LAWS)


def level_shrink_is_positive() -> bool:
    import montecarlo as M
    return float(M.DEFAULTS["level_shrink"]) > 0.0


def poll_channel_is_off() -> bool:
    import montecarlo as M
    return M.DEFAULTS["poll_paths"] == "off"


def turnout_correlation_is_a_correlation() -> bool:
    import montecarlo as M
    return 0.0 < float(M.TURNOUT_CORRELATION) < 1.0


def overhang_default_is_a_known_rule() -> bool:
    import montecarlo as M
    return M.DEFAULTS["overhang_rule"] in M.OVERHANG_RULES


def overhang_rules_include_the_comparison_laws() -> bool:
    import montecarlo as M
    return {"expand", "cap", "level"} <= set(M.OVERHANG_RULES)


def splinter_weight_falls_back_to_default() -> bool:
    import pools
    return (pools.splinter_parent_weight({}, "X") == pools.SPLINTER_PARENT_WEIGHT
            and pools.splinter_parent_weight({"parent_weight": 0.5}, "X") == 0.5)


def starting_level_is_local_national_blend() -> bool:
    import levels
    import montecarlo as M
    # the run reads `levels.SPINE_K` when the scenario's spine_k is None, and
    # that weight puts mass on the party's own local route
    return M.DEFAULTS["spine_k"] is None and float(levels.SPINE_K) > 0.0


def roll_is_ward_totals_apportioned() -> bool:
    path = ROOT / "data" / "processed" / "vd_ward_2026.csv"
    if not path.exists():
        skip("data/processed/vd_ward_2026.csv is not on this machine")
    head = path.open(encoding="utf-8").readline().strip().split(",")
    return "part_registered_2026" in head and "roll_snapshot" in head


def ifp_pool_only_in_simulation_spec() -> bool:
    published = ROOT / "data" / "processed" / "pools_2026.json"
    simulation = ROOT / "data" / "processed" / "pools_2026_simulation.json"
    if not (published.exists() and simulation.exists()):
        skip("the 2026 pool specs are not on this machine")
    import pools
    name = pools.SIMULATION_BLOC["name"]
    return (name not in json.loads(published.read_text())["categories"]
            and name in json.loads(simulation.read_text())["categories"])


PROBES = {f.__name__: f for f in (
    bye_weight_is_positive, bye_weight_is_half, draw_law_is_universal, level_shrink_is_positive,
    poll_channel_is_off, turnout_correlation_is_a_correlation,
    overhang_default_is_a_known_rule, overhang_rules_include_the_comparison_laws,
    splinter_weight_falls_back_to_default, starting_level_is_local_national_blend,
    roll_is_ward_totals_apportioned, ifp_pool_only_in_simulation_spec)}


# ---------------------------------------------------------------------------
# the checker, over any register (so it can be run on a constructed one)
# ---------------------------------------------------------------------------

def resolve(symbol: str):
    """``module.attr[.attr]`` imported from ``src``; raises if it does not exist."""
    module, _, attrs = symbol.partition(".")
    obj = importlib.import_module(module)
    for attr in attrs.split("."):
        obj = getattr(obj, attr)
    return obj


def faults(doc: dict, probes: dict, page_exists=lambda p: (ROOT / p).exists(),
           run_probes: bool = True) -> list[str]:
    out = []
    listed = set((doc.get("register") or {}).get("pages") or [])
    cited = set()
    seen = set()
    for c in doc.get("claim") or []:
        cid = c.get("id", "<no id>")
        if cid in seen:
            out.append(f"{cid}: id repeated")
        seen.add(cid)
        cited.add(c.get("page"))
        for key in ("id", "page", "text", "symbol", "state"):
            if not c.get(key):
                out.append(f"{cid}: no {key}")
        if c.get("state") not in STATES:
            out.append(f"{cid}: state {c.get('state')!r} is not one of {STATES}")
        try:
            resolve(c.get("symbol", ""))
        except Exception as exc:                      # noqa: BLE001
            out.append(f"{cid}: symbol {c.get('symbol')!r} does not resolve ({exc})")
        probe = c.get("probe")
        if c.get("state") in ("off", "absent") and not probe:
            out.append(f"{cid}: a non-live claim declares no probe")
        if probe and probe not in probes:
            out.append(f"{cid}: probe {probe!r} is not defined")
        elif probe and run_probes:
            if probes[probe]() is not True:
                out.append(f"{cid}: probe {probe} is False, so the declared state "
                           f"{c.get('state')!r} does not hold")
    out += [f"page {p!r} is listed and no claim cites it" for p in sorted(listed - cited)]
    out += [f"page {p!r} is cited and not listed" for p in sorted(cited - listed)]
    out += [f"page {p!r} is listed and does not exist" for p in sorted(listed)
            if not page_exists(p)]
    return out


def _live() -> dict:
    return tomllib.loads(REGISTER.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_every_symbol_exists_every_probe_holds_and_the_register_is_clean():
    doc = _live()
    found = faults(doc, PROBES)
    assert not found, "\n".join(found)


def test_the_register_was_read_in_full():
    doc = _live()
    tables = len(re.findall(r"^\[\[claim\]\]", REGISTER.read_text(encoding="utf-8"),
                            flags=re.M))
    assert len(doc["claim"]) == tables
    scanned(doc["claim"], of=tables, low=1.0, high=1.0,
            what="claims parsed", denominator="[[claim]] tables in the file text")
    assert 20 <= tables <= 200, tables
    assert {c["state"] for c in doc["claim"]} <= set(STATES)
    # the register states the known claims truthfully: the five pages found
    # non-live were corrected on 2026-10-16, and each correction is there, live
    # (the by-election one live since `w_bye` became 0.5 on 2026-10-17,
    # JUDGEMENT-CALLS §A59; its page text changed 2026-10-21)
    by_id = {c["id"]: c for c in doc["claim"]}
    for cid, state in (("byelections-tilt-expected-share", "live"),
                       ("log-scale-bell-curve", "live"),
                       ("four-census-pools", "live"),
                       ("starting-level-blends-local-and-national", "live"),
                       ("roll-ward-snapshot-whole-vds", "live")):
        assert by_id[cid]["state"] == state, (cid, by_id[cid]["state"])


def test_the_pages_listed_are_the_pages_cited():
    doc = _live()
    listed = set(doc["register"]["pages"])
    cited = {c["page"] for c in doc["claim"]}
    assert listed == cited, (sorted(listed - cited), sorted(cited - listed))
    assert EXPECTED_PAGES <= listed, sorted(EXPECTED_PAGES - listed)
    assert all((ROOT / p).exists() for p in listed)


def test_the_detector_sees_each_fault():
    probes = {"yes": lambda: True, "no": lambda: False}
    good = {"register": {"pages": ["a"]},
            "claim": [dict(id="x", page="a", text="t", symbol="pools.fit_city",
                           state="live")]}
    exists = lambda p: True  # noqa: E731
    assert faults(good, probes, exists) == []
    def mutated(**change):
        c = dict(good["claim"][0], **change)
        return faults({"register": good["register"], "claim": [c]}, probes, exists)
    assert any("does not resolve" in f for f in mutated(symbol="pools.no_such_thing"))
    assert any("does not resolve" in f for f in mutated(symbol="no_such_module.x"))
    assert any("no probe" in f for f in mutated(state="off"))
    assert any("is False" in f for f in mutated(state="off", probe="no"))
    assert faults({"register": good["register"], "claim": [
        dict(good["claim"][0], state="off", probe="yes")]}, probes, exists) == []
    assert any("not defined" in f for f in mutated(probe="nope"))
    assert any("is not one of" in f for f in mutated(state="maybe"))
    assert any("listed and no claim" in f for f in faults(
        {"register": {"pages": ["a", "b"]}, "claim": good["claim"]}, probes, exists))
    assert any("cited and not listed" in f for f in faults(
        {"register": {"pages": []}, "claim": good["claim"]}, probes, exists))
    assert any("does not exist" in f for f in faults(good, probes, lambda p: False))


def test_a_mutated_live_probe_turns_the_register_red():
    """Mutation of the thing a claim speaks of: set `w_bye` to 0 and the
    claims declaring the by-election channel `live` go red; set back, the
    register is clean."""
    import montecarlo as M
    if not (ROOT / "data" / "processed" / "byelection_party_deltas.csv").exists():
        skip("data/processed/byelection_party_deltas.csv is not on this machine")
    declared = [c for c in _live()["claim"]
                if c.get("probe") in ("bye_weight_is_positive", "bye_weight_is_half")]
    only = dict(_live(), claim=declared)
    saved = M.DEFAULTS["w_bye"]
    M.DEFAULTS["w_bye"] = 0.0
    try:
        red = [f for f in faults(only, PROBES, page_exists=lambda p: True)
               if "is False" in f]
    finally:
        M.DEFAULTS["w_bye"] = saved
    assert len(declared) >= 4 and len(red) == len(declared), (len(red), len(declared))
    # the halfway claim also needs the weight applied as given
    half = dict(_live(), claim=[c for c in declared if c["probe"] == "bye_weight_is_half"])
    saved_mode = M.DEFAULTS["bye_weight_mode"]
    M.DEFAULTS["bye_weight_mode"] = "inverse_variance"
    try:
        red_mode = [f for f in faults(half, PROBES, page_exists=lambda p: True)
                    if "is False" in f]
    finally:
        M.DEFAULTS["bye_weight_mode"] = saved_mode
    assert half["claim"] and len(red_mode) == len(half["claim"]), red_mode
    assert not [f for f in faults(_live(), PROBES) if "bye_weight_is" in f]


if __name__ == "__main__":
    run_module(globals())
