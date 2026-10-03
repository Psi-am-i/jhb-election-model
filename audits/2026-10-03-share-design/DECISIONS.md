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
| 2, 12 | A seal shows when a forecast was made, not that it was its maker's only one: `/seal/1` is anonymous and stores nothing, so anyone can seal any number of variants before polls open. The cards, the arrival view and `privacy.md` therefore promise no scoring or ranking: the story card's foot reads "Bring this link back after the count to compare it with the result."; the return card's "Compare both with the result after the count." A ranking of shared forecasts would need one stored entry per person before polls open, which "nothing stored" rules out. **Decided by the owner, below.** |
| 2, 12 | Preview versions (`*.workers.dev`) refuse `/seal/1` (403) and still answer `/seal/1/check`: they share the live `SEAL_KEY`, and a preview built with a later `polls_open` would sign links the live site accepts. |
| 2, 12 | `/seal/1/check` checks the signature on the fields as the link carries them, before reading the forecast, and adds `readable`: a link sealed under an earlier `context_ref` still checks as sealed. The page cannot open such a link; keeping old contexts so it can is not built. |
| 6 | An image is kept at the edge a year when its link's seal checks, an hour otherwise (`share-edge.js` `imageCache`). |
| 7 | The return card's date line names whose seal it is ("{Name}'s forecast sealed …"). The friend's seal is not carried: it signs the friend's name, which "Leave their name off" removes from the link. |

## Entries and the ranking (owner, 2026-10-03)

| item | as built |
|---|---|
| 2, 12 | Every sealed forecast is ranked, each seal one entry, even when one person seals several. Each successful seal is stored at sealing in the D1 database `joburg-entries` (binding `ENTRIES`, `migrations/0001_entries.sql`): the forecast, the name typed, the seal time and id, the model version. No IP address, user agent, cookie or account. A failed insert is logged by reason and the reader keeps the seal (`share-edge.js` `storeEntry`). |
| 2, 12 | The share sheet seals a name 1.5 s after typing pauses, or when the field is left, not 0.5 s after each pause (`make-share.js` `NAME_PAUSE_MS`): each seal is an entry, and a half-typed name would be one. Opening the sheet still seals; a reader who opens it, then names the forecast, makes two entries of one forecast, one anonymous. |
| 2, 12 | `/seal/1` is rate-limited per connection by the Workers Rate Limiting binding `SEAL_LIMIT`, thirty a minute, keyed by an HMAC of the address (JUDGEMENT-CALLS.md §N9). |
| 2, 12 | Before the results, `/your-forecast/` and the arrival view show only "N forecasts sealed so far" (`GET /entries/1/count`, kept at the edge a minute; `interactive/js/entries.js`). No name or forecast is listed. |
| 3 | Results night: `src/rank_entries.py` scores every entry by `score_forecasts` against the result and writes `content/joburg/leaderboard.json`; `/leaderboard/` is built once `content/joburg/leaderboard.toml` says `published = true`, and only then is it in the nav. Ties: the earlier seal, then the seal id (JUDGEMENT-CALLS.md §N7). |
| 2, 12 | Entries are deleted ninety days after the leaderboard is published (JUDGEMENT-CALLS.md §N8); one is deleted sooner on request by its seal id (`docs-public/privacy.md`). |
| 2, 12 | Until the owner creates `joburg-entries` and uncomments the binding in `wrangler.toml`, no seal is stored and every seal logs one `console.error` line with the reason only. A forecast sealed in that gap is not an entry. |

## After the review of the entries (2026-10-03)

| item | as built |
|---|---|
| 1 | Every entry is ranked and listed on `/leaderboard/`; the `top` setting is gone (owner: "we can rank all entries"). `leaderboard.json` is served whole by design. |
| 1 | The board's data is gitignored, as `content/<city>/leaderboard.json` and `site/leaderboard/leaderboard.json`, and `deploy_check.SHIPPED_UNCOMMITTED` lets the built copy ship: a name removed from the board is not kept in the public repository's history. `rank_entries.py --drop <seal id>` removes one entry from the published board; `--anonymise` replaces every name at the ninety-day deletion, when the export `~/joburg-entries.json` is also deleted (JUDGEMENT-CALLS.md §N8). |
| 2 | The rate limit counts an IPv6 connection by its /64 (`seal.js` `rateAddress`); IPv4 by the whole address. |
| 3 | Opening the share sheet still seals, and so enters the forecast (the owner's rule: each seal is one entry). The sheet and `privacy.md` say so. Moving the seal to the share action is not done. |
| 4 | Not limited further: one connection can make thirty entries a minute, and the binding allows no daily period. The leaderboard says one person may hold several places. A daily cap would need a counter in D1 or a Durable Object; not built. |
| 5, 6 | `privacy.md` and §N8 state D1 Time Travel's recovery copy (up to thirty days) and a backstop: entries are deleted within six months of polling day if no leaderboard is published. |
| 7, 8 | A failing limiter lets the seal through and logs the reason; the entry's row is built inside `storeEntry`'s guard, so a row that cannot be built fails the entry, not the seal. |
| 9 | The vote error is rounded once, to `rank_entries.VOTE_DP` decimals, before ranking; the page prints that value at `vote_dp` from the artefact. |
| 12 | `id_chars` and `vote_dp` are written into `leaderboard.json`; `leaderboard.js` reads them and types neither. |
| 13 | `docs/DEPLOY-UAT.md` "Entries at launch": empty `entries` before the site is announced. |
