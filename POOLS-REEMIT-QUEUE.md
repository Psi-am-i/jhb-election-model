# What is waiting for the next `pools.py` re-emit window

**A CODE change to `src/pools.py` moves `pools_sha` and invalidates every pool
spec** — count them with step 3's command, never from a number in a document. Re-emitting is cheap and deterministic — it changes nothing but the
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
2. Re-emit every spec, with nothing else running.

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

   ⛔ **THIS PARAGRAPH USED TO CARRY A COUNT AND THE COUNT WENT STALE — which
   is precisely the failure it was written to warn about.** It said the loop
   emits 27 against 26 on disk, the 27th being `tshwane/pools_2026.json`, which
   queue entry 2 made emittable and which "has never been emitted". It has:
   the 2026-09-08 window emitted every spec, `tshwane/pools_2026.json` among
   them, so the before-count and the after-count are now the same number and an
   operator following this step would have gone looking for a discrepancy that
   is not there. **Verified 2026-09-13 by running the `find` above and by
   `tests/test_register_matches_code.py`, whose `DELETED` note records the same
   window re-emitting the full set.**

   ⚠️ **So no count is written here, in either direction.** Run the loop, run
   the `find`, and check that what is on disk is what the loop issued and that
   every spec carries one `pools_sha`. **Count against what the loop issued,
   not against a number in a document** — including this one.

   *(Undecided, and it must be decided before the window: does Tshwane also
   need a `--simulation` spec? Johannesburg has one. If yes the loop issues one
   more than it does today.)*
4. Re-take the baseline (`compare_history`) and the freeze, in that order, on a
   settled tree. **Every number quoted afterwards comes from that run.**

---

## Queued — two entries, both opened 2026-09-13

⛔ **THE ENTRY NUMBERS ARE ONE NAMESPACE SHARED WITH
`audits/ULTRA-REVIEW-1-pools-reemit.md`, WHICH IS FROZEN.** The brief uses
**1-6** for the rows below and **7-10** for its own amendments (7 = the turnout
band, 8 = `_nnls`, 9 = the pool-bounds guard, 10 = the C and D terms). A new row
here therefore starts **above the highest number already used in either
document**. ⚠️ **This sentence used to name that number and it has been outgrown
twice** — it said 11, and the rows below now reach past it. Read the tables and
take the next one from them; do not take it from here. This was got wrong once, on 2026-09-03: the
arrival-budget row was filed as "entry 7" and collided with the brief's turnout
band — two live changes in one batch under one name, and a reviewer would have
checked the wrong one. **Never renumber an existing row**; the brief cannot be
amended and the references are spread across a dozen files.

⛔ **ENTRIES 4 AND 11 AND THE R-1 DECISION ARE ONE CHANGE, NOT THREE.** They are
the same two functions (`arrival_group_record`, `_arrival_total_prior`); entry 4
widens the record 22 → 29 rows, so entry 11's measurements must be re-derived
*after* it and R-1 (§1.180 / §L6) is a decision about that same statistic. The
only forecast-moving work in this queue is those three together. See both rows.

**ENTRIES 19 AND 20 ARE QUEUED. Entries 1-6 are not** — they were VERIFIED IN
CODE ON 2026-09-08, ENTRY BY ENTRY, and the table below had said otherwise for
days, which was the third time a tracking document in this batch understated the
tree (R4, §1.197; entry 11; then all six). **Those rows have not been deleted**:
every one is in *Landed in the tree* with the grep that proves it. What each
check found:

| # | proof it is in the tree |
|---|---|
| 1 | `config_path: Path = CONFIG` appears **0** times — resolved in the body |
| 2 | `target.crosswalk` appears **2** times |
| 3 | `declared_roster` / `resolve_roster` both defined |
| 4 | `grep -cE "\b_citywide_for\(" src/pools.py` returns **10** — one `def` and **nine** call sites. ⚠️ **Three probes for this one row were wrong before one was right (2026-09-12), and entry 4 is the entry that moves NUMBERS.** (a) The row cited `or _npe_citywide_for` at 9 sites; the wiring was refactored into the `_citywide_for` helper and that token now survives only inside a COMMENT, so the proof returned 1 and read as "never landed". (b) The helper's own docstring said "all eight sites" when there were nine. (c) `[^_]_citywide_for\(` still matches INSIDE `_npe_citywide_for` (the preceding char is `e`), so it over-counts. Use the word boundary: `_` is a word char, so `\b` cannot match between `e` and `_`. §1.224. |
| 5 | `unclassified_with_national_record` emitted into the spec |
| 6 | `_required_gate` at **4** sites |

**Do not read the length of the *Landed* table as work outstanding** — none of
it is. The outstanding work is entries 19 and 20 below, and then the window.

### Entry 4, checked again on 2026-09-13 — and the claim about it needs two corrections

`_citywide_for` is wired at every site that needs a metro-year's citywide shares
(the `\b_citywide_for\(` grep above), and its `_npe_citywide_for` fallback serves
**all eight metros at 2006**, where `metro_file` returns nothing for any of them.
So **`metro_file` is no longer the binding constraint** and §1.136's account of
the 2016 specs is history rather than current state.

⚠️ **Two things that were said about this row are wrong, and both were checked
rather than assumed.**

1. **The arrival record does not start at 2004→2006.** It starts one cycle
   earlier, at 1999→2000, with a single Johannesburg row — `levels.HELD_BACK`
   gates `lge2000` and `npe1999` for the other seven metros and **not** for
   Johannesburg, so that one row flows through while its seven siblings do not.
2. **2004→2006 is not eight metros, it is six.** The READER serves all eight;
   the RECORD drops Mangaung and Buffalo City at that cycle through the
   `len(arr) < 3` floor (JUDGEMENT-CALLS §L7, which names those two rows as
   among the three smallest arrival totals in the whole record). "The reader can
   see it" and "the record contains it" are different claims and this row
   conflated them.

Re-derive the row count from `pools.arrival_group_record()` rather than from any
figure in this file; the 22 → 29 widening the coupling warning above depends on
is the quantity to check, and it is a live call, not a number.

⛔ **ENTRY 11 LANDED ON 2026-09-03**, folded into entry 4 as the coupling warning above it required, under `prereg/2026-09-03-arrival-record-widening.md` P2. Verified in code 2026-09-08: `_arrival_total_prior` returns `np.mean([e for _, _, e in rec])` — the MEAN, over the ENTRANTS-ONLY third element. **The batch plan's checklist still read it as unstarted for five days**, which is the second time that block has understated the tree (the first was R4 itself, §1.197). Its full evidence is kept below in *Landed in the tree*.

### The queued entries

⛔ **BOTH ARE IN `pools._EMIT_DEPENDENCIES` TERRITORY AND NEITHER CAN BE TAKEN
OUTSIDE THE WINDOW.** Entry 19 changes `parties.py`, which is an emit dependency,
so it moves `deps_sha`; entry 20 changes a message string in `pools.py`, which
`_code_sha` hashes, so it moves `pools_sha`. Each invalidates every spec.

| # | change | what it moves, and the acceptance test | opened |
|---|---|---|---|
| 19 | ⛔ **A PARTY THAT CHANGES ITS REGISTERED NAME BETWEEN ELECTIONS BECOMES AN ARRIVAL CARRYING ITS PREDECESSOR'S FULL VOTE, AND NOTHING DETECTS IT.** `parties.canonical` derives a code from the name, so the 1999 file's `NEW NATIONAL PARTY` and the 2004 file's `NUWE NASIONALE PARTY / NEW NATIONAL PARTY` fold to **different codes** — verified by calling `parties.canonical` on both — and `parties.ALIASES` has no entry for either. Every consumer that asks "did this party exist at the preceding election?" answers no. **Measured 2026-09-13, reading the raw NPE files directly and folding both spellings to one code: the 1999→2004 arrival pool falls in all eight metros, Cape Town's from 22.28% to 11.45%**, which is the largest. The fix is a `parties.ALIASES` entry. ⚠️ **The class is wider than the instance and is NOT closed by this row** — only the top arrival of each metro-year was ever checked. `DATA-QUALITY.md` item 17 carries the class and the detection method. | ⚖️ **Number-neutral on the tree as it stands, on evidence, and the evidence is narrower than the change.** **No LGE file carries either spelling** (grep over `data/`; both occur only in `npe1999_approx_*` and `npe2004_*`), and the NNP had dissolved before the 2006 local election, so no local record moves. Probed read-only in fresh processes, with a positive control that fires and reverts: adding the alias leaves `levels.theta_record` for all eight metros at 2011/2016/2021 and `pools.arrival_group_record` / `home_splinter_record` at all four targets **byte-identical**. ⛔ **That is not the emitted spec.** The acceptance test is the window's own: emit, and diff every spec. Anything that moves is a consumer the probe did not reach. | 2026-09-13 |
| 20 | **`pools.arrival_rules` emits a `RETROSPECTIVE` warning that is false at every spec on disk.** The at-home branch of `band_for` labels its record *"home-city splits (…), RETROSPECTIVE: not all precede this target"* **unconditionally**. That was true until the target cutoff landed on 2026-08-14; since then the home record handed to that branch is already filtered, and the label survives as a claim about the code's own behaviour that the code stopped having. **Verified 2026-09-13: no spec on disk carries a `splinter_home.measured_at` year at or after its own target**, so the warning is false on every one. It is read where it does most harm — `seed_notes["ASA"]` in the 2021 specs, the note beside the largest arrival in the panel. ⚠️ **The fix is to make the label CONDITIONAL, not to delete it**: under `--retrospective-home` the cutoff is off and the warning is true and wanted. MODEL-LOG §1.232. | **Number-neutral in intent — it is a note, not a computation** — and it still moves `pools_sha`, because `_code_sha` hashes string constants. Same class as entry 16, and for the same reason it belongs in this batch rather than in a window of its own. Acceptance test: emit and diff; `seed_notes` and the artefact key should move and nothing else. | 2026-09-13 |


---

## Landed in the tree, awaiting only the pending emit

⛔ **THESE ARE NOT QUEUED — THEY ARE IN THE CODE.** They landed after the batch
commit and before the emit window, which is the one moment such a change is
cheap: `pools_sha` has to move for the batch anyway, so a number-neutral repair
taken now costs nothing, and the same repair taken a day after the emit costs a
whole window. **They share the batch's numbering namespace** (see the warning
above the queued table) and are listed here so the next reader can tell what the
key moved for.

⚠️ **All three came out of ultra review #1** (`audits/ULTRA-REVIEW-1-pools-reemit.md`),
were re-derived against the tree before being applied, and are number-neutral on
the tree as it stands — **which the emit must confirm, not assume**: emit, and
diff the specs. Anything that moves means one of them was transcribed wrong.

| # | change | why it is number-neutral today | landed |
|---|---|---|---|
| 6 | **`pools.gate`'s typed party default.** `parties = list(cfg.gate.get("gate_parties", ["ANC","DA","EFF"]))` silently duplicates `config/dimensions.toml`'s own `gate_parties`, and would take over unnoticed if that block were renamed or dropped. Replace the fallback with a refusal — a dimension gate keyed to three parties typed in code is the class the owner ruled out on 2026-08-30, because the cast changes every cycle and a typed default cannot. ⚠️ **This fix was written and REVERTED on 2026-08-31**, in the same session that queued it: it is executable code, so it moved `pools_sha` from `dbdf171344ffd5f0` to `e44c09169ba266ca` and every one of the eighteen specs immediately reported STALE. **The guard worked; the discipline did not.** Recorded here rather than in a comment because the failure is instructive — a change can be small, correct, and still belong in the window. | Trivially number-neutral in intent (the config already declares the same three parties, so nothing computed changes), **and that is the acceptance test** — emit before and after and diff. Bundle with entry 5, which is the other party-cast change. | §1.141, 2026-08-31 |
| 5 | ⛔ **THE PARTY CAST IS TYPED INTO CODE IN TWO PLACES, AND ONE OF THEM DECIDES HOW EVERY UNSEEN PARTY IS SIZED.** **(a) `pools.SPLITS`** types six parties and their parents — COPE, EFF, NFP, GOOD, MK, ASA — and `classify_arrival` reads it to decide whether a party absent from the baseline is sized as **a fraction of a named parent** or **at the typical entrant's result**. Two different machineries, chosen by a dict literal. A party that splits before 2026 and is not typed in is silently routed to the entrant path with no warning; COPE/NFP/GOOD sit in `exclude=frozenset(SPLITS)` forever even in cities where they arrived from nothing. The file's own docstring records that getting ActionSA's classification wrong produced 0.1% against an actual 18.12%. **(b) `levels.TYPE_A_EVENTS`** types six party-years that, when `FILTER_TYPE_A` is set, are dropped from the record `sd(log θ)` is estimated from — so it moves **every band width in the forecast**. Currently off behind an env var, and one env var from being live. **Three of its six rows are already restatable from SPLITS** (its own comments say so). **The fix:** move both into one tracked `config/splits.toml` — `parent`, `pair`, `why`, `home` per party, plus the two non-split event shapes (`MERGER_ABSORBED`, `LEADER_DEATH`) as dated rows. `classify_arrival` then reads city judgement → `config/splits.toml` → entrant, which is the precedence it already has for the judgement layer. Nothing about the mechanism changes; the cast becomes editable without touching `pools.py`. ⚠️ **`tests/test_chain.py` and `test_blended_centres.py` currently PIN THE HARDCODING AS THE CONTRACT** — they assert on `SIMULATION_BLOC`, `PLAN_BOUNDS` delivery and `classify_arrival`'s precedence. They move in the same commit or they fail for the right change. | Moving a table out of `pools.py` changes the file's code hash and therefore the artefact key, even if every emitted value is identical. **Verify number-neutrality explicitly**: emit before and after and diff the specs — if anything moves, the table was transcribed wrong. Unlike entry 4 this SHOULD be number-neutral, and that is the test. | §1.140, 2026-08-30 |
| 4 | ⛔ **`pools.metro_file` CANNOT SEE THE 2000 AND 2006 METRO RESULTS, WHICH ARE ON DISK.** It resolves only `_metros/lge{year}_{CODE}_vd_party.csv` and `_reports/…_downloadable_party_results.csv` — 2011, 2016 and 2021 only — while the archive holds eight reconciled `lge2006_{CODE}_vd_party_clean.csv` (and `lge2000_JHB`) that `levels._citywide` reads every run, and that `DATA-QUALITY.md` item 13 verified at 100% reconciliation. **Verified consequence:** `metro_file('JHB','2006')` is `None`, `entrant_record(lge_transitions(before='2016'))` is `[]`, so `arrival_rules` takes its `if not record: return {}, {}` exit and **all eight 2016 specs carry zero seeds and `arrival_group: null`** — the whole reason the arrival validation is one cycle wide. **The record is NOT the constraint**: `arrival_group_record('2016')` returns 6 rows (totals 1.64/0.36/2.56/5.61/1.02/0.41%), so §1.135's *"not enough record to fit"* is wrong and `arrival_group_spec` returned `None` on `not parties`. The reader already exists inside `pools.py` — `_npe_citywide_for` reads the clean format from that directory — so this is WIRING, not new parsing. **Then**, second step, reconcile the two arrival definitions: `arrival_group_record` counts local > 0 and preceding NPE ≤ 0 (`:2549`), `newcomers` additionally requires absence from the preceding-LGE `composition` (`:3263-3266`). | ⛔ **THIS ONE MOVES NUMBERS, NOT ONLY `pools_sha`.** Entries 1-3 change a key; this changes every fitted quantity in every spec — the entrant record, the arrival-group record, the splinter records and the pool ratios all gain rows. The window's "re-take the baseline" step is load-bearing here in a way it is not for the others, and a fresh baseline is mandatory. ⛔ **DO NOT TAKE THIS ROW ALONE — IT IS ONE THIRD OF A SINGLE CHANGE.** Widening the reader adds rows to `arrival_group_record` (22 → 29), which is the input to **entry 11** (population and statistic both wrong, right by accident) and to the **R-1 decision** (§1.180, JUDGEMENT-CALLS §L6: pooled MEAN over ENTRANTS ONLY; recency measured and not supported). All three are the same two functions — `arrival_group_record` and `_arrival_total_prior`. Taken separately they measure one quantity three times against three different records and believe the last. **One commit, one pre-registration.** | §1.136, 2026-08-29; coupling §1.179-§1.180, 2026-09-03 |
| 3 | **A roster/reach seam for a target that has not happened.** Both inputs the group-arrival mechanism needs — `contesting_parties` (who is standing) and `_ward_reach` (where) — read the target's **result file**, which does not exist at 2026. So `roster_is_real` is False, `arrival_group_spec` returns `None`, and the emitted 2026 spec carries `arrival_group: null`: the mechanism cannot be CONSTRUCTED, not merely switched off. Add a declared-roster path (the code's own suggestion is `judgements/joburg-2026.toml`) so a published nomination list can be supplied on 16 September **without a code change on the day**. | Changing where a roster comes from changes what the code computes, so it moves `pools_sha`. The re-emit it forces is one the roster itself would have forced anyway. | §1.135, 2026-08-29 |
| 2 | **`pools._target_roll` reads the crosswalk from `target.processed`** and must read `city.processed` — i.e. `target.crosswalk`. **This is what blocks `pools.py --city <any non-joburg> --target 2026 --emit`**, so no second city can have a 2026 spec until it lands. Its own docstring already states the intent ("that lands in *the city's own processed directory*"); the code disagrees with it. The refusal message beside it names the wrong path and must be corrected with it. | Changing a path expression changes what the code computes, so it moves `pools_sha`. Everything else in F15 landed in §1.120 without touching `pools.py`. | §1.120, 2026-08-28 |
| 1 | **`pools.CONFIG` is frozen as a function default** in three signatures — `artefact_key`, `stale_reason`, `load_config` (`config_path: Path = CONFIG`). Rebinding `pools.CONFIG` moves nothing, in parent or worker. | Resolving it in the body is a change to what the code computes. It is the `LEVEL_DF` §1.33 class, and it is why `pools.CONFIG` is deliberately **left out** of `montecarlo.MODULE_CONSTANTS` — declaring it would record the live attribute while the computation used the frozen one, which is a FALSE delivery proof rather than a missing one (§1.106). | §1.106, 2026-08-27 |
| 11 | ⛔ **LANDED 2026-09-03, WITH ENTRY 4, UNDER `prereg/2026-09-03-arrival-record-widening.md` P2. THE ARRIVAL GROUP BUDGET IS MEASURED OVER A WIDER POPULATION THAN IT IS SPENT ON, AND WITH THE WRONG STATISTIC. IT IS RIGHT BY ACCIDENT.** `group_total = _arrival_total_prior(...)` is the **median** of `arrival_group_record`, which counts every party with local votes and no preceding national vote — **splits included**, because EFF, ActionSA, COPE, GOOD, MK and the NFP all had no national record at their first local election. `arrival_rules` then spends that budget only over `entrant_sizes`, which **excludes every `as_split` party**. Re-derived over all 22 rows (2026-09-03): JHB 2021 is **19.99% as a group and 1.87% excluding splits**, a factor of 10.7; TSH 5.4x; EKU 5.1x. Pooled: all-arrivals median **2.1701% (used)**, entrants-only mean **2.2853% (correct)**. Two errors of opposite sign — population ~1.3x too broad, and a **median where the consumer is an expectation**, which is the same correction the entrant branch made on 2026-08-17 after the median under-forecast every arrival by a factor of four, undone here in aggregate. ⚠️ **THEY MUST MOVE TOGETHER**: entrants-only median alone is 1.6679% (**−23%**), all-arrivals mean alone is 4.2711% (**+97%**). *Not checked:* whether `as_split` routing agrees with `SPLITS` for every party in the record — a declared parent absent from `index` falls back to the entrant branch and **is** budgeted. | ⛔ **MOVES NUMBERS.** ⛔ **PRE-REGISTER ON THE POST-ENTRY-4 RECORD, NOT THIS ONE.** The 2.1701% → 2.2853% (+5.5%) above is measured on TODAY'S 22-row record and is the wrong number to pre-register, because entry 4 widens the record first. On the 29-row record the entrants-only pooled mean is **2.1867%**, so the correction against today's all-arrivals median of 2.1701% is **+0.8%, not +5.5%**. **The expected seat effect is therefore ~ZERO, and that is the PASS condition, not a disappointment** — this entry buys defensibility, not accuracy. If `compare_history` moves more than a seat or two, something else is coupled and the coupling is the finding. **If `compare_history` moves more than a seat or two, something else is coupled and the coupling is the finding.** Fix both halves in one commit; a one-sided fix is worse than the current state. ⛔ **AND IT IS COUPLED TO ENTRY 4 AND TO R-1 — ALL THREE ARE THE SAME TWO FUNCTIONS.** Entry 4 wires `_npe_citywide_for` into the shares sites, which ADDS rows to `arrival_group_record` (22 → 29). So the 2.1701% / 2.2853% measured here is taken on a record entry 4 changes, and the R-1 decision (pooled median vs recency for `_arrival_total_prior`) is a decision about *this same statistic*. **Taking them separately means measuring the same quantity three times against three different records and believing the last one.** Sequence: settle R-1, land entry 4, THEN re-derive this table on the widened record and fix both halves — one commit, one pre-registration. | §1.179, 2026-09-03 |
| 15 | **The adults reprojection was gated on the BASE dimension's delimitation while reprojecting on the AGE dimension's**. The gate and the operation read two different dimensions. Silent direction: base matches the election and age does not — the block never runs, `adults_by_ward` stays on its own polygon set, and the join to this election's wards **SUCCEEDS anyway because ward codes are reused**. Now gated independently on `int(age_delim) != delimitation_for(year)`. ⚠️ **The adults join still has NO key-set assertion** — `.get(w, 0.0)` reads an unmatched ward as zero adults and `_nest` fits `adult_share` to the floor rather than raising. Recorded, not fixed: a refusal on an unreachable path is a guard nothing can exercise. §1.207. | Every dimension in `config/dimensions.toml` is Census 2022 on delimitation 2021, so the two gates always agree and the branch is unreachable **today**. Verified rather than assumed: `pool_counts` run on nine city-years before and after, hashing all four count matrices, every fitted rate, `violations` and `unidentified` — **identical on all nine**. The emit must still confirm it by diff. Guarded by `test_each_census_dimension_is_reprojected_on_its_own_delimitation`, which CONSTRUCTS the divergence (base moved onto the election's delimitation, age left behind) and asserts exactly one reprojection runs; the old nesting gives zero. | 2026-09-08 |
| 17 | **The five definitions of "an arrival" are named, and one of them was documented backwards.** `pools.ARRIVAL_DEFINITIONS` registers all five with predicate, population, splits treatment, computing site and consumer; each site carries `# ARRIVAL DEFINITION: <NAME>`. `arrival_group_record`'s docstring claimed *"EFF, ActionSA, COPE, GOOD, MK and the NFP are all in these totals"* — **four of the six are in no row of the record**, because each held a preceding national vote. Measured: only NFP (2011, 5 rows) and ASA (2021, 4 rows) ever appear, so the all-arrivals/entrants-only distinction bites in 9 rows of 29. Corrected with the measured table. §1.206. | **No forecast number moves** — `_arrival_total_prior` already computed the entrants total from the actual membership, not from the docstring's list. The register is a new module-level dict, so it moves `pools_sha` while changing nothing computed; the corrected docstring does not move it at all. Guarded by two tests, three mutations run and all three caught. | 2026-09-08 |
| 18 | **Two comments claimed `read_municipality` handles the header drift between `_metros/` and the `_clean` files** (`pools.py` metro_roster, `archive.py`'s manifest). It does not and cannot: it parses the IEC raw header only and raises `KeyError: 'VOTINGDISTRICT'` on a clean file (verified). This is the comment that would tell a future session it is safe to widen `metro_file` — which breaks `metro_citywide`, `metro_roster` and `_ward_reach` at once, and would invite removing `entrant_record`'s reach skip. §1.208, batch plan R4. | Comment-only in both files, so it does not move `pools_sha` at all. Listed here because it belongs to the same batch's record, not because it forces the window. | 2026-09-08 |
| 16 | **The nesting-violation message accused the wrong term** (search `THE RATIO IS IMPOSSIBLE` in `pools.py`). It read *"registered is 187% of the level above it, **which is impossible**"*, which frames the roll — an in-person appearance with an ID book — as the suspect number against a modelled small-area census estimate. It now says the RATIO is impossible and the count is not, and states what the number impeaches: `_nest` forces every ward to its published totals, so only the SPLIT is estimated. The owner's ordering (2026-09-06): registration and votes outrank the census always; census is the apportionment key for the pool split and the soft eligible-pool ceiling, never a validator. §1.196. | A message string. `_code_sha` hashes the syntax tree and string constants are in it, so it moves the key while changing nothing computed — which is precisely why it goes in this batch and not in a window of its own. No test pins the text (this repository asserts numbers, not notes). | 2026-09-06 |
| 14 | **`overperform` is read in the `weights` branch of `arrival_rules` too**. `PARTY_KEYS` documents it as *"a multiplier on the default strength"* scoped to no branch, and the closed-key refusal ACCEPTS it beside `weights` — so a party declared with pools and a multiplier passed every guard, was seeded at the comparator mean, and said nothing. That is the silent-discard class `PARTY_KEYS` exists to close, surviving inside the mechanism that closed it. Both branches now compute `size = (stated or base) * mult` and set `judged = stated is not None or mult != 1.0`, so either key holds the party outside the group budget (§L2). | **No judgement file in the tree declares `weights`, `support` or `overperform`** — all 408 `[party.X]` tables carry `baseline_share` and `parent` and nothing else — so no party is `judged` and every emitted band and seed is computed exactly as before. The repair changes what happens on **16 September**, when a nomination list is pasted in under time pressure, and changes nothing measured before it. Guarded by case (6) of `test_a_declared_strength_is_read_and_does_not_narrow_its_own_band`, which asserts the implied citywide share (not the note) at 3x, the band unmoved, and the 29 undeclared entrants still holding the 1.75% record. | 2026-09-06 |
| 13 | **One name per dataset in `emit_pools`**. `record` was bound to `turnout_record(...)`, read by `turnout_band` and `turnout_limits`, and then rebound 240 lines later to `entrant_record(lge_transitions(...))` and passed to `arrival_rules`. Two unrelated series under one name inside one function: anything hoisted past the rebinding silently reads the other. Renamed to `entrant_hist` at all three sites. | A pure rename. It moves `pools_sha` because `_code_sha` hashes the syntax tree and `co_varnames` are in it — which is the point of entry 6's story: *"a change can be small, correct, and still belong in the window."* | 2026-09-06 |
| 12 | **`arrival_group_record`'s accumulator annotation matched its return type**. Declared `list[tuple[float, float]]`, returns `list[tuple[float, float, float]]`, appends `(total, alpha, entrants)`. Left over from the 2 → 3 widening the docstring is pinned on. | A local annotation is not evaluated at runtime and no value changes. It is in the AST, so it moves the key regardless. | 2026-09-06 |

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
