# What is waiting for the next `pools.py` re-emit window

**A CODE change to `src/pools.py` moves `pools_sha` and invalidates all eighteen
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
2. Re-emit all eighteen specs, with nothing else running:

       for c in joburg tshwane ekurhuleni ethekwini capetown mangaung \
                nelsonmandelabay buffalocity; do
         for y in 2016 2021; do
           .venv/bin/python src/pools.py --city $c --target $y --emit
         done
       done
       .venv/bin/python src/pools.py --city joburg --target 2026 --emit
       .venv/bin/python src/pools.py --city joburg --target 2026 --simulation --emit

3. Confirm all eighteen carry ONE `pools_sha` and that it matches the new code.
4. Re-take the baseline (`compare_history`) and the freeze, in that order, on a
   settled tree. **Every number quoted afterwards comes from that run.**

---

## Queued

| # | change | why it needs the window | raised |
|---|---|---|---|
| 6 | **`pools.gate`'s typed party default.** `parties = list(cfg.gate.get("gate_parties", ["ANC","DA","EFF"]))` (`pools.py:3479`) silently duplicates `config/dimensions.toml`'s own `gate_parties`, and would take over unnoticed if that block were renamed or dropped. Replace the fallback with a refusal — a dimension gate keyed to three parties typed in code is the class the owner ruled out on 2026-08-30, because the cast changes every cycle and a typed default cannot. ⚠️ **This fix was written and REVERTED on 2026-08-31**, in the same session that queued it: it is executable code, so it moved `pools_sha` from `dbdf171344ffd5f0` to `e44c09169ba266ca` and every one of the eighteen specs immediately reported STALE. **The guard worked; the discipline did not.** Recorded here rather than in a comment because the failure is instructive — a change can be small, correct, and still belong in the window. | Trivially number-neutral in intent (the config already declares the same three parties, so nothing computed changes), **and that is the acceptance test** — emit before and after and diff. Bundle with entry 5, which is the other party-cast change. | §1.141, 2026-08-31 |
| 5 | ⛔ **THE PARTY CAST IS TYPED INTO CODE IN TWO PLACES, AND ONE OF THEM DECIDES HOW EVERY UNSEEN PARTY IS SIZED.** **(a) `pools.SPLITS`** (`pools.py:2155`) types six parties and their parents — COPE, EFF, NFP, GOOD, MK, ASA — and `classify_arrival` reads it to decide whether a party absent from the baseline is sized as **a fraction of a named parent** or **at the typical entrant's result**. Two different machineries, chosen by a dict literal. A party that splits before 2026 and is not typed in is silently routed to the entrant path with no warning; COPE/NFP/GOOD sit in `exclude=frozenset(SPLITS)` forever even in cities where they arrived from nothing. The file's own docstring records that getting ActionSA's classification wrong produced 0.1% against an actual 18.12%. **(b) `levels.TYPE_A_EVENTS`** (`levels.py:411`) types six party-years that, when `FILTER_TYPE_A` is set, are dropped from the record `sd(log θ)` is estimated from — so it moves **every band width in the forecast**. Currently off behind an env var, and one env var from being live. **Three of its six rows are already restatable from SPLITS** (its own comments say so). **The fix:** move both into one tracked `config/splits.toml` — `parent`, `pair`, `why`, `home` per party, plus the two non-split event shapes (`MERGER_ABSORBED`, `LEADER_DEATH`) as dated rows. `classify_arrival` then reads city judgement → `config/splits.toml` → entrant, which is the precedence it already has for the judgement layer. Nothing about the mechanism changes; the cast becomes editable without touching `pools.py`. ⚠️ **`tests/test_chain.py` and `test_blended_centres.py` currently PIN THE HARDCODING AS THE CONTRACT** — they assert on `SIMULATION_BLOC`, `PLAN_BOUNDS` delivery and `classify_arrival`'s precedence. They move in the same commit or they fail for the right change. | Moving a table out of `pools.py` changes the file's code hash and therefore the artefact key, even if every emitted value is identical. **Verify number-neutrality explicitly**: emit before and after and diff the specs — if anything moves, the table was transcribed wrong. Unlike entry 4 this SHOULD be number-neutral, and that is the test. | §1.140, 2026-08-30 |
| 4 | ⛔ **`pools.metro_file` CANNOT SEE THE 2000 AND 2006 METRO RESULTS, WHICH ARE ON DISK.** It resolves only `_metros/lge{year}_{CODE}_vd_party.csv` and `_reports/…_downloadable_party_results.csv` — 2011, 2016 and 2021 only — while the archive holds eight reconciled `lge2006_{CODE}_vd_party_clean.csv` (and `lge2000_JHB`) that `levels._citywide` reads every run, and that `DATA-QUALITY.md` item 13 verified at 100% reconciliation. **Verified consequence:** `metro_file('JHB','2006')` is `None`, `entrant_record(lge_transitions(before='2016'))` is `[]`, so `arrival_rules` takes its `if not record: return {}, {}` exit and **all eight 2016 specs carry zero seeds and `arrival_group: null`** — the whole reason the arrival validation is one cycle wide. **The record is NOT the constraint**: `arrival_group_record('2016')` returns 6 rows (totals 1.64/0.36/2.56/5.61/1.02/0.41%), so §1.135's *"not enough record to fit"* is wrong and `arrival_group_spec` returned `None` on `not parties`. The reader already exists inside `pools.py` — `_npe_citywide_for` reads the clean format from that directory — so this is WIRING, not new parsing. **Then**, second step, reconcile the two arrival definitions: `arrival_group_record` counts local > 0 and preceding NPE ≤ 0 (`:2549`), `newcomers` additionally requires absence from the preceding-LGE `composition` (`:3263-3266`). | ⛔ **THIS ONE MOVES NUMBERS, NOT ONLY `pools_sha`.** Entries 1-3 change a key; this changes every fitted quantity in every spec — the entrant record, the arrival-group record, the splinter records and the pool ratios all gain rows. The window's "re-take the baseline" step is load-bearing here in a way it is not for the others, and a fresh baseline is mandatory. | §1.136, 2026-08-29 |
| 3 | **A roster/reach seam for a target that has not happened.** Both inputs the group-arrival mechanism needs — `contesting_parties` (who is standing) and `_ward_reach` (where) — read the target's **result file**, which does not exist at 2026. So `roster_is_real` is False, `arrival_group_spec` returns `None`, and the emitted 2026 spec carries `arrival_group: null`: the mechanism cannot be CONSTRUCTED, not merely switched off. Add a declared-roster path (the code's own suggestion is `judgements/joburg-2026.toml`) so a published nomination list can be supplied on 16 September **without a code change on the day**. | Changing where a roster comes from changes what the code computes, so it moves `pools_sha`. The re-emit it forces is one the roster itself would have forced anyway. | §1.135, 2026-08-29 |
| 2 | **`pools._target_roll` reads the crosswalk from `target.processed`** (`pools.py:1910`) and must read `city.processed` — i.e. `target.crosswalk`. **This is what blocks `pools.py --city <any non-joburg> --target 2026 --emit`**, so no second city can have a 2026 spec until it lands. Its own docstring already states the intent ("that lands in *the city's own processed directory*"); the code disagrees with it. The refusal message at `:1912-1922` names the wrong path and must be corrected with it. | Changing a path expression changes what the code computes, so it moves `pools_sha`. Everything else in F15 landed in §1.120 without touching `pools.py`. | §1.120, 2026-08-28 |
| 1 | **`pools.CONFIG` is frozen as a function default** in three signatures — `artefact_key`, `stale_reason`, `load_config` (`config_path: Path = CONFIG`). Rebinding `pools.CONFIG` moves nothing, in parent or worker. | Resolving it in the body is a change to what the code computes. It is the `LEVEL_DF` §1.33 class, and it is why `pools.CONFIG` is deliberately **left out** of `montecarlo.MODULE_CONSTANTS` — declaring it would record the live attribute while the computation used the frozen one, which is a FALSE delivery proof rather than a missing one (§1.106). | §1.106, 2026-08-27 |

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
