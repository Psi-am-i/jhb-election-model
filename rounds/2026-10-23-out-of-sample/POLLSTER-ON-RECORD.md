# Pollster on the record: backtest settings and out-of-sample scores

> ⛔ **Every backtest figure dated before 2026-10-23 is in-sample and is not evidence of forecast accuracy.** Several of the model's settings were chosen on records that include the elections scored (this note). The scores were withdrawn from the site on that day (MODEL-LOG §1.333).

**Date:** 2026-10-23
**Reviewer standpoint:** election forecaster and survey methodologist (the `pollster` skill). Read-only review; nothing in the model was run for this note.

**The owner's question, verbatim:**

> Is it how forecasts are meant to work to publish backtest scores from settings chosen with the results of the elections being scored (or later ones), and to keep those settings?

Then: (1) which exceptions, if any, the forecasting and polling literature accepts, and whether the census exception is one; (2) for each setting, what a correct out-of-sample treatment is, and what to do when there is too little earlier data; (3) how model-selection decisions (the switches) should be handled so the published score is honest; (4) what should happen to the scores already published.

**Evidence read:** `src/backtest.py` (the four provenance registers), `src/montecarlo.py` (`TURNOUT_CORRELATION`, `compress_levels`), `src/levels.py` (`SPINE_K` and the module docstring), `config/dimensions.toml` (census entries), `src/pools.py` (`composition_at`), `content/joburg/stats.toml` (which backtest figures are published), and `MODEL-LOG.md` §1.44, §1.55, §1.63, §1.225. Numbers below are quoted from those sections, each with its panel, draw count and section. "Coherent seat error" is the project's summed absolute seat error across all parties, with seats allocated from one consistent vote vector; half of it is the number of seats given to the wrong party. Citations are from memory; confidence is stated for each in the source list at the end.

---

## The answer

**No.** A score computed with settings that were chosen while looking at the results being scored is an in-sample fit. Publishing it as a backtest, or as evidence of how accurate the forecast will be, overstates the model's skill. The forecasting literature is uniform on this (Tashman 2000; Hyndman & Athanasopoulos 2021; Cawley & Talbot 2010; Lauderdale & Linzer 2015 for election models specifically). The owner's own rule, that a backtest may use only data from before the election, is the standard rule.

**Keeping the settings is a separate question, and for the 2026 forecast the answer is yes.** Every one of these settings was chosen on data from 2021 or earlier, and the election being forecast is 4 November 2026. Using all available history to set the parameters of a live forecast is correct practice. What is wrong is the label on the backtest scores, not the live forecast's use of the settings.

So the two halves are:

| | Verdict |
|---|---|
| Publishing the current backtest scores as out-of-sample accuracy | Not acceptable. They are in-sample for every setting fitted on the scored elections. |
| Using the current settings in the 2026 forecast | Acceptable. 2026 post-dates all data they were chosen on. |
| What has to change | How the backtest computes its settings (per target, from strictly earlier data), and how the existing scores are labelled. |

**The comparison with uniform swing is affected more than the absolute scores.** Uniform swing has no fitted parameters, so it cannot leak. A model whose settings saw the answer, scored against a baseline that did not, has its margin over the baseline overstated specifically. The figures of this kind on record are "beats uniform swing in 8 of 9" (§1.44, nine city-years, 1500 draws, with the level shrink on) and "margin over uniform swing 18.3%" (§1.225, 24 city-years, 1000 draws, polls off). The site publishes the same kind of comparison (`backtest_wins`, `backtest_crps_better` and the per-metro CRPS table in `content/joburg/stats.toml`).

### Three kinds of contamination, which are not equally serious

The settings in the owner's table fall into three classes. Treating them alike would either overstate or understate the problem.

| Class | What happened | Seriousness | Settings in this class |
|---|---|---|---|
| **Fitted on the scored results** | The value was estimated from, or optimised against, the elections being scored. | Full in-sample. The score is not out-of-sample for any row the fit saw. | Level shrink 0.35 and scale 0.04; turnout correlation 0.63; spine k = 1.0 if its fit reached 2016→2021 (unsettled) |
| **Typed, then confirmed by a sweep on the panel** | A value was written down, a sweep on the panel was run, and the value was kept because alternatives did not score better. | Weaker. The value was not moved by the panel, but it survived a test on the panel, so the published score is the best of the options tried. Not validation; not full re-selection either. | New-party chance 0.25 and size range; Dirichlet scale 1.0; arrival-group draw off; the values of ward noise (sd 0.10) and of the level floor (1e-6) |
| **Chosen on a mechanism argument** | The setting fixes a defect in the machinery, and the reason does not depend on any score. | Not a leak, even if it was measured on the panel afterwards. | Polls off (an owner design decision, §1.225); the *existence* of ward noise and of the separate level floor. Their *values* belong in the second class (see §3). |

One caution on typed values. A value typed by someone who already knew the 2011, 2016 and 2021 results is not a value that read no result. The new-party chance of 0.25 sits in this position: it is typed from the plan, but the plan was written by people who knew that the NFP (2011), the AIC (2016) and ActionSA (2021) had arrived (register note, `FITTED_ON_UNINSTRUMENTED["entrant_prob"]`). The literature calls this researcher degrees of freedom (Simmons, Nelson & Simonsohn 2011) or the garden of forking paths (Gelman & Loken 2013).

---

## (1) Exceptions the literature accepts, and the census

### What is accepted

**Ex-post or conditional forecasts, if labelled as such.** The forecasting texts separate an *ex-ante* forecast, which uses only what was known at the forecast origin, from an *ex-post* forecast, which feeds in the realised values of explanatory variables but still withholds the outcome (Hyndman & Athanasopoulos 2021, the ex-ante and ex-post forecasts section; Armstrong 2001; Clements & Hendry 1998 on conditional forecasting). Ex-post evaluation is accepted as a test of a model's *structure*: given the right inputs, does the mechanism produce the right outcome? It is not accepted as a measure of *forecast accuracy*, because the forecaster will not have those inputs on the day. The condition is that it is labelled ex-post wherever the score appears.

**Information that is public before polling day, even if it ships in the results file.** This one is not an exception. It is ordinary pre-election data. The model already treats two inputs this way, correctly: ballot presence by ward (nomination lists close weeks before polling day, `FITTED_ON["contestation"]`) and registration on the certified roll. Both are known to a real forecaster before the vote.

**Data vintages.** The real-time data literature (Croushore & Stark 2001) shows that evaluating a forecast with later, revised data rather than the vintage available at the time can change conclusions materially. The accepted practice is to use the vintage that existed at the forecast origin, and where that is impossible, to say so and measure the difference where any earlier vintage exists.

### What is not accepted

- Parameters estimated or tuned on the scored outcomes (the first class above).
- Choosing a model form or a switch by comparing scores on the same elections later reported as the test.
- Leave-one-out within one election cycle presented as out-of-sample. The eight metros at 2021 share one national swing (the ANC's fall, ActionSA's arrival everywhere at once), so a fold that holds out one 2021 metro still trains on seven others from the same cycle. The literature on cross-validation with structured data says folds must be blocked on the dependence: here, by cycle (Roberts et al. 2017; Bergmeir, Hyndman & Koo 2018 for the time-series case).

### Whether the census exception is one

**Yes, in kind: it is an ex-post covariate, which is an accepted class when labelled.** The owner's reasons are a reasonable argument for it: the census supplies only each ward's population-group split, is taken roughly once a decade, and is a covariate rather than an outcome.

**It is not a measured exception, and it is not free.** Three points:

1. **Census 2022 composition embeds migration that happened after the earlier targets**, and migration correlates with vote change. Wards that grew fastest between 2011 and 2022 (informal settlements, new suburbs in Gauteng) are also where turnout and party shares moved. A covariate measured after the target carries some of the target's change inside it. How much is an empirical question.
2. **The backtest's census lag differs from the live forecast's.** `config/dimensions.toml` holds one census, 2022, with its shares held flat for every election. So relative to the census, the 2011 target is 11 years earlier, 2016 is 6 years earlier, 2021 is 1 year earlier, and the live 2026 forecast is 4 years later. At the 2021 target the backtest has near-contemporaneous ward composition, which is better information than the 2026 forecast will have. The honest analogue of the live forecast is a census some years *before* the target.
3. **The measurement that would bound it is not available yet.** Census 2011 ward tables are not held (`config/dimensions.toml`: the 2011 entry is commented out as "not held", and obtaining it is called "the highest-value outstanding data request after home language"). With Census 2011 on the 2011 delimitation, the 2016 and 2021 targets could be re-run on it (joined through voting districts, as `pools.composition_at` already requires across delimitations) and compared with the Census 2022 runs. If the difference is inside draw noise, the exception is justified by measurement. If it is not, the size of the difference is the size of the leak. Until then, the census exception is argued, not tested, and should be labelled that way.

There is also an undercount question in Census 2022 that I recall Stats SA's post-enumeration survey put at roughly 31% nationally. I am not certain of the figure. If the undercount differs by population group, the composition is biased in a direction unrelated to timing. That is a data-quality matter for `DATA-QUALITY.md`, separate from the out-of-sample question.

---

## (2) Correct treatment for each setting

### The general method: rolling origin, blocked by cycle

For each target year T, every fitted setting is recomputed using only elections strictly before T. This is evaluation on a rolling forecasting origin (Tashman 2000; Hyndman & Athanasopoulos 2021). On this archive:

| Target | Local elections available before it | Earlier backtest rows available for tuning-type settings |
|---|---|---|
| 2011 | 2000, 2006 (files on disk for all eight metro codes; Buffalo City and Mangaung were not metros before 2011) | none |
| 2016 | 2000, 2006, 2011 | the eight 2011 rows |
| 2021 | 2000, 2006, 2011, 2016 | the eight 2011 rows and the eight 2016 rows |

The project already does this in one place. `src/width_record.py` fits the universal draw's widths for each target on strictly earlier cycles (2016 on 2011, 2021 on 2011–2016), per the `NOT_FITTED["draw_law"]` entry. That is the template for every row below.

**When there is too little earlier data**, the standard fallback has three parts, used together:

1. **A declared prior, written down before the run** and filed in `JUDGEMENT-CALLS.md` with the reason. The neutral choice is usually the identity (the setting off) or a value from outside the panel.
2. **Bracketing sensitivity arms** at the defensible extremes, reported beside the main result, so the reader sees how much the undeclared choice could matter.
3. **The row labelled** as using a declared setting, not a fitted one.

For the 2011 rows this will often be the only option. Whether 2011 rows then enter the headline or are reported separately is the owner's choice; both are defensible if labelled. My recommendation is a headline on the 16 rows at 2016 and 2021, forward-chained, with the 8 rows at 2011 reported beside it as "settings declared, not fitted".

### Row by row

| Setting | What it was chosen on | Correct treatment | When earlier data is too thin |
|---|---|---|---|
| **Census 2022 ward composition** | the 2022 census, after every past target | Keep as a labelled ex-post covariate. Obtain Census 2011 ward tables and re-run the 2016 and 2021 targets on them; the difference is the measured size of the exception. | At 2011 the only earlier census is 2001, on different boundaries. Keep 2022, labelled ex-post, or drop the 2011 rows from the headline. |
| **Turnout correlation 0.63** | 14 metro-transitions, 2011→2016 and 2016→2021 (`montecarlo.py` comment) | Recompute per target from transitions strictly before it: at 2021, the 2011→2016 transitions; at 2016, the 2006→2011 transitions; at 2011, 2000→2006. The register already schedules this (`FITTED_ON_UNINSTRUMENTED["turnout_correlation"]`). | Boundary changes before 2011 (Tshwane's absorption of Metsweding; Buffalo City and Mangaung becoming metros) may leave too few comparable transitions at 2011. Then declare a value and bracket it with arms at 0 (independent groups) and 1 (one shared turnout move). |
| **Level shrink 0.35, scale 0.04** | Johannesburg 2016 and the eight 2021 metros: leave-one-out for the value, and the form and the scale chosen with all nine in view (§1.44) | Rolling origin, and the form choice goes inside the loop too. For 2021 rows: choose among the four forms and fit the strength and scale on the 2011 and 2016 rows only. For 2016 rows: fit on the 2011 rows only. | At 2011 there are no earlier backtest rows to tune on. Set the shrink to 0 (the identity), declared, and show an arm at the current value as a sensitivity. |
| **Spine k = 1.0** | the `levels.py` docstring says "180 party-city-years across eight metros and three transitions"; kept after a sweep on 16 backtests | First settle the provenance (see below). If it reached 2016→2021, refit per target. The plateau reported in `levels.py` (0.2377, 0.2358, 0.2387 at k = 0.5, 1.0, 1.5; the docstring gives no unit, and from context I read it as a root-mean-square error in log share) suggests the leak is small, but that plateau was measured on the data in question, so it has to be re-measured forward-chained, not argued. | k is a weight between two routes; at 2011, with one earlier local transition, declare k = 1.0 (routes equal at one unit of evidence) and bracket at the ends of the plateau. |
| **New-party chance 0.25 and size range** | typed from the plan, kept after a sweep on 9 backtests (coherent seat error 254 / 262 / 264 at 0.25 / 0.290 / 0.353, register note) | Derive the arrival base rate from arrivals strictly before the target. For 2011 that is the 2000 and 2006 local elections plus the 2004 and 2009 national elections (COPE's 2009 arrival is in that window). | The pre-2011 record is a handful of arrivals. Declare the value as a judgement, written before scoring, and bracket it. Note that only the 2011 rows use it, so it affects at most 8 of 24 rows. |
| **Slate growth 0.22** | slate changes up to 2016→2021 | Make it target-aware for consistency, but it is not read in any test draw (`levels.projected_contestation` is never called where real lists exist), so it does not touch any published score. | No score action needed. |
| **Dirichlet scale 1.0** | a sweep on 9 backtests (§1.55: kept at the fitted 1.0 although 2.0 scored better on CRPS) | Not read by the current draw method, so it touches no published score. §1.55's decision not to adopt 2.0 was the correct one on these grounds. | If the key is truly unread, remove it from the register as inert or mark it inert; carrying a contamination entry for an unread constant reports a risk that does not exist. |

### Spine k: what I could and could not settle

`src/backtest.py` files spine k under `PROVENANCE_UNSETTLED` because two comments disagree. I looked for the fitting code and found none in `src/`: `levels.SPINE_K = 1.0` is a literal, the output of a one-off analysis described in the `levels.py` docstring. "Three transitions" on an archive holding the 2000, 2006, 2011, 2016 and 2021 local elections most plausibly means 2006→2011, 2011→2016 and 2016→2021, which would include the 2021 result. That is my reading of the docstring, not a verified fact. The way to settle it is to write the fit as code that takes the target year, run it per target, and see whether k moves.

---

## (3) Model-selection decisions: the switches

The switches (polls off, arrival-group draw off, the draw method, ward noise, the level floor) are part of the fitting procedure. A choice between options made by comparing scores is a parameter estimate with a discrete range, and the literature treats it as such. Selecting on the test set and then reporting the test score is the specific error that nested cross-validation exists to prevent (Varma & Simon 2006; Cawley & Talbot 2010; Hastie, Tibshirani & Friedman 2009, the "wrong and right way to do cross-validation" section).

### The rule that makes the published score honest

1. **Classify each switch by the reason it was set**, not by whether it was measured. A switch set on a mechanism argument is not a leak. A switch set because one arm scored better on the panel is.
2. **Score-chosen switches go inside the rolling origin**: the choice for 2021 rows is made on the 2011 and 2016 rows, the choice for 2016 rows on the 2011 rows. Where no earlier rows exist (2011), the switch takes a value declared before scoring.
3. **Record how many alternatives were tried for each decision.** The best of many tries on one panel is optimistic in proportion to the number of tries (White 2000; Bailey, Borwein, López de Prado & Zhu 2014). `MODEL-LOG.md` already records the arms; the count belongs beside each published score.

### Applied to each switch

| Switch | Reason it was set | Class | Treatment |
|---|---|---|---|
| **Polls off** | Owner design decision to pull polls out pending a redesign (§1.225, quoted there), pre-registered before both arms ran. Measured effect: coherent seat error 725 on, 723 off, on 24 city-years at 1000 draws, which §1.225 states is not distinguishable from zero. | Mechanism/design | This is the correct pattern: decision on grounds independent of the score, pre-registered, measured afterwards. Keep it off at every target and say so. |
| **Arrival-group draw off** | Never reachable before §1.63; once repaired and swept on nine city-years, coherent seat error was 254 off and 348 on, worse in 6 rows and better in 1 (§1.63). | Confirmed by the panel | "Off" was the state before any evidence, because the switch did not exist. The panel confirmed it. A forward check was impossible: the evidence came from 2021 rows only, and Johannesburg 2016 had no spec. Treat as a declared setting at every target. The effect is far outside draw noise of ±2 to ±4 seats (§1.44), so the leak in the published score from this choice is small relative to the choice itself. |
| **Draw method** | The universal draw was adopted over the incumbent by comparing arms on the panel; its widths are fitted per target on earlier cycles. | Score-chosen (the law), forward-fitted (the widths) | The widths are already correct. The choice of law was made with the 2016 and 2021 rows in view, so the forward-chained run must choose it on earlier rows only, or declare it and label the score. |
| **Ward noise** | Existence: audit finding that ward winners were deterministic given a citywide draw, which overstated the chance of overhang (`NOT_FITTED["ward_noise_sd"]`). Value: sd 0.10, "typed at 0.10 on an audit, never measured and never bounded" (`JUDGEMENT-CALLS.md` §A38), adopted 2026-08-06 because "the audit suite showed headlines stable" (`montecarlo.py` comment beside `DEFAULTS`). | Mechanism for the switch; typed then confirmed on the panel for the value | Keep the switch. Declare the value before the forward-chained run and bracket it. |
| **Level floor** | Existence: audit finding that the share floor made levels below 0.2% unreachable and inflated the micro-party tail (`NOT_FITTED["level_floor"]`). Value: 1e-6, adopted 2026-08-06 with the note "structural rows barely move" (`montecarlo.py`), recorded as §F19 in `JUDGEMENT-CALLS.md`. | Mechanism for the switch; typed then confirmed on the panel for the value | Keep. A floor of 1e-6 is a numerical guard rather than a modelling choice, so the leak through its value is likely negligible; declare it and move on. |

**Where this departs from the owner's table.** The owner's table lists all five switches as "chosen by comparing scores on these same backtests". On the register's evidence that is true of the draw method, true in the weaker confirming sense of the arrival-group draw and of the ward-noise and level-floor *values*, and not true of polls off or of the decision to *have* ward noise and a separate level floor, which rest on defects in the machinery found by audit. The difference matters because a mechanism fix does not need to go inside the rolling origin; a score-chosen value does.

### The selection no per-setting fix removes

The model has been developed by more than two hundred iterations, each judged by "does the backtest against real results improve?" (`CLAUDE.md` §1, `ITERATING.md`). Every structural change kept for scoring better on the panel is a selection on the panel. Refitting each constant per target removes the leak from the constants; it does not remove the leak from the choice of model structure, which was made with all 24 rows in view. This is the specification-search problem (Leamer 1983) and the reason Lauderdale & Linzer (2015) argue that election models refined on a small set of past elections understate their own error.

**The only remedy is data the model has not seen, and there is one: the 2026 local election on 4 November 2026.** The standard procedure (the forecasting competitions' sealed hold-out, Makridakis & Hibon 2000; pre-registration, Nosek et al. 2018) is:

- freeze the code, the settings and the emitted specs before polling day;
- publish a hash of the frozen state, dated, before polling day;
- score that frozen forecast against the certified result, and publish the score whatever it is.

That number will be the first out-of-sample accuracy figure this model has. It is one city-year per metro, so it will be noisy; it is the only one that is clean.

---

## (4) What should happen to the scores already published

1. **Relabel them now, without deleting them.** The site's backtest figures (in `content/joburg/stats.toml`: `backtest_wins`, `backtest_crps_better`, the per-metro CRPS table, and the home page's count of wards whose winner the backtest called) should say that some settings were chosen with these elections' results, so the figures describe fit to past elections and not forecast accuracy. Under the project's correction convention, the correction says what was wrong (these were described as tests on past elections using only earlier data; some settings were chosen on those elections) and what changed, and nothing else.
2. **Compute the forward-chained panel and publish it beside the old figures.** The gap between the two is the measured optimism of the in-sample scores. Publishing both is more informative than replacing one with the other, and a reader can see the size of the problem instead of being told about it.
3. **Keep the current settings in the 2026 forecast**, but produce them by the same per-target procedure run with all data through 2021, so the live forecast is the last step of the forward chain rather than a separate artefact. Where the procedure returns the current values (turnout correlation 0.63 is already estimated through 2021), nothing moves.
4. **Freeze and publish the 2026 forecast's hash before 4 November 2026**, and after the result, publish the score of the frozen forecast as the out-of-sample figure.
5. **Label the census exception** on the site and in the scoreboard as an ex-post covariate, argued and not yet measured, until the Census 2011 comparison exists.

---

## Claims considered and rejected

| Claim | Why it is rejected | Evidence |
|---|---|---|
| Leave-one-city-year-out over the nine city-years makes the level shrink out-of-sample | Eight of the nine rows are one cycle, so every fold trains on the held-out row's own national swing. Choosing 0.350 in all nine folds is what one dominant cycle would produce, so fold stability is not evidence of transfer. | §1.44 panel composition (Johannesburg 2016 plus the eight metros at 2021) |
| The level shrink has no forward evidence at all | Rejected in the other direction. Fitted on Johannesburg 2016 alone (strength 0.375) and applied to the eight 2021 metros, it improved 6 of 8 and took reconstructed seat error from 284 to 258 (§1.44, offline screen on cached mean vectors). That is a forward test. Its limits: the functional form was chosen with the 2021 rows in view, and the figure is the offline reconstruction, not a full model run. | §1.44 |
| A typed constant read no result | Not when the person typing it knew the results. | `FITTED_ON_UNINSTRUMENTED["entrant_prob"]` |
| A sweep that left a value unchanged validates it | It shows the value was the best of the options tried on the panel, which is selection with a null outcome. Weaker than fitting; not validation. | §1.55 (Dirichlet scale), register note on new-party chance |
| The census is safe because it is a covariate, not an outcome | A covariate measured after the target carries post-target migration, which correlates with vote change; and the backtest's census lag (1 to 11 years ahead of the target) differs from the live forecast's (4 years behind). Untested until Census 2011 ward tables are held. | `config/dimensions.toml`, `pools.composition_at` |
| The settings must be removed from the 2026 forecast | 2026 post-dates every election they were chosen on. Using all history for a live forecast is correct. | Dates in the owner's table |
| The flat plateau in spine k means its leak is harmless | The plateau was measured on the data whose use is in question. It has to be re-measured with per-target fits. | `levels.py` docstring |

---

## Sources, with my confidence in each citation

| Source | Used for | Confidence |
|---|---|---|
| Tashman, L.J. (2000). Out-of-sample tests of forecasting accuracy: an analysis and review. *International Journal of Forecasting* 16(4). | Rolling-origin evaluation as the standard | High |
| Hyndman, R.J. & Athanasopoulos, G. (2021). *Forecasting: Principles and Practice*, 3rd ed. OTexts. | Time-series cross-validation on a rolling origin; ex-ante vs ex-post forecasts | High |
| Armstrong, J.S. (ed.) (2001). *Principles of Forecasting*. Kluwer. | Ex-ante testing as the standard for accuracy claims | Medium on the exact wording |
| Clements, M.P. & Hendry, D.F. (1998). *Forecasting Economic Time Series*. Cambridge. | Conditional forecasting | Medium |
| Croushore, D. & Stark, T. (2001). A real-time data set for macroeconomists. *Journal of Econometrics* 105(1). | Data vintages change forecast evaluations | High |
| Varma, S. & Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. *BMC Bioinformatics* 7:91. | Nested validation for selection | High |
| Cawley, G.C. & Talbot, N.L.C. (2010). On over-fitting in model selection and subsequent selection bias in performance evaluation. *Journal of Machine Learning Research* 11. | Selection on the test set biases the reported score | High |
| Hastie, T., Tibshirani, R. & Friedman, J. (2009). *The Elements of Statistical Learning*, 2nd ed., §7.10.2. | The wrong and right way to do cross-validation | High |
| Roberts, D.R. et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* 40(8). | Blocking folds on the dependence structure | High |
| Bergmeir, C., Hyndman, R.J. & Koo, B. (2018). A note on the validity of cross-validation for evaluating autoregressive time series prediction. *Computational Statistics & Data Analysis* 120. | When ordinary cross-validation is and is not valid for time-ordered data | Medium-high |
| Leamer, E.E. (1983). Let's take the con out of econometrics. *American Economic Review* 73(1). | Specification search | High |
| White, H. (2000). A reality check for data snooping. *Econometrica* 68(5). | Best-of-many optimism | High |
| Bailey, D.H., Borwein, J.M., López de Prado, M. & Zhu, Q.J. (2014). Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. *Notices of the AMS* 61(5). | Backtest overfitting grows with the number of trials | High |
| Simmons, J.P., Nelson, L.D. & Simonsohn, U. (2011). False-positive psychology. *Psychological Science* 22(11). | Researcher degrees of freedom | High |
| Gelman, A. & Loken, E. (2013). The garden of forking paths. Working paper; published form in *American Scientist* (2014). | Choices made after seeing the data | High |
| Lauderdale, B.E. & Linzer, D.A. (2015). Under-performing, over-performing, or just performing? The limitations of fundamentals-based presidential election forecasting. *International Journal of Forecasting* 31(3). | Election models refined on few past elections understate their error | High |
| Makridakis, S. & Hibon, M. (2000). The M3-Competition. *International Journal of Forecasting* 16(4). | Sealed hold-out as the accepted evaluation design | High |
| Nosek, B.A. et al. (2018). The preregistration revolution. *PNAS* 115(11). | Pre-registration before the outcome is known | High |
| Gneiting, T. & Raftery, A.E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA* 102(477). | CRPS as a proper score for the headline | High |
| Stats SA, Census 2022 post-enumeration survey | Census 2022 undercount of roughly 31% | Low on the figure; check before citing |
