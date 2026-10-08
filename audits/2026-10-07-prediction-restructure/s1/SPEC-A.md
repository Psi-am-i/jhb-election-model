# S1 slice A specification: rule A and both ballots in the draws

Designer A, 2026-10-08. Read-only; nothing in the repository was edited. Probes
ran in-process with outputs only under `/Users/simondavis/.claude/jobs/26965cd4/tmp/s1-a/`
(scripts in `scripts/`, the prototype function in `proto/prediction.py`).
Tree at HEAD `0398232`, host Atlas.

## 0. Measurements this spec rests on

| # | finding | status |
|---|---|---|
| M1 | The live tree reproduces the served draws: a 5,000-draw `run_model` at joburg 2026, seed 20261104, gives ward winners equal to `site/draws/base.bin`'s `ward_winner` block in every cell. | verified, `scripts/probe_run.py` + `scripts/analyse.py` |
| M2 | Universe == schema roster == served `parties`: 74 codes, alphabetical. The served `OTHER` column of `pr_share` is 0.0 in every draw (mean 0.0, max 0.0) and `seats/deduct` OTHER max is 0. There is no mass outside the roster in the live draws. | verified (manifest + unpack; probe `roster==universe True`) |
| M3 | No ward has a tied modal count at the published seed and draws (5,000). | verified, `analyse.py` "tied wards (probe): []" |
| M4 | Rebuilding whole votes as `round(share x total)` misses the integers `run_model` hands `eligible_parties` by up to 4 votes in 1.6-2.0% of cells, even from unrounded shares and the integer row total (200 draws: 399 ward cells, 330 list cells differ). From the served 1e-5-step shares it is worse. Two scalar totals per draw therefore cannot make G2 an equality. | verified, inline probe on `run200.pkl` |
| M5 | `eligible_parties -> outside_pool_wards -> allocate_with_overhang` on a draw's recorded integers and winners reproduces `run.seat_draws[d]`: 0 mismatches in 200 sampled draws of 5,000. | verified, `analyse.py` |
| M6 | Rule A (prototype) on joburg 2026, 5,000 draws: ANC 70 (all ward seats; item 16 fires, ANC excess 11), DA 65, ASA 28, EFF 26, PA 24, MK 23, then 17 parties on 1-4. Ward calls ANC 70, DA 44, PA 10, MK 9, EFF 2 (identical to today's start). Ballot totals: ward 984,627, list 984,630 (sum 1,969,257; `x-total-votes` is 1,986,759). Today's start (`start_rule`) gives ANC 70, DA 66, ASA 27, EFF 25, PA 23, MK 22, SACP 5, ... | verified, `analyse.py`; old start from `site/your-forecast/forecast.json` |
| M7 | Exact integer mean with round-half-to-even equals `int(round(float(np.mean(...))))` for every party at 5,000 draws (0 differences). | verified, `analyse.py` |
| M8 | The prototype reproduces §1.290's row joburg 2021 exactly (A seats dict and ward wins equal to `backtest/results/joburg-2021.json`), with the ENTRANT relabel applied after the rule and before the seat law. | verified, `scripts/repro_one.py` |
| M9 | Interim re-seat: the rule-A votes summed per party as a combined share, seated by today's `reader_seats` at total 1,969,257 and at 1,986,759, give exactly the rule-A seats. | verified, inline probe |
| M10 | Served file gzip: today 855,507 bytes. Plus a whole-vote ward block and list block (uint32, column-major as `reweight.pack` writes): 1,700,229, over `BUDGET_GZIP_BYTES` = 1,500,000 (`tests/test_export_draws.py:72`). With `pr_share` dropped: 1,419,546. | verified, inline probe (real 5,000-draw integers) |
| M11 | A 4th modal-call site exists: `montecarlo.main` writes `ward_winner_probs.csv`'s `winner` as `order[0]` of `np.argsort(-ward_winner_counts[wi])` (`montecarlo.py:5595`), default (unstable) sort. S0 listed three. | verified, read |
| M12 | `montecarlo.py` is in the seat Worker's copied closure (`worker-api/tools/sync_seats_py.mjs` FILES), so any edit to it stales `worker-api/seats-py/src/` and its `code_ref.py`. | verified, read |
| M13 | `render_home.py:147` reads the served `pr_share` block for the published token `home.overhang_list_share`. | verified, read |

S0 finding 3 ("`run_model` keeps OTHER in the quota pool") is not what the code
does: `run_model` has no OTHER party; `OTHER` is `export_draws.build`'s sum of
the universe parties that never take a seat, and it is empty at joburg 2026
(M2). The owner's decision "OTHER kept in the pool as the simulations have it"
is implemented here as: every universe party enters the pool under its own
code, exactly as in the draw; nothing is summed before the seat law and
nothing is dropped. "Others" is a display grouping only. (argued from M2, M5)

## 1. Changes, file by file

### 1.1 `src/montecarlo.py`: two recorded fields, nothing else

Only these edits. The draw loop, `allocate_with_overhang`, `main` and every
random call are untouched (that is what keeps FLOW's whole-suite exemption,
§4).

- `ModelRun`: two fields after `ward_share_draws`:

      pr_vote_draws: np.ndarray | None = None    # (draws, parties) int64
      ward_vote_draws: np.ndarray | None = None  # (draws, parties) int64

  Comment: the whole votes per ballot per draw that the seat law read
  (`eligible_parties`'s two arguments), columns in `universe` order; recorded
  from values already computed, so they change no draw.
- `run_model`, beside the share arrays: `pr_vote_draws = np.zeros((draws, npar), dtype=np.int64)`, same for `ward_vote_draws`.
- In the loop, immediately after `pr_totals_d` is built (`montecarlo.py:5226`),
  and from those dicts, not recomputed:

      ward_vote_draws[d] = [ward_totals_d[universe[i]] for i in range(npar)]
      pr_vote_draws[d] = [pr_totals_d[universe[i]] for i in range(npar)]

- Trace: after `43_ward_share_draws` (`:5331`):

      trace.put("42a_pr_vote_draws", pr_vote_draws, detail=True)
      trace.put("43a_ward_vote_draws", ward_vote_draws, detail=True)

  (`42a_` sorts after `42_`; nothing parses stage numbers, checked by grep.)
- Return both in `ModelRun(...)`.
- Docstrings: `ModelRun` (the field comment above), `run_model` (names the two
  recorded fields and the test that proves they move nothing).

### 1.2 `src/prediction.py` (new): rule A, one definition

Top-level imports: `math`, `numpy` only. It goes into the page (PAGE_FILES) and,
through `reader_seats`, the seat Worker, so it must not import `montecarlo` at
module level.

    class RuleAError(ValueError): the draws cannot give a prediction; the message says why.

    def ward_calls(ward_winners, ward_parties, wards, weights=None) -> dict[str, str]

`ward_winners` is `(draws, wards)` of indices into `ward_parties`. For each
ward: the (weighted) count of draws each party wins it,
`np.bincount(col, weights=weights, minlength=len(ward_parties))`; the call is
the party with the largest count; **a tie goes to the party code first in
Python string order** (`min` over the tied codes), independent of the order of
`ward_parties` or of any array. With unit weights counts are integers and a
tie is exact. With weights a tie is exact float equality of the two weighted
sums (same arithmetic for both, so deterministic; stated in the docstring).
Returns `{str(ward): party}`.

    def mean_votes(votes, columns, weights=None) -> dict[str, int]

`votes` is `(draws, len(columns))` of integers; refused (RuleAError naming the
argument) if not 2-D, wrong width, not an integer dtype, or any negative.
Unit weights (`weights is None`, or every weight equal, which is what the
page's untouched setting passes: `reweight.uniform` returns `np.ones(n)`):
exact integer arithmetic, `S = votes.sum(axis=0)` as Python ints,
`whole = round_half_even(S / n)` computed by `divmod` (no float). The same
test routes `ward_calls` to integer counts. So the build (no weights) and the
hand-off at the published setting (uniform weights) take one arithmetic path
by construction. Other weights:
`float(w @ votes[:, j]) / w.sum()`, then Python `round` (half to even). Every
column is kept, zero included, in `columns` order.

    def rule_a(ward_winners, ward_parties, wards, ward_votes, list_votes,
               columns, *, weights=None, ward_ids=None) -> dict

Returns the prediction object

    {"ward_calls": [party, ...],          # in ward_ids order (default: wards)
     "ward_votes": {party: int},          # every column
     "list_votes": {party: int}}

Refusals (RuleAError, by name; G3): `ward_votes` or `list_votes` is None or
missing ("the draws carry no list_vote block"); either fails `mean_votes`'
checks; the two arrays are equal in every cell ("one ballot is a copy of the
other"); `ward_ids` is not a permutation of `wards`; `weights` not finite,
negative, wrong length or summing to zero; a call names a party absent from
`columns` (a ward winner the vote blocks do not carry). No seats in the
object: seats are derived (`seats_of`), never stored as an input.

    def seats_of(prediction, council: int, *, order=None) -> dict

The one composition of the seat law outside `run_model`'s loop. Lazily imports
`montecarlo as M` and `seats`. Counts wins from `ward_calls`;
`pooled = eligible_parties(ward_votes, list_votes)`; `combined` re-keyed in
`order` (default: the key order of `list_votes`) so an exact remainder tie
falls the same way every call (today's `reader_seats` rule);
`outside_pool_wards`; `M.COUNCIL` set to `council` around
`M.allocate_with_overhang(combined, pool_wins, M.STATUTORY_VALUES["overhang_rule"], ...)`
and restored in `finally` (moved here from `reader_seats`, so it exists once).
Returns `reader_seats`' result shape: `{"seats": {p: {"ward","pr","total"}},
"council", "majority", "excessive", "excessive_fired", "independent_wards",
"no_pr_list_wards", "pool": [codes in combined]}`. Raises `ValueError` /
`RuntimeError` from the law unchanged; callers decide.

Module docstring: the rule in three reader sentences (each ward to the party
that wins it in the most simulations; each party's mean ward-ballot and mean
list-ballot whole votes; seats by the law from those), the tie rule, the
rounding, "no party is summed or dropped", and pointers to JUDGEMENT-CALLS §Q
and MODEL-LOG §1.290.

### 1.3 `src/reader_seats.py`: delegate the composition (no behaviour change)

`reader_seats` keeps its signature and every refusal. After validation and
`combined_votes`, it calls
`prediction.seats_of({"ward_calls": [ward_winners[w] for w in wards], "ward_votes": {}, "list_votes": votes}, context["council"], order=list(votes))`,
maps a raised `ValueError`/`RuntimeError` to its existing error text,
**keeps `import montecarlo as M` and `from seats import ...` at module level**
with a comment saying why (the seat Worker's FILES are held equal to
`reader_seats`' import closure measured in a fresh interpreter,
`tests/test_reader_seats.py`; `prediction.seats_of` imports `montecarlo`
lazily because `prediction.py` also ships to the page, so without the
top-level import the measured closure would lose `montecarlo`, `seats`,
`coalitions`, `fold`, `polling`, the test would ask for them to be dropped
from FILES, and the Worker would ship without the seat law), keeps the
"dropped" check (now `pool` against `votes`), and adds `votes`/`assumption`.
The inline `eligible_parties` / `outside_pool_wards` / `M.COUNCIL` /
`allocate_with_overhang` block (`reader_seats.py:~318-360`) is deleted. Its
module docstring's "It calls the project's seat law" list points at
`prediction.seats_of`. Slice B then changes the signature to two ballots on
top of this. `prediction.py` joins `sync_seats_py.mjs` FILES (closure test, §4;
§1.13) and the copy is re-synced.

Why A does this rather than leaving it to B: otherwise two compositions exist
between the slices, the one thing the coupling warning forbids. (argued)

### 1.4 `src/export_draws.py`

- `_run_law` returns `"ward_votes": np.asarray(run.ward_vote_draws)` and
  `"list_votes": np.asarray(run.pr_vote_draws)`.
- `shared_draw_differences`: add `"ward_votes", "list_votes"` to the per-draw
  keys compared across laws (they are drawn before the law).
- `build`: after `ward_winner`,

      blocks.append(("ward_vote", W.astype(_uint(W)), universe))
      blocks.append(("list_vote", L.astype(_uint(L)), universe))

  Columns are the run's **whole universe**, every party under its own code,
  none summed into OTHER (§0, G4). Delete the `pr_share` block (decision D-A1
  below) and `PR_SHARE_STEP`.
- Delete `COMBINED_SHARE_REFUSAL` and the manifest key `combined_share`. Add a
  manifest field `vote_blocks`:
  `{"unit": "whole votes", "columns": "the run's universe; no party summed or dropped", "source": "ModelRun.ward_vote_draws and pr_vote_draws: the integers run_model's seat law read", "combined": "seats.eligible_parties(ward_vote, list_vote) per draw; not stored"}`.
- New predicate `ballot_faults(manifest) -> list[str]` (G5): complaints when a
  vote block is missing, has a non-integer dtype, or its columns differ from
  the other's; when `combined_share` is present alongside the blocks ("lifted
  and refused at once"); or when it is absent without both blocks.
  `build` calls it on its own output and raises `SystemExit` on any complaint.
- Module docstring: the block list, "What the export asserts", the
  `combined_share` bullet replaced by the lift, "Storage choices" (votes:
  narrowest unsigned integer, exact; no stepped block remains).

### 1.5 `src/reweight.py`

- New `list_shares(list_votes) -> np.ndarray`: `votes / votes.sum(axis=1, keepdims=True)`; refuses (`Refused`) a draw with no list vote. One definition of "list share from the draw file".
- `poll_weights` docstring: `shares` is `list_shares(arrays["list_vote"])`, columns the `list_vote` block's.
- `reweight.py` is in the seat Worker's CARD_FILES: re-sync (§1.13).

### 1.6 `src/score_forecasts.py`

`model_forecast` is replaced (same name, new signature):

    def model_forecast(ward_winners, ward_parties, wards, ward_votes, list_votes,
                       columns, schema: dict) -> dict

It calls `prediction.rule_a(..., ward_ids=schema x-ward-ids)`; refuses, naming
them, any column with votes > 0 off the schema roster and any roster party
missing from `columns` (today's refusal, kept); returns

    {"model_ref": None, "ward_calls": [...], "ward_votes": {...},
     "list_votes": {...}, "outside_roster": {"ward": 0, "list": 0},
     "combined_share": {p: (w+l)/(W+L) * x-share-sum.target},   # INTERIM, B deletes
     "coalition": [], "mayor": None, "display_name": None}

`outside_roster` is the rule-A vote on columns off the roster, per ballot
(always 0 when it returns, since a positive value is refused; it is recorded so
G4's "mass per ballot" is a field, not an inference). Delete `import
statistics` if unused. Module docstring: replace "The model is scored as a
reader who saved the model's central state untouched ... MEDIAN combined share"
with the rule-A text and a pointer to `prediction.py`; say the function holds a
*prediction* (STYLE rule 11).

### 1.7 `src/build_make.py`

- `start_state(manifest, arrays, schema)`: reads blocks `ward_winner`,
  `ward_vote`, `list_vote` by name; a missing one raises
  `MakeBuildError("build_make: the draw file carries no <name> block")` (G3).
  Calls `score_forecasts.model_forecast(arrays["ward_winner"], manifest["ward_parties"], wards, arrays["ward_vote"], arrays["list_vote"], columns, schema)`;
  `seated = prediction.seats_of(pred, context["council"], order=roster)`.
  Interim check (kept until B): `reader_seats(combined_share/target, calls,
  context, total)` must give the same totals as `seated`, else
  `MakeBuildError` (M9 says it does today).
  Returns `{"ward_calls", "ward_votes", "list_votes", "seats": {p: total},
  "combined_share" (INTERIM), "published_middle": {} (INTERIM, B deletes with
  make.js' note), "rule": "rule A: src/prediction.py"}`.
- Delete `start_plan` and `import start_rule`.
- `total_votes` and `x-total-votes` unchanged in A (B decides the ballot totals;
  §5 hand-off).
- Module docstring "The start state, stated exactly": rewritten to rule A.

### 1.8 `interactive/pyboot/page.py`

- `import prediction as P`; delete `import start_rule`.
- `_ward_calls(cell, w)`: `winner` for every ward comes from
  `P.ward_calls(winners, codes, wards, w)` (one tie rule for `compute`'s map and
  the hand-off). `dist`, `bands` and the `hit` membership stay as they are;
  `RM.ward_call(ward, winner, probs[j, codes.index(winner)], dist)`.
- `handoff(request_json)`: request `{"settings": ...}` (`total` accepted and
  ignored). After the weights, read blocks `ward_vote` and `list_vote`
  (missing -> `{"refused": "the draw file carries no list_vote block"}`, G3),
  call `P.rule_a(winners, codes, wards, wv, lv, cols, weights=w)`; a
  `RuleAError` -> `{"refused": str(exc)}`. Return
  `{"ward_calls": {ward: party}, "ward_votes": {...}, "list_votes": {...},
  "share": {p: (w+l)/(W+L)*100}}` (`share` INTERIM for `make.js` until B). No
  `seats`, no `middle`: the page seats through the seat Worker.
- `_weights` (poll path, `page.py:164-175`) and `analyse` (`:522`): replace
  `pr_share` with `R.list_shares(arrays["list_vote"])` and the `list_vote`
  block's columns. In `analyse`, `points` keeps the reader's shares on the
  list-vote columns; a reader party not in those columns is refused
  (`ValueError`), and the `OTHER` sum is deleted (no lumped column exists).
- Module docstring: the hand-off paragraph.

### 1.9 `src/render_home.py`

`:147` reads `R.list_shares(blocks["list_vote"])[:, cols["list_vote"].index(party)]`;
docstring (`:125`) and the token source string (`:276`, and the matching
`home.html` token text) say `site/draws list_vote`. The value moves by at most
half the old step (5e-6, argued); display unchanged. The build's ledger may ask
for a reason for the changed source: "the list vote is now read as whole votes;
it was a share stored to 1e-5".

### 1.10 Retired: `src/start_rule.py`

Deleted with its references: `sync_py.mjs` PAGE_FILES and its comment;
`build_make`, `page.py`; docstrings/comments in `build_your_forecast.py:17`,
`interactive/README.md:134`, `interactive/js/play-share.js:12`; `make.js:33,
192, 714` comments (B's file: listed in the hand-off). `scenarios.py` stays in
PAGE_FILES only if `page.py`'s closure still imports it (start_rule was its
importer per the comment): the PAGE_FILES both-ways test decides.

### 1.11 `interactive/tools/sync_py.mjs`

PAGE_FILES: `+ "prediction.py"`, `- "start_rule.py"`, `scenarios.py` per §1.10.
Re-run it; commit `interactive/py/page/`.

### 1.12 `audits/2026-10-07-prediction-restructure/backtest/rule_a.py` (new)

`one.py` stays as the record of how §1.290 ran. `rule_a.py <city> <year>
<out.json>`: same set-up as `one.py`, no `eligible_parties` monkeypatch;
`pred = prediction.rule_a(run.ward_winner_draws, run.universe, run.wards,
run.ward_vote_draws, run.pr_vote_draws, run.universe)`; ENTRANT relabel
applied to `pred` (calls and both vote dicts, summing collisions) after the
rule and before `seats_of(pred, M.COUNCIL)`, as `one.py` effectively did (M8);
writes the A block in `one.py`'s keys. `compare_rule_a.py <results> <new>`
diffs `A.seats`, `A.ward_wins`, `A.seat_err`, `A.wards_ok`,
`A.ward_vote_err_pp`, `A.list_vote_err_pp`, `A.excessive` for all 24 and exits
1 on any difference, then prints the A columns of `TABLE.txt`. Acceptance: 24
of 24 identical. About 24 minutes of `run_model` (1,000 draws each).

### 1.13 Served artefacts, in-slice

- Re-export the three cells (`export_draws.py --out <scratch>` per cell, then
  `--index`) and commit to `site/draws/`; `test_served_draws` is red until then.
  `draws_sha256` and `model_sha256` change: record old and new (MODEL-LOG).
- `node worker-api/tools/sync_seats_py.mjs` (montecarlo.py, reader_seats.py,
  reweight.py, new prediction.py) and commit the copy and `code_ref.py`. The
  seat Worker is not deployed in A.
- `.venv/bin/python src/model_index.py` (COMBINED_SHARE_REFUSAL and
  PR_SHARE_STEP leave the register; prediction.py's names join).

## 2. Records (same commit)

- **MACHINERY.md**: replace "Where a reader's own forecast opens — `src/start_rule.py`" (`:1997`) with "Our prediction — `src/prediction.py`" (rule A, tie rule, rounding, `seats_of` as the one composition, callers). Update the export section (`:1914`: blocks `ward_vote`/`list_vote`, `pr_share` gone, refusal lifted), the `score_forecasts` bullet (`:2146`), `run_model`'s recorded fields, and the trace stage list.
- **JUDGEMENT-CALLS.md**, new `## Q. Added 2026-10-08 — reducing the forecast to our prediction`:
  - §Q1 rule A itself, ⚖️ owner's choice (2026-10-08), evidence MODEL-LOG §1.290, what it cannot test (excessive seats: no past city-year had any; 2026 rule A fires item 16 for the ANC, M6). Replaces the start rule (record the retirement here: seat-first targets at the panel middles, raised to the ward floor).
  - §Q2 the tie rule (first code in string order), 🔴 typed; how to check: count tied wards at each published run (zero at joburg 2026, M3).
  - §Q3 whole votes by round-half-to-even of the mean, 🔴 typed, moves at most one vote per party.
  - §Q4 nothing summed, nothing dropped: every universe party in the pool under its own code; off-roster mass refused, recorded as `outside_roster`. With the G4 toy as the evidence that summing would seat differently.
  - Add rows to the "Named constants"/rules table if the register's guard requires them (it will say).
  - §M1 (`:249`, `:2945`) mentions "the start state's combined total": add "see §Q" (B rewrites §M1).
- **MODEL-LOG.md**, new `## 1.29x Our prediction from one function; both ballots in the draws (2026-10-xx)`: what was (start_rule; combined-share refusal; `pr_share` at 1e-5; four modal-call sites with three tie rules, M11), what is, and the decision. Measurements the writer pastes from runs: §1.290 table reproduced 24/24; the recording moved no draw (§3's one-off proof); the new and old `draws_sha256`/`model_sha256`; gzip size; the 2026 rule-A prediction against today's start, party by party (M6 is the probe's preview); rule-A ballot totals against `x-total-votes`.
- **Docstrings**: every file in §1 as listed there; `skills/forecast-stage-realisation/SKILL.md` gains the two stages' field inventory; QC.md §3's "maintained by hand" paragraph is replaced by the pointer to the new coverage test (G6).

## 3. Guards owned (G1-G6)

Each: population checked both ways, a constructed violation caught and quiet
when reverted.

**G1** `tests/test_prediction_rule.py` (new).
- `test_rule_a_has_one_definition_and_its_importers_are_declared`: AST-scan every `src/*.py` and `interactive/pyboot/page.py` for imports of `prediction`. `DECLARED_IMPORTERS = {"score_forecasts", "build_make", "reader_seats", "page"}`; assert found == declared (both directions); `scanned(files, of=len(glob src/*.py)+1, low=1.0, high=1.0)`. Constructed: a temp module importing `prediction` is reported; removed, quiet.
- `test_no_modal_or_mean_reduction_over_draws_outside_prediction`: in every function of the same population, flag (a) `argmax`/`argsort`/`bincount`/`max` calls whose source text names `ward_winner` or `winners`, (b) `mean`/`median`/`sum(axis=0)` whose source names `ward_vote`, `list_vote`, `pr_vote_draws` or `ward_vote_draws`. `EXEMPT = {(file, function): reason}`, populated by the writer from the first scan's output, each with a reason (expected among them: `montecarlo.main`, the forecast map's `winner`, M11 and Q3; `page._ward_calls`' `hit`, dist membership). Nothing is pre-listed that the rule does not flag. Register->code: an exemption matching no site fails. Constructed: a source string with `ward_winner_counts.argmax(axis=1)` inside a fake function is flagged; removed, quiet.
- `test_a_tied_ward_resolves_one_way_through_build_handoff_compute_and_scorer`: constructed draws, 4 draws x 2 wards, ward 1 tied 2-2 between `ZED` and `ABC`, with `ward_parties = ["ZED", "ABC"]` (so an order-based rule would pick ZED). Through `prediction.rule_a`, `score_forecasts.model_forecast`, `build_make.start_state` (constructed manifest/arrays/schema) and `page.handoff` + `page.compute` (constructed cell): every one calls `ABC`. Control: assert `ward_parties[0] == "ZED"` and that `np.argmax` on the counts gives ZED, so the test distinguishes the rules.
- `test_rule_a_whole_votes_are_the_exact_mean`: constructed integer block whose column means fall exactly on x.5 (2.5 -> 2, 3.5 -> 4) and off it; half-to-even asserted. Control: a constructed half-up rounding gives 3 for 2.5, so the test separates the two.

**G2** `tests/test_export_draws.py` and `tests/test_served_draws.py`.
- `test_export_draws::test_the_vote_blocks_are_run_model_s_integers_and_rule_a_agrees`: in-process `E._run_law("deduct", "joburg", "2026", 40, published seed)`; `E.build({"deduct": r})`; unpack. Assert `ward_vote`/`list_vote` equal `r["ward_votes"]`/`r["list_votes"]` cell for cell; `rule_a` on unpacked == `rule_a` on in-process (calls, both vote dicts); `set(eligible_parties(...))` equal; `seats_of` equal. Constructed: the served list block with two columns swapped -> rule-A votes differ, caught; reverted, quiet. `_run_law` exits unless `PYTHONHASHSEED == "0"`, which `run_all.py` sets; under bare pytest the test skips loudly, naming the seed.
- `test_chain::test_the_seat_law_on_recorded_votes_is_every_draw_s_council` (or in `test_prediction_rule`): joburg 2021, 20 draws; for every draw, `seats_of` on that draw's recorded votes and winners equals `run.seat_draws[d]`. Constructed: one party's list votes zeroed in one draw -> mismatch.
- `test_served_draws::test_every_cell_carries_both_ballot_blocks`: population = `index.json` cells (check 4 already holds both directions); each manifest passes `E.ballot_faults` with no complaint; both blocks integer, row sums > 0, columns identical across cells. Constructed (in memory): a manifest with `list_vote` removed, and one with `combined_share` re-added, are each caught and quiet when reverted.
- Existing tests in these modules rewritten for the new blocks: `_constructed_runs` gains `ward_votes`/`list_votes`; `test_the_build_puts_every_seat_winner...` asserts the vote blocks keep `Z` under its own code; `test_shares_and_turnouts...` loses the `pr_share` step check and gains the integer check; `test_the_manifest_centres_are_the_trace_s_and_combined_share_is_refused` -> `..._and_combined_share_is_lifted`.

**G3** `prediction.rule_a` with `list_votes=None`, and with `list_votes is ward_votes`, raise `RuleAError` naming the cause (`test_prediction_rule`); `page.handoff` on a constructed cell whose manifest lacks `list_vote` returns `{"refused": ...list_vote...}` (`tests/test_your_forecast_page.py` and the node fixture in `interactive/tests/page.test.mjs`); `build_make.start_state` without `ward_vote` raises `MakeBuildError` naming it.

**G4** `tests/test_prediction_rule.py::test_no_party_is_summed_and_summing_would_seat_differently`: toy council of 10 seats, 5 wards; parties A, B and six minor parties each under a quota whose sum is over one. `rule_a` keeps all eight columns; `seats_of` gives the minors 0. The same votes with the minors summed into one `OTHER` column give OTHER a seat: the test asserts the two councils differ (it can see). `tests/test_score_forecasts.py::test_model_forecast_records_outside_roster_mass_and_refuses_it`: `outside_roster == {"ward": 0, "list": 0}` on a roster-matched case; a column off the roster with votes > 0 is refused naming it; with 0 votes it is accepted.

**G5** `tests/test_export_draws.py::test_the_combined_share_refusal_is_lifted_and_never_both`: the export's manifest has no `combined_share` and both blocks; `E.ballot_faults` on (refusal + blocks) and on (no refusal, one block) each complain; the clean manifest does not.

**G6** lands first, in this order:
1. `tests/test_stage_realisation.py`: `ALL_PREDICATES` (every `faults_*`), `CORRUPTIONS` (predicate -> constructed broken payload, lifted from the existing per-test pairs), and `test_every_predicate_has_a_constructed_violation`, both directions plus `scanned(..., low, high)` against the healthy payloads' field count, as `test_stage_estimation.py:1647`. QC.md §3 updated: the "maintained by hand" paragraph and the inline stage list (`QC.md:65-67`) with the two new stages.
2. New predicates `faults_in_vote_matrix(payload, name, draws, parties)` (2-D, integer, non-negative, row sums > 0) and `faults_between_votes_and_shares(votes, shares)` (|votes/rowsum - share| <= parties/rowsum per cell), each registered with a constructed violation; `test_the_realisation_segment_emits_every_stage_it_claims_to` adds `42a_pr_vote_draws`, `43a_ward_vote_draws`; `test_a_real_trace_passes_every_predicate_in_this_file` runs them.
3. `tests/test_chain.py::test_passing_a_run_directory_changes_no_drawn_number`: the loop covers `("pr_share_draws", "ward_share_draws", "pr_vote_draws", "ward_vote_draws")`.

**One-off proof that recording moved no draw (MODEL-LOG, not a test):** as
`test_draw_record.py` check 1 did in its window: the pre-change commit
(`git archive` to scratch) and the changed tree at joburg 2026, published
seed, 200 draws, each in its own interpreter under `HASH_SEED`; every `*draws`
field equal and the only new fields the two vote arrays. `test_draw_record`'s
live checks then cover the new fields automatically (it compares every
`*draws` attribute).

## 4. Test list

`.venv/bin/python tests/run_all.py -k <module>` for each of:

| module | why it can see A |
|---|---|
| `prediction_rule` (new) | G1, G3, G4 |
| `chain` | no-perturb loop, seat law per draw |
| `stage_realisation` | G6 coverage, new stages |
| `draw_record` | compares every `*draws` field of `ModelRun` |
| `export_draws` | G2, G5, blocks, budget (slow: four models) |
| `served_draws` | re-exported cells, G2 |
| `score_forecasts` | `model_forecast` rewritten, G4 record |
| `reader_seats` | delegation to `seats_of`; closure test with `prediction.py` |
| `your_forecast_page` | start and hand-off tests rewritten (`test_the_start_is...`, `test_the_hand_off_is...`), `analyse` on list votes |
| `reweight` | `list_shares`; `poll_weights` on list votes (`test_reweight.py:275-279`) |
| `home_page`, `published_page` | `home.overhang_list_share` source |
| `regressions` | `PR_SHARE_STEP` named at `:825-830` |
| `entries`, `rank_entries` | import `score_forecasts`; seat a stored forecast |
| `worker_routing` | `:816` reads `D.start.combined_share` (interim key kept) |
| `model_index` | after regeneration |

Node, by file: `interactive/tests/page.test.mjs` (PAGE_FILES both-ways; the
hand-off fixture `native-play.json` regenerated by `tools/native_play.py`,
deliberately, with the reason in the commit; its assertion compares the
prediction fields, not `seats`), `make.test.mjs` (the start, seated),
`builder.test.mjs`, `yf.test.mjs`, `play-share.test.mjs`;
`worker-api/test/node/build.test.js` and `node worker-api/tools/sync_seats_py.mjs --check`.

Not run in A, with reason: `test_levers_are_live` (reads `run_model`
baselines; two added arrays move no lever verdict, and it is the slowest
module), `calibration_report`, `drawer`, `pool_conservation` (read the share
arrays, which do not change).

**Whole-suite exception: none applies (argued).** `montecarlo.py` gains two
recorded fields filled from dicts already computed, with no random call and no
reordering; nothing `run_model` imports changes; `seats.py`, `stats.py`,
`build_site.py` are not touched. The one place this can be challenged: if the
writer touches the draw loop beyond the two assignments (for example to call
`seats_of` from it), the exception applies and the whole suite runs in the
background on a frozen tree. The changed published-token source (§1.9) is a
published figure, covered by S5's whole suite, not brought forward by FLOW.

## 5. Order and dependencies

Before A: nothing outside A. Inside A, in order: (1) G6's realisation coverage
assertion; (2) `montecarlo.py` fields + trace + no-perturb + the one-off proof;
(3) `prediction.py`, `reader_seats` delegation, G1/G3/G4; (4) `export_draws`,
`reweight`, `render_home`, re-export of the cells, G2/G5; (5) `score_forecasts`,
`build_make`, `page.py`, PAGE_FILES, `start_rule` deleted, node fixture;
(6) backtest reproduction; (7) records, `model_index`, re-syncs.

**A hands B:**
- The prediction object from `score_forecasts.model_forecast` / `build_make.start_state` (`forecast.json` `start`: `ward_calls`, `ward_votes`, `list_votes`, derived `seats`) and from `page.handoff` (`ward_calls` as `{ward: party}`, `ward_votes`, `list_votes`). B's make-state `f` encodes exactly these.
- Interim keys B deletes: `start.combined_share`, `start.published_middle` (= `{}`), `handoff.share`; with them `make.js` `fromMiddle` / `raisedAtStart` / `raisedText` / `paintStartNote` and their comments (`:33, 192, 214-266, 313, 400, 711-726`), `f.js:76`'s sessionStorage `combined_share`, `builder-state.startState({calls, share})`, `tests/test_worker_routing.py:816`.
- `prediction.seats_of(pred, council, order=)` is the seat law B's two-ballot `reader_seats` calls after validation; `reader_seats` already delegates.
- Ballot totals: the rule-A sums per ballot are available; `x-total-votes` (`build_make.total_votes`) is unchanged in A and is B's to replace.
- Known interim difference: under non-uniform weights the page seats the interim `share` through today's `reader_seats` at the fixed `ctx.T`, while rule A's seats are `seats_of` on the weighted whole votes. M9 covers unit weights only; nothing in A checks the weighted case. B closes it with the two-ballot entry and its stated totals.

**A hands C:** `forecast.json` `start` is the object C seals and the `/forecast`
pointer reads; `draws_sha256` changes with the re-export (C's ledger field).

**Files A shares:** `page.py` (A; C if the hand-off note moves), `build_make.py`
(A, B), `score_forecasts.py` (A, B), `reader_seats.py` (A delegation, B
signature), `sync_py.mjs` (A), `worker-api/seats-py/src/` copy (A re-sync, B
deploy), `render_home.py` (A; C if `ballots.typical.*` tokens live there),
`reweight.py` (A). `src/share-edge.js`: not touched by A.

## 6. Decisions, open questions, estimate

- **D-A1 (owner): drop `pr_share` for the two vote blocks.** Measured (M10): keeping both is 1,700,229 bytes gzipped, over the 1,500,000 budget; dropping `pr_share` is 1,419,546. `pr_share` would be a lossy stored copy of `list_vote / row sum`. Cost: §1.5, §1.8, §1.9 and their tests (a published token's source changes; display unchanged). Alternative (ii): keep `pr_share`, raise `BUDGET_GZIP_BYTES` to about 1.75 MB (owner approves a PLAN number), and §1.5/§1.8/§1.9 drop out of A. Recommended: (i).
- **D-A2: whole votes per draw, not two scalar totals.** The owner's correction 1 reads as "record two totals"; M4 shows totals cannot make G2 an equality. The recorded fields are the integers the seat law read; still "a recorded field" (no draw moves). Asks the coordinator to confirm the reading.
- **Q1 (coordinator):** S0 finding 3 and the brief's "OTHER included" assume an OTHER mass in the draws; there is none at joburg 2026 (M2). This spec keeps every party under its own code and refuses off-roster mass. If the owner meant a literal `OTHER` key in the prediction object, `reader_seats`' roster refusal must admit it (B), and summing changes seats (G4 toy).
- **Q2:** `reader_seats` delegation (§1.3) edits a B file in A. If the coordinator prefers B to do it, `seats_of` and `reader_seats` are two compositions until B lands.
- **Q3:** `montecarlo.main`'s `winner` column (M11) is a fourth modal-call site with an unstable sort. Routing it through `prediction.ward_calls` changes `montecarlo.py` beyond a recorded field, which brings the whole suite forward (FLOW). A exempts it in G1 with the reason and relies on `test_served_draws` check 2 (winner equal where the top count is unique) plus M3 (no ties). Route it in a later model-tier version?
- **Q4:** page load grows from about 0.86 MB to 1.42 MB gzipped per cell under D-A1 (1.70 MB under (ii)). Phase 2 lazy-loads the engine; Phase 1 does not change when it loads.
- **Risk:** `declares.py` and the ledger see a changed `model_sha256`/code hash for the served cells; the published forecast artefacts in `data/processed` are not regenerated (no draw moved), so their declarations still name the old commit, which `declares` scores by commit existence, not equality (read, not run with the change).
- **Estimate:** 2 days writing and checks, including about 24 minutes for the backtest reproduction, a few minutes per export cell (one 5,000-draw `run_model` took 151 s here; the export runs four laws in parallel; three cells), and `test_export_draws` (minutes).
