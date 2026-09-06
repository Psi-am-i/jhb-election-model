# What is waiting for the next `pools.py` re-emit window

**A CODE change to `src/pools.py` moves `pools_sha` and invalidates all **twenty-six**
pool specs.** Re-emitting is cheap and deterministic — it changes nothing but the
key — but it is expensive in *coordination*: while it runs, **nobody may run the
model, `compare_history`, or any sweep**, because a number measured against a
moving artefact is not a measurement (CLAUDE.md, "Shared artefacts").

So `pools.py` changes are **batched**, and this file is the batch. Opened
2026-08-28 at the owner's instruction: *"batch it. keep a log of what goes in it
as we move along."*

**A comment-or-docstring-only change to `pools.py` does NOT move the hash** and
does not belong here — verified again on 2026-08-28 (`dbdf171344ffd5` before and
after declaring `_LOG_FLOOR`). Only changes to what the code *computes* qualify.

---

## The window, when it is taken

1. Land every queued change below in one commit.
2. Re-emit all **twenty-six** specs, with nothing else running.

   ⛔ **THIS LOOP SAID `2016 2021` AND OMITTED 2011 — EIGHT SPECS.** The 2011
   targets were added on 2026-09-02, the loop never moved, and following it
   verbatim would have left a third of the panel on pre-batch code while
   `compare_history` measured the mixture. The 2011 specs are also the ones
   carrying every arithmetically-impossible composition cell, so they are the
   last eight anyone should skip.

       for c in joburg tshwane ekurhuleni ethekwini capetown mangaung \
                nelsonmandelabay buffalocity; do
         for y in 2011 2016 2021; do
           .venv/bin/python src/pools.py --city $c --target $y --emit
         done
       done
       .venv/bin/python src/pools.py --city joburg --target 2026 --emit
       .venv/bin/python src/pools.py --city joburg --target 2026 --simulation --emit
       # and tshwane 2026, emittable since queue entry 2 landed:
       .venv/bin/python src/pools.py --city tshwane --target 2026 --emit

3. **Count what you emitted and confirm they carry ONE `pools_sha`.**

       find data/processed -name 'pools_*.json' | wc -l

   ⚠️ **The command above emits 27 and there are 26 on disk today.** The 27th is
   `tshwane/pools_2026.json`, which queue entry 2 made emittable and which has
   never been emitted. **So the count goes 26 → 27, and that is expected.** An
   operator who reads "confirm twenty-six" and counts 27 will resolve the
   discrepancy at speed, in the dark, in an irreversible window — which is why
   the number is not restated here. **Count against what the loop issued, not
   against a number in a document.**

   *(Undecided, and it must be decided before the window: does Tshwane also need
   a `--simulation` spec? Johannesburg has one. If yes the count is 28.)*
4. Re-take the baseline (`compare_history`) and the freeze, in that order, on a
   settled tree. **Every number quoted afterwards comes from that run.**

---

## Queued

⛔ **THE ENTRY NUMBERS ARE ONE NAMESPACE SHARED WITH
`audits/ULTRA-REVIEW-1-pools-reemit.md`, WHICH IS FROZEN.** The brief uses
**1-6** for the rows below and **7-10** for its own amendments (7 = the turnout
band, 8 = `_nnls`, 9 = the pool-bounds guard, 10 = the C and D terms). A new row
here therefore starts at **11**. This was got wrong once, on 2026-09-03: the
arrival-budget row was filed as "entry 7" and collided with the brief's turnout
band — two live changes in one batch under one name, and a reviewer would have
checked the wrong one. **Never renumber an existing row**; the brief cannot be
amended and the references are spread across a dozen files.

⛔ **ENTRIES 4 AND 11 AND THE R-1 DECISION ARE ONE CHANGE, NOT THREE.** They are
the same two functions (`arrival_group_record`, `_arrival_total_prior`); entry 4
widens the record 22 → 29 rows, so entry 11's measurements must be re-derived
*after* it and R-1 (§1.180 / §L6) is a decision about that same statistic. The
only forecast-moving work in this queue is those three together. See both rows.

| # | change | why it needs the window | raised |
|---|---|---|---|
| 11 | ⛔ **THE ARRIVAL GROUP BUDGET IS MEASURED OVER A WIDER POPULATION THAN IT IS SPENT ON, AND WITH THE WRONG STATISTIC. IT IS RIGHT BY ACCIDENT.** `group_total = _arrival_total_prior(...)` is the **median** of `arrival_group_record`, which counts every party with local votes and no preceding national vote — **splits included**, because EFF, ActionSA, COPE, GOOD, MK and the NFP all had no national record at their first local election. `arrival_rules` then spends that budget only over `entrant_sizes`, which **excludes every `as_split` party**. Re-derived over all 22 rows (2026-09-03): JHB 2021 is **19.99% as a group and 1.87% excluding splits**, a factor of 10.7; TSH 5.4x; EKU 5.1x. Pooled: all-arrivals median **2.1701% (used)**, entrants-only mean **2.2853% (correct)**. Two errors of opposite sign — population ~1.3x too broad, and a **median where the consumer is an expectation**, which is the same correction the entrant branch made on 2026-08-17 after the median under-forecast every arrival by a factor of four, undone here in aggregate. ⚠️ **THEY MUST MOVE TOGETHER**: entrants-only median alone is 1.6679% (**−23%**), all-arrivals mean alone is 4.2711% (**+97%**). *Not checked:* whether `as_split` routing agrees with `SPLITS` for every party in the record — a declared parent absent from `index` falls back to the entrant branch and **is** budgeted. | ⛔ **MOVES NUMBERS.** ⛔ **PRE-REGISTER ON THE POST-ENTRY-4 RECORD, NOT THIS ONE.** The 2.1701% → 2.2853% (+5.5%) above is measured on TODAY'S 22-row record and is the wrong number to pre-register, because entry 4 widens the record first. On the 29-row record the entrants-only pooled mean is **2.1867%**, so the correction against today's all-arrivals median of 2.1701% is **+0.8%, not +5.5%**. **The expected seat effect is therefore ~ZERO, and that is the PASS condition, not a disappointment** — this entry buys defensibility, not accuracy. If `compare_history` moves more than a seat or two, something else is coupled and the coupling is the finding. **If `compare_history` moves more than a seat or two, something else is coupled and the coupling is the finding.** Fix both halves in one commit; a one-sided fix is worse than the current state. ⛔ **AND IT IS COUPLED TO ENTRY 4 AND TO R-1 — ALL THREE ARE THE SAME TWO FUNCTIONS.** Entry 4 wires `_npe_citywide_for` into the shares sites, which ADDS rows to `arrival_group_record` (22 → 29). So the 2.1701% / 2.2853% measured here is taken on a record entry 4 changes, and the R-1 decision (pooled median vs recency for `_arrival_total_prior`) is a decision about *this same statistic*. **Taking them separately means measuring the same quantity three times against three different records and believing the last one.** Sequence: settle R-1, land entry 4, THEN re-derive this table on the widened record and fix both halves — one commit, one pre-registration. | §1.179, 2026-09-03 |
| 6 | **`pools.gate`'s typed party default.** `parties = list(cfg.gate.get("gate_parties", ["ANC","DA","EFF"]))` (`pools.py:3479`) silently duplicates `config/dimensions.toml`'s own `gate_parties`, and would take over unnoticed if that block were renamed or dropped. Replace the fallback with a refusal — a dimension gate keyed to three parties typed in code is the class the owner ruled out on 2026-08-30, because the cast changes every cycle and a typed default cannot. ⚠️ **This fix was written and REVERTED on 2026-08-31**, in the same session that queued it: it is executable code, so it moved `pools_sha` from `dbdf171344ffd5f0` to `e44c09169ba266ca` and every one of the eighteen specs immediately reported STALE. **The guard worked; the discipline did not.** Recorded here rather than in a comment because the failure is instructive — a change can be small, correct, and still belong in the window. | Trivially number-neutral in intent (the config already declares the same three parties, so nothing computed changes), **and that is the acceptance test** — emit before and after and diff. Bundle with entry 5, which is the other party-cast change. | §1.141, 2026-08-31 |
| 5 | ⛔ **THE PARTY CAST IS TYPED INTO CODE IN TWO PLACES, AND ONE OF THEM DECIDES HOW EVERY UNSEEN PARTY IS SIZED.** **(a) `pools.SPLITS`** (`pools.py:2155`) types six parties and their parents — COPE, EFF, NFP, GOOD, MK, ASA — and `classify_arrival` reads it to decide whether a party absent from the baseline is sized as **a fraction of a named parent** or **at the typical entrant's result**. Two different machineries, chosen by a dict literal. A party that splits before 2026 and is not typed in is silently routed to the entrant path with no warning; COPE/NFP/GOOD sit in `exclude=frozenset(SPLITS)` forever even in cities where they arrived from nothing. The file's own docstring records that getting ActionSA's classification wrong produced 0.1% against an actual 18.12%. **(b) `levels.TYPE_A_EVENTS`** (`levels.py:411`) types six party-years that, when `FILTER_TYPE_A` is set, are dropped from the record `sd(log θ)` is estimated from — so it moves **every band width in the forecast**. Currently off behind an env var, and one env var from being live. **Three of its six rows are already restatable from SPLITS** (its own comments say so). **The fix:** move both into one tracked `config/splits.toml` — `parent`, `pair`, `why`, `home` per party, plus the two non-split event shapes (`MERGER_ABSORBED`, `LEADER_DEATH`) as dated rows. `classify_arrival` then reads city judgement → `config/splits.toml` → entrant, which is the precedence it already has for the judgement layer. Nothing about the mechanism changes; the cast becomes editable without touching `pools.py`. ⚠️ **`tests/test_chain.py` and `test_blended_centres.py` currently PIN THE HARDCODING AS THE CONTRACT** — they assert on `SIMULATION_BLOC`, `PLAN_BOUNDS` delivery and `classify_arrival`'s precedence. They move in the same commit or they fail for the right change. | Moving a table out of `pools.py` changes the file's code hash and therefore the artefact key, even if every emitted value is identical. **Verify number-neutrality explicitly**: emit before and after and diff the specs — if anything moves, the table was transcribed wrong. Unlike entry 4 this SHOULD be number-neutral, and that is the test. | §1.140, 2026-08-30 |
| 4 | ⛔ **`pools.metro_file` CANNOT SEE THE 2000 AND 2006 METRO RESULTS, WHICH ARE ON DISK.** It resolves only `_metros/lge{year}_{CODE}_vd_party.csv` and `_reports/…_downloadable_party_results.csv` — 2011, 2016 and 2021 only — while the archive holds eight reconciled `lge2006_{CODE}_vd_party_clean.csv` (and `lge2000_JHB`) that `levels._citywide` reads every run, and that `DATA-QUALITY.md` item 13 verified at 100% reconciliation. **Verified consequence:** `metro_file('JHB','2006')` is `None`, `entrant_record(lge_transitions(before='2016'))` is `[]`, so `arrival_rules` takes its `if not record: return {}, {}` exit and **all eight 2016 specs carry zero seeds and `arrival_group: null`** — the whole reason the arrival validation is one cycle wide. **The record is NOT the constraint**: `arrival_group_record('2016')` returns 6 rows (totals 1.64/0.36/2.56/5.61/1.02/0.41%), so §1.135's *"not enough record to fit"* is wrong and `arrival_group_spec` returned `None` on `not parties`. The reader already exists inside `pools.py` — `_npe_citywide_for` reads the clean format from that directory — so this is WIRING, not new parsing. **Then**, second step, reconcile the two arrival definitions: `arrival_group_record` counts local > 0 and preceding NPE ≤ 0 (`:2549`), `newcomers` additionally requires absence from the preceding-LGE `composition` (`:3263-3266`). | ⛔ **THIS ONE MOVES NUMBERS, NOT ONLY `pools_sha`.** Entries 1-3 change a key; this changes every fitted quantity in every spec — the entrant record, the arrival-group record, the splinter records and the pool ratios all gain rows. The window's "re-take the baseline" step is load-bearing here in a way it is not for the others, and a fresh baseline is mandatory. ⛔ **DO NOT TAKE THIS ROW ALONE — IT IS ONE THIRD OF A SINGLE CHANGE.** Widening the reader adds rows to `arrival_group_record` (22 → 29), which is the input to **entry 11** (population and statistic both wrong, right by accident) and to the **R-1 decision** (§1.180, JUDGEMENT-CALLS §L6: pooled MEAN over ENTRANTS ONLY; recency measured and not supported). All three are the same two functions — `arrival_group_record` and `_arrival_total_prior`. Taken separately they measure one quantity three times against three different records and believe the last. **One commit, one pre-registration.** | §1.136, 2026-08-29; coupling §1.179-§1.180, 2026-09-03 |
| 3 | **A roster/reach seam for a target that has not happened.** Both inputs the group-arrival mechanism needs — `contesting_parties` (who is standing) and `_ward_reach` (where) — read the target's **result file**, which does not exist at 2026. So `roster_is_real` is False, `arrival_group_spec` returns `None`, and the emitted 2026 spec carries `arrival_group: null`: the mechanism cannot be CONSTRUCTED, not merely switched off. Add a declared-roster path (the code's own suggestion is `judgements/joburg-2026.toml`) so a published nomination list can be supplied on 16 September **without a code change on the day**. | Changing where a roster comes from changes what the code computes, so it moves `pools_sha`. The re-emit it forces is one the roster itself would have forced anyway. | §1.135, 2026-08-29 |
| 2 | **`pools._target_roll` reads the crosswalk from `target.processed`** (`pools.py:1910`) and must read `city.processed` — i.e. `target.crosswalk`. **This is what blocks `pools.py --city <any non-joburg> --target 2026 --emit`**, so no second city can have a 2026 spec until it lands. Its own docstring already states the intent ("that lands in *the city's own processed directory*"); the code disagrees with it. The refusal message at `:1912-1922` names the wrong path and must be corrected with it. | Changing a path expression changes what the code computes, so it moves `pools_sha`. Everything else in F15 landed in §1.120 without touching `pools.py`. | §1.120, 2026-08-28 |
| 1 | **`pools.CONFIG` is frozen as a function default** in three signatures — `artefact_key`, `stale_reason`, `load_config` (`config_path: Path = CONFIG`). Rebinding `pools.CONFIG` moves nothing, in parent or worker. | Resolving it in the body is a change to what the code computes. It is the `LEVEL_DF` §1.33 class, and it is why `pools.CONFIG` is deliberately **left out** of `montecarlo.MODULE_CONSTANTS` — declaring it would record the live attribute while the computation used the frozen one, which is a FALSE delivery proof rather than a missing one (§1.106). | §1.106, 2026-08-27 |


---

## Windows already taken (so the next reader knows why the key moved)

**2026-09-02 — §1.160/§1.161, and NOT this queue.** The delimitation fix and the
crosswalk-reader delegation are `pools.py` code changes that were *not* batched
through this file: they were forced by a defect being fixed, not chosen for a
window. `pools_sha` moved `1bf57e9bb84ee0dc → 86995c914b530216` and **all 26**
specs (18 original + 8 new 2011 targets) were re-emitted.

**None of entries 1–6 was taken in that window**, deliberately:

* **Entry 4 moves numbers and is booked behind ultra review #1** (CLAUDE.md,
  "review it BEFORE the re-emit"). Taking it opportunistically because a window
  happened to be open is exactly the trade that review exists to prevent.
* **Entries 5 and 6** are the party-cast changes and belong together.
* **Entry 2 is still open.** ⚠️ Note that the SAME defect — reading a
  city-level crosswalk through `target.processed` — was written afresh in
  `pools.vd_map` on 2026-09-02 and caught before it shipped (§1.161 §3). The
  class recurs; entry 2 is the remaining instance.

So the queue is unchanged and still has six entries. A window being open is not
a reason to spend it.

---

## Considered and NOT queued

* **`pools._LOG_FLOOR`** — kept and declared rather than deleted (owner,
  2026-08-28). Unexercised, not dead: the two-census interpolation is capability
  a second census would need immediately, and the Stats SA correspondence is
  live on exactly that. Declared by comment and in `JUDGEMENT-CALLS.md`, neither
  of which moves the hash. §1.119
* **The `ALPHA_*` family and the other ten emit-time constants** — no change is
  proposed. They are correctly absent from `MODULE_CONSTANTS`; their delivery
  proof is `pools_sha` itself, so a sweep of any of them that does not move the
  key never arrived (§1.106).
* **F18's crosswalk deduplication** — deliberately scoped to leave `pools.py`
  alone. `pools._target_roll` is a separate, intentional roll sum and stays
  (§1.116).
