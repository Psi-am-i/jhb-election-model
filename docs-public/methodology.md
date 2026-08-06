# How the model works

This page explains the machinery behind the forecast in plain language: what
is actually being predicted, how the simulation runs, how we know the parts of
it that *can* be tested actually work — and which parts can never be tested,
only stated honestly. The full technical version, with every parameter and
validation table, is
[`METHODOLOGY.md` on GitHub](https://github.com/Psi-am-i/jhb-election-model/blob/main/METHODOLOGY.md).

## How Johannesburg's council elections actually work

Johannesburg's council is elected on two ballots at once. On the first, 135
ward seats are decided race by race, first past the post — if your candidate
wins your ward, they win that seat, full stop. On the second, you vote for a
party. It seems intuitive that the two ballots elect two separate halves of
the council, but that isn't how it works. The two ballots are **added
together**, and that combined share decides the *total* number of seats each
party is entitled to. Ward wins don't add to a party's total — they fill it.
The other 135 seats are then allocated from the party lists to top every
party up to its entitlement. (The part almost everyone gets wrong — including
an early version of this model's own plan — is thinking the party ballot
alone sets the totals. It's *both ballots combined*, and for a party whose
voters split their tickets the difference is worth real seats.)

The niggle is that a party can win *more* wards than its combined share
entitles it to. Say a small party's support is tightly concentrated: it wins
3 wards outright, but its overall share of both ballots entitles it to only
2 seats. Nobody unseats a ward winner — the party keeps all 3, and the seat
law's "excessive seats" clause (Schedule 1, item 16, completed by a 2021
amendment) settles the overflow: the winner receives **no list seats at
all**, and the other parties' list seats are recalculated over the seats
that remain. The council does not grow. We did not take this on trust — we
found the Electoral Commission's own published calculation applying exactly
this in Laingsburg in 2021, where the DA won 3 of 4 wards on 23% of the
vote. The over-winner stays slightly over-represented; the cost falls on
everyone else.

Two consequences shape everything on this site. First, the council is always
close to proportional, so a fragmented vote produces a fragmented council.
Second, the excessive-seats clause — and our forecast finds it is now the
ANC's normal condition: a citywide vote in the mid-twenties, but stronghold
wards that still win, roughly 73 wards against a 65-seat entitlement, in six
of every seven simulations. Its ward count becomes an unbreakable floor, its
list seats go to zero, and the squeeze lands on every other party's list
seats — inside a council fixed at 270, with the majority fixed at 136.

## The machinery of prediction

The forecast comes from running 5,000 simulations of the same pipeline:

1. **Start from the most recent full map.** The 2024 provincial ballot,
   counted in all 865 of Johannesburg's voting districts, is the baseline —
   the last complete picture of where every party's support sits.
2. **Draw a scenario for 2026.** Each run picks a citywide outcome: how far
   the ANC's camp falls, how much the opposition's rises, how the vote splits
   within each camp. Parties that share voters are drawn *together* — the DA
   and ActionSA compete for the same pool, so one's gain is partly the
   other's loss, and the same holds for the ANC, EFF and MK, who fight over a
   pool of their own. The draws are centred on the evidence we have (fifteen
   by-elections, the published polls) and bounded by every national-to-local
   swing actually observed since 2006. When evidence implies something
   history has never produced, history wins: our by-elections implied the
   Patriotic Alliance's citywide vote multiplying roughly sevenfold — but
   by-elections happened to fall in its strongholds, and strongholds are not
   the city. The model pulls that claim back to the top of its supportable
   range, a little more than doubling.
3. **Paint the scenario onto the map.** The citywide outcome is distributed
   across the 865 districts using each party's own geography — where its
   votes really were cast before. This is the model's best-tested idea:
   *where* a party's support sits barely moves between elections, even when
   *how much* support it has swings wildly. The geography is measured once
   and reused; the levels are the uncertain part.
4. **Turn out the voters.** Each district's turnout is projected with its own
   uncertainty, bounded by how much turnout has actually shifted there
   before. One finding worth knowing: the citywide turnout *level* cannot
   change a single seat, because the seat formula scales with it. Only
   *relative* differences between districts matter — and contrary to what
   you have probably heard, even large turnout shifts between districts,
   tested directly, move a couple of seats at most.
5. **Count both ballots.** The ward ballot differs from the party-list
   ballot — voters split their tickets, and we measured each party's split
   from 2021. Ward winners are called race by race; list votes are tallied
   citywide.
6. **Apply the law.** The statutory seat formula — the same arithmetic the
   electoral commission uses — allocates all seats, overhang included. Then
   every possible coalition is checked against that simulation's own majority
   line: every pair of parties, every tripartite alliance, every combination
   of the parties that won seats — with no judgement applied about who
   *would* work with whom.

Repeat 5,000 times, each run drawing fresh values within every variable's
bounds, and the output is not a single prediction but a distribution: how
often each seat count occurs, how often each coalition clears the bar — the
probability of each scenario, not a guess at one.

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

## Corrections and review

After the first version of this forecast was built, a full review found six
implementation errors — one of which made its primary claim outright false.
All six were fixed, and the forecast changed materially. The whole episode —
finding the errors and repairing them — is documented on the
[review page](review).

We publish it because it is worth demonstrating how errors lead to
improvement and better understanding. If you don't look for errors — if you
don't *want* to find them — you are not trying to learn; you are actively
avoiding improvement. A model that admits no error in its construction is
almost guaranteed to be wrong. Good models are the product of continuous
error-correction, each fix pushing them closer to behaving like the real
thing they describe. They do not arrive fully formed — and a model that hides
its mistakes, or hides from them, is refusing the chance to be better, and
should not be trusted.

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
  overhang calculation, and with overhang now the *likely* outcome, we put the
  question to the Commission on 5 August 2026 and are awaiting its answer —
  but a 2021 amendment to the law and the Commission's own published handling
  of Laingsburg 2021 settle the arithmetic, and the forecast applies it.
- **Arithmetic is not politics.** The model says which governments are
  numerically possible. Whether people who dislike each other will sit in
  the same room is not a modelling question.
