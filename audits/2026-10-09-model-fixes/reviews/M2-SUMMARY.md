# Slice M2 diff review: summary and dispositions (2026-10-09)

One blind reviewer, `M2-PACKET.md`, reviewing `954086b..2933c2e`. Scratch
trees and probes are in `/tmp/m2rev/`.

## The parts the review found correct (verified)
- **Statute.** Items 12(2), 13(1)(b) and 16(5) are implemented by adding the
  doubled list votes to `combined`. G7's hand council is correct.
- **Item 6.**
  - `slate_coverage` is the one definition.
  - The clip is `min(…, WARD_PR_RATIO_MAX)` with no floor.
  - No `[0, 2.0]` copy remains.
- **Item 9.** No band reader is left in `src/`, `tests/`, `worker-api/` or
  `interactive/`.
- **Numbers.**
  - At mangaung 2011 and ethekwini 2016, items 3, 9 and 10 move nothing:
    every array is bit-identical once item 6 is reverted.
  - At Johannesburg 2026 the seven parties enter at 0.42% list share
    together, and the PA's mean seats are consistent with arm B6.
- **Expected red.** `test_chain`, `test_stage_inputs` and the five
  `test_citywide_table` tests fail only on the stale code keys.

## Findings and dispositions

| # | finding | disposition |
|---|---|---|
| B1 | P8 and O5 were measured on the wrong population. Item 8 enters parties at 20 of 24 city-years, and the spec's probe read Johannesburg's previous LGE for every city. Verified by the reviewer. | Accepted. P8's panel list and its null, and O5's no-record counts, are re-measured before the pre-registration is committed (step 9). This blocks the pre-registration, not the code. |
| S1 | `41_guards.level_sd_default_parties` names roster parties outside the universe, so the batch's own predicate fires at the 2011 city-years. | Accepted: record only parties in `index`. Add a real-trace check at a 2011 city-year, or a constructed case. |
| S2 | The comment and §A29 say the sd these parties were given is the ceiling, which holds for 6 of 20. | Accepted, as a wording fix. Coordinator re-derivation, `levels.theta_prior` (~1085): a party in the record with no baseline gets `sd_for(0.0)`, which is evaluated at the 1e-5 size floor. That is a width at a size the party does not have, so `level_sd_default` stands. The comment and §A29 say exactly that, and the departure from SPEC §1.7 step 6 is recorded. |
| S3 | The width-ceiling tripwire exempts by route string, not by the drawer's predicate. | Accepted. Exempt only `41_guards.level_sd_default_parties`. Assert `_local_record_only ⊆ level_sd_default_parties`, and run the reviewer's mutation (delete `or party in local_only`) to show it is caught. |
| S4 | With `bounds_checked` out of `GUARD_DENOMINATOR_KEYS`, an unchecked board passes. | Accepted. Population check: the keys of `bounds_checked` equal {p in the declared §3.5 ranges ∩ universe with base > 0.005}. A run without `apply_city` must be told apart, not silently accepted. |
| S5 | `test_judgement_sheet` is red, not on the list. It has been red since M1. | Accepted. Regenerate `JUDGEMENT-SHEET.md` now and at step 12 (add it beside `model_index` in R3.6). |
| N1 | `{ward: None}` messages say "unopposed" where the evidence is "no ward ballot". Two independents in a declared slate would refuse falsely (argued). | Accepted. Change the wording. State the independents limit in §Q7. No code change for it. |
| N2 | `projected_contestation` now acts on vote-weighted values, which it was not fitted on. Inert at 2026. | Note in §F35. |
| N3 | `PLAN-TO-LIVE.md:459` still cites `ARRIVAL_BAND_LO/HI`. The served `site/your-forecast/py/montecarlo.py` is re-synced at the site build. | Fix the doc line. The served copy follows at the UAT build. |
| N4 | CHANGE's ward share is about 1e-6, not 0 (`level_floor`), so P6/P8's "0 in every draw" fails literally. | Pre-registration wording, at step 9. |
| N7 | The window also rebuilds the citywide table, re-ships the page's copy, and regenerates `JUDGEMENT-SHEET.md`. | Accepted. Add to R3.6 and to the window steps. |
| — | `levers_are_live`: `build_make.npe_priors(wards)` takes an argument it never reads. It comes from B2a (8dffae8), not this batch. | Fix in this round. Delete the parameter and update its callers. |
