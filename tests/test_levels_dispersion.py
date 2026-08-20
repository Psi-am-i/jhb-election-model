"""CLASS 14 — A MEASUREMENT WHOSE SUBJECT CAN MOVE UNDER IT.

`src/theta_residual.py` answers the question MODEL-LOG §1.50 asserted an answer
to and never computed: what IS the conditional dispersion of log θ about the
centre `theta_prior` would have used? Its table is quoted in §1.59, in
`JUDGEMENT-CALLS.md` against `SD_FLOOR`, and in its own docstring — three places
that go stale silently if the thing being measured changes shape.

**The first version of that module was wrong, and this file is why it was caught
in minutes rather than after being quoted.** It rebuilt `levels.sd_for` outside
its closure, because `sd_for` is defined inside `theta_prior` and cannot be
called from anywhere else. The rebuild fed it each party's *historical* sizes;
the real one regresses on ``baseline.get(party)``, the party's size at the
TARGET. Different line, different answer — 0.530 against the model's 0.150 at
0.1% of the vote. The module now takes both the centre and the width from
`theta_prior` itself and rebuilds nothing.

What is left to guard is the three claims the write-ups actually lean on.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import cityconfig  # noqa: E402
import levels  # noqa: E402
import theta_residual as TR  # noqa: E402


def test_the_harness_takes_its_width_from_the_model_and_never_rebuilds_it():
    """Every measured row carries a width `theta_prior` actually returned.

    A ``nan`` here means the party got a residual but no width, so the ratio
    column in §1.59 is being computed over a different population than the
    dispersion column — the exact shape of error that produced §1.55's backwards
    result one file over.
    """
    rows = TR.residuals()
    assert rows, "no residuals at all — the harness is not reading the archive"
    missing = [r for r in rows if not (r[2] == r[2])]
    assert not missing, (
        f"{len(missing)} of {len(rows)} residual rows carry no fitted width "
        f"(first: {missing[0][3]} at {missing[0][5]} {missing[0][4]}). "
        f"`theta_prior`'s `groups['sd']` no longer covers every party it "
        f"returns a prior for, so §1.59's `sd_for` column and its `measured` "
        f"column are over different populations.")
    # and it must be the model's own number, not a lookalike
    year = sorted({r[4] for r in rows})[-1]
    code = next(r[5] for r in rows if r[4] == year)
    target = cityconfig.use_target(year)
    npe = cityconfig.preceding(year, "NPE")
    before = levels._citywide(
        "data/raw/elections/"
        + cityconfig.CALENDAR[npe].results.replace("{CODE}", code))
    _priors, groups = levels.theta_prior(target, before)
    for size, _resid, width, party, y, c, _had in rows:
        if y != year or c != code:
            continue
        assert abs(width - float(groups["sd"][party])) < 1e-12, (
            f"{party} at {code} {year}: the harness recorded width {width:.6f} "
            f"and `theta_prior` returns {groups['sd'][party]:.6f}. The harness "
            f"has acquired a second copy of the dispersion fit.")


def test_the_floor_binds_at_the_top_of_the_ballot_and_only_there():
    """§1.59's first finding is that `SD_FLOOR` — not the fit — sets the width
    for large parties, and that the measurement lands on it.

    If the fit ever rises above the floor at 40% of the vote, "the floor is
    doing the work, not the fit" is stale. If the floor ever binds in the
    MIDDLE of the ballot, §1.59's second finding — that the prior is 1.7x to
    3.5x too narrow across 0.2% to 15% — would be partly masked by it, because
    the floor would be widening the very band the finding is about.
    """
    rows = TR.residuals()
    widths = {}
    for size, _resid, width, _party, _y, _c, _had in rows:
        widths.setdefault(_bin_of(size), []).append(width)
    def on_floor(band):
        w = widths.get(band, [])
        return sum(1 for x in w if abs(x - levels.SD_FLOOR) < 1e-12), len(w)

    hit, total = on_floor(">=15%")
    assert total, "no parties at or above 15% of the vote — the archive is wrong"
    assert hit > total / 2, (
        f"SD_FLOOR={levels.SD_FLOOR} now binds on only {hit} of {total} "
        f"observations at or above 15% of the vote. §1.59 reports 20 of 37 and "
        f"reads the floor as what puts the large-party width on the "
        f"measurement; if the fit has risen clear of it, that reading is "
        f"stale. Re-run `src/theta_residual.py`.")
    low = sum(on_floor(b)[0] for b in ("<0.2%", "0.2-1%", "1-5%"))
    assert low == 0, (
        f"SD_FLOOR now binds on {low} observations below 5% of the vote, so it "
        f"is setting the width inside the band §1.59 says is 1.7x to 3.5x too "
        f"NARROW. That finding is measured against the fit and would be partly "
        f"masked by the floor. Re-run `src/theta_residual.py` before quoting "
        f"the second finding.")


def test_the_residuals_are_forward_validated():
    """No residual may be measured against a centre that saw its own outcome.

    The whole value of §1.59 is that it is out of sample. `theta_record`
    enforces "strictly before the target"; this asserts the consequence, which
    is the part a reader relies on: the earliest local election in the calendar
    contributes NO residuals, because there is nothing before it to build a
    centre from.
    """
    rows = TR.residuals()
    lge = sorted((y for y, e in cityconfig.CALENDAR.items()
                  if e.kind == "LGE" and e.results), key=int)
    measured = {r[4] for r in rows}
    assert lge[0] not in measured, (
        f"{lge[0]} is the first local election in the calendar and it "
        f"contributes residuals, so something built a centre from a record "
        f"that cannot exist. `theta_record`'s 'strictly before the target' "
        f"contract is broken and §1.59 is an in-sample result.")
    assert measured <= set(lge[1:]), (
        f"residuals measured at {sorted(measured - set(lge[1:]))}, which are "
        f"not local elections with results")


def _bin_of(size: float) -> str:
    for (lo, hi), name in zip(TR.BINS,
                              ("<0.2%", "0.2-1%", "1-5%", "5-15%", ">=15%")):
        if lo <= size < hi:
            return name
    return ">=15%"


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
