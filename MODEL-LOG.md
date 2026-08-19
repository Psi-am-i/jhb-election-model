# Johannesburg Election Model

A voting-district model of the City of Johannesburg — 5,000 simulations over 865 voting districts, both ballots, the statutory seat formula, and the coalition arithmetic it permits. The forecast, the machinery, and the full warts-and-all record of how it was built, reviewed, broken and corrected.

# Log — findings, obstacles, decisions, mitigations

A running record of what was built, what got in the way, what was decided and
why. Two purposes: to feed the eventual description of the model, and to keep an
honest register of the assumptions it rests on so they can be mitigated rather
than forgotten.

Append to this file as work proceeds. `SOURCES.md` records *where data came
from*; this records *what we learned and chose*.

**The history starts with the plan.** Appendix A is the rev-2 build plan as it
was written, before any of it was implemented, and every numbered finding below
is a delta from it. Several of its central assumptions turned out to be wrong —
seats follow the combined ward+PR vote rather than the PR ballot (1.1), θ has
two incompatible definitions and §3.5 quotes the wrong one (1.6), §3.4(b) pairs
binary logit with softmax (1.5), multiplicative θ cannot create a party from
zero (1.11) — and the plan is kept unedited because the divergence *is* the
record. A plan quietly corrected after the fact teaches nobody anything.

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
[68–131]** after the ANC's ward floor (still firing in 90% of surge draws:
~62 wards on an entitlement of about 50) is deducted. Short by 39 at the
median; the surge hands the DA an outright majority in only ~3% of
simulations (47/1,500; max draw 155). Triple-check correction 2026-08-07:
an earlier wording called the 95th percentile (131) "the luckiest
simulation" — the tail above it exists and occasionally clears 136; the
page now says "about 3 in 100". Claims section rewritten accordingly
(step 2 is "even reaching the number doesn't make it half").

**Steelman (user-requested, 2026-08-07).** Zille's exact words (Business Day
2026-03-01: "We need 490,000 registered DA voters to go vote DA, if they do
that we win an outright majority") name no denominator. Most charitable
reading: against 2021's per-ballot poll (A/2 = 1,834,260/2 ≈ 917k), 490k is
53.4% — internally coherent ONLY if the poll stays frozen while the DA
doubles, i.e. every other party combined sheds ~190k votes (−28% vs 2021).
No mechanism in the record. Sharper still: votes-majority ≠ seats-majority
under the amended Schedule 1 — allocator experiment (surge composition, ANC
wall fixed at 62 wards): DA at 50% of the vote → 123 seats; 54% → 131;
solving, ~57% needed for 136. Confirmed in the draws: the 47/1,500 surge
simulations where the DA reaches 136 are those where its turnout surge flips
ANC stronghold wards (ANC median 47 seats there vs 66 elsewhere). The
claim's only true worlds are an evidence-free frozen poll, or breaking the
ANC's ward wall — which is a persuasion story, not a turnout story.
Published as "Could she still be right?" in the claims section.

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

### 1.24 Phase 2 approved: one engine, many cities — and the stat-provenance layer it needs ✅ *plan filed as `EXPANSION.md`*

`whysoserious.city` becomes a portal to per-city models. Planning that
exposed a defect that is already live in Johannesburg, and it is the more
important half of the work.

**Model results are typed into prose by hand, so they go stale silently.**
A full inventory found ~40 restatements of model quantities outside the
generated blocks, many duplicated across files (587,000 ×3, "129 of 135"
×3, "73 wards / 65 entitlement" ×3, "865 VDs" ×6, "5,000 simulations" ×5) —
and four that are simply **wrong on the published site**: the standfirst's
"DA finishing first 54%" (model: 62%), "roughly 73 wards on a 65-seat
entitlement in six of every seven simulations" (model: ~74 wards, ~59
entitlement, 96%), the portal dateline's pre-rev-3 "majority bar to ~141"
(the council is fixed at 270), and `review.md`'s "largest party in 63%",
which contradicts the sheet's own 54%.

**The fix is not simply to auto-update them.** A number inside a dated
argument must not move underneath the argument: "short by 39 seats" is only
true while the DA's median is 97. So every reused stat is tagged:

- **`free`** — recomputed each build; a statement of what the model says now.
- **`fixed`** — pinned to the moment it was written, with the run that
  produced it; the build reports **drift** when the live model moves away
  from the pin (per-token tolerance), so a human re-pins or rewrites the
  argument. Drift warns, never blocks.

Both modes carry source and insertion timestamp. The registry is per-city
YAML covering **numbers and strings** — the headline's "the ANC" is a model
result too, and would be wrong if another party started overhanging.
Rendered tokens carry their provenance in data-attributes: pinned figures
read plainly but reveal "pinned 7 Aug 2026 · model now says 103" on hover.

**Also found, to be fixed by the same refactor:** the interactive template
hand-mirrors `montecarlo.DEFAULTS` in three places (JS constants, 19 slider
attribute triples, `DEFAULT_CFG`) with a fourth copy in `leverage.py` — and
they have already drifted (`POLLING_SPAN` is 4 in the JS, 8.0 in Python).
Four parallel copies of the party chips/names exist across the renderers.
`build_interactive.py` will generate all of it from the city config.

**Structure of the expansion** (decisions with the user, 2026-08-07): one
repo, one Worker, `cities/<code>.toml` configs, `site/<slug>/` builds, a
newsdesk routine per city, a place-derived palette per city, and **Tshwane
as the pilot** — 107 wards, 778 VDs, a genuinely different party universe
(VF+ 7.8% first-class, PA marginal) and a live ActionSA-led coalition under
strain. Data for all eight metros is already in hand (`SOURCES.md`).

**Standing rule for the refactor: Johannesburg's forecast may not move.**
Every step re-runs Joburg and asserts `forecast_summary.json` is unchanged
(DA 79 / ANC 74, P(ANC+DA) 87.6%, P(excessive) 96.3%). The engine gets
generalised; the numbers do not.

### 1.25 Blocs tested out of sample: the structure is not a predictive win ✅

The bloc grouping had been argued for from spatial evidence (§1.18) but never
tested against the thing it exists to do — predict. `fold.py` gained a third
transfer mode, `--transfer bloc`, which carries the *bloc's* share-weighted θ
and applies it to every member, instead of carrying each party's own θ. The
default is unchanged, so **the published forecast is untouched**; this is a
diagnostic, not a model change.

**Result: the two folds disagree, and neither is decisive.** VD MAE is the
PR ballot; both parameter files were refit from scratch immediately before
these runs (see the defect below, which is why that sentence is here).

| Fold | per-party θ | bloc θ |
|---|---|---|
| 2019→2021 (θ from 2014→2016) | seat error 126, wards 127/135, VD MAE 0.83pp | 126, **126/135** (worse), 0.84pp |
| 2014→2016 (θ from 2019→2021) | seat error 94, wards 131/135, VD MAE 1.18pp | 94, **133/135** (better), 1.19pp |

Four things had to be understood before those numbers meant anything:

1. **Total seat error cannot see this test at all.** A bloc transfer conserves
   the bloc's total and only changes the split, so a gain in one member is
   paid for by the other, and the total is identical by construction in both
   folds. Predicting 2021, going bloc-wise moved the ANC from +15 to +24 seats
   and the EFF from +13 to +4 — the same 28, redistributed. Predicting 2016 it
   moved the ANC from −13 to −8 and the EFF from −8 to −13 — the same 21. The
   only metrics with any power here are ward winners and VD MAE.
2. **The 2019→2021 fold is dominated by a problem that is not bloc structure.**
   44 of its 126 seat error is ActionSA, which did not exist in 2019 and is
   therefore predicted at zero; the ANC and DA overshoots are largely that 18%
   of the vote being redistributed to whoever was on the ballot. That fold
   measures new-entrant blindness (R7), and bloc structure only faintly.
3. **The folds point opposite ways, and by small margins.** Predicting 2021,
   the bloc transfer calls one more ward wrong; predicting 2016, it calls two
   more ward *right*. VD MAE is worse under the bloc transfer in both folds,
   by 0.01pp — which is to say, by nothing.
4. **The DA/ActionSA pair yields no observation.** ActionSA's θ of 1.0 is the
   default for a party with no prior election, not a measurement, so the
   test's second bloc is inert in both folds.

On the substantive question — do bloc members move together? — the two
transitions genuinely disagree. Measured as the citywide LGE/NPE ratio (raw
θ), into 2021 the ANC was 0.670 and the EFF 0.681, 1.7% apart: they moved
together, as a shared pool of voters predicts. Into 2016 the ANC was 0.859
and the EFF 1.079, 25.6% apart and in opposite directions. One observation
each way.

**Conclusion, stated as weakly as the evidence deserves.** The bloc structure
is not shown to improve prediction, and is not shown to harm it. With two
usable transitions split one-all it *cannot* be, and no amount of care with
the harness will fix a sample of two. This is precisely why the grouping
remains a documented judgement exposed as a slider (§1.4, A7) rather than a
fitted parameter — and it is now a judgement with a published null result
behind it rather than an untested assumption. `--transfer bloc` stays in the
tree so the test re-runs for free on any new city or any new election.

**A defect found while running this, and a second left open.** The first draft
of this entry reported the 2014→2016 fold as *identical to two decimals* under
both transfer modes — seat error 60, 134/135 wards. That was wrong, and the
way it was wrong is worth recording. `fold.py` wrote its fitted parameters to
`data/processed/fold{N}_parameters.csv` with no city in the path, and read
`--fit-from` back from the same place, so **any Tshwane fold run silently
overwrote Johannesburg's fitted parameters** — and `fold1_parameters.csv` is
what `montecarlo.py`, `export_interactive.py` and `leverage.py` read to build
the live forecast. The file on disk was months-stale relative to the pipeline
that produced the rest of the run. Both call sites now use `City.processed`
(O11), which keeps Johannesburg on the legacy path and puts every other city
under `data/processed/<slug>/`; verified by running Tshwane's fold 2 and
confirming Joburg's file was untouched, and the whole Monte Carlo was re-run
afterwards to confirm `forecast_summary.json` is byte-identical to the
published one. The published forecast was never contaminated — only this
diagnostic was — but it was one `--city tshwane --fold 1` away from being so.

The second defect is **open**. The bloc transfer averages *calibrated* θ,
which is what `load_parameters` returns, and fold 2's calibrated θ sits 4–7×
below its raw θ (ANC raw 0.670 → calibrated 0.129; DA 0.859 → 0.116; EFF
0.681 → 0.166) while fold 1's calibrated θ tracks its raw θ closely (ANC
0.859 → 0.832). Fold 2's in-sample fit still reproduces citywide shares to
+0.00pp, so the calibration converged — but a solution that far from raw
suggests the calibrated θ vector is only weakly identified once the universe
holds 68 parties and an 18% party with a zero base, because within-VD
renormalisation absorbs much of a uniform rescaling. If so, *transferring*
calibrated θ across folds depends on which solution the solver happened to
land on, and every `--fit-from` result inherits that. This does not affect the
live forecast, which never transfers θ. Registered as R8; until it is
settled, `--fit-from` numbers should be treated as indicative, not exact.

### 1.26 The splinter question: how a judgement became a measurement 🟡 *2026-08-09/10*

This entry is deliberately a narrative rather than a result. It records a
single line of enquiry that started as a check on §1.25 and ended by
overturning a published claim, a bloc assignment and three of my own
intermediate conclusions. The false steps are kept because the sequence is
the point: each wrong answer came from too small a sample, and each was
corrected by getting more data rather than by thinking harder.

**Where it started: verifying §1.25 instead of trusting it.** Re-running the
bloc test's own numbers reproduced fold 2 exactly and fold 1 not at all. The
cause was a defect, not a mistake in the arithmetic: `fold.py` wrote and read
fitted parameters at a path with no city in it, so a Tshwane run silently
overwrote Johannesburg's — and `fold1_parameters.csv` is what the live
forecast reads (O11). §1.25's second fold had been written up from a stale
file. Corrected, the bloc transfer is *better* on that fold (133/135 wards
against 131) and worse on the other, which is what §1.25 now says.

**The question that opened everything.** The forecast's treatment of MK rests
on θ_MK = 0.60 — how much of its 2024 national vote it keeps at a local
election — with a hard cap of 1.00. Where does 0.60 come from? Nowhere
measurable. So: what has actually happened to parties formed by a defector
facing their first local election?

**Sample of one, and a wrong conclusion.** Johannesburg had exactly one clean
precedent, the EFF: 10.13% in 2014 → 11.09% in 2016, θ = 1.09, contesting all
135 wards. On that basis I argued MK's 0.60 was indefensible and should rise
to ~0.95. That was wrong, and it was wrong because n=1.

**Sample of four, and a different wrong conclusion.** COPE was the obvious
adversarial case — a defector-led party that fielded a full slate (130/130)
and still fell to 1.15%. Testing it needed the 2009 NPE, which the project did
not hold and which is on none of the documented routes. It turned out the IEC
publishes every election from 1999 at an unlinked URL
(`/content/uploadedfiles/{YYYY} {NPE|LGE}.zip`, DATA-QUALITY 10c). With 2009
in hand COPE reads θ = **0.12** — a ninefold difference from the EFF at
almost identical debut size and identical contestation. Four observations
then showed 0.04, 0.12, 1.09, 1.20 and I called the distribution bimodal.

**Sample of six, and the bimodality dissolved.** Ingesting the rest of the
tail added UDM (0.29) and ID (0.85), filling the gap. Bimodality withdrawn.

**Sample of twenty-four, and it came back for a good reason.** The archives
are national, so the same splinter can be measured in all eight metros. Two
things then became visible that no single city could show:

| splinter | JHB | TSH | EKU | CPT | ETH | NMA | MAN | BUF | range |
|---|---|---|---|---|---|---|---|---|---|
| COPE 09→11 | 0.12 | 0.12 | 0.18 | 0.16 | 0.19 | 0.28 | 0.24 | 0.22 | **0.12–0.28** |
| ID 04→06 | 0.86 | 0.73 | 0.99 | 1.37 | 1.17 | 1.22 | 0.80 | 0.65 | **0.65–1.37** |
| EFF 14→16 | 1.08 | 1.01 | 1.05 | 1.24 | 1.49 | 1.21 | 1.03 | 1.50 | **1.01–1.50** |

Within a party θ barely moves across eight cities; between parties it moves by
a factor of ten. **The branch is a national property of the party, not a local
one** — which is what makes it a single judgement rather than one per city.
The middle (0.29–0.64) is empty in 24 observations. The two earlier samples
were too small and too polluted by parties of noise size (AGANG 8,124 votes,
GOOD 4,677) to show either fact.

**What is now rule and what is still judgement.**

* Contestation is a **ceiling, not a predictor**: under ~20% of wards, θ never
  exceeded 0.29; above ~70%, it ranges the full 0.12–1.50.
* Debut size matters within the surviving branch: the EFF's four largest-base
  metros landed at 1.01, 1.03, 1.05, 1.08 — mean reversion, and the relevant
  comparator for MK, which debuts at 12.2% of Johannesburg.
* The one free parameter left is whether the leadership holds together, which
  is not measurable in advance. `montecarlo.py` gained a `splinter` scenario
  key implementing exactly this: draw a branch, then draw θ from that branch's
  measured range. Default is empty, so the published forecast is unchanged.

At `fracture_prob` 0.33 (the base rate: one of three meaningful splinters
fractured) MK's 90% interval widens from 12–28 seats to 3–37, P(MK ≤ 5) goes
from 0.0% to 14.8% and P(MK ≥ 30) from 3.5% to 20.0%. The current model
assigns almost no probability to either of the two things that actually
happen to splinters.

**Then ActionSA broke the other half of the rule.** The natural companion
judgement was that the splinter takes votes from the party its leader left.
The EFF and COPE both support it — measured NPE to NPE, the ANC loses 0.757pp
per point of EFF and 0.851pp per point of COPE, and the DA loses little or
gains. ActionSA is a DA splinter and does the opposite. Per point of
ActionSA in 2021: **ANC −0.381pp, EFF −0.262pp, DA +0.199pp**. Controlling for
turnout by measuring vote *retention* rather than share, the DA's retention is
uncorrelated with ActionSA's local strength (−0.043) while the ANC's
(−0.290) and the EFF's (−0.264) fall away.

So the origin of the leader does not determine who pays. Two further
measurements say what did:

* **The DA's own retention has a racial gradient and ActionSA's vote has
  none.** The DA kept 56.6% of its 2019 vote in wards under 40% Black African
  and 36.1% in wards over 80% — correlation −0.631 with ward population group
  (Stats SA 2022 ward product, already held in `data/raw/covariates`).
* Every significant party in Johannesburg is racially sorted; ActionSA alone
  is not. Correlation of 2021 PR share with a ward's Black African share:
  **ANC +0.911, EFF +0.850, VF+ −0.554, DA −0.884, ActionSA +0.022.** It
  polled 17.6% / 20.0% / 17.7% across the three ward types.

That is a single candidate with genuinely cross-racial reach, which is rare
enough in this electorate to be treated as a property of the case rather than
a generalisable rule. It is also the mechanism the model has no way to
represent: the grouping of ActionSA with the DA (`DA_BLOC`) means the
forecast funds ActionSA's gains out of DA losses inside a conserved bloc
total, when the measurement says they came from the ANC. The published
methodology already conceded that the DA/ActionSA grouping has no shared
geography and rests instead "on the argument about where defectors go" —
that argument is now contradicted by the defectors' own voters. **This
requires a methodology correction, not only a config change**, and it is
load-bearing: pinning the DA-bloc split alone moves P(ANC+DA majority) from
87.6% to 98.4%.

**A third self-correction.** From ActionSA taking ANC votes I inferred that
the model's spatially flat generic entrant (A6) must be wrong, and that an
entrant should inherit the geography of whoever it recruits from. Measuring
it killed that too: ActionSA's coefficient of variation across voting
districts is **0.44**, the flattest of any significant party (DA 1.04, EFF
0.75, ANC 0.67). The flat-entrant assumption is the closest available match
to the only entrant on record. Who funds a new party and where it is strong
are separate questions, and conflating them was my error.

**One hypothesis left open, and it is testable before the election.** COPE's
debut was flat (CV 0.45) and it collapsed; the EFF's was concentrated (CV
0.69) and it held. If a defined heartland predicts survival, that converts
the leadership judgement into a measurement — and MK's spatial concentration
can be computed from the eight by-elections it has contested since 2024. With
two observations this is a hypothesis, not a finding.

**What the exercise cost and returned.** Five archives ingested
(`src/ingest_historic.py`), all reconciling to the vote, with 2009 checked
against the IEC's own published Johannesburg report. Folds went from two to
five and blind cross-fold validation from two predictions to twelve — which
immediately showed that **2019→2021 transfers worst to every other cycle**
(mean seat error 94 against 2014→2016's 67), a live concern because
`w_recency` weights 2021 at 0.70 and γ falls back to the 2021→2024 fit. Three
data defects were documented (DATA-QUALITY 10a–10c), one of which — thousands
separators in the vote column — silently discards 68.4% of Johannesburg's
2009 votes while dropping only 4.0% of its rows.

### 1.27 Cross-appeal: where a new party's votes land, measured ✅ *2026-08-10*

§1.26 established *how much* a splinter keeps. This is the other half — *where*
it puts it — and unlike the branch question it turned out to be measurable
rather than judged, including for MK.

**The model's assumption, stated.** Prediction is `expit(level + γ·dev)`, so a
party's geography *is* its `dev` column: its deviation from its own citywide
mean, district by district. A party with no baseline has no `dev`, so
`montecarlo.py` set it to zero — a new party lands evenly across the city.
That was never argued for; it was what falls out of having nothing to put
there.

**How I got this wrong twice, and what fixed it.** From the ActionSA finding
(§1.26) I concluded a flat entrant must be wrong and that an entrant should
inherit the geography of whoever it recruits from. I then reversed on the
grounds that ActionSA's coefficient of variation across districts is 0.44, the
flattest of any significant party — so flat looked like the best available
match. Both steps were wrong, and the second was wrong in an instructive way:
**coefficient of variation measures dispersion, and the claim was about
inheritance.** How spread out a party is says nothing about whose map it
copied. The right statistic is the entrant against the parent's map.

**The coefficient.** Take each party's district share over its citywide share,
so the index has mean 1, and fit

    entrant_index(i) = (1 − k) · parent_index(i) + k

`k = 0` is the parent's geography exactly; `k = 1` is spread evenly, no
inheritance. Fitted across every entrant the project holds:

| entrant | debut | parent map | corr | slope | **k** | |
|---|---|---|---|---|---|---|
| MK | 2024 | ANC 2019 | +0.568 | 0.97 | **0.03** | inherits |
| EFF | 2014 | ANC 2009 | +0.698 | 0.95 | **0.05** | inherits |
| ActionSA | 2021 | DA 2019 | −0.005 | −0.00 | **1.00** | ignores it entirely |
| COPE | 2009 | ANC 2004 | −0.160 | −0.16 | 1.16 | ignores it |
| UDM | 1999 | ANC 1999 | −0.238 | −0.40 | 1.40 | *unreliable* |
| ID | 2004 | PAC 1999 | −0.337 | −0.71 | 1.71 | *unreliable* |

The last two are marked unreliable and should not be quoted: 1999 is the
earliest election held, so the UDM is measured against a *contemporaneous*
parent rather than a prior one, and the PAC's 0.69% makes its map mostly
noise.

**The result that matters for 2026: MK's k is 0.03.** MK debuted at an NPE, so
its map already exists and it is the ANC's map. Where MK's votes sit is not a
judgement in this forecast — it is a measurement, and it says the ANC's
geography, almost exactly. The same is true of the EFF at 0.05.

**Validated out of sample.** Fold 2 predicts 2021 with ActionSA seeded at its
true 18.12%, so only placement is being tested:

| placement | VD MAE (PR) | total seat error |
|---|---|---|
| no entrant at all | — | **126** |
| flat (the old default) | 0.52pp | 56 |
| DA's map, k = 0.00 | 0.67pp | 48 |
| DA's map, k = 0.50 | 0.56pp | 46 |
| DA's map, k = 1.00 | **0.52pp** | 56 |

VD-level MAE — the metric that matches how k is defined — improves
monotonically to k = 1.0, independently reproducing the fitted k = 1.00.
Seat error prefers k ≈ 0.25–0.5, but seat allocation is lumpy and that is
threshold behaviour, not better placement. `k = 1.0` reproduces the flat
result exactly, which is the implementation's own check.

**The largest single lesson is not about k at all.** Merely *representing* the
entrant takes 2021's seat error from 126 to 56. New-entrant blindness (R7) is
the dominant error in that fold by a wide margin, and the geography dial moves
it by a further ten.

**Why ActionSA is the exception, and why it is not a rule.** ActionSA is the
only party in Johannesburg whose vote carries no racial gradient. Correlation
of 2021 PR ward share with a ward's Black African share (Stats SA 2022 ward
product, all 135 wards):

    ANC +0.911 · EFF +0.850 · IFP +0.270 · ALJAMAAH −0.154
    PA −0.280 · ACDP −0.297 · VF+ −0.554 · DA −0.884 · ActionSA +0.022

It polled 17.6% / 20.0% / 17.7% across wards that are under 40%, 40-80% and
over 80% Black African (27, 23 and 85 wards). The
mirror of that is the DA's own retention, which was strongly graded: it kept
56.6% of its 2019 vote in wards under 40% Black African and 36.1% in wards
over 80%, correlation −0.631. A single candidate with genuinely cross-racial
reach is rare enough in this electorate that k = 1 should be treated as a
property of that case, not a default.

**Implemented, both places, default unchanged.**

* `fold.py` — `--entrant CODE=SHARE[:PARENT:K]`, weighted so the citywide
  total holds for any k. The bare `CODE=SHARE` form is unchanged and flat.
* `montecarlo.py` — scenario key `entrant_geography`, applied as
  `dev[:, ENTRANT] = (1 − k) · dev[:, parent]`, which is the same
  interpolation expressed directly in logit space. Default `{}` leaves the
  forecast untouched: re-running the published scenario changes **0 of 555
  values** and adds no summary keys.

For 2026 the generic entrant is a party nobody has seen, and the observed k
spans 0.03 to 1.16 — genuinely unknown. Flat stays the default, but it is now
a stated choice with a measured range behind it rather than an artefact of
having nothing to put in the column.

**Open.** Whether spatial concentration at debut predicts survival — COPE was
flat (CV 0.45) and collapsed, the EFF concentrated (CV 0.69) and held. Two
observations, so a hypothesis only; MK's concentration is computable from the
eight by-elections it has contested since 2024, which would make the §1.26
branch judgement measurable too.

### 1.28 By-elections now move the ward they happened in ✅ *2026-08-10*

**The defect.** E4 turns each by-election into a *citywide* per-party delta and
applies it to that party's citywide centre. The ward identity is used to
compute the delta and then discarded, so a contest in ward 82 moved ward 82's
forecast exactly as much as it moved ward 1's. Worse, ρ — how typical a ward
is of the city — *down-weights* atypical wards, which is right for estimating
a citywide level and precisely backwards for using a ward's own result on
itself. Ward winners are 135 separate first-past-the-post races, and this is
the one place where local evidence is strongest.

The cost was concrete: the model gave **DA 64%** in a ward the PA won in April
2025, and **ANC 94%** in one the PA won that October.

**The term.** Each contest shifts its own voting districts by the logit
movement it actually showed,

    shift(p) = w · exp(−age/τ) · clamp[ logit(share_bye) − logit(share_2021) ]

with three deliberate choices: ρ is *not* applied (no generalisation is being
asked for); the shift lands on the contest's **voting districts** rather than
its ward, because by-elections sit on 2021 boundaries and the forecast on 2026
ones while VDs carry across both; and ward and PR carry separate weights,
because a by-election is a ward contest whose evidence about list voting in
the same ward is real but weaker, and says nothing about list voting anywhere
else. Tested at ward 0.75 / PR 0.35, cap 1.5 logit (which binds on 11 of the 65 party-contest rows that have a share on
both sides, spread across 9 of them), τ 18 months as the citywide term uses.

**Result — surgical.** Of 135 ward calls, exactly **one** changes:

| ward | by-election winner | model now | with the term |
|---|---|---|---|
| 82 | PA 42% | DA 64% | **PA 68%** ← flips |
| 29 | PA 30% | ANC 94% | ANC 77% |
| 59 | ANC 57% | ANC 65% | ANC 75% |
| 9 | ALJAMAAH 60% | ALJAMAAH 47% | ALJAMAAH 53% |
| 130 | ANC 34% | ANC 99% | ANC 95% |
| 87/89/90/99/102 | DA 83–98% | DA 100% | DA 100% |

Every ward moves toward its own observed result; the DA strongholds, where the
by-elections confirmed the DA, do not move at all. Seats barely notice: ANC
median +1, every other party unchanged, P(ANC+DA majority) +0.0pp.

**A containment limit, stated rather than hidden.** Shares renormalise within
each VD and the citywide total is pinned by calibration, so lifting a party in
ward 82 shaves a vanishing amount off it elsewhere. That is a property of any
model that fixes citywide totals — measured here at well under a seat — not a
leak in this term.

**Not enabled.** `w_bye_local_ward` and `w_bye_local_pr` default to 0, so the
published forecast is unchanged (0 of 555 values). Per the standing decision
of 2026-08-10, nothing ships to the public forecast until everything
outstanding is tested and the harness can predict previous elections.

### 1.29 Making the measurement trustworthy: toothless tests, a banner that reports the run, and two temporal leaks ✅ *2026-08-11*

Nothing here changes the forecast. It changes what the model's own instruments
are worth, which was the precondition for changing anything else: a review had
found **6 of 18 chain tests do not fail when the defect they name is put back**,
and the in-sample banner — the thing that decides whether a backtest score may
be read as skill — was wrong in both directions at once.

**Method: every claim below was verified by reinstating the defect.** A test
that passes is not evidence; a test that fails when, and only when, the thing
it names is broken is. Fourteen mutations were applied to `src/` and the named
tests run against each.

**The three pool-fit tests certified IPF, not the fit.** `fit_city` runs
`raw = fit_joint(...)` then `R = balance_margins(raw, ...)`, and IPF forces
both margins exactly whatever it is handed — so "no negative rate" and "each
pool allocates one vote", asserted on the finished matrix, were statements
about one line of `balance_margins`. Replacing `fit_joint` with uniform 1/n
leaves all three green. They now assert on the raw fit, which `fit_city`
returns rather than the test refitting (the universe filter is easy to miss,
and a test that fitted a different problem would certify the answer).

**And both constraints are enforced by construction**, inside
`_project_simplex`, so a fit that never looked at the data still satisfies
them. The test that catches that is new and is not a magnitude: giving every
pool the citywide shares is a *feasible point* of the problem `fit_joint`
minimises, so a minimiser must return a strictly lower objective. Uniform 1/n
fails it by 4x.

**A temporal test that asserted against the calendar.**
`test_the_level_prior_reads_no_election_at_or_after_its_target` checked that
the CALENDAR contains an LGE before 2016 — true with `theta_record`'s cutoff
deleted, and not a statement about the level prior at all. Temporal tests now
watch the file opens (`_support.election_files_read`): every result file is
named for its election, so a θ record for 2016 that touches `lge2021_...` has
read its answer and says which file.

**Three spec tests certified a file, not the code.** They read
`pools_2026.json` off disk, so a regression in the emit path was invisible
until someone re-emitted — which is exactly when nobody is looking. They now
build the spec through `emit_pools`, which returns it and writes nothing.
One of them also counted the wrong thing: with the empty-roster fallback
removed the spec still carried 40-odd fitted parties, because the defect
deletes only the parties that arrived *after* the fitting election. It now
requires anything above 0.5% of the baseline to reach the spec by some route,
and loses MK when the fallback goes.

**FITTED_ON was wrong both ways.** `theta_mode`, `individual_theta`,
`f_other`, `PLAN_BOUNDS`, `ward_pr_ratio_overrides` and
`pa_contestation_uplift` had been removed from the in-sample list on the
grounds that `levels.py` measures θ from transitions strictly before the
target. True per party, false in general — the measurement covers the parties
the record covers, and one it cannot reach falls back to the typed number.
Measured at target 2021:

| route | parties | of the baseline | worst case |
|---|---|---|---|
| measured θ prior | 36 | 100% | — |
| `theta_mode` | 1 | 11.07% | **ASA 1.50** — ActionSA's only local result IS the target |
| `individual_theta` | 31 | 40.21% | bands whose docstring cites "Al Jama-ah 3.12 in 2021" |

In the other direction the list carried `splinter`, which is not a scenario
key at all, so `contaminated()` could never drop it and every target from 2011
to 2016 was reported in-sample on the strength of a constant that does not
exist; `entrant_geography` is empty by default and read by nothing, and was
flagged the same way. **No target could print an all-clear whether or not one
was owed.**

The fix is to stop asserting and start measuring: `montecarlo.note_constant`
records each hand-typed constant a run actually consumes and what consumed it,
`ModelRun.constants_read` exposes it, and the banner reports that. It moved to
after the run for the same reason — before it, only a guess is available. Two
tests keep the ledger honest: every `note_constant` name must be declared in
FITTED_ON (else a fallback goes unnamed) and every FITTED_ON key must be
reachable by a run (else it is a verdict no scenario can clear).

**Leak 1 — the splinter record hardcoded 2024.** `splinter_record`'s three
pairs (COPE 2009, EFF 2014, MK 2024) had their years fixed in the signature
and the caller passed no target, so a backtest at 2016 sized its splinters on
a split eight years in its own future. It now takes the target and drops
splits that had not happened — which retires the FITTED_ON key entirely, the
same trade γ already makes, where the code enforces what the key announced.

**Leak 2 — contestation was read off the result.** `levels.contestation` and
`pools._ward_reach` both justify reading the target's own file on the grounds
that nomination lists close and are published before polling day. Sound, and
not what the code did: both counted a ward only where the party had
`Party_Votes > 0` — not who stood but who scored. The IEC publishes a row per
party per voting district *where that party is on the ballot* (20-34 parties
per VD in Johannesburg 2021, not a cross-product), so the row's existence is
the nomination fact, and 40% of ward-ballot rows carry no votes. Counting rows
reads no result and moves 27 parties: **Royal Loyal Progress stood in all 135
wards and scored in 79**, so a full slate was being called 59% of a slate. It
is not a footnote — contestation multiplies the ward/PR ratio in the drawer
and sets an arrival's size in the record.

**The live 2026 forecast does not move**, checked by re-emitting and diffing:
2026 has no result file, so the arrival rules fall back to 2021 reach, and
every party those rules touch is one that did not stand in 2021. All 21
`first_local_election` entries identical, seeds unchanged, drawer goldens
green. The movement is confined to the backtests, which is where the leak was.

**What the banner now says at 2021** — and why it still cannot print an
all-clear:

    IN-SAMPLE — THESE ARE NOT OUT-OF-SAMPLE SCORES
      individual_theta  read 2021 — the bands say so themselves ...
        consumed by: ABAHLALY_BAAHI, ... (+23 more)
      pools             read 2021 — Census 2022 post-dates the target ...
      theta_mode        read 2021 — ASA 1.50 ...
        consumed by: ASA
    Also read, and clean at this target:
      contestation      read no result — ward-ballot PRESENCE ...

Three things stand between this and a clean 2021 banner, all now named rather
than assumed: pool composition comes from Census 2022, which post-dates the
target; ActionSA has no measurable θ because 2021 is its only local election;
and 31 minor parties have no retention record to measure. The first is
fixable with the 2011 census, the second is not fixable at all and belongs in
a declared scenario, the third is the micro-party band problem already open.

Suite: 9 seats + 6 drawer + 4 temporal + **26** chain, all green.

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
| O11 | `fold.py` wrote and read fitted parameters at `data/processed/fold{N}_parameters.csv` with no city in the path, so a Tshwane run overwrote Johannesburg's — and `fold1_parameters.csv` feeds the live forecast | Both call sites use `City.processed`: Joburg keeps the legacy path, other cities go to `data/processed/<slug>/`. Caught only because a stale file made §1.25's second fold report numbers that could not be reproduced. | ✅ |
| O13 | ✅ **RESOLVED as far as the data allows.** Two councils could not be reconstructed, and it is a data limit rather than a bug: independents cannot be told apart. Every IEC file we hold names every independent candidate `INDEPENDENT` — there is no candidate column at VD level — so `ward_winners`, which picks the top *name* in each ward, sums them into one bloc. Three candidates on 300 votes each become a bloc of 900 and beat a party on 700, crediting a ward win nobody won. Measured: Buffalo City 2021 counts 1 independent ward against the IEC's C = 0, eThekwini 2016 counts 5 against 4 — over by exactly one in each. C leaves the seat pool *before* the quota is struck, so `available` is 99 instead of 100 (BUF) and 214 instead of 215 (ETH), and quota = A // available + 1 comes out 3,555 vs 3,519 and 9,964 vs 9,918, both about 1% high. **A itself is exactly right in both** (BUF 351,899, ETH 2,132,173, to the vote), so the vote data and the eligibility rule are sound. Johannesburg and Tshwane pass only because their independents never top a ward. `backtest.py` therefore refuses Buffalo City, which is the correct refusal. | The detailed-results PDFs were checked and carry no candidate names — they are a municipality-level party summary, and the IEC publishes no candidate-level municipal product. **So C is now read from the IEC's Seat Calculation Detail** in `backtest.py` and the seat tests, with the counted figure kept as the upper bound it is and a test that it never falls below the published C. Buffalo City scores again (CRPS 7.93, seat MAE 10) and the suite is 28/28. Cost: one structural input now comes from the IEC rather than from votes, stated in DATA-QUALITY.md item 12. | ✅ |
| O14 | `INDEPENDENT` is declared twice (`parties.py`, `seats.py`) and both hold `"INDEPENDENT"`, the PRE-canonical label, while `parties.canonical()` maps that onto `"IND"`. The seats path is self-consistent because it works in raw names throughout, so nothing is wrong today — but `montecarlo.py` and `benchmarks.py` both carry `p != INDEPENDENT and p != "IND"` workarounds, which is two authors having hit it. An attempt to unify it by canonicalising the seats path broke all 24 city-year checks at once, because the IEC report's own party rows are raw: the fix is to canonicalise BOTH sides or neither, and it needs doing deliberately rather than in passing. | Reverted; recorded here instead of half-done. | 🔴 |
| O12 | Backtests cannot run at 2011 or 2016: `pools_2011.json` does not exist and `pools_2016.json` predates the counted-pool rebuild, so it has no `registered` key and `pool_spec` dies on a `KeyError`. Only 2021 and 2026 are runnable, which means the in-sample banner's clean case is currently untestable end to end. | Re-emit both specs (`python src/pools.py --city joburg --target {2011,2016} --emit`) before the next backtest round. Not done here: emitting rewrites files the forecast path reads, and this session's remit was the instruments, not the outputs. | 🔴 |
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

### R8 — Calibrated θ may be only weakly identified 🔴 *affects `--fit-from` only*

Fold 2's calibrated θ sits 4–7× below its raw θ (ANC raw 0.670 → calibrated
0.129, DA 0.859 → 0.116, EFF 0.681 → 0.166) while fold 1's tracks raw closely
(ANC 0.859 → 0.832). Both folds reproduce citywide shares in-sample to
+0.00pp, so the solver converged either way — which is the concern: with 68
parties and an 18% party holding a zero base, within-VD renormalisation
absorbs much of a uniform rescaling of θ, so many θ vectors may fit equally
well. Anything that *transfers* calibrated θ between folds then inherits
whichever solution the solver reached, and a stale parameter file (O11)
showed exactly that sensitivity: the same fold scored 60 seat error under one
file and 94 under a freshly-fitted one. **No effect on the live forecast**,
which fits θ in place and never transfers it. To settle it: check whether
`calibrate_theta` has a unique solution under the current universe, and if
not, pin the gauge (e.g. constrain the vote-weighted mean of θ) before any
`--fit-from` result is quoted as exact.

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

### THE TWO GAPS BETWEEN HERE AND A LIVE SITE (2026-08-12)

Both are structural, both are open, and the second is on a clock.

- **Task #22 — the model runs national→local, which is half the story.**
  Every party's level is built from the last NATIONAL result and converted
  downward by θ. That is the right spine for a nationally-organised party and
  the wrong one for a party whose evidence is local, and the model has no way
  to tell them apart. **Measured on 2021**: predicting each party's local
  share from the previous national result × θ beats using the previous local
  result directly for ANC, DA, VF+, ACDP and AIC — and loses for EFF, PA, IFP
  and Al Jama-ah. Five to four. Neither route dominates and the model uses one
  of them unconditionally.

  ActionSA is the extreme case, and it is why this surfaced. Its national
  result is the *weakest* thing we know about it: 18.12% locally in 2021
  against 6.22% nationally in 2024, a local premium of **2.91**, and the
  forecast is built on the 6.22% and then discounts it by a group average of
  0.88. It has no θ of its own because θ is only ever measured national→local
  and ActionSA had no national vote before its first local one. The same holds
  for the PA, and for every local formation the model cannot really carry:
  Defenders of the People in Tshwane, the Cape Coloured Congress, the Northern
  Alliance in Nelson Mandela Bay, the ratepayer associations.

  *The partial fix* is to measure θ in both directions — a local→national pair
  inverted is the same quantity, and it would recover ActionSA's 2.91 as its
  own evidence, moving it from θ 0.88 to about 1.3. Worth doing and not a
  cure: it is a patch on the same pipe.

  **WHAT THE SLIDING SCALE IS NOT — two negative results, 2026-08-12.** The
  obvious design is to score each party on how *local* it is and weight its
  local record accordingly. Measured, that does not work:

  * *Geographic concentration does not predict the local premium.* Scoring
    each party by the share of its metro vote in its single best metro
    (NCC 100% Cape Town, IFP 72% eThekwini, MK 62% eThekwini, ActionSA 52%
    Johannesburg, EFF 26% — exactly the "perfectly even" value) and
    correlating that against its 2019→2021 local premium gives **r = −0.09
    over 13 parties.** No relationship.
  * *The premium is not concentrated at home either.* Comparing each party's
    local premium in its strongest metro against the median elsewhere: the
    **median ratio is 0.93, and only 3 of 10 parties exceed 1.** An
    established party converts national support to local support at about the
    same rate wherever it stands.

  So "local party" is not a geographic property and should not be modelled as
  one. What distinguishes ActionSA is not *where* its vote is but *which
  election it is built for* — and the only measurable signature of that is the
  party's own local-to-national ratio, which needs one observed pair of both
  election types. ActionSA has exactly one. That makes the both-directions θ
  fix above the *whole* of the measurable answer, not a stopgap, and it
  removes the case for a separate "local party" class.

  **PRECEDENT (2026-08-12).** Reif and Schmitt's second-order election model
  (1980) is the frame and it predicts what this model already measures:
  in second-order elections — explicitly including municipal ones — turnout
  falls, nationally governing parties lose vote share, and small, new and
  opposition parties gain. Our measured θ *is* the second-order effect (ANC
  0.77–0.84, small parties above 1), which is worth stating on the
  methodology page because it means the structure is not ad hoc.
  The local-party literature offers two further mechanisms, and only one
  survives contact with our data:
  * *Local parties win where national parties field no candidate.* Real
    elsewhere, **not operative in a South African metro**: tested on
    Johannesburg 2021, the ANC, DA and EFF each field a ward candidate in
    **135 of 135 wards**. Dead here.
  * *Local parties with governing experience survive better*, against the
    cost-of-ruling thesis that holds for national parties. This is live and
    directly relevant — ActionSA now governs Tshwane in coalition — and 2026
    is its first test. Nothing in our record can settle it beforehand.

  *The real fix* is that a party's level should come from BOTH its previous
  local and its previous national result, weighted by which has historically
  been more informative for a party like it. The weights are measurable — the
  five-to-four table above is that experiment, run on one city and nine
  parties; it should be run across eight metros and several cycles before any
  weight is chosen. Two honest constraints on the design: the local result is
  five years stale by polling day where the national is two, so recency is a
  real argument for the current spine and the blend must price it; and this
  changes the published forecast materially, so it lands before a deploy, not
  after.

- **Task #23 — we have no stated view on how to read a poll, and the polls
  have started.** The machinery exists (`poll_id`, `poll_weight`, a register
  in `POLLING.md`, a `polls.json`) and `poll_weight` is **0**: no poll touches
  the forecast today. That was defensible while there was nothing to read. It
  is not defensible into an election, and the gap is not "turn the dial up" —
  it is that we have no policy, and the raw material is worse than it looks:

  1. **They disagree by more than the thing being forecast.** The SRF Q2 CoJ
     wave has DA 42 / ANC 18; the Ipsos metro subsample has ANC 35 / DA 25.
     That is a thirty-point spread on the ANC between two houses in the same
     year. Averaging them is a decision, not a neutral act.
  2. **There is almost no metro-level track record to weight them by**, and
     what there is is bad: pre-2021 polling missed ActionSA by about ten
     points in this city.
  3. **A cutoff filter is not currently expressible.** `polls.json` carries
     `fieldwork` as free text ("8–31 July 2026"), so a backtest cannot
     mechanically exclude a poll taken after its target. Any poll term added
     before that is fixed is a temporal leak waiting to happen, and this
     repository has just spent a week removing those.
  4. **A poll and the model's own level prior estimate the same quantity.**
     The model now measures θ per party from that city's own transitions. A
     poll is a competing estimate of the same number, not extra information to
     be added on top, and the blend has to say which it trusts where — with
     the answer bounded by evidence rather than chosen.

  What is needed is a written policy — which houses and geographies are
  admitted, how fieldwork dates are parsed and filtered, how house effects and
  herding are handled, how a poll is reconciled against the measured prior
  rather than averaged with it — and then the dial. The policy is the work;
  the dial is an afternoon.


- **Task #16** — Census 2022 Small Area Layer: **requested from Stats SA 2026-08-05** (email sent), awaiting reply.
- **Task #18** — historic VD boundaries: **requested from the IEC Delimitation Directorate 2026-08-05** (email sent), awaiting reply. Would convert R1 from mitigated to resolved.
- **Task #20** — Schedule 1 overhang worked example: **four-question request sent to the IEC 2026-08-05**, awaiting reply. In parallel, an archive hunt for a real historical overhang municipality is running. P(overhang) ~72–96% across readings; the answer moves P(ANC+DA) across 72–91% (§1.16).
- **Task #21 (new, 2026-08-10)** — **Census 2022 home language by ward**, from
  Stats SA. Now the binding constraint on the model's structure, ahead of the
  SAL: population group cannot distinguish pools that are linguistically
  rather than racially sorted, and two measurements say that distinction is
  real (ANC vs IFP correlate −0.14 despite both being African-supported; DA
  and VF+ correlate +0.61 to +0.86 despite differing in language). It would
  also bound MK demographically instead of by judgement. Draft request at
  `drafts/statssa-request-language.md`, **not yet sent**.
- **External** — 2026 registration-weekend figures, when published.

### Open from the 2026-08-09/10 splinter work (§1.26, §1.27), ranked

1. ✅ **RESOLVED BY DELETION.** `DA_BLOC` membership was contradicted by
   measurement — and blocs no longer exist (87806a7); the model draws from
   voter pools fitted per city. Kept for the record: ActionSA's gains
   were funded by the ANC and the EFF, not the DA (per point of ActionSA:
   ANC −0.381pp, EFF −0.262pp, DA **+0.199pp**; DA vote retention uncorrelated
   with ActionSA's local strength at −0.043). The model funds ActionSA out of
   DA losses inside a conserved bloc total. **Load-bearing** — pinning the
   DA-bloc split alone moves P(ANC+DA majority) from 87.6% to 98.4%. Needs a
   config change *and* a rewrite of the published methodology paragraph, which
   currently defends the grouping on "the argument about where defectors go".
2. ✅ **RESOLVED 2026-08-11.** The claim is gone: `docs-public/methodology.md`
   was rewritten for pools and no longer contains it. Kept for the record: `docs-public/methodology.md`
   says the fully blind seat error "grows fivefold". Measured today: 96 → 126,
   a factor of 1.3. On the like-for-like metric — parties that actually won
   seats, excluding ActionSA, which cannot be represented at all — it is
   10 → 71, sevenfold. The claim understates the limitation but cannot be
   reproduced from any number the model prints. Rewrite naming its metric and
   **register it as a stat token**; it was typed prose, which is exactly what
   `stats.py` exists to prevent.
3. ~~**The by-election ward-local term was never built.**~~ ✅ *built
   2026-08-10, §1.28* — but **not enabled**: `w_bye_local_ward` and
   `w_bye_local_pr` default to 0, pending the standing decision that nothing
   ships to the public forecast until the outstanding items are tested and the
   harness can predict previous elections. At the tested weights it flips
   exactly one of 135 ward calls, the one the PA actually won.
4. **Phantom seats from the share floor.** `SHARE_FLOOR` (0.002 per VD across
   865 VDs) is worth about two seats on its own. In fold 2 it hands 42 seats to
   21 parties that won nothing — the whole of that fold's headline error. The
   live forecast carries a smaller version: `ARISE_SOUTH_AFRICA`,
   `UNITED_AFRICANS_TRANSFORMATION` and `ALLIED_MOVEMENT_FOR_CHANGE` each hold
   a median seat.
5. ~~**`archive.py` manifest is missing six hashes**~~ ✅ *done 2026-08-10* —
   the 1999/2004/2009 NPE and 2000/2006/2011 LGE archives are documented in
   `SOURCES.md` and fingerprinted in the manifest, which now covers 244 files
   and verifies clean (`src/archive.py --verify`: 0 differences). It had never
   been tracked at all, despite O10 saying it was, so it is force-added.
6. **`fold.py` overwrites the live forecast's γ whatever diagnostic you ran.**
   It writes `fold{N}_parameters.csv` regardless of `--turnout`, so a
   `--turnout ratio` experiment silently replaces the default-fitted γ that
   `montecarlo.py` reads. This bit us on 2026-08-10: a diagnostic run moved 55
   of the forecast's 555 values before anyone noticed, and regenerating with
   defaults restored them exactly. Same class as O11, keyed on the turnout
   method rather than the city. The parameter file should carry the method in
   its name, or the forecast should read a pinned copy.
7. **`turnout.py --out` ignores the active city.** It defaults to
   `data/processed/turnout.csv` whatever `--city` says, so a Tshwane run
   overwrites Johannesburg's published turnout file. The three consumers
   (`montecarlo.py`, `export_interactive.py`, `leverage.py`) all default their
   `--processed` to the same place, so the writer and readers have to move
   together — found 2026-08-10 while making `turnout.py` city-safe.
8. **`fold.py --city tshwane --fold 3/4/5`** dies with a bare
   `FileNotFoundError` on the base election file rather than saying the fold
   does not exist for that city. Only Johannesburg has the pre-2011 ingest.
9. ✅ **RESOLVED.** The Monte Carlo *is* year-parameterised — `run_model` takes
   a target and `backtest.runnable_targets` derives the set per city, so the
   distributional forecast scores against 2016 and 2021 today. Kept for the
   record as written: it used not to be, and only the deterministic core could
   be scored, via the folds.

---

## 1.30 The spine, the calibration, and what nine city-years actually show (2026-08-13)

### Task #22 is closed, but not by the fix the log proposed

**The proposed partial fix is measurably worse than doing nothing.** §6 proposed
measuring θ in both directions, on the reasoning that a local→national pair
inverted is the same quantity and would give ActionSA a θ of its own. Held out a
metro at a time over 180 party-city-years, pooling reverse observations into the
θ record gives RMSE(log) **0.292 against forward-only 0.275**, and every adaptive
blend built on it is worse than the same blend on forward θ. The reason is in the
pairs: a reverse observation divides a local result by a *later* national one, so
the party's secular trend enters with the opposite sign. The PA, growing,
measures 1.90 forward and 0.60 reverse; the ANC, declining, 0.85 and 1.05. They
are not the same quantity, and pooling them averages a party's trend into its
local premium. **Rejected.**

**What works is a blend keyed on EVIDENCE, not on geography.** A party's level
now comes from both its previous national result (× θ) and its previous local
result (× ρ, the measured LGE-to-LGE retention), weighted `k/(worth+k)` toward
the local route, where `worth` is what that party's own θ record is worth. The
banding is unambiguous:

| θ evidence | n | RMSE national | RMSE local | best weight on local |
|---|---|---|---|---|
| 0 – 2 | 60 | 1.53 | 0.72 | 1.00 |
| 2 – 5 | 55 | 0.089 | 0.24 | 0.10 |
| 5 – 20 | 65 | 0.20 | 0.41 | 0.10 |

**It is not party size in disguise.** Within *every* size band the flip survives:
among parties under 0.5% of the vote, those with θ evidence want the national
route (best w 0.00) and those without want the local one (best w 1.00). Keying
the same rule on size is worse (0.2377 against 0.2358). Held out by metro:
**0.236 against the national spine's 0.275, a 14% gain**, winning on four metros
of eight by count and on the pooled vote-weighted error because the wins land
where the national route fails worst (Buffalo City 0.320 → 0.111) and the losses
where it was already accurate (Mangaung 0.077 → 0.094). This also closes §6's
"the local result is five years stale" concern without a term: each route is
corrected by a ratio fitted over its own gap, and w was fitted on local results
that were themselves five years stale.

For Johannesburg 2026 the spine moves ActionSA from **5.98% to 15.23%** (w=1.00
— it has no forward θ at all), the PA from 5.51% to 6.63%, and the ANC and DA by
under half a point each, which is the shape a correct fix should have.

### Calibration (external review §2)

* **sd(log θ) now reaches the draw** (item 2). It was measured and discarded: a
  pooled party had no level uncertainty of its own at all, because the pool's
  turnout moved every member together and the Dirichlet only redistributed
  between them. Draws are Student-t in log space, df 4 — unbounded support, so
  nothing that has happened has probability zero.
* **One correlated citywide turnout factor** (item 3), ρ = **0.63 MEASURED**
  over 14 metro-transitions. Black African, Coloured and White move almost as
  one (+0.86 to +0.91); Indian/Asian is the loose one (+0.21 to +0.47). Four
  independent pools put the citywide sd at 0.50 of a single pool's; the record
  says 0.82. So aggregate turnout uncertainty was understated by 1.64×.
  Implemented as a Gaussian copula, so every pool keeps exactly the marginal
  band measured for it and only the dependence changes.

### Four faults the nine-city sweep found (`src/sweep.py`, new)

1. **The fold's θ calibration had an unidentified scale, and it drifted.**
   `predict` renormalises within each VD, so multiplying every θ by a constant
   changes nothing once the levels are low enough — and the IPF wandered four
   orders of magnitude down. The ANC ended fold 2 at θ = 0.0001, a level of
   −10.2, with the parties pinned at the level floor only 3.6 logits below it:
   0.67% of the vote each, just over the quota, and **21 parties that won
   nothing took 2 seats apiece — 42 of that fold's 96 seat errors.** Pinning
   Σ base·θ = 1 removes all 42. **This log blamed SHARE_FLOOR for those seats
   (§1.26 item 4) and that was wrong**: lowering the floor from 0.002 to 1e-6
   changes the seat totals *not at all*, which is how the real cause was found.
   Fold 2's error is now honestly composed — 44 of it is ActionSA, and the big
   parties inherit those seats.
2. **Every historical backtest ran with turnout forbidden to rise.**
   `turnout_band` capped the top at the highest turnout the city had recorded —
   the identical error its own docstring rejects for the bottom. It bound at
   **4 of 4 pools for every metro at target 2016 and 3–4 of 4 at 2021**, and at
   **0 of 4 for 2026**, because 2021 was the lowest on record. The instrument
   was biased in exactly the runs used to judge the model and not in the run
   being judged. Now built in **logit space**: the constraint is on the
   *change* ("no more than has been observed"), which is what was wanted, and a
   proportion on its natural scale cannot leave (0,1), so there is no cap
   anywhere — neither the observed maximum nor the 1.0 that briefly replaced it.
3. **A splinter band of one observation was a band of zero width.** At target
   2021 **seven of the eight metros** have an away-splinter record of exactly
   one observation, so `(min, median, max)` gave low == high: a triangular
   asserting the arrival's size was known exactly. ActionSA then took 19 of
   Tshwane's 214 seats against a band of 0.4%–0.4% — an outcome the forecast had
   *ruled out*, not merely thought unlikely. Bands are now lognormal with the
   width borrowed from the pooled cross-metro record, floored, and capped at
   1.0 of the parent (Johannesburg's own record implied 1.17, which is not a
   bold forecast but an arithmetic impossibility).
4. **Two readers still pointed at the un-namespaced processed directory.**
   `turnout.py --out` was fixed on the writer side; `export_interactive.py` and
   `leverage.py` still defaulted `--processed` to `data/processed`, which is
   *Johannesburg's*. A Tshwane run read Johannesburg's turnout, γ and ward parts
   and then wrote its `interactive_data.json` over the file the published page
   loads. (§1.26 items 6 and 7 were already fixed on the writer side; item 8,
   `fold.py`'s bare `FileNotFoundError`, now names the folds the city can run.)

### The largest error in the record is new parties, and tuning will not fix it

Across nine city-years the dominant anomaly is one class: **a party that won
seats with a median of zero, eleven times.** The PA in four metros, ActionSA in
Tshwane and eThekwini, the Cape Coloured Congress, the Northern Alliance, the
AIC twice. Measured, ActionSA took **0.611, 0.315, 0.289 and 0.103 of the DA's
vote** in the four metros it contested and nothing in the four it did not; the
away-splinter record it was sized from (COPE and EFF) tops out at **0.017**. It
is 30–70× larger than anything on record, so no widening of the arrival band
reaches it and none should — the record genuinely does not contain a party like
this. Ward contestation gates arrival (0.00 where ActionSA did not stand) but
does not predict magnitude (r = +0.12 across the four it did).

That is the strongest available argument for **task #23**: for a party with no
electoral history, polls are the only pre-election evidence that exists, and
pre-2021 polls had ActionSA near 6% against the model's 0.17% in Tshwane.

### Scored against the baselines, honestly

Nine city-years, total absolute seat error, model against the naive references:

| city-year | model | last-lge | uniform-swing | prior-lge-noise |
|---|---|---|---|---|
| Johannesburg 2016 | 62 | 92 | **26** | 91 |
| Johannesburg 2021 | **65** | 134 | 126 | 125 |
| Tshwane 2021 | **54** | 80 | 60 | 77 |
| Ekurhuleni 2021 | 54 | 72 | **48** | 66 |
| eThekwini 2021 | 42 | 82 | **36** | 76 |
| Cape Town 2021 | 43 | 68 | **38** | 63 |
| Mangaung 2021 | 11 | 24 | **8** | 20 |
| Nelson Mandela Bay 2021 | **18** | 28 | 22 | 27 |
| Buffalo City 2021 | 14 | 14 | **12** | 15 |

**The model beats uniform swing in three of nine and loses six.** It beats
last-lge and prior-lge-noise almost everywhere, which is a much weaker claim —
those are pure persistence. Uniform swing is the one baseline that carries any
information about which way the country is moving, and it is the one the model
does not reliably beat. That is Murphy's point about standards of reference
restated in this repository's own numbers, and it is unchanged by everything
above.

**A note on the published-run comparison, because it is easy to get wrong.**
`validation_2021.json` lists only the top TWELVE parties, while these targets
have 15 to 24 actual seat-winners, so its seat error is truncated and is not
comparable to a figure summed over the whole ballot. On the same twelve parties
the current model is better in five of eight (eThekwini 25 against 35, Cape Town
26 against 37, Nelson Mandela Bay 12 against 16, Mangaung 9 against 11,
Ekurhuleni level) and worse in three (Johannesburg 59 against 56, Tshwane 51
against 44, Buffalo City 14 against 10).

### The two Johannesburg failures are not the same failure

`src/diagnose.py` decomposes one city-year into citywide vote, ward seats, list
seats, and every ward called wrong. It says the two Johannesburg errors, 62 and
65, have almost nothing in common:

* **2016 is ONE NUMBER.** The ANC is +8.83pp on the PR ballot, and the DA
  (−5.90) and EFF (−3.73) are its mirror image. The geography is fine — 126 of
  135 wards called correctly, and **not one of the nine misses gave the actual
  winner under 2%**, so every one was a close contest lost rather than a fault.
  The ANC alone is 25 of the 62 seats. The cause is honest rather than a bug:
  the only θ evidence available before 2016 puts the ANC's local retention near
  0.95, and in 2016 it was 0.80. Uniform swing beats the model here precisely
  because the 2009→2014 national movement carried that decline and θ did not.
* **2021 is arrivals and the tail.** ActionSA −14, the PA −8, and fourteen
  parties one or two seats short each. The ANC's **ward seats are exactly right,
  87 against 87** — its entire seat error is in LIST seats, 15 against 4, driven
  by a +3.02pp citywide vote error. Geography right, level wrong, and the two
  are cleanly separable. Three of the seven wrong ward calls gave the actual
  winner **under 2%** (Al Jama-ah in ward 79800009, the PA in 79800017 and
  79800018) — those are faults, not bad luck.

So "Johannesburg got worse with more data" is not what happened: 62 and 65 are
different diseases, and the 2016 one is a single level miss the record could not
have warned about.

### The DA over-prediction and the ActionSA miss are ONE error (2026-08-15)

Asked what the DA's voter pools are and whether they amount to a third of the
city. They do not, and answering it properly found that two of the model's
largest errors are the same error.

**The DA's pools, Johannesburg 2021.** Its vector is White 64.3%, Coloured
14.7%, Black African 11.3%, Indian/Asian 9.6% — so 88.7% of its vote comes from
pools holding **42.0% of the votes cast** (35.0% of the roll; they turn out well
above the city average). A DA on 33% of the city therefore is not "33% of the
population": it requires taking

    Black African 6%   Coloured 74%   Indian/Asian 86%   White 67%

**Those rates are not impossible, and that is the point.** The ecological fit on
2016 measured the DA at Black African 6.2%, Coloured 77.9%, Indian/Asian 71.2%,
White 87.5%, and every pool's rates sum to 100% across parties by construction.
So the drawn 33% is consistent with the DA holding its 2016 position. The actual
25.45% needs White ~52%. **The DA's rate in the White pool collapsed from 87.5%
to about 52% between 2016 and 2021**, and the model carries 2016 forward.

**Where it went is in the pool vectors.** ActionSA is a DA splinter and inherits
its parent's vector: **ASA is 67.2% White against the DA's 64.3%**. They compete
for the same voters, and the pool renormalisation is supposed to debit the DA
when ActionSA takes them.

Tested by forcing ActionSA to its actual 18.12% and changing nothing else:

    party      actual    as-is    ASA forced correct
    DA         25.45%   33.00%          27.11%
    ASA        18.12%    5.75%          14.38%
    ANC        33.22%   39.99%          38.47%
    EFF        10.11%   14.09%          13.36%
    DA seats       71       90              75

**The DA's error falls from +7.55pp to +1.66pp, and its seat error from +19 to
+4, with no change to the DA's own machinery.** The ANC barely moves, because it
draws from a different pool — which is the pool structure doing exactly what it
was built to do, and is the strongest evidence yet that the pool layer is sound.

Three consequences.

1. **A claim made earlier in this session was wrong.** "ANC 40.0 + DA 33.0 = 73%
   is an established-party level error that no arrival work touches" is false for
   the DA half. Most of the DA's error IS the arrival error, arriving through the
   shared pool.
2. **The residual is the ANC**, +5.25pp even with ActionSA corrected, in the
   Black African pool. That is the genuinely separate problem.
3. **Nothing here needs a new mechanism.** The debit already works; it is starved
   because the thing debiting it is too small. Every point of improvement on
   arrivals buys most of a point on the DA for free.

### CONFIRMED OPEN: the splinter branch reports a blend it does not use (2026-08-15)

An independent review claimed the splinter path never executes. Checked, and it
is **half right, in the half that matters for credibility**.

`emit_pools` writes ActionSA's seed note as

    SPLIT from DA (Mashaba, the DA's own mayor of Johannesburg...): takes 15.1%
    of a vector that is 35% DA's pool rates and 65% the city's own composition

while `no_measured_vector` records, for the same party,

    ASA: entrant, even share of every pool

All 39 parties with no measured vector get "entrant"; not one gets "splinter of".
The two sites disagree because `arrival_rules` routes ActionSA through
`classify_arrival` (which resolves the parent from `SPLITS`) while the
composition-vector loop reads the raw `parent` field from
`judgements/<city>-<target>.toml`, and every one of those is `""`.

**The emitted vector is nonetheless the blended one** — it comes from the
`arrival_rules` capture, which is why ActionSA's Black African weight moves
0.856 / 0.599 / 0.194 as `SPLINTER_PARENT_WEIGHT` goes 0.0 / 0.35 / 0.9. So the
model is not using an even split. But it *reports* two incompatible provenances
for the same party, and one of them is wrong.

That is the kind of thing a hostile reader finds first, and this repository's own
`JUDGEMENT-CALLS.md` standard says a reviewer who finds one advertised constant
that does not do what it says will not trust the measured ones. **Fix before
publication**: route the composition loop through `classify_arrival` so both
sites agree, or drop the second message.

Related and still open: the review measures the top three parties' realised
`sd(log)` at 0.078 against a measured 0.26. With the centres now binding, the
model is accurate and overconfident rather than inaccurate and overconfident.
The level shock is applied inside the pool and then renormalised away for a
dominant member, so it must move to the centres — before the IPF — to transmit.

### The dividing line is a NATIONAL RECORD, not novelty (2026-08-16)

Scored the first-local-election path on its own — a party with a national
baseline that has never faced a local election, sized as
``national base x parent theta x ward reach x coherence``. 45 cases across nine
city-years:

    median model/actual ratio   0.85      (1.00 = unbiased)
    geometric mean              0.83
    within a factor of two      78%
    median |log ratio|          0.27

Against arrivals — parties with **no national record at all** — at **22%** within
a factor of two, 7 of 32.

**So the model is good at new parties and bad at unknown ones, and the line
between them is whether a national election has already measured them.** That is
a much more useful statement than "the model is bad at new parties", which is
what every summary so far has said, and it changes what the remaining work is:
the arrival machinery is the problem, and the first-local path is not.

It matters most for what it says about **2026**. MK is on the good path, not the
bad one — it holds 12.2% of Johannesburg's 2024 national vote and is seeded at
8.18%. The concern recorded earlier in this log, that "MK 2026 is an
ActionSA-class event in the category with a measured record of 1 in 32", is
**wrong**: ActionSA in 2021 had no national vote at all and was an arrival, while
MK has one and is not. RISE (1.70%) and BOSA (1.11%) are on the same path.

The 15% under-bias is measured on 45 cases and is a candidate correction, but it
is **not testable historically**: 44 of the 45 fall at 2021, so a backtest at
2021 has one prior case to fit on. It is available to the live forecast and
untestable by the harness, which is the same position as `w_bye` — argued, not
tested, and it should be labelled that way if it is ever applied.

### Does it matter which party a splinter is classed as leaving? (2026-08-16)

Put to the repository that ActionSA is recorded as a DA splinter while the data
say its support pools are nothing like the DA's. Both halves are true, and the
test is what the classification actually buys.

`parent` controls three things: the splinter FRACTION is a share of the parent's
own vote, the starting VECTOR is 35% the parent's, and `home` travels with the
Split record. For ActionSA at Johannesburg 2021:

    if parent were   its 2019 JHB share   seed = f x share   inherited vector (BA/White)
    DA                        29.63%             4.48%           0.417 / 0.431
    ANC                       49.62%             7.51%           0.703 / 0.219
    ACTUAL                                      18.12%           0.556 / 0.344

**The truth is between the two parents on both quantities**, and closer to
neither. Scored end to end, the classification is worth almost nothing:
Johannesburg 2021 CRPS **73.07 as a DA splinter against 72.68 as an ANC
splinter**. The seed moves 5.08% to 7.38% and both are a third of the answer.

Two conclusions.

**The model conflates two different things under one field.** LINEAGE is a fact —
Mashaba was the DA's mayor and resigned from the DA — and it is the right basis
for `home` (his base is Johannesburg) and arguably for the splinter fraction,
which is a statement about how much of a leader's old party follows them. The
DONOR POOL is an empirical question with a different answer: measured, ActionSA
drew **ANC −0.381 and EFF −0.262 per point while the DA GAINED +0.199**. A
non-negative inherited vector cannot represent a parent that gains, which is why
the fitted blend lands between the two parents rather than on either.

**It only ever matters for a party's FIRST election.** After that the vector is
fitted from ward data. ActionSA's 2026 vector is 61.5% Black African and
ward-identified, against the 12.1% it was *given* in 2021 — so the 2026 forecast
does not rest on the inheritance guess at all. The classification is a one-cycle
bootstrap, and the evidence that it is wrong arrives at the same moment it stops
being used.

So: not worth re-classing ActionSA, and worth separating the two meanings if the
splinter path is ever rebuilt. `parent` should mean who left; a donor
specification, signed, should mean whose voters — and the repo already has the
flows for one party.

### Correction: the "DA +0.199" figure is ward-level and has been over-quoted (2026-08-16)

§1.26 records that per point of ActionSA in 2021 the **ANC −0.381pp, EFF
−0.262pp, DA +0.199pp**, and that figure has been quoted repeatedly since — this
session used it four times to argue that a non-negative composition vector
cannot represent a parent that GAINS.

Re-measured across the eight metros, it does not reproduce with that sign:

    regression of each party's change on ActionSA's share, 8 metros
    NPE 2019 -> LGE 2021    ANC -0.530   EFF -0.255   DA -0.309
    LGE 2016 -> LGE 2021    ANC -0.404   EFF -0.230   DA -0.502

The original is a **ward-level regression inside Johannesburg**, not a
cross-metro one — a different unit of analysis, and confounded in the obvious
way: ActionSA and the DA are strong in the same wards, so a positive share
correlation between them does not mean the DA gained from ActionSA.

**The defensible sentence is the one §1.26 itself gives two lines later**, on
retention rather than share: *"the DA's retention is uncorrelated with
ActionSA's local strength (−0.043) while the ANC's (−0.290) and the EFF's
(−0.264) fall away."* That still makes the point that matters — a splinter of
the DA did not take DA votes — without claiming the DA gained.

Quote the −0.043 retention figure, not the +0.199 share figure. The argument
about signed donor vectors survives: the DA's donation is approximately ZERO
where its lineage says it should be the whole of it, and a composition vector
normalised to one still cannot express "this party took nothing from its
parent" without silently reallocating that share elsewhere.

### Two things this did NOT do

* **The point-estimate rates matrix is still a point estimate** (review item 6).
  Hierarchical multinomial-Dirichlet with ward-varying rates is a substantial
  piece of work and is untouched.
* **The by-election ward-local term (#3) still cannot be tested.** It is not
  waiting on the harness. `byelection_*.csv` covers 2022-06-01 to 2026-02-25 —
  the window since the last LGE — so no historical target has by-election data
  at all, and `w_bye` (0.40) is equally inert in every backtest above. The term
  is **untestable with the data held**, not merely untested, and the only way to
  change that is to scrape the 2011–2021 by-election windows.

---

## 1.31 The arrival channel was working and the scoreboard could not see it (2026-08-16)

The question asked was whether any *defensible judgement call* would improve the
backtests. `entrant_prob` was the obvious candidate: §A of `JUDGEMENT-CALLS.md`
already called it "the most quotable undefended constant in the model", it is
typed at **0.25**, and the base rate is measurable — **an arrival won at least one
seat in 7 of the 9 backtested city-years (78%), median 3 arrivals apiece**:

| city-year | arrivals winning seats |
|---|---|
| Johannesburg 2016 | 2 |
| Johannesburg 2021 | 3 |
| Tshwane 2021 | 3 |
| Ekurhuleni 2021 | 3 |
| eThekwini 2021 | 10 |
| Cape Town 2021 | 7 |
| Mangaung 2021 | 0 |
| Nelson Mandela Bay 2021 | 4 |
| Buffalo City 2021 | 0 |

So it was swept over the nine city-years at 0.25 and 0.55. The two rows came back
**byte-identical** — CRPS 269.9, coherent-seat error 336, ranks 4-12 −42.9pp, at
both values.

### Why: a scoring fault, not a model fault

The instrumented run says the machinery works. On Johannesburg 2016, where the
**AIC arrived and took 1.62% of the list vote and 4 seats**, the generic slot drew:

| `entrant_prob` | ENTRANT mean list share | ENTRANT mean seats |
|---|---|---|
| 0.25 | **1.39%** | **3.82** |
| 0.99 | 5.43% | 14.98 |

At the committed 0.25 the model sized the arrival **almost exactly right**. The
scoreboard then threw the answer away. `compare_history.run_city_year` computed
`entrant_actual` and passed it to `score_seats` **and to nothing else** — not to
`vote_table`, not to `rank_bands`, not to `seats_from_draws`, not to
`coherent_seats`. So for that city-year the record read:

* AIC list mean **`NaN`**, flagged *"missed entirely — won seats, median zero"*;
* 4 seats of error for the AIC seats not forecast;
* **plus** 4 more for the phantom `ENTRANT` seats, since `ENTRANT` is a key in
  `coherent` and not in `actual_seats`;
* and ranks 4-12 short by the 1.39pp the model had actually put there —
  in the band this model is already most short in.

Eight seats of error on a forecast that was right, in every city-year where a
party arrived, which is seven of nine.

This is the **same class of fault as the turnout band capped at the observed
maximum**: not the model being wrong, the *instrument* being wrong, in exactly
the runs used to judge the model. `backtest.relabel_entrant` had already fixed
this once, for ward probabilities, and its docstring says why — *"the model
punished for the one thing the entrant machinery exists to get right"*. The fix
did not generalise because it was applied at one call site instead of at the run.

### The fix

`backtest.relabel_run(run, entrant)` renames the generic column **on the run
itself**, once, immediately after `entrant_actual` is known and before any table
is built, so every downstream helper inherits it. It merges rather than renames
if the arrived party somehow already holds a column.

On Johannesburg 2016 alone, at 400 draws:

| | before | after |
|---|---|---|
| AIC list mean vs actual 1.62% | `NaN` | **1.35%** |
| AIC ward mean vs actual 1.40% | `NaN` | **1.41%** |
| ranks 4-12 signed error | −2.34pp | **−0.92pp** |

Note what the fix does **not** do: in a city-year where no party arrived,
`entrant_actual` is `None`, the relabel is a no-op, and the entrant's phantom
seats are still counted as error. That is correct — the model should pay for
predicting an arrival that did not happen. It is also what makes `entrant_prob` a
real trade-off for the first time: raising it helps the seven city-years with an
arrival and hurts the two without.

### And then it still would not sweep — the second fault

With the relabel in, `entrant_prob` was swept again over the nine city-years,
0.25 against 0.50, by editing `montecarlo.DEFAULTS`. **The rows came back
byte-identical a second time.** The AIC's predicted mean was 1.42280805013110%
at both values, to sixteen figures.

`montecarlo.DEFAULTS` is not what a city-year runs on. `compare_history` calls
`apply_city` before `load_scenario`, and `apply_city` copies
`cities/<city>.toml`'s scalars *over* DEFAULTS. `cities/joburg.toml` sets
**sixteen** of them, `entrant_prob = 0.25` among them, so the edit was reverted
before it could be read.

And DEFAULTS is a module global that `apply_city` never resets. Six of the eight
metro configs set no scalars at all. So in a multi-city run **every city after
Johannesburg inherits Johannesburg's sixteen judgement values** — its `w_bye`,
its `f_other`, its `pa_contestation_uplift`, its turnout constants. That is
harmless today, and only for a reason the code does not enforce: those sixteen
currently equal DEFAULTS, because joburg.toml was generated from them. The next
per-city tuning breaks it silently.

`compare_history` gained `--set KEY=VALUE`, threaded through `run_city_year` and
applied *after* `apply_city`, which is the only override that survives. Swept
honestly, `entrant_prob` is emphatically not inert — at 0.99 on Johannesburg
2016 the entrant lands at **5.35% against the AIC's actual 1.62%** and takes 14
seats against 4, and ranks 4-12 flips from −0.92pp to **+2.87pp**.

**So the answer to the question that started this is no.** `entrant_prob` was
the strongest candidate for a defensible upward revision — a typed 0.25 against
a measured 78% base rate — and once it could be measured at all, the typed value
turned out to be close to right and raising it makes the forecast worse. The
base rate answers "how often does *an* arrival win a seat", which is not the
question the constant asks; the constant asks how big *the largest* arrival is,
and at 0.25 × E[triangular(1%, 4%, 12%)] = 1.42% it is already sized on that.

Both faults are now covered by **CLASS 11 — a constant that cannot be swept**, in
`tests/test_regressions.py`, along with a test that fails the moment
`cities/joburg.toml` and `DEFAULTS` disagree on any key.

### What the fix left behind, measured

With the instrument corrected the nine city-years read:

| | before | after |
|---|---|---|
| coherent seat error, 9 city-years | 336 | **314** (uniform swing 376, last-LGE 594) |
| beats uniform swing | 4/9 | **6/9** |
| ranks 1-3 | +35.5pp | +35.8pp |
| ranks 4-12 | −42.9pp | **−37.4pp** |
| ranks 13+ | −6.0pp | −4.6pp |

Per city-year, model against uniform swing: Johannesburg 2016 **22/26 W**, 2021
**104/126 W**, Tshwane **42/60 W**, Ekurhuleni **30/48 W**, eThekwini 36/36 L,
Cape Town 42/38 L, Mangaung 10/8 L, Nelson Mandela Bay **20/22 W**, Buffalo City
**8/12 W**. The three losses are narrow; the wins are not.

**The remaining −37.4pp is not an arrivals problem and cannot be tuned away.**
Of it, only **−0.69pp** is parties the model never carried at all, so extra
entrant slots would buy essentially nothing — a negative result worth the space,
because "give the model more entrant slots" is the obvious next move and it is
wrong. 97% is parties the model *does* carry and under-forecasts.

Nor is it a dispersion problem. The fitted `sd_for(size)` was checked against the
realised spread of each party's own θ record at Johannesburg 2021:

| | model sd | measured sd |
|---|---|---|
| ANC (56% of baseline) | 0.150 | 0.053 |
| DA (30%) | 0.159 | 0.103 |
| IFP (1.8%) | 0.281 | 0.337 |
| VF+ (0.9%) | 0.320 | 0.391 |
| PA (0.07%) | 0.540 | 0.952 |

Median model/measured ratio **0.96** over 14 parties. The level spread is
calibrated — slightly wide at the top, slightly narrow at the very bottom.
Widening it to chase the misses below would break the calibration everywhere.

### Where it actually is: parties carried at a token value

Ranking the 79 parties in the 4-12 band across the nine city-years by how far
the model was under:

| city-year | party | predicted | actual | |
|---|---|---|---|---|
| Cape Town 2021 | Cape Coloured Congress | 0.07% | 2.83% | **39.6×** |
| Johannesburg 2021 | PA | 0.08% | 2.96% | **39.4×** |
| Nelson Mandela Bay 2021 | Northern Alliance | 0.12% | 2.09% | 17.2× |
| Nelson Mandela Bay 2021 | DOP | 0.10% | 1.38% | 13.3× |
| Cape Town 2021 | Africa Restoration Alliance | 0.06% | 0.64% | 11.1× |
| Ekurhuleni 2021 | PA | 0.17% | 1.87% | 11.1× |
| eThekwini 2021 | Active Citizens Coalition | 0.09% | 0.81% | 8.5× |

The median party in the band is under by 1.64×; **16 of 79 are under by more
than 5×, and those 16 alone carry +16.4pp of the −37.4pp.** Every one of them is
predicted at **0.05–0.17%** — a token value — and every one is a locally
organised party standing seriously in that metro for the first time.

They are *effectively* arrivals, and the model does not treat them as such,
because the arrival test is "no baseline at all" and each of these had a trace
in the preceding national election in that metro. So each is routed through
θ × (a baseline of ~0.1%), and θ near 0.9 keeps it there. The model already
knows those records are worthless — `RELIABILITY_HALF = 0.002` gives a 0.07%
baseline a reliability of 0.26, so its θ is mostly the group centre — and then
applies the group centre to a number that means nothing anyway.

**The arrival record for these same city-years says a typical arrival takes
1.64% (IQR 1.43–2.29%, n=9 before 2021).** That is close to what these parties
actually got. So the identified change is: **move the arrival boundary from "no
baseline" to "no *usable* baseline"**, with the threshold taken from the
reliability function already in the code rather than invented. Expected reach:
up to ~16pp of the ranks 4-12 deficit. NOT YET BUILT, and not a constant that
can be swept — it is a change to which machinery sizes a party.

### The sweep, done honestly — and the difference between "better" and "defensible"

Through `--set`, over the nine city-years at 1200 draws:

| `entrant_prob` | CRPS | coherent-seat error | beats uniform swing | ranks 1-3 | ranks 4-12 | ranks 13+ |
|---|---|---|---|---|---|---|
| **0.25** (committed) | 269.9 | **314** | **6/9** | +35.8 | −37.4 | −4.6 |
| 0.35 (derived, below) | **267.7** | 316 | **6/9** | +30.7 | −35.1 | −4.0 |
| 0.40 | 268.1 | **314** | **6/9** | +29.0 | −34.9 | −4.0 |
| 0.55 | 274.0 | 322 | 5/9 | +21.9 | **−31.8** | −3.2 |

The bands improve monotonically — the entrant is filling the mid-ballot, which
is the band the model is short in — but CRPS and seat error turn at about 0.40
and are clearly worse by 0.55. So there is an optimum near 0.40.

**And taking it would not be defensible.** 0.40 is better on these nine
city-years *because it was chosen on these nine city-years*. Nothing outside
them picks it, and the seat error does not move at all (314 either way): the
gain is CRPS 1.8 and 2.5pp of band, redistributed rather than won — Cape Town
improves 42→38, Johannesburg 2016 worsens 22→24, eThekwini 36→38. Adopting it
would be fitting the constant to the scoreboard, which is the one thing this
register exists to catch.

There **is** a derivation available, and it is out-of-sample. The arrival record
for these city-years — the observed entry sizes of parties that arrived *before*
each target — has median 1.641% and mean 1.998%. The model's expected entrant
share is `entrant_prob × E[triangular(1%, 4%, 12%)]` = `entrant_prob × 5.667%`.
Matching the record gives:

* **0.290** to match its median
* **0.353** to match its mean

The committed 0.25 sits just below that range and the empirical optimum just
above it. **0.35 was then measured on its own account** and lands where that
predicts: the best CRPS of any value tried (267.7) and two more seats of error
(316 against 314). Across 0.25 → 0.40 the seat error moves by 2 in 314 and the
CRPS by 2 in 268 — the whole range is inside the noise.

That the whole range is noise is not an assertion. The same committed 0.25 run
at **1500** draws instead of 1200 returns **316**, not 314 — so the draw noise on
this measure is itself ±2 seats, which is the entire spread across 0.25, 0.35 and
0.40. Nothing in that range is distinguishable from anything else in it.

So the verdict is: **leave `entrant_prob` at 0.25.** The derivation brackets the
incumbent, the empirical optimum is indistinguishable from it, and the only value
that clearly *is* different (0.55) is clearly worse. If it is ever moved it
should be moved to ~0.35 with the arrival record cited, never to 0.40 with the
backtest cited — and the change would be cosmetic either way.

### One open observation, not chased

The suite emits, on the current tree:

    ! 0.60% of the citywide level asked for more than a party's own pools can
      supply and was clipped (PA). Those parties belong to fewer pools than
      their level implies; check their vectors.

PA again, and from the opposite direction to the backtest misses above: in the
2026 configuration its level *exceeds* what its pool membership can supply, so
it is clipped. Both symptoms point at the same thing — PA's pool vector is the
one the model is least able to represent — but they are not the same defect and
this one is untested by any backtest. Recorded so it is not rediscovered.

### The general lesson, which is the third instance of it

Three times now the thing that looked like a modelling deficiency was a
measurement deficiency:

1. the turnout band capped at the observed maximum, bound at 4/4 pools for 2016;
2. `home_splinter_record` reading a 2024 result at target 2021;
3. this.

All three made the model look **worse** than it was, which is the direction that
does not get caught by wanting the number to be good. The guard that generalises
is not another test of a constant — it is: **before tuning a constant, sweep it
to a value that must change the answer, and confirm the answer changes.** A
constant whose extreme value changes nothing is not calibrated, it is
disconnected. That check is cheap and it is what found this.

---

## 1.32 The arrival machinery: the total was right by luck and the split was wrong (2026-08-17)

The task named at the end of §1.30 — "fix the arrival machinery, which is half
the missing small-party seats" — done, after two wrong turns worth recording
because each was measured.

### What was actually broken

`pools.arrival_rules` sized an entrant at `np.median(peers)`, the median of the
arrivals that contested about as much of the city. The band around it ran
`[q25, median, q95]`, typically **17–24× the seed** at the top. That band could
never do anything, because `pool_spec` balances both margins by IPF and **IPF
pins each party's mean to its centre**. Measured on eThekwini 2021, Active
Citizens drew p50 0.0083% and p95 0.3613% — a 44× spread, correctly shaped —
around a mean of 0.0798%, against an actual 0.81%.

So the right tail survived only as spread about a centre four times too low.

### Wrong turn one: seed at the mean

Arrival sizes are violently right-skewed. Over the 77 arrivals on record before
2021 the median is 0.0498% and the **mean 0.2378%**, a ratio of 4.78; among
wide-reach arrivals, 0.0798% against **0.3398%**, 4.26. Since IPF pins the mean,
whatever goes in `centres` *is* the expected value, so it should be the
expectation. Applied, re-emitted, scored:

| | seat error | beats u-swing | 1-3 | 4-12 | 13+ |
|---|---|---|---|---|---|
| median seed (committed) | 316 | 6/9 | +35.5 | −37.1 | −4.6 |
| **mean seed** | **322** | **5/9** | +10.2 | −37.3 | **+19.4** |

**Worse.** The mean is right per party and wrong per city, because a city fields
twenty to forty arrivals: 30 × 0.34% is a **10.2% arrival total** against a
record whose median is 1.64% and whose maximum over sixteen metro-years is
4.74%. The over-allocation landed exactly where it was put — ranks 13+ went from
−4.6pp to +19.4pp — and ranks 4-12 did not move at all.

The median seed had been getting the group total right **by luck**: 30 × 0.08%
≈ 1.6%, which is the record. Nobody chose that; it fell out.

### What shipped: hold the total, split by reach

The group TOTAL is the quantity that behaves regularly (§1.24's finding, and the
reason `arrival_group_record` exists). The SPLIT is what ward reach predicts —
arrivals contesting 60–90% of wards clear 0.5% at **27.3%** against 7–8% in
every other reach band. So: take the reach-matched **mean** for the relative
weighting, where it carries the reach signal, and **rescale the whole entrant
group to the arrival-total record** (`_arrival_total_prior`, median of city-years
strictly before the target). Splitters are untouched — ActionSA in Johannesburg
is a splinter and stays at 5.08%; the thirty-one entrants around it now sum to
exactly 1.64%.

| | seat error | beats u-swing | 1-3 | 4-12 | 13+ |
|---|---|---|---|---|---|
| median seed (was committed) | 316 | 6/9 | +35.5 | −37.1 | −4.6 |
| mean seed | 322 | 5/9 | +10.2 | −37.3 | +19.4 |
| **group total, reach split** | **312** | **7/9** | +32.4 | −37.3 | **−1.7** |

eThekwini flips from a loss to a win (36 → 34). Both numbers are measured on
transitions strictly before the target and neither is fitted to a backtest score.

### What it does NOT fix, and this is the honest limit

**Ranks 4-12 did not move: −37.1 → −37.3pp.** All three variants leave it
untouched. The mechanism can redistribute the arrival group and get its total
right; it cannot say *which* arrival will be the big one. Cape Town 2021's
arrivals totalled 4.74% with the Cape Coloured Congress alone taking 2.83%, and
nothing in a nomination list distinguishes it from the twenty other parties on
the same ballot with the same ward reach.

That is the same wall as §1.30's: the model is good at parties a national
election has already measured and bad at unknown ones. It is now good at the
*aggregate* of the unknown ones too. The individual remains out of reach, and
the honest thing is to say so on the site rather than keep tuning at it.

---

## 1.33 The centres did not bind in two draws out of five, and nothing said so (2026-08-17)

Two defects from an independent review, both of the same shape: a piece of
machinery that does not run, reports nothing when it does not run, and therefore
reads as working.

### F1 — `except Exception: pass` around the mechanism the whole layer is named for

`draw_pools` shocks the pool × party centres, re-balances them by IPF so the
shock survives into the draw (§1.30), and wrapped the balance in
`except Exception: pass`. When `pools.balance_margins` raised, `pool_props` kept
the **unshocked** values — so the level shock was discarded **for every party in
that draw**, not just for the party that made the problem infeasible.

Measured, 300 draws per city-year, before the fix:

| city-year | balances | raised | rate |
|---|---|---|---|
| **Johannesburg 2026 (the live forecast)** | 300 | 128 | **42.7%** |
| Nelson Mandela Bay 2021 | 300 | 38 | **12.7%** |
| Johannesburg 2016, Johannesburg 2021, Tshwane, Ekurhuleni, eThekwini, Cape Town, Mangaung, Buffalo City (all 2021) | 300 each | 0 | 0.0% |

Two things about that table matter more than the headline. **It fires almost
entirely in the forecast nobody can score** — over the nine backtested
city-years the rate is 1.4%, and the review found that forcing it to zero left
the backtest output bit-identical, so no amount of backtesting could have found
it. And **it fires preferentially on the draws where the shock is largest**,
because that is what makes the problem infeasible — the mechanism was absent
exactly where it mattered most.

(The review checked five of the nine and reported 0.0% for all of them. Nelson
Mandela Bay was not among the five and is the second site; it is here because it
was measured, not because it was expected.)

**It is not slow convergence.** 20,000 iterations at tol 1e-9 gives 38.9%
against 40.9% — essentially no change. It is genuine infeasibility: a party
asking for more votes than exist in the pools it belongs to. IPF preserves
structural zeros, so a party's ceiling is the votes cast in its own pools, and
above that no matrix satisfies both margins at all.

**The party is the PA and the number is 102%.** It is a member of exactly one
pool at Johannesburg 2026 — Coloured, weight 1.0000, and at 2026 that weight is
flagged `identified=False`, a bound-limited artefact rather than a measurement.
The pool holds 122,771 registered voters (5.2% of the roll) at a modal turnout
of 0.543, so it casts about 66,700 votes. The spine gives the PA 6.65% of the
city, the by-election blend takes it to 7.4% — about 68,000 votes. That is 102%
of every Coloured vote cast in Johannesburg before any shock is applied, and the
shock has asked for as much as 254% of it. The run already printed
`! 0.60% of the citywide level asked for more than a party's own pools can
supply and was clipped (PA)` and nobody connected the two lines.

#### The cause is upstream, and this change does NOT fix it

The chain, measured rather than argued:

1. **`fit_joint` returns a corner solution.** The PA's Johannesburg 2021 rates
   are `Coloured 0.5149` and **exactly 0.0000** on Black African, Indian/Asian
   and White — FISTA's simplex projection sitting on the non-negativity
   boundary. The emitted "Coloured 1.0000" vector *is* that corner.
2. **0.5149 is 10.5pp above the PA's own Duncan-Davis ceiling of 0.410**, which
   this code computes and then uses only to set a display flag. `MACHINERY.md`
   §0 claimed "every estimate is projected into its Duncan-Davis interval";
   `pools.bounds` is read at exactly one place, `PoolFit.identified`, and
   nothing projects. That sentence has been corrected rather than deleted, with
   the reason, in the same commit.
3. **The ward geography refutes the corner directly.** Binning all 135
   Johannesburg wards by Coloured share, 71.9% of the PA's vote arises in wards
   over 30% Coloured — but **28.1% arises below that**: 18.2% in 10–30% wards
   and 9.9% in wards under 10% Coloured. A 100/0 vector is not what the data
   says. Implied citywide, the corner gives the PA 34,170 votes against an
   actual 27,346.
4. Hence a single-pool vector; hence a 2026 level the pool layer cannot express;
   hence a per-draw IPF that fails in two draws out of five; hence a silent
   `pass`.

**Everything below is a guard on step 4.** Whether the vector is too narrow or
the level too high is contested and needs its own measurement, and nothing here
settles it. The value of the guard is that the disagreement is now safe and
visible instead of silent.

#### What was done

* **A pool-capacity ceiling, water-filled.** The shocked column targets are held
  under `POOL_CAPACITY_MARGIN = 0.98 ×` each party's own pool capacity before
  the balance (`montecarlo.capped_targets`, applied in both `pool_spec` and
  `draw_pools`). Johannesburg 2026: **42.7% → 0.0%**.
* **The `pass` is gone.** The fallback is now the same bounded alternating
  scaling `pool_spec` has always used one stage earlier
  (`montecarlo.partial_balance`), so a failure degrades the shock instead of
  deleting it; and it is counted onto `ModelRun.ipf_failures` /
  `.ipf_balances` / `.ipf_clipped` / `.ipf_worst` / `.ipf_headroom`, the way
  `bounds_violations` already was, and printed by `main`.
* **The report names the party and the ratio.** Before any draw:
  `! at or near their pools' capacity before any shock: PA 98%`. After:
  `per-draw centre balance: 600 attempted, 0 fell back (0.0%)` and
  `PA 39.2% worst 204% of capacity`. "125 balance failures" would not have found
  this; "PA, asked 204% of its pools' capacity, in 39% of draws" would have
  found it in one run.

#### A NAIVE CLIP DOES NOT WORK — measured, and this is the trap

Two sites rescale the column margin and would undo it:

* `pool_spec` clipped at the ceiling and then wrote `want = want / want.sum()`;
  after a clip that sum is below one, so the divide put the clipped party
  straight back over its own ceiling. **The order was also wrong**: the clip was
  applied to the raw centres and the normalisation afterwards, when the quantity
  that has to be feasible is the normalised one. Normalise first, then cap.
* `pools.balance_margins` opens with
  `target_cols *= target_rows.sum() / target_cols.sum()`, because IPF has no
  solution unless the two margins agree on the grand total. Hand it column
  targets that sum short and it restores exactly the mass the clip removed —
  to the offender included.

So `capped_targets` preserves the total to floating point and moves the excess
sideways, in proportion to what the remaining columns already hold, iterating
until nothing is over its cap. `tests/test_ipf_feasibility.py::
test_capped_targets_preserves_the_total_it_is_given` pins that invariant over
200 random cases, because it is the one a future edit would break.

#### There are TWO ways for the margins to conflict and the clip fixes ONE

A **column** can ask for more than its pools hold. That is the PA, and the cap
removes it.

A **row** can hold more votes than its members' targets add up to. That is
Nelson Mandela Bay 2021's Indian/Asian pool: 8,303.3 votes against 8,168.5 asked
of its sixteen members between them. It cannot be removed by moving the party
margin without re-creating the column case, so **the cap does nothing for NMB**:
no party there is within half of its capacity (maximum headroom 0.48, and
`ipf_clipped` is empty for the whole run), and with the cap in place and the
fallback still `pass` the city's backtest output is bit-identical to the
committed one. The row conflict goes to `partial_balance` and is counted: 38 of
300 draws (12.67%) before, 42 of 300 (14.00%) after. **That difference is not a
change in the failure mechanism** — `rng.dirichlet` consumes a
value-dependent number of variates through its rejection sampler, so the moment
one draw's pool proportions differ the stream diverges and the counts are two
samples of the same rate rather than a before and an after.

#### Results

**Johannesburg 2026, 600 draws** (mean citywide PR share):

| | before | after |
|---|---|---|
| per-draw balance fallback rate | **41.8%** | **0.0%** |
| DA | 32.81% | 32.66% |
| ANC | 20.01% | 20.21% |
| ASA | 12.02% | 11.82% |
| MK | 10.26% | 10.55% |
| EFF | 9.10% | 8.51% |
| PA | 5.75% | **6.02%** |
| DA realised sd(log) | 0.168 | **0.189** |

Seat medians are unchanged to within a seat (DA 88→87, ANC 61→62, ASA 26→26,
MK 24→24, EFF 23→21, PA 17→18); the bands widen at the top, which is the point —
DA 67–116 → 64–118, MK 8–56 → 8–59. The DA's realised sd(log) moving 0.168 →
0.189 against a measured 0.15–0.35 is the mechanism arriving in the 42% of draws
it had been absent from.

**The nine city-years, 400 draws.** Eight of nine are **bit-identical**. Only
Nelson Mandela Bay 2021 moves, and every one of its numbers improves:

| | before | after |
|---|---|---|
| list MAE | 2.73pp | 2.34pp |
| ward MAE | 3.24pp | 2.83pp |
| seat error (median) | 24 | 22 |
| **seat error (coherent)** | **20** | **16** |
| CRPS | 18.1 | 17.8 |
| ranks 1-3 abs | 7.67pp | 6.44pp |
| ranks 4-12 abs | 6.55pp | 6.18pp |

### CORRECTION, same day: the backtest improvement above is DRAW NOISE

Everything from here to the end of this subsection was written at **400 draws**
and it does not survive. It is left in place rather than deleted, because the
mistake is the instructive part.

The claim was: 312 → 308 over the nine, Nelson Mandela Bay 20 → 16, and — since
eight city-years did not move by a single count — the whole of it attributable
to the one city-year where the mechanism fired. The reasoning is sound in form
and wrong in fact, because **the ninth city-year's own seed noise is the same
size as the effect.**

An independent reviewer A/B'd it at **1500** draws, five seeds per arm, by
patching `partial_balance` to return the row-normalised `R0` (which reproduces
the old per-draw `except: pass`):

| arm | NMB coherent seat error, five seeds | mean | CRPS |
|---|---|---|---|
| new (`partial_balance`) | 20, 20, 18, 18, 18 | **18.8** | 17.91 |
| old (`pass`) | 20, 18, 20, 18, 20 | **19.2** | 17.91 |

Seed-to-seed spread is 2 seats **in both arms**; the gap between arms is 0.4, and
`pr_mae` is marginally *better* in the old arm. The committed `history.json` at
1500 draws gives Nelson Mandela Bay **20**, not 16, and a nine-city-year total of
**312** — identical to the figure this section was comparing against.

**So: the fix is correct and its backtest benefit is nil.** Both halves of that
sentence matter. A mechanism discarded in 42.7% of the published forecast's draws
is a defect whatever the backtest says, and it fires almost entirely where no
backtest can score it — which is exactly why a backtest gain was never the reason
to make the change and should never have been quoted as one.

This is `ITERATING.md` rule 6 one level up. The rule says a constant must be
swept to a value that must change the answer before it is tuned. The same
discipline applies to a *result*: **the first thing a measurement must establish
is that it measured something.** 400 draws could not, and the number was reported
anyway because it pointed the way the change was hoped to point.

Third instrument failure in three days, and the only one where the instrument was
a draw count.

#### What did not work

* **A plain `np.minimum(target, ceiling)`.** Undone by both rescale sites above;
  `balance_margins` restores the removed mass on its first line. This is not a
  hypothetical — it is the shape the first attempt took.
* **More iterations.** 20,000 at tol 1e-9 moved the 2026 failure rate 40.9% →
  38.9%. Infeasibility does not converge.
* **A tighter margin than 0.98.** Swept on the 2026 forecast, 600 draws:
  `POOL_CAPACITY_MARGIN` at 1.0000 leaves the rate at **41.5%**, 0.9999 at
  41.5%, 0.9975 at 41.0%, 0.995 at 39.8%, 0.992 at 37.0%, 0.991 at 37.0% — and
  then **0.990 and 0.980 both give exactly 0.0%**. A cliff, not a slope, which
  says the last percent is a CONVERGENCE-RATE problem rather than a feasibility
  one: `balance_margins` stops at a relative tolerance of 1e-12, IPF approaches
  a boundary solution geometrically, and inside about 1% of the boundary 2,000
  iterations are not enough. (The review reported 40.1% at 1.00 and 22.4% at
  0.999 for the same sweep; 22.4% does not reproduce here and 41.5% / 41.5%
  does. The disagreement does not change the choice — everything at or below
  0.99 is zero — but the 0.999 figure should not be quoted.) 0.98 is kept rather
  than 0.99 because it is a round number one full step clear of a cliff edge
  whose position is a function of the iteration cap, not of the model.
* **60 passes instead of 200 in the per-draw fallback**, to save time. Measured
  at Nelson Mandela Bay against the 200-pass matrix: 30 passes differ by 186
  votes, 60 by 45.6, 100 by 16.7, on a city of 364,000. The saving was not worth
  a number that differs from the committed one for no stated reason, so
  `PARTIAL_BALANCE_PASSES` stays at 200 at both sites.

### F6 — `LEVEL_DF` was inert at every value

```python
def log_shock(rng, sd, size=None, df: float = LEVEL_DF):
```

Python evaluates a default argument **once, at import**. Setting
`montecarlo.LEVEL_DF` afterwards changed nothing, and the review swept it at
2.5, 4, 7, 30, 200 and 1000 for **byte-identical output every time**.
`JUDGEMENT-CALLS.md` carried it at 🔴 — one of the numbers most in need of
attack in the register — and it did nothing at any value. This is `ITERATING.md`
rule 6 live: *before tuning a constant, sweep it to a value that MUST change the
answer, and confirm the answer changes.*

It is the same class as §1.31's `entrant_prob`, reached by a different route
(there, `apply_city` overwrote the edit; here, the binding froze it). Both look
identical from the outside: a sweep that returns identical rows.

`df` now resolves `LEVEL_DF` in the function body from a `None` sentinel.
**The value is unchanged at 7.0.**

#### The sweep, now that it is possible

Johannesburg 2026, 3,000 draws, same seed:

| df | MK p99 | MK p99.9 | MK max | ALJAMAAH max | DA sd(log) | MK sd(log) |
|---|---|---|---|---|---|---|
| 3 | 24.95% | 32.66% | **46.23%** | 4.85% | **0.2395** | 0.6339 |
| **7** | 26.14% | 33.69% | **37.53%** | 2.99% | **0.1886** | 0.6041 |
| 1000 | 25.23% | 30.49% | **33.78%** | 3.49% | **0.1835** | 0.5985 |

So the constant does what it claims to do — it is a **tail** parameter, and at
df=3 it inflates the largest party's realised dispersion by 27% over the normal
limit — and it does not do what it was suspected of doing. **MK's wide seat band
is not the Student-t tail**: at 600 draws MK's 5th–95th seat band is 8–53 at
df=2.5 and 8–57 at df=1000, essentially unmoved across a factor of 400 in tail
weight. That band is the within-pool Dirichlet plus the correlated turnout
copula, and anyone who goes after it through `LEVEL_DF` will spend a day for
nothing. Recorded here so they do not.

The nine city-years, 400 draws — the first honest sweep of this constant:

| df | coherent seat error | beats uniform swing | ranks 1-3 abs | ranks 4-12 abs |
|---|---|---|---|---|
| 3 | 316 | 6/9 | 72.07pp | 58.09pp |
| **7 (committed)** | **308** | **7/9** | **70.83pp** | **55.95pp** |
| 30 | 308 | 6/9 | 72.23pp | 56.54pp |

**The typed value survives its first measurement.** It ties df=30 on seat error
and beats it on beats-uniform-swing and on both absolute bands, and beats df=3
on everything. That is thin evidence — 308 against 308 is inside draw noise —
but it is evidence where there was none, and `LEVEL_DF` is demoted 🔴 → 🟡 on
the same terms `entrant_prob` was in §1.31: still typed, now swept.

### Four more constants were frozen the same way

An AST walk of `src/` found the same binding at four other sites, all numeric,
all invisible to a sweep:

| site | constant |
|---|---|
| `fold.logit` | `SHARE_FLOOR` |
| `montecarlo.logit` | `SHARE_FLOOR` |
| `montecarlo.solve_and_predict` | `SHARE_FLOOR` (as `level_floor`) |
| `levels.spine` | `SPINE_K` |

`SPINE_K` is at 🔴 in the register with a rejected step-function alternative
recorded against it — a constant nobody could have swept. All four now resolve
in the body. Five further sites capture module-level *containers* or *paths*
(`METRO_CODES` ×4, `REPORTS`, `REGISTER`, `CONFIG`, `CLAIM_PATTERNS`); they have
the same hazard in principle but nothing sweeps them and mutating them in place
does reach the default, so they are exempted **by name** in the test rather than
silently.

### The tests

New file `tests/test_ipf_feasibility.py`, five tests, and **all five fail on the
pre-fix code**:

| test | failure message on the old code |
|---|---|
| `test_the_balance_is_never_asked_for_more_than_the_pools_can_hold` | *the per-draw IPF was handed a column target above that party's own pool capacity (254% of it) — draw 55, column 34: capacity 66,684.8 votes, asked 169,241.8* |
| `test_a_failed_balance_is_counted_and_reported_rather_than_passed` | *make_drawer's closure carries no ipf_stats, so run_model has no way to learn that the per-draw balance failed and no test can assert on it* |
| `test_capped_targets_preserves_the_total_it_is_given` | *module 'montecarlo' has no attribute 'capped_targets'* |
| `test_level_df_reaches_the_draw` | *log_shock returned the same draws at LEVEL_DF 2.5 and 1000, which differ by two orders of magnitude in tail weight* |
| `test_no_numeric_module_constant_is_a_default_argument` | names all five sites: `fold.py:110 logit(... = SHARE_FLOOR)`, `levels.py:459 spine(... = SPINE_K)`, `montecarlo.py:237 logit(... = SHARE_FLOOR)`, `montecarlo.py:288 log_shock(... = LEVEL_DF)`, `montecarlo.py:458 solve_and_predict(... = SHARE_FLOOR)` |

The first asserts on the **numbers the balance was handed**, not on the source
text, because a clip written into the code and undone by a later rescale would
pass a source check and fail this one — which is exactly the failure mode the
first attempt had. The last is the generalising one: it is what stops the class
rather than the instance.

`tests/test_drawer.py`'s golden prior was re-recorded, deliberately, with the
reason and the before/after in the file.

### Open, and named so it is not mistaken for closed

* **The ecological fit is not projected into its own bounds.** Steps 1–3 above.
  This is the cause; everything in F1 is a guard on the symptom.
* **The PA's 2026 level and its pool vector disagree by 2%** even after the
  clip, and the clip resolves that against the level. Whether that is right is
  not settled here.
* **`POOL_CAPACITY_MARGIN = 0.98` is typed**, chosen as the largest round number
  that takes the failure rate to zero. It is in the register at 🔴.
* **Nelson Mandela Bay 2021 still falls back on 13-14% of draws**, for the row
  reason, which no column cap can fix. It is now counted and printed instead of
  silent, and the fallback is a partial balance rather than nothing — worth 4
  coherent seats — but the underlying conflict stands.

---

## 1.34 The scoreboard could not see the model's largest error, and one of its statistics was hiding it (2026-08-17)

**No forecast moved. Only what the scoreboard reports.** Every seat error and
every CRPS in `data/processed/history.json` is unchanged: at 1500 draws the
coherent seat error is **312** across the nine city-years, it beats uniform swing
**7/9**, and the signed bands are 1-3 **+32.42pp**, 4-12 **−37.30pp**, 13+
**−1.65pp** — the committed figures to the digit. Two before/after runs at 400
draws are identical on `seat_abs_err`, `seat_abs_err_coherent` and `crps` in all
nine city-years, and differ in the tenth significant figure of `pr_mae` for
eThekwini alone, which is float-reduction noise.

Both defects were found by an outside review. Both are instrument faults, which
is the reason they survived: nothing they touched ever looked wrong.

### F2 — a signed band total is not a measure of error

`compare_history.rank_bands` reported a SIGNED sum of per-party error inside each
rank band, and its docstring defended the choice ("the sign is the finding").
The sign IS a finding — it is what shows ranks 1-3 eating ranks 4-12 — but
reported alone it nets out offsetting errors, and the band then reports as
accurate when it is nothing of the kind.

Recomputed with absolute per-party error inside the same bands (1500 draws):

| city-year | 1-3 signed | 1-3 ABS | 4-12 signed | 4-12 ABS | coherent seat error |
|---|---|---|---|---|---|
| Johannesburg 2016 | +0.46 | 5.55 | −0.81 | 1.60 | 22 |
| **Johannesburg 2021** | **+1.32** | **26.50** | −2.40 | 10.00 | **106** |
| Tshwane 2021 | +7.78 | 7.78 | −8.99 | 8.99 | 40 |
| Ekurhuleni 2021 | +5.84 | 5.84 | −5.84 | 7.82 | 30 |
| eThekwini 2021 | +2.54 | 3.87 | −1.73 | 8.60 | 34 |
| Cape Town 2021 | +7.84 | 7.84 | −6.87 | 6.87 | 42 |
| Mangaung 2021 | +1.12 | 1.25 | −3.10 | 3.72 | 10 |
| Nelson Mandela Bay 2021 | +6.15 | 8.13 | −6.16 | 6.30 | 20 |
| Buffalo City 2021 | −0.63 | 4.89 | −1.39 | 1.90 | 8 |
| **TOTAL** | **+32.42** | **71.65** | −37.30 | 55.81 | **312** |

**Johannesburg 2021 read +1.32pp on the published statistic and is 26.50pp
wrong.** ANC +6.52 and DA +7.39 cancel against ActionSA −12.59 (39.75% forecast
against 33.22% actual, 32.84 against 25.45, 5.53 against 18.12). It is the
model's WORST city-year on seats — 106 of 312, a third of the total error from
one of nine city-years — and it was the SECOND-BEST row of the headline band
table. The signed nine-city-year total understates the top-of-ballot error by
**2.2×**. (The review measured +1.36 / 26.69 and a total of +32.67 / 72.06 at a
different draw count; the reading is not sensitive to it.)

Note also what the absolute column does to the reading of the whole table.
Signed, ranks 1-3 (+32.42) and ranks 4-12 (−37.30) look like one story: the top
is eating the middle, roughly point for point. Absolute, ranks 1-3 (71.65) is
*larger* than ranks 4-12 (55.81), so the top of the ballot is not a
well-forecast band that has been handed someone else's votes; it is the worse of
the two. Every "the model over-predicts the top three and under-predicts the
middle" sentence in this log is true of the net and incomplete about the size.

**Both columns are now printed, and neither replaces the other.** Where they
agree (Tshwane +7.78/7.78, Cape Town +7.84/7.84) every party in the band errs
the same way, and that is itself worth seeing.

### F2b — mass on parties that never stood was reported nowhere

`rank_bands` iterates the parties that actually stood, so any share the model
assigns to a party that contested nothing falls outside all three bands. It is
**6.53pp across the nine city-years**, and it is exactly why the three signed
bands summed to −6.53pp rather than to zero — a discrepancy visible in the
printed totals for months and explained nowhere. It includes the generic
`ENTRANT` column in a city-year where nobody arrived, which is a real error the
model should pay for — at Johannesburg 2021 the phantom is 1.49pp and **1.44pp
of it is `ENTRANT`**: ActionSA is declared with a seed and therefore has a
baseline, so no party qualifies as having arrived from nothing, the relabel is a
no-op, and the generic entrant column stands as pure invented vote. That is the
correct treatment and it had no home in any statistic. Now a column
(`phantom`) and a total, with the
identity `Σ bands + phantom = 0` asserted by a test.

### F3 — the harness computed no calibration statistic at all

This is the finding F2 was hiding. `score.py` has produced coverage and a
randomised PIT per run since it was written; `compare_history` — the
nine-city-year scoreboard everything is judged on — pulled `crps.total` out of
it and dropped the rest. So the model's largest *systematic* property was
unmeasured by the thing that measures the model, and an outside reviewer had to
compute it by hand.

Pooled over the nine city-years, at 1500 draws:

| population | n | 50% | 80% | 90% | mean PIT | χ² vs flat (9 df, 5% crit 16.92) |
|---|---|---|---|---|---|---|
| claimed by the model (forecast-selected — neutral) | 53 | 58% | 89% | 96% | **0.587** | 23.4 |
| won a seat (outcome-selected — inflated) | 132 | **42%** | **73%** | **87%** | **0.760** | 148.9 |
| every scored column (neutral, diluted) | 331 | 77% | 89% | 95% | **0.559** | 22.0 |

**All three reject uniformity and all three skew the same way: the model
under-forecasts.** Independent confirmation from `src/sweep.py`, which flags the
truth falling outside the 90% band: **ten anomalies of "interval excludes the
truth (below) — won N, above the whole forecast", and zero of the opposite
kind.** Ten out of ten in one direction.

The interpretation matters and is easy to get backwards:

* `seat_holders` **conditions on the outcome.** Zero is the bottom of the seat
  support, so winning a seat selects over-performers and this population reads
  high even for a perfect forecaster — `score.py`'s own docstring records
  simulating 93% of perfectly-calibrated replicates printing "under-dispersed,
  widen it" under exactly this rule. It is quoted because it is the population a
  reader assumes, and it is labelled inflated wherever it is quoted.
* `all` does **not** condition on the outcome, but ~200 of its 331 columns are
  parties correctly at zero on both sides: a free interval hit at every level
  and a near-uniform PIT. It is diluted towards flat, and it *still* comes out
  at 0.559 with χ² past the critical value.
* `claimed` selects on the FORECAST alone, which is the one rule under which PIT
  uniformity survives selection. **It is the honest test and it agrees: mean
  0.587, χ² 23.4 against a critical 16.92.** This is stronger than the reviewer's
  version of the finding, which rested on the two populations that can be
  argued with.

**This is a LEVEL finding, not a DISPERSION finding, and the distinction decides
the remedy.** The 90% band covers 87% of seat-holding outcomes and the 80%
covers 73%: the bands are roughly the right WIDTH. On the columns the model
actually claims they are, if anything, too wide (58/89/96 against 50/80/90). What
is wrong is where they are CENTRED. Widening the intervals would improve
coverage on the outcome-selected population, cost sharpness everywhere, and fix
nothing — and it is precisely what `score.pit_histogram`'s shape verdict advises,
because a sloped histogram with mass in the last bins trips its U-shape test. The
report now prints the χ² next to the verdict and says in as many words that the
verdict is a shape heuristic and the χ² is the test.

### What was added, and what was deliberately not

`compare_history.calibration_columns` (per city-year, unpooled) and
`pooled_calibration` (the figure to quote), both built on `score.seat_matrix`,
`score.pit_values` and `score.coverage` — **nothing reimplemented**, so a single
run's report and the pooled report cannot drift apart. `score.py` was not
modified.

Per city-year figures are printed for provenance and **labelled as noise**,
because they are: Johannesburg 2021 reads 12/62/75 on n=8 claimed columns and
Cape Town reads 43/100/100 on n=7. Nothing at that size distinguishes a 50%
interval from an 80% one, and a reader quoting one of those rows is quoting
nothing. Only the pooled row means anything.

The PIT randomisation is seeded per city-year (`_pit_seed`, CRC32 of the
city-year name) rather than on `score.pit_values`'s single module default, which
would give every city-year's k-th column the same uniform — nine draws doing the
work of 130, and one unlucky value tilting the pooled histogram. It cannot change
a conclusion, only the noise on one.

`tests/test_calibration_report.py` is new and every test in it fails on the
pre-fix code (verified against a clean `git archive` of HEAD). It asserts on
computed numbers rather than on source text — including that a PERFECTLY
calibrated synthetic forecast reads as calibrated, which is the null `score.py`
records having failed twice before, and that the same data transformed WITHOUT
the randomisation fails it, so the randomisation is genuinely being tested rather
than a kind seed.

### What this does not do

It does not fix the bias. It makes it visible, in the standard report, next to
the number that decides whether an iteration ships. The next question — whether
the level shortfall at the top of the ballot and the arrival/small-party
shortfall in ranks 4-12 are one fault or two — is now measurable and was not.

---

## 1.35 `first_local_election` was dead code, and the evidence that it should stay dead (2026-08-17)

`pools.first_local_election` computed a level for "a party with a national
baseline facing its first local election" — national base × parent θ × ward
reach × leadership coherence — and MK in 2026 was the case it was written for.
It was **read by nothing**. The value reached `emit_pools`' returned dict under
`first_local_election` and stopped there: `run_model` loads only `pools`,
`fitted_on`, `splinter_home`, `seeds`, `seed_bands`, `seed_notes`,
`arrival_group` and `provenance` from the spec (`montecarlo.py:1648-1657`), and
the string `first_local_election` occurs nowhere in `src/` outside `pools.py`
itself. The output was discarded twice over: the loop also wrote
`seed_notes[party]`, and `pool_seed_notes` is looked up only inside
`if seeds:`, for parties in `seeds` — which these parties are excluded from by
construction, since a party with a positive baseline is not a `newcomer` and
therefore never becomes an arrival. The one consumer is a `verbose` print that
could not fire for them.

So the function is deleted, with its emitted key and with `_npe_citywide`,
which had no other caller. **No forecast moves**, and the reason it does not is
the finding: the levels these parties actually got came from the spine all
along.

### The measurement that says it should not be revived

46 parties on that path, nine city-years, 2000 draws. The comparison is between
the level `first_local_election` would have set and the level the spine
actually set, each against the party's realised share:

| | MAE | median ratio | within 2× | sd(log ratio) |
|---|---|---|---|---|
| `first_local_election` | 0.224pp | 0.59 | 62% | 1.19 |
| the spine | **0.176pp** | **0.78** | **76%** | **0.74** |

**The spine wins MAE in 8 of the 9 city-years.** Quote that, not the 36-of-46
party-level count: parties share city-years, so the paired sign test over
parties is not independent and its p = 0.00016 is optimistic. The clustered
version — a sign test over city-years — survives at **p ≈ 0.039**, which is the
honest number.

Two refutations of the obvious rescues, both measured:

* **A free in-sample rescale makes it worse.** Multiplying every
  `first_local_election` level by the constant that sets the geometric mean
  ratio to exactly 1.00 — a parameter fitted on the answer, so the most
  favourable treatment available — moves within-2× from 62% to **49%**. The
  errors are not a shared bias; they are spread.
* **Every blend weight is monotonically worse than the pure spine.** There is
  no interior optimum to find.

### The caveat, which cuts the same way

This population is tiny parties: median actual share **0.15%**, and only **4 of
46** cases exceed 1% actual. At MK's magnitude the record is n≈2 and *neither*
path is validated. That is an argument for deleting the one nobody can show is
better — it is not an argument for wiring it in. Nothing here supports moving
MK from 11.3% to 8.18%.

### The more alarming half: the credited mechanism never ran

`MACHINERY.md` credited this row with "**78% within a factor of two, 45 cases,
median ratio 0.85**". That figure **reproduces for the SPINE, not for the
function it credits.** The instrument was `src/arrivals.py`, which scores
`run.pr_share_draws` — whatever actually ran — and `first_local_election` never
reached a run. Confirmed by reproducing that entry's companion figure,
`arrivals: 7/32`, exactly.

The *finding* of that entry survives: something in the model does place these
parties within a factor of two three times in four. The mechanism the
documentation credits with it is fictional. This is the second instance in two
days of a documented lever that no run reads (§1.33's five dead levers were the
first), and it is the case `CLAUDE.md`'s rule about measured-versus-argued
constants was written for — the measurement existed only in a commit message
and a scratch file, so the register said "measured" about a number no register
could have produced.

---

## 1.36 We shipped the same fault twice in two days, in two different statistics (2026-08-17)

**No forecast moved.** Re-running the nine city-years at 1500 draws against the
committed `data/processed/history.json`: coherent seat error **312 → 312** and
identical in every city-year, median seat error 354 → 354, CRPS total 268.3 →
268.3 to the digit, beats uniform swing **7/9 → 7/9**, signed bands +32.50 /
−37.34 / −1.69 unchanged and absolute bands 71.12 / 55.76 unchanged. The single
exception is eThekwini's ranks-13+ *absolute* band, 14.47 → 14.37 across the
nine-city total. That is not this change: two runs of the SAME code with
identical arguments give 4.183 and 4.274 for that figure and `pr_mae` differing
in the sixth significant figure, with `crps` identical to sixteen digits.
eThekwini has a pre-existing float-reduction nondeterminism, noted in §1.34 for
the same city and the same statistic. Everything else is byte-identical.

### The defect, stated plainly

§1.34 fixed `rank_bands`, which had reported a **signed sum** of per-party error
inside each rank band. A signed sum cancels offsetting errors: Johannesburg 2021
read +1.32pp while being 26.50pp wrong. That fix was right, it was argued at
length, and its reasoning was written into a docstring, a test file, ITERATING
rule 7 and a JUDGEMENT-CALLS row.

**In the same commit we shipped a pooled PIT mean that does exactly the same
thing.** It averages over every claimed column at once. An independent reviewer
split that population by actual PR rank — using the ordering `rank_bands`
computes eleven lines above — and the pooled figure came apart:

| claimed columns, nine city-years | n | mean PIT | 95% CI (cluster bootstrap) | nominal 50% covers |
|---|---|---|---|---|
| ranks 1-3 | 27 | **0.431** | [0.380, 0.479] | 70% |
| ranks 4-12 | 26 | **0.750** | [0.674, 0.810] | 27% |
| pooled | 53 | 0.588 | — | 58% |

Re-derived here independently from the committed `history.json` and confirmed by
a fresh 1500-draw run; the CIs resample **city-years**, not columns, 20,000
replicates. The reviewer's figures were 0.431 [0.380, 0.480], 0.750 [0.672,
0.810] and 0.587 — the same to the third decimal.

**The pooled 0.588 is the average of a −0.069 and a +0.250.** Both CIs exclude
0.50, in opposite directions. The model **over**-forecasts the top three and
**under**-forecasts the middle — which is precisely what the signed vote bands
(+32.50pp at ranks 1-3, −37.34pp at 4-12) had been saying since §1.34. The two
instruments agreed completely. Only the aggregation was wrong.

**A signed average across bands with opposite errors is not a measure of bias,
for exactly the reason a signed sum within a band is not a measure of error.**
It is the same arithmetic, one level up, and we wrote the argument down on a
Monday and violated it on a Tuesday. There is no interesting story here: the
rank split was already computed, in the same file, in the function immediately
above the one that needed it.

### The width verdict is band-dependent too, and there are two of it

§1.34 concluded "the bands are roughly the right WIDTH; what is wrong is where
they are CENTRED", and ITERATING rule 8 turned that into "widening would be the
wrong fix". Split by rank that is right at the top and wrong in the middle.

There is a second wrinkle, and it changes the number by 19 points. Two coverage
statistics are available and they are not the same:

| nominal 50% | `score.coverage` (quantile interval) | randomised PIT in the central 50% |
|---|---|---|
| ranks 1-3 | 0.704 | 0.704 |
| ranks 4-12 | 0.462 | **0.269** |

`score.coverage` reads the empirical quantile interval, which on integer seats
must include whole endpoints and therefore over-covers — its own docstring says
so, "worth a few points at the 50% level". The randomised PIT carries no such
inflation. At ranks 1-3 the forecast distributions are tens of seats wide and
one endpoint is worth nothing, so the two agree to the third decimal. At ranks
4-12 the parties hold one to ten seats, an endpoint is a large slice of the
interval, and the raw coverage is inflated from 0.27 to 0.46 — from "far too
narrow" to "about right". **The reviewer quoted 0.27 and the harness printed
0.46; both are correct and they are different statistics.** Both are now
printed, side by side, and the PIT-corrected one is labelled as the one to read.

So the width verdict, per band: ranks 1-3 too WIDE (70% at a nominal 50%) and
over-forecast; ranks 4-12 too NARROW (27%) and under-forecast. No single change
to dispersion improves both, and the pooled statistic will report progress for
one that makes one band worse and the other better by the same amount.

### The `all` population was documented as neutral and is not

`compare_history` labelled `all` "every scored column (neutral, but diluted by
correct zeros)". `score.seat_matrix` admits a column when `truth[i] > 0 or
samples[:, i].max() > 0`. The second clause selects on the forecast, which is
neutral. **The first lets a party in because it WON**, which is outcome
selection — the very thing `seat_holders` is labelled inflated for.

It is not a technicality. Five of the 331 `all` columns carry PIT **exactly
1.0**: Johannesburg 2016 ALJAMAAH, Johannesburg 2021 PA, eThekwini 2021
MINORITIES_OF_SOUTH_AFRICA, Cape Town 2021 CAPE_MUSLIM_CONGRESS and
DEMOCRATIC_INDEPENDENT_PARTY. The model gave each of them zero seats in every
single draw; they are in the population only because they won one. `all` is a
**mixture** of an outcome-selected set and a neutral one, and the neutral part is
itself diluted by ~200 parties correctly at zero on both sides. Two errors
pushing opposite ways, so the population tests nothing and its 0.560 should not
be quoted as corroboration of anything. `claimed` is the honest test and it is
also the one that comes apart by rank.

**`score.py` was not changed.** The admission rule is right for CRPS, which is
what that function exists for. What was wrong was the label, and the label is
what a reader acts on.

### One statistic, three numbers, one commit

`rank_bands`' docstring quoted ranks 1-3 as +1.36 / 26.69 per city-year and
+32.67 / 72.06 in total; MODEL-LOG §1.34's table quoted +1.32 / 26.50 and
+32.42 / 71.65; the committed `history.json` gives +32.50 / 71.12. All three are
the same statistic at different draw counts, and a reader had no way to tell a
re-run from a regression. **Quote the draw count wherever the number is quoted,
or quote neither.** The docstring now says "committed `history.json`, 1500
draws" and lists all three values with that explanation attached, so the next
reader sees the spread rather than rediscovering it.

### What was added

`rank_band_of` — one definition of the bands, used by the vote table and the
calibration table alike, so "ranks 1-3" cannot come to mean two different sets
of parties. `calibration_columns` now takes `actual_pr`, labels every column
with its band, and stores per-column interval hits (from `score.coverage`, one
column at a time — nothing reimplemented) so that a pooled figure can be
recomputed over any subset without re-running nine city-years. An aggregate
cannot be disaggregated, which is why the split was impossible to make from the
committed artefact. `pooled_by_band` does the split, with a cluster bootstrap
over city-years at a fixed seed. The report prints the band table under the
pooled one and says which to read.

Columns with no actual PR rank — parties the model gave seats to that contested
nothing — get an `off-ballot` bucket rather than being swept into 13+. It is the
calibration counterpart of `rank_bands`' phantom mass; there are 18 of them in
`all` and they cover 100% at every level, being forecast and actual zero alike.

### The tests, and what they would have caught

`tests/test_calibration_report.py` gains five. The load-bearing one builds nine
synthetic city-years biased UP at ranks 1-3 and DOWN at ranks 4-12 by equal and
opposite amounts. **On the pre-fix code that fixture pools to a mean PIT of
0.485** — indistinguishable from a perfectly centred forecast — with the report's
verdict reading *"U-shaped: the truth lands outside the distribution too often —
under-dispersed, widen it"*, which is the wrong remedy for both bands at once.
Verified against a clean `git archive` of HEAD: with the new keyword argument
shimmed away so the substantive assertion is the one that fires, it fails with
"pooled_calibration reports no split by rank band". The others assert that the
bands partition the population exactly (numerators and denominators both), that
the report prints the per-band numbers rather than merely computing them, that a
zero-forecast party which wins seats lands in `all` and not in `claimed` and
carries PIT exactly 1.0, and that the discreteness gap between the two coverage
measures appears on a two-seat band and not on a wide one, with the corrected
statistic passing the null.

### What this does not do

It still does not fix the bias — and it now says the bias is two biases. §1.34
closed by asking "whether the level shortfall at the top of the ballot and the
arrival/small-party shortfall in ranks 4-12 are one fault or two". The
calibration answers it the same way the vote bands did: **two**, with opposite
signs and opposite width errors. Any iteration that proposes a single dispersion
or level change should expect the per-band table to move in opposite directions
and should be judged on both rows, not on their average.

The lesson worth keeping is not "check the aggregation". It is that we had
already learned it, written it down, tested it, and then applied it to one
statistic and not to the one we added in the same breath. A rule written in a
docstring is not applied to code that has not been written yet.

---

## 1.37 Seven more levers that do nothing, and an audit that was a comment (2026-08-17)

Acting on a second independent review of the same day's work. Everything here is
a defect in an *instrument* or in the *record*; none of it moves a forecast, and
that is the pattern rather than a coincidence.

### The improvement claimed in §1.33 was draw noise, and is retracted there

Measured at 400 draws, retracted at 1500. See the correction inside §1.33. The
lesson is `ITERATING.md` rule 6 applied one level up: **the first thing a
measurement must establish is that it measured something.**

### CLASS 12 covered 13 of 27 tunables, and a deletion silently removed coverage

*(The denominator moved to 26 in this same commit, when `ward_pr_ratio_overrides` was deleted. The figures below are as measured before that deletion; a count that goes stale inside the commit that staled it is the reason the enumeration test compares sets rather than quoting a number.)*

`PERTURB` was a hand-maintained allowlist. Hand-maintained allowlists rot, and
this one rotted within a day of being written:

* **13 of 27 `DEFAULTS` keys were perturbed.** Among the 14 that were not:
  `ward_pr_ratio_overrides` — which this file's own docstring names as one of
  the four instances that motivated it.
* **Three `PERTURB` entries were silently skipped** by the `key not in DEFAULTS`
  guard. Two were `polling_lean` and `polling_span`, deleted hours earlier —
  **so a deletion removed its own test coverage and nothing failed.** The third
  was `turnout_correlation`, a module constant that had therefore never been
  exercised at all despite appearing in the list.

`test_every_defaults_key_is_swept_or_excused` now enumerates in both directions,
the way `test_every_tunable_constant_is_in_the_judgement_register` already did.
Non-judgement keys (`draws`, `seed`, `pools`, `poll_id`) are named in
`OPERATIONAL` with reasons rather than omitted.

### Raising coverage to 23 of 27 found seven more inert levers

| lever | why it does not move |
|---|---|
| `theta_mode` | read only in the `blended_centres` branch for parties the spine cannot reach. Inert at 2021, **live at 2026**, where such parties exist. |
| `f_other` | same branch, inert everywhere |
| `individual_theta` | dead as a *default*, live as an *internal channel* — `montecarlo.py:1842` writes into the same key for seeded arrivals. One key, two jobs. |
| `poll_k` | the legacy `poll_id` poll path. Verified directly: 1.0 vs 40.0 at 2026 moves DA/ANC/ASA/MK/EFF by **exactly 0.0000pp**, while `metro_poll` is consumed. |
| `bye_local_cap`, `bye_tau_months` | parameters of the ward-local by-election term, gated shut at 0.0 |
| `entrant_geography` | empty by default |

Each is now in `EXPECTED_INERT` with a checkable reason. **`theta_mode`'s asymmetry — RETRACTED the same day.** This section originally
read: *"the constant that gave ActionSA 1.50 fitted on the 2021 target is inert
at every scoreable target and still live in the forecast. That is the best
possible arrangement and it happened by accident."* It was measured while another
worker was re-emitting `pools_*.json`, so the baseline moved under the sweep. On
a settled tree `theta_mode` is consumed at **zero of ten** runnable targets —
2026 included — which `run.constants_read` and the in-sample banner both confirm.

There is no asymmetry and there was no happy accident. `theta_mode`, `f_other`
and `individual_theta` are simply **dead**, on the identical evidence that got
`ward_pr_ratio_overrides` and `first_local_election` deleted the same day. One
standard of evidence, three dispositions — see §1.41.

### `ward_pr_ratio_overrides` deleted — consumed at no target

`run.constants_read` reports it read at none of 2016, 2021, 2026, because
`levels.ward_pr_ratios` returns a fallback at all of them and the override is
gated on `not fallback` — which the code's own comment already said. Removed
from `DEFAULTS`, `apply_city`, two city tomls, `backtest.FITTED_ON` and the
register. The `FITTED_ON` removal matters on its own: a contamination entry for
a constant that cannot be read reports a risk that does not exist, which is the
same fault in the other direction as the phantom keys §1.29 removed from that
list. The interactive also surfaced it as a **slider**, so a user could move a
control that changed nothing.

### CLASS 12 had three false-negative channels of its own

It compared list shares only, so it called `ward_noise_sd` and
`pa_contestation_uplift` dead — both are live on the ward side. Adding the ward
ballot fixed those and left `overhang_rule` reading dead, because that lever
touches **only seat allocation**, after every vote is drawn. Three blind spots
in a test written to find blind spots, each found by the next thing it wrongly
accused. It now compares the list ballot, the ward ballot, ward wins and seats.

Also: perturbations are serialised with `json.dumps`, not an f-string. Python's
`repr` of a dict uses single quotes, `json.loads` rejects it, `parse_set` falls
back to storing the raw string, and the model gets a `str` where it expects a
mapping — surfacing as an `AttributeError` deep inside `run_model` rather than
as a clear failure.

### The stat audit was a comment, not an audit

`orphaned_scenario_claims` correctly detected all ten front-page claims pinned to
`turnout_tilt_da` — a lever `run_model` no longer has — and **printed**. Nothing
stopped the build. Those claims survived weeks and two independent reviews that
each named them, because detection without refusal is a comment.

An unresolved token was already fatal, on the grounds that it would publish a
blank. **An orphan is worse: it publishes a NUMBER that reads as current, cannot
be re-derived, and cannot drift** — so every audit downstream reports it clean.
Now fatal, with `--allow-orphans` to stage the fix. `build_site.py` currently
refuses to publish, which is correct and is the point.

### Two judgements inside the capacity cap, one of them unregistered

`POOL_CAPACITY_MARGIN = 0.98` decides how much mass moves and was argued at
length in §1.33. **Where it goes was not argued at all.** Measured on the live
2026 forecast, 600 draws: a mean **0.445%** of the city moves sideways (median
0.000%, p90 1.462%, max **6.933%**), firing in 39.2% of draws. Because the rule
is proportional to what each party already holds, **the DA collects roughly a
third and the ANC a fifth** — so the guard transfers the PA's truncated upside
to the band already measured as over-forecast, and correlates the DA's upside
with the size of the PA's level shock. Registered at 🔴, counted on
`capped_targets.moved`, and two unmeasured alternatives named (proportional to
headroom; proportional to pool overlap with the offender).

`capped_targets` also has one branch that cannot keep both its invariants —
when the capacities do not cover the city it returns every element *above* its
cap. It cannot fire in this model. It is counted anyway, because an uncounted
branch that silently does the opposite of its docstring is the exact defect the
function was written to remove.

### Six wrong rows in `MACHINERY.md`

`pools.fit_national` (does not exist), "235 observations at 2026" (the run prints
**257**), ward contestation "not modelled" (it is measured, and §3 of the same
document said so), "44 of its 45 cases" (**42**), `ward_pr_ratio_overrides` listed
as a judgement that saw the targets (deleted), and `polling_lean` listed as
*switched off* when it had been **deleted in the same commit that wrote the line**.

Four of the six were named in the previous review and survived a pass that was
supposed to fix them. The document is the methodology the site links to.

---

## 1.38 The method of bounds was computed on every fit and enforced on none (2026-08-17)

`pools.bounds` is the Duncan-Davis method of bounds: no model and no estimate,
just the interval a party's rate in a pool can arithmetically lie in given the
ward table. It has been computed on every fit since the joint fit was written,
stored on every `PartyFit` — and read at exactly one place, `identified()`,
where it sets a display flag. **Nothing projected onto it.** A quantity that is
computed, stored, displayed and never enforced is the same class of defect as
§1.33's dead levers and §1.35's dead function, reached from the opposite
direction: not a lever nothing reads, but a *constraint* nothing obeys.

### What it cost, across ten city-years

Refitting every (city, fitting-year) pair a production emit uses, the committed
code emits **11 rates the ward arithmetic forbids**:

| city-year | party | pool | fitted | Duncan-Davis interval | outside by |
|---|---|---|---|---|---|
| joburg 2021 | PA | Coloured | 0.4121 | [0.1384, 0.4097] | +0.0024 |
| joburg 2021 | PA | Black African | 0.0000 | [0.0002, 0.0333] | −0.0002 |
| joburg 2021 | Al Jama-ah | Indian/Asian | 0.1899 | [0.0211, 0.1888] | +0.0011 |
| **nelsonmandelabay 2016** | **DA** | **Black African** | **0.0059** | **[0.0312, 0.2270]** | **−0.0253** |
| buffalocity 2016 | DA | White | 0.9623 | [0.4247, 0.9263] | +0.0360 |
| buffalocity 2016 | DA | Black African | 0.0341 | [0.0442, 0.1973] | −0.0101 |
| ethekwini 2016 | DA | Black African | 0.0077 | [0.0112, 0.2182] | −0.0035 |
| capetown 2016 | DA | Black African | 0.0291 | [0.0323, 0.3279] | −0.0032 |
| ethekwini 2016 | Minority Front | Indian/Asian | 0.0237 | [0.0003, 0.0236] | +0.0000 |
| ethekwini 2016 | Democratic Liberal Congress | Indian/Asian | 0.0224 | [0.0105, 0.0222] | +0.0002 |
| ethekwini 2016 | Minorities of SA | Indian/Asian | 0.0141 | [0.0000, 0.0141] | +0.0000 |

**This was never only the PA.** The DA is below its own arithmetic floor in the
Black African pool in *four* cities, worst at Nelson Mandela Bay 2016, where
0.0059 is 5.3× below a floor of 0.0312 — the model was fitting a DA that could
not have won the Black African votes it demonstrably did win, and putting the
difference in the White pool instead. Its emitted composition there goes Black
African 0.60% → 3.17%, White 55.71% → 54.79%. At Buffalo City 2016, Black
African 11.28% → 14.62%, White 66.71% → 63.92%.

### The mechanism of the failure, and why IPF could not repair it

At Johannesburg 2021 `fit_joint` returns a corner for the PA — Black African
0.0000, Coloured **0.5149**, Indian/Asian 0.0000, White 0.0000 — 10.5pp above
that party's own Duncan-Davis ceiling of 0.4097. It is not the optimiser: plain
NNLS lands on 0.5421 with the same three zeros. It is the ecological inference
problem, where a rate of 0.003 on a pool casting 523,499 votes manufactures more
squared error than it buys.

`balance_margins` then walked it to 0.4121 — still outside — and the emitted
vector was Coloured **1.0000**. At the 2026 target that party's level is ~102%
of every vote the Coloured pool casts, the per-draw balance cannot solve it, and
until yesterday's capacity cap that was swallowed by a bare `except` in 42.7% of
the live forecast's draws.

**IPF cannot repair a corner, and this is the general statement of why.** IPF is
multiplicative, so a cell at exactly 0.0 is a fixed point: no number of
iterations moves it. The only cell it could scale for the PA was the one already
at the ceiling. So `balance_margins` can never widen a single-pool vector, in
this or any other city — which is the root reason the capacity cap had to exist.

### The fix, and which half of it does the work

`balance_within_bounds` replaces `balance_margins` inside `fit_city`. Each
half-step scales a row (or column) by the single factor that lands its
**clipped** sum on the known total — a Bregman projection onto a convex set,
exactly as the unbounded half-step is, so all three known things hold at once
rather than in sequence. **A projection followed by a rescale is not a
projection**, and clipping-then-IPF is precisely how 0.5149 became 0.4121 rather
than 0.4097. Every cell the fit zeroed is seeded with the pool's share of the
votes the clipped fit could not place, because a multiplicative iteration cannot
reach a zero and a corner is full of them.

Both halves are necessary and **neither works alone**, which was worth measuring
rather than asserting:

* **Bounds without the seeding does not converge at all.** With the PA capped at
  the Coloured pool's 27,183-vote ceiling and zeroed elsewhere, its column can
  only ever account for 27,183 of its 27,346 votes; the iteration runs to its
  cap and raises.
* **Seeding without the bounds changes nothing.** Running the identical
  iteration with the box widened to [0, 1]: 3 violations at Johannesburg 2021,
  PA Coloured **1.0000** — the same corner, unmoved. The reason is exact: with
  no ceiling the Coloured cell absorbs the party's whole total by scaling, so no
  votes are ever *unplaced* and no cell is ever seeded. **The bound is what
  creates unplaced votes; the seed is only what lets a multiplicative iteration
  place them.**

After: **0 violations at all ten city-years**, both margins still exact (pool
rates sum to 1 to 1e-9, worst implied citywide share off by 5.6e-17). The PA at
Johannesburg 2021 emits Coloured **0.9942**, elsewhere 0.0058.

### The guard is now inert, which is the point

`montecarlo --city joburg --target 2026 --draws 600`, before and after:

| | fell back | held at pool capacity |
|---|---|---|
| committed | 0.0% (the cap works) | **PA in 39.2% of draws, worst ask 204% of capacity** |
| after | 0.0% | **nothing held, in any of 600 draws** |

Yesterday's water-filling capacity cap took the *fallback* rate from 42.7% to
0.0% and its own write-up said it was a guard rather than a cure. It is now a
guard with nothing to guard against on this target: no party asks for more of a
pool than the pool has. The PA is the party that changes, and it changes in the
direction the cap was suppressing — its 2026 mean goes 5.03% → 5.76% and its p95
7.24% → 11.79%, because it was previously pinned at a ceiling it should never
have been standing on. **That is a real move in the live forecast**, made by
removing a constraint that existed only to contain a fitting artefact.

### What the fix does NOT do, stated plainly

The projection removes only the corners the arithmetic can *refute*. The PA at
Cape Town 2016 is still emitted at Coloured 1.0000 after the fix, because
nothing in that city's ward table forbids it.

And it does not reach the ward geography. Binning Johannesburg's 135 wards by
Coloured share, 71.9% of the PA's vote arises in wards over 30% Coloured, 18.2%
in 10–30% wards and **9.9% in wards under 10%**; in the 89 wards under 2%
Coloured it polled 1,173 votes against 392,961 Black African votes cast, an
implied rate of 0.00299 worth ~1,563 votes, about **5.7% of its citywide total**.
The projection gets to 0.58%, not 5.7%.

**That gap is not a bug in the projection — it is the difference between a bound
and an estimate.** Duncan-Davis cannot exclude that all 1,173 of those votes came
from those same wards' 6,674 Coloured voters, which is exactly why the floor is
0.00016 and not 0.00299. Arithmetic forces only 163 of the PA's 27,346 votes out
of the Coloured pool. Anything more requires believing the party is not at its
ceiling, and that is a model, not a bound.

### The rejected alternative, with its number

**Redistributing the truncated excess** (variant B) rather than truncating it:
clip to the ceiling, then spread the removed mass over the pools with remaining
headroom before balancing. It moves the PA to Coloured 0.816 / Black African
0.101 / White 0.050 / Indian 0.033, and Al Jama-ah from Indian 0.994 to 0.642.

It is worse, on the quantity the fit exists to minimise. Weighted SSE against
the observed ward table at Johannesburg 2021 (lower is better; the null that
gives every pool the city's own shares is 1.238e-01):

| | ward SSE | vs committed |
|---|---|---|
| raw `fit_joint` (violates bounds) | 1.6723e-02 | −3.3% |
| committed `balance_margins` | 1.7289e-02 | — |
| **projection (adopted)** | **1.7346e-02** | **+0.33%** |
| redistribution (rejected) | 1.8434e-02 | +6.6% |

Variant B pays **twenty times** as much ward fit as the projection does. Its
composition overshoots the ward geography in the other direction — 18.4%
non-Coloured against a geographic estimate of ~6%, where the projection
undershoots at 0.58%; on the Black African pool alone, where the geography is
sharpest, B's 10.1% is marginally closer than A's 0.36% to the implied 5.7%, and
that ambiguity is why the ward fit rather than the PA alone decides it.
Vote-weighted mean R² over all parties: committed 0.6865, projection 0.6890,
redistribution 0.6835.

### The backtest does not discriminate, and is reported anyway

Nine city-years at 1500 draws, from a clean `git archive` of HEAD with every
pool artefact re-emitted for each variant:

| | coherent seat error | beats uniform swing | CRPS | mean list MAE | bands 1-3 / 4-12 / 13+ |
|---|---|---|---|---|---|
| committed | 312 | 7/9 | 268.3 | 2.510pp | +32.50 / −37.34 / −1.69 |
| projection (adopted) | **306** | 6/9 | 266.1 | **2.465pp** | +32.52 / −37.18 / −1.70 |
| redistribution | **306** | 8/9 | **265.4** | 2.501pp | +32.47 / −36.69 / −1.96 |

Draw noise on the seat error is ±2 to ±4, so **none of this is a result**. Both
variants land on the same 306; the uniform-swing counts differ only through ties
(Mangaung 10 → 8 → 6 against a uniform swing of 8; eThekwini 34 → 36 → 34
against 36). **Variant B is marginally ahead on CRPS and on the uniform-swing
count, and it is still rejected**, because those differences are inside the
noise band and the ward fit — the only data either variant is estimated from —
is not: B costs 6.6% of it against A's 0.33%. It also moves Al Jama-ah from
99.4% Indian/Asian to 64.2% on no evidence at all, its bounds requiring nothing
of the kind.

This was a correctness fix and was not expected to score. It did not.

### The one judgement in it, and its measured size

How the unplaced votes are spread across a party's zeroed cells is a choice. It
is made the same way `balance_margins` already made it for a party with no
spatial signal at all — proportional to pool size, the maximum-entropy answer
for a cell nothing is known about — and three candidate rules were compared
(pool size, remaining headroom, uniform).

For any party the ward data can see it is **not a lever**: the PA's non-Coloured
share is 0.582% / 0.582% / 0.692% under the three rules, because *how much* must
leave the saturated pool is fixed by the bounds and the margins, and only the
split of that fixed amount is chosen. For micro-parties whose entire column is
blank it is the whole answer — up to 0.37 of composition for DISRUPT_PARTY — but
those are exactly the parties `identified()` already reports as unmeasured, and
the choice is the one the surrounding code already made.

---

## 1.39 Rule 8 was wrong twice in two days, in opposite directions, from the same mistake (2026-08-17)

**No forecast moved.** Nothing in this entry touches what is drawn; it changes
what is reported and what the record says about it. `src/pools.py`,
`src/montecarlo.py`, `src/score.py` and `src/backtest.py` are untouched.

### The short version

`ITERATING.md` rule 8 has now given the next iteration a *wrong instruction on
dispersion twice inside forty-eight hours*, and the two instructions were
opposites:

| when | rule 8 said | evidence it rested on |
|---|---|---|
| §1.34 | "roughly the right WIDTH; do not widen" | pooled 90% coverage, 87% vs 90% |
| §1.36 | ranks 4-12 "too NARROW — widen them" | the 50% PIT column alone, 27% vs 50% |
| now | **both bands are ~1.35× too WIDE**; they differ only in LEVEL | probit-SD 0.740 / 0.734, and all three coverage levels read together |

Each time the fault was identical in form: **a width verdict taken from a
statistic that also moves with the level**, read at one nominal level, with no
interval on it. The second reading was worse than the first, because it was
confident and it was published as an instruction.

### The evidence that settles it

The committed artefact, `claimed` columns, ranks 4-12:

    50% covers 32%     80% covers 89%     90% covers 96%
    (nominal 50)       (nominal 80)       (nominal 90)

**A forecast whose intervals are too narrow under-covers at EVERY level. That is
what narrow means.** This one over-covers at 80 and at 90. The reading that
sent the next iteration to widen the band used the 50% cell and ignored the two
cells that contradict it.

What produces a low 50% with a high 80 and 90 is a forecast that is *shifted* —
it has vacated the middle of its own interval — sitting inside intervals that
are *too wide*.

That is not an argument, it is a fixture, and it is in the suite. Nine small
parties on a mean of 4 seats (the real band's scale), forecast width and truth
shift controlled independently, run through this repository's own
`calibration_columns`. Reproduce with
`tests/test_calibration_report.py::_shift_scale_results(4242, 12, width_mult=W,
shift=S)`:

| ranks 4-12 fixture | mean PIT | 50% | 80% | 90% | PIT var | probit-SD | sd(z) |
|---|---|---|---|---|---|---|---|
| correct width, no shift | 0.552 | 0.454 | 0.824 | 0.880 | 0.0829 | 1.021 | 1.000 |
| correct width, **+2 shift** | 0.794 | 0.269 | **0.556** | **0.759** | 0.0450 | 0.917 | 1.000 |
| correct width, +3 shift | 0.876 | 0.167 | 0.361 | 0.509 | 0.0240 | 0.953 | 1.000 |
| **1.6× too wide, +2 shift** | 0.740 | 0.435 | **0.861** | **0.935** | 0.0270 | 0.571 | 0.650 |
| **the model, ranks 4-12** | **0.757** | **0.321** | **0.893** | **0.964** | 0.0388 | **0.734** | — |

A shift takes coverage away at every level. **Only excess width puts it back at
80 and 90**, and at 80 and 90 the model's row sits with the too-wide arm, not
with the correct-width one. Read the `sd(z)` column too: exactly 1.000 at every
shift when the width is right, and 0.650 when the forecast is widened by 1.6×.
That is what a width statistic looks like.

### The statistic that answers it, and three that do not

Nothing above is a *measurement* of width — it is an argument from the shape of
three numbers. So the report now carries a statistic with the level divided out.

**`pit_dispersion` = `sd(Φ⁻¹(u))`.** Under a location shift of a roughly normal
forecast, `Φ⁻¹(u)` translates: the shift lands in the mean and leaves the spread
alone. 1.00 is right; below 1.00 too wide. On the committed artefact:

| claimed columns | n | mean PIT | probit-mean (level) | **probit-SD (width)** |
|---|---|---|---|---|
| ranks 1-3 | 27 | 0.434 | −0.143 | **0.740** |
| ranks 4-12 | 28 | 0.757 | +0.789 | **0.734** |

**The two bands are dispersed almost identically** — both about 1/0.74 ≈ 1.35×
wider than the errors they cover — and differ only in level. That is the correct
reading, and it is the opposite of what rule 8 said yesterday for one band and
the same as what it said for the other, which is why reading one band at a time
kept producing half-right answers.

`dispersion_ratio` is the exact version: `z = (truth − forecast mean) / forecast
sd` per column, centred, whose sd is invariant to a shift by construction. It
needs per-column mean and sd, which `calibration_columns` now stores as `z`, so
it reads `—` on the artefact written before this change. **It needs a canonical
re-run to be quoted; the probit-SD above does not.**

**Three statistics were used or proposed for this and are not fit for it. Each
is now printed with its own refutation, or labelled unreliable in place.**

1. **Coverage at one nominal level.** Confounded with the level. The mistake,
   twice.
2. **PIT variance against 1/12** — proposed in this very review as
   "shift-invariant, therefore a clean dispersion statistic". **It is not
   shift-invariant.** A PIT is bounded on [0, 1], so a shift piles mass against
   an endpoint and the variance falls whatever the width is. On the
   correct-width fixture above it reads **0.0829, 0.0450, 0.0240** at shifts of
   0, +2 and +3 seats against a nominal 0.0833 — a pure level error reading as a
   3.5× under-dispersion. It is printed in the width table specifically so that
   the next reader meets it already refuted. Corollary: the artefact's 0.0388 at
   ranks 4-12 is **not** evidence of narrowness, and neither is the emptiness of
   its tails (0 columns below PIT 0.05, 1 above 0.95) — a shifted forecast
   evacuates one tail and a wide one evacuates both.
3. **Recentring the PIT about its own mean and re-reading coverage** (the
   "shift-corrected central-50" figure of 0.93). Same boundary problem: on the
   correct-width fixture it reads 0.55, 0.85, 0.94 at shifts of 0, +2, +3. It
   does not remove the shift; it reports it.
4. **`score.pit_histogram`'s shape verdict.** It tests the two END bins, so a
   *monotone increasing* histogram scores as U-shaped. On ranks 4-12 it reads
   `[1, 1, 1, 11, 14]` — 25 of 28 columns in the top two bins, nothing at the
   bottom — and prints *"U-shaped … under-dispersed, widen it"*, while calling
   the pooled population *"hump-shaped — over-dispersed, hedging"*. **The report
   contradicted itself and both halves were quoted.** `score.py` is deliberately
   **not** changed — the heuristic is serviceable for what it is for, and what
   was wrong was quoting it about width. The report now says so where it prints
   it.

### The corollary that was also wrong

Rule 8 concluded that "no single change can fix both bands", because one wanted
widening and the other narrowing. **Both want narrowing.** They differ in level,
and since shares sum to one that difference is a single **zero-sum transfer**:
+32.52pp at ranks 1-3 and +6.36pp of phantom mass against −37.18pp at 4-12 and
−1.70pp at 13+, summing to zero by construction. So "narrow the seat
distribution and move mass from the top three to the middle" is one coherent
proposal rather than two contradictory ones. It still has to beat the baselines
on history before it ships; nothing here says it will.

### And the coverage rows were never significant

`_cluster_bootstrap_ci` was applied to `mean_pit` and to nothing else, so every
coverage figure in the report was a bare point estimate — and the entire width
argument turned on one. Coverage rows now print with cluster-bootstrap intervals
(ranks 4-12 at 50%: **32% [19–50]**, which includes nominal). Against nominal,
on a binomial test that ignores clustering and therefore flatters every cell:

| | ranks 1-3 | ranks 4-12 |
|---|---|---|
| 50% (PIT) | 19/27, p = 0.026 | 9/28, p = 0.044 |
| 80% (PIT) | 25/27, p = 0.072 | 25/28, p = 0.16 |
| 90% (PIT) | 26/27, p = 0.23 | 27/28, p = 0.22 |
| probit-SD vs 1.0 | 0.740, p = 0.030 | 0.734, p = 0.025 |
| **probit-SD, both bands pooled** | | **p = 0.003** |

**Said plainly: the 80% and 90% over-coverage this entry argues from is not
individually significant.** What it does is rule out the narrow reading — a
narrow forecast cannot over-cover at any level — while the weight of the
evidence sits in the level-free dispersion statistic, which uses all 55 columns
at once. Two caveats pushing opposite ways: columns cluster within city-year, so
every p above is optimistic; and the probit-SD is attenuated by the shift, so
1.35× understates the excess width.

And the discreteness correction is thinner than anything it was used to support.
What turned "about right" (43% raw) into "far too narrow" (27–32%
PIT-corrected), and carried §1.36's entire width argument, is **three discordant
columns out of 28** — a one-sided sign test at p = 0.125; at ranks 1-3 it is two
columns, p = 0.25. The correction is real and points the right way. It is not a
result a conclusion can be built on alone, and one was.

### Root cause: there was no committed artefact to check anything against

`.gitignore:5` is `data/**`. **`data/processed/history.json` had never been
committed**, and is overwritten by every run. Yet `compare_history.rank_bands`
stated *"EVERY FIGURE ABOVE IS THE COMMITTED `data/processed/history.json` AT
1500 DRAWS"*, and `pooled_by_band`, `calibration_columns`, §1.33 and §1.36 all
cite it as an authority. Nothing could diff it; no test could hold a document
against it.

The consequence is not hypothetical. Artefact on disk against the record written
minutes later:

| | the record said | the artefact says |
|---|---|---|
| ranks 1-3 | n=27, PIT 0.431, cov 70% | n=27, **0.434**, **78%** (quantile) / 70% (PIT) |
| ranks 4-12 | n=**26**, PIT 0.750, cov **46%** | n=**28**, **0.757**, **43%** |
| ranks 1-3 absolute | 71.12pp | **69.59pp** |
| coherent seat error | 312 (§1.36) | **306** |
| CRPS total | 268.3 (§1.36) | **266.1** |

Three reviews have now rediscovered this class of rot and each time it was
written up as carelessness. It is not carelessness; it is a missing guard.

**What was done.** `data/processed/history.json` and `history.md` are
un-ignored and tracked, with the reasoning in `.gitignore` itself.
`ITERATING.md` rule 8 carries two tables behind a `CHECKED-AGAINST-ARTEFACT`
marker, and
`tests/test_calibration_report.py::test_the_documented_figures_match_the_committed_artefact`
parses them and fails the build when they and `history.json` disagree, printing
the corrected row in the failure message. A second test asserts the `.gitignore`
negation exists **and sits after the `data/**` line**, because before it the
negation does nothing and the failure is silent.

**What that guard does not cover, stated so nobody assumes otherwise:** prose
anywhere; `MODEL-LOG.md`, which is append-only and whose figures are correct *as
of* their entry — rewriting them would destroy the record; the docstrings in
`src/`; and any figure not in the marked tables. A test that parsed every
document for every number would be unmaintainable and switched off within a
week. `rank_bands`' docstring no longer types a nine-city-year total at all; it
points at the checked table.

### The lesson, which is not "check the aggregation"

§1.36 closed by saying the lesson was not "check the aggregation" but that we
had learned that rule, written it down, and then failed to apply it to code
written in the same breath. This entry says something narrower and more
uncomfortable: **the same team, in the same file, on consecutive days, answered
one question — is this forecast too wide? — three times, and got two different
wrong answers before getting a right one.** Every wrong answer was argued from
real numbers computed by this repository's own code. What was missing each time
was not diligence but a statistic capable of separating the two things being
confused, and an interval saying whether the difference was there at all.

The reviewer who found this fault also proposed PIT variance as the fix, and
that proposal is wrong in the same family as the fault. Three of the numbers
offered as corroboration — the variance, the empty tails, the shift-corrected
central-50 — are all confounded by the shift they were meant to control for.
**Being right about the diagnosis is not the same as being right about the
instrument**, and the instrument is what the next iteration will use.

---

## 1.40 Half of `balance_within_bounds` was never about the bounds, and a wrong-city file was published as a delimitation problem (2026-08-17)

Two faults found by an independent review of §1.38 and of the multi-city
blocker. They are unrelated except in kind: **in both, a mechanism was given a
causal story it does not have, and the story was written into the record and
acted on.**

---

### Part A — the seeding fires on a condition the bounds have no part in

§1.38 stated, as a measured conclusion: *"The bound is what creates unplaced
votes; the seed is only what lets a multiplicative iteration place them."*
`JUDGEMENT-CALLS.md` recorded the trigger as *"when the Duncan-Davis ceiling
stops a cell absorbing a party's whole total"*. **Neither is what the code
does.** Read the line:

```python
unplaced = np.maximum(target_cols - np.minimum(counts, hi_c).sum(axis=0), 0.0)
```

`counts` is the **raw NNLS fit**. Nothing in a least-squares problem ties a
column sum to a party's vote total, so the raw fit does not reproduce party
totals and `unplaced` is positive whether or not any bound exists. Measured at
Ekurhuleni 2016 **with the box removed entirely** (`lo=0`, `hi=1`, so the clip
is provably inert — zero cells exceed `hi_c`):

| | with lo=0, hi=1 | with the real box |
|---|---|---|
| parties seeded | **15 of 25** | 21 of 25 |
| votes unplaced | **3,716 (0.41% of the city)** | 3,716 |
| cells clipped by a ceiling | **0** | 8 |

So there are **two independent triggers**, and the record conflated them:

* **seeding** fires when the raw NNLS column falls short of the party's known
  total — a property of least squares, present at every fit;
* **the box** binds when a cell would leave its Duncan-Davis interval — present
  at five of the ten fits.

A ceiling that clips a cell *enlarges* the shortfall it is compared against. It
does not create it. §1.38's "seeding without the bounds changes nothing"
experiment was real, but it measured the *outcome* at Johannesburg 2021, not the
trigger, and the causal sentence drawn from it was wrong.

#### What that cost: the bounded path ran on fits with nothing to correct

Ward SSE, weighted by votes, against `balance_margins` at each of the ten
production fits. §1.38 quoted Johannesburg's **+0.33%** as the price of the fix.
It is **the fourth smallest of ten**:

| fit | violations | ward SSE cost | cost with the box removed |
|---|---|---|---|
| nelsonmandelabay 2016 | 1 | **+3.71%** | +0.00% |
| buffalocity 2016 | 2 | **+2.02%** | +0.02% |
| **ekurhuleni 2016** | **0** | **+0.61%** | **+0.61% — all of it seeding** |
| joburg 2021 | 3 | +0.33% | +0.18% |
| ethekwini 2016 | 4 | +0.23% | +0.10% |
| capetown 2016 | 1 | +0.15% | +0.13% |
| joburg 2011 | 0 | +0.01% | +0.01% |
| mangaung 2016 | 0 | +0.01% | +0.01% |
| tshwane 2016 | 0 | +0.00% | +0.00% |
| joburg 2016 | 0 | +0.00% | −0.00% |

**Ekurhuleni 2016 had zero violations and paid 0.61% anyway**, every point of it
from seeding. Worse, `balance_margins`' answer there is not merely feasible — it
is a **fixed point of the bounded iteration** (one full sweep moves it by
2.8e-12) *and* a strictly better ward fit. The iteration only left it because
the seeding moved the starting point before the first sweep. The cost was real:
the DA's Indian/Asian rate went 1.00 → 0.90, and Al Jama-ah went from 82.9%
Black African / 17.1% Coloured to a four-pool vector with 32.1% White — a large
composition change at a city where the ward arithmetic refuted nothing.

#### The fix

Balance the margins first; if every rate already lies inside its Duncan-Davis
interval, **that is the answer and it is returned untouched**. Only a fit the
arithmetic can actually refute pays for the projection. Enforcing a constraint
is not the same as replacing a solver.

| | before | after |
|---|---|---|
| Duncan-Davis violations, all ten fits | 0 | **0** |
| fits passing through untouched | 0 | **5 of 10** — joburg 2011, joburg 2016, tshwane 2016, ekurhuleni 2016, mangaung 2016 |
| worst pool-margin error (rates sum to 1) | 4.33e-12 | **4.33e-12** |
| worst implied citywide share error | 2.22e-16 | **2.22e-16** |
| Ekurhuleni ward SSE cost | +0.61% | **+0.00%** |

Both margins are held at least as tightly as before. That took two adjustments
**at the call site**, because `montecarlo` runs `balance_margins` once per draw
and its output must not move: its stop is tightened from 1e-12 to 1e-15 (a
relative-to-grand-total criterion, so at 1e-12 a small party's share can still
be off by 1e-12; measured at under a millisecond per fit, inside the shipped
2000-iteration cap), and one exact column rescale then lands the party margin
exactly. The tighter stop has to come first, or the rescale is large enough to
push a cell already sitting **at** its ceiling straight through it — which was
measured, and put Ekurhuleni back to +0.61%.

#### What did NOT change, and it matters

`pools_2026.json` is **byte-identical** (sha256 dfc97a61e4301363 before and
after). Johannesburg 2021 — the fit the live forecast is built on — has three
violations, still takes the projection, and its rate matrix is unchanged to
0.0e+00. Five of the eleven emitted artefacts move (`pools_2016.json`,
`pools_2021.json`, and tshwane/ekurhuleni/mangaung at 2021) and they are all
**backtest inputs**. This is a correctness fix to the historical fits; it does
not touch the published forecast.

#### The rejected alternative stands, and its justification was overstated

**Variant B — redistributing the truncated excess by headroom — remains
rejected.** It moves Al Jama-ah from 99.4% to 64.2% Indian/Asian on no evidence,
its bounds requiring nothing of the kind, and that is sufficient.

But **the "+0.33% vs +6.6%" comparison used to justify it was a one-city
measurement presented as the method's price.** Both numbers are Johannesburg
2021 only, and +0.33% is the **fourth smallest of the ten** — it is
Johannesburg's number, not the projection's. The honest statement of the
projection's cost is a **range across the ten fits: +0.00% to +3.71%**, and
after this fix +0.00% to +3.71% over the five fits that need it and exactly
+0.00% over the five that do not.
Variant B was never measured at the other nine. Quoting the most favourable of
ten as though it characterised the method is the same error as §1.36's, and it
happened in the write-up of the fix for §1.38.

---

### Part B — "almost certainly a delimitation boundary" was a wrong-city file

Emitting any non-Johannesburg city at 2026 refused with:

> *"100.0% of the roll is in wards with no measured composition… a ward-code
> mismatch between the 2026 roll and the composition fitted on 2021 — almost
> certainly a delimitation boundary."*

**That diagnosis was false, and it was published.** `_target_roll` ended:

```python
path = target.processed / f"vd_ward_{target.year}.csv"
if not path.exists():
    path = Path("data/processed") / f"vd_ward_{target.year}.csv"
```

`data/processed/` is not a shared root. It is **Johannesburg's own directory**,
because `cities/joburg.toml` is the one config carrying
`legacy_processed_root`. So every other city silently loaded **Johannesburg's
ward roll**, whose codes are `798000xx` against Tshwane's `799000xx` — a 100%
join failure, reported as geography. This is the un-namespaced-outputs hazard
already on file for this project, firing for real.

The branch could never have helped even the city it stole from: Johannesburg's
2026 target **is** its default target, so `target.processed` already resolves to
the bare `data/processed/` and the first line finds the file. **It was
reachable only by a city it could only mislead.**

Fixed: the fallback is deleted, a missing roll is a refusal naming the file it
wanted, and the join-failure message now prints the unmatched and the known ward
codes side by side so the next reader can tell a delimitation change (shared
prefix) from a wrong file (different prefix) without guessing.

    Tshwane 2026: no ward roll for this city. Wanted
    data/processed/tshwane/2026/vd_ward_2026.csv, which does not exist.

A **stated stand-in was removed with it.** `registered_at_target` used to fall
back to the fitting election's roll and print a warning; with the wrong-city
fallback gone, the only way to reach it was a genuinely missing roll, and
absorbing that into pool sizes five years out of date is worse than refusing.

#### The blocker was never delimitation, and the scoping answer is small

The 2026 VD layer is **already on disk for all eight metros**
(`data/raw/geo/vds2026_{CODE}.geojson`), and every one carries the five fields
`build_concordance.ward_parts` needs. Building each city's roll from it and
joining the result to that city's 2021-fitted composition:

| city | VDs | 2026 wards | registered | unmatched roll |
|---|---|---|---|---|
| joburg | 865 | 135 | 2,348,781 | 0.0% |
| tshwane | 774 | 107 | 1,619,402 | **0.0%** |
| ekurhuleni | 642 | 112 | 1,666,980 | **0.0%** |
| mangaung | 382 | 51 | 429,098 | **0.0%** |
| nelsonmandelabay | 253 | 60 | 601,715 | **0.0%** |
| buffalocity | 366 | 50 | 428,729 | **0.0%** |
| ethekwini | 858 | 112 | 1,982,217 | 0.8% |
| capetown | 802 | 118 | 2,100,405 | 1.8% |

**There is no delimitation blocker anywhere.** Five of the seven join perfectly.
eThekwini's 0.8% and Cape Town's 1.8% are one and two genuinely new wards
(`59500112`; `19100117`, `19100118`) created by 2026 ward-count growth — same
prefix, sequential numbers — both far below the 50% refusal threshold, and
eThekwini below even the 1% warning.

**What actually blocks it is two lines in `build_concordance.py`**, which I do
not own and have not touched:

1. `gpd.read_file(args.geo_dir / "vds2026_{CODE}.geojson")` never substitutes
   `{CODE}` (it does not go through `cityconfig.resolve_path`), so **the script
   is broken for every city, Johannesburg included** — the committed
   `data/processed/vd_ward_2026.csv` cannot currently be regenerated by the code
   that claims to produce it;
2. `--out-dir` defaults to a hard-coded `data/processed`, so even once (1) is
   fixed, `build_concordance.py --city tshwane` would **overwrite Johannesburg's
   roll**. The same hazard as Part A, one script upstream, still live.

---

## 1.41 The fix disabled the guard, and the silence was the evidence (2026-08-17)

A third independent review of the same day's work. The headline is a regression
this project introduced and then cited as proof the change had worked.

### The capacity guard went blind and its silence was read as success

`montecarlo.py` computed a party's pool ceiling from an **indicator**:

    1.0 if float(scenario["pools"][nm]["members"].get(pp, 0.0)) > 0 else 0.0

A membership of 0.00019 counted exactly like one of 1.0, so a party's ceiling was
the size of every pool it *touched at all* rather than of the pools it draws
from. That was survivable only while the fit emitted hard zeros. §1.38's
Duncan-Davis projection ended that: it seeds every zeroed cell, so the PA's 159
displaced votes flipped three indicator bits and its declared ceiling went from
the Coloured pool alone to **1.0000**.

Measured on the emitted artefacts:

| | ceiling exactly 1.0, 2026 | mean ceiling | the PA |
|---|---|---|---|
| indicator (as shipped) | **74 of 75** | 0.994 | 1.0000 |
| weight-aware | 0 of 75 | 0.447 | **0.0689** |

The PA draws **99.18% of its vote from a pool casting 6.73% of the ballots**, and
its 2026 centre asks for about **109% of that pool**. The guard could not see it.

**And the silence became the evidence.** §1.38 reported *"a guard with nothing to
guard against on this target"*, and this project reported to its owner that the
run showed *"0 fell back, nothing held in any draw"* — presenting a blind
detector's quiet as proof the constraint was satisfied. It was not satisfied; it
was unmeasurable. That is the sixth instrument failure in three days and the
second time a fix and its own refutation shipped together.

### The obvious repair is arithmetically sound and empirically a disaster

The fix proposed by the review, and adopted here before being measured, was the
largest citywide share a party can reach while holding its own weight vector with
every pool rate at most one:

    min over pools g with w_g > 0 of  poolshare_g / w_g

It is correct as arithmetic. On the artefacts it does exactly what it claims:
parties at a ceiling of 1.0 go from 74 of 75 to **0 of 75**, the mean ceiling
from 0.994 to 0.447, and the PA from 1.0000 to **0.0689** — bounding it near the
6.73% pool it takes 99.18% of its vote from.

**Nine city-years: coherent seat error 306 → 486.** Isolated by reverting this
one expression and nothing else, Mangaung alone goes **10 → 112**.

**Why, and the first version of this paragraph was too weak.** It said the bound
"assumes a party's pool composition is fixed… the draw varies each pool's
turnout, so the realised composition moves". True, but it makes this sound like
a variance problem you could out-sample. It is not.

`balance_margins` is **plain IPF**. IPF multiplies rows and columns, so it
preserves zeros and can scale any *positive* cell arbitrarily. The exact
single-party feasibility condition is therefore about the **support**, not the
magnitudes:

    want_p  <=  sum of poolshare_g over pools where R[g,p] > 0

**That is the indicator ceiling.** `min_g poolshare_g / w_g` is strictly tighter
and is **not a necessary condition** — it bounds a quantity IPF exists to move.
Demonstrated directly on Mangaung 2021: the ANC's weight-aware ceiling is 0.0983
and its actual share 0.5151, so the new cap rejects it by 5.2×; hand the same
matrix to IPF and it **converges, delivering 0.5151 exactly**, by relocating the
party — emitted composition `[0.8166 0.0214 0.1568 0.0052]`, realised
`[0.9638 0.0152 0.0167 0.0043]`.

So the composition is not jittered by the draw. It is **re-fitted
deterministically by IPF on every draw**, and the ceiling bounded the seed rather
than the outcome.

**Reverted, and the indicator ceiling is not a placeholder — it is the exact
bound.** Its job is to catch a ceiling near zero, a party in no usable pool at
all, and it still does that. What no cap can do is flag *implausibility*: the PA
drawing 99.18% of its vote from a 6.73% pool while its centre asks 109% of that
pool is a real disagreement and **not an infeasibility**, because IPF will
satisfy it by relocating the party wholesale.

The two jobs should be split. Keep the indicator as the hard gate, and add a
**displacement diagnostic** — `KL(realised ‖ emitted)` computed once at mid
turnout, so it is draw-invariant by construction and reports rather than clips.
It reads correctly on the case at hand, firing on exactly the parties whose
emitted weights are infeasible and going quiet once §1.42's denominator is fixed:

| | KL as emitted | after §1.42 |
|---|---|---|
| Mangaung 2021 ANC | 0.1163 | 0.0059 |
| Mangaung 2021 DA | 0.1005 | 0.0416 |
| Buffalo City DA | 0.0791 | 0.0064 |
| Johannesburg 2021 DA | 0.0358 | 0.0146 |

**Not yet built.** `ITERATING.md`: worse does not ship, and "arithmetically
defensible" is not a measurement — but note the refutation here is *analytic*,
not empirical. The 306 → 486 was the symptom; the IPF support argument is the
cause, and it would have been findable without a backtest.

This is the fourth time in three days that a proposed fix had to be measured
before it could be believed, and the second where the argument for it was
airtight and the number was not.

### The scoreboard was not reproducible run to run

`backtest.entrant_actual_for` broke a newcomer tie with
`max(newcomers, key=newcomers.get)`, which returns the first maximum in
**iteration order**. Three identical `compare_history` runs at 120 draws produced
three different JSON hashes and a ranks-13+ absolute band of **15.2164 / 15.2164
/ 15.3080**. Every A/B this project ran — including the ones that measured these
very fixes — carried that on top of seed noise.

Now `key=lambda p: (newcomers[p], p)`. **This makes the answer stable, not
right:** where two arrivals genuinely tie, one takes the ENTRANT relabel and the
other scores as missed entirely whichever way it falls. What the relabel *should*
do with a real tie is open.

*(The review's specific instance was wrong — eThekwini 2021 has ASA winning
outright on 4 seats, no tie. The reproducibility failure is real and was
reproduced here before being fixed; the example was not.)*

### Three excuses in `EXPECTED_INERT` that were not true

* **`poll_k`** was certified inert on a null measured **with the gate shut**
  (`poll_id` is None by default, so the branch never ran). Opened, `poll_k`
  1.0 → 1000 moves the DA **33.26 → 36.67pp and 89.8 → 99.2 seats**, live at
  2016, 2021 and 2026. This is `ITERATING.md` rule 6's exact fault, committed
  inside the commit that automated rule 6. A `PAIRED` sweep now perturbs a
  conditional lever together with its condition.
* **`individual_theta`** was excused as "dead as a default, live as an internal
  channel". The internal write is a **dead store** — confirmed three ways.
* **`entrant_geography`** was excused on a perturbation that supplied no
  `parent`. That is a fact about the sweep, not the model.

### A disposition inconsistency, left open on purpose

`theta_mode`, `f_other` and `individual_theta` are consumed at **zero of ten**
runnable targets — the identical evidence on which `ward_pr_ratio_overrides` and
`first_local_election` were deleted the same day. They have not been deleted,
because `theta_mode` is a declared contamination source in `backtest.FITTED_ON`
and removing it changes what the in-sample banner asserts. **One standard of
evidence, three dispositions.** That needs a decision rather than a default, and
recording it is not the same as resolving it.

### Smaller, and each the same shape

* The `capped_targets` counters' comment claimed two readers that **did not
  exist** — written in the commit arguing that a computed-and-never-read quantity
  is a defect. They were also module-level and never reset, so they accumulated
  across the nine city-years of one invocation. Reset per run and carried on
  `ModelRun`.
* `MACHINERY.md` still carried a `ward_pr_ratio_overrides` row while another line
  of the same document said the key was deleted — and that row was listed among
  the "six wrong rows fixed". **Fifth time a row has survived a pass written to
  fix it.**
* §1.37's `theta_mode` "inert at 2021, live at 2026" reading is **retracted**: it
  was measured while another worker re-emitted `pools_*.json`, so the baseline
  moved under the sweep. There is no asymmetry and no happy accident.
* "163 votes" was **159** — a typed figure disagreeing with the weight quoted in
  its own row.
* `interactive_template.html` emitted **six keys that no longer exist** into a
  block whose purpose is to be pasted into `--config`, which hard-exits on an
  unknown key. Latent only because the page is withheld.
* **Registered at 🔴, pre-existing and undocumented anywhere:** the run prints
  `implied θ outside §3.5 sanity ranges` and reports **ANC 57.7%, EFF 53.2%,
  Al Jama-ah 47.7%, PA 34.0%** on the shipped forecast. Over half the ANC's draws
  fall outside the model's own declared range for its retention, and no document
  mentions it. A diagnostic the model prints against itself, passed over.

### One review finding that does not reproduce

`ward_noise_sd` was reported *"live at 0.60 but fully inert at 0.1001 and below"*.
Measured against 0.10 on ward wins: **0.0 → 66 wards change, 0.05 → 15, 0.1001 →
0, 0.15 → 25, 0.60 → 423.** Monotone and live throughout. **The reviewer
re-derived it and withdrew the finding**, on two grounds better than the ones
given here: the zero is **symmetric** (0.0999 is as inert as 0.1001, whereas a
real dead zone "at 0.1001 and below" would be one-sided), and it **closes with
draws** — the same ±0.1% perturbations give 1 change at 400 draws and 1–2 at
1500. Resolution, not a dead zone. No change made.

One incidental worth keeping: at `ward_noise_sd = 0` the `rng.normal(...)` call
is **skipped entirely**, so the RNG stream desynchronises for every draw after
it. The 66 wards at `sd = 0` are a stream shift plus a noise removal, not a
clean measurement. **`sd = 0` is not a usable control point** for this or any
other lever whose guard skips a draw.

### The process lesson, now in `CLAUDE.md`

Partitioning parallel work by *file* is not enough. `pools.py` and
`compare_history.py` do not overlap as files and collide completely as work,
because both depend on `pools_*.json`. One writer owns the artefacts; nobody else
measures while it writes; the canonical run happens once, at the end, on a
settled tree. **A number measured against a moving artefact is not a
measurement, and it reads exactly like one.**

---

## 1.42 Two denominators for one quantity, and the pool collapse that built a guard (2026-08-17)

Found by chasing *why* §1.41's ceiling regressed rather than accepting *that* it
did. The ceiling was wrong. What it collided with is a separate and larger
defect, and this is its entry.

### The emitted compositions were arithmetically impossible

`PartyFit.composition(pool_votes)` names what it wants in its own signature and
docstring — *"where the party's votes come from"* — and the rates it multiplies
were fitted against `pool_votes = (comp * vote).sum(axis=0)`. The production call
handed it **`target_shares`, a projected REGISTRATION-share vector**, while
`montecarlo.pool_spec` sized the same pools from the **counted roll times
turnout**. Two denominators for one quantity, and a category error against the
function's own contract. The arrival branch three hundred lines below already
used the counted roll, so both sat in the same emitted dict.

Testing every emitted weight against `poolshare_g / actual_share_p` — the
ceiling of a party taking **100%** of that pool:

| normalised on | infeasible party-pairs, nine city-years |
|---|---|
| `pool_shares_at_target` (as shipped) | **5 of 339** |
| counted registration | 4 of 339 |
| **votes cast (registered × turnout)** | **0 of 339** |

Worst: **Mangaung 2021, the ANC claiming 15.68% of its vote from an Indian/Asian
pool casting 1.54% of the ballots — 5.2× the arithmetic maximum.** Then the DA at
Mangaung 2.28×, Buffalo City 2.12×, Ekurhuleni 1.64×, Johannesburg 2016 1.12×.
**Every violation is on the smallest pool**, and the last of them closes only
when turnout enters — registration alone leaves four.

### Two failures compounded

**The extrapolator amplifies.** `projected_pool_shares` extends the last interval
by `damping × step` = 0.6 × 2.5 = **1.5**, so the "damping" makes the step
*larger*. Mangaung's Indian/Asian series is `2011: 0.0, 2014: 0.0, 2016: 0.0524`
— the category is simply absent before 2016 — so it reads a spurious trend and
lands on `0.0524 × 2.5 = 0.1311`, 2.5× the counted share.

**And at Nelson Mandela Bay it went negative.** The same extrapolator sends that
pool to `0.01730 + 1.5 × (−0.01332) = −0.0027`, clipped to `1e-6` — **exactly
zero**. So every *fitted* party received no weight at all in a pool holding
**9,596 registered voters at 86.5% turnout, 2.28% of ballots cast**. Its emitted
membership was sixteen parties, every one of them `no_measured_vector`, with
`identified: []`.

**That collapsed pool is the failure the per-draw capacity guard was built for.**
`pool_spec`'s own comment blames it in as many words — *"its Indian/Asian pool
holds 2.3% of the city's votes and its sixteen members' centres do not add to
that between them, so no matrix"*. §1.33 measured that site at a 12.7% per-draw
failure rate and called it a *row*-side infeasibility that no column cap could
fix. It was neither: **it was this.**

### The fix, and what it is not

One line, plus hoisting two blocks: pass `registered × turnout[g][1]` — the
vector `pool_spec` itself builds — instead of `target_shares`.

* **5 infeasible party-pairs → 0.**
* Nelson Mandela Bay's Indian/Asian pool goes from **16 members, 0 identified**
  to **26 members, 2 identified**. The pool repopulates.
* Mangaung's ANC: Indian/Asian weight **0.1568 → 0.0205**, under its 0.0299 max.

**Nine city-years: 312 → 310.** That is nothing, and it is nothing for a reason
worth stating: **IPF pins the citywide levels whatever the seed composition
says** — measured identical to five decimals under the emitted and the corrected
seed. The composition is a KL anchor, not a claim the level layer acts on. So
this moves only the ward and seat layer, and there it nets to noise (NMB −2,
Mangaung −2, Ekurhuleni −2, Tshwane +2, Buffalo City +2).

**It is a correctness fix and the 2 seats are not claimed.** The case for it is
that the model was emitting compositions that cannot exist, that IPF was silently
repairing them every draw, and that one whole pool had been extrapolated out of
existence.

### Why nothing caught it

Because everything downstream absorbed it. IPF forced the pool margin on every
draw, so the levels came out right; `identified()` reported the collapsed pool as
unmeasured, which read as a known limitation rather than a bug; and the capacity
guard's per-draw failure at NMB was attributed to a row-side infeasibility in
§1.33 rather than to its cause. **Three separate mechanisms each turned the
defect into something that looked like ordinary weakness.**

The measurement that would have found it needs no backtest: for every emitted
weight, is `w_pg ≤ poolshare_g / s_p`? That is arithmetic on the artefact, and it
now belongs in the test suite.

---

## 1.43 The θ estimator is at its ceiling, measured four ways (2026-08-17)

The mid-ballot deficit — ranks 4-12 at **−36.88pp**, 71 of 81 party-slots in one
direction, 130 seats — has been attacked seven times and has moved once. The
obvious remaining suspect was the retention estimator, which throws away most of
what it is shown. **It is not the cause.** Four things were tried and three are
negative results; recording them is the point of this entry.

### The suspicion, and why it looked strong

`levels.theta_record` builds an observation as `(ratio, size)` and **discards the
metro and the year** at the moment of append. So VF Plus's seventeen θ
observations collapse into one scalar:

    2016:  CPT 1.220  EKU 0.966  ETH 0.918  JHB 0.811  MAN 0.779  NMA 0.427  TSH 0.793   gm 0.811
    2021:  BUF 1.376  CPT 1.509  EKU 1.031  ETH 1.195  JHB 1.347  MAN 1.095  NMA 1.131  TSH 1.243   gm 1.232

2021 is high in **all eight metros at once** — a year effect, and the estimator
cannot express it. A variance decomposition agreed: after removing each party's
own mean, **year explains 8.7%** of residual variance against metro's **2.5%**,
with a fragmentation signature (ANC 0.915 → 0.951 → 0.864 → 0.781 against IFP
0.904 → 0.675 → 0.949 → 1.771).

### NEGATIVE 1 — the year effect does not forecast

The decomposition is in-sample and **conditions on the party effect already being
removed**, so it measures the year's share of the residual, not its forecasting
value. Forward validation — predict each LGE from strictly earlier cycles only,
which is what forecasting does:

| specification | forward RMSE(log θ) |
|---|---|
| intercept only | 0.8153 |
| + size (today's centre) | 0.8045 |
| + size + party dummies, **no pooling** | **1.0308** |
| + size + party, ridge 2 (≈ `SHRINK`) | **0.7150** ← best |
| + size + year-trend | 0.8281 |
| + size + trend + size×year | 0.9159 |
| + size + trend + interaction + party, ridge 2 | 0.7879 |

The year term **hurts alone**, the fragmentation interaction **hurts badly**, and
both hurt on top of the party term. Exactly what §1.7 recorded — *"θ is political
weather"* — now measured on the full panel rather than one fold.

**The trap worth naming: 8.7% of residual variance explained is not forecasting
skill.** This project has now hit that shape three times — the signed rank bands,
the pooled PIT, and this.

### POSITIVE — what the same experiment vindicates

* **The party term is the single biggest win**, 0.8045 → 0.7150, and θ is
  autocorrelated at **+0.623** per cycle (OLS slope +0.394, so heavily
  mean-reverting — which is why §1.7's slope-1 transfer failed and why the pure
  centre is also wrong; the optimum is interior, and it is where the model sits).
* **Shrinkage is essential, not incidental.** Unpooled party dummies score
  **1.0308** — worse than using no party term at all.

### NEGATIVE 2 — `SHRINK = 2.0` is already optimal

Never fitted or swept in this project's history. Forward RMSE against the ridge:

    ridge   1.0    2.0    3.0    4.0    8.0   20.0
    unwtd  .7216  .7149  .7184  .7238  .7430  .7697
    v-wtd  .2200  .2311  .2436  .2537  .2780  .3033

The two criteria disagree — the same 🔴 already registered against the spine's
fitting criterion. Scored on the model itself, **`SHRINK = 1.0` is worse on all
three measures**: coherent seat error **314 against 312**, beats-uniform-swing
**5/9 against 6/9**, CRPS **268.3 against 264.8**. The conflict resolves in favour
of the unweighted result and the committed value. Register upgraded from
"pre-existing" to measured.

### NEGATIVE 3 — the blend is right to ignore the ρ record's evidence

`spine` computes `_worth_r` and discards it with an underscore; the blend weight
`w = k/(worth_θ + k)` is keyed on θ evidence alone. That looked like an oversight
— a party with a rich local record and thin θ is still pushed onto the national
route. Made symmetric, `w = (worth_ρ + k)/(worth_ρ + worth_θ + 2k)`:

| | seat error | beats u-swing | CRPS | ranks 4-12 |
|---|---|---|---|---|
| committed | **312** | **6/9** | **264.8** | −37.2 |
| both-worth blend | 338 | 4/9 | 280.8 | −40.98 |

Worse on everything. **The asymmetry is correct and is now documented as
deliberate rather than accidental.**

### THE ONE FIX THAT SHIPPED — a swallowed file error

`theta_record` built its paths with `f"data/raw/elections/npe{npe}_{code}_vd_party.csv"`
instead of the calendar template. The 1999 national election is on disk as
`npe1999_approx_JHB_vd_party.csv`, so the open failed, `_citywide` swallowed the
`FileNotFoundError` and returned `{}`, and the **entire NPE1999 → LGE2000
transition contributed nothing** while `lge2000_JHB_vd_party_clean.csv` sat
beside it. Resolved through the calendar: θ observations go **119 → 126** at
target 2021 and **257 → 264** at 2026.

Coherent seat error **310 → 312**, inside the ±2–4 draw noise, which is expected:
the recovered transition is Johannesburg-only. **Kept because a swallowed file
error is indistinguishable from a deliberate exclusion**, not because it scored.

**A side effect worth recording, because it looked like a regression.** The fix
changes θ, therefore the draws, and the CLASS 12 lever sweep immediately reported
`overhang_rule` inert. It is not broken. `allocate_with_overhang` returns
immediately on `rule == "cap" or not over`, so when no party's ward wins exceed
its proportional entitlement, all four rules — `cap`, `level`, `deduct`,
`expand` — return the same allocation. Measured at 200 draws, an excessive-seats
party appears in **1 draw of 200 at Johannesburg 2021 against 120 of 200 at
2026**. The lever is live at 2026, worth 52 seats of movement; the sweep's 40
draws simply stopped catching 2021's half-percent case.

It is now in `EXPECTED_INERT` for 2021 alone, and the entry says plainly that
this excuse is **weaker than `w_bye`'s**: that one is inert by construction, this
one only because a rare clause misses under this seed and draw count. Raise
`DRAWS` and the test's own `elif` will fail the entry as a stale register claim,
which is the intended behaviour. The sweep's failure message also gained the
**year** — without it, a lever inert at one target reads identically to one dead
at every target, and that omission cost a diagnosis here.

### Also found, not fixed

`theta_prior` and `_shrunk` are **two different estimators for the same
quantity**. `_shrunk` shrinks toward `size_centre`; `theta_prior` shrinks toward
the flat `mu_all` and ignores `size_centre` entirely. They disagree by
construction — ANC 0.869 against 0.862, PA 1.115 against 1.197 — and the drawer
uses one while the spine uses the other. At least one is wrong. Undocumented
until now.

**`SD_FLOOR` sets the level spread of the largest parties, and nothing else.**
Found while re-registering the constants this section disturbed. `sd_for` fits
dispersion against size and then clips it to `[0.15, 1.20]`; the fit reaches the
floor at about 15% share (`at_10%` = 0.163, `at_40%` = 0.150). So at
Johannesburg the floor binds on **ANC 49.6%, DA 29.6% and EFF 14.9% at 2021, and
ANC 32.0% and DA 25.0% at 2026** — and on nobody else. The ceiling binds only on
parties at 0.00% baseline share (10 of 46 at 2021, none at 2026).

Two things follow. First, **the top of the ballot's uncertainty is a typed
constant**, not a measurement, which is not what §3.5 or the spread table imply.
Second, the floor holds those parties *wider* than the fit asks for — and ranks
1-3 is exactly the band this model over-forecasts (+32.50pp signed, mean PIT
0.431) while both neutral coverage populations say the forecast is **too wide**
(58/89/96 and 77/89/95 against nominal 50/80/90). That makes `SD_FLOOR` a live
suspect for the excess width at the top of the ballot. **It has never been
swept.** Registered 🔴; not tested here, because it is a separate change and this
section's thesis is about the θ centre.

**Superseded the next day by §1.45, which swept it.** Two claims in the
paragraph above need correcting there: the floor does not merely hold those
parties wider than the fit asks, it flattens all three to one identical number;
and it is not simply excess width, because the θ record for that band says
0.227 — wider than either the fit or the floor. Read §1.45, not this.

### What this means for the mid-ballot

**Best-case forward RMSE is 0.715 in log — a typical error of about 2× on θ.**
That is the ceiling given four cycles and eight metros, and the model is at it.
The mid-ballot deficit is therefore **not an estimation failure**, and no
enrichment of the θ centre will close it. The remaining lever is correcting the
systematic level bias downstream, where an independent review has measured the
only candidate with an out-of-sample gain.

---

## 1.44 The mid-ballot deficit is a vector too widely spread, and one smooth shrink closes most of it (2026-08-17)

§1.43 established that θ cannot be estimated better and that the remaining lever
is the systematic level bias. This is that lever, and it is the largest single
improvement this model has had.

### The reframing that made it tractable

Seven attempts had treated the mid-ballot as an estimation problem for the
parties in ranks 4-12. It is not. Across nine city-years the two bands are
**+32.30pp** (ranks 1-3, over-forecast) against **−36.20pp** (ranks 4-12,
under-forecast), and ranks 13+ sit at **+0.78pp**. Two nearly equal and opposite
numbers are not two faults; they are one.

(Those three figures are measured on the cached mean vectors described below, at
400 draws over the full party list. `compare_history`'s own band table gives
+32.50 and −36.88pp on the same populations. The small gap is draw count and
nothing else — it is quoted here so the two instruments are not mistaken for a
disagreement.) The forecast's **share vector is too
widely spread**, and the standard remedy for a vector of noisy estimates is to
shrink it toward its centre.

### Screening the candidates without paying for a run each

Coherent seats are largest remainder on a **mean** vector, and summed absolute
PR error needs only a mean vector too. So the nine city-years' full mean
predicted vectors were cached once and every candidate transform fitted offline.
The screen was validated before it was trusted: rebuilding coherent seats from a
combined ward+PR entitlement reproduces the runs' own figures at **306 against
308**, one city-year off by two. Four one-parameter families,
leave-one-city-year-out, against a 148.55pp baseline:

| form | PR error | vs base | improved | seats |
|---|---|---|---|---|
| baseline | 148.55pp | — | — | 306 |
| threshold λ (the review's form) | 138.08 | −10.47 | 5/9 | 284 |
| power α (`q ∝ p^α`) | 138.52 | −10.03 | 7/9 | 278 |
| **smooth ramp** | **137.12** | **−11.43** | **7/9** | **276** |
| linear in size | 149.62 | +1.07 | 7/9 | 298 |

The ramp keeps `1 − c·s/(s+h)` of each level and gives the mass back by
renormalising. **`h` is a scale, not a tuned constant**: swept twenty-fold from
0.02 to 0.40 the gain runs −11.7, −13.6, −13.0, −11.4, −9.6, −9.3, −7.6, −5.6pp
and improves 7 of 9 at every value. There is no cliff, which is the whole
argument against the review's threshold — that one is knife-edged, giving −13.2%
at 5%, −5.6% at 8% and −0.8% at 15%.

### Why this is not scoreboard-fitting (ITERATING.md rule 10)

**The parameter is fitted on one city-year from a different cycle and transfers
to eight metros in the next one.** Fitted on Johannesburg 2016 alone it comes out
at **0.375**; applied to the eight 2021 metros — seven of them different cities,
none seen by the fit — it improves 6 of 8 and takes reconstructed seat error from
284 to 258. Leave-one-city-year-out across all nine chooses **0.350 in every one
of the nine folds**. A constant that lands in the same place from one city-year,
from nine, and across a cycle boundary is a property of the model, not of the
scoreboard.

**What rule 10 still has against it, stated plainly:** the *family* was chosen by
screening four candidates against these same nine city-years. The direction and
magnitude are corroborated out of sample; the choice of functional form is not.

### Scored in the model

Committed at `level_shrink = 0.35`, `level_shrink_scale = 0.04`, nine city-years,
at the protocol 1500 draws and again at 600 for the paired per-city-year detail:

| draws | | coherent seat error | beats u-swing | CRPS |
|---|---|---|---|---|
| **1500** | baseline | 312 | 6/9 | 264.8 |
| **1500** | level shrink | **264** | **8/9** | **236.4** |
| 600 | baseline | 308 | 7/9 | 265.0 |
| 600 | level shrink | 268 | 8/9 | 235.2 |

The two draw counts agree on direction and very nearly on size, which is the
point of running both: −48 and −40 against a draw noise of ±2 to ±4.

Per city-year at 1500 draws it improves seven, ties one and loses one:

| | JHB16 | JHB21 | TSH | EKU | ETH | CPT | MAN | NMB | BCM | total |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 20 | 106 | 42 | 30 | 38 | 40 | 8 | 20 | 8 | 312 |
| shrink | 18 | 94 | 32 | 20 | 32 | 32 | 8 | 18 | 10 | **264** |

The only loss is **Buffalo City, 8 → 10**, and the only tie is Mangaung — the
two smallest councils, at 100 and 101 seats, which is where the offline screen
predicted the cost would fall. At 600 draws Mangaung was a loss too (6 → 10), so
that one is partly draw noise and is not evidence of anything. Draw noise is ±2
to ±4; −48 is not in it.

### The band the whole exercise was aimed at

From the committed artefact, regenerated at 1500 draws — signed and absolute,
because a signed total is not an error total (rule 7):

| band | signed before | signed after | absolute before | absolute after |
|---|---|---|---|---|
| ranks 1-3 | +31.95pp | **+10.62pp** | 72.07pp | **61.09pp** |
| ranks 4-12 | −36.88pp | **−22.76pp** | 56.63pp | **48.42pp** |
| ranks 13+ | −1.55pp | **+5.60pp** | 14.57pp | 16.89pp |
| phantom | +6.48pp | +6.54pp | — | — |

**The −36.88pp that seven attempts could not move is −22.76pp**, a 38%
reduction, and ranks 1-3 fall by 67%. The absolute columns fall with the signed
ones in both bands, which is the test that matters: mass was moved to the right
parties, not merely cancelled between them. The three signed bands plus the
phantom still balance exactly — +10.62, +5.60 and +6.54 against −22.76 — because
shares sum to one and always did.

### The corroboration that matters most

`c` was fitted on summed absolute PR error. It was never fitted on calibration —
so the PIT is an independent statistic, and it moves the same way:

| band | mean PIT, baseline | mean PIT, shrink | (0.50 is right) |
|---|---|---|---|
| ranks 1-3 | 0.425 | **0.464** | over-forecast, corrected |
| ranks 4-12 | 0.750 | **0.680** | under-forecast, reduced |

(1500 draws. At 600 the same pair reads 0.425 → 0.464 and 0.750 → 0.675.)

Both bands move toward centre, and the per-city-year signed band errors fall
almost everywhere: eThekwini +2.82/−1.97 → +0.09/−0.23, Ekurhuleni +5.53/−5.49 →
+3.10/−3.94, Tshwane +7.88/−9.11 → +5.23/−7.08.

### The cost, which is real

The freed mass is returned by uniform renormalisation — a multiplicative boost
with many micro-parties to receive it. In the offline screen ranks 13+ go from
**+0.78pp to +8.68pp**: a band that was unbiased becomes an over-forecast one.
**In the model the damage is much smaller** — under 1pp per city-year — because
the pool constraints and the IPF absorb most of it, but the sign is the same and
it is the first thing to attack if this is revisited.

Three targeted redistributions were measured and all three **scored worse** on
both summed absolute error and seats, while balancing the bands better:

| redistribution | PR error | seats | bands 1-3 / 4-12 / 13+ |
|---|---|---|---|
| uniform renormalise (committed) | 134.91 | 272 | +6.63 / −20.21 / +8.68 |
| to predicted ranks 4-12 | 139.32 | 284 | −0.57 / −9.01 / +4.01 |
| to everything below the top 3 | 137.12 | 280 | −0.98 / −12.84 / +8.53 |
| below top 3, weighted by room | 142.58 | 288 | +16.37 / −22.33 / +1.71 |

That is a genuine conflict between a signed-bias criterion and an absolute-error
one, and it is recorded rather than resolved by preference.

### Two things it does NOT break

**The pool-capacity guard does not reopen.** The shrink lifts small parties, and
the PA is the party whose 2026 level was asking about 102% of the Coloured pool,
so this was the obvious way for the change to do damage. Measured at 2026, 300
draws, lever off against on: the PA goes 0.0635 → 0.0668, still under its 0.0689
arithmetic ceiling, and `cap_moved` and `cap_undershoots` are **zero in both
arms** — the Duncan-Davis enforcement of §1.42 had already closed that hole and
the shrink does not force it back open.

**The published 2026 forecast does move**, and materially: the DA goes 0.328 →
0.310 on the PR ballot with the ANC flat at 0.201 → 0.202 (the ANC is smaller in
2026, so the size-dependent pull takes less from it). That is a forecast change
to be republished deliberately, not a side effect to be discovered later.

---

## 1.45 `SD_FLOOR` swept: it is not an error, and it is buying seats with width (2026-08-18)

§1.44 registered `SD_FLOOR` at 🔴 as a live suspect and never-swept. Swept now,
nine city-years, 600 draws.

### What the floor actually does

It does not merely clamp the largest party. The size fit produces a real,
monotone gradient across the top of the ballot, and **the floor flattens it to a
single number**. At Johannesburg 2021, `theta_prior`'s emitted `sd(log θ)`:

| `SD_FLOOR` | ANC (49.6%) | DA (29.6%) | EFF (14.9%) |
|---|---|---|---|
| 0.05 or 0.10 — floor never binds | 0.1110 | 0.1257 | 0.1484 |
| **0.15, committed** | **0.1500** | **0.1500** | **0.1500** |
| 0.30 | 0.3000 | 0.3000 | 0.3000 |

So at the committed value the three largest parties are given **identical**
level spreads, and the size-dependence that `sd_for` exists to provide is
switched off for exactly the parties that hold most of the council.

### The scoreboard says the floor earns its place

| `SD_FLOOR` | coherent seats | CRPS | beats u-swing |
|---|---|---|---|
| off (0.05 / 0.10) | 272 | 238.0 | 8/9 |
| **0.15, committed** | **268** | **235.1** | 8/9 |
| 0.22 | 276 | 242.1 | 8/9 |
| 0.30 | 272 | 256.6 | 8/9 |

0.15 is the optimum of those tested on both. **So it is not an obvious error and
it is not removed.** Note the seat column honestly: 268 against 272 is 4 seats
at 600 draws, where draw noise is ±2–4, so the seat result is at the edge of
noise. CRPS is the firmer signal, and it agrees.

### But the width statistic says the opposite, and that is the finding

`dispersion` is the exact `sd(z)`, where **1.0 is correct width**:

| `SD_FLOOR` | ranks 1-3 sd(z) | ranks 4-12 sd(z) |
|---|---|---|
| off | **0.948** | **0.684** |
| 0.15, committed | 0.842 | 0.628 |
| 0.22 | 0.818 | 0.662 |
| 0.30 | 0.786 | 0.682 |

**With the floor off, the top of the ballot is very nearly the right width
(0.948 against a nominal 1.0). The committed floor makes it too wide (0.842),
and it makes ranks 4-12 worse as well.** Every step up from "off" is a step away
from correct width, in both bands.

### Is 0.15 a judgement or a derived number? A judgement — and the fit under it is the real problem

**Typed, not derived.** No derivation of 0.15 is recorded anywhere. The comment
directly above the constant argues that there is no large-party *threshold* —
which is a different claim, about shape, not about this value — and the value
has simply stood since.

But measuring the quantity it clamps changes the story. Direct binned
`sd(log θ)`, eight metros, all transitions strictly before 2026, n=264:

| baseline share | n | median θ | sd(log θ) |
|---|---|---|---|
| 0 – 0.2% | 79 | 1.310 | 0.925 |
| 0.2 – 0.5% | 63 | 1.028 | 0.815 |
| 0.5 – 2% | 51 | 1.015 | 0.659 |
| 2 – 10% | 24 | 0.881 | 0.638 |
| 10 – 15% | 8 | 0.976 | 0.147 |
| **≥ 15% — where the floor binds** | **39** | 0.922 | **0.227** |

**The record says those parties move by 0.227 in log. The size fit gives them
0.111 to 0.148. The typed floor of 0.150 is still 34% below the measurement.**

So the floor is not a hedge bolted on top of a good estimate. It is a partial,
undeclared correction toward a dispersion the fit **under-produces at the top of
the ballot** — and it does not correct far enough. The defect is in `sd_for`,
which fits `log(residual²)` linearly in `log(size)` across a population whose
variance is dominated by the 142 observations under 0.5%, and then extrapolates
that line out to 50% share. The direct estimate for the band (n=39) is the more
trustworthy number for large parties, and the fit disagrees with it by 2×.

### The tension this leaves, unresolved

Two sound measurements point opposite ways:

* The **θ record** says large-party dispersion is 0.227, so both the fit and the
  floor are too narrow.
* The **realised forecast error** says the opposite: with the floor off,
  ranks 1-3 width is already nearly correct (sd(z) 0.948), and raising θ
  dispersion makes the whole forecast too wide (0.842 at 0.15, 0.786 at 0.30).

The most likely reconciliation is **double counting**: θ is not the only source
of level spread in a draw — the turnout copula, the pool Dirichlet and the ward
noise all contribute — so a forecast carrying the full historical θ dispersion
*plus* those would be wider than the errors it actually makes. If that is right,
the θ-dispersion layer should not be asked to reproduce the marginal record on
its own, and the honest statement is that **no part of this model currently owns
the total-width budget**. Nobody has decomposed realised width by source, and
until someone does, tuning `SD_FLOOR` is tuning one term of a sum nobody has
written down.

### Disposition

**Kept at 0.15.** It is optimal among the values tested on both scored metrics,
and worse does not ship. Register moves 🔴 → 🟡: measured, best of those tried,
but **still a typed number, still not derived, and now known to sit between a
fit that is too narrow and a record that is wider than the forecast can afford.**

The next move is not to tune this constant. It is to decompose realised forecast
width by source and find out which layer is over-contributing — at which point
this floor should be re-swept, and may well want to move in either direction.

### A note on sweeping it

0.05 and 0.10 are byte-identical because the fit never goes below 0.111, so
neither binds. A sweep of this constant has exactly one "off" arm however many
low values are tried, and reading two identical rows as a dead lever would be
wrong.

---

## 1.46 The artefacts now carry a key, and the model is not bit-reproducible across processes (2026-08-18)

Two findings from the same afternoon, the second found by accident while
checking the first.

### `pools_*.json` now says what built it

The specs are precomputed, so `pools.py` can change without them changing, and a
measurement taken across that gap is not a measurement. The only protection was
`CLAUDE.md`'s *"one writer, and nobody measures while it writes"* — a rule a
person has to remember — and **it has already failed twice**: a lever sweep
returned different answers on two identical runs, and two `EXPECTED_INERT`
reasons written from those readings had to be retracted.

Each spec now carries an `artefact_key`: the city, the target, a hash of the
config, and a hash of `pools.py`. `run_model` checks it and prints a named
reason when it does not match. Two tests hold it up — one that every committed
spec is current, one that a perturbed key is actually *reported*, because a
staleness check that cannot detect staleness is the blind pool ceiling again.

**The code hash ignores comments and docstrings**, deliberately. This project
requires the documentation to change in the same commit as the model, so a
whole-file hash would fire on every improved comment — and a guard that cries
wolf is a guard everyone learns to ignore. It hashes the parsed syntax tree with
docstrings stripped: verified that a rewritten docstring plus a new comment
leaves the hash unchanged, and that `SPLIT_SD_FLOOR` 0.90 → 0.91 moves it.

All eleven specs were re-emitted to carry keys. **Emission is deterministic: the
only difference from the pre-key versions, in all eleven, is the key itself** —
no value changed, which is both the safety check for the re-emit and evidence
that re-emitting is not the hazard the protocol treats it as. The hazard is
re-emitting *while someone is measuring*, which is a different thing.

Worth recording alongside: **the pool specs are not tracked by git.** The
artefacts the entire model depends on have no version history at all, which is
part of why staleness was invisible.

### The model is bit-reproducible within a process, not across one

Found while verifying the re-emit had moved nothing: two runs at the same seed
in different processes hash differently. At first reading that looks like the
re-emit having moved the model. It is not, and the check that separated them is
worth keeping — current code against the pre-key artefact and against the
re-emitted one, in one process, gave the same answer for both.

The cause is `levels.theta_record`, which iterates `set(before) & set(after)` at
`levels.py:243` and `:274` and appends each party's observations in that order.
Set iteration order over strings varies with `PYTHONHASHSEED`, and floating
point addition is not associative, so the sums differ in their last bits.

**The size of it is 5.6e-17** — the last bit of a float64, on the ANC's mean PR
share, with 43 of 56 parties differing at all. Five separate processes give
**identical** scored results at Johannesburg 2021, 600 draws: coherent seat
error 92, CRPS 68.716, list MAE 5.7793, every digit.

So this is not a correctness problem and nothing measured in this repository is
in question. It is an **instrument** problem, and it has two consequences worth
writing down:

* `test_drawer.py` claimed the draw is "bit-for-bit reproducible for a given
  numpy version". True within a process, false across one; the comment is
  corrected.
* **A bit-level hash is not a valid cross-process instrument**, so the
  acceptance test for parallelising the nine city-years cannot be "identical bit
  for bit" — it must be "identical scored metrics". That criterion had already
  been written the wrong way and would have sent someone chasing a phantom.

Setting `PYTHONHASHSEED` in the harness would make runs bit-comparable and is
worth doing on its own account. Sorting the two iterations would fix the cause
outright and is a one-line change, but it moves every number in the last bits
and therefore wants its own deliberate golden re-record rather than being
smuggled in here.

---

## 1.47 Deleting a one-party constant exposed a double count in the mechanism meant to replace it (2026-08-18)

The project owner asked for `pa_contestation_uplift` to go: *"a single party
fiddle must go."* Removing it turned out to uncover two larger things.

### The constant

1.25, applied to the PA's ward/PR ratio alone, because the PA fought 52 of 135
Johannesburg wards in 2021 while the model assumed every party fought all of
them. It lived in the `elif` for when the target's nomination lists are not
published — **which is every live forecast and no backtest**. The register
carried that as a disclosure ("consumed at 2026 only, so it cannot contaminate a
backtest"). It reads better the other way round: **the one place it was live was
the one place nothing could test it.**

`levels.contestation`'s own docstring had said it *"replaces
`pa_contestation_uplift`"* for weeks while the constant went on firing.

### First finding: 2026 was the only target running without contestation at all

Because the constant held that branch, the live forecast applied **no**
contestation to anybody, while every backtest applied it to everybody. The
backtests were validating a different model from the one being published. That
is the more serious half of what the constant was hiding.

### Second finding: the mechanism itself double-counts

Generalising the fallback made the branch testable for the first time — suppress
2021's own lists, fall back to 2016's, and score it. Four metros at 2021, 400
draws:

| | coherent seats | CRPS | ward MAE |
|---|---|---|---|
| oracle — the target's own lists | 176 | 150.3 | 10.79 |
| fallback — the previous LGE's lists | 178 | 150.3 | 9.64 |
| **no contestation at all** | **174** | **148.1** | **8.90** |

The fallback is a sound substitute for the oracle, which was the question asked.
But **both are worse than not applying contestation at all**, and worst on ward
MAE, the metric the mechanism directly targets.

The cause is a double count. `ward_pr_ratios` measures each party's ward-over-PR
ratio from the **previous LGE's actual votes**, and a party that stood in 38% of
wards banked ward votes in only those wards — so the measured ratio has already
been discounted by that party's contestation. Multiplying by the contested share
again applies the same discount twice. Measured at Johannesburg:

* correlation between the measured ratio and the contested share: **+0.699**
* mean ratio for parties contesting under 25% of wards: **0.512** (n=13)
* mean ratio for parties contesting over 75%: **1.075** (n=10)
* divide the ratio through by contestation and the correlation flips to
  **−0.499** — an over-correction, which is what a second application is.

### The fix: contestation is a CHANGE, not a level

What the measured ratio cannot know is how a party's slate has changed *since*
the election it was measured at. So the multiplier is now
`contest_target / contest_previous_lge`, against the same LGE `ward_pr_ratios`
reads. Four metros at 2021, 400 draws:

| | coherent seats | CRPS | ward MAE |
|---|---|---|---|
| as a level (what shipped) | 176 | 150.3 | 10.79 |
| none | 174 | 148.1 | 8.90 |
| **as a change** | **170** | **146.7** | **8.53** |

Best on all three, and it resolves the live-forecast branch by construction:
with no nomination lists the ratio is 1.0, so **2026 correctly gets no
adjustment** — which is what it was accidentally doing before, for the wrong
reason and with one party excepted.

Scored on the full panel, nine city-years at the protocol 1500 draws:

| | coherent seats | beats u-swing | CRPS |
|---|---|---|---|
| committed (contestation as a level) | 264 | 8/9 | 236.3 |
| **as a change** | **254** | 8/9 | **232.8** |

Per city-year, against the committed run: 18→16, 94→86, 32→30, 20→18, 32→32,
32→34, 8→10, 18→18, 10→10. **Four improve, two worsen by two apiece (Cape Town
and Mangaung), three are level** — so the −10 is carried mostly by Johannesburg
2021, and that is worth saying rather than quoting the total alone.

The ward MAE column moves much further than the seat column, which is where a
**ward-ballot** correction should show: Johannesburg 2021 5.29 → 4.59pp, Cape
Town 2.27 → 1.41pp, eThekwini 1.24 → 0.78pp, Tshwane 1.78 → 1.33pp. Draw noise
is ±2 to ±4 on seats and −10 is outside it, but the ward column is the one that
carries the argument.

**This is the mechanism being made correct, not tuned.** No constant was fitted:
the form follows from noticing that `ward_pr_ratios` already contains the thing
being multiplied in again.

### A register entry retired itself

`overhang_rule` was excused as inert at 2021 on 2026-08-17, and that entry
recorded its own weakness: the overhang clause fired in 1 draw of 200 there, so
the lever was inert only because a rare clause missed under one seed and draw
count, and *"raise DRAWS or change the seed and it may become live, at which
point the `elif` above will fail this entry as a stale register claim."*

Changing the ward wins is exactly what this correction does. The clause now
fires at 2021, the sweep reported the entry as stale, and it is deleted. **The
excuse expired on its own terms, one day after it was written**, which is the
behaviour the register was built for — an excuse that cannot go stale is a
suppression.

### What it does to the published forecast

Removing the constant is not cosmetic. Johannesburg 2026, 400 draws, ward share
and mean seats before and after:

| | ANC | DA | EFF | ASA | MK | PA |
|---|---|---|---|---|---|---|
| before, ward share | 20.28% | 32.09% | 9.61% | 8.50% | 8.87% | **8.07%** |
| after | 21.68% | 34.31% | 10.26% | 9.02% | 9.49% | **2.67%** |
| seats before → after | 59.0 → 60.4 | 83.2 → 86.4 | 24.8 → 25.6 | 25.9 → 26.6 | 24.6 → 25.4 | **19.5 → 12.4** |

The PA loses about seven seats. That is the whole of what the one-party constant
was worth, and it was worth it in a direction nothing could check.

---

## 1.48 The width budget: the within-pool Dirichlet supplies the spread, not θ (2026-08-18)

§1.45 left `SD_FLOOR` stuck between two sound measurements pointing opposite
ways, and said the next move was to decompose realised width by source rather
than tune the constant. This is that decomposition. `src/width_budget.py` runs
it.

### Method, and the defect in the obvious version of it

Disable one variance source at a time; measure how much of the DRAWN spread
disappears, as `sd(log citywide PR share)` per party across draws. That quantity
needs no outcome, so it can be measured on the live target as well as a
backtest.

**Switching a source off also changes how many random numbers the draw
consumes**, so every later draw shifts. A single-seed ablation therefore mixes
"this source contributed variance" with "the stream moved" — and the first run
reported *negative* contributions for ward noise, i.e. removing a noise source
appearing to make the forecast wider. That is impossible, and it was the
giveaway. The harness now averages five seeds and prints the full model's own
seed-to-seed spread as a floor: 0.02–0.08, so nothing under about 0.15 is a
finding.

### The budget — Johannesburg 2021, 300 draws, mean of five seeds

Share of drawn variance removed, `1 − var_without / var_full`:

| source removed | ANC | DA | EFF | ASA | IFP | VF+ | PA | AlJam | ACDP | COPE |
|---|---|---|---|---|---|---|---|---|---|---|
| θ level shock | 0.37 | 0.54 | 0.20 | 0.07 | 0.21 | 0.19 | 0.24 | 0.44 | 0.28 | 0.07 |
| pool turnout copula | −0.02 | 0.03 | 0.03 | 0.03 | −0.02 | −0.12 | 0.06 | 0.02 | 0.11 | 0.01 |
| **within-pool Dirichlet** | **0.67** | **0.39** | **0.84** | **0.97** | **0.97** | **0.93** | **0.93** | **0.83** | **0.97** | **0.98** |
| ward noise | −0.02 | 0.07 | −0.03 | 0.05 | −0.09 | −0.01 | 0.06 | 0.06 | 0.01 | 0.01 |
| per-VD turnout noise | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| turnout blend jitter | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| entrant slot | −0.01 | 0.04 | 0.06 | 0.01 | −0.02 | −0.03 | 0.07 | −0.07 | 0.06 | −0.01 |
| everything except θ | 0.67 | 0.41 | 0.84 | 0.97 | 0.97 | 0.94 | 0.93 | 0.84 | 0.97 | 0.98 |

Four things follow, and the first was not expected.

**1. The within-pool Dirichlet is the dominant source of width for almost every
party** — 83% to 98% for everyone except the ANC (67%) and the DA (39%). It has
never been treated as a width lever; `DIRICHLET_FLOOR` sits in the register as a
guard against a degenerate concentration, not as the thing that decides how wide
the forecast is.

**2. θ and the Dirichlet are very nearly the whole budget, and roughly additive
in variance** (ANC 0.37 + 0.67 = 1.04, EFF 0.20 + 0.84 = 1.04, DA 0.54 + 0.39 =
0.93), which is what two independent multiplicative shocks should give. The
"everything except θ" row reproduces the Dirichlet row almost exactly, so the
remaining sources really are negligible rather than merely small.

**3. Two constants do nothing to citywide width — and that is a statement about
citywide width only.** `turnout_noise_sd` and `turnout_blend_jitter` remove
**exactly 0.00** at every party, confirming the register's note that 0.08 i.i.d.
over 855 VDs contributes ~0.003 citywide. **The copula's ≤0.11 is a weaker
claim** and was over-stated in the first draft of this section — see the
verification below.

**4. It answers §1.45.** The θ record for parties ≥15% gives sd(log θ) = 0.227
against the fit's 0.111–0.148, and §1.45 could not say whether the layer was too
narrow or the forecast too wide. Now it can: **θ carries 37% (ANC) and 54% (DA)
of the variance, and the Dirichlet independently supplies most of the rest.** A
layer that is one term of a sum should not be asked to reproduce the marginal
record of the whole. Raising θ dispersion to 0.227 would multiply θ's variance by
about 2.3 and take the DA's total to ~1.7× — when realised ranks 1-3 `sd(z)` is
already **0.855**, i.e. the forecast is about 17% too wide *now*.

### Verified against the obvious objection: are these mechanisms even running?

A source that removes **exactly** 0.00 looks more like a broken mechanism than a
small one, and this repository has shipped that mistake before. So each was
checked rather than argued.

**They run, and they vary.** Instrumented over one run: the copula is called 240
times returning pool turnouts from **0.486 to 0.740** (sd 0.075), the level
shock 60 times returning 0.943 to 1.363, the Dirichlet 240 times. The ablation
patches are reached — the copula's replacement was called 5,000 times across the
five-seed measurement.

**The turnout knobs are LIVE, and they act on the ward layer, not on citywide
dispersion.** Perturbed at Johannesburg 2021, 250 draws:

| setting | ANC citywide sd | ward wins moved | |
|---|---|---|---|
| noise 0, jitter 0 | 0.073329 | — | baseline |
| noise 0.08 (committed) | 0.073329 | **46** | |
| noise 0.8 | 0.073329 | **418** | |
| jitter 0.25 (committed) | 0.073329 | **14** | |
| jitter 1.0 | 0.073329 | **32** | |

Citywide dispersion is identical to six decimals across a tenfold change, while
ward wins move by hundreds. Every output — PR shares, ward shares, ward wins,
seat draws — differs at every setting. **These are ward-allocation levers that
average out citywide, which is what i.i.d. noise over 855 voting districts
should do.** They are not broken, and "0.00" here means "not a source of
citywide width", not "does nothing".

**The copula claim was over-stated and is corrected here.** The table above
reports −0.02 for the ANC; three seeds at 250 draws give **+0.050**, and the
noise floor is 0.04. So "essentially nothing" was wrong. Measured across parties
of different pool concentration, the shape is coherent:

| party | pool concentration | variance the copula supplies |
|---|---|---|
| **PA** | ~94% Coloured | **+0.124** |
| ANC | broad | +0.050 |
| DA | broad | +0.044 |
| Al Jama-ah | narrow but tiny | −0.070 (its own sd is 0.945; this is noise) |

**The copula supplies roughly 4–12% of drawn variance, most for the party most
concentrated in a single pool** — which is exactly what a pool-turnout mechanism
should do, and is the evidence that it works rather than merely runs.

One hypothesis was tested and **refuted**: that it cancels because a *common*
turnout factor divides out of a share. If that were the mechanism, decorrelating
the pools would make the copula bite. It does not — the contribution is +0.055
at `TURNOUT_CORRELATION = 0.0` against +0.050 at 0.63, unchanged. So the
correlation constant is not what makes the effect small, and **why 4–12% rather
than more is still unexplained.**

### Why the copula's effect is bounded — mostly answered

The remaining puzzle was why a mechanism that swings pool turnout from 0.486 to
0.740 supplies only 4–12% of a party's drawn variance. The answer is that **the
IPF pins the expectation**, so pool turnout cannot move a party's level — only
the split around it.

Measured from a run's own trace, drawn mean against the centre it was given,
Johannesburg 2021 at 400 draws: **mean ratio 1.0012 across the 14 parties above
0.2%**. The level is where the centre put it.

Two qualifications, both real:

* **The pinning is tight in aggregate and loose per party** (sd 0.0763). The
  pattern is systematic rather than random — ANC 0.921, DA 0.930, EFF 0.914
  against AIC 1.125 — the top of the ballot drawn 7–9% *below* its centre and
  small parties above. That is the entrant rescale (`target *= (1 − share)`)
  and the arrival slot taking mass, which `test_drawer.py` documents as a known
  and separate effect.
* Correlations between a pool's drawn turnout and a party's share run **+0.02 to
  +0.15**, and the DA's is ~+0.12 against *every* pool, which is a common-turnout
  signature rather than a differential-composition one. So the residual is not
  purely the differential either.

So: level pinned, split free, residual small. That is enough to stop treating
the copula's size as evidence of anything about `TURNOUT_CORRELATION`, and not
enough to call the mechanism fully explained.

### What this means for `SD_FLOOR`

**It should come down, not up** — the opposite of what the θ record alone
suggests, and the same direction the width statistic said in §1.45. With the
floor off, ranks 1-3 `sd(z)` goes 0.842 → 0.948 against a nominal 1.0.

The obstacle is unchanged and is not a width question: removing the floor cost 4
coherent seats and 2.9 CRPS, because extra width hedges the residual LEVEL bias
that survives (ranks 1-3 mean PIT is 0.483, not 0.500). That is `ITERATING.md`
rule 8's pathology exactly, and the order of operations follows from it —
**close the residual level bias first, then drop the floor**, rather than paying
for a better-calibrated width with a worse score.

---

## 1.49 One estimator, not two — and the divergence never reached a forecast (2026-08-18)

`theta_prior` and `_shrunk` estimate the same quantity and disagreed by
construction: `_shrunk` shrank a party toward `size_centre`, `theta_prior`
toward the flat `mu_all`. ANC 0.869 against 0.862, PA 1.115 against 1.197. The
register carried it at 🔴 as *"at least one is wrong"*, and it was picked up here
because it looked like the most likely remaining source of a **size-dependent
level bias** — the fault the level shrink was built to correct.

### The flat centre was the wrong one

`theta_prior`'s comment opened *"One common centre: the record says the trend
does not vary with size."* **That claim is false**, and `size_centre` exists
because it is: on eight metros the median θ runs **1.31 below 0.2% of the vote
against 0.94 above 15%** — small parties gain going into a local election and
large ones lose (§1.30's Reif–Schmitt second-order effect). A common centre
erases that, and erases it against exactly the mid-ballot parties the model
under-forecasts.

### But it reached nothing, and that is the finding

The divergent quantity is the **mode**. Two places read it, and neither is live:

* The `blended_centres` branch for parties **the spine cannot reach** — and the
  spine reaches every party at every target measured (Johannesburg 2021 46 of
  46, 2026 76 of 69, Tshwane, Ekurhuleni and Cape Town likewise; **zero parties
  and 0.0000% of the baseline** take the fallback).
* The **by-election clamp**, which reads the band as `low/mid` and `high/mid` —
  relative spreads, from which a shift in the centre cancels exactly.

Confirmed by perturbation rather than by reading: shifting the whole band ×3 —
which is what a change of centre does — gives **byte-identical seat draws at
2021 and at 2026**.

**A wrong perturbation first said otherwise, and it is worth recording why.**
Multiplying only the *mode* by 3 moved the 2026 forecast, and that looked like
proof the centre was live. It was not: tripling the mode alone breaks the
`low/mid` ratio, which is not something a change of centre can do. What that
run actually demonstrated is that **the by-election clamp is live at 2026 and
sensitive to the band's SPREAD** — a real fact about a different quantity.
`ITERATING.md` rule 6 says perturb to a value that must change the answer; it is
equally necessary that the perturbation be one the real quantity could produce.

### Disposition

`theta_prior` now shrinks toward `size_centre`, at the party's own weighted
observed size, exactly as `_shrunk` does. The two agree to **1e-16** across 26
parties at 2021 and 42 at 2026. Four city-years at 400 draws are **identical to
every digit** before and after, so this is a correctness fix and is not claimed
as an improvement.

The register moves 🔴 → ⚪. What remains true and is worth keeping in view: the
quantity `theta_prior` *does* supply to the forecast is the **`sd`**, not the
mode — and that is the `SD_FLOOR` path of §1.45 and §1.48, which is still open.

---

## 1.50 `SD_FLOOR` is not a hedge — it is roughly the right conditional dispersion (2026-08-18)

§1.45 registered `SD_FLOOR` as a typed number that scored best without anyone
knowing why, and read it as width hedging a level bias. §1.48's width budget
said it should come down. Both readings are now superseded, and the constant
stays — for a reason, which is the difference that matters.

### The level bias was closed twice, and the floor did not come free

§1.45's plan was: close the residual level bias, then drop the floor. The level
shrink (§1.44) and the contestation correction (§1.47) both did that. Re-swept
on the current model, nine city-years, 600 draws:

| `SD_FLOOR` | coherent seats | CRPS | beats u-swing |
|---|---|---|---|
| off (0.05 / 0.10) | 268 | 234.5 | 7/9 |
| **0.15, committed** | **258** | **231.9** | 7/9 |
| 0.22 | 266 | 239.2 | 6/9 |

**The gap widened rather than closed** — 4 seats before, 10 now. So the
"hedging a level bias" reading is refuted: two changes that measurably reduced
the level bias left the floor more valuable, not less.

### The two bands want opposite things

| `SD_FLOOR` | ranks 1-3 sd(z) | ranks 4-12 sd(z) |
|---|---|---|
| off | **0.952** | 0.786 |
| 0.15 | 0.844 | **0.856** |
| 0.22 | 0.826 | 0.876 |

`sd(z) = 1.0` is correct width. **Ranks 1-3 want the floor off; ranks 4-12 want
it on**, and 0.15 is where the trade balances. A floor that binds on two or
three parties moves the mid-ballot's width because shares sum to one — so this
is not a "top of the ballot" constant at all, it is a lever on the *relative*
width of top against middle.

### A real statistical bug in the fit, and correcting it makes the model worse

The dispersion fit is 2.5× to 3.8× narrower than the binned record at every
size. That is not a modelling choice; it is a **known bias**. `sd_for` recovers
a dispersion from a least-squares line through `log(residual²)`, and if
`r ~ N(0, σ²)` then `r²/σ²` is chi-square with one degree of freedom, so
`E[log χ²₁] = ψ(½) + log 2 = −1.270363`. The line therefore estimates
`log σ² − 1.270363`, and exponentiating half of it returns **0.5298 σ**. The
correction is `exp(1.270363/2) = 1.887365` — derived, not fitted.

It checks out to three decimals against the record it is fitting: the binned
`sd(log θ)` for parties at or above 15% of the vote is **0.227** over 39
observations, the uncorrected fit gives **0.120**, and 0.120 × 1.8874 =
**0.2265**.

**Applied, it makes the model worse on everything:**

| | coherent seats | CRPS | beats u-swing | ranks 4-12 sd(z) |
|---|---|---|---|---|
| uncorrected, floor 0.15 | **258** | **231.9** | **7/9** | **0.856** |
| chi-square corrected | 268 | 246.8 | 6/9 | 0.522 |

(With the correction the floor stops binding at all — the corrected fit never
goes below 0.15 — which is why all three floor values give one row.)

### Why, and what the floor actually is

This is §1.48's width budget stated as a measurement rather than an argument.
**The binned record is a MARGINAL dispersion** — everything that moved a party's
local share against its national one — while **this layer is CONDITIONAL**: the
within-pool Dirichlet independently supplies 39–98% of drawn variance, and the
turnout and ward layers a little more. Asking θ to reproduce the marginal record
counts the same uncertainty twice, and the forecast goes from nearly correct
width (0.856) to badly over-wide (0.522).

So **`SD_FLOOR = 0.15` is approximately the conditional dispersion this layer
should carry**, sitting between the raw fit (0.120, too narrow because of the
bias above) and the marginal record (0.227, too wide because it belongs to the
whole model). That is a far better reason to keep it than "it scored best", and
it is the reason the derived quantity **cannot replace it**: the derived
quantity answers a different question.

`LOG_CHI2_BIAS` is left in `levels.py` as a documented, deliberately unused
constant, because the next person to notice the fit is too narrow will
rediscover it in an afternoon, and this is the measurement that says what
happens next.

### What would replace it honestly

Not a better θ dispersion. A **joint** calibration: fit the layers together
against realised width so that the total is right, instead of fitting each
against its own marginal and hoping. That needs the width budget of §1.48 as its
instrument and is a larger piece of work than a constant.

---

## 2. External evaluation against forecasting best practice (2026-08-11)

An independent review researched published practice and then judged this model
against it. Kept here because the recommendations should outlive the session
they were made in, and because several of them contradict claims this log made
earlier.

**The headline claim does not survive.** Aggregated over the two scorable
targets the model has CRPS 119.3 against uniform swing's 152.0 — 21%
distributional skill — but **seat MAE 164 against 152, which is *negative*
point-forecast skill**. Both runs print the in-sample banner, so there are
currently zero declared out-of-sample scores. The defensible statement is: *the
intervals add value over a point forecast; the central estimate does not yet
beat uniform swing.*

**The under-dispersion is structural, not a tuning problem.** The only citywide
level shock for any significant party is its pool's ratio triangular — Black
African 2021 is [0.890, 0.956, 1.009], sd about 2.4%, with probability exactly
zero outside it. That ratio is computed as a fixed-composition weighted average
of some sixty parties' swings, so *its variance is smaller than any individual
party's by construction*. Compounding it: `tie` is None in every emitted pool,
so four pools draw four independent shocks; and `turnout_noise_sd = 0.08` is
i.i.d. over 855 voting districts, so its citywide effect is 0.003 — there is
effectively no aggregate turnout uncertainty in a model whose own documentation
says 2021 was decided by 587,000 abstentions.

**On the ecological inference:** the estimator is better than Goodman
regression, the uncertainty treatment worse than any modern EI method. The
joint fit with non-negativity and a per-pool simplex is the right structure;
IPF to both known margins is standard and sound; reporting Duncan-Davis bounds
and flagging unidentified rates is better than most published work. But
`fit_joint` returns a point estimate treated as known thereafter — Freedman's
criticism of King's EI in stronger form, since we have no standard errors at
all — and the constant-rate-across-wards assumption is the exact one that fails
when group behaviour correlates with group share. A Black African voter in
Sandton and one in Diepsloot are not the same voter, and nothing here tests it.

**On the pools:** population group is a defensible proxy, and the admission
gate — out-of-sample cross-city, with in-sample gain explicitly rejected as
evidence — is better than standard practice. But the gate can only test
dimensions you can *add*; it cannot tell you the base dimension is
insufficient. Four pools for sixty-nine parties is coarse, and the Dirichlet
split within a pool is doing almost all the work.

**On benchmarking:** persistence is a floor, not a bar. The standard is the most
accurate available naive reference, and specifically the optimal convex
combination of persistence and climatology (Murphy 1992). All three of our
baselines are persistence variants.

### Recommendations, in the order given

1. Fix the scoring denominators first — every tuning decision is made against
   this instrument. *(done, 2026-08-11)*
2. Connect the measured `sd(log theta)` to the draw and replace bounded
   triangulars with unbounded heavy-tailed distributions. Bounded supports
   assign probability zero to events that happened: Al Jama-ah won a seat in
   2016 with 0 of 500 draws non-zero, an infinite log score.
3. Add a single correlated citywide turnout shock.
4. Rebuild entrants as a group total then a split — arrival probability near 1
   for an event seen in 5 of 5 transitions, support including the observed
   16.05%, funded from measured donors rather than proportionally from
   everyone (ActionSA drew ANC -0.381 and EFF -0.262 per point while the DA
   *gained* +0.199).
5. Ingest polls. The literature is unanimous that a party with no electoral
   history can only be forecast from polls; pre-2021 polls had ActionSA near
   6%, roughly sixty times closer than our default.
6. Replace the point-estimate rates matrix with posterior draws — hierarchical
   multinomial-Dirichlet with ward-varying rates (Rosen, Jiang, King & Tanner
   2001; `eiPack`).
7. Add climatology and national-swing benchmarks, and their convex combination.
8. Leave-one-metro-out across all eight metros: turns n=2 into about sixteen
   scorable city-years, and is the only way to demonstrate skill rather than
   assert it.
9. Test the constant-rate-across-wards assumption by re-fitting on ward strata.
10. Fix the variogram score — normalise by pair count, fixed common party set.

Also named as missing and not on that list: a **sensitivity decomposition**
attributing forecast variance to each source, which is why the `levels.py`
disconnection went unnoticed for as long as it did.

Sources are recorded in the task descriptions; the principal ones are Gneiting,
Balabdaoui & Raftery (JRSS-B 2007) on calibration and sharpness, Murphy (W&F
1992) on standards of reference, Freedman et al. on solutions to the ecological
inference problem, Rosen/Jiang/King/Tanner (2001) on the RxC case, and
Stoetzer/Neunhoeffer et al. (Political Analysis 2019) on multi-party forecasting.

---

# Appendix A — the original plan (rev 2), as written

Kept verbatim, including the parts the build disproved. Where a section was
later contradicted, the finding that did it is named in §1 above; nothing here
has been amended to match what was learned. Its figures are historical — what
the plan asserted on the day it was written — not statements about the current
model, and they are not maintained.

# Johannesburg 2026 LGE — Data Acquisition, Ingestion and Modelling Plan (rev 2)

**Purpose:** build a voting-district-level model of the City of Johannesburg that (a) predicts the council composition after the election on **4 November 2026** (date now proclaimed), (b) is backtested against 2016 and 2021, and (c) identifies which wards' turnout has the greatest leverage on the final seat arithmetic.

**Rev 2 changes:** seat count verified against the statutory cap; θ parameters recentred on CoJ-specific 2024 data rather than Gauteng-wide figures; parameters reparameterised at bloc level with an explicit correlation structure for the Monte Carlo; swing moved from additive to logit space; PA and Al Jama-ah promoted out of `OTHER`; fold-1 2011 inconsistency resolved; §8 added as an empirical anchor table so defaults are traceable to sources.

**Status of URLs:** links marked ✔ were confirmed during research. Links marked ⚠ are the expected path structure and should be verified before scripting against them.

---

## 0. What is actually being predicted

Johannesburg's council is elected under mixed-member proportional representation:

- 135 ward seats, first-past-the-post
- 135 PR seats, **compensatory**
- 270 total; majority = 136

**Seat count, verified.** The Municipal Structures Act caps any council at 270 councillors and CoJ has been at that cap since 2016, per MDB testimony to Parliament — so 135/270/136 is stable for 2026 despite one April 2026 press report claiming 274/138 (treat that as journalist error; it contradicts the statutory cap and every other source). One residual check at data-load time: confirm the IEC's 2026 ward list for JHB contains exactly 135 wards, and fail loudly if not.

The compensatory mechanism is the single most important structural fact. Winning a ward does not add a seat — it decides which of your entitled seats is filled by a ward councillor.

> ### ⚠️ Correction (rev 2 → rev 3): the entitlement is **not** the PR ballot share
>
> Rev 2 asserted that "a party's total seat count is determined by its citywide
> PR ballot share". **This is wrong**, and it was verified wrong against the
> IEC's own *Seat Calculation Detail* reports for both 2016 and 2021.
>
> Entitlement is determined by the party's share of the **combined ward + PR
> vote**. The statutory formula (Municipal Structures Act, Schedule 1), quoted
> verbatim on the IEC report, is:
>
> ```
> Q = (A / (B - C - D)) + 1 ; disregarding fractions
>
>   A  total valid votes cast for all parties, WARD AND PR BALLOTS ADDED TOGETHER
>   B  total seats available in the municipality (270)
>   C  independent ward councillors elected
>   D  ward councillor seats from parties with no PR list
> ```
>
> Seats are then `floor(votes / Q)` per party, with the shortfall allocated by
> largest remainder. Two exclusions from `A`, both verified to the vote:
> independents, and parties that contested a ward but registered no PR list.
>
> `src/seats.py` implements this and `src/validate_seats.py` reproduces the
> published council **exactly** for both elections — quota, `A`, and every party's
> seat count — from the VD-level result files alone:
>
> | | A | Q | ANC | DA | ActionSA | EFF |
> |---|---|---|---|---|---|---|
> | 2016 | 2,496,617 | 9,247 | 121 | 104 | — | 30 |
> | 2021 | 1,834,260 | 6,794 | 91 | 71 | 44 | 29 |
>
> **Why rev 2's error was invisible.** For almost every party the ward and PR
> shares agree to within about a point, so PR share is an excellent proxy and the
> substitution costs nothing. In 2016 the DA polled 38.34% ward / 38.48% PR —
> which is exactly why the "104 seats ≈ 38.4% of 270" check in rev 2 appeared to
> confirm the PR-only rule. **ActionSA in 2021 is the counter-example**: 13.98% on
> the ward ballot against 18.12% on PR, a 4.1pp split-ticket gap. Under the
> PR-only rule they would be entitled to ~49 seats; they got 44. They contested
> 134 of 135 wards, so this is genuine ticket-splitting, not missing candidates.
>
> **Consequence:** the primary target is citywide **combined ward + PR** share,
> and the ward ballot is roughly half of it. Ward-level modelling is not the
> secondary concern described below — it is half the answer, and any party whose
> two ballots diverge (a new insurgent party, or one with weak local candidates)
> will be mis-forecast by a PR-only model. §3 must model both ballots.

**Consequence for model design:** a ward-by-ward FPTP model that reports "seats won" is still the wrong quantity — but so is a PR-only model. Model both ballots, combine them, then allocate. Ward-level modelling additionally matters for:

1. **Overhang.** If a party wins more wards than its entitlement, the extra ward seats are retained and the effective majority threshold moves. **Verified: no overhang in 2016 or 2021** (`src/validate_seats.py` checks this directly). But 2021 was closer than rev 2 implied — the ANC took 87 wards against an entitlement of 91, leaving just 4 PR seats and only 5 wards of headroom. With the ANC's citywide share falling faster than its ward-level dominance in its strongholds, overhang is a live risk for 2026, not a theoretical one. Keep the check and report the margin.
2. **Turnout leverage.** Citywide share is a turnout-weighted average of VD-level shares, so identifying which VDs move that average most is a ward-level question.

Also note **contestation coverage** as a distinct effect from ticket-splitting: the PA contested only 52 of 135 wards in 2021, so its ward-ballot total is structurally capped regardless of support. A 2026 forecast must take a view on how many wards each party fields candidates in.

---

## 1. Data sources

### 1.1 Election results

| # | Source | Contents | Link |
|---|---|---|---|
| R1 | IEC results portal | Live and archived results dashboards | https://results.elections.org.za/ ⚠ |
| R2 | IEC Election Reports & Results | Downloadable result sets, all elections | https://www.elections.org.za/ ✔ (navigate to Elections → Election Reports and Results) |
| R3 | SANEF Elections Portal | VD-level results with area-level CSV export; substantially easier than R2 | https://elections.sanef.org.za/ ✔ |
| R4 | IEC by-election reports | Per-contest ward results since Nov 2021 | via R2 ⚠ |

Elections required:

- **2011 LGE** — *optional* share prior for fold 1 only. CoJ had 130 wards / 260 seats in 2011, so using it requires extending the VD concordance back one more delimitation. Only worth it if fold 1 underperforms without it.
- **2014 NPE** — provincial ballot, VD level (baseline for fold 1)
- **2016 LGE** — ward ballot + PR ballot, VD and ward level (target of fold 1, baseline for fold 2)
- **2019 NPE** — provincial ballot, VD level (baseline for fold 2)
- **2021 LGE** — ward ballot + PR ballot, VD and ward level (target of fold 2, baseline for fold 3)
- **2024 NPE** — provincial ballot, VD level (baseline for fold 3)
- **By-elections 2021–2026** — all CoJ wards, plus Gauteng-wide for the swing estimator

Note that national and provincial elections have no wards. 2024 data exists only at VD level, which is why VD must be the atomic unit throughout.

### 1.2 Geography and crosswalks

| # | Source | Contents | Link |
|---|---|---|---|
| G1 | MDB Spatial Knowledge Hub | Shapefiles: ward boundaries by year, municipal boundaries | https://www.demarcation.org.za/ ✔ |
| G2 | MDB Ward Delimitation 2024/2026 | 2026 ward boundaries, councillor counts per municipality, ward information tables, story map | https://www.demarcation.org.za/ward-delimitation-2024-2026/ ✔ |
| G3 | MDB Ward Delimitation Booklet | Documents the VD-within-ward numbering convention needed for the join | https://www.demarcation.org.za/wp-content/uploads/2024/07/MDB-Ward-Delimitation-Booklet-Digital-1.pdf ✔ |
| G4 | IEC VD boundaries | Voting district shapefiles and VD→ward lookup per election | via R2 ⚠ |

**The boundary problem.** Wards went from 4,468 nationally in 2021 to 4,488 in 2026. CoJ's own ward count and boundaries have shifted at every delimitation. Ward identifiers are therefore **not** comparable across years. VDs are more stable but not fully stable either — they split as registration grows.

### 1.3 Covariates

| # | Source | Contents |
|---|---|---|
| C1 | Stats SA Census 2022, Small Area Layer | Income, dwelling type, employment, household size |
| C2 | Wazimap-NG | Pre-joined census data, friendlier API |
| C3 | IEC voters' roll statistics | Registered voters by VD, by age band and sex |

Covariates are used only for the turnout sub-model. They are not needed for share prediction and adding them there invites overfitting.

### 1.4 By-election and polling comparators

| # | Source | Value | Link |
|---|---|---|---|
| B1 | The South Africa Brief | Ward-level by-election writeups with 2021 and 2024 comparators already computed — saves considerable work | https://thesouthafricabrief.substack.com/ ✔ |
| B2 | inside-politics | Metro turnout trend series and a resources page for 2026/7 | https://inside-politics.org/ ✔ |
| B3 | The Common Sense (SRF) | Metro polling and 2014/2016/2019/2021/2024 metro comparisons | https://www.thecommonsense.co.za/ ✔ |
| B4 | Ipsos, News24/City Press | Independent polling for triangulation | — |

---

## 2. Ingestion and restructuring

### Step 1 — Establish the atomic unit

Use **voting district** as the unit of observation for all elections. Everything aggregates upward from there.

### Step 2 — Build a VD concordance

VDs split and merge between elections. Construct a concordance table mapping each historic VD to 2026 VDs by spatial intersection of the shapefiles.

- **Split** (one 2014 VD → several 2026 VDs): apportion historic votes across the children.
- **Merge**: sum.
- **Boundary nibble** (minor edge adjustments): ignore below a threshold, default 2% of area.

> **Assumption A1 — within-VD homogeneity.** When splitting a historic VD, its vote shares are assumed uniform across the child VDs. This is false in practice — VD splits often follow exactly the socioeconomic gradients that predict voting. Mitigate by apportioning on **registered voters** rather than area wherever the roll permits, and by flagging split-derived observations so their influence can be down-weighted.
>
> Adjustable: `w_split` — weight applied to split-derived VD observations in fitting. Default **0.6**, range 0.3–1.0.

### Step 3 — Party normalisation

Build an explicit party crosswalk with three fields: `raw_name`, `canonical_party`, `lineage_flag`.

`lineage_flag` values:
- `continuous` — same party, comparable across years (ANC, DA, EFF from 2014, IFP, FF+, ACDP, **PA from 2016, Al Jama-ah**)
- `new` — no prior baseline (EFF in 2014, ActionSA in 2021, MK/RISE/BOSA in 2024)
- `successor` — inherits a predecessor's baseline at some discount (e.g. treatment of COPE)
- `aggregate` — swept into an `OTHER` bucket

**PA and Al Jama-ah are tracked individually, not aggregated.** Rev 2 change, and the reason is ward arithmetic: both have geographically concentrated support that wins wards, which is exactly what the overhang check and ward-count outputs care about. The PA took 2.9% of CoJ in 2024 with support concentrated in Eldorado Park / Westbury / Ennerdale / Newclare, won the Ward 82 by-election in April 2025 by 1,245 votes after more than doubling its 2021 share, and is the only party to have gained multiple CoJ council seats between elections since 2021 — plausible for up to five ward wins in 2026. Al Jama-ah's support sits almost entirely in Wards 9, 10 and 58 and it won Ward 9 on the 2024 provincial ballot. A model that leaves either in `OTHER` will miscount ward winners in specific, predictable places.

The `OTHER` bucket (now: everything outside ANC, DA, EFF, MK, ActionSA, PA, IFP, FF+, ACDP, Rise, BOSA, Al Jama-ah) is still not a nuisance term — the residual was ~4.4% of CoJ in 2024, independents are now permitted, and 508 parties registered nationally — but it no longer conceals any party capable of winning a ward. Define its membership explicitly in the crosswalk so `f_other` has a fixed denominator across years.

> **Assumption A2 — new-party baselines.** New parties have no VD-level history, so their 2026 VD shares must be imputed from their 2024 provincial-ballot VD shares scaled by a party-level LGE factor (§3.3). This is the largest single source of model error and should be reported separately in backtesting.

### Step 4 — Turnout series

Per VD per election, record: registered voters, votes cast, turnout. Then compute the **drop-off ratio**:

```
λ(LGE_t) = turnout(LGE_t) / turnout(NPE_{t-1})
```

giving `λ_2016 = T2016/T2014` and `λ_2021 = T2021/T2019` for every VD. This is the core object of the model.

### Step 5 — Assign to 2026 wards

Join 2026 VDs to 2026 wards using the MDB lookup (G2/G3). Reaggregate all reweighted historic results into 2026 ward envelopes.

### Step 6 — Storage

Parquet, one table per (election, unit) pair, plus the concordance and crosswalk tables. Python with pandas and geopandas; the spatial intersections are the only computationally awkward part and they only need running once.

---

## 3. The model

### 3.1 Decomposition

For voting district *i* and party *p*:

```
Votes(i,p) = Registered(i) × Turnout(i) × Share(i,p)
```

Three sub-models, in ascending order of difficulty and descending order of how much anyone talks about them.

### 3.2 Registration sub-model

Largely observed. Take the current roll, apply VD-level growth from the 2026 registration weekends. Low uncertainty; not worth elaborate treatment.

### 3.3 Turnout sub-model — the one that matters

```
T_2026(i) = T_2024(i) × λ̂(i)
```

Estimate `λ̂(i)` as a weighted blend of observed history, adjusted by covariates:

```
λ̂(i) = w_recency · λ_2021(i) + (1 − w_recency) · λ_2016(i)
       + β · (covariate deviation)
```

> **Assumption A3 — relative stability of drop-off.** The *absolute* level of turnout drift is not assumed stable; the *relative pattern* across VDs is. That is, if Sandton VDs dropped off less than Ivory Park VDs in both 2016 and 2021, they will again in 2026. This is the model's central bet and it is a reasonable one — differential turnout has been the most stable feature of South African metro elections.

> ### ⚠️ Measured (rev 3): A3 holds, but λ is the wrong carrier of it
>
> `src/turnout.py` computes the series and tests A3 rather than assuming it.
> Two results, and the second matters more than the first.
>
> **A3 is real but modest.** The correlation between λ_2016 and λ_2021 across
> 823 VDs is **+0.39**. That is the right sign, and it is not a small-sample
> artefact — it is flat to slightly *lower* when restricted to larger VDs
> (+0.32 for VDs above 2,000 registered) and +0.33 registration-weighted. But
> λ_2016 explains only about 15% of the variance in λ_2021, which is a long way
> from "the most stable feature of South African metro elections".
>
> **The previous LGE's turnout level predicts better than λ does.** Predicting
> 2021 VD turnout, with every predictor rescaled to the true citywide total so
> the comparison is only about the relative pattern:
>
> | Predicting | Previous LGE level | The ratio form above | Preceding NPE level |
> |---|---|---|---|
> | 2021 turnout | **0.0409** | 0.0592 | 0.0657 |
> | 2016 turnout | **0.0527** | *(needs the 2009 NPE)* | 0.0769 |
>
> MAE in turnout points. The ordering is the same in both cycles and the
> interpretation is simple: **like predicts like.** LGE turnout patterns are
> predicted better by the previous *LGE* than by the preceding *NPE*, and the
> ratio form only partially closes that gap because it starts from the NPE base
> and corrects toward LGE with λ.
>
> The rescaling matters — without it the ratio form looks far worse still,
> because it carries 2016's drop-off into 2021 and overshoots the citywide level
> by 25% (correction ×0.80). 2021's collapse was much deeper than 2016's, which
> is exactly what `w_recency` exists to hedge and exactly why it cannot be
> hedged from one prior cycle.
>
> **Suggested change to §3.3:** anchor on `T_2021(i)` (the previous LGE) rather
> than `T_2024(i) × λ̂(i)`, with the citywide level supplied separately by the
> λ blend or by scenario. Keep λ̂ for the citywide level, where it performs fine
> — the blend implies 0.66 and a 41.7% citywide 2026 turnout, inside §8.2's
> 38–42% expectation. Two caveats before adopting it: this is two cycles of
> evidence, and 2021 was Covid-affected, so §4's folds should score both forms
> head to head rather than switching on this alone.

**A free covariate the first draft threw away: by-election turnout.** By-elections are used in §3.6 only for share deltas, but their *turnout relative to the same ward's 2021 turnout* is a live differential-enthusiasm signal for λ̂. Example of why this matters: in the March 2025 Ward 99 (Linden/Blairgowrie) by-election the DA took 98% but turnout collapsed to 24% from 57% — suburban-fortress apathy is precisely the failure mode of the "DA voters turn out for locals" bet, and no other data source measures it before election day. Feed `turnout_bye(w)/turnout_2021(w)`, normalised against the same ratio's citywide median across contested wards, into the covariate term of λ̂ for VDs in and demographically adjacent to contested wards. Weight it modestly (it shares A4's selection bias), but do not discard it.

### 3.4 Share sub-model

**Rev 2: two structural changes here.**

**(a) θ is drawn at bloc level, not party level.** The first draft's party-level θ values are strongly cross-correlated because the parties share voter pools — θ_DA and θ_ASA fight over the same voters, as do θ_ANC, θ_EFF and θ_MK. Sampling them independently in the Monte Carlo generates incoherent draws (e.g. ANC, EFF and MK all simultaneously at the top of their ranges). The historical data says the *bloc-level* NPE→LGE shift is the stable object, and the party-level factors are mostly within-bloc reshuffling:

| Transition | ANC-EFF(-MK) bloc | DA(-ASA-BOSA) bloc |
|---|---|---|
| 2004 prov → 2006 LGE | −6 pts | +7 pts |
| 2009 prov → 2011 LGE | −3 | +12 |
| 2014 prov → 2016 LGE | −6 | +6 |
| 2019 prov → 2021 LGE | −22 | +13 |
| Mean | **≈ −9** | **≈ +9.5** |

(The wild 2021 party-level factors — ANC 0.67, DA 0.97 — are largely ActionSA's entry redistributing votes *within* the anti-ANC bloc plus a Covid-era turnout collapse; the bloc numbers are far better behaved.)

So: draw a bloc dip/bounce `Δ_bloc` for each of {ANC-EFF-MK}, {DA-ASA-BOSA}, then draw a **within-bloc split** (Dirichlet over the bloc's parties, concentration set from polling and by-elections), and derive each party's implied θ_p from the two. Parties outside both blocs (PA, IFP, FF+, ACDP, Al Jama-ah, Rise, OTHER) keep individual factors — their voter pools genuinely are separate. The per-party θ ranges in §3.5 survive as *sanity bounds* on the derived values and as the interface for scenario levers, not as independent sampling distributions.

**(b) Swing is applied in logit space, not additively.** The first draft's `+ δ_p` breaks at VD level: the DA averages 5% in Soweto wards, so any meaningful negative δ pushes shares negative, and the subsequent renormalisation redistributes swing in ways nobody chose. Instead:

```
logit(Share_2026(i,p)) = logit(Share_2024(i,p) × θ_p) + γ_p · localdev(i,p) + δ_p
```

with softmax renormalisation within each VD. δ_p is now a log-odds shift — uniform in logit space, which approximates proportional swing where a party is small and additive swing where it is mid-sized, and can never produce a negative share. `γ_p` retains its meaning: how much of a party's local variation is preserved versus flattened toward its citywide mean. Floor input shares at ~0.2% before the logit to keep zero-vote VDs finite.

### 3.5 Parameter table

These are the knobs. Defaults are informed priors, not estimates — fit what you can in backtesting and leave the rest as scenario levers. **Rev 2: every θ baseline is now the CoJ-specific 2024 provincial-ballot result (see §8), not the Gauteng-wide figure the first draft used for ActionSA. The factor and the baseline must live on the same geography or the VD-level imputation silently overshoots.** Per-party θ values are *derived* from bloc draws per §3.4(a); the ranges below bound the derived values.

| Parameter | Meaning | Default | Range | Basis |
|---|---|---|---|---|
| `w_recency` | Weight on 2021 vs 2016 drop-off | 0.70 | 0.50–0.90 | Recency vs sample size; note this makes 2021's Covid-era collapse dominant — test sensitivity in fold 2 |
| `w_split` | Down-weight for split-derived VDs | 0.60 | 0.30–1.00 | Judgement |
| `Δ_ANCbloc` | ANC-EFF-MK bloc NPE→LGE shift, pts | −9 | −22 to −3 | Four observed transitions: −6, −3, −6, −22 (§3.4a) |
| `Δ_DAbloc` | DA-ASA-BOSA bloc shift, pts | +9 | +5 to +14 | Four observed transitions: +7, +12, +6, +13 |
| `θ_ANC` | ANC LGE factor vs 2024 CoJ base 32% | 0.75 | 0.65–0.90 | Observed: 44.5/52 ≈ **0.86** (2016), 33.6/50 ≈ **0.67** (2021). The first draft's 0.85 default contradicted its own w_recency = 0.7, which implies ≈ 0.73. Centre there unless 2021 is explicitly argued as an outlier |
| `θ_DA` | DA LGE factor vs 2024 CoJ base 25% | 1.30 | 1.05–1.60 | Bloc bounce +9 on base 32% mostly accrues to DA if ASA/BOSA stay weak; SRF Q1-2026 has DA at 39% in Joburg ⇒ implied ≈ 1.56 at the poll's face value. Negatively correlated with θ_ASA by construction |
| `θ_EFF` | EFF LGE factor vs 2024 CoJ base 12.5% | 0.85 | 0.55–1.10 | Observed 11.1/10 ≈ **1.11** (2016) but 10.6/15 ≈ **0.71** (2021) — the first draft's "near-flat" claim was wrong. SRF Q1-2026: EFF 5% in Gauteng, consistent with the low end |
| `θ_ASA` | ActionSA LGE factor vs **2024 CoJ base 6.2%** (88k votes) | 1.50 | 0.90–3.00 | First draft used the 4.16% Gauteng base — wrong geography; on the correct 6.2% base its 2.2 default implied 13.6% citywide. Bear case: SRF Q1-2026 has ASA at 7% (⇒ ~1.1); support halved 2021→2024. Bull case: polls also missed ASA badly in 2021, and it took 22.7% in the Sept-2025 Ward 130 Soweto by-election (~3× its 2024 level there), beating MK and the EFF. Genuinely wide; keep it wide but centred lower |
| `θ_MK` | MK LGE factor vs 2024 CoJ base 12.2% | 0.60 | 0.30–1.00 | No ward machinery; list-vote party facing a two-ballot contest. Corroboration since first draft: MK's by-election strength is a KZN phenomenon — in its one Soweto test (Ward 130) it was beaten by ActionSA — and Ipsos has MK at 8% in Gauteng vs 12.2% CoJ 2024. Regional caveat: MK led the CBD in 2024 (28% average) so apply θ_MK's uncertainty with γ_MK high — its decline will not be spatially uniform |
| `θ_PA` | PA LGE factor vs 2024 CoJ base 2.9% | 1.40 | 1.00–2.20 | New in rev 2. Doubled its 2021 share in the Ward 82 by-election win; only party gaining multiple CoJ seats mid-term; concentrated support ⇒ ward-win relevant |
| `f_other` | Growth factor on the (redefined, smaller) `OTHER` bucket | 1.30 | 1.00–1.80 | Residual ≈ 4.4% in 2024 CoJ; independents now permitted; 508 parties registered |
| `τ` | By-election weight half-life (months) | 18 | 6–36 | Trades recency against sample |
| `α_split` | Dirichlet concentration for within-bloc splits | — | — | Set per bloc from polling dispersion; low α for the DA bloc (ASA outcome genuinely bimodal), higher for the ANC bloc |
| `w_bye` | Weight on by-election swing vs polling in `δ_p` | 0.40 | 0.00–1.00 | See A4 |
| `κ_ward` | Ward-ballot vs PR-ballot differential | 0.03 | 0.00–0.08 | Independents and local candidates outperform on the ward ballot |

### 3.6 By-election weighting

```
weight(j) = exp(−age_months(j) / τ) × √(votes_cast(j)) × ρ(j)
```

where `ρ(j)` measures how closely ward *j*'s 2024 party profile resembles the citywide profile.

> **Assumption A4 — by-election selection bias.** By-elections are emphatically not a random sample. They occur where a councillor died, resigned or was expelled, which skews heavily toward ANC-held wards and toward wards with unstable local politics. Turnout of 18–50% makes them candidate-driven rather than brand-driven.
>
> **Mitigation, and this is the important design choice: use deltas, not levels.** Never feed a by-election's raw vote share into the model. Feed the *change* between that ward's by-election result and its own 2024 result. Levels inherit the selection bias; within-ward deltas largely difference it out. This is why `w_bye` defaults below 0.5 — even differenced, by-elections are a directional signal rather than a swing model.

### 3.7 Seat allocation

1. Predict PR ballot share citywide.
2. Allocate 270 seats by the Municipal Structures Act Schedule 1 quota-and-surplus method.
3. Predict ward winners from ward-ballot shares (PR shares adjusted by `κ_ward`).
4. Deduct ward wins from each party's entitlement.
5. **Check for overhang.** If any party's ward wins exceed its entitlement, expand the council and recompute — the majority threshold moves off 136.

### 3.8 Coalition enumeration and power indices

The seat vector is not the output. The output is the structure of possible governments it permits.

**Full enumeration.** For every Monte Carlo draw, enumerate all 2ⁿ subsets of represented parties and flag those reaching the majority threshold. With eight to twelve parties holding seats this is 256–4,096 subsets per draw — computationally free. There is no reason to pre-filter on plausibility, and good reason not to.

**Reduce to minimal winning coalitions.** A winning subset is *minimal* if dropping any member costs it the majority. The set of MWCs is far smaller than the set of winning coalitions and far more informative: it is the set of deals where every partner has real leverage. Report MWCs, not all winners.

**Compute power indices.** This is the part that directly answers the "you never know in politics" concern. Two indices, both cheap:

- **Banzhaf index** — the share of winning coalitions in which party *p* is *pivotal* (its removal breaks the majority)
- **Shapley–Shubik index** — pivotality weighted by ordering, a better proxy for bargaining sequence

Power indices are the reason a 10% party is not a 10% actor. In 2016 the EFF took roughly 11% in Johannesburg and then determined the mayoralty without entering government at all — Mashaba ran a minority administration on external EFF support for three years. ActionSA's 16.5% in 2021 bought it a similar structural position. In both cases seat share badly understated leverage, and a Banzhaf calculation would have shown it in advance.

Report each party's power index as a **distribution across Monte Carlo draws**, not a point value. A party whose Banzhaf index is 0.05 in the median draw but 0.30 in the tenth percentile is exactly the kind of thing this exercise exists to surface.

**Add a minority-government class.** The majority threshold is not actually the binding constraint on electing a mayor. The mayor is chosen by councillors present and voting, so abstention can install a minority administration. This has happened in Johannesburg more than once, including after 2021 when the DA took mayoralties without partners, agreements or majorities. Model a third outcome class alongside majority coalition and no-government: **plurality bloc plus abstention**, viable wherever the largest bloc exceeds the sum of parties that would actively vote against it.

**Keep political feasibility as a separate, toggleable layer.** Compute the arithmetic without any refusal constraints. Then annotate — not filter — with declared positions (who has ruled out whom, which mayoral candidates cannot plausibly serve under which). Store these as an editable table with a confidence weight, because declared red lines in South African coalition politics have a short half-life. Mashaba entered politics to remove the ANC and now governs Tshwane with it. The arithmetic layer should never inherit an assumption that a stated refusal will hold.

---

## 4. Backtesting

### 4.1 Folds

| Fold | Baseline | Target | New entrant present |
|---|---|---|---|
| 1 | 2014 NPE (2011 LGE optional — see §1.1 ward-count caveat) | 2016 LGE | EFF |
| 2 | 2019 NPE + 2016 LGE + by-elections | 2021 LGE | ActionSA |
| 3 | 2024 NPE + 2021 LGE + by-elections | 2026 LGE | MK |

Fit parameters on fold 1, validate on fold 2, then apply to fold 3. Do not fit on both folds and report the fit — with two observations that is not validation, it is decoration.

### 4.2 Metrics

- **Citywide:** MAE on PR share in percentage points, per party
- **Ward-level:** MAE on party share; proportion of wards with correct predicted winner; Brier score on ward winner
- **Seat:** MAE on seat counts
- **The one that matters:** did the model correctly identify which coalition combinations cleared the majority threshold? A model that is accurate to ±3 points but calls the coalition arithmetic wrong has failed at the only task that has consequences.

### 4.3 A warning worth internalising before you start

Both backtest folds contain a major new entrant, and so does the live case. New parties are precisely where the model has no information and must lean entirely on `θ_p`, a hand-set prior. Expect something like ±1.5 points MAE on established parties and ±5 or worse on new ones.

That asymmetry is not a detail. With DA + ActionSA needing 136 of 270 and central estimates falling short of it (the draft-1 figure of ~122 predates the rev-2 parameter changes — recompute, but the qualitative point survives every parameterisation tried), the coalition question turns on the `OTHER` tail and on ActionSA's recovery — the two least predictable quantities in the model. Note the rev-2 bloc structure sharpens this: DA and ASA outcomes are now negatively correlated by construction, so their *combined* seat count is more stable across draws than either party's — which is the politically relevant quantity. **The honest output is a distribution over coalition-viability, not a seat forecast.** Run 5,000 Monte Carlo draws over the parameter ranges in §3.5 and report the probability that each coalition clears the threshold. That is a defensible deliverable. A point estimate is not.

---

## 5. Turnout leverage analysis

This addresses your second question directly, and it is the part most likely to produce something genuinely new.

**Method.** For each of the 135 wards *w*:

1. Perturb turnout in every VD within *w* by ±5 percentage points, holding shares fixed.
2. Re-run the full pipeline.
3. Record Δ in each party's seat count and Δ in the DA+ActionSA combined total.
4. Define leverage as `L(w) = |Δseats| / Δturnout`, and normalise by ward registered voters to separate "big ward" from "pivotal ward".

> **Assumption A5 — marginal voters resemble their VD.** "Holding shares fixed" assumes the voters who appear or stay home under the perturbation vote like their VD's existing voters. This is the standard assumption and probably conservative in the direction that matters (in high-ANC-share VDs the marginal stay-at-home voter is, if anything, *more* likely a disaffected ANC voter than the VD average), but the headline finding below depends on it, so it gets named and numbered like the others. Sensitivity check: re-run leverage with marginal voters drawn from a 50/50 blend of VD shares and the ward's non-voter demographic profile.

**Expected finding, stated in advance so it can be falsified.** Leverage will *not* be highest in marginal wards. It will be highest in **high-registration, high-ANC-share, historically low-turnout wards** — the Soweto and Orange Farm clusters. Those wards hold the largest stock of latent votes whose appearance or non-appearance moves the citywide PR average most. A marginal ward in Northcliff flips one ward seat and, under compensatory PR, changes the council composition by almost nothing. A ten-point turnout swing across Soweto moves the ANC's citywide share by several points and reallocates a dozen seats.

If that prediction holds, it has a practical implication: the DA's path to 136 with ActionSA depends less on persuading anyone and more on whether ANC-inclined voters in the south stay home. Which is an uncomfortable thing for a model to say, but it is what the arithmetic of compensatory PR implies.

**Secondary output.** A per-ward turnout elasticity index, mappable, which is the artefact most likely to be useful to anyone actually campaigning.

---

## 6. Known limits

- **Candidate effects are not modelled.** Zille and Mashaba are large, citywide, and have no VD-level signature the model can learn. They enter only through `δ_p`, set by hand from polling.
- **Independents.** Now permitted and unmodellable from history. They live in `OTHER`.
- **Coalition formation is not a vote-share problem.** The model tells you which arithmetic is available. It says nothing about whether two people who dislike each other will sit in the same room.
- **Polling scarcity.** Metro-level polls are few and methodologically opaque. Triangulate; do not anchor.

---

## 7. Suggested build order

1. Party crosswalk and VD concordance — dull, unglamorous, and about 60% of the total effort. Do it first and do it properly.
2. Turnout series and λ computation. At this point you can already answer the leverage question, before any share modelling at all.
3. Backtest fold 1, calibrate `θ` parameters.
4. Backtest fold 2, validate.
5. Monte Carlo over the parameter ranges for 2026.
6. Leverage analysis and mapping.

Steps 1 and 2 alone would produce something worth having.

---

## 8. Empirical anchors (rev 2)

Every default in §3.5 should be traceable to a number here. Items marked **[verify]** are press-reported and must be recomputed from IEC raw data during Step 1; the rest were cross-checked during revision (July 2026).

### 8.1 CoJ 2024 provincial ballot (the θ baselines)

| Party | 2024 CoJ % | 2024 CoJ votes | 2021 LGE % | Implied trajectory |
|---|---|---|---|---|
| ANC | 32 | ~450,000 | 33.6 | Bloc erosion to MK, not to opposition |
| DA | 25 | ~350,000 | 26.2 | Flat NPE-to-NPE; LGE bounce is the question |
| EFF | 12.5 | ~180,000 | 10.6 | Peaked 2019 (15% prov); declining |
| MK | 12.2 | ~170,000 | — | New; Soweto avg 19%, CBD avg 28%, Suburbs 4% |
| ActionSA | 6.2 | ~88,000 | 16.1 | Halved 2021→2024; the model's biggest single uncertainty |
| PA | 2.9 | ~41,000 | ~1.2 | Growing, concentrated |
| Rise | 1.6 | ~22,000 | — | Suburbs-only support base |
| IFP | 1.4 | ~20,000 | ~1.3 | Zulu-ward concentrated; competes with MK |
| BOSA | 1.0 | ~14,000 | — | Suburbs-only |
| Al Jama-ah | 0.8 | ~12,000 | ~0.9 | Wards 9/10/58 only; won Ward 9 in 2024 |
| FF+ | 0.8 | ~11,000 | ~1.6 | |
| ACDP | 0.8 | ~11,000 | ~1.0 | |
| Residual OTHER | ~4.4 | | | `f_other` denominator |

Source: ward-by-ward analysis of IEC 2024 results (Wilkinson/Daily Friend, Sep 2025, using Adrian Frith's data). Votes rounded; **[verify]** exact figures against IEC VD-level files in Step 1.

### 8.2 Turnout series (the λ anchors)

| Election | CoJ turnout | Notes |
|---|---|---|
| 2014 NPE | **72.57%** of 2,184,484 registered | ✔ computed from IEC VD-level bulk (provincial ballot, 825 VDs, 130 wards) |
| 2016 LGE | **57.06%** of 2,246,350 registered | ✔ IEC turnout report; matches the COGTA district profile's 57.1% |
| 2019 NPE | **67.22%** of 2,291,299 registered | ✔ computed from IEC VD-level bulk (provincial ballot, 853 VDs) |
| 2021 LGE | **42.61%** of 2,220,710 registered | ✔ IEC turnout report (947,305 votes); press-reported "≈43%" confirmed |
| 2024 NPE | **60.79%** of 2,348,781 registered | ✔ computed from IEC VD-level bulk (provincial ballot, 865 VDs) |

All five are now computed or IEC-confirmed rather than press-reported. The
series is monotonically declining across comparable election types and CoJ sits
slightly above the national figure in each NPE year (2019: 67.2 vs 66; 2024:
60.8 vs 58.64), which is the expected metro pattern. Note the registration
denominator is *not* monotonic — it peaks in 2019, dips in 2021, and recovers by
2024 — so λ must be computed against each year's own base, not a trend line.

Implied citywide λ under the §3.3 blend lands near **0.65–0.70** on the 2024 base, i.e. a 2026 turnout prior of roughly 38–42% citywide absent an enthusiasm shock. The IEC is actively campaigning against a repeat of 2021; December 2025 registration stood at 27.67M nationally — feed the 2026 registration-weekend deltas into §3.2 when published.

### 8.3 Polling (δ anchors — triangulate, do not anchor, per §6)

| Poll | Date | Numbers |
|---|---|---|
| SRF (Social Research Foundation) | Q1 2026 | **Joburg: DA 39%.** Gauteng: DA 37, ANC 31, ASA 7, EFF 5. Zille favourability 65% in Joburg. SRF cautions the Gauteng subsample has a high margin of error |
| Ipsos Khayabus | ~Q3 2025 | Gauteng: ANC 42, DA 24, EFF 14, MK 8 |

The two polls disagree wildly on the ANC-DA gap (SRF: DA +6; Ipsos: ANC +18). That spread — not either point estimate — is the honest input to δ_p's prior width. Recall also that pre-2021 polling missed ActionSA by ~10 points in CoJ.

### 8.4 By-election evidence, CoJ 2025–26 (for §3.6 deltas and §3.3 turnout covariate)

| Ward | Date | Result | Signal |
|---|---|---|---|
| 82 (Westbury/Newclare/Bosmont) | Apr 2025 | PA won by 1,245 votes, >2× its 2021 share; turnout 27% | θ_PA; PA ward-win capability |
| 99 (Linden/Blairgowrie) | Apr 2025 | DA 98%; turnout 24% (was 57%) | Suburban turnout apathy — feeds §3.3 covariate |
| 130 (Soweto) | Sep 2025 | ANC held, down ~10pts; ASA 22.7% (≈3× its 2024 level), beat MK and EFF | θ_ASA bull case; θ_MK bear case in Gauteng |
| 90 (Hyde Park/Parkmore) | Nov 2025 | DA held; Rise 8% in Hyde Park | Rise remains suburbs-only |
| Evaton West, Emfuleni (not CoJ) | May 2026 | DA beat ANC by 8 votes in an ANC stronghold | Directional corroboration of SRF; treat with A4 caution — it is one ward |

**[verify]** all against IEC by-election reports (R4) rather than press writeups, and extend the table with every CoJ by-election Nov 2021 – Oct 2026 during Step 1.

### 8.5 What changed between draft 1 and rev 2, in one line each

1. Seat count 270 confirmed against the statutory cap; 274 press claim rejected.
2. Election date fixed: 4 November 2026.
3. θ_ASA baseline corrected from Gauteng 4.16% to CoJ 6.2%; default cut from 2.2 to 1.5.
4. θ_ANC default cut from 0.85 to 0.75 to agree with the plan's own recency weighting.
5. θ_EFF "near-flat" claim corrected (observed 1.11 then 0.71); default cut to 0.85.
6. θ derivation moved to bloc level with Dirichlet within-bloc splits; correlation structure now explicit.
7. Additive δ_p replaced with logit-space swing.
8. PA and Al Jama-ah promoted out of `OTHER`; `OTHER` membership pinned.
9. By-election turnout ratio added as a λ̂ covariate.
10. Assumption A5 (marginal-voter composition) named in §5.
11. CoJ overhang "precedent" removed — none verifiable; check retained.
12. 2011 fold-1 inconsistency resolved (optional, with 130-ward caveat).
