# The scoreboard as it stood before the canonical run (archived 2026-09-13)

**Kept because it is the only record of what every claim made before
2026-09-13 was computed on.** Do not quote it; do not delete it.

⛔ **This pair is incoherent three ways over, which is why it was retired.**

| file | git last touched it | its own manifest says |
|---|---|---|
| `history.json` | `1d9a0e1` | commit `efa06f78`, **`git_dirty: true`** |
| `history.md` | `60b3341` | names no commit at all |

Three provenances for two files that read as one artefact, one of them a dirty
tree. `DATA-QUALITY.md` §16 records the divergence. Every citation of "the
committed 24-row artefact" before this date is ambiguous between them.

It is also **schema 1**: no `uniform-swing+roster` opponent, no `contaminated`
or `constants_read` (so it cannot declare its own in-sample status), no `guards`
block (`guards: null` on all 24 records, so any "measured zero" read from it is
unmeasured), and its `prior-lge-noise` `seat_abs_err_coherent` field holds the
**non-coherent** statistic — 1274, which schema 3 keeps under the honest name
`seat_abs_err` while the real coherent allocation reads 1361. Verified identical
on 24/24 rows: that change is a metric redefinition, not a behaviour change.

Superseded by the canonical run at commit `d08d705` — 24 rows, 1000 draws,
seed 20261104, `git_dirty: false`, schema 3. MODEL-LOG §1.231.
