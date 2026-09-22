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

## Queued — read the table for what is outstanding, never a count from this line

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

**ENTRIES 19 AND 20 ARE QUEUED. Entries 21-25 LANDED on 2026-09-14 (§1.238) and are in *Landed in the tree* below with the greps that prove it; entry 26 landed earlier the same day. Entries 1-6 are not** — they were VERIFIED IN
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
it is. The outstanding work is entries 19-25 below, and then the window.

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

⛔ **EVERY ONE OF THESE IS IN `pools._EMIT_DEPENDENCIES` TERRITORY AND NONE CAN
BE TAKEN OUTSIDE THE WINDOW.** Entry 19 changes `parties.py`, which is an emit
dependency, so it moves `deps_sha`; entries 20-25 change `pools.py` — a message
string in 20's case, executable code in the rest — and `_code_sha` hashes both,
so each moves `pools_sha`. Entries 24 and 25 additionally move `config_sha` and
`gates_sha`. Each invalidates every spec. **Entries 21-25 have now done so**, in
the tree and un-emitted, which is why the two staleness guards are red until the
window is taken.

⛔ **ENTRY 23 LANDED 2026-09-14 AND THE DECISION BELOW IS NOW MOOT FOR
CORRECTNESS.** The derivation is right whether or not the paste carries
`[roster.wards]`; what a ward paste still needs on the night is a ward map for
the target year, or it refuses with an actionable message pointing at
`[roster.reach]`. The original framing is kept because it is the reason the row
was ranked where it was. It was the only row in this queue whose cost is
incurred on a specific night rather than at the next measurement, and whose damage is *invisible* — a 20-ward entrant sized as a
city-wide contender, carrying a reach value that 15 of the 55 parties in
`_ward_reach('JHB','2021')` legitimately hold. Its row states the one condition
that bounds the urgency, and that condition is a decision the owner has not yet
made: **whether the nomination paste will carry a `[roster.wards]` block at
all.**

⛔ **ENTRIES 21, 22, 23 AND 25 WERE ALL FAIL-OPEN OR CRY-WOLF PATHS, AND NONE
WAS A TUNING CHANGE. ALL FOUR LANDED 2026-09-14 (§1.238), EACH WITH A GUARD AND
EACH MUTATION-TESTED.** Each makes a mechanism that currently reports a wrong state
confidently report the right one. **Every one was found by the same instrument —
fault injection with a working revert, and each now HAS a guard built the same
way** (`tests/test_prior_local_fails_closed.py`,
`test_census_refusal_is_not_swallowed.py`,
`test_declared_reach_matches_ward_reach.py`,
`test_artefact_key_discriminates.py`), each mutation-tested.
⚠️ **One of those guards passed under the defect AND under its fix on the first
attempt** — it patched the sentinel's CONSUMER instead of running its
PRODUCER — and was rewritten until the mutation was caught. §1.238. Entries 21, 23 and 25 are expected to be number-neutral and the
evidence is in each row; **entry 22 is not certain to be, and entry 24 moves a
provenance field on purpose.** They are independent of one another and may be
taken separately.

⚠️ **A PROBE BUG WAS HIT AND CAUGHT WHILE VERIFYING ENTRY 25**, and it is worth
one line because this repository has been burned by the class before
(*"probe bugs look like findings"*). `stale_reason(spec, city, target)` takes the
**whole spec dict**, not its `artefact_key`. Passing the key returns *"emitted
before artefact keys existed"* for every spec — which reads exactly like a
finding about the tree and is a finding about the probe. The implausibility of
the result is what exposed it, not the code. **Any scan that reports the same
alarming thing about every member of its population should be suspected of
scanning the wrong thing first.**

⛔ **ENTRIES 21 AND 22 WERE BOTH FAIL-OPEN PATHS, AND NEITHER WAS A TUNING
CHANGE. BOTH LANDED 2026-09-14.** Both make a guard that currently scores a missing record as a safe
one say so instead. Entry 21 is expected to be number-neutral and emit-neutral
and the evidence for that is in its row; **entry 22 is not certain to be, and
its row says what must be decided before it lands.** They are independent — 21
is the roster/mass path, 22 the census-join path — and may be taken separately,
but both were found by the same instrument (fault injection with a revert). Both
LANDED on 2026-09-14 and each now carries a guard built the same way; entry 22
landed in the **survivable** form this paragraph called for, and the "not certain
to be number-neutral" reservation was discharged by measurement, not by
assumption (§1.238).

| # | change | what it moves, and the acceptance test | opened |
|---|---|---|---|
| 28 | ⛔ **THE SPLIT BRANCH OF `arrival_rules` DISCARDS `support` AND `overperform` IN SILENCE.** `elif as_split:` sizes every `parent = …` party at the splinter-record median (`f_mid`) and never reads the two keys the `weights` and entrant branches both read (`stated = declared.get("support")`). A size typed beside a parent is accepted by `PARTY_KEYS`, raises nothing, and changes nothing — found 2026-09-16 sizing the SACP, which is why §L13 uses `weights` + `support` instead of `parent`. **Fix:** the split branch reads both keys the same way and marks the party `judged`. | No spec on disk declares `support` beside a `parent`, so it SHOULD be number-neutral on every spec except the key hash — verify by emit-and-diff. Acceptance: a fixture with `parent` + `support = 0.01` seeds at 1%, and reverting the fix makes it seed at `f_mid` (mutation). | 2026-09-16 |
| 27 | ⛔ **TWO CONFIRMED RENAMES, AND THEY ARE NOT NUMBER-NEUTRAL — MEASURED, NOT ASSUMED.** The owner confirmed 2026-09-16: `CAPE COLOURED CONGRESS` = `NATIONAL COLOURED CONGRESS`, and `CAPE PARTY / KAAPSE PARTY` = `CAPE INDEPENDENCE PARTY / KAAPSE ONAFHANKLIKHEIDS PARTY`. Both are `parties.py` alias entries and belong with entry 19 (the NNP case), which is the same class. ⛔ **Unlike entry 19 these MOVE NUMBERS on the tree as it stands.** Probed in-process against a clean subprocess: `CAPE_PARTY_KAAPSE_PARTY` goes 1 -> 2 theta observations in **all eight metros** (theta is pooled over `levels.METRO_CODES`, so a Cape Town identity reaches Johannesburg), and `arrival_group_record('2026')`'s group-total sum falls 1.071016 -> 1.064779 — CIP's 0.635% at Cape Town 2021 ceasing to be an arrival, which is entry 19's predicted direction measured on a second instance. **The mechanism to carry forward: a merge does not only re-label, it JOINS two half-observations into a whole one**, at whatever transition the halves span — 2019->2021 here, not the 2021->2024 step the rename sits on. CCC->NCC alone moves nothing yet (theta pairs an NPE with the LGE that follows, and 2024's is the unheld 2026), but it will the moment Cape Town 2026 is forecast, where NCC carries 3.482% with no local record while CCC's 2.804% sits under a dead code. §1.243, corrected by §1.244. | ⛔ **Moves `deps_sha` and invalidates all 27 specs**, and — unlike every other row in this table — **an emit is not sufficient**: it changes model inputs, so it needs a PRE-REGISTRATION and a panel measured both ways before it ships. Do NOT fold it into the nomination-night emit, which is a two-spec roster change touching no code. Acceptance test: the theta record gains exactly the joins the merge licenses and no others, and the arrival delta equals the merged parties' own shares. | 2026-09-16 |
| 19 | ⛔ **A PARTY THAT CHANGES ITS REGISTERED NAME BETWEEN ELECTIONS BECOMES AN ARRIVAL CARRYING ITS PREDECESSOR'S FULL VOTE, AND NOTHING DETECTS IT.** `parties.canonical` derives a code from the name, so the 1999 file's `NEW NATIONAL PARTY` and the 2004 file's `NUWE NASIONALE PARTY / NEW NATIONAL PARTY` fold to **different codes** — verified by calling `parties.canonical` on both — and `parties.ALIASES` has no entry for either. Every consumer that asks "did this party exist at the preceding election?" answers no. **Measured 2026-09-13, reading the raw NPE files directly and folding both spellings to one code: the 1999→2004 arrival pool falls in all eight metros, Cape Town's from 22.28% to 11.45%**, which is the largest. The fix is a `parties.ALIASES` entry. ⚠️ **The class is wider than the instance and is NOT closed by this row** — only the top arrival of each metro-year was ever checked. `DATA-QUALITY.md` item 17 carries the class and the detection method. | ⚖️ **Number-neutral on the tree as it stands, on evidence, and the evidence is narrower than the change.** **No LGE file carries either spelling** (grep over `data/`; both occur only in `npe1999_approx_*` and `npe2004_*`), and the NNP had dissolved before the 2006 local election, so no local record moves. Probed read-only in fresh processes, with a positive control that fires and reverts: adding the alias leaves `levels.theta_record` for all eight metros at 2011/2016/2021 and `pools.arrival_group_record` / `home_splinter_record` at all four targets **byte-identical**. ⛔ **That is not the emitted spec.** The acceptance test is the window's own: emit, and diff every spec. Anything that moves is a consumer the probe did not reach. | 2026-09-13 |
| 20 | **`pools.arrival_rules` emits a `RETROSPECTIVE` warning that is false at every spec on disk.** The at-home branch of `band_for` labels its record *"home-city splits (…), RETROSPECTIVE: not all precede this target"* **unconditionally**. That was true until the target cutoff landed on 2026-08-14; since then the home record handed to that branch is already filtered, and the label survives as a claim about the code's own behaviour that the code stopped having. **Verified 2026-09-13: no spec on disk carries a `splinter_home.measured_at` year at or after its own target**, so the warning is false on every one. It is read where it does most harm — `seed_notes["ASA"]` in the 2021 specs, the note beside the largest arrival in the panel. ⚠️ **The fix is to make the label CONDITIONAL, not to delete it**: under `--retrospective-home` the cutoff is off and the warning is true and wanted. MODEL-LOG §1.232. | **Number-neutral in intent — it is a note, not a computation** — and it still moves `pools_sha`, because `_code_sha` hashes string constants. Same class as entry 16, and for the same reason it belongs in this batch rather than in a window of its own. Acceptance test: emit and diff; `seed_notes` and the artefact key should move and nothing else. | 2026-09-13 |
| 26 | ⛔ **THE EMITTED SPEC AND `montecarlo`'S OWN OFF-BALLOT DROP DISAGREE ABOUT WHAT THE 2026 BALLOT IS, AND NOTHING SAID SO.** `resolve_roster` (`:4765`) has resolved published/declared/projected since entry 3 landed, and `emit_pools` (`:5058`) has used that roster to drop off-ballot parties from the POOLS ever since — but the result was folded only into the free-text `provenance` sentence ("roster {roster_source}; reach {reach_source}"), never written as a field. Meanwhile `montecarlo.roster_for_target` (`:3521`, called `:3856`) asks only whether `CALENDAR[year].results` exists, gets `not_yet_held` for every target through 2026, and disables the OWN-CALLER off-ballot drop unconditionally — so the pools are built from a projected ballot while the theta-baseline drop that runs beside them is switched off, and the emitted spec carried no field a reader could check either claim against. Owner's framing: *"fix that gap so nobody is confused."* **The fix, in two halves.** (a) `emit_pools`'s return dict now carries `roster` (sorted list), `roster_source` and `reach_source` as top-level fields — the same values `provenance` already states in prose, machine-readable for the first time. (b) `roster_for_target` gains a **fourth** state, `"projected"`: for a not-yet-held target whose spec carries a `roster_source`, it returns that roster instead of an empty one, so the off-ballot drop runs against the SAME ballot the pools were built from. A spec that names a `roster_source` with no readable `roster` behind it **raises** rather than falling back to `not_yet_held` — the identical fail-closed discipline `contesting_parties` already has, one layer up (`tests/test_roster_fails_closed.py`, section 4, four constructed shapes: missing/empty/wrong-type). `arrival_group: None` at a projected roster is LEFT ALONE: `emit_pools` builds it only `if roster_source in ("published", "declared")` (`:5579`), which is `pools.py`'s own internal choice not to construct a structured arrival split from total ignorance about a hypothetical newcomer, and is a different mechanism from the drop this entry wires up — not the same defect, on inspection. | ⛔ **(a) MOVES `pools_sha`, IS INTENDED NUMBER-NEUTRAL, AND THE EMIT MUST CONFIRM IT.** Three new keys added to a dict that already contained the values as a substring of `provenance`; nothing computed changes. Acceptance test: emit and diff every spec — every existing field byte-identical, `artefact_key` moved, and `roster`/`roster_source`/`reach_source` present and matching the `provenance` sentence's own claim. ⚖️ **(b) is `montecarlo.py`, confirmed OUTSIDE `_EMIT_DEPENDENCIES`** (`("parties","cityconfig","ingest_lge","levels")`, `pools.py:337`) — it does not move `pools_sha` and forces no re-emit on its own. ⛔ **BUT (b) IS NOT NUMBER-NEUTRAL, AND MUST NOT BE FILED AS IF IT WERE.** It is INERT on the tree as it stands — every spec on disk today predates the `roster_source` field, so `roster_for_target` reads `None` and every target still resolves `not_yet_held`, unchanged ⛔ **THE CITATION THIS ROW USED AS ITS EVIDENCE WAS THE WRONG CRITERION, AND IS CORRECTED HERE, 2026-09-14.** The row cited `tests/test_roster_fails_closed.py::test_the_run_records_which_roster_state_it_was_in` — a real run against the live 2026 spec — as *verifying* that (b) is inert. That test **typed `NOT_YET_HELD`, `roster_size == 0` and an empty `roster_dropped` as literals**, so it was never evidence of inertness: it was a TRIPWIRE that this row's own acceptance test below is *designed* to trip. **Two criteria in one row that could not both hold** — the test "still asserts `NOT_YET_HELD`" and the acceptance test demands `03_roster.state == "projected"`. Reproduced end to end before repair, in an isolated tree, against a spec carrying those three fields with a **stand-in roster** — the spec's own pool composition, 35 parties; the real one is `resolve_roster`'s projection, a superset of it, which only the emit can produce — the same run returns **`projected`, a non-zero roster size and a non-empty drop (13 parties against that stand-in)**, and all three literals fail together — mid-window, reading as a regression rather than as the guard's own premise expiring (CLAUDE.md §4 requirement 3). **WHICH ONE WAS WRONG: the citation, not the claim.** (b) really is inert on the tree as it stands — every spec on disk carries no `roster_source`, verified by reading the JSON — and the acceptance criterion below is the right one and stands unchanged. The test now DERIVES what it expects from what the spec carries, has been run green in BOTH worlds (pre-emit and against a post-emit-shaped spec), and was mutation-tested three ways: cutting the spec→scenario wiring, making `roster_for_target` ignore the scenario, and making it invent a `projected` state the spec does not claim — each turns it red, and each reverts to green. **Once (a) is emitted with a real 2026 roster, (b) starts firing on the LIVE FORECAST**: the off-ballot drop will run for the first time at an unheld target, against an assumption rather than a fact — this is a deliberate reversal of the decision previously recorded in `roster_for_target`'s own docstring ("wiring the declared list into this drop would move the live 2026 forecast, which is a scored change and not a failure-path fix"), taken here because the disagreement between the two mechanisms was judged the larger defect. **This is the one number in the batch that a diff cannot certify by itself** — `compare_history` cannot arbitrate a target with no result to score against, so the acceptance test is procedural: after the emit, run the live 2026 forecast once with `--run-dir` and confirm `03_roster.state == "projected"` and that the console print announcing the projected roster as an assumption appears. ⚠️ **AND A SECOND CORRECTION TO THIS CRITERION, 2026-09-14: `roster_dropped` WILL NOT NAME THE PARTIES `pools.py`'s `dropped from the pools` PRINT REPORTS, AND MUST NOT BE EXPECTED TO.** The two drops are taken against **different populations** and their sets are **disjoint by construction of the two floors**. `pools.resolve_roster` deletes `deliberate` from `composition` — the fitted pool vectors — and `deliberate` is `(thin OR local_thin) AND composition`, while `thin` is *defined* as baseline parties **not in** `composition`, so `thin AND composition` is empty and pools drops only the `local_thin` half. `montecarlo.run_model` calls `levels.absent_from_ballot(base_city_d, roster)` where `base_city_d` is the preceding **NPE citywide baseline**, so it drops the baseline parties missing from the roster — which is the `thin` half, and `local_thin` is by definition absent from the baseline entirely. Partially reproduced: 13 parties dropped by `run_model` against a stand-in roster, every one a small 2024 national party with no local record. **The checkable criterion, which needs only the spec and the trace:** `03_roster.dropped` equals the parties in the run's baseline that are absent from the spec's own `roster` field, and no party appears in both. Expecting the two prints to agree would report a correct run as broken on the one night nobody has time to re-derive it. Guarded by `tests/test_roster_fails_closed.py` (positive control, four fault-injected unreadable-roster shapes, and the held-target non-override case) and `tests/test_stage_inputs.py` (`roster.projected_but_empty`, the calendar-agreement check widened both directions). One new test failure is EXPECTED and TEMPORARY while this entry sits un-emitted: `test_stage_inputs.py::test_a_real_run_produces_a_trace_that_passes_every_predicate` correctly reports `pools.stale` against the moved `pools_sha` — the guard working as designed, not a regression — and clears once the batch (this entry included) is emitted. | 2026-09-14 |


---

## Guard specifications for entries 21-25

**Both defects are FAIL-OPEN paths, so fault injection is the honest
instrument** — there is nothing to observe on a healthy tree, and a test whose
premise is a passing tree expires silently (`CLAUDE.md` §4). Each guard below is
written to §4's four-part standard for an absence-shaped claim, and each says
what it **cannot** prove. The exemplar for both is
`tests/test_roster_fails_closed.py`, which separates published / not-yet-held /
unreadable for `contesting_parties`; these are the same shape one layer down.

⛔ **ASSERT STATES, COUNTS AND MASSES — NEVER LOG TEXT.** A test pinned to a
message stays green while the arithmetic beside it is broken, and both of these
defects print a cheerful message while doing the wrong thing.

⚠️ **Neither guard may be written before the fix it guards**, and neither may be
written from these paragraphs alone: the four injections in guard A are the ones
that found the defect, and re-deriving them against the repaired code is the
check that the repair is the one specified rather than the one that makes the
test pass.

### Guard A — `tests/test_prior_local_fails_closed.py` (entry 21)

**The claim.** *No run weighs a roster deletion against a record it could not
read.* An absence claim, so:

**0. THE RIGHT POPULATION, BOTH DIRECTIONS.** The population is **every target
the emit loop issues**, not Johannesburg. Enumerate it from the loop's own
sources — `backtest.runnable_targets` plus the declared-roster targets — assert
the scanned set **equals** that population rather than merely being contained in
it, and scan both directions:

* *forward* — for every target, the fitting year's record resolves to state
  **read** and the two consumers run normally;
* *reverse* — for every target, each constructed unreachable state **refuses**.

The reverse direction is the one that stops the guard passing by refusing
everything, and the forward direction is the one that stops it passing by
refusing nothing. **The register→code direction is the one this repository's
guards have historically missed** (§4's scanned-the-wrong-set class), so assert
that every cause `_npe_citywide_for` can return is exercised by a case below —
iterate the state enum, do not list the cases by hand.

**1. IT LOOKED.** Spy on the real I/O, as `_support.election_files_read` does:
the fitting year's result file must actually be **opened**, and the shares must
come back non-empty. `_npe_citywide_for` is deliberately not memoised (the
`levels._citywide` docstring explains why the memo was rejected), which is the
property the spy depends on — **assert that too**, or the spy goes blind the day
someone adds a cache. Bound the population **two-sidedly as a fraction of a
computed denominator**: for each target, `len(prior_local)` against
`len(contesting_parties(city, fitting_year))` must lie inside a band, and
`sum(prior_local.values())` must be 1.0 to tolerance. A one-sided floor ratchets
— when it trips, the cheapest fix is to lower it.

**2. IT CAN SEE — AND GOES QUIET WHEN REVERTED.** Four constructed causes, and
**the fourth is the one that makes this guard worth writing**:

| injected cause | the ceiling must |
|---|---|
| no `CALENDAR[year].results` template | **REFUSE** |
| result file absent at both candidate paths | **REFUSE** |
| the election in `levels.HELD_BACK` | **REFUSE** |
| file read, `total == 0` (`BallotType` misses the filter) | **ADMIT** |

⛔ **The fourth row is the discriminator.** A naive repair — *refuse whenever
`prior_local` is empty* — passes the first three and **fails the fourth**, and
that is exactly the distinction the defect is about: a record that was read and
is genuinely empty is not a record that could not be read. Without this row the
guard would certify the wrong fix. After each injection, **revert it and assert
the refusal goes away and the admitted mass returns to its pre-injection value**
— a detector that cannot go quiet is not a detector.

**Assert the numbers, not the message:** on the unreachable injections assert
the refusal carries the *true* mass (the record read through an unpatched path),
not zero; on the reverted runs assert the deleted-party count and mass are
identical to the control. Do the same for the **second consumer**: `_local_thin`
(the §K2 floor) must refuse on an unreachable record and must still thin
normally on a genuinely empty one — assert the resulting roster **size**, which
is where the 35 → 62 divergence in entry 21 shows up.

**3. CONSTRUCTED INPUT, NOT OBSERVED.** Every case above is injected. Build the
`total == 0` file as a temporary CSV whose `BallotType` values miss the filter;
reach the absent-file case by redirecting `CALENDAR[<year>].results`, **not** by
moving anything under `data/` — `data/**` is gitignored, shared with every other
worker, and nothing restores it.

**And the thing that is not in the rule and matters most here:** patch
`_npe_citywide_for` to return a sentinel state and assert `resolve_roster`
**propagates** it. Without that, the helper can be perfectly correct and the
ceiling still be weighed on something else — and `resolve_roster` calls
`_npe_citywide_for` directly rather than through `_citywide_for`, so there is a
real second path to get wrong.

⚠️ **What this guard cannot prove.** It exercises `resolve_roster`, not
`emit_pools`. A spec emitted through a different path would not be covered, and
the only thing that closes that is the window's own emit-and-diff.

### Guard B — `tests/test_census_refusal_is_not_swallowed.py` (entry 22)

**The claim.** *No city-year leaves the record without the run saying which one
and why.* Note the shape: this is **not** "no city-year is ever dropped" —
dropping a genuinely absent election is correct — it is that **silence is
forbidden**. That reframing is what makes the claim testable.

**0. THE RIGHT POPULATION, BOTH DIRECTIONS.** The population is **every
(city, year) with a result file on disk**, computed from `CALENDAR` × the eight
cities by testing for the file, and asserted **equal** to what was scanned.
Both directions:

* every city-year `pool_counts` serves appears in `registration_series` /
  `turnout_record`; and
* every city-year it refuses appears in a **stated loss list carrying a cause**
  — `not_on_disk`, `held_back`, `census_join_unsafe` — and the causes partition
  the refused set with no residue. A refusal with no cause, or a cause not in
  the enum, fails.

**1. IT LOOKED.** Bound **two-sidedly, as a fraction of a computed denominator**:
`len(registration_series(city)) / len(years with a result file on disk for that
city)` must lie inside a band, per city. Assert the **refused set is non-empty**
(so the guard has something to see) **and bounded above** (so it cannot pass by
everything failing). ⚠️ **Today's refused set is an OBSERVED property of the
tree** — joburg 1999/2004/2019 — and `CLAUDE.md` §4 is explicit that a premise
like that expires silently. So it is the **denominator only**; the *detector* is
proved by §2, and if `DATA-QUALITY.md` item 18's `vd_map` repair is ever taken
the refused set legitimately shrinks and this bound must move with it.

**2. IT CAN SEE — AND GOES QUIET WHEN REVERTED.** One injection per refusal, each
reverted:

| refusal | how to make it fire | must then |
|---|---|---|
| `:1085` drift ceiling | lower `CENSUS_DRIFT_CEILING` until a real city-year trips (0.05 → 0.003 trips joburg 2000) | name the year **and** the drift cause; revert → the year returns and nothing is reported |
| `:1108` <50% wards matched | constructed empty/partial ward map for the target year | name the year and the match cause |
| `:1117` no ward joined | constructed disjoint ward keys | name the year and the join cause |
| genuinely absent file | redirect `CALENDAR[year].results` to a path not on disk | drop it quietly as `not_on_disk` — **this is the discriminator**, and a repair that simply makes every refusal fatal fails here |
| a real `TypeError` inside `pool_counts` | inject one | **PROPAGATE** — `:2593`'s `except (Exception, SystemExit)` must no longer swallow it |

⛔ **Assert the CONSEQUENCE, not only the membership.** The measured harm is a
band that narrows silently: on the drift injection, `turnout_band`'s widths move
by up to 23.1% while the centre does not. Assert the **widths** before and after,
and assert they return exactly on revert. A guard that checks only which years
are in the dict would stay green if the record were right and the band were
computed from something else.

**3. CONSTRUCTED INPUT, NOT OBSERVED.** Every injection above is a constructed
parameter or a redirected path. Nothing asserts a property of the census files
themselves.

⚠️ **What this guard cannot prove.** I could not construct a case where
`_reprojection_drift`'s `:1539` `None` ("nothing could be measured") admits a
join that the `:1108` guard then passes — on this tree the two are coupled, so
the `shift nan` message is a **false statement, not an open hole**. The guard can
therefore assert only that the message reports what was measured (a sentinel,
not a conclusion); **it cannot prove the fail-open is unreachable**, and that
should not be claimed. If the `vd_map` repair in `DATA-QUALITY.md` item 18 is
ever taken, the coupling changes and this must be re-derived.

⛔ **The honest name for both of these is mutation testing.** The four-part rule
is the cheap approximation. Before either guard is believed, change one line of
the repaired code — make the refusal a warning, make the sentinel compare equal
to zero — and confirm the suite goes red.

### Guard C — `tests/test_declared_reach_matches_ward_reach.py` (entry 23)

**The claim.** *There is one definition of reach, and the declared path computes
it.* Not an absence claim but an **agreement** claim, which is easier to test and
which the comment at `:4592` already asserts in prose — so the guard is the
comment made executable, and the reason it is needed is that the comment was
false while it read as verified.

**0. THE RIGHT POPULATION, BOTH DIRECTIONS.** The population is **every producer
of a reach value**, not the declared path alone. Enumerate them — today
`_ward_reach` and `declared_roster`'s derivation — and assert the enumeration
**equals** what the module actually contains, by scanning for the computation
rather than listing call sites by hand. ⚠️ **This is the register→code direction
this repository keeps missing:** a third reach producer added later must fail
this test, or the guard silently stops covering the thing it is named for. Assert
both directions — every enumerated producer is reached by a case, and every case
maps to an enumerated producer.

**1. IT LOOKED.** Assert the denominators are the **same quantity**, not merely
that two numbers match on one example: for a declaration covering the whole
ballot, `declared_roster`'s reach must equal `_ward_reach`'s for **every party**,
and the shared denominator must equal the city's ward count from
`vd_map(city, year)`. Bound two-sidedly against a computed denominator: the
number of parties compared must be a sensible fraction of
`len(contesting_parties(city, year))`, non-empty and not everything.

**2. IT CAN SEE — AND GOES QUIET WHEN REVERTED.** The three constructed cases
that found this defect, each reverted:

| construction | must give |
|---|---|
| one party on *k* of the city's *N* wards | reach **k/N** — today 20/135 = 0.1481, **not** 1.0 |
| the same party, plus a second on the other *N−k* | the first party's reach **unchanged** |
| an explicit `[roster.reach]` for that party | the declared value wins, derivation ignored |

⛔ **The second row is the load-bearing one and is the one a naive fix passes by
accident.** A repair that divides by `len(seen)` computed over a *fuller* paste
still makes reach depend on who else was typed; only a denominator taken from the
**city** makes it a property of the party. Assert invariance under adding and
removing other parties — that is the property, and the single-case equality is
just one instance of it.

**3. CONSTRUCTED INPUT, NOT OBSERVED.** Patch only the lineage read so the real
`declared_roster` body executes; **do not write into `judgements/`**, which is
tracked and shared. Assert the derivation is reached at all (it is guarded by
`if wards:`), or a `parties`-only fixture will pass this test by never running
the code.

⚠️ **What this guard cannot prove.** It tests the value, not the consumers. That
a wrong reach flips the `abs(r - 1.0) < 0.25` bucket in `comparators` and
maximises `arrival_group_spec`'s split weights is asserted **separately**, by
feeding both reach values through those two functions and asserting the bucket
and the weight — otherwise the reach could be repaired and a consumer still read
a stale copy.

### Guard D — `tests/test_artefact_key_discriminates.py` (entries 24 and 25)

**The claim.** *Every input the key hashes changes an emitted number, and every
input that changes an emitted number is hashed.* **Both directions matter and
they fail differently:** the forward direction failing is silent staleness
(entry 24); the reverse failing is cry-wolf (entry 25), and cry-wolf is the worse
of the two here because it trains the reader to ignore the field.

**0. THE RIGHT POPULATION, BOTH DIRECTIONS.** The population is **every component
of `artefact_key`** and **every environment gate `_gates_sha` hashes**. Derive
both from the code — iterate `artefact_key(...)`'s returned field names and the
`_gates_sha` state dict — never from a list typed in the test; `stale_reason`
already carries the scar of a set typed in two places. Assert the enumeration
equals what the functions produce, so a field added to either is covered or the
test fails.

**1. IT LOOKED.** For each key field, assert it is **non-constant**: something in
its declared population moves it. A field that never moves is not being checked
by anything. Bound two-sidedly — the number of fields that move under a given
perturbation must be exactly the ones expected, not "at least one".

**2. IT CAN SEE — AND GOES QUIET WHEN REVERTED.**

| construction | must give |
|---|---|
| two different `*.toml` in one directory, hashed by their own paths | **different** `config_sha` (today: identical — the defect) |
| a `config_path` that does not exist | a **stated** outcome, distinguishable from a real directory |
| zero `*.toml` in the directory | the **same** sentinel as `_cities_sha`'s zero-file case — today `"missing"` against `sha256("")[:16]` |
| edit a file in the directory | `config_sha` moves (this already holds — assert it so the repair cannot regress to hashing one file) |
| `THETA_WINDOW=2` | `stale_reason` returns **None** for every spec |
| `HELD_BACK_OFF=1` | `stale_reason` returns **a reason** for every spec |

⛔ **The last two rows are one test, not two, and taking only the first is how
this gets half-repaired.** Deleting the whole `_gates_sha` dict would satisfy the
`THETA_WINDOW` row and destroy the guard `HELD_BACK_OFF` provides. Assert both,
and revert each.

**3. CONSTRUCTED INPUT, NOT OBSERVED.** Build the config directories in a
temporary tree. ⚠️ **The `stale_reason` rows read the specs on disk, which is an
OBSERVED premise** — they pass today only because every spec is currently clean,
and they would expire the moment the tree is legitimately stale. Assert the
clean-baseline precondition **explicitly and skip loudly if it does not hold**,
rather than letting the test quietly become vacuous.

⚠️ **What this guard cannot prove.** It cannot prove `THETA_WINDOW` changes no
emitted number — only that `pools.py` never reads it and that `pools`'s sole use
of `levels` is `_held_back`. That is a **static** argument, and it is the
strongest one available without an emit; it must be re-derived if `pools` ever
grows a second use of `levels`. Assert *that*: the set of `levels` attributes
`pools` touches, scanned from the source, must equal `{_held_back}` — which turns
an argument into a tripwire.

---

## Landed in the tree, awaiting only the pending emit

⛔ **THESE ARE NOT QUEUED — THEY ARE IN THE CODE.** They landed after the batch
commit and before the emit window, which is the one moment such a change is
cheap: `pools_sha` has to move for the batch anyway, so a number-neutral repair
taken now costs nothing, and the same repair taken a day after the emit costs a
whole window. **They share the batch's numbering namespace** (see the warning
above the queued table) and are listed here so the next reader can tell what the
key moved for.

⚠️ **Entries 4, 5 and 6 came out of ultra review #1** (`audits/ULTRA-REVIEW-1-pools-reemit.md`),
were re-derived against the tree before being applied, and are number-neutral on
the tree as it stands. **This sentence said "all three" while the table held
fourteen rows, and it was already stale before entries 21-25 joined them** —
count the table, never this line. — **which the emit must confirm, not assume**: emit, and
diff the specs. Anything that moves means one of them was transcribed wrong.

| # | change | why it is number-neutral today | landed |
|---|---|---|---|
| 29 | ⛔ **LANDED 2026-09-21, §1.249 — and this one is NOT number-neutral.** `arrival_rules`' no-parent branch spread an entrant evenly over every pool (`np.full(n, 1/n)`), the same assumption removed from the composition path on 2026-08-31 and left standing in the copy that runs second and overwrites it. It now takes the city's own composition from `city_mix_for`, passed in so there is one definition, and raises if it is missing. | **It moves numbers, deliberately.** 18 of the 27 emitted specs carry at least one exactly-flat vector and 45 of them are in the live Johannesburg 2026 spec, so the emit will move the published forecast. Held for ultra review 2 (`audits/ULTRA-REVIEW-2-pool-seed-shapes.md`), which runs BEFORE the emit; `compare_history` is re-taken after. | 2026-09-21 |
| 21 | ⛔ **LANDED 2026-09-14, §1.238.** `_npe_citywide_state` returns `(shares, state)`; `_npe_citywide_for` is kept as the shares-only wrapper for the callers that legitimately skip a missing metro-year. `resolve_roster` refuses on any state but `read`, and `read` INCLUDES a genuine zero. Proof in the tree: `grep -c "def _npe_citywide_state" src/pools.py` returns 1 and `grep -c 'prior_local_state != "read"' src/pools.py` returns 1. Guarded by `tests/test_prior_local_fails_closed.py` (6 tests); the fix was mutated off and 2 of them went red. Re-verified over 32 city-years — every emit target plus every city's unheld target — all reading a real record, so the refusal blocks nothing. ⛔ **LANDED 2026-09-14, §1.238.** `_npe_citywide_state` returns `(shares, state)`; `_npe_citywide_for` is kept as the shares-only wrapper for the callers that legitimately skip a missing metro-year. `resolve_roster` refuses on any state but `read`, and `read` INCLUDES a genuine zero. Proof in the tree: `grep -c "def _npe_citywide_state" src/pools.py` returns 1 and `grep -c 'prior_local_state != "read"' src/pools.py` returns 1. Guarded by `tests/test_prior_local_fails_closed.py` (6 tests); the fix was mutated off and 2 of them went red. Re-verified over 32 city-years — every emit target plus every city's unheld target — all reading a real record, so the refusal blocks nothing. ⛔ **LANDED 2026-09-14, §1.238.** `_npe_citywide_state` returns `(shares, state)`; `_npe_citywide_for` is kept as the shares-only wrapper for the callers that legitimately skip a missing metro-year. `resolve_roster` refuses on any state but `read`, and `read` INCLUDES a genuine zero. Proof in the tree: `grep -c "def _npe_citywide_state" src/pools.py` returns 1 and `grep -c 'prior_local_state != "read"' src/pools.py` returns 1. Guarded by `tests/test_prior_local_fails_closed.py` (6 tests); the fix was mutated off and 2 of them went red. Re-verified over 32 city-years — every emit target plus every city's unheld target — all reading a real record, so the refusal blocks nothing. ⛔ **THE `complete = true` ROSTER DELETION CEILING FAILS OPEN WHEN THE PRIOR-LOCAL RECORD IS UNREACHABLE — INSIDE THE GUARD WRITTEN TO PREVENT EXACTLY THAT DAMAGE.** `prior_local = _npe_citywide_for(city.code, year)` (`:4808`) returns `{}` for **four causes the caller cannot tell apart** (`:3579-3607`): no `CALENDAR[year].results` template; the file absent at either candidate path; `levels.HELD_BACK`; and `total == 0`. **Only the last means "read it, and the mass really is zero".** Verified 2026-09-14 by reaching each branch deliberately — all four return `{}`, one distinct value across four causes; the control `_npe_citywide_for('JHB','2021')` returns 54 parties summing to 1.000000. The ceiling then scores `dropped_mass = sum((prior_local or {}).get(p, 0.0) for p in deliberate)` (`:4962`), which is **0.0 for an unreachable record**, so `dropped_mass > ROSTER_DROP_CEILING` is false and the refusal never fires. The guard's own comment two lines above says *"A count is not a check … the number that matters is the MASS"* — and the mass is precisely what fails open. **Reproduced without stubbing the guarded function:** joburg 2026, a half-typed nomination list (the top six of 2021) marked `complete = true`, with `CALENDAR['2021'].results` redirected to a filename not in the checkout so the real `path.exists()` branch runs — `data/**` is gitignored, so "not in this checkout" is a realistic state. Record reachable → **REFUSED**, "would delete 48 parties holding 7.77% of the 2021 vote, above the 1.5% ceiling"; record unreachable → **ADMITTED**, printing *"48 parties holding 0.00% of the 2021 vote are dropped"*; injection reverted → **REFUSED** again, identically. **The true mass silently deleted is 7.77% across 48 parties, above five times the ceiling**, and §1.175 measured a wrongly-fired drop at 2.4-2.9% while noting ~0.4% is a seat under largest remainder. ⚠️ **The same `{}` disables a SECOND consumer in the opposite direction.** `_local_thin` (`:4819`) is the §K2 floor; with `prior_local` empty it is empty too, and the incomplete-roster union re-admits everything it had excluded — measured on the same constructed inputs, the roster goes **35 → 62 parties, 27 re-admitted holding 1.09% of the 2021 vote**, each individually below `PRIOR_LOCAL_FLOOR`. (That figure is from constructed `composition`/`baseline` inputs, not from an emitted spec; the direction and the mechanism are the claim, not the magnitude.) ⭐ **This is the repository's own empty-record-vs-unreachable-record class, one layer below `tests/test_roster_fails_closed.py`** — that file separates published / not-yet-held / unreadable for `contesting_parties`, the roster path, and **nothing does the same for `_npe_citywide_for`, the mass path the deletion is actually weighed on**. **The fix:** give `_npe_citywide_for` a state alongside the shares — `None`, or a typed result mirroring `montecarlo.roster_for_target`'s three-state shape — distinguishing *read* and *read-and-genuinely-empty* from *no template / absent / held back*; then make **both** the `complete` deletion and the §K2 floor **refuse** on unreachable rather than score zero. Note `_citywide_for` (`:2341`) already tallies `metro` / `fallback` / `unavailable` into `_TRANSITION_LEDGER`, so the distinction is already recognised as load-bearing — it just never reaches a caller; and `resolve_roster` calls `_npe_citywide_for` **directly**, bypassing even that tally. | ⛔ **Moves `pools_sha` — it is executable code in `_code_sha`'s AST — and is expected to be NUMBER-NEUTRAL and EMIT-NEUTRAL on this tree.** Verified 2026-09-14 across **all 26 targets the window's loop issues** (8 cities × 2011/2016/2021, plus joburg and tshwane 2026): every one reads a real record — smallest 8 parties (buffalocity 2016), largest 54 (joburg 2026), every mass 1.000000. **So no target currently takes the unreachable path and the new refusal blocks nothing.** ⛔ **That is a prediction, not the test.** The acceptance test is the window's own: emit, and diff every spec — anything that moves means the state was threaded wrong at one of the call sites. A second acceptance condition, and the one that matters: the guard specified below must FIRE on the constructed unreachable record and GO QUIET when it is reverted, which is how this defect was found and is the only evidence the repair works. | §1.238, 2026-09-14 |
| 22 | ⛔ **LANDED 2026-09-14, §1.238, in the SURVIVABLE form the row required.** `PoolCountsUnsafe` (not a `SystemExit`) carries the three census refusals; `ElectionUnavailable(SystemExit)` carries `not_on_disk`/`held_back`; one helper serves all three callers, files the loss under `POOL_LOSS_CAUSES` and does NOT catch `Exception`, so a real `TypeError` propagates. `_reprojection_drift` gained a `DRIFT_UNMEASURABLE` sentinel and `pool_counts` refuses on it. ⚠️ **TWO CORRECTIONS TO THIS ROW.** (a) The census loss is not joburg/tshwane/capetown — it is **2004 and 2019 in ALL EIGHT cities**, plus joburg 1999; the other seven are refused earlier at 1999/2000 by `levels.HELD_BACK`. (b) The row recorded only a failure to CONSTRUCT a case where the `:1539` `None` admits a join the 50% guard then passes; a panel scan over all eight cities × every calendar year settles it — **no city-year is admitted on an uncomputable drift**, so the new refusal is number-neutral and only renames the cause. Guarded by `tests/test_census_refusal_is_not_swallowed.py` (6 tests), mutation-tested twice. ⛔ **LANDED 2026-09-14, §1.238, in the SURVIVABLE form the row required.** `PoolCountsUnsafe` (not a `SystemExit`) carries the three census refusals; `ElectionUnavailable(SystemExit)` carries `not_on_disk`/`held_back`; one helper serves all three callers, files the loss under `POOL_LOSS_CAUSES` and does NOT catch `Exception`, so a real `TypeError` propagates. `_reprojection_drift` gained a `DRIFT_UNMEASURABLE` sentinel and `pool_counts` refuses on it. ⚠️ **TWO CORRECTIONS TO THIS ROW.** (a) The census loss is not joburg/tshwane/capetown — it is **2004 and 2019 in ALL EIGHT cities**, plus joburg 1999; the other seven are refused earlier at 1999/2000 by `levels.HELD_BACK`. (b) The row recorded only a failure to CONSTRUCT a case where the `:1539` `None` admits a join the 50% guard then passes; a panel scan over all eight cities × every calendar year settles it — **no city-year is admitted on an uncomputable drift**, so the new refusal is number-neutral and only renames the cause. Guarded by `tests/test_census_refusal_is_not_swallowed.py` (6 tests), mutation-tested twice. ⛔ **LANDED 2026-09-14, §1.238, in the SURVIVABLE form the row required.** `PoolCountsUnsafe` (not a `SystemExit`) carries the three census refusals; `ElectionUnavailable(SystemExit)` carries `not_on_disk`/`held_back`; one helper serves all three callers, files the loss under `POOL_LOSS_CAUSES` and does NOT catch `Exception`, so a real `TypeError` propagates. `_reprojection_drift` gained a `DRIFT_UNMEASURABLE` sentinel and `pool_counts` refuses on it. ⚠️ **TWO CORRECTIONS TO THIS ROW.** (a) The census loss is not joburg/tshwane/capetown — it is **2004 and 2019 in ALL EIGHT cities**, plus joburg 1999; the other seven are refused earlier at 1999/2000 by `levels.HELD_BACK`. (b) The row recorded only a failure to CONSTRUCT a case where the `:1539` `None` admits a join the 50% guard then passes; a panel scan over all eight cities × every calendar year settles it — **no city-year is admitted on an uncomputable drift**, so the new refusal is number-neutral and only renames the cause. Guarded by `tests/test_census_refusal_is_not_swallowed.py` (6 tests), mutation-tested twice. ⛔ **THREE CENSUS REFUSALS ARE SWALLOWED BY CALLERS THAT CATCH `SystemExit`, SO A REFUSAL WRITTEN TO *STOP* A WRONG JOIN INSTEAD *DELETES* THAT CITY-YEAR WITH NO OUTPUT.** The refusals are `pools.py:1085` (census drift ceiling), `:1108` (fewer than 50% of election wards matched) and `:1117` ("no ward joined the census"). Every historical caller of `pool_counts` already catches them: `:1279` `except SystemExit: continue  # that election is not on disk for this city`; `:2399` a bare `except SystemExit: continue`; `:2593` `except (Exception, SystemExit): continue`, which also swallows a genuine `TypeError`/`KeyError`. The diff's own comment at `:1024` names the mechanism — *"Nobody saw it because `turnout_record` swallows the refusal"* — and then adds two more refusals into it. **The `:1279` comment is false on this tree, verified 2026-09-14**: `registration_series` silently drops joburg **1999, 2004, 2019**, and tshwane and capetown **1999, 2000, 2004, 2019** — **every one of those result files is on disk**. The real causes are the census join (0 of 1 / 110 / 136 wards for joburg) and `levels.HELD_BACK`, neither of which is "not on disk". Johannesburg's `registration_series` therefore returns **eight** cycles while the function's own docstring promises *"ten cycles … (2000 through 2024)"*. The input defect underneath is `DATA-QUALITY.md` item 18. ⭐ **FAULT INJECTION, both directions, is what proves the swallow rather than the symptom:** lowering `CENSUS_DRIFT_CEILING` 0.05 → 0.003 makes joburg **2000** genuinely trip the drift refusal at `:1085`; `turnout_record(kind="LGE")` goes `['2000','2006','2011','2016','2021']` → `['2006','2011','2016','2021']` and `registration_series` loses 2000 too — **no refusal reaches the caller, nothing is printed, and the record is simply one year shorter.** Reverting the ceiling restores both exactly. **The consequence, measured on the same injection:** `turnout_band` **narrows by up to 23.1%** (pool 2: width 0.7511 → 0.5777; pool 1 −10.0%; pool 0 −7.4%; pool 3 unmoved), with the **centre unmoved**. ⚠️ **That corrects the shape of the harm as it was briefed to me.** `turnout_band` centres on `arr[-1]` (`:2471`), so a dropped year re-centres the forecast **only if it is the most recent LGE**; drop any earlier one and what moves is the **spread**. ⭐ **BOTH HALVES ARE NOW MEASURED, AND THEY RECONCILE.** A blind reviewer independently confirmed the swallow is firing and forced a **Tshwane 2016** refusal — the most recent LGE in that record — measuring a turnout centre moving by **-0.4919 (63.3% -> 14.1%) with zero output**. My injection dropped joburg **2000**, the earliest, and narrowed the band by 23.1% with the centre unmoved. **Same defect, two magnitudes, selected by WHICH year trips**: the trapdoor (a re-centred forecast, catastrophic, needs the latest LGE to trip) and the live effect (a silently sharpened band, subtle, any other year). ⛔ **Neither number bounds the other and the entry must carry both** — quoting only the 23.1% understates the worst case by two orders of magnitude, and quoting only the -0.4919 makes it look like a rare corner rather than something already happening. A silently narrowed band is the worse failure of the two — it is an overconfident forecast with no trace, and calibration damage is not visible in a point score. ⚠️ **Related, same function, and NOT reproducible as a fail-open:** `_reprojection_drift` returns `None` at **both** `:1511` ("nothing is lost", safe) and `:1539` ("the census mixes came out empty, nothing could be measured"), and `:1084` treats both as safe; `CENSUS_COVERAGE_FLOOR` was demoted to a `print` at `:1092`, so the quantitative backstop is gone. When drift is uncomputable `:1096` prints *"admitted because the loss is demographically even (shift nan)"* — **stating a conclusion the code never reached, and it is also wrong about its own outcome**: on every case observed (joburg 1999/2004/2019, tshwane/capetown 2004/2019) the run is **refused two lines later** by the 50% guard, so nothing is admitted. ⛔ **I could not construct a case where the `:1539` `None` admits a join the 50% guard then passes**, and that failure to reproduce is recorded deliberately: on this tree the message is a lie, not a hole. **The fix:** give `pool_counts` a distinguishable refusal — a `PoolCountsUnsafe` exception, or a `strict=` flag — so *"not on disk"* and *"on disk and the join is unsafe"* cannot be caught by one `except`; narrow `:2593`'s `except (Exception, SystemExit)` to the absence case so a `TypeError` propagates; return a sentinel from `_reprojection_drift` for *could not compute* and **refuse** on it rather than admitting; and correct `:1096` to say what was actually measured. | ⛔ **Moves `pools_sha`, and unlike entry 21 this one is NOT certain to be number-neutral — it is the one to pre-register.** Nothing on this tree currently trips `:1085`, so the drift refusal itself changes nothing; but `:1108` fires **today** on joburg 1999/2004/2019 and on tshwane/capetown 2004/2019, and the whole point of the change is that those stop being silent. **Two outcomes are possible and they must be told apart before the window:** if the distinguishable refusal is made *fatal*, the emit **stops** on those city-years and the window cannot complete; if it is made *loud but survivable* (the intended reading — these are historical record reads, not the target's own), every emitted number is unchanged and the only difference is that the run says which years it lost and why. ⛔ **DECIDE WHICH BEFORE LANDING IT**, and land the survivable version: making a historical gap fatal would block eight cities from emitting on a defect that has been present all along, which is a bigger change than the one being fixed. Acceptance test: emit and diff every spec — **every value identical, `pools_sha` moved, and the run's output now naming 1999/2004/2019 as census-join failures instead of dropping them under a comment that says they are not on disk.** | §1.238, 2026-09-14 |
| 23 | ⛔ **LANDED 2026-09-14, §1.238.** The denominator is `len(set(vd_map(city, target.year)[0].values()))` — 135 at both 2021 and 2026. Wards named outside the city's set are REPORTED, not refused: the identifier spaces may legitimately differ (`79800001` against `1`) and a guard that fires on the correct input on the one night it runs is worse than no guard. That is an addition beyond this row and is flagged as one. All three of guard C's constructed cases pass and the denominator mutated back to the paste turns 2 tests red. **The 16 September decision this row demanded is now moot for correctness** — the derivation is right either way — but a `[roster.wards]` paste still needs a ward map for the target year or it refuses with an actionable message. ⛔ **LANDED 2026-09-14, §1.238.** The denominator is `len(set(vd_map(city, target.year)[0].values()))` — 135 at both 2021 and 2026. Wards named outside the city's set are REPORTED, not refused: the identifier spaces may legitimately differ (`79800001` against `1`) and a guard that fires on the correct input on the one night it runs is worse than no guard. That is an addition beyond this row and is flagged as one. All three of guard C's constructed cases pass and the denominator mutated back to the paste turns 2 tests red. **The 16 September decision this row demanded is now moot for correctness** — the derivation is right either way — but a `[roster.wards]` paste still needs a ward map for the target year or it refuses with an actionable message. ⛔ **LANDED 2026-09-14, §1.238.** The denominator is `len(set(vd_map(city, target.year)[0].values()))` — 135 at both 2021 and 2026. Wards named outside the city's set are REPORTED, not refused: the identifier spaces may legitimately differ (`79800001` against `1`) and a guard that fires on the correct input on the one night it runs is worse than no guard. That is an addition beyond this row and is flagged as one. All three of guard C's constructed cases pass and the denominator mutated back to the paste turns 2 tests red. **The 16 September decision this row demanded is now moot for correctness** — the derivation is right either way — but a `[roster.wards]` paste still needs a ward map for the target year or it refuses with an actionable message. ⛔ **`declared_roster` DERIVES REACH AGAINST THE DECLARED PARTIES, NOT THE CITY — AND THE COMMENT ABOVE IT CLAIMS THE OPPOSITE.** `:4594-4598` builds `seen = {w for ws in wards.values() for w in ws}` — the union over **only the parties typed in so far** — and returns `len(set(ws)) / len(seen)`. `_ward_reach` (`:3359`) builds `seen` from **every row of the whole ward ballot** and returns `len(w)/len(seen)`. The comment claims they are *"derived the same way … so the two definitions of 'reach' cannot drift"*; **they already have.** Verified 2026-09-14 by running the real `declared_roster` body on a constructed `[roster.wards]` block (only the file read patched): one entrant declared on **20 of Johannesburg's 135 wards** (denominator from `vd_map(city,'2021')`) gets reach **1.0** against a true **0.1481** — **6.75x**. The bucket flip is confirmed, not inferred: `abs(r - 1.0) < 0.25` is **True** at 1.0 and **False** at 0.1481, so `comparators(reach)` (`:4174`) sizes it against full-reach city-wide peers, and `arrival_group_spec`'s split weights (`:3835`) give it the maximum. ⭐ **AND IT IS WORSE THAN A WRONG DENOMINATOR: REACH IS NOT A PROPERTY OF THE PARTY AT ALL.** Same party, same 20 wards, but a second party declared on the other 115 → its reach falls **1.0 → 0.1481** with nothing about its own declaration changed. **The value is a function of how far through the paste the typist has got**, so the error is *maximal at the first party entered* and shrinks monotonically as the list grows — the opposite of the direction anyone would check. ⭐ **AND IT IS INDISTINGUISHABLE FROM A CORRECT VALUE:** `_ward_reach('JHB','2021')` returns exactly **1.0 for 15 of its 55 parties**, so a reach of 1.0 on a 20-ward party looks like every genuinely city-wide party in the record. Nothing is anomalous on inspection. ⚠️ **SCOPE, WHICH BOUNDS THE URGENCY AND THE BRIEF DID NOT STATE IT.** The derivation is guarded by `if wards:` and by `setdefault`, so it fires **only when a `[roster.wards]` block is pasted** and an explicit `[roster.reach]` still wins. A `parties`-only paste — the commoner shape — cannot reach this code at all. **So the answer to "must it precede the nomination paste" is conditional: YES if the 16 September paste will carry per-ward nominations, NO if it will carry `parties` alone.** That is the owner's decision and it should be made before the day, not on it. **The fix:** divide by the city's own ward count (`len(set(vd_map(city, target.year)[0].values()))`), which is what `_ward_reach` means by `seen`; or derive reach only under `complete = true`, where the declared set *is* the city. ⛔ **Do not "fix" it by deleting the derivation** — that restores the `reach = None` defect the comment above it was written to close. | ⛔ **Moves `pools_sha`.** ⚖️ **Number-neutral on every spec on disk, because no judgement file in the tree carries a `[roster.wards]` block** — the derivation is unreachable today, which is exactly why it has survived. **Verify that rather than assume it:** grep the judgement files for `[roster.wards]` before landing, and the window's emit-and-diff is the acceptance test as usual. ⛔ **Its real acceptance test is not the emit at all** — it is a constructed partial declaration whose reach matches `_ward_reach`'s definition on the same wards, and a second-party case proving the first party's reach does not move. This is the one entry in the batch whose value is entirely in the future, on one night, under time pressure. | §1.238, 2026-09-14 |
| 24 | ⛔ **LANDED 2026-09-14, §1.238.** The directory scan was KEPT, as the row insisted; the digest now covers the named file AND the directory listing, so the argument is live and a sibling edit still moves it. A named file not on disk refuses; the zero-file case refuses through `_toml_population`, one definition shared with `_cities_sha`, replacing two different silent sentinels. `stale_reason`'s label moved with the population. Guarded by `tests/test_artefact_key_discriminates.py`; the argument made inert again turns 3 tests red. ⛔ **LANDED 2026-09-14, §1.238.** The directory scan was KEPT, as the row insisted; the digest now covers the named file AND the directory listing, so the argument is live and a sibling edit still moves it. A named file not on disk refuses; the zero-file case refuses through `_toml_population`, one definition shared with `_cities_sha`, replacing two different silent sentinels. `stale_reason`'s label moved with the population. Guarded by `tests/test_artefact_key_discriminates.py`; the argument made inert again turns 3 tests red. ⛔ **LANDED 2026-09-14, §1.238.** The directory scan was KEPT, as the row insisted; the digest now covers the named file AND the directory listing, so the argument is live and a sibling edit still moves it. A named file not on disk refuses; the zero-file case refuses through `_toml_population`, one definition shared with `_cities_sha`, replacing two different silent sentinels. `stale_reason`'s label moved with the population. Guarded by `tests/test_artefact_key_discriminates.py`; the argument made inert again turns 3 tests red. **`_config_sha`'s PARAMETER SELECTS A DIRECTORY, SO TWO DIFFERENT CONFIG FILES HASH IDENTICALLY.** `:389-396` takes `Path(config_path).parent` and globs `*.toml`. Verified 2026-09-14 on a constructed directory holding `alpha.toml` and `beta.toml`: `_config_sha(alpha.toml)`, `_config_sha(beta.toml)` **and `_config_sha(does_not_exist.toml)` all return the same hash** — the parameter is inert, and a path that is not on disk is not noticed. So `artefact_key(..., config_path=X)` cannot tell two configs apart: a silent-staleness hole inside the field added to close one. ⚠️ **TWO CORRECTIONS TO HOW THIS WAS BRIEFED TO ME, AND BOTH CHANGE THE FIX.** **(1) The directory glob is DELIBERATE and must not be reverted.** The docstring is explicit — it replaced a single named path precisely because that was *"a population bug, not a missing file"*, and editing any file in the directory does move the hash (verified: editing `beta.toml` moves `_config_sha(alpha.toml)`). The defect is not that it scans the directory; it is that **the signature says `config_path: Path` while the population is a directory**, so the argument documents a promise the function does not keep. **(2) The empty-directory case does NOT raise `FileNotFoundError`.** `_sha` (`:201-206`) catches `OSError` and returns the literal string **`"missing"`**, so `_config_sha` returns `"missing"` where `_cities_sha` (`:348`) returns `sha256("")[:16]` = `e3b0c44298fc1c14` — both verified. The asymmetry the brief describes is real and its two arms are **two different silent sentinels**, not an exception against a hash. Worse in one way than briefed: `"missing"` is a **fixed string in a hash field**, so with `config/` emptied every spec agrees with every other and staleness becomes undetectable rather than loud. ⚠️ **The label at `:486` is the one honest thing here** — `f"{Path(config_path).parent}/*.toml"` correctly describes what was scanned. **Do not "fix the message"**; it is the signature that lies. **The fix:** make the population explicit — take the directory as the argument (`config_dir`), or keep the file argument and hash *both* the named file and the directory listing so the two claims are separable; and give the zero-file case one stated sentinel shared with `_cities_sha`, which by `CLAUDE.md` §4 should be a refusal rather than either silent value. | ⛔ **Moves `pools_sha`.** ⚖️ **Number-neutral in intent — it changes a provenance field, not a computed value** — but ⛔ **it MOVES `config_sha` ITSELF if the sentinel or the hashed population changes**, which marks every spec stale for a reason that is correct rather than cry-wolf. **Take it in the same window as the emit**, never after: landing it a day later costs a whole window for a field nobody would think to re-check. Acceptance test: emit and diff — every computed value identical, `config_sha` and `pools_sha` moved, and a constructed two-file directory giving two different hashes. | §1.238, 2026-09-14 |
| 25 | ⛔ **LANDED 2026-09-14, §1.238.** The `THETA_WINDOW` entry is deleted from `_gates_sha`'s dict and `HELD_BACK_OFF`/`HELD_BACK_n` stay. Verified in three subprocesses: unset and `THETA_WINDOW=2` give an identical key, `HELD_BACK_OFF=1` moves `gates_sha` and nothing else. Both directions are asserted and the gate put back turns 2 tests red. The guard also scans the AST for the set of `levels` attributes `pools` touches and requires it to stay `{_held_back}`, which turns the static argument into a tripwire. ⛔ **LANDED 2026-09-14, §1.238.** The `THETA_WINDOW` entry is deleted from `_gates_sha`'s dict and `HELD_BACK_OFF`/`HELD_BACK_n` stay. Verified in three subprocesses: unset and `THETA_WINDOW=2` give an identical key, `HELD_BACK_OFF=1` moves `gates_sha` and nothing else. Both directions are asserted and the gate put back turns 2 tests red. The guard also scans the AST for the set of `levels` attributes `pools` touches and requires it to stay `{_held_back}`, which turns the static argument into a tripwire. ⛔ **LANDED 2026-09-14, §1.238.** The `THETA_WINDOW` entry is deleted from `_gates_sha`'s dict and `HELD_BACK_OFF`/`HELD_BACK_n` stay. Verified in three subprocesses: unset and `THETA_WINDOW=2` give an identical key, `HELD_BACK_OFF=1` moves `gates_sha` and nothing else. Both directions are asserted and the gate put back turns 2 tests red. The guard also scans the AST for the set of `levels` attributes `pools` touches and requires it to stay `{_held_back}`, which turns the static argument into a tripwire. **`THETA_WINDOW` MOVES THE ARTEFACT KEY AND CHANGES NOTHING EMITTED — A CRY-WOLF HOLE IN THE ONE FIELD THAT MUST NOT CRY WOLF.** It sits in `_gates_sha` (`:311`) beside `HELD_BACK_OFF` and `HELD_BACK_n`. **`pools.py` reads it nowhere else** — one line, verified — and `pools`'s *only* use of the `levels` module is `_levels._held_back` at `:937` and `:3598`, so the gate cannot reach an emitted number through the import either. Its real consumers are `levels.py:604/681` (trimming the θ record), `theta_residual.py`, `freeze.py` and `montecarlo.py`. **Verified end to end 2026-09-14, read-only, emitting nothing:** with `THETA_WINDOW` unset, `stale_reason` reports **every spec on disk clean** (count from step 3's `find`); with `THETA_WINDOW=2` it reports **every one of them stale**, naming `gates_sha`; unset again, every one clean. `artefact_key` confirms the isolation — `gates_sha` is the **only** field that moves. ⭐ **THIS BLOCKS A PLANNED EXPERIMENT, AND THAT IS THE REASON TO TAKE IT.** `prereg/2026-09-13-held-back-quarantine-asymmetry.md` names `HELD_BACK_OFF=1 THETA_WINDOW=2` as the partial separation of the θ half of the damage from ρ. ⚠️ **Stated precisely: the prereg raises it in its "what this arm cannot do" section, conditional on P3 landing high — a contemplated next arm, not a scheduled one.** Run it today and every spec prints STALE and a non-null `stale_reason` is stamped into `02_pools_artefact` **on a tree where nothing is stale** — the exact cry-wolf failure the comment at `:320-336` gives as the reason `montecarlo` is excluded from `_deps_sha`. ⛔ **`HELD_BACK_OFF` and `HELD_BACK_n` MUST STAY.** `HELD_BACK_OFF=1` genuinely changes what `_npe_citywide_for` reads (the prereg says so and `:3598` is the line), so for those two the staleness is true and wanted. The fix is surgical: **delete the `THETA_WINDOW` entry from `_gates_sha`'s dict**, or move it to a provenance field that is recorded and not compared. | ⛔ **Moves `pools_sha` AND `gates_sha`** — removing a key from the hashed dict changes the digest for every spec, so this necessarily marks them all stale once, which the pending emit absorbs. **That is the whole argument for taking it in THIS window**: after the emit it costs a window of its own, and before the θ/ρ arm it is the difference between an experiment that can be read and one that stamps a false staleness into its own trace. ⚖️ **Number-neutral by construction** — the value is not read by any emit-path computation, which is the finding itself. Acceptance test: emit and diff (every value identical, key moved), then set `THETA_WINDOW=2` and confirm `stale_reason` returns `None` for every spec while `HELD_BACK_OFF=1` still returns a reason for every spec. **Both directions, or the repair has only been half made.** | §1.238, 2026-09-14 |
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
