# How the model was broken — and fixed

Most forecasts show you their conclusions. This page shows you our mistakes.
After the first version of this model was built, we reviewed it the way a
hostile examiner would — against its own written plan, line by line, output by
output. The review found **six implementation errors**, one of which made the
forecast's original headline claim outright false. Every error was fixed the
same day, the forecast changed materially, and the full technical audit is
published, warts and all, in
[`model-review.html` on GitHub](https://github.com/Psi-am-i/jhb-election-model/blob/main/model-review.html).
Here is what happened, in plain language — and why we think publishing it
makes the forecast more worth your trust, not less.

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
**61% of the very same simulations**. The published conclusion wasn't wrong
because the maths was wrong; it was wrong because a human had quietly
filtered the question through political taste, which is exactly what the plan
had forbidden.

## The other five, briefly

- **The plan's own scepticism about MK was silently discarded.** The plan
  said MK — a party with no local-government machinery — should be expected
  to underperform its national result. The simulation's internals quietly
  centred MK on holding its ground instead, making an MK collapse nearly
  impossible to draw. The plan and the code disagreed, and nobody had
  noticed.
- **Ward winners were never actually counted.** The forecast allocated seats
  from vote totals but skipped predicting who *wins each ward* — which is
  the step that detects overhang, the council growing beyond 270. The plan
  had flagged overhang as a live risk. It turned out to be the modal outcome,
  and the first forecast simply could not see it.
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

There were also data bugs found along the way — including 87 district-year
records where more people had voted than were registered, a sign of broken
registration counts that had quietly poisoned the turnout projections.

## What the fixes changed

The corrected forecast is meaningfully different from the one first computed:

- **Overhang went from invisible to the headline.** In roughly nine
  simulations in ten, the ANC wins more wards than its shrunken vote entitles
  it to, the council grows past 270, and the majority bar rises to about 141.
- **The DA's dominance shrank.** Largest party in 63% of simulations, not
  86% — the ANC's overhang seats close the gap.
- **A kingmaker verdict flipped.** The first sheet asserted the Patriotic
  Alliance mattered more to coalition-building than ActionSA. Computed
  properly, it is the other way around.
- **The realistic outcomes clarified into three:** a grand coalition, a
  DA-led minority government resting on abstention (viable in 61% of
  simulations), or a DA arrangement with one of the parties it has publicly
  ruled out.

## What the review could not fix

Honesty about the repairs requires honesty about the remainder. A party that
does not yet exist cannot be forecast, only allowed for. The legal fine print
of overhang has never been demonstrated in a published calculation by the
electoral commission — obtaining one is now the top open item. And the range of possible 2026 outcomes
is judgement that no amount of testing can turn into fact: bounded by twenty
years of observed swings, tilted by current evidence, and fully exposed as
adjustable dials on the [interactive page](interactive).

## Why publish this at all

Because the alternative is worse. Every model contains errors; the only
question is whether they are found, and whether anyone is told. This one was
reviewed hard enough to break, fixed in the open, and re-checked — the
review, the fixes and the re-run are all in the public repository. A forecast
that shows you its repair history is one you can calibrate your trust
against. One that doesn't is asking you to take it on faith.
