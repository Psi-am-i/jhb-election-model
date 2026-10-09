# Diff-review dispositions (slices A and B)

**Slice A** (`A-DIFF-REVIEW-FINDINGS.txt`): all accepted.
- Accepted: B1 (the regenerations, done in the check step), B2 (G1 widened and
  routed), should-fix 1–7, and notes S1 (`forecast_data` calls
  `our_prediction`), §Q3/§Q1 wording, and the `start_state` wrap.
- Not acted on, as notes: pool-order remainder ties beyond `test_chain`'s 20
  draws; float-weighted ties (documented); the map tooltip order on a tie (no
  ties at the published seed); the `faults_between_votes_and_shares` tolerance
  (sound as a bound).
- Check step: the reproduction came out 23 of 24; the coordinator accepted
  Johannesburg 2016 as a record correction (MODEL-LOG §1.291). The expired
  DUAL_ROUNDING control was rebuilt on a constructed input.

**Slice B** (`B-DIFF-REVIEW-SUMMARY.md`): all accepted.
- Accepted: should-fix 1–6 and the notes, as sent to the writer on 2026-10-08:
  - the release order in `docs/DEPLOY-UAT.md`;
  - §R1's direction;
  - the "next edit" wording and the bounds note;
  - the bounds guard widened;
  - G8 as a pure function;
  - MACHINERY on the four readers;
  - the `paintWard` catch;
  - plain error text;
  - the `#note-vote` wording;
  - G7 scanning the tools;
  - the stale text;
  - FORMAT declared;
  - `roll_snapshot` raising an error.
- Carried to slice C: G16 compares decoded states; the card's "% of votes"
  header.
- Kept as is: `make_fixtures.py` and `placeholder-model.json`, prototype-only,
  as their headers now say.
