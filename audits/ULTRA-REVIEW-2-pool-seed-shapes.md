# Ultra review 2 — the pool-seed shape batch

**DRAFT of 2026-09-21. Not yet run.**

⛔ **FREEZE THIS DOCUMENT BEFORE A LINE OF THE BATCH IS WRITTEN, AND DO NOT AMEND
IT ONCE THE CODE EXISTS.** Same rule as review 1: if the hunt list is edited
while the change is being written, the code gets written to pass it and the
review inherits a blind spot shaped exactly like this brief. Anything to add
must be added now.

## When to run it

⛔ **BEFORE the emit, never after.** Once `pools_*.json` is re-emitted the
baseline has moved and there is nothing clean to compare against.

    write the change, leave it un-emitted → archive the 27 current specs
      → THIS REVIEW → fix what it finds → one-writer window, emit
      → compare_history → freeze

**Form of the command, decided 2026-09-21 with the owner.** The change goes on
its own branch, pushed, with a pull request based on `remediation`, and the
review is run as `/code-review ultra <PR#>`. The bare form bundles the whole
local branch, which is 43 commits and 298 files ahead of `main` — the reviewer
would spend itself on a fortnight of typography and claims work instead of on
the seeds.

## Why this one

It is the case the project's normal nets do not reach. It **moves forecast
numbers**; `forecast_frozen.json` is barred from arbitrating (CLAUDE.md §1); the
backtest cannot distinguish a fixed bug from a new one; and `pools_*.json` is
gitignored, so `artefact_key` is the only record that anything changed. It also
touches a rule that has already been half-fixed once — which is the specific
failure mode this project keeps hitting (`no-duplicated-logic`).

## The evidence this batch starts from

Two tests have been red for weeks. Read off the emitted specs
(`data/processed/<city>/pools_<year>.json`), they are **two causes, not four
problems**. Written up as MODEL-LOG §1.248 and §1.249.

**Cause 1 — "an even share of every pool", still live in the arrival path.**
`arrival_rules`' no-parent branch sets `vec = np.full(n_pools, 1.0 / n_pools)`
(`pools.py:4638`). `_capture_from_share` converts that to
`capture_g = share · (1/n) · electorate / pool_size_g`, and the composition loop
at `pools.py:5890` multiplies it back by `registered[g]`, which is the same
number in every pool — so the emitted composition is **exactly `1/n`**, whatever
the pools are worth. At Mangaung 2016 that gives four entrants 0.25 of their
vote from an Indian/Asian pool casting 1,176, and the guard reports AIC at
1.31x its capacity.

The identical assumption was removed from the **composition** path on
2026-08-31, and the comment left behind (`pools.py:5800`) says why in its own
words: *"THIS WAS AN EVEN SHARE OF EVERY POOL … AND THAT IS NOT A NEUTRAL
ASSUMPTION — IT IS AN IMPOSSIBLE ONE"*, measured at Buffalo City 2016 at
**228.93x**. One rule, two encodings, one fixed — and the unfixed one runs
second and overwrites the fixed one.

⚠️ The artefact already contradicts itself and nothing noticed: the
`no_measured_vector` note records *"spread as the city's own pool composition"*
for exactly the parties whose emitted weights are `0.25, 0.25, 0.25, 0.25`,
while the city's own composition is `[0.722, 0.046, 0.025, 0.207]`.

**Cause 2 — a party fitted at one size and sold at another.** Buffalo City, Cape
Town and Nelson Mandela Bay 2011 all seed **DA in White** at 0.602 / 0.536 /
0.624, and all three specs record `derived_from: pool vectors fitted on <city>
2006`. The DA of 2006 really was that concentrated; the DA of 2011 won Cape Town
outright, which no White pool can supply at any turnout. The composition carries
the party's **shape** from the earlier election and its **level** from the target
one, and the uniform rescale sends the smallest pool over capacity.

**Not in scope, and say so:** `test_the_three_known_things_hold_at_once` reports
Mangaung 2016 pool rates as `[1, 1, 0, 1]`. That pool's `rates_on_a_bound` note
says `adult_share` fitted to 1.0000, on a bound, *"a clipped corner and not a
measurement"* — an identification failure in the fit, not a seed shape. Cause 1
may or may not clear the test; **the batch does not claim it will.**

## What is being changed

Written after this brief is frozen, so the reviewer is told the intent, not the
diff:

1. **The arrival no-parent branch stops assuming an even share of every pool**
   and spreads like the city, by the same argument and for the same reason as
   the 2026-08-31 composition fix. `arrival_rules` does not receive the fit
   context, so the vector must come from something it does receive —
   `registered` — and the reviewer should check that choice, not assume it.
2. **The two encodings of "we have no information" are reduced to one**, or, if
   they cannot be, the second one is made to fail loudly rather than silently
   produce a different answer.
3. **Cause 2 is not repaired in this batch.** A fit-time capacity constraint was
   already built, measured and reverted (§1.41, coherent seat error 306 → 486),
   and capping the emitted seed changes where IPF converges. It is recorded, the
   guard keeps reporting it, and it gets its own pre-registered round.

## Hunt list

1. **Is the new spread right, or merely not-uniform?** `registered` share,
   votes-cast share and `pool_shares_at_target` are three different vectors and
   the batch picks one. Say which is correct for a party nobody has measured,
   and whether the choice is consistent with `city_mix_for`, which uses
   `pool_votes`. If the two disagree, that is the same defect again in a new
   place.
2. **Does the party's citywide size survive?** `seeds` is
   `sum(r · registered) / registered.sum()`. The change must move only the
   *shape*; if a party's seeded citywide share moves, the batch has changed two
   things while claiming one.
3. **`MAX_POOL_CAPTURE` interacts.** Capture is capped per pool. Under a
   city-shaped spread the cap binds in different places than under a flat one —
   check whether any party now silently loses mass to the cap, and where that
   mass goes.
4. **Does anything else still write `1/n`?** `pools.py` has six uniform writers
   (`4546, 4622, 4638, 5760, 5792, 5890`). Establish for each whether it means
   "no data" or something else, and whether any other one can overwrite a
   considered vector the way `5890` overwrites `5822`.
5. **Order of assignment.** `composition[party]` is written by the
   no-measured-vector branch and then overwritten in the arrivals loop. Confirm
   the final writer is the intended one for every class of party — splinter,
   entrant with a parent, entrant from nothing, fitted — and that
   `no_measured_vector`'s note still describes what was actually written.
6. **The guard's population.** `test_no_emitted_composition_weight_is_
   arithmetically_impossible` has twice scanned the wrong set (§1.42, §1.162).
   Check it now scans every emitted spec, that an unscannable spec is named
   rather than skipped, and that the batch has not narrowed the population to
   the set it fixes.
7. **Does the change reach 2026?** The published forecast is the only spec a
   reader sees. State whether Johannesburg 2026 has any entrant-from-nothing,
   and therefore whether this batch moves the live forecast or only the panel.
8. **Mutation.** Revert the one-line change and confirm the guard goes red
   again, and that the new test (if any) fails for the right reason rather than
   on a message string (`assert-the-number-not-the-message`).

## What the reviewer gets

* The PR diff, based on `remediation`.
* The 27 **pre-emit** specs, archived before the batch — a diff of `pools.py`
  without the artefacts it produces is half the evidence.
* MODEL-LOG §1.248 and §1.249, `POOLS-REEMIT-QUEUE.md`, and
  `audits/ULTRA-REVIEW-1-pools-reemit.md` for what the last one found.

## Severability

Nothing here has a deadline. The 2026 emit for Johannesburg is already done and
the site is built from it; this batch is about the **panel**, unless hunt 7 says
otherwise. If a finding would take days, the batch can wait — there is no
second baseline to protect and no date to hit.
