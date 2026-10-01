# Proposed STYLE.md rewrites of /review (published 6 August 2026) — for the owner

Source: `docs-public/review.md`. The page is a published, dated piece: its
`pubdate` reads "6 August 2026: Published", its body is in
`<span data-asof="2026-08-06">` passages, and it carries a "what the model says
now" box. Under the publication convention that body is frozen, so none of
this is applied. Applied in this sweep: the "what the model says now" box (live
text) and the kicker/standfirst in `src/build_site.py` (site chrome).

Typed figures inside the dated spans (61%, 87, 63%, 86%, "six of seven",
"five times") are kept exactly; nothing is added. The `data-asof` wrappers
stay.

Two statements in the body are no longer true and are not style questions:
"They are now wired in, with their weight adjustable" (polls; no poll has been
an input since 12 September) and "the council growing beyond 270" (the law
fixes the council at 270; the page's own later section says so). HANDOVER lists
the first as fix-soon. Under the convention they need a dated note or a
correction, not a silent edit; that is the owner's call.

---

## Intro (outside the spans)

Before:

> After the first version of this model was built, we reviewed it the way a hostile examiner would — against its own written plan, line by line, output by output. The review found **six implementation errors**, one of which made the forecast's original headline claim outright false. Every error was fixed the same day, the forecast changed materially, and the full technical audit is published, warts and all, in [`model-review.html` on GitHub](…). Here is what happened, in plain language — and why we think publishing it makes the forecast more worth your trust, not less.

After:

> After the first version of this model was built, it was reviewed line by line and output by output against its own written plan. The review found **six implementation errors**, one of which made the forecast's headline claim false. Every error was fixed the same day, and the forecast changed materially. The full technical audit is in [`model-review.html` on GitHub](…).

## The error that mattered most

Before:

> The first version of the forecast declared: *no two- or three-party coalition can reach a majority except the ANC and DA together.* That claim was false — and the model's own simulations proved it false, because nobody had asked them.
>
> The plan the model was built from had been explicit: check **every** combination of parties, mechanically, with no opinions about who would plausibly govern with whom — precisely because South African coalition politics has a habit of making yesterday's unthinkable arrangement tomorrow's government. The build ignored that instruction and checked six hand-picked, "realistic" coalitions. When the full check was finally run, a combination nobody had thought to test — DA + EFF + MK — cleared the majority line in **61% of the very same simulations**. The published conclusion wasn't wrong because the maths was wrong; it was wrong because a human had quietly filtered the question through political taste, which is exactly what the plan had forbidden.

After:

> The first version of the forecast said: *no two- or three-party coalition can reach a majority except the ANC and DA together.* The model's own simulations showed that to be false; they had not been asked.
>
> The plan required checking **every** combination of parties, with no view on who would govern with whom. The build checked six hand-picked coalitions instead. Run in full, the check found DA + EFF + MK clearing the majority line in **61% of the same simulations**. The arithmetic was right; the question had been filtered by political judgement, which the plan forbade.

## The other five, briefly

Before (first bullet):

> **The plan's own scepticism about MK was silently discarded.** The plan said MK — a party with no local-government machinery — should be expected to underperform its national result. The simulation's internals quietly centred MK on holding its ground instead, making an MK collapse nearly impossible to draw. The plan and the code disagreed, and nobody had noticed.

After:

> **The plan's scepticism about MK was dropped.** The plan said MK, a party with no local-government machinery, should be expected to underperform its national result. The simulation centred MK on holding its ground instead, which made an MK collapse nearly impossible to draw.

Before (second bullet):

> **Ward winners were never actually counted.** The forecast allocated seats from vote totals but skipped predicting who *wins each ward* — which is the step that detects overhang, the council growing beyond 270. The plan had flagged overhang as a live risk. It turned out to be the modal outcome, and the first forecast simply could not see it.

After (wording only; see the note above on "growing beyond 270"):

> **Ward winners were not counted.** The forecast allocated seats from vote totals and did not predict who *wins each ward*, the step that detects overhang, the council growing beyond 270. The plan had flagged overhang as a risk. It was the most common outcome, and the first forecast could not see it.

Before (third bullet):

> **Real evidence was collected and then ignored.** Fifteen by-elections and the published polls had been gathered — and influenced nothing. The forecast cited them as sources while its numbers rested entirely on historical patterns. They are now wired in, with their weight adjustable.

After (wording only; see the note above on "wired in"):

> **Evidence was collected and not used.** Fifteen by-elections and the published polls had been gathered and influenced nothing. The forecast cited them as sources while its numbers rested on historical patterns. They are now wired in, with their weight adjustable.

Before (fourth bullet):

> **The validation was oversold.** The sheet said the model was tested "without being shown the answer". In truth the test had been given the citywide totals and only had to place them geographically. Genuinely blind, the seat error is five times larger. The claim now says exactly what was and wasn't tested.

After:

> **The validation was overstated.** The sheet said the model was tested "without being shown the answer". The test had been given the citywide totals and only had to place them geographically. Fully blind, the seat error is five times larger. The claim now says what was tested.

Before (fifth bullet):

> **Small parties moved in lockstep.** Every minor party rose and fell together in the simulations, producing absurdly confident seat ranges for them. They now move independently, with ranges set from their actual history.

After:

> **Small parties moved in lockstep.** Every minor party rose and fell together in the simulations, which made their seat ranges far too narrow. They now move independently, with ranges set from their history.

Before (closing paragraph):

> There were also data bugs found along the way — including 87 district-year records where more people had voted than were registered, a sign of broken registration counts that had quietly poisoned the turnout projections.

After:

> Data errors were also found, including 87 district-year records where more people voted than were registered. The broken registration counts had distorted the turnout projections.

## What the fixes changed

Before:

> The corrected forecast is meaningfully different from the one first computed:
>
> - **The excessive-seats clause went from invisible to the headline.** In roughly six of seven simulations, the ANC wins more wards than its shrunken vote entitles it to — and (as we later confirmed from the statute and a real 2021 precedent) it keeps them all, gets zero list seats, and the shortfall comes out of everyone else's list seats, inside a fixed 270.
> - **The DA's dominance shrank.** Largest party in 63% of simulations, not 86% — the ANC's overhang seats close the gap.
> - **A kingmaker verdict flipped.** The first sheet asserted the Patriotic Alliance mattered more to coalition-building than ActionSA. Computed properly, it is the other way around.
> - **The realistic outcomes clarified into three:** a grand coalition, a DA-led minority government resting on abstention (viable in 61% of simulations), or a DA arrangement with one of the parties it has publicly ruled out.

After:

> The corrected forecast differs materially from the first:
>
> - **The excessive-seats clause became the headline.** In about six of seven simulations the ANC wins more wards than its vote entitles it to. It keeps them all and gets no list seats, and the shortfall comes out of the other parties' list seats inside a fixed 270, as the statute and a 2021 precedent later confirmed.
> - **The DA's lead shrank.** Largest party in 63% of simulations, not 86%; the ANC's overhang seats close the gap.
> - **A kingmaker finding reversed.** The first sheet said the Patriotic Alliance mattered more to coalition-building than ActionSA. Computed correctly, it is the other way round.
> - **Three outcomes remained:** a grand coalition, a DA-led minority government resting on abstention (viable in 61% of simulations), or a DA arrangement with one of the parties it has publicly ruled out.

## What the review could not fix

Before:

> Honesty about the repairs requires honesty about the remainder. A party that does not yet exist cannot be forecast, only allowed for. The legal fine print of overhang has never been demonstrated in a published calculation by the electoral commission — we put the question to the Commission on 5 August 2026 and are awaiting its answer. And the range of possible 2026 outcomes is judgement that no amount of testing can turn into fact: bounded by twenty years of observed swings, tilted by current evidence, and fully exposed as adjustable dials on the interactive page.

After:

> A party that does not yet exist cannot be forecast, only allowed for. The Electoral Commission has never published a calculation demonstrating the legal fine print of overhang; we put the question to it on 5 August 2026 and have no answer yet. The range of possible 2026 outcomes is judgement that testing cannot turn into fact: bounded by twenty years of observed swings, tilted by current evidence, and exposed as adjustable dials on the interactive page.

## Why publish this at all

Before:

> Because the alternative is worse. Every model contains errors; the only question is whether they are found, and whether anyone is told. This one was reviewed hard enough to break, fixed in the open, and re-checked — the review, the fixes and the re-run are all in the public repository. A forecast that shows you its repair history is one you can calibrate your trust against. One that doesn't is asking you to take it on faith.

After (heading: "The record"):

> The review, the fixes and the re-run are in the public repository.
