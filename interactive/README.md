# Readers' forecasts: prototype

"Make your own forecast", "play with the model", sign-in to save, the share
sheet and share image, and the shared forecast page, for
joburg.whysoserious.city. **A prototype**: the builder's and shared page's
figures are synthetic, and on a loopback host sign-in and saving are stubs that
never leave the browser. "Play with the model" runs on the model's published
draws (`site/draws/`) and computes every figure with `src/reweight.py` under
Pyodide in a Web Worker (below); `build_site.py` builds it into the site as
`/play/` (`src/build_play.py`, "Play with the model, built" below). Seats
on the builder and the shared page come from the project's own seat code
(`src/reader_seats.py` and its imports) running under Pyodide, from a served
copy in `py/`. Nothing under `site/` or `src/` is touched at run time.

The backend is specified, not built: `BACKEND.md`.

## Open it

```
cd ~/projects/atlas-jhb-election-model
python3 -m http.server 8801 --bind 127.0.0.1      # port 8801, never 8765
```

| page | URL |
|---|---|
| Make your own forecast | http://127.0.0.1:8801/interactive/make.html |
| Play with the model | http://127.0.0.1:8801/interactive/model.html |
| A shared forecast (demo) | http://127.0.0.1:8801/interactive/f/?id=demo7Qx2Lp |
| Privacy notice placeholder | http://127.0.0.1:8801/interactive/privacy-placeholder.html |

`python3 -m http.server` listens with a backlog of five, and the pages fetch
enough modules at once that some connections are reset; if a page fails to
load a module, serve with a larger backlog:
`python3 -c "import http.server as h, functools; S=type('S',(h.ThreadingHTTPServer,),{'request_queue_size':128}); S(('127.0.0.1',8801), functools.partial(h.SimpleHTTPRequestHandler, directory='.')).serve_forever()"`.

Serve the repository root, not `interactive/`: the nav links point at the live
pages in `../site/`, and the builder imports the Worker's own `validate.js`,
`seats.js` and generated schema from `../worker-api/`. The pages are ES modules,
so `file://` does not work.

**Copy the Python first**, after checkout and after any change to it:
`node interactive/tools/sync_py.mjs` (`--check` to verify). It writes
`interactive/py/` (gitignored): the seat code, with worker-api's own copy rule
and file list, plus the seat Worker's `entry.py`; and, separately, the page
code in `py/page/` (`PAGE_FILES`: `reweight.py` and its import closure;
`PAGE_DATA`: the poll register and the city file it opens). `manifest.json`
carries both lists and a hash of each. Without it the builder stays locked and
"play with the model" keeps the published forecast, and each says which
command to run.

Tests: `node --test interactive/tests/*.test.mjs`. Set `PYODIDE_NODE` to a
directory holding `node_modules/pyodide` (0.29.5) to also run both engines
under Pyodide; otherwise those two tests are skipped and say so. After a
re-export of `site/draws/` or a change to the page code, regenerate the native
fixture: `.venv/bin/python interactive/tools/native_play.py --write` (the test
says when).
Screenshots at 375 px and 1440 px are in `screenshots/`.

To rebuild the fixtures: `python3 interactive/tools/make_fixtures.py`.

## Play with the model, built

`build_site.py` builds the page into the site on every Johannesburg build
(`src/build_play.py` assembles it; `build_site` renders, audits, scans and
stamps it like every other page). Served layout, under the site root:

| path | what |
|---|---|
| `play/index.html` | `model.html` with the site's `THEME_HEAD`, nav and footer, and a build twin of each results element filled at its `__PLAY:<name>__` marker (`build_play.FILL`): the banner and seat rows from the forecast sheet's own seat tokens, the one-line result, the published ward map (`render_map.ward_layers`, a `MAP` generated region), turnout by group, where each party's votes come from, and the notes' figures, all as `{{tokens}}`. First paint is ledgered tokens, no script; nothing of `/forecast` is embedded |
| `play/js/` | `model.js` (the LIVE writer), `play-state.js`, `model-worker.js` (its one draws line rewritten to `../../draws/`), `reweight-engine.js`, `play-share.js` (the share sheet, LIVE writer of region `share`), `play-card.js` (the share image, a LIVE writer of no region), `card-text.js` |
| `play/css/interactive.css`, `play/css/play.css`, `play/pyboot/page.py` | copies (`play.css` holds the page's own rules, every class `pl-`) |
| `play/py/manifest.json`, `play/py/page/` | the page's Python, copied by `tools/sync_py.mjs`, which the build runs |
| `play/parties.json` | party names, colours and the article a name takes ("the ANC") |
| `play/ward_paths.json` | the ward boundaries and place labels, and the stripe tile, for the map under a reader's settings |
| `play/labels.json` | `js/labels.js`'s words and number range, for the share image's random label |
| `draws/` | the published draws (`export_draws`), already under `site/` |

The number gate holds it: every figure a reader's settings produce is written
by `play/js/model.js` (and the share sheet by `play/js/play-share.js`), into `data-live` regions that hold no digit at
build time; `stats.script_writes` refuses the build otherwise
(`tests/test_play_page.py`). The page says once, in its notes, that these
figures are worked out in the reader's browser. Each results element has a
build twin of tokens and a LIVE sibling: `model.js` sets `data-touched` on the
`result` region when a control is away from the published setting, and
`css/play.css` swaps them. Opened from the repository as the prototype, the
page shows no published figures (they exist only once built): build into a
scratch directory, link `site/draws/` and `site/share.jpg` beside it, and serve
that directory to see the page as it ships.

### Saving and sharing, anonymous

A reader's settings live in the page's address (`js/play-state.js`:
`?t=…&p=…&k=…&l=…&b=…&mv=…&n=…`, only the fields that differ from the published
setting, checked against the controls' bounds on load; a field out of bounds
falls back to the published setting and the page says which). "Share this
forecast" opens a sheet with an optional name (free text, at most
`NAME_MAX` characters, put only in the field, the link and the image, drawn as
text), the image, and the link (copy, or the phone's own share sheet). The
image, 1200×630 or 1080×1920, is drawn in the browser by `js/play-card.js` from
the same compute result the page shows: the Hillbrow Tower strip from
`share.jpg`; a headline saying whose figures these are ("The model's
Johannesburg forecast" with the name on a "Shared by" line when nothing is
moved, "<name>'s settings on the model" with "Not the model's forecast" under
it when something is); the largest-party line, ties apart; the ward map, north
marked, with a line saying it holds the ward seats only; and each party's
middle seat count with the range holding nine in ten. No account, no cookie, no storage, nothing sent: a shared link shows
the page's generic preview (`og:` tags with no figure, the site's
`share.jpg`). Tests: `tests/play-share.test.mjs`, `tests/test_play_page.py`.
Screenshots: `screenshots/play-*.png`.

## Files

| path | what |
|---|---|
| `make.html`, `js/make.js` | the builder: map, vote shares, coalition, results, save and share |
| `js/builder-state.js` | the builder's state and every edit to it; pure, and can only hold a valid forecast (DESIGN-decided §14) |
| `js/seat-engine.js`, `pyboot/boot.py` | seats under Pyodide: the Worker's `seatRequest`, the seat Worker's `entry.answer`, the Worker's `checkSeatAnswer` |
| `tools/sync_py.mjs`, `py/` | the served copy of the seat code (gitignored; written by the tool) |
| `js/api.js` | the one backend door: the stub on loopback hosts, the Worker API elsewhere (`?api=stub` / `?api=live` override) |
| `tests/` | `node --test`: random builder edits against `validate.js` and the seat law; `/api/me` mapping |
| `model.html`, `js/model.js` | play with the model: the page's one source (the build cuts its `__DEVONLY__` spans and fills its `__PLAY…__` markers), and the ONE module that writes figures, only into `data-live` regions (`stats.LIVE_WRITERS["play/js/model.js"]`) |
| `js/model-worker.js`, `js/reweight-engine.js`, `pyboot/page.py` | the Web Worker, the engine loader (injectable, also run by the node test), and the Python entry that routes settings to `src/reweight.py` |
| `js/play-state.js` | the reader's settings, their bounds and the URL form (F16); pure |
| `js/play-share.js`, `js/play-card.js`, `js/card-text.js` | play's share sheet, its share image, and the measured text layout and PNG step both share images use |
| `tools/native_play.py`, `tests/native-play.json`, `tests/play-settings.json` | the native side of the native-vs-Pyodide harness (F19), its stored output, and the settings both sides compute; `--measure` reports what `page.py` imports and opens |
| `f/index.html`, `js/f.js` | the shared forecast page, `/f/<id>` in production |
| `js/map.js` | the ward map (geographic and equal-sized), painting, keyboard |
| `js/card.js` | the share image, SVG to PNG, 1200×630 and 1080×1920 |
| `js/share.js` | the share sheet |
| `js/auth-ui.js` | sign-in and the consent screen, rendered from `js/consent-terms.js` |
| `js/consent-terms.js` | the consent wording, its keys and its version hash: one definition, imported by the page and `worker-api` |
| `js/labels.js` | the default-label word list and generator: one definition, imported by the page stub and `worker-api` |
| `js/api-stub.js` | **stub** of the API in BACKEND.md, in localStorage; used through `js/api.js` |
| `js/common.js` | fixture loading, escaping, theme toggle |
| `css/interactive.css` | styles; a copy of the site palette |
| `fixtures/` | **placeholders**, below |
| `tools/make_fixtures.py` | writes `fixtures/` |

## What is stubbed, and what replaces it

| stub | stands in for | the real thing |
|---|---|---|
| `fixtures/placeholder-model.json` | the model's roster, most likely ward winners, combined vote shares, the combined total they scale to, and published seats | the S2 export (`site/draws/base.bin` + manifest, PLAN.md) and the certified roster in IEC ballot order |
| roster names and colours on the unbuilt model page (`placeholder-model.json`, and the code spaced out for other parties) | the roster | served: `play/parties.json`, written by `build_play.py` from `render_sheet.NAMES`/`CHIPS` and `parties.display_name` |
| the ADAPTER block in `pyboot/page.py` | Lane R's `page_polls`, `poll_trust_sd`, `poll_weights(trust=)`, `turnout_tilt(pin_to=)`, `figure()["withheld"]`, `sampling_se`, and Lane E's `model_sha256` | delete the block's fallbacks at merge |
| `js/api-stub.js` (loopback hosts only) | the Worker API and OAuth | `worker-api/`, reached through `js/api.js` on any other host |
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

1. **How a reader's forecast becomes seats: `src/reader_seats.py`, BUILT.**
   The reader edits each party's COMBINED vote share and the ward winners
   (DESIGN-decided §10). The builder (`js/make.js`) sends the Worker's own
   request (`seatRequest`) to the seat Worker's own handler (`entry.answer`)
   under Pyodide and checks the answer with the Worker's `checkSeatAnswer`, so
   the seats on screen are the seats the server stores. The page paints first
   and unlocks its controls when Pyodide, numpy and the seat modules have
   loaded; the load times are logged to the console and kept in
   `window.__seatEngineTimes`. The builder can only hold a valid forecast
   (§14): see "Design decisions".
2. **The engine: BUILT (S6 Lane P).** `src/reweight.py` under Pyodide in a Web
   Worker, behind a first paint of the published forecast. Each cell's
   `manifest.json` + `base.bin` is fetched when first chosen. Until a control
   moves the page shows the published panels and runs no figure; once one
   moves, the seat table is computed and every published panel says it is of
   the published forecast. Every figure shows its ± seats (`figure()`'s
   `sampling_se`); a move that would take any figure the page shows past
   `reweight.MAX_FIGURE_SE_SEATS` (`within_precision`, via `pyboot/page.py`)
   or below the effective-draw floor stops: the control returns to the last
   setting that passed and greys. A link opened past it shows "withheld".
3. **The trust-slider mapping** is the owner's (SPEC-v2 decision 2): trust t
   gives the poll error `poll_sd / t`, so 100 is the poll's own sampling error
   and 0 is no weight.
4. **Ward order and ids** in the forecast body must be the 2026 delimitation's
   135 wards in ward-number order, and the roster the IEC's certified list
   (CLAUDE.md §4b).
5. **Server-rendered `/f/<id>`** with Open Graph tags; the comment at the top of
   `f/index.html` lists them.
6. **Production mode is wired, not exercised.** On a non-loopback host
   `js/api.js` talks to the Worker: sign-in goes to `/auth/<provider>/start`,
   the callback's `/make?consent=1` opens the consent screen from `GET /api/me`
   (deletion date, X handle, unverified address), and a page whose wording hash
   differs from the server's says so before the reader fills anything in.
   **Not built:** the Turnstile widget. `POST /api/forecasts` needs its token
   when `TURNSTILE_REQUIRED` is on, so a production save fails until it is.
7. **What production must serve beside the page:** `worker-api/src/validate.js`,
   `blocklist.js`, `seats.js`, `http.js`, `generated/forecast.schema.json`, and
   `interactive/py/` + `pyboot/`, at the same relative paths (or rewrite the
   imports in one place at build). The page loads Pyodide 0.29.5 and numpy
   from cdn.jsdelivr.net.

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
* **An impossible forecast cannot be built (DESIGN-decided §14).** The map
  starts with every ward at the model's call (or the model page's lever state),
  and the vote at the model's shares. There is no eraser and no "clear": a ward
  changes winner, it is never empty. The vote is held as whole votes summing
  exactly to the combined total the seat law scales to, so it always sums to
  100%; moving one party rescales the others in proportion. A party that wins
  a ward keeps at least one vote, which is the seat law's own condition
  (`reader_seats` refuses a ward winner with no votes); giving a ward to a
  party with none raises it to one vote, with a note. Undo restores the ward
  calls and the votes together. The only things left for the reader before a
  save are choices, not repairs: a coalition, and a label the validator
  accepts (checked as they type with the Worker's own `cleanDisplayName`).
  Making does not need an account; saving and sharing do.
* **Three ways to call a ward**: tap or drag on the map (drag with mouse or pen
  only, so a finger can scroll), a whole compass sector at once, and a list of
  one select per ward, grouped by sector, for keyboard and screen-reader users.
  The map is one tab stop; arrow keys move between neighbouring wards, Enter
  paints (Delete explains that every ward needs a winner). Undo keeps the last
  60 edits.
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
9. ~~The trust-slider mapping (Integration 3).~~ Decided 2026-09-30.
