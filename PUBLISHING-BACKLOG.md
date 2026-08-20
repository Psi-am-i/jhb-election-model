# Publishing backlog — the presentation layer, deliberately not the model

**This list is separate on purpose.** The other list is "get a working
prediction model that is publishable". This one is everything that only matters
*once* it is. Nothing here is allowed to compete for attention with the model,
and nothing here is a reason to change a forecast.

The project owner's standing position, 2026-08-18 and again 2026-08-20:

> "I am not concerned with the live page or what lives on it. Nor am I
> interested in the interactive... I am only interested in this model's ability
> to predict."
>
> "we will rebuild interactive and live page when model is ready."

So: **build these when the model is ready, not before.** Read
`ITERATING.md` rule 5 — nothing is republished until the model that produced it
has beaten the previous iteration on history.

---

## 1. The interactive is a frozen program, not a stale page

`forecast-interactive.html` and `site/dev/interactive.html` are **tracked**,
were built 7–8 August, and still carry a "PA's wider slate" slider driving
`paUplift` — a constant the model deleted on 2026-08-18.

`src/build_interactive.py` **refuses to rebuild them**, and says why:

> the interactive page has not been ported to voter pools: its in-browser
> drawer is the old two-bloc engine and there is nothing left to feed it. The
> published page stays frozen in the meantime.

So a reader opening either file sees controls for constants that no longer
exist, driving an engine that no longer exists. That is not a stale figure, it
is a **stale program**, and it is the third instance of a pattern `CLAUDE.md`
opens by warning about — after the `turnout_tilt_da` claims and `site/plan.html`
being served for weeks after no build produced it.

**Nothing in the model reads them.** They are inert as far as the forecast is
concerned. They are only a trap for a human.

When the model is ready, the options are:

* **port** the in-browser drawer to voter pools — the only one that makes the
  page true again, and the largest;
* **delete** both files — they are outputs of an engine that no longer exists;
* **banner** them as frozen, if they are wanted as a historical record.

Until then they should not be read as current by anyone, including us.

## 2. The 2026 forecast has moved and has not been republished

Two changes this week moved the live numbers, both deliberately, neither
published:

* the **level shrink** (§1.44) — DA 0.328 → 0.310 on the PR ballot;
* the **contestation correction** (§1.47) — PA ward share 8.07% → 2.67% and
  mean seats 19.5 → 12.4, with every other party gaining slightly.

Whatever is published next has to be produced by one settled run, with the
stat tokens regenerated from it, per `CLAUDE.md`'s rule that a model figure is
never typed into prose.

## 3. Orphaned stat tokens

`content/joburg/stats.toml` still carries claim tokens the build refuses to
publish. Removing or re-deriving them is a **content** decision, not a code one,
and it waits for the same settled run.

---

# The revamp: plan of attack

Written 2026-08-20 at the owner's request — *"we will use our new model to
update and revamp it completely… a revamped interactive with our new levers and
exposing our judgement calls… and we need to allow users to try it."*

**This is a plan, not a commitment to build now.** `ITERATING.md` rule 5 still
holds: nothing is republished until the model that produced it has beaten the
previous iteration on history. It has (254 against 312 a week ago, 8 of 9
against uniform swing) — so the gate is passable, but the model list should be
closed first.

## 1. What is actually broken, precisely

`build_interactive.py` refuses to run, and its note names the exact reason:

> That drawer is the two-bloc engine, which the model no longer has: it takes
> two membership lists and two shift triangulars, and there is nothing left to
> feed it. Porting it means handing the JS the emitted pool spec — N pools, each
> with members {party: weight}, a ratio triangular and an alpha — and replacing
> the two hard-coded dials with one per pool.

That note is from before the level shrink, the contestation correction and the
Dirichlet handle. **The port is bigger than it says**, because the level chain
it must mirror has changed underneath it.

## 2. The fidelity problem, which is the whole design constraint

The page reimplements the forecast in JavaScript so a reader can move dials and
watch seats respond. That means **two implementations of one model**, and the
second one drifts. This repository has already published a page whose controls
drove constants the model had deleted.

So the revamp is only worth doing with a **fidelity gate**:

* `export_interactive.py` emits the data pack **and** a reference run — a set of
  scenarios with the Python model's answer for each;
* the page recomputes those scenarios in the browser on load and **refuses to
  render** if it disagrees beyond a stated tolerance;
* the tolerance is published on the page, not hidden.

`src/width_budget.py` and the `--run-dir` trace are the instruments that make
this checkable: the trace gives the Python intermediates for any scenario, so a
JS/Python disagreement can be localised to a stage instead of argued about.

**If we will not build the gate, do not build the page.** An interactive that
can silently disagree with the model is worse than no interactive.

## 3. Which levers to expose — and which must NOT be

Twenty-five keys are in `DEFAULTS`. Most should never reach a slider. The last
week measured which is which, and that is the real inheritance from the model
work.

### Expose — these move the answer and a reader can reason about them

| lever | default | what a reader is choosing |
|---|---|---|
| `level_shrink` | 0.35 | how hard the top of the ballot is pulled toward the middle. **The single biggest modelling choice in the forecast** (§1.44) |
| `dirichlet_scale` | 1.0 | how much the within-pool split is allowed to vary — the dominant width lever (§1.48, §1.55) |
| `entrant_prob`, `entrant_share` | 0.25, [1,4,12]% | whether a party arrives from nothing, and how big |
| `spine_k` | 1.0 | how much a party's own local record outweighs the national spine |
| `w_bye` | 0.4 | how much by-election evidence counts. **2026 only** — no past target has any |
| `overhang_rule` | deduct | the statutory reading. `deduct` is the law; `expand` and `cap` are labelled counterfactuals |
| `turnout_pattern_blend` | 0.5 | which turnout pattern the draw leans on |

### Do NOT expose — with the reason, because each is a trap

* **`turnout_noise_sd`, `turnout_blend_jitter`** — measured to change citywide
  dispersion by nothing at all across a tenfold move (§1.48). They move ward
  wins, so they are not dead, but a slider that visibly does nothing to the
  headline teaches the reader the model is unresponsive.
* **`ward_noise_sd`, `dirichlet_floor`, `level_floor`, `poll_k`,
  `bye_local_cap`, `bye_tau_months`, `w_bye_local_*`, `entrant_geography`** —
  guards, gated-off machinery, or numerical floors. `w_bye_local_*` are 0.0 by
  design and untestable in any backtest.
* **`poll_id`, `poll_weight`** — the legacy poll path. Live and conditional, and
  exposing it invites a reader to import a poll the model was not validated with.
* **`SD_FLOOR`** — a module constant, not a scenario key, and §1.50 shows it is
  a conditional dispersion doing a subtle job. A slider would invite exactly the
  misreading the register spent two sections correcting.

**The principle**: a lever earns a slider if moving it is a *modelling opinion a
reader can hold*. Guards, floors and instruments are not opinions.

## 4. Exposing the judgement calls — the genuinely new thing

`JUDGEMENT-CALLS.md` is already the register, with a status per row: 🔴 wants a
second opinion · 🟡 defensible, bounded by evidence · 🟢 forced by arithmetic.
**That structure is the feature.** Nobody else publishing a forecast shows this.

Proposed: every exposed lever carries its register status inline, and clicking
it opens the row — the value, where it lives in the code, what was measured, and
what would change our mind. Generated from `JUDGEMENT-CALLS.md` at build time so
it cannot go stale, and the build fails if a slider has no register row.

The honest framing to put on the page: **these are the numbers the data did not
force.** Some are measured and survived (`SHRINK = 2.0`, `entrant_prob`), some
are typed and admitted (`w_bye`), and at least one is a known open question
(the §3.5 θ sanity ranges the model violates and reports against itself).

## 5. What the page must say about itself

* the backtest, prominently: **254 coherent seat error against uniform swing's
  376**, and that this is nine city-years with eight in a single cycle;
* that ranks 4-12 are under-forecast by 22.76pp and the model knows it;
* that the tail is over-forecast by 5.60pp as a *deliberate* trade (§1.54);
* the ward-level approximation the page makes against the Python model, measured
  and quoted, as `export_interactive.py`'s docstring already promises.

## 5b. The publication gate — from the pollster review, 2026-08-20

Six blocking items. These are not "would be nice": each is a sentence a hostile
expert can write after the result if it is missing, and the first one is a
sentence that ends a public forecast.

1. **No zero-probability outcomes on the live ballot.** Six backtest columns
   have the truth above every draw, two of them at 7 and 8 seats — Cape Town's
   Cape Coloured Congress and Johannesburg's PA. Before publishing, produce the
   list of every 2026 ballot party with `P(≥1 seat) < 0.02` and defend each by
   name, or widen until it can be defended. *"The model said it was impossible
   and it happened"* would have been writable twice about 2021. Gated on task
   A2.
2. **Calibration quoted on a population fixed before the forecast is made** —
   done, `reference`, §1.56 — with `sd(z)` per band and an interval on it, and
   the direction STATED rather than left to be discovered.
3. **A pre-registered, timestamped, hash-identified forecast** published before
   polling day and never edited after, with the scoring code frozen beside it.
   `artefact_key` and the golden tests are the discipline; they need pointing at
   the public artefact.
4. **The Gauteng / non-Gauteng split disclosed** — done in `history.md`, task
   A7 — and the headline written as *"8 of 9 city-years, 8 of which are one
   election."*
5. **Every claim regenerated from the current model.** Two changes this week
   move the Johannesburg 2026 numbers materially (DA 0.328 → 0.310 from the
   shrink; PA 19.5 → 12.4 seats from deleting `pa_contestation_uplift`).
   Republishing is a decision to take BEFORE a journalist quotes the old number.
6. **The poll section written honestly.** The 2026 register carries essentially
   one independent house (SRF/Victory Research, two waves) with ~500-person
   metro subsamples and an undisclosed likely-voter screen. A single house is a
   level, not a house effect; a ~500 metro cut carries the parent design effect
   on top of its own n. Say how much weight polls carry, on which parties
   (arrivals only), and that the spread across houses is unestimable with what
   exists.

Strongly wanted, not blocking:

* **Both remaining "argued, not tested" mechanisms labelled at the point of
  quotation**, per `CLAUDE.md`. There are now four, not two: `w_bye`, the
  first-local-election bias correction, the contestation correction (which is
  the identity at 2026 — task A4), and the poll path (task A8).
* **A stated failure mode, in the model's own voice.** *"The largest error in
  the 2021 backtest was ActionSA, forecast at 6.3% against 18.1%. A party with
  no electoral record cannot be forecast from a record it does not have. If a
  comparable party emerges in 2026, this forecast will be wrong in the same
  way."* Already true, already measured, and it buys more credibility than any
  item on the model list.
* **Coalition and majority probabilities checked for calibration, not merely
  produced.** A hung-council probability is the number that gets quoted, and it
  is a threshold on a sum — it inherits every width fault amplified.

**And what cannot be fixed with the data held, so must be said rather than
interpolated:** with four cycles, eight metros and one arrival-heavy cycle the
panel cannot identify (a) whether the level shrink is regularisation or a
fragmentation trend, (b) house effects, or (c) the size of an unknown arrival.
Those three are the model's real uncertainty and **none of them is in the
intervals.**

## 6. Order of work

1. **Close the model list.** The successor to §1.55 — a band-dependent
   concentration — is the last thing that can move the score.
2. **One settled run** at 1500 draws produces every published number, and the
   stat tokens regenerate from it. No figure typed into prose.
3. **Port `export_interactive.py`** to emit the pool spec plus the reference
   scenarios.
4. **Build the fidelity gate before the UI.** If the browser cannot reproduce
   the Python answer, nothing else matters.
5. **Then** the UI: sliders for the seven, register status inline, backtest and
   known weaknesses on the face of it.
6. Delete or banner the two frozen artefacts at that point, not before — they
   are the fallback if the port stalls.
