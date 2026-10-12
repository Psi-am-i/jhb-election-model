# Review: one chance on the reader's card (6ae7e90, 63138a8)

Independent diff review, `git diff 6ae7e90~1 63138a8`, branch `site-release`,
against `CARD-COHERENCE-BRIEF.md`. Read-only: nothing edited, built, deployed
or emitted. Reviewer: atlas-claude, 2026-10-12.

**Verdict: ship after fixes.** One blocking finding (1): the edge accepts a
card answer from the previous seat Worker and would cache its wording, measured
from the medians, for a year. The rest of the brief is implemented correctly
and the new rules are mutation-sensitive.

## Findings

### 1. BLOCKING — the edge accepts an old seat Worker's answer and caches it immutably at `/og/3/`

`src/share-edge.js:196-198` checks only that `outcome.boldest` is an object.
The seat Worker before this change returns `boldest = {party, seats, middle,
p, text}`, which passes. A new site Worker against an old `joburg-seats`
therefore draws "Your boldest call: … We give that …" with a call measured
from `middle_seats`, with no one-seat skip and with the badge banding the
exact chance (so badge and printed figure can disagree at an edge). A sealed
link's image is stored at `/og/3/…&ds=<draws hash>` with
`max-age=31536000, immutable` (`share-edge.js:265`, `imageCache`). The draws
do not change in this release, so the key stays valid after the Worker is
redeployed and the wrong image is served for the year.

Three routes reach it:
- the brief's own order ("UAT version URL, then deploy, then redeploy
  `joburg-seats`");
- `docs/DEPLOY-UAT.md:289` "Either order of deployment works for link
  previews except one window", which names only the harmless window (new
  Worker, old `forecast.json`, same prediction) and omits this one;
- the rollback paragraph (`docs/DEPLOY-UAT.md:280`): "Rolling back only
  `joburg-seats` puts link previews on the generic image" is no longer true.

The 2026-10-10 release had this property ("The other order fails visibly but
safely": the edge refused an answer with no `boldest`). This change loses it.

**Fix.** In `cardAnswer`, refuse an answer whose call was not measured from
the prediction: add `|| !("prediction" in o.boldest)` to the condition at
line 198 (`prediction` is `null` on a no-call answer, so `in` is the right
test). Add a node test feeding `cardFor` an answer whose `boldest` carries
`middle` and no `prediction`, asserting rejection. Rewrite the DEPLOY-UAT
paragraph to say `joburg-seats` deploys first, that the other order now falls
back to `/og.png`, and correct the rollback line. Until the guard ships,
deploy `joburg-seats` before the site Worker (DEPLOY-UAT's numbered steps
already do; the brief's order does not).

### 2. SHOULD-FIX — `printed_chance` is a second copy of `chance_text`'s thresholds

`src/reweight.py:918` and `:935` each carry `0.99`, `0.0005`, `0.095` and the
two format strings. The docstring says "The rounding is chance_text's own (its
format strings), so the two cannot differ"; it is a copy, so they can. They
agree today: I compared them on 2,000,001 evenly spaced chances in [0, 1] plus
the edge values (0.0005, 0.095, 0.99, 0.145, 0.445, 0.295, 0.0495, 0.04995),
parsing `chance_text`'s output back to a fraction: 0 disagreements, and on
the same grid every badge's band contains the printed figure. The project
rule is one definition.

**Fix.** One helper returns the printed value and its text (e.g.
`_printed(p) -> (value, text)`); `chance_text` and `printed_chance` both read
it.

### 3. SHOULD-FIX — nothing checks that the page sends the prediction

`make.js:416` and `:1016` send `prediction: D.start.seats`; `page.py:565`
raises without it. No test asserts the request field. Deleting it leaves the
suite green and breaks "Analyse my forecast", the arrival view and the page's
share image at runtime ("The analysis could not run").

**Fix.** Add `"prediction: D.start.seats"` to `need_js` in
`tests/test_your_forecast_page.py:1975` (or assert both call sites).

### 4. SHOULD-FIX — the page-level boldest-call assertion is vacuous

`tests/test_your_forecast_page.py:1509`:
`assert bold["party"] is None or bold["prediction"] == …`. The request sends
`seats = d["start"]["seats"]` as both the reader's seats and the prediction,
so `party` is always `None` and the second clause never runs.
`interactive/tools/native_play.py` also passes `"prediction": seats`, so the
Pyodide-against-native comparison (`page.test.mjs`) never compares a non-null
boldest call.

**Fix.** One `analyse` call whose prediction differs from the reader's seats
(e.g. the start with one party moved by several seats), asserting the call's
party, seats, `prediction` and `p` against `reweight.boldest_call` on the
served draws. Give `native_play` one such case too.

### 5. SHOULD-FIX — the image cache key and the Worker's 409 check name the draws, not the prediction

`start.seats` is a function of the draws AND of code (`prediction.py`, the
seat law, `score_forecasts.model_forecast`; `build_make.start_state`). The
edge cache key is `ds=<draws_sha256>` (`share-edge.js:265`), and
`entry.load_prediction` (`entry.py:105`) and `card` check only the draws
hash. A future change to the prediction with the same draws would keep
immutable images measured from the old prediction, and a warm seat Worker
isolate would keep the old `start.seats` in `_DRAWS` without a 409. Not
reachable in this release (no prediction code changes).

**Fix.** Put a hash of `start.seats` (or `start.f`) in `forecast.json`, send
it with `/v1/card`, check it in `card` alongside `draws_sha256`, and add it
to the cache key; or bump `CARD_VERSION` as a release rule whenever
`prediction.py` or the seat law changes, written in DEPLOY-UAT.

### 6. NOTE — failure modes in the seat Worker, and why refusing is right

From `entry.py:136-150` and `share-edge.js:196-283`:

| failure | Worker | reader sees |
|---|---|---|
| `forecast.json` missing or non-200 | `RuntimeError`, `_DRAWS` unset, 503 | `/og.png` (302, `no-store`); retried next request |
| `forecast.json` names other draws | `ValueError`, `_DRAWS` unset, 503 | `/og.png`, as above |
| cold isolate | three sequential fetches, the 5.4 MB `base.bin` and `forecast.json` parsed | card, or `/og.png` past `SEATS_TIMEOUT_MS` (3 s) |
| warm isolate, new draws published | 409 (pre-existing) | `/og.png` |

Refusing is better than falling back to `middle_seats`: a fallback would print
a call from a different reference beside a badge and cache it, which is the
defect the brief removes. Two costs: during a hash mismatch every card request
re-downloads and re-parses the full draws (no negative cache), and the cold
path adds one serial fetch under the 3 s budget. Fetching the three files with
one `Promise.all`-equivalent (`asyncio.gather`) would remove the added
latency. On the page, no check ties `forecast.json`'s `draws_sha256` to the
draws Pyodide loaded; the prediction and draws are deployed together, so this
is a browser-cache-skew risk only.

### 7. NOTE — the known limit is unchanged by the one-seat rule

Every 50th published simulation (n = 100), each taken as a reader's forecast
against the prediction: median boldest-call chance 1.13%; badges 90 Hail Mary,
10 Wild call. The calls that set them are mostly parties the prediction holds
at 0 to 3 seats, called at 2 to 16 seats (e.g. People of Joburg 0 → 3 or 4,
Ekhethu 0 → 2, BOSA 3 → 16), which the one-seat rule does not reach. This is
BADGE-DECISION's "known limit, accepted" re-measured under the new reference.

### 8. NOTE — wording

- Card wording matches the brief: "Your boldest call: the Patriotic Alliance
  at 38 seats." then "We give that a 4% chance." (`share-card.js:111`,
  `:91`); the arrival view keeps its "<name>'s boldest call" lead; no "this
  outcome" on any card (asserted in `share.test.mjs`).
- "Analyse my forecast" prints "Council outcome: …" and "We give that council
  outcome a 45% chance." (`make.js:1055-1056`), as the brief asks.
- The no-call line "No call goes beyond our prediction." uses "our
  prediction" in STYLE.md rule 11's sense. It is also printed when the reader
  differs only in skipped one-seat parties, where it is true of calls counted
  and slightly loose as a description of the forecast.
- STYLE.md:66's example ("We give this outcome an N% chance") now describes
  wording the cards no longer print; it still describes the per-party seat and
  vote tooltips in Analyse (`make.js:1076-1085`, `chanceSentence`). Worth a
  line in STYLE.md naming the call chance as the card's.
- `arrival.js:115-116`: `.yf-arr-chance` now holds the call line and
  `.yf-arr-bold` the chance. The class names describe the old content; check
  the styling in the screenshot step.
- JUDGEMENT-CALLS §N10 states measured figures ("twenty-three parties", ANC
  66 against 70). I re-derived both (below); they belong in MODEL-LOG or
  BADGE-DECISION with a pointer from §N10, per CLAUDE.md §2.

### 9. NOTE — one definition and copies

- `worker-api/seats-py/src/reweight.py` is byte-identical to
  `src/reweight.py` (`cmp`), and `node worker-api/tools/sync_seats_py.mjs
  --check` reports "10 files and code_ref.py, current". The copy is
  gitignored and made by that tool, as the brief requires.
- `site/your-forecast/py/reweight.py` and `site/your-forecast/py/page/reweight.py`
  (tracked) differ from `src/reweight.py` at line 136, `SKIPPED_CALL_SEATS`:
  `site/` is the previous release build and is regenerated by the release
  build. Not rebuilt here.
- No JavaScript computes a call, a chance or a badge: `share-card.js` reads
  `outcome.boldest.text` and `outcome.badge` from Python.

### 10. NOTE — CARD_VERSION 2 → 3

`/og/1/` and `/og/2/` answer 301 to `/og/3/` with the query kept
(`share-edge.js:452-453`); the 301 is matched before the cache, so v2 edge
cache entries are unreachable; the v3 key is new. Sealed links keep working:
the seal covers the link's fields, not the version or the code. A crawler
holding the v2 bytes keeps them until it re-fetches (as recorded in
DEPLOY-UAT for v1 → v2). Correct, subject to finding 1.

## What I checked

Measured on the served pair `site/draws/` and `site/your-forecast/forecast.json`
(model 7ea27c28):
- `forecast.json` `draws_sha256` equals sha256(manifest + base.bin): true.
- `start.seats` against `middle_seats`: 23 parties differ; ANC 70 against
  66, DA 65 against 66. The prediction against itself: no call, Safe bet.
  Eight parties sit at 1 seat in the prediction.
- Badge against printed chance: 0 disagreements on the grid in finding 2.
- Mutations of `src/reweight.py`, each run against the seven boldest-call and
  badge tests in `tests/test_reweight.py` (scratch copies, repo untouched):

  | mutation | red |
  |---|---|
  | skip removed (`x == m` only) | one-seat test |
  | skip `and` → `or` | by-hand, measured-from-prediction, one-seat |
  | measured from `middle_seats` | measured-from-prediction, one-seat, owner's table |
  | badge reads the exact chance | printed-chance edges |
  | `SKIPPED_CALL_SEATS = 2` | by-hand, one-seat |

- The one-seat rule names no party (`reweight.py:1144-1158`) and applies to
  parties with no draw column.
- Targeted Python modules, run after the last commit:
  `.venv/bin/python tests/run_all.py -k reweight -k reader_seats -k share -k
  page_share -k worker_routing -k your_forecast_page -k judgement_sheet -k
  register_matches_code`: 8 modules, exit 0, 0 failed in each (171 passed in
  total). This is a PARTIAL RUN (8 of 80 modules), not a suite run.
- `node --test interactive/tests/share.test.mjs`: 27 pass, 0 fail.
- The new share tests construct their failing case (the fixture asserts the
  two chances differ, so a card printing the council figure fails).
  `test_the_card_reads_the_published_prediction_the_draws_were_built_into`
  reads served files for its positive half (observed input); its refusal half
  is constructed.

## What I did not check

- The whole suite; `worker-api` vitest; `page.test.mjs` under Pyodide.
- Regenerating `share-fixture.json` or `native-play.json` with their tools.
- A scratch build, the 1200-wide card screenshot, the UAT Version URL, the
  deployed seat Worker's behaviour under a real cold start.
- Visual layout of the link, story and two-forecast cards with the swapped
  line order.
