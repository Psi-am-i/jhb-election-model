# S1 slice C: our sealed prediction and `/forecast` (specification)

Designer C, 2026-10-08. Read-only; host Atlas (`hostname -s`). Each claim is marked
**V** (verified: file:line or a command run this session) or **A** (argued).

## 0. Facts the design rests on

| # | fact | V/A |
|---|---|---|
| F1 | Only the live Worker can seal: `seal()` answers 503 without `SEAL_KEY` and 403 on a preview (`src/share-edge.js:382-403`, `seal`). | V |
| F2 | The entry is inserted after the 200 is answered (`ctx.waitUntil(stored)`), so a read immediately after the seal can find no row. | V (`share-edge.js:396-397`) |
| F3 | `n` is inside the signature (`seal.js` `sealMessage`, `SEALED_KEYS = ["v","c","f","n"]`). | V |
| F4 | `cardName` returns `""` for "the model", "official", "whysoserious" (`worker-api/src/blocklist.js:9-11`, `interactive/js/play-state.js:77-82`), and `seal()` refuses a non-empty name `cardName` changes (400). | V |
| F5 | D1 holds no column marking ours; `rank_entries` scores every row (`src/rank_entries.py` `rank_entries`). | V |
| F6 | `storeEntry` failures are `console.error` only (Workers Logs: seven days). Analytics Engine is bound (`ARRIVALS`, `joburg_arrivals`) and keeps three months (`wrangler.toml:70-95`). | V |
| F7 | `cardImage`'s `catch {}` returns 302 `/og.png` and writes nothing. The fallback test asserts `not r["logs"]` and `not r["points"]`, not `errors` (`tests/test_worker_routing.py:917-946`). | V |
| F8 | The single simulation is drawn in three places, all chosen by `scenarios.typical` (`src/scenarios.py:228`): the "two ballots" strip (`src/render_sheet.py:903-972`, `__BALLOTS__` region of both `forecast-sheet.html` and `drafts/forecast-draft.html`, `PAGES` at `render_sheet.py:432`); the map's council inset and its caption sentence (`src/render_map.py:344-372`, `:399-400`). `hex_cartogram.py` draws no inset (`:425` is a label only). | V |
| F9 | `scenarios.typical` has no other caller (`git grep "typical("`). Once both callers go, `test_regressions.test_no_top_level_function_is_defined_and_never_used` fires (its `ALLOWED` is empty, `tests/test_regressions.py:560-575`). `test_scenarios.py` has no test of it. | V |
| F10 | Four live tokens leave with the strip, not three: `ballots.typical.draw`, `.anc_wards`, `.anc_list` and `ballots.p_anc_excessive`, all with `superseded_at = null` in `publications/joburg/ledger.jsonl` (scan run this session). `ballots.p_anc_excessive` duplicates `tile.p_anc_excessive` on the same page (`forecast-sheet.html:217`). | V |
| F11 | `build_site` refuses a published token that leaves the registry and the pages unretired, with no escape flag (`src/build_site.py:1308-1340`); only `publication.retire` sets `superseded_at` (`src/publication.py:829-878`), and it requires `change_class ∈ CHANGE_CLASSES = (recompute, data_revision, mechanism, bugfix)` (`publication.py:95`). | V |
| F12 | `publication.history` reads exactly `publications/<city>/ledger.jsonl` (`publication.py:276-290`), so `seals.jsonl` beside it is not read as publication rows. The path is not gitignored (`git check-ignore` rc=1). | V |
| F13 | `build_all` runs `render_map`, then `render_sheet`, then `build_site` (`src/build_all.py:90-101`); `build_make.forecast_data` runs inside `build_site` after `forecast.html` is rendered (`build_site.py:1135-1180`). So nothing rendered into `forecast-sheet.html` can read the build's `forecast.json`. | V |
| F15 | The four tokens' first rows are ledger lines 39-42 and 358-361, inside the first 665 rows the UAT scratch ledger keeps (`docs/DEPLOY-UAT.md:108-110`); a retirement appended to the real ledger (now 1763 lines) is after row 665, so the scratch copy would hold the tokens unretired and a UAT build without the strip would refuse (F11). | V (`grep -n`, `wc -l`) |
| F16 | `forecast.json` carries no make-state format field today (keys: `model_ref, election, context_ref, draws_sha256, total_votes_source, schema, geometry, start, baseline`), and Python cannot import `make-state.js`. | V |
| F14 | The working tree is dirty on `forecast-sheet.html`, `drafts/forecast-draft.html`, `site/claims.html`, `site/css/site.css`, `content/joburg/NUMBERS-REVIEW.md` (claims copy edits, not in the regions this slice edits) and has an untracked `audits/2026-10-07-stamp-design/`. | V (`git diff --stat`) |

## 1. Changes, file by file

### 1.1 New `src/seal_ours.py`: the manual seal, its ledger, and the card check

Module docstring states: the command, when to run it (when the owner is happy with
the live prediction, after promote, after any D1 clear), the ledger schema below,
and that the ledger is the only thing that marks a seal as ours. It holds its own
CLI command lines (the `diagnose.py` precedent, CLAUDE.md §5): `rank_entries`
imports it, so it needs no `ENTRY_POINTS` entry and must not get one
(`test_the_allowlist_exempts_nothing_that_is_already_imported`). **A**

Constants:

    LEDGER = "seals.jsonl"                 # publications/<slug>/seals.jsonl
    LEDGER_SCHEMA = 1
    LEDGER_KEYS = ("schema", "seal_id", "sealed_at", "model_ref", "draws_sha256",
                   "context_ref", "v", "f", "build_commit")
    OUR_LABEL = ""                         # the `n` our seal carries (F3, F4)
    READBACK_TRIES, READBACK_WAIT_S = 6, 2  # F2: bounded retry, then refuse

`build_commit` is one field beyond the brief's list: the most recent commit whose
committed `site/<YF_DIR>/forecast.json` is byte-identical to the live one (step 3 below). It is
what makes `model_ref` resolvable when `model_ref` ends in `-dirty`. Owner to accept
or drop (Q4). **A**

Pure functions (no I/O; the guards test these offline):

    parse_seal(s: str) -> tuple[str, int]
        "<t base36>.<sig 43 chars>" -> (seal_id=sig, sealed_at=int(t, 36)).
        Refuses (ValueError) anything checkSeal's regex would refuse
        (`^([0-9a-z]{1,9})\.([A-Za-z0-9_-]{43})$`).

    seal_body(live: dict) -> dict
        {"v": <make-state FORMAT as live forecast.json declares it (slice B names
        the field)>, "c": live["context_ref"], "f": live["start"][<B's field for f>],
        "n": OUR_LABEL}. Refuses if f is missing or empty.

    row_problems(d1_row: dict, body: dict, live: dict, seal_id: str, sealed_at: int) -> list[str]
        Every difference between the D1 row read back and what was sealed:
        seal_id, sealed_at, label == OUR_LABEL, model_ref == live["model_ref"],
        context_ref == body["c"], state == body["f"], and (G7, seal side) the stored
        `forecast` JSON's ward_calls, ward_votes and list_votes equal live["start"]'s
        same three fields exactly (votes and calls, not seats). Field names per
        slice B; the comparison covers every field of the prediction object except
        seats. Empty list = agree.

    ledger_row(body, live, seal_id, sealed_at, build_commit) -> dict
        Exactly LEDGER_KEYS, in that order.

    load_seals(path) -> list[dict]
        Reads the ledger; refuses a line whose keys are not exactly LEDGER_KEYS, a
        schema other than LEDGER_SCHEMA, a repeated seal_id, or rows not in
        ascending sealed_at. Missing file -> [].

    card_url(host, row) -> str
        https://<host>/og/1/link.png?v=..&c=..&f=..&s=<base36(sealed_at)>.<seal_id>
        (n omitted: OUR_LABEL is empty, and share-edge `linkQuery` writes only keys
        present).

    ledger_d1_problems(seals: list[dict], rows: list[dict]) -> list[str]
        For every ledger row: a D1 row with its seal_id exists, and its sealed_at,
        label, model_ref, context_ref and state equal the ledger's (ledger f vs D1
        state). Returns one line per missing or differing seal, naming the seal_id
        and the field. This is the one definition `rank_entries` and `verify` use.

    ours_to_rank(seals, lock_iso: str) -> tuple[dict | None, list[dict]]
        (the last ledger row with sealed_at * 1000 < Date.parse(lock), the earlier
        ones). `lock_iso` is forecast.json `election.polls_open`.

I/O wrappers (thin; each takes its I/O as a parameter defaulting to the real one, so
tests pass fakes):

    fetch_live(host) -> (dict, bytes)      GET https://<host>/<YF_DIR>/<build_make.DATA>
    post_seal(host, body) -> str           POST https://<host>/seal/1; returns s; any
                                           status but 200 -> refuse with the status and
                                           the Worker's error text
    seal_check(host, body, s) -> dict      POST /seal/1/check; must answer
                                           sealed=true, before_polls=true, readable=true
    d1_row(seal_id) -> dict | None         env -u CLOUDFLARE_API_TOKEN npx wrangler d1
                                           execute joburg-entries --remote --json
                                           --command "SELECT <ENTRY_COLUMNS> FROM entries
                                           WHERE seal_id = '<seal_id>'"
                                           (seal_id is checked against parse_seal's
                                           alphabet first, so it is safe to interpolate;
                                           columns from rank_entries.entry_columns())
    d1_rows() -> list[dict]                the same, without WHERE (for verify)

The D1 auth is wrangler's OAuth login, exactly as `docs/DEPLOY-UAT.md` uses it; no
token appears in a file or a command (`~/CLAUDE.md` rule 4). **A**

Subcommands:

    seal [--host joburg.whysoserious.city] [--adopt S]
      1. Refuse unless publications/<slug>/seals.jsonl has no uncommitted change
         (git status --porcelain on that path).
      2. live, raw = fetch_live(host).
      3. build_commit = the most recent commit in
         `git log --format=%H -- site/<YF_DIR>/<DATA>` whose blob of that path
         equals raw byte for byte; refuse only if none does ("the live
         forecast.json is no committed build"). HEAD may have moved past the
         deployed commit (docs committed after promote), so HEAD is not required.
      4. body = seal_body(live). Unless --adopt: s = post_seal(host, body).
         With --adopt S: s = S (recovery when a previous run sealed but died
         before writing the ledger; S is printed by every run).
         Print s and card_url at once, before anything that can fail.
      5. seal_id, sealed_at = parse_seal(s). seal_check(...) must agree.
      6. d1 = d1_row(seal_id), retried READBACK_TRIES times READBACK_WAIT_S apart
         (F2). None after the last -> refuse: "sealed (s=...) but no D1 row after
         N tries; re-run with --adopt <s>".
      7. row_problems(d1, body, live, seal_id, sealed_at) must be empty, else refuse
         listing each.
      8. Refuse if seal_id is already in the ledger (a repeat in the same second
         gives the same seal_id: INSERT OR IGNORE).
      9. Append ledger_row(...) as one JSON line, then
         git commit -m "Seal our prediction <seal_id[:12]>" -- publications/<slug>/seals.jsonl
         (a pathspec commit: nothing else staged is committed).

    verify [--host ...]
      ledger_d1_problems(load_seals(...), d1_rows()) must be empty; prints one line
      per ledger seal. Run after any D1 clear (§1.6) and on results night.

    check-card [--host ...]       (G18)
      For the live start's link (v, c, f; unsealed) and, when the last ledger row's
      context_ref equals live context_ref, that row's card_url: GET without
      following redirects; each must answer 200, Content-Type image/png, a body
      starting with the PNG signature; the sealed one with
      Cache-Control "public, max-age=31536000, immutable" (share-edge imageCache(true)).
      A 302 to /og.png fails and prints "card fell back: see Workers Logs event=card".
      Both link.png and story.png.

### 1.2 `src/rank_entries.py`: ours by the ledger only

Signature change (keyword-only, no default, so no caller can forget it):

    rank_entries(rows, forecasts, result, *, seals: list[dict],
                 without_ours: bool = False, seat_source=None) -> dict

Behaviour, in order, before any scoring:

1. `problems = seal_ours.ledger_d1_problems(seals, rows)`; non-empty -> ValueError
   "the seal ledger and the D1 export disagree:" + each line. (Ledger -> D1 both
   ways on the fields; D1 -> ledger is not checkable: see Q6.)
2. If `seals` is empty and not `without_ours`: ValueError "no seal of ours in
   publications/<slug>/seals.jsonl; pass --without-ours to rank readers alone".
3. `ours, earlier = seal_ours.ours_to_rank(seals, lock)`, where `lock` is
   `forecasts[ours["context_ref"]]["election"]["polls_open"]`; refuse if that
   forecast.json is not given (the existing missing-context refusal covers it) or
   if `ours` is None while seals exist ("every seal of ours is after polls open").
4. The rows whose seal_id is in `{e["seal_id"] for e in earlier}` are removed
   before scoring: earlier versions of ours are not ranked (BRIEF change 3,
   "ranks one"). They are listed in the artefact, not silently dropped.
5. Scoring and order unchanged (`score_forecasts.score`, `.rank`). Ours is scored by
   the same `score()` as every reader.
6. Every output row gains `"ours": bool`, true on exactly the row of
   `ours["seal_id"]`. That row's `name` is `OURS_NAME` (a new module constant,
   wording owner's, Q3), never the D1 label.
7. The artefact gains
   `"ours": {"id": <seal_id[:ID_CHARS]>, "sealed_at": <iso>, "excluded": [<earlier ids[:ID_CHARS]>]}`
   or `null` with `without_ours`.

`main`: new `--seals PATH` (default `publications/<slug>/seals.jsonl`) and
`--without-ours`. `edit_board` (`--drop`, `--anonymise`): `--anonymise` leaves the
`ours` row's name as `OURS_NAME` (it is not a person's name); `--drop` of ours is
refused ("ours is not removed on request"). Docstring: the results-night steps gain
`seal_ours.py verify` before step 1 and the seal-count check (§1.4) after step 1.

`load_export`'s exact-column check is unchanged here; slice B changes
`ENTRY_COLUMNS` and its version column, and this slice's fixtures follow B's.

### 1.3 Removing the single simulation from `/forecast`

`src/render_sheet.py`:
- Delete the "two ballots" block: `bar`, `round_to_total`, the `seat_detail_draws.csv`
  read, `typical`, `anc_note`, `ballots_caption`, the assert, `strip`, and the write
  loop (`:880-972`). The `__BALLOTS__` region is replaced by the pointer (§1.5), so
  the write loop is replaced, not deleted: the same marker pair, now named
  `__PREDICTION_START__`/`__PREDICTION_END__`, written into each of `PAGES`.
  Refuse (SystemExit) if a page in `PAGES` still carries `__BALLOTS_START__` after
  the write, or carries neither marker.
- Remove the `p_excessive` lookup if nothing else in the function uses it (check
  at write time).

`forecast-sheet.html` and `drafts/forecast-draft.html`: the `__BALLOTS__` region
becomes an empty `__PREDICTION__` marker pair that `render_sheet` fills. (These two
files carry uncommitted edits, F14.)

`src/render_map.py`:
- Delete the council inset (`:344-372`: the `seat_draws.csv` read, `scenarios.typical`,
  the bar, the "The full council — N seats, one typical simulation" caption) and
  `{inset}` from the SVG; keep the "Ward races" label (move it out of `inset` into
  `labels`).
- Delete the caption sentence "The bar shows the whole council, ward and list seats
  together, in one typical simulation." (`:399-400`).
- `KEY_PARTIES` and `GREY`: delete if unused afterwards.

`src/scenarios.py`: delete `typical` (F9); remove "Used by the two ballots bars and
the map's council bar" wherever it is quoted.

`src/css/components.css`: delete `.ballots`, `.ballot`, `.ballot-h`, `.ballot-bar*`
and their comment. `src/css/page-sheet.css:76-79`: delete the `figcaption.ballots-note`
rule. `src/js/maps.js:14-15`: the comment drops "the council bar under the map and
the two-ballots strip". (No dead-selector test exists in `test_site_assets.py`: V by
its test list; the deletion is hygiene.)

**Tokens (F10, F11, F15).** All four are retired with `publication.retire("joburg", t,
reason=..., change_class="mechanism")` against the real ledger **by the writer, in
the same commit that removes the strip** (CLAUDE.md §2; the ledger is append-only,
and the tokens are off every page, so `dated_context_violations` cannot fire). The
S5 whole suite then sees them retired. The UAT scratch ledger must carry them too
(F15): `docs/DEPLOY-UAT.md`'s scratch rule changes from "the first 665 rows" to "the
first 665 rows, then every later row whose `superseded_at` is set" (retirements are
facts about what is current, not part of the edition being replayed). That also
carries the three existing retirement rows into UAT; coordinator to confirm (Q11).
Reasons:
- `ballots.typical.draw`, `.anc_wards`, `.anc_list`: "The two-ballots bars showed
  one simulation, which is not a forecast. They were removed from /forecast;
  our prediction replaces them."
- `ballots.p_anc_excessive`: "Shown only in the removed two-ballots caption; the
  same figure stays on /forecast as tile.p_anc_excessive."

`mechanism` is the nearest class but it is not a model change; Q2 asks whether to
add a class (a `publication.py` change, a shared helper) instead.

### 1.4 `src/share-edge.js`: durable seal outcomes (G17) and the card's reason (G18)

Functions touched: `storeEntry`, `seal`, `cardImage`, `cardFor`. (Slice B is likely
to touch `entryRow`, `ENTRY_COLUMNS`, `decodeLink`, `cardAnswer`, `cardFor`'s spec
call; this slice does not touch those lines except `cardFor`'s throws.)

**Seal outcomes.** New Analytics Engine binding `SEALS`, dataset `joburg_seals`, kept
apart from `ARRIVALS` so the arrival counts and their tests do not move. **A**

    export const SEAL_OUTCOMES = ["stored", "repeat", "no_binding", "row_failed", "insert_failed"];
    function sealPoint(env, host, outcome)   // one point: blobs [outcome, host], doubles [1], indexes ["seal"]
                                             // never throws; a failing binding is logged by reason

`storeEntry(env, makeRow, host)` writes exactly one point per call:
- no binding -> `no_binding` (and the existing console.error);
- row build throws -> `row_failed`;
- insert throws -> `insert_failed`;
- insert succeeds: `res.meta.changes === 1` -> `stored`; `0` -> `repeat`
  (INSERT OR IGNORE of a seal already stored); `meta` absent -> `insert_failed`
  with reason "no meta" logged (an answer that cannot prove a row is not counted as
  stored). **A** (D1's `run()` returns `meta.changes`: to be confirmed by the
  writer against Cloudflare's D1 docs before relying on it, Q7.)

`seal()` passes `url.host` to `storeEntry`. Nothing about the reader, the name or the
forecast is in a point.

Results-night identity (the runbook check, in `rank_entries`' docstring and
`docs/DEPLOY-UAT.md`): over the window since the last D1 clear,
`SUM stored` from `joburg_seals` (host = the live host) == D1 row count + rows
deleted on request since then; `SUM` of the three failure outcomes is reported, and
any non-zero is told to the owner before ranking. Pure helper in `rank_entries`:

    seal_count_problems(points: dict[str, int], d1_rows: int, deleted: int) -> list[str]

and `main --seal-counts <AE SQL JSON export> --deleted N` (scope beyond G17's stated
home, "share-edge.js + a runbook check": the coordinator may cut it to the runbook
check alone); with `--seal-counts`
given, non-empty problems refuse unless `--accept-seal-counts` is passed, and the
counts are written into the artefact under `"seal_counts"`. Without
`--seal-counts`, ranking refuses ("give the seal counts, or --no-seal-counts and
say why") so the check cannot be skipped by omission. **A**

**Card fallback reason.** `cardFor` throws a `CardError(reason)` (a small class,
exported) for each named failure: `no_forecast`, `no_seats_binding`,
`seats_status`, `seats_timeout`, `answer_incomplete`. `cardImage`'s catch becomes
`catch (e) { console.error({ event: "card", fallback: true, reason: e instanceof
CardError ? e.reason : "unexpected" }); return fallback(url); }`. The reason only:
no URL, name or forecast (the `_leaks` and write-nothing tests hold that).

`wrangler.toml`: a second `[[analytics_engine_datasets]]` (`SEALS`, `joburg_seals`)
with a comment saying what it holds, and the "change them together" pointer to
`docs-public/privacy.md`.

`docs-public/privacy.md` (same commit): under "The seal", one sentence: each seal
also writes one Analytics Engine data point holding whether the entry was stored,
repeated or failed, and the site's address; nothing about the person or the
forecast; deleted after three months.

### 1.5 The replacement pointer on `/forecast`

Written by `render_sheet` into `__PREDICTION__`, a short `<details class="rollup"
data-band="forecast" open>` block:

    <summary><span class="eyebrow">Our prediction</span><h2>One complete result</h2></summary>
    <p>Our forecast is how often each outcome happens. Our prediction is the one
    complete result we commit to: a winner in every ward and a seat count for every
    party, adding up to {{council_size}}. It gives
    <party> {{@prediction.seats.<code>=N;int;<source>}} seats, ... (every party it
    seats, in seat order).
    <a href="<YF_HREF>#break">See it ward by ward</a>.</p>

- Rule 11: labelled prediction; single numbers; no range; no vote percentage, so no
  ballot to name. The wording is the owner's to approve (Q3).
- Every party the prediction seats, or none (memory: no party singled out). Token
  per party `prediction.seats.<code lower>`, source
  `"our prediction (<function>), site/draws sha <draws_sha256[:12]>"`.
- `href` from `build_your_forecast.YF_HREF`, never typed, so Phase 2's path move
  carries it.
- **Where the figures come from (F13).** `render_sheet` cannot read the build's
  forecast.json. It calls the one prediction function on `site/draws/`, the same
  input the build reads. Slice A must expose a function returning the prediction
  object with its derived seats from the draws directory without the node schema
  step; this slice asks for `build_make.our_prediction(draws=DRAWS) -> dict`, which
  `build_make.start_state` also uses. If A's design cannot, `render_sheet` imports
  A's function directly and joins G1's declared caller list (Q1).
- Risk accepted and stated: when a party's predicted seats fall to zero its token
  leaves the page, and the next build refuses until it is retired (F11). Figure-free
  pointer (a sentence and the link, no tokens) is the fallback if the owner prefers
  no retirement chore (Q3).

### 1.6 Documents that change in step with the code

- `docs/DEPLOY-UAT.md` step 4: `.venv/bin/python src/seal_ours.py check-card`
  after every promote (G18). "Entries at launch": the clear runs before our seal;
  after any clear, run `seal_ours.py verify`; a ledger seal missing from D1 is
  resealed (and the old ledger line stays, since `rank_entries` uses the last one
  before the lock). Slice B's export-then-clear step gets the same note.
- `wrangler.toml` ENTRIES note: same ordering sentence.
- `CLAUDE.md`: nothing (no number, no new rule).

## 2. Records (CLAUDE.md §2)

| file | entry |
|---|---|
| `JUDGEMENT-CALLS.md` | **New:** "Our prediction is sealed by hand and the last seal before polls open is scored": manual, owner's timing; earlier seals of ours are excluded from the board and listed; `OUR_LABEL = ""` and `OURS_NAME` with why (F3, F4); status: decided 2026-10-08; how to check: `test_rank_entries` G16 tests. **New:** "A seal outcome is counted in Analytics Engine, not D1" (a D1 failure cannot be counted in D1); the results-night identity. `READBACK_TRIES`/`READBACK_WAIT_S` declared as unmeasured operational constants if `test_every_tunable_constant_is_in_the_judgement_register` reaches `src/seal_ours.py` (check at write time). |
| `MACHINERY.md` | `seal_ours` (command, ledger schema, the read-back and its retry, verify, check-card); `rank_entries` ours rule; the seal-outcome points; the card fallback reasons; `/forecast` carries no single simulation, and the pointer's source. |
| `MODEL-LOG.md` (append) | What was: `/forecast` showed simulation 1622 (strip and map inset) chosen by `scenarios.typical`; what is now: the pointer to our prediction; the decision (BRIEF change 4); the four retired tokens with their reasons. No model number moves; the draws are untouched by this slice. |
| docstrings | `seal_ours` (whole module); `rank_entries` module docstring (ours, results-night steps); `share-edge.js` header (ENTRIES paragraph: the outcome point; the image paragraph: the reason logged); `render_sheet`/`render_map` comments on the removed blocks deleted, not left describing code that is gone; `scenarios` module docstring line 16 if it names `typical`. |

## 3. Guards owned

Each: population, both directions where bidirectional, a constructed violation
caught and quiet when reverted.

**G7 (card and seal side)** — `tests/test_entries.py::test_our_prediction_is_stored_as_the_build_states_it`
and `tests/test_worker_routing.py::test_our_card_draws_the_build_s_prediction`.
- Population: the real built `site/<YF_DIR>/forecast.json` (`W._share_setup`); its
  `start` f; the prediction object's fields minus seats (ward_calls, ward_votes,
  list_votes). Assert the field set compared equals the object's field set minus
  `seats` (so a sixth field added by B joins or fails).
- Seal side: seal `start.f` with `n=""` through the real worker and fake D1; the
  stored row's `forecast` fields equal `start`'s. Card side: `cardFor` with a fake
  SEATS on the `start` link; the spec's calls equal `start.ward_calls` and its vote
  rows are the ones decoded from f (per B's card fields).
- Violation: an override of `share-edge.js` that reverses `ward_calls` in `entryRow`
  / in `cardFor`'s spec input -> caught; reverted -> quiet.
- Fifth consumer (the pointer): `tests/test_site_structure.py::test_the_forecast_pointer_is_our_prediction`:
  every `prediction.seats.*` token on built `forecast.html` equals `start`'s derived
  seats, and the set of parties equals `{p: seats[p] > 0}` both ways. Violation: a
  copy of the page with one token's value changed, and one with a party dropped ->
  caught.
- `seal_ours.row_problems` covers the same equality at run time against live data;
  unit test with a fake row differing in each compared field, one at a time.

**G11** — `tests/test_site_structure.py::test_forecast_carries_no_single_simulation`.
- Population: built `site/forecast.html` and the sources `forecast-sheet.html`,
  `drafts/forecast-draft.html`; assert the built page has > 0 tokens and its
  `published` rows from `statlib.render` are the population scanned.
- Asserts: no `__BALLOTS_START__`, no `ballot-bar`, no `ballots-note`, no
  "typical simulation"; no token on the page whose source matches
  `r"simulation \d+"` (a figure drawn from one draw); `scenarios` has no `typical`
  attribute; the four tokens of F10 are retired in `publication.latest("joburg")`
  with a non-empty reason (retired in the writer's commit, so green from then on).
- Violation: insert the old strip snippet (from git `HEAD~` of render_sheet output,
  constructed inline) and, separately, a token `{{@x=1;int;seat_detail_draws.csv,
  simulation 7}}` -> each caught; reverted -> quiet.
- Pointer reads the prediction: G7's fifth-consumer test above.

**G16** — `tests/test_rank_entries.py`:
- `test_ours_is_marked_by_the_ledger_alone`: rows include one labelled `OURS_NAME`
  by a reader (not in the ledger) and ours (in the ledger, label ""); exactly one
  row has `ours: true`, and it is the ledger's. Violation: a variant of the rule
  that marks by label -> caught.
- `test_only_the_last_seal_before_polls_open_is_ranked`: three ledger seals, the
  third after `polls_open`; the board ranks the second, lists the first in
  `ours.excluded`, and the third refuses as "after polls open" if it is the only
  one. Assert the board's row count == D1 rows − excluded (both ways: no excluded
  seal on the board, every other row on it).
- `test_ledger_and_d1_disagreement_refuses`: a ledger seal missing from the export;
  a ledger f differing from the D1 state; a differing context_ref, model_ref,
  sealed_at, label -> each refused naming the seal_id and field; the agreeing
  ledger -> quiet.
- `test_no_seal_of_ours_refuses_unless_said`: empty ledger refuses;
  `without_ours=True` ranks; `ours` is null in the artefact.
- `seal_ours.load_seals` refusals (keys, schema, repeat, order) in
  `tests/test_rank_entries.py` too (one module tests the ledger's reader and its
  user).

**G17** — `tests/test_entries.py::test_every_seal_outcome_writes_one_point`:
- Population: every case of `entry_problems` (stored, repeat, refused, throw, no
  binding) plus a fake D1 answering without `meta`; assert one SEALS point per
  call of storeEntry and none for a refused seal (refusals never reach storeEntry),
  outcome per case as listed in §1.4, blobs exactly `[outcome, host]`.
- The fake D1 in `test_worker_routing.DRIVER` returns `{success: true, meta:
  {changes: 1|0}}`, and the driver gains a `SEALS` recorder (`sealPoints`, separate
  from `points`) with "absent"/"throw" modes like ARRIVALS.
- Violations: storeEntry writing `stored` on an ignored insert; writing nothing on
  `insert_failed`; a point carrying the label -> each caught.
- `seal_count_problems`: unit test, constructed counts (equal, short by one, a
  failure present) in `tests/test_rank_entries.py`.
- Privacy: `privacy_problems` gains the outcome-point sentence; the existing
  mutate-and-catch pattern extended with its removal.

**G18** — `tests/test_worker_routing.py::test_the_image_asks_the_seat_worker_and_falls_back_to_the_generic_image`
extended: each of its five fallback cases also asserts `errors == [{"event":
"card", "fallback": True, "reason": <the case's reason>}]`; the 200 case (a fake
SEATS returning a complete answer, added) asserts `errors == []`. Violation: an
override with the old bare `catch {}` -> caught. `seal_ours.check-card`'s decision
(`card_problems(status, headers, body)`) unit-tested on a 302, a 200 text/html, a
200 PNG with the short cache header for a sealed link, and a good answer.

**G19** — `tests/test_site_structure.py::test_nothing_on_forecast_posts_to_seal`:
- Population: built `forecast.html` and every script it loads, enumerated by the
  same reader `statlib.script_writes` uses; assert the count enumerated equals the
  page's `<script src>` count and is > 0.
- Asserts: no `seal/1` in the page or any of those scripts; no import of
  `share-sheet.js`.
- Violation: a copy of `maps.js` with `fetch("seal/1")` appended, and a copy of the
  page with a `<script src="your-forecast/js/share-sheet.js">` -> each caught.

## 4. The test list

    .venv/bin/python tests/run_all.py -k entries -k rank_entries -k worker_routing \
        -k site_structure -k scenarios -k regressions -k standalone_modules \
        -k publication_ledger -k published_page -k site_assets -k number_scan \
        -k model_index -k register_matches_code -k hex_cartogram -k map_stripes
    node --test interactive/tests/share.test.mjs interactive/tests/yf.test.mjs

| module | why it sees this slice |
|---|---|
| entries | storeEntry, seal outcomes, privacy page, G7 seal side, G17 |
| rank_entries | rank_entries, seal_ours ledger, G16, seal counts |
| worker_routing | share-edge routes, card fallback (G18), fake D1/SEALS driver, G7 card side; its no-data-point test must stay green with SEALS kept apart |
| site_structure | G11, G19, the pointer (G7 fifth consumer) |
| scenarios | `scenarios` loses `typical` |
| regressions | the unused-function test (F9) |
| standalone_modules | `seal_ours` is imported by `rank_entries`, so it must not be in `ENTRY_POINTS` |
| publication_ledger | four retirements |
| published_page | "what this tree builds today" fires until the site is rebuilt and committed; the live-figure check sees the new tokens |
| site_assets, number_scan | the page, its CSS and the pointer's tokens |
| model_index, register_matches_code | new public constants in `src/` (`seal_ours`, `rank_entries.OURS_NAME`, `SEAL_OUTCOMES` is JS). Regenerate `src/model_index.py` before the run (QC.md §4) |
| hex_cartogram, map_stripes | `render_map` edited around them |
| share.test.mjs, yf.test.mjs | import `share-edge.js` / the page modules |

**Existing fixtures C moves:** every `test_rank_entries` call of `rank_entries`
(`_board` and the refusal tests) passes `seals=[], without_ours=True`, and the
forecast fixture `{CTX: {"schema", "context_ref"}}` gains `election.polls_open`;
`test_entries.entry_problems` and `seal_problems` stop asserting "no points" for
`SEALS` (they keep it for `ARRIVALS`) and assert the outcome points instead;
`test_worker_routing`'s fallback test asserts the `errors` reasons. Re-recorded
deliberately, said in the commit message.

**Whole-suite exception: none.** This slice changes no `src/montecarlo.py`, no file
`run_model` imports, and none of `stats.py`, `build_site.py`, `seats.py` (FLOW.md).
`render_sheet`/`render_map` are scripts with no importer in the model path. The
pointer is kept out of `build_site` for that reason (§1.5). **A** (importers of
`render_sheet`/`render_map` not exhaustively listed; `git grep "import render_sheet"`
at write time.)

## 5. Order and dependencies

- **Before C:** slice A (the prediction function, the `start` block with derived
  seats, `build_make.our_prediction` or equivalent) and slice B (`f` in `start`, the
  make-state FORMAT, `ENTRY_COLUMNS` and the entry version, the stored `forecast`
  shape, the card's vote fields). C's G7 tests compare against A's and B's field
  names. **Hard hand-off from B (F16): B writes the make-state format version into
  `forecast.json` as a field the Python seal reads; without it `seal_ours` cannot
  build the `/seal/1` body.**
- **C hands on:** the ledger and `seal_ours` for Phase 2's path move (`YF_DIR`,
  `DATA` constants, not literals); `ours: true` on board rows for Phase 3's
  leaderboard styling; `OURS_NAME` wording for Phase 3's words pass; the card check
  for Phase 3's prediction card (whose title for an empty `n` is Phase 3's).
- **Shared files:** `src/share-edge.js` (B: `entryRow`, `ENTRY_COLUMNS`,
  `decodeLink`, `cardAnswer`, `cardFor`'s spec call; C: `storeEntry`, `seal`'s
  `storeEntry` call, `cardImage`, `cardFor`'s throws); `tests/test_entries.py`,
  `tests/test_worker_routing.py`, `tests/test_rank_entries.py` (B changes fixtures
  for the new version); `src/build_make.py` (A owns; C only calls);
  `forecast-sheet.html`, `drafts/forecast-draft.html` (dirty, F14); `wrangler.toml`
  and `docs/DEPLOY-UAT.md` (B: the export-then-clear note).
- **Owner steps C creates:** the UAT scratch ledger built by the new rule (Q11); the first
  `seal_ours.py seal` after promote and after the launch clear; `check-card` after
  every promote.

## 6. Risks and open questions

| # | question / risk | recommendation |
|---|---|---|
| Q1 | The pointer needs the prediction from `site/draws/` without `forecast.json` (F13). | A exposes `build_make.our_prediction`; else `render_sheet` joins G1's caller list. |
| Q2 | No `change_class` fits "removed by decision". | Use `mechanism` with the reason; adding a class touches `publication.py` (a shared helper, possible whole-suite trigger). |
| Q3 | Pointer wording, per-party figures (retirement chore when a party drops to zero seats) or figure-free; `OURS_NAME` wording on the board. | Per-party, every seated party; owner approves words. |
| Q4 | `build_commit` in the ledger beyond the brief's fields. | Keep: it resolves a `-dirty` `model_ref`. |
| Q5 | Our seal carries `n=""`; a reader opening our prediction and sharing unnamed seals the same `f` unnamed. Same second -> same seal_id (INSERT OR IGNORE): the reader's copy is absorbed into ours. | Accept; negligible. |
| Q6 | D1 -> ledger is not checkable: a seal of ours made through the page, or a run that died before the ledger write and was never adopted, is indistinguishable from a reader's anonymous entry. | Accept; `--adopt` and the printed `s` cover the crash case. |
| Q7 | `meta.changes` on D1 `run()` must be confirmed against Cloudflare's D1 docs before `repeat` vs `stored` relies on it. | Writer confirms with a cited URL in the share-edge comment, or drops `repeat` and counts calls. |
| Q8 | Any D1 clear (launch, slice B's export-then-clear, a reader's deletion of ours is refused) after our seal makes `rank_entries` refuse until resealed. | Intended; runbook orders the clear before the seal. |
| Q9 | The working tree is dirty on two files this slice edits (F14). | Coordinator reconciles before the writer starts (QC.md §3). |
| Q11 | The UAT scratch-ledger rule changes to carry retirement rows (F15). | Accept; the alternative is retiring in the scratch copy by hand at every UAT build. |
| Q12 | Owner-facing decisions the brief does not make: our seal's empty label and the board name `OURS_NAME`; earlier seals of ours excluded from the board and listed under `ours.excluded`. | Owner confirms both; recorded in JUDGEMENT-CALLS. |
| Q10 | A UAT build cannot exercise the seal, the read-back, `verify` or `check-card` (previews refuse `/seal/1`; D1 is live). | Unit-test the pure functions offline; the live run is an owner step. |

**Estimate:** one writer-day: `seal_ours` and its tests half a day; `rank_entries`
and G16 two hours; the `/forecast` removal, pointer and G11/G19 two hours;
share-edge G17/G18 with the driver changes two hours; records and the runbook an
hour. Plus the owner's live steps (seal, verify, check-card), under an hour.
