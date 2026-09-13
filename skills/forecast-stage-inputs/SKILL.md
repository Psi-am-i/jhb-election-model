---
name: forecast-stage-inputs
description: Become a narrow expert on the INPUTS segment of this forecasting model's stage trace — 00_target, 01_scenario_in, 02_pools_artefact and 03_roster. Use when auditing what entered a run, checking that no input post-dates the election being forecast, reading or writing tests/test_stage_inputs.py, diagnosing a trace directory, changing what run_model records at those four stages, or investigating a defect whose symptom appeared downstream (θ, the spine, the centres, the draws) and whose cause might be an input. Written for someone who knows forecasting and does not know this codebase.
---

# The inputs segment of the trace

`src/montecarlo.py::run_model` emits every stage as JSON when given
`--run-dir`. Thirteen stages, in pipeline order:

```
00_target · 01_scenario_in · 02_pools_artefact · 03_roster     ← THIS SKILL
10_theta_prior · 20_spine · 30_centres
40_draws · 41_guards · 42_pr_share_draws · 43_ward_share_draws · 44_seat_draws · 45_delivered
```

Generate one:

```
.venv/bin/python src/montecarlo.py --city joburg --target 2021 --run-dir /tmp/t
.venv/bin/python src/montecarlo.py --city joburg --target 2026 --run-dir /tmp/t26   # the live forecast
```

Tracing is **opt-in and inert**: with no `--run-dir` every `Trace` method returns
its argument and writes nothing, and `tests/test_chain.py` asserts a traced run
is byte-identical to an untraced one. `main` additionally **refuses to publish**
when `--run-dir` is given — a diagnostic run does not rewrite
`data/processed/*`. (It used to. Two diagnostic runs replaced the shipped
5,000-draw forecast on 2026-08-28 and a cartogram test went red an hour later.)

The question this segment answers, and the only one:

> **Is what entered the model what we think it is, and is all of it available
> before the target election?**

Everything downstream is a transformation of these four payloads. A defect here
is invisible where it is introduced and expensive where it is found.

---

## The four stages, field by field

### `00_target` — which election, and how big

Written at the very top of `run_model`, before anything is read.

| field | type | meaning |
|---|---|---|
| `city` | str | the city **slug** (`joburg`, `tshwane`, …). Deliberately not the `City` object, which `repr()`s to ~4 kB of config. |
| `year` | str | the target election year, a key of `cityconfig.CALENDAR`. **A string, always** — see the traps. |
| `council` | int | total council seats for that city in that year, from `cities/<slug>.toml` `[structure.by_year.<year>]`. Sets the module global `COUNCIL`. |
| `draws` | int | Monte Carlo sample count (`scenario["draws"]`). |
| `seed` | int | RNG seed (`scenario["seed"]`); the whole of reproducibility. |

`council = wards + list_seats` holds for all eight metros at every LGE on file,
and `wards = ceil(council/2)` — both statutory. Neither `wards` nor
`list_seats` is recorded here; re-derive from `cityconfig`.

**The cutoff lives here and is not written down.** `Target.date` is polling day,
and the city's own `[structure].election_date` overrides the calendar's when it
names the same year — which is the case for the not-yet-held 2026 target, whose
announced date can move. `polling.usable_for` admits a poll only when its
machine-readable `fieldwork_end` precedes `target.date`. **No stage records that
date**, so two runs either side of a date change are indistinguishable in the
trace while the admitted poll set differs. See *What I could not check*.

### `01_scenario_in` — the settled lever set

`{k: v for k, v in scenario.items() if not k.startswith("_")}`, written
immediately after `00_target` and **before any input is loaded**.

* The key set is exactly `montecarlo.DEFAULTS` — 35 keys as of 2026-09-13.
* Values are post-resolution: `DEFAULTS` → `--config` file → `--set` →
  `--draws`/`--seed`, with `apply_city` having first reset `DEFAULTS` to
  `_PRISTINE_DEFAULTS` and written the city's own `[judgements.scalars]` over
  it. (The reset was missing until 2026-08-18, so a city inherited whatever the
  previous city in the loop declared, and which one depended on iteration
  order.)
* `_`-prefixed keys are the run's own bookkeeping (`_delivered`,
  `_constants_read`, `_pools_stale`, `_roster_state`) and are filtered out here.
  Most are set *after* this stage anyway.
* `overhang_rule` is **statute**, not a lever: `montecarlo.STATUTORY_VALUES`
  pins it to `"deduct"` and `load_scenario` refuses any other value without
  `--counterfactual`. A trace carrying `"expand"` is an analysis run and must
  never be read as the forecast.

Every `DEFAULTS` key sits in **exactly one** of `backtest`'s four provenance
registers, and which one is a statement about *evidence*, not importance:

| register | claim |
|---|---|
| `FITTED_ON` | read an election result; consumption **proved** by `note_constant` |
| `FITTED_ON_UNINSTRUMENTED` | read an election result; consumption **not** instrumented |
| `PROVENANCE_UNSETTLED` | nobody yet knows which of the two |
| `NOT_FITTED` | reads no election result, with the reason |

The first three carry year tuples. A lever is *implicated* at target *T* when
any listed year ≥ *T*.

### `02_pools_artefact` — which pool spec was read

Written only inside `if not scenario.get("pools")`, i.e. only when `run_model`
loads the spec itself.

| field | type | meaning |
|---|---|---|
| `path` | str | the spec read, always `<city.processed>/pools_<target>.json`. Johannesburg keeps the legacy bare `data/processed/` root. |
| `artefact_key` | dict | nine members; the delivery proof. See below. |
| `stale_reason` | str \| None | `None` means the spec still matches live code and config. **A sentence, not a boolean** — the useful part is *which* thing moved. |
| `fitted_on` | str | the election year the pool **ratios** were fitted on. `emit_pools` resolves it as `from_year or target.previous_lge or target.year`. |

`artefact_key` (`pools.artefact_key`, schema 2):

| member | what it hashes |
|---|---|
| `schema` | the key's own shape (int, currently `2`) |
| `city`, `target` | identity; `stale_reason` compares these with a better message |
| `pools_sha` | `src/pools.py`, hashed over its **AST with docstrings stripped**, so comment edits do not cry wolf |
| `config_sha` | every `config/*.toml`, name and content |
| `cities_sha` | every `cities/*.toml` — a **panel** input: adding a ninth city moves the turnout band of all existing specs |
| `deps_sha` | `src/{parties,cityconfig,ingest_lge,levels}.py` |
| `judgements_sha` | `judgements/<slug>-<year>.toml`, hashed as parsed payload |
| `gates_sha` | the resolved state of `HELD_BACK_OFF` and `THETA_WINDOW` — env vars that change what is read and that an AST hash cannot see |

Every `*_sha` is `sha256(...).hexdigest()[:16]` — sixteen lowercase hex
characters. `montecarlo` is **deliberately excluded** from `deps_sha`
(`read_ward_crosswalk` is a genuine emit dependency, but the module changes most
working days and hashing it would mark all 26 specs stale continuously).

A spec whose key does not match live code is **STALE**: `run_model` prints a
warning and **continues**. Nothing refuses. The trace is where that survives.

### `03_roster` — who is on the target's ballot

| field | type | meaning |
|---|---|---|
| `state` | str | `"published"` or `"not_yet_held"` |
| `size` | int | number of parties on the target's ballot (`len(_roster)`) |
| `dropped` | list[str] | parties removed from the baseline because they did not stand; sorted |

`roster_for_target` has **three** outcomes and only two are return values:

* `published` — `CALENDAR[year].results` is a template, the file was read, the
  off-ballot drop ran.
* `not_yet_held` — `CALENDAR[year].results is None`. No result file can exist,
  so the drop is disabled **knowingly**. This is the live 2026 forecast.
* *unreadable* — raises `SystemExit`. Never reaches the trace.

The drop removes parties present in the previous NPE baseline that are not on
this local ballot, **before** θ, ρ, the spine, the pool fit or the seeds see
them. Johannesburg 2021: 13 of 57 — ≈0.42% of the baseline, of the order of one
invented seat, funded out of the parties ranked 4th to 12th.

**The discriminator is the results template, not the clock.** A date comparison
would flip state on polling day and refuse the next target days before anyone
had ingested a file.

⚠️ **`len(dropped)` is not bounded by `size`.** They count different
populations: `dropped` is parties in the **previous NPE** baseline that did not
stand locally, `size` is parties on **this LGE's** ballot. Across the 24-city-year
panel the ratio runs 0.15 (Cape Town 2011, 5/34) to 1.00 (Buffalo City 2011,
9/9). Johannesburg 2021 is 13/57.

---

## The invariants, and why each exists

They live as pure predicates in `tests/test_stage_inputs.py`
(`offences_target`, `offences_scenario_in`, `offences_pools_artefact`,
`offences_roster`, `offences_across`) and each returns `(id, detail)` pairs.
`INVARIANTS` in that file is the full catalogue with its rationale; the
condensed reasoning:

**`00_target`.** The field set must be exact — a field that quietly disappears
takes its invariant with it. `year` must be a **string**: every cutoff
comparison in this repository is a lexicographic string compare on a
zero-padded year, and an int does not raise, it compares wrong. The year must be
in the calendar and must be an **LGE** — this model forecasts a metro council.
`council` must equal what `cities/<slug>.toml` gives for that city-year: the
active city is process-global and the module's `COUNCIL` is set from the target,
so a disagreement is the city-namespacing class (a Tshwane run reaching
Johannesburg's outputs). `draws > 0`; `seed` an int.

**`01_scenario_in`.** The key set must equal `DEFAULTS`, in both directions — a
missing key means a lever was consumed from somewhere the artefact does not
record; an extra one means a city toml or a scenario file invented a lever,
which `apply_city` accepted until 2026-08-22. Every key must sit in exactly one
provenance register: 27 of 35 reached neither list as recently as this summer,
and an unregistered lever cannot be audited for leakage at all. `overhang_rule`
must be `"deduct"`. `seed` and `draws` must agree with `00_target` — they are
read from one dict at one moment, so a disagreement means the trace directory
holds files from two runs.

**`02_pools_artefact`.** `stale_reason` must be `None`. `artefact_key` must be
present (a spec emitted before keys existed cannot be shown to match the running
code) and its member set must be **exactly** the nine the code produces — a
field in the stored key that the code no longer produces is the register→code
blindness this project calls its worst class, and `pools.stale_reason` was bitten
by exactly that. Schema must be the expected int. Every non-identity member must
be sixteen hex characters: a blank hash cannot differ from the next one, so
staleness would pass for ever, silently. The key's `city`/`target` must match the
run. The path must be `pools_<target>.json`.

⛔ **And the cutoff: `fitted_on` must be strictly before the target year.**
Nothing in `src/` checks this. `emit_pools` takes `from_year or
target.previous_lge or target.year`, so a `--from-year` at or after the target,
or a target with no previous LGE, fits the pool ratios on the target's own
result. All 26 specs on disk are clean today (`2006→2011`, `2011→2016`,
`2016→2021`, `2021→2026`).

**`03_roster`.** `state` must be one of the two. `published` ⟹ `size > 0`:
**this is the positive control, and it is the defect exactly.** An empty roster
is the value meaning *drop nobody*, and it used to be indistinguishable from an
election not yet held, so any fault inside `contesting_parties` — a renamed
`sPartyName` column, a moved archive file, a wrong working directory (the path
it builds is relative) — silently disabled the drop. `not_yet_held` ⟹ `size ==
0` and `dropped == []`. `dropped` sorted and unique. And the state must agree
with the calendar: `CALENDAR[year].results is None` ⟺ `not_yet_held`, because
that is the same condition `contesting_parties` keys its legitimate empty return
on, so the two cannot honestly disagree.

**Across the four.** All four stages present. If `02` is missing, the caller
supplied `scenario["pools"]` itself and **no staleness check ran**. `pools` must
appear in `_index.constants_read` — that is `note_constant` firing in the same
branch that writes `02`, and without it `in_sample_banner` reports the run clean
on the largest input it has. And `45_delivered["pools"]` must carry the same
artefact key and the same `fitted_on`: they are built from one dict three lines
apart, which means they are two copies of one number and one of them will go
stale.

---

## The traps

**1. `01_scenario_in` records `pools: {}` on every run.** It is written *before*
the spec is loaded; `scenario["pools"]` is assigned about sixty lines later. So
the stage that is supposed to be the record of the lever set records the
dominant input at a value it was never consumed at. `pools` is a `FITTED_ON` key
implicated at 2011, 2016 and 2021 — **a cutoff audit reading the lever set alone
clears the single largest input the model has.** What makes it visible is
`02_pools_artefact.artefact_key` and `_index.constants_read`, which is why
`implicated_levers()` needs `_index`. Do not "fix" this by moving the `put` call
without checking every consumer: a 70-party dict inline in the trace is a large
payload, and `02` is the better record.

**2. A trace directory is a bag of files, not a run.** Nothing stamps them with a
run id. The agreement checks (`seed`, `draws`, `city`/`target` in the artefact
key, the `pools_<year>.json` basename) are what make a mixed trace detectable.

**3. `run_model` continues on a stale spec.** It prints `! pools_<year>.json is
STALE: <reason>` and carries on. `scenario["_pools_stale"]` travels into
`forecast_summary.json`, and `02_pools_artefact.stale_reason` into the trace.
Nobody refuses. Treat a non-null `stale_reason` as *this run is not evidence*.

**4. `stale_reason` fails CLOSED and says so.** If the check itself raises, the
reason becomes `"staleness could not be determined (…) — treat this spec as
UNVERIFIED"`. That string is not `None`, so the invariant fires. Good.

**5. `FITTED_ON["splinter_home"] = ("2019", "2024")` over-declares.** At target
2021 the register implicates it, while the emitted 2021 spec's own
`splinter_home.measured_at` is `["2014", "2019"]` — both before the target,
because `emit_pools` passes `home_cutoff = target.year`. The banner is therefore
noisier than the artefact warrants. Conservative direction, so not a leak; but
the spec records the precise answer and the banner does not read it.
`02_pools_artefact` does not carry `splinter_home` at all — only
`45_delivered["pools"].who` does, as a prose string.

**6. `pools_2026_simulation.json` exists** — a `split_bloc` spec whose
`artefact_key` says `joburg`/`2026`, identical to the published one's identity.
`stale_reason` would not distinguish them. The spec carries a `simulation_only`
marker; **`02_pools_artefact` does not propagate it.** Only `path` tells them
apart, and `run_model` constructs `path` from the target, so the discriminator
holds only while nobody copies a file over `pools_2026.json`.

**7. `gates_sha` is the hole the code hash cannot see.** `HELD_BACK_OFF=1` takes
`levels.HELD_BACK` from 14 entries to 0 and leaves `deps_sha` byte-identical.
`gates_sha` records the resolved env state instead. A spec emitted under a
diagnostic gate is *recorded as one*, not refused.

**8. The two registers are read differently, deliberately.** A `FITTED_ON` key is
implicated only when the run's read log names it (consumption is instrumented);
an uninstrumented or unsettled key is implicated on **presence**, because
nothing records its read. That asymmetry is `backtest._grade`'s. Reproduce it;
do not "improve" it — merging the two claims a proof that does not exist.

---

## What I could not check, and why

* **The date.** No stage records `target.date`, the actual cutoff for polls and
  for anything else dated. The city config can override it for a not-yet-held
  election. *Fix: add `"date": target.date.isoformat()` to `00_target`, and the
  poll-admission cutoff becomes checkable from the trace.*
* **The census behind the pools.** `FITTED_ON["pools"]` declares the pool
  *composition* as Census 2022 — which post-dates every target before 2026 and
  is accepted as a covariate ("it says who lives in a ward, not how they
  voted"). `02_pools_artefact` records `fitted_on` (an election) and not the
  census year, so the trace cannot check that declaration. It is in
  `config/dimensions.toml` and therefore inside `config_sha`, but only as a
  hash.
* **Who is on the roster.** `03_roster` records `size` and `dropped`, not the
  roster itself, so "these 13 were dropped *because* they are not on the ballot"
  is not verifiable from the trace. 57 names is a small payload; recording them
  would close it.
* **Whether a lever was overridden.** `01_scenario_in` records settled values,
  not their route — `DEFAULTS` vs city toml vs `--config` vs `--set` are
  indistinguishable. Compare against `montecarlo.DEFAULTS` after
  `apply_city(city)` to recover the diff.
* **Whether the spec's *inputs* moved.** `artefact_key` is deliberately not a
  hash of the census and roll files — too large, too numerous, and a wrong-city
  input is caught by `pools.py` refusing the fallback by name instead.
* **Nothing, on the panel — but the panel is reachable.**
  `src/compare_history.py --run-dir /tmp/t` writes **one trace per city-year**
  into `/tmp/t/<city>-<year>/`, so every invariant here can be run over all
  sixteen at once (~3 min). Do that after any change to `pools.py`, to
  `cityconfig.CALENDAR`, or to a `cities/*.toml`. It is not wired into the
  suite, because the suite must not depend on a full panel run.

---

## Working on this segment

* Run the module alone: `.venv/bin/python tests/test_stage_inputs.py`
  (~12 s; it builds its own 24-draw trace).
* Check an existing trace:
  `JHB_STAGE_TRACE=/tmp/t .venv/bin/python tests/test_stage_inputs.py`.
* **The module must be listed in `tests/run_all.py`'s `MODULES`** or it is not
  collected, and `test_every_test_module_is_collected` turns the suite red.
* Adding an invariant means adding **three** things: an entry in `INVARIANTS`
  (the id and its rationale), the check inside a predicate, and an entry in
  `CORRUPTIONS` (a constructed payload that must trip it).
  `test_the_corruption_table_covers_every_declared_invariant` fails on either
  half, in both directions.
* Adding a **field** to a stage means updating the field-set invariant — they
  are deliberately exact rather than "at least", so a new field is a failing
  test and a conscious decision rather than an unchecked payload.
* `ARTEFACT_KEY_FIELDS` is a third copy of a set that already exists twice in
  `pools.py`. It is justified only by
  `test_the_artefact_key_field_set_matches_the_code`, which compares it with
  `pools.artefact_key()` in both directions. Do not add a fourth copy.
* ⛔ `data/processed/pools_*.json` is precomputed and shared. Changing
  `src/pools.py` does nothing until you re-emit, and re-emitting moves the
  baseline of every measurement anyone else is taking. See `CLAUDE.md` §3 and
  `POOLS-REEMIT-QUEUE.md`. **Nothing in this segment requires a re-emit.**
