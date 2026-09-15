# QC — how a change is made here, and how it is shown to work

This is the process document: the loop a change goes round, the observation
machinery that watches the model run, and what counts as evidence that the
change works.

It is deliberately short, and it is short by one rule: **prose here only for what
lives nowhere else in a root document; a pointer everywhere else.** A rule
written twice is a rule that drifts, and the copy nobody remembers to update goes
on looking true.

⛔ **No figure is generated in this document, so no figure appears in it.** Where
you want a number — a test count, a stage count, a score — the claim beside it
names the instrument that prints it. Run that.

---

## 1. The loop

`CLAUDE.md` §4 is the authority and states it in full: design in parallel and
**read-only**, re-derive the decisive number yourself rather than reading a
summary, review blind, apply only what the check and the review agree on,
measure, write it up.

What decides whether the result ships is `ITERATING.md`: **more honest usually
ships**, and what does not ship is a change that scores worse *and* explains
nothing. The standard it is scored against is a backtest on real elections
(`CLAUDE.md` §1) — never the published forecast, never a freeze, never a golden,
never an earlier output of this model.

## 2. Pre-registration

A prediction written down before the run is what turns a result into evidence.
It is committed to `prereg/` **before** the run it predicts, one file per
question, and it is never edited afterwards: it is scored as written, including
the part it falsified. `prereg/README.md` carries the rule and the standing
outcome of each.

Predict against the world and against the mechanism. Two failure modes are on
the record and both void the exercise: predicting against a prior output of this
model, which is self-benchmarking; and naming a quantity that can be redefined
underneath the prediction, so the measurement answers a different question than
the one asked (MODEL-LOG §1.231).

## 3. Gated stage observation

**`run_model` writes each stage of a run as JSON when given `--run-dir`.** That
trace is the seam every gate hangs on, and the seam is free in both directions:

* **Observing does not perturb.** The drawn seats and both drawn share arrays
  are identical with and without a run directory —
  `test_chain.py::test_passing_a_run_directory_changes_no_drawn_number` runs the
  model twice on one seed and compares them. (It compares the draws, not the
  bytes of the run. Read its docstring before citing it for anything wider.)
* **Observing does not overwrite.** A diagnostic run neither creates nor
  rewrites a single file in the processed directory —
  `test_chain.py::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts`
  runs the real command against the real directory and compares every file's
  bytes, over the whole directory rather than a list of names. `data/**` is
  gitignored, so nothing else would notice (MODEL-LOG §1.118).

The stages, grouped by the segment that owns them:

    00_target · 01_scenario_in · 02_pools_artefact · 03_roster     inputs
    10_theta_prior · 20_spine · 30_centres                         estimation
    40_draws · 41_guards · 42_pr_share_draws
    43_ward_share_draws · 44_seat_draws · 45_delivered             realisation

Each segment has a skill that documents its stages field by field, with units,
invariants and the traps that have already caught readers out, and a test module
that is the executable form of the same:

| segment | the question it answers | skill | tests |
|---|---|---|---|
| inputs | what entered the run, and whether all of it existed before the target election | `skills/forecast-stage-inputs/` | `tests/test_stage_inputs.py` |
| estimation | how big the model thinks each party is, and where that came from | `skills/forecast-stage-estimation/` | `tests/test_stage_estimation.py` |
| realisation | how drawn shares become an allocated council | `skills/forecast-stage-realisation/` | `tests/test_stage_realisation.py` |

Which stages a segment owns is stated in its skill, and what the trace actually
emits is asserted against that claim by
`test_stage_realisation.py::test_the_realisation_segment_emits_every_stage_it_claims_to`.

### ⚠️ Every gate carries its own positive control

**The warning that governs this design: this model has already shipped a stage
observer that could not see.** `arrival_reconciliation` read the post-relabel
index, so it was silent on most of the panel while filing a whole cycle's arrival
mass as unexplained (MODEL-LOG §1.230). A trace is a **record, not a check**: it
will record a guard that has gone blind exactly as readily as a working one, and
an observer that cannot demonstrate detection is worse than none, because it
reads as coverage.

So a stage gate is a **pure predicate over one stage payload** — it runs with no
data on disk — and it ships with a **constructed** healthy payload it must pass
and a **constructed** broken one it must catch. Constructed, not copied out of a
passing run: a fixture lifted from a green tree expires silently on the day the
tree changes (`CLAUDE.md` §4, requirement 3).

⛔ **The pairing is mechanised in two of the three segments, and this is the one
place this document's own rule is a convention rather than a guard.** Inputs and
estimation declare their invariants and their violations in tables and assert
that the two sets agree **in both directions** —
`test_the_corruption_table_covers_every_declared_invariant`,
`test_every_predicate_has_a_constructed_violation` — so a predicate with no
violation, or a violation naming an invariant nobody declared, is a failure.
Realisation writes its healthy/broken pairs out test by test and nothing asserts
the set is complete: a realisation predicate added without its pair is not
caught. Until then the rule there is maintained by hand. **Done when
`tests/test_stage_realisation.py` carries a coverage assertion that fails in both
directions, as the other two do.**

⚠️ **A positive control can itself be blind, and one here was.**
`bounds_violations` counted draws rather than bound-checks, so its control could
not fail in either direction (MODEL-LOG §1.231, *Corrections to §1.230*). The
control is part of the gate and is reviewed as one.

## 4. Testing a change

Three shapes, and they fail differently.

* **Value tests** — assert the number, not the message. A test on a `why` note
  stays green while the arithmetic beside it is broken.
* **Absence-shaped scans** — a test that searches live state and asserts
  emptiness. This is the suite's largest single source of defects, and
  `CLAUDE.md` §4 states the four things one must prove: that it scanned the right
  population, that it looked, that it can see a constructed violation and goes
  quiet when that is reverted, and that its input is constructed rather than
  observed. `tests/_support.py::scanned` mechanises the second and its docstring
  explains why the bound is two-sided against a computed denominator.
* **Stage predicates** — §3.

The honest name for what all three approximate is mutation testing: change one
line, watch whether the suite stays green.

### Running them

`CLAUDE.md` §5 carries the commands. While iterating, `-k` the modules the change
reaches; before committing, the whole suite once, for the whole batch.

⚠️ **`run_all.py` prints a `passed / failed / skipped` line per module and no
grand total.** Read the module lines. A `-k`/`-x` run additionally prints
`*** PARTIAL RUN` and is not a suite run; the counts quoted anywhere must come
from the run that finished *after* the last edit. **Never pipe it through `tail`
or `head`** — the pipeline reports the pipe's exit status, so a failing suite
exits zero.

Two preconditions that are easy to skip and expensive to skip:

* **Before quoting a number out of any artefact**, `src/declares.py --verify` —
  an artefact declaring nothing is a known gap, one declaring wrongly is a gap
  wearing a badge.
* **Before measuring anything on a tree more than one worker is touching**,
  `CLAUDE.md` §3: one writer, and nobody measures while it writes. Documents
  included — do not edit a file while an audit of it runs.

## 5. Every plan item names its completion predicate

**An item in a plan, a queue or a tracker states the artefact or the test that
will exist when it is done** — not what will have been decided, and not what will
have been understood.

Without it a tracker cannot be resolved by reading it, and the failure is not
theoretical: trackers in this repository have listed already-shipped work as
outstanding, and plans exist here whose items nothing can adjudicate. **An
unticked box is not evidence**; the next session must verify in the code, which
is exactly the cost the item was supposed to remove.

A completion predicate is also the honest place to write "this cannot be
checked". An item whose predicate is *"argued, not tested"* is fine. An item with
no predicate at all is a note, not a plan.

## 6. What enforces what — and the one thing that does not

| the claim | what goes red when it stops being true |
|---|---|
| the trace changes no drawn number | `test_chain.py::test_passing_a_run_directory_changes_no_drawn_number` |
| a diagnostic run does not publish | `test_chain.py::test_a_diagnostic_run_does_not_overwrite_the_published_artefacts` |
| the trace emits the stages the segment claims | `test_stage_realisation.py::test_the_realisation_segment_emits_every_stage_it_claims_to` |
| every stage predicate can see a violation | the corruption tables in `test_stage_inputs.py` and `test_stage_estimation.py`; in `test_stage_realisation.py`, nothing — §3 |
| an absence-shaped scan actually looked | `tests/_support.py::scanned`, at each call site |
| a test module is collected at all | `test_regressions.py::test_every_test_module_is_collected` |
| `CLAUDE.md`'s entry-point block is still true of the tree | `tests/test_standalone_modules.py` |
| every tunable constant is in the register | `test_regressions.py::test_every_tunable_constant_is_in_the_judgement_register` for membership, `tests/test_register_matches_code.py` for both directions — ⚠️ membership is a bare substring test and one pair passes on an accident (MODEL-LOG §1.230) |
| an artefact declares what produced it | `src/declares.py --verify` |
| **this document is read at all** | **nothing** |

That last row is the point of the table. The pointer in `CLAUDE.md` §4 is the
only mechanism that brings this document into a session, nothing fails if it is
deleted, and a method that survives only in a session's memory is the defect this
document exists to fix.
