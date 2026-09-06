# What we are doing, and what the published forecast is not

This repository is **iterating a model**. That sentence sets the terms for every
comparison made here, and it is written down because it is easy to lose.

## The published forecast is not a benchmark

`joburg.whysoserious.city` carries a forecast. It is **a recent output of an
earlier version of this model**, published because it was the best we had at the
time. It is not a target, not a baseline, and not a thing to be defended.

Specifically, it is **not evidence about anything**:

* Being close to the published forecast is not a virtue. The published forecast
  has never been scored against the election it forecasts, because that election
  has not happened.
* Being far from the published forecast is not a fault. If the model has
  improved, the numbers *should* move, and a change that moves nothing has
  probably not fixed anything.
* `data/processed/validation_<year>.json` is a useful record of what an earlier
  version scored on a past election, and it is legitimate to compare against —
  but as a **previous iteration**, on identical terms, and only where the
  comparison is like-for-like. It stores twelve parties where the targets have
  fifteen to twenty-four seat-winners, so a seat error read off it is truncated
  and is not comparable to one summed over the whole ballot.

## The only question

> Does the current model predict past elections better than the previous version
> and better than the naive baselines, on the whole ballot, out of sample?

⛔ **AND NOTHING THIS MODEL HAS PRODUCED IS AN ANSWER TO IT.** Not the published
forecast, not `data/processed/forecast_frozen.json`, not a golden, not a prior
run. The standard is **real election results**, and agreement with an earlier
output is evidence of nothing because that output was never known to be right.
"Reproduce the old numbers or revert" enshrines the current bugs as correct.
Stated in full in `CLAUDE.md` — *"Nothing this model has ever produced is a
standard of correctness"* — and not restated here, because a rule written twice
is a rule that drifts.

If yes, it is a candidate for publication. If no, it does not ship and we keep
iterating. There is no third outcome in which a worse model is published because
it is newer, better argued, or built from more measurements.

### ⛔ AMENDED 2026-09-01 BY THE OWNER — THE RULE IS NOW "MORE HONEST USUALLY SHIPS"

> *"Please remove 'worse does not ship' — you make it mean something new each
> time. **More honest usually ships.**"* — owner, 2026-09-01

**"Worse does not ship" is retired as a rule.** It was invoked in this project
for a scorer change, a data ingest and a pool fix inside one week, meaning
something different each time — which is what a rule that has stopped carrying
its own reasoning looks like. A phrase that can justify any of three opposite
decisions is not a standard.

**The standard is: a change that makes the model MORE HONEST usually ships, even
when a headline score worsens.** More honest means: a real measurement replacing
a typed constant; real data replacing an assumed absence; a rigged comparison
made fair; an instrument that can no longer flatter itself.

**What still does not ship is a change that scores worse AND explains nothing** —
because that is the case where a worse score almost always means something
nonsensical or inert has been modelled, which is the reasoning the old rule was
carrying and the only part worth keeping.

**And "more honest" is a claim that must be argued, not asserted.** Say what the
change makes true that was false before. If the only argument is that the number
went the way you wanted, it is not an honesty argument.

### The 2026-08-27 amendment this supersedes — a more honest model beats a rigged one

**The owner's amendment, and the reasoning is the part that matters:**

> *the rule is "worse doesn't ship" because worse almost always means you've
> modelled something that's nonsense or ineffective. However, there are many
> exceptions especially when we are replacing smuggled constants or values
> inserted because they seem to work without any mechanism or explanation for
> it. In those cases, a more honest model is better than a rigged one.*

**Why the rule exists is now written down, and it is not "the score is the
truth".** It is that a change which scores worse has *almost always* modelled
something nonsensical or inert, and the score is the cheapest available detector
of that. The score is an INSTRUMENT, not the objective. Where the instrument and
the objective come apart, the objective wins — and the objective is a model whose
every number has a mechanism behind it.

So the bar governs **candidate improvements** — a new mechanism, a refitted
constant, a lever someone wants to turn. Is this better? If not, it does not
ship.

It does **not** govern **replacing something unjustifiable with something
justified**, of which there are two kinds:

1. **An impossibility.** Something the model's own invariants forbid or that
   cannot be true of the world — a rate above 100%, a negative count, votes
   exceeding voters. §1.100: 560,217 registered voters among 300,374 adults is
   not "a configuration that scores well"; it is wrong, and a score cannot make
   it right.
2. **A smuggled constant** — a value that reached the model because it seemed to
   work, carrying no mechanism, no derivation and no interval. Its score is not
   evidence *for* it, because a number fitted to the panel will of course score
   on the panel. **That is what "rigged" means here, and a rigged number scoring
   well is the symptom, not the defence.** Replacing one with a derived quantity
   may cost accuracy and still be right, because what is being bought is the
   ability to know why the model says what it says.

**A caution that belongs with this, because the exception is powerful enough to
be dangerous.** "This constant is smuggled" is very easy to say about any number
one dislikes. The register in `JUDGEMENT-CALLS.md` is what settles it — a
constant marked 🔴 there, with no measurement behind it, is smuggled; one with a
measurement and an interval is not, however inconvenient. If the status is
arguable, it is a candidate improvement and faces the full bar.

**The exception is not a loophole, and these conditions are all required:**

1. **It must be an impossibility or a smuggled constant, on the register's
   evidence — not on anyone's opinion.** "I think this value is badly chosen" is
   a candidate improvement and faces the full bar.
2. **The cost is MEASURED, in full, and published in `MODEL-LOG`.** No repair
   ships on the argument alone. §1.100 records +8 seats, +3.09 CRPS and a failed
   Key 1 for exactly this reason.
3. **Key 2 and Key 4 still bind.** Calibration and held-out NLL are untradeable
   for repairs as for anything else. A repair that breaks calibration does not
   ship; it goes back for a better repair.
4. **The cost is recorded as a DEBT, with a hypothesis.** A repair that costs
   accuracy is evidence that the defect was doing load-bearing work, and the
   entry must say what work is suspected and how to test it. §1.100's hypothesis
   is that the inflated white pool was standing in for a differential-turnout
   effect the model under-weights.
5. **The debt is revisited.** If the load-bearing work is later supplied and the
   deficit does not close, the hypothesis was wrong and the entry must be
   rewritten to say so — a loss taken for correctness is a different claim from a
   loss expected to be recovered.

**What this exception does NOT license.** It is not a route for a change that
merely scores worse and has a good story. It is not a reason to stop measuring.
It is not precedent for trading Key 2 or Key 4. And it is not available to
anything that could instead be expressed as a lever and swept — if the choice has
a range, it is a candidate improvement and faces the bar.

**NEVER INVOKED.** It was opened for §1.100 and §1.102 then reverted that
change outright, so nothing has shipped under it. It is kept — at the owner's
direction — because the reasoning is right and will be needed: the argument that
a score is an INSTRUMENT for detecting nonsense rather than the objective itself,
and that a derived number beats a rigged one, does not depend on the case that
prompted it. The first genuine use should record itself here.

### AMENDED 2026-08-23 BY THE OWNER — accuracy is necessary, and it is not sufficient

The owner's amendment, in his words: *a model should ideally be better at
forecasting but it should also be derived as far as possible*, and the bar
needs to be **more nuanced** than a single seat total.

He is right, and the reason is measurable rather than philosophical. **The
instrument this section used was underpowered and pointed at the wrong
quantity.** A cluster bootstrap of the sixteen-city-year coherent seat total
gives **384 with a 95% interval of [258, 554]** — ±148. Every verdict this file
has recorded on a 4-to-26 seat difference was read off a number whose own
sampling uncertainty is thirty times larger. The comparisons are **paired** —
same city-years, same seeds, same baselines — and the pairing was being thrown
away. §1.82.

Worse, §1.81's Condition 2 required a candidate's nine-city-year total to fall
below **254**, a number produced by a model that had *less data*. That demands
that adding true information never hurt a misspecified model, which is false in
general and is the very symptom under investigation.

So the bar has four keys. **A change must pass Keys 1, 2 and 4. Key 3 may buy a
bounded amount of Key 1, and may never buy Key 2 or Key 4.**

**KEY 1 — the paired, cycle-replicated comparison.** For each of the sixteen
city-years take the paired difference against the incumbent on identical seeds.
Report the sign count and the sum **split by cycle** (2016: 8 metros; 2021: 8).
The pass condition is *replication*, not a p-value:

> the sign of the effect is the same in **both** cycles, **no cycle shows a net
> loss**, and at least one cycle has ≥5 of 8 city-years strictly better.

**Do not quote a p-value from the eight metros inside a cycle.** They share one
national swing, so the binomial and the metro bootstrap are both
anti-conservative — a metro-resampled interval of [−28, −4] on a 16-seat effect
is narrower than the truth. Between-cycle replication is honest because the two
cycles are genuinely different elections. This is rule 11's language, applied to
seats for the first time.

This instrument can resolve a consistent moderate effect and cannot resolve a
small one; on ~2 effective clusters that is a fact about the panel, not a defect
of the test. **Anything below "most metros, both cycles, same direction" is
`undetermined`, not `adopted`.**

**⛔ KEY 1 CANNOT CURRENTLY ARBITRATE THE ARRIVAL CHANNEL, AND EVERY SEAT FIGURE
IN THIS FILE IS SCORED AFTER THE RELABEL.** `compare_history.py:1221` runs
`backtest.relabel_run` on every run before scoring, renaming the model's generic
`ENTRANT` column onto `max(newcomers, key=seats)` — the largest realised arrival,
chosen with the outcome in hand (`backtest.py:596`). **The baselines have no
such column**: `benchmarks.py` never builds an `ENTRANT`, so there is nothing to
relabel and no equivalent benefit. The model is handed a free correct label on
the single hardest column in the panel and uniform swing is not.

This is the same class of fault as `claimed` selecting away from the
forecaster's own failures, which rule 8 identified and fixed by introducing
`reference`; it was never fixed here. **MEASURED 2026-08-31, and it is no longer
unquantified: the free label is worth 11.52 CRPS — 3.5% of the model's 329.50 —
and 2.17 points of the margin over uniform swing, which falls from 37.8% to
35.7%.** Seat error (coherent) goes 386 → 426. Reproduce with
`JHB_SCORE_NO_RELABEL=1 .venv/bin/python src/compare_history.py`, which withholds
the label from the model everywhere it is used, not only at `relabel_run`. The
ablation moves **exactly the ten city-years where a label exists** and is
bit-identical at the six where `entrant_actual` is `None` — an internal check
that it is measuring the label and nothing else.

The effect touches the arrival columns only, so it does not void comparisons
that leave those columns alone — but it does mean **no seat or CRPS comparison
in this file arbitrates a change to the arrival channel.** The label-free referee
`backtest.arrival_group_score` is the fix, and it must be reported beside the
relabelled score as a sensitivity pair, never instead of it. **DONE 2026-08-31:**
`compare_history`'s report now carries a section "The arrival channel, scored
without the label" on every run — it had been computed into `history.json` and
rendered nowhere since it was repaired. Panel mass PIT **0.692**, seats PIT
**0.602**, above 0.5 at **13 of 16** city-years. §1.133, §1.136, §1.148.

**AMENDED 2026-08-31 — the relabel does not always fire, and where it does not,
something worse happens.** `entrant_actual` is `None` at **6 of the 16
city-years** — joburg 2021, tshwane 2016 and 2021, mangaung 2021, buffalocity
2016 and 2021 — because no newcomer took a seat for it to be named after. The
block above reads as though the relabel is universal; at those six the model's
generic `ENTRANT` **survives into scoring as its own party column**, carrying
2.71 CRPS across the panel (0.86 at joburg 2021, the model's single largest
extra column). So the fault has two faces, not one: at ten city-years the model
gets a free correct label, and at six it is scored on a column no baseline has
and no real party corresponds to. **Joburg 2021 — the flagship city-year — is one
of the six.** MODEL-LOG §1.144 §4.

### Which scores may be compared across forecasters, and which may not

**AMENDED 2026-08-31, measured, and it corrects §1.141.** The scored column set
depends on the forecaster (`score.seat_matrix`: a column is kept if the party
won a seat **or this forecaster gave it one in any draw**), so forecasters are
routinely scored over different *d* — 430 columns for the model against 232 for
uniform swing over the panel. That does **not** invalidate every score, and the
distinction is exact rather than a matter of degree:

| statistic | shape | comparable across forecasters? |
|---|---|---|
| `crps["total"]` | **sum** over columns | **YES** — an unscored column is identically zero in every draw against a truth of zero, so its CRPS is exactly 0 |
| `energy` | `E‖X−y‖ − ½E‖X−X′‖` | **YES** — a zero coordinate adds nothing to a Euclidean norm |
| `crps["mean"]` | sum ÷ `n_scored` | **NO** — flatters the forecaster with more columns; moves the model's margin 37.8% → 66.5% |
| `variogram` | **mean over pairs** | **NO** — padding adds zero-valued pairs and grows the denominator, so the score *shrinks*: uniform swing 4.0384 → 1.8916 when padded 19 → 56 (**joburg 2021 only**, not a panel figure) |
| `n_scored`, `coverage_all` | counts over the set | **NO** |

**The CRPS row is verified on the panel, not argued: max |own_total −
union_total| = 0.0 across all 64 forecaster × city-year combinations.** The
energy and variogram rows are a mathematical argument from their form, checked
at ONE city-year (joburg 2021) — the invariance of a norm to a zero coordinate is
exact, so a single check is a spot-check rather than a sample, but say which it
is. `energy` additionally sub-samples above `max_draws=4000` with a fixed seed,
so at production draw counts it is a **stochastic** statistic and small
differences in it are not meaningful. The correct common support is the
**union**, and because the sum is invariant, the union is what already ships —
no change is required to Key 1. The **intersection** is wrong and biases toward
the baselines, deleting 44.00 CRPS of earned penalty from uniform swing against
9.04 from the model.

**So: quote `crps["total"]` and `energy` across forecasters. Never quote
`crps["mean"]` or `variogram` across forecasters without holding the universe.**

**KEY 2 — calibration is a floor, not a currency.** CRPS must not worsen beyond
its noise, and the level-free width statistics on the `reference` population
must not worsen. **Key 2 is not tradeable.** A worse-calibrated model actively
misleads a reader, and honest intervals are this project's whole public claim.
Accuracy can be bought with a good story; calibration cannot.

**KEY 4 — the ESTIMATION RECORD is a floor too, and it is not tradeable.**

> **THE QUANTITY.** For each fold *f* ∈ {2016, 2021}:
>
> **Population.** Every (party, metro) pair for which the model forms a θ prior
> at *f*: the party appears with share > 0 in both the preceding NPE and the
> LGE *f* citywide tallies for that metro, and in `theta_prior`'s `priors` with
> a mode strictly above zero.
> Metros: the eight of `levels.METRO_CODES`. Environment: `THETA_WINDOW=0`,
> `THETA_EXCLUDE_TARGETS` empty, `FILTER_TYPE_A` and
> `EXCLUDE_DEMARCATION_CROSSING` unset. **At 2026-08-28 this is n=97 at 2016 and
> n=138 at 2021, eight metro-year clusters each.**
>
> **The forecast scored.** One `levels.theta_prior(f, baseline)` call per metro,
> with **the baseline `run_model` passes** — the metro's preceding-NPE citywide
> shares with off-ballot parties already dropped by `levels.absent_from_ballot`.
> Centre `m = priors[party][1]`; width `w = groups["sd"][party] =
> sd_for(baseline[party])`, clamp and all. **Neither is rebuilt.**
>
> **The score.** The negative log density of the realised `log θ` under the
> predictive `montecarlo.log_shock` actually draws — `log m + s·t_df`,
> `s = w·√((df−2)/df)`, `df = LEVEL_DF` — with the constants carried:
>
>     z = (log θ − log m)/s
>     NLL = log s + ((df+1)/2)·log(1 + z²/df) + C(df)
>     C(df) = ½·log(dfπ) + logΓ(df/2) − logΓ((df+1)/2)
>
> Reported as the mean over the fold's population, and as the mean of the eight
> per-metro-year means. **Baseline: 2016 = 1.1363, 2021 = 1.1425.**
>
> **The comparison.** Paired on observation identity `(party, metro, fold)`,
> over the SAME population; each arm scored under its own centre AND width,
> because a change moves both. **If a candidate changes the population the
> comparison is VOID** until it is re-scored on the intersection with both
> counts reported.
>
> **The floor.** Key 4 **FAILS** if, in either fold, EITHER trigger fires:
>
> * the **one-sided 95% lower bound** on the paired per-cluster delta lies above
>   zero — `t(0.95, G−1)`, which is 1.895 at G=8. **α = 0.05, one-sided,
>   declared here** rather than left implicit: the first version tested
>   `lo > 0` on a *two-sided* 95% interval, i.e. α = 0.025, which is
>   conservative in the one direction a floor cannot afford;
> * or **≥7 of the 8 metro-year clusters worsen** — one-sided exact binomial,
>   P(X≥7 | p=½) = 9/256 = 0.035. The t interval is driven by the BETWEEN-cluster
>   variance and can miss a small but utterly consistent worsening; the sign
>   count cannot, and it is free.
>
> A point-estimate worsening that fires neither is `undetermined` and **does not
> block**, because this is a floor and not a gate. A cluster mean below 1e-9 is
> float dust and counts as no direction at all (§1.126).
>
> **Folds 2006 and 2011 are computed, reported, and NOT part of the floor.** See
> the fold note below.

`src/theta_residual.py` — `held_out_nll()["<fold>"]["COMMITTED"]["mean"]`, and
`key4_delta()` for the comparison — is **one implementation of that quantity.**
It is not the definition.

> ⛔ **THIS KEY WAS OPERATIONALISED AGAINST THE WRONG THING IN THREE SEPARATE
> WAYS UNTIL 2026-08-28, and the block above is the fix.** It used to read
> *"held-out NLL on `theta_residual`'s folds"*, and the table it pointed at
> labelled its first column "A = committed".
>
> 1. **`form_a` is not the committed estimator.** Its fit regresses on the
>    record's own reliability-weighted size where `sd_for` regresses on the
>    party's size at the target, and it is fitted once per fold where `sd_for`
>    is refitted per metro-year. **The mechanism is dispositive and needs no
>    number:** A/B/C are rebuilt from `_fit_line` and reach `levels` only through
>    the clamp, so a change to `sd_for` moves the model and leaves the gate
>    where it was. `DUPLICATION-AUDIT.md` had named the same seam from the other
>    side.
> 2. **The harness passed a baseline the model does not pass** — the raw
>    citywide tally, not the one with off-ballot parties dropped. 286 parties
>    across 32 metro-years; the largest single width moved 0.605.
> 3. **The score was a Gaussian and the model draws a Student-t₇.** At
>    `w = SD_FLOOR` and `|r| = 2` the Gaussian charges 87.9 nats where the t₇
>    charges 13.3 — and every candidate this key has been used on works by
>    removing or reweighting far-tail observations.
>
> **Every held-out NLL figure quoted anywhere in this repository before that
> date is form A's, Gaussian, without its ½log2π, on the raw baseline.** They
> are marked in place where they appear. Re-measuring the Type A filter, state C
> and the four `THETA_WINDOW` arms on the corrected instrument is the first item
> of MODEL-LOG §1.124's open list, and it must happen before F22+F23.
>
> **A promotion key names a quantity and its estimator, not a script's output.**
> Key 1 would survive a rewrite of `compare_history.py`. Key 4 did not survive
> the rewrite of `theta_residual.py` that already happened — which is the whole
> argument for the block above.

**⛔ WHAT KEY 4 IS FOR — restated by the owner on 2026-08-29, replacing the
justification it was created with.**

> Key 4 is **a floor on the θ width estimator**, and that is the whole of it. It
> asserts that a change may not make the model's estimate of `sd(log θ)` worse
> out of sample on the record where that record is thickest — 235 observations
> across 16 metro-year clusters, against Keys 1 and 2's ~2 effective clusters.
> It is untradeable because a layer that has stopped estimating its own
> dispersion honestly cannot be repaired by a better score somewhere else.
>
> **It is NOT a guard against an exclusion moving volatility out of the prior
> and into the error.** It was believed to be, for the reason set out below, and
> §1.125 measured that it is not — Type A passes it at every `LEVEL_DF` from 3
> to 1000, on either baseline, under either scoring family. **Nothing in this
> bar now performs that job.**

**⛔ THE VACANCY — added 2026-08-29, and it is to be read as a KNOWN HOLE IN THE
BAR, not as a formality.**

> **The bar has no instrument that can block a change which improves the many by
> degrading the few.** The evidence that this is a live failure mode and not a
> hypothetical: under the Type A filter the θ prior's PIT variance falls and its
> coverage rises at both folds — the body of the distribution improves — while
> `mean z²` at 2016 worsens **6.230 → 7.400**, and the trimmed figure (dropping
> three rows) *improves* to 3.642. **Ninety-odd ordinary parties are forecast
> better by forecasting three party-structural collapses worse**, and every
> aggregate score in this bar reads that as an improvement, because it is one on
> average.
>
> Whether that trade is a defect or the correct behaviour is **itself unsettled**
> — §1.71 and §1.73 argue a collapse is not retention and belongs to
> `pools.SPLITS` and the arrival machinery rather than to θ. **Until an
> instrument exists that can put a number on it, no exclusion or record
> restriction may be adopted on the strength of an aggregate score alone**, and
> any candidate of that shape must carry an explicit statement of what it makes
> worse and where.
>
**WHAT NOW OCCUPIES THE VACANCY — 2026-08-29, MODEL-LOG §1.128.** The search for
a replacement found that the obvious one is empty by construction, and that the
honest occupant is a **precondition**, not a fifth key.

> **(a) ROUTE, DO NOT DROP — a Key 3 / rule 10 condition, and it is checkable
> rather than statistical.** *An exclusion or record restriction may not ship
> unless the volatility it removes is carried somewhere the model still draws
> from, and its register must say where, PER ROW.*
>
> On the Type A register this currently fails **four of six rows**: `SPLITS`
> routes the IFP's NFP split and the DA's ActionSA split, and routes nothing for
> the ID **merger** (there is no merger machinery in `src/` at all), for COPE's
> or Agang's **post-formation collapse** (`SPLITS["COPE"]` models COPE's birth,
> not its death), or for Minority Front's **leader death**. `arrivals.py` models
> entry and has no exit path. **Unrouted rows that a given fold can actually
> move: two of three at 2016, four of five at 2021, four of six at 2026** — the
> filter keys transitions strictly before the target, so fold 2016 loses only the
> three 2011 rows and one of those (IFP) is routed.
>
> **(b) THE WIDTH CHANNEL, POOLED — REPORTED FOR EVERY RECORD-TOUCHING
> CANDIDATE, AND NOT A GATE.** ⛔ It was adopted as a floor on 2026-08-29 and
> that was one review too early: **its 2016 verdict flips with `LEVEL_DF`** —
> Type A FAILS it at df 3 and 4 (one-sided bounds +0.0159 and +0.0082, 7/8
> clusters worse) and does not block at df ≥ 7, where the margin is p = 0.0526.
> `LEVEL_DF` is 🟡, typed, never measured, and **was 4.0 until this branch**. It
> becomes a gate when that constant is measured or when the pass rule declares
> its df. It is nonetheless **the best-powered instrument in this bar** — MDE
> 0.094 / 0.046 nats against Key 4's 0.230 / 0.130, because holding the residual
> fixed strips the centre-movement noise — and it still cannot separate this
> candidate from noise. Note `Δ_total ≠ Δ_width + Δ_centre`: NLL is jointly
> non-linear, the split is path-dependent, and what is reported is the
> incumbent-first path. §1.129. A residual is `log θ − log(centre)`, so an arm carrying the
> incumbent's residual with the candidate's width isolates the width alone:
> `theta_residual.py --dump-arm` twice, then `--compare`. It is the vacated
> quantity — *did this narrow the prior relative to what it must forecast?* — on
> the full n=97/138, eight real metro-year clusters, and a population the
> candidate cannot choose. **Report it for every candidate that touches the
> record.** Type A reads +0.0921 at 2016 (one-sided bound −0.0017) and +0.0209 at
> 2021 (−0.0249): worse at both folds, blocking at neither.
>
> **(c) THE PER-BIN SPLIT IS REPORTED AND NOT GATED.** Three mid-ballot bins fail
> uncorrected in the same direction at both folds — and **not one survives Holm
> across the nine bins** (smallest p 0.0079 against a critical 0.0056). "7/7
> clusters worse" at 2021 1–5% is **not a second witness**: the exact sign test
> gives 0.0078 against the t's 0.0079, two readings of one statistic. It buys
> robustness, not corroboration. The instrument is the right shape and the panel
> is too small. **Never quote the uncorrected table without the Holm column** —
> `--compare` now prints both.
>
> **(d) AND THE GAP IS STILL REAL.** On every instrument this repository has, the
> Type A filter does **not** harm calibration. **No instrument this repository
> has** restores the old block — the tail-weighted family built for exactly this
> shape has not been tried (§1.129) — and manufacturing an instrument to reach a
> verdict already held is the failure §1.124 exists to name. Decline such a change on (a) — typed, unfalsifiable, and
> four of six rows routing the volatility nowhere — or adopt it. Do not invent an
> instrument to do it for you.

MODEL-LOG §1.125, §1.126, §1.127, §1.128.

**KEY 4 IS A LAYER FLOOR, NOT THE MODEL'S PREDICTIVE SCORE.** It scores the θ
**width** estimator about `theta_prior`'s **own** centre. The model does not draw
about that centre: `make_drawer` is handed `centres[party]` from
`blended_centres`, which for any party the spine reaches is the spine's level,
then tilted by by-elections and polls. That is deliberate — Key 4's value is that
it scores **the θ layer** on the structural-event parties where Keys 1 and 2 are
blind — but it must never be quoted as the model's estimation loss.

**THE FOLD NOTE.** 2006 and 2011 are computable and are not gated, for two
structural reasons and one that the band above has largely spent.

1. **2011 is a CONSTANT under every change this key is used on.** `theta_record`
   filters the fitting record; `residuals` never filters the held-out set; the
   2011 fit uses only pre-2011 transitions. §1.78 and §1.80 both show
   `5.5915 → 5.5915`. **Gating on a fold that cannot move is not a gate**, and
   no band touches that.
2. **2006's fit rests on a single transition**, `npe1999_approx → lge2000`,
   whose national file the calendar itself calls *"the approximate pre-metro
   footprint"*. A data-quality reason, also unaffected by the band.
3. Multiplicity, which **used to be the dominant term and no longer is.** This
   note said an unbanded "must not worsen in any fold" rejects a neutral change
   ~75% of the time on two folds and ~94% on four — **true of the bare
   inequality this same commit replaced, and stale on arrival.** With the band
   at one-sided α = 0.05 the figures are ~9.8% and ~18.5% (upper bounds; the
   folds are positively correlated, 2016's record being nested in 2021's).
   Adding folds is now cheap, and if it is done, **control family-wise error
   across them (Holm) rather than testing each at α**, or the problem the band
   solved comes straight back. §1.126.
**Call 2011 the structural-events fold — and read a movement in it as a positive
signal IF AND ONLY IF the volatility is routed** (the precondition above; a
candidate that improves 2011 by dropping rows that go nowhere has moved
volatility out of the prior and into the error, which is the same movement read
the other way). Subject to that: a
candidate that materially improves it has stopped asking θ to forecast a
collapse — COPE, the NFP split, the DA/ID merger — which §1.71 says should be
handled by `SPLITS` and arrivals instead.

**A/B/C are still printed and are still useful**, as a three-way comparison of
WHICH RESIDUAL is fitted with `_fit_line` held constant. They are diagnostics.
They are not the floor.

> ⛔ **AMENDED BY THE OWNER, 2026-08-29. THE JUSTIFICATION BELOW IS DEAD AND
> THE KEY IS KEPT.** The paragraph that follows is retained as the record of why
> Key 4 was created, and it is **no longer why Key 4 exists**. See "WHAT KEY 4
> IS FOR" immediately above and "THE VACANCY" immediately below.
>
> The measurement (2026-08-28, MODEL-LOG §1.125): Re-measured on the committed width, the model's baseline and the
> Student-t₇ it draws, **Type A's 2016 fold no longer worsens** — four
> metro-years better, four worse, the 95% interval straddling zero — and 2021
> improves. **Key 4 does not block the change it was created to block.** The old
> block was a Gaussian tail penalty (87.9 nats against the t₇'s 13.3 on one
> collapse) that the model does not incur. Type A is *still refuted*, on §1.74's
> seat condition, and §1.82's refutation of recency weighting *survives and is
> now banded*. But this paragraph's argument is undercut, and the bar is the
> owner's to amend. **Read §1.125 before relying on it.** The recommendation
> there is to keep Key 4 as the layer floor it honestly is and add a PIT
> instrument — which can see a too-narrow width where a t₇ log score
> structurally cannot — before any exclusion is reconsidered.

**This key exists because the first draft of this amendment did not have it, and
an independent review showed the bar would then have shipped the bare Type A
filter** — the one change §1.74, §1.82 and the plan all agree must NOT ship,
because an exclusion moves volatility out of the model's prior and into its
error. Checked against §1.82's own table: Type A improves both cycles (−10,
−14) and improves CRPS (329.4 → 320.3), so it passes Keys 1 and 2 cleanly. The
old §1.61/§1.74 condition — held-out NLL must improve in both folds — was the
guard against exactly that, and dropping it opened the hole.

Keys 1 and 2 score the **panel**, where the parties undergoing structural events
are a handful of columns among hundreds. Key 4 scores **the estimator on those
parties**. Without it a change can get better at the parties the model already
handles by getting worse at the parties it does not — and both rejected
exclusions have precisely that signature: CRPS improves while held-out NLL at
2016 worsens (Type A 0.7531 → 0.8611, state C 0.7531 → 0.9512). **Those three
figures are form A's, Gaussian, without its ½log2π, on the raw baseline** —
measured before the correction above, and the committed baselines are 1.1363 and
1.1425. The ARGUMENT rests on the direction, and the direction is not in doubt;
none of the numbers is the model's. Re-measuring them on the corrected
instrument is item 1 of MODEL-LOG §1.124's open list and must happen before
F22+F23.

It also restores rule 11's logic to this bar — **but only if the clusters are
counted honestly.** Keys 1 and 2 run on ~2 effective clusters; Key 4 runs on
**16 metro-years across 2 cycles**, so its effective count is well below 16 and
above 2. (This line said "18" until 2026-08-28, which predates §1.70's panel
doubling and counted a different set — and it said it as though 18 were 18
independent facts, importing into the key's own justification the exact over-read
rule 11 exists to warn against. The band in the block above is what actually
prices the clustering.)

**Note the asymmetry, which is deliberate.** Key 4 is a *floor* (must not
worsen), not §1.74's *gate* (must improve in both folds). A change may be
NLL-neutral and ship on the panel; it may not ship while making the estimator
worse where the record is thickest.

**KEY 3 — derivedness, priced in the same units as the score.** *"More derived"*
must be measured or it becomes rhetoric and will be used as such. Define
**Derivedness Debt**, in coherent seats:

    D = SUM over constants i of  s_i * L_i

where `L_i` is the constant's **leverage** — the range of panel seat error as it
is swept across its declared defensible range, which `sweep.py` already does —
and `s_i` is its **undefendedness**: typed with no range 1.0, a point off a
record with no interval 0.5, bounded only by a sweep on this panel 0.25,
measured with an interval 0, forced by arithmetic 0. `D` is "how many seats of
this forecast are decided by numbers nobody can defend", and it is a committed
harness artefact, never a claim in prose.

**The trade, and the four things that stop it becoming a licence:**

* **A — non-inferiority, not equivalence-with-excuses.** The trade is available
  only where Key 1 returns `undetermined`. A *replicated* loss fails, whatever
  `D` does. You may buy past noise; you may not buy past a measurement.
* **B — a budget that never refills.** **12 coherent seats on the sixteen**,
  about 3% of 384 and well inside the margin over uniform swing (384 vs 530).
  Every trade spends from it; it is never topped up. Without this, "derived but
  slightly worse" is a ratchet that walks the model downhill one defensible step
  at a time. **This number is DECLARED, not measured** — see
  `JUDGEMENT-CALLS.md`.
* **C — the debt must be RETIRED, not relabelled.** A constant counts only when
  it is deleted from `src/` and its register row is gone. Replacing
  `X = 0.35` with `X = 0.35  # now justified by a paragraph` retires nothing.
* **D — pre-register the derivedness claim, not only the score claim.** Before
  the run: which register rows this retires, what the replacement is estimated
  from, **how many independent clusters that record has**, and the expected `D`.
  §1.80 is the template, and it is why §1.81 is a result rather than a
  rationalisation.

**What does not change.** Rule 10 still forbids choosing the deciding parameter
on the scoreboard; rule 11 still requires saying which validation loop a fit is
in; and a change that is *materially* worse still does not ship, however
elegant. The amendment widens what counts as better — it does not remove the
requirement to measure.

## What follows from that

1. **Score against history and against baselines, not against ourselves.** The
   references are `last-lge`, `uniform-swing`, `prior-lge-noise` (`benchmarks.py`)
   and the previous iteration's recorded scores. Uniform swing is the one that
   matters — it is the only baseline carrying any information about direction.

   **And it is not a strawman — settled 2026-08-20, do not re-litigate.** The
   standard objection is that `last-lge` (594) and `prior-lge-noise` (561) are
   weak, and that the honest reference is Murphy's convex combination of
   persistence and swing. That combination collapses to a *damped* swing
   (`prev + w·swing`), it was built as `benchmarks.blended-swing`, and its
   optimum is **on the boundary at w = 1.0 — uniform swing itself.** Seat error
   is monotone decreasing across the whole interval (594 at 0.0, 456 at 0.5, 376
   at 1.0); the unconstrained optimum at w = 1.05 is worth 4 seats in 376, is not
   a blend, and **loses leave-one-out, 380 against 376.** MODEL-LOG §1.57.

   What is NOT settled, and is the live objection to the headline, is that the
   margin is a **Gauteng** result: **30% off uniform swing inside Gauteng, 24%
   outside** (16 city-years, 2026-08-23), and a loss at Mangaung. `history.md`
   prints the split; quote it. *The 42% / 10% this rule carried until 2026-08-23
   was a nine-city-year figure and was left behind by §1.70 — §1.77's re-read
   did not reach it because the audit test parses only rule 8's two marked
   tables.*

   And quote the **sign count**, which is now the strongest thing this project
   can say: **12 wins, 2 losses, 2 ties against uniform swing across sixteen
   city-years — 7-1 on the 2016 cycle and 5-1-2 on the 2021 one.** It replicates
   across two genuinely different elections, which is what the amended bar's own
   Key 1 asks of any candidate.
2. **A change is not an improvement until it is scored.** Measured, out of
   sample, across as many city-years as the data supports (`src/sweep.py`,
   `src/compare_history.py`, `src/diagnose.py`).
3. **A change that only moves the 2026 numbers cannot be validated here.**
   Anything driven by by-election evidence is in this position: the scraped
   window is 2022-06-01 to 2026-02-26, so no past target has any. Such changes
   are argued, not tested, and must be labelled that way.
4. **Regressions are findable and must stay findable.** The golden-seed
   characterisation tests (`tests/test_drawer.py`) exist to make every movement
   in the prior deliberate. Re-record them when a change is intended, and say in
   the file what changed and why.
5. **The live site is downstream of all of this.** Nothing is republished until
   the model that produced it has beaten the previous iteration on history.
6. **Before tuning a constant, sweep it to a value that MUST change the answer,
   and confirm the answer changes.** A constant whose extreme value moves nothing
   is not calibrated, it is disconnected — and a flat sweep reads as "this lever
   does nothing" when the truth is "you did not pull it". `entrant_prob` returned
   byte-identical rows twice for two different reasons (MODEL-LOG §1.31), and the
   first reading of that was that the arrival machinery was inert. It was not: it
   was sizing the AIC to within 0.2pp and the scoreboard was discarding the
   answer. Sweep through `compare_history.py --set KEY=VALUE`, which lands after
   `apply_city`; editing `montecarlo.DEFAULTS` does **not** reach a run.
   **A MODULE CONSTANT HAS ITS OWN VERSION OF THIS, and setting the module
   attribute is not enough on its own.** `def f(..., df=LEVEL_DF)` evaluates the
   constant once at import, so `montecarlo.LEVEL_DF = 30` reaches nothing:
   `LEVEL_DF` was swept at 2.5, 4, 7, 30, 200 and 1000 for byte-identical output
   at every value while sitting at 🔴 in the register, and `SHARE_FLOOR` and
   `SPINE_K` were frozen at four more sites (MODEL-LOG §1.33). Every constant in
   `src/` now resolves in the function body, and
   `tests/test_ipf_feasibility.py::test_no_numeric_module_constant_is_a_default_argument`
   fails the build if a new one is frozen — but the rule stands whatever the
   test says: **the first thing a sweep must prove is that it swept something.**
7. **A signed error total is not an error total, and a statistic that reports no
   fault is not evidence there is none.** Both of this project's scoreboards
   failed that way at once and neither failure moved a forecast. The rank bands
   reported a SIGNED sum, so Johannesburg 2021's ranks 1-3 read +1.36pp while
   being 26.69pp wrong — the model's worst city-year on seats was the band
   table's second-best row. And the harness computed **no calibration statistic
   at all**: `score.py` had produced coverage and PIT per run for months and
   `compare_history` took `crps.total` and dropped the rest. Both are now in the
   standard report (`compare_history.py`, MODEL-LOG §1.34). When a statistic
   says the model is fine, check what it is capable of saying.

   **AND A NULL IS ONLY AS BROAD AS THE OUTPUT IT WAS MEASURED ON**, which has
   now bitten twice. CLASS 12 compared list shares only and called
   `ward_noise_sd` and `pa_contestation_uplift` dead; both are live on the ward
   side (§1.37). The width budget looked at citywide share only and called the
   turnout knobs zero; they move 46 ward wins (§1.48, §1.51). Before writing "no
   effect", say which output you looked at, and check the one the mechanism
   claims to act on. Two companions to it: never quote a contribution smaller
   than the noise floor printed beside it (§1.48 did, and was corrected), and a
   null measured with a gate shut is a statement about the gate — which is how
   `poll_k` was wrongly certified inert.
8. **Width and level are different faults with opposite remedies, and NEITHER
   can be read off a coverage number.** This rule has now been wrong twice in
   two days, in opposite directions, and both times because a width verdict was
   taken from coverage at a single nominal level. Read the paragraph after the
   table before proposing anything.

   The LEVEL genuinely differs by rank band, and that part has never been in
   doubt. The WIDTH does not: **both bands are too wide, by almost exactly the
   same factor.**

   ⛔ **RE-RECORDED 2026-08-31, DELIBERATELY, AND HERE IS WHY.** The PIT
   randomisation was re-keyed from COLUMN POSITION to `(seed, party name)`
   (§1.150), because the old keying let the seed alone move `reference`/2021
   probit-SD by 0.0327 — making a Key 2 finding built on it 3.4 sd of a paired
   re-roll. Re-keying necessarily moves every PIT value once. Measured against
   the previous artefact: ranks 1-3 **0.510 → 0.510** (it has returned to where it began), ranks
   4-12 **0.613 → 0.629**. The second exceeds this table's own ±0.012 tolerance, which is how
   the guard caught it — correctly.

   **No conclusion moves.** Ranks 1-3 remains centred (CI contains 0.50, cycles
   of opposite sign) and ranks 4-12 remains the one departed band. The
   re-record was intended for the re-emit window; it landed early because
   re-taking the baseline *is* the re-record, which was not obvious in advance.

   <!-- CHECKED-AGAINST-ARTEFACT: data/processed/history.json, claimed columns.
        tests/test_calibration_report.py::test_the_documented_figures_match_the_committed_artefact
        parses the two tables below and fails the build if they and the artefact
        disagree. Do not hand-edit a cell; re-run compare_history.py, commit the
        artefact, and paste what the report printed. -->

   | claimed columns | n | mean PIT | 50% (PIT) | 80% (PIT) | 90% (PIT) | probit-SD |
   |---|---|---|---|---|---|---|
   | ranks 1-3 | 63 | 0.527 | 73% | 94% | 94% | 0.760 |
   | ranks 4-12 | 65 | 0.588 | 62% | 91% | 94% | 0.851 |

   | twenty-one-city-year vote error | signed | absolute |
   |---|---|---|
   | ranks 1-3 | -4.83pp | 181.50pp |
   | ranks 4-12 | -12.54pp | 105.77pp |
   | ranks 13+ | +3.91pp | 24.15pp |
   | phantom (parties that did not stand) | +13.47pp | — |

   **BOTH TABLES ARE NOW MEASURED ON TWENTY-ONE CITY-YEARS (2026-09-02,
   `MODEL-LOG` §1.160/§1.161).** They were nine until §1.70, sixteen until
   §1.77, and are twenty-one now that the 2011 cycle is emitted. The standing
   instruction from §1.70 — *"every number in this repository predating this
   entry was measured on [the old panel] and must be re-read before it is
   quoted again"* — applies again, to everything quoted off the sixteen.

   ⛔ **THE RANKS 1-3 SIGN FLIPPED, AND THE PREVIOUS VERSION OF THIS PARAGRAPH
   SAID IT WOULDN'T.** On sixteen city-years it read *"the fault keeps its shape
   and grows with the panel"*, with ranks 1-3 at **+13.15pp** signed. On
   twenty-one it is **-4.83pp**. The model does not over-forecast the top three;
   on this panel it slightly under-forecasts them. **That claim survived two
   panel expansions and did not survive the third**, which is the whole argument
   for re-reading rather than re-quoting — a sign is the most confidently
   repeated thing in this document and it was wrong.

   The other bands keep their direction and shrink: ranks 4-12 -27.44 →
   **-12.54pp** signed, ranks 13+ +5.04 → **+3.91pp**. Absolute error roughly
   doubles at the top (94.41 → **181.50pp**) and grows by half in the middle
   (71.81 → **105.77pp**), which is expected when five city-years are added from
   a cycle the model had never been scored on; absolute error over more columns
   is not a regression and is not read as one.

   **Phantom mass grew, and it is where the missing sign went**: +9.25 →
   **+13.47pp** on parties that did not stand at all. The three signed bands sum
   to **-13.47pp** rather than to zero for exactly that reason. No band can see
   it, because each iterates the parties that DID stand. A reader comparing the
   ranks 1-3 sign across panels without also reading this row will mis-attribute
   the flip to the top of the ballot; it belongs to the column that is not in
   either table.

   Mean PIT: ranks 1-3 0.510 → **0.527**, ranks 4-12 0.629 → **0.588**. The
   middle band moved toward 0.50 and the top band moved away from it, in the
   direction the signed error now says. **Only ranks 4-12 still excludes 0.50**
   on the cluster bootstrap — [0.509, 0.654] — and ranks 1-3 at [0.494, 0.557]
   straddles it comfortably.

   The width statistic moved substantially and in the direction that matters:
   probit-SD 0.624 → **0.760** at the top and 0.808 → **0.851** in the middle,
   both toward 1.0. **Nothing about the width was changed between the two
   measurements — the panel was**, so this is not evidence that a width fix
   worked. It is evidence that the sixteen-city-year width verdict was measured
   on too little, and the earlier reading of the top band as far too sharp was
   overstated. 50% PIT coverage falls 83% → 73% at the top with it.

   **The tail is the cost, it was attacked, and it stays.** Ranks 13+ sit at
   **+3.91pp** signed on twenty-one city-years (+5.04pp on the sixteen, −1.55pp
   before the shrink, +5.60pp on the nine): a band that was very nearly unbiased
   is over-forecast, because the shrink returns its freed mass by uniform
   renormalisation and there are many micro-parties to receive it. §1.54 built
   the obvious fix — a soft floor on the receiving side — and measured it: it
   closes the tail and **costs 14 to 22 coherent seats**, while making ranks 1-3
   and 4-12 *both worse*. The mass withheld from the tail goes to the TOP, not
   the middle, because every weight tried is monotone in size. And the tail is
   **33 of 3,684 seats** at stake across the twenty-one — **0.90%** of what is
   being contested, against 1.1% on the sixteen and 1.8% on the nine. ⚠️ The 33
   did not move when five city-years were added, so the share falls purely
   because the denominator grew; that is arithmetic, not an improvement.

   So this is a bias the project has decided to carry, on the record, rather
   than an outstanding defect.

   **On level.** On twenty-one city-years the claimed mean PIT is **0.527** at
   ranks 1-3 and **0.588** at ranks 4-12 — both above 0.50, i.e. both bands now
   read as UNDER-forecast rather than as an over-forecast averaged with an
   under-forecast. Only the ranks 4-12 cluster-bootstrap CI excludes 0.50 —
   **[0.509, 0.654]** — against ranks 1-3 at **[0.494, 0.557]**, which does not
   separate from centred.

   ⚠️ **The sentence this replaces said the model "still over-forecasts the top
   three", and on this panel it does not.** The figures it quoted ([0.537,
   0.684] and [0.474, 0.544]) were the sixteen-city-year values and must not be
   requoted. ~~**That split survived the panel doubling**, which is the first
   out-of-sample evidence rule 8 has ever had for its central claim: it was
   measured on one electoral cycle and it holds on two.~~

   > ⛔ **FALSE ON THE ARTEFACT THIS RULE CITES (2026-08-29, MODEL-LOG §1.132).**
   > The pooled interval above is correctly computed; the out-of-sample
   > inference from it is not. **Split by cycle, the split is a 2021
   > phenomenon and is ABSENT at 2016.** At 2016 the ranks 4-12 signed vote
   > error across the eight metros is **−0.04pp** against 2021's **−26.07pp**,
   > `sd(z)` is **0.485** against 2021's **2.262**, and the mean-PIT interval
   > contains 0.50. The only band with a significant 2016 deviation is ranks
   > 1-3, **running opposite to 2021**. It holds on one cycle and is absent on
   > the other, so pooling two cycles that disagree in sign is what produced the
   > appearance of replication. **Never quote a width or a PIT pooled over
   > cycles without the per-cycle pair beside it.**

   **That gap is a zero-sum transfer, not two independent faults**: shares sum
   to one, so the +12.55pp at ranks 1-3, the +4.42pp at 13+ and the +9.60pp of
   phantom mass are the same points as the −26.57pp at ranks 4-12 — they balance
   to the last decimal. A level fix must MOVE mass; adding it anywhere takes it
   from somewhere, which is exactly why the level shrink had to redistribute
   what it took rather than simply lower the top.

   **On width — and this is the part that was wrong.** This rule once said
   ranks 4-12 were "too NARROW — widen them", on the strength of the 50% column
   alone, which then read 31%. **A forecast whose intervals are too narrow
   under-covers at EVERY level.** They over-covered at 80% and 90% then, and
   they still do (91% and 94%). What produces a low 50% with a high 80 and 90 is
   a forecast that is *shifted* — it has vacated the middle of its own interval
   — sitting inside intervals that are *too wide*.

   The level shrink is the direct evidence for that reading, because it moved
   the level and nothing else: the 50% (PIT) column for ranks 4-12 went from
   **31% to 51%** without a single interval being widened or narrowed, and the
   contestation correction of §1.47 took it on to **59%** the same way. A width
   fix could not have done either.

   Both also moved the level-free width statistic toward correct without
   touching a width constant: ranks 4-12 `sd(z)` was **0.628** before the level
   shrink and is **0.823** now, against a nominal 1.0. That is what it looks
   like when a LEVEL fault stops masquerading as a width one.

   That is not an argument, it is a fixture, and it is in the suite. The rows
   below come from `tests/test_calibration_report.py::_shift_scale_results(4242,
   12, width_mult=W, shift=S)` — nine small parties on a mean of 4 seats, the
   real band's scale — run through this repository's own `calibration_columns`:

   | ranks 4-12 fixture | mean PIT | 50% | 80% | 90% | PIT var | probit-SD | sd(z) |
   |---|---|---|---|---|---|---|---|
   | correct width, no shift | 0.552 | 0.454 | 0.824 | 0.880 | 0.0829 | 1.021 | 1.000 |
   | correct width, **+2 shift** | 0.794 | 0.269 | **0.556** | **0.759** | 0.0450 | 0.917 | 1.000 |
   | correct width, +3 shift | 0.876 | 0.167 | 0.361 | 0.509 | 0.0240 | 0.953 | 1.000 |
   | **1.6× too wide, +2 shift** | 0.740 | 0.435 | **0.861** | **0.935** | 0.0270 | 0.571 | 0.650 |
   | **the model, ranks 4-12** | **0.757** | **0.321** | **0.893** | **0.964** | 0.0388 | **0.734** | — |

   A shift takes coverage away at every level. **Only excess width puts it back
   at 80 and 90**, and the model's row sits with the too-wide arm at both.

   The statistics that settle it are in the report's *"Is it the right WIDTH?"*
   table, which divides the level out: **probit-SD is 0.740 at ranks 1-3 and
   0.734 at ranks 4-12** — 1.00 being right, below 1.00 too wide. The two bands
   are dispersed almost identically, both about **1.35× wider** than the errors
   they cover. Note `sd(z)` in the table above: exactly 1.000 at every shift
   when the width is right. That is the column to prefer once the artefact
   carries it; the artefact quoted here predates it.

   **So the corollary that "no single change can fix both bands" is also
   wrong.** Both bands want the same thing on width — narrowing — and the level
   difference is one transfer. A change that narrows the seat distribution and
   moves mass from the top three to the middle is a single coherent proposal,
   not two contradictory ones. It still has to beat the baselines on history
   before it ships.

   **Statistics that do NOT answer the width question, and were each used to:**
   - *Coverage at one nominal level.* Confounded with the level. This is the
     mistake, twice.
   - *PIT variance against 1/12.* Claimed as "shift-invariant, therefore
     clean". It is not shift-invariant — a PIT is bounded, so a shift piles mass
     against an endpoint and the variance falls whatever the width is. On the
     correct-width fixture above it reads **0.0829, 0.0450 and 0.0240** at
     shifts of 0, +2 and +3 seats against a nominal 0.0833: a pure level error
     reading as a 3.5× under-dispersion. So the model's 0.0388 is not evidence
     of narrowness — and neither are its empty tails (0 columns below PIT 0.05,
     1 above 0.95), since a shift evacuates one tail and excess width evacuates
     both.
   - *Recentring the PIT about its own mean and re-reading coverage.* Same
     boundary problem; on that fixture it reads 0.55, 0.85, 0.94 at shifts of 0,
     +2, +3 — it does not remove the shift, it reports it.
   - *`score.pit_histogram`'s shape verdict.* It tests the two END bins, so a
     monotone-increasing histogram scores as U-shaped. On ranks 4-12 it reads
     `[1, 1, 1, 11, 14]` — 25 of 28 columns in the top two bins, nothing at the
     bottom — and prints *"U-shaped … under-dispersed, widen it"*.

   **And read the intervals — none of these coverage cells is strong evidence
   on its own.** Coverage rows are now printed with cluster-bootstrap intervals
   (ranks 4-12 at 50%: 32% [19–50], which includes nominal). Taken one at a
   time, against nominal, on a binomial test that ignores clustering and so
   flatters every one of them:

   | | ranks 1-3 | ranks 4-12 |
   |---|---|---|
   | 50% (PIT) | 19/27, p = 0.026 | 9/28, p = 0.044 |
   | 80% (PIT) | 25/27, p = 0.072 | 25/28, p = 0.16 |
   | 90% (PIT) | 26/27, p = 0.23 | 27/28, p = 0.22 |
   | probit-SD vs 1.0 | 0.740, p = 0.030 | 0.734, p = 0.025 |
   | **probit-SD, both bands** | | **p = 0.003** |

   So the 80% and 90% over-coverage this rule argues from is **not individually
   significant**, and it should not be quoted as though it were. What it does is
   rule out the narrow reading — a narrow forecast cannot over-cover at all —
   while the weight of the evidence sits in the level-free dispersion statistic,
   which uses all 55 columns at once and rejects correct dispersion at
   p ≈ 0.003. Two caveats in opposite directions: columns cluster within
   city-year, so the true p is larger than any figure above; and the probit-SD
   is attenuated by the shift, so the true excess width is larger than 1.35×.

   The discreteness correction is thinner still. What turned "about right" (43%
   raw) into "far too narrow" (32% PIT-corrected) at ranks 4-12, and carried
   §1.36's whole width argument, is **three discordant columns** out of 28 — a
   one-sided sign test at p = 0.125. At ranks 1-3 it is two, p = 0.25. The
   correction is real and the direction is right; it is not a result you can
   build a conclusion on by itself, and it was.

   **A WIDTH COMPARISON GOES ON `reference`, NEVER ON `claimed` — added
   2026-08-20, and it changes the ranks 4-12 half of everything above.**
   `claimed` selects columns from the forecaster's own draws, so two settings of
   a lever are scored on two different populations: 58, 67 and 81 columns across
   the `dirichlet_scale` sweep, of which 30, 37 and 45 are ranks 4-12. Worse,
   the rule selects **away from the failures** — a party the model gives a seat
   in fewer than half its draws is a party the model is failing on, and Cape
   Town's Cape Coloured Congress (z = +12.1) and Johannesburg's PA (z = +9.3)
   are outside `claimed` and inside `reference`.

   On the fixed population ranks 4-12 read `sd(z)` **1.940** against `claimed`'s
   0.823. Ranks 1-3 are the same 27 columns in both and are unchanged at 0.855.

   **AND CHOOSE THE STATISTIC BY THE BAND — §1.58, the same day.** `sd(z)`
   supersedes probit-SD *on continuous columns* and is meaningless on a
   near-degenerate discrete one: where the forecast is roughly Bernoulli(p) and
   the truth is zero, `z = −√(p/(1−p))` exactly, and observed `z` on the 96
   such ranks-13+ columns correlates with that expression at **+0.93**.
   probit-SD is valid there and is attenuated by a shift, so it is a lower
   bound wherever `mean z` is far from zero. Neither is right everywhere; the
   pair is. So:

   - **Ranks 1-3: genuinely too wide, by about 1.5×** (probit-SD 0.682, `mean
     z` −0.009 so nothing is attenuating it). This is the band that is too wide
     and the band that responds to `dirichlet_scale`.
   - **Ranks 4-12: not describable by one width.** On the same 74 columns
     `sd(z)` says 1.940 (far too narrow), `IQR-sd` says 0.595 (too wide) and
     probit-SD says 1.020 (about right, attenuated by `mean z` +0.796). They
     disagree because the distribution is a narrow shifted bulk plus two
     enormous outliers. **Mis-shaped, not mis-scaled** — no scalar fixes it.
   - **Ranks 13+: probit-SD 1.188, and INERT** — 1.208 → 1.192 across a 32-fold
     change in concentration. 124 of the 225 fixed columns. `dirichlet_scale`
     is not their lever.
   - The corollary two paragraphs above — "both bands want the same thing on
     width, narrowing" — is **withdrawn**. It was read off `claimed`, and on a
     fixed population only ranks 1-3 wants narrowing.
   - **CRPS wants the forecast narrower than the seat error does, all the way
     out**: across `dirichlet_scale` 0.5 → 16 CRPS falls monotonically 256.4 →
     212.5 while coherent seats stay flat at 254–262. A width decision taken on
     CRPS alone runs to the end of the sweep. Do not take one.

   The multiplier this rule quotes as "about **1.35×** wider" is also stale: it
   comes from probit-SD figures (0.740 / 0.734) measured before the level
   shrink. The committed artefact reads 0.685 / 0.695 probit-SD, i.e. 1.17–1.21×
   on `claimed` — and on `reference` ranks 4-12 the sign reverses entirely.
   MODEL-LOG §1.56.

   **`reference` coverage and PIT are not calibration figures.** A population
   fixed on inputs must contain columns that are zero on both sides, each a free
   interval hit, so it reads optimistically by construction. The dilution is
   identical at every setting, which is what makes a DIFFERENCE readable.
   Quote `claimed` for "is this model calibrated"; quote `reference` for "did
   that change help".
9. **Quote the pooled calibration figure, never a city-year's — and never the
   pooled figure alone.** Pool over CITY-YEARS: per city-year it is four to
   fifteen scored columns, Johannesburg 2021 reads 12/62/75 against nominal
   50/80/90 on n=8 and Cape Town 43/100/100 on n=7, and neither says anything.
   Do NOT pool over RANK BANDS: that is rule 8, and it is where the pooled
   number stops being an estimate of anything. The report prints the city-years
   for provenance and labels them as noise, and prints the band split next to
   the pool.
10. **"Improves the backtest" and "defensible" are different claims, and only the
   second one ships.** A constant chosen because it scores best on the nine
   city-years has been fitted to the scoreboard. `entrant_prob` has a clear
   empirical optimum near 0.40 and it was **not** adopted, because nothing
   outside those nine picks it; the arrival record independently gives 0.29–0.35.
   **That advice is WITHDRAWN as of 2026-08-22 (MODEL-LOG §1.69), and the
   withdrawal is instructive.** Both derived values were measured on the nine
   city-years at 1500 draws and both are worse, monotonically: 254 coherent at
   the committed 0.25, **262 at 0.290 and 264 at 0.353**, with CRPS 232.7 /
   234.3 / 236.1. *Worse, and nothing more honest is being bought.* Note this is not a constant chosen ON
   the scoreboard — 0.25 is the incumbent and the scoreboard was used to REJECT
   a change, which is the one thing it is unambiguously for. And §1.31's finding
   that "the whole range is inside the noise" **has expired**: the same sweep
   moved 2 seats then and moves 10 now, because the level shrink, the
   contestation correction and the poll paths all landed in between. A null is a
   statement about the model that measured it. When a change improves the score,
   say *what evidence outside the score chose it* — and if the answer is "the
   score", say so and leave the constant alone.
11. **"It was forward validated" does not answer rule 10. Say WHICH LOOP.**
    Added 2026-08-20 after the claim *"that is a fit to the forward-validated
    record, not the scoreboard, so rule 10 permits it"* was made about the
    `sd_for` refit and does not survive contact.

    **`compare_history` IS a forward-validated record** — of the whole model
    rather than of one layer — and it is computed on the same elections. "The
    record" and "the scoreboard" are not two datasets. There are three levels,
    and only one of them is where rule 10 bites:

    | | what happens | leakage? |
    |---|---|---|
    | **L0 — estimation** | the model fits its own parameters from data strictly before its target, afresh at every target (`theta_prior` refits `sd_for` per metro-year) | **none.** This is what a model does; rule 10 is not about it |
    | **L1 — specification** | a person chooses the functional form, the covariate, the bin edges — **once, having looked at every target including the ones L2 scores** | **this is the leak** |
    | **L2 — evaluation** | the nine city-years | biased by exactly as much as L1 saw |

    Choosing at L1 using data L2 then scores makes L2 optimistically biased.
    That is the standard nested-cross-validation result and it is the same trap
    §1.44 already carries: the level shrink's *value* was chosen by
    leave-one-city-year-out, but its *functional form* was chosen by screening
    four candidates against all nine.

    **So the defence of a fit is never "it was out of sample". It is the number
    of INDEPENDENT CLUSTERS the fit had, against the number of free parameters
    it spent.** On this panel those numbers are brutal:

    - the **scoreboard** has 9 city-years of which **8 share one cycle** — the
      2021 national swing, ActionSA's arrival, one fragmentation shock. Under
      any honest clustering the effective sample is **about 2**.
    - the **θ residual record** (`src/theta_residual.py`) has **n=403 across 32
      metro-year clusters** spanning four cycles. (Written as 257 across 18
      when this passage was drafted; §1.70 doubled the panel to eight metros
      and nobody came back for the sentence. Re-measured 2026-08-28. **Key 4's
      own two folds are the 2016 and 2021 slices: n=235 across 16 clusters.**)

    The forecasting literature's rule of thumb is on the order of 30 independent
    observations per free parameter before a fitted choice is trustworthy. At
    two effective clusters **the scoreboard supports approximately zero
    parameters chosen on it**, which is why rule 10 exists and why it has been
    right every time it has been applied. Sixteen clusters is not thirty, but
    it is not two either, and the difference is the whole argument.

    **The protocol that follows.** When a specification choice must be made from
    data, nest it explicitly: choose the form on the earlier targets, apply it
    unchanged to the later one, and report L2 only on the held-out target — then
    reverse. With four LGE targets in the θ record that is executable (choose on
    2006+2011+2016, apply to 2021; then choose on 2006+2011+2021, apply to
    2016). And say in advance what result would count, because **an effect
    smaller than two effective clusters can resolve is "undetermined", not
    "adopted"**.

12. **A SCORING CHANGE PROVES IT RAN ON PRODUCTION TYPES BEFORE IT ARBITRATES
    ANYTHING.** Added 2026-08-29. Rule 6 makes a *lever* prove it swept
    something; the same obligation falls on an *instrument*, and this bar did
    not have it.

    `backtest.arrival_group_score` — the label-free arrival referee, built
    precisely to remove the outcome-favourable relabel — indexed `seat_draws`
    (a `list[dict[str, int]]`) as a 2-D array and raised `IndexError` on **every
    one of the sixteen city-years, from the day it was written**.
    `compare_history` catches per city-year, so the failure printed as
    `nothing runnable` and **read as absence of data rather than as a defect**.
    The suite was green and `freeze --verify` VERIFIED throughout: *the preflight
    tests the MODEL and cannot see a broken REFEREE.* Its one unit test used a
    dense 2-D fixture production never builds — the right function with the wrong
    types.

    So: **a new or changed score must be run once through `compare_history` on
    real input and return a finite number on every city-year before any verdict
    is read off it, and a per-city-year `failed:` line is a BUILD FAILURE, not a
    null.** "It is in the suite" is not this proof — a fixture proves mechanism,
    not that the production caller can reach it. §1.136.

13. **A CYCLE THAT CANNOT MOVE IS NOT A CYCLE THAT REPLICATED.** Added
    2026-08-29. Key 1's pass condition asks that *"no cycle shows a net loss"* —
    and a cycle where the candidate is structurally inert satisfies that
    trivially, eight city-years at a time.

    **For any arrival-channel candidate, 2016 is a null arm**: all eight emitted
    2016 specs carry `arrival_group: null` and **zero** seeds,
    `montecarlo.py:2699` leaves `group_idx = None`, and the same RNG draws are
    consumed either way — confirmed empirically on 2026-08-29, when all eight
    2016 city-years came back byte-identical across both arms. The fold note
    under Key 4 already says this in its own case — *"gating on a fold that
    cannot move is not a gate"* — and it applies to Key 1 unchanged.

    **A candidate must state, before the run, which cycles its arm can move. A
    frozen cycle is reported as `null arm`, never as "no net loss".** §1.136.

## When to stop — written 2026-08-21, because "keep iterating" is not a plan

> ## ⚠️ THIS SECTION IS OBSOLETE (2026-08-23) — READ `PLAN-TO-LIVE.md` INSTEAD
>
> **Both of its load-bearing premises have been overturned.**
>
> * *"Nine city-years, about two effective clusters."* §1.70 doubled the panel
>   to **sixteen city-years and two cycles**. The argument that the panel
>   "supports approximately zero parameters chosen on it" was correct given its
>   premise, and the premise was never a fact about South African electoral
>   data — it was a fact about which ingest had been run.
> * *"There is no remaining change that improves seat accuracy."* Three
>   candidates now improve CRPS and two improve seats: the Type A filter
>   (384 → 360, CRPS 320.3), the footprint exclusion (384 → 368, CRPS 324.7),
>   and the two combined (366). See §1.78, §1.81, §1.82.
>
> The section is kept because `MODEL-LOG` reasoning refers to it and because
> deleting a superseded argument destroys the record of why it was made. **Do
> not act on it.** The current plan, its freeze date and its abandon-condition
> are in `PLAN-TO-LIVE.md`; the current acceptance bar is the amendment at the
> top of this file.


⛔ **STALE SINCE THE PANEL BECAME 24, AND THIS FILE'S OWN RULE SAYS SO.**
§1.77 instructs that every number predating §1.70 be re-read before it is quoted
again; the panel then went 16 → 24 on 2026-09-02 and this headline never moved.
**On the current 24 city-years the coherent seat error is 707** — 29.5 per
city-year against the 24.0 below — and no uniform-swing comparison has been
taken on the wider panel. The paragraph is kept because the *sign* of the claim
is what matters and it has not been retested, not because the figure is current.
⚠️ **Do not quote 384 without saying it is sixteen city-years.**

The only question this file asks is whether the model predicts past elections
better than the last version and better than the baselines. It does: **384
coherent seat error against uniform swing's 530 across sixteen city-years, with
12 wins, 2 losses and 2 ties — 7-1 on the 2016 cycle and 5-1-2 on the 2021 one**,
and uniform swing is measured to be the strongest member of the naive family
(§1.57). The sign replicates across two genuinely different elections, which is
what this file's own amended Key 1 asks of any candidate.

*(Corrected 2026-08-23. This paragraph said "254 against uniform swing's 376" —
a NINE-city-year figure — for a day after §1.77 re-read rules 1 and 8 onto
sixteen. §1.77's own instruction was that every number predating §1.70 must be
re-read before it is quoted again, and the file's own headline verdict was the
number it missed. The section below is likewise still written on nine.)* What follows is the
other half of the question, which this file never answered: **when is it done?**

### The panel has a floor, and the model is close to it

Three separate measurements, none of which were taken to answer this:

* **The scoreboard carries about two effective clusters.** Nine city-years, eight
  of them one cycle (rule 11). The forecasting rule of thumb is ~30 independent
  observations per fitted parameter. **This panel supports approximately zero
  parameters chosen on it**, which is why rule 10 has been right every time.
* **θ is at its estimation ceiling.** Forward validation puts the floor at
  RMSE(log θ) = 0.715 — a typical error of about 2× on a party's retention —
  and every enrichment tried (year, metro, fragmentation, party dummies
  unpooled) scored *worse* out of sample (§1.43).
* **A third of the error is one party in one city.** Johannesburg 2021 is 86 of
  the 254, and ASA is the largest single party term at 47 of 290 on the median
  vector — an arrival with one prior local election. Its miss mechanically
  generates the ANC, DA and EFF over-forecasts, because shares sum to one.

### And there is no remaining change that improves seat accuracy

Everything with a measurement behind it has now been tried:

| candidate | result | measured at |
|---|---|---|
| `sd_for` refit, two forms | **verdict STALE** — refuted on form A's Gaussian score on the raw baseline, and A/B/C reach `levels` only through the clamp, so that gate cannot see an `sd_for` change at all (Key 4 correction block) | §1.62 |
| arrival-group draw | **re-measured 2026-08-29 and still refuted** — but the 254 → 348 was scored through the outcome-favourable relabel and on a half-null panel, so **cite §1.136, not §1.63** | §1.63, §1.136 |
| chi-square bias correction | **refuted** — worse on everything | §1.50, §1.59 |
| tail soft-floor | **refuted** — costs 14–22 seats | §1.54 |
| symmetric spine blend | **refuted** — 312 → 338 | register |
| `dirichlet_scale` narrowing | **a trade, not a win** — fixes ranks 1-3 width and costs 4 seats at 1.4, 8 at 2.0 | §1.55, §1.58 |

**⛔ THE ARRIVAL ROW IS RE-MEASURED, NOT MERELY RE-ASSERTED (2026-08-29, §1.136).**
Its original 254 → 348 is withdrawn as evidence on three counts: it was scored
after `backtest.relabel_run`, which renames the model's nameless `ENTRANT` onto
`max(newcomers, key=seats)` — the largest realised arrival, chosen with the
outcome in hand (`backtest.py:596`); half its panel is a **structural null arm**
(all eight 2016 specs carry `arrival_group: null` and zero seeds); and the lever
is **mis-scoped** — it zeroes every seeded arrival column, so it deletes the
splinter channel rather than replacing the generic slot, turning ActionSA's 6.85%
seed into 0.18% against an actual 18.12%.

The fair re-run was done on 2026-08-29 with the label-free referee and **the
refutation holds** — 2 of 8 metros at 2021, pooled Σ|mass_err| 0.2714 → 0.5084,
Key 2's level-free width 1.2000 → 1.3557, and the direction survives dropping the
two largest arrival metros. **But it refutes THAT LEVER, not the idea of scoring
arrivals as a group**, and no later citation may collapse the two. A test of the
group *estimator* needs a lever scoped to the generic slot alone; it does not
exist.

The last row is the only one with a live case, and it is a trade: ranks 1-3 are
about 1.47× too wide (probit-SD 0.682, unattenuated) and narrowing fixes it **at
the cost of coherent seats**. *Worse with nothing more honest bought* decides that, and rule 10
decides it again, since the method-of-moments fit names 1.0.

### So the remaining work is not modelling

**Stop opening new modelling fronts.** What is left that is worth doing:

1. **Publish.** The forecast is the point, the published page is an output of an
   earlier version, and the pre-nomination window closes on 16 September. This is
   the only time-critical item and its value decays to zero.
2. **A4, on 16 September.** Dated and certain: real nomination lists make the
   contestation correction live, retire `contestation_expand`, and cut phantom
   entrant mass. Mechanical, not a modelling bet.
3. **Disclosure, which is cheap and forecloses the strongest criticisms** —
   already largely done: the Gauteng split (§A7), calibration on a fixed
   population (§1.56), and the stated failure mode the publication gate asks for.

**What to stop:** any constant fitted on these nine city-years. A3's
fragmentation-dependent shrink is the clearest example — its per-city-year
optimum really does span 0.00 to 0.65, and that heterogeneity cannot be
distinguished from the 2021 shock with two effective clusters. It is the same bet
§1.62 just lost.

### What would license restarting

Not an idea. **More independent clusters.** Concretely: the pre-2011 archive
ingested for the seven metros that only have Johannesburg before 2011, which
would roughly double the θ record's cycles; or the 2026 result itself, which adds
a genuinely independent cycle and is the first honest out-of-sample test this
model will ever get.

Until one of those exists, a change that improves the nine city-years is
evidence about the nine city-years.

### And the panel was smaller than the archive for a second reason nobody had found

**Added 2026-08-22 after an outside audit — MODEL-LOG §1.69.** The paragraph
above is right that the pre-2011 archive is the thing to get. It was wrong about
what stood between here and a bigger panel, in a way that made the ceiling look
lower than it is.

`backtest.runnable_targets` reports what the ARCHIVE supports: 2011, 2016 and
2021 **for all eight metros — twenty-four city-years.** `compare_history.runnable`
reported nine. The gap was never stated anywhere, and it had two independent
causes that looked identical from outside because both produced a silent absence:

1. **No emitted pool spec.** Seven of the eight metros had `pools_2021.json` and
   nothing else. This needed **no new data at all** — the `lge2011_*` and
   `npe2014_*` files have been on disk throughout — and it has been fixed: all
   eight 2016 specs are now emitted.
2. **No γ fold.** A 2016 target needs a γ fold strictly preceding it, which is
   fold 3 (2009 NPE → 2011 LGE), which needs `npe2009` and `lge2006`. **Those
   exist for Johannesburg and for no other metro.** There is no way round it:
   fold 1 targets 2016 itself, so borrowing its γ reads the answer.

So the second blocker IS the pre-2011 ingest this file already named — and the
first one was a separate, invisible, entirely mechanical limit sitting in front
of it. **That changes the value of the ingest, not the verdict.** The pre-2011
archive for seven metros now buys **seven city-years and a second full electoral
cycle immediately**, because the other half of the work is done and committed.
It is no longer "roughly double the θ record's cycles, eventually"; it is the
single remaining step.

`compare_history` now PRINTS what the archive supports and this harness cannot
run, with the reason, on every invocation. The number of city-years is the
denominator of every claim this file makes, and it must not be able to shrink
quietly again.

## Where the record lives

* `MODEL-LOG.md` — findings, obstacles, decisions, mitigations. Append, never
  rewrite.
* `JUDGEMENT-CALLS.md` — every structural choice not forced by the data.
* `data/processed/history.md` — the current iteration's scores against history.
* `DATA-QUALITY.md`, `SOURCES.md` — what the inputs are and what is wrong with
  them.
