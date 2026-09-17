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

**Since 2026-08-24 that refusal is survivable.** It was a MANDATORY step in
`build_all.py`, ahead of `build_site` and `build_portal`, so the one-command
build died before it reached either — and with them the stat-provenance audits
that only `build_site.py` runs. The interactive steps are now behind
`build_all.py --interactive`, off by default, non-fatal and last. MODEL-LOG
§1.89.

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
previous iteration on history. It had, when this was written (~~254 against 312
a week ago, 8 of 9 against uniform swing~~) — so the gate is passable, but the
model list should be closed first. ⚠️ **Those are NINE-city-year figures and are
struck** (2026-09-13): the panel is twenty-four, the specs were re-emitted on
2026-09-08, and the opponent to headline is now the roster-aware reference and
not plain uniform swing (MODEL-LOG §1.229). **The gate is re-read from the run,
never from this line.**

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

* the backtest, prominently: the coherent seat error against the baselines, how
  many city-years that is, and how many of them share a cycle. ⛔ **The figures
  are NOT typed here** (corrected 2026-09-13): this line used to read "254
  coherent seat error against uniform swing's 376, and that this is nine
  city-years with eight in a single cycle", which was a **nine**-city-year
  reading, superseded at §1.70 (sixteen) and again on 2026-09-02
  (twenty-four) — a publication instruction carrying a three-panels-old number
  is how a stale figure reaches a reader. They go on the page as stat tokens
  from the run, per `CLAUDE.md` §2. ⚠️ **And uniform swing is no longer the
  right opponent to headline**: `benchmarks.uniform_swing_roster` gives the
  reference the same nomination roster the model reads, so it is the honest
  comparison at 2021 and the margin against it is much the smaller one
  (MODEL-LOG §1.229). Two of its panel figures carry an arbitrary tie-break
  band that must be quoted with them — `benchmarks.canonical_order`;
* that ranks 4-12 are under-forecast and the model knows it — ⚠️ the "22.76pp"
  that stood here is a nine-panel figure (§1.36) and is not the current reading;
* that the tail is over-forecast as a *deliberate* trade (§1.54) — ⚠️ likewise
  the "5.60pp": read the band table from the run, do not type it;
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
  the 2021 backtest was ActionSA: the model forecast a small fraction of the
  18.12% it took. A party with no electoral record cannot be forecast from a
  record it does not have. If a comparable party emerges in 2026, this forecast
  will be wrong in the same way."* Already true, already measured, and it buys
  more credibility than any item on the model list.
  ⛔ **THE NUMBER WAS WRONG AND CAME OFF THE WRONG ROW** (corrected 2026-09-13).
  This sentence read *"forecast at 6.3% against 18.1%"*. **6.3% is not the
  model's forecast** — it is the Ipsos-poll conversion in `POLLING.md`, whose
  table puts the model's own Johannesburg figure in the next column at 6.4%,
  while `MACHINERY.md` §"new vs unknown parties" says 6.9% for the same
  quantity. Three numbers, one claim, and the one chosen for publication was the
  one belonging to a different forecaster. **Read it from the run and register
  it as a stat token; do not type it into the sentence.** The realised 18.12% is
  a published election result (`SOURCES.md`) and is the only figure here that
  may be typed.
* **Coalition and majority probabilities checked for calibration, not merely
  produced.** A hung-council probability is the number that gets quoted, and it
  is a threshold on a sum — it inherits every width fault amplified.

**And what cannot be fixed with the data held, so must be said rather than
interpolated:** with four cycles, eight metros and one arrival-heavy cycle the
panel cannot identify (a) whether the level shrink is regularisation or a
fragmentation trend, (b) house effects, or (c) the size of an unknown arrival.
Those three are the model's real uncertainty and **none of them is in the
intervals.**

## 5c. Forecasting before the nomination lists are final

The lists are the one input the live forecast does not have, and they land on
**16 September 2026** — nominations closed 28 August, polling is 4 November. We
are not waiting for them. Two stages, and the discipline is that stage 1 must be
frozen before stage 2 exists, or the revision is indistinguishable from a fit.

### Stage 1 — now, and it already runs

The model does not need the lists to produce a forecast. Where they are absent it
projects each party's slate forward from 2021 (`contestation_expand`, §1.60) and
sizes any unknown newcomer through the generic `ENTRANT` slot. That is a
forecast, not a placeholder.

**Publish it, hash it, and never edit it.** Timestamped, `artefact_key` recorded,
scoring code frozen beside it — publication gate item 3. A forecast issued before
the lists is the only one that can later be shown to have been a forecast.

### The list-dependence is measurable NOW, and should be published with it

⛔ **STRUCK 2026-09-16 — THE TABLE BELOW AND THE "±3 SEATS" SENTENCE UNDER IT ARE
A SUPERSEDED MEASUREMENT AND MUST NOT BE QUOTED OR PUBLISHED.** It was measured
at §1.60 (2026-08-20), on the nine-city-year panel, at 1200 draws, with the poll
channel ON and before the 2026-09-08 and 2026-09-14 re-emits. Every one of those
premises has since moved. **The disclosed judgement call is the lever, not the
seat figure** — `contestation_expand = 0.220`, `JUDGEMENT-CALLS.md` §A5, status
🔴 — and a seat sensitivity is a MEASUREMENT, which belongs in `MODEL-LOG.md`
under the run that produced it, never typed into a publishing instruction. If a
list-dependence band is wanted for the page, re-measure it on the current tree
and quote it as a stat token from that run. Kept, struck, as the record of what
was believed on 2026-08-20.

~~We can say in advance how much the lists can move the answer, because the
channel they act through is a declared lever. Johannesburg 2026, 1200 draws,
median seats across the defensible range of `contestation_expand` (§1.60: the
record's pooled median is 0.220, the most recent cycle alone about 0.5):~~

| | 0.0 *(slates unchanged)* | **0.220** *(shipped)* | 0.5 *(last cycle's rate)* |
|---|---|---|---|
| DA | 83 | 81.5 | 80 |
| ANC | 62 | 61 | 60 |
| **PA** | **17** | **19** | **22** |
| ASA | 25 | 24 | 24 |

~~So the honest statement to publish is: **the nomination lists are worth about
±3 seats to the PA and about ∓2 to the DA, and essentially nothing to anyone
else.**~~ ⛔ **STRUCK 2026-09-16 — see the banner above. Do not publish this
sentence; re-measure or say nothing.** A reader who is told that in August cannot be surprised in September.

### What actually changes on 16 September

| channel | what the lists do | expected movement |
|---|---|---|
| contestation | real slates replace the projection; `contestation_expand` goes inert | the table above, resolved to one column |
| arrival-group spec | `pools.arrival_group_spec` gains a roster and emits for 2026 | **none** — the mechanism is measured worse and stays off (§1.63) |
| phantom entrant mass | we learn who is actually standing, so mass on parties that filed nothing can be withdrawn | unquantified; 11.6 seats across the nine backtest city-years |
| a party we have never seen | a filed newcomer with no baseline | already covered by the generic slot, but by name rather than generically |

### The rule for the revision

Publish stage 2 as a **labelled revision beside stage 1, not over it**: both
visible, both dated, with the difference attributed to the channel that caused
it. If the revision is larger than the band published in August, say so and say
why — that is a finding about the projection, and it is the only out-of-sample
test `contestation_expand` will ever get (it is inert at every backtestable
target, §1.60).

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

---

## 7. The map contradicts the forecast — an equal-area alternative (owner, 2026-08-23)

**The owner's observation, and it is measurably right.** On the geographic ward
map the DA looks dominant because the wards it wins are large and low-density,
while ANC and MK wards are small and dense. Wards are *designed* to hold roughly
equal population, so area carries no information at all — but it is what the eye
reads.

Measured on the committed `ward_winner_probs.csv` and `ward_paths.json`
(135 wards):

| party | wards won | % of seats | % of the map's ink | distortion |
|---|---|---|---|---|
| **ANC** | 66 | **48.9%** | **30.1%** | 0.62× |
| **DA** | 51 | **37.8%** | **61.9%** | **1.64×** |
| MK | 10 | 7.4% | 1.2% | **0.16×** |
| PA | 6 | 4.4% | 5.2% | 1.17× |
| EFF | 1 | 0.7% | 0.3% | 0.43× |
| IFP | 1 | 0.7% | 1.3% | 1.78× |

**Corrected 2026-08-24.** The first version of this table read 30.6 / 61.7 /
1.4 / 4.7 and listed only four parties. Those are each ward's **bounding box**,
reproduced to the decimal — and a bounding box is not what is drawn. The
polygon figures are above; the DA is over-drawn slightly more than was stated,
MK under-drawn slightly more, and the two wards this table used to omit are 1.5%
of the ink. The conclusion is unchanged and the arithmetic was not. MODEL-LOG
§1.90.

The largest ward has **142×** the bounding-box area of the smallest. The median
DA ward is **4.2×** the median ANC ward and **6.6×** the median MK ward.

**So the map shows the DA occupying nearly two-thirds of the visual field while
the forecast has it second on seats.** That is the picture contradicting the
headline, on the same page.

### Options, in order of how well they fit this specific problem

1. **Hex tile cartogram — one equal hexagon per ward.** ★ **BUILT 2026-08-24 —
   `src/hex_cartogram.py`, not yet wired into any page.** See MACHINERY.md and
   MODEL-LOG §1.90. Measured on the emitted figure, every party's ink share now
   equals its seat share to within 1e-9. It is a second map, not a replacement,
   exactly as recommended below; the page needs a
   `__HEXMAP_START__`/`__HEXMAP_END__` marker pair and a toggle, and neither
   exists yet.
   135 hexes, each ward snapped to the nearest free cell on a hex grid by
   minimising total displacement from its real centroid. Honest by construction
   here, because **one ward returns exactly one councillor** — equal area is not
   a distortion of the truth, it *is* the truth about representation. Used by the
   FT, BBC and Guardian for UK constituencies for the same reason.
2. **Dorling cartogram** — equal circles (or circles sized by registered voters)
   repelled apart. Keeps rough position, loses shape and adjacency. Easier than
   hexes, uglier.
3. **Contiguous (Gastner–Newman) cartogram** — warp the real boundaries until
   area ∝ voters. Keeps recognisable geography; hardest to implement and can look
   grotesque at 135 units.
4. **Ward strip** — 135 equal tiles sorted by margin, not by geography. Abandons
   place entirely but shows the competitive middle better than any map.

### The recommendation, and the reason it is not simply "replace the map"

**Show both, side by side or on a toggle, and print the distortion figure
between them.** Geography answers *where*; the cartogram answers *how many*. A
reader who only sees the cartogram loses the real fact that the DA's support is
spatially concentrated in the north — which is true, and interesting, and not a
distortion.

And the 1.63× / 0.63× table above is **publishable content in its own right**: it
is a genuinely interesting fact about Johannesburg that most maps of it hide.

**Implementation note.** `src/render_map.py` already computes ward centroids and
writes an inline SVG between `__MAP_START__`/`__MAP_END__`. A hex layout is an
assignment problem over those centroids and needs no new data. This is
presentation work and belongs in this file, not on the model list.

**Still open on this item**, now that the cartogram itself exists:

* the toggle, and the marker pair on whichever page carries it;
* the distortion table as **stat tokens** in `content/joburg/stats.toml` — it is
  publishable content in its own right and must not be typed into prose. There
  is no emitter for it yet; `hex_cartogram.ink_table` returns the numbers.
* **`render_map.py`'s party key omits MK**, which wins 10 wards in this
  forecast. Its swatch list is `("ANC", "DA", "EFF", "ASA", "PA", "IFP",
  "ALJAMAAH")`. The cartogram's includes MK. One line, for whoever next holds
  that file — it was left alone because re-running `render_map.py` rewrites
  `forecast-sheet.html`.

## 8. The publication convention — agreed with the owner 2026-09-17, and to be DONE

The owner, on agreeing: *"make a note and to do actions lest it's something we
agree on enthusiastically and then do not do!"* This section is that note. It
is presentation only and never a reason to change a forecast (`CLAUDE.md` §1).

**The convention**, taken from forecasting and news practice (FiveThirtyEight,
The Economist, Silver Bulletin, newsroom correction policy). No polling standard
prescribes it; AAPOR's transparency code covers disclosure, not revision:

1. **Live data** (tiles, tables, map) is always CURRENT and shows its HISTORY:
   an arrow and a "was X on <date>" tooltip taken from the publication ledger.
2. **Written pieces** (headlines, commentary, tested claims) are FROZEN as
   published and dated. When their figures move materially they get an
   appended, dated **"Since then (<date>):"** note with today's figures, and the
   original is never rewritten.
3. **An update is not a correction.** In an update the model or the world moved
   and the piece was true on its date. In a correction the piece was wrong when
   published. A correction carries a visible **"Correction:"** label and goes
   on a public corrections list.

**To do** (task list, 2026-09-17):
- [ ] Arrows and "was X on <date>" tooltips on every live figure, from
      `changes.json`/ledger. Blocked on moving script-written figures to
      build-time token spans first, since the scripts currently bypass the ledger.
- [ ] A reusable, token-driven "Since then" block. First use: the Zille claim,
      keeping the 7 August prediction and adding today's answer.
- [ ] A "Correction:" label and a public corrections list. First entries: the
      live 31 August page's "just 7 list seats" (median total minus mean wards)
      and "Smaller parties — 39 seats" (medians summed as if additive).
- [ ] The headline archive and headline-change announcements use this same
      record. Every send needs owner approval.
- [ ] A build check: a frozen piece whose tokens moved materially must carry a
      Since-then note, or `--publish` refuses.
