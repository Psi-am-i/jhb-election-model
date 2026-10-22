# Slice M3 diff review: summary and dispositions (2026-10-09)

One blind reviewer, `M3-PACKET.md`, reviewing `309481f..22dadaa`. The
reviewer's scratch trees and probes are in `/tmp/m3rev/`.

## The parts the review found correct (verified)
- **Item 12 changes no drawn number.** Johannesburg 2026, 200 draws, with the
  record and without it: every stage and every guard is byte-identical.
- **Item 11a.** `_shrink_one` is the one per-party body, evaluated at the
  party's current size.
- **Item 16's window is estimation, not tuning.** It is scored against
  realised ratios. The walk-forward has no look-ahead and its records are
  nested. The reviewer re-derived both 2026 windows independently and got the
  same values.
- **Item 17.** `level_shock_sd` is the one definition. `level_sd_default`
  binds nowhere at 2021 or 2026.
- **Expected red.** Every failure checked is red for the R3.6 cause.

## Coordinator re-derivation
I re-ran KEY 4's committed held-out NLL with `/tmp/m3rev/key4.py`, with no
window and with the run's own window:
- **2021:** 1.1299 with no window, 1.0391 with the run's window (h = 3.0).
- **2006, 2011, 2016:** unchanged, because the window is ∞ at those targets.
- **Conclusion:** the baselines re-recorded in a885b28 measure an estimator
  the model no longer runs.

## Owner's decisions (2026-10-09)
- **`level_sd_default` is deleted:** "If the old constant has been replaced
  with new machinery it should be deleted."
- **CLAUDE.md §5 gains the `group_share_record.py --emit` line.** The
  coordinator added it, with the owner's approval.
- **The window tie is settled by measuring the uncertainty.** Compute a
  cycle-clustered paired difference between the best window and each wider
  one. Take the widest window that is not measurably worse than the best.
  The rule is written down before it runs.
- **The tripwire is left as specified.** The owner: "the tripwire cant fire
  for the party which has the largest rise and sets the tripwire. I do not see
  why that is a problem." The pre-registration states that the PA/Coloured
  pair cannot fire under this rule, replacing O1's prediction.

## Dispositions

| # | finding | disposition |
|---|---|---|
| 1 | KEY 4 and PIT were re-recorded with no window; `theta_residual` passes no `h`. | Fix. Pass each fold's `size_window` into `theta_prior`, and add the window constants to `_levels_state`'s cache key. Re-record KEY 4 and PIT, with the reason written in the file. `test_drawer`'s goldens are re-recorded once, after the re-emit, at the run's windows. |
| 2 | The PA's outcome turns on the typed tie, `SIZE_WINDOW_TIE`. | Owner: measure it. The window rule becomes "the widest window whose cycle-clustered paired error difference from the best is not measurably worse". Write the rule first, in `JUDGEMENT-CALLS.md` §A52 and the docstring, then run it. It applies to every target and route. Report the windows it gives. The typed tie is deleted if the new rule replaces it. |
| 3 | The tripwire cannot see PA/Coloured. | Owner: leave it. The pre-registration says so at step 9. |
| 4 | `theta_residual.form_b`/`form_c` re-implement the shrink at the observed size. | Fix. Route both through `levels._shrink_one`, and correct `form_b`'s docstring. |
| 5 | A silent "no record" passes every predicate, and the city slug falls back to `""` in silence. | Fix. The slug lookup refuses a target with no city. After the window's `--emit`, a real run at a covered city-year must report a count, not "no record". Add this to the R3.6 window steps. |
| 6 | G21's set check is tautological; G15's "can see" step tests nothing; G19's h=∞ line compares a value with itself. | Fix each. Build the expected set independently, construct a real stale record, and drop or replace the G19 line. |
| 7 | `level_sd_default` is inert. | Owner: delete it. A party with no size and no θ fit stops the run instead of falling back. Show by an in-process scan that this never happens at the 24 panel city-years or 2026. Add the name to the register's `DELETED`. |
| 8 | Nothing checks that `level_sd_at_size` and `level_sd_default_parties` are disjoint. | Moot after 7. |
| 9 | §A52 copies the per-target window values, which are measurements. | Replace them with a pointer to the `20_spine` trace. The values go in the batch's MODEL-LOG entry at step 13. |
| 10 | `site/methodology.html` must not deploy before the re-run. | Already true: one UAT carries both. Noted for the deploy. |
| 11 | `theta_prior` and `spine` receive different baselines for seeded parties. This is harmless: seeded parties take the seeded level and zero shock. | Note only. |
