# How the model works

This page explains the machinery in plain language: what is actually being
predicted, how the simulation runs step by step, how we know the parts that
*can* be tested work — and which parts can only be stated honestly. If you
want the full technical record, every file and every workaround is in the
[public repository](https://github.com/Psi-am-i/jhb-election-model), and the
scoring is on the [about the model](about) page.

## How accurate is it?

A forecast that has never been scored is an opinion. So this one is run against
an election that has already happened — the 2021 municipal election, in
{{backtest_cities}} cities — and scored against what actually occurred.

The comparison that matters is not "did it get close", but "did it beat what
anyone could do without a model". The standard in election forecasting is
**uniform swing**: take the national change since the last election and apply it
equally everywhere. It is much harder to beat than it sounds, because it already
knows the last result and the direction the country moved. We score against that
and two others — the last local result repeating unchanged, and that result with
uncertainty drawn around it — and compare the model against **whichever did best
in each city**, not the weakest of the three.

The model wins in **{{backtest_wins}} of {{backtest_cities}}** cities on the
measure that counts a forecast's whole range rather than a single guess (CRPS),
with **{{backtest_crps_better}}** less error in total. On the blunter measure of
seats put in the wrong column it misses **{{backtest_seat_err_model}}** across
all those councils against the baselines' **{{backtest_seat_err_baseline}}**, and
it calls the winner correctly in **{{backtest_wards_called}} of
{{backtest_wards}}** wards.

Two honest caveats. Two of the three alternatives produce a single number rather
than a range, which the range-based score treats kindly. And the model is
compared against the best baseline in each city, which is the hardest test
available but still a test of arithmetic, not of politics. The full scoring, city
by city and party by party, with our forecast beside the real result, is on the
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
Second, the excessive-seats clause, which the model expects to catch the ANC
in {{p_excessive_anc}} of simulations: a citywide vote in the mid-twenties,
but stronghold wards that still win. Where it fires, the party's ward count
becomes an unbreakable floor, its list seats go to zero, and the squeeze lands
on every other party's list seats — inside a council fixed at
{{council_size}}, with the majority fixed at {{majority}}.

## The model, step by step

Here is the whole thing in order. Nothing below is more complicated than it
looks.

### 1. Start by counting who can vote, and where

Before any modelling, the Electoral Commission publishes how many people are
registered to vote in each of Johannesburg's {{n_vds}} voting districts. We
take that count. It is not estimated, projected or adjusted — it is the roll,
published before polling day, and it is the foundation everything else sits
on.

### 2. Sort those voters into pools

A **pool** is a group of voters who are choosing between the same parties —
people with a shared shortlist.

**Where the categories come from.** Johannesburg currently has four pools, and
they are not our invention: they are Statistics South Africa's own population
group categories, in Stats SA's own words — *Black African, Coloured,
Indian/Asian, White* — taken per ward from the Census 2022 Ward Statistical
Product. We use their terms rather than substituting our own so that anyone
can check the input against the published source. A fifth Stats SA category,
"Other", is not carried: it is about half a percent of the population, no
party's rate in it could be identified, and inventing a constituency for it
would assert something the data does not support.

That is an uncomfortable thing to model and we should say why we do it. It is
not a claim that people vote according to their race, or that anyone must. It
is that South African cities are still physically laid out by apartheid
planning, so a voting district is one of the few things in the data that
actually distinguishes one group of voters from another — and the parties
themselves behave as though this were true. Al Jama-ah takes about a fifth of
one pool and essentially nothing anywhere else. The Patriotic Alliance takes
about two-fifths of another and nothing at all in the other three. Those are
measurements, not opinions.

**These categories are too coarse, and we intend to replace them.** Population
group is the only ward-level characteristic Stats SA publishes, and it plainly
does not describe how voters actually group: the ANC and the IFP both draw
overwhelmingly from the same population group and stand on entirely separate
ground, which is a linguistic and regional division rather than a racial one.
The right input is **home language by ward**, which Stats SA holds but does not
publish in the ward product; we have requested it. Income, employment and
dwelling type would help too, and are also request-only — reasonably so, since
at ward level they can identify households. Until those arrive we
carry one extra pool that the census cannot see, identified instead from a
party's own geography — the constituency the IFP stands on — and we label it
for what was measured rather than what we suspect it is.

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

Each drawn outcome is spread back across all {{n_vds}} voting districts using each
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
- **The model runs from national results downward, and that is half the
  story.** Every party's starting level comes from the last *national*
  election, converted down to local. That is the right way round for a
  nationally organised party and the wrong way round for one whose support is
  local — and tested on 2021 the two routes are close to even, five parties to
  four. ActionSA is the sharpest case: it polled 18.12% in this city's 2021
  local election and 6.22% nationally in 2024, and the forecast is built on
  the smaller, less relevant number. Local formations — a ratepayers'
  association, a party that exists in one metro — are carried poorly for the
  same reason. Fixing it means drawing a party's level from its local and
  national records together, weighted by which has actually been more
  informative for a party like it. It is the largest open item on the model.
- **No poll is used in the forecast. This changed on 12 September 2026, and
  before that date polls were used.**

  *This page has twice described the wrong state of this switch, and both times
  in the same direction — the text stayed still while the model moved. It said
  "no poll is currently used at all" for a day after that stopped being true on
  2026-08-22, which is the most serious error this site has carried; it then
  described a weighting cap for three weeks after that cap was retired. So the
  date above is not decoration. **If you are reading this and the site's
  forecast still differs from a no-polls model, this sentence is stale again and
  the forecast is what to believe.***

  **Why they were taken out.** Polls were an input until 12 September. Removing
  them is not a judgement that they are worthless — it is that we had no
  designed answer to how several polls should interact with each other: how much
  two waves from one house count against one wave from another, how a party-
  internal poll is discounted, how a national poll and a metro poll combine. The
  weighting we had was defensible one poll at a time and improvised across
  several. Rather than keep shipping a forecast that depended on it, the channel
  is off until that is designed properly.

  **What it was worth, measured.** We aim to score {{backtest_target}} past city
  elections across the country — eight metros, three elections each — and how
  many are in the panel on any given day depends on which specs have been
  emitted. Against the panel as it stood, removing polls changed the total seat
  error from
  {{polls_off_seat_err_before}} to {{polls_off_seat_err_after}} and the
  distributional score (CRPS) from {{polls_off_crps_before}} to
  {{polls_off_crps_after}}. Both move the right way and neither is large: seven
  elections moved at all, one of them by six seats *against* the change. The honest summary is that **we cannot distinguish the poll channel's
  contribution from zero**, which is itself a reason not to let it move a
  published headline while its design is unsettled.

  **What we intend.** To use every poll we receive, and to put the weighting in
  the reader's hands — a control on this site letting you say how far you trust
  each individual poll, within that poll's own margin of error, and see the
  forecast respond. That is the design being worked on; it is not built yet, and
  we would rather say so than ship the half of it we had.

  **The caution that has always motivated this is unchanged**: the polls that
  exist disagree with each other by more than the quantity being forecast — one
  house had the DA on 42% and the ANC on 18% in the same year another had the
  ANC on 35% and the DA on 25% — and metro-level polling has little track record
  here to weight them by; pre-2021 polling missed ActionSA in this city by about
  ten points. Every poll we hold is still listed, with its caveats, and the
  model is still read against them as an outside check that it is in the
  ballpark. They are evidence we look at. They are not, at present, an input.
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
