# How the forecast places MK's vote in a voting district

Code at HEAD (bb280c8). 0.9 = live spec; 0.35 = same spec without judgements (parent_weight is the only owner key set).

## Short answer

Not the 2024 percentage itself: MK keeps its 2024 *ratio to its city average* in every voting district (VD), and the whole map is scaled to the 2026 citywide total. Dube Hostel Hall: 47.2% in 2024, about 34% in 2026. The splinter rule's "city average" (65% at 0.35, 10% at 0.9) never touches the map; it only books MK's citywide votes across four voter pools.

## 1. The pipeline

1. **2024 map.** MK's 2024 national-ballot share per VD and citywide (`montecarlo.py:5698-5699`): 12.22% citywide, 172,958 votes.
2. **Lean.** `dev = logit(VD share) − logit(city share)` (`:6162-6165`). Logit is log-odds; dev is how far above or below its city average MK ran there.
3. **Strength of lean, γ.** MK is in neither fold 1 nor `gamma_recent.csv`, so γ = 1.0, the typed default (`:6298-6315`, JUDGEMENT-CALLS §A48): the 2024 lean carries over in full.
4. **2026 citywide total.** Centre 10.10% (trace `30_centres`), drawn around 9.09% (`35_widths`); 5,000-draw mean 8.99%.
5. **Scale.** One multiplier θ on MK's 2024 city share, solved so VD shares weighted by expected votes (roll × turnout pattern, `:7030`) add to the drawn total (`:1373-1385`). VD share = `expit(logit(12.22% × θ) + γ·dev)`; then each VD's party shares are divided by their sum to total 100% (`:1430-1431`).
6. **Votes** = share × roll × turnout. Ward and list ballots use the same dev for MK.

## 2. Worked example (MK at 8.99%)

θ is not in the trace. Re-derived with HEAD's solve loop on the probe's mean targets, MK set to 8.99%, mean turnout weights (reproduces the probe's per-draw VD shares within 0.7pp). θ = 0.729, so MK's level = 12.22% × 0.729 = 8.90%, logit −2.326.

| | Dube Hostel Hall, VD 32871078 (2026 ward 38) | Bryanston Parallel Medium, VD 32850772 (2026 ward 106) |
|---|---|---|
| Estimated voter mix BA/Col/Ind/Wh (pool fit, `composition("voted")`, 2021 wards 79800038 / 79800106) | 98.1 / 1.1 / 0.1 / 0.7% | 4.5 / 1.3 / 3.4 / 90.7% |
| MK 2024 | 817 / 1,731 = 47.2% | 70 / 2,792 = 2.51% |
| dev | −0.112 − (−1.972) = +1.860 | −3.661 − (−1.972) = −1.689 |
| raw share | expit(−2.326 + 1.860) = 38.6% | expit(−2.326 − 1.689) = 1.77% |
| ÷ VD row total (1.132 / 1.106) | 34.1% | 1.60% |
| expected votes cast | 4,103 × 38.1% = 1,564 | 4,323 × 48.4% = 2,092 |
| MK votes | ≈ 533 | ≈ 34 |

The pool vector appears nowhere here. (100-draw probe means, total 7.69%: 30.1% and 1.78%.)

## 3. What the pool vector does

The vector (`pools.py:6363`: `α × ANC vector + (1−α) × city mix`) seeds a balance forcing each party's citywide total to its centre (`montecarlo.py:2973-2978`; per draw `_balanced_props`, `:4236`). It decides which pool's turnout shock moves MK's total.

MK's votes by pool at 8.99%:

| | Black African | Coloured | Indian/Asian | White |
|---|---|---|---|---|
| 0.9 | 87.2% (79,339) | 3.1% (2,861) | 2.1% (1,917) | 7.5% (6,830) |
| 0.35 | 68.6% (62,362) | 5.6% (5,106) | 3.5% (3,169) | 22.3% (20,325) |

Paired 5,000-draw runs (`.claude/rebuild-2026-10-15b`): mean 8.99% both, sd 7.81 vs 7.80pp, seats 23.30 both, wards 10.28 vs 10.29. Draw by draw they differ by sd 0.21pp; 4% of draws by more than 0.5pp.

**It never enters the map.** `dev` is byte-identical in both, list and ward, so its only route to a VD is MK's drawn citywide total: largest VD mean-share difference 0.023pp, against a citywide-mean difference of 0.012pp. Pool vectors place a party on the map only when it has no 2024 record (seeded arrivals, local-only parties, `:6093-6103`).

## 4. Where the 2024 map puts MK's votes

Ecological estimates from MK's 2024 VD votes and each VD's voter mix (99.6% of votes matched):

| method | BA | Col | Ind | Wh |
|---|---|---|---|---|
| neighbourhood (votes split by VD mix) | 80.9% | 3.9% | 2.5% | 12.8% |
| vote-weighted non-negative regression | 94.1% | 0.3% | 0.0% | 5.6% |

The neighbourhood method leans toward the city mix (ANC: 14.5% White vs its fitted 4.8%; regression 6.6%). Both MK estimates are nearer 0.9 than 0.35. The vector is linear in α by construction, so the White share matches α ≈ 0.97 (regression) or ≈ 0.70 (neighbourhood).

## 5. Ways to make them agree

**(a) Fit MK's vector from its 2024 VD results.** Pools are fitted on the 2021 local election (`fitted_on`); MK did not stand, so it can never be "identified" (`pools.py:6570-6575`) and the splinter rule fills in. The regression above gives support rates BA 19.7%, Col 0.5%, Ind 0.0%, Wh 2.2% (pools.py's own fitter and `identified()` test not applied). Trade-off: national-ballot support at MK's first-election peak, applied to a local election.

**(b) parent_weight only where no record exists.** (a) as a rule: a measured vector replaces the judgement, as `write_lineage_template` says should happen after an election. Trade-off: retires §SJ1; changes every splinter with a national record; needs a backtest.

**(c) Blend MK's map toward the ANC's.** A new lever on dev, like the entrant option at `:6176-6197`, whose comment records MK's 2024 map as almost the ANC's (k = 0.03). Trade-off: unlike the vector, it moves VD means and ward winners; a new, unscored judgement.
