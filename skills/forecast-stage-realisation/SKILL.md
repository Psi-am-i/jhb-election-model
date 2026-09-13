---
name: forecast-stage-realisation
description: Observe the REALISATION segment of the Johannesburg forecast pipeline — stages 40_draws, 41_guards, 42_pr_share_draws, 43_ward_share_draws, 44_seat_draws, 45_delivered. Use when reading or writing anything between the drawn vote shares and the allocated council: the per-draw share arrays, the ~20 guard counters, Schedule 1 seat allocation, overhang, the chamber fill, or the delivery proof. Carries the field inventory with units, the invariants and why each holds, the traps, and what could not be checked.
---

# The realisation segment: draws → shares → seats

`run_model` emits thirteen stages under `--run-dir` (opt-in; `--trace-detail`
adds the per-draw arrays; `test_chain` asserts the run is byte-identical with
and without either). The last six are this skill's subject. Everything here was
established against a real trace — `src/montecarlo.py --city joburg --target
2021 --draws 400 --seed 12345 --run-dir /tmp/... --trace-detail` — not inferred
from the source.

The executable form of everything below is **`tests/test_stage_realisation.py`**
(47 tests). Its predicates are pure functions over one stage payload, so they
run with no data; each is exercised against a constructed healthy payload, a
constructed corrupted one, and a real 40-draw trace generated in the test.

---

## 1. The field inventory, with units

### `40_draws` — the summary. Six dicts, all keyed by party.

| field | units | sums to |
|---|---|---|
| `pr_mean` | fraction of the citywide PR ballot | **1** |
| `pr_p5`, `pr_p95` | the same, 5th/95th marginal percentile over draws | nothing in particular (0.596 and 1.613 at joburg 2021) |
| `ward_mean` | fraction of the citywide ward ballot | **1** |
| `ward_win_sum` | ward wins **summed over every draw** | **draws × wards** (54,000 = 400 × 135) |
| `seat_mean` | mean council seats per party | **the mean chamber** (exactly 270.0) |

`pr_mean` / `pr_p5` / `pr_p95` / `ward_mean` cover the whole universe (55
parties at joburg 2021). `ward_win_sum` (5 parties) and `seat_mean` are subsets
— `seat_mean`'s keys are the union of what the seat draws contain.

### `41_guards` — twenty counters. **Exactly twenty; the list is in the test.**

Three are **denominators**, not events, and everything else is read against
them:

* `bounds_checked` — incremented once per draw, so it **IS** the draw count.
  Nothing else in the payload is, which makes it the only field tying the board
  to the draws it describes.
* `ipf_balances` — one per draw in which the shock was non-degenerate.
* `solve_calls` — two per draw (`solve_and_predict` runs twice).

The events: `bounds_violations` (per party, §3.5 θ-bound breaches, denominator
`bounds_checked`), `ipf_failures` (balances that fell back to `partial_balance`,
discarding the level shock for **every** party in that draw),
`ipf_clipped` (per party, draws held at pool capacity), `ipf_headroom`
(per party, pre-draw ask ÷ capacity — the only sight of who is *about* to be
clipped), `cap_moved` / `cap_undershoots` (`capped_targets`' redistribution),
`excessive_draws` and `overhang_count` (item 16 triggers), and eight `solve_*`
counters.

### `42_pr_share_draws`, `43_ward_share_draws` — `(draws, parties)` float arrays

Citywide share of one ballot per draw. Every row sums to 1 to floating point
(normalised in the loop by `votes / max(votes.sum(), 1e-12)`). Written only
under `--trace-detail`.

### `44_seat_draws` — a list of `{party: int}`, one per draw

Whole councillors, and the **total entitlement** (ward plus list), which is what
Schedule 1 allocates. Not the list half.

### `45_delivered` — the value-bearing read log

`{name: {values, where, kinds, who, reads, dropped}}`. The four lists are
de-duplicated and capped at `montecarlo.DELIVERY_MAX_VALUES` (12), with
`dropped` counting what the cap refused. `kinds` is the strength of the claim:
`consulted` (recorded at the reading site — a delivery proof), `resolved` (this
process *held* the value; proves nothing was read — §1.68), `resolved-frozen`,
`not-imported`, `missing`. At joburg 2021: 53 records, 12 `consulted`, 45
`resolved`, 2 `resolved-frozen`.

---

## 2. The invariants, and why each holds

**Conservation and arithmetic identity, mostly** — which is why this segment is
unusually checkable. Seats are a step function of votes through a quota, so a
small vote error is amplified at the quota and rounded away below it; nothing
about *magnitudes* is checkable here, and everything about *bookkeeping* is.

1. **Every row of 42/43 sums to one.** By construction. A row that sums to
   **zero** is the one to hunt: the arrays are `np.zeros((draws, npar))` filled
   inside the loop, so a loop that ended early leaves unfilled rows and every
   summary over them is diluted towards zero rather than absent — which reads
   as a quiet forecast, not as a broken one.
2. **`40_draws` is a summary of 42, 43 and 44, and can be recomputed exactly.**
   Verified to 3.3e-16 on the real trace, and 0.0 for the percentiles. This one
   comparison catches three separate defect classes: a summary taken from a
   different array; a statistic stored under another's name; and column
   misalignment (see trap 1).
3. **`sum(ward_win_sum)` is a whole multiple of the draws.** `argmax` always
   returns something, so every draw seats every ward and the total is conserved
   by construction. A remainder means a ward was skipped or double-counted —
   the only way this number can move.
4. **`bounds_checked == len(44_seat_draws)`.** The board and the draws came
   from one run, or they did not.
5. **Every dict-valued counter is bounded by its own denominator**, and the
   orderings hold: `ipf_failures ≤ ipf_balances`, `solve_nonconvergent ≤
   solve_calls`, `..._reachable ≤ ...`, `solve_calls ≤ solve_rounds`,
   `floor_injected_mean ≤ floor_injected_worst`.
6. **`sum(overhang_count) ≥ excessive_draws`.** The first counts (draw, party)
   pairs, the second counts draws with any such party.
7. **`sum(seats) == council − C − D`, on every branch.** `deduct` returns
   `{**sub.seats, **fixed}` allocated over `COUNCIL − sum(fixed)`; `expand`
   adds the excess to a council grown by the same amount; `level` allocates
   over the grown total; `cap` allocates over `COUNCIL`. The council moves and
   the identity does not. Since `C` is structurally zero here (the universe
   drops INDEPENDENT/IND — a registered assumption, not a law) and `D` needs a
   ward winner whose citywide PR total rounds to zero, the shipped form is
   **every draw fills exactly the council**: 270 in all 400 draws at joburg
   2021. Neither `C`, `D` nor the per-draw council size reaches any stage
   payload, so the observer has to be *told* — the predicate takes
   `outside_pool` (default 0, stating the assumption) rather than guessing.
8. **`0 ≤ pr_p5 ≤ pr_p95 ≤ 1`.**
9. **`45_delivered`: `reads ≥ len(values)`** (each read adds at most one
   distinct value), lists ≤ 12 long, `dropped > 0` only when the list is full,
   `kinds` non-empty and drawn from the vocabulary.

**The positive control on the whole observer** is invariant 4 plus the three
denominators being non-zero. A board of zeros is what a clean run and a run
that counted nothing both look like. `arrival_reconciliation` was blind at 20
of 24 rows while reporting nothing wrong; the denominators are what separate
"nothing fired" from "nothing was counted".

---

## 3. Traps — verified, not inherited

### 1. ⛔ 42 and 43 carry NO party names

They are bare arrays. They are readable only because two independent decisions
happen to agree: `universe = sorted(...)` in `run_model` (line ~4032), and
`Trace.put` dumping with `sort_keys=True`. Column *i* is therefore
`sorted(40_draws["pr_mean"])[i]`. Break either and every party's band silently
belongs to its neighbour, with no error anywhere. Nothing else in the
repository asserts this.

### 2. ⛔ "Sums to the council" is the wrong invariant

Schedule 1 strikes the quota over `council − C − D`: independent ward winners
(`C`) and ward winners of parties with no PR list (`D`) leave the pool **with**
the councillor. A forecaster's draws may lawfully fill `council − C − D`. At
joburg 2021, `C = D = 0` in all 400 draws (the universe drops INDEPENDENT/IND,
so `C` is structurally zero — a registered assumption, not a measurement; the
IEC records `C = 1` at eThekwini 2011 and `C = 4` at 2016, and the model is
scored against both). `chamber_fill` exists to flag, not to correct, and the
predicate is told `C + D` rather than inferring it — pass `outside_pool=None`
to make it decline to judge the fill at all.

### 3. ⛔ A per-party median over draws is not a council

**Measured, joburg 2021, 400 draws:** the marginal medians sum to **254**, the
means to exactly **270**. Storing one under the other's name is a defect this
project has had twice. `40_draws.seat_mean` is a mean; the test asserts it and
names the median explicitly in the failure message when it is not.

### 4. ⛔ Exact ties are manufactured, and the tie-break is a string hash

`seats.allocate` ranks remainders by `(-remainder, -combined)`. Two parties
with **equal integer combined votes** produce a bit-identical key; Python's sort
is stable; so the seat goes to whoever came first in the dict. That dict comes
from `seats.eligible_parties`, which iterates `set(ward_votes) | set(pr_votes)`
— a set-of-strings order, i.e. a function of how the party NAME hashes and of
nothing electoral. `allocate`'s own docstring says float remainders make an
exact tie unreachable; equal integers reach it directly, and Schedule 1 breaks
an exact tie **by lot**.

**Measured, joburg 2021, 400 draws, seed 12345:** three allocations hit an
exact tie straddling the cut (ATM / UNITED\_CULTURAL\_MOVEMENT twice at 3,409
combined votes; UIM / ALJAMAAH once at 4,371), and reversing the key order of
`combined` moved a seat in **1 of 400 draws**.

`montecarlo.fix_hash_seed` pins `PYTHONHASHSEED=0` at seven entry points, so
shipped runs are repeatable — but repeatable is not correct, and the residue is
that **renaming a party can move a seat**. The rate is small here and will not
be small everywhere: a sibling reference that gives identically-reached parties
identical shares manufactures whole groups of exact ties.

### 5. The pool-capacity cap is INERT on everything the backtest can see

`capped_targets` redistributes truncated mass **proportional to what each party
already holds**, which pushes it to the top of the ballot — the code's own
comment calls this the larger of its two judgements and reports it firing in
39.2% of draws on the live 2026 forecast. **Measured here at nine city-years**
(joburg 2011/2016/2021, NMB 2016/2021, Cape Town 2016/2021, eThekwini 2016,
Ekurhuleni 2021, Tshwane 2021, 60 draws each): `cap_moved = 0`,
`ipf_clipped = {}`, `cap_undershoots = 0`, `ipf_failures = 0/60` at **every
one**. So the redistribution rule exists only on the forecast the backtest
cannot score, and no panel measurement can validate it. Treat "the cap does not
bind" as a statement about 2021 and earlier, never about 2026.

### 6. `solve_nonconvergent` is saturated, and so is its "reassuring" variant

At joburg 2021: `solve_calls = 800`, `solve_nonconvergent = 800`,
`solve_nonconvergent_reachable = 800`. The comment at the call site says to read
the *reachable* counter instead because it excludes parties under the level
floor — but it is equally pinned at 100%, so it distinguishes nothing. What
makes the saturation harmless is the **gap**, not the count:
`solve_worst_gap_reachable = 1.16e-5`. Read the gaps; the counts carry no
information on the shipped configuration.

### 7. `--run-dir` never writes into the tree, but `--processed` does

`run_model` only *reads* the processed directory; `main` publishes to it. A
diagnostic run prints that it did not rewrite the artefacts. Do not point
`--processed` at a bare `/tmp` directory expecting an overlay — the run dies on
a missing `turnout.csv`. Copy the directory (**copy**, do not symlink: writes
would follow the link back into the tree).

---

## 4. What is currently wrong

1. **`ipf_worst` is not on the guard board.** `ModelRun` carries it as a typed
   field and `41_guards` does not carry the key, so the "whole board" the
   `ModelRun.guards` docstring promises is one counter short. Its only reader
   is `montecarlo.main`'s verbose print, which `compare_history` suppresses with
   `verbose=False` — so on the panel it is computed and read by nobody, which
   is the class this segment's observer exists against.
2. **`cap_moved` adds two different units into one accumulator.**
   `capped_targets.moved` is incremented at two call sites with no reset
   between: `pool_spec` passes **shares** (a vector summing to 1) and the
   per-draw IPF passes **votes** (≈1.8M for CoJ), once per draw.
   `compare_history`'s scoreboard formats the sum as `pct4`. It has never been
   seen because the counter is 0 everywhere on the panel (trap 5); the first
   city-year where the cap fires will print a percentage in the hundreds of
   thousands.
3. **`data/processed/history.json` carries no guard board at all.** Its 24
   records predate `ModelRun.guards`, so the "measured zero" the guard table
   promises has never actually been written to disk. Re-run
   `compare_history` before quoting any guard state from that file.
4. **The tie-break defect of trap 4 is live**, at a measured 1 draw in 400 at
   joburg 2021. `tests/test_stage_realisation.py` ships it as two
   **characterisation** tests, which pass today and fail the day the defect is
   fixed — the message says so. They are deliberately not shipped red.

---

## 5. What could NOT be checked

* **The vote totals the seats were allocated from are not in the trace.**
  `combined`, the per-draw quota, the council size, the threshold, and `C`/`D`
  are all locals of `run_model`; `council_sizes` and `thresholds` reach
  `ModelRun` but no stage payload. **No observer can re-derive a single seat
  draw from the trace.** The shares in 42/43 are normalised, so the scale is
  gone. The tie probe in the test therefore wraps the real `allocate` for the
  duration of one run rather than reconstructing anything — a reconstruction
  would be measuring the reconstruction.
* **Whether a ward with no registered voters credits a spurious winner.**
  `ward_tally.argmax(axis=1)` on an all-zero row returns index 0 and credits
  `universe[0]`. Wards with no VD are excluded upstream (a printed warning at
  Cape Town 2016 names one), so this is guarded elsewhere, not here — but
  `ward_win_sum` is conserved either way and cannot distinguish the two.
* **`ipf_headroom` coverage is checked only coarsely.** It is built over the
  union of pool *members*, which is not obliged to be the universe, so the test
  bounds coverage at 50–100% rather than asserting equality. Dropping one party
  from the map is not detected; dropping forty is.
* **Magnitudes.** Nothing here says the shares are *right*, only that they are
  shares. Calibration is `score.py`'s job and the backtest's.
* **Whether the `expand` / `level` overhang branches are exercised.** The
  shipped rule is `deduct`; the fill invariant for the expanding rules is
  derived from the source and tested on constructed payloads only.
* **`45_delivered` covers the whole run, not this segment.** A record's absence
  cannot be attributed to the realisation stages.

---

## 6. Running it

    .venv/bin/python tests/test_stage_realisation.py          # 47 tests, ~12s
    .venv/bin/python tests/run_all.py -k stage_realisation

The integration tests generate their own 40-draw trace in a temporary directory
(≈11s), reading the real `data/processed/joburg/2021`. They **skip loudly**,
naming the missing file, when the inputs are not on disk — they are not
weakened to compensate.

To look at a trace by hand:

    .venv/bin/python src/montecarlo.py --city joburg --target 2021 \
        --draws 400 --seed 12345 --processed /tmp/overlay/proc \
        --run-dir /tmp/overlay/trace --trace-detail

where `/tmp/overlay/proc` is a **copy** of `data/processed/joburg/2021`.
