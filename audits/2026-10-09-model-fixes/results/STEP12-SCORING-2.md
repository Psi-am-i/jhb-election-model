# Step 12 scoring, scorer 2 (2026-10-10)

Scored against `prereg/2026-10-10-model-correction-batch.md` §4 with amendments
A1-A13, on the raw outputs of step 11 (`data/arms/step11/`, the arm trees under
the step 11 session's scratch directory). Brief:
`reviews/STEP12-SCORING-BRIEF.md` (c4cd8b1). Written without seeing scorer 1.

## How the numbers were obtained

Re-derivation scripts are in this session's scratch directory
(`scratchpad/scoring-2/`: `lib.py`, `scores.py`, `ident.py`, `panel.py`,
`y2026.py`, `rest.py`, `specs.py`, `boot.py`). Nothing was read from
`STEP11-RESULTS.md` or `measures.json`.

**Re-derived from the raw arrays (`arrays.npz`, aligned by party name through
`meta.json`):**
- Every "identical" verdict: all saved arrays (PR and ward share draws, PR and
  ward vote draws, seat draws, per-draw ward winners mapped to party names,
  ward-winner counts, pool turnout draws, council sizes, thresholds), element
  for element, universes compared as sets.
- `pr_mae`, `ward_mae` and `seat_abs_err_coherent` for all 240 panel runs (10
  arms × 24 city-years), recomputed from `pr_share_draws`, `ward_share_draws`
  and `seat_draws` with the actual results from the real tree's
  `compare_history.actual_shares` / `_actual_seats` and its `coherent_seats` /
  `seat_abs_err` (read-only import), ENTRANT relabelled as `relabel_run` does.
  All 240 equal each run's own `result.json` exactly (0 mismatches). Every
  panel aggregate below is mine.
- Mean seats, mean list shares, per-draw gaps (list − ward, 100 × (PR share −
  ward share)), ward wins, the seven item-8 parties' shares and seat
  distribution, CHANGE's ward share, the SACP's seats.
- P1's population counts and the A-against-B0 comparison, from the saved
  per-draw `tie_class_per_draw` array.
- E1-E4: a field-by-field diff of every arm's 27 specs (in each arm tree's
  `data/processed`) against `data/arms/A-specs-pre-batch/`.
- The arm tree hashes (prereg's command) and the committed arm diffs' sha256:
  equal to `STEP11-RUNS.md` §1 for all eight trees and five diffs.

**Read directly from the raw traces (a run's own record, not recomputable from
the arrays):** `02_pools_artefact.stale_reason` (253 traces) and
`meta.pools_stale` (301 runs); `20_spine.size_window`; `20_spine.level`;
`30_centres`; `41_guards` (`roster_unrepresented`,
`level_sd_default_parties`, `level_sd_at_size`, `group_share_tripwire` — the
within-pool split arrays it counts are not saved); `45_delivered`.

**Taken as given:**
- The tie class of each `allocate` call (the instrument's output; the arrays do
  not carry each call's `combined`), including rule A's seat-call class at
  Johannesburg 2016 (`rule_a-joburg-2016/meta.json`). Rule A's tied wards
  (top two `ward_winner_counts` equal, from each `rule_a-*/arrays.npz`) and
  its seat error (`seat_abs_err` of `rule_a.json["A"]["seats"]` against
  `_actual_seats`) are re-derived: 0 tied wards in all 48 rule-A runs; seat
  error equal to `rule_a.json` at 48 of 48.
- P3: `data/arms/step11/unopposed_{B,C,C16,E}.json` (the harness's output; I
  did not re-call `levels.unopposed_wards`).
- A4's three `test_stage_inputs` results and the `-k chain` results
  (`STEP11-RUNS.md` §2; tests not re-run).
- Ward-winner accuracy and Brier for B4 (`result.json["wards"]`) and the
  `uniform-swing+roster` coherent error for P2b
  (`result.json["opponents"]`).

Draw counts: every panel run 1,000 draws, every Johannesburg 2026 run 5,000,
seed 20261104 in all 301 runs (`meta.seed`). Units: shares and gaps in
percentage points; seats are mean seats over draws.

---

## Verdict table

"A3" marks a line A3 says was known before writing: scored, not counted as a
confirmed prediction. "RD" = re-derived by me; "TR" = read from a raw trace;
"G" = taken as given.

| prediction / clause | verdict | deciding number (arm, run) | source | how |
|---|---|---|---|---|
| **E1** B0 specs byte-identical to A's | held (A3) | 27 of 27 byte-identical | arm specs vs `A-specs-pre-batch` | RD |
| **E2** B6, B8 differ only in `artefact_key.deps_sha` | held | 27 of 27 in each arm differ in that one path only | same | RD |
| **E3** B, C, C16, E: only the exempt fields differ | held | 2011 specs and Tshwane 2026: key + `seed_bands` only; 16 backtest 2016/2021 specs: key, `seed_bands`, `seed_notes` (every changed note is a band-sentence deletion; 0 others); 2 Johannesburg 2026 specs: key incl. `judgements_sha`, `seeds` (46), `seed_notes`, `seeded_arrival_mass` (0.034967 → 0.021867), `no_measured_vector` (SACP only), `pools` (SACP weights in 4 pools / 5 in the simulation spec; other members ≤ 1.1e-16 and ≤ 2.2e-16) — see the note under the table; C and C16 specs 27/27 byte-identical; `group_share_record.json` `cities` one sha256 (`17a2639b1b6a84fd`) in B, C, C16, E | same | RD |
| **E4** 2011 specs carry no seeds | held | 0 seeds in all 8 2011 specs, every arm | same | RD |
| **P10** clause 1, `stale_reason` null (and A4's first bullet) | held | 0 non-null of 253 traces; `meta.pools_stale` null in 301 of 301 runs | `02_pools_artefact.json`, `meta.json` | TR |
| **P10** clause 2, no run of B-E refuses | held | every run of every arm has arrays and meta (0 failed) | run directories | RD |
| **P10/A4** three `test_stage_inputs` tests pass in B, C, C16, E | held | passed, not skipped | `STEP11-RUNS.md` §2 | G |
| **P10** clause 3 (draws not moved by item 10) | not scored (argued, per §4) | — | — | — |
| **P1** population 2 identity, A vs B0, 2026 | held | pop. 1 = 15 draws in both arms, the same draws; 0 of 4,985 pop.-2 draws with a different seat vector; all share, vote, ward-winner, turnout arrays identical in all 5,000 draws | `arrays.npz` | RD |
| **P1** population 2 identity, A vs B0, panel | held | 0 pop.-2 draws with a different seat vector at 24 of 24; all non-seat arrays identical at 24 of 24 | same | RD |
| **P1** pop. 1 > 0 in A at 2026 | held (A3 for class item 2) | 15 draws (14 item 2, 1 lot) | `tie_class_per_draw` | RD (class G) |
| **P1** class lot < 2% in every arm | held | largest lot share in any single run, any arm: 0.20% (A, B0, D, D0, E); arm aggregates ≤ 0.031% | same | RD (class G) |
| **P2** tied wards 0 at 24 in A and B0 | held | 0 and 0 (from `ward_winner_counts`; `rule_a.json` `tied_wards` empty too) | `rule_a-*/arrays.npz` | RD |
| **P2** rule A differs only where it meets a tie | held | rule A's seats and ward wins identical A vs B0 at 24 of 24 | `rule_a.json` | RD from G files |
| **P2** Johannesburg 2016 tie; seat error differs by 0 or 2 | held (A3) | seat call class lot, AIC/TRULY_ALLIANCE 3,743 votes each (G); seat error 28 in A, 28 in B0, difference 0 (RD); summed over 24: 737 and 737 | `rule_a-joburg-2016/meta.json`, `rule_a.json` | G/RD |
| **P2b** `uniform-swing+roster` panel total in [837, 841] under B0 | held | 837 (A also 837) | `result.json` `opponents` | G (sum mine) |
| **P3** `unopposed_wards` = `{}` at 25 targets in B-E; no refusal | held | `{}` at 25 of 25 in B, C, C16, E; no run failed | `unopposed_*.json` | G |
| **P4, P5, P9** | not scored (per §4) | — | — | — |
| **P6** implementation check (A8; not a prediction) | within both intervals | B6 2026: PA 16.921 seats (16.85 ± 0.5); PA mean gap −0.188 (−0.19 ± 0.1) | `arrays.npz` | RD |
| **P6 F1** PA ratio 2.000 → 1.029 | held (A3) | A 2.0; B6 1.02929 | `meta.ward_pr_ratio` | TR |
| **P6 F2** PA mean gap in [−0.6, +0.2]; ≤ 1% of draws at or below −1.76 | held (A3) | A −5.527 → B6 −0.188; 0.00% of draws ≤ −1.76 (range −1.13 to +0.48) | `arrays.npz` | RD |
| **P6 F3** DA, ANC, EFF, ASA, MK mean gaps in their ranges | held (A3) | DA −1.365 [−1.8, −1.1]; ANC −0.487 [−0.8, −0.3]; EFF −0.987 [−1.2, −0.8]; ASA +2.670 [+2.5, +3.0]; MK +0.455 [+0.2, +0.6]; all inside [−1.76, +6.16]; DA ≤ −1.76 in 17.86% of draws (the file expected above 1%) | same | RD |
| **P6 F4** PA seats [16.0, 18.5], ward wins [4.5, 6.5] | held (A3) | 16.921 seats; 5.069 ward wins | same | RD |
| **P6 F5** DA and ANC +1.0 to +3.0; no other party but the PA > 1.5 | held (A3) | DA +2.008, ANC +1.943; largest other EFF +0.853 | same | RD |
| **P6 F6** PR share draws identical | held (A3) | identical at 2026 (PR votes and pool turnout too) | same | RD |
| **P6 B1** `pr_mae` identical at every city-year | held (A3) | PR share draws identical at 24 of 24; `pr_mae` equal at 24 of 24 | same | RD |
| **P6 B2** panel-mean ward MAE falls | held (A3) | 2.9905 → 2.9014 (−0.0891) | recomputed `ward_mae` | RD |
| **P6 B2** the five named city-years improve or hold | falsified (2 of 5); A3: a failure is a finding | ekurhuleni 2021 +0.0146, joburg 2021 +0.1541 (worse); NMB 2021 −0.0299, buffalocity 2016 −0.0136, mangaung 2021 −0.0732 | same | RD |
| **P6 B2** no city-year worse by more than 0.15 | falsified; A3 as above | ethekwini 2016 +0.4248, capetown 2021 +0.2499, ethekwini 2021 +0.1762, joburg 2021 +0.1541 | same | RD |
| **P6 B3** coherent seat error −15 to 0 (A2) | held (A3) | 735 → 721 (−14) | recomputed | RD |
| **P6 B4** ward accuracy recorded | recorded, no prediction | 2,120 → 2,115 of 2,191 wards; ward-weighted Brier 0.0537 → 0.0540 | `result.json["wards"]` | G |
| **P6** CHANGE: no ward candidate, coverage 0, ratio 0, ward share < 1e-5, 0 wins (B-E) | held | coverage 0.0 (previous 0.9943), ratio 0.0 in B, C, C16, D, E (and D0); ward share 9.44e-7 to 1.24e-6, 0 draws ≥ 1e-5, 0 ward wins | `meta`, `arrays.npz` | RD/TR |
| **P6** addendum C1-C3 | not scored (no arm, per §4) | — | — | — |
| **P8** B8 identical to A at the four | held | identical at buffalocity 2011, buffalocity 2021, ethekwini 2016, mangaung 2011, and at no other city-year | `arrays.npz` | RD |
| **P8** panel-mean list MAE B8 − A ≤ +0.005 | **falsified** | 3.1599 → 3.2352 (+0.0754) | recomputed `pr_mae` | RD |
| **P8** list MAE falls at the three city-years over 1% | **falsified (0 of 3)** | ekurhuleni 2011 3.551 → 4.491 (+0.940); mangaung 2021 1.765 → 2.376 (+0.611); NMB 2021 2.814 → 2.844 (+0.029) | same | RD |
| **P8** coherent seat error, summed (A2) | inconclusive (A2 middle region +1 to +4) | 735 → 737 (+2) | same | RD |
| **P8** `roster_unrepresented` equals §1.1; never `"not_checked"` (B8, B-E) | held (A3) | equal party for party at the seven 2011 city-years and `[]` at the other 17 and 2026, in B8, B, C, C16, D, D0, E | `41_guards` | TR |
| **P8** 2026: the seven together 0.2-0.5% | held (A3) | 0.4151% (B8) | `arrays.npz` | RD |
| **P8** 2026: each below 0.15% | held | largest UIM 0.1267% (B8) | same | RD |
| **P8** 2026: together 0 or 1 seat in > 80% of draws | held | 84.30% (B8) | same | RD |
| **P11** PA falls 0.5-2.5 seats (C vs B, 2026) | held | 17.073 → 16.290 (−0.784) | `arrays.npz` | RD |
| **P11** no other party moves by more than 0.6 seats | **falsified** | EFF 27.950 → 28.927 (+0.977) | same | RD |
| **P11** DA gains 0-1.5 | held | +0.511 | same | RD |
| **P11** ANC gains 0-1.5 | **falsified** | 65.925 → 65.593 (−0.332) | same | RD |
| **P11** panel list MAE moves < 0.05 at every city-year | **falsified** | 18 of 24 city-years at ≥ 0.05; largest mangaung 2021 −0.603; then mangaung 2011 −0.472, capetown 2016 +0.344, capetown 2011 +0.321 | recomputed | RD |
| **P11** coherent seat error within ±6 | held | 725 → 723 (−2) | same | RD |
| **P16** h = inf for θ and ρ at all 25 targets, statuses as §1.2 | held (A3) | h = inf at 25 of 25; status, best, scored, clusters by year equal §1.2 (2011 θ underdetermined —/83/1, ρ underdetermined —/0/0; 2016 θ derived inf/168/2, ρ underdetermined —/74/1; 2021 θ derived 2.0/265/3, ρ derived 0.25/165/2; 2026 θ derived 1.5/403/4, ρ derived 0.5/283/3) | C16 `20_spine.size_window` | TR |
| **P16** C16 identical to C at 24 + 2026; PA moves 0 | held (A3) | identical at 25 of 25 | `arrays.npz` | RD |
| **P17** MK falls 1.5-4 seats (D vs C16, 2026) | **falsified** (by 0.104 seats) | 25.077 → 23.681 (−1.396) | `arrays.npz` | RD |
| **P17** ASA falls 0-1.5 | held | −0.431 | same | RD |
| **P17** BOSA, RISE gain 0-0.7 each | held | BOSA +0.275; RISE +0.204 | same | RD |
| **P17** GOOD gains under 0.3 | not scorable | GOOD is in `03_roster.dropped` at 2026 and in neither arm's universe | `03_roster`, `meta.universe` | TR |
| **P17** AHC gains under 0.3 | held | 1.135 → 1.149 (+0.015) | `arrays.npz` | RD |
| **P17** every other spine-level riser gains under 0.3 | held | 86 parties' `20_spine.level` rises D vs C16; largest seat gain outside the named: DUDULA +0.119 | `20_spine.level`, arrays | TR/RD |
| **P17** ANC gains 0-1.5 | held | +1.143 | arrays | RD |
| **P17** DA gains 0-1.5 | held | 69.594 → 69.614 (+0.021) | same | RD |
| **P17** EFF gains 0-1.5 | **falsified** | 28.927 → 28.091 (−0.836) | same | RD |
| **P17/A1** the seven in C16's `level_sd_default_parties`; D's `level_sd_at_size` within ±0.005 of A1 | held | all seven present in C16; D: 0.6738, 0.5989, 0.5569, 0.5554, 0.5413, 0.4575, 0.4231 against 0.674, 0.599, 0.557, 0.555, 0.541, 0.457, 0.423 | `41_guards` | TR |
| **P17** the seven 0 or 1 seat in > 80% of D's draws | held | 82.44% | arrays | RD |
| **P17** panel-mean list MAE "falls by 0.00-0.05" / "a rise above 0.05 falsifies" | ambiguous: not held under the range reading, not falsified under the threshold reading | 3.2237 → 3.2572 (+0.0336) | recomputed | RD |
| **P17** coherent seat error within ±6 | held | 723 → 727 (+4) | same | RD |
| **P13** SACP centre 0.06-0.10%, equal to B's seed within ±1% (A8) | held (A8: by construction; range sized from a model output, not counted) | seed 0.0621% = `30_centres.before_shrink` 0.0621% (B) | B's `pools_2026.json`, `30_centres` | RD/TR |
| **P13** SACP mean seats < 0.3, below A's | held | 0.184 (A 3.486) | arrays | RD |
| **P13** SACP P(≥ 1 seat) < 0.12, below A's | held | 0.063 (A 0.693) | same | RD |
| **P13** centre below A's | held | B 0.0621% vs A 1.31% (`before_shrink`) | `30_centres` | TR |
| **P13** other generic entrants' seeds move < 3% | held | all 45 entrant seeds × (1 − 0.02838), i.e. −2.838% each | specs | RD |
| **P13** SPEC P13 seat transfers | reported only (per §4) | B vs A: ANC +2.180, DA +2.619 | arrays | RD |
| **P12** clause 1: record present vs moved aside identical; aside reports `"no record"` | held (A3) | identical on every array and on `30_centres` before and after shrink; `"no record"` | arrays, traces | RD/TR |
| **P12** clause 2: a count with `population` = `scanned` in every covered run | held under reading 1, falsified for 8 runs per arm under reading 2 (see departures) | 17 runs per arm (2016, 2021, 2026) report a count, `population` = `scanned` in all 17, `key_current` true; the 8 2011 runs report `"no record"` | `41_guards` | TR |
| **P12** clause 3: `PA\|Coloured` not firing at 2026 in B, C, C16, D, E | **falsified in all five arms** (A3 listed it as known) | share of draws above threshold 0.8123 against `fire_at` 0.05: B 67.86% (3,393), C 61.08% (3,054), C16 61.08% (3,054), D 60.68% (3,034), E 47.94% (2,397); D0 47.94%; the only firing pair in each | `41_guards.group_share_tripwire` | TR |
| **P19** E ≡ D0 at 2026, every centre and array | held (A3) | identical on every array; `30_centres` before and after shrink equal; E's derived class weights all 0.0 | arrays, `30_centres.bye_weight` | RD/TR |
| **P19/A5** ACP and T&S centre in E = E's seed within ±1% | held (by construction, A5) | ACP 0.0353% = seed (relative difference 0); T&S 0.0623% = seed (0) | E `pools_2026.json`, `30_centres` | RD/TR |
| **P19/A5** each above its E value in D | held | ACP 0.8412% vs 0.0353%; T&S 0.0814% vs 0.0623% (`before_shrink`) | `30_centres` | TR |
| **P19/A5** ACP mean seats in E < 0.2 | held | 0.102 (D 2.325) | arrays | RD |
| **P19/A5** DA's and MK's deltas no longer reach centres | moved to A3 by A5; not counted | — | — | — |
| **P19/A5** direction E − D: PA down, DA down, ANC up | held (the block's only blind part) | PA 16.310 → 15.197 (−1.113); DA 69.614 → 69.267 (−0.347); ANC 66.735 → 69.378 (+2.642) | arrays | RD |
| **P19** E ≡ D on the panel | held (A3) | identical at 24 of 24 | arrays | RD |
| **P19** `bye_weight_mode` inert at 2026 in E | held (A3) | the `inverse_variance` run is identical on every array and `30_centres`; its `meta.bye_weight_mode` is `inverse_variance` | arrays, meta | RD/TR |
| **P19** `BYE_MIN_WEIGHT` inert at 2026 in E | held (A3) | the run with 1.0 is identical; `45_delivered` records 1.0 read in that run, 30.0 in E's | arrays, `45_delivered` | RD/TR |
| **P14** | withdrawn (per §4) | — | — | — |
| **Item 10's other rows** | not scored (per §4) | — | — | — |
| Turnout band table (§2, SPEC §1.9) | no prediction | not re-derived | — | — |

**E3 note.** E3 allows "the SACP's pool membership, and fields derived from
those". I read the other members' weight changes (at most 1.1e-16 and 2.2e-16,
floating-point size) and `no_measured_vector` (changed for the SACP only) as
derived from the SACP's change. A reader who takes E3's field list literally
would call these two "other differing fields"; E3 is then falsified at the two
Johannesburg 2026 specs only, and §4 says a falsified E clause is investigated
before the arms reading those specs are scored.

**P17 panel ambiguity.** §4 states "list MAE (panel mean) falls by 0.00-0.05
points" and "a panel-mean list MAE rise above 0.05 points falsifies". A rise of
0.0336 is outside the first and below the second. A2 gave middle regions to the
seat clauses only. Under the range reading the clause is not held; under the
threshold reading it is not falsified.

**P6 B2 "improve or hold".** No tolerance is stated. Under a strict reading two
named city-years fail (ekurhuleni 2021 +0.0146, joburg 2021 +0.1541). Under a
reading that takes "hold" as within the file's own 0.15 noise statement,
joburg 2021 still fails at +0.1541.

### Tally

Counting each row above that carries a verdict, excluding A3/A8/by-construction
lines and rows not scored: **falsified** — P8 panel-mean list MAE, P8 the three
city-years, P11 other-party bound (EFF), P11 ANC, P11 panel per-city-year bound,
P17 MK, P17 EFF. Falsified but in A3's class (known before writing; a failure is
still a finding): P6 B2 named five, P6 B2 0.15 bound, P12 clause 3.
**Inconclusive** — P8 coherent (A2). **Ambiguous** —
P17 panel list MAE; P12 clause 2 (population reading).

### A limit on the panel and arm-difference clauses (measured, not a prereg instrument)

§3 states that B to E "share draws and seeds", and A, B0, B6, B8 likewise. The
seed is shared; the per-draw values are paired only for some pairs. Per-draw
correlation of the largest party's PR share between arms, over the 25 runs:
A/B0 and A/B6 1.0 at all 25; D/E 1.0 at the 24 panel runs, −0.01 at 2026;
**A/B8 median −0.001** (1.0 at the four identical city-years); **B/C median
0.58** (0.014 at 2026); **C16/D median 0.17**. Where the draws are unpaired, an
arm difference carries the Monte Carlo error of both runs. A bootstrap over each
run's 1,000 draws (300 resamples; `boot.py`) gives the standard error of a
per-city-year `pr_mae` difference, treating the two arms as unpaired: median
0.19-0.20 points, largest 0.36-0.37, for each of A/B8, B/C, C16/D; for the
panel mean 0.041-0.042. Against that: P8's panel-mean +0.0754 is 1.8 such
errors, ekurhuleni 2011's +0.940 is 4.1 (error 0.229), mangaung 2021's +0.611 is
2.4 (0.252), NMB 2021's +0.029 is 0.1 (0.202). P11's per-city-year bound of
0.05 is a quarter of the per-city-year error (B/C are partly paired, so the
unpaired error overstates theirs). P17's panel-mean +0.0336 is 0.8 errors. These limits do not
change any verdict, which §4 defines by the stated ranges.

A check of where 11a's panel movement enters (B against C): at mangaung 2011,
where list MAE moved −0.472, no party's `20_spine.level` or `30_centres` level
above 0.01% moved by more than 0.006 in natural log; ANC mean list share moved
57.773 → 58.546 with per-draw correlation 0.24 between the arms. At mangaung
2021 (−0.603) the largest centre move is the PA's, 1.530% → 1.414% (−0.078 in
log), and the ANC's mean list share moved 47.664 → 48.585 with per-draw
correlation 0.047.

---

## Departures from the pre-registration

**1. C16's recipe fails `git apply --check` (A13: that stops the arm).**
- Prereg: §3 and A13 — a recipe that fails `git apply --check` on W stops that
  arm. §3.3 itself specifies a `--3way` application with one conflict and its
  resolution.
- Done: `git apply --check -R` of cdcf517 fails at W and equally at acbd9f8,
  where the prereg built and hashed the recipe (`STEP11-RUNS.md` §1). The arm
  was built by the 3-way application and the stated resolution; at acbd9f8
  that reproduces the prereg's own C16 hash `81d681500680923d…` and tree
  `e2ab33c6ebdd48d6`. I recomputed the C16 tree hash (`70788004167673cc`) and
  the committed C16 diff hash (`e5fbb23b953343f0…`, 361 lines); both equal
  `STEP11-RUNS.md`.
- If the arm stands: verdicts as in the table.
- If A13 stops C16: C and B are built on C16's tree, so they stop too. Not
  scorable: P16 (C16 vs C); P17 entire (D vs C16), including A1's C16 half;
  P11 (C vs B); P13 (B vs A); the B, C, C16 parts of E3 (E's specs carry the
  same field list, so E3 holds on E alone), of P1's lot clause, of CHANGE, of
  P8's guard clause and of P12 clauses 2 and 3. Still scored: E1, E2, E4,
  P10, P1, P2, P2b, P3 (on E), P6 on B6, P8 on B8, CHANGE and the guard on D
  and E, P12 on D and E (clause 3 falsified in both), P19 entire. The
  falsifications of P11 (EFF, ANC, panel) and P17 (MK, EFF) then become not
  scorable; P8's and P6 B2's remain.

**2. B6's tree hash needs a trailing blank line.**
- Prereg: §3.1's resolution text, and the stated diff sha256
  `9ed8630ee0f952f6…` (236 lines).
- Done: the resolution as written gives 235 lines and `2e0d65f81b3b9205…`; the
  built arm keeps one blank line after `return out` at the end of `levels.py`
  and gives the stated hash. I confirmed the committed `B6.src.diff` hashes to
  `9ed8630ee0f952f6…` (236 lines), the B6 tree to `0ea073d69372edb7`, and that
  B6's `levels.py` ends `return out\n\n`.
- If the stated hash is the authority (as A6 makes it for B8): B6 is the
  pre-registered arm; verdicts as in the table.
- If the resolution text is the authority: the built tree is not arm B6, and
  the P6 lines (F1-F6, B1-B4, the implementation check) and E2's B6 half are
  not scorable on it. The difference is one newline and no code.

**3. P12's population: 17 covered runs per arm, not 24.**
- Prereg: P12 clause 2, "in every run of B, C, C16 and E at a city-year the
  record covers". It does not say which years the record covers.
- Done: `group_share_record.json` covers 2016, 2021 and 2026 for all eight
  cities (`cities.<city>` keys in E's tree); the 8 2011 runs report
  `"no record"`.
- Reading 1 (the clause is conditional on coverage): 17 covered runs per arm,
  all a count with `population` = `scanned` — held.
- Reading 2 (the prereg expected every panel run to be covered): the 8 2011
  runs per arm fail "is a count, not `"no record"`" — falsified for 8 of 25
  runs in each of B, C, C16, (D, D0,) E.

**4. The `seed_notes` count (18).**
- Prereg: E3 exempted `seed_notes` at the two Johannesburg 2026 specs; A11
  extended the exemption to every spec, for band-sentence text changes, citing
  "the 2016 and 2021 specs" (window commit body said 18 specs, its writer's
  table 16).
- Measured (E's tree): 18 specs carry a `seed_notes` change — the 16 backtest
  2016/2021 specs and the 2 Johannesburg 2026 specs; no 2011 spec and not
  Tshwane 2026. In the 16, every changed note is a band-sentence replacement
  (0 other content changes). In the 2026 specs the SACP's note also changes
  content (seeded declaration → "entrant from nothing"), which E3's SACP
  exemption covers.
- E3's verdict is held whether the count is 16 or 18: the 2 extra are the 2026
  specs E3 exempted from the start.

**5. Output paths.**
- Prereg: §2, 2026 runs with `--run-dir` "into the arm's scratch directory".
- Done: every run's raw outputs, trace included, went to
  `data/arms/step11/<arm>/<label>/` in the real tree (gitignored); panel runs
  were traced as well (`trace/<city>-<year>/`). STEP11-RUNS §5 records the real
  tree's `data/processed`, `site/`, `content/`, `publications/`, `prereg/`,
  `src/`, `tests/` listings unchanged across the runs (I did not re-check).
- No verdict depends on the path.

**6. Arm D and D0 trees.** D and D0 ran in E's tree with `--set w_bye=0.4` and
`--set w_bye=0` (`meta.tree`, `meta.overrides` in every D/D0 run), as §3
specifies. Not a departure; recorded because the prereg lists D's specs as
"E's tree".

**7. B, C and C16 hold no `bye_value.json`; three `-k chain` tests fail
there.** §2's gate names `test_every_emitted_pool_spec_carries_a_current_artefact_key`
(passed in every tree) and `test_the_specs_on_disk_agree_with_the_constructed_one`
(passed, not skipped, in the W-based trees). The three failures
(`SystemExit: …bye_value.json is missing`, a 2026 run with no `w_bye`
override) are outside the gate (taken from `STEP11-RUNS.md` §2). No arm run
reads the file: every B, C, C16 run carries `w_bye=0.4` (`meta.overrides`). No
verdict depends on it.

**8. The draws are not paired between some arms** (above). §3's "share draws
and seeds" is a premise of the design, not a scored clause; the verdicts are
scored by the stated ranges regardless.

---

## What the pre-registration did not predict

1. **`PA|Coloured` fires at Johannesburg 2026 in every W-based arm.** Threshold
   0.8123 = the PA's Coloured-pool record 0.4290 + the Coloured pool's margin
   0.3832 (E's `group_share_record.json`, `cities.joburg.2026`, margin over 16
   cycles); `fire_at` 0.05. Share of draws with the PA's within-pool Coloured
   share above 0.8123: B 67.86%, C 61.08%, C16 61.08%, D 60.68%, D0 47.94%,
   E 47.94% (5,000 draws each). It is the only firing pair at 2026 in each arm;
   P12 and A3 stated it cannot fire by construction (owner's rule, M3).
2. **Item 8 raised list MAE at all three high-mass city-years** (B8 − A:
   ekurhuleni 2011 +0.940, mangaung 2021 +0.611, NMB 2021 +0.029) and the
   panel mean by +0.0754; per city-year it rose at 9 of the 20 entered
   city-years (largest besides the three: joburg 2011 +0.651, tshwane 2011
   +0.478, ethekwini 2011 +0.466, capetown 2016 +0.441) and fell at 11 (largest
   capetown 2021 −0.390, joburg 2016 −0.361, ekurhuleni 2016 −0.352, NMB 2016
   −0.348).
   Five of the six 2011 city-years with an entered party rose. B8 and A share
   no per-draw pairing outside the four identical city-years.
3. **11a moves panel list MAE by 0.3-0.6 points at four city-years** (mangaung
   2021 −0.603, mangaung 2011 −0.472, capetown 2016 +0.344, capetown 2011
   +0.321), against §1.3's spine changes (panel 90th percentile |Δlog| 0.0096).
   At mangaung 2011 no centre above 0.01% moved by more than 0.006 in log; the
   B/C per-draw correlation of the ANC's list share there is 0.24.
4. **11a moves the EFF by +0.977 seats and the ANC by −0.332 at 2026** (C vs
   B), where §1.3 measured the EFF's spine at −0.003 and the ANC's at +0.003 in
   log.
5. **Item 17 moves the EFF by −0.836 seats and the IFP by +0.186 at 2026** (D vs
   C16), though neither's `20_spine.level` changes (identical in both arms).
6. **Item 6 worsens ward MAE by more than 0.15 at four city-years** (B6 − A):
   ethekwini 2016 +0.4248, capetown 2021 +0.2499, ethekwini 2021 +0.1762,
   joburg 2021 +0.1541, while the panel mean falls 0.0891.
7. **GOOD is off the 2026 ballot** (`03_roster.dropped`), though §1.3 and P17
   sized its spine move.
8. **E3's floating-point drift**: other members' pool weights in the two 2026
   specs differ from A's by up to 1.1e-16 (`pools_2026.json`) and 2.2e-16
   (`pools_2026_simulation.json`).
9. **D against E at Johannesburg 2026 moves more than the three named parties**:
   EFF +2.582, ASA −1.408, IFP −0.608, ALL_CITIZENS_PARTY −2.222 mean seats.
10. **Population 1 (P1) varies by arm at 2026**: 15 (A, B0), 7 (B6), 12 (B8),
    13 (B), 10 (C, C16), 9 (D), 11 (D0, E) draws; lot class 0 or 1 draw in
    every arm; no draw in both classes.
