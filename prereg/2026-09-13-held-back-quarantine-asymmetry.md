# Pre-registration — lifting `levels.HELD_BACK`, and the asymmetry it is taken on

Written 2026-09-13 on branch `remediation` at `251ea6f`, **BEFORE either arm was
run and before any probe of either arm's result.** Not edited after the result.

> **AMENDED 2026-09-13, STILL BEFORE THE RUN.** Two facts arrived from the
> `src/backtest.py` work in flight, both verified here at unit level before
> being accepted (CLAUDE.md §3: verify at unit level while another worker holds
> the tree, and say so). They sharpen §0, P1, P4 and §5 and add one clause to
> §2. **No prediction was weakened, reversed or removed** — the amendments are
> additive and are marked `[AMENDED]`. Amending a pre-registration after the
> measurement is barred; amending it before is the only time corrections can be
> taken at all, and the alternative is a run scored against facts already known
> to be false. The pre-amendment text is recoverable from git.

⚠️ **The author of this file did not take the measurement and has not seen a
number from it.** Everything below was established by reading `src/levels.py`,
`src/pools.py`, `src/montecarlo.py`, `src/compare_history.py`, `src/backtest.py`,
`src/freeze.py` and the emitted specs' own `transition_ledger`. Where a figure is
cited it is cited to the file or the `MODEL-LOG` § that generated it, never
copied (CLAUDE.md rule zero).

---

## 0. ⛔ THE BRIEF WAS WRONG ABOUT WHAT THIS RUN MEASURES, AND THE CORRECTION IS THE POINT

The brief describes one arm — `HELD_BACK_OFF=1` against a control — and calls it
"lifting the hold". **It is not.** `HELD_BACK` reaches the model by **two paths
with different lifetimes**, and a run taken without a re-emit lifts exactly one
of them.

| path | where it is computed | reached by `HELD_BACK_OFF=1` **without** an emit? |
|---|---|---|
| `levels.theta_record` → `theta_prior`, `spine` | **run time**, every run | **YES** — it opens the raw files itself |
| `levels.local_record` (ρ) → `spine` | **run time**, every run | **YES** — same |
| `pools.entrant_record` | **emit time**, frozen into `pools_<year>.json` | **NO** |
| `pools.arrival_group_record` | **emit time**, frozen into the spec | **NO** |
| `pools.splinter_record` / `home_splinter_record` | emit time | **NO — and structurally inert anyway, see P2** |

`montecarlo.run_model` calls `_levels.theta_prior` and `_levels.spine` live
(`src/montecarlo.py:3829`, `:4539`); it reads the pool records out of
`data/processed/<city>/pools_<year>.json` (`src/montecarlo.py:3661`). So the
emit-time half of the quarantine stays in force no matter what the environment
says, because it is already baked into the artefact on disk.

**This is not a defect in the experiment. It is the experiment.** `MODEL-LOG`
§1.158 closes by naming the next diagnostic in terms:

> **So the test is: hold the pre-2011 data out of the POOLED records only,
> leaving θ alone, and see whether the last 6.01 returns.**

An arm of `HELD_BACK_OFF=1` **with the existing specs untouched** is exactly
that configuration: θ and ρ live, the pooled records held. The no-emit
constraint the owner imposed for tree-settling reasons happens to produce the
run §1.158 asked for. **A re-emit under `HELD_BACK_OFF=1` would destroy the
experiment**, not complete it — it would collapse the two arms back into
§1.154's already-measured full lift.

### Three further corrections to the brief

1. **"the splinter, entrant and pooled records" is wrong on the splinter third.**
   `pools.splinter_record` iterates only `SPLITS[*].measured_from` pairs — the
   COPE, EFF and MK national pairs — none of which is 1999 or 2000. The emitted
   specs' own `transition_ledger` records `unavailable: 0` for both
   `splinter_record` and `home_splinter_record` on **every** spec, against a
   non-zero `unavailable` on `entrant_record` and `arrival_group_record`. The
   quarantine costs the splinter records nothing, and cannot. §1.158's phrasing
   predates the ledger (§1.209) and was never re-checked against it.

2. **`levels.local_record` is a second run-time reader that `THETA_WINDOW` does
   not trim.** The window check lives inside `theta_record`
   (`src/levels.py:681`); `local_record` (`:775`) has none. §1.158 reasoned
   "`THETA_WINDOW` trims only the θ record, so the remainder is in the pooled
   records" — but ρ is neither trimmed by the window *nor* pooled into the
   spec. **Part of §1.158's unexplained remainder may be ρ, at run time.** This
   run can see that; §1.158's sweep could not.

3. **[AMENDED] The emit-time asymmetry has a concrete shape, and it is more
   lopsided than "seven metros held".** `pools.arrival_group_record()` returns
   29 rows; re-derived here per cycle rather than taken on report, they are
   **1 / 6 / 6 / 8 / 8** across `1999→2000`, `2004→2006`, `2009→2011`,
   `2014→2016`, `2019→2021`. **The earliest cycle is a single row, and it is
   Johannesburg's** — `_citywide_for` returns `{}` for the other seven at
   `lge2000` because `_npe_citywide_for` honours `_held_back`, and Johannesburg
   is not held. So the pooled arrival budget `_arrival_total_prior` spends is
   built on a record whose first cycle is one city. That is `pools.py:2286`'s
   *"8-way asymmetry taken on an absence"* in its actual proportions, and it is
   **emit-time, so this run does not move it** (see §5.1).

4. **[AMENDED] ⚠️ AND A SECOND, UNRELATED ASYMMETRY WILL BE MISTAKEN FOR THIS
   ONE.** At `2004→2006` and `2009→2011` the reader serves **all eight** metros
   and the record still carries **six**. The missing two are dropped by the
   `len(arr) < 3` floor inside `arrival_group_record` — Mangaung and Buffalo
   City at 2006, Mangaung and Buffalo City at 2011 — because a symmetric
   Dirichlet α is not estimable below three members. **This has nothing to do
   with `HELD_BACK`.** The floor's own comment records its measured effect on
   the budget and cites `JUDGEMENT-CALLS` §L7; it selects on the dependent
   variable and is left in place deliberately, pending its own window and its
   own pre-registration. **Anyone reading per-cycle row counts as evidence about
   the quarantine will over-attribute by two rows in each of two cycles.**
   Written down here so that this run's write-up cannot make that mistake.

5. **The gate's own citation has drifted.** `HELD_BACK`'s reason string cites
   *"a 13.65 CRPS regime effect … (MODEL-LOG 1.154)"*. §1.154's table generates
   a different figure on a different panel; the 13.65 is §1.158's table
   (unlimited against history-held-back). Not material to the run — noted so
   that whoever voids the gate quotes the right §.

**What the brief got right and I confirmed:** `HELD_BACK` holds `lge2000` and
`npe1999` for the seven non-Johannesburg metros only (`src/levels.py:266`);
Johannesburg is deliberately excluded, with the reason recorded in-place;
`HELD_BACK_OFF=1` empties the dict at import; `_npe_citywide_for` calls
`levels._held_back` and returns `{}` (`src/pools.py:3576`), and callers guard on
empty, so a quarantined metro-year is absent rather than refused.

---

## 1. The commands, and the tree they must be run on

⛔ **`data/processed/history.json` and `history.md` ARE TRACKED IN GIT AND HOLD
THE CANONICAL PANEL** installed at `251ea6f`. `compare_history` overwrites them
by default. **Both arms must redirect**, or the reference artefact is destroyed
and `data/**` is gitignored for everything that would restore the rest:

    mkdir -p /tmp/hb

**Control arm** (gate ON — the state the specs were emitted in):

    .venv/bin/python src/compare_history.py --draws 1000 \
        --json /tmp/hb/control.json --md /tmp/hb/control.md

**Treatment arm** (gate OFF at run time, specs untouched):

    HELD_BACK_OFF=1 .venv/bin/python src/compare_history.py --draws 1000 \
        --json /tmp/hb/treat.json --md /tmp/hb/treat.md

No `--seed` flag exists; both arms take `montecarlo.DEFAULTS["seed"]`, which the
manifest records. `montecarlo` re-execs under a fixed `PYTHONHASHSEED`, so hash
order is pinned without operator action. Draws are stated explicitly rather than
left to the default so the command is reproducible from this file alone.

**Run them serially, control first.** They are the same tree; running them
concurrently violates CLAUDE.md §3's one-writer rule on nothing in particular
but makes a crash ambiguous between arms.

### What must be true before either arm starts

| check | requirement |
|---|---|
| `git status --short` | **empty output.** The documentation and `src/backtest.py` work in flight must be committed or stashed first. |
| `git rev-parse HEAD` | recorded into this file's RESULT section; both arms must report the same `manifest.git_commit`. |
| `manifest.git_dirty` | **`false` in both arms.** A `true` here voids the run. |
| `.venv/bin/python src/declares.py --verify` | exit 0 — no `~` (declared and wrong) and no `✗` (undeclared). |
| `.venv/bin/python tests/run_all.py` | a full run, no `*** PARTIAL RUN`, after the last edit to the tree. |
| `find data/processed -name 'pools_*.json'` | count recorded; **no emit between the arms.** |

⛔ **NO EMIT, IN EITHER ARM, FOR ANY REASON.** `POOLS-REEMIT-QUEUE.md`'s queue is
empty and only the window remains, so there is no pending reason to emit; and an
emit taken with `HELD_BACK_OFF=1` set would write specs whose `gates_sha` records
a diagnostic state (`pools._gates_sha`) and would silently make the quarantine
unrecoverable without a second emit.

---

## 2. The population, and how I will know the referee ran

The canonical artefact at `251ea6f` declares its own population in
`manifest.population` — `n_scored_rows`, and an `excluded` list with a reason per
row. `compare_history.runnable` derives the admitted set from
`backtest.runnable_targets` minus rows with no pool spec and no γ fold; neither
test reads `HELD_BACK`. **The panel is therefore predicted invariant to the
gate**, and that is itself an assertion, not an assumption.

**Assert, in both arms:**

1. `manifest.population.n_scored_rows` is **equal in both arms** and equal to the
   canonical artefact's value at `251ea6f`.
2. `manifest.population.excluded` is **empty in both arms** — matching the
   canonical artefact. Any entry means a row was refused or *crashed*; a crash is
   recorded there by `main` and stamped with its exception.
3. **Process exit status is 0 in both arms.** `_exit_code` returns **2** when any
   city-year raised, precisely so a shrunken panel cannot be mistaken for a
   complete one. A non-zero exit voids the comparison regardless of what the
   totals say.
4. The printed header `panel: N city-year(s) scored, M the archive supports but
   this harness cannot` agrees with (1) and (2).
5. The `rows=` token inside `seat_abs_err_coherent=…/rows=N` agrees with (1) in
   both arms.

**Proof the treatment arm actually took** (this is the clause that catches a
mis-typed environment variable, which would otherwise return two identical
panels and read as "the quarantine does nothing"):

6. `manifest.env_switches.raw.HELD_BACK_OFF` is **`null` in control** and
   **`"1"` in treatment**. `src/freeze.py` registers `HELD_BACK_OFF` as the
   eighth switch and `compare_history`'s manifest carries the same block.
7. Every `manifest.pool_artefact_keys[<city>][<spec>].gates_sha` is **byte
   identical between the two arms**, and identical to the value the specs carry
   on disk. This proves **no re-emit happened** and the emit-time half of the
   quarantine stayed in force — it is the assertion that makes this a
   decomposition rather than a repeat of §1.154.
8. At least one row differs between the arms on at least one scored metric. **If
   every row is identical to 0.000, clause 6 is lying or the gate is not wired to
   the θ path**, and the run is void rather than null.

### [AMENDED] 9-10 — the contamination banner, which is about to change under us

`backtest.FITTED_ON["splinter_home"]` now carries an **empty years tuple**, so
`backtest.contaminated` (which tests `y >= target`) can no longer implicate it.
Verified here: it stays in `FITTED_ON` because `test_chain.py::test_every_
constant_the_model_falls_back_to_says_when_it_was_fitted` matches
`note_constant` call sites **bidirectionally**, so the key can be neither
deleted nor moved to another register.

9. **`splinter_home` is absent from `contaminated` on every row of BOTH arms.**
   The canonical artefact at `251ea6f` predates this change and still names it;
   **that is a difference between the canonical artefact and the arms, not
   between the arms**, and it must not be read as an effect of the gate. My §2
   clauses 1-2 assert only `n_scored_rows` and `population.excluded` against the
   canonical artefact — never `contaminated`, never `in_sample` — so nothing in
   this pre-registration breaks. `manifest.in_sample` will differ from the
   canonical artefact for this reason alone.

10. **`constants_read` and `contaminated` must not disagree, for any key, on any
    row.** The canonical artefact contains its own refutation: joburg 2021
    carries `constants_read["splinter_home"] = ["GOOD, NFP measured at 2014,
    2019"]` — both years strictly before the target, i.e. clean — while listing
    `splinter_home` as contaminated in the same object. joburg 2016 does the
    same with "NFP measured at 2014". The verdict and the evidence sit in one
    record and nothing prints them together.

⛔ **A general guard on this does NOT belong in a pre-registration, and I am
declining to put one here.** A pre-registration binds one run; this is an
invariant of every scoreboard ever written, and a clause here would be checked
once and then expire. **Nor does it belong as a regex over the note**: I wrote
that detector while preparing this file, ran it, and it reported 48 violations
of which every one I inspected was a false positive — it flags "90 θ and 9 ρ
observations **before 2011**" as a year at or after 2011. That is the
`MEMORY.md` "probe bugs look like findings" class caught in the act, and it is
also why the real defect has survived: **the years exist only as prose in the
note, and prose cannot be compared to a verdict.**

**Where it belongs, and it is a structural fix rather than a test:** the years
are already structured one layer up — `pools.emit` writes
`marker["splinter_home"]["measured_at"]` as a real list. Carry that list onto
the scoreboard row beside the prose note, then assert in `tests/test_chain.py`,
next to the bidirectional guard that already binds this key, that for every row
and every key **`max(measured_at) >= target` iff the key is in `contaminated`**.
That is `MEMORY.md`'s "assert the number, not the message" applied to the one
place where the number exists and the message is what got tested. It needs the
four-part treatment CLAUDE.md §4 requires of an absence-shaped test — state the
population, bound it two-sidedly, construct a violation and confirm the detector
goes quiet when it is reverted — and it is **not** this agent's to write.

Clause 10 stays in this file only in its narrow, one-run form: **assert the two
lists agree in both of my arms**, because my run produces two fresh artefacts
and checking them costs nothing. A disagreement does not void the comparison —
it is a defect in the banner, not in the draws — but it must be reported rather
than passed over, because P4 and P5 are read off those same rows.

---

## 3. Predictions

Each clause is falsifiable from the two artefacts alone. Directions are stated
as *treatment relative to control*; "worse" means a higher CRPS or a higher
`seat_abs_err_coherent`.

### P1 — MECHANISM: only the run-time readers move, and I can name them

Lifting the gate adds observations to `levels.theta_record` and
`levels.local_record` only. `src/freeze.py`'s `HELD_BACK_OFF` register entry
records the measured size of that widening (both records, and the extra parties
it admits) and cites `MODEL-LOG` §1.193; those counts are the prediction's
mechanism, not a prediction of this run.

The emitted specs are not re-read, so `entrant_record` and
`arrival_group_record` keep the quarantined `unavailable` counts their
`transition_ledger` already records.

**[AMENDED] Concretely, what stays frozen:** the arrival record stays at its
**1 / 6 / 6 / 8 / 8** shape in both arms, first cycle Johannesburg-only. If the
run-time lift alone recovers most of the damage (P3), it does so **while the
arrival record is still one city deep at 1999→2000** — which is the sharpest
available statement of how little the emit-time channel would then be carrying.

**Falsified if:** any spec's `gates_sha`, `transition_ledger` or mtime changes
during the run; or `manifest.pool_artefact_keys` differs between arms.

### P2 — MECHANISM, EXACT: the splinter records cannot move

`splinter_record` and `home_splinter_record` are structurally incapable of
reading a quarantined file: they read only `SPLITS[*].measured_from` pairs, and
the ledger records `unavailable: 0` for both on every emitted spec. This is a
claim about the code, not about the tree.

**Falsified if:** any spec's `marker.splinter_home.fractions` differs between
arms, or any splinter-derived band in a `--run-dir` trace moves. (It cannot — the
specs are not rewritten — so this clause is really a check that P1 held.)

### P3 — PRIMARY, DIRECTIONAL AND BOUNDED: the run-time channel carries most of the damage

§1.158's table generates the full-lift cost (unlimited against history-held-back)
and the residual its window sweep could not recover. **I predict the treatment
arm is WORSE than control on panel CRPS, by more than 3 and less than the full
effect §1.158 recorded.**

The reasoning, and the reason the band is wide at the top: §1.158 attributed the
recovered portion to θ recency and the residual to the pooled records. But ρ is a
run-time reader the window never trimmed, so **some of what §1.158 booked to the
pooled records is in this arm, not outside it.** I therefore expect this arm to
cost *more* than §1.158's θ-only figure and *less* than the full lift.

**Falsified if:** the treatment arm is **better** than control on CRPS, or worse
by less than 3, or worse by at least the full-lift figure §1.158 recorded. Each
of those falsifies a different thing, and I am saying so in advance:

* **Better, or worse by < 3** → the run-time channel is not where the damage is;
  §1.158's decomposition is wrong in the direction that matters, and the
  emit-time records (`entrant_record`, `arrival_group_record`) carry it. That
  would make a *re-emit* arm the necessary next run.
* **Worse by ≥ the full-lift figure** → the emit-time channel contributes
  nothing, the pooled half of the quarantine is doing no work at all, and seven
  of the fourteen `HELD_BACK` entries are inert decoration.

### P4 — THE NAMED ASYMMETRY: Johannesburg's rows move, although Johannesburg is not held back

`theta_record` and `local_record` both iterate `METRO_CODES` — **all eight** —
and `run_model` passes `codes` through to them. The θ and ρ records are *pooled
across metros*: a Johannesburg forecast is built from a record that includes the
other seven metros' transitions. So excluding seven metros' pre-2011 history
changes the Johannesburg forecast even though Johannesburg's own pre-2011 files
were never withheld.

**I predict every Johannesburg row moves between the arms**, on CRPS, on seats,
or both.

**[AMENDED] There are TWO asymmetries pointing the same way, not one.** The
run-time one this clause predicts (θ and ρ pooled over all eight `METRO_CODES`,
so the seven-metro hold reaches Johannesburg's forecast) and the emit-time one
§0.3 quantifies (the arrival record's first cycle is Johannesburg alone). They
are independent mechanisms on different paths with different lifetimes, and both
make Johannesburg the exception in a record that is described as excluding
Johannesburg from the exception. **Only the first is in scope for this run**;
naming the second here is what stops the write-up claiming this run addressed
it.

This matters beyond bookkeeping. The gate's in-place comment records that a
previous version which *included* Johannesburg moved KEY 4's held-out NLL at
fold 2016 — an untradeable floor moving because of the gate rather than the
data, caught by the suite. The current gate was written to fix that by excluding
Johannesburg's own files. **If P4 holds, that fix is incomplete**: Johannesburg's
files are live, but Johannesburg's *record* is still seven-eighths quarantined,
and KEY 4's folds are Johannesburg's. The gate is described as a seven-metro hold
and is in fact an eight-metro one.

**Falsified if:** all three Johannesburg rows are identical to 0.000 on both
metrics. That would mean the θ/ρ records are effectively per-city after all, and
the pooling this clause rests on does not reach the forecast.

**How I will detect it:** a per-row Δ table over all scored rows from the two
`history.json` files, with the Johannesburg rows called out separately. **Not**
from the panel total, which averages the asymmetry away — that is the mistake
this clause exists to prevent.

**⛔ And the KEY 4 floor must be re-checked in the treatment arm before anything
is concluded**, because a floor that moves with the gate is the defect the gate
already caused once. If it moves again, that is a finding about the gate
independent of every score in this document.

### P5 — THE 2011 ROWS MOVE, AND THIS IS THE SHARPEST CLAUSE

A 2011 target's records read transitions strictly before 2011, which includes
`npe1999 → lge2000` (θ) and `lge2000 → lge2006` (ρ). Both are quarantined for
seven metros. **I predict every non-Johannesburg 2011 row moves.**

This is the clause doing the real work, for the reason the polls
pre-registration's 2011 clause did: it is exact, it is checkable on a named set
of rows, and it is the one that establishes the switch turns off what it claims
to. It also runs *opposite* to that earlier prediction — 2011 rows were inert to
the poll channel and must not be inert to this one — so it cannot be satisfied by
a run that simply failed to change anything.

**Falsified if:** any non-Johannesburg 2011 row is identical to 0.000 on both
metrics.

### P6 — NUISANCE, PREDICTED SO IT IS NOT MISREAD AS A FAULT

`pools._gates_sha` hashes the *resolved* gate state, so under `HELD_BACK_OFF=1`
every spec's stored `gates_sha` disagrees with what the code would now produce,
and `montecarlo` prints `! pools_<year>.json is STALE: …` for each. **This is
correct behaviour and expected on every row of the treatment arm and on none of
the control arm.** It is a warning, not a refusal: `run_model` records
`_pools_stale` and continues.

**Falsified if:** the treatment arm does *not* print it — which would mean
`gates_sha` is not seeing the variable and clause 7 of §2 is not the proof it
claims to be.

### What I am NOT predicting

**No prediction is made against `forecast_frozen.json`, the published site, any
golden, or the canonical `history.json` as a standard of correctness.** The
canonical artefact is used in §2 only as a *declared population* to assert row
count against — never as a score to match. CLAUDE.md §1: agreement with a prior
output is evidence of nothing.

---

## 4. ⛔ THE TRAP — WRITTEN BEFORE THE NUMBER EXISTS

`HELD_BACK`'s own reason string says the hold is *"NOT because it scores worse"*,
and `levels.py` states the hazard directly: **a hold-back justified by a score is
selection of training data on the test set — the same failure as tuning a
parameter to the panel, one level up and harder to see.**

So, decided in advance and binding on whoever reads the result:

| result | what it licenses |
|---|---|
| treatment **better** or **indistinguishable** | **LIFT.** The quarantine costs nothing and has no remaining justification. Delete the entries, record the run, void the gate. |
| treatment **worse**, cause **localised and named** (a specific record, a specific metro, a specific mechanism) | **NEITHER LIFT NOR KEEP — FIX.** The honest repair is to model the regime: a covariate, a window, a weight, or a per-cycle k\*. Deleting the rows is the last resort, not the first. |
| treatment **worse**, cause **unexplained** | **NEITHER.** This is the state the gate is *already* in, and re-measuring it changes nothing. The hold continues on the same unchanged footing — an admission of ignorance with an expiry date — and the next run is the emit-time arm. |
| treatment **worse**, and that is offered as the reason to keep the hold | ⛔ **REFUSED.** This is the trap. A score measured on the panel cannot license removing data from the fit, because the panel is the test set. Any write-up that reaches for it has committed the error `levels.py` names. |

**There is no result of this run that licenses "keep the quarantine because it
scores better."** The only question this run can answer is *where the damage
lives*, which is diagnostic. Whether the data is fit to use is a question about
the data — its provenance, its reconciliation, the exchangeability of its
cycle — and it is not on this axis at all. The files are ingested and reconciled
at 100%; nothing measured here changes that.

**And one result licenses action regardless of every score above:** if P4 holds,
the gate is mis-described and the KEY 4 floor is gate-sensitive. That is a defect
in the instrument, and an instrument defect is not traded off against a panel
total.

---

## 5. What this run cannot settle

1. **The emit-time half is untouched, by construction.** The residual between
   this arm and a full lift is `entrant_record` + `arrival_group_record`, and it
   requires a re-emit under `HELD_BACK_OFF=1` — a batched operation under
   `POOLS-REEMIT-QUEUE.md`, on a settled tree, with its own pre-registration.
   **This run measures one of two channels and must be reported as such.**

   **[AMENDED] What the emit-time arm would actually move, now that its shape is
   known:** a re-emit under `HELD_BACK_OFF=1` would take the `1999→2000` cycle
   of `arrival_group_record` from **one row to up to eight** — "up to", because
   the `len(arr) < 3` floor (§0.4) may drop some of the seven on their own
   merits, and which ones is not predictable from here. That changes the
   population `_arrival_total_prior` is measured over, and therefore the pooled
   arrival budget, and therefore every seeded arrival. **It is forecast-moving
   and needs its own pre-registration**, which must be written before that emit
   and not derived from this document.

2. **θ and ρ cannot be separated in this arm.** Both lift together. A partial
   separation exists — `HELD_BACK_OFF=1 THETA_WINDOW=2` — but ρ has no window,
   so ρ cannot be isolated at all without a code change. If P3 lands high, that
   code change is the next thing worth writing.

3. **No new city-years become scoreable.** 2000 and 2006 are refused as targets
   by `backtest.runnable_targets`, and **the brief's reason is not the code's
   reason**: the code refuses them for want of a `[structure.by_year.<year>]`
   council size in `cities/<slug>.toml` and a `montecarlo.GAMMA_FOLD` entry.
   Separately, IEC Seat Calculation Detail exists in `data/raw/elections/_source/`
   for **Johannesburg 2016 and 2021 only** — so seat-level ground truth is thin
   across the whole panel, not specially absent at 2000 and 2006. Either way this
   run scores the same rows as the control.

4. **1999 is an approximated metro footprint for all eight metros.** No metro
   existed before the December 2000 demarcation, so `npe1999_approx_<CODE>` is a
   reconstruction. **Correcting the brief precisely:** the files *do* carry a
   `Ward` column, but it is **empty on every row** — 2000 carries real ward codes
   and 1999 carries none. A blank ward parses as the key `""` rather than
   raising, so anything ward-level built from 1999 aggregates silently into one
   bucket. Nothing in this run reads 1999 at ward level, but the hazard belongs
   in the record. `npe1999` also lacks a `BallotType` column, which
   `_npe_citywide_for` handles deliberately (`row.get("BallotType") in (None,
   "", "PR")`).

5. **k\* for the 2000 cycle is still not measured.** The gate's stated voiding
   condition names it; §1.158 replaced it with the pooled-record test this run
   performs half of. **This run does not void the gate on its own terms** — it
   supplies the half §1.158 asked for, and the write-up must say which condition
   it satisfied and which it did not.

6. **[AMENDED] It cannot separate the quarantine from the `len(arr) < 3`
   floor**, and no run of this shape can. Both thin the arrival record, both
   thin it asymmetrically across metros, and only one of them is the gate. The
   floor is emit-time and untouched here, so it is held constant between the
   arms and confounds nothing *within* this run — but any statement about "the
   arrival record's coverage" drawn from this run must name both. §L7 owns the
   floor; this document does not.

7. **A panel total cannot arbitrate a per-row effect.** P4 and P5 are per-row
   clauses and must be scored per row. A run reported only as a total will
   average out exactly the asymmetry this pre-registration was written to expose.

---

# RESULT — to be written after both arms, predictions above not to be edited

*(empty; the run has not been taken)*

Record here: both `manifest.git_commit` values, `git_dirty`, draw count, seed,
`n_scored_rows`, `population.excluded`, both exit codes, both
`env_switches.raw.HELD_BACK_OFF`, and the `gates_sha` equality check from §2
clause 7 — **before** any score. Then the per-row Δ table, the Johannesburg rows
called out, the 2011 rows called out, and a scoring table with one verdict per
clause including what was falsified.
