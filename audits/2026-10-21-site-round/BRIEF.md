# Site round, 21 October 2026 (before go-live)

Owner, 2026-10-21, verbatim:

> on hme put yor forecast block under the forecast put it in a half width
> column next to articles. Put what is this in a single columnn above the
> footer. on our forecast put the share button by map and after each section
> of forecast.
> on your forecast - the column with all the parties, put PAC under AIC and
> put everyone below under "other parties" - then list other parties
> alphabetically - ward vote is an oidd thing to ask across a map. We should
> tell them to set the list vote since they have already called the wards.
> the last two party claims dont read right. if you read quote - then our
> judgement they dobt go together. We are taking the quote and turning it
> into a claim - then judging it. the claim and judgemt should go together.
> Review - headline "How the model is tested" And intoduction should explain
> that this is an exposition of how the model is improved. It is discussing
> the very first version, but the same process applies to each revision.
> corrections remove every instance of "the page says" - which is meanimgless

> the parties which have largest vote in our model are shown, the rest are hidden

Written before the code; not amended after.

## Items

1. **Home.** Order: lede; the forecast (map and seats); then two half-width
   columns, the articles at the left and the "Your Forecast" block at the
   right; the party claims; "How this is built"; then "What this is" in one
   full-width column, last before the footer. No text changes.
2. **/forecast.** The page's share button (the one sheet `build_site.share_button`
   already writes) gets a second opener beside the map ("Who wins where") and
   one at the end of each `<h2>` section of the forecast (the sections from
   "Who wins where" to "Who can govern"). Every opener opens the same sheet
   for the same page link. No new share target.
3. **/your-forecast/, section 2, the vote column.**
   a. Order: the parties by their list vote in our prediction (the published
      start), largest first. Shown: each party at or above 0.25% of the list
      vote in our prediction (`make.js`, a named constant; the published start
      puts PAC and AIC above it and the next party, at 0.20%, below). The
      rest go in the collapsed "Other parties", alphabetically. A party with
      no PR list is ordered by its ward vote.
   b. The reader sets the LIST vote. Each row's slider and box are the
      party's list vote, as a percent of the list ballot. Its ward vote
      follows at the gap it had (the engine's existing rule, run the other
      way: the page sets the ward vote to the asked list share minus the
      party's current gap, and the list follows at that gap). The collapsed
      control under each row becomes "Adjust ward vote": the ward vote as
      points from the list vote. A party with no PR list keeps a ward-vote
      slider, labelled as the ward vote. The slider's ends are the party's
      ward limits for the called wards plus its gap. The column heading says
      "List vote" and the totals line is unchanged. No change to
      `builder-state.js`, the seat law or Rule A.
4. **Claims (all five, one rule).** The verdict moves from beside the
   speaker to beside the claim we test: after the quote, one line holding the
   claim's label (`claims.toml` `label`) and its verdict together. The speaker
   line keeps the party, the speaker and the source.
5. **/review.** Title "How the model is tested". The introduction says the
   page shows how the model is improved: each version is reviewed against its
   own plan and the errors found are fixed and published; this page is that
   review of the first version, and the same process is applied to each
   revision. The rest of the page is unchanged. The home page's link text
   follows the title.
6. **/corrections.** No "The page says": each "What is right." states the
   right fact.

## Checks (QC.md §4b)

Diff reviewed by another agent before the build. Then: the site build and
`deploy_check`; the page tests for each page touched (`-k` home, forecast
sheet, your_forecast, claims, published_page, model_claims); the whole suite
once for the UAT version.
