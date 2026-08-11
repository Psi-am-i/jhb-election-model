# How the model works

This page explains the machinery in plain language: what is actually being
predicted, how the simulation runs step by step, how we know the parts that
*can* be tested work — and which parts can only be stated honestly. If you
want the full technical record, every file and every workaround is in the
[public repository](https://github.com/Psi-am-i/jhb-election-model), and the
scoring is on the [about the model](about) page.

## How accurate is it?

The model has been run against an election that has already happened — the
2021 municipal election — in **eight cities**, and scored against what
actually occurred and against three deliberately simple alternatives. It beats
all of them in seven of the eight. The full scoring, city by city and party by
party, with our forecast beside the real result, is on the
[about the model](about) page.

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
wards that still win. Its ward count becomes an unbreakable floor, its list
seats go to zero, and the squeeze lands on every other party's list seats —
inside a council fixed at {{council_size}}, with the majority fixed at
{{majority}}.

## The model, step by step

Here is the whole thing in order. Nothing below is more complicated than it
looks.

### 1. Start by counting who can vote, and where

Before any modelling, the Electoral Commission publishes how many people are
registered to vote in each of Johannesburg's roughly 865 voting districts. We
take that count. It is not estimated, projected or adjusted — it is the roll,
published before polling day, and it is the foundation everything else sits
on.

### 2. Sort those voters into pools

A **pool** is a group of voters who are choosing between the same parties —
people with a shared shortlist. Johannesburg has four: Black African,
Coloured, Indian/Asian and White.

That is an uncomfortable thing to model and we should say why we do it. It is
not a claim that people vote according to their race, or that anyone must. It
is that South African cities are still physically laid out by apartheid
planning, so a voting district is one of the few things in the data that
actually distinguishes one group of voters from another — and the parties
themselves behave as though this were true. Al Jama-ah takes about a fifth of
one pool and essentially nothing anywhere else. The Patriotic Alliance takes
about two-fifths of another and nothing at all in the other three. Those are
measurements, not opinions.

**How big is each pool?** Each ward's registered voters, split by that ward's
own composition, added up across all 135 wards. The census tells us the
*proportions* within a ward; the roll tells us the *number*, and where the two
disagree the roll wins. It disagrees a lot: the census implies about 300,000
white adults in Johannesburg while the roll carries roughly 560,000 registered
white voters. We publish that gap rather than absorbing it.

### 3. Measure how each party does in each pool

Now the only real statistics in the model. We know how every ward voted, and
we know roughly what each ward is made of. From 135 wards at once we can work
backwards to how each party performs with each pool — the same way you can
work out the price of apples and oranges from a stack of shopping receipts
without ever seeing inside a bag.

This is done for every party simultaneously, under two rules that must hold:
no party can win a negative number of votes, and everyone's votes in a pool
must add up to that pool's voters. Fitting parties one at a time breaks both —
an early version had a party winning a *negative* share of one pool, which is
not a small error but an impossible one.

### 4. Work out what might change

Steps 1–3 describe the last election. This step is the forecast, and it is the
part that is genuinely uncertain, so instead of picking one answer we draw
thousands.

Two things get drawn:

- **How each party's support moves.** Parties usually do worse locally than
  nationally, and we measure how much from every previous national-to-local
  transition on record for that party — not a guess, and not the same number
  for everyone.
- **Turnout, per pool.** This is the only genuinely unknown quantity, and it
  is drawn from what turnout has actually done in that city before. In 2021
  every pool's turnout was the lowest on record, which is why the range has to
  allow falls as well as rises.

### 5. Handle parties that were not there last time

This is the hardest part of forecasting an election and where models usually
fail. There are two kinds of new party and they behave nothing alike:

- A **split** is when a known person leaves a known party and takes some of
  its vote with them: Zuma leaving the ANC for MK, Malema for the EFF, Mashaba
  leaving the DA for ActionSA. A split starts with a leader, a machine and a
  share of somebody's existing vote. We size it as a fraction of its parent,
  from what previous splits actually took.
- An **entrant** is a name on a ballot with none of that. Most new parties are
  this, and most of them get almost nothing.

Telling them apart matters more than anything else in the model. Before we
did, every party that managed to file candidates everywhere was being sized as
though it were the EFF's 2016 breakthrough — filing papers is cheap, and in
Cape Town that put more than the entire electorate into the hands of parties
that did not exist. Separating the two fixed it.

One further thing we found, which surprised us: how much a split takes depends
overwhelmingly on **whether the leader's own following is in this city**, not
on how famous they are. Patricia de Lille was at least as well known
nationally in 2019 as Julius Malema was in 2014; her party took about
one-eighteenth as much of the DA's vote in Johannesburg as it did in her own
Cape Town. A reputation does not travel. A constituency does not move.

### 6. Paint the result back onto the map

Each drawn outcome is spread back across all 865 voting districts using each
party's own geography — where its votes actually were last time. This is the
best-tested idea in the model: *where* a party's support sits barely moves
between elections even when *how much* it has swings wildly.

### 7. Count both ballots and apply the law

Voters split their tickets, so the ward ballot and the party ballot are
counted separately, each party's split measured from its own past behaviour.
Ward winners are called race by race. Then the statutory formula — the same
arithmetic the Electoral Commission uses — allocates every seat, excessive
seats included.

### 8. Do it {{n_draws}} times

Each run draws fresh values within every bound. The output is not a
prediction but a distribution: how often each seat count happens, how often
each coalition clears the line. Every possible combination of parties is
checked against that run's own majority line, with no judgement about who
would work with whom.

Why simulate at all, rather than publish one number? Because Johannesburg's
politics runs on thresholds — a coalition either reaches {{majority}} seats or
it does not — and near a threshold small uncertainties have large, lopsided
consequences that no error bar can carry.

## What a pool is — and what it is not

A pool is **not** an alliance, a coalition, or a prediction about who will
govern with whom. It is a statement about voters, not parties: a set of
parties competing for the same people. The DA and ActionSA drawing from the
same pool means that when one rises the other tends to fall in the same
places — which is why their *combined* range is much tighter than either
party's own, and why ignoring it produces impossible scenarios where both
surge at once out of nowhere.

It is also not a claim about why anyone votes as they do. We can measure that
a pool of voters moved; we cannot measure why, and aggregate data can never
tell you. Any sentence on this site that appears to explain a voter's
reasoning is overreach, and we would like to know about it.

## How we know it works

Three checks, in increasing order of difficulty.

**The seat law is exact.** Our implementation reproduces the published
councils to the seat — quota, vote totals, every party — for eight
municipalities across three elections, from the raw voting-district files. The
legal arithmetic is not an assumption. One exception is documented: the
Commission publishes every independent candidate under a single name, so where
several stand in one ward they cannot be told apart, and we take the
Commission's own count of independent ward councillors rather than inferring
it.

**The geography transfers.** Shown only citywide totals for 2021 — nothing
about where the votes sat — the model placed them well enough to call
{{blind_test_called}} of {{blind_test_of}} ward winners.

**The whole thing beats the simple alternatives, in cities it was never built
for.** This is the test that matters, and the one most forecasts skip. A model
tuned on one city can look superb there and have learned nothing but that
city. So the entire pipeline is run independently in eight metros — each
fitted only on its own wards, its own roll, its own history — and scored
against three baselines that need no model at all. The results are on the
[about the model](about) page, including the city where the model *loses*.

## What this does not cover

- **A party that does not exist yet is still the hardest case.** We now
  separate splits from entrants and size each from the record, which is a
  large improvement, but a genuinely new formation with a popular leader
  remains the biggest single source of error.
- **Two inputs could not be confined to the period before the test election**,
  and every run prints them above its own results: the ward-level census
  (2022, the only one we hold) and the record of how much breakaway parties
  take. Both are declared on the [about the model](about) page.
- **Overhang's legal fine print is untested in court.** The Commission has
  never published a worked metro overhang example. We put the question to it
  on 5 August 2026 and are awaiting an answer; a 2021 amendment and the
  Commission's own handling of Laingsburg 2021 settle the arithmetic, and the
  forecast applies it.
- **Arithmetic is not politics.** The model says which governments are
  numerically possible. Whether people who dislike each other will sit in the
  same room is not a modelling question.

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

## Going deeper

Everything above is a simplification of something you can read in full. The
code, the data recipes, the running log of findings and mistakes, and the
known defects in the public records we depend on are all published:

- [the repository](https://github.com/Psi-am-i/jhb-election-model) — all of it
- `MODEL-LOG.md` — every finding, obstacle and decision, in order, including
  the ones that went badly
- `DATA-QUALITY.md` — defects in the official published records, with the ward
  and the arithmetic for each
- `SOURCES.md` — where every input came from and how to fetch it again
