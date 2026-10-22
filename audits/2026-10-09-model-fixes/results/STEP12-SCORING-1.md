# Step 12 scoring 1: the batch pre-registration, scored (2026-10-10)

Scorer 1 of 2, working from `reviews/STEP12-SCORING-BRIEF.md` (c4cd8b1) alone.
The rule is `prereg/2026-10-10-model-correction-batch.md` §4 with amendments
A1-A13; where an amendment restates a clause, the amendment is scored. Where §4
is ambiguous the clause is scored under each reading.

**Sources of every number.** Raw outputs in `data/arms/step11/<arm>/<label>/`
(`arrays.npz`, `meta.json`, `result.json`, `trace/`), the arm trees' own specs
(`<scratchpad>/arms/<arm>/data/processed/pools_*.json`) and `rule_a.json`.
Re-derivation scripts are in this session's scratch directory
(`scratchpad/score1/`: `lib.py`, `panel.py`, `tot.py`, `y2026.py`, `rest.py`,
`guard_spec.py`); none writes inside the repository. `STEP11-RESULTS.md` and
`measures.json` were used only to find what to check; no verdict below rests on
a number taken from either.

**How the panel scores were re-derived.** `pr_mae`, `ward_mae` and
`seat_abs_err_coherent` were recomputed from each run's saved arrays: actual
shares from `compare_history.actual_shares` and actual seats and the arrival
label from `compare_history._actual_seats` (read-only, current tree), the
arrival relabel applied to the arrays as `backtest.relabel_run` does, the
share-weighted MAE and the largest-remainder coherent council reimplemented in
the script. All 240 panel runs (10 arms × 24 city-years) agree with the run's
own `result.json` exactly (0 mismatches at 1e-9 on both MAEs, 0 on coherent
seats).

"Identical" below means every saved array (PR and ward share draws, PR and ward
vote draws, seat draws, per-draw ward winners by party name, pool turnout draws)
equal element for element, aligned by party name, with the universes checked
equal first.

**A3** marks a line the pre-registration declared known before writing; it is
scored and does not count toward a tally of confirmed predictions.

---

## 1. Verdict table

| prediction | verdict | deciding number (source) | re-derived? | A3 |
|---|---|---|---|---|
| E1 B0 specs byte-identical | held | 27/27 byte-identical (arm tree specs) | yes | A3 |
| E2 B6, B8 specs differ only in `deps_sha` | held | 27/27 differ only at `/artefact_key/deps_sha`, both arms | yes | |
| E3 B, C, C16, E specs | held under A11; see readings | field sets below; 326 changed notes, all band deletions; C ≡ C16 27/27; `group_share_record` `cities` one hash `17a2639b1b6a84fd` | yes | |
| E4 2011 specs carry no seeds | held | 0 seeds in all 8, B and E (C, C16 byte-identical to each other) | yes | |
| P10 stale specs, refusals | held (clauses 1-2; clause 3 argued, not scored) | `stale_reason` null in 253/253 traces; `pools_stale` null in 250 run metas and 48 rule-A metas; 301/301 run directories complete | yes (A4 tests: given) | |
| P1 population-2 identity, A vs B0 | held | 2026: 0 of 4,985 pop-2 draws differ; panel: 0 at 24/24; all share, vote, winner, turnout arrays identical | yes | |
| P1 pop. 1 > 0 in A at 2026 | held | 15 draws (14 item 2, 1 lot) | yes, from the saved per-draw classes | A3 (item 2) |
| P1 class lot < 2% in every arm | held | largest lot share in any run 0.20% (A, B0, D, D0, E) | yes, from the saved per-draw classes | |
| P2 tied wards 0 | held | 0 at 24/24 in A and B0 (`rule_a.json` `tied_wards`) | yes | |
| P2 rule A differs only where a tie is met | held | seats and ward wins identical at 24/24 | yes | |
| P2 Johannesburg 2016 tie, seat error differs by 0 or 2 | held | tie AIC/TRULY_ALLIANCE 3,743 each, class lot, in both; seat error 28 and 28 (difference 0) | yes | A3 |
| P2b uniform-swing+roster total in [837, 841] | held | 837 (B0), sum of `result.json` `opponents["uniform-swing+roster"].seat_abs_err_coherent` | summed; per-row values given | |
| P3 `unopposed_wards` = `{}` | held | `{}` at 25/25 in B, C, C16, E (re-run in each tree) | yes | |
| P6 F1 PA ratio 2.000 → 1.029 | held | 2.000 → 1.0293 (`meta.ward_pr_ratio`) | yes | A3 |
| P6 F2 PA mean gap in [−0.6, +0.2]; ≤1% of draws at or below −1.76 | held | −0.188; 0.00% (range −1.13 to +0.48) | yes | A3 |
| P6 F3 five mean gaps | held | DA −1.36, ANC −0.49, EFF −0.99, ASA +2.67, MK +0.46, each in range | yes | A3 |
| P6 F4 PA seats, ward wins | held | 16.92 in [16.0, 18.5]; 5.07 in [4.5, 6.5] | yes | A3 |
| P6 F5 DA, ANC +1.0 to +3.0; no other > 1.5 | held | DA +2.01, ANC +1.94, largest other EFF +0.85 | yes | A3 |
| P6 F6 PR share draws identical | held | identical (PR votes, pool turnout identical too) | yes | A3 |
| P6 B1 list MAE identical | held | PR share draws identical and `pr_mae` equal at 24/24 | yes | A3 |
| P6 B2 ward MAE | partly held (readings below) | panel mean 2.9905 → 2.9014; joburg 2021 +0.1541, ekurhuleni 2021 +0.0146; four city-years worse by > 0.15, largest ethekwini 2016 +0.4248 | yes | A3 |
| P6 B3 coherent seat error (A2) | held | 735 → 721 (−14), in A2's holds region [−15, 0] | yes | A3 |
| P6 B4 ward winner accuracy | recorded only | 2,120 → 2,115 of 2,191 | from `result.json` | |
| P6 implementation check (A8, not a prediction) | inside both intervals | PA seats 16.921 (16.85 ± 0.5); PA gap −0.188 (−0.19 ± 0.1) | yes | |
| P6 CHANGE (N4) | held | B, C, C16, D, E: coverage 0.0, ratio 0.0, ward share 9.4e-7 to 1.24e-6, 0 draws ≥ 1e-5, 0 ward wins | yes | |
| P8 the four city-years identical | held | B8 ≡ A at buffalocity 2011, 2021, ethekwini 2016, mangaung 2011 | yes | |
| P8 panel-mean list MAE, B8 − A ≤ +0.005 | **falsified** | +0.0754 (3.1599 → 3.2352) | yes | |
| P8 list MAE falls at the three > 1% city-years | **falsified** at all three | ekurhuleni 2011 +0.940, mangaung 2021 +0.611, nelsonmandelabay 2021 +0.029 | yes | |
| P8 coherent seat error (A2) | inconclusive (A2 middle region) | 735 → 737 (+2) | yes | |
| P8 `roster_unrepresented` | held | equal to §1.1 at the seven 2011 city-years, `[]` at the other 17 and 2026, in B8, B, C, C16, D, D0, E; never `"not_checked"` | yes | A3 |
| P8 2026: seven together 0.2-0.5%, each < 0.15%, 0-1 seat in > 80% | held | 0.415%; largest UIM 0.127%; 84.3% | yes | A3 (share) |
| P11 PA falls 0.5-2.5 seats | held | 17.07 → 16.29 (−0.78) | yes | |
| P11 no other party moves > 0.6 | **falsified** | EFF +0.98 | yes | |
| P11 DA and ANC each gain 0-1.5 | partly held | DA +0.51 held; ANC −0.33 falsified | yes | |
| P11 panel list MAE moves < 0.05 at every city-year | **falsified** | 18 of 24 at ≥ 0.05; largest mangaung 2021 −0.603 | yes | |
| P11 panel coherent seat error within ±6 | held | 725 → 723 (−2) | yes | |
| P16 every window infinite, statuses as §1.2 | held | h = inf for θ and ρ at all 25 targets; status/best/scored/clusters equal §1.2 row for row (C16 `20_spine.size_window`) | yes | A3 |
| P16 C16 identical to C | held | identical at 25/25; PA moves 0 seats | yes | A3 |
| P17 MK falls 1.5-4 seats | **falsified** | 25.08 → 23.68 (−1.40), 0.10 short of the bound | yes | |
| P17 ASA falls 0-1.5 | held | −0.43 | yes | |
| P17 BOSA, RISE each gain 0-0.7 | held | +0.27, +0.20 | yes | |
| P17 GOOD gains under 0.3 | not scorable (or vacuously held) | GOOD is not in C16's or D's 2026 universe; 0 seats in both | yes | |
| P17 AHC gains under 0.3 | held | +0.01 | yes | |
| P17 every other spine-level riser gains under 0.3 | held | largest DUDULA +0.119 (86 risers in the traces) | yes | |
| P17 ANC, DA, EFF each gain 0-1.5 | partly held | ANC +1.14, DA +0.02 held; EFF −0.84 falsified | yes | |
| P17 / A1 level sd of the seven | held | all seven in C16 `level_sd_default_parties`; D `level_sd_at_size` within ±0.005 of A1 for all seven | yes | |
| P17 seven: 0-1 seat in > 80% (D) | held | 82.4% | yes | |
| P17 panel-mean list MAE falls 0.00-0.05 | falsified as a range; not falsified under the stated falsifier | D − C16 = +0.0336 (a rise, below 0.05) | yes | |
| P17 panel coherent seat error within ±6 | held | 723 → 727 (+4) | yes | |
| P13 SACP centre 0.06-0.10% (A8: equal to B's seed within ±1%) | held | seed 0.0621%, `30_centres.before_shrink` 0.0621% (equal); `after_shrink` 0.0838% | yes | A8: range from a model output |
| P13 SACP mean seats < 0.3, P(≥1 seat) < 0.12, each below A's | held | 0.184 (A 3.486); 0.063 (A 0.693); centre below A's 1.310% | yes | |
| P13 other generic entrants' seeds move < 3% | held | 45 entrants, each −2.8383% | yes | |
| P12 record present ≡ moved aside; aside reports `"no record"` | held | identical arrays and `30_centres`; `"no record"` | yes | A3 |
| P12 count, `population` = `scanned`, in every covered run of B, C, C16, E | held under the literal reading (see §3) | 17 runs per arm, all dicts with `population` = `scanned`, `key_current` true | yes | |
| P12 `PA|Coloured` does not fire at 2026 in B, C, C16, D, E | **falsified** in all five | fires in B 67.9%, C 61.1%, C16 61.1%, D 60.7%, E 47.9% of draws against `fire_at` 0.05 (`41_guards.group_share_tripwire`) | read from the run's trace; not recomputed | A3 |
| P19 E ≡ D0 at 2026 | held | identical arrays and `30_centres`; E's class weights both 0.0 | yes | A3 |
| P19 E ≡ D on the panel | held | 24/24 identical | yes | A3 |
| P19 `bye_weight_mode` and `BYE_MIN_WEIGHT` inert | held | both runs identical to E (arrays, `30_centres`) | yes | A3 |
| P19 / A5 ACP and T&S centres equal E's seeds ±1%; D above E | held | ACP 0.0353% = seed (0.0000%), D 0.841%; T&S 0.0623% = seed, D 0.0814% | yes | by construction (centres) |
| P19 / A5 ACP mean seats in E < 0.2 | held | 0.102 | yes | |
| P19 / A5 direction E − D: PA down, DA down, ANC up | held | PA −1.11, DA −0.35, ANC +2.64 | yes | blind |
| Item 10's other rows | not scorable | prereg: not scored on arms (G18 is a test) | — | |
| P4, P5 | not scorable | prereg §4: a test and records; no model number moves | — | |
| P9 | not scorable | prereg §4, §3.6: no arm isolates it; argued null | — | |
| P6 addendum C1-C3 | not scorable | needs a no-slate-change arm, not built (prereg §4 P6) | — | |
| P6 reproduction check against 733 | not made | prereg §4 P6: no earlier output is a reference | — | |
| P13 seat transfers (ANC +1 to +3.5, DA 0 to +1.5) | not scorable | no arm isolates item 18. Reported, B − A: ANC +2.18, DA +2.62 | yes (reported only) | |
| P16 R2.5 other-party and panel clauses | withdrawn by the prereg | not scored | — | |
| P14 | withdrawn (R2.5) | not scored | — | |

Source legend for the table: `arrays` = `data/arms/step11/<arm>/<label>/arrays.npz`;
`result` = the run's `result.json`; `meta` = its `meta.json`; trace keys are
`trace/<file>.json` (forecast runs) or `trace/<label>/<file>.json` (panel runs).

Falsified clauses, by prediction: P8 panel-mean list MAE and the three named
city-years; P11 "no other party > 0.6", ANC's gain, and the per-city-year list
MAE bound; P17 MK's fall, EFF's gain, and (under one reading) the panel list MAE
range. P12 clause 3 is falsified and is an A3 line.

---

## 2. Per-prediction detail

### E1-E4 (spec neutrality)

Re-derived by a recursive JSON diff of every arm tree's 27 specs against arm A's
copy (`guard_spec.py`).

- E1: B0 27/27 byte-identical. Held.
- E2: B6 and B8, every spec differs at `/artefact_key/deps_sha` and nowhere else. Held.
- E3: B, C, C16 and E give the same field sets:
  9 specs (eight 2011, `tshwane/pools_2026.json`): `artefact_key`
  (`cities_sha`, `deps_sha`, `pools_sha`) and `seed_bands` removed; 16 specs
  (2016, 2021): those plus `seed_notes`; the two Johannesburg 2026 specs: those
  plus `judgements_sha`, `no_measured_vector`, `pools`, `seed_notes`,
  `seeded_arrival_mass`, `seeds`. C's and C16's specs are byte-identical, 27/27.
  `group_share_record.json` `cities`, canonical JSON sha256 `17a2639b1b6a84fd`
  in all four.
  - `seed_notes` in the 16 backtest specs: 234 notes changed; 230 lose a
    "Band …" sentence for "The draw's width comes from the pool split."; the 4
    ASA splinter notes (ekurhuleni, ethekwini, joburg, tshwane 2021) lose the
    band range and keep the source phrase, folded into the previous sentence.
    A11 names these four. No other note content differs.
  - `no_measured_vector` at 2026: only the SACP's entry changes ("judged
    weights" → the generic entrant text). Derived from the SACP's membership.
  - `pools` at 2026: the SACP's member weights (4 pools; 5 in the simulation
    spec, which adds `IFP-located`), and other members' weights differing by at
    most 1.11e-16 (29 parties) and 2.22e-16 (45 parties).
  - **Reading 1** (`seed_notes` exempt everywhere for band-deletion text, A11;
    the ~1e-16 weight differences are floating-point consequences of the SACP
    renormalisation, so "fields derived from those"): **held**.
  - **Reading 2** (E3 as first written, `seed_notes` exempt only at the two 2026
    specs): falsified at 16 specs. A11 was appended after the window emit had
    been inspected and before any arm ran; it is the scored text.
  - **Reading 3** (any changed member weight other than the SACP's is "another
    differing field"): falsified at the two 2026 specs by 74 weight entries,
    each within 2.22e-16.
- E4: every 2011 spec carries 0 seeds in B and E (and C, C16, byte-identical to C). Held.

### P10

`02_pools_artefact.stale_reason` null in all 253 traced runs (25 per arm × 10,
plus the three extra E runs); `meta.pools_stale` null in every run and in the 48
rule-A runs. 301 run directories, each with `meta.json`; the harness asserts
after writing, so a refusal leaves no `meta.json`. Clauses 1-2 held. A4's three
`test_stage_inputs` tests: taken as given from `STEP11-RUNS.md` §2 (not re-run).

### P1

The per-draw tie classes are the classifier's output saved at run time
(`tie_class_per_draw`); the classification itself cannot be recomputed from the
saved arrays (the `allocate` inputs are not saved). I read the harness code
(`harness/arm_run.py` `classify`) against §2's specification: quota, whole-vote
surplus, shortfall, ranking by (−surplus, −votes), the straddling pair and the
lot/item-2 split match.

| arm | 2026 pop. 1 (item 2 / lot) | panel pop. 1 summed (item 2 / lot) | largest lot share in any run |
|---|---|---|---|
| A | 15 (14 / 1) | 15 (13 / 2) | 0.20% |
| B0 | 15 (14 / 1) | 15 (13 / 2) | 0.20% |
| B6 | 7 (7 / 0) | 18 (15 / 3) | 0.10% |
| B8 | 12 (11 / 1) | 18 (17 / 1) | 0.10% |
| B | 13 (12 / 1) | 24 (22 / 2) | 0.10% |
| C, C16 | 10 (9 / 1) | 22 (18 / 4) | 0.10% |
| D | 9 (8 / 1) | 22 (14 / 8) | 0.20% |
| D0, E | 11 (10 / 1) | 22 (14 / 8) | 0.20% |

A vs B0: population 1 is the same 15 draws at 2026; 0 of 4,985 population-2
draws have a different seat vector; 5 population-1 draws do. Panel: 0
population-2 differences at 24/24; 3 population-1 draws differ (ekurhuleni
2021, ethekwini 2021, capetown 2011). All non-seat arrays identical everywhere.
Held.

### P2, P2b

From each arm's `rule_a-<city>-<year>/rule_a.json` and `meta.json`: `tied_wards`
empty at 24/24 in both; rule A's seats and ward wins identical at 24/24; the
only non-untied rule-A seat call is Johannesburg 2016, class lot, AIC and
TRULY_ALLIANCE at 3,743 votes, shortfall 11, in both arms; seat error 28 in
both. Rule A's seat error summed: 737 in both. P2b: 837 in B0 (837 in A), in
[837, 841]. The per-city-year baseline values are `compare_history`'s own; I
summed them and did not recompute the baseline. Held.

### P3

Re-run in each of B's, C's, C16's and E's trees (the harness's `unopposed.py`
logic, printing only): 25 targets each, no non-empty result. No run refused.
Held.

### P6 (B6 against A)

Every F line held (table in §1; all re-derived from the 2026 arrays). F2 range
of B6's per-draw PA gap −1.13 to +0.48. F3's expected DA tail: 17.86% of B6
draws at or below −1.76 (the file says this is not a failure of the fix).

B2. The file's text: "the panel mean falls. City-years where a party … at least
doubled its ward count (Ekurhuleni 2021 PA, Nelson Mandela Bay 2021 PA,
Johannesburg 2021 PA, Buffalo City 2016 AIC, Mangaung 2021 AIC) improve or
hold; I expect no city-year to worsen by more than 0.15 pp."

| clause | B6 − A ward MAE | verdict |
|---|---|---|
| panel mean falls | −0.0891 (2.9905 → 2.9014) | held |
| named five improve or hold | ekurhuleni 2021 +0.0146, nelsonmandelabay 2021 −0.0299, joburg 2021 +0.1541, buffalocity 2016 −0.0136, mangaung 2021 −0.0732 | falsified at joburg 2021 under every reading; ekurhuleni 2021 falsified if "hold" means no rise, held if "hold" tolerates a rise of 0.015 (no tolerance is stated) |
| no city-year worse by > 0.15 | ethekwini 2016 +0.4248, capetown 2021 +0.2499, ethekwini 2021 +0.1762, joburg 2021 +0.1541 | falsified if "I expect" is a prediction; not scored if it is an expectation outside the scored lines (the file states a falsifier only for B3 and a withdrawal rule naming B3 and F2) |

B2 overall: partly held. The file's withdrawal rule ("B3 worse by more than 4
seats with B2 not improving; or F2 failing") is not met: B3 −14, F2 held.

B3: 735 → 721 (−14), A2 holds region. B4 (recorded only, from `result.json`):
2,120 → 2,115 wards called right of 2,191.

Reported on B against A, not scored: PA gap −0.19, PA 17.07 seats and 5.04 ward
wins, DA +2.62, ANC +2.18, SACP −3.30.

CHANGE: held in all five arms (numbers in §1).

### P8 (B8 against A)

Per city-year, B8 − A, list MAE / coherent seats (re-derived):
joburg 2011 +0.651/+6, 2016 −0.361/−2, 2021 −0.086/0; tshwane 2011 +0.478/+4,
2016 +0.025/+2, 2021 −0.030/0; ekurhuleni 2011 +0.940/+6, 2016 −0.352/−4, 2021
−0.046/−2; ethekwini 2011 +0.466/+4, 2016 0/0, 2021 −0.048/−2; capetown 2011
−0.155/−2, 2016 +0.441/0, 2021 −0.390/−6; mangaung 2011 0/0, 2016 −0.115/−2,
2021 +0.611/+2; nelsonmandelabay 2011 +0.225/+2, 2016 −0.348/−2, 2021
+0.030/−2; buffalocity 2011 0/0, 2016 −0.125/0, 2021 0/0.

- Panel-mean list MAE +0.0754: falsified (bound +0.005).
- The argued mechanism ("entering it near its previous share cuts the error")
  fails at all three city-years where the entered mass exceeds 1% of the
  previous LGE list.
- Coherent +2: A2's middle region ("+1 to +4: inconclusive"). Under §4's
  original text ("falls by 0 to 12"; falsified "up by more than 4") it is
  neither held nor falsified either; A2 governs.
- The seven at 2026 in the other arms (reported): B 0.414% / 83.4%; C, C16
  0.374% / 83.7%; D 0.426% / 82.4%; E 0.446% / 81.4%.

### P11 (C against B)

2026 seat changes (re-derived): EFF +0.98, PA −0.78, DA +0.51, ANC −0.33, ASA
−0.26, MK −0.14, BOSA −0.12, ACDP +0.11, ATM +0.11; all others under 0.1.
"No other party moves by more than 0.6" is falsified by EFF whether or not the
DA and the ANC count as "other". Panel: 18 of 24 city-years move by ≥ 0.05 in
list MAE (the six that do not: joburg 2011, joburg 2016, tshwane 2021,
ekurhuleni 2016, ethekwini 2021, mangaung 2016); the largest are mangaung 2021
−0.603, mangaung 2011 −0.472, capetown 2016 +0.344, capetown 2011 +0.321. Panel
mean −0.0115; coherent 725 → 723.

### P16 (C16 against C)

Re-derived from every C16 trace's `20_spine.size_window`: one tuple per target
year and route, equal to §1.2 (2011 θ underdetermined, scored 83, 1 cluster; ρ
underdetermined, 0, 0; 2016 θ derived best inf 168, 2; ρ underdetermined 74, 1;
2021 θ derived best 2.0, 265, 3; ρ derived best 0.25, 165, 2; 2026 θ derived
best 1.5, 403, 4; ρ derived best 0.5, 283, 3), h = inf throughout. C's trace
reports `h = inf, arm = "C: forced inf"` on both routes. C16 ≡ C at all 25
runs. Held.

### P17 (D against C16)

- MK −1.40: falsified, 0.10 seats short of the 1.5 lower bound.
- EFF −0.84: falsified ("each gain 0-1.5").
- GOOD: §1.3 tabulates GOOD's spine level (and the traces carry one: 0.249% →
  0.272%), but GOOD is not in C16's or D's 2026 universe; the spec records RISE
  "merged with GOOD". Reading 1: not scorable (no ballot party). Reading 2: held
  vacuously (0 seats in both, a gain of 0).
- Spine-level risers: 86 parties rise in `20_spine.level`, D against C16 (42
  unseeded). Excluding the named parties, the largest seat gain is DUDULA
  +0.119. IFP gains +0.19 and is not a riser. Held under either population
  (§1.3's list or the traces').
- Panel list MAE +0.0336. **Reading 1** ("each range as stated": the range is a
  fall of 0.00-0.05): falsified. **Reading 2** (the clause's own falsifier, "a
  panel-mean list MAE rise above 0.05 points falsifies the account"): not
  falsified, and the predicted fall did not happen either.
- Coherent 723 → 727 (+4), within ±6. Held.

### P13 (B against A)

Re-derived from A's and B's `pools_2026.json` and the 2026 runs: SACP seed A
0.01310, B 0.000621; `before_shrink` equals the seed in both; `after_shrink` A
0.01622, B 0.000838; mean list share A 1.399%, B 0.074%; mean seats A 3.486, B
0.184; P(≥1 seat) A 0.693, B 0.063. All 45 generic entrants (B's note begins
"entrant from nothing", SACP excluded) move by −2.8383%; no seed is added or
removed. Held. The SACP's centre clause is scored under A8 (equal to the seed,
by construction); the 0.06-0.10% range was sized from a model output (A8).

### P12

- Clause 1: E's record-moved-aside run is identical to E's run on every array
  and on `30_centres` before and after the shrink; it reports `"no record"`. Held.
- Clause 2: in each of B, C, C16, D, D0 and E, the 16 runs at 2016 and 2021 and
  the 2026 run report a dict with `population` = `scanned` and `key_current`
  true; the eight 2011 runs report `"no record"`. Held under the literal reading
  ("a city-year the record covers" = 2016, 2021, 2026); see §3 for the other.
- Clause 3: `PA|Coloured` fires at 2026 in every W-based arm. Draws above
  threshold 0.8123, from `41_guards.group_share_tripwire.pairs`: B 3,393
  (67.86%), C 3,054 (61.08%), C16 3,054 (61.08%), D 3,034 (60.68%), D0 2,397
  (47.94%), E 2,397 (47.94%); `fire_at` 0.05. It is the only firing pair at
  2026 in each arm. **Falsified.** This share is read from the run's own trace;
  it is not recomputed, because the per-pool party share draws the tripwire
  scans are not saved.

### P19

All re-derived. E's derived class weights: `under` 0.0, `at_or_over` 0.0. E ≡ D0
at 2026 (arrays and `30_centres`). E ≡ D at 24/24 panel city-years. The
inverse-variance run (scenario `bye_weight_mode` = `inverse_variance`) and the
`BYE_MIN_WEIGHT = 1.0` run are each identical to E. A5: ACP E centre = seed
0.000353 exactly, D 0.008412; T&S E centre = seed 0.000623 exactly, D 0.000814;
ACP mean seats E 0.102, D 2.325; T&S E 0.184, D 0.250. Direction (E − D): PA
16.31 → 15.20, DA 69.61 → 69.27, ANC 66.74 → 69.38. All held.

Under P19's original second bullet (superseded by A5, recorded only): T&S "from
about 0.11% to about 0.06%" read against D 0.081% → E 0.062%; ACP "returns to
about its arrival seed (0.050% list mean)" read against E's list mean 0.041%.
"About" has no bound, so neither is scorable as written.

---

## 3. Departures from the pre-registration

| departure | prereg said | done | does a verdict depend on it |
|---|---|---|---|
| C16 recipe and `git apply --check` | §3: a recipe that does not apply cleanly is reported before a run, never patched by hand without a dated note. A13: a recipe that fails `git apply --check` on W stops that arm. | `git apply --check -R` of cdcf517 fails at W and identically at acbd9f8, where §3.3 built it as a `--3way` application with one named conflict. The arm was built by §3.3's resolution, which reproduces the prereg's acbd9f8 hash; reported in `STEP11-RUNS.md` before any run; no dated note appended to the prereg. | **Yes.** B and C are built on C16 (§3: B = W + 3.3 + 3.4 + 3.5; C = W + 3.3 + 3.4). If A13 is read literally, C16, C and B are stopped, and these become not scorable: P16, P17 (D against C16), P11, P13 (B against A), CHANGE in B/C/C16, P12 clause 2-3 in B/C/C16, the P8 guard clause in B/C/C16, E3 for B/C/C16. Still scorable from A, B0, B6, B8, D, D0, E: E1, E2, E3/E4 (E), P1, P2, P2b, P3 (E), P6 (B6), P8 (B8), P12 in D/E (clause 3 still falsified there), P19, P10. If A13's check is read as the 3-way application §3.3 specifies (the only form that recipe could ever pass), every verdict above stands. |
| B6 tree hash | §3.1: cut `theirs` at `slate_coverage`'s `return out`; result diff sha256 `9ed8630ee0f952f6…`, 236 lines. | The cut as written gives 235 lines, `2e0d65f81b3b9205…`; the stated hash needs one blank line kept after `return out`. The stated hash was taken as the authority. | Only through what counts as arm B6. If the stated hash governs (as A6 rules for B8), B6 is the arm and P6 is scored as above. If the recipe text governs, the built tree is not the one described and P6 and B6's P1 counts are not scorable from it. The difference is one trailing newline at the end of `levels.py`; argued, not tested: it changes no compiled code, so the arrays would be the same. |
| P12's population | "In every run of B, C, C16 and E at a city-year the record covers". | The record covers 2016, 2021 and 2026, so 17 runs per arm; the 2011 runs report `"no record"`. | Clause 2 is held under the literal reading. If "covers" was meant as every panel city-year plus 2026 (25 runs), clause 2 is falsified at the eight 2011 runs per arm. |
| `seed_notes` count | E3 exempted `seed_notes` at the two 2026 specs only; A11 exempts it at every spec for band-deletion text. | 18 specs carry a `seed_notes` change: the 16 backtest 2016/2021 specs and the 2 Johannesburg 2026 specs (2d73de7's body said 18, its writer's table 16). | E3 is held under A11 and falsified at 16 specs under E3's first text. A11 was written after the window emit was inspected, before any arm ran. |
| Output paths | §2: `--run-dir` into the arm's scratch directory; isolation by tree and working directory. | Trees and their `data/processed` in the session scratch directory; raw outputs and traces written to `data/arms/step11/<arm>/` in the real tree (gitignored). The real tree's `data/processed`, `site/`, `content/`, `publications/`, `prereg/`, `src/`, `tests/` digests are reported unchanged (`STEP11-RUNS.md` §5; given). | No. Where a run writes its trace changes no drawn number (`--run-dir` is opt-in and asserted number-neutral by `test_chain`), and no run read from `data/arms/`. |
| `data/raw` read-only | §2: `data/raw` linked read-only. | Symlinked, not read-only at the filesystem; checked after the runs: no file newer than the pre-emit marker (given). | No, if nothing was written. The check is an mtime fence, which detects a write but is the weaker kind of evidence `CLAUDE.md` §4 names. |
| Three `-k chain` failures in B, C, C16 | §2: `-k chain` passes the named artefact-key test, and `test_the_specs_on_disk_agree_with_the_constructed_one` passes, not skips. | Both named tests passed in every tree. Three other chain tests failed in B, C, C16 (`bye_value.json is missing`: a 2026 run without the `w_bye` override, in trees that hold no file by design). | No under the literal reading (only the named tests are required). Under "`-k chain` passes as a whole", B, C, C16 failed the precondition; no arm run used the failing path, since every B/C/C16 run set `w_bye=0.4`. |
| D0 panel runs | Not specified (D0 is a 2026 control in P19). | Run at 24 city-years; no prediction reads them. D0's panel totals equal D's and E's (3.2572 / 2.9782 / 727). | No. |
| Arrays captured before `relabel_run` | §4 defines "identical" over drawn arrays, stage unstated. | Saved before `compare_history`'s relabel; scoring (`result.json`) is after it. My re-derivation applied the relabel and matched `result.json` at 240/240. | No. The relabel is a deterministic rename keyed by the actual result, the same in both arms of any comparison. |
| Per-draw tie classes | §2 describes the classifier. | Saved as a per-draw flag array; the classifier's inputs are not saved. | P1's counts rest on the run-time instrument; I verified its code against §2 and recounted from the flags, but could not reclassify. |

---

## 4. What the pre-registration did not predict

1. **The `PA|Coloured` tripwire fires at Johannesburg 2026 in every W-based arm**:
   B 67.86%, C and C16 61.08%, D 60.68%, D0 and E 47.94% of 5,000 draws above
   threshold 0.8123, against `fire_at` 0.05; the only firing pair at 2026. The
   prereg (P12, A3, §6) said it cannot fire under the owner's rule. Setting the
   by-election weight from 0.4 (D) to 0 (D0, E) lowers it by 12.7 points.
2. **The tripwire on the panel** (B): 19-89 firing pairs per 2016 run
   (buffalocity 19, mangaung 30, tshwane 35, nelsonmandelabay 51, ekurhuleni 60,
   joburg 62, ethekwini 75, capetown 89); 0-2 per 2021 run. The 2011 runs report
   `"no record"`: 2011 is not in the record.
3. **GOOD is not a 2026 ballot party in the arms that P17 compares**; RISE is
   recorded as merged with it. §1.3 tabulated a spine level for GOOD and P17
   predicted its seat gain.
4. **Item 11a moves list MAE at the city-year level more than the panel mean
   shows**: 18 of 24 city-years by ≥ 0.05, up to 0.603, against a panel
   mean of −0.0115 and §1.3's measured spine change (90th percentile |Δlog|
   0.0096). At 2026 the largest seat mover under 11a is the EFF (+0.98), not the
   PA (−0.78).
5. **Item 17 moves the EFF down** (−0.84 seats) and the IFP up (+0.19), neither
   a spine-level riser in the prediction.
6. **Item 6's ward MAE gains are uneven**: four city-years worsen by more than
   0.15 (ethekwini 2016 +0.4248, capetown 2021 +0.2499, ethekwini 2021 +0.1762,
   joburg 2021 +0.1541) while mangaung 2011 improves by 1.8748, which is 0.078
   of the panel-mean fall of 0.0891 (1.8748 / 24).
7. **Item 8 raises list MAE where the entered mass is largest**: ekurhuleni 2011
   +0.940, mangaung 2021 +0.611, joburg 2011 +0.651, tshwane 2011 +0.478,
   ethekwini 2011 +0.466, capetown 2016 +0.441.
8. **E against D at 2026, beyond the three predicted directions**: ANC +2.64,
   EFF +2.58, ACP −2.22, ASA −1.41, PA −1.11, IFP −0.61, DA −0.35 mean seats.
9. **Floating-point weight differences in the 2026 specs**: 29 (spec) and 45
   (simulation spec) non-SACP member weights differ by at most 1.11e-16 and
   2.22e-16.
10. **Turnout bands (item 10's review, no prediction)**: arm B's drawn q5-q95
    at Johannesburg 2026 is Coloured 33.4-72.7% and Indian/Asian 20.1-71.5%
    against observed LGE ranges 33.0-64.8% and 16.0-58.5% (re-derived for this
    row from `pool_turnout_draws`; the other rows of `turnout_B.json` given).

---

## 5. Re-derived and taken as given

Re-derived from raw arrays, traces, specs or a read-only re-run: every number in
§1 except those listed below; the 240 panel scores (matched `result.json`
exactly); all identity checks; the spec field diffs; `unopposed_wards` in four
trees; the window tuples; the guard lists; the seeds and centres.

Taken as given, with source:
- P1's per-draw tie classes (the run-time instrument's saved flags; counts
  recomputed from them, classification not re-run).
- P12's `PA|Coloured` draw counts and threshold (`41_guards` in each run's
  trace; the per-pool draws are not saved).
- P2b's per-city-year baseline errors (`result.json` `opponents`; summed here).
- B4's ward-hit counts (`result.json` `wards`).
- A4's three test outcomes, arm A's `SHA256SUMS` check, the `data/raw` mtime
  check and the real-tree digests (`STEP11-RUNS.md`).
- The turnout table rows other than Johannesburg 2026 (`turnout_B.json`).
