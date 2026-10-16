# Facts for the "how the forecast is made" explainer (re-checked 2026-10-16 on code 369adb5; forecast artefacts regenerated on 08136c5)

Method of the re-check: forecast figures read from `site/draws/base.bin` + `manifest.json` (5,000 draws, seed 20261104), `data/processed/forecast_summary.json`, `ward_winner_probs.csv`, `pools_2026.json`; worked examples re-derived in process (`montecarlo.run_model` with `solve_and_predict` wrapped, 100 draws, no file written under data/**).

## A. Where a party's 2026 citywide level comes from (ANC example; run trace stages 20_spine, 30_centres)
- Latest results: NPE 2024 Joburg ANC 31.96% (recounted from `npe2024_JHB_vd_party.csv`); LGE 2021 PR 33.22%.
- National route: 2024 national x the party's average past national-to-local ratio (0.878 for the ANC, shrunk toward a size-based centre; `levels.spine`, `_shrink_one`) = 28.07%.
- Local route: 2021 local x average five-year local-to-local ratio (0.848) = 28.17%; blended with local weight 0.0295 (k = SPINE_K = 1.0, worth 32.9), so the ANC is ~97% national route = 28.07%.
- Big-party shrink (level_shrink 0.35, scale 0.04; each party keeps 1 - 0.35*s/(s+0.04)): level 28.07% -> 26.40%. All parties' levels sum to 1.1119 and every party is divided by that total: ANC expected list share 23.74% (5,000-draw mean of list-vote share 23.76%).
- No trend term (MODEL-LOG "the model has no trend term"; arrival-total trend rejected in JUDGEMENT-CALLS; owner's momentum proposal of 2026-09-04 recorded not started).
- ANC Joburg record: local PR 2000 58.8%, 2006 62.7%, 2011 59.3%, 2016 44.9%, 2021 33.2%; national 1999 67.4%, 2004 68.6%, 2009 62.4%, 2014 52.3%, 2019 49.6%, 2024 32.0%. Straight line through local results -> 32.0% in 2026 (recomputed); through national 2004-24 -> 32.3% (recomputed); last local fall repeated -> 21.5%.
- Expected list share (centre) / 5,000-draw mean list share / mean seats / seat 5th-95th / mean ward wins (deduct law; every draw sums to 270):
  - ANC 23.7 / 23.8 / 71.7 / 51-83 / 69.2
  - DA 26.0 / 26.1 / 69.8 / 52-88 / 44.4
  - EFF 11.0 / 11.0 / 30.3 / 18-46 / 3.4
  - ActionSA 11.7 / 11.7 / 27.2 / 17-40 / 0.0
  - MK 9.1 / 9.0 (median 6.7, median seats 17) / 23.4 / 4-64 / 10.5
  - PA 5.8 / 6.0 / 15.8 / 5-33 / 4.7
- Ward favourites (`ward_winner_probs.csv`, 135 wards): ANC 78, DA 45, PA 5, MK 3, EFF 3, IFP 1.
- The mean list shares are 0.01-0.15 points above the centres partly because ward-only parties leave the list ballot and their mass (about 0.4% of list votes) returns to list parties (MODEL-LOG, ward-contest rule).

## B. Where the variation comes from
1. Citywide level per party is set for 2026 (above), not copied from 2024.
2. Each simulation draws each party's citywide share around its centre; width measured from how far past local results strayed from expectations (universal draw).
3. Turnout drawn per voting district per simulation (turnout_noise_sd 0.08); each party's ward tally multiplied by an independent ward-level random factor, sd 0.10 (`ward_noise_sd`).
- The SHAPE of the map does not change systematically (polls off; by-election weights 0 for every party in the 2026 trace).
- Council: every one of the 5,000 draws seats exactly 270 (ward seats won by parties with no list are inside the 270).

## C. How a party with a 2024 record is placed in a voting district (MK worked example; supersedes mk-worked-example.md, which describes the retired 0.9/0.35 blend)
- MK 2024 national ballot: 172,958 of 1,415,548 valid votes = 12.22% (recounted). Lean gamma = 1.0; dev identical on list and ward ballots.
- MK set to 9.02% (5,000-draw mean list share); other parties' targets = 100-draw means rescaled to sum to 1; mean turnout weights. Solve step: theta = 0.7245, base level 12.218% x 0.7245 = 8.85%, logit -2.332. (Old draft: theta 0.729, 8.90%, MK 8.99%.) The replica of the solve loop reproduces a draw's own district shares exactly (5 draws checked).
- Dube Hostel Hall (VD 32871078, ward 38, whole district, 4,103 registered): 2024 817/1,731 = 47.2%; lean +1.860; raw 38.4%; row total 1.132; final 33.9%; expected cast 4,103 x 38.0% = 1,560; MK votes ~529. 100-draw mean share 30.1% (at MK total 7.73%); single step at 7.73% gives 31.2%.
- Bryanston Parallel Medium (VD 32850772, ward 106, whole district, 4,323 registered): 2024 70/2,792 = 2.51%; lean -1.689; raw 1.76%; row total 1.084; final 1.63%; expected cast 4,323 x 48.7% = 2,105; MK votes ~34. 100-draw mean 1.81%; single step at 7.73% gives 1.31%.
- Voter mix (pool fit, composition("voted"), 2021 wards 79800038 / 79800106) unchanged: 98.1/1.1/0.1/0.7% and 4.5/1.3/3.4/90.7%.
- MK's group vector is now fitted from its own 2024 national results by ward (`pools.vector_from_own_record`; spec `fitted_from_national`): rates BA 19.5%, Col 0.0%, Ind 0.3%, White 1.9%; identified in BA and White only; BA rate bounds 12.6%-20.5%. Votes booked to groups: BA 94.3%, Col 0.0%, Ind 0.1%, White 5.6% (was 87.2/3.1/2.1/7.5 under the parent_weight 0.9 blend). RISE (BA 18.7, Col 6.8, Ind 14.0, White 60.6) and BOSA (29.4/3.3/7.4/59.9) are fitted the same way; five parties whose 2024 fit identifies no pool keep the lineage rule.
- The vector still only books citywide votes to groups for turnout; it never places votes for a party with a record (`place_by_pool` is called only for seeded arrivals and local-record-only parties). Not re-measured: the old paired 0.9-vs-0.35 comparison (sd 0.21 pp etc.) described a retired arm and is dropped from the page.

## D. The ward check (why the model starts from the previous ward map) - NOT re-run
Full report: /private/tmp/wardcheck/out/REPORT.md. Scores 2019/2021 on the 2021 ward map; independent of the 2026 model changes. Headline: literal "population group shares x ward roll" misses citywide (ANC +6.6 pts, DA -8.1 in 2019); previous ward map scaled to the new city total beats group arithmetic 2019 -> 2021 (9.1 vs 12.4 wrong-party share points; 130 vs 127 winners).

## E. The voters' roll
- IEC roll of 26 Sept 2026 (identical 29 Sept): 2,417,915 in 865 VDs and 135 wards (summed from `ward_parts`: 1,059 VD-ward rows, 181 split in the planners' file; after assignment every VD with registration sits in one ward - checked).
- Each VD wholly in one ward by a solved assignment (`archive/vd-ward-assignment-2026/`). Ratio of IEC ward total to assigned 2024 registration: sd 0.060 (0.82-1.27), against sd 0.168 (0.70-1.70) under proportional scaling. Ward 60: 14,810 registered in 2024 (planners' parts), 25,231 in the IEC 2026 count (checked). About 17 VDs counted in wards neither geo file offers; 40 near-tie placements.
- Effect: IEC ward totals alone changed 2 ward favourites (120, 124; DA to ANC; ANC mean seats 71.2 -> 71.7). Whole-VD assignment changed 5 more (34 ANC>MK, 68 DA>PA, 82 PA>DA, 92 DA>ANC, 120 ANC>DA); largest mean-seat move 0.12 (ANC 71.71 -> 71.83) (reports/model-changes/2026-10-16/prereg-scoring.md). City-wide shares unchanged (largest move 0.001 points).

## F. Small parties, independents and ward-only candidates
- History (eight metros, 2006-2021, ward ballot; NOT re-derived - a quick recount from the merged IND rows gives 5 eThekwini wins in 2016 and 1 Buffalo City win in 2021 against the IEC's published 4 and 0, the same gap MODEL-LOG records when it put C in the truth; the page quotes the IEC's figures): ward-only small parties 1,598 candidacies, 0 wins, median 0.15% where they stood; independents 5 ward wins 2011-21, all eThekwini (1 in 2011, 4 in 2016); 0 of 372 elsewhere; typical winning margin ~4 points; 9 of 10 poll-toppers beat the ANC in wards it dominated (~76% before); in 6 of 9 the independent vote was 0 next time. Splits in the dominant party's base is an interpretation, not provable from the files.
- 2026 ballots (`levels.ballots`, judgements/joburg-2026.toml roster): 82 parties = 75 with a list + 7 ward-only; 80 with ward candidates. Ward-only in the model: Afrika Unite Congress (2 wards), Civic Movement for Progressive Citizens (135), MAWUSA Movement Party (26), Resident Development (1), Tau Dia Rora Cultural and Traditional Lekgotla (1), UDM (134); the seventh, INDEPENDENT, is outside every run's universe.
- Rule (live): a ward-only party gets no list votes (list vote 0 in all 5,000 draws) and is masked to its slated wards; 49 of 81 modelled parties have a ward-ballot mask; CHANGE and PRO SOUTH AFRICA stand for the list only. Ward wins by ward-only parties over 5,000 draws: Resident Development 71 draws, Tau Dia Rora 65, Afrika Unite Congress 42, others 0; 175 draws (3.5%) have at least one, max 3, mean 0.04 seats per draw; each won only a slated ward.
- Small-party geography: all 53 pool-placed parties have a non-flat list-ballot map (largest range across VDs 6.57 log-odds).
