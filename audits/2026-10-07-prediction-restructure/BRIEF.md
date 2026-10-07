# Brief: forecast, prediction, result (owner, 2026-10-07; revised 2026-10-08)

Terms as defined in `STYLE.md` rule 11. Revision 3, after the blind review
(`review/SYNTHESIS.md`), the backtest (`MODEL-LOG.md` §1.290) and the owner's
answers of 2026-10-08. Earlier revisions are in git history. Under guard and
provenance review (`FLOW.md`) before it is built.

Owner decisions, 2026-10-08:
- **Rule A** reduces our forecast to our prediction.
- **Our prediction is sealed and scored** like a reader's.
- **A prediction carries the four things an election produces:** ward votes,
  ward seats, list votes and the final seat count.
- **Excessive seats follow the law.** Schedule 1, the "deduct" reading,
  `tests/test_overhang.py` pinned to Laingsburg 2021.
- **Emulate the real election, for us and for readers:** ward votes, list
  votes, ward wins, and list seats allocated by the law (D1 resolved as (i)).
- **No backward compatibility.** Nothing has been advertised, so existing
  sealed entries may be invalidated. Whatever this changes in the forecast or
  its artefacts is recorded as what was, what is now, and the decision
  (`MODEL-LOG.md`, `JUDGEMENT-CALLS.md`), not avoided.

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
   - The draws' fingerprint changes and the change is recorded.
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

## Readers' predictions carry both ballots (D1 = (i), owner 2026-10-08)

13. **A reader's entry holds what an election produces:** a winner for every ward,
    a ward-ballot vote share and a list-ballot vote share for every party, and the
    seats the law allocates from them (ward seats from the ward winners, list
    seats from the combined vote, excessive seats kept).
    - A new entry version, with the editor showing two vote rows.
    - The seat service, the validator, the stored schema, `score_forecasts` and
      the cards all read the new version. The old one is retired, not supported.
    - Existing D1 entries are exported to a file in the repository and then
      cleared, **at a step the owner approves when it is reached**.
    - The competition's scoring keys (`JUDGEMENT-CALLS.md` §N4) do not change
      unless the owner says so; key 3 already compares the list vote with the
      list ballot.
    - **Open for review:** in a real election the ward votes decide the ward
      winners. A reader sets both, so they can disagree (130 wards to a party on
      5% of the ward vote). The review says whether to refuse, warn or allow.

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
Phase 1 about two days with change 13; Phase 2 two days; Phase 3 a day. The
flow that builds it, and when the whole suite runs, is `FLOW.md`.
