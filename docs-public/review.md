# How the model is tested

<div class="pubdate">6 August 2026: Published</div>

This page shows how the model is improved. Each version is reviewed the way a
hostile examiner would, against its own written plan, line by line and output
by output, and the errors found are fixed and published. What follows is that
review of the very first version; the same process is applied to each revision
since.

The review of the first version found **six implementation errors**, one of which made the
forecast's original headline claim outright false. Every error was fixed the
same day, and the forecast changed materially.
Here is what happened, in plain language — and why we think publishing it
makes the forecast more worth your trust, not less.

<aside class="since"><div class="since-h">{{generated_date}}: what This Model says now</div>
<p>The figures below describe This Model as it stood on 6 August 2026: the first version, and
the version after its fixes.
The largest party today: {{p_anc_largest}} chance it's the ANC alone and {{p_da_largest}} chance
it's the DA alone. Two or more parties tie for the most seats: {{p_largest_tied}} chance. The ANC
triggers the excessive-seats clause: {{p_excessive_anc}} chance. A chance is the share of the
{{n_draws}} simulations in which the outcome happens. No
poll has been an input since <span data-asof="2026-09-12">12 September 2026</span>. The page is a record of how the
errors were found and fixed. Errors in the page itself are corrected in place and listed on the
<a href="corrections">corrections page</a>.</p></aside>

<span data-asof="2026-08-06">

## The error that mattered most

The first version of the forecast declared: *no two- or three-party coalition
can reach a majority except the ANC and DA together.* That claim was false —
and the model's own simulations proved it false, because nobody had asked
them.

The plan the model was built from had been explicit: check **every**
combination of parties, mechanically, with no opinions about who would
plausibly govern with whom — precisely because South African coalition
politics has a habit of making yesterday's unthinkable arrangement tomorrow's
government. The build ignored that instruction and checked six hand-picked,
"realistic" coalitions. When the full check was finally run, a combination
nobody had thought to test — DA + EFF + MK — cleared the majority line in
**{{rev0806_da_eff_mk_share}} of the very same simulations**. The published conclusion wasn't wrong
because the maths was wrong; it was wrong because a human had quietly
filtered the question through political taste, which is exactly what the plan
had forbidden.

</span>
<span data-asof="2026-08-06">

## The other five, briefly

- **The plan's own scepticism about MK was silently discarded.** The plan
  said MK — a party with no local-government machinery — should be expected
  to underperform its national result. The simulation's internals quietly
  centred MK on holding its ground instead, making an MK collapse nearly
  impossible to draw. The plan and the code disagreed, and nobody had
  noticed.
- **Ward winners were never actually counted.** The forecast allocated seats
  from vote totals but skipped predicting who *wins each ward* — which is
  the step that detects excessive seats: a party winning more wards than its
  vote entitles it to. It keeps those wards and gets no list seats, and the
  other parties share the remaining seats of the fixed 270-seat council. The
  plan had flagged this as a live risk. It happened in most simulations, and
  the first forecast could not see it.
- **Real evidence was collected and then ignored.** Fifteen by-elections and
  the published polls had been gathered — and influenced nothing. The
  forecast cited them as sources while its numbers rested entirely on
  historical patterns. They are now wired in, with their weight adjustable.
- **The validation was oversold.** The sheet said the model was tested
  "without being shown the answer". In truth the test had been given the
  citywide totals and only had to place them geographically. Genuinely
  blind, the seat error is five times larger. The claim now says exactly
  what was and wasn't tested.
- **Small parties moved in lockstep.** Every minor party rose and fell
  together in the simulations, producing absurdly confident seat ranges for
  them. They now move independently, with ranges set from their actual
  history.

There were also data bugs found along the way — including {{rev0806_overvote_records}} district-year
records where turnout was above 105% of registered voters, a sign of broken
registration counts that had quietly poisoned the turnout projections.

</span>
<span data-asof="2026-08-06">

## What the fixes changed

The corrected forecast is meaningfully different from the one first computed:

- **The excessive-seats clause went from invisible to the headline.** In
  most simulations, the ANC wins more wards than its shrunken
  vote entitles it to — and (as we later confirmed from the statute and a real
  2021 precedent) it keeps them all, gets zero list seats, and the shortfall
  comes out of everyone else's list seats, inside a fixed 270.
- **The DA's dominance shrank.** Largest party in {{rev0806_da_largest_fixed}} of simulations, not
  {{rev0806_da_largest_first}} — the ANC's overhang seats close the gap.
- **A kingmaker verdict flipped.** The first sheet asserted the Patriotic
  Alliance mattered more to coalition-building than ActionSA. Computed
  properly, it is the other way around.
- **The realistic outcomes clarified into three:** a grand coalition, a
  DA-led minority government resting on abstention (viable in {{rev0806_da_minority_viable}} of
  simulations), or a DA arrangement with one of the parties it has publicly
  ruled out.

</span>
<span data-asof="2026-08-06">

## What the review could not fix

Honesty about the repairs requires honesty about the remainder. A party that
does not yet exist cannot be forecast, only allowed for. The excessive-seats
clause has never been tested in court. The Electoral Commission's own published
calculation for Laingsburg in 2021 applies it; we put our reading to the
Commission on 5 August 2026 and are awaiting its answer. And the range of possible 2026 outcomes
is judgement that no amount of testing can turn into fact: bounded by twenty
years of observed swings, tilted by current evidence, and fully exposed as
adjustable dials on the interactive page.

</span>
<span data-asof="2026-08-06">

## Why publish this at all

Because the alternative is worse. Every model contains errors; the only
question is whether they are found, and whether anyone is told. This one was
reviewed hard enough to break, fixed in the open, and re-checked — the
review, the fixes and the re-run are all in the public repository. A forecast
that shows you its repair history is one you can calibrate your trust
against. One that doesn't is asking you to take it on faith.

</span>
