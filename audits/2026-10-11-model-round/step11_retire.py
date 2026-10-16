"""Retire the published tokens the 16 October build no longer writes (11 + 24).

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

ANC_BOX = ("The ANC claim's 'what the model says now' box was rewritten for the "
           "16 October forecast (owner, 2026-10-16): the ANC reaches a majority "
           "alone in none of the simulations, said in words, so its share is not printed.")
DA_BOX = ("The 490,000 claim's 'what the model says now' box was replaced by the "
          "owner's text (2026-10-16): the DA wins a majority alone in none of the "
          "simulations, so the count, the share and the ward-wall figures are not printed.")
COAL = ("This coalition is no longer a smallest majority in at least 5% of "
        "simulations (render_sheet MIN_SMALLEST), so the who-can-govern table "
        "does not list it.")
TILE = ("This party now triggers the excessive-seats clause in fewer simulations "
        "than the tile names a party at (scenarios.EXCESSIVE_FLOOR), so the tile "
        "does not name it.")

#: Retired by the 16 October regenerated sheet (render_sheet on the new run).
SHEET = {
    "claim.anc_alone.share": ANC_BOX,
    **{f"claim.da_alone.{k}": DA_BOX
       for k in ("count", "share", "wall_anc_low", "wall_anc_top", "wall_count", "wall_flips")},
    **{f"coal.{c}.{k}": COAL
       for c, ms in (("ANC+PA+MK", ("ANC", "MK", "PA")), ("ASA+EFF+PA+MK", ("ASA", "EFF", "MK", "PA")))
       for k in ("cushion_when_wins", "majority", "seats_when_wins", "stability",
                 *(f"survive.{m}" for m in ms))},
    "tile.p_excessive.eff": TILE,
    "tile.p_excessive.mk": TILE,
}

RETIRE = {
    **{f"play.bye.w_bye_0.{p}": BYE
       for p in ("ALJAMAAH", "ALL_CITIZENS_PARTY", "ANC", "ASA", "MK", "PA", "RISE")},
    "play.splinter.MK.city": SPLIT,
    "play.splinter.MK.parent": SPLIT,
    "play.votes.MK.white": GROUP,
    "play.votes.RISE.coloured": GROUP,
    **SHEET,
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
