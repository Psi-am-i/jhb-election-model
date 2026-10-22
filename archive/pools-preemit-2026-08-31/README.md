# The eighteen specs as they stood before the re-emit window

Copied 2026-08-31 from `data/processed/**/pools_*.json`, all eighteen at
`pools_sha = dbdf171344ffd5f0`.

## Why this directory exists

**`data/**` is gitignored, so the specs have no version history — that is the
whole reason the `artefact_key` exists.** But four of the six queued entries
(1, 2, 5, 6) are claimed **number-neutral**, and the acceptance test for a
number-neutral change is *"emit before and after and diff the specs"*.

**That test is impossible to run after the fact.** Once the window is taken the
old specs are gone and there is nothing to diff against — so the claim that
entries 1, 2, 5 and 6 changed nothing would be unfalsifiable, and entry 5 in
particular is a **transcription of a party table** whose failure mode is a
dropped or mistyped row producing a 180× sizing error with no symptom.

So: archived **before** a line of the batch was written. Raised in review,
2026-08-31.

## How to use it

After the emit, for each spec:

    diff <(jq -S 'del(.artefact_key)' archive/pools-preemit-2026-08-31/<slug>_pools_<year>.json) \
         <(jq -S 'del(.artefact_key)' data/processed/<slug>/pools_<year>.json)

`artefact_key` is expected to change — it carries a hash of `pools.py`'s code,
and the batch changes that code. **Everything else must be identical for entries
1, 2, 5 and 6.** Entry 4 is expected to move numbers: it changes every fitted
quantity in every spec, and the 2016 specs in particular should go from
`seeds = 0` and `arrival_group: null` to populated.

## The before-state, for the record

| | |
|---|---|
| specs | 18 (8 metros × 2016/2021, plus joburg 2026 and 2026-simulation) |
| `pools_sha` | `dbdf171344ffd5f0`, identical across all eighteen |
| 2016 arrival state | `seeds = 0`, `arrival_group: null`, **all eight** |
| 2026 arrival state | `seeds = 0`, `arrival_group: null`, **both** |
