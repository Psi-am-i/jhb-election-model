# Ultra review 1 — the `pools.py` re-emit batch

**DRAFT of 2026-08-31, reviewed. Not yet run.**

⛔ **FREEZE THIS DOCUMENT BEFORE A LINE OF THE BATCH IS WRITTEN, AND DO NOT AMEND
IT ONCE THE CODE EXISTS.** If the hunt list below is visible while the `pools.py`
changes are being written, the code gets written to pass it and the review
inherits a blind spot shaped exactly like this brief. Anything to add must be
added now.

## When to run it

⛔ **BEFORE the emit, never after.** Once `pools_*.json` is re-emitted the
baseline has moved and there is nothing clean to compare against.

    write the changes → archive the 18 current specs → THIS REVIEW
      → fix what it finds → one-writer window, emit → re-take compare_history
      → re-take the freeze

    /code-review ultra

**It needs a diff, so the changes must be written first and left un-emitted.**
Give the reviewer the eighteen archived pre-emit specs alongside the diff — a
diff of `pools.py` without the artefacts it produces is half the evidence.

**Severability, decided now rather than on 14 September.** Only **entry 3** has a
hard date: nomination lists are published **16 September 2026**. Entries 1, 2, 4,
5 and 6 have none. If a finding triaged "fix before emit" would run past that
date, the batch is severable at entry 3 — at the cost of a second window and a
second baseline. Take that decision deliberately; do not discover it under time
pressure.

## Why this one

It is the only change on the calendar where a defect would be expensive **and**
this project's normal safety nets do not reach: it moves forecast numbers,
`forecast_frozen.json` is barred from arbitrating, the backtest cannot tell a
fixed bug from a new one, and **the specs are not tracked by git** (verified —
`git ls-files` returns nothing for `pools_*.json`), so the `artefact_key` is the
only record that anything changed.

## What is being changed

Six entries in `POOLS-REEMIT-QUEUE.md`. Read it first; it carries the evidence.

**Entry 4 — the largest.** `pools.metro_file` resolves only `_metros/…` and
`_reports/…`, i.e. 2011/2016/2021, while the archive holds eight reconciled
`lge2006_{CODE}_vd_party_clean.csv` (and `lge2000_JHB`) that `levels._citywide`
reads every run. So `metro_file('JHB','2006')` is `None`, `entrant_record` is
`[]`, `arrival_rules` early-exits, and **all eight 2016 specs carry zero seeds and
`arrival_group: null`** (verified on all eight). Second step: reconcile the
arrival definitions — **see hunt 2, which is narrower than it sounds.**

**Entry 3 — the roster/reach seam, and the only entry with a deadline.**
`contesting_parties` and `_ward_reach` both read the target's own result file,
which for 2026 does not exist. **Both 2026 specs are in the same empty state as
2016** (`arrival_group: null`, `seeds=0`) — so this entry takes the *live
published forecast's* arrival machinery from nothing to live, on a mechanism
validated on one cycle today and two after entry 4. It exists so the nomination
list is a config edit on the day rather than a code change during the fortnight
the 2026 forecast most needs to be runnable.

**Entry 5 — a table transcription, and it has the batch's worst failure mode.**
See hunt 3.

**Entries 1, 2 and 6** — a `Path` frozen as a function default in three
signatures, `_target_roll` reading the crosswalk from the wrong config, and
`gate_parties` duplicating `config/dimensions.toml`. All claimed number-neutral.

**Scope the blast radius correctly.** `arrival_group_draw` defaults to `False`
(`montecarlo.py:307`), so a spec's `arrival_group` block is not consumed unless
that lever is on — while `seeds`, `entrant_record`, the splinter records and the
pool ratios are consumed always. "Changes every fitted quantity" is true of the
*file* and misleading about the *model*.

## What to hunt

**1. The 2000/2006 reader — two readers of one file.** New parsing against files
nobody has read through this path. `DATA-QUALITY.md` records four IEC CSV quirks
that corrupt data **silently rather than erroring**; check the new reader against
every one. Does it agree with `levels._citywide`, which already reads these
files from a different directory? **Two readers of one file that disagree is this
repository's signature defect**, the owner's standing rule is one definition
only, and `levels.py:591` records that this exact defect already bit once.

**2. The arrival reconciliation — and there are TWO differences, only one of
which is in scope.**

| | baseline tested against | population selected from |
|---|---|---|
| `entrant_actual_for` (the relabel) | `run.index`, the model's universe | seat winners |
| `arrival_group_score` (the referee) | `_npe_baseline`, preceding NPE citywide | the whole PR ballot |

⛔ **The population difference is NOT a discrepancy to reconcile — it is a fix
made on 2026-08-29.** Reading `actual_seats` filtered arrivals to `s > 0`,
understating realised mass in all 16 city-years and by *exactly zero* in four of
them. **Do not let this review recommend reverting it.** Only the **baseline**
difference is in scope.

The concrete case: at joburg 2021 the disagreement is about **ActionSA, which
holds 44 of the 46 arrival seats.** Pool-seeding puts ASA into `run.index`, which
makes it permanently ineligible to be `entrant_actual`, while it remains an
arrival to `arrival_group_score`. One party and one mechanism — not 32 parties.

**3. Entry 5's transcription, row by row.** `pools.SPLITS` is read by
`classify_arrival` to decide whether a party absent from the baseline is sized
**as a fraction of a named parent** or **at the typical entrant's result** — two
different machineries selected by a dict literal. `pools.py`'s own docstring
records what a wrong classification costs: **0.1% against an actual 18.12% for
ActionSA, a 180× error, with no symptom.** A dropped row, a flipped `home` or a
mistyped `parent` produces exactly that. **No test in the suite can arbitrate
it**: `test_chain.py` and `test_blended_centres.py` pin the hardcoding as the
contract and move in the same commit. Verify the new config row-for-row against
the deleted `SPLITS` and `TYPE_A_EVENTS`, and confirm `classify_arrival`'s
precedence (city judgement → splits → entrant) is unchanged.

**4. Entry 4 changes what "replicates in both cycles" MEANS.** Every
cycle-replication result in this repository was measured with the **2016 arrival
arm dead**, and Key 1's pass condition *is* replication across cycles. Nothing
will error; the numbers quietly start meaning something else. Identify anything
that changes the **character** of the 2016 arm rather than its values, and list
every measured claim that must be re-read afterwards. §1.70 is the precedent:
the panel doubled and nine-city-year figures stayed in circulation for weeks.

**5. What supplies 2016's arrival mass today, and does it stack?** With
`seeds=0` everywhere, the model still forecasts arrival mass at 2016 — and it is
a near-constant 1.28–1.56% across all eight metros against a realised
0.31–4.74%. That is a fallback, not a fit. **After entry 4 seeds the 2016 specs,
does the fallback switch off or stack on top?** If it stacks, 2016 arrival mass
roughly doubles and nothing errors.

**6. The `artefact_key`.** It is the only thing standing between a stale spec and
a believed result. Does it still change when it should?

**7. Determinism of emission.** Re-emitting an unchanged spec must change nothing
but the key. If emission is order- or dict-iteration-dependent this batch is
where it surfaces: `PYTHONHASHSEED` is pinned only from a `__main__` guard, so
any importing caller is unpinned (§1.145).

**8. This repository's four recurring defects — hunt them by name.**
* **A guard that reads as working and cannot fire.** Six found in the last week.
  For every new check, construct the failure state.
* **A test whose name states a property it does not assert.**
* **A fixture of the wrong TYPE** — the right function on data production never
  builds. `arrival_group_score` raised on every city-year for its entire life
  while its one test passed a dense 2-D fixture.
* **A number typed in two places.** One will go stale.

**9. What breaks at 2026 specifically.** Fifteen specs are backtest targets and
one is the live forecast. A change that improves the backtest and breaks the 2026
path would pass every test in the suite.

## What NOT to spend it on

Documentation wording, the queue document itself, and anything the 16-city-year
backtest adjudicates in three minutes. Also **not** whether the `artefact_key`
stays put on a comment-only edit — that is verified twice and recorded as settled.

## What "done" looks like

Every finding triaged into **fix before the emit**, **fix after**, or **rejected
with a reason**. Nothing deferred silently. The emit does not happen until the
first list is empty — subject to the severability decision above.
