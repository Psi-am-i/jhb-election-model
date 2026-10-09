# Brief: site batch of 2026-10-09 (owner's notes)

Site and interactive changes under QC.md §4b. They run in parallel with the
prediction restructure and must not stop it. The owner approves this brief
before any page code changes. Items 6 and 7 are read-only research and
generation into this directory, so they start now.

## Items

1. **One callout box: what you changed, what actually moved.** Two sections at
   the top and bottom of the forecast's lever area are hidden today (owner's
   screenshots 01.06.55 and 01.07.01, not yet readable here). They are merged
   into one well-laid-out box with two parts:
   - what the reader changed;
   - what moved as a result.

   The purple box appears at both the top and the bottom of the forecast.
   Coordinated with prediction-restructure Phase 2, which moves the levers to
   `/forecast`, so it is built once.
2. **The same for the prediction.** What the reader changed from our prediction,
   and what that does to the council. The wording is to be designed, and the
   owner reviews it.
3. **"Our chance, within N seats" columns** (screenshot 01.09.22; `make.js`
   `paintAnalysis`). The column is the forecast's chance that the party's real
   result lands within N seats of the reader's number, or within N points on
   the list vote. Reworded so it says that; one definition of N is kept.
4. **A call-to-action redesign** (screenshot 01.42.48). A front-end designer
   returns options as mock-ups before anything is built.
5. **A home page introduction**, in the owner's words, edited to STYLE.md:
   - what the site is and how the model works;
   - judgement calls declared and alterable;
   - no opinion polls;
   - the baseline comparison;
   - why: a history-derived base forecast that local knowledge can adjust;
   - built from voting districts up;
   - unaffiliated, primary sources.

   Every figure is a token from where it is generated. The "34%" must be found
   at its source or not used. Lives in `content/joburg/home.toml`. The owner
   approves the text before it is built.
6. **How Johannesburg elections work.** A summary of the mechanism and the law,
   citing the statutes by section and item. It is a research step: the
   citations are checked against primary sources before any text is written.
7. **Animated maps.**
   - Our forecast map, with stripes on contested wards, for each previous
     Johannesburg election the model can forecast (each from data before that
     election).
   - The real winners' maps for each election with ward boundaries on disk.
   - Both animated as GIFs, as a starting point for "what changed and what did
     not".
   - Generated into this directory first. Publishing is a later decision.

## Out of scope

Any forecast number or model change. The prediction restructure's own items.

## Tiers

- Items 1, 2 and 4: interactive behaviour (page node tests, `yf_jump_check`,
  screenshots).
- Items 3, 5 and 6: cosmetic (page modules, `number_scan`, screenshots).
- Item 7: generation only, with no site change until approved.

8. **Each party's best case, and what had to happen** (owner, 2026-10-09). The
   owner, verbatim: "find a per party best result map and analyse what happened
   for this to occur (everything is within historical bounds... which means
   it's possible) What happened in these simulations to give these outcomes?"
   - For each party, the best 1% of simulations by its seats is analysed. The
     single most extreme draw is one in 5,000 and says little.
   - The analysis covers what those simulations have in common: turnout by
     voter group, each party's vote on both ballots, which wards flipped from
     the usual winner, and whether excessive seats fired.
   - One representative map is drawn from the group.
   - Under STYLE.md rule 11 a single simulation is neither our forecast nor our
     prediction, and is labelled "one of the simulations".
   - Read-only analysis into `best-cases/` first; publishing is a later
     decision.
