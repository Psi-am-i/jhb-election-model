# S1 slice B: the reader entry, new version (specification)

Designer B, 2026-10-08. Read-only; nothing in the repository was edited. Covers
PACKET.md slice B and Amendment 1. **V** = verified (file:line or a command run
in this session; probes in this scratch dir). **A** = argued.

## 0. Facts this spec rests on

| fact | status |
|---|---|
| The live entry path is the site Worker: `src/share-edge.js` seals, decodes with `make-state.decode`, stores in D1 `joburg-entries` (binding `ENTRIES`, `wrangler.toml:136-140`), migrations in root `migrations/` | V |
| Live D1 `entries` table equals `migrations/0001_entries.sql` (7 columns) | V (read of `sqlite_master` on `6f3e7b01…`) |
| Entry row count in production | **not verified**: the count query was denied by the permission classifier. The export script must print it itself (G20). |
| The account store `joburg-forecasts` (`worker-api/src/forecasts.js`, which imports `worker-api/generated/forecast.schema.json`) is not deployed: no such Worker on the account, no such D1, `worker-api/wrangler.jsonc` ids are placeholders, README says nothing provisioned | V (Cloudflare `workers_list`, `d1_databases_list`; `worker-api/wrangler.jsonc:6-8,58-63`; `worker-api/README.md:6-8`) |
| `joburg-seats` (the seat Worker) IS deployed; it serves `/v1/card` to the site Worker's link previews | V (`workers_list`; `src/share-edge.js:176-190`) |
| The placeholder schema has 14 parties, a different total; the page's schema (`site/your-forecast/forecast.json`) has the 74-party roster equal to the draws' `parties` | V (S0 + `python3` read of both files) |
| The draws carry `OTHER` as a 75th column in `pr_share` and `seats/*`; `OTHER` is never a ward winner (`ward_parties` has 23 codes, no OTHER) | V (manifest read) |
| `run_model` builds per-draw integer tallies `ward_totals_d`, `pr_totals_d` and calls `eligible_parties` with both | V (`src/montecarlo.py:5225-5228`) |
| `seats.eligible_parties(ward, pr)` admits a party on `pr > 0`; `outside_pool_wards` routes a ward winner outside the pool to D | V (`src/seats.py:56-98`) |
| `reader_seats` imports only `montecarlo` and `seats` from `src/` | V (`src/reader_seats.py:92-95`) |
| The repository is PUBLIC on GitHub; `backups/` and the leaderboard are gitignored for privacy | V (`gh repo view`, `.gitignore:79,83-89`) |
| The 2026 roll is per ward (135 rows, MDB ids `798xxxxx`); `ward_parts(2026)` gives 1,059 VD-ward parts over 865 VDs with ward numbers `'1'…` | V (`archive/iec-registration-2026-09-26/`; probe `turnout.py`) |
| 6 of those parts (4,919 of 2,348,781 part-registration) have no 2021 VD record | V (probe `turnout.py`) |

## 1. Decisions (a writer cannot choose differently)

**D1. Ballot totals are a property of the state.** Each prediction's ward total
is Σ `ward_votes`, its list total Σ `list_votes`, both carried in `f`. Our
prediction states rule A's totals; a Phase 2 hand-off states its own (its
turnout levers move them). The schema carries no total: `x-total-votes` and
`x-share-sum` are deleted and nothing replaces them. `build_make.total_votes`
is retired. Reason: BRIEF change 7 says the hand-off carries the rule-A
prediction as `f`; a fixed total would force a rescale, and `decode(f)` would
then differ from A's object (G7). (A)

**D2. OTHER is appended to the vote codes.** `ctx.codes` stays the 74-party
roster (ward-callable). `ctx.voteCodes = [...codes, others]`, where `others`
is the schema's `x-others`, derived at build from the draws (the one `pr_share`
column not in `manifest.parties`; refuse unless exactly one). OTHER is a
pooled party: it can earn list seats, as in the draws (owner decision 2). It
can never be a ward winner. (A, follows S0 decision 2)

**D3. Whole votes everywhere; percent is display only.** The stored body, the
seat request and the scorer carry `{party: whole votes}` per ballot.

**D4. Validity (entry) = the seat law's refusals only.** Bounds from Amendment 1
are editor constraints, never validity: they are regenerated with data, and
enforcing them in `decode` would silently invalidate sealed links and our own
`f`. (A)

**D5. context_ref = `sha256(json([parties, wards, others]))[:12]`.** Nothing
else, so new bounds or a new roll snapshot do not break links.

**D6. FORMAT = "2"** (`make-state.js`), the one definition of the entry
version. `make_schema.mjs` imports it and writes `properties.v = {const:
FORMAT}`; Python reads `schema["properties"]["v"]["const"]`.

## 2. Changes, file by file

### 2.1 `interactive/js/make-state.js` (encoding; G7 encoding side)

`FORMAT = "2"`. Payload, base64url, no byte left over:

    k                       palette size, one byte (>=1)
    k indices into ctx.codes  (OTHER cannot be addressed: it is not in ctx.codes)
    ward calls              packed, ceil(log2 k) bits, schema ward order
    |voteCodes| varints     ward-ballot whole votes, voteCodes order (LEB128)
    |voteCodes| varints     list-ballot whole votes, same order
    m, m indices            coalition, into ctx.codes

- `encode(state, coalition, ctx)`; `state = {calls, ward: {code:int}, list: {code:int}}`.
- `decode(payload, ctx) -> {state, coalition}`; after parsing calls
  `B.invariantErrors(state, ctx)` and throws its first error.
- `sameState(a, b, ctx)`: calls and both vote maps over `ctx.voteCodes`.
- `serialize`, `parse` unchanged in shape; `parse` refuses `v !== "2"` with the
  existing "made by another version of this page" note (this is the accepted
  behaviour for old links, BRIEF 13).

### 2.2 `interactive/js/builder-state.js` (validity, editor, bounds)

`contextOf(schema)` returns `{codes, voteCodes, others, wards, noList,
model_ref, v, bounds}`; `T` is removed. `bounds = schema["x-editor-bounds"]`
(§2.9); `contextOf` throws if it is missing or its `e` keys are not exactly the
wards.

**Validity** `invariantErrors(state, ctx)` (decoder, builder, tests):
1. one winner per ward, each in `ctx.codes` (OTHER refused by name);
2. every value in both maps a non-negative safe integer, keys exactly `voteCodes`;
3. each ballot total >= 1;
4. **refusal R1:** a ward winner with 0 ward votes;
5. **refusal R2:** a ward winner not in `noList` with 0 list votes;
6. a `noList` party with list votes > 0.
No upper bound on totals (D1, D4).

**Editor bounds** (Amendment 1 point 2), all shares of the ballot total, computed
per call, O(wards):

    won_e[P]   = Σ_{w: calls[w]=P} e[w]                (e: the ward's share of expected ward votes)
    floor[P]   = max(q_win · won_e[P], P wins a ward ? 1 vote : 0)
    ceiling[P] = won_e[P] + q_run · (1 − won_e[P])     (noList: list ceiling 0; OTHER: won_e = 0)

In votes: `floorVotes = ceil(floor·T_ward)`, `ceilVotes = floor(ceiling·T_ward)`.
It treats wards independently and is a bound on the citywide ward vote, not a
seat count. Feasible always: Σ floor <= q_win <= 1 and Σ ceiling >= 1 for >= 3
codes. (A)

**List follows ward** (Amendment 1 point 1). Each party carries a gap
`g[P] = listShare[P] − wardShare[P]`, implicit in the state.
- `setWardPercent(state, ctx, code, pct)`: target clamped to `[floorVotes,
  ceilVotes]`; others rescaled by **bounded** largest remainder (`apportion`
  gains a `maxes` argument: water-filling that fixes any party past its min or
  max and repeats); then `listFollow`: each party's list share := its new ward
  share + its old gap, clamped to >= 0 (>= 1 vote for an R2 party), apportioned
  to the unchanged list total. Returns `{state, clamped: null|"floor"|"ceiling", which}`.
- `setListGap(state, ctx, code, points)`: clamps `points` to
  `[gap_min, gap_max]` (bounds), sets that party's list share, rescales the
  other parties' list shares in proportion; if any other party's resulting gap
  leaves `[gap_min, gap_max]`, the requested gap is reduced (bisection) to the
  largest feasible. `noList` parties have no gap control (list fixed at 0).
- `assignWards`, `setCalls`: change calls, then `clampToBounds(state)`: every
  party below its new floor raised, every party above its new ceiling lowered,
  others rescaled by bounded apportion; returns the moved codes for the page's
  note (replaces `raiseFloors`).
- `stateFromPrediction(ctx, pred)` (new; the ONE entry from a prediction
  object, used for the build block and the hand-off): `pred = {ward_calls,
  ward_votes, list_votes}`; `ward_calls` either a schema-ordered list or
  `{ward: code}`. Throws, naming the field, on: a missing ballot (`"the
  prediction has no list_votes"`), a missing or extra vote code, a missing ward,
  any `invariantErrors`. **No fallback calls, no even spread.**
- `outOfBounds(state, ctx) -> [{code, ballot, kind, have, bound}]`: the parties
  outside the editor bounds. Not an error.
- **Deleted:** `votesFromPercent`, `startState` (with its `fallbackCalls`),
  `percentOf` (replaced by `percentOf(state, ctx, ballot)`), `FLOOR_VOTES` as a
  standalone floor (it becomes the 1-vote term in `floor`), `forecastBody`
  (replaced by `entryBody`).
- `entryBody(state, ctx, {coalition, mayor, display_name})` returns exactly the
  keys `validate.js` accepts: `{v, model_ref, ward_calls, ward_votes,
  list_votes, coalition, mayor, display_name}`.
- `History` keeps `{calls, ward, list}`.

### 2.3 `interactive/js/make.js` (the editor; region `b-vote`, same writer contract)

- `start()`: `pubStart = MS.decode(D.start.f, ctx).state`, then assert
  `MS.sameState(pubStart, B.stateFromPrediction(ctx, D.start), ctx)` and throw
  if not (G7 page side).
- `handoffState(settings)`: `B.stateFromPrediction(ctx, await
  engineCall("handoff", {settings}))` (the `total` argument is gone; A owns the
  handoff's return shape, which is the prediction object).
- `follow()` (G8): the `catch` and the `refused` branch each write
  `one.followText` ("Your changes to the model could not be opened here: <why>.")
  and unhide `one.follow`; no bare `return` remains. A newer-ticket return stays
  silent (a newer setting is on its way).
- `buildVote()`: ONE row per vote code (roster alphabetical rules unchanged;
  OTHER last, named "Others"): ward-vote slider + percent box, and a collapsed
  "Adjust list vote" control per party with a pp stepper bounded by
  `[gap_min, gap_max]`. Header words per STYLE rule 11: "Ward vote %" and,
  inside the control, "List vote: ±x points from ward vote". `noList` rows show
  no list control and say "ward ballot only".
- A live line in `b-vote`, `.yf-totals`: "Ward ballot: N votes. List ballot: M
  votes." from the state's sums (the stated totals, BRIEF 13). Percent display
  uses each ballot's own total.
- Slider `min`/`max` attributes follow `floor`/`ceiling` after every edit, so
  the reader sees the range move as they paint.
- `one.floornote` texts: floor ("<Party> wins wards worth at least x% of the ward
  vote on your map"), ceiling ("<Party> cannot pass the winner in wards it does
  not win").
- Out-of-bounds note (point 4): when a state arrives from a link or a hand-off
  with `B.outOfBounds` non-empty, `one.linknote` says which party is outside the
  editor's range and that its next edit brings it inside. The state opens as is.
- `prmodel` ("Back to the start votes") restores `from.ward` and `from.list`.
- Every `B.percentOf(st, ctx)` passed as `vote:` to a card or `share:` to
  `analyse` becomes `B.percentOf(st, ctx, "list")` (key 3 and the card column are
  the list ballot). Every `B.forecastBody` becomes `B.entryBody`.
- `partyOf("OTHER")` returns `{name: "Others", colour: OTHERS_COLOUR}`
  (`share-card.js`'s constant), as `share-edge.js` `party()` does.

### 2.4 `interactive/your-forecast.html`

`b-vote`: the sub-line and `#note-vote` footnote rewritten for "ward vote, with
the list vote following it"; add `<p class="yf-totals yf-slot" role="status">`.
No build-time digit (number scan). Phase 2 renames the file; Phase 1 edits it in place.

### 2.5 `src/reader_seats.py`

    reader_seats(ward_votes: dict[str,int], list_votes: dict[str,int],
                 ward_winners: dict[str,str], context: dict) -> dict

- `context` gains `others` (code or `None`); `context_errors` checks it is not on
  `parties`.
- Refusals, each named: context errors; values not non-negative ints (bool
  refused); keys outside `parties ∪ {others}`; a ballot total of 0; list votes
  for a `no_pr_list` party; missing or unknown wards; a winner off the roster or
  equal to `others`; **R1** a winner with 0 ward votes; **R2** a winner not in
  `no_pr_list` with 0 list votes (G14: without it the statute moves its wards to
  D in silence).
- Then `pooled = eligible_parties(ward_votes, list_votes)` (the statute's own
  test on real arguments), reordered to `context["parties"] + [others]` (one
  deterministic order for allocate's exact-tie rule), `outside_pool_wards`,
  `allocate_with_overhang` as now.
- Returns as now, with `votes` replaced by `pool` (`{party: combined votes}`).
- **Deleted:** `combined_votes`, `_share_errors`, `total_votes`, `tolerance`.
  `ASSUMPTION` rewritten (two ballots, statute pool).
- Import closure unchanged, so `sync_seats_py.FILES` unchanged (V: imports at
  `reader_seats.py:92-95`).

### 2.6 Seat Worker and seam

- `worker-api/seats-py/src/entry.py`: `ARGUMENTS = ("ward_votes", "list_votes",
  "ward_winners", "context")`; docstring contract updated. `/v1/card` unchanged
  except it passes the new body through.
- `worker-api/src/seats.js`: `seatRequest(entry, schema)` returns `{ward_votes,
  list_votes, ward_winners, context}` (context = `x-seat-context` with `others`);
  `checkSeatAnswer` checks seat keys against `voteCodes` (OTHER may hold seats,
  never wards). `SeatsRefused` field becomes `"ward_votes"`.
- `worker-api/test/fake-seats.js`: new body.
- Re-copy: `sync_seats_py.mjs` and `interactive/tools/sync_py.mjs` (`--check`
  fires until both run). Deploy `joburg-seats` before the site Worker that sends
  the new body (order, §5).

### 2.7 `src/share-edge.js` (B's functions only)

- `decodeLink`: unchanged logic (FORMAT and context_ref read from MS/D).
- `ENTRY_COLUMNS` gains `"version"` (after `"forecast"`); `entryRow` binds
  `Number(MS.FORMAT)` and stores `JSON.stringify(B.entryBody(...))`; inside the
  row builder `validateForecast(body, D.forecast.schema)` must pass or the row
  fails (the seal is kept, as now).
- `cardAnswer`: `B.entryBody`, `seatRequest` new body; `cardFor`: `vote:
  B.percentOf(state, ctx, "list")`; `party("OTHER")` -> Others.
- C owns `storeEntry`, `cardImage`, `sealedPage` tags (G17, G18). Phase 2 owns
  `PAGE`.

### 2.8 `migrations/0002_entry_version.sql` (root, joburg-entries)

    ALTER TABLE entries ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

Existing rows read as version 1; the new Worker binds 2. Applied by the owner
(`npx wrangler d1 migrations apply joburg-entries --remote`) **before** the
new Worker is promoted (the old Worker's 7-column insert still works after it).

### 2.9 `src/build_make.py` and `worker-api/tools/make_schema.mjs`

- `model_artefact`: drops `total_votes`; adds `others` (D2) and `editor_bounds`
  (below). `make_schema.build`: deletes `x-total-votes`, `x-share-sum`,
  `combined_share`; adds `properties.v {const: FORMAT}` (imports
  `../../interactive/js/make-state.js`), `ward_votes`/`list_votes` objects keyed
  by vote codes (`integer`, `minimum 0`), `x-others`, `x-vote-codes`,
  `x-editor-bounds`, and `x-parties` gains `{code: OTHER, name: "Others"}`.
  `x-seat-context` gains `others`. Its CLI no longer writes
  `generated/forecast.schema.json` (§2.12); it writes `generated/geometry.json`
  only, and its `--model` default (the placeholder fixture) is deleted.
- `forecast_data()`: `context_ref` per D5. `start` = A's prediction object
  `{ward_calls, ward_votes, list_votes}` plus `f`, written by one node call that
  runs `make-state.encode` then `decode` and `B.outOfBounds`; the build refuses
  (`MakeBuildError`) unless `decode(f)` equals the object (calls and both maps),
  and records `start.out_of_bounds` (the list, possibly empty) as a reported
  fact. `total_votes_source` deleted.
- `editor_bounds(city, target) -> dict` (new), written as `x-editor-bounds`:

      e          {ward: share of expected ward votes}, Σ = 1
      q_win      lowest winning share of the ward vote, panel   (JUDGEMENT-CALLS)
      q_run      highest runner-up share of the ward vote, panel
      gap_min, gap_max   list% − ward% per party per city-year, panel extremes
      panel      [result file names], sources {path: sha256}, rules {name: sentence}

  - Expected ward votes `E[w] = roll_2026[w] × turnout[w]`. `roll` from the
    newest `archive/iec-registration-*/<city>_ward_registration_*.csv` (the
    snapshot `inputs_preflight` selects; refuse if none), MDB ids mapped through
    `score_forecasts.ward_number(id, city.ward_prefix)`. `turnout[w]` =
    registration-weighted mean over `montecarlo.ward_parts(target)`'s parts in
    `w` of the part's VD's ward-ballot turnout at the preceding LGE
    (`cityconfig.preceding(target, "LGE")`; valid ward votes / registered).
    Parts whose VD has no record there are left out of the mean (6 parts, 4,919
    voters, V); a ward with no part with a record refuses the build.
  - The panel: every cleaned metro LGE file `data/raw/elections/lge<year>_<CODE>_vd_party_clean.csv`
    with `year < target`. 40 city-years today (V, probe `bounds.py`).
  - One reader of the cleaned layout: `score_forecasts._read_rows` gains a
    fourth return value `vd_roll {vd: (ward, registered, ward_valid)}`;
    `ingest_result` ignores it. No new CSV reader.
- `baseline()`: adds `list_vote` (PR ballot percent) and `ward_vote` (Ward
  ballot percent) per party; the card's "vs 2021" uses `list_vote`, so a list
  percent is never compared with a combined one. `vote` (combined) is deleted.
  C's card reads `list_vote`.
- Docstring rewritten: start = prediction object, totals per state, bounds.

### 2.10 `src/score_forecasts.py`

- `seat_forecast(entry, schema)`: refuses `entry["v"] != schema["properties"]["v"]["const"]`
  with `"entry version <v> is not read by this scorer"`; then
  `reader_seats(ward_votes, list_votes, winners, context)`.
- `score()`: key 3 `f_points = 100 · list_votes[p] / Σ list_votes`. One helper
  `onto_codes(values, vote_codes, others)` maps the result onto the forecast's
  codes: each roster party keeps its own, every other certified party is summed
  into OTHER; used for the actual list share (key 3) and the actual seats (key 1)
  so the forecast's OTHER is compared with the result's off-roster mass, not with 0.
- `schema_context` returns `(context, ward_ids)`; share target and total gone.
- `ingest_result`: seats the result by `reader_seats(ward_total, pr_total,
  wards, context)` directly; the share round-trip check is deleted (nothing to
  round).
- `model_forecast`: **A deletes it** (replaced by `prediction.py`). B does not
  redefine it; B's docstring edits state that `score` reads the entry version 2
  fields.
- Module docstring: "What a forecast is" -> what an entry is (rule 11: an entry is
  a prediction).

### 2.11 `src/rank_entries.py`

- `load_export`: columns now include `version`.
- `rank_entries`: refuses every row whose `version` != the forecast.json schema's
  `v`, naming the seal ids (G12), before scoring.
- New subcommands (no new module, so `test_standalone_modules` is untouched):
  - `--export-version N --out-dir D`: runs `npx wrangler d1 execute
    joburg-entries --remote --json --command "SELECT <ENTRY_COLUMNS> FROM
    entries WHERE version = N ORDER BY seal_id"` (subprocess injectable), writes
    `D/entries-v<N>.json` and `D/EXPORT.json` = `{exported_at (UTC ISO),
    database_name, database_id (read from wrangler.toml [[d1_databases]]
    binding ENTRIES), query, columns, row_count, sha256}`; prints count, time,
    sha and id (G20).
  - `--clear-version N --export D --confirm <first 12 of sha256>`: re-reads
    `EXPORT.json`, re-hashes the data file, refuses on mismatch, on a missing
    confirm, or when a fresh `SELECT COUNT(*) … WHERE version = N` differs from
    `row_count`; then `DELETE FROM entries WHERE version = N`. The owner runs it,
    at the step he approves (BRIEF 13).
- Default `--out-dir`: `backups/entries-v1-<UTC date>/` (gitignored). See Q1.

### 2.12 `worker-api/src/validate.js` and the placeholder schema (G13)

- `validateForecast` reads version 2: keys exactly `v, model_ref, ward_calls,
  ward_votes, list_votes, coalition, mayor, display_name`; `v` must equal the
  schema const (`refuse("v", "made by another version of this page")`);
  vote maps keyed exactly by `x-vote-codes`, safe non-negative integers, each
  ballot total >= 1, R1, R2, noList list = 0. Rebuilds the value in roster order.
- **Retire `worker-api/generated/forecast.schema.json`** (owner decision 5 checked:
  the store is not in use). Every importer reads `build_make.forecast_data()`'s
  schema (built file `site/your-forecast/forecast.json`, path from one
  constant, which Phase 2 re-points): `worker-api/src/forecasts.js:3`,
  `worker-api/test/helpers.js:4`, `worker-api/test/node/consent-screen.test.js:14`,
  `interactive/tests/builder.test.mjs:31`, `tests/test_score_forecasts.py:55`,
  `interactive/js/common.js` `loadSchema` (prototype only).
- Dormant prototype modules that read `combined_share` and are not served
  (`interactive/js/f.js`, `api-stub.js`, `api.js` save path, `interactive/f/`):
  see Q3.

### 2.13 `docs-public/privacy.md`

"each party's vote" -> "each party's vote on the ward ballot and on the list
ballot", and "the version of the entry". `test_entries.PRIVACY_MUST` gains those
phrases.

### 2.14 Tools and fixtures

`interactive/tools/share_fixture.py`, `make_fixtures.py`,
`share_screenshots.mjs`, `yf_jump_check.mjs`, `interactive/tests/share-fixture.json`:
regenerated for version 2 bodies (`entryBody`, `stateFromPrediction`).

## 3. Records

- **MACHINERY.md**: the entry (prediction) shape and encoding v2; totals per
  state; the seat request; the editor bounds and list-follows-ward rule; the
  refusals; where each lives.
- **JUDGEMENT-CALLS.md**, new entries, each with status, evidence, how to check:
  1. **Panel scope for the editor bounds**: all metro LGE city-years before the
     target (alternative: the city's own). Evidence: probe numbers below.
  2. **`q_win`**: recommend the panel minimum (no real ward winner is outside the
     editor). Sensitivity: p01 would exclude 1% of 3,434 real winners, p05 5%.
  3. **`q_run`**: the panel maximum runner-up share.
  4. **`gap_min`, `gap_max`**: panel extremes of list% − ward% per party (pp).
  5. **Turnout source**: the preceding LGE's VD ward-ballot turnout, parts with no
     record left out of the ward mean.
  6. **Bounds are editor constraints, not validity** (D4).
- **MODEL-LOG.md** (append, dated; the measured values live here and in the
  generated `x-editor-bounds`, nowhere else):

  | probe (this session, 40 metro LGE city-years, 3,434 wards) | value |
  |---|---|
  | lowest winning ward share | 23.6% (JHB 2021 ward 82) |
  | winning share, 1st / 5th percentile | 35.1% / 43.7% |
  | highest runner-up share | 47.8% (NMA 2006) |
  | list% − ward%, all parties (766 party-city-years) | −1.76 to +6.16 pp |
  | same, Johannesburg, parties >= 1% of ward vote | −1.38 (DA 2021) to +4.14 (ActionSA 2021) pp |
  | 2026 ward turnout from 2021 VDs via ward_parts | 22.7% to 58.2%, median 41.9% |
  | our prediction inside the bounds | yes at min, p01 and p05: **approximate**, modal wards from `site/draws` and the mean LIST share standing in for the unexported ward share (probe `ours.py`); the real check is `start.out_of_bounds` once A lands |

  Plus: what was (one combined vote, fixed total, v1 entries) and what is, as the
  brief's no-compatibility rule requires.
- **Docstrings**: `reader_seats`, `seats.js`, `entry.py`, `validate.js`,
  `make-state.js`, `builder-state.js`, `make.js` header, `build_make`,
  `score_forecasts`, `rank_entries` (steps on results night now include the
  version filter and the export/clear commands).

## 4. Guards owned by slice B

Each: population stated and checked both ways, a constructed violation caught,
and quiet when reverted.

| guard | test (file) | population | constructed violation |
|---|---|---|---|
| **G7 (encoding)** | `test_your_forecast_page.py::test_the_start_is_decode_of_its_f` | `forecast_data().start`: 135 calls, both maps over `x-vote-codes` (keys equal both ways) | change one list vote in a copy of `start` -> caught; revert -> quiet |
| | `make.test.mjs` "the page opens on decode(start.f)" and "encode(decode(f)) is f, byte for byte" | `D.start.f`; random reachable states (`walk`) | flip one varint byte -> decode refuses or differs |
| | `make.test.mjs` "every consumer of start.f is declared" | a scan of `interactive/js`, `src`, `site` sources for `start.f` / `stateFromPrediction`: found set == `PREDICTION_CONSUMERS` (build block, page start; C adds card and sealed entry) | add a reference in a temp copy -> unlisted consumer named |
| **G8** | `make.test.mjs` "the hand-off arrives or says why" | `follow()`'s three branches (ok, refused, threw), stubbed `engineCall` | handoff missing `list_votes` -> `followText` names it and the state is unchanged; replace the status write with a bare `return` (source mutation) -> red |
| **G12** | `test_entries.py::test_the_table_holds_exactly_the_entry_columns_both_ways` (extended) | `migration_columns()` composes 0001's CREATE TABLE with every later `ALTER TABLE entries ADD COLUMN` in file order == `ENTRY_COLUMNS` | an ADD COLUMN not in `ENTRY_COLUMNS`; `ENTRY_COLUMNS` without `version` |
| | `test_rank_entries.py::test_a_row_of_another_version_is_refused_by_name` | every row of a constructed export | one row `version: 1` -> refusal names its seal id; all `2` -> ranks |
| | `test_score_forecasts.py::test_a_v1_body_is_refused_with_a_version_error` and `worker-api/test/validate.test.js` | `score`, `validateForecast` | a v1-shaped body (`combined_share`) -> version error, field `v` |
| **G13** | `test_site_structure.py::test_one_entry_schema` (or `test_your_forecast_page`) | every tracked file naming `forecast.schema.json` or importing a schema JSON: set == declared list (none outside `make_schema.mjs`'s `build` docs) | re-add the placeholder in a temp tree -> named |
| **G14** | `test_reader_seats.py::test_a_ward_winner_with_no_list_vote_is_refused` | `reader_seats` on a valid two-ballot input | set the winner's list votes to 0 -> refused naming it; mark it `no_pr_list` -> seated through D |
| | `builder.test.mjs` "R1 and R2: one vote seats a ward winner, zero is refused, on each ballot" | builder vs CPython `reader_seats` | at one vote seats; at zero refused, each ballot |
| **G15** | `test_score_forecasts.py::test_key_three_reads_only_the_list_ballot` | `score` on a constructed entry | move ward votes only -> `list_vote_error` unchanged (seats may move); move list votes -> changes |
| **G20** | `test_rank_entries.py::test_the_export_carries_time_count_sha_and_database` | `--export-version` with a fake runner | missing field, a sha that does not match the file, a clear with a stale count or no confirm -> refused |
| **Amendment 1, point 3** | `test_your_forecast_page.py::test_the_editor_bounds_are_regenerated_from_the_panel` | `x-editor-bounds.panel` == the glob of cleaned metro LGE files before the target (both ways); every recorded sha == the file; `e` keys == the schema wards | `editor_bounds` on a temp copy of the panel with one ward's winning share lowered below `q_win` -> `q_win` moves to it; one VD's registration changed -> `e` moves; one party's list votes changed -> a gap bound moves; each reverted -> equal to the served bounds |
| | `builder.test.mjs` "the bounds are read, not typed" | `builder-state.js` source | a numeric literal for a bound (constructed) -> found |

Blinded or replaced (their premise ends): `test_your_forecast_page` about lines
600-720 (`combined_share` sums, `x-total-votes`, handoff `share`; A replaces the
handoff ones), `test_reader_seats` items 5 (rounding) and the share-tolerance
test, `test_score_forecasts::test_the_model_forecast_is_*` (A),
`worker-api/test/validate.test.js` `combined_share` cases, `guards.test.js`
lines 24-35, `builder.test.mjs` lines 86-201. The reproduction test is
strengthened: each draw's captured `ward_totals_d` and `pr_totals_d` (wrap
`M.eligible_parties` instead of `allocate_with_overhang`) through the new
`reader_seats` give that draw's seats, wards, excessive set and council.

## 5. Tests that can see slice B

**Python** `run_all.py -k`: `reader_seats` (signature, closure, seat service),
`score_forecasts` (key 3, version, OTHER aggregation, ingest), `rank_entries`
(version, export/clear), `entries` (columns, privacy, edge row), `your_forecast_page`
(start, f, bounds, schema), `worker_routing` (its node snippet uses
`B.startState`, `test_worker_routing.py:815-816`), `share` (forecast.json
baseline), `served_draws` (forecast.json `draws_sha256`), `overhang` (names
`reader_seats` as a call site, `test_overhang.py:718-761`), `seats` (C/D note
at :389), `site_structure` (G13), `number_scan` and `site_assets` (template
change).

**Node, by file:** `interactive/tests/builder.test.mjs`, `make.test.mjs`,
`share.test.mjs`, `yf.test.mjs`, `page.test.mjs` (served copy), and
`worker-api` vitest: `validate.test.js`, `guards.test.js`, `render.test.js`,
`node/build.test.js`, `node/consent-screen.test.js`. Plus
`node worker-api/tools/sync_seats_py.mjs --check`, `node
interactive/tools/sync_py.mjs --check`, `interactive/tools/yf_jump_check.mjs`.

**Whole-suite exception: no.** B touches neither `montecarlo.py` nor `seats.py`,
and `reader_seats.py` is not in `run_model`'s import closure. `score_forecasts`
and `build_make` are imported by the page and the build, whose importers are
listed above. (A)

## 6. Order and dependencies

- **Before B:** slice A's prediction function and its object (with OTHER), the
  per-draw ballot totals, `build_make.start_state` and `page.handoff` returning
  the object. B cannot build `forecast.json` until A's export exists.
- **Q2 decides who lands the `reader_seats` signature** (it must exist when A's
  function seats).
- **B hands C:** `B.entryBody`, `stateFromPrediction`, `percentOf(…,"list")`,
  `PREDICTION_CONSUMERS` (C adds card and sealed entry), `baseline.list_vote`,
  the `version` column and the scorer's version check for `rank_entries`' ledger work.
- **Files shared:** `build_make.py` (A: start; B: schema, context_ref, bounds,
  baseline, f), `score_forecasts.py` (A deletes `model_forecast`; B the rest),
  `share-edge.js` (B: `ENTRY_COLUMNS`, `entryRow`, `cardAnswer`, `cardFor`; C:
  `storeEntry`, `cardImage`), `make.js` and `make-state.js` (B encodes; C reads),
  `rank_entries.py` (B: version, export; C: ledger), `page.py` (A only;
  `analyse` receives list percent unchanged in shape).
- **Release order:** apply `0002` -> deploy `joburg-seats` (new body) -> promote
  the site Worker -> `--export-version 1` -> owner approves -> `--clear-version 1`.
  A reverse order makes every seal-time insert or card call fail (inserts fail
  silently under today's `storeEntry`).

## 7. Point 4: the note case, and the refusals

- With floors and ceilings from the painted map, the builder cannot produce
  "130 wards on 5% of the ward vote" or a zero-vote winner. The "allowed with a
  note" case **disappears for the builder**.
- It survives for states the builder did not make: a link, a hand-off, our
  prediction if `start.out_of_bounds` is non-empty, or any state after the bounds
  are regenerated. These open with a note naming the party and the bound; the
  next edit of that party clamps it.
- Refusals are unchanged and live in the seat law and validity only: R1, R2, plus
  the structural ones (§2.2). Bounds never refuse.
- Trade-off: a reader cannot express a ward win below `q_win`, or a list gap
  outside the panel's. With the minimum and the extremes recommended, no outcome
  in the 40 city-years is excluded.

## 8. Open questions for the coordinator

1. **The D1 export cannot be committed as is.** The repository is public and the
   rows hold reader-typed names; `privacy.md` says entries live at Cloudflare and
   are deleted at ninety days. Recommend: the data file in gitignored
   `backups/`, `EXPORT.json` (time, count, sha, database id) committed. BRIEF 13
   says "a file in the repository": owner to decide.
2. **Who lands the `reader_seats` two-ballot signature.** Recommend A seats its
   prediction through `reader_seats` (so "re-seats exactly under reader_seats"
   holds by construction) and therefore lands §2.5 first; otherwise A calls the
   primitives in the order `parties + [OTHER]` and B's test proves equality.
3. **Dormant prototype modules** (`f.js`, `api-stub.js`, `api.js` save path,
   `interactive/f/`, `common.js loadAll`) read `combined_share` and the
   placeholder model; none is served. Retire them with the placeholder, or
   leave them declared stale. Recommend retire (no consumer).
4. **OTHER earns seats as one pooled party.** Owner decision 2, but a bloc of
   fragments can cross a quota no fragment would. A's G4 records it; the reader's
   "Others" row inherits it.
5. **`gap` bounds in points bind big parties, not small ones.** A 0.5% party may
   move by the full −1.8/+6.2 pp. A ratio bound would bind smaller parties; the
   owner and coordinator framed the gap in points, so the spec uses points.
6. **Independents** are ward-only through `no_pr_list`; the 2026 roster has
   `no_pr_list: []` (V, `build_make.py:145`), so the mechanism is ready and not
   exercised. The certified roster is §4b's.
7. **Production entry count** unverified (permission denied); the export prints it.

## 9. Estimate

Two and a half days for one writer: encoding and builder with bounded
apportion and bounds (1), seat law, Worker seam, validator, schema retirement,
scorer and rank/export (1), page editor, records and guards (0.5). Diff review
and targeted tests on top.
