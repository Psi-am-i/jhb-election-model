# Model correction batch, 2026-10-09: the specification

Designer: one, read-only (`SPEC-PACKET.md`), plus items 11-14 from the BRIEF's
"Owner's decisions, 2026-10-09 (later)". Scope: items 1-6, 8-14 of
`BRIEF.md`. Out of scope: item 7's level fix as such, item 15 (cosmetic), any
change to the SACP beyond item 13 and to the All Citizens Party beyond item 14.

Probes run for this specification are read-only, wrote nothing under `data/`,
and live in `/Users/simondavis/.claude/jobs/26965cd4/tmp/modelspec/`
(`universe_gap.py`, `unopposed.py`, `floor_check.py`, `item11_spine.py`, with
their `.json` outputs). Each figure below names the probe that produced it.
"Measured" means a probe printed it; "read" means a file or the code says it;
"argued" means neither.

---

## 0. Decisions this specification takes that the owner should see first

| # | the decision | why | what the brief said |
|---|---|---|---|
| O1 | **Item 11 as specified is not candidate b2 as measured.** b2 (`item7/scripts/variants.py`, `spine_with(0.921, 0.762)`) replaced the PA's θ and ρ multipliers with the size-centre value at its current size and **dropped the PA's own record**; it touched the PA only. The general change ("`_shrunk` evaluates the size centre at the party's current base, for every party") keeps every party's own record, weighted `worth/(worth+SHRINK)` as now. Measured (`item11_spine.py`, joburg 2026, spine level before by-elections, shrink and renormalisation): the PA's spine level moves 6.43% → 6.05% (Δlog −0.061), not to b2's level. The 23.95 → 11.15 seat move in item 7's table came from dropping the PA's own record, which nobody has approved. **Consequence:** after this batch the PA's centre still exceeds the whole Coloured pool (item 7's defect stands), and item 12's tripwire will report it: predicted PA/Coloured firing above 25% of draws on arm D (§6, item 12 under "nulls"). | The owner approved "for everyone"; the measured candidate was PA-only and did something else as well. | "candidate b2 of item7/FINDINGS.md" |
| O2 | **Item 11 includes the no-record case (11b).** A party with no θ (or ρ) record of its own currently takes the flat common mean `mu_all` in `levels.spine` (`mu_t.get(party, c_t)`), while `levels.theta_prior` already gives such a party the size centre at its current size. 11b makes the spine do what `theta_prior` does. It is the larger half of item 11 at 2026: MK's spine level 11.31% → 9.93% (Δlog −0.130), seven small national-only parties +0.24 to +0.30 in log, local-only parties +0.12 (measured, `item11_spine.py`, B11=1 against B11=0). Measured and reported as its own arm so the owner can strike it. | "growth measured at current size for every party" covers a party with no history; leaving it on the flat mean is the one place the size signal is still erased. | not addressed |
| O3 | **Item 6's clip: the upper bound becomes `WARD_PR_RATIO_MAX`; no lower clip is added.** Replacing `[0, 2.0]` with `[WARD_PR_RATIO_MIN, WARD_PR_RATIO_MAX] = [0.5, 2.0]` raises the floor from 0 to 0.5. Measured (`floor_check.py`, joburg 2026): one party falls below 0.5, CHANGE, whose 2026 slate is empty (PR list only, `declared_contestation`'s complete roster gives 0.0) — the 0.5 floor would give it ward votes in wards where it has no candidate. Every term of `ratio × now/was` is non-negative, so no lower clip is needed. `WARD_PR_RATIO_MIN` is the floor on the *measured* ratio, a different quantity. | Item 8 brings CHANGE into the run, so the brief's literal reading would create a ward candidate that does not exist. | "the registered `WARD_PR_RATIO_MIN/MAX` is used instead" |
| O4 | **Item 3 is implemented as statute in the seat law and as a refusal in the draw loop.** No ward in any metro LGE file 2000-2021 (40 files) has fewer than two ward-ballot parties, and none has PR rows without ward rows (`unopposed.py`); every 2026 Johannesburg ward lists at least 49 parties in `[roster.wards]` (read, `pools.declared_roster`). Modelling an uncontested ward inside the draw loop (fixed winner, no ward ballot, PR doubled) has no case to score. The seat law takes the extra votes as an input; `run_model` refuses a target with an unopposed ward, naming it. | A draw-loop branch nothing exercises is argued, not tested. | "counted twice" |
| O5 | **Item 8's guard refuses only for parties with a previous-LGE record; it reports the rest.** Backtest city-years carry roster parties with no national baseline, no previous-LGE list vote and no seed (probe `universe_gap.py`: joburg 2011 7, capetown 2011 21, ethekwini 2011 8, 2021 9, and others; 2026: 0). These are pools' unseeded arrivals (`no_measured_vector` in the spec), a pools question outside this batch. The guard refuses at every target for the with-record class and, at a target with no result file (2026), for the no-record class too. | A two-way guard that refuses at most backtest city-years stops the panel. | "a guard checks the certified roster against the run's parties in both directions" |
| O6 | **One `pools.py` re-emit window, for this batch's changes only.** `levels.py` is in `pools._EMIT_DEPENDENCIES`; items 10 and 11 change its code, so the window is forced. Queue rows 19, 20, 26, 27, 28, 31, 32 and 33 stay queued: four of them move numbers under their own pre-registrations, and folding them in would make this batch's measurement unattributable. This departs from the queue's "land every queued change in one commit", which is why it is the owner's. | §5 | — |
| O7 | **Item 14's derivation has a thin record.** The by-election archive starts 2022-02. The only real result after a by-election run in it is the 2024 national ballot (metro VD files only): 30 metro contests before 2024-05-29, 75 party-metro pairs, 40 with two or more contests (measured, inline probe; the method is §6, P14). The pre-registered rule says what happens if the data do not settle a minimum. The derived minimum is not chosen to exclude the All Citizens Party; if it admits it, that goes to the owner. | — | "derived from data" |
| O8 | **Item 13 makes the SACP a generic entrant.** Deleting `weights` and `support` from `[party.SOUTH_AFRICAN_COMMUNIST_PARTY]` sends it down `arrival_rules`' entrant branch: reach-matched comparators (it is listed in all 135 wards of `[roster.wards]`), the even pool spread, the group rescale, zero level shock, the pool split. §L13 measured this route at about 0.06%. The owner's note that the SACP stands "only in some wards" disagrees with the declared slate (135 of 135, read); noted, not changed. | "sized and varied by the same rules as other parties of its kind" | — |

---

## 1. Item by item

Line numbers are at commit 597ec38 and are for finding the place; the function
name is the address.

### 1.1 Item 1 — ties settled by a seeded lot

**One definition, in `src/seats.py`** (stdlib only, so it ships to Pyodide and
the seat Worker unchanged):

```python
def lot_identity(city: str, target: str, seed) -> str:
    """The run's identity for the lot: f"{city}|{target}|{seed}". No party enters it."""

def lot_order(tied, key: str) -> list[str]:
    """The tied codes in the order the lot draws them.
    canon = sorted(set(str(p) for p in tied))      # enumeration only
    ticket(i) = hashlib.sha256(f"{key}#{i}".encode()).digest()
    return [p for _, p in sorted(zip((ticket(i) for i in range(len(canon))), canon))]"""
```

The seed (`key`) never contains a party code. String order only numbers the
tied codes; which number wins is the key's.

**What the lot guarantees, and what no lot can.** For an exact tie the inputs
of the tied parties are identical, so only their codes tell them apart. For one
fixed key, renaming a tied party so that it sorts on the other side of its
rival hands the event to the rival: that is unavoidable for any deterministic
rule. What the lot guarantees is that no code is favoured across events: over
many keys each tied party wins with equal frequency, whatever the codes (G1b).
The alphabetical rule favoured the earlier code at every event. Untied events
never read the lot, and there a code swap gives the swapped answer (G4). Key forms, fixed:

| event | key |
|---|---|
| ward call | `f"{run_lot}|ward|{ward_id}"` |
| seat, prediction / reader / truth | `f"{run_lot}|seat|{round}"` |
| seat, inside a draw | `f"{run_lot}|draw{d}|seat|{round}"` |

`round` is the allocation round: 0 for the first `allocate`, then the index of
each re-allocation in `allocate_with_overhang`'s `deduct` and `level` loops.

**`seats.allocate(combined, total_seats=270, independent_wards=0,
no_pr_list_wards=0, *, lot: str | None = None)`**: after item 2's ranking, find
the group of parties whose `(surplus, votes)` equals that of `ranked[shortfall-1]`.
If that group extends past the cut, the `m` seats falling to it go to
`lot_order(group, lot)[:m]`; if `lot is None` raise `ValueError` naming the tied
codes and Schedule 1 item 13(2)(b). Untied allocations do not read `lot`.
Delete the comment at `seats.py:133-134`.

**`montecarlo.allocate_with_overhang(..., *, lot: str | None = None)`**: pass
`f"{lot}|seat|{r}"` to every `allocate` call, `r` counting from 0 across the
function (the first call, then each `level` or `deduct` round).

**`ModelRun` gains `lot: str`**, set in `run_model` as
`seats.lot_identity(target.city.slug, str(target.year), scenario["seed"])`.
The draw loop passes `lot=f"{run.lot}|draw{d}"` to `allocate_with_overhang`.

**Ward calls, `src/prediction.py`:**
- `top_party(scores, *, lot: str | None = None)`: on a tie at the top, return
  `seats.lot_order(tied, lot)[0]`; `lot is None` with a tie raises `RuleAError`.
  The caller passes the ward's key.
- `ward_calls(..., weights=None, *, lot)` builds `f"{lot}|ward|{ward}"` per ward.
- `rule_a(..., *, weights=None, ward_ids=None, lot)` passes it to `ward_calls`.
- `seats_of(prediction, council, *, order=None, lot)` passes `lot` to
  `allocate_with_overhang`. `order` stays (it fixes the pool's key order for
  the trace); it no longer decides anything.
- Module docstring "Ties": rewritten to the lot (§2 records).

`prediction` imports `seats` lazily inside `top_party` (the page's ward map
must not load the model; `seats` is stdlib-only, so this is cheap).

**Callers, every one:**

| caller | lot it passes |
|---|---|
| `build_make.forecast_data` | writes `schema["x-seat-context"]["lot"] = seats.lot_identity(ak["city"], ak["target"], ak["seed"])` from the draws manifest's `artefact_key`; `context_ref` (roster and wards only) does not move |
| `build_make.start_state` | the schema's `x-seat-context["lot"]` to `model_forecast` and `seats_of` |
| `score_forecasts.model_forecast` | `schema_context(schema)[0]["lot"]` to `rule_a` |
| `reader_seats.context_errors` | requires `"lot"`, a non-empty `str` |
| `reader_seats.reader_seats` | `context["lot"]` to `seats_of` |
| `reader_seats.context_for(..., lot)` / `context_from_run` | `context_from_run` passes `run.lot` |
| `interactive/pyboot/page.py` `_ward_calls`, `handoff` | `seats.lot_identity(*(manifest["artefact_key"][k] for k in ("city","target","seed")))` |
| `scenarios.modal_winners(winners, wards, *, lot)` and its callers `scenarios.main`, `render_sheet` (`_sc.modal_winners`, ~709) | `seats.lot_identity` from `forecast_summary.json`'s `scenario` (city, target, seed); refuse if any is missing |
| `diagnose.main` | `run_.lot` |
| `score.score_wards(ward_probs, actual, edges=None, *, lot)` | `compare_history` (~1528) `run.lot`; `backtest` (~1428) `run.lot`; `benchmarks` (~1133) `seats.lot_identity(city, year, f"benchmark:{name}")` |
| `montecarlo.main`, `ward_winner_probs.csv` (~5621) | `winner = prediction.top_party({universe[i]: count}, lot=f"{run.lot}|ward|{w}")`; `dist` keeps its order by count (display) |
| `benchmarks.council_from_shares` | `seats.lot_identity(city, year, f"benchmark:{name}")`; `canonical_order` is deleted (§1.1a) |
| `backtest.actual_result` (~994) | `seats.lot_identity(city, year, "actual")` |
| `fold.py` (~682, ~700) | `f"{fold_label}|actual"`, `f"{fold_label}|predicted"` |
| `validate_seats.py` (~86) | `seats.lot_identity(city, year, "validate")` |
| `audits/2026-10-07-prediction-restructure/backtest/rule_a.py` | `seats.lot_identity(city, year, seed)` of the run it reduces |

**1.1a `benchmarks.canonical_order` is deleted** and `council_from_shares`
passes the tally straight through. Its name rule was the only thing making the
baselines reproducible; the lot does that without a name. Its 837/841 band
(name rule and its mirror) is replaced by one figure per seed.

**Not in the population, stated:** within one draw, `ward_tally.argmax`
(`run_model` ~5231) breaks an exact float tie by universe order; the tally
carries multiplicative lognormal ward noise, so an exact tie needs two equal
floats (argued, not measured). `fold.py`'s diagnostic `max(wards[w], key=...)`
ward calls (~672) are a printed fold diagnostic. Neither is changed; both are
named in §Q2's rewrite.

**`src/interactive_template.html`'s JS `allocate`** is dead:
`build_interactive.py` raises `SystemExit` at import ("not ported",
`build_all.py:104`). Not changed; named in §Q2 so nobody reads it as a second
seat law.

### 1.2 Item 2 — integer surpluses

`seats.allocate`:
```python
surpluses = {p: v - round_one[p] * quota for p, v in combined.items()}   # int
ranked = sorted(combined, key=lambda p: (-surpluses[p], -combined[p]))
remainders = {p: surpluses[p] / quota for p in combined}                  # derived, display
```
`Allocation` gains `surpluses: dict[str, int]` and `ranking: list[str]`
(`ranked` after the lot). `remainders` stays, derived from `surpluses`.

Two parties with equal integer surplus are ordered by votes (13(2)(b), 16(4)(c));
only equal surplus *and* equal votes reaches the lot. Module docstring: add one
paragraph on the rule and the lot.

### 1.3 Item 3 — unopposed wards

- `seats.eligible_parties(ward_votes, pr_votes, unopposed_pr=None)`:
  `unopposed_pr` is `{party: its PR votes in the wards it won unopposed}`, added
  to that party's combined votes (items 12(2), 13(1)(b)); item 16(5) follows
  because `allocate_with_overhang` reads `combined`. A key not in the pool is
  ignored (an independent or a no-list party is outside it anyway).
- `levels.unopposed_wards(target, city) -> dict[str, str]`: `{ward: party}` for
  each ward with exactly one ward-ballot party — from the result file's
  `BallotType == "Ward"` rows where it exists, else from
  `pools.declared_roster(...)["wards"]` (a ward listed for exactly one party,
  `IND` counting as a party). `{}` when neither exists.
- `run_model`: after the roster block, `if levels.unopposed_wards(...)` raise
  `SystemExit` naming the wards: "Schedule 1 item 12(2): an uncontested ward is
  not modelled in the draws (MODEL-LOG §<new>)".
- `backtest.actual_result`: computes `unopposed_pr` from the result file's PR
  rows in those wards and passes it. `{}` at every city-year today.
- `prediction.seats_of` and `reader_seats` are not changed: no run, and so no
  draws file, can exist for a target with an unopposed ward.

### 1.4 Item 4 — `test_overhang` on Laingsburg's real votes

`tests/test_overhang.py`: replace `LAINGSBURG_VOTES` with the IEC's published
totals (`audits/2026-10-09-site-batch/law/sources/iec-lge2021-seat-calculation-detail-wc051-laingsburg.pdf`, read):

```python
LAINGSBURG_VOTES = {"ANC": 1694, "DA": 1530, "EFF": 74, "KDF": 1576,
                    "KGP": 41, "KOP": 395, "PA": 895, "VFPLUS": 248}   # A = 6,453
LAINGSBURG_WINS = {"DA": 3, "ANC": 1}
LAINGSBURG_COUNCIL = 7
```
Rewrite the block comment's hand arithmetic: at 7 seats, quota 922, DA
entitled to 2 against 3 wards; requota (6453 − 1530)//(7 − 3) + 1 = 1,231; the
published council ANC 2, DA 3, KDF 1, PA 1. Assertions:
- `test_the_constructed_entitlements_...`: total 6,453, DA entitlement 2;
- `test_the_laingsburg_2021_requota_...`: `seats == {"ANC": 2, "DA": 3, "KDF": 1, "PA": 1}`,
  council 7, `over == {"DA": 1}`, and the published round-two ranking:
  `allocate({k: v for k, v in LAINGSBURG_VOTES.items() if k != "DA"},
  total_seats=4).ranking == ["PA", "ANC", "KOP", "KDF", "VFPLUS", "EFF", "KGP"]`
  and its `quota == 1231`. This pins item 2's ordering to the counting
  authority's own column.
- KDF at the original quota is 2 and after the requota 1: assert both (the
  seat the clause cost it).
The other three call sites (~385, ~566, ~591) use the new constants unchanged.

### 1.5 Item 5 — records

In §2.

### 1.6 Item 6 — PA contestation, vote-weighted

- **New** `levels.slate_coverage(target, city, weights_lge) -> dict[str, float]`:
  the prototype `audits/2026-10-09-model-questions/data/scripts/votecov.py`,
  as one function. For each party `p` that `levels.contestation(target, city)`
  returns: weights = `p`'s PR votes per VD at `weights_lge` (the forecast
  target's previous LGE, for both `now` and `was`); each VD placed in its ward
  by `pools.vd_map(city, target.year)` (split VD → part with most registered);
  coverage = Σ weights in wards `p` contests at `target` / Σ weights. Slates:
  the result file's ward rows where it exists, else `[roster.wards]`. A party
  with no PR vote at `weights_lge` keeps `contestation`'s count fraction.
  `levels.contestation` is unchanged (it is the who-stands fact that
  `declared_contestation`'s completeness logic and `compare_history` ~653 read).
- `run_model` ~4238 and ~4242: `_contest` and `_contest_prev` come from
  `slate_coverage(..., weights_lge=target.previous_lge)`. The projected and
  partial paths (`projected_contestation`) run on these values as now.
- `run_model` ~4802:
  `ratio[i] = float(min(ratio[i] * (now / was), WARD_PR_RATIO_MAX))`. Delete
  the `np.clip(..., 0.0, 2.0)` literal. (Decision O3.)
- Comment ~4792-4795 (integrity F1, stale) rewritten: the change is the share
  of the party's own previous list vote in wards it contests.
- `note_constant(scenario, "contestation", ...)`: the note says "vote-weighted".

### 1.7 Item 8 — the seven certified parties, and the roster ↔ universe guard

The seven (measured, roster minus run universe, joburg 2026):
AMALGAMATED_RAINBOW_MOVEMENT, CHANGE, ECONOMIC_EMANCIPATION_FORUM,
INTERNATIONAL_REVELATION_CONGRESS, SHOSHOLOZA_PROGRESSIVE_PARTY,
THE_ORGANIC_HUMANITY_MOVEMENT, UIM. All are pool members in `pools_2026.json`,
none is seeded, all have a 2021 Johannesburg list vote (0.377% together on the
raw 2021 PR file, `universe_gap.py`; integrity F4's 0.30% was a different
measure).

`run_model`:
1. **Hoist** the previous-LGE read (`prior_lge_file`, `prior_ward`, `prior_pr`,
   `wc`, `pc`, `scenario["_prior_ward_share"]`, `prior_pr_share`, ~4690-4706)
   to just before `baseline_before_seeds` (~4330). It is moved, not copied;
   nothing between the two sites rebinds those names (read).
2. **Classify**, one function, `levels.local_record_only(roster, baseline,
   prev_local, seeds) -> list[str]`: roster parties, not `IND`/`INDEPENDENT`,
   not in `baseline`, not seeded (`seed > 0`), with `prev_local[p] > 0`.
   Called with `base_city_d` after the off-ballot drop, `prior_pr_share`, and
   `scenario["pool_seeds"]`. Stored as `scenario["_local_record_only"]`.
3. **Enter them**: `base_city_d[p] = prior_pr_share[p]` for each.
4. **Geography**: the seed placement loop (~4349-4361) runs over
   `seeds ∪ local_record_only` (one loop; the condition reads "a party with no
   national geography"). They are pool members, so `members_by_party` has
   their 2021-fitted vectors.
5. **Spine**: `_levels.spine(target, {p: v for p, v in base_city_d.items() if
   p not in local_record_only}, prior_pr_share, k=..., read_local_only=
   set(local_record_only))`. They take the spine's local-only route
   (`local × exp(mu_r)`), which `blended_centres` reads as "spine level" because
   they are in `base_city` and `spine_level`. `levels.spine` gains
   `read_local_only: frozenset = frozenset()`; a party in it is not appended to
   `local_only_unused`. Rewrite F6's comment (~1427-1436) to say who reads it.
6. **Width**: they are not seeded, so `pool_sd_shock` gives them `sd_for_party`,
   which is `level_sd_default` (they are absent from `theta_prior`'s baseline).
   JUDGEMENT-CALLS §A29 is amended: `level_sd_default` now binds, for these
   parties, named per run in `41_guards.level_sd_default_parties`.
7. **Guard**, after `universe` is built (~4387), `_roster_universe_check(roster,
   roster_state, universe, prior_pr_share, seeds, base_npe)` returning
   `{"missing_with_record", "extra", "unrepresented_no_record"}`:
   - `missing_with_record`: roster parties (not IND) with a previous-LGE list
     vote or a baseline or a seed, absent from `universe` → **SystemExit**.
   - `extra`: universe parties not on the roster, except `ENTRANT` where the
     generic slot is legitimately present → **SystemExit** when the roster
     state is `published` or `projected`.
   - `unrepresented_no_record`: roster parties (not IND) with none of the
     three → recorded in `41_guards.roster_unrepresented` (sorted names); at a
     target with no result file, **SystemExit** if non-empty.
   - Skipped (recorded as `"not_checked"`) when `roster_state == "not_yet_held"`.

### 1.8 Item 9 — the band correction (item9 FINDINGS Q5, all 15 rows)

| Q5 # | file, function | change |
|---|---|---|
| 1 | `montecarlo.make_drawer`, `pool_sd_shock` comment (~2874-2884) | Say: seeded arrivals take 0; their width is the within-pool Dirichlet (α = m·A_pool); JUDGEMENT-CALLS §<new, row 12>. Code unchanged. |
| 2 | `montecarlo.make_drawer`, `individual` loop (~2774-2786) | Delete the `seed_band` lookup and the triangular branch. A non-pooled seeded party falls to the ordinary `(centre, sd)` path; `test_pool_conservation`'s every-seeded-party-in-a-pool test keeps that unreachable. |
| 3 | `montecarlo.blended_centres` (~2036-2066) | Delete `bands`; the seeded route is `mode_level = base`. `tests/test_blended_centres.py` drops `pool_seed_bands` from its scenarios (~175-989) and the case at ~340 ("no pool_seed_bands") becomes the only form. |
| — | `montecarlo.run_model` (~4001) | Delete `scenario["pool_seed_bands"] = ...`. Rewrite the dead-store comment at ~4365-4382 to past tense, one paragraph. |
| 4 | `pools.arrival_rules` entrant note (~5106-5112) | Drop "Band … carried across as a RELATIVE width"; say "the draw's width comes from the pool split". |
| 5 | `pools.arrival_rules` weights-branch note (~4938-4941) | Drop "Band … — the declaration sets the level, the record sets the width"; same replacement. |
| 6 | `pools.py` ~4187-4193 | Delete `ARRIVAL_BAND_LO`, `ARRIVAL_BAND_HI`, their comment, `lo_e`/`hi_e` (~4896-4897), the `"band"` key of `rules[party]` (~5110-5112), `seed_bands` (~6323) and its emission (~6460). `band_for` and `_band_from` keep their four-tuple signature unchanged (`f_mid` sizes splits); at the call site `f_lo`, `f_hi` are bound to `_`. |
| 7 | `pools.py` ~5058-5066 | Comment: superseded, the band was never read (§1.198). |
| 8 | `pools.arrival_rules` docstring (~4752) | "the band on the whole thing" removed. |
| 9 | `JUDGEMENT-CALLS.md` §L2 | Retired, citing item9 finding 5. |
| 10 | `JUDGEMENT-CALLS.md` register row (~100) and §F32 (~1472) | Deleted with the constants; `tests/test_register_matches_code.py`'s `DELETED` note records it. |
| 11 | `JUDGEMENT-CALLS.md` §L13 "How to check it" | Moot: §L13 is retired by item 13. |
| 12 | `JUDGEMENT-CALLS.md`, new entry | Zero level shock for seeded arrivals: value 0; why (the split carries the width); evidence item9 finding 4 (P(≥1 seat) 0.059 → 0.064 with the size-line shock); how to check. 🟡 |
| 13 | `MACHINERY.md` ~282-285 | "each draw applies a Student-t level shock (sd 0 for seeded arrivals), …". |
| 14 | `tests/test_levers_are_live.py:840` | Delete the `pool_seed_bands` entry. |
| 15 | `tests/test_pool_conservation.py` (~550-598) | Message and docstring: no seed band exists; "2026 has no roster" corrected (the 2026 spec carries seeds). |

Also: `tests/test_chain.py` ~1819-1820 and `tests/test_regressions.py` ~196-206
read `ARRIVAL_BAND_LO/HI` and `seed_bands`; delete those assertions with the
band, each with a one-line note naming this batch. `montecarlo.py` ~1605
comment drops `ARRIVAL_BAND_LO/HI` from its list.

### 1.9 Item 10 — the smaller items

| item | file, function | change |
|---|---|---|
| a stale or unreadable pool spec stops the run | `montecarlo.run_model` (~3929-3945) | `_stale` truthy → `SystemExit(f"pools_{year}.json is stale: {_stale}. Re-emit (POOLS-REEMIT-QUEUE.md).")`. The `except Exception` sets the same refusal with `exc!r`. An escape exists only as `scenario["allow_stale_pools"] = True` (not in `DEFAULTS`; a diagnostic run sets it explicitly; the trace and `forecast_summary.json` record it). |
| γ = 1.0 default registered | `run_model` (~4568-4582); `JUDGEMENT-CALLS.md` new entry | `note_value(scenario, "gamma.default_1.0", sorted(parties), ...)`; the register entry names the rule (no fold γ and no recent γ → 1.0) and points at the note for the count. |
| city-mean turnout fallback registered | `run_model` (~4634-4640); new register entry | `note_value(scenario, "turnout.mean_fallback_vds", n, ...)` with the share of the roll; entry as above. |
| turnout band width reviewed | the writer, read-only, after the window (step 11), from arm B's runs (`ModelRun.pool_turnout_draws` and the citywide turnout per draw) | A table per pool and citywide: drawn turnout q5/q95 at joburg 2026 and at each panel city-year against the observed min/max over that city's LGEs 2000-2021, into the batch's MODEL-LOG entry. **No code change in this batch**; any change is the owner's. |
| preflight says "present" | `inputs_preflight._rows` (roll row, ~115) and `main` (~186) | The roll row carries `"used": False`; `main` prints `present` (not `ok`) for a row with `ok and not used`, and adds "the model does not read this input". `tests/test_inputs_preflight.py` asserts the word. |
| `levels._citywide` refuses a renamed column | `levels._citywide_and_roster` (~346-347) | `except KeyError as exc: raise SystemExit(f"{path}: column {exc} missing — a renamed column, not an empty election")`. |
| `bounds_checked` counts checks | `montecarlo.run_model` (~5159-5174), `ModelRun.bounds_checked` (~3469), `main` (~5505), `compare_history` (~3012) | `bounds_checked: dict[str, int]`, incremented per party inside the `if p in index and base > 0.005` test; `main` divides by `bounds_checked[p]`; `compare_history`'s `sumrate` sums both dicts. `41_guards` gains `"draws": draws`. |

### 1.9a Every change to `41_guards`, in one place

`tests/test_stage_realisation.py` (~104-128) pins the field set; change the pin
once, with all five:

| field | type | item |
|---|---|---|
| `bounds_checked` | `int` → `dict[str, int]` (per-party checks) | 10 |
| `draws` (new) | `int`, the run's draws; denominator of `overhang_count` (was mapped to `bounds_checked`, ~121) and `excessive_draws` | 10 |
| `roster_unrepresented` (new) | sorted `list[str]`, or `"not_checked"` | 8 |
| `level_sd_default_parties` (new) | sorted `list[str]` | 8 |
| `group_share_tripwire` (new) | `dict` as §1.11, or `"no record"` | 12 |

`GUARD_DENOMINATOR_KEYS` gains `draws`; the rate map: `bounds_violations →
bounds_checked` (per party), `overhang_count → draws`.

### 1.10 Item 11 — growth measured at current size

`src/levels.py`:
- New private helper `_shrink_one(obs, size, fit, mu_all) -> (mu, worth, own, target)`:
  the per-party body of `_shrunk` with the target taken at `size`. `_shrunk`
  and `theta_prior` both call it (one estimator, as §A26 requires).
- `_shrunk(record, report=None, *, current: dict[str, float])`: `size =
  current.get(party)`; a party in `record` with no positive `current` size
  keeps the observation-weighted mean size and is counted in
  `report["size_fallback"]` (no level reads it: the spine consults `mu_t` only
  where `national > 0`, `mu_r` only where `local > 0`).
- **11b**: `_shrunk` also returns, for every party in `current` with no record
  and `size > 0`, `mu = target(size)` (weight 0 on its own record). `report`
  counts them as `"at_size_centre"`. The spine's `mu_t.get(party, c_t)` and
  `mu_r.get(party, c_r)` then find them; `centre_fallback` counts only parties
  where `fit is None`.
- `spine`: `_shrunk(theta_obs, theta_shrink, current=baseline)`,
  `_shrunk(rho_obs, rho_shrink, current=prev_local)`.
- `theta_prior`: `obs_size` → `baseline.get(party)` (falls back to `obs_size`
  where it is 0, counted in its `shrink` block).
- The return stays a three-tuple; `tests/test_theta_prior.py` (~483, ~500)
  pass `current=` explicitly.
- Docstrings of `_shrunk`, `size_centre`, `theta_prior` say the size is the
  party's current one. `MACHINERY.md` §spine says so.

### 1.11 Item 12 — the group-share tripwire (reports, changes no number)

- **Record artefact.** New `src/group_share_record.py` with `--emit`, writing
  `data/processed/group_share_record.json`: for each city, each target in
  `{2011, 2016, 2021, 2026}`, `record[pool][party]` = the party's largest
  Duncan-Davis upper bound in that pool over this city's real results strictly
  before the target (LGEs and NPE files), and `margin[pool]` = the largest
  one-cycle rise of a fitted pool rate (`pools.fit_city`) by any party in any
  metro strictly before the target. The method is
  `item7/scripts/panel_rates.py`, `panel_2024.py` and `guard_probe.py`'s
  `thresholds`, as functions. The file carries an `artefact_key`
  (`pools_sha`, `deps_sha`, its own code sha) and is added to
  `declares.py` and to `tests/test_intermediates_are_current.py`.
- **Counting.** `montecarlo.make_drawer` records, per draw, each pool's
  within-pool member shares after the Dirichlet split (the quantity
  `capture.py` read from the Dirichlet call). `run_model` counts, per
  `(party, pool)` with member weight > 0, the draws in which the share exceeds
  `record + margin`; `41_guards.group_share_tripwire = {f"{party}|{pool}":
  {"draws": n, "share": n/draws, "threshold": t}}` for every pair with `share
  > 0.05`, plus `"population"` and `"scanned"` counts. Missing record file:
  `"group_share_tripwire": "no record"` (stated, not zero).
- **Reporting.** `montecarlo.main` writes `guards.group_share_tripwire` into
  `forecast_summary.json`; `build_site.py` prints one line per firing pair.
  Nothing reads it back into a draw.

### 1.12 Item 13 — the SACP like everyone else

- `judgements/joburg-2026.toml`: delete `weights` and `support` under
  `[party.SOUTH_AFRICAN_COMMUNIST_PARTY]` and the comment block above it
  (~501-509); keep the header line with a one-line pointer to the retired
  §L13. Line ~427's summary comment: the SACP is a generic entrant.
- `JUDGEMENT-CALLS.md` §L13: retired (⚪), with the owner's words and the
  pointer to this batch's MODEL-LOG entry.
- No code change. `judgements_sha` moves for the 2026 specs only.

### 1.13 Item 14 — a derived minimum before by-election evidence moves a small party

- **Derivation first, as a pre-registered measurement** (§6, P14), before any
  code. It produces two numbers: `BYE_MIN_CONTESTS` and `BYE_MIN_PARTY_VOTES`.
- **Code**, `montecarlo.blended_centres` ~2105: the gate becomes
  `weight_sum >= BYE_MIN_WEIGHT and contests >= BYE_MIN_CONTESTS and
  party_votes >= BYE_MIN_PARTY_VOTES`, the same for every party.
  `party_votes` is a new column of `byelection_party_deltas.csv`, written by
  `src/byelections.py` (the party's own votes summed over the contests that
  enter `weight_sum`). `_bye_spread` carries it.
- `montecarlo.py` module constants `BYE_MIN_CONTESTS`, `BYE_MIN_PARTY_VOTES`,
  each in `CONSTANTS_READ` (~1551) and the register, with the derivation's
  MODEL-LOG § as evidence.
- `export_draws.py` ~621-639: `reaches_model` uses the same three-part test,
  through one function `montecarlo.bye_admitted(weight_sum, contests,
  party_votes) -> bool` that `blended_centres` also calls.
- If the derivation does not settle (P14's rule), no code changes and the
  owner decides.

---

## 2. Records to change

| file | where | change | item |
|---|---|---|---|
| `JUDGEMENT-CALLS.md` | §Q2 | Rewritten: a ward tie in the simulations goes by seeded lot (key form, `seats.lot_order`); Schedule 1 item 8(2) settles a real ward tie by lot (D9: the old text said Schedule 1 has no rule). The site table keeps its history rows and gains "now: the lot" for all six, including `montecarlo.main`. Status ⚖️ statute-shaped. Names the two sites outside the population (§1.1). | 1, 5 |
| `JUDGEMENT-CALLS.md` | register row ~249 ("a reader edits the combined vote") and §M1 | Amended: an equal surplus goes to the higher vote (13(2)(b), 16(4)(c)); only an equal surplus and equal vote reaches the lot, where the statute is silent. Dated amendment, original text kept. | 1, 2, 5 |
| `JUDGEMENT-CALLS.md` | new §Q5 (or next free) | D1/D2: a party with ward candidates and no list is removed from A and its ward seats from the denominator (`seats.outside_pool_wards`), and the re-quota denominator is C − (D + E + F): both follow the IEC's published formula (the Laingsburg report prints Q = (A−B)/(C−(D+E+F))+1), not the statute's text, which has no such term. ⚖️ judgement, the counting authority's practice. How to check: a Seat Calculation Detail with F > 0. | 5 |
| `JUDGEMENT-CALLS.md` | new entries | the seeded lot for exact remainder ties (statute silent); zero level shock for seeded arrivals (Q5 #12); γ = 1.0 default; city-mean turnout fallback; `BYE_MIN_CONTESTS`, `BYE_MIN_PARTY_VOTES`; the group-share tripwire's threshold (record + largest one-cycle rise, 5% of draws) | 1, 9, 10, 12, 14 |
| `JUDGEMENT-CALLS.md` | §L2 retired; §L13 retired; §F32 and register row deleted; §A29 amended; §F35 notes the contestation change's upper clip | 9, 13, 8, 6 |
| `JUDGEMENT-CALLS.md` | §A42 ("the arrival boundary") | Note: a roster party with a previous-LGE record and no national baseline is no longer outside the run (item 8); the no-record residual is named per run. | 8 |
| `src/seats.py` | module docstring, `allocate` | integer surplus, the lot; delete the "lot … unreachable" comment | 1, 2 |
| `src/reader_seats.py` | docstring "Ties" (~80-84) | the lot, key from the context | 1 |
| `src/prediction.py` | docstring "Ties" | the lot | 1 |
| `src/benchmarks.py` | module docstring (~48), `uniform_swing_roster` (~798-883) | the name rule is gone; the ActionSA "coin toss" paragraph says the lot decides it, by seed | 1 |
| `src/export_draws.py` ~40, `src/overhang_regimes.py` ~71 | comments on the tie order | the lot | 1 |
| `src/levels.py` | `spine` F6 comment; `_shrunk`, `theta_prior` docstrings | items 8, 11 | 8, 11 |
| `MACHINERY.md` | ~282-285; the spine section; the seat section | items 9, 11, 1-2 | |
| `MACHINERY.md` lines 154 and 426-429 | the capacity guard described as if it fires (integrity F2) | say it cannot fire (every party has weight in every pool) and point at the tripwire | 12 |
| `MODEL-LOG.md` | new § (append) | what was / what is / measurements, per §6's runs; Johannesburg 2016's rule-A row recomputed; tie counts; the empty unopposed population; the re-emit's `pools_sha` | all |
| `DATA-QUALITY.md` | new item | the roster's no-record residual per backtest city-year (`41_guards.roster_unrepresented`) | 8 |
| `POOLS-REEMIT-QUEUE.md` | new row (next number above the highest in this file and in `audits/ULTRA-REVIEW-1-pools-reemit.md`) | this batch's `pools.py` and `levels.py` changes, landed in the window; rows 19, 20, 26-28, 31-33 stay queued (O6) | 9, 10, 11, 12 |
| `prereg/` | new file, before the run | §6 | |
| `site/` and `content/` copy that quotes the SACP's 1.31% or describes the seat tie rule | owner's publication process | not this batch's; listed for the next site brief | 13, 1 |

---

## 3. Guards

Each guard: population (and how it is asserted to be the scanned set), the
constructed violation, the revert, and the file. "Value" guards are not
absence-shaped; "scan" guards meet CLAUDE.md §4's four requirements.

| # | guard | kind | population | constructed violation → caught; reverted → quiet | file |
|---|---|---|---|---|---|
| G1 | the lot decides an exact tie, deterministically, name-free | value | constructed councils | (a) two parties equal on surplus and votes straddling the cut: winner = `lot_order(...)[0]` for key K, identical on 3 calls; a different key K' (search the first 20 keys for one) gives the other party. (b) Over 1,000 keys, each of two tied parties wins between 0.45 and 0.55; renaming one code to sort last leaves both inside the band. (c) `lot=None` with that tie raises; with no tie, `lot=None` returns the old council. | `tests/test_seats.py` |
| G2 | the ward lot, same three properties, through every caller | value | the six ward-call sites | a constructed `ward_winners` with ward W tied: `prediction.ward_calls`, `score_forecasts.model_forecast`, `build_make.start_state`, `page._ward_calls`/`handoff`, `scenarios.modal_winners`, `score.score_wards`, `montecarlo.main`'s winner column give one party, the same one, for one lot; another lot flips it (key searched as G1). Extends `tests/test_prediction_rule.py`'s existing tie-through-every-caller test (~373-464). | `tests/test_prediction_rule.py` |
| G3 | build, page and scorer hold one lot | value | `forecast.json` | `x-seat-context["lot"] == seats.lot_identity(manifest artefact_key)`; mutate the manifest seed → the build's lot changes and the page's (computed from the manifest) agrees | `tests/test_prediction_rule.py`, `tests/test_served_draws.py` |
| G4 | no name order reaches a result | value | constructed | swap two codes in an untied council and in an untied ward set → the swapped answer; shuffle the input dict order of a tied council 24 ways (`allocation_outcomes_over_orderings`, `test_stage_realisation` ~817) → one outcome (was: more than one) | `tests/test_stage_realisation.py`, `tests/test_roster_aware_baseline.py` (replacing its `canonical_order` tests at ~118 and ~590-608) |
| G5 | integer surplus | value | constructed | two parties whose float remainders misorder but integer surpluses are equal: the higher vote wins; with float ranking restored (mutation) the test fails | `tests/test_seats.py` |
| G6 | Laingsburg | value | the IEC's published case | §1.4; mutation: re-quota denominator `C − D + 1` or float ranking → fails | `tests/test_overhang.py` |
| G7 | unopposed wards | scan + value | every ward of the 40 metro LGE files and the 2026 declared slates; asserts the count of wards scanned equals the sum of the files' ward counts (two-sided, `_support.scanned`) | constructed slates with one ward listing one party → `unopposed_wards` returns it and `run_model`'s check refuses; reverted → `{}`. Seat law: hand-computed council with an unopposed ward, counted twice | `tests/test_unopposed.py` (new) |
| G8 | roster ↔ universe | scan | the roster at each runnable target, classified into the three classes; asserts classes partition the roster | constructed `roster/universe/prev_local/seeds` dicts: a with-record party missing → refused; an extra universe party → refused; a no-record party → recorded, refused only when `has_result_file` is false; reverted → quiet. Plus one in-process `run_model` at joburg 2026, 20 draws, asserting the seven are in `run.universe` | `tests/test_roster_universe.py` (new) |
| G9 | the contestation change has one definition and the upper clip | value | constructed `now/was` | `slate_coverage` on a constructed 3-ward city equals the hand value; a party with `now = 0` gets ratio 0 (would be 0.5 under the brief's literal floor); `ratio·now/was = 3` → 2.0 | `tests/test_declared_ward_slates.py` |
| G10 | stale spec stops the run | value | constructed | a spec dict with a moved `pools_sha` → `run_model` raises; `stale_reason` raising → refuses; `allow_stale_pools=True` → runs and records it | `tests/test_stage_inputs.py` |
| G11 | `_citywide` refuses a renamed column | value | constructed CSV | a file with `Party_Votes` renamed → `SystemExit`; original → shares | `tests/test_citywide_table.py` |
| G12 | `bounds_checked` is a per-party denominator | value | constructed | `test_stage_realisation`'s denominator predicate (~630-636) checks `bounds_checked[p] <= draws` and `bounds_violations[p] <= bounds_checked[p]`; `overhang_count` maps to `draws`; violation: a payload with `bounds_violations[p] > bounds_checked[p]` → caught | `tests/test_stage_realisation.py`, `tests/test_scoreboard_disclosure.py` (~81) |
| G13 | item 11's size is the current one | value | constructed record | two parties with identical observations and different `current` sizes get different `mu`; passing obs-mean sizes as `current` reproduces the old values exactly; `theta_prior` and `_shrunk` agree party for party (existing §A26 test, widened to `current`) | `tests/test_theta_prior.py`, `tests/test_spine.py` |
| G14 | the tripwire can see | scan | every `(party, pool)` with member weight > 0; `population == scanned` asserted | constructed drawer output with one party at `record + margin + 0.1` in 50% of draws → fires; at `record` → quiet. In-process at joburg 2026 (200 draws): `population` equals the count of positive member weights in the spec | `tests/test_stage_realisation.py` (new predicate `faults_group_share`, registered in its table) |
| G15 | the record file is current | regenerate | `group_share_record.json` | purge and rebuild in an isolated tree; byte-equal | `tests/test_intermediates_are_current.py` |
| G16 | by-election gate, one definition | value | constructed rows | `bye_admitted` on rows at, below and above each threshold; `export_draws`' `reaches_model` equals `blended_centres`' admission for every row of the real CSV | `tests/test_export_draws.py`, `tests/test_blended_centres.py` |
| G17 | no `seed_bands` reader survives | scan | `src/*.py` | grep for `pool_seed_bands`, `seed_bands`, `ARRIVAL_BAND_` → empty; a constructed source string containing one is caught | `tests/test_levers_are_live.py` (the register's own deleted-name check) |
| G18 | the preflight word | value | `inputs_preflight._rows` on a constructed snapshot dir | the roll row prints `present` and "does not read"; the other rows unchanged | `tests/test_inputs_preflight.py` |

---

## 4. Targeted tests (iterate with these; the whole suite once, §7)

```
.venv/bin/python tests/run_all.py -k seats -k overhang -k prediction_rule \
  -k reader_seats -k score_forecasts -k stage_realisation -k roster_aware_baseline \
  -k scenarios -k unopposed -k roster_universe -k declared_ward_slates \
  -k stage_inputs -k stage_estimation -k citywide_table -k inputs_preflight \
  -k scoreboard_disclosure -k theta_prior -k spine -k blended_centres \
  -k pool_conservation -k chain -k regressions -k register_matches_code \
  -k intermediates_are_current -k export_draws -k served_draws -k levers_are_live \
  -k standalone_modules -k model_index -k temporal
```
`-k levers_are_live` is the slow one: run it once, after item 9 and item 14.
`test_temporal` because items 8, 12 and 14 add reads of past elections.
`test_standalone_modules` because `group_share_record.py` is a new entry point
(add it to CLAUDE.md §5's block and to `ENTRY_POINTS`).

---

## 5. Re-emit and batching

**A re-emit is required.** `levels.py` is in `pools._EMIT_DEPENDENCIES`
(`pools.py:357`), so items 10 (`_citywide_and_roster`), 11 (`_shrunk`,
`theta_prior`, `spine`), 3 (`unopposed_wards`), 6 (`slate_coverage`) and 8
(`local_record_only`) move `deps_sha` for every spec. Item 9 rows 4-6 move
`pools_sha`. Item 13 moves `judgements_sha` for the two 2026 Johannesburg
specs. With item 10's refusal, an un-emitted spec stops every run, the suite
included: **the emit must come before any measurement and before the suite.**

Current state (measured, `stale_reason` over every spec): 27 specs, one
`pools_sha` (`c70b8fc5bcd79279`), none stale.

**Item 10's `_citywide` refusal cannot fire inside the window** (measured,
inline probe over `data/raw/elections/*.csv`): 88 of 90 files carry
`sPartyName` and `Party_Votes`; the two that do not are the original
downloads `lge2016_JHB_vd_party.csv` and `lge2021_JHB_vd_party.csv`, and
`cityconfig`'s LGE template names the `_clean` files (read: `Target.results`
returns `lge{year}_{CODE}_vd_party_clean.csv`), so no run or emit opens them.

**Is the re-emit number-neutral?** Expected yes for items 3, 6, 8, 9, 10, 11:
`pools.py` calls `levels._citywide`, `_held_back`, `HELD_BACK`,
`absent_from_ballot`, `contestation` and `projected_contestation` only (read),
none of which changes behaviour on present inputs. Item 13 is not neutral: it
re-sizes the SACP and, through the group rescale, every generic entrant in the
2026 spec. Check: before the batch's measurement, diff each re-emitted spec
against its predecessor field by field (excluding `artefact_key`,
`seed_notes`, `seed_bands`); only `pools_2026.json` and
`pools_2026_simulation.json` may differ, and only in `seeds`, `seed_notes`,
`seeded_arrival_mass`, the SACP's pool membership, and fields derived from
those.

**The window** (`POOLS-REEMIT-QUEUE.md` steps 1-4): one commit with every
`pools.py`/`levels.py`/judgement change of this batch; the loop including 2011
and both 2026 Johannesburg specs and Tshwane 2026; count against the loop;
`group_share_record.py --emit`; then the measurement. Nobody else runs the
model while it runs. Queue rows 19, 20, 26, 27, 28, 31, 32, 33 stay queued
(O6).

---

## 6. Pre-registration draft

To be committed as `prereg/2026-10-09-model-correction-batch.md` **before** the
first measurement run, and never edited after. Every prediction is against the
world or the mechanism; none is against a published or earlier output. Runs:
in-process `run_model` + `compare_history.run_city_year` (no `history.json`
written), the 24 city-years `compare_history.runnable` returns, 1,000 draws,
seeds as `compare_history` derives them, `PYTHONHASHSEED=0`; Johannesburg 2026
at the published seed, 5,000 draws. Arms: **A** the tree before the batch
(re-emitted? no: the pre-batch tree with its own specs, run from a `git
archive` of 597ec38 into a scratch tree), **B** items 1-6, 8-10, 12, 13 (the
batch without 11 and 14), **C** = B + 11a, **D** = C + 11b, **E** = D + 14.
B-E share draws and seeds. Separating 11a, 11b and 14 is what makes each
attributable; B carries everything predicted to be near-null on the panel.

### P1-P2 (items 1, 2): ties
- **P1.** Johannesburg 2026, 5,000 draws: the number of draws in which an
  `allocate` call meets an exact tie (equal integer surplus and equal votes)
  straddling the cut is reported per arm (instrument: a counter on
  `seats.allocate`, the `tie_at_the_cut` detector rewritten to integer
  surpluses). Prediction: more than 0 (joburg 2021 hit three in 400 draws,
  `test_stage_realisation` docstring), under 2% of draws. In draws without a
  tie the seat vector is identical between A and B **if nothing else in B moved
  that draw**; since items 6, 8 and 13 move every draw, this is asserted on a
  separate arm B0 = A + items 1-2 only, where it must hold exactly.
- **P2.** On the panel, rule A's prediction (`backtest/rule_a.py`, `seats_of`
  with the lot) differs from A's only at city-years with an exact seat tie; at
  Johannesburg 2016 (AIC and TRULY_ALLIANCE tied on 3,743, MODEL-LOG §1.291)
  rule A's seat error is 28 or 30, by the lot. Tied wards per city-year: 0 at
  all 24 (as measured in §1.291) — a non-zero count falsifies that record.
- **P2b.** Baselines (`benchmarks`): `uniform-swing+roster`'s panel total lies
  inside [837, 841], the band the name rule and its mirror spanned.

### P3-P5, P9, P10 (items 3, 4, 5, 9, 10): nulls
- Item 3: `unopposed_wards` returns `{}` at all 24 city-years and at 2026; no
  number moves.
- Item 4: the test pins the IEC's council; no model number moves.
- Item 9: on arm B0 + item 9, `pr_share_draws`, `seat_draws` bit-identical to
  B0 (`band[1] = 1.0`; the branch is unreachable).
- Item 10: bit-identical draws, except that a stale spec now refuses (none is
  stale after the window).
- Item 12: bit-identical draws with and without the tripwire's counting.
  Prediction at joburg 2026 on arm B: the PA/Coloured pair fires in more than
  50% of draws (item 7 measured 69% before items 6 and 8); after D, still
  above 25% (item 11 moves the PA's spine level by −6%, measured, so the
  overrun is not removed by this batch).

### P6 (item 6): restated from `PREREG-ward-list-fix.md`, plus the clip
F1-F6 and B1-B3 as written there, scored on arm B against arm A, with one
amendment registered here before the run: CHANGE enters the run (item 8) with
an empty 2026 slate, so its ratio is 0 and its ward vote is 0 in every draw
(under the brief's literal `[0.5, 2.0]` clip it would be 0.5 × its list share).
Because item 8 and item 13 also move every draw in B, F2/F4/F5 are scored on
B and on an arm B6 = A + item 6 alone; B6 must reproduce the investigation's
numbers within draw noise (PA seats 16.85 ± 0.5, PA gap −0.19 ± 0.1).

### P8 (item 8): the seven, and the panel
- 2026: the seven take, together, a mean list share of 0.2-0.5% (their 2021
  raw share 0.377%, times the local-only route's ρ centre for parties of their
  size, before renormalisation; argued from the spine route). Each is below
  0.15%; together they win 0 or 1 seat in more than 80% of draws.
  CHANGE's mean ward share is 0. The mass comes out of every other party in
  proportion (renormalisation).
- Panel: the city-years with with-record roster parties outside the universe
  (from `universe_gap.py`): joburg 2011 (3, 0.857% of the previous LGE list),
  2016 (3, 0.553%), 2021 (1, 0.005%); tshwane 2011 (2, 0.403%), 2016 (2,
  0.162%); ekurhuleni 2011 (1, 0.215%); ethekwini 2021 (1, 0.080%); capetown
  2011 (1, 0.152%), 2016 (2, 0.320%); mangaung 2016 (1, 0.012%);
  nelsonmandelabay 2011 (2, 0.367%), 2016 (1, 0.092%). At these 12, list MAE
  falls or holds (those parties' predicted share moves from 0 toward a real
  positive result); at the other 12, item 8 moves nothing. Panel coherent seat
  error: falls by 0-6 seats from item 8 alone (scored on B8 = A + item 8).
- `41_guards.roster_unrepresented` non-empty at the city-years `universe_gap.py`
  lists and empty at 2026.

### P11 (item 11): per party, against the mechanism
The spine-level change is computed, not run (`item11_spine.py`), so the
prediction is the propagation through the rest of the model, which is
monotone in a party's centre before renormalisation.
- **11a (arm C against B), joburg 2026.** Spine-level Δlog: PA −0.061, AIC
  +0.022, GOOD +0.039, UDM +0.013, every other party within ±0.01. Prediction:
  PA mean seats fall by 0.5-2.5 from arm B's value; no other party moves by
  more than 0.6 seats; the DA and ANC each gain 0-1.5. **Not** b2's −12.8:
  that came from dropping the PA's own record.
- **11b (arm D against C), joburg 2026.** Spine-level Δlog: MK −0.130; BOSA
  +0.087; RISE +0.049; ASA −0.033; national-only small parties (ARISE_SOUTH_AFRICA,
  UNITED_AFRICANS_TRANSFORMATION, ALLIED_MOVEMENT_FOR_CHANGE, HOPE4SA, DUDULA,
  ACTION_ALLIANCE_DEVELOPMENT_PARTY, SOUTH_AFRICAN_RAINBOW_ALLIANCE) +0.24 to
  +0.30; local-only parties (PARTY_OF_ACTION, ABANTU_BATHO_CONGRESS, UIM, DOP,
  BLACK_FIRST_LAND_FIRST, …) +0.12. Prediction: MK mean seats fall by 1.5-4;
  ASA by 0-1.5; BOSA, RISE each gain 0-0.7; each small party gains under 0.3;
  ANC, DA, EFF each gain 0-1.5 from MK's loss.
- **Panel (arms C and D against B).** The panel's spine-level changes are in
  `item11_<city>_<year>_b{0,1}.json` (computed before this draft; summarised in
  §6a below). Prediction: list MAE moves by less than 0.05 points at every
  city-year under 11a; under 11b the panel-mean list MAE falls (small
  national-only parties gain going local, which is what `size_centre` measured
  and what the flat mean erased), by 0.00-0.05 points; coherent seat error
  moves by at most ±6 seats under each. A panel-mean list MAE rise above 0.05
  points under 11b falsifies the mechanism account.

### P13 (item 13): the SACP
SACP centre falls from 1.62% (stage 30_centres, item 9 table) to the generic
entrant level for its reach, 0.06-0.10% (§L13 measured ≈0.06% for this route;
item 9's reach-1 entrants sit at 0.086% centre). Its mean seats fall from 3.49
to under 0.3; P(≥1 seat) from 0.69 to under 0.12. Its ~1.3 points of mass go
mostly to the ANC (its pool vector is now the even city spread, not ANC-shaped,
so ANC gains less than the whole: predict ANC +1 to +3.5 seats, DA +0 to +1.5).
Every generic entrant's seed moves by under 3% (the group rescale gains one
member). No backtest number moves.

### P14 (item 14): the derivation, then the effect
**Derivation (before the gate is coded).**
- Population: every (party, metro) with by-election evidence dated before
  2024-05-29 in `data/raw/byelections/byelections_SA_vd_party.csv` (measured:
  30 contests, 75 pairs, 40 with ≥ 2 contests). Outcome: the party's change in
  citywide share from the 2021 LGE list ballot to the 2024 provincial ballot
  in that metro (`npe2024_<CODE>`), the only real result after these
  by-elections. The cross-ballot step is a limit, stated wherever the result is
  quoted.
- Predictor: the model's own tilt — `byelections.py`'s weighted delta for that
  party, computed with the 2024 election date as the target date — against no
  tilt. Error: absolute error of `base + w_bye × delta_pr` against `base`,
  in points, by bins of contests (1, 2, 3-4, 5+) × party votes
  (< 250, 250-1,000, > 1,000), for parties under 1% base and over 1%.
- Rule, fixed now: `BYE_MIN_CONTESTS` and `BYE_MIN_PARTY_VOTES` are the
  smallest bin edges at which the tilted error is below the untilted error for
  parties under 1%, with every larger bin also below. If no bin under 1% beats
  no tilt, the minimum is "never for a party under 1%" and that goes to the
  owner as the derived answer. If any cell holds fewer than 5 pairs, the
  adjacent bins merge before the rule is applied. Secondary (reported, not
  deciding): leave-one-contest-out within the 311 contests nationally, the same
  bins, predicting a held-out contest's delta from the others'.
- Not chosen against the All Citizens Party (2 contests, 198 party votes,
  weight 49.55): whatever the rule yields is applied to it, and if it is
  admitted the owner is told before the code lands.
**Effect (arm E against D), joburg 2026.** Parties at or above weight 30
today: ANC, EFF, DA, MK, AIC, PA, ASA, ALL_CITIZENS_PARTY, ATM, IFP,
TRUTH_AND_SOLIDARITY_MOVEMENT (`byelection_party_deltas.csv`, read). Predicted
per party: those with ≥ 4 contests are unaffected unless the derived vote
minimum exceeds their party votes. If ALL_CITIZENS_PARTY is excluded, its
centre returns to its arrival seed region (item 9 measured 0.050% list mean at
`w_bye = 0`), its mean seats fall from about 2 to under 0.2, and TRUTH_AND_SOLIDARITY
(2 contests) falls from 0.111% to about 0.06% centre. No backtest number moves
(the by-election archive starts 2022; no backtest target reads it).

### 6a. Item 11 on the panel (computed before this draft)
Measured, `item11_spine.py` over the 24 panel city-years (spine level only,
inputs approximating the run's: raw previous-NPE and previous-LGE list shares,
no mergers, drop or seeds). Parties at 0.1% or more in either arm:

| arm | party-city-years | median abs Δlog | 90th percentile abs Δlog | parties ≥ 0.5% with abs Δlog ≥ 0.10 |
|---|---|---|---|---|
| 11a alone | 398 | 0.001 | 0.012 | none |
| 11a + 11b | 379 | 0.006 | 0.133 | NFP at Ekurhuleni 2016 (0.624% → 0.554%) and eThekwini 2016 (2.464% → 2.783%) |

So on the panel 11a is near-inert and 11b reaches mainly parties under 0.5%.
The P11 panel predictions above are stated against these figures.

---

## 7. Writing order, and where the suite runs

One writer. Each step ends with its targeted modules (§4) green.

1. **Law layer.** Item 2 (`seats.allocate` integer surplus, `Allocation`
   fields), then item 1 (`lot_identity`, `lot_order`, `allocate(lot=)`,
   `allocate_with_overhang(lot=)`, `ModelRun.lot`, every caller in §1.1, delete
   `canonical_order`), then item 4's test. Tests: G1-G6.
2. **Records for 1, 2, 5** (§2 rows marked 1, 2, 5).
3. **Item 3** (G7). **Item 10** except the stale-spec refusal (G11, G12, G18;
   register entries).
4. **Item 9** montecarlo/test/record parts (rows 1-3, 9-15), then its
   `pools.py` rows 4-8 (G17).
5. **Item 8** (G8), **item 6** (G9).
6. **Item 11** (G13). **Item 12** code and `group_share_record.py` (G14,
   G15). **Item 13** judgement file and register.
7. **Item 14 derivation** (read-only, its own pre-registered section),
   then the gate (G16) — or, if the derivation does not settle, stop and report.
8. **Item 10's stale-spec refusal last** (G10), so steps 1-7 can run the model.
9. **Commit the pre-registration** (§6, filled: P14's derived thresholds go in
   before arm E runs).
10. **The window**: commit, re-emit, count, `group_share_record.py --emit`,
    the spec diff check (§5).
11. **Measurement**: arms A, B0, B6, B8, B, C, D, E on the panel and 2026, on
    the settled tree, nothing else running.
12. **Regenerate generated documents** (`src/model_index.py`), then
    **the whole suite once** (`tests/run_all.py`, full log read, no pipe).
13. **MODEL-LOG** entry with the scored pre-registration; `prereg/README.md`
    row; then the publishing run (`montecarlo.py` without `--run-dir`) and
    the draws export are the owner's.

---

## 8. Risks and estimate

| risk | where | mitigation |
|---|---|---|
| A caller of `allocate`/`top_party` is missed and meets a tie with `lot=None` | §1.1's table | fail-closed by design (raises on a tie only); G2's every-caller test; `test_prediction_rule`'s scan |
| The page computes a different lot from the build | `page.py` reads the manifest; build writes the schema | G3 |
| Item 11 and 11b move MK and small parties more than predicted | `levels` | arms C and D separate it; the owner may strike 11b |
| Owner expected b2's PA effect from item 11 | O1 | stated first in this document |
| Item 8 adds parties at `level_sd_default` | `pool_sd_shock` | named per run; §A29 amended |
| The re-emit is not neutral beyond the 2026 specs | §5 | the field-by-field diff before measuring |
| Item 14's record is too thin to settle | O7 | the rule says what happens; owner decides |
| The stale-spec refusal blocks the writer mid-batch | item 10 | landed last (step 8) |
| `group_share_record.py` is slow (one `fit_city` per metro-year) | item 12 | run once per window, keyed |
| The seven parties' `_vd_pool_composition` placement differs from their real 2021 geography | item 8, step 4 | argued: the vectors are fitted on 2021 ward data; their own per-VD shares were rejected because the 2021 and 2024 VD keys differ and it would be a second placement rule |

**Estimate** (writer time, excluding the owner): law layer and callers 5-7 h;
records 2 h; items 3, 10 2-3 h; item 9 2 h; items 8, 6 4-5 h; item 11 2 h; item
12 4-6 h; item 13 0.5 h; item 14 derivation 3-4 h and gate 1 h; window 1 h;
measurement (eight arms × 24 city-years × 1,000 draws, plus 2026 at 5,000,
6 in parallel) 4-6 h wall; suite one run; MODEL-LOG 2 h. About 35-45 hours of
work over 3-4 days.

---

## Revision 2 (2026-10-09, after the owner's decisions on this specification)

The owner's answers (`BRIEF.md`, "Owner's decisions on the specification"):
O4 accepted; O6 accepted (one re-emit window, this batch only; queue rows 19,
20, 26-28, 31-33 stay queued); writing approved. Items 16-19 are added; item 19
replaces item 14 (§1.13, P14, G16 above are superseded by R2.4 and are kept
only as history). Everything above that this revision does not name stands.

New probe for this revision (read-only, same scratch directory):
`item16_spine.py` (the spine level with each party's own observations limited
to those within a log-size window `H16` of its current size, plus 11b).

### R2.1 Item 16 — a party's own record counts only from elections at a similar size

**Mechanism.** In the shared helper `levels._shrink_one` (§1.10), before the
own mean is taken, keep only the party's observations `(r, sz)` with
`|ln sz − ln current| ≤ h`, where `current` is the party's current size on that
record's route (national share for θ, previous-local share for ρ). If none
survive, the party has no own record on that route: weight 0, and it takes the
size-group centre at its current size (item 11; item 17 for its width). Applied
to every party, in `_shrunk` and in `theta_prior` alike, through the one
helper. `worth` (the spine's blend key) is computed over the surviving
observations only, so a party whose record is all from another size also loses
its record's pull in the blend.

**The window is derived, per target, never typed as a value.** New
`levels.size_window(target, record_fn) -> (h, report)`, called once per record
(θ via `theta_record`, ρ via `local_record`), so θ and ρ each get their own
window:

1. Walk the calendar's targets `T_1 < … < T_k ≤ target` (only targets strictly
   before `target` contribute evaluation data; the window used at `target`
   reads nothing at or after it, which `test_temporal` asserts).
2. The *new* observations at `T_j` are `record_fn(T_j)` minus
   `record_fn(T_{j−1})`, as multisets per party.
3. For each new observation `(r, sz)` of party `p`, predict `ln r` from `p`'s
   record at `T_{j−1}` by `_shrink_one` with `current = sz` and window `h`
   (the size-centre fit also taken from the record at `T_{j−1}`).
4. Score: reliability-weighted mean absolute error in `ln r`, over every new
   observation of every party in every metro.
5. Candidate grid (typed, and registered as such): `h ∈ {0.25, 0.5, 0.75, 1.0,
   1.5, 2.0, 3.0, ∞}` in natural-log units of size (1.0 ≈ a factor of 2.7).
   `h` = the grid value with the lowest error; a tie within 0.005 goes to the
   wider value. Fewer than 20 scored observations → `h = ∞` (no filter, item
   11a's behaviour), reported as `"underdetermined"`.
6. `report` carries the error at every grid value, the count scored and the
   choice; `run_model` records it with `note_value(scenario,
   "levels.size_window.theta"/"…rho", h)` and writes the table into the
   `20_spine` trace.

**Register.** JUDGEMENT-CALLS new entry: the window rule (the grid and the
tie rule are typed; the value is measured per target). 🟡 "measured, the grid
chosen".

**Guards.**

| # | guard | kind | constructed violation → caught; reverted → quiet | file |
|---|---|---|---|---|
| G19 | the filter | value | a party with observations at 0.02% and 3% and current size 3%: at `h = 1` only the 3% observation enters its mean; at `h = ∞` both; with every observation outside the window, its `mu` equals the size centre at 3% and its `worth` is 0. `h = ∞` reproduces item 11a's values exactly on the real record. | `tests/test_theta_prior.py` |
| G20 | the derivation can see | value | a constructed record whose new observations equal the party's near-size history and differ from its far-size history → the derivation returns a finite `h`; a record where size carries nothing (identical ratios at all sizes) → `∞` by the tie rule; fewer than 20 scored → `"underdetermined"` | `tests/test_spine.py` |
| G21 | no look-ahead | scan | spying file opens (the existing `test_the_level_prior_reads_no_election_at_or_after_its_target` pattern): `size_window(T)` opens no election file dated at or after `T`; population = every runnable target, asserted equal to `compare_history.runnable`'s | `tests/test_temporal.py` |

**Measured before this draft** (`item16_spine.py`, Johannesburg 2026, spine
level only, inputs as in §6a, 11b on, against the current tree's level; the
window is the derivation's to choose, so three candidates are shown):

| party | now | h = 0.5 | h = 1.0 | h = 2.0 |
|---|---|---|---|---|
| PA | 6.43% | 2.25% | 2.61% | 2.61% |
| ANC | 27.99% | 26.24% | within ±5% in log | within ±5% in log |
| EFF | 12.23% | 11.13% | 11.48% | within ±5% in log |
| MK | 11.31% | 9.93% | 9.93% | 9.93% (11b, not item 16) |
| IFP | 1.34% | 1.60% | 1.51% | within ±5% in log |
| VFPLUS | 0.76% | 0.83% | 0.82% | within ±5% in log |
| PAC | 0.28% | 0.26% | 0.26% | within ±5% in log |

The PA's θ observations sit at bases of 0.014%-0.29% (item 7) against a
current 2.9%, a log distance of at least 2.3, so any window below 2.3 removes
its whole θ record, and its ρ record (2016 local base) likewise. That is the
b2 candidate's effect, reached by a rule applied to every party: item 7 measured
b2 at 11.15 PA seats alone and 7.73 on item 6.

### R2.2 Item 17 — no-record parties: their size group's average and range

The average is item 11b (§1.10): `mu = size_centre` at the party's current size.
The range: a no-record party's level shock sd is the size-group width at its
current size, from the same function `theta_prior` uses for every party with a
baseline. That function (`sd_for`, today a closure in `theta_prior`) is lifted
to module level as `levels.size_sd(size)`, one definition; `theta_prior` calls
it. In `montecarlo.make_drawer`, `sd_for_party(p)` becomes
`sd_measured.get(p)` if present, else `levels.size_sd(base_city[p])`; the
`level_sd_default` fallback remains only for a party with no size at all
(`base_city[p] ≤ 0`), counted in `41_guards.level_sd_default_parties`.

This replaces §1.7 step 6: the seven item-8 parties take `size_sd` at their
2021 local share, not `level_sd_default`; §A29 is amended to say
`level_sd_default` binds only where no size exists. Seeded arrivals keep sd 0
(item 9's judgement): they are drawn by the pool split, and item 17 does not
reach them.

Item 17 is arm D (formerly "11b"). Guard G22 (`tests/test_spine.py`): a
constructed no-record party at 0.1% and at 10% gets `mu = size_centre(size)`
and `sd = size_sd(size)` at each; `sd_for_party` for a party absent from
`_theta_sd` returns `size_sd`, and `level_sd_default` only when its base is 0.

### R2.3 Item 18 — the SACP as a normal new party

As §1.12 (item 13), unchanged. The owner's question "split or new entrant?" is
answered by the specification as "new entrant": no `parent`, no `weights`, no
`support`. Its alliance status is a comment in the judgement file and a sentence
in the retired §L13, not a mechanism. P13 stands.

### R2.4 Item 19 — by-elections weighted by their incremental, out-of-sample value

Replaces §1.13, P14 and G16.

**The question.** Did by-election evidence, historically, predict the next real
result beyond what the model predicted without it? Its weight is the measured
increment; if none is measurable, the weight is zero. Every party, the same
rule.

**Population.** Every (party, metro) pair with at least one by-election
contest in a metro, in `data/raw/byelections/byelections_SA_vd_party.csv`, dated
before 2024-05-29, and with a list vote at the 2021 LGE or the 2024 provincial
ballot in that metro. Measured: 30 metro contests, 75 party-metro pairs, 40
with two or more contests. The next real result after these by-elections is the
2024 provincial ballot (`npe2024_<CODE>`); the archive starts 2022-02, so no
local election follows any by-election in it. **This is the whole record, and
it is a cross-ballot test: by-elections are local ward contests, the outcome is
a national-provincial ballot.** Stated at every quotation.

**The model's baseline prediction of that result,** without by-elections:
the 2021 LGE list share converted to the national ballot by the model's own
national-local relation at the party's size — `B = s_2021 / exp(mu_θ(p))`,
with `mu_θ` from `_shrunk` on `theta_record` for a 2024 target (items 11, 16
and 17 applied, the record strictly before 2024). Where the party has no 2021
list share, `B` is 0.

**The augmented prediction:** `B + w · δ_pr`, where `δ_pr` is `byelections.py`'s
weighted delta for the party in that metro with the target date set to
2024-05-29 (same `τ`, same similarity weight), converted to the PR scale as
`blended_centres` does.

**The test.**
1. Residual `e = actual_2024 − B`.
2. `w` is estimated leave-one-metro-out: on the seven other metros, the
   least-squares slope of `e` on `δ_pr` through the origin, floored at 0.
   Two size classes, each with its own `w`: parties under 1% of the 2021 list
   in that metro, and parties at 1% or more.
3. Out-of-sample gain per class: `G = mean|e| − mean|e − w_(−m) · δ_pr|` over
   the held-out metros, in points.
4. Uncertainty: 2,000 bootstrap resamples of metros (the cluster), recomputing
   steps 2-3; the 5th percentile of `G`.
5. **Rule, fixed now:** a class's weight is the slope fitted on all eight metros
   if the 5th percentile of its `G` is above 0; otherwise 0. A class with fewer
   than 10 pairs takes 0 ("not measurable").
6. Secondary, reported and not deciding: the same procedure predicting each
   contest's delta from the party's other contests in the same metro, all 311
   contests nationally.

**What changes in code.**
- New `src/bye_value.py` (read-only CLI and importable function) computing the
  test and writing `data/processed/bye_value.json` with an `artefact_key`
  (the by-election file's sha, `deps_sha`, its own code sha): both classes'
  `w`, `G`, its interval, the pair counts and the rule's verdict. Added to
  `declares.py`, `tests/test_intermediates_are_current.py`, `ENTRY_POINTS` and
  CLAUDE.md §5's block.
- `montecarlo.blended_centres`: the blend weight `w = scenario["w_bye"]`
  becomes the class weight from `bye_value.json` for the party's size class
  (its previous-LGE list share; MK and others with none use the 2024 national
  share). `w_bye` stays in `DEFAULTS` as an override for sweeps only, default
  `None` meaning "derived"; a non-`None` value is recorded as an override.
  `BYE_MIN_WEIGHT` is unchanged and still gates admission.
- Missing or stale `bye_value.json` at a target that reads by-elections:
  `SystemExit` (same class as item 10's stale spec).
- `export_draws.py` ~621-639 reports the class weight beside `reaches_model`.
- JUDGEMENT-CALLS §A35 (`w_bye` 0.40) is superseded by a new entry for the
  derived weights, with the typed parts named (the two classes and their 1%
  edge, the leave-one-metro-out design, the 5th-percentile rule, the 10-pair
  floor).

**Guards.**

| # | guard | kind | constructed violation → caught; reverted → quiet | file |
|---|---|---|---|---|
| G23 | the test can see an increment | value | constructed pairs where `e = 0.5·δ` exactly → `w ≈ 0.5` and the class is admitted; `e` independent of `δ` → the 5th-percentile `G` ≤ 0 and `w = 0`; 9 pairs → `w = 0`, "not measurable" | `tests/test_bye_value.py` (new) |
| G24 | one weight reaches the model | value | `blended_centres` on a constructed party in each class uses that class's `w` from a constructed `bye_value.json`; deleting the file refuses; a stale key refuses | `tests/test_blended_centres.py` |
| G25 | no look-ahead | scan | the test opens no by-election dated on or after 2024-05-29 for the 2024 outcome and reads no file at or after 2024 for `B`; population = the pairs, asserted equal to the count the function reports | `tests/test_temporal.py` |
| G26 | `export_draws` and the model agree | value | for every row of the real CSV, `export_draws`' reported weight equals `blended_centres`' | `tests/test_export_draws.py` |

### R2.5 Pre-registration arms, revised

Runs as §6. Arms: **A** (pre-batch tree), **B0** (A + items 1-2), **B6** (A +
item 6), **B8** (A + item 8), **B** (items 1-6, 8-10, 12, 18), **C** (B + 11a),
**C16** (C + 16), **D** (C16 + 17), **E** (D + 19). B through E share draws
and seeds. P1-P10, P13 (= item 18) stand as written; P11's "11b" predictions
now belong to arm D (item 17), unchanged in content, and P14 is withdrawn.

**P16 (arm C16 against C).**
- The derived windows at each runnable target and at 2026 are reported first.
  Prediction: finite (below ∞) for θ at 2021 and 2026; "underdetermined" or ∞
  is possible at 2011, where few transitions precede it.
- Johannesburg 2026, if `h_θ` and `h_ρ` are below 2.3: the PA's spine level
  falls to 2.2-2.7% (computed above), its mean seats fall by 8-14 from arm C's
  value, its ward wins to under 3 on average, and the PA/Coloured tripwire
  pair fires in under 10% of draws. If either window is 2.3 or above, the PA
  moves by under 2 seats and the tripwire still fires above 25%: then item 16
  does not address the PA, and that is reported as the result.
- Other parties at 2026, within ±10% in spine level for every party at 1% or
  more except where the table above shows otherwise (ANC −6%, EFF −6 to −9%,
  IFP +12 to +18% at the windows shown). ANC and DA gain the PA's seats
  (+3 to +6 each), as item 7 measured for every level candidate.
- Panel: coherent seat error falls (the PA's 2021 overshoot is the largest
  single item 7 records); list MAE falls or holds at every city-year where an
  emergence-era party exists (PA 2021, EFF 2016 if its 2014 base differs by
  more than `h` from its 2016 size, ASA has no θ evidence and is unaffected).
  A panel coherent-seat-error rise of more than 4 seats falsifies "own records
  from other sizes mislead".

**P17 (arm D against C16).** As P11's 11b block (MK −1.5 to −4 seats; small
national-only parties up by under 0.3 seats each), plus: the seven item-8
parties' drawn list-share sd(log) moves from `level_sd_default`'s 0.45 to
`size_sd` at 0.01-0.2%, which is wider; together they still win 0 or 1 seat
in more than 80% of draws.

**P19 (the test, then arm E against D).**
- Test prediction, written before it is computed: the under-1% class has
  fewer than 40 pairs with any contest beyond one, the cross-ballot noise
  dominates, and its weight comes out 0. The 1%-and-over class: no prediction
  of sign; its 5th-percentile gain is within ±0.3 points of 0.
- If both weights are 0, at Johannesburg 2026: the All Citizens Party's centre
  returns to about its arrival seed (item 9 measured 0.050% list mean at
  `w_bye = 0`), mean seats from about 2 to under 0.2; Truth and Solidarity
  0.111% → about 0.06%; the PA loses the 0.78-point by-election tilt (item 7's
  step table) on top of arm D; the DA's +0.093 and MK's +0.106 weighted deltas
  no longer reach the centres. Item 7 measured `w_bye = 0` on the published
  model at PA 22.30 and DA 64.75 seats; the direction (PA down, DA down, ANC
  up) is predicted again here, the size is not, because arm D's centres differ.
- No backtest number moves: no backtest target reads the by-election file.

### R2.6 Writing order, revised

Steps 1-6 of §7 stand, with item 11 now: 11a, then item 16 (`size_window`,
the filter), then item 17 (`size_sd`, the drawer fallback). Step 7 becomes:
**item 19's test** (`bye_value.py`, read-only, its pre-registered section
committed first), then its model wiring (G23-G26). Steps 8-13 stand; step 9's
pre-registration is §6 as amended by R2.5, committed before arm A runs; step
10's window also runs `bye_value.py` after the re-emit; step 11 runs arms A,
B0, B6, B8, B, C, C16, D, E.

### R2.7 Targeted tests, added

`-k bye_value` (new). `-k temporal`, `-k spine`, `-k theta_prior` now also
cover items 16, 17 and 19.

### R2.8 Estimate, revised

Item 16: 4-6 h (the walk over targets, the multiset differencing, G19-G21).
Item 17: 1-2 h. Item 19: 5-7 h (the 2024 baseline, the bootstrap, the
artefact, G23-G26), replacing item 14's 4-5 h. Measurement: nine arms instead
of eight, 5-7 h wall. Total about 42-55 hours of work over 4-5 days.

---

## Revision 3 (2026-10-09, after the M1 blind diff review; coordinator-accepted)

Notes appended, not edits to the text above, which stands where these do not
name it.

### R3.1 P1, split into two populations

P1's "in draws without a tie the seat vector is identical between A and B0"
used "tie" for equal surplus AND equal votes. Item 2 alone also moves a draw
whose last seat falls between parties with an **equal whole-vote surplus and
unequal votes**: the float remainder `votes/quota − floor` can put the smaller
party first, where items 13(2)(b) and 16(4)(c) give the seat to the higher vote.
The review found published councils in that class. So on arm B0 against A:

- **Population 1**, draws in which some `allocate` call has an equal whole-vote
  surplus straddling the cut (equal votes or not): the council may move. Counted
  per arm, split into "unequal votes" (item 2, statute-required) and "equal
  votes" (item 1, the lot).
- **Population 2**, every other draw: the seat vector is identical, exactly.

Both counts are TO-MEASURE at the run. The instrument is P1's counter on
`seats.allocate`, keyed on the integer surplus. The brief's acceptance line
carries the same amendment.

### R3.2 Expected red during the batch: `test_export_draws`

`test_export_draws` compares the published seat files with a re-run under the
current seat law. Item 2 (R3.1, population 1) changes councils, so it is red by
design from M1 until the publishing run and the draws export at step 13. That
is not a regression, and nobody re-exports mid-batch: an export before the
window and the measurement would publish a model the batch has not measured.
The end-of-batch suite reads this module's failure against R3.1's population 1.
The same holds for anything that compares the committed `site/` or
`data/processed` artefacts with the current law (`test_served_draws` check 2 on
a tied ward; `test_score_forecasts`, `test_entries` and `test_rank_entries`
against a `forecast.json` without `x-seat-context.lot` until the site build).

### R3.3 G6 cannot see float ranking

G6 (`test_overhang`, Laingsburg) pins the published council, the re-quota
quota and the published round-two ranking, and catches a wrong re-quota
denominator. Laingsburg's surpluses are all distinct, so a reversion to float
ranking orders them identically and G6 stays green. **G5 (`test_seats`) is the
detector for float ranking.** G6's row in §3 is read with this note.

### R3.4 Deduct and level reuse round 0

`allocate_with_overhang`'s first `deduct` or `level` iteration allocates the
same council as round 0. It reuses round 0's allocation instead of re-drawing it
under round 1's key, so an exact tie cannot fall one way where the excess is
measured and the other way in the council returned. Round keys therefore count
real re-allocations only: round 1 is the first re-quota.
`tests/test_seats.py::test_the_first_deduct_round_reuses_round_zero_instead_of_redrawing_it`.

### R3.5 One key scheme, one writer

Keys are built only by `seats.ward_key`, `seats.draw_key` and `seats.seat_key`
from `seats.lot_identity`, which refuses a missing part. `x-seat-context.lot`
has one writer, `worker-api/tools/make_schema.mjs`, from the model artefact
(`build_make.model_artefact` → `build_make.run_lot`). The baselines' ward calls
(`benchmarks.council_from_shares`) route a tie through `prediction.top_party`
under the baseline's lot. Deploy order: `docs/DEPLOY-UAT.md`, "Releasing the
seeded lot".

### R3.5 (coordinator, 2026-10-09): one more test is red by design

`test_draw_record::test_the_published_seats_are_byte_equal_with_recording_on`
re-runs the published 2026 run under the current seat law and compares it byte
for byte with the published `seat_draws.csv`. It fails in the M1 check step.

**Cause** (argued from the M1 review's measurement that item 2 moves 5 of
5,000 published councils, and not counted draw by draw here): the same as
`test_export_draws`. The published file is stale under the corrected law until
the step-13 re-export. It is added to R3.2's expected-red list.

It must turn green after the re-export. If it does not, that is a finding.


### R3.6 (writer, slice M2 step 3, 2026-10-09): tests red by design until the re-emit

Step 3 changes `src/levels.py` (`unopposed_wards` and its helpers for item 3,
the renamed-column refusal for item 10). `levels.py` is in
`pools._EMIT_DEPENDENCIES` and in the citywide table's code key, so every
emitted spec's `deps_sha` and the table's `levels_sha` no longer match the
live code. Nothing is re-emitted mid-batch (§5, O6). These are red until the
step-10 window, and are expected to turn green after it; one that does not is
a finding:

- `test_chain::test_every_emitted_pool_spec_carries_a_current_artefact_key`:
  every `pools_*.json` reports `deps_sha` moved.
- `test_stage_inputs::test_a_real_run_produces_a_trace_that_passes_every_predicate`:
  the real run's `pools.stale` predicate fires on the same `deps_sha`.
- `test_citywide_table`: `test_the_table_on_disk_is_a_fresh_build_byte_for_byte`,
  `test_a_table_holding_the_target_election_is_refused`,
  `test_a_table_from_other_code_is_refused`,
  `test_a_missing_entry_stops_the_run_instead_of_falling_back`,
  `test_the_table_reproduces_every_drawn_array_of_a_native_run`: each refuses
  `data/processed/citywide_2026.json` on `levels_sha`. The table is rebuilt
  with the window (`src/citywide_table.py`; the page's copy re-ships with it),
  which §5's window list did not name and should.

`test_intermediates_are_current` stays green: it does not key on `levels.py`.

### R3.6, step 4 addendum (writer, 2026-10-09)

Step 4 changes `src/pools.py` code (item 9 rows 4-8), so every spec's
`pools_sha` now moves as well as its `deps_sha`. The same tests are red for
that second cause; no new test joins the list. Emitted specs still carry a
`seed_bands` field until the re-emit, which nothing reads.

`test_levers_are_live::test_no_function_argument_is_accepted_and_never_used`
is red on `build_make.npe_priors(wards)`, a parameter introduced by slice B2a
(8dffae8) and untouched by this batch. It is not a stale-spec failure and not
this batch's; it is reported to the coordinator, not fixed here.

### R3.6, step 5 addendum (writer, 2026-10-09)

Step 5's `levels.py` and `montecarlo.py` changes move `deps_sha` again; the
same three tests stay red for the same cause, and no new test joins the list.

### R3.6, fix-round addendum (writer, after the M2 review, 2026-10-09)

- **Generated documents.** `JUDGEMENT-SHEET.md` (`src/judgement_sheet.py`)
  joins the register, so `test_judgement_sheet` goes red whenever
  JUDGEMENT-CALLS.md changes; it was red from M1 until this round regenerated
  it (M2 review S5). It is regenerated with `MODEL-INDEX.md` before every
  quoted run and at step 12, and is red by design only between a register
  edit and that regeneration.
- **The window (step 10) also rebuilds three things**, each red until rebuilt
  (M2 review N7):
  - the citywide table, `src/citywide_table.py` (`levels_sha`), and the
    page's served copy, re-shipped from it;
  - `JUDGEMENT-SHEET.md`, after the batch's last register edit;
  - and, as already listed, the pool specs.

### R3.7 (writer, after the M2 review, 2026-10-09): item 8's width departs from §1.7 step 6's premise

§1.7 step 6 gives the item-8 parties `level_sd_default` because "they are
absent from `theta_prior`'s baseline", so `sd_for_party` would fall back. They
are absent from the baseline but present in its θ record, and `theta_prior`
emits an sd for every party in the record: for a party with no baseline,
`sd_for(0.0)`, the size line evaluated at the 1e-5 size floor. That is a width
at a size the party does not have, and for some it is `SD_CEILING` (joburg
2011's CHRISTIAN_DEMOCRATIC_PARTY tripped the estimation width-ceiling
tripwire). `make_drawer` therefore gives every item-8 party `level_sd_default`
explicitly, which is the value §1.7 step 6 intended, and records it in
`41_guards.level_sd_default_parties`. The width-ceiling tripwire exempts
exactly the parties in that record. Item 17 (R2.2) replaces the default for
them with `size_sd` at their local share.

### R3.6, slice M3 addendum (writer, 2026-10-09)

- **`test_drawer`'s two goldens** (`test_party_marginals_match_recorded`,
  `test_pool_marginals_match_recorded`) are red from item 11a (43f9ddb).
  Attributed by running the module in clean worktrees: green at 309481f, red
  at 43f9ddb and at a885b28. Cause: the fixture builds the drawer's inputs
  with `levels.theta_prior` and `levels.spine` on the real record, and item
  11a moves both estimators' centres (the size point); item 17 moves them
  again (no-record parties at the size centre). Item 16 does not reach this
  fixture: it calls both at their default window, ∞. These are goldens, not a
  standard: they are re-recorded once, deliberately and with the reason, after
  the window's re-emit (which moves the 2026 spec they read as well), not
  twice. The item-11a commit omitted this module from its targeted run; that
  is how it went unseen until item 17's run.
- **`test_levels_dispersion`'s Key 4 and PIT constants** went red from item
  11a too, and were re-recorded in the item-16 commit (a885b28) with the
  paired `key4_delta` measurement in the file. They read no spec, so the
  window does not move them again.
- **Item 12's record is not on disk until the window** (`group_share_record.py
  --emit` is a window step, §5). Until then:
  `test_intermediates_are_current::test_the_group_share_record_is_a_fresh_build`
  (G15) fails on the missing file, and
  `test_the_uncovered_set_is_exactly_the_declared_one_BOTH_WAYS` fails on the
  `group_share_record.json` pattern matching nothing. Both are expected to turn
  green after the emit; one that does not is a finding. Every run before the
  emit reports `41_guards.group_share_tripwire = "no record"`. A build into a
  temporary directory twice, in two processes, gave byte-identical files.
- **`test_levers_are_live::test_every_tunable_lever_actually_moves_the_forecast`**
  is red after item 17 (run once, after ee16123): `level_sd_default` does not
  move the forecast at 2021 or 2026 (perturbed to 1.6). Cause: item 17 (R2.2)
  gives every drawn party with a size the size-group width, so the default
  binds only where a drawn party has no size or the run has no θ fit, which
  no swept target has. This is what R2.2 intended. Not resolved by the writer:
  the harness accepts an inert excuse only with a model-free gate that proves
  the gate shut, and the last gate written for this lever
  (`level_sd_fallback_never_binds`) was deleted for being wrong. Options for
  the coordinator: an `EXPECTED_INERT` entry with such a gate, or deleting the
  lever (and keeping a refusal for the no-size case). The rest of the module:
  22 passed.
- **Consolidated expected red for the end-of-batch suite, as of slice M3:**
  R3.6 — `test_chain` (spec keys), `test_stage_inputs` (real-run stale
  predicate), `test_citywide_table` ×5, `test_intermediates_are_current` ×2
  (the group-share record), `test_drawer` ×2 (goldens, re-recorded once after
  the re-emit); R3.5 — `test_draw_record`; R3.2 — `test_export_draws` and the
  tests it names; and the `level_sd_default` lever above, pending a decision.
