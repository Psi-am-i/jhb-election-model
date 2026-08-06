"""Run the excessive-seats counterfactuals for the regime-comparison table.

Three answers to the same arithmetic (a party winning more wards than its
proportional share):

* ``deduct`` — South African law as amended (Act 3/2021): council fixed at
  270, the winner keeps its wards, everyone else is squeezed. This is the
  published reference run and is NOT re-run here.
* ``expand`` — the old-Germany answer (pre-2013 Überhangmandate) and this
  project's pre-research reading: the council grows by the excess.
* ``level`` — the modern-Germany answer (Ausgleichsmandate): the council
  grows until every ward winner is covered proportionally; nobody pays.

Each counterfactual is a full run at the published seed, so the table on the
forecast sheet compares the SAME 5,000 simulated elections under different
law. Outputs land as data/processed/regime_{rule}_summary.json and
regime_{rule}_seat_draws.csv, and the reference outputs are restored by
re-running the default rule afterwards (deterministic seed — bit-identical).

Usage:
    python src/overhang_regimes.py          # then: python src/render_sheet.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import montecarlo

PROCESSED = Path("data/processed")


def main() -> int:
    for rule in ("expand", "level"):
        print(f"\n=== overhang_rule={rule} ===")
        montecarlo.main(["--set", f"overhang_rule={rule}"])
        shutil.copy(PROCESSED / "forecast_summary.json",
                    PROCESSED / f"regime_{rule}_summary.json")
        shutil.copy(PROCESSED / "seat_draws.csv",
                    PROCESSED / f"regime_{rule}_seat_draws.csv")
    print("\n=== restoring the reference (default rule) ===")
    montecarlo.main([])
    return 0


if __name__ == "__main__":
    sys.exit(main())
