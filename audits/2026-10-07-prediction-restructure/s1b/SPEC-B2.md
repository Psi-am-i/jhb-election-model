# Slice B2: ward-by-ward editor bounds (specification)

Designer, 2026-10-09. Read-only: nothing in the repository was edited. Probes
are in this directory and write only here. **V** = verified (file:line, or a
probe run in this session, named). **A** = argued.

Probe oracle: `scipy` is not in `.venv` (V). It was installed into
`./pylib` of this scratch directory for the probes' LP checks only. Nothing in
this spec's generator depends on it unless the owner approves decision O3.

## 0. Finding

At the owner's rule (past extremes, widened by 5 points), ward-by-ward ranges
add the joint condition to slice B. On our prediction's map they leave the
citywide floors unchanged. Across the panel they raise the mean floor of the
larger parties by about 2 points (§6).

- **Across the panel:** for the 69 party-city-years with at least 5% of the
  ward vote, the mean floor is 10.4% against slice B's 8.5%. It is above
  slice B's in 43 of the 69 (V, `extra.py`).
- **Our prediction's map (ANC 70 wards):** the ANC's floor is 0.9% from the
  ward ranges alone, and 8.4% once slice B's per-ward winning share is applied
  in each ward. Slice B gives the same 8.4% (V, `ours.py`).
- **The screenshot state** (ANC 8.4%, DA 29.3%, rule A's map, values read off
  `s2/screens-b/vote-375-edited.png` to one decimal) is jointly feasible under
  those ranges. The LP's least violation is 0.06 points, which is the size of
  the read-off rounding (V, `ours.py`).
- **What excludes the screenshot state** (each measured, owner decision O1):
  - ranges at percentiles of the swings rather than extremes;
  - a citywide swing allowance per party (§9), which is not in the packet's
    ward-by-ward brief.

What ward-by-ward does add: every state the editor makes becomes a result that
some set of ward votes could produce. Inside the per-party box of §3 (its
ceilings are close to slice B's but not equal: ANC 71.8% against 72.6% on
rule A's map), 71 of 100 states reached by moves
anywhere in a slider's range had no ward-vote matrix behind them. The median
shortfall was 7.6 points and the largest 27.6 (V, `walk_wide.py`, rule A's map,
ext+sb ranges). With moves of up to 10 points the count was 0 of 100 (V,
`walk.py`).

## 1. Facts this spec rests on

| fact | status |
|---|---|
| Slice B's ward bound: `wonE` sums `e[w]` over a party's called wards; `wardBounds` gives floor `q_win·won`, ceiling `won + q_run·(1−won)` | V `builder-state.js:100-117` |
| `editor_bounds` widens `panel_extremes` by `EDITOR_WIDEN_PP`, caps `q_run` at `RUNNER_UP_MAX`; served `q_win` 0.1862, `q_run` 0.5, gap −6.758..+11.157 | V `build_make.py:250-288`; `site/your-forecast/forecast.json` read |
| `expected_ward_shares`: e = 2026 roll × preceding-LGE VD turnout over `montecarlo.ward_parts` parts | V `build_make.py:189-247` |
| `montecarlo.ward_parts`: unheld target → crosswalk (split VDs apportioned by `part_registered`); held target → its own file, every VD whole | V `montecarlo.py:865-945` |
| `score_forecasts._read_rows` aggregates ward votes by ward; it returns no per-VD party votes | V `score_forecasts.py:234-279` |
| Cleaned metro LGE files: 8 metros × 2000, 2006, 2011, 2016, 2021; `npe2024_*_vd_party.csv` also exist | V `ls data/raw/elections` |
| VD continuity between consecutive LGEs, by target registration matched to a previous-election VD: 82.5% (MAN 2011→16) to 99.8% (CPT 2016→21); 2026 wards with a part lacking a 2021 VD: 5; with no prior: 0 | V `swing.py`, `ours.py` |
| Rule A's start: ANC 70, DA 44, PA 10, MK 9, EFF 2 wards; ward vote ANC 21.31%, DA 25.17%, PA 11.86%, EFF 10.42%, ASA 9.18%, MK 8.57% | V `forecast.json` read |
| 54 of 74 roster parties have no 2021 ward vote in any 2026 ward (MK, BOSA, RISE, SACP, All Citizens Party among those above 0.3%) | V `ours.py` |
| The page already runs Pyodide (`v0.29.5/full` from jsdelivr) and numpy in a Worker | V `reweight-engine.js:19`, `model-worker.js:1-3` |
| `montecarlo` does not import `score_forecasts` or `build_make` | V grep |

## 2. Per ward, per party: the range

For target ward w and party p, with all shares of w's valid ward-ballot votes:

1. **Prior `h[w][p]`:** p's share in w at the preceding LGE
   (`cityconfig.Target.previous_lge`). Each target part
   `(vd, ward, part_registered)` from `montecarlo.ward_parts(target)` takes its
   VD's previous ward-ballot votes times `part_registered / Σ part_registered`
   of that VD. A part whose VD has no previous record is left out, and the
   count is recorded (as `expected_ward_shares` does). Party names are folded
   by `parties.canonical`. (V, `load.prior_on`; the generator reads through
   `ward_parts` and an extended `_read_rows`, §8.)
2. **Swing allowance by starting share.** Use every consecutive metro LGE pair
   (a → b) with b < target: 32 pairs for 2026 (8 metros × 4). For each, b's
   wards take a's VD votes by the same join. The population is the
   (ward, party) pairs where the party **stood both times** (h > 0 and s > 0).
   `INDEPENDENT` is excluded because the files merge every independent in a VD
   into one row (DATA-QUALITY item 12). Pairs are binned by h at the edges
   `SWING_BINS` = (0.01, 0.05, 0.15, 0.35, 0.60). Each bin carries
   `(d_lo, d_hi)`, the least and greatest s − h.
3. **Range:** `lo = max(0, h + d_lo − 0.05)`, `hi = min(1, h + d_hi + 0.05)`
   (`EDITOR_WIDEN_PP`, the owner's 5 points).
4. **No record in this ward, but a record in the city** at the preceding LGE
   (a party that stood elsewhere): take p's citywide previous ward-ballot share
   as h and apply 2–3.
5. **New to the city** (no ward vote anywhere in the city at the preceding
   LGE: MK, BOSA, RISE, SACP and 50 others in 2026): `lo = 0`,
   `hi = min(1, N + 0.05)`. N is the greatest share any party new to its city
   took in a ward, over the same pairs. For 2026, N = 46.4% (EFF, Ekurhuleni
   2016, ward 79700102) (V, `newcomer.py`).
6. **A ward with no prior record:** every party [0, 1], counted. There are none
   in 2026 (V).

Why steps 4 and 5 are separate (V, `newcomer.py`, 32 pairs): the h = 0
population mixes parties new to the city (19,244 pairs, greatest 46.4%) with
parties absent only from that ward (4,100 pairs, greatest 73.2%). The top of
the second group is the ANC returning to Nelson Mandela Bay ward 29300045 in
2011, after fielding no ward candidate there in 2006. Next is the DA in Cape
Town ward 19100013. Both are candidacy lapses, and the editor cannot know
candidacy (§10, limit 1).

**2026 allowance** (V, `b2bt.allowance("2027","ext")`; stood-both pairs, IND
excluded, 32 pairs). `d_lo..d_hi` in points:

| h bin | pairs | d_lo .. d_hi |
|---|---|---|
| (0, 1%] | 11,279 | −1.0 .. +24.2 |
| (1, 5%] | 4,076 | −4.8 .. +62.0 (PA, JHB 2021 ward 79800018, 2.6 → 64.6%) |
| (5, 15%] | 1,854 | −14.2 .. +56.5 |
| (15, 35%] | 922 | −30.9 .. +54.5 |
| (35, 60%] | 759 | −47.4 .. +46.0 |
| (60, 100%] | 2,243 | −62.7 .. +30.2 |

Each extreme was opened before being used (V, `swing.py` and the ward reads in
this session). Before conditioning on candidacy, the largest drops were
candidacy lapses (the ANC in NMA 2006 and 2016, 84.7 → 0 and 79.8 → 0). After
conditioning, the extremes are real swings: the PA surge in Eldorado Park, and
the Independent Democrats' 2011 merger into the DA (DA 32.1 → 86.6% in Cape
Town ward 19100066).

**The per-ward shape of slice B is kept and applied inside each ward:** the
painted winner holds at least `q_win`, and every other party at most `q_run`
(both from `panel_extremes`, unchanged). Without it, the ANC's floor on rule
A's map is 0.9%. With it, the floor is 8.4% (V, `ours.py`).

## 3. The joint condition in a painted ward, and what the editor enforces

**The ward's set.** With painted winner W, S_w is the set of share vectors x
with `lo ≤ x ≤ hi`, `Σx = 1` and `x_W ≥ x_q` for every q, using the ranges of
§2 after the per-ward shape.

**Its per-party projection, in closed form** (no LP; `ward_poly.ward_range`,
ported to JS). Let L = Σ_{q≠W} lo_q.
- σmax = min(hi_W, 1 − L).
- σmin = the least σ ≥ max(lo_W, max_q lo_q) with σ + Σ_{q≠W} min(hi_q, σ) ≥ 1,
  found by walking the sorted hi values.
- S_w is empty iff σmin > σmax.
- Winner: [σmin, σmax].
- Non-winner p, with L_p = L − lo_p:
  - min = max(lo_p, 1 − σmax − Σ_{q∉{W,p}} min(hi_q, σmax));
  - max = min(hi_p, σ*, 1 − σ* − L_p), with σ* = clip((1 − L_p)/2,
    max(lo_W, max_{q∉{W,p}} lo_q), hi_W), plus the absorption check in the
    probe's code.

Checked against an LP oracle (V, `verify_poly.py`, `verify_poly2.py`): 3,400
random wards of 2 to 40 parties gave 0 feasibility disagreements, and 6,254
party min/max values gave 0 mismatches beyond 1e-7.

**Per-party citywide box:** floor_p = Σ_w e_w · min_w(p) and ceil_p =
Σ_w e_w · max_w(p). Computing it costs O(W·P·log P): about 135 × 74 × 7 ≈ 70k
operations for the whole map. A paint stroke recomputes only the painted wards
and updates the totals incrementally (A).

**Options, measured:**

| option | what it enforces | per stroke | on load | measured |
|---|---|---|---|---|
| (a) per-party box only | each party alone inside its ward-built range | O(W·P log P), under 1 ms (A) | nothing | 71/100 far-move states infeasible jointly (`walk_wide.py`); 0/100 with moves of up to 10 points (`walk.py`) |
| (b) box + whole-state LP check as a note | (a), and a note when the whole state has no ward matrix | as (a) | one LP per check, debounced, in the worker | the LP solves rule A's case in 0.43 s natively, Python matrix build included (`extra.py`) |
| **(c) witness editor (recommended)** | every state carries a ward-share matrix X inside every S_w, so the whole state is feasible by construction | O(W·P log P) per slider move or painted ward (A) | one LP when a state arrives from a link or a hand-off | moves exact to 3e-16 and always inside, 200 random moves (`witness.py`) |

**Recommended: (c).** The packet asks the editor to enforce the winner
condition in each painted ward. (a) enforces it per party but not for the
state: measured above. (b) detects but does not prevent. (c) prevents, at
box cost per stroke, and its slider range is exactly the box.

**(c), mechanism.**
- **State in the editor:** `{calls, ward, list, X}`. X is shares, wards ×
  roster. `ward` (whole votes) is X aggregated by e onto the state's ward
  total and apportioned (existing bounded largest remainder). `list` follows
  by the existing gap rule (`listFollow`, gap bounds unchanged). **f does not
  carry X:** encoding, `decode`, validity and G7 are unchanged (SPEC-B D4).
- **Slider move**, party p to target t in [floor_p, ceil_p]:
  1. Build Y, the point of each S_w where p is greatest (or least), disturbing
     the rest least:
     - the winner's share stays at x_wW unless the feasible σ interval for that
       p value excludes it, in which case it is clipped into the interval;
     - the other parties keep `lo + k·(x − lo)`, water-filled to their caps
       `min(hi, σ)`.
  2. Set X ← (1−λ)X + λY, with λ = (t − V_p)/(ceil_p − V_p) (or towards floor_p).
  Convexity keeps X in every S_w, and V_p lands on t exactly (V, `witness.py`
  with a proportional-to-room fill. The least-disturbance fill is A; a test is
  in §7).
- **Paint stroke,** ward w to W':
  - put X_w into S_w(W') by the same rule: σ' = clip(x_wW', feasible
    interval), others clipped into `[lo, min(hi, σ')]` and water-filled
    in proportion to their current shares;
  - O(P log P) per ward;
  - the citywide votes move by e_w × the ward's change. Painting a ward moves
    that party's vote, as winning a ward does.
- **Load** (our prediction, a link, a hand-off): solve for X by LP: least total
  |slack| on the citywide equalities `Σ_w e_w X_wp = V_p`, subject to X in every
  S_w. Sizes for Joburg: 9,990 share variables, 148 slack variables, 209
  equalities and 9,855 winner rows. All 9,855 can bind, because the newcomer
  cap exceeds every winner's floor (V, `extra.py`). Slack under 1e-6 (half a
  vote) counts as inside.
  - **Our prediction:** solved at build and shipped as `start.witness`
    (sparse; G7 untouched).
  - **Links and hand-offs:** solved in the page's existing Pyodide worker with
    Pyodide's `scipy` (HiGHS), loaded only then (O3).
- **Rejected while designing:** rebuilding X by sweeps of single-party moves.
  It stalled 18 to 36 points short after 200 sweeps on 20 feasible states (V,
  `witness.py`).
- **History** keeps X with each state, as float32: 135 × 74 × 4 bytes ≈ 40 kB
  per entry, so 2.4 MB at the current limit of 60. A limit of 30 is
  recommended (A).

## 4. At the edges

1. **A painted ward no vote vector can satisfy** (S_w empty: the winner's hi is
   below another party's lo or below `q_win`, or Σ lo > 1).
   - The paint is allowed: readers hand-pick every ward.
   - That ward's ranges become slice B's shape alone: winner [q_win, 1], others
     [0, q_run]. That shape is always feasible with three or more parties (A).
   - The page names the ward and party: "Ward 34: no past result has <party>
     winning here; this ward uses the widest rule."
   - Counts: 2026 under the recommended ranges, 0 of 9,990 (ward, party) pairs
     are unpaintable. At p01 the count is 2,361, and at p05 8,998 (V,
     `extra.py`). The panel's real winners fell back in 3 of 2,191 wards
     (Durban 2016) (V, `backtest2.log`).
2. **A state from a link or a hand-off outside the joint set** (LP slack ≥
   1e-6). It opens as it is, and its seats are computed from its votes as now.
   The note names each party whose reachable value differs, and by how much.
   The editor's X is the LP's least-slack matrix, so the **first edit of any
   kind** replaces the out-of-range votes with that matrix's aggregation plus
   the edit, and the note says this before it happens. This replaces slice B's
   "its next edit brings it inside", which the slice B review found false for
   the gap bound (finding 3). The gap rule is unchanged, and its out-of-range
   case keeps slice B's wording, corrected per that finding.
3. **Bounds never decide validity** (SPEC-B D4). `invariantErrors`, `decode`,
   `validate.js`, `reader_seats` and the scorer read neither the ranges nor X.

## 5. Our prediction (rule A) inside the new bounds

Measured on `forecast.json` start, e from the served `x-editor-bounds` (V,
`ours.py`):

| ranges | wards falling back | per-party box | whole-state LP slack |
|---|---|---|---|
| extremes, no per-ward shape | 0 | inside | 0 |
| **extremes + slice B per-ward shape (recommended)** | 0 | inside | 0 |
| p01 + shape | 0 | inside | 0 |
| p05 + shape | 11 (MK's modal wards among them) | inside after fallback | 0 after fallback |

Rule A is inside under the recommended ranges. Under p05, MK's newcomer cap
(6.0% + 5 points) is below `q_win`, so MK cannot win any ward. That is a
finding about the bounds, not about rule A: MK has no local-election record,
and the panel cannot see it. The 2024 national file
(`npe2024_JHB_vd_party.csv`) is a possible prior for parties new to local
elections. It is flagged, not chosen: O2.

Rule A is also inside the citywide swing allowance of §9 (V, `cityswing.py`).

## 6. Evidence: the backtest

Population: 24 city-years (2011, 2016, 2021 × 8 metros); 2,191 wards; 40,937
(ward, party) pairs where the party had a prior share or a result there
(IND excluded). Each city-year is built only from elections before it: swing
pairs with b < target, slice B's extremes from files before the target, and e
from the target's roll times the preceding election's turnout. The roll is
published before polling day (`ward_parts` docstring). The real ward winners
are painted. The citywide limit is the per-party box, and the joint check is
the LP with e weights. V, `b2bt.py` → `backtest2.log`.

| ranges | real ward results outside their range | of which winners | real citywide ward shares outside the editor's limits | city-years whose real state fails the joint LP | wards falling back |
|---|---|---|---|---|---|
| **extremes + shape (recommended)** | 28 of 40,937 (23 stood both, 4 new to the city, 1 did not stand) | 18 | **0 of 665** parties | 0 of 24 | 3 |
| extremes, no shape | 27 | 17 | 0 of 665 | 0 | 3 |
| p01 + shape | 184 | 44 | 1 of 665 (Minority Front, Durban 2016, 0.60% vs floor 0.66%) | 1 | 13 |
| p05 + shape | 820 | 160 | 7 of 665 (EFF in Ekurhuleni, Joburg and Tshwane 2016; DA in Cape Town and NMA 2011; Minority Front; IND) | 6 | 13 |
| **slice B (current)** | 1 of 40,937 (implied per-ward rule: winner ≥ q_win, others ≤ q_run) | 1 | **0 of 665** | n/a | n/a |

The 28 ward results outside the recommended ranges, by cause (V, the
`OUTLIST` print):

| cause | results | where |
|---|---|---|
| merger | 10 | Cape Town 2011, DA after absorbing the Independent Democrats |
| local surges and the drops beside them | 7 | Al Jama-ah in Joburg 2021 ward 9; PA in Joburg 2021 wards 17 and 18, with the DA's drop in ward 18; UDM in NMA 2016 ward 30; IFP's drop in Durban 2011; the ANC in Joburg 2011 ward 50 |
| candidacy | 5 | the ANC in NMA: returning in 2011 below its city-prior floor (3 wards), not standing in 2016 (1), and returning in 2021 (1) |
| a party's collapse | 4 | Minority Front, Durban 2016 |
| a newcomer above the cap built before it | 1 | EFF, Ekurhuleni 2016 (46.4% against a cap of 46.3%) |
| slice B's own q_win miss | 1 | DA, Joburg 2021 ward 82 (23.6%) |

Width of the citywide limit given the real winners: 69 party-city-years with
at least 5% of the ward vote, among each city-year's top four (V,
`extra.py`):

| ranges | mean ceiling − floor | mean floor | floor above slice B's |
|---|---|---|---|
| extremes + shape | 51.9 points | 10.4% | 43 of 69 |
| p01 + shape | 38.9 | 12.9% | 52 |
| p05 + shape | 28.7 | 17.0% | 55 |
| slice B | 58.8 | 8.5% | — |

**Limit, stated here:** e is expected turnout, and the real citywide share is
weighted by real turnout. Recomputing with real turnout weights (hindsight,
"hind" in the log) changes no count at the extremes (V).

## 7. Records, guards and tests

### JUDGEMENT-CALLS (new §R6–§R11; §R5 superseded)

- **§R5 superseded:** the each-ward-alone bound. What was: `wonE` and
  `wardBounds`. What is: §R6–§R10. The decision and its date.
- **§R6 · ward ranges from the preceding LGE and swings in consecutive metro
  LGEs, conditioned on standing in both** (⚖️ argued). Alternatives:
  unconditioned, where candidacy lapses set the extremes (84.7 → 0); the
  city's own transitions only.
- **§R7 · `SWING_BINS` = (0.01, 0.05, 0.15, 0.35, 0.60)** (🔴 typed). It
  matters because the spread of swings grows with starting share (table §2).
  How to check: the test shows a bin's extremes move only when that bin's
  population changes.
- **§R8 · no ward record → the city's share as the prior; new to the city →
  `[0, N + 5]`** (⚖️ argued, `newcomer.py` figures). Alternative, not taken:
  the 2024 national election as a prior for parties new to local elections
  (O2).
- **§R9 · extremes rather than percentiles** (⚖️ owner's call, O1, citing
  "use real historical limits and allow 5% either side"). Evidence: §6.
- **§R10 · slice B's per-ward shape kept inside each ward; an unsatisfiable
  painted ward falls back to it** (⚖️ argued).
- **§R11 · the witness editor; the LP on load** (⚖️ argued; O3 if scipy).

### MODEL-LOG (append, dated)

- What was: slice B's bound.
- What is: §2–§4.
- The tables of §0, §5 and §6, measured by the writer's own build and tests,
  not copied from this spec.
- `start.out_of_bounds` and the LP slack of `start.witness`.

### MACHINERY

The ward ranges, the ward set, the witness, the load LP, the fallback, and
where each lives.

### Guards

Each states its population and checks it both ways, catches a constructed
violation, and goes quiet when the violation is reverted.

| guard | test | population | constructed violations |
|---|---|---|---|
| **The ranges are regenerated from the panel** | `test_your_forecast_page.py::test_the_ward_ranges_are_regenerated_from_the_panel` (replaces the q_win/e parts of `test_the_editor_bounds_are_regenerated_from_the_panel`, keeps its gap and q_run parts) | `x-editor-bounds.swing.pairs` == every (city, a, b) of consecutive cleaned metro LGE files with b < target, both ways; each file's sha256 recorded; `ward_ranges` keys == schema wards both ways; `party_ranges` keys == roster both ways; the (ward, party) keys of `ward_ranges` == the set of pairs with a non-zero prior, computed independently in the test from the preceding file through `ward_parts`, both ways; each `party_ranges` entry is the city-prior range exactly when `city_share` > 0 and the newcomer range otherwise, both ways. Slice B review finding 4 (one-sided floors, the cap, the previous-turnout file) is not closed by B2 unless the writer extends the kept q_run and gap parts the same way; B2 recommends doing so in the same test | on temp copies: (1) one VD's party votes in the preceding file raised → exactly the wards `ward_parts` maps that VD to change their range, no other ward; (2) one split VD's `part_registered` changed in a copied crosswalk → both its wards' priors and `e` move; (3) one stood-both pair in a transition file pushed past its bin's extreme → that bin's `d_hi` moves, no other bin; (4) a party's ward rows deleted in one ward of the preceding file → its range there becomes its city-prior range; (5) a party deleted from the whole preceding file → it gets the newcomer range; each reverted → equal to the served bounds |
| **Closed form equals the set** | `builder.test.mjs` "the ward range is the set's projection" | random wards of 2–5 parties | compared with vertex enumeration of S_w in the test, which needs no LP library; a constructed formula with the winner condition dropped → caught |
| **Witness invariant** | `builder.test.mjs` random walk (extended) | every state the walk reaches | X inside every S_w (ranges, Σ = 1, winner ≥ each), aggregation equal to `ward` to rounding, slider range equal to the box; one cell of X perturbed in a copy → named; reverted → quiet |
| **Load LP** | `test_your_forecast_page.py::test_the_start_witness_is_inside_and_aggregates_to_start` and a node test of the worker's call | `start.witness` over all wards; a walk-made state; a constructed infeasible state (ANC below its floor) | witness inside every S_w and aggregating to start's ward votes within half a vote; the infeasible state → slack > 0 and the note names the ANC |
| **Bounds read, not typed** | `builder.test.mjs` "the bounds are read from the schema, not typed" | `BOUND_FUNCTIONS` becomes `["wardRange", "boxOf", "extremePoint", "paintInto", "gapOf", "listBounds", "contextOf"]` | a numeric literal in any of them → found |

### Targeted tests (exact list)

Python, `run_all.py -k`:
- `your_forecast_page`;
- `score_forecasts` (because `_read_rows` gains a return);
- `rank_entries` and `entries` (they import `score_forecasts`);
- `prediction_rule` (imports `score_forecasts`, V grep);
- `site_assets`, `site_structure` and `number_scan` (note texts in the template).

Node, by file:
- `interactive/tests/builder.test.mjs`, `make.test.mjs`, `yf.test.mjs`,
  `page.test.mjs` (served copy);
- `worker-api/test/node/build.test.js` (`make_schema.mjs` checks the
  `editor_bounds` keys, V `make_schema.mjs:66-70`);
- `node interactive/tools/sync_py.mjs --check` (if the LP module is copied to
  the page);
- `interactive/tools/yf_jump_check.mjs`.

### Whole-suite exception

No. B2 touches neither `montecarlo.py` (it only calls `ward_parts`, read-only)
nor anything `run_model` imports. `score_forecasts` is not imported by
`montecarlo` (V). FLOW.md's exceptions do not apply (A).

## 8. Files, functions, estimate; what this replaces

**`src/score_forecasts.py`**
- `_read_rows(path, *, roll=False, vd_votes=False)`. The fifth return,
  `{vd: {IEC name: ward votes}}`, comes when `vd_votes` is set. It remains
  the one reader of the cleaned layout.

**`src/build_make.py`**
- `ward_priors(city, target, wards) -> (h, city_share, provenance)`, through
  `montecarlo.ward_parts(target)` and `Target.previous_lge`.
- `swing_allowance(city, target) -> {bins, d, n_new_cap, pairs, sources}`.
- `ward_ranges(city, target, wards, roster) -> {ward_ranges, party_ranges}`.
  `ward_ranges` holds only (ward, party) pairs with a prior. Other parties take
  their `party_ranges` entry (city prior or newcomer).
- `editor_bounds` adds `ward_ranges`, `party_ranges`, `swing` and
  `SWING_BINS` to `x-editor-bounds`. It keeps `e`, `q_win`, `q_run`, the gap
  bounds and their provenance.
- `forecast_data` adds `start.witness` from the load LP.

**LP module**
- `src/ward_witness.py`, one function `witness(e, ranges, calls, V) ->
  (X, slack)`. It runs at build, which needs `scipy` in `.venv` (O3), and in
  the page worker with Pyodide's scipy, copied by `sync_py.mjs`. It is the
  only definition.

**`worker-api/tools/make_schema.mjs`**
- Accepts the new keys.

**`interactive/js/builder-state.js`**
- New: `wardRange` (the closed form), `boxOf`, `extremePoint`, `paintInto`,
  `moveParty`, and `fallbackWards`.
- `outOfBounds` returns the joint-slack parties (from the load LP) plus the
  gap cases.
- `History` carries X.
- **Deleted:** `wonE`, `wardBounds`, `clampToBounds`; `setWardPercent` becomes
  `moveParty` plus aggregation.

**`interactive/js/make.js`**
- Load-time witness call; note texts (§4).
- Sliders take the box.
- "Preparing the ward ranges" status until X exists for a link or hand-off.

**Pyodide worker**
- `handoff` returns the witness with the prediction.
- A `witness` call for links.
- `scipy` is loaded on first need.

**Replaces in slice B:** `wonE`, `wardBounds`, `clampToBounds`, JUDGEMENT-CALLS
§R5, the q_win-only floor and the q_run-only ceiling. **Kept:** `e`, `q_win`
and `q_run` (now per-ward shape), the gap bounds, `listBounds`, `listFollow`,
`setListGap`, and D4.

**Estimate:** about 4.5 days for one writer.

| part | days |
|---|---|
| generator and `_read_rows` | 1 |
| witness editor in JS | 1.5 |
| LP module, build and worker wiring | 1 |
| guards, records and notes | 1 |

Option (a) alone would be about 2 days and option (b) about 3. Diff review and
the targeted tests are on top of each.

## 9. Option for the owner: a citywide swing allowance (outside the brief)

Same panel, same widening. A party's citywide ward-ballot share moves from its
prior by at most the panel's extremes for its starting size, ± 5 points. A
party new to the city may reach at most the greatest share a newcomer has
taken, + 5. Measured (V, `cityswing.py`):

- **Out of sample, 24 city-years, 641 parties:** 13 outside.
  - 12 are in 2011, whose allowance comes from one round of transitions; 8 of
    those are the DA, in all eight metros, in the year it absorbed the
    Independent Democrats.
  - 1 is in 2021 (EFF, Durban, +6.9 points).
  - 2016: none.
- **2026 allowance (32 transitions):**

  | party | allowed citywide ward share | rule A |
  |---|---|---|
  | ANC | 19.6–51.6% | 21.3% |
  | DA | 14.0–46.0% | 25.2% |
  | PA | 0–14.7% | 11.9% |
  | MK | 0–19.0% | 8.6% |

  Rule A is inside for every party. The screenshot's ANC 8.4% is outside.
- In the witness editor it would be one more set of bounds, on the aggregates
  in the load LP. A slider move's λ would be capped so that no other party
  leaves its allowance: O(P) per move (A).

## 10. Limits

1. **Candidacy.** The editor cannot know which parties stand in which ward. The
   IEC's per-ward candidate list is a §4b-type input with no second source.
   With it, a party not standing would get [0, 0] in that ward. Without it,
   5 of the 28 backtest misses come from candidacy (§6).
2. **VD reuse across delimitations.** The join is by VD number. A number
   reused for a different place is undetectable from the files (A). Matched
   registration ranges from 82.5% to 99.8% (§1).
3. **Mergers.** A merger known before the election (the Independent
   Democrats into the DA, 2011) is not summed into the prior. It accounts for
   10 of the 28 ward misses.
4. **Phone timings** are argued from operation counts. Only native Python and
   HiGHS times were measured. Pyodide's scipy download size and solve time on
   a phone are not measured.
5. **The witness fill rule** decides which other parties make way when one
   moves. It is specified (least disturbance, in proportion to holdings above
   the floor), but other rules are possible. It is visible to readers as how
   the others move.

## 11. Decisions for the owner

- **O1.** Extremes (the plain reading of the rule; adds the joint condition
  only; excludes no real citywide result) or percentiles (raise floors, but
  exclude 184 or 820 real ward results and 1 or 7 real citywide results, and
  make 2,361 or 8,998 of 9,990 2026 (ward, party) pairs unpaintable).
- **O2.** For parties new to local elections, the 2024 national file as a
  prior, or the newcomer cap.
- **O3.** Add `scipy` to `.venv` for the build's witness LP, and load
  Pyodide's scipy in the page for links and hand-offs. Or choose option (a)
  or (b), which need no solver for (a) and the same solver for (b).
- **O4.** The citywide swing allowance of §9.

## Probes (this directory)

`load.py`, `swing.py`, `newcomer.py`, `deviation.py` (residual swings:
ward-level extremes barely narrow after removing the citywide swing),
`ward_poly.py`, `verify_poly.py` (3,000 wards of 2–9 parties),
`verify_poly2.py` (400 wards of 10–40 parties; its print line still says
3000 because it was copied from the first), `b2bt.py` →
`backtest2.log`, `extra.py`, `ours.py`, `walk.py`, `walk_wide.py`,
`witness.py`, `cityswing.py`. `backtest.log` predates the newcomer split and
the fallback, and is superseded by `backtest2.log`.
