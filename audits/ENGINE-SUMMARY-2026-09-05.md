# Where the forecast engine stands — 2026-09-05

Written for the owner, to be discussed. Every number re-derived; the stale ones
are labelled stale.

---

## 1. The architecture, and the owner's description of it

> *"The base model calculates from election to election as a baseline. All the
> others are levers to forecast the effect of those events on the model."*

**That is right, and it is the clearest one-line statement of this engine we
have.** Precisely:

**The baseline** takes the last local election in that city and asks *who voted
for whom, and where*. It splits every ward's voters into four census pools and
measures what share of each pool every party took. That composition is a
**measured fact about the previous election**. It then carries the pool **sizes**
forward to the target using the registration roll, and carries the party
**levels** forward using the preceding national election. Draw, allocate by
iterative proportional fitting, convert to seats under Schedule 1.

**Everything else is a lever for an event the baseline cannot see:**

| lever | the event it exists for |
|---|---|
| turnout bands | the electorate not showing up in the same proportions |
| arrival machinery | a party that did not exist last time |
| splinter machinery | a party that left a known party and took voters with it |
| poll channel | information newer than the last election |
| level shrink, θ spine | national swing not landing evenly in one city |

**And one thing that is not a lever at all**: the overhang rule is statute. It
is part of the definition of the outcome, like the council having a fixed size.

⚠️ **One refinement to the owner's description.** The baseline is not purely
election-to-election. The *level* comes from the preceding **national** election,
not the preceding local one, because national elections are more recent and more
frequent. So the base is "last local election for the shape, last national
election for the level" — and the join between those two is the θ spine, which
is one of the model's more fragile parts.

---

## 2. How accurate it is

**24 city-years — eight metros × 2011, 2016, 2021.** Councils of 90 to 270
seats.

| | coherent seat error, as a share of the council |
|---|---|
| median (p50) | **15.3%** |
| p75 | 20.2% |
| **p80** | **25.4%** |
| p90 | 29.5% |
| worst | **35.1%** — Mangaung 2011, 34 of 97 |

In seats: median 29, mean 29.5, best 8, largest absolute **88 of 270 at
Johannesburg 2021**.

⛔ **A MEDIAN IS NOT A BAND.** Half the panel is worse than 15.3% by
construction. **An 80% band on this record is ±25% of council — on
Johannesburg's 270 seats, ±68.** Quoting the median as "expected error" is the
most likely way this summary gets misused downstream.

**And the model against its baselines, on the same 24:** model **707**, uniform
swing **885**, last-LGE 1315, prior-LGE-noise 1274 — a **20.1% margin** over the
strongest naive reference. An error figure without its benchmark cannot be
checked.

⚠️ **Every seat figure in this project is scored AFTER a free label.**
`backtest.relabel_run` renames the model's generic `ENTRANT` column onto the
largest party that actually arrived — chosen with the outcome in hand, and given
to no baseline. Withholding it moves seat error 386 → 426. **The 2026 forecast
will not get that label.**

By cycle: **2011 total 329 · 2016 total 124 · 2021 total 254.**

⚠️ **Every figure above is from a scoreboard last taken at the FIRST commit of
this batch.** It predates the turnout band, the bounded estimator, the roster
seam, the widened arrival record and everything since. It is the honest current
number and it is not the number after the pending emit.

⚠️ **And the documented headline is staler still.** `ITERATING.md` says *"384
coherent seat error against uniform swing's 530"* — a **sixteen** city-year
figure, written before the panel became 24. Per city-year that was 24.0 seats
against today's 29.5. The panel got harder when 2011 was added, and the file
already carries an instruction that every number must be re-read when the panel
grows. It has not been.

**What that means in plain terms.** On a typical metro the model gets the
council roughly right to within a sixth of its seats. It is comfortably better
than assuming the last result repeats, and better than applying the national
swing uniformly — measured to be the strongest naive alternative. It is not
close to calling a coalition correctly on a knife-edge.

---

## 3. What is good

**The instrument is unusually honest.** Almost every number in the model is
derived from counted data rather than typed, and the ones that are typed are in
a register with their evidence and their status. That is rarer than it sounds.

**The pool method is the right shape for this problem.** Splitting the electorate
by census group and measuring each party's draw from each is exactly how you
capture that Johannesburg's ANC decline is a Black-African-pool phenomenon while
the DA's collapse is a Coloured- and Indian-pool one. A national-swing model
cannot see either.

**2016 is genuinely well forecast** — 124 seats of error across eight metros, a
cycle with no large arrival and no merger.

**The statute layer is right.** Ward and PR combined for the quota, the
excessive-seats provision as a rule rather than a lever, C and D terms handled.
This has been checked against the Act.

**The guard culture works.** In this batch alone the repository's own tests
caught: a duplicate ward-crosswalk reader, a test that never ran, a dead symbol
in the register, and three regressions the author introduced while fixing other
things. Several defects were found by the tests rather than by anyone looking.

---

## 4. What needs work, in order of how much it costs the forecast

**0. ⛔ THE LARGEST LIVE UNCERTAINTY IS A PARAMETER THE MODEL DOES NOT HAVE, AND
THE PANEL HAS TWO OBSERVATIONS OF IT THAT DISAGREE SIXFOLD.**

MK is not an arrival — it is a declared ANC splinter and takes its **level** from
the 2024 national election, where it won **12.22% in Johannesburg**. The question
that decides the Johannesburg headline is how much of a fresh national vote a new
party keeps when it fights its first *local* election. The panel has exactly two
prior cases, and they do not agree:

| | national | next local | kept |
|---|---|---|---|
| **COPE** 2009 → 2011 | 9.61% | 1.11% | **0.12** |
| **EFF** 2014 → 2016 | 10.13% | 10.93% | **1.08** |

Across all eight metros the retention is **0.12–0.28 in one cycle and 1.01–1.50
in the other** — tight within each cycle, six-fold apart between them. That is a
cycle-level regime with a missing covariate, the same shape as `k*` and the
arrival series.

**Applied to MK in Johannesburg: 1.47% on the COPE regime, 13.20% on the EFF
regime.** An 11.7-point swing in citywide share — roughly **31 seats of 270** —
and the difference between MK being irrelevant and MK deciding the coalition.

⚠️ **This cannot be fitted.** Two cycles support zero parameters. The honest
treatment is a level prior for MK wide enough to span both regimes, with COPE and
EFF named. **It forecloses the first criticism any expert will make**: *"you gave
MK its 2024 national number in a local election, and COPE lost 88% of its in
exactly that transition."*

**1. Level carry-forward is the biggest defect the BACKTEST can see — and the
2011 evidence is COPE, not the DA.** Composition is measured at election T−1; the level is applied at
election T; the model multiplies them. A party already taking 95% of a small pool
cannot absorb a 1.7× level jump without demanding more votes than the pool holds.
Every arithmetically-impossible cell is the DA at 2011 — the DA/ID merger cycle.
**But the DA is not what makes 2011 the worst cycle.** COPE is over-forecast at
**7 of 8 metros, by +4.1 to +11.3 points** — about 55 points of signed error
against the DA's 48 — and the fatal cells sit at only three metros contributing
106 of the 329.

⚠️ **So the named fix does not touch most of it.** Projecting composition onto
target-year pool capacity binds only where a fitted rate approaches 1; COPE at
9–15% of the citywide vote is nowhere near a pool ceiling. That repair fixes the
DA cells and would leave the COPE error essentially in place.

**The 2011 instance is national-splinter decay — the same object as item 0, live
at 2026.** The owner's instinct that mergers and splits need explicit treatment
is right; the mechanism is that composition is a T−1 object, the level a T
object, and the model multiplies them.

**2. Arrivals are systematically under-forecast, and the model knows it.** Every
estimator tested under-predicts arrival mass — but state the unit correctly:
that is **8 cells over TWO scored targets** (four estimators × 2016 and 2021),
not eight independent observations. The stronger instrument is the panel's own:
**mass PIT above 0.5 at 20 of 24 city-years, mean 0.679.** The
entrants-only series runs 0.84% → 2.04% → 3.61% across the three cycles and no
backward-looking statistic tracks a rise like that. **The 2026 arrival mass is
more likely low than high**, and that belongs in the published copy.

**3. There is no sentiment or momentum term, and the evidence says there should
be.** Measured this week: Johannesburg's ANC+EFF+ActionSA bloc has been flat at
88–91% of the Black African pool for 25 years while the ANC alone fell 90.7% →
53.5%. That is a transfer inside a pool, not noise. The ANC's decline has exactly
one inflection and it follows a leadership change. The DA lost two-thirds of the
Coloured pool in one cycle after Maimane and Mashaba left — the same event moving
four pools by four different amounts. **None of this is modelled.**

**4. ⛔ THE POLL CHANNEL IS ON IN THE PUBLISHED FORECAST, AT FULL BELIEF.** An
earlier draft of this summary said it was "switched off". That is false of the
artefact: `forecast_frozen.json` carries `poll_credence: 1.0` and
`poll_paths: "all"`. The −6-coherent-seat measurement was a backtest score for a
configuration the live run is not using, and MODEL-LOG §1.94 says explicitly
that it *"does not by itself mean switch the channel off at 2026"*.

**What it is anchored on**: after the screen excludes two party-commissioned
waves, **two SRF/Victory Research waves, n≈504 and n≈503** — roughly 500-person
metro subsamples, one house, behind a 53% likely-voter screen. House effects are
not estimable from a single house; the code says so itself. A likely-voter
screen is a model, not a measurement, and a metro subsample carries the parent
survey's design effect on top of its own small n. **If the published number is
materially moved by that poll, the page must say so.**

**5. The panel cannot support much more.** Eight metros sharing a national swing
within each cycle is about **2–3 effective clusters**. Three separate measurements
say the scoreboard supports roughly zero fitted parameters. **More history or the
2026 result is what licenses further tuning — not more ideas.**

---

## 4a. Decisions the owner has taken

| decision | date | reasoning |
|---|---|---|
| **Publish Johannesburg and Tshwane only this cycle** | 2026-09-06 | Cape Town, Mangaung, Buffalo City and Nelson Mandela Bay carry fitted rates on bounds at 15 of 24 city-years — including Cape Town 2011 fitting **162,262 registered Indian/Asian voters against a census population of 74,993 of all ages**. Johannesburg, Tshwane, Ekurhuleni and eThekwini are clean. |
| **BOSA stays unparented** | 2026-09-06 | It has a measured level (1.02% in Johannesburg, 2024), so a parent would change its **pool vector**, not its size. The DA took 66.3% of Johannesburg's White pool and 2.0% of its Black African pool; Maimane's proposition was to Black voters and he left in a dispute about that constituency. A DA-weighted vector describes BOSA worse than the city average does. |
| **MK keeps its 2024 level as its base** | 2026-09-06 | Not a prior spanning COPE and the EFF. COPE's 0.19 has a cause — an open leadership war — and the ANC held (0.99) and the DA gained (1.49) in the same cycle. ATM, a third first-local case, held at 1.14, and MK's own 8 Johannesburg by-elections since 2024 run at **0.87** of its national share. |

## 5. Open defects, named

* **Mangaung's Indian/Asian pool is degenerate** — 3,531 registered voters and a
  fitted turnout of exactly 0.0000. A live test failure, mislabelled as
  "expected" until this week.
* **BOSA is treated as arriving from nothing.** It is Maimane's party — a DA
  split by any reading — and declaring its parent would move the Johannesburg
  numbers.
* **`REGISTRATION_MAX = 2.0` binds on four cells in two cities**, two of which
  the register cites as proof it binds on nothing. The constant needs
  re-measuring or converting to a refusal.
* **A citation inverted in five places** — the register claims the census
  over-statement explains registration rates above 1; `DATA-QUALITY` item 11 says
  it *widens* the gap.
* **The live 2026 forecast has no arrivals at all.** Every vectorless party
  carries a 2024 national baseline, so the arrival machinery is inert until a
  nomination list is declared on 16 September.

---

## 6. What to expect on 4 November

**±25% of council on an 80% band — for Johannesburg, ±68 seats.** The median is
15.3% and half the panel is worse than the median.

⚠️ **An earlier draft said "±15% for a metro with no large arrival". Both halves
were wrong.** 15.3% is a median, not a band; and splitting the panel on realised
arrival mass, the large-arrival city-years have a **better** tail (p80 16.2%)
than the no-arrival ones (p80 26.9%) — because six of the seven large-arrival
cases are 2021, and the no-arrival set carries every 2011 small-metro disaster.
**The panel cannot separate "large arrival" from "cycle"**, so the conditional is
withdrawn.

⛔ **And the direction of the MK error is NOT the arrival-channel direction.** MK
is a declared splinter carrying a national level, so the arrival channel's
8-cell under-prediction does not apply to it. **The one comparable case on this
panel points the other way**: COPE was over-forecast at 7 of 8 metros in exactly
this transition. So the honest statement is that **MK's level is the single
largest source of error in the Johannesburg forecast and its sign is unknown**,
not that new parties will be under-stated.

**What this accuracy supports saying in public.** Ranges and scenarios. It does
**not** support a claim about who leads or which coalition forms: the model has
never been shown to call one, the panel contains no test of it, and the largest
input to the Johannesburg arithmetic has two prior observations six-fold apart.
Never publish a point without its band in the same sentence, and never publish
the median as "expected error".
