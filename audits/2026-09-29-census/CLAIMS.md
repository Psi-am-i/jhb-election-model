# F10 mechanism census — the claims, written before any mutation runs

Scope (owner, 2026-09-29): the mechanisms F3 and F5 added. PUBLISHING-BACKLOG
§15 defines the method: per claimed mechanism, **switch it off**, **nudge it**
in a stated direction, and **disable its guard**; each mutation is read
through the `--run-dir` trace, and the first stage that changes must be the
stage the claim names. Nothing below is edited after a run; a claim that
fails is scored as failed.

**Fixtures.** Two targets, one seed (20261104), 300 draws per run:

* **B = mangaung 2016** — a backtest target whose fitting year (2011)
  triggers F3's hold at the turnout level.
* **J = joburg 2026** — the live target, where both declared mergers fire.

Emit-time mechanisms are exercised by building the spec **in process**
(`pools.emit_pools`, lineage template stubbed, nothing under `data/`
written) and running `montecarlo.run_model` on it directly, the method of
§1.269 and §1.275. The trace stages are those `run_model` records: `00_target`,
`01_scenario_in`, `02_pools_artefact`, `03_roster`, `10_theta_prior`,
`20_spine`, `30_centres`, `40_draws`, `41_guards`, `42_pr_share_draws`,
`43_ward_share_draws`, `44_seat_draws`, `45_delivered`.

"First changed stage" compares each stage's JSON against the unmutated run at
the same seed. **Pre-registered limit:** §1.275 found that a change to one
pool vector moves every party's draw, so for a spec-level mutation the
prediction is about the FIRST changed stage, not about which parties move
after it.

---

## F3 — a pool silenced at a nested level is held at the city's rate

### C1. `_nest_holding_silent` holds a silenced pool (`pools.py`, JUDGEMENT-CALLS §L14)

**Claim.** In a fitting year where a nested solve drives a populated pool's
rate to 0.0, the pool is held at the city's own rate and the rest re-fitted,
so the emitted spec carries that pool. At B, the Indian/Asian pool is in
`pools` with registered > 0 and a central turnout > 0.

| mutation | what is done | prediction |
|---|---|---|
| off | replace with the free fit (`_nest`, no hold, `silenced` reported empty) | B's emit **refuses** (the memberless-pool guard, C3). No run happens; that refusal is the finding "live" |
| nudge | the held value × 1.10 | B's spec: the Indian/Asian pool's central turnout **rises**; at least one other pool's central turnout **falls** (the re-fit gives back the votes). First changed run stage: **`02_pools_artefact`** |
| guard | `HoldCascadeRefused` not raised (loop exits with the cascade unheld) | `test_pool_bounds` fails (the cascade tests on a constructed table). No change at B or J: the cascade occurs zero times on the panel (§1.275) |

### C2. The cascade re-hold (`_nest_holding_silent`'s loop)

**Claim.** A re-fit that silences a second pool holds it too. On the real
panel it never fires (zero of 72 solves, §1.275), so it is live only on a
constructed table.

| mutation | what is done | prediction |
|---|---|---|
| off | one hold pass, no loop | **no change** at B or J (inert on the panel, as claimed); `test_pool_bounds::test_a_refit_that_silences_a_second_pool_holds_it_too` **fails** |
| nudge | not applicable: the loop has no magnitude | — |
| guard | see C1's guard | — |

### C3. `emit_pools` refuses a pool with no members (`pools.py`, prereg P1)

**Claim.** A spec that would declare a pool and omit it is not written.

| mutation | what is done | prediction |
|---|---|---|
| off (= disable the guard) | restore the old `continue` | with C1 also off, B's spec is written **without** Indian/Asian and `_p1_violations` reports it. With C1 on, **no change** anywhere (nothing reaches the guard). `test_pool_bounds` P1 predicate tests stay green (they test the predicate, not the guard): **the guard is unguarded by the suite** unless a test calls `emit_pools` on a silenced table |

### C4. The run-time recompute of the fitting year's composition (`montecarlo.py`, `_vd_pool_composition`)

**Claim.** `run_model` rebuilds `pool_counts(fitted_on)` at run time, so F3's
hold reaches the VD pool composition independently of the spec. At B it acts
after the spec is read.

| mutation | what is done | prediction |
|---|---|---|
| off | `_vd_pool_composition` built from the free fit (no hold) for B | stages `00`–`30` **unchanged**; the first changed stage is **`40_draws` or later** |
| nudge | the held value × 1.10 inside the run-time recompute only (spec untouched) | as off: nothing before `40_draws` moves |
| guard | none | — |

---

## F5 — a merger moves `retention × predecessor` to the partner on the ballot

### C5. `apply_mergers` on the national baseline (`montecarlo.run_model`, JUDGEMENT-CALLS §O1)

**Claim.** At J, GOOD → RISE and FORUM_4_SERVICE_DELIVERY → ASA each move
`MERGER_RETENTION × P` of the 2024 baseline, recorded in
`scenario["_mergers"]`. The baseline feeds the θ prior first.

| mutation | what is done | prediction |
|---|---|---|
| off | `pools.MERGERS = ()` for the run only (the spec keeps its blended vectors) | first changed stage **`10_theta_prior`**; RISE's `20_spine` level **falls** to 1.4411% (§1.275's r = 0 value) |
| nudge | `MERGER_RETENTION` 0.75 → 0.85 for the run only | first changed stage **`10_theta_prior`**; RISE's spine level **rises** by the factor (1 + 0.85·P/B) / (1 + 0.75·P/B) with P = 0.2251%, B = 1.5569%, to within 1e-9 relative; ASA's spine level rises; no other party's spine level rises |
| guard | `MergerRefused` not raised when two partners are on the ballot and one is off | `test_roster_aware_baseline` fails; no change at J (no such declaration) |

### C6. `apply_mergers` on the preceding local result (`prior_pr_share`)

**Claim.** The PR base the blend reads takes the same transfer where the
successor holds a local record. At J, RISE has none (no 2021 local ballot),
so only FORUM_4 → ASA acts here.

| mutation | what is done | prediction |
|---|---|---|
| off | skip this one call | first changed stage **`30_centres`**; ASA's centre changes; RISE's centre does **not** change |
| nudge | not separately applicable (it reads the same `MERGER_RETENTION` as C5) | — |
| guard | the "never creates a record" rule: allow a successor with no local record to receive | RISE's `30_centres` value **changes**; `test_roster_aware_baseline::test_a_merger_never_creates_a_record_the_successor_lacks` fails |

### C7. The merger vector blend in `emit_pools` (`blend_merger_vectors`)

**Claim.** The successor's pool vector becomes the mass-weighted blend of its
own and its predecessor's; this is what differs between J's spec with and
without mergers.

| mutation | what is done | prediction |
|---|---|---|
| off | skip the blend (build J's spec without it) | spec: RISE's and ASA's `members` weights change, nothing else in `pools`; run: first changed stage **`02_pools_artefact`** |
| nudge | blend at twice the moved mass | RISE's Coloured weight moves further in the same direction as off → on (§1.275: 0.072 → 0.133 at r = 0.75); first changed stage **`02_pools_artefact`** |
| guard | the running mass: blend each merger against the pre-merger share alone | **no change** at J (the successors are distinct, §1.278); `test_roster_aware_baseline::test_two_mergers_into_one_successor_give_the_mass_weighted_average` fails |

### C8. `apply_mergers` in `theta_residual` (Key 4's baseline)

**Claim.** Inert at every held election, because no declared merger predates
one; present so the day one does, Key 4 measures the baseline the model runs.

| mutation | what is done | prediction |
|---|---|---|
| off | skip the call | **no change** at B (a held election); `test_roster_aware_baseline::test_every_consumer_the_spec_names_calls_apply_mergers` fails |
| nudge / guard | not applicable | — |

---

## Output

Three lists, read before `build_site.py --publish`:

* **dead** — an "off" that changed nothing where the claim says it is live;
* **wrong-way or wrong-stage** — a nudge in the wrong direction or of the
  wrong size, or a first changed stage other than the one claimed;
* **unguarded** — a disabled guard that no test notices.

A prediction above that is itself "unguarded" (C3) is recorded as claimed and
still listed.
