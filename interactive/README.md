# Readers' forecasts

"Your forecast" (adjust the model, then break it), sign-in to save, the share
sheet and share image, and the shared forecast page, for
joburg.whysoserious.city.

One page is BUILT into the site and ships anonymous (no sign-in, no server
storage, no prize): "your forecast" (`/your-forecast/`,
`src/build_your_forecast.py`), below. It replaced "play with the model"
(`/play/`) and "make your own forecast" (`/make/`) on 2026-10-03, which are
now its two sections; `src/worker.js` answers both old addresses with a 301 to
it, query string kept, so a shared link restores. It runs on the model's
published draws (`site/draws/`) and computes every figure with the project's
own Python under Pyodide in two Web Workers. Nothing under `site/` or `src/`
is touched at run time.

Still a **prototype**: sign-in, saving and the shared forecast page (`f/`),
which run on the synthetic fixtures and, on a loopback host, on stubs that
never leave the browser. Their backend is specified in `BACKEND.md` and built
in `worker-api/`, not deployed.

## Open it

The page has no figures until it is built. Build into a scratch directory,
link `site/draws/`, `site/logos/` and `site/share.jpg` beside it, and serve
that directory:

```
cd ~/projects/atlas-jhb-election-model
.venv/bin/python src/build_site.py --out /tmp/yf/site
python3 -m http.server 8801 --bind 127.0.0.1 --directory /tmp/yf/site   # port 8801, never 8765
```

| page | URL |
|---|---|
| Your forecast | http://127.0.0.1:8801/your-forecast/ |
| A shared forecast (demo), from the repository root | http://127.0.0.1:8801/interactive/f/?id=demo7Qx2Lp |
| Privacy notice placeholder, from the repository root | http://127.0.0.1:8801/interactive/privacy-placeholder.html |

`python3 -m http.server` listens with a backlog of five, and the page fetches
enough modules at once that some connections are reset; if a module fails to
load, serve with a larger backlog:
`python3 -c "import http.server as h, functools; S=type('S',(h.ThreadingHTTPServer,),{'request_queue_size':128}); S(('127.0.0.1',8801), functools.partial(h.SimpleHTTPRequestHandler, directory='/tmp/yf/site')).serve_forever()"`.
The pages are ES modules, so `file://` does not work.

**Copy the Python first**, after checkout and after any change to it:
`node interactive/tools/sync_py.mjs` (`--check` to verify). It writes
`interactive/py/` (gitignored): the seat code, with worker-api's own copy rule
and file list, plus the seat Worker's `entry.py`; and, separately, the page
code in `py/page/` (`PAGE_FILES`: `reweight.py`, `start_rule.py` and their
import closure; `PAGE_DATA`: files that closure opens, none today).
`manifest.json` carries both lists and a hash of each. The build runs it.

Tests: `node --test interactive/tests/*.test.mjs`. Set `PYODIDE_NODE` to a
directory holding `node_modules/pyodide` (0.29.5) to also run both engines
under Pyodide; otherwise those two tests are skipped and say so. After a
re-export of `site/draws/` or a change to the page code, regenerate the native
fixture: `.venv/bin/python interactive/tools/native_play.py --write` (the test
says when). Screenshots at 375 px and 1440 px are in `screenshots/yf-*.png`
(`tools/yf_screenshots.mjs`, which can serve a scratch build to the browser
itself with `YF_ROOT`, no port). Whether the page jumps when a lever moves:
`PLAYWRIGHT=<playwright index.mjs> YF_ROOT=site node
interactive/tools/yf_jump_check.mjs` (exit 1 on a jump or an overflowing
reserved region; `YF_JUMP_DEBUG=1` names the blocks that changed height).

To rebuild the fixtures: `python3 interactive/tools/make_fixtures.py`.

## Your forecast, built

`build_site.py` builds it on every Johannesburg build
(`src/build_your_forecast.py` assembles it and copies its files;
`build_site` renders, audits, scans and stamps it like every other page, and
removes the retired `play/` and `make/` directories). Served layout, under
the site root:

| path | what |
|---|---|
| `your-forecast/index.html` | `your-forecast.html` with the site's head (`build_site.SITE_HEAD`: `css/site.css` and the site's scripts), nav and footer; section 1's build twins filled at its `__PLAY:<name>__` markers (`build_play.FILL`: the banner and seat rows from the forecast sheet's own seat tokens, the one-line result, the published ward map, turnout by group, where each party's votes come from, the notes' figures), all as `{{tokens}}`; section 2's seat-table attributes at its `__MAKE:<name>__` markers. First paint is ledgered tokens, no script |
| `your-forecast/js/` | section 1: `model.js` (LIVE writer), `play-state.js`, `play-card.js` and `play-share.js` (writers), `model-worker.js` (its one draws line rewritten to `../../draws/`), `reweight-engine.js`, `pubtip.js`; section 2: `make.js` and `make-share.js` (writers), `make-state.js`, `builder-state.js`, `map.js`, `make-worker.js`, `seat-engine.js` (its `seats.js` import rewritten to `./seats.js`), `seats.js` and `http.js` (from `worker-api/src`, Worker only); both: `yf-url.js` (the one address), `forecast-card.js` (the share image, a writer of no region), `card-text.js`, `seat-table.js`, `tip.js` (where each tooltip goes) |
| `your-forecast/css/` | `interactive.css`, `play.css` (section 1's rules, every class `pl-`), `your-forecast.css` (the layout and what both sections share, every class `yf-`) |
| `your-forecast/pyboot/` | `page.py` (section 1's engine, and section 2's hand-off and analysis), `boot.py` (the seat code's) |
| `your-forecast/py/` | the served Python, copied by `tools/sync_py.mjs` |
| `your-forecast/parties.json`, `ward_paths.json`, `labels.json`, `laws.json` | party names, colours, articles and whether the site has a logo; the ward boundaries; the share label words; the seat laws' names (`render_sheet.SEAT_LAWS`, as `/forecast` prints them) |
| `your-forecast/forecast.json` | section 2's one data file (`build_make.forecast_data`): the generated schema, the ward geometry, the published start, `context_ref` |
| `draws/` | the published draws (`export_draws`), already under `site/` |

The number gate holds it: every figure a reader's settings or edits produce
is written by a module `stats.LIVE_WRITERS` lists, into `data-live` regions
that hold no digit at build time, each region with one writer;
`stats.script_writes` refuses the build otherwise
(`tests/test_your_forecast_page.py`). Section and step numbers are CSS
counters for that reason.

### Section 1, "Adjust the model"

The published draws re-weighted by the reader's turnout by population group,
one poll and how far to believe it, and the weight of by-elections, and
seated under a law the reader picks: "See how other systems would seat this
vote", with South African law and Germany's of 2000, 2015 and 2023 under the
names `/forecast` gives them. Levers on the left, one card each; on a wide
screen a column that holds still while the levers scroll, the map above the
seat table, each the column's full width. The map's height is capped by the
window so the table's head shows under it, and the column, never taller than
the window, scrolls on its own for the rest. The banner of seats sticks while section
1 is in view and leaves with it.
Each results element has a build twin of tokens and a LIVE sibling:
`model.js` sets `data-touched` on the `result` region when a control is away
from the published setting, and `css/play.css` swaps them. The status strip
reads "Your changes: …". A computation in flight shows a floating
"Computing…" (`busy`), which reserves no space. A seat row or banner entry
whose middle moved since the figures last shown pulses once, with a ▲ or ▼;
on a narrow screen with the seat table out of view, a toast (`toast`,
headed "Since your last change") names the parties that moved, each with its
logo where the site has one. The banner's own arrows are against the
published forecast. Under
`prefers-reduced-motion` nothing moves. The share row ends the section;
only a council seated under South African law can be shared
(`play-state.shareable`): under another law the button is disabled and says
why.

### Section 2, "Break the model"

The same forecast as the reader's own: every ward called, each party's share
of the combined vote set, a coalition picked, the seats from the seat law
under Pyodide (`reader_seats`, the Worker's own request and check). It loads
its data and its seat Worker (a second Pyodide) when the reader comes near it,
or at once for a link carrying a section 2 forecast or `#break`.

**Where it starts.** Untouched, section 1 is the published forecast and
section 2 opens at the published start (`build_make.start_state`, written
into `forecast.json`): each ward's modal winner over the published draws
(`score_forecasts.model_forecast`), and shares that seat each party the seat
panel names at its published middle, or its ward count where higher, Others
taking the rest (`src/start_rule.py`, whose docstring states the rule). Once
section 1 moves, `page.py`'s `handoff` applies the same rule to the reader's
weighted draws: each ward's most likely winner under the reader's changes
(exactly the winners section 1 shows), and shares from the weighted middles
of the statutory seats. While section 2 is unedited it follows section 1;
once edited, a change in section 1 overwrites nothing, and the status line
offers to start again from it (undo restores the edits). A link's forecast
is kept as the reader's. While the forecast is still its start, a line under
"Your council" names every named party the ward floor raised above its
middle seat count (`handoff` returns the middles; the published start's are
`forecast.json`'s `published_middle`), and the share image says the same.

**The walkthrough.** Four numbered steps: call the wards, set the vote, pick
who governs, see how likely it is. One is highlighted at a time; "Next" marks
a step done, highlights the next, scrolls to it and focuses its first control
(the first vote slider, the first coalition chip, "Analyse my forecast").
Every step stays usable whichever is highlighted. The chips for painting
wards are every party seated in the reader's council or at its start, and
the party chosen (`builder-state.chipParties`, one rule for every party);
every other party is in the select beside them.

**The calls to act** (owner, 2026-10-05) are full-width rows, each with one
line on what it gives: "Share this forecast" at the end of section 1
(section 1's sheet) and at the foot of section 2, before the notes (section
2's sheet: the map, the seats, our chance, a sealed link); "Analyse my
forecast" in step 4.

**"Analyse my forecast"** (`page.py`'s `analyse`, `reweight.within_band`,
`reweight.ward_calls_likelihood`; JUDGEMENT-CALLS §N3). Every chance is the
published forecast's. The region opens with what "this outcome" is (the
reader's council-level outcome, `share-card.outcomeWords`), its chance, and a
line that it is the citywide result only. "Your map" (ward wins) is the
reader's map, each ward in the colour called and as strong as our chance for
that call, with the number of calls expected to come true beside it;
"Citywide vote and seats" is the table below and the totals. The long
explanation is the note on the outcome. Hovering a ward gives the chance of the reader's call
there; each party's seats get the chance of landing within
`reweight.ANALYSIS_SEAT_BAND` seats; its vote the chance its LIST-BALLOT share
lands within `ANALYSIS_SHARE_BAND_POINTS` points (the draws carry no combined
share, and the page says so); and the whole forecast the expected number of
the reader's ward calls that come true ("We expect N of your M ward calls to
come true. But historical trends can always be broken."), with beneath it the
rank of the reader's calls among the simulations' ward results, worded as a
rank and never as a chance (JUDGEMENT-CALLS §N3). A ward's chance shows on
hover, on keyboard focus and on a tap with no party chosen. Once shown, the
analysis follows every edit.

### The address is the forecast

`js/yf-url.js` is the page's one address writer. Three disjoint parts:
section 1's (`play-state.js`: `t p k l b mv`, only the fields that differ
from the published setting, checked against the controls' bounds on load),
section 2's (`make-state.js`: `v=1&c=<context ref>&f=<payload>`, the whole
state in base64url, refused with a note if it fails any rule of
DESIGN-decided §14 or was made against another roster, ward list or vote
total), and the name `n` (`play-state.cleanName`, the one rule: free text, at
most `NAME_MAX` characters, refused whole when longer). A write by one
section never touches the other's part. Section 1's share link carries its
part and the name; section 2's carries both sections, since it continues
section 1. Old `/play/?…` and `/make/?…` links reach the page through the
Worker's redirect with their query strings and read back unchanged
(`tests/yf.test.mjs`).

**Share images** (`js/forecast-card.js`, the one card module): section 1's
words and rows from `js/play-card.js` (a headline saying whose figures these
are, the largest-party line, the reader's map, each party's middle seat count,
at 1200×630 or 1080×1920); section 2's from `js/make-share.js` ("[Name]'s
election forecast", the reader's map, each party's seats, the coalition).
Both on the site's photograph of Hillbrow Tower (`share.jpg`). No account, no
cookie, no storage, nothing sent: a shared link shows the page's generic
preview (`og:` tags with no figure, the site's `share.jpg`).

Tests: `tests/test_your_forecast_page.py` (the gate, both directions, guards
firing and going quiet, section 1's rows at uniform weights, the start's
definition, the hand-off, the analysis); `interactive/tests/yf.test.mjs` (the
address, both sections, old links); `make.test.mjs` (section 2's part, its
refusals, the card, CPython seats, Pyodide = CPython); `page.test.mjs`
(section 1's engine and section 2's hand-off and analysis, Pyodide = CPython);
`play-share.test.mjs`, `play-state.test.mjs`; `tests/test_worker_routing.py`
(the redirects). Screenshots: `screenshots/yf-*.png`.

## Files

| path | what |
|---|---|
| `your-forecast.html` | the page's one source: the build cuts its `__DEVONLY__` spans and fills its markers |
| `js/model.js` | section 1's LIVE writer (`stats.LIVE_WRITERS["your-forecast/js/model.js"]`); it owns the re-weighting Worker and lends it to section 2 (`engineCall`, `onForecast`) |
| `js/model-worker.js`, `js/reweight-engine.js`, `pyboot/page.py` | the re-weighting Web Worker, the engine loader (injectable, also run by the node test), and the Python entry: `compute`, `handoff`, `analyse` |
| `js/play-state.js` | section 1's settings, their bounds, its address part (F16) and the share rule; pure |
| `js/play-share.js`, `js/play-card.js`, `js/card-text.js` | section 1's share sheet, its share image's words and rows (drawn by `js/forecast-card.js`), and the measured text layout and PNG step |
| `js/make.js`, `js/make-share.js`, `js/make-state.js`, `js/make-worker.js` | section 2: its LIVE writer, its share sheet, its address part, the seat Worker |
| `js/yf-url.js` | the page's one address: both parts and the name; pure but for the one history call |
| `js/forecast-card.js` | the share image both sections draw |
| `js/builder-state.js` | section 2's state and every edit to it; pure, and can only hold a valid forecast (DESIGN-decided §14) |
| `js/seat-table.js` | the site's one seat table, drawn from a reader's figures: the JavaScript twin of `src/seat_table.py`, the same markup for the same rows (`tests/test_seat_table.py`); styled by `src/css/seat-table.css` |
| `js/pubtip.js` | section 1's published map tooltip (copies a ward's `data-tip`) |
| `js/seat-engine.js`, `pyboot/boot.py` | seats under Pyodide: the Worker's `seatRequest`, the seat Worker's `entry.answer`, the Worker's `checkSeatAnswer` |
| `tools/sync_py.mjs`, `py/` | the served copy of the Python (gitignored; written by the tool) |
| `tools/native_play.py`, `tests/native-play.json`, `tests/play-settings.json` | the native side of the native-vs-Pyodide harness (F19), its stored output, and the settings both sides compute (section 1's cases and section 2's `section2` block); `--measure` reports what `page.py` imports and opens |
| `tools/yf_screenshots.mjs` | the screenshots |
| `tools/yf_jump_check.mjs` | the no-jump check: document height, scroll and the landmarks around every lever move, at 375 and 1440 |
| `css/interactive.css`, `css/play.css`, `css/your-forecast.css` | styles |
| `js/api.js` | the one backend door: the stub on loopback hosts, the Worker API elsewhere (`?api=stub` / `?api=live` override) |
| `tests/` | `node --test`: random builder edits against `validate.js` and the seat law; the address; `/api/me` mapping |
| `f/index.html`, `js/f.js` | the shared forecast page, `/f/<id>` in production |
| `js/map.js` | the ward map (geographic and equal-sized), painting, keyboard |
| `js/card.js` | the share image, SVG to PNG, 1200×630 and 1080×1920 |
| `js/share.js` | the share sheet |
| `js/auth-ui.js` | sign-in and the consent screen, rendered from `js/consent-terms.js` |
| `js/consent-terms.js` | the consent wording, its keys and its version hash: one definition, imported by the page and `worker-api` |
| `js/labels.js` | the default-label word list and generator: one definition, imported by the page stub and `worker-api` |
| `js/api-stub.js` | **stub** of the API in BACKEND.md, in localStorage; used through `js/api.js` |
| `js/common.js` | fixture loading, escaping, theme toggle |
| `fixtures/` | **placeholders**, below |
| `tools/make_fixtures.py` | writes `fixtures/` |

## What is stubbed, and what replaces it

| stub | stands in for | the real thing |
|---|---|---|
| `fixtures/placeholder-model.json` | the model's roster, most likely ward winners, combined vote shares, the combined total they scale to, and published seats | the S2 export (`site/draws/base.bin` + manifest, PLAN.md) and the certified roster in IEC ballot order |
| roster names and colours on the unbuilt model page (`placeholder-model.json`, and the code spaced out for other parties) | the roster | served: `your-forecast/parties.json`, written by `build_play.py` from `render_sheet.NAMES`/`CHIPS` and `parties.display_name` |
| the ADAPTER block in `pyboot/page.py` | Lane R's `page_polls`, `poll_trust_sd`, `poll_weights(trust=)`, `turnout_tilt(pin_to=)`, `figure()["withheld"]`, `sampling_se`, and Lane E's `model_sha256` | delete the block's fallbacks at merge |
| `js/api-stub.js` (loopback hosts only) | the Worker API and OAuth | `worker-api/`, reached through `js/api.js` on any other host |
| `fixtures/geometry.json` sectors | the S5 ward-to-sector file | S5 |
| `privacy-placeholder.html` | DRAFT privacy notice (placeholders for the owner's decisions), competition rules, report route | the owner's decisions filled in, checked by counsel |

**The fixtures are synthetic on purpose.** A seeded random generator made them;
none is derived from `ward_draws.csv`, `seat_draws.csv` or any model artefact,
because the model is about to be re-emitted and a real-looking number in a
prototype is a model number in a page. They feed only the prototype pages
(`f/`, the backend's tests); the built `/your-forecast/` reads the published
draws, and no fixture ships.

**Copies to remove at integration** (each is a second definition):

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
   or below the effective-draw floor stops, and says so where it stops
   (owner, 2026-10-05): a slider halts at the furthest setting that passes,
   the track beyond it shaded, with one line under the slider saying why; an
   option of a discrete control (a poll, a by-election weight, a seat law)
   refused at the other settings returns to the last option, is marked, and
   the line beside its control names it and says why. Both are forgotten
   when another control moves. A link opened past it greys the controls and
   shows "withheld".
3. **The trust-slider mapping** is the owner's (SPEC-v2 decision 2): trust t
   gives the poll error `poll_sd / t`, so 100 is the poll's own sampling error
   and 0 is no weight.
4. **Ward order and ids** in the forecast body must be the 2026 delimitation's
   135 wards in ward-number order, and the roster the IEC's certified list
   (CLAUDE.md §4b).
5. **Server-rendered `/f/<id>`** with Open Graph tags; the comment at the top of
   `f/index.html` lists them.
6. **Saving with sign-in is not part of `/your-forecast/`.** The built page is
   anonymous; the old builder's sign-in and save path (`js/api.js`,
   `js/auth-ui.js`, `js/share.js`, `js/card.js`) is no longer imported by it.
   What follows applies when a signed-in save is added back.
   **Production mode is wired, not exercised.** On a non-loopback host
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
  starts with every ward at the model's call (or section 1's, under its settings),
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
  the party chips ride along at the bottom of the map card; section 1
  keeps its seat banner at the top of the screen, and a toast names the
  parties whose seats moved while the seat table is out of view.
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
