# Johannesburg Election Model

A voting-district model of the City of Johannesburg — 5,000 simulations over 865 voting districts, both ballots, the statutory seat formula, and the coalition arithmetic it permits. The forecast, the machinery, and the full warts-and-all record of how it was built, reviewed, broken and corrected.

# Log — findings, obstacles, decisions, mitigations

A running record of what was built, what got in the way, what was decided and
why. Two purposes: to feed the eventual description of the model, and to keep an
honest register of the assumptions it rests on so they can be mitigated rather
than forgotten.

Append to this file as work proceeds. `SOURCES.md` records *where data came
from*; this records *what we learned and chose*.

Status key: **✅ resolved** · **🟡 mitigated, live risk** · **🔴 open, needs a human**

---

## 1. Findings that changed the model

### 1.1 Seat entitlement follows the combined ward+PR vote, not the PR ballot ✅

**What the plan said.** §0: "A party's total seat count is determined by its
citywide **PR ballot share**", and therefore "ward-level prediction is *not* the
primary target."

**What is actually true.** Entitlement follows the party's share of the ward and
PR votes *added together*. From the IEC's own Seat Calculation Detail report,
quoting Municipal Structures Act Schedule 1:

```
Q = (A / (B - C - D)) + 1 ; disregarding fractions
A = total valid votes for all parties, WARD AND PR BALLOTS ADDED TOGETHER
B = seats available (270)   C = independent ward councillors
D = ward seats held by parties with no PR list
```

Then `floor(votes / Q)` per party, shortfall by largest remainder. `A` excludes
independents *and* parties with no PR list.

**Evidence.** `src/seats.py` + `src/validate_seats.py` reproduce the published
council exactly — quota, `A`, and every party's seat count — for three
elections across two council sizes:

| | A | Q | Seats | Result |
|---|---|---|---|---|
| 2011 | 2,162,768 | 8,319 | 260 | quota matches published |
| 2016 | 2,496,617 | 9,247 | 270 | ANC 121, DA 104, EFF 30 — all match |
| 2021 | 1,834,260 | 6,794 | 270 | ANC 91, DA 71, ASA 44, EFF 29 — all match |

The exclusions reconcile to the vote: 1,846,189 − 11,904 independents − 24
Sakhisizwe − 1 African Covenant = 1,834,260.

**Why the error survived review.** Ward and PR shares usually agree within a
point, so PR is an excellent proxy. In 2016 the DA polled 38.34% ward / 38.48%
PR — which is precisely why the plan's own sanity check ("104 seats ≈ 38.4% of
270") appeared to confirm the PR-only rule. **ActionSA in 2021 is the
counter-example**: 13.98% ward against 18.12% PR, worth about five seats. They
contested 134 of 135 wards, so it is genuine ticket-splitting, not absent
candidates.

**Decision.** The ward ballot is roughly half the target quantity. §3 must model
both ballots (task #12). §0 carries a rev-3 correction box.

**Second-order effects now tracked.**
- *Contestation coverage* is distinct from ticket-splitting: the PA fielded ward
  candidates in only 52 of 135 wards in 2021, structurally capping its ward
  total regardless of support. A 2026 forecast needs a view on how many wards
  each party contests.
- *Overhang* did not occur in 2016 or 2021, but 2021 was closer than the plan
  implied — the ANC took 87 wards against an entitlement of 91, five wards of
  headroom. With its citywide share falling faster than its stronghold
  dominance, overhang is a live 2026 risk, not a theoretical one.

### 1.2 A3 holds, but λ is the wrong carrier of it 🟡

**What the plan said.** §3.3 predicts `T_2026(i) = T_2024(i) × λ̂(i)`, resting on
A3: the relative pattern of turnout drop-off across VDs is stable. The plan calls
this "the model's central bet" and "the most stable feature of South African
metro elections".

**What is measured.** `src/turnout.py` tests it rather than assuming it.

*A3 is real but modest.* Correlation between λ_2016 and λ_2021 across 823 VDs is
**+0.39**. Not a small-sample artefact — flat to slightly lower among larger VDs
(+0.32 above 2,000 registered), +0.33 registration-weighted. But λ_2016 explains
only ~15% of the variance in λ_2021.

*The previous LGE's level predicts better than λ does.* Predicting VD turnout,
every predictor rescaled to the true citywide total so only the relative pattern
is judged (MAE in turnout points):

| Predicting | Previous LGE level | Plan's ratio form | Preceding NPE level |
|---|---|---|---|
| 2021 | **0.0409** | 0.0592 | 0.0657 |
| 2016 | **0.0527** | *(needs 2009 NPE)* | 0.0769 |

Same ordering both cycles. **Like predicts like**: LGE patterns are predicted by
the previous LGE; the ratio form only partially closes the gap because it starts
from an NPE base and corrects toward LGE with λ.

**Decision.** Recorded in §3.3 as a *suggested* change, deliberately weaker than
the §0 correction: two cycles of evidence, and 2021 was Covid-affected. Task #19
scores both forms inside the folds on seat outcome, not VD turnout MAE, before
either is adopted. λ̂ is retained for the citywide level regardless — it implies
0.66 and a 41.9% citywide 2026 turnout (41.7% pre-cleanup), inside §8.2's 38–42%.

**Method note worth keeping.** The rescaling is load-bearing. Without it the
comparison is rigged: a citywide-drift predictor is handed the true 2021 total
while the ratio form must infer the level from 2016's drop-off. Unrescaled, the
ratio form overshoots the citywide level by 25%, because 2021's collapse was far
deeper than 2016's — which is what `w_recency` exists to hedge, and exactly why
it cannot be hedged from a single prior cycle.

### 1.3 The concordance is easier than planned, the ward apportionment harder ✅

The plan anticipated intersecting historic VD shapefiles against 2026 ones. Not
needed: 98.8–100% of each election's VDs persist in the 2026 set under the same
number, and those that do not carry 0.21–0.45% of votes.

The reverse is true for step 5. 181 of 865 VDs straddle a 2026 ward boundary, so
their votes must be split. Assumption A1 asks for registration weighting "wherever
the roll permits" — it does: on the MDB layer `REGPOP` is the VD total and
`WardPop` is the *part's own* registration, reconciling exactly for all 865 VDs
(grand total 2,348,781). This also correctly zero-weights **59 sliver parts**
holding no registered voters, which area weighting would have given real vote
share.

### 1.4 Two of the plan's four bloc transitions are confirmed ✅

From the party crosswalk, on the PR ballot: 2014→2016 gives ANC bloc −6.6 / DA
bloc +6.1 against the plan's cited −6 / +6; 2019→2021 gives −21.1 / +13.9
against −22 / +13.

### 1.5 §3.4(b) pairs binary logit with softmax, which is inconsistent ✅

**What the plan says.** Work in logit space, then "softmax renormalisation"
within each VD.

**Why that is wrong.** `logit(p) = log(p/(1−p))` exponentiates to *odds*, so a
softmax over logits normalises odds rather than shares. Odds and shares diverge
as p grows, so the error falls almost entirely on the largest parties. In fold 1
it put the ANC at 54.0% against an actual 44.9% *even though θ had been set to
the exactly-observed citywide ratio* — a 9-point error generated purely by the
renormalisation.

Softmax pairs with multinomial log-shares; binary logit pairs with expit followed
by rescaling.

**Decision.** Use logit → expit → rescale. This keeps the logit semantics
§3.4(b) actually wants (proportional swing where a party is small, additive where
mid-sized, never negative). VD-level MAE fell from 0.93pp to 0.49pp on the
change, and the EFF's citywide error from −5.4pp to +0.02pp.

### 1.6 θ has two incompatible definitions, and §3.5 quotes the wrong one 🟡

Calibrating fold 1 exposed that "θ" can mean two different numbers:

- **raw** — the observed citywide LGE/NPE ratio. This is what §3.5 quotes
  ("Observed: 44.5/52 ≈ 0.86 (2016)"), and fold 1 reproduces it exactly:
  θ_ANC raw = 0.86.
- **calibrated** — the value that reproduces that citywide ratio *through the
  model*, once within-VD renormalisation is accounted for. θ_ANC calibrated =
  **0.79**, θ_DA raw 1.19 against calibrated **1.46**.

Feeding a raw ratio in as if it were calibrated leaves a systematic residual on
the biggest parties — ANC +3.1pp, DA −3.3pp in fold 1 before the fix.

**Decision.** `calibrate_theta()` solves for the model-consistent value by
iterative proportional fitting. Both are reported and written to
`fold1_parameters.csv`. **§3.5's prior ranges are in raw units and cannot be fed
to the model directly** — they need converting, or restating in calibrated units,
before the Monte Carlo uses them. This is a live trap for task #11.

### 1.7 Fold 2: γ transfers across cycles, θ does not ✅

The plan's §4.1 discipline — fit on fold 1, validate on fold 2, never fit both
and report the fit — turns out to separate the two parameters cleanly.

| fold 2 configuration | VD MAE | ward winner | seat MAE | total seat error |
|---|---|---|---|---|
| refit in-sample (reference) | 0.54pp | — | — | — |
| **θ and γ both from fold 1** | 0.60pp | 128/135 | 1.86 | **54** |
| **γ from fold 1, θ recalibrated** | 0.58pp | 128/135 | 0.50 | **12** |

Transferring γ costs almost nothing — VD MAE 0.58 against an in-sample 0.54, and
the ward-winner count is identical either way. Transferring θ costs a great deal:
the seat error more than quadruples.

**Interpretation.** γ is structural — it encodes *where* a party's support sits
relative to its citywide mean, and that geography is stable between cycles. θ is
political weather, and 2014→2016 tells you very little about 2019→2021. This is
strong support for §3.5's treatment of θ as a wide scenario lever rather than a
fitted constant, and it means γ can reasonably be fitted once and reused.

Against §4.3's stated expectation of "±1.5 points MAE on established parties":
fully out-of-sample, the ANC came in at −0.42pp, the IFP −0.90pp, but the DA
+3.08pp and the EFF +2.60pp. So the expectation is roughly right for some and
optimistic for others.

### 1.8 Turnout is second-order for seats; θ dominates ✅ *task #19*

The turnout sub-model is now wired into the folds — VDs are weighted by predicted
votes cast in the *target* election rather than by the baseline's, which is what
`fold.py` did before and which silently assumed the turnout pattern does not
change between an NPE and an LGE.

**First attempt produced a null result that was an artefact.** With θ recalibrated
per run, all four turnout specifications gave identical seats. That is because
calibration forces predicted citywide shares to match the actual under *whatever*
weights are supplied, so the weighting is absorbed into θ and can never reach the
seat allocation. The test only means anything with θ held fixed.

**With θ and γ both fixed from fold 1, so turnout is the only thing varying:**

| turnout weighting | ward winner | total seat error | ANC PR err | DA PR err |
|---|---|---|---|---|
| actual target turnout (oracle) | 128/135 | 60 | −2.16pp | +5.55pp |
| previous LGE pattern | 126/135 | 60 | −1.93pp | +5.14pp |
| the plan's λ ratio form | 126/135 | 60 | −2.15pp | +5.49pp |
| baseline votes cast (the crude assumption) | 128/135 | 54 | −0.37pp | +3.01pp |

Two things stand out. **A perfect turnout forecast does not improve the seat
outcome** — the oracle scores no better than the crude assumption. And the crude
assumption scores *best*, because fold 1's θ was itself calibrated under baseline
weighting, so applying it under the same weighting is internally consistent while
switching introduces a mismatch.

**Conclusions.**
1. Turnout weighting shifts citywide shares by 1–2pp and total seat error by
   about 6. Real, but small beside θ error, which moved the same metric from 12
   to 54.
2. **Consistency between how θ is calibrated and how it is applied matters more
   than which turnout specification is used.** This is a live constraint on the
   Monte Carlo.
3. Effort spent improving the turnout sub-model buys less accuracy than effort
   spent on θ. That reorders the priorities the plan implies.

### 1.9 §5's leverage prediction is half right, and its magnitude is overstated ✅

§5 states its expected finding "in advance so it can be falsified". Taking that
at its word, `src/leverage.py` tests it.

**What was predicted and what was found.** Leverage is measured as entitlement
displaced per point of ward turnout, on a central scenario built from §3.5's
default θ values.

| §5's prediction | Correlation with leverage | Verdict |
|---|---|---|
| *not* highest in marginal wards | −0.399 with marginality | **confirmed, strongly** |
| highest in high-registration wards | +0.365 with registration | **confirmed** |
| highest in high-ANC-share wards | −0.358 with ANC share | **contradicted** |
| highest in historically low-turnout wards | +0.321 with turnout | **contradicted** |

So the *negative* half of the prediction — that this is not a marginal-seats
story — holds firmly, and is the more important half, because it is what
distinguishes compensatory PR from a first-past-the-post intuition. The
*positive* half, that leverage concentrates in the low-turnout Soweto and Orange
Farm clusters, does not hold as a linear relationship. Leverage tracks a ward's
*distinctiveness* from the citywide mix weighted by its registration, and the
northern suburbs are just as distinctive as the south.

**The magnitude claim fails by more.** §5 says "a ten-point turnout swing across
Soweto moves the ANC's citywide share by several points and reallocates a dozen
seats". Perturbing whole 30-ward blocs across a full ten-point span:

| cluster perturbed by ±5 points | seats moved | DA+ActionSA entitlement |
|---|---|---|
| 30 highest ANC-share wards | 2 | −1.55 |
| 30 lowest ANC-share wards | 2 | +1.84 |
| 30 most marginal wards | 1 | −1.13 |

About two seats, not a dozen — overstated by roughly four to six times.

**This reverses the plan's strategic conclusion.** §5 concludes that "the DA's
path to 136 with ActionSA depends less on persuading anyone and more on whether
ANC-inclined voters in the south stay home". On these numbers it does not. In the
central scenario DA+ActionSA reach 113 and need 136 — 23 seats short — while a
full ten-point differential turnout swing across thirty wards is worth under two
seats to them. **Differential turnout cannot close a gap of that size; only
persuasion can.** That is consistent with the fold finding that θ dominates
turnout, and the two results reinforce each other.

**Method note.** The first implementation measured leverage in integer seats and
returned zero for almost every ward, with a spurious 2 for whichever ward sat on
a largest-remainder boundary. That is a property of the rounding, not the ward.
Fractional entitlement (party votes ÷ quota) is continuous and is what §5's
"per-ward turnout elasticity index" actually asks for.

### 1.10 The citywide turnout *level* cannot affect seats at all ✅

Follows from the Schedule 1 formula and is worth stating explicitly because it
sharpens what the turnout work is for. The quota is `Q = A/(B−C−D) + 1` where `A`
is total votes cast. Scale every VD's turnout by a constant and `A` scales, `Q`
scales with it, `floor(votes/Q)` is unchanged and every remainder is unchanged —
so the seat allocation is identical.

**Only *differential* turnout across VDs can move seats**, by changing the mix
that produces citywide shares. The projected ~41.9% citywide 2026 turnout is
therefore useful for reporting and for §5's leverage question, but contributes
nothing to the seat forecast on its own. §5's leverage analysis is precisely the
right framing: the question is never "how high is turnout" but "which VDs turn
out relative to which others".

### 1.11 Multiplicative θ cannot create a party from zero 🟡

ActionSA took 18.12% in 2021 from 0.00% in the 2019 baseline. Because θ is
multiplicative, no value of it can produce that — and worse, calibrating θ by IPF
with the entrant missing **silently distorts every other party's θ to absorb the
gap**: the ANC's calibrated θ came out at 0.12 and the DA's at 0.15, values that
look like parameters but are artefacts.

**Decision.** `--entrant CODE=SHARE` seeds a party absent from the baseline at an
assumed citywide share, spatially flat, and lets the rest renormalise around it.
With ActionSA seeded, fold 2's VD MAE drops from 0.94pp to 0.54pp and the θ
values become interpretable again.

**Consequence for 2026.** MK is present in the 2024 base at 12.22%, so it is
*not* this case and multiplicative θ_MK works. But any party that contests 2026
without a 2024 provincial-ballot presence needs an absolute share prior, not a θ.
The PA is a near-miss illustration: 0.03% → 2.96% is a raw θ of 122, which is
technically representable but not meaningfully a "factor".

### 1.12 2026 ward boundaries are a near-total redraw ✅

129 of 135 CoJ wards changed shape for 2026; only 6 are unchanged. Ward *count*
stays 135, confirming §0's 135/270/136 and refuting the press report of 274
seats. Of the 860 VDs common to 2021 and 2026: 640 stay in the same ward, 40
move ward, 180 are split across 2026 wards.

---

### 1.13 The forecast: no two-party majority exists except ANC+DA ⚠️ superseded — see 1.14/1.15

> **This section's coalition conclusion was falsified by the 2026-08-04
> external review.** Its enumeration covered six hand-picked coalitions;
> checked over all subsets of the same draws, DA+EFF+MK reached 136 in 60.8%
> of them. The corrected forecast is §1.15. Kept for the record.

5,000 draws over §3.5's ranges, bloc-level per §3.4(a), both ballots, Schedule 1
allocation. Seed 20261104.

| party | median seats | 5th–95th |
|---|---|---|
| DA | 87 | 63–105 |
| ANC | 67 | 53–81 |
| EFF | 27 | 17–39 |
| MK | 25 | 16–36 |
| ActionSA | 17 | 5–38 |
| PA | 11 | 9–15 |

| coalition | P(≥136) | median | 5th–95th |
|---|---|---|---|
| DA + ActionSA | **0.0%** | 105 | 91–116 |
| DA + ActionSA + IFP + VF+ + ACDP | 0.1% | 116 | 102–128 |
| ANC + EFF + MK | 0.0% | 120 | 108–129 |
| **ANC + DA** | **87.5%** | 154 | 127–175 |
| every party outside the ANC bloc | 99.9% | 150 | 141–162 |

The DA is the largest single party in 86.1% of draws.

**The finding.** No two- or three-party coalition reaches 136 except ANC+DA. A
majority excluding the ANC bloc is arithmetically available — the whole non-ANC
field is worth about 150 — but it requires close to *every* other party in the
council, which puts the PA (median 11) and the minor-party tail in a pivotal
position rather than ActionSA alone.

DA+ActionSA is tightly bounded at 91–116 despite ActionSA's own range being wide
(5–38). That is §3.4(a)'s bloc structure working as intended: drawing the bloc
shift and splitting within it makes the two negatively correlated, so their
*combined* total is far more stable than either party's — which is the
politically relevant quantity.

**Consistency with the rest of the work.** §5's leverage result said differential
turnout is worth about two seats across a thirty-ward, ten-point swing. The gap
from DA+ActionSA's 105 to 136 is 31 seats. The two results agree: turnout
mobilisation cannot bridge that, and the plan's §5 conclusion that the DA's path
runs through ANC voters staying home does not survive either test.

**What this is conditional on.** §3.5's ranges are informed priors, not
estimates, and the result inherits them entirely. It also inherits R7:
established parties are forecast well and genuinely new ones not at all. A party
that does not exist in the 2024 baseline cannot appear in any draw.

### 1.14 External review (2026-08-04): six errors, six unstated assumptions ✅ *all fixed*

Full review in `model-review.html`. The errors, one line each, with the fix:

- **E1 — coalition enumeration was pre-filtered on plausibility**, exactly what
  §3.8 forbade, and the published "no two/three-party coalition except ANC+DA"
  was false (DA+EFF+MK: 60.8% of the old draws). Fixed: `src/coalitions.py`
  does full enumeration, minimal winning coalitions, Banzhaf/Shapley–Shubik,
  and the minority-government class, on per-draw thresholds.
- **E2 — the within-bloc Dirichlet was centred on 2024 proportions**, silently
  discarding §3.5's per-party views (θ_MK 0.60 was unreachable); the θ modes
  also imply an ANC-bloc shift of −14.8 against the table's −9 — an internal
  inconsistency the old code resolved without flagging. Fixed: split centres on
  the θ-mode view (tilted by evidence, below), bloc-shift modes are derived and
  clamped to the historical ranges, and every draw's implied θ is checked
  against §3.5's ranges with the violation rate reported.
- **E3 — ward winners and overhang were never computed**, despite §3.7 step 5
  and §0 flagging overhang as live. Fixed: per-draw FPTP winners over the 135
  2026 wards, overhang expands the council and moves the threshold
  (`overhang_rule: expand`; a `cap` counterfactual bounds the unverified
  statutory fine print).
- **E4 — by-elections, polling and census covariates influenced nothing.**
  Fixed: `src/byelections.py` implements §3.6 (within-ward deltas, exp-decay ×
  √votes × ρ weighting) and the §3.3 turnout covariate data; the deltas tilt
  each party's central level at `w_bye` (0.40), clamped to §3.5's ranges so
  stronghold swings cannot claim absurd citywide levels; a polling lever spans
  the SRF↔Ipsos disagreement.
- **E5 — the sheet's "without being shown the answer" overstated the fold-2
  validation** (θ was recalibrated against the actual citywide result). Fixed
  in the sheet's wording; §5B now states that the backtests validate the
  spatial machinery and the citywide ranges are unvalidated priors.
- **E6 — minor parties moved in lockstep under one f_other draw**, giving
  two-seat "90% intervals". Fixed: independent per-party triangulars with
  ranges set around the observed fold ratios (IFP 1.34→1.97, VF+ 0.81→1.65,
  ACDP 0.58→1.82, Al Jama-ah 3.12); Al Jama-ah's θ is now documented here
  rather than invented silently.

Assumptions surfaced and made adjustable (all are sliders on
`forecast-interactive.html` and keys in `montecarlo.DEFAULTS`):
ward/PR ratios (MK 0.80 judgement, PA contestation uplift 1.25), per-draw
turnout uncertainty (pattern blend + σ 0.08 noise), γ for parties fold 1 never
saw now fitted on 2021→2024 (`gamma_recent.py`: ASA **0.49**, PA 0.54 — the
old silent 1.0 was far off), the A5 marginal-voter blend
(`leverage.py --marginal blend`: leverage magnitudes halve, rankings and the
"turnout cannot close the gap" conclusion survive), and a generic-entrant slot
(P 0.25, share mode 4%) because every fold and the live case contained one.

Also fixed while in there: **87 VD-years with turnout above 105%**
(registration mismatches; one VD projected 9.9% 2026 turnout off a 245% "2019
turnout") are now dropped from the λ series — A3's correlation eases to +0.32
and no conclusion changes. Fold 2 re-scored on the cleaned data: γ-transfer
129/135 ward winners (was 128) with seat error 12 unchanged; the fully blind
configuration worsens to 60 (was 54), so "θ does not transfer" strengthens.
The §3.3 by-election turnout covariate is also now wired into λ̂
(`--kappa-bye`, default 0.25): 14 wards' contests tilt 91 VDs by ×0.91–×1.14,
and — consistent with turnout being second-order — the seat forecast is
essentially unchanged by it.

### 1.15 The corrected forecast: overhang is the norm, and it raises everyone's bar ✅

5,000 draws, seed 20261104, all fixes and evidence blending in
(`data/processed/forecast_summary.json` is the machine-readable record).

| party | median seats | 5th–95th | mean ward wins |
|---|---|---|---|
| DA | 81 | 55–103 | 57 |
| ANC | 75 | 58–86 | 73 |
| EFF | 28 | 18–40 | 1 |
| ActionSA | 26 | 10–50 | 0 |
| MK | 20 | 12–29 | 1 |
| PA | 14 | 10–17 | 1.5 |
| new entrant | 0 | 0–19 | 0 |

**The new headline: P(overhang) ≈ 87–90%, almost entirely the ANC's.** With
its citywide share in the mid-20s but its stronghold wards intact against a
fragmented opposition, the ANC wins ~73 of 135 wards on a ~65-seat
entitlement. The council expands to a median of ~281 and the majority
threshold moves to ~141. Every coalition now has to clear a higher, moving
bar — this is what killed the marginal three-party arithmetic from the old
run (DA+EFF+MK falls from 60.8% to ~26%). Caveat carried on everything
overhang-conditional: the expansion rule is the plan's reading of Schedule 1,
unverified against an IEC worked example (none exists for CoJ); the `cap`
toggle bounds its effect.

Coalition arithmetic, fully enumerated (per-draw thresholds):

| finding | value |
|---|---|
| ANC+DA majority (also the dominant MWC) | **86.5%** |
| DA+EFF+ASA | 34% |
| DA+EFF+MK | 26% |
| DA minority via abstention, 2021 pattern (only ANC opposes) | **61%** |
| ANC minority, only DA opposes | 38% |
| majority without ANC, EFF and MK together (needs ~the whole field) | 99.2% at median 157 vs threshold ~141 |
| Banzhaf medians | DA 29%, ANC 24%, EFF 11%, **ASA 11%**, MK 8%, PA 5% |

The power indices settle the sheet's asserted claim the review flagged:
ActionSA out-ranks the PA as kingmaker (11% vs 5%) — the old sheet had it
backwards. The by-election blend is what moves ActionSA (centre 9.3% → 13.1%;
its contested-ward deltas imply it holds its 2021 level where it is
organised); `w_bye` to zero removes it, and the slider exists for exactly that
argument.

---

### 1.16 Blind math audit (2026-08-05): core verified; the overhang *reading* is the dominant uncertainty 🟡

An independent agent audited all mathematics blind (code before prose;
`model-review.html` addendum pending). Verified correct against known answers:
Schedule 1 allocator, Banzhaf/Shapley, IPF, samplers, turnout corrections,
leverage arithmetic. Safe fixes landed same night (JS seed reproducibility,
export means, percentile rounding, doc drifts 86.6→86.5 / 41.7→41.9).

Three material findings were implemented as knobs (`overhang_rule=deduct`,
`ward_noise_sd`, `level_floor`) and measured at 3,000 draws each:

| configuration | P(ANC+DA) | threshold | DA minority (2021 pattern) | majority w/o ANC bloc |
|---|---|---|---|---|
| **expand** (published) | 86.3% | 141 | 61.7% | 99.3% |
| **deduct** (3rd statutory reading) | **90.7%** | 136 | 53.0% | **97.0%** |
| **cap** (counterfactual) | 72.4% | 136 | 80.9% | 100.0% |
| ward noise σ=0.10 | 86.5% | 140 | 62.5% | 99.6% |
| ward noise σ=0.20 | 84.3% | 139 | 65.5% | 99.7% |
| level-floor fix | 85.6% | 141 | 63.8% | 99.5% |

**Conclusions.** (1) The audit's bracketing claim is confirmed in the numbers:
deduct falls *outside* [cap, expand] on the non-bloc-field row (97.0 vs
99.3–100). (2) The statutory overhang reading swings P(ANC+DA) across
**72–91%** and DA-minority across **53–81%** — it is the forecast's dominant
uncertainty, dwarfing every modelling knob; task #20 (IEC worked example) is
now the single most important open item. (3) The **qualitative** findings
survive every configuration: ANC+DA is the only reliable two-party majority in
all three rules, ward-wins-exceed-entitlement occurs in ~72–96% of draws
regardless of treatment, and the three-outcomes frame holds. (4) Ward noise
softens P(overhang) (89→83% at σ=0.10) without moving headlines — adopt once
σ is fold-calibrated. (5) The level-floor artefact, measured, is immaterial to
the structural rows (99.5 vs 99.3) — the auditor's mechanism was real but its
magnitude small; fix anyway for cleanliness.

**Not yet adopted into published numbers** — defaults unchanged pending a
decision on how the site should present the overhang-reading range.

### 1.17 Overhang RESOLVED: the statute says "deduct", and the IEC has applied it ✅ *task #20 closed by archive*

The archive hunt (2026-08-05) answered task #20 without waiting for the IEC.

**The law.** Schedule 1 item 16 ("Excessive seats") as it stood pre-2021 said
only that the excessive party "must not be allocated any seats from its list"
and "the seats of ward candidates are not affected" — silent on the overflow.
The **Municipal Structures Amendment Act 3 of 2021** (commenced 1 Nov 2021)
added subitems (3)–(9), verbatim:

> (3) A new quota of votes for a seat must be determined in accordance with
> the following formula (fractions to be disregarded): (A − B) / (C − (D + E)) + 1
> — where A = total valid votes for all parties; B = total votes for the party
> with excessive seats (party vote and ward candidates); **C = the number of
> seats in the council**; D = seats awarded to the party with excessive seats;
> E = independent ward councillors elected.
> (4)(a) The total number of valid votes cast for each party … excluding the
> party that has excessive seats, must be divided by the quota … (6) … the
> Commission must deduct … the number of ward candidates … declared elected.

**The precedent.** Laingsburg WC051, LGE 2021: DA won 3 of 4 wards on 23.06%
(entitlement 2). The IEC's published Seat Calculation Detail carries an
"Excessive Seat Calculation" block: DA's votes excluded, new quota
(6,453−1,530)/(7−3)+1 = 1,231, DA gets 3 ward + 0 PR, the remaining 4 seats
re-run among the others — **council stays 7**; the Karoo Democratic Force lost
the seat an "expand" reading would have preserved. (~65 Seat Calculation
Detail reports scanned across 2011/2016/2021; Laingsburg is the only
excessive-seat case found. Portal quirk: KZN path segment is `KN`.)

**Consequences.** (1) `overhang_rule="deduct"` — implemented from the audit —
matches the statutory formula (iterative exclusion, fixed council) and becomes
the DEFAULT; "expand" survives as a labelled counterfactual. (2) The majority
threshold is 136, full stop; the published "council grows to ~281, bar rises
to ~141" narrative is wrong law and must be corrected site-wide. (3) From the
audit suite: P(ANC+DA) rises ~86→91%, DA-minority-via-abstention falls
~62→53%, majority-without-the-ANC-bloc falls to ~97%. (4) The ANC's ward
strength still matters enormously — wins ≥ entitlement zero its list seats
and floor its total at its ward count — but it squeezes *other* parties
within 270 rather than raising the bar. (5) The IEC letter stands as
confirmation; the archive answered first.

Sources: francesbaard.gov.za consolidated Structures Act PDF; PMG
Act 3 of 2021 PDF; results.elections.org.za LGEPublicReports/1091/Seat
Calculation Detail/WP/WC051.pdf; copies in the session scratchpad.

### 1.18 Audit defaults adopted; blocs shown to be reservoirs, not pipes ✅

**Defaults adopted (2026-08-06),** per the audit suite in §1.16: `ward_noise_sd`
0.10 (winner-calling was deterministic per draw), `level_floor` 1e-6 (micro
floor artefact), and the deduct statute per §1.17. Poll evidence moved from the
two-endpoint `polling_lean` to a register (`polls.json`) consumed by both the
model (`poll_id`/`poll_weight`) and the interactive's poll picker, every poll
carrying source URL and caveat. Current published run: DA 79 (53–100), ANC 75,
ASA 25, MK 19–20, PA 13; threshold 136 fixed; P(ANC+DA) 86.5%; DA largest 61%;
DA ward wins soften ~57→49 under noise (its leads are narrow where the ANC's
are deep).

**Bloc leakage measured (2026-08-06), now a headline on the site.** Per-VD
bloc vote-count changes across transitions:

| transition | ANC-bloc Δ votes | DA-bloc Δ votes | capture of shed votes | VD-level r |
|---|---|---|---|---|
| 2019 NPE → 2021 LGE | −586,775 | −51,587 | **−8.8%** (negative!) | −0.39 |
| 2021 LGE → 2024 NPE | +399,253 | +54,190 | n/a (ANC regained) | +0.07 |

In the ANC bloc's record collapse, the DA bloc captured **none** of the
587k shed votes — its own count fell despite ActionSA's arrival at 18%. The
opposition's share surge was pure turnout composition. Supports the model's
watertight-bloc structure (levels drawn per bloc, no cross-flow mechanism);
caveat: Ward 130 (ASA 22.7% in a stronghold at 32% turnout) and SRF-July's
ANC 18 would require genuine crossing — 2026 may be the first real test.
Published as "When the ANC falls, nobody catches the votes" (forecast) and in
the interactive's Voting-blocs explainer.

### 1.19 Equality triggers the clause: "equal to or greater" taken at its word; audit round-2 repairs ✅

**A second-round audit (background agent, 2026-08-06, full report at
`audits/model-audit-2026-08-06-second-round.md`) verified the deduct machinery — 0 mismatches in 4,000
randomised trials against a direct implementation of the (A−B)/(C−(D+E))+1
formula, JS↔Python parity inside the disclosed ward-resolution gap — and
found one place the code measurably parted ways with the statute's wording.**

**The ruling.** Amended item 16(1) triggers the excessive-seats machinery for
a party whose ward seats are *"equal to or greater than"* its entitlement;
both engines fired only on strictly-greater. Excluding an exactly-at-quota
party is not a no-op: it recomputes the quota for everyone else (the audit
brute-forced 166k forced-equality cases; 4.2% shift a seat between the other
parties). Laingsburg (3 wins vs 2 entitlement) cannot arbitrate the equality
case, and the text is arguably ambiguous about whether an exactly-equal party
"has excessive seats" — we adopt the plain reading, and both engines now
trigger on ≥ (guarded to parties with at least one ward). Parties fixed in
cascade re-allocation rounds now also count as excessive (they previously
went unrecorded).

**Effect (seed 20261104, 5,000 draws).** P(any party excessive) 95.2% →
96.3% (ANC 96.3%, Al Jama-ah 0.1%, DA 0.06%, IFP 0.04%); ANC median 75 → 74
— the ANC sat exactly on the 74/75 largest-remainder boundary, so the small
quota recomputations tip the printed median while the mean barely moves;
P(ANC+DA) 88.5% → 87.6%; DA 79 and all other medians unchanged; council 270
and threshold 136 in every draw. **Correction to §1.18:** it quoted "P(ANC+DA)
86.5%" — that was the pre-adoption expand-rule figure; the adopted deduct run
gave 88.5%, and the ≥ trigger now gives 87.6%.

**`p_overhang` retired.** The summary's `p_overhang` was `(council>270)`,
structurally 0.0 under deduct, printed beside per-party excessive rates —
a self-contradiction waiting for a downstream consumer. Replaced by
`p_excessive_any` (share of draws in which any party triggers item 16);
`forecast_summary.json` schema and consumers updated.

**Page furniture repaired (the audit's promotion blockers).** Dev
interactive: duplicate `scenarioJson` id removed (the bottom "Reproduce this
exactly" section rendered a permanently empty textarea); the near-miss
footnote was computed then unconditionally overwritten — dead since the
coalition-table redesign, now rendered; walk-out column no longer silently
drops partners with 10–50% survival — rescues are searched for every exit
below 50% and fatal exits are named ("X exit breaks it"); the excessive-seats
tile now shows the ANC's own rate rather than the any-party rate; the
kingmaker caption describes the normalised Banzhaf index it actually plots;
"Others"/"New entrant" are flagged as synthetic partners in the coalition
footnote; the colophon cites the amended statute instead of "§3.7 fine print
unverified". Sheet: the two-ballots strip now sums exactly 135 + 135 = 270
(largest-remainder rounding with an explicit Smaller-parties bucket; list =
council − wards by construction) and the ANC-list figcaption is computed from
the data (currently zero: 74 = 74). METHODOLOGY.md §5A/§5B/item J rewritten
to the deduct statute and current run; POLLING.md now carries the Ipsos
PA 4 / IFP 2 minor-party provenance. The draft page's GEN block, stale since
the defaults adoption, is regenerated alongside the sheet's.

**Acknowledged, not fixed (unreachable or second-order):** JS `allocate`'s
zero-vote branch divergence from Python (needs vote totals below the seat
count); combined votes from drawn targets vs converged IPF output (bounded by
IPF tolerance); `POLLING_SPAN`/`_leanSign` dead code in the JS engine.

### 1.20 Who-turns-out tilts: turnout as people, not parameters ✅

**The interactive's turnout dials were parameter-shaped** ("50% toward 2021",
"σ 0.08") while the question readers bring is people-shaped — the DA's own
campaign line is that ~490,000 DA votes on both ballots deliver an outright
majority (Zille, Business Day 2026-03-01; 500,000 in later coverage).
Replaced with two sliders — voters in ANC-leaning wards and in DA-leaning
wards each move between **stay home** (that area's worst local-election
turnout on record) and **all turn out** (its 2024 national-election turnout,
which is what "all our voters" means in practice) — plus presets "Every DA
voter turns out" and "The ANC machine delivers". Anchors are computed per VD
from `turnout.csv` (2024 NPE; min of 2011/2016/2021 LGE) and carried to the
ward pack as `v24`/`vlo`; citywide they are 60.5% and 42.5% against a ~42%
baseline — the "stay home" floor nearly coincides with the forecast baseline
because the model already assumes near-record-low turnout. New scenario keys
`turnout_tilt_anc`/`turnout_tilt_da` ∈ [−1, 1], default 0 (published forecast
unchanged); VD/ward lean = which bloc's 2024 base share leads.

**The tilt is compositional by design.** First implementation applied the
tilt to the IPF weights — and the calibration absorbed it (citywide shares
are pinned to the drawn targets, so a DA-ward surge just deflated DA's
within-ward shares; the "test" answered itself). Correct construction:
within-area shares stay as the scenario calibrated them (IPF runs on the
untilted weights) and the tilt changes who casts votes, so the citywide
result moves mechanically. Python: `weight_cal` (untilted) for
`solve_and_predict`, tilted `weight` for vote aggregation. JS: per-party
shift = tilted/untilted ward-geography overlap applied to the combined vote.

**Measured (JS engine, 1,500 draws, defaults otherwise):** every DA-leaning
ward at national-election turnout lifts the DA 79 → 84 seats and P(largest)
66 → 76% — and P(any party governs alone) stays 0.0%: the claim fails by
roughly fifty seats. Adding "ANC areas stay home" changes nothing (their
baseline already is the record low). The mirror surge lifts the ANC only
+1 seat — it is seat-capped at its ward wins by the excessive-seats law —
while its bloc partners gain and the DA falls to 70. Python-engine
confirmation run alongside; page controls regrouped (who-shows-up sliders
headline the Turnout group; split-predictability, by-election weight and the
old map/scatter dials under a collapsed Fine-tuning; MK/PA judgement calls
collapsible).

### 1.21 Turnout tilts made party-selective; the 490k claim gets its own section ✅ *supersedes 1.20's measured numbers*

**User critique, accepted:** the 1.20 tilt was a *ward-level* tide — raising a
DA-leaning ward's turnout also cast more votes for the ANC voters living in
it, which contradicts the story being tested ("one bloc's voters turn out").
Reworked in both engines: the tilt now scales the target **bloc's
supporters** — wherever in the city they live — between the draw's turnout
and the anchors, leaving their neighbours untouched. Mechanically: within-VD
shares stay as the scenario calibrated them (IPF on untilted weights); per-VD
per-party scale `1 + |t|·(anchor/t_draw − 1)` applied to the bloc's columns
at vote aggregation and in the ward-winner tallies (so a mobilised camp can
now flip wards, which the ward-tide version could not do honestly). Direction
clamps: "all turn out" can only add votes, "stay home" only remove them —
needed because the worst-LGE anchor (42.5% citywide) sits a hair *above* the
forecast baseline (41.9%): the model already assumes near-record-low turnout,
so "their voters stay home" is not a scenario, it is the baseline. Sliders
relabelled "ANC-bloc voters (ANC · EFF · MK)" / "DA-bloc voters (DA ·
ActionSA)"; readouts report the change in that bloc's cast votes (+49% / +38%
at the all-out anchors). Non-bloc parties are untouched by the dials, said on
the page.

**Superseding measurements (1,500 draws each, both engines agree):**
- *Every DA-camp voter at 2024 national turnout:* DA polls ~436,000 of a
  ~1.16 m poll (~38%) — note it still does not reach the claim's own 490,000
  — and takes a median **90 seats [62–118]**; P(largest) 85%; P(governs
  alone) ~0.1–0.3%. The 490k claim falls 46 seats short, and even the
  luckiest run in 5,000 is 18 short. Adding "ANC-bloc voters stay home"
  changes nothing (see the clamp note above).
- *The ANC machine delivers:* ANC 74 → **81 [66–97]** — more responsive than
  the ward-tide version because its supporters' surge now defends and takes
  wards — but the larger gains still flow to the EFF (27 → 35) and MK
  (19 → 25), with the DA down to 67 and P(ANC+DA) at 74%.

**Publication changes:** the 490k verdict moved out of the sidebar into a
"The parties' claims — tested" section on both the forecast page and the
interactive results column (three numbered steps: half-of-the-wrong-number /
436k-not-490k / 38%-of-votes-buys-fewer-seats, with the run-it-yourself
presets); headline and standfirst reworded (rev 4: "Nobody will win
Johannesburg — and an obscure voting law will give the ANC more seats than
expected"); dateline strip moved below the colophon on all pages; mobile
width fixed (h1 `text-wrap:balance` was shortening lines; ≤560px padding
tightened); base `a{color}` element rule added to every stylesheet so no
future link can fall back to unreadable browser-default blue. Change-badge
system from earlier today (▲/▼ vs previous run + sticky summary bar) applies
to all of these experiments.

### 1.22 The regime comparison: three answers to excessive seats, one set of draws ✅

The legacy `expand` rule earned its keep as a counterfactual: it is exactly
old Germany's *Überhangmandate* (pre-2013 — winner keeps the surplus, the
chamber grows, nobody else loses a seat). Added the third answer as
`overhang_rule="level"` — modern Germany's *Ausgleichsmandate*: the council
grows until every ward winner is covered proportionally. Published as "If we
handled excessive seats the German way" on the forecast page: the SAME 5,000
draws (seed 20261104) scored under all three rules, table generated by
`render_sheet.py` from `src/overhang_regimes.py` outputs (never hand-copied).

| rule | council (med) | majority | ANC | ANC share | DA |
|---|---|---|---|---|---|
| SA law (deduct) | 270 | 136 | 74 | 27.4% | 79 |
| Old Germany (expand) | 279 | 140 | 74 | 26.5% | 82 |
| Modern Germany (level) | 308 | 155 | 74 | 24.0% | 92 |

The ANC's ward wins are identical in every column — the rules differ only in
who absorbs the surplus: the other parties (SA), everyone a little (old
Germany), or the chamber itself (modern Germany, ANC diluted to its true
~24% weight). Note the levelled council is 308, not the ~338 a naive
wins÷share division suggests — largest-remainder covers the wards earlier.
Coda on the page: Germany abolished overhang outright in 2023 (unfunded
constituency winners simply are not seated), a reading no South African
lawyer has yet proposed.

### 1.23 Site redesign round: bands and roll-ups, hi-anchor turnout, symmetric crossover, four-regime table ✅ *supersedes 1.21's claim numbers*

**Model changes (user-resolved 2026-08-07):**
- *Turnout "all turn out" anchor* moved from each area's 2024 national
  turnout to its **highest turnout on record** (max over 2011–2024, national
  and local; per VD/ward `t_hi`/`vhi`). "Stay home" unchanged (worst LGE on
  record). Clamps unchanged (up only adds, down only removes).
- *Voter cross-over goes symmetric lost-votes*: left now mirrors right — a
  share of the DA bloc's losses (local share below its national base)
  crossing to the ANC bloc — replacing the old redirect-the-bounce transfer.
  Honest consequence, stated on the page: the DA-bloc shift range observed
  2006–2024 is +5…+14 points and bounds every simulation, so the left side
  currently moves nothing. It exists for symmetry, and for the day the
  record changes. VF+ stays outside the DA bloc (user-confirmed).
- *Fourth regime published*: the `cap` rule is Germany-2023 (fixed 270,
  wins not seated beyond entitlement); `overhang_regimes.py` runs it and the
  forecast's table is now four columns — SA law 270/136 · Germany 2000
  279/140 · Germany 2015 308/155 · Germany 2023 270/136 (ANC at its pure
  proportional share).

**Superseding claim measurements (1,500 draws, hi-anchor):** every DA-camp
voter at the record anchor now *does* clear Zille's number — ~524,000 DA
votes (F_DA ×1.64) — and the claim still fails: the poll swells to ~1.29 m,
the majority line moves to ~644,000, the DA's 41% buys a median **97 of 136
[68–131]** after the ANC's ward floor (~62 wards on an entitlement near 49)
is deducted. Short by 39; the luckiest simulation in 5,000 is still five
short. Claims section rewritten accordingly (step 2 is now "even reaching
the number doesn't make it half").

**Presentation:** both pages restructured into roll-up sections (forecast:
The forecast / Commentary / About-the-model bands with expand-collapse-all;
interactive: presets as an always-visible strip, left bar retitled "Change
the variables" with Party levels → Turnout → Poll weighting → Judgement
calls → Wildcard entrants → Bloc shifts → Fine-tuning, forecast-position
notches on every slider, values in accent below); stat boxes redesigned
(orange %-plus-"Chance" line, six boxes ending in a 270·136 info box; DA-
minority tile retired to its section); the interactive gained the live
135+135=270 strip; map keys speak in Safe/strongly leaning/leaning/toss-up;
headline split with a smaller second sentence; "simulation" replaces "run",
"slider" replaces "dial"; wide-screen width tier added; party colour chips
in the regime table.

## 2. Obstacles and how they were handled

| # | Obstacle | Resolution | Status |
|---|---|---|---|
| O1 | `results.elections.org.za` and `www.elections.org.za` return 403 to curl regardless of UA/referer | Generated *report files* are served straight through and are curl-able; only the SPA shell and bulk zips are gated. Bulk zips fetched by navigating a real browser tab. | ✅ |
| O2 | Browser downloads land in `~/Downloads`, which macOS TCC blocked from the terminal | User granted Full Disk Access. This blocked the project for a full session. | ✅ |
| O3 | By-election reports reachable only via per-session `ReportViewer?_f=<token>` links; tokens fail outside the browser that made them | Bypassed entirely — the by-election *dashboard* is backed by static JSON needing no session, and its per-municipality file is *richer* than the PDF (VD level, all parties, candidate names). | ✅ |
| O4 | Election IDs are not years and differ per ballot | Read off the portal's dropdown. 2019 Provincial is **827**, not 700 — guessing from the National id would have failed silently. Recorded in `SOURCES.md`. | ✅ |
| O5 | 2014 NPE 404s on the results-portal pattern | Published on the other host (`www.elections.org.za/content/Elections/Downloadable-results/...`), found via the portal UI. | ✅ |
| O6 | Historic VD boundaries needed to verify the concordance geometrically | Not published anywhere reachable — checked the MDB's full 43-service ArcGIS list, both DCAT catalogues, ArcGIS Online search, the IEC's GeoServer, and an Internet Archive CDX sweep of both hosts. | 🔴 task #18 |
| O7 | Census 2022 Small Area Layer (income, dwelling, employment) not downloadable | Stats SA supplies on request only. Ward-level product acquired as partial substitute — age/sex/population group, no income or employment. | 🔴 task #16 |
| O8 | IEC publishes registration by age/sex only to municipality level, server-rendered, no API | VD-level registration *totals* come from the result files and the VD layer. Ward-level age/sex substituted from the census product. | 🟡 |
| O9 | 2026 registration-weekend deltas not published | Nothing to do but wait; §3.2 feeds them in when available. | 🔴 external |
| O10 | Sources disappear — the MDB has already retired the per-municipality shapefile downloads its old site served | `src/archive.py` records every file with SHA-256 and provenance; the manifest is committed even though `data/` is gitignored. `--verify` detects drift. | ✅ |

---

## 3. Data traps found (each corrupts silently rather than erroring)

| Trap | Where | Handling |
|---|---|---|
| Unquoted commas in voting-station names shift every later column, **while row width stays constant** because a trailing pad column absorbs it | 2019 NPE, e.g. JHB VD 32851278 `TENT (TSUTSUMANE, EXT 7 )` | Rows anchored at both ends, not by position. A column-count check does *not* catch this. |
| Encoding drift | 2019 is DOS CP850 (`CAF\x90` = CAFÉ), 2011 is UTF-16, rest UTF-8 | BOM check, then decode-probe |
| Header drift and a volatile `Generated Datetime: <timestamp>` header | across years | header normalisation |
| `VALID VOTES` / `TotalValidVotes` is the *party's* votes, not the VD total | 2014 NPE and all LGE files | VD total recomputed by summing parties |
| Initials-derived party codes collide | `ARISE SOUTH AFRICA` → `ASA` merged into ActionSA; `ALLIED MOVEMENT FOR CHANGE` → `AMC` merged into `AFRICAN MOVEMENT CONGRESS` | Derived codes are now full names; the builder *fails* on any merge via a derived code |
| Comparing station names against a file that has none flags everything | 2014 bulk carries no station names, so every 2011/2014 VD flagged as changed | compare only when both sides name a station |
| `REGPOP` on the 2026 VD layer is a **2024** snapshot (sums to 2,348,781) | boundary layer | documented; do not read as current registration |

---

## 4. Assumption and mitigation register

The model's live risks, and what is being done about each.

### R1 — VD boundary stability ✅ *tested in fold 2, immaterial*

**Resolved empirically (task #17).** Fold 2 was run three ways — all VDs, the 93
flagged VDs down-weighted at `w_split` 0.6, and those VDs excluded outright:

| | ward winner | seat MAE | total seat error | θ_ANC |
|---|---|---|---|---|
| all VDs | 128/135 | 0.50 | 12 | 1.32 |
| suspect down-weighted | 129/135 | 0.50 | 12 | 1.32 |
| suspect excluded | 127/134 | 0.43 | 10 | 1.30 |

Citywide party errors are identical to 0.01pp across all three, θ moves by at
most 0.03, and the ward-winner count moves by one either way. **The assumption is
not doing meaningful work**, so the missing historic VD boundaries (task #18) do
not block any conclusion the model draws. Task #18 stays open as a nice-to-have,
downgraded from a blocker.

The flags themselves are retained — they cost nothing and would catch a future
delimitation that *did* move VDs materially.

*Original entry, kept for the reasoning:*

### R1(prior) — why this looked like the highest residual risk 🟡

**Assumption.** A VD keeping its number kept its catchment, so historic votes
describe the same ground as the 2026 VD they are matched to.

**Why it may fail.** When a VD splits, one child conventionally keeps the
parent's number over a *smaller* area. An unchanged number can hide a changed
catchment. This cannot be checked geometrically — no historic VD boundaries are
published (O6).

**Evidence for.** Two independent proxies. Registration tracks the citywide
trend (median per-VD ratio 0.97–0.99; only 0–2 VDs per transition lose >30%
relative, where routine carve-ups would leave a fat left tail). And ~90% of VDs
keep the same voting station between consecutive elections, 99.1% for 2024→2026.

**Mitigation in place.** Every VD carries a `stability` flag (registration drift
>30% against citywide, or changed voting station), putting 2.8–13.1% of votes per
election under suspicion. Suspect VDs can be down-weighted via `w_split`.

**Mitigation outstanding.** Task #17: run fold 2 three ways — all VDs, suspect
down-weighted, suspect excluded — and compare θ. If estimates move materially the
assumption is doing real work and boundaries must be sourced (task #18). If they
barely move, the assumption is *tested* rather than hoped.

**Exposure is asymmetric.** The risk falls on the backtest folds, which compare
VD shares across time. The 2026 projection is much less exposed, because the 2026
VD set *is* the 2024 set.

### R2 — Which turnout specification 🟡

Covered in 1.2. Mitigation: task #19 scores both forms in the folds on seat
outcome. λ̂ retained for the citywide level either way.

### R3 — Within-VD homogeneity when apportioning split VDs 🟡

**Assumption (A1).** A VD's vote shares are uniform across its ward parts.

**Why it may fail.** Ward boundaries often follow the socioeconomic gradients
that predict voting, so a split VD's parts may genuinely differ.

**Mitigation in place.** Apportionment is weighted by *registered voters* per
part, not area, which is what A1 itself asks for; 59 zero-voter slivers correctly
get zero weight. Split-derived observations are flagged for `w_split`
down-weighting. Affects 181 of 865 VDs.

**Residual.** Registration weighting fixes the *size* of each part, not
differences in political composition between them. Irreducible without
sub-VD data.

### R4 — Missing covariates for the turnout sub-model 🔴

Income, dwelling type and employment are unavailable (O7). The turnout
sub-model can be built on age/sex/population group and refined later. Ward-level
rather than small-area granularity also limits the covariate term's resolution.

### R5 — Concordance leakage 🟡 *small and quantified*

0.21–0.45% of each election's votes sit in VDs that no longer exist (mostly tents
and temporary stations). Recorded as `method='unmatched'` rather than dropped, so
the loss stays visible downstream instead of becoming a silent shortfall.

### R7 — New-entrant blindness 🟡 *structural, quantified in fold 1*

**The problem.** §4.3 warns that new parties are where the model has no
information. Fold 1 measures it. Every established party's citywide share is
reproduced to within 0.03pp, ward winners are called correctly in 132 of 135
wards, and seat MAE is 0.71 — but the model misses **the AIC entirely (4 actual
seats, 0 predicted)** and Al Jama-ah (1 actual, 0 predicted), because both polled
0.00% in the 2014 baseline. It also invents single seats for six minor parties
that faded.

Total absolute seat error is 12, of which 5 is new-entrant blindness and most of
the rest is small-party churn in the largest-remainder tail.

**Why this matters more for 2026 than the headline suggests.** Every fold
contains a new entrant, and so does the live case (MK). §4.3's point stands and
is now measured rather than asserted: the model is near-exact on parties it has
seen and blind to those it has not.

**Mitigation.** θ for new entrants is a pure prior and must be treated as a
scenario lever, not an estimate. §4.3's conclusion — that the honest output is a
distribution over coalition viability rather than a seat forecast — is the right
response to this, and fold 1 supports it.

### R6 — Single-cycle inference 🟡

Several parameters rest on two observed NPE→LGE transitions, one of which (2021)
was Covid-affected and anomalously deep. `w_recency` exists to hedge this but
cannot be calibrated from one prior cycle. Treat 2021-derived defaults as scenario
levers, not estimates — which is what §3.5 already says, and the turnout work
confirms was wise.

---

## 5. Decisions taken

| Decision | Rationale |
|---|---|
| Keep canonical party code separate from modelling bloc | Seat allocation needs every party's identity — the IFP, VF+, ACDP and AIC all won CoJ seats in 2021. `OTHER` means "not separately modelled", never "discarded". |
| Derived party codes are full names, not initials | Initials collided and silently merged distinct parties. Verbosity costs nothing for residual-bucket parties; collisions cost a lot. |
| Merging raw party strings is only valid when explicit | The crosswalk builder fails on any merge that happens through a derived code. |
| Concordance keys on VD number, not geometry | 98.8–100% coverage, <0.5% leakage, and no historic geometry exists to intersect against. Risk carried as R1 with flags. |
| Apportion split VDs by registered voters, not area | A1 asks for it, the data permits it, and it correctly zero-weights 59 slivers. |
| Turnout defined as votes cast / registered, higher ballot at an LGE | MEC7 is not published per VD. Runs ~0.05pp below the IEC's published figure; λ is a ratio so a consistent bias largely divides out. Consistency across elections beats matching the headline. |
| Unmatched VDs recorded, not dropped | A silent shortfall is worse than a visible one. |
| Archive manifest committed though data is gitignored | Sources are not durable (O10). |
| §0 treated as a correction, §3.3 as a suggestion | §0 is verified against the IEC's own arithmetic three times over; §3.3 rests on two cycles, one anomalous. Different evidence, different confidence. |
| Coalition arithmetic is never pre-filtered on plausibility | Review E1: the filtered version published a false conclusion. Feasibility is annotation (minority-class opposition sets are editable scenarios), arithmetic is exhaustive. |
| Overhang expands the council (`expand`), with a `cap` counterfactual toggle | §3.7's reading of Schedule 1; the statutory redistribution fine print is unverified against an IEC worked example, so both bounds ship. |
| Evidence tilts priors, never replaces them | By-election deltas and polling move the *modes*, clamped to §3.5's historical ranges; `w_bye` and the polling lever expose the weights. A stronghold swing cannot claim an absurd citywide level. |
| Every review-flagged assumption is a user-facing control | `forecast-interactive.html` sliders share `montecarlo.DEFAULTS`' schema; a slider position round-trips to `--config scenario.json`. Interacting with the sensitivity is how a reader learns what matters. |

---

## 6. What still needs a person

- **Task #16** — Census 2022 Small Area Layer: **requested from Stats SA 2026-08-05** (email sent), awaiting reply.
- **Task #18** — historic VD boundaries: **requested from the IEC Delimitation Directorate 2026-08-05** (email sent), awaiting reply. Would convert R1 from mitigated to resolved.
- **Task #20** — Schedule 1 overhang worked example: **four-question request sent to the IEC 2026-08-05**, awaiting reply. In parallel, an archive hunt for a real historical overhang municipality is running. P(overhang) ~72–96% across readings; the answer moves P(ANC+DA) across 72–91% (§1.16).
- **External** — 2026 registration-weekend figures, when published.
