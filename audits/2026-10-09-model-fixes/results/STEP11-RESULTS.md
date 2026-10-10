# Step 11 results: the arm measurements (2026-10-10)

Measured quantities for every prediction in
`prereg/2026-10-10-model-correction-batch.md` (with amendments A1-A13), by the
pre-registered instrument. Each section gives the pre-registered statement in
brief, then the measurement. No prediction is scored here; scoring is a
separate step.

**Runs.** 301 processes, 0 failed, seven at once: ten arms (A, B0, B6, B8, B,
C, C16, D, D0, E) × (24 panel city-years at 1,000 draws + Johannesburg 2026 at
5,000 draws), rule A in A and B0 at the 24 city-years, and three extra
Johannesburg 2026 runs in E's tree. Seed 20261104 everywhere,
`PYTHONHASHSEED=0`. Builds, hashes and commands: `STEP11-RUNS.md` (6ee7429).
D0's panel runs were made as well; no prediction reads them.

**Where the numbers come from.** Raw outputs per run:
`data/arms/step11/<arm>/<label>/` (`meta.json`, `arrays.npz`, `result.json`
for panel runs, `trace/`). Every number below is in
`data/arms/step11/measures.json` (produced by `harness/analyse.py`), the spec
comparison in `data/arms/step11/spec_diff.json` (`harness/spec_diff.py`), the
turnout table in `data/arms/step11/turnout_B.json` (`harness/turnout_table.py`),
item 3 in `data/arms/step11/unopposed_<arm>.json` (`harness/unopposed.py`).
"Identical" below means every saved drawn array (PR and ward share draws, PR and
ward vote draws, seat draws, per-draw ward winners, pool turnout draws) equal
element for element, aligned by party name.

Units: shares and gaps in percentage points unless stated; seats are mean seats
over draws; list MAE (`pr_mae`) and ward MAE (`ward_mae`) are
`compare_history`'s, in points; coherent seat error is
`seat_abs_err_coherent`, in seats.

The real tree's `data/processed`, `site/`, `content/`, `publications/`,
`prereg/`, `src/`, `tests/` and `data/arms/A-specs-pre-batch/` have the same
sha256 listing after the runs as before them; no file under `data/raw` is newer
than the marker taken before the first emit; no `history.json` was written.

---

## E1-E4: the emitted specs (`spec_diff.json`)

Field-by-field comparison of every arm's 27 specs against arm A's copy of the
pre-batch specs.

- **E1 (B0).** 27 of 27 byte-identical to A's, `artefact_key` included.
- **E2 (B6, B8).** In both arms all 27 differ from A's in exactly one JSON
  path, `/artefact_key/deps_sha`.
- **E3 (B, C, C16, E).** The four arms give the same field list at every spec:
  - all 27: `artefact_key` (`cities_sha`, `deps_sha`, `pools_sha`; plus
    `judgements_sha` at `pools_2026.json` and `pools_2026_simulation.json`);
    `seed_bands` absent in all 27 (present in all 27 of A's);
  - the 8 2011 specs and `tshwane/pools_2026.json`: nothing else;
  - the 16 2016 and 2021 specs: `seed_notes`, 234 notes changed: 230 with the
    "Band x%-y% on the record …" sentence replaced by "The draw's width comes
    from the pool split." (matched by `spec_diff.band_deletion`), and 4 ASA
    splinter notes (ekurhuleni 2021, ethekwini 2021, joburg 2021, tshwane
    2021) whose "Band x%-y% from the … record." sentence is folded into
    "…, from the … record; the draw's width comes from the pool split." No
    other note content changed. No other field differs in these 16.
  - `pools_2026.json` and `pools_2026_simulation.json`: `seeds` (46 of 46
    changed), `seeded_arrival_mass` (0.034967 → 0.021867), `seed_notes` (46,
    band sentence and group-rescale text), `no_measured_vector` (SACP only),
    `pools`: the SACP's member weights (4 pools in `pools_2026.json`, 5 in the
    simulation spec), and other members' weights differing by at most
    1.1e-16 (29 parties) and 2.2e-16 (45 parties).
  - **The `seed_notes` count (window commit 2d73de7 said 18 specs, its writer's
    table 16).** From the specs: 18 specs carry a `seed_notes` change: the 16
    backtest 2016/2021 specs (8 metros × 2) and the 2 Johannesburg 2026 specs.
    No 2011 spec and not Tshwane 2026.
  - C's and C16's specs: 27 of 27 byte-identical to each other.
  - `group_share_record.json` `cities` content: one sha256 in B, C, C16 and E
    (`17a2639b1b6a84fd`, canonical JSON).
- **E4.** The 8 2011 specs in each of B, C, C16, E carry 0 seeds.
- E's 27 specs, `group_share_record.json` and `bye_value.json` are
  byte-identical to the window's (2d73de7) in the real tree.

## P10 (item 10): stale specs and refusals

- `02_pools_artefact.stale_reason` (trace) and `ModelRun.scenario["_pools_stale"]`:
  null in all 253 traced runs (25 per arm × 10 arms + 3 extras); `_pools_stale`
  null in the 48 rule-A runs. `allow_stale_pools` set in no run;
  `_pools_stale_allowed` false wherever the code records it.
- Refusals: none. Every run of every arm completed (0 failed of 301).
- A4: in B, C, C16 and E, `test_a_current_spec_is_not_refused`,
  `test_a_spec_with_a_moved_pools_sha_stops_the_run` and
  `test_a_staleness_check_that_raises_stops_the_run` passed (not skipped)
  after the emit (`STEP11-RUNS.md` §2).

## P1 (items 1, 2): ties at the cut

Tie classifier of §2 (`harness/arm_run.py`); one `allocate_with_overhang` call
per draw asserted in every run.

Draws in population 1, by class (a draw with any `allocate` call in the class):

| arm | 2026: pop. 1 | 2026: item 2 | 2026: lot | panel (24 summed): pop. 1 | panel: item 2 | panel: lot | largest lot share of draws in any run, % |
|---|---|---|---|---|---|---|---|
| A | 15 | 14 | 1 | 15 | 13 | 2 | 0.20 |
| B0 | 15 | 14 | 1 | 15 | 13 | 2 | 0.20 |
| B6 | 7 | 7 | 0 | 18 | 15 | 3 | 0.10 |
| B8 | 12 | 11 | 1 | 18 | 17 | 1 | 0.10 |
| B | 13 | 12 | 1 | 24 | 22 | 2 | 0.10 |
| C | 10 | 9 | 1 | 22 | 18 | 4 | 0.10 |
| C16 | 10 | 9 | 1 | 22 | 18 | 4 | 0.10 |
| D | 9 | 8 | 1 | 22 | 14 | 8 | 0.20 |
| D0 | 11 | 10 | 1 | 22 | 14 | 8 | 0.20 |
| E | 11 | 10 | 1 | 22 | 14 | 8 | 0.20 |

No draw in any run had both classes. The 2026 runs have 5,000 draws, each panel
run 1,000.

A against B0 (`measures.json` `P1_A_vs_B0`):
- Johannesburg 2026: population 1 is 15 draws in both arms (the same draws).
  Of the 4,985 draws in population 2 in both, 0 have a different seat vector.
  5 draws of population 1 have a different seat vector. PR and ward share
  draws, PR and ward vote draws and per-draw ward winners: identical.
- Panel: at all 24 city-years, 0 population-2 draws with a different seat
  vector; share, vote and ward-winner arrays identical at all 24. Seat vectors
  differ in 3 population-1 draws (ekurhuleni 2021, ethekwini 2021, capetown
  2011, one each). Population 1 is non-empty at 9 city-years in A, 15 draws
  in all (joburg 2021 1, tshwane 2011 1, ekurhuleni 2021 2, ethekwini 2016 1,
  ethekwini 2021 3, capetown 2011 2, mangaung 2011 1, mangaung 2021 2,
  buffalocity 2021 2).

## P2 (items 1, 2): rule A, A against B0

Each arm's own `rule_a.py`, unchanged; its seat call classified by the same
instrument (`measures.json` `P2_rule_a`).

- Tied wards (`tied_wards`): 0 at all 24 city-years in A and in B0.
- Rule A's seats and ward wins: identical between A and B0 at all 24.
- Rule A's seat call meets a tie at one city-year, Johannesburg 2016, in both
  arms: class lot, AIC and TRULY_ALLIANCE, 3,743 votes each, whole-vote
  surplus 3,743, shortfall 11. A (name order) and B0 (seeded lot) seat the
  same allocation. Rule A seat error at Johannesburg 2016: 28 in A, 28 in B0
  (difference 0). Every other city-year's rule-A seat call is untied.
- Rule A seat error summed over the 24: 737 in A, 737 in B0.
- **P2b.** `uniform-swing+roster`'s `seat_abs_err_coherent` summed over the 24
  city-years: 837 in B0 (837 in A).

## P3 (item 3): unopposed wards

`levels.unopposed_wards` in B's, C's, C16's and E's trees at the 24 runnable
targets and Johannesburg 2026: `{}` at all 25 in all four. No run refused.

## P6 (item 6): B6 against A, and CHANGE

`measures.json` `P6_B6_vs_A_2026`, `P6_B6_vs_A_panel`, `P6_B_vs_A_*`, `P6_CHANGE`.

**Implementation check (A8; not a prediction):** B6 at Johannesburg 2026: PA
mean seats 16.92 (stated 16.85 ± 0.5); PA mean gap (list − ward) −0.188 points
(stated −0.19 ± 0.1).

Johannesburg 2026, A → B6:

| line | quantity | A | B6 | pre-registered |
|---|---|---|---|---|
| F1 | PA ward/PR ratio (`ModelRun.ratio`) | 2.000 | 1.029 | 2.000 → 1.029 |
| F2 | PA mean gap, points | −5.53 | −0.19 | in [−0.6, +0.2] |
| F2 | share of draws with PA gap ≤ −1.76 | 99.9% | 0.0% (range of draws −1.13 to +0.48) | at most 1% |
| F3 | DA mean gap | +0.19 | −1.36 | [−1.8, −1.1] |
| F3 | ANC mean gap | +0.83 | −0.49 | [−0.8, −0.3] |
| F3 | EFF mean gap | −0.34 | −0.99 | [−1.2, −0.8] |
| F3 | ASA mean gap | +3.27 | +2.67 | [+2.5, +3.0] |
| F3 | MK mean gap | +0.98 | +0.46 | [+0.2, +0.6] |
| F3 | DA draws with gap ≤ −1.76 | 0.06% | 17.9% | expected above 1% |
| F4 | PA mean seats | 24.02 | 16.92 | [16.0, 18.5] |
| F4 | PA mean ward wins | 10.54 | 5.07 | [4.5, 6.5] |
| F5 | DA mean seats change | | +2.01 | +1.0 to +3.0 |
| F5 | ANC mean seats change | | +1.94 | +1.0 to +3.0 |
| F5 | largest other change (not PA) | | EFF +0.85 | under 1.5 |
| F6 | PR share draws | | identical (PR vote draws and pool turnout draws identical too) | identical |

Panel (24 city-years), A → B6:
- **B1.** PR share draws identical at 24 of 24; `pr_mae` equal at 24 of 24.
- **B2.** Panel-mean ward MAE 2.9905 → 2.9014 (−0.0891). The named
  city-years: ekurhuleni 2021 +0.0146, nelsonmandelabay 2021 −0.0299, joburg
  2021 +0.1541, buffalocity 2016 −0.0136, mangaung 2021 −0.0732. City-years
  worsening by more than 0.15: ethekwini 2016 +0.4248, capetown 2021 +0.2499,
  ethekwini 2021 +0.1762, joburg 2021 +0.1541 (largest rise 0.4248).
- **B3.** Coherent seat error summed: 735 → 721 (−14).
- **B4.** Ward winner accuracy (`result["wards"]`), summed over the 24: 2,120
  of 2,191 wards called right in A, 2,115 in B6; ward-weighted multicategory
  Brier 0.0537 in A, 0.0540 in B6.

Reported on B against A, not scored (items 8 and 18 move the same draws): F2
PA mean gap −0.19 (0.0% of draws ≤ −1.76); F4 PA 17.07 seats, 5.04 ward wins;
F5 DA +2.62, ANC +2.18 (largest other: SACP −3.30). Panel: ward MAE mean
−0.0180, coherent 735 → 725.

**CHANGE** (B, C, C16, D, E at Johannesburg 2026): not listed in the declared
ward slates (`[roster.wards]`, 80 parties listed); slate coverage now 0.0
(previous 0.994); ward/PR ratio 0.0; ward share between 9.4e-7 and 1.24e-6 in
every draw of every arm (0 draws at or above 1e-5); 0 ward wins.

## P8 (item 8): B8 against A

`measures.json` `P8_*`.

- **The four city-years** (buffalocity 2011, buffalocity 2021, ethekwini 2016,
  mangaung 2011): B8 identical to A at all four.
- **Panel-mean list MAE:** A 3.1599, B8 3.2352, B8 − A = +0.0754.
- **The three city-years over 1%:** ekurhuleni 2011 3.551 → 4.491 (+0.940);
  mangaung 2021 1.765 → 2.376 (+0.611); nelsonmandelabay 2021 2.814 → 2.844
  (+0.029).
- Per city-year list MAE / coherent seat change, B8 − A: joburg 2011
  +0.651/+6, joburg 2016 −0.361/−2, joburg 2021 −0.086/0, tshwane 2011
  +0.478/+4, tshwane 2016 +0.025/+2, tshwane 2021 −0.030/0, ekurhuleni 2011
  +0.940/+6, ekurhuleni 2016 −0.352/−4, ekurhuleni 2021 −0.046/−2, ethekwini
  2011 +0.466/+4, ethekwini 2016 0/0, ethekwini 2021 −0.048/−2, capetown 2011
  −0.155/−2, capetown 2016 +0.441/0, capetown 2021 −0.390/−6, mangaung 2011
  0/0, mangaung 2016 −0.115/−2, mangaung 2021 +0.611/+2, nelsonmandelabay
  2011 +0.225/+2, nelsonmandelabay 2016 −0.348/−2, nelsonmandelabay 2021
  +0.029/−2, buffalocity 2011 0/0, buffalocity 2016 −0.125/0, buffalocity
  2021 0/0.
- **Coherent seat error summed:** 735 → 737 (+2).
- **`41_guards.roster_unrepresented`:** in B8, B, C, C16, D, D0 and E, equal
  party for party to §1.1's lists at the seven 2011 city-years (capetown 15,
  ekurhuleni 8, ethekwini 7, joburg 7, tshwane 4, nelsonmandelabay 3,
  mangaung 2), `[]` at the other 17 and at Johannesburg 2026; never
  `"not_checked"`.
- **Johannesburg 2026, the seven** (B8): together mean list share 0.415%; each
  (%): AMALGAMATED_RAINBOW_MOVEMENT 0.033, CHANGE 0.043,
  ECONOMIC_EMANCIPATION_FORUM 0.039, INTERNATIONAL_REVELATION_CONGRESS 0.105,
  SHOSHOLOZA_PROGRESSIVE_PARTY 0.021, THE_ORGANIC_HUMANITY_MOVEMENT 0.047,
  UIM 0.127; together 0 or 1 seat in 84.3% of draws (mean 0.94 seats). None is
  in A's universe. Same quantities in the other arms: B 0.414%, 83.4%; C and
  C16 0.374%, 83.7%; D 0.426%, 82.4%; E 0.446%, 81.4%.

## P11 (item 11a): C against B

- Johannesburg 2026, mean seats B → C: PA 17.07 → 16.29 (−0.78); DA 69.08 →
  69.59 (+0.51); ANC 65.92 → 65.59 (−0.33). Largest other moves: EFF +0.98,
  ASA −0.26, MK −0.14, BOSA −0.12, ACDP +0.11, ATM +0.11; every other party
  under 0.1.
- Panel, list MAE C − B per city-year: largest |change| 0.603 (mangaung 2021,
  −0.603); others over 0.3: mangaung 2011 −0.472, capetown 2016 +0.344,
  capetown 2011 +0.321. City-years with |change| ≥ 0.05: 18 of 24 (full list
  in `measures.json` `P11_panel`). Panel mean −0.0115.
- Coherent seat error summed: 725 → 723 (−2).

## P16 (item 16): C16 against C

- Windows (`20_spine.size_window` in C16's traces), h = inf for θ and ρ at
  all 24 panel targets and at Johannesburg 2026. Status, best, scored,
  clusters by target year (the same at every city of a year):

  | target | θ | ρ |
  |---|---|---|
  | 2011 | underdetermined, —, 83, 1 | underdetermined, —, 0, 0 |
  | 2016 | derived, inf, 168, 2 | underdetermined, —, 74, 1 |
  | 2021 | derived, 2.0, 265, 3 | derived, 0.25, 165, 2 |
  | 2026 | derived, 1.5, 403, 4 | derived, 0.5, 283, 3 |

- C16 identical to C at all 24 city-years and at Johannesburg 2026 (the PA
  moves 0 seats).

## P17 (item 17): D against C16

- Johannesburg 2026, mean seats C16 → D: MK 25.08 → 23.68 (−1.40); ASA
  29.42 → 28.98 (−0.43); BOSA +0.27; RISE +0.20; GOOD is not in either arm's 2026 universe (no seats in
  either); AHC +0.01; ANC 65.59 → 66.74 (+1.14); DA 69.59 → 69.61
  (+0.02); EFF 28.93 → 28.09 (−0.84). Spine level rises under item 17 for 86
  parties at 2026 (`20_spine.level`, D against C16; seeded parties included);
  apart from the named ones the largest seat gain among them is DUDULA +0.12
  (same among the 38 unseeded). IFP +0.19 (not a spine-level riser).
- The seven (A1): in C16 all seven are in
  `41_guards.level_sd_default_parties`; in D `41_guards.level_sd_at_size`:
  SHOSHOLOZA_PROGRESSIVE_PARTY 0.6738, AMALGAMATED_RAINBOW_MOVEMENT 0.5989,
  ECONOMIC_EMANCIPATION_FORUM 0.5569, CHANGE 0.5554,
  THE_ORGANIC_HUMANITY_MOVEMENT 0.5413, INTERNATIONAL_REVELATION_CONGRESS
  0.4575, UIM 0.4231 (A1's values: 0.674, 0.599, 0.557, 0.555, 0.541, 0.457,
  0.423). Together 0 or 1 seat in 82.4% of D's draws.
- Panel-mean list MAE: C16 3.2237, D 3.2572, D − C16 = +0.0336. Coherent seat
  error summed: 723 → 727 (+4). Per city-year in `measures.json`
  `P17_panel`.

## P13 (item 18): the SACP, B against A

| quantity (Johannesburg 2026) | A | B |
|---|---|---|
| seed in the arm's own `pools_2026.json` | 0.01310 | 0.000621 |
| `30_centres.before_shrink` | 0.01310 | 0.000621 (equal to the seed) |
| `30_centres.after_shrink` | 0.01622 | 0.000838 |
| mean list share, % | 1.399 | 0.074 |
| mean seats | 3.486 | 0.184 |
| P(at least one seat) | 0.693 | 0.063 |

- Generic entrants' seeds (45 parties whose B note starts "entrant from
  nothing", SACP excluded), B against A: every one −2.838% (relative).
- Reported only: ANC +2.18 and DA +2.62 mean seats, B against A.

## P12 (item 12): the group-share tripwire

- E's tree, Johannesburg 2026, with `group_share_record.json` moved aside:
  identical to E's run with it present (every drawn array, and
  `30_centres` before and after the shrink); `41_guards.group_share_tripwire`
  = `"no record"`.
- Every run of B, C, C16, D, D0 and E at 2016, 2021 and Johannesburg 2026 (17
  per arm; the record covers 2016, 2021 and 2026 for all eight cities)
  reports a count with `population` = `scanned` and `key_current` true. The
  2011 runs report `"no record"` (2011 is not in the record).
- **`PA|Coloured` at Johannesburg 2026 is among the firing pairs in every
  arm**, with threshold 0.8123 and `fire_at` 0.05: share of draws above the
  threshold B 67.9% (3,393), C 61.1% (3,054), C16 61.1%, D 60.7% (3,034), D0
  and E 47.9% (2,397). It is the only firing pair at 2026 in each arm.
- Firing pairs per panel run (B): 2016 runs 19-89 pairs each, 2021 runs 0-2.
  Per run and arm in `measures.json` `P12_tripwire`.

## P19 (item 19): E against D0 and D

- E's derived class weights (`30_centres.bye_weight`): under 0.0, at_or_over
  0.0 (`w_bye` not set). D0: override 0.0; D: override 0.4.
- **E against D0, Johannesburg 2026:** identical on every drawn array and on
  `30_centres` before and after the shrink.
- **E against D on the panel:** identical at 24 of 24.
- **Inertness in E at 2026:** `--set bye_weight_mode=inverse_variance` and
  `montecarlo.BYE_MIN_WEIGHT = 1.0` (from 30.0) each give a run identical to
  E's on every drawn array and on `30_centres`. Delivery: the
  inverse-variance run's scenario and `01_scenario_in` carry
  `bye_weight_mode: "inverse_variance"` (E's: `"fixed"`); the key has no entry
  in `45_delivered` in any of the three runs. `45_delivered` records
  `montecarlo.BYE_MIN_WEIGHT` read once at `montecarlo:run_model` with value
  1.0 in the modified run and 30.0 in E's and in the inverse-variance run.
- A5, Johannesburg 2026:

  | quantity | E | D |
  |---|---|---|
  | All Citizens Party seed in E's `pools_2026.json` | 0.000353 | |
  | ACP `30_centres.before_shrink` | 0.000353 (equal to the seed) | 0.008412 |
  | ACP `30_centres.after_shrink` | 0.000478 | 0.010708 |
  | ACP mean seats | 0.102 | 2.325 |
  | Truth and Solidarity seed in E's spec | 0.000623 | |
  | T&S `30_centres.before_shrink` | 0.000623 (equal to the seed) | 0.000814 |
  | T&S `30_centres.after_shrink` | 0.000840 | 0.001095 |
  | T&S mean seats | 0.184 | 0.250 |

- Direction, mean seats E − D: PA 16.31 → 15.20 (−1.11); DA 69.61 → 69.27
  (−0.35); ANC 66.74 → 69.38 (+2.64). (MK −0.18.)

## SPEC §1.9: the turnout bands, arm B

Drawn: `pool_turnout_draws` from arm B's runs, q5–q95, %. Citywide per draw:
the registration-weighted mean of the pool draws, weights = each pool's
`registered` in the run's own spec (`pools.turnout_limits`' definition).
Observed: `pools.turnout_record(city, cfg, before="2022", kind="LGE")`, min–max
over the city's LGEs listed (2000-2021 as the calendar carries them; Johannesburg
from 2000, the others from 2006); observed citywide uses the target spec's
registration weights, so it differs slightly between a city's rows. At
Johannesburg 2026 the observed columns equal the spec's own
`turnout_limits.observed_*`. Each cell: drawn q5–q95 / observed min–max.

| city-year | observed LGEs | Black African | Coloured | Indian/Asian | White | citywide |
|---|---|---|---|---|---|---|
| joburg-2026 | 2000, 2006, 2011, 2016, 2021 | 27.5–47.2 / 35.2–50.8 | 33.4–72.7 / 33.0–64.8 | 20.1–71.5 / 16.0–58.5 | 38.2–66.7 / 48.5–69.5 | 31.9–53.1 / 38.8–56.4 |
| joburg-2011 | 2000, 2006, 2011, 2016, 2021 | 28.9–48.9 / 35.2–50.8 | 27.7–47.6 / 33.0–64.8 | 19.7–36.2 / 16.0–58.5 | 38.0–58.9 / 48.5–69.5 | 31.7–49.8 / 38.7–56.0 |
| joburg-2016 | 2000, 2006, 2011, 2016, 2021 | 39.6–61.2 / 35.2–50.8 | 36.4–77.0 / 33.0–64.8 | 25.3–68.5 / 16.0–58.5 | 51.8–74.2 / 48.5–69.5 | 43.2–64.3 / 38.5–56.1 |
| joburg-2021 | 2000, 2006, 2011, 2016, 2021 | 39.4–60.6 / 35.2–50.8 | 41.7–79.7 / 33.0–64.8 | 27.7–79.3 / 16.0–58.5 | 54.6–79.3 / 48.5–69.5 | 44.2–65.3 / 38.8–56.3 |
| tshwane-2011 | 2006, 2011, 2016, 2021 | 27.7–48.2 / 37.1–51.6 | 11.3–22.9 / 15.4–54.7 | 14.1–28.2 / 14.1–63.3 | 41.1–61.4 / 51.2–74.4 | 32.0–50.4 / 40.5–58.2 |
| tshwane-2016 | 2006, 2011, 2016, 2021 | 40.7–59.0 / 37.1–51.6 | 25.4–65.0 / 15.4–54.7 | 8.8–26.0 / 14.1–63.3 | 56.8–77.4 / 51.2–74.4 | 45.5–63.5 / 40.7–58.5 |
| tshwane-2021 | 2006, 2011, 2016, 2021 | 42.0–60.9 / 37.1–51.6 | 26.8–78.2 / 15.4–54.7 | 29.0–82.2 / 14.1–63.3 | 58.0–83.9 / 51.2–74.4 | 47.9–67.4 / 40.7–58.7 |
| ekurhuleni-2011 | 2006, 2011, 2016, 2021 | 31.6–51.4 / 36.7–52.6 | 29.1–48.8 / 38.0–65.1 | 17.9–33.6 / 24.2–56.6 | 42.9–64.1 / 54.1–74.0 | 33.7–52.0 / 41.7–56.1 |
| ekurhuleni-2016 | 2006, 2011, 2016, 2021 | 43.9–61.5 / 36.7–52.6 | 32.5–74.1 / 38.0–65.1 | 31.2–63.3 / 24.2–56.6 | 56.2–76.3 / 54.1–74.0 | 46.8–63.9 / 41.8–56.3 |
| ekurhuleni-2021 | 2006, 2011, 2016, 2021 | 42.9–59.3 / 36.7–52.6 | 44.7–79.3 / 38.0–65.1 | 33.9–75.9 / 24.2–56.6 | 60.3–82.7 / 54.1–74.0 | 47.8–64.6 / 42.3–56.7 |
| ethekwini-2011 | 2006, 2011, 2016, 2021 | 34.3–55.5 / 37.1–60.1 | 20.7–38.4 / 27.9–54.4 | 28.9–49.1 / 37.9–57.8 | 39.0–60.8 / 49.7–66.9 | 34.5–53.4 / 40.6–58.5 |
| ethekwini-2016 | 2006, 2011, 2016, 2021 | 49.0–69.3 / 37.1–60.1 | 31.9–73.5 / 27.9–54.4 | 34.2–67.2 / 37.9–57.8 | 50.6–73.0 / 49.7–66.9 | 47.4–67.9 / 40.6–58.6 |
| ethekwini-2021 | 2006, 2011, 2016, 2021 | 45.8–66.0 / 37.1–60.1 | 35.5–70.6 / 27.9–54.4 | 40.1–72.2 / 37.9–57.8 | 55.6–75.7 / 49.7–66.9 | 46.6–67.2 / 40.6–58.6 |
| capetown-2011 | 2006, 2011, 2016, 2021 | 37.5–58.3 / 32.3–59.7 | 31.5–52.1 / 40.9–63.5 | 43.9–64.9 / 52.9–67.1 | 54.1–73.7 / 63.5–77.3 | 40.6–58.2 / 45.5–63.7 |
| capetown-2016 | 2006, 2011, 2016, 2021 | 50.0–67.6 / 32.3–59.7 | 37.7–78.0 / 40.9–63.5 | 49.2–79.1 / 52.9–67.1 | 63.1–81.6 / 63.5–77.3 | 49.6–73.2 / 46.0–64.0 |
| capetown-2021 | 2006, 2011, 2016, 2021 | 43.9–61.2 / 32.3–59.7 | 43.0–78.1 / 40.9–63.5 | 47.7–78.3 / 52.9–67.1 | 67.3–83.7 / 63.5–77.3 | 50.5–72.7 / 46.2–64.2 |
| mangaung-2011 | 2006, 2011, 2016, 2021 | 33.7–54.8 / 38.0–53.2 | 18.2–34.7 / 24.8–57.5 | 33.8–54.7 / 42.9–56.0 | 36.1–57.4 / 46.4–65.8 | 34.1–53.9 / 42.2–55.7 |
| mangaung-2016 | 2006, 2011, 2016, 2021 | 42.8–60.0 / 38.0–53.2 | 32.9–74.3 / 24.8–57.5 | 36.8–69.6 / 42.9–56.0 | 51.9–74.3 / 46.4–65.8 | 45.2–62.3 / 42.6–55.9 |
| mangaung-2021 | 2006, 2011, 2016, 2021 | 44.6–61.5 / 38.0–53.2 | 34.3–74.5 / 24.8–57.5 | 39.2–69.9 / 42.9–56.0 | 52.1–75.0 / 46.4–65.8 | 47.0–63.7 / 42.8–56.0 |
| nelsonmandelabay-2011 | 2006, 2011, 2016, 2021 | 50.2–71.0 / 40.5–61.7 | 30.8–52.4 / 40.7–64.2 | 34.3–55.6 / 44.3–81.5 | 41.8–64.0 / 52.7–72.9 | 45.8–64.2 / 44.5–63.9 |
| nelsonmandelabay-2016 | 2006, 2011, 2016, 2021 | 52.4–69.8 / 40.5–61.7 | 38.8–79.8 / 40.7–64.2 | 52.0–83.4 / 44.3–81.5 | 56.7–77.3 / 52.7–72.9 | 52.2–72.4 / 44.8–64.1 |
| nelsonmandelabay-2021 | 2006, 2011, 2016, 2021 | 48.2–64.3 / 40.5–61.7 | 43.0–78.2 / 40.7–64.2 | 53.6–90.2 / 44.3–81.5 | 58.4–81.7 / 52.7–72.9 | 51.4–70.7 / 45.2–64.3 |
| buffalocity-2011 | 2006, 2011, 2016, 2021 | 42.7–64.1 / 43.5–54.4 | 2.2–5.2 / 3.2–61.9 | 3.3–7.5 / 4.6–55.2 | 55.5–74.9 / 52.8–73.2 | 41.2–60.6 / 43.9–55.0 |
| buffalocity-2016 | 2006, 2011, 2016, 2021 | 45.1–62.7 / 43.5–54.4 | 18.8–82.9 / 3.2–61.9 | 20.7–83.4 / 4.6–55.2 | 52.2–73.5 / 52.8–73.2 | 45.7–64.5 / 44.4–55.5 |
| buffalocity-2021 | 2006, 2011, 2016, 2021 | 43.8–60.2 / 43.5–54.4 | 20.9–85.7 / 3.2–61.9 | 10.3–69.5 / 4.6–55.2 | 63.0–80.5 / 52.8–73.2 | 45.6–62.8 / 44.4–55.6 |

The observed range for a panel row includes LGEs after that target (the SPEC
asks for 2000-2021 at every row); the model's own band at a panel target was
built from LGEs before it.

## Panel totals per arm (all 24 city-years, from `measures.json` `panel_scores`)

| arm | list MAE, panel mean | ward MAE, panel mean | coherent seat error, sum |
|---|---|---|---|
| A | 3.1599 | 2.9905 | 735 |
| B0 | 3.1599 | 2.9905 | 735 |
| B6 | 3.1599 | 2.9014 | 721 |
| B8 | 3.2352 | 3.0204 | 737 |
| B | 3.2352 | 2.9726 | 725 |
| C | 3.2237 | 2.9582 | 723 |
| C16 | 3.2237 | 2.9582 | 723 |
| D | 3.2572 | 2.9782 | 727 |
| D0 | 3.2572 | 2.9782 | 727 |
| E | 3.2572 | 2.9782 | 727 |

## What the pre-registration did not anticipate

- **B6's recipe** reproduces the stated hash only with one trailing blank line
  kept in `levels.py` (`STEP11-RUNS.md` §1).
- **C16's recipe** fails `git apply --check` (the A13 test) at W and equally
  at acbd9f8, where it was written; it is a 3-way application with the
  conflict §3.3 resolves (`STEP11-RUNS.md` §1). The arm was built and run.
- **`PA|Coloured` fires at Johannesburg 2026** in B, C, C16, D and E (P12),
  in 48-68% of draws against `fire_at` 0.05.
- **The 2011 runs report `"no record"`** for the tripwire: the record covers
  2016, 2021 and 2026 only. P12's "every run … at a city-year the record
  covers" is therefore 17 runs per arm.
- **B, C and C16 hold no `bye_value.json`** (their `w_bye=0.4` skips it); three
  `-k chain` tests that run Johannesburg 2026 without an override refuse there
  (`STEP11-RUNS.md` §2). No arm run was affected.
