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

    **THE MAJORITY CLAIM DID NOT SURVIVE THE PANEL DOUBLING, AND THIS TEST NO
    LONGER MAKES IT (MODEL-LOG §1.77).** §1.59 measured 20 of 37 — a majority —
    on nine city-years, and asserted `hit > total / 2` on the strength of it. On
    the sixteen city-years §1.70 opened up it is **26 of 64**, and the top-bin
    dispersion the floor was promoted for landed at 0.273 against a used 0.158.
    So the assertion below is now the STRUCTURAL claim, which is what the name
    of this test says and what is robust to how many city-years exist: the floor
    binds at the top of the ballot, it binds there materially, and it binds
    nowhere below 5%. The MAGNITUDE claim moved to §1.77 where the measurement
    that would refute it is recorded next to it.
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
    assert hit, (
        f"SD_FLOOR={levels.SD_FLOOR} no longer binds on ANY of the {total} "
        f"observations at or above 15% of the vote. The fit has risen clear of "
        f"the floor everywhere, so 'the floor is what puts the large-party "
        f"width on the measurement' — §1.59's first finding, and the reason "
        f"JUDGEMENT-CALLS carries SD_FLOOR at 🟢 on the top bin — is dead "
        f"rather than merely weakened. Re-run `src/theta_residual.py` and "
        f"rewrite that row.")
    assert hit * 3 > total, (
        f"SD_FLOOR={levels.SD_FLOOR} binds on {hit} of {total} observations at "
        f"or above 15% of the vote — under a third. §1.59 measured 20 of 37 on "
        f"nine city-years and §1.77 measured 26 of 64 on sixteen; a further "
        f"fall means the fit is rising through the floor and the constant is "
        f"on its way to inert. That is a finding, not a failure: measure it, "
        f"write it up, and move this bound.")
    # WHERE §1.59's SECOND FINDING ACTUALLY LIVES is below 1% of the vote —
    # the two bands carrying 250 of the 314 sub-5% observations and the two
    # whose intervals exclude the model's width most comfortably. Nothing may
    # sit on the floor there, or the finding is measuring the floor.
    tiny = sum(on_floor(b)[0] for b in ("<0.2%", "0.2-1%"))
    assert tiny == 0, (
        f"SD_FLOOR binds on {tiny} observations below 1% of the vote. §1.59's "
        f"second finding — that the prior is 1.7x to 3.5x too NARROW across "
        f"the small and middle ballot — is measured against the FIT, and the "
        f"floor setting the width for any of those parties would partly "
        f"measure the floor instead. Re-run `src/theta_residual.py` before "
        f"quoting it.")
    # BETWEEN 1% AND 5% A HANDFUL IS TOLERATED, AND EXACTLY ONE IS EXPECTED.
    # This was `== 0` until 2026-08-23 and it began failing when §1.70 doubled
    # the panel — not because the floor spread, but because the enlarged record
    # admits a TARGET 2011 fit at all, and 2011 is the target with the least
    # history behind its `sd_for` line. The single case is MINORITY_FRONT at
    # eThekwini, target 2011, at **4.7997% of the vote** — a fifth of a point
    # under the bin edge, in the one fold whose line is built on two prior
    # cycles. The next smallest fitted width below 5% is 0.1773, well clear.
    # So: one boundary observation, not a floor that has started setting the
    # mid-ballot width. MODEL-LOG §1.77.
    mid = on_floor("1-5%")[0]
    below5 = sum(on_floor(b)[1] for b in ("<0.2%", "0.2-1%", "1-5%"))
    assert mid * 50 <= below5, (
        f"SD_FLOOR binds on {mid} of the {below5} observations below 5% of the "
        f"vote — over 2%, where §1.77 recorded exactly one boundary case at "
        f"4.7997%. The floor has started setting the width inside the band "
        f"§1.59 says is too narrow, which would partly mask that finding. "
        f"Re-run `src/theta_residual.py`, identify the observations, and say "
        f"whether this is still a bin edge or a real spread.")


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
