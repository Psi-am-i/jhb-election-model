# Pre-registration — widening the arrival record, and the budget it feeds

**Written 2026-09-03, BEFORE a line of the change.** Queue entries 4 and 11 and
the R-1 decision (§1.180 / JUDGEMENT-CALLS §L6), taken as one window.

⛔ **This supersedes the pre-registration in `POOLS-REEMIT-QUEUE.md`, which was
in an editable table cell — against this directory's own rule — and which was
wrong in the way that matters: it predicted a channel that is INERT in the
published forecast and said nothing about the one that moves it.**

---

## Why the old pre-registration was void

**The arrival machinery does not touch the live 2026 forecast at all.**
Verified against `data/processed/pools_2026.json`: `seeds` is empty,
`arrival_group` is `null`, and every one of the **21** parties with no measured
vector — `MK` 12.2184%, `RISE` 1.5569%, `BOSA` 1.0174%, and eighteen smaller —
carries a 2024 national baseline. `newcomers` filters on `baseline <= 0`, so it
is **empty**, `arrival_rules` seeds nothing, and `_arrival_total_prior` is never
spent. The budget's +0.8% is +0.8% of nothing.

So *"the budget moves +0.8% and the expected seat effect is ~zero"* was
guaranteed true, for the wrong reason, about a channel with no consumer.

**Meanwhile the same change moves the model's dominant width lever.**
`emit_pools` builds the per-pool split sample by calling `metro_citywide` over
every year in the transition set (`pools.py:4780`) — one of the four sites the
widening touches. `JUDGEMENT-CALLS.md` §B calls that concentration *"the model's
dominant width lever (83-98% of drawn variance for every party except ANC and
DA)."*

Reconstructed from the live spec, reproducing today's α **exactly** before
changing anything:

| pool | today (matches the spec) | widened | change |
|---|---|---|---|
| Black African | 15.61 | **12.73** | **−18.4%** |
| Coloured | 22.58 | **14.54** | **−35.6%** |
| Indian/Asian | 21.51 | **16.15** | **−24.9%** |
| White | 21.94 | 22.42 | +2.2% |

Metro-years in the sample: **24 → 33**.

⛔ **And therefore the old pass condition was inverted: if the panel came back
"~zero", that would be evidence the wiring never reached `dirichlet_alpha`.**

---

## P0 — Scope, named before the diff

Wired to `x or _npe_citywide_for(code, year)`:

1. `measure_pool_ratios` — `pools.py:2779` and `:2780`
2. `entrant_record` — `pools.py:3002`
3. `arrival_group_record` — `pools.py:3330`
4. the `emit_pools` split-sample loop — `pools.py:4780`

Already carrying the fallback, untouched: `splinter_record` `:3095-3096`,
`home_splinter_record` `:3148-3151`.

**Deliberately NOT widened**, with reasons:

* `metro_file` itself — it feeds `read_municipality`, which cannot parse the
  clean files (`KeyError`, verified), and widening it breaks `metro_citywide`,
  `metro_roster` and `_ward_reach` at once.
* `_ward_reach` — same reader. **Consequence, stated in advance:** the
  2000→2006 transition has no measured reach, so `entrant_record` would fall
  back to `reach.get(party, 1.0)` and record every pre-2006 arrival as having
  contested **100% of wards** — 9 rows of 319 at target 2026, 9 of 63 at 2016,
  landing in the `abs(r − 1.0) < 0.25` bucket that sizes seat-winning arrivals.
  **Those rows are SKIPPED, not defaulted.**
* `pools.py:3404` — a membership test, not a share.

*Falsified if the diff touches any site not on this list, or omits one on it.*

## P1 — The record

`arrival_group_record('2026')`: **22 → 29 rows**. The seven added are
**JHB 2000** and **2006 for JHB, TSH, EKU, ETH, CPT, NMA**. (MAN and BUF at 2006
have fewer than three arrivals and fall under the existing `len(arr) < 3` floor.)

*Falsified by any difference in count or membership.*

## P2 — The budget (queue entry 11 + R-1)

`_arrival_total_prior`, becoming the **pooled mean over entrants only**:

| target | today | predicted |
|---|---|---|
| 2011 | **None** | **1.8769%** (n=7) |
| 2016 | 1.3312% | **1.3977%** (n=13) |
| 2021 | 1.6155% | **1.6433%** (n=21) |
| 2026 | 2.1701% | **2.1867%** (n=29) |

*Falsified outside ±1e-6.* §L6's own out-of-sample table is measured on a record
that only exists **after** this lands, and is re-verified exactly once, after
the emit.

## P3 — The live forecast. **This is the prediction that matters.**

Johannesburg 2026 `alpha`: `[15.61, 22.58, 21.51, 21.94]` →
**`[12.73, 14.54, 16.15, 22.42]`**. *Falsified if any pool differs by > 0.05.*

Stated in advance: this **widens** the dominant width lever on three of four
pools. **Seat BANDS should widen; seat MEANS should move little. If the mean
seat vector moves by more than ~2 seats, α is interacting with something else
and that interaction is the finding.**

## P4 — The 2016 arm, and the tripwire it retires

`entrant_record(before='2016')`: **0 → 63 rows** (54 with measured reach, 9
skipped per P0). All eight 2016 specs go from **zero seeds to non-zero**.
Currently 2011 and 2016 are both entirely dead: 8 specs each, zero seeds, zero
`arrival_group`, zero `entrant_record`.

*Falsified if any 2016 spec still emits zero seeds.*

⛔ **`HANDOVER.md` calls 2016 "the strongest tripwire in the set" — "if any 2016
city-year moves by one seat, the lever is reaching something it must not, and
the run is void." THAT INSTRUMENT IS RETIRED BY THIS CHANGE.** Every conclusion
resting on "2016 came back byte-identical" is named and re-scoped in the same
commit, or it will later be cited as though it still held.

## P5 — The 2021 band

Full-reach arrival: `base` 0.3398% → **0.2818%**; band `[0.114, 1, 4.787]` →
**`[0.172, 1, 5.580]`**. *Falsified outside ±0.005 on the ratios.* The level
effect is absorbed by the group rescale; the **band is not rescaled**, so the
width change survives.

## P6 — What decides it, chosen now

* **KEY 1 will return `undetermined`, structurally** — 2016 goes from a null arm
  to a live one, so cross-cycle replication cannot mean anything here.
  Committed in advance so it cannot be discovered afterwards.
* **KEY 2 (CRPS on `reference`) is the binding condition, and untradeable.**
* **KEY 4 cannot fire** — neither path touches `sd_for` or `theta_prior`. Both
  halves stated, per the standing rule.
* **No seat or CRPS figure from `compare_history` arbitrates the arrival
  channel.** `backtest.arrival_group_score` is reported label-free **beside**
  the relabelled score, never instead of it.

## P7 — Direction

Every quantity above is scored in **|error|**, with the direction that counts as
better named. No signed quantity without a named direction.

## P8 — The honest basis for adoption, stated before the run

This ships on **"more honest usually ships"** plus §L6's out-of-sample table —
**not** on a panel score. Whether the widened α is *better* cannot be settled
with the data held: Key 2 is the only key that can see a width change, it is
untradeable in one direction only, and with ~2 effective clusters the panel
cannot resolve a moderate width effect. **A panel score may not be recruited
afterwards as though it had been the test.**

---

## Known asymmetries, declared

* **`levels.HELD_BACK` quarantines `lge2000`/`npe1999` for seven metros but not
  Johannesburg.** So the widened record gives the published city a fifth cycle
  no other metro contributes, drawn from the cycle whose `k*` is the 0.62
  outlier. The 2000 row is **n=1, is Johannesburg, is selected by file
  provenance rather than any criterion, and rests on the approximate pre-metro
  footprint** — in which VF Plus is a phantom arrival (§1.181).
* **The quarantine is temporary.** Lifting it moves this quantity a **fourth**
  time. Recorded so that is a known future event, not a discovery.
* **`arrival_group_spec` keeps the all-arrivals population** — only
  `_arrival_total_prior` is repaired here. Half a fix on a pair whose docstring
  says it must not be half-fixed. Tolerable only because `arrival_group_draw`
  defaults off and was refuted (CRPS 85.9 → 109.9); it must not be left looking
  fixed.
