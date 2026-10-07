# Brief: forecast, prediction, result (owner, 2026-10-07; revised 2026-10-08)

Terms as defined in `STYLE.md` rule 11. Revision 2, after the blind review
(`review/SYNTHESIS.md`) and the backtest (`MODEL-LOG.md` §1.290). Revision 1 was
approved on hold; it is in git history. **This revision needs the owner's
approval before anything is built.**

Owner decisions, 2026-10-08:
- **Rule A** reduces our forecast to our prediction.
- **Our prediction is sealed and scored** like a reader's.
- **A prediction carries the four things an election produces:** ward votes,
  ward seats, list votes and the final seat count.
- **Excessive seats follow the law.** Schedule 1, the "deduct" reading,
  `tests/test_overhang.py` pinned to Laingsburg 2021.

## Phase 1: our prediction (model/pipeline tier, whole suite once)

1. **Rule A, one definition.** For each ward, the party that wins it in the most
   simulations. For each party, its mean ward-ballot vote and its mean list-ballot
   vote across simulations. Seats from those wards and votes by the seat law
   (`eligible_parties`, `outside_pool_wards`, `allocate_with_overhang`). It lives
   in one function. These all point at it and stop defining their own:
   - `score_forecasts.model_forecast` (its docstring today says median combined
     shares);
   - `build_make.start_state`;
   - the page's hand-off (weighted by the reader's lever settings).

   `start_rule.py`'s seat-first rule is retired. Recorded in:
   - `JUDGEMENT-CALLS.md`, as a new entry: the rule is a choice, with
     §1.290 as evidence;
   - `MACHINERY.md`;
   - the docstrings.
2. **Each simulation's ward-ballot and list-ballot votes are published** in
   `site/draws/`. Today only the list share is, and `COMBINED_SHARE_REFUSAL`
   states why the combined vote is not.
   - Rule A needs both ballots, on the build and in the page's hand-off.
   - No published seat figure moves: the captured tallies reproduce all 5,000
     draws (review A, re-derived).
   - The draws' fingerprint changes. Link previews re-render once; seals do not
     depend on the draws.
3. **Our prediction is sealed.** Every published version is sealed and dated.
   The one scored is the last sealed before the lock (07:00 SAST, 4 November),
   by the same `score()` as readers, in the same ranking, labelled as ours.
4. **The "typical simulation" bar and strip leave `/forecast`.** They are
   simulation 1622: one draw, which gives BOSA 16 seats against a middle of 1.
   They are replaced by a short pointer to our prediction.
5. **Rule 11 names the ballots.** "% of votes" on a card or page says which
   ballot it is. Entries are scored on the list ballot (`score_forecasts` key 3),
   so the column a reader is scored on says "list vote".

## Phase 2: the pages (interactive tier)

6. **The levers move to `/forecast`, after our forecast,** as a forecast section:
   stripes, ranges, chances, recomputed from the reader's settings.
   - The page engine loads when the reader reaches the section.
   - It stays on `/your-prediction/` too, because the hand-off needs it.
   - Moving a lever now makes a forecast. A forecast is shared as a link to its
     settings, not sealed. **This reverses the owner's 6 October rule** that
     moving a lever seals a named reader card.
7. **"Make this your prediction"** carries the rule-A prediction for those
   settings (the encoded state `f`) plus the lever keys to `/your-prediction/`.
   It is a one-shot hand-off: today's live following of section 1 by section 2
   ends.
8. **`/your-forecast/` becomes `/your-prediction/`, titled "Your prediction".**
   - It holds "Break the model": every ward called, seats adding to the council,
     sealed and scored.
   - It opens on our prediction, or on the one handed off by change 7.
   - Our prediction is shown there with how it was reduced from the forecast:
     rule A in two or three reader sentences, every figure a token.
9. **Old links route by what they carry.** In `src/worker.js` and
   `src/share-edge.js`:
   - a `/your-forecast/` link with a prediction (`f`) goes to
     `/your-prediction/`;
   - a link with lever keys only goes to `/forecast#adjust`;
   - `/play/` goes straight to `/forecast`, and `/make/` to `/your-prediction/`.

   Also re-pointed: `share-edge.js` `PAGE`, `og:url`, the asset paths,
   `rank_entries`' forecast path, the `stats.LIVE_WRITERS` keys, and the tests
   that pin the path.
10. **Each page says what it is.**
    - `/forecast`: how often each outcome happens across the simulations; what to
      read before the election.
    - `/your-prediction/`: one complete result that could happen; what we commit
      to and what the result is measured against.

## Phase 3: cards and words (cosmetic tier)

11. **Two cards of ours.**
    - **Our forecast card**, from `/forecast`, a redesign of today's model card:
      contested wards striped, ranges and chances per party, OFFICIAL FORECAST
      stamp.
    - **Our prediction card**, from `/your-prediction/`: the reader-card layout
      (% of seats, list vote, seats, change since 2021, chamber, solid map),
      OFFICIAL PREDICTION stamp (owner supplying).
    - Readers' cards: "<Name>'s Prediction" with their stamp.
    - Stamps large enough to read at phone width; overlap allowed if legible.
12. **Words across the site** follow rule 11: nav, home block, headings, buttons,
    share sheets, cards, leaderboard, edit mode, `og:` tags. A wording change,
    not an error, so no correction entries. Methodology gets a short "Forecast,
    prediction, result" section.

## Decision needed before Phase 1 is built

**D1. Readers' predictions and the two ballots.**
- Today a reader's entry holds one vote share per party, used for both ballots.
  Our prediction will hold two.
- Either:
  - **(i)** readers' entries also hold a ward vote and a list vote: a new entry
    version, two vote rows in the editor, and old entries stay valid with one
    share used for both; or
  - **(ii)** readers keep one share. Their editor opens our prediction with its
    list vote, and our card shows both ballots while theirs shows one.
- (i) meets the four-quantities principle for everyone. (ii) is smaller. Whichever
  is chosen, the competition's scoring keys (`JUDGEMENT-CALLS.md` §N4) do not
  change unless the owner says so.

## Out of scope

- Renaming code identifiers (`score_forecasts`, `forecastSpec`, `ward_calls`,
  `interactive/` file names); docstrings say which of the three they hold.
- Any change to the forecast itself: the draws' seats and shares, `/forecast`'s
  ranges and chances.
- Tshwane.

## Acceptance

- Our prediction:
  - is rule A, from one function;
  - is identical on the build, on `/your-prediction/`'s opening state, on our
    card and in the sealed entry (one comparison, all four);
  - re-seats exactly under `reader_seats`.
- Rule A run on the backtest panel reproduces §1.290's table.
- Every sealed entry in D1 resolves through the redirect to the same entry, the
  same seats and the same chance. Previews may re-render.
- No reader-facing "forecast" names a single scenario and no "prediction" names a
  range. Checked by a scan, with a constructed violation it must catch.
- `/forecast` carries no single simulation.

## Tier and estimate

- Phase 1: model/pipeline. Whole suite once, before promote.
- Phase 2: interactive (QC.md §4b step 3) plus Worker routing tests.
- Phase 3: cosmetic.

Each phase is reviewed as a diff before it runs, and goes to UAT separately.
Phase 1 about a day; Phase 2 two days; Phase 3 a day. Add a day if D1 is (i).
