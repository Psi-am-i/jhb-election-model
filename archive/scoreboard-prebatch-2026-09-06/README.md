# The pre-batch scoreboard, preserved before the manifest change

`data/processed/history.json` as it stood at commit `db0789c` (mtime 2026-09-06),
i.e. **before** the 2026-09-08 pools re-emit and before the manifest envelope.

It is the artefact three blind reviewers and I re-derived §1.214's correction
from, and the only in-tree record of the pre-batch state:

    seat_abs_err_coherent = 707      [rows=24]
    seat_abs_err          = 689      [rows=24]
    crps                  = 539.41   [rows=24]
    n_scored              = 528      [rows=24]
    uniform-swing         = 885      [rows=24, coherent]

⛔ It is the OLD bare-list shape and `compare_history.load_history` REFUSES it by
design. That is not a defect: a scoreboard that cannot say what produced it is
exactly what the refusal exists to stop. Read it with `json.load` directly, and
only for historical comparison — never as a baseline to be beaten, which rule 1
bars.

⚠️ It is also MIXED VINTAGE against the tree that now exists: it describes the
pre-batch model while `data/processed/**/pools_*.json` carry the post-emit key
`843229dbe414b6b9`. That mismatch is why it is archived rather than left in
place to be read by accident.
