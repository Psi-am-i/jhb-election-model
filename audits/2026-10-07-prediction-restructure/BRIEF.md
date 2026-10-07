# Brief: forecast, prediction, result (owner, 2026-10-07)

Terms as defined in `STYLE.md` rule 11. For owner approval before anything is built
(QC.md §4b).

## Changes

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
5. **Stamp wording.** The owner's stamp reads OFFICIAL FORECAST. Under rule 11
   the card shows a prediction. **Owner decides:** keep it as the brand mark, or
   supply an OFFICIAL PREDICTION version.
6. **Words across the site.** Navigation, home page ("Make your own forecast"
   block), headings, buttons, share-sheet text, card text, leaderboard, edit-mode
   labels, `og:` tags: "forecast" where it is a forecast, "prediction" where it is
   one. A wording change, not an error: no correction entries.
7. **Methodology gets one short section**, "Forecast, prediction, result", in
   reader words (rule 11's table, rewritten in reader terms).

## Open decision that this brief depends on

**Our prediction's vote shares.** A prediction carries a vote share for every
party. Today's (from `src/start_rule.py`) are each party's seats divided by the
council, so on our card "% of votes" equals "% of seats" on every row. Either:

- **(a)** our prediction takes the model's middle vote share per party, and its
  seats follow from those votes and the ward calls under the seat law, exactly as
  a reader's do. Changes the start rule: **model/published-figure tier, the whole
  suite once**, and our predicted seats may move (not yet computed); or
- **(b)** keep the start rule and drop "% of votes" from our card only.

Recommended: (a). A prediction with invented vote shares is not one that could
happen in the sense rule 11 requires.

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
