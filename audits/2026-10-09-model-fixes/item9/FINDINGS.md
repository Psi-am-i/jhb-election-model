# Item 9: the 46 seeded parties with no level shock

Read-only investigation, 2026-10-09, Atlas. Scripts and raw outputs are in
`scripts/`. Every draw figure comes from an in-process `run_model`, Johannesburg
2026, 5,000 draws, seed 20261104, `PYTHONHASHSEED=0`, with `DEFAULTS`
(`scripts/run.py`).

**The base run reproduces the published draws exactly** (verified,
`scripts/check_pub.py`): all 5,000 × 74 seat vectors (`seats/deduct`) and all
list-vote vectors in `site/draws/base.bin` are identical. Model sources are
unchanged between 75123b3 and HEAD; the uncommitted edits are outside the
model modules.

Variants (same seed; the random stream diverges once a variant changes a draw):
- **base**: the published model.
- **nosplit**: every `rng.dirichlet` inside `make_drawer` returns its mean. This
  removes the within-pool split (and would remove the arrival-group Dirichlet,
  which is off by default). What remains is turnout, the other parties' level
  shocks through the IPF balance, and the ward layer.
- **shock**: the 46 seeded parties get a level-shock sd from the size line
  fitted to the 28 non-seeded pooled parties (`sd = 0.0018 − 0.0700·ln(centre)`,
  0.29–0.56 across the 46; `scripts/sdmap.json`).

## Ranked findings

1. **The within-pool split is effectively all of the 46's variation** (verified).
   The 90% log width of the drawn list share, `W = ln(q95/q5)`, is 5.6–8.3 for
   the 44 generic entrants under base and 0.20 under nosplit, for every one of
   them. The pool concentrations are A = 16.3 (Black African), 20.9 (Coloured),
   21.4 (Indian/Asian) and 22.1 (White), so a member at a 0.07% mean has a
   per-component concentration of about 0.01: a spike at zero with a rare large
   draw. The median draw for each of the 44 is 0.0001% of the list vote (about
   one vote); 78–93% of draws are below 0.01%.

2. **By the declared test the 44 entrants are too wide; at the seat level they
   match the record, given the group budget** (verified; the two measures
   disagree, and the disagreement goes to the owner).
   - Declared test (written in `scripts/analyse.py` before the draw statistics
     were computed): drawn `W` against the bootstrap 90% CI of `W` over the
     party's reach-matched comparators from the spec's own `entrant_record`
     (|reach − r| < 0.25, as `arrival_rules` builds it). All 45 entrants:
     **too wide**. Drawn W 5.6–8.3; comparator W 3.1–4.3, CI upper bound at most
     4.8. The excess is entirely below the median: the drawn q5 and q50 are
     equal (0.0001%), and no comparator arrival on record scored below 0.01%.
   - Seat-level check: the drawn list share at which P(≥1 seat) passes 0.5 is
     about 0.19%. Fraction of reach-matched comparators at or above 0.19%:
     0.34 (reach ≈ 1), 0.20 (≈ 0.5), 0.12 (≈ 0.15) on the raw record; 0.083,
     0.036 and 0.026 after the same ×0.22 group rescale the model applies. Drawn
     P(≥1 seat): 0.06–0.09 (reach ≈ 1), 0.04 (≈ 0.4–0.5), 0.03 (≤ 0.25).
   - Upper tail: drawn q95 for a reach-1 entrant is 0.23–0.39%; comparator q95
     × 0.22 is 0.31%.
   - Coverage (share of comparator results inside the party's drawn 5–95%
     interval, 90% if location and width both match): 0.67–0.76 at reach ≥ 0.7,
     0.30–0.66 below. This mixes location (the ×0.22 rescale) with width.
   - The ×0.22 rescale conditions each party on a ballot of 45 entrants. The
     record supports a negative relation (corr(entrant count, mean log share)
     = −0.50 over 24 city-years) but its largest ballot held 34 entrants, so
     2026 is an extrapolation (argued).

3. **The 45 as a group vary about as much as the record** (verified).
   Drawn group total (sum of the 45 list shares): q5 / q50 / q95 = 0.43 / 2.65
   / 9.09%, sd(log) 0.95, W 3.06. Record of entrant totals per city-year
   (entrants absent from the previous LGE PR ballot, splits excluded, 24
   panel city-years 2011–2021): 0.59 / 2.21 / 5.86%, sd(log) 0.81, W 2.29. The
   spec's own arrival-group record (29 metro-years) has sd(log) 1.04. Largest
   entrant's share of the group: drawn median 0.55 (q5 0.30, q95 0.90); record
   median 0.48 (q5 0.19, q95 0.78). The group is drawn slightly wider and
   slightly more concentrated than the record; the record has no city-year
   common factor large enough to require one (ICC of log entrant share by
   city-year 0.15; within-city-year sd 1.14 against 1.23 overall).

4. **Adding the missing level shock changes almost nothing** (verified, shock
   variant). Median generic P(≥1 seat) 0.059 → 0.064; median generic q95
   0.234% → 0.296%; group seats mean 8.15 → 9.15 (q5–q95 1–22 → 1–24); SACP
   seats mean 3.49 → 3.58, P(≥1) 0.69 → 0.69. Seat means of ANC, DA, EFF, MK,
   ASA and PA move by at most 0.46. The group-seat rise is mostly a level
   effect of the counterfactual, not width: `log_shock` has median 1 and mean
   above 1, so shocking these parties raises their expected share before
   normalisation (argued). The width-relevant figures are P(≥1 seat) and q95. Non-seeded parties of the same centre that
   do carry a shock (COPE 0.066%, sd 0.43; ACFT 0.048%, sd 0.55; Bolsheviks
   0.040%, sd 0.65) draw the same shape as their seeded neighbours: q5 = q50 =
   0.0001%, P(≥1 seat) 0.03–0.05.

5. **The SACP is wider than every record it can be compared with** (verified).
   Declared at 1.31% (JUDGEMENT-CALLS §L13), centre 1.62%, drawn mean 1.40%,
   drawn q5 / q50 / q95 = 0.0044 / 0.58 / 5.61%: W 7.15, upper half
   ln(q95/q50) 2.27, lower half ln(q50/q5) 4.89. Its emitted band is 0.15–4.78×
   the centre (W 3.46). Continuing parties starting at 1–5% (panel, n 52) show a
   log-ratio q5 / q50 / q95 of −1.93 / −0.76 / +0.78 (W 2.71, halves 1.17 and
   1.54). Seats: median 1, q5–q95 0–14, mean 3.49, P(≥1) 0.69. It has
   concentration ≈ 0.25 in the Black African pool, so the split puts 8% of
   draws below 0.01%. The shock is not the cause and would not fix it.

6. **Two of the 46 are centred far above their seed by the by-election tilt**
   (verified from `data/processed/byelection_party_deltas.csv` and the earlier
   investigation's `q1_w_bye0.json`, not re-run here). All Citizens Party: seed
   0.036%, centre 1.07%, drawn mean 0.91%, P(≥1 seat) 0.61, from 2 contests
   (weighted delta +2.05 pp; 198 votes in two Johannesburg ward by-elections,
   2025-10-15 and 2026-02-25). With `w_bye = 0` its list mean was 0.050%.
   Truth and Solidarity Movement: centre 0.111% against 0.086% for its peers,
   0.062% with `w_bye = 0`. Within item 9's population this is the largest
   single deviation from the arrival record, and it is a level question, not a
   width one.

7. **The split's spike reaches parties with a real record** (verified; outside
   item 9's population, reported because it is the same mechanism). PAC, centre
   0.37%, real Johannesburg results 0.267% (2021 LGE) and 0.230% (2024
   provincial ballot), draws a median of 0.0048% and P(< 0.01%) = 0.55. AIC,
   AHC, ATM, UDM, AZAPO, APC and Dudula behave the same way. The record for
   continuing parties starting at 0.25–1% has a log-ratio q5 of −1.42 (n 92).
   This belongs to the within-pool split reformulation already scheduled.

8. **Seeded centre, seed and drawn mean are three different numbers** (verified).
   For a generic reach-1 entrant: seed 0.064% (spec), centre 0.086% (stage
   30_centres, ≈1.35 × seed), drawn mean ≈ 0.074% (centre ÷ Σcentres, Σcentres
   = 1.17). The 1.35 ratio between seed and centre was not traced here (seeds
   are added to `base_city_d` at `montecarlo.py` ~4336; the cause lies
   downstream of that). Consequence: the 44 generic entrants' drawn means sum to
   about 2.49% of the list vote (group 3.40% less All Citizens 0.91%), against
   the 2.19% arrival-total budget the record set, about 14% larger than
   declared (verified arithmetic; cause not traced).

## Q1. Who they are

46 seeded parties, all on the declared 2026 roster (`roster_source = declared`)
and absent from both the 2024 Johannesburg provincial-ballot baseline and the
2021 Johannesburg LGE. None has a Johannesburg result in 2021 or 2024
(verified against `data/raw/elections`, canonical names; the `npe2024` file is
the **provincial** ballot, from `Provincial.zip`, SOURCES.md). 45 are
"entrant from nothing", sized at the mean of their reach-matched comparators
and then rescaled ×0.22 as a group (45 entrants summing to 9.93% against an
arrival-total record of 2.19%). The SACP is declared in
`judgements/joburg-2026.toml` and sits outside the group budget. Seeded mass
3.50% of the city (spec `seeded_arrival_mass`). Seats are `seats/deduct`.

| party | reach | seed % | centre % (after shrink) | centre ÷ Σcentres % | drawn mean % | drawn list share q5 / q50 / q95 % | seats median (q5–q95) | P(≥1 seat) | why seeded | record elsewhere |
|---|---|---|---|---|---|---|---|---|---|---|
| SOUTH_AFRICAN_COMMUNIST_PARTY |  | 1.310 | 1.622 | 1.386 | 1.399 | 0.0044 / 0.5802 / 5.606 | 1 (0–14) | 0.69 | owner-declared size 1.31% (JC §L13), weights declared | none |
| ALL_CITIZENS_PARTY | 36% | 0.036 | 1.072 | 0.916 | 0.914 | 0.0041 / 0.3236 / 3.884 | 1 (0–10) | 0.61 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale; centre raised by by-election tilt | 2024 prov. ballot ETH 0.018%, MAN 0.052% |
| TRUTH_AND_SOLIDARITY_MOVEMENT | 97% | 0.064 | 0.111 | 0.095 | 0.089 | 0.0001 / 0.0001 / 0.394 | 0 (0–1) | 0.09 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale; centre raised by by-election tilt | none |
| AFRICAN_RENAISSANCE_UNITY | 72% | 0.067 | 0.090 | 0.077 | 0.072 | 0.0001 / 0.0001 / 0.282 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| VUKA_SA | 95% | 0.065 | 0.087 | 0.074 | 0.073 | 0.0001 / 0.0001 / 0.226 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| INDEPENDENT_CITIZENS_MOVEMENT | 92% | 0.064 | 0.086 | 0.074 | 0.071 | 0.0001 / 0.0001 / 0.260 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | 2021 LGE EKU 0.451% |
| MOVE_SA | 97% | 0.064 | 0.086 | 0.074 | 0.074 | 0.0001 / 0.0001 / 0.254 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AFRICAN_ECONOMIC_FREEDOM | 100% | 0.064 | 0.086 | 0.074 | 0.070 | 0.0001 / 0.0001 / 0.296 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AFRICAN_UNEMPLOYED_CONGRESS | 100% | 0.064 | 0.086 | 0.074 | 0.063 | 0.0001 / 0.0001 / 0.234 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AFRIKA_MAYIBUYE_MOVEMENT | 100% | 0.064 | 0.086 | 0.074 | 0.079 | 0.0001 / 0.0001 / 0.288 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| ALLIED_INDEPENDENTS_UMBRELLA | 100% | 0.064 | 0.086 | 0.074 | 0.068 | 0.0001 / 0.0001 / 0.256 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| ALL_NATIVES_OF_SOUTH_AFRICA | 100% | 0.064 | 0.086 | 0.074 | 0.087 | 0.0001 / 0.0001 / 0.349 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AZANIAN_GROUND_FORCES | 100% | 0.064 | 0.086 | 0.074 | 0.063 | 0.0001 / 0.0001 / 0.269 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| CIVIC_MOVEMENT_FOR_PROGRESSIVE_CITIZENS | 100% | 0.064 | 0.086 | 0.074 | 0.080 | 0.0001 / 0.0001 / 0.301 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| EKHETHU_PEOPLES_PARTY | 100% | 0.064 | 0.086 | 0.074 | 0.073 | 0.0001 / 0.0001 / 0.295 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| KNOW_YOUR_POWER | 100% | 0.064 | 0.086 | 0.074 | 0.075 | 0.0001 / 0.0001 / 0.248 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| LABOUR_PARTY_OF_SOUTH_AFRICA | 100% | 0.064 | 0.086 | 0.074 | 0.077 | 0.0001 / 0.0001 / 0.268 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| MINORITY_FRONT | 100% | 0.064 | 0.086 | 0.074 | 0.068 | 0.0001 / 0.0001 / 0.256 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | LGE ETH 2000-2021 (4.66, 6.24, 4.94, 0.46, 0.50%) |
| NCC | 100% | 0.064 | 0.086 | 0.074 | 0.074 | 0.0001 / 0.0001 / 0.271 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | 2024 prov. ballot CPT 3.48% |
| PEOPLE_OF_JOBURG | 100% | 0.064 | 0.086 | 0.074 | 0.065 | 0.0001 / 0.0001 / 0.234 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| PEOPLE_S_MOVEMENT_FOR_CHANGE | 100% | 0.064 | 0.086 | 0.074 | 0.071 | 0.0001 / 0.0001 / 0.300 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | 2024 prov. ballot CPT 0.186% |
| SERVICE_DELIVERY_PARTY | 100% | 0.064 | 0.086 | 0.074 | 0.070 | 0.0001 / 0.0001 / 0.259 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| ACTIVE_AFRICAN_CHRISTIANS_UNITED_MOVEMENT | 99% | 0.063 | 0.086 | 0.073 | 0.072 | 0.0001 / 0.0001 / 0.265 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| SOUTH_AFRICAN_PEOPLE_S_CIVIC_ORGANIZATION | 99% | 0.063 | 0.085 | 0.073 | 0.066 | 0.0001 / 0.0001 / 0.278 | 0 (0–1) | 0.06 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| UMPHAKATHI_WARONA | 98% | 0.063 | 0.085 | 0.073 | 0.075 | 0.0001 / 0.0001 / 0.287 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| NATIONAL_DEMOCRATIC_CONVENTION | 76% | 0.060 | 0.081 | 0.069 | 0.081 | 0.0001 / 0.0001 / 0.293 | 0 (0–1) | 0.07 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | 2006 LGE JHB 0.233% (and 4 other metros) |
| PRO_SOUTH_AFRICA | 50% | 0.045 | 0.061 | 0.052 | 0.053 | 0.0001 / 0.0001 / 0.133 | 0 (0–0) | 0.04 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AFRICAN_LABOUR_CONVENTION | 38% | 0.038 | 0.051 | 0.043 | 0.042 | 0.0001 / 0.0001 / 0.086 | 0 (0–0) | 0.04 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| ECONOMIC_REDRESS_MOVEMENT | 4% | 0.032 | 0.043 | 0.037 | 0.034 | 0.0001 / 0.0001 / 0.052 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| LAND_PARTY | 4% | 0.032 | 0.043 | 0.037 | 0.032 | 0.0001 / 0.0001 / 0.062 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | 2021 LGE CPT 0.042%; 2024 prov. ballot CPT 0.032% |
| GAP_FIXERS_OF_SOUTH_AFRICA | 6% | 0.032 | 0.043 | 0.037 | 0.037 | 0.0001 / 0.0001 / 0.073 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| KINGDOM_COVENANT_DEMOCRATIC_PARTY | 6% | 0.032 | 0.043 | 0.037 | 0.033 | 0.0001 / 0.0001 / 0.057 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| COMBAT | 14% | 0.031 | 0.042 | 0.036 | 0.046 | 0.0001 / 0.0001 / 0.057 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| COMMUNITY_FIRST_MOVEMENT | 15% | 0.031 | 0.042 | 0.036 | 0.044 | 0.0001 / 0.0001 / 0.082 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AFRICAN_ROYAL_RAINBOW_CONGRESS | 21% | 0.031 | 0.042 | 0.036 | 0.037 | 0.0001 / 0.0001 / 0.059 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| GAZA_DEMOCRATIC_FRONT | 21% | 0.031 | 0.042 | 0.036 | 0.031 | 0.0001 / 0.0001 / 0.072 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| ILIZWE_NATHI | 17% | 0.031 | 0.042 | 0.036 | 0.042 | 0.0001 / 0.0001 / 0.076 | 0 (0–0) | 0.04 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| IMSTAYING | 17% | 0.031 | 0.042 | 0.036 | 0.035 | 0.0001 / 0.0001 / 0.060 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| MAWUSA_MOVEMENT_PARTY | 19% | 0.031 | 0.042 | 0.036 | 0.033 | 0.0001 / 0.0001 / 0.075 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| MOVEMENT_OF_RESIDENTS_PARTY | 24% | 0.031 | 0.042 | 0.036 | 0.034 | 0.0001 / 0.0001 / 0.074 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| AFRIKA_UNITE_CONGRESS | 1% | 0.029 | 0.039 | 0.033 | 0.036 | 0.0001 / 0.0001 / 0.056 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| CHRIST_KINGDOM_PARTY | 1% | 0.029 | 0.039 | 0.033 | 0.036 | 0.0001 / 0.0001 / 0.058 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| LEKWE_BEPE_KINGDOM_PARTY | 1% | 0.029 | 0.039 | 0.033 | 0.034 | 0.0001 / 0.0001 / 0.055 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| PEOPLE_S_CONSENT_PARTY | 1% | 0.025 | 0.033 | 0.028 | 0.030 | 0.0001 / 0.0001 / 0.031 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| RESIDENT_DEVELOPMENT | 1% | 0.025 | 0.033 | 0.028 | 0.027 | 0.0001 / 0.0001 / 0.029 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |
| TAU_DIA_RORA_CULTURAL_AND_TRADITIONAL_LEKGOTLA | 1% | 0.025 | 0.033 | 0.028 | 0.032 | 0.0001 / 0.0001 / 0.035 | 0 (0–0) | 0.03 | entrant from nothing; reach-matched comparator mean × 0.22 group rescale | none |

## Q2. The record

Citywide PR shares, 8 metros, consecutive LGE pairs with targets 2011, 2016
and 2021 (the 24-city-year panel), read with `levels._citywide_and_roster`
(the HELD_BACK gate is bypassed deliberately: this measures the world and
feeds no model). Continuing = on both PR ballots. Bin = share at the earlier
election. Log ratio = ln(later/earlier). Absolute change in percentage points.
Departed = on the earlier PR ballot, absent from the later one.

| starting share | continuing n | departed n (rate) | log ratio q5 / q25 / q50 / q75 / q95 | sd | W = q95 − q5 | abs change pp q5 / q50 / q95 |
|---|---|---|---|---|---|---|
| 0–0.05% | 15 | 61 (0.80) | −1.18 / −0.10 / +0.75 / +1.03 / +1.54 | 0.87 | 2.73 | −0.027 / +0.026 / +0.062 |
| 0.05–0.1% | 19 | 38 (0.67) | −0.92 / −0.59 / +0.08 / +0.44 / +0.84 | 0.69 | 1.76 | −0.053 / +0.004 / +0.136 |
| 0.1–0.25% | 49 | 44 (0.47) | −1.46 / −0.69 / −0.15 / +0.28 / +1.52 | 0.91 | 2.99 | −0.150 / −0.020 / +0.878 |
| 0.25–1% | 92 | 19 (0.17) | −1.42 / −0.99 / −0.57 / +0.04 / +1.36 | 0.83 | 2.78 | −0.565 / −0.164 / +1.078 |
| 1–5% | 52 | 6 (0.10) | −1.93 / −1.27 / −0.76 / +0.06 / +0.78 | 0.86 | 2.71 | −2.881 / −0.800 / +2.837 |
| ≥ 5% | 56 | 1 (0.02) | −0.31 / −0.20 / −0.05 / +0.15 / +0.44 | 0.27 | 0.75 | −14.5 / −1.26 / +8.93 |

Below 0.1%, most parties do not stand again, so the continuing rows there are
survivors and their positive median is selection.

**Arrivals.** 352 on the panel, of which 314 entrants (38 are the registered
splits COPE, NFP, EFF, GOOD, ASA). Entrant share q5 / q25 / q50 / q75 / q95 =
0.014 / 0.034 / 0.063 / 0.148 / 0.803%, sd(log) 1.23. The spec's
`entrant_record` (304 rows: all metros, transitions before 2026, splits
excluded, rows without a measured ward reach skipped, §1.198) by reach:

| reach | n | share q5 / q50 / q95 % | mean % | sd(log) | W |
|---|---|---|---|---|---|
| 0–0.25 | 128 | 0.013 / 0.048 / 0.276 | 0.114 | 1.00 | 3.06 |
| 0.25–0.5 | 28 | 0.025 / 0.085 / 1.333 | 0.263 | 1.21 | 3.96 |
| 0.5–0.75 | 28 | 0.015 / 0.104 / 0.788 | 0.190 | 1.14 | 3.94 |
| 0.75–0.95 | 28 | 0.038 / 0.143 / 1.584 | 0.422 | 1.33 | 3.74 |
| 0.95–1 | 92 | 0.026 / 0.083 / 0.850 | 0.250 | 1.18 | 3.50 |

Entrant totals per city-year (24): q5 / q50 / q95 = 0.59 / 2.21 / 5.86%,
sd(log) 0.81. Entrants per city-year: median 11, max 34. Pre-2011 transition
(2000→2006, held back from the model, reported for completeness): continuing
log-ratio W 0.81–1.50 below 5%, entrant sd(log) 1.11.

## Q3. The draws

Per party: table in Q1 and finding 1. Units as in Q2, with the drawn list
share in place of the later share and the drawn median as the reference:

| population | drawn W (base) | W (nosplit) | ln(q95/q50) | ln(q50/q5) | P(share < 0.01%) |
|---|---|---|---|---|---|
| 44 generic entrants, centre 0.03–0.11% | 5.6–8.3 | 0.20 | 5.6–8.3 | ≈ 0 | 0.78–0.93 |
| All Citizens Party, centre 1.07% | 6.86 | 0.20 | 2.49 | 4.38 | 0.08 |
| SACP, centre 1.62% | 7.15 | 0.25 | 2.27 | 4.89 | 0.08 |
| group of 45 (sum) | 3.06 | 0.20 | 1.23 | 1.82 | — |

Everything except the split contributes W ≈ 0.20 (nosplit). The pool-stage
output (`draw_pools` target) and the final list share agree in the upper tail;
the target's W is larger (50–160) only because its q5 is closer to zero; that
the ward layer floors the list share near one vote is argued from the q5 of
0.0001%, not traced in code.

## Q4. Verdict by size bin

| bin | population | declared test (log width vs comparator CI) | seat probability | upper tail (q95) | group total | verdict |
|---|---|---|---|---|---|---|
| 0–0.05% and 0.05–0.1% | 43 generic entrants (+ Truth and Solidarity at 0.11%) | too wide, all | matches record × 0.22 | matches record × 0.22 | matches (slightly wide) | **too wide below the median, matching where seats are decided.** Adding a source is not supported: the shock run moves nothing measurable. The lower-tail excess is the split's shape. |
| 1–5% | SACP; All Citizens Party (by-election centre) | too wide (W 7.15 against band 3.46 and continuing record 2.71) | — | wider than record (2.27 against 1.54) | — | **too wide on both halves.** Adding a shock would widen it further. |

Occam, as the owner framed it: no new variation source for the 46. The
existing variation is not too narrow anywhere; where it misfits it is too wide,
and that is the within-pool split (one concentration per pool, member α =
m·A), which is already scheduled for reformulation. The SACP and All Citizens
Party are the owner's call: the first because its width is far beyond any
record, the second because its level comes from 198 by-election votes.

## Q5. Claims that a variation source runs for these parties, and the correction

The stated mechanism ("the arrival band carries their uncertainty") does not
run. What runs is the pool Dirichlet. Each place below states otherwise or
depends on the dead band. Correction under the Occam verdict: the records say
the split carries the width, the zero shock is registered as a judgement call
with this measurement, and **the dead band is deleted** (the triangular branch,
the `band[1]` multiplier, the emitted `seed_bands`, `ARRIVAL_BAND_LO/HI` and
their register rows). Deleting is chosen over labelling because a labelled
unread artefact is what survived two rounds of repair (§1.198). No forecast
number changes: `band[1]` is 1.0 and the branch is unreachable.

Cost class (CLAUDE.md §3): **free** = comment or record only, no hash move;
**suite** = `montecarlo.py` code, no re-emit; **re-emit** = `pools.py` code,
moves every spec hash, batched per `POOLS-REEMIT-QUEUE.md`.

| # | where | the claim | correction | cost |
|---|---|---|---|---|
| 1 | `src/montecarlo.py` ~2874–2884, `pool_sd_shock` | seeded arrivals get 0 "on the argument that … a t-shock on top would double-count the uncertainty the band already carries" | Comment: their width comes from the within-pool Dirichlet (α = m·A_pool), not the band; zero shock registered as JUDGEMENT-CALLS entry citing finding 4 (adding the size-line shock moves P(≥1 seat) 0.059 → 0.064). Code unchanged. | suite (comment) + free (register) |
| 2 | `src/montecarlo.py` ~2774–2786, `individual` loop | the `seed_band` triangular branch ("An arrival's band IS the estimate, so it keeps its triangular") | Unreachable while every seeded party is a pool member (`test_every_seeded_party_belongs_to_a_pool`). Delete it; a non-pooled seed then falls to the ordinary level path, and the existing pool-membership test keeps guarding it. | suite |
| 3 | `src/montecarlo.py` ~2036–2066, `blended_centres` | reads `band[1]` as a multiplier | `band[1]` is 1.0 by construction; read the seed directly and drop the band from this path. | suite; `tests/test_blended_centres.py` (lines ~175–989 build scenarios with `pool_seed_bands`) must change with it |
| 4 | `src/pools.py` ~5106–5112, entrant `seed_notes` | "Band x–y on the record, carried across as a RELATIVE width" (emitted into every spec and the run notes) | Drop the band clause; say the draw's width comes from the pool split. | re-emit |
| 5 | `src/pools.py` ~4938, declared-party note (SACP) | "the declaration sets the level, the record sets the width" | Same correction; the SACP's drawn W is 7.15 against its band's 3.46. | re-emit |
| 6 | `src/pools.py` ~4187–4191, `ARRIVAL_BAND_LO/HI` comment | "consumed in `montecarlo` as `low, _, high = seed_band`" | Delete the constants with the band. | re-emit (constants deleted) |
| 7 | `src/pools.py` ~5058–5066 | the band "could not do anything … because `pool_spec` balances both margins by IPF" | Superseded: the band is never read (§1.198). | free (comment) |
| 8 | `src/pools.py` ~4752, `arrival_rules` docstring | returns "the band on the whole thing" | Add: emitted, not drawn from. | free (docstring) |
| 9 | `JUDGEMENT-CALLS.md` §L2 | "The declaration sets the LEVEL; the record sets the WIDTH" | False: the pool Dirichlet sets the width whatever the band says. Retire it, citing finding 5. | free |
| 10 | `JUDGEMENT-CALLS.md` lines ~100, ~1474–1476, ~1590 (`ARRIVAL_BAND_LO/HI`) | "the triangular support of every seeded arrival", "consumed … as `low, _, high = seed_band`" | Delete with the constants. | free |
| 11 | `JUDGEMENT-CALLS.md` §L13 (SACP) | "How to check it … against the band the arrival record puts around the declared level" | Check against the drawn interval; the band draws nothing. | free |
| 12 | `JUDGEMENT-CALLS.md` (missing) | zero level shock for seeded arrivals, called "the owner's decision" in MODEL-LOG §1.198 and registered nowhere | New entry: value 0, why, finding 4 as evidence, how to check. | free |
| 13 | `MACHINERY.md` ~282–285 | "each draw applies a Student-t level shock, the correlated turnout copula and a within-pool Dirichlet" | Not to seeded arrivals: shock sd 0. (MACHINERY ~50–58 already describes the split correctly.) | free |
| 14 | `tests/test_levers_are_live.py:840` | `pool_seed_bands` in `RUNTIME_INJECTED` ("not a lever") | Delete the entry with the band. | suite (delete the entry with the band) |
| 15 | `tests/test_pool_conservation.py` (assert message) | "2026 has no roster" | Stale: the 2026 spec carries 46 seeds. | free (test message) |

## Rejected claims

| claim | evidence against |
|---|---|
| "The 46 have no variation" (reading of integrity F3's "no level shock") | Drawn W 5.6–8.3; the split gives them more spread in log terms than any comparator record. |
| "Their band carries the uncertainty" (`montecarlo.py` comment) | §1.198 measured the band unread; confirmed here: the seeded draws are the pool Dirichlet's (nosplit leaves W 0.20). |
| "A level shock is needed so the variation happens" | Shock variant: P(≥1 seat) 0.059 → 0.064, group seats mean 8.15 → 9.15, big-party seat means move ≤ 0.46. |
| "The sd(log) 1.7–2.3 in F3 measures their width" | sd(log) here is dominated by the mass near zero; the 90% interval puts q5 = q50 at about one vote. Reported as P(< 0.01%) instead. |
| "Any of the 46 has a Johannesburg 2021 or 2024 result" | None does, under canonical names; seven have results elsewhere (Q1 table). |

## Limits

- The ×0.22 conditioning of the record is the model's own group-budget
  judgement (JUDGEMENT-CALLS §L6). Against the raw record, the seat-level check
  says too narrow at the top (record 0.34 against drawn 0.06–0.09 at reach ≈ 1);
  that is the level question, not the width one.
- 2026's 45 entrants exceed the record's largest ballot (34).
- The shock and nosplit variants do not share the base's random stream once a
  draw changes, so differences under about 0.01 in probabilities are within
  draw noise (argued, not measured by repeat seeds).
