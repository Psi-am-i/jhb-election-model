# Readers' forecasts: prototype

"Make your own forecast", "play with the model", sign-in to save, the share
sheet and share image, and the shared forecast page, for
joburg.whysoserious.city. **A prototype**: every figure is synthetic, seats come
from a stand-in that is not the seat law, and sign-in and saving are stubs that
never leave the browser. Nothing under `site/` or `src/` is touched or read at
run time.

The backend is specified, not built: `BACKEND.md`.

## Open it

```
cd ~/projects/jhb-election-model
python3 -m http.server 8801 --bind 127.0.0.1      # port 8801, never 8765
```

| page | URL |
|---|---|
| Make your own forecast | http://127.0.0.1:8801/interactive/make.html |
| Play with the model | http://127.0.0.1:8801/interactive/model.html |
| A shared forecast (demo) | http://127.0.0.1:8801/interactive/f/?id=demo7Qx2Lp |
| Privacy notice placeholder | http://127.0.0.1:8801/interactive/privacy-placeholder.html |

Serve the repository root, not `interactive/`: the nav links point at the live
pages in `../site/`. The pages are ES modules, so `file://` does not work.
Screenshots at 375 px and 1440 px are in `screenshots/`.

To rebuild the fixtures: `python3 interactive/tools/make_fixtures.py`.

## Files

| path | what |
|---|---|
| `make.html`, `js/make.js` | the builder: map, vote shares, coalition, results, save and share |
| `model.html`, `js/model.js` | play with the model, against synthetic draws |
| `f/index.html`, `js/f.js` | the shared forecast page, `/f/<id>` in production |
| `js/map.js` | the ward map (geographic and equal-sized), painting, keyboard |
| `js/card.js` | the share image, SVG to PNG, 1200×630 and 1080×1920 |
| `js/share.js` | the share sheet |
| `js/auth-ui.js` | sign-in and the consent screen, rendered from `js/consent-terms.js` |
| `js/consent-terms.js` | the consent wording, its keys and its version hash: one definition, imported by the page and `worker-api` |
| `js/labels.js` | the default-label word list and generator: one definition, imported by the page stub and `worker-api` |
| `js/api-stub.js` | **stub** of the API in BACKEND.md, in localStorage |
| `js/allocator-stub.js` | **stub** seat allocator, deliberately not the law |
| `js/common.js` | fixture loading, escaping, theme toggle |
| `css/interactive.css` | styles; a copy of the site palette |
| `fixtures/` | **placeholders**, below |
| `tools/make_fixtures.py` | writes `fixtures/` |

## What is stubbed, and what replaces it

| stub | stands in for | the real thing |
|---|---|---|
| `fixtures/placeholder-model.json` | the model's roster, most likely ward winners, combined vote shares, the combined total they scale to, and published seats | the S2 export (`site/draws/base.bin` + manifest, PLAN.md) and the certified roster in IEC ballot order |
| `fixtures/placeholder-draws.json` | per-draw pool turnouts, list shares and seats for each grid cell and seat law | S2 and S3 of PLAN.md |
| `js/model.js` re-weighting | `src/reweight.py` (PLAN S4), run under Pyodide | delete the JavaScript; one definition in Python |
| `js/allocator-stub.js` | `seats.allocate` | the model's own function under Pyodide; see "Integration" |
| `js/api-stub.js`, `js/auth-ui.js` provider buttons | the Worker API and OAuth | `worker-api/` |
| `fixtures/geometry.json` sectors | the S5 ward-to-sector file | S5 |
| `privacy-placeholder.html` | DRAFT privacy notice (placeholders for the owner's decisions), competition rules, report route | the owner's decisions filled in, checked by counsel |

**The fixtures are synthetic on purpose.** A seeded random generator made them;
none is derived from `ward_draws.csv`, `seat_draws.csv` or any model artefact,
because the model is about to be re-emitted and a real-looking number in a
prototype is a model number in a page. Every page and every share image carries
a "prototype, placeholder data" line.

**Copies to remove at integration** (each is a second definition):

* the site palette in `css/interactive.css` and the theme script in each page's
  `<head>`: production injects `build_site.THEME_HEAD` and `nav_for`;
* party colours and names in `tools/make_fixtures.py`, a third copy after
  `render_sheet.CHIPS` and `render_map.py`. Emit them once, with the roster;
* the ward geometry in `fixtures/geometry.json`, copied from
  `data/processed/ward_paths.json` and `ward_hex_layout.json` (sha256 of each
  source recorded in the file).

**The compass sectors do not reproduce DESIGN-decided §1's table.** Derived by
its stated method (central = nearest fifth of ward centroids, the rest by
bearing), the prototype gets a different split of the non-central wards; four
variants of "centroid" tried, none matched. The original derivation was not
committed. S5 should commit its code and be the one source.

## Integration: what the real pages need

1. **How a reader's forecast becomes seats: `src/reader_seats.py`.** The
   reader edits each party's COMBINED vote share, ward and list ballots
   together, which is what the statute counts (DESIGN-decided §10), plus the
   ward winners. `reader_seats(combined_shares, ward_winners, context,
   total_votes)` scales the shares to the start state's combined total and
   seats them by Schedule 1 and item 16 (JUDGEMENT-CALLS §M1). The page must
   run that file under Pyodide; the stub still shares 135 list seats on the
   shares alone, and is labelled as a stand-in on every screen.
2. **The engine**: `reweight.py` and `seats.py` under Pyodide, loaded behind the
   static first paint (PLAN §9). The untouched model page shows the published
   draws exactly; effective draws beside every result; refusal below the floor.
3. **The trust-slider mapping** from 0–100 to a poll error is a design decision.
   The stand-in maps 0 to "off" and otherwise 30 to 3 points; PLAN §5's table
   gives the effective draws each poll error leaves.
4. **Ward order and ids** in the forecast body must be the 2026 delimitation's
   135 wards in ward-number order, and the roster the IEC's certified list
   (CLAUDE.md §4b).
5. **Server-rendered `/f/<id>`** with Open Graph tags; the comment at the top of
   `f/index.html` lists them.

## Design decisions made here

* **A reader's work wears the interactive hue, the model's wears amber.** The
  site already gives the interactive `--k-interactive` on the home page. Here
  every reader-made thing (the map frame, the results rule, the "A reader's
  forecast" stamp, the share image's top rule and footer) is in that hue, and
  every control that copies the model's answer is an amber button. The shared
  page opens with a stamp and a boxed statement that it is not the model's
  forecast, and the share image says so in words.
* **No party is singled out (DESIGN-decided §8).** Parties are alphabetical
  everywhere a reader chooses (brush, vote shares, coalition), every party has
  the same control with the same range, and nothing is pre-selected: tapping a
  ward before choosing a party asks for a party rather than defaulting to one.
  Result lists sort by the reader's own seats.
* **The vote shares start at the model's; the map starts empty.** The
  map is the game, so it starts blank, with "start from the model's map" and
  "fill empty wards with the model's call" one tap away. The shares start
  where the model is, so a reader who only calls wards still gets a council.
  Each is a party's share of all votes, ward and list ballots together.
* **Saving needs all 135 wards, vote shares summing to 100, and a coalition.**
  Making does not need an account; saving and sharing do.
* **Three ways to call a ward**: tap or drag on the map (drag with mouse or pen
  only, so a finger can scroll), a whole compass sector at once, and a list of
  135 selects grouped by sector for keyboard and screen-reader users. The map
  is one tab stop; arrow keys move between neighbouring wards, Enter paints,
  Delete clears. Undo keeps the last 60 strokes.
* **On a phone** the map scrolls sideways at a size where a ward is tappable;
  the party chips ride along at the bottom of the map card; the model page
  keeps a one-line result bar at the bottom of the screen.
* **Share sheet**: the native share sheet first where it exists (with the PNG
  attached when `navigator.canShare({files})` allows, and the image rendered
  before the button enables so the call stays inside the tap), then copy link,
  download image, and plain links to X, Facebook, LinkedIn, WhatsApp and email.
  No network SDKs, no tracking pixels. Native `<dialog>` with `showModal()`
  (inert background, Escape closes, focus returns to the opener); a bottom
  sheet under 560 px.
* **Share image**: two sizes, 1200×630 for link previews and 1080×1920 for
  stories (content above y = 1720, clear of the reply bar). Site name, the
  reader's map, top five seat totals, the coalition with its seat total against
  the majority of the council as seated (both from the seat answer, never
  typed), the reader's name or "A reader", and "A reader's forecast, not the
  model's". Names are escaped. Text is laid out by measured width in the
  server's DejaVu faces: a long title drops to a smaller size, and a party
  name too long for its column shrinks, then is cut with an ellipsis, rather
  than run into its bar. The browser's PNG uses system fonts; the server's uses
  an embedded font (BACKEND.md §5).

## Legal

**Checked against the text of POPIA as I understand it, not by a lawyer. Have
counsel review the consent screen, the privacy notice and any competition rules
before sign-in goes live.**

| requirement | how the prototype meets it |
|---|---|
| What a saved forecast is | Owner, 2026-09-29: a PREDICTION of the outcome, treated as ordinary personal information, not s26 special personal information (the draft notice states this as the responsible party's view, **counsel to confirm**). Explicit consent is kept anyway: its own required, unticked box |
| Consent informed and specific | The screen's text (`js/consent-terms.js`) states the one post-election email sent whatever is ticked, that anyone with the link can see a prediction, the analysis against past elections, what happens without a confirmed email, and the copies that outlast a deletion. Its version is a hash of that text, checked by the server |
| Consent voluntary and specific | "Contact me if I win" and "send me updates" are separate, unticked and optional; saving works with both off |
| Electronic direct marketing needs opt-in, s69 | "Updates" is opt-in; every email carries an unsubscribe link (BACKEND §8) |
| Minimality, s10 | provider account id and one CONFIRMED email; no name, photo, contacts or location. An unconfirmed address gets one confirmation link and is stored only if it is used |
| No name on shared links | Owner, 2026-09-29: a shared forecast shows a label: the reader's own text, their X @username, or a random "pollster-23" style label chosen per forecast (`js/labels.js`) |
| Children, s34–35 | 18+ confirmed before saving |
| Transfer outside South Africa, s72 | placeholder on the consent screen and in the draft notice: the jurisdiction is the owner's decision (R5 finding 3) |
| Deletion, s24 | delete a forecast or everything, no email needed; deleted links answer 410; the copies that outlast it (D1 Time Travel, Workers Logs, browser caches) are listed in the draft notice |
| Competitions (Consumer Protection Act s36 and regulations) | rules page placeholder linked from the opt-in; rules must exist before any prize is offered |

**Declined or changed from the request, and why:**

* "Users will use a social or any OAuth to **create** a forecast": the
  prototype lets anyone make a forecast and asks for sign-in only to save and
  share it. Requiring an account before a reader can try the page collects
  contact details from people who have not decided to keep anything, which
  weakens the voluntariness of the consent POPIA needs. **Owner's decision.**
* The sign-in does not ask for, and the backend spec does not store, anything
  a provider offers beyond name, email and account id (friend lists, profile
  photos, location).
* No tracking pixels or social SDKs on these pages; share buttons are plain
  links.

## Open decisions for the owner

1. Sign in to **create**, or sign in to **save and share** (built as the latter).
2. Which providers: Google, Apple, Microsoft, Facebook and X are built as
   buttons (the email link was dropped). Each needs an app registration, a
   privacy-policy URL and (Apple, Facebook) a data-deletion URL. X does not
   reliably return an email. Instagram has no personal-account sign-in (Meta
   closed it in December 2024).
3. Retention: proposed deletion on 30 June 2027; updates until unsubscribe.
4. Prizes: whether there are any, the rules, the promoter, how ties break, and
   who may enter. The scoring rule is frozen before 4 November (DESIGN-decided §5).
5. The lock time: proposed 07:00 SAST on 4 November, when polls open.
6. `noindex` on `/f/*`: recommended, so search engines do not index readers'
   names against political forecasts; shared links still preview.
7. Whether a reader's name appears on any public leaderboard (needs its own
   consent, not built).
8. Per-user cap on saved forecasts (proposed 20) and the D1 location hint.
9. How ward calls become combined votes for `seats.allocate` (Integration 1),
   which is a model question.
10. The trust-slider mapping (Integration 3).
