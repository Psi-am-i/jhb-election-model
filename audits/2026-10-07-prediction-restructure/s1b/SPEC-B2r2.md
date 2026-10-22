# Slice B2, revision 2: ward-by-ward editor bounds with a measured allowance

Designer, 2026-10-09. This revision applies the owner's decisions on SPEC-B2
(PACKET.md, "Owner's decisions on SPEC-B2"). Read-only: nothing in the
repository was edited. Probes are in this directory. **V** = verified (a probe
run in this session, named). **A** = argued.

Everything not restated here stands as in `SPEC-B2.md`:
- facts §1;
- the per-ward set and its closed form §3, LP-checked on 3,400 wards;
- edges §4;
- limits §10.

The LP oracle in the probes is scipy, installed in this directory's
`./pylib`. The build gains scipy only in B2b (owner approved, O3).

## 0. What changed from revision 1, and the results

| item | revision 1 | revision 2 |
|---|---|---|
| widening of the swing ranges | flat 5 points | the mean record exceedance, measured: 6.98 points for ward swings, 5.16 for citywide swings (2026 build) |
| widening of `q_win` | 5 points | the measured mean, 4.93 (2 record events) |
| widening of `q_run` and the gap bounds | 5 points | 5 points where the quantity has fewer than 2 record events (`q_run`, `gap_min`); the measured mean where it has 2 or more (`gap_max`, 1.37) (§2) |
| parties new to local elections | `[0, 46.4% + 5]` in every ward | prior from the 2024 national result; range from the measured national-to-local change (§3) |
| new to the city, no national vote either | the cap above | `[0, 35.6% + 6.98]` per ward, `[0, 14.0% + 5.16]` citywide |
| citywide swing limit | option O4 | in B2a (§4) |
| delivery | one slice | B2a (no solver, shippable alone) and B2b (witness editor, scipy) |

**Results (2026, rule A's map; V, `b2r2.py 2026`, `walk_b2a*.py`):**
- **Rule A** is inside under both B2a and B2b. Its whole-state LP slack is 0.
- **The screenshot state** (ANC 8.4%) is outside B2a: the ANC's citywide limit
  is 19.4–51.7%. B2b also excludes it.
- **Backtest, out of sample (24 city-years):** 21 of 665 real citywide results
  fall outside the editor's limits. 19 of them are in 2011, the year
  built from one round of history; 0 are in 2016, and 2 in 2021. 50 of 40,937
  real ward results fall outside their ranges (§7).
- **B2a's remaining gap:** on rule A's map, none of 200 B2a states had a
  jointly infeasible ward matrix. With repainting, 19 of 100 did (largest
  16.5 points). B2b closes that.

## 1. The record-exceedance allowance (owner's O1)

### Method (V, `records.py`)

- **Rounds.** Rounds are ordered by the later election of each consecutive
  metro LGE pair: 2006, 2011, 2016, 2021. The eight metros of one election
  form one round, and the first round sets the record. In every later round,
  a swing that beats the record in its direction is an event, and its size is
  new record minus old record.
- **Ward level.** Stood-both (ward, party) pairs, binned by starting ward share
  (`SWING_BINS`, SPEC-B2 §2).
- **Citywide.** Stood-both (city, party) pairs, binned by prior citywide share.
- **Two scopes:**
  - **party-own:** a record per (party, bin, direction). This is the owner's
    literal wording.
  - **pooled:** a record per (bin, direction) over all parties. This is the
    quantity the editor's bin extremes are made of, so it is the allowance
    that matches how the bounds are built.

### Exclusions, detected from the data

Each rule runs per metro and per pair (a → b). A party's swings in that pair
are left out of the record measurement only. The bounds keep every real swing.

| kind | rule (thresholds typed, JUDGEMENT-CALLS §R13) | found |
|---|---|---|
| **merger** | a party with ≥ 1% of the ward vote at a stands nowhere at b, with no ward or list vote. Its absorber is the stood-both party whose ward swing correlates best with the vanished party's ward share at a, if r ≥ 0.5 | ID into DA: Cape Town 2011 (r 0.90), Joburg 2011 (0.82). NFP into IFP: Durban 2016 (0.52). The NFP failed to register in 2016 and its voters went to the IFP; the rule calls this a merger. ID in NMA 2011 has r 0.50, which falls just below the threshold and counts as a dissolution |
| **split** | a party new to the city with ≥ 5% of the ward vote at b. Its source is the party whose ward swing is most negatively correlated with the newcomer's ward share, if r ≤ −0.5 | EFF from the ANC: Ekurhuleni, Joburg, NMA and Tshwane 2016. ID from the DA: Cape Town 2006. **Spurious:** EFF "from VF+" in Mangaung 2016 (−0.64), and COPE "from the DA" in NMA 2011 (−0.55; COPE came from the ANC). Below 5%, COPE's 2011 split is not detected elsewhere |
| **collapse** | a party falling from ≥ 2% to under a quarter of that share | COPE: Mangaung and NMA 2016. Minority Front: Durban 2016. AIC: Buffalo City 2021 |
| not excluded | new parties with no correlated source | EFF Buffalo City 2016; ActionSA Ekurhuleni, Joburg and Tshwane 2021 |

The detector is imperfect: two of its seven splits are spurious. The choice of
exclusion rule barely moves the allowance:

| exclusions | pooled ward mean | pooled citywide mean |
|---|---|---|
| the data rules above | 6.98 points | 5.16 points |
| COPE and the ID merger only | 7.07 | 5.75 |
| none | 7.56 | not run |

### Exceedances

All values in points, with exclusions by the data rules, over 32 pairs (V,
`records.py`). Ward level, party-own, by bin:

| bin | events | mean | median | sd | p25–p75 | max |
|---|---|---|---|---|---|---|
| (0, 1%] | 39 | 1.59 | 0.26 | 3.27 | 0.09–1.62 | 17.83 |
| (1, 5%] | 31 | 4.43 | 2.23 | 7.50 | 0.66–3.68 | 40.35 |
| (5, 15%] | 16 | 6.38 | 5.77 | 5.53 | 2.39–7.18 | 19.14 |
| (15, 35%] | 11 | 10.81 | 7.72 | 9.15 | 3.61–13.44 | 30.26 |
| (35, 60%] | 6 | 9.47 | 3.95 | 10.33 | 3.01–13.12 | 31.04 |
| (60, 100%] | 6 | 13.90 | 14.44 | 9.21 | 5.86–19.10 | 29.19 |
| **all** | **109** | **5.14** | **2.24** | **7.53** | **0.42–5.88** | **40.35** |

Ward level, pooled:
- 15 events: mean **6.98**, median 4.67, sd 8.06, p25–p75 3.40–6.22, range
  0.10–32.76.
- By bin, the counts are 1, 4, 2, 3, 1 and 4, so no bin has a usable sample
  on its own.
- The largest event is the PA in Eldorado Park, Joburg 2021: +32.76 over the
  previous record of its bin. Without it the mean is 5.14.

Citywide:
- party-own: 34 events, mean 1.59, median 0.62, sd 2.56, max 10.64;
- pooled: 11 events, mean **5.16**, median 5.22, sd 4.36, p25–p75 1.68–5.79,
  range 1.20–14.06.

**Exceedances do not shrink from round to round:** the ward pooled mean by
round is 3.12 (2011, 8 events), 6.89 (2016, 2) and 13.20 (2021, 5). The
correlation of |old record| with exceedance (+0.25 at ward level, −0.14
citywide pooled) is computed across bins. Larger-share bins have both larger
records and larger swings, so it is confounded by bin size and does not bear
on growth within a record.

The ward-level records have not converged. The 2021 local surges (PA, Al
Jama-ah) are each far beyond any earlier record.

### Leave-one-election-out and causal checks (V, `loo.py`)

For each held-out election Y, the bin extremes come from pairs before Y and
are widened by A. The tables count real stood-both swings at Y outside them.
"LOO" takes A from the record events of every other election. "Causal" takes
A only from events before Y; 2011 has none.

Ward level. Population: stood-both (ward, party) swings at Y against bin
extremes ± A, before the per-ward shape. This is not §7's population.

| Y | A = 0 | flat 5 | pooled mean (LOO A) | pooled median | party-own mean | pooled mean, causal |
|---|---|---|---|---|---|---|
| 2011 | 41/5,096 | 12 | 0 (11.39) | 2 (7.52) | 13 (4.56) | n/a |
| 2016 | 8/5,820 | 6 | 2 (7.00) | 6 (4.17) | 5 (5.78) | 6 (3.12) |
| 2021 | 7/7,283 | 5 | 5 (3.87) | 5 (4.05) | 5 (4.86) | 5 (3.87) |

Citywide. Population: stood-both (city, party) swings at Y.

| Y | A = 0 | flat 5 | pooled mean (LOO A) | pooled median | party-own mean | pooled mean, causal |
|---|---|---|---|---|---|---|
| 2011 | 20/73 | 12 | 13 (2.87) | 14 (1.71) | 16 (0.97) | n/a |
| 2016 | 8/92 | 0 | 0 (7.21) | 0 (5.57) | 0 (2.07) | 0 (7.90) |
| 2021 | 4/117 | 1 | 1 (5.09) | 2 (1.72) | 2 (1.67) | 1 (5.09) |

### Assessment and recommendation

- **Use the mean of the pooled exceedances, per level, recomputed at every
  build.** Held out, it misses fewer ward results than the flat 5 points in
  2011 and 2016 (0 against 12; 2 against 6), and the same in 2021. Citywide
  it matches the flat 5 in 2016 and 2021, and misses one more in 2011 (13
  against 12). It misses no more than the median anywhere.
- **Do not use the party-own mean** for bounds built from pooled extremes. It
  is a different quantity: parties' own records are shorter, so the mean is
  smaller (1.59 citywide). Applied to pooled extremes it misses the most of
  the three.
- **Do not use the max.** At ward level it is 32.8 points, which removes the
  bound.
- **Does it work?** It is sound as an average and weak as a guarantee:
  - the samples are 15 and 11 events;
  - one event moves the ward mean by 1.8 points (6.98 with the PA surge, 5.14
    without);
  - exceedances are not shrinking.
  - It leaves the 2021-type local surges outside, as any average must: in each
    held-out election, 5 to 6 ward results stay outside whatever the
    statistic, short of the max.
  - In the 2026 build it lands close to the owner's original 5 points:
    6.98 for wards, 5.16 citywide.

## 2. The shape bounds: `q_win`, `q_run` and the gap

The same record rule applies per election over all metros (V, inline probe).

| quantity | per election, 2000 → 2021 | record events | mean |
|---|---|---|---|
| lowest winning share | 33.5, 29.6, 34.2, 34.0, 23.6% | 2006: 3.88; 2021: 5.99 | 4.93 |
| highest runner-up | 47.4, 47.8, 47.3, 46.2, 41.3% | 2006: 0.35 | 0.35 (1 event) |
| gap min (list − ward, points) | −0.60, −0.60, −1.76, −0.31, −1.38 | 2011: 1.15 | 1.15 (1 event) |
| gap max | 2.06, 2.53, 3.42, 6.16, 4.14 | 0.47, 0.89, 2.74 | 1.37 |

**Recommended:**
- the measured mean where a quantity has at least 2 events: `q_win` 23.62 −
  4.93 = 18.69%, and `gap_max` 6.16 + 1.37 = 7.53;
- `EDITOR_WIDEN_PP` = 5 where it has fewer: `q_run` capped at 50%, and
  `gap_min` −6.76.

**Measured cost of measuring everywhere:**
- `gap_min` would be −1.76 − 1.15 = −2.91;
- our prediction would then sit outside on the PA's gap: rule A has the PA's
  list share 5.53 points below its ward share (V, `b2r2.py 2026`);
- that is a fact about the model's draws (the PA's mean list vote against its
  mean ward vote), not about rule A or the bounds;
- the panel's widest such gap is 1.76 points. It is worth a MODEL-LOG entry
  whichever rule is chosen.

## 3. Parties new to local elections: the 2024 national prior (owner's O2)

**Files.** These exist for all eight metros, and V `ls` confirmed each:
- `npe2004`, `npe2009`, `npe2014`, `npe2019` and `npe2024_<CODE>_vd_party.csv`:
  one ballot, per VD, no ward;
- `npe1999_approx_*`, an approximation, left out.

The pairs measured are 2004 → 2006, 2009 → 2011, 2014 → 2016 and 2019 → 2021:
32 city pairs. An NPE is joined to the next LGE's wards by VD number through
that LGE's own VD-to-ward record (`montecarlo.ward_parts`). It is joined to
2026 through the crosswalk.

**The national-to-local change (V, `npe.py`).** Citywide, LGE ward share minus
NPE share, stood both, by NPE share:

| NPE share | n | median diff | median ratio | min .. max |
|---|---|---|---|---|
| (0, 1%] | 251 | −0.01 | 0.91 | −0.7 .. +2.9 |
| (1, 5%] | 64 | −0.38 | 0.85 | −3.8 .. +1.9 |
| (5, 15%] | 25 | −0.11 | 0.99 | −10.9 (COPE, Mangaung 2011) .. +9.5 |
| (15, 35%] | 30 | +4.40 | 1.19 | −15.0 (COPE, BUF 2011) .. +14.3 |
| (35, 60%] | 18 | −6.91 | 0.85 | −15.6 (ANC, Joburg 2021) .. +6.9 |
| (60, 100%] | 16 | −6.44 | 0.91 | −11.6 .. +5.0 |

**Parties at their first local election after a national one.** There are 36
cases with at least 0.5% of the NPE vote. The median ratio of LGE to NPE share
is 0.92. COPE accounts for 8 of the cases, at ratios of 0.12 to 0.29: it
collapsed at its first local election, so the collapse rule applies (§1).
Without COPE, 28 cases have a median ratio of 1.04: EFF 2016 at 0.99 to 1.41,
ID 2006, GOOD and ATM 2021.

**The usual deterioration, measured:**
- a party new to local elections shows none beyond COPE's collapse;
- across all parties, the change depends on size: small parties lose a little
  (median ratio 0.85 at 1–5%), and the largest lose 6 to 7 points.

**Rule (B2a).** A roster party with no ward vote in the city at the preceding
LGE, but a vote at the preceding NPE, is handled as follows.
- **Ward prior:** its NPE share in the ward. Its range is that prior plus the
  extremes, by bin, of the NPE → LGE ward change (stood-both pairs before the
  target, with collapses excluded by the §1 rule), ± the ward allowance.
- **Citywide limit:** its NPE city share plus the NPE → LGE citywide change
  extremes by bin, ± the citywide allowance.
- **Centre:** the measured ratio (1.04, COPE excluded) is recorded as the
  centring adjustment. Because it is 1 within the sample's noise, it moves no
  bound.

**2026, Joburg.** Eight roster parties are new to local elections with a 2024
national vote: MK 12.22%, RISE 1.56%, BOSA 1.02%, United Africans
Transformation 0.15%, Operation Dudula 0.11%, and three under 0.1%.
- Their citywide limits are MK 2.9–26.9%, RISE 0–8.6% and BOSA 0–8.1% (V).
- 46 roster parties have neither a 2021 local nor a 2024 national vote. They
  take the newcomer caps:
  - ward [0, 35.6% + 6.98]: 35.6% is the largest ward share of a party new to
    its city with no vote at the preceding NPE;
  - citywide [0, 14.0% + 5.16]: 14.0% is ActionSA, Joburg 2021.

## 4. The ranges and limits, as built (B2a and B2b share them)

**Ward range for (w, p), target T.** h is the preceding LGE's share, joined
through `ward_parts`.

| condition | range |
|---|---|
| h > 0 | h + bin extremes ± A_ward |
| h = 0 but a city record | the city share as h, same rule |
| new to local, with an NPE vote | NPE ward share (or NPE city share) + NPE → LGE extremes ± A_ward |
| none of the above | [0, N_ward + A_ward] |

The painted winner takes at least `q_win`; every other party at most `q_run`.
A ward whose set is empty falls back to that shape alone.

**Citywide limit for p:**

| condition | limit |
|---|---|
| prior citywide share H (e-weighted onto the target's wards) > 0 | H + citywide bin extremes ± A_city |
| new to local, with an NPE vote | NPE city share + NPE → LGE citywide extremes ± A_city |
| neither | [0, N_city + A_city] |

The allowances A_ward and A_city are the means of the pooled record events
before T (§1). They are regenerated at every build and written into
`x-editor-bounds` with their event lists, so the value is fetched, never
typed.

**2026 values (V, `b2r2.py 2026`):**

| quantity | value |
|---|---|
| A_ward | 6.98 (15 events) |
| A_city | 5.16 (11 events) |
| `q_win` | 18.69% |
| `q_run` | 50% (5-point rule, 1 event) |
| (ward, party) cells from local history | 2,700 |
| from the national prior | 1,080 |
| newcomer cells | 6,210 |
| unpaintable (ward, party) pairs | 0 of 9,990 |

## 5. B2a: no solver, shippable alone

### What the editor enforces

Each party's ward vote is kept inside **[lo_p, hi_p] = [max(box floor_p, city
lo_p), min(box ceil_p, city hi_p)]**:
- the box is SPEC-B2 §3's closed-form per-ward projection, summed with e
  (exact per party);
- the city limit comes from §4;
- the other parties are rescaled by the existing bounded apportion.

Recomputed on every paint stroke: closed form O(W·P log P), about 70k
operations; intersection O(P) (A: under 1 ms on a phone).

Conflicts:
- **The map needs more than history allows** (box floor > city hi): the map
  wins. hi_p becomes the box floor, and the note names the party: "<Party>'s
  wards need more of the vote than any past election gives it." 0 cases on
  rule A's map, and 0 in 100 repainted states (V).
- **Σ lo > 1:** the city floors are lowered in proportion until the
  apportion fits, with the same note. Not observed: over 100 repainted states
  the largest Σ lo was 0.491 (V, `walk_b2a_paint.py`). The rule is argued.

**What B2a does not enforce** (V, `walk_b2a.py`, `walk_b2a_paint.py`):
- On rule A's map, 0 of 200 states jointly infeasible (moves anywhere in range,
  or up to 10 points). The city limit closes revision 1's 71/100 gap there.
- With repainting (40% of steps repaint 10 wards), 19 of 100 states jointly
  infeasible: median slack 0, p90 6.4 points, largest 16.5.

### Files and functions (B2a)

**`src/score_forecasts.py`**
- `_read_rows(..., vd_votes=False)`: a fifth return of per-VD ward votes. It
  stays the one reader. A sibling `_read_npe(path)` is added in the same
  module for the NPE layout: one ballot, no BallotType.

**`src/build_make.py`**
- `ward_priors(city, target, wards)`: through `montecarlo.ward_parts(target)`
  and `Target.previous_lge`. Returns h, the city shares and provenance.
- `npe_priors(city, target, wards)`: the preceding NPE, through the same
  parts.
- `swing_panel(city, target)`: stood-both ward and citywide pairs (LGE → LGE
  and NPE → LGE). Returns bin extremes, sources and sha256s.
- `record_events(panel)` and `exclusions(panel)`: the §1 rules. Each event
  carries (round, bin, direction, old, new, exceedance); each exclusion its
  evidence (kind, party, partner, r).
- `allowances(events, target)`: A_ward, A_city and the shape widening of §2.
- `ward_ranges(...)` and `city_limits(...)`: the result goes into
  `x-editor-bounds` as `ward_ranges` (sparse), `party_ranges`, `city_limits`,
  `allowance {value, events}`, `exclusions`, `shape {q_win, q_run, gap_min,
  gap_max, events}`, `SWING_BINS`, and the thresholds of §1.
- `EDITOR_WIDEN_PP` stays, as the widening for quantities with fewer than
  `MIN_RECORD_EVENTS` = 2 events.

**`worker-api/tools/make_schema.mjs`**: accepts the keys.

**`interactive/js/builder-state.js`**
- New: `wardRange` (closed form), `boxOf(calls)` (incremental by ward),
  `limits(calls)` (box ∩ city, with the conflict rules).
- `setWardPercent`, `clampToBounds` and `outOfBounds` read `limits`.
- **Deleted:** `wonE`, `wardBounds`.

**`interactive/js/make.js`**: slider min/max from `limits`; the conflict and
out-of-limit notes.

**Records (B2a):**
- **JUDGEMENT-CALLS:**
  - §R5 superseded;
  - §R6 ward ranges;
  - §R7 `SWING_BINS` (🔴 typed);
  - §R8 the national prior and the newcomer caps;
  - §R9 the allowance is the mean of the pooled record exceedances (⚖️
    owner's call, measured; evidence §1);
  - §R10 the per-ward shape and its fallback;
  - §R12 the citywide limit (⚖️ owner, O4);
  - §R13 the exclusion thresholds: 1% vanish, 5% split, 2% → a quarter
    collapse, |r| ≥ 0.5 (🔴 typed; the two spurious splits named);
  - §R14 `MIN_RECORD_EVENTS` = 2, below which `EDITOR_WIDEN_PP` stays.
- **MODEL-LOG:**
  - what was and what is;
  - the §1, §3 and §7 tables, from the writer's own build;
  - the PA gap of rule A (§2).
- **MACHINERY:** the ranges, the limits, the conflicts, where each lives.

**Guards (B2a).** Each states its population, checks both ways, catches a
constructed violation and is quiet when it is reverted.

| guard | test | population | constructed violations |
|---|---|---|---|
| ranges regenerated | `test_your_forecast_page.py::test_the_ward_ranges_are_regenerated_from_the_panel` | panel pairs == consecutive cleaned LGE files before the target, and NPE → LGE pairs == the NPE files with a following LGE before the target, both ways; `ward_ranges` keys == the pairs with a non-zero LGE prior, recomputed in the test, both ways; each `party_ranges` entry is of the kind its party's history says (LGE, NPE or newcomer), both ways | as SPEC-B2 §7 (1)–(5), plus (6) a party's rows deleted from the preceding NPE → it becomes a newcomer; (7) a party's NPE votes in one VD raised → exactly the wards of that VD's parts move |
| record events | `test_your_forecast_page.py::test_the_allowance_is_the_mean_of_record_events` | `allowance.events` == the events recomputed from the panel, both ways; the value == their mean | a constructed later round with a swing 3 points beyond a bin's record → one new event of 3 points, and the allowance moves to the new mean; a constructed vanished party with a correlated absorber → a merger exclusion appears and the absorber's event disappears; each reverted → equal to served |
| shape rule | the same test | `shape.events` per quantity | a constructed election with a lower winning share → a `q_win` event; a quantity with one event keeps `EDITOR_WIDEN_PP` |
| closed form | `builder.test.mjs` "the ward range is the set's projection" | random wards of 2–5 parties against vertex enumeration | winner condition dropped → caught |
| limits | `builder.test.mjs` random walk (extended to repaint) | every state | each ward vote inside `limits`; a constructed map whose box floor passes a city ceiling → conflict note, ceiling raised to the floor |
| bounds read | `builder.test.mjs` typed-bound scan | `BOUND_FUNCTIONS` = `wardRange`, `boxOf`, `limits`, `gapOf`, `listBounds`, `contextOf` | a literal → found |
| our prediction | `make.test.mjs` (existing) `start.out_of_bounds == B.outOfBounds(start)` | — | — |

**Targeted tests (B2a).** Python `run_all.py -k`:
- `your_forecast_page`, `score_forecasts`, `rank_entries`, `entries`,
  `prediction_rule`;
- `site_assets`, `site_structure`, `number_scan`.

Node, by file:
- `builder.test.mjs`, `make.test.mjs`, `yf.test.mjs`, `page.test.mjs`;
- `worker-api/test/node/build.test.js`;
- `yf_jump_check.mjs`.

**Whole suite:** no FLOW.md exception applies. Nothing touched is imported by
`run_model`; `montecarlo` imports neither `score_forecasts` nor `build_make`
(V).

**Estimate (B2a):** about 3 days for one writer, with diff review and targeted
tests on top.

| part | days |
|---|---|
| generator: priors, NPE, panel, events, exclusions, allowances | 1.5 |
| JS limits and notes | 0.5 |
| guards and records | 1 |

## 6. B2b: the witness editor (scipy)

B2b builds on B2a's ranges and limits. Its mechanism is SPEC-B2 §3(c),
unchanged:
- a ward-share matrix X inside every ward's set;
- slider moves by convex combination toward the moved party's extreme points;
- paint strokes put the painted ward into its new set;
- one LP on load (links and hand-offs), our prediction's X solved at build.

Two additions:
- **The citywide limit in a move.** A move's λ is capped so that no other
  party's aggregate leaves its city limit: O(P) per move (A). The slider's
  range is then the box intersected with what that cap allows.
- **The load LP** carries the city limits as bounds on the aggregates. A state
  outside them gets the least-slack matrix and the SPEC-B2 §4.2 note.

**Files (B2b):**
- `src/ward_witness.py`: `witness(e, ranges, calls, V, city_limits) -> (X,
  slack)`, through `scipy.optimize.linprog` with HiGHS. It is copied to the
  page by `sync_py.mjs` and runs in the Pyodide worker with Pyodide's scipy,
  loaded on first need.
- `requirements` and the venv gain scipy (owner approved).
- `build_make.forecast_data` adds `start.witness`.
- `builder-state.js`: `extremePoint`, `paintInto`, `moveParty`; `History`
  carries X (float32, limit 30).
- The worker gains `handoff` + witness and a `witness` call.

**Guards (B2b):**
- SPEC-B2 §7's witness invariant and load-LP guards;
- `sync_py.mjs --check`;
- a Python test comparing `witness` against the JS closed form on random wards
  (node snippet). LP min and max per party must equal `wardRange`.

**Targeted tests (B2b):** B2a's list plus `node interactive/tools/sync_py.mjs
--check`. Whole suite: no exception, since scipy enters the build, not
`run_model` (A).

**Estimate (B2b):** about 2.5 days after B2a.

| part | days |
|---|---|
| LP module, build and worker wiring | 1 |
| witness editor in JS | 1 |
| guards | 0.5 |

## 7. Re-measured: rule A, the screenshot, the backtest

### 2026 (V, `b2r2.py 2026`; e from the served `x-editor-bounds`)

| party | box (B2b slider range before the city cap) | citywide limit | B2a limits | rule A | screenshot |
|---|---|---|---|---|---|
| ANC | 8.5–72.1 | 19.4–51.7 | 19.4–51.7 | 21.31 | **8.4 (outside)** |
| DA | 7.7–68.7 | 13.9–46.2 | 13.9–46.2 | 25.17 | 29.3 |
| PA | 1.5–46.1 | 0–14.9 | 1.5–14.9 | 11.86 | 13.8 |
| MK | 0.8–48.8 | 2.9–26.9 | 2.9–26.9 | 8.57 | 10.0 |
| EFF | 0.2–48.5 | 0–22.9 | 0.2–22.9 | 10.42 | 12.1 |
| ActionSA | 0–48.1 | 2.3–25.9 | 2.3–25.9 | 9.18 | 10.7 |
| BOSA | 0–46.7 | 0–8.1 | 0–8.1 | 0.92 | 1.1 |
| RISE | 0–46.8 | 0–8.6 | 0–8.6 | 1.51 | 1.8 |

**Rule A:**
- B2a: inside for every party; no ward falls back; no conflict.
- B2b: joint LP slack 0.
- Its gaps, from the PA's −5.53 to ActionSA's +3.27, are inside the
  recommended gap bounds (−6.76, +7.53).

**Screenshot state:**
- B2a: outside on the ANC alone (8.4% against 19.4%).
- B2b: the ward-level LP slack is 0.12 points (near-feasible on the ward
  ranges alone), and the citywide limit excludes it.

### Backtest

Population: 24 city-years, each built only from elections before it: the
allowance from record events before T (5 points in 2011, which has none), and
the NPE prior from the preceding NPE. V, `b2r2.py` → `b2r2.log`.

| measure | revision 2 (B2a and B2b) | revision 1 (flat 5, newcomer cap) | slice B |
|---|---|---|---|
| allowance used (ward / city) | 2011: 5 / 5; 2016: 3.12 / 7.90; 2021: 3.87 / 5.09 | 5 / — | — |
| real ward results outside their range | **50 of 40,937**: 37 in 2011, 7 in 2016, 6 in 2021 | 28 | 1 |
| real citywide shares outside the per-party box | 0 of 665 | 0 | 0 |
| real citywide shares outside the citywide limit (and so outside B2a) | **21 of 665**: 19 in 2011, 0 in 2016, 2 in 2021 | not in the design | not in the design |
| city-years whose real state fails the B2b joint LP (ward ranges) | 0 of 24 | 0 | n/a |
| city-years with anything outside B2b (LP or citywide limit) | 10 of 24 (8 in 2011) | — | — |
| wards falling back to the shape | 3 (Durban 2016) | 3 | — |

The revision 1 column differs from revision 2 in two rules at once: the
allowance (causal, 3.12 and 3.87 in 2016 and 2021, against a flat 5), and the
national prior for parties new to local elections. The national prior's
share is measured by rerunning revision 2 without it (`NO_NPE=1`, V):
- 43 ward misses and 14 citywide misses;
- the newcomer cap without a national vote then puts EFF 2016 outside in 9
  wards;
- so the prior removes those 9 and adds COPE's 17 (net +7 wards), and adds
  COPE's 7 citywide misses.
The remaining 28 → 43 comes from the smaller causal allowance and the lower
newcomer cap.

The 50 ward results outside, by party and cause (V, `MISS`):

| party | election | results | cause |
|---|---|---|---|
| COPE | 2011 | 17 | collapse at its first local election, which the new NPE prior exposes. Under revision 1's newcomer cap these were inside |
| DA | 2011 | 12 | the ID merger |
| ANC | 2011 | 4 | |
| NFP | 2011 | 3 | |
| Minority Front | 2016 | 4 | collapse |
| PA, DA, Al Jama-ah, ANC | 2021 | 6 | local surges and the drops beside them |
| others | | 4 | |

The 21 citywide results outside:
- 2011: the DA in all 8 metros (merger), COPE in 7 (collapse), the ANC in 3,
  and the IFP in Durban;
- 2021: EFF in Durban (10.15% against 9.7%), and ActionSA in Joburg (13.98%
  against a newcomer cap of 10.0%, built when no earlier newcomer had passed
  4.9%).

## 8. Limits

Revision 1's §10 stands. Added:
1. The allowance rests on 15 ward events and 11 citywide events. It is not
   converging, and one event moves the ward mean by 1.8 points (§1).
2. Record events are pooled across metros within one election. A metro's own
   history would give smaller samples still.
3. The exclusion detector mislabels 2 of 7 splits, and calls the NFP's
   failure to register a merger. Its effect on the allowance is within 0.6
   points (§1).
4. COPE-type first-election collapses fall outside the NPE prior's range: 17
   ward results and 7 citywide results in 2011. That is the cost of O2, and
   it is measured.

## 9. Decisions remaining for the owner

- **D1.** The shape widening: the measured mean only where 2 or more events
  exist (recommended), or everywhere. Everywhere puts our prediction outside
  on the PA's gap (§2).
- **D2.** Ship B2a first, then B2b (recommended). B2a alone leaves the joint
  gap measured with repainting: 19 of 100 states.

## Probes (this directory, added in revision 2)

- `records.py`: record events, exclusions, statistics.
- `loo.py`: leave-one-election-out and causal checks.
- `npe.py`: the national-to-local change; 2026 parties new to local.
- `b2r2.py`: ranges, limits, the 2026 checks and the backtest; output in
  `b2r2.log`.
- `walk_b2a.py`, `walk_b2a_paint.py`: B2a's joint gap.

`b2r2.py` was run with `SHAPE_MIN_EVENTS=2` for the recommended shape rule. The
counts are identical with 1. Revision 1's probes are unchanged.
