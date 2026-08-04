# How the model works

This page explains the machinery behind the forecast in plain language: what
is actually being predicted, how the simulation runs, how we know the parts of
it that *can* be tested actually work — and which parts can never be tested,
only stated honestly. The full technical version, with every parameter and
validation table, is
[`METHODOLOGY.md` on GitHub](https://github.com/Psi-am-i/jhb-election-model/blob/main/METHODOLOGY.md).

## What is actually being decided

Johannesburg's council is elected on two ballots at once: 135 ward seats
decided race by race, and 135 seats filled from party lists. The part almost
everyone gets wrong is how they combine. A party's total number of seats is
set by its share of **both ballots added together** — winning a ward does not
*add* a seat, it just fills one of the seats the party was already entitled
to. The list seats then top each party up toward its fair share.

This has two consequences that shape everything on this site. First, the
council is close to proportional, so a fragmented vote produces a fragmented
council. Second, a party that wins *more* wards than its proportional
entitlement keeps the extras — and the council grows beyond 270 to
accommodate them. That is called overhang, and the forecast finds it is now
the ANC's normal condition: a mid-twenties citywide vote, but stronghold wards
that still win. The majority line moves from 136 to roughly 141, and every
possible coalition has to clear the higher bar.

## The engine, in six steps

Each of the 5,000 simulations runs the same pipeline:

1. **Start from the most recent full map.** The 2024 provincial ballot,
   counted in all 865 of Johannesburg's voting districts, is the baseline —
   the last complete picture of where every party's support sits.
2. **Draw a scenario for 2026.** Each run picks a citywide outcome: how far
   the ANC's camp falls, how much the opposition's rises, how the vote splits
   within each camp. Parties that share voters are drawn *together* — the DA
   and ActionSA compete for the same pool, so one's gain is partly the
   other's loss. The draws are centred on the evidence we have (fifteen
   by-elections, the polls) and bounded by every national-to-local swing
   actually observed since 2006.
3. **Paint the scenario onto the map.** The citywide outcome is distributed
   across the 865 districts using each party's own geography. This is the
   model's best-tested idea: *where* a party's support sits barely moves
   between elections, even when *how much* support it has swings wildly. The
   geography is measured once and reused; the levels are the uncertain part.
4. **Turn out the voters.** Each district's turnout is projected with its own
   uncertainty. One finding worth knowing: the citywide turnout *level*
   cannot change a single seat, because the seat formula scales with it.
   Only *differences* between districts matter — and even those, tested
   directly, move a couple of seats at most.
5. **Count both ballots.** The ward ballot differs from the list ballot —
   voters split their tickets, and we measured each party's split from 2021.
   Ward winners are called race by race; list votes are tallied citywide.
6. **Apply the law.** The statutory seat formula — the same arithmetic the
   electoral commission uses — allocates all seats, overhang included. Then
   every possible coalition is checked against that simulation's own majority
   line: every pair, every triple, every combination of the parties that won
   seats, with no judgement applied about who *would* work with whom.

Repeat 5,000 times and the output is not a prediction but a distribution:
how often each seat count occurs, how often each coalition clears the bar.

## How we know it works — and what that does not cover

Three checks matter, in increasing order of difficulty:

**The seat law is exact.** Our implementation of the seat formula reproduces
the real, published 2011, 2016 and 2021 Johannesburg councils to the seat —
quota, vote totals, every party — from the raw voting-district files. The
legal arithmetic is not an assumption.

**The geography transfers.** Fitted on one election cycle and tested on the
next, the map-painting step holds up: shown only the 2021 citywide totals —
nothing about where the votes sat — the model placed them well enough to call
129 of 135 ward winners.

**But the citywide ranges cannot be validated.** When the model is tested
fully blind — told nothing about 2021 at all — its seat error grows fivefold.
That is the honest boundary: the machinery that turns a citywide outcome into
seats is validated; the range of citywide outcomes for 2026 is informed
judgement, bounded by history and tilted by evidence, but judgement all the
same. It is why the output is a distribution, why the probabilities are only
as good as the stated assumptions — and why every one of those assumptions is
a slider on the [interactive page](interactive), so you can test how much any
conclusion depends on them.

## The model was broken once, and we published the repair

After the first version of this forecast was built, a full review found six
implementation errors — one of which made the original headline claim
outright false. All six were fixed the same day, the forecast changed
materially, and the whole episode is documented on the
[review page](review), because a model whose mistakes are hidden is not worth
trusting.

## The dials you can turn

Every scenario assumption sits at a documented default, bounded by observed
history, and adjustable on the [interactive page](interactive): how far each
party's national support carries into a local election, how much weight the
by-elections get, which poll you believe, how the two ballots differ, what
turnout does, whether a brand-new party appears — and what happens to the
council when overhang strikes. The page re-runs the full simulation in your
browser and emits a scenario file that reproduces your settings exactly in
the published model.

## Limits worth knowing

- **A party that does not exist yet is invisible.** ActionSA went from
  nothing to 44 seats in one cycle. The simulations carry a slot for an
  unknown newcomer, but that is an honest patch, not foresight.
- **Overhang's legal fine print is untested in court or precedent.** The
  electoral commission has never published a worked example of a metro
  overhang calculation. With overhang now the *likely* outcome, we have asked
  for one; until then the model carries both readings of the law and reports
  the difference.
- **Arithmetic is not politics.** The model says which governments are
  numerically possible. Whether people who dislike each other will sit in
  the same room is not a modelling question.
