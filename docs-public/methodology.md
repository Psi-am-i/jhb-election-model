# How the model works

The full technical record, every file and every workaround, is in the
[public repository](https://github.com/Psi-am-i/jhb-election-model).

## How Johannesburg's council elections work

Johannesburg's council is elected on two ballots at once. On the first, 135
ward seats are decided race by race, first past the post. On the second, you
vote for a party. The two ballots do not elect two halves of the council. They
are **added together**, and the combined share decides the *total* number of
seats each party is entitled to. Ward wins do not add to a party's total; they
fill it. The other 135 seats are allocated from the party lists to top every
party up to its entitlement. A common mistake, made in an early version of this
model's own plan, is to think the party ballot alone sets the totals. For a
party whose voters split their tickets, the difference is worth seats.

A party can win *more* wards than its combined share entitles it to. Say a
small party with concentrated support wins 3 wards outright, but its share of
both ballots entitles it to 2 seats. It keeps all 3. The seat law's "excessive
seats" clause (Schedule 1, item 16, completed by a 2021 amendment) settles the
overflow: the party receives **no list seats**, and the other parties' list
seats are recalculated over the seats that remain. The council does not grow.
The Electoral Commission's own published calculation applies exactly this in
Laingsburg in 2021, where the DA won {{hist_laingsburg_da_wards}} of {{hist_laingsburg_wards}} wards on {{hist_laingsburg_da_share}} of the vote. The
over-winner stays slightly over-represented; the cost falls on everyone else.

Two consequences shape this site. The council is always close to proportional,
so a fragmented vote produces a fragmented council. The excessive-seats clause
catches the ANC in {{p_excessive_anc}} of simulations: a citywide vote in the
mid-twenties, with stronghold wards that still win. Where it fires, the party's
ward count is a floor, its list seats go to zero, and the squeeze lands on
every other party's list seats, inside a council fixed at {{council_size}} with
the majority at {{majority}}.

## The model, step by step

### 1. Count who can vote, and where

The Electoral Commission publishes how many people are registered in each
ward. The forecast uses its count of registered voters as at 26 September 2026.
The Commission counts each voting district in a single ward and publishes no
figure per voting district. So the model places each of Johannesburg's
{{n_vds}} voting districts wholly in the ward that best reproduces the
Commission's totals, and shares each ward's total among its voting districts in proportion
to their registration when the wards were drawn. That roll is the model's
foundation.

### 2. Sort those voters into pools

A **pool** is a group of voters choosing between the same parties.

**Where the categories come from.** Johannesburg has four pools. They are
Statistics South Africa's population group categories, in Stats SA's own words
(*Black African, Coloured, Indian/Asian, White*), taken per ward from the
Census 2022 Ward Statistical Product. We use their terms so that anyone can
check the input against the published source. A fifth category, "Other", is not
carried: it is about half a percent of the population, and no party's rate in
it could be identified.

This is not a claim that people vote by race, or that anyone should. South
African cities are still laid out by apartheid planning, so a voting district's
population group is one of the few things in the data that distinguishes one
group of voters from another, and the parties' results follow it. Al Jama-ah
takes about a fifth of one pool and almost nothing elsewhere. The Patriotic
Alliance takes about two-fifths of another and nothing in the other three.

**These categories are too coarse.** Population group is the only ward-level
characteristic Stats SA publishes, and it does not describe how voters group:
the ANC and the IFP draw overwhelmingly from the same population group and
stand on separate ground, a linguistic and regional division rather than a
racial one. The better input is
**home language by ward**, which Stats SA holds but does not publish in the
ward product; we have requested it. Income, employment and dwelling type would
also help, and are also request-only, since at ward level they can identify
households. Until those arrive the forecast uses the four census pools.

**How big is each pool?** Each ward's registered voters, split by that ward's
census population shares, summed across all 135 wards. The census gives the
*proportions* within a ward; the roll gives the *number*. The voters' roll does
not record population group, so the split assumes every group in a ward
registers at the same rate.

### 3. Measure how each party does in each pool

This is the model's statistics. We know how every ward voted and roughly what
each ward is made of. From 135 wards at once the model works back to how each
party performs in each pool, as you can work out the price of apples and
oranges from a stack of receipts without seeing inside a bag.

It does this for every party at once, under two rules: no party can win a
negative number of votes, and the votes in a pool must add up to that pool's
voters. Fitting parties one at a time breaks both; an early version had a party
winning a *negative* share of one pool.

### 4. Work out what might change

Steps 1–3 describe the last election. This step is the forecast, and it is
uncertain, so the model draws thousands of answers instead of picking one.

Two things are drawn:

- **How each party's support moves.** Parties usually do worse locally than
  nationally. The model measures the gap for each party from its own
  national-to-local transitions on record. A party's starting level blends its
  national result, converted down to local, with its last local result: the
  less record a party has of that gap, the more its local result counts.
  ActionSA polled {{hist_asa_pr_2021}} in this city's 2021 local election and
  {{hist_asa_npe_2024}} in the city in the 2024 national election. It has no
  national-to-local gap on record, so its starting level comes from its local
  result alone. In this forecast its level is set by our judgement instead, at
  17.6% of the list vote: the model carries the 2021 result forward at the
  share a typical party of its size keeps between local elections, and its
  by-elections lift it part of the way back; we judge that ActionSA keeps more
  of its 2021 vote than that. Every other party's share is scaled down in proportion so
  the shares still add up, and ActionSA keeps the model's usual uncertainty
  for a party of that size. It cannot be changed on [your
  forecast](your-forecast/).
- **Turnout, per pool.** It is the one unknown quantity, and it is drawn from
  what turnout has done in that city before. In 2021 every pool's turnout was
  the lowest on record, so the range allows falls as well as rises.

Recent by-elections tilt parties' expected shares before the draws (see *The
judgement calls*, below).

### 5. Handle parties that were not there last time

This is the hardest part of forecasting an election. There are two kinds of
new party, and they behave differently:

- A **split** is a known person leaving a known party and taking some of its
  vote: Zuma leaving the ANC for MK, Malema for the EFF, Mashaba leaving the DA
  for ActionSA. A split starts with a leader, a machine and a share of an
  existing vote. It is sized as a fraction of its parent, from what previous
  splits took. A split that has stood in a national election since, as MK did
  in 2024, takes where its voters are from that result by ward, not from its
  parent.
- An **entrant** is a name on a ballot with none of that. Most new parties are
  entrants, and most get almost nothing.

Before the model told them apart, every party that filed candidates everywhere
was sized like the EFF's 2016 breakthrough. Filing papers is cheap, and in Cape
Town that gave parties that did not exist more votes than the entire
electorate. Separating the two fixed it.

How much a split takes depends overwhelmingly on **whether the leader's own
following is in this city**, not on how famous the leader is. Patricia de Lille was at
least as well known nationally in 2019 as Julius Malema was in 2014; her party
took about one-eighteenth as much of the DA's vote in Johannesburg as it did in
Cape Town.

### 6. Paint the result back onto the map

Each drawn outcome is spread back across all {{n_vds}} voting districts using
each party's own geography: where its votes were last time. This is the
best-tested idea in the model. *Where* a party's support sits barely moves
between elections, even when *how much* it has swings widely.

### 7. Count both ballots and apply the law

Voters split their tickets, so the ward ballot and the party ballot are counted
separately, each party's split measured from its own past behaviour. A party
gets ward votes only in the wards where it has a candidate. A party with ward
candidates and no party list is not on the party ballot; a ward it wins is its
seat, and the list seats are shared among the other parties over the seats that
remain. Ward winners are called race by race. Then the statutory formula, the arithmetic the
Electoral Commission uses, allocates every seat, excessive seats included.

### 8. Do it {{n_draws}} times

Each run draws fresh values within every bound. The output is a distribution:
how often each seat count happens, and how often each coalition clears the
line. Every combination of parties is checked against that run's own majority
line, with no judgement about who would work with whom.

Johannesburg's politics runs on thresholds: a coalition either reaches
{{majority}} seats or it does not. Near a threshold, small uncertainties have
large, lopsided consequences that a single number with an error bar cannot
show.

## What a pool is, and what it is not

A pool is **not** an alliance, a coalition, or a prediction about who will
govern with whom. It describes voters, not parties: a set of parties competing
for the same people. The DA and ActionSA drawing from the same pool means that
when one rises in a simulation the other tends to fall in the same places. The
effect is a mild offset (together they vary less than they would independently),
not a rule that one gains exactly what the other loses.

It is also not a claim about why anyone votes as they do. Aggregate data can
show that a pool of voters moved, not why. A sentence on this site that appears
to explain a voter's reasoning is overreach, and we would like to hear about it.

## How accurate is it?

There are three checks, in increasing order of difficulty.

**The seat law is exact.** The implementation reproduces the published councils
to the seat (quota, vote totals, every party) for eight municipalities across
three elections, from the raw voting-district files. One exception is
documented: the Commission publishes every independent candidate under a single
name, so where several stand in one ward they cannot be told apart, and we take
the Commission's own count of independent ward councillors.

**The geography transfers.** <span data-asof="2026-08-04">Given only citywide
totals for 2021, the model placed the votes well enough to call
{{blind_test_called}} of {{blind_test_of}} ward winners. That test was run on 4
August 2026 and has not been re-run on the current model.</span>

**The whole model beats simple baselines.** It is run on the 2021 election in
{{backtest_cities}} metros and wins in **{{backtest_wins}}** of them on the measure that
scores a forecast's whole range (CRPS), with **{{backtest_crps_better}}** less error in
total. Each metro against its best baseline by that measure, and the seats each
gives to the wrong party (lower is better in every column):

| metro | model's error (CRPS) | best baseline's error (CRPS) | best baseline | seats given to the wrong party: model | seats given to the wrong party: best baseline |
|---|---|---|---|---|---|
| Johannesburg | {{val_joburg_crps}} | {{val_joburg_best_crps}} | {{val_joburg_best}} | {{val_joburg_wrong}} | {{val_joburg_best_wrong}} |
| Tshwane | {{val_tshwane_crps}} | {{val_tshwane_best_crps}} | {{val_tshwane_best}} | {{val_tshwane_wrong}} | {{val_tshwane_best_wrong}} |
| Ekurhuleni | {{val_ekurhuleni_crps}} | {{val_ekurhuleni_best_crps}} | {{val_ekurhuleni_best}} | {{val_ekurhuleni_wrong}} | {{val_ekurhuleni_best_wrong}} |
| eThekwini | {{val_ethekwini_crps}} | {{val_ethekwini_best_crps}} | {{val_ethekwini_best}} | {{val_ethekwini_wrong}} | {{val_ethekwini_best_wrong}} |
| Cape Town | {{val_capetown_crps}} | {{val_capetown_best_crps}} | {{val_capetown_best}} | {{val_capetown_wrong}} | {{val_capetown_best_wrong}} |
| Mangaung | {{val_mangaung_crps}} | {{val_mangaung_best_crps}} | {{val_mangaung_best}} | {{val_mangaung_wrong}} | {{val_mangaung_best_wrong}} |
| Nelson Mandela Bay | {{val_nelsonmandelabay_crps}} | {{val_nelsonmandelabay_best_crps}} | {{val_nelsonmandelabay_best}} | {{val_nelsonmandelabay_wrong}} | {{val_nelsonmandelabay_best_wrong}} |
| Buffalo City | {{val_buffalocity_crps}} | {{val_buffalocity_best_crps}} | {{val_buffalocity_best}} | {{val_buffalocity_wrong}} | {{val_buffalocity_best_wrong}} |
| all {{backtest_cities}} | {{val_total_crps}} | {{val_total_best_crps}} | | {{backtest_seat_err_model}} | {{backtest_seat_err_baseline}} |

The seat columns judge only the single most likely outcome, so their margins
are smaller. It calls the winner in **{{backtest_wards_called}} of {{backtest_wards}}**
wards.

<!-- __VALIDATION__ -->

<!-- __JUDGEMENTS_START__ -->

<!-- Written by src/judgement_sheet.py from the Plain fields in JUDGEMENT-CALLS.md. Edit those; this region is regenerated by the site build. -->

## The judgement calls

These are choices about how the model works that the data did not make for us. Each is filed, with its evidence, in the [register of judgement calls](https://github.com/Psi-am-i/jhb-election-model/blob/main/JUDGEMENT-CALLS.md).

**No poll is used.** There is no designed rule yet for how several polls combine. With polls in, the forecast moves toward the polls the rules admit; what that was worth when measured is under *Where polls fit*, below. On [your forecast](your-forecast/) you can pick one poll at a time and choose how far to believe it.

**The largest parties are pulled down.** Before the simulations are drawn, each party's expected share is cut by an amount that grows with its size, and the vote freed is returned to all parties in proportion to their share. Without the cut, forecasts of past elections gave the largest parties too much and the middle-sized parties too little; adding it was the largest single improvement the model has had. The smallest parties are now forecast slightly too high. It cannot be changed on [your forecast](your-forecast/).

**How far each party's support can move.** Each party's simulated support is drawn from a bell curve on a log scale, so its share is multiplied up or down. The curve is wider for a smaller party and for a party new to the city. Its width is measured from how far the model's expected shares missed in the past elections before this one. Part of each simulation's move is shared by all parties. It cannot be changed on [your forecast](your-forecast/).

**How much recent by-elections count.** Each party's expected share is set halfway between what the model expects from earlier elections and what the by-elections since 2021 imply for it. Nobody knows the right weight, so the two count equally. A party that had a vote in the 2024 national election cannot be moved by its by-elections further than the model's usual range for it allows, so a party whose by-elections imply a very large swing moves less than halfway. A party whose only earlier vote is the 2021 local election has no such range and moves halfway. A party with no earlier vote at all is covered under new parties and by-elections. A party that stood only for ward seats in 2021, and not on the party list, is not moved. In Johannesburg the by-elections reach the forecast; Tshwane's are not yet read. On [your forecast](your-forecast/) you can make by-elections count not at all or fully.

**New parties and by-elections.** A party with no vote in the 2024 national election and none in the 2021 local election, on the list or in a ward, is not moved by its by-elections, and the by-election setting on [your forecast](your-forecast/) does not move it either. A few ward contests are not enough to size a party nobody has measured before; such a party is sized the way earlier new parties did in their first election.

**Turnout moves together across population groups.** In each simulation, turnout in the four population groups rises and falls together, to one degree for every pair: the average of how closely each pair's turnout moved between past local elections in the metros. Black African, Coloured and White turnout have moved closely together, and Indian/Asian turnout much less. Separate figures for each pair have not been tried. Removing the link was tested and changed the forecast's spread very little, and why it matters so little is not yet explained. It cannot be changed on [your forecast](your-forecast/).

**The excessive-seats clause.** The clause is applied as amended in 2021, with the arithmetic the Commission used in Laingsburg in 2021 (see *How Johannesburg's council elections work*). No court has ruled on it. [Your forecast](your-forecast/) applies three versions of Germany's seat law instead; two of them enlarge the council and move the majority line.

**Expected turnout leans on 2021.** Each voting district's turnout is projected from how far turnout fell from the national election to the local election two years later, in 2016 and in 2021, with 2021 counting for 70%. The weight comes from the model's original plan and has never been tested. Turnout fell less in 2016, so weighting the two equally would raise projected turnout. On [your forecast](your-forecast/) you can move the turnout of any or all four population groups at once. A group you leave alone stays at the forecast's turnout.

**What a merger keeps.** When parties merge, or one stands down for another, and only one of them is on the ballot, it inherits 75% of the other's previous vote. The rest goes to the parties that compete for the same voters, as any absent party's vote does. In 2026 ActionSA inherits from Forum 4 Service Delivery, and Rise Mzansi from GOOD. No merger in the record shows how much carries over, so the share is a judgement; a review in September that was not shown our reasoning recommended 50%. A lower share moves the inheriting party down. It cannot be changed on [your forecast](your-forecast/).

<!-- __JUDGEMENTS_END__ -->

## What this does not cover

- **A party that does not exist yet is the hardest case.** Splits and entrants
  are sized separately from the record, but a new formation with a popular
  leader remains the largest single source of error.
- **Overhang's legal fine print is untested in court.** The Commission has never
  published a worked metro overhang example. We put the question to it on 5
  August 2026 and have no answer yet. A 2021 amendment and the Commission's own
  handling of Laingsburg 2021 settle the arithmetic, and the forecast applies
  it.
- **No poll is used in the forecast.** Polls were an input until 12 September
  2026 and are not one now. Why they were taken out, what they were worth, and
  what is planned are under *Where polls fit*, below.
- **Small parties' range is wider than the record.** In the simulations, a
  party that is established but small sometimes reaches a share no such party
  has reached in the record. In the eight metros' consecutive local elections
  from 2006 to 2021, 337 times a party had under {{small_party_share}} of the list vote at
  one election, and none reached {{small_party_surge_share}} at the next ([model log, §1.296](https://github.com/Psi-am-i/jhb-election-model/blob/main/MODEL-LOG.md)).
  In this forecast, {{small_party_surge}} of the simulations give at least one such
  party more than {{small_party_surge_share}}. A fix is in progress.
- **Arithmetic is not politics.** The model says which governments are
  numerically possible, not which will form.

## Where polls fit

Polls were an input to the forecast until 12 September 2026. Since then, none
is.

**If the forecast ever differs from a no-polls model, this section is out of
date and the forecast is what to believe.**

### Why they were taken out

There was no designed answer to how several polls should combine: how much two
waves from one house count against one wave from another, how a party-internal
poll is discounted, how a national poll and a metro poll combine. The weighting
was defensible one poll at a time and improvised across several. The channel is
off until that is designed. Removing polls is not a judgement that they are
worthless.

### What they were worth, measured

The aim is to score {{backtest_target}} past city elections across the country,
eight metros with three elections each; how many are in the panel on a given
day depends on which have been prepared. Against the panel as it stood,
removing polls changed the total seat error from
{{polls_off_seat_err_before}} to {{polls_off_seat_err_after}} and the
distributional score (CRPS) from {{polls_off_crps_before}} to
{{polls_off_crps_after}}. Both moved the right way and neither by much: seven
elections moved at all, one of them by six seats *against* the change. **The
poll channel's contribution cannot be distinguished from zero.** That is a
reason not to let it move a published headline while its design is unsettled.

### What we intend

We intend to use every poll received and to put the weighting in the
reader's hands.
[Your forecast](your-forecast/) has a first version: you choose how far to trust
each poll, and the published simulations are re-weighted in your browser. The
published forecast uses no poll.

### Why polls are read with caution

The polls that exist disagree with each other by more than the quantity being
forecast: one house had the DA on {{poll_srf_q2_da}} and the ANC on {{poll_srf_q2_anc}} in the same year
another had the ANC on {{poll_ipsos_w2_anc}} and the DA on {{poll_ipsos_w2_da}}. Metro-level polling has little
track record here to weight it by; pre-2021 polling missed ActionSA in this
city by about ten points. Every poll we hold is listed, with its caveats, and
the model is read against them as an outside check. They are not, at present,
an input.

## Corrections and review

After the first version of this forecast was built, a review found six
implementation errors, one of which made its main claim false. All six were
fixed, and the forecast changed materially. The errors and the repairs are on
the [review page](review). Errors that reached readers since are on the
[corrections page](corrections).

## Going deeper

The code, the data recipes, the log of findings and mistakes, and the known
defects in the public records the model depends on are published:

- [the repository](https://github.com/Psi-am-i/jhb-election-model)
- `MODEL-LOG.md`: every finding, obstacle and decision, in order, including the
  ones that went badly
- `DATA-QUALITY.md`: defects in the official published records, with the ward
  and the arithmetic for each
- `SOURCES.md`: where every input came from and how to fetch it again
