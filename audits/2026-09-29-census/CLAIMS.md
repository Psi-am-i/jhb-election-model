# F10 mechanism census — the claims, written before any mutation runs

**Revised 2026-09-29 on the R3 review and its fix check (`R3-findings.md`),
before any mutation has run.** The version at `335a721` is superseded: it named `02_pools_artefact`
for spec-level mutations, a stage whose payload cannot see spec content; it
named the wrong stage for C6; two predictions held whatever the mutation did;
and two mechanisms had no claim. Nothing below is edited after a run.

Scope (owner, 2026-09-29): the mechanisms F3 and F5 added.
PUBLISHING-BACKLOG §15: per mechanism, **switch it off**, **nudge it** in a
stated direction, **disable its guard**; the first changed stage must be the
one claimed.

## Method, fixed in advance

**Fixtures.** One seed (20261104), 300 draws, `trace_detail` on (stages
42–44 are written only then):

* **B = mangaung 2016**: its fitting year (2011) triggers F3's turnout-level
  hold, its seeds reach the run-time composition, and the 2006 registration
  hold reaches it through `registration_series`.
* **J = joburg 2026**: both declared mergers fire.
* **K = constructed**, for C8 only (below).

**Isolation.** Every run is made from a scratch root that mirrors the
repository with `data/processed` an APFS clone (`census.py make_root`).
Both the BASE and the mutated spec are emitted in process, in fresh
processes, so `_PANEL_SPREAD_CACHE` and the `theta_residual` memo cannot carry
one emit's result into another (R3 F9). A spec is written exactly as
`emit_pools` writes it (`sort_keys=True`): the draw follows the members' key
order (found building the harness).

**What is compared.** Two things, in order:

1. **The spec diff** (emit-time mutations): which fields of the emitted spec
   change. This is the discriminating evidence for a spec-level mutation.
2. **The trace**: the first stage whose JSON differs, ignoring `path`.
   `02_pools_artefact` records only the spec's path, key, stale reason and
   fitting year (montecarlo.py:3953), so **no spec-content change can appear
   there**; spec members, turnout and alpha first reach the trace at
   `40_draws` (seed VD placement and the drawer). A spec change that moves
   `seeds` moves `base_city_d` and appears at `20_spine` first; which applies
   is decided by the spec diff's `seeds` field, as pre-registered per claim.
   §1.275: any spec-vector change moves every party's draw, so `40_draws`
   changing is weak evidence on its own.

**Guards, measured.** Every mutation is applied as an exact SOURCE edit in
a scratch copy of `src/` and `tests/` (`census.py`), and these test modules
are run against it: `pool_bounds`, `pool_conservation`,
`roster_aware_baseline`, `theta`, `chain`. A `pools.py` edit moves
`pools_sha`, which would fail `test_chain`'s current-key test on every spec
(R3 fix check N3); each scratch root therefore stamps its clone's specs with
its own code hash, and a **CONTROL** mutant (an inert code edit to
`pools.py`) must produce no test failure beyond the base's own. "Guarded"
means a test fails that fails in neither the base nor the control. The claim
is only about these modules, and says so. Every "off" is written so the code
still runs: an assignment is replaced, never deleted (N1, N2).

---

## F3 — a pool silenced at a nested level is held at the city's rate

### C1. `_nest_holding_silent` (pools.py:1027, JUDGEMENT-CALLS §L14)

**Claim.** A populated pool driven to rate 0.0 by a nested solve is held at
the city's rate (`_uninformed_rate`) and the rest re-fitted, so B's spec
carries Indian/Asian with registered > 0 and central turnout > 0.

| mutation | exactly | prediction |
|---|---|---|
| off | `silenced` forced empty: the free fit is returned | B's emit **refuses** (C3's guard). *Inferred* from §1.269's old-code result, not re-derived; the path that would break it is an arrival vector carrying Indian/Asian weight > 1e-4 (pools.py:6316). If the emit does not refuse, that is recorded as a finding |
| nudge | the held value × 1.10 | spec: B's Indian/Asian **central turnout = the unmutated held value × 1.10** (turnout_band's centre is the fitting-year rate, and `_nnls` resets held coordinates exactly), to 1e-9 relative; at least one other pool's central turnout **falls**. Trace: first changed stage **`20_spine` if the spec diff shows `seeds` changed, else `40_draws`** |
| guard | delete `raise HoldCascadeRefused` (pools.py:1064), so the loop holds every pool and exits | `test_pool_bounds` **fails** (`test_a_refit_that_silences_a_second_pool_holds_it_too`, part d). At B and J: no change *on the fitting years §1.275 scanned*; the emits also call `pool_counts` on panel years and national years that were never scanned (R3 F8), so a change there is recorded as a finding, not an error |

### C2. The cascade re-hold (the loop in C1)

**Claim.** Live only on a constructed table; zero cascades on the 72 solves
§1.275 scanned.

| mutation | exactly | prediction |
|---|---|---|
| off | one hold pass, no loop | spec diff at B and J **empty** on the fitting years §1.275 scanned; a change from an unscanned panel or national year is a finding, not an error. `test_pool_bounds::test_a_refit_that_silences_a_second_pool_holds_it_too` **fails** (parts b and d) |

### C3. `emit_pools` refuses a memberless pool (pools.py:6379)

| mutation | exactly | prediction |
|---|---|---|
| guard off | the refusal replaced by `continue` | with C1 on: spec diff at B **empty** (nothing reaches it). With C1 also off: B's spec written **without** Indian/Asian, `_p1_violations` non-empty. Test modules: **none fails** — unguarded, as stated |

### C4. The run-time composition (`_vd_pool_composition`, montecarlo.py:3990)

**Claim.** `run_model` rebuilds `pool_counts(fitted_on)` at run time, so F3
reaches the VD composition independently of the spec. At B it acts through
the seeded parties' VD shares (B has seeds).

| mutation | exactly | prediction |
|---|---|---|
| off | the run-time `pool_counts` made with the hold off (spec untouched) | first changed stage **exactly `40_draws`**; stages 00–30 identical |
| nudge | the run-time held value × 1.10 (spec untouched) | first changed stage **exactly `40_draws`** |

### C9. The panel spread skips held pools (pools.py:3071) — *added on R3, narrowed on its fix check*

**Claim.** A transition to or from a held pool is not a movement, so
`panel_turnout_spread` skips it. Every held cell on the panel is
Indian/Asian, so the skip removes Indian/Asian transitions only.

| mutation | exactly | prediction |
|---|---|---|
| off | the `if i in ia or j in ib: continue` removed | **discriminating:** `panel_turnout_spread(cfg, before=…)` called read-only in a fresh process: the Indian/Asian entry **changes** at `before="2016"` and at `before="2026"`; no other pool's entry changes unless it is on the pooled fallback (fewer than `_OWN_EVIDENCE_MIN_OBS` own moves), which is reported. **Spec:** an Indian/Asian `turnout` band end changes at B or J only where the panel value exceeds the city's own range (`turnout_band`'s `max(measured, own)`); `registered` and `members` do not change. Where a band changes, first changed stage **`40_draws`** |
| guard | none exists | test modules: expected **none fails** beyond the control — unguarded |

---

## F5 — a merger moves `retention × predecessor` to the partner on the ballot

### C5. `apply_mergers` on the national baseline (montecarlo.py:4067)

**Claim.** At J each declared merger moves `MERGER_RETENTION × P` of the 2024
baseline; the baseline reaches the θ prior first through RISE's and ASA's
size-dependent entries (`size_centre`, `sd_for`). **Only RISE isolates C5**:
ASA also receives C6's local transfer.

| mutation | exactly | prediction |
|---|---|---|
| off | the call's result replaced by its input (`_mergers = []`, baselines unchanged; C6 left on) | first changed stage **`10_theta_prior`**; if 10 is unchanged, **`20_spine`**, and that is recorded, not failed (R3 F6). RISE's spine level **= 1.4411% ± 0.00005pp** (§1.275's r = 0) |
| nudge | `MERGER_RETENTION` 0.75 → 0.85 (both calls read it, and the emit's blend) | first changed stage **`10_theta_prior`** (else `20_spine`, recorded). RISE's spine level **rises by the factor (1 + 0.85·P/B) / (1 + 0.75·P/B)**, with P = GOOD's pre-merger share and B = RISE's taken from the run's own `_mergers` rows, to 1e-9 relative; no party other than RISE and ASA has a spine level that rises |
| guard | `MergerRefused` not raised (pools.py:3770) | `test_roster_aware_baseline` **fails** (`test_the_roster_decides_which_partner_inherits`, three-partner block); no change at J |

### C6. `apply_mergers` on the preceding local result (montecarlo.py:4682)

**Claim.** The PR base the spine reads takes the same transfer where the
successor holds a local record. At J: FORUM_4 (0.0332% of the 2021 PR vote)
→ ASA; RISE has no local record and receives nothing.

| mutation | exactly | prediction |
|---|---|---|
| off | `prior_pr_share = pc` (the call's input, unmerged) | first changed stage **`20_spine`** (ASA's spine level is its local level, w = 1); ASA's spine level **falls**; RISE's spine level **unchanged** |
| guard | the no-record rule removed: `out[successor] = out.get(successor, 0.0) + moved` and the `continue` at pools.py:3775 deleted | first changed stage **`20_spine`**; RISE **acquires a local record** and moves from the national-only route to the blend; `test_roster_aware_baseline::test_a_merger_never_creates_a_record_the_successor_lacks` **fails** |
| (same edit, tests) | — | test modules: expected **none fails** beyond the control — the consumer scan works per function and still finds the first call (R3 F10) |

### C7. The merger vector blend in `emit_pools` (pools.py:6245)

**Claim.** The successor's vector becomes the mass-weighted blend of its own
and the predecessor's.

| mutation | exactly | prediction |
|---|---|---|
| off | the `blend_merger_vectors` call replaced by setting each row's `vector_blended` to False (the loop after it reads that key, N1) | spec diff at J: **RISE's and ASA's member weights, and every pool's `alpha`**, change (ASA's 2021 metro shares enter `splits`, pools.py:6371); **`turnout`, `registered`, `identified` do not**. Trace first changed stage **`40_draws`** (no `seeds` change: RISE and ASA are not seeded). Test modules, source edit: expected **none fails** — no test checks that `emit_pools` makes the call |
| nudge | blend at twice the moved mass | RISE's Coloured weight **further from its unblended value, in the same direction** as unblended → blended (§1.275: 0.072 → 0.133); first changed stage **`40_draws`** |
| guard | the running mass removed (each merger blended against the pre-merger share) | spec diff at J **empty** (distinct successors, §1.278); `test_two_mergers_into_one_successor_give_the_mass_weighted_average` **fails** |

### C8. `apply_mergers` in `theta_residual` (theta_residual.py:247) — *fixture corrected on R3*

**Claim.** Key 4's residuals are computed on the merged baseline. Inert at
every held election today because no declared merger predates one. `run_model`
does not call `theta_residual`, so B and J cannot show it (R3 F4).

| mutation | exactly | prediction |
|---|---|---|
| off | the line deleted (`before` stays bound). Fixture K, fixed now: Johannesburg 2021; the predecessor is the largest party in the 2019 national result not on the 2021 ballot; the successor is the DA (on the 2021 ballot, with a 2019 share and a 2021 share, so its residual row exists); dated 2020-06-01. `probe.py c8` computes both with `pools.MERGERS` patched and the cache cleared | base code: K's rows **differ** from the real-MERGERS rows (the fixture is live); mutant: K's rows **equal** the real-MERGERS rows; real-MERGERS rows **identical** base vs mutant. `test_roster_aware_baseline::test_every_consumer_the_spec_names_calls_apply_mergers` **fails** |

### C10. The per-VD transfer (pools.py:3784) — *added on R3*

**Claim.** At J, RISE and ASA take on the predecessors' VD pattern; this
reaches the run only through `base_share_d`.

| mutation | exactly | prediction |
|---|---|---|
| off | the `if vds is not None:` block skipped | first changed stage **exactly `40_draws`** (the citywide shares, and so stages 10–30, are untouched) |
| (same edit, tests) | — | `test_roster_aware_baseline::test_a_merger_moves_retention_times_the_predecessor_and_nothing_else` **fails** (it passes `per_vd` and asserts the VD shares) |

---

## Not claimed, and why

Register-only or report-only, no effect on a draw: the `_levels_state`
MERGERS/RETENTION memo keys (theta_residual.py:200), `note_constant
("MERGER_RETENTION")` and `backtest.FITTED_ON["MERGER_RETENTION"]`, the spec's
`mergers` field, and the held-pool `unidentified` / `rates_on_a_bound` text.
The date gate (pools.py:3763) and the retention range check (pools.py:3752)
are covered by tests and are what make C8 inert and C5's nudge legal.

## Output

Three lists, read before `build_site.py --publish`: **dead**,
**wrong-way or wrong-stage**, **unguarded**.
