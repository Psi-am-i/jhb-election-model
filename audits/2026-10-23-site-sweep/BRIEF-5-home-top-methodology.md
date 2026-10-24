# Brief 5: the home page's top, and the methodology page

Owner's answers, 2026-10-25: `OWNER-DECISIONS-ANSWERED.md` item 38 (part A)
and `OWNER-DECISIONS.md` item 39 (part B, **not yet answered: do not start
part B until this file says it is**). Branch `site-sweep-1`. A writer makes
the edits; I review the diff; then the publish build and UAT. Every
reader-facing word below is the owner's or approved by them; **add no other
words** (memory `no-unapproved-reader-words`). If an edit seems to need a word
this brief does not give, stop and list it in the report.

## Part A. The home page's top (`content/joburg/home.toml`, `src/render_home.py`)

1. **Headline.** Three sentences, the first two as now:
   "<em>A coalition is all but inevitable.</em> The largest party is too close
   to call. It is {word} that the council will not match the vote
   proportionally."
   - `{word}` is a new figure-chosen phrase, `lede_overhang_word`: the claims
     scale's verdict (`render_sheet`'s scale, JUDGEMENT-CALLS "Verdicts", with
     its edge rule and judged on the printed chance) for the chance the clause
     applies to `lede_overhang_party` (the ANC today, 87% → VERY LIKELY →
     "very likely"), lower-cased. One definition: call the scale, do not copy
     its bands.
   - Only QUITE LIKELY, VERY LIKELY and NEAR CERTAIN read as "It is … that";
     below QUITE LIKELY the build stops with a message saying the owner has
     not given words for that case.
   - Register the new phrase in `render_home`'s phrase table beside
     `lede_coalition` and `lede_race`.
2. **Paragraph 1**: the ward sentence and "Chance of one party winning
   outright: …" exactly as now, with their tokens and arrows.
3. **Paragraph 2** (replaces "Proportional representation is meant to … should
   allow."): "Proportional representation is designed to give each party seats
   that match their support. Direct representation lets voters elect a
   specific person to represent them. Our local government elections are a mix
   of both: we directly elect ward councillors and then each party is
   allocated additional seats so that each party's percentage of the council
   matches their percentage of the vote. There is an edge case where this
   doesn't happen."
4. **Paragraph 3** (replaces "That is surprisingly likely … party-list
   vote."): "A ward you win cannot be taken away, so a party that wins many
   wards can end up with more council seats than its share of the vote should
   allow. This Model gives {a/an} {p_overhang} chance of this happening with
   {overhang_party} this year. It forecasts that they will hold about
   {overhang_seats} of the seats with only {overhang_votes} of the vote."
   - "a" or "an" is chosen by how the printed figure is spoken (an 8%, an
     11%, an 18%, an 80-89%; a otherwise). Test the edges.
   - `{p_overhang}`, `{overhang_party}`, `{overhang_seats}`: the existing
     tokens and phrases.
5. **`{overhang_votes}` becomes the combined vote.** Schedule 1 items 12-13
   and 16 count a party's party-list and ward-candidate votes together, and
   so does `seats.eligible_parties`; the page compared seats with the
   party-list vote alone. New token `home.overhang_vote_share`: the party's
   median share of the combined votes (ward + list) over all parties, the
   statute's A, independents' ward votes excluded, in the simulations where
   the clause applies to it, from the published draws' `ward_vote` and
   `list_vote` blocks joined as `_overhang` joins now. Report the value (my
   probe: 0.2301) and how independents appear in those blocks.
   - Tooltip: "SOURCE: This Model. The middle share of the votes, ward and
     party-list together, won by the party the excessive-seats clause applies
     to most often, in the simulations where it applies."
   - `home.overhang_list_share` is no longer printed; leave its retirement to
     `revive_retire.py` and extend that script so it is handled, or `--apply`
     stops.
   - Docstrings of `_overhang` and the phrase table say which vote it is.
6. **Layout.** The three paragraphs are three `<p class="sub">`-styled
   paragraphs (or the page's existing paragraph style); check a phone width.

## Part B. The methodology page — waits for item 39

Apply item 39's answer as given. As recommended, which may change:

7. `src/build_validation.NOTICE` becomes "We have withdrawn our scores for
   previous elections while they are re-run." `tests/test_quarantine.py`
   stays the guard; update its expected text if it pins it.
8. Delete from the judgement calls' Plain fields in `JUDGEMENT-CALLS.md` (the
   source of the methodology region): the three sentences beginning "Those
   tests' settings had been chosen on the same election(s)" / "That test's
   settings", and the cut's sentence "without the cut those tests gave …".
   Regenerate the region; edit nothing in it by hand.
9. Delete the ActionSA sentence "From 21 to 23 October ActionSA's level …
   withdrawn on 23 October." and its token's use.
10. Delete the subsection "What they were worth, measured".
11. "Corrections and review" becomes: "This Model is constantly reviewed,
    errors found and fixed. We have given an example of this process on the
    [Review page](review). Errors that reached readers are on the
    [corrections page](corrections)."

## Limits

- No forecast number changes; no `montecarlo.py`, no re-emit, no writes under
  `data/` (run `src/backup_ignored.py` first if anything must).
- Full CPU is allowed. Targeted tests (`tests/run_all.py -k ...`), including
  `render_home`'s, the quarantine guard and the judgement sheet; no whole
  suite.
- Re-render the pages the changes reach and commit, one commit per part.
  Do not run `revive_retire.py --apply`, `build_site.py --publish`, or deploy.
- Do not sub-delegate. Report: each change with before and after text, the
  new token's value, any other page that compares seats with the party-list
  vote (list them, change nothing), test output, commits.
