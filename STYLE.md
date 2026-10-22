# How the site talks to readers

Applies to every reader-facing word: pages, corrections, claims, UI text, share
images, marketing copy. Owner, 2026-10-01.

0. **The tone is dry.** State the fact and stop; the reader draws the conclusion.
   Understatement over emphasis. If a figure is damning, print the figure. If a
   claim failed, show the result next to the claim. Do not explain the joke.

1. **Every sentence carries information.** If the reader already knows it, or it
   restates the sentence before, delete it.
   - ✗ "Your forecast is yours, and the page says so — ours stays where it is, and
     a small note shows how far apart the two are."
   - ✓ "The note under your council shows how far it is from the model's forecast."

2. **Say what is, not what isn't.** Do not report that something did not change,
   was not affected or still holds, unless the reader would reasonably assume
   otherwise.

3. **Corrections have two parts and nothing else.** *What was wrong*: quote the
   wrong sentence, give the reason in one or two lines. *What changed*: the new
   wording or figure. No re-explaining the box, no defending the old text, no
   list of what stayed the same.
   - ✓ "**What was wrong.** We said the DA and the ANC are 'the most reliable
     majority in the city that does not involve the EFF or MK'. Many governing
     majorities occur in most simulations; DA + ANC is only the most common
     *two-party* one. **What changed.** The sentence now says 'the most reliable
     two-party majority in the city'."

4. **No lilt.** No em-dash asides for voice, no paired clauses for rhythm, no
   reassurance, no editorial adjectives ("strikingly", "crucially").

5. **Short beats complete.** One clause per idea. A caveat that matters gets its
   own short sentence; one that does not, goes.

6. **Plain words, the reader's units.** Seats and chances (rule 10). No
   internal terms (draws, cells, pools, CRPS, trust units) unless the page
   explains them where they appear.

7. **Neutral by construction.** Parties in alphabetical or numeric order. No
   verdict words about a party's prospects ("fantasy", "special universe"). The
   figures carry the judgement.

8. **Numbers are tokens, never typed** (CLAUDE.md §2). This guide covers the words
   around them.

9. **A standfirst never restates the first paragraph.** Either the standfirst says it or the body does. Every sentence has a subject and a verb.

10. **Chance in headlines, simulations in explanations.** Headlines, ledes, tiles, verdicts, banners and share images state a chance ('47% chance it's the ANC'). The simulations are how the chance is measured; say so where the method is explained (methodology, footnotes, how to read), not in the claim.

11. **Forecast, prediction, result: three different things** (owner, 2026-10-07).
    Every reader-facing word uses them in this sense and no other.

    | term | what it is | how it is drawn |
    |---|---|---|
    | **forecast** | how often each thing happens across all the model's simulations of the election: chances, ranges, middles | stripes on contested wards, bands, ranges, chances |
    | **prediction** | one complete scenario: a winner in every ward, a vote share and a seat count for every party, the seats adding up to the council. It must be a result that could happen | solid ward colours, single numbers, no ranges |
    | **result** | what the election produces; it is compared with a prediction number for number | as a prediction |

    - **Ours:** `/forecast` is our forecast. Our prediction is the single scenario
      we call, and the one a share card titled with our name shows.
    - **Readers'** entries are predictions. A reader who moves the model's
      levers is changing a forecast; the entry they share and are scored on is
      a prediction.
    - A chance printed beside a prediction is the forecast's chance of
      something in that prediction, not a property of the prediction. In
      "Analyse my forecast" it is the chance of each party's seats and vote
      landing near the reader's ("Chance it lands within 2 seats"; "We give
      this outcome an N% chance") and of each ward call. A share card prints
      no chance: its badge says how close the prediction is to ours, in words
      (JUDGEMENT-CALLS §N10), and no figure of that closeness is printed.
    - ✗ "Your forecast: the ANC on N seats." ✓ "Your prediction: the ANC on N seats."
    - ✗ "Our prediction gives the ANC between A and B seats." ✓ "Our forecast
      gives the ANC between A and B seats."
    - Code identifiers (`score_forecasts`, `forecastSpec`, `ward_calls`) predate
      these terms and keep their names; their docstrings say which of the three
      they hold.
