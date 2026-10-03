# Decisions on the share design (DESIGN.md §7)

`DESIGN.md` and the mockups beside it are the approved design of 3 October
2026, copied here from the designer's scratch folder. These are the answers to
its open decisions, as built.

## The owner's (2026-10-03)

| §7 | decision |
|---|---|
| 5 | Headline in Title Case: "{Name}'s Election Forecast" (`share-card.js` `cardTitle`). |
| 4 | Boldness badge: Safe call at 20% or more, Bold call from 5% to under 20%, Wild call under 5%. A judgement call: JUDGEMENT-CALLS.md §N6. |
| 3 | Results-night scoring in the competition's order: seats per party, then wards, then vote per party (JUDGEMENT-CALLS.md §N4). |
| 2, 12 | Sealed links. The site's Worker signs a link's state and a server timestamp with HMAC-SHA256 under the Worker secret `SEAL_KEY`. A sealed link shows "Sealed <date time SAST>"; a tampered or unsigned one shows "Not sealed". The Worker refuses to seal from the moment polls open (`content/joburg/election.toml` `polls_open`, on `cities/joburg.toml`'s polling day). Only links sealed before polls open are eligible for any ranking. Nothing about the person is stored. The seal replaces the design's `d=` date parameter. |

## The lead's defaults

| §7 | decision |
|---|---|
| 6 | Edge cache only; no R2. |
| 7 | The friend's name is shown on a return card, with "Leave their name off". |
| 8 | No short links now. |
| 9 | "new" for any party not on the 2021 Johannesburg ballot, SACP and Rise Mzansi included. |
| 11 | The link card keeps a small "A reader's forecast, not the model's" line at its foot. |
| 1 | Not decided here: links are shared anonymously, as `/your-forecast/` already did. |
| 10 | Not decided here: a successor party shows "new", as §9. |
