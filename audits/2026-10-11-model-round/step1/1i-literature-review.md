# 1i. How other multiparty forecasts represent vote-share uncertainty: literature review

Read-only research for the 2026-10-11 model round. Nothing in `src/` or `data/`
written; no model run, no `compare_history`, no emit; no sub-delegation. Sources
were read on 2026-10-12 through web search and the full texts where they could be
downloaded (PDF text extracted in the session scratchpad, `lit/`). Every source is
in the table at the end with its URL and year. Quotes are at most 15 words.

Labels: **cited** = stated in the named source; **argued** = this review's
reasoning, not stated by any source; **measured** = a number from this round's
audits (`1f-randomness-consistency-audit.md`, `1b-small-party-design-v3.md`,
`1h-plausibility-check-design.md`), quoted by pointer.

**The owner's question.** If the uncertainty mechanism produces error across the
whole size range, is a fix applied below 5% a bandage on a more fundamental
problem, and how do other models handle it?

---

## 1. How published multiparty forecasts represent vote shares

### 1.1 The families in use

| family | how it works | who uses it for elections | cited weakness |
|---|---|---|---|
| Dirichlet (one concentration) | shares ~ Dir(φ·μ); every party's variance is μ(1−μ)/(φ+1) for one φ | Stoetzer et al. 2019 and the Zweitstimme model (fundamentals part only); Hanretty 2021 (UK by-elections); Bauer et al. 2018 (KOALA, poll sampling only) | ratios of components independent (Aitchison, via Katz & King 1999 and Hanretty 2021); one parameter sets the whole covariance (Elfadaly & Garthwaite 2013) |
| Dirichlet-multinomial | the Dirichlet as the prior on a multinomial count | KOALA (Bauer et al. 2018); Zweitstimme poll likelihood | as above; Selb & Chen 2023 name its lack of per-party variances as the reason they did not use it |
| generalised Dirichlet (Connor-Mosimann) | stick-breaking with a separate Beta per stick; about twice the parameters | no election forecast found | order-dependent; harder to handle with many categories (cited, Stan forum, anecdotal) |
| additive logistic normal / Student-t (log-ratio Gaussian or t with a full scatter matrix) | log(v_j / v_ref) ~ multivariate normal or t, mapped back to the simplex | Katz & King 1999 (district-level UK, t); Stoetzer et al. 2019 and Zweitstimme 2021 (latent poll state: log-ratio random walk with a full evolution covariance); Garcia Montalvo et al. 2019 (Spain, multivariate Gaussian poll errors with learned cross-party correlation) | no support at zero; results depend on the reference party unless the covariance is full; a free covariance has (P−1)P/2 parameters |
| logit / multinomial-logit with party-specific variance | each party's log or logit share gets its own variance term; inverse multinomial link closes the composition | Selb & Chen 2023 (German polls); Shirani-Mehr et al. 2018 (two-party, logit); Linzer 2013 (two-party, logit random walk) | identification needs a reference or sum-to-zero; per-party variances need data per party |
| multilevel regression and post-stratification (MRP) | multinomial model of individual vote with area and demographic effects | Lauderdale et al. 2020 (YouGov, UK and US); Garcia Montalvo et al. 2019 (fundamental model) | needs survey microdata; not a model of election-to-election movement |
| swing rules | uniform (add the same points everywhere), proportional (multiply), or Electoral Calculus's strong transition model (declining parties fall multiplicatively) | UK seat projections | uniform swing can go negative for small parties; proportional swing has no clear empirical advantage in the UK (Pack 2010) |

### 1.2 What each source says, in its own words (cited)

- **Aitchison's critique of the Dirichlet**, as relayed by Katz & King (1999):
  Dirichlet models "require the ratios of 'compositions' ... to be independent".
  Aitchison's remedy was a normal distribution on the log-ratios. Hanretty (2021)
  repeats it: the Dirichlet was deprecated because components are independent
  conditional on covariates.
- **Katz & King (1999)**, the founding multiparty electoral-data model, reject both
  the Dirichlet and the logistic normal. They find most districts more clustered
  and a minority more dispersed than a normal implies, and adopt the **additive
  logistic Student-t** with a full (J−1)×(J−1) scatter matrix and small estimated
  degrees of freedom. They also insist that
  electoral zeros are structural: a party that does not stand is information, not
  a rounding error.
- **Stoetzer, Neunhoeffer, Gschwend, Munzert & Sternberg (2019)** use a Dirichlet
  regression for the fundamentals forecast, then set the forecast equal to "the
  log-ratio transformed values" of a latent poll state, which evolves as a random
  walk with a full evolution covariance (SPD as reference). Small parties are
  pooled into "others". The 2021 Zweitstimme note adds that election-day forecasts
  "from the dynamic process alone were overconfident", corrected by "adding
  additional error variation to the forecast of each party".
- **Selb & Chen (2023)**, 5,240 German polls, model each party's log share with its
  own variance and say why they did not use a Dirichlet: "we can estimate separate
  variances for each party." Average absolute bias differs by party in points, but
  "these differences lessen" relative to party size.
- **Hanretty (2021)**, UK by-elections, uses a Dirichlet regression with one
  precision φ "the same for all components". He had to choose a prior on φ so
  that small parties have a non-zero chance of keeping a deposit, and notes φ can
  be modelled with covariates (per contest, still one value across parties).
- **Elfadaly & Garthwaite (2013)**: the Dirichlet "is not flexible enough to
  represent a broad range of prior information."
- **Gelman, Hullman, Wlezien & Morris (2020)**, on the 2020 US forecasts: a model
  whose cross-state covariances are too low must make each state's uncertainty
  too wide to get the national width right; low correlation also arises from
  adding "independent state errors with a long-tailed distribution".
- **Heidemanns, Gelman & Morris (2020)** (The Economist) build the between-state
  correlation matrix from past results and demographics, then by "setting negative
  correlations to zero, then adding a constant" to all elements.

### 1.3 The Dirichlet's size law, from its moments (cited formula; argued reading)

A Dirichlet with concentrations α_i, α_0 = Σα_i has marginal X_i ~ Beta(α_i,
α_0 − α_i), variance α_i(α_0 − α_i)/(α_0²(α_0 + 1)), and every covariance negative
(Wikipedia, Dirichlet distribution). With mean p = α_i/α_0, the relative standard
deviation is √((1−p)/(p(α_0+1))), approximately 1/√(α_i) for a small party. When
α_i < 1 the Beta density is unbounded at zero.

Read against this model (argued): the within-pool split gives a member with a
small cell α_i = A_g × cell share far below 1, so its draw is a spike at zero plus
rare large draws. 1f §2.2 and §2.3 measure exactly this (median draw of a 0.1-0.3%
party 0.035× its centre on the panel; realised median 0.84×). The 1/√p law is the
law of multinomial sampling noise, which is why the Dirichlet is the correct tool
in KOALA, where the only uncertainty is a poll's sample. Election-to-election
movement does not follow it: 1f §4.1's record log-sd rises from 0.21 (≥ 15%) to
about 0.8 at 2-5% and then stays between 0.68 and 0.90 down to < 0.05%. A 1/√p law
from 20% to 0.1% would multiply the sd by about 14; the record multiplies it by
about 4, nearly all of it above 2% (derived from 1f §4.1, measured).

### 1.4 Small parties and "others" (cited)

Every national multiparty forecast found handles small parties by pooling them:
Stoetzer et al. ("others" as the combined share of all remaining parties),
Hanretty 2021 ("all other" parties, including UKIP and the Greens), the Economist
and FiveThirtyEight (third parties absorbed into uncertainty; 538 2016 used the
undecided and third-party share to widen uncertainty). None publishes a
per-party draw for dozens of parties below 1%. Fisher's 2013 UK forecast, on a
linear scale, gave the Liberal Democrats a 95% interval of 0-26% with zero as a
"hard boundary that had to be invoked": the additive-scale failure, the mirror
image of the Dirichlet's spike.

### 1.5 New parties (cited)

Garcia Montalvo, Papaspiliopoulos & Stumpf-Fetizon (2019) build their Spanish
model around new-party entry (Podemos, Ciudadanos), using survey microdata that
already asked about the new parties; their drawn seat distributions for the new
parties have long right tails produced by D'Hondt, not by the vote model. Stoetzer
et al. set a first-time party's previous share to 0 in the fundamentals model.
No source found models a new party's vote uncertainty as a class with its own
width; the record-derived "about twice as uncertain as an established party of
the same size" in 1f §2.4 has no published counterpart to check it against.

### 1.6 Uniform versus proportional swing (cited)

Pack (2010) re-ran three UK elections and found "no evidence" that proportional
swing beats uniform swing. Electoral Calculus's strong transition model makes
declining parties "fall multiplicatively, with those losses split among the
advancing parties" (New Statesman, 2024). Hanretty (2024) notes that MRP estimates
resemble proportional swing more than uniform swing, and that the Liberal
Democrats "suffer quite badly when models spread out their support". This debate
is about geography (how a citywide change distributes across areas), not about
the size of the citywide change; it bears on the pool layer, not on the level
shock.

---

## 2. Calibration to historical error by party size, and common swings

### 2.1 Error as a function of size (cited)

- **Selb & Chen (2023)**: absolute poll bias ranges by party in points, but
  relative to party size the differences "lessen", and total variance is about
  twice what sampling implies. All parties in their data are above about 5%, so
  the result says nothing about parties below 1%.
- **Zweitstimme (2021)** adds error variation per party after back-testing found
  election-day forecasts overconfident. The correction is per party, not a
  function of size.
- **Katz & King (1999)** fit one scatter matrix per model; each log-ratio gets its
  own variance, so size dependence is absorbed per party, not parameterised.
- **No source found** fits error variance as an explicit function of vote share
  across a long tail of small parties. The nearest are the variable-dispersion
  option in Dirichlet and beta regression (Hanretty's footnote: φ modelled with
  covariates), which varies precision across contests, not across parties.

### 2.2 Common swings and correlated errors (cited)

- **Shirani-Mehr, Rothschild, Goel & Gelman (2018)**: polls for one election
  "often share a common component of error" (about 2 points election-level bias).
- **Garcia Montalvo et al. (2019)** decompose poll error into house, election,
  trend and idiosyncratic terms and "learn the correlations between the
  idiosyncratic errors for different parties".
- **Stoetzer et al. (2019)** estimate the full evolution covariance of the
  log-ratios; most correlations are indistinguishable from zero, with two
  interpretable positive ones (Left with AfD, Greens with CDU/CSU, relative to SPD).
- **Gelman et al. (2020)** argue that too-low correlation is detectable from
  implausible individual or conditional outcomes, and used such anomalies to find
  bugs in their own model (their section on using anomalous predictions).
- **Heidemanns et al. (2020)** do not estimate the correlation matrix freely; they
  construct it and shrink it toward a common positive correlation.

### 2.3 Read against this model (measured, then argued)

1f §4.1 measures no common factor in the draws (mean pairwise correlation of drawn
log shares among parties below 1%: 0.004) against a record in which every size
band below 5% moved together in 2011. 1h §4.6 finds total vote movement beyond any
real election in a large fraction of backtest draws. Gelman et al.'s mechanism
predicts both (argued): independent, long-tailed per-party noise inflates each
party's width and the sum of absolute movements while removing the joint movement
the record shows. The Roodt (2021) observation that the vote for parties other
than the ANC, DA and EFF "more than doubled" between 2016 and 2021 is a
national-level instance of a shared small-party swing (cited, secondary).

---

## 3. Local, fragmented and South African settings

- **South African forecasting literature is thin.** No peer-reviewed probabilistic
  forecast of South African local or national vote shares was found. What exists:
  - the CSIR results-night model (fuzzy clustering of voting districts on past
    behaviour, extrapolation from early counts), which is a nowcast from declared
    results, not a pre-election forecast;
  - the Social Research Foundation's polls, which publish results under low,
    medium and high turnout scenarios; Ipsos did not model turnout in 2024
    (Financial Mail, 2024, secondary);
  - news analysis of 2021 fragmentation (Roodt 2021) and turnout
    (KAS / Schulz-Herzenberg on abstention).
  None of these describes how small-party uncertainty is represented.
- **Municipal and by-election analogues.** Hanretty (2021) is the closest: a
  multiparty, local, zero-laden setting. It uses a single-precision Dirichlet and
  reports good calibration, but with five categories, small parties pooled, and a
  prior on φ chosen so small-party outcomes are possible at all.
- **Fragmented PR systems.** Garcia Montalvo et al. (Spain, 52 provinces, new
  parties) and the German models are the nearest; both work on a log or log-ratio
  Gaussian scale with learned cross-party correlation, and both pool or omit
  parties below national relevance.
- **Turnout.** The forecasting literature found treats turnout outside the
  vote-share model (scenarios in SRF; ignored in Linzer and the Economist, which
  model two-party share). Nothing found bears on the disconnect 1f §4.2 measures
  between pool turnout and voting-district turnout.

---

## 4. Synthesis for this model

### 4.1 Is the root problem the Dirichlet split?

**Yes, for the shape of small-party draws; and the missing common swing comes
from the same design, independent per-party noise, in both layers (argued, on
cited grounds).** The level shocks are independent per party (1f §1 row 3) and
the within-pool split adds independent noise with the sampling size law on top.
The within-pool split uses one concentration per pool, so:

1. every member's relative spread is set by its cell share times one number
   (§1.3, cited formula), which reproduces sampling noise rather than the record's
   size curve (1f §4.1, measured);
2. members move independently apart from the negative correlation the
   sum-to-one constraint forces (cited formula); with the level shocks also
   independent, nothing in the draw is shared among small parties (1f §4.1,
   measured). Removing the Dirichlet alone would not add a shared swing; the
   replacement has to carry one;
3. two width sources, the level shock and the Dirichlet, act on the same quantity
   without knowing about each other (1f §3.1, measured; MACHINERY "Where the
   forecast's width comes from").

The literature treats (1) and (2) as known properties of the Dirichlet (Aitchison,
Katz & King, Elfadaly & Garthwaite, Selb & Chen), and treats (2)'s consequence,
implausible individual outcomes from independent long-tailed noise, as a model
defect (Gelman et al. 2020).

A below-5% patch removes (1) for parties below the line and adds a common factor
among them. It leaves the Dirichlet on every party above the line, including
small cells of parties just above it: 1b v3's own table shows the VF+, IFP, RISE
and BOSA still above 5% in a fifth of Johannesburg 2026 draws (measured). That is
the bandage pattern the owner describes.

### 4.2 What the literature would substitute

**A log-scale (logistic-normal or logistic-t) draw for every party, with a
party-specific variance and a structured covariance** (cited: Katz & King 1999;
Stoetzer et al. 2019; Selb & Chen 2023; Garcia Montalvo et al. 2019). Mapped onto
this model (argued):

| piece | literature | this model |
|---|---|---|
| scale | log or log-ratio, closed by the multinomial-logit (softmax) link | latent log level per party, closed by normalisation; the existing capacity water-fill and IPF keep pool capacity |
| tails | Student-t with small df (Katz & King) | the level shock is already t7 |
| variance | per party (Selb & Chen; Katz & King) | per party as a function of size and history class, fitted to the record of residuals about the centre actually used; 1b v3 §3.3 already specifies this below the line |
| covariance | full where parties are few; constructed and shrunk where data are thin (Heidemanns et al.) | low rank: a cycle factor shared by all parties with size-dependent loading, a metro factor, and an own term; 1b v3 §3.2 already specifies this below the line |
| geography | separate layer (state or province deviations; swing rules) | the pool split, demoted from width source to a composition layer, or replaced by per-pool log-scale deviations about the citywide draw |

The 1b v3 unit-class draw is therefore the standard mechanism applied to part of
the spectrum. The literature gives no reason to stop it at a size line; it gives
reasons to apply one mechanism to all parties and let the variance function carry
the size dependence.

### 4.3 Pitfalls

| pitfall | source | how it applies here |
|---|---|---|
| **Width double-counted or lost when a layer is removed** | argued; MACHINERY "Each layer carries a CONDITIONAL share" (§1.50) | the level width below 15% is set narrow because the Dirichlet carries the rest. Removing or demoting the Dirichlet without re-fitting the level width to the full record makes every affected party too narrow, and the change scores as a regression for reasons unrelated to the mechanism |
| **Zeros** | Katz & King 1999 (structural zeros); Tsagris & Stewart 2014 (zeros in Dirichlet and log-ratio models) | logistic-normal has no mass at zero. With a known roster every drawn party has a positive centre, so this does not bite at the citywide level. It bites for a party that may effectively vanish (withdrawal, a 2011-style collapse) and for seeded arrivals with no record; those need an explicit mixture or a class width, not the Dirichlet's accidental spike |
| **Parameter count** | Katz & King 1999; Honaker, Katz & King 2001 (computation with more than three parties); Tomz et al. 2002 | Johannesburg 2026 draws dozens of parties; a free covariance is impossible. Low-rank factor structure plus a variance function of size is the only feasible form (argued) |
| **Covariance from few elections** | Heidemanns et al. 2020 construct and shrink rather than estimate | four metro LGE transitions give four cycle means per size band; a cycle-factor loading estimated from them is weak. Cross-metro co-movement within a cycle adds observations but they share the cycle (1f §4.1 already notes they are not independent) |
| **Reference-party dependence** | Selb & Chen 2023 footnote 1; Hanretty 2021 | additive log-ratios depend on the reference unless the covariance is full. Modelling latent log levels closed by normalisation avoids choosing a reference (argued) |
| **Fitting criterion** | Hanretty 2021: log-ratio regressions minimise error on the log-ratio scale, and lost to the Dirichlet | applies to estimating centres. Here the centre is fixed by the spine and IPF; only the draw's shape around a fixed centre changes (argued) |
| **Tail weight** | Katz & King 1999 (small df); Gelman et al. 2020 (independent long tails lower effective correlation) | t tails on the own term reintroduce Gelman et al.'s low-correlation effect; heavy tails belong on the shared factors if the record supports them (argued, untested) |
| **Large parties already fit** | 1f §2.2 (≥ 15% close to the record; slightly wide), measured | replacing the Dirichlet above 5% changes parties whose draws already match the record; the backtest must show they do not get worse, and their gain is consistency, not accuracy |

### 4.4 Where the literature is silent

- Size-dependent variance across a long tail of parties below 1%. Every model
  found pools such parties into "others".
- What replaces a pool split as within-group composition noise in an
  ecological, group-based model with IPF balancing. No published election model
  has this structure.
- A width class for new parties. The record in 1f §2.4 is the only evidence.
- South African local elections: no published probabilistic vote-share model.
- Turnout coupling between a group layer and an area layer.

### 4.5 Contrary evidence

| claim against replacing the Dirichlet | source | why it does or does not transfer |
|---|---|---|
| Dirichlet regression beat log-ratio regression (in-sample MAE 3.5 vs 6.2 points) | Hanretty 2021 | compares fitting criteria for centres, with structural zeros replaced by 1/40,000 (which makes log-ratios extreme). Here the centre is fixed and only the draw shape is in question. Hanretty also needed a prior on φ to give small parties non-zero chances, the same symptom |
| Leading multiparty forecasts still use a Dirichlet | Stoetzer et al. 2019; Bauer et al. 2018 | Stoetzer uses it for a seven-category fundamentals prior with small parties pooled, and maps to log-ratios for the forecast state. KOALA uses it for sampling noise, where the 1/√p law is correct |
| The Dirichlet matches the record above 5% | 1f §2.2, measured | true; a replacement has to match it there too, and the backtest is the test |

---

## Recommendation

Treat the problem as one mechanism, not a small-party defect: replace the
within-pool Dirichlet as the source of party-level width with one log-scale draw
for every party, whose variance is a function of size and history class fitted
to the record and whose correlation comes from a shared cycle factor (loading by
size), a metro factor and an own term. Keep the pool layer for composition, at a
width estimated from how much group shares moved about the citywide change, and
re-fit the level width to the full record in the same change, so that no width is
lost or counted twice. The 1b v3 specification is the template; the change is to
remove its size line rather than to add one.

**Evidence strength.**
- Strong (several independent published sources): the single-concentration
  Dirichlet's restrictions; log-ratio Gaussian or t with party-specific variances
  and correlation as the established alternative; independent long-tailed noise
  producing implausible outcomes.
- Moderate (this round's measurements): the record's size curve is not the 1/√p
  law; small parties share a cycle swing.
- Weak or absent: anything about dozens of sub-1% parties, new-party width, or
  group-based ecological models with IPF. Whether the unified draw improves the
  backtest is untested; it is a question for a pre-registered arm, with the
  above-5% parties' calibration as an explicit falsifier.

---

## Sources

| author(s) | year | title | URL | method | relevance |
|---|---|---|---|---|---|
| Katz, J. N. & King, G. | 1999 | A Statistical Model for Multiparty Electoral Data (APSR 93:15-32) | https://gking.harvard.edu/files/multiparty.pdf | additive logistic Student-t, full scatter matrix, structural zeros | founding multiparty model; rejects the Dirichlet and the normal |
| Honaker, J., Katz, J. N. & King, G. | 2001 | An Improved Statistical Model for Multiparty Electoral Data (working paper; Political Analysis 2002) | https://authors.library.caltech.edu/records/c5d2w-qmn15 | fast approximation to Katz & King | computational cost beyond three parties |
| Tomz, M., Tucker, J. A. & Wittenberg, J. | 2002 | An Easy and Accurate Regression Model for Multiparty Electoral Data (Political Analysis 10:66-83) | https://ideas.repec.org/a/cup/polals/v10y2002i01p66-83_00.html | seemingly unrelated regressions | simpler alternative that scales to many parties |
| Stoetzer, L. F., Neunhoeffer, M., Gschwend, T., Munzert, S. & Sternberg, S. | 2019 | Forecasting Elections in Multiparty Systems: A Bayesian Approach Combining Polls and Fundamentals (Political Analysis 27:255-262); online appendix | https://www.sowi.uni-mannheim.de/media/Lehrstuehle/sowi/Gschwend/Article/append-forecasting_elections_in_multiparty_systems.pdf | Dirichlet regression (fundamentals) + log-ratio random walk with full evolution covariance | zweitstimme.org method; small parties pooled |
| Neunhoeffer, M., Gschwend, T., Munzert, S., Stoetzer, L. F. & Sternberg, S. | 2021 (PS Jan 2022) | Zweitstimme Model: A Dynamic Forecast of the 2021 German Federal Election | https://www.sowi.uni-mannheim.de/media/Lehrstuehle/sowi/Gschwend/Article/zweitstimme_model_a_dynamic_forecast_of_the_2021_german_federal_election.pdf | as above, plus per-party added election-day error | overconfidence corrected per party |
| Selb, P. & Chen, S. | 2023 | Bias and Variance in Multiparty Election Polls (POQ 87:1025-1037) | https://kops.uni-konstanz.de/bitstreams/d23681c6-43c3-49cb-bc00-c4c4845d42a5/download | log-share model, inverse multinomial link, party-specific variances | explicit reason for not using the Dirichlet |
| Hanretty, C. | 2021 | Forecasting multiparty by-elections using Dirichlet regression (IJF) | https://chrishanretty.co.uk/pubs/10.1016_j.ijforecast.2021.03.007/fulltext.pdf | Dirichlet regression, one φ; compared to log-ratio regression | closest local analogue; contrary evidence |
| Hanretty, C. | 2024 | Why is the MRP so variable when the uniform national swing is so predictable? | https://www.chrishanretty.co.uk/posts/changing_consty_fx/ | commentary | MRP resembles proportional swing; spread support penalises concentrated small parties |
| Gelman, A., Hullman, J., Wlezien, C. & Morris, G. E. | 2020 | Information, incentives, and goals in election forecasts (JDM 15:863-880) | https://mucollective.northwestern.edu/files/2020%20-%20Gelman,%20Information,%20Incentives%20and%20Goals%20in%20election%20forecasts.pdf | critique of forecast correlation structure | independent long-tailed noise and too-low correlation produce implausible outcomes |
| Heidemanns, M., Gelman, A. & Morris, G. E. | 2020 | An Updated Dynamic Bayesian Forecasting Model for the 2020 Election (HDSR) | https://sites.stat.columbia.edu/gelman/research/published/hdsr_forecasting.pdf | constructed and shrunk between-state correlation | how to set a covariance without enough elections |
| Linzer, D. A. | 2013 | Dynamic Bayesian Forecasting of Presidential Elections in the States (JASA 108:124-134) | https://ocf.berkeley.edu/~vsheu/Midterm%202%20Project%20Files/Linzer-prespoll-May12.pdf | logit-scale random walk, hierarchical | logit scale for bounded shares |
| Shirani-Mehr, H., Rothschild, D., Goel, S. & Gelman, A. | 2018 | Disentangling Bias and Variance in Election Polls (JASA) | https://sites.stat.columbia.edu/gelman/research/published/polling-errors.pdf | logit model of election-level bias and variance | common election-level error component |
| Garcia Montalvo, J., Papaspiliopoulos, O. & Stumpf-Fetizon, T. | 2019 | Bayesian forecasting of electoral outcomes with new parties' competition (arXiv 1612.03073) | https://arxiv.org/pdf/1612.03073 | MRP fundamentals + multivariate Gaussian poll errors with learned cross-party correlation | new parties; fragmented PR; province-level seats |
| Bauer, A., Bender, A., Klima, A. & Küchenhoff, H. | 2018 | KOALA: A new paradigm for election coverage (arXiv 1807.09665) | https://arxiv.org/pdf/1807.09665 | Bayesian multinomial-Dirichlet now-cast | Dirichlet used where uncertainty is sampling only |
| Lauderdale, B. E., Bailey, D., Blumenau, J. & Rivers, D. | 2020 | Model-based pre-election polling for national and sub-national outcomes in the US and UK (IJF 36:399-413) | https://ideas.repec.org/a/eee/intfor/v36y2020i2p399-413.html | MRP | sub-national multiparty estimation (abstract only read) |
| Ford, R., Jennings, W., Pickup, M. & Wlezien, C. | 2016 | From polls to votes to seats: forecasting the 2015 British general election (Electoral Studies 41:244-249) | https://eprints.soton.ac.uk/381998 | poll pooling, projection, seat simulation | five/six-party UK; method details not read |
| Fisher, S. | 2013 | A long-range forecast for a 2015 British General Election | https://electionsetc.com/2013/10/25/a-long-range-forecast-for-a-2015-british-general-election-based-on-current-polls-and-historical-polls-and-votes/ | regression on historical poll-vote errors | linear-scale interval clipped at zero for a small party |
| Pack, M. | 2010 | Uniform versus proportional swing: which is best? | https://www.markpack.org.uk/7556/uniform-versus-proportional-swing-which-is-best/ | re-run of three UK elections | no evidence for proportional swing |
| Walker, B. (New Statesman) | 2024 | Britain Predicts | https://sotn.newstatesman.com/2024/05/britainpredicts | strong transition model description | multiplicative falls for declining parties |
| Jennings, W. & Wlezien, C. | 2018 | Election polling errors across time and space (Nature Human Behaviour) | https://eprints.soton.ac.uk/421260 | 30,000 polls, 351 elections | poll error lower under PR; party-size result not found in the abstract |
| Elfadaly, F. G. & Garthwaite, P. H. | 2013 | Eliciting Dirichlet and Connor-Mosimann prior distributions for multinomial models (TEST 22:628-646) | https://ideas.repec.org/a/spr/testjl/v22y2013i4p628-646.html | prior elicitation | Dirichlet inflexibility; generalised Dirichlet as remedy |
| Wikipedia contributors | accessed 2026 | Dirichlet distribution | https://en.wikipedia.org/wiki/Dirichlet_distribution | reference | variance, covariance and marginal formulas |
| Wikipedia contributors | accessed 2026 | Generalized Dirichlet distribution | https://en.wikipedia.org/wiki/Generalized_Dirichlet_distribution | reference | Connor-Mosimann structure |
| Tsagris, M. & Stewart, C. | 2014 | A Dirichlet Regression Model for Compositional Data with Zeros (arXiv 1410.5011); cites Martin-Fernandez et al. 2003 on multiplicative zero replacement (original not read) | https://arxiv.org/pdf/1410.5011 | Dirichlet regression with zeros | log-ratio methods and zeros |
| Ellis, P. | 2020 | NZ 2020 general election forecasts | https://freerangestats.info/elections/nz-2020 | Bayesian state-space, t prior on swing | threshold and electorate seats handled by simulation; scale not stated |
| FiveThirtyEight (Silver, N.) | 2016 | A User's Guide To FiveThirtyEight's 2016 General Election Forecast | https://fivethirtyeight.com/features/a-users-guide-to-fivethirtyeights-2016-general-election-forecast | poll-based simulation | third-party and undecided share widen uncertainty |
| Roodt, M. (African Arguments) | 2021 | What did we learn from South Africa's local elections? | https://africanarguments.org/?p=37947 | news analysis | shared small-party rise 2016-2021 |
| CSIR (SABC News) | 2024 | CSIR election results prediction methodology explained | https://www.sabcnews.com/sabcnews/csir-election-results-prediction-methodology-explained/ | fuzzy clustering of voting districts, results-night | the only documented South African statistical model; a nowcast |
| Financial Mail | 2024 | The perils of polling | https://www.pressreader.com/south-africa/financial-mail/20240502/281891598349459 | news | SRF turnout scenarios; Ipsos without turnout modelling |
| Konrad Adenauer Stiftung (Schulz-Herzenberg quoted) | 2021/2022 | Analysing voter abstention in the 2021 local government elections | https://www.kas.de/be/einzeltitel/-/content/analysing-voter-abstention-in-the-2021-local-government-elections | survey analysis | turnout, not vote-share uncertainty |
