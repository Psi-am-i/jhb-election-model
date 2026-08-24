"""CLASS: A LIVE-LOOKING NUMBER FED BY A DEAD MODEL.

`mode = "free"` is the registry's promise that a figure is recomputed from the
current model every build. It is not, and was never, a promise about how old
the model is. A free token resolves out of a FILE, and the file has a date.

`anc_entitlement` — `mode = "free"`, `source = "regime:cap:parties.ANC.median"`,
used twice on the live front page — resolved out of `regime_cap_summary.json`,
dated 2026-08-07, whose scenario block still names `turnout_tilt_da` and twelve
other levers `run_model` has not had for weeks. Every build republished that
number as current. The drift audit reported no drift throughout, correctly: a
frozen file cannot drift, so the one mechanism that could have caught it was
structurally incapable of doing so, and `mode = "free"` was reading as the
reassurance.

These tests hold the two signals apart on purpose. The scenario-key check is the
strong one — it identifies the model that wrote the file from what the file says
about itself. mtime is the weak fallback and is tested as such.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module  # noqa: E402

import build_site  # noqa: E402
import montecarlo  # noqa: E402
import stats  # noqa: E402

REGISTRY = {"anc_entitlement": {"mode": "free", "format": "int",
                                "source": "regime:cap:parties.ANC.median"}}


def _processed(tmp: Path, *, regime_scenario: dict, regime_age_s: float = 0.0,
               reference_scenario: dict | None = None) -> Path:
    """A miniature data/processed with a reference run and one regime file."""
    live = sorted(montecarlo.DEFAULTS)[:3]
    reference = {"scenario": reference_scenario if reference_scenario is not None
                 else {k: 1 for k in live},
                 "parties": {"ANC": {"median": 90}}}
    (tmp / "forecast_summary.json").write_text(json.dumps(reference))
    regime = tmp / "regime_cap_summary.json"
    regime.write_text(json.dumps({"scenario": regime_scenario,
                                  "parties": {"ANC": {"median": 50}}}))
    if regime_age_s:
        old = time.time() - regime_age_s
        os.utime(regime, (old, old))
    return tmp


def _problems(**kwargs):
    with tempfile.TemporaryDirectory() as d:
        processed = _processed(Path(d), **kwargs)
        ctx = stats.load_context(processed)
        return stats.freshness_problems(REGISTRY, ctx), ctx


def test_a_free_token_whose_source_file_names_a_deleted_lever_is_flagged():
    """THE DEFECT, in its strong form: the file says which model wrote it."""
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    scenario["turnout_tilt_da"] = 1.0          # deleted from run_model
    problems, _ = _problems(regime_scenario=scenario)
    assert len(problems) == 1, problems
    item = problems[0]
    assert "turnout_tilt_da" in item["extinct"], item
    assert "anc_entitlement" in item["tokens"], item
    assert "overhang_regimes" in item["remedy"], item


def test_a_free_token_whose_source_file_predates_the_reference_is_flagged():
    """The weak signal, alone: same lever set, older file."""
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    problems, _ = _problems(regime_scenario=scenario,
                            regime_age_s=stats.FRESHNESS_GRACE_S + 60)
    assert len(problems) == 1, problems
    assert problems[0]["behind"] is True, problems
    assert problems[0]["extinct"] == [], (
        "the mtime case must not be reported as a lever problem")


def test_a_current_source_file_is_not_flagged():
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    problems, _ = _problems(regime_scenario=scenario)
    assert problems == [], problems


def test_the_pipeline_ordering_lag_is_not_reported_as_staleness():
    """`overhang_regimes` writes the copies BEFORE restoring the reference.

    A check that fires on a correctly built pipeline gets switched off. The
    grace window is what stops that, and it is the reason the window exists —
    not tolerance for staleness. The defect this was written for was 16 days.
    """
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    problems, _ = _problems(regime_scenario=scenario,
                            regime_age_s=stats.FRESHNESS_GRACE_S / 2)
    assert problems == [], problems


def test_a_run_only_fact_in_the_reference_is_not_mistaken_for_a_dead_lever():
    """`arrival_group` is recorded by a run and is not in DEFAULTS.

    Comparing a scenario block against `montecarlo.DEFAULTS` alone flags the
    reference run itself, and a check that flags a file the same run just wrote
    is noise. The comparison is against DEFAULTS *and* the reference's own
    scenario keys.
    """
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    scenario["arrival_group"] = "shape"
    problems, _ = _problems(regime_scenario=scenario,
                            reference_scenario={**scenario})
    assert problems == [], problems


def test_the_message_names_the_file_both_dates_and_what_to_re_run():
    """A guard that says only 'stale' costs the reader the investigation."""
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    scenario["turnout_tilt_da"] = 1.0
    problems, _ = _problems(regime_scenario=scenario)
    report = stats.freshness_report(problems)
    for needed in ("regime_cap_summary.json", "forecast_summary.json",
                   problems[0]["file_date"], problems[0]["reference_date"],
                   "anc_entitlement", "overhang_regimes"):
        assert needed in report, f"{needed!r} missing from:\n{report}"


def test_nested_blocks_do_not_count_as_levers():
    """A regime summary carries theta_mode; the reference carries pools."""
    scenario = {k: 1 for k in sorted(montecarlo.DEFAULTS)[:3]}
    scenario["theta_mode"] = {"ANC": 0.9}
    scenario["_pools_stale"] = False
    problems, _ = _problems(regime_scenario=scenario)
    assert problems == [], problems


def test_the_site_build_refuses_rather_than_warns():
    """Not behavioural — `build_site.main` renders the whole site.

    It asserts the WIRING, which is the part that was missing: this repository
    has already proved that printing a finding is not enough.
    `orphaned_scenario_claims` printed its ten front-page claims through two
    independent reviews that both named them, and nothing stopped the build.
    """
    import inspect
    source = inspect.getsource(build_site.main)
    assert "freshness_problems" in source, (
        "build_site never asks whether a token's source file is stale")
    assert "allow_stale_sources" in source, (
        "no staging escape hatch — the fix cannot be landed in steps")
    guard = source[source.index("freshness_problems"):]
    assert "raise SystemExit" in guard.split("n_pinned")[0], (
        "a stale source only warns. A print is a comment, not an audit.")


if __name__ == "__main__":
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
