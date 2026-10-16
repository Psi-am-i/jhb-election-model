"""Retire the eleven published tokens the 16 October build no longer writes.

`build_site.py` refuses a build while a published token has left the registry
unretired. The UAT build ran this against a scratch copy of the ledger. Live
promotion runs it once against the real ledger, before `build_site.py
--publish`:

    .venv/bin/python audits/2026-10-11-model-round/step11_retire.py            # real ledger
    .venv/bin/python audits/2026-10-11-model-round/step11_retire.py --root DIR # a copy

Each token was last published 2026-10-11 (run r-c68c627d287e-e6f5c4f1-dirty).
A token already retired in the target ledger is skipped, so a second run
appends nothing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import publication as P  # noqa: E402

BYE = ("The line under the by-election control compared the weight-0 cell with "
       "the forecast. The forecast's by-election weight is now 0, so that cell "
       "is the forecast and no party's seats move.")
SPLIT = ("MK's split between ANC areas and the city average was an assumption. "
         "MK is now placed from its own 2024 national result by ward, so the "
         "assumed split is not printed.")
GROUP = ("This population-group share of the party's vote is now below the "
         "chart's label threshold (build_play.SEGMENT_LABEL_MIN), so the figure "
         "is no longer printed. The bar segment is still drawn.")

RETIRE = {
    **{f"play.bye.w_bye_0.{p}": BYE
       for p in ("ALJAMAAH", "ALL_CITIZENS_PARTY", "ANC", "ASA", "MK", "PA", "RISE")},
    "play.splinter.MK.city": SPLIT,
    "play.splinter.MK.parent": SPLIT,
    "play.votes.MK.white": GROUP,
    "play.votes.RISE.coloured": GROUP,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=None,
                    help="ledger root (default: the real publications/)")
    args = ap.parse_args(argv)
    root = args.root or (REPO / P.LEDGER_ROOT)
    latest = P.latest("joburg", root=root)
    for token, reason in RETIRE.items():
        row = latest.get(token)
        if row is None:
            print(f"  ? {token}: not in the ledger at {root}")
            continue
        if row.superseded_at:
            print(f"  - {token}: already retired {row.superseded_at}")
            continue
        P.retire("joburg", token, reason=reason, change_class="mechanism", root=root)
        print(f"  ✓ {token} retired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
