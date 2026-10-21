# Blind pollster review: turnout at `4fb8002` (2026-10-17)

Brief: `../POLLSTER-BRIEF.md`, issued verbatim. Read-only. Scratch scripts `decomp_check.py`, `error_vs_shift.py` (copied beside this file). [V] verified by the reviewer in code, spec or data; [R] taken from `map/map.md`, `measure/report.md` or MODEL-LOG §1.317.

## Verified by the reviewer

- [V] The citywide turnout level does not reach shares or seats: a district's votes are reg × n × mix with mix normalised (`district_pool_turnout`, `drawn_district_turnout`, `district_votes`); a common factor leaves shares, ward argmaxes and quotas unchanged, the 0.95 clip excepted. What reaches the vote is the district turnout pattern and the pool shocks k_g = drawn/reference relative to each other.
- [V] The skew is constructed: `pools.turnout_band` is symmetric in logit around the last LGE pool rate; `_tri_ppf` draws a triangular in turnout space; E[k] = mean/mode > 1 below 50% turnout, < 1 above. JHB 2026 (`pools_2026.json`): Black African ×1.0224, Coloured ×0.9824, Indian/Asian ×1.0855, White ×0.9942. Indian/Asian band 0.085–0.836 (half-width 2.0 logits). No measurement of the direction of turnout change enters.
- [V] A symmetric triangular of half-width h holds 90% within ±0.684h, so a support edge at the record's q90 |Δlogit| gives a 90% interval ≈ 0.68 × q90.
- [V] Projected citywide turnout has no skill over "same as last LGE": mean abs error 9.45 vs 9.46 points (24 city-years, `partA1_citywide.csv`); cycle means +13.1 / +6.9 / −8.4, sd 11.1; within-cycle residual 2.8 points RMS.
- [V] Between-district turnout composition, independent decomposition from raw IEC files: DA +1.34 (2011→16) and +1.57 (2016→21), 8-metro means, positive at 7/8 each; JHB +1.24 and +0.69 (report: +1.45, +1.5, +1.38, +0.77; convention differences).
- [V] Model list error at `4fb8002` (`history.json`) vs the realised-minus-projected composition shift (`partA4`), 24 city-years: correlation −0.07 (DA), +0.06 (ANC). Adding the shift: DA MAE 3.35 → 3.71, ANC 3.31 → 3.61; demeaned shift: DA 3.46, ANC 3.27. Mean model-minus-actual by cycle: 2011 DA −5.67, ANC −5.75; 2016 +0.90, +0.06; 2021 +2.96, +1.56.
- [V] Within-district slope of share change on turnout change (`partB6`), non-mixed districts: |slope| ≤ 0.2 share points per turnout point at every metro, DA and ANC, 2011→16 and 2016→21; mixed signs, mostly < 0.1.

## Q1. Fit to drive a published forecast?

- Mean: no, as built. The only route by which it moves the means is the skew, whose sign is set by each pool's 2021 turnout being above or below 50%. JHB 2026: DA −0.28 points, −0.6 seats, P(ANC largest alone) +2.8 points [R]; the record's realised differential has the opposite sign at 18/24 [R]. The structure (district votes = reg × turnout × mix) is right and harmless once the skew is removed.
- Width: not supported as turnout-derived width. Pool shocks add DA sd 3.77 → 4.20 [R]; band narrow by construction [V]; coverage 13/24 (level) and 15/24 (differential) [R]; CRPS 542.7 → 542.5 [R]. Acceptable only as declared, unvalidated variance, conditional on list-share PIT/coverage at N-P passing (not seen).
- Reader turnout control: not fit; withdraw or label unvalidated. §1.315: Black African +5 points → DA −4.1 seats [R], the conditional the oracle arms contradict; any displayed turnout figure inherits a level forecast with no skill.

## Q2. Why does feeding realised turnout raise list error?

- (i) Ecological pool-turnout bias: partly; not the whole cause (N-Ovd +0.478, N-Opool +0.672 [R]; ≈0.19 attributable).
- (iii) θ already carries local-election turnout behaviour: leading explanation, untested. θ contains the NPE→LGE composition (+1.8 to +2.7 DA per cycle [R]); the projection under-predicts DA-area turnout (19/24 [R]); feeding realised turnout re-applies a composition θ absorbed. Consistent: shift uncorrelated with model error [V]; worsens DA where the centre was already high [V]; demeaned shift does not help [V]. §V1 records the θ-implied reference was not built.
- (ii) Within-pool preference moves with turnout: weakly bounded at district level (≤0.2, mixed signs [V]); mixed districts and citywide differential abstention not identified.
- (iv) Centres already wrong, so any systematic move scores worse: part of it on the DA side [V]; does not explain the ANC side (2016 errors ≈0, shift hurt 0.69 → 1.28 [V]).
- Separating measurement: θ re-estimated on shares standardised to the turnout pattern the projection method would have produced for each training election; run N-P and N-Ovd on it. Under (iii) N-Ovd beats N-P pooled and at ≥14/24; under (ii) it still loses. Cheaper first look: composition anomaly against θ's training average vs centre error; correct mechanism → clearly negative DA correlation (within-cycle against the projection-based shift: −0.3 [V], undecided at n=24).

## Q3. Is 3.212 → 3.152 evidence the change is right?

No. It comes from the skew [R], whose direction no measurement sets [V]; the DA was over-forecast at 2016/2021 targets [V], so a fixed DA-down nudge helps by construction (largest gains NMB 2016, CPT 2016 [R]). Better at 15/24, sign test p ≈ 0.31; no standard error for 0.06. Accidental tuning, in a direction the record contradicts at 18/24.

## Q4. Ranked improvements

1. Remove the skew (logit-space draw with median at centre, or normalise k to mean 1). JHB 2026 ≈ DA +0.28, P(ANC largest) −2.8 [R]. Pre-register list error rising ≈0.06 toward 3.21; record as debt. Hours. Removes an artefact.
2. Reference consistent with θ (θ-implied reference, or θ on turnout-standardised shares; test in Q2). Days plus re-emit. Estimation.
3. Pool shocks from a fitted spread, not a support edge: logit-normal/t, sd and ρ fitted to panel Δlogit; target the Black African–White differential with a counted proxy (single-pool districts), not `pool_counts`. Accept at 19–24/24 coverage at nominal 90% on held-out cycles (today 13, 15). ≈1 day plus re-emit. Estimation.
4. Citywide level: band a published figure from the panel distribution of LGE/NPE turnout ratios over strictly earlier cycles; 90% coverage over 24. Low cost. Estimation.
5. Spatial pattern: weight the previous LGE pattern over λ (λ worst at 22/24 [R]; §1.2 MAE 0.0409 vs 0.0592). Pre-register held-out pattern-only RMSE falls and the A4 partisan slope shrinks toward 0. Low cost. Estimation.
6. Pool turnout rates: one definition, bootstrap SEs, shrink failing pools to the panel; test on counted turnout in single-pool districts. Medium. Estimation.
7. Width-record carry with the draw's own function; σ with/without by CRPS and coverage. Medium. Estimation.
8. Within-pool party-specific turnout elasticity only if test 2 fails; record bounds it small; high cost and tuning risk.
9. Register: IPF rounds to tolerance (D5), correct §V4; remove "the band is the model's forecast of turnout" from §V6; re-measure §A41, §F23, §F34.

Wrong now: 1, 9. Undefended: 3–7.

## Q5. What should ship?

Turnout entering the vote, with the skew removed, the reference unchanged until test 2 runs, and the turnout control withdrawn or labelled unvalidated. With the skew out, turnout's effect on the means is ≈0 (`turnout_moved` DA +0.04 [R]), so the record cannot separate old and new on means; the old mechanism's property that turnout reached nothing was false of the world (between-district composition +1.3 to +1.6 DA per cycle [V]). Nothing relying on the turnout-to-vote conditional (scenarios, validated width) until the θ-consistent reference is tested. The ≈0.06 list-error rise from removing the skew is debt with hypothesis (iii).
