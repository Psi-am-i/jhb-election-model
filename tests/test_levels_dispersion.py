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
    # AND IT MUST BE THE MODEL'S OWN NUMBER, NOT A LOOKALIKE — including the
    # BASELINE. `run_model` drops parties that are not on the target's ballot
    # before it calls `theta_prior`, and `sd_for`'s fit is built off whatever
    # baseline it is handed, so passing the raw citywide tally here fits a
    # different line and returns a different width for EVERY party. This test
    # rebuilt with the raw tally until 2026-08-28 and agreed with a harness
    # that was making the same mistake. MODEL-LOG §1.124.
    #
    # Every metro-year, not one: the divergence that was missed was largest at
    # metros with the most off-ballot parties, and a single spot-check is how
    # it survived. Costs nothing — `residuals` is memoised and `theta_prior` is
    # cheap next to it.
    for year in sorted({r[4] for r in rows}):
        for code in sorted({r[5] for r in rows if r[4] == year}):
            _check_one(rows, year, code)


def _check_one(rows, year, code):
    target = cityconfig.use_target(year)
    npe = cityconfig.preceding(year, "NPE")
    lge_tpl = cityconfig.CALENDAR[year].results
    before = levels._citywide(
        "data/raw/elections/"
        + cityconfig.CALENDAR[npe].results.replace("{CODE}", code))
    for gone in levels.absent_from_ballot(
            before, levels.ballot_roster(
                "data/raw/elections/" + lge_tpl.replace("{CODE}", code))):
        before.pop(gone, None)
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
        f"nine city-years, §1.77 measured 26 of 64 on sixteen, and §1.124 "
        f"measures 32 of 64 once the harness uses the baseline `run_model` "
        f"actually passes; a fall means the fit is rising through the floor "
        f"and the constant is on its way to inert. That is a finding, not a "
        f"failure: measure it, write it up, and move this bound.")
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
    # BETWEEN 1% AND 5% A HANDFUL IS TOLERATED. IT IS CURRENTLY ZERO.
    # This was `== 0` until 2026-08-23, when §1.70's doubled panel admitted a
    # TARGET 2011 fit and MINORITY_FRONT at eThekwini — 4.7997% of the vote, a
    # fifth of a point under the bin edge — landed on the floor. **It is off it
    # again as of §1.124**: correcting the harness to use `run_model`'s
    # baseline WIDENS the fit below 5% (median width 0.272 → 0.300 in this
    # band) and narrows it at the top, because the off-ballot parties being
    # dropped sit at the small end of the size axis where the slope is
    # steepest. The bound is kept loose rather than tightened back to `== 0`:
    # one boundary observation is not a finding either way, and re-tightening
    # would make a bin edge into a tripwire. MODEL-LOG §1.77, §1.124.
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


# --------------------------------------------------------------------------
# KEY 4's INSTRUMENT. MODEL-LOG §1.124.
# --------------------------------------------------------------------------

# The Key-4 baselines, re-recorded 2026-08-28 when the instrument was fixed
# three ways in one commit: the baseline `residuals` passes `theta_prior` became
# the one `run_model` passes (off-ballot parties dropped), the score became the
# Student-t the model DRAWS rather than a Gaussian it does not, and the log
# score's constant is carried. **Re-record these deliberately and say why here.**
# A silent re-record destroys the only guard on an untradeable floor.
#
#   before, Gaussian without its constant, raw baseline:  2016 1.3241  2021 0.5791
#   after,  t7 with constants, model baseline:            2016 1.1363  2021 1.1425
#
# Note what the fix did to the SHAPE: under the Gaussian the two folds looked
# 2.3x apart, and under the predictive the model actually draws they are within
# 0.006 nats of each other. The spread was the Gaussian tail penalty on three
# known party-structural events, not a property of the width layer.
KEY4_BASELINE = {"2016": 1.1363, "2021": 1.1425}


def test_key_4_is_scored_on_the_width_the_model_actually_used():
    """`held_out_nll`'s COMMITTED column, not its A column, is the floor.

    **This test exists because the two were confused for three months.**
    `ITERATING.md`'s Key 4 said, verbatim, "Held-out NLL on `theta_residual`'s
    folds must not worsen in either fold", and the stage-1 table it pointed at
    labelled column A "committed". `form_a`'s own docstring says it is not: its
    fit regresses on the record's own reliability-weighted size where
    `levels.sd_for` regresses on ``baseline.get(party)``, and it is fitted once
    per fold where `sd_for` is refitted per metro-year. So an untradeable floor
    was being read off an estimator the model does not run — the same seam
    `DUPLICATION-AUDIT.md` flagged from the other side.

    Asserted here: COMMITTED scores `theta_prior`'s own widths, recomputed
    independently of `held_out_nll`'s loop; every row is scored, so the column
    is comparable with A/B/C; and the recorded baselines still hold.
    `test_a_change_to_levels_moves_key_4` carries the mechanism half.
    """
    rows = TR.residuals()
    table = TR.held_out_nll()

    by_target: dict[str, list] = {}
    for row in rows:
        by_target.setdefault(row[4], []).append(row)

    for year, entry in table.items():
        blk = entry["COMMITTED"]
        assert blk, f"fold {year} has no COMMITTED column at all"
        # EVERY ROW MUST BE SCORED, or COMMITTED's mean is over a different
        # population than A/B/C's and the columns cannot be read against each
        # other. A `nan` width is structurally unreachable today — every party
        # `residuals` emits is in the baseline, hence in `priors`, hence a key
        # of `groups["sd"]` — and this is what says so if that ever changes.
        assert blk["unscored"] == 0, (
            f"fold {year}: {blk['unscored']} observations have no usable "
            f"width, so COMMITTED is averaged over {blk['n']} where A/B/C are "
            f"averaged over {entry['n']}. Two means over different "
            f"populations are not a comparison.")
        assert blk["n"] == entry["n"] == len(by_target[year])

        scored = [(r[1], r[2], (r[4], r[5])) for r in by_target[year]]
        mine = sum(TR.nll_t(resid, w) for resid, w, _ in scored) / len(scored)
        assert abs(mine - blk["mean"]) < 1e-9, (
            f"fold {year}: COMMITTED reports {blk['mean']:.6f}; scoring "
            f"`theta_prior`'s own widths under the same predictive gives "
            f"{mine:.6f}. The column is no longer the committed estimator.")

    for year, expected in KEY4_BASELINE.items():
        got = table[year]["COMMITTED"]["mean"]
        assert abs(got - expected) < 5e-4, (
            f"KEY 4, fold {year}: the committed held-out NLL is {got:.4f} "
            f"against a recorded {expected:.4f}. `ITERATING.md` declares this "
            f"floor UNTRADEABLE, so a move is either a finding or a "
            f"regression and it is never nothing. Measure it with "
            f"`theta_residual.key4_delta` — a bare difference of means is not "
            f"a comparison — then re-record the constant above WITH THE "
            f"REASON.")


def test_a_change_to_levels_moves_key_4():
    """The invariant whose absence caused the bug: the floor must be LIVE.

    `form_a` is rebuilt from `_fit_line` and reaches `levels` only through the
    clamp, so a change to `sd_for`'s covariate or weighting moves the model and
    leaves A exactly where it was. That is the defect, stated as a property,
    and it is the thing worth testing — an assertion that COMMITTED merely
    *differs* from A by some margin would go stale the moment someone improved
    the width layer, which is what Key 4 exists to encourage.

    **This also guards the memo.** `residuals` is `lru_cache`d, and
    `test_levers_are_live._patched` sets `levels` constants process-globally
    and restores them in a `finally` — which cannot invalidate a cache. The
    cache is therefore keyed on `_levels_state()`, and the third leg below is
    what says so: after the patch is restored, the original answer must come
    back, not the patched one.

    One metro, because the property is per-observation and eight would cost
    45 seconds to say the same thing.
    """
    one = ("JHB",)
    before = {(r[3], r[4]): r[2] for r in TR.residuals(codes=one)}
    assert before, "no residuals for JHB alone — the subset is wrong"

    was = levels.SD_FLOOR
    try:
        levels.SD_FLOOR = 0.40
        during = {(r[3], r[4]): r[2] for r in TR.residuals(codes=one)}
    finally:
        levels.SD_FLOOR = was

    assert during.keys() == before.keys(), \
        "the patch changed the POPULATION, not just the widths"
    moved = [k for k in before if abs(before[k] - during[k]) > 1e-12]
    assert moved, (
        "raising `levels.SD_FLOOR` from 0.15 to 0.40 moved not one committed "
        "width. Key 4 is no longer measuring anything `levels.py` controls — "
        "which is exactly the state the COMMITTED column was added to end.")
    assert min(during.values()) >= 0.40 - 1e-12, (
        "a width came back below the patched floor; `sd_for`'s clamp is not "
        "reading the module constant at call time")

    after = {(r[3], r[4]): r[2] for r in TR.residuals(codes=one)}
    assert after == before, (
        "the memo served a result measured under the PATCHED `levels` after "
        "the patch was restored. `_levels_state()` is not keying on everything "
        "that matters — add the constant you just introduced to it.")



def test_key4_delta_is_the_pass_rule_and_has_actually_been_run():
    """`key4_delta` decides an UNTRADEABLE floor and had no caller and no test.

    MODEL-LOG §1.125's ten-row verdict table — the evidence for "Key 4 no
    longer blocks the Type A filter" — was produced by a script that was not in
    the tree, so the refusal on population drift, the band, the sign trigger
    and `fails` were all unexercised. An audit found it; this is the fix.
    Synthetic arms, because the property is arithmetic and does not need the
    archive. MODEL-LOG §1.126.
    """
    import math

    # Eight metro-year clusters, four observations each, at one fold.
    codes = ["JHB", "TSH", "CPT", "ETH", "EKU", "MAN", "NMA", "BUF"]
    base = {(f"P{j}", "2021", c): (0.30 + 0.01 * j, 0.40)
            for c in codes for j in range(4)}

    # 1. IDENTICAL ARMS — zero delta, no failure, and the fold is asserted.
    same = TR.key4_delta(base, dict(base), "2021")
    assert same["n"] == 32 and same["clusters"] == 8
    assert abs(same["cluster_delta"]) < 1e-12
    assert same["worse_clusters"] == 0, (
        "a zero delta counted as a worsening — the float-dust guard is gone, "
        "and a genuine no-op will be reported as directional again (§1.126)")
    assert not same["fails"]

    # 2. THE FOLD IS ASSERTED, not trusted. `del fold` made it decorative.
    try:
        TR.key4_delta(base, dict(base), "2016")
    except ValueError as e:
        assert "fold 2016" in str(e)
    else:
        raise AssertionError("key4_delta accepted observations from the wrong "
                             "fold; the `fold` argument is decorative again")

    # 3. POPULATION DRIFT REFUSES. Scoring the intersection silently would let
    #    a candidate 'improve' by dropping the rows it forecasts worst.
    short = {k: v for k, v in base.items() if k[0] != "P3"}
    try:
        TR.key4_delta(base, short, "2021")
    except ValueError as e:
        assert "population moved" in str(e)
    else:
        raise AssertionError("key4_delta compared two different populations")

    # 4. A CONSISTENT WORSENING IN EVERY CLUSTER FAILS. Widths halved is a
    #    gross miscalibration and the floor must catch it.
    narrow = {k: (r, w * 0.5) for k, (r, w) in base.items()}
    bad = TR.key4_delta(base, narrow, "2021")
    assert bad["cluster_delta"] > 0 and bad["fails"], (
        f"halving every width did not fail the floor: "
        f"delta {bad['cluster_delta']:+.4f}, one-sided lower bound "
        f"{bad['one_sided_lo']:+.4f}. Key 4 is not a floor.")

    # 5. THE ONE-SIDED THRESHOLD IS THE ONE THAT DECIDES, and it is tighter
    #    than the two-sided bound it replaced (t(0.95,7)=1.895 < 2.365). The
    #    halved-width arm has ZERO between-cluster variance — every cluster
    #    moves identically — so both bounds collapse onto the point estimate
    #    and only `>=` holds there. The strict inequality is asserted below on
    #    the tilted arm, which has real spread.
    assert bad["one_sided_lo"] >= bad["ci95"][0]

    # 6. THE SIGN TRIGGER FIRES INDEPENDENTLY of the band. Seven of eight
    #    clusters worse by a hair, one much better: the mean is dragged
    #    negative and the interval is wide, so only the sign count can see it.
    # `w = 0.40` sits slightly WIDE of the per-observation optimum (which is
    # at |z| = 1, i.e. w = |r|·√(7/5)), so a hair wider is a hair worse and
    # 0.93× is better. 4.0× would have been worse too — the first draft of this
    # fixture used it and got 8 of 8, which is why the assertion below pins the
    # count rather than trusting the construction.
    tilt = {}
    for k, (r, w) in base.items():
        tilt[k] = (r, w * (1.001 if k[2] != "BUF" else 0.93))
    sign = TR.key4_delta(base, tilt, "2021")
    assert sign["worse_clusters"] == 7, sign["worse_clusters"]
    assert sign["sign_fail"] and sign["fails"], (
        "seven of eight metro-years worsening did not fail the floor. The "
        "t interval is driven by the BETWEEN-cluster variance and cannot see "
        "a small, utterly consistent worsening; the exact binomial can, and "
        "P(X>=7 | p=0.5) = 9/256 = 0.035.")
    assert sign["one_sided_lo"] > sign["ci95"][0], (
        "the one-sided bound is not tighter than the two-sided one on an arm "
        "with real between-cluster spread; `_t_crit_one_sided` is wrong")
    assert not sign["one_sided_lo"] > 0, (
        "this fixture no longer isolates the sign trigger — the band catches "
        "it too, so the test has stopped testing what it says it does")


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
