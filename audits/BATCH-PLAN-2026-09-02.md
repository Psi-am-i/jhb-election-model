# Batch plan — the six queued `pools.py` entries (2026-09-02)

> **This is the tracked copy and the one that governs.** A session-local plan file
> is not a record: this batch spans sessions and a dated deliverable, so the plan
> and its checklist live here. Tick an item only when it has landed WITH its
> measurement beside it. **Nothing is ticked on intent.**
>
> Companion documents: `ULTRA-REVIEW-1-pools-reemit.md` (the FROZEN brief — read,
> never amend), `ULTRA-REVIEW-1-STATE.md` (the branch state, which may be edited),
> `../POOLS-REEMIT-QUEUE.md` (the six entries and their evidence).

*Revised after a pollster review of the first draft. Three defects in that draft were confirmed against the tree and are fixed here; one design question it surfaced is now the first item of work.*

## Context

`POOLS-REEMIT-QUEUE.md` holds six changes to `src/pools.py`. **All six are undone**, verified in code. Four further changes (turnout band, `_nnls` bound, guard population, C/D terms) are already written and committed on `splinter-rule-and-historical-tail`, un-emitted.

The frozen brief `audits/ULTRA-REVIEW-1-pools-reemit.md` books one billed ultra review for this batch and requires it **before the emit** — afterwards there is no clean baseline. So: write → review → fix findings → **one** emit → re-baseline → freeze.

Nomination lists publish **16 September 2026**, 14 days out.

### Owner decisions already taken

- **Measurement**: hybrid — in-process verification for the number-neutral entries, one emit-measure-restore cycle for entry 4.
- **Roster**: support full per-ward nominations; before lists land, fall back to previous elections with a declared judgement on direction.
- **COPE/ActionSA transitional-party error**: deferred until the internals are sound.
- **Capacity check**: reports loudly, never refuses.

---

## What the review changed

**Three defects in the first draft, all verified:**

1. **The neutrality baseline was the wrong archive.** `archive/pools-preemit-2026-09-02/` is at `pools_sha 86995c91`, which **predates** the turnout band and `_nnls` bound (`9f9ac9e`). Diffing post-Phase-1 emissions against it is non-empty *by construction*, so every "number-neutral" acceptance test in the draft was uninterpretable — and the failure mode is the worst kind: *"the diff is expected to differ, so I stopped reading it."*
2. **Entry 3 contradicted itself.** The design said the absent-roster path projects reach via `projected_contestation`; the acceptance test said the absent path must reproduce `pools_2026.json` byte-for-byte. Both cannot hold.
3. **The entry-5 warning I proposed cannot fire.** `newcomers = {p for p in no_vector if baseline.get(p, 0.0) <= 0.0}` (`pools.py:3818`) — every party reaching `classify_arrival` has a baseline of zero by construction, so "baseline exceeds a floor" is an empty trigger. A guard that reads as working and cannot fire, in a plan whose own risk register names that class.

**Two claims cut as void:** `_npe_citywide_for` builds its path from `cityconfig.CALENDAR[year].results`, and **every** template is `*_clean.csv` / `npe*_vd_party.csv` — it can never reach `_reports/`. So the UTF-16 corruption path does not exist; R0a's encoding half and risk item 4 are removed.

**And the scope was wrong.** Entry 4 turns the arrival machinery on at **2011 as well as 2016 — 16 of 24 scored city-years**. `_arrival_total_prior('2011')` returns `None` today and `entrant_record` before 2011 is empty. The frozen brief says "the 2016 arm" because the eight 2011 targets did not exist when it was written. `ULTRA-REVIEW-1-STATE.md` must correct this or the reviewer hunts the wrong blast radius.

---

## ⛔ R-1 — Settle the estimator question before writing entry 4

The review measured the widened record in-process. Entry 4 as queued does this:

| target | rows | median arrival total | α (concentration) |
|---|---|---|---|
| 2011 | 0 → 7 | none → 1.4728% | none → 10.874 |
| 2016 | 6 → 13 | 1.3312% → 1.4728% | 8.654 → 10.874 |
| 2021 | 14 → 21 | 1.6155% → **1.5703%** | 4.357 → 9.758 |
| **2026 (live)** | 22 → 29 | **2.1701% → 1.7458%** | **5.096 → 8.406** |

**The live 2026 arrival total falls 19.6% and its concentration parameter rises 65%.** Higher α means a *more even* split — and the mechanism exists because "the largest arrival took 91% of the group in Johannesburg 2021". Pooling 2000/2006, where arrivals were many micro-parties splitting evenly, suppresses the concentrated-arrival case: the ActionSA case, which the code's own docstring calls the single largest error the model makes.

`_arrival_total_prior` is a **pooled median of a visibly trending series** (2016: 0.31–4.74%; 2021: 1.53–19.99%). Extending the panel backwards adds only low-arrival cycles. This is the `k*` error in a different quantity — `CLAUDE.md` §4 records `k*` at 0.62/2.48/1.70/1.76 with the quiet cycle as the outlier, and 2000/2006 are the pre-realignment analogue.

**The decision, in writing, before a line of entry 4:** dispersion (`sd(log)`) is a property of the world and may be pooled across the widened panel; the **central level** should come from the most recent cycle or a recency-weighted mean, not a pooled median. That is the level-vs-shape line in `CLAUDE.md`. If we instead ship the pooled median, the 2026 forecast's arrival total drops a fifth on the strength of two pre-realignment cycles, and no backtest on 2011/2016 can adjudicate it — those are the cycles the widening flatters.

**No new blind pollster round is needed here: the reviewer already answered it.** This round is to take the decision, record it in `MODEL-LOG.md` and `JUDGEMENT-CALLS.md`, and write entry 4 to match.

---

## Sequence

**R0 → R1 {1,2,6,min_oos_gain} → R2 {artefact_key} → R3 {3} → R4 {4} → R5 {5} → suite → re-archive → ULTRA → fix → one emit → baseline → freeze**

**Entry 3 moves to third, and the sever point moves to entry 4.** The brief severs *at* entry 3 — but entry 3 is the item with the date and entry 4 has none. Entry 3's acceptance test is independent of entry 4 once its absent path is settled as byte-identical (below). If the review runs long, entries 1, 2, 6, R2 and 3 are all emittable before 16 September and entry 4 takes a second window, which the brief already prices.

4-before-5 is retained and verified: `arrival_group_spec` calls `arrival_group_record` at `pools.py:3117`, and entry 5's acceptance test is a byte diff that needs one candidate cause.

### R0 — Measure, write nothing

- **R0a** — in-process: compare `_ward_reach(code, y)` vs `levels.contestation(Target(y), city)`. These read different files with different ward normalisation and are the *existing* second reader. *(The encoding/cross-file half of the original R0a is cut as void.)*
- **R0b** — the attribution anchor. Emit all 26 on the current tree; **⛔ SAVE that emit as `archive/pools-postphase1-2026-09-02/` BEFORE restoring** — this is the baseline R1, R2, R3 and R5 all need, it costs five minutes, and it is impossible to recover later. Then measure (`compare_history --json /tmp/… --md /tmp/…`), restore from the pre-emit archive, verify hashes and `git status --short` clean.
- **R0c** — re-run `compare_history` on the *restored* tree and confirm it reproduces §1.166's **707 / 539.41 on 24 city-years**. Otherwise the "before" leg is a citation, not a measurement.
- Snapshot `data/processed/**` hashes before any emit and diff after — `compare_history` writes `history.json` by default. Never enumerate "26 files" from memory.
- **No pollster** — instrumentation.

### R1 — Entries 1, 2, 6 + `min_oos_gain` (plumbing)

Entry 6 moves forward: `gate()` is `--gate`-only, cannot move a spec value, and bundling a zero-risk refusal behind the batch's riskiest transcription is backwards. `min_oos_gain` (`pools.py:4100`) has the identical defect one line later — fix both, because fixing one instance removes the symptom that would have found the other.

- **1**: resolve `CONFIG` in the body of `artefact_key`, `stale_reason`, `load_config`.
- **2**: `pools.py:2424` → `target.crosswalk`; correct the refusal message. **Neutral, and why is verified**: `_target_roll` is reached only when `CALENDAR[year].results` is falsy (2026 only), and for joburg 2026 `target.processed` collapses to `city.processed`, so the paths are identical. Assert that rather than assuming, including the `except SystemExit: pass` fall-through at `:2423`.
- **6**: replace both `cfg.gate.get(key, <literal>)` fallbacks with refusals naming `config/dimensions.toml`; delete the queued-defect comment in the same commit.
- **Verification**: three constructed violations. Diffs against **`pools-postphase1`**, excluding the `artefact_key` block.
- **No pollster.** Plumbing.
- ⚠️ From here `test_every_emitted_pool_spec_carries_a_current_artefact_key` is red until the emit — record as a fourth expected failure in `ULTRA-REVIEW-1-STATE.md`; treat any *other* failure in that module as real.

### R2 — The `artefact_key` population (blocks R3 and R5)

A **population** bug: the claim is "what this spec was built from"; the population scanned is one named file. `judgements/{slug}-{year}.toml` sets `parent`, `weights` and therefore seeds, and **is in no hash anywhere** — so a nomination-list edit on 16 September would move nothing and every spec would report itself current.

- `config_sha` → a hash over all `config/*.toml`, sorted, name-and-content.
- Add **`judgements_sha`** over `lineage_path(city, target)`, hashing the **parsed payload, not the bytes** (precedent: `theta_residual.py:196`). Byte-hashing marks 26 specs stale on every comment edit and the guard becomes noise.
- Fix `stale_reason` (`pools.py:288`): it hardcodes the compared set and indexes a literal dict, so any new key is **recorded and never checked**. Derive the set from the key; label via `.get(m, m)`. Bump `schema` to 2.
- **Every byte-identity test in R1, R3, R5 must exclude the `artefact_key` block** — this round changes it by design.
- **Verification**: entirely in-process. Perturb each key; assert `stale_reason` names it. Assert a comment-only judgement edit does *not* move it.
- **No pollster.** Delivery-proof mechanism.
- Close honestly: name every hand-editable input still outside the key (`cities/*.toml` at minimum).

### R3 — Entry 3 (the roster seam; the dated entry)

- Keep `contesting_parties` **pure**. Add `declared_roster(city, target)` reading a `[roster]` table from `judgements/{slug}-{year}.toml`, precedence at the `emit_pools` call site (`pools.py:3765`). `load_lineage` already ignores unknown tables, so the config side can be prepared and reviewed before the code lands. This keeps `tests/test_chain.py:454` true.
- Schema: `parties = [...]`, optional `[roster.wards]` per-party ward lists (full fidelity for when lists land), optional `[roster.reach]` fractions.
- **⛔ THE ABSENT PATH CARRIES REACH FORWARD UNCHANGED.** This resolves the draft's contradiction. Today `reach = _ward_reach(code, target.year) or _ward_reach(code, year)` — the fitting year's reach. Keep exactly that, make it **announced in `provenance`** rather than silent, and let `[roster.reach]` override. Do **not** substitute a `projected_contestation` expansion by default: 65.5% of parties expand and 34.5% do not, so applying the 0.220 median uniformly over-states reach for a third of the roster, and reach is the split weight. This also keeps entry 3 genuinely number-neutral, which is what lets it move earlier.
- **⛔ THE SHARPEST HAZARD IN THE SEQUENCE.** `pools.py:3802` drops every composition party not on the roster — 2.4–2.9% of a city's vote across 16–20 parties. A partial paste on 16 September silently deletes them and the run looks fine. **`roster_is_real` and `roster_is_complete` are two facts; only the second may license dropping.** Constructed-violation test, mandatory.
- **`arrival_group` stays off.** `arrival_group_draw` was measured and rejected at 2021 (CRPS 85.9 → 109.9). The seam makes the block constructible; the commit message must not imply the lever moved.
- **Verification**: absent `[roster]` reproduces `pools-postphase1/pools_2026.json` byte-for-byte (excluding `artefact_key`); a constructed roster populates seeds and `arrival_group` — assert **structure, not values**, since entry 4 will move the values; `provenance` names roster source and reach source; R2's `judgements_sha` moves when the roster is added.
- **Flying blind on everything predictive** — no 2026 result, no backtest arm. Label **argued, not tested** in the docstring, `JUDGEMENT-CALLS.md` and `MACHINERY.md`.
- **⛔ Pollster, BLIND.** A selection rule feeding a forecast. Ask: carry forward unchanged / apply the measured 0.220 expansion / accept a hand-declared list — which is defensible and what does each get wrong? State the 2.4–2.9% *without* the verdict word. **Add the case the seam exists for**: a published list names a party with zero prior vote and no measured geography — what is the defensible seed, and the defensible band around it?

### R4 — Entry 4 (the only round that moves numbers)

**Never widen `metro_file`** — it feeds `read_municipality`, which cannot parse the clean files (`KeyError`, verified), and widening breaks `metro_citywide`, `metro_roster` and `_ward_reach` at once. Correct the two comments that falsely claim the drift is handled (`pools.py:3163-3166`, `archive.py:68-70`).

Apply `x or _npe_citywide_for(...)` at the four **shares** sites, each with its own reason: `entrant_record` `:2755`, `arrival_group_record` `:3073`, `measure_pool_ratios` `:2531`, the `emit_pools` split loop `:3958`. All four are always-consumed. Do not widen `_ward_reach` or `metro_roster` here.

- **The HELD_BACK gate is inherited for free** — confirmed: `_npe_citywide_for` calls `levels._held_back`, returns `{}` for the seven quarantined metros at `lge2000`, and all four sites guard on empty. **But** it leaves an 8-way asymmetry taken on an absence. **Instrument it**: transitions offered vs used, per record, into `provenance`.
- Apply the R-1 decision on level-vs-dispersion.
- **Fix the fabricated covariate**: `entrant_record` does `reach.get(party, 1.0)` (`pools.py:2762`) — asserting a party contested *every* ward when no ward file exists. That is 100% of the new 2011 record. **Skip the row instead.** One line.
- Register `len(arr) < 3` (`pools.py:3080`) in `JUDGEMENT-CALLS.md` — it selects on the dependent variable and drops the lowest-arrival city-years (MAN 0.330%, BUF 0.493% at 2006), unevenly by cycle.
- Rename `total_log_median` (`pools.py:3125`), which holds `np.mean(logs)`. Refresh the stale docstring figures at `:3929` and in `arrival_group_record` — `CLAUDE.md` §2, same commit.
- **Second step** — the arrival reconciliation is **baseline-only**; the population difference is a 2026-08-29 fix the brief forbids reverting.
- **One emit-measure-restore cycle**, giving entry 4's effect **conditional on the bounded rates and the measured band** — say it that way, never "entry 4 alone", or the number will be misquoted the way the 21-city-year figures were.

**Pre-registration — five falsifiable numbers, replacing the draft's three directions:**

| # | prediction | falsified if |
|---|---|---|
| P1 | 2026 arrival total → **1.75% ± 0.02** (−19.6%); 2021 → **1.570% ± 0.005** | either rises, or 2026 lands outside 1.70–1.80% |
| P2 | 2026 α **5.096 → 8.406**; `sd(log)` narrows **1.1540 → 1.0422** | α does not rise, or sd does not narrow |
| P3 | **Eight 2011 specs gain non-empty `seeds`** for the first time | any 2011 spec still carries `seeds = {}` |
| P4 | **2011 seat error and CRPS move by MORE than 2016's** — 2011 goes from no arrival machinery to full, 2016 only from no seeds to seeds | 2011 moves less than 2016 |
| P5 | The 2016 fallback **switches off rather than stacks** — arrival mass does not reach 2.8–3.1% | it lands in that band |

*(The draft's "does 2016 move" is cut: 2016 cannot not move, so it predicts only that the change compiles. "Does 2021 move" is retained inside P1, but note the group channel moves 2021 only 2.8% relative — a small move is not confirmation.)*

- **Three read-only agents** returning specifications: reader agent, blast-radius agent (every measured claim needing re-reading because the 2011 *and* 2016 arms were dead when taken), reconciliation agent (given the brief's prohibition).
- **Pollster**: the estimator question was already answered at R-1. This round's pollster pass is a **sighted check that the implementation matches the decision** — not a fresh blind ask.

### R5 — Entry 5 (narrow form)

**Move neither table.** `TYPE_A_EVENTS` cannot move — `montecarlo.MODULE_CONSTANTS:1540` declares it under `levels` and `test_delivery_proof.py:228` fails if a declared name stops resolving; and it cannot be derived from `SPLITS` (direction inverted, date basis differs, `ASA` has `measured_from=None`, three of six rows are not splits). `SPLITS` moving costs a byte-identical `why` round-trip that `test_chain.py:544` pins, on the table whose miscoding cost 180×, and a flipped `home` is caught by nothing — while the benefit largely exists already, since `classify_arrival` reads the city judgement file first.

**⛔ Re-specify the detector — the draft's trigger cannot fire.** Two changes:
- Trigger on the party's share in the **preceding NPE** (`target.previous_npe`), not its baseline — a party that exists nationally but not locally. That is computable at the call site and is exactly the ActionSA/MK shape.
- **Make it durable, not a print.** A `print` during an emit is scrollback, and the emit is the one operation nobody re-runs. Have `classify_arrival` return an explicit unclassified marker, size it as an entrant as today, and **write the list into the emitted spec** alongside `no_measured_vector` (`pools.py:4037`). Then it is diffable, survives into `compare_history`, and a test can assert on it.
- The byte-identity test must then exclude that new field.
- **Verification**: all 26 specs byte-identical to the R3 state apart from the new field.
- **⛔ Pollster, BLIND, on one question only** — the draft's "config file or warning" is a false dichotomy (editability vs detection are not alternatives) and is cut. Keep: **"is 'split vs entrant' a binary a forecaster should be drawing at all?"** The reviewer's provisional answer is *no* — it is a hard switch between two estimators chosen by a dict literal with a 180× penalty and no test that can arbitrate it, and the defensible form is a continuous inherited-support weight. That is a substantial estimator change, correctly **out of this batch**; record it as a finding for the next one.

### Then

1. Full suite once on a settled tree; report honestly.
2. **Re-archive and verify** both archives byte-identical after the restore cycles; rebuild if drifted.
3. Update `ULTRA-REVIEW-1-STATE.md`: the fourth expected failure, **entry 4's true scope (2011 *and* 2016, 16 of 24)**, the `arrival_group_draw` scoping caveat, and the R0b/R4 numbers.
4. **Ask the owner to launch `/code-review ultra`** — user-triggered and billed.
5. Triage: fix-before / fix-after / rejected-with-reason. **The emit does not happen until the first list is empty.**
6. **One emit, 26 specs** — the queue's loop says eighteen and is stale; correct it first. Then `compare_history`, then the freeze, nothing else running.

---

## Risk register

1. **Entry 4 inert at 2011** while `pools_sha` moves, so nothing goes red. *Caught by P3 and P4.*
2. **An incomplete 2026 roster deletes pool members** on the live forecast, on the day, no second chance. *Caught by the `roster_is_complete` split.*
3. **`judgements_sha` marks 26 specs stale on every comment edit** → the guard becomes noise. *Caught by hashing the parsed payload.*
4. **A restore silently misses a file** — `compare_history` writes `history.json` by default. *Snapshot hashes before, diff after, `git status --short` clean.*
5. **`HELD_BACK_OFF=1` becomes load-bearing** on the arrival record. *Caught only by the offered-vs-used instrumentation; if dropped as scope creep, record that it was.*
6. **The conditional effect gets quoted as "entry 4 alone."** *Name it "given the bounded rates and the measured band" everywhere it is written.*
7. **Severability taken under time pressure.** *Decided now: sever at entry 4, not entry 3.*

---

## Verification

Per round: targeted tests green; each constructed violation caught by the same detector; for number-neutral rounds, `emit_pools()` in-process for all 26 diffed against **`archive/pools-postphase1-2026-09-02/`**, excluding the `artefact_key` block, zero writes; pollster and I agree before applying, and where we disagree the disagreement goes to the owner rather than being split; `MODEL-LOG.md` appended with the numbers including negative results.

At the end: full suite once, both archives verified, `ULTRA-REVIEW-1-STATE.md` updated, then the owner launches the review.

## Tracking

The plan and its checklist are recorded in the repository at **`audits/BATCH-PLAN-2026-09-02.md`** — not only here — because this batch spans sessions and the 16 September deadline. Every item below is ticked there as it lands, with the measurement beside it. Nothing is ticked on intent.

```
R-1  [x] SETTLED, and the plan's own position is WITHDRAWN (§1.180).
         Measured on the entrants-only, widened record and scored out of sample:
           pooled MEDIAN 3.0777 | pooled MEAN 2.6146 | recency 2.6893 | last 2.7746
         -> MEAN not median (the consumer pins a mean; the score agrees).
         -> RECENCY NOT SUPPORTED: worse than pooled, and 0.08pp is inside noise.
            The pooled mean wins on PARSIMONY, not on score. No half-life param.
         -> The all-arrivals -19.6% that motivated the worry is a population
            artefact: on entrants-only the widening moves the mean just -4.3%.
         -> 8 of 8 cells UNDER-predict. A level bias, deliberately NOT fixed --
            a trend term on 2 targets / ~3 clusters is the k* mistake again.
R0   [x] a: _ward_reach vs levels.contestation -- EXACT agreement, 24/24,
         symmetric difference 0, max|diff| 0.0000 (MODEL-LOG §1.169).
         Found: contestation reaches 2000/2006 where _ward_reach cannot,
         AND it is UNGATED -- returns 13 parties for a held-back CPT 2000.
     [x] b: DONE. 26 emitted, archive/pools-postphase1-2026-09-02/ saved,
         measured, restored -- 146 files byte-identical. {7,8} = seat 707->707,
         CRPS 539.41->542.77. ⛔ PRE-REGISTRATION REFUTED: 2011 rose (41.1->41.6),
         it did not fall toward 2016. Coverage does NOT track score (§1.170).
     [x] c: DONE. Restored tree re-measures to 707 / 539.41 on 24, exactly.
R1   [x] entry 1 CONFIG in body (3 sigs) -- constructed violation: rebinding
         pools.CONFIG now moves config_sha 050fa0e6 -> 5a89be58
     [x] entry 2 target.crosswalk -- joburg unchanged (135/2,348,781),
         tshwane 2026 now RESOLVES (107/1,619,402) where it refused
     [x] entry 6 both --gate keys via _required_gate; constructed violations
         refuse by name; comment deleted. ⚠️ the '2 of 2 by grep' claim was
         WRONG -- it named a spelling, not the defect class; the two members
         that move numbers are fixed in R1b
     [x] 3 constructed violations caught; ALL 26 of 26 IDENTICAL vs postphase1
R1b  [x] pollster review: the shipped band was set by ONE broken row
         (buffalocity Coloured turnout 0.0375, |dlogit| 3.6529, vs a
         second-largest of 1.4320). Winsorised, and the pooled floor now
         applies only where a pool cannot speak for itself.
         PRE-REGISTRATION CONFIRMED ON ALL FOUR CLAUSES:
           2016 CRPS +3.142 -> -0.132   (104% of the regression recovered)
           seat 707 -> 703,  CRPS 542.77 -> 539.41
           coverage 21/24 unchanged,  width 38.6pp -> 30.6pp   (§1.172)
     [x] damping + max_extrapolation refuse -- entry 6's REAL population, the
         two members that move numbers (§1.171's 'grep' named a spelling)
     [x] anchor RE-TAKEN: archive/pools-anchor-2026-09-02/ is now THE baseline;
         pools-postphase1 is superseded for byte-identity
     [x] 4th expected failure recorded in ULTRA-REVIEW-1-STATE.md
R2   [x] config_sha over ALL config/*.toml -- constructed second file moves it
     [x] judgements_sha over the PARSED payload -- comment-only edit does NOT
         move it, a changed `parent` DOES
     [x] stale_reason DERIVES its set from the key; schema -> 2
     [x] 4 constructed violations, and COMMITTED AS THREE GUARDS in
         test_chain.py (R1's were demonstrations that left nothing behind).
         26/26 IDENTICAL vs pools-anchor excluding artefact_key. (§1.173)
     [x] BLIND pollster pass found the key still short by four inputs:
         + cities_sha  (panel input via panel_turnout_spread -- §1.168 CREATED it)
         + deps_sha    (parties/cityconfig/ingest_lge/levels; montecarlo
                        excluded to avoid crying wolf, risk named)
         + set comparison, so a field the code no longer produces is caught
         + schema now compared
         + montecarlo no longer FAILS OPEN on a staleness error
         Fixed 2 defective tests of mine: one wrote into the live hashed
         config/ dir, one globbed and never asserted non-empty (the headline
         guard passed on ZERO specs on a fresh clone). 26/26 identical. (§1.174)
     [x] still outside and RECORDED not fixed: vd_ward_<target>.csv (real gap),
         data/raw (manifest covers it), emit params, _pools_stale unread
R3   [x] declared_roster + [roster] schema (parties / wards / reach)
     [x] absent path carries reach forward UNCHANGED, announced in provenance
         -> provenance: "roster declared; reach 2021 ward ballot, carried forward unchanged"
     [x] roster_is_real vs roster_is_complete; only complete may drop
     [x] byte-identity vs postphase1 for absent roster; structural test for constructed
     [x] labelled argued-not-tested in docstring + JUDGEMENT-CALLS §L + MACHINERY
     [x] pollster BLIND  -> BLOCKING finding, and it was right (§1.178)
R3b  [x] FIX: the projected branch ran in the declared case too; declared roster
         was overwritten two lines after being read. NEWPARTY in seeds: False -> True
     [x] extract `resolve_roster`; 4-row truth table in ms + 1 end-to-end anchor (97s)
     [x] `support` read outside `if weights:`; it was silently discarded
     [x] lo_e/hi_e hoisted -- UnboundLocalError on the documented path, and an
         order-dependent band [0.029, 1.0, 0.358] when it did not raise
     [x] band divides by the comparator mean, not the adjusted centre (x36 -> 7.7%)
     [x] PARTY_KEYS closed; unknown key refuses. 408 tables carry only the dead one
     [x] 3 mutations run; ONE SURVIVED (asserted the note, not the arithmetic) -> fixed
     [x] group rescale renormalised the declaration away: 12.00% -> 0.3687%.
         A judged size is now outside the budget; the other 29 still total 1.75%
     [x] 2 more mutations, both caught (judged back in budget; budget switched off)
     [x] retired `roster_is_real` from JUDGEMENT-CALLS -- the register guard caught it
     [x] moved 4 new tests above test_chain's __main__ block -- guard caught that too
     [x] pollster BLIND on the fixes -> agreed both open judgements, found 6 more
R3c  [x] `weights` alone declared a size nobody stated (default_support 4.8x low
         vs base) AND escaped the group budget on `not weights` -> keys on `judged`
     [x] [roster] closed: LINEAGE_TABLES ([rostr] fell through to PROJECTED),
         ROSTER_KEYS (partys = [] did the same), KNOWN_PARTY_CODES ('VF PLUS' ->
         VF_PLUS phantom + real VFPLUS deleted under complete = true)
     [x] ROSTER_DROP_CEILING 1.5%: a `complete` drop reports MASS and refuses
         above it without confirm_drop (JUDGEMENT-CALLS §L4)
     [x] MAX_POOL_CAPTURE registered §L5 + capture_shortfall; 6% concentrated
         delivers 2.85% (53% short), was silent under a note saying DECLARED
     [x] 4 stale record figures corrected + pinned by a test that DERIVES them
         (22 rows / median 2.1701% / max 19.99%; sites said "sixteen… 3.11%")
     [x] 6 mutations, 6 caught. The name guard caught my own §1.178 tests.
     [x] corrected my own E5 framing: tests REACH both arms, nothing SCORES them
QUEUE[x] entry 11 filed: the group budget is measured over splits+entrants and
         spent over entrants only, with a MEDIAN where the consumer is an
         expectation. 2.1701% used vs 2.2853% correct -- right by accident.
         ⛔ MOVES NUMBERS, both halves together, inside the ultra review scope.
R4   [ ] ⛔ ARCHIVE THE POST-R4 EMIT **BEFORE** RESTORING. R0b says it in
         full: "impossible to recover later". Without it R5 and every ultra
         fix are attributed against a PRE-R4 baseline and R4's own
         contribution can never be separated again. FIVE MINUTES.
     [ ] ⛔ PLACEBO EMIT, the constructed null arm that replaces the 2016
         tripwire: restrict the fallback to years metro_citywide already
         covers; every spec must come back byte-identical to the pre-batch
         archive. Separates "wired correctly" from "the new data moved things".
     [ ] provenance: transitions offered vs used, per record, INTO the spec --
         the specs are not in git, so after the restore a number's provenance
         exists nowhere
     [ ] per-city seeded arrival mass as a fraction of the electorate, all 26
     [ ] tell the paid reviewers IN WRITING that the specs contradict the code
         by design and which tests are red on purpose
     [ ] ⛔ FOLD IN QUEUE ENTRY 11. R-1, entry 4 and entry 11 are all the same two
         functions (`arrival_group_record` / `_arrival_total_prior`). Entry 4
         widens the record 22 -> 29 rows, so entry 11's 2.1867% must be
         RE-DERIVED after it, and R-1 is a decision about that same statistic.
         Taken separately this measures one quantity three times against three
         records and believes the last. One commit, one pre-registration.
     [ ] pre-register P1-P5 in writing BEFORE either arm
     [ ] `or _npe_citywide_for` at the 4 shares sites only
     [ ] skip entrant_record rows with unknown reach (no 1.0 default)
     [ ] instrument transitions offered vs used in provenance
     [ ] register len(arr)<3; rename total_log_median; refresh 3 stale docstring figures
     [ ] correct the 2 false comments (pools.py:3163, archive.py:68)
     [ ] baseline-only arrival reconciliation
     [ ] emit-measure-restore; report as "conditional on bounded rates + measured band"
     [ ] pollster SIGHTED check vs the R-1 decision
R5   [ ] detector triggers on preceding-NPE share, not baseline
     [ ] durable: emitted into the spec, not printed
     [ ] byte-identity vs R3 state apart from the new field
     [ ] pollster BLIND on the split-vs-entrant binary; record as next-batch finding
R5   [x] detector triggers on preceding-NPE share, not baseline
     [x] durable: emitted into the spec as `unclassified_with_national_record`
     [x] UNCLASSIFIED_FLOOR registered JUDGEMENT-CALLS §L8; changes no number
     [x] found RISE 1.56% and BOSA 1.02% -- BOSA is Maimane's party, treated as
         arriving from nothing. FLAGGED FOR THE OWNER, not decided.
     [x] test keys on MISSING LINEAGE not size (MK at 12.22% must not flag)
     [x] pollster BLIND on the split-vs-entrant binary -> recorded as a
         next-batch finding rather than reviewed; §1.185-§1.186 supersede it
         with the owner's momentum/sentiment mechanism
PRE  [x] 16 SEPTEMBER REHEARSAL — the real 2021 ballot (57 parties) pasted as a
         2026 list. IT REFUSED on the first run: KNOWN_PARTY_CODES was the alias
         tables alone, so the long tail of real small parties resolved unknown.
         Fixed; "known" now includes anyone who stood at the last local election.
         Locked as test_a_realistic_nomination_list_is_accepted.
     [x] nomination-day template written into judgements/joburg-2026.toml,
         COMMENTED — judgements_sha verified unchanged at 7de48723562cad2e
     [x] the template states the three things nobody knows at 22:00: complete
         defaults false; booleans must be bare; a roster paste is a TWO-spec
         re-emit, not the panel window
     [x] BOSA decision: stays unparented, recorded §1.194
     [x] owner's decision: publish JOHANNESBURG AND TSHWANE ONLY
     [x] env register closed BOTH ways; JHB_SCORE_NO_RELABEL registered
         (it changes what the SCORER is — 40 coherent seats)
     [x] §L9's evidence corrected; the VALUE 2.0 marked undefended and deferred
     [ ] ASK THE OWNER TO LAUNCH /code-review ultra ultra-review-base
END  [x] full suite once, reported honestly
         -> 451 passed, 5 failed, 17 skipped. 31 modules, 813s, no PARTIAL
            banner, run at HEAD. TWO of the five are LIVE DEFECTS (Mangaung's
            degenerate pool; the DA composition infeasibility), three expected.
     [ ] both archives re-verified byte-identical
     [ ] ULTRA-REVIEW-1-STATE.md: 4th failure, entry 4 scope (2011+2016, 16 of 24),
         arrival_group_draw caveat, R0b and R4 numbers
     [ ] correct the queue's window loop: eighteen -> twenty-six
     [ ] ASK the owner to launch /code-review ultra
     [ ] triage every finding; emit only when fix-before is empty
     [ ] one emit -> compare_history -> freeze
```

## Critical files

`src/pools.py` (all six entries), `src/levels.py` (`HELD_BACK`/`_held_back` 258-317, `contestation` 1444-1499, `TYPE_A_EVENTS` 526-553), `src/ingest_lge.py` (`read_municipality` 56-94), `tests/test_chain.py` (roster premise 454, `SPLITS` pin 518-568, artefact-key guards 947-1000), `tests/test_regressions.py` (111, 136-143), `audits/ULTRA-REVIEW-1-STATE.md` (the only review doc that may be edited), `POOLS-REEMIT-QUEUE.md` (window loop still says eighteen).
