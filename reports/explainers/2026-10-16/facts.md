# Facts for the "how the forecast is made" explainer (gathered 2026-10-15; each verified by an agent read of the code and spot-checked by the orchestrator)

## A. Where a party's 2026 citywide level comes from (ANC example; code at 17a59c1)
- Latest results: NPE 2024 Joburg ANC 31.96%; LGE 2021 PR 33.22%.
- National route: 2024 national × the party's average past national→local ratio (θ ≈ 0.878 for the ANC, shrunk toward a size-based centre; levels.py `spine`, `_shrink_one`) → 28.07%.
- Local route: 2021 local × average five-year local→local ratio (ρ ≈ 0.848) → 28.17%; blended with weight k/(worth+k), k = SPINE_K = 1.0, worth 32.9 → the ANC is ~97% national route → 28.07%.
- Big-party shrink (level_shrink 0.35; each party keeps 1 − 0.35·s/(s+0.04)): level 28.07% → 26.40%. These are LEVELS: all parties' levels sum to 1.1119; every party is divided by that common total, so the ANC's expected list share is 23.74% (5,000-draw mean 23.67%).
- No trend term: MODEL-LOG §1.184 "the model has no trend term"; trend for arrival totals tested and rejected (JUDGEMENT-CALLS §L6: out-of-sample 3.03 vs pooled mean 2.61). Owner's momentum/acceleration proposal of 2026-09-04 recorded "Not started" (MODEL-LOG §1.185).
- ANC Joburg record: local PR 2000 58.8%, 2006 62.7%, 2011 59.3%, 2016 44.9%, 2021 33.2%; national 1999 67.4%, 2004 68.6%, 2009 62.4%, 2014 52.3%, 2019 49.6%, 2024 32.0%. Straight line through local results → ~32.0% in 2026; through national 2004-24 → ~32.3%; extending only the last local step → ~21.5%. Model's expected share 23.7%.
- Expected list shares (centre / 5,000-draw mean): ANC 23.7/23.7, DA 26.0/26.0, EFF 11.0/11.0, ActionSA 11.7/11.6, MK 9.1/9.0 (median 6.7), PA 5.8/5.9.

## B. Where the variation comes from (code at 17a59c1)
1. Citywide level per party is set for 2026 (above), not copied from 2024.
2. Each simulation draws each party's citywide share around its centre; width measured from how far past local results strayed from expectations (universal draw, JUDGEMENT-CALLS §A57).
3. Turnout drawn per voting district per simulation (vd_turnout noise, montecarlo.py ~:7223); each party's ward tally multiplied by an independent ward-level random factor, sd 0.10 (`ward_noise_sd`, montecarlo.py:386, ~:7283).
- The SHAPE of the map does not change systematically: nothing moves a party up in one area and down in another except the random ward/turnout terms (polls off; by-elections weight 0 at 2026).

## C. How a party with a 2024 record is placed in a voting district (MK worked example)
Full worked example with arithmetic: /private/tmp/claude-501/-Users-simondavis-projects-atlas-jhb-election-model/f5276bbd-e0c8-4b12-ac68-aa8bf3b1000e/scratchpad/r.md (read it; numbers there, including Dube Hostel Hall 47.2% → ~34%, Bryanston 2.51% → ~1.6%, θ=0.729, γ=1.0 for MK). Key facts: the VD keeps MK's 2024 lean relative to its city average (log-odds), scaled to the 2026 city total; the pool (population-group) vector never places votes for a party with a record; it only attributes citywide votes to groups for turnout. Ecological estimate of who voted MK in 2024: 81-94% Black African — nearer the owner's 0.9 call than the 0.35 default. Owner chose option A (fit MK's vector from its own 2024 results); queued.

## D. The ward check (why the model starts from the previous ward map)
Full report: /private/tmp/wardcheck/out/REPORT.md (read it). Headline: the literal "population group shares × ward roll" recipe misses citywide (ANC +6.6 pts, DA −8.1 in 2019) because registration rates differ by group; with registration-fitted splits the city matches by construction but wards miss (hostel IFP ward 65: 59.5% counted vs 3.6%); the previous ward map scaled to the new city total beats group arithmetic 2019→2021 (9.1 vs 12.4 wrong-party share points; 130 vs 127 winners). The White pool is not White voters only (1.74 registered "White" per census White adult).

## E. The voters' roll
Forecast now reads the IEC roll of 26 Sept 2026 (identical 29 Sept): 2,417,915. The IEC counts each voting district wholly in one ward; the old roll used planners' estimated splits (ward 60: 14,810 → 25,231). A solved district-to-ward assignment reproduces IEC ward totals with a ward-ratio spread of sd 0.060 (was 0.168). The roll changes where votes are, not citywide shares (the citywide share is set first; MODEL-LOG §1.304): 2 then 5 ward favourites changed, under 1 seat per party.

## F. Small parties, independents and ward-only candidates (eight metros, 2006-2021, ward ballot)
- Ward-only small parties (on the ward ballot in <20% of wards, no PR list or <1% PR): 1,598 candidacies, 0 wins; median 0.15% where they stood.
- Independents: 5 ward wins 2011-21, all eThekwini (1 in 2011, 4 in 2016); 0 of 372 elsewhere; typical winning margin ~4 points; 9 of 10 poll-toppers beat the ANC in wards the ANC had dominated (~76% before); prior independent showing in the ward does not predict a win; in 6 of 9 the independent vote was 0 next time. Interpretation (not provable from the files, no names): splits in the dominant party's local base.
- The model's rule being built (owner): a ward-only candidate gets no list votes and can win only the wards it contests — which ward first, then who lives there (better: which party those voters already backed).
