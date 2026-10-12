# Slice B2a diff review: summary (2026-10-09)

Blind reviewer, using `B2A-DIFF-REVIEW-PACKET.md`.

**Re-derived exactly by the reviewer, in-process:**
- the record allowances: A_ward 6.98 from 15 events, A_city 5.16 from 11;
- `q_win` 18.687%;
- the gap bounds, −6.758 to +7.523;
- all eight citywide limits;
- that rule A is inside;
- that ANC dragged to 8.4% clamps at 19.447%, set by the city limit;
- the JS closed form against the probe, on 20,000 random wards: largest
  difference 2.2e-16;
- the generator against `b2r2.py`, on 9,990 ranges and 74 limits: no
  mismatches.

No B2b code and no scipy.

**Blocking:**
- B1: `city_limits` and the record-event exclusions have no regeneration
  guard. Five mutations left every test green. `ward_ranges` and
  `city_limits` derive a party's kind by two different rules.

**Should fix:**
- S1: the reader notes misstate their cause for the 54 parties with no local
  history; "widest rule" is an internal term; an eased bound is never
  mentioned; `#note-vote` is incomplete.
- S2: the TO-MEASURE tables.
- S3: an undeclared mean-turnout fallback, used for 8 of 2,819 panel wards.
- S4: a guard that cannot fail.
- S5: a docstring that states the wrong rule.
- S6: one-sided checks and an in-memory mutation.

**Notes:**
- `make_schema` checks only the keys, not the value shapes.
- `elections=` is not passed through to `expected_ward_shares`.
- The typed-bound scan allows the literal 2.

**Disposition:** all accepted and sent to the writer on 2026-10-09. The
reviewer's cache files in `s1b/probes/` were removed by the coordinator.
