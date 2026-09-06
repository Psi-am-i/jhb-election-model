"""CLASS: A GUARD THE ONE-COMMAND PATH NEVER REACHES.

`build_site.py` carries the stat-provenance audits — `stats.audit` (a model
figure typed into prose), `orphaned_scenario_claims` (a pinned claim tied to a
deleted lever) and `stats.freshness_problems` (a live-looking token fed by a
dead model's file). Every one of them refuses to publish.

None of them ran. `build_all.py` executed `build_interactive.py` as a MANDATORY
step ahead of `build_site` and `build_portal`, and `build_interactive.py` raises
`SystemExit` at module level on purpose — the interactive page's in-browser
drawer is the old two-bloc engine and has not been ported to voter pools. So the
documented one-command build stopped, on every city, always, before it reached a
single audit; the guards only ever ran when a human typed `build_site.py`.

The step that broke the build was working exactly as designed. What was wrong was
that a step nothing depends on could be fatal. These tests hold the shape of the
fix: the pipeline reaches the site and the portal even when an optional step
declines, and a step that everything downstream DOES depend on still stops it.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import run_module, scanned  # noqa: E402

import build_all  # noqa: E402
import cityconfig  # noqa: E402


class _Result:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


def _fake_subprocess(fail_substrings=(), log=None):
    """Stand in for `subprocess.run`, failing any command naming a substring."""
    def run(cmd, *args, **kwargs):
        if log is not None:
            log.append(list(cmd))
        joined = " ".join(cmd)
        return _Result(1 if any(s in joined for s in fail_substrings) else 0)
    return run


def _main(argv, fail_substrings=()):
    log: list[list[str]] = []
    real = build_all.subprocess.run
    build_all.subprocess.run = _fake_subprocess(fail_substrings, log)
    try:
        code = build_all.main(argv)
    finally:
        build_all.subprocess.run = real
    return code, [" ".join(c) for c in log]


def test_build_site_and_portal_are_reached_when_an_optional_step_refuses():
    """THE DEFECT. `build_interactive` exits 1; the site must still be built."""
    code, ran = _main(["--city", "joburg", "--interactive"],
                      fail_substrings=("build_interactive.py",
                                       "export_interactive.py"))
    assert code == 0, f"build_all returned {code} after an optional refusal"
    assert any("build_site.py" in c for c in ran), (
        "build_site.py was never reached — the stat-provenance audits "
        f"(stats.audit, orphaned_scenario_claims, freshness_problems) did not "
        f"run. Commands executed: {ran}")
    assert any("build_portal.py" in c for c in ran), (
        f"build_portal.py was never reached. Commands executed: {ran}")


def test_the_interactive_page_is_not_built_by_default():
    """It refuses by design. Asking for it every time makes refusal routine.

    **(1) and (2) added 2026-08-31.** The two `assert not any(...)` clauses are
    satisfied by an EMPTY command log, and the log is empty whenever `build_all`
    stops routing through `subprocess.run` — an in-process call, a `Popen`, a
    task runner. So the absence is asserted against the same denominator that
    produces it, and the SAME substring detector is required to find
    `build_interactive.py` when the flag IS passed. A detector that cannot find
    the thing present proves nothing by not finding it absent.
    """
    _, ran = _main(["--city", "joburg"])
    opted, _ = _main(["--city", "joburg", "--interactive"]), None
    with_flag = opted[1]

    scanned(ran, of=with_flag, low=0.4, high=1.0,
            what="commands the default build ran",
            denominator="commands the --interactive build ran")
    assert any("build_interactive.py" in c for c in with_flag), (
        f"the substring detector cannot find build_interactive.py even when "
        f"--interactive is passed, so its silence on the default build is "
        f"worth nothing. Commands: {with_flag}")

    assert not any("build_interactive.py" in c for c in ran), (
        "build_interactive ran without --interactive, and it is a step that "
        "deliberately refuses")
    assert not any("export_interactive.py" in c for c in ran), (
        "the interactive data pack was built and nothing reads it")


def test_the_interactive_steps_are_optional_and_last():
    """Optional so a refusal is survivable; last so an unmodelled crash is too."""
    city = cityconfig.use("joburg")
    args = type("A", (), {"model": False, "regimes": False, "deploy": False,
                          "interactive": True})()
    steps = build_all.plan(args, city)
    labels = [label for label, _, _ in steps]
    interactive = [i for i, (_, cmd, _) in enumerate(steps)
                   if "interactive" in " ".join(cmd)]
    site = [i for i, (_, cmd, _) in enumerate(steps)
            if "build_site.py" in " ".join(cmd) or
            "build_portal.py" in " ".join(cmd)]
    assert interactive and site, labels
    assert min(interactive) > max(site), (
        f"an interactive step runs before the site/portal steps: {labels}")
    for i in interactive:
        assert steps[i][2] is True, f"{steps[i][0]!r} is marked required"


def test_a_required_step_still_stops_the_build():
    """The optional path must not have made every failure survivable."""
    try:
        _main(["--city", "joburg"], fail_substrings=("render_map.py",))
    except SystemExit as exc:
        assert "ward map" in str(exc), exc
    else:
        raise AssertionError(
            "a REQUIRED step failed and the build carried on — the site would "
            "be assembled from half-finished inputs")


def test_a_required_failure_does_not_reach_the_site():
    log: list[list[str]] = []
    real = build_all.subprocess.run
    build_all.subprocess.run = _fake_subprocess(("render_map.py",), log)
    try:
        build_all.main(["--city", "joburg"])
    except SystemExit:
        pass
    finally:
        build_all.subprocess.run = real
    ran = [" ".join(c) for c in log]
    # (1) IT LOOKED. `not any(...)` over an empty log is a pass, and an empty
    # log is what a build that stopped shelling out produces. The required step
    # must be seen to have been ATTEMPTED before its non-reaching of the site
    # means anything.
    assert any("render_map.py" in c for c in ran), (
        f"the failing REQUIRED step was never attempted, so the build did not "
        f"stop — it never started. Commands: {ran}")
    assert not any("build_site.py" in c for c in ran), ran


if __name__ == "__main__":
    # Append new tests ABOVE this line.
    raise SystemExit(run_module(globals()))
