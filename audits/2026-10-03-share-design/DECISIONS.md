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
| 2, 12 | Sealed links. The site's Worker signs a link's state and a server timestamp with HMAC-SHA256 under the Worker secret `SEAL_KEY`. A sealed link shows "Sealed <date time SAST>"; a tampered or unsigned one shows "Not sealed". The Worker refuses to seal from the moment polls open (`content/joburg/election.toml` `polls_open`, on `cities/joburg.toml`'s polling day). Only links sealed before polls open are eligible for any ranking. Nothing about the person is stored. The seal replaces the design's `d=` date parameter. Limit, below. |

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

## After the review of the build (2026-10-03)

| item | as built |
|---|---|
| 2, 12 | A seal shows when a forecast was made, not that it was its maker's only one: `/seal/1` is anonymous and stores nothing, so anyone can seal any number of variants before polls open. The cards, the arrival view and `privacy.md` therefore promise no scoring or ranking: the story card's foot reads "Bring this link back after the count to compare it with the result."; the return card's "Compare both with the result after the count." A ranking of shared forecasts would need one stored entry per person before polls open, which "nothing stored" rules out. **Open, owner.** |
| 2, 12 | Preview versions (`*.workers.dev`) refuse `/seal/1` (403) and still answer `/seal/1/check`: they share the live `SEAL_KEY`, and a preview built with a later `polls_open` would sign links the live site accepts. |
| 2, 12 | `/seal/1/check` checks the signature on the fields as the link carries them, before reading the forecast, and adds `readable`: a link sealed under an earlier `context_ref` still checks as sealed. The page cannot open such a link; keeping old contexts so it can is not built. |
| 6 | An image is kept at the edge a year when its link's seal checks, an hour otherwise (`share-edge.js` `imageCache`). |
| 7 | The return card's date line names whose seal it is ("{Name}'s forecast sealed …"). The friend's seal is not carried: it signs the friend's name, which "Leave their name off" removes from the link. |
