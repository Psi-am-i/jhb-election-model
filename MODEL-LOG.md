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

1. **`DA_BLOC` membership is contradicted by measurement.** ActionSA's gains
   were funded by the ANC and the EFF, not the DA (per point of ActionSA:
   ANC −0.381pp, EFF −0.262pp, DA **+0.199pp**; DA vote retention uncorrelated
   with ActionSA's local strength at −0.043). The model funds ActionSA out of
   DA losses inside a conserved bloc total. **Load-bearing** — pinning the
   DA-bloc split alone moves P(ANC+DA majority) from 87.6% to 98.4%. Needs a
   config change *and* a rewrite of the published methodology paragraph, which
   currently defends the grouping on "the argument about where defectors go".
2. **The "fivefold" claim is live and wrong.** `docs-public/methodology.md`
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
9. **The Monte Carlo is not year-parameterised**, so the *distributional*
   forecast still cannot be scored against a past election — only the
   deterministic core can, via the folds. Realistic scorable targets are 2011,
   2016 and 2021; pre-2011 wards predate two delimitations.



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
