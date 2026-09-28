# F3 (C1 conservation, queue entry 30): the in-process proof, 2026-09-29

Written by the F3 agent in `/tmp/f3/` and copied here so the proof can be re-run
(`prereg/README.md`: a harness that is cited is committed).

* `build_spec.py`: calls `pools.emit_pools` in-process with
  `write_lineage_template` stubbed, so no spec is written.
* `run_all.sh`: builds all 26 emittable city-years under the old code (a
  `git archive` of `69cc6cc`) and the new code.
* `compare.py`: field-by-field comparison.

**Checked by the lead:**
* P1 counted with the lead's own predicate, which unwraps the harness's
  `{"ok", "spec"}` wrapper. A first version did not, read empty fields and
  passed everything; it was caught because the positive control on the live
  on-disk `mangaung/pools_2016.json` was added after it.
* **Old code:** 4 of 26 specs violate P1, exactly buffalocity 2016 and mangaung
  2011, 2016 and 2021, all Indian/Asian.
* **New code:** 0 of 26.

The cause and fix are MODEL-LOG §1.269, the fallback value is
JUDGEMENT-CALLS §L14, and the queue entry is POOLS-REEMIT-QUEUE entry 30.
