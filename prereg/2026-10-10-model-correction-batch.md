# Pre-registration: the model correction batch, arms A to E (step 9)

Written 2026-10-10, before any arm is emitted or run. Not to be edited after
the first arm runs; it is scored as written, including what it falsifies.

Sources: `audits/2026-10-09-model-fixes/spec/SPEC.md` §6 (the draft), §6a, §7,
R2.5 (arms revised), R2.6 and the R3.x notes; `BRIEF.md` and every owner
decision in it; `reviews/M2-SUMMARY.md` (B1, N4), `reviews/M3-SUMMARY.md` (the
window rule; the tripwire cannot fire for the PA in the Coloured pool),
`reviews/M4-SUMMARY.md` (arm E; `EXPECTED_INERT`);
`prereg/2026-10-10-byelection-value-test.md` (scored); MODEL-LOG §1.295; the
step 9 writer brief, `reviews/STEP9-WRITER-BRIEF.md`.

Every prediction is about the world or the mechanism. Where a figure from an
earlier measurement sizes an expected change, the line says so and says why
the mechanism ties it to the world. An arm compared with another arm is two
fresh runs of this batch's measurement; neither is a standard of correctness.
The standard is the backtest against real results (`CLAUDE.md` §1,
`ITERATING.md`).

Three kinds of evidence, labelled where used: **measured** (a probe printed it,
command given), **read** (a file or the code says it), **argued** (neither).

---

## 1. Measured before this was written

All of it read-only, run from the repository root at `acbd9f8` unless a tree
is named, `PYTHONHASHSEED=0`, nothing written under `data/`, `site/`,
`content/` or `publications/`. Scripts lived in this session's scratch
directory; each is described here completely enough to rebuild, and the
composition it performs is stated in full.

### 1.1 B1: item 8's population, on each city-year's own previous LGE

SPEC P8's panel list and O5's no-record counts came from a probe that read
Johannesburg's previous LGE for every city (M2 review B1). Re-measured here
through the model's own functions, imported, composed in `run_model`'s order
(`montecarlo.run_model` at `acbd9f8`, the baseline block through the
`roster_universe_check` call):

1. `fold.load` + `fold.citywide` on `target.results(target.previous_npe)`
   (the national baseline);
2. `montecarlo.roster_for_target(target, scenario)`, with `scenario` carrying
   the pool spec's `roster` and `roster_source` (read from the spec file, not
   run; only the 2026 target uses them);
3. `pools.apply_mergers(baseline, roster, year)`, then every party in
   `levels.absent_from_ballot(baseline, roster)` removed;
4. `fold.load(..., "PR")` + `fold.citywide` on
   `target.results(target.previous_lge)`, then `pools.apply_mergers` on it
   (`prior_pr_share`);
5. `levels.local_record_only(roster, baseline, prior_pr_share, seeds)`, with
   `seeds` the spec's `seeds` field (read, not run);
6. `montecarlo.roster_universe_check` twice: once on the universe arm A builds
   (baseline plus seeds plus `ENTRANT` where no arrival is named), where it
   refuses naming exactly step 5's list at every city-year that has one; and
   once with step 5's parties added, which returns the no-record residual.

Population: every target `compare_history.runnable` returns for the eight
cities in `compare_history.CITIES` (24 city-years), plus Johannesburg 2026.

Two limits, stated here because both lists depend on them:
- The seeds are the **pre-window** specs' (emitted by pre-batch code). The
  classification of step 5 is identical with the seeds removed at every one
  of the 25 targets (measured), so it does not depend on them. The no-record
  residual does: a party seeded at a target is "with record". The 2011 specs
  carry no seeds, which is why the residual exists at 2011 only.
- Cross-check, a **probe, not a measurement**: `run_model` in-process at
  capetown 2011, capetown 2021, ekurhuleni 2011 and mangaung 2021, 20 draws,
  through `scenario["allow_stale_pools"] = True` on the current stale specs.
  Its `_local_record_only` and `41_guards.roster_unrepresented` equal the
  composition's lists at all four. No other output of those runs is used.

**Item 8's class: roster parties with a previous-LGE list vote, no national
baseline and no seed** (each party's previous-LGE list share in brackets, %):

| city-year | previous LGE | parties item 8 enters | together, % of the previous LGE list |
|---|---|---|---|
| buffalocity 2011 | 2006 | none | 0 |
| buffalocity 2016 | 2011 | PAN_AFRICANIST_MOVEMENT (0.2315) | 0.2315 |
| buffalocity 2021 | 2016 | none | 0 |
| capetown 2011 | 2006 | ABOLITION_OF_INCOME_TAX_AND_USURY_PARTY (0.0453) | 0.0453 |
| capetown 2016 | 2011 | AFRICA_MUSLIM_PARTY (0.2827), CAPE_MUSLIM_CONGRESS (0.2453), CAPE_PARTY_KAAPSE_PARTY (0.1317), NATIONAL_PEOPLE_S_PARTY (0.0633) | 0.7230 |
| capetown 2021 | 2016 | CAPE_MUSLIM_CONGRESS (0.2715), DEMOCRATIC_INDEPENDENT_PARTY (0.2784), PA (0.1616), PEOPLE_S_DEMOCRATIC_MOVEMENT (0.0189), SIZWE_UMMAH_NATION (0.0227), THE_GREENS (0.0347) | 0.7878 |
| ekurhuleni 2011 | 2006 | CHRISTIAN_DEMOCRATIC_PARTY (0.1699), DISPLACEES_RATE_PAYERS_ASSOCIATION (1.4309), INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA (0.3507), SIMUNYE_IN_CHRIST_ORGANISATION (0.3587), THEMBISA_CONCERNED_RESIDENTS_ASSOCIATION (0.2110) | 2.5212 |
| ekurhuleni 2016 | 2011 | INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA (0.3243) | 0.3243 |
| ekurhuleni 2021 | 2016 | INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA (0.1356) | 0.1356 |
| ethekwini 2011 | 2006 | AZAPO (0.2386), TRULY_ALLIANCE (0.6997) | 0.9384 |
| ethekwini 2016 | 2011 | none | 0 |
| ethekwini 2021 | 2016 | ACADEMIC_CONGRESS_UNION (0.0440), ALLIED_MOVEMENT_FOR_CHANGE (0.0779), INDEPENDENT_PEOPLE_S_PARTY (0.1356), MINORITIES_OF_SOUTH_AFRICA (0.2732), TRULY_ALLIANCE (0.4242) | 0.9550 |
| joburg 2011 | 2006 | CHRISTIAN_DEMOCRATIC_PARTY (0.2151), CHRISTIAN_FRONT (0.1878), OKM (0.4537) | 0.8566 |
| joburg 2016 | 2011 | ALJAMAAH (0.2717), OKM (0.2529), THE_SOCIALIST_PARTY_OF_AZANIA (0.0285) | 0.5531 |
| joburg 2021 | 2016 | BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA (0.0045) | 0.0045 |
| mangaung 2011 | 2006 | none | 0 |
| mangaung 2016 | 2011 | DIKWANKWETLA_PARTY_OF_SOUTH_AFRICA (0.2535), UNITED_RESIDENTS_FRONT (0.1357) | 0.3892 |
| mangaung 2021 | 2016 | AGENCY_FOR_NEW_AGENDA (1.5747), BOTSHABELO_UNEMPLOYED_MOVEMENT (0.1208), UNITED_CHRISTIAN_DEMOCRATIC_PARTY (0.2845), UNITED_RESIDENTS_FRONT (0.0885) | 2.0686 |
| nelsonmandelabay 2011 | 2006 | UNITED_INDEPENDENT_FRONT (0.4367) | 0.4367 |
| nelsonmandelabay 2016 | 2011 | CHRISTIAN_DEMOCRATIC_PARTY (0.1631) | 0.1631 |
| nelsonmandelabay 2021 | 2016 | PA (0.2917), UNITED_FRONT_OF_THE_EASTERN_CAPE (0.8011) | 1.0928 |
| tshwane 2011 | 2006 | CHRISTIAN_DEMOCRATIC_PARTY (0.3064) | 0.3064 |
| tshwane 2016 | 2011 | AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE (0.0875), CHRISTIAN_DEMOCRATIC_PARTY (0.1070), MOVEMENT_DEMOCRATIC_PARTY (0.0337) | 0.2282 |
| tshwane 2021 | 2016 | AFRICAN_MANDATE_CONGRESS (0.0889), CHRISTIAN_DEMOCRATIC_PARTY (0.0572), FORUM_4_SERVICE_DELIVERY (0.0407) | 0.1869 |
| joburg 2026 | 2021 | AMALGAMATED_RAINBOW_MOVEMENT (0.0273), CHANGE (0.0380), ECONOMIC_EMANCIPATION_FORUM (0.0376), INTERNATIONAL_REVELATION_CONGRESS (0.0892), SHOSHOLOZA_PROGRESSIVE_PARTY (0.0162), THE_ORGANIC_HUMANITY_MOVEMENT (0.0425), UIM (0.1258) | 0.3766 |

Item 8 enters parties at **20 of the 24** panel city-years; the four where it
enters none are buffalocity 2011, buffalocity 2021, ethekwini 2016 and
mangaung 2011.

**The no-record residual (O5): roster parties with no previous-LGE list vote,
no national baseline and no seed**, which `41_guards.roster_unrepresented`
records. Non-empty at seven city-years, all 2011; empty at the other 17 and at
Johannesburg 2026:

| city-year | count | parties |
|---|---|---|
| capetown 2011 | 15 | AFRICAN_BOND_OF_UNITY, CAPE_MUSLIM_CONGRESS, COMMUNITY_COALITION, DEMOCRATS_FOR_CHANGE, INDEPENDENT_CIVIC_ORGANISATION_OF_SOUTH_AFRICA, NATIONAL_ALLIANCE_FOR_DEMOCRACY, NATIONAL_INDEPENDANT_CIVIC_ORGANISATION, NATIONAL_PEOPLE_S_PARTY, NFP, PAN_AFRICANIST_MOVEMENT, SOCIAL_DEMOCRATIC_PARTY, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION, UNITED_MAJORITY_FRONT, UNIVERSAL_CIVICS_OF_SOUTH_AFRICA, WESTERN_CAPE_COMMUNITY |
| ekurhuleni 2011 | 8 | BLACK_CONSCIOUSNESS_PARTY, FIRST_NATION_LIBERATION_ALLIANCE, NATIONAL_REPUBLICAN_PARTY, NFP, PAN_AFRICANIST_MOVEMENT, PEOPLE_S_CIVIC_ORGANISATION, THE_REAL_CONGRESS, UMHLABA_UHLAGENE_PEOPLES_UNITED_NATIONS |
| ethekwini 2011 | 7 | AFRICAN_CHRISTIAN_ALLIANCE_AFRIKANER_CHRISTEN_ALLIANSIE, BLACK_CONSCIOUSNESS_PARTY, NFP, SOCIALIST_GREEN_COALITION, SOLIDARITY_PARTY, UNITED_ACTION_FRONT, UNITED_RESIDENTS_FRONT |
| joburg 2011 | 7 | ALJAMAAH, BLACK_CONSCIOUSNESS_PARTY, LIBERAL_DEMOCRATIC_PARTY, NFP, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION, THE_SOCIALIST_PARTY_OF_AZANIA, UNITED_RESIDENTS_FRONT |
| tshwane 2011 | 4 | BLACK_CONSCIOUSNESS_PARTY, CHRISTIAN_FRONT, INDEPENDENT_RATEPAYERS_ASSOCIATION_OF_SA, NFP |
| nelsonmandelabay 2011 | 3 | AFRICAN_COMMUNITY_MOVEMENT, CHRISTIAN_DEMOCRATIC_PARTY, SOUTH_AFRICAN_PROGRESSIVE_CIVIC_ORGANISATION |
| mangaung 2011 | 2 | BLACK_CONSCIOUSNESS_PARTY, UNITED_RESIDENTS_FRONT |

The guard's `extra` direction (a universe party not on the roster) is empty
at all 25 targets (measured, same composition).

### 1.2 The item-16 windows, under the window rule

`levels.size_window(target, levels.theta_record, record=levels.theta_record(target))`
and `levels.size_window(target, levels.local_record)` at `acbd9f8`, for each
target year (the records are pooled over `levels.METRO_CODES`, so the window
is one per year and route, the same for every city):

| target | θ: h, status, best, scored, cycles | ρ: h, status, best, scored, cycles |
|---|---|---|
| 2011 | inf, underdetermined, —, 83, 1 | inf, underdetermined, —, 0, 0 |
| 2016 | inf, derived, inf, 168, 2 | inf, underdetermined, —, 74, 1 |
| 2021 | inf, derived, 2.0, 265, 3 | inf, derived, 0.25, 165, 2 |
| 2026 | inf, derived, 1.5, 403, 4 | inf, derived, 0.5, 283, 3 |

This is not blind: the M3 fix-round addendum (SPEC R3.6) already reported
every window infinite on the current archive. The mechanism: with at most four
cycles, the cluster-robust standard error carries one to three degrees of
freedom, so no wider window is measurably worse than the best, and the rule
takes the widest grid value.

### 1.3 Spine levels per arm at Johannesburg 2026 and on the panel

Each arm's own `levels.spine` (the arm trees of §3), on inputs composed as in
§1.1 plus `run_model`'s next steps: item 8's parties entered at their
previous-LGE list share, the pre-window spec's seeds added
(`max(base + seed, 0)`), the spine called on that baseline minus item 8's
parties with `prev_local = prior_pr_share`, `k = levels.SPINE_K`,
`read_local_only` = item 8's parties, and `h_theta = h_rho = inf` (§1.2).
The spine level is before by-elections, the shrink and renormalisation. A
seeded party's spine level does not reach its centre (it takes its seed), so
seeded parties are marked and set aside.

- **Arm B reproduces the pre-11a estimator exactly**: the spine at
  Johannesburg 2026 on arm B's `levels.py` equals the spine on `b033b35`'s
  `levels.py` (the commit before item 11a) for all 109 parties.
- **C16 equals C**: identical for all 109 parties (the windows are infinite).
- Johannesburg 2026, spine level in %, and the change in natural log:

| party | B | C | D, E | Δlog 11a (C vs B) | Δlog 17 (D vs C16) |
|---|---|---|---|---|---|
| DA | 30.875 | 30.881 | 30.881 | +0.000 | +0.000 |
| ANC | 27.992 | 28.073 | 28.073 | +0.003 | +0.000 |
| ASA | 13.509 | 13.509 | 13.066 | +0.000 | −0.033 |
| EFF | 12.233 | 12.199 | 12.199 | −0.003 | +0.000 |
| MK | 11.309 | 11.309 | 9.931 | +0.000 | −0.130 |
| PA | 6.427 | 6.047 | 6.047 | −0.061 | +0.000 |
| RISE | 1.597 | 1.597 | 1.663 | +0.000 | +0.041 |
| IFP | 1.337 | 1.348 | 1.348 | +0.008 | +0.000 |
| BOSA | 0.942 | 0.942 | 1.027 | +0.000 | +0.087 |
| VFPLUS | 0.764 | 0.768 | 0.768 | +0.006 | +0.000 |
| ATM | 0.354 | 0.356 | 0.361 | +0.003 | +0.015 |
| AHC | 0.317 | 0.317 | 0.345 | +0.000 | +0.082 |
| AIC | 0.312 | 0.319 | 0.319 | +0.022 | +0.000 |
| GOOD | 0.249 | 0.249 | 0.272 | +0.000 | +0.090 |
| UDM | 0.128 | 0.130 | 0.130 | +0.013 | +0.000 |

  Other unseeded parties moved by 11a by 0.01 or more in log, all under 0.1%:
  AGENCY_FOR_NEW_AGENDA +0.089, BOLSHEVIKS_PARTY_OF_SOUTH_AFRICA −0.058, NFP
  +0.053, FORUM_4_SERVICE_DELIVERY +0.045, INTERNATIONAL_REVELATION_CONGRESS
  −0.032, COPE +0.031, AGANG −0.020, APC +0.013, AZAPO +0.013. Under item 17:
  national-only small parties DUDULA +0.283, UNITED_AFRICANS_TRANSFORMATION
  +0.253; local-only parties (PARTY_OF_ACTION, ABANTU_BATHO_CONGRESS, UIM, DOP,
  BLACK_FIRST_LAND_FIRST and others) +0.12 to +0.19, all under 0.11%.
- Panel (24 city-years, unseeded parties at 0.1% or more in any of B, C, E):
  11a, 346 party-city-years, median |Δlog| 0.001, 90th percentile 0.0096,
  no party at 0.5% or more moved by 0.10 or more. Item 17, the same 346,
  median 0.000, 90th percentile 0.118; at 0.5% or more and |Δlog| ≥ 0.10:
  AGANG joburg 2016 (0.449% → 0.511%), NFP ethekwini 2016 (2.464% → 2.783%),
  NFP ekurhuleni 2016 (0.624% → 0.554%).

### 1.4 Every arm tree builds and runs

Each tree of §3 was imported and run for 20 draws (the 597ec38-based trees on
the current specs, which they only warn about; the `acbd9f8`-based trees
through `allow_stale_pools` and `--set w_bye=0.4`) at mangaung 2016 and
Johannesburg 2026, the `acbd9f8`-based trees also at Johannesburg 2011. All
ran. This was a buildability probe: no number from it was printed or kept.

---

## 2. The runs (step 11)

- **Panel:** the 24 city-years `compare_history.runnable` returns, each through
  `compare_history.run_city_year` in-process (no `history.json` written),
  1,000 draws, the seed `run_city_year` uses (`seed=None`, so
  `DEFAULTS["seed"]`), `PYTHONHASHSEED=0`.
- **Johannesburg 2026:** `montecarlo.run_model` in-process with the scenario
  `load_scenario` builds after `apply_city`, 5,000 draws, `DEFAULTS["seed"]`,
  `PYTHONHASHSEED=0`, with `--run-dir` into the arm's scratch directory so the
  stage payloads can be compared.
- **Isolation.** Each arm runs in its own scratch tree: a checkout built as §3
  says, its own copy of `data/processed` (never shared, never a symlink to
  another arm's), `data/raw` linked read-only, the working directory set to
  the tree. `run_model` reads the pool spec from `target.city.processed`
  (`data/processed[/<slug>]` relative to the working directory); the
  `processed` argument redirects turnout, γ and by-election files only. Arms
  are therefore separated by tree and working directory, never by a
  `processed` argument.
- **Specs.** Arm A reads the pre-batch specs. Every other arm emits its own
  into its tree with `POOLS-REEMIT-QUEUE.md` step 2's loop (every
  city-year, both Johannesburg 2026 specs, Tshwane 2026), then
  `group_share_record.py --emit` where the arm has item 12 (B, C, C16, E), and
  `bye_value.py --emit` in E's tree. Before any run in a tree:
  `tests/run_all.py -k chain` passes
  `test_every_emitted_pool_spec_carries_a_current_artefact_key` in that tree,
  and `test_artefact_key_discriminates::test_the_specs_on_disk_agree_with_the_constructed_one`
  passes (not skips) in the `acbd9f8`-based trees.
- ⛔ **Arm A's specs must be copied before the window.** Step 10 overwrites
  `data/processed/pools_*.json` in the repository. Before the window's first
  emit, `data/processed` is copied into arm A's tree and the sha256 of every
  `pools_*.json` recorded; arm A runs on that copy.
- **Every run of every arm** records `02_pools_artefact.stale_reason` null
  (and `ModelRun`'s `_pools_stale` None). Arms A, B0, B6, B8 contain no
  refusal and only warn, so this is asserted from the trace or the run, not
  inferred from the run completing. A run that reports a stale spec is not a
  measurement and is re-done after a correct emit.
- **Instruments added for the measurement, not to the model:**
  - **The tie classifier (P1).** A wrapper around `montecarlo.allocate`,
    installed for the run as `test_stage_realisation`'s real-trace test
    installs one, delegating unchanged and accepting any keyword (arm A's
    `allocate` has no `lot`). For each call it computes, on the call's
    `combined`, `total_seats`, `independent_wards`, `no_pr_list_wards`:
    `available`, `quota = total // available + 1`, whole-vote surplus
    `v − (v // quota) · quota`, `shortfall`, the ranking by
    `(−surplus, −votes)`, and the pair straddling the cut
    (`ranked[shortfall − 1]`, `ranked[shortfall]`). The call is in class
    **lot** if the pair is equal on surplus and on votes, class **item 2** if
    equal on surplus and unequal on votes, otherwise untied (the logic of
    `tests/test_stage_realisation.py::tie_at_the_cut` at `acbd9f8`, extended to
    the unequal-votes class). A second wrapper around
    `montecarlo.allocate_with_overhang` numbers the draws, so each call is
    assigned to its draw. A draw is in **population 1** if any of its calls is
    in class lot or item 2, in **population 2** otherwise.
  - **Rule A (P2):** each arm's own
    `audits/2026-10-07-prediction-restructure/backtest/rule_a.py` (at 597ec38
    it breaks a tie by name; from 954086b it passes the lot).
- **Turnout band review (item 10, SPEC §1.9):** the table of drawn turnout
  q5/q95 per pool and citywide against the observed range is computed from arm
  B's runs and reported in the batch's MODEL-LOG entry. No prediction.

---

## 3. The arms and how each is built

Base commits: **597ec38** (the tree before the batch) and **W**, the commit at
which step 11 runs. Every recipe below for the W-based arms was built and
checked against `acbd9f8`. If W's `src/` differs from `acbd9f8`'s (a fix from
the step 8 review), each recipe is re-applied with `git apply --check`, the
tree hashes below no longer apply, and any recipe that does not apply cleanly
is reported before a run; none is patched by hand without a dated note
appended here.

**Tree hash**: `find src -type f -name '*.py' | LC_ALL=C sort | xargs cat |
shasum -a 256`, first 16 hex characters, on the tree built at `acbd9f8`.

| arm | what it contains | code state | `w_bye` | specs | tree hash |
|---|---|---|---|---|---|
| **A** | the tree before the batch | `git archive 597ec38` | the city file's 0.4 | pre-batch, copied before the window | `7a0d39ae11e41fce` |
| **B0** | A + items 1-2 (and 4-5, which are a test and records) | `git archive 954086b` (the only commit after 597ec38 and up to 954086b that touches `src/`, `cities/` or `judgements/` is 954086b) | 0.4 | own emit | `0983a6f0b3fbf0aa` |
| **B6** | A + item 6 | 597ec38 + recipe 3.1 | 0.4 | own emit | `0ea073d69372edb7` |
| **B8** | A + item 8 (with the M2 fix round's report filter) | 597ec38 + recipe 3.2 | 0.4 | own emit | `d2b3afbdb9bfa09d` |
| **B** | items 1-6, 8-10, 12, 18 | W + recipe 3.3 + 3.4 + 3.5 | `--set w_bye=0.4` | own emit, record | `a4574cf3542727e9` |
| **C** | B + 11a | W + recipe 3.3 + 3.4 | `--set w_bye=0.4` | own emit, record | `33acd90bb91ba1a2` |
| **C16** | C + 16 | W + recipe 3.3 | `--set w_bye=0.4` | own emit, record | `e2ab33c6ebdd48d6` |
| **D** | C16 + 17 | W unchanged | `--set w_bye=0.4` | E's tree | = E |
| **D0** | control: D at weight 0 | W unchanged | `--set w_bye=0` | E's tree | = E |
| **E** | D + 19: everything | W unchanged | derived (`bye_value.json`) | own emit, record, `bye_value.py --emit` | `ddb9a6d3714ae29a` |

B, C, C16, D, D0 and E share draws and seeds (same draw count and seed, same
code outside the item under test). A, B0, B6 and B8 share draws and seeds
with each other.

**Why `w_bye` is set in B to D.** Every W-based tree carries item 19's wiring,
which reads the class weights from `bye_value.json` when `w_bye` is not set.
Without an override, arms B to D would be arm E at Johannesburg 2026. Before
item 19 the weight was `w_bye = 0.4` in `cities/joburg.toml` (read at
597ec38; deleted in e0ce282). `--set w_bye=0.4` is the override path
`DEFAULTS` documents: `bye_weight` returns `(0.4, "override")`,
`bye_weight_mode` stays `"fixed"`, and `run_model` skips the file
(`if bye and scenario["w_bye"] is None`). 1cb5cad's refusal is for a city
file, not `--set` (read; the probe of §1.4 ran with it). On the panel `bye` is
empty at every city-year, so the setting moves nothing there.

**D0** is added because the brief and `M4-SUMMARY.md` state that arm E equals
arm D on every centre and every draw. That holds for D at weight 0, not for D
at the pre-item-19 weight 0.4, where P19's second bullet (kept as written)
predicts differences. Both are pre-registered (§4, P19).

### 3.1 B6: item 6 alone on 597ec38

Item 6 and item 8 share commit 2933c2e. B6 takes the item-6 hunks of
`git show 2933c2e -- src/levels.py src/montecarlo.py`, split at each `@@`
line, in this order (0-based):

| # | file | hunk header | item |
|---|---|---|---|
| 3 | levels.py | `@@ -1572,7 +1579,15 @@ def contestation(` | 6 (`_result_slates` split out) |
| 4 | levels.py | `@@ -1584,8 +1599,67 @@ def contestation(` | 6 (`slate_coverage`) |
| 8 | montecarlo.py | `@@ -3870,6 +3887,84 @@ def _projected_roster_declaration(` | 6 and 8: defines `slate_change_ratio` and `roster_universe_check`; the second is never called in B6 |
| 9 | montecarlo.py | `@@ -4280,12 +4375,15 @@ def run_model(` | 6 (`slate_coverage` for `now` and `was`) |
| 10 | montecarlo.py | `@@ -4352,7 +4450,7 @@ def run_model(` | 6 (note text) |
| 16 | montecarlo.py | `@@ -4839,16 +4967,25 @@ def run_model(` | 6 (the cap, `slate_change_ratio`) |

Applied with `git apply --3way` on a clone at 597ec38. `montecarlo.py` applies
cleanly. `levels.py` conflicts once, because the 3-way merge carries item 3's
`UNOPPOSED WARDS` section (not in B6) in as context. Resolution, exactly:
replace the conflict block with the `theirs` side cut just before the line
`# UNOPPOSED WARDS` (and its preceding blank lines and rule line), which ends
the block at `slate_coverage`'s `return out`. Result: `git diff 597ec38 -- src`
has sha256 `9ed8630ee0f952f6…`, 236 lines.

### 3.2 B8: item 8 alone on 597ec38

The remaining hunks of the same split: 0, 1, 2 (levels.py: `spine`'s
`read_local_only` and the F6 comment), 5 (levels.py: `local_record_only`),
6, 7 (montecarlo.py: `make_drawer`'s `level_sd_default` record, SPEC R3.7),
8 (as in B6; `slate_change_ratio` is never called in B8), 11, 12, 13, 14, 15
(the previous-LGE read hoisted, the classification, the seed-placement loop,
the guard), 17 (the spine call), 18 (the two `41_guards` fields). Applied with
`git apply --3way` on 597ec38; two conflicts, resolved exactly:

- `levels.py`: keep `ours`, then append from `theirs` only the text from
  `def local_record_only(` to the end of the block (drop item 3's
  `UNOPPOSED WARDS` section, carried in as context).
- `montecarlo.py`, the `41_guards` dict: keep `ours`
  (`"bounds_checked": bounds_checked,`; item 10's per-party dict and `draws`
  key are not in B8), then add
  `"roster_unrepresented": roster_unrepresented,` and
  `"level_sd_default_parties": sorted(p for p in draw_target.level_sd_default if p in index),`
  (the second with 03e0b3c's S1 filter; the rest of 03e0b3c's `src` changes
  to these files are messages and a comment).

Result: `git diff 597ec38 -- src` sha256 `eea149ebfa404314…`, 341 lines.

### 3.3 C16: item 17 removed from W

On a clone at W: `git show 6074382 -- src | git apply -R --3way` (applies
cleanly; it restores `level_sd_default`, which item 17 made inert and the
owner deleted, and without which a no-record party has no width), then
`git show cdcf517 -- src | git apply -R --3way` (`levels.py` clean;
`montecarlo.py` one conflict). Resolution, exactly: `cdcf517`'s side of the
conflict is empty; keep `ours` up to the line `def level_shock_sd(` and drop
from there to the end of the block. The kept part is the later group-share
functions (451e02a, 3c4efad); `level_shock_sd` is item 17's. No reference to
`level_shock_sd` or `levels.size_sd` remains in `src/`. Result:
`git diff acbd9f8 -- src` sha256 `81d681500680923d…`, 361 lines. Item 8's
parties take `level_sd_default` in C16, as before item 17 (SPEC R3.7).

### 3.4 C: item 16 switched off on C16

In `montecarlo.run_model`, after the line
`_h_rho, _win_rho = _levels.size_window(target, _levels.local_record)`,
insert:

```python
        # ARM C (step 9 prereg): item 16 off, no size filter on either route.
        _h_theta = _h_rho = float("inf")
        _win_theta = dict(_win_theta, h="inf", arm="C: forced inf")
        _win_rho = dict(_win_rho, h="inf", arm="C: forced inf")
```

`theta_prior`, `spine` and the trace then read no filter. Since §1.2 measured
every window infinite, this changes only the trace's window report; it is
built so that C16 against C is a test, not an identity by construction.
Result against `acbd9f8`: sha256 `618f9e961bf9d4a2…`.

### 3.5 B: item 11a switched off on C

In `src/levels.py`, two lines:

- `theta_prior`: `if size > 0.0:` → `if False:  # ARM B (step 9 prereg): item 11a off`
  (the `else` branch takes `_observed_size(own)` with an infinite window);
- `_shrunk`: `size = float(current.get(party, 0.0) or 0.0)` →
  `size = 0.0  # ARM B (step 9 prereg): item 11a off, observed size`.

The size centre is then taken at the reliability-weighted size the party's own
ratios were measured off, as before 43f9ddb; with item 17 removed and the
window infinite, the estimator equals `b033b35`'s (§1.3, all 109 parties at
Johannesburg 2026; G13 asserts the same on constructed records). The
`size_fallback` counter then counts every party; it is a report. Result
against `acbd9f8`: sha256 `d39643bc448d055d…`.

### 3.6 What no arm separates

Items 3, 4, 5, 9, 10, 12 and 18 have no arm of their own. Item 18 (the SACP)
is scored on B against A for the SACP's own figures only (P13). Items 3, 9 and
10 are argued null, with the M2 reviewer's measurement that at mangaung 2011
and ethekwini 2016 every array is identical once item 6 is reverted
(`M2-SUMMARY.md`), and G7, G10, G12, G17 as the tests. B against A, and B6 and
B8 against A, are therefore attributed jointly where noted.

---

## 4. Predictions and how each is scored

"Identical" means every drawn array (the two share-draw arrays, the two vote
arrays, the seat draws, the ward winners) equal element for element.
"List MAE", "ward MAE" and "coherent seat error" are `compare_history`'s
`pr_mae`, `ward_mae` and `seat_abs_err_coherent`. Seat figures are mean seats
over draws.

### Specs and records emitted in each tree (SPEC §5's neutrality check)

- **E1.** B0's emitted specs are byte-identical to arm A's copied specs,
  including `artefact_key` (954086b changes no file `pools.py` hashes).
- **E2.** B6's and B8's specs equal A's except `artefact_key.deps_sha`.
- **E3.** B, C, C16 and E: every spec equals A's except `artefact_key`
  (`pools_sha`, `deps_sha`, `cities_sha`; `judgements_sha` at the two
  Johannesburg 2026 specs), the removed `seed_bands` field, and at
  `pools_2026.json` and `pools_2026_simulation.json` the fields SPEC §5 names
  (`seeds`, `seed_notes`, `seeded_arrival_mass`, the SACP's pool membership,
  and fields derived from those). C's and C16's specs are byte-identical to
  each other (the C switch is in `montecarlo.py`, outside the emit's
  dependencies). `group_share_record.json` has identical `cities` content in
  B, C, C16 and E.
- **E4.** The 2011 specs emitted in B to E carry no seeds, as the pre-window
  ones do (§1.1's residual depends on it).

Holds: every clause. Falsified: any other differing field. A falsified E
clause is investigated before the arms that read those specs are scored.

### Item 10 (all arms): the stale-spec refusal

- **P10.** No run of any arm reports a stale spec (`stale_reason` null); no
  run of B to E refuses; no arm's draws move because of item 10 (argued: the
  refusal and the per-party `bounds_checked` read no random number and change
  no drawn value; G10 and G12 test them; no arm separates item 10).

Holds: the first two clauses. The third is argued and is not scored.

### P1 (items 1, 2): ties at the cut, per R3.1

- Johannesburg 2026, A against B0: every draw in population 2 has an
  identical seat vector, and every vote and share array is identical in every
  draw. Population 1 is counted in each of A and B0 (and reported for every
  arm), split into class item 2 and class lot.
- Prediction: population 1 is more than 0 draws in A at Johannesburg 2026;
  class lot is under 2% of draws in every arm. (The M1 review measured 5 of
  5,000 published councils moved by item 2: not blind for class item 2.)
- The panel, A against B0: the same identity in population 2 at all 24
  city-years.

Holds: identity in population 2 everywhere, both counts within the stated
ranges. Falsified: any population-2 draw whose seats differ, any vote array
that differs, class lot at 2% or more in an arm, or population 1 empty in A at
2026.

### P2 (items 1, 2): rule A on the panel, A against B0

- Rule A's prediction (each arm's own `rule_a.py`) under B0 differs from A's
  only at city-years where its own ward calls or seat calls meet a tie (a
  ward tied in the count of simulations, or a seat call in class lot or item
  2). Tied wards: 0 at all 24 city-years in both arms (the record of
  MODEL-LOG §1.291; a non-zero count falsifies that record).
- Johannesburg 2016: rule A's seat call meets the exact tie §1.291 records
  (AIC and TRULY_ALLIANCE equal on 3,743 votes); rule A's seat error under B0
  differs from A's by 0 or 2 seats, the lot choosing one of the two
  allocations of the tied seat.
- **P2b.** The `uniform-swing+roster` baseline's panel total under B0 lies in
  [837, 841], the span of the name rule and its mirror (the lot chooses among
  the same alternatives).

Holds / falsified: as stated, clause by clause.

### P3, P4, P5, P9 (items 3, 4, 5, 9): nulls

- Item 3: `levels.unopposed_wards` returns `{}` at all 24 city-years and at
  Johannesburg 2026 in B to E; no run refuses for an unopposed ward.
- Items 4, 5: a test and records; no model number moves. Not scored on arms.
- Item 9: no arm isolates it; argued null (§3.6). Not scored.

Holds: item 3's clause. Falsified: a non-empty result or a refusal.

### P6 (item 6): `PREREG-ward-list-fix.md`, plus the cap

F1-F6 and B1-B4 as written in
`audits/2026-10-09-model-questions/PREREG-ward-list-fix.md`, scored on B6
against A (2026 at 5,000 draws and the panel at 1,000, not the 1,000-draw
seed-20261104 runs that file names; its interval predictions are about means
and per-draw envelopes, which the draw count does not move). F2, F4 and F5
are also reported on B against A, where items 8 and 18 move the same draws,
and are not scored there. The addendum's C1-C3 need a "no slate change" arm
that is not built here; not scored. Its reproduction check against the
canonical 733 is not made (no earlier output is a reference).

- **Implementation check, not a standard:** B6's Johannesburg 2026 PA mean
  seats within 16.85 ± 0.5 and PA mean gap (list − ward) within −0.19 ± 0.1
  points: the investigation's prototype (a monkeypatch of
  `levels.contestation`) on the same mechanism. A miss says the code does not
  implement what the prototype measured; it says nothing about which is
  right.
- **CHANGE** (N4, amended from SPEC §6's "0"): in every arm with items 6 and 8
  (B to E), CHANGE fields no 2026 ward candidate, its slate coverage is 0 and
  its ward/PR ratio 0; its ward share is at the `level_floor` scale (about
  1e-6), below 1e-5 in every draw, and it wins no ward in any draw.

Holds / falsified: per F and B line as that file states; the implementation
check by its two intervals; CHANGE by the 1e-5 bound and zero ward wins.

### P8 (item 8): the parties item 8 enters, B8 against A

- **The four city-years where item 8 enters no party** (buffalocity 2011,
  buffalocity 2021, ethekwini 2016, mangaung 2011): B8 identical to A.
- **The 20 where it enters parties** (§1.1): panel-mean list MAE over the 24
  city-years falls or holds (B8 − A ≤ +0.005 points). At each of the three
  city-years where the entered mass exceeds 1% of the previous LGE list
  (ekurhuleni 2011, 2.52%; mangaung 2021, 2.07%; nelsonmandelabay 2021,
  1.09%), list MAE falls. Argued: a party on the ballot with a previous-LGE
  list share of that size keeps a measurable share at the next election, and
  entering it near its previous share cuts the error from its whole actual
  share, while the renormalisation takes the same mass from every other party
  in proportion.
- Coherent seat error summed over the panel: falls by 0 to 12 seats.
- `41_guards.roster_unrepresented` equals §1.1's no-record lists at the seven
  2011 city-years and is empty at the other 17 and at Johannesburg 2026, in
  B8 and in B to E; it is never `"not_checked"`.
- Johannesburg 2026, B8 against A: the seven parties together take a mean
  list share of 0.2-0.5% (the M2 reviewer measured 0.42% at 2933c2e: not
  blind); each is below 0.15%; together they win 0 or 1 seat in more than 80%
  of draws.

Holds: every clause. Falsified: any non-identical array at the four;
panel-mean list MAE up by more than 0.005 points; list MAE not lower at any of
the three named city-years; coherent seat error up by more than 4 seats
summed; a guard list different from §1.1's; any 2026 clause outside its range.

### P11 (item 11a): C against B

The spine change is computed (§1.3); the prediction is its propagation, which
is monotone in a party's centre before renormalisation.

- Johannesburg 2026: PA mean seats fall by 0.5-2.5 from B's; no other party
  moves by more than 0.6 seats; the DA and the ANC each gain 0-1.5.
- Panel: list MAE moves by less than 0.05 points at every city-year; coherent
  seat error summed over the panel moves by at most ±6 seats.

Holds / falsified: each range as stated.

### P16 (item 16): C16 against C

- **The windows themselves:** h = inf for θ and for ρ at every runnable target
  and at Johannesburg 2026, the status at each as §1.2's table (measured
  already, §1.2; the step-11 runs re-report them in `20_spine`).
- **Therefore C16 is identical to C** at all 24 city-years and at
  Johannesburg 2026; only the trace's window report differs.
- R2.5's conditional branches resolve to their own fallback clause: no window
  is below 2.3, so item 16 does not address the PA on the current archive (the
  PA moves by 0 seats), and that is reported as the result. R2.5's
  other-party and panel clauses (ANC −6%, EFF −6 to −9%, IFP +12 to +18%,
  panel coherent seat error falling) were stated for finite windows and are
  withdrawn by this note, not scored.
- R2.5's tripwire clause (the PA/Coloured pair firing under 10% or above 25%
  of draws) is replaced, M3 owner's decision: under the owner's rule the pair
  cannot fire, because the PA's own largest rise sets the Coloured pool's
  margin. See P12.

Holds: every window infinite and C16 identical to C. Falsified: any finite
window or any non-identical array.

### P17 (item 17): D against C16

- Johannesburg 2026: MK mean seats fall by 1.5-4; ASA's by 0-1.5; BOSA and
  RISE each gain 0-0.7; GOOD and AHC each gain under 0.3; every other party
  whose spine level rises under item 17 (§1.3) gains under 0.3; the ANC, the
  DA and the EFF each gain 0-1.5.
- The seven item-8 parties: their level-shock sd moves from
  `level_sd_default` (0.45 in log) to `levels.size_sd` at their own 2021 list
  share, which is wider; together they still win 0 or 1 seat in more than 80%
  of draws.
- Panel: list MAE (panel mean) falls by 0.00-0.05 points; coherent seat error
  summed over the panel moves by at most ±6 seats. A panel-mean list MAE rise
  above 0.05 points falsifies the account that small national-only parties
  gain going local, which the size centre measured and the flat mean erased.

Holds / falsified: each range as stated.

### P13 (item 18): the SACP, B against A

- In B the SACP is a generic entrant: its centre (`30_centres`) is 0.06-0.10%;
  its mean seats are under 0.3; P(at least one seat) is under 0.12. Each is
  below arm A's own value at Johannesburg 2026.
- Every other generic entrant's seed in B's 2026 spec moves by under 3% from
  A's (the group rescale gains one member).
- SPEC P13's seat transfers (ANC +1 to +3.5, DA 0 to +1.5) are not scorable:
  no arm isolates item 18, and items 6 and 8 move the same draws. Reported
  only. No backtest number moves from item 18.

Holds / falsified: each SACP and seed clause by its range.

### P12 (item 12): the group-share tripwire

- In E's tree at Johannesburg 2026, a run with `group_share_record.json`
  present and one with it moved aside are identical; the second reports
  `"no record"`.
- In every run of B, C, C16 and E at a city-year the record covers,
  `41_guards.group_share_tripwire` is a count, not `"no record"`, and its
  `population` equals `scanned`.
- The pair `PA|Coloured` is not among the firing pairs at Johannesburg 2026 in
  B, C, C16, D or E. That is a property of the threshold: the PA's centre
  still exceeds the whole Coloured pool's share (item 7's defect stands after
  this batch; O1), and the tripwire does not see it.

Holds / falsified: clause by clause.

### P19 (item 19): E against D, and E against D0

- **E against D0** (the brief's and `M4-SUMMARY.md`'s statement, on the arm it
  is true of): at Johannesburg 2026, both derived class weights are 0, so E is
  identical to D0 on every centre and every drawn array.
- **E against D, Johannesburg 2026** (R2.5's P19, second bullet, unchanged):
  the All Citizens Party's centre returns to about its arrival seed (item 9
  measured 0.050% list mean at `w_bye = 0`), its mean seats fall from about 2
  to under 0.2; Truth and Solidarity's centre falls from about 0.11% to about
  0.06%; the PA loses its by-election tilt on top of D; the DA's and MK's
  weighted deltas no longer reach their centres. Direction: PA down, DA down,
  ANC up; sizes not predicted, because D's centres differ from the model item
  7 measured.
- **E against D on the panel:** identical at all 24 city-years (no backtest
  target reads the by-election file).
- **`bye_weight_mode` and `BYE_MIN_WEIGHT` are inert at Johannesburg 2026 in
  E:** setting `bye_weight_mode="inverse_variance"`, or `BYE_MIN_WEIGHT` to any
  value, leaves every centre and drawn array identical, because the blend is
  entered only when `w > 0` and both class weights are 0. Their
  `EXPECTED_INERT` entries, each with a gate check that the class weights are
  0, are a window task (step 10), not part of this document.
- **P14 is withdrawn** (R2.5; item 19 replaced item 14).

Holds / falsified: E ≡ D0 exactly; the D clauses by direction and the stated
bounds; panel identity; the two inertness checks exactly.

### Item 10's other rows

`levels._citywide`'s renamed-column refusal cannot fire inside the window
(SPEC §5, read); the preflight wording is a test (G18). Not scored on arms.

---

## 5. Choices R2.5 left open, and what this document chose

| open point | chosen | why |
|---|---|---|
| how arms B to D carry "without item 19" | `--set w_bye=0.4`, the pre-item-19 city value | the W-based trees read derived weights otherwise; the override path is documented and refuses nothing |
| the brief's "E equals D" against P19's E-vs-D differences | both kept; D at 0.4 (P19 as written), control D0 at 0 (the brief's identity) | the identity is true of D0, not of D; neither statement is dropped |
| arms needing interleaved commits | B6, B8 forward from 597ec38 by hunk selection; C16 by reverting 6074382 and cdcf517; C and B as two-line switches on C16 | 11a and 16 cannot be reverted as commits (later code builds on `_shrink_one`); each switch reproduces the earlier estimator, checked in §1.3 |
| B0's specs | emitted in its own tree, predicted byte-identical to A's (E1) | the coordinator's step 8 note argues B0 could reuse A's; emitting and comparing turns that argument into a check |
| the P1 instrument | the classifier of §2, a wrapper delegating unchanged | no counter exists in `src/`; the test helper's logic, extended to the item-2 class |
| P6's 1,000-draw, seed-20261104 runs | scored at the batch's draw counts | one set of runs per arm |
| P8's "falls or holds" at every city-year | panel mean, plus strict falls at the three city-years over 1% | renormalisation moves every party at a high-mass city-year, so a per-city-year "holds" cannot fail usefully at the small ones |
| the window predictions (M3) | h = inf everywhere, from §1.2 | measured, not blind; stated as such |

## 6. Rejected claims

| claim | where | evidence that replaced it |
|---|---|---|
| item 8 enters parties at 12 city-years (joburg 2011, 2016, 2021; tshwane 2011, 2016; ekurhuleni 2011; ethekwini 2021; capetown 2011, 2016; mangaung 2016; nelsonmandelabay 2011, 2016) | SPEC §6 P8 | the probe read Johannesburg's previous LGE for every city (M2 B1); on each city's own previous LGE it is 20 of 24 (§1.1) |
| no-record residual: joburg 2011 7, capetown 2011 21, ethekwini 2011 8, 2021 9 | SPEC O5 | §1.1: capetown 2011 15, ethekwini 2011 7, ethekwini 2021 0, plus ekurhuleni 8, tshwane 4, nelsonmandelabay 3, mangaung 2 at 2011 |
| CHANGE's ward share is 0 in every draw | SPEC §6 P6, P8 | `level_floor` keeps it near 1e-6 (M2 N4) |
| 11a moves GOOD by +0.039 in log and every other party within ±0.01 | SPEC §6 P11 | on the run's inputs (mergers, drop, seeds), GOOD moves by under 0.001 under 11a and +0.090 under item 17; nine parties under 0.1% move by 0.01-0.09 under 11a (§1.3) |
| the PA's spine level falls to 2.2-2.7% under item 16 | SPEC R2.1, R2.5 P16 | the window rule gives h = inf at every target (§1.2) |
| the PA/Coloured tripwire pair fires above 25% (O1) or under 10% (P16) of draws | SPEC O1, §6, R2.5 | it cannot fire under the owner's rule (M3) |
| arm E equals arm D on every centre and draw | `M4-SUMMARY.md`, step 9 brief | true of D at weight 0 (D0); D at the pre-item-19 weight 0.4 differs at 2026 (P19) |
