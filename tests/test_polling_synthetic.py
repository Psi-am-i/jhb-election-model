"""CLASS 15 (continued) — SYNTHETIC POLLS, BECAUSE TWO REAL ONES CANNOT FIND A BUG.

The register holds two admitted 2026 polls and they are the same house, the same
size, the same method and 150 days apart. Every property the new weighting
depends on — that a second house loosens the cap, that a huge sample cannot
break the floor, that a poll agreeing with the model moves nothing — is
unexercised by them, and a weighting scheme nobody has pushed on is a scheme
whose failure mode you meet in public.

So these are made-up polls, deliberately kept inside plausible South African
metro bounds (no party at 90%, samples between a few hundred and a few
thousand), driven through the real arithmetic.

**And they are not only a convenience.** Once readers can submit their own polls
to the competition, the weighting is an untrusted-input surface: a reader-entered
poll claiming a million respondents, or an unsigned sample size, or shares that
sum to three, is an *expected* input and not a hypothetical one. Several of the
cases below are that reader, and the assertions are the bound on what they can
do to the published forecast.

MODEL-LOG §1.67.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _support import ROOT, run_module  # noqa: E402

sys.path.insert(0, str(ROOT / "src"))

import polling as PG  # noqa: E402

POLL_DAY = date(2026, 11, 4)

# A plausible Johannesburg 2026 reading: close to the real July wave, which had
# DA 42, ANC 18, MK 13, ASA 10, EFF 8.
PLAUSIBLE = {"DA": 0.40, "ANC": 0.20, "MK": 0.12, "ASA": 0.11, "EFF": 0.08}


def poll(**kw) -> dict:
    """A synthetic metro poll of Johannesburg, with sane defaults."""
    base = {
        "id": kw.pop("id", "synthetic"),
        "house": kw.pop("house", "HouseA"),
        "scope": "metro",
        "city": "joburg",
        "fieldwork_end": kw.pop("fieldwork_end", "2026-09-01"),
        "n": kw.pop("n", 800),
        "n_basis": kw.pop("n_basis", "standalone"),
        "numbers": kw.pop("numbers", dict(PLAUSIBLE)),
    }
    base.update(kw)
    return base


def _weight(polls, party, share, model_sd):
    """The weight the model would actually give this aggregate. One place.

    **AND IT MUST MIRROR THE MODEL, WHICH IT STOPPED DOING (§1.92).** When the
    two-term σ was adopted the cap was deleted under the same switch, and this
    helper went on applying `weight_cap` — so every test in this file was
    measuring a hybrid that the model does not run: the NEW σ against the OLD
    cap. One house pinned at exactly 0.500 from one wave to a hundred, which
    looked like the cap working and was the helper disagreeing with the code.

    A second copy of a calculation is this repository's most reliable defect.
    The branch below is the same one `montecarlo` takes.
    """
    sd = PG.aggregate_sd(polls, party, share, asof=POLL_DAY)
    raw = PG.blend_weight(sd, model_sd)
    if PG.SIGMA_TWO_TERM:
        return raw                       # no cap: the floor in σ_common is it
    return min(raw, PG.weight_cap(PG.effective_houses(polls, asof=POLL_DAY)))


def test_a_second_house_is_worth_more_than_a_second_wave():
    """The property the whole scheme turns on, stated as a comparison.

    Two waves of one house and two waves of two houses are the same amount of
    fieldwork. They are not the same amount of evidence, and if the arithmetic
    cannot tell them apart then publishing more often is a way to buy influence.

    **Under the two-term sigma the guarantee is STRONGER than it was, and it is
    structural rather than truncated (MODEL-LOG 1.92).** The retired form bounded a
    single house with `weight_cap` — an explicit ceiling, chosen. Deleting the
    cap does not remove the bound, because SIGMA_COMMON never divides by
    `h_eff`: a lone house's weight therefore SATURATES on its own. Measured on
    this fixture: one house is worth 0.5226 at one wave, 0.5755 at a hundred and
    0.5761 at ten thousand, while two houses pass that ceiling with four polls.

    The first version of this test asked the wrong question — it compared a
    hundred polls against two and found volume winning, which is not a defect
    but a comparison of fieldwork quantity. Hold volume constant and replication
    wins at every level (1 house / 2 / 4 at 100 polls: 0.5755 / 0.5945 / 0.6045).
    """
    one_house = [poll(id="a1", house="HouseA", fieldwork_end="2026-07-01"),
                 poll(id="a2", house="HouseA", fieldwork_end="2026-09-01")]
    two_houses = [poll(id="a1", house="HouseA", fieldwork_end="2026-07-01"),
                  poll(id="b1", house="HouseB", fieldwork_end="2026-09-01")]

    w_one = _weight(one_house, "DA", 0.40, 0.045)
    w_two = _weight(two_houses, "DA", 0.40, 0.045)
    # Same fieldwork, different replication. The margin is modest under the
    # two-term form and that is the point: all a second house buys is halving
    # SIGMA_IDIO, because the common term is common — Shirani-Mehr et al.
    # measure that it "persists unchanged, even when averaging over a large
    # number of surveys". Measured today: 0.518 -> 0.533.
    assert w_two > w_one + 0.01, (
        f"two waves of ONE house take {w_one:.3f} of the blend and two waves of "
        f"TWO houses take {w_two:.3f} — barely different. A second house must "
        f"be worth materially more than a second wave, or a single house can "
        f"buy the forecast by publishing weekly.")

    # AND THE BOUND THAT REPLACED THE CAP: one house runs out of road.
    flood = [poll(id=f"f{i}", house="HouseA") for i in range(10_000)]
    modest = [poll(id=f"m{i}", house=f"H{i % 2}") for i in range(4)]
    w_flood = _weight(flood, "DA", 0.40, 0.045)
    w_modest = _weight(modest, "DA", 0.40, 0.045)
    assert w_flood < w_modest, (
        f"ten thousand waves of ONE house take {w_flood:.4f} of the blend and "
        f"four polls from TWO houses take {w_modest:.4f}. A single house has "
        f"out-published two houses, which is the failure `weight_cap` used to "
        f"prevent by truncation and SIGMA_COMMON is supposed to prevent by "
        f"never shrinking. If this fails, SIGMA_COMMON has been divided by "
        f"h_eff somewhere.")

    # ...and it genuinely saturates, rather than merely rising slowly.
    assert w_flood - _weight(
        [poll(id=f"g{i}", house="HouseA") for i in range(1_000)],
        "DA", 0.40, 0.045) < 1e-3, (
        "a single house's weight is still climbing between 1,000 and 10,000 "
        "waves. It must converge, or the ceiling is only far away rather than "
        "real.")


def test_a_million_respondents_cannot_break_the_floor():
    """The adversarial case, which is a real reader input once entries open.

    Sampling error goes to zero with n. Total error does not: house, screen and
    drift are a floor no sample size penetrates. If this fails, a reader can
    type a large enough n to make their own poll the forecast.
    """
    honest = poll(n=800)
    absurd = poll(n=1_000_000)
    sd_honest = PG.aggregate_sd([honest], "DA", 0.40, asof=POLL_DAY)
    sd_absurd = PG.aggregate_sd([absurd], "DA", 0.40, asof=POLL_DAY)
    assert sd_absurd < sd_honest, "a larger sample must reduce sampling error"
    assert sd_absurd > 0.02, (
        f"a million-respondent poll is priced at {sd_absurd:.4f} — under 2pp. "
        f"House, screen and drift are a FLOOR that no sample size may cross; if "
        f"they can be sampled away, the decomposition has collapsed back to "
        f"sampling error and the single-house protection is gone.")
    w = _weight([absurd], "DA", 0.40, 0.045)
    ceiling = PG.house_ceiling([absurd], "DA", 0.40, 0.045, asof=POLL_DAY)
    assert w <= ceiling + 1e-9, (
        f"a million-respondent single-house poll takes {w:.3f} of the blend, "
        f"above the ceiling {ceiling:.4f} that one house can ever reach. That "
        f"ceiling is not a chosen cap — it is `sigma_floor`, this poll's own "
        f"sigma with the sampling term removed, so exceeding it means sampling "
        f"error has been allowed to go negative somewhere.")


def test_a_poll_that_agrees_with_the_model_moves_nothing_much():
    """A sanity check that would catch a sign error or a units error instantly."""
    mu = 0.40
    p = poll(numbers=dict(PLAUSIBLE, DA=mu))
    w = _weight([p], "DA", mu, 0.045)
    blended = (1 - w) * mu + w * mu
    assert abs(blended - mu) < 1e-12, (
        f"a poll reading exactly the model's own centre moved it to {blended:.4f}"
        f" from {mu:.4f}. The blend is not a convex combination.")


def test_a_poll_that_disagrees_moves_the_centre_toward_it_and_not_past_it():
    """Bounded, monotone, and on the correct side. Catches a swapped weight."""
    mu, polled = 0.30, 0.42
    w = _weight([poll(numbers=dict(PLAUSIBLE, DA=polled))], "DA", polled, 0.045)
    blended = (1 - w) * mu + w * polled
    assert mu < blended < polled, (
        f"model {mu:.3f}, poll {polled:.3f}, blended {blended:.3f} — the result "
        f"is outside the interval between them, so the weight is not a convex "
        f"combination weight.")
    ceiling = PG.house_ceiling(
        [poll(numbers=dict(PLAUSIBLE, DA=polled))], "DA", polled, 0.045,
        asof=POLL_DAY)
    assert blended - mu <= (polled - mu) * ceiling + 1e-9, (
        f"a single-house poll moved the centre {blended - mu:.4f} of the "
        f"{polled - mu:.4f} gap — a fraction of {(blended - mu) / (polled - mu):.4f}, "
        f"above the {ceiling:.4f} ceiling one house can ever take. The bound is "
        f"derived from `sigma_floor`, not asserted as a round number.")


def test_more_waves_of_one_house_approach_a_floor_and_never_cross_it():
    """Monotone, convergent, and bounded BELOW by the floor the model states.

    The floor is not typed here. It is :func:`polling.sigma_floor` — the same
    `aggregate_sd` call with the sampling term switched off — so this test
    cannot pass while disagreeing with the model about where the floor is,
    which is precisely what a hand-typed 3.35pp allowed (MODEL-LOG 1.92).

    Measured under the two-term sigma on this fixture, 1 to 100 waves:
    4.301 -> 3.865pp against a floor of 3.860pp.
    """
    waves = {k: [poll(id=f"w{i}", house="HouseA") for i in range(k)]
             for k in (1, 2, 4, 8, 20, 100)}
    sds = [PG.aggregate_sd(w, "DA", 0.40, asof=POLL_DAY) for w in waves.values()]
    floor = PG.sigma_floor(waves[100], "DA", 0.40, asof=POLL_DAY)

    assert all(b <= a + 1e-12 for a, b in zip(sds, sds[1:])), (
        f"sigma is not monotone decreasing in the number of waves: {sds}")
    assert all(x >= floor - 1e-12 for x in sds), (
        f"sigma {min(sds):.5f} has crossed BELOW its own floor {floor:.5f}. "
        f"Only the sampling term may shrink with waves; if the total goes under "
        f"the floor then a house term is being averaged away by republication.")
    assert sds[-1] - floor < 1e-4, (
        f"one hundred waves reach {sds[-1]:.5f} against a floor of {floor:.5f} "
        f"— still {sds[-1] - floor:.5f} above it. The sampling term is supposed "
        f"to be nearly exhausted by then; if it is not, waves are worth far "
        f"more than intended and a house can publish its way to influence.")
    assert sds[0] - sds[-1] < 0.01, (
        f"waves alone move sigma by {sds[0] - sds[-1]:.4f}. Sampling is meant to "
        f"be the SMALL part of a metro poll's error, and if it is the large "
        f"part the decomposition has the wrong shape.")


def test_an_undisclosed_screen_is_priced_worse_than_a_disclosed_one():
    """Otherwise there is no incentive to publish a method, and no cost to not."""
    hidden = PG.aggregate_sd([poll()], "DA", 0.40, asof=POLL_DAY)
    shown = PG.aggregate_sd([poll(screen_disclosed=True)], "DA", 0.40,
                            asof=POLL_DAY)
    assert shown < hidden, (
        f"a poll with a published likely-voter screen is priced at {shown:.4f} "
        f"and one that hides it at {hidden:.4f}. Hiding the screen must cost "
        f"something or the term is decorative.")


def test_a_stale_poll_is_priced_worse_than_a_fresh_one():
    """Drift is the one term that grows while we wait, and it must bite."""
    fresh = PG.aggregate_sd([poll(fieldwork_end="2026-10-28")], "DA", 0.40,
                            asof=POLL_DAY)
    stale = PG.aggregate_sd([poll(fieldwork_end="2026-01-15")], "DA", 0.40,
                            asof=POLL_DAY)
    assert stale > fresh, (
        f"a poll from January is priced at {stale:.4f} and one from last week "
        f"at {fresh:.4f}. Opinion moves; the drift term must make the older one "
        f"worth less.")


def test_a_subsample_of_a_national_poll_counts_for_less_than_its_headline_n():
    """The 504-respondent problem, as a property rather than a caveat string."""
    sub = poll(n=504, n_basis="metro-subsample")
    standalone = poll(n=504, n_basis="standalone")
    assert (PG.aggregate_sd([sub], "DA", 0.40, asof=POLL_DAY)
            > PG.aggregate_sd([standalone], "DA", 0.40, asof=POLL_DAY)), (
        "a metro cut of a national sample is priced the same as a "
        "purpose-designed metro poll of the same headline size")


if __name__ == "__main__":
    raise SystemExit(run_module(sys.modules[__name__]))
