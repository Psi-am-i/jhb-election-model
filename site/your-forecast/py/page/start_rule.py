"""Where a reader's own forecast starts: seats per party, then the vote that gives them.

ONE DEFINITION for both places a reader's forecast is opened from the model's
draws (owner, 2026-10-03):

* the build (``build_make.start_state``) writes the start of "Break the model"
  on ``/your-forecast/`` from the published draws, each draw counted once;
* the page (``interactive/pyboot/page.py``'s ``handoff``) opens the same section
  from the reader's "Adjust the model" settings, with the draws weighted as
  those settings weight them (``reweight``).

With unit weights the two are the same call, and
``tests/test_your_forecast_page.py`` holds them equal.

The rule (the vote-share half of ``build_make``'s start, steps 1-5)
=================================================================

1. **Targets.** Each party the seat panel names (``scenarios.NAMED_PARTIES``)
   gets its middle seat count under the weights, and "Others" (every other
   party) the middle of the seats they hold within each draw; both by
   ``reweight.weighted_quantile`` at one half, rounded to a whole seat. With
   unit weights this is ``scenarios.seat_quantiles``' median on the draws.
2. **The ward floor.** A party holds at least the wards it is called for, so a
   target below that count is raised to it.
3. **The council's size.** The seats left over (or missing) go to (or come
   from) "Others", the remainder row. Only if taking the missing seats would put
   Others below its ward floor are they taken one per row per round instead,
   from the rows whose weighted mean over the draws falls furthest below their
   middle, never below a row's ward floor.
4. **Others** is split among its parties by largest remainder on each party's
   weighted mean seats over the draws, none below its ward floor.
5. **Votes.** Each party's combined vote is its target seats' share of the
   council, in whole votes of the total by largest remainder; a party with no
   target seat gets none.

Imported by the page under Pyodide, so it imports only numpy, ``reweight`` and
``scenarios`` (``interactive/tools/sync_py.mjs`` PAGE_FILES, measured by
``interactive/tests/page.test.mjs``).
"""
from __future__ import annotations

import math

import numpy as np

import reweight as R
import scenarios


class StartRuleError(ValueError):
    """The draws cannot give a start by this rule; the message says why."""


def apportion(weights: dict, total: int, floors: dict) -> dict:
    """Whole numbers summing to ``total`` in proportion to ``weights``, none
    below its ``floors`` entry: largest remainder, ties by input order."""
    fixed: dict = {}
    while True:
        free = [k for k in weights if k not in fixed]
        left = total - sum(fixed.values())
        w = math.fsum(weights[k] for k in free)
        raw = {k: (left * weights[k] / w if w > 0 else left / len(free)) for k in free}
        under = [k for k in free if raw[k] < floors.get(k, 0)]
        if not under:
            break
        for k in under:
            fixed[k] = floors.get(k, 0)
    out = {k: math.floor(v) for k, v in raw.items()}
    spare = total - sum(fixed.values()) - sum(out.values())
    for k in sorted(raw, key=lambda k: -(raw[k] - out[k]))[:spare]:
        out[k] += 1
    out.update(fixed)
    return {k: out[k] for k in weights}


def start_seats(parties: list[str], seats, council_draws, calls: list[str],
                weights=None) -> dict:
    """The council a reader's forecast opens with, steps 1-4 of the module
    docstring. ``parties`` are the columns of ``seats`` (``(draws, parties)``,
    the draws' ``seats/deduct`` block); ``council_draws`` each draw's council
    size under the statute; ``calls`` the ward winners. Unit weights when
    ``weights`` is None.

    Returns ``{"seats", "published", "rows"}``: the target per party (zeros
    left out), each panel row's middle, and each row's target.
    """
    S = np.asarray(seats, dtype=float)
    w = R.uniform(S.shape[0]) if weights is None else np.asarray(weights, dtype=float)
    p = w / w.sum()
    council_draws = np.asarray(council_draws, dtype=float)
    council = int(round(float(np.median(council_draws))))
    if not np.all(council_draws == council):
        raise StartRuleError("the draws' council size varies under the statutory law")
    col = {c: j for j, c in enumerate(parties)}
    named = [c for c in scenarios.NAMED_PARTIES if c in col]
    others = [c for c in parties if c not in named]
    held = {c: 0 for c in parties}
    for c in calls:
        held[c] += 1
    series = {c: S[:, col[c]] for c in named}
    series["OTHERS"] = council_draws - sum(series[c] for c in named)
    middle = {g: int(round(R.weighted_quantile(x, w, 0.5))) for g, x in series.items()}
    floor = {c: held[c] for c in named}
    floor["OTHERS"] = sum(held[c] for c in others)
    rows = {g: max(middle[g], floor[g]) for g in series}
    gap = {g: float(p @ series[g]) - middle[g] for g in series}
    order = list(series)
    left = council - sum(rows.values())
    # step 3: Others is the remainder row
    take = left if rows["OTHERS"] + left >= floor["OTHERS"] else floor["OTHERS"] - rows["OTHERS"]
    rows["OTHERS"] += take
    left -= take
    while left:
        step = 1 if left > 0 else -1
        ranked = sorted(order, key=lambda g: (-gap[g] * step, order.index(g)))
        moved = False
        for g in ranked:
            if left == 0:
                break
            if step < 0 and rows[g] <= floor[g]:
                continue
            if step > 0 and rows[g] < floor[g]:
                continue
            rows[g] += step
            left -= step
            moved = True
        if not moved:
            raise StartRuleError("the panel's rows cannot fill the council above their ward floors")
    split = apportion({c: float(p @ S[:, col[c]]) for c in others}, rows["OTHERS"],
                      {c: held[c] for c in others})
    out = {c: rows[c] for c in named}
    out.update(split)
    return {"seats": {c: n for c, n in out.items() if n}, "published": middle, "rows": rows}


def start_shares(seats: dict, roster: list[str], total: int) -> dict:
    """Step 5: each party's combined vote as a percent of ``total``, from
    whole votes in proportion to its target seats."""
    votes = apportion({c: float(seats.get(c, 0)) for c in roster}, total, {})
    return {c: votes[c] / total * 100 for c in roster}
