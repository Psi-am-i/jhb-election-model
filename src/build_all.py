"""Build one city end to end, then the site around it.

    python src/build_all.py --city joburg           # renders + site
    python src/build_all.py --city joburg --model   # re-run the model first

The model step is separate and opt-in because it takes minutes and its
output is deterministic — there is no point re-running 5,000 draws to fix a
sentence. Everything downstream of it is cheap and always runs.

Each step is echoed with its command so a failure can be reproduced by hand,
and the run stops at the first failure rather than building half a site.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import cityconfig


def run(label: str, cmd: list[str]) -> None:
    print(f"\n• {label}\n  $ {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"\n{label} failed — stopping before the site is "
                         f"built from half-finished inputs.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    cityconfig.add_city_argument(ap)
    ap.add_argument("--model", action="store_true",
                    help="re-run the Monte Carlo before rendering (slow)")
    ap.add_argument("--regimes", action="store_true",
                    help="also re-run the overhang counterfactuals (slower)")
    ap.add_argument("--deploy", action="store_true",
                    help="publish afterwards with wrangler")
    args = ap.parse_args(argv)

    city = cityconfig.use(args.city)
    py = sys.executable
    c = ["--city", city.slug]

    print(f"building {city.name} ({city.code}) — council {city.council}, "
          f"majority {city.majority}, {city.wards} wards")

    if args.model:
        run("Monte Carlo", [py, "src/montecarlo.py", *c])
    if args.regimes:
        run("overhang counterfactuals", [py, "src/overhang_regimes.py"])

    run("interactive data pack", [py, "src/export_interactive.py", *c])
    run("ward map", [py, "src/render_map.py", *c])
    run("sheet figures, claims, regimes", [py, "src/render_sheet.py", *c])
    run("interactive page", [py, "src/build_interactive.py", *c])
    run("site", [py, "src/build_site.py"])
    run("portal", [py, "src/build_portal.py"])

    if args.deploy:
        run("deploy", ["npx", "wrangler", "deploy"])
    else:
        print("\nnot deployed. To publish:"
              "\n  env -u CLOUDFLARE_API_TOKEN npx wrangler deploy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
