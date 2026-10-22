# Pre-registration — the rate bound is applied per level, not one bound for three

**Written 2026-09-05, BEFORE the change.** Found by the unbilled code review run
against `ultra-review-base`; finding 1 of 14, its only HIGH.

---

## The defect

Phase 1a (`9f9ac9e`) bounded `_nnls` to `[0, 1]` on the stated grounds that
*"a value above 1.0 is not a rate at all"*. `_nest` fits **three** levels with
that one solver:

| level | can it exceed 1? |
|---|---|
| `adult_share` — adults per person | **No.** Bound is correct. |
| `turnout` — voters per registered | **No.** Bound is correct. |
| **`registration` — registered per census adult** | **YES, and the model already says so.** |

Registered voters are **counted**; census voting-age population is **modelled**,
and `DATA-QUALITY.md` item 11 records the 2022 census as over-stating exactly
the white and Indian groups by 14% and 24%. `pool_counts` computes the ratio
itself and files it as `census_correction`, calling it *"a property of the
census, not of the model"* — **1.206 for Indian/Asian and 1.480 for White at
Johannesburg 2021.** Then the solver clips the same quantity to 1.0.

## The evidence for the new bound

Unbounded registration rate, every metro × 2011/2016/2021, measured 2026-09-05:

* Almost all pools sit **well below 1**.
* Persistently above 1, and consistent across cycles — **Johannesburg White
  1.38 / 1.71 / 1.74**, **Cape Town Indian/Asian 1.82 / 1.92 / 1.72**, Nelson
  Mandela Bay Indian/Asian 1.08 / 1.09, Mangaung White 1.26 / 1.36 / 1.31.
  These match the documented census over-statement in direction and rough size.
* **The only values above 2 are Mangaung Indian/Asian: 4.34 and 3.36** — the
  pool this repository already reports as degenerate (3,531 registered, fitted
  turnout of exactly 0.0000, and the standing failure of
  `test_the_three_known_things_hold_at_once`).

So **`REGISTRATION_MAX = 2.0`** admits every rate the census defect explains and
binds only on the pool already known to be broken. It is a **runaway guard, not
an estimate**, and it is registered as such.

## P1 — What the fix is

`_nest` takes an `upper`; `adult_share` and `turnout` keep **1.0**;
`registration` gets **`REGISTRATION_MAX = 2.0`**. No other behaviour changes.

*Falsified if any level other than `registration` changes bound.*

## P2 — The registered-roll split, at 2021

Predicted, measured before the change:

| city | pool | now | after |
|---|---|---|---|
| Johannesburg | **White** | 20.0% | **25.2%** |
| Johannesburg | Black African | 67.1% | 64.8% |
| Johannesburg | Indian/Asian | 6.4% | 4.5% |
| Johannesburg | Coloured | 6.5% | 5.5% |
| Cape Town | **Indian/Asian** | 4.3% | **8.5%** |
| Cape Town | White | 24.8% | 22.6% |
| Cape Town | Coloured | 37.3% | 35.4% |
| Mangaung | Indian/Asian | 1.0% | 2.0% |
| Buffalo City | Indian/Asian | 2.6% | 3.7% |

**12 pools move more than 0.5pp at 2021; the largest is +5.2pp.**
*Falsified if any figure differs by more than 0.3pp, or if a pool not listed
moves more than 0.5pp.*

## P3 — ⛔ THE PREDICTION THAT MATTERS: the DA/White infeasibility should shrink

`test_no_emitted_composition_weight_is_arithmetically_impossible` reports the DA
needing more White votes than that pool can cast — **3 fatal and 13 straining
across 24 city-years under the current code, and every fatal one is DA/White**.

**If that is an artefact of this bound rather than a fit defect, enlarging the
White pool by a fifth must reduce it.** Predicted: **fatal count falls below 3**,
and Johannesburg's and Cape Town's ratios fall.

⚠️ *This is the falsifiable half.* If the fatal count does **not** fall, the two
findings are unrelated, the DA/White corner is a genuine ecological-inference
limit, and that is the finding — it must be reported as such and not quietly
dropped.

## P4 — What must NOT change

`census_correction` is `max(implied, 1.0)` computed **after** the fit, so it will
move with `registered`. It must remain **≥ 1.0** everywhere. Turnout rates must
stay within `[0, 1]`. *Falsified by any turnout outside that range.*

## P5 — The clip must stop being silent

`_nnls`'s docstring already promises the caller *"must SAY SO rather than quietly
using the clipped value — see the `unidentified` list"*. That list is computed
and **read by nothing** (review finding 2), so the promise is false today.

It is emitted into the spec and printed by the run. And its message currently
blames the ward table — *"cannot identify this pool"* — for pools reaching
**71.1%** and **77.2%** of individual wards, which is abundant identifying
variation (finding 3). The message must distinguish *"unidentified"* from
*"the true rate exceeds the bound"*.

*Falsified if a bound-clipped pool emits no record of it.*

## Basis for adoption

This ships because the bound was **applied to a quantity the model separately
computes as greater than 1**, which is a defect on its face and not a matter of
taste. The panel cannot adjudicate it: pool sizes feed everything, and no key
isolates them. **P3 is the one empirical check available**, and it is stated
before the run with a named falsification.
