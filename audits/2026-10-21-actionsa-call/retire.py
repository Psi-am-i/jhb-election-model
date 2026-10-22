"""Retire the published tokens the 21 October build no longer writes.

`build_site.py` refuses a build while a published token has left the registry
unretired. The 16 October list (`audits/2026-10-11-model-round/step11_retire.py`)
is not reused: that build never reached the real ledger, and most of its
tokens are written again by this one. The publish build against a copy of
the ledger named exactly these. Run against a copy for UAT and once against
the real ledger before the live `build_site.py --publish`:

    .venv/bin/python audits/2026-10-21-actionsa-call/retire.py            # real ledger
    .venv/bin/python audits/2026-10-21-actionsa-call/retire.py --root DIR # a copy

A token already retired in the target ledger is skipped.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import publication as P  # noqa: E402

GROUP = ("This population-group share of the party's vote is now below the "
         "chart's label threshold (build_play.SEGMENT_LABEL_MIN), so the figure "
         "is no longer printed. The bar segment is still drawn.")
TILE = ("This party now triggers the excessive-seats clause in fewer simulations "
        "than the tile names a party at (scenarios.EXCESSIVE_FLOOR), so the tile "
        "does not name it.")

ANC_BOX = ("The ANC claim's 'what the model says now' box was rewritten for the "
           "16 October forecast (owner, 2026-10-16): the ANC reaches a majority "
           "alone in none of the simulations, said in words, so its share is not printed.")
DA_BOX = ("The 490,000 claim's 'what the model says now' box was replaced by the "
          "owner's text (2026-10-16): the DA wins a majority alone in none of the "
          "simulations, so the count, the share and the ward-wall figures are not printed.")
COAL = ("This coalition is no longer a smallest majority in at least 5% of "
        "simulations (render_sheet MIN_SMALLEST), so the who-can-govern table "
        "does not list it.")
BYE = ("The forecast now counts by-elections at half weight, so the line under "
       "the by-election control compares each setting with that; this party's "
       "seats at this setting are no longer listed there.")
SPLIT = ("MK's split between ANC areas and the city average was an assumption. "
         "MK is now placed from its own 2024 national result by ward, so the "
         "assumed split is not printed.")
CENSUS = ("The forecast now splits each ward's registered voters by that ward's "
          "census population shares and uses no census adult counts, so this "
          "comparison of adults with registered voters is not printed.")

COALITIONS = {
    "ANC+ASA+EFF+MK": ("ANC", "ASA", "EFF", "MK"),
    "ANC+ASA+EFF+PA": ("ANC", "ASA", "EFF", "PA"),
    "ANC+EFF+PA": ("ANC", "EFF", "PA"),
    "ANC+PA+MK": ("ANC", "MK", "PA"),
    "ASA+EFF+PA+MK": ("ASA", "EFF", "MK", "PA"),
    "DA+ASA+EFF+MK": ("ASA", "DA", "EFF", "MK"),
    "DA+ASA+EFF+PA": ("ASA", "DA", "EFF", "PA"),
    "DA+EFF+PA": ("DA", "EFF", "PA"),
    "DA+PA+MK": ("DA", "MK", "PA"),
}

RETIRE = {
    "play.votes.MK.white": GROUP,
    "play.votes.RISE.coloured": GROUP,
    "tile.p_excessive.eff": TILE,
    "claim.anc_alone.share": ANC_BOX,
    **{f"claim.da_alone.{k}": DA_BOX
       for k in ("count", "share", "wall_anc_low", "wall_anc_top", "wall_count", "wall_flips")},
    **{f"coal.{c}.{k}": COAL
       for c, ms in COALITIONS.items()
       for k in ("cushion_when_wins", "majority", "seats_when_wins", "stability",
                 *(f"survive.{m}" for m in ms))},
    **{f"play.bye.w_bye_0.{p}": BYE
       for p in ("ALJAMAAH", "ALL_CITIZENS_PARTY", "ASA", "MK", "PA", "RISE")},
    **{f"play.bye.w_bye_1.{p}": BYE
       for p in ("ALL_CITIZENS_PARTY", "ASA", "MK")},
    "play.splinter.MK.city": SPLIT,
    "play.splinter.MK.parent": SPLIT,
    "hist_census_white_adults": CENSUS,
    "hist_roll_white_voters": CENSUS,
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
