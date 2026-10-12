# Model correction batch: specification packet (the approved items)

One designer, read-only. Issued 2026-10-09. Writes only to
`audits/2026-10-09-model-fixes/spec/` and scratch. Do not sub-delegate.

Read:
- `CLAUDE.md` (all of it: §3 one writer and re-emit batching, §4 pre-registration
  and the guard rules, §5 running things);
- `QC.md`;
- `audits/2026-10-09-model-fixes/BRIEF.md` (items 1–6, 8, 9 and 10);
- `item9/FINDINGS.md` (its Q5 list of 15 places where the band claim is false);
- `audits/2026-10-09-model-questions/FINDINGS.md` and `integrity/FINDINGS.md`;
- `audits/2026-10-09-site-batch/law/SUMMARY.md` (D1–D10);
- `MODEL-LOG.md` §1.291–§1.294.

**Scope: approved items only.**
1. Ties settled by a seeded lot (ward calls and seat remainders).
2. Integer surpluses.
3. Unopposed wards counted twice. First check whether any 2026 Johannesburg
   ward is unopposed.
4. `test_overhang` pinned to the real Laingsburg votes.
5. Records corrected (§Q2, §M1, the D1/D2 judgement call).
6. PA contestation, vote-weighted (`PREREG-ward-list-fix.md`).
8. The seven certified parties brought into the run, plus a roster ↔ universe
   guard.
9. The band correction, per item9 Q5. No new variation source.
10. The smaller items.

**Out of scope, pending the owner:**
- item 7's level fix and the group-share guard;
- any change to the SACP or to the All Citizens Party.

Return a specification a writer cannot read two ways:
- file by file, with exact functions;
- the records to change;
- the guards, each with its population, its constructed violation and its file;
- the exact targeted test list.

Also give:
- **Whether a pools re-emit is needed** (`POOLS-REEMIT-QUEUE.md`), and the
  batching. Item 9's corrections 4–6 touch `pools.py`.
- **A pre-registration draft** for the whole batch's effect on the backtest
  (`compare_history` metrics and direction) and on the 2026 forecast (seats
  per party). It is predicted against the mechanism, never against a prior
  output.
- **The writing order,** and where the one whole-suite run sits.
- **Risks and an estimate.**
