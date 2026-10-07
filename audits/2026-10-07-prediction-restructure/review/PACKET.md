# Blind review packet: forecast, prediction, result

Issued verbatim to two independent reviewers, 2026-10-08. Do not rewrite it.

## Ground rules

- **Read-only.** Do not edit any file in the repository. Do not run
  `src/montecarlo.py`, `src/compare_history.py`, `src/build_site.py`,
  `src/pools.py --emit` or anything else that writes into `data/`, `site/`,
  `content/` or `publications/`. Scratch files go in the scratch directory you are
  given, nowhere else. Use `.venv/bin/python`.
- **Do not sub-delegate** to other agents.
- **Do not read** `audits/2026-10-07-prediction-restructure/BRIEF.md` (this packet
  contains it) or anything under `~/.claude/`.
- Read `CLAUDE.md`, `STYLE.md` (rule 11 especially) and `QC.md` §4b first.
- For every claim you make, say whether you **verified** it (file and line, or a
  computation you ran, with the command) or are **arguing** it.

## The problem, in the owner's words (verbatim)

1. "the forecast page gives specific party numbers that add to the council size.
   many share sheets say the opposite. the correct share sheet is the reader card
   full. which show change vs 2021 % of seats and % of votes and pure seats."
2. "One typical simulation sounds random. How is a reader meant to understand what
   our prediction is or theirs? A prediction MUST match a possible reality.
   Period. While our model gives a range to everything - when it comes to a
   measurable prediction, especially as a competiton you have to decide - you
   can't have ranges."
3. "Our forecast has ranges - our predicton is to the seat."
4. "We need to clearly capture in our terminogy and documentation that tehre are
   three things: 1. A Forecast- how often something happens over 5000 simulations
   of the event. It uses stripes and ranges and bands. 3. A Prediction: A single
   scenario we consider the most likely that only has specific numbers. solid map
   colors. single numbers. 3. A Result: what actually happens and can be matched
   exactly to a preiction. Our forecast heading is exacly that. Your forecast
   section is actually a forecast and then a prediction. We might be better off
   putting the forecast levers after our forecast and making the user section
   YOUR PREDICTION."
5. "We should also be able to share both our forecast and our prediction. The
   forecast is great as it shows battlegrounds and spreads. It's what people want
   to know before an election. The prediction is what we predict - it's our line
   in the sand vs. the result. Please also add this to user facing text on
   forecast and prediction pages. Our prediction should be on the prediction page
   and how we reduced it from forecast."

The terms are now defined in `STYLE.md` rule 11.

## Where things stand (facts to check, not conclusions)

- The live site: `site/forecast.html` (our forecast: seat table of per-party
  middles, which the page says do not add up; a "full council" bar from one
  simulation), `site/your-forecast/index.html` (two sections: "Adjust the model"
  levers, then "Break the model", where a reader calls every ward).
- "Our" current complete scenario is the `start` object in
  `site/your-forecast/forecast.json`, built by `src/build_make.py` `start_state`
  under the rule in `src/start_rule.py` (read its docstring). Ward calls come from
  `src/score_forecasts.py` `model_forecast`.
- Seat law for a complete scenario: `worker-api/seats-py/src/entry.py` `answer`
  (see `interactive/tools/share_fixture.py` for how to call it from Python), and
  `src/reader_seats.py`.
- Per-ward winner probabilities: `data/processed/ward_winner_probs.csv`. Per-party
  seat summaries incl. mean ward wins: `data/processed/forecast_summary.json`.
  Per-simulation seats for all parties: `data/processed/seat_detail_draws.csv`.
  The published draws: `site/draws/` (loader in `entry.py`).
- Share cards: `interactive/js/share-card.js`, `interactive/js/play-card.js`,
  `interactive/js/share-sheet.js`. Worker routes and redirects: `src/worker.js`,
  `src/share-edge.js`.
- A mock-up of "our" card filled with the current `start`:
  `audits/2026-10-07-stamp-design/v4-our-call-link.png` and
  `v4-our-call-story.png`; the script that built its data:
  `audits/2026-10-07-stamp-design/model_call.py`.

## The proposed brief (owner-approved, on hold for this review)


1. **Levers move to `/forecast`, after our forecast.** "Adjust the model" becomes a
   section of `/forecast` headed as a forecast: stripes, ranges, chances, all
   recomputed from the reader's settings. The page engine loads when the reader
   reaches the section or touches a lever, so `/forecast` opens as fast as now.
   Its share is a link to the settings (a forecast is not sealed or scored), plus a
   button: **"Make this your prediction"**, which opens change 2 starting from
   the prediction those settings give.
2. **`/your-forecast/` becomes `/your-prediction/`, titled "Your prediction".** It
   holds what is now "Break the model": every ward called, a vote share per party,
   seats that add up to the council, sealed and scored. Opens on our prediction, or
   on the prediction from the settings sent by change 1.
3. **Old links keep working.** `/your-forecast/…` redirects to `/your-prediction/…`
   with its query and fragment, in the Worker's existing redirect table (where
   `/play/` and `/make/` already go). Sealed links already shared, and their link
   previews, resolve to the same entry.
4. **Our share card is our prediction.** Title "Our Johannesburg Prediction"
   (or the stamp, change 5); reader-card layout; numbers = our prediction. The
   ranges stay on `/forecast`. Readers' cards: "Simon's Prediction".
5. **Stamp wording.** The prediction card carries an OFFICIAL PREDICTION stamp,
   which the owner is supplying. The forecast card (change 8) carries OFFICIAL
   FORECAST.
6. **Words across the site.** Navigation, home page ("Make your own forecast"
   block), headings, buttons, share-sheet text, card text, leaderboard, edit-mode
   labels, `og:` tags: "forecast" where it is a forecast, "prediction" where it is
   one. A wording change, not an error: no correction entries.
7. **Methodology gets one short section**, "Forecast, prediction, result", in
   reader words (rule 11's table, rewritten in reader terms).

8. **Both of ours can be shared** (owner, 2026-10-08). Our forecast card, from
   `/forecast`: battlegrounds and spreads, stripes on contested wards, ranges and
   chances, what readers want to know before an election. Our prediction card,
   from `/your-prediction/`: single numbers, solid map, our line in the sand
   against the result.
9. **Each page says what it is, in reader words.** `/forecast` and
   `/your-prediction/` each carry a short passage: a forecast is how often each
   outcome happens across the simulations and is what to read before the
   election; a prediction is one complete result that could happen, what we
   commit to and what the result is measured against.
10. **Our prediction is on the prediction page, with how it was reduced from the
    forecast**: the rule that turns the forecast into one scenario (how each ward
    is called, where the vote shares come from, how the seats follow), stated in
    reader words beside our prediction's numbers, with every figure a token.

## Open decision that this brief depends on

**Our prediction's vote shares.** A prediction carries a vote share for every
party. Today's (from `src/start_rule.py`) are each party's seats divided by the
council, so on our card "% of votes" equals "% of seats" on every row. Either:

- **(a)** our prediction takes the model's middle vote share per party, and its
  seats follow from those votes and the ward calls under the seat law, exactly as
  a reader's do. Changes the start rule: **model/published-figure tier, the whole
  suite once**, and our predicted seats may move (not yet computed); or
- **(b)** keep the start rule and drop "% of votes" from our card only.


## Out of scope

- Renaming code identifiers (`score_forecasts`, `forecastSpec`, `ward_calls`,
  file names under `interactive/`); docstrings say which of the three they hold.
- Any change to the model or `/forecast`'s existing figures.
- Tshwane.

## Acceptance

- `/forecast`: our forecast unchanged above; levers section below recomputes
  stripes, ranges and chances; "Make this your prediction" lands on
  `/your-prediction/` with the matching start.
- `/your-prediction/` passes everything `/your-forecast/` passes now.
- Every sealed link in D1 resolves through the redirect to the same entry and the
  same preview image (checked against the live table).
- No reader-facing "forecast" names a single scenario; no "prediction" names a
  range (a scan, with a constructed violation it must catch).
- Our card and `/your-prediction/`'s opening state show the same numbers.

## Tier and estimate

Interactive behaviour (QC.md §4b step 3): page modules, interactive node tests by
file, `yf_jump_check`, Worker routing tests, screenshots. Plus the whole suite
once if (a). Roughly a day of work with review: changes 1–3 are most of it
(moving the engine between pages and the redirect); 4–7 are wording and the card.

## Questions

Answer each. Rank findings by how much they matter. Be concrete.

1. **The problem.** Does the brief solve what the owner asked for in the five
   quotes? Anything asked for and missing, or added and not asked for? Are the
   three definitions in `STYLE.md` rule 11 sound, and consistent with how the
   site, the cards and the competition scoring actually work today?
2. **The solution.** What breaks or gets harder: shared and sealed links already
   in the wild (D1 entries, link previews), scoring of entries, the page engine
   moving to `/forecast`, the hand-off between the two pages, tests that pin the
   current structure. What would you change in the brief?
3. **The vote-share decision ("Open decision").** Which vote shares should our
   prediction carry? Assess (a), (b) and any alternative you think better.
   Compute what (a) would give (seats per party, any excessive-seat overhang,
   whether it seats under the law) and say how it compares with (b), using the
   data above, in scratch only. Specifically: is "every ward called for its most
   likely winner" plus "each party's middle vote share" a result that could
   happen, and is it a defensible reading of "a single scenario we consider the
   most likely"? Compare each ward-calling rule's ward totals per party with the
   mean ward wins in the simulations.
4. **The reduction the prediction page must explain** (change 10). Is there a
   rule for reducing the forecast to one scenario that is honest, explainable in
   two or three sentences to a reader, and consistent with how readers' own
   predictions are made and scored? State it.

Return: your findings, each with evidence and verified/argued; then a short
answer to each question.
