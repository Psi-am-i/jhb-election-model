# Sharing a reader's forecast: card, link preview, arrival, return

Design for joburg.whysoserious.city, 3 October 2026. Covers section 2 of
`/your-forecast/` ("Break the model"): the reader's own forecast. Section 1's
card (a reader's settings on the model) keeps its own rule, critic G1: no
reader's name over the model's figures.

Mockups in this folder, all drawn by `render.mjs` from `data.json`, which
`make_data.py` writes from repository files and the project's own code:

| file | what |
|---|---|
| `card-1200x630.png` | link preview, forecast A ("Thandi") |
| `card-1200x630-B.png` | link preview, forecast B ("@kgomotso_m"): a longer label, a three-party coalition |
| `card-1080x1920.png` | story card, forecast A |
| `duel-1200x630.png` | the two forecasts on one card |
| `arrival-375.png`, `arrival-1440.png` | the page a shared link opens, forecast A |

The mockups are HTML rendered by headless Chromium with the self-hosted IBM
Plex files (`.claude/worktrees/followup/src/fonts/`). Paths under
`.claude/worktrees/followup/` reach `main` when that branch merges. Production keeps one SVG
card builder (`interactive/js/forecast-card.js`); the mockups show layout and
content, not that builder's output.

## 1. Where the mockup figures come from

No seat count, share or chance in the mockups was typed.

| figure | source |
|---|---|
| the start both forecasts are derived from | `site/your-forecast/forecast.json` `start` (the published start of section 2) |
| seats, wards, PR seats, council size, majority, excessive seats | `src/reader_seats.reader_seats`, the seat law, on each forecast's ward calls and combined shares |
| "We give this outcome a N% chance" | `interactive/pyboot/page.py` `analyse()` (followup worktree, commit bd7842f), which calls `reweight.council_outcome` on the published draws `site/draws/base.bin` (5,000 draws, identical bytes in the main checkout and the followup worktree) |
| 2021 seats | `data/processed/history.json`, Johannesburg 2021 record, `seats[code][0]` (actual); sums to 270 |
| 2021 vote | `data/raw/elections/lge2021_JHB_vd_party_clean.csv`, PR and Ward ballots summed per party (1,846,189 valid votes), names mapped by `data/processed/party_crosswalk.csv`; every 2021 seat-holder maps to a current code |
| 2021 wards won | the same file, Ward ballot, plurality per ward: ANC 87, DA 43, IFP 2, PA 2, Al Jama-ah 1 (135 wards) |
| party colours, names, logo flags | `site/your-forecast/parties.json`; logos `site/logos/*.png` (12 parties) |
| ward shapes | `forecast.json` `geometry` |

**The two forecasts are made by rule, not by hand** (`make_data.py` `RULES`):

* **A**: the start's ward calls, except that each ward whose most likely
  winner has under 55% (`data/processed/ward_winner_probs.csv`) goes to its
  second most likely; the start's combined shares; coalition = parties in seat
  order until a majority. Result: ANC 72, DA 65, ActionSA 26, EFF 25, PA 23,
  MK 22; ANC + DA 137 seats; outcome chance 26%. The ANC wins 72 wards on
  25.9% of the vote, two more than its entitlement, so the excessive-seats
  clause fires: 72 ward seats, 0 PR.
* **B**: the same with a 70% cut; shares halfway between the start's and the
  2021 combined vote; coalition = seat order skipping the second-largest party.
  Result: ANC 81, DA 69, ActionSA 36, EFF 27; ANC + ActionSA + EFF 144 seats;
  outcome chance 17%.

**"New"** means the party was not on the 2021 Johannesburg ballot (zero 2021
votes in the file above). In A that is MK, SACP, All Citizens Party, BOSA,
Rise Mzansi, Dudula and four smaller parties. SACP existed in 2021 and did not
stand, so the card's word "new" is shorthand; the page's footnote should say
"not on the 2021 ballot".

## 2. The card

### What each size carries

The link preview is seen at about 350 px wide in a WhatsApp or X timeline,
29% of its drawn size. Text below 22 px on the 1200-wide card falls under
7 px there. So the link card carries what reads at that size and leaves the
rest to the story card and the page.

| element | 1200×630 link | 1080×1920 story | arrival page |
|---|---|---|---|
| "[Name]'s election forecast" | yes, shrinks to fit | yes, shrinks to fit | yes |
| our logo (tower J, `.claude/worktrees/followup/src/brand/logo.svg`) | top right, 118 px tall | top left, 130 px | site header |
| largest party's colour | 10 px band across the top | 16 px band | swatch beside "shared with you" |
| largest party's logo | in its row, same size as every other logo | same | same |
| the council, 270 seats | yes: the main graphic | yes | yes |
| seats per party | top 6 + Others | top 6 + Others | top 9 + Others (7 on a phone) |
| seats vs 2021 | yes | yes | yes |
| wards won, PR seats | in the graphic (solid and tinted) | columns too | columns (PR column dropped on a phone) |
| vote % | no | yes | yes |
| vote vs 2021, points | no | yes | yes (not on a phone) |
| governing coalition and its seats | yes | yes | yes |
| ward map | no | yes, 340 px | yes |
| the outcome in words, "We give this outcome N% chance" | yes | yes | yes, in a box under the headline |
| boldness badge | yes | yes | yes |
| made date, days to the vote | yes | yes | days to the vote |
| excessive-seats note, when the clause fires | no | yes | footnote |
| make-yours URL | yes | yes | buttons |

Dropped from the link card, and why: the map (at 29% the 135 wards are a
smear of two colours, and the council graphic already shows who wins how many
wards); vote % and vote change (two more columns would push the type under
legible size); ward and PR counts as numbers (the graphic shows the split).

### The council graphic

270 squares, 27 columns of 10, filled column by column. Governing parties
first, in seat order, then the rest in seat order. Within a party, ward seats
solid and PR seats at 42% opacity. A stepped white line encloses the first 135
seats; a governing block that crosses it holds a majority. The line is placed
from the forecast's own `majority`, so a council that the law sizes
differently draws its line in the right place. This is the one bold element;
everything else on the card is type and rows.

Why not a hemicycle: it is every parliament chart, it wastes the bottom third
of a landscape card, and its majority mark is a tick on a curve that does not
survive 29% scale. The grid fills the space and the step is visible at 350 px.

### Neutrality (DESIGN-decided §8, STYLE 7)

* The colour band and the first row follow the forecast's largest party,
  whoever it is. No word on the card calls it the winner.
* Every party with a logo gets it at the same size; no party is enlarged.
* Rows are in the reader's seat order, ties by name (the page's rule).
* A tie for the most seats: the band splits into the tied parties' colours in
  equal widths, and the outcome line reads "A tie for the most seats".

### Words on the card

* Headline: "[Name]'s election forecast" (`cardTitle`, sentence case; the
  brief wrote Title Case, listed in §7).
* "The ANC is the largest party, no party has a majority, and the ANC and
  the DA govern." then "We give this outcome a 26% chance." The first line
  defines "this outcome" exactly as `council_outcome` reads it (largest
  party, majority alone or not, the coalition reaching a majority), so the
  chance cannot be read as the chance of the whole forecast.
* "Make yours at joburg.whysoserious.city" (link card), "Bring this link back
  after the count. It will be scored against the result." (story card).
* The mockup's link card has no "Not the model's forecast" line; the story
  card's foot keeps it. That line was added to the card after the 2 October
  review (`make-share.js` foot), so dropping it from the link card is a change
  to reviewed wording and is listed in §7.

### Long names

`NAME_MAX` is 24. The headline shrinks to fit 900 px (link) and 960 px
(story), floor 40 px, then truncates with an ellipsis. Forecast B's 11-letter
handle fits at 56 px.

## 3. Link previews rendered per link

Today every shared `/your-forecast/` link previews as `share.jpg`, because the
page is static and crawlers (WhatsApp, Facebook, X, LinkedIn, Slack, iMessage)
run no JavaScript.

### The route

The share link gains one field, `d=YYYYMMDD`, the date the page made the
link. Without it the edge cannot print "Made 3 October 2026" or the days to
the vote, because the crawler fetches the image later than the share. `d` is
not personal; it is also not proof of when the forecast was made (anyone can
type it), which is what sealed links (§5) are for.

```
crawler GET /your-forecast/?v=1&c=<ctx>&f=<payload>&n=<name>&d=<date>
  src/worker.js
    f absent or unparseable  -> static page unchanged (og:image = share.jpg)
    f present                -> HTMLRewriter on the static page:
        og:title       "<name>'s election forecast"
        og:description "<outcome words> We give this outcome N% chance."  (from the seat service, below)
        og:image       https://joburg.whysoserious.city/og/1/link.png?<same query, normalised>
        twitter:image  .../og/1/link.png?...
        og:url         the canonical link (normalised query)

GET /og/1/<link|story>.png?c=&f=&n=&d=
  forecasts Worker (worker-api, over the existing service binding)
    1. normalise: c, f, n, d only, in that order; n through play-state.cleanName
       and the blocklist (BACKEND §6); d a valid date not after today; refuse
       anything else with 400
    2. cache key = sha256(draws_sha256 | size | c | f | n | d)
       Cache API hit -> PNG
    3. make-state.decode(f) -> calls, votes, coalition   (the page's own decoder)
    4. SEATS service binding, POST /v1/card:
         reader_seats(...)            -> seats, ward, pr, council, majority, excessive
         reweight.council_outcome(...) on the published draws -> p, text
    5. buildForecastCardSVG(spec)     (the page's own builder, extended per §2)
       resvg-wasm + embedded IBM Plex TTF -> PNG
    6. Cache-Control: public, max-age=31536000, immutable; Cache API put
```

* **Seats and the chance come only from Python**, in `seats-py`, the Python
  Worker that already computes seats for saved forecasts
  (`worker-api/src/seats.js`). It gains one endpoint returning seats and the
  outcome chance. `council_outcome` stays the one definition; no JavaScript
  count. A forged `f` cannot put seats on our image that the law would not
  give, because the Worker never reads seats from the link.
* **The draws in the Python Worker**: `reweight.unpack` of `site/draws/base.bin`
  (3.2 MB, 5,000 draws), fetched once per isolate from the static assets and
  kept in a module global. Only the seat block and the council block are
  needed; a slimmer export (5,000 draws × the seat columns, one byte each) is
  an option if cold starts are slow.
* **Fonts**: resvg needs TTF/OTF, not the site's WOFF2. Bundle IBM Plex Sans
  SemiBold/Bold and Serif SemiBold TTF (OFL) in place of DejaVu in
  `worker-api/src/render.js`.
* **A person opening the link never waits on Python.** The rewritten HTML is
  cached under the same key as the image, and the share sheet warms both. On
  a cache miss for a browser (not a crawler user agent), `src/worker.js`
  serves the static page at once with only the name in the `og:` tags and
  fills the cache in the background (`ctx.waitUntil`).
* **The cache key includes `draws_sha256`**, so a re-published forecast
  re-renders the chance instead of serving the old one.
* **Nothing about the person is stored.** The image exists in Cloudflare's
  edge cache only, which evicts on its own. The name on it is text the reader
  put in a link they chose to share. Writing the PNGs to R2 would make every
  shared name durable server-side, so this design does not; listed in §7.
* **Fallback**: any failure (seat service down, decode refusal, timeout over
  3 s) returns a 302 to `/share.jpg`, and the HTML keeps the generic tags. A
  preview never shows an error.
* **Crawler limits** (reported, not tested here): WhatsApp is said to drop
  large preview images and to fetch with a short timeout. The cards are flat colour and text; Chromium's PNGs of the
  mockups are 107-116 KB (1200×630) and 271 KB (1080×1920). A cold Python Worker is the slow step (below), so the
  share sheet warms the image: when the reader opens it, the page requests
  `/og/1/link.png?...` once, so the crawler that follows finds it cached at
  that edge.

### Cost on Workers Paid

Prices from developers.cloudflare.com/workers/platform/pricing, read
3 October 2026 (page dated 2 October 2026). Render CPU and Python cold start
are not measured; the CPU figure below is an assumption to be replaced by a
measurement from `wrangler dev`.

| item | price | at 100,000 shared forecasts and 1,000,000 preview fetches in a month |
|---|---|---|
| plan | $5.00/month, includes 10M requests and 30M CPU ms | $5.00 |
| requests | $0.30 per million over 10M | $0 (about 1.2M) |
| CPU | $0.02 per million CPU ms over 30M | $0 at an assumed 200 ms per render (20M ms) |
| KV short links (optional, §5) | 1M writes and 10M reads included; then $5.00 and $0.50 per million | $0 |
| Python Worker cold start | Cloudflare's own benchmark: 1,027 ms mean with memory snapshots (changelog 8 December 2025) | latency, not cost |

The bill stays at the $5 plan unless renders exceed roughly 150,000 a month
at 200 ms each.

## 4. What someone sees when they click a shared link

`arrival-375.png`, `arrival-1440.png`.

1. **The friend's forecast, read-only, at the top.** "A forecast shared with
   you, made 3 October 2026." Headline, then the outcome box: the outcome in
   words, "We give this outcome a 26% chance.", the badge, and one line saying
   the chance is ours and the seats are theirs.
2. **On a phone, one button straight after the box**: "Make your own,
   starting from Thandi's". The full forecast below it is a long scroll at
   375 px.
3. The council graphic, the map, the full table (seats, wards, PR, vote, both
   changes vs 2021).
4. **Three ways on**, in this order:
   * "Start from Thandi's": opens section 2 with the friend's forecast as the
     reader's start, edits allowed. Their label is not carried over.
   * "Start from our forecast": section 2 at the published start.
   * "See our forecast": `/forecast`.
5. Days to the vote, what happens after the count, and "Nothing stored".

The arrival is the same `/your-forecast/` page in a read-only state chosen by
a `from=1` flag the share link carries (a link the reader copies from their
own address bar stays editable). No new page or route.

### The return card ("Thandi and @kgomotso_m")

`duel-1200x630.png`. After someone who arrived from a link shares their own,
the share sheet offers a second image: both councils, both chances, and a
table of seats per party for each with the difference. The link carries both
forecasts: the reader's part as today, the friend's as `vs=<payload>&vn=<label>`.
Measured: forecast A's query is 261 characters (`f` 230), so a two-forecast
link is about 530 characters. X counts any link as 23; WhatsApp and SMS show
the full text but accept it.

The friend's label appears on the second person's card. The friend put it in
a link they shared; the second person chooses to re-share it. The share sheet
shows both labels before sharing and offers "Leave their name off", which
replaces it with "a friend".

## 5. Making people come back, with nothing stored about them

Ranked by value for effort. Value: does it bring a reader back or bring a new
one in. Effort: days of work for one agent, with tests.

| rank | idea | value | effort | how |
|---|---|---|---|---|
| 1 | Per-link preview image (§3) | high: the card is what friends see before they click | 3-4 days | §3 |
| 2 | "We give this outcome N% chance" and the boldness badge on the card | high: a reason to share and to argue | 1 day once §3 exists | the chance is already computed by `analyse()`; bands below |
| 3 | Score the link after the count | high: a reason to keep the link and open it once more | 2 days, after the result-ingest path exists | below |
| 4 | Return card (§4) | medium-high: each arrival can produce a second share | 2 days | `vs`/`vn` in `yf-url.js`, `duelCardSpec` in `make-share.js` |
| 5 | Arrival counting by channel | medium: tells the owner which share works | 0.5 day | below |
| 6 | Days to the vote on card and page | low-medium | 0.5 day | from `forecast.json` `election.date` and the made date |
| 7 | Sealed links | medium, only if anonymous forecasts are ranked | 2 days | below |
| 8 | Short links | low: long links work everywhere they are pasted | 1 day | below |

**Boldness bands.** A judgement call on the page's own chance, to be recorded
in JUDGEMENT-CALLS if adopted:

| badge | chance of the reader's outcome |
|---|---|
| Safe call | 20% or more |
| Bold call | 5% to under 20% |
| Wild call | under 5% |

For calibration, the chances `council_outcome` gives on the published draws
(each draw once, no coalition): ANC largest without a majority 46.7%, DA
largest without a majority 45.2%, EFF largest 2.9%, ActionSA largest 1.7%, MK
largest 1.4%, a tie for the most seats 1.4%, PA largest 0.5%, any party alone
with a majority 0.1% or less. With a coalition: ANC largest and ANC + DA
governing 25.5%; ANC largest and ANC + ActionSA + EFF 16.7%; DA largest and
DA + ActionSA + EFF 17.9%. So no outcome can be safer than about 47%, a
two-party government lands in "Safe" or "Bold", and a forecast where a third
party leads is "Wild". (`data.json` `calibration`.)

**Scoring after the count.** The link holds the whole forecast, so on and after
results night the page scores whatever link it opens against the declared
result, in the order DESIGN-decided §13 fixes: seat total error, then
ward-count error, then correct ward calls. The page shows the three numbers
and how the model's own forecast scored on the same three. A scored link
previews with its score on the card. This needs the result-ingest path and
the party-name mapping that DESIGN-decided §5 says do not exist yet, and the
scoring code frozen before 4 November.

**Arrival counting.** Share links go out as `https://joburg.whysoserious.city/s/?…`
with the same query; `src/worker.js` answers `/s/` with a 302 to
`/your-forecast/?…&from=1` and counts the hit (Workers Analytics Engine, one
data point: path `/s/`, the `ch` value if present, nothing else). `ch` is set
by the share button used (`wa`, `x`, `copy`, `native`), so the owner sees which
channel brings people back. No IP, cookie or forecast is recorded.

**Sealed links.** A link-only forecast carries no proof of when it was made,
so anyone could make one after the result. To rank anonymous forecasts at all,
the share button asks the Worker to sign `sha256(c|f) | time` with a key held
as a Worker secret, and the link carries `s=<signature>`. On results night a
link whose signature predates 07:00 on 4 November is eligible; one without is
scored but unranked. Nothing about the reader is stored; the Worker keeps no
record of what it signed. Without this, the scoring in rank 3 is a reader
checking themselves, not a competition.

**Short links.** `/s/<8 chars>` → KV `{query}`, written on share, no person,
no IP, expiring 30 June 2027 (the retention date proposed in BACKEND §8).
Short links make the stored state the forecast itself, which the link-only
design avoids; long links work. Recommended only if analytics show long links
being cut.

## 6. Code changes and tests

| change | file | tests |
|---|---|---|
| card spec: council graphic, coalition-first order, majority step, change vs 2021, outcome words, chance, badge, band in the largest party's colour, tie case, headline fit | `interactive/js/forecast-card.js` (`drawCouncil`), `make-share.js` (`cardOf`) | majority step encloses exactly `majority − 1` cells for councils of 269, 270, 272; tie renders split band and no "largest" words; `NAME_MAX` label fits at 40 px or is ellipsised; no party name or colour appears in the module (§8) |
| 2021 baselines into `forecast.json`: seats, wards, combined vote per roster code, `null` for not on the ballot | `src/build_make.py` from `history.json` and the 2021 VD file | sums: seats 270, wards 135, votes = 1,846,189; every 2021 party maps to a crosswalk canonical code. Two 2021 seat-holders are not on the 2026 roster (GOOD, UIM: checked against `x-seat-context.parties`); their rows appear on no card |
| outcome chance on the page's card | `make.js` passes `analyse().outcome` to `setShareable` | card text equals the page's analysis text |
| `/v1/card` in the seat service | `worker-api/seats-py/src/entry.py`, `worker-api/src/seats.js` | Pyodide answer = CPython `reader_seats` + `council_outcome` on the published draws (the existing native-vs-Pyodide harness) |
| `/og/1/*.png` route, HTMLRewriter for `og:` tags, 302 fallback | `src/worker.js`, `worker-api/src/render.js` | bad `f` → generic tags; unknown `c` → generic; seats in the query ignored; name with bidi/control characters cleaned; cache key changes with `draws_sha256`; `deploy_check` still passes |
| Plex TTFs for resvg | `worker-api/` assets | rendered PNG width of a known string within 2 px of Chromium's |
| read-only arrival (`from=1`), "Start from Thandi's", phone CTA | `your-forecast.html`, `make.js`, `yf-url.js` | `from=1` disables edits until a start is chosen; the friend's label is not carried |
| return card, `vs`/`vn` | `yf-url.js`, `make-share.js` | round-trip of both payloads; "Leave their name off" |
| `/s/` redirect and counting | `src/worker.js` | 302 keeps the query; only `ch` and path are written |
| boldness bands | one constant beside `reweight.chance_text` | band edges at exactly 5% and 20% |

## 7. Open decisions for the owner

1. **Sharing without sign-in.** DESIGN-decided §9 says sign-in is needed to
   save and share. This design shares anonymously from the link, as
   `/your-forecast/` already does. Which governs the competition?
2. **Ranking anonymous links.** Without sealed links (§5) a link can be made
   after the result. Rank only signed-in saved forecasts, add sealed links, or
   score links for the reader's own interest and rank nothing anonymous?
3. **Competition order.** The brief says seats per party, then ward calls, then
   vote per party. DESIGN-decided §13 says seat total error, then ward-count
   error, then correct ward calls, with no vote key. Which is current?
4. **Boldness bands**: 20% and 5%, and the words Safe, Bold, Wild.
5. **Headline case**: "Thandi's election forecast" (the page's `cardTitle`) or
   "Thandi's Election Forecast" (the brief).
6. **R2 or edge cache only** for rendered cards. R2 makes previews durable and
   cheaper to re-serve; it also keeps every shared name on our storage.
7. **The friend's label on a return card**: shown by default with "Leave their
   name off", or off by default.
8. **Short links** (KV, expiring 30 June 2027): build now or only if needed.
9. **"New"** on the card for a party not on the 2021 ballot, including SACP,
   which existed but did not stand.
10. **Mergers in "vs 2021".** Rise Mzansi shows "new", but GOOD (1 seat in
    2021, not on the 2026 roster) merged into it, and DESIGN-decided §10 treats
    GOOD-RISE as a merger at 75% retention. Does a successor show its
    predecessor's 2021 figures, or "new"?
11. **"Not the model's forecast" on the link card.** The reviewed card carries
    it in its foot; this design drops it from the 1200×630 card because the
    headline names whose forecast it is. Keep or drop?
12. **`d` in the link**, so an edge-rendered card can print its date and the
    days to the vote.

## Ideas considered and dropped

| idea | why dropped |
|---|---|
| Hemicycle for the council | wastes a third of a landscape card; the majority mark does not survive 29% scale (§2) |
| Map on the link card | at 350 px the 135 wards read as two colour fields; the council graphic carries the ward count |
| The largest party's logo enlarged beside the headline | singles out a party (§8); the colour band already follows the forecast |
| A JavaScript count of `council_outcome` at the edge | a second definition of the chance; the Python seat service already runs at the edge |
| Seats read from the link for the image | a forged link would put any seat count on an image from our domain |
| Rendering the preview in a headless browser at the edge (Browser Rendering) | seconds per render and a per-browser-hour price, for an image resvg draws in one call |
| Leaderboard of anonymous links | needs the links stored, which the link-only design exists to avoid |
| "Chance of your whole forecast" | about zero for any full set of 135 calls, the model's own included (`ward_calls_likelihood` docstring); the council-level outcome is the figure that means something |
