"""Build one city end to end, then the site around it.

    python src/build_all.py --city joburg           # renders + site
    python src/build_all.py --city joburg --model   # re-run the model first

The model step is separate and opt-in because it takes minutes and its
output is deterministic — there is no point re-running 5,000 draws to fix a
sentence. Everything downstream of it is cheap and always runs.

Each step is echoed with its command so a failure can be reproduced by hand,
and the run stops at the first failure rather than building half a site.

**A step may be OPTIONAL, and an optional step's refusal does not stop the
build.** `build_interactive.py` raises `SystemExit` at module level, on
purpose: the interactive page's in-browser drawer is the old two-bloc engine
and has not been ported to voter pools, so it refuses rather than publish
arithmetic that disagrees with the model. It sat in this pipeline as a
mandatory step, ahead of `build_site` and `build_portal`, which meant those
two were UNREACHABLE through this script on every city, always — and with
them the stat-provenance guards that only `build_site.py` runs
(`stats.audit`, `orphaned_scenario_claims`, `stats.freshness_problems`). The
documented one-command path never reached the audits that exist to stop a
stale number being published, and only a human invoking `build_site.py` by
hand ever did.

So the interactive steps are now opt-in (`--interactive`), non-fatal, and run
LAST. Opt-in because they are currently disabled by design; non-fatal so
re-enabling them cannot take the site down again; last so that even a failure
mode this script does not model leaves a built site behind.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

import cityconfig


def run(label: str, cmd: list[str], *, optional: bool = False) -> bool:
    """Run one step. Returns True if it succeeded.

    A REQUIRED step's failure stops the build, because everything after it
    would be assembled from half-finished inputs. An OPTIONAL step's failure
    is reported and skipped: it is a step the pipeline can be complete
    without, and one deliberately-disabled step must never be able to make
    the rest of the site unbuildable. See the module docstring.
    """
    print(f"\n• {label}\n  $ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode == 0:
        return True
    if optional:
        print(f"  !! {label} declined (exit {result.returncode}). It is "
              f"optional — the build continues without it.")
        return False
    raise SystemExit(f"\n{label} failed — stopping before the site is "
                     f"built from half-finished inputs.")


def plan(args, city) -> list[tuple[str, list[str], bool]]:
    """The ordered step list: ``(label, command, optional)``.

    Separated from :func:`main` so the order can be asserted without running
    anything — `build_site` and `build_portal` were unreachable here for as
    long as nothing could look at this list. See `tests/test_build_all.py`.
    """
    py = sys.executable
    c = ["--city", city.slug]
    steps: list[tuple[str, list[str], bool]] = []

    # STEP 0: THE POLL REGISTER, BEFORE ANYTHING IS PUBLISHED. A malformed
    # record used to be dropped in silence, so a `scope` of "Metro" or a typo'd
    # `city` could take a poll out of the forecast and out of the published page
    # with no warning anywhere. Cheap, and it runs before the slow steps so a
    # bad record costs a second rather than a full build. MODEL-LOG §1.68.
    steps.append(("poll register", [py, "-c",
                                    "import sys; sys.path.insert(0, 'src'); "
                                    "import polling; polling.validate_or_die(); "
                                    "print('  polls.json: no malformed records')"],
                  False))

    if args.model:
        steps.append(("Monte Carlo", [py, "src/montecarlo.py", *c], False))
    if args.regimes:
        steps.append(("overhang counterfactuals",
                      [py, "src/overhang_regimes.py"], False))

    steps.append(("ward map", [py, "src/render_map.py", *c], False))
    # The equal-ward cartogram, behind the map's toggle. After render_map, whose
    # ward_paths.json it reads; one splice per page that carries the markers.
    for page in ("forecast-sheet.html", "drafts/forecast-draft.html"):
        steps.append((f"ward cartogram → {page}",
                      [py, "src/hex_cartogram.py", "--into", page], False))
    steps.append(("sheet figures, claims, regimes",
                  [py, "src/render_sheet.py", *c], False))
    steps.append(("site", [py, "src/build_site.py"], False))
    steps.append(("portal", [py, "src/build_portal.py"], False))

    # LAST, AND OPTIONAL. `build_interactive.py` refuses at import (not ported
    # to voter pools); `export_interactive.py` only feeds it, so both are
    # behind the same flag rather than paying for a data pack nothing reads.
    if args.interactive:
        steps.append(("interactive data pack",
                      [py, "src/export_interactive.py", *c], True))
        steps.append(("interactive page",
                      [py, "src/build_interactive.py", *c], True))

    if args.deploy:
        steps.append(("deploy", ["npx", "wrangler", "deploy"], False))
    return steps


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    cityconfig.add_city_argument(ap)
    ap.add_argument("--model", action="store_true",
                    help="re-run the Monte Carlo before rendering (slow)")
    ap.add_argument("--regimes", action="store_true",
                    help="also re-run the overhang counterfactuals (slower)")
    ap.add_argument("--deploy", action="store_true",
                    help="publish afterwards with wrangler")
    ap.add_argument("--interactive", action="store_true",
                    help="also rebuild the interactive page. OFF by default: "
                         "it is not ported to voter pools and refuses. The "
                         "step is optional, so its refusal no longer stops "
                         "the site and portal from being built.")
    args = ap.parse_args(argv)

    city = cityconfig.use(args.city)

    print(f"building {city.name} ({city.code}) — council {city.council}, "
          f"majority {city.majority}, {city.wards} wards")

    declined: list[str] = []
    for label, cmd, optional in plan(args, city):
        if not run(label, cmd, optional=optional):
            declined.append(label)

    if declined:
        print(f"\nskipped optional step(s): {', '.join(declined)}")
    if not args.deploy:
        print("\nnot deployed. To publish:"
              "\n  env -u CLOUDFLARE_API_TOKEN npx wrangler deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
